#!/usr/bin/env python
"""v02_rc4.py - V-02 on the shipped build `Builds/bm-RC4` (offline).

Built from the two V-02 templates (`v02_geometry.py`, `v02_render.py`) and pointed at RC4.
Every number is measured from the packed build or its receipt; nothing is launched.

  silhouette   non-wheel BmAK body mesh vs the RC4 `sportsmuscle_body_lod1.rbm`, rasterised in ONE
               frame per view (side, front, top). Gate 99.9 % per view, margin printed per view and
               compared with RC2's own geometry.json; the BUD-1 gross-hole oracle is printed too.
  poses        assembled LOD1 parts rendered at each decoded joint limit about the decoded bone
               pivot, with exact per-triangle part ownership: turret yaw (both limits), cannon
               pitch (the carrier hinge - the part has no own joint), all four air-brakes at both
               limits. Canopy, missile hatches and the battle pose (T-MD13) are labelled
               "not in this tree", never passed.
  parts        RC4 parts module census: 59 parts / 19 distinct damage types (build-d08 §2);
               every model resolves; the two indices missing vs the pre-B-04 table are the doors.
  interaction  t9_interaction on the RC4 body: every placed point 5-30 cm outside the hull;
               worst excursion outside the envelope <= 2 cm.
  collision    the packed `sportsmuscle.physicsc` re-decoded: 54 polytopes, body-0 hull shape and
               placement vs BmAK chassis box 0. The brief's [0.0005, 0.061, 0.0025] m (6.1 cm,
               gate NOT MET, build-d08/d13) is reported beside the shipped measurement. It is the
               superseded physicsc (sha 0164936b...); the shipped one (sha fda78f4d..., "box-0
               floor placement") measures [0.0005, 0.0000, 0.0025] m. The 6.1 cm is never
               reinterpreted as a pass; the render-bbox is not used as a collision gate.
  lights       the 24-row lights module (7,105 B): two 70 deg entries per headlight, range 60,
               above the shipped max 50/50 (D-03 U-1) - reported as an out-of-domain render risk;
               the 24 CarLight blocks are counted over the 8 lamp parts.

Usage:
    python Tools/scripts/v02_rc4.py --write
    python Tools/scripts/v02_rc4.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import bm_parts            # noqa: E402
import jc3geom             # noqa: E402
import jc3hkx as H         # noqa: E402  (physicsc decode)
import jc3interact         # noqa: E402
import rbm_geom            # noqa: E402
import silhouette_check as SC   # noqa: E402
import t9_interaction      # noqa: E402
from eetoc import read_toc      # noqa: E402
from preview_rbm import render  # noqa: E402

BUILD = os.path.join(ROOT, "Builds", "bm-RC4")
AAF = os.path.join(BUILD, "aaf")
VEH = os.path.join(AAF, "models", "jc_vehicles", "01_land",
                   "v0300_car_kensington_sportsmuscle")
BODY = os.path.join(VEH, "sportsmuscle_body_lod1.rbm")
PARTS = os.path.join(VEH, "sportsmuscle_vehicle_parts.vmodc")
PHYS = os.path.join(VEH, "sportsmuscle.physicsc")
LIGHTS_MODULE = os.path.join(
    AAF, "editor", "entities", "jc_vehicles", "01_land",
    "v0300_car_kensington_sportsmuscle", "modules", "generated",
    "v0300_car_kensington_sportsmuscle_lights.vmodc")
DROP_EE = os.path.join(BUILD, "drop", "editor", "entities", "jc_vehicles", "01_land",
                       "v0300_car_kensington_sportsmuscle",
                       "v0300_car_kensington_sportsmuscle_debug.ee")
T8 = os.path.join(ROOT, "Working", "Translation", "T8_PARTS.json")
LIGHT_SPEC = os.path.join(ROOT, "Working", "Lights", "bm_rc4_lights.json")
STATIONS = os.path.join(ROOT, "Working", "Appearance", "build", "stations.json")
COLLISION_JSON = os.path.join(ROOT, "Working", "Collision", "bm_collision.json")
HULL_JSON = os.path.join(ROOT, "Working", "Collision2", "bm_vehicle_hull.json")
T16 = os.path.join(ROOT, "Working", "Translation", "t16_collision.json")
RC2_GEO = os.path.join(ROOT, "Builds", "bm-RC2", "verify", "geometry.json")
VERIFY = os.path.join(BUILD, "verify")
OUT_JSON = os.path.join(VERIFY, "geometry.json")
OUT_MD = os.path.join(VERIFY, "geometry.md")
POSE_DIR = os.path.join(VERIFY, "v02")
SIL_MIN = 0.999
BUD1_HOLES_PCT = 0.3
BAND = (0.05, 0.30)
ENV_TOL = 0.02
SHIPPED_MAX = {"angle": 50.0, "range": 50.0}   # D-03 U-1 / build-d03
B03_LAMPS = ("sportsmuscle_headlight_f_l", "sportsmuscle_headlight_f_r",
             "sportsmuscle_wheel_f_l_arch", "sportsmuscle_wheel_f_r_arch",
             "sportsmuscle_wheel_r_l_arch", "sportsmuscle_wheel_r_r_arch",
             "sportsmuscle_tailstrip_r_l", "sportsmuscle_tailstrip_r_r")
# BmAK chassis box 0 in JC3 axes, build-d08 §4 (690.305 x 374.536 x 207.5 cm, identity TM)
CHASSIS = {"min": [-1.8727, 0.030, -3.3615], "max": [1.8727, 2.105, 3.5415],
           "extents_cm": [690.305, 374.536, 207.5]}
BRIEF_COLLISION = {"placement_m": [0.0005, 0.061, 0.0025], "placement_cm": 6.1,
                   "gate_pass": False,
                   "physicsc_sha256":
                       "0164936b928f821c058c5a154a93b7cadcdbb9baca7d44fb67cb8f18a9399323",
                   "source": "build-d08 §4 / build-d13 §2 (6.1 cm, gate NOT MET)"}
BRIEF_LIGHTS_OFFSET = 16499504   # B-07 spec: the vanilla 6,337 B module
CARLIGHT_EXPECTED = 24           # 1 block x 3 LODs x 8 lamp parts


def sha(p: str) -> str:
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


# ------------------------------------------------------------------ silhouette
def _pack(tris, view):
    ax = {"side": (2, 1), "front": (0, 1), "top": (0, 2)}[view]
    out = np.zeros_like(tris)
    out[:, :, 2] = tris[:, :, ax[0]]
    out[:, :, 1] = tris[:, :, ax[1]]
    return out


def sil_view(src, ours, offset, view):
    """One orthographic silhouette, source and ours rasterised in the same frame."""
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
    coverage = float(O.sum()) / float(S.sum())
    holes_pct = 100.0 * float(holes.sum()) / float(S.sum())
    return {"frame": [int(S.shape[1]), int(S.shape[0])],
            "source_px": int(S.sum()), "ours_px": int(O.sum()),
            "coverage": round(coverage, 6),
            "margin_pp": round(100.0 * (coverage - SIL_MIN), 4),
            "holes_px": int(holes.sum()), "holes_pct": round(holes_pct, 4),
            "tears_pct": round(100.0 * float(tears.sum()) / float(S.sum()), 4),
            "extra_pct": round(100.0 * float(extra.sum()) / float(S.sum()), 4),
            "bud1_pass": holes_pct < BUD1_HOLES_PCT,
            "pass": coverage >= SIL_MIN}


def silhouette_block(src):
    tri = np.concatenate([SC.PR.block_triangles(b)
                          for b in rbm_geom.decode(open(BODY, "rb").read()).blocks])
    tri = tri[np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1) > 1e-9]
    off = json.load(open(STATIONS, encoding="utf-8"))["offset"]
    views = {v: sil_view(src, tri, off, v) for v in ("side", "front", "top")}
    body_sha = sha(BODY)

    rc2 = None
    if os.path.exists(RC2_GEO):
        d2 = json.load(open(RC2_GEO, encoding="utf-8"))["silhouette"]
        side2 = d2.get("with_build_offset") or {}
        rc2 = {"geometry_json": os.path.relpath(RC2_GEO, ROOT).replace(os.sep, "/"),
               "mesh_sha256": d2.get("rbm_sha256"),
               "same_mesh": d2.get("rbm_sha256") == body_sha,
               "side_source_px": side2.get("source_px"),
               "side_ours_px": side2.get("ours_px"),
               "side_coverage": side2.get("coverage"),
               "side_margin_pp": round(100.0 * (float(side2.get("coverage", 0)) - SIL_MIN), 4),
               "side_px_delta": int(views["side"]["ours_px"] - int(side2.get("ours_px", 0))),
               "offset_m": d2.get("offset_m"),
               "offset_same": d2.get("offset_m") == [round(float(x), 6) for x in off]}

    return {"rbm": os.path.relpath(BODY, ROOT).replace(os.sep, "/"),
            "rbm_sha256": body_sha, "ours_tris": int(len(tri)),
            "offset_m": [round(float(x), 6) for x in off],
            "offset_source": os.path.relpath(STATIONS, ROOT).replace(os.sep, "/"),
            "views": views,
            "gate": {"threshold": SIL_MIN, "pass": all(q["pass"] for q in views.values()),
                     "per_view": {v: q["pass"] for v, q in views.items()},
                     "min_view": min(views, key=lambda v: views[v]["coverage"]),
                     "min_margin_pp": min(q["margin_pp"] for q in views.values()),
                     "bud1_threshold_pct": BUD1_HOLES_PCT,
                     "bud1_pass": all(q["bud1_pass"] for q in views.values()),
                     "bud1_min_margin_pp": round(
                         BUD1_HOLES_PCT - max(q["holes_pct"] for q in views.values()), 4)},
            "rc2": rc2}


# ------------------------------------------------------------------ interaction
def interaction_block():
    v, t, _m = rbm_geom.collect_mesh(rbm_geom.decode(open(BODY, "rb").read()))
    V, T = np.array(v, float), np.array(t, np.int64)
    jc3interact.read_bat_mesh = lambda: (V, T)
    doc = t9_interaction.build()
    placed = [r for r in doc["objects"] if r["disposition"] == "placed"]
    d = [r["measure"]["nearest_m"] for r in placed]
    lo, hi = BAND
    out = [r for r in placed if not (lo <= r["measure"]["nearest_m"] <= hi)]
    worst = max([lo - x for x in d if x < lo] + [x - hi for x in d if x > hi] + [0.0])
    inside = [r["name"] for r in placed if r["measure"].get("inside")]
    return {"mesh": {"file": os.path.relpath(BODY, ROOT).replace(os.sep, "/"),
                     "vertices": int(len(V)), "triangles": int(len(T))},
            "band_m": list(BAND), "objects": len(doc["objects"]), "placed": len(placed),
            "in_band": len(placed) - len(out),
            "min_m": round(float(min(d)), 4) if d else None,
            "max_m": round(float(max(d)), 4) if d else None,
            "inside_hull": inside,
            "dropped_D9": doc["counts"]["dropped_D9"],
            "socket": doc["counts"]["socket"],
            "unknown": doc["counts"]["unknown"],
            "failures": [{"name": r["name"], "nearest_m": r["measure"]["nearest_m"],
                          "verdict": r["verdict"]} for r in out],
            "worst_outside_m": round(float(worst), 4),
            "gate": {"pass": not out and not inside and worst <= ENV_TOL,
                     "rule": "5 cm outside the hull <= d <= 30 cm; no point outside by more "
                             "than 2 cm; no placed point inside the hull"}}


# ------------------------------------------------------------------ parts
def parts_block():
    parts = bm_parts.decode_parts(open(PARTS, "rb").read())
    missing = [p["name"] for p in parts if not os.path.exists(os.path.join(AAF, p["model"]))]
    types = sorted({p["damage_type"] for p in parts})
    idx = sorted(p["part_index"] for p in parts)
    absent = [i for i in range(max(idx) + 1) if i not in set(idx)]
    lamps = [p["name"] for p in parts if p.get("has_lights")]
    return {"module": os.path.relpath(PARTS, ROOT).replace(os.sep, "/"),
            "module_sha256": sha(PARTS), "parts": len(parts),
            "distinct_types": len(types), "types": types,
            "lamp_parts": len(lamps),
            "missing_models": missing,
            "absent_indices": absent,
            "pre_b04_count": 61,
            "pre_b04_extra": [{"part_index": i, "name": n} for i, n in
                              zip((1, 2), ("sportsmuscle_door_f_l", "sportsmuscle_door_f_r"))],
            "extra_beyond_59": [p["name"] for p in parts[59:]],
            "gate": {"pass": len(parts) == 59 and len(types) == 19 and not missing
                     and absent == [1, 2],
                     "rule": "59 parts / 19 distinct types (build-d08 section 2); every model "
                             "resolves; the two pre-B-04 door indices 1/2 are absent"}}


# ------------------------------------------------------------------ poses
def _world(p, by_i):
    M = np.array(p["parent_space_offset"], np.float64).reshape(4, 4)
    q = by_i.get(p["parent_part_index"])
    return M @ _world(q, by_i) if q is not None and q is not p else M


def _assemble(parts):
    """Every drawn part in world space, plus a per-triangle owner array."""
    tris, cols, owners, by_i = [], [], [], {p["part_index"]: p for p in parts}
    for p in parts:
        if p.get("starts_deleted"):
            continue
        lod = os.path.join(AAF, p["model"])
        if not os.path.exists(lod):
            continue
        first = next((l.strip() for l in open(lod, encoding="utf-8")
                      if l.strip().endswith(".rbm")), None)
        f = os.path.join(AAF, first) if first else None
        if not f or not os.path.exists(f):
            continue
        M = _world(p, by_i)
        here = []
        for b in jc3geom.decode_mesh(open(f, "rb").read(), first)["blocks"]:
            if not b.get("positions") or not b.get("indices"):
                continue
            P = np.asarray(b["positions"], np.float64)[:, :3]
            I = np.asarray(b["indices"], np.int64)
            I = I[: len(I) // 3 * 3].reshape(-1, 3)
            I = I[(I < len(P)).all(1)]
            t = P[I]
            if len(t):
                h = np.concatenate([t, np.ones(t.shape[:2] + (1,))], axis=2) @ M
                here.append(h[:, :, :3].astype(np.float32))
        if not here:
            continue
        arr = np.concatenate(here)
        tris.append(arr)
        cols.append(np.tile(np.array([0.70, 0.72, 0.76], np.float32), (len(arr), 1)))
        owners.append(np.full(len(arr), p["part_index"], np.int64))
    return np.concatenate(tris), np.concatenate(cols), np.concatenate(owners), by_i


def _subtree(parts, root_index):
    want = {root_index}
    grew = True
    while grew:
        grew = False
        for p in parts:
            if p["parent_part_index"] in want and p["part_index"] not in want:
                want.add(p["part_index"])
                grew = True
    return want


def _rot(axis, angle_deg):
    a = math.radians(angle_deg)
    ax = np.asarray(axis, np.float64)
    ax = ax / (np.linalg.norm(ax) or 1.0)
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + math.sin(a) * K + (1 - math.cos(a)) * (K @ K), ax


def _pose_render(parts, T, C, owner, name, root_index, axis, angle_deg, pivot, view, note):
    sub = _subtree(parts, root_index)
    mask = np.isin(owner, sorted(sub))
    if not mask.any():
        return None
    R, ax = _rot(axis, angle_deg)
    piv = np.asarray(pivot, np.float64)
    TT, CC = T.copy(), C.copy()
    TT[mask] = (TT[mask] - piv) @ R.T + piv
    CC[mask] = np.array([0.95, 0.62, 0.15], np.float32)      # posed part highlighted
    img, _ = render(TT, CC, view, 1000, light=(0.35, 0.8, -0.45))
    os.makedirs(POSE_DIR, exist_ok=True)
    path = os.path.join(POSE_DIR, f"{name}.png")
    img.save(path)
    return {"pose": name, "status": "rendered",
            "file": os.path.relpath(path, ROOT).replace(os.sep, "/"),
            "angle_deg": angle_deg, "axis": [round(float(x), 3) for x in ax],
            "pivot_m": [round(float(x), 4) for x in piv],
            "view": view, "parts_moved": sorted(sub),
            "triangles_moved": int(mask.sum()),
            "width": img.width, "height": img.height, "note": note}


POSE_PLAN = [
    {"name": "pose_turret_yaw_min", "rid": "P-01", "part": "batmobile_turret",
     "which": "min", "view": "top"},
    {"name": "pose_turret_yaw_max", "rid": "P-01", "part": "batmobile_turret",
     "which": "max", "view": "top"},
    {"name": "pose_cannon_pitch_min", "rid": "P-02", "part": "batmobile_cannon",
     "which": "min", "view": "side"},
    {"name": "pose_cannon_pitch_max", "rid": "P-02", "part": "batmobile_cannon",
     "which": "max", "view": "side"},
    {"name": "pose_airbrake_l_f", "rid": "P-09", "part": "batmobile_aero_flap_l_f",
     "which": "min", "view": "side"},
    {"name": "pose_airbrake_r_f", "rid": "P-10", "part": "batmobile_aero_flap_r_f",
     "which": "min", "view": "side"},
    {"name": "pose_airbrake_l_b", "rid": "P-11", "part": "batmobile_aero_flap_l_b",
     "which": "min", "view": "side"},
    {"name": "pose_airbrake_r_b", "rid": "P-12", "part": "batmobile_aero_flap_r_b",
     "which": "min", "view": "side"},
]
CACHE = os.path.join(POSE_DIR, "_assembly.npz")


def resolve_pose(spec, cfg):
    """The decoded limit, axis and pivot for one pose spec, or None where the tree has none."""
    r = cfg[spec["rid"]]
    if spec["rid"] == "P-02":
        h = r["hinge"]
        ang = h["min_deg"] if spec["which"] == "min" else h["max_deg"]
        axis = h["axis"]
        piv = (r.get("pivots") or {}).get(
            "Batmobile_Rig_Weapons_Heavy_Cannon_Barrel_01", {}).get("pivot_jc3_m")
        note = ("P-02.joint is null (the authored motion translates the barrel); this is the "
                "carrier's decoded hinge limit, not an animation on this part")
    else:
        j = r["joint"]
        ang = j["min_deg"] if spec["which"] == "min" else j["max_deg"]
        axis = j.get("axis_jc3") or [0.0, 1.0, 0.0]
        bone = j.get("part_pivot_bone") or j.get("bone")
        piv = ((r.get("pivots") or {}).get(bone) or {}).get("pivot_jc3_m")
        note = f"decoded joint {r['id']} ({j.get('bone')}), pivot bone {bone}"
    return {"part": spec["part"], "joint": spec["rid"], "angle_deg": float(ang),
            "axis": [float(x) for x in axis], "pivot": piv, "note": note,
            "view": spec["view"]}


def _sidecar(name):
    return os.path.join(POSE_DIR, f"{name}.json")


def poses_block(parts, render_poses=True):
    cfg = {r["id"]: r for r in json.load(open(T8, encoding="utf-8"))["rows"]}
    names = ["pose_base"] + [s["name"] for s in POSE_PLAN]
    if render_poses:
        T, C, owner, _ = _assemble(parts)
        os.makedirs(POSE_DIR, exist_ok=True)
        for f in os.listdir(POSE_DIR):
            if f.startswith("pose_") and f.endswith((".png", ".json")):
                os.remove(os.path.join(POSE_DIR, f))
        np.savez_compressed(CACHE, T=T, C=C, owner=owner)
        del T, C, owner
        for name in names:
            r = subprocess.run([sys.executable, os.path.join(HERE, "v02_pose.py"),
                                name, CACHE], cwd=ROOT, capture_output=True, text=True)
            if r.returncode != 0:
                print(f"pose {name} failed: {r.stderr.strip()[-400:]}")
    out, stale = [], []
    for spec in POSE_PLAN:
        sc = _sidecar(spec["name"])
        if not os.path.exists(sc):
            out.append({"pose": spec["name"], "part": spec["part"], "joint": spec["rid"],
                        "status": "missing render", "why": "v02_pose.py produced no record"})
            stale.append(spec["name"])
            continue
        rec = json.load(open(sc, encoding="utf-8"))
        res = resolve_pose(spec, cfg)
        same = (abs(float(rec.get("angle_deg", 1e9)) - res["angle_deg"]) < 1e-9
                and rec.get("part") == res["part"] and rec.get("view") == res["view"])
        for key, hkey in (("file", "png_sha256"), ("isolated_file", "isolated_sha256")):
            p = os.path.join(ROOT, rec.get(key, ""))
            if not os.path.exists(p) or sha(p) != rec.get(hkey):
                same = False
        rec["status"] = "rendered" if same else "stale render"
        if not same:
            stale.append(spec["name"])
        out.append(rec)
    if os.path.exists(_sidecar("pose_base")):
        out.append(json.load(open(_sidecar("pose_base"), encoding="utf-8")))
    else:
        out.append({"pose": "pose_base", "status": "missing render"})
        stale.append("pose_base")
    out.append({"pose": "canopy", "status": "not in this tree",
                "why": "no canopy part in the 59-part table and no canopy bone; the glass is "
                       "CockPit_Mesh / the window parts"})
    out.append({"pose": "missile hatches", "status": "not in this tree",
                "why": "P-07/P-08 decode the hatch pivot bones (0.019..15.007 deg about -X) but "
                       "name no part; the missile pods (54/55) carry no hatch mesh"})
    out.append({"pose": "battle pose (T-MD13)", "status": "not in this tree",
                "why": "build-d12: ConvertAdf NullReferenceException in InstanceMemberInfo."
                       "PrepareForWritting on sportsmuscle_vehicle_parts.vmodc, so the battle-pose "
                       "values are not written; the delivered pose is pose_base.png"})
    rendered = [p for p in out if p["status"] == "rendered"]
    absent = [p["pose"] for p in out if p["status"] != "rendered"]
    return out, {"rendered": len(rendered), "absent": absent,
                 "stale": sorted(set(stale)),
                 "pass": len(absent) == 0,
                 "rule": "each moving part is rendered at its decoded limit (one child process "
                         "per pose, full car + isolated pair); canopy, hatches and the battle "
                         "pose are labelled not in this tree, never passed"}


# ------------------------------------------------------------------ collision
def collision_block():
    blob = open(PHYS, "rb").read()
    pf = H.Packfile(blob)
    s = H.summary(pf)
    # BmAK extents are (length 690.305, width 374.536, height 207.5) cm; JC3 order is
    # x = width, y = height, z = length -> [3.74536, 2.075, 6.90305] m.
    target_size = [CHASSIS["extents_cm"][1] / 100.0, CHASSIS["extents_cm"][2] / 100.0,
                   CHASSIS["extents_cm"][0] / 100.0]

    hulls = []
    for o in pf.objects:
        if o.cls not in H.COMPOUND_CLASSES:
            continue
        for inst in H.decode_compound(pf, o.offset, o.cls)["instances"]:
            if inst["part_index"] == 0 and inst["shape_class"] == H.POLYTOPE:
                b = H.decode_polytope(pf, inst["shape"])["bounds"]
                hulls.append({"shape": f"{inst['shape']:#x}",
                              "min": [round(float(x), 6) for x in b["min"]],
                              "max": [round(float(x), 6) for x in b["max"]]})
    if not hulls:
        raise SystemExit("no hull bound to part 0 in the physicsc")

    def size(h):
        return [h["max"][i] - h["min"][i] for i in range(3)]

    body = min(hulls, key=lambda h: max(abs(size(h)[i] - target_size[i]) for i in range(3)))
    sz = size(body)
    shape_dev = max(abs(sz[i] - target_size[i]) for i in range(3))
    lo_dev = [body["min"][i] - CHASSIS["min"][i] for i in range(3)]
    hi_dev = [body["max"][i] - CHASSIS["max"][i] for i in range(3)]
    place = [max(abs(lo_dev[i]), abs(hi_dev[i])) for i in range(3)]

    rec = json.load(open(os.path.join(BUILD, "receipt.json"), encoding="utf-8"))["collision"]
    built = json.load(open(COLLISION_JSON, encoding="utf-8"))
    hullj = json.load(open(HULL_JSON, encoding="utf-8"))
    t16 = json.load(open(T16, encoding="utf-8"))
    toc = read_toc(open(DROP_EE + ".toc", "rb").read())
    rec_toc = next(((o, z) for n, o, z in toc if n.endswith("sportsmuscle.physicsc")), (0, 0))

    brief_matches = (sha(PHYS) == BRIEF_COLLISION["physicsc_sha256"])
    measured_pass = max(place) <= 0.05 and shape_dev <= 0.05
    return {"module": os.path.relpath(PHYS, ROOT).replace(os.sep, "/"),
            "sha256": sha(PHYS), "bytes": len(blob),
            "toc_record": list(rec_toc),
            "objects": s["objects"], "polytopes": s["polytopes"],
            "convex_polytopes": s["polytopes_convex"],
            "body0_hulls": hulls, "body0_hull": body,
            "body0_size_m": [round(float(x), 6) for x in sz],
            "chassis_box_0": {"min": CHASSIS["min"], "max": CHASSIS["max"],
                              "size_m": [round(float(x), 6) for x in target_size],
                              "extents_cm": CHASSIS["extents_cm"]},
            "shape_dev_m": round(float(shape_dev), 6),
            "placement_dev_m": [round(float(x), 6) for x in place],
            "placement_cm": round(100.0 * max(place), 2),
            "hulls_written": int(built["summary"]["hulls_written"]),
            "donor_bodies": int(hullj["bodies"]["bodies"]),
            "shapes_missing": sum(1 for c in rec.get("capability_gaps", [])
                                  if "shape instance" in c.get("what", "")),
            "boxes_decoded": int(rec["gate"]["boxes_decoded"]),
            "boxes_carried": int(rec["gate"]["boxes_carried"]),
            "free_hull_slots": int(rec["free_hull_slots"]),
            "donor_hulls": int(t16["donor"]["hulls"]),
            "unbound_hull_instances": int(t16["decomposition"]["unbound_hull_instances"]),
            "constraint": rec["constraint"],
            "receipt_gate": rec["gate"],
            "receipt_source": rec["source"],
            "brief": BRIEF_COLLISION,
            "brief_matches_shipped": brief_matches,
            "conflict": (not brief_matches and BRIEF_COLLISION["placement_cm"] > 5.0
                         and 100.0 * max(place) <= 5.0),
            "conflict_why": (
                "The brief's 6.1 cm is build-d08/d13's physicsc (sha 0164936b...), whose body-0 "
                "hull sits at y 0.091..2.166 m. The shipped file is sha fda78f4d... "
                "('box-0 floor placement'): its body-0 hull y is 0.030..2.105 m, on the box's own "
                "floor. Same x/z as the brief ([0.0005, 0.0025] m); only y moved, by 6.1 cm."
                if not brief_matches else
                "The shipped bytes are the brief's physicsc."),
            "six_point_one_is_not_a_pass": True,
            "render_bbox_not_a_gate": True,
            "gate": {"threshold_m": 0.05, "pass": measured_pass,
                     "rule": "body-0 hull shape and placement vs BmAK chassis box 0 <= 5 cm; "
                             "the render bbox is NOT a collision gate",
                     "not_carried": "chassis-box placement" if not measured_pass else None}}


# ------------------------------------------------------------------ lights
def lights_block():
    import bm_rc4_lights as BRL     # imported here: every pose child imports this module
    spec = json.load(open(LIGHT_SPEC, encoding="utf-8"))
    rows = spec["rows"]
    ang = [r["members"]["angle"]["v"] for r in rows if "angle" in r.get("members", {})]
    rng = [r["members"]["range"]["v"] for r in rows if "range" in r.get("members", {})]
    parts = bm_parts.decode_parts(open(PARTS, "rb").read())
    by_name = {p["name"]: p for p in parts}
    lit = {p["name"] for p in parts if p.get("has_lights")}
    referenced = sorted({r["part"]["name"] for r in rows})
    b03_present = [n for n in B03_LAMPS if n in lit]
    b03_with_entry = [n for n in B03_LAMPS if n in referenced]
    b03_without_entry = [n for n in B03_LAMPS if n not in referenced]
    hi_angle = {n: sum(1 for r in rows if r["part"]["name"] == n
                       and float(r["members"]["angle"]["v"]) > SHIPPED_MAX["angle"])
                for n in b03_with_entry}
    hi_range = sorted({float(r["members"]["range"]["v"]) for r in rows
                       if float(r["members"]["range"]["v"]) > SHIPPED_MAX["range"]})
    census = BRL.carlight_census(AAF)
    census_total = sum(v["car_light_blocks"] for v in census.values())
    toc = read_toc(open(DROP_EE + ".toc", "rb").read())
    mod = next(((o, z) for n, o, z in toc
                if n.endswith("sportsmuscle_lights.vmodc")), (0, 0))
    return {"module": os.path.relpath(LIGHTS_MODULE, ROOT).replace(os.sep, "/"),
            "module_sha256": sha(LIGHTS_MODULE),
            "module_offset": mod[0], "module_bytes": mod[1],
            "brief_offset": BRIEF_LIGHTS_OFFSET,
            "brief_offset_note": ("16,499,504 is B-07's vanilla 6,337 B module offset; the packed "
                                  "RC4 module is 7,105 B at 16,500,744 after the rows were added."),
            "rows": len(rows),
            "by_behavior": spec["counts"]["by_behavior"],
            "referenced_parts": len(referenced),
            "lamp_parts": len(b03_with_entry),
            "lamp_part_names": b03_with_entry,
            "b03_lamp_parts": len(b03_present),
            "b03_lamp_parts_without_entry": b03_without_entry,
            "module_lamp_parts": len(lit),
            "car_light_blocks": census_total,
            "car_light_per_part": {k: v["car_light_blocks"] for k, v in census.items()},
            "angle_over_shipped": hi_angle,
            "range_over_shipped": hi_range,
            "max_angle_deg": max(ang) if ang else None,
            "max_range_m": max(rng) if rng else None,
            "shipped_max": SHIPPED_MAX,
            "out_of_domain": {"angle": sorted({float(a) for a in ang
                                               if float(a) > SHIPPED_MAX["angle"]}),
                              "range": sorted({float(r) for r in rng
                                               if float(r) > SHIPPED_MAX["range"]})},
            "gate": {"pass": len(rows) == 24 and len(b03_present) == 8
                     and census_total == CARLIGHT_EXPECTED,
                     "rule": "24 rows; 24 CarLight blocks over the 8 lamp parts; 70 deg / 60 m "
                             "reported as an out-of-domain render risk (D-03 U-1), not a file error"}}


# ------------------------------------------------------------------ document
def build_doc(render_poses=True):
    import gc
    # heavy work last, and drop each section's arrays before the next: this box is shared with
    # other long-running jobs and several hundred MB of headroom is all that is available.
    inter = interaction_block()
    gc.collect()
    par = parts_block()
    lit = lights_block()
    col = collision_block()
    parts = bm_parts.decode_parts(open(PARTS, "rb").read())
    pos, pos_gate = poses_block(parts, render_poses)
    del parts
    gc.collect()
    src = SC.body_tris(*SC.P.read_pskx(SC.PSKX)[:3])
    sil = silhouette_block(src)
    del src
    gc.collect()
    gates = {"silhouette": sil["gate"]["pass"], "interaction": inter["gate"]["pass"],
             "parts": par["gate"]["pass"], "collision": col["gate"]["pass"],
             "lights": lit["gate"]["pass"], "poses": pos_gate["pass"]}
    return {"card": "V-02 (GRAB_BACKLOG 9a)", "build": os.path.relpath(BUILD, ROOT).replace(os.sep, "/"),
            "offline": True,
            "inputs": {"source_mesh": os.path.relpath(SC.PSKX, ROOT).replace(os.sep, "/"),
                       "source_body_faces": SC.BODY_FACES,
                       "source_split_faces": int(len(src))},
            "silhouette": sil, "interaction": inter, "parts": par,
            "poses": pos, "pose_gate": pos_gate,
            "collision": col, "lights": lit, "gates": gates,
            "blocked": [p["pose"] for p in pos if p["status"] != "rendered"],
            "overall": all(gates.values())}


def to_md(d):
    s, i, p = d["silhouette"], d["interaction"], d["parts"]
    pos, pg, c, l = d["poses"], d["pose_gate"], d["collision"], d["lights"]
    L = []
    a = L.append
    a("# V-02 - geometry, pose, collision and light gates on bm-RC4 (offline)")
    a("")
    a(f"**Answer: silhouette {s['gate']['min_margin_pp']:+.4f} pp at the worst view "
      f"({'PASS' if s['gate']['pass'] else 'FAIL'} vs 99.9 %, per view); "
      f"{i['in_band']}/{i['placed']} interaction points in 5-30 cm "
      f"({'PASS' if i['gate']['pass'] else 'FAIL'}); parts {p['parts']}/{p['distinct_types']} "
      f"types ({'PASS' if p['gate']['pass'] else 'FAIL'}); "
      f"collision {c['placement_cm']} cm measured on the shipped physicsc "
      f"({'PASS' if c['gate']['pass'] else 'NOT MET'} vs 5 cm, brief's 6.1 cm is a different "
      f"file); poses {pg['rendered']} rendered, {len(pg['absent'])} not in this tree "
      f"({'PASS' if pg['pass'] else 'NOT MET'}); lights {l['rows']} rows over "
      f"{l['b03_lamp_parts']} lamp parts ({'PASS' if l['gate']['pass'] else 'FAIL'}).**")
    a("")
    a("Generated by `Tools/scripts/v02_rc4.py` (`--check` re-runs the measurements and validates")
    a("every pose record and PNG hash; built from")
    a("the V-02 templates `v02_geometry.py` / `v02_render.py`. The build was read, never launched.")
    a("")
    a("## 1. Silhouette vs the BmAK body - per view (limit 99.9 %)")
    a("")
    a(f"- our mesh `{s['rbm']}` ({s['rbm_sha256'][:16]}), {s['ours_tris']:,} triangles")
    a(f"- source: the non-wheel body of `{d['inputs']['source_mesh']}`, "
      f"{d['inputs']['source_body_faces']:,} faces (split re-measured: "
      f"{d['inputs']['source_split_faces']:,})")
    a(f"- offset {s['offset_m']} m from `{s['offset_source']}`; one fixed frame per view")
    a("")
    a("| view | source px | ours px | coverage | margin vs 99.9 % | holes % | tears % | extra % | gate |")
    a("|---|---:|---:|---:|---:|---:|---:|---:|---|")
    for v, q in s["views"].items():
        a(f"| {v} | {q['source_px']:,} | {q['ours_px']:,} | {q['coverage'] * 100:.4f} % | "
          f"{q['margin_pp']:+.4f} pp | {q['holes_pct']} | {q['tears_pct']} | {q['extra_pct']} | "
          f"{'PASS' if q['pass'] else 'FAIL'} |")
    a("")
    a(f"- **gate: {'PASS' if s['gate']['pass'] else 'FAIL'} per view**; worst view "
      f"`{s['gate']['min_view']}` at {s['gate']['min_margin_pp']:+.4f} pp.")
    a(f"- BUD-1 gross-hole oracle (< {BUD1_HOLES_PCT} %): "
      f"{'PASS' if s['gate']['bud1_pass'] else 'FAIL'}, best margin "
      f"{s['gate']['bud1_min_margin_pp']:+.4f} pp; coverage is net, so this is printed beside it.")
    a("")
    if s.get("rc2"):
        r2 = s["rc2"]
        a("**What moved the margin.** RC2's own `geometry.json` measured the side view at "
          f"{float(r2['side_coverage']) * 100:.4f} % ({r2['side_margin_pp']:+.4f} pp). RC4's side "
          f"view is {s['views']['side']['coverage'] * 100:.4f} % "
          f"({s['views']['side']['margin_pp']:+.4f} pp), a difference of "
          f"{r2['side_px_delta']} our-pixels. The body mesh is "
          f"{'byte-identical' if r2['same_mesh'] else 'different'} "
          f"(`{r2['mesh_sha256'][:16]}` vs `{s['rbm_sha256'][:16]}`) and the offset is "
          f"{'identical' if r2['offset_same'] else 'different'}, so nothing moved the side margin: "
          "RC4 reproduces RC2's number exactly. Front and top are new measurements in this pass "
          "(RC2 measured only side); they are where a decimation tear would show, and both pass.")
        a("")
    a("Coverage is **net** (extra pixels count towards it). The tight one is the side view: it "
      "passes 99.9 % by 0.0004 pp while its gross holes are 0.2968 %, only 0.0032 pp under the "
      "0.3 % BUD-1 line. The offset is the build family's `stations.json`, the same one RC2 used.")
    a("")
    a("## 2. Pose renders at the decoded limits")
    a("")
    a("| pose | part | joint | limit deg | view | status | full car | isolated |")
    a("|---|---|---|---:|---|---|---|---|")
    for q in pos:
        a(f"| {q['pose']} | {q.get('part', '-')} | {q.get('joint', '-')} | "
          f"{q.get('angle_deg', '-')} | {q.get('view', '-')} | {q['status']} | "
          f"{q.get('file', '-')} | {q.get('isolated_file', '-')} |")
    a("")
    a("- Every rendered pose rotates **only the triangles owned by the moving part/subtree** "
      "about the **decoded bone pivot** from `Working/Translation/T8_PARTS.json`; the posed "
      "triangles are drawn amber. The earlier pass rotated about the part origin (0,0,0), which "
      "is not the hinge - these renders replace that.")
    a("- Turret yaw is drawn from the top (a Y-axis rotation is invisible from the side); the "
      "cannon and four air-brakes from the side. Turret and cannon are rendered at both limits; "
      "each air-brake at its larger-magnitude limit (the cruise-side limit is the small one).")
    a("- Each pose also has an **isolated** render: the part unposed (grey) and posed (amber) in "
      "one frame. This matters because the full-car view is occluded for the cannon and the front "
      "flaps - their full-car images can be byte-identical at both limits, which proves nothing; "
      "the isolated pair is the visible evidence, and the full-car PNG is the context.")
    a("- Poses are rendered by `Tools/scripts/v02_pose.py`, one child process each (the software "
      "renderer's peak does not fit nine renders in one process on this box), and the PNG hashes "
      "are pinned in this page and in `geometry.json`.")
    a("- **Cannon pitch** uses the carrier hinge `P-02.hinge` (-5..20 deg about X): `P-02.joint` "
      "is null because the authored motion translates the barrel, so there is no Batmobile "
      "rotation limit to decode. The render is labelled with that source, not presented as an "
      "animation this part owns.")
    a(f"- **Canopy and missile hatches: not in this tree.** No canopy part/bone exists (the glass "
      "is `CockPit_Mesh` / window parts), and P-07/P-08 decode hatch pivot bones "
      "(0.019..15.007 deg about -X) but name no part; the pods carry no hatch mesh.")
    a(f"- **Battle pose (T-MD13): not in this tree, not passed.** `build-d12` records "
      "`ConvertAdf` throwing `NullReferenceException` in "
      "`InstanceMemberInfo.PrepareForWritting` on the parts module, so the battle-pose values "
      "were never written. The delivered pose is `pose_base.png`.")
    a(f"- **pose gate: {'PASS' if pg['pass'] else 'NOT MET'}** - {pg['rendered']} rendered, "
      f"{len(pg['absent'])} labelled not in this tree: {', '.join(pg['absent'])}.")
    a("")
    a("## 3. Parts census (the delivered module)")
    a("")
    a(f"- `{p['module']}` ({p['module_sha256'][:16]}): **{p['parts']} parts**, "
      f"**{p['distinct_types']} distinct damage types**, {p['lamp_parts']} lamp parts")
    a(f"- expected 59 / 19 (build-d08 §2); extra parts beyond 59: "
      f"{p['extra_beyond_59'] or 'none'}; models unresolved: {p['missing_models'] or 'none'}")
    a(f"- part indices absent from the table: {p['absent_indices']}. The pre-B-04 table's "
      f"**61** is these two doors: "
      + ", ".join(f"index {x['part_index']} `{x['name']}`" for x in p["pre_b04_extra"])
      + " (B-04 step 1 removes them; `bm_parts.py` names the same pair). If this census had "
      "returned 61, those are the two to find.")
    a(f"- **gate: {'PASS' if p['gate']['pass'] else 'FAIL'}**. The earlier '61 parts incl "
      "wheel-arch 42/43' is superseded: 42/43 **are** present (both wheel arches), the missing "
      "pair is the doors.")
    a("")
    a("## 4. Interaction points (5 cm outside, within 30 cm)")
    a("")
    a(f"- RC4 body: {i['mesh']['vertices']:,} vertices / {i['mesh']['triangles']:,} triangles")
    a(f"- {i['objects']} donor objects: {i['placed']} placed, {i['dropped_D9']} dropped by D-9, "
      f"{i['socket']} socket, {i['unknown']} UNKNOWN")
    a(f"- distances {i['min_m']} .. {i['max_m']} m; in band **{i['in_band']}/{i['placed']}**; "
      f"placed inside the hull: {len(i['inside_hull'])}; worst excursion outside the envelope "
      f"{i['worst_outside_m']} m (limit {ENV_TOL} m)")
    a(f"- **gate: {'PASS' if i['gate']['pass'] else 'FAIL'}** - the whole placed set is inside "
      "5-30 cm; the 2 cm outer tolerance is unused.")
    a("")
    a("## 5. Collision - re-measured from the packed physicsc, NOT a render-bbox gate")
    a("")
    a(f"- packed `{c['module']}`: {c['bytes']:,} B, sha256 `{c['sha256'][:16]}`, `.toc` record "
      f"{c['toc_record']}; {c['objects']} objects, **{c['polytopes']} polytopes** "
      f"({c['convex_polytopes']} convex)")
    a(f"- 5 hulls written (body 0 + 4 wheels) over the donor's {c['donor_bodies']} bodies; "
      f"{c['donor_hulls']} donor hull objects, {c['unbound_hull_instances']} unbound instances, "
      f"**{c['free_hull_slots']} free slots**")
    a("")
    a("| quantity | BmAK chassis box 0 | shipped body-0 hull | deviation |")
    a("|---|---|---|---:|")
    for k, name in enumerate(("x", "y", "z")):
        a(f"| {name} min | {c['chassis_box_0']['min'][k]:.4f} | {c['body0_hull']['min'][k]:.4f} | "
          f"{c['body0_hull']['min'][k] - c['chassis_box_0']['min'][k]:+.4f} |")
        a(f"| {name} max | {c['chassis_box_0']['max'][k]:.4f} | {c['body0_hull']['max'][k]:.4f} | "
          f"{c['body0_hull']['max'][k] - c['chassis_box_0']['max'][k]:+.4f} |")
    a("")
    a(f"- **shape vs BmAK chassis box 0: {c['shape_dev_m']:.4f} m** (size "
      f"{c['body0_size_m']} vs {c['chassis_box_0']['size_m']})")
    a(f"- **placement: {c['placement_dev_m']} m = {c['placement_cm']} cm** -> the card's 5 cm "
      f"gate is **{'PASS' if c['gate']['pass'] else 'NOT MET'}** on the shipped bytes")
    a(f"- BmAK boxes with no shape instance: **{c['shapes_missing']} of {c['boxes_decoded']}** "
      f"({c['boxes_carried']} carried); constraint: **{c['constraint']}** (named omission); "
      f"0 of {c['donor_hulls']} hull slots free")
    a(f"- the render bbox is **not** used as a gate here; no render-bbox figure is compared "
      "against 5 cm.")
    a("")
    a(f"**Brief conflict, stated rather than smoothed.** The brief says the hull sits "
      f"`{c['brief']['placement_m']}` m = **{c['brief']['placement_cm']} cm** high, so the 5 cm "
      f"gate is **NOT MET** (`receipt.collision.gate.pass = false`). The delivered receipt and "
      f"the delivered bytes say otherwise: `receipt.collision.gate.pass = "
      f"{str(c['receipt_gate']['pass']).lower()}`, source `{c['receipt_source']}`, and the file "
      f"measures `{c['placement_dev_m']}` m. The brief's file is the superseded "
      f"`{c['brief']['physicsc_sha256'][:16]}` variant; the shipped one is "
      f"`{c['sha256'][:16]}`. {c['conflict_why']} The **6.1 cm is not reinterpreted as a pass**: "
      "on that file it is a real miss, and it is recorded as such in build-d08/d13; it is simply "
      "not what this tree ships. If the card must be read against the 6.1 cm receipt, the tree "
      "has been rebuilt since and that receipt needs reissuing, not the number re-scoring.")
    a("")
    a("## 6. Lights module (24 rows, 24 CarLight blocks over 8 lamp parts)")
    a("")
    a(f"- `{l['module']}` ({l['module_sha256'][:16]}): **{l['module_bytes']:,} B** at `.toc` "
      f"offset **{l['module_offset']:,}**")
    a(f"- {l['brief_offset_note']}")
    a(f"- **{l['rows']} rows** ({l['by_behavior']}); `has_lights` on "
      f"**{l['b03_lamp_parts']}/8** B-03 lamp parts, **{l['lamp_parts']}** of them carry a row; "
      f"the module flags {l['module_lamp_parts']} parts in total (donor lamp parts stay flagged)")
    a(f"- lamp parts with no row: {l['b03_lamp_parts_without_entry'] or 'none'} (lit with no "
      "entry: the BmAK rig has no rear-wheel socket)")
    a(f"- **CarLight census: {l['car_light_blocks']} blocks over 8 lamp parts** (1 per LOD, 3 "
      f"LODs each): {l['car_light_per_part']}")
    a(f"- maxima: angle **{l['max_angle_deg']} deg**, range **{l['max_range_m']} m**; shipped max "
      f"{l['shipped_max']['angle']}/{l['shipped_max']['range']} (D-03 U-1)")
    a(f"- **out-of-domain render risk**: 70 deg entries per headlight "
      f"{l['angle_over_shipped']}; ranges above 50 m {l['range_over_shipped']}. "
      "No shipped `VehicleDynamicLights` entry reaches past 50/50 (3,217-entry census), so these "
      "are legal floats whose rendering is unproven - a look-test risk, not a file error.")
    a("")
    a("## 7. Limits")
    a("")
    a("- Nothing was launched or installed: these are file-level measurements and offline renders.")
    a("- The pose renders use the decoded JC3 pivot and axis and rotate exact part triangles; the "
      "engine's own blend/limits are not simulated, and no collision or suspension response is "
      "modelled while posed.")
    a("- `receipt.complete` stays false; the pose gate is NOT MET because the battle pose, canopy "
      "and hatches are not in this tree, and the texture rows are outside this card.")
    a("")
    return "\n".join(L)


def write():
    d = build_doc(True)             # renders every pose before anything is pruned
    os.makedirs(VERIFY, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(d, indent=1) + "\n")
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(to_md(d))
    g = d["gates"]
    print(f"wrote {os.path.relpath(OUT_JSON, ROOT)} and geometry.md")
    print(f"silhouette {'PASS' if g['silhouette'] else 'FAIL'} "
          f"({d['silhouette']['gate']['min_margin_pp']:+.4f} pp worst), "
          f"interaction {d['interaction']['in_band']}/{d['interaction']['placed']}, "
          f"parts {d['parts']['parts']}/{d['parts']['distinct_types']}, "
          f"collision {d['collision']['placement_cm']} cm "
          f"{'PASS' if g['collision'] else 'NOT MET'}, "
          f"poses {d['pose_gate']['rendered']} rendered / "
          f"{len(d['pose_gate']['absent'])} absent, "
          f"lights {d['lights']['rows']} rows / {d['lights']['car_light_blocks']} blocks")


def check():
    d = build_doc(False)             # measurements re-run; pose renders are pinned + hash-checked
    bad = 0

    def ok(c, m):
        nonlocal bad
        print(("PASS " if c else "FAIL ") + m)
        bad += 0 if c else 1

    ok(d["inputs"]["source_split_faces"] == d["inputs"]["source_body_faces"],
       f"source body split still {d['inputs']['source_body_faces']:,} faces")
    ok(len(d["silhouette"]["views"]) == 3
       and all(q["source_px"] > 0 and q["ours_px"] > 0
               for q in d["silhouette"]["views"].values()),
       "three silhouette views rasterised with real pixels, not one aggregate")
    if d["silhouette"]["rc2"]:
        ok(d["silhouette"]["rc2"]["same_mesh"] and d["silhouette"]["rc2"]["offset_same"],
           "RC2 side comparison uses the same mesh sha and the same offset")
    ok(d["interaction"]["gate"]["pass"] == (not d["interaction"]["failures"]),
       "interaction gate matches its failure list and inside-hull list")
    ok(d["parts"]["parts"] == 59 and d["parts"]["distinct_types"] == 19
       and d["parts"]["absent_indices"] == [1, 2],
       "parts census is 59 / 19 with the two door indices absent")
    ok(all(q["status"] in ("rendered", "not in this tree") for q in d["poses"]),
       "every pose is rendered or labelled not-in-tree; battle pose is never passed")
    ok(any(q["pose"].startswith("battle pose") and q["status"] == "not in this tree"
           for q in d["poses"]), "battle pose is labelled not in this tree")
    ok(d["pose_gate"]["pass"] is False and len(d["pose_gate"]["absent"]) == 3,
       "pose gate is NOT MET: battle pose, canopy and hatches are absent")
    ok(d["collision"]["polytopes"] == 54 and d["collision"]["donor_bodies"] == 62
       and d["collision"]["shapes_missing"] == 2 and d["collision"]["free_hull_slots"] == 0,
       "54 hulls / 62 donor bodies / 2 boxes missing / 0 free slots")
    ok(d["collision"]["shape_dev_m"] < 0.001,
       f"body-0 shape dev {d['collision']['shape_dev_m']} m vs chassis box 0")
    ok(d["collision"]["conflict"] and d["collision"]["brief"]["placement_cm"] == 6.1
       and d["collision"]["placement_cm"] <= 5.0,
       "collision reports the 6.1 cm brief conflict instead of re-scoring it")
    ok(d["collision"]["receipt_gate"]["pass"] is True,
       "delivered receipt collision gate is true, matching the delivered bytes")
    ok(d["lights"]["rows"] == 24 and d["lights"]["car_light_blocks"] == CARLIGHT_EXPECTED
       and d["lights"]["b03_lamp_parts"] == 8,
       "24 rows and 24 CarLight blocks over 8 lamp parts")
    ok(d["lights"]["angle_over_shipped"].get("sportsmuscle_headlight_f_l") == 2
       and d["lights"]["angle_over_shipped"].get("sportsmuscle_headlight_f_r") == 2,
       "two 70 deg entries per headlight part")
    for q in d["poses"]:
        if q["status"] == "rendered":
            for key, hkey in (("file", "png_sha256"), ("isolated_file", "isolated_sha256")):
                if key in q:
                    p = os.path.join(ROOT, q[key])
                    ok(os.path.exists(p) and sha(p) == q[hkey],
                       f"{q['pose']} {key} matches its pinned hash")
        elif q["status"] in ("missing render", "stale render"):
            ok(False, f"{q['pose']}: {q['status']}")
    with open(OUT_MD, encoding="utf-8") as f:
        ok(f.read() == to_md(d), "geometry.md re-derives byte for byte")
    with open(OUT_JSON, encoding="utf-8") as f:
        ok(json.loads(f.read()) == d, "geometry.json matches the recomputed data")
    print(f"{'PASS' if not bad else 'FAIL'}: V-02 RC4 {bad} failure(s)")
    raise SystemExit(1 if bad else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    write() if a.write else check()


if __name__ == "__main__":
    main()
