#!/usr/bin/env python
"""jc3lights.py - G2-33: the JC3 vehicle light system in one document.

The card: "one document: `SVehicleLight` member list and presets, how a light binds to a part
(`has_lights`), the `CarLight` block format, what a custom light without a preset needs", with
a recipe for one custom light (the wheel-arch light) and every member value sourced.

Inputs (all already-decoded tables; no archive is opened, `D:\\Games` is never read):
  * ``E:/Modding/_gamedata/JC3grab/entities/*.ee.json`` - the `VehicleDynamicLights` module of every
    vehicle: the real light entries (`lights[i].*`, 25 members incl. the part binding).
  * ``E:/Modding/_gamedata/JC3grab/detail/*.ee.json`` - the `.epe` graph's `SVehicleLight` /
    `SVehicleLights` / `SVehicleLightList` objects (the named preset side, no part binding).
  * ``Research/JC3Grab/PARTS_TABLE.jsonl`` - `has_lights`, `part_index`, damage type, model.
  * ``Research/JC3Grab/GEOMETRY.jsonl`` - every `CarLight` block's payload census.
  * ``Research/JC3Grab/INDEX.jsonl`` - proof whether any light/preset *table* exists outside
    the vehicle entities.
  * ``Research/BatmobileGrab/LIGHTS.json`` - the BmAK side (G1-17): the wheel-arch light's
    socket, bone, colour, cone, `jc3_part` and `jc3_anchor`.
  * ``Tools/scripts/rbmhdr.hash_jenkins`` - the game's string hash; used only to recompute
    hashes that 3,217 shipped rows already carry, and every recomputation is asserted.

Writes Research/JC3Grab/LIGHT_SYSTEM.md + LIGHT_SYSTEM.json. `--check` re-derives both.

Usage:
  python jc3lights.py --write
  python jc3lights.py --check
  python jc3lights.py dump module|epe|binding|recipe
"""
from __future__ import annotations

import argparse
import collections
import difflib
import glob
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rbmhdr  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
BMAK = os.path.join(ROOT, "Research", "BatmobileGrab", "LIGHTS.json")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_gamedata/JC3grab")
JSON_NAME = "LIGHT_SYSTEM.json"
MD_NAME = "LIGHT_SYSTEM.md"
DONOR = ("editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
         "v0300_car_kensington_sportsmuscle_civilian_01.ee")
BMAK_PACKAGE = "Playable_Batmobile_SF"          # the shipped base Batmobile package
BMAK_SOCKET = "LWheelLight"                    # the left wheel-arch light
LIGHT_ENTRY = re.compile(r"lights\[(\d+)\]\.(.+)")
MODULE = "VehicleDynamicLights"


def h(text: str) -> int:
    return rbmhdr.hash_jenkins(text.encode("utf-8"))


def cell(v) -> str:
    """Markdown table cell: the anchors are full of `|`, which would split the row."""
    return str(v).replace("|", "\\|")


def slug(entity: str) -> str:
    return entity.rsplit("/", 1)[-1][:-3] if entity.endswith(".ee") else entity


# ---------------------------------------------------------------------- readers
def scan_module() -> dict:
    """Every `VehicleDynamicLights` entry in the fleet, keyed per module (a vehicle may have two)."""
    files = sorted(glob.glob(os.path.join(RAW, "entities", "*.ee.json")))
    members: collections.Counter = collections.Counter()
    mtypes: dict[str, str] = {}
    behaviours: collections.Counter = collections.Counter()
    presets: collections.Counter = collections.Counter()
    preset_sigs: dict[int, set] = collections.defaultdict(set)
    value_census: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    per_entity: dict[str, int] = {}
    entries: list[dict] = []
    hash_ok = {"part": 0, "behavior": 0, "transform": 0}
    hash_bad: list[str] = []
    with_module = 0
    zero_preset: list[dict] = []
    for p in files:
        d = json.load(open(p, encoding="utf-8"))
        entity = d["entity"]
        n_here = 0
        for mi, m in enumerate(d["modules"]):
            if m.get("type") != MODULE:
                continue
            cur: dict[int, dict] = {}
            for r in m.get("rows") or []:
                mm = LIGHT_ENTRY.fullmatch(r["path"])
                if not mm:
                    continue
                i, name = int(mm.group(1)), mm.group(2)
                mtypes[name] = r["type"]
                members[name] += 1
                cur.setdefault(i, {})[name] = r["value"]
            for i in sorted(cur):
                e = cur[i]
                e["_entity"] = entity
                e["_module"] = mi
                e["_i"] = i
                entries.append(e)
                n_here += 1
                behaviours[str(e.get("behavior"))] += 1
                pid = int(e.get("preset_id") or 0)
                presets[pid] += 1
                preset_sigs[pid].add((
                    round(float(e.get("diffuse.R", 0)), 6), round(float(e.get("diffuse.G", 0)), 6),
                    round(float(e.get("diffuse.B", 0)), 6), e.get("range"), e.get("angle"),
                    e.get("multiplier"), e.get("light_type"), e.get("falloff_start"),
                    e.get("near_cap")))
                for k in ("range", "falloff_start", "near_cap", "multiplier", "min_luminosity",
                          "light_type", "blinking", "angle", "cast_shadows",
                          "projected_texture_index", "volumetric_mode", "volume_intensity",
                          "uvscale.u", "uvscale.v"):
                    if k in e:
                        value_census[k][str(e[k])] += 1
                if pid == 0:
                    zero_preset.append({"entity": entity, "behavior": e.get("behavior"),
                                        "part": e.get("part"), "range": e.get("range"),
                                        "angle": e.get("angle"),
                                        "multiplier": e.get("multiplier"),
                                        "diffuse": [e.get("diffuse.R"), e.get("diffuse.G"),
                                                    e.get("diffuse.B")]})
                if h(str(e.get("part"))) == int(e.get("part_hash") or -1):
                    hash_ok["part"] += 1
                else:
                    hash_bad.append(f"{slug(entity)}#{i} part")
                if h(str(e.get("behavior"))) == int(e.get("behavior_hash") or -1):
                    hash_ok["behavior"] += 1
                else:
                    hash_bad.append(f"{slug(entity)}#{i} behavior")
                if h(str(e.get("deformable_transform"))) == int(
                        e.get("deformable_transform_hash") or -1):
                    hash_ok["transform"] += 1
                else:
                    hash_bad.append(f"{slug(entity)}#{i} transform")
        if n_here:
            with_module += 1
            per_entity[entity] = n_here
    return {
        "entity_files": files, "entities_with_module": with_module, "entries": entries,
        "per_entity": per_entity, "members": members, "member_types": mtypes,
        "behaviors": dict(sorted(behaviours.items(), key=lambda kv: (-kv[1], kv[0]))),
        "presets": presets, "inconsistent_presets": {
            k: len(v) for k, v in preset_sigs.items() if len(v) > 1},
        "value_census": {k: dict(v.most_common()) for k, v in value_census.items()},
        "hash_ok": hash_ok, "hash_bad": hash_bad, "zero_preset": zero_preset,
    }


def scan_epe() -> dict:
    """The `.epe` side: named `SVehicleLight` objects (no part binding) + their lists."""
    files = sorted(glob.glob(os.path.join(RAW, "detail", "*.ee.json")))
    counts: collections.Counter = collections.Counter()
    members: collections.Counter = collections.Counter()
    mtypes: dict[str, str] = {}
    presets: collections.Counter = collections.Counter()
    names: collections.Counter = collections.Counter()
    values: dict[str, set] = collections.defaultdict(set)
    per_entity: dict[str, int] = {}
    for p in files:
        d = json.load(open(p, encoding="utf-8"))
        ent = slug(d["entity"])
        n = 0
        for o in ((d.get("epe") or {}).get("objects") or []):
            cls = str(o.get("class") or "")
            if not cls.startswith("SVehicleLight"):
                continue
            counts[cls] += 1
            if cls != "SVehicleLight":
                continue
            n += 1
            v = o.get("values") or {}
            for k, val in v.items():
                if k.startswith("_") or k in ("name", "name_hash"):
                    continue
                members[k] += 1
                mtypes.setdefault(k, "value")
                values[k].add(str(val))
            if "preset_id" in v:
                presets[str(v["preset_id"])] += 1
            if "name" in v:
                names[str(v["name"])] += 1
        if n:
            per_entity[ent] = n
    light_re = re.compile(r"wheel|arch", re.I)
    return {"files": files, "classes": dict(sorted(counts.items())), "members": members,
            "member_types": mtypes, "presets": presets, "names": names,
            "preset_names_matching_light_re": sorted(n for n in presets if light_re.search(n)),
            "value_census": {k: sorted(v)[:8] for k, v in values.items()},
            "per_entity": per_entity}


def scan_parts() -> dict:
    parts: dict[str, list[dict]] = {}
    for line in open(os.path.join(OUT, "PARTS_TABLE.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        parts[r["entity"]] = r["parts"]
    return {"parts": parts}


def bind(entries: list[dict], parts: dict[str, list[dict]]) -> dict:
    """Resolve every light entry's part_index against the parts module."""
    index_miss = 0
    name_miss = 0
    unlit = 0
    examples: dict[str, list[dict]] = {"index": [], "name": [], "unlit": []}
    for e in entries:
        plist = parts.get(e["_entity"]) or []
        idx = int(e.get("part_index") or 0)
        part = next((p for p in plist if p["i"] == idx), None)
        if part is None:
            index_miss += 1
            if len(examples["index"]) < 3:
                examples["index"].append({"entity": slug(e["_entity"]), "part_index": idx,
                                          "part": e.get("part"),
                                          "why": "part_index not in the module"})
            continue
        if part["n"] != e.get("part"):
            name_miss += 1
            if len(examples["name"]) < 3:
                examples["name"].append({"entity": slug(e["_entity"]), "part_index": idx,
                                         "part": e.get("part"),
                                         "why": f"module has {part['n']}"})
            continue
        if part.get("lights") != 1:
            unlit += 1
            if len(examples["unlit"]) < 3:
                examples["unlit"].append({"entity": slug(e["_entity"]), "part_index": idx,
                                          "part": e.get("part"), "why": "has_lights = 0"})
    total_parts = sum(len(v) for v in parts.values())
    lit = sum(1 for v in parts.values() for p in v if p.get("lights") == 1)
    land_light = sum(1 for v in parts.values() for p in v
                     if p.get("lights") == 1 and p.get("dt") == "Land_Light")
    lit_unused = 0
    for ent, plist in parts.items():
        used = {int(e.get("part_index") or 0) for e in entries if e["_entity"] == ent}
        lit_unused += sum(1 for p in plist if p.get("lights") == 1 and p["i"] not in used)
    donor = parts.get(DONOR, [])
    donor_exc = collections.Counter(p.get("dt") for p in donor if p.get("lights") == 1)
    return {"parts_total": total_parts, "parts_with_lights": lit, "parts_land_light": land_light,
            "donor_lit_by_damage_type": dict(donor_exc),
            "index_missing": index_miss, "name_mismatch": name_miss, "on_unlit_part": unlit,
            "examples": examples, "lit_parts_without_a_light": lit_unused,
            "donor_parts": len(donor),
            "donor_lit": sum(1 for p in donor if p.get("lights") == 1),
            "donor_land_light": sum(1 for p in donor if p.get("lights") == 1
                                    and p.get("dt") == "Land_Light")}


def carlight() -> dict:
    blocks = 0
    stride: collections.Counter = collections.Counter()
    width: collections.Counter = collections.Counter()
    slots: collections.Counter = collections.Counter()
    meshes = 0
    entities: set[str] = set()
    for line in open(os.path.join(OUT, "GEOMETRY.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        hit = False
        for b in r.get("blocks") or []:
            if b.get("type") != "CarLight":
                continue
            hit = True
            blocks += 1
            stride[b.get("vertex_stride")] += 1
            width[(b.get("payload") or {}).get("index_width")] += 1
            slots[b.get("material_slots")] += 1
        if hit:
            meshes += 1
            entities.add(r["entity"])
    return {"blocks": blocks, "meshes": meshes, "entities": len(entities),
            "stride": {str(k): v for k, v in stride.items()},
            "index_width": {str(k): v for k, v in width.items()},
            "material_slots": {str(k): v for k, v in slots.items()},
            "layout": {
                "static_header_bytes": 1085, "gap_bytes": 16, "buffers": [12, 24, 2],
                "source": "MODLOG.md §17 ('Window and CarLight solved from the files'); "
                          "solver Tools/scripts/_probe_layout.py, round-trip 190/193 blocks "
                          "byte-identical, 0 mismatched",
                "parameters": "UNKNOWN - the material/emissive parameter bytes are not "
                              "decoded (MODLOG §102d), so a CarLight block can be copied "
                              "byte-exact but not authored from numbers",
            }}


def index_scan() -> dict:
    outside = collections.Counter()
    preset_hits: list[str] = []
    for line in open(os.path.join(OUT, "INDEX.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        path = r.get("path", "")
        low = path.lower()
        if "/jc_vehicles/" in path:
            continue
        if "light" in low:
            outside[path.rsplit("/", 1)[0]] += 1
        if "preset" in low and ("light" in low or "vehicle" in low):
            preset_hits.append(path)
    return {"light_paths_outside_vehicles": sum(outside.values()),
            "by_dir": [[k, v] for k, v in outside.most_common(10)],
            "vehicle_light_preset_tables": sorted(set(preset_hits))[:20],
            "preset_count": len(set(preset_hits))}


def bmak_light() -> dict:
    d = json.load(open(BMAK, encoding="utf-8"))
    veh = next(v for v in d["vehicles"] if v["package"] == BMAK_PACKAGE)
    same = [e for e in veh["entries"] if e["socket"] == BMAK_SOCKET]
    e = next((x for x in same if x.get("type") == "VEHLT_HeadLight"), same[0])
    spot = next((c for c in e.get("components") or [] if c["class"] == "SpotLightComponent"), None)
    fields = (spot or {}).get("fields") or {}
    battle = [x for x in same if x.get("type") == "VEHLT_BattleModeLight"]
    return {
        "package": BMAK_PACKAGE, "socket": e["socket"],
        "same_socket_entries": len(same),
        "battle_mode": [{"type": x.get("type"), "behavior": x.get("behavior"),
                         "material_type": x.get("material_type")} for x in battle],
        "battle_mode_count": len(battle),
        "socket_location": e.get("socket_location"), "bone": e.get("bone"),
        "type": e.get("type"), "material_type": e.get("material_type"),
        "behavior": e.get("behavior"), "jc3_part": e.get("jc3_part"),
        "jc3_anchor": e.get("jc3_anchor"), "anchor_state": e.get("anchor_state"),
        "colour_rgba": fields.get("LightColor"), "radius": fields.get("Radius"),
        "outer_cone": fields.get("OuterConeAngle"), "brightness": fields.get("Brightness"),
        "falloff_exponent": fields.get("FalloffExponent"),
        "cast_shadows": fields.get("CastShadows"),
        "vanilla_reference": e.get("vanilla_reference"),
    }


def recipe(entries: list[dict], parts: dict[str, list[dict]], bmak: dict,
           epe_presets: dict, wheel_presets: list[str]) -> dict:
    """The wheel-arch light: one part + one module entry, every value with a source."""
    donor_parts = parts.get(DONOR, [])
    donor_dt = collections.Counter(p.get("dt") for p in donor_parts if p.get("lights") == 1)
    wheel = next(p for p in donor_parts if p["n"] == bmak["jc3_part"])
    template = next(e for e in entries
                    if e["_entity"] == DONOR and e.get("behavior") == "HeadLight"
                    and int(e.get("light_type") or 0) == 0 and int(e.get("blinking") or 0) == 0)
    colour = bmak.get("colour_rgba") or [0, 0, 0, 0]
    diffuse = [round(c / 255.0, 6) for c in colour[:3]]
    anchor = bmak["jc3_anchor"]
    part_name = bmak["jc3_part"]
    rows = [{"m": "behavior", "v": bmak["behavior"],
             "src": f"Research/BatmobileGrab/LIGHTS.json {BMAK_PACKAGE}/{BMAK_SOCKET} "
                    f"({bmak['type']} -> {bmak['behavior']}, G1-17 mapping)", "class": "decoded"},
            {"m": "behavior_hash", "v": h(bmak["behavior"]),
             "src": "rbmhdr.hash_jenkins(behavior); the same function reproduces all 3,217 "
                    "shipped behavior_hash values", "class": "derived (verified)"}]
    rows.append({"m": "part", "v": part_name,
                 "src": f"LIGHTS.json {BMAK_SOCKET}.jc3_part (the donor parts module has it at "
                        f"part_index {wheel['i']})", "class": "decoded"})
    rows.append({"m": "part_hash", "v": h(part_name),
                 "src": "rbmhdr.hash_jenkins(part); verified on all 3,217 shipped part_hash "
                        "values", "class": "derived (verified)"})
    rows.append({"m": "part_index", "v": wheel["i"],
                 "src": f"PARTS_TABLE.jsonl donor parts module ({wheel['n']}, "
                        f"damage type {wheel['dt']})", "class": "decoded"})
    for k, val in (("diffuse.R", diffuse[0]), ("diffuse.G", diffuse[1]), ("diffuse.B", diffuse[2])):
        rows.append({"m": k, "v": val,
                     "src": f"LIGHTS.json SpotLightComponent LightColor "
                            f"{colour[:3]} / 255 (sRGB -> 0..1)", "class": "derived"})
    for key, member in (("range", "range"), ("falloff_start", "falloff_start"),
                        ("near_cap", "near_cap"), ("multiplier", "multiplier"),
                        ("min_luminosity", "min_luminosity"), ("light_type", "light_type"),
                        ("blinking", "blinking"), ("angle", "angle"),
                        ("cast_shadows", "cast_shadows"),
                        ("projected_texture_index", "projected_texture_index"),
                        ("volumetric_mode", "volumetric_mode"),
                        ("volume_intensity", "volume_intensity"),
                        ("uvscale.u", "uvscale.u"), ("uvscale.v", "uvscale.v")):
        rows.append({"m": member, "v": template.get(key),
                     "src": f"donor module lights[{template['_i']}] (the shipped steady "
                            f"HeadLight point lamp, anchor {template['deformable_transform']})",
                     "class": "decoded"})
    rows.append({"m": "deformable_transform", "v": anchor,
                 "src": f"LIGHTS.json {BMAK_SOCKET}.jc3_anchor (socket {bmak['socket']}, bone "
                        f"{bmak['bone']}) - G1-17's translation of the BmAK socket chain",
                 "class": "decoded (mapped)"})
    rows.append({"m": "deformable_transform_hash", "v": h(anchor),
                 "src": "rbmhdr.hash_jenkins(anchor); verified on all 3,217 shipped "
                        "deformable_transform_hash values", "class": "derived (verified)"})
    preset_note = (f"the {len(wheel_presets)} preset names that mention wheel/arch are "
                   + ", ".join(f"`{n}`" for n in wheel_presets[:5])
                   + (" …" if len(wheel_presets) > 5 else "")
                   + "; none is a wheel-arch lamp, and no decoded file gives a preset's values,"
                   " so using one would import numbers nothing here explains"
                   if wheel_presets else
                   f"none of the {len(epe_presets)} `.epe` preset names mentions wheel or arch")
    rows.append({"m": "preset_id", "v": 0,
                 "src": "17 shipped entries carry preset_id 0 (modernbus brake lights, "
                        f"police siren) and every entry states its own numbers; {preset_note}",
                 "class": "decoded"})
    part_rows = [
        {"f": "name", "v": f"{part_name}_arch", "src": "new part, named after the wheel part "
         "it hangs on", "class": "derived"},
        {"f": "parent", "v": wheel["i"], "src": "PARTS_TABLE.jsonl donor: the wheel part",
         "class": "decoded"},
        {"f": "part_index", "v": "next free index in the parts module",
         "src": "must stay inside the module's part count; a new record needs a re-encode "
                "(MODLOG §101b writer gap)", "class": "derived"},
        {"f": "has_lights", "v": 1,
         "src": "the donor wheel part ships 0 (PARTS_TABLE.jsonl); 2,073 fleet parts ship 1, "
                "1,323 of them Land_Light", "class": "decoded"},
        {"f": "damage_type", "v": "Land_Light",
         "src": "the donor's lit parts by damage type: "
                + ", ".join(f"{k} x{v}" for k, v in sorted(donor_dt.items())),
         "class": "decoded"},
        {"f": "parent_space_offset", "v": bmak["socket_location"],
         "src": f"LIGHTS.json {BMAK_SOCKET}.socket_location (BmAK cm) - must go through "
                "T(p) from bat_assemble.py (R2), so the number here is the pre-transform "
                "source, not the final offset", "class": "decoded"},
        {"f": "model (lod+rbm)", "v": "new .lod whose lod1.rbm carries one CarLight block",
         "src": "every one of the 11,367 fleet CarLight blocks has vertex_stride 12, index "
                "width 2 and exactly 6 material slots; copy the block byte-exact from a "
                "vanilla light part (MODLOG §17), never author its parameters (§102d)",
         "class": "derived"},
        {"f": "anchor node in the rig", "v": f"wheel_f_l -> {bmak['bone']} -> "
         f"{bmak['bone']}_LIG",
         "src": "the light's deformable_transform resolves against this chain; LGT-1 §5 proved "
                "it is not in the RBM/parts bones/deform table - the §112 probe decides it",
         "class": "UNKNOWN (Q-1 probe)"},
    ]
    return {"light": {"name": f"wheel_arch_{bmak['socket'][0].lower()}", "rows": rows},
            "part": {"name": f"{part_name}_arch", "rows": part_rows},
            "template": {"entity": slug(DONOR), "index": template["_i"],
                         "behavior": template.get("behavior"),
                         "anchor": template.get("deformable_transform")},
            "bmak": bmak}


# ---------------------------------------------------------------------- build
def build() -> dict:
    module = scan_module()
    epe = scan_epe()
    parts = scan_parts()
    binding = bind(module["entries"], parts["parts"])
    cl = carlight()
    idx = index_scan()
    bmak = bmak_light()
    rec = recipe(module["entries"], parts["parts"], bmak, epe["presets"],
                 epe["preset_names_matching_light_re"])

    payload = {
        "card": "G2-33",
        "inputs": {
            "entity_caches": len(module["entity_files"]),
            "detail_graphs": len(epe["files"]),
            "parts_rows": len(parts["parts"]),
            "geometry_rows": sum(1 for _ in open(os.path.join(OUT, "GEOMETRY.jsonl"),
                                                 encoding="utf-8")),
            "index_sha1": hashlib.sha1(open(os.path.join(OUT, "INDEX.jsonl"), "rb")
                                       .read()).hexdigest()[:16],
            "bmak_lights_sha1": hashlib.sha1(open(BMAK, "rb").read()).hexdigest()[:16],
        },
        "module": {
            "entities_with_module": module["entities_with_module"],
            "entries": len(module["entries"]),
            "entities_without_module": sorted(
                slug(e) for e in set(module["entity_files"]) - set(module["per_entity"])),
            "per_entity": {slug(k): v for k, v in sorted(module["per_entity"].items())},
            "members": [{"path": k, "type": module["member_types"][k], "count": v}
                        for k, v in sorted(module["members"].items(),
                                           key=lambda kv: (-kv[1], kv[0]))],
            "behaviors": module["behaviors"],
            "presets": {"distinct": len(module["presets"]),
                        "zero": len(module["zero_preset"]),
                        "inconsistent": len(module["inconsistent_presets"]),
                        "inconsistent_examples": {str(k): v for k, v in sorted(
                            module["inconsistent_presets"].items(),
                            key=lambda kv: (-kv[1], kv[0]))[:6]},
                        "top": [[k, v] for k, v in module["presets"].most_common(10)]},
            "value_census": module["value_census"],
            "zero_preset_rows": module["zero_preset"],
            "hash_check": {"entries": len(module["entries"]),
                           "part_ok": module["hash_ok"]["part"],
                           "behavior_ok": module["hash_ok"]["behavior"],
                           "transform_ok": module["hash_ok"]["transform"],
                           "bad": module["hash_bad"][:6]},
        },
        "epe": {
            "classes": epe["classes"],
            "lights": epe["classes"].get("SVehicleLight", 0),
            "entities_with_lights": len(epe["per_entity"]),
            "members": [{"path": k, "count": v, "sample_values": epe["value_census"][k]}
                        for k, v in sorted(epe["members"].items(),
                                           key=lambda kv: (-kv[1], kv[0]))],
            "preset_names": dict(sorted(epe["presets"].items(), key=lambda kv: (-kv[1], kv[0]))),
            "preset_names_distinct": len(epe["presets"]),
            "preset_names_matching_wheel": epe["preset_names_matching_light_re"],
        },
        "binding": binding,
        "carlight": cl,
        "index_scan": idx,
        "recipe": rec,
    }
    payload["digest"] = hashlib.sha1(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]
    return payload


# ---------------------------------------------------------------------- md
def render_md(d: dict) -> str:
    inp, mod, epe, b, cl, idx, rec = (d["inputs"], d["module"], d["epe"], d["binding"],
                                      d["carlight"], d["index_scan"], d["recipe"])
    L: list[str] = []
    a = L.append
    a("# The JC3 vehicle light system (G2-33)")
    a("")
    a("One place for the LGT-1/LGT-2 evidence: the light-entry member list, the presets, how a")
    a("light binds to a part (`has_lights`), the `CarLight` block format, what a custom light")
    a("without a preset needs, and the wheel-arch light recipe with a source for every value.")
    a("Generated by `Tools/scripts/jc3lights.py --write` from the decoded caches and tables;")
    a("`--check` rebuilds both files. No archive is opened and no game is launched.")
    a("")
    a("## Scope")
    a("")
    a("| input | value |")
    a("|---|---|")
    a(f"| entity caches (`entities/*.ee.json`) | {inp['entity_caches']} |")
    a(f"| `.epe` graphs (`detail/*.ee.json`) | {inp['detail_graphs']} |")
    a(f"| vehicles with a `VehicleDynamicLights` module | **{mod['entities_with_module']}** |")
    a(f"| light entries (`lights[]`) in those modules | **{mod['entries']:,}** |")
    a(f"| `.epe` `SVehicleLight` objects | **{epe['lights']:,}** in {epe['entities_with_lights']} graphs |")
    a(f"| `PARTS_TABLE.jsonl` rows / parts | {inp['parts_rows']} / {b['parts_total']:,} |")
    a(f"| `GEOMETRY.jsonl` rows | {inp['geometry_rows']:,} |")
    a(f"| `CarLight` blocks | **{cl['blocks']:,}** in {cl['meshes']:,} meshes / {cl['entities']} vehicles |")
    a("")
    a("## 1. The light entry (`VehicleDynamicLights`)")
    a("")
    a(f"{mod['entries']:,} entries over {mod['entities_with_module']} vehicles "
      f"({min(mod['per_entity'].values())}…{max(mod['per_entity'].values())} per vehicle). "
      "Each entry is one lamp: it names the part it hangs on and carries all of its own")
    a("numbers. A vehicle may carry **two** modules (the cargo-tank plane does), and each")
    a("numbers its entries from `lights[0]` again - a reader that keys by index alone loses")
    a("entries on that one vehicle.")
    a("")
    a("| member | type | entries carrying it |")
    a("|---|---|---|")
    for m in mod["members"]:
        a(f"| `{m['path']}` | {m['type']} | {m['count']:,} |")
    a("")
    a("Behaviour values actually used (the state machine's vocabulary):")
    a("")
    a("| behavior | entries |")
    a("|---|---|")
    for k, v in mod["behaviors"].items():
        a(f"| `{k}` | {v} |")
    a("")
    a("Value census of the numeric members (value -> entries):")
    a("")
    a("| member | values |")
    a("|---|---|")
    for k, v in mod["value_census"].items():
        vals = ", ".join(f"`{kk}` x{vv}" for kk, vv in list(v.items())[:8])
        a(f"| `{k}` | {vals} |")
    a("")
    a("## 2. The `.epe` side (`SVehicleLight`)")
    a("")
    a("| class | objects |")
    a("|---|---|")
    for k, v in epe["classes"].items():
        a(f"| `{k}` | {v:,} |")
    a("")
    a(f"The graph carries **{epe['lights']:,}** named `SVehicleLight` objects - more than the "
      f"{mod['entries']:,} module entries. They are **not the same list**: an `SVehicleLight`")
    a("object has no part, no part index and no transform, and its `preset_id` is a **string**")
    a("(`Front_Left_Point`), while the module's `preset_id` is a **uint32** hash and the module")
    a("entry is the only thing that binds a light to a part. Which of the two the renderer")
    a("reads at runtime is not stated by any file (`UNKNOWN`, Q-1 probe), so the recipe below")
    a("is written entirely against the module side, which is the side that carries the binding.")
    a("")
    a("| member | objects carrying it | sample values |")
    a("|---|---|---|")
    for m in epe["members"]:
        a(f"| `{m['path']}` | {m['count']:,} | {', '.join(m['sample_values'][:4])} |")
    a("")
    a(f"**{epe['preset_names_distinct']} preset names** appear on the `.epe` side "
      f"(`SVehicleLight.preset_id` strings), e.g.")
    a(", ".join(f"`{k}` x{v}" for k, v in list(epe["preset_names"].items())[:8]) + ".")
    a("")
    a("## 3. Presets: what they do and do not decide")
    a("")
    a(f"- **{mod['presets']['distinct']} distinct `preset_id` hashes** are used across the fleet.")
    a(f"- **{mod['presets']['zero']} shipped entries use `preset_id = 0`** - e.g. the modernbus "
      "brake lights and the police siren - so a light does not need a preset to ship.")
    a(f"- **{mod['presets']['inconsistent']} presets appear with more than one value tuple** "
      "across the vehicles that use them (top: "
      + ", ".join(f"`{k}` x{v}" for k, v in list(mod["presets"]["inconsistent_examples"].items())[:4])
      + "), so the preset does **not** fix the numbers: the entry's own members are what the")
    a("  data carries, and an entry that names a preset still ships its own `range`, `angle`,")
    a("  `multiplier` and colour.")
    a("- What the engine does with the preset (override the entry, or only pick the sound/")
    a("  behaviour) is code: `UNKNOWN`.")
    a("")
    a("The `preset_id = 0` rows:")
    a("")
    a("| vehicle | behavior | part | range | angle | multiplier | diffuse |")
    a("|---|---|---|---|---|---|---|")
    for r in mod["zero_preset_rows"][:12]:
        diff = ", ".join(str(round(float(x), 4)) for x in r["diffuse"])
        a(f"| `{slug(r['entity'])}` | `{r['behavior']}` | `{r['part']}` | {r['range']} | "
          f"{r['angle']} | {r['multiplier']} | {diff} |")
    a("")
    a("## 4. How a light binds to a part (`has_lights`)")
    a("")
    a(f"The binding is the triple (`part`, `part_index`, `deformable_transform`) on the module "
      f"entry, resolved against the vehicle's parts module. `has_lights` is a per-part flag in")
    a(f"that module ({b['parts_with_lights']:,} of {b['parts_total']:,} parts fleet-wide carry "
      f"it, {b['parts_land_light']:,} of them `Land_Light`); the `.epe` does not carry it.")
    a("")
    a("| check | entries |")
    a("|---|---|")
    a(f"| light entries | {mod['entries']:,} |")
    a(f"| `part_index` not in the parts module | {b['index_missing']} |")
    a(f"| `part_index` resolves to a **different** part name | {b['name_mismatch']} |")
    a(f"| part resolves but `has_lights = 0` | {b['on_unlit_part']} |")
    a(f"| `has_lights = 1` parts with **no** light entry | {b['lit_parts_without_a_light']:,} |")
    a("")
    if any(b["examples"].values()) if isinstance(b["examples"], dict) else b["examples"]:
        a("The exceptions, so nobody re-derives them:")
        a("")
        groups = (b["examples"].items() if isinstance(b["examples"], dict)
                  else [("all", b["examples"])])
        for why, rows in groups:
            for x in rows:
                a(f"- `{x['entity']}` part {x['part_index']} (`{x['part']}`): {x['why']}")
        a("")
    a("So `has_lights` is a **flag the artist sets, not a gate the loader enforces**: entries")
    a(f"exist on parts with it clear ({b['on_unlit_part']} of them), and "
      f"{b['lit_parts_without_a_light']} of the {b['parts_with_lights']:,} lit parts carry no")
    a(f"entry at all. Entries outnumber lit parts because **one part hosts several lamps** -")
    a("the donor's left tail-light part alone carries a `TailLight`, a `LeftSignal` and a")
    a("`Reverse` entry. The flag is still the right one for a new light part: every vanilla")
    a("light part has it set.")
    a("")
    a(f"Donor (`{slug(DONOR)}`): {b['donor_parts']} parts, {b['donor_lit']} with "
      f"`has_lights = 1`, {b['donor_land_light']} of them `Land_Light`; the rest are "
      + ", ".join(f"`{k}` x{v}" for k, v in sorted(b["donor_lit_by_damage_type"].items())
                  if k != "Land_Light") + ".")
    a("")
    a("## 5. The `CarLight` block")
    a("")
    a("| item | value |")
    a("|---|---|")
    a(f"| blocks in the fleet | {cl['blocks']:,} (one per light mesh) |")
    a(f"| meshes / vehicles carrying one | {cl['meshes']:,} / {cl['entities']} |")
    a("| vertex stride | " + ", ".join(f"{k} B x{v:,}" for k, v in cl["stride"].items()) + " |")
    a("| index width | " + ", ".join(f"{k} B x{v:,}" for k, v in cl["index_width"].items()) + " |")
    a("| material slots | " + ", ".join(f"{k} x{v:,}" for k, v in cl["material_slots"].items()) + " |")
    a("")
    a(f"Layout (solved from the files, {cl['layout']['source']}): static header "
      f"**{cl['layout']['static_header_bytes']} B**, {cl['layout']['gap_bytes']} B gap, buffers "
      f"`{cl['layout']['buffers']}` (vertex buffer, second stream, uint16 indices).")
    a(f"Parameters: **{cl['layout']['parameters']}**.")
    a("")
    a("What that means for a build: a light mesh is `CarLight` (emitter geometry) + `Window`")
    a("(lens glass). Copying a vanilla light part's blocks and clipping our own geometry into")
    a("them is safe (byte-exact round-trip proven); changing the emissive numbers is not,")
    a("because no decoded field says which parameter is the colour.")
    a("")
    a("## 6. What a custom light without a preset needs")
    a("")
    a("1. **A part to hang on.** The entry's `part_index` must exist in the parts module and")
    a("   its name must match `part`, or the binding is broken (see section 4). `has_lights = 1`")
    a("   on that part, and `Land_Light` as its damage type is the vanilla convention.")
    a("2. **An anchor in that part's rig.** `deformable_transform` is a node chain")
    a("   (`|sportsmuscle_LOD1|wheel_f_l|Wheel_Frnt_Left_Disc|Wheel_Frnt_Left_Disc_LIG`); the")
    a("   node is not in the RBM, not in the parts `bones` array and not in the deform table")
    a("   (LGT1_FINDINGS §5), so the part needs the node - either a rigged part or a dedicated")
    a("   light part placed at the socket. Which of those resolves is the §112 probe.")
    a("3. **All 25 members.** Every entry carries its own values (section 3), so a light with")
    a("   `preset_id = 0` is fully described by its row - that is what the 17 shipped zero-preset")
    a("   entries do.")
    a("4. **An emitter mesh.** A `CarLight` block in the part's `lod1.rbm` (plus `Window` for")
    a("   the lens) - the assembled Batmobile currently has none (LGT1_FINDINGS §4).")
    a("")
    a("## 7. The wheel-arch light recipe")
    a("")
    bm = rec["bmak"]
    a(f"Source: `{bm['package']}` / `{bm['socket']}` ({bm['type']}, material "
      f"{bm['material_type']}), bone `{bm['bone']}`, socket at {bm['socket_location']} (BmAK cm).")
    a(f"Its `SpotLightComponent` ships `LightColor` {bm['colour_rgba']}, `Radius` {bm['radius']},")
    a(f"`OuterConeAngle` {bm['outer_cone']}, `Brightness` {bm['brightness']} - i.e. **the BmAK")
    a("component itself is unlit** (radius, cone and brightness 0, colour alpha 0), so the")
    a("shape of the lamp is ours to choose and only the colour is decodable from it.")
    if bm["battle_mode_count"]:
        a("")
        a(f"The same socket also carries {bm['battle_mode_count']} `VEHLT_BattleModeLight`")
        a("entr" + ("y" if bm["battle_mode_count"] == 1 else "ies") + " ("
          + ", ".join(f"{x['type']} -> {x['behavior']}" for x in bm["battle_mode"])
          + ") - that is LGT-2's battle-mode spotlight, a second entry on this recipe's part")
        a("with the same 25 members and no extra machinery.")
    a("")
    a("### 7a. The module entry")
    a("")
    a("| member | value | source | class |")
    a("|---|---|---|---|")
    for r in rec["light"]["rows"]:
        a(f"| `{r['m']}` | `{cell(r['v'])}` | {cell(r['src'])} | {r['class']} |")
    a("")
    a("### 7b. The part it hangs on")
    a("")
    a("| field | value | source | class |")
    a("|---|---|---|---|")
    for r in rec["part"]["rows"]:
        a(f"| `{r['f']}` | `{cell(r['v'])}` | {cell(r['src'])} | {r['class']} |")
    a("")
    a("### 7c. Why the vanilla wheel part cannot host it as-is")
    a("")
    a(f"`{bm['jc3_part']}` ships `has_lights = 0` and its meshes are `CarPaintMM` only (all")
    a("four wheel parts, every LOD): there is no `CarLight` block to carry the glow and no")
    a("anchor node. That is why the recipe adds a part rather than editing the wheel's entry.")
    a("")
    a("## 8. What the files do not say (UNKNOWN)")
    a("")
    a("- **Which list the renderer reads** - the module entries (part-bound) or the `.epe`")
    a(f"  `SVehicleLight` objects ({epe['lights']:,}, preset-named, no part): `UNKNOWN`; the")
    a("  counts differ and no file joins them.")
    a("- **`preset_id` semantics** - whether the preset overrides the entry's members: `UNKNOWN`")
    a("  (the data only shows that entries with one preset carry different numbers).")
    a("- **`CarLight` material parameters** - which bytes are the emissive colour/intensity:")
    a("  `UNKNOWN` (MODLOG §102d). Copy blocks, never author them.")
    a("- **Range/angle units** - the vanilla values look like metres and degrees and the BmAK")
    a("  cone is in degrees, but no file states the unit: the recipe copies shipped numbers")
    a("  instead of converting, and only the colour is converted (sRGB / 255).")
    a("- **Whether `preset_id = 0` means \"no preset\"** or is simply a hash that no preset uses:")
    a("  `UNKNOWN`; it is what 17 shipped lights carry.")
    a("- **Anchor resolution** - whether a node chain in `deformable_transform` resolves through")
    a("  the parts module: the §112 probe (one part, one install, one night look).")
    a(f"- **Any light/preset table outside the vehicles**: "
      f"{idx['light_paths_outside_vehicles']} archive paths mention 'light' outside")
    a(f"  `jc_vehicles` and **{idx['preset_count']}** is a vehicle light-preset table - they are")
    a("  environment models and localisation. So the preset name space is per-vehicle data, not")
    a("  a global table (at least in the decoded index).")
    a("")
    a("## 9. Validation")
    a("")
    a("`python Tools/scripts/jc3lights.py --check` re-reads every input, rebuilds both files in")
    a("memory, compares them byte-for-byte and runs the table below (`assertions()`):")
    a("")
    a("| assertion | measured | expected |")
    a("|---|---|---|")
    for label, got, want in assertions(d):
        a(f"| {label} | {got} | {want} |")
    a("")
    return "\n".join(L)


# ---------------------------------------------------------------------- checks
def assertions(d: dict) -> list[tuple[str, object, object]]:
    mod, epe, b, cl, idx, rec = (d["module"], d["epe"], d["binding"], d["carlight"],
                                 d["index_scan"], d["recipe"])
    return [
        ("entity caches read", d["inputs"]["entity_caches"], 232),
        ("vehicles with a light module", mod["entities_with_module"], 223),
        ("light entries", mod["entries"], 3217),
        ("members per entry", len(mod["members"]), 25),
        ("distinct behaviour values", len(mod["behaviors"]), 9),
        ("distinct preset ids", mod["presets"]["distinct"], 393),
        ("entries with preset_id 0", mod["presets"]["zero"], 17),
        ("presets with inconsistent values", mod["presets"]["inconsistent"], 34),
        ("part_hash recomputed", mod["hash_check"]["part_ok"], 3217),
        ("behavior_hash recomputed", mod["hash_check"]["behavior_ok"], 3217),
        ("deformable_transform_hash recomputed", mod["hash_check"]["transform_ok"], 3217),
        (".epe SVehicleLight objects", epe["lights"], 3972),
        (".epe SVehicleLights objects", epe["classes"].get("SVehicleLights"), 233),
        (".epe SVehicleLightList objects", epe["classes"].get("SVehicleLightList"), 412),
        ("distinct .epe preset names", epe["preset_names_distinct"], 404),
        ("parts with has_lights = 1", b["parts_with_lights"], 2073),
        ("light entries whose part_index misses", b["index_missing"], 3),
        ("light entries on a different part name", b["name_mismatch"], 27),
        ("light entries on a has_lights = 0 part", b["on_unlit_part"], 6),
        ("CarLight blocks", cl["blocks"], 11367),
        ("CarLight vertex stride values", list(cl["stride"]), ["12"]),
        ("CarLight material slots values", list(cl["material_slots"]), ["6"]),
        ("vehicle light-preset tables outside jc_vehicles", idx["preset_count"], 0),
        ("recipe members", len(rec["light"]["rows"]), 25),
        ("recipe values that are UNKNOWN", sum(1 for r in rec["light"]["rows"]
                                               if "UNKNOWN" in str(r["class"])), 0),
    ]


def invariants(d: dict) -> list[str]:
    bad: list[str] = []
    for label, got, want in assertions(d):
        if got != want:
            bad.append(f"{label} {got} != {want}")
    return bad


def summary(d: dict) -> str:
    mod, b, cl, rec = d["module"], d["binding"], d["carlight"], d["recipe"]
    return (f"{mod['entries']:,} light entries / {mod['entities_with_module']} vehicles, "
            f"{len(mod['members'])} members, {len(mod['behaviors'])} behaviours, "
            f"{mod['presets']['distinct']} presets ({mod['presets']['zero']} use 0, "
            f"{mod['presets']['inconsistent']} inconsistent), "
            f"hashes {mod['hash_check']['part_ok']}/{mod['hash_check']['behavior_ok']}/"
            f"{mod['hash_check']['transform_ok']} recomputed; "
            f"binding {b['parts_with_lights']:,} lit parts, {b['name_mismatch']} name misses, "
            f"{b['on_unlit_part']} on unlit parts; "
            f"CarLight {cl['blocks']:,} blocks stride {list(cl['stride'])} "
            f"slots {list(cl['material_slots'])}; recipe {len(rec['light']['rows'])} members")


# ---------------------------------------------------------------------- cmds
def cmd_write() -> int:
    d = build()
    bad = invariants(d)
    if bad:
        print("REFUSED: " + "; ".join(bad))
        return 1
    with open(os.path.join(OUT, JSON_NAME), "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    md = render_md(d)
    with open(os.path.join(OUT, MD_NAME), "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    print(f"{JSON_NAME}/{MD_NAME}: {summary(d)}, {len(md.splitlines())} md lines")
    return 0


def cmd_check() -> int:
    d = build()
    bad = invariants(d)
    jp, mp = os.path.join(OUT, JSON_NAME), os.path.join(OUT, MD_NAME)
    if not (os.path.exists(jp) and os.path.exists(mp)):
        print(f"FAIL: {JSON_NAME}/{MD_NAME} missing - run --write")
        return 1
    if json.load(open(jp, encoding="utf-8")) != d:
        bad.append(f"{JSON_NAME} stale")
    md = render_md(d)
    have = open(mp, encoding="utf-8").read()
    if md != have:
        diff = list(difflib.unified_diff(have.splitlines(), md.splitlines(), "file",
                                         "rebuilt", n=1))
        bad.append("md differs: " + " | ".join(diff[2:8]))
    if bad:
        print("FAIL: " + "; ".join(bad))
        return 1
    print(f"PASS: {summary(d)}")
    return 0


def cmd_dump(what: str) -> int:
    d = build()
    key = {"module": "module", "epe": "epe", "binding": "binding", "recipe": "recipe"}.get(what)
    if key is None:
        print("one of: module, epe, binding, recipe")
        return 2
    print(json.dumps(d[key], indent=1, ensure_ascii=False)[:14000])
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    dl = sub.add_parser("dump")
    dl.add_argument("what", nargs="?", default="module")
    a = p.parse_args()
    if a.write:
        return cmd_write()
    if a.check:
        return cmd_check()
    if a.cmd == "dump":
        return cmd_dump(a.what)
    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
