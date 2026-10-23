#!/usr/bin/env python3
"""
psk_bounds.py - measure a Source-engine PSK/PSKX mesh's bounding box.

Why
---
`AGENTS.md` forbids treating pretrained knowledge as evidence, so "a Batmobile is
about 4.5 m long" is not an acceptable input. The PSKX stores raw vertex
positions, so the real dimensions can be measured instead of recalled.

PSK layout (Source engine, 32-bit little-endian):
    char[20] flags
    int32   numVertex, numTriangles, numBones, numMaterials, numLODGroups
    int32   animBytes
    int32   pad[2]
    VBlock  numVertex * 32   (float3 boneIndex, float3 pos, float2 uv, int32 pad)
    VPoint  numVertex * 12   (float3 position)   <-- what we want
    FBlock  numTriangles * 12

PSKX appends extra LOD groups after the base mesh, which we skip.

Usage:
    python psk_bounds.py <file.pskx> [...]
"""

from __future__ import annotations

import struct
import sys


class PskError(Exception):
    pass


def read_bounds(path: str) -> dict:
    with open(path, "rb") as fh:
        flags = fh.read(20)
        # numVertex, numTriangles, numBones, numMaterials, numLODGroups,
        # animBytes, then int32 pad[2]  -> 8 ints = 32 bytes
        hdr = struct.unpack("<8i", fh.read(32))
        num_vertex, num_tri, num_bones, num_mat, num_lod, anim_bytes = hdr[:6]

        if num_vertex <= 0 or num_vertex > 20_000_000:
            raise PskError(f"implausible numVertex={num_vertex}")

        fh.seek(num_vertex * 32, 1)          # skip VBlock
        raw = fh.read(num_vertex * 12)       # VPoint
        if len(raw) != num_vertex * 12:
            raise PskError("truncated VPoint")

        xs, ys, zs = [], [], []
        for i in range(num_vertex):
            x, y, z = struct.unpack_from("<3f", raw, i * 12)
            xs.append(x); ys.append(y); zs.append(z)

    if not xs:
        raise PskError("no vertices")
    return {
        "flags": flags.split(b"\x00")[0].decode("ascii", "replace"),
        "num_vertex": num_vertex,
        "num_triangles": num_tri,
        "num_bones": num_bones,
        "num_materials": num_mat,
        "num_lod_groups": num_lod,
        "min": (min(xs), min(ys), min(zs)),
        "max": (max(xs), max(ys), max(zs)),
    }


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    for p in argv:
        try:
            r = read_bounds(p)
        except (OSError, PskError) as e:
            print(f"{p}: ERROR {e}", file=sys.stderr)
            continue
        w = r["max"][0] - r["min"][0]
        h = r["max"][1] - r["min"][1]
        d = r["max"][2] - r["min"][2]
        print(f"{p}")
        print(f"  flags={r['flags']}  verts={r['num_vertex']}  tris={r['num_triangles']}  "
              f"bones={r['num_bones']}  mats={r['num_materials']}  lods={r['num_lod_groups']}")
        print(f"  min = [{r['min'][0]:.4f}, {r['min'][1]:.4f}, {r['min'][2]:.4f}]")
        print(f"  max = [{r['max'][0]:.4f}, {r['max'][1]:.4f}, {r['max'][2]:.4f}]")
        print(f"  W x H x L = {w:.4f} x {h:.4f} x {d:.4f}   (source units)")
        print(f"  W x H x L / 2.54 = {w/2.54:.2f} x {h/2.54:.2f} x {d/2.54:.2f} in")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))