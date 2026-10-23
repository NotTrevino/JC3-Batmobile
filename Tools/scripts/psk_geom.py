#!/usr/bin/env python3
"""
psk_geom.py - extract and inspect the geometry of a Source-engine PSK/PSKX mesh.

Why
---
`psk_bounds.py` already proved the Batmobile's bounding box, but a bounding box is
not a shape. The reshape that is being attempted here is a TOPOLOGY-PRESERVING one:
the JC3 engine rejects any edit that changes a vertex or index count (test-018,
test-019), so the only thing that can be done to the donor car is MOVE ITS EXISTING
1024 VERTICES. To know where they ought to go, the target's actual surface is needed,
not a remembered impression of what a Tumbler looks like -- `AGENTS.md` forbids
treating pretrained knowledge as evidence.

Two things this adds over psk_bounds.py:

  1. `stats` / `dump`  - the whole VPoint array as a float64 (N,3) cloud, cached.
  2. `preview`          - a point-cloud SIDE/TOP/FRONT render.

`preview` exists because the PSK's axis mapping was recorded in MODLOG as
"reasoned inference, not proven": the note reasoned that X must be length because
the alternative reading makes the car twice as wide as it is long. That reasoning is
plausible but it is not evidence, and every millimetre of the eventual carve depends
on it. Rendering the cloud and looking at it settles it in one image.

Why a point cloud and not the triangle renderer
----------------------------------------------
`rbm_geom._shade` rasterises triangle by triangle in a Python loop. That is fine for
a 1,024-vertex render block and hopeless for ~200,000. A z-buffered splat of the
vertices is pure numpy, and for reading a SILHOUETTE -- the only thing a frozen-
topology reshape can actually change -- it is the better tool anyway.

Usage:
    python psk_geom.py stats    <file.pskx> [...]
    python psk_geom.py preview  <file.pskx> -o out.png [--size 900]
    python psk_geom.py dump     <file.pskx> -o cloud.npz
"""

from __future__ import annotations

import argparse
import os
import struct
import sys


class PskError(Exception):
    pass


# ---------------------------------------------------------------------------
# reading
# ---------------------------------------------------------------------------

# Chunked container, solved from the actual bytes of Batmobile_V2.pskx.
#
# A plain Source PSK starts with char[20] flags then int32 counts, which is what
# `psk_bounds.py` assumes. This file is NOT that: it opens with the 8-byte magic
# "ACTRHEAD", and reading it as a flat PSK yields numVertex = 20100482, i.e. the
# low 4 bytes of the root chunk's 8-byte size field. Measured layout:
#
#   0x00  "ACTRHEAD"        id[8]
#   0x08  version[16]       zero-filled here
#   0x18  u64               = 0 in this file
#   0x20  "PNTS0000"        id[8]  (id "PNTS", version "0000")
#   0x28  version[16]       "0000" + zero fill
#   0x38  u32 stride        = 12
#   0x3c  u32 count         = 201338
#   0x40  float3[count]
#
# Both chunks are 32 bytes of header. Only those two chunks exist: a scan of the
# whole 17.4 MB file for 4-character all-caps ids finds nothing but the float data
# coincidentally looking like ASCII. So there are NO triangles in this file, which is
# why every command here works on a point cloud and why the renderer is a splat.
CHUNK_ID = b"PNTS"
PNTS_HEADER = 32


def read_verts(path: str):
    """Return (verts float64 (N,3), info dict). Locates the PNTS chunk by signature."""
    import numpy as np

    size = os.path.getsize(path)
    with open(path, "rb") as fh:
        blob = fh.read()
    off = blob.find(CHUNK_ID)
    if off < 0:
        raise PskError(f"no {CHUNK_ID.decode()} chunk found -- not a chunked PSKX")
    if off + PNTS_HEADER > size:
        raise PskError(f"{CHUNK_ID.decode()} chunk header runs past EOF at {off}")
    stride, count = struct.unpack_from("<2I", blob, off + 24)
    if stride != 12:
        raise PskError(f"VPoint stride is {stride}, expected 12")
    if count == 0 or count > 20_000_000:
        raise PskError(f"implausible PNTS count={count}")
    start = off + PNTS_HEADER
    if start + count * stride > size:
        raise PskError(f"PNTS payload runs past EOF: need {count*stride} at {start}, file is {size}")
    V = np.frombuffer(blob, dtype="<f4", count=count * 3, offset=start)
    V = V.reshape(count, 3).astype(np.float64)
    return V, {"num_vertex": count, "stride": stride, "chunk_offset": off,
               "num_triangles": 0, "file_size": size}


def read_tris(path: str):
    """Always empty: this container carries no triangle chunk (see CHUNK_ID note)."""
    import numpy as np

    return np.zeros((0, 3), dtype=np.int64), read_verts(path)[1]


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------

# Same view convention as rbm_geom.VIEWS (ha, va, cam) = (axis across the frame, axis up
# the frame, axis the camera looks down), so a PSK preview and an RBM preview can be put
# side by side and compared without thinking about it:
#   side  = length across, height up, camera on width
#   top   = length across, width up,   camera on height
#   front = width across,  height up,  camera on length
VIEWS = {
    "side":  (2, 1, 0),
    "top":   (2, 0, 1),
    "front": (0, 1, 2),
}


def splat(V, view: str, size: int, axis_map=None, axes=None):
    """Z-buffered point splat. Returns (img uint8 (size,size,3), filled pixel count).

    `axis_map` permutes the file's three axes into JC3's (width, up, length) = (X, Y, Z)
    before the view is chosen, so a Batmobile render and a donor RBM render can be
    stacked and compared directly. `axes` bypasses that and gives (h, v, cam) straight.
    """
    import numpy as np

    Pv = V[:, axis_map] if axis_map is not None else V
    ha, va, cam = axes if axes is not None else VIEWS[view]

    P = np.stack([Pv[:, ha], Pv[:, va]], axis=1)
    lo, hi = P.min(axis=0), P.max(axis=0)
    span = (hi - lo).max() or 1.0
    s = (size - 4) / span
    mid = (lo + hi) / 2.0
    px = (P[:, 0] - mid[0]) * s + size / 2.0
    py = size / 2.0 - (P[:, 1] - mid[1]) * s

    ix = np.rint(px).astype(np.int64)
    iy = np.rint(py).astype(np.int64)
    keep = (ix >= 0) & (ix < size) & (iy >= 0) & (iy < size)
    ix, iy = ix[keep], iy[keep]
    depthv = Pv[keep, cam]

    zbuf = np.full((size, size), np.nan)
    # a point wins its pixel if it is nearer than what is already there; "nearer"
    # is measured away from the cloud centre so the sign is right from either side
    ref = np.median(Pv[:, cam])
    order = np.argsort(-np.sign(depthv - ref) * np.abs(depthv - ref))
    zbuf[iy[order], ix[order]] = depthv[order]

    hit = np.isfinite(zbuf)
    img = np.full((size, size, 3), 255.0)
    if hit.any():
        d = zbuf[hit]
        lo_d, hi_d = d.min(), d.max()
        t = (d - lo_d) / (hi_d - lo_d if hi_d > lo_d else 1.0)
        lum = 0.25 + 0.75 * np.clip(t, 0.0, 1.0)
        base = np.array([0.55, 0.58, 0.64])
        img[hit] = base * lum[:, None] * 255.0
    return np.clip(img, 0, 255).astype(np.uint8), int(hit.sum())


def render_sheet(V, out: str, size: int = 900, axis_map=None, title: str = "") -> str:
    import numpy as np
    from PIL import Image

    views = ("side", "top", "front")
    panels = [splat(V, v, size, axis_map=axis_map)[0] for v in views]

    lo, hi = V.min(axis=0), V.max(axis=0)
    caption = (f"{title}   W(x) x H(y) x L(z) = {hi[0]-lo[0]:.2f} x {hi[1]-lo[1]:.2f} "
               f"x {hi[2]-lo[2]:.2f} source units   (n={len(V)})")
    gap = 10
    band = 26
    W = len(views) * size + (len(views) + 1) * gap
    H = size + band + 2 * gap
    canvas = np.full((H, W, 3), 238, dtype=np.uint8)
    for i, img in enumerate(panels):
        x0 = gap + i * (size + gap)
        y0 = gap + band
        canvas[y0:y0 + size, x0:x0 + size] = img
    im = Image.fromarray(canvas)
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    for i, v in enumerate(views):
        d.text((gap + i * (size + gap) + 6, gap + 6), v.upper(), fill=(20, 20, 20))
    d.text((gap, gap + band - 10), caption, fill=(20, 20, 20))
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    im.save(out)
    return out


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------

def cmd_stats(args) -> int:
    import numpy as np

    for p in args.files:
        try:
            V, h = read_verts(p)
        except (OSError, PskError) as e:
            print(f"{p}: ERROR {e}", file=sys.stderr)
            continue
        lo, hi = V.min(axis=0), V.max(axis=0)
        w, hh, d = hi - lo
        print(p)
        print(f"  verts={h['num_vertex']}  tris={h['num_triangles']} (no triangle chunk)  "
              f"PNTS at 0x{h['chunk_offset']:X}, stride {h['stride']}")
        print(f"  min = [{lo[0]:.4f}, {lo[1]:.4f}, {lo[2]:.4f}]")
        print(f"  max = [{hi[0]:.4f}, {hi[1]:.4f}, {hi[2]:.4f}]")
        print(f"  axis extents  X {w:.4f}   Y {hh:.4f}   Z {d:.4f}")
        longest = int(np.argmax([w, hh, d]))
        print(f"  longest axis: {'XYZ'[longest]}")
        print(f"  ratios to longest: " + "  ".join(
            f"{a}={v/max(w, hh, d):.4f}" for a, v in zip("XYZ", (w, hh, d))))
    return 0


def cmd_preview(args) -> int:
    V, h = read_verts(args.input)
    # --as-axes permutes the file's axes into JC3's (width, up, length). The default
    # is identity, i.e. "assume the file already uses JC3 axes", which is exactly the
    # assumption that has to be tested rather than assumed.
    axis_map = [int(c) for c in args.as_axes] if args.as_axes else None
    out = render_sheet(V, args.output, size=args.size, axis_map=axis_map,
                       title=os.path.basename(args.input))
    lo, hi = V.min(axis=0), V.max(axis=0)
    print(f"{args.input}: {h['num_vertex']} verts, {h['num_triangles']} tris")
    print(f"  axis extents  X {hi[0]-lo[0]:.4f}   Y {hi[1]-lo[1]:.4f}   Z {hi[2]-lo[2]:.4f}")
    print(f"  rendered with as_axes={axis_map or 'identity'}")
    print(f"wrote {out}")
    return 0


def cmd_dump(args) -> int:
    import numpy as np

    V, h = read_verts(args.input)
    T, _ = read_tris(args.input) if args.with_tris else (np.zeros((0, 3), dtype=np.int64), h)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
    np.savez_compressed(args.output, verts=V, tris=T, num_vertex=h["num_vertex"],
                        num_triangles=h["num_triangles"])
    print(f"{args.input}: wrote {args.output}  verts={V.shape} tris={T.shape}")
    return 0


def cmd_load(args) -> int:
    """Render from a cached .npz produced by `dump`, for quick iteration."""
    import numpy as np

    z = np.load(args.cache)
    V = z["verts"]
    axis_map = [int(c) for c in args.as_axes] if args.as_axes else None
    out = render_sheet(V, args.output, size=args.size, axis_map=axis_map,
                       title=os.path.basename(args.cache))
    print(f"{args.cache}: {V.shape[0]} verts  wrote {out}")
    return 0


def cmd_grid(args) -> int:
    """Render all nine (horizontal axis, vertical axis) pairs.

    Ratios alone cannot tell width from height -- 349 and 234 are both plausible for
    either. Laying out every ordered pair and looking at it settles it in one image:
    only one row can show a recognisable car's side elevation, which is what proves
    which of the two remaining axes is length.
    """
    import numpy as np
    from PIL import Image, ImageDraw

    V, h = read_verts(args.input)
    size = args.size
    gap, band = 6, 20
    canvas = np.full((3 * size + 4 * gap + band, 3 * size + 4 * gap, 3), 238, dtype=np.uint8)
    for r in range(3):
        for c in range(3):
            if r == c:
                continue
            cam = 3 - r - c                       # the axis that is neither
            img, _ = splat(V, None, size, axes=(c, r, cam))
            x0 = gap + c * (size + gap)
            y0 = gap + band + r * (size + gap)
            canvas[y0:y0 + size, x0:x0 + size] = img
    im = Image.fromarray(canvas)
    d = ImageDraw.Draw(im)
    d.text((gap, 4), "rows = vertical axis (XYZ),  columns = horizontal axis (XYZ),  "
                     "camera on the third axis", fill=(0, 0, 0))
    os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
    im.save(args.output)
    print(f"{args.input}: {h['num_vertex']} verts")
    lo, hi = V.min(axis=0), V.max(axis=0)
    for k, a in enumerate("XYZ"):
        print(f"  {a}: {lo[k]:10.3f} .. {hi[k]:10.3f}   extent {hi[k]-lo[k]:9.3f}")
    print(f"wrote {args.output}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("stats", help="per-axis extents and ratios")
    p.add_argument("files", nargs="+")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("preview", help="SIDE/TOP/FRONT point-cloud render")
    p.add_argument("input")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--size", type=int, default=900)
    p.add_argument("--as-axes", nargs=3, metavar=("W", "U", "L"),
                   help="permute the file's axes into JC3 width/up/length, e.g. --as-axes 2 1 0")
    p.set_defaults(func=cmd_preview)

    p = sub.add_parser("dump", help="cache vertices (+ triangles) to .npz")
    p.add_argument("input")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--with-tris", action="store_true")
    p.set_defaults(func=cmd_dump)

    p = sub.add_parser("load", help="render from a cached .npz")
    p.add_argument("cache")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--size", type=int, default=900)
    p.add_argument("--as-axes", nargs=3, metavar=("W", "U", "L"))
    p.set_defaults(func=cmd_load)

    p = sub.add_parser("grid", help="all nine (horizontal, vertical) axis pairs")
    p.add_argument("input")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--size", type=int, default=700)
    p.set_defaults(func=cmd_grid)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
