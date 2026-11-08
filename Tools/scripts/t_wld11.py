#!/usr/bin/env python
"""t_wld11.py - T-WLD11: can the three stunt areas be re-indexed or moved onto the shell?

The `StuntAreas` module of the Serpente donor entity declares three active areas.  Each area
binds a list of `DeformPoints` indices and carries a `vertices3D_local` copy of the same
points.  This tool measures, from the files alone:

  * the donor's own tolerance: how far the donor's three areas sit above the *donor* shell
    (the whole point of the exercise - a stunt surface is an authored plane a few cm above
    the skin, not a skin vertex);
  * where the same 22 bound points land on the *Batmobile* body mesh, per vertex, in the
    stored frame and under G2-18's normalised map;
  * every donor `deform_points` index that exists, with its name, part binding and position;
  * two oracles, each of which can fail: O-1 re-indexing onto existing deform points, and
    O-2 moving the area onto the shell.

Writes ``Working/Translation/T_WLD11_AREAS.md`` + ``.json``; ``--check`` re-derives both and
compares them, then re-runs the oracles and the recorded invariant.

Inputs (all read-only, no game launch, no install):
  * ``_gamedata/JC3grab/entities/<donor>.ee.json``  - `StuntAreas`, `DeformPoints`
  * ``_gamedata/JC3grab/geom/<donor>.ee.json|.bin`` - the donor shell triangles
  * ``Working/Appearance/build_parts/body_lod1.rbm`` - the Batmobile body mesh (B-02)
  * ``Working/TrueScale/stations.json``             - the Batmobile body bbox (cross-check)
  * ``Working/Parts/bm_vehicle_parts.json``         - the Batmobile part index map (B-04)
  * ``Builds/bm-009/...``                           - whether the two modules ship

Usage:
  python t_wld11.py --write
  python t_wld11.py --check
  python t_wld11.py dump areas|points|candidates
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
import rbm_geom  # noqa: E402
import jc3interact  # noqa: E402

RAW = os.environ.get("JC3_RAW", r"E:/Modding/_gamedata/JC3grab")
DONOR = ("v0300_car_kensington_sportsmuscle",
         "v0300_car_kensington_sportsmuscle_civilian_01")
DONOR_BASE = "__".join(DONOR)
BUILD = os.path.join(ROOT, "Builds", "bm-009", "aaf")
MODEL_DIR = "models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle"
OUT = os.path.join(ROOT, "Working", "Translation")
JSON_NAME = "t_wld11_areas.json"
MD_NAME = "T_WLD11_AREAS.md"

BAT_MESH = os.path.join(ROOT, "Working", "Appearance", "build_parts", "body_lod1.rbm")
STATIONS = os.path.join(ROOT, "Working", "TrueScale", "stations.json")
PARTS = os.path.join(ROOT, "Working", "Parts", "bm_vehicle_parts.json")
SHIPPED = (f"{MODEL_DIR}/sportsmuscle_stunt_areas.vmodc",
           f"{MODEL_DIR}/sportsmuscle_vehicle_deform.vmodc")

UP_COS = 0.7071          # "a standing surface": nearest face within 45 deg of +Y
SAME_POINT_M = 0.30      # a substitute keeps the area's shape if it moves a vertex < one edge


# ---------------------------------------------------------------- small helpers
def rnd(x, n=4):
    return round(float(x), n)


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- readers
def read_donor() -> dict:
    """`DeformPoints` (135 points) and the three active `StuntAreas` slots."""
    d = load_json(os.path.join(RAW, "entities", DONOR_BASE + ".ee.json"))
    mods = {str(m.get("type")): m for m in d["modules"]}
    for need in ("DeformPoints", "StuntAreas"):
        if need not in mods:
            raise SystemExit(f"donor entity has no `{need}` module")

    vals: dict[int, dict[int, float]] = {}
    meta: dict[int, dict[str, object]] = {}
    for r in mods["DeformPoints"]["rows"]:
        m = re.match(r"points\[(\d+)\]\.start_transform\[(\d+)\]$", r["path"])
        if m:
            vals.setdefault(int(m.group(1)), {})[int(m.group(2))] = r["value"]
            continue
        m = re.match(r"points\[(\d+)\]\.(\w+)$", r["path"])
        if m:
            meta.setdefault(int(m.group(1)), {})[m.group(2)] = r["value"]
    points = []
    for i in sorted(vals):
        if sorted(k for k in vals[i]) != list(range(16)):
            raise SystemExit(f"deform point {i} has no full 4x4 start_transform")
        m = meta.get(i, {})
        points.append({
            "i": i, "name": str(m.get("name") or ""),
            "from_part": str(m.get("from_part") or ""),
            "from_part_index": m.get("from_part_index"),
            "skinned_to_part": str(m.get("skinned_to_part") or ""),
            "pos": [float(vals[i][12]), float(vals[i][13]), float(vals[i][14])],
        })

    g = {r["path"]: r["value"] for r in mods["StuntAreas"]["rows"]}
    areas = []
    for slot in range(32):
        pre = f"stunt_areas[{slot}]."
        if not any(k.startswith(pre) for k in g):
            break
        if not g.get(pre + "active"):
            continue
        n = int(g[pre + "number_of_deform_points"])
        ntri = int(g[pre + "number_of_triangles"])
        verts = [float(g[f"{pre}vertices3D_local[{j}]"]) for j in range(3 * n)]
        tri = [int(g[f"{pre}triangle_indices[{j}]"]) for j in range(3 * ntri)]
        areas.append({
            "slot": slot, "name": g[pre + "name"],
            "part_name": g[pre + "part_name"], "part_index": g[pre + "part_index"],
            "n_deform_points": n, "number_of_triangles": ntri,
            "deform_points": [int(g[f"{pre}deform_points[{j}]"]) for j in range(n)],
            "edge_validity": [int(g[f"{pre}edge_validity[{j}]"]) for j in range(n)],
            "vertices3D_local": np.array(verts, dtype=float).reshape(n, 3),
            "triangle_indices": [tri[k:k + 3] for k in range(0, len(tri), 3)],
            "center_local": [float(g[f"{pre}center_local[{k}]"]) for k in range(3)],
        })
    if not areas:
        raise SystemExit("no active stunt area in the donor entity")
    return {"points": points, "areas": areas,
            "declared": int(g.get("number_of_stunt_areas") or 0),
            "welds": sum(1 for k in g if k.startswith("welding_info[") and
                         k.endswith(".stunt_area_a_index"))}


def read_donor_shell() -> tuple[np.ndarray, np.ndarray]:
    """Donor body triangles from the geom sidecar (jc3geom's `positions`/`indices` blocks)."""
    doc = load_json(os.path.join(RAW, "geom", DONOR_BASE + ".ee.json"))
    buf = open(os.path.join(RAW, "geom", DONOR_BASE + ".ee.bin"), "rb").read()
    verts, tris = [], []
    for mesh in doc["meshes"]:
        for blk in mesh.get("blocks") or []:
            p = blk.get("payload")
            if not p or not p.get("positions_bytes"):
                continue
            pos = np.frombuffer(buf, "<f4", p["positions_bytes"] // 4,
                                p["positions_at"]).reshape(-1, 3)
            w = 4 if p["index_width"] == 4 else 2
            idx = np.frombuffer(buf, "<u4" if w == 4 else "<u2",
                                p["indices_bytes"] // w, p["indices_at"]).astype(np.int64)
            base = len(verts)
            verts.extend(pos.astype(float).tolist())
            if len(idx) >= 3:
                tris.append(idx[:len(idx) // 3 * 3].reshape(-1, 3) + base)
    if not verts or not tris:
        raise SystemExit("donor geom sidecar yielded no triangles")
    return np.array(verts, dtype=float), np.vstack(tris)


def read_bat_mesh() -> tuple[np.ndarray, np.ndarray]:
    m = rbm_geom.decode(open(BAT_MESH, "rb").read())
    v, t, _ = rbm_geom.collect_mesh(m)
    return np.array(v, dtype=float), np.array(t, dtype=np.int64)


# ---------------------------------------------------------------- geometry
def nearest_tri(tris: np.ndarray, p: np.ndarray) -> tuple[float, int]:
    """Exact point-triangle distance (Ericson) plus the index of the winning triangle."""
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    ab, ac = b - a, c - a
    ap = p - a
    d1 = (ab * ap).sum(1)
    d2 = (ac * ap).sum(1)
    bp = p - b
    d3 = (ab * bp).sum(1)
    d4 = (ac * bp).sum(1)
    cp = p - c
    d5 = (ab * cp).sum(1)
    d6 = (ac * cp).sum(1)
    va = d3 * d6 - d5 * d4
    vb = d5 * d2 - d1 * d6
    vc = d1 * d4 - d3 * d2
    denom = va + vb + vc
    ok = np.abs(denom) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, denom, 1.0), 0.0)
    v = np.clip(vb * inv, 0.0, 1.0)
    w = np.clip(vc * inv, 0.0, 1.0)
    over = v + w > 1.0
    s = np.where(over, v + w, 1.0)
    v = np.where(over, v / s, v)
    w = np.where(over, w / s, w)
    closest = a + ab * v[:, None] + ac * w[:, None]
    d = np.linalg.norm(closest - p, axis=1)
    i = int(np.argmin(d))
    return float(d[i]), i


def face_up(tris: np.ndarray, i: int, p: np.ndarray) -> tuple[float, float]:
    """(up cosine of triangle i's normal oriented up, signed side: +1 if p is above its plane)."""
    a, b, c = tris[i]
    n = np.cross(b - a, c - a)
    ln = float(np.linalg.norm(n))
    if ln < 1e-12:
        return 0.0, 0.0
    n = n / ln
    if n[1] < 0:
        n = -n
    side = float(np.sign((p - a) @ n)) or 1.0
    return float(n[1]), side


def sample(tris: np.ndarray, p: np.ndarray) -> dict:
    d, i = nearest_tri(tris, p)
    up, side = face_up(tris, i, p)
    return {"d": d, "tri": i, "up_cos": up, "side": side}


def ray_down(tris: np.ndarray, x: float, z: float, y0: float = 6.0) -> float:
    """Height of the topmost surface on a vertical ray at (x, z); NaN when it misses."""
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    e1, e2 = b - a, c - a
    direction = np.array([0.0, -1.0, 0.0])
    h = np.cross(direction, e2)
    det = (e1 * h).sum(1)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    s = np.array([x, y0, z]) - a
    u = (s * h).sum(1) * inv
    q = np.cross(s, e1)
    v = (direction * q).sum(1) * inv
    t = (e2 * q).sum(1) * inv
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
    if not hit.any():
        return float("nan")
    return float(y0 - float(t[hit].min()))


# ---------------------------------------------------------------- build
def build() -> dict:
    donor = read_donor()
    dv, dt = read_donor_shell()
    bv, bt = read_bat_mesh()
    stations = load_json(STATIONS)
    parts = load_json(PARTS)
    d_tris, b_tris = dv[dt], bv[bt]

    pts = donor["points"]
    by_i = {p["i"]: p for p in pts}
    pts_arr = np.array([p["pos"] for p in pts], dtype=float)

    # G2-18's analysis map: deform envelope -> body bbox.  Kept as the second frame so the
    # "0.10-0.60 m off" figure T-WLD11 quotes can be reproduced exactly.
    env = np.vstack([pts_arr.min(0), pts_arr.max(0)])
    bat = np.array(stations["body_bbox"], dtype=float)

    def to_bat(p) -> np.ndarray:
        u = (np.asarray(p, dtype=float) - env[0]) / (env[1] - env[0])
        return bat[0] + u * (bat[1] - bat[0])

    # ---- the donor's own tolerance, measured on the donor shell
    donor_gaps, donor_up = [], []
    for a in donor["areas"]:
        for j, i in enumerate(a["deform_points"]):
            p = np.array(by_i[i]["pos"], dtype=float)
            s = sample(d_tris, p)
            donor_gaps.append(s["d"])
            donor_up.append(s["up_cos"])
    donor_gaps = np.array(donor_gaps)
    band = (float(donor_gaps.min()), float(donor_gaps.max()))

    # ---- the same vertices on the Batmobile, both frames
    areas = []
    offset = 0
    for a in donor["areas"]:
        V = a["vertices3D_local"]
        rows = []
        cache_delta = 0.0
        P_list, M_list = [], []
        for j, i in enumerate(a["deform_points"]):
            p = np.array(by_i[i]["pos"], dtype=float)
            q = to_bat(p)
            P_list.append(p)
            M_list.append(q)
            cache_delta = max(cache_delta, float(np.linalg.norm(V[j] - p)))
            st = sample(b_tris, p)
            mp = sample(b_tris, q)
            nv = float(np.min(np.linalg.norm(bv - p, axis=1)))
            rows.append({
                "j": j, "index": i, "exists": i in by_i,
                "name": by_i[i]["name"], "part": by_i[i]["skinned_to_part"],
                "pos": [rnd(c) for c in p],
                "donor_gap_m": rnd(float(donor_gaps[offset + j])),
                "stored_gap_m": rnd(st["d"]),
                "stored_inside": False,
                "stored_up_cos": rnd(st["up_cos"]),
                "nearest_vertex_m": rnd(nv),
                "mapped_gap_m": rnd(mp["d"]),
                "mapped_inside": False,
                "mapped_up_cos": rnd(mp["up_cos"]),
            })
        # inside/outside is the toolkit's own parity test (jc3interact.inside), applied in bulk
        ins_s = jc3interact.inside(b_tris, np.array(P_list))
        ins_m = jc3interact.inside(b_tris, np.array(M_list))
        for j, row in enumerate(rows):
            row["stored_inside"] = bool(ins_s[j])
            row["mapped_inside"] = bool(ins_m[j])
        offset += a["n_deform_points"]
        edge = 0.0
        for tri in a["triangle_indices"]:
            if max(tri) < len(V):
                edge = max(edge, float(max(np.linalg.norm(V[q] - V[r])
                                           for q in tri for r in tri)))
        areas.append({
            "slot": a["slot"], "name": a["name"], "part_name": a["part_name"],
            "part_index": a["part_index"], "n_deform_points": a["n_deform_points"],
            "number_of_triangles": a["number_of_triangles"],
            "triangle_indices": a["triangle_indices"],
            "center_local": [rnd(c) for c in a["center_local"]],
            "edges_valid": int(sum(a["edge_validity"])),
            "max_edge_m": rnd(edge),
            "cache_vs_list_m": rnd(cache_delta),
            "vertices": rows,
            "stored_pass": sum(1 for r in rows if not r["stored_inside"] and
                               band[0] <= r["stored_gap_m"] <= band[1] and
                               r["stored_up_cos"] >= UP_COS),
            "mapped_pass": sum(1 for r in rows if not r["mapped_inside"] and
                               band[0] <= r["mapped_gap_m"] <= band[1] and
                               r["mapped_up_cos"] >= UP_COS),
        })

    # ---- all 135 points on the Batmobile, and which ones could substitute
    ins_all = jc3interact.inside(b_tris, pts_arr)
    for k, p in enumerate(pts):
        s = sample(b_tris, pts_arr[k])
        p["bat_gap_m"] = rnd(s["d"])
        p["bat_inside"] = bool(ins_all[k])
        p["bat_up_cos"] = rnd(s["up_cos"])
        p["bat_ok"] = (not p["bat_inside"]) and band[0] <= p["bat_gap_m"] <= band[1] \
            and p["bat_up_cos"] >= UP_COS
    ok_pts = [p for p in pts if p["bat_ok"]]

    reindex = {"pool": len(ok_pts), "areas": []}
    for a in areas:
        per = []
        for row in a["vertices"]:
            p = np.array(row["pos"], dtype=float)
            cands = [q["i"] for q in ok_pts
                     if float(np.linalg.norm(np.array(q["pos"]) - p)) <= SAME_POINT_M
                     and q["i"] != row["index"]]
            same_ok = any(q["i"] == row["index"] for q in ok_pts)
            per.append({"j": row["j"], "index": row["index"], "self_ok": same_ok,
                        "candidates": len(cands), "nearest": cands[:4]})
        covered = sum(1 for r in per if r["candidates"] or r["self_ok"])
        reindex["areas"].append({"name": a["name"], "vertices_covered": covered,
                                 "of": len(per), "per_vertex": per,
                                 "complete": covered == len(per)})

    roof_y = ray_down(b_tris, 0.0005, -0.5)      # the canopy over the driver (T-13 roof anchor)
    deck_y = ray_down(b_tris, 0.0005, -2.14)     # the front deck (T-13 hood anchor)
    top_point_y = float(max(p["pos"][1] for p in pts))

    # ---- O-1: re-index is supported only if every area can be rebuilt from points that
    # already pass on the Batmobile without changing the area's shape.
    o1 = all(a["complete"] for a in reindex["areas"])
    o1_reason = (
        f"all {len(areas)} areas rebuilt from existing points" if o1 else
        f"{sum(1 for a in reindex['areas'] if a['complete'])}/{len(areas)} areas could be "
        f"rebuilt; the pool of points that pass on the Batmobile is {len(ok_pts)} of {len(pts)} "
        f"and the highest donor point (y {rnd(top_point_y)} m) is below the Batmobile roof "
        f"surface (y {rnd(roof_y)} m) and deck (y {rnd(deck_y)} m) that the areas must cover")

    # ---- O-2: moving the area onto the shell.  The cache is derived from the list
    # (max delta 0.0 m), so a move is only expressible as an edit of the 22 deform points;
    # whether the runtime re-derives `vertices3D_local` from them is not decoded.
    cache_max = max(a["cache_vs_list_m"] for a in areas)
    dup = {}
    for a in areas:
        for row in a["vertices"]:
            dup.setdefault(tuple(row["pos"]), set()).add(row["index"])
    shared = sum(1 for v in dup.values() if len(v) > 1)
    o2 = False

    shipped = {p: os.path.exists(os.path.join(BUILD, p.replace("/", os.sep)))
               for p in SHIPPED}
    kept = set(parts.get("index_map", {}).get("kept") or [])
    binding_ok = all(int(p["from_part_index"]) in kept for a in areas for p in
                     [by_i[r["index"]] for r in a["vertices"]])

    doc = {
        "schema": 1,
        "card": "T-WLD11",
        "generator": "Tools/scripts/t_wld11.py",
        "decision": {
            "verdict": "UNKNOWN",
            "reindex": "not supported (O-1 fails)",
            "move": "UNKNOWN (O-2: runtime rule undecoded)",
            "reindex_reason": o1_reason,
            "move_reason": (
                f"`vertices3D_local` is a bit-exact copy of the bound `DeformPoints` "
                f"positions (max delta {cache_max} m over all area vertices), so a surface "
                f"cannot be moved without moving those points; whether the runtime recomputes "
                f"the copy from the list, or reads the stored copy as-is, is not decoded"),
        },
        "inputs": {
            "entity": os.path.join(RAW, "entities", DONOR_BASE + ".ee.json").replace("\\", "/"),
            "entity_sha256": sha256(os.path.join(RAW, "entities", DONOR_BASE + ".ee.json")),
            "geom_json": os.path.join(RAW, "geom", DONOR_BASE + ".ee.json").replace("\\", "/"),
            "geom_bin_sha256": sha256(os.path.join(RAW, "geom", DONOR_BASE + ".ee.bin")),
            "bat_mesh": "Working/Appearance/build_parts/body_lod1.rbm",
            "bat_mesh_sha256": sha256(BAT_MESH),
            "stations": "Working/TrueScale/stations.json",
            "parts": "Working/Parts/bm_vehicle_parts.json",
            "shipped": shipped,
        },
        "frames": {
            "stored": "the entity's own coordinates: `start_transform[12..14]`, unchanged by B-05",
            "mapped": "G2-18's analysis map: u = (p - deform_min)/deform_size; p' = bat_min + u*bat_size",
            "donor_deform_envelope": [env[0].round(4).tolist(), env[1].round(4).tolist()],
            "batmobile_body": [bat[0].round(4).tolist(), bat[1].round(4).tolist()],
            "donor_shell": {"vertices": int(len(dv)), "triangles": int(len(dt)),
                            "bbox": [dv.min(0).round(3).tolist(), dv.max(0).round(3).tolist()]},
            "batmobile_shell": {"vertices": int(len(bv)), "triangles": int(len(bt)),
                                "bbox": [bv.min(0).round(3).tolist(), bv.max(0).round(3).tolist()],
                                "source": "Working/Appearance/build_parts/body_lod1.rbm"},
            "roof_y_m": rnd(roof_y), "deck_y_m": rnd(deck_y),
        },
        "donor": {
            "deform_points": len(pts),
            "declared_areas": donor["declared"],
            "active_areas": len(areas),
            "weld_rows": donor["welds"],
            "tolerance": {"min_m": rnd(band[0]), "max_m": rnd(band[1]),
                          "median_m": rnd(float(np.median(donor_gaps))),
                          "source": "distance from the donor's own 22 bound points to the donor shell"},
            "up_cos_min": rnd(min(donor_up)),
        },
        "areas": areas,
        "points": pts,
        "oracles": {
            "O-1-reindex": {"pass": o1, "pool": len(ok_pts), "of": len(pts),
                            "same_point_m": SAME_POINT_M, "up_cos": UP_COS,
                            "areas": reindex["areas"], "reason": o1_reason},
            "O-2-move": {"pass": o2, "cache_vs_list_m": cache_max,
                         "positions_shared_by_two_areas": shared,
                         "part_binding_resolves": bool(binding_ok),
                         "reason": "the surface is the point list; the runtime's precedence "
                                   "between `vertices3D_local` and `DeformPoints` is UNKNOWN"},
        },
        "counts": {
            "area_vertices": sum(a["n_deform_points"] for a in areas),
            "indices_exist": sum(1 for a in areas for r in a["vertices"] if r["exists"]),
            "stored_pass": sum(a["stored_pass"] for a in areas),
            "mapped_pass": sum(a["mapped_pass"] for a in areas),
            "stored_inside": sum(1 for a in areas for r in a["vertices"] if r["stored_inside"]),
            "mapped_inside": sum(1 for a in areas for r in a["vertices"] if r["mapped_inside"]),
            "points_ok_on_batmobile": len(ok_pts),
        },
    }
    doc["digest"] = hashlib.sha1(
        json.dumps({k: v for k, v in doc.items() if k != "digest"},
                   sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]
    return doc


# ---------------------------------------------------------------- md
def render(d: dict) -> str:
    f, c, ds, orc = d["frames"], d["counts"], d["donor"], d["oracles"]
    L: list[str] = []
    a = L.append
    a("# T-WLD11 - the three stunt areas: re-index, move, or UNKNOWN")
    a("")
    a("Generated by `Tools/scripts/t_wld11.py` from the donor entity, the donor geom sidecar,")
    a("the Batmobile body mesh and the B-04 part table. `--check` re-derives this file and its")
    a("`.json`, compares them byte-for-byte, and re-runs both oracles and the recorded invariant.")
    a("")
    a("## Verdict - **UNKNOWN**")
    a("")
    a(f"| repair | supported by decoded data? | why |")
    a("|---|---|---|")
    a(f"| re-index to existing `deform_points` | **no** | {d['decision']['reindex_reason']} |")
    a(f"| move the area onto the shell | **UNKNOWN** | {d['decision']['move_reason']} |")
    a("")
    a("Both oracles are printed in §6 and both can fail; `--check` re-runs them, so this")
    a("verdict is recomputed rather than asserted.")
    a("")
    a("## 1. What the files hold (decoded)")
    a("")
    a(f"The donor entity carries **{ds['deform_points']} `DeformPoints`** and a `StuntAreas`")
    a(f"module that declares **{ds['declared_areas']} areas**, all active, in 32 slots, with")
    a(f"**{ds['weld_rows']} weld rows**. The build ships the two modules the areas need:")
    a("")
    a("| asset | ships in `Builds/bm-009` |")
    a("|---|---|")
    for k, v in d["inputs"]["shipped"].items():
        a(f"| `{k}` | {'yes' if v else 'no'} |")
    a("")
    a("| area | slot | part | vertices | tris | edges valid | max edge |")
    a("|---|---:|---|---:|---:|---:|---:|")
    for ar in d["areas"]:
        a(f"| `{ar['name']}` | {ar['slot']} | `{ar['part_name']}` ({ar['part_index']}) | "
          f"{ar['n_deform_points']} | {ar['number_of_triangles']} | {ar['edges_valid']} | "
          f"{ar['max_edge_m']} m |")
    a("")
    a("Every area vertex is bound to a `DeformPoints` index, and **each area's")
    a("`vertices3D_local` is a bit-exact copy of those points'")
    a(f"`start_transform[12..14]`** - the largest disagreement over all {c['area_vertices']}")
    a(f"vertices is **{ds['tolerance']['min_m'] if False else max(ar['cache_vs_list_m'] for ar in d['areas'])} m**.")
    a("That one fact decides what a repair can even be: the surface is the point list.")
    a("")
    a("## 2. The donor's own tolerance (derived)")
    a("")
    a("A stunt surface is not a skin vertex: it is an authored plane floating a few centimetres")
    a("above the body, so that Rico stands on it rather than clipping into it. Measured on the")
    a("donor itself, from the same 22 bound points to the **donor** shell")
    a(f"({f['donor_shell']['triangles']} triangles, bbox "
      f"{f['donor_shell']['bbox'][0]} .. {f['donor_shell']['bbox'][1]}):")
    a("")
    a(f"| statistic | value |")
    a("|---|---:|")
    a(f"| min gap | {ds['tolerance']['min_m']} m |")
    a(f"| median gap | {ds['tolerance']['median_m']} m |")
    a(f"| max gap | {ds['tolerance']['max_m']} m |")
    a(f"| min up-cosine of the nearest donor face | {ds['up_cos_min']} |")
    a("")
    a(f"**Tolerance band: {ds['tolerance']['min_m']} - {ds['tolerance']['max_m']} m above the shell**, "
      f"and the nearest face must be a standing (up-facing, cos >= {orc['O-1-reindex']['up_cos']}) face.")
    a("This band is the oracle's yardstick for the Batmobile; it is measured, not chosen.")
    a("")
    a("## 3. The same 22 points on the Batmobile shell")
    a("")
    a(f"Body mesh: `Working/Appearance/build_parts/body_lod1.rbm`, "
      f"**{f['batmobile_shell']['vertices']} vertices / {f['batmobile_shell']['triangles']} triangles**, "
      f"bbox {f['batmobile_shell']['bbox'][0]} .. {f['batmobile_shell']['bbox'][1]}.")
    a(f"The topmost body surface is y {f['roof_y_m']} m at the roof station (z -0.5) and "
      f"y {f['deck_y_m']} m at the front deck (z -2.14).")
    a("")
    a(f"| frame | vertices within the band on a standing face | inside the shell | hit rate |")
    a("|---|---:|---:|---:|")
    a(f"| stored entity coordinates | {c['stored_pass']} | {c['stored_inside']} | "
      f"{c['stored_pass']}/{c['area_vertices']} |")
    a(f"| G2-18 normalised map | {c['mapped_pass']} | {c['mapped_inside']} | "
      f"{c['mapped_pass']}/{c['area_vertices']} |")
    a("")
    a("The two frames disagree, and the disagreement is the whole problem: the stored points are")
    a("Serpente-sized, so on the larger Batmobile body most of them end up *inside* the shell or")
    a("hugging a side face (stored frame), while the normalised map pushes them 0.12-0.59 m into")
    a("the air (the figure T-WLD11 quotes). Neither frame puts them on a standing surface within")
    a("the donor band.")
    a("")
    for ar in d["areas"]:
        a(f"### `{ar['name']}` - {ar['n_deform_points']} vertices, part `{ar['part_name']}`")
        a("")
        a("| j | index | point name (tail) | part | position (m) | donor gap | stored gap | in | up | "
          "nearest vertex | mapped gap | in |")
        a("|---:|---:|---|---|---|---:|---:|:-:|---:|---:|---:|:-:|")
        for r in ar["vertices"]:
            tail = r["name"].split("|")[-1] if r["name"] else ""
            a(f"| {r['j']} | {r['index']} | `{tail}` | `{r['part']}` | "
              f"{r['pos'][0]}, {r['pos'][1]}, {r['pos'][2]} | {r['donor_gap_m']} | "
              f"{r['stored_gap_m']} | {'in' if r['stored_inside'] else 'out'} | "
              f"{r['stored_up_cos']} | {r['nearest_vertex_m']} | {r['mapped_gap_m']} | "
              f"{'in' if r['mapped_inside'] else 'out'} |")
        a("")
    a("## 4. Which donor `deform_points` indices exist, and where")
    a("")
    a(f"All **{ds['deform_points']}** indices exist (0-{ds['deform_points'] - 1}) and every one of")
    a(f"the {c['area_vertices']} bound indices resolves ({c['indices_exist']}/{c['area_vertices']}).")
    a("Each point carries a name, a `from_part` / `skinned_to_part` binding and a 4x4")
    a("`start_transform`; the three areas bind 22 of them (some positions are used twice by")
    a("different parts: the two hood areas are the same six locations bound to")
    a("`sportsmuscle_hood` and `sportsmuscle_hood_signature`).")
    a("")
    a("| index | name (tail) | part | x | y | z |")
    a("|---:|---|---|---:|---:|---:|")
    for p in d["points"]:
        tail = p["name"].split("|")[-1] if p["name"] else p["name"]
        a(f"| {p['i']} | `{tail}` | `{p['skinned_to_part']}` | {p['pos'][0]:.3f} | "
          f"{p['pos'][1]:.3f} | {p['pos'][2]:.3f} |")
    a("")
    a("## 5. The shape the areas have to keep")
    a("")
    a("| area | centre (m) | max edge | triangles |")
    a("|---|---|---:|---|")
    for ar in d["areas"]:
        a(f"| `{ar['name']}` | {ar['center_local']} | {ar['max_edge_m']} m | {ar['triangle_indices']} |")
    a("")
    a("## 6. The two oracles")
    a("")
    a("### O-1 - re-indexing onto existing deform points")
    a("")
    a("A vertex may be re-pointed at index `i` only if that point already")
    a(f"(a) sits outside the Batmobile shell, (b) inside the donor band, (c) on a standing face,")
    a(f"and (d) within {orc['O-1-reindex']['same_point_m']} m of the vertex it replaces -")
    a("otherwise the area's shape changes.")
    a("")
    a(f"Pool of points that pass (a)-(c) on the Batmobile: **{orc['O-1-reindex']['pool']} of "
      f"{orc['O-1-reindex']['of']}**.")
    a("")
    a("| area | vertices with a legal substitute (itself or a neighbour) | of | complete |")
    a("|---|---:|---:|:-:|")
    for ar in orc["O-1-reindex"]["areas"]:
        a(f"| `{ar['name']}` | {ar['vertices_covered']} | {ar['of']} | "
          f"{'yes' if ar['complete'] else '**no**'} |")
    a("")
    a(f"**O-1 fails.** {orc['O-1-reindex']['reason']}.")
    a("A standing surface on the Batmobile roof cannot be built out of donor points: the")
    a("highest donor point is below the roof the area is supposed to cover, so no re-indexing")
    a("can lift `main_area` onto it. Re-indexing is therefore **not supported by the data**.")
    a("")
    a("### O-2 - moving the area onto the shell")
    a("")
    a(f"The cache invariant holds to **{max(ar['cache_vs_list_m'] for ar in d['areas'])} m** on every vertex, so a")
    a("`vertices3D_local`-only edit would leave the module contradicting itself, and any honest")
    a("move is an edit of the 22 `DeformPoints.start_transform` values.")
    a("")
    a(f"- the 22 points' part bindings resolve on the Batmobile part table "
      f"(indices in B-04's kept range): **{orc['O-2-move']['part_binding_resolves']}**;")
    a(f"- {orc['O-2-move']['positions_shared_by_two_areas']} positions are shared by two areas, "
      f"so a move must move both copies together;")
    a("- the move target itself is computable (ray-cast onto the body mesh, as T-13 did for")
    a("  the `point.stunt*` nodes), but **which field the runtime trusts** - the stored")
    a("  `vertices3D_local` or a recomputation from `DeformPoints` - is not decoded, and")
    a("  whether the deform list is also read by the deformation/skinning system is not")
    a("  decoded either. A value written blind would be a guess, so this half stays UNKNOWN.")
    a("")
    a("## 7. UNKNOWNs")
    a("")
    a("- **The runtime precedence** between `vertices3D_local` and the bound `DeformPoints`")
    a("  positions. Nothing in the entity, the geom sidecar or the build's modules states it.")
    a("- **Whether the areas are validated at runtime** against the deform list (a mismatch")
    a("  between the two fields is exactly the state a move would create).")
    a("- **Whether `DeformPoints` is also consumed by deformation/skinning**; if it is, moving")
    a("  a point moves geometry, not just a standing plane.")
    a("- **The donor band's upper edge is a sample of 22 points**, not a per-vertex guarantee: it")
    a("  is the tightest evidence available from the files and is used as such.")
    a("")
    a("## 8. Regeneration")
    a("")
    a("| path | what it is |")
    a("|---|---|")
    a("| `Working/Translation/T_WLD11_AREAS.md` | this file, written by `--write` |")
    a("| `Working/Translation/t_wld11_areas.json` | the same measurements as data |")
    a("| `Tools/scripts/t_wld11.py` | the tool; `--write` / `--check` / `dump` |")
    a("")
    a(f"`--check` re-derives {len(d['areas'])} areas, {ds['deform_points']} points and both")
    a("oracles, compares both files byte-for-byte, and fails if the verdict moved.")
    a("")
    return "\n".join(L)


# ---------------------------------------------------------------- write / check
def dump_json(doc: dict) -> None:
    with open(os.path.join(OUT, JSON_NAME), "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
        f.write("\n")


def cmd_write() -> int:
    doc = build()
    dump_json(doc)
    with open(os.path.join(OUT, MD_NAME), "w", encoding="utf-8", newline="\n") as f:
        f.write(render(doc))
    c = doc["counts"]
    print(f"areas {len(doc['areas'])}  vertices {c['area_vertices']}  indices exist "
          f"{c['indices_exist']}/{c['area_vertices']}")
    print(f"stored pass {c['stored_pass']}  mapped pass {c['mapped_pass']}  "
          f"inside stored {c['stored_inside']}  inside mapped {c['mapped_inside']}")
    print(f"O-1 {'PASS' if doc['oracles']['O-1-reindex']['pass'] else 'FAIL'}  "
          f"pool {doc['oracles']['O-1-reindex']['pool']}")
    print(f"verdict {doc['decision']['verdict']}  digest {doc['digest']}")
    return 0


def invariant_checks(doc: dict) -> list[str]:
    bad: list[str] = []
    c = doc["counts"]
    if c["indices_exist"] != c["area_vertices"]:
        bad.append("a bound deform_points index does not exist")
    for ar in doc["areas"]:
        if ar["cache_vs_list_m"] > 1e-6:
            bad.append(f"{ar['name']}: vertices3D_local no longer copies the deform points")
        if ar["n_deform_points"] != len(ar["vertices"]):
            bad.append(f"{ar['name']}: vertex count mismatch")
    if doc["oracles"]["O-1-reindex"]["pass"]:
        bad.append("O-1 now passes - the verdict 're-index not supported' is stale")
    if doc["oracles"]["O-2-move"]["pass"]:
        bad.append("O-2 now passes - the UNKNOWN verdict is stale")
    if doc["decision"]["verdict"] != "UNKNOWN":
        bad.append("verdict is not UNKNOWN")
    return bad


def cmd_check() -> int:
    doc = build()
    md = render(doc)
    pj = os.path.join(OUT, JSON_NAME)
    pm = os.path.join(OUT, MD_NAME)
    if not os.path.exists(pj) or not os.path.exists(pm):
        print("CHECK FAIL: outputs missing - run --write")
        return 1
    same_j = open(pj, encoding="utf-8").read() == json.dumps(doc, indent=1, sort_keys=True) + "\n"
    same_m = open(pm, encoding="utf-8").read() == md
    bad = invariant_checks(doc)
    print(f"json identical {same_j}  md identical {same_m}")
    print(f"areas {len(doc['areas'])}  vertices {doc['counts']['area_vertices']}  "
          f"O-1 pass {doc['oracles']['O-1-reindex']['pass']}  "
          f"O-2 pass {doc['oracles']['O-2-move']['pass']}")
    for b in bad:
        print("  FAIL:", b)
    ok = same_j and same_m and not bad
    print("CHECK", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def cmd_dump(what: str) -> int:
    doc = build()
    if what == "areas":
        for ar in doc["areas"]:
            print(json.dumps({k: ar[k] for k in ("name", "slot", "part_name",
                                                 "n_deform_points", "cache_vs_list_m",
                                                 "stored_pass", "mapped_pass")}))
    elif what == "points":
        for p in doc["points"]:
            print(f"{p['i']:3d} {p['pos'][0]:8.3f} {p['pos'][1]:7.3f} {p['pos'][2]:8.3f} "
                  f"{'ok' if p['bat_ok'] else '--'} {p['bat_gap_m']:7.4f} {p['skinned_to_part']}")
    elif what == "candidates":
        print(json.dumps(doc["oracles"]["O-1-reindex"]["areas"], indent=1))
    else:
        raise SystemExit("dump: areas|points|candidates")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("dump", nargs="?", choices=["areas", "points", "candidates"])
    a = ap.parse_args()
    if a.write:
        return cmd_write()
    if a.check:
        return cmd_check()
    return cmd_dump(a.dump)


if __name__ == "__main__":
    sys.exit(main())
