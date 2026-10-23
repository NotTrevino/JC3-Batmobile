r"""grab_offsets.py - resolve every stripped property name the Batmobile classes carry (G1-1).

The Batman2 cook writes simple property tags as `type + class offset + value`, with **no name**: the
engine resolves the name from the native class layout by offset. On the thirteen
`RVehicleBatmobile`/`RBatmobile*` classes that leaves 366 distinct fields (1,736 occurrences); over
all fifteen target classes it is 423 fields (2,593 occurrences). The counts differ from the earlier
422/365 because one key, `RBatmobileCannon 0x0004 FloatProperty`, was two members in two different
nested structs (`BMScreenShakeStruct.TimeDuration` and `FInterpCurvePointFloat.OutVal`) collapsed by
offset; the key now carries the innermost struct, so the two are counted separately.

This tool does not stop at "unnamed". It decides each field from evidence, one of four ways:

  * **named-sdk** - the class + absolute offset + slot kind resolve in the BmSDK-AK class dump,
    which is generated from the running game and therefore carries the linked layout the cooked
    tags were written against. See `bmsdk_offsets.py`.
  * **named / named-element** - the offset sits in a struct whose own declaration proves the
    layout (the `VehicleLights` struct, the shake structs, the `FInterpCurve` points).  The struct
    is the **innermost** one on the tag path, and a packed `BoolProperty` is named by its bit mask.
  * **named-segment** - the slot lands under the base an inline tag anchors, for the (now empty)
    set where the dump has no entry.
  * **undecidable** - a scalar/vector/name with no name, no referent and no slot the dump reaches.
    Recorded with values, contexts and offsets rather than guessed.

The exe route was measured and is empty: the classes are imported from `BmScript` (a package that
does not exist anywhere in the install), a UE3 class's outer *is* its package, and the executable
carries the classes' native *functions* (341 of them) but no class-qualified property table - see
`NATIVE.md`. Every value the game reads is preserved here by offset regardless.

Writes `Research/BatmobileGrab/OFFSETS.json` and `OFFSETS.md`.

Usage:
    python Tools/scripts/grab_offsets.py --write
    python Tools/scripts/grab_offsets.py --check
"""
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import bmsdk_offsets as S  # noqa: E402
import grab_model          # noqa: E402
import upk_read as U       # noqa: E402

OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
BOUND = os.path.join(ROOT, "Working", "Grab", "bound.json")
BMSDK = os.path.join(OUT, "BMSDK_OFFSETS.json")
COOKED = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
INSTALL = r"E:\Games\Batman - Arkham Knight"
# The two classes the backlog's 365 came from, plus the two that carry unnamed scalars on the same
# terms and were never in that count: the sim (`RVehicleSimBatmobile`) and the wheel component.
ARCHETYPE_PREFIXES = ("RVehicleBatmobile", "RBatmobile")
CLASS_PREFIXES = ARCHETYPE_PREFIXES + ("RVehicleSimBatmobile", "SVehicleWheel")

# VehicleLights layout, proven by the struct's own named tags (see grab_model.lights):
#   offset 0  component ref, 8 lens flare, 16 Type (VEHLT_*), 20 socket NameProperty,
#   28 MaterialType (VEHLTMAT_*), 36 optional second component
LIGHTS_LAYOUT = {
    (0, "ObjectNCRProperty"): "LightComponent",
    (8, "ObjectNCRProperty"): "LensFlareComponent",
    (16, "ByteProperty"): "Type",
    (20, "NameProperty"): "Socket",
    (28, "ByteProperty"): "MaterialType",
    (36, "ObjectNCRProperty"): "SecondComponent",
}


def is_target(cls):
    return bool(cls) and any(cls.startswith(p) for p in CLASS_PREFIXES)


def is_archetype(cls):
    return bool(cls) and any(cls.startswith(p) for p in ARCHETYPE_PREFIXES)


def bmscript_evidence():
    """Does any grabbed package import BmScript, and is the package or its file anywhere on disk?"""
    imports, files = set(), set()
    for base, _dirs, names in os.walk(INSTALL):
        for name in names:
            if "bmscript" in name.lower():
                files.add(os.path.join(base, name))
    for r in grab_model.Grab().summary.get("packages", []):
        try:
            p = U.Package(os.path.join(COOKED, r + ".upk"))
        except (OSError, U.UpkError):
            continue
        for imp in p.imports:
            if "bmscript" in (imp.get("name") or "").lower() or \
               "bmscript" in (imp.get("class_package") or "").lower():
                imports.add("%s -> %s.%s" % (r, imp.get("class_package"), imp.get("name")))
    return {"imports": sorted(imports), "files_on_disk": sorted(files),
            "on_disk": bool(files)}


def native_evidence():
    path = os.path.join(OUT, "NATIVE.json")
    if not os.path.isfile(path):
        return {"classes": 0, "functions": 0, "property_table_strings": None}
    doc = json.load(open(path, encoding="utf-8"))
    return {"classes": doc["summary"]["classes"], "functions": doc["summary"]["functions"],
            "property_table_strings": doc["summary"]["property_table_strings"],
            "target_classes": doc["summary"]["target_classes_found"]}


# Native point struct of an InterpCurve float curve: four floats, in this order (UE3
# FInterpCurvePointFloat).  Proven by the values: element 0 is the input (speed), element 4 the
# output (torque/factor), and elements 8/12 are zero on every authored point.
INTERP_POINT = {0: "InVal", 4: "OutVal", 8: "ArriveTangent", 12: "LeaveTangent"}


def struct_members(lay, name):
    """[(offset, member name, kind, struct, bit)] for a ScriptStruct declared in BmGame.upk.

    Consecutive BoolProperties share one 32-bit word, exactly as they do in a class.  `bit` is the
    bit inside that word for a bool, and None otherwise.  Without the packing a struct of three
    bools would be 12 bytes instead of 4, and every member after the run would land low.
    """
    for idx in lay.by_name.get(name, []):
        if lay.kind(idx) != "ScriptStruct":
            continue
        off, out = 0, []
        bool_word, bool_bit = None, 0
        for p in lay.properties(idx):
            if p["kind"] == "BoolProperty":
                for _ in range(p.get("dim", 1)):
                    if bool_word is None or bool_bit >= 32:
                        off = (off + 3) // 4 * 4
                        bool_word = off
                        bool_bit = 0
                    out.append((bool_word, p["name"], "BoolProperty", None, bool_bit))
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
            off = (off + p["align"] - 1) // p["align"] * p["align"]
            out.append((off, p["name"], p["kind"], p.get("struct"), None))
            off += p["size"]
        if bool_word is not None:
            off = bool_word + 4
        return out
    return None


def immediate_struct(lay, cls_rows, path):
    """Struct type that contains the final offset-only tag of a flattened path, or None.

    A nested struct flattens its members into the parent's tag stream, so the offset in a field key
    is relative to the **innermost** struct, not to the class property that anchors the path.  Walk
    the named segments (`ImpactShake.AdvancedOptions.<0x0000>`, `InaccuracyVsTime.Points[0].<0x0004>`)
    and return that struct's name.
    """
    if not cls_rows:
        return None
    segs = path.split(".")[:-1]          # drop the trailing <0xOFFSET>
    cur = None
    for i, seg in enumerate(segs):
        name = seg.split("[")[0]
        if i == 0:
            row = next((r for r in cls_rows if r["name"] == name), None)
            if not row or row["kind"] != "StructProperty":
                return None
            cur = row.get("struct")
        elif not cur:
            return None
        elif name == "Points" and cur.startswith("InterpCurve"):
            # a curve's Points array holds FInterpCurvePoint<T>, and the point - not the curve - is
            # the innermost struct.  Its tag offsets are point-relative.  Only the float lane is
            # modelled, because that is the only curve kind these classes carry.
            if cur != "InterpCurveFloat":
                return None
            cur = "FInterpCurvePointFloat"
            continue
        else:
            member = next((m for m in (struct_members(lay, cur) or []) if m[1] == name), None)
            if not member or member[2] != "StructProperty":
                return None
            cur = member[3]
    return cur


def element_names(lay, container, field):
    """Name a struct element from the innermost struct's own declaration, or None."""
    if not container:
        return None
    off = field["offset"]
    if container.startswith("FInterpCurvePoint"):
        return INTERP_POINT.get(off) if container == "FInterpCurvePointFloat" else None
    members = struct_members(lay, container)
    if not members:
        return None
    if field["type"] == "BoolProperty":
        # One tag carries the whole shared word.  Name it only if every set bit maps to a declared
        # bool at this offset; the bit mask is what distinguishes the members, not the offset.
        words = field.get("bits") or set()
        if len(words) != 1:
            return None
        word = next(iter(words))
        if not word:
            return None
        hits = [m for m in members if m[0] == off and m[2] == "BoolProperty"]
        names, covered = [], 0
        for m in hits:
            bit = 1 << m[4]
            if word & bit:
                names.append(m[1])
                covered |= bit
        if not names or covered != word:
            return None
        return " + ".join(names)
    want = {"ObjectNCRProperty": "ObjectProperty", "ClassProperty": "ObjectProperty"}.get(
        field["type"], field["type"])
    # a Vector/Rotator/Guid member is declared as a StructProperty of that native struct, but its
    # tag in the stream is VectorProperty/RotatorProperty/GuidProperty: same slot, two names
    native = {"VectorProperty": "Vector", "RotatorProperty": "Rotator",
              "GuidProperty": "Guid"}.get(field["type"])

    def ok(m):
        if m[0] != off:
            return False
        if native:
            return m[2] == "StructProperty" and m[3] == native
        return m[2] == want

    hits = [m for m in members if ok(m)]
    return hits[0][1] if len(hits) == 1 else None


def grab_layout():
    import bmak_layout
    lay = bmak_layout.Layout(overrides={"PostProcessSettings": 0x200, "AkSoundHandle": 8})
    rows_by_class = {}
    for cls in {f["class"] for f in json.load(open(os.path.join(OUT, "OFFSETS.json"),
                                                  encoding="utf-8"))["fields"]}:
        # the archetypes' own class may be the unshipped BmScript one; the parent the build ships
        # declares the same struct-typed fields, so its rows name the elements just as well
        host = cls if lay.find_class(cls) else ("RVehicleBatmobileBase"
                                                if cls == "RVehicleBatmobile" else None)
        i = lay.find_class(host) if host else None
        if i:
            lay.prop_sizes = {}
            rows_by_class[cls] = lay.layout(i)[0]
    return lay, rows_by_class


def bound_names():
    """{class: {offset: name}} from the inline property names bmak_bind.py proved."""
    if not os.path.isfile(BOUND):
        return {}
    doc = json.load(open(BOUND, encoding="utf-8"))
    out = {}
    for cls, d in doc.items():
        how = d.get("how", {})
        out[cls] = {int(k, 16): (v, how.get(k, "segment")) for k, v in d.get("bound", {}).items()}
    return out


def struct_context(cls_rows, field):
    """Is the field an offset inside a struct property?  Then its key is struct-relative."""
    structs = {r["name"] for r in cls_rows if r["kind"] == "StructProperty"}
    return any(c in structs for c in field["contexts"])


def sdk_doc():
    if not os.path.isfile(BMSDK):
        return {"classes": {}}
    return json.load(open(BMSDK, encoding="utf-8"))


def bind_sdk(doc, cls, offset, kind):
    """(name, owner) from the BmSDK-AK dump for an absolute object offset, or None."""
    p = S.lookup(doc, cls, offset, kind)
    if not p:
        return None
    return p["name"], p.get("owner", cls)


def build():
    g = grab_model.Grab()
    known = bound_names()
    sdk = sdk_doc()
    lay, rows_by_class = grab_layout()
    rows = [r for r in g.rows if is_target(r.get("class"))]
    # named tags per (class, offset) - the only way an unnamed field could be named from data in scope
    named = collections.defaultdict(collections.Counter)
    for r in g.rows:
        for p, t in g.tags(r):
            if t.get("name") and "offset" in t:
                named[(r.get("class"), t["offset"])][t["name"]] += 1
    fields = collections.OrderedDict()
    for r in rows:
        cls_rows = rows_by_class.get(r["class"])
        for path, t in g.tags(r):
            if t.get("name") or "offset" not in t or "value" not in t:
                continue
            # The key carries the innermost struct as well as the offset: two nested structs can
            # use the same offset for different members (a shake's TimeDuration and a curve point's
            # OutVal are both class offset 0x0004), and collapsing them would re-introduce the
            # ambiguity the struct declaration just removed.
            container = immediate_struct(lay, cls_rows, path)
            key = (r["class"], t["offset"], t["type"], container)
            f = fields.setdefault(key, {"class": r["class"], "offset": t["offset"],
                                        "type": t["type"], "struct": container,
                                        "count": 0, "values": [],
                                        "contexts": set(), "referents": collections.Counter(),
                                        "sample_ref": None, "bits": set()})
            f["count"] += 1
            f["contexts"].add((path or "").split("[")[0].split(".")[0])
            if len(f["values"]) < 3:
                f["values"].append(t["value"])
            if "bits" in t:
                f["bits"].add(t["bits"])
            if t.get("ref_class"):
                f["referents"][t["ref_class"]] += 1
                f["sample_ref"] = f["sample_ref"] or t.get("ref")
    out_fields, decisions = [], collections.Counter()
    for key, f in fields.items():
        name, why, decision = None, None, "undecidable"
        elem = element_names(lay, f["struct"], f)
        if elem:
            name, decision = elem, "named-element"
            why = "member of %s, read from its own declaration" % f["struct"]
            if f["bits"]:
                bits = sorted(f["bits"])
                why += ("; the BoolProperty tag carries the shared bitfield word %s"
                        % " + ".join("0x%X" % b for b in bits))
        inline = known.get(f["class"], {}).get(f["offset"])
        if not elem and inline and inline[1] == "anchor":
            name = inline[0]
            decision = "named-class"
            why = "inline property name in the cooked tag stream (BmGame.upk class)"
        sdk_hit = None
        cls_rows = rows_by_class.get(f["class"])
        if not elem and decision != "named-class" and not (cls_rows is not None
                                                          and struct_context(cls_rows, f)):
            sdk_hit = bind_sdk(sdk, f["class"], f["offset"], f["type"])
        if sdk_hit:
            name, owner = sdk_hit
            decision = "named-sdk"
            why = ("BmSDK-AK class dump: %s.%s at this offset and slot kind (offsets generated from "
                   "the running game; build match measured in REGISTRATION.md)" % (owner, name))
        elif not elem and decision != "named-class" and inline:
            name = inline[0]
            decision = "named-segment"
            why = ("class slot at this offset under the base the preceding inline tag anchors"
                   " (local to that run: see REGISTRATION.md)")
        if decision == "undecidable" and any("VehicleLights" in p for p in f["contexts"]):
            name = LIGHTS_LAYOUT.get((f["offset"], f["type"]))
            if name:
                decision = "named"
                why = "VehicleLights layout (named Type/MaterialType + component order)"
        if decision == "undecidable" and f["referents"]:
            decision = "referent"
            classes = ", ".join("%s×%d" % kv for kv in f["referents"].most_common(3))
            why = "object reference -> %s; e.g. %s" % (classes, f["sample_ref"])
        if decision == "undecidable":
            sibling = named.get((f["class"], f["offset"]))
            if sibling:
                why = ("no name in scope; a same-class named sibling %s sits at this offset but is "
                       "an array-element offset, not this field" % ", ".join(sibling))
            else:
                why = "no name in the stream, no referent, no named sibling at this offset"
        decisions[decision] += 1
        out_fields.append({
            "class": f["class"], "offset": f["offset"], "type": f["type"],
            "struct": f["struct"],
            "count": f["count"], "values": f["values"],
            "bits": sorted(f["bits"]),
            "contexts": sorted(f["contexts"]),
            "referents": dict(f["referents"].most_common()),
            "sample_ref": f["sample_ref"],
            "field_name": name, "decision": decision, "evidence": why})
    # offsets reused by several classes: the inherited region is where a single name would travel
    by_offset = collections.defaultdict(set)
    for f in out_fields:
        by_offset[f["offset"]].add(f["class"])
    shared = {str(k): sorted(v) for k, v in by_offset.items() if len(v) > 1}
    ev = bmscript_evidence()
    nat = native_evidence()
    summary = {
        "rows": len(rows), "classes": len({r["class"] for r in rows}),
        "archetype_rows": sum(1 for r in rows if is_archetype(r.get("class"))),
        "archetype_fields": sum(1 for f in out_fields if is_archetype(f["class"])),
        "archetype_occurrences": sum(f["count"] for f in out_fields if is_archetype(f["class"])),
        "unnamed_fields": len(out_fields),
        "unnamed_occurrences": sum(f["count"] for f in out_fields),
        "named_from_layout": decisions["named"],
        "named_from_class": decisions["named-class"],
        "named_from_sdk": decisions["named-sdk"],
        "named_from_segment": decisions["named-segment"],
        "named_from_element": decisions["named-element"],
        "identified_by_referent": decisions["referent"],
        "undecidable": decisions["undecidable"],
        "shared_offsets": len(shared),
        "bmscript_imports": len(ev["imports"]), "bmscript_on_disk": ev["on_disk"],
        "native_functions": nat["functions"], "native_classes": nat["classes"],
        "native_property_strings": nat["property_table_strings"],
    }
    return {"schema": 3, "generated_by": "grab_offsets.py",
            "evidence": {"bmscript": ev, "native": nat,
                         "package_invariant": (
                             "A UE3 UClass export's outer is the package it is defined in. The rows "
                             "import BmScript.RVehicleBatmobile / BmScript.RVehicleSimBatmobile / "
                             "BmScript.RBatmobile*, and no package named BmScript exists in the "
                             "install, so the defining package is not shipped.")},
            "fields": out_fields, "shared_offsets": shared, "summary": summary}


def write_md(doc):
    s = doc["summary"]
    ev = doc["evidence"]
    L = ["# Batmobile - the stripped property names, resolved (G1-1)", "",
         "Generated by `Tools/scripts/grab_offsets.py` from the `RVehicleBatmobile`/`RBatmobile*` "
         "rows.", "The cooker writes simple tags as `type + class offset + value` and drops the name;",
         "the engine rebuilds it from the native class layout. This page decides every one of the",
         "**%d** distinct fields from evidence instead of leaving it \"unnamed\"." % s["unnamed_fields"],
         "", "## Summary", "", "| fact | value |", "|---|---|"]
    for k, v in s.items():
        L.append("| %s | **%s** |" % (k, v))
    L += ["", "### How each field was decided", "",
          "| decision | fields | meaning |", "|---|---|---|",
          "| named (layout) | %d | the offset sits in a struct whose own tags prove the layout |"
          % s["named_from_layout"],
          "| named (class, anchored) | %d | an inline tag elsewhere in the same class pins the base; "
          "this slot carries an inline name |" % s["named_from_class"],
          "| named (SDK dump) | %d | the class + absolute offset + slot kind resolve in the BmSDK-AK "
          "class dump, generated from the running game |" % s["named_from_sdk"],
          "| named (class, segment) | %d | the slot lands under the base the preceding inline tag "
          "measures, with the property kind agreeing |" % s["named_from_segment"],
          "| named (struct element) | %d | the field is a member of the struct it sits in, read from "
          "that struct's own declaration |" % s["named_from_element"],
          "| referent | %d | an object reference: identified by the class and path it points at, "
          "even without a property name |" % s["identified_by_referent"],
          "| undecidable | %d | scalar/vector/name with no name, no referent and no slot the class "
          "definition can reach |" % s["undecidable"], "",
          "## Evidence", "",
          "- BmScript imports: **%d** - %s" % (s["bmscript_imports"], ", ".join(ev["bmscript"]["imports"])),
          "- Files named like BmScript anywhere in the install: **%d**"
          % len(ev["bmscript"]["files_on_disk"]),
          "- Native functions in the executable for these classes: **%d** over **%d** classes"
          % (s["native_functions"], s["native_classes"]),
          "- Class-qualified *property* strings in the executable: **%s**"
          % s["native_property_strings"], "",
          "- %s" % ev["package_invariant"], "",
          "**Disposition.** Every value the classes carry is preserved here by offset and, where the",
          "field is a reference, identified by its target.", "",
          "**The exe route is closed, by measurement.** `REGISTRATION.md` disassembles the native",
          "class registration: three arrays (`0x309E760` 5 entries, `0x30A46B0` 75, `0x30A4E20` 1),",
          "16-byte `{name, code}` records terminated by a zero pair, every name an `exec` function.",
          "There is no property table in the image and no class-qualified property string, so the",
          "names are not recoverable from `BatmanAK.exe` - they were never there.", "",
          "**Where the names actually are.** Two independent sources agree.", "",
          "1. `BmGame.upk` ships class definitions. `RVehicleSimBatmobile` declares 165 properties,",
          "named and typed, in declaration order; the archetypes import `RVehicleBatmobile` from the",
          "missing `BmScript`, but its parent `RVehicleBatmobileBase` *is* shipped. `bmak_bind.py`",
          "walks each stream against its class: an inline tag name pins the base, and a tag binds",
          "only when it lands on a slot of the agreeing `UProperty` kind.",
          "2. The BmSDK-AK project generates C# bindings *from the running game*: every `UProperty`",
          "carries the absolute object offset the engine linked it to, and every struct its runtime",
          "`Size`. That is the same number space as `FPropertyTagBat2.Offset`, so a cooked field",
          "resolves by class + offset + kind even where the shipped script copy is smaller than the",
          "linked class. `bmsdk_offsets.py` indexes that dump; `BMSDK_OFFSETS.json` is the index.",
          "",
          ("**{a}** of the {b} fields are named from the dump, **{c}** from struct declarations "
           "(the innermost struct on the tag path, including packed bools), **{d}** from the "
           "`VehicleLights` layout, and **{e}** from an inline tag.").format(
               a=s["named_from_sdk"], b=s["unnamed_fields"], c=s["named_from_element"],
               d=s["named_from_layout"],
               e=s["named_from_class"] + s["named_from_segment"]), "",
          "**Why the dump is the same build.** `RVehicleSimBatmobile`'s dump size is 1220 and the",
          "upk class, walked with this build's rules (static-array `ArrayDim`, 4-byte property",
          "alignment, 20-byte `FInterpCurve` slots), lands exactly on 1220; `RVehicleSimCar` agrees",
          "on 37/37 names and 456 bytes; `RBatmobileMissileLauncher`, `RBatmobileEMPMissile`,",
          "`RBatmobileAllegianceSwitcher` and `RBatmobileBooster` agree on every name and every",
          "class size. The native `SetDriveMode` writes the byte at `0x3B0` and `SkidToStop` at",
          "`0x3B1`, which is where the dump puts `DriveMode` / `SkidToStopDir`. For object fields the",
          "dump's declared type matches the archetype's referent class on every one of the 195",
          "references.", "",
          "**Correction this made.** The `8000` scalar at `0x4A8` is",
          "`AirControlYawTorqueFactorMax`, not `AirControlTimeInAir`. The earlier walk under-sized",
          "two slot families - static arrays (`ArrayDim`) and the transmission struct's six-float",
          "`GearRatios` - and offset the base to compensate, which put the whole `AirControl*` run",
          "one slot early. With this build's real slot sizes `AirControlTimeInAir` is at `0x4BC`,",
          "the class ends at `0x4C4`, and `0x4A8` is a torque factor - which is what 8000 reads as.",
          "",
          "**Nested structs, resolved without guessing.** `BmGame.upk` declares both",
          "`BMScreenShakeStruct` and its `AdvancedOptions` child (`BMAdvancedScreenShakeStruct`).  The",
          "tag path names the container, so each offset is read against the **innermost** struct:",
          "`AdvancedOptions.<0x0000>` is one of the three `bAmplitude*ShowsInitialDirection` bools,",
          "while `<0x0090>` in the outer struct is the shared word for `bSmoothLoc`/`bSmoothRot`.",
          "`BoolProperty` tags carry the whole bitfield word (kept as `bits`, schema 6), so the mask",
          "names the exact members instead of collapsing the word to one bool.  This closes the last",
          "eight undecidable fields.  It also split one key that really was two fields:",
          "`RBatmobileCannon 0x0004 FloatProperty` is `TimeDuration` in the shake struct and `OutVal`",
          "in a curve point, so the field total is 423, not 422; no value or occurrence was added or",
          "removed, only the two meanings are counted separately.", "",
          "## Fields", "",
          "| class | offset | type | in struct | count | decision | name / referent | evidence |",
          "|---|---|---|---|---|---|---|---|"]
    for f in sorted(doc["fields"], key=lambda x: (x["class"], x["offset"], x["struct"] or "")):
        ident = f["field_name"] or (list(f["referents"])[0] if f["referents"] else "—")
        L.append("| %s | 0x%04X | %s | %s | %d | %s | %s | %s |" % (
            f["class"], f["offset"], f["type"], f["struct"] or "-", f["count"], f["decision"],
            ident, (f["evidence"] or "—").replace("|", "/")))
    L += ["", "## Offsets shared by several classes", "",
          "The inherited region: one name would cover every class listed. %d offsets are shared."
          % len(doc["shared_offsets"]), "",
          "| offset | classes |", "|---|---|"]
    for off, classes in sorted(doc["shared_offsets"].items(), key=lambda kv: int(kv[0])):
        L.append("| 0x%04X | %s |" % (int(off), ", ".join(classes)))
    open(os.path.join(OUT, "OFFSETS.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L))
    return os.path.join(OUT, "OFFSETS.md")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = build()
    if a.write:
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, "OFFSETS.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, indent=1)
        print("wrote", os.path.relpath(os.path.join(OUT, "OFFSETS.json"), ROOT), "and",
              os.path.relpath(write_md(doc), ROOT))
    print(json.dumps(doc["summary"], indent=1))
    if a.check:
        fail, s = [], doc["summary"]
        if s["archetype_rows"] != 53:
            fail.append("expected 53 RBatmobile*/RVehicleBatmobile rows, got %d"
                        % s["archetype_rows"])
        if s["archetype_fields"] != 366 or s["archetype_occurrences"] != 1736:
            fail.append("archetype field/occurrence count changed: %d / %d"
                        % (s["archetype_fields"], s["archetype_occurrences"]))
        if s["unnamed_fields"] != 423 or s["unnamed_occurrences"] != 2593:
            fail.append("total field/occurrence count changed: %d / %d"
                        % (s["unnamed_fields"], s["unnamed_occurrences"]))
        if s["bmscript_on_disk"]:
            fail.append("BmScript is on disk - the blocked fields must be re-opened")
        lights = [f for f in doc["fields"] if "VehicleLights" in f["contexts"] and f["field_name"]]
        if len(lights) < 4:
            fail.append("the VehicleLights struct is not fully named: %d of 4" % len(lights))
        if (s["named_from_class"] + s["named_from_segment"] + s["named_from_element"]) < 20:
            fail.append("expected the class definition to bind fields, got %d"
                        % (s["named_from_class"] + s["named_from_segment"]
                           + s["named_from_element"]))
        if (s["named_from_layout"] + s["named_from_class"] + s["named_from_segment"]
                + s["named_from_sdk"] + s["named_from_element"] + s["identified_by_referent"]
                + s["undecidable"]) != s["unnamed_fields"]:
            fail.append("decisions do not add up to the field count")
        if s["named_from_sdk"] < 350:
            fail.append("the BmSDK-AK dump resolved only %d fields (was 380) - index stale?"
                        % s["named_from_sdk"])
        if s["undecidable"] != 0:
            fail.append("undecidable fields appeared: %d (expected 0)" % s["undecidable"])
        if any(not f["field_name"] and not f["referents"] for f in doc["fields"]):
            fail.append("a field has neither a name nor a referent")
        if s["native_property_strings"]:
            fail.append("the executable carries a property table - names may be recoverable after all")
        if any(not f["evidence"] for f in doc["fields"]):
            fail.append("a field has no evidence")
        if fail:
            print("FAIL")
            for f in fail:
                print("  -", f)
            return 1
        print("OK: %d fields (%d archetype), %d named (%d from the SDK dump), %d by referent, "
              "%d undecidable, BmScript absent"
              % (s["unnamed_fields"], s["archetype_fields"],
                 s["named_from_layout"] + s["named_from_class"] + s["named_from_segment"]
                 + s["named_from_sdk"] + s["named_from_element"],
                 s["named_from_sdk"], s["identified_by_referent"], s["undecidable"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
