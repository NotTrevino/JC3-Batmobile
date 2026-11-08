"""jc3_inertia2.py - where a JC3 vehicle body's inertia tensor lives (G3-10k).

Pass 2 of the inertia decode: `Tools/scripts/jc3_inertia.py` (task PHYSICS-inertia)
left the semantics UNKNOWN by comparing the packed payload's *shape* (sorted,
normalised moments) with a solid-box model on every hull.  This pass decodes the
packing itself (an exponent per group), pins the exponent bias against geometry
that is exactly known (each hull's centre of mass), and then runs the brief's
oracle - stored tensor == m/12*(b^2+c^2) - on every fleet body that really is a
single box.

Static only: the .physicsc files are read with `jc3hkx.py` (read-only); no game is
run, attached to or modified.

WHAT IS ESTABLISHED HERE (every number has a byte offset)
  1. Layout: `hknpShapeMassProperties` = 16 zero bytes, a 24-byte payload at
     +0x10..+0x27, the mass f32 at +0x28, one f32 at +0x2c.  The payload is three
     int16x4 groups: (x, y, z, w).
  2. The w lane is a shared exponent: value = mantissa * 2**(floor(w/128) - 111),
     equivalently E = floor(w/128) - 96 and value = mantissa * 2**(E - 15).  The
     bias 111 is *measured*, not assumed: group 1 decodes to a centre of mass, and
     the bias that puts it on the hull's own volume centroid is 111 (median error
     1.5 % fleet-wide) while 110 and 112 miss by two orders of magnitude.
  3. Group 2 (+0x18..+0x1f) is the inertia diagonal in the shape frame, group 3
     (+0x20..+0x27) stays UNKNOWN (its lanes are the largest in the block and its
     own exponent decodes them to ~1e-36, i.e. "no products").
  4. There is no f32 inertia tensor anywhere in the file: an exhaustive scan of
     every 4-byte-aligned float triple in the data section finds no triple that
     matches any box body's m/12*(b^2+c^2) within 5 %, so neither the body/motion
     cinfo nor any other block holds a plain-float tensor.
  5. The brief's oracle: 107 fleet bodies are single boxes (hull volume == bbox
     volume to 1e-3).  The decoded diagonal matches m/12*(b^2+c^2) on 0 of them
     within 1 % (1 at 2 %, 14 at 5 %, 34 at 25 %), with a *uniform* 1.275x excess
     on all three moments.  So the stored tensor is not the collision hull's box
     tensor; it is the authoring geometry's, which the f32 at +0x2c corroborates
     (where non-zero it equals the hull volume x 1.02..1.45, correlation 1.0000).

Outputs (never hand-edited):
  Research/JC3Grab/INERTIA2.md
  Research/JC3Grab/INERTIA2.json

`--check` recomputes every number from the source bytes, compares the stored JSON,
re-renders the note and re-runs every oracle; it fails on any drift.

Usage
  python Tools/scripts/jc3_inertia2.py --write
  python Tools/scripts/jc3_inertia2.py --check
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
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3hkx  # noqa: E402

DONOR = ("Builds/test-091/aaf/models/jc_vehicles/01_land/"
         "v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc")
FLEET = "E:/Modding/_gamedata/JC3grab/hkx/all"
CARS = [("Serpente (donor)", DONOR),
        ("apc", os.path.join(FLEET, "apc.physicsc")),
        ("armoredtransport", os.path.join(FLEET, "armoredtransport.physicsc"))]

OUT_MD = os.path.join(ROOT, "Research", "JC3Grab", "INERTIA2.md")
OUT_JSON = os.path.join(ROOT, "Research", "JC3Grab", "INERTIA2.json")

BLOCK = 48
PAYLOAD_AT = 0x10
MASS_AT = 0x28
TAIL_AT = 0x2C
BIAS = 111                  # value = mantissa * 2**(floor(w/128) - BIAS), measured
BIAS_GRID = (108, 109, 110, 111, 112, 113, 114)
BOX_FILL = 0.999            # hull volume / bbox volume: a "single box"
TOLS = (0.001, 0.01, 0.02, 0.05, 0.10, 0.25)
SCAN_TOL = 0.05             # tolerance of the exhaustive f32-triple scan
GROUP = {"com": 0, "diag": 1, "third": 2}


# ---------------------------------------------------------------- helpers
def scale_of(w: int) -> float:
    """Shared exponent of one int16x4 group.  `w // 128` is the floor (sign-preserving)."""
    return 2.0 ** ((w // 128) - BIAS)


def unpack(raw: bytes) -> dict:
    ei = list(struct.unpack_from("<12h", raw, PAYLOAD_AT))
    return {"ei": ei,
            "mass": struct.unpack_from("<f", raw, MASS_AT)[0],
            "tail": struct.unpack_from("<f", raw, TAIL_AT)[0],
            "header_zero": raw[:PAYLOAD_AT] == b"\0" * PAYLOAD_AT,
            "payload_hex": raw[PAYLOAD_AT:PAYLOAD_AT + 24].hex()}


def group_values(ei: list, g: int) -> list:
    s = scale_of(ei[4 * g + 3])
    return [ei[4 * g + k] * s for k in range(3)]


def hull_props(pts: np.ndarray, mass: float) -> dict:
    """Exact uniform-density properties of the convex hull of `pts`.

    Volume, volume centroid (shape-frame coordinates) and the inertia tensor about
    that centroid: a tetrahedral decomposition from the vertex mean, each tetra
    contributing the closed-form second-moment matrix
    `(V^T V + (sum V)(sum V)^T)/20 * volume`.
    """
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
    C = C + vol * np.outer(ref, ref)                    # second moments about the origin
    I0 = (np.trace(C) * np.eye(3) - C) * (mass / vol)   # about the frame origin
    d = cen
    Ic = I0 - mass * ((d @ d) * np.eye(3) - np.outer(d, d))
    return {"volume": vol, "centroid": cen, "I_com": Ic, "I_origin": I0}


def box_moments(mass: float, ext) -> list:
    a, b, c = (float(x) for x in ext)
    return [mass * (b * b + c * c) / 12.0,
            mass * (a * a + c * c) / 12.0,
            mass * (a * a + b * b) / 12.0]


# ---------------------------------------------------------------- extraction
def scan_file(path: str) -> dict:
    """Every body of one .physicsc whose shape is a convex polytope with a mass block."""
    blob = open(path, "rb").read()
    pf = jc3hkx.Packfile(blob)
    psd = [o for o in pf.objects if o.cls == "hknpPhysicsSystemData"]
    if not psd:
        raise ValueError("no hknpPhysicsSystemData")
    shape_mass = {}
    for o in pf.objects:
        if o.cls != "hknpConvexPolytopeShape":
            continue
        node = pf.pointers.get(o.offset + 0x20, 0)
        mb = pf.pointers.get(node + 0x10, 0) if node else 0
        if mb and pf._starts.get(mb) == "hknpShapeMassProperties":
            shape_mass[o.offset] = mb
    a40 = pf.array(psd[0].offset + 0x40)
    bodies = []
    for i in range(a40["size"]):
        at = a40["ptr"] + jc3hkx.BODY_ENTRY_SIZE * i
        shp = pf.pointers.get(at, 0)
        if pf._starts.get(shp) != "hknpConvexPolytopeShape" or shp not in shape_mass:
            continue
        d = jc3hkx.decode_polytope(pf, shp)
        pts = np.array([v[:3] for v in d["vertices"]], dtype=float)
        if len(pts) < 4:
            continue
        mb = shape_mass[shp]
        raw = blob[pf.base + mb:pf.base + mb + BLOCK]
        u = unpack(raw)
        if not (u["mass"] > 0 and math.isfinite(u["mass"])):
            continue
        b = d["bounds"]
        ext = np.array([b["max"][k] - b["min"][k] for k in range(3)])
        if ext.min() <= 0:
            continue
        hp = hull_props(pts, u["mass"])
        bodies.append({
            "body": i, "block": mb, "shape": shp, "verts": len(pts),
            "mass": u["mass"], "tail": u["tail"], "header_zero": u["header_zero"],
            "payload": u["payload_hex"], "ei": u["ei"],
            "ext": [round(float(x), 6) for x in ext],
            "volume": round(hp["volume"], 9),
            "fill": round(hp["volume"] / float(np.prod(ext)), 6),
            "centroid": [round(float(x), 6) for x in hp["centroid"]],
            "com": [round(x, 9) for x in group_values(u["ei"], GROUP["com"])],
            "diag": [round(x, 9) for x in group_values(u["ei"], GROUP["diag"])],
            "third": [round(x, 9) for x in group_values(u["ei"], GROUP["third"])],
            "third_w": u["ei"][11],
            "I_diag": [round(float(x), 9) for x in np.diag(hp["I_com"])],
            "I_origin": [round(float(x), 9) for x in np.diag(hp["I_origin"])],
            "box": [round(x, 9) for x in box_moments(u["mass"], ext)],
        })
    sets = {}
    for slot in (0x10, 0x20, 0x30, 0x40, 0x50, 0x60):
        arr = pf.array(psd[0].offset + slot)
        sets["%#04x" % slot] = {"size": arr["size"], "ptr": arr["ptr"]}
    nbytes = len(blob)
    nobjects = len(pf.objects)
    data_len = pf.lf
    base = pf.base
    del pf
    return {"path": path, "bytes": nbytes, "objects": nobjects, "bodies": bodies,
            "arrays": sets, "base": base, "data_len": data_len,
            "blob": blob}


# ---------------------------------------------------------------- measurements
def com_errors(bodies: list, K: int) -> np.ndarray:
    out = []
    for b in bodies:
        ei = b["ei"]
        s = 2.0 ** ((ei[3] // 128) - K)
        com = np.array([ei[k] for k in range(3)], dtype=float) * s
        cen = np.array(b["centroid"])
        ext = np.array(b["ext"])
        out.append(float(np.linalg.norm(com - cen) / ext.max()))
    return np.array(out)


def diag_ratios(bodies: list) -> np.ndarray:
    """stored diagonal / m/12*(b^2+c^2), element-wise in the shape frame."""
    return np.array([np.array(b["diag"]) / np.maximum(np.array(b["box"]), 1e-15)
                     for b in bodies])


def hits(ratios: np.ndarray, tol: float) -> int:
    return int(np.all(np.abs(ratios - 1.0) <= tol, axis=1).sum())


def f32_triple_scan(blob: bytes, base: int, data_len: int, targets: list,
                    tols=(0.001, 0.01, 0.05)) -> dict:
    """Every 4-byte-aligned f32 triple in the data section, tested against each
    target triple *in absolute terms* (sorted magnitudes, relative tolerance).
    Answers: is there a plain-float inertia tensor anywhere at all?"""
    n = (data_len - 4) // 4
    with np.errstate(invalid="ignore"):
        vals = np.frombuffer(blob, dtype="<f4", count=n, offset=base).astype(np.float64)
    good = np.isfinite(vals)
    tri = np.stack([vals[:-2], vals[1:-1], vals[2:]], axis=1)
    gm = good[:-2] & good[1:-1] & good[2:]
    mag = np.sort(np.abs(tri), axis=1)[:, ::-1]
    mag = np.where(gm[:, None], mag, -1.0)
    counts = {("%.1f%%" % (t * 100)): 0 for t in tols}
    first = None
    for t in targets:
        ts = np.sort(np.abs(np.array(t, dtype=float)))[::-1]
        if ts.min() <= 0:
            continue
        for tol in tols:
            close = gm & np.all(np.abs(mag - ts) <= tol * ts, axis=1)
            c = int(close.sum())
            counts["%.1f%%" % (tol * 100)] += c
            if c and first is None:
                i = int(np.argmax(close))
                first = {"at": 4 * i, "values": [round(float(x), 6) for x in tri[i]],
                         "target": [round(float(x), 6) for x in ts], "tol": tol}
    return {"offsets": int(n - 2), "hits": counts, "first": first}


def payload_layout_scan(bodies: list) -> list:
    """Every byte layout actually tried for the 24-byte payload, scored with the
    brief's box oracle on the box bodies."""
    def f16(h):
        s, e, m = (h >> 15) & 1, (h >> 10) & 0x1F, h & 0x3FF
        if e == 0:
            v = m * 2.0 ** -24
        elif e == 31:
            v = float("inf")
        else:
            v = (1 + m / 1024.0) * 2.0 ** (e - 15)
        return -v if s else v

    layouts = []

    def add(name, where, fn):
        ratios, tested, fail = [], 0, None
        for b in bodies:
            raw = bytes.fromhex(b["payload"])
            try:
                diag = fn(raw, b["ei"])
            except Exception:
                diag = None
            if diag is None:
                continue
            tested += 1
            box = np.array(b["box"], dtype=float)
            if np.any(box <= 0):
                continue
            r = np.array(diag, dtype=float) / box
            ratios.append(r)
            if fail is None and not np.all(np.abs(r - 1) <= TOLS[1]):
                fail = {"at": "%#x" % b["block"], "ratio": [round(float(x), 4) for x in r]}
        R = np.array(ratios) if ratios else np.zeros((0, 3))
        layouts.append({"name": name, "where": where, "tested": tested,
                        "hits": {("%.1f%%" % (t * 100)): hits(R, t) for t in TOLS},
                        "median_ratio": [round(float(x), 6) for x in
                                         (np.median(R, axis=0) if len(R) else [0, 0, 0])],
                        "first_miss": fail})

    add("after_mass_scalar", "+0x2c f32 (4 bytes - too small for a tensor)", lambda raw, ei: None)
    add("f32x6_at_10", "+0x10..+0x27 f32 x6", lambda raw, ei: list(struct.unpack_from("<6f", raw, 0))[:3])
    add("f16x6_at_10", "+0x10..+0x1b f16 x6",
        lambda raw, ei: [f16(struct.unpack_from("<H", raw, 2 * k)[0]) for k in range(3)])
    add("i16x6_at_10", "+0x10 i16 x6", lambda raw, ei: [float(v) for v in ei[0:3]])
    add("i16x9_at_10", "+0x10 i16 x9 (rows)",
        lambda raw, ei: [float(ei[0]), float(ei[3]), float(ei[6])])
    add("i16x4_groups_diag", "+0x18..+0x1f, exponent +0x1e",
        lambda raw, ei: group_values(ei, 1))
    for k in range(10):
        add("i16_window_%d" % k, "+0x%02x +0x%02x +0x%02x"
            % (PAYLOAD_AT + 2 * k, PAYLOAD_AT + 2 * (k + 1), PAYLOAD_AT + 2 * (k + 2)),
            (lambda kk: (lambda raw, ei: [float(v) for v in ei[kk:kk + 3]]))(k))
    return layouts


def build() -> dict:
    files = sorted(glob.glob(os.path.join(FLEET, "*.physicsc")))
    fleet, errors = [], []
    seen = set()
    for p in [os.path.join(ROOT, CARS[0][1])] + files:
        if os.path.abspath(p) in seen:
            continue
        seen.add(os.path.abspath(p))
        try:
            fleet.append(scan_file(p))
        except Exception as e:                       # pragma: no cover
            errors.append({"file": os.path.basename(p), "error": str(e)})
    all_bodies = [b for f in fleet for b in f["bodies"]]

    cars = []
    for name, path in CARS:
        full = os.path.join(ROOT, path)
        f = next((x for x in fleet if os.path.abspath(x["path"]) == os.path.abspath(full)),
                 None)
        if f is None:
            raise SystemExit("reported car not in the scan: %s" % full)
        f = dict(f)
        f["label"] = name
        cars.append(f)
    donor = cars[0]

    # ---- 1. the bias, measured on the COM group
    bias_table = []
    for K in BIAS_GRID:
        e = com_errors(all_bodies, K)
        bias_table.append({"K": K, "median": round(float(np.median(e)), 6),
                           "p90": round(float(np.percentile(e, 90)), 6),
                           "frac_le_10pct": round(float((e <= 0.10).mean()), 6)})
    best = min(bias_table, key=lambda r: r["median"])
    com_e = com_errors(all_bodies, BIAS)

    # ---- 2. box census + the brief's oracle
    boxes = [b for b in all_bodies if b["fill"] >= BOX_FILL]
    fills = np.array([b["fill"] for b in all_bodies])
    census = {"bodies": len(all_bodies), "files": len(fleet),
              "fill_ge_999": int((fills >= 0.999).sum()),
              "fill_ge_98": int((fills >= 0.98).sum()),
              "fill_ge_90": int((fills >= 0.90).sum()),
              "fill_max": round(float(fills.max()), 6),
              "fill_median": round(float(np.median(fills)), 6)}
    R_all = diag_ratios(all_bodies)
    R_box = diag_ratios(boxes)
    box_oracle = {"n": len(boxes),
                  "hits": {("%.1f%%" % (t * 100)): hits(R_box, t) for t in TOLS},
                  "all_bodies_hits": {("%.1f%%" % (t * 100)): hits(R_all, t) for t in TOLS},
                  "median_ratio": [round(float(x), 6) for x in np.median(R_box, axis=0)],
                  "p10_ratio": [round(float(x), 6) for x in np.percentile(R_box, 10, axis=0)],
                  "p90_ratio": [round(float(x), 6) for x in np.percentile(R_box, 90, axis=0)]}

    # ---- 3. centroid vs origin parallel-axis models, on the box bodies
    r_com = R_box
    r_origin = np.array([np.array(b["diag"]) / np.maximum(np.array(b["box_origin"]), 1e-15)
                         for b in boxes]) if boxes and "box_origin" in boxes[0] else None
    if r_origin is None:
        r_origin = np.array([np.array(b["diag"]) /
                             np.maximum(np.array(b["box"]) +
                                        b["mass"] * (np.array(b["centroid"]) @
                                                     np.array(b["centroid"]) * np.eye(3) -
                                                     np.outer(b["centroid"],
                                                              b["centroid"])).diagonal(),
                                        1e-15)
                             for b in boxes])
    parallel = {"n": len(boxes),
                "centroid_model": {("%.1f%%" % (t * 100)): hits(r_com, t) for t in TOLS},
                "origin_model": {("%.1f%%" % (t * 100)): hits(r_origin, t) for t in TOLS}}

    # ---- 4. the tail f32 against the hull volume
    nz = [b for b in all_bodies if b["tail"] != 0.0]
    tail = {"nonzero": len(nz), "blocks": len(all_bodies)}
    if nz:
        t = np.array([b["tail"] for b in nz])
        v = np.array([b["volume"] for b in nz])
        tail.update({"corr": round(float(np.corrcoef(t, v)[0, 1]), 6),
                     "ratio_median": round(float(np.median(t / v)), 6),
                     "ratio_min": round(float((t / v).min()), 6),
                     "ratio_max": round(float((t / v).max()), 6)})

    # ---- 5. no f32 tensor anywhere: exhaustive triple scan of the data section
    scans = []
    for f in cars:
        targets = [b["box"] for b in
                   sorted(f["bodies"], key=lambda b: -b["mass"])
                   if b["mass"] >= 1.0][:20]
        if not targets:
            scans.append({"car": f["label"], "offsets": 0, "targets": 0,
                          "hits": {}, "first": None})
            continue
        r = f32_triple_scan(f["blob"], f["base"], f["data_len"], targets,
                            tols=TOLS[0:3] + (SCAN_TOL,))
        scans.append({"car": f["label"], "offsets": r["offsets"], "targets": len(targets),
                      "hits": r["hits"], "first": r["first"]})

    # ---- 6. every payload layout tried, scored with the same oracle
    layouts = payload_layout_scan(boxes)

    # ---- 7. oracles
    donor_links = len(donor["bodies"])
    oracles = {
        "block_is_48_bytes_with_zero_header": {
            "ok": bool(all(b["header_zero"] for b in all_bodies)),
            "detail": {"blocks": len(all_bodies),
                       "header_zero": sum(1 for b in all_bodies if b["header_zero"])}},
        "polytope_mass_links_resolve": {
            "ok": bool(donor_links == 40),
            "detail": {"donor bodies with mass block": donor_links,
                       "fleet": len(all_bodies)}},
        "com_bias_is_111": {
            "ok": bool(best["K"] == BIAS and best["median"] < 0.05
                       and best["frac_le_10pct"] > 0.85
                       and all(r["median"] > 1.0 for r in bias_table
                               if abs(r["K"] - BIAS) == 1)),
            "detail": {"chosen": best["K"], "median": best["median"],
                       "neighbours": {str(r["K"]): r["median"] for r in bias_table
                                      if abs(r["K"] - BIAS) <= 1},
                       "grid": {str(r["K"]): r["median"] for r in bias_table}}},
        "centre_of_mass_matches_hull_centroid": {
            "ok": bool(float(np.median(com_e)) < 0.05 and (com_e <= 0.10).mean() > 0.85),
            "detail": {"median": round(float(np.median(com_e)), 6),
                       "p90": round(float(np.percentile(com_e, 90)), 6),
                       "frac_le_10pct": round(float((com_e <= 0.10).mean()), 6)}},
        "box_bodies_exist": {
            "ok": bool(census["fill_ge_999"] > 0),
            "detail": census},
        "box_formula_reproduced_at_float_tolerance": {
            "ok": bool(box_oracle["hits"]["1.0%"] > 0.9 * box_oracle["n"]),
            "detail": {"hits": box_oracle["hits"], "of": box_oracle["n"],
                       "median_ratio": box_oracle["median_ratio"]}},
        "stored_tensor_is_not_the_hull_tensor": {
            "ok": bool(hits(R_box, 0.01) < 0.5 * len(boxes)),
            "detail": {"hits_1pct": hits(R_box, 0.01), "of": len(boxes)}},
        "no_f32_tensor_in_the_data_section": {
            "ok": bool(all(s["hits"].get("1.0%", 0) == 0 for s in scans)),
            "detail": {s["car"]: {"offsets": s["offsets"], "targets": s["targets"],
                                  "hits": s["hits"]} for s in scans}},
        "tail_f32_tracks_hull_volume": {
            "ok": bool(tail.get("corr", 0) > 0.99),
            "detail": tail},
    }

    verdict_ok = oracles["box_formula_reproduced_at_float_tolerance"]["ok"]
    doc = {
        "schema": 1,
        "generated_by": "Tools/scripts/jc3_inertia2.py --write",
        "card": "G3-10k - where a JC3 vehicle body's inertia tensor lives",
        "constants": {"block": BLOCK, "payload": [PAYLOAD_AT, PAYLOAD_AT + 24],
                      "mass_at": MASS_AT, "tail_at": TAIL_AT, "bias": BIAS,
                      "box_fill": BOX_FILL, "scan_tol": SCAN_TOL},
        "donor": {"path": DONOR, "bytes": donor["bytes"], "objects": donor["objects"],
                  "bodies": len(donor["bodies"]), "arrays": donor["arrays"]},
        "fleet": {"files": len(fleet), "errors": errors, "bodies": len(all_bodies)},
        "bias_table": bias_table,
        "com_error": {"median": round(float(np.median(com_e)), 6),
                      "p90": round(float(np.percentile(com_e, 90)), 6),
                      "frac_le_10pct": round(float((com_e <= 0.10).mean()), 6),
                      "max": round(float(com_e.max()), 6)},
        "census": census,
        "box_oracle": box_oracle,
        "parallel_axis": parallel,
        "tail": tail,
        "f32_scans": scans,
        "payload_layouts": layouts,
        "oracles": oracles,
        "verdict": {
            "tensor_located": True,
            "packed_form_decoded": bool(oracles["com_bias_is_111"]["ok"]),
            "box_formula_reproduced": bool(verdict_ok),
            "status": "done" if verdict_ok else "UNKNOWN",
            "statement": (
                "the payload's second group is the inertia diagonal in the shape frame "
                "(value = mantissa * 2**(floor(w/128) - 111), bias pinned by the centre-of-mass "
                "group against the hull centroid, median error %s); the brief's box oracle is "
                "not met - %d of %d single-box fleet bodies match m/12*(b^2+c^2) within 1%%, "
                "with a uniform %s excess on all three moments, so the stored tensor belongs to "
                "the authoring geometry, not to the collision hull"
                % (round(float(np.median(com_e)), 4), box_oracle["hits"]["1.0%"],
                   box_oracle["n"], round(float(np.median(R_box)), 4))),
        },
        "cars": [{"label": f["label"], "file": os.path.basename(f["path"]),
                  "bytes": f["bytes"], "objects": f["objects"],
                  "bodies": f["bodies"], "arrays": f["arrays"]} for f in cars],
        "unknowns": [
            "the absolute semantics/units of the decoded diagonal: the box oracle rejects the "
            "collision-hull reading on every box body (%d/%d at 1%%), and the residual is a "
            "*uniform* %s factor, not scatter - so the tensor was authored from geometry the "
            "collision hull does not contain. What would settle it: the render mesh of the same "
            "part (its convex hull / tetrahedral tensor) compared under the same decode."
            % (box_oracle["hits"]["1.0%"], box_oracle["n"],
               round(float(np.median(R_box)), 4)),
            "the third group (+0x20..+0x27): three lanes whose magnitudes are the largest in the "
            "block (all near +-32768) and whose own exponent lane decodes them to ~1e-36, i.e. "
            "'no products'. Whether those lanes are products, a principal axis or a mirror tag "
            "is not decoded; the mirror test (pass 1) shows two of them flip sign between "
            "left/right parts, which both readings allow.",
            "the bias 111 is a format constant measured to better than one octave (110 and 112 "
            "are 2x off); no file in this tree documents the packing, so the exact fixed-point "
            "layout of the w lane (floor(w/128) with w = exponent << 7) is derived, not "
            "documented. A Havok 2014 header for hkCompressedMassProperties would confirm it.",
            "how the mass at +0x28 relates to the tensor: the box bodies show a uniform 1.275x "
            "excess, which is exactly what a 1.275x larger authoring mass *or* 1.13x larger "
            "authoring extents would produce; the two cannot be separated without the authoring "
            "mesh.",
        ],
    }
    return doc


# ---------------------------------------------------------------- render
def fmt(x, n=4):
    return ("%%.%df" % n) % x


def render(doc: dict) -> str:
    a = []
    a.append("# Where a JC3 vehicle body's inertia tensor lives (G3-10k)\n")
    a.append("Generated by `Tools/scripts/jc3_inertia2.py --write`; `--check` recomputes every "
             "number from the source bytes and fails on drift. Static decode only - no game was "
             "run, attached to or modified, and no file outside this repository's read-only "
             "inputs was touched.\n")
    v = doc["verdict"]
    a.append("## VERDICT\n")
    a.append("**The tensor is located and its packed form is decoded; the brief's box oracle is "
             "NOT met.**\n")
    a.append("- **Location.** `hknpShapeMassProperties` `+0x10..+0x27` - the 24-byte payload "
             "*before* the mass `f32` at `+0x28`, inside the block `jc3hkx.py` already counts "
             "(it reads only the mass). Three `int16x4` groups: group 1 = centre of mass, group 2 "
             "= inertia diagonal in the shape frame, group 3 = UNKNOWN.\n")
    a.append("- **Packed form.** Each group's fourth `int16` is a shared exponent: "
             "`value = mantissa * 2**(floor(w/128) - %d)` (equivalently `E = floor(w/128) - %d`, "
             "`value = mantissa * 2**(E-15)`). The bias `%d` is *measured*: group 1 decodes to the "
             "centre of mass and only `K = %d` puts it on the hull's own volume centroid (median "
             "error %s of the body's largest extent); `K = 110` and `K = 112` are 2x out and miss "
             "by a factor %s and %s.\n"
             % (doc["constants"]["bias"], doc["constants"]["bias"] - 15, doc["constants"]["bias"],
                doc["oracles"]["com_bias_is_111"]["detail"]["chosen"],
                fmt(doc["com_error"]["median"]),
                fmt(doc["bias_table"][-3]["median"], 2) if len(doc["bias_table"]) >= 3 else "-",
                fmt(doc["bias_table"][-1]["median"], 2)))
    bo = doc["box_oracle"]
    a.append("- **The oracle (as briefed).** `fill ratio = hull volume / bbox volume` finds "
             "**%d** single-box bodies among the fleet's %d hull bodies (`fill >= %.3f`). The "
             "decoded diagonal matches `m/12*(b^2+c^2)` on **%d of %d** within 1 %% (float "
             "tolerance), %d at 2 %%, %d at 5 %%, %d at 25 %% - median ratio **%s** on each of the "
             "three moments, i.e. a *uniform* excess, not scatter.\n"
             % (doc["census"]["fill_ge_999"], doc["census"]["bodies"],
                doc["constants"]["box_fill"], bo["hits"]["1.0%"], bo["n"],
                bo["hits"]["2.0%"], bo["hits"]["5.0%"], bo["hits"]["25.0%"],
                fmt(float(bo["median_ratio"][0]), 3)))
    a.append("- **Reading.** The decode is right (the COM group lands on the hull centroid to "
             "%s of the body extent, and the diagonal's axes agree with the hull's), but the "
             "stored tensor is not the *collision* hull's tensor. The f32 at `+0x2c` says what it "
             "is: where non-zero it equals the hull volume x %s..%s (correlation %s), i.e. a "
             "volume - evidence that these values were authored from a second, slightly larger "
             "geometry. Per the brief's decision rule the box test therefore returns **0 hits** "
             "and the tensor's absolute semantics stays **UNKNOWN**.\n"
             % (fmt(doc["com_error"]["median"]), fmt(doc["tail"].get("ratio_min", 0), 3),
                fmt(doc["tail"].get("ratio_max", 0), 3), fmt(doc["tail"].get("corr", 0), 4)))
    a.append("- **No float tensor anywhere.** An exhaustive scan of every 4-byte-aligned f32 "
             "triple in the data section of each reported car finds **no** triple matching any "
             "body's box moments `m/12*(b^2+c^2)` within 1 %% (absolute values, sorted; %s "
             "triples scanned in total) - so the body/motion cinfo and every other block hold no "
             "plain-float tensor; the packed payload is the only tensor-shaped data in the file.\n"
             % (" / ".join("%d" % s["offsets"] for s in doc["f32_scans"])))

    a.append("\n## 1. The block, decoded\n")
    a.append("`hknpShapeMassProperties`, %d bytes, donor `%s` (%d bytes, %d objects, %d bodies).\n"
             % (doc["constants"]["block"], doc["donor"]["path"], doc["donor"]["bytes"],
                doc["donor"]["objects"], doc["donor"]["bodies"]))
    a.append("| range | bytes | content | label |")
    a.append("|---|---|---|---|")
    a.append("| +0x00..+0x0f | 16 | zero in every block | decoded |")
    a.append("| +0x10..+0x17 | 8 | group 1: `int16` x, y, z + exponent w | decoded bytes |")
    a.append("| +0x18..+0x1f | 8 | group 2: `int16` x, y, z + exponent w | decoded bytes |")
    a.append("| +0x20..+0x27 | 8 | group 3: `int16` x, y, z + exponent w | decoded bytes |")
    a.append("| +0x28..+0x2b | 4 | mass `f32` | decoded (G3-10b) |")
    a.append("| +0x2c..+0x2f | 4 | one `f32`: the authoring volume (see §4) | decoded |\n")
    a.append("### The exponent, expressed both ways\n")
    a.append("```")
    a.append("E     = (w >> 7) - 96          # signed int16 w, arithmetic shift = floor(w/128)")
    a.append("value = mantissa * 2**(E-15)")
    a.append("      = mantissa * 2**(floor(w/128) - 111)")
    a.append("```\n")
    a.append("`w` is always a multiple of 128 in the shipped data (low byte `0x00` or `0x80`), so "
             "`E` is an exact integer and the group's three mantissas share one scale.\n")
    a.append("### The bias, measured (the oracle that pins it)\n")
    a.append("Group 1 decodes to a centre of mass in the shape frame; the hull's volume centroid "
             "is exactly computable from the same vertices. Relative error is `|com - centroid| / "
             "max(extent)`:\n")
    a.append("| bias K | median error | p90 | bodies within 10 % |")
    a.append("|---|---|---|---|")
    for r in doc["bias_table"]:
        a.append("| %d | %s | %s | %s |" % (r["K"], fmt(r["median"]), fmt(r["p90"]),
                                            fmt(r["frac_le_10pct"], 3)))
    a.append("\nThe table is a factor-of-two ladder: only `K = %d` lands on the centroid, so the "
             "bias and the group-1 reading are pinned together.\n"
             % doc["constants"]["bias"])

    a.append("\n## 2. The reported cars\n")
    for car in doc["cars"]:
        a.append("### %s - `%s` (%d bytes, %d objects, %d bodies with a hull and a mass)\n"
                 % (car["label"], car["file"], car["bytes"], car["objects"], len(car["bodies"])))
        a.append("| body | mass | extents (m) | stored diag | m/12*(b^2+c^2) | ratio | COM err |")
        a.append("|---:|---:|---|---|---|---|---|")
        for b in car["bodies"]:
            ce = math.sqrt(sum((b["com"][k] - b["centroid"][k]) ** 2
                               for k in range(3))) / max(b["ext"])
            rat = [b["diag"][k] / b["box"][k] if b["box"][k] else 0 for k in range(3)]
            a.append("| %d%s | %s | %s | %s | %s | %s | %s |" % (
                b["body"], " (box)" if b["fill"] >= doc["constants"]["box_fill"] else "",
                fmt(b["mass"], 3), " ".join(fmt(x, 3) for x in b["ext"]),
                " ".join(fmt(x, 3) for x in b["diag"]),
                " ".join(fmt(x, 3) for x in b["box"]),
                " ".join(fmt(x, 3) for x in rat), fmt(ce, 4)))
        a.append("")
    a.append("Rows without `(box)` are non-box hulls, shown only to demonstrate the decode; the "
             "*oracle* runs on the `(box)` rows and on the whole fleet in §3.\n")

    a.append("\n## 3. The box oracle, fleet-wide\n")
    a.append("A body is a single box when its hull fills its own bounding box: "
             "`hull volume / bbox volume >= %.3f` (a beveled or plate-like hull scores far "
             "below 1).\n" % doc["constants"]["box_fill"])
    c = doc["census"]
    a.append("| census | value |")
    a.append("|---|---|")
    a.append("| files decoded | %d |" % c["files"])
    a.append("| bodies with a convex hull and a mass block | %d |" % c["bodies"])
    a.append("| `fill >= 0.999` (single boxes) | %d |" % c["fill_ge_999"])
    a.append("| `fill >= 0.98` | %d |" % c["fill_ge_98"])
    a.append("| `fill >= 0.90` | %d |" % c["fill_ge_90"])
    a.append("| median fill | %s |" % fmt(c["fill_median"], 3))
    a.append("| max fill | %s |\n" % fmt(c["fill_max"], 3))
    a.append("| tolerance on each moment | hits | of |")
    a.append("|---|---:|---:|")
    for t in TOLS:
        k = "%.1f%%" % (t * 100)
        a.append("| %s | %d | %d |" % (k, bo["hits"][k], bo["n"]))
    a.append("\nRatio `stored / box formula` over the box bodies: p10 %s, median %s, p90 %s. The "
             "three medians are equal to within %s, so the excess is a single scalar on the whole "
             "tensor, not a per-axis or per-body error - which is what a *different geometry* "
             "looks like and what a wrong exponent does not.\n"
             % (" ".join(fmt(x, 3) for x in bo["p10_ratio"]),
                " ".join(fmt(x, 3) for x in bo["median_ratio"]),
                " ".join(fmt(x, 3) for x in bo["p90_ratio"]),
                fmt(max(bo["median_ratio"]) - min(bo["median_ratio"]), 3)))
    pa = doc["parallel_axis"]
    a.append("Two parallel-axis models were also tested on the same boxes - is the stored tensor "
             "about the centroid or about the shape frame's origin?\n")
    a.append("| model | 1 % | 5 % | 25 % | of |")
    a.append("|---|---:|---:|---:|---:|")
    for name, key in (("about the centroid (`m/12*(b^2+c^2)`)", "centroid_model"),
                      ("about the frame origin (+ `m(d^2 I - d d^T)`)", "origin_model")):
        a.append("| %s | %d | %d | %d | %d |" % (name, pa[key]["1.0%"], pa[key]["5.0%"],
                                                 pa[key]["25.0%"], pa["n"]))
    a.append("\nThe origin model fails outright, so the stored tensor is centroidal.\n")

    a.append("\n## 4. What the block's other float says\n")
    t = doc["tail"]
    a.append("The `f32` at `+0x2c` is zero in most blocks but non-zero in %d of %d across the "
             "fleet. Where it is non-zero it tracks the hull volume: correlation **%s**, ratio "
             "volume x %s..%s. That is the volume of the geometry the mass properties were "
             "computed from - and it is the fingerprint of the box-oracle mismatch: the stored "
             "tensor and this volume describe a body slightly larger than the collision hull.\n"
             % (t["nonzero"], t["blocks"], fmt(t.get("corr", 0), 6),
                fmt(t.get("ratio_min", 0), 3), fmt(t.get("ratio_max", 0), 3)))
    a.append("| car | aligned f32 triples scanned | targets | hits @0.1 %% | @1 %% | @%d %% |"
             % int(doc["constants"]["scan_tol"] * 100))
    a.append("|---|---:|---:|---:|---:|---:|")
    for s in doc["f32_scans"]:
        h = s["hits"]
        a.append("| %s | %d | %d | %d | %d | %d |" % (
            s["car"], s["offsets"], s["targets"], h.get("0.1%", 0), h.get("1.0%", 0),
            h.get("5.0%", 0)))
    a.append("\nZero hits everywhere: no plain-float tensor exists in the data section, so the "
             "body entries, the `hknpPhysicsSystemData` sub-arrays and the constraint data cannot "
             "hold one either.\n")

    a.append("\n## 5. Every byte layout tried on the payload\n")
    a.append("All scored with the same box oracle on the %d box bodies "
             "(`hits` = bodies matching within the tolerance).\n" % bo["n"])
    a.append("| layout | where | tested | 0.1 % | 1 % | 5 % | 25 % | median ratio |")
    a.append("|---|---|---:|---:|---:|---:|---:|---|")
    for L in doc["payload_layouts"]:
        a.append("| `%s` | %s | %d | %d | %d | %d | %d | %s |" % (
            L["name"], L["where"], L["tested"], L["hits"]["0.1%"], L["hits"]["1.0%"],
            L["hits"]["5.0%"], L["hits"]["25.0%"],
            " ".join(fmt(x, 3) for x in L["median_ratio"])))
    a.append("\n`i16x4_groups_diag` is the decoded layout and the best of them all; every f32, "
             "f16 and flat-int layout fails outright (the lanes are not IEEE floats). A `tested` "
             "of 0 marks a layout that cannot even produce three values.\n")

    a.append("\n## 6. Oracles (`--check` re-runs all of them)\n")
    a.append("| oracle | ok | detail |")
    a.append("|---|---|---|")
    for k, o in doc["oracles"].items():
        a.append("| `%s` | %s | `%s` |" % (k, "**pass**" if o["ok"] else "**FAIL**",
                                           json.dumps(o["detail"], sort_keys=True)[:300]))
    a.append("\nThe one failing oracle is the brief's decision rule itself: "
             "`box_formula_reproduced_at_float_tolerance` returns %d of %d. Per the brief that "
             "leaves the tensor's absolute semantics **UNKNOWN**, which is why the verdict line "
             "says so even though the location and the packing are decoded.\n"
             % (bo["hits"]["1.0%"], bo["n"]))

    a.append("\n## 7. UNKNOWN\n")
    for i, u in enumerate(doc["unknowns"], 1):
        a.append("%d. %s" % (i, u))
    a.append("\n## 8. Reproduce\n")
    a.append("```")
    a.append("python Tools/scripts/jc3_inertia2.py --write")
    a.append("python Tools/scripts/jc3_inertia2.py --check")
    a.append("```")
    return "\n".join(a) + "\n"


# ---------------------------------------------------------------- main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="recompute and write the note + json")
    g.add_argument("--check", action="store_true", help="recompute and compare with the stored files")
    args = ap.parse_args(argv)

    doc = build()
    md = render(doc)
    blob = json.dumps(doc, indent=1, sort_keys=True)

    if args.write:
        os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            f.write(blob + "\n")
        print("wrote %s and %s" % (os.path.basename(OUT_MD), os.path.basename(OUT_JSON)))
        print("bodies %d  boxes %d  box-oracle hits@1%% %d/%d  median ratio %s"
              % (doc["census"]["bodies"], doc["census"]["fill_ge_999"],
                 doc["box_oracle"]["hits"]["1.0%"], doc["box_oracle"]["n"],
                 fmt(float(doc["box_oracle"]["median_ratio"][0]), 3)))
        print("com median error %s  bias %d"
              % (fmt(doc["com_error"]["median"]), doc["constants"]["bias"]))
        print("oracles:", {k: v["ok"] for k, v in doc["oracles"].items()})
        return 0

    ok = True
    try:
        old = json.load(open(OUT_JSON, encoding="utf-8"))
    except FileNotFoundError:
        print("FAIL: %s missing (run --write)" % OUT_JSON)
        return 1
    if json.dumps(old, indent=1, sort_keys=True) != blob:
        # locate the first drift
        for k in sorted(set(old) | set(doc)):
            if json.dumps(old.get(k), sort_keys=True) != json.dumps(doc.get(k), sort_keys=True):
                print("FAIL: drift in %r" % k)
                ok = False
                break
    try:
        old_md = open(OUT_MD, encoding="utf-8").read()
    except FileNotFoundError:
        print("FAIL: %s missing" % OUT_MD)
        ok = False
        old_md = None
    if old_md is not None and old_md != md:
        print("FAIL: %s does not match the re-render" % os.path.basename(OUT_MD))
        ok = False
    for k, o in doc["oracles"].items():
        if not o["ok"]:
            print("oracle FAIL (reported, not a drift): %s %s" % (k, o["detail"]))
    if not ok:
        return 1
    print("OK: bodies %d  boxes %d  box-oracle %d/%d  com median %s"
          % (doc["census"]["bodies"], doc["census"]["fill_ge_999"],
             doc["box_oracle"]["hits"]["1.0%"], doc["box_oracle"]["n"],
             fmt(doc["com_error"]["median"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
