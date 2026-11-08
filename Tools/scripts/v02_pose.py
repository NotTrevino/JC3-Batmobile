#!/usr/bin/env python
"""v02_pose.py - render one V-02 pose in its own process, for `v02_rc4.py`.

The parent assembles the delivered parts once into `Builds/bm-RC4/verify/v02/_assembly.npz`; this
child loads that cache, rotates the exact triangles of the moving subtree about the decoded bone
pivot from `Working/Translation/T8_PARTS.json`, and writes:

  <name>.png           the assembled car, posed part in amber
  <name>_isolated.png  the same part unposed (grey) and posed (amber), in one frame
  <name>.json          the record the parent reads (limit, axis, pivot, PNG hashes)

One process per pose because the software renderer's peak is large and this box is shared.

    python Tools/scripts/v02_pose.py pose_turret_yaw_max <cache.npz>
    python Tools/scripts/v02_pose.py pose_base <cache.npz>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import v02_rc4 as V
from preview_rbm import render

AMBER = np.array([0.95, 0.62, 0.15], np.float32)
GREY = np.array([0.55, 0.57, 0.60], np.float32)
LIGHT = (0.35, 0.8, -0.45)


def sha(p: str) -> str:
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def rel(p: str) -> str:
    return os.path.relpath(p, V.ROOT).replace(os.sep, "/")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("cache")
    a = ap.parse_args()
    os.makedirs(V.POSE_DIR, exist_ok=True)
    d = np.load(a.cache)
    T, C, owner = d["T"], d["C"], d["owner"]

    if a.name == "pose_base":
        img, _ = render(T, C, "side", 1000, light=LIGHT)
        p = os.path.join(V.POSE_DIR, "pose_base.png")
        img.save(p)
        rec = {"pose": "pose_base", "status": "rendered", "angle_deg": 0,
               "file": rel(p), "view": "side", "width": img.width, "height": img.height,
               "png_sha256": sha(p),
               "note": "the delivered pose; every section at its authored 0 position"}
        json.dump(rec, open(os.path.join(V.POSE_DIR, "pose_base.json"), "w", encoding="utf-8",
                            newline="\n"), indent=1)
        return 0

    spec = next((s for s in V.POSE_PLAN if s["name"] == a.name), None)
    if spec is None:
        raise SystemExit(f"unknown pose {a.name}")
    cfg = {r["id"]: r for r in json.load(open(V.T8, encoding="utf-8"))["rows"]}
    j = V.resolve_pose(spec, cfg)
    parts = V.bm_parts.decode_parts(open(V.PARTS, "rb").read())
    pr = next((p for p in parts if p["name"] == spec["part"]), None)
    if pr is None:
        raise SystemExit(f"{spec['part']} is not a part in the delivered module")
    if not j["pivot"]:
        raise SystemExit(f"{spec['name']}: no decoded pivot")

    sub = V._subtree(parts, pr["part_index"])
    mask = np.isin(owner, sorted(sub))
    if not mask.any():
        raise SystemExit(f"{spec['name']}: no triangles owned by {sorted(sub)}")
    R, ax = V._rot(j["axis"], j["angle_deg"])
    piv = np.asarray(j["pivot"], np.float64)
    TT, CC = T.copy(), C.copy()
    TT[mask] = (TT[mask] - piv) @ R.T + piv
    CC[mask] = AMBER

    img, _ = render(TT, CC, j["view"], 1000, light=LIGHT)
    p = os.path.join(V.POSE_DIR, f"{a.name}.png")
    img.save(p)

    # isolated: the unposed subtree in grey beside its posed copy in amber, framed to the part
    I, J = T[mask], TT[mask]
    TI = np.concatenate([I, J])
    CI = np.concatenate([np.tile(GREY, (len(I), 1)), np.tile(AMBER, (len(J), 1))])
    iso, _ = render(TI, CI, j["view"], 1000, light=LIGHT)
    ip = os.path.join(V.POSE_DIR, f"{a.name}_isolated.png")
    iso.save(ip)

    rec = {"pose": a.name, "part": spec["part"], "joint": spec["rid"],
           "limit_deg": j["angle_deg"], "angle_deg": j["angle_deg"],
           "axis": [round(float(x), 3) for x in ax],
           "pivot_m": [round(float(x), 4) for x in piv],
           "view": j["view"], "parts_moved": sorted(sub),
           "triangles_moved": int(mask.sum()),
           "status": "rendered", "note": j["note"],
           "file": rel(p), "isolated_file": rel(ip),
           "width": img.width, "height": img.height,
           "isolated_width": iso.width, "isolated_height": iso.height,
           "png_sha256": sha(p), "isolated_sha256": sha(ip)}
    json.dump(rec, open(os.path.join(V.POSE_DIR, f"{a.name}.json"), "w", encoding="utf-8",
                        newline="\n"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
