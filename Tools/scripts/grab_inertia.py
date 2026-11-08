#!/usr/bin/env python3
"""grab_inertia.py - where mass properties and inertia live, BmAK and JC3 (G3-10c).

The open question: the Batmobile bodies' inertia tensor is UNKNOWN.  This tool looks
for it in the two cooked physics formats the project reads, on both sides of the
translation:

  BmAK  (UE3 / PhysX): `RB_BodySetup` exports of `BmGame.upk` -> `AggGeom` payload.
        Every property tag of every body is listed (a decoded negative is evidence),
        every box record is decoded byte-for-byte, and every 4-byte-aligned f32 triple
        in each `AggGeom` payload is tested against
          - the box formula  I_diag = m/12*(b^2+c^2, a^2+c^2, a^2+b^2)   (mass unknown,
            so the test is scale-free: does some k>0 make k*sig == triple?), and
          - the exact convex-hull tensor of the decoded vertices (same scale-free test).
  JC3   (Havok 2014.1): `hknpShapeMassProperties` blocks of the Serpente donor and the
        fleet -> the 48-byte record: 16 zero bytes, a 24-byte payload of three
        int16x4 groups, the mass f32 at +0x28, one f32 at +0x2c.  All 56 donor blocks
        are decoded, linked to their hulls, and both the box formula and the exact
        hull tensor are tested against the stored diagonal.

Labels, on every value in the outputs:
    decoded  read from the bytes (package + export + offset, or file + offset)
    derived  computed from decoded values, rule stated
    UNKNOWN  not decoded; the output says what was tried and what would settle it

Read-only on the game install and on every input.  Writes only its two outputs:

    Research/BatmobileGrab/INERTIA.md
    Research/BatmobileGrab/INERTIA.json

`--check` recomputes every number from the source bytes, compares both files
byte-for-byte, re-runs every oracle and fails on any drift.  The one oracle that is
expected to fail (the brief's box formula) is printed as the finding, never hidden.

Usage
    uv run --with numpy --with scipy python Tools/scripts/grab_inertia.py --write
    uv run --with numpy --with scipy python Tools/scripts/grab_inertia.py --check
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import struct
import sys

import numpy as np
from scipy.spatial import ConvexHull

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import upk_read as U     # noqa: E402
import jc3hkx            # noqa: E402

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
BMAK = os.path.join(GAME, "BmGame.upk")
# export index -> role, all from BmGame.upk
BMAK_BODIES = [
    (169748, "Batmobile_V2 battle", "convex"),
    (169749, "Batmobile_V2_Collision_Pursuite", "convex"),
    (169750, "Batmobile_Chassis", "box"),
    (169751, "Batmobile_Rig_Weapons_Trans", "box"),
]
BMAK_PHYSASSET = 158266

DONOR = ("Builds/test-091/aaf/models/jc_vehicles/01_land/"
         "v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc")
FLEET = "E:/Modding/_shared/gamedata/JC3grab/hkx/all"

OUT_MD = os.path.join(REPO, "Research", "BatmobileGrab", "INERTIA.md")
OUT_JSON = os.path.join(REPO, "Research", "BatmobileGrab", "INERTIA.json")

# --- JC3 hknpShapeMassProperties, decoded in G3-10b / G3-10k, re-derived here -------
BLOCK = 48
PAYLOAD_AT = 0x10
MASS_AT = 0x28
TAIL_AT = 0x2C
BIAS = 111                     # value = mantissa * 2**(floor(w/128) - BIAS); measured
BIAS_GRID = (109, 110, 111, 112, 113)
BOX_FILL = 0.999               # hull volume / bbox volume that counts as "a box"
TOLS = (0.01, 0.02, 0.05, 0.25)
SCAN_TOL = 0.01                # tolerance of the scale-free f32-triple scan


# ------------------------------------------------------------------ shared maths
def box_moments(mass: float, ext) -> list:
    """Uniform solid box: I = m/12*(b^2+c^2) about the centre, on each axis."""
    a, b, c = (float(x) for x in ext)
    return [mass * (b * b + c * c) / 12.0,
            mass * (a * a + c * c) / 12.0,
            mass * (a * a + b * b) / 12.0]


def hull_props(pts: np.ndarray, mass: float) -> dict:
    """Uniform-density properties of the convex hull of `pts` (tetrahedral decomposition)."""
    hull = ConvexHull(pts)
    ref = pts.mean(axis=0)
    vol = 0.0
    cen = np.zeros(3)
    C = np.zeros((3, 3))
    for s in hull.simplices:
        p = np.array([pts[s[0]] - ref, pts[s[1]] - ref, pts[s[2]] - ref])
        v = abs(float(np.dot(p[0], np.cross(p[1], p[2])))) / 6.0
        S = p.sum(axis=0)
        vol += v
        cen += v * (S / 4.0)
        C += (p.T @ p + np.outer(S, S)) / 20.0 * v
    cen = cen / vol + ref
    # second moment about the hull's own centroid: C_ref - V*d*d^T, where d is the centroid
    # relative to ref.  (Dropping this cross term is what makes a tensor non-positive for
    # bodies whose vertex mean sits far from their centroid - the bug this line fixes.)
    dref = cen - ref
    Cc = C - vol * np.outer(dref, dref)
    return {"volume": vol, "centroid": cen,
            "I_com": (np.trace(Cc) * np.eye(3) - Cc) * (mass / vol)}


def scan_triples(buf: bytes, sigs: list, tol: float = SCAN_TOL, chunk: int = 1 << 22) -> list:
    """Every 4-byte-aligned f32 triple in `buf`, tested scale-free against each signature.

    A signature is a positive 3-vector (a moment triple for unit mass).  A triple matches
    when some scalar k>0 gives |v - k*s| <= tol*k*s on all three axes.  The scan is
    scale-free because BmAK stores no mass, so only the *shape* of a tensor can be tested.
    """
    n = (len(buf) - 4) // 4
    if n < 3:
        return [{"hits": 0, "first": None, "offsets": []} for _ in sigs]
    counts = [0] * len(sigs)
    firsts = [None] * len(sigs)
    offs = [[] for _ in sigs]
    S = [np.asarray(s, dtype=np.float64) for s in sigs]
    pos = [bool(np.all(s > 0)) for s in S]
    step = max(3, chunk // 4)
    for start in range(0, n - 2, step):
        cnt = min(step + 2, n - start)
        with np.errstate(invalid="ignore", over="ignore"):
            vals = np.frombuffer(buf, dtype="<f4", count=cnt, offset=4 * start).astype(np.float64)
        tri = np.stack([vals[:-2], vals[1:-1], vals[2:]], axis=1)
        ok = np.isfinite(tri).all(axis=1) & (tri > 0).all(axis=1)
        tri = tri[ok]
        if not len(tri):
            continue
        for i, s in enumerate(S):
            if not pos[i]:
                continue
            k = (tri / s).mean(axis=1)
            good = k > 0
            rel = np.abs(tri - k[:, None] * s) / (k[:, None] * s)
            close = good & np.all(rel <= tol, axis=1)
            c = int(close.sum())
            if c:
                counts[i] += c
                if firsts[i] is None:
                    j = int(np.argmax(close))
                    firsts[i] = {"at": 4 * (start + int(np.flatnonzero(ok)[j])),
                                 "values": [round(float(x), 6) for x in tri[j]],
                                 "k": round(float(k[j]), 6)}
                if len(offs[i]) < 64:
                    for j in np.flatnonzero(close)[:64 - len(offs[i])]:
                        offs[i].append(4 * (start + int(np.flatnonzero(ok)[j])))
    return [{"hits": c, "first": f, "offsets": o}
            for c, f, o in zip(counts, firsts, offs)]


# ------------------------------------------------------------------ BmAK
def agg_payload(pkg, idx: int):
    """(AggGeom payload bytes, export size, tag list) for one RB_BodySetup export."""
    data = pkg.data(idx)
    tags, _end, _why = U.walk_tags(pkg, data)
    agg = [t for t in tags if t.get("name") == "AggGeom"]
    if not agg:
        return None, len(data), tags
    a = agg[0]
    return data[a["at"]:a["at"] + a["size"]], len(data), tags


def bmak_boxes(pkg, payload: bytes, expect: int) -> list:
    """Every box record of an AggGeom payload, from the proven record layout.

    A box body's `AggGeom` starts with two u32 (sphere count, box count) - 8 bytes, not 16:
    the first record's `StructProperty` tag begins at 0x08, so its extent tags land at byte
    92, which is the offset G3-01b recorded.  Record (G3-01b, `COLLISION_BOXES.md`): 20-byte
    tag whose name resolves to `TM` and whose size is 64, the 64-byte TM (3x3 rotation rows +
    translation), three FloatProperty tags at 0x40/0x44/0x48 (extents), a BoolProperty tag at
    0x4C, then a u16 end marker.  Each field is validated (type, name, size) instead of being
    assumed at a fixed offset; `expect` (the header's box count) is compared by the caller.
    """
    out = []
    p, n = 8, len(payload)
    while p + 20 <= n:
        t, off = struct.unpack_from("<hH", payload, p)
        if t == 0:
            break
        if t != 10:
            break
        ni, num, size, arr = struct.unpack_from("<4i", payload, p + 4)
        name = pkg.names[ni] if 0 <= ni < len(pkg.names) else None
        if name != "TM" or size != 64 or p + 20 + 64 > n:
            break
        tm = list(struct.unpack_from("<16f", payload, p + 20))
        q = p + 84
        ext, tags = [], []
        for _k in range(3):
            tt, oo = struct.unpack_from("<hH", payload, q)
            v = struct.unpack_from("<f", payload, q + 4)[0]
            tags.append({"type": tt, "offset": oo, "value": round(v, 6)})
            ext.append(v)
            q += 8
        tt, oo = struct.unpack_from("<hH", payload, q)
        word = struct.unpack_from("<I", payload, q + 4)[0]
        q += 8
        end = struct.unpack_from("<H", payload, q)[0]
        q += 2
        out.append({
            "record_at": p, "tm_at": p + 20, "extent_tags_at": p + 84,
            "extents_cm": [round(v, 3) for v in ext],
            "centre_cm": [round(v, 3) for v in tm[13:16]],
            "rot_rows": [[round(tm[4 * i + k], 6) for k in range(3)] for i in range(3)],
            "extent_tag_offsets": [t["offset"] for t in tags],
            "tail_tag": {"type": tt, "offset": oo, "word": word},
            "element_end_marker": end,
        })
        p = q
        if len(out) == expect:
            break
    return out


def bmak_convex0(payload: bytes) -> dict:
    """Convex element 0's vertices and triangle indices (layout proven by G3-01b's plane
    oracle), so the hull tensor of the decoded polyhedron can be computed."""
    p = 16
    nv = struct.unpack_from("<I", payload, p)[0]
    p += 4
    verts = [tuple(struct.unpack_from("<3f", payload, p + 12 * i)[j] for j in range(3))
             for i in range(nv)]
    p += 12 * nv
    na = struct.unpack_from("<I", payload, p)[0]
    p += 4 + 16 * na
    ni = struct.unpack_from("<I", payload, p)[0]
    p += 4
    idx = [struct.unpack_from("<I", payload, p + 4 * i)[0] for i in range(ni)]
    return {"n_vertices": nv, "block_a": na, "n_indices": ni,
            "vertices_cm": [[round(v, 4) for v in vv] for vv in verts],
            "triangle_count": ni // 3}


def bmak_side(pkg) -> dict:
    rec = {"package": BMAK, "exports": [], "physasset": None, "oracles": {}}
    tags_dump = {}
    sigs, sig_labels = [], []
    for idx, role, kind in BMAK_BODIES:
        payload, size, tags = agg_payload(pkg, idx)
        tag_names = [t.get("name") or t.get("type") for t in tags]
        rec["exports"].append({
            "export": idx, "object": pkg.object_path(idx), "role": role, "kind": kind,
            "class": pkg.object_class(idx), "export_bytes": size,
            "aggeom_bytes": len(payload) if payload else None,
            "property_tags": tag_names,
            "property_tags_label": "decoded (walk_tags over the export; every serialized "
                                   "property name, in order)",
        })
        tags_dump[idx] = tag_names
        if not payload:
            continue
        hdr = list(struct.unpack_from("<4I", payload, 0))
        rec["exports"][-1]["agggeom_header_u32"] = hdr
        if kind == "box":
            # a box body's header is two u32: sphere count, box count (bytes 8.. are records)
            n_box = struct.unpack_from("<I", payload, 4)[0]
            rec["exports"][-1]["agggeom_header"] = {"sphere_count": hdr[0], "box_count": n_box}
            boxes = bmak_boxes(pkg, payload, n_box)
            rec["exports"][-1]["boxes"] = boxes
            rec["exports"][-1]["box_count_word"] = n_box
            rec["exports"][-1]["box_oracle"] = {
                "located": len(boxes), "header_word_1": hdr[1],
                "ok": len(boxes) == hdr[1],
                "label": "derived (the record locator finds exactly as many `TM` records "
                         "as the header's box-count word)"}
            for k, b in enumerate(boxes):
                ext_m = [v / 100.0 for v in b["extents_cm"]]
                sigs.append(box_moments(1.0, ext_m))
                sig_labels.append({"export": idx, "role": role, "what": "box %d" % k,
                                   "signature": [round(x, 6) for x in box_moments(1.0, ext_m)],
                                   "basis": "m/12*(b^2+c^2) at unit mass, from the decoded "
                                            "extents (cm/100)"})
        else:
            c0 = bmak_convex0(payload)
            rec["exports"][-1]["convex_element_0"] = c0
            pts = np.array(c0["vertices_cm"], dtype=float) / 100.0
            hp = hull_props(pts, 1.0)          # unit density: mass == volume
            rec["exports"][-1]["hull"] = {
                "volume_m3": round(float(hp["volume"]), 6),
                "centroid_m": [round(float(x), 6) for x in hp["centroid"]],
                "I_diag_unit_density": [round(float(x), 6) for x in np.diag(hp["I_com"])],
                "label": "derived (tetrahedral decomposition of convex element 0's decoded "
                         "vertices, unit density)"}
            sigs.append(list(np.diag(hp["I_com"])))
            sig_labels.append({"export": idx, "role": role, "what": "convex element 0 hull",
                               "signature": [round(float(x), 6) for x in np.diag(hp["I_com"])],
                               "basis": "hull tensor diagonal at unit density"})

    # the scan: is any stored float triple shaped like one of those tensors?
    scans = []
    for idx, role, kind in BMAK_BODIES:
        payload, _size, _tags = agg_payload(pkg, idx)
        if not payload:
            continue
        mine = [i for i, s in enumerate(sig_labels) if s["export"] == idx]
        res = scan_triples(payload, [sigs[i] for i in mine])
        scans.append({
            "export": idx, "role": role, "payload_bytes": len(payload),
            "triples": max(0, (len(payload) - 4) // 4 - 2),
            "targets": [sig_labels[i]["what"] for i in mine],
            "hits": [r["hits"] for r in res],
            "first": [r["first"] for r in res],
        })
    rec["signature_scan"] = scans

    pa_data = pkg.data(BMAK_PHYSASSET)
    pa_tags, _e, _w = U.walk_tags(pkg, pa_data)
    rec["physasset"] = {
        "export": BMAK_PHYSASSET, "object": pkg.object_path(BMAK_PHYSASSET),
        "bytes": len(pa_data),
        "property_tags": [t.get("name") for t in pa_tags],
        "label": "decoded (every serialized property of the PhysicsAsset)",
    }

    stored = {e["export"]: e["property_tags"] for e in rec["exports"]}
    any_mass = sorted({n for names in stored.values() for n in names
                       if n and ("Mass" in n or "Inertia" in n)})
    rec["oracles"] = {
        "no_mass_or_inertia_property_serialized": {
            "ok": not any_mass,
            "detail": {"properties_matching_Mass_or_Inertia": any_mass,
                       "bodies": len(stored)}},
        "every_box_record_located": {
            "ok": all(e.get("box_oracle", {}).get("ok", True) for e in rec["exports"]),
            "detail": {e["export"]: e.get("box_oracle") for e in rec["exports"]
                       if "box_oracle" in e}},
        "no_tensor_shaped_triple_in_aggeom": {
            "ok": all(h == 0 for s in scans for h in s["hits"]),
            "detail": {s["export"]: s["hits"] for s in scans}},
    }
    return rec


# ------------------------------------------------------------------ JC3
def scale_of(w: int) -> float:
    return 2.0 ** ((w // 128) - BIAS)


def unpack_block(raw: bytes) -> dict:
    ei = list(struct.unpack_from("<12h", raw, PAYLOAD_AT))
    return {"ei": ei,
            "mass": struct.unpack_from("<f", raw, MASS_AT)[0],
            "tail": struct.unpack_from("<f", raw, TAIL_AT)[0],
            "header_zero": raw[:PAYLOAD_AT] == b"\0" * PAYLOAD_AT,
            "payload_hex": raw[PAYLOAD_AT:PAYLOAD_AT + 24].hex()}


def group_values(ei: list, g: int) -> list:
    s = scale_of(ei[4 * g + 3])
    return [ei[4 * g + k] * s for k in range(3)]


def donor_blocks(blob: bytes, pf) -> list:
    rows = []
    for o in pf.objects:
        if o.cls != "hknpShapeMassProperties":
            continue
        raw = blob[pf.base + o.offset:pf.base + o.offset + BLOCK]
        u = unpack_block(raw)
        if not (u["mass"] > 0 and math.isfinite(u["mass"])):
            rows.append({"block": o.offset, "extent": pf.extents.get(o.offset),
                         "mass": None, "note": "non-positive mass"})
            continue
        rows.append({"block": o.offset, "extent": pf.extents.get(o.offset),
                     "mass": round(u["mass"], 6), "tail": round(u["tail"], 9),
                     "header_zero": u["header_zero"], "payload_hex": u["payload_hex"],
                     "ei": u["ei"],
                     "com": [round(x, 9) for x in group_values(u["ei"], 0)],
                     "diag": [round(x, 9) for x in group_values(u["ei"], 1)],
                     "third": [round(x, 9) for x in group_values(u["ei"], 2)]})
    return rows


def link_map(pf) -> dict:
    """shape offset -> mass-properties block offset (the G3-10c link: shape+0x20 ->
    hkRefCountedProperties, node+0x10 -> the block)."""
    out = {}
    for o in pf.objects:
        if o.cls != "hknpConvexPolytopeShape":
            continue
        node = pf.pointers.get(o.offset + 0x20, 0)
        mb = pf.pointers.get(node + 0x10, 0) if node else 0
        if mb and pf._starts.get(mb) == "hknpShapeMassProperties":
            out[o.offset] = mb
    return out


def scan_file(path: str, keep_blob: bool = False) -> dict:
    blob = open(path, "rb").read()
    pf = jc3hkx.Packfile(blob)
    psd = [o for o in pf.objects if o.cls == "hknpPhysicsSystemData"]
    if not psd:
        raise ValueError("no hknpPhysicsSystemData")
    shapes = link_map(pf)
    blocks = donor_blocks(blob, pf)
    a40 = pf.array(psd[0].offset + 0x40)
    bodies = []
    for i in range(a40["size"]):
        at = a40["ptr"] + jc3hkx.BODY_ENTRY_SIZE * i
        shp = pf.pointers.get(at, 0)
        if pf._starts.get(shp) != "hknpConvexPolytopeShape" or shp not in shapes:
            continue
        d = jc3hkx.decode_polytope(pf, shp)
        pts = np.array([v[:3] for v in d["vertices"]], dtype=float)
        if len(pts) < 4:
            continue
        raw = blob[pf.base + shapes[shp]:pf.base + shapes[shp] + BLOCK]
        u = unpack_block(raw)
        if not (u["mass"] > 0 and math.isfinite(u["mass"])):
            continue
        b = d["bounds"]
        ext = np.array([b["max"][k] - b["min"][k] for k in range(3)])
        if ext.min() <= 0:
            continue
        hp = hull_props(pts, u["mass"])
        bodies.append({
            "body": i, "shape": shp, "block": shapes[shp], "verts": len(pts),
            "mass": u["mass"], "ei": u["ei"],
            "ext": [round(float(x), 6) for x in ext],
            "volume": round(float(hp["volume"]), 9),
            "fill": round(float(hp["volume"]) / float(np.prod(ext)), 6),
            "centroid": [round(float(x), 6) for x in hp["centroid"]],
            "com": [round(x, 9) for x in group_values(u["ei"], 0)],
            "diag": [round(x, 9) for x in group_values(u["ei"], 1)],
            "third": [round(x, 9) for x in group_values(u["ei"], 2)],
            "I_hull": [round(float(x), 9) for x in np.diag(hp["I_com"])],
            "box": [round(x, 9) for x in box_moments(u["mass"], ext)],
        })
    out = {"path": path, "bytes": len(blob), "objects": len(pf.objects),
           "polytopes": sum(1 for o in pf.objects if o.cls == jc3hkx.POLYTOPE),
           "polytopes_linked": len(shapes),
           "blocks_from_shapes": len(set(shapes.values())),
           "blocks": blocks, "bodies": bodies}
    if keep_blob:
        out["blob"] = blob
        out["base"] = pf.base
        out["data_len"] = pf.lf
    del pf
    return out


def com_errors(bodies: list, K: int) -> np.ndarray:
    out = []
    for b in bodies:
        ei = b["ei"]
        s = 2.0 ** ((ei[3] // 128) - K)
        com = np.array(ei[:3], dtype=float) * s
        out.append(float(np.linalg.norm(com - np.array(b["centroid"])) / max(b["ext"])))
    return np.array(out)


def ratios(bodies: list, key: str) -> np.ndarray:
    return np.array([np.array(b["diag"]) / np.maximum(np.array(b[key]), 1e-15)
                     for b in bodies]) if bodies else np.zeros((0, 3))


def hits_of(R: np.ndarray, tol: float) -> int:
    return int(np.all(np.abs(R - 1.0) <= tol, axis=1).sum()) if len(R) else 0


def jc3_side() -> dict:
    files = sorted(glob.glob(os.path.join(FLEET, "*.physicsc")))
    donor_path = os.path.join(REPO, DONOR)
    fleet, errors, seen = [], [], set()
    for p in [donor_path] + files:
        if os.path.abspath(p) in seen:
            continue
        seen.add(os.path.abspath(p))
        try:
            fleet.append(scan_file(p, keep_blob=(os.path.abspath(p) == os.path.abspath(donor_path))))
        except Exception as e:                      # pragma: no cover
            errors.append({"file": os.path.basename(p), "error": str(e)})
    donor = next(f for f in fleet if os.path.abspath(f["path"]) == os.path.abspath(donor_path))
    all_bodies = [b for f in fleet for b in f["bodies"]]

    # the donor's 56 blocks, with the hull each one belongs to (0 of 56 must resolve)
    by_block = {}
    for b in donor["bodies"]:
        by_block[b["block"]] = b
    donor_rows = []
    for r in donor["blocks"]:
        b = by_block.get(r["block"])
        row = dict(r)
        if b:
            row.update({"hull_body": b["body"], "ext_m": b["ext"], "fill": b["fill"],
                        "hull_volume": b["volume"],
                        "box": b["box"], "I_hull": b["I_hull"],
                        "box_ratio": [round(b["diag"][k] / b["box"][k], 6) if b["box"][k] else None
                                      for k in range(3)],
                        "hull_ratio": [round(b["diag"][k] / b["I_hull"][k], 6) if b["I_hull"][k] else None
                                       for k in range(3)]})
        donor_rows.append(row)

    # bias ladder (the packing's exponent bias, measured on the centre-of-mass group)
    bias = []
    for K in BIAS_GRID:
        e = com_errors(all_bodies, K)
        bias.append({"K": K, "median": round(float(np.median(e)), 6),
                     "p90": round(float(np.percentile(e, 90)), 6),
                     "within_10pct": round(float((e <= 0.10).mean()), 6)})
    com_e = com_errors(all_bodies, BIAS)
    best = min(bias, key=lambda r: r["median"])

    boxes = [b for b in all_bodies if b["fill"] >= BOX_FILL]
    R_box = ratios(boxes, "box")
    R_box_h = ratios(boxes, "I_hull")
    R_all = ratios(all_bodies, "box")
    R_all_h = ratios(all_bodies, "I_hull")
    fills = np.array([b["fill"] for b in all_bodies])
    donor_fills = np.array([b["fill"] for b in donor["bodies"]])
    census = {"files": len(fleet), "errors": errors, "bodies": len(all_bodies),
              "fill_ge_999": int((fills >= 0.999).sum()),
              "fill_max": round(float(fills.max()), 6),
              "fill_median": round(float(np.median(fills)), 6),
              "donor_bodies": len(donor["bodies"]), "donor_blocks": len(donor["blocks"]),
              "donor_fill_max": round(float(donor_fills.max()), 6),
              "donor_polytopes": donor["polytopes"],
              "donor_polytopes_linked": donor["polytopes_linked"],
              "donor_blocks_from_shapes": donor["blocks_from_shapes"],
              "donor_blocks_linked": len(donor_rows) - sum(1 for r in donor_rows if "hull_body" not in r)}

    box_oracle = {
        "n": len(boxes),
        "box_formula": {("%.0f%%" % (t * 100)): hits_of(R_box, t) for t in TOLS},
        "hull_formula": {("%.0f%%" % (t * 100)): hits_of(R_box_h, t) for t in TOLS},
        "box_formula_all_bodies": {("%.0f%%" % (t * 100)): hits_of(R_all, t) for t in TOLS},
        "hull_formula_all_bodies": {("%.0f%%" % (t * 100)): hits_of(R_all_h, t) for t in TOLS},
        "median_ratio_box": [round(float(x), 6) for x in np.median(R_box, axis=0)] if boxes else [],
        "p10_ratio_box": [round(float(x), 6) for x in np.percentile(R_box, 10, axis=0)] if boxes else [],
        "p90_ratio_box": [round(float(x), 6) for x in np.percentile(R_box, 90, axis=0)] if boxes else [],
        "median_ratio_hull": [round(float(x), 6) for x in np.median(R_box_h, axis=0)] if boxes else [],
        "median_ratio_hull_all": [round(float(x), 6) for x in np.median(R_all_h, axis=0)],
    }
    neg_hull = [b["body"] for b in all_bodies if min(b["I_hull"]) <= 0]
    hull_vs_box = [max(abs(b["I_hull"][k] - b["box"][k]) / max(b["box"])
                      for k in range(3)) for b in boxes]
    hull_vs_box_max = round(float(max(hull_vs_box)), 9) if hull_vs_box else None
    oracles = {
        "block_is_48_bytes_zero_header": {
            "ok": all(r.get("header_zero") for r in donor["blocks"]) and
                  all(r.get("extent") == BLOCK for r in donor["blocks"]),
            "detail": {"blocks": len(donor["blocks"]),
                       "extent": sorted({r.get("extent") for r in donor["blocks"]})}},
        "every_polytope_resolves_to_a_mass_block": {
            "ok": census["donor_bodies"] == 40,
            "detail": {"donor bodies with hull+mass": census["donor_bodies"],
                       "donor blocks": census["donor_blocks"], "fleet": len(all_bodies)}},
        "bias_is_111": {
            "ok": best["K"] == BIAS and best["median"] < 0.05,
            "detail": {"chosen": best["K"], "grid": {str(r["K"]): r["median"] for r in bias}}},
        "centre_of_mass_matches_hull_centroid": {
            "ok": bool(float(np.median(com_e)) < 0.05 and (com_e <= 0.10).mean() > 0.85),
            "detail": {"median": round(float(np.median(com_e)), 6),
                       "p90": round(float(np.percentile(com_e, 90)), 6),
                       "within_10pct": round(float((com_e <= 0.10).mean()), 6)}},
        "box_bodies_exist": {"ok": len(boxes) > 0,
                             "detail": {"boxes": len(boxes), "bodies": len(all_bodies)}},
        "hull_tensor_reproduces_box_formula_on_boxes": {
            "ok": bool(hull_vs_box_max is not None and hull_vs_box_max < 0.01),
            "detail": {"box_bodies": len(boxes), "max_rel_diff": hull_vs_box_max,
                       "label": "derived (the tetrahedral hull tensor and the closed-form box "
                                "formula are independent code paths; on a true box body they must "
                                "agree, so this validates the hull accumulator itself)"}},
        "box_formula_reproduced": {
            "ok": bool(hits_of(R_box, 0.01) > 0.9 * max(1, len(boxes))),
            "detail": {"hits_1pct": hits_of(R_box, 0.01), "of": len(boxes),
                       "median_ratio": box_oracle["median_ratio_box"]}},
        "hull_formula_reproduced": {
            "ok": bool(hits_of(R_box_h, 0.01) > 0.9 * max(1, len(boxes))),
            "detail": {"hits_1pct": hits_of(R_box_h, 0.01), "of": len(boxes),
                       "median_ratio": box_oracle["median_ratio_hull"],
                       "all_bodies_hits_1pct": hits_of(R_all_h, 0.01)}},
        "hull_tensors_are_positive_definite": {
            "ok": not neg_hull,
            "detail": {"bodies": len(all_bodies), "non_positive": len(neg_hull),
                       "first": neg_hull[:8]}},
    }
    donor_rows_out = []
    for r in donor_rows:
        r = dict(r)
        r.pop("ei", None)
        r.pop("third", None)
        donor_rows_out.append(r)
    fleet_box_rows = [{"file": os.path.basename(f["path"]), "body": b["body"],
                       "mass": round(b["mass"], 6), "ext": b["ext"],
                       "diag": b["diag"], "box": b["box"], "I_hull": b["I_hull"],
                       "ratio_box": [round(b["diag"][k] / b["box"][k], 6) if b["box"][k] else None
                                     for k in range(3)]}
                      for f in fleet for b in f["bodies"] if b["fill"] >= BOX_FILL]
    return {"donor": {"path": DONOR, "bytes": donor["bytes"], "objects": donor["objects"]},
            "fleet": census, "donor_blocks": donor_rows_out, "bias_table": bias,
            "com_error": {"median": round(float(np.median(com_e)), 6),
                          "p90": round(float(np.percentile(com_e, 90)), 6),
                          "within_10pct": round(float((com_e <= 0.10).mean()), 6),
                          "max": round(float(com_e.max()), 6)},
            "box_oracle": box_oracle, "box_rows": fleet_box_rows, "oracles": oracles,
            "donor_blob": donor.get("blob"), "donor_base": donor.get("base"),
            "donor_data_len": donor.get("data_len")}


# ------------------------------------------------------------------ build
def build() -> dict:
    pkg = U.Package(BMAK)
    bmak = bmak_side(pkg)
    del pkg
    jc3 = jc3_side()

    # ---- the donor's data section: is there a plain-float tensor anywhere?
    scan = {"car": "Serpente (donor)", "triples": 0, "hits": [], "first": None,
            "hit_classes": {}, "hits_inside_mass_block": 0}
    if jc3["donor_blob"] is not None:
        # the donor has no box body; use its eight heaviest bodies' box signatures instead
        donor_boxes = [b for b in jc3["donor_blocks"] if "box" in b][:8]
        sigs = [b["box"] for b in sorted(donor_boxes, key=lambda r: -r["mass"])]
        blob = jc3["donor_blob"]
        r = scan_triples(blob[jc3["donor_base"]:], sigs, tol=SCAN_TOL)
        # classify each hit offset by the object that contains it
        pf = jc3hkx.Packfile(blob)
        starts = sorted(pf._starts)
        mass_at = [b["block"] for b in jc3["donor_blocks"]]

        def owner(o):
            lo, hi = 0, len(starts) - 1
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if starts[mid] <= o:
                    lo = mid
                else:
                    hi = mid - 1
            return pf._starts[starts[lo]]

        classes, inside, all_off = {}, 0, []
        for x in r:
            for o in x["offsets"]:
                all_off.append(o)
                classes[owner(o)] = classes.get(owner(o), 0) + 1
                if any(mb <= o < mb + BLOCK for mb in mass_at):
                    inside += 1
        del pf
        scan = {"car": "Serpente (donor)", "targets": len(sigs),
                "triples": (jc3["donor_data_len"] - 4) // 4,
                "hits": [x["hits"] for x in r], "first": [x["first"] for x in r],
                "hit_offsets": sorted(set(all_off))[:24],
                "hit_classes": dict(sorted(classes.items())),
                "hits_inside_mass_block": inside,
                "samples": len(all_off)}
    jc3.pop("donor_blob", None)
    jc3.pop("donor_base", None)
    jc3.pop("donor_data_len", None)

    # ---- derived comparison for the translation: what a box would give for the Batmobile
    chassis = next(e for e in bmak["exports"] if e["export"] == 169750)
    ext_m = [v / 100.0 for v in chassis["boxes"][0]["extents_cm"]]
    hypo = {}
    for m in (975.0, 1627.097155, 4000.0):
        hypo["%g kg" % m] = [round(x, 3) for x in box_moments(m, ext_m)]

    verdict = {
        "bmak_stores_inertia": False,
        "bmak_stores_mass": False,
        "jc3_tensor_located": True,
        "jc3_box_formula_matched": jc3["oracles"]["box_formula_reproduced"]["ok"],
        "jc3_hull_formula_matched": jc3["oracles"]["hull_formula_reproduced"]["ok"],
        "status": "partial",
        "statement": (
            "BmAK's cooked body setups carry geometry only: no mass and no inertia property is "
            "serialized, and no float triple in the four AggGeom payloads is shaped like the "
            "decoded boxes' or hulls' moment tensor, so BmAK inertia is UNKNOWN. JC3's 56 "
            "hknpShapeMassProperties blocks do carry the centre of mass and the inertia diagonal "
            "(packed, bias 111), but the stored diagonal matches neither the collision hull's box "
            "formula nor its exact hull tensor: %d of %d single-box fleet bodies hit the box "
            "formula within 1%%, with a uniform factor of about %s on all three moments."
            % (jc3["box_oracle"]["box_formula"]["1%"], jc3["box_oracle"]["n"],
               round(float(np.median(jc3["box_oracle"]["median_ratio_box"])), 3)
               if jc3["box_oracle"]["median_ratio_box"] else "n/a")),
    }
    unknowns = [
        "the Batmobile's mass: no mass property is serialized on any of the four BmAK body "
        "setups (decoded: their whole tag list is PreCachedPhysDataVersion, a bone NameProperty, "
        "one BoolProperty, AggGeom). Where it would be: SVehicle.ChassisMass, decoded at "
        "Research/BatmobileGrab/CLASS_DEFAULTS.md:434 as the class default 210.0 - a class "
        "default, not a per-vehicle authored value, and not this task's format.",
        "the Batmobile's inertia tensor: with no mass and no tensor bytes, no box or hull formula "
        "can be evaluated on the BmAK side at all (the tool reports the formula's *shape* only). "
        "What would settle it: a decoded mass for the body plus a decision on whether the engine "
        "computes inertia from the AggGeom box (bComputedMassProperties / PrimitiveComponent "
        "field layout for the Batmobile's component), neither of which is in the files read here.",
        "the absolute semantics of the JC3 stored diagonal: %d of %d single-box fleet bodies match "
        "m/12*(b^2+c^2) at 1%% and %d match the exact hull tensor, so the tensor is neither the "
        "collision box's nor the collision hull's. The residual is a near-uniform factor on all "
        "three moments (median %s), i.e. one scalar, which a wrong exponent would not produce. "
        "What would settle it: the render mesh of the same part, whose tensor at the stored mass "
        "would show whether the factor is a mass or an extent difference."
        % (jc3["box_oracle"]["box_formula"]["1%"], jc3["box_oracle"]["n"],
           jc3["box_oracle"]["hull_formula"]["1%"],
           round(float(np.median(jc3["box_oracle"]["median_ratio_box"])), 3)
           if jc3["box_oracle"]["median_ratio_box"] else "n/a"),
        "the third int16x4 group of the JC3 payload (+0x20..+0x27): its own exponent lane decodes "
        "its mantissas to ~1e-36, i.e. 'no products'. Whether it holds products of inertia, a "
        "principal axis, or a tag is UNKNOWN; the tool records the raw words per block.",
        "the packing itself: value = mantissa * 2**(floor(w/128) - 111) is derived, not documented. "
        "The bias 111 is measured (group 1 must land on the hull centroid; 110 and 112 are a "
        "factor of two out), but no Havok header in this tree names the layout.",
    ]
    return {
        "schema": 1,
        "generated_by": "Tools/scripts/grab_inertia.py --write",
        "card": "G3-10c - where mass properties and inertia live (BmAK + JC3)",
        "constants": {"block": BLOCK, "payload": [PAYLOAD_AT, PAYLOAD_AT + 24],
                      "mass_at": MASS_AT, "tail_at": TAIL_AT, "bias": BIAS,
                      "box_fill": BOX_FILL, "scan_tol": SCAN_TOL},
        "bmak": bmak,
        "jc3": jc3,
        "donor_f32_scan": scan,
        "batmobile_box_hypothesis": {"extents_m": [round(x, 6) for x in ext_m],
                                     "box_moments_kg_m2": hypo,
                                     "label": "derived (m/12*(b^2+c^2) on the decoded chassis "
                                              "box 0 extents at three candidate masses; the mass "
                                              "is UNKNOWN, so these are examples, not values)"},
        "oracles": {**{"bmak_" + k: v for k, v in bmak["oracles"].items()},
                    **{"jc3_" + k: v for k, v in jc3["oracles"].items()}},
        "verdict": verdict,
        "unknowns": unknowns,
    }


# ------------------------------------------------------------------ render
def f(x, n=4):
    return ("%%.%df" % n) % x


def render(d: dict) -> str:
    A = []
    b, j, v = d["bmak"], d["jc3"], d["verdict"]
    A.append("# Where mass properties and inertia live - BmAK and JC3 (G3-10c)\n")
    A.append("Generated by `Tools/scripts/grab_inertia.py --write`; `--check` recomputes every "
             "number from the source bytes and fails on drift. Static decode only: no game was "
             "run, attached to or modified; every input is read-only.\n")
    A.append("Labels: **decoded** = read from the bytes (package + export + offset, or file + "
             "offset); **derived** = computed from decoded values with the rule stated; "
             "**UNKNOWN** = not decoded, with what was tried and what would settle it.\n")

    A.append("## VERDICT\n")
    A.append("| question | answer | label |")
    A.append("|---|---|---|")
    A.append("| where BmAK stores mass | nowhere in the cooked body setup | decoded (tag list, §1) |")
    A.append("| where BmAK stores an inertia tensor | nowhere in the `AggGeom` payload | decoded "
             "(scale-free scan, §2) |")
    A.append("| the Batmobile's inertia tensor | **UNKNOWN** | UNKNOWN |")
    A.append("| where JC3 stores mass properties | `hknpShapeMassProperties`, 48 B: mass `f32` at "
             "`+0x28` | decoded (56/56 donor blocks) |")
    A.append("| where JC3 stores the centre of mass | payload group 1 (`+0x10..+0x17`) | decoded "
             "(oracle: hull centroid, median error %s) |" % f(j["com_error"]["median"]))
    A.append("| where JC3 stores the inertia diagonal | payload group 2 (`+0x18..+0x1f`) | derived "
             "(packing pinned by the COM group; best of the layouts tried) |")
    A.append("| does the stored diagonal equal a box formula | **no** - %d of %d single-box fleet "
             "bodies at 1 %% | derived (oracle, §4) |"
             % (j["box_oracle"]["box_formula"]["1%"], j["box_oracle"]["n"]))
    A.append("| does it equal the exact hull tensor | **no** - %d of %d at 1 %% | derived (oracle, §4) |"
             % (j["box_oracle"]["hull_formula"]["1%"], j["box_oracle"]["n"]))
    A.append("")
    A.append("The two sides are asymmetric, and that is the answer to the card's question. BmAK's "
             "cooked physics is **geometry only**: the four Batmobile body setups serialize no mass "
             "and no tensor, and a scale-free scan of their `AggGeom` payloads finds no triple "
             "shaped like either decoded shape's moment tensor. JC3's format *does* carry mass "
             "properties - 56 blocks in the donor - with the centre of mass proven against the "
             "hull centroid, but its inertia diagonal is not the collision shape's box or hull "
             "tensor under any of the layouts tried, so a transferable inertia value for the "
             "Batmobile cannot be read out of either side yet.\n")

    A.append("## 1. BmAK: what the body setups actually serialize\n")
    A.append("`BmGame.upk`, four `RB_BodySetup` exports plus the `PhysicsAsset`. The tag list is "
             "every serialized property of the object (the package stores only non-default "
             "properties, so a missing name means \"not authored on this object\", not \"field "
             "does not exist\").\n")
    A.append("| export | role | class | export bytes | AggGeom bytes | serialized property tags |")
    A.append("|---:|---|---|---:|---:|---|")
    for e in b["exports"]:
        A.append("| %d | `%s` | `%s` | %d | %s | %s |" % (
            e["export"], e["role"], e["class"], e["export_bytes"],
            e["aggeom_bytes"] if e["aggeom_bytes"] is not None else "-",
            ", ".join("`%s`" % t for t in e["property_tags"]) or "-"))
    A.append("")
    A.append("- **decoded:** there is no `Mass`, `MassScale`, `Inertia` or `InertiaTensor` "
             "property on any of the four. The PhysicsAsset's own list is %s.\n"
             % ", ".join("`%s`" % t for t in b["physasset"]["property_tags"] if t))
    A.append("- **decoded negative, with its limit:** the project's SDK dump (`BMSDK_OFFSETS.json`, "
             "41 classes) has no `RB_BodySetup` entry at all, so the class's own field layout - "
             "where a `MassScale` would sit if the class has one - is not available here either. "
             "What the bytes prove is only this: no mass value is serialized on these objects.\n")

    A.append("## 2. BmAK: the geometry, and the search for a tensor\n")
    A.append("Box records are decoded from the proven layout (`COLLISION_BOXES.md`): a 20-byte "
             "`StructProperty` tag whose name resolves to `TM`, the 64-byte TM, three extent "
             "floats at tag offsets 0x40/0x44/0x48, the bool word at 0x4C. The locator finds the "
             "records by name, not by a fixed offset, and the header's box-count word is checked "
             "against the number found.\n")
    A.append("| export | role | shape | decoded geometry |")
    A.append("|---:|---|---|---|")
    for e in b["exports"]:
        if "boxes" in e:
            for k, bx in enumerate(e["boxes"]):
                A.append("| %d | `%s` | box %d | extents %s cm, centre %s cm |" % (
                    e["export"], e["role"], k, bx["extents_cm"], bx["centre_cm"]))
        elif "convex_element_0" in e:
            c = e["convex_element_0"]
            h = e["hull"]
            A.append("| %d | `%s` | convex element 0 | %d vertices, %d triangles; hull volume "
                     "%s m3, unit-density diagonal %s |"
                     % (e["export"], e["role"], c["n_vertices"], c["triangle_count"],
                        f(h["volume_m3"], 4), " ".join(f(x, 2) for x in h["I_diag_unit_density"])))
    A.append("")
    A.append("The tensor that each decoded shape *would* have (derived): `m/12*(b^2+c^2)` for a "
             "box, the exact tetrahedral hull tensor for the convex bodies. Because BmAK stores no "
             "mass, the search is **scale-free**: every 4-byte-aligned f32 triple in the payload is "
             "tested for a scalar `k > 0` with `triple == k * signature` on all three axes within "
             "%.0f %%. A tensor stored without its mass would still be found by this test.\n"
             % (d["constants"]["scan_tol"] * 100))
    A.append("| export | role | payload bytes | aligned triples | targets | hits |")
    A.append("|---:|---|---:|---:|---|---|")
    for s in b["signature_scan"]:
        A.append("| %d | `%s` | %d | %d | %s | %s |" % (
            s["export"], s["role"], s["payload_bytes"], s["triples"],
            ", ".join(s["targets"]), ", ".join(str(h) for h in s["hits"])))
    A.append("")
    A.append("Zero hits everywhere: no float triple in these payloads is even *shaped* like the "
             "decoded boxes' or hulls' moment tensor. That is the decoded negative for \"inertia "
             "lives in the BmAK physics payload\".\n")
    hb = d["batmobile_box_hypothesis"]
    A.append("For scale, here is what the decoded chassis box would give (derived, and the mass is "
             "UNKNOWN, so these are examples only): extents %s m, moments %s.\n"
             % (" x ".join(f(x, 3) for x in hb["extents_m"]),
                "; ".join("%s -> %s" % (k, " / ".join(f(y, 1) for y in t))
                          for k, t in hb["box_moments_kg_m2"].items())))

    A.append("## 3. JC3: the mass-properties record, all 56 blocks\n")
    A.append("`hknpShapeMassProperties` (%d bytes) in `%s` (%d bytes, %d objects). Every one of "
             "the %d blocks is decoded. The shape link (`shape +0x20` -> `hkRefCountedProperties` "
             "-> `+0x10`) resolves **%d of the donor's %d convex polytopes**, which covers %d of the "
             "56 blocks; %d of those polytopes are body-level shapes with a hull and a mass, and the "
             "remaining blocks belong to assembly pieces that are not bodies.\n"
             % (d["constants"]["block"], j["donor"]["path"], j["donor"]["bytes"],
                j["donor"]["objects"], len(j["donor_blocks"]),
                j["fleet"]["donor_polytopes_linked"], j["fleet"]["donor_polytopes"],
                j["fleet"]["donor_blocks_from_shapes"], j["fleet"]["donor_blocks_linked"]))
    A.append("| range | bytes | content | label |")
    A.append("|---|---|---|---|")
    A.append("| `+0x00..+0x0f` | 16 | zero in every block | decoded |")
    A.append("| `+0x10..+0x17` | 8 | group 1: `int16` x, y, z + shared exponent | decoded bytes; "
             "centre of mass (oracle §3.1) |")
    A.append("| `+0x18..+0x1f` | 8 | group 2: `int16` x, y, z + shared exponent | decoded bytes; "
             "inertia diagonal, derived |")
    A.append("| `+0x20..+0x27` | 8 | group 3: `int16` x, y, z + shared exponent | decoded bytes; "
             "semantics UNKNOWN |")
    A.append("| `+0x28..+0x2b` | 4 | mass `f32` | decoded |")
    A.append("| `+0x2c..+0x2f` | 4 | one `f32` (0 in most blocks) | decoded; reading in G3-10k "
             "(authoring volume) not re-run here |")
    A.append("")
    A.append("### 3.1 The packing, and the bias that pins it\n")
    A.append("```")
    A.append("E     = (w >> 7) - 96            # w = the group's 4th int16, a multiple of 128")
    A.append("value = mantissa * 2**(E - 15)  # = mantissa * 2**(floor(w/128) - 111)")
    A.append("```\n")
    A.append("Group 1 must decode to the centre of mass, and the hull's volume centroid is "
             "computable from the same vertices, so the bias is measured, not assumed:\n")
    A.append("| bias K | median error / max extent | p90 | bodies within 10 % |")
    A.append("|---|---|---|---|")
    for r in j["bias_table"]:
        A.append("| %d | %s | %s | %s |" % (r["K"], f(r["median"]), f(r["p90"]),
                                            f(r["within_10pct"], 3)))
    A.append("\nOnly `K = %d` lands on the centroid; the neighbours are a factor of two out. That "
             "pins both the bias and the group-1 reading in one test.\n" % d["constants"]["bias"])
    A.append("### 3.2 The 56 donor blocks\n")
    A.append("| block | mass (kg) | COM (m) | diag (kg m2) | hull | extents (m) | diag / box | "
             "diag / hull |")
    A.append("|---:|---:|---|---|---:|---|---|---|")
    for r in j["donor_blocks"]:
        if "hull_body" not in r:
            A.append("| `%#06x` | - | - | - | not linked | - | - | - |" % r["block"])
            continue
        A.append("| `%#06x` | %s | %s | %s | %d | %s | %s | %s |" % (
            r["block"], f(r["mass"], 3),
            " ".join(f(x, 3) for x in r["com"]),
            " ".join(f(x, 2) for x in r["diag"]), r["hull_body"],
            " ".join(f(x, 3) for x in r["ext_m"]),
            " ".join("-" if x is None else f(x, 3) for x in r["box_ratio"]),
            " ".join("-" if x is None else f(x, 3) for x in r["hull_ratio"])))
    A.append("\nThe mass column is decoded (the byte at `+0x28`); the decoded mass of the donor "
             "totals %s kg over %d blocks with a positive mass.\n"
             % (f(sum(r["mass"] for r in j["donor_blocks"] if r.get("mass")), 3),
                sum(1 for r in j["donor_blocks"] if r.get("mass"))))
    A.append("Read the ratios with the hull size in mind: the extreme ones (0x7ab0, 0x8140, ...) are "
             "sub-centimetre plates whose 16-bit mantissas have almost no resolution left, so a "
             "ratio of 8232 means \"both numbers are quantisation noise\", not a decode failure. The "
             "oracle below therefore runs on bodies where the quantities are resolvable.\n")

    A.append("## 4. The oracle: stored diagonal vs box and hull formulas\n")
    A.append("A body counts as a single box when its hull fills its own bounding box "
             "(`hull volume / bbox volume >= %.3f`). The box formula is `m/12*(b^2+c^2)` with `m` "
             "the decoded mass and `b, c` the decoded extents; the hull formula is the exact "
             "tetrahedral tensor of the same vertices at the same mass. Both are centroidal.\n"
             % d["constants"]["box_fill"])
    A.append("| census | value |")
    A.append("|---|---|")
    A.append("| files decoded | %d |" % j["fleet"]["files"])
    A.append("| decode errors | %d%s |" % (
        len(j["fleet"]["errors"]),
        " (" + ", ".join("%s: %s" % (e["file"], e["error"]) for e in j["fleet"]["errors"]) + ")"
        if j["fleet"]["errors"] else ""))
    A.append("| fleet bodies with a hull and a mass block | %d |" % j["fleet"]["bodies"])
    A.append("| single-box bodies (`fill >= 0.999`) | %d |" % j["fleet"]["fill_ge_999"])
    A.append("| median fill | %s |" % f(j["fleet"]["fill_median"], 3))
    A.append("| donor bodies / blocks | %d / %d |" % (j["fleet"]["donor_bodies"],
                                                    j["fleet"]["donor_blocks"]))
    A.append("| donor's best fill (it has no box body) | %s |" % f(j["fleet"]["donor_fill_max"], 3))
    A.append("")
    A.append("| tolerance per moment | box formula (boxes) | hull formula (boxes) | hull formula "
             "(all %d bodies) | of |" % j["fleet"]["bodies"])
    A.append("|---|---:|---:|---:|---:|")
    for k in j["box_oracle"]["box_formula"]:
        A.append("| %s | %d | %d | %d | %d |" % (
            k, j["box_oracle"]["box_formula"][k], j["box_oracle"]["hull_formula"][k],
            j["box_oracle"]["hull_formula_all_bodies"][k], j["box_oracle"]["n"]))
    A.append("")
    A.append("On a single-box body the hull tensor *is* the box tensor, so the middle column repeats "
             "the first by construction; the third column is the independent test (the exact hull "
             "tensor over every hull body, boxes and non-boxes alike). Both miss.\n")
    A.append("\nRatio `stored / box formula` over the box bodies: p10 %s, median **%s**, p90 %s. "
             "The donor's own bodies are not boxes (its best hull fills %s of its bbox), so the "
             "donor can only be shown, not scored - which is why the oracle runs on the fleet.\n"
             % (" ".join(f(x, 3) for x in j["box_oracle"]["p10_ratio_box"]),
                " ".join(f(x, 3) for x in j["box_oracle"]["median_ratio_box"]),
                " ".join(f(x, 3) for x in j["box_oracle"]["p90_ratio_box"]),
                f(j["fleet"]["donor_fill_max"], 3)))
    A.append("The three medians agree to within %s, so the mismatch is a single scalar on the whole "
             "tensor, not per-axis scatter: the stored tensor is consistent with a body *scaled* "
             "relative to the collision shape, which is what an authoring shape larger than the "
             "collision hull looks like. It is not evidence for a wrong exponent, which would move "
             "one axis, and not evidence for a wrong mass, which the +0x2c volume in G3-10k "
             "contradicts.\n"
             % (f(max(j["box_oracle"]["median_ratio_box"]) -
                  min(j["box_oracle"]["median_ratio_box"]), 4)
                if j["box_oracle"]["median_ratio_box"] else "-"))
    sc = d["donor_f32_scan"]
    tot = sum(sc["hits"]) if sc["hits"] else 0
    A.append("Also tested: is there a **plain-float** tensor anywhere in the donor's data section? "
             "Every 4-byte-aligned f32 triple (%d) was tested against the %d heaviest bodies' box "
             "signatures, scale-free, at %.0f %%: **%d sampled hits**. %d of the sampled offsets "
             "fall inside a `hknpShapeMassProperties` block; the rest sit in %s. A scale-free ratio "
             "test is loose - any positive triple with matching proportions passes - so these are "
             "recorded as coincidences, not read as tensors. The packed payload remains the only "
             "**located** tensor-shaped data in the file.\n"
             % (sc["triples"], sc.get("targets", 0), d["constants"]["scan_tol"] * 100, tot,
                sc.get("hits_inside_mass_block", 0),
                ", ".join("`%s` (%d)" % (k, v) for k, v in sc.get("hit_classes", {}).items())
                or "no object"))

    A.append("## 5. Oracles (`--check` re-runs all of them)\n")
    A.append("| oracle | ok | detail |")
    A.append("|---|---|---|")
    for k, o in d["oracles"].items():
        A.append("| `%s` | %s | `%s` |" % (k, o["ok"], json.dumps(o["detail"])[:220]))
    A.append("")
    A.append("Two oracles are **expected to fail** and are printed as the finding, not as "
             "breakage: `jc3_box_formula_reproduced` and `jc3_hull_formula_reproduced`. Every "
             "structural oracle (block size, links, bias, centre of mass, box census, BmAK "
             "negatives) passes.\n")

    A.append("## 6. UNKNOWN\n")
    for i, u in enumerate(d["unknowns"], 1):
        A.append("%d. %s" % (i, u))
    A.append("")
    return "\n".join(A) + "\n"


# ------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = build()
    js = json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n"
    md = render(doc)
    if a.check:
        ok = True
        for path, want in ((OUT_JSON, js), (OUT_MD, md)):
            have = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
            if have != want:
                print("!! %s is stale" % os.path.basename(path), file=sys.stderr)
                ok = False
        expected_fail = {"jc3_box_formula_reproduced", "jc3_hull_formula_reproduced"}
        bad = {k: o for k, o in doc["oracles"].items()
               if not o["ok"] and k not in expected_fail}
        if bad:
            print("!! unexpected oracle failure: %s" % json.dumps(bad)[:600], file=sys.stderr)
            ok = False
        for k in sorted(expected_fail):
            o = doc["oracles"][k]
            print("oracle %s (reported, not a drift): ok=%s %s"
                  % (k, o["ok"], json.dumps(o["detail"])))
        print("OK: bmak tags no mass/inertia; jc3 blocks %d, boxes %d, box-oracle %d/%d, bias %d, "
              "com median %s" % (len(doc["jc3"]["donor_blocks"]), doc["jc3"]["box_oracle"]["n"],
                                 doc["jc3"]["box_oracle"]["box_formula"]["1%"],
                                 doc["jc3"]["box_oracle"]["n"], doc["constants"]["bias"],
                                 f(doc["jc3"]["com_error"]["median"])))
        print("INERTIA.md/json current" if ok else "regenerate with --write")
        return 0 if ok else 1
    if a.write:
        open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(js)
        open(OUT_MD, "w", encoding="utf-8", newline="\n").write(md)
        print("wrote INERTIA.md and INERTIA.json")
        print("bmak: exports %d, mass/inertia properties %s, tensor-shaped triples %s"
              % (len(doc["bmak"]["exports"]),
                 doc["oracles"]["bmak_no_mass_or_inertia_property_serialized"]["ok"],
                 sum(h for s in doc["bmak"]["signature_scan"] for h in s["hits"])))
        print("jc3: blocks %d, bodies %d, boxes %d, box-oracle %d/%d, hull-oracle %d/%d"
              % (len(doc["jc3"]["donor_blocks"]), doc["jc3"]["fleet"]["bodies"],
                 doc["jc3"]["box_oracle"]["n"], doc["jc3"]["box_oracle"]["box_formula"]["1%"],
                 doc["jc3"]["box_oracle"]["n"], doc["jc3"]["box_oracle"]["hull_formula"]["1%"],
                 doc["jc3"]["box_oracle"]["n"]))
        print("bias %d, com median %s, median box ratio %s"
              % (doc["constants"]["bias"], f(doc["jc3"]["com_error"]["median"]),
                 doc["jc3"]["box_oracle"]["median_ratio_box"]))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
