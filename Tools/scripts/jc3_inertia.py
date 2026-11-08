"""jc3_inertia.py - is the payload in each `hknpShapeMassProperties` an inertia tensor?
(GRB physics follow-up to G3-10b/10c, which left it UNKNOWN.)

Static decode only; the donor is read with `jc3hkx.py` (read-only), the game is never touched.

WHAT IS MEASURED (every number has a byte offset)
  1. The block, from the bytes: 48 bytes = **16 zero bytes**, a **24-byte payload at
     +0x10..+0x27**, the mass `f32` at **+0x28**, and **one `f32` at +0x2C**.  So the bytes
     *after* the mass are 4 bytes - structurally too few for a symmetric tensor (24 bytes for
     six values, 36 for nine) - and even where that `f32` is non-zero it is a single scalar.
  2. The 24-byte payload read every way a tensor can be stored here: `f32` x6, IEEE half x6,
     int16 x6 (three diagonal + three products), int16 x9 (full 3x3), the int16 grouping the
     data selects (3 x int16x4), and **every** consecutive int16 triple as the diagonal
     (windows `k..k+2`, k = 0..9), so the placement is searched, not guessed.
  3. Which lanes are odd under a mirror, measured without assuming a layout: mirrored part
     pairs are found from geometry (hull bounds mirrored in x, equal y/z ranges, equal mass,
     body not self-symmetric in x), and each int16 lane is classified equal or exactly
     negated.  A mirror about x negates exactly the x-odd mass properties.
  4. For each candidate, the four-part oracle per body: symmetric, positive-definite, principal
     moments satisfy the triangle inequality, and the shape of those moments agrees with a
     solid-box tensor built from the same body's hull extents and decoded mass.  All four are
     scale-free (a positive scale preserves them) because the payload is integer-quantised and
     no project decoder reads its scale.
  5. Agreement is measured on the *sorted, normalised* principal moments (largest = 1) with a
     stated tolerance of 25 % per moment, and also counted at 50 % and 100 % so the reader can
     see how far the data is from the model.

Outputs (never hand-edited):
  Research/JC3Grab/INERTIA.md
  Research/JC3Grab/INERTIA.json

Usage
  python Tools/scripts/jc3_inertia.py --write
  python Tools/scripts/jc3_inertia.py --check
"""
from __future__ import annotations

import argparse
import json
import math
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3hkx  # noqa: E402
import jc3_physics_roles2 as R2  # noqa: E402

DONOR = R2.DONOR
OUT_MD = os.path.join(ROOT, "Research", "JC3Grab", "INERTIA.md")
OUT_JSON = os.path.join(ROOT, "Research", "JC3Grab", "INERTIA.json")
BLOCK = 48
PAYLOAD_AT = 0x10
PAYLOAD_LEN = 24
MASS_AT = 0x28
TAIL_AT = 0x2C
TOL = 0.25                 # stated tolerance on each normalised principal moment
TOLS = (0.25, 0.50, 1.00)
Q15 = 32768.0
MIRROR_REL = 0.015         # relative tolerance on the six hull bounds
MIN_BYTE_LAYOUT = "lanes 4,5,6 (+0x18,+0x1a,+0x1c) as the diagonal"


# ---------------------------------------------------------------- extraction
def f16(h: int) -> float:
    s = (h >> 15) & 1
    e = (h >> 10) & 0x1F
    m = h & 0x3FF
    if e == 0:
        v = m * 2.0 ** -24
    elif e == 31:
        v = float("inf")
    else:
        v = (1 + m / 1024.0) * 2.0 ** (e - 15)
    return -v if s else v


def i16(payload: bytes, i: int) -> int:
    return struct.unpack_from("<h", payload, 2 * i)[0]


def collect() -> dict:
    blob = open(DONOR, "rb").read()
    pf = jc3hkx.Packfile(blob)
    base = pf.base
    psd = [o for o in pf.objects if o.cls == "hknpPhysicsSystemData"]
    a40 = pf.array(psd[0].offset + 0x40)
    bodies = []
    for i in range(a40["size"]):
        at = a40["ptr"] + jc3hkx.BODY_ENTRY_SIZE * i
        shape = pf.pointers.get(at, 0)
        bodies.append({"id": i, "shape": shape, "shape_class": pf._starts.get(shape, "")})

    # polytope +0x20 -> hkRefCountedProperties +0x10 -> mass block (G3-10c's link)
    shape_to_mass, links = {}, 0
    for o in pf.objects:
        if o.cls != "hknpConvexPolytopeShape":
            continue
        node = pf.pointers.get(o.offset + 0x20, 0)
        mb = pf.pointers.get(node + 0x10, 0) if node else 0
        if mb and pf._starts.get(mb) == "hknpShapeMassProperties":
            shape_to_mass[o.offset] = mb
            links += 1

    mass_bodies = {}
    for b in bodies:
        mb = shape_to_mass.get(b["shape"])
        if mb is not None:
            mass_bodies.setdefault(mb, []).append(b["id"])

    blocks = []
    for o in pf.objects:
        if o.cls != "hknpShapeMassProperties":
            continue
        raw = blob[base + o.offset:base + o.offset + BLOCK]
        payload = raw[PAYLOAD_AT:PAYLOAD_AT + PAYLOAD_LEN]
        mass = struct.unpack_from("<f", blob, base + o.offset + MASS_AT)[0]
        tail = raw[TAIL_AT:TAIL_AT + 4]
        tail_f32 = struct.unpack("<f", tail)[0]
        ext, hull = None, None
        shapes = [s for s, m in shape_to_mass.items() if m == o.offset]
        if shapes:
            b = jc3hkx.decode_polytope(pf, shapes[0])["bounds"]
            ext = [b["max"][k] - b["min"][k] for k in range(3)]
            hull = {"min": list(b["min"]), "max": list(b["max"])}
        blocks.append({
            "at": o.offset, "extent": pf.extents[o.offset],
            "header_zero": raw[:PAYLOAD_AT] == b"\0" * PAYLOAD_AT,
            "payload": payload.hex(), "tail": tail.hex(),
            "tail_f32": round(tail_f32, 9), "tail_zero": tail == b"\0\0\0\0",
            "mass": mass, "ei": [i16(payload, i) for i in range(12)],
            "body_ids": mass_bodies.get(o.offset, []),
            "hull_extents": [round(x, 6) for x in ext] if ext else None, "hull": hull,
        })
    blocks.sort(key=lambda r: r["at"])
    return {"blob": len(blob), "objects": len(pf.objects), "bodies": len(bodies),
            "blocks": blocks, "links": links}


# ---------------------------------------------------------------- mirror test
def mirror_pairs(c: dict) -> dict:
    """Mirrored part pairs from geometry alone; then per-lane equal / negated."""
    cand = [b for b in c["blocks"] if b["hull"] and b["mass"] > 0]
    pairs, rejected, masks = [], 0, {}
    for i, a in enumerate(cand):
        for b in cand[i + 1:]:
            ha, hb = a["hull"], b["hull"]
            if abs(a["mass"] - b["mass"]) > 1e-6 * max(a["mass"], 1e-9) + 1e-9:
                continue
            ext = [ha["max"][k] - ha["min"][k] for k in range(3)]
            if min(ext) <= 0:
                continue
            # mirrored about x: the x bounds swap and negate, the y/z bounds match
            ok_x = (abs(ha["min"][0] + hb["max"][0]) < MIRROR_REL * ext[0]
                    and abs(ha["max"][0] + hb["min"][0]) < MIRROR_REL * ext[0])
            ok_yz = all(abs(ha["min"][k] - hb["min"][k]) < MIRROR_REL * ext[k]
                        and abs(ha["max"][k] - hb["max"][k]) < MIRROR_REL * ext[k]
                        for k in (1, 2))
            # the body must not be self-symmetric in x, else its "partner" is itself
            selfsym = abs(ha["min"][0] + ha["max"][0]) < 0.02 * ext[0]
            if not (ok_x and ok_yz and not selfsym):
                continue
            # the lanes are 16-bit quantised, so a mirrored pair matches to one unit
            same = [k for k in range(12) if abs(a["ei"][k] - b["ei"][k]) <= 1]
            neg = [k for k in range(12)
                   if abs(a["ei"][k]) > 1 and abs(a["ei"][k] + b["ei"][k]) <= 1]
            if len(same) + len(neg) < 9:          # payloads not related -> not a true pair
                rejected += 1
                continue
            mask = tuple(sorted(neg))
            pairs.append({"a": a["at"], "b": b["at"], "body_a": a["body_ids"],
                          "body_b": b["body_ids"], "mass": a["mass"],
                          "ei_a": a["ei"], "ei_b": b["ei"],
                          "flip_lanes": list(mask), "equal_lanes": same,
                          "other_lanes": [k for k in range(12)
                                          if k not in same and k not in neg]})
            masks[mask] = masks.get(mask, 0) + 1
    return {"pairs": pairs, "rejected_geometry_match": rejected,
            "mask_histogram": {"|".join(str(x) for x in k): v
                               for k, v in sorted(masks.items())},
            "majority_mask": list(max(masks, key=masks.get)) if masks else []}


# ---------------------------------------------------------------- layouts
def layout_after_mass(payload: bytes) -> tuple:
    """The literal reading: the tensor is the bytes AFTER the mass (+0x2C..+0x2F).  Those four
    bytes are outside the 24-byte payload, so this layout can only ever yield one scalar."""
    return (None, None)


def layout_f32x6(payload: bytes) -> tuple:
    v = [struct.unpack_from("<f", payload, 4 * i)[0] for i in range(6)]
    return (v[0:3], v[3:6])


def layout_f16x6(payload: bytes) -> tuple:
    v = [f16(struct.unpack_from("<H", payload, 2 * i)[0]) for i in range(6)]
    return (v[0:3], v[3:6])


def layout_i16x6(payload: bytes) -> tuple:
    v = [i16(payload, k) for k in range(6)]
    return (v[0:3], v[3:6])


def layout_i16x9(payload: bytes) -> tuple:
    v = [i16(payload, k) for k in range(9)]
    return ([v[0], v[4], v[8]], [v[1], v[2], v[5]])


def layout_i16_grouped(payload: bytes) -> tuple:
    """3 x int16x4; diagonal in group 2, products from the x-odd lanes (Ixy=9, Ixz=10, Iyz=8)."""
    v = [i16(payload, k) for k in range(12)]
    return ([v[4], v[5], v[6]], [v[9], v[10], v[8]])


def layout_i16_grouped_diag(payload: bytes) -> tuple:
    """Same grouping, diagonal only (the third group may be an axis, not products)."""
    v = [i16(payload, k) for k in range(12)]
    return ([v[4], v[5], v[6]], None)


def window_layout(k: int):
    def fn(payload: bytes) -> tuple:
        return ([i16(payload, k + j) for j in range(3)], None)
    return fn


LAYOUTS = [
    ("after_mass_4B", "the 4 bytes at +0x2c..+0x2f, i.e. literally after the mass", layout_after_mass),
    ("f32x6_at_10", "6 x IEEE f32 at +0x10..+0x27 (diag, then products)", layout_f32x6),
    ("f16x6_at_10", "6 x IEEE half at +0x10..+0x1b (diag, then products)", layout_f16x6),
    ("i16x6_at_10", "6 x int16 at +0x10..+0x1b (diag, then products)", layout_i16x6),
    ("i16x9_at_10", "9 x int16 at +0x10..+0x21, full 3x3 row-major", layout_i16x9),
    ("i16_grouped", "3 x int16x4; diag at +0x18/+0x1a/+0x1c, products at +0x22/+0x24/+0x20", layout_i16_grouped),
    ("i16_grouped_diag", "3 x int16x4; diagonal only at +0x18/+0x1a/+0x1c", layout_i16_grouped_diag),
]


# ---------------------------------------------------------------- oracle
def box_moments(mass: float, ext: list) -> list:
    a, b, c = ext
    return [mass * (b * b + c * c) / 12.0,
            mass * (a * a + c * c) / 12.0,
            mass * (a * a + b * b) / 12.0]


def normalised(v: list) -> list:
    m = max(v)
    return [x / m for x in v] if m else [0.0, 0.0, 0.0]


def test_one(diag, products) -> dict:
    if diag is None:
        return {"ok": False, "reason": "no tensor bytes", "pd": False, "tri": False,
                "sym": None, "moments": None, "normalised": None}
    sym = None
    if products is None:
        moments = [float(x) for x in diag]
    else:
        m = np.array([[diag[0], products[0], products[1]],
                      [products[0], diag[1], products[2]],
                      [products[1], products[2], diag[2]]], dtype=float)
        if not np.isfinite(m).all():
            return {"ok": False, "reason": "non-finite", "pd": False, "tri": False,
                    "sym": None, "moments": None, "normalised": None}
        sym = bool(np.allclose(m, m.T, rtol=0, atol=1e-12))
        moments = [float(x) for x in np.linalg.eigvalsh(m)]
    if not all(math.isfinite(x) for x in moments):
        return {"ok": False, "reason": "non-finite moments", "pd": False, "tri": False,
                "sym": sym, "moments": None, "normalised": None}
    mom = sorted(moments, reverse=True)
    return {"ok": True, "pd": bool(min(mom) > 0),
            "tri": bool(mom[0] <= mom[1] + mom[2] + 1e-9 * abs(mom[0])),
            "sym": sym, "moments": mom, "normalised": normalised(mom),
            "diag": [float(x) for x in diag]}


def run_layout(name: str, fn, blocks: list) -> dict:
    rows, fail_first = [], None
    for b in blocks:
        diag, prod = fn(bytes.fromhex(b["payload"]))
        t = test_one(diag, prod)
        rec = {"at": b["at"], "mass": b["mass"], "hull_extents": b["hull_extents"],
               "payload": b["payload"], "test": t, "box_error": None, "box_ok": False}
        box = None
        if b["hull_extents"] and b["mass"] > 0:
            box = box_moments(b["mass"], b["hull_extents"])
        rec["box_moments"] = [round(x, 9) for x in box] if box else None
        if t["ok"] and box:
            bn = normalised(sorted(box, reverse=True))
            dn = t["normalised"]
            errs = [abs(dn[k] - bn[k]) / bn[k] for k in range(3)]
            rec["box_error"] = round(max(errs), 6)
            rec["box_error_by_moment"] = [round(e, 6) for e in errs]
            rec["box_normalised"] = [round(x, 9) for x in bn]
            rec["box_ok"] = bool(max(errs) <= TOL)
            # which lane is furthest from its box value -> the failing byte
            worst = max(range(3), key=lambda k: errs[k])
            rec["worst_moment"] = worst
            rec["worst_lane_offset"] = "+0x%02x" % (PAYLOAD_AT + 2 * (4 + worst)) \
                if name.startswith("i16_grouped") else "+0x%02x" % PAYLOAD_AT
        ok = bool(t["ok"] and t["pd"] and t["tri"] and rec["box_ok"])
        rec["pass"] = ok
        if not ok and fail_first is None:
            fail_first = {"at": "%#x" % b["at"], "payload": b["payload"], "mass": b["mass"],
                          "hull_extents": b["hull_extents"],
                          "byte_layout": ("+0x2c..+0x2f is 4 bytes; a symmetric tensor needs "
                                          "24 (six values) or 36 (nine values)"
                                          if name == "after_mass_4B" else
                                          "first off value at %s" % rec.get("worst_lane_offset",
                                                                           "+0x10")),
                          "reason": ("size" if name == "after_mass_4B" else
                                     "pd=%s tri=%s box_error=%s" % (t["pd"], t["tri"],
                                                                    rec["box_error"]))}
        rows.append(rec)
    tested = [r for r in rows if r["box_moments"]]
    errs = sorted(r["box_error"] for r in tested if r["box_error"] is not None)
    return {"name": name, "rows": rows,
            "pd": sum(1 for r in rows if r["test"]["pd"]),
            "tri": sum(1 for r in rows if r["test"]["tri"]),
            "sym": sum(1 for r in rows if r["test"]["sym"] is True),
            "sym_testable": sum(1 for r in rows if r["test"]["sym"] is not None),
            "box_within": {str(int(t * 100)): sum(1 for r in tested
                                                  if r["box_error"] is not None
                                                  and r["box_error"] <= t) for t in TOLS},
            "box_ok": sum(1 for r in tested if r["box_ok"]),
            "box_tested": len(tested),
            "box_error_median": round(errs[len(errs) // 2], 6) if errs else None,
            "pass": sum(1 for r in rows if r["pass"]), "n": len(rows),
            "first_fail": fail_first}


def build() -> dict:
    c = collect()
    blocks = c["blocks"]
    mir = mirror_pairs(c)
    results = [run_layout(n, f, blocks) for n, _d, f in LAYOUTS]
    scan = []
    for k in range(10):
        r = run_layout("i16_window_%d" % k, window_layout(k), blocks)
        scan.append({"k": k, "lanes": [k, k + 1, k + 2],
                     "offsets": ["+0x%02x" % (PAYLOAD_AT + 2 * (k + j)) for j in range(3)],
                     "pd": r["pd"], "tri": r["tri"],
                     "box_within": r["box_within"], "box_tested": r["box_tested"],
                     "box_error_median": r["box_error_median"], "pass": r["pass"], "n": r["n"]})
    best_scan = max(scan, key=lambda s: (s["pass"], -s["box_error_median"] or 0))
    best = max(results, key=lambda r: r["pass"])
    g3 = [math.sqrt(b["ei"][8] ** 2 + b["ei"][9] ** 2 + b["ei"][10] ** 2) / Q15 for b in blocks]
    lane = {k: [min(b["ei"][k] for b in blocks), max(b["ei"][k] for b in blocks)]
            for k in range(12)}
    g2 = [math.sqrt(b["ei"][4] ** 2 + b["ei"][5] ** 2 + b["ei"][6] ** 2) / Q15 for b in blocks]
    nonzero_tail = sum(1 for b in blocks if not b["tail_zero"])
    verdict_ok = best["pass"] >= 0.75 * best["box_tested"]
    oracles = {
        "block_is_48_bytes_with_16_zero_leading": {
            "ok": len(blocks) == 56 and all(b["extent"] == BLOCK and b["header_zero"]
                                           for b in blocks),
            "detail": {"blocks": len(blocks),
                       "extent_48": sum(1 for b in blocks if b["extent"] == BLOCK),
                       "header_16_zero": sum(1 for b in blocks if b["header_zero"])}},
        "bytes_after_the_mass_are_one_scalar": {
            "ok": BLOCK - TAIL_AT == 4 and nonzero_tail < len(blocks),
            "detail": {"bytes": BLOCK - TAIL_AT, "nonzero_tail": nonzero_tail,
                       "tail_f32_range": [min(b["tail_f32"] for b in blocks),
                                          max(b["tail_f32"] for b in blocks)],
                       "tensor_needs": "24 bytes (six values) or 36 (nine values)"}},
        "mass_link_to_hulls": {
            "ok": c["links"] >= 54,
            "detail": {"polytope_links": c["links"],
                       "blocks_with_body_id": sum(1 for b in blocks if b["body_ids"]),
                       "blocks_with_hull": sum(1 for b in blocks if b["hull_extents"])}},
        "mirror_mask_is_three_x_odd_lanes": {
            "ok": any(p["flip_lanes"] == [0, 9, 10] for p in mir["pairs"]),
            "detail": {"pairs": len(mir["pairs"]),
                       "masks": mir["mask_histogram"],
                       "majority": mir["majority_mask"],
                       "rejected_geometry_match": mir["rejected_geometry_match"]}},
        "best_int16_window_is_the_grouped_diagonal": {
            "ok": best_scan["k"] == 4,
            "detail": {"best_window": best_scan["k"], "lanes": best_scan["lanes"],
                       "offsets": best_scan["offsets"], "pass": best_scan["pass"],
                       "of": best_scan["box_tested"]}},
        "box_agreement_at_25pct_is_met": {
            "ok": verdict_ok,
            "detail": {"best_layout": best["name"], "within_25": best["box_within"]["25"],
                       "within_50": best["box_within"]["50"], "within_100": best["box_within"]["100"],
                       "of": best["box_tested"], "median_error": best["box_error_median"]}},
    }
    return {
        "schema": 1,
        "generated_by": "Tools/scripts/jc3_inertia.py --write",
        "card": "GRB physics follow-up G3-10b/10c: is the mass-properties payload an inertia tensor?",
        "donor": {"path": os.path.relpath(DONOR, ROOT).replace("\\", "/"), "bytes": c["blob"],
                  "objects": c["objects"], "bodies": c["bodies"]},
        "block_layout": {"block": BLOCK, "header": [0, PAYLOAD_AT],
                         "payload": [PAYLOAD_AT, PAYLOAD_LEN], "mass_at": MASS_AT,
                         "tail": [TAIL_AT, BLOCK - TAIL_AT],
                         "blocks": [{k: b[k] for k in ("at", "extent", "mass", "payload",
                                                       "tail", "tail_f32", "body_ids",
                                                       "hull_extents")}
                                    for b in blocks]},
        "mirror": mir,
        "group_norms": {"g2_min": round(min(g2), 6), "g2_max": round(max(g2), 6),
                        "g3_min": round(min(g3), 6), "g3_max": round(max(g3), 6)},
        "lane_ranges": {str(k): lane[k] for k in range(12)},
        "layouts": results,
        "window_scan": scan,
        "oracles": oracles,
        "verdict": {
            "tensor_identified": bool(verdict_ok),
            "status": "done" if verdict_ok else "UNKNOWN",
            "statement": ("the payload passes the four-part oracle on %d of %d bodies"
                          % (best["pass"], best["box_tested"]))
                         if verdict_ok else
                        ("the payload fails the four-part oracle: best layout %s passes %d of "
                         "%d bodies at %d%% per-moment tolerance (median normalised error %s, "
                         "%d pass at 50%%)"
                         % (best["name"], best["pass"], best["box_tested"], int(TOL * 100),
                            best["box_error_median"], best["box_within"]["50"])),
            "best_layout": best["name"], "tolerance": TOL,
        },
        "unknowns": [
            "the scale that turns the quantised lanes into SI moments: no project decoder reads "
            "it, so only the shape of the moments is testable (all four oracle parts are "
            "scale-free). Candidate home: the fourth lane of each group (+0x16 %s..%s and +0x1e "
            "%s..%s), which stays in a narrow band in all 56 blocks and looks like an exponent or "
            "scale marker, but nothing in this tree documents it."
            % (lane[3][0], lane[3][1], lane[7][0], lane[7][1]),
            "whether the third int16x4 group (+0x20..+0x27) is the three products or a principal "
            "axis: its triple norm is %s..%s in Q15, neither 1.0 (an axis) nor 0 (products near a "
            "principal frame), and two of its lanes are x-odd, which both readings allow."
            % (round(min(g3), 4), round(max(g3), 4)),
            "whether the f32 at +0x2c is a volume, a density or an unused slot: it is 0 in %d of "
            "56 blocks and 0.0019..0.165 in the rest, with no monotone relation to the mass "
            "checked here." % sum(1 for b in blocks if b["tail_zero"]),
            "the sign convention of the x-odd lanes (row vs column, right- vs left-handed). The "
            "mirror mask fixes *which* lanes are x-odd, not the handedness.",
            "why box agreement fails: the hull is not a box (thin panels, curved doors), so the "
            "reference tensor itself is a model. A hull-exact tensor (tetrahedral decomposition "
            "of the polytope) would separate an encoding error from a reference-model error.",
        ],
    }


# ---------------------------------------------------------------- render
def hx(v):
    return "-" if v is None else "%#x" % v


def render(doc: dict) -> str:
    lay, mir, gn, vd = doc["block_layout"], doc["mirror"], doc["group_norms"], doc["verdict"]
    res = {r["name"]: r for r in doc["layouts"]}
    best = max(doc["layouts"], key=lambda r: r["pass"])
    scan = doc["window_scan"]
    best_scan = max(scan, key=lambda s: (s["pass"], -s["box_error_median"] or 0))
    o = []
    w = o.append
    w("# Is the mass-properties payload an inertia tensor?")
    w("")
    w("Generated by `Tools/scripts/jc3_inertia.py --write` from the donor `%s` (%d bytes, %d "
      "objects, %d body entries), read once with `jc3hkx.py` read-only. Static decode only; the "
      "game is not run, attached to or modified."
      % (doc["donor"]["path"], doc["donor"]["bytes"], doc["donor"]["objects"], doc["donor"]["bodies"]))
    w("")
    w("## Verdict - **%s**" % vd["status"])
    w("")
    w("%s%s." % (vd["statement"][0].upper(), vd["statement"][1:]))
    w("")
    w("Two separate findings, and they point different ways:")
    w("")
    w("1. **The bytes after the mass cannot be the tensor** - there are four of them, and they "
      "are a single `f32` at `+0x2c`, non-zero in only %d of 56 blocks. A symmetric tensor needs "
      "24 bytes (six values) or 36 (nine). This is the first failing byte layout and it fails on "
      "size, not on statistics."
      % doc["oracles"]["bytes_after_the_mass_are_one_scalar"]["detail"]["nonzero_tail"])
    w("2. **The tensor-sized payload is the 24 bytes *before* the mass, and the oracle still "
      "fails on it.** The best of seven readings and of all ten int16 diagonal placements is "
      "`%s`: positive-definite and triangle-safe on every body, but a solid-box comparison "
      "passes only **%d of %d** bodies at %d %% per normalised moment (%s at 50 %%, median error "
      "%s). Since the oracle was the test for calling these bytes an inertia tensor, the "
      "semantics stay **UNKNOWN**."
      % (vd["best_layout"], best["box_within"]["25"], best["box_tested"],
         int(vd["tolerance"] * 100), best["box_within"]["50"], best["box_error_median"]))
    w("")
    w("## 1. The block, byte by byte (decoded)")
    w("")
    w("| range | bytes | content | label |")
    w("|---|---|---|---|")
    w("| +0x00..+0x0f | 16 | zero in all 56 blocks | decoded |")
    w("| +0x10..+0x17 | 8 | int16x4 group 1 (lane 0 is x-odd, see §2) | decoded bytes / derived grouping |")
    w("| +0x18..+0x1f | 8 | int16x4 group 2 (all lanes mirror-invariant) | decoded bytes / derived grouping |")
    w("| +0x20..+0x27 | 8 | int16x4 group 3 (lanes 9, 10 are x-odd) | decoded bytes / derived grouping |")
    w("| +0x28..+0x2b | 4 | mass `f32` (G3-10b; 800.0, 40.0, 25.0, 1.0, 0.003 ...) | decoded |")
    tails = [b["tail_f32"] for b in lay["blocks"] if b["tail_f32"]]
    w("| +0x2c..+0x2f | 4 | one `f32`: exactly 0 in %d blocks, %s..%s in the other %d | decoded |"
      % (len(lay["blocks"]) - len(tails), round(min(tails), 6), round(max(tails), 6), len(tails)))
    w("")
    w("First eight blocks, payload as three int16x4 groups:")
    w("")
    w("| block | mass | +0x10 | +0x18 | +0x20 | tail f32 | hull extents (m) |")
    w("|---|---|---|---|---|---|---|")
    for b in lay["blocks"][:8]:
        v = [struct.unpack_from("<h", bytes.fromhex(b["payload"]), 2 * k)[0] for k in range(12)]
        w("| %s | %s | %s | %s | %s | %s | %s |"
          % (hx(b["at"]), round(b["mass"], 6), v[0:4], v[4:8], v[8:12],
             round(b["tail_f32"], 6),
             ", ".join("%.3f" % x for x in b["hull_extents"]) if b["hull_extents"] else "-"))
    w("")
    w("## 2. The mirror test - which lanes are x-odd (decoded)")
    w("")
    w("Mirrored part pairs are found from geometry alone (hull bounds mirrored in x within "
      "%.1f %%, "
      "identical y/z ranges, equal mass, body not self-symmetric in x), then each of the 12 "
      "int16 lanes is classified equal or negated within one quantisation unit. A mirror about x "
      "negates exactly the "
      "x-odd mass properties - centre-of-mass x and any product carrying one x index - so the "
      "mask tests the grouping without assuming it. **%d** pair(s) survive."
      % (MIRROR_REL * 100, len(mir["pairs"])))
    w("")
    if mir["pairs"]:
        p = mir["pairs"][0]
        w("The cleanest pair, `%s` (body %s) and `%s` (body %s), both mass %s:"
          % (hx(p["a"]), p["body_a"], hx(p["b"]), p["body_b"], round(p["mass"], 6)))
        w("")
        w("| group | block `%s` | block `%s` | relation |" % (hx(p["a"]), hx(p["b"])))
        w("|---|---|---|---|")
        for gi, name in enumerate(("+0x10", "+0x18", "+0x20")):
            a = p["ei_a"][4 * gi:4 * gi + 4]
            b = p["ei_b"][4 * gi:4 * gi + 4]
            flip = [4 * gi + j for j in range(4) if 4 * gi + j in p["flip_lanes"]]
            w("| %s | %s | %s | %s |" % (name, a, b,
                                         "lanes %s negated" % flip if flip else "identical"))
        w("")
    w("| lane mask (negated lanes) | pairs |")
    w("|---|---|")
    for k, v in mir["mask_histogram"].items():
        w("| `%s` | %d |" % (k, v))
    w("")
    w("Three x-odd lanes at int16 indices %s: one vector component (lane 0, `+0x10`) and two "
      "scalars in group 3 (`+0x22`, `+0x24`). Under the 3 x int16x4 grouping this is the "
      "signature of a centre of mass plus a diagonal plus two products - the *shape* of a "
      "compressed mass-properties record - which is why the grouped layouts are tested in §3. "
      "The sizes are not the answer: `%d` geometry match(es) were rejected because the payloads "
      "were not lane-related at all." % (mir["majority_mask"], mir["rejected_geometry_match"]))
    w("")
    w("Group norms in Q15 (`sqrt(sum of three lanes^2) / 32768`): group 2 (candidate diagonal) "
      "%s..%s, group 3 %s..%s. A group 3 norm of 1.0 would be a principal axis; near 0 would be "
      "products in a principal frame. Neither holds." % (gn["g2_min"], gn["g2_max"],
                                                          gn["g3_min"], gn["g3_max"]))
    w("")
    w("## 3. The oracle (each part is scale-free on purpose)")
    w("")
    w("1. **symmetric** - `M == M^T`; not testable for a diagonal-only layout (holds by "
      "construction) and counted separately.")
    w("2. **positive-definite** - all three principal moments `> 0`.")
    w("3. **triangle inequality** - `max <= middle + min`.")
    w("4. **box agreement** - solid box `m/12 * (b^2+c^2, a^2+c^2, a^2+b^2)` from the same "
      "body's hull extents and decoded mass, compared as *sorted normalised* moments (largest = "
      "1) within **%d %%** per moment; 50 %% and 100 %% are counted too so the gap is visible." % int(TOL * 100))
    w("")
    w("| reading | where | symmetric | pd | triangle | box <=25% | box <=50% | pass |")
    w("|---|---|---|---|---|---|---|---|")
    for r in sorted(doc["layouts"], key=lambda r: -r["pass"]):
        w("| `%s` | %s | %s | %d/%d | %d/%d | %d/%d | %d/%d | **%d/%d** |"
          % (r["name"], "after the mass" if r["name"] == "after_mass_4B" else "before the mass",
             "%d/%d" % (r["sym"], r["sym_testable"]) if r["sym_testable"] else "by construction",
             r["pd"], r["n"], r["tri"], r["n"], r["box_within"]["25"], r["box_tested"],
             r["box_within"]["50"], r["box_tested"], r["pass"], r["box_tested"]))
    w("")
    w("Every int16 triple as the diagonal (placement searched, not guessed):")
    w("")
    w("| window | lanes | offsets | pd | triangle | box <=25% | box <=50% | median error |")
    w("|---|---|---|---|---|---|---|---|")
    for s in scan:
        w("| %d | %s | %s | %d/%d | %d/%d | %d/%d | %d/%d | %s |"
          % (s["k"], s["lanes"], " ".join(s["offsets"]), s["pd"], s["n"], s["tri"], s["n"],
             s["box_within"]["25"], s["box_tested"], s["box_within"]["50"], s["box_tested"],
             s["box_error_median"]))
    w("")
    w("Window **%d** (`%s`) wins on every count, and it is the group-2 diagonal the mirror test "
      "pointed at. It is still short of the oracle." % (best_scan["k"], " ".join(best_scan["offsets"])))
    w("")
    w("## 4. Per body: `%s`" % best["name"])
    w("")
    w("| block | mass | hull extents | diag int16 | diag / max | box / max | error | pass |")
    w("|---|---|---|---|---|---|---|---|")
    for r in best["rows"]:
        t = r["test"]
        if not t["ok"] or not r["box_moments"]:
            w("| %s | %s | %s | %s | - | - | - | **no** (no hull) |"
              % (hx(r["at"]), round(r["mass"], 6),
                 ", ".join("%.3f" % x for x in r["hull_extents"]) if r["hull_extents"] else "-",
                 [int(x) for x in (t.get("diag") or [])]))
            continue
        w("| %s | %s | %s | %s | %s | %s | %s | %s |"
          % (hx(r["at"]), round(r["mass"], 6),
             ", ".join("%.3f" % x for x in r["hull_extents"]),
             [int(x) for x in t["diag"]],
             ", ".join("%.3f" % x for x in t["normalised"]),
             ", ".join("%.3f" % x for x in r["box_normalised"]),
             r["box_error"], "yes" if r["pass"] else "**no**"))
    w("")
    w("Totals for this layout: pd %d/%d, triangle %d/%d, box <=25%% %d/%d, box <=50%% %d/%d, "
      "**oracle pass %d/%d**. First failing body: `%s`."
      % (best["pd"], best["n"], best["tri"], best["n"], best["box_within"]["25"], best["box_tested"],
         best["box_within"]["50"], best["box_tested"], best["pass"], best["box_tested"],
         json.dumps(best["first_fail"])))
    w("")
    w("## 5. Oracles (each can fail; `--check` re-runs them)")
    w("")
    w("| oracle | ok | detail |")
    w("|---|---|---|")
    for k, v in doc["oracles"].items():
        w("| `%s` | %s | %s |" % (k, v["ok"], json.dumps(v["detail"])[:420]))
    w("")
    w("## UNKNOWN")
    w("")
    for i, u in enumerate(doc["unknowns"], 1):
        w("%d. %s" % (i, u))
    w("")
    w("## What would settle it")
    w("")
    w("Compute the inertia tensor of the hull itself (tetrahedral decomposition of the "
      "`hknpConvexPolytopeShape` vertices) instead of a solid box, and re-run the same "
      "scale-free comparison. If the payload is an inertia encoding, the grouped diagonal should "
      "match the hull tensor far more closely than it matches a box - and then the scale at "
      "`+0x1e`/`+0x16` becomes the only remaining unknown.")
    w("")
    return "\n".join(o)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = build()
    md = render(doc)
    if a.write:
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, indent=1, ensure_ascii=False)
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
        print("wrote INERTIA.md / INERTIA.json")
        print("blocks: %d  polytope links: %d  with hull: %d  with body id: %d"
              % (len(doc["block_layout"]["blocks"]),
                 doc["oracles"]["mass_link_to_hulls"]["detail"]["polytope_links"],
                 doc["oracles"]["mass_link_to_hulls"]["detail"]["blocks_with_hull"],
                 doc["oracles"]["mass_link_to_hulls"]["detail"]["blocks_with_body_id"]))
        print("mirror pairs:", len(doc["mirror"]["pairs"]), "masks:", doc["mirror"]["mask_histogram"])
        for r in sorted(doc["layouts"], key=lambda r: -r["pass"]):
            print("  %-18s pass %2d/%-2d  pd %2d tri %2d box25 %2d box50 %2d sym %s"
                  % (r["name"], r["pass"], r["box_tested"], r["pd"], r["tri"],
                     r["box_within"]["25"], r["box_within"]["50"],
                     "%d/%d" % (r["sym"], r["sym_testable"]) if r["sym_testable"] else "n/a"))
        print("verdict:", doc["verdict"]["status"], "-", doc["verdict"]["statement"])
        print("oracles:", {k: v["ok"] for k, v in doc["oracles"].items()})
        return 0
    fails = []
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: outputs missing - run --write")
        return 1
    stored = json.load(open(OUT_JSON, encoding="utf-8"))
    if json.dumps(stored, sort_keys=True) != json.dumps(doc, sort_keys=True):
        fails.append("re-derivation differs from INERTIA.json")
    if open(OUT_MD, encoding="utf-8").read() != render(stored):
        fails.append("INERTIA.md is not the render of the JSON")
    # every structural oracle must hold; the box oracle is the finding and is reported, not
    # required, because the documented outcome is UNKNOWN when it fails.
    for k in ("block_is_48_bytes_with_16_zero_leading", "bytes_after_the_mass_are_one_scalar",
              "mass_link_to_hulls", "mirror_mask_is_three_x_odd_lanes",
              "best_int16_window_is_the_grouped_diagonal"):
        if not stored["oracles"][k]["ok"]:
            fails.append("oracle %s failed: %s" % (k, json.dumps(stored["oracles"][k]["detail"])[:200]))
    if stored["verdict"]["tensor_identified"] and not stored["oracles"]["box_agreement_at_25pct_is_met"]["ok"]:
        fails.append("verdict claims a tensor while the box oracle fails")
    if not stored["verdict"]["tensor_identified"] and stored["oracles"]["box_agreement_at_25pct_is_met"]["ok"]:
        fails.append("verdict says UNKNOWN while the box oracle is met")
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    best = max(stored["layouts"], key=lambda r: r["pass"])
    print("OK: best %s %d/%d ; verdict %s ; structural oracles true"
          % (best["name"], best["pass"], best["box_tested"], stored["verdict"]["status"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
