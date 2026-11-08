#!/usr/bin/env python
"""v02a_rc4.py - V-02 part A only, on the shipped build `Builds/bm-RC4` (offline, read-only).

Built from the V-02 template `v02_geometry.py` (not `v02_render.py`) and pointed at RC4. No render,
no pose, no light gate: the four gates of part A, measured on the build and on the packed `.ee`.

  silhouette   non-wheel BmAK body vs the RC4 `sportsmuscle_body_lod1.rbm`, one fixed frame per
               view (side, front, top). Gate 99.9 % per view; margin printed per view and compared
               with RC2's own `Builds/bm-RC2/verify/geometry.json`.
  census       the RC4 parts module: 59 parts / 19 distinct damage types (build-d08 section 2);
               every part model resolves; which indices are absent.
  interaction  `t9_interaction.build()` with `jc3interact.read_bat_mesh` pointed at the RC4 body:
               5 cm <= d <= 30 cm, no point outside the envelope by more than 2 cm.
  collision    the packed `sportsmuscle.physicsc` re-decoded (the member inside the shipped `.ee`,
               not a report text): body-0 hull shape/placement vs BmAK chassis box 0, hulls that
               differ from the donor, free hull slots, which of BmAK's 3 boxes have a shape, and
               the constraint count. The brief's [0.0005, 0.061, 0.0025] m (6.1 cm) is printed as
               the superseded payload's figure; it is never counted as a pass.

Usage:
    python Tools/scripts/v02a_rc4.py --gate silhouette
    python Tools/scripts/v02a_rc4.py --gate census
    python Tools/scripts/v02a_rc4.py --gate interaction
    python Tools/scripts/v02a_rc4.py --gate collision
    python Tools/scripts/v02a_rc4.py --gate all

Every gate prints JSON to stdout and also writes `tmp/freebuff/verify-v02a/<gate>.json`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bm_parts            # noqa: E402
import jc3hkx as H         # noqa: E402
import jc3interact         # noqa: E402
import rbm_geom            # noqa: E402
import silhouette_check as SC   # noqa: E402
import t9_interaction      # noqa: E402
from eetoc import sarc_dir, unaaf   # noqa: E402

BUILD = os.path.join(ROOT, "Builds", "bm-RC4")
AAF = os.path.join(BUILD, "aaf")
VEH = os.path.join(AAF, "models", "jc_vehicles", "01_land",
                   "v0300_car_kensington_sportsmuscle")
BODY = os.path.join(VEH, "sportsmuscle_body_lod1.rbm")
PARTS = os.path.join(VEH, "sportsmuscle_vehicle_parts.vmodc")
PHYS = os.path.join(VEH, "sportsmuscle.physicsc")
EE = os.path.join(BUILD, "drop", "editor", "entities", "jc_vehicles", "01_land",
                  "v0300_car_kensington_sportsmuscle",
                  "v0300_car_kensington_sportsmuscle_debug.ee")
DONOR_PHYS = os.path.join(ROOT, "Builds", "test-091", "aaf", "models", "jc_vehicles",
                          "01_land", "v0300_car_kensington_sportsmuscle",
                          "sportsmuscle.physicsc")
STATIONS = os.path.join(ROOT, "Working", "Appearance", "build", "stations.json")
RC2_GEO = os.path.join(ROOT, "Builds", "bm-RC2", "verify", "geometry.json")
HULL_JSON = os.path.join(ROOT, "Working", "Collision2", "bm_vehicle_hull.json")
OUT = os.path.join(ROOT, "tmp", "freebuff", "verify-v02a")
SIL_MIN = 0.999
BUD1_HOLES_PCT = 0.3
BAND = (0.05, 0.30)
ENV_TOL = 0.02
BRIEF_PLACEMENT_M = [0.0005, 0.061, 0.0025]
BRIEF_LIMIT_M = 0.05


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def emit(gate: str, doc: dict) -> None:
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"{gate}.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(doc, indent=1) + "\n")
    print(json.dumps(doc, indent=1))


# ------------------------------------------------------------------ silhouette
def _pack(tris, view):
    ax = {"side": (2, 1), "front": (0, 1), "top": (0, 2)}[view]
    out = np.zeros_like(tris)
    out[:, :, 2] = tris[:, :, ax[0]]
    out[:, :, 1] = tris[:, :, ax[1]]
    return out


def _view(src, ours, offset, view):
    src = src + np.asarray(offset, np.float64)
    PS, PO = _pack(src, view), _pack(ours, view)
    p = PS.reshape(-1, 3)[:, [2, 1]]
    lo, hi = p.min(0), p.max(0)
    m = 0.02 * float((hi - lo).max())
    lo, hi = lo - m, hi + m
    S = SC.rasterize(PS, lo, hi, 2400)
    O = SC.rasterize(PO, lo, hi, 2400)
    holes, extra = S & ~O, O & ~S
    tears = holes & SC.erode(S, 3)
    cov = float(O.sum()) / float(S.sum())
    holes_pct = 100.0 * float(holes.sum()) / float(S.sum())
    return {
        "frame": [int(S.shape[1]), int(S.shape[0])],
        "source_px": int(S.sum()), "ours_px": int(O.sum()),
        "coverage": round(cov, 6),
        "margin_pp": round(100.0 * (cov - SIL_MIN), 4),
        "holes_px": int(holes.sum()), "holes_pct": round(holes_pct, 4),
        "tears_px": int(tears.sum()),
        "tears_pct": round(100.0 * float(tears.sum()) / float(S.sum()), 4),
        "extra_px": int(extra.sum()),
        "extra_pct": round(100.0 * float(extra.sum()) / float(S.sum()), 4),
        "bud1_pass": holes_pct < BUD1_HOLES_PCT,
        "pass": cov >= SIL_MIN,
    }


def gate_silhouette() -> dict:
    src = SC.body_tris(*SC.P.read_pskx(SC.PSKX)[:3])
    blob = open(BODY, "rb").read()
    ours = np.concatenate([SC.PR.block_triangles(b) for b in rbm_geom.decode(blob).blocks])
    ours = ours[np.linalg.norm(np.cross(ours[:, 1] - ours[:, 0],
                                        ours[:, 2] - ours[:, 0]), axis=1) > 1e-9]
    off = json.load(open(STATIONS, encoding="utf-8"))["offset"]
    views = {v: _view(src, ours, off, v) for v in ("side", "front", "top")}
    body_sha = sha(blob)

    rc2 = None
    if os.path.exists(RC2_GEO):
        d2 = json.load(open(RC2_GEO, encoding="utf-8"))["silhouette"]
        s2 = d2["with_build_offset"]
        rc2 = {
            "geometry_json": rel(RC2_GEO),
            "mesh_sha256": d2.get("rbm_sha256"),
            "same_mesh": d2.get("rbm_sha256") == body_sha,
            "offset_m": d2.get("offset_m"),
            "offset_same": d2.get("offset_m") == [round(float(x), 6) for x in off],
            "side_source_px": s2.get("source_px"),
            "side_ours_px": s2.get("ours_px"),
            "side_coverage": s2.get("coverage"),
            "side_margin_pp": round(100.0 * (float(s2["coverage"]) - SIL_MIN), 4),
            "side_px_delta": int(views["side"]["ours_px"] - int(s2.get("ours_px", 0))),
            "side_holes_pct": s2.get("holes_pct"),
        }
    return {
        "gate": "silhouette",
        "command": "python Tools/scripts/v02a_rc4.py --gate silhouette",
        "rbm": rel(BODY), "rbm_sha256": body_sha,
        "body_bytes": len(blob), "ours_tris": int(len(ours)),
        "source": rel(SC.PSKX), "source_body_faces": SC.BODY_FACES,
        "source_split_faces": int(len(src)),
        "offset_m": [round(float(x), 6) for x in off], "offset_source": rel(STATIONS),
        "views": views,
        "rc2": rc2,
        "pass": all(q["pass"] for q in views.values()),
        "min_margin_pp": min(q["margin_pp"] for q in views.values()),
        "bud1_pass": all(q["bud1_pass"] for q in views.values()),
    }


# ------------------------------------------------------------------ census
def gate_census() -> dict:
    aaf_blob = open(PARTS, "rb").read()
    ee_stream = unaaf(open(EE, "rb").read())
    ents = sarc_dir(ee_stream)
    name, eo, ez = next((n, o, z) for n, o, z in ents
                        if n.endswith("sportsmuscle_vehicle_parts.vmodc"))
    ee_blob = ee_stream[eo:eo + ez]
    parts = bm_parts.decode_parts(aaf_blob)
    ee_parts = bm_parts.decode_parts(ee_blob)
    missing = [p["name"] for p in parts if not os.path.exists(os.path.join(AAF, p["model"]))]
    types = sorted({p["damage_type"] for p in parts})
    idx = sorted(p["part_index"] for p in parts)
    absent = [i for i in range(max(idx) + 1) if i not in set(idx)]
    return {
        "gate": "census",
        "command": "python Tools/scripts/v02a_rc4.py --gate census",
        "module_aaf": rel(PARTS), "module_aaf_sha256": sha(aaf_blob), "module_aaf_bytes": len(aaf_blob),
        "module_ee": f"{rel(EE)}::{name}", "module_ee_sha256": sha(ee_blob),
        "module_ee_bytes": len(ee_blob), "aaf_matches_ee": sha(aaf_blob) == sha(ee_blob),
        "parts": len(parts), "distinct_types": len(types), "types": types,
        "ee_parts": len(ee_parts), "ee_distinct_types": len({p["damage_type"] for p in ee_parts}),
        "expected": {"parts": 59, "types": 19, "source": "build-d08 section 2"},
        "indices": idx, "absent_indices": absent,
        "missing_models": missing, "models_resolved": len(parts) - len(missing),
        "lamp_parts": sum(1 for p in parts if p.get("has_lights")),
        "extra_beyond_59": [p["name"] for p in parts[59:]],
        "pass": len(parts) == 59 and len(types) == 19 and not missing and absent == [1, 2],
    }


# ------------------------------------------------------------------ interaction
def gate_interaction() -> dict:
    v, t, _m = rbm_geom.collect_mesh(rbm_geom.decode(open(BODY, "rb").read()))
    V, T = np.array(v, float), np.array(t, np.int64)
    jc3interact.read_bat_mesh = lambda: (V, T)
    doc = t9_interaction.build()
    placed = [r for r in doc["objects"] if r["disposition"] == "placed"]
    d = [r["measure"]["nearest_m"] for r in placed]
    lo, hi = BAND
    out_band = [r for r in placed if not (lo <= r["measure"]["nearest_m"] <= hi)]
    inside = [r["name"] for r in placed if r["measure"].get("inside")]
    worst = max([lo - x for x in d if x < lo] + [x - hi for x in d if x > hi] + [0.0])
    return {
        "gate": "interaction",
        "command": "python Tools/scripts/v02a_rc4.py --gate interaction",
        "mesh": {"file": rel(BODY), "sha256": sha(open(BODY, "rb").read()),
                 "vertices": int(len(V)), "triangles": int(len(T)),
                 "bbox_m": [[round(float(x), 4) for x in V.min(0)],
                            [round(float(x), 4) for x in V.max(0)]]},
        "band_m": [lo, hi], "envelope_tolerance_m": ENV_TOL,
        "objects": len(doc["objects"]), "placed": len(placed),
        "in_band": len(placed) - len(out_band),
        "distances_m": {"min": round(float(min(d)), 4), "max": round(float(max(d)), 4)},
        "failures": [{"name": r["name"], "nearest_m": r["measure"]["nearest_m"],
                      "verdict": r["verdict"]} for r in out_band],
        "inside_hull": inside,
        "worst_outside_m": round(float(worst), 4),
        "counts": doc["counts"],
        "pass": not out_band and not inside and worst <= ENV_TOL,
    }


# ------------------------------------------------------------------ collision
def _ee_member(suffix: str) -> tuple[str, bytes]:
    stream = unaaf(open(EE, "rb").read())
    n, o, z = next((n, o, z) for n, o, z in sarc_dir(stream) if n.endswith(suffix))
    return n, stream[o:o + z]


def _box_jc3(row: dict) -> dict:
    """box_tms (PSK axes: x length, y width, z height) -> JC3 axes (x width, y height, z length).

    Mapping used: JC3 x <- extent/centre index 1, JC3 y <- index 2, JC3 z <- index 0.
    Corroborated by the record's own pskx bounds (x 702.56 length, y 349.53 width, z 234.185
    height) and by box 0 landing at y 0.030..2.105 m, the floor 8390 names.
    """
    c = row["translation_cm"]
    e = row["extents_cm"]
    half = [e[1] / 200.0, e[2] / 200.0, e[0] / 200.0]
    cen = [c[1] / 100.0, c[2] / 100.0, c[0] / 100.0]
    return {"min": [cen[i] - half[i] for i in range(3)],
            "max": [cen[i] + half[i] for i in range(3)],
            "size": [2.0 * h for h in half]}


def gate_collision() -> dict:
    member, blob = _ee_member("sportsmuscle.physicsc")
    aaf_blob = open(PHYS, "rb").read()
    donor_blob = open(DONOR_PHYS, "rb").read()
    pf = H.Packfile(blob)
    s = H.summary(pf)
    pfd = H.Packfile(donor_blob)

    # every compound shape instance, with the hull's world AABB
    hulls, referenced, all_instances = [], {}, []
    for o in pf.objects:
        if o.cls not in H.COMPOUND_CLASSES:
            continue
        for inst in H.decode_compound(pf, o.offset, o.cls)["instances"]:
            all_instances.append(inst)
            if inst["shape_class"] != H.POLYTOPE:
                continue
            base = H.decode_polytope(pf, inst["shape"])["bounds"]
            wb = H.transform_aabb(base, inst["basis"], inst["translation"])
            referenced[inst["shape"]] = referenced.get(inst["shape"], 0) + 1
            hulls.append({"shape": f"{inst['shape']:#x}", "part_index": inst["part_index"],
                          "instance": inst["index"],
                          "translation": [round(float(x), 6) for x in inst["translation"]],
                          "min": [round(float(x), 6) for x in wb["min"]],
                          "max": [round(float(x), 6) for x in wb["max"]],
                          "size": [round(float(wb["max"][i] - wb["min"][i]), 6) for i in range(3)]})

    body = [h for h in hulls if h["part_index"] == 0]
    if len(body) != 1:
        raise SystemExit(f"expected 1 part-0 hull, got {len(body)}")
    tgt = _box_jc3(next(r for r in json.load(open(HULL_JSON, encoding="utf-8"))["box_tms"]
                        if r["export"] == 169750 and r["box"] == 0))
    b = body[0]
    size_dev = max(abs(b["size"][i] - tgt["size"][i]) for i in range(3))
    place = [max(abs(b["min"][i] - tgt["min"][i]), abs(b["max"][i] - tgt["max"][i]))
             for i in range(3)]

    # which hulls differ from the original donor. Compare DECODED vertices/planes, not object
    # bytes: a polytope's arrays sit outside its object extent, so a byte slice is not the hull.
    def sig(pack, off):
        d = H.decode_polytope(pack, off)
        return (d["vertex_count"], d["plane_count"],
                sorted(tuple(round(float(c), 5) for c in v) for v in d["vertices"]))

    changed = []
    for o in pf.objects:
        if o.cls != H.POLYTOPE:
            continue
        if sig(pf, o.offset) != sig(pfd, o.offset):
            parts = sorted({h["part_index"] for h in hulls if h["shape"] == f"{o.offset:#x}"})
            ds, dd = H.decode_polytope(pf, o.offset), H.decode_polytope(pfd, o.offset)
            changed.append({
                "shape": f"{o.offset:#x}", "part_indices": parts,
                "ship_size_m": [round(float(ds["bounds"]["max"][i] - ds["bounds"]["min"][i]), 6)
                                for i in range(3)],
                "donor_size_m": [round(float(dd["bounds"]["max"][i] - dd["bounds"]["min"][i]), 6)
                                 for i in range(3)]})

    # BmAK's 3 boxes vs the hulls actually in the file (extent match within 1 cm)
    boxes, carried = [], 0
    for r in json.load(open(HULL_JSON, encoding="utf-8"))["box_tms"]:
        bx = _box_jc3(r)
        best, dev = None, None
        for h in hulls:
            dmax = max(abs(h["size"][i] - bx["size"][i]) for i in range(3))
            if dev is None or dmax < dev:
                best, dev = h, dmax
        ok = dev is not None and dev <= 0.01
        carried += ok
        boxes.append({"export": r["export"], "bone": r["bone"], "box": r["box"],
                      "size_m": [round(x, 6) for x in bx["size"]],
                      "nearest_hull_part_index": best["part_index"] if best else None,
                      "best_size_dev_m": round(float(dev), 6) if dev is not None else None,
                      "has_shape": ok})

    classes = s["class_counts"]
    constraints = sum(v for k, v in classes.items() if "Constraint" in k)
    free_slots = s["polytopes"] - len(referenced)
    return {
        "gate": "collision",
        "command": "python Tools/scripts/v02a_rc4.py --gate collision",
        "shipped_member": f"{rel(EE)}::{member}",
        "sha256": sha(blob), "bytes": len(blob),
        "aaf_copy": rel(PHYS), "aaf_copy_sha256": sha(aaf_blob),
        "aaf_matches_ee": sha(aaf_blob) == sha(blob),
        "donor": rel(DONOR_PHYS), "donor_sha256": sha(donor_blob),
        "donor_bytes": len(donor_blob),
        "objects": s["objects"], "polytopes": s["polytopes"],
        "polytopes_convex": s["polytopes_convex"],
        "shape_instances": len(all_instances),
        "hull_instances": len(hulls),
        "hull_shapes_referenced": len(referenced),
        "free_hull_slots": free_slots,
        "hulls_differing_from_donor": changed,
        "hulls_written": len(changed),
        "donor_bodies": json.load(open(HULL_JSON, encoding="utf-8"))["bodies"]["bodies"],
        "body0_hull": b,
        "chassis_box_0": {"min": [round(x, 6) for x in tgt["min"]],
                          "max": [round(x, 6) for x in tgt["max"]],
                          "size_m": [round(x, 6) for x in tgt["size"]]},
        "shape_dev_m": round(float(size_dev), 6),
        "placement_dev_m": [round(float(x), 6) for x in place],
        "placement_cm": round(100.0 * max(place), 2),
        "limit_m": BRIEF_LIMIT_M,
        "boxes": boxes, "boxes_decoded": len(boxes), "boxes_carried": carried,
        "constraint_objects": constraints,
        "constraint_brief": "Physics.Batmobile_V3_Physics declares 1 constraint; named omission "
                            "(no JC3 constraint writer)",
        "brief_payload": {
            "placement_m": BRIEF_PLACEMENT_M,
            "max_placement_m": max(BRIEF_PLACEMENT_M),
            "gate_pass": max(BRIEF_PLACEMENT_M) <= BRIEF_LIMIT_M,
            "sha256": "0164936b928f821c058c5a154a93b7cadcdbb9baca7d44fb67cb8f18a9399323",
            "file_present_in_rc4_tree": False,
            "source": "build-d08 section 4 / build-d13 section 2; corrected in "
                      "tmp/freebuff/reports/correction-8390-collision-placement.md section 2",
        },
        "three_point_one_is_not_a_pass": True,
        "render_bbox_not_a_gate": True,
        "pass": max(place) <= BRIEF_LIMIT_M and size_dev <= BRIEF_LIMIT_M,
    }


GATES = {"silhouette": gate_silhouette, "census": gate_census,
         "interaction": gate_interaction, "collision": gate_collision}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gate", required=True, choices=[*GATES, "all"])
    a = ap.parse_args()
    if a.gate == "all":
        for name, fn in GATES.items():
            emit(name, fn())
    else:
        emit(a.gate, GATES[a.gate]())


if __name__ == "__main__":
    main()
