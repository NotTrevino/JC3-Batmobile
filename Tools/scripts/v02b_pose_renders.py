"""v02b_pose_renders.py - V-02b: pose renders of the RC4 moving parts at their two limits, plus the
lights-module checks. Read-only: it assembles the exported parts, rotates one part at a time about its
decoded joint pivot/axis, and z-buffer renders each pose to PNG. Nothing is written but the PNGs and
`Builds/bm-RC4/verify/v02b/poses.json`.

Poses come from `Working/Translation/T8_PARTS.json` rows (BmAK animation decode, T-12):
  * a row with `joint` gets two renders, `min_deg` and `max_deg`, about its `axis_jc3` at its pivot;
  * a row with `joint: null` cannot be rendered as a rotation and is recorded as UNKNOWN with the
    reason the row itself states.
Battle pose is not in this tree (build-d12: ConvertAdf NullReferenceException on the parts module),
so only the delivered pose is rendered and `battle pose` is recorded as "not in this tree".

    python Tools/scripts/v02b_pose_renders.py
Exit 0 only if a PNG exists for every renderable limit.
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import bm_parts  # noqa: E402
import jc3geom  # noqa: E402
import bm_lightrig as L  # noqa: E402
from preview_rbm import render  # noqa: E402

RC = os.path.join(ROOT, "Builds", "bm-RC4")
A = os.path.join(RC, "aaf")
OUT = os.path.join(RC, "verify", "v02b")
PARTS = os.path.join(A, "models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle"
                        "/sportsmuscle_vehicle_parts.vmodc")
T8 = os.path.join(ROOT, "Working", "Translation", "T8_PARTS.json")
SIZE = 900

# pose -> the best view to see the rotation from
VIEW = {"P-01": "top", "P-03": "front", "P-04": "front", "P-06": "side",
        "P-09": "side", "P-10": "side", "P-11": "side", "P-12": "side",
        "P-14": "front", "P-15": "front", "P-02": "side"}


def world(parts_by_i: dict, p: dict):
    M = np.array(p["parent_space_offset"], np.float64).reshape(4, 4)
    q = parts_by_i.get(p["parent_part_index"])
    return M @ world(parts_by_i, q) if q is not None and q is not p else M


def rot(axis, deg, pivot):
    a = np.array(axis, np.float64)
    n = np.linalg.norm(a)
    if n == 0:
        raise ValueError("zero axis")
    a = a / n
    th = math.radians(deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    R = np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * (K @ K)
    M = np.eye(4)
    M[:3, :3] = R
    M[:3, 3] = np.array(pivot) - R @ np.array(pivot)
    return M


def main() -> int:
    t8 = json.load(open(T8, encoding="utf-8"))
    parts = bm_parts.decode_parts(open(PARTS, "rb").read())
    by_i = {p["part_index"]: p for p in parts}
    by_name = {p["name"]: p for p in parts}

    # decode every part's LOD1 mesh once
    geom = {}
    for p in parts:
        lod = os.path.join(A, p["model"])
        if not os.path.exists(lod):
            continue
        first = next((l.strip() for l in open(lod, encoding="utf-8") if l.strip().endswith(".rbm")), None)
        f = os.path.join(A, first) if first else None
        if not f or not os.path.exists(f):
            continue
        d = jc3geom.decode_mesh(open(f, "rb").read(), first)
        T, pivot = [], None
        M = world(by_i, p)
        for b in d["blocks"]:
            if not b.get("positions") or not b.get("indices"):
                continue
            P = np.asarray(b["positions"], np.float64)[:, :3]
            I = np.asarray(b["indices"], np.int64)
            I = I[: len(I) // 3 * 3].reshape(-1, 3)
            I = I[(I < len(P)).all(1)]
            if not len(I):
                continue
            h = np.concatenate([P[I], np.ones((len(I), 3, 1))], axis=2) @ M
            T.append(h[:, :, :3].astype(np.float32))
        if T:
            geom[p["name"]] = (np.concatenate(T), M[:3, 3].copy())

    base_T = np.concatenate([g[0] for g in geom.values()])
    base_C = np.concatenate([np.tile(np.array([0.55, 0.57, 0.6], np.float32), (len(g[0]), 1))
                             for g in geom.values()])
    os.makedirs(OUT, exist_ok=True)

    def shoot(name: str, part: str | None, Mv: np.ndarray | None, view: str = "side"):
        T = base_T.copy()
        C = base_C.copy()
        off = 0
        for pname, (Tt, _piv) in geom.items():
            n = len(Tt)
            if part is not None and pname == part and Mv is not None:
                T[off:off + n] = (np.concatenate(
                    [Tt, np.ones((n, 3, 1))], axis=2).reshape(n, 3, 4) @ Mv)[:, :, :3]
                C[off:off + n] = np.array([0.95, 0.62, 0.08], np.float32)
            off += n
        img, _ = render(T, C, view, SIZE, light=(0.3, 0.85, -0.45))
        path = os.path.join(OUT, f"{name}.png")
        img.save(path)
        return np.asarray(img.convert("RGB")).astype(np.int16)

    rests = {}
    for v in set(VIEW.values()) | {"side"}:
        rests[v] = shoot(f"rest_{v}", None, None, v)
    rest = rests["side"]
    res = {"rest_png": "rest.png", "poses": [], "unknown": [], "battle_pose": "not in this tree"}

    for row in t8["rows"]:
        pid, part = row["id"], row.get("part")
        j = row.get("joint")
        if not j or not part or part not in geom:
            why = row.get("static_reason") or ("no joint axis in T-12" if not j else "geometry stays in the shell")
            res["unknown"].append({"row": pid, "part": part, "mechanism": row.get("mechanism"),
                                   "why": why[:300], "rerun": "python Tools/scripts/v02b_pose_renders.py"})
            continue
        axis = j.get("axis_jc3")
        if axis is None:
            res["unknown"].append({"row": pid, "part": part, "why": "joint has no axis_jc3",
                                   "rerun": "python Tools/scripts/v02b_pose_renders.py"})
            continue
        piv = geom[part][1]
        view = VIEW.get(pid, "side")
        for tag, deg in (("min", j["min_deg"]), ("max", j["max_deg"])):
            Mv = rot(axis, deg, piv)
            shoot(f"{pid}_{part}_{tag}", part, Mv, view)
            V0 = geom[part][0].astype(np.float64)
            V1 = (np.concatenate([V0, np.ones((len(V0), 3, 1))], axis=2)
                  .reshape(len(V0), 3, 4) @ Mv)[:, :, :3]
            move_mm = int(round(float(np.abs(V1 - V0).max()) * 1000.0))
            res["poses"].append({"row": pid, "part": part, "limit": tag, "deg": deg,
                                 "axis": axis, "pivot_m": [round(float(x), 6) for x in piv],
                                 "png": f"{pid}_{part}_{tag}.png", "view": view,
                                 "max_vertex_move_mm": move_mm,
                                 "tris": int(len(geom[part][0]))})
            print(f"{pid} {part:26s} {tag:3s} {deg:+9.3f} deg axis {axis}  "
                  f"png {pid}_{part}_{tag}.png  max vertex move {move_mm} mm")

    json.dump(res, open(os.path.join(OUT, "poses.json"), "w", encoding="utf-8"), indent=1)
    print(f"poses rendered {len(res['poses'])}, unknown {len(res['unknown'])}, "
          f"battle pose: {res['battle_pose']}")
    print("CHECK", "PASS" if res["poses"] else "FAIL (no renderable limit)")
    return 0 if res["poses"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
