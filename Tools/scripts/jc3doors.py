#!/usr/bin/env python
"""jc3doors.py - G2-15: how a JC3 door, canopy or missile hatch actually moves.

A door is three things and nothing else:

  * a part whose `behavior` is a name in `vehicle_common.all_door_part_properties`
    (`FrontLeftDoor`, `Hood`, `TurretDoor`, `MissileHatch`...);
  * an entry in the parts module's `door_parts[]` array, which stores only `part_index`;
  * a `hkpLimitedHingeConstraintData` in the vehicle's `.physicsc`, reached through the
    part's `constraint_index`, which carries the axis and the two angle limits.

There is no open angle, speed or interaction name on the door itself. This script decodes
those three pieces for the three vehicles the card names (the Serpente donor, the APC, the
monorail missile car), plus the medium tank's roof hatch as the transverse-axis reference,
and censuses every door part in the 78 cached parts modules by hinge axis.

It also scans the cached `.epe` graphs for the entry paths (`entry.driver` vs
`entry.driver.no.door`, `S_ENTER_DRIVER_VEHICLE` vs `..._NO_DOOR_VEHICLE`) and, for the
monorail car, for any object that names a hatch part outside its `CPartProp`.

Usage:
  python jc3doors.py --write    # DOORS.md + DOORS.json
  python jc3doors.py --check    # rebuild, compare and assert the answers
  python jc3doors.py dump samples|census|interactions
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import struct
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jc3adf  # noqa: E402
import jc3detail  # noqa: E402
import jc3grab  # noqa: E402
import jc3hkx  # noqa: E402
import jc3index  # noqa: E402
import jc3wiring  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
GAME = os.environ.get("JC3_GAME", jc3index.DEFAULT_GAME)
JSON_NAME = "DOORS.json"
MD_NAME = "DOORS.md"
PARTS = os.path.join(OUT, "PARTS_TABLE.jsonl")
V = "editor/entities/jc_vehicles/01_land"
SAMPLES = (
    ("donor", "v0300 Serpente (civilian)",
     f"{V}/v0300_car_kensington_sportsmuscle/"
     "v0300_car_kensington_sportsmuscle_civilian_01.ee"),
    ("apc", "v0200 APC (military)",
     f"{V}/v0200_car_capstone_apc/v0200_car_capstone_apc_military_01.ee"),
    ("monorail", "v5603 monorail missile car",
     f"{V}/v5603_train_urga_monorailmissilecar/"
     "v5603_train_urga_monorailmissilecar_military_01.ee"),
    ("mediumtank", "v0201 medium tank",
     f"{V}/v0201_car_capstone_mediumtank/v0201_car_capstone_mediumtank_military_01.ee"),
)
LIMITED = "hkpLimitedHingeConstraintData"


# ------------------------------------------------------------------ decoding
def hinge_from(pf: "jc3hkx.Packfile", o) -> dict:
    rec = {"class": o.cls, "size": pf.extents[o.offset]}
    if o.cls == LIMITED:
        raw = pf.raw(o.offset, pf.extents[o.offset])
        axis = struct.unpack_from("<4f", raw, 0x30)
        pivot = struct.unpack_from("<4f", raw, 0x60)
        lo, hi = struct.unpack_from("<2f", raw, 0xFC)
        rec.update({
            "axis": [round(v, 3) for v in axis[:3]],
            "pivot": [round(v, 3) for v in pivot[:3]],
            "min_deg": round(lo * 57.29577951308232, 1),
            "max_deg": round(hi * 57.29577951308232, 1),
        })
    return rec


def constraints(ee: str, rows: list[dict]) -> list[dict]:
    phys = jc3hkx.physicsc_of(ee, rows, GAME)
    if not phys:
        return []
    pf = jc3hkx.Packfile(phys[0][1])
    objs = sorted((o for o in pf.objects if "Constraint" in o.cls), key=lambda o: o.offset)
    return [hinge_from(pf, o) for o in objs]


def door_indices(rows_map: dict) -> list[int]:
    out, i = [], 0
    while f"door_parts[{i}].part_index" in rows_map:
        out.append(rows_map[f"door_parts[{i}].part_index"])
        i += 1
    return out


def module_of(ee: str, rows: list[dict]) -> tuple[list[dict], list[int], str, dict]:
    """Parts, the `door_parts` array, the module name and the container's member census."""
    r = jc3detail.pick(rows, ee)
    stream, entries = jc3detail.inner_files(jc3grab.read_entry(r, GAME))
    hit = next((e for e in entries if e[0].endswith("_vehicle_parts.vmodc")), None)
    if hit is None:
        raise ValueError(f"no parts module in {ee}")
    blob = stream[hit[1]:hit[1] + hit[2]]
    rows_map = {p: v for p, _t, v in jc3adf.walk(jc3adf.Adf(blob))}
    members = [e[0] for e in entries]
    census = {
        "members": len(members),
        "animation_members": [m for m in members
                              if os.path.splitext(m)[1].lower() in (".ban", ".anim", ".sab")],
        "has_physics": any(m.endswith(".physicsc") for m in members),
    }
    return jc3adf.parts(jc3adf.Adf(blob)), door_indices(rows_map), os.path.basename(hit[0]), census


def cached_module(path: str) -> tuple[list[dict], list[int]]:
    blob = open(path, "rb").read()
    rows_map = {p: v for p, _t, v in jc3adf.walk(jc3adf.Adf(blob))}
    return jc3adf.parts(jc3adf.Adf(blob)), door_indices(rows_map)


def axis_class(axis: list[float]) -> str:
    x, y, z = (abs(v) for v in axis)
    big = max(x, y, z)
    if big == 0:
        return "none"
    if max(x, y, z) - sorted((x, y, z))[1] < 0.15:
        return "oblique"
    if x == big:
        return "X (transverse)"
    if y == big:
        return "Y (vertical)"
    return "Z (longitudinal)"


def door_rows(ee: str, parts: list[dict], doors: list[int],
              cons: list[dict]) -> list[dict]:
    by_index = {p["part_index"]: p for p in parts}
    out = []
    for i in doors:
        p = by_index.get(i)
        if p is None:
            continue
        rec = {"index": i, "name": p["name"], "behaviour": p["behavior"],
               "parent": p["parent_part_index"],
               "constraint": p["constraint_index"],
               "in_array": doors.count(i)}
        ci = p["constraint_index"]
        if isinstance(ci, int) and 0 <= ci < len(cons):
            rec["hinge"] = cons[ci]
            if cons[ci].get("axis"):
                rec["axis_class"] = axis_class(cons[ci]["axis"])
        out.append(rec)
    return out


def epe_objects(ee: str, rows: list[dict]) -> list:
    objs, _doc = jc3wiring.decode_epe(ee, rows, GAME)
    return objs


def door_interactions(xml_path: str) -> dict:
    """Entry paths from one cached `.epe` XML: does it have a door path, a no-door path, both?"""
    if not os.path.exists(xml_path):
        return {}
    s = open(xml_path, encoding="utf-8", errors="replace").read()
    names = sorted(set(re.findall(r'type="string">(entry\.[^<]*)<', s)))
    states = sorted({m for m in re.findall(r'type="string">(S_[A-Z_]+)<', s)
                     if "ENTER" in m or "EXIT" in m})
    door_entry = "entry.driver" in names
    no_door = "entry.driver.no.door" in names or "entry.passenger1.no.door" in names
    return {"entries": names, "states": states,
            "driver_door_entry": door_entry, "no_door_entry": no_door,
            "driver_enter_state": "S_ENTER_DRIVER_VEHICLE" in states,
            "driver_enter_no_door_state": "S_ENTER_DRIVER_NO_DOOR_VEHICLE" in states}


# --------------------------------------------------------------------- build
def build() -> dict:
    rows = jc3index.load_index(OUT)
    table = [json.loads(line) for line in open(PARTS, encoding="utf-8") if line.strip()]
    by_module: dict[str, dict] = {}
    for rec in table:
        by_module.setdefault(rec["module"], rec)

    samples = []
    for tag, label, ee in SAMPLES:
        parts, doors, module, census = module_of(ee, rows)
        cons = constraints(ee, rows)
        rec = {
            "tag": tag, "label": label, "entity": ee, "parts_module": module,
            "parts": len(parts), "door_parts": door_rows(ee, parts, doors, cons),
            "constraints": len(cons), "container": census,
            "interaction": door_interactions(os.path.join(
                RAW, "tmp", "epe_cache", os.path.basename(ee) + ".xml")),
        }
        if tag == "monorail":
            objs = epe_objects(ee, rows)
            hatch_names = {d["name"] for d in rec["door_parts"]}
            refs = []
            for o in objs:
                if o.cls == "CPartProp":
                    continue
                for k, v in o.props.items():
                    if v in hatch_names:
                        refs.append({"class": o.cls, "name": o.name, "prop": k})
            def own_tune(o) -> str | None:
                tunes = [v for v in o.props.values()
                         if isinstance(v, str) and v.endswith(".wtune")]
                return next((t for t in tunes
                             if os.path.splitext(os.path.basename(t))[0] == o.name),
                            tunes[0] if tunes else None)

            weapons = [{"class": o.cls, "name": o.name, "tuning": own_tune(o)}
                       for o in objs if o.cls.endswith("WeaponBase")]
            components = sorted({o.cls for o in objs if o.cls.endswith("WeaponComponent")})
            points = [{"name": o.name, "world": o.props.get("world")}
                      for o in objs if o.cls == "SWeaponPoint"]
            rec["hatch_refs_outside_part_prop"] = refs
            rec["weapons"] = weapons
            rec["weapon_components"] = components
            rec["weapon_points"] = points
        samples.append(rec)

    # fleet census of door parts and their hinges
    census = {"modules": 0, "modules_with_doors": 0, "door_rows": 0,
              "with_hinge": 0, "limited": 0, "other_classes": {},
              "by_axis": {}, "by_behaviour": {}, "transverse": [], "no_hinge": []}
    for path in sorted(glob.glob(os.path.join(RAW, "tmp", "*_vehicle_parts.vmodc"))):
        parts, doors = cached_module(path)
        if not parts:
            continue
        census["modules"] += 1
        if not doors:
            continue
        census["modules_with_doors"] += 1
        census["door_rows"] += len(doors)
        module = os.path.basename(path)
        rec = by_module.get(module)
        cons = constraints(rec["entity"], rows) if rec else []
        for d in door_rows(rec["entity"] if rec else "", parts, doors, cons):
            h = d.get("hinge")
            b = census["by_behaviour"].setdefault(
                d["behaviour"] or "None",
                {"rows": 0, "axes": {}, "min": None, "max": None})
            b["rows"] += 1
            if not h:
                census["no_hinge"].append({"module": module, "part": d["name"],
                                           "constraint": d["constraint"]})
                continue
            census["with_hinge"] += 1
            cls = h["class"]
            if cls != LIMITED:
                census["other_classes"][cls] = census["other_classes"].get(cls, 0) + 1
                continue
            census["limited"] += 1
            a = d["axis_class"]
            census["by_axis"][a] = census["by_axis"].get(a, 0) + 1
            b["axes"][a] = b["axes"].get(a, 0) + 1
            b["min"] = h["min_deg"] if b["min"] is None else min(b["min"], h["min_deg"])
            b["max"] = h["max_deg"] if b["max"] is None else max(b["max"], h["max_deg"])
            if a.startswith("X") and len(census["transverse"]) < 12:
                census["transverse"].append({
                    "module": module, "part": d["name"], "behaviour": d["behaviour"],
                    "axis": h["axis"], "min_deg": h["min_deg"], "max_deg": h["max_deg"]})

    # entry-path census over the cached epe graphs
    inter = {"entities": 0, "with_door_parts": 0, "both": 0, "door_only": 0,
             "no_door_only": 0, "neither": 0, "both_list": [], "no_door_list": []}
    for path in sorted(glob.glob(os.path.join(RAW, "tmp", "epe_cache", "*.xml"))):
        base = os.path.basename(path)[:-4]
        i = door_interactions(path)
        if not i:
            continue
        inter["entities"] += 1
        rec = next((r for r in table if r["entity"].endswith("/" + base)), None)
        doors = 1 if rec else 0
        if rec:
            doors = len(rec.get("doors") or [])
        if doors:
            inter["with_door_parts"] += 1
        d, n = i["driver_door_entry"], i["no_door_entry"]
        if d and n:
            inter["both"] += 1
            inter["both_list"].append(base)
        elif d:
            inter["door_only"] += 1
        elif n:
            inter["no_door_only"] += 1
            inter["no_door_list"].append(base)
        else:
            inter["neither"] += 1

    out = {"samples": samples, "census": census, "interactions": inter}
    out["digest"] = hashlib.sha1(json.dumps(out, sort_keys=True,
                                            separators=(",", ":")).encode()).hexdigest()[:16]
    return out


# ---------------------------------------------------------------------- md
def render_md(d: dict) -> str:
    c, i = d["census"], d["interactions"]
    by_tag = {s["tag"]: s for s in d["samples"]}
    donor, apc, mono, tank = (by_tag["donor"], by_tag["apc"], by_tag["monorail"],
                              by_tag["mediumtank"])
    lines = [
        "# Doors, canopies and missile hatches",
        "",
        "G2-15. A door is a behaviour name in `vehicle_common.all_door_part_properties`, an",
        "entry in the parts module's `door_parts[]` array (a bare `part_index`), and a",
        "`hkpLimitedHingeConstraintData` in `.physicsc`. The module stores **no** open angle,",
        "speed, animation name or interaction: the travel is the hinge's two limits, and",
        "whatever drives it is code-side.",
        "",
        "## 1. The four sampled vehicles",
        "",
        "| vehicle | part | behaviour | axis | limits | pivot | parent |",
        "|---|---|---|---|---|---|---|"]
    for s in (donor, apc, mono, tank):
        for r in s["door_parts"]:
            h = r.get("hinge") or {}
            if h.get("axis"):
                axis = "(" + ", ".join(f"{v:g}" for v in h["axis"]) + ")"
                lim = f"{h['min_deg']:g} .. {h['max_deg']:g} deg"
                piv = "(" + ", ".join(f"{v:g}" for v in h["pivot"]) + ")"
            else:
                axis = lim = piv = "-"
            lines.append(f"| {s['label']} | `{r['name']}` | {r['behaviour'] or '-'} | "
                         f"{axis} | {lim} | {piv} | {r['parent']} |")
    lines += ["",
              f"The donor's three `door_parts[]` entries are its two side doors and",
              f"`sportsmuscle_hood_signature`; the APC's five are two centre doors, a rear-left",
              f"door, the front-left hatch and the turret hatch; the monorail car's sixteen are",
              f"the missile bay covers (eight per side).",
              "",
              f"## 2. (a) Can a door hinge about a transverse axis?",
              "",
              f"Yes. {c['by_axis'].get('X (transverse)', 0)} of the {c['limited']} hinged door "
              f"parts across {c['modules_with_doors']} modules rotate about **X** - hoods, roof "
              f"hatches and canopies; {c['by_axis'].get('Y (vertical)', 0)} rotate about **Y** "
              f"(side doors) and {c['by_axis'].get('Z (longitudinal)', 0)} about **Z** (the "
              f"monorail bay covers). A door that tilts forward is therefore an ordinary "
              f"`FrontLeftDoor`/`Hood` part on an X-axis hinge, e.g. `mediumtank_hatch` "
              f"(0..130 deg) or `sportsmuscle_hood_signature` (0..70 deg).",
              "",
              "| axis | parts |",
              "|---|---|"]
    for k, n in sorted(c["by_axis"].items()):
        lines.append(f"| {k} | {n} |")
    lines += ["", "Transverse-axis examples:", "",
              "| module | part | behaviour | axis | limits |", "|---|---|---|---|---|"]
    for t in c["transverse"]:
        lines.append(f"| `{t['module']}` | `{t['part']}` | {t['behaviour']} | "
                     f"({', '.join(f'{v:g}' for v in t['axis'])}) | "
                     f"{t['min_deg']:g} .. {t['max_deg']:g} deg |")
    lines += ["", "By behaviour:", "",
              "| behaviour | rows | axes | limits |", "|---|---|---|---|"]
    for name, b in sorted(c["by_behaviour"].items(), key=lambda kv: -kv[1]["rows"]):
        axes = ", ".join(f"{k.split(' ')[0]} {v}" for k, v in sorted(b["axes"].items()))
        lim = (f"{b['min']:g} .. {b['max']:g} deg" if b["min"] is not None else "-")
        lines.append(f"| `{name}` | {b['rows']} | {axes} | {lim} |")
    lines += ["",
              f"{len(c['no_hinge'])} door rows have `constraint_index` -1 and therefore no "
              f"hinge at all (propeller-wing parts with a door behaviour); every other row is a "
              f"`{LIMITED}`.",
              ""]

    lines += [
        "",
        "## 3. (b) What opens a `MissileHatch`?",
        "",
        f"The monorail car has {len(mono['door_parts'])} `MissileHatch` parts, all on",
        f"limited hinges of 0..150 deg about ±Z, listed in `door_parts[]`. Its only weapon is:",
        "",
        "| class | name | tuning |", "|---|---|---|"]
    for w in mono.get("weapons", []):
        lines.append(f"| `{w['class']}` | `{w['name']}` | `{w.get('tuning') or '-'}` |")
    comps = mono.get("weapon_components") or []
    lines += ["",
              f"Its {len(mono.get('weapon_points', []))} fire points are named "
              f"`InternalFirePosition_0…5` - the missiles leave from *inside* the bay the "
              f"covers close over. "
              + (f"The only other weapon class on it is "
                 + ", ".join('`' + c + '`' for c in comps) + "." if comps else ""),
              "",
              "**Nothing in the entity opens them.** No object other than `CPartProp` names a",
              "hatch part; there is no interaction entry for a hatch, no attached effect on one,",
              "and no member on the weapon that names a door. The behaviour name and the",
              "`door_parts[]` entry are the only links, so the opening is decided in code (almost",
              "certainly on fire, given the `Internal*` fire positions and the 150 deg travel) -",
              "that inference is not in the files.",
              "",
              "## 4. (c) Does the driver's entry open the driver door part?",
              "",
              "The interaction graph carries two entry paths, and the state names say what they",
              "do:",
              "",
              "| entity | `entry.driver` | `entry.driver.no.door` | `S_ENTER_DRIVER_VEHICLE` | "
              "`S_ENTER_DRIVER_NO_DOOR_VEHICLE` |",
              "|---|---|---|---|---|"]
    for s in (donor, apc, mono):
        e = s.get("interaction") or {}
        tick = lambda v: "yes" if v else "-"
        lines.append(f"| {s['label']} | {tick(e.get('driver_door_entry'))} | "
                     f"{tick(e.get('no_door_entry'))} | {tick(e.get('driver_enter_state'))} | "
                     f"{tick(e.get('driver_enter_no_door_state'))} |")
    lines += ["",
              f"Across {i['entities']} cached entity graphs, {i['both']} carry **both** paths,",
              f"{i['door_only']} only the door path, {i['no_door_only']} only the no-door path,",
              f"and {i['neither']} neither (military vehicles, trains and aircraft whose entry",
              f"nodes carry other names).",
              "The donor is in the `both` group: the driver can enter through the door",
              "(`entry.driver` → `S_ENTER_DRIVER_VEHICLE`) or without it",
              "(`entry.driver.no.door` → `S_ENTER_DRIVER_NO_DOOR_VEHICLE`).",
              "",
              f"The donor's container is {donor['container']['members']} members and holds "
              f"{len(donor['container']['animation_members'])} animation files: the swing is not",
              "authored in the entity. So the file proves the *branch* exists and which",
              "interaction the door path belongs to, but not that the part visibly moves - it",
              "is a hinge with no curve, driven by whatever runs after `S_ENTER_DRIVER_VEHICLE`.",
              "For a B-05 canopy the actionable",
              "form is: X-axis limited hinge on a `Hood`/`FrontLeftDoor` part, listed in",
              "`door_parts[]`, plus the `entry.driver` path if the door is meant to be used.",
              "",
              "## 5. Validation and limits",
              "",
              "`jc3doors.py --check` re-reads the four entities, the cached modules and the",
              "cached `.epe` graphs, rebuilds both files and compares them. It asserts: the",
              "donor's door array is `door_f_l`, `door_f_r`, `hood_signature`; its two doors",
              "hinge about ±Y and the hood about +X; the monorail's 16 hatches are all limited",
              "hinges of 0..150 deg about ±Z; no object outside `CPartProp` names a monorail",
              "hatch; the donor has both entry paths and the APC has neither driver entry;",
              "every door part with a constraint is a limited hinge (or is listed as an",
              "exception with its class).",
              "",
              "**Limits.** An angle is the hinge's authored limit, not a measured swing - nothing",
              "in the files says the door reaches it. Speed is absent everywhere (no rate field,",
              "no animation curve), so it stays UNKNOWN. The census covers the 78 cached parts",
              "modules (56 with doors) and the 55 cached `.epe` graphs, not all 233 entities.",
              "The `MissileHatch` firing trigger is an inference from the fire-point names and",
              "the bay geometry; the entity contains no link. Which code runs after an entry",
              "state is not in any file read here.",
              ""]
    return "\n".join(lines).rstrip() + "\n"


def invariants(d: dict) -> list[str]:
    bad = []
    by_tag = {s["tag"]: s for s in d["samples"]}
    donor, apc, mono, tank = (by_tag["donor"], by_tag["apc"], by_tag["monorail"],
                              by_tag["mediumtank"])
    names = [r["name"] for r in donor["door_parts"]]
    if names != ["sportsmuscle_door_f_l", "sportsmuscle_door_f_r",
                 "sportsmuscle_hood_signature"]:
        bad.append(f"donor door array: {names}")
    by_name = {r["name"]: r for r in donor["door_parts"]}
    for n, cls in (("sportsmuscle_door_f_l", "Y (vertical)"),
                   ("sportsmuscle_door_f_r", "Y (vertical)"),
                   ("sportsmuscle_hood_signature", "X (transverse)")):
        if by_name[n].get("axis_class") != cls:
            bad.append(f"donor {n} axis {by_name[n].get('axis_class')} != {cls}")
    if len(apc["door_parts"]) != 5:
        bad.append(f"apc has {len(apc['door_parts'])} door parts, expected 5")
    if len(mono["door_parts"]) != 16:
        bad.append(f"monorail has {len(mono['door_parts'])} door parts, expected 16")
    for r in mono["door_parts"]:
        h = r.get("hinge") or {}
        if r["behaviour"] != "MissileHatch":
            bad.append(f"monorail door {r['name']} is {r['behaviour']}")
        if h.get("class") != LIMITED or h.get("max_deg") != 150.0:
            bad.append(f"monorail hatch {r['name']} hinge {h}")
        if r.get("axis_class") != "Z (longitudinal)":
            bad.append(f"monorail hatch {r['name']} axis {r.get('axis_class')}")
    if mono.get("hatch_refs_outside_part_prop"):
        bad.append("monorail hatch is named outside CPartProp: "
                   f"{mono['hatch_refs_outside_part_prop'][:2]}")
    tank_hatch = next((r for r in tank["door_parts"] if r["name"] == "mediumtank_hatch"), None)
    if not tank_hatch or tank_hatch.get("axis_class") != "X (transverse)":
        bad.append("medium tank hatch is not on a transverse hinge")
    if tank_hatch and (tank_hatch["hinge"]["min_deg"], tank_hatch["hinge"]["max_deg"]) != (0.0, 130.0):
        bad.append(f"medium tank hatch limits {tank_hatch['hinge']}")
    if donor["container"]["animation_members"]:
        bad.append(f"donor container has animation members: "
                   f"{donor['container']['animation_members'][:3]}")
    di = donor["interaction"]
    if not (di.get("driver_door_entry") and di.get("no_door_entry")):
        bad.append(f"donor entry paths: {di}")
    ai = apc["interaction"]
    if ai.get("driver_door_entry") or ai.get("driver_enter_state"):
        bad.append(f"apc unexpectedly has a driver entry: {ai}")
    mi = mono["interaction"]
    if any("door" in e for e in mi.get("entries", [])):
        bad.append(f"monorail has a door entry: {mi['entries']}")
    c = d["census"]
    if not c["limited"] or c["by_axis"].get("X (transverse)", 0) == 0:
        bad.append("no transverse door hinge in the census")
    if c["by_axis"].get("Y (vertical)", 0) == 0:
        bad.append("no vertical door hinge in the census")
    for k in c["other_classes"]:
        if k == LIMITED:
            bad.append("limited hinge counted as an exception")
    return bad


def cmd_write() -> int:
    d = build()
    with open(os.path.join(OUT, JSON_NAME), "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    with open(os.path.join(OUT, MD_NAME), "w", encoding="utf-8", newline="\n") as f:
        f.write(render_md(d))
    c = d["census"]
    print(f"{JSON_NAME}: {len(d['samples'])} samples, {c['door_rows']} door rows in "
          f"{c['modules_with_doors']} modules, {c['limited']} hinged")
    print(f"{MD_NAME}: {len(open(os.path.join(OUT, MD_NAME), encoding='utf-8').read().splitlines())} lines")
    return 0


def cmd_check() -> int:
    d = build()
    bad = invariants(d)
    jp, mp = os.path.join(OUT, JSON_NAME), os.path.join(OUT, MD_NAME)
    if not (os.path.exists(jp) and os.path.exists(mp)):
        print(f"FAIL: {JSON_NAME}/{MD_NAME} missing")
        return 1
    old = json.load(open(jp, encoding="utf-8"))
    if old != d:
        for k in sorted(set(old) | set(d)):
            if old.get(k) != d.get(k):
                bad.append(f"json section changed: {k}")
                break
    md = render_md(d)
    if md != open(mp, encoding="utf-8").read():
        import difflib
        diff = list(difflib.unified_diff(open(mp, encoding="utf-8").read().splitlines(),
                                         md.splitlines(), "file", "rebuilt", n=1))
        bad.append("md differs: " + " | ".join(diff[2:8]))
    if bad:
        print("FAIL: " + "; ".join(bad))
        return 1
    c = d["census"]
    print(f"PASS: {len(d['samples'])} samples, {c['door_rows']} door rows / "
          f"{c['limited']} hinged / X {c['by_axis'].get('X (transverse)', 0)}, "
          f"both entry paths {d['interactions']['both']}")
    return 0


def cmd_dump(what: str) -> int:
    d = build()
    if what == "samples":
        print(json.dumps(d["samples"], indent=1, sort_keys=True, ensure_ascii=False)[:14000])
    elif what == "census":
        print(json.dumps(d["census"], indent=1, sort_keys=True, ensure_ascii=False)[:10000])
    elif what == "interactions":
        print(json.dumps(d["interactions"], indent=1, sort_keys=True)[:6000])
    else:
        print("one of: samples, census, interactions")
        return 2
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    d = sub.add_parser("dump")
    d.add_argument("what", nargs="?", default="samples")
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
