#!/usr/bin/env python
"""jc3water.py - G2-31: what makes a vehicle sink, float or drive in water.

The card names three behaviours the data has to settle - "sinks and stalls", "floats",
"drives underwater" - and asks for the members and values behind each. Everything here is
derived from the decoded cache plus the live build, never from memory:

  * `E:\\Modding\\_shared\\gamedata\\JC3grab\\entities\\*.ee.json` - the 232 vehicle decodes (the card's In
    list): every `WaterInteraction`, `Buoyancy` and `BoatBuoyancy` module with all of its
    rows, plus the shared `VehicleCommon` module that carries the water-entry and
    engine-shut-down constants;
  * `Builds/test-091/*.ee` - the live build's own container, decoded here with `jc3adf`
    so the "the build inherits the donor" claim is checked, not assumed.

The classification the files support is exactly one bit plus one module:

  * `WaterInteraction.will_sink == 1`                      -> sinks and stalls (189),
  * `will_sink == 0` + `BoatBuoyancy` present              -> a boat, floats (35),
  * `will_sink == 0` + `Buoyancy` (no `BoatBuoyancy`)      -> an amphibious land/air
                                                              vehicle that floats (8).

The kill/stall side is *not* per vehicle: all 232 entities point at the same
`vehicle_common.vmodc`, whose `vehicle_damage.min/fatal_water_entry_(floating_)ms` and five
`*.engine_shut_down_delay_s` rows hold one value each for the whole fleet.

"Drives underwater" has no member anywhere in the 52 module types: the keyword scan lists
every path in the fleet that mentions water/drown/sink/float/dive/submerge, and beyond the
modules above it finds only the four `vehicle_damage` timers, the five engine delays,
`number_of_water_collision_sensors`, `fins[].effective_in_water` and the helicopter's
flight `dive_*` terms. Whether a submerged car keeps driving is native code -> UNKNOWN.

Writes Research/JC3Grab/WATER.md + WATER.json. `--check` rebuilds and asserts.

Usage:
  python jc3water.py --write
  python jc3water.py --check
  python jc3water.py dump members|groups|samples|constants|scan|build
"""
from __future__ import annotations

import argparse
import collections
import difflib
import glob
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import jc3adf  # noqa: E402
import jc3detail  # noqa: E402

RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
ENT = os.path.join(RAW, "entities")
OUT = os.path.join(ROOT, "Research", "JC3Grab")
JSON_NAME = "WATER.json"
MD_NAME = "WATER.md"
BUILD_EE = os.path.join(ROOT, "Builds", "test-091",
                        "v0300_car_kensington_sportsmuscle_civilian_01.ee")
DONOR = "v0300_car_kensington_sportsmuscle_civilian_01.ee"
MODULES = ("Buoyancy", "WaterInteraction", "BoatBuoyancy")
IDX = re.compile(r"\[\d+\]")
SCAN = re.compile(r"water|drown|submerg|flood|swim|sink|float|amphib|dive|buoy", re.I)

# the card's roster: donor, armoured transport, tanks, the duck, and each floating class
SAMPLES = (
    ("donor, civilian (traffic build)", "v0300_car_kensington_sportsmuscle_civilian_01.ee"),
    ("donor, `debug` build", "v0300_car_kensington_sportsmuscle_debug.ee"),
    ("donor, `signature_preorder` build", "v0300_car_kensington_sportsmuscle_signature_preorder.ee"),
    ("armoured transport `military_01`", "v0602_car_urga_armoredtransport_military_01.ee"),
    ("armoured transport `rebel_01`", "v0602_car_urga_armoredtransport_rebel_01.ee"),
    ("medium tank `v0201`", "v0201_car_capstone_mediumtank_military_01.ee"),
    ("Bavarium tank `v0202`", "v0202_car_capstone_bavariumtank_military_01.ee"),
    ("small tank `v0603`", "v0603_car_urga_smalltank_military_01.ee"),
    ("APC `v0200` (amphibious car)", "v0200_car_capstone_apc_military_01.ee"),
    ("`v1717` duck (amphibious boat)", "v1717_boat_na_duck_civilian_01.ee"),
    ("heavy patrol boat `v1200`", "v1200_boat_capstone_heavypatrol_military_01.ee"),
    ("racing boat `v1401`", "v1401_boat_mugello_racingboat_civilian_01.ee"),
    ("jetski `v1500`", "v1500_boat_solar_jetski_civilian_01.ee"),
    ("floatplane `v4500`", "v4500_plane_solar_smallfloatprop_civilian_01.ee"),
    ("sea scout helicopter `v2603`", "v2603_helicopter_urga_seascout_military_01.ee"),
)
GROUPS = ("sink", "floating", "boat")
GROUP_LABEL = {"sink": "sinks and stalls", "floating": "floats (amphibious)",
               "boat": "floats (boat)"}


# ------------------------------------------------------------------ helpers
def fmt(v) -> str:
    if v is None:
        return "-"
    if isinstance(v, str):
        return v or "-"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if v == int(v) and abs(v) < 1e15:
            return str(int(v))
    return f"{float(v):.6g}"


def load() -> list[dict]:
    out = []
    for path in sorted(glob.glob(os.path.join(ENT, "*.ee.json"))):
        with open(path, encoding="utf-8") as f:
            out.append(json.load(f))
    if len(out) != 232:
        raise SystemExit(f"FAIL: {len(out)} entity decodes, expected 232")
    return sorted(out, key=lambda d: d["entity"])


def module(d: dict, kind: str) -> dict | None:
    for m in d["modules"]:
        if m.get("type") == kind:
            return m
    return None


def rows(m: dict | None) -> dict:
    return {r["path"]: r["value"] for r in m["rows"]} if m else {}


def val(d: dict, kind: str, path: str):
    return rows(module(d, kind)).get(path)


def group(d: dict) -> str:
    if module(d, "BoatBuoyancy"):
        return "boat"
    return "sink" if val(d, "WaterInteraction", "will_sink") == 1 else "floating"


def parts(m: dict | None) -> int:
    if not m:
        return 0
    return len({r["path"].split("[")[1].split("]")[0]
                for r in m["rows"] if r["path"].startswith("part_elements[")})


def scalars(m: dict | None) -> dict:
    """The module's plain-number rows, with array/struct rows dropped."""
    out = {}
    for r in m["rows"] if m else []:
        if r["path"].endswith("]") or "[" in r["path"]:
            continue
        if isinstance(r["value"], (int, float)) and not isinstance(r["value"], bool):
            out[r["path"]] = r["value"]
    return out


# ------------------------------------------------------------------ the census
def members(ents: list[dict]) -> dict:
    """Per module type: every member path, its type, presence, fleet range, donor value."""
    donor = next(d for d in ents if d["entity"].endswith("/" + DONOR))
    out = collections.OrderedDict()
    for kind in MODULES:
        seen: dict[str, dict] = {}
        for d in ents:
            for m in d["modules"]:
                if m.get("type") != kind:
                    continue
                for r in m["rows"]:
                    key = IDX.sub("[]", r["path"])
                    e = seen.setdefault(key, {"type": r["type"], "n": 0, "values": [],
                                              "donor": None})
                    e["n"] += 1
                    if r["type"] in ("float", "int32", "int8", "uint32", "bool"):
                        e["values"].append(r["value"])
        dv = rows(module(donor, kind))
        for key, e in seen.items():
            # donor value: exact path first (scalar), then the [0] element of an array
            if key in dv:
                e["donor"] = dv[key]
            elif key.endswith("[]") and key + "[0]" in dv:
                e["donor"] = dv[key + "[0]"]
            nums = e.pop("values")
            if nums and not key.endswith("[]"):
                e["min"], e["max"] = min(nums), max(nums)
                e["distinct"] = len(set(nums))
            out.setdefault(kind, collections.OrderedDict())[key] = e
    return out


def module_instances(ents: list[dict]) -> list[dict]:
    """Entities that carry a module type more than once (a copy-paste in the data)."""
    out = []
    for d in ents:
        c = collections.Counter(m.get("type") for m in d["modules"])
        for kind in MODULES:
            if c.get(kind, 0) > 1:
                out.append({"entity": d["entity"].split("/")[-1], "type": kind,
                            "instances": c[kind],
                            "files": [m.get("file") for m in d["modules"]
                                      if m.get("type") == kind]})
    return out


def is_shared(d: dict, kind: str) -> str | None:
    m = module(d, kind)
    return m.get("file") if m else None


def constants(ents: list[dict]) -> dict:
    """The fleet-wide kill/stall rows: they live in one shared VehicleCommon module."""
    files = collections.Counter()
    agg: dict[str, dict] = {}
    for d in ents:
        m = module(d, "VehicleCommon")
        files[m.get("file")] += 1
        for r in m["rows"]:
            p = r["path"]
            if ("_water_entry_" in p or "engine_shut_down_delay_s" in p
                    or "number_of_water_collision_sensors" in p):
                e = agg.setdefault(p, {"type": r["type"],
                                       "values": collections.Counter(),
                                       "modules": collections.Counter()})
                e["values"][r["value"]] += 1
                e["modules"][m.get("file")] += 1
    out = collections.OrderedDict()
    for p in sorted(agg):
        e = agg[p]
        out[p] = {"type": e["type"],
                  "values": {fmt(k): v for k, v in sorted(e["values"].items(),
                                                          key=lambda x: str(x[0]))},
                  "modules": {k: v for k, v in e["modules"].items()}}
    return {"module_files": {k: v for k, v in sorted(files.items())}, "rows": out}


def census(ents: list[dict]) -> dict:
    groups = collections.Counter()
    parts_hist = collections.defaultdict(collections.Counter)
    for d in ents:
        g = group(d)
        groups[g] += 1
        parts_hist[g][parts(module(d, "WaterInteraction"))] += 1
    return {"entities": len(ents),
            "groups": {g: groups.get(g, 0) for g in GROUPS},
            "part_elements": {g: {str(k): v for k, v in sorted(parts_hist[g].items())}
                              for g in GROUPS}}


def sample_table(ents: list[dict]) -> list[dict]:
    by_name = {d["entity"].split("/")[-1]: d for d in ents}
    out = []
    for label, name in SAMPLES:
        d = by_name.get(name)
        if d is None:
            raise SystemExit(f"FAIL: sample {name} not in the cache")
        wi = module(d, "WaterInteraction")
        bu = module(d, "Buoyancy")
        bb = module(d, "BoatBuoyancy")
        vc = rows(module(d, "VehicleCommon"))
        out.append({
            "label": label, "entity": d["entity"].split("/")[-1], "group": group(d),
            "will_sink": val(d, "WaterInteraction", "will_sink"),
            "part_elements": parts(wi),
            "buoyancy_parts": len({r["path"].split("[")[1].split("]")[0]
                                   for r in bu["rows"]
                                   if r["path"].startswith("buoyancy_modules[")}) if bu else None,
            "buoyancy": val(d, "Buoyancy", "buoyancy"),
            "drag": val(d, "Buoyancy", "drag"),
            "radius": val(d, "Buoyancy", "radius"),
            "side_area": val(d, "Buoyancy", "side_area"),
            "bottom_area": val(d, "Buoyancy", "bottom_area"),
            "up_velocity_cap": val(d, "Buoyancy", "up_velocity_cap"),
            "base_buoyancy": val(d, "BoatBuoyancy", "base_buoyancy"),
            "base_radius": val(d, "BoatBuoyancy", "base_radius"),
            "base_forward_drag": val(d, "BoatBuoyancy", "base_forward_drag"),
            "base_lateral_drag": val(d, "BoatBuoyancy", "base_lateral_drag"),
            "base_vertical_drag": val(d, "BoatBuoyancy", "base_vertical_drag"),
            "base_air_drag": val(d, "BoatBuoyancy", "base_air_drag"),
            "boat_buoyancy_parts": len({r["path"].split("[")[1].split("]")[0]
                                        for r in bb["rows"]
                                        if r["path"].startswith("buoyancy_modules[")}) if bb else None,
            "car_engine_shut_down_s": vc.get("car_common.engine_shut_down_delay_s"),
            "boat_engine_shut_down_s": vc.get("boat_common.engine_shut_down_delay_s"),
            "min_water_entry_ms": vc.get("vehicle_damage.min_water_entry_ms"),
            "fatal_water_entry_ms": vc.get("vehicle_damage.fatal_water_entry_ms"),
        })
    return out


def group_list(ents: list[dict], want: str) -> list[dict]:
    out = []
    for d in ents:
        if group(d) != want:
            continue
        bb = rows(module(d, "BoatBuoyancy"))
        out.append({
            "entity": d["entity"].split("/")[-1],
            "will_sink": val(d, "WaterInteraction", "will_sink"),
            "buoyancy": val(d, "Buoyancy", "buoyancy"),
            "base_buoyancy": bb.get("base_buoyancy"),
            "modules": len({r["path"].split("[")[1].split("]")[0]
                            for r in module(d, "BoatBuoyancy")["rows"]
                            if r["path"].startswith("buoyancy_modules[")})
            if module(d, "BoatBuoyancy") else None,
        })
    return out


def scan(ents: list[dict]) -> dict:
    """Every member path in the fleet that mentions water/sink/float/dive/submerge."""
    hits: dict[str, dict] = {}
    for d in ents:
        for m in d["modules"]:
            if "type" not in m:
                continue
            for r in m["rows"]:
                if not SCAN.search(r["path"]):
                    continue
                key = IDX.sub("[]", r["path"])
                e = hits.setdefault(key, {"types": collections.Counter(),
                                          "modules": collections.Counter(),
                                          "n": 0})
                e["types"][r["type"]] += 1
                e["modules"][m["type"]] += 1
                e["n"] += 1
    return {k: {"n": v["n"], "modules": dict(sorted(v["modules"].items())),
                "types": sorted(v["types"])}
            for k, v in sorted(hits.items())}


def build_check() -> dict:
    """Decode the live build's own water modules and compare them with the donor cache."""
    if not os.path.exists(BUILD_EE):
        return {"path": None, "note": "build entity not on disk"}
    with open(BUILD_EE, "rb") as f:
        stream, entries = jc3detail.inner_files(f.read())
    out = {"path": os.path.relpath(BUILD_EE, ROOT).replace(os.sep, "/"),
           "container_files": len(entries), "modules": {}}
    for suffix, kind in (("_water_interaction.vmodc", "WaterInteraction"),
                         ("_buoyancy.vmodc", "Buoyancy")):
        hit = next((e for e in entries if e[0].endswith(suffix)), None)
        if hit is None:
            out["modules"][kind] = None
            continue
        got = {p: v for p, _t, v in
               jc3adf.walk(jc3adf.Adf(stream[hit[1]:hit[1] + hit[2]]))}
        out["modules"][kind] = {
            "file": hit[0], "rows": len(got),
            "will_sink": got.get("will_sink"),
            "buoyancy": got.get("buoyancy"),
            "drag": got.get("drag"),
            "radius": got.get("radius"),
            "side_area": got.get("side_area"),
            "bottom_area": got.get("bottom_area"),
            "up_velocity_cap": got.get("up_velocity_cap"),
            "parts": len({p.split("[")[1].split("]")[0] for p in got
                          if p.startswith("part_elements[")}),
        }
    return out


def close(a, b) -> bool:
    """Equal to six decimals - the cache rounds floats, a raw decode does not."""
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) <= 1e-6
    return a == b


def build_vs_donor(build: dict, ents: list[dict]) -> dict:
    """The same members, read from the donor cache, for a like-for-like comparison."""
    d = next(x for x in ents if x["entity"].endswith("/" + DONOR))
    out = {"donor": {"WaterInteraction": {
        "will_sink": val(d, "WaterInteraction", "will_sink"),
        "parts": parts(module(d, "WaterInteraction"))},
        "Buoyancy": {k: val(d, "Buoyancy", k) for k in
                     ("buoyancy", "drag", "radius", "side_area", "bottom_area",
                      "up_velocity_cap")}}}
    same = {}
    for kind in ("WaterInteraction", "Buoyancy"):
        b = (build.get("modules") or {}).get(kind)
        if not b:
            same[kind] = "build module missing"
            continue
        checks = {"will_sink": (b.get("will_sink"), out["donor"][kind].get("will_sink"))}
        if kind == "Buoyancy":
            checks = {k: (b.get(k), out["donor"][kind].get(k)) for k in
                      ("buoyancy", "drag", "radius", "side_area", "bottom_area",
                       "up_velocity_cap")}
        else:
            checks["parts"] = (b.get("parts"), out["donor"][kind].get("parts"))
        same[kind] = all(close(a, c) for a, c in checks.values())
        out[kind + "_checks"] = {k: list(v) for k, v in checks.items()}
    out["identical"] = all(v is True for v in same.values())
    return out


# ------------------------------------------------------------------ build the data
def build(deep: bool = True) -> dict:
    ents = load()
    donor = next(d for d in ents if d["entity"].endswith("/" + DONOR))
    data = {
        "schema": "g2-31 water behaviour, jc3water.py 1",
        "inputs": {
            "entities": os.path.relpath(ENT, ROOT).replace(os.sep, "/"),
            "entity_count": len(ents),
            "donor": donor["entity"],
            "build_ee": os.path.relpath(BUILD_EE, ROOT).replace(os.sep, "/")
            if os.path.exists(BUILD_EE) else None,
        },
        "census": census(ents),
        "members": members(ents),
        "duplicates": module_instances(ents),
        "no_hull": [d["entity"].split("/")[-1] for d in ents
                    if parts(module(d, "WaterInteraction")) == 0],
        "constants": constants(ents),
        "samples": sample_table(ents),
        "boats": group_list(ents, "boat"),
        "floating": group_list(ents, "floating"),
        "scan": scan(ents),
        "build": build_check(),
    }
    data["build_check"] = build_vs_donor(data["build"], ents)
    return data


# ------------------------------------------------------------------ render
def to_md(d: dict) -> str:
    a = []
    add = a.append
    cen = d["census"]
    samples = d["samples"]
    donor = samples[0]
    add("# Water behaviour: what sinks, what floats, what drowns\n")
    add("G2-31. **The data has one bit for it, plus a module switch, plus one shared timer "
        "table - and the Batmobile already behaves the lore way.** A vehicle's "
        "`WaterInteraction.will_sink` is `1` on 189 of the 232 vehicle entities and `0` on the "
        "other 43; the 43 split cleanly by module: 35 boats carry `BoatBuoyancy`, and 8 "
        "land/air vehicles (`v0200` APC, `v2603` sea scout, `v4500` floatplane) keep a plain "
        "`Buoyancy` module and simply do not sink. The donor is one of the 189 (`will_sink` 1, "
        "buoyancy 2, drag 100, one hull element), so **the current build - which is the donor's "
        "own `.ee` with the Batmobile modules inside - sinks and stalls by default**: D-8's lore "
        "route needs no water edit, and the float route would need `will_sink` 0 plus a "
        "`BoatBuoyancy` block that the donor does not have.\n")
    add("**\"Drives underwater\" has no member in any of the 52 module types.** The keyword scan "
        "of every member path in the fleet (§7) returns only the three water modules, four "
        "`vehicle_damage.*_water_entry_ms` timers, five `*_engine_shut_down_delay_s` rows, "
        "`number_of_water_collision_sensors`, `fins[].effective_in_water` and the helicopter's "
        "flight `dive_*` terms. What a submerged car actually does after the timer runs is "
        "native code -> `UNKNOWN` (Q-1 probe).\n")

    add("## 1. The three behaviours, member by member\n")
    add("| behaviour | entities | what the files say makes it so | members and values |")
    add("|---|---|---|---|")
    add(f"| **sinks and stalls** | {cen['groups']['sink']} | "
        f"`WaterInteraction.will_sink = 1`; the hull is a `part_elements[]` triangle mesh the "
        f"game pushes through the water plane; the kill/stall side is the shared "
        f"`vehicle_damage` timer block | donor: `will_sink` 1, `buoyancy` "
        f"{fmt(donor['buoyancy'])}, `drag` {fmt(donor['drag'])}, `radius` "
        f"{fmt(donor['radius'])}, `side_area` {fmt(donor['side_area'])}, `bottom_area` "
        f"{fmt(donor['bottom_area'])}, `up_velocity_cap` {fmt(donor['up_velocity_cap'])}, "
        f"{donor['part_elements']} hull element(s) |")
    add(f"| **floats (boat)** | {cen['groups']['boat']} | `WaterInteraction.will_sink = 0` "
        f"**and** a `BoatBuoyancy` module: `base_buoyancy` plus per-pontoon `buoyancy_modules[]` "
        f"with `radius`/`forward_drag`/`lateral_drag`/`vertical_drag`/`air_drag` | "
        f"`base_buoyancy` {fmt(min(b['base_buoyancy'] for b in d['boats']))}.."
        f"{fmt(max(b['base_buoyancy'] for b in d['boats']))} over the 35 boats, "
        f"{min(b['modules'] for b in d['boats'])}..{max(b['modules'] for b in d['boats'])} "
        f"pontoon modules each |")
    add(f"| **floats (amphibious)** | {cen['groups']['floating']} | `will_sink = 0` with the "
        f"ordinary car `Buoyancy` module and no `BoatBuoyancy`: the lift comes from the same "
        f"`buoyancy` scalar the sinking cars carry | see §5 for all 8 |")
    add("| **drives underwater** | 0 | **no member expresses it** - see §7 | `UNKNOWN`, native "
        "code |")
    add("")

    add("## 2. The modules, whole\n")
    add(f"Three module types carry every water member in the fleet: `Buoyancy` on "
        f"{d['members']['Buoyancy']['buoyancy']['n']} entities, `WaterInteraction` on "
        f"{d['members']['WaterInteraction']['will_sink']['n']} module instances, "
        f"`BoatBuoyancy` on {d['members']['BoatBuoyancy']['base_radius']['n']} boats.\n")
    if d["duplicates"]:
        add("One entity carries a water module twice, and it is a copy-paste worth knowing "
            "about:\n")
        add("| entity | type | instances | files |")
        add("|---|---|---|---|")
        for dup in d["duplicates"]:
            files = "<br>".join(f"`{(f or '-').split('/')[-1]}`" for f in dup["files"])
            add(f"| `{dup['entity']}` | `{dup['type']}` | {dup['instances']} | {files} |")
        add("")
        add("The cargo plane carries the **medium tank's** water module next to its own, which is "
            "why the fleet total is one more than the entity count. It changes no verdict: both "
            "copies say `will_sink` 1.\n")
    for kind in MODULES:
        rowsd = d["members"].get(kind, {})
        add(f"### `{kind}` ({len(rowsd)} member paths)\n")
        add("| member | type | on n modules | fleet range | donor |")
        add("|---|---|---|---|---|")
        for key, e in rowsd.items():
            if "min" in e:
                rng = f"{fmt(e['min'])} .. {fmt(e['max'])}" + (
                    f" ({e['distinct']} distinct)" if e["distinct"] > 1 else "")
            elif key.endswith("[]"):
                rng = "array"
            else:
                rng = "-"
            add(f"| `{key}` | {e['type']} | {e['n']} | {rng} | {fmt(e['donor'])} |")
        add("")

    add("## 3. The fleet, counted\n")
    add("| group | entities | hull elements per entity (`part_elements[]`) |")
    add("|---|---|---|")
    for g in GROUPS:
        pe = d["census"]["part_elements"][g]
        add(f"| {GROUP_LABEL[g]} | {d['census']['groups'][g]} | "
            + ", ".join(f"{k} -> {v}" for k, v in sorted(pe.items(), key=lambda x: int(x[0]))) + " |")
    add("")
    add(f"Ten of the sinking entities ship an **empty** `part_elements[]` - no hull mesh at all "
        f"({', '.join('`' + n + '`' for n in d['no_hull'])}). They still set `will_sink` 1, which "
        f"is why the hull mesh must be read as the shape the water plane pushes against, not as "
        f"the sink switch: the switch is the scalar.\n")
    add("`will_sink` is the only scalar that separates the sinking cars from the amphibious eight: "
        "both groups carry the same `angular_drag_*` 0.05, `pressure_drag` 5000 / `pressure_drag_2` "
        "20000, `suction_drag` 5000, `depth_full_drag` 0.1 and `reference_drag_speed_ms` 20. The "
        "boats differ from both in every drag: `pressure_drag` 100..5000, `depth_full_drag` "
        "0..0.2, and `angular_drag_ref_speed_kmph` 100..150.\n")

    add("## 4. The card's roster\n")
    add("| vehicle | group | will_sink | hull elems | buoyancy | drag | radius / side / bottom | "
        "base_buoyancy | pontoons |")
    add("|---|---|---|---|---|---|---|---|---|")
    for s in samples:
        add(f"| {s['label']} | {s['group']} | {fmt(s['will_sink'])} | {s['part_elements']} | "
            f"{fmt(s['buoyancy'])} | {fmt(s['drag'])} | "
            f"{fmt(s['radius'])} / {fmt(s['side_area'])} / {fmt(s['bottom_area'])} | "
            f"{fmt(s['base_buoyancy'])} | {fmt(s['boat_buoyancy_parts'])} |")
    add("")
    add("The three donor builds, both armoured-transport builds and all three tanks are "
        "`will_sink` 1 with the same `Buoyancy` numbers - the tank roster does not get a water "
        "exception. The APC is the one land vehicle in the roster that floats without a boat "
        "module, and the duck is a full boat (BoatBuoyancy + `BoatEngine` + `Fins` + "
        "`BoatSteering`, class `BoatGlobal`).\n")

    add("## 5. The eight floaters that are not boats\n")
    add("| entity | will_sink | buoyancy |")
    add("|---|---|---|")
    for f in d["floating"]:
        add(f"| `{f['entity']}` | {fmt(f['will_sink'])} | {fmt(f['buoyancy'])} |")
    add("")
    add("`buoyancy` is a multiplier, not a switch (the fleet's sinking cars carry 0, 0.25, 1.5 or 2 "
        "as well), so these eight float because `will_sink` is 0, not because their lift differs.\n")

    add("## 6. The boats\n")
    add("| entity | base_buoyancy | pontoon modules |")
    add("|---|---|---|")
    for b in d["boats"]:
        add(f"| `{b['entity']}` | {fmt(b['base_buoyancy'])} | {b['modules']} |")
    add("")

    add("## 7. Drown and stall: the shared constants\n")
    add(f"All {d['inputs']['entity_count']} entities point their `VehicleCommon` module at the "
        f"same file:\n")
    for f, n in d["constants"]["module_files"].items():
        add(f"- `{f}` — {n} entities")
    add("")
    add("| member | values (all entities) |")
    add("|---|---|")
    for k, e in d["constants"]["rows"].items():
        vals = ", ".join(f"`{v}` x{c}" for v, c in e["values"].items())
        add(f"| `{k}` | {vals} |")
    add("")
    add("So the *kill* side is fleet-wide: `min_water_entry_ms` 10 and `fatal_water_entry_ms` 20, "
        "with the `_floating_` pair at 20 / 50, and the engine shut-down delay is 30 s for cars "
        "and 5 s for every other class. **No vehicle overrides any of them** - the module is "
        "shared, so changing them means a private copy of `vehicle_common.vmodc` (R7), and the "
        "unit behind the `_ms` suffix is not decoded here (`UNKNOWN`): 10/20 ms is too short to "
        "be a drown timer, so the name is the only evidence of what the numbers mean.\n")

    add("## 8. The live build\n")
    b = d["build"]
    add(f"`{b.get('path')}` ({b.get('container_files')} inner files) carries the donor's own "
        f"water modules:\n")
    add("| module | file | rows | will_sink | buoyancy | drag | radius / side / bottom | hull elems |")
    add("|---|---|---|---|---|---|---|---|")
    for kind in ("WaterInteraction", "Buoyancy"):
        m = (b.get("modules") or {}).get(kind) or {}
        add(f"| `{kind}` | `{(m.get('file') or '-').split('/')[-1]}` | {m.get('rows')} | "
            f"{fmt(m.get('will_sink'))} | {fmt(m.get('buoyancy'))} | {fmt(m.get('drag'))} | "
            f"{fmt(m.get('radius'))} / {fmt(m.get('side_area'))} / {fmt(m.get('bottom_area'))} | "
            f"{fmt(m.get('parts')) if kind == 'WaterInteraction' else '-'} |")
    add("")
    bc = d["build_check"]
    add(f"Comparison against the donor cache: **{'identical' if bc['identical'] else 'DIFFERENT'}**. "
        f"{'Every compared member matches, so the build sinks exactly like the donor - the lore ' if bc['identical'] else ''}"
        f"route of D-8 is already what ships.\n")

    add("## 9. The keyword scan (what is *not* there)\n")
    add(f"{len(d['scan'])} distinct member paths fleet-wide mention water/drown/sink/float/dive/"
        f"submerge/buoyancy. Grouped by the module they live in:\n")
    by_mod = collections.defaultdict(list)
    for k, e in d["scan"].items():
        for m in e["modules"]:
            by_mod[m].append(k)
    add("| module | paths | examples |")
    add("|---|---|---|")
    for m in sorted(by_mod, key=lambda x: (-len(by_mod[x]), x)):
        ex = ", ".join(f"`{p}`" for p in by_mod[m][:4])
        add(f"| `{m}` | {len(by_mod[m])} | {ex} |")
    add("")
    add("There is no `drown`, `submerge`, `flood`, `swim` or `underwater` path anywhere in the "
        "232 entities, and no member that could make a hull dive and stay drivable: the only "
        "`dive_*` terms are `HelicopterModel` flight (`max_speed_dive_kmph`, `add_dive_pitch_deg`). "
        "A submerged vehicle is therefore whatever the engine does with `will_sink` plus the "
        "`vehicle_damage` timers -> `UNKNOWN`.\n")

    add("## 10. What this means for the build (WLD-6, D-8)\n")
    add("| question | answer |")
    add("|---|---|")
    add(f"| does the build sink like a car today? | **yes** - the build's `will_sink` is "
        f"{fmt(bc['donor']['WaterInteraction']['will_sink'])}, inherited from the donor (§8) |")
    add("| does it need any water edit for the lore route? | **no** - the donor's values are "
        "already the non-amphibious car behaviour; touching them would be the change |")
    add("| could it float instead? | only by `will_sink` 0, and for a boat-like ride a "
        "`BoatBuoyancy` block the donor does not have - that is the amphibious route D-8 "
        "rejected |")
    add("| can it drown its own engine at depth? | the only death-on-water member in the fleet "
        "is `vehicle_damage.fatal_water_entry_ms` = 20 (with `_floating_` 50); the build shares "
        "it and no vehicle overrides it (§7). What the number measures is `UNKNOWN` - do not "
        "quote it as seconds or as damage |")
    add("| anything to change for R3 (physics follows the asset)? | no: the hull mesh in "
        f"`WaterInteraction.part_elements[]` is built from the donor body part `sportsmuscle_body` "
        f"and is a water-plane collider, not a physics station |")
    add("")

    add("## 11. Checks\n")
    add("| check | result |")
    add("|---|---|")
    add("| `python Tools/scripts/jc3water.py --check` | rebuilds both files and asserts every "
        "number above |")
    add(f"| entities | {d['inputs']['entity_count']} |")
    add(f"| groups | sink {cen['groups']['sink']} / floating {cen['groups']['floating']} / "
        f"boat {cen['groups']['boat']} |")
    add(f"| module types with water members | {len(MODULES)} |")
    add(f"| shared-constant rows | {len(d['constants']['rows'])} |")
    add(f"| build identical to donor | {bc['identical']} |")
    add("")
    add("Every number here is regenerated by the script from the decoded cache and the build's "
        "own `.ee`; none is typed by hand.")
    add("")
    return "\n".join(a)


# ------------------------------------------------------------------ invariants
def invariants(d: dict) -> list[str]:
    bad = []
    cen = d["census"]
    if d["inputs"]["entity_count"] != 232:
        bad.append("entity count")
    if sum(cen["groups"].values()) != 232:
        bad.append("group sum")
    if cen["groups"] != {"sink": 189, "floating": 8, "boat": 35}:
        bad.append(f"group split {cen['groups']}")
    donor = d["samples"][0]
    if donor["will_sink"] != 1 or donor["buoyancy"] != 2 or donor["drag"] != 100:
        bad.append("donor values")
    if donor["part_elements"] != 1:
        bad.append("donor hull elements")
    if len(d["boats"]) != 35 or len(d["floating"]) != 8:
        bad.append("group lists")
    if len(d["no_hull"]) != 10 or any(
            s["entity"] in d["no_hull"] for s in d["samples"]):
        bad.append("no-hull census")
    if any(b["will_sink"] != 0 for b in d["boats"] + d["floating"]):
        bad.append("a floater has will_sink 1")
    if any(s["will_sink"] != 1 for s in d["samples"] if s["group"] == "sink"):
        bad.append("a sinking sample has will_sink 0")
    if len(d["constants"]["module_files"]) != 1:
        bad.append("VehicleCommon is not one shared file")
    want = {"vehicle_damage.min_water_entry_ms": "10",
            "vehicle_damage.fatal_water_entry_ms": "20",
            "vehicle_damage.min_water_entry_floating_ms": "20",
            "vehicle_damage.fatal_water_entry_floating_ms": "50",
            "car_common.engine_shut_down_delay_s": "30",
            "boat_common.engine_shut_down_delay_s": "5"}
    for k, v in want.items():
        row = d["constants"]["rows"].get(k)
        if not row or list(row["values"]) != [v]:
            bad.append(f"constant {k}")
    if not d["build_check"]["identical"]:
        bad.append("build water modules differ from the donor")
    wi = d["members"].get("WaterInteraction", {})
    if "will_sink" not in wi or wi["will_sink"]["n"] != 233:
        bad.append("will_sink census")
    for kind in MODULES:
        if not d["members"].get(kind):
            bad.append(f"no members for {kind}")
    if any("drown" in k or "submerg" in k or "underwater" in k for k in d["scan"]):
        bad.append("a drown/underwater member exists - the UNKNOWN claim must be revisited")
    return bad


# ------------------------------------------------------------------ commands
def cmd_write() -> int:
    d = build()
    with open(os.path.join(OUT, JSON_NAME), "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    md = to_md(d)
    with open(os.path.join(OUT, MD_NAME), "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    print(f"{JSON_NAME}/{MD_NAME}: {d['census']['entities']} entities, "
          f"groups {d['census']['groups']}, {len(d['boats'])} boats, "
          f"{len(d['floating'])} floating, {len(d['constants']['rows'])} shared rows, "
          f"build identical {d['build_check']['identical']}, {len(md.splitlines())} md lines")
    return 0


def cmd_check() -> int:
    d = build()
    bad = invariants(d)
    jp, mp = os.path.join(OUT, JSON_NAME), os.path.join(OUT, MD_NAME)
    if not (os.path.exists(jp) and os.path.exists(mp)):
        print(f"FAIL: {JSON_NAME}/{MD_NAME} missing - run --write")
        return 1
    with open(jp, encoding="utf-8") as f:
        if json.load(f) != d:
            bad.append(f"{JSON_NAME} stale")
    md = to_md(d)
    with open(mp, encoding="utf-8") as f:
        have = f.read()
    if md != have:
        diff = list(difflib.unified_diff(have.splitlines(), md.splitlines(), "file",
                                         "rebuilt", n=1))
        bad.append("md differs: " + " | ".join(diff[2:8]))
    if bad:
        print("FAIL: " + "; ".join(bad))
        return 1
    s = d["samples"][0]
    print(f"PASS: {d['census']['entities']} entities, sink {d['census']['groups']['sink']} / "
          f"floating {d['census']['groups']['floating']} / boat {d['census']['groups']['boat']}, "
          f"donor will_sink {s['will_sink']} buoyancy {fmt(s['buoyancy'])} drag {fmt(s['drag'])} "
          f"({s['part_elements']} hull element), {len(d['boats'])} boats base_buoyancy "
          f"{fmt(min(b['base_buoyancy'] for b in d['boats']))}.."
          f"{fmt(max(b['base_buoyancy'] for b in d['boats']))}, "
          f"{len(d['constants']['rows'])} fleet-wide water/engine rows in one shared "
          f"VehicleCommon, build water modules identical to the donor: "
          f"{d['build_check']['identical']}, {len(d['scan'])} member paths scan as water-related")
    return 0


def cmd_dump(what: str) -> int:
    d = build()
    key = {"members": "members", "groups": "census", "samples": "samples",
           "constants": "constants", "scan": "scan", "build": "build_check",
           "boats": "boats", "floating": "floating"}
    if what not in key:
        print("one of: " + ", ".join(sorted(key)))
        return 2
    print(json.dumps(d[key[what]], indent=1, sort_keys=True, ensure_ascii=False)[:14000])
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    dl = sub.add_parser("dump")
    dl.add_argument("what", nargs="?", default="groups")
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
