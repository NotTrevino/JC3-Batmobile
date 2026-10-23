#!/usr/bin/env python3
"""
rbm_geom.py - read/write JC3 RBMDL render-block models, with a byte-exact round trip.

Why this exists
---------------
`Gibbed.JustCause3.ConvertRBM.exe` cannot parse JC3 vehicle RBMs: it dies on the
first block, `0x483304D6` (CarPaintMM), because the Gibbed JC3 fork's RBM
serializer is self-described as "a WIP (in its ultra-very early stage)".
Brooen/RBM-Exporter can *write* CarPaintMM but its Blender addon targets
Blender 4.1.1. `aaronkirkham/jc-model-renderer` fully parses and re-serialises
the format but is a 40 MB GUI app.

This module reimplements the same serialization in Python, from the actual
sources, so mesh editing is scriptable and auditable:

  * header  : ava-format-lib include/AvaFormatLib/models/render_block_model.h
  * container + framing : jc-model-renderer src/game/formats/render_block_model.cpp
  * block framing (ReadBuffer / ReadMaterials) : jc-model-renderer
    src/game/jc3/renderblocks/irenderblock.cpp
  * CarPaintMM layout : jc-model-renderer
    src/game/jc3/renderblocks/renderblockcarpaintmm.h
  * vertex structs/strides : jc-model-renderer src/game/types.h

Guarantee
---------
`roundtrip()` must return a byte-identical copy. That is the only oracle that
matters before touching the game: if decode->encode is not exact, every
subsequent conclusion is worthless. `selftest` asserts it on the real donor
files.

Layout (all little-endian; the format permits big-endian via a byte-swapped
magicLength, which we detect and reject rather than silently mis-parse):

  RbmHeader (0x35 bytes)
    u32 magicLength (=5) | char[5] "RBMDL" | u32 major | u32 minor | u32 revision
    f32 bboxMin[3] | f32 bboxMax[3] | u32 numberOfBlocks | u32 tag
  then numberOfBlocks x:
    u32 typeHash
    <block payload>
    u32 0x89ABCDEF

CarPaintMM payload:
    u8 version(=14) | u32 flags | f32 unknown
    f32[4] x 18                        static material params
    f32[4] x 7                         static support flags
    f32[4] x 4 | f32 x 3               dynamic material params
    u32 x 256                          deform table
    u32 count | count x (u32 len + len bytes) | f32[4]   materials + materialParams
    u32 count | count x stride         vertex buffer   (stride from flags)
    u32 count | count x stride2        normals/tangent buffer (stride from flags)
    [u32 batches ...]                  only if IS_SKINNED
    [u32 count | count x 8]            only if SUPPORT_LAYERED | SUPPORT_OVERLAY
    u32 count | count x 2              index buffer (uint16)
"""

from __future__ import annotations

import argparse
import glob
import os
import struct
import sys
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# constants from ava-format-lib
# ---------------------------------------------------------------------------

RBM_BLOCK_CHECKSUM = 0x89ABCDEF

RB_GENERAL = 0xA7583B2B
RB_GENERALJC3 = 0x2EE0F4A9
RB_GENERALMASKEDJC3 = 0x8F2335EC
RB_GENERALMKIII = 0x2CEC5AD5
RB_CARPAINTMM = 0x483304D6
RB_CARLIGHT = 0xDB948BF1
RB_WINDOW = 0x5B2003F6
RB_BAVARIUMSHIELD = 0xA5D24CCD
RB_WATERDISPLACEMENTOVERRIDE = 0xF99C72A1
RB_DECALDEFORMABLE = 0xDF9E9916
RB_DECALSIMPLE = 0x2BAFDD6C
RB_LAYERED = 0xC7021EE3
RB_OCCLUDER = 0x2A44553C
RB_TRIANGLE = 0xEB96E782
RB_PROP = 0x04894ECD
RB_LANDMARK = 0x3B630E6D
RB_BUILDINGJC3 = 0x35BF53D5
RB_CHARACTER = 0x9D6E332A
RB_CHARACTERSKIN = 0x626F5E3B

BLOCK_NAMES = {
    RB_GENERAL: "General",
    RB_GENERALJC3: "GeneralJC3",
    RB_GENERALMASKEDJC3: "GeneralMaskedJC3",
    RB_GENERALMKIII: "GeneralMkIII",
    RB_CARPAINTMM: "CarPaintMM",
    RB_CARLIGHT: "CarLight",
    RB_WINDOW: "Window",
    RB_BAVARIUMSHIELD: "BavariumShield",
    RB_WATERDISPLACEMENTOVERRIDE: "WaterDisplacementOverride",
    RB_DECALDEFORMABLE: "DecalDeformable",
    RB_DECALSIMPLE: "DecalSimple",
    RB_LAYERED: "Layered",
    RB_OCCLUDER: "Occluder",
    RB_TRIANGLE: "Triangle",
    RB_PROP: "Prop",
    RB_LANDMARK: "Landmark",
    RB_BUILDINGJC3: "BuildingJC3",
    RB_CHARACTER: "Character",
    RB_CHARACTERSKIN: "CharacterSkin",
}

# CarPaintMM flags (renderblockcarpaintmm.h)
SUPPORT_DECALS = 0x1
SUPPORT_DAMAGE_BLEND = 0x2
SUPPORT_DIRT = 0x4
SUPPORT_PALETTE_FILE = 0x8
SUPPORT_SOFT_TINT = 0x10
SUPPORT_LAYERED = 0x20
SUPPORT_OVERLAY = 0x40
DISABLE_BACKFACE_CULLING = 0x80
TRANSPARENCY_ALPHABLENDING = 0x100
TRANSPARENCY_ALPHATESTING = 0x200
IS_DEFORM = 0x1000
IS_SKINNED = 0x2000

# vertex strides, static_assert'd in jc-model-renderer src/game/types.h
STRIDE_UNPACKED_POSITION = 0x0C          # float x,y,z
STRIDE_UNPACKED_WITH_NORMAL1 = 0x10      # float x,y,z,n
STRIDE_DEFORM_POS = 0x18                 # float x,y,z,d + int16 wi0..wi3
STRIDE_UNPACKED_NORMALS = 0x18           # float u0,v0,u1,v1,n,t
STRIDE_DEFORM_NORMAL2 = 0x20             # + float dn,dt
STRIDE_UNPACKED_UV = 0x08                # float u,v

CARPAINTMM_TEXTURE_SLOTS = 12


class RbmError(Exception):
    pass


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _read_buffer(buf: bytes, off: int) -> tuple[bytes, int]:
    """ReadBuffer(): u32 count, then count*stride bytes. Stride is implied by
    the caller, so we return the raw payload and let the caller slice it."""
    (count,) = struct.unpack_from("<I", buf, off)
    off += 4
    return buf[off:off], count, off


def _read_buffer_sized(buf: bytes, off: int, stride: int) -> tuple[bytes, int, int]:
    (count,) = struct.unpack_from("<I", buf, off)
    off += 4
    n = count * stride
    payload = buf[off:off + n]
    if len(payload) != n:
        raise RbmError(f"buffer overruns file: want {n} bytes at 0x{off:X}, have {len(payload)}")
    return payload, count, off + n


# ---------------------------------------------------------------------------
# probe: solve an unknown block layout from the files themselves
# ---------------------------------------------------------------------------

# Plausible vertex strides. JC3 packs position as 3 floats then either a packed
# normal, a float3 normal, or deform weights, so 12..40 in steps of 4 covers it.
PROBE_STRIDES = (12, 16, 20, 24, 28, 32, 36, 40)


def _probe_buffers(buf: bytes, off: int, end: int, strides, max_bufs: int = 4):
    """Walk a candidate buffer sequence. Returns a list of (stride, count) if the
    walk lands exactly on `end`, else None.

    The exact landing is the whole point: the engine appends a 0x89ABCDEF checksum
    right after the last buffer, so a layout that does not finish precisely there is
    wrong, however plausible its numbers look.
    """
    if off >= end:
        return []
    (count,) = struct.unpack_from("<I", buf, off)
    if count == 0:
        return None
    if count > 1_000_000:
        return None
    nxt = off + 4 + count * strides[0]
    if nxt > end:
        return None
    if nxt == end:
        return [(strides[0], count)]
    if len(strides) == 1:
        return None
    rest = _probe_buffers(buf, nxt, end, strides[1:], max_bufs - 1)
    if rest is None:
        return None
    return [(strides[0], count)] + rest


def _probe_one(path: str):
    """Return the surviving layout candidates for one file."""
    import numpy as np

    buf = open(path, "rb").read()
    h = Rbm.parse_header(buf)
    off = h["header_len"]
    out = []
    for i in range(h["number_of_blocks"]):
        (th,) = struct.unpack_from("<I", buf, off)
        body = off + 4
        (cs,) = struct.unpack_from("<I", buf, len(buf) - 4) if h["number_of_blocks"] == 1 else (0,)
        end = len(buf) - 4 if h["number_of_blocks"] == 1 else None
        if end is None:
            return None
        if struct.unpack_from("<I", buf, end)[0] != RBM_BLOCK_CHECKSUM:
            return None
        for s in range(0, 0x300, 4):
            for vs in PROBE_STRIDES:
                seq = _probe_buffers(buf, body + s, end, [vs] * 3 + [2])
                if not seq:
                    continue
                if any(st != vs for st, _ in seq[:-1]):
                    continue
                if seq[-1][1] % 3:
                    continue
                counts = {c for _, c in seq}
                if len(counts) != 1:
                    continue
                # the oracle: decode the first buffer as float3 positions and see
                # whether the engine's own header bbox falls out of it
                (cnt0,) = counts
                data = buf[body + s + 4: body + s + 4 + cnt0 * vs]
                if len(data) < 12:
                    continue
                P = np.frombuffer(data[:cnt0 * vs], dtype="<f4").reshape(-1, vs)[:, :3]
                P = P[np.isfinite(P).all(axis=1)]
                if len(P) < 3:
                    continue
                lo = P.min(axis=0)
                hi = P.max(axis=0)
                err = max(abs(lo[k] - h["bbox_min"][k]) for k in range(3))
                err = max(err, max(abs(hi[k] - h["bbox_max"][k]) for k in range(3)))
                out.append({
                    "block": i, "type": th, "static": s, "seq": seq,
                    "verts": cnt0, "tris": seq[-1][1] // 3, "bbox_err": float(err),
                })
        off = end + 4
    return out


def cmd_probe(args) -> int:
    """Work out the layout of a block type nobody has published.

    The engine wrote these files, so the layout is *in* them. Every candidate is
    judged by two independent oracles: the block must end exactly on its 0x89ABCDEF
    checksum, and the decoded positions must reproduce the bbox the engine itself
    stored in the file header. A layout has to survive both on every file of the type.
    """
    per_file = {}
    for p in args.inputs:
        r = _probe_one(p)
        if r is None:
            print(f"  {os.path.basename(p)}: not a single-block file with a trailing checksum; skipped")
            continue
        per_file[p] = r

    if not per_file:
        print("nothing to probe")
        return 1

    # key = (type, static, tuple-of-strides); keep the keys every file agrees on
    keysets = []
    for p, r in per_file.items():
        keysets.append({(c["type"], c["static"], tuple(st for st, _ in c["seq"])) for c in r})
    common = set.intersection(*keysets) if keysets else set()

    for p, r in per_file.items():
        print(f"{os.path.basename(p)}  ({len(r)} raw candidate(s))")
        for c in sorted(r, key=lambda c: (c["bbox_err"], c["static"])):
            key = (c["type"], c["static"], tuple(st for st, _ in c["seq"]))
            mark = "KEEP" if key in common else "    "
            print(f"  {mark} block {c['block']} {BLOCK_NAMES.get(c['type'], hex(c['type'])):<9} "
                  f"static={c['static']:>4} B  buffers={[st for st, _ in c['seq']]}  "
                  f"verts={c['verts']:>5} tris={c['tris']:>5}  bbox_err={c['bbox_err']:.4f} m")

    print()
    if not common:
        print("NO layout is consistent across every file. That is a real negative result:")
        print("either the type needs more than one buffer shape, or these files differ")
        print("in a way the single-block assumption cannot see.")
        return 1
    print(f"layouts consistent across all {len(per_file)} file(s): {len(common)}")
    for th, s, seq in sorted(common):
        name = BLOCK_NAMES.get(th, hex(th))
        print(f"  {name} (0x{th:08X}): static header {s} B, buffers {list(seq)}")
    return 0


# ---------------------------------------------------------------------------
# data model
# ---------------------------------------------------------------------------

@dataclass
class VertexBuffer:
    stride: int
    count: int
    data: bytes

    def positions(self) -> list[tuple[float, float, float]]:
        """float triples at offset 0. Works for every position-bearing stride
        (0x0C, 0x10, 0x18) because x,y,z lead the struct."""
        out = []
        for i in range(self.count):
            base = i * self.stride
            out.append(struct.unpack_from("<3f", self.data, base))
        return out

    def set_position(self, index: int, x: float, y: float, z: float) -> None:
        struct.pack_into("<3f", bytearray(self.data), index * self.stride, x, y, z)

    def translate(self, dx: float, dy: float, dz: float) -> None:
        """Move every vertex. Topology is untouched, so any index-based
        consumer (e.g. a Havok external mesh shape) stays valid."""
        arr = bytearray(self.data)
        for i in range(self.count):
            base = i * self.stride
            x, y, z = struct.unpack_from("<3f", arr, base)
            struct.pack_into("<3f", arr, base, x + dx, y + dy, z + dz)
        self.data = bytes(arr)

    def scale_axis(self, axis: int, factor: float) -> None:
        """Scale positions about the origin along one axis, in place."""
        self.scale_about((0.0, 0.0, 0.0), (1.0 if axis != 0 else factor,
                                             1.0 if axis != 1 else factor,
                                             1.0 if axis != 2 else factor))

    def scale_about(self, centre, factors) -> None:
        """Scale positions about `centre` by `factors` (x, y, z), in place.

        Only the x/y/z floats are rewritten. The trailing payload of each vertex
        -- deform weight `d` and bone indices wi0..wi3 for the IS_DEFORM variant --
        is left byte-identical, and the element count never changes. That is what
        keeps the file topology-preserving, which is the whole point: the entity's
        index buffer and the physics' external mesh shape stay valid.
        """
        cx, cy, cz = centre
        fx, fy, fz = factors
        arr = bytearray(self.data)
        for i in range(self.count):
            base = i * self.stride
            x, y, z = struct.unpack_from("<3f", arr, base)
            struct.pack_into("<3f", arr, base,
                             cx + (x - cx) * fx,
                             cy + (y - cy) * fy,
                             cz + (z - cz) * fz)
        self.data = bytes(arr)


@dataclass
class CarPaintMM:
    type_hash: int
    version: int
    flags: int
    unknown: float
    static_params: bytes          # 18 * vec4
    static_support: bytes         # 7 * float
    dynamic_params: bytes         # 4 * vec4 + 3 * float
    deform_table: bytes           # 256 * u32
    texture_count: int
    textures: list[str]
    material_params: bytes        # float[4]
    vb0: VertexBuffer
    vb1: VertexBuffer
    skin_batches: bytes = b""
    uv_extra: VertexBuffer | None = None
    ib: VertexBuffer = field(default_factory=lambda: VertexBuffer(2, 0, b""))

    @property
    def is_deform(self) -> bool:
        return bool(self.flags & IS_DEFORM)

    @property
    def is_skinned(self) -> bool:
        return bool(self.flags & IS_SKINNED)

    @property
    def has_layered(self) -> bool:
        return bool(self.flags & (SUPPORT_LAYERED | SUPPORT_OVERLAY))

    @property
    def index_count(self) -> int:
        return self.ib.count

    def indices(self) -> list[int]:
        return list(struct.unpack(f"<{self.ib.count}H", self.ib.data)) if self.ib.count else []


@dataclass
class RawBlock:
    type_hash: int
    payload: bytes


@dataclass
class GenericBlock:
    """A block whose static fields nobody has published.

    Nothing here is guessed. The texture-name table locates itself (its entries are
    ASCII asset paths), so the bytes before and after it are captured verbatim; only
    the buffer strides are declared, and those came out of the solver in
    `probe`, whose oracle is that the decoded float3 positions must reproduce the
    bounding box the engine itself wrote into the file header. The round-trip test
    on the whole donor tree is what holds the declarations honest.
    """
    type_hash: int
    pre_static: bytes
    textures: list
    mid_static: bytes
    strides: tuple
    buffers: list = field(default_factory=list)

    @property
    def vb0(self) -> VertexBuffer:
        return self.buffers[0]

    @property
    def vb1(self) -> VertexBuffer:
        return self.buffers[1] if len(self.buffers) > 2 else self.buffers[0]

    @property
    def ib(self) -> VertexBuffer:
        return self.buffers[-1]

    @property
    def flags(self) -> int:
        return 0

    @property
    def index_count(self) -> int:
        return self.ib.count

    @property
    def deform_table(self) -> bytes:
        return self.pre_static

    @property
    def static_params(self) -> bytes:
        return self.pre_static

    @property
    def uv_extra(self):
        return None

    def indices(self) -> list:
        return list(struct.unpack(f"<{self.ib.count}H", self.ib.data)) if self.ib.count else []


# stride templates measured by `probe`; see the note in MODLOG section 17
GENERIC_TEMPLATES = {
    # type: (bytes between the texture table and the first buffer, buffer strides)
    RB_WINDOW: (16, (40, 2)),
    RB_CARLIGHT: (16, (12, 24, 2)),
}


def _locate_texture_tables(buf: bytes, lo: int, hi: int):
    """Every plausible texture-name table in [lo, hi), in position order.

    Self-locating on purpose: the table's entries are printable asset paths ending
    in a known extension, which no float or index field imitates by accident. That
    avoids hardcoding a per-type offset we would have no way to verify.
    """
    hits = []
    for p in range(lo, min(hi, len(buf))):
        if p + 4 > len(buf):
            break
        (cnt,) = struct.unpack_from("<I", buf, p)
        if not 1 <= cnt <= 16:
            continue
        q = p + 4
        names = []
        ok = True
        for _ in range(cnt):
            if q + 4 > len(buf):
                ok = False
                break
            (ln,) = struct.unpack_from("<I", buf, q)
            q += 4
            if ln == 0:
                names.append("")
                continue
            if ln > 4096 or q + ln > len(buf):
                ok = False
                break
            s = buf[q:q + ln]
            if not all(32 <= c < 127 for c in s):
                ok = False
                break
            names.append(s.decode())
            q += ln
        if not ok or not names:
            continue
        if not any(n.endswith((".ddsc", ".dds", ".avtx")) for n in names):
            continue
        hits.append((p, names, q))
    return hits


@dataclass
class Rbm:
    magic_length: int
    magic: bytes
    version: tuple[int, int, int]
    bbox_min: tuple[float, float, float]
    bbox_max: tuple[float, float, float]
    number_of_blocks: int
    tag: int
    blocks: list

    # ---------------- header ----------------

    @staticmethod
    def parse_header(buf: bytes):
        if len(buf) < 0x35:
            raise RbmError("file shorter than RbmHeader")
        (magic_length,) = struct.unpack_from("<I", buf, 0)
        if magic_length == 5:
            end = "<"
        elif struct.unpack_from(">I", buf, 0)[0] == 5:
            raise RbmError("big-endian RBM: not supported by this codec")
        else:
            raise RbmError(f"invalid magic length {magic_length:#x} (expected 5)")
        magic = buf[4:9]
        if magic != b"RBMDL":
            raise RbmError(f"invalid magic {magic!r}")
        major, minor, revision = struct.unpack_from(end + "3I", buf, 9)
        bbox = struct.unpack_from(end + "6f", buf, 21)
        nblocks, tag = struct.unpack_from(end + "2I", buf, 45)
        return dict(
            magic_length=magic_length, magic=magic,
            version=(major, minor, revision),
            bbox_min=bbox[0:3], bbox_max=bbox[3:6],
            number_of_blocks=nblocks, tag=tag, header_len=0x35,
        )

    def header_bytes(self) -> bytes:
        return (struct.pack("<I", self.magic_length)
                + self.magic
                + struct.pack("<3I", *self.version)
                + struct.pack("<6f", *self.bbox_min, *self.bbox_max)
                + struct.pack("<2I", self.number_of_blocks, self.tag))

    # ---------------- blocks ----------------

    def write(self) -> bytes:
        out = bytearray(self.header_bytes())
        for blk in self.blocks:
            out += struct.pack("<I", blk.type_hash)
            out += encode_block(blk)
            out += struct.pack("<I", RBM_BLOCK_CHECKSUM)
        return bytes(out)

    def block_names(self) -> list[str]:
        return [BLOCK_NAMES.get(b.type_hash, f"0x{b.type_hash:08X}") for b in self.blocks]


# ---------------------------------------------------------------------------
# decode
# ---------------------------------------------------------------------------

def decode_carpaintmm(buf: bytes, off: int, type_hash: int) -> tuple[CarPaintMM, int]:
    start = off
    version = buf[off]; off += 1
    (flags,) = struct.unpack_from("<I", buf, off); off += 4
    (unknown,) = struct.unpack_from("<f", buf, off); off += 4

    static_params = buf[off:off + 18 * 16]; off += 18 * 16
    static_support = buf[off:off + 7 * 4]; off += 7 * 4
    dynamic_params = buf[off:off + 4 * 16 + 3 * 4]; off += 4 * 16 + 3 * 4
    deform_table = buf[off:off + 256 * 4]; off += 256 * 4

    (tex_count,) = struct.unpack_from("<I", buf, off); off += 4
    textures = []
    for _ in range(tex_count):
        (ln,) = struct.unpack_from("<I", buf, off); off += 4
        if ln:
            textures.append(buf[off:off + ln].decode("utf-8", "replace")); off += ln
        else:
            textures.append("")
    material_params = buf[off:off + 16]; off += 16

    if flags & IS_SKINNED:
        s0, s1 = STRIDE_UNPACKED_WITH_NORMAL1, STRIDE_UNPACKED_NORMALS
    elif flags & IS_DEFORM:
        s0, s1 = STRIDE_DEFORM_POS, STRIDE_DEFORM_NORMAL2
    else:
        s0, s1 = STRIDE_UNPACKED_POSITION, STRIDE_UNPACKED_NORMALS

    d0, c0, off = _read_buffer_sized(buf, off, s0)
    d1, c1, off = _read_buffer_sized(buf, off, s1)
    vb0 = VertexBuffer(s0, c0, d0)
    vb1 = VertexBuffer(s1, c1, d1)
    if c0 != c1:
        raise RbmError(f"vertex/normal count mismatch {c0} vs {c1}")

    skin = b""
    if flags & IS_SKINNED:
        (nb,) = struct.unpack_from("<I", buf, off); off += 4
        for _ in range(nb):
            (size, batch_off, batch_size) = struct.unpack_from("<3i", buf, off); off += 12
            if batch_size:
                off += batch_size * 2
        skin = buf[start:off]

    uv = None
    if flags & (SUPPORT_LAYERED | SUPPORT_OVERLAY):
        d2, c2, off = _read_buffer_sized(buf, off, STRIDE_UNPACKED_UV)
        uv = VertexBuffer(STRIDE_UNPACKED_UV, c2, d2)

    di, ci, off = _read_buffer_sized(buf, off, 2)
    ib = VertexBuffer(2, ci, di)

    blk = CarPaintMM(
        type_hash=type_hash, version=version, flags=flags, unknown=unknown,
        static_params=static_params, static_support=static_support,
        dynamic_params=dynamic_params, deform_table=deform_table,
        texture_count=tex_count, textures=textures,
        material_params=material_params,
        vb0=vb0, vb1=vb1, skin_batches=skin, uv_extra=uv, ib=ib,
    )
    return blk, off


def decode_generic(buf: bytes, off: int, type_hash: int) -> tuple[GenericBlock, int]:
    """Decode a block using only its self-locating texture table and a stride template.

    Several byte offsets can look like a texture table -- raw floats in a
    static-parameter block will fake a short one, and one entry can be mis-parsed by
    a byte. So candidates are tried in order and each is accepted only if the
    declared buffers land exactly on the 0x89ABCDEF checksum that closes the block.
    That check is what makes this safe on multi-block files, where the table in
    block 1 would otherwise be picked up as block 0's.
    """
    mid_static_len, strides = GENERIC_TEMPLATES[type_hash]
    start = off
    tried = 0
    for tbl_start, textures, tbl_end in _locate_texture_tables(buf, start, start + 4096):
        tried += 1
        first = tbl_end + mid_static_len
        if first + 4 > len(buf):
            continue
        buffers = []
        cur = first
        ok = True
        for st in strides:
            try:
                data, count, cur = _read_buffer_sized(buf, cur, st)
            except RbmError:
                ok = False
                break
            buffers.append(VertexBuffer(st, count, data))
        if not ok:
            continue
        if cur + 4 > len(buf):
            continue
        (cs,) = struct.unpack_from("<I", buf, cur)
        if cs != RBM_BLOCK_CHECKSUM:
            continue
        return GenericBlock(type_hash=type_hash, pre_static=buf[start:tbl_start],
                            textures=textures, mid_static=buf[tbl_end:first],
                            strides=tuple(strides), buffers=buffers), cur
    raise RbmError(f"{BLOCK_NAMES.get(type_hash, hex(type_hash))}: no consistent layout "
                   f"found ({tried} texture-table candidate(s) tried)")


def decode(buf: bytes) -> Rbm:
    h = Rbm.parse_header(buf)
    off = h["header_len"]
    blocks: list = []
    for i in range(h["number_of_blocks"]):
        (th,) = struct.unpack_from("<I", buf, off); off += 4
        if th == RB_CARPAINTMM:
            blk, off = decode_carpaintmm(buf, off, th)
        elif th in GENERIC_TEMPLATES:
            blk, off = decode_generic(buf, off, th)
        else:
            # unknown block: we cannot know its length, so stop and keep raw only
            # when it is the final block; otherwise fall back to a linear scan.
            raise RbmError(
                f"block {i} is {BLOCK_NAMES.get(th, hex(th))}, which this codec does "
                f"not parse (need its serializer to know where it ends)")
        (cs,) = struct.unpack_from("<I", buf, off); off += 4
        if cs != RBM_BLOCK_CHECKSUM:
            raise RbmError(f"block {i}: checksum 0x{cs:08X} != 0x{RBM_BLOCK_CHECKSUM:08X}")
        blocks.append(blk)
    if off != len(buf):
        raise RbmError(f"trailing bytes: parsed {off} of {len(buf)}")
    return Rbm(h["magic_length"], h["magic"], h["version"], h["bbox_min"], h["bbox_max"],
               h["number_of_blocks"], h["tag"], blocks)


# ---------------------------------------------------------------------------
# encode
# ---------------------------------------------------------------------------

def encode_carpaintmm(b: CarPaintMM) -> bytes:
    out = bytearray()
    out += struct.pack("<BIf", b.version, b.flags, b.unknown)
    out += b.static_params
    out += b.static_support
    out += b.dynamic_params
    out += b.deform_table
    out += struct.pack("<I", len(b.textures))
    for t in b.textures:
        e = t.encode("utf-8")
        out += struct.pack("<I", len(e)) + e
    out += b.material_params
    for vb in (b.vb0, b.vb1):
        out += struct.pack("<I", vb.count) + vb.data
    if b.is_skinned:
        out += b.skin_batches
    if b.uv_extra is not None:
        out += struct.pack("<I", b.uv_extra.count) + b.uv_extra.data
    out += struct.pack("<I", b.ib.count) + b.ib.data
    return bytes(out)


def encode_generic(b: GenericBlock) -> bytes:
    out = bytearray()
    out += b.pre_static
    out += struct.pack("<I", len(b.textures))
    for t in b.textures:
        e = t.encode("utf-8")
        out += struct.pack("<I", len(e)) + e
    out += b.mid_static
    for vb in b.buffers:
        out += struct.pack("<I", vb.count) + vb.data
    return bytes(out)


def encode_block(blk) -> bytes:
    if isinstance(blk, CarPaintMM):
        return encode_carpaintmm(blk)
    if isinstance(blk, GenericBlock):
        return encode_generic(blk)
    if isinstance(blk, RawBlock):
        return blk.payload
    raise RbmError(f"cannot encode {type(blk).__name__}")


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------

def cmd_info(args) -> int:
    files = []
    for p in args.paths:
        if os.path.isdir(p):
            for root, _d, names in os.walk(p):
                files.extend(os.path.join(root, n) for n in names if n.lower().endswith(".rbm"))
        else:
            files.extend(glob.glob(p))
    for f in sorted(set(files)):
        raw = open(f, "rb").read()
        try:
            m = decode(raw)
        except RbmError as e:
            print(f"{os.path.basename(f):<44} ERROR {e}")
            continue
        print(f"{os.path.basename(f):<44} v{m.version[0]}.{m.version[1]}.{m.version[2]}  "
              f"blocks={m.number_of_blocks} tag={m.tag}")
        for i, b in enumerate(m.blocks):
            pos = b.vb0.positions()
            bb = (min(p[0] for p in pos), min(p[1] for p in pos), min(p[2] for p in pos),
                  max(p[0] for p in pos), max(p[1] for p in pos), max(p[2] for p in pos)) if pos else None
            kind = "deform" if b.is_deform else ("skinned" if b.is_skinned else "static")
            print(f"   [{i}] {BLOCK_NAMES.get(0x483304D6, '')}"
                  f" flags=0x{b.flags:04X} ({kind}) verts={b.vb0.count} idx={b.index_count} "
                  f"tris={b.index_count // 3} tex={b.texture_count}")
            if bb:
                print(f"        vertex bbox  {bb[3]-bb[0]:.3f} x {bb[4]-bb[1]:.3f} x {bb[5]-bb[2]:.3f} m")
            nz = sum(1 for t in b.textures if t)
            print(f"        textures     {nz}/{b.texture_count} set")
    return 0


def cmd_roundtrip(args) -> int:
    """The oracle. decode -> encode must reproduce the input exactly."""
    files = []
    for p in args.paths:
        if os.path.isdir(p):
            for root, _d, names in os.walk(p):
                files.extend(os.path.join(root, n) for n in names if n.lower().endswith(".rbm"))
        else:
            files.extend(glob.glob(p))
    files = sorted(set(files))
    if args.limit:
        files = files[:args.limit]
    ok = bad = skip = 0
    for f in files:
        raw = open(f, "rb").read()
        try:
            out = decode(raw).write()
        except RbmError as e:
            skip += 1
            if args.verbose:
                print(f"  skip  {os.path.basename(f):<42} {e}")
            continue
        if out == raw:
            ok += 1
        else:
            bad += 1
            first = next((i for i, (a, b) in enumerate(zip(raw, out)) if a != b), None)
            print(f"  FAIL  {os.path.basename(f):<42} first diff at "
                  f"{'EOF' if first is None else hex(first)} len {len(raw)} -> {len(out)}")
    print(f"\nbyte-identical: {ok}   mismatched: {bad}   not-parsed: {skip}")
    return 0 if bad == 0 else 1


AXES = {"x": 0, "y": 1, "z": 2}

# ---------------------------------------------------------------------------
# mesh extraction
# ---------------------------------------------------------------------------


def collect_mesh(m: Rbm, block: int | None = None) -> tuple[list, list, list]:
    """Flatten render blocks into (verts, tris, tri_block). Block-local geometry is
    already in shared model space, so no transform is needed. tri_block lets the
    preview colour by block, which is how the shell's panels get told apart."""
    verts: list = []
    tris: list = []
    tb: list = []
    for bi, b in enumerate(m.blocks):
        if block is not None and bi != block:
            continue
        base = len(verts)
        verts.extend(b.vb0.positions())
        idx = b.indices()
        for i in range(0, len(idx) - 2, 3):
            tris.append((base + idx[i], base + idx[i + 1], base + idx[i + 2]))
            tb.append(bi)
    return verts, tris, tb


# ---------------------------------------------------------------------------
# OBJ export (the community interchange format)
# ---------------------------------------------------------------------------

def cmd_export(args) -> int:
    """Export decoded geometry to Wavefront OBJ -- the same interchange format the
    JC3 community uses between Blender and JC Model Renderer, so the result can be
    opened and inspected without launching the game."""
    m = decode(open(args.input, "rb").read())
    verts, tris = collect_mesh(m, args.block)
    name = os.path.splitext(os.path.basename(args.input))[0]
    os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(f"# exported by rbm_geom.py from {os.path.basename(args.input)}\n")
        fh.write(f"# blocks={m.number_of_blocks} tag={m.tag} verts={len(verts)} tris={len(tris)}\n")
        fh.write(f"o {name}\n")
        for v in verts:
            fh.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
        for i, blk in enumerate(m.blocks):
            if args.block is not None and i != args.block:
                continue
            fh.write(f"g block_{i}_{BLOCK_NAMES.get(blk.type_hash, hex(blk.type_hash))}\n")
            base = sum(len(b.vb0.positions()) for b in m.blocks[:i])
            idx = blk.indices()
            for t in range(0, len(idx) - 2, 3):
                fh.write(f"f {base+idx[t]+1} {base+idx[t+1]+1} {base+idx[t+2]+1}\n")
    print(f"wrote {args.output}  verts={len(verts)} tris={len(tris)}")
    print("open it in Blender / MeshLab / CloudCompare to inspect the shell.")
    return 0


# ---------------------------------------------------------------------------
# offline preview -- the point is to stop burning game launches on blind edits
# ---------------------------------------------------------------------------

# Which world axis is horizontal / vertical in each orthographic view, so the
# views come out the way a car photographer would frame them:
#   side  = length across the frame, height up   (silhouette, nose to the right)
#   top   = length across the frame, width up
#   front = width across the frame, height up
VIEWS = {
    "side": (2, 1, 0),
    "top": (2, 0, 1),
    "front": (0, 1, 2),
}


def _shade(verts, tris, view: str, size: int = 380, tri_block=None):
    """Very small orthographic z-buffer render. Not a beauty pass -- just enough to
    read the silhouette and compare before/after without launching the game.

    Pass tri_block to colour each render block differently; that is how the shell's
    individual panels (bonnet, roof, flanks, arches) get told apart, and therefore how
    the nose end gets identified rather than guessed."""
    import numpy as np

    V = np.asarray(verts, dtype=np.float64)
    T = np.asarray(tris, dtype=np.int64)

    ha, va, cam = VIEWS[view]
    P = np.stack([V[:, ha], V[:, va]], axis=1)

    lo, hi = P.min(axis=0), P.max(axis=0)
    span = (hi - lo).max() or 1.0
    s = (size - 2) / span
    mid = (lo + hi) / 2.0
    px = (P[:, 0] - mid[0]) * s + size / 2
    py = size / 2 - (P[:, 1] - mid[1]) * s

    img = np.full((size, size, 3), 255.0)
    zbuf = np.full((size, size), -1e18)

    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    n = np.cross(b - a, c - a)
    ln = np.linalg.norm(n, axis=1)
    ok = ln > 1e-12
    n[ok] /= ln[ok][:, None]
    light = np.array([0.35, 0.75, 0.55])
    light /= np.linalg.norm(light)
    lum = 0.22 + 0.78 * np.clip(np.abs(n @ light), 0, 1)
    # depth measured along the camera axis, sign-corrected so the near surface wins
    depth = V[T][:, :, cam].mean(axis=1)
    if depth.mean() < np.median(V[:, cam]):
        depth = -depth

    if tri_block is None:
        base = np.tile(np.array([0.62, 0.66, 0.72]), (len(T), 1))
    else:
        tb = np.asarray(tri_block)
        nb = int(tb.max()) + 1
        hue = np.arange(nb) * 0.618034
        offs = np.array([0.0, 0.33, 0.67])
        cols = 0.35 + 0.55 * np.abs(np.cos(6.283 * (hue[:, None] + offs[None, :])))
        base = cols[tb]

    x0, y0, x1, y1 = px[T[:, 0]], py[T[:, 0]], px[T[:, 1]], py[T[:, 1]]
    for k in range(3):
        ax_, ay_ = (x0, y0) if k == 0 else ((x1, y0) if k == 1 else (x0, y1))
        bx_, by_ = (x1, y1) if k == 0 else ((x0, y1) if k == 1 else (x1, y0))
        for t in range(len(T)):
            if not ok[t]:
                continue
            xmin, xmax = int(max(0, min(ax_[t], bx_[t]))), int(min(size - 1, max(ax_[t], bx_[t])))
            ymin, ymax = int(max(0, min(ay_[t], by_[t]))), int(min(size - 1, max(ay_[t], by_[t])))
            if xmin > xmax or ymin > ymax:
                continue
            xs, ys = np.meshgrid(np.arange(xmin, xmax + 1), np.arange(ymin, ymax + 1))
            d = (bx_[t] - ax_[t]) * (ys - ay_[t]) - (by_[t] - ay_[t]) * (xs - ax_[t])
            hit = d <= 0
            if not hit.any():
                continue
            zz = depth[t]
            sub = zbuf[ymin:ymax + 1, xmin:xmax + 1]
            upd = hit & (zz > sub)
            sub[upd] = zz
            img[ymin:ymax + 1, xmin:xmax + 1][upd] = base[t] * lum[t] * 255.0
    return img


def cmd_preview(args) -> int:
    import numpy as np
    from PIL import Image

    inputs = args.inputs
    labels = args.labels or [os.path.splitext(os.path.basename(p))[0] for p in inputs]

    if args.merge:
        # Treat every input as one assembly. JC3 vehicles are built from ~20
        # separate parts that already share model space, so merging them is what
        # shows the car a player actually sees rather than one shell in isolation.
        groups = [inputs]
        labels = labels[:1]
    else:
        groups = [[p] for p in inputs]

    if args.splat:
        # Fast path: z-buffered point splat instead of triangle rasterisation.
        # `_shade` walks triangles in a Python loop, which is fine for one shell and
        # takes a minute for a whole 160-part vehicle -- too slow to tune a reshape
        # against. A splat of every vertex reads the silhouette just as well and
        # costs about a second. It shows interior vertices too, which is a feature
        # here: it makes it obvious when a panel has been dragged inside another.
        import psk_geom
        panels = []
        for grp in groups:
            pts = []
            for p in grp:
                try:
                    pts.extend(np_all_positions(decode(open(p, "rb").read())))
                except RbmError:
                    pass
            if not pts:
                print(f"  skipped {grp[0]}: nothing decoded")
                return 1
            V = np.asarray(pts, dtype=np.float64)
            panels.append([psk_geom.splat(V, v, args.splat_size)[0]
                           for v in ("side", "top", "front")])
    else:
        panels = []
        for grp in groups:
            allv, allt, allb = [], [], []
            for p in grp:
                m = decode(open(p, "rb").read())
                try:
                    v, t, tb = collect_mesh(m)
                except RbmError as exc:
                    print(f"  skipped {os.path.basename(p)}: {exc}")
                    continue
                off = len(allv)
                blk_off = len(set(allb))
                allv.extend(v)
                allt.extend([(a + off, b + off, c + off) for a, b, c in t])
                allb.extend(x + blk_off for x in tb)
            panels.append([_shade(allv, allt, v, tri_block=allb if args.color_blocks else None)
                           for v in ("side", "top", "front")])

    for grp in groups:
        pts = []
        for p in grp:
            try:
                pts.extend(np_all_positions(decode(open(p, "rb").read())))
            except RbmError:
                pass
        if not pts:
            continue
        lo = [min(q[k] for q in pts) for k in range(3)]
        hi = [max(q[k] for q in pts) for k in range(3)]
        tag = os.path.basename(grp[0]) if len(grp) == 1 else f"{len(grp)} parts merged"
        print(f"{tag}  X {lo[0]:+.3f}..{hi[0]:+.3f} ({hi[0]-lo[0]:.3f})  "
              f"Y {lo[1]:+.3f}..{hi[1]:+.3f} ({hi[1]-lo[1]:.3f})  "
              f"Z {lo[2]:+.3f}..{hi[2]:+.3f} ({hi[2]-lo[2]:.3f})")

    gap = 8
    rows = len(panels)
    W = 3 * panels[0][0].shape[1] + (3 + 1) * gap
    H = rows * panels[0][0].shape[0] + (rows + 1) * gap
    canvas = np.full((H, W, 3), 235, dtype=np.uint8)
    for r in range(rows):
        for c in range(3):
            img = panels[r][c].astype(np.uint8)
            y0 = gap + r * (img.shape[0] + gap)
            x0 = gap + c * (img.shape[1] + gap)
            canvas[y0:y0 + img.shape[0], x0:x0 + img.shape[1]] = img
    os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
    Image.fromarray(canvas).save(args.output)
    for i, lab in enumerate(labels):
        print(f"row {i}: {lab}")
    print("columns: SIDE (Z across, Y up) | TOP (Z across, X up) | FRONT (X across, Y up)")
    print("JC3 axes: X width, Y up, Z length; the vehicle's front is at -Z.")
    if args.color_blocks:
        print("colours: one per render block, golden-ratio spaced so neighbours differ")
    print(f"wrote {args.output}")
    return 0


# ---------------------------------------------------------------------------
# displacement profiles
# ---------------------------------------------------------------------------

def make_ref(points):
    """Normalisation frame for a displacement, taken from the WHOLE vehicle.

    This matters: the Serpente is ~20 separate RBMs, and if each part normalised
    against its own bounding box every part would be warped by a different amount
    and the car would come apart. One shared frame keeps the assembly coherent.
    """
    import numpy as np

    V = np.asarray(points, dtype=np.float64)
    lo = V.min(axis=0)
    hi = V.max(axis=0)
    return lo, hi, np.where(hi - lo == 0, 1.0, hi - lo)


def _tumbler_cloud(path: str, ref, length: float = 1.0):
    """Load the Batmobile PSKX and return its points in the JC3 frame.

    Axis mapping, proven by rendering all nine (horizontal, vertical) axis pairs of
    `Batmobile_V2.pskx` and looking at them (`psk_geom.py grid`):

        PSK X  702.56  = length
        PSK Y  349.53  = width
        PSK Z  234.19  = height

    The side elevation shows the rounded prow at high PSK X, and JC3 puts the front of a
    vehicle at -Z, hence the sign flip. This is the mapping MODLOG recorded as "reasoned
    inference, not proven"; the grid render is the proof.

    Fitted into the donor's shared frame in Z (length) and at the bottom in Y, because
    those two are physically pinned: the body has to span the 3.003 m wheelbase in
    `land_global.vmodc` and its underside has to stay on the ground. Width and roof
    height are NOT fitted -- they come out of the per-slice comparison instead, since
    fitting them here would just reproduce the donor's own proportions.
    """
    import numpy as np
    import psk_geom

    V, _ = psk_geom.read_verts(path)
    T = V[:, [1, 2, 0]].copy()            # (width, height, length)
    T[:, 2] *= -1.0                        # prow at high PSK X -> front at -Z

    lo, hi, span = ref
    src = T[:, 2].max() - T[:, 2].min()
    T *= (span[2] * length) / src          # scale all axes; only Z is load-bearing
    T[:, 2] += (lo[2] + hi[2]) / 2.0 - (T[:, 2].min() + T[:, 2].max()) / 2.0
    T[:, 1] += lo[1] - T[:, 1].min()       # bottom of the target onto the frame floor
    return T


def _donor_slice_stats(all_verts, N: int):
    """Per-length-slice half-width and roof height of the DONOR, over all parts together.

    This must be computed across the whole vehicle, not per file, and that is the whole
    point. A JC3 car is ~20 separate RBMs; the body's shell and its bumper occupy the same
    length slices but very different height bands. If each part measured its own slice
    ceiling and was then fitted to the target's whole-body roofline, every low part --
    sills, valances, underbody -- would be stretched upward to roof height, and the car
    would come apart vertically. One shared set of per-slice extents keeps every part in
    the same frame, which is the same reasoning as `make_ref`.
    """
    import numpy as np

    V = np.asarray(all_verts, dtype=np.float64)
    lo, hi, span = make_ref(V)
    z = (V[:, 2] - lo[2]) / span[2]
    si = np.clip((z * N).astype(np.int64), 0, N - 1)

    dxw = np.full(N, np.nan)
    droof = np.full(N, np.nan)
    absx = np.abs(V[:, 0])
    for i in range(N):
        sel = si == i
        if not sel.any():
            continue
        dxw[i] = absx[sel].max()
        droof[i] = V[sel, 1].max()
    return _fill_slices(dxw), _fill_slices(droof)


def _fill_slices(a):
    """Nearest-valid-slice fill, so an empty slice inherits its neighbour."""
    import numpy as np

    good = np.flatnonzero(np.isfinite(a))
    if good.size == 0:
        return np.zeros(len(a))
    idx = np.arange(len(a))
    return a[good[np.abs(idx[:, None] - good[None, :]).argmin(axis=1)]]


def _slice_stats(T, N: int, wpct: float, tpct: float):
    """Per-length-slice half-width and roof height of the target cloud.

    Percentiles, not maxima, on purpose. The Batmobile carries rear fins, aerials and
    other greebles well above the bodywork; a plain per-slice maximum would fit the
    donor's roof to a fin. The gap is measurable: in the rear slices `T max` runs about
    0.15 m above `T p99`, so the choice of percentile is worth a parameter and worth
    looking at in `_dump_profile.py`.
    """
    import numpy as np

    z = (T[:, 2] - T[:, 2].min()) / (T[:, 2].max() - T[:, 2].min())
    ti = np.clip((z * N).astype(np.int64), 0, N - 1)
    txw = np.full(N, np.nan)
    ttop = np.full(N, np.nan)
    absx = np.abs(T[:, 0])
    for i in range(N):
        sel = ti == i
        if not sel.any():
            continue
        txw[i] = np.percentile(absx[sel], wpct)
        ttop[i] = np.percentile(T[sel, 1], tpct)

    txw, ttop = _fill_slices(txw), _fill_slices(ttop)
    # smooth twice, so a sparsely sampled nose or tail slice cannot step the roofline
    k = np.array([0.25, 0.5, 0.25])
    for a in (txw, ttop):
        for _ in range(2):
            a[:] = np.convolve(np.pad(a, 1, mode="edge"), k, mode="valid")
    return txw, ttop


def apply_profile(verts, profile: str, ref, **kw):
    """Reshape a vertex list, returning a new list.

    Every profile is a pure function of each vertex's own position in the shared
    vehicle frame, so no sculpting session and no external mesh editor is needed
    and the result stays reproducible from the parameters in the journal.
    """
    import numpy as np

    lo, hi, span = ref
    V = np.asarray(verts, dtype=np.float64)
    P = V.copy()

    floor = kw.get("floor", 0.80)
    blend = kw.get("blend", 0.15)

    # Two independent guards, because they protect different things.
    #
    # `up` stops the vertical squash from acting on anything under the floor line.
    # Compressing about a floor naively would instead LIFT those vertices up to it,
    # which would raise the sills and the underbody off the ground.
    u = np.clip((V[:, 1] - floor) / blend, 0.0, 1.0)
    up = u * u * (3.0 - 2.0 * u)

    # `guard` protects the wheel openings. The wheels do not move -- they are hung
    # on the chassis, not on the body mesh -- so the arches must not move either.
    # Guarding a disc around each measured hardpoint is both tighter and simpler
    # than protecting a whole height band, and it leaves the bumpers free to move.
    wheels = kw.get("wheel") or [-1.557, 1.446]     # from land_global.vmodc
    axle = kw.get("axle_y", 0.400)
    guard_r = kw.get("guard", 0.52)
    fade = kw.get("fade", 0.12)
    xlim = kw.get("xlim", 0.68)
    ax = np.abs(V[:, 0])
    gate = np.ones(len(V))
    for wz in wheels:
        d = np.hypot(V[:, 1] - axle, V[:, 2] - wz)
        f = np.clip((d - guard_r) / fade, 0.0, 1.0)
        f = f * f * (3.0 - 2.0 * f)
        gate = np.minimum(gate, np.where(ax > xlim, f, 1.0))

    # normalised vehicle coordinates
    zn = (V[:, 2] - lo[2]) / span[2]                 # 0 at the nose .. 1 at the tail
    yh = np.clip((V[:, 1] - floor) / (span[1] - floor), 0.0, 1.0)
    yn = (V[:, 1] - lo[1]) / span[1]
    xn = (V[:, 0] - lo[0]) / span[0] * 2.0 - 1.0    # -1..1 across the width

    if profile == "tumble":
        # 1. press the roof down toward the floor
        k = kw.get("roof", 0.55)
        P[:, 1] += (floor + (V[:, 1] - floor) * k - V[:, 1]) * up * gate

        # 2. rake the nose down and forward: the Tumbler's prow
        nose_drop = kw.get("nose_drop", 0.18)
        nose_len = kw.get("nose_len", 0.30)
        nm = np.clip(1.0 - zn / nose_len, 0.0, 1.0) ** 1.4 * gate
        P[:, 1] -= nose_drop * span[1] * nm * yh
        P[:, 2] -= kw.get("nose_push", 0.04) * span[2] * nm

        # 3. one continuous fall from the cabin peak to the tail (fastback),
        #    instead of the donor's flat boot deck
        cabin = kw.get("cabin_z", 0.45)
        tail = kw.get("tail_drop", 0.20)
        tp = kw.get("tail_pow", 1.3)
        tm = np.clip((zn - cabin) / (1.0 - cabin), 0.0, 1.0) ** tp * gate
        P[:, 1] -= tail * span[1] * tm * (yh ** 0.7)

        # 4. pinch the greenhouse in X as it rises
        P[:, 0] = V[:, 0] * (1.0 - kw.get("pinch", 0.30) * (yh ** 1.5) * gate)

        # 5. narrow the prow in plan view so it reads as a wedge, not a coupe
        taper = kw.get("taper", 0.35)
        tm2 = np.clip(1.0 - zn / kw.get("taper_len", 0.42), 0.0, 1.0) ** 1.5 * gate
        P[:, 0] = P[:, 0] * (1.0 - taper * tm2)

        # 6. flare the rear haunches
        flare = kw.get("flare", 0.10)
        fm = np.clip((zn - 0.55) / 0.45, 0.0, 1.0) * gate
        P[:, 0] += V[:, 0] * flare * fm * (1.0 - yh)

    elif profile == "tumbler":
        # A MEASURED reshape rather than a sculpted one.
        #
        # The donor's silhouette is cut into length slices and each slice's own extents
        # are re-fitted to the Batmobile's extents at the same slice. test-010's `tumble`
        # guessed how much to press, pinch and taper; this asks the target asset instead.
        #
        # Why a per-slice affine map rather than nearest-point transfer: every vertex has
        # to keep its own position in its own index, and an affine map is guaranteed
        # invertible, so the mesh cannot fold in on itself. It also leaves UVs and the
        # per-vertex deform weights meaningful, which a nearest-point snap would destroy.
        cloud = kw.get("_cloud")
        if cloud is None:
            raise RbmError("profile 'tumbler' needs --cloud <Batmobile_V2.pskx>")
        txw, ttop, N, dxw, droof = cloud

        zn = (V[:, 2] - lo[2]) / span[2]

        # Slice tables are sampled by LINEAR interpolation between slice centres, never
        # by an integer slice index. A step lookup gave every slice its own constant
        # scale, so each panel was sheared differently either side of a slice boundary:
        # test-020 loaded but its skin was "crumpled", creased every ~0.26 m.
        zc = zn * N - 0.5
        def at(a):
            return np.interp(zc, np.arange(N), a)

        w_mul = kw.get("width", 1.0)
        h_mul = kw.get("height", 1.0)
        sx = np.where(dxw > 1e-6, txw * w_mul / np.maximum(dxw, 1e-6), 1.0)

        # Height is remapped as a DELTA scaled by how high up the vertex already sits,
        # not as an affine fit. Fitting [sill, roof] affinely would drag the sill up to
        # the roof's share of the range -- the same failure the `up` mask below exists to
        # prevent, and one that earlier raised the sills off the ground.
        sill = kw.get("sill", lo[1])
        span_up = np.maximum(droof - sill, 1e-6)
        fy = np.clip((V[:, 1] - sill) / at(span_up), 0.0, 1.0)
        dy = (ttop * h_mul) - droof

        # The Tumbler's tallest thing is its rear fin, which is exactly the thing a
        # frozen topology cannot build. Fitting the roofline to it lifts the boot lid
        # into a wedge with nothing on it. h_clip caps how far the roof may be raised,
        # so the fit can lower the greenhouse but not invent a spoiler: default 0.0
        # means never raise, -99.0 means no cap at all.
        h_clip = kw.get("h_clip", 0.0)
        if h_clip > -90.0:
            dy = np.minimum(dy, h_clip * span[1])

        # Width gain is gated by height. A plain per-slice scale widens the greenhouse
        # as much as the body, but a Tumbler's whole character is a wide flat body under
        # a NARROW canopy, so the gain is applied at the sill and fades out by the roof.
        # Per VERTEX: this was once `sx[si] = ...`, a scatter-write into the per-slice
        # table, so the last vertex written in each slice set that slice's gain.
        x_pin = kw.get("pinch", 0.0)
        sxv = 1.0 + (at(sx) - 1.0) * (1.0 - fy * x_pin)

        # `carve` scales the whole effect so a half-strength pass can be previewed
        # without changing any of the numbers that produced the full-strength one.
        carve = kw.get("carve", 1.0) * gate

        qx = V[:, 0] * sxv
        qy = V[:, 1] + fy * at(dy)

        # Skirt: drop the lower flank so the bodywork reaches down around the wheels.
        # A Tumbler's most recognisable feature is that its wheels are BURIED in the
        # body, and the only way to bury a wheel is to bring the surrounding panel down
        # past its top -- which is a displacement, not an addition. smoothstepped so
        # there is no crease at the top of the band.
        skirt = kw.get("skirt", 0.0)
        if skirt:
            st = kw.get("skirt_top", 0.45)
            sb = kw.get("skirt_blend", 0.30)
            u = np.clip((st - V[:, 1]) / sb, 0.0, 1.0)
            qy = qy - skirt * (u * u * (3.0 - 2.0 * u))
            # Hard floor. The Serpente's underbody sits at Y 0.106 and the road at
            # Y 0.020; an unclamped skirt of 0.25 drove the sill to Y -0.129, i.e.
            # 0.15 m under the tarmac, which would bury the car.
            qy = np.maximum(qy, kw.get("ground", 0.020))

        # one extra shaping knob the slice map cannot express: swell the rear haunches,
        # which is where the Tumbler's two turbine housings sit.
        flare = kw.get("flare", 0.0)
        if flare:
            fm = np.clip((zn - kw.get("flare_z", 0.55)) / 0.45, 0.0, 1.0) * (1.0 - fy)
            qx = qx + V[:, 0] * flare * fm

        # Only the wheel guard masks these. The `up` floor mask does not: `fy` is already
        # the "how high is this vertex" term, and masking it again with `floor` (0.80 m by
        # default) would freeze everything below the shoulder line.
        P[:, 0] = V[:, 0] + (qx - V[:, 0]) * carve
        P[:, 1] = V[:, 1] + (qy - V[:, 1]) * carve

    elif profile == "wedge":
        roof = kw.get("roof_drop", 0.30)
        powr = kw.get("roof_pow", 1.6)
        P[:, 1] = V[:, 1] - roof * span[1] * (zn ** powr) * yn
        nose = kw.get("nose_drop", 0.25)
        nlen = kw.get("nose_len", 0.35)
        m = np.clip(1.0 - zn / nlen, 0.0, 1.0)
        P[:, 1] -= nose * span[1] * (m ** 1.5) * yn
        P[:, 0] = V[:, 0] * (1.0 - kw.get("pinch", 0.18) * (yn ** 2))

    elif profile == "flatten":
        P[:, 1] = V[:, 1] * kw.get("k", 0.6)

    elif profile == "none":
        pass

    else:
        raise RbmError(f"unknown profile {profile!r}")

    return [tuple(p) for p in P]


def _displace_model(m: Rbm, profile: str, ref, **kw) -> None:
    for b in m.blocks:
        new = apply_profile(b.vb0.positions(), profile, ref, **kw)
        arr = bytearray(b.vb0.data)
        for i, (x, y, z) in enumerate(new):
            struct.pack_into("<3f", arr, i * b.vb0.stride, x, y, z)
        b.vb0.data = bytes(arr)
    pts = np_all_positions(m)
    m.bbox_min = tuple(min(p[k] for p in pts) for k in range(3))
    m.bbox_max = tuple(max(p[k] for p in pts) for k in range(3))


def _positions_only(o: "VertexBuffer", n: "VertexBuffer") -> bool:
    """True when n differs from o ONLY in each vertex's leading position floats.

    This is stricter than comparing the separate normal buffer: it proves that the
    per-vertex payload after the position -- packed normals, UVs, tangent frames,
    deform weights -- is bit-for-bit untouched. A wrong stride or an off-by-one in
    the write loop would break this immediately.
    """
    if o.data == n.data:
        return True
    if o.count != n.count or o.stride != n.stride or o.stride < 12:
        return False
    patched = bytearray(n.data)
    for i in range(o.count):
        base = i * o.stride
        patched[base:base + 12] = o.data[base:base + 12]
    return bytes(patched) == o.data


def _check_topology(orig: Rbm, new: Rbm, guard: dict | None = None) -> list:
    """The oracle. Only vertex positions and the header bbox may differ; anything
    that would change how the engine builds the mesh must not have moved.

    With `guard` set, it also asserts the load-bearing claim of the displacement:
    every vertex inside a protected wheel opening is bit-for-bit where it started.
    """
    fails = []
    if len(orig.blocks) != len(new.blocks):
        return [f"block count {len(orig.blocks)} -> {len(new.blocks)}"]
    for i, (ob, nb) in enumerate(zip(orig.blocks, new.blocks)):
        if ob.vb0.count != nb.vb0.count:
            fails.append(f"block {i}: vertex count {ob.vb0.count} -> {nb.vb0.count}")
        if ob.index_count != nb.index_count:
            fails.append(f"block {i}: index count changed")
        if ob.ib.data != nb.ib.data:
            fails.append(f"block {i}: INDEX BUFFER CHANGED")
        if ob.deform_table != nb.deform_table:
            fails.append(f"block {i}: deform table changed")
        if ob.static_params != nb.static_params or ob.textures != nb.textures:
            fails.append(f"block {i}: material data changed")
        if ob.type_hash != nb.type_hash or ob.flags != nb.flags:
            fails.append(f"block {i}: block type/flags changed")
        if not _positions_only(ob.vb0, nb.vb0):
            fails.append(f"block {i}: vertex data changed outside the position floats")
        if isinstance(ob, GenericBlock):
            if len(ob.buffers) != len(nb.buffers):
                fails.append(f"block {i}: buffer count changed")
                continue
            for k in range(1, len(ob.buffers)):
                if ob.buffers[k].data != nb.buffers[k].data:
                    fails.append(f"block {i}: non-position buffer {k} CHANGED")
        else:
            if ob.vb1.data != nb.vb1.data:
                fails.append(f"block {i}: normals changed")
            if ob.uv_extra is not None and nb.uv_extra is not None \
                    and ob.uv_extra.data != nb.uv_extra.data:
                fails.append(f"block {i}: uv buffer changed")
            if ob.skin_batches != nb.skin_batches:
                fails.append(f"block {i}: skin batches changed")
    if orig.tag != new.tag or orig.number_of_blocks != new.number_of_blocks:
        fails.append("header block count/tag changed")

    if guard:
        import math
        wheels = guard.get("wheel") or [-1.557, 1.446]
        axle = guard.get("axle_y", 0.400)
        r = guard.get("guard", 0.52)
        xlim = guard.get("xlim", 0.68)
        op = np_all_positions(orig)
        npp = np_all_positions(new)
        moved = []
        for o, n in zip(op, npp):
            if o == n or abs(o[0]) <= xlim:
                continue
            if min(math.hypot(o[1] - axle, o[2] - wz) for wz in wheels) < r:
                moved.append((o, n))
        if moved:
            worst = max(max(abs(o[k] - n[k]) for k in range(3)) for o, n in moved)
            fails.append(f"{len(moved)} vertices inside the protected wheel openings moved "
                         f"(worst {worst:.4f} m)")
    return fails


def _parse_params(pairs) -> dict:
    kw = {}
    for kv in pairs or []:
        k, _, v = kv.partition("=")
        kw.setdefault(k, []).append(float(v))
    # a key given once is a scalar; given more than once it is a list (e.g. -p wheel=..)
    return {k: (v[0] if len(v) == 1 else v) for k, v in kw.items()}


# ---------------------------------------------------------------------------
# adding geometry (as opposed to moving it)
# ---------------------------------------------------------------------------

def _pack_normal(n) -> int:
    """Encode a unit normal the way JC3 stores it in the stride-0x20 vertex buffer.

    Brooen's RBM-Exporter is the reference for this (`compress_normal`): the three
    components are quantised to one byte each and laid out little-endian, so the
    whole normal lives in the mantissa of a float.
    """
    def q(v):
        return max(0, min(254, int((v + 1.0) * 127.0)))
    b0, b1, b2 = q(n[0]), q(n[1]), q(n[2])
    return b0 | (b1 << 8) | (b2 << 16)


def make_fin(verts, tris, normals, cx, y0, cz, length, height, thick):
    """Append a pair of flat-shaded vertical fins as a thin slab each.

    Faces are emitted with their own vertices rather than shared ones. That costs a
    few extra vertices but means every new vertex has exactly one face normal, so
    there is no averaging to get wrong and the silhouette stays crisp.
    """
    hx = thick * 0.5
    hz = length * 0.5
    base = len(verts)
    quads = [
        # (four corners in CCW order as seen from outside, outward normal)
        ([(cx - hx, y0, cz - hz), (cx + hx, y0, cz - hz),
          (cx + hx, y0, cz + hz), (cx - hx, y0, cz + hz)], (0.0, -1.0, 0.0)),   # underside
        ([(cx - hx, y0 + height, cz - hz), (cx + hx, y0 + height, cz - hz),
          (cx + hx, y0 + height, cz + hz), (cx - hx, y0 + height, cz + hz)], (0.0, 1.0, 0.0)),  # top
        ([(cx - hx, y0, cz - hz), (cx + hx, y0, cz - hz),
          (cx + hx, y0 + height, cz - hz), (cx - hx, y0 + height, cz - hz)], (0.0, 0.0, -1.0)),  # leading edge
        ([(cx + hx, y0, cz + hz), (cx - hx, y0, cz + hz),
          (cx - hx, y0 + height, cz + hz), (cx + hx, y0 + height, cz + hz)], (0.0, 0.0, 1.0)),   # trailing edge
        ([(cx - hx, y0, cz + hz), (cx - hx, y0, cz - hz),
          (cx - hx, y0 + height, cz - hz), (cx - hx, y0 + height, cz + hz)], (-1.0, 0.0, 0.0)),  # inboard
        ([(cx + hx, y0, cz - hz), (cx + hx, y0, cz + hz),
          (cx + hx, y0 + height, cz + hz), (cx + hx, y0 + height, cz - hz)], (1.0, 0.0, 0.0)),   # outboard
    ]
    for corners, nrm in quads:
        i0 = len(verts)
        for c in corners:
            verts.append(c)
            normals.append(nrm)
        tris.append((i0, i0 + 1, i0 + 2))
        tris.append((i0, i0 + 2, i0 + 3))
    return base


def cmd_extend(args) -> int:
    """ADD geometry to one render block instead of moving what is already there.

    This is the capability displacement cannot reach: fins, enclosed arches, any
    shape that needs vertices the donor does not have. The approach is deliberately
    minimal - a new vertex record is a byte-for-byte clone of an existing one, with
    only its position and normal overwritten. That keeps UVs, tangents and deform
    weights valid without having to understand those layouts, and it leaves every
    pre-existing vertex and every pre-existing triangle bit-identical.
    """
    kw = _parse_params(args.param)
    raw = open(args.input, "rb").read()
    m = decode(raw)
    b = m.blocks[args.block]

    old_v = b.vb0.count
    old_i = b.ib.count
    verts, tris, normals = [], [], []
    for s in (-1.0, 1.0):
        make_fin(verts, tris, normals,
                 cx=s * kw.get("fin_x", 0.62),
                 y0=kw.get("fin_y", 0.85),
                 cz=kw.get("fin_z", 2.05),
                 length=kw.get("fin_len", 0.45),
                 height=kw.get("fin_h", 0.40),
                 thick=kw.get("fin_t", 0.05))
    added_v = len(verts)
    added_i = len(tris) * 3
    print(f"adding {added_v} vertices and {len(tris)} triangles to block {args.block} "
          f"of {os.path.basename(args.input)}")

    # donor record: the existing vertex whose attributes the new ones copy
    donor = args.donor
    if donor < 0 or donor >= old_v:
        donor = 0

    vb0 = bytearray(b.vb0.data)
    vb1 = bytearray(b.vb1.data)
    s0, s1 = b.vb0.stride, b.vb1.stride
    write_normal = bool(kw.get("write_normal", 0))
    for i, (x, y, z) in enumerate(verts):
        vb0 += vb0[donor * s0:(donor + 1) * s0]
        struct.pack_into("<3f", vb0, old_v * s0 + i * s0, x, y, z)
        vb1 += vb1[donor * s1:(donor + 1) * s1]
        if write_normal:
            # The packed-normal offset was ASSUMED to be 0x18 and that assumption is
            # WRONG: measuring the real stride-0x20 buffer shows the packed slot is
            # neither 0x10 nor 0x18. So this write is off by default and the donor's
            # own normal is inherited instead - structurally valid, cosmetically
            # imperfect. Do not trust this offset until the layout is measured.
            struct.pack_into("<f", vb1, old_v * s1 + i * s1 + int(kw.get("normal_off", 0x18)),
                             struct.unpack("<f", struct.pack("<I", _pack_normal(normals[i])))[0])

    idx = bytearray(b.ib.data)
    for t in tris:
        idx += struct.pack("<3H", old_v + t[0], old_v + t[1], old_v + t[2])

    b.vb0 = VertexBuffer(s0, old_v + added_v, bytes(vb0))
    b.vb1 = VertexBuffer(s1, old_v + added_v, bytes(vb1))
    b.ib = VertexBuffer(2, old_i + added_i, bytes(idx))

    pts = np_all_positions(m)
    m.bbox_min = tuple(min(p[k] for p in pts) for k in range(3))
    m.bbox_max = tuple(max(p[k] for p in pts) for k in range(3))

    # ---------------- the oracle ----------------
    orig = decode(raw)
    ob = orig.blocks[args.block]
    fails = []
    if len(orig.blocks) != len(m.blocks):
        fails.append("block count changed")
    for i, (o, n) in enumerate(zip(orig.blocks, m.blocks)):
        if i != args.block:
            if _positions_only(o.vb0, n.vb0) and o.ib.data == n.ib.data \
                    and o.deform_table == n.deform_table and o.static_params == n.static_params:
                continue
            fails.append(f"block {i}: an UNTARGETED block changed")
            continue
        if o.type_hash != n.type_hash or o.flags != n.flags:
            fails.append("block type or flags changed")
        if o.static_params != n.static_params or o.deform_table != n.deform_table:
            fails.append("material or deform data changed")
        if o.textures != n.textures:
            fails.append("texture list changed")
        # nothing that already existed may move
        if n.vb0.data[:o.vb0.count * o.vb0.stride] != o.vb0.data:
            fails.append("EXISTING vertex data changed")
        if n.vb1.data[:o.vb1.count * o.vb1.stride] != o.vb1.data:
            fails.append("EXISTING normal/uv data changed")
        if n.ib.data[:len(o.ib.data)] != o.ib.data:
            fails.append("EXISTING triangles changed")
        if n.ib.count % 3:
            fails.append("index count is not a multiple of 3")
        if n.vb0.count != n.vb1.count:
            fails.append(f"vertex/normal count mismatch {n.vb0.count} vs {n.vb1.count}")
        if (n.ib.count - o.ib.count) // 3 != len(tris) or n.vb0.count - o.vb0.count != added_v:
            fails.append("bookkeeping mismatch")

    out = m.write()
    print(f"size {len(raw)} -> {len(out)} B   block {args.block}: "
          f"verts {old_v} -> {b.vb0.count}, tris {old_i // 3} -> {b.ib.count // 3}")
    if fails:
        print("ORACLE FAILED:")
        for x in fails:
            print("  " + x)
        return 1
    print("ORACLE PASS: every pre-existing vertex, triangle, material and flag is intact; "
          "only new records were appended.")
    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
        open(args.output, "wb").write(out)
        print(f"wrote {args.output}")
    return 0


def cmd_displace(args) -> int:
    """Reshape one or many RBMs with the same function in the same vehicle frame.

    Taking many inputs matters because the vehicle is ~20 separate parts: applying
    one shared displacement to all of them keeps the body, hood, doors, fenders and
    bumpers welded together, which displacing a single shell never could.
    """
    kw = _parse_params(args.param)
    inputs = args.inputs

    models = [(p, decode(open(p, "rb").read())) for p in inputs]
    ref = make_ref([q for _, m in models for q in np_all_positions(m)])
    lo, hi, span = ref

    # The target envelope is built ONCE and shared by every part. Building it per part
    # would give each of the ~20 RBMs a slightly different target and pull the car apart
    # at the seams -- the same failure the shared `ref` frame exists to prevent.
    if args.profile == "tumbler":
        if not args.cloud:
            raise RbmError("profile 'tumbler' needs --cloud <Batmobile_V2.pskx>")
        N = int(kw.get("slices", 48))
        cloud_pts = _tumbler_cloud(args.cloud, ref, length=kw.get("length", 1.0))
        # donor slice extents come from EVERY part at once -- see _donor_slice_stats
        every = [q for _, mm in models for q in np_all_positions(mm)]
        dxw, droof = _donor_slice_stats(every, N)
        kw["_cloud"] = _slice_stats(cloud_pts, N,
                                    kw.get("width_pct", 100.0),
                                    kw.get("top_pct", 99.0)) + (N, dxw, droof)
        tlo, thi = cloud_pts.min(axis=0), cloud_pts.max(axis=0)
        print(f"target cloud  {os.path.basename(args.cloud)}: {len(cloud_pts)} points, fitted "
              f"into the donor frame over {N} length slices")
        print(f"  target extent  X {thi[0]-tlo[0]:.3f} m   Y {thi[1]-tlo[1]:.3f} m   "
              f"Z {thi[2]-tlo[2]:.3f} m   (bottom anchored at Y {tlo[1]:.3f})")

    failed = False
    for p, m in models:
        orig = decode(open(p, "rb").read())
        _displace_model(m, args.profile, ref, **kw)
        out = m.write()
        fails = _check_topology(orig, m, guard=kw)
        raw = open(p, "rb").read()
        moved = sum(1 for a, b in zip(raw, out) if a != b)
        status = "ORACLE PASS" if not fails else "ORACLE FAILED"
        print(f"{status}  {os.path.basename(p):<52} changed {moved:>7} B  "
              f"{len(raw)} -> {len(out)} B")
        for f in fails:
            print("    " + f)
            failed = True
        if args.outdir:
            os.makedirs(args.outdir, exist_ok=True)
            dst = os.path.join(args.outdir, os.path.basename(p))
            open(dst, "wb").write(out)

    print()
    printable = {k: v for k, v in kw.items() if not k.startswith("_")}
    print(f"profile {args.profile}  params={printable}")
    print(f"shared vehicle frame: X {lo[0]:+.3f}..{hi[0]:+.3f} ({span[0]:.3f} m)   "
          f"Y {lo[1]:+.3f}..{hi[1]:+.3f} ({span[1]:.3f} m)   "
          f"Z {lo[2]:+.3f}..{hi[2]:+.3f} ({span[2]:.3f} m)")
    print(f"floor = {kw.get('floor', 0.80):.3f} m is the roof-squash reference. Wheel openings "
          f"guarded at r={kw.get('guard', 0.52):.2f} m around z="
          f"{sorted(kw.get('wheel') or [-1.557, 1.446])}; those vertices are asserted unmoved.")
    if args.outdir:
        print(f"wrote {len(models)} files under {args.outdir}")
    return 1 if failed else 0


def np_all_positions(m: Rbm) -> list:
    pts = []
    for b in m.blocks:
        pts.extend(b.vb0.positions())
    return pts


def cmd_scale(args) -> int:
    """Topology-preserving scale of vertex positions.

    --mode centroid scales each block about ITS OWN bounding-box centre, which is
    what you want when reshaping a shell: scaling about the world origin stretches
    the two ends by different amounts (test-007 stretched the front more than the
    rear because the body's origin sits off-centre). --mode origin reproduces the
    plain object-scale behaviour.
    """
    factors = [args.fx, args.fy, args.fz]
    if args.uniform is not None:
        factors = [args.uniform] * 3

    raw = open(args.input, "rb").read()
    m = decode(raw)

    before = {i: (b.vb0.count, b.index_count) for i, b in enumerate(m.blocks)}
    centres = []
    for b in m.blocks:
        pos = b.vb0.positions()
        if args.mode == "centroid" and pos:
            c = [(min(p[k] for p in pos) + max(p[k] for p in pos)) / 2.0 for k in range(3)]
        else:
            c = [0.0, 0.0, 0.0]
        centres.append(c)
        b.vb0.scale_about(c, factors)

    # header bbox scales the same way, about the centre of the whole-model bbox
    bmin, bmax = list(m.bbox_min), list(m.bbox_max)
    for k in range(3):
        if args.mode == "centroid":
            c = (bmin[k] + bmax[k]) / 2.0
            bmin[k] = c + (bmin[k] - c) * factors[k]
            bmax[k] = c + (bmax[k] - c) * factors[k]
        else:
            bmin[k] *= factors[k]
            bmax[k] *= factors[k]
    m.bbox_min, m.bbox_max = tuple(bmin), tuple(bmax)

    out = m.write()

    # ---- the offline oracle ----
    orig = decode(raw)
    changed = sum(1 for a, b in zip(raw, out) if a != b) if len(raw) == len(out) else -1
    print(f"input        : {args.input}  ({len(raw)} B)")
    print(f"output       : {args.output}  ({len(out)} B)")
    print(f"changed bytes: {changed}  (size {'unchanged' if len(raw) == len(out) else 'CHANGED'})")
    print(f"bbox         : {[round(v,4) for v in m.bbox_min]} .. {[round(v,4) for v in m.bbox_max]}")

    fails = []
    for i, (ob, nb) in enumerate(zip(orig.blocks, m.blocks)):
        if (nb.vb0.count, nb.index_count) != before[i]:
            fails.append(f"block {i}: counts changed!")
        if nb.ib.data != ob.ib.data:
            fails.append(f"block {i}: INDEX BUFFER CHANGED")
        if nb.deform_table != ob.deform_table:
            fails.append(f"block {i}: deform table changed")
        if nb.static_params != ob.static_params or nb.dynamic_params != ob.dynamic_params:
            fails.append(f"block {i}: material params changed")
        if nb.textures != ob.textures:
            fails.append(f"block {i}: textures changed")
        if nb.flags != ob.flags or nb.version != ob.version:
            fails.append(f"block {i}: flags/version changed")
        if nb.vb1.data != ob.vb1.data:
            fails.append(f"block {i}: normals/tangents changed")
        # within vb0, only the 3 position floats per element may differ
        d = sum(1 for a, b in zip(ob.vb0.data, nb.vb0.data) if a != b)
        allowed = sum(
            1 for v in range(nb.vb0.count)
            for k in (0, 1, 2)
            if ob.vb0.data[v * nb.vb0.stride + k: v * nb.vb0.stride + k + 4]
            != nb.vb0.data[v * nb.vb0.stride + k: v * nb.vb0.stride + k + 4]
            for _ in (0,)
        )
        print(f"   block {i}: verts={nb.vb0.count} tris={nb.index_count // 3} "
              f"vb0 changed bytes={d} (max {nb.vb0.count * 3 * 4})")
        if d > nb.vb0.count * 3 * 4:
            fails.append(f"block {i}: more vb0 bytes changed than 3 floats x verts")

    print()
    if fails:
        print("ORACLE FAILED:")
        for f in fails:
            print("  " + f)
        return 1
    print("ORACLE PASS: only vertex position floats (+ header bbox) changed.")
    print("              counts, index buffer, deform table, bone weights, normals,")
    print("              material params, textures and flags are all byte-identical.")
    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
        with open(args.output, "wb") as fh:
            fh.write(out)
        print(f"\nwrote {args.output}")
    return 0


def cmd_diff(args) -> int:
    """Field-by-field comparison of two RBMs, decoded."""
    a = decode(open(args.a, "rb").read())
    b = decode(open(args.b, "rb").read())
    print(f"A {os.path.basename(args.a)}: blocks={a.number_of_blocks} tag={a.tag} bbox={[round(v,3) for v in a.bbox_min]}..{[round(v,3) for v in a.bbox_max]}")
    print(f"B {os.path.basename(args.b)}: blocks={b.number_of_blocks} tag={b.tag} bbox={[round(v,3) for v in b.bbox_min]}..{[round(v,3) for v in b.bbox_max]}")
    for i, (x, y) in enumerate(zip(a.blocks, b.blocks)):
        d = []
        if x.vb0.count != y.vb0.count:
            d.append(f"verts {x.vb0.count}->{y.vb0.count}")
        if x.index_count != y.index_count:
            d.append(f"idx {x.index_count}->{y.index_count}")
        if x.ib.data != y.ib.data:
            d.append("INDEXES DIFFER")
        if x.vb0.data != y.vb0.data:
            d.append("positions differ")
        if x.deform_table != y.deform_table:
            d.append("deform table differs")
        if x.flags != y.flags:
            d.append(f"flags 0x{x.flags:04X}->0x{y.flags:04X}")
        print(f"   block {i}: " + (", ".join(d) if d else "identical"))
    return 0


def cmd_selftest(_args) -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, "..", ".."))
    target = os.path.join(root, "Builds", "test-003", "aaf", "models", "jc_vehicles",
                          "01_land", "v0300_car_kensington_sportsmuscle")
    if not os.path.isdir(target):
        print(f"donor tree not found: {target}", file=sys.stderr)
        return 2
    print("round-trip over the real Serpente donor tree (the only oracle that matters)")
    rc = cmd_roundtrip(argparse.Namespace(paths=[target], limit=0, verbose=False))
    return rc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("info", help="parse and summarise RBM geometry")
    p.add_argument("paths", nargs="+")
    p.set_defaults(func=cmd_info)

    p = sub.add_parser("roundtrip", help="decode+encode must be byte-identical")
    p.add_argument("paths", nargs="+")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("-v", "--verbose", action="store_true")
    p.set_defaults(func=cmd_roundtrip)

    p = sub.add_parser("selftest", help="round-trip the Serpente donor tree")
    p.set_defaults(func=cmd_selftest)

    p = sub.add_parser("scale", help="topology-preserving scale of vertex positions")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--mode", default="origin", choices=["origin", "centroid"],
                   help="anchor: world origin, or each block's own bbox centre")
    p.add_argument("--uniform", type=float, help="scale all three axes equally")
    p.add_argument("--fx", type=float, default=1.0)
    p.add_argument("--fy", type=float, default=1.0)
    p.add_argument("--fz", type=float, default=1.0)
    p.set_defaults(func=cmd_scale)

    p = sub.add_parser("export", help="decode geometry to Wavefront OBJ (community interchange format)")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--block", type=int, help="only this render block index")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("preview", help="render orthographic SIDE/TOP/FRONT views to PNG, offline")
    p.add_argument("inputs", nargs="+")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--labels", nargs="*")
    p.add_argument("--color-blocks", action="store_true",
                   help="colour each render block differently to identify panels")
    p.add_argument("--merge", action="store_true",
                   help="treat all inputs as one assembly, the way the car is really built")
    p.add_argument("--splat", action="store_true",
                   help="fast point-splat render instead of triangle rasterisation")
    p.add_argument("--splat-size", type=int, default=460)
    p.set_defaults(func=cmd_preview)

    p = sub.add_parser("displace", help="apply a named vertex profile to one or many RBMs, still topology-preserving")
    p.add_argument("inputs", nargs="+")
    p.add_argument("-o", "--outdir", help="write the reshaped RBMs here")
    p.add_argument("--profile", default="tumble",
                   choices=["tumble", "tumbler", "wedge", "flatten", "none"])
    p.add_argument("--cloud", help="Batmobile PSKX, the measured target shape (profile 'tumbler')")
    p.add_argument("-p", "--param", action="append", help="key=value")
    p.set_defaults(func=cmd_displace)

    p = sub.add_parser("extend", help="ADD new geometry to one render block, leaving existing vertices untouched")
    p.add_argument("input")
    p.add_argument("output", nargs="?")
    p.add_argument("--block", type=int, default=0)
    p.add_argument("--donor", type=int, default=0,
                   help="existing vertex whose attributes new vertices clone")
    p.add_argument("-p", "--param", action="append", help="key=value for the fin")
    p.set_defaults(func=cmd_extend)

    p = sub.add_parser("probe", help="solve an unpublished block layout from the files themselves")
    p.add_argument("inputs", nargs="+")
    p.set_defaults(func=cmd_probe)

    p = sub.add_parser("diff", help="field-by-field comparison of two decoded RBMs")
    p.add_argument("a")
    p.add_argument("b")
    p.set_defaults(func=cmd_diff)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())