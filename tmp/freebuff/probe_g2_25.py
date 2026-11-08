"""Independent re-derivation for G2-25 (does not import jc3hudwpn). Plain grep/awk style checks."""
import json
import os
import re
import sys

HUD = r"E:\Modding\_JC3grab\hud\dec\scripts"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
hud = open(os.path.join(HUD, "hud.as"), encoding="utf-8", errors="replace").read()

out = {}
# 1. script count + who defines/calls the two functions
out["as_files"] = sum(1 for _ in os.walk(HUD) for n in _[2] if n.endswith(".as")) if False else \
    sum(1 for b, _d, ns in os.walk(HUD) for n in ns if n.endswith(".as"))
for fn in ("InitVehicleWeapons", "UpdateVehicleWeapons", "UpdateWeaponReticle",
           "ShowMissileLocked"):
    defs = len(re.findall(r"function\s+" + fn + r"\s*\(", hud))
    called = len(re.findall(r"(?<!function )" + fn + r"\(", hud)) - 0
    # count call lines that are not the definition line
    lines = [l for l in hud.splitlines() if fn + "(" in l and "function " + fn not in l]
    out[fn] = {"defs": defs, "call_lines": len(lines),
               "callers": sorted({re.search(r"this\." + fn, l) is not None for l in lines})[:3]}
# 2. arg counts by plain split of the parameter list
for fn in ("InitVehicleWeapons", "UpdateVehicleWeapons", "UpdateWeaponReticle"):
    m = re.search(r"function\s+" + fn + r"\(([^)]*)\)", hud)
    out[fn]["args"] = len([p for p in m.group(1).split(",") if p.strip()])
# 3. slot array + the on-foot constant
out["slot_array"] = hud.count("MCI_vehicle_weapons0") , hud.count("MCI_vehicle_weapons1")
out["E_NUM_WEAPON_SLOTS"] = int(re.search(r"E_NUM_WEAPON_SLOTS:\* = (\d+)", hud).group(1))
out["vehicle_slot_consts"] = re.findall(r"EVEHICLE_WEAPON_SLOT_\w+:\w+ = \d+", hud)
# 4. overcharge alpha, cooldown degrees
m = re.search(r"if\(is_overcharged\)\s*\{\s*bullet_bar_alpha = ([\d.]+);", hud)
out["overcharge_alpha"] = m.group(1) if m else None
out["cooldown_deg"] = re.search(r"weapon_cooldown \* (\d+)", hud).group(1)
# 5. heat anywhere in the vehicle-weapon API
out["heat_in_signatures"] = [l.strip() for l in hud.splitlines()
                             if "function " in l and re.search(r"\b(Init|Update)VehicleWeapons\b", l)
                             and "heat" in l.lower()]
out["heat_state_consts"] = len(re.findall(r"HEAT_STATE_\w+:int = \d+",
                                          open(os.path.join(HUD, "hud_code", "heat", "heat.as"),
                                               encoding="utf-8", errors="replace").read()))
# 6. POI types and the lock-on one
out["poi_types"] = len(re.findall(r"private const POI_TYPE_\w+:int = \d+;", hud))
out["lock_on"] = re.search(r"POI_TYPE_LOCK_ON_TARGET:int = (\d+)", hud).group(1)
out["lock_on_rot"] = re.search(r"LOCK_ON_TARGET_ROTATION_TIME:Number = ([\d.]+)",
                               open(os.path.join(HUD, "hud_code", "poi.as"), encoding="utf-8",
                                    errors="replace").read()).group(1)
# 7. icon ids straight from the index
ids = set()
n_files = 0
for line in open(os.path.join(ROOT, "Research", "JC3Grab", "INDEX.jsonl"), encoding="utf-8"):
    if "/weapon_icons/" not in line:
        continue
    p = json.loads(line)["path"].split("/")[-1]
    m = re.fullmatch(r"(\d+)(_sm)?\.ddsc", p)
    if m:
        ids.add(int(m.group(1)))
        n_files += 1
out["icon_ids"] = len(ids)
out["icon_files"] = n_files
# 8. BmAK setters
iface = json.load(open(os.path.join(ROOT, "Research", "BatmobileGrab", "HUD_INTERFACES.json"),
                       encoding="utf-8"))
out["batmobile_setters"] = len(iface["HudModuleBatmobile"]["setters"])
out["all_setters"] = sum(len(v["setters"]) for v in iface.values())
out["setters_with_heat"] = [s["name"] for v in iface.values() for s in v["setters"]
                            if "heat" in s["name"].lower()]
print(json.dumps(out, indent=1, sort_keys=True))
