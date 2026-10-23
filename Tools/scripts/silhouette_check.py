"""silhouette_check.py - how much of the SOURCE body silhouette does a decimated body_lod1 keep?

Why this exists: BUD-1's oracle is "decimation holes drop below 0.3% of the silhouette (today
1.01%)". A hole is a pixel the full-resolution source covers and our decimated RBM does not, in the
SAME orthographic frame - so the number is a geometry fact, not a screenshot judgement.

    python Tools/scripts/silhouette_check.py Working/Appearance/build/body_lod1.rbm

Source: the NON-WHEEL body of Batmobile_V2.pskx - the same bone classification bat_assemble uses to
split body from wheels (classify -> round parts -> the N largest anchor the wheels -> other round
parts inside a wheel join it), through the same transform (to_jc3_rot, scale 0.01). The face count
is asserted against the 214,737 body faces MODLOG #106 measured, so the split cannot silently
diverge from the build's. The frame is FIXED (source bbox + 2% margin, side view), so two builds
measured against the same source are directly comparable pixel for pixel.

Reports: source/ours silhouette pixels, coverage, holes (source has, we don't) and extra (we have,
source doesn't) as % of the source silhouette, plus the boundary-edge share of each mesh.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import psk2rbm as P            # noqa: E402
import pskx_parts as PX        # noqa: E402
import rbm_geom as R           # noqa: E402
import preview_rbm as PR       # noqa: E402
from bat_assemble import to_jc3_rot  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PSKX = os.path.join(ROOT, "Working", "Appearance", "grab", "Playable_Batmobile_SF",
                    "SkeletalMesh3", "Batmobile_V2.pskx")
# the build's own body split (Working/Appearance/build/pipeline.log: "wheel faces outside their
# tyre circle -> body: 1396"). MODLOG #106 quoted 214,737 from a one-off script; this script runs
# bat_assemble's exact classification and gets 215,893, so it asserts against the build's number.
BODY_FACES = 215_893


def body_tris(Pp, W, F, scale=0.01, nwheels=4):
    """the non-wheel body TRIANGLES (coordinates), exactly as bat_assemble.main() splits them:
    classify -> round parts -> the N largest anchor the wheels -> other round parts inside a wheel
    join it -> faces weighted to a wheel but beyond the tyre radius return to the static body."""
    Vw = to_jc3_rot(Pp[W["p"]]) * scale
    tris = F["w"].astype(np.int64)
    bones, Wt = PX.skeleton(PSKX)
    fb = PX.face_bones(Pp, W, F, Wt, len(bones))
    cl = PX.classify(Vw, tris, fb, len(bones))
    round_b = [b for b, (k, _n, _info) in cl.items() if k == "spinning"]
    size = lambda b: max(cl[b][2][3], cl[b][2][4])
    anchors = sorted(round_b, key=size, reverse=True)[:nwheels]
    if len(anchors) != nwheels:
        raise SystemExit(f"found {len(anchors)} round parts for {nwheels} wheels")
    cz = np.median([cl[b][2][0][2] for b in anchors])
    corner = {b: ("f" if cl[b][2][0][2] < cz else "r") + "_" + ("l" if cl[b][2][0][0] < 0 else "r")
              for b in anchors}
    wheel_of = dict(corner)
    for b in round_b:                                    # attach other round parts INSIDE a wheel
        if b in wheel_of:
            continue
        c = cl[b][2][0]
        for ab in anchors:
            ac, r = cl[ab][2][0], size(ab) / 2
            if np.sign(c[0]) == np.sign(ac[0]) and np.linalg.norm(c[1:] - ac[1:]) < r and size(b) <= 2 * r:
                wheel_of[b] = corner[ab]
    part = np.array(["body"] * len(F), dtype=object)
    for b, c in wheel_of.items():
        part[fb == b] = "wheel_" + c
    # hub-radius correction: nothing outside the tyre's own circle can spin with it (MODLOG #70)
    hubs = {}
    for c in sorted({v for v in wheel_of.values()}):
        bs = [b for b, cc in wheel_of.items() if cc == c and size(b) >= 0.8 * max(size(x) for x in anchors)]
        tb = min(bs, key=lambda b: cl[b][2][2])
        pts = Vw[np.unique(tris[fb == tb])]          # tyre vertices only, as in main()
        lo, hi = pts.min(0), pts.max(0)
        hubs[c] = ((lo + hi) / 2, (hi[1] - lo[1]) / 2)
    cen = Vw[tris].mean(1)
    for c, (ctr, rad) in hubs.items():
        sel = part == "wheel_" + c
        d = np.linalg.norm(cen[:, 1:] - ctr[1:], axis=1)
        part[sel & (d > 1.03 * rad)] = "body"
    return Vw[tris[part == "body"]]


def rasterize(tris, lo, hi, size):
    """boolean coverage mask of tris in the fixed frame (side view: screen x = Z, y = Y)."""
    P2 = tris[:, :, [2, 1]]
    span = float((hi - lo).max()) or 1.0
    scale = (size - 40) / span
    W = int((hi[0] - lo[0]) * scale) + 40
    H = int((hi[1] - lo[1]) * scale) + 40
    Q = (P2 - lo) * scale + 20
    Q[:, :, 1] = H - Q[:, :, 1]
    mask = np.zeros((H, W), bool)
    for t in range(len(Q)):
        (x0, y0), (x1, y1), (x2, y2) = Q[t]
        minx, maxx = int(max(0, min(x0, x1, x2))), int(min(W - 1, max(x0, x1, x2)))
        miny, maxy = int(max(0, min(y0, y1, y2))), int(min(H - 1, max(y0, y1, y2)))
        if maxx < minx or maxy < miny:
            continue
        ys, xs = np.mgrid[miny:maxy + 1, minx:maxx + 1]
        den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(den) < 1e-9:
            continue
        a = ((y1 - y2) * (xs - x2) + (x2 - x1) * (ys - y2)) / den
        b = ((y2 - y0) * (xs - x2) + (x0 - x2) * (ys - y2)) / den
        c = 1 - a - b
        inside = (a >= -1e-6) & (b >= -1e-6) & (c >= -1e-6)
        if inside.any():
            mask[miny:maxy + 1, minx:maxx + 1] |= inside
    return mask


def erode(mask, r):
    """binary erosion by a (2r+1) square, no scipy."""
    H, W = mask.shape
    out = np.ones_like(mask)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            sub = np.zeros_like(mask)
            y0, y1 = max(0, dy), min(H, H + dy)
            x0, x1 = max(0, dx), min(W, W + dx)
            sub[y0 - dy:y1 - dy, x0 - dx:x1 - dx] = mask[y0:y1, x0:x1]
            out &= sub
    return out


def boundary_share(tris):
    """fraction of edges used by exactly one triangle (open borders tear first)."""
    e = np.concatenate([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]).astype(np.int64)
    e = np.sort(e, axis=1)
    _, cnt = np.unique(e, axis=0, return_counts=True)
    return float((cnt == 1).sum()) / len(cnt)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rbm", help="the decimated body lod1 to measure")
    ap.add_argument("--size", type=int, default=2400, help="frame width in px")
    ap.add_argument("--save", metavar="DIR", help="write source/ours/hole masks as PNGs")
    a = ap.parse_args()

    Pp, W, F, _mats = P.read_pskx(PSKX)
    src = body_tris(Pp, W, F)
    if len(src) != BODY_FACES:
        raise SystemExit(f"body split gives {len(src):,} faces, the build's classification gives "
                         f"{BODY_FACES:,} - the split has drifted from the build's")
    # the build translates the car to the vanilla ground/centre (stations.json, written by
    # bat_assemble.main()); the RBM vertices carry it, so the source must too or every edge of
    # every plate shows a shift-induced gap and the tear count means nothing.
    stations = os.path.join(os.path.dirname(os.path.abspath(a.rbm)), "stations.json")
    if os.path.exists(stations):
        off = np.asarray(json.load(open(stations, encoding="utf-8"))["offset"], np.float64)
        src = src + off
        print(f"applied the build's own offset {off.tolist()} to the source")
    ours = np.concatenate([PR.block_triangles(b) for b in R.decode(open(a.rbm, "rb").read()).blocks])
    ours = ours[np.linalg.norm(np.cross(ours[:, 1] - ours[:, 0], ours[:, 2] - ours[:, 0]), axis=1) > 1e-9]

    pts = src.reshape(-1, 3)[:, [2, 1]]
    lo, hi = pts.min(0), pts.max(0)
    m = 0.02 * float((hi - lo).max())
    lo, hi = lo - m, hi + m

    S = rasterize(src, lo, hi, a.size)
    O = rasterize(ours, lo, hi, a.size)
    holes, extra = S & ~O, O & ~S
    # a decimated outline never lands pixel-exact on the source outline, so most raw "holes" are
    # slivers along the OUTSIDE edge. A real decimation tear - the gaps the user sees up close -
    # is a hole at least 3 px INSIDE the source silhouette (between plates, not on the outline).
    tears = holes & erode(S, 3)
    print(f"frame {S.shape[1]}x{S.shape[0]}  source {len(src):,} tris  ours {len(ours):,} tris")
    print(f"silhouette   source {S.sum():,} px   ours {O.sum():,} px   coverage {O.sum() / S.sum():.4f}")
    print(f"holes        {holes.sum():,} px = {100.0 * holes.sum() / S.sum():.3f}% of the source silhouette")
    print(f"of which interior tears (>=3 px inside the outline)  {tears.sum():,} px = "
          f"{100.0 * tears.sum() / S.sum():.3f}%")
    print(f"extra        {extra.sum():,} px = {100.0 * extra.sum() / S.sum():.3f}% of the source silhouette")
    print(f"boundary edges   source {100 * boundary_share(src):.0f}%   ours {100 * boundary_share(ours):.0f}%")
    if a.save:
        os.makedirs(a.save, exist_ok=True)
        for name, M in (("source", S), ("ours", O), ("holes", holes), ("tears", tears)):
            Image.fromarray((M * 255).astype(np.uint8)).save(os.path.join(a.save, f"{name}.png"))
        print(f"masks -> {a.save}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
