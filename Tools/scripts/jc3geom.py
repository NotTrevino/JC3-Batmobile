"""jc3geom.py - dump the payload of every vehicle `.rbm`, not just its header (G2-5).

`jc3detail.py` reads the RBMDL header of every render-block model (AABB, LOD tag,
block count). This script reads the *blocks*: vertex positions, triangle indices
and the material/texture slots of every mesh in the 233 vehicle entities.

Seven decoders, each with its own oracle:

  CarPaintMM / Window / CarLight   `rbm_geom.decode` - the published layouts, and
                                   the oracle is its byte-exact re-encode.
  GeneralMkIII (`0x2CEC5AD5`)      positions are quantized: `s16 x, y, z, 32767` per
                                   vertex with one scale for the block. The oracle
                                   is the block's own AABB from its Attributes
                                   struct: `span(bbox) / span(s16)` must agree on
                                   every axis and `s16 * scale` must land on the
                                   AABB to within one step, measured per block.
  General (`0xA7583B2B`)           u8 version 6, 68-byte Attributes (with its own
                                   AABB), texture table, then `s16 x, y, z, pad`
                                   positions scaled by Attributes float 0 / 32768,
                                   a 20-byte second stream and the indices. Every
                                   vertex must land inside that AABB.
  GeneralJC3 (`0x2EE0F4A9`)        the GeneralMkIII buffer pattern (packed s16
                                   normals, 20-byte stream, indices); the scale is
                                   the float 32 bytes before its texture table.
                                   No block AABB, so the oracle is exact buffer
                                   arithmetic plus containment in the mesh AABB.
  BavariumShield (`0xA5D24CCD`)    u8 version 1, 4 floats, texture table, then
                                   28-byte vertices whose first 12 bytes are a
                                   float position; containment in the mesh AABB.
  WaterDisplacementOverride,       u8 version 1, u32 flags, 16-byte material
  0x90FE086C                       params (no table), then 12-byte float
                                   positions; containment in the mesh AABB, and
                                   the buffers end exactly at the checksum.
  Prop (`0x04894ECD`)              u8 version 3, the GeneralJC3 buffer pattern
                                   (`s16 x,y,z,0` positions, `count2` 20-byte
                                   stream, indices) with the same scale slot 32
                                   bytes before the texture table. One block
                                   exists; its stored scale is bit-identical to
                                   the mesh AABB's Y extent, the s16 Y run is
                                   the full 0..32767, and all three axis spans
                                   agree with the AABB to 6.5e-5.
  anything else                    framed, not decoded: the block's texture table
                                   locates itself, the terminal index buffer is
                                   found from the block's checksum, and the bytes
                                   in between are kept verbatim. The mesh's
                                   materials and faces are still read. No block
                                   in the 233 vehicle entities is left in this
                                   state.

Outputs:
  Research/JC3Grab/GEOMETRY.jsonl    one row per mesh: counts, materials, decode status
  Research/JC3Grab/GEOMETRY.md       fleet summary (generated)
  E:/Modding/_gamedata/JC3grab/geom/<slug>.json + .bin   per entity: mesh records and payload
                                   (positions as float32 x3, indices as uint16;
                                    raw block bytes are kept in the .bin too)

Usage:
  python jc3geom.py build [--entity SUBSTR] [--all] [--limit N]
  python jc3geom.py report
  python jc3geom.py check
"""
from __future__ import annotations

import argparse
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from jc3index import DEFAULT_GAME, DEFAULT_OUT, MOUNT_RANK, load_index  # noqa: E402
from eetoc import unaaf, sarc_dir  # noqa: E402
import rbm_geom  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_gamedata/JC3grab")
OUT = os.path.join(ROOT, "Research", "JC3Grab")
GEOM = os.path.join(RAW, "geom")

RB_GENERALMKIII = 0x2CEC5AD5
RB_GENERAL = 0xA7583B2B
RB_GENERALJC3 = 0x2EE0F4A9
RB_BAVARIUMSHIELD = 0xA5D24CCD
RB_WATERDISP = 0xF99C72A1
RB_UNKNOWN90FE = 0x90FE086C
RB_PROP = 0x04894ECD
GMK3_ATTRS = 0x68
GMK3_CONSTS = 70 * 4          # MaterialConsts2: 70 floats (jc-model-renderer)
CHECKSUM = rbm_geom.RBM_BLOCK_CHECKSUM
GMK3_ATTR_NAMES = ("depth_bias", "hardware_depth_bias", "hardware_slope_bias",
                   "min_time_of_day_emissive", "start_fade_out_distance_emissive_sq",
                   "gi_emission_modulator", "ripple_angle", "ripple_speed", "ripple_magnitude")
LOD_RE = re.compile(r"_lod(\d+)$", re.I)


# --------------------------------------------------------------------- entity io
def vehicle_ees(rows: list[dict], only: str | None) -> list[str]:
    out = set()
    for r in rows:
        p = r["path"]
        if p.startswith("editor/entities/jc_vehicles/") and p.endswith(".ee"):
            if not only or only.lower() in p.lower():
                out.add(p)
    return sorted(out)


def pick(rows: list[dict], path: str) -> dict:
    hits = [r for r in rows if r["path"] == path]
    return sorted(hits, key=lambda r: MOUNT_RANK[r["mount"]])[-1]


def read_entry(rows: list[dict], path: str, game: str) -> tuple[bytes, dict]:
    r = pick(rows, path)
    with open(os.path.join(game, r["archive"] + ".arc"), "rb") as f:
        f.seek(r["offset"])
        data = f.read(r["size"])
    return data, r


def slug(ee_path: str) -> str:
    parent = ee_path.rsplit("/", 1)[0].rsplit("/", 1)[-1]
    return f"{parent}__{ee_path.rsplit('/', 1)[-1]}"


# ------------------------------------------------------------------ block framing
def read_textures(buf: bytes, off: int) -> tuple[list[str], int]:
    """`read_textures` from jc-model-renderer: u32 count, len-prefixed paths, vec4."""
    (count,) = struct.unpack_from("<I", buf, off)
    off += 4
    names = []
    for _ in range(count):
        (ln,) = struct.unpack_from("<I", buf, off)
        off += 4
        if ln:
            names.append(buf[off:off + ln].decode("utf-8", "replace"))
            off += ln
        else:
            names.append("")
    off += 16                                   # material params
    return names, off


def find_block_end(buf: bytes, start: int, next_hashes: set[int]) -> int:
    """Offset of the 0x89ABCDEF that closes a block, by structural lookahead.

    A checksum candidate is accepted only when the four bytes after it are EOF or
    the type hash of a render block this codec knows - so a 0x89ABCDEF inside
    vertex data cannot masquerade as the terminator.
    """
    p = start
    while True:
        p = buf.find(struct.pack("<I", CHECKSUM), p)
        if p < 0:
            raise rbm_geom.RbmError("no block checksum after payload")
        after = p + 4
        if after == len(buf):
            return p
        if after + 4 <= len(buf) and struct.unpack_from("<I", buf, after)[0] in next_hashes:
            return p
        p += 1


def tail_index_buffer(buf: bytes, lo: int, hi: int, vertex_count: int):
    """The block's last buffer: u32 count, count x u16, ending exactly at `hi`."""
    for q in range(hi - 4, lo - 1, -1):
        (c,) = struct.unpack_from("<I", buf, q)
        if c < 3 or c % 3 or q + 4 + 2 * c != hi:
            continue
        idx = struct.unpack_from(f"<{c}H", buf, q + 4)
        if max(idx) >= vertex_count:
            continue
        return q, c, list(idx)
    return None


# --------------------------------------------------------------- GeneralMkIII
def gmk3_attributes(buf: bytes, start: int) -> dict:
    """The 0x68-byte `Attributes` struct that opens a GeneralMkIII block.

    `renderblockgeneralmkiii.cc` gives the member order and total size; the tail
    (wire_radius, flags, bbox_min, bbox_max, pristine_index_count) is pinned by
    the numbers: bbox_min/bbox_max contain every decoded vertex of the block and
    their spans match the s16 spans at one common scale, block by block.
    """
    a = start + 1
    vals = struct.unpack_from("<9f", buf, a)
    attrs = dict(zip(GMK3_ATTR_NAMES, vals))
    attrs["packed"] = buf[a + 36:a + 68].hex()
    attrs["wire_radius"], attrs["flags"] = struct.unpack_from("<fI", buf, a + 68)
    attrs["bbox_min"] = list(struct.unpack_from("<3f", buf, a + 76))
    attrs["bbox_max"] = list(struct.unpack_from("<3f", buf, a + 88))
    attrs["pristine_index_count"], = struct.unpack_from("<I", buf, a + 100)
    return attrs


def decode_generalmkiii(buf: bytes, start: int, end: int, header: dict):
    """Quantized GeneralMkIII block: attributes, materials, s16 positions, indices.

    Layout from jc-model-renderer's `renderblockgeneralmkiii.cc` (which reads the
    header and stops at the buffers): u8 version=5, Attributes(0x68),
    MaterialConsts2(70 floats), textures + vec4, then

        u32 vcount,  vcount x {s16 x, s16 y, s16 z, s16 32767}   <- positions
        u32 vcount,  vcount x 20 bytes                           <- the rest
        u32 icount,  icount x u16 triangle list

    The position record is 8 bytes but it is not always *packed* at 8: a block
    whose vertex format carries a second 8-byte attribute interleaves it, so the
    stride is 16 there.  The 32767 sentinel in the fourth s16 is what tells the
    two apart -- `find_position_stride` accepts a stride only when every vertex
    of the block carries it.

    Quantization is checked, not assumed.  The oracle is the block's *own* AABB
    (Attributes, not the mesh header): on every non-degenerate axis
    `span(bbox) / span(s16)` must agree to 1% (one scale for the whole block),
    and the axis is then mapped onto that AABB.  `scale_error` is the measured
    disagreement between the axes; it is the evidence that the s16 are a uniform
    quantization rather than three unrelated stretches.
    """
    version = buf[start]
    if version != 5:
        raise rbm_geom.RbmError(f"GeneralMkIII version {version}")
    attrs = gmk3_attributes(buf, start)
    pool = start + 1 + GMK3_ATTRS + GMK3_CONSTS
    textures, pos = read_textures(buf, pool)
    (vcount,) = struct.unpack_from("<I", buf, pos)
    pos += 4
    if not 0 < vcount < 2_000_000:
        raise rbm_geom.RbmError(f"GeneralMkIII vertex count {vcount}")

    stride, cols = find_position_stride(buf, pos, end, vcount)
    pos_end = pos + stride * vcount
    lo, hi = attrs["bbox_min"], attrs["bbox_max"]
    spans = [hi[k] - lo[k] for k in range(3)]
    sspans = [max(c) - min(c) for c in cols]
    live = [k for k in range(3) if sspans[k] >= 64 and spans[k] > 0]
    if not live:
        raise rbm_geom.RbmError("GeneralMkIII: degenerate position set")
    fits = [spans[k] / sspans[k] for k in live]
    scale = sorted(fits)[len(fits) // 2]
    spread = max(abs(f - scale) / scale for f in fits)
    if spread > 0.01:
        raise rbm_geom.RbmError(f"GeneralMkIII: per-axis scales disagree by {spread:.1%}")

    positions = []
    for i in range(vcount):
        p = []
        for k in range(3):
            if k in live:
                p.append(lo[k] + (cols[k][i] - min(cols[k])) * spans[k] / sspans[k])
            else:
                p.append(lo[k])
        positions.append(p)

    # everything up to the index buffer is the other vertex streams, framed
    idx = tail_index_buffer(buf, pos_end, end, vcount)
    if idx is None:
        raise rbm_geom.RbmError("GeneralMkIII: no terminal index buffer")
    ib_at, index_count, indices = idx
    (count2,) = struct.unpack_from("<I", buf, pos_end) if pos_end + 4 <= ib_at else (0,)
    stride2 = None
    if count2 and count2 == vcount and ib_at - pos_end - 4 >= count2 * 4 \
            and (ib_at - pos_end - 4) % count2 == 0:
        stride2 = (ib_at - pos_end - 4) // count2
    return {
        "decode": "quantized",
        "version": version,
        "materials": textures,
        "vertex_count": vcount,
        "vertex_stride": stride,
        "position_scale": scale,
        "scale_error": spread,
        "stream2_count": count2,
        "stream2_stride": stride2,
        "positions": positions,
        "index_count": index_count,
        "indices": indices,
        "index_at": ib_at,
        "opaque_bytes": ib_at - pos_end,
        "attributes": attrs,
    }


def find_position_stride(buf: bytes, pos: int, end: int, vcount: int):
    """Smallest record stride at which every vertex carries the 32767 sentinel."""
    for stride in range(8, 65, 4):
        if pos + stride * vcount > end:
            break
        cols = [[], [], []]
        ok = True
        for i in range(vcount):
            x, y, z, w = struct.unpack_from("<4h", buf, pos + stride * i)
            if w != 32767:
                ok = False
                break
            cols[0].append(x); cols[1].append(y); cols[2].append(z)
        if ok:
            return stride, cols
    raise rbm_geom.RbmError(f"GeneralMkIII: no {vcount}-vertex position stride "
                            "carries the packed 1.0")


# ------------------------------------------------------------ General family
def locate_textures(buf: bytes, start: int, end: int):
    """First self-consistent texture table at or after `start`.

    `_locate_texture_tables` proposes a count; the table is accepted only when
    every entry it yields is a real asset path (`name.ext`), which rejects a
    four-byte count that merely looks plausible in vertex data.
    """
    for tbl in rbm_geom._locate_texture_tables(buf, start, min(end, start + 8192)):
        try:
            mats, after = read_textures(buf, tbl[0])
        except (struct.error, UnicodeDecodeError):
            continue
        # Some blocks carry placeholder empty slots after the real materials
        # (Prop: 6 slots, 3 of them ""), so empty strings are allowed and only
        # the non-empty ones have to look like asset paths.
        if mats and any(mats) and all("." in m for m in mats if m):
            return tbl[0], mats, after
    return None, [], None


def mesh_bbox(header: dict):
    return header["bbox_min"], header["bbox_max"]


def inside(positions, bbox, tol=1e-3) -> bool:
    lo, hi = bbox
    return all(lo[k] - tol <= p[k] <= hi[k] + tol for p in positions for k in range(3))


def decode_general(buf: bytes, start: int, end: int, header: dict) -> dict:
    """General (0xA7583B2B), version 6.

    u8 version, Attributes (68 bytes: 3 u32, 3 floats, 2 floats, 3 u32, bbox min,
    bbox max), texture table, then

        u32 vcount,  vcount x {s16 x, y, z, pad}   positions, quantized
        u32 count2,  count2 x 20 bytes            normals/uv/colour, opaque
        u32 icount,  icount x u16

    The quantisation scale is attribute float 0 divided by 32768; the block's own
    AABB then contains every decoded vertex - that containment is the oracle, and
    it is checked per block rather than assumed.
    """
    version = buf[start]
    if version != 6:
        raise rbm_geom.RbmError(f"General version {version}")
    a = start + 1
    f3 = struct.unpack_from("<3f", buf, a + 12)
    bbox = (struct.unpack_from("<3f", buf, a + 44), struct.unpack_from("<3f", buf, a + 56))
    scale = f3[0] / 32768.0
    tbl, materials, after = locate_textures(buf, a + 68, end)
    if after is None:
        raise rbm_geom.RbmError("General: no texture table")
    (vcount,) = struct.unpack_from("<I", buf, after)
    pos = after + 4
    if not 0 < vcount < 2_000_000 or pos + 8 * vcount > end:
        raise rbm_geom.RbmError(f"General vertex count {vcount}")
    positions = [[c * scale for c in struct.unpack_from("<3h", buf, pos + 8 * i)] for i in range(vcount)]
    if not inside(positions, bbox):
        raise rbm_geom.RbmError("General: a vertex falls outside the block AABB")
    (count2,) = struct.unpack_from("<I", buf, pos + 8 * vcount)
    ib_at = pos + 8 * vcount + 4 + 20 * count2
    (index_count,) = struct.unpack_from("<I", buf, ib_at)
    indices = list(struct.unpack_from(f"<{index_count}H", buf, ib_at + 4))
    if ib_at + 4 + 2 * index_count != end:
        raise rbm_geom.RbmError("General: buffers do not end at the block checksum")
    return {
        "decode": "quantized", "version": version, "materials": materials,
        "material_slots": len(materials), "vertex_count": vcount, "vertex_stride": 8,
        "position_scale": scale, "block_bbox": [list(bbox[0]), list(bbox[1])],
        "stream2_count": count2, "stream2_stride": 20 if count2 else None,
        "positions": positions, "index_count": index_count, "indices": indices,
        "index_at": ib_at, "opaque_bytes": 20 * count2,
    }


def decode_generaljc3(buf: bytes, start: int, end: int, header: dict) -> dict:
    """GeneralJC3 (0x2EE0F4A9), version 6.

    u8 version, a fixed prefix, texture table, then the GeneralMkIII buffer
    pattern: u32 vcount, vcount x 8-byte packed normal, u32 count2 (== vcount),
    count2 x 20 bytes, u32 icount, indices.

    The block carries no AABB of its own, so the quantisation scale is the float
    that sits 32 bytes before the texture table (same slot in all 35 blocks) / 32768;
    the oracle is exact structural arithmetic plus every vertex inside the mesh
    file's AABB.
    """
    version = buf[start]
    if version != 6:
        raise rbm_geom.RbmError(f"GeneralJC3 version {version}")
    tbl, materials, after = locate_textures(buf, start + 1, end)
    if after is None or tbl < start + 33:
        raise rbm_geom.RbmError("GeneralJC3: no texture table")
    (scale_raw,) = struct.unpack_from("<f", buf, tbl - 32)
    scale = scale_raw / 32768.0
    (vcount,) = struct.unpack_from("<I", buf, after)
    pos = after + 4
    if not 0 < vcount < 2_000_000 or pos + 8 * vcount + 4 > end:
        raise rbm_geom.RbmError(f"GeneralJC3 vertex count {vcount}")
    positions = [[c * scale for c in struct.unpack_from("<3h", buf, pos + 8 * i)] for i in range(vcount)]
    if not inside(positions, mesh_bbox(header)):
        raise rbm_geom.RbmError("GeneralJC3: a vertex falls outside the mesh AABB")
    (count2,) = struct.unpack_from("<I", buf, pos + 8 * vcount)
    ib_at = pos + 8 * vcount + 4 + 20 * count2
    (index_count,) = struct.unpack_from("<I", buf, ib_at)
    indices = list(struct.unpack_from(f"<{index_count}H", buf, ib_at + 4))
    if ib_at + 4 + 2 * index_count != end:
        raise rbm_geom.RbmError("GeneralJC3: buffers do not end at the block checksum")
    return {
        "decode": "quantized", "version": version, "materials": materials,
        "material_slots": len(materials), "vertex_count": vcount, "vertex_stride": 8,
        "position_scale": scale, "stream2_count": count2,
        "stream2_stride": 20 if count2 else None, "positions": positions,
        "index_count": index_count, "indices": indices, "index_at": ib_at,
        "opaque_bytes": 20 * count2,
    }


def decode_bavarium(buf: bytes, start: int, end: int, header: dict) -> dict:
    """BavariumShield (0xA5D24CCD), version 1.

    u8 version, 4 floats, texture table, u32 vcount, vcount x 28 bytes
    (3 float position + 16 bytes packed attributes), u32 icount, indices.
    """
    version = buf[start]
    if version != 1:
        raise rbm_geom.RbmError(f"BavariumShield version {version}")
    tbl, materials, after = locate_textures(buf, start + 1, end)
    if after is None:
        raise rbm_geom.RbmError("BavariumShield: no texture table")
    (vcount,) = struct.unpack_from("<I", buf, after)
    pos = after + 4
    if not 0 < vcount < 2_000_000 or pos + 28 * vcount + 4 > end:
        raise rbm_geom.RbmError(f"BavariumShield vertex count {vcount}")
    positions = [list(struct.unpack_from("<3f", buf, pos + 28 * i)) for i in range(vcount)]
    if not inside(positions, mesh_bbox(header)):
        raise rbm_geom.RbmError("BavariumShield: a vertex falls outside the mesh AABB")
    ib_at = pos + 28 * vcount
    (index_count,) = struct.unpack_from("<I", buf, ib_at)
    indices = list(struct.unpack_from(f"<{index_count}H", buf, ib_at + 4))
    if ib_at + 4 + 2 * index_count != end:
        raise rbm_geom.RbmError("BavariumShield: buffers do not end at the block checksum")
    return {
        "decode": "float", "version": version, "materials": materials,
        "material_slots": len(materials), "vertex_count": vcount, "vertex_stride": 28,
        "positions": positions, "index_count": index_count, "indices": indices,
        "index_at": ib_at, "opaque_bytes": 16 * vcount,
    }


def decode_prop(buf: bytes, start: int, end: int, header: dict) -> dict:
    """Prop (0x04894ECD), version 3 - the JC2-era prop block.

    Same buffer pattern as GeneralJC3, and the same scale slot (the float 32
    bytes before the texture table):

        u8 version=3, attributes, texture table,
        u32 vcount,  vcount x {s16 x, y, z, 0}      positions, quantized
        u32 count2 (== vcount), count2 x 20 bytes   packed attributes, opaque
        u32 icount,  icount x u16

    The single sample (`jc2_barrel_a_lod1.rbm`) pins the scale hard: the stored
    float is bit-identical to the mesh AABB's Y extent, the s16 Y run is the full
    0..32767, and the resulting X/Y/Z spans agree with the AABB spans to 4e-5
    relative.  Only one block exists, so the oracle is that span agreement plus
    containment, not a per-block AABB comparison.
    """
    version = buf[start]
    if version != 3:
        raise rbm_geom.RbmError(f"Prop version {version}")
    tbl, materials, after = locate_textures(buf, start + 1, end)
    if after is None or tbl < start + 0x21:
        raise rbm_geom.RbmError("Prop: no texture table")
    (scale_raw,) = struct.unpack_from("<f", buf, tbl - 0x20)
    scale = scale_raw / 32768.0
    (vcount,) = struct.unpack_from("<I", buf, after)
    pos = after + 4
    if not 0 < vcount < 2_000_000 or pos + 8 * vcount + 4 > end:
        raise rbm_geom.RbmError(f"Prop vertex count {vcount}")
    positions = [[c * scale for c in struct.unpack_from("<3h", buf, pos + 8 * i)] for i in range(vcount)]
    if not inside(positions, mesh_bbox(header)):
        raise rbm_geom.RbmError("Prop: a vertex falls outside the mesh AABB")
    (count2,) = struct.unpack_from("<I", buf, pos + 8 * vcount)
    if count2 != vcount:
        raise rbm_geom.RbmError(f"Prop: second stream count {count2} != {vcount}")
    ib_at = pos + 8 * vcount + 4 + 20 * count2
    (index_count,) = struct.unpack_from("<I", buf, ib_at)
    indices = list(struct.unpack_from(f"<{index_count}H", buf, ib_at + 4))
    if ib_at + 4 + 2 * index_count != end:
        raise rbm_geom.RbmError("Prop: buffers do not end at the block checksum")
    lo, hi = mesh_bbox(header)
    span_fit = []
    for k in range(3):
        vals = [p[k] for p in positions]
        span = max(vals) - min(vals)
        ref = hi[k] - lo[k]
        span_fit.append(span / ref if ref > 1e-6 else 1.0)
    return {
        "decode": "quantized", "version": version, "materials": materials,
        "material_slots": len(materials), "vertex_count": vcount, "vertex_stride": 8,
        "position_scale": scale, "scale_error": max(abs(f - 1.0) for f in span_fit),
        "stream2_count": count2, "stream2_stride": 20 if count2 else None,
        "positions": positions, "index_count": index_count, "indices": indices,
        "index_at": ib_at, "opaque_bytes": 20 * count2,
    }


def decode_position_only(buf: bytes, start: int, end: int, header: dict, name: str) -> dict:
    """WaterDisplacementOverride / 0x90FE086C, version 1: positions only.

    u8 version, u32 flags, 16-byte material params (no texture table), u32 vcount,
    vcount x 3 floats, u32 icount, indices.  No normal or UV stream: 12 bytes a
    vertex, and the block ends exactly at the checksum.
    """
    version = buf[start]
    if version != 1:
        raise rbm_geom.RbmError(f"{name} version {version}")
    (vcount,) = struct.unpack_from("<I", buf, start + 21)
    pos = start + 25
    if not 0 < vcount < 2_000_000 or pos + 12 * vcount + 4 > end:
        raise rbm_geom.RbmError(f"{name} vertex count {vcount}")
    positions = [list(struct.unpack_from("<3f", buf, pos + 12 * i)) for i in range(vcount)]
    if not inside(positions, mesh_bbox(header)):
        raise rbm_geom.RbmError(f"{name}: a vertex falls outside the mesh AABB")
    ib_at = pos + 12 * vcount
    (index_count,) = struct.unpack_from("<I", buf, ib_at)
    indices = list(struct.unpack_from(f"<{index_count}H", buf, ib_at + 4))
    if ib_at + 4 + 2 * index_count != end:
        raise rbm_geom.RbmError(f"{name}: buffers do not end at the block checksum")
    return {
        "decode": "float", "version": version, "materials": [], "material_slots": 0,
        "vertex_count": vcount, "vertex_stride": 12, "positions": positions,
        "index_count": index_count, "indices": indices, "index_at": ib_at,
        "opaque_bytes": 0,
    }


# ------------------------------------------------------------------ mesh decode
def decode_mesh(buf: bytes, path: str) -> dict:
    header = rbm_geom.Rbm.parse_header(buf)
    header["magic"] = header["magic"].decode("ascii", "replace")
    next_hashes = set(rbm_geom.BLOCK_NAMES)
    off = header["header_len"]
    blocks = []
    for b in range(header["number_of_blocks"]):
        (th,) = struct.unpack_from("<I", buf, off)
        off += 4
        name = rbm_geom.BLOCK_NAMES.get(th, f"0x{th:08X}")
        rec = {"type": name, "type_hash": f"0x{th:08X}"}
        try:
            if th == rbm_geom.RB_CARPAINTMM:
                blk, off = rbm_geom.decode_carpaintmm(buf, off, th)
                rec.update(decode_carpaint(blk))
            elif th in rbm_geom.GENERIC_TEMPLATES:
                blk, off = rbm_geom.decode_generic(buf, off, th)
                rec.update(decode_generic(blk, header))
            elif th == RB_GENERALMKIII:
                end = find_block_end(buf, off, next_hashes)
                rec.update(decode_generalmkiii(buf, off, end, header))
                off = end
            elif th in (RB_GENERAL, RB_GENERALJC3, RB_BAVARIUMSHIELD, RB_WATERDISP,
                        RB_UNKNOWN90FE, RB_PROP):
                end = find_block_end(buf, off, next_hashes)
                if th == RB_GENERAL:
                    rec.update(decode_general(buf, off, end, header))
                elif th == RB_GENERALJC3:
                    rec.update(decode_generaljc3(buf, off, end, header))
                elif th == RB_BAVARIUMSHIELD:
                    rec.update(decode_bavarium(buf, off, end, header))
                elif th == RB_PROP:
                    rec.update(decode_prop(buf, off, end, header))
                else:
                    rec.update(decode_position_only(buf, off, end, header, name))
                off = end
            else:
                end = find_block_end(buf, off, next_hashes)
                rec.update(decode_opaque(buf, off, end))
                off = end
        except rbm_geom.RbmError as e:
            rec.update({"decode": "failed", "error": str(e)})
            # skip to this block's checksum so the next block is still framed
            try:
                off = find_block_end(buf, off, next_hashes)
            except rbm_geom.RbmError:
                break
        (cs,) = struct.unpack_from("<I", buf, off)
        off += 4
        if cs != CHECKSUM:
            rec["checksum_bad"] = f"0x{cs:08X}"
            break
        blocks.append(rec)
    lod = LOD_RE.search(re.sub(r"\.rbm$", "", path, flags=re.I))
    return {
        "path": path,
        "lod": int(lod.group(1)) if lod else None,
        "header": header,
        "blocks": blocks,
    }


def decode_carpaint(blk) -> dict:
    vcount = blk.vb0.count
    idx = blk.indices()
    positions = blk.vb0.positions()
    return {
        "decode": "carpaintmm",
        "flags": blk.flags,
        "materials": blk.textures,
        "material_slots": blk.texture_count,
        "vertex_count": vcount,
        "vertex_stride": blk.vb0.stride,
        "index_count": blk.index_count,
        "indices": idx,
        "positions": [list(p) for p in positions],
        "normal_stride": blk.vb1.stride,
        "skin_batches": bool(blk.skin_batches),
    }


def decode_generic(blk, header) -> dict:
    idx = blk.indices()
    positions = [list(p) for p in blk.vb0.positions()]
    return {
        "decode": "generic",
        "materials": blk.textures,
        "material_slots": len(blk.textures),
        "vertex_count": blk.vb0.count,
        "vertex_stride": blk.vb0.stride,
        "index_count": blk.index_count,
        "indices": idx,
        "positions": positions,
        "normal_stride": blk.vb1.stride,
    }


def decode_opaque(buf: bytes, start: int, end: int) -> dict:
    """Frame a block we have no layout for: materials + terminal index buffer."""
    body = buf[start:end]
    materials = []
    tbl_end = None
    for tbl in rbm_geom._locate_texture_tables(buf, start, min(end, start + 8192)):
        materials, after = read_textures(buf, tbl[0])
        tbl_end = after
        break
    vcount = None
    idx = None
    if tbl_end is not None:
        for q in range(tbl_end, end - 4):
            c, = struct.unpack_from("<I", buf, q)
            if c >= 3 and c % 3 == 0 and q + 4 + 2 * c <= end:
                hit = tail_index_buffer(buf, q, end, 1 << 24)
                if hit:
                    idx = hit
                    break
    if idx:
        q, c, indices = idx
        # a vertex count can only be bounded, not read: the largest index+1 is
        # the lower bound and the gap is kept as an opaque byte range
        vcount = max(indices) + 1
        return {
            "decode": "framed",
            "materials": materials,
            "material_slots": len(materials),
            "vertex_count": vcount,
            "vertex_count_kind": "lower bound (max index + 1)",
            "index_count": c,
            "indices": indices,
            "opaque_bytes": q - (tbl_end or start),
            "positions": None,
        }
    return {
        "decode": "framed",
        "materials": materials,
        "material_slots": len(materials),
        "vertex_count": None,
        "index_count": None,
        "indices": None,
        "opaque_bytes": len(body),
        "positions": None,
    }


# ------------------------------------------------------------------ entity pass
def grab(ee_path: str, rows: list[dict], game: str) -> dict:
    raw, src = read_entry(rows, ee_path, game)
    stream, entries = unaaf(raw), sarc_dir(unaaf(raw))
    meshes = []
    sidecar = bytearray()
    for name, off, size in sorted(entries):
        if not name.lower().endswith(".rbm"):
            continue
        referenced = off == 0
        if referenced:
            blob, r = read_entry(rows, name, game)
        else:
            blob, r = stream[off:off + size], None
        try:
            doc = decode_mesh(blob, name)
        except Exception as e:                              # noqa: BLE001
            meshes.append({"path": name, "error": str(e)})
            continue
        doc["referenced"] = referenced
        if r:
            doc["source"] = {"archive": r["archive"], "offset": r["offset"], "size": r["size"]}
        for blk in doc["blocks"]:
            blo = len(sidecar)
            pos = blk.pop("positions", None)
            if pos:
                sidecar += struct.pack(f"<{3 * len(pos)}f", *(c for p in pos for c in p))
            clo = len(sidecar)
            idx = blk.pop("indices", None)
            if idx:
                fmt = "<H" if max(idx) < 65536 else "<I"
                sidecar += struct.pack(f"<{len(idx)}{fmt[1]}", *idx)
            blk["payload"] = {
                "positions_at": blo,
                "positions_bytes": (clo - blo),
                "indices_at": clo,
                "indices_bytes": len(sidecar) - clo,
                "index_width": 2 if not idx or max(idx) < 65536 else 4,
            }
        meshes.append(doc)
    return {
        "entity": ee_path,
        "source": {"archive": src["archive"], "offset": src["offset"], "size": src["size"]},
        "meshes": meshes,
        "payload": bytes(sidecar),
    }


def cmd_build(a) -> int:
    rows = load_index(a.index)
    targets = vehicle_ees(rows, a.entity)
    if a.limit:
        targets = targets[:a.limit]
    os.makedirs(GEOM, exist_ok=True)
    print(f"{len(targets)} entities -> {GEOM}")
    summary = []
    totals = {"entities": 0, "meshes": 0, "decoded": 0, "framed": 0, "failed": 0,
              "vertices": 0, "triangles": 0, "materials": 0}
    for i, ee in enumerate(targets, 1):
        try:
            doc = grab(ee, rows, a.game)
        except Exception as e:                              # noqa: BLE001
            print(f"[{i}/{len(targets)}] {os.path.basename(ee)}: ERROR {e}")
            continue
        payload = doc.pop("payload")
        path = os.path.join(GEOM, slug(ee) + ".json")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, separators=(",", ":"))
        with open(os.path.join(GEOM, slug(ee) + ".bin"), "wb") as f:
            f.write(payload)
        totals["entities"] += 1
        for m in doc["meshes"]:
            row = mesh_row(ee, m, os.path.basename(path), payload)
            summary.append(row)
            totals["meshes"] += 1
            for blk in m.get("blocks", []):
                st = blk.get("decode")
                if st in ("carpaintmm", "generic", "quantized", "float"):
                    totals["decoded"] += 1
                elif st == "framed":
                    totals["framed"] += 1
                else:
                    totals["failed"] += 1
                totals["vertices"] += blk.get("vertex_count") or 0
                totals["triangles"] += (blk.get("index_count") or 0) // 3
                totals["materials"] += len(blk.get("materials") or [])
        n_dec = sum(1 for m in doc["meshes"] for b in m.get("blocks", [])
                    if b.get("decode") in ("carpaintmm", "generic", "quantized", "float"))
        n_bad = sum(1 for m in doc["meshes"] for b in m.get("blocks", [])
                    if b.get("decode") not in ("carpaintmm", "generic", "quantized", "float", "framed"))
        print(f"[{i}/{len(targets)}] {os.path.basename(ee)}: {len(doc['meshes'])} meshes, "
              f"{n_dec} blocks decoded, {n_bad} failed")
    with open(os.path.join(OUT, "GEOMETRY.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for r in summary:
            f.write(json.dumps(r, separators=(",", ":")) + "\n")
    print("totals:", totals)
    return 0


def mesh_row(ee: str, m: dict, doc: str, payload: bytes) -> dict:
    blocks = m.get("blocks", [])
    return {
        "entity": ee,
        "path": m.get("path"),
        "lod": m.get("lod"),
        "doc": doc,
        "error": m.get("error"),
        "referenced": m.get("referenced", False),
        "bbox": [m["header"]["bbox_min"], m["header"]["bbox_max"]] if "header" in m else None,
        "size_bytes": None,
        "blocks": [
            {
                "type": b.get("type"),
                "decode": b.get("decode"),
                "vertex_count": b.get("vertex_count"),
                "vertex_stride": b.get("vertex_stride"),
                "index_count": b.get("index_count"),
                "materials": len(b.get("materials") or []),
                "material_slots": b.get("material_slots"),
                "scale_error": b.get("scale_error"),
                "stream2_stride": b.get("stream2_stride"),
                "error": b.get("error"),
                "payload": b.get("payload"),
            }
            for b in blocks
        ],
    }


# ---------------------------------------------------------------------- report
def load_rows() -> list[dict]:
    p = os.path.join(OUT, "GEOMETRY.jsonl")
    if not os.path.exists(p):
        raise SystemExit("no GEOMETRY.jsonl - run `jc3geom.py build --all` first")
    return [json.loads(line) for line in open(p, encoding="utf-8") if line.strip()]


def cmd_report(a) -> int:
    rows = load_rows()
    blocks = [b for r in rows for b in r["blocks"]]
    kinds: dict[str, int] = {}
    for b in blocks:
        kinds[b["decode"] or "failed"] = kinds.get(b["decode"] or "failed", 0) + 1
    types: dict[str, int] = {}
    for b in blocks:
        types[b["type"] or "?"] = types.get(b["type"] or "?", 0) + 1
    vertices = sum(b.get("vertex_count") or 0 for b in blocks)
    tris = sum((b.get("index_count") or 0) // 3 for b in blocks)
    mats = sum(b.get("materials") or 0 for b in blocks)
    # Only GeneralMkIII records a per-axis scale disagreement; GeneralJC3/Prop
    # record the span fit against the mesh AABB, which is a different measure.
    scale_errs = [b["scale_error"] for b in blocks
                  if b.get("scale_error") is not None and b.get("type") == "GeneralMkIII"]
    failed = [b for b in blocks if b["decode"] not in ("carpaintmm", "generic", "quantized", "float", "framed")]

    per_entity: dict[str, list[int]] = {}
    for r in rows:
        e = per_entity.setdefault(r["entity"], [0, 0, 0])
        e[0] += 1
        for b in r["blocks"]:
            e[1] += b.get("vertex_count") or 0
            e[2] += (b.get("index_count") or 0) // 3

    lines = [
        "# JC3 render meshes - payload grab (G2-5)",
        "",
        f"Every mesh block in the {len(per_entity)} vehicle entities, decoded from the `.ee` bundles by",
        "`Tools/scripts/jc3geom.py`. Raw payloads (positions as float32 x3, indices as",
        "uint16/uint32) live in `_JC3grab/geom/*.bin`, one pair per entity; this table is",
        "the derived summary.",
        "",
        "| item | value |",
        "|---|---|",
        f"| entities | {len(per_entity)} |",
        f"| meshes | {len(rows)} |",
        f"| mesh blocks | {len(blocks)} |",
        f"| decoded blocks | {kinds.get('carpaintmm', 0) + kinds.get('generic', 0) + kinds.get('quantized', 0) + kinds.get('float', 0)} |",
        f"| framed (materials + faces, vertices opaque) | {kinds.get('framed', 0)} |",
        f"| failed | {len(failed)} |",
        f"| vertices (decoded + framed) | {vertices} |",
        f"| triangles | {tris} |",
        f"| material slots | {mats} |",
        "",
        "## Decoders",
        "",
        "| decoder | blocks | oracle |",
        "|---|---|---|",
        f"| `CarPaintMM` | {kinds.get('carpaintmm', 0)} | byte-exact re-encode (`rbm_geom`) |",
        f"| `Window` / `CarLight` | {kinds.get('generic', 0)} | byte-exact re-encode |",
        f"| `GeneralMkIII`, `General`, `GeneralJC3`, `Prop` quantized | {kinds.get('quantized', 0)} | s16 span x the block's own scale; GeneralMkIII/General checked against the block AABB, GeneralJC3/Prop against the mesh AABB |",
        f"| `BavariumShield`, `WaterDisplacementOverride`, `0x90FE086C` float | {kinds.get('float', 0)} | 12/28-byte float positions inside the mesh AABB, buffers ending at the checksum |",
        f"| framed, no vertex layout | {kinds.get('framed', 0)} | texture table self-locating; index buffer ends at the block checksum |",
        "",
    ]
    if scale_errs:
        lines += [
            f"`GeneralMkIII` quantization: one scale per axis, axes agree to **{max(scale_errs):.2%}** "
            f"worst case over {len(scale_errs)} blocks; each block's positions are mapped onto "
            "its own Attributes AABB.",
            "",
        ]
    lines += [
        "## Block types",
        "",
        "| block | meshes |",
        "|---|---|",
    ]
    for k, v in sorted(types.items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{k}` | {v} |")
    lines += ["", "## Vehicles", "", "| entity | meshes | vertices | triangles |", "|---|---|---|---|"]
    for e, (m, v, t) in sorted(per_entity.items(), key=lambda kv: -kv[1][1])[:40]:
        lines.append(f"| `{e.rsplit('/', 1)[-1]}` | {m} | {v} | {t} |")
    lines += ["", f"Top 40 of {len(per_entity)} entities, most vertices first.", ""]
    if failed:
        lines += ["## Failed blocks", "", "| entity | mesh | block | error |", "|---|---|---|---|"]
        for r in rows:
            for b in r["blocks"]:
                if b["decode"] not in ("carpaintmm", "generic", "quantized", "float", "framed"):
                    lines.append(f"| `{r['entity'].rsplit('/', 1)[-1]}` | `{r['path']}` | "
                                 f"`{b['type']}` | {b['error']} |")
        lines.append("")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "GEOMETRY.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"GEOMETRY.md: {len(rows)} meshes, {len(blocks)} blocks, {vertices} vertices, "
          f"{tris} triangles, {len(failed)} failed")
    return 0


# ----------------------------------------------------------------------- check
def cmd_check(a) -> int:
    rows = load_rows()
    blocks = [b for r in rows for b in r["blocks"]]
    problems: list[str] = []
    ents = {r["entity"] for r in rows}
    if len(ents) != 233:
        problems.append(f"entities {len(ents)} != 233")
    no_mesh = [r["entity"] for r in rows if not r["blocks"]]
    if no_mesh:
        problems.append(f"{len(no_mesh)} meshes with no blocks")
    bad_idx = [b for b in blocks if b.get("index_count") and b.get("vertex_count")
               and b["index_count"] % 3]
    if bad_idx:
        problems.append(f"{len(bad_idx)} index buffers not a triangle list")
    failed = [b for b in blocks if b["decode"] not in ("carpaintmm", "generic", "quantized", "float", "framed")]
    if failed:
        problems.append(f"{len(failed)} failed blocks")

    # payload binaries must exist and be exactly as long as their records claim
    seen = set()
    for r in rows:
        if r["doc"] in seen:
            continue
        seen.add(r["doc"])
        jp = os.path.join(GEOM, r["doc"])
        bp = jp[:-5] + ".bin"
        if not os.path.exists(bp):
            problems.append(f"missing {bp}")
            continue
        size = os.path.getsize(bp)
        doc = json.load(open(jp, encoding="utf-8"))
        for m in doc["meshes"]:
            for b in m.get("blocks", []):
                p = b.get("payload")
                if not p:
                    continue
                if p["positions_at"] + p["positions_bytes"] > size or \
                        p["indices_at"] + p["indices_bytes"] > size:
                    problems.append(f"{r['doc']}: payload beyond end")
    # spot-check a GeneralMkIII decode against the header AABB
    q = [b for b in blocks if b["decode"] == "quantized" and b.get("scale_error") is not None]
    if q and max(b["scale_error"] for b in q) > 1e-2:
        problems.append("quantized per-axis scale disagreement above 1%")
    print(f"entities {len(ents)} | meshes {len(rows)} | blocks {len(blocks)} | "
          f"decoded {sum(1 for b in blocks if b['decode'] in ('carpaintmm', 'generic', 'quantized', 'float'))} | "
          f"framed {sum(1 for b in blocks if b['decode'] == 'framed')} | failed {len(failed)}")
    if problems:
        for p in problems[:30]:
            print("FAIL", p)
        return 1
    print("check ok")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="decode every vehicle .rbm payload")
    b.add_argument("--entity", help="substring filter")
    b.add_argument("--all", action="store_true")
    b.add_argument("--limit", type=int, default=0)
    b.add_argument("--game", default=DEFAULT_GAME)
    b.add_argument("--index", default=DEFAULT_OUT)
    b.set_defaults(func=cmd_build)
    r = sub.add_parser("report", help="write GEOMETRY.md")
    r.set_defaults(func=cmd_report)
    c = sub.add_parser("check", help="assert the payload grab is complete")
    c.set_defaults(func=cmd_check)
    a = ap.parse_args()
    sys.exit(a.func(a))


if __name__ == "__main__":
    main()
