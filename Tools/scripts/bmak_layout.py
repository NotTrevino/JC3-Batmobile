"""bmak_layout.py - bind the Batmobile classes' cooked offsets to their property names (G1-1).

The cooked vehicle packages write simple property tags as `type + class offset + value` and drop
the name.  The names are not in the archetype, but they *are* in `BmGame.upk`, which ships the
script classes these archetypes were built from: every class export owns one child export per
`UProperty`, named and typed (FloatProperty, BoolProperty, ObjectProperty, ...).

What `BmGame.upk` does not ship is the byte offset: UE3 assigns it when the class links, walking
the property chain in declaration order.  This tool reproduces that walk for the export chain in
`BmGame.upk` and binds every offset by laying the properties out in order, then proves the result
against the offsets the cooked data actually carries (`Research/BatmobileGrab/OFFSETS.json`) and
against each class's default object.

Usage:
    python Tools/scripts/bmak_layout.py --fit RBatmobileCannon
    python Tools/scripts/bmak_layout.py --report
"""
import argparse
import collections
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import upk_read as U  # noqa: E402

GAME = r"E:\Games\Batman - Arkham Knight"
PKG = os.path.join(GAME, "BmGame", "CookedPCConsole", "BmGame.upk")
OFFSETS = os.path.join(ROOT, "Research", "BatmobileGrab", "OFFSETS.json")
# Struct slots whose declaration is not in BmGame.upk but whose size the dump/usage pins.
DEFAULT_OVERRIDES = {"PostProcessSettings": 0x200, "AkSoundHandle": 8}

# Sizes of the primitive property types in a UE3 x64 object.  `align` is what `UProperty::Link`
# uses for the next property's offset.
#
# Every type aligns to 4 here, pointer members included.  That is this build's actual rule, not a
# default: the BmSDK-AK dump puts `SlipstreamingVehicle` (an ObjectProperty) at 0x34C, right after a
# float at 0x348, and `TransformationRotation` (a 12-byte struct) at 0x384 - neither is 8-aligned.
# With 8-byte alignment the sim's class extent comes out 4 bytes long and its later properties
# drift one slot off the dump.
PRIMITIVE = {
    "ByteProperty": (1, 1),
    "IntProperty": (4, 4),
    "BoolProperty": (4, 4),
    "FloatProperty": (4, 4),
    "ObjectProperty": (8, 4),
    "ObjectNCRProperty": (8, 4),
    "ClassProperty": (8, 4),
    "NameProperty": (8, 4),
    "StrProperty": (16, 4),
    "StringProperty": (16, 4),
    "ArrayProperty": (16, 4),
    "VectorProperty": (12, 4),
    "RotatorProperty": (12, 4),
    "GuidProperty": (16, 4),
    "StructProperty": (None, 4),
    "FixedArrayProperty": (None, 4),
    "MapProperty": (16, 4),
    # UComponentProperty / UInterfaceProperty are UObjectProperty subclasses: one pointer slot.
    # They must be here or the walk silently drops them and every following property lands 8
    # bytes low - which is what mislabelled `RInventoryGadget.Mesh` (0x318) as XrayMaskMaterial.
    "ComponentProperty": (8, 4),
    "InterfaceProperty": (8, 4),
    "DelegateProperty": (16, 4),
}

# Native structs that have no ScriptStruct export in BmGame.upk.
NATIVE_STRUCT = {
    "Vector": 12,
    "Vector2D": 8,
    "Rotator": 12,
    "Quat": 16,
    "Plane": 16,
    "Matrix": 64,
    "Color": 4,
    "LinearColor": 16,
    "Guid": 16,
    # FInterpCurve<T> is `TArray<FInterpCurvePoint<T>> Points; EInterpCurveMode InterpMethod;`.
    # On this 64-bit build a TArray is 16 bytes (8-byte Data, 4 ArrayNum, 4 ArrayMax) and the mode
    # enum is one byte, rounded to 4: the slot is 20 bytes whatever T is.  The BmSDK-AK dump puts
    # consecutive curve properties 20 bytes apart (0x1DC to 0x1F0), which settles it.  The point
    # data itself lives in the tag payload, not here.
    "InterpCurveFloat": 20,
    "InterpCurveVector": 20,
    "InterpCurveQuat": 20,
    "InterpCurveVector2D": 20,
    "InterpCurveTwoVectors": 20,
    "Box": 25,
    "BoxSphereBounds": 28,
    "RangeVector": 24,
    "IntPoint": 8,
    "Pointer": 8,
}

OFFSET_TYPES = {"FloatProperty", "IntProperty", "BoolProperty", "ByteProperty", "NameProperty",
                "StrProperty", "ObjectProperty", "ObjectNCRProperty", "StructProperty",
                "ArrayProperty", "VectorProperty", "RotatorProperty", "ClassProperty",
                "MapProperty", "GuidProperty"}

# The cooked tag stream and the class's UProperty subclass disagree on names for object slots:
# the class says ObjectProperty/ClassProperty, the tag says ObjectNCRProperty ("no create
# reference").  They occupy the same 8-byte pointer slot, so the fit must treat them as one.
TAG_KIND = {
    "ObjectNCRProperty": "ObjectProperty",
    "ObjectProperty": "ObjectProperty",
    "ClassProperty": "ObjectProperty",
    "ComponentProperty": "ObjectProperty",
    "InterfaceProperty": "ObjectProperty",
}


def same_kind(tag_type, prop_kind):
    return TAG_KIND.get(tag_type, tag_type) == TAG_KIND.get(prop_kind, prop_kind)


class Layout:
    def __init__(self, path=PKG, overrides=None, prop_sizes=None):
        self.overrides = dict(overrides or {})
        # per-property slot sizes: a struct slot is the size the *class default object* gives it,
        # and an InterpCurveFloat's size follows its point count (8 + 16*points), which differs
        # between the CDO and the archetypes that override the curve.  The class layout uses the
        # CDO's count, so the size has to be set per property, not per type.
        self.prop_sizes = dict(prop_sizes or {})
        self.pkg = U.Package(path)
        self.by_name = collections.defaultdict(list)
        for i, e in enumerate(self.pkg.exports, 1):
            self.by_name[e["name"]].append(i)
        self.children = collections.defaultdict(list)
        for i, e in enumerate(self.pkg.exports, 1):
            self.children[e["outer_index"]].append(i)
        self._struct_size = {}

    # -- object helpers ---------------------------------------------------

    def export(self, i):
        return self.pkg.exports[i - 1]

    def kind(self, i):
        return self.pkg.class_name(self.export(i)["class_index"])

    def is_class(self, i):
        return self.kind(i) is None

    def find_class(self, name):
        for i in self.by_name.get(name, []):
            if self.is_class(i) and self.export(i)["outer_index"] in (0, -1) or \
               (self.is_class(i) and self.export(i)["outer_index"] <= 0):
                return i
        return None

    def super_of(self, i):
        s = self.export(i)["super_index"]
        return s if s > 0 else None

    def chain(self, i):
        out = []
        while i:
            out.append(i)
            i = self.super_of(i)
        return list(reversed(out))

    def defaults(self, cls):
        name = "Default__" + self.export(cls)["name"]
        for i in self.by_name.get(name, []):
            return i
        return None

    # -- struct sizes -----------------------------------------------------

    def struct_target(self, i):
        e = self.export(i)
        raw = self.pkg.image[e["offset"]:e["offset"] + e["size"]]
        if len(raw) < 4:
            return None
        return struct.unpack_from("<i", raw, len(raw) - 4)[0]

    def struct_size(self, name):
        if name in self.overrides:
            return self.overrides[name]
        if name in NATIVE_STRUCT:
            return NATIVE_STRUCT[name]
        if name in self._struct_size:
            return self._struct_size[name]
        size = None
        for i in self.by_name.get(name, []):
            if self.kind(i) == "ScriptStruct":
                props = self.properties(i)
                off = 0
                bool_word = None
                bool_bit = 0
                for p in props:
                    if p["kind"] == "BoolProperty":
                        # UE3 packs consecutive bools into one 32-bit word, exactly as the class
                        # walk below does.  Without this a struct of three bools is 12 bytes
                        # instead of 4, and every member after it lands low.
                        for _ in range(p.get("dim", 1)):
                            if bool_word is None or bool_bit >= 32:
                                off = _align(off, 4)
                                bool_word = off
                                bool_bit = 0
                            bool_bit += 1
                            if bool_bit >= 32:
                                off = bool_word + 4
                                bool_word = None
                                bool_bit = 0
                        continue
                    if bool_word is not None:
                        off = bool_word + 4
                    bool_word = None
                    bool_bit = 0
                    off = _align(off, p["align"])
                    off += p["size"]
                if bool_word is not None:
                    off = bool_word + 4
                # the struct itself is 4-aligned in this build: `TArray Points` (16) plus the
                # one-byte InterpMethod is 17, and the engine rounds that to 20, which is the
                # spacing the class dump shows between consecutive curve properties
                size = _align(off, 4)
                break
        if size is None:
            raise KeyError("unknown struct %r" % name)
        self._struct_size[name] = size
        return size

    # -- properties -------------------------------------------------------

    def properties(self, cls):
        """UProperty children of `cls`, in declaration order, with their type.

        The script compiler prepends each new UField to UStruct::Children, so the export table's
        order is the reverse of the declaration order: `Children` points at the highest export
        index and every property's `Next` points one index lower.  Lay them out in chain order.
        """
        out = []
        for i in sorted(self.children.get(cls, []), reverse=True):
            k = self.kind(i)
            if k not in PRIMITIVE:
                continue
            e = self.export(i)
            size, align = PRIMITIVE[k]
            dim = self.array_dim(i)
            if k == "StructProperty":
                target = self.struct_target(i)
                tname = self.pkg.object_name(target)
                size = self.prop_sizes.get(e["name"], self.struct_size(tname))
                out.append({"index": i, "name": e["name"], "kind": k, "size": size * dim,
                            "align": align, "struct": tname, "dim": dim})
            elif k == "FixedArrayProperty":
                size = 4
                out.append({"index": i, "name": e["name"], "kind": k, "size": size,
                            "align": align, "struct": None, "dim": dim})
            else:
                out.append({"index": i, "name": e["name"], "kind": k, "size": size * dim,
                            "align": align, "struct": None, "dim": dim})
        return out

    def array_dim(self, i):
        """`UProperty::ArrayDim`: a static array is one property of N slots, not N properties.

        Cooked script arrays such as `GearRatios[6]` and `BoostCooldown[3]` are declared once with
        ArrayDim 6 / 3 and occupy 6 / 3 element slots in the class layout; without this the walk
        under-counts every array and every property after it lands too low.  The field sits at
        byte 6 of the property export's serialized `UProperty` header, which was checked against
        the BmSDK-AK class dump: the six `GearRatios` slots and three `BoostCooldown` slots it
        emits line up exactly with dim 6 and dim 3 here.
        """
        e = self.export(i)
        raw = self.pkg.image[e["offset"]:e["offset"] + e["size"]]
        if len(raw) < 10:
            return 1
        dim = struct.unpack_from("<i", raw, 6)[0]
        return dim if 0 < dim <= 1024 else 1

    def layout(self, cls):
        """Lay a class and its script ancestors out from offset 0.

        UE3 packs consecutive bool properties into one 32-bit bitfield word, so a run of bools
        shares an offset and the word advances only every 32 bits (or when a non-bool follows).
        That is why the sim class shows all fifteen of its bools at one offset.
        """
        rows = []
        off = 0
        bool_word = None
        bool_bit = 0
        for ci in self.chain(cls):
            for p in self.properties(ci):
                if p["kind"] == "BoolProperty":
                    for _ in range(p.get("dim", 1)):
                        if bool_word is None or bool_bit >= 32:
                            off = _align(off, 4)
                            bool_word = off
                            bool_bit = 0
                        rows.append(dict(p, owner=self.export(ci)["name"], offset=bool_word,
                                         bit=bool_bit, size=4, dim=1))
                        bool_bit += 1
                        if bool_bit >= 32:
                            off = bool_word + 4
                            bool_word = None
                            bool_bit = 0
                    continue
                if bool_word is not None:
                    # the bitfield word is finished: the next non-bool starts after it
                    off = bool_word + 4
                bool_word = None
                bool_bit = 0
                off = _align(off, p["align"])
                rows.append(dict(p, owner=self.export(ci)["name"], offset=off))
                off += p["size"]
        if bool_word is not None:
            off = bool_word + 4
        return rows, off

    def top_level_offsets(self, cls):
        """Absolute offsets from each class's default object, for fitting."""
        cdo = self.defaults(cls)
        if not cdo:
            return [], None
        e = self.export(cdo)
        raw = self.pkg.image[e["offset"]:e["offset"] + e["size"]]
        tags, _end, why = U.walk_tags(self.pkg, raw)
        return [t for t in tags if t.get("type") in OFFSET_TYPES and "offset" in t], why


def _align(v, a):
    return (v + a - 1) // a * a


def observed():
    doc = json.load(open(OFFSETS, encoding="utf-8"))
    out = collections.defaultdict(dict)
    for r in doc["fields"]:
        # The struct-aware split can list one class slot twice (Cannon 0x0004 is TimeDuration in
        # the shake struct and OutVal in a curve point), but a layout has one slot there, so the
        # fit must score it once.
        out[r["class"]].setdefault((r["offset"], r["type"]), r)
    return {cls: list(rows.values()) for cls, rows in out.items()}


def fit(lay, cls, obs, lo=0, hi=0x1000, step=4):
    rows, total = lay.layout(cls)
    tags, why = lay.top_level_offsets(cls)
    scored = []
    for base in range(lo, hi, step):
        hits = set()
        for t in tags:
            rel = t["offset"] - base
            for r in rows:
                if r["offset"] == rel and r["kind"] == t["type"]:
                    hits.add(("cdo", t["offset"]))
                    break
        for o in obs:
            rel = o["offset"] - base
            for r in rows:
                if r["offset"] == rel and r["kind"] == o["type"]:
                    hits.add(("obs", o["offset"], o["type"]))
                    break
        scored.append((len(hits), base))
    return rows, total, tags, why, sorted(scored, reverse=True)


def cmd_fit(a):
    lay = Layout(overrides=DEFAULT_OVERRIDES)
    cls = lay.find_class(a.cls)
    if not cls:
        print("class not found in BmGame.upk:", a.cls)
        return 1
    rows, total, tags, why, scored = fit(lay, cls, observed().get(a.cls, []))
    print("%s: export %d, %d properties, laid out %#x bytes, CDO %s (%d tags, %s)" % (
        a.cls, cls, len(rows), total, lay.defaults(cls), len(tags), why))
    for hits, base in scored[:6]:
        print("  base %#06x -> %d/%d matches" % (base, hits, len(tags) + len(observed().get(a.cls, []))))
    base = scored[0][1]
    print("\n  layout at base %#06x" % base)
    for r in rows:
        print("    %#06x %-40s %-18s %2d %s" % (base + r["offset"], r["name"], r["kind"],
                                                r["size"], r["owner"]))
    return 0


def cmd_report(a):
    lay = Layout(overrides=DEFAULT_OVERRIDES)
    classes = a.classes or ["RVehicleSimBatmobile"]
    for cls_name in classes:
        cls = lay.find_class(cls_name)
        if not cls:
            print("%-32s not in BmGame.upk" % cls_name)
            continue
        rows, total = lay.layout(cls)
        print("%-32s %3d props, %#6x bytes, CDO %s" % (cls_name, len(rows), total,
                                                       lay.defaults(cls)))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fit", dest="cls", metavar="CLASS")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--classes", nargs="*")
    a = ap.parse_args()
    if a.cls:
        return cmd_fit(a)
    return cmd_report(a)


if __name__ == "__main__":
    raise SystemExit(main())
