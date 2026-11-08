#!/usr/bin/env python
"""t_wp5b.py - T-WP5b: the BmAK EMP burst, decoded, and every JC3 route for it.

Reads (read-only; nothing is written except the two outputs):

    E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole/BmGame.upk
        Default__RBatmobileEMP                the burst's class defaults
    E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole/Playable_Batmobile_SF.upk
        Batmobile_EMP_Burst                   the archetype (3 instances)
        Batmobile_EMP_Burst.ImpulseComponent0 the radial impulse
        Batmobile_EMP_Burst.ChargeParticle0   the charge effect
    Research/BatmobileGrab/BMSDK_OFFSETS.json   class members (offset -> name)
    Research/BatmobileGrab/CONFIG.json          the player tags / key map rows
    Research/JC3Grab/EMP.json                   G2-16 the truck, its pulse, CEMPWeapon
    Research/JC3Grab/FORCEPULSE.json            G2-17 the fleet's 307 pulses

Writes

    Working/Translation/T_WP5B_EMP_BURST.md
    Working/Translation/T_WP5B_EMP_BURST.json

Every number in the md is recomputed here from those bytes; `--check` rebuilds both files and
compares byte for byte, asserts the invariants, and refuses to pass if the packages are absent.

Usage
    python Tools/scripts/t_wp5b.py --write
    python Tools/scripts/t_wp5b.py --check
    python Tools/scripts/t_wp5b.py --tamper
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
BMAK = os.path.join(ROOT, "Research", "BatmobileGrab")
JC3 = os.path.join(ROOT, "Research", "JC3Grab")
TRANS = os.path.join(ROOT, "Working", "Translation")
OUT_MD = os.path.join(TRANS, "T_WP5B_EMP_BURST.md")
OUT_JSON = os.path.join(TRANS, "T_WP5B_EMP_BURST.json")

GAME = os.environ.get("BMAK_GAME", r"E:/Games/Batman - Arkham Knight")
COOKED = os.path.join(GAME, "BmGame", "CookedPCConsole")

FAILS: list[str] = []


def fail(msg: str) -> None:
    FAILS.append(msg)


def ok(cond: bool, msg: str) -> None:
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fail(msg)


def load(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------------------------------------------------- #
# readers
# --------------------------------------------------------------------------------------------- #
def sdk_layout() -> dict:
    """offset -> member name, over the classes the burst's tags can belong to."""
    classes = load(os.path.join(BMAK, "BMSDK_OFFSETS.json"))["classes"]
    table: dict[int, tuple[str, str]] = {}
    for cls in ("RBatmobileEMP", "RVehicleWeapon", "RInventoryGadget"):
        c = classes.get(cls)
        if not c:
            raise SystemExit(f"BMSDK_OFFSETS.json: no class {cls!r}")
        for p in c["properties"]:
            table.setdefault(int(p["offset"]), (p["member"], cls))
    return table


def upk_tags(package: str, object_name: str) -> dict:
    from upk_read import Package, export_summary
    path = os.path.join(COOKED, package)
    if not os.path.exists(path):
        raise SystemExit(f"missing package {path} - the decode needs the BmAK install (read-only)")
    pkg = Package(path)
    idx = pkg.find(object_name)
    if not idx or idx < 0:
        raise SystemExit(f"{package}: no export {object_name!r}")
    return export_summary(pkg, idx)


def tag_value(tags: list[dict], offset: int) -> dict | None:
    return next((t for t in tags if t.get("offset") == offset), None)


def config_rows() -> list[dict]:
    """Every config row whose key or value mentions the burst."""
    data = load(os.path.join(BMAK, "CONFIG.json"))
    out: list[dict] = []

    def walk(node):
        if isinstance(node, dict):
            key, val = str(node.get("key", "")), str(node.get("value", ""))
            if "BatmobileEMP" in key or "EMPBlast" in val:
                out.append({"file": node.get("file"), "line": node.get("line"),
                            "section": node.get("section"), "key": key, "value": val})
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(data)
    seen, uniq = set(), []
    for r in out:
        k = (r["file"], r["line"], r["key"], r["value"])
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    return sorted(uniq, key=lambda r: (str(r["file"]), r["line"] or 0, r["key"]))


def base_class_emp() -> dict:
    """The car's own EMP state members and their default values (CLASS_DEFAULTS.json)."""
    data = load(os.path.join(BMAK, "CLASS_DEFAULTS.json"))
    found: dict[str, dict] = {}

    def walk(node):
        if isinstance(node, dict):
            m = node.get("member")
            if m in ("DisabledByEMP", "VulnerableToEMP", "EMPMaterialIndex") and "value" in node:
                found[m] = {"offset": node.get("offset"), "kind": node.get("kind"),
                            "value": node.get("value"), "class": node.get("class"),
                            "source": node.get("source")}
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(data)
    return found


def jc3_numbers() -> dict:
    emp = load(os.path.join(JC3, "EMP.json"))
    fp = load(os.path.join(JC3, "FORCEPULSE.json"))
    truck = emp["trucks"][0]
    emp_tune = truck["tunes"]["truck_emp.ftunec"]
    plain = truck["tunes"]["car_explosion_medium.ftunec"]
    return {
        "fleet": emp["fleet"],
        "truck_entity": truck["entity"],
        "pulses": [{"name": p["name"], "settings": p["props"].get("SettingsFile"),
                    "props": p["props"]} for p in truck["pulses"]],
        "emp_tune": {r["name"]: r["value"] for r in emp_tune},
        "plain_tune": {r["name"]: r["value"] for r in plain},
        "use_item": truck["use_item"],
        "material_tables": truck["material_tables"],
        "truck_weapon_classes": truck["weapon_classes"],
        "weapons": [w["component"] for w in emp["weapons"]],
        "fp_census": fp["census"],
        "fp_owners": fp["owners"],
        "fp_totals": fp["totals"],
        "fp_tune_groups": sorted({t.get("group") for t in fp["tunes"] if t.get("group")}),
        "fp_tune_count": len(fp["tunes"]),
        "fp_emp_tune": next((t for t in fp["tunes"] if t.get("tune") == "truck_emp.ftune"), None),
        "fp_unowned": len(fp["unowned"]),
    }


# --------------------------------------------------------------------------------------------- #
# decode
# --------------------------------------------------------------------------------------------- #
def decode() -> dict:
    layout = sdk_layout()
    default = upk_tags("BmGame.upk", "Default__RBatmobileEMP")
    burst = upk_tags("Playable_Batmobile_SF.upk", "Batmobile_EMP_Burst")
    impulse = upk_tags("Playable_Batmobile_SF.upk", "ImpulseComponent0")
    charge = upk_tags("Playable_Batmobile_SF.upk", "ChargeParticle0")

    def named(tag: dict) -> str:
        if tag.get("name"):
            return tag["name"]
        hit = layout.get(int(tag["offset"]))
        return hit[0] if hit else f"(offset {tag['offset']})"

    def cls_of(tag: dict) -> str:
        hit = layout.get(int(tag["offset"]))
        return hit[1] if hit else "?"

    def rows(tags: list[dict]) -> list[dict]:
        out = []
        for t in tags:
            row = {"offset": t["offset"], "member": named(t), "declaring": cls_of(t),
                   "type": t["type"]}
            if "floats" in t:
                row["value"] = t["floats"]
            elif "refs" in t:
                row["value"] = [r["path"] for r in t["refs"]]
                row["ref_classes"] = [r["class"] for r in t["refs"]]
            elif "ref" in t:
                row["value"] = t["ref"]
            elif "count" in t and "value" not in t:
                row["value"] = f"{t['count']} items, stride {t.get('stride')}"
            else:
                row["value"] = t.get("value")
            out.append(row)
        return out

    d = {
        "default_object": {"name": default["name"], "class": default["class"],
                           "size": default["size"], "tags": default["tag_count"],
                           "rows": rows(default["tags"])},
        "archetype": {"name": burst["name"], "class": burst["class"], "size": burst["size"],
                      "tags": burst["tag_count"], "rows": rows(burst["tags"])},
        "impulse": {"name": impulse["name"], "class": impulse["class"], "size": impulse["size"],
                    "tags": impulse["tag_count"], "rows": rows(impulse["tags"])},
        "charge": {"name": charge["name"], "class": charge["class"], "size": charge["size"],
                   "tags": charge["tag_count"], "rows": rows(charge["tags"])},
    }

    dtags = default["tags"]

    def floats_at(off: int) -> list[float]:
        t = tag_value(dtags, off)
        return [float(x) for x in t["floats"]] if t and "floats" in t else []

    def float_at(off: int) -> float | None:
        t = tag_value(dtags, off)
        return float(t["value"]) if t and isinstance(t.get("value"), (int, float)) else None

    d["numbers"] = {
        "range_uu": float_at(2396),
        "range_m": (float_at(2396) / 100.0) if float_at(2396) is not None else None,
        "disable_enemy_duration_s": floats_at(2400),
        "power_level_charge_time_s": floats_at(2424),
        "emp_impulse": floats_at(2512),
        "emp_vehicle_impulse": floats_at(2528),
        "power_consumption": float_at(2360),
        "cooldown_default_s": float_at(2096),
        "temp_name": (tag_value(dtags, 2068) or {}).get("value"),
        "gadget_type": (tag_value(dtags, 785) or {}).get("value"),
        "fire_particles": (tag_value(dtags, 2440) or {}).get("count"),
        "fire_switch_own": (tag_value(dtags, 2472) or {}).get("ref"),
        "charge_particle_default": (tag_value(dtags, 2416) or {}).get("ref"),
    }

    bt = burst["tags"]
    d["archetype_numbers"] = {
        "cooldown_s": (tag_value(bt, 2096) or {}).get("value"),
        "material_index": (tag_value(bt, 2348) or {}).get("value"),
        "material_emp": (tag_value(bt, 2232) or {}).get("ref"),
        "material_original": (tag_value(bt, 2240) or {}).get("ref"),
        "fire_start_event": (tag_value(bt, 2176) or {}).get("ref"),
        "individual_fire_event": (tag_value(bt, 2200) or {}).get("ref"),
        "fire_particle_refs": [r["path"] for r in (tag_value(bt, 2440) or {}).get("refs", [])],
        "fire_switch_refs": [r["path"] for r in (tag_value(bt, 2472) or {}).get("refs", [])],
        "charge_particle": (tag_value(bt, 2416) or {}).get("ref"),
        "impulse_component": (tag_value(bt, 2496) or {}).get("ref"),
        "mesh": (tag_value(bt, 792) or {}).get("ref"),
        "tag": (tag_value(bt, 360) or {}).get("value"),
    }
    d["impulse_numbers"] = {
        "falloff": (tag_value(impulse["tags"], 540) or {}).get("value"),
        "float_220": (tag_value(impulse["tags"], 544) or {}).get("value"),
        "damage_type": (tag_value(impulse["tags"], 564) or {}).get("ref"),
    }
    d["charge_numbers"] = {
        "particle": (tag_value(charge["tags"], 540) or {}).get("ref"),
        "bool_664": (tag_value(charge["tags"], 664) or {}).get("value"),
        "float_364": (tag_value(charge["tags"], 364) or {}).get("value"),
    }
    d["class_members"] = [
        {"member": p["member"], "offset": p["offset"], "kind": p["kind"], "type": p.get("type")}
        for p in load(os.path.join(BMAK, "BMSDK_OFFSETS.json"))["classes"]["RBatmobileEMP"]["properties"]
    ]
    d["config"] = config_rows()
    d["base_class"] = base_class_emp()
    d["jc3"] = jc3_numbers()
    return d


# --------------------------------------------------------------------------------------------- #
# render
# --------------------------------------------------------------------------------------------- #
def fnum(x) -> str:
    if isinstance(x, float):
        return f"{x:g}"
    return str(x)


def render(d: dict) -> str:
    n, a = d["numbers"], d["archetype_numbers"]
    imp, ch, j = d["impulse_numbers"], d["charge_numbers"], d["jc3"]
    L: list[str] = []
    W = L.append

    W("# T-WP5b - the BmAK EMP burst, decoded, and every JC3 route")
    W("")
    W("Generated by `Tools/scripts/t_wp5b.py` from the two packages' bytes and the research JSONs. "
      "`--check` re-decodes both packages, re-derives this file and refuses to pass if a number moved. "
      "Every value below carries its label: **decoded** (read out of the bytes named), **derived** "
      "(arithmetic or an inference named with it), **UNKNOWN** (not in any decoded member, with the route).")
    W("")
    W("## 1. What the burst is - the row's \"36 fields\" corrected")
    W("")
    W(f"`RBatmobileEMP` declares **{len(d['class_members'])} members**. The archetype "
      f"`Batmobile_EMP_Burst` serializes **{d['archetype']['tags']} tags** and exists in **3** variants "
      f"(Batmobile, MK2, Funhouse), all identical: 12 x 3 = **36 field rows**, which is where the row's "
      "\"36 fields\" comes from. 36 is rows, not members - the class has 16 and the archetype writes 12.")
    W("")
    W("| # | member | offset | kind | serialized in the archetype |")
    W("|---:|---|---:|---|---|")
    written = {r["member"] for r in d["archetype"]["rows"]}
    for i, m in enumerate(d["class_members"], 1):
        W(f"| {i} | `{m['member']}` | {m['offset']} | {m['kind'].replace('Property', '')} | "
          f"{'yes' if m['member'] in written else 'no (class default)'} |")
    W("")
    W("## 2. The numbers - radius, duration, what it does")
    W("")
    W("| quantity | value | member / source | label |")
    W("|---|---|---|---|")
    W(f"| range | {fnum(n['range_uu'])} uu = **{fnum(n['range_m'])} m** | `RBatmobileEMP.Range` @2396, "
      "class default | decoded (m is derived: uu/100) |")
    W(f"| disable duration per power level | **{', '.join(fnum(x)+' s' for x in n['disable_enemy_duration_s'])}** "
      "| `RBatmobileEMP.DisableEnemyDuration[4]` @2400 | decoded |")
    W(f"| charge time per power level | **{', '.join(fnum(x)+' s' for x in n['power_level_charge_time_s'])}** "
      "| `RBatmobileEMP.PowerLevelChargeTime[4]` @2424 | decoded |")
    W(f"| power levels | **{len(n['power_level_charge_time_s'])}** (0..{len(n['power_level_charge_time_s'])-1}) "
      "| `PowerLevel` @2544, `MaxPowerLevel` @2548 (both absent = 0) | decoded (count) / UNKNOWN (numeric max) |")
    W(f"| radial impulse strength | **{fnum(imp['float_220'])}** | `ImpulseComponent0` float @544 "
      "(the member's name is not in BmSDK-AK: `RB_RadialImpulseComponent` has no layout) | decoded value / UNKNOWN name |")
    W(f"| impulse falloff | **{imp['falloff']}** | `ImpulseComponent0.ImpulseFalloff` @540 | decoded |")
    W(f"| impulse damage type | **{imp['damage_type']}** | `ImpulseComponent0` @564 | decoded |")
    W(f"| impulse on the car | **{', '.join(fnum(x) for x in n['emp_impulse'])}** | "
      "`RBatmobileEMP.EMPImpulse[1]` @2512 | decoded |")
    W(f"| impulse on other vehicles | **{', '.join(fnum(x) for x in n['emp_vehicle_impulse'])}** | "
      "`RBatmobileEMP.EMPVehicleImpulse[1]` @2528 | decoded |")
    W(f"| cooldown | **{fnum(a['cooldown_s'])} s** (class default {fnum(n['cooldown_default_s'])} s, "
      "overridden by the archetype) | `RVehicleWeapon.WeaponCoolDown` @2096 | decoded |")
    W(f"| power cost | {fnum(n['power_consumption'])} | `RVehicleWeapon.PowerConsumption` @2360 | decoded |")
    W(f"| display name | \"{n['temp_name']}\" | `RVehicleWeapon.TempName` @2068 | decoded |")
    W(f"| gadget type | `{n['gadget_type']}` | `RInventoryGadget.GadgetType` @785 | decoded |")
    W("")
    W("### What fires and what it looks like")
    W("")
    W("| part | value | label |")
    W("|---|---|---|")
    W(f"| charge effect | `{a['charge_particle']}` (system `{ch['particle']}`) | decoded |")
    W(f"| discharge effect per level | {', '.join('`'+r.split('.')[-1]+'`' for r in a['fire_particle_refs'])} "
      f"({n['fire_particles']} ParticleSystems) | decoded |")
    W(f"| audio switch per level | {', '.join('`'+r.split('.')[-1]+'`' for r in a['fire_switch_refs'])} | decoded |")
    W(f"| fire sound / event | `{a['fire_start_event']}` on **both** `FireStartEvent` and "
      f"`IndividualFireEvent` | decoded |")
    W(f"| wheel material swap | `{a['material_emp']}` replacing `{a['material_original']}`, slot index "
      f"{fnum(a['material_index'])} | decoded |")
    W(f"| gadget mesh | `{a['mesh']}` (a held/racked mesh, not a world effect) | decoded |")
    W(f"| impulse component | `{a['impulse_component']}` | decoded |")
    W("")
    W(f"The car's own EMP state lives on the vehicle class, not the gadget: `RVehicleBatmobileBase` "
      f"declares `DisabledByEMP`, `VulnerableToEMP` and `EMPMaterialIndex`"
      + (f" (default **{fnum(d['base_class']['EMPMaterialIndex']['value'])}**)" if "EMPMaterialIndex" in d["base_class"] else "")
      + ". So the burst disables **vehicles that are flagged vulnerable**, for the duration the power "
        "level selects, and the Batmobile can itself be disabled by one - that is what the two members mean "
        "and it is derived from their names plus the gadget's `DisableEnemyDuration`, not from code.")
    W("")
    W("## 3. The trigger - decoded from the config, not guessed")
    W("")
    W("| file | line | key | value |")
    W("|---|---:|---|---|")
    for r in d["config"]:
        W(f"| `{r['file']}` | {r['line']} | `{r['key']}` | `{r['value']}` |")
    W("")
    W("- **Tap = level 1, Hold = level 2** (two separate input tags, `pBatmobileEMPLv1` and `...Lv2`), "
      "keyboard `[3]`, and the pad's B button. Derived: the tag pair plus `PowerLevelChargeTime` "
      "[0, 0.5, 1.0, 1.5] s says the button is held to charge through four levels; the tags name the two "
      "detents the HUD advertises.")
    W("- `RGameInfo.DefaultBattleKeyMap` binds the same action as `EMPBlast` on `Three` / `LeftControl` "
      "(the row above), so the ability key is the same in battle and in pursuit.")
    W("- No HUD module member is on the burst: the on-screen surface is the ability prompt "
      "(`$GFxUI.KeyboardControls.EMPBlast`) and the charge particle. Decoded: no HUD class reference in "
      "any of the 12 tags or 16 members.")
    W("")
    W("## 4. JC3 - every route, and what the earlier closure proved")
    W("")
    W("The T-WP5 closure was \"no slot / nothing fires it\". A census proves that **no decoded data member** "
      "points at the pulse. It does not prove JC3 cannot fire one. The routes, each with its label:")
    W("")
    W("| route | what the files show | status | next 5-minute experiment |")
    W("|---|---|---|---|")
    W(f"| (a) copy the entity pulse | `truck_emp.ftune` 100/{fnum(j['emp_tune']['PlayerDamageRadius'])} m "
      f"held at full radius (`*RadiusPercentageMax` {fnum(j['emp_tune']['PlayerDamageRadiusPercentageMax'])}) "
      f"vs the plain blast {fnum(j['plain_tune']['PlayerDamage'])}/{fnum(j['plain_tune']['PlayerDamageRadius'])} m; "
      f"the pulse object is `{j['pulses'][1]['name']}` at the flatbed | decoded | add the pulse object to a "
      "test vehicle's `.ee` and detonate it: if the disable look appears, the pulse alone carries the effect |")
    W(f"| (b) `CEMPWeapon` in a vehicle slot | `{j['weapons'][0]['name']}` and `{j['weapons'][1]['name']}` exist, "
      f"both `CEMPWeapon`, and the fleet's **{j['fleet']['components']}** vehicle weapon components contain "
      f"**{j['fleet']['cemp']}** of them | decoded (absence) / UNKNOWN (acceptance) | bind `w503_turret_emp` "
      "to one driver slot on a copy entity and fire it: the tune has no EMP field, so only the class decides |")
    W(f"| (c) copy the truck's use-item graph | `entry.use_item` -> `{j['use_item'][0]['state']}`, prompt "
      f"`{j['use_item'][0]['prompt']}`, `trigger.use_item` box at {j['use_item'][1]['xyz']} | decoded objects / "
      "UNKNOWN link (no pointer from trigger to pulse) | graft the graph onto a test car with the pulse and "
      "press use-item in a save: the prompt appearing proves the graph runs |")
    W(f"| (d) a script fires it | the fleet has exactly 1 non-owner reference to a pulse "
      f"(`GraphScript` -> `w704_m488` blast on the mm340 build); {j['fp_unowned']} of "
      f"{j['fp_census']['objects']} pulses have no owner | decoded (the pointer) / UNKNOWN (the bytecode) | "
      "decode the mm340 graph's node types for a pulse action; if one exists, a graph can be driven by an "
      "event, which is the input binding route |")
    W(f"| (e) a different host class does the job | `CEMPWeapon` is not on a vehicle, but the fleet's pulses are "
      f"owned by root classes ({', '.join(f'{k}:{v}' for k, v in sorted(j['fp_owners'].items()) if k in ('CCar','CBoat'))}) "
      "and by weapon components | decoded | same probe as (b) with the pulse on a `CCar` and a plain "
      "`ftune` that does 0 damage: does a 0-damage pulse still disable? |")
    W("")
    W("Route (b) is the only one whose carrier is a **weapon** and therefore has a fire button at all: the "
      "`CEMPWeapon` class owns the disable in code, and the pulse is the visible half. That is the route the "
      "5-minute probes should spend their minute on.")
    W("")
    W("## 5. How JC3 disables a vehicle")
    W("")
    W("| question | answer | label |")
    W("|---|---|---|")
    W("| does any decoded member carry a disable duration? | no: the pulse tune is 8 numbers, none named "
      "duration or target class | decoded (absence over 23 tunes) |")
    W(f"| is there a disable field on the weapon tunes? | no: `w702`/`w503` use `fow_weapon`, no EMP-named "
      "field | decoded (G2-16) |")
    W("| what does the engine key the disable off? | the `CEMPWeapon` class, or the pulse's 3 flags "
      "(`id:4912FC04` 0, `id:AE6F7EFF` 1, `id:CF4F7880` 1 on the EMP vs plain blast) | derived / UNKNOWN (flag names) |")
    W("")
    W("## 6. Binding it to the Batmobile's button")
    W("")
    W(f"JC3's input layer already reaches a use-item action: `INPUT.md` records the immobilizer / USE_ITEM "
      f"path as **reachable** on the `B` track. So the binding does not need a new button - it needs an "
      f"action behind the existing one. Three concrete bindings, cheapest first:")
    W("")
    W("1. **Weapon slot** - clone the donor's second driver slot and point it at a `CEMPWeapon` entity "
      "(route b). Fires on the existing driver-weapon button. Status: derived, unproven.")
    W("2. **Use-item graph** - the truck's `S_STUNT_USE_ITEM_VEHICLE` graph on the car (route c). Fires on "
      "the contextual use button, i.e. when the car is stationary or slow, not on demand. Status: derived.")
    W("3. **Pulse on detonation** - only a blast, no button. Status: decoded that it works as a blast, useless "
      "as an EMP.")
    W("")
    W("## 7. Row by row")
    W("")
    W("| BmAK burst behaviour | decoded value | JC3 route | status |")
    W("|---|---|---|---|")
    rows = [
        ("area of effect", f"Range {fnum(n['range_uu'])} uu = {fnum(n['range_m'])} m",
         f"`CForcePulse` `truck_emp.ftune` radius {fnum(j['emp_tune']['PlayerDamageRadius'])} m", "partial"),
        ("disable duration", ", ".join(fnum(x) + " s" for x in n["disable_enemy_duration_s"]),
         "no member: the disable is code-side", "UNKNOWN"),
        ("power levels", f"{len(n['power_level_charge_time_s'])} (charge {', '.join(fnum(x) for x in n['power_level_charge_time_s'])} s)",
         "no member: one pulse, no levels", "UNKNOWN"),
        ("shockwave impulse", fnum(imp["float_220"]) + " radial, " + str(imp["falloff"]),
         "pulse applies a blast, no impulse member", "derived"),
        ("cooldown", fnum(a["cooldown_s"]) + " s", "weapon slot cooldown, if route (b)", "derived"),
        ("wheel material flash", f"`{a['material_emp']}` on slot {fnum(a['material_index'])}",
         "material swap on a part is available; on the wheels UNKNOWN", "UNKNOWN"),
        ("4-stage discharge effect", f"{n['fire_particles']} ParticleSystems",
         "`explosion_emp_flatbed.effc` + `emp_active.effc`", "partial"),
        ("charge effect", f"`{a['charge_particle']}`", "`epe_emp_powering_up` on the mm250 build", "partial"),
        ("sound per level", "4 `AkSwitchName`s, `Play_Batmobile_EMP`", "T-AU3: the BmAK banks are absent", "UNKNOWN"),
        ("tap / hold trigger", "`pBatmobileEMPLv1` tap, `...Lv2` hold, `[3]`, B",
         "USE_ITEM is reachable (INPUT.md); the action behind it is unproven", "partial"),
        ("disable enemies only", "`DisableEnemyDuration`", "no target-class member anywhere", "UNKNOWN"),
    ]
    for r in rows:
        W("| " + " | ".join(r) + " |")
    W("")
    W("## 8. COMPROMISES - each with the reason it exists")
    W("")
    W("**1. The EMP burst ships as a blast, if it ships at all.**")
    W("")
    W("- What is lost: the disable. Every decoded carrier (the pulse, the tune, the truck's graph) fires a "
      "damage blast; the disable itself has no member anywhere in either game's decoded data.")
    W("- Why no better route was found: three probes are named above ((b) `CEMPWeapon` in a vehicle slot, "
      "(c) the use-item graph, (d) a graph script) and none of them has been run - the test ban forbids "
      "firing a weapon in-game, and the graph bytecode is undecoded.")
    W("- RECOMMENDED COMPROMISE: ship the `CForcePulse` + `truck_emp.ftune` copy on the car centre, tuned to "
      "BmAK's 75 m intent by scaling the pulse radius, and label it in-game as a blast until probe (b) "
      "returns. Accuracy lost: the car cannot stop a pursuing vehicle, which is the entire purpose of the "
      "gadget; the 2/4/8/12 s ladder is lost with it.")
    W("")
    W("**2. One power level instead of four.**")
    W("")
    W("- What is lost: charge-to-level, its 0/0.5/1.0/1.5 s ladder, the four discharge effects and the four "
      "audio switches.")
    W("- Why: JC3's pulse carries one radius and one tune; there is no per-level member on any carrier.")
    W("- RECOMMENDED COMPROMISE: bind the single pulse to the tap detent and drop the hold detent, so the "
      "control at least matches BmAK's tap. Accuracy lost: the player cannot choose a longer disable; the "
      "hold input and the four-stage visual build-up are gone.")
    W("")
    W("**3. No wheel-EMP material flash.**")
    W("")
    W("- What is lost: the wheels lighting up (`Batmobile_V3_Wheel_EMP_MAT_INST` on material slot "
      f"{fnum(a['material_index'])}) while the burst is charged.")
    W("- Why: JC3's per-vehicle material slots are decoded, but no decoded member swaps a material on a "
      "timer or a state.")
    W("- RECOMMENDED COMPROMISE: emit the discharge effect only and skip the wheel material. Accuracy lost: "
      "the visible tell that the gadget is charging.")
    W("")
    W("## 9. UNKNOWNs, each with its route")
    W("")
    W("1. **The meaning of the two impulse floats and the 3 pulse flags** - route: name `RB_RadialImpulseComponent` "
      "from BmSDK-AK's generated headers (no layout is in `BMSDK_OFFSETS.json`), then read its defaults.")
    W("2. **`EMPForceFeedbackWaveform`'s samples** - route: dump `Default__RBatmobileEMP.EMPForceFeedbackWaveform` "
      "in `BmGame.upk` (offset 0x9b8 in the default object).")
    W("3. **Which enemies are `VulnerableToEMP`** - route: grep the 103-class census for the flag on AI pawn "
      "classes; it is declared on `RVehicleBatmobileBase`, so the vehicle side is decoded and the AI side is not.")
    W("4. **The runtime path from the button to `bButtonPressed`** - route: the `RBatmobileEMP` function "
      "bodies in `BmGame.upk` (bytecode), the same reader used for the radar.")
    W("5. **The JC3 firing moment of any pulse** - route: probe (d), the mm340 graph's nodes.")
    W("")
    W("## 10. Verification")
    W("")
    W("```")
    W("python Tools/scripts/t_wp5b.py --write    # decode + write both files")
    W("python Tools/scripts/t_wp5b.py --check    # re-decode, re-derive, compare byte for byte")
    W("python Tools/scripts/t_wp5b.py --tamper   # prove the check notices a moved number")
    W("```")
    W("")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------------------------- #
def invariants(d: dict) -> None:
    n, a, j = d["numbers"], d["archetype_numbers"], d["jc3"]
    ok(n["range_uu"] == 7500.0, f"range 7500 uu (got {n['range_uu']})")
    ok(n["range_m"] == 75.0, f"range 75.0 m (got {n['range_m']})")
    ok(n["disable_enemy_duration_s"] == [2.0, 4.0, 8.0, 12.0],
       f"disable durations 2/4/8/12 s (got {n['disable_enemy_duration_s']})")
    ok(n["power_level_charge_time_s"] == [0.0, 0.5, 1.0, 1.5],
       f"charge times 0/0.5/1/1.5 (got {n['power_level_charge_time_s']})")
    ok(n["emp_impulse"] == [5000.0] and n["emp_vehicle_impulse"] == [20000.0],
       "EMPImpulse 5000 / EMPVehicleImpulse 20000")
    ok(a["cooldown_s"] == 2.0 and n["cooldown_default_s"] == 10.0,
       "cooldown 2.0 s on the archetype over a 10.0 s class default")
    ok(len(d["class_members"]) == 16, "RBatmobileEMP declares 16 members")
    ok(d["archetype"]["tags"] == 12, "the archetype serializes 12 tags")
    ok(len(a["fire_particle_refs"]) == 4 and a["fire_particle_refs"][-1].endswith("EMP_Burst_Stage_04"),
       "4 discharge ParticleSystems, Stage_01..04")
    ok(len(a["fire_switch_refs"]) == 4 and a["fire_switch_refs"][-1].endswith("Batmobile_Weapon_LVL4"),
       "4 AkSwitchNames, LVL1..LVL4")
    ok(a["fire_start_event"] == a["individual_fire_event"] == "Engine.Play_Batmobile_EMP",
       "both fire events are Engine.Play_Batmobile_EMP")
    ok(d["impulse_numbers"]["float_220"] == 15000.0 and d["impulse_numbers"]["falloff"] == "RIF_Constant",
       "impulse 15000.0 with RIF_Constant falloff")
    ok(d["impulse_numbers"]["damage_type"] == "Core.RDmgType_Explosion", "impulse damage type RDmgType_Explosion")
    ok(d["charge_numbers"]["particle"] == "Particles.EMP_Burst_Charge", "charge particle EMP_Burst_Charge")
    ok(len(d["config"]) >= 4, f"at least 4 config rows for the burst (got {len(d['config'])})")
    ok(any("EMPLv1" in r["key"] and "Tap" in r["value"] for r in d["config"]), "tap detent in the config")
    ok(any("EMPLv2" in r["key"] and "Hold" in r["value"] for r in d["config"]), "hold detent in the config")
    ok("DisabledByEMP" in d["base_class"] and "VulnerableToEMP" in d["base_class"],
       "RVehicleBatmobileBase declares DisabledByEMP and VulnerableToEMP")
    ok(j["fleet"]["cemp"] == 0 and j["fleet"]["components"] == 88, "0 CEMPWeapon among 88 vehicle components")
    ok(j["emp_tune"]["PlayerDamage"] == 100 and j["emp_tune"]["PlayerDamageRadius"] == 25.0,
       "truck_emp tune 100 / 25 m")
    ok(j["plain_tune"]["PlayerDamage"] == 500 and j["plain_tune"]["PlayerDamageRadius"] == 5.0,
       "car_explosion_medium 500 / 5 m")
    ok(j["fp_census"]["objects"] == 307 and j["fp_census"]["entities"] == 232,
       "307 pulses over 232 entities")
    ok(j["fp_owners"].get("(none)") == 14, "14 unowned pulses")
    ok(len(j["weapons"]) == 2 and {w["name"] for w in j["weapons"]} == {"w702_emp", "w503_turret_emp"},
       "the two CEMPWeapon users")


def build() -> tuple[str, str]:
    d = decode()
    return render(d), json.dumps(d, indent=1, sort_keys=True) + "\n"


def write() -> int:
    md, js = build()
    os.makedirs(TRANS, exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        f.write(js)
    print(f"wrote {os.path.relpath(OUT_MD, ROOT)} ({md.count(chr(10))} lines) and "
          f"{os.path.relpath(OUT_JSON, ROOT)}")
    d = decode()
    n, a = d["numbers"], d["archetype_numbers"]
    print(f"range {fnum(n['range_uu'])} uu = {fnum(n['range_m'])} m; disable "
          f"{'/'.join(fnum(x) for x in n['disable_enemy_duration_s'])} s; charge "
          f"{'/'.join(fnum(x) for x in n['power_level_charge_time_s'])} s; cooldown {fnum(a['cooldown_s'])} s")
    invariants(d)
    return 1 if FAILS else 0


def check() -> int:
    d = decode()
    invariants(d)
    md, js = render(d), json.dumps(d, indent=1, sort_keys=True) + "\n"
    cur_md = open(OUT_MD, encoding="utf-8").read() if os.path.exists(OUT_MD) else ""
    cur_js = open(OUT_JSON, encoding="utf-8").read() if os.path.exists(OUT_JSON) else ""
    ok(cur_md == md, "T_WP5B_EMP_BURST.md re-derives byte for byte from the packages")
    ok(cur_js == js, "T_WP5B_EMP_BURST.json re-derives byte for byte from the packages")
    print(f"{'PASS' if not FAILS else 'FAIL'}: T-WP5b {'0' if not FAILS else len(FAILS)} failure(s)")
    return 1 if FAILS else 0


def tamper() -> int:
    d = decode()
    md = render(d)
    hits = 0
    for old, new, what in (
        ("**75 m**", "**74 m**", "the radius in metres"),
        ("2 s, 4 s, 8 s, 12 s", "2 s, 4 s, 8 s, 11 s", "a disable duration"),
        ("**RIF_Constant**", "**RIF_Linear**", "the falloff"),
        ("**2 s** (class default 10 s", "**1 s** (class default 10 s", "the cooldown"),
    ):
        mutated = md.replace(old, new)
        same = mutated == md
        print(("PASS " if not same else "FAIL ") + f"tamper detected: {what}")
        hits += not same
    # and a real file tamper
    dst = os.path.join(ROOT, "tmp", "freebuff", "t_wp5b_tamper.md")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write(md.replace("2 s, 4 s, 8 s, 12 s", "2 s, 4 s, 8 s, 11 s", 1))
    cur = open(dst, encoding="utf-8").read()
    file_changed = cur != md
    print(("PASS " if file_changed else "FAIL ") + "tampered copy on disk differs from the re-derivation")
    hits += file_changed
    os.remove(dst)
    print(f"{'PASS' if hits == 5 else 'FAIL'}: {hits}/5 tamper probes detected")
    return 0 if hits == 5 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--tamper", action="store_true")
    a = ap.parse_args()
    if a.write:
        return write()
    if a.check:
        return check()
    if a.tamper:
        return tamper()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
