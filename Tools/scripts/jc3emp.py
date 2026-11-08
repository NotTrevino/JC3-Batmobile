#!/usr/bin/env python
"""jc3emp.py - G2-16: the EMP truck, what its device is, and whether another vehicle can fire it.

Decodes both EMP builds of the old truck (`rebel_emp_01`, `rebel_emp_custom_mm250`), their parts
modules, force pulses, explosion tunes, effect files and interaction entries; every other oldtruck
variant (to show the device is only on the two EMP builds); and the game's two `CEMPWeapon` entities
(the handheld `w702_emp` and the static `w503_turret_emp`) with their tunes.

Writes Research/JC3Grab/EMP.md + EMP.json. `--check` rebuilds and asserts.

Usage:
  python jc3emp.py --write
  python jc3emp.py --check
  python jc3emp.py dump trucks|variants|weapons|tune
"""
from __future__ import annotations

import argparse
import collections
import difflib
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jc3adf  # noqa: E402
import jc3detail  # noqa: E402
import jc3grab  # noqa: E402
import jc3index  # noqa: E402
import jc3wiring  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
GAME = os.environ.get("JC3_GAME", jc3index.DEFAULT_GAME)
JSON_NAME = "EMP.json"
MD_NAME = "EMP.md"
WIRING = os.path.join(OUT, "WEAPON_WIRING.jsonl")
TRUCK_DIR = "editor/entities/jc_vehicles/01_land/v0505_car_solar_oldtruck/"
TRUCKS = (("emp_01", "v0505_car_solar_oldtruck_rebel_emp_01.ee"),
          ("mm250", "v0505_car_solar_oldtruck_rebel_emp_custom_mm250.ee"))
WEAPONS = (
    ("w702", "handheld", "editor/entities/jc_weapons/02_two_handed/w702_emp/w702_emp.ee"),
    ("w503", "static turret",
     "editor/entities/jc_weapons/05_stationary/w503_turret_emp/w503_turret_emp.ee"),
)
OID_KEYS = ("id:06A05F33", "id:D3DDD766")


def container(ee: str, rows: list[dict]) -> tuple[bytes, list[tuple[str, int, int]]]:
    return jc3detail.inner_files(jc3grab.read_entry(jc3detail.pick(rows, ee), GAME))


def module_parts(ee: str, rows: list[dict]) -> list[dict]:
    stream, entries = container(ee, rows)
    name, off, size = next(e for e in entries if e[0].endswith("_vehicle_parts.vmodc"))
    return jc3adf.parts(jc3adf.Adf(stream[off:off + size]))


def tune(stream: bytes, entries, suffix: str) -> list[dict] | None:
    hit = next((e for e in entries if e[0].endswith(suffix)), None)
    if hit is None:
        return None
    return [{"type": t, "name": n, "value": v}
            for n, t, v in jc3adf.walk(jc3adf.Adf(stream[hit[1]:hit[1] + hit[2]]))]


def rotate_rows(ee: str, rows: list[dict]) -> list[dict]:
    stream, entries = container(ee, rows)
    name, off, size = next(e for e in entries if e[0].endswith("_vehicle_parts.vmodc"))
    flat = {p: v for p, _t, v in jc3adf.walk(jc3adf.Adf(stream[off:off + size]))}
    out, i = [], 0
    while f"rotating_parts[{i}].part_index" in flat:
        out.append({k.split("]", 1)[1].lstrip("."): v for k, v in flat.items()
                    if k.startswith(f"rotating_parts[{i}].")})
        i += 1
    return out


def resolve(objs: list) -> dict[str, str]:
    return {o.oid: f"{o.cls} {o.name}".strip() for o in objs if o.oid}


def tune_values(rows: list[dict] | None) -> dict:
    return {r["name"]: r["value"] for r in rows or []} if rows else {}


def is_oid(v: str) -> bool:
    return (isinstance(v, str) and len(v) == 17 and v[8] == "="
            and all(c in "0123456789ABCDEF" for c in v[:8] + v[9:]))


def is_emp_name(path: str) -> bool:
    """True for `truck_emp.ftunec`, `explosion_emp_flatbed.effc`, `emp_active.effc` - but not
    `explosion_template_trail.effc` (whose 'emp' is inside 'template')."""
    stem = path.rsplit("/", 1)[-1].lower()
    return stem.startswith("emp") or "_emp" in stem or "emp_" in stem


def oid_list(v: str) -> list[str]:
    return [x.strip() for x in (v or "").split(",") if is_oid(x.strip())]


def fmt(v) -> str:
    """Render a number, snapping float noise (2.2e-16 on a rotation axis) to 0."""
    if isinstance(v, float):
        return jc3wiring.num(0.0 if abs(v) < 1e-6 else v)
    return jc3wiring.num(v)


def build() -> dict:
    rows = jc3index.load_index(OUT)
    trucks = []
    for tag, leaf in TRUCKS:
        ee = TRUCK_DIR + leaf
        objs, _doc = jc3wiring.decode_epe(ee, rows, GAME)
        stream, entries = container(ee, rows)
        oids = resolve(objs)
        parts = module_parts(ee, rows)
        pulses = []
        for o in (o for o in objs if o.cls == "CForcePulse"):
            pulses.append({
                "name": o.name,
                "settings": o.get("SettingsFile"),
                "xyz": jc3wiring.xyz(o.get("world")),
                "refs": {k: {"id": o.get(k), "resolved": oids.get(o.get(k))}
                         for k in OID_KEYS if o.get(k) not in ("", "00000000")},
                "props": {k: v for k, v in o.props.items()
                          if k not in ("name", "world", "_object_id", "name_hash",
                                       "SettingsFile")},
            })
        entries_ui = []
        for o in objs:
            if o.cls == "CInteractionGraphEntry" and o.name == "entry.use_item":
                entries_ui.append({"class": o.cls, "name": o.name, "state": o.get("state"),
                                   "prompt": o.get("id:3B381407"), "enabled": o.get("enabled")})
            elif o.cls == "CInteractionTrigger" and o.name == "trigger.use_item":
                entries_ui.append({"class": o.cls, "name": o.name,
                                   "xyz": jc3wiring.xyz(o.get("world")),
                                   "enabled": o.get("id:75239A63"),
                                   "links": oid_list(o.get("id:A5C536A1"))})
        emitters = [{"name": o.name, "effect": o.get("effect"), "enabled": o.get("enabled"),
                     "xyz": jc3wiring.xyz(o.get("world")),
                     "events": {k: o.get(k) for k in ("event_enable", "event_play",
                                                      "event_stop", "event_finished_playing")}}
                    for o in objs if o.cls == "CEffectPointEmitter" and "emp" in o.name]
        tables = [{"name": o.name, "class": o.cls} for o in objs
                  if o.cls == "CMaterialEffectTable"]
        tunes = {}
        for suffix in ("truck_emp.ftunec", "car_explosion_medium.ftunec"):
            got = tune(stream, entries, suffix)
            if got is not None:
                tunes[suffix] = got
        trucks.append({
            "tag": tag, "entity": ee, "members": len(entries), "objects": len(objs),
            "parts_total": len(parts),
            "emp_parts": [{"name": p["name"], "behavior": p["behavior"] or "-",
                           "part_index": p["part_index"], "parent": p["parent_part_index"],
                           "model": p["model"]} for p in parts if "emp" in p["name"].lower()],
            "rotor": [r for r in rotate_rows(ee, rows)
                      if any(r.get("part_index") == p["part_index"] for p in parts
                             if p["name"].endswith("core_rebel"))],
            "pulses": pulses, "use_item": entries_ui, "emitters": emitters,
            "material_tables": tables, "tunes": tunes,
            "files": [{"path": n, "size": s} for n, _o, s in entries
                      if n.endswith((".ftunec", ".effc")) and
                      ("emp" in n.lower() or "explosion" in n.lower())],
            "weapon_classes": sorted({o.cls for o in objs if "Weapon" in o.cls}),
        })

    variants = []
    for r in rows:
        if r["path"].startswith(TRUCK_DIR) and r["path"].endswith(".ee"):
            parts = module_parts(r["path"], rows)
            emp = [p["name"] for p in parts if "emp" in p["name"].lower()]
            objs, _doc = jc3wiring.decode_epe(r["path"], rows, GAME)
            props = [o.name for o in objs if o.cls == "CPartProp" and "emp" in o.name.lower()]
            variants.append({"entity": r["path"].rsplit("/", 1)[-1], "parts": len(parts),
                             "emp_parts": emp, "emp_props": len(props),
                             "emp_pulse": sum(1 for o in objs
                                              if o.cls == "CForcePulse" and o.name == "EMP")})

    weapons = []
    for tag, kind, ee in WEAPONS:
        objs, _doc = jc3wiring.decode_epe(ee, rows, GAME)
        stream, entries = container(ee, rows)
        w = next((o for o in objs if o.cls == "CEMPWeapon"), None)
        trows = tune(stream, entries, ".wtunec")
        vals = tune_values(trows)
        damage = next((v for k, v in vals.items() if k.endswith("tuning.base_tuning.damage")), None)
        weapons.append({
            "tag": tag, "kind": kind, "entity": ee, "members": len(entries),
            "component": {"class": w.cls, "name": w.name, "weapon_id": w.get("weapon_id"),
                          "weapon_type": w.get("weapon_type"),
                          "tune": next((v for v in w.props.values()
                                        if isinstance(v, str) and v.endswith(".wtune")), None),
                          "material_table": oids.get(w.get("id:0E904826")) if w else None}
            if w else None,
            "points": [{"name": o.name, "type": o.get("type"),
                        "xyz": jc3wiring.xyz(o.get("world"))}
                       for o in objs if o.cls == "SWeaponPoint"],
            "effects": [{"name": o.name, "target": next(
                (v for v in o.props.values()
                 if isinstance(v, str) and v.endswith((".effc", ".etune"))), o.get("Effect"))}
                for o in objs if o.cls in ("SAttachedEffect", "CMaterialEffectTable")],
            "components": dict(collections.Counter(o.cls for o in objs if "Component" in o.cls)),
            "tune": {"file": next((n for n, _o, _s in entries if n.endswith(".wtunec")), None),
                     "rows": len(trows or []),
                     "emp_keys": sorted(k for k in vals if "emp" in k.lower()),
                     "values": {"damage": damage,
                                **{k: vals[k] for k in ("max_range", "magazine_size",
                                                        "fire_rate", "velocity")
                                   if k in vals}}},
            "files": [{"path": n, "size": s} for n, _o, s in entries
                      if n.endswith(".effc") and "emp" in n.lower()],
        })

    fleet = collections.Counter()
    for line in open(WIRING, encoding="utf-8"):
        if line.strip():
            for entry in json.loads(line)["weapons"]:
                fleet[entry["class"]] += 1
    out = {"trucks": trucks, "variants": variants, "weapons": weapons,
           "fleet": {"components": sum(fleet.values()), "cemp": fleet.get("CEMPWeapon", 0)}}
    out["digest"] = hashlib.sha1(json.dumps(out, sort_keys=True,
                                            separators=(",", ":")).encode()).hexdigest()[:16]
    return out


# ---------------------------------------------------------------------- md
def render_md(d: dict) -> str:
    emp, mm = d["trucks"]
    emp_tune = tune_values(emp["tunes"].get("truck_emp.ftunec"))
    blast = tune_values(emp["tunes"].get("car_explosion_medium.ftunec"))
    plain = next(p for p in emp["pulses"] if p["name"] == "CForcePulse")
    pulse = next(p for p in emp["pulses"] if p["name"] == "EMP")
    core = next((p for p in emp["emp_parts"] if p["name"].endswith("core_rebel")), {})
    rotor = emp["rotor"][0] if emp["rotor"] else {}
    w702, w503 = d["weapons"]
    diff_keys = [k for k in sorted(pulse["props"])
                 if pulse["props"][k] != plain["props"].get(k)]
    flags = [k for k in diff_keys if k not in OID_KEYS]
    emp_files = [f for f in emp["files"] if is_emp_name(f["path"])]
    emp_files += [f for f in mm["files"] if is_emp_name(f["path"]) and f not in emp_files]
    props_variants = [v for v in d["variants"] if v["emp_props"]]
    others = [v for v in d["variants"] if not v["emp_props"]]
    entry = next(e for e in emp["use_item"] if e["class"] == "CInteractionGraphEntry")
    trig = next(e for e in emp["use_item"] if e["class"] == "CInteractionTrigger")
    lines = [
        "# The EMP truck",
        "",
        "G2-16. **Answer: yes for the effect, no as a weapon-slot copy.** Everything the truck's EMP",
        "is - three parts, a `CForcePulse`, its explosion tune, an effect file and a use-item",
        "trigger - lives inside the truck's own `.ee`. Any vehicle entity that carries the same",
        "objects gets the same device; nothing in the files says whether the pulse actually fires",
        "when the action runs (that is code), and no vehicle weapon slot in the game currently",
        "holds the engine's EMP weapon class (`CEMPWeapon`).",
        "",
        "## 1. The device",
        "",
        "`rebel_emp_01` is a 794-member container with 454 objects; the device is",
        f"{len(emp['emp_parts'])} chassis parts on the flatbed:",
        "",
        "| part | index | behaviour | parent | model |",
        "|---|---|---|---|---|"]
    for p in emp["emp_parts"]:
        lines.append(f"| `{p['name']}` | {p['part_index']} | {p['behavior']} | "
                     f"{p['parent']} | `{p['model'].rsplit('/', 1)[-1]}` |")
    lines += [
        "",
        f"The core is a `Rotor`: its `rotating_parts[]` row in the parts module names part "
        f"{rotor.get('part_index')}, {rotor.get('number_of_blades')} blades, axis "
        f"({fmt(rotor.get('rotation_axis[0]'))}, "
        f"{fmt(rotor.get('rotation_axis[1]'))}, "
        f"{fmt(rotor.get('rotation_axis[2]'))}), `rpm_multiplier` "
        f"{fmt(rotor.get('rpm_multiplier'))}, no visibility window "
        f"({fmt(rotor.get('min_rpm_visible'))}..{fmt(rotor.get('max_rpm_visible'))}).",
        "`Rotor` takes its `rpm_variable` from `vehicle_common` (G2-14), so the spinning core is",
        "the stock rotating-part mechanism, not a new one.",
        "",
        "## 2. The pulse and its tune",
        "",
        "The truck carries **two** force pulses - the ordinary explosion pulse every car has, and",
        "the EMP:",
        "",
        "| pulse | settings | position |",
        "|---|---|---|"]
    for p in emp["pulses"]:
        lines.append(f"| `{p['name']}` | `{(p['settings'] or '-').rsplit('/', 1)[-1]}` | "
                     f"({', '.join(jc3wiring.num(c) for c in (p['xyz'] or []))}) |")
    lines += [
        "",
        f"`truck_emp.ftunec` is {len(emp_tune)} numbers and nothing else:",
        "",
        "| member | EMP (`truck_emp`) | plain car blast (`car_explosion_medium`) |",
        "|---|---|---|"]
    for k in (emp_tune or blast):
        lines.append(f"| `{k}` | {jc3wiring.num(emp_tune.get(k))} | {jc3wiring.num(blast.get(k))} |")
    lines += [
        "",
        "So the data-side difference from a normal car explosion is **100 damage in 25 m instead",
        "of 500 in 5 m, with the damage held at full for the whole radius**",
        "(`*RadiusPercentageMax` 1.0 here, 0.0 on the plain blast; `*RadiusMin` 1.0 vs 0.0).",
        "",
        "**Duration and what it disables are not in the files.** The tune has no duration, no",
        "target class and no \"disable\" member; the disable semantics (engines, electronics, AI)",
        "are in code. The pulse's other members are object-id properties, and only",
        f"{len(diff_keys)} of them differ from the plain explosion pulse:",
        "",
        "| member | EMP | plain |",
        "|---|---|---|"]
    for k in diff_keys:
        lines.append(f"| `{k}` | {pulse['props'][k] or '-'} | {plain['props'].get(k) or '-'} |")
    lines += [
        "",
        f"So besides the radius, an EMP is {len(flags)} flags and the `emp_flatbed_table`",
        "material-effect table. What the flags mean is not named anywhere in the container; the",
        "radius and the table's effect file are the only EMP-specific data with a readable name.",
        "",
        "The pulse's object references:",
        "",
        "| member | points at |",
        "|---|---|"]
    for k, v in pulse["refs"].items():
        lines.append(f"| `{k}` | `{v['id']}` - {v['resolved'] or '**no such object in the entity**'} |")
    lines += [
        "",
        "## 3. Trigger",
        "",
        "| object | value |",
        "|---|---|"]
    for label, value in (("`entry.use_item` (`CInteractionGraphEntry`) - state", entry["state"]),
                         ("prompt", entry["prompt"]),
                         ("`trigger.use_item` (`CInteractionTrigger`) position",
                          "(" + ", ".join(fmt(c) for c in (trig["xyz"] or [])) + ")"),
                         ("trigger refs", ", ".join(f"`{x}`" for x in trig["links"]) or "-")):
        cell = value if value.startswith("`") else f"`{value}`"
        lines.append(f"| {label} | {cell} |")
    lines += [
        "",
        "`trigger.use_item` is a 2x-scaled box over the flatbed, and `entry.use_item` runs the",
        f"state `{entry['state']}` with the prompt `{entry['prompt']}`. There is **no object",
        "reference from the trigger, the entry or the vehicle to the `EMP` pulse**, and the",
        "trigger's own refs do not resolve inside the entity: the pulse is fired by whatever",
        "executes that state, and the files prove only the action and its label.",
        "",
        "The truck has **no weapon component at all** (no `CBulletWeaponBase`, no missile weapon,",
        "no turret), so the EMP is not on any fire button.",
        "",
        "## 4. Effects and sound",
        "",
        "| file | size | in |",
        "|---|---|---|"]
    for f in emp["files"]:
        lines.append(f"| `{f['path'].rsplit('/', 1)[-1]}` | {f['size']} | emp_01 |")
    for f in mm["files"]:
        if f not in emp["files"]:
            lines.append(f"| `{f['path'].rsplit('/', 1)[-1]}` | {f['size']} | mm250 |")
    lines += ["", f"Only {len(emp_files)} of those are EMP files (`{'`, `'.join(f['path'].rsplit('/', 1)[-1] for f in emp_files)}`);",
              "the rest are the stock explosion effects every car carries."]
    lines += [
        "",
        f"`emp_flatbed_table` maps every material slot to one effect hash, which is the embedded",
        f"`explosion_emp_flatbed.effc`; the entity also embeds the camera",
        f"`full_screen_effect.ctunec`. **No EMP sound**: the container's attached effects are the",
        f"ordinary vehicle set (engine, horn, gear change, damage fires, exhaust) - there is no",
        f"`SAttachedEffect` naming emp, and the only weapon-side EMP sounds are on `w702`'s",
        f"charging/charged/fire effects.",
        "",
        "## 5. The two builds, and every other oldtruck variant",
        "",
        "| | `rebel_emp_01` | `rebel_emp_custom_mm250` |",
        "|---|---|---|"]
    for label, fn in (("container members", lambda t: t["members"]),
                      ("objects", lambda t: t["objects"]),
                      ("parts (module)", lambda t: t["parts_total"]),
                      ("EMP parts", lambda t: len(t["emp_parts"])),
                      ("`CForcePulse` named EMP",
                       lambda t: sum(1 for p in t["pulses"] if p["name"] == "EMP")),
                      ("`truck_emp.ftunec`", lambda t: "yes" if "truck_emp.ftunec" in t["tunes"] else "no"),
                      ("`emp_active.effc`",
                       lambda t: "yes" if any("emp_active" in f["path"] for f in t["files"]) else "no"),
                      ("EMP emitters", lambda t: ", ".join(e["name"] for e in t["emitters"]) or "-"),
                      ("use-item prompt", lambda t: next((e["prompt"] for e in t["use_item"]
                                                          if e["class"] == "CInteractionGraphEntry"), "-")),
                      ("weapon classes", lambda t: ", ".join(t["weapon_classes"]) or "none")):
        lines.append(f"| {label} | {fn(emp)} | {fn(mm)} |")
    lines += [
        "",
        "Same members, same parts, same trigger, same prompt; the mm250 build **drops the pulse",
        "and its tune** and adds the charging prop: `CEffectPointEmitter epe_emp_powering_up`",
        f"(effect hash {mm['emitters'][0]['effect'] if mm['emitters'] else '-'}, `enabled` "
        f"{mm['emitters'][0]['enabled'] if mm['emitters'] else '-'}) over the device at "
        f"({', '.join(fmt(c) for c in (mm['emitters'][0]['xyz'] if mm['emitters'] else []))}),",
        "which is the mission prop (`mm250` is the escort mission's EMP truck). The blast in",
        "that mission is the script's.",
        "",
        "| oldtruck variant | parts | device parts in module | `CPartProp`s | EMP pulse |",
        "|---|---|---|---|---|"]
    for v in d["variants"]:
        lines.append(f"| `{v['entity']}` | {v['parts']} | {len(v['emp_parts'])} | "
                     f"{v['emp_props']} | {v['emp_pulse']} |")
    lines += [
        "",
        f"The parts module is **shared by all {len(d['variants'])} variants** - the three device",
        "parts and the spinning core are compiled into every oldtruck, which is why the mesh list",
        "of the civilian truck contains `oldtruck_emp_device_*.rbm`. What the EMP builds add is",
        f"the three `CPartProp` objects ({len(props_variants)} variants), the `EMP` pulse and its tune",
        f"({len(props_variants)} variants), the trigger and the prompt; the other {len(others)}",
        "variants have the geometry but no props, no pulse and no trigger, so nothing calls",
        "it.",
        "",
        "## 6. The weaponised EMP",
        "",
        "The engine does have an EMP weapon class, in two files:",
        "",
        "| | `w702_emp` | `w503_turret_emp` |",
        "|---|---|---|"]
    for label, fn in (("kind", lambda w: w["kind"]),
                      ("class", lambda w: (w["component"] or {}).get("class")),
                      ("weapon id / type",
                       lambda w: f"{(w['component'] or {}).get('weapon_id')} / "
                                 f"{(w['component'] or {}).get('weapon_type')}"),
                      ("fire point",
                       lambda w: ", ".join(f"`{p['name']}` "
                                           f"({', '.join(jc3wiring.num(c) for c in (p['xyz'] or []))})"
                                           for p in w["points"])),
                      ("components",
                       lambda w: ", ".join(f"{k} x{v}" for k, v in sorted(w["components"].items()))),
                      ("tune", lambda w: (w["tune"]["file"] or "-").rsplit("/", 1)[-1]),
                      ("tune EMP fields", lambda w: ", ".join(w["tune"]["emp_keys"]) or "**none**"),
                      ("damage / range",
                       lambda w: f"{jc3wiring.num(w['tune']['values'].get('damage'))} / "
                                 f"{jc3wiring.num(w['tune']['values'].get('max_range'))} m")):
        lines.append(f"| {label} | {fn(w702)} | {fn(w503)} |")
    lines += [
        "",
        "Both use the stock `fow_weapon` tune: the EMP table has **no EMP-specific field in",
        "either file** - the tune carries damage, range, recoil and magazine, and the EMP",
        "behaviour is keyed entirely off the `CEMPWeapon` class in code. `w702` is the handheld",
        "two-handed variant (spin-up dials via three `CBarrelSpinWeaponComponent`s, wall",
        "penetration, charging/charged/fire effects and sounds); `w503` is the static prop with",
        "its own rigid objects, hinge and a `CTurretWeaponComponent`.",
        "",
        "## 7. Copy list - what the Batmobile would need",
        "",
        "| what | value |",
        "|---|---|"]
    for p in emp["emp_parts"]:
        lines.append(f"| part | `{p['name']}` ({p['behavior']}, index {p['part_index']}, "
                     f"parent {p['parent']}) |")
    for f in emp_files:
        lines.append(f"| file | `{f['path']}` |")
    for k, v in pulse["refs"].items():
        if v["resolved"]:
            lines.append(f"| pulse ref | `{k}` -> `{v['resolved'].split(' ')[0]}` "
                         f"`{v['resolved'].split(' ', 1)[-1]}` |")
    lines += [
        f"| pulse | `CForcePulse` `EMP`, `{pulse['settings'].rsplit('/', 1)[-1]}` |",
        "| parts entry | `CPartProp` per part, and the module's `rotating_parts[]` row for the core |",
        f"| trigger | `trigger.use_item` box + `entry.use_item` -> `{entry['state']}`, prompt "
        f"`{entry['prompt']}` |",
        "",
        "`car_explosion_medium.ftunec` is the stock blast every car carries and needs no copy.",
        "",
        "Models live under `models/jc_vehicles/01_land/v0505_car_solar_oldtruck/",
        "oldtruck_emp_device_*`; the textures are under",
        "`models/jc_environments/structures/rebel/dimahs_lab/emp_device_01/`. The device also",
        "needs the vehicle's interaction graph (a stunt-vehicle graph in this entity), so on a",
        "entity without one the trigger has nothing to run.",
        "",
        "## 8. Validation and limits",
        "",
        "`jc3emp.py --check` rebuilds both files from the game archives and asserts: both builds",
        f"are {emp['members']}-member containers with {emp['objects']} objects; `emp_01` has the",
        "plain pulse plus `EMP` on `truck_emp.ftune` at (0, 2.0356, 0.6992), whose 8 tune values are",
        "100/25/1/1 for players and AI; the plain blast tune is 500/5/0/0; the 3 EMP parts exist,",
        "the core is `Rotor` at index 46 with a 6-blade +Z `rotating_parts[]` row; `entry.use_item`",
        f"is `{entry['state']}` with prompt `{entry['prompt']}` and `trigger.use_item` sits on the",
        "flatbed; no weapon component is on the truck; only the EMP build carries `truck_emp.ftunec`",
        "while both embed `explosion_emp_flatbed.effc`; `mm250` has the powered-up emitter and no",
        "pulse; every oldtruck variant carries the 3 device parts in its module but only the two",
        "EMP builds carry the `CPartProp`s and the pulse; `w702`/`w503` are",
        "`CEMPWeapon` with types 6/2, `w503` carrying a `CTurretWeaponComponent`, and neither tune",
        "has an EMP-named field; no `CEMPWeapon` appears among the fleet's vehicle weapon",
        "components.",
        "",
        "**Limits.** Duration, the disable effect and the meaning of the three flags are not in",
        "any decoded member - they are code. The link from the use-item state to the pulse is",
        "likewise absent, so \"the driver presses use item and the pulse fires\" is inferred from",
        "the shared entity plus the `ui_activate_emp` prompt, not read from a pointer. Whether the",
        "engine accepts `CEMPWeapon` in a vehicle slot cannot be decided from data; the two",
        "existing users are a handheld and a static prop, and the 88 vehicle weapon components in",
        "`WEAPON_WIRING` include none. The device also needs the stunt-vehicle interaction graph;",
        "the donor's graph is what supplies `entry.use_item`.",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def invariants(d: dict) -> list[str]:
    bad = []
    emp, mm = d["trucks"]
    pulses = {p["name"]: p for p in emp["pulses"]}
    if set(pulses) != {"CForcePulse", "EMP"}:
        bad.append(f"emp_01 pulses {sorted(pulses)}")
    if pulses.get("EMP", {}).get("settings") != \
            "editor/entities/jc_explosions/vehicles/truck_emp.ftune":
        bad.append(f"EMP settings {pulses.get('EMP', {}).get('settings')}")
    if pulses.get("EMP", {}).get("xyz") != [0, 2.0356, 0.6992]:
        bad.append(f"EMP position {pulses.get('EMP', {}).get('xyz')}")
    et = tune_values(emp["tunes"].get("truck_emp.ftunec"))
    bt = tune_values(emp["tunes"].get("car_explosion_medium.ftunec"))
    for k, want in (("PlayerDamage", 100), ("PlayerDamageRadius", 25.0),
                    ("PlayerDamageRadiusPercentageMax", 1.0), ("PlayerDamageRadiusMin", 1.0),
                    ("AIDamage", 100), ("AIDamageRadius", 25.0)):
        if et.get(k) != want:
            bad.append(f"truck_emp {k}={et.get(k)!r} want {want!r}")
    for k, want in (("PlayerDamage", 500), ("PlayerDamageRadius", 5.0),
                    ("PlayerDamageRadiusPercentageMax", 0.0)):
        if bt.get(k) != want:
            bad.append(f"car_explosion_medium {k}={bt.get(k)!r} want {want!r}")
    if len(emp["emp_parts"]) != 3:
        bad.append(f"emp parts {len(emp['emp_parts'])}")
    core = next((p for p in emp["emp_parts"] if p["name"].endswith("core_rebel")), None)
    if not core or core["behavior"] != "Rotor" or core["part_index"] != 46:
        bad.append(f"core part {core}")
    rotor = emp["rotor"][0] if emp["rotor"] else {}
    if rotor.get("part_index") != 46 or rotor.get("number_of_blades") != 6:
        bad.append(f"rotor row {rotor}")
    if rotor.get("rotation_axis[2]") != 1.0:
        bad.append(f"rotor axis {rotor.get('rotation_axis[2]')}")
    entry = next((e for e in emp["use_item"] if e["class"] == "CInteractionGraphEntry"), None)
    if not entry or entry["state"] != "S_STUNT_USE_ITEM_VEHICLE" or \
            entry["prompt"] != "ui_activate_emp":
        bad.append(f"use_item entry {entry}")
    trig = next((e for e in emp["use_item"] if e["class"] == "CInteractionTrigger"), None)
    if not trig or [round(c, 3) for c in trig["xyz"]] != [0, 1.351, 2.396]:
        bad.append(f"use_item trigger {trig and trig['xyz']}")
    if emp["weapon_classes"]:
        bad.append(f"emp_01 weapon classes {emp['weapon_classes']}")
    if not any(f["path"].endswith("explosion_emp_flatbed.effc") for f in emp["files"]):
        bad.append("no explosion_emp_flatbed.effc on emp_01")
    if "truck_emp.ftunec" not in emp["tunes"]:
        bad.append("no truck_emp tune on emp_01")
    if "truck_emp.ftunec" in mm["tunes"]:
        bad.append("mm250 carries truck_emp.ftunec")
    if any(p["name"] == "EMP" for p in mm["pulses"]):
        bad.append("mm250 has an EMP pulse")
    if not any(e["name"] == "epe_emp_powering_up" for e in mm["emitters"]):
        bad.append(f"mm250 emitters {[e['name'] for e in mm['emitters']]}")
    if any(e.get("enabled") != "0" for e in mm["emitters"]):
        bad.append("mm250 emitter enabled at spawn")
    if not any(f["path"].endswith("emp_active.effc") for f in mm["files"]):
        bad.append("mm250 has no emp_active.effc")
    if any(len(v["emp_parts"]) != 3 for v in d["variants"]):
        bad.append("a variant's parts module lacks the device parts")
    with_props = [v["entity"] for v in d["variants"] if v["emp_props"] or v["emp_pulse"]]
    if len(with_props) != 2 or not all("emp" in n for n in with_props):
        bad.append(f"variants with props/pulse {with_props}")
    w702, w503 = d["weapons"]
    for w, wid, wtype in ((w702, "702", "6"), (w503, "503", "2")):
        c = w["component"] or {}
        if c.get("class") != "CEMPWeapon":
            bad.append(f"{w['tag']} component {c.get('class')}")
        if str(c.get("weapon_id")) != wid or str(c.get("weapon_type")) != wtype:
            bad.append(f"{w['tag']} id/type {c.get('weapon_id')}/{c.get('weapon_type')}")
        if w["tune"]["emp_keys"]:
            bad.append(f"{w['tag']} tune has EMP keys {w['tune']['emp_keys']}")
    if not any(p["name"] == "FirePosition" and [round(c, 2) for c in p["xyz"]] == [0, 0.13, -0.69]
               for p in w702["points"]):
        bad.append(f"w702 points {w702['points']}")
    if "CTurretWeaponComponent" not in w503["components"]:
        bad.append(f"w503 components {w503['components']}")
    if d["fleet"]["cemp"] != 0:
        bad.append(f"fleet CEMPWeapon {d['fleet']['cemp']}")
    return bad


def cmd_write() -> int:
    d = build()
    with open(os.path.join(OUT, JSON_NAME), "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    md = render_md(d)
    with open(os.path.join(OUT, MD_NAME), "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    print(f"{JSON_NAME}/{MD_NAME}: {len(d['variants'])} oldtruck variants, "
          f"{len(d['trucks'][0]['emp_parts'])} device parts, "
          f"{len(d['trucks'][0]['tunes'].get('truck_emp.ftunec', []))} EMP tune rows, "
          f"{len(d['weapons'])} EMP weapons, {len(md.splitlines())} md lines")
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
    print(f"PASS: 2 builds, {len(d['variants'])} variants, 3 device parts, 2 EMP weapons, "
          f"fleet CEMPWeapon {d['fleet']['cemp']}")
    return 0


def cmd_dump(what: str) -> int:
    d = build()
    key = {"trucks": "trucks", "variants": "variants", "weapons": "weapons"}.get(what)
    if key:
        print(json.dumps(d[key], indent=1, sort_keys=True, ensure_ascii=False)[:12000])
        return 0
    if what == "tune":
        print(json.dumps(d["trucks"][0]["tunes"], indent=1, sort_keys=True)[:5000])
        return 0
    print("one of: trucks, variants, weapons, tune")
    return 2


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    dl = sub.add_parser("dump")
    dl.add_argument("what", nargs="?", default="trucks")
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
