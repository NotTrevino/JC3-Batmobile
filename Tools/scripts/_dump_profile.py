#!/usr/bin/env python3
"""
_dump_profile.py - print the numbers the tumbler carve actually works from.

Why
---
The first carve pass produced a flat slab with the greenhouse crushed away. That is a
bug in the *target*, not in the fit, and it is invisible in a render: all you see is a
low box. The cause is that the Tumbler's per-slice roofline is taken as a percentile of
every vertex in the slice, and the Batmobile carries rear fins and aerials that sit far
above the body -- so "the top of this slice" measures a fin, the donor's roof gets mapped
to fin height, and everything below it is squashed proportionally.

So: print the donor's roofline, the target's distribution at several percentiles, and
the ratio the fit would apply, slice by slice. Numbers first, then a picture.

Usage:
    python _dump_profile.py --cloud <Batmobile_V2.pskx> [--slices 48] [--top-pct 99]
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    import numpy as np
    import psk_geom
    import rbm_geom

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cloud", required=True)
    ap.add_argument("--input", default=r"E:\Modding\_gamedata\jc3_early\SerpenteR-EE\models"
                                     r"\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle"
                                     r"\sportsmuscle_body_lod1.rbm")
    ap.add_argument("--parts", help="file list building the SHARED vehicle frame; the frame "
                                    "must match the build or these numbers are not comparable")
    ap.add_argument("--slices", type=int, default=48)
    ap.add_argument("--top-pct", type=float, default=99.0)
    args = ap.parse_args()

    m = rbm_geom.decode(open(args.input, "rb").read())
    V = np.asarray(rbm_geom.np_all_positions(m), dtype=np.float64)

    # The frame must come from the same set of parts the build displaces, or the target
    # cloud is fitted to a different length and every number below is off by that ratio.
    frame_pts = list(rbm_geom.np_all_positions(m))
    if args.parts:
        frame_pts = []
        for line in open(args.parts, encoding="utf-8-sig"):
            line = line.strip()
            if line:
                frame_pts.extend(rbm_geom.np_all_positions(
                    rbm_geom.decode(open(line, "rb").read())))
    lo, hi, span = rbm_geom.make_ref(frame_pts)
    print(f"shared frame from {len(frame_pts)} vertices"
          + (" (--parts)" if args.parts else " (this file only)"))

    T = rbm_geom._tumbler_cloud(args.cloud, (lo, hi, span), length=1.0)
    N = args.slices

    def slice_index(P):
        z = (P[:, 2] - P[:, 2].min()) / (P[:, 2].max() - P[:, 2].min())
        return np.clip((z * N).astype(np.int64), 0, N - 1)

    ti = slice_index(T)

    print(f"donor  {os.path.basename(args.input)}: {len(V)} verts over {N} slices")
    print(f"  frame  Z {lo[2]:+.3f}..{hi[2]:+.3f}   Y {lo[1]:+.3f}..{hi[1]:+.3f}")
    print()
    print(f"{'sl':>3} {'zn':>5} | {'donor maxY':>10} {'donor |X|':>9} "
          f"| {'T p50':>7} {'T p90':>7} {'T p99':>7} {'T max':>7} "
          f"| {'Y gain':>7} {'X gain':>7}")
    print("-" * 96)

    for i in range(N):
        ds = V[slice_index(V) == i]
        ts = T[ti == i]
        if not len(ds):
            continue
        zn = (lo[2] + (hi[2] - lo[2]) * (i + 0.5) / N)
        zn = (zn - lo[2]) / span[2]
        dmaxy = ds[:, 1].max()
        dxw = np.abs(ds[:, 0]).max()
        if not len(ts):
            print(f"{i:>3} {zn:>5.2f} | {dmaxy:>10.3f} {dxw:>9.3f} |  (no target points)")
            continue
        ty = ts[:, 1]
        p50, p90, p99 = (np.percentile(ty, q) for q in (50, 90, args.top_pct))
        tmax = ty.max()
        txw = np.percentile(np.abs(ts[:, 0]), 99.0)
        ygain = p99 - dmaxy
        xgain = txw / dxw if dxw > 1e-6 else float("nan")
        print(f"{i:>3} {zn:>5.2f} | {dmaxy:>10.3f} {dxw:>9.3f} "
              f"| {p50:>7.3f} {p90:>7.3f} {p99:>7.3f} {tmax:>7.3f} "
              f"| {ygain:>+7.3f} {xgain:>7.3f}")

    ty = T[:, 1]
    print()
    print(f"target Y percentiles overall: "
          + "  ".join(f"p{q}={np.percentile(ty, q):.3f}" for q in (1, 25, 50, 75, 90, 99, 100)))
    print(f"target X |extent| overall:   "
          + "  ".join(f"p{q}={np.percentile(np.abs(T[:, 0]), q):.3f}"
                      for q in (50, 90, 99, 100)))
    print()
    print("If T max is much larger than T p99 in the rear slices, the excess is the")
    print("fins/aerials and the roofline is being fitted to a fin. Fit p90 or the")
    print("silhouette of the BODY, not the max of everything in the slice.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
