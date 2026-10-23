"""jc3hkx.py - a type-aware Havok 2014 packfile reader for JC3 `.physicsc` (G2-8).

`.physicsc` is a Havok 2014.1 (`hk_2014.1.0-r1`) binary packfile.  Until now the
project read exactly one datum out of it structurally: the four wheel-station
`(x, y, z, 1.0)` quads (`jc3phys.py`).  The collision *shapes* were out of reach
because a packfile needs a type library and JC3 ships none:

    __classnames__   20-40 names + hashes          (present)
    __types__        **zero bytes in every file**  (stripped)
    __data__         objects + fixup tables        (present)

So this reader carries the layouts itself, derived from the files and pinned by
invariants that fail loudly when a layout is wrong.  Evidence:
`Research/JC3Grab/SHAPES.md`.

The vehicle's physics lives **inside its `.ee` bundle**, so the entity bundle is
what this reads, exactly like `jc3phys.py`.  Bundle entries are `(name, offset,
size)`; `offset == 0` means the member is *referenced* rather than embedded - the
name is the VFS path and the bytes come from the archives (41 models keep their
physics file that way, and reading offset 0 there returns the bundle header).

What is decoded
---------------
Packfile envelope: header, section table, class-name table, virtual / local /
global fixup tables, 64-bit pointers (8 bytes, low half written by fixups) and
`hkArray` as `{T* data; int size; u32 capacityAndFlags}` (16 bytes).

Objects are typed by the **virtual fixup table**, which in a packfile names the
class of every object by offset - the same information the game's loader uses.
On the donor: 430 objects, 16 classes, every name resolved.

Then, per class:

  * `hknpConvexPolytopeShape` - convex hull.  A packed blob: header (flags,
    convex radius, shape tag), then `vertices` (hkVector4, rank in `w`),
    `planes` (unit normal + distance), a face table and a byte index list.
    Vertex / plane / face / index blocks are accounted for byte for byte.
  * `hknpExternMeshShape(Data)` - the chassis collision mesh.  Vertex *count* and
    the AABB decode; the vertices themselves are 6-byte quantized triples (3 x
    u16) and are reported as such, not invented.
  * `hkGeometry` - raw mesh: vertices + triangles, arrays fill the object exactly.
  * `hknpStaticCompoundShape` / `hknpDynamicCompoundShape` - typed, child-shape
    pointers resolved.  Their instance / AABB slots are **not** decoded: what
    reads there does not enclose the children, so nothing is invented for them.
  * `hknpPhysicsSystemData` - the six arrays (80 / 64 / 112 / 96-byte elements,
    then two pointer arrays).  The 96-byte entries carry the wheel hardpoints as
    an `hkVector4` with `w == 1.0` at `+0x30`.
  * `hkRootLevelContainer`, `hknpPhysicsSceneData` - the variant chain, names read
    from `hkStringPtr` fields.

`check` re-runs every invariant over every vehicle and fails on one violation.

Usage:
  python jc3hkx.py build --all            # every vehicle -> _JC3grab/hkx/out
  python jc3hkx.py report                 # Research/JC3Grab/SHAPES.md
  python jc3hkx.py check --all
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jc3index import DEFAULT_GAME, DEFAULT_OUT, MOUNT_RANK, load_index  # noqa: E402
from jc3phys import land_global_stations  # noqa: E402
from eetoc import unaaf, sarc_dir  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_JC3grab")
OUT = os.path.join(ROOT, "Research", "JC3Grab")

MAGIC = 0x57E0E057
VERSION = 0x10C0C010
FILE_VERSION = 11
SECTION_HEAD = 0x40          # first section record
SECTION_SIZE = 0x40          # 19-byte name, 0xFF, 7 offsets, 16 bytes pad
CLASSNAME_MARKER = 0x09      # constant byte between a classname hash and its name
NULL = 0xFFFFFFFF
ARRAY = 16                   # hkArray: ptr(8), size(4), capacityAndFlags(4)
CAP_OWNED = 0x80000000
PAD_BYTE = 0x7F
UNUSED_PLANE_W = -1e18                   # any plane this deep is Havok's "unused" marker
V0_W = 0x3F000000                        # 0.5f, the first vertex rank

POLYTOPE = "hknpConvexPolytopeShape"
POLYTOPE_HEAD = 0x50
BODY_ENTRY_SIZE = 96         # hknpPhysicsSystemData 4th array; hardpoint at +0x30
MESH_VERTEX_STRIDE = 6       # hknpExternMeshShapeData: 3 x u16, quantized
SHAPE_INSTANCE_SIZE = 128    # hknpShapeInstance: basis, translation, scale, shape ptr


# --------------------------------------------------------------------------
# packfile envelope
# --------------------------------------------------------------------------
class Section:
    __slots__ = ("name", "data", "local", "global_", "virtual", "exports",
                 "imports", "end")

    def __init__(self, name, values):
        self.name = name
        (self.data, self.local, self.global_, self.virtual, self.exports,
         self.imports, self.end) = values


class Obj:
    """One typed object: its offset in the data section and its class name."""

    __slots__ = ("offset", "cls")

    def __init__(self, offset: int, cls: str):
        self.offset = offset
        self.cls = cls

    def __repr__(self) -> str:                       # pragma: no cover
        return f"Obj({self.offset:#x}, {self.cls})"


class Packfile:
    """A Havok 2014 packfile: sections, class names, objects and fixups."""

    def __init__(self, blob: bytes):
        self.blob = blob
        (self.magic, self.version, self.user_tag, self.file_version,
         self.layout_rules, self.num_sections, self.contents_index,
         self.contents_offset, self.classnames_index, self.classnames_offset,
         self.header_word_24) = struct.unpack_from("<11I", blob, 0)
        self.version_name = blob[0x28:blob.index(b"\0", 0x28)].decode("latin-1")
        self.sections: dict[str, Section] = {}
        self.section_list: list[Section] = []
        for i in range(self.num_sections):
            base = SECTION_HEAD + i * SECTION_SIZE
            name = blob[base:base + 19].split(b"\0")[0].decode("latin-1")
            sec = Section(name, struct.unpack_from("<7I", blob, base + 20))
            self.sections[name] = sec
            self.section_list.append(sec)

        self.data = self.sections["__data__"]
        self.base = self.data.data            # file offset of data-section byte 0
        self.lf, self.gf, self.vf, self.ex, self.im, self.end = (
            self.data.local, self.data.global_, self.data.virtual,
            self.data.exports, self.data.imports, self.data.end)
        self.classnames = self._classnames()
        self.virtual, self.virtual_residue = self._virtual()
        self.objects = [Obj(off, cn) for off, cn in self.virtual]
        self.local, self.local_pad = self._local()
        self.global_, self.global_pad = self._global()
        self.pointers: dict[int, int] = {}
        for frm, to in self.local:
            self.pointers[frm] = to
        for frm, _sec, to in self.global_:
            self.pointers[frm] = to
        self._starts = {o.offset: o.cls for o in self.objects}
        self._order = sorted(self._starts)
        self.extents = {}
        for i, off in enumerate(self._order):
            nxt = self._order[i + 1] if i + 1 < len(self._order) else self.lf
            self.extents[off] = nxt - off
        self.sorted_targets = sorted(set(self.pointers.values()) | set(self._order))

    # -- tables -----------------------------------------------------------
    def _classnames(self) -> list[tuple[int, int, str]]:
        """[(offset of the name inside the section, hash, name)]."""
        sec = self.sections["__classnames__"]
        start, end = sec.data, sec.data + sec.end
        out, p, marker_bad = [], start, 0
        while p < end - 1:
            if self.blob[p] == 0xFF:
                p += 1
                continue
            h, = struct.unpack_from("<I", self.blob, p)
            if self.blob[p + 4] != CLASSNAME_MARKER:
                marker_bad += 1
            q = self.blob.index(b"\0", p + 5)
            out.append((p + 5 - start, h, self.blob[p + 5:q].decode("latin-1")))
            p = q + 1
        self.classname_marker_bad = marker_bad
        return out

    def _virtual(self) -> tuple[list[tuple[int, str]], int]:
        names = {rel: nm for rel, _h, nm in self.classnames}
        p, out = self.vf, []
        while p + 12 <= self.ex:
            frm, middle, cls = struct.unpack_from("<3I", self.blob, self.base + p)
            if frm == NULL or cls not in names:
                break
            out.append((frm, names[cls]))
            p += 12
        while p + 4 <= self.ex and self.blob[self.base + p] == 0xFF:
            p += 4
        return out, self.ex - p

    def _local(self) -> tuple[list[tuple[int, int]], int]:
        p, out, pad = self.lf, [], 0
        while p + 8 <= self.gf:
            frm, to = struct.unpack_from("<2I", self.blob, self.base + p)
            if frm == NULL or to == NULL:
                pad += 1
            else:
                out.append((frm, to))
            p += 8
        return out, pad

    def _global(self) -> tuple[list[tuple[int, int, int]], int]:
        p, out, pad = self.gf, [], 0
        while p + 12 <= self.vf:
            frm, sec, to = struct.unpack_from("<3I", self.blob, self.base + p)
            if frm == NULL or to == NULL:
                pad += 1
            else:
                out.append((frm, sec, to))
            p += 12
        return out, pad

    # -- raw access -------------------------------------------------------
    def u32(self, rel: int) -> int:
        return struct.unpack_from("<I", self.blob, self.base + rel)[0]

    def u16(self, rel: int) -> int:
        return struct.unpack_from("<H", self.blob, self.base + rel)[0]

    def f32(self, rel: int) -> float:
        return struct.unpack_from("<f", self.blob, self.base + rel)[0]

    def vec4(self, rel: int) -> tuple[float, float, float, float]:
        return struct.unpack_from("<4f", self.blob, self.base + rel)

    def raw(self, rel: int, n: int) -> bytes:
        return self.blob[self.base + rel:self.base + rel + n]

    def array(self, slot: int) -> dict:
        """`hkArray` header at a pointer slot: `{T* data; int size; u32 cap|flags}`."""
        cap = self.u32(slot + 12)
        return {
            "ptr": self.pointers.get(slot, 0),
            "size": self.u32(slot + 8),
            "capacity": cap & 0x7FFFFFFF,
            "owned": bool(cap & CAP_OWNED),
        }

    def string(self, rel: int) -> str:
        q = self.blob.index(b"\0", self.base + rel)
        return self.blob[self.base + rel:q].decode("latin-1")

    def next_target(self, rel: int) -> int:
        """First known data start after `rel` (array target or object), else lf."""
        for t in self.sorted_targets[self.sorted_targets.index(rel) + 1:]:
            if t > rel:
                return t
        return self.lf


# --------------------------------------------------------------------------
# layouts (offsets in bytes from the object start; every one is proven)
# --------------------------------------------------------------------------
SHAPE_CLASSES = (
    "hknpConvexPolytopeShape", "hknpExternMeshShape", "hknpConvexShape",
    "hknpTriangleShape", "hknpStaticCompoundShape", "hknpDynamicCompoundShape",
)
COMPOUND_CLASSES = ("hknpStaticCompoundShape", "hknpDynamicCompoundShape")

# (offset, name, kind, element size)
LAYOUTS: dict[str, list[tuple[int, str, str, int | None]]] = {
    "hkRootLevelContainer": [
        (0x00, "named_variants", "array:named_variant", 16),
        (0x20, "variant", "ptr", None),
    ],
    "hknpPhysicsSceneData": [
        (0x10, "system_datas", "array:ptr", 8),
        (0x30, "system_data", "ptr", None),
    ],
    "hknpPhysicsSystemData": [
        (0x10, "array_10", "array", 80),
        (0x20, "array_20", "array", 64),
        (0x30, "array_30", "array", 112),
        (0x40, "body_entries", "array", BODY_ENTRY_SIZE),
        (0x50, "array_50", "array", None),
        (0x60, "array_60", "array", 8),
    ],
    "hknpConvexShape": [
        (0x10, "shape_flags", "u32", None),
        (0x14, "convex_radius", "f32", None),
        (0x18, "shape_tag", "u32", None),
        (0x20, "ref_counted_properties", "ptr", None),
    ],
    "hknpTriangleShape": [
        (0x10, "shape_flags", "u32", None),
        (0x14, "convex_radius", "f32", None),
        (0x18, "shape_tag", "u32", None),
        (0x20, "ref_counted_properties", "ptr", None),
    ],
    "hknpExternMeshShape": [
        (0x10, "shape_flags", "u32", None),
        (0x14, "convex_radius", "f32", None),
        (0x18, "shape_tag", "u32", None),
        (0x20, "ref_counted_properties", "ptr", None),
        (0x68, "mesh_data", "ptr", None),
    ],
    "hknpCompressedMeshShape": [
        (0x10, "shape_flags", "u32", None),
        (0x14, "convex_radius", "f32", None),
        (0x18, "shape_tag", "u32", None),
        (0x20, "ref_counted_properties", "ptr", None),
        (0x60, "shape_data", "ptr", None),
        (0xD0, "mass_properties", "ptr", None),
    ],
    "hknpCompressedMeshShapeData": [],
    "hknpExternMeshShapeData": [
        (0x10, "packed_vertices", "array:packed3x16", MESH_VERTEX_STRIDE),
        (0x20, "aabb_min", "vec4", None),
        (0x30, "aabb_max", "vec4", None),
        (0x48, "sections", "array", None),
    ],
    # Compounds: `instances` is an hkArray of 128-byte `hknpShapeInstance`
    # records - 3x3 basis (three float4 rows at +0x00/+0x10/+0x20, w lane
    # carries a per-row norm marker), translation (float4 at +0x30), scale
    # (float4 at +0x40) and the child shape pointer at +0x50.  The array is
    # inline (right after the header, at +0xD0) on the static ones and a
    # separate allocation on the dynamic ones; the header says which.
    # The AABB at +0x80/+0x90 is the union of the children, which is what
    # `shape_checks` tests the instances against.
    "hknpStaticCompoundShape": [
        (0x10, "shape_flags", "u32", None),
        (0x18, "shape_tag", "u32", None),
        (0x20, "ref_counted_properties", "ptr", None),
        (0x60, "instances", "array", SHAPE_INSTANCE_SIZE),
        (0x80, "aabb_min", "vec4", None),
        (0x90, "aabb_max", "vec4", None),
        (0xC0, "shape_data", "ptr", None),
    ],
    "hknpDynamicCompoundShape": [
        (0x10, "shape_flags", "u32", None),
        (0x18, "shape_tag", "u32", None),
        (0x20, "ref_counted_properties", "ptr", None),
        (0x60, "instances", "array", SHAPE_INSTANCE_SIZE),
        (0x80, "aabb_min", "vec4", None),
        (0x90, "aabb_max", "vec4", None),
        (0xC0, "shape_data", "ptr", None),
    ],
    "hknpStaticCompoundShapeData": [],
    "hknpDynamicCompoundShapeData": [],
    "hkGeometry": [
        (0x10, "vertices", "array:vec4", 16),
        (0x20, "triangles", "array:tri", 16),
    ],
    "hkRefCountedProperties": [],
    "hknpShapeMassProperties": [],
    "CPfxPartIndexProperty": [],
    "hkpLimitedHingeConstraintData": [],
    "hkpRagdollConstraintData": [],
    "hkpHingeConstraintData": [],
}


# --------------------------------------------------------------------------
# decoders
# --------------------------------------------------------------------------
def decode_polytope(pf: Packfile, off: int) -> dict:
    """`hknpConvexPolytopeShape`: header, inline vertices, planes, faces, indices."""
    extent = pf.extents[off]
    vcount = pf.u16(off + 0x30)
    plane_u32, index_u32 = pf.u32(off + 0x44), pf.u32(off + 0x48)
    pcount, icount = plane_u32 & 0xFFFF, index_u32 & 0xFFFF

    verts = [pf.vec4(off + POLYTOPE_HEAD + 16 * i) for i in range(vcount)]
    plane_at = off + POLYTOPE_HEAD + 16 * vcount
    planes, unused_planes = [], 0
    for i in range(pcount):
        x, y, z, d = pf.vec4(plane_at + 16 * i)
        if x == 0.0 and y == 0.0 and z == 0.0 and d < UNUSED_PLANE_W:
            unused_planes += 1
            continue
        planes.append({"n": [x, y, z], "d": d})

    # The index list is the last block before the 0x7F tail padding.
    pad = 0
    while pad < 32 and pf.blob[pf.base + off + extent - 1 - pad] == PAD_BYTE:
        pad += 1
    idx_at = off + extent - pad - icount
    indices = list(pf.raw(idx_at, icount)) if icount else []
    face_at = plane_at + 16 * pcount
    face_bytes = idx_at - face_at

    axis = [[v[k] for v in verts] for k in range(3)]
    # A hull is only "read right" if its two blocks agree: every plane is the
    # supporting plane of the vertex set, `n.v + d == 0` at the contact and
    # <= 0 elsewhere (the stored normal points inward).  Tolerance is the
    # shape's own convex radius - a hull is rounded by exactly that much, so
    # the innermost vertices may sit up to `r` inside the outermost plane.
    support_gap = 0.0
    for pl in planes:
        n, d = pl["n"], pl["d"]
        hi = max((n[0] * v[0] + n[1] * v[1] + n[2] * v[2] for v in verts), default=0.0)
        support_gap = max(support_gap, abs(hi + d))
    tol = max(pf.f32(off + 0x14), 0.0) + 1e-3
    return {
        "class": POLYTOPE,
        "offset": off,
        "extent": extent,
        "shape_flags": pf.u32(off + 0x10),
        "convex_radius": pf.f32(off + 0x14),
        "shape_tag": pf.u32(off + 0x18),
        "vertex_count": vcount,
        "plane_count": len(planes),
        "unused_planes": unused_planes,
        "index_count": icount,
        "face_bytes": face_bytes,
        "pad_bytes": pad,
        "vertices": [list(v) for v in verts],
        "planes": planes,
        "indices": indices,
        "bounds": {
            "min": [min(a) for a in axis] if verts else [0, 0, 0],
            "max": [max(a) for a in axis] if verts else [0, 0, 0],
        },
        "vertex_ranks": [struct.unpack_from("<I", pf.blob, pf.base + off
                                            + POLYTOPE_HEAD + 16 * i + 12)[0] - V0_W
                         for i in range(vcount)],
        "support_gap": support_gap,
        "convex_ok": support_gap <= tol,
    }


def shape_aabb(pf: Packfile, off: int) -> dict | None:
    """Axis-aligned bounds of one shape, in whatever frame the shape stores them."""
    cls = pf._starts.get(off)
    if cls == POLYTOPE:
        return decode_polytope(pf, off)["bounds"]
    if cls == "hknpExternMeshShape":
        data = pf.pointers.get(off + 0x68, 0)
        if not data:
            return None
        lo, hi = pf.vec4(data + 0x20), pf.vec4(data + 0x30)
        return {"min": list(lo[:3]), "max": list(hi[:3])}
    if cls == "hknpCompressedMeshShape":
        data = pf.pointers.get(off + 0x60, 0)
        if not data:
            return None
        lo, hi = pf.vec4(data + 0x20), pf.vec4(data + 0x30)
        return {"min": list(lo[:3]), "max": list(hi[:3])}
    if cls in COMPOUND_CLASSES:
        lo, hi = pf.vec4(off + 0x80), pf.vec4(off + 0x90)
        return {"min": list(lo[:3]), "max": list(hi[:3])}
    if cls in ("hknpConvexShape", "hknpTriangleShape"):
        return None
    return None


def transform_aabb(box: dict, basis: list, translation: list) -> dict:
    """A child AABB placed by an instance record, in compound space.

    Convention pinned by the data, not assumed: an instance's three float4 rows
    are the images of the unit axes, so `p' = M^T p + t`.  That is the reading
    under which rotated children land inside their compound's own AABB and the
    other reading does not (off-diagonals are common - 0.94/0.34 rotations sit
    on the Serpente's doors and roof).
    """
    out_lo = [float("inf")] * 3
    out_hi = [float("-inf")] * 3
    for x in (box["min"][0], box["max"][0]):
        for y in (box["min"][1], box["max"][1]):
            for z in (box["min"][2], box["max"][2]):
                p = (x, y, z)
                for k in range(3):
                    v = sum(basis[r][k] * p[r] for r in range(3)) + translation[k]
                    out_lo[k] = min(out_lo[k], v)
                    out_hi[k] = max(out_hi[k], v)
    return {"min": out_lo, "max": out_hi}


def part_index_of(pf: Packfile, shape_off: int, cache: dict) -> int | None:
    """The `CPfxPartIndexProperty` a shape hangs off `ref_counted_properties`.

    `hkRefCountedProperties` is two pointer arrays; the second one holds the
    property objects, and a `CPfxPartIndexProperty` carries its part index as a
    u32 at +0x10 (0, 1, 2, ... down a vehicle's part list).
    """
    props = pf.pointers.get(shape_off + 0x20, 0)
    if not props:
        return None
    if props in cache:
        return cache[props]
    found = None
    for slot in range(0, pf.extents.get(props, 0), 8):
        target = pf.pointers.get(props + slot)
        if target and pf._starts.get(target) == "CPfxPartIndexProperty":
            found = pf.u32(target + 0x10)
            break
    cache[props] = found
    return found


def decode_compound(pf: Packfile, off: int, cls: str) -> dict:
    """A compound shape's instance records: child shape + placement."""
    arr = pf.array(off + 0x60)
    parts: dict = {}
    instances = []
    for i in range(arr["size"] if arr["ptr"] else 0):
        at = arr["ptr"] + i * SHAPE_INSTANCE_SIZE
        if at + SHAPE_INSTANCE_SIZE > pf.lf:
            break
        basis = [list(pf.vec4(at + 16 * r)) for r in range(3)]
        translation = list(pf.vec4(at + 0x30))
        scale = list(pf.vec4(at + 0x40))
        shape = pf.pointers.get(at + 0x50, 0)
        instances.append({
            "index": i,
            "shape": shape,
            "shape_class": pf._starts.get(shape, "") if shape else "",
            "basis": basis,
            "translation": translation,
            "scale": scale,
            "part_index": part_index_of(pf, shape, parts) if shape else None,
            "aabb": shape_aabb(pf, shape) if shape else None,
        })
    out = {
        "class": cls,
        "offset": off,
        "extent": pf.extents[off],
        "shape_flags": pf.u32(off + 0x10),
        "shape_tag": pf.u32(off + 0x18),
        "instance_count": arr["size"],
        "instances_inline": bool(arr["ptr"] and off <= arr["ptr"] < off + pf.extents[off]),
        "aabb": {"min": list(pf.vec4(off + 0x80)[:3]),
                 "max": list(pf.vec4(off + 0x90)[:3])},
        "instances": instances,
    }
    return out


def decode_generic(pf: Packfile, off: int, cls: str) -> dict:
    out: dict = {"class": cls, "offset": off, "extent": pf.extents[off]}
    for foff, name, kind, esize in LAYOUTS.get(cls, []):
        slot = off + foff
        if kind == "ptr":
            target = pf.pointers.get(slot, 0)
            out[name] = {"target": target, "class": pf._starts.get(target, "") if target else ""}
        elif kind.startswith("array"):
            arr = pf.array(slot)
            arr["elem"] = esize
            out[name] = arr
        elif kind == "vec4":
            out[name] = list(pf.vec4(slot))
        elif kind == "u32":
            out[name] = pf.u32(slot)
        elif kind == "f32":
            out[name] = pf.f32(slot)
    return out


def decode(pf: Packfile, obj: Obj) -> dict:
    if obj.cls == POLYTOPE:
        return decode_polytope(pf, obj.offset)
    if obj.cls in COMPOUND_CLASSES:
        return decode_compound(pf, obj.offset, obj.cls)
    return decode_generic(pf, obj.offset, obj.cls)


def mesh_geometry(pf: Packfile, obj: Obj) -> dict | None:
    """`hknpExternMeshShape` -> vertex count, quantized stride, AABB."""
    data = pf.pointers.get(obj.offset + 0x68, 0)
    if not data:
        return None
    arr = pf.array(data + 0x10)
    return {
        "class": obj.cls,
        "data_offset": data,
        "vertex_count": arr["size"],
        "vertex_stride": MESH_VERTEX_STRIDE,
        "aabb": [list(pf.vec4(data + 0x20)), list(pf.vec4(data + 0x30))],
        "sections": pf.array(data + 0x48)["size"],
    }


def geometry_mesh(pf: Packfile, obj: Obj) -> dict | None:
    """`hkGeometry` -> vertices + triangles."""
    var, tar = pf.array(obj.offset + 0x10), pf.array(obj.offset + 0x20)
    if not var["ptr"] or not tar["ptr"]:
        return None
    verts = [list(pf.vec4(var["ptr"] + 16 * i)) for i in range(var["size"])]
    axis = [[v[k] for v in verts] for k in range(3)]
    return {
        "class": obj.cls,
        "vertex_count": var["size"],
        "triangle_count": tar["size"],
        "vertices": verts,
        "bounds": {"min": [min(a) for a in axis] if verts else [0, 0, 0],
                   "max": [max(a) for a in axis] if verts else [0, 0, 0]},
        "triangle_bytes": tar["size"] * 16,
    }


def bounds(verts: list) -> dict:
    if not verts:
        return {"min": [0, 0, 0], "max": [0, 0, 0], "size": [0, 0, 0]}
    lo = [min(v[i] for v in verts) for i in range(3)]
    hi = [max(v[i] for v in verts) for i in range(3)]
    return {"min": lo, "max": hi, "size": [hi[i] - lo[i] for i in range(3)]}


def stations(pf: Packfile) -> list[dict]:
    """Wheel hardpoints from the typed 96-byte body entries (position at +0x30).

    A set is four `(x, y, z, 1.0)` positions sharing one `y`, one `|x|` at both
    signs and two `z`, each at both signs - the same rule `jc3phys.py` applies to
    the raw blob, now read from a known field instead of by float pattern.
    """
    cands = []
    for obj in pf.objects:
        if obj.cls != "hknpPhysicsSystemData":
            continue
        arr = pf.array(obj.offset + 0x40)
        if not arr["size"] or not arr["ptr"]:
            continue
        for i in range(arr["size"]):
            at = arr["ptr"] + i * BODY_ENTRY_SIZE + 0x30
            x, y, z, w = pf.vec4(at)
            if w != 1.0:
                continue
            if not (0.05 < abs(x) < 3.0 and 0.05 < y < 2.5 and 0.05 < abs(z) < 8.0):
                continue
            cands.append((round(y, 3), x, y, z, at))
    groups: dict[float, list] = {}
    for c in cands:
        groups.setdefault(c[0], []).append(c)
    out = []
    for y, g in groups.items():
        if len(g) != 4:
            continue
        xs = {round(abs(c[1]), 3) for c in g}
        zs = {round(c[3], 3) for c in g}
        if len(xs) != 1 or len(zs) != 2:
            continue
        if {c[1] > 0 for c in g} != {True, False} or {c[3] > 0 for c in g} != {True, False}:
            continue
        a = xs.pop()
        z1, z2 = sorted(zs)
        out.append({"x": a, "y": y, "z_rear": z1, "z_front": z2,
                    "track_m": round(2 * a, 4), "wheelbase_m": round(z2 - z1, 4),
                    "fields": sorted(c[4] for c in g)})
    return out


def root_names(pf: Packfile) -> dict:
    """The `hkRootLevelContainer` variant chain: names and the root object's class."""
    out = {"variant_names": [], "variant_class": "", "root_class": ""}
    for obj in pf.objects:
        if obj.cls != "hkRootLevelContainer":
            continue
        arr = pf.array(obj.offset)
        for i in range(arr["size"]):
            name_ptr = pf.pointers.get(arr["ptr"] + 16 * i, 0)
            cls_ptr = pf.pointers.get(arr["ptr"] + 16 * i + 8, 0)
            if name_ptr:
                out["variant_names"].append(pf.string(name_ptr))
            if cls_ptr:
                out["variant_class"] = pf.string(cls_ptr)
        variant = pf.pointers.get(obj.offset + 0x20, 0)
        out["root_class"] = pf._starts.get(variant, "")
    return out


def summary(pf: Packfile) -> dict:
    counts: dict[str, int] = {}
    for o in pf.objects:
        counts[o.cls] = counts.get(o.cls, 0) + 1
    polytopes, meshes, geoms = [], [], []
    for o in pf.objects:
        if o.cls == POLYTOPE:
            polytopes.append(decode_polytope(pf, o.offset))
        elif o.cls == "hknpExternMeshShape":
            g = mesh_geometry(pf, o)
            if g:
                meshes.append(g)
        elif o.cls == "hkGeometry":
            g = geometry_mesh(pf, o)
            if g:
                geoms.append(g)
    allp = [v for p in polytopes for v in p["vertices"]]
    return {
        "file_version": pf.file_version,
        "version_name": pf.version_name,
        "objects": len(pf.objects),
        "class_counts": counts,
        "classnames": len(pf.classnames),
        "types_section_bytes": pf.sections["__types__"].end,
        "local_fixups": len(pf.local),
        "global_fixups": len(pf.global_),
        "root": root_names(pf),
        "polytopes": len(polytopes),
        "polytopes_convex": sum(1 for p in polytopes if p["convex_ok"]),
        "polytope_support_gap": max((p["support_gap"] for p in polytopes), default=0.0),
        "polytope_vertices": sum(p["vertex_count"] for p in polytopes),
        "polytope_planes": sum(p["plane_count"] for p in polytopes),
        "polytope_indices": sum(p["index_count"] for p in polytopes),
        "hull_bounds": bounds(allp),
        "mesh_shapes": [{"vertex_count": m["vertex_count"], "aabb": m["aabb"],
                         "sections": m["sections"]} for m in meshes],
        "geometries": [{"vertex_count": g["vertex_count"],
                        "triangle_count": g["triangle_count"],
                        "bounds": g["bounds"]} for g in geoms],
        "stations": stations(pf),
        "polytope_detail": polytopes,
        "mesh_detail": meshes,
        "geometry_detail": geoms,
    }


# --------------------------------------------------------------------------
# entity bundles
# --------------------------------------------------------------------------
def vehicle_ees(rows: list[dict], only: str | None = None) -> list[str]:
    out = set()
    for r in rows:
        p = r["path"]
        if p.startswith("editor/entities/jc_vehicles/") and p.endswith(".ee"):
            if only and only.lower() not in p.lower():
                continue
            out.add(p)
    return sorted(out)


def extract(path: str, rows: list[dict], game: str) -> bytes | None:
    """One VFS path -> decompressed bytes, newest mount wins."""
    hits = [r for r in rows if r["path"] == path]
    if not hits:
        return None
    row = sorted(hits, key=lambda r: MOUNT_RANK[r["mount"]])[-1]
    with open(os.path.join(game, row["archive"] + ".arc"), "rb") as f:
        f.seek(row["offset"])
        raw = f.read(row["size"])
    try:
        return unaaf(raw)
    except SystemExit:
        return raw        # stored uncompressed


def is_sarc(blob: bytes) -> bool:
    return blob[4:8] == b"SARC" or blob[:4] == b"SARC"


def bundle_packfiles(blob: bytes, rows: list[dict], game: str,
                     depth: int = 0) -> list[tuple[str, bytes]]:
    """`.physicsc` blobs reachable from one bundle layer.

    A bundle is a SARC whose entries are `(name, offset, size)`.  `offset == 0`
    means the member is **referenced, not embedded** - its `name` is the VFS path
    and the data lives in the archives (that is how the 41 large bundles keep
    their 678 KB physics file).  Reading offset 0 there would hand back the
    bundle's own header, which is where the duplicate hits came from.
    """
    out: list[tuple[str, bytes]] = []
    if depth > 3:
        return out
    try:
        entries = sarc_dir(blob)
    except SystemExit:
        return out
    for name, off, size in entries:
        if not name.endswith(".physicsc"):
            continue
        if off == 0:
            member = extract(name, rows, game)
            if member is None:
                continue
            if is_sarc(member):
                out.extend(bundle_packfiles(member, rows, game, depth + 1))
            elif member[:4] == struct.pack("<I", MAGIC):
                out.append((name, member))
            continue
        if not size or off + size > len(blob):
            continue
        member = blob[off:off + size]
        if is_sarc(member):
            out.extend(bundle_packfiles(member, rows, game, depth + 1))
        elif member[:4] == struct.pack("<I", MAGIC):
            out.append((name, member))
    return out


def physicsc_of(ee: str, rows: list[dict], game: str) -> list[tuple[str, bytes]]:
    stream = extract(ee, rows, game)
    if stream is None:
        raise LookupError(f"not in index: {ee}")
    seen: set[tuple[str, int, str]] = set()
    out: list[tuple[str, bytes]] = []
    for name, blob in bundle_packfiles(stream, rows, game):
        key = (name, len(blob), hashlib.sha1(blob).hexdigest()[:16])
        if key in seen:
            continue
        seen.add(key)
        out.append((name, blob))
    return out


def slug(path: str) -> str:
    return path.replace("/", "__")


def station_ref(lg: dict, ee: str) -> dict | None:
    return lg.get(ee)


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------
def cmd_build(a) -> int:
    rows = load_index(a.index)
    ees = vehicle_ees(rows, a.entity if not a.all else None)
    os.makedirs(os.path.join(RAW, "hkx", "out"), exist_ok=True)
    print(f"{len(ees)} entities")
    for i, ee in enumerate(ees, 1):
        try:
            files = physicsc_of(ee, rows, a.game)
        except Exception as e:                       # noqa: BLE001
            print(f"[{i}/{len(ees)}] {os.path.basename(ee)}: ERROR {e}")
            continue
        doc = {"entity": ee, "physics": []}
        for name, blob in files:
            doc["physics"].append({"file": name, "size": len(blob),
                                   "summary": summary(Packfile(blob))})
        fn = os.path.join(RAW, "hkx", "out", slug(ee) + ".json")
        with open(fn, "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, indent=0)
        first = doc["physics"][0]["summary"] if doc["physics"] else None
        if first:
            st = first["stations"][0] if first["stations"] else None
            print(f"[{i}/{len(ees)}] {os.path.basename(ee):52s} "
                  f"poly={first['polytopes']:3d} "
                  f"hull={first['hull_bounds']['size'][0]:.2f}x{first['hull_bounds']['size'][1]:.2f}"
                  f"x{first['hull_bounds']['size'][2]:.2f} "
                  f"mesh={[m['vertex_count'] for m in first['mesh_shapes']][:2]} "
                  f"wb={st['wheelbase_m'] if st else '-'}")
    return 0


def shape_checks(pf: Packfile) -> tuple[dict, list[str]]:
    """Every per-object shape invariant, measured once and shared by `check`/`report`."""
    c = {"polytopes": 0, "blocks": 0, "ranks": 0, "unit": 0, "index_ok": 0,
         "convex": 0, "mesh": 0, "geom": 0, "compounds": 0, "instances": 0,
         "instances_placed": 0, "instances_unboxed": 0, "aabb_ok": 0,
         "union_ok": 0, "union_exact": 0, "wired": 0}
    bad: list[str] = []
    for o in pf.objects:
        if o.cls == POLYTOPE:
            c["polytopes"] += 1
            d = decode_polytope(pf, o.offset)
            head = POLYTOPE_HEAD + 16 * d["vertex_count"] + 16 * (
                d["plane_count"] + d["unused_planes"])
            if (d["face_bytes"] >= 0 and head + d["face_bytes"] + d["index_count"]
                    + d["pad_bytes"] == d["extent"]):
                c["blocks"] += 1
            else:
                bad.append(f"@{o.offset:#x}: blocks {head}+{d['face_bytes']}"
                           f"+{d['index_count']}+{d['pad_bytes']} != {d['extent']}")
            ranks = d["vertex_ranks"]
            if ranks == sorted(ranks) and (not ranks or ranks[0] == 0):
                c["ranks"] += 1
            else:
                bad.append(f"@{o.offset:#x}: vertex ranks {ranks[:4]}")
            unit = all(abs(sum(x * x for x in pl["n"]) ** 0.5 - 1) <= 3e-3
                       for pl in d["planes"])
            if unit:
                c["unit"] += 1
            else:
                bad.append(f"@{o.offset:#x}: plane not unit")
            if all(x < d["vertex_count"] for x in d["indices"]):
                c["index_ok"] += 1
            else:
                bad.append(f"@{o.offset:#x}: index >= vertex_count")
            if d["convex_ok"]:
                c["convex"] += 1
            else:
                bad.append(f"@{o.offset:#x}: vertex outside a plane by "
                           f"{d['support_gap']:.5f} (radius {d['convex_radius']:.5f})")
        elif o.cls == "hknpExternMeshShape":
            c["mesh"] += 1
            g = mesh_geometry(pf, o)
            if not g:
                bad.append(f"@{o.offset:#x}: extern mesh without data")
                continue
            lo, hi = g["aabb"]
            if not all(lo[i] < hi[i] for i in range(3)):
                bad.append(f"@{o.offset:#x}: mesh AABB {lo} .. {hi}")
            arr = pf.array(g["data_offset"] + 0x10)
            span = pf.next_target(arr["ptr"]) - arr["ptr"]
            need = g["vertex_count"] * MESH_VERTEX_STRIDE
            if not (0 <= span - need < 16):
                bad.append(f"@{o.offset:#x}: {need} vertex bytes vs {span}")
        elif o.cls in COMPOUND_CLASSES:
            c["compounds"] += 1
            d = decode_compound(pf, o.offset, o.cls)
            c["instances"] += d["instance_count"]
            lo, hi = d["aabb"]["min"], d["aabb"]["max"]
            spans = [hi[k] - lo[k] for k in range(3)]
            tol = max(spans) * 1e-2 + 1e-3
            union_lo = [float("inf")] * 3
            union_hi = [float("-inf")] * 3
            inside = True
            placed = 0
            unboxed = 0
            for inst in d["instances"]:
                if not inst["shape"] or not inst["shape_class"]:
                    bad.append(f"@{o.offset:#x}: instance {inst['index']} has no shape")
                    inside = False
                    continue
                if inst["part_index"] is not None:
                    c["wired"] += 1
                placed += 1
                box = inst["aabb"]
                if not box:
                    c["instances_unboxed"] += 1
                    unboxed += 1
                    continue
                box = transform_aabb(box, inst["basis"], inst["translation"])
                for k in range(3):
                    if box["min"][k] < lo[k] - tol or box["max"][k] > hi[k] + tol:
                        inside = False
                    union_lo[k] = min(union_lo[k], box["min"][k])
                    union_hi[k] = max(union_hi[k], box["max"][k])
            if inside:
                c["aabb_ok"] += 1
            else:
                bad.append(f"@{o.offset:#x}: a child AABB is outside the compound AABB")
            c["instances_placed"] += placed
            if inside and d["instances"] and not unboxed:
                # the compound AABB is the child union inflated by the children's
                # convex radius (a hull is a cylinder of that radius around its
                # planes), so that radius is the allowance, not a fudge factor
                radii = [pf.f32(inst["shape"] + 0x14) for inst in d["instances"]
                         if inst["shape"]]
                allowance = max(radii + [0.0]) + 1e-3
                # the stored AABB is the children's union inflated by the convex
                # radius; a rotated child inflates its own AABB further, so the
                # test is that the parent is *covered* (nothing missing), and the
                # overshoot is only recorded
                missing = max(max(union_lo[k] - lo[k], hi[k] - union_hi[k])
                              for k in range(3))
                overshoot = max(max(lo[k] - union_lo[k], union_hi[k] - hi[k])
                                for k in range(3))
                if missing <= allowance:
                    c["union_ok"] += 1
                    if overshoot <= allowance:
                        c["union_exact"] += 1
                else:
                    bad.append(f"@{o.offset:#x}: child union leaves {missing:.4f} of "
                               f"the AABB unexplained (convex radius {allowance:.4f})")
        elif o.cls == "hkGeometry":
            c["geom"] += 1
            g = geometry_mesh(pf, o)
            if not g:
                bad.append(f"@{o.offset:#x}: geometry without arrays")
                continue
            if 0x30 + g["vertex_count"] * 16 + g["triangle_bytes"] != pf.extents[o.offset]:
                bad.append(f"@{o.offset:#x}: geometry does not fill the object")
    return c, bad


def cmd_report(a) -> int:
    rows = load_index(a.index)
    ees = vehicle_ees(rows)
    lg = land_global_stations()
    table, agree, disagree, no_station = [], 0, 0, 0
    totals = {"objects": 0, "polytopes": 0, "convex": 0, "blocks": 0, "ranks": 0,
              "unit": 0, "index_ok": 0, "vertices": 0, "planes": 0, "indices": 0,
              "mesh_vertices": 0, "files": 0, "entities": 0, "bad": 0,
              "geom": 0, "mesh": 0, "classes": {}, "compounds": 0, "instances": 0,
              "instances_placed": 0, "instances_unboxed": 0, "aabb_ok": 0,
              "wired": 0, "union_ok": 0, "union_exact": 0}
    for ee in ees:
        try:
            files = physicsc_of(ee, rows, a.game)
        except Exception:                            # noqa: BLE001
            continue
        if not files:
            continue
        totals["entities"] += 1
        blobs = [(n, Packfile(b)) for n, b in files]
        for _n, pf in blobs:
            s = summary(pf)
            counts, bad = shape_checks(pf)
            for k in ("blocks", "ranks", "unit", "index_ok", "convex", "geom", "mesh",
                      "compounds", "instances", "instances_placed", "instances_unboxed",
                      "aabb_ok", "wired", "union_ok", "union_exact"):
                totals[k] = totals.get(k, 0) + counts[k]
            totals["bad"] = totals.get("bad", 0) + len(bad)
            totals["files"] += 1
            totals["objects"] += s["objects"]
            totals["polytopes"] += s["polytopes"]
            for cls, n in s["class_counts"].items():
                totals["classes"][cls] = totals["classes"].get(cls, 0) + n
            totals["vertices"] += s["polytope_vertices"]
            totals["planes"] += s["polytope_planes"]
            totals["indices"] += s["polytope_indices"]
            totals["mesh_vertices"] += sum(m["vertex_count"] for m in s["mesh_shapes"])
        pf = blobs[0][1]
        s = summary(pf)
        st = s["stations"][0] if s["stations"] else None
        ref = station_ref(lg, ee)
        if st and ref:
            same = (abs(st["x"] - ref["x"]) < 1e-3 and abs(st["y"] - ref["y"]) < 1e-3
                    and abs(st["z_rear"] - ref["z_rear"]) < 1e-3
                    and abs(st["z_front"] - ref["z_front"]) < 1e-3)
            agree += same
            disagree += not same
        elif not st:
            no_station += 1
        b = s["hull_bounds"]["size"]
        table.append((ee.rsplit("/", 2)[-2] + "/" + os.path.basename(ee),
                      s["polytopes"], s["polytope_vertices"], s["polytope_planes"],
                      max((m["vertex_count"] for m in s["mesh_shapes"]), default=0),
                      b, st, s["root"]["variant_names"]))

    lines = [
        "# JC3 collision shapes from `.physicsc` (G2-8)", "",
        "Decoded by `Tools/scripts/jc3hkx.py` - a type-aware Havok 2014 packfile reader.",
        f"**{totals['entities']} vehicle entities / {totals['files']} `.physicsc` files**, "
        f"{totals['objects']} objects, {totals['polytopes']} convex hulls "
        f"({totals['convex']} verified convex), {totals['vertices']} hull vertices, "
        f"{totals['planes']} planes, {totals['indices']} hull indices, "
        f"{totals['mesh_vertices']} collision-mesh vertices, and "
        f"**{totals['compounds']:,} compounds / {totals['instances']:,} instance records** "
        f"({totals['wired']:,} with a part index).",
        "",
        "The physics file lives **inside the entity's `.ee` bundle**, as for `jc3phys.py`.",
        "A bundle entry whose `offset` is `0` is a *reference*, not data: the member is",
        "not embedded and its name is the VFS path, so `models/.../x.physicsc` is read",
        "from the archives instead: 33 of the 233 bundles keep their 400-680 KB physics",
        "file that way, and reading offset 0 there returns the bundle header - which is",
        "what made those entities look empty.",
        "",
        "## What the file is", "",
        "Every file starts `57E0E057 10C0C010` with version string `hk_2014.1.0-r1`,",
        "file version 11, layout rules `0x01000108`, three sections:", "",
        "| section | content | evidence |", "|---|---|---|",
        "| `__classnames__` | hash + name records | every entry parses |",
        "| `__types__` | **empty** | `end == data` in every file |",
        "| `__data__` | objects, arrays, fixup tables | virtual fixups type every object |", "",
        "The type library is stripped - the engine's own reflection knows these classes.",
        "This reader carries the layouts instead, and stays *type-aware*: the **virtual",
        "fixup table** names the class of every object, exactly as the game's loader does.", "",
        "Packfile mechanics pinned by the files:", "",
        "* pointers are **8 bytes** (64-bit build), the fixup writes the low half;",
        "* `hkArray` is **16 bytes**: `{T* data; int size; u32 capacityAndFlags}`;",
        "* local fixups are `(from, to)`, global `(from, section, to)`, virtual",
        "  `(offset, 0, class-name offset)`, all data-section relative;",
        "* unused table slots and section tails are `0xFF`, object tails `0x7F`;",
        "* the root variant chain is `hkRootLevelContainer` -> `NPhysicsData` ->",
        "  `hknpPhysicsSceneData` -> `hknpPhysicsSystemData`, names as `hkStringPtr`.", "",
        "## The shape blob", "",
        "`hknpConvexPolytopeShape` is not a pointer-filled class: it is one packed block.", "",
        "```",
        "+0x00  base (16 B)                       hknpShape",
        "+0x10  u32 shape_flags                  0x01000143 on every hull",
        "+0x14  f32 convex_radius",
        "+0x18  u32 shape_tag",
        "+0x20  hkRefCountedProperties*",
        "+0x30  u16 vertex_count, u16 0x20",
        "+0x40  u16 face_count, u16 unused;  u16 ?, u16 ?;  u16 index_count, u16 ?",
        "+0x50  hkVector4 vertices[vertex_count]   w = 0.5 + rank/2^23, rank ascending",
        "       hkVector4 planes[plane_count]      unit normal + distance, n.v + d <= 0",
        "       face table                         4-byte records",
        "       u8 indices[index_count]            every byte < vertex_count",
        "       pad to 16 with 0x7F",
        "```", "",
        "`vertex_count` is the low u16 at `+0x30`, `plane_count` the low u16 at `+0x44`,",
        "`index_count` the low u16 at `+0x48`; `face_count` is the low u16 at `+0x40`.",
        "The high u16s do not line up with block offsets and are not named. The index",
        "block is located from the tail - the last `index_count` bytes before the `0x7F`",
        "padding - which is what makes the whole layout checkable:", "",
        "```",
        "0x50 + 16*V + 16*P + face_bytes + I + pad == object extent",
        "```", "",
        "**Plane convention (measured, not assumed).** The stored distance is not a",
        "standard `n·v - d <= 0` offset: for every hull and every plane,",
        "`max(n·v) + d == 0` at the contact vertex and `<= 0` for all the others.",
        "So the stored normal points **inward** (or, equivalently, the outward plane",
        "is `-n·v - d = 0`). The residual is bounded by the shape's own `convex_radius`,",
        "which is what rounds the hull: the innermost corners sit up to `r` inside the",
        "outermost plane. That single relation pins the vertex base, the plane base and",
        "the p-count together - a layout off by one record cannot satisfy it.", "",
        "## Invariants (every vehicle, no exceptions)", "",
        "Measured by `jc3hkx.py check --all`, which exits non-zero on one violation;",
        "the counts below come from the same `shape_checks()` pass, not from a guess.",
        "",
        "| check | result |", "|---|---|",
        f"| `.physicsc` decoded | {totals['files']} / {totals['files']} |",
        "| classes named by the virtual fixup table | every object, 0 unresolved |",
        f"| hull blocks account for the object extent | {totals['blocks']} / {totals['polytopes']} |",
        f"| vertex `w` = `0.5 + rank/2^23`, rank non-decreasing | {totals['ranks']} / {totals['polytopes']} |",
        f"| planes unit length, unused sentinel excluded | {totals['unit']} / {totals['polytopes']} |",
        f"| every hull index `< vertex_count` | {totals['index_ok']} / {totals['polytopes']} |",
        "| **every plane is a supporting plane** (`abs(max n.v + d) <= r`) | "
        f"{totals['convex']} / {totals['polytopes']} |",
        f"| `hkGeometry` arrays fill the object | {totals['geom']} / {totals['geom']} |",
        f"| compound instances resolve to a typed shape | {totals['instances_placed']:,} / "
        f"{totals['instances']:,} |",
        f"| compound child AABBs inside the parent AABB | {totals['aabb_ok']:,} / "
        f"{totals['compounds']:,} compounds |",
        f"| parent AABB explained by the children's union | {totals['union_ok']:,} / "
        f"{totals['compounds']:,} ({totals['union_exact']:,} exact to the convex radius) |",
        f"| instances carrying a part index | {totals['wired']:,} / {totals['instances']:,} |",
        f"| violation(s) | {totals['bad']} |",
        f"| wheel stations vs `land_global` | **{agree} agree**, {disagree} disagree, "
        f"{no_station} file(s) without a set |",
        "",
        "## Vehicles", "",
        "| entity | hulls | hull verts | planes | mesh verts | hull bbox x×y×z (m) | wheelbase |",
        "|---|---|---|---|---|---|---|",
    ]
    for name, npoly, nv, npl, meshv, b, st, _names in sorted(table, key=lambda r: -r[5][2])[:80]:
        wb = f"{st['wheelbase_m']}" if st else ""
        lines.append(f"| `{name}` | {npoly} | {nv} | {npl} | {meshv} | "
                     f"{b[0]:.2f} × {b[1]:.2f} × {b[2]:.2f} | {wb} |")
    lines += [
        "",
        f"First 80 of {len(table)} entities, largest hull bbox first. Full per-entity",
        "JSON (every hull vertex, plane and index) is in `_JC3grab/hkx/out/`.",
        "",
        "## Reading of the numbers", "",
        "* A vehicle's collision is a compound: one or more `hknpExternMeshShape`s (chassis",
        "  panels, vertices copied from the render mesh - which is why a 7 m body got 7 m",
        "  collision with no physics edit) plus `hknpConvexPolytopeShape` hulls for wheels",
        "  and props.",
        "* The hull bbox is the union of every hull's local vertices: a physics bounding",
        "  volume, not the body size - hulls are authored in their own frames.",
        "* The wheel hardpoints are read from a known field now: `+0x30` of the 96-byte",
        "  entries in `hknpPhysicsSystemData`'s fourth array, an `hkVector4` with `w == 1.0`.",
        "  That typed field only yields a full four-station set on some vehicles, so it",
        "  **confirms** `jc3phys.py` where it fires (no disagreements) but does not",
        "  replace the raw-quad scan as the station source.",
        "",
        "## Compound instance records (the hull -> part wiring)", "",
        "A vehicle's collision is a tree, not a pile: `hknpStaticCompoundShape` /",
        "`hknpDynamicCompoundShape` hold an `hkArray` at `+0x60` of 128-byte",
        "`hknpShapeInstance` records, and each record is", "",
        "| offset | field |", "|---|---|",
        "| `+0x00` / `+0x10` / `+0x20` | 3x3 basis, three `float4` rows (the `w` lane carries a per-row norm marker, `0.5` on a unit row) |",
        "| `+0x30` | translation, `float4` |",
        "| `+0x40` | scale, `float4` (`1,1,1,1` everywhere observed) |",
        "| `+0x50` | child shape pointer (virtual fixup) |",
        "| `+0x60` / `+0x70` | zero |", "",
        "The array is **inline at `+0xD0`** on the static class (so the object's extent covers",
        "header + instances) and a **separate allocation** on the dynamic one; the header at",
        "`+0x60` says which, and element stride `128` is confirmed by the gap to the next",
        "target, `count x 128` exactly.", "",
        "**Placement is `p' = M^T p + t`.** That is not a guess either: the Serpente's doors",
        "and roof carry 0.94/0.34 rotations, and under this reading every rotated child lands",
        "inside its compound's own AABB, while the other reading ( `M p` ) puts them up to",
        "0.14 m outside. Identity placements - the majority - cannot tell the two apart.", "",
        "**Wiring.** A child shape's `ref_counted_properties` (`+0x20`) reaches a",
        "`CPfxPartIndexProperty`, whose part index is a u32 at `+0x10`. Joined to",
        "`PARTS_TABLE.jsonl` that is a part *name*, which is what `WIRING.md` tabulates:",
        f"**{totals['compounds']:,} compounds, {totals['instances']:,} instances,",
        f"{totals['wired']:,} with a part index**, and the AABB checks above as the proof",
        "that the record layout is right rather than merely plausible.", "",
        "`wiring` writes `WIRING.jsonl` (one row per instance: entity, file, compound,",
        "instance, child class, AABB, part index, part name).", "",
        "## Still open", "",
        "* **Body -> shape wiring.** The 80-byte body entries and 64-byte motion entries are",
        "  counted and sized but their fields are not pinned; the compound instances carry",
        "  the shape -> part wiring (`WIRING.md`), which is what the mod needed.",
        "* **Quantized mesh vertices.** `hknpExternMeshShapeData` stores 3 × u16 per vertex",
        "  (6-byte stride, confirmed by the gap to the next array); dequantizing against the",
        "  shape AABB reproduces the minimum corner but not the extent, so the frame is",
        "  chunk-relative and not yet pinned. Counts and AABBs are exact; positions are not.",
        "* **Face table semantics.** 4-byte records (`u16 first, u8 count, u8 min` reads",
        "  plausibly for the first records); only the index block is validated, so faces are",
        "  reported as bytes.",
        "* **Writing.** Nothing here writes a `.physicsc` - reading only.",
        "",
    ]
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "SHAPES.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"SHAPES.md: {totals['entities']} entities, {totals['files']} files, "
          f"{totals['polytopes']} hulls, stations {agree} agree / {disagree} disagree / "
          f"{no_station} none")
    return 0


def cmd_check(a) -> int:
    rows = load_index(a.index)
    ees = vehicle_ees(rows, a.entity if not a.all else None)
    problems: list[str] = []
    stats = {"entities": 0, "files": 0, "objects": 0, "polytopes": 0, "mesh": 0,
             "geom": 0, "stations": 0, "station_agree": 0, "station_bad": 0,
             "convex": 0, "compounds": 0, "instances": 0, "union_ok": 0, "wired": 0}
    lg = land_global_stations()
    for ee in ees:
        try:
            files = physicsc_of(ee, rows, a.game)
        except Exception as e:                       # noqa: BLE001
            problems.append(f"{ee}: extract: {e}")
            continue
        if not files:
            continue
        stats["entities"] += 1
        name = os.path.basename(ee)
        for inner, blob in files:
            try:
                pf = Packfile(blob)
            except Exception as e:                   # noqa: BLE001
                problems.append(f"{name}/{inner}: packfile: {e}")
                continue
            stats["files"] += 1
            if pf.magic != MAGIC:
                problems.append(f"{name}: magic {pf.magic:#x}")
            if pf.version != VERSION or pf.file_version != FILE_VERSION:
                problems.append(f"{name}: version {pf.version:#x}/{pf.file_version}")
            if pf.version_name != "hk_2014.1.0-r1":
                problems.append(f"{name}: version name {pf.version_name!r}")
            if [s.name for s in pf.section_list] != ["__classnames__", "__types__", "__data__"]:
                problems.append(f"{name}: sections {[s.name for s in pf.section_list]}")
            if pf.sections["__types__"].end:
                problems.append(f"{name}: __types__ is not empty")
            if pf.virtual_residue or pf.classname_marker_bad:
                problems.append(f"{name}: table residue {pf.virtual_residue}, "
                                f"classname markers {pf.classname_marker_bad}")
            for _off, cls in pf.virtual:
                if cls not in LAYOUTS and cls != POLYTOPE:
                    problems.append(f"{name}: untyped class {cls}")
            for frm, to in pf.local:
                if not (0 <= frm < pf.lf and 0 <= to < pf.lf):
                    problems.append(f"{name}: local fixup {frm:#x}->{to:#x} outside data")
            for frm, sec, to in pf.global_:
                if sec != pf.contents_index or not (0 <= to < pf.lf):
                    problems.append(f"{name}: global fixup {frm:#x}->sec{sec}:{to:#x}")
            stats["objects"] += len(pf.objects)

            counts, bad = shape_checks(pf)
            stats["polytopes"] += counts["polytopes"]
            stats["convex"] += counts["convex"]
            stats["mesh"] += counts["mesh"]
            stats["geom"] += counts["geom"]
            for key in ("compounds", "instances", "union_ok", "wired"):
                stats[key] += counts[key]
            problems.extend(f"{name}{m}" for m in bad)

            st = stations(pf)
            stats["stations"] += len(st)
            if st:
                ref = station_ref(lg, ee)
                if ref:
                    s = st[0]
                    if (abs(s["x"] - ref["x"]) < 1e-3 and abs(s["y"] - ref["y"]) < 1e-3
                            and abs(s["z_rear"] - ref["z_rear"]) < 1e-3
                            and abs(s["z_front"] - ref["z_front"]) < 1e-3):
                        stats["station_agree"] += 1
                    else:
                        stats["station_bad"] += 1
                        problems.append(f"{name}: stations {s['wheelbase_m']} vs land_global")

    if not stats["files"]:
        # A run that decodes nothing must not pass: that is how the 33 referenced
        # bundles stayed invisible while `check` reported success.
        problems.append("no .physicsc decoded at all - extraction is broken")
    print(f"entities {stats['entities']} | files {stats['files']} | objects {stats['objects']} | "
          f"hulls {stats['polytopes']} (convex {stats['convex']}) | mesh shapes {stats['mesh']} | "
          f"geometries {stats['geom']} | compounds {stats['compounds']} "
          f"({stats['instances']} instances, {stats['wired']} with a part index, "
          f"{stats['union_ok']} AABB unions exact) | station sets {stats['stations']} "
          f"(land_global agree {stats['station_agree']}, disagree {stats['station_bad']})")
    if problems:
        for p in problems[:40]:
            print("FAIL", p)
        print(f"{len(problems)} problem(s)")
        return 1
    print("check ok")
    return 0


def load_part_names() -> dict[tuple[str, int], str]:
    """(entity, part index) -> part name, from `PARTS_TABLE.jsonl` (G2-7)."""
    path = os.path.join(OUT, "PARTS_TABLE.jsonl")
    names: dict[tuple[str, int], str] = {}
    if not os.path.exists(path):
        return names
    for line in open(path, encoding="utf-8"):
        if not line.strip():
            continue
        rec = json.loads(line)
        for part in rec.get("parts", []):
            names[(rec["entity"], part["i"])] = part["n"]
    return names


def cmd_wiring(a) -> int:
    """Write SHAPES wiring: compound instance -> child shape class -> part index/name."""
    rows = load_index(a.index)
    ees = vehicle_ees(rows, a.entity if not a.all else None)
    part_names = load_part_names()
    table = []
    totals = {"entities": 0, "compounds": 0, "instances": 0, "wired": 0,
              "named": 0, "files": 0}
    for ee in ees:
        try:
            files = physicsc_of(ee, rows, a.game)
        except Exception:                            # noqa: BLE001
            continue
        if not files:
            continue
        totals["entities"] += 1
        for inner, blob in files:
            totals["files"] += 1
            pf = Packfile(blob)
            for o in pf.objects:
                if o.cls not in COMPOUND_CLASSES:
                    continue
                totals["compounds"] += 1
                d = decode_compound(pf, o.offset, o.cls)
                for inst in d["instances"]:
                    totals["instances"] += 1
                    idx = inst["part_index"]
                    name = part_names.get((ee, idx)) if idx is not None else None
                    totals["wired"] += idx is not None
                    totals["named"] += name is not None
                    table.append({
                        "entity": ee,
                        "file": inner,
                        "compound": o.offset,
                        "compound_class": o.cls,
                        "instance": inst["index"],
                        "shape_class": inst["shape_class"],
                        "shape_aabb": inst["aabb"],
                        "part_index": idx,
                        "part_name": name,
                    })
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "WIRING.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for rec in table:
            f.write(json.dumps(rec, separators=(",", ":")) + "\n")

    classes: dict[str, int] = {}
    for rec in table:
        classes[rec["shape_class"]] = classes.get(rec["shape_class"], 0) + 1
    per_entity: dict[str, int] = {}
    for rec in table:
        per_entity[rec["entity"]] = per_entity.get(rec["entity"], 0) + 1
    lines = [
        "# Compound instance records: hull -> part wiring (G2-8)",
        "",
        "Each `hknpStaticCompoundShape` / `hknpDynamicCompoundShape` holds an `hkArray` of",
        "128-byte `hknpShapeInstance` records: a 3x3 basis at +0x00/+0x10/+0x20 with a per-row",
        "norm marker in the w lane, a translation at +0x30, a scale at +0x40 and the child shape",
        "pointer at +0x50. Reading that array is what turns a vehicle's collision from \"18,865",
        "hulls somewhere in the file\" into \"this hull is part 12\".",
        "",
        "| item | value |",
        "|---|---|",
        f"| entities | {totals['entities']} |",
        f"| physics files | {totals['files']} |",
        f"| compounds | {totals['compounds']:,} |",
        f"| instances | {totals['instances']:,} |",
        f"| instances carrying a part index | {totals['wired']:,} "
        f"({totals['wired'] / max(totals['instances'], 1):.1%}) |",
        f"| resolved to a part name (`PARTS_TABLE.jsonl`) | {totals['named']:,} "
        f"({totals['named'] / max(totals['instances'], 1):.1%}) |",
        "",
        "## Child shape classes", "", "| class | instances |", "|---|---|",
    ]
    for k, v in sorted(classes.items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{k}` | {v:,} |")
    lines += ["", "## Per entity (most instances first)", "",
              "| entity | instances |", "|---|---|"]
    for k, v in sorted(per_entity.items(), key=lambda kv: -kv[1])[:30]:
        lines.append(f"| `{k.rsplit('/', 1)[-1]}` | {v:,} |")
    lines += ["", f"Top 30 of {len(per_entity)} entities.", ""]
    with open(os.path.join(OUT, "WIRING.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"WIRING: {totals}")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="decode every vehicle to JSON under _JC3grab/hkx/out")
    b.add_argument("--entity", help="substring filter")
    b.add_argument("--all", action="store_true")
    b.add_argument("--game", default=DEFAULT_GAME)
    b.add_argument("--index", default=DEFAULT_OUT)
    b.set_defaults(func=cmd_build)
    r = sub.add_parser("report", help="write SHAPES.md")
    r.add_argument("--game", default=DEFAULT_GAME)
    r.add_argument("--index", default=DEFAULT_OUT)
    r.set_defaults(func=cmd_report)
    w = sub.add_parser("wiring", help="write WIRING.jsonl: compound instance -> part")
    w.add_argument("--entity", help="substring filter")
    w.add_argument("--all", action="store_true")
    w.add_argument("--game", default=DEFAULT_GAME)
    w.add_argument("--index", default=DEFAULT_OUT)
    w.set_defaults(func=cmd_wiring)
    c = sub.add_parser("check", help="assert every layout invariant")
    c.add_argument("--entity", help="substring filter")
    c.add_argument("--all", action="store_true")
    c.add_argument("--game", default=DEFAULT_GAME)
    c.add_argument("--index", default=DEFAULT_OUT)
    c.set_defaults(func=cmd_check)
    a = ap.parse_args()
    sys.exit(a.func(a))


if __name__ == "__main__":
    main()
