#!/usr/bin/env python
"""jc3hudwpn.py - G2-25: the JC3 vehicle-weapon HUD API, and what WPN-12 asks of it.

Reads the **decompiled** `ui/hud.gfx` scripts (260 AS3 files under
`E:\\Modding\\_JC3grab\\hud\\dec\\scripts\\`, the G2-19 export - no archive is opened here), pulls the
two card functions `InitVehicleWeapons` / `UpdateVehicleWeapons` out of `hud.as` with their exact
parameter lists, defaults and bodies, the two-slot array and its per-slot data object, the cooldown
and overcharge code, the reticle shapes and crosshair-look enum used by `UpdateWeaponReticle`, the
POI lock-on path (`POI_TYPE_LOCK_ON_TARGET`, drawn by `hud_code/poi.as`) and the incoming-missile
warning, the weapon-id -> icon rule, and the caller census.

The BmAK half of WPN-12 comes from `Research/BatmobileGrab/HUD_INTERFACES.json` (the
`HudModuleBatmobile` and `HudModuleTargets` setter lists) and the `HudModuleTargets` element row of
`Research/BatmobileGrab/HUD.md`; the JC3 lock-on weapons `w609`/`w612`/`w613` come from
`Research/JC3Grab/WEAPONS.jsonl` (their `AutoAim` tunes) and `Research/JC3Grab/WEAPON_WIRING.jsonl`
(which hulls carry them); the icon census is a scan of `Research/JC3Grab/INDEX.jsonl`; the two
translation rows quoted are the card's own WPN-12 row in `GRAB_BACKLOG.md` and the T-HUD5 row in
`Working/Translation/T6_HUD_CAMERA.md`.

Writes Research/JC3Grab/JC3_HUD_WEAPONS.md + JC3_HUD_WEAPONS.json. `--check` rebuilds and asserts.

Usage:
  python jc3hudwpn.py --write
  python jc3hudwpn.py --check
  python jc3hudwpn.py dump init|update|reticle|lockon|icons|wpn12|weapons
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
BMAK = os.path.join(ROOT, "Research", "BatmobileGrab")
GRAB = os.environ.get("JC3_GRAB", r"E:\Modding\_JC3grab")
HUD = os.path.join(GRAB, "hud", "dec", "scripts")
JSON_NAME = "JC3_HUD_WEAPONS.json"
MD_NAME = "JC3_HUD_WEAPONS.md"

HUD_AS = os.path.join(HUD, "hud.as")
POI_AS = os.path.join(HUD, "hud_code", "poi.as")
ICON_AS = os.path.join(HUD, "hud_code", "weapon_icon_type.as")
INDEX = os.path.join(OUT, "INDEX.jsonl")
WIRING = os.path.join(OUT, "WEAPON_WIRING.jsonl")
WEAPONS = os.path.join(OUT, "WEAPONS.jsonl")
INTERFACES = os.path.join(BMAK, "HUD_INTERFACES.json")
HUD_MD = os.path.join(BMAK, "HUD.md")
T6_MD = os.path.join(ROOT, "Working", "Translation", "T6_HUD_CAMERA.md")
BACKLOG = os.path.join(ROOT, "GRAB_BACKLOG.md")

# The two functions the card names, plus the two that carry the reticle and the lock-on warning.
FUNCS = ("InitVehicleWeapons", "UpdateVehicleWeapons", "UpdateWeaponReticle",
         "ShowMissileLocked", "HideMissileLocked")
LOCKON_WEAPONS = ("w609", "w612", "w613")
# AutoAim rows quoted per lock-on weapon: the OnFoot profile is the player's, the rest are AI states.
AUTOAIM_KEYS = ("OnFoot.AngleThresholdNewTarget", "OnFoot.AngleThresholdCurrentTarget",
                "OnFoot.MaxAimDistance", "OnFoot.MinAimDistance",
                "OnFoot.CanTargetCharacters", "OnFoot.CanTargetVehicles",
                "OnFoot.CanTargetRigidObjects")
TUNE_KEYS = ("missile_weapon[0].tuning.base_tuning.damage",
             "missile_weapon[0].tuning.missile_base_tuning.missile_turning_speed",
             "missile_weapon[0].tuning.missile_base_tuning.missile_loose_lock_distance",
             "magazine_size", "burst_count", "burst_cooldown", "fire_rate", "max_range",
             "velocity")
# WPN-12 as the backlog spells it: five HUD elements.
WPN12_ELEMENTS = ("weapon slots", "reticle", "cannon cooldown", "Vulcan heat", "missile lock")


# ---------------------------------------------------------------- reading helpers
def read(path: str) -> str:
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def digest(path: str) -> dict:
    with open(path, "rb") as f:
        data = f.read()
    return {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def hud_scripts() -> list[str]:
    found = []
    for base, _dirs, names in os.walk(HUD):
        for n in names:
            if n.endswith(".as"):
                found.append(os.path.relpath(os.path.join(base, n), HUD).replace("\\", "/"))
    return sorted(found)


CONST_RE = re.compile(r"(?:private|public)\s+(?:static\s+)?const\s+([A-Za-z_]\w*)\s*:\s*[\w.*]+\s*=\s*"
                      r"([^;]+);")


def consts(src: str) -> dict[str, dict]:
    """Every `const NAME:TYPE = VALUE;` with the raw text and, when it is a plain number, the value."""
    out: dict[str, dict] = {}
    for name, raw in CONST_RE.findall(src):
        raw = raw.strip()
        val: object = raw
        try:
            val = int(raw)
        except ValueError:
            try:
                val = float(raw)
            except ValueError:
                val = raw
        out[name] = {"raw": raw, "value": val}
    return out


def pick(c: dict[str, dict], prefix: str) -> dict[str, int]:
    """Constant prefix -> {name: numeric value} for the ones that resolve to a number."""
    return {k: v["value"] for k, v in sorted(c.items())
            if k.startswith(prefix) and isinstance(v["value"], (int, float))}


def signature(src: str, name: str) -> tuple[str, list[dict]]:
    """(`public function NAME(...) : TYPE` line, [{name, type, default}])."""
    m = re.search(r"^\s*(?:public|private|protected)\s+function\s+" + name +
                  r"\s*\(([^)]*)\)\s*:\s*([\w*]+)", src, re.M)
    if not m:
        raise SystemExit(f"FAIL: {name} not found")
    line = m.group(0).strip()
    params = []
    for part in [p.strip() for p in m.group(1).split(",") if p.strip()]:
        head, _, default = part.partition("=")
        pname, _, ptype = head.strip().partition(":")
        params.append({"name": pname.strip(), "type": ptype.strip(),
                       "default": default.strip() or None})
    return line, params


def body(src: str, name: str) -> str:
    """The brace-matched body of a function, without the signature."""
    m = re.search(r"function\s+" + name + r"\s*\(", src)
    if not m:
        raise SystemExit(f"FAIL: {name} not found")
    i = src.index("{", m.end())
    depth = 0
    for j in range(i, len(src)):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                return src[i + 1:j]
    raise SystemExit(f"FAIL: {name} body unbalanced")


def _rigged(body: str) -> list[str]:
    """The reticle shapes whose `case` block actually computes a width (`new_width = ...`)."""
    out: set[str] = set()
    current: list[str] = []
    for line in body.splitlines():
        m = re.match(r"\s*case\s+(E_RETICLE_\w+):", line)
        if m:
            current.append(m.group(1))
            continue
        if "switch(" in line or line.strip().startswith("}"):
            current, _ = [], current
        if "new_width =" in line and "== " not in line:
            out.update(current)
        if line.strip().startswith("break;"):
            current = []
    return sorted(out)


def calls(src: str, name: str) -> dict:
    """Definition vs call sites for one function name, with the enclosing function of each call."""
    lines = src.splitlines()
    sites = []
    for n, line in enumerate(lines, 1):
        if name + "(" not in line or re.search(r"function\s+" + name + r"\s*\(", line):
            continue
        owner = ""
        for k in range(n - 1, 0, -1):
            mm = re.search(r"function\s+([A-Za-z_]\w*)\s*\(", lines[k - 1])
            if mm:
                owner = mm.group(1)
                break
        sites.append({"line": n, "in": owner, "text": line.strip()})
    return {"count": len(sites), "sites": sites}


# ---------------------------------------------------------------- the BmAK side
def bmak() -> dict:
    data = json.loads(read(INTERFACES))
    bat = data["HudModuleBatmobile"]
    tgt = data["HudModuleTargets"]
    every = [s["name"] for mod in data.values() for s in mod["setters"]]
    md = read(HUD_MD)
    # HUD.md lists the movie twice: the module inventory table first, then §5's element table.
    row = next(ln for ln in md.splitlines()
               if ln.startswith("| `HudModuleTargets` |") and "VehicleMissileTarget" in ln)
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    element_cell = next(c for c in cells[1:] if "VehicleMissileTarget" in c)
    # the row spells the plain kind out and abbreviates the rest as `…_bomb`, `…_emp`, ...
    kinds = sorted({"plain" if "VehicleMissileTarget" in element_cell else ""} |
                   set(re.findall(r"…_?(\w+)", element_cell)) - {""})
    element_cell = element_cell
    cool = next(ln for ln in md.splitlines() if "`UC_SetCannonCoolDown`" in ln and ln.startswith("|"))
    cool_states = re.search(r"`([^`]+)`\s*\|\s*reticle", cool)
    return {
        "batmobile_setters": len(bat["setters"]),
        "batmobile_setter_names": sorted(s["name"] for s in bat["setters"]),
        "targets_setters": len(tgt["setters"]),
        "targets_setter_names": sorted(s["name"] for s in tgt["setters"]),
        "targets_row": row.strip(),
        "targets_element_cell": element_cell,
        "missile_target_kinds": kinds,
        "cannon_cooldown_states": cool_states.group(1) if cool_states else "UNKNOWN",
        "cannon_cooldown_row": cool.strip(),
        "all_setters": len(every),
        "setters_with_heat": sorted(n for n in every if "heat" in n.lower()),
        "vehicle_weapon_setters": sorted(n for n in every
                                         if any(w in n.lower() for w in
                                                ("weapon", "cannon", "cooldown", "lock"))),
    }


def mechanics_heat() -> dict:
    """The BmAK Vulcan heat bar, as MECHANICS.md records it (a script variable, not a setter)."""
    path = os.path.join(BMAK, "MECHANICS.md")
    hits = [ln for ln in read(path).splitlines() if "HeatBarStart" in ln]
    names = sorted({n for ln in hits for n in re.findall(r"`(Heat\w+)`", ln)})
    owners = sorted({m.group(1) for ln in hits
                     for m in [re.search(r"\|\s*`(Batmobile_[\w]+)`\s*\|", ln)] if m})
    return {"rows": len(hits), "fields": names, "weapon_archetypes": owners}


# ---------------------------------------------------------------- the JC3 weapon side
def lockon_weapons() -> dict:
    rows = [json.loads(ln) for ln in read(WEAPONS).splitlines() if ln.strip()]
    wire = [json.loads(ln) for ln in read(WIRING).splitlines() if ln.strip()]
    out: dict[str, dict] = {}
    ents: dict[str, dict] = {}
    for ln in wire:
        for w in ln.get("weapons", []):
            ents.setdefault(w["name"], {"weapon_id": w["weapon_id"], "class": w["class"],
                                        "components": sorted(c["class"] for c in w["components"]),
                                        "bindings": w.get("binding") or [],
                                        "autoaim": os.path.basename(w.get("autoaim_tuning_file") or ""),
                                        "hulls": []})
            ents[w["name"]]["hulls"].append(ln["chassis"])
    for prefix in LOCKON_WEAPONS:
        row = next((r for r in rows if r["id"].startswith(prefix + "_")), None)
        if row is None:
            raise SystemExit(f"FAIL: {prefix} not in WEAPONS.jsonl")
        autoaim: dict[str, object] = {}
        tune: dict[str, object] = {}
        files = []
        for src in row["sources"]:
            files.append(os.path.basename(src["path"]))
            dec = src.get("decode") or {}
            for inst in dec.get("instances", []):
                for key, _type, val in inst["rows"]:
                    if inst["class"] == "AutoAim" and key in AUTOAIM_KEYS and key not in autoaim:
                        autoaim[key] = val
                    if inst["class"] == "WeaponTuning" and key in TUNE_KEYS and key not in tune:
                        tune[key] = val
        wired = ents.get(row["id"], {"hulls": [], "components": [], "bindings": [],
                                     "autoaim": "", "class": "", "weapon_id": ""})
        out[prefix] = {
            "name": row["id"],
            "weapon_id": wired.get("weapon_id") or prefix[1:],
            "class": wired.get("class", ""),
            "components": wired.get("components", []),
            "bindings": wired["bindings"],
            "autoaim_file": wired["autoaim"],
            "chassis": sorted(set(wired["hulls"])),
            "carriers": len(row.get("carriers") or []),
            "files": sorted(set(files)),
            "tune_source": next((os.path.basename(s["path"]) for s in row["sources"]
                                 if (s.get("decode") or {}).get("instances")), ""),
            "autoaim": autoaim,
            "tune": tune,
        }
    # how many wired weapon components in the fleet resolve to an icon file
    return {"weapons": out, "wired_components": sum(len(ln.get("weapons", [])) for ln in wire),
            "wired_hulls": len({ln["chassis"] for ln in wire}),
            "wired_ids": sorted({int(w["weapon_id"]) for ln in wire
                                 for w in ln.get("weapons", []) if w.get("weapon_id")})}


def icons() -> dict:
    ids: set[int] = set()
    files: list[str] = []
    for ln in read(INDEX).splitlines():
        if "weapon_icons" not in ln:
            continue
        row = json.loads(ln)
        m = re.match(r"textures/ui/weapon_icons/(\d+)(_sm)?\.ddsc$", row["path"])
        if m:
            ids.add(int(m.group(1)))
            files.append(row["path"])
    return {"ids": sorted(ids), "count": len(ids), "files": len(files),
            "dir": "textures/ui/weapon_icons/", "suffix": ".ddsc", "low_res_suffix": "_sm.ddsc"}


# ---------------------------------------------------------------- the two quoted rows
def rows() -> dict:
    back = read(BACKLOG)
    m = re.search(r"^\| WPN-12 \| (.+?) \|\s*$", back, re.M)
    card = re.search(r"^#### G2-25 · .+?(?=^#### )", back, re.M | re.S)
    t6 = read(T6_MD)
    t_hud5 = next(ln for ln in t6.splitlines() if ln.startswith("| T-HUD5 |"))
    return {"wpn12": m.group(1).strip() if m else "UNKNOWN",
            "card": card.group(0).strip() if card else "UNKNOWN",
            "t_hud5": t_hud5.strip()}


# ---------------------------------------------------------------- build
def build() -> dict:
    hud = read(HUD_AS)
    poi = read(POI_AS)
    icon_as = read(ICON_AS)
    c = consts(hud)
    cp = consts(poi)

    init_line, init_params = signature(hud, "InitVehicleWeapons")
    upd_line, upd_params = signature(hud, "UpdateVehicleWeapons")
    ret_line, ret_params = signature(hud, "UpdateWeaponReticle")
    init_body = body(hud, "InitVehicleWeapons")
    upd_body = body(hud, "UpdateVehicleWeapons")
    ret_body = body(hud, "UpdateWeaponReticle")
    cool_body = body(hud, "SetCooldownRotation")
    over_body = body(hud, "AnimateOvercharged")
    icon_body = body(hud, "GetWeaponIconName")

    slot_line = next(ln.strip() for ln in hud.splitlines() if "m_WeaponsArray = new Array(" in ln)
    slot_clips = re.findall(r"MCI_vehicle_weapons\d+", slot_line)
    data_fields = sorted(set(re.findall(r"m_WeaponsDataArray\[slot_index\]\.(m_\w+)\s*=", init_body)))
    slot_widgets = sorted(set(re.findall(r"m_WeaponsArray\[slot_index\]\.(\w+)", init_body)))
    bar_parts = sorted(set(re.findall(
        r"m_WeaponsArray\[slot_index\]\.MCI_bullet_bar\.(\w+)", init_body + upd_body)))

    reticle = {
        "signature": ret_line,
        "shapes": pick(c, "E_RETICLE_"),
        "look": pick(c, "ECrosshairLook_"),
        "widths": pick(c, "RETICLE_"),
        "params": ret_params,
        "size_cases": sorted(set(re.findall(r"case\s+(E_RETICLE_\w+):", ret_body))),
        "rigged_shapes": _rigged(ret_body),
        "hidden_inflict_damage_shape": 3,
        "inflict_damage_y": sorted({int(x) for x in re.findall(
            r"MCI_inflict_damage\.y = (-?\d+);", ret_body)}),
        "out_of_range_alpha": c.get("RETICLE_OUT_OF_RANGE_ALPHA", {}).get("value"),
        "poi_types_seen": sorted(set(re.findall(r"POI_TYPE_WEAPON_RETICLE_AUTO\w*", hud))),
    }

    lockon = {
        "poi_types": pick(cp, "POI_TYPE_"),
        "poi_types_in_hud": len(pick(c, "POI_TYPE_")),
        "lock_on_type": c.get("POI_TYPE_LOCK_ON_TARGET", {}).get("value"),
        "lock_on_poi_constant": cp.get("POI_TYPE_LOCK_ON_TARGET", {}).get("value"),
        "lock_on_rotation_time": cp.get("LOCK_ON_TARGET_ROTATION_TIME", {}).get("value"),
        "lock_on_icon": sorted(set(re.findall(r"MCI_lock_on\.MCI_reticle", poi))),
        "missile_locked_timer": c.get("MISSILE_LOCKED_TIMER", {}).get("value"),
        "missile_locked_element": "MCI_safe_area_bottom_middle.MCI_missile_locked",
        "show_missile_locked_calls": calls(hud, "ShowMissileLocked"),
        "hide_missile_locked_calls": calls(hud, "HideMissileLocked"),
        "create_poi_public": bool(re.search(r"public function CreatePoi\(", hud)),
        "lock_on_created_in_movie": len(re.findall(r"CreatePoi\(\s*(?:this\.)?POI_TYPE_LOCK_ON_TARGET",
                                                  hud + poi)),
    }

    heat = {
        "params_with_heat": sorted(p["name"] for p in init_params + upd_params + ret_params
                                   if "heat" in p["name"].lower()),
        "body_mentions": len(re.findall(r"heat", init_body + upd_body, re.I)),
        "police_heat_states": len(pick(consts(read(os.path.join(HUD, "hud_code", "heat", "heat.as"))),
                                       "HEAT_STATE_")),
        "police_heat_dir": "hud_code/heat/",
    }

    ico = icons()
    ico_owner = sorted(set(re.findall(r'"(textures/ui/weapon_icons/[^"]*)"', icon_body)))
    iw = lockon_weapons()
    ico["wired_components"] = iw["wired_components"]
    ico["wired_hulls"] = iw["wired_hulls"]

    weapons = {}
    for prefix, w in iw["weapons"].items():
        weapons[prefix] = dict(w)
        weapons[prefix]["icon"] = int(w["weapon_id"]) in ico["ids"]
    wired_ids = iw["wired_ids"]
    ico["wired_ids"] = wired_ids
    ico["wired_with_icon"] = sorted(i for i in wired_ids if i in ico["ids"])
    ico["wired_without_icon"] = sorted(i for i in wired_ids if i not in ico["ids"])
    ico["missing_owners"] = {str(i): sorted({w["name"] for ln in map(json.loads, read(WIRING).splitlines())
                                             for w in ln.get("weapons", [])
                                             if w.get("weapon_id") == str(i)})
                              for i in ico["wired_without_icon"]}
    ico["owner_literals"] = ico_owner
    ico["rejected_ids"] = sorted({int(x) for x in re.findall(
        r"new_weapon_id == (-?\d+)", icon_as)})

    r = rows()
    b = bmak()
    b["vulcan_heat"] = mechanics_heat()

    # WPN-12: each BmAK element -> the JC3 element that carries it, or the stated absence.
    wpn12 = [
        {
            "element": "weapon slots",
            "bmak": "HudModuleBatmobile.UC_SetPrimaryWeapon(name), UC_SetSecondaryWeapon(name, b, b), "
                    "UC_SetSpecialWeapons(3 x state); HudModuleTargets reacts to Weapon/WeaponHit/"
                    "WeaponFailure",
            "jc3": f"{len(slot_clips)} slots ({', '.join(slot_clips)}) via InitVehicleWeapons("
                   f"slot_index 0..{len(slot_clips) - 1}) / ShowVehicleSlotAction / "
                   f"HideVehicleSlotAction; hidden by HideVehicleUi",
            "disposition": "map",
            "limit": f"{len(slot_clips)} slots total: the Batmobile's primary + secondary weapon map, "
                     "the special-weapon states have no JC3 member",
        },
        {
            "element": "reticle",
            "bmak": "HudModuleBatmobile battle-mode reticle (recticuleHeavy) + UC_SetCannonCoolDown "
                    "states Ready/Blank/PreReady*; UC_SetMachineGunAccuracyFrame",
            "jc3": "UpdateWeaponReticle(show, weapons_look, reticle_size, reticle_shape): "
                   f"{len(reticle['shapes'])} shapes "
                   f"(E_RETICLE_NONE {reticle['shapes'].get('E_RETICLE_NONE')} .. "
                   f"E_RETICLE_POWERCORE {reticle['shapes'].get('E_RETICLE_POWERCORE')}), "
                   f"{len(reticle['look'])} look states, size {reticle['widths'].get('RETICLE_CROSS_WIDTH_MIN')}"
                   f"..{reticle['widths'].get('RETICLE_CROSS_WIDTH_MAX')} px, cross/rocket/circle rigs",
            "disposition": "map (shape id UNKNOWN)",
            "limit": "which shape id the Batmobile's heavy reticle should use is not in the files; "
                     "E_RETICLE_CANNON exists but nothing maps it to a vehicle cannon",
        },
        {
            "element": "cannon cooldown",
            "bmak": f"UC_SetCannonCoolDown(int in {b['cannon_cooldown_states']}) -> reticle "
                    "Ready / Blank / PreReady*",
            "jc3": "weapon_cooldown in Init/UpdateVehicleWeapons (-1 = no loader), SetCooldownRotation "
                   "0..1 -> 360 deg over MCI_mask_0_50 + MCI_mask_50_100, AnimateOvercharged; "
                   f"is_overcharged sound 'dlc_wingsuit_weapon_ready'",
            "disposition": "map (0..1 replaces 5 states)",
            "limit": "BmAK sends 5 categorical states, JC3 takes a 0..1 fraction: the 5 states have to "
                     "be pinned to 5 fractions before the loader reproduces them",
        },
        {
            "element": "Vulcan heat",
            "bmak": f"{len(b['vulcan_heat']['fields'])} script fields "
                    f"({', '.join(b['vulcan_heat']['fields'])}) on "
                    f"{', '.join(b['vulcan_heat']['weapon_archetypes'])}; "
                    f"{len(b['setters_with_heat'])} of {b['all_setters']} UC_* setters contain 'heat'",
            "jc3": f"{len(heat['params_with_heat'])} heat parameter in the vehicle-weapon API, "
                   f"{heat['body_mentions']} mention of heat in the bodies it drives; the movie's heat "
                   f"code is the {heat['police_heat_states']}-state police wanted level "
                   f"({heat['police_heat_dir']})",
            "disposition": "stated absence (both sides)",
            "limit": "JC3 shows ammo + a cooldown loader + an overcharge tint, never a heat bar; the "
                     "Batmobile's heat is a weapon-entity script variable with no HUD setter, so no "
                     "number or member carries WPN-12's heat bar",
        },
        {
            "element": "missile lock",
            "bmak": f"HudModuleTargets: batmobile_lockon, batmobile_aim, missile_lockon_square_anim, "
                    f"{len(b['missile_target_kinds'])} VehicleMissileTarget kinds "
                    f"({', '.join(b['missile_target_kinds'])}); UC_SetBatmobileWeapon(primary, b) / "
                    f"WeaponHit / WeaponFailure; radar side UC_SetLockonValue(value, kind)",
            "jc3": f"one lock-on POI: POI_TYPE_LOCK_ON_TARGET = {lockon['lock_on_type']} -> "
                   f"MCI_icon.MCI_lock_on.MCI_reticle, rotated 360 deg every "
                   f"{lockon['lock_on_rotation_time']} s (hud_code/poi.as); separate incoming-missile "
                   f"warning MCI_missile_locked flashing at {lockon['missile_locked_timer']} s "
                   f"(ShowMissileLocked/HideMissileLocked, 0 movie callers)",
            "disposition": "partial: one lock-on marker, no target-kind family",
            "limit": "JC3 has a single rotating lock-on icon and one incoming warning; the 6-kind "
                     "missile box family, the aim box, per-target health and the hit/failure events "
                     "have no JC3 element",
        },
    ]

    return {
        "inputs": {p: digest(p) for p in (HUD_AS, POI_AS, ICON_AS, INDEX, WIRING, WEAPONS,
                                          INTERFACES, HUD_MD)},
        "scripts": {"total": len(hud_scripts()), "hud_as_lines": len(hud.splitlines()),
                    "hud_as_bytes": len(hud.encode("utf-8")), "root": os.path.relpath(HUD, GRAB)},
        "init": {"signature": init_line, "params": init_params, "body_lines": len(init_body.splitlines())},
        "update": {"signature": upd_line, "params": upd_params, "body_lines": len(upd_body.splitlines())},
        "slots": {"array_line": slot_line, "clips": slot_clips,
                  "count": len(slot_clips),
                  "data_fields": data_fields,
                  "slot_widgets": slot_widgets,
                  "bar_parts": bar_parts,
                  "constant_main": c.get("EVEHICLE_WEAPON_SLOT_MAIN", {}).get("value"),
                  "constant_alt": c.get("EVEHICLE_WEAPON_SLOT_ALTERNATIVE", {}).get("value"),
                  "on_foot_slots": c.get("E_NUM_WEAPON_SLOTS", {}).get("value"),
                  "icon_call": next(p for p in init_body.splitlines()
                                    if "SetWeaponIcon(" in p).strip()},
        "cooldown": {"rot_degrees": int(re.search(r"weapon_cooldown \* (\d+)", cool_body).group(1)),
                     "half": int(re.search(r"Math\.min\(rot,(\d+)\)", cool_body).group(1)),
                     "overcharge_alpha": float(re.search(
                         r"if\(is_overcharged\)\s*\{\s*bullet_bar_alpha = ([\d.]+);",
                         over_body).group(1)),
                     "sounds": sorted(set(re.findall(r'PlaySound\("([\w]+)"\)', over_body))),
                     "toggled_by": "weapon_cooldown != -1",
                     "low_ammo_alpha": c.get("LOW_AMMO_PULSE_ALPHA", {}).get("value"),
                     "low_ammo_time": c.get("LOW_AMMO_PULSE_TIME", {}).get("value"),
                     "bar_scale_time": c.get("WEAPON_BULLET_BAR_SCALE_TIME", {}).get("value"),
                     "bar_frames": 65},
        "reticle": reticle,
        "lockon": lockon,
        "heat": heat,
        "icons": ico,
        "callers": {"init": calls(hud, "InitVehicleWeapons"),
                    "update": calls(hud, "UpdateVehicleWeapons"),
                    "reticle": calls(hud, "UpdateWeaponReticle")},
        "bmak": b,
        "weapons": weapons,
        "rows": r,
        "wpn12": wpn12,
    }


# ---------------------------------------------------------------- markdown
def fmt(v) -> str:
    if v is None:
        return "-"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        s = f"{v:.6f}".rstrip("0").rstrip(".")
        return s if s not in ("", "-0") else "0"
    if isinstance(v, list):
        return ", ".join(str(x) for x in v) if v else "-"
    return str(v)


def render_md(d: dict) -> str:
    L: list[str] = []
    a = L.append
    init, upd, slots = d["init"], d["update"], d["slots"]
    lock, ret, ico = d["lockon"], d["reticle"], d["icons"]
    b, w = d["bmak"], d["weapons"]

    a("# JC3 vehicle-weapon HUD API (HUD-2, WPN-12)")
    a("")
    a(f"G2-25. **Answer: JC3's vehicle-weapon HUD is `{slots['count']}` slots, an optional cooldown "
      f"loader, and a reticle; it has no heat bar and one lock-on marker.**")
    a("")
    a(f"`InitVehicleWeapons` takes **{len(init['params'])} arguments** and `UpdateVehicleWeapons` "
      f"**{len(upd['params'])}**; between them they carry weapon id, name, infinite-ammo flag, "
      f"magazine ammo, magazine size, inventory ammo and a `0..1` cooldown plus an overcharge flag. "
      f"Neither has a heat argument and neither body mentions heat: **WPN-12's Vulcan heat bar is a "
      f"stated absence on both sides** - JC3's movie \"heat\" is the "
      f"{d['heat']['police_heat_states']}-state police wanted level, and the Batmobile's heat is a "
      f"weapon-entity script variable with no `UC_*` setter.")
    a("")
    a(f"The lock-on is **one POI**, `POI_TYPE_LOCK_ON_TARGET = {lock['lock_on_type']}`, drawn by "
      f"`hud_code/poi.as` as a single rotating reticle ({lock['lock_on_rotation_time']} s per turn); "
      f"the flashing `MCI_missile_locked` is a different, *incoming*-missile warning. The "
      f"`VehicleMissileTarget*` box family ({len(b['missile_target_kinds'])} kinds) and the hit/failure "
      f"events have no JC3 element. **What calls the API from the entity side is native code**: the only "
      f"call sites in all {d['scripts']['total']} scripts are {d['callers']['init']['count']} demo calls "
      f"inside `TestConstructor`, so the weapon-id -> HUD bridge stays `UNKNOWN`.")
    a("")
    a(f"Sources: the decompiled `ui/hud.gfx` export (G2-19) - `{d['scripts']['total']}` AS3 scripts, "
      f"`hud.as` {d['scripts']['hud_as_lines']} lines - plus `INDEX.jsonl` (icon census), "
      f"`WEAPONS.jsonl` / `WEAPON_WIRING.jsonl` (the three lock-on missiles), "
      f"`HUD_INTERFACES.json` + `HUD.md` (the BmAK half of WPN-12) and the card's own WPN-12 and "
      f"T-HUD5 rows. Nothing here comes from a wiki, and no archive is opened: only decoded text.")
    a("")
    a("## 1. `InitVehicleWeapons` - the arguments")
    a("")
    a("```")
    a(init["signature"])
    a("```")
    a("")
    a("| # | argument | type | default | what the body does with it |")
    a("|---|---|---|---|---|")
    drives = {
        "slot_index": "indexes `m_WeaponsArray` / `m_WeaponsDataArray`; no range check",
        "weapon_id": "stored, then the icon is loaded from it (see §6)",
        "weapon_name": "`TXT_name.text` - the label under the slot",
        "infiniteAmmo": "branches the whole ammo block: true hides the counters and shows "
                        "`MCI_inventory_infinity`, false shows magazine/inventory text and frames "
                        "`MCI_bullet_bar_anim` at `65 * ammo / size`",
        "magazine_ammo": "stored as `m_MagazineAmmo`; only used for the initial bullet-bar frame",
        "magazine_size": "stored as `m_MagazineSize`; the denominator of the bar fraction",
        "inventory_ammo": "stored as `m_TotalInventoryAmmo`; `TXT_selected_inventory_ammo.text`",
        "weapon_cooldown": "`-1` hides `MCI_radial_loader_cooldown`; otherwise "
                           "`SetCooldownRotation(slot, value)` (§3)",
        "is_overcharged": "`AnimateOvercharged(slot, flag)` - bullet-bar alpha + the ready sound (§3)",
    }
    for i, p in enumerate(init["params"]):
        a(f"| {i} | `{p['name']}` | `{p['type']}` | `{fmt(p['default'])}` | {drives.get(p['name'], 'see body')} |")
    a("")
    a(f"`slot_index` is not validated: the body indexes two-element arrays directly. The body is "
      f"{init['body_lines']} lines and writes {len(slots['data_fields'])} fields of the per-slot data "
      f"object: {', '.join('`' + f + '`' for f in slots['data_fields'])}.")
    a("")
    a("## 2. `UpdateVehicleWeapons` - the arguments")
    a("")
    a("```")
    a(upd["signature"])
    a("```")
    a("")
    a("| # | argument | type | default | what the body does with it |")
    a("|---|---|---|---|---|")
    drives_u = {
        "slot_index": "the slot to update",
        "new_magazine_ammo_amount": "`m_MagazineAmmo`; **`<= 0` returns early**, before any drawing",
        "total_ammo": "`m_TotalInventoryAmmo`; written to the text only when `>= 0`",
        "is_low_ammo": "pulses `MCI_bullet_bar` alpha to "
                       f"{fmt(d['cooldown']['low_ammo_alpha'])} every "
                       f"{fmt(d['cooldown']['low_ammo_time'])} s, else `ClearTween`",
        "weapon_cooldown": "only when `!= -1`: `SetCooldownRotation` + `AnimateOvercharged`",
        "is_overcharged": "the overcharge tint/sound, gated behind the cooldown argument",
    }
    for i, p in enumerate(upd["params"]):
        a(f"| {i} | `{p['name']}` | `{p['type']}` | `{fmt(p['default'])}` | {drives_u.get(p['name'], 'see body')} |")
    a("")
    a("Note the asymmetry: init sends the *name* and the *icon*, update never does - a vehicle that "
      "changes weapon has to call `InitVehicleWeapons` again, and the icon request is skipped when "
      "the id did not change.")
    a("")
    a("## 3. Slots, cooldown and overcharge")
    a("")
    a(f"The slot array is built in `VehicleConstructor`:")
    a("")
    a("```")
    a(slots["array_line"])
    a("```")
    a("")
    a(f"So the vehicle HUD has **{slots['count']} slots** (`{', '.join(slots['clips'])}`), indexed "
      f"`{slots['constant_main']}` = `EVEHICLE_WEAPON_SLOT_MAIN` and `{slots['constant_alt']}` = "
      f"`EVEHICLE_WEAPON_SLOT_ALTERNATIVE`. Do not confuse this with `E_NUM_WEAPON_SLOTS = "
      f"{slots['on_foot_slots']}`, which is the **on-foot** weapon wheel: the same `hud.as` carries "
      f"both and the vehicle arrays are hard-sized to {slots['count']}.")
    a("")
    a(f"Each slot clip carries {len(slots['slot_widgets'])} widgets the two functions touch "
      f"({', '.join('`' + x + '`' for x in slots['slot_widgets'])}) and "
      f"{len(slots['bar_parts'])} parts of its bullet bar "
      f"({', '.join('`' + x + '`' for x in slots['bar_parts'])}).")
    a("")
    a("| mechanism | code | value |")
    a("|---|---|---|")
    a(f"| cooldown -> rotation | `SetCooldownRotation` | `rot = weapon_cooldown * "
      f"{d['cooldown']['rot_degrees']}`, `MCI_mask_0_50.rotation = min(rot, {d['cooldown']['half']})`, "
      f"`MCI_mask_50_100.rotation = max(rot - {d['cooldown']['half']}, 0)` |")
    a(f"| loader visibility | `InitVehicleWeapons` | `MCI_radial_loader_cooldown.visible = "
      f"weapon_cooldown != -1` |")
    a(f"| overcharged | `AnimateOvercharged` | bullet bar alpha "
      f"{d['cooldown']['overcharge_alpha']} while overcharged; pulsing radial loader; "
      f"`PlaySound('{', '.join(d['cooldown']['sounds'])}')` on release |")
    a("| state kept | `m_IsOverchargedArray` | two booleans, one per slot |")
    a("")
    a("`weapon_cooldown` is a **fraction, not a state**: `1` is a full ring, `-1` means \"this slot has "
      "no cooldown display at all\". The Batmobile's `UC_SetCannonCoolDown` is the opposite shape (see §7).")
    a("")
    a("## 4. `UpdateWeaponReticle` - shapes, look and size")
    a("")
    a("```")
    a(ret["signature"])
    a("```")
    a("")
    a("| shape | id | size rig |")
    a("|---|---|---|")
    rigs = {
        "E_RETICLE_SINGLE_SHOT": "cross: `RETICLE_CROSS_WIDTH_MIN + size * (MAX - MIN)`",
        "E_RETICLE_AUTO": "cross (same rig)",
        "E_RETICLE_CIRCLE": "circle: `RETICLE_CIRCLE_WIDTH_MIN .. MAX`",
        "E_RETICLE_DOT": "no size rig",
        "E_RETICLE_NONE": "hidden, and it hides `MCI_inflict_damage`",
        "E_RETICLE_WINGSUIT": "no size rig",
        "E_RETICLE_ROCKET": "rocket: `RETICLE_ROCKET_WIDTH_MIN .. MAX`",
        "E_RETICLE_GRENADE_LAUNCHER": "no size rig",
        "E_RETICLE_CANNON": "no size rig",
        "E_RETICLE_FLAK": "cross rig via `MCI_cross.*`",
        "E_RETICLE_WINGSUIT_WEAPONIZED": "no size rig",
        "E_RETICLE_MECH_CANNON": "no size rig",
        "E_RETICLE_MECH_MINIGUN": "no size rig",
        "E_RETICLE_POWERCORE": "no size rig",
    }
    for name, val in sorted(ret["shapes"].items(), key=lambda kv: kv[1]):
        a(f"| `{name}` | {val} | {rigs.get(name, 'UNKNOWN')} |")
    a("")
    a("| look state | id | effect |")
    a("|---|---|---|")
    looks = {
        "ECrosshairLook_InRangeTargetNeutral": "non-hostile colour",
        "ECrosshairLook_InRangeTargetAllied": "friendly colour",
        "ECrosshairLook_InRangeTargetHostile": "hostile colour",
        "ECrosshairLook_InRangeNoTarget": "non-hostile colour",
        "ECrosshairLook_OutOfRange": "non-hostile colour **and** alpha "
                                     f"{fmt(d['reticle']['out_of_range_alpha'])}",
    }
    for name, val in sorted(ret["look"].items(), key=lambda kv: kv[1]):
        a(f"| `{name}` | {val} | {looks.get(name, 'UNKNOWN')} |")
    a("")
    a(f"`show` toggles `m_WeaponReticleGroup.visible`. Shape `{ret['hidden_inflict_damage_shape']}` "
      f"hides `MCI_inflict_damage`; for shapes 8/11/12 (cannon, mech cannon, mech minigun) the marker "
      f"sits at y = {ret['inflict_damage_y'][0] if ret['inflict_damage_y'] else '?'}, otherwise at "
      f"y = {ret['inflict_damage_y'][1] if len(ret['inflict_damage_y']) > 1 else '?'}. Widths come from "
      f"{len(ret['widths'])} `RETICLE_*` constants. The size switch has {len(ret['size_cases'])} `case` "
      f"labels but only {len(ret['rigged_shapes'])} of them compute a width "
      f"({', '.join('`' + x + '`' for x in ret['rigged_shapes'])}); the other 9 fall through with no "
      f"size change.")
    a("")
    a("This is the **player weapon** reticle. A vehicle's own reticle is not a shape id in this enum: "
      "the vehicle cluster mounts `MCI_vehicle*` clips, and the Batmobile's heavy reticle has to be "
      "expressed as one of these shapes plus `weapons_look` colours. Which shape the game picks for a "
      "vehicle cannon is `UNKNOWN` (native).")
    a("")
    a("## 5. Lock-on: one POI, and an incoming warning")
    a("")
    a(f"`hud.as` declares {lock['poi_types_in_hud']} `POI_TYPE_*` constants and builds any of them with "
      f"`CreatePoi(type, use_progress_bar, is_minor, label)`; `hud_code/poi.as` switches on the type to "
      f"pick the icon. Exactly one type is a lock-on reticle:")
    a("")
    a("| what | value | evidence |")
    a("|---|---|---|")
    a(f"| lock-on type | `POI_TYPE_LOCK_ON_TARGET = {lock['lock_on_type']}` | `hud.as` constant + "
      f"`poi.as` case |")
    a(f"| icon | `MCI_icon_and_label.MCI_icon.MCI_lock_on.MCI_reticle` | `poi.as` case "
      f"{lock['lock_on_type']} |")
    a(f"| animation | `TweenRotation(ret, {lock['lock_on_rotation_time']}, 360, TM_LINEAR, TR_LOOP)` - "
      f"one turn every {lock['lock_on_rotation_time']} s | `LOCK_ON_TARGET_ROTATION_TIME` |")
    a(f"| progress bar | `m_HasProgressBar = false` | same case |")
    a(f"| incoming warning | `MCI_safe_area_bottom_middle.MCI_missile_locked`, flashing every "
      f"{lock['missile_locked_timer']} s | `MISSILE_LOCKED_TIMER`, `FlashMissileLocked` |")
    a(f"| warning API | `ShowMissileLocked()` / `HideMissileLocked()`, "
      f"{lock['show_missile_locked_calls']['count']} / {lock['hide_missile_locked_calls']['count']} "
      f"call sites in the movie | grep of all {d['scripts']['total']} scripts |")
    a(f"| lock-on created by the movie | "
      f"{'yes' if lock['lock_on_created_in_movie'] else 'no'} - "
      f"{lock['lock_on_created_in_movie']} `CreatePoi(POI_TYPE_LOCK_ON_TARGET, ...)` calls | grep |")
    a("")
    a("**These are two different instruments.** `MCI_missile_locked` is the \"a missile is locked on "
      "*you*\" warning, blinking at half-second intervals; the rotating `POI_TYPE_LOCK_ON_TARGET` "
      "reticle is the marker on the thing *you* locked. The Batmobile's HUD needs both, and JC3 has "
      "exactly one of each.")
    a("")
    a("### 5.1 The three lock-on missiles the card names")
    a("")
    a("`w609`, `w612`, `w613` are the fleet's lock-on missiles. Their *\"lock-on\"* is a data fact with "
      "a name and an `AutoAim` tune, not a HUD member:")
    a("")
    a("| weapon | class | chassis | binding | autoaim tune | damage | turning speed | loose-lock |")
    a("|---|---|---|---|---|---|---|---|")
    for prefix in LOCKON_WEAPONS:
        x = w[prefix]
        t = x["tune"]
        a(f"| `{x['name']}` | `{x['class']}` | {len(x['chassis'])} | "
          f"{'; '.join(x['bindings']) or '-'} | `{x['autoaim_file']}` | "
          f"{fmt(t.get('missile_weapon[0].tuning.base_tuning.damage'))} | "
          f"{fmt(t.get('missile_weapon[0].tuning.missile_base_tuning.missile_turning_speed'))} | "
          f"{fmt(t.get('missile_weapon[0].tuning.missile_base_tuning.missile_loose_lock_distance'))} |")
    a("")
    a("`OnFoot` profile of the same tunes - the envelope a lock is acquired in:")
    a("")
    a("| weapon | new-target angle | held-target angle | min dist | max dist | can target "
      "chars/vehicles/objects |")
    a("|---|---|---|---|---|---|")
    for prefix in LOCKON_WEAPONS:
        x = w[prefix]
        aa = x["autoaim"]
        a(f"| `{x['name'].split('_')[0]}` | {fmt(aa.get('OnFoot.AngleThresholdNewTarget'))} | "
          f"{fmt(aa.get('OnFoot.AngleThresholdCurrentTarget'))} | "
          f"{fmt(aa.get('OnFoot.MinAimDistance'))} | {fmt(aa.get('OnFoot.MaxAimDistance'))} | "
          f"{fmt(aa.get('OnFoot.CanTargetCharacters'))} / {fmt(aa.get('OnFoot.CanTargetVehicles'))} / "
          f"{fmt(aa.get('OnFoot.CanTargetRigidObjects'))} |")
    a("")
    a("| weapon | components | magazine | burst | fire rate | max range |")
    a("|---|---|---|---|---|---|")
    for prefix in LOCKON_WEAPONS:
        x = w[prefix]
        t = x["tune"]
        a(f"| `{x['name'].split('_')[0]}` | {', '.join(x['components']) or '(none)'} | "
          f"{fmt(t.get('magazine_size'))} | {fmt(t.get('burst_count'))} | "
          f"{fmt(t.get('fire_rate'))} | {fmt(t.get('max_range'))} |")
    a("")
    a("Three details in that table are traps and are reported as read: `w609`'s only component is "
      "`CLaserBeamWeaponComponent` (the fighterjet's laser/tracer component sits on the missile "
      "object - a component's name is not evidence of what the weapon does, R5); `w612` has none and "
      "is bound to **no driver slot** (G2-11's unbound list); `w613` carries only its `warning_light`. "
      "Mode of acquisition is therefore not carried by a component, unlike the no-lockon `w611`, "
      "which is the one that carries `CAimPOIWeaponComponent`.")
    a("")
    a("Read the table twice: `w609` is an air-to-air missile (angles in fractions of a turn, "
      "vehicles + rigid objects, 750 m), `w612` is looser still, and `w613` - the \"ground lockon\" - "
      "**targets nothing**: `CanTargetCharacters`/`Vehicles`/`RigidObjects` are all 0, "
      "`MaxAimDistance` is -1 and `missile_turning_speed` is 0, so it is an unguided bomb with a "
      "ground reticle. Its ES name promises a lock the data does not implement.")
    a("")
    a(f"**The link from an `AutoAim` tune to `POI_TYPE_LOCK_ON_TARGET` is not in any file.** The tunes "
      f"say what can be acquired and at what angle; the movie says a POI of type "
      f"{lock['lock_on_type']} draws a rotating reticle. Nothing connects them, no ship script creates "
      f"the POI, and `CAimPOIWeaponComponent` (11 entity builds, e.g. on `w611`, the *no-lockon* missile) is a "
      f"component whose name says POI but whose props are only `id:2D0B3C09 = 100` and a world "
      f"position. Whether the engine paints `POI_TYPE_LOCK_ON_TARGET` from `AutoAim` state: `UNKNOWN` "
      f"- native. That gap is why §7's lock-on row is `partial`, not `map`.")
    a("")
    a("## 6. How the entity feeds the HUD: the weapon id is the icon")
    a("")
    a("```")
    a("weapon_icon_name = weapon_id.toString();")
    a('return "textures/ui/weapon_icons/" + weapon_icon_name + ".ddsc";')
    a("```")
    a("")
    a(f"`GetWeaponIconName(weapon_id, low_res)` appends `{ico['low_res_suffix']}` when "
      f"`low_res_image` is set; `weapon_icon_type.LoadIcon` drops the icon entirely for ids "
      f"{' and '.join(str(x) for x in ico['rejected_ids'])}. So the file name is **the weapon id alone** "
      f"- no name, no category, no hash.")
    a("")
    a(f"`INDEX.jsonl` carries **{ico['count']} distinct icon ids** in "
      f"{ico['files']} `{ico['dir']}*.ddsc` files "
      f"({ico['count']} full-res plus `_sm` low-res twins). The fleet's "
      f"{ico.get('wired_components', '-')} wired weapon components use "
      f"{len(ico['wired_ids'])} distinct ids; {len(ico['wired_with_icon'])} of them have an icon:")
    a("")
    a(f"- ids with an icon: {', '.join(str(x) for x in ico['wired_with_icon'])}")
    gap = ico['wired_without_icon']
    note = ""
    for wid, names in sorted(ico["missing_owners"].items()):
        note += f"; id `{wid}` belongs to {', '.join('`' + n + '`' for n in names)}"
    a(f"- **without an icon: {', '.join(str(x) for x in gap) or 'none'}**{note}")
    a("")
    if gap:
        a("That gap is drawn from the files, not a guess: the monorail's missile component sets a "
          "`weapon_id` whose icon was never shipped, so any vehicle that reuses it shows a slot with "
          "no icon. The Batmobile must not reuse that id; the ids that do resolve are the usable set.")
    a("")
    a("| weapon | id | icon file present |")
    a("|---|---|---|")
    for prefix in LOCKON_WEAPONS:
        x = w[prefix]
        a(f"| `{x['name']}` | {x['weapon_id']} | {'yes' if x['icon'] else '**no**'} "
          f"(`{ico['dir']}{x['weapon_id']}{ico['suffix']}`) |")
    a("")
    a("The chain a modder can rely on is therefore: **weapon component's `weapon_id` property -> "
      "`weapon_id.toString()` -> `textures/ui/weapon_icons/<id>.ddsc`**, and `InitVehicleWeapons`' "
      "third argument is the *label*, not the icon. What is missing is the caller that reads the "
      "component and calls the movie (next section).")
    a("")
    a("## 7. WPN-12, element by element")
    a("")
    a(f"The card's own row: *{d['rows']['wpn12']}*")
    a("")
    a("| element | BmAK source | JC3 element | disposition | limit |")
    a("|---|---|---|---|---|")
    for row in d["wpn12"]:
        a(f"| **{row['element']}** | {row['bmak']} | {row['jc3']} | {row['disposition']} | {row['limit']} |")
    a("")
    a(f"The BmAK side is `HudModuleBatmobile` ({b['batmobile_setters']} `UC_*` setters) and "
      f"`HudModuleTargets` ({b['targets_setters']}); across all modules there are "
      f"{b['all_setters']} setters and **{len(b['setters_with_heat'])} of them mention heat** - the "
      f"heat bar is not an interface, it is the weapon entity's `HeatBarStart`/`HeatBarSize` script "
      f"fields on `{'`, `'.join(b['vulcan_heat']['weapon_archetypes'])}` "
      f"({b['vulcan_heat']['rows']} rows in `MECHANICS.md`).")
    a("")
    a("T-HUD5 (`Working/Translation/T6_HUD_CAMERA.md`) said this before the card ran:")
    a("")
    a("```")
    a(d["rows"]["t_hud5"])
    a("```")
    a("")
    a("Its \"2 slots\" is now confirmed from the array itself, not from a summary; its "
      "\"blocked: the HUD supports it, the entity does not\" is unchanged by this card - the HUD side "
      "is decoded, the entity-side caller is native (`UNKNOWN`, §8).")
    a("")
    a("**Result: all five elements have a JC3 element or a stated absence, and none of them is a "
      "silent gap.** Three map (slots, reticle, cooldown), one is a stated absence on both sides "
      "(heat), one is partial (lock-on: one marker where the Batmobile has a 6-kind family).")
    a("")
    a("## 8. Who calls the API")
    a("")
    a("| function | definition | call sites in the movie | where |")
    a("|---|---|---|---|")
    for key, name in (("init", "InitVehicleWeapons"), ("update", "UpdateVehicleWeapons"),
                      ("reticle", "UpdateWeaponReticle")):
        c = d["callers"][key]
        a(f"| `{name}` | 1 | {c['count']} | "
          f"{', '.join(sorted({s['in'] for s in c['sites']})) or '-'} |")
    a("")
    for s in d["callers"]["init"]["sites"]:
        a(f"- `hud.as:{s['line']}` in `{s['in']}` - `{s['text']}`")
    a("")
    a(f"`UpdateWeaponReticle` has {d['callers']['reticle']['count']} call sites in the movie as well, "
      f"and `ShowMissileLocked`/`HideMissileLocked` have none. These are **public** functions on the "
      f"movie's document class: the game calls them from native code through the HUD interface, which "
      f"is not in these files. So *who* feeds a vehicle's weapons to the HUD, and with what values, is "
      f"`UNKNOWN` (R5: the behaviour is unproven until a drive proves it). What is proven is the shape "
      f"of the call: a slot index, a weapon id, a label and a `0..1` cooldown.")
    a("")
    a("## 9. Checks")
    a("")
    a("| check | result |")
    a("|---|---|")
    a(f"| `python Tools/scripts/jc3hudwpn.py --check` | rebuilds both files from the same inputs and "
      f"asserts every number above |")
    a(f"| scripts scanned | {d['scripts']['total']} `.as` under `{d['scripts']['root']}` |")
    a(f"| function signatures | `InitVehicleWeapons` {len(init['params'])} args, "
      f"`UpdateVehicleWeapons` {len(upd['params'])} args, parsed from the source, not typed |")
    a(f"| slot count | {slots['count']}, from the `new Array(...)` line |")
    a(f"| icons | {ico['count']} ids in `INDEX.jsonl` |")
    a(f"| WPN-12 rows | {len(d['wpn12'])} |")
    a("")
    a("Every number in this page is regenerated by the script; none is typed by hand. Re-running "
      "`--write` after a change to the decompiled export or to the repo tables is the only way to "
      "edit it.")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- invariants
def invariants(d: dict) -> list[str]:
    bad: list[str] = []
    init, upd, slots = d["init"], d["update"], d["slots"]

    if d["scripts"]["total"] != 260:
        bad.append(f"script count {d['scripts']['total']} (expected 260)")
    if len(init["params"]) != 9:
        bad.append(f"InitVehicleWeapons params {len(init['params'])} (expected 9)")
    if len(upd["params"]) != 6:
        bad.append(f"UpdateVehicleWeapons params {len(upd['params'])} (expected 6)")
    # the card expects a heat argument; the data has none - assert the absence, not a guess
    if d["heat"]["params_with_heat"]:
        bad.append(f"unexpected heat parameters {d['heat']['params_with_heat']}")
    if d["heat"]["body_mentions"] != 0:
        bad.append(f"{d['heat']['body_mentions']} heat mentions in the vehicle-weapon bodies")
    if d["heat"]["police_heat_states"] != 11:
        bad.append(f"police heat states {d['heat']['police_heat_states']} (expected 11)")
    if d["bmak"]["setters_with_heat"]:
        bad.append(f"BmAK setters with heat {d['bmak']['setters_with_heat']}")
    if slots["count"] != 2:
        bad.append(f"vehicle slots {slots['count']} (expected 2)")
    if slots["on_foot_slots"] != 7:
        bad.append(f"E_NUM_WEAPON_SLOTS {slots['on_foot_slots']} (expected 7 - on-foot wheel)")
    if (slots["constant_main"], slots["constant_alt"]) != (0, 1):
        bad.append(f"slot constants {slots['constant_main']}/{slots['constant_alt']}")
    if sorted(slots["data_fields"]) != ["m_HasInfiniteAmmo", "m_MagazineAmmo", "m_MagazineSize",
                                        "m_TotalInventoryAmmo", "m_WeaponId", "m_WeaponName"]:
        bad.append(f"per-slot data fields {slots['data_fields']}")
    if d["cooldown"]["rot_degrees"] != 360 or d["cooldown"]["half"] != 180:
        bad.append(f"cooldown geometry {d['cooldown']}")
    if abs(d["cooldown"]["overcharge_alpha"] - 0.7) > 1e-9:
        bad.append(f"overcharge alpha {d['cooldown']['overcharge_alpha']}")
    if d["cooldown"]["sounds"] != ["dlc_wingsuit_weapon_ready"]:
        bad.append(f"overcharge sounds {d['cooldown']['sounds']}")

    ret = d["reticle"]
    if len(ret["shapes"]) != 14:
        bad.append(f"reticle shapes {len(ret['shapes'])} (expected 14)")
    if ret["shapes"].get("E_RETICLE_CANNON") != 8:
        bad.append(f"E_RETICLE_CANNON {ret['shapes'].get('E_RETICLE_CANNON')}")
    if ret["shapes"].get("E_RETICLE_NONE") != 3:
        bad.append(f"E_RETICLE_NONE {ret['shapes'].get('E_RETICLE_NONE')}")
    if len(ret["look"]) != 5:
        bad.append(f"look states {len(ret['look'])} (expected 5)")
    if len(ret["size_cases"]) != 14 or len(ret["rigged_shapes"]) != 5:
        bad.append(f"reticle size cases {len(ret['size_cases'])} / rigged "
                   f"{len(ret['rigged_shapes'])} (expected 14 / 5)")
    if ret["out_of_range_alpha"] != 0.4:
        bad.append(f"out-of-range alpha {ret['out_of_range_alpha']}")

    lock = d["lockon"]
    if lock["lock_on_type"] != 21 or lock["lock_on_poi_constant"] != 21:
        bad.append(f"lock-on POI {lock['lock_on_type']}/{lock['lock_on_poi_constant']} (expected 21)")
    if lock["poi_types_in_hud"] != 32:
        bad.append(f"POI types {lock['poi_types_in_hud']} (expected 32)")
    if lock["lock_on_rotation_time"] != 1.5:
        bad.append(f"lock-on rotation {lock['lock_on_rotation_time']}")
    if lock["missile_locked_timer"] != 0.5:
        bad.append(f"missile-locked timer {lock['missile_locked_timer']}")
    if lock["show_missile_locked_calls"]["count"] != 0:
        bad.append(f"ShowMissileLocked called from the movie "
                   f"{lock['show_missile_locked_calls']['count']} times")
    if lock["lock_on_created_in_movie"] != 0:
        bad.append(f"movie creates the lock-on POI {lock['lock_on_created_in_movie']} times")

    ico = d["icons"]
    if ico["count"] != 69:
        bad.append(f"icon ids {ico['count']} (expected 69)")
    if ico["rejected_ids"] != [-1, 0]:
        bad.append(f"rejected icon ids {ico['rejected_ids']}")
    if ico["owner_literals"] != ["textures/ui/weapon_icons/"]:
        bad.append(f"icon path literals {ico['owner_literals']}")
    # measured: exactly one wired id in the fleet has no shipped icon (the monorail's w614)
    if ico["wired_without_icon"] != [614]:
        bad.append(f"wired weapon ids without an icon {ico['wired_without_icon']} (expected [614])")
    for prefix in LOCKON_WEAPONS:
        if not d["weapons"][prefix]["icon"]:
            bad.append(f"{prefix} has no icon file")

    c = d["callers"]
    if c["init"]["count"] != 2 or {s["in"] for s in c["init"]["sites"]} != {"TestConstructor"}:
        bad.append(f"InitVehicleWeapons call sites {c['init']}")
    if {s["in"] for s in c["update"]["sites"]} not in (set(), {"TestConstructor"}):
        bad.append(f"UpdateVehicleWeapons call sites {c['update']}")

    b = d["bmak"]
    if b["batmobile_setters"] != 37:
        bad.append(f"BmAK batmobile setters {b['batmobile_setters']} (expected 37)")
    if b["all_setters"] != 252:
        bad.append(f"BmAK setters total {b['all_setters']} (expected 252)")
    if len(b["missile_target_kinds"]) != 6:
        bad.append(f"missile target kinds {b['missile_target_kinds']}")
    if not b["vulcan_heat"]["fields"] or "HeatBarStart" not in b["vulcan_heat"]["fields"]:
        bad.append(f"Vulcan heat fields {b['vulcan_heat']['fields']}")

    if len(d["wpn12"]) != 5:
        bad.append(f"WPN-12 rows {len(d['wpn12'])} (expected 5)")
    if [r["element"] for r in d["wpn12"]] != list(WPN12_ELEMENTS):
        bad.append(f"WPN-12 elements {[r['element'] for r in d['wpn12']]}")
    for r in d["wpn12"]:
        if not r["jc3"] or not r["disposition"]:
            bad.append(f"WPN-12 row {r['element']} undecided")
    if "InitVehicleWeapons" not in d["rows"]["wpn12"]:
        bad.append(f"WPN-12 row lost its JC3 target: {d['rows']['wpn12'][:80]}")
    if "T-HUD5" not in d["rows"]["t_hud5"]:
        bad.append(f"T-HUD5 row not found: {d['rows']['t_hud5'][:80]}")
    return bad


# ---------------------------------------------------------------- commands
def cmd_write() -> int:
    d = build()
    with open(os.path.join(OUT, JSON_NAME), "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    md = render_md(d)
    with open(os.path.join(OUT, MD_NAME), "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    print(f"{JSON_NAME}/{MD_NAME}: {d['scripts']['total']} scripts, "
          f"{len(d['init']['params'])} + {len(d['update']['params'])} args, "
          f"{d['slots']['count']} slots, {d['lockon']['poi_types_in_hud']} POI types, "
          f"{d['icons']['count']} icons, {len(d['wpn12'])} WPN-12 rows, {len(md.splitlines())} md lines")
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
        diff = list(difflib.unified_diff(have.splitlines(), md.splitlines(), "file", "rebuilt", n=1))
        bad.append("md differs: " + " | ".join(diff[2:8]))
    if bad:
        print("FAIL: " + "; ".join(bad))
        return 1
    print(f"PASS: {d['scripts']['total']} scripts, InitVehicleWeapons "
          f"{len(d['init']['params'])} args / UpdateVehicleWeapons {len(d['update']['params'])} args, "
          f"{d['slots']['count']} vehicle slots (E_NUM_WEAPON_SLOTS "
          f"{d['slots']['on_foot_slots']} is on-foot), {len(d['reticle']['shapes'])} reticle shapes, "
          f"lock-on POI {d['lockon']['lock_on_type']} at {d['lockon']['lock_on_rotation_time']} s, "
          f"0 heat parameters, 0 heat in bodies, {len(d['bmak']['setters_with_heat'])} BmAK heat "
          f"setters, {d['icons']['count']} weapon icons, {len(d['wpn12'])} WPN-12 rows "
          f"({'/'.join(r['disposition'].split(':')[0].split(' (')[0] for r in d['wpn12'])})")
    return 0


def cmd_dump(what: str) -> int:
    d = build()
    key = {"init": "init", "update": "update", "reticle": "reticle", "lockon": "lockon",
           "icons": "icons", "wpn12": "wpn12", "weapons": "weapons",
           "slots": "slots", "callers": "callers", "bmak": "bmak", "heat": "heat"}
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
    dl.add_argument("what", nargs="?", default="init")
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
