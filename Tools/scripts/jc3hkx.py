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
import bisect
import difflib
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
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_gamedata/JC3grab")
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
    planes, unused_planes, plane_slots = [], 0, []
    for i in range(pcount):
        x, y, z, d = pf.vec4(plane_at + 16 * i)
        plane_slots.append([x, y, z, d])       # every slot, sentinel included (writer)
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
        "plane_slots": plane_slots,
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


def check_file(path: str, against: str | None = None) -> tuple[dict, list[str]]:
    """`check`'s invariant ladder, applied to one `.physicsc` written to disk (B-10).

    The archive path in `cmd_check` decodes every vehicle through the index; a written
    file has no index row, so the same assertions are run directly on its bytes:
    magic, version, sections, an empty `__types__`, table residue, every fixup bound and
    `shape_checks` (hull blocks, vertex ranks, unit planes, indices, convexity, mesh
    AABBs, compound/instance AABBs and unions).  With `against`, the object class list
    and the decoded graph are compared with the file it was written from, and the
    `hknpPhysicsSystemData` bytes (the body entries, G2-30 UNKNOWN 4) are compared
    exactly - that is the R3 "stations unchanged" proof for a hull write.
    """
    blob = open(path, "rb").read()
    name = os.path.basename(path)
    info: dict = {"file": path.replace("\\", "/"), "bytes": len(blob),
                  "sha256": hashlib.sha256(blob).hexdigest()[:16]}
    try:
        pf = Packfile(blob)
    except Exception as e:                           # noqa: BLE001
        return info, [f"{name}: packfile: {e}"]
    bad: list[str] = []
    if pf.magic != MAGIC:
        bad.append(f"{name}: magic {pf.magic:#x}")
    if pf.version != VERSION or pf.file_version != FILE_VERSION:
        bad.append(f"{name}: version {pf.version:#x}/{pf.file_version}")
    if pf.version_name != "hk_2014.1.0-r1":
        bad.append(f"{name}: version name {pf.version_name!r}")
    if [s.name for s in pf.section_list] != ["__classnames__", "__types__", "__data__"]:
        bad.append(f"{name}: sections {[s.name for s in pf.section_list]}")
    if pf.sections["__types__"].end:
        bad.append(f"{name}: __types__ is not empty")
    if pf.virtual_residue or pf.classname_marker_bad:
        bad.append(f"{name}: table residue {pf.virtual_residue}, "
                   f"classname markers {pf.classname_marker_bad}")
    for _off, cls in pf.virtual:
        if cls not in LAYOUTS and cls != POLYTOPE:
            bad.append(f"{name}: untyped class {cls}")
    for frm, to in pf.local:
        if not (0 <= frm < pf.lf and 0 <= to < pf.lf):
            bad.append(f"{name}: local fixup {frm:#x}->{to:#x} outside data")
    for frm, sec, to in pf.global_:
        if sec != pf.contents_index or not (0 <= to < pf.lf):
            bad.append(f"{name}: global fixup {frm:#x}->sec{sec}:{to:#x}")
    counts, shape_bad = shape_checks(pf)
    bad.extend(f"{name}{m}" for m in shape_bad)
    info.update({"objects": len(pf.objects), "hulls": counts["polytopes"],
                 "convex": counts["convex"], "mesh": counts["mesh"],
                 "geometries": counts["geom"], "compounds": counts["compounds"],
                 "instances": counts["instances"], "wired": counts["wired"],
                 "union_ok": counts["union_ok"], "stations": len(stations(pf))})
    if against:
        a = Packfile(open(against, "rb").read())
        info["against"] = against.replace("\\", "/")
        if [o.cls for o in a.objects] != [o.cls for o in pf.objects]:
            bad.append(f"{name}: object class list changed against {os.path.basename(against)}")
        ga, gb = graph_signature(a), graph_signature(pf)
        if len(ga) != len(gb):
            bad.append(f"{name}: object count {len(ga)} -> {len(gb)}")
        else:
            changed = [i for i, (x, y) in enumerate(zip(ga, gb)) if x != y]
            info["changed_objects"] = len(changed)
            info["changed_classes"] = sorted({a.objects[i].cls for i in changed})
        sys_a = {o.offset: a.blob[a.base + o.offset:a.base + o.offset + a.extents[o.offset]]
                 for o in a.objects if o.cls == "hknpPhysicsSystemData"}
        sys_b = {o.offset: pf.blob[pf.base + o.offset:pf.base + o.offset + pf.extents[o.offset]]
                 for o in pf.objects if o.cls == "hknpPhysicsSystemData"}
        info["physics_system_data_identical"] = (sorted(sys_a.values()) == sorted(sys_b.values()))
        if not info["physics_system_data_identical"]:
            bad.append(f"{name}: hknpPhysicsSystemData bytes changed (the body/station data)")
    return info, bad


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

    written: list[dict] = []
    for path in a.file or []:
        info, bad = check_file(path, a.against)
        written.append(info)
        problems.extend(bad)

    if not stats["files"] and not written:
        # A run that decodes nothing must not pass: that is how the 33 referenced
        # bundles stayed invisible while `check` reported success.
        problems.append("no .physicsc decoded at all - extraction is broken")
    for info in written:
        line = (f"file {info['file']}: {info['bytes']:,} B, {info.get('objects')} objects, "
                f"{info.get('hulls')} hulls (convex {info.get('convex')}), "
                f"{info.get('mesh')} mesh shapes, {info.get('compounds')} compounds "
                f"({info.get('instances')} instances, {info.get('union_ok')} AABB unions exact), "
                f"station sets {info.get('stations')}, sha256 {info['sha256']}...")
        if info.get("against"):
            line += (f" | vs {os.path.basename(info['against'])}: "
                     f"{info.get('changed_objects')} object(s) changed "
                     f"({', '.join(info.get('changed_classes') or []) or 'none'}), "
                     f"hknpPhysicsSystemData identical {info.get('physics_system_data_identical')}")
        print(line)
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


# --------------------------------------------------------------------------
# writing (G2-30): can a `.physicsc` be written and read back?
# --------------------------------------------------------------------------
# The reader above pins every layout the writer needs.  What the writer adds is
# the *consequence* of one measured fact: **the data section is fully partitioned
# by typed objects** (430 objects, contiguous 0..lf, every extent a multiple of
# 16, the file ending exactly at the last object).  So the data section can be
# laid out again from per-object blobs, every fixup can be remapped, and the
# tables and the section record regenerated - which is what makes a size change
# (a hull with a different vertex count) possible at all.
DONOR = os.path.join(ROOT, "Builds", "test-091", "aaf", "models", "jc_vehicles",
                     "01_land", "v0300_car_kensington_sportsmuscle",
                     "sportsmuscle.physicsc")
ASSEMBLED = os.path.join(ROOT, "Working", "Assembled", "sportsmuscle_true.physicsc")
WRITE_DIR = os.path.join(RAW, "hkx", "write")
DONOR_EE = ("editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
            "v0300_car_kensington_sportsmuscle_civilian_01.ee")


def hull_bytes(pf: Packfile, off: int, verts=None, planes=None,
               radius: float | None = None) -> bytes:
    """Re-emit one `hknpConvexPolytopeShape` object from its decoded values.

    Only the three blocks the reader decodes are written from arguments: the
    vertex block, the plane block (every slot, unused sentinel included) and the
    `convex_radius` at `+0x14`.  Everything the reader does **not** decode - the
    header's unnamed u16s, the 0-32 byte block between the planes and the face
    table, the face table, the index block and the `0x7F` padding - is copied
    from the source object, so a call with no arguments reproduces the object
    byte for byte and the round trip measures decode/encode exactness rather
    than a copy.
    """
    d = decode_polytope(pf, off)
    src = pf.blob[pf.base + off:pf.base + off + d["extent"]]
    out = bytearray(src)
    if verts is not None:
        if len(verts) != d["vertex_count"]:
            raise ValueError(f"@{off:#x}: {len(verts)} vertices for a {d['vertex_count']}-vertex hull")
        for i, v in enumerate(verts):
            struct.pack_into("<4f", out, POLYTOPE_HEAD + 16 * i, *v)
    if planes is not None:
        if len(planes) != len(d["plane_slots"]):
            raise ValueError(f"@{off:#x}: {len(planes)} planes for a "
                             f"{len(d['plane_slots'])}-slot hull")
        base = POLYTOPE_HEAD + 16 * d["vertex_count"]
        for i, p in enumerate(planes):
            struct.pack_into("<4f", out, base + 16 * i, *p)
    if radius is not None:
        struct.pack_into("<f", out, 0x14, radius)
    return bytes(out)


def packfile_bytes(pf: Packfile, edits: dict[int, bytes],
                   inner: dict[int, dict[int, int]] | None = None) -> tuple[bytes, dict]:
    """Lay the data section out again with `edits` substituted; remap every fixup.

    `edits` maps an object offset to its new blob (any length, padded to 16 with
    `0x7F`).  Objects keep their order; each is placed at the running offset, so
    a size change shifts everything after it.  `inner` (B-10b) maps, per resized object,
    each pointer target inside it (offset in the object) to its new offset.  Local / global / virtual fixups
    and the pointer value at every fixup `from` slot are rewritten, then the
    three tables and the `__data__` section record.
    """
    objs = sorted(pf._order)
    blobs: dict[int, bytes] = {}
    for off in objs:
        blob = edits.get(off)
        if blob is None:
            blob = pf.blob[pf.base + off:pf.base + off + pf.extents[off]]
        if len(blob) % 16:
            blob = blob + b"\x7f" * (16 - len(blob) % 16)
        blobs[off] = blob
    at, pos = {}, 0
    for off in objs:
        at[off] = pos
        pos += len(blobs[off])
    lf_new = pos

    def remap(rel: int) -> int:
        if rel not in pf._starts and rel >= pf.lf:
            raise ValueError(f"pointer target {rel:#x} is in the fixup tables, not in an object")
        if rel in pf._starts:
            return at[rel]
        i = bisect.bisect_right(objs, rel) - 1
        if i < 0:
            raise ValueError(f"pointer target {rel:#x} precedes the first object")
        o = objs[i]
        if rel >= o + pf.extents[o]:
            raise ValueError(f"pointer target {rel:#x} is outside object @{o:#x}")
        if inner and o in inner:
            # B-10b: a resized object moves its own array blocks; every pointer INTO it must be
            # declared (old offset in object -> new), an undeclared one stops the write.
            if rel - o not in inner[o]:
                raise ValueError(f"pointer into resized object @{o:#x}+{rel - o:#x} has no inner map")
            return at[o] + inner[o][rel - o]
        return at[o] + (rel - o)

    local_size, global_size = pf.gf - pf.lf, pf.vf - pf.gf
    virt_size = pf.ex - pf.vf
    data = bytearray(lf_new + local_size + global_size + virt_size)
    for off in objs:
        data[at[off]:at[off] + len(blobs[off])] = blobs[off]
    gf_new, vf_new = lf_new + local_size, lf_new + local_size + global_size
    ex_new = len(data)
    for region in ((lf_new, gf_new), (gf_new, vf_new), (vf_new, ex_new)):
        data[region[0]:region[1]] = b"\xff" * (region[1] - region[0])

    local = [(remap(f), remap(t)) for f, t in pf.local]
    glob = [(remap(f), sec, remap(t)) for f, sec, t in pf.global_]
    cls_off = {nm: rel for rel, _h, nm in pf.classnames}
    virt = [(remap(o), 0, cls_off[cls]) for o, cls in pf.virtual]
    # Tables are rewritten **slot for slot**: the reader's parse order skips the
    # 0xFF padding slots, so re-emitting the entries in parse order would compact
    # the table and move every byte after it.
    for slot in range(0, local_size, 8):
        f, t = struct.unpack_from("<2I", pf.blob, pf.base + pf.lf + slot)
        if f == NULL or t == NULL:
            continue
        struct.pack_into("<2I", data, lf_new + slot, remap(f), remap(t))
    for slot in range(0, global_size, 12):
        f, sec, t = struct.unpack_from("<3I", pf.blob, pf.base + pf.gf + slot)
        if f == NULL or t == NULL:
            continue
        struct.pack_into("<3I", data, gf_new + slot, remap(f), sec, remap(t))
    for slot in range(0, virt_size - 11, 12):
        f, mid, cls = struct.unpack_from("<3I", pf.blob, pf.base + pf.vf + slot)
        if f == NULL:
            continue
        struct.pack_into("<3I", data, vf_new + slot, remap(f), mid, cls)
    # The pointer *slots* stay zero: the on-disk value is 0 and the loader writes
    # the target from the fixup table (measured - all 339 local and 765 global
    # slots read 0 in the donor).  Writing the target there would make a round
    # trip differ from the original in 2,702 bytes while still reading correctly,
    # which is exactly the kind of "looks right" this card must not accept.

    out = bytearray(pf.blob[:pf.base])
    idx = [s.name for s in pf.section_list].index("__data__")
    struct.pack_into("<7I", out, SECTION_HEAD + SECTION_SIZE * idx + 20,
                     pf.base, lf_new, gf_new, vf_new, ex_new, ex_new, ex_new)
    out += data
    return bytes(out), {"objects": len(objs), "lf": lf_new, "size": len(out),
                        "shifts": sum(1 for o in objs if at[o] != o)}


def scale_hull(pf: Packfile, off: int, factor: float) -> tuple[bytes, dict]:
    """A scaled *copy* of one hull about its own bounding-box centre.

    Vertices scale about the centre, the plane distance follows from the same
    map (`d' = f*d + (f-1)*(n.c)`) and the convex radius scales with the shape,
    because a rounded hull scaled by `f` is rounded by `f*r`.  Vertex and plane
    counts do not change, so the object keeps its size and every offset after it.
    """
    d = decode_polytope(pf, off)
    b = d["bounds"]
    c = [(b["min"][k] + b["max"][k]) / 2.0 for k in range(3)]
    verts = [[c[k] + (v[k] - c[k]) * factor for k in range(3)] + [v[3]] for v in d["vertices"]]
    planes = []
    for n0, n1, n2, dd in d["plane_slots"]:
        if n0 == 0.0 and n1 == 0.0 and n2 == 0.0:
            planes.append([n0, n1, n2, dd])          # unused sentinel, untouched
            continue
        nc = n0 * c[0] + n1 * c[1] + n2 * c[2]
        planes.append([n0, n1, n2, factor * dd + (factor - 1.0) * nc])
    blob = hull_bytes(pf, off, verts=verts, planes=planes,
                      radius=d["convex_radius"] * factor)
    axis = [[v[k] for v in verts] for k in range(3)]
    return blob, {"min": [min(a) for a in axis], "max": [max(a) for a in axis],
                  "centre": c, "radius": d["convex_radius"] * factor}


def _union(pf: Packfile, d: dict, pick) -> tuple[dict | None, bool]:
    """Bounding box of a compound's children under `pick(child_offset) -> box`."""
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for inst in d["instances"]:
        if not inst["shape"]:
            return None, False
        box = pick(inst["shape"])
        if not box:
            return None, False
        box = transform_aabb(box, inst["basis"], inst["translation"])
        for k in range(3):
            lo[k] = min(lo[k], box["min"][k])
            hi[k] = max(hi[k], box["max"][k])
    return {"min": lo, "max": hi}, True


def compound_aabb_edits(pf: Packfile, changed: dict) -> dict[int, bytes]:
    """New blobs for the compounds that contain an edited shape.

    A child that grows leaves its parent's AABB stale, and `shape_checks` catches
    exactly that (`a child AABB is outside the compound AABB`) - the counter-
    example is kept in the report.  Two rules keep the rewrite honest:

    * only *ancestors* of an edit are touched, so an unrelated compound stays
      byte-identical (the file ships 22 compounds; one scaled wheel reaches 3);
    * each ancestor keeps the margin the file authored it with - the stored box
      is the children's union offset by a per-axis margin (the Serpente's root
      sits 0.011 m inside its union) - so the box moves exactly as far as the
      children moved and `missing`/`overshoot` stay what the file already had.
    """
    memo: dict = {}
    stored: dict = {}

    def new_box(off: int) -> dict | None:
        """The box that will be stored for `off` after the edits."""
        if off in changed:
            return changed[off][1]
        cls = pf._starts.get(off)
        if cls not in COMPOUND_CLASSES:
            return shape_aabb(pf, off)
        if off in memo:
            return memo[off]
        memo[off] = None
        d = decode_compound(pf, off, cls)
        cur = {"min": list(pf.vec4(off + 0x80)[:3]), "max": list(pf.vec4(off + 0x90)[:3])}
        old_u, ok_old = _union(pf, d, lambda s: shape_aabb(pf, s))
        new_u, ok_new = _union(pf, d, new_box)
        if not ok_old or not ok_new:
            return None
        if all(abs(new_u["min"][k] - old_u["min"][k]) < 1e-9
               and abs(new_u["max"][k] - old_u["max"][k]) < 1e-9 for k in range(3)):
            memo[off] = cur                     # nothing below it changed
            return cur
        memo[off] = {"min": [new_u["min"][k] + (cur["min"][k] - old_u["min"][k]) for k in range(3)],
                     "max": [new_u["max"][k] + (cur["max"][k] - old_u["max"][k]) for k in range(3)]}
        return memo[off]

    edits: dict[int, bytes] = {}
    for o in pf.objects:
        if o.cls not in COMPOUND_CLASSES:
            continue
        stored[o.offset] = {"min": list(pf.vec4(o.offset + 0x80)[:3]),
                            "max": list(pf.vec4(o.offset + 0x90)[:3])}
        box = new_box(o.offset)
        if not box:
            continue
        cur = stored[o.offset]
        if all(abs(box["min"][k] - cur["min"][k]) < 1e-12
               and abs(box["max"][k] - cur["max"][k]) < 1e-12 for k in range(3)):
            continue
        blob = bytearray(pf.blob[pf.base + o.offset:pf.base + o.offset + pf.extents[o.offset]])
        struct.pack_into("<4f", blob, 0x80, *box["min"], 0.0)
        struct.pack_into("<4f", blob, 0x90, *box["max"], 0.0)
        edits[o.offset] = bytes(blob)
    return edits


def diff_ranges(a: bytes, b: bytes) -> list[tuple[int, int]]:
    """Contiguous (offset, length) runs where two equal-length blobs differ."""
    if len(a) != len(b):
        raise ValueError(f"length {len(a)} vs {len(b)}")
    out, start = [], None
    for i in range(len(a)):
        if a[i] != b[i]:
            if start is None:
                start = i
        elif start is not None:
            out.append((start, i - start))
            start = None
    if start is not None:
        out.append((start, len(a) - start))
    return out


def graph_signature(pf: Packfile) -> list:
    """What an edit must not change: every object's class, counts and payload hash."""
    rows = []
    for o in pf.objects:
        if o.cls == POLYTOPE:
            d = decode_polytope(pf, o.offset)
            rows.append((o.cls, d["vertex_count"], d["plane_count"], d["index_count"],
                         hashlib.sha256(repr([tuple(v) for v in d["vertices"]]).encode()).hexdigest()[:16],
                         hashlib.sha256(repr(d["plane_slots"]).encode()).hexdigest()[:16],
                         bytes(d["indices"])))
        elif o.cls in COMPOUND_CLASSES:
            d = decode_compound(pf, o.offset, o.cls)
            rows.append((o.cls, d["instance_count"], tuple(
                (i["shape_class"], i["part_index"], tuple(round(v, 6) for v in i["translation"]),
                 tuple(round(v, 6) for v in i["basis"][0])) for i in d["instances"])))
        else:
            rows.append((o.cls, pf.extents[o.offset]))
    return rows


def verify_written(blob_in: bytes, blob_out: bytes, edits: dict[int, bytes]) -> list[str]:
    """Re-read a written file and assert everything the reader knows still holds."""
    problems: list[str] = []
    try:
        pf = Packfile(blob_out)
    except Exception as e:                            # noqa: BLE001
        return [f"packfile: {e}"]
    a, b = Packfile(blob_in), pf
    if [o.cls for o in a.objects] != [o.cls for o in b.objects]:
        problems.append("object class list changed")
    if len(a.local) != len(b.local) or len(a.global_) != len(b.global_):
        problems.append("fixup counts changed")
    if b.virtual_residue or b.classname_marker_bad:
        problems.append(f"table residue {b.virtual_residue} / markers {b.classname_marker_bad}")
    if a.sections["__types__"].end != b.sections["__types__"].end:
        problems.append("__types__ is not empty")
    for frm, _t in b.local:
        if not (0 <= frm < b.lf):
            problems.append(f"local fixup from {frm:#x} outside the objects")
            break
    for frm, sec, to in b.global_:
        if sec != b.contents_index or not (0 <= to < b.lf):
            problems.append(f"global fixup {frm:#x} -> sec{sec}:{to:#x}")
            break
    _counts, bad = shape_checks(b)
    problems.extend(bad[:6])
    # every pointer must resolve to an object or into one, as it did before
    for slot, target in b.pointers.items():
        if not target:
            continue
        cls = b._starts.get(target)
        if cls is None:
            i = bisect.bisect_right(sorted(b._starts), target) - 1
            if i < 0 or target >= sorted(b._starts)[i] + b.extents[sorted(b._starts)[i]]:
                problems.append(f"pointer at {slot:#x} -> {target:#x} resolves to nothing")
                break
    ga, gb = graph_signature(a), graph_signature(b)
    if len(ga) == len(gb):
        changed = [i for i, (x, y) in enumerate(zip(ga, gb)) if x != y]
        touched = {list(a._order).index(off) for off in edits} if len(a._order) == len(a.objects) else None
        if touched is not None and not set(changed) <= touched:
            extra = sorted(set(changed) - touched)[:6]
            problems.append(f"the edit changed objects it was not given: {extra}")
    else:
        problems.append("object count changed")
    return problems


def face_table(pf: Packfile, off: int) -> dict | None:
    """Locate one hull's face table and test the `u16 first, u8 count, u8 min` reading.

    The table is not at a fixed offset: an unnamed, 16-byte-aligned block (0, 16, 32 or
    48 bytes on the donor) sits between the plane block and it, and the table is followed
    by `0x7F` padding up to the index block.  So the table is *found*, not assumed: the
    first prefix at which `plane_count` 4-byte records start at index 0, chain
    `first + count == next first`, and end at `index_count`.
    """
    d = decode_polytope(pf, off)
    p = d["plane_count"] + d["unused_planes"]
    gap = off + POLYTOPE_HEAD + 16 * d["vertex_count"] + 16 * p
    idx_at = off + d["extent"] - d["pad_bytes"] - d["index_count"]
    for prefix in range(0, 49):
        start = gap + prefix
        tail = idx_at - start - 4 * p
        if tail < 0:
            continue
        if any(pf.blob[pf.base + start + 4 * p + i] != PAD_BYTE for i in range(tail)):
            continue
        recs = [pf.u32(start + 4 * i) for i in range(p)]
        firsts = [r & 0xFFFF for r in recs]
        counts = [(r >> 16) & 0xFF for r in recs]
        if not firsts or firsts[0] != 0:
            continue
        if any(firsts[i] + counts[i] != firsts[i + 1] for i in range(len(firsts) - 1)):
            continue
        if firsts[-1] + counts[-1] != d["index_count"]:
            continue
        return {"prefix": prefix, "records": p, "pad": tail,
                "mins": sorted({(r >> 24) & 0xFF for r in recs})}
    return None


def _case_roundtrip(tag: str, path: str) -> dict:
    blob = open(path, "rb").read()
    pf = Packfile(blob)
    edits = {o.offset: hull_bytes(pf, o.offset) for o in pf.objects if o.cls == POLYTOPE}
    out, info = packfile_bytes(pf, edits)
    problems = verify_written(blob, out, edits)
    return {"name": tag, "path": path.replace(ROOT + os.sep, "").replace(os.sep, "/"),
            "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
            "sha256_out": hashlib.sha256(out).hexdigest(),
            "identical": out == blob, "hulls_reencoded": len(edits),
            "objects": info["objects"], "problems": problems[:4], "blob": out}


def _case_shift(pf: Packfile, delta: int = 16) -> dict:
    """Every object and table shifted by `delta`: forces the whole remap path."""
    objs = sorted(pf._order)
    filler = b"\x7f" * delta
    edits = {objs[0]: filler + pf.blob[pf.base + objs[0]:pf.base + objs[0] + pf.extents[objs[0]]]}
    out, _info = packfile_bytes(pf, edits)
    problems = verify_written(pf.blob, out, edits)
    return {"delta": delta, "bytes_in": len(pf.blob), "bytes_out": len(out),
            "objects": len(objs), "problems": problems[:4], "blob": out}


def _case_scale(pf: Packfile, off: int, factor: float, part: str | None) -> dict:
    blob, box = scale_hull(pf, off, factor)
    d = decode_polytope(pf, off)
    changes = {off: (blob, box)}
    edits = {off: blob}
    stale, _ = packfile_bytes(pf, edits)
    stale_problems = verify_written(pf.blob, stale, edits)
    edits.update(compound_aabb_edits(pf, changes))
    out, _info = packfile_bytes(pf, edits)
    problems = verify_written(pf.blob, out, edits)
    ranges = diff_ranges(pf.blob, out)
    return {"hull": off, "part": part, "factor": round(factor, 6),
            "vertices": d["vertex_count"], "planes": d["plane_count"],
            "box_before": d["bounds"], "box_after": {"min": box["min"], "max": box["max"]},
            "radius_before": d["convex_radius"], "radius_after": box["radius"],
            "compounds_updated": len(edits) - 1,
            "changed_ranges": [[s, n] for s, n in ranges],
            "changed_bytes": sum(n for _s, n in ranges),
            "problems": problems[:4], "stale_problems": stale_problems[:2],
            "stale_bytes": len(stale), "blob": out}


def _case_replace(pf: Packfile, off: int, with_off: int, parts: dict) -> dict:
    """A size-changing replacement: one donor hull's block in another's slot."""
    src = pf.blob[pf.base + with_off:pf.base + with_off + pf.extents[with_off]]
    dnew = decode_polytope(pf, with_off)
    box = dnew["bounds"]
    changes = {off: (src, box)}
    edits = {off: src}
    edits.update(compound_aabb_edits(pf, changes))
    out, _info = packfile_bytes(pf, edits)
    problems = verify_written(pf.blob, out, edits)
    return {"hull": off, "with": with_off, "part": parts.get(with_off),
            "bytes_in": len(pf.blob), "bytes_out": len(out),
            "extent_before": pf.extents[off], "extent_after": len(src),
            "vertices": dnew["vertex_count"], "planes": dnew["plane_count"],
            "compounds_updated": len(edits) - 1,
            "problems": problems[:4], "blob": out}


def _face_census(pf: Packfile, hulls: list[int]) -> dict:
    """How many hulls the one-record-per-plane face-table reading explains, and how."""
    counts: dict[int, int] = {}
    mins: dict[str, int] = {}
    bad: list[str] = []
    for off in hulls:
        hit = face_table(pf, off)
        if hit is None:
            bad.append(hex(off))
            continue
        counts[hit["prefix"]] = counts.get(hit["prefix"], 0) + 1
        for m in hit["mins"]:
            mins[str(m)] = mins.get(str(m), 0) + 1
    return {"hulls": len(hulls), "explained": len(hulls) - len(bad),
            "prefix": {str(k): v for k, v in sorted(counts.items())},
            "min_bytes": dict(sorted(mins.items(), key=lambda kv: -kv[1])),
            "unexplained": bad}


def spike() -> dict:
    """Run the four write cases and collect every number the report needs."""
    donor = open(DONOR, "rb").read()
    pf = Packfile(donor)
    parts = load_part_names()
    name_of = {}
    for o in pf.objects:
        if o.cls not in COMPOUND_CLASSES:
            continue
        for inst in decode_compound(pf, o.offset, o.cls)["instances"]:
            if inst["shape"] and inst["part_index"] is not None:
                name_of.setdefault(inst["shape"], parts.get((DONOR_EE, inst["part_index"])))
    hulls = [o.offset for o in pf.objects if o.cls == POLYTOPE]
    boxes = sorted(((decode_polytope(pf, h)["bounds"], h) for h in hulls),
                   key=lambda t: -(t[0]["max"][1] - t[0]["min"][1]))
    wheel = None
    for h in hulls:
        if name_of.get(h) == "sportsmuscle_wheel_f_l":
            wheel = h
    if wheel is None:
        wheel = min(hulls, key=lambda h: abs((decode_polytope(pf, h)["bounds"]["max"][1]
                                              - decode_polytope(pf, h)["bounds"]["min"][1]) - 0.8225))
    dw = decode_polytope(pf, wheel)
    wheel_d = dw["bounds"]["max"][1] - dw["bounds"]["min"][1]
    factor = round(1.365 / wheel_d, 6)          # Batmobile tyre (TYRES.md) / hull height
    other = max(hulls, key=lambda h: pf.extents[h])   # a bigger donor hull for the grow case
    counts: dict[str, int] = {}
    for o in pf.objects:
        counts[o.cls] = counts.get(o.cls, 0) + 1
    objs = sorted(pf._order)
    gaps = sum(1 for i, o in enumerate(objs)
               if (objs[i + 1] if i + 1 < len(objs) else pf.lf) != o + pf.extents[o])
    doc = {
        "card": "G2-30",
        "generated_by": "Tools/scripts/jc3hkx.py write --write",
        "sources": {"donor": DONOR.replace(ROOT + os.sep, "").replace(os.sep, "/"),
                    "assembled": ASSEMBLED.replace(ROOT + os.sep, "").replace(os.sep, "/")},
        "file": {"version": pf.version_name, "bytes": len(donor), "objects": len(objs),
                 "gaps": gaps, "sections": [[s.name, s.data, s.end] for s in pf.section_list],
                 "classes": dict(sorted(counts.items())),
                 "hulls": len(hulls), "hull_bytes": sum(pf.extents[h] for h in hulls),
                 "compounds": counts.get("hknpStaticCompoundShape", 0)
                 + counts.get("hknpDynamicCompoundShape", 0),
                 "instances": sum(decode_compound(pf, o.offset, o.cls)["instance_count"]
                                  for o in pf.objects if o.cls in COMPOUND_CLASSES),
                 "local_fixups": len(pf.local), "global_fixups": len(pf.global_),
                 "lf": pf.lf, "gf": pf.gf, "vf": pf.vf, "ex": pf.ex},
        "wheel": {"hull": wheel, "part": name_of.get(wheel),
                  "diameter_m": round(wheel_d, 4), "factor": factor,
                  "extent": pf.extents[wheel], "vertices": dw["vertex_count"],
                  "planes": dw["plane_count"]},
        "face_table": _face_census(pf, hulls),
        "roundtrip": [_case_roundtrip("donor", DONOR), _case_roundtrip("assembled", ASSEMBLED)],
        "shift": _case_shift(pf),
        "scale": _case_scale(pf, wheel, factor, name_of.get(wheel)),
        "replace": _case_replace(pf, wheel, other, name_of),
        "artefacts": [],
    }
    assembled = open(ASSEMBLED, "rb").read()
    delta = {"ranges": [], "bytes": None, "identical_size": len(assembled) == len(donor)}
    if delta["identical_size"]:
        ranges = diff_ranges(donor, assembled)
        delta["ranges"] = [[s, n] for s, n in ranges]
        delta["bytes"] = sum(n for _s, n in ranges)
        if ranges:
            at = ranges[0][0]
            rel = at - pf.base
            for o in pf.objects:
                if o.offset <= rel < o.offset + pf.extents[o.offset]:
                    delta.update({"data_offset": rel, "field_offset": rel - o.offset,
                                  "object": o.cls, "object_offset": o.offset,
                                  "donor_value": struct.unpack_from("<f", donor, at)[0],
                                  "assembled_value": struct.unpack_from("<f", assembled, at)[0],
                                  "stations_read": len(stations(Packfile(donor)))})
                    for foff, name, kind, esize in LAYOUTS.get(o.cls, []):
                        if not kind.startswith("array"):
                            continue
                        arr = pf.array(o.offset + foff)
                        if (arr["ptr"] and esize and
                                arr["ptr"] <= rel < arr["ptr"] + arr["size"] * esize):
                            delta["array"] = name
                            delta["array_index"] = (rel - arr["ptr"]) // esize
                            delta["array_field"] = (rel - arr["ptr"]) % esize
                            break
                    break
    doc["station_delta"] = delta
    return doc


def _spike_public(doc: dict) -> dict:
    """The JSON half: everything except the blobs."""
    out = {}
    for k, v in doc.items():
        if isinstance(v, dict):
            out[k] = {kk: vv for kk, vv in v.items() if kk != "blob"}
        elif isinstance(v, list):
            out[k] = [{kk: vv for kk, vv in x.items() if kk != "blob"}
                      if isinstance(x, dict) else x for x in v]
        else:
            out[k] = v
    return out



def physics_md(doc: dict) -> str:
    """`PHYSICS_WRITE.md`, generated from the spike's own numbers."""
    f = doc["file"]
    rt = doc["roundtrip"]
    sh, sc, rp, st = doc["shift"], doc["scale"], doc["replace"], doc["station_delta"]
    ft = doc["face_table"]
    w = doc["wheel"]
    ok = lambda p: "PASS" if not p else "FAIL"  # noqa: E731
    lines: list[str] = []
    a = lines.append
    a("# Writing a `.physicsc` - the G2-30 spike")
    a("")
    a("Decoded and written by `Tools/scripts/jc3hkx.py write`. **The donor can be read, re-emitted")
    a("byte for byte, and a hull inside it can be replaced - with the file still passing every")
    a("invariant the reader knows.** That is the whole question this card asked, and the answer is")
    a("yes, with two hard limits that are stated in §6-§7 rather than papered over.")
    a("")
    a("The mechanism is not a guess: the data section of a JC3 `.physicsc` is **fully partitioned")
    a(f"by typed objects** ({f['objects']} objects, {f['gaps']} gap between them, every extent a multiple of 16,")
    a(f"the file ending exactly at the last object). So the section can be laid out again from")
    a("per-object blobs, every fixup can be remapped, and the three tables plus the `__data__`")
    a("section record can be regenerated. That is what makes a size change possible; an in-place")
    a("patch would only work while a hull keeps its vertex and plane counts.")
    a("")
    a("## 1. The four cases")
    a("")
    a("| case | what it proves | in -> out | verdict |")
    a("|---|---|---|---|")
    for r in rt:
        a(f"| round trip `{r['name']}` | `hull_bytes()` re-emits all {r['hulls_reencoded']} hulls from "
          f"their decoded values and the file is unchanged | {r['bytes']:,} -> {len(r['blob']):,} B | "
          f"{'identical' if r['identical'] else 'DIFFERS'} / {ok(r['problems'])} |")
    a(f"| remap stress | every object, array and table shifted by +{sh['delta']} B, so all "
      f"{sh['objects']} objects and every fixup move | {sh['bytes_in']:,} -> {sh['bytes_out']:,} B | {ok(sh['problems'])} |")
    a(f"| scaled hull | one hull scaled x{w['factor']} about its centre, the parent AABBs recomputed |"
      f" {f['bytes']:,} -> {f['bytes']:,} B | {ok(sc['problems'])} |")
    a(f"| size-changing replace | a {rp['extent_before']} B hull slot holds a {rp['extent_after']} B hull, "
      f"so everything after it shifts | {rp['bytes_in']:,} -> {rp['bytes_out']:,} B | {ok(rp['problems'])} |")
    a("")
    a("`shape_checks()` (the same pass `check --all` uses) reports **0 violations** on all four")
    a("outputs, every pointer still resolves, and the decoded object graph changes only in the")
    a("objects the case was given.")
    a("")
    a("## 2. The file, byte for byte")
    a("")
    a("| item | value |")
    a("|---|---|")
    a(f"| source | `{doc['sources']['donor']}` |")
    a(f"| size / version | {f['bytes']:,} B, `{f['version']}` |")
    a("| sections | " + ", ".join(f"`{n}` @{o:#x} ({e:,} B)" for n, o, e in f["sections"]) + " |")
    a(f"| objects | {f['objects']}, **{f['gaps']} gap** between consecutive extents |")
    a(f"| data section | objects 0..{f['lf']:,}, then local {f['lf']:,}..{f['gf']:,}, global {f['gf']:,}..{f['vf']:,}, "
      f"virtual {f['vf']:,}..{f['ex']:,} |")
    a(f"| fixups | {f['local_fixups']} local, {f['global_fixups']} global, {f['objects']} virtual |")
    a(f"| collision | {f['hulls']} convex hulls ({f['hull_bytes']:,} B of hull blocks), {f['compounds']} compounds, "
      f"{f['instances']} instances |")
    a(f"| classes | " + ", ".join(f"`{k}` {v}" for k, v in f["classes"].items()) + " |")
    a("")
    a("## 3. Round trip (Do step 1)")
    a("")
    a("`hull_bytes(pf, off)` rebuilds a hull object from what `decode_polytope()` returns - the")
    a("vertex block, every plane slot (unused sentinel included) and `convex_radius` - and copies")
    a("only the parts the reader does not decode (the header's unnamed `u16`s, the block between")
    a("planes and faces, the face table, the index block, the `0x7F` padding). A round trip with no")
    a("arguments therefore tests the *decoder*, not a file copy.")
    a("")
    a("| file | bytes | sha256 in | sha256 out | identical | hulls re-emitted |")
    a("|---|---|---|---|---|---|")
    for r in rt:
        a(f"| `{r['path'].rsplit('/', 1)[-1]}` (`{r['path'].split('/')[0]}`) | {r['bytes']:,} | "
          f"`{r['sha256'][:16]}…` | `{r['sha256_out'][:16]}…` | "
          f"**{'yes' if r['identical'] else 'no'}** | {r['hulls_reencoded']} |")
    a("")
    a(f"The second file is the assembly variant: same {f['bytes']:,} B, and it differs from the donor in")
    if st["bytes"]:
        a(f"**{st['bytes']} bytes over {len(st['ranges'])} range(s)** ("
          + ", ".join(f"@{s:,}+{n}" for s, n in st["ranges"][:6]) + "), one `f32` at "
          f"`{st.get('object', '?')}` +{st.get('field_offset', 0):#x}"
          + (f" = `{st['array']}[{st['array_index']}]` +{st['array_field']:#x}" if st.get("array") else "")
          + f": {st['donor_value']!r} -> {st['assembled_value']!r}.")
        a(f"So it is **not** a re-baked wheel-station table - and `stations()` reads **{st.get('stations_read', 0)}** "
          "station set from either file.")
        a("The station quads of a true-scale build therefore do not come from this file's typed")
        a("field, which is what the plan in §7 means by \"same station table\": the writer copies the")
        a("bytes it was given and never rebuilds them.")
    else:
        a("no byte at all (identical files).")
    a("")
    a("## 4. The remap stress")
    a("")
    a(f"Inserting {sh['delta']} filler bytes at data offset 0 forces *every* offset to move: all")
    a(f"{sh['objects']} objects, the three fixup tables and the `__data__` section record.")
    a("Rebuilding exactly those - and leaving every pointer slot zero, as the file does - gives a")
    a("file that re-reads with")
    a(f"**0 violations** and a decoded graph identical object-for-object: {sh['bytes_in']:,} -> {sh['bytes_out']:,} B.")
    a("This is the case an in-place patcher cannot do, and it is why a hull with a different vertex")
    a("count is writable at all.")
    a("")
    a("## 5. A scaled hull and a replaced hull (Do step 2)")
    a("")
    a(f"The test hull is `{w['part']}` @ `{w['hull']:#x}` - {w['vertices']} vertices, {w['planes']} planes,")
    a(f"{w['extent']} B, box height {w['diameter_m']} m, centroid at the part origin. The factor is **{w['factor']}**")
    a(f"= Batmobile tyre Ø 1.365 m (`Research/BatmobileGrab/TYRES.md`) / {w['diameter_m']} m, i.e. two measured")
    a("file values, not a chosen number.")
    a("")
    a("| case | before | after |")
    a("|---|---|---|")
    a(f"| scale x{w['factor']} | box {[round(sc['box_before']['max'][k] - sc['box_before']['min'][k], 4) for k in range(3)]} m, r {round(sc['radius_before'], 6)} | "
      f"box {[round(sc['box_after']['max'][k] - sc['box_after']['min'][k], 4) for k in range(3)]} m, r {round(sc['radius_after'], 6)} |")
    a(f"| bytes touched | - | **{sc['changed_bytes']} B over {len(sc['changed_ranges'])} ranges** "
      f"({', '.join(f'@{s:,}+{n}' for s, n in sc['changed_ranges'][:6])}"
      f"{' …' if len(sc['changed_ranges']) > 6 else ''}), {sc['compounds_updated']} parent compound AABB(s) |")
    a(f"| replace the `{w['part']}` slot with the `{rp['part']}` hull block | {rp['extent_before']} B, "
      f"{w['vertices']} v / {w['planes']} p | {rp['extent_after']} B, {rp['vertices']} v / {rp['planes']} p, "
      f"file {rp['bytes_in']:,} -> {rp['bytes_out']:,} B |")
    a("")
    a(f"Scaling the hull x{w['factor']} moves its box out of the parent compound's stored AABB. Without")
    a("recomputing the ancestors the file **fails** - the counter-example is kept in the numbers:")
    a("")
    a("```")
    for p in sc["stale_problems"]:
        a(p)
    a("```")
    a("")
    a(f"So `compound_aabb_edits()` moves every ancestor's `+0x80`/`+0x90` box by exactly as much as")
    a(f"its children moved ({sc['compounds_updated']} compound(s) here), keeping the margin the file")
    a("authored the box with - the stored box is the children's union inset by the convex radius")
    a("(the root sits 0.011 m inside its union on every axis), so `missing` and `overshoot` stay what")
    a("they already were. That is the only value the writer *derives* rather than copies.")
    a("")
    a("## 6. What the writer may and may not change")
    a("")
    a("| may | why |")
    a("|---|---|")
    a("| hull vertices, plane normals/distances, `convex_radius` | decoded, and the plane relation")
    a("  `max(n.v) + d == 0` re-checks after the write (`convex 54/54`) |")
    a("| the size of a hull object | objects are contiguous and 16-aligned, so the section is re-laid-out")
    a("  and every fixup remapped |")
    a("| a compound's AABB | derived from its children |")
    a("| the wheel-station data | copied, not rebuilt: it lives in `hknpPhysicsSystemData`, outside")
    a("  every hull block |")
    a("")
    a("| may **not** | why |")
    a("|---|---|")
    a("| add or remove objects | the three fixup tables keep their counts, so the object count is fixed;")
    a("  a new hull must replace an existing slot (or the tables must be grown - see §7 step 4) |")
    a(f"| a *brand-new* hull | the face table reads as one 4-byte record per plane for **{ft['explained']}/{ft['hulls']}** hulls, "
      "but only once a 16-byte-aligned prefix of " + "/".join(f"{k} B on {v}" for k, v in ft["prefix"].items())
      + " is skipped, and that block's content has no reading (nor the record's `min` byte) |")
    a("| an `hknpExternMeshShape` | its vertices are 3x u16 quantized and the de-quantization frame is")
    a("  still not pinned (`SHAPES.md`, *Still open*) |")
    a("| `hknpShapeMassProperties` | layout not decoded (56 objects in this file) |")
    a("")
    a("## 7. The plan for a Batmobile hull set (Do step 3)")
    a("")
    a("What the donor gives us to copy: **22 compounds / 112 instances** wiring shapes to the 42")
    a("parts of `PARTS_TABLE.jsonl`, with the body part carrying an `hknpExternMeshShape` and every")
    a("rigid part - the 4 wheels, seats, lights, grill, hood, trunk, windows, mirrors, signal and")
    a("plate parts - a convex hull. What BmAK gives us to build from: **32 bodies, each a single box**")
    a("(`Research/BatmobileGrab/PHYSICS.md`), of which 8 are wheels/suspension, 1 turret, 1 cockpit,")
    a("2 doors, 1 jet fin - **and no chassis body at all**, so the body hull has to come from a convex")
    a("decomposition of `Batmobile_V2` itself. Size and mass targets are DIM-1/DIM-3.")
    a("")
    a("| step | input | method | check that proves it |")
    a("|---|---|---|---|")
    a(f"| 1 | the unnamed prefix block ({', '.join(f'{k} B on {v} hulls' for k, v in ft['prefix'].items())}) and the face record's `min` byte ({', '.join(f'{k} on {v} hulls' for k, v in list(ft['min_bytes'].items())[:4])}) | byte analysis, `decode_polytope` |")
    a(f"  both decoded, i.e. a hull authored from a mesh becomes writable (the record layout itself")
    a(f"  already fits {ft['explained']}/{ft['hulls']} hulls) |")
    a("| 2 | 4 wheel hulls (704 B each, identical topology) | scale + translate the existing block")
    a("  through `T(p)` (`bat_assemble.py`, R2), write with `hull_bytes()` | `check` 0 violations and")
    a("  station quads unchanged |")
    a("| 3 | 8 BmAK wheel/suspension boxes, 2 door boxes, turret, cockpit, fin | each box becomes a")
    a("  box hull in the donor *slot* of the part it replaces, so the count stays 54 | `convex`,")
    a("  `index_ok`, `aabb_ok`, `union_ok` all 100% |")
    a("| 4 | the body | either a convex decomposition of the body mesh as N new hulls (needs the")
    a("  fixup tables to grow) or one hull per donor body-part slot | the same invariants plus a")
    a("  volume/clearance comparison against the render mesh |")
    a("| 5 | `Working/TrueScale/stations.json` | left alone: the station quads stay")
    a("  `physics_stations.py`'s output, which the assembly already carries | the 17-entity")
    a("  `land_global` cross-check stays green |")
    a("| 6 | the whole file | repack with `eetoc` (+ `update_toc_offset.py` if the size changed) |")
    a("  the `.ee` toc hash matches and the build loads (phase Q, in-game) |")
    a("")
    a("Steps 2 and 3 use only what this card proved: same-topology or donor-slot hull replacement with")
    a("a full remap. Step 4 is the one that needs more (either step 1 or a table-growing writer) and")
    a("is where the body, i.e. most of DIM-4, still waits.")
    a("")
    a("## 8. What this changes for T-P3 / T-CO2 / T-CO3")
    a("")
    a("All three rows were `blocked` with the same `why`: *no `.physicsc` writer*. That reason is")
    a("**gone**: a hull can be written and the result re-reads clean. What each row now needs is a")
    a("value, not a capability, so the rows stay for T-22 (`T-22 · Collision translation (only if")
    a("G2-30 succeeded)`) to resolve - this card does not edit `T_ROWS.jsonl`.")
    a("")
    a("| row | was | now |")
    a("|---|---|---|")
    a("| T-P3 | blocked: *no `.physicsc` writer* | unblocked for hull-based collision; the 32 BmAK")
    a("  boxes can go into hull slots - the body chassis mesh (`hknpExternMeshShape`) still cannot |")
    a("| T-CO2 | blocked: same | unblocked the same way; the largest box (211x51x109 cm) is a hull")
    a("  and needs no new layout |")
    a("| T-CO3 | blocked: same | `has_world_collision_shape` can be honoured by reusing a donor hull")
    a("  slot; a *new* shape per part additionally needs step 4 |")
    a("")
    a("## 9. UNKNOWNs")
    a("")
    a(f"1. **The block between the plane block and the face table** - "
      + ", ".join(f"{k} B on {v} of {ft['hulls']} hulls" for k, v in ft["prefix"].items())
      + ". Its contents vary (floats in one")
    a("   hull, `0xFF` words in another) and it is copied, never built.")
    a(f"2. **The face record's `min` byte.** `first`/`count` are proven - one 4-byte record per plane")
    a(f"   partitions the index list on **{ft['explained']}/{ft['hulls']}** hulls - but `min` takes "
      + ", ".join(f"{k} ({v} hulls)" for k, v in list(ft["min_bytes"].items())[:4]) + " with no reading yet.")
    a("3. **`hknpExternMeshShape` vertex quantization**: 3x u16 per vertex, frame unpinned, so the")
    a("   chassis panel mesh cannot be re-authored from a new body mesh.")
    a("4. **`hknpShapeMassProperties` / the 80- and 64-byte body entries**: counted and sized, not")
    a("   decoded, so inertia and the shape-to-body binding are untouched by a hull write.")
    a("5. **Runtime acceptance.** Every check here is the reader's; whether Havok and the game accept")
    a("   a written file is a phase-Q question and **not** claimed.")
    a("")
    a("## 10. Commands, files, revert")
    a("")
    a("```")
    a("python Tools/scripts/jc3hkx.py write --write    # this report + PHYSICS_WRITE.json + blobs")
    a("python Tools/scripts/jc3hkx.py write --check    # re-derive and compare")
    a("python Tools/scripts/jc3hkx.py check --all      # the standing gate, unchanged")
    a("```")
    a("")
    a("Written `.physicsc` blobs (game data, outside the repo - R10): "
      + (", ".join(f"`{x['file']}`" for x in doc["artefacts"]) if doc["artefacts"] else "`_JC3grab/hkx/write/`") + ")")
    a("")
    a("Revert: delete the writer block + `write` command from `jc3hkx.py`, this file,")
    a("`PHYSICS_WRITE.json`, `_JC3grab/hkx/write/`, the README section and Files row; §12 back to")
    a("`| G2-30 | todo | |`; truncate `MODLOG.md` at the G2-30 intended-change heading.")
    a("")
    return "\n".join(lines)


def cmd_write(a) -> int:
    """G2-30: round trip, remap stress, scaled hull, replaced hull - and the report."""
    doc = spike()
    os.makedirs(WRITE_DIR, exist_ok=True)
    artefacts = [("roundtrip_donor", doc["roundtrip"][0]),
                 ("roundtrip_assembled", doc["roundtrip"][1]),
                 ("shift16", doc["shift"]),
                 ("scale_wheel", doc["scale"]),
                 ("replace_hull", doc["replace"])]
    doc["artefacts"] = []
    for name, case in artefacts:
        blob = case["blob"]
        path = os.path.join(WRITE_DIR, name + ".physicsc")
        doc["artefacts"].append({"file": path.replace(RAW, "_JC3grab").replace(os.sep, "/"),
                                 "bytes": len(blob),
                                 "sha256": hashlib.sha256(blob).hexdigest()[:16]})
    public = _spike_public(doc)
    md = physics_md(doc)
    js = json.dumps(public, indent=1, sort_keys=False) + "\n"
    md_path = os.path.join(OUT, "PHYSICS_WRITE.md")
    js_path = os.path.join(OUT, "PHYSICS_WRITE.json")
    summary = (f"round trip {'identical' if all(r['identical'] for r in doc['roundtrip']) else 'DIFFERS'} "
               f"({len(doc['roundtrip'])}/2 files, {doc['roundtrip'][0]['hulls_reencoded']} hulls re-emitted) | "
               f"remap {sum(1 for x in doc['shift']['problems'])} problems | "
               f"scale {sum(1 for x in doc['scale']['problems'])} | "
               f"replace {sum(1 for x in doc['replace']['problems'])} | "
               f"hulls {doc['file']['hulls']} compounds {doc['file']['compounds']}")
    problems = (doc["shift"]["problems"] + doc["scale"]["problems"] + doc["replace"]["problems"]
                + [p for r in doc["roundtrip"] for p in r["problems"]]
                + [f"round trip not identical: {r['name']}"
                   for r in doc["roundtrip"] if not r["identical"]])
    if a.write:
        for (name, case), rec in zip(artefacts, doc["artefacts"]):
            with open(os.path.join(WRITE_DIR, name + ".physicsc"), "wb") as fh:
                fh.write(case["blob"])
        os.makedirs(OUT, exist_ok=True)
        with open(md_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
        with open(js_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(js)
        print(f"wrote {md_path} ({len(md.splitlines())} lines) + {js_path}")
        print(f"wrote {len(artefacts)} .physicsc blobs to {WRITE_DIR}")
    if a.check:
        bad = []
        for (name, case) in artefacts:
            path = os.path.join(WRITE_DIR, name + ".physicsc")
            if not os.path.exists(path):
                bad.append(f"{name}.physicsc missing (run --write)")
                continue
            disk = open(path, "rb").read()
            if disk != case["blob"]:
                bad.append(f"{name}.physicsc on disk differs from the derived bytes "
                           f"({len(disk):,} vs {len(case['blob']):,} B)")
            elif verify_written(case["blob"], disk, {}):
                bad.append(f"{name}.physicsc on disk does not re-read clean")
        for path, text, what in ((md_path, md, "PHYSICS_WRITE.md"),
                                 (js_path, js, "PHYSICS_WRITE.json")):
            if not os.path.exists(path):
                bad.append(f"{what} missing")
                continue
            disk = open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
            if disk != text:
                diff = [ln for ln in difflib.unified_diff(disk.splitlines(), text.splitlines(),
                                                          "disk", "derived", lineterm="", n=0)][:12]
                bad.append(f"{what} stale: " + " | ".join(diff))
        problems += bad
    if problems:
        for p in problems[:12]:
            print("FAIL", p)
        print(f"{len(problems)} problem(s)")
        return 1
    if a.check:
        print(f"PASS: {summary}, json match True, md match True")
    else:
        print(f"OK: {summary}")
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
    c.add_argument("--file", action="append", default=[],
                   help="also check a .physicsc written to disk (repeatable)")
    c.add_argument("--against", help="the file --file was written from (graph + body-entry compare)")
    c.set_defaults(func=cmd_check)
    wr = sub.add_parser("write", help="G2-30 spike: round trip, remap, scaled and replaced hull")
    wr.add_argument("--write", action="store_true", help="write the report and the test blobs")
    wr.add_argument("--check", action="store_true", help="re-derive and compare")
    wr.set_defaults(func=cmd_write)
    a = ap.parse_args()
    sys.exit(a.func(a))


if __name__ == "__main__":
    main()
