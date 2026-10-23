"""Layout report for any PSKX vehicle source: per-material face counts, centroids
and bboxes (PSK + JC3 frames), wheel-station table from the wheel materials
clustered into 4 corners, and the wheelbase/track ratios that pin body fit and
hardpoint placement. The user's "loop": alignment numbers out of the asset, no
hand-tuned builds. Usage: python _pskx_layout.py <file.pskx> [--wheel-mats ...]
"""
import sys

import numpy as np

sys.path.insert(0, "Tools/scripts")
from psk2rbm import read_pskx, to_jc3  # noqa: E402


def main():
    args = sys.argv[1:]
    path = args[0]
    subs = (args[1].split(",") if len(args) > 1 else
            ["Wheel_V2", "Tyre", "Discbreak"])
    P, W, F, mats = read_pskx(path)
    print("== %s: %d points %d faces %d materials" % (path, len(P), len(F), len(mats)))
    pos = P[W["p"].astype(int)]
    print("-- per-material (faces, centroid PSK XYZ, bbox LxWxH):")
    for i, nm in enumerate(mats):
        sel = np.where(F["m"] == i)[0]
        if not len(sel):
            continue
        pts = pos[F["w"][sel]].reshape(-1, 3)
        print("  %6d %-38s c=(%7.1f,%7.1f,%6.1f) lxwxh=%.1fx%.1fx%.1f" % (
            len(sel), nm, *pts.mean(0),
            *(pts.max(0) - pts.min(0))))
    wm = [i for i in range(len(F))
          if any(s in mats[int(F["m"][i])] for s in subs)]
    cen = pos[F["w"][wm]].mean(1)
    mx, my = np.median(cen[:, 0]), np.median(cen[:, 1])
    print("-- wheel stations (PSK frame: X=length prow+, Y=width, Z=up):")
    st = {}
    for qx in (0, 1):
        for qy in (0, 1):
            s = np.array([c for c in cen
                          if (c[0] > mx) == qx and (c[1] > my) == qy])
            st[(qx, qy)] = s.mean(0)
            print("  corner X%s Y%s  n=%5d  (%7.1f, %7.1f, %6.1f)" % (
                ">med" if qx else "<=med", ">med" if qy else "<=med",
                len(s), *s.mean(0)))
    xs = sorted(v[0] for v in st.values())
    ys = sorted(v[1] for v in st.values())
    L, Wd = P[:, 0].max() - P[:, 0].min(), P[:, 1].max() - P[:, 1].min()
    print("-- wheelbase %.1f / length %.1f = %.3f" % (xs[-1] - xs[0], L, (xs[-1] - xs[0]) / L))
    print("-- track %.1f / width %.1f = %.3f" % (ys[-1] - ys[0], Wd, (ys[-1] - ys[0]) / Wd))


main()
