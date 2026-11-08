"""v02_render.py - V-02 (part): assembled-car renders of the RC, and do the shipped Serpente panels SHOW?

Assembles every part of Builds/bm-RC1's parts module at LOD1 (first mesh of its .lod), placed by the
parent chain of `parent_space_offset` (4x4, translation in [12:15]), and z-buffer renders six views
(side L/R, front, rear, top, bottom) with preview_rbm.render. Meshes byte-identical to the vanilla
Serpente are drawn RED, the Batmobile's own GREY, so any visible red is Serpente bodywork showing
through. Parts with starts_deleted are skipped (they never draw).

Out: Builds/bm-RC1/verify/v02/{side_l,side_r,front,rear,top,bottom}.png + geometry.json
    python Tools/scripts/v02_render.py
Not covered here (V-02 items 2-4): pose renders at each moving part's limits, the silhouette %,
interaction-point distances. Exit 0 only if no view shows more than 0.5 % red of the car's pixels.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import bm_parts  # noqa: E402
import jc3geom  # noqa: E402  (decodes every block type, GeneralMkIII included)
from preview_rbm import render  # noqa: E402

RC = os.path.join(ROOT, "Builds", "bm-RC1")
A = os.path.join(RC, "aaf")
OUT = os.path.join(RC, "verify", "v02")
LIMIT = 0.5   # % red of car pixels


def main() -> int:
    import v04_audio  # noqa: F401  (keeps sys.path consistent)
    import bm_budget
    V = bm_budget._vanilla()
    parts = bm_parts.decode_parts(open(os.path.join(A, bm_parts.MODULE), "rb").read())
    by_i = {p["part_index"]: p for p in parts}

    def world(p):
        M = np.array(p["parent_space_offset"], np.float64).reshape(4, 4)
        q = by_i.get(p["parent_part_index"])
        return M @ world(q) if q is not None and q is not p else M

    tris, cols, per = [], [], {}
    for p in parts:
        if p.get("starts_deleted"):
            continue
        lod = os.path.join(A, p["model"])
        if not os.path.exists(lod):
            continue
        first = next((l.strip() for l in open(lod, encoding="utf-8") if l.strip().endswith(".rbm")), None)
        f = os.path.join(A, first) if first else None
        if not f or not os.path.exists(f):
            continue
        raw = open(f, "rb").read()
        vanilla = V.get(first) == raw
        lamp = vanilla and bool(p.get("has_lights"))   # kept vanilla lamps (user 2026-10-31): amber, not red
        M = world(p)
        d = jc3geom.decode_mesh(raw, first)
        n = 0
        for b in d["blocks"]:
            if not b.get("positions") or not b.get("indices"):
                continue
            P = np.asarray(b["positions"], np.float64)[:, :3]
            I = np.asarray(b["indices"], np.int64)
            I = I[: len(I) // 3 * 3].reshape(-1, 3)
            I = I[(I < len(P)).all(1)]
            t = P[I]
            if not len(t):
                continue
            h = np.concatenate([t, np.ones(t.shape[:2] + (1,))], axis=2) @ M
            tris.append(h[:, :, :3].astype(np.float32))
            cols.append(np.tile(np.array([0.95, 0.6, 0.05] if lamp else [0.85, 0.08, 0.08] if vanilla else [0.55, 0.57, 0.6], np.float32), (len(t), 1)))
            n += len(t)
        per[p["name"]] = {"tris": n, "vanilla_mesh": vanilla, "kept_lamp": lamp}
    T, C = np.concatenate(tris), np.concatenate(cols)
    os.makedirs(OUT, exist_ok=True)
    views = {"side_l": ("side", 1), "side_r": ("side", -1), "rear": ("front", 1), "front": ("front", -1),  # +z faces the rear (taillights seen there)
             "top": ("top", 1), "bottom": ("top", -1)}
    axis = {"side": 0, "front": 2, "top": 1}
    res = {}
    for name, (v, sgn) in views.items():
        TT = T.copy()
        if sgn < 0:   # look from the other side: mirror the depth axis
            TT[:, :, axis[v]] *= -1
            TT[:, :, 0 if v != "side" else 2] *= -1
        img, _ = render(TT, C, v, 1000, light=(0.3, 0.85, -0.45))
        img.save(os.path.join(OUT, f"{name}.png"))
        a = np.asarray(img).astype(np.int32)
        car = (np.abs(a - a[0, 0]).sum(2) > 10)
        red = car & (a[:, :, 0] > 1.8 * a[:, :, 1] + 10) & (a[:, :, 0] > 1.8 * a[:, :, 2] + 10)
        amber = car & (a[:, :, 0] > 1.8 * a[:, :, 2] + 10) & (a[:, :, 1] > 1.8 * a[:, :, 2] + 10)
        res[name] = {"car_px": int(car.sum()), "red_px": int(red.sum()), "lamp_px": int(amber.sum()),
                     "lamp_pct": round(100.0 * amber.sum() / max(car.sum(), 1), 3),
                     "red_pct": round(100.0 * red.sum() / max(car.sum(), 1), 3)}
    vis = {k: v for k, v in res.items() if v["red_pct"] > LIMIT}
    json.dump({"views": res, "parts": per, "limit_pct": LIMIT}, open(os.path.join(OUT, "geometry.json"), "w"), indent=1)
    for k, v in res.items():
        print(f"{k:7s} car {v['car_px']:7d} px, Serpente-red {v['red_px']:6d} px = {v['red_pct']:.3f} %, kept lamps {v['lamp_pct']:.3f} %")
    shown = sorted(k for k, v in per.items() if v["vanilla_mesh"])
    print(f"{len(per)} parts drawn ({len(shown)} with vanilla Serpente meshes); "
          + ("PASS: no view shows Serpente bodywork above 0.5 %" if not vis else f"FAIL: Serpente bodywork visible in {sorted(vis)}"))
    return 0 if not vis else 1


if __name__ == "__main__":
    sys.exit(main())
