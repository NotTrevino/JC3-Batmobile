#!/usr/bin/env python3
"""grab_skins.py - BmAK skins: MK2, Jokerfied, Standard, and the Playable baseline (G3-05b).

Decodes, from the cooked packages themselves, the four Batmobile skeletal meshes:

    Showcase_Batmobiles_Standard.upk    SkeletalMesh  Batmobile_V2
    Showcase_Batmobiles_MK2.upk         SkeletalMesh  Batmobile_MK2_Skin
    Showcase_Batmobiles_Jokerfied.upk    SkeletalMesh  Batmobile_Jokerfied_Skin
    Playable_Batmobile_SF.upk           SkeletalMesh  Batmobile_V2   (the drivable car)

for each: the mesh's material-slot array and the MIC/Material chain behind every slot,
the mesh's SkeletalMeshSockets, the PhysicsAsset and its RB_BodySetups, the LOD blocks,
and how each skin differs from `Playable_Batmobile_SF`'s `Batmobile_V2`.

Writes:
    Research/BatmobileGrab/SKINS.md
    Research/BatmobileGrab/SKINS.json

Labels on every value (the project rule):
    decoded  read from bytes - the source is an export index plus a byte offset in the
             export payload, or a package + export index
    derived  computed from decoded values, with the rule stated next to it
    UNKNOWN  not decoded; the reason says what was tried and where it would be found

Nothing here is taken from Arkham Knight, UE3 or JC3 knowledge: every layout used is
either stated in this file's docstring with the oracle that proves it, or marked UNKNOWN.

Layouts used, and what proves them
----------------------------------
SkeletalMeshSocket payload - three shapes, all closing on their 2-byte terminator:
    4 tags: NameProperty at class offset 0x54 (socket name), NameProperty at 0x5c (bone),
            VectorProperty at 0x64 (relative location), RotatorProperty at 0x70 (relative
            rotation) -> 4*4 + 8 + 8 + 12 + 12 + 2 = 58 bytes;
    3 tags: name, bone, relative location -> 4*3 + 8 + 8 + 12 + 2 = 42 bytes;
    2 tags: name, bone -> 4*2 + 8 + 8 + 2 = 26 bytes.
    Oracle: `size == 4*tag_count + 8*names + 12*location + 12*rotation + 2` on every socket
    (asserted by --check); the shapes are counted in SKINS.md, so a socket with no stored
    rotation is visible instead of being silently given one.

Mesh material-slot array (not a property tag; it sits in the mesh's untagged data):
    int32 count, then count * int32 object references.
    Oracle 1 (containment): every non-zero reference resolves to an export of class
    MaterialInstanceConstant or Material, and no other position in the first 32 KiB of the
    payload satisfies that for 8 or more consecutive references.
    Oracle 2 (independent read): for `Batmobile_V2` the decoded order equals the
    `Materials[19]` list in Working/Appearance/grab/Playable_Batmobile_SF/SkeletalMesh3/
    Batmobile_V2.props.txt (an umodel props dump, not this decoder) - same 19 names, same
    order.  Verified by --check; the comparison is recorded in the JSON.
    The element is 4 bytes, so the slot's FName is not in the cooked mesh: a slot is
    identified by the material object it points at, not by a stored name.

SkeletalMeshLODInfo (ArrayProperty payload): int32 count, then `count` property-tag
    streams, each terminated by the 2-byte 00 00.  Oracle: the element streams consume the
    LODInfo payload exactly (sum of element sizes == the array's recorded size).

PhysicsAsset / RB_BodySetup / AggGeom: decoded by `grab_collision_geom.py`'s own
    functions (`agg_of`, `header`, `boxes_tagged`, `decode_static`), so the box geometry in
    this file is the same decode as COLLISION_GEOM.md - not a second implementation.

Usage:
    uv run --with numpy --with pillow python Tools/scripts/grab_skins.py --write
    uv run --with numpy --with pillow python Tools/scripts/grab_skins.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

import grab_collision_geom as CG  # noqa: E402  (the project's AggGeom decoder)
import upk_read as U  # noqa: E402

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
OUT = os.path.join(REPO, "Research", "BatmobileGrab")
MD_PATH = os.path.join(OUT, "SKINS.md")
JSON_PATH = os.path.join(OUT, "SKINS.json")

# The independent read of the Playable mesh's material list (umodel props dump, GRB-10).
PROPS = os.path.join(REPO, "Working", "Appearance", "grab", "Playable_Batmobile_SF",
                     "SkeletalMesh3", "Batmobile_V2.props.txt")

MATERIAL_CLASSES = ("MaterialInstanceConstant", "Material")
SLOT_NAMES = ("DiffuseColor", "SpecularColor", "SpecularPower", "Normal", "EmissiveColor")

PACKAGES = (
    {"key": "playable", "role": "baseline",
     "package": "Playable_Batmobile_SF", "mesh": "Batmobile_V2"},
    {"key": "standard", "role": "showcase",
     "package": "Showcase_Batmobiles_Standard", "mesh": "Batmobile_V2"},
    {"key": "mk2", "role": "showcase",
     "package": "Showcase_Batmobiles_MK2", "mesh": "Batmobile_MK2_Skin"},
    {"key": "jokerfied", "role": "showcase",
     "package": "Showcase_Batmobiles_Jokerfied", "mesh": "Batmobile_Jokerfied_Skin"},
)
BASELINE = "playable"
SCAN_WINDOW = 0x8000          # the slot array is at 0x2063 / 0x2099 / 0x26c1; 32 KiB is roomy


# --------------------------------------------------------------------------- helpers

def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def i32(b, o):
    return struct.unpack_from("<i", b, o)[0]


def sha1(b):
    return hashlib.sha1(b).hexdigest()


def tag_names(tags, type_):
    return [t.get("value") for t in tags if t.get("type") == type_]


def named(tags, name):
    return next((t for t in tags if t.get("name") == name), None)


def tag_span(tag):
    """(header_start, payload_start, payload_end) of a tag, from its recorded `at`."""
    at = tag["at"]
    start = at - (20 if "name" in tag else 4)
    return start, at, at + (tag.get("size") or 0)


# --------------------------------------------------------------------------- package

class Skin:
    """One package: the mesh, its slots, sockets, LODs and the package's PhysicsAsset(s)."""

    def __init__(self, spec):
        self.key = spec["key"]
        self.role = spec["role"]
        self.name = spec["package"]
        self.mesh_name = spec["mesh"]
        self.path = os.path.join(GAME, self.name + ".upk")
        self.pkg = U.Package(self.path)
        self.bytes = os.path.getsize(self.path)
        self.mesh = self._find(self.mesh_name, "SkeletalMesh")
        self.data = self.pkg.data(self.mesh)
        self.tags, self.tags_end, self.tags_stop = U.walk_tags(self.pkg, self.data)
        self.material_exports = {i for i in range(1, self.pkg.export_count + 1)
                                 if self.pkg.object_class(i) in MATERIAL_CLASSES}

    def _find(self, name, cls):
        hits = [i for i in range(1, self.pkg.export_count + 1)
                if self.pkg.object_class(i) == cls and self.pkg.object_name(i) == name]
        if not hits:
            raise SystemExit("%s has no %s named %r" % (self.name, cls, name))
        return hits[0]

    def class_of(self, index):
        return self.pkg.object_class(index)


# --------------------------------------------------------------------------- mesh parts

def decode_sockets(skin):
    """Sockets array -> per-socket record.  Identity comes from the socket's own name tag."""
    tag = named(skin.tags, "Sockets")
    if not tag:
        return {"verdict": "UNKNOWN", "reason": "the mesh carries no Sockets tag", "sockets": []}
    out, fails = [], []
    for ref in tag.get("refs") or []:
        idx = ref["index"]
        s = U.export_summary(skin.pkg, idx)
        names = tag_names(s["tags"], "NameProperty")
        vec = next((t.get("value") for t in s["tags"] if t.get("type") == "VectorProperty"), None)
        rot = next((t.get("value") for t in s["tags"] if t.get("type") == "RotatorProperty"), None)
        # accounting: 4 bytes per tag header + 8 per name + 12 per vector/rotator + 2 terminator
        expected = (4 * s["tag_count"] + 8 * len(names)
                    + 12 * (1 if vec is not None else 0)
                    + 12 * (1 if rot is not None else 0) + 2)
        if len(names) < 2 or s["size"] != expected or s["parsed_bytes"] != expected - 2:
            fails.append({"index": idx, "tags": s["tag_count"], "size": s["size"],
                          "parsed": s["parsed_bytes"], "expected": expected,
                          "stop": s["stop"]})
        out.append({"socket": names[0] if names else None,
                    "bone": names[1] if len(names) > 1 else None,
                    "location_uu": vec, "rotation_uu": rot,
                    "has_location": vec is not None, "has_rotation": rot is not None,
                    "shape": "%dt" % s["tag_count"],
                    "export": idx, "bytes": s["size"]})
    return {"verdict": "decoded" if not fails else "partial",
            "array_count": tag.get("count"),
            "sockets": out,
            "accounting_failures": fails,
            "label": "decoded (ArrayProperty Sockets -> SkeletalMeshSocket exports; each socket's "
                     "4 offset-only tags: name@0x54, bone@0x5c, location@0x64, rotation@0x70)"}


def decode_slots(skin):
    """The mesh's material-slot array: find the count+refs run whose refs are all materials."""
    d = skin.data
    limit = min(len(d), SCAN_WINDOW)
    candidates = []
    for pos in range(0, limit - 4):
        n = i32(d, pos)
        if not (8 <= n <= 512) or pos + 4 + 4 * n > len(d):
            continue
        refs = [i32(d, pos + 4 + 4 * k) for k in range(n)]
        nonnull = [r for r in refs if r]
        if len(nonnull) < 8:
            continue
        if all(r in skin.material_exports for r in nonnull):
            candidates.append((pos, n, refs))
    if len(candidates) != 1:
        return {"verdict": "UNKNOWN",
                "reason": "%d candidate count+reference runs in the first %d bytes; a unique "
                          "candidate is required" % (len(candidates), limit),
                "candidates": [{"at": p, "count": n} for p, n, _ in candidates],
                "slots": []}
    pos, n, refs = candidates[0]
    slots = []
    for k, r in enumerate(refs):
        if r == 0:
            slots.append({"slot": k, "material": None, "class": None, "export": 0,
                          "at": pos + 4 + 4 * k,
                          "label": "decoded (int32 reference = 0: empty slot)"})
        else:
            slots.append({"slot": k, "material": skin.pkg.object_name(r),
                          "class": skin.pkg.object_class(r), "export": r,
                          "at": pos + 4 + 4 * k,
                          "label": "decoded (int32 reference at payload byte %d)"
                                   % (pos + 4 + 4 * k)})
    return {"verdict": "decoded",
            "count_at": pos, "refs_at": pos + 4, "count": n,
            "slots": slots,
            "nonnull": sum(1 for s in slots if s["material"]),
            "label": "decoded (int32 count then count * int32 object references; every non-zero "
                     "reference resolves to a MaterialInstanceConstant or Material export of "
                     "this package, and no other 8+-reference run in the first %d bytes does)"
                     % limit}


def decode_lods(skin):
    """LODInfo: count then count terminated property-tag streams."""
    tag = named(skin.tags, "LODInfo")
    if not tag:
        return {"verdict": "UNKNOWN", "reason": "the mesh carries no LODInfo tag", "lods": []}
    d, off, end = skin.data, tag["at"], tag["at"] + tag["size"]
    n = i32(d, off)
    off += 4
    lods, fails = [], []
    for k in range(n):
        sub, stop, why = U.walk_tags(skin.pkg, d, off)
        if why == "end":
            nxt = stop + 2
        elif why == "eof":
            nxt = stop
        else:
            nxt = stop
        fields = {}
        floats = [t.get("value") for t in sub if t.get("type") == "FloatProperty"]
        if floats:
            fields["display_factor"] = floats[0]
        if len(floats) > 1:
            fields["lod_hysteresis"] = floats[1]
        for t in sub:
            if t.get("name"):
                fields[t["name"]] = t.get("count") if t.get("type") == "ArrayProperty" else t.get("value")
        if not sub or nxt <= off:
            fails.append({"lod": k, "at": off, "stop": why, "tags": len(sub)})
            break
        lods.append({"lod": k, "at": off, "bytes": nxt - off, "tags": len(sub),
                     "fields": fields})
        off = nxt
    return {"verdict": "decoded" if not fails and off == end else "partial",
            "count": n, "payload_bytes": tag["size"], "consumed": off - tag["at"],
            "lods": lods, "failures": fails,
            "label": "decoded (ArrayProperty LODInfo: count, then terminated tag streams; the "
                     "streams consume the payload)"}


# --------------------------------------------------------------------------- materials

def parent_of(skin, index):
    """The MIC/Material this object instantiates: an object reference to a material export."""
    s = U.export_summary(skin.pkg, index)
    for t in s["tags"]:
        ref = t.get("value")
        if not isinstance(ref, int) or not ref or ref == index:
            continue
        cls = skin.pkg.object_class(ref)
        if cls in MATERIAL_CLASSES:
            return {"export": ref, "name": skin.pkg.object_name(ref), "class": cls,
                    "tag_offset": t.get("offset"),
                    "label": "decoded (object reference at class offset %s)" % (
                        hex(t["offset"]) if t.get("offset") is not None else "?")}
    return None


def params_of(skin, index):
    """Scalar / vector / texture parameter arrays of a MaterialInstanceConstant."""
    s = U.export_summary(skin.pkg, index)
    out = {"scalars": {}, "vectors": {}, "textures": {}}
    for kind, key in (("scalars", "ScalarParameterValues"),
                      ("vectors", "VectorParameterValues"),
                      ("textures", "TextureParameterValues")):
        tag = named(s["tags"], key)
        for item in (tag or {}).get("items") or []:
            if not isinstance(item, list):
                continue
            name = next((x.get("value") for x in item if x.get("type") == "NameProperty"
                         and isinstance(x.get("value"), str)), None)
            if not name:
                continue
            val = next((x.get("value") for x in item
                        if x.get("type") in ("FloatProperty", "VectorProperty")), None)
            if val is None:
                vtag = next((x for x in item if x.get("name") == "ParameterValue"), None)
                val = (vtag or {}).get("floats")
            if val is None:
                ref = next((x for x in item
                            if x.get("type") in ("ObjectNCRProperty", "ObjectProperty")), None)
                if ref is not None:
                    idx = ref.get("value")
                    val = {"export": idx, "object": skin.pkg.object_name(idx) if idx else None,
                           "class": skin.pkg.object_class(idx) if idx else None}
            if val is None:
                continue
            out[kind][name] = {"value": val, "array": key,
                               "tag_offset": (tag or {}).get("offset")}
    return out


def master_slots(skin, index):
    """A Material's DiffuseColor / ... slot -> expression reference (the MATERIALS.md shape)."""
    s = U.export_summary(skin.pkg, index)
    out = {}
    for tag in s["tags"]:
        if tag.get("name") not in SLOT_NAMES:
            continue
        props = tag.get("props") or []
        ref = next((x for x in props if x.get("value")), None)
        out[tag["name"]] = {
            "at": tag.get("at"), "type": tag.get("type"),
            "expression": (ref or {}).get("ref"),
            "expression_class": (ref or {}).get("ref_class"),
            "expression_export": (ref or {}).get("value"),
            "label": "decoded (the slot tag's own payload at payload byte %s)" % tag.get("at"),
        }
    return out


def chain_of(skin, index, seen=None):
    """Chain from a slot object up to the master Material, with each step's parameters."""
    seen = seen or set()
    steps = []
    cur = index
    while cur and cur not in seen and len(steps) < 8:
        seen.add(cur)
        s = U.export_summary(skin.pkg, cur)
        step = {
            "export": cur,
            "name": skin.pkg.object_name(cur),
            "class": skin.pkg.object_class(cur),
            "outer": skin.pkg.object_path(skin.pkg.exports[cur - 1]["outer_index"]),
            "bytes": s["size"], "tags": s["tag_count"], "stop": s["stop"],
            "sha1": sha1(skin.pkg.data(cur)),
            "params": params_of(skin, cur),
        }
        if skin.pkg.object_class(cur) == "Material":
            step["material_slots"] = master_slots(skin, cur)
            steps.append(step)
            break
        nxt = parent_of(skin, cur)
        if nxt:
            step["parent"] = nxt
            steps.append(step)
            cur = nxt["export"]
        else:
            step["parent"] = None
            steps.append(step)
            break
    return steps


# --------------------------------------------------------------------------- physics

def physics_assets(skin):
    out = []
    for i in range(1, skin.pkg.export_count + 1):
        if skin.pkg.object_class(i) != "PhysicsAsset":
            continue
        s = U.export_summary(skin.pkg, i)
        body_tag = named(s["tags"], "BodySetup")
        bounds_tag = named(s["tags"], "BoundsBodies")
        boundsf_tag = named(s["tags"], "Bounds")
        rec = {
            "export": i, "name": skin.pkg.object_name(i), "bytes": s["size"],
            "outer": skin.pkg.object_path(skin.pkg.exports[i - 1]["outer_index"]),
            "body_count": (body_tag or {}).get("count"),
            "bounds_bodies_count": (bounds_tag or {}).get("count"),
            "bounds_count": (boundsf_tag or {}).get("count"),
            "object_refs": [{"value": t.get("value"), "ref": t.get("ref")}
                            for t in s["tags"]
                            if t.get("type") in ("ObjectNCRProperty", "ObjectProperty")],
            "bodies": [],
            "label": "decoded (ArrayProperty BodySetup / BoundsBodies / Bounds counts and their "
                     "object references)",
        }
        out.append(rec)
        for ref in (body_tag or {}).get("refs") or []:
            idx = ref["index"]
            agg, size, tags = CG.agg_of(skin.pkg, idx)
            bones = tag_names(tags, "NameProperty")
            body = {
                "export": idx,
                "bytes": size,
                "bone": bones[0] if bones else None,
                "agggeom_bytes": len(agg) if agg else None,
                "label": "decoded (NameProperty inside the RB_BodySetup's tags)",
            }
            if agg:
                hdr = CG.header(agg)
                body["agg_header_u32"] = {
                    "words": hdr,
                    "label": "decoded (words 0..3 of the AggGeom payload; the project's "
                             "COLLISION_GEOM.md labels word 0 spheres, word 1 boxes, word 2 "
                             "sphyl, word 3 convex count when it is small)",
                }
                boxes = CG.boxes_tagged(agg)
                body["boxes"] = boxes
                body["box_count_word"] = hdr[1]
                body["box_count_matches_word1"] = (hdr[1] == len(boxes))
                if hdr[3] and hdr[3] < 256:
                    c0 = CG.convex0(agg)
                    body["convex_element_0"] = {"vertices": c0["nV"], "triangles": c0["nI"] // 3}
            rec["bodies"].append(body)
    return out


def physics_instance(skin):
    out = []
    for i in range(1, skin.pkg.export_count + 1):
        if skin.pkg.object_class(i) != "PhysicsAssetInstance":
            continue
        s = U.export_summary(skin.pkg, i)
        bodies = [t for t in s["tags"] if t.get("type") == "ArrayProperty"
                  and "RB_BodyInstance" in str(t.get("name") or "")]
        out.append({"export": i, "name": skin.pkg.object_name(i), "bytes": s["size"],
                    "outer": skin.pkg.object_path(skin.pkg.exports[i - 1]["outer_index"]),
                    "body_instance_arrays": [{"tag": t.get("name"), "count": t.get("count")}
                                             for t in bodies]})
    return out


def actor_links(skin):
    """The level actor / component that carries the mesh, and the mesh it names."""
    out = []
    for i in range(1, skin.pkg.export_count + 1):
        cls = skin.pkg.object_class(i)
        if cls not in ("RSkeletalMeshActor", "SkeletalMeshComponent"):
            continue
        s = U.export_summary(skin.pkg, i)
        refs = [{"export": t.get("value"), "object": t.get("ref"),
                 "class": t.get("ref_class"), "tag_offset": t.get("offset")}
                for t in s["tags"] if t.get("ref_class") == "SkeletalMesh"]
        out.append({"export": i, "class": cls, "name": skin.pkg.object_name(i),
                    "bytes": s["size"], "stop": s["stop"], "tags": s["tag_count"],
                    "mesh_refs": refs,
                    "outer": skin.pkg.object_path(skin.pkg.exports[i - 1]["outer_index"])})
    return out


# --------------------------------------------------------------------------- comparison

def props_oracle(slots):
    """Independent read: umodel's `Materials[19]` list vs the byte-decoded slot order."""
    if not os.path.exists(PROPS):
        return {"present": False,
                "verdict": "UNKNOWN",
                "reason": "the umodel props dump %s is not on disk" % PROPS}
    want = []
    with open(PROPS, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line.startswith("Materials[") and " = " in line and line.split("]")[0][10:].isdigit():
                rhs = line.split(" = ", 1)[1]
                if "'" in rhs:
                    want.append(rhs.split("'")[1].split(".")[-1])
    got = [s["material"] for s in slots]
    return {"present": True, "source": PROPS,
            "umodel": want, "decoded": got,
            "match": want == got,
            "verdict": "decoded" if want == got else "MISMATCH",
            "label": "derived: the byte-decoded slot order equals the umodel `Materials[]` list "
                     "(an independent read of the same mesh)"}


def byte_diff(a, b, chunk=8192):
    """Differing byte offsets of two equal-length payloads (chunked: 20 MB x2)."""
    if len(a) != len(b):
        return None
    diff = []
    for start in range(0, len(a), chunk):
        x = a[start:start + chunk]
        y = b[start:start + chunk]
        if x != y:
            for i in range(len(x)):
                if x[i] != y[i]:
                    diff.append(start + i)
    return diff


def _field_spans(skin):
    """(start, end, category) for every byte field this decoder can name in the payload.

    A differing offset is only called a "reference" or a "tag name index" because it lies in
    a field whose position and size are decoded - never because its bytes look like one.
    """
    spans = []
    for t in skin.tags:
        named_tag = "name" in t
        h0 = t["at"] - (20 if named_tag else 4)
        at = t["at"]
        if named_tag:
            spans.append((h0, at, "tag_header"))
            end = at + (t.get("size") or 0)
            if end > at:
                spans.append((at, end, "tag_payload:%s" % (t.get("name") or "?")))
            for k in range(len(t.get("refs") or [])):
                spans.append((at + 4 + 4 * k, at + 8 + 4 * k,
                              "ref:%s" % (t.get("name") or "?")))
        else:
            spans.append((h0, at, "tag_value"))
    spans.sort()
    return spans


def _category(spans, off):
    for s, e, cat in spans:
        if s <= off < e:
            return cat, s
        if s > off:
            break
    return "outside_decoded_spans", None


def _layout(skin):
    return [(t.get("name"), t.get("type"), t.get("offset"), t.get("size"), t.get("count"))
            for t in skin.tags]


def classify_diff(base, other, diff):
    """What the differing bytes are, by the decoded field they fall in."""
    if not diff:
        return {"bytes": 0}
    x, y = base.data, other.data
    spans = _field_spans(base)
    slots = decode_slots(base)
    if slots.get("verdict") == "decoded":
        spans.append((slots["count_at"], slots["refs_at"], "slot_array:count"))
        for k in range(slots["count"]):
            spans.append((slots["refs_at"] + 4 * k, slots["refs_at"] + 4 * k + 4, "slot_ref"))
        spans.sort()
    cats, ref_fields, outside = {}, {}, []
    for off in diff:
        cat, start = _category(spans, off)
        cats[cat] = cats.get(cat, 0) + 1
        if (cat.startswith("ref:") or cat == "slot_ref") and start is not None:
            ref_fields[start] = cat
        elif cat == "outside_decoded_spans":
            outside.append(off)
    same, different, examples = 0, 0, []
    for start, cat in sorted(ref_fields.items()):
        if start + 4 > len(x) or start + 4 > len(y):
            continue
        a = i32(x, start)
        b = i32(y, start)
        na = base.pkg.object_name(a) if 0 < a <= base.pkg.export_count else None
        nb = other.pkg.object_name(b) if 0 < b <= other.pkg.export_count else None
        if na and na == nb:
            same += 1
        else:
            different += 1
            if len(examples) < 6:
                examples.append({"at": start, "field": cat, "playable": a,
                                 "playable_name": na, "other": b, "other_name": nb})
    runs = []
    for i in diff:
        if runs and i - runs[-1][1] <= 8:
            runs[-1][1] = i
        else:
            runs.append([i, i])
    clusters = []
    for o in outside:
        if clusters and o - clusters[-1][1] <= 8:
            clusters[-1][1] = o
        else:
            clusters.append([o, o])
    outside_clusters, index_like = [], 0
    for s, e in clusters:
        hit = None
        for back in range(0, 4):                     # the value's low byte may start anywhere
            w = s - back
            if w < 0 or w + 4 > len(x) or w + 4 > len(y):
                continue
            va, vb = i32(x, w), i32(y, w)
            na = base.pkg.object_name(va) if 0 < va <= base.pkg.export_count else None
            nb = other.pkg.object_name(vb) if 0 < vb <= other.pkg.export_count else None
            if na and na == nb:
                hit = {"at": s, "to": e, "word_at": w, "playable": va,
                       "playable_name": na, "other": vb, "other_name": nb}
                break
        if hit:
            index_like += 1
        if len(outside_clusters) < 8:
            outside_clusters.append(hit or {"at": s, "to": e, "word_at": None})
    return {"outside_index_like": index_like, "outside_cluster_count": len(clusters),
            "bytes": len(diff),
            "categories": dict(sorted(cats.items())),
            "ref_fields": len(ref_fields),
            "ref_fields_same_name": same,
            "ref_fields_different": different,
            "ref_examples": examples,
            "outside_bytes": len(outside),
            "outside_clusters": outside_clusters,
            "ranges": [[s, e, e - s + 1] for s, e in runs],
            "range_count": len(runs),
            "tag_stream_end": base.tags_end,
            "bytes_before_tag_stream_end": sum(1 for i in diff if i < base.tags_end),
            "bytes_after_tag_stream_end": sum(1 for i in diff if i >= base.tags_end),
            "tag_layout_identical": _layout(base) == _layout(other)}


def diff_sockets(base, other):
    a, b = base["by_name"], other["by_name"]
    common = sorted(set(a) & set(b))
    return {
        "counts": [len(a), len(b)],
        "same_name_set": set(a) == set(b),
        "only_in_baseline": sorted(set(a) - set(b)),
        "only_in_other": sorted(set(b) - set(a)),
        "bone_differences": [{"socket": k, "baseline": a[k]["bone"], "other": b[k]["bone"]}
                             for k in common if a[k]["bone"] != b[k]["bone"]],
        "location_differences": [k for k in common
                                 if a[k]["location_uu"] and b[k]["location_uu"]
                                 and any(abs(x - y) > 1e-3 for x, y in
                                         zip(a[k]["location_uu"], b[k]["location_uu"]))],
        "rotation_differences": [k for k in common
                                 if a[k]["rotation_uu"] and b[k]["rotation_uu"]
                                 and list(a[k]["rotation_uu"]) != list(b[k]["rotation_uu"])],
    }


def diff_slots(base, other):
    a = [(s["material"], s["class"]) for s in base["slots"]]
    b = [(s["material"], s["class"]) for s in other["slots"]]
    rows = [{"slot": k, "baseline": a[k] if k < len(a) else None,
             "other": b[k] if k < len(b) else None,
             "same": (k < len(a) and k < len(b) and a[k] == b[k])}
            for k in range(max(len(a), len(b)))]
    return {"counts": [len(a), len(b)], "identical": a == b, "rows": rows,
            "differing_slots": [r["slot"] for r in rows if not r["same"]]}


def diff_materials(base_chains, other_chains):
    """Same-named material reached by both slot chains: parameter-by-parameter comparison."""
    out = []
    ba, ob = {}, {}
    for mc in base_chains:
        for st in mc["chain"]:
            ba.setdefault(st["name"], st)
    for mc in other_chains:
        for st in mc["chain"]:
            ob.setdefault(st["name"], st)
    for name in sorted(set(ba) & set(ob)):
        pa, pb = ba[name]["params"], ob[name]["params"]
        rows = []
        for kind in ("scalars", "vectors", "textures"):
            for key in sorted(set(pa[kind]) | set(pb[kind])):
                va = pa[kind].get(key, {}).get("value")
                vb = pb[kind].get(key, {}).get("value")
                if isinstance(va, dict):
                    va = va.get("object")
                if isinstance(vb, dict):
                    vb = vb.get("object")
                if va != vb:
                    rows.append({"kind": kind, "parameter": key,
                                 "baseline": va, "other": vb})
        out.append({"material": name, "differences": rows,
                    "same_sha1": ba[name]["sha1"] == ob[name]["sha1"]})
    return out


# --------------------------------------------------------------------------- build

def build():
    skins = {}
    for spec in PACKAGES:
        s = Skin(spec)
        sock = decode_sockets(s)
        slots = decode_slots(s)
        lods = decode_lods(s)
        chains = []
        for slot in slots["slots"]:
            if not slot["material"]:
                continue
            chains.append({"slot": slot["slot"], "start": slot["material"],
                           "start_class": slot["class"],
                           "start_export": slot["export"],
                           "chain": chain_of(s, slot["export"])})
        skins[s.key] = {
            "key": s.key, "role": s.role, "package": s.name, "package_bytes": s.bytes,
            "package_exports": s.pkg.export_count,
            "mesh": {"name": s.mesh_name, "class": "SkeletalMesh", "export": s.mesh,
                     "bytes": len(s.data), "sha1": sha1(s.data),
                     "tag_count": len(s.tags), "tags_end": s.tags_end,
                     "tags_stop": s.tags_stop,
                     "outer": s.pkg.object_path(s.pkg.exports[s.mesh - 1]["outer_index"])},
            "mesh_tags": [{"name": t.get("name"), "type": t.get("type"),
                           "offset": t.get("offset"), "size": t.get("size"),
                           "count": t.get("count")}
                          for t in s.tags],
            "sockets": sock,
            "slots": slots,
            "lods": lods,
            "material_chains": chains,
            "physics_assets": physics_assets(s),
            "physics_instances": physics_instance(s),
            "actors": actor_links(s),
        }
        skins[s.key]["sockets"]["by_name"] = {
            x["socket"]: x for x in sock["sockets"] if x["socket"]}
        skins[s.key]["slot_oracle"] = (props_oracle(slots["slots"])
                                       if s.key == BASELINE else None)

    base = skins[BASELINE]
    for key, sk in skins.items():
        if key == BASELINE:
            continue
        diff = byte_diff(base_data(base), base_data(sk))
        sk["vs_baseline"] = {
            "mesh": {
                "bytes_equal": base["mesh"]["bytes"] == sk["mesh"]["bytes"],
                "sha1_equal": base["mesh"]["sha1"] == sk["mesh"]["sha1"],
                "bytes": diff and len(diff),
                "diff": (classify_diff(_PACKAGE_CACHE[BASELINE], _PACKAGE_CACHE[key], diff)
                         if diff is not None else None),
            },
            "sockets": diff_sockets(base["sockets"], sk["sockets"]),
            "slots": diff_slots(base["slots"], sk["slots"]),
            "materials": diff_materials(base["material_chains"], sk["material_chains"]),
            "physics": {
                "baseline_assets": [{"name": p["name"], "export": p["export"],
                                     "body_count": p["body_count"]}
                                    for p in base["physics_assets"]],
                "other_assets": [{"name": p["name"], "export": p["export"],
                                  "body_count": p["body_count"]}
                                 for p in sk["physics_assets"]],
            },
        }

    unknowns = collect_unknowns(skins)
    return {
        "schema": 1,
        "card": "G3-05b",
        "generated_by": "Tools/scripts/grab_skins.py --write",
        "game_dir": GAME,
        "packages": [{"key": s.key, "package": s.name, "path": s.path,
                      "bytes": s.bytes, "exports": s.pkg.export_count} for s in _ALL],
        "skins": skins,
        "unknowns": unknowns,
    }


_PACKAGE_CACHE = {}
_ALL = []


def base_data(sk):
    return _PACKAGE_CACHE[sk["key"]].data


# --------------------------------------------------------------------------- md

def _shape_counts(sockets):
    counts = {}
    for row in sockets:
        counts[row["shape"]] = counts.get(row["shape"], 0) + 1
    return counts


def _fmt_vec(v, nd=4):
    if v is None:
        return "—"
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(str(x) if isinstance(x, int)
                               else ("%." + str(nd) + "g") % float(x) for x in v) + "]"
    if isinstance(v, float):
        return ("%." + str(nd) + "g") % v
    return str(v)


def render_md(doc):
    S = doc["skins"]
    keys = [s["key"] for s in PACKAGES]
    L = []
    A = L.append
    A("# Batmobile skins - MK2, Jokerfied, Standard and the Playable baseline (G3-05b)")
    A("")
    A("Generated by `Tools/scripts/grab_skins.py --write`; `--check` re-derives it from the")
    A("packages and fails on any drift, so nothing here is hand-maintained.")
    A("")
    A("Every value carries a label: **decoded** (export index + byte offset inside the export),")
    A("**derived** (rule and inputs stated) or **UNKNOWN** (what was tried, where it would be).")
    A("Nothing is filled in from Arkham Knight, UE3 or JC3 knowledge; where the bytes do not")
    A("say, the answer is UNKNOWN.")
    A("")
    A("## 1. Sources")
    A("")
    A("| key | role | package | bytes | exports | mesh | mesh export |")
    A("|---|---|---|---:|---:|---|---:|")
    for k in keys:
        s = S[k]
        A("| `%s` | %s | `%s` | %s | %s | `%s` | %d |" % (
            k, s["role"], s["package"], f"{s['package_bytes']:,}",
            f"{s['package_exports']:,}", s["mesh"]["name"], s["mesh"]["export"]))
    A("")
    A("## 2. The meshes")
    A("")
    A("| key | mesh | export bytes | sha1 | Sockets | slots (non-empty) | LODs | PhysicsAsset |")
    A("|---|---|---:|---|---:|---:|---:|---|")
    for k in keys:
        s = S[k]
        pa = ", ".join("`%s`" % p["name"] for p in s["physics_assets"]) or "none in package"
        A("| `%s` | `%s` | %s | `%s` | %s | %s | %s | %s |" % (
            k, s["mesh"]["name"], f"{s['mesh']['bytes']:,}", s["mesh"]["sha1"][:16],
            s["sockets"]["array_count"], "%d (%d)" % (s["slots"].get("count") or 0,
                                                      s["slots"].get("nonnull") or 0),
            s["lods"].get("count"), pa))
    A("")
    A("Mesh payload tag streams (decoded; the mesh's own property tags):")
    A("")
    A("| key | tags | stream ends at | stop | tags |")
    A("|---|---:|---:|---|---|")
    for k in keys:
        s = S[k]
        names = ", ".join("`%s`×%s" % (t["name"], t["count"]) if t.get("count") is not None
                          else "`%s`" % (t["name"] or "(offset-only)")
                          for t in s["mesh_tags"] if t.get("name"))
        A("| `%s` | %d | %s | %s | %s |" % (k, s["mesh"]["tag_count"],
                                            s["mesh"]["tags_end"], s["mesh"]["tags_stop"], names))
    A("")
    A("The material-slot array is **not** a property tag: it sits in the mesh's untagged data")
    A("(§3). The LOD blocks are decoded in §6.")
    A("")
    A("## 3. Material slots")
    A("")
    A("Decoded as `int32 count` then `count` × `int32` object references. The oracle is")
    A("containment: every non-zero reference resolves to a `MaterialInstanceConstant` or")
    A("`Material` export of the same package, and no other run of 8+ such references exists in")
    A("the first 32 KiB of the payload, so the location is unique. A slot therefore has no")
    A("stored name - its identity is the material object it points at.")
    A("")
    for k in keys:
        s = S[k]
        sl = s["slots"]
        A("### `%s` - %s: %s slots (count at payload byte %s, references from byte %s)" % (
            k, s["package"], sl.get("count"), sl.get("count_at"), sl.get("refs_at")))
        A("")
        if sl.get("verdict") != "decoded":
            A("- **UNKNOWN**: %s" % sl.get("reason"))
            A("")
            continue
        A("| slot | material | class | export |")
        A("|---:|---|---|---:|")
        for row in sl["slots"]:
            A("| %d | %s | %s | %s |" % (row["slot"],
                                         "`%s`" % row["material"] if row["material"] else "*(empty)*",
                                         row["class"] or "—", row["export"] or "—"))
        A("")
        o = s.get("slot_oracle")
        if o:
            A("- **Independent oracle**: %s" % (
                "the decoded order equals the umodel props dump's `Materials[%d]` list, name for "
                "name (`%s`) - **%s**" % (len(o["umodel"]), o["source"], o["match"])
                if o.get("present") else
                "UNKNOWN - %s" % o.get("reason")))
            A("")
    A("## 4. MIC chains and their parameters")
    A("")
    A("For every non-empty slot the chain is followed through object references whose class is")
    A("`MaterialInstanceConstant` or `Material`, up to the master `Material` (max 8 hops).")
    A("Parameters come from `ScalarParameterValues` / `VectorParameterValues` /")
    A("`TextureParameterValues` arrays of each step; the master's slot → expression map is the")
    A("same decode `MATERIALS.md` uses.")
    A("")
    for k in keys:
        s = S[k]
        A("### `%s` - %s" % (k, s["package"]))
        A("")
        A("| slot | chain (class: object) | master |")
        A("|---:|---|---|")
        for mc in s["material_chains"]:
            steps = " → ".join("%s `%s`" % (st["class"], st["name"]) for st in mc["chain"])
            master = next((st["name"] for st in mc["chain"] if st["class"] == "Material"), "—")
            A("| %d | %s | `%s` |" % (mc["slot"], steps, master))
        A("")
        for mc in s["material_chains"]:
            A("#### slot %d - `%s`" % (mc["slot"], mc["start"]))
            A("")
            for st in mc["chain"]:
                p = st["params"]
                A("- `%s` (%s, export %d, %s bytes, %d tags, sha1 `%s`)" % (
                    st["name"], st["class"], st["export"], f"{st['bytes']:,}", st["tags"],
                    st["sha1"][:12]))
                for kind, label in (("vectors", "vector"), ("scalars", "scalar"),
                                    ("textures", "texture")):
                    rows = p[kind]
                    if not rows:
                        continue
                    A("  - %s parameters (%d): %s" % (label, len(rows), ", ".join(
                        "`%s`=%s" % (n, (_fmt_vec(v["value"]) if not isinstance(v["value"], dict)
                                        else "`%s`(#%s)" % (v["value"].get("object"),
                                                            v["value"].get("export"))))
                        for n, v in sorted(rows.items()))))
                slots = st.get("material_slots") or {}
                if slots:
                    A("  - master slot → expression: %s" % ", ".join(
                        "%s→`%s`" % (name, (slots[name].get("expression") or "—"))
                        for name in SLOT_NAMES if name in slots))
                if st.get("parent") is None and st["class"] != "Material":
                    A("  - parent: **UNKNOWN** - no material-class object reference in this object")
            A("")
    A("## 5. Sockets")
    A("")
    A("Each socket export is `4*tag_count + 8*names + 12*location + 12*rotation + 2` bytes,")
    A("with the tags offset-only: socket name at class offset 0x54, bone at 0x5c, relative")
    A("location at 0x64, relative rotation at 0x70. The observed shapes are 4 tags / 58 bytes,")
    A("3 tags / 42 bytes (no stored rotation) and 2 tags / 26 bytes (name and bone only); the")
    A("byte accounting closes on every one of them and `--check` fails if any stops closing.")
    A("")
    for k in keys:
        s = S[k]
        A("### `%s` - %d sockets (array count %s)" % (k, len(s["sockets"]["sockets"]),
                                                     s["sockets"]["array_count"]))
        A("")
        A("accounting failures: %d" % len(s["sockets"]["accounting_failures"]))
        A("")
        A("shapes: %s" % ", ".join("%s tags ×%d" % (shape[:-1], n) for shape, n in sorted(
            _shape_counts(s["sockets"]["sockets"]).items())))
        A("")
        A("sockets with no stored relative rotation: %d; with no stored location: %d" % (
            sum(1 for r in s["sockets"]["sockets"] if not r["has_rotation"]),
            sum(1 for r in s["sockets"]["sockets"] if not r["has_location"])))
        A("")
        A("| socket | bone | relative location (UU) | relative rotation (UU) |")
        A("|---|---|---|---|")
        for row in s["sockets"]["sockets"]:
            A("| `%s` | `%s` | %s | %s |" % (row["socket"], row["bone"],
                                             _fmt_vec(row["location_uu"], 4),
                                             _fmt_vec(row["rotation_uu"], 0)))
        A("")
    A("## 6. LOD blocks")
    A("")
    for k in keys:
        s = S[k]
        lod = s["lods"]
        A("### `%s` - %s LODs, %s bytes of LODInfo" % (k, lod.get("count"),
                                                       lod.get("payload_bytes")))
        A("")
        if lod.get("verdict") != "decoded":
            A("- **%s**: %s (failures: %s)" % (lod.get("verdict"), lod.get("consumed"),
                                               lod.get("failures")))
            A("")
            continue
        A("| LOD | payload byte | element bytes | tags | display factor | hysteresis | LODMaterialMap | bEnableShadowCasting | TriangleSortSettings |")
        A("|---:|---:|---:|---:|---|---|---:|---:|---:|")
        for row in lod["lods"]:
            f = row["fields"]
            A("| %d | %d | %d | %d | %s | %s | %s | %s | %s |" % (
                row["lod"], row["at"], row["bytes"], row["tags"],
                _fmt_vec(f.get("display_factor")), _fmt_vec(f.get("lod_hysteresis")),
                f.get("LODMaterialMap"), f.get("bEnableShadowCasting"),
                f.get("TriangleSortSettings")))
        A("")
    A("## 7. PhysicsAsset and RB_BodySetups")
    A("")
    for k in keys:
        s = S[k]
        A("### `%s` - %s" % (k, s["package"]))
        A("")
        if not s["physics_assets"]:
            A("- **no `PhysicsAsset` export in this package.** Where the mesh's collision comes "
              "from is not in these bytes (§9).")
            A("")
            continue
        for pa in s["physics_assets"]:
            A("- `%s` (export %d, %s bytes, outer `%s`): BodySetup %s, BoundsBodies %s, Bounds %s" % (
                pa["name"], pa["export"], f"{pa['bytes']:,}", pa["outer"],
                pa["body_count"], pa["bounds_bodies_count"], pa["bounds_count"]))
            for ref in pa["object_refs"]:
                A("  - object reference %s -> `%s`" % (ref["value"], ref["ref"]))
            A("")
            A("| body export | bone | bytes | AggGeom bytes | header words | boxes |")
            A("|---:|---|---:|---:|---|---:|")
            for b in pa["bodies"]:
                hdr = (b.get("agg_header_u32") or {}).get("words")
                A("| %d | `%s` | %s | %s | %s | %s |" % (
                    b["export"], b["bone"], b["bytes"], b["agggeom_bytes"],
                    hdr if hdr else "—", len(b.get("boxes") or []) if b.get("agggeom_bytes") else "—"))
            A("")
            for b in pa["bodies"]:
                if not b.get("boxes"):
                    continue
                A("- body %d (`%s`) geometry, same decode as `COLLISION_GEOM.md`:" % (b["export"], b["bone"]))
                for i, bx in enumerate(b["boxes"]):
                    A("  - box %d: extents %s cm, centre %s cm, rotation not decoded" % (
                        i, _fmt_vec(bx["extents_cm"], 6), _fmt_vec(bx["centre_cm"], 4)))
                A("  - oracle: AggGeom word 1 = %s, boxes decoded = %d -> **%s**" % (
                    b.get("box_count_word"), len(b["boxes"]),
                    "match" if b.get("box_count_matches_word1") else "MISMATCH"))
                if b.get("convex_element_0"):
                    c = b["convex_element_0"]
                    A("  - convex element 0 also present: %d vertices / %d triangles" % (
                        c["vertices"], c["triangles"]))
                A("")
        if s["physics_instances"]:
            for pi in s["physics_instances"]:
                A("- `PhysicsAssetInstance` (export %d, %s bytes, outer `%s`): %s" % (
                    pi["export"], pi["bytes"], pi["outer"],
                    ", ".join("%s×%s" % (b["tag"], b["count"]) for b in pi["body_instance_arrays"])
                    or "no body-instance array"))
            A("")
    A("## 8. What carries the mesh in the level")
    A("")
    A("| key | object | class | bytes | mesh reference |")
    A("|---|---|---|---:|---|")
    for k in keys:
        for a in S[k]["actors"]:
            refs = ", ".join("`%s` (#%s)" % (r["object"], r["export"]) for r in a["mesh_refs"]) or "—"
            A("| `%s` | `%s` | %s | %d | %s |" % (k, a["name"], a["class"], a["bytes"], refs))
    A("")
    A("## 9. How each skin differs from `Playable_Batmobile_SF`'s `Batmobile_V2`")
    A("")
    for k in keys:
        if k == BASELINE:
            continue
        s = S[k]
        d = s["vs_baseline"]
        A("### `%s` vs baseline" % k)
        A("")
        md = d["mesh"]
        A("- mesh payload: %s bytes vs %s; sha1 %s. Differing bytes: %s." % (
            f"{s['mesh']['bytes']:,}", f"{S[BASELINE]['mesh']['bytes']:,}",
            "equal" if md["sha1_equal"] else "different",
            "none" if md["sha1_equal"] else (
                "**not comparable (different sizes)**" if not md["bytes_equal"] else md["bytes"])))
        if md.get("diff"):
            dd = md["diff"]
            A("  - decoded tag layouts identical: %s; differing bytes by the decoded field they "
              "fall in: %s" % (dd["tag_layout_identical"], ", ".join(
                  "%s %d" % (c, n) for c, n in dd["categories"].items())))
            if dd["ref_fields"]:
                A("  - object-reference fields touched: %d; their two readings resolve to the "
                  "**same object name**: %d; different: %d" % (
                      dd["ref_fields"], dd["ref_fields_same_name"], dd["ref_fields_different"]))
            for e in dd["ref_examples"]:
                A("    - %s at %s: %s/`%s` vs %s/`%s`" % (e["field"], hex(e["at"]), e["playable"],
                                                          e["playable_name"], e["other"],
                                                          e["other_name"]))
            A("  - ranges: %d; before the tag stream ends (%d): %d bytes; after: %d bytes" % (
                dd["range_count"], dd["tag_stream_end"], dd["bytes_before_tag_stream_end"],
                dd["bytes_after_tag_stream_end"]))
            if dd["outside_clusters"]:
                A("  - %d bytes fall outside every decoded field, in %d clusters; %d of those "
                  "clusters have a 4-byte reading whose two values resolve to the **same object "
                  "name** (i.e. object indices), the rest are UNKNOWN: %s" % (
                      dd["outside_bytes"], dd["outside_cluster_count"], dd["outside_index_like"],
                      "; ".join("%s: %s/`%s` vs %s/`%s`" % (
                          hex(c["at"]), c["playable"], c["playable_name"], c["other"],
                          c["other_name"]) if c.get("word_at") is not None
                          else "%s: no matching reading" % hex(c["at"])
                          for c in dd["outside_clusters"])))
        sd = d["sockets"]
        A("- sockets: %d vs %d; same name set **%s**; only in baseline %s; only here %s" % (
            sd["counts"][1], sd["counts"][0], sd["same_name_set"],
            sd["only_in_baseline"] or "—", sd["only_in_other"] or "—"))
        if sd["bone_differences"]:
            A("  - bone differences: %s" % "; ".join(
                "`%s`: %s → %s" % (b["socket"], b["baseline"], b["other"])
                for b in sd["bone_differences"]))
        if sd["location_differences"]:
            A("  - relative-location differences (>1e-3 UU): %s" % ", ".join(
                "`%s`" % x for x in sd["location_differences"]))
        if sd["rotation_differences"]:
            A("  - relative-rotation differences: %s" % ", ".join(
                "`%s`" % x for x in sd["rotation_differences"]))
        sl = d["slots"]
        A("- material slots: %d vs %d; identical list **%s**" % (
            sl["counts"][1], sl["counts"][0], sl["identical"]))
        if sl["differing_slots"]:
            A("  - differing slots: %s" % ", ".join(str(x) for x in sl["differing_slots"]))
            A("")
            A("| slot | baseline | this skin |")
            A("|---:|---|---|")
            for row in sl["rows"]:
                if row["same"]:
                    continue
                A("| %d | %s | %s |" % (
                    row["slot"],
                    ("`%s`" % row["baseline"][0])
                    if row["baseline"] and row["baseline"][0] else "—",
                    ("`%s`" % row["other"][0])
                    if row["other"] and row["other"][0] else "*(empty)*"))
        A("")
        ident = [m for m in d["materials"] if not m["differences"]]
        diffs = [m for m in d["materials"] if m["differences"]]
        A("- materials reached by both chains: %d; identical parameters %d; differing %d" % (
            len(d["materials"]), len(ident), len(diffs)))
        for m in diffs:
            A("  - `%s`: %s" % (m["material"], "; ".join(
                "%s `%s`: %s → %s" % (x["kind"], x["parameter"], _fmt_vec(x["baseline"]),
                                      _fmt_vec(x["other"])) for x in m["differences"])))
        A("- collision: baseline PhysicsAsset(s) %s; this package %s" % (
            ", ".join("`%s` (%s bodies, export %s)" % (p["name"], p["body_count"], p["export"])
                      for p in d["physics"]["baseline_assets"]) or "none",
            ", ".join("`%s` (%s bodies, export %s)" % (p["name"], p["body_count"], p["export"])
                      for p in d["physics"]["other_assets"]) or "none"))
        A("")
    A("## 10. UNKNOWNs")
    A("")
    for i, u in enumerate(doc["unknowns"], 1):
        A("%d. **%s** - %s" % (i, u["what"], u["why"]))
    A("")
    A("## 11. Oracles and checks")
    A("")
    A("`--check` re-derives every table above from the packages and fails if this file or the")
    A("JSON changes. It also asserts:")
    A("")
    A("- every socket's tag stream closes on its 2-byte terminator (58 / 42 / 26 bytes);")
    A("- the material-slot candidate is unique in each mesh;")
    A("- the baseline mesh's decoded slot order equals the umodel `Materials[]` props list;")
    A("- each LODInfo element's tag streams consume the LODInfo payload exactly;")
    A("- `AggGeom` word 1 equals the number of decoded box records on every body that has boxes;")
    A("- the four packages opened are the four the card names.")
    A("")
    return "\n".join(L)


# --------------------------------------------------------------------------- unknowns

def collect_unknowns(skins):
    U_ = []
    for k in (s["key"] for s in PACKAGES):
        s = skins[k]
        if not s["physics_assets"]:
            U_.append({"what": "`%s`: the mesh's collision asset" % s["package"],
                       "why": "the package carries no `PhysicsAsset` export at all (export census "
                              "by class, this tool); which asset the skin uses in game is not in "
                              "these bytes - it would be a reference from the archetype or the "
                              "level actor, which G3-01 covers for the drivable car only"})
    U_.append({"what": "slot names (the `FName` next to each slot's material)",
               "why": "the cooked slot element is a single 4-byte object reference - there is no "
                      "name field in the mesh payload, so a slot is identified by its material "
                      "object; `MATERIALS.md`'s slot numbering is the same object order, not a "
                      "second field"})
    U_.append({"what": "the mesh geometry behind the 20 MB of bulk data (vertex counts, bones, "
                       "bounds per LOD)",
               "why": "this card decodes the mesh's property tags, slots, sockets and collision; "
                      "the bulk vertex/index blocks are not decoded here - they are named by "
                      "`MESHES.md` from an umodel export, which is a different read"})
    std = skins["standard"]["vs_baseline"]["mesh"]["diff"]
    U_.append({"what": "the %d bytes that differ after the tag stream between Standard's and "
                       "Playable's `Batmobile_V2`" % std["outside_bytes"],
               "why": "the two meshes differ in %d bytes in total; the decoded tag layouts are "
                      "identical, all %d decoded object-reference fields resolve to the same "
                      "names, and %d of the %d clusters left over have a 4-byte reading whose two "
                      "values resolve to the same object name. The rest are in the payload's bulk "
                      "data, where no field is decoded: telling them apart would need the "
                      "vertex/index/section layout, which this card does not decode (`MESHES.md`'s "
                      "geometry comes from an umodel export, a different read)" % (
                          std["bytes"], std["ref_fields"], std["outside_index_like"],
                          std["outside_cluster_count"])})
    U_.append({"what": "which skin the drivable car selects, and when",
               "why": "the packages hold four meshes; the code that swaps `Batmobile_V2` for "
                      "`Batmobile_MK2_Skin` / `Batmobile_Jokerfied_Skin` is not in them - it would "
                      "be a class default or a Kismet action (G3-02/G3-06)"})
    U_.append({"what": "the material-parameter effect on screen (whether any decoded difference "
                       "is visible)",
               "why": "the parameters are decoded, the shader that consumes them is not; see "
                      "`COLOUR.md` for what is missing between a parameter and a pixel"})
    return U_


# --------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()

    global _ALL
    _ALL = [Skin(spec) for spec in PACKAGES]
    for s in _ALL:
        _PACKAGE_CACHE[s.key] = s

    doc = build()
    md = render_md(doc)
    js = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"

    if a.write:
        with open(MD_PATH, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        with open(JSON_PATH, "w", encoding="utf-8", newline="\n") as f:
            f.write(js)
        print("wrote SKINS.md and SKINS.json")
        for spec in PACKAGES:
            s = doc["skins"][spec["key"]]
            print("  %-10s %-32s mesh %-24s slots %-3s sockets %-3s lods %-2s physics %s" % (
                spec["key"], s["package"], s["mesh"]["name"], s["slots"].get("count"),
                len(s["sockets"]["sockets"]), s["lods"].get("count"),
                ",".join(p["name"] for p in s["physics_assets"]) or "-"))
        print("  unknowns:", len(doc["unknowns"]))
        return 0

    fails = []
    if not (os.path.exists(MD_PATH) and os.path.exists(JSON_PATH)):
        print("FAIL: outputs missing - run --write first")
        return 1
    stored = json.load(open(JSON_PATH, encoding="utf-8"))
    have_md = open(MD_PATH, encoding="utf-8").read()
    if stored != json.loads(js):
        fails.append("SKINS.json is stale (inputs changed since --write)")
    if have_md != md:
        fails.append("SKINS.md is stale (inputs changed since --write)")

    S = stored["skins"]
    for spec in PACKAGES:
        k = spec["key"]
        if k not in S:
            fails.append("skin %s missing" % k)
            continue
        s = S[k]
        if s["mesh"]["name"] != spec["mesh"]:
            fails.append("%s mesh %r != %r" % (k, s["mesh"]["name"], spec["mesh"]))
        if s["sockets"]["accounting_failures"]:
            fails.append("%s: %d socket(s) do not close on 58 bytes" % (
                k, len(s["sockets"]["accounting_failures"])))
        if s["slots"].get("verdict") != "decoded":
            fails.append("%s: slot array not decoded (%s)" % (k, s["slots"].get("verdict")))
        if s["lods"].get("verdict") != "decoded":
            fails.append("%s: LODInfo not decoded (%s)" % (k, s["lods"].get("verdict")))
        for pa in s["physics_assets"]:
            for b in pa["bodies"]:
                if b.get("boxes") and not b.get("box_count_matches_word1"):
                    fails.append("%s body %d: AggGeom word 1 %s != %d boxes" % (
                        k, b["export"], b.get("box_count_word"), len(b["boxes"])))
    o = (S[BASELINE].get("slot_oracle") or {})
    if not o.get("present"):
        fails.append("baseline slot oracle unavailable (%s)" % o.get("reason"))
    elif not o.get("match"):
        fails.append("baseline slot order does not match the umodel Materials[] list")

    # assertions the card leans on: the four named meshes, and Jokerfied's 10 bodies
    if not any(p["body_count"] == 10 for p in S["jokerfied"]["physics_assets"]):
        fails.append("Jokerfied PhysicsAsset does not report 10 bodies")
    if not any(p["body_count"] == 32 for p in S["playable"]["physics_assets"]):
        fails.append("baseline PhysicsAsset does not report 32 bodies")

    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("OK 4 packages, %d sockets, %d slots, %d material chains, %d unknowns; md+json "
          "byte-identical to a fresh rebuild" % (
              sum(len(S[k]["sockets"]["sockets"]) for k in S),
              sum(S[k]["slots"].get("count") or 0 for k in S),
              sum(len(S[k]["material_chains"]) for k in S),
              len(stored["unknowns"])))
    for k in S:
        o2 = S[k].get("slot_oracle")
        if o2 and o2.get("present"):
            print("  oracle %s: umodel Materials[%d] == decoded order -> %s" % (
                k, len(o2["umodel"]), o2["match"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
