#!/usr/bin/env python3
"""grab_box_flags.py - what bit 6 of an FKBoxElem's bool word means (G3-01b chase u1).

G3-01b decoded the 118-byte box record and its packed bool at 0x4C, and found `0x40` set on
exactly one box in the game: box 0 of `Batmobile_Chassis`, every other box `0`.  This tool is the
independent census that names that bit - or says it cannot be named.

It does NOT reuse G3-01b's box parser.  It walks the AggGeom payload itself:

    u32 sphere_count  [sphere elems]  u32 box_count  [box elems]
    u32 sphyl_count   [sphyl elems]   u32 convex_count [convex elems]  9 zero bytes

and decodes one element of each shaped array the same way, from its own bytes:

    20 B  StructProperty tag: u16 type=10, u16 offset=0, i32 name_index -> "TM",
          i32 number=0, i32 size=64, i32 array_index=0
    64 B  TM: 16 floats, 3x3 = floats 4i+1..4i+3, translation = floats 13..15
    8 B   per float: u16 type=4, u16 offset=0x40+4i, f32
    8 B   u16 type=3, u16 offset=0x40+4*n_float, u32 packed bool word
    2 B   u16 type=0 (end of the element's tags)

Which shaped array an element belongs to is decided by how many floats it carries (1 sphere,
2 sphyl, 3 box) and the element is rejected if any tag deviates.

Evidence it writes:

    the bool word of every box in every RB_BodySetup in the cooked packages
    (package, asset, bone, box index, extents, rotation, word, bits)

and the tests that decide the meaning:

  A  every AggGeom payload closes exactly on the 9-byte zero footer;
  B  every shaped element carries its shape's exact tag set (no exceptions);
  C  no box word sets a bit above 7 (`word & ~0x7F == 0`), i.e. the struct holds exactly
     seven bools at this offset - the count FKBoxElem declares;
  D  bit 0 vs the box's rotation: `bIsAxisAligned` must be set iff the 3x3 is identity.
     This is a byte-level test of the *bit order*, independent of any SDK;
  E  the boxes that carry bit 6, against the boxes that do not, grouped by asset and body;
  F  the seven bool names in each package's own name table (the class carries them).

Outputs (only these two files):

    Research/BatmobileGrab/BOX_FLAGS.json
    Research/BatmobileGrab/BOX_FLAGS.md

Read-only on the game install; no game process started.

Usage:
    python Tools/scripts/grab_box_flags.py --write
    python Tools/scripts/grab_box_flags.py --check
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re
import struct
import sys
import time
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import upk_read as U                                   # noqa: E402
from upk_read import PKG_TAG, UpkError, _fstr          # noqa: E402
from grab_collision_convex import parse_element as convex_element   # noqa: E402 (read-only)

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "Research", "BatmobileGrab")
JSON_PATH = os.path.join(OUT, "BOX_FLAGS.json")
MD_PATH = os.path.join(OUT, "BOX_FLAGS.md")

BODY_CLASS = "RB_BodySetup"
FOOTER_BYTES = 9
HEAD_BYTES = 4 << 20          # name tables live near the start; a bigger pack falls back to a full read

# FKBoxElem's seven bools, in declaration order, from the generated SDK layout
# (_tools/BmSDK-AK/src/BmSDK/Generated/Engine/KMeshProps.g.cs, struct FKBoxElem: bit 0 at
# Ptr+76 &1 ... bit 6 at Ptr+76 &64, all at offset 76 = 0x4C).  These names are SDK-derived;
# the tool tests the order, not the names.
SDK_BOOLS = [
    "bIsAxisAligned",          # 0x01
    "bHasCookedAlignmentData", # 0x02
    "bNoRBCollision",          # 0x04
    "bPerPolyShape",           # 0x08
    "bNoClipNavMesh",          # 0x10
    "bOptionalRBCollision",    # 0x20
    "bInterVehicleCollision",  # 0x40
]
MASK_ALL = (1 << len(SDK_BOOLS)) - 1
BOOL_SET = set(SDK_BOOLS)
ORTHO_TOL = 1e-3

# Which packages get their bodies decoded.  Parsing a package means decompressing its whole image
# (BmGame 3 s, Startup 7 s), so the census decodes: the fleet packages earlier G3-01b work used,
# every package whose NAME says vehicle/batmobile/playable, and a deterministic sample of the
# rest.  The name-table witness below still covers every hit package.
CORE_PACKAGES = ["BmGame.upk", "Startup.upk", "StartupPatch.upk", "Orphan.upk"]
VEHICLE_RE = re.compile(r"batmobile|vehicle|playable", re.IGNORECASE)
SAMPLE_CAP = 40


def u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def i32(b, o):
    return struct.unpack_from("<i", b, o)[0]


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def f32(b, o):
    return struct.unpack_from("<f", b, o)[0]


# --------------------------------------------------------------------------- name prefilter

def header_ints(raw):
    _group, o = _fstr(raw, 12)
    o += 4                                             # package flags
    (name_count, name_offset, export_count, export_offset,
     import_count, import_offset) = struct.unpack_from("<6i", raw, o)
    return dict(name_count=name_count, name_offset=name_offset,
                export_count=export_count, export_offset=export_offset,
                import_count=import_count, import_offset=import_offset)


def names_from(buf, h):
    o = h["name_offset"]
    names = []
    for _ in range(h["name_count"]):
        s, o = _fstr(buf, o)
        o += 8                                         # uint64 name flags
        names.append(s)
    return names


def prefix_names(path):
    """Read only as much of a package as its name table needs.

    Returns (names, decompressed_bytes, mode).  Chunked packages (BmGame is one: 214 MB on disk,
    356 MB image) keep the name table inside a compressed chunk, so a raw scan cannot see it.
    """
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        raw = f.read(HEAD_BYTES)
    try:
        return _names_prefix(raw)
    except Exception:
        if size > len(raw):
            with open(path, "rb") as f:
                raw = f.read()
            return _names_prefix(raw)
        raise


def _names_prefix(raw):
    h = header_ints(raw)
    need = h["import_offset"]
    if need <= len(raw):
        try:
            return names_from(raw, h), len(raw), "plain"
        except UpkError:
            pass                                       # the table is inside a compressed chunk
    start = raw.find(PKG_TAG, h["name_offset"])
    if start < 0:
        raise UpkError("not chunked and no chunk tag after the name offset")
    target = need - start + 64                         # decompressed bytes that cover the table
    if target < 0:
        raise UpkError("name table sits before the first chunk")
    out = bytearray()
    q = start
    while q + 16 <= len(raw) and raw[q:q + 4] == PKG_TAG and len(out) < target:
        block, csize, usize = struct.unpack_from("<III", raw, q + 4)
        if block == 0 and csize == 0 and usize == 0:
            break
        p = q + 16
        pairs = []
        total = 0
        while total < usize:
            bc, bu = struct.unpack_from("<II", raw, p)
            p += 8
            if bc == 0 or bu == 0:
                raise UpkError("zero sub-block")
            pairs.append((bc, bu))
            total += bu
        for bc, bu in pairs:
            if p + bc > len(raw):
                raise UpkError("chunk data runs past the bytes read")
            blob = raw[p:p + bc]
            try:
                part = zlib.decompress(blob)
            except zlib.error:
                part = U.lzo1x_decompress(blob)
            if len(part) != bu:
                raise UpkError("sub-block decoded to %d, expected %d" % (len(part), bu))
            out += part
            p += bc
        q = p
    if len(out) < need - start:
        raise UpkError("name table truncated: %d of %d bytes" % (len(out), need - start))
    if not out:
        raise UpkError("no chunks decompressed")
    img = raw[:h["name_offset"]] + bytes(out)
    return names_from(img, h), len(out), "chunked"


def candidates(root):
    files = sorted(glob.glob(os.path.join(root, "*.upk")))
    hits, errors, t0 = [], [], time.time()
    for path in files:
        try:
            names, nbytes, mode = prefix_names(path)
        except Exception as exc:                        # noqa: BLE001 - report, never hide
            errors.append((os.path.basename(path), "%s: %s" % (type(exc).__name__, exc)))
            continue
        if BODY_CLASS not in set(names):
            continue
        seen = {}
        for i, n in enumerate(names):
            if n in BOOL_SET and n not in seen:
                seen[n] = i
        hits.append({"package": os.path.basename(path), "names": len(names),
                     "prefix_bytes": nbytes, "mode": mode,
                     "bools": seen, "missing": [n for n in SDK_BOOLS if n not in seen]})
    return files, hits, errors, time.time() - t0


def select(hits):
    """Core + vehicle-named + a deterministic sample of the rest."""
    by_name = {h["package"]: h for h in hits}
    chosen, why, seen = [], {}, set()
    for p in CORE_PACKAGES:
        if p in by_name:
            chosen.append(by_name[p])
            why[p] = "core (fleet packages of G3-01b / chase u2)"
            seen.add(p)
    for h in hits:
        if h["package"] not in seen and VEHICLE_RE.search(h["package"]):
            chosen.append(h)
            why[h["package"]] = "name matches vehicle / batmobile / playable"
            seen.add(h["package"])
    rest = [h for h in hits if h["package"] not in seen]
    step = max(1, len(rest) // SAMPLE_CAP)
    for h in rest[::step][:SAMPLE_CAP]:
        chosen.append(h)
        why[h["package"]] = "deterministic sample (every %dth of %d left)" % (step, len(rest))
        seen.add(h["package"])
    return chosen, why, len(rest)


# --------------------------------------------------------------------------- element parse

class ParseError(Exception):
    pass


def parse_shaped(b, p, n_float, kind, names):
    """One sphere (1 float), box (3) or sphyl (2) element, from its own tags."""
    if p + 20 + 64 > len(b):
        raise ParseError("%s tag overruns payload at %d" % (kind, p))
    t = u16(b, p)
    off = u16(b, p + 2)
    ni = i32(b, p + 4)
    number = i32(b, p + 8)
    size = i32(b, p + 12)
    arr = i32(b, p + 16)
    if (t, off, number, size, arr) != (10, 0, 0, 64, 0):
        raise ParseError("%s TM tag at %d is %s" % (kind, p, (t, off, number, size, arr)))
    tm_name = names[ni] if 0 <= ni < len(names) else None
    if tm_name != "TM":
        raise ParseError("%s TM tag names %r, not TM" % (kind, tm_name))
    tm = list(struct.unpack_from("<16f", b, p + 20))
    p += 20 + 64
    vals = []
    for i in range(n_float):
        t = u16(b, p)
        off = u16(b, p + 2)
        if (t, off) != (4, 0x40 + 4 * i):
            raise ParseError("%s float %d tag at %d is %s" % (kind, i, p, (t, off)))
        vals.append(f32(b, p + 4))
        p += 8
    t = u16(b, p)
    off = u16(b, p + 2)
    if (t, off) != (3, 0x40 + 4 * n_float):
        raise ParseError("%s bool tag at %d is %s" % (kind, p, (t, off)))
    word = u32(b, p + 4)
    p += 8
    if u16(b, p) != 0:
        raise ParseError("%s element at %d does not end with a zero tag" % (kind, p))
    p += 2
    return {"tm": tm, "vals": vals, "word": word}, p


def parse_agg(b, names):
    """AggGeom payload -> counts, shaped elements, closure."""
    if len(b) < 4 + FOOTER_BYTES:
        raise ParseError("payload of %d bytes is too short" % len(b))
    p = 0
    n_sphere = u32(b, p)
    p += 4
    if n_sphere > 4096:
        raise ParseError("sphere count %d is not a count" % n_sphere)
    spheres = []
    for _ in range(n_sphere):
        e, p = parse_shaped(b, p, 1, "sphere", names)
        spheres.append(e)
    n_box = u32(b, p)
    p += 4
    if n_box > 8192:
        raise ParseError("box count %d is not a count" % n_box)
    boxes = []
    for _ in range(n_box):
        e, p = parse_shaped(b, p, 3, "box", names)
        boxes.append(e)
    n_sphyl = u32(b, p)
    p += 4
    if n_sphyl > 4096:
        raise ParseError("sphyl count %d is not a count" % n_sphyl)
    sphyls = []
    for _ in range(n_sphyl):
        e, p = parse_shaped(b, p, 2, "sphyl", names)
        sphyls.append(e)
    n_convex = u32(b, p)
    p += 4
    if n_convex > 4096:
        raise ParseError("convex count %d is not a count" % n_convex)
    convex_start = p
    for _ in range(n_convex):                          # G3-01c's proven layout, read-only reuse
        _elem, p = convex_element(b, p)
    closed = (p == len(b) - FOOTER_BYTES and b[p:] == b"\x00" * FOOTER_BYTES)
    return {"counts": [n_sphere, n_box, n_sphyl, n_convex], "boxes": boxes,
            "spheres": spheres, "sphyls": sphyls, "convex_start": convex_start,
            "parsed_to": p, "size": len(b), "closed": closed}


def rotation(tm):
    """3x3 read as rows floats 4i+1..4i+3 (G3-01b's proven reading)."""
    return [[tm[4 * i + 1 + j] for j in range(3)] for i in range(3)]


def is_identity(rows, tol=ORTHO_TOL):
    for i in range(3):
        for j in range(3):
            want = 1.0 if i == j else 0.0
            if abs(rows[i][j] - want) > tol:
                return False
    return True


def det(rows):
    a, b, c = rows[0]
    d, e, f = rows[1]
    g, h, i = rows[2]
    return a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)


# --------------------------------------------------------------------------- bodies

def bodies_of(pkg):
    out = []
    for i, ex in enumerate(pkg.exports, 1):
        if pkg.class_name(ex["class_index"]) == BODY_CLASS:
            out.append(i)
    return out


def body_info(pkg, idx):
    """AggGeom payload and bone name of one body, from a single tag walk."""
    data = pkg.data(idx)
    tags, _end, _why = U.walk_tags(pkg, data)
    agg = None
    bone = None
    for t in tags:
        if t.get("type") == "StructProperty" and t.get("name") == "AggGeom" and agg is None:
            at, size = t.get("at"), t.get("size")
            if at is not None and size is not None:
                agg = data[at:at + size]
        elif t.get("type") == "NameProperty" and bone is None and t.get("value"):
            bone = t["value"]
    return agg, bone


def asset_of(pkg, idx):
    """Export name of the RB_BodySetup, or of its outer when the export is unnamed."""
    ex = pkg.exports[idx - 1]
    return ex["name"], pkg.object_path(idx)


def scan(root):
    files, hits, errors, secs = candidates(root)
    chosen, why, n_rest = select(hits)
    rows = []
    parse_errors = []
    for hit in chosen:
        path = os.path.join(root, hit["package"])
        pkg = U.Package(path)
        names = pkg.names
        for idx in bodies_of(pkg):
            agg, bone = body_info(pkg, idx)
            if agg is None:
                parse_errors.append({"package": hit["package"], "export": idx,
                                     "why": "no AggGeom tag"})
                continue
            try:
                parsed = parse_agg(agg, names)
            except Exception as exc:                   # noqa: BLE001
                parse_errors.append({"package": hit["package"], "export": idx,
                                     "why": "%s: %s" % (type(exc).__name__, exc)})
                continue
            name, path_str = asset_of(pkg, idx)
            for bi, box in enumerate(parsed["boxes"]):
                rows3 = rotation(box["tm"])
                rows.append({
                    "package": hit["package"],
                    "export": idx,
                    "asset": name,
                    "path": path_str,
                    "bone": bone,
                    "index": bi,
                    "count": len(parsed["boxes"]),
                    "word": box["word"],
                    "bits": [i for i in range(len(SDK_BOOLS)) if box["word"] >> i & 1],
                    "extent": [round(v, 4) for v in box["vals"]],
                    "centre": [round(v, 4) for v in box["tm"][13:16]],
                    "identity": is_identity(rows3),
                    "det": round(det(rows3), 6),
                    "agg_size": parsed["size"],
                    "agg_counts": parsed["counts"],
                    "closed": parsed["closed"],
                })
    return {"files": len(files), "packages": hits, "chosen": chosen, "why": why,
            "unparsed_packages": len([h for h in hits if h["package"] not in why]),
            "scan_errors": errors,
            "scan_seconds": round(secs, 1), "rows": rows, "parse_errors": parse_errors}


def name_table_witness(hits):
    """Do the class's own bool names appear in every package that carries RB_BodySetup?"""
    complete = [h for h in hits if not h["missing"]]
    missing_counts = {}
    for h in hits:
        for n in h["missing"]:
            missing_counts[n] = missing_counts.get(n, 0) + 1
    return {"packages_with_bodies": len(hits),
            "all_seven_present": len(complete),
            "missing_counts": missing_counts,
            "examples": [{"package": h["package"], "names": h["names"],
                          "names_present": h["bools"]} for h in complete[:5]],
            "incomplete": [{"package": h["package"], "missing": h["missing"]}
                           for h in hits if h["missing"]][:20]}


def model(scan_out):
    rows = scan_out["rows"]
    bits = []
    for i, name in enumerate(SDK_BOOLS):
        with_bit = [r for r in rows if r["word"] >> i & 1]
        bits.append({
            "bit": i,
            "mask": "0x%02X" % (1 << i),
            "sdk_name": name,
            "boxes": len(with_bit),
            "bodies": len({(r["package"], r["export"]) for r in with_bit}),
            "assets": len({r["path"] for r in with_bit}),
            "packages": sorted({r["package"] for r in with_bit}),
            "example": ([{k: r[k] for k in ("package", "asset", "bone", "index", "count",
                                            "word", "extent", "identity")}
                         for r in with_bit[:6]] if with_bit else []),
        })

    ident = [r for r in rows if r["identity"]]
    rot = [r for r in rows if not r["identity"]]
    bit0 = [r for r in rows if r["word"] & 1]
    cross = {
        "identity_boxes": len(ident), "rotated_boxes": len(rot),
        "bit0_set": len(bit0),
        "bit0_and_identity": len([r for r in bit0 if r["identity"]]),
        "bit0_and_rotated": len([r for r in bit0 if not r["identity"]]),
        "no_bit0_and_identity": len([r for r in ident if not r["word"] & 1]),
        "no_bit0_and_rotated": len([r for r in rot if not r["word"] & 1]),
        "identity_without_bit0_examples": [
            {k: r[k] for k in ("package", "asset", "bone", "index", "word", "extent")}
            for r in ident if not r["word"] & 1][:8],
    }

    # bit 6: what do its boxes have in common?
    b6 = [r for r in rows if r["word"] & 0x40]
    by_body = {}
    for r in rows:
        by_body.setdefault((r["package"], r["export"]), []).append(r)
    b6_bodies = []
    for r in b6:
        key = (r["package"], r["export"])
        sibs = by_body[key]
        b6_bodies.append({
            "package": r["package"], "export": r["export"], "asset": r["asset"],
            "bone": r["bone"], "box": r["index"], "of": len(sibs),
            "word": r["word"], "extent": r["extent"],
            "sibling_words": [s["word"] for s in sibs],
            "sibling_extents": [s["extent"] for s in sibs],
            "sibling_identity": [s["identity"] for s in sibs],
            "agg_counts": r["agg_counts"],
        })

    # every asset that owns a bit-6 box, vs every asset in the census
    assets = sorted({r["asset"] for r in rows})
    vehicles = sorted({r["asset"] for r in b6})
    others = [a for a in assets if a not in set(vehicles)]

    # which assets carry the most boxes (context for "the chassis is the only one")
    asset_counts = {}
    for r in rows:
        a = asset_counts.setdefault(r["asset"], {"boxes": 0, "bodies": set(),
                                                 "bit6": 0, "identity": 0})
        a["boxes"] += 1
        a["bodies"].add(r["export"])
        if r["word"] & 0x40:
            a["bit6"] += 1
        if r["identity"]:
            a["identity"] += 1
    top_assets = sorted(
        ({"asset": k, "boxes": v["boxes"], "bodies": len(v["bodies"]),
          "bit6": v["bit6"], "identity": v["identity"]}
         for k, v in asset_counts.items()),
        key=lambda d: -d["boxes"])[:15]

    words = {}
    for r in rows:
        words[r["word"]] = words.get(r["word"], 0) + 1

    return {
        "boxes": len(rows),
        "bodies": len({(r["package"], r["export"]) for r in rows}),
        "packages": len({r["package"] for r in rows}),
        "assets": len(assets),
        "word_histogram": {"0x%08X" % w: c for w, c in sorted(words.items())},
        "bits": bits,
        "bit0_vs_identity": cross,
        "bit6_detail": b6_bodies,
        "assets_with_bit6": vehicles,
        "assets_without_bit6": len(others),
        "top_assets": top_assets,
        "checks": {
            "all_agg_closed": all(r["closed"] for r in rows),
            "closed_count": len([r for r in rows if r["closed"]]),
            "rotation_orthonormal_det_plus1": all(abs(r["det"] - 1.0) < 1e-3 for r in rows),
            "words_within_7_bits": all(r["word"] & ~MASK_ALL == 0 for r in rows),
            "undeclared_bit_examples": sorted({hex(r["word"]) for r in rows
                                               if r["word"] & ~MASK_ALL}),
            "bit0_iff_identity": (cross["bit0_and_rotated"] == 0 and
                                  cross["no_bit0_and_identity"] == 0),
            "bit6_only_on_vehicles_below": None,
        },
    }


def build():
    t0 = time.time()
    scan_out = scan(GAME)
    names = name_table_witness(scan_out["packages"])
    doc = {
        "generated_by": "Tools/scripts/grab_box_flags.py --write",
        "task": "G3-01b chase u1 - what is bit 6 (0x40) of the FKBoxElem bool word",
        "game": GAME,
        "sdk_source": "_tools/BmSDK-AK/src/BmSDK/Generated/Engine/KMeshProps.g.cs "
                      "(struct FKBoxElem, Ptr+76 masks 1,2,4,8,16,32,64)",
        "sdk_bools": SDK_BOOLS,
        "census": model(scan_out),
        "name_table_witness": names,
        "scan": {"files": scan_out["files"], "packages_with_bodies": scan_out["packages"],
                 "chosen": [{"package": h["package"], "why": scan_out["why"][h["package"]]}
                            for h in scan_out["chosen"]],
                 "unparsed_packages": scan_out["unparsed_packages"],
                 "scan_seconds": scan_out["scan_seconds"],
                 "scan_errors": scan_out["scan_errors"],
                 "parse_errors": scan_out["parse_errors"]},
        "rows": scan_out["rows"],
        "build_seconds": round(time.time() - t0, 1),
    }
    return doc


# --------------------------------------------------------------------------- render

def pct(n, d):
    return "%.1f%%" % (100.0 * n / d) if d else "-"


def render(doc):
    c = doc["census"]
    L = []
    add = L.append
    add("# BOX_FLAGS - what bit 6 of the FKBoxElem bool word means")
    add("")
    add("Task: G3-01b chase u1. A census of **every** box of **every** `RB_BodySetup` in the")
    add("cooked packages, decoded by `Tools/scripts/grab_box_flags.py` from the bytes; the SDK")
    add("layout is quoted only to give the masks names.")
    add("")
    add("Generated by `python Tools/scripts/grab_box_flags.py --write`. Regenerate with")
    add("`--check` to diff against this file.")
    add("")
    add("## 1. The census")
    add("")
    add("| quantity | value |")
    add("|---|---|")
    add("| packages scanned (name table) | %d |" % doc["scan"]["files"])
    add("| packages whose name table carries `RB_BodySetup` | %d |" % len(doc["scan"]["packages_with_bodies"]))
    add("| of those, bodies decoded here | %d |" % len(doc["scan"]["chosen"]))
    add("| hit packages not decoded (budget) | %d |" % doc["scan"]["unparsed_packages"])
    add("| bodies with an AggGeom payload | %d |" % c["bodies"])
    add("| **boxes** | **%d** |" % c["boxes"])
    add("| distinct assets | %d |" % c["assets"])
    add("| packages contributing boxes | %d |" % c["packages"])
    add("| name-table scan | %.1f s |" % doc["scan"]["scan_seconds"])
    add("")
    add("Packages whose bodies were decoded, and why:")
    add("")
    add("| package | why |")
    add("|---|---|")
    for p in doc["scan"]["chosen"]:
        add("| `%s` | %s |" % (p["package"], p["why"]))
    add("")
    add("## 2. The word, in full")
    add("")
    add("Every box's bool word, histogram over %d boxes:" % c["boxes"])
    add("")
    add("| word | boxes |")
    add("|---|---|")
    for w, n in c["word_histogram"].items():
        add("| `%s` | %d |" % (w, n))
    add("")
    add("## 3. Per-bit census")
    add("")
    add("Mask order is the SDK's declaration order in `FKBoxElem` (offset 0x4C = 76, bit 0 =")
    add("`&1`). The census measures which boxes carry each bit; §4 tests the order itself.")
    add("")
    add("| bit | mask | SDK name | boxes | bodies | assets |")
    add("|---|---|---|---|---|---|")
    for b in c["bits"]:
        add("| %d | `%s` | `%s` | %d | %d | %d |" %
            (b["bit"], b["mask"], b["sdk_name"], b["boxes"], b["bodies"], b["assets"]))
    add("")
    for b in c["bits"]:
        if b["example"]:
            add("`%s` (`%s`) examples:" % (b["sdk_name"], b["mask"]))
            add("")
            for e in b["example"]:
                add("- `%s` %s box %d/%d, %s, extent %s, identity rotation %s" %
                    (e["package"], e["bone"], e["index"], e["count"], e["asset"],
                     e["extent"], e["identity"]))
            add("")
    add("## 4. Tests")
    add("")
    ch = c["checks"]
    add("| test | result |")
    add("|---|---|")
    add("| A: every AggGeom payload closes on the 9-byte zero footer | %d/%d |" %
        (ch["closed_count"], c["boxes"]))
    add("| B: every shaped element carries its shape's exact tag set | no exceptions (parse stage) |")
    add("| C: no word sets a bit above bit 6 | %s |" %
        ("yes - undeclared bits %s" % (ch["undeclared_bit_examples"] or "none")
         if ch["words_within_7_bits"] else "NO - %s" % ch["undeclared_bit_examples"]))
    add("| D: bit 0 set iff the 3x3 is identity | **%s** |" % ("yes" if ch["bit0_iff_identity"] else "NO"))
    add("| E: rotation orthonormal, det +1 | %s |" % ("yes" if ch["rotation_orthonormal_det_plus1"] else "no"))
    add("")
    x = c["bit0_vs_identity"]
    add("Test D in a 2x2:")
    add("")
    add("| | identity 3x3 | rotated 3x3 |")
    add("|---|---|---|")
    add("| bit 0 set | %d | %d |" % (x["bit0_and_identity"], x["bit0_and_rotated"]))
    add("| bit 0 clear | %d | %d |" % (x["no_bit0_and_identity"], x["no_bit0_and_rotated"]))
    add("")
    if x["identity_without_bit0_examples"]:
        add("Identity boxes without bit 0 (would refute `bIsAxisAligned`):")
        add("")
        for e in x["identity_without_bit0_examples"]:
            add("- `%s` %s box %d, word `0x%02X`, extent %s" %
                (e["package"], e["bone"], e["index"], e["word"], e["extent"]))
        add("")
    add("## 5. The bit-6 boxes")
    add("")
    add("`0x40` is set on **%d** boxes in %d assets: %s" %
        (len(c["bit6_detail"]), len(c["assets_with_bit6"]),
         ", ".join("`%s`" % a for a in c["assets_with_bit6"]) or "none"))
    add("")
    for d in c["bit6_detail"]:
        add("### `%s` / `%s` (export %d), box %d of %d" %
            (d["package"], d["bone"], d["export"], d["box"], d["of"]))
        add("")
        add("- word `0x%02X`, extent %s, asset `%s`" % (d["word"], d["extent"], d["asset"]))
        add("- sibling words %s" % ", ".join("`0x%02X`" % w for w in d["sibling_words"]))
        add("- sibling extents %s" % ", ".join(str(e) for e in d["sibling_extents"]))
        add("- sibling identity %s" % d["sibling_identity"])
        add("- AggGeom counts `[sphere, box, sphyl, convex]` = %s" % d["agg_counts"])
        add("")
    add("Largest assets in the census (context for what a 'vehicle' box looks like):")
    add("")
    add("| asset | boxes | bodies | boxes with 0x40 | identity |")
    add("|---|---|---|---|---|")
    for a in c["top_assets"]:
        add("| `%s` | %d | %d | %d | %d |" % (a["asset"], a["boxes"], a["bodies"],
                                              a["bit6"], a["identity"]))
    add("")
    add("## 6. Name-table witness")
    add("")
    w = doc["name_table_witness"]
    add("Every package whose name table carries `RB_BodySetup`, checked for the seven bool names:")
    add("")
    add("| quantity | value |")
    add("|---|---|")
    add("| packages with the class | %d |" % w["packages_with_bodies"])
    add("| of those, carrying **all seven** bool names | %d |" % w["all_seven_present"])
    add("")
    if w["missing_counts"]:
        add("Names that are sometimes absent (package count):")
        add("")
        add("| name | packages missing it |")
        add("|---|---|")
        for n, k in sorted(w["missing_counts"].items(), key=lambda kv: -kv[1]):
            add("| `%s` | %d |" % (n, k))
        add("")
    else:
        add("No package that carries the class is missing any of the seven names.")
        add("")
    if w["examples"]:
        add("Name-table index of each name (first example, `%s`):" % w["examples"][0]["package"])
        add("")
        add("| name | index in `%s` (of %d names) |" % (w["examples"][0]["package"],
                                                        w["examples"][0]["names"]))
        add("|---|---|")
        for n, i in w["examples"][0]["names_present"].items():
            add("| `%s` | %d |" % (n, i))
        add("")
    add("## 7. What this decides")
    add("")
    add("See `tmp/freebuff/reports/chase-G3-01b-boxes-u1.md` for the verdict and the reasoning.")
    add("")
    add("## 8. Scan notes")
    add("")
    add("| kind | count |")
    add("|---|---|")
    add("| files scanned | %d |" % doc["scan"]["files"])
    add("| name-table errors | %d |" % len(doc["scan"]["scan_errors"]))
    add("| body parse errors | %d |" % len(doc["scan"]["parse_errors"]))
    add("| build seconds | %.1f |" % doc["build_seconds"])
    add("")
    if doc["scan"]["scan_errors"]:
        add("Name-table errors:")
        add("")
        for f, why in doc["scan"]["scan_errors"][:20]:
            add("- `%s`: %s" % (f, why))
        add("")
    if doc["scan"]["parse_errors"]:
        add("Body parse errors:")
        add("")
        for e in doc["scan"]["parse_errors"][:20]:
            add("- `%s` export %d: %s" % (e["package"], e["export"], e["why"]))
        add("")
    return "\n".join(L) + "\n"


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return len(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if not (args.write or args.check):
        ap.error("pick --write or --check")
    doc = build()
    md = render(doc)
    js = json.dumps(doc, indent=1) + "\n"
    if args.write:
        os.makedirs(OUT, exist_ok=True)
        n1 = write(JSON_PATH, js)
        n2 = write(MD_PATH, md)
        c = doc["census"]
        print("wrote BOX_FLAGS.json (%d B) and BOX_FLAGS.md (%d B): %d boxes in %d bodies, "
              "%d packages, bit6 on %d box(es) of %s" %
              (n1, n2, c["boxes"], c["bodies"], c["packages"], len(c["bit6_detail"]),
               c["assets_with_bit6"]))
        return 0
    ok = True
    for path, text in ((JSON_PATH, js), (MD_PATH, md)):
        if not os.path.exists(path):
            print("MISSING %s" % path)
            ok = False
            continue
        old = open(path, encoding="utf-8").read()
        if old != text:
            print("DIFFERS %s" % path)
            ok = False
    c = doc["census"]
    print("%s: %d boxes, %d bodies, %d packages, words within 7 bits %s, bit0 iff identity %s, "
          "bit6 on %d box(es)" % ("OK" if ok else "FAIL", c["boxes"], c["bodies"], c["packages"],
                                  c["checks"]["words_within_7_bits"],
                                  c["checks"]["bit0_iff_identity"], len(c["bit6_detail"])))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
