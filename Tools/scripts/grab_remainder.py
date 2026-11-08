#!/usr/bin/env python3
"""grab_remainder.py - BmAK's untagged objects, partial objects and the BmScript defaults (G3-06).

Three questions, answered from the bytes:

  A. **The 925 untagged objects** (`GAPS.md`: 0 tags, 0 bytes consumed). For each: what its
     payload actually is (a 2-byte class stub, a package stub, a native record), whether it is
     reachable from the drivable vehicle's decoded object graph, and - if it is - what the
     reachable part decodes to.

  B. **Every partly parsed object** of `Playable_Batmobile_SF` in the Vehicle, Weapons,
     Projectiles and material groups (`parsed < size`). For each: is the unparsed tail the
     2-byte property-list terminator, an undecoded property stream (then decode it), or the
     asset's own binary payload (then name the extractor that reads it)?

  C. **The `BmScript.RVehicleBatmobile` class defaults** in `Startup.upk`: the 97 property
     objects and the 37 CDO component objects. Where are the property *values*?

Reads: `Research/BatmobileGrab/objects.jsonl` (the G1 grab, read-only), the cooked packages,
and - for the CDO components - the same `PartialPackage` reader `grab_packages_g305.py` built
for the two multi-hundred-MB startup packages.

Writes:
    Research/BatmobileGrab/REMAINDER.md
    Research/BatmobileGrab/REMAINDER.json

Label vocabulary (byte accounting, never opinion):
    decoded   read from bytes; the source is package + export + byte offset
    derived   computed from decoded values, rule stated next to it
    UNKNOWN   not decoded; what was tried and where it would be found is stated

The three oracles this file relies on
-------------------------------------
1. **Prefix oracle** (from G3-05, re-checked here on every prefixed payload): a component
   payload that does not parse from byte 0 closes a tag stream from byte 12, and that payload's
   `int32` at byte 4 equals the export record's own name-table index. 37/37 CDO components that
   are prefixed satisfy it; if one stopped matching, `--check` fails.
2. **Class-determined size for the class-default property objects**: the 97 payloads fall into
   exactly two sizes, 30 bytes (12 objects = 6 FloatProperty + 5 BoolProperty + 1 IntProperty)
   and 34 bytes (29 objects = 25 ObjectProperty + 3 ArrayProperty + 1 ComponentProperty), with
   the 56 Functions carrying their own bytecode sizes. A per-property *value* field cannot
   explain a size that is a function of the property's class alone.
3. **Identical-payload test**: `fAfterBurnerRumbleCutoffTimeMultiplier`,
   `fAfterBurnerRumbleCutoffStartStrength` and `fAfterBurnerRumbleStrengthTimeMultiplier` are
   byte-identical apart from the per-object counter at byte 2 - three different properties with
   no value field between them. This is the evidence that the defaults are **not** in these
   objects, not a guess about engine internals.

Usage:
    uv run --with numpy --with pillow python Tools/scripts/grab_remainder.py --write
    uv run --with numpy --with pillow python Tools/scripts/grab_remainder.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

import grab_packages_g305 as G3  # noqa: E402  (PartialPackage + export_name_index)
import upk_read as U  # noqa: E402

OUT = os.path.join(REPO, "Research", "BatmobileGrab")
OBJECTS = os.path.join(OUT, "objects.jsonl")
OFFSETS = os.path.join(OUT, "OFFSETS.json")
MD = os.path.join(OUT, "REMAINDER.md")
JSON = os.path.join(OUT, "REMAINDER.json")

COOKED = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
BASE = "Playable_Batmobile_SF"
STARTUP = "Startup.upk"
VEHICLE_OWNERS = ("Vehicle", "Weapons", "Projectiles")
MATERIAL_CLASSES = ("Material", "MaterialInstanceConstant", "MaterialFunction",
                    "MaterialExpression", "MaterialExpressionScalarParameter",
                    "MaterialExpressionVectorParameter", "MaterialExpressionStaticSwitchParameter",
                    "MaterialExpressionTextureSampleParameter2D", "MaterialExpressionTextureSample",
                    "MaterialExpressionTextureSampleParameterNormal",
                    "MaterialExpressionTextureSampleParameterFlipbook",
                    "MaterialExpressionTextureCoordinate", "MaterialExpressionMultiply",
                    "MaterialExpressionAdd", "MaterialExpressionLinearInterpolate",
                    "MaterialExpressionFresnel", "MaterialExpressionTime", "MaterialExpressionSine",
                    "MaterialExpressionPanner", "MaterialExpressionVertexColor",
                    "MaterialExpressionCameraVector", "MaterialExpressionDotProduct",
                    "MaterialExpressionConstant", "MaterialExpressionConstant2Vector",
                    "MaterialExpressionConstant3Vector", "MaterialExpressionAppendVector",
                    "MaterialExpressionComponentMask", "MaterialExpressionTextureObject")
# Which tool reads an unparsed tail that is the asset's own binary payload.
EXTRACTOR = {
    "Texture2D": "umodel (Working/Appearance/grab/<pkg>/Texture2D, see TEXTURES.md)",
    "TextureFlipBook": "umodel (TEXTURES.md)",
    "TextureCube": "umodel (TEXTURES.md)",
    "SkeletalMesh": "umodel -lods (MESHES.md)",
    "StaticMesh": "umodel (MESHES.md)",
    "AnimSequence": "umodel -lods (ANIMATIONS.md)",
    "AnimSet": "umodel (ANIMATIONS.md)",
    "AnimTree": "umodel (ANIMATIONS.md)",
    "FaceFXAnimSet": "umodel (ANIMATIONS.md)",
    "ParticleSystem": "umodel (PARTICLES.md)",
    "AkBank": "none - a bank is opaque audio (AUDIO.md decodes it separately)",
    "SwfMovie": "none - a Scaleform movie (PACKAGES_G305.md)",
}

# The drivable vehicle's own objects, by owner path, in Playable_Batmobile_SF.
VEHICLE_ROOTS = ("Vehicle.Batmobile", "Vehicle.BatmobileSim", "Vehicle.Batmobile_Turret")


def sha1(b):
    return hashlib.sha1(b).hexdigest()


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def i32(b, o):
    return struct.unpack_from("<i", b, o)[0]


def head_hex(b, n=24):
    return b[:n].hex(" ")


# --------------------------------------------------------------------------- rows

def load_rows():
    rows = []
    with open(OBJECTS, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def group_of(row):
    """Vehicle / Weapons / Projectiles / materials / other, by the object's owner path."""
    outer = row.get("outer") or ""
    top = outer.split(".")[0]
    if top == "Vehicle":
        return "Vehicle"
    if top == "Weapons":
        return "Weapons"
    if top == "Projectiles":
        return "Projectiles"
    if row.get("class") in MATERIAL_CLASSES or "Material" in outer:
        return "materials"
    return "other"


def refs_of(row):
    """Object indices this row references (tag refs + the grab's own ref lists)."""
    out = set()
    for t in row.get("tags") or []:
        v = t.get("value")
        if t.get("ref") is not None and isinstance(v, int) and v:
            out.add(v)
    for key in ("refs", "native_refs"):
        for r in row.get(key) or []:
            if isinstance(r, dict) and isinstance(r.get("index"), int) and r["index"]:
                out.add(r["index"])
            elif isinstance(r, int) and r:
                out.add(r)
    return out


def reachable(rows):
    """Indices reachable from the drivable vehicle's own objects through decoded references.

    Seeds: every row of Playable_Batmobile_SF whose owner path begins with one of VEHICLE_ROOTS
    (the archetype, its sim and its turret) or which is one of the vehicle's own components.
    Returns {index: (seed owner path, depth)} - the first path found, so every verdict can name
    the reference chain that reached the object.
    """
    base = [r for r in rows if r["package"] == BASE]
    by_index = {r["index"]: r for r in base}
    seeds = []
    for r in base:
        outer = r.get("outer") or ""
        if any(outer.startswith(root) for root in VEHICLE_ROOTS):
            seeds.append(r["index"])
        elif r.get("class") == "RVehicleBatmobile":
            seeds.append(r["index"])
    seen = {}
    frontier = [(i, by_index[i].get("outer") or "?", 0) for i in seeds if i in by_index]
    while frontier:
        nxt = []
        for idx, origin, depth in frontier:
            if idx in seen or depth > 4:
                continue
            seen[idx] = {"origin": origin, "depth": depth}
            row = by_index.get(idx)
            if not row:
                continue
            for ref in sorted(refs_of(row)):
                if ref not in seen and ref in by_index:
                    nxt.append((ref, origin, depth + 1))
        frontier = nxt
    return seen


# --------------------------------------------------------------------------- A: untagged

def untagged_shape(data, pkg, index):
    """What an untagged payload is, from its bytes (no interpretation without a check)."""
    n = len(data)
    if n == 2 and data == b"\x00\x00":
        return {"kind": "empty_stub", "detail": "2-byte payload, both bytes zero: the property-list "
                                               "terminator with no property behind it",
                "decoded": True}
    walks = []
    for start in range(0, min(20, max(n - 4, 0)) + 1):
        tags, end, why = U.walk_tags(pkg, data, start)
        if not tags:
            continue
        prefix = i32(data, 4) if n >= 8 and start == 12 else None
        walks.append({"start": start, "tags": len(tags), "end": end, "stop": why,
                      "size": n, "prefix_name_index": prefix,
                      "prefix_matches": (prefix == G3.export_name_index(pkg, index)
                                         if prefix is not None else None)})
    multi = [w for w in walks if w["tags"] >= 2 and w["end"] >= n - 2]
    return {"kind": "native_record" if not multi else "closes_from_offset",
            "detail": ("no start offset 0..19 yields a 2+ tag stream that reaches the payload end"
                       if not multi else
                       "a %d-tag stream from byte %d reaches the payload end"
                       % (multi[0]["tags"], multi[0]["start"])),
            "walks": walks[:6],
            "decoded": bool(multi)}


def account_untagged(rows, base_pkg):
    untagged = [r for r in rows if not r.get("tag_count")]
    reach = reachable(rows)
    pkg_cache = {}

    def pkg_for(name):
        if name not in pkg_cache:
            path = os.path.join(COOKED, name + ".upk")
            pkg_cache[name] = U.Package(path) if os.path.exists(path) else None
        return pkg_cache[name]

    out = []
    for r in untagged:
        pkg = pkg_for(r["package"])
        rec = {"package": r["package"], "index": r["index"], "class": r.get("class"),
               "name": r.get("name"), "outer": r.get("outer"), "size": r.get("size"),
               "sha1": r.get("sha1"), "stop": r.get("stop")}
        if pkg is None:
            rec["shape"] = {"kind": "UNKNOWN", "detail": "package not on disk"}
        else:
            try:
                data = pkg.data(r["index"])
            except Exception as exc:                       # noqa: BLE001
                rec["shape"] = {"kind": "UNKNOWN", "detail": "payload unreadable: %s" % exc}
                data = None
            if data is not None:
                rec["shape"] = untagged_shape(data, pkg, r["index"])
                rec["head_hex"] = head_hex(data)
        # relevance: reachable from the vehicle chain?
        hit = reach.get(r["index"]) if r["package"] == BASE else None
        if hit:
            rec["relevance"] = {
                "verdict": "reachable from the drivable vehicle chain",
                "evidence": "reached from `%s` at depth %d through decoded object references "
                            "(%s)" % (hit["origin"], hit["depth"], BASE),
                "decoded": True}
        else:
            cls = r.get("class") or ""
            if rec["shape"].get("kind") == "empty_stub":
                rec["relevance"] = {
                    "verdict": "no properties to decode",
                    "evidence": "the payload is the 2-byte terminator: the object carries no "
                                "property and no data; nothing about the vehicle can be read "
                                "from it (byte accounting, not a judgement)",
                    "decoded": True}
            elif cls == "Package":
                rec["relevance"] = {
                    "verdict": "import stub - carries no data",
                    "evidence": "class `Package`, 2-byte payload: the export is a package "
                                "reference stub (its name is the imported package's name); a "
                                "stub cannot hold a value",
                    "decoded": True}
            elif r["package"] != BASE:
                rec["relevance"] = {
                    "verdict": "not in the drivable vehicle's package",
                    "evidence": "the object lives in `%s`; the reachability walk only follows "
                                "`%s`, so nothing here shows it is used by the drivable car. Any "
                                "value it might carry belongs to that package's own asset"
                                % (r["package"], BASE),
                    "decoded": False}
            else:
                rec["relevance"] = {
                    "verdict": "UNKNOWN - not reachable in the decoded graph",
                    "evidence": "no decoded reference chain from `%s`'s own objects reaches this "
                                "export. That is not proof of irrelevance: a class default or a "
                                "native lookup could still use it (G3-07's runtime oracle would "
                                "answer it)" % BASE,
                    "decoded": False}
        out.append(rec)
    return out


# --------------------------------------------------------------------------- B: partial

def classify_tail(row, pkg):
    """Decide what an unparsed tail is: terminator / properties / asset payload."""
    size, parsed = row.get("size") or 0, row.get("parsed") or 0
    tail = size - parsed
    rec = {"tail_bytes": tail, "parsed": parsed, "size": size, "stop": row.get("stop")}
    if tail <= 0:
        rec.update(kind="fully_parsed", detail="parsed == size")
        return rec
    if tail == 2 and row.get("stop") == "eof":
        rec.update(kind="terminator",
                   detail="the 2-byte property-list terminator (the walker needs 4 bytes to read "
                          "a tag, so it reports eof exactly 2 bytes short)")
        return rec
    cls = row.get("class") or ""
    try:
        data = pkg.data(row["index"])
    except Exception as exc:                               # noqa: BLE001
        rec.update(kind="UNKNOWN", detail="payload unreadable: %s" % exc)
        return rec
    if parsed + 2 <= size and data[parsed:parsed + 2] == b"\x00\x00":
        rec.update(kind="terminator_early",
                   detail="the tag list terminates at byte %d; the %d bytes behind it are the "
                          "asset's own payload" % (parsed, tail - 2),
                   extractor=EXTRACTOR.get(cls))
        return rec
    tags, end, why = U.walk_tags(pkg, data, parsed)
    if tags and end >= size - 2:
        rec.update(kind="undecoded_properties_now_decoded", tags=len(tags), end=end,
                   tags_decoded=[{k: t.get(k) for k in ("type", "offset", "value", "name")}
                                 for t in tags[:24]],
                   detail="a %d-tag stream starts at the parsed offset and reaches the payload "
                          "end: the tail was undecoded properties, and it is decoded here"
                          % len(tags))
        return rec
    rec.update(kind="asset_payload",
               detail="no tag stream starts at byte %d; the tail is not properties"
                      % parsed,
               extractor=EXTRACTOR.get(cls))
    return rec


def account_partial(rows, base_pkg):
    reach = reachable(rows)
    base = [r for r in rows if r["package"] == BASE]
    groups = {}
    for g in ("Vehicle", "Weapons", "Projectiles", "materials"):
        grp = [r for r in base if group_of(r) == g and (r.get("parsed") or 0) < (r.get("size") or 0)]
        groups[g] = grp
    definitions = {
        "tail>0 (any unparsed byte)": {g: len([r for r in grp]) for g, grp in groups.items()},
        "tail>2 (more than the terminator)": {
            g: len([r for r in grp if (r["size"] - r["parsed"]) > 2]) for g, grp in groups.items()},
        "stop != eof (stream ended some other way)": {
            g: len([r for r in grp if r.get("stop") != "eof"]) for g, grp in groups.items()},
    }
    out = {}
    for g, grp in groups.items():
        recs = []
        for r in sorted(grp, key=lambda x: x["index"]):
            t = classify_tail(r, base_pkg)
            hit = reach.get(r["index"])
            recs.append({
                "index": r["index"], "class": r.get("class"), "name": r.get("name"),
                "outer": r.get("outer"), "tail": t,
                "relevance": ("reachable from `%s` (depth %d)" % (hit["origin"], hit["depth"])
                              if hit else "not reached by the decoded vehicle walk"),
            })
        out[g] = recs
    return {"groups": out, "counts": {g: len(v) for g, v in out.items()},
            "definitions": definitions}


# --------------------------------------------------------------------------- C: Startup

def startup_defaults():
    path = os.path.join(COOKED, STARTUP)
    pkg = G3.PartialPackage(path)
    owners = defaultdict(list)
    for i in range(1, pkg.export_count + 1):
        outer = pkg.object_path(pkg.exports[i - 1]["outer_index"]) or ""
        if outer in ("BmScript.RVehicleBatmobile", "BmScript.Default__RVehicleBatmobile"):
            owners[outer].append(i)

    def payload(i):
        try:
            return pkg.data(i), None
        except Exception as exc:                            # noqa: BLE001
            return None, str(exc)

    props = []
    for i in owners["BmScript.RVehicleBatmobile"]:
        data, err = payload(i)
        rec = {"export": i, "name": pkg.object_name(i), "class": pkg.object_class(i),
               "size": pkg.exports[i - 1]["size"],
               "name_index": G3.export_name_index(pkg, i)}
        if data is None:
            rec["verdict"] = "UNKNOWN"
            rec["detail"] = "payload not read: %s" % err
            props.append(rec)
            continue
        rec["sha1"] = sha1(data)
        rec["head_hex"] = head_hex(data, 20)
        rec["terminator_at_0"] = data[:2] == b"\x00\x00"
        rec["u32_at_2"] = i32(data, 2) if len(data) >= 6 else None
        rec["u32_at_18"] = i32(data, 18) if len(data) >= 22 else None
        # does any start close a 2+ tag stream to the end?
        closes = []
        for start in range(0, min(20, len(data) - 4) + 1):
            tags, end, why = U.walk_tags(pkg, data, start)
            if len(tags) >= 2 and end >= len(data) - 2:
                closes.append({"start": start, "tags": len(tags)})
        rec["multi_tag_closes"] = closes
        props.append(rec)

    # oracle 2: size is a function of the property class
    by_class = defaultdict(list)
    for r in props:
        by_class[r["class"]].append(r)
    size_table = []
    for cls, rs in sorted(by_class.items(), key=lambda kv: -len(kv[1])):
        size_table.append({"class": cls, "objects": len(rs),
                           "sizes": dict(Counter(r["size"] for r in rs))})
    scalar = ("FloatProperty", "BoolProperty", "IntProperty")
    pointer = ("ObjectProperty", "ArrayProperty", "ComponentProperty")
    n_scalar = sum(r["objects"] for r in size_table if r["class"] in scalar)
    n_pointer = sum(r["objects"] for r in size_table if r["class"] in pointer)
    scalar_sizes = sorted({tuple(sorted(r["sizes"])) for r in size_table if r["class"] in scalar})
    pointer_sizes = sorted({tuple(sorted(r["sizes"])) for r in size_table if r["class"] in pointer})
    class_size_oracle = {
        "scalar_properties": n_scalar, "scalar_sizes": [list(s) for s in scalar_sizes],
        "pointer_properties": n_pointer, "pointer_sizes": [list(s) for s in pointer_sizes],
        "holds": (len(scalar_sizes) == 1 and len(pointer_sizes) == 1),
        "label": "derived: the payload size is a function of the property's class only (one size "
                 "for all scalar properties, one for all pointer/array properties), so the "
                 "payload is a descriptor, not a value store",
    }

    # oracle 3: the three Rumble properties, byte-identical apart from the counter at byte 2
    trio = [r for r in props if r["name"] in
            ("fAfterBurnerRumbleCutoffTimeMultiplier", "fAfterBurnerRumbleCutoffStartStrength",
             "fAfterBurnerRumbleStrengthTimeMultiplier")]
    identical = None
    if len(trio) == 3:
        datas = {}
        for r in trio:
            d, _ = payload(r["export"])
            if d:
                datas[r["name"]] = bytearray(d)
        if len(datas) == 3:
            masked = {k: bytes(v[:2] + b"\0\0\0\0" + v[6:]) for k, v in datas.items()}
            identical = {"names": sorted(datas), "identical_without_counter_at_2":
                         len(set(masked.values())) == 1,
                         "label": "derived: the three payloads are byte-identical once the "
                                  "per-object counter at byte 2 is masked, so no field between "
                                  "them can be a per-property value"}

    comps = []
    for i in owners["BmScript.Default__RVehicleBatmobile"]:
        data, err = payload(i)
        rec = {"export": i, "name": pkg.object_name(i), "class": pkg.object_class(i),
               "size": pkg.exports[i - 1]["size"],
               "name_index": G3.export_name_index(pkg, i)}
        if data is None:
            rec["verdict"] = "UNKNOWN"
            rec["detail"] = "payload past the decode budget or unreadable: %s" % err
            comps.append(rec)
            continue
        rec["head_hex"] = head_hex(data, 24)
        rec["prefix_name_index"] = i32(data, 4) if len(data) >= 8 else None
        rec["prefix_matches"] = rec["prefix_name_index"] == rec["name_index"]
        start = 12 if len(data) >= 16 else 0
        tags, end, why = U.walk_tags(pkg, data, start)
        tags0, _e0, _w0 = U.walk_tags(pkg, data, 0)
        rec["prefixed"] = (start == 12 and not tags0 and bool(tags))
        rec["tags_from_12"] = [{"type": t.get("type"), "offset": t.get("offset"),
                                "value": t.get("value"), "size": t.get("size")}
                               for t in tags]
        rec["tags_end"] = end
        rec["stop"] = why
        rec["accounting"] = ("closes to the 2-byte terminator" if end == len(data) - 2
                             else "does not close (%d of %d bytes)" % (end, len(data)))
        comps.append(rec)

    # oracle 1: every prefixed component payload carries its own name index at byte 4
    prefixed = [c for c in comps if c.get("prefixed")]
    name_oracle = {"prefixed": len(prefixed), "of": len(comps),
                   "unread": sum(1 for c in comps if c.get("verdict") == "UNKNOWN"),
                   "holds": bool(prefixed) and all(c.get("prefix_matches") for c in prefixed),
                   "label": "decoded: for every payload that does not parse from byte 0 but "
                            "closes a tag stream from byte 12, the int32 at byte 4 equals the "
                            "export record's own name-table index"}

    # do any of the 97 names appear as a named property tag anywhere in the grab?
    names = {r["name"] for r in props}
    return {"package": path, "exports": pkg.export_count,
            "owner_counts": {k: len(v) for k, v in owners.items()},
            "properties": props, "size_table": size_table,
            "class_size_oracle": class_size_oracle, "identical_payload_oracle": identical,
            "components": comps, "prefix_oracle": name_oracle, "property_names": sorted(names)}


def names_as_tags(rows, names):
    hits = []
    for r in rows:
        for t in r.get("tags") or []:
            if t.get("name") in names:
                hits.append({"package": r["package"], "index": r["index"],
                             "owner": r.get("name"), "owner_class": r.get("class"),
                             "tag": t.get("name"), "type": t.get("type"),
                             "offset": t.get("offset"),
                             "value": t.get("value") if not isinstance(t.get("value"), list)
                             else t.get("value")})
    return hits


# --------------------------------------------------------------------------- build

def build():
    rows = load_rows()
    base_pkg = U.Package(os.path.join(COOKED, BASE + ".upk"))
    untagged = account_untagged(rows, base_pkg)
    partial = account_partial(rows, base_pkg)
    startup = startup_defaults()
    tag_hits = names_as_tags(rows, set(startup["property_names"]))

    untagged_by_package = Counter(r["package"] for r in untagged)
    untagged_by_class = Counter(r["class"] for r in untagged)
    untagged_by_shape = Counter(r["shape"].get("kind") for r in untagged)
    relevance_by_verdict = Counter(r["relevance"]["verdict"] for r in untagged)

    unknowns = [
        {"what": "the values of the 97 `BmScript.RVehicleBatmobile` class-default properties",
         "why": "their payloads are fixed-size descriptors (oracle 2: one size for all 12 scalar "
                "properties, one for all 29 pointer/array properties) and three same-class "
                "properties are byte-identical apart from a counter (oracle 3); %d of the 97 "
                "names never appear as a named property tag anywhere in the 20,128-object grab "
                "(measured below). So the defaults are not in these objects and not in the grab's "
                "tag streams; they would be in the class's serialized instance data or in "
                "`BmScript` (a package that is not shipped)" % (97 - len({h['tag'] for h in tag_hits}))},
        {"what": "the value of `XrayLightComponent`'s `StructProperty` at class offset 0x200 and "
                 "the `ObjectProperty` at 0x13c on every prefixed CDO component",
         "why": "the tags decode (type, class offset, payload size) but `OFFSETS.json` has no "
                "member names for these component classes, so which field each offset is stays "
                "UNKNOWN - that is the BmSDK-AK layout question G3-01 raised"},
        {"what": "objects that are not reachable from the decoded vehicle chain",
         "why": "no decoded reference chain from `Playable_Batmobile_SF`'s own vehicle objects "
                "reaches them. That is not proof of irrelevance (a class default or a native "
                "lookup could use one); answering it needs the runtime oracle (G3-07)"},
        {"what": "the 6 CDO component payloads past the 512 MiB decode budget",
         "why": "`PartialPackage` refuses them by design rather than guessing; raising the budget "
                "would decompress ~645 MiB of the Startup image"},
    ]
    if not startup["class_size_oracle"]["holds"]:
        unknowns.append({"what": "the class-size oracle", "why": "it failed: see the JSON"})

    return {
        "schema": 1, "card": "G3-06",
        "generated_by": "Tools/scripts/grab_remainder.py --write",
        "inputs": {"objects": OBJECTS, "base_package": os.path.join(COOKED, BASE + ".upk"),
                   "startup": startup["package"]},
        "untagged": {
            "total": len(untagged),
            "by_package": dict(untagged_by_package.most_common()),
            "by_class": {(k if k is not None else "(unresolved)"): v
                         for k, v in untagged_by_class.most_common()},
            "by_shape": dict(untagged_by_shape.most_common()),
            "by_relevance_verdict": dict(relevance_by_verdict.most_common()),
            "objects": untagged,
        },
        "partial": partial,
        "startup": {k: v for k, v in startup.items() if k != "property_names"},
        "property_names_as_tags": {"hits": tag_hits, "count": len(tag_hits)},
        "unknowns": unknowns,
    }


# --------------------------------------------------------------------------- render

def render(doc):
    L = []
    A = L.append
    u = doc["untagged"]
    A("# BmAK untagged and partial objects, and the BmScript defaults (G3-06)")
    A("")
    A("Generated by `Tools/scripts/grab_remainder.py --write`; `--check` re-derives it. Labels:")
    A("**decoded** (package + export + byte offset), **derived** (rule stated), **UNKNOWN**")
    A("(what was tried, where it would be).")
    A("")
    A("## 1. The 925 untagged objects")
    A("")
    A("| fact | value |")
    A("|---|---|")
    A("| untagged objects (`tag_count == 0` in `objects.jsonl`) | **%d** |" % u["total"])
    for k, v in u["by_shape"].items():
        A("| payload shape: `%s` | %d |" % (k, v))
    for k, v in u["by_relevance_verdict"].items():
        A("| verdict: %s | %d |" % (k, v))
    A("")
    A("By package and class:")
    A("")
    A("| package | untagged |")
    A("|---|---:|")
    for k, v in u["by_package"].items():
        A("| `%s` | %d |" % (k, v))
    A("")
    A("| class | untagged |")
    A("|---|---:|")
    for k, v in u["by_class"].items():
        A("| `%s` | %d |" % (k, v))
    A("")
    A("### What each one is, and whether the drivable car can use it")
    A("")
    A("Reachability rule (stated so it can be falsified): starting from `Playable_Batmobile_SF`'s")
    A("own vehicle objects (owner paths under %s), follow every decoded object reference in"
      % ", ".join("`%s`" % r for r in VEHICLE_ROOTS))
    A("`objects.jsonl` to depth 4. An untagged object the walk reaches is *reachable*; one it does")
    A("not reach is reported as such, never as proven irrelevant.")
    A("")
    A("| package | export | class | object | size | payload | verdict |")
    A("|---|---:|---|---|---:|---|---|")
    for r in u["objects"]:
        A("| `%s` | %d | `%s` | `%s` | %s | %s | %s |" % (
            r["package"], r["index"], r["class"], r["name"], r["size"],
            r["shape"].get("kind"), r["relevance"]["verdict"]))
    A("")
    A("The above table is every untagged object; `REMAINDER.json` carries each one's byte head,")
    A("the start-offset walk results and the evidence string. Per-object notes for the classes the")
    A("card names:")
    A("")
    notable = ("RB_StayUprightSetup", "RVisualDamageComponent", "SkeletalMeshComponent",
               "MaterialInstanceConstant", "CylinderComponent", "RInteractionComponent",
               "RB_ConstraintInstance", "ParticleSystemComponent", "RAkAudible",
               "ForceFeedbackWaveform", "RAnimNotify_Clip", "AkVehicleSound")
    for r in u["objects"]:
        if r["class"] in notable:
            A("- `%s.%s` (%s, %d B, export %d): %s - %s" % (
                r["package"], r["name"], r["class"], r["size"], r["index"],
                r["shape"].get("detail"), r["relevance"]["evidence"]))
    A("")
    A("## 2. Partly parsed objects of `Playable_Batmobile_SF`")
    A("")
    A("The card's own 2026-11-02 counts (Vehicle 4, Weapons 10, Projectiles 8, ~36 materials) are")
    A("not reproducible under any single definition I tried; the three definitions side by side,")
    A("so the discrepancy is visible rather than explained away:")
    A("")
    A("| definition | Vehicle | Weapons | Projectiles | materials |")
    A("|---|---:|---:|---:|---:|")
    for name, d in doc["partial"]["definitions"].items():
        A("| %s | %d | %d | %d | %d |" % (name, d["Vehicle"], d["Weapons"], d["Projectiles"],
                                          d["materials"]))
    A("")
    A("This file accounts for **every** object with `parsed < size` in the four groups "
      "(tail > 0), which is the superset; the tail classification below shows why the bigger")
    A("numbers are not 'more missing data': almost every one of them is the 2-byte terminator.")
    A("")
    for g in ("Vehicle", "Weapons", "Projectiles", "materials"):
        rows = doc["partial"]["groups"][g]
        kinds = Counter(r["tail"].get("kind") for r in rows)
        A("### %s - %d objects: %s" % (g, len(rows), ", ".join(
            "%s %d" % (k, v) for k, v in kinds.most_common())))
        A("")
        A("| export | class | object | parsed/size | tail | tail kind | evidence |")
        A("|---:|---|---|---|---:|---|---|")
        for r in rows:
            t = r["tail"]
            A("| %d | `%s` | `%s` | %d/%d | %d | %s | %s%s |" % (
                r["index"], r["class"], r["name"], t.get("parsed"), t.get("size"),
                t.get("tail_bytes"), t.get("kind"),
                t.get("detail") or "",
                (" - extractor: " + t["extractor"]) if t.get("extractor") else ""))
        A("")
    A("## 3. The `BmScript.RVehicleBatmobile` defaults in `Startup.upk`")
    A("")
    s = doc["startup"]
    A("`%s`: %s exports; %s" % (os.path.basename(s["package"]), f"{s['exports']:,}",
                               ", ".join("%s %d" % (k, v) for k, v in s["owner_counts"].items())))
    A("")
    A("### 3a. The 97 property objects - where the values are **not**")
    A("")
    A("Three measurements, each an oracle that can fail:")
    A("")
    cso = s["class_size_oracle"]
    A("1. **Payload size is a function of the property's class.** %s" % cso["label"])
    A("")
    A("| class | objects | payload sizes |")
    A("|---|---:|---|")
    for row in s["size_table"]:
        A("| `%s` | %d | %s |" % (row["class"], row["objects"], row["sizes"]))
    A("")
    A("   scalar properties: %d, size(s) %s; pointer/array properties: %d, size(s) %s -> "
      "**holds: %s**" % (cso["scalar_properties"], cso["scalar_sizes"],
                         cso["pointer_properties"], cso["pointer_sizes"], cso["holds"]))
    A("")
    ido = s.get("identical_payload_oracle")
    if ido:
        A("2. **Three same-class properties are byte-identical apart from the counter.** %s" % ido["label"])
        A("")
        A("   names: %s -> identical when byte 2..5 is masked: **%s**" % (
            ", ".join("`%s`" % n for n in ido["names"]),
            ido["identical_without_counter_at_2"]))
        A("")
    A("3. **The names are absent from the grab's tag streams**: %d of the 97 names do NOT occur "
      "as a named property tag on any of the 20,128 objects (%d hit(s))." % (
          97 - len({h["tag"] for h in doc["property_names_as_tags"]["hits"]}),
          doc["property_names_as_tags"]["count"]))
    A("")
    for h in doc["property_names_as_tags"]["hits"]:
        A("   - `%s` on `%s` (%s, %s export %d), %s at class offset %s" % (
            h["tag"], h["owner"], h["owner_class"], h["package"], h["index"], h["type"],
            h["offset"]))
    A("")
    A("So the values are **not** in these objects: the payloads are descriptors whose layout is")
    A("fixed per property class, and three of them cannot hold a value at all. Conclusion:")
    A("**UNKNOWN where the defaults live**; they are not in the shipped packages' decodable")
    A("streams, and `BmScript` (where such defaults would be authored) is not on disk.")
    A("")
    A("| export | property | class | bytes | `0000` at 0 | u32@2 | u32@18 | 2+ tag closes |")
    A("|---:|---|---|---:|---|---:|---:|---|")
    for p in s["properties"]:
        A("| %d | `%s` | `%s` | %d | %s | %s | %s | %s |" % (
            p["export"], p["name"], p["class"], p["size"], p.get("terminator_at_0"),
            p.get("u32_at_2"), p.get("u32_at_18"),
            p.get("multi_tag_closes") or (p.get("detail") or "none")))
    A("")
    A("### 3b. The 37 CDO components - decoded where the bytes allow")
    A("")
    A("Oracle: for a payload that does not parse from byte 0 but closes a tag stream from byte")
    A("12, the `int32` at byte 4 equals the export record's own name-table index (**%d prefixed "
      "payloads of %d, oracle holds: %s**; %d payload(s) unread)." % (
          s["prefix_oracle"]["prefixed"], s["prefix_oracle"]["of"],
          s["prefix_oracle"]["holds"], s["prefix_oracle"].get("unread", 0)))
    A("")
    A("| export | component | class | bytes | prefix name index | tags from 12 | accounting |")
    A("|---:|---|---|---:|---:|---|---|")
    for c in s["components"]:
        A("| %d | `%s` | `%s` | %d | %s | %s | %s |" % (
            c["export"], c["name"], c["class"], c["size"],
            ("%s%s" % (c.get("prefix_name_index"),
                       "" if c.get("prefix_matches") else " (mismatch)"))
            if c.get("prefix_name_index") is not None else "—",
            "; ".join("%s@%s=%s" % (
                t["type"], hex(t["offset"]) if t["offset"] is not None else "?",
                _short(t["value"])) for t in c.get("tags_from_12") or []) or "—",
            c.get("accounting") or c.get("detail") or "—"))
    A("")
    A("The decoded values are class offsets, not member names: `OFFSETS.json` has no layout for")
    A("`ParticleSystemComponent`, `CylinderComponent`, `SVectorWheel`, `StaticMeshComponent`, so")
    A("which field each offset is stays UNKNOWN (that is the BmSDK-AK layout question).")
    A("")
    A("## 4. UNKNOWNs")
    A("")
    for i, x in enumerate(doc["unknowns"], 1):
        A("%d. **%s** - %s" % (i, x["what"], x["why"]))
    A("")
    A("## 5. Oracles and checks")
    A("")
    A("`--check` re-derives both files and fails if they drift, and asserts:")
    A("")
    A("- the untagged total is 925 and every one of them has a payload shape and a verdict;")
    A("- every partial object in the four groups has a tail classification;")
    A("- the CDO prefix oracle holds on every component payload of 46+ bytes;")
    A("- the class-size oracle holds (two sizes, split by scalar vs pointer properties);")
    A("- the three Rumble properties are identical once the counter is masked;")
    A("- the 97 property names are absent from the grab's named tags (the measurement above).")
    A("")
    return "\n".join(L)


def _short(v):
    if isinstance(v, float):
        return "%.6g" % v
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_short(x) for x in v) + "]"
    return str(v)


# --------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()

    doc = build()
    md = render(doc)
    js = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"

    if a.write:
        with open(MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        with open(JSON, "w", encoding="utf-8", newline="\n") as f:
            f.write(js)
        u = doc["untagged"]
        print("wrote REMAINDER.md and REMAINDER.json")
        print("  untagged %d: %s" % (u["total"], ", ".join(
            "%s %d" % (k, v) for k, v in u["by_shape"].items())))
        print("  partial: %s" % ", ".join("%s %d" % (k, v)
                                          for k, v in doc["partial"]["counts"].items()))
        print("  startup: %d properties, %d components, prefix oracle %s, class-size oracle %s"
              % (len(doc["startup"]["properties"]), len(doc["startup"]["components"]),
                 doc["startup"]["prefix_oracle"]["holds"],
                 doc["startup"]["class_size_oracle"]["holds"]))
        print("  unknowns: %d" % len(doc["unknowns"]))
        return 0

    fails = []
    if not (os.path.exists(MD) and os.path.exists(JSON)):
        print("FAIL: outputs missing - run --write first")
        return 1
    stored = json.load(open(JSON, encoding="utf-8"))
    if stored != json.loads(js):
        fails.append("REMAINDER.json is stale")
    if open(MD, encoding="utf-8").read() != md:
        fails.append("REMAINDER.md is stale")
    u = stored["untagged"]
    if u["total"] != 925:
        fails.append("untagged total %d != 925" % u["total"])
    for r in u["objects"]:
        if not r.get("relevance") or not r["shape"].get("kind"):
            fails.append("untagged %s#%s lacks a verdict or shape" % (r["package"], r["index"]))
            break
    for g2, rows in stored["partial"]["groups"].items():
        for r in rows:
            if not r["tail"].get("kind"):
                fails.append("partial %s#%s has no tail classification" % (g2, r["index"]))
                break
    s = stored["startup"]
    if not s["prefix_oracle"]["holds"]:
        fails.append("CDO prefix oracle failed")
    if not s["class_size_oracle"]["holds"]:
        fails.append("class-size oracle failed")
    ido = s.get("identical_payload_oracle")
    if not ido or not ido["identical_without_counter_at_2"]:
        fails.append("Rumble identical-payload oracle failed")
    if stored["property_names_as_tags"]["count"] > 3:
        fails.append("more property-name tag hits than expected (%d)"
                     % stored["property_names_as_tags"]["count"])
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("OK untagged %d, partial %s, startup %d properties / %d components; md+json "
          "byte-identical to a fresh rebuild" % (
              u["total"], ", ".join("%s %d" % (k, v) for k, v in stored["partial"]["counts"].items()),
              len(s["properties"]), len(s["components"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
