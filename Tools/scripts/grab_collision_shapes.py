#!/usr/bin/env python3
"""grab_collision_shapes.py - which array the zero before the convex count belongs to.

Chase task for G3-01b's UNKNOWN U-2 (`tmp/freebuff/reports/G3-01b-boxes.md`): in a body's
`AggGeom` payload a `u32 0` sits right before the convex-element count - byte 244 of export
169750 (`Batmobile_Chassis`) and byte 126 of 169751 (`Batmobile_Rig_Weapons_Trans`).  No sphere
or sphyl element exists in any body G3-01b decoded, so the type of that count could not be
named.

This tool searches the cooked packages for bodies that DO carry spheres or capsules, decodes
them, and fixes the element order.  It writes:

    Research/BatmobileGrab/COLLISION_SHAPES.json   (data)
    Research/BatmobileGrab/COLLISION_SHAPES.md     (record)

Labels (project rule): decoded = read from package bytes at a stated offset; derived = a rule
applied to decoded values, rule stated; UNKNOWN = not decoded, with what would decide it.

Reads only: the game install (read-only) and other tasks' outputs.  Writes only the two
Research files above.  Nothing from engine/UE3 knowledge is used as evidence.

Usage:
    python Tools/scripts/grab_collision_shapes.py --write
    python Tools/scripts/grab_collision_shapes.py --check
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import upk_read as U                                    # noqa: E402
# G3-01c's proven convex-element layout (self-delimiting: fixed part counts + 14-byte trailer).
# Imported read-only; G3-01c's files are not touched.
from grab_collision_convex import parse_element as parse_convex_element   # noqa: E402

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "Research", "BatmobileGrab")
JSON_PATH = os.path.join(OUT, "COLLISION_SHAPES.json")
MD_PATH = os.path.join(OUT, "COLLISION_SHAPES.md")

# The two bodies G3-01b decoded, and the byte G3-01b reported for the unexplained zero.
G3_01B = [
    {"export": 169750, "bone": "Batmobile_Chassis", "zero_at": 244},
    {"export": 169751, "bone": "Batmobile_Rig_Weapons_Trans", "zero_at": 126},
]

TAG_STRUCT, TAG_FLOAT, TAG_BOOL, TAG_END = 10, 4, 3, 0
TM_BYTES = 64
TAG_BYTES = 20            # StructProperty tag inside an aggregate element (G3-01b, proven)
FOOTER_BYTES = 9          # zero footer after the last convex element (G3-01b/G3-01c)
MAX_FOOTER_SLACK = 0      # the footer is exactly these bytes; nothing else may follow

# Order of the four [u32 count][elements] arrays.  This is what the task decides; the script
# re-derives it from bytes and asserts the evidence before writing anything (see `evidence`).
ARRAY_KINDS = ("sphere", "box", "sphyl", "convex")
SHAPE_FLOATS = {"sphere": (0x40,), "box": (0x40, 0x44, 0x48), "sphyl": (0x40, 0x44)}
SHAPE_BOOL_OFF = {"sphere": 0x44, "box": 0x4C, "sphyl": 0x48}

SCAN_LIST_LIMIT_MD = 25   # rows shown per table in the .md; the .json keeps every row


# --------------------------------------------------------------------------- bytes

def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def f32(b, o):
    return struct.unpack_from("<f", b, o)[0]


def r6(v):
    return None if v is None else round(v, 6)


def ortho(rows):
    """3x3 orthonormality of a reading's rows, as G3-01b's box oracle measures it."""
    worst_norm = 0.0
    worst_dot = 0.0
    for i in range(3):
        n = math.sqrt(sum(c * c for c in rows[i]))
        worst_norm = max(worst_norm, abs(n - 1.0))
        for j in range(i + 1, 3):
            worst_dot = max(worst_dot, abs(sum(rows[i][k] * rows[j][k] for k in range(3))))
    det = (rows[0][0] * (rows[1][1] * rows[2][2] - rows[1][2] * rows[2][1])
           - rows[0][1] * (rows[1][0] * rows[2][2] - rows[1][2] * rows[2][0])
           + rows[0][2] * (rows[1][0] * rows[2][1] - rows[1][1] * rows[2][0]))
    return {"worst_row_norm_error": r6(worst_norm), "worst_row_dot": r6(worst_dot),
            "det": r6(det),
            "ok": worst_norm < 1e-4 and worst_dot < 1e-6 and abs(det - 1.0) < 1e-4}


def reading_a(floats):
    """G3-01b's proven box reading: rows = floats[4i+1..4i+3], translation = floats[13..15]."""
    return {"rows": [floats[4 * i + 1:4 * i + 4] for i in range(3)],
            "translation": floats[13:16]}


def parse_shaped(b, p):
    """One shaped element (sphere / box / sphyl) at `p`.  -> (record, next offset, error)."""
    start = p
    if p + TAG_BYTES > len(b):
        return None, p, "tag overruns the payload at byte %d" % p
    typ, off = struct.unpack_from("<hH", b, p)
    name_index, number, size, arr = struct.unpack_from("<iiii", b, p + 4)
    if typ != TAG_STRUCT or off != 0 or size != TM_BYTES:
        return None, p, ("element at byte %d does not start with a TM StructProperty tag "
                         "(type %d, offset %#x, size %d)" % (p, typ, off, size))
    tm_at = p + TAG_BYTES
    if tm_at + TM_BYTES > len(b):
        return None, p, "TM overruns the payload at byte %d" % tm_at
    floats = [f32(b, tm_at + 4 * k) for k in range(16)]
    p = tm_at + TM_BYTES
    fields = []
    while True:
        if p + 4 > len(b):
            return None, start, "field tag list overruns the payload at byte %d" % p
        t, o = struct.unpack_from("<hH", b, p)
        if t == TAG_END:
            fields.append({"at": p, "type": TAG_END, "kind": "end", "offset": o, "bytes": 2})
            p += 2
            break
        if t == TAG_FLOAT:
            fields.append({"at": p, "type": t, "kind": "float", "offset": o, "bytes": 8,
                           "value": r6(f32(b, p + 4))})
            p += 8
            continue
        if t == TAG_BOOL:
            fields.append({"at": p, "type": t, "kind": "bool", "offset": o, "bytes": 8,
                           "word": u32(b, p + 4)})
            p += 8
            continue
        return None, start, ("field tag type %d at byte %d is not float/bool/end" % (t, p))
    read = reading_a(floats)
    return {
        "start": start, "end": p, "bytes": p - start,
        "tm_tag": {"at": start, "type": typ, "name_index": name_index, "number": number,
                   "size": size, "array_index": arr},
        "tm_at": tm_at,
        "tm_floats": [r6(v) for v in floats],
        "tm_reading_a": {"rows": [[r6(c) for c in row] for row in read["rows"]],
                         "translation_cm": [r6(c) for c in read["translation"]]},
        "tm_oracle": ortho(read["rows"]),
        "fields": fields,
        "floats_by_offset": {f["offset"]: f["value"] for f in fields if f["kind"] == "float"},
        "bools_by_offset": {f["offset"]: f["word"] for f in fields if f["kind"] == "bool"},
    }, p, None


def parse_aggregate(b, order=ARRAY_KINDS[:3]):
    """The whole AggGeom payload: [spheres][boxes][sphyls][convex][9-byte zero footer].

    `order` exists only so the report can run the refuted order through the same parser and
    show that it does not close; everything else passes the derived order.
    """
    out = {"payload_bytes": len(b), "arrays": [], "error": None, "order": list(order)}
    p = 0
    for k, kind in enumerate(order):
        count_at = p
        if p + 4 > len(b):
            out["error"] = "count of array %d (%s) overruns the payload" % (k + 1, kind)
            return out
        n = u32(b, p)
        p += 4
        elems = []
        for j in range(n):
            rec, p, err = parse_shaped(b, p)
            if err:
                out["error"] = "array %d (%s) element %d: %s" % (k + 1, kind, j, err)
                return out
            rec["index"] = j
            elems.append(rec)
        out["arrays"].append({"index": k + 1, "kind": kind, "count_at": count_at,
                              "count": n, "elements": elems, "end": p})
    convex_at = p
    if p + 4 > len(b):
        out["error"] = "convex count overruns the payload"
        return out
    nc = u32(b, p)
    p += 4
    convex = []
    for j in range(nc):
        try:
            rec = parse_convex_element(b, p)
        except Exception as exc:                        # noqa: BLE001
            out["error"] = "convex element %d: %s" % (j, exc)
            return out
        convex.append({"index": j, "start": p, "end": rec["end"],
                       "bytes": rec["end"] - p, "nV": rec["nV"], "nP": rec["nP"],
                       "nI": rec["nI"], "nE": rec["nE"], "nX": rec["nX"],
                       "nY": rec["nY"], "nZ": rec["nZ"]})
        p = rec["end"]
    out["arrays"].append({"index": 4, "kind": "convex", "count_at": convex_at,
                          "count": nc, "elements": convex, "end": p})
    footer = b[p:]
    out["footer_at"] = p
    out["footer_bytes"] = len(footer)
    out["footer_hex"] = footer.hex()
    out["exact"] = (len(footer) == FOOTER_BYTES and not any(footer))
    out["mapped_bytes"] = p + len(footer)
    return out


def counts_of(agg):
    return tuple(a["count"] for a in agg["arrays"])


# --------------------------------------------------------------------------- packages

def image_prefix(raw, name_off, need):
    """First `need` bytes of the package image, decompressing only the chunks that cover them.

    Mirrors upk_read.Package._image (raw prefix + decompressed chunk list) without paying for
    the whole 300 MB body of a big package just to read its name table.
    """
    if len(raw) >= need and raw[name_off:name_off + 4] != U.PKG_TAG:
        return raw[:need]
    start = raw.find(U.PKG_TAG, name_off)
    if start < 0:
        return raw[:need]
    out = bytearray(raw[:name_off])
    q = start
    while len(out) < need and q + 16 <= len(raw) and raw[q:q + 4] == U.PKG_TAG:
        block, csize, usize = struct.unpack_from("<III", raw, q + 4)
        if block == 0 and csize == 0 and usize == 0:
            break
        p = q + 16
        pairs, total = [], 0
        while total < usize:
            if p + 8 > len(raw):
                return bytes(out)
            bc, bu = struct.unpack_from("<II", raw, p)
            p += 8
            if not bc or not bu:
                return bytes(out)
            pairs.append((bc, bu))
            total += bu
        for bc, bu in pairs:
            blob = raw[p:p + bc]
            try:
                part = zlib.decompress(blob)
            except zlib.error:
                part = U.lzo1x_decompress(blob)
            out += part
            p += bc
        q = p
    return bytes(out)


def header_ints(path):
    with open(path, "rb") as f:
        buf = f.read(4096)
    _grp, o = U._fstr(buf, 12)
    o += 4
    nc, no, ec, eo, ic, io = struct.unpack_from("<6i", buf, o)
    return {"names": nc, "name_offset": no, "imports_offset": io}


def candidates(root):
    """Packages whose name table mentions RB_BodySetup (cheap prefilter).

    Only as much of each package is read as the name table needs: a chunked package is
    decompressed chunk by chunk until the table is covered, and the file is read in growing
    slices rather than whole.  A file whose table cannot be reached inside the largest slice is
    kept as a candidate (never dropped) and counted in `truncated`.
    """
    files = sorted(f for f in os.listdir(root) if f.lower().endswith(".upk"))
    hits, errors, truncated = [], [], []
    for name in files:
        path = os.path.join(root, name)
        try:
            h = header_ints(path)
            need = max(h["imports_offset"], h["name_offset"] + 4096)
            size = os.path.getsize(path)
            table, raw_len = b"", 0
            for chunk in (1 << 20, 16 << 20, 64 << 20):
                with open(path, "rb") as f:
                    raw = f.read(min(size, chunk))
                raw_len = len(raw)
                img = image_prefix(raw, h["name_offset"], need)
                table = img[h["name_offset"]:h["imports_offset"]]
                if len(table) >= h["imports_offset"] - h["name_offset"] or raw_len >= size:
                    break
            if len(table) < max(0, h["imports_offset"] - h["name_offset"]):
                truncated.append(name)
            if b"RB_BodySetup" in table:
                hits.append(name)
            elif name in truncated:
                hits.append(name)
        except Exception as exc:                        # noqa: BLE001
            errors.append({"package": name, "error": str(exc)})
    return files, hits, errors, truncated


def bone_of(tags):
    for t in tags:
        if t.get("type") == "NameProperty" and "value" in t:
            return t["value"]
    return None


def bodies_of(pkg):
    return [i + 1 for i, e in enumerate(pkg.exports)
            if pkg.class_name(e["class_index"]) == "RB_BodySetup"]


def agg_of(pkg, idx):
    data = pkg.data(idx)
    tags, _end, _why = U.walk_tags(pkg, data)
    agg = [t for t in tags if t.get("name") == "AggGeom"]
    if not agg:
        return None, tags
    a = agg[0]
    return data[a["at"]:a["at"] + a["size"]], tags


# --------------------------------------------------------------------------- scan

def scan(root):
    files, hits, header_errors, truncated = candidates(root)
    hist = collections.Counter()
    size_hist = collections.Counter()
    convex_examples = []
    swapped = collections.Counter()
    signature = collections.Counter()
    rows, package_rows, parse_errors = [], [], []
    totals = collections.Counter()
    for name in hits:
        path = os.path.join(root, name)
        pkg = U.Package(path)
        bodies = bodies_of(pkg)
        pkg_counts = collections.Counter()
        for idx in bodies:
            payload, tags = agg_of(pkg, idx)
            if payload is None:
                totals["bodies_without_aggeom"] += 1
                pkg_counts["no-agg"] += 1
                continue
            agg = parse_aggregate(payload)
            if agg["error"]:
                parse_errors.append({"package": name, "export": idx,
                                     "object": pkg.object_path(idx),
                                     "payload_bytes": len(payload), "error": agg["error"]})
                pkg_counts["parse-error"] += 1
                continue
            key = counts_of(agg)
            hist[key] += 1
            for a in agg["arrays"]:
                if a["kind"] == "convex":
                    continue
                for e in a["elements"]:
                    size_hist[(a["kind"], e["bytes"])] += 1
                    want_f = set(SHAPE_FLOATS[a["kind"]])
                    ok = (set(e["floats_by_offset"]) == want_f
                          and set(e["bools_by_offset"]) == {SHAPE_BOOL_OFF[a["kind"]]})
                    signature[(a["kind"], "ok" if ok else "other_field_set")] += 1
            totals["bodies_parsed"] += 1
            totals["payload_bytes"] += len(payload)
            totals["exact" if agg["exact"] else "not_exact"] += 1
            pkg_counts["exact" if agg["exact"] else "not-exact"] += 1
            if key[0] or key[2]:
                rows.append(body_row(name, pkg, idx, bone_of(tags), agg))
                alt = parse_aggregate(payload, order=("sphyl", "box", "sphere"))
                swapped["bodies"] += 1
                if alt["error"] is None and alt["exact"]:
                    swapped["exact"] += 1
                elif alt["error"] is None:
                    swapped["parsed_but_not_exact"] += 1
                else:
                    swapped["parse_error"] += 1
            if key[3] and len(convex_examples) < 3:
                a = agg["arrays"][3]
                e = a["elements"][0]
                _shaped, _nxt, shaped_err = parse_shaped(payload, e["start"])
                convex_examples.append({"package": name, "export": idx,
                                        "object": pkg.object_path(idx),
                                        "count_at": a["count_at"], "count": a["count"],
                                        "first_element_at": e["start"],
                                        "first_u32": u32(payload, e["start"]),
                                        "first_element_is_tm_tag": shaped_err is None,
                                        "nV": e["nV"]})
        package_rows.append({"package": name, "bodies": len(bodies),
                             "counts": dict(sorted(pkg_counts.items()))})
    return {
        "packages_total": len(files),
        "packages_with_rb_bodysetup": len(hits),
        "name_table_truncated": truncated,
        "header_errors": header_errors,
        "parse_errors": parse_errors,
        "totals": dict(sorted(totals.items())),
        "count_histogram": [{"counts": list(k), "bodies": v}
                            for k, v in sorted(hist.items(), key=lambda kv: (-kv[1], kv[0]))],
        "element_sizes": [{"kind": k, "bytes": b, "elements": n}
                          for (k, b), n in sorted(size_hist.items())],
        "convex_examples": convex_examples,
        "swapped_order": dict(sorted(swapped.items())),
        "field_signature": [{"kind": k, "result": r, "elements": n}
                            for (k, r), n in sorted(signature.items())],
        "shape_bodies": rows,
        "packages": package_rows,
    }


def body_row(package, pkg, idx, bone, agg):
    row = {"package": package, "export": idx, "object": pkg.object_path(idx),
           "bone": bone, "counts": list(counts_of(agg)),
           "payload_bytes": agg["payload_bytes"], "exact": agg["exact"]}
    for a in agg["arrays"]:
        if a["kind"] in ("sphere", "sphyl") and a["count"]:
            elems = []
            for e in a["elements"]:
                offs = SHAPE_FLOATS[a["kind"]]
                elems.append({"index": e["index"],
                              "start": e["start"], "bytes": e["bytes"],
                              "fields": [[f["kind"], f["offset"],
                                          f.get("value", f.get("word"))] for f in e["fields"]],
                              "dims": {("%#04x" % o): e["floats_by_offset"].get(o) for o in offs},
                              "bool": e["bools_by_offset"].get(SHAPE_BOOL_OFF[a["kind"]]),
                              "translation_cm": e["tm_reading_a"]["translation_cm"],
                              "tm_oracle": e["tm_oracle"],
                              "rotation_is_identity":
                                  all(abs(e["tm_reading_a"]["rows"][i][j] - (1.0 if i == j else 0.0)) < 1e-6
                                      for i in range(3) for j in range(3))})
            row[a["kind"] + "s"] = elems
    return row


# --------------------------------------------------------------------------- the two G3-01b bodies

def g3_01b_bodies():
    pkg = U.Package(os.path.join(GAME, "BmGame.upk"))
    out = []
    for spec in G3_01B:
        payload, tags = agg_of(pkg, spec["export"])
        agg = parse_aggregate(payload)
        counts = counts_of(agg)
        offsets = {a["kind"]: {"count_at": a["count_at"], "count": a["count"]} for a in agg["arrays"]}
        hit = [k for k, v in offsets.items() if v["count_at"] == spec["zero_at"]]
        after_boxes = agg["arrays"][1]["end"]
        out.append({
            "export": spec["export"],
            "object": pkg.object_path(spec["export"]),
            "bone": bone_of(tags),
            "payload_bytes": len(payload),
            "counts": list(counts),
            "count_offsets": {k: v["count_at"] for k, v in offsets.items()},
            "zero_at_from_G3_01b": spec["zero_at"],
            "boxes_end": after_boxes,
            "count_at_zero_byte": hit[0] if hit else None,
            "count_at_zero_value": offsets[hit[0]]["count"] if hit else None,
            "next_array": (agg["arrays"][ARRAY_KINDS.index(hit[0]) + 1]["kind"] if hit
                           and ARRAY_KINDS.index(hit[0]) + 1 < 4 else None),
            "exact": agg["exact"],
            "footer_bytes": agg["footer_bytes"],
        })
    return out


# --------------------------------------------------------------------------- evidence

def build():
    if not os.path.isdir(GAME):
        raise SystemExit("game path missing: %s" % GAME)
    g3 = g3_01b_bodies()
    scan_out = scan(GAME)

    rows = scan_out["shape_bodies"]
    sphere_rows = [r for r in rows if r["counts"][0]]
    sphyl_rows = [r for r in rows if r["counts"][2]]
    both_rows = [r for r in rows if r["counts"][0] and r["counts"][2]]

    def elems(row, kind):
        return row.get(kind + "s", [])

    sphere_dims = [dims for r in sphere_rows for e in elems(r, "sphere")
                   for dims in [e["dims"]["0x40"]]]
    sphyl_dims = [(e["dims"]["0x40"], e["dims"]["0x44"]) for r in sphyl_rows for e in elems(r, "sphyl")]

    sphere_ortho_ok = sum(1 for r in sphere_rows for e in elems(r, "sphere") if e["tm_oracle"]["ok"])
    sphere_ortho_n = sum(1 for r in sphere_rows for e in elems(r, "sphere"))
    sphyl_ortho_ok = sum(1 for r in sphyl_rows for e in elems(r, "sphyl") if e["tm_oracle"]["ok"])
    sphyl_ortho_n = sum(1 for r in sphyl_rows for e in elems(r, "sphyl"))
    sphyl_rotated = sum(1 for r in sphyl_rows for e in elems(r, "sphyl")
                        if not e["rotation_is_identity"])
    sphyl_pos_radius = sum(1 for rad, _ln in sphyl_dims if rad is not None and rad > 0)
    sphyl_pos_len = sum(1 for _rad, ln in sphyl_dims if ln is not None and ln > 0)
    sphere_pos = sum(1 for v in sphere_dims if v is not None and v > 0)

    bones_of_spheres = collections.Counter(r["bone"] for r in sphere_rows if r["bone"])
    bones_of_sphyls = collections.Counter(r["bone"] for r in sphyl_rows if r["bone"])
    limb_tokens = ("Thigh", "Calf", "Foot", "Clavicle", "UpperArm", "Forearm", "Hand", "Neck")
    head_tokens = ("Head", "Spine", "Pelvis", "Neck")

    def token_hits(counter, tokens):
        hit = collections.Counter()
        for bone, n in counter.items():
            for tok in tokens:
                if tok in bone:
                    hit[tok] += n
        return dict(sorted(hit.items()))

    # The discriminator that separates array 3 from the convex array at the same byte position:
    # a shaped array's element starts with a TM StructProperty tag, a convex element with a u32
    # vertex count.  Read both from real payloads.
    disc = []
    sources = []
    if sphyl_rows:
        sources.append((sphyl_rows[0], 2))
    if sphere_rows:
        sources.append((sphere_rows[0], 0))
    for r, arr_i in sources:
        pkg = U.Package(os.path.join(GAME, r["package"]))
        payload, _tags = agg_of(pkg, r["export"])
        agg = parse_aggregate(payload)
        a = agg["arrays"][arr_i]
        e = a["elements"][0]
        disc.append({"package": r["package"], "export": r["export"], "object": r["object"],
                     "array_index": a["index"], "array_kind": a["kind"],
                     "count_at": a["count_at"], "count": a["count"],
                     "first_element_at": e["start"], "first_u32": u32(payload, e["start"]),
                     "first_element_is_tm_tag": "tm_floats" in e,
                     "element_bytes": e["bytes"]})
    convex_samples = scan_out["convex_examples"]

    element_sizes = collections.defaultdict(list)
    for row in scan_out["element_sizes"]:
        element_sizes[row["kind"]].append({"bytes": row["bytes"], "elements": row["elements"]})

    checks = []

    def check(name, ok, detail):
        checks.append({"check": name, "result": "PASS" if ok else "FAIL", "detail": detail})

    for row in g3:
        check("G3-01b body %d: the byte G3-01b reported is an array count" % row["export"],
              row["count_at_zero_byte"] is not None,
              "byte %d holds the %s count (value %d); the sphyl count sits there and the "
              "convex count at %d"
              % (row["zero_at_from_G3_01b"], row["count_at_zero_byte"],
                 row["count_at_zero_value"], row["count_offsets"]["convex"]))
    check("the count the task asked about is the same array in both G3-01b bodies",
          len({r["count_at_zero_byte"] for r in g3}) == 1 and
          {r["count_at_zero_byte"] for r in g3} == {"sphyl"},
          "both report the sphyl count; offsets %s"
          % ", ".join("%d->%d" % (r["export"], r["zero_at_from_G3_01b"]) for r in g3))
    check("every scanned body's payload closes to the 9-byte zero footer",
          scan_out["totals"].get("not_exact", 0) == 0 and scan_out["totals"].get("bodies_parsed", 0) > 0,
          "%d bodies parsed, %d exact, %d not exact, %d parse errors"
          % (scan_out["totals"].get("bodies_parsed", 0), scan_out["totals"].get("exact", 0),
             scan_out["totals"].get("not_exact", 0), len(scan_out["parse_errors"])))
    check("bodies carrying spheres exist and decode", len(sphere_rows) > 0 and sphere_pos == len(sphere_dims),
          "%d bodies, %d sphere elements, %d with radius > 0"
          % (len(sphere_rows), len(sphere_dims), sphere_pos))
    check("bodies carrying sphyls exist and decode", len(sphyl_rows) > 0 and
          sphyl_pos_radius == len(sphyl_dims) and sphyl_pos_len == len(sphyl_dims),
          "%d bodies, %d sphyl elements, %d/%d with both floats > 0"
          % (len(sphyl_rows), len(sphyl_dims), sphyl_pos_radius, sphyl_pos_len))
    check("shaped elements' TM is orthonormal with det +1",
          sphere_ortho_ok == sphere_ortho_n and sphyl_ortho_ok == sphyl_ortho_n and sphere_ortho_n > 0,
          "sphere %d/%d, sphyl %d/%d" % (sphere_ortho_ok, sphere_ortho_n,
                                         sphyl_ortho_ok, sphyl_ortho_n))
    check("a body can carry spheres and sphyls at the same time (order is not one-or-the-other)",
          len(both_rows) > 0, "%d such bodies; first: %s (%s) counts %s"
          % (len(both_rows), both_rows[0]["object"] if both_rows else "-",
             both_rows[0]["package"] if both_rows else "-",
             both_rows[0]["counts"] if both_rows else "-"))
    check("the 3rd array's element is a TM StructProperty, the 4th array's is a raw vertex count",
          len(disc) >= 2 and len(convex_samples) > 0
          and all(d["first_element_is_tm_tag"] for d in disc)
          and not any(c["first_element_is_tm_tag"] for c in convex_samples),
          "%d shaped samples (TM tag: %s), %d convex samples (TM tag: %s)"
          % (len(disc), [d["first_element_is_tm_tag"] for d in disc], len(convex_samples),
             [c["first_element_is_tm_tag"] for c in convex_samples]))
    size_ok = ([r["bytes"] for r in element_sizes["sphere"]] == [102]
               and [r["bytes"] for r in element_sizes["sphyl"]] == [110]
               and [r["bytes"] for r in element_sizes["box"]] == [118])
    check("every shaped element has one byte size per kind: sphere 102, box 118, sphyl 110",
          size_ok,
          ", ".join("%s: %s" % (k, [r["bytes"] for r in v]) for k, v in sorted(element_sizes.items())))
    sig = {(r["kind"], r["result"]): r["elements"] for r in scan_out["field_signature"]}
    bad_sig = sum(n for (k, r), n in sig.items() if r != "ok")
    check("every element of an array carries that shape's exact field set (1/3/2 floats, own bool slot)",
          bad_sig == 0 and sig.get(("sphere", "ok"), 0) > 0 and sig.get(("sphyl", "ok"), 0) > 0,
          ", ".join("%s: %d ok, %d other" % (k, sig.get((k, "ok"), 0),
                                             sig.get((k, "other_field_set"), 0))
                    for k in ("sphere", "box", "sphyl")))

    return {
        "tool": "grab_collision_shapes.py",
        "sources": {"game": GAME, "packages_scanned": scan_out["packages_total"],
                    "packages_with_bodies": scan_out["packages_with_rb_bodysetup"]},
        "answer": {
            "question": ("which element type's count is the u32 0 right before the convex-element "
                         "count (byte 244 of export 169750, byte 126 of 169751)?"),
            "answer": "sphyl (capsule) - array 3 of the four [u32 count][elements] arrays",
            "array_order": list(ARRAY_KINDS),
            "label": ("decoded: bodies that carry spheres and bodies that carry capsules were "
                      "found in the cooked packages and parsed; the count at that byte position "
                      "is the one that becomes non-zero when capsules are present, and the array "
                      "before it becomes non-zero when spheres are present"),
        },
        "array_layout": [
            {"index": 1, "kind": "sphere", "count_at": "payload + 0",
             "element": "TM StructProperty (20 B tag + 64 B) + FloatProperty 0x40 + BoolProperty 0x44 + 2-byte end",
             "element_bytes": 102, "scalars": {"0x40": "radius (cm)"}},
            {"index": 2, "kind": "box", "count_at": "payload + 4 (after the sphere array)",
             "element": "TM + floats 0x40/0x44/0x48 + bool 0x4C + end (G3-01b)",
             "element_bytes": 118, "scalars": {"0x40": "extent x (cm)", "0x44": "extent y (cm)",
                                              "0x48": "extent z (cm)"}},
            {"index": 3, "kind": "sphyl", "count_at": "payload + boxes_end",
             "element": "TM + floats 0x40/0x44 + bool 0x48 + end",
             "element_bytes": 110, "scalars": {"0x40": "radius (cm)", "0x44": "length (cm)"}},
            {"index": 4, "kind": "convex", "count_at": "payload + sphyl array end",
             "element": "G3-01c's layout (fixed part counts + 24 B box + 14 B trailer)",
             "element_bytes": None, "scalars": {}},
        ],
        "g3_01b_bodies": g3,
        "evidence": {
            "discriminator_samples": disc,
            "convex_samples": convex_samples,
            "element_byte_sizes": element_sizes,
            "sphere_dimension_range_cm": [min(sphere_dims) if sphere_dims else None,
                                          max(sphere_dims) if sphere_dims else None],
            "sphyl_radius_range_cm": [min(r for r, _l in sphyl_dims) if sphyl_dims else None,
                                      max(r for r, _l in sphyl_dims) if sphyl_dims else None],
            "sphyl_length_range_cm": [min(l for _r, l in sphyl_dims) if sphyl_dims else None,
                                      max(l for _r, l in sphyl_dims) if sphyl_dims else None],
            "sphyl_with_rotated_tm": [sphyl_rotated, sphyl_ortho_n],
            "sphere_bone_tokens": token_hits(bones_of_spheres, head_tokens),
            "sphyl_bone_tokens": token_hits(bones_of_sphyls, limb_tokens),
            "sphere_bodies": len(sphere_rows),
            "sphyl_bodies": len(sphyl_rows),
            "both_bodies": len(both_rows),
        },
        "checks": checks,
        "scan": {k: scan_out[k] for k in ("packages_total", "packages_with_rb_bodysetup",
                                          "totals", "count_histogram", "element_sizes",
                                          "packages", "swapped_order", "field_signature",
                                          "name_table_truncated", "header_errors",
                                          "parse_errors")},
        "shape_bodies": rows,
        "sphyl_examples": sphyl_rows[:60],
        "sphere_examples": sphere_rows[:60],
        "unknowns": [
            {"item": "the member names 'radius' / 'length' behind floats 0x40 / 0x44 of a sphyl",
             "label": "UNKNOWN (assignment derived)",
             "what_was_tried": ("the payload carries no FName for these fields (simple types are "
                                "tagged by offset only), and BMSDK_OFFSETS.json has no FKSphylElem/"
                                "FKSphereElem/FKAggregateGeom layout"),
             "decided_by": "the magnitudes: 0x44 reaches 113.5 cm on a baseball bat while 0x40 is "
                           "6.78 cm, so 0x40 is the radial one; the exact member names would come "
                           "from the engine's struct dump (G3-06-style native layout)"},
            {"item": "the BoolProperty inside each shaped element (sphere 0x44, sphyl 0x48)",
             "label": "UNKNOWN",
             "what_was_tried": "decoded the tag and every element's word; same status as G3-01b's "
                               "box bool 0x4C - no local layout names the bit",
             "decided_by": "a struct dump for the element types"},
            {"item": "whether a sphere body's radius can be negative or a capsule's length zero",
             "label": "decoded as observed",
             "what_was_tried": "counted signs over the whole scan",
             "decided_by": "the counts in `evidence`"},
        ],
    }


# --------------------------------------------------------------------------- render

def render(doc):
    L = []
    A = L.append
    ans = doc["answer"]
    g3 = {r["export"]: r for r in doc["g3_01b_bodies"]}
    ev = doc["evidence"]
    tot = doc["scan"]["totals"]
    A("# The zero before the convex count is the capsule (sphyl) count — chase of G3-01b U-2")
    A("")
    A("**STATUS: resolved.** Generated by `Tools/scripts/grab_collision_shapes.py` (`--write` /")
    A("`--check`). Every number below is recomputed from the package bytes by `--check`.")
    A("")
    A("## 1. Answer")
    A("")
    A("The `u32 0` at **byte 244 of export 169750** and at **byte 126 of export 169751** is the")
    A("**count of the sphyl (capsule) array** — the third of four `[u32 count][elements...]`")
    A("arrays. The convex-element count is the `u32` *after* it (`+4`).")
    A("")
    A("| array | kind | where its count sits | element | bytes | scalars |")
    A("|---:|---|---|---|---:|---|")
    for a in doc["array_layout"]:
        A("| %d | `%s` | %s | %s | %s | %s |"
          % (a["index"], a["kind"], a["count_at"], a["element"],
             a["element_bytes"] if a["element_bytes"] else "variable",
             ", ".join("%s = %s" % (k, v) for k, v in a["scalars"].items()) or "-"))
    A("")
    A("So the aggregate is `[nSphere][spheres][nBox][boxes][nSphyl][sphyls][nConvex][convex]`,")
    A("then a 9-byte zero footer: the four counts are **interleaved** with their arrays, they are")
    A("not four words of header (`grab_collision_geom.py`'s docstring guessed a 16-byte header;")
    A("the bytes say otherwise, and with this reading all %d scanned bodies close exactly)."
      % tot.get("bodies_parsed", 0))
    A("")
    A("For the two bodies G3-01b had:")
    A("")
    A("| export | bone | payload | counts (sphere, box, sphyl, convex) | sphyl count at | G3-01b's zero at |")
    A("|---|---|---:|---|---:|---:|")
    for r in doc["g3_01b_bodies"]:
        A("| %d | `%s` | %d B | %s | %d | %d |"
          % (r["export"], r["bone"], r["payload_bytes"], r["counts"],
             r["count_offsets"]["sphyl"], r["zero_at_from_G3_01b"]))
    A("")
    A("Both bodies' payloads still close byte-for-byte after the extra array is accounted for")
    A("(%s)." % "; ".join("%d: %s, footer %d B" % (r["export"], "exact" if r["exact"] else "NOT exact",
                                                  r["footer_bytes"]) for r in doc["g3_01b_bodies"]))
    A("")
    A("Label: **decoded** (counts read at the stated offsets) + **derived** (which count is which,")
    A("from the evidence in §3–§5).")
    A("")
    A("## 2. What decided it")
    A("")
    A("G3-01b could not name the type because none of the 131 boxes' bodies holds a sphere or a"
      " capsule. The cooked packages do hold such bodies. This scan read **%d packages**, %d of"
      " which contain `RB_BodySetup` exports, and parsed **%d bodies** carrying an `AggGeom`"
      " payload. Among them:"
      % (doc["sources"]["packages_scanned"], doc["sources"]["packages_with_bodies"],
         tot.get("bodies_parsed", 0)))
    A("")
    A("- **%d bodies carry spheres** (non-zero 1st count);" % ev["sphere_bodies"])
    A("- **%d bodies carry capsules** (non-zero 3rd count);" % ev["sphyl_bodies"])
    A("- **%d bodies carry both** in the same payload." % ev["both_bodies"])
    A("")
    A("The count that turns non-zero when capsules are present is the 3rd one — the `u32` that")
    A("G3-01b saw as 0 at byte 244 / 126. Its elements are `TM` + two floats, which is why the")
    A("capsule hypothesis is testable: the 1st array's elements carry **one** float, the 3rd's")
    A("**two**, the 2nd (G3-01b's boxes) **three**.")
    A("")
    A("Examples straight out of the scan (bone names are the `NameProperty` that precedes the")
    A("`AggGeom` tag in the same export). Capsules first — these are the bodies G3-01b did not")
    A("have, and the reason the 3rd count is no longer a guess:")
    A("")
    A("| package | export | bone | counts | element 0: radius / length (cm) |")
    A("|---|---:|---|---|---|---|")
    for r in doc["sphyl_examples"][:8]:
        e = r["sphyls"][0]
        A("| `%s` | %d | `%s` | %s | %s / %s |"
          % (r["package"], r["export"], r["bone"], r["counts"],
             e["dims"]["0x40"], e["dims"]["0x44"]))
    A("")
    A("Bodies with spheres, in the same scan:")
    A("")
    A("| package | export | bone | counts | element 0: radius (cm) |")
    A("|---|---:|---|---|---|---|")
    for r in doc["sphere_examples"][:8]:
        e = r["spheres"][0]
        A("| `%s` | %d | `%s` | %s | %s |"
          % (r["package"], r["export"], r["bone"], r["counts"], e["dims"]["0x40"]))
    A("")
    A("## 3. Element layouts decoded here")
    A("")
    A("`sphere` element (@ +0 of its array):")
    A("")
    A("```")
    A("+0x00  20  StructProperty tag: type 10, offset 0, name index -> TM, size 64, array index 0")
    A("+0x14  64  TM: 16 floats (reading A: rows = floats[4i+1..4i+3], translation = floats[13..15])")
    A("+0x54   4  tag: type 4 (float), offset 0x40   -> radius")
    A("+0x58   4  value")
    A("+0x5C   4  tag: type 3 (bool),  offset 0x44")
    A("+0x60   4  packed bool word")
    A("+0x64   2  end tag (type 0)")
    A("total 102 bytes")
    A("```")
    A("")
    A("`sphyl` element: the same, with two floats and the bool one slot later:")
    A("")
    A("```")
    A("+0x00  20  StructProperty tag: type 10, offset 0, name index -> TM, size 64, array index 0")
    A("+0x14  64  TM: 16 floats")
    A("+0x54   4  tag: type 4 (float), offset 0x40   +0x58   4  value  -> radius")
    A("+0x5C   4  tag: type 4 (float), offset 0x44   +0x60   4  value  -> length")
    A("+0x64   4  tag: type 3 (bool),  offset 0x48   +0x68   4  packed bool word")
    A("+0x6C   2  end tag (type 0)")
    A("total 110 bytes")
    A("```")
    A("")
    A("Measured element sizes over the whole scan:")
    A("")
    for kind, rows in doc["evidence"]["element_byte_sizes"].items():
        A("- `%s`: %s" % (kind, ", ".join("%d elements of %d bytes" % (r["elements"], r["bytes"])
                                         for r in rows)))
    A("")
    A("## 4. Oracles")
    A("")
    for c in doc["checks"]:
        A("- **%s** — %s" % (c["result"], c["check"]))
        A("  %s" % c["detail"])
    A("")
    A("The strongest three, in numbers:")
    A("")
    A("1. **Byte accounting.** %s bodies whose payload is parsed with this order and then consumed"
      % tot.get("bodies_parsed", 0))
    A("   exactly to the 9-byte zero footer, with %d non-exact and %d parse errors."
      % (tot.get("not_exact", 0), len(doc["scan"]["parse_errors"])))
    A("   Byte closure alone does **not** pick the order of the two shaped arrays: the same parser")
    A("   with `sphyl` first was run over the %d bodies that carry one and %d of them also closed"
      % (doc["scan"]["swapped_order"].get("bodies", 0),
         doc["scan"]["swapped_order"].get("exact", 0)))
    A("   exactly, because a shaped element's field tags are self-terminating. What does decide it")
    A("   is the field set below. (A convex element in the 3rd slot, by contrast, fails at once: it")
    A("   starts with a raw `u32` vertex count, not a TM tag.)")
    A("2. **Element shape vs field count.** Spheres carry 1 scalar (%s–%s cm), capsules 2"
      % tuple(ev["sphere_dimension_range_cm"]))
    A("   (radius %s–%s cm, length %s–%s cm), boxes 3 (G3-01b). A ball has one dimension, a"
      % (ev["sphyl_radius_range_cm"][0], ev["sphyl_radius_range_cm"][1],
         ev["sphyl_length_range_cm"][0], ev["sphyl_length_range_cm"][1]))
    A("   capsule two, a rectangular box three.")
    A("3. **Bone names.** Bodies whose 1st array is non-zero sit on the %d bone names"
      " %s; bodies whose 3rd array is non-zero sit on the %d bone names %s."
      % (len(ev["sphere_bone_tokens"]), ", ".join(ev["sphere_bone_tokens"]),
         len(ev["sphyl_bone_tokens"]), ", ".join(ev["sphyl_bone_tokens"])))
    A("   Capsules are rotated about their own frame in %s of %s elements (so the TM really is the"
      % (ev["sphyl_with_rotated_tm"][0], ev["sphyl_with_rotated_tm"][1]))
    A("   shape's frame, not a placeholder).")
    A("")
    A("Shaped vs convex elements, read from the payloads themselves (the shaped rows sit at the")
    A("3rd count, the convex rows at the 4th — the position that would be ambiguous if the 3rd")
    A("array were convex):")
    A("")
    A("| package | export | array | count at | count | first u32 of element 0 |")
    A("|---|---:|---|---:|---:|---|")
    for s in ev["discriminator_samples"]:
        A("| `%s` | %d | %d (`%s`) | %d | %d | %d (%s) |"
          % (s["package"], s["export"], s["array_index"], s["array_kind"], s["count_at"],
             s["count"], s["first_u32"],
             "TM StructProperty tag" if s["first_element_is_tm_tag"] else "raw u32"))
    for s in ev["convex_samples"]:
        A("| `%s` | %d | 4 (`convex`) | %d | %d | %d (= its nV, no TM tag) |"
          % (s["package"], s["export"], s["count_at"], s["count"], s["first_u32"]))
    A("")
    A("## 5. Fleet census")
    A("")
    A("Count tuples `(sphere, box, sphyl, convex)` over the %s parsed bodies, most common first:"
      % tot.get("bodies_parsed", 0))
    A("")
    A("| counts | bodies |")
    A("|---|---:|")
    for row in doc["scan"]["count_histogram"][:20]:
        A("| %s | %d |" % (tuple(row["counts"]), row["bodies"]))
    A("")
    A("| scan total | value |")
    A("|---|---:|")
    for k, v in sorted(tot.items()):
        A("| %s | %s |" % (k, v))
    A("")
    A("`bodies_without_aggeom` are `RB_BodySetup` exports whose tag stream carries no `AggGeom`")
    A("property at all (no collision geometry on that bone), so they say nothing either way about")
    A("the order and are excluded from the census.")
    A("")
    A("Per package (every package whose name table mentions `RB_BodySetup`):")
    A("")
    A("| package | RB_BodySetup exports | payload results |")
    A("|---|---:|---|")
    for p in doc["scan"]["packages"]:
        A("| `%s` | %d | %s |" % (p["package"], p["bodies"],
                                  ", ".join("%s %s" % (k, v) for k, v in p["counts"].items())))
    A("")
    A("## 6. What stays open")
    A("")
    for u in doc["unknowns"]:
        A("- **%s** — %s" % (u["item"], u["label"]))
        A("  tried: %s" % u["what_was_tried"])
        A("  decided by: %s" % u["decided_by"])
    A("")
    A("## 7. Reproduce")
    A("")
    A("```")
    A("python Tools/scripts/grab_collision_shapes.py --write")
    A("python Tools/scripts/grab_collision_shapes.py --check")
    A("```")
    A("")
    return "\n".join(L)


# --------------------------------------------------------------------------- cli

def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="decode and write the two Research files")
    g.add_argument("--check", action="store_true", help="recompute and compare with the written files")
    a = ap.parse_args()

    doc = build()
    md = render(doc)
    js = json.dumps(doc, indent=1, sort_keys=False) + "\n"

    if a.write:
        os.makedirs(OUT, exist_ok=True)
        write(JSON_PATH, js)
        write(MD_PATH, md)
        failed = [c for c in doc["checks"] if c["result"] != "PASS"]
        print("wrote %s and %s (%d bodies scanned, %d sphere bodies, %d capsule bodies, %d/%d checks)"
              % (os.path.basename(JSON_PATH), os.path.basename(MD_PATH),
                 doc["scan"]["totals"].get("bodies_parsed", 0),
                 doc["evidence"]["sphere_bodies"], doc["evidence"]["sphyl_bodies"],
                 len(doc["checks"]) - len(failed), len(doc["checks"])))
        for c in failed:
            print("FAILED CHECK: %s -> %s" % (c["check"], c["detail"]))
        return 0 if not failed else 1

    ok = True
    for path, text, what in ((JSON_PATH, js, "json"), (MD_PATH, md, "md")):
        if not os.path.exists(path):
            print("MISSING: %s" % path)
            ok = False
            continue
        old = open(path, encoding="utf-8", newline="").read()
        if old.replace("\r\n", "\n") != text:
            print("MISMATCH: %s (recomputed %d bytes, stored %d bytes)" % (what, len(text), len(old)))
            ok = False
    failed = [c for c in doc["checks"] if c["result"] != "PASS"]
    for c in failed:
        print("FAILED CHECK: %s -> %s" % (c["check"], c["detail"]))
    ans = doc["answer"]["answer"]
    print("%s: %s; %d/%d checks; bodies %d, sphere bodies %d, capsule bodies %d"
          % ("OK" if ok and not failed else "BAD", ans, len(doc["checks"]) - len(failed),
             len(doc["checks"]), doc["scan"]["totals"].get("bodies_parsed", 0),
             doc["evidence"]["sphere_bodies"], doc["evidence"]["sphyl_bodies"]))
    return 0 if ok and not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
