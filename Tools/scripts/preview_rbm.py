"""preview_rbm.py - software-render an RBM to PNG, so appearance can be judged without launching JC3.

Why this exists: the only oracle for a material build used to be "install it and drive". A screenshot
then answers several questions at once and answers none of them separately. This renders the staged
RBM directly - orthographic, z-buffered, one flat colour per material block - so geometry errors
(holes, inverted winding, misplaced parts) and material assignment (which block owns which panels) are
visible in seconds, offline, before any deploy.

    python Tools/scripts/preview_rbm.py Working/Appearance/build/body_lod1.rbm -o Working/Appearance/diag
    python Tools/scripts/preview_rbm.py <file.rbm> --view side --shade material --size 1200
    python Tools/scripts/preview_rbm.py <file.rbm> --albedo Working/Appearance/build/ddsc

`--albedo DIR` is the honest preview: each block is tinted with the mean colour of its own diffuse
.ddsc (exported with Gibbed's ConvertTexture), so a too-dark or missing albedo shows up as a too-dark
or flat car - the failure mode that shipped as test-078, where the body was byte 14 instead of 67.

Views are engine axes: X = width (right), Y = up, Z = length (front positive).
`--shade material` colours every block differently (stable palette by block index);
`--shade normal` is a plain lambert render, for judging shape alone.
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rbm_geom as R  # noqa: E402

CONVERT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "Gibbed", "Gibbed.JustCause3.ConvertTexture.exe")


def ddsc_mean(path):
    """mean sRGB of a .ddsc, by exporting it with Gibbed and reading the DDS. Cached per process."""
    if path in _MEAN_CACHE:
        return _MEAN_CACHE[path]
    out = None
    if os.path.exists(CONVERT):
        with tempfile.TemporaryDirectory() as td:
            shutil.copy(path, os.path.join(td, "t.ddsc"))
            subprocess.run([CONVERT, "t.ddsc"], cwd=td, capture_output=True)
            dds = glob.glob(os.path.join(td, "*.dds"))
            if dds:
                im = Image.open(dds[0]).convert("RGB")
                out = (np.asarray(im, np.float32) / 255.0).reshape(-1, 3).mean(0)
    _MEAN_CACHE[path] = out
    return out


_MEAN_CACHE = {}

# stable, high-contrast palette: block 0 always the same colour across builds
PALETTE = np.array([
    [0.85, 0.20, 0.20], [0.20, 0.55, 0.90], [0.95, 0.75, 0.15], [0.25, 0.75, 0.35],
    [0.75, 0.30, 0.85], [0.95, 0.50, 0.15], [0.20, 0.80, 0.85], [0.85, 0.45, 0.65],
    [0.55, 0.55, 0.20], [0.35, 0.35, 0.85], [0.70, 0.70, 0.70], [0.95, 0.95, 0.55],
    [0.45, 0.85, 0.65], [0.85, 0.65, 0.45], [0.60, 0.75, 0.95], [0.95, 0.35, 0.55],
    [0.50, 0.85, 0.30], [0.30, 0.45, 0.60], [0.80, 0.80, 0.40],
], dtype=np.float32)


def block_triangles(b):
    """(n,3,3) world-space triangles for one block. Positions live in vb0's first float3."""
    pos = np.frombuffer(b.vb0.data, dtype=np.float32).reshape(-1, b.vb0.stride // 4)[:, :3]
    idx = np.frombuffer(b.ib.data, dtype=np.uint16).reshape(-1, 3).astype(np.int64)
    idx = idx[(idx < len(pos)).all(1)]
    return pos[idx]


def render(tris, colours, view, size, light):
    # screen axes + depth axis per view
    ax = {"side": (2, 1, 0), "front": (0, 1, 2), "top": (2, 0, 1)}[view]
    P = tris[:, :, list(ax[:2])]
    D = tris[:, :, ax[2]]
    lo = P.reshape(-1, 2).min(0)
    hi = P.reshape(-1, 2).max(0)
    span = float((hi - lo).max()) or 1.0
    scale = (size - 40) / span
    W = int((hi[0] - lo[0]) * scale) + 40
    H = int((hi[1] - lo[1]) * scale) + 40
    Q = (P - lo) * scale + 20
    Q[:, :, 1] = H - Q[:, :, 1]                      # screen y points down

    # face normals in world space, for shading only
    e1 = tris[:, 1] - tris[:, 0]
    e2 = tris[:, 2] - tris[:, 0]
    n = np.cross(e1, e2)
    ln = np.linalg.norm(n, axis=1)
    keep = ln > 1e-9
    n = n[keep] / ln[keep, None]
    tris, Q, D, colours = tris[keep], Q[keep], D[keep], colours[keep]

    lam = np.abs(n @ np.asarray(light, np.float32))
    shade = 0.28 + 0.72 * lam
    rgb = np.clip(colours * shade[:, None], 0, 1)

    img = np.zeros((H, W, 3), np.float32)
    zbuf = np.full((H, W), -np.inf, np.float32)
    order = np.argsort(-D.mean(1))                   # far first (painter's, z-buffer decides)
    for t in order:
        (x0, y0), (x1, y1), (x2, y2) = Q[t]
        z0, z1, z2 = D[t]
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
        if not inside.any():
            continue
        z = a * z0 + b * z1 + c * z2
        sub = zbuf[miny:maxy + 1, minx:maxx + 1]
        win = inside & (z > sub)
        if not win.any():
            continue
        sub[win] = z[win]
        img[miny:maxy + 1, minx:maxx + 1][win] = rgb[t]
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)), (W, H)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rbm")
    ap.add_argument("-o", "--out-dir", default="Working/Appearance/diag")
    ap.add_argument("--view", choices=["side", "front", "top", "all"], default="all")
    ap.add_argument("--shade", choices=["material", "normal"], default="material")
    ap.add_argument("--size", type=int, default=1000)
    ap.add_argument("--albedo", metavar="DIR",
                    help="tint each block by the mean of its own dif .ddsc found in DIR")
    ap.add_argument("--json", help="also dump per-block tri counts and bboxes")
    a = ap.parse_args()

    m = R.decode(open(a.rbm, "rb").read())
    views = ["side", "front", "top"] if a.view == "all" else [a.view]
    total = 0
    for view in views:
        all_t, all_c = [], []
        for i, b in enumerate(m.blocks):
            t = block_triangles(b)
            if not len(t):
                continue
            total += len(t)
            if a.albedo:
                dif = (getattr(b, "textures", None) or [None])[0]
                p = os.path.join(a.albedo, os.path.basename(dif)) if dif else None
                m = ddsc_mean(p) if p and os.path.exists(p) else None
                col = (m if m is not None else np.array([0.55, 0.55, 0.55], np.float32))
                col = np.clip(col * 1.35, 0, 1)          # rough daylight lift, not a lighting model
            else:
                col = (PALETTE[i % len(PALETTE)] if a.shade == "material"
                       else np.array([0.72, 0.74, 0.78], np.float32))
            all_t.append(t)
            all_c.append(np.repeat(col[None], len(t), 0))
        T = np.concatenate(all_t)
        C = np.concatenate(all_c)
        img, (w, h) = render(T, C, view, a.size, light=(0.45, 0.8, -0.55) if view == "top" else (0.3, 0.85, -0.45))
        os.makedirs(a.out_dir, exist_ok=True)
        stem = os.path.splitext(os.path.basename(a.rbm))[0]
        p = os.path.join(a.out_dir, f"{stem}_{view}.png")
        img.save(p)
        print(f"{p}  {w}x{h}  {len(T):,} tris")

    if a.json:
        info = {"blocks": [{"i": i, "type": R.BLOCK_NAMES.get(b.type_hash, hex(b.type_hash)),
                            "tris": len(block_triangles(b)),
                            "albedo": (ddsc_mean(os.path.join(a.albedo, os.path.basename(b.textures[0])))
                                       .round(3).tolist()
                                       if a.albedo and b.textures and os.path.exists(
                                           os.path.join(a.albedo, os.path.basename(b.textures[0]))) else None),
                            "textures": list(getattr(b, "textures", []) or [])}
                           for i, b in enumerate(m.blocks)]}
        json.dump(info, open(a.json, "w"), indent=1)
        print("block inventory ->", a.json)


if __name__ == "__main__":
    main()
