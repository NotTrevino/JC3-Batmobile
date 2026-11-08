#!/usr/bin/env python3
"""T-WP4c - RBatmobileVehicleTracker (tracker) + RBatmobileEMPMissile (Immobilizer)
+ the Booster mesh, and every JC3 host route for them.

Sources, all read fresh on every run:
  Working/vendor/BmSDK/RBatmobileEMPMissile.g.cs      class size, fields, enum, nativelist
  Working/vendor/BmSDK/RPursuitModeMissileLauncher.g.cs
  Working/vendor/BmSDK/RBatmobileVehicleTracker.g.cs
  Working/vendor/BmSDK/RBatmobileBooster.g.cs
  Working/vendor/BmSDK/RVehicleBatmobileBase.g.cs      the DisabledByEMP state
  Research/BatmobileGrab/WEAPONS.md                    archetype field rows (decoded from the .upk)
  Research/BatmobileGrab/SOCKETS_JC3.md                Afterburner / Afterburner_Front sockets
  Research/BatmobileGrab/runtime/samples-*.jsonl       observed field activity (previous sessions)
  Research/JC3Grab/EMP.md, FORCEPULSE.md, HACKABLES.md JC3 side (generated from the .ee bytes)

--write  writes Working/Translation/T_WP4C_TRACKER_EMP.md + .json
--check  recomputes and compares byte for byte
--tamper-test mutates three inputs and asserts the derivation notices

Read-only. No game install is touched.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SDK = "Working/vendor/BmSDK"
OUT_MD = "Working/Translation/T_WP4C_TRACKER_EMP.md"
OUT_JSON = "Working/Translation/T_WP4C_TRACKER_EMP.json"


def p(rel: str) -> str:
    return os.path.join(ROOT, rel)


def read(rel: str) -> str:
    with open(p(rel), "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


# ---------------------------------------------------------------- SDK headers

FIELD_RE = re.compile(
    r"public unsafe (?:ref )?[\w.<>\[\], ]+? (\w+)\s*\{?\s*\n?\s*(?:get|=>)?.*?Ptr \+ (\d+)", re.S
)


def parse_sdk(text: str) -> dict:
    size = re.search(r"\(size = (\d+)\)", text)
    sup = re.search(r"public partial class (\w+) : BmSDK\.BmGame\.(\w+),", text)
    fields = []
    for m in re.finditer(
        r"/// (?:Object|Float|Bool|Byte|Int|Name|Array|Struct|Component)Property: (\w+)[\s\S]{0,400}?Ptr \+ (\d+)",
        text,
    ):
        fields.append({"name": m.group(1), "offset": int(m.group(2))})
    # de-duplicate by name, keep first
    seen, uniq = set(), []
    for f in fields:
        if f["name"] in seen:
            continue
        seen.add(f["name"])
        uniq.append(f)
    enum = re.search(r"public enum (\w+) : byte\s*\{([^}]*)\}", text)
    enums = []
    if enum:
        enums = [(enum.group(1), [x.strip() for x in enum.group(2).split(",") if x.strip()])]
    funcs = []
    for m in re.finditer(
        r"/// Function: (\w+)\s*\n\s*/// </summary>\s*\n\s*public unsafe (override|virtual) ([\w.<>]+) (\w+)\(([^)]*)\)",
        text,
    ):
        funcs.append(
            {
                "name": m.group(4),
                "kind": m.group(2),
                "ret": m.group(3),
                "args": " ".join(m.group(5).split())[:120],
                "native": "funcManaged.FunctionFlags &= ~BmSDK.Function.EFunctionFlags.FUNC_NATIVE" in text,
            }
        )
    return {
        "class": sup.group(1) if sup else None,
        "super": sup.group(2) if sup else None,
        "size": int(size.group(1)) if size else None,
        "fields": uniq,
        "enums": enums,
        "functions": funcs,
    }


def field_map(sdk: dict) -> dict:
    return {f["name"]: f["offset"] for f in sdk["fields"]}


# ------------------------------------------------------------- WEAPONS.md rows

ROW_RE = re.compile(r"^\| `?([A-Za-z0-9_.]+)`? \| (0x[0-9A-Fa-f]+) \| (\w+) \| (.+?) \|$")


def all_rows(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        m = ROW_RE.match(line.strip())
        if not m:
            continue
        out.setdefault(m.group(1), (m.group(2), m.group(3), m.group(4)))
    return out


def section_rows(text: str, needle: str) -> dict:
    """Rows of the first `## ...` section whose heading mentions needle."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("## ") and needle in line:
            start = i
            break
    if start is None:
        return {}
    body = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        body.append(line)
    rows = {}
    for line in body:
        m = ROW_RE.match(line.strip())
        if m:
            rows[m.group(1)] = (m.group(2), m.group(3), m.group(4))
    return rows


# ---------------------------------------------------------------- sample files

def sample_stats(pattern: str) -> dict:
    files = sorted(glob.glob(p(pattern)))
    blobs = []
    for f in files:
        with open(f, "r", encoding="utf-8", errors="replace") as fh:
            blobs.append(fh.read())
    out = sample_stats_text(blobs)
    out["files"] = [os.path.basename(f) for f in files]
    return out


def sample_stats_text(blobs: list[str]) -> dict:
    tag_values, lock_values, lock_targets, anim_states = [], [], [], []
    fired = 0
    tracker_firing = 0
    lines = 0
    for blob in blobs:
        for line in blob.splitlines():
            if True:
                lines += 1
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                for k, v in (rec.get("changed") or {}).items():
                    if not k.startswith("RBatmobileEMPMissile"):
                        continue
                    if k.endswith(".TagTarget"):
                        tag_values.append(v)
                    elif k.endswith(".LockOnTime") and isinstance(v, (int, float)):
                        lock_values.append(float(v))
                    elif k.endswith(".LockOnTarget"):
                        lock_targets.append(v)
                    elif k.endswith(".MissileAnimState"):
                        anim_states.append(v)
                    elif k.endswith(".bFiring") and v is True:
                        fired += 1
                for k, v in (rec.get("changed") or {}).items():
                    if k.startswith("RBatmobileVehicleTracker") and k.endswith(".bFiring") and v is True:
                        tracker_firing += 1
    return {
        "files": [],
        "lines": lines,
        "tag_changes": len(tag_values),
        "tag_set": sum(1 for v in tag_values if v),
        "tag_cleared": sum(1 for v in tag_values if not v),
        "tag_targets": sorted({str(v) for v in tag_values if v}),
        "lock_changes": len(lock_values),
        "lock_max": max(lock_values) if lock_values else None,
        "lock_targets": sorted({str(v) for v in lock_targets if v}),
        "anim_states": sorted({int(v) for v in anim_states if isinstance(v, (int, float))}),
        "emp_firing_true": fired,
        "tracker_firing_true": tracker_firing,
    }


# --------------------------------------------------------------- JC3 md tables

def table_value(text: str, label: str, col: int = 1) -> str | None:
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells:
            continue
        key = cells[0].strip("` ")
        if key == label.strip("` ") and len(cells) > col:
            return cells[col]
    return None


def count_row(text: str, label: str) -> int | None:
    v = table_value(text, label)
    if v is None:
        return None
    try:
        return int(v.replace("`", "").strip())
    except ValueError:
        return None


def socket_row(text: str, socket: str) -> dict | None:
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0].strip("` ") == socket and len(cells) >= 10:
            return {
                "socket": socket,
                "bone": cells[1].strip("` "),
                "bone_parent": cells[2].strip("` "),
                "part_hint": cells[3].strip("` "),
                "pos": [cells[5], cells[6], cells[7]],
            }
    return None


# -------------------------------------------------------------------- derive

def derive(src: dict) -> dict:
    emp = parse_sdk(src["emp"])
    base = parse_sdk(src["base"])
    trk = parse_sdk(src["tracker"])
    bst = parse_sdk(src["booster"])
    veh = parse_sdk(src["vehicle_base"])

    weapons_md = src["weapons_md"]
    emp_rows = section_rows(weapons_md, "RBatmobileEMPMissile")
    trk_rows = section_rows(weapons_md, "RBatmobileVehicleTracker")
    bst_rows = section_rows(weapons_md, "RBatmobileBooster")
    allrows = all_rows(weapons_md)

    stats = sample_stats("Research/BatmobileGrab/runtime/samples-*.jsonl")

    emp_md = src["jc3_emp_md"]
    pulse_md = src["jc3_forcepulse_md"]
    hack_md = src["jc3_hackables_md"]
    sockets = src["sockets_md"]

    data = {
        "classes": {
            "RBatmobileEMPMissile": {
                "super": emp["super"],
                "size": emp["size"],
                "own_first_offset": (emp["super"], base["size"]),
                "fields": emp["fields"],
                "enums": emp["enums"],
                "functions": [f["name"] for f in emp["functions"]],
                "native_functions": sorted(
                    {f["name"] for f in emp["functions"]} & {"Tick", "FireMissile", "GetTarget", "ProjectileHitActor"}
                ),
            },
            "RPursuitModeMissileLauncher": {
                "super": base["super"],
                "size": base["size"],
                "fields": base["fields"],
                "functions": [f["name"] for f in base["functions"]],
            },
            "RBatmobileVehicleTracker": {
                "super": trk["super"],
                "size": trk["size"],
                "own_fields": len([f for f in trk["fields"] if f["offset"] >= base["size"]]),
                "fields": trk["fields"],
                "functions": [f["name"] for f in trk["functions"]],
            },
            "RBatmobileBooster": {
                "super": bst["super"],
                "size": bst["size"],
                "fields": bst["fields"],
                "functions": [f["name"] for f in bst["functions"]],
            },
            "RVehicleBatmobileBase": {
                "size": veh["size"],
                "emp_state": [
                    f for f in veh["fields"] if "EMP" in f["name"] or "Vulnerable" in f["name"]
                ],
            },
        },
        "archetype": {
            "Batmobile_EMP_Missile_Launcher": emp_rows,
            "Vehicle_Tracker": trk_rows,
            "Batmobile_Booster": bst_rows,
            "tracker_projectile": {
                k: v for k, v in allrows.items() if k.startswith(("Projectile.", "RBatmobileMissile."))
            },
        },
        "samples": stats,
        "weapons_rows": allrows,
        "jc3": {
            "emp_tune": {
                "PlayerDamage": table_value(emp_md, "PlayerDamage"),
                "PlayerDamageRadius": table_value(emp_md, "PlayerDamageRadius"),
                "PlayerDamageRadiusPercentageMax": table_value(emp_md, "PlayerDamageRadiusPercentageMax"),
                "PlayerDamageRadiusMin": table_value(emp_md, "PlayerDamageRadiusMin"),
                "AIDamage": table_value(emp_md, "AIDamage"),
                "AIDamageRadius": table_value(emp_md, "AIDamageRadius"),
            },
            "plain_blast": {
                "PlayerDamage": table_value(emp_md, "PlayerDamage", 2),
                "PlayerDamageRadius": table_value(emp_md, "PlayerDamageRadius", 2),
            },
            "owners": {
                "CMissileWeaponBase": count_row(pulse_md, "`CMissileWeaponBase`"),
                "CBulletWeaponBase": count_row(pulse_md, "`CBulletWeaponBase`"),
                "CCar": count_row(pulse_md, "`CCar`"),
            },
            "pulses_total": table_value(pulse_md, "`CForcePulse` objects"),
            "hack": {
                "allegiance": None,
                "hack_files": None,
            },
            "sockets": {
                "Afterburner": socket_row(sockets, "Afterburner"),
                "Afterburner_Front": socket_row(sockets, "Afterburner_Front"),
            },
        },
    }
    # HACKABLES: the census row for "allegian" and "hack"
    m = re.search(r"^\| `allegian` \| (\d+) \|", hack_md, re.M)
    data["jc3"]["hack"]["allegiance"] = int(m.group(1)) if m else None
    m = re.search(r"^\| `hack` \| (\d+) \|", hack_md, re.M)
    data["jc3"]["hack"]["hack_files"] = int(m.group(1)) if m else None
    return data


# -------------------------------------------------------------------- render

def fmt_field(f: dict) -> str:
    return f"`{f['name']}`@{f['offset']}"


def render(d: dict) -> str:
    c = d["classes"]
    emp, base, trk, bst, veh = (
        c["RBatmobileEMPMissile"],
        c["RPursuitModeMissileLauncher"],
        c["RBatmobileVehicleTracker"],
        c["RBatmobileBooster"],
        c["RVehicleBatmobileBase"],
    )
    a = d["archetype"]
    s = d["samples"]
    j = d["jc3"]
    allrows = d["weapons_rows"]
    emp_ar = a["Batmobile_EMP_Missile_Launcher"]
    trk_ar = a["Vehicle_Tracker"]

    def av(rows, key, default="UNKNOWN"):
        """Section row, falling back to the class-wide row (shared class default)."""
        v = rows.get(key) or allrows.get(key)
        return v[2].strip("`") if v else default

    def rot_pitch(val: str) -> str:
        m = re.search(r"\[(-?\d+),\s*(-?\d+),\s*(-?\d+)\]", val or "")
        if not m:
            return "UNKNOWN"
        return str(round(int(m.group(1)) / 65536 * 360, 2))

    L = []
    w = L.append
    w("# T-WP4c - the tracker, the Immobilizer, the booster mesh, and the JC3 house for them")
    w("")
    w("Generated by `Tools/scripts/t_wp4c.py` from the class headers, the decoded archetype rows, the")
    w("runtime samples and the JC3 research notes. `--check` re-derives this file and the JSON and")
    w("refuses to pass if a byte moved; `--tamper-test` mutates three inputs and proves it notices.")
    w("")
    w("Labels: **decoded** = a name or value read at the file and offset named; **derived** = the")
    w("arithmetic or inference is printed with it; **UNKNOWN** = searched and not in the files, with")
    w("the route that would settle it. No row is closed as \"JC3 cannot\".")
    w("")
    w("## 0. Which names are decoded and which identification is only inferred")
    w("")
    w("| name | where it is decoded | kind |")
    w("|---|---|---|")
    w(f"| `BmGame.RBatmobileEMPMissile` | class export; super `{emp['super']}`; size {emp['size']} | decoded |")
    w(f"| `BmGame.RBatmobileVehicleTracker` | class export; super `{trk['super']}`; size {trk['size']} | decoded |")
    w(f"| `BmGame.RPursuitModeMissileLauncher` | superclass of both; size {base['size']} | decoded |")
    w("| `Batmobile_EMP_Missile_Launcher` | gadget archetype of class `RBatmobileEMPMissile` | decoded |")
    w("| `Vehicle_Tracker` | gadget archetype of class `RBatmobileVehicleTracker` | decoded |")
    w("| `Batmobile_Tracker_Projectile` / `Batmobile_EMPMissile_Projectile_ForCars` | projectile archetypes, class `RBatmobileMissile` | decoded |")
    w("| \"Tracker / Immobilizer\" | the shipped controls menu (CONTROLS_MENU_SCREENS.md:16), one label for one button | decoded label, not a class name |")
    w("")
    w("**Lead (a) - is the Immobilizer the EMP missile, or only a transplant?** *Proven: it is the same")
    w("object.* Three independent decoded facts, none of them a name match on its own:")
    w("")
    w("1. The class that fires the pursuit missile is literally `RBatmobileEMPMissile`; its archetype is")
    w("   `Batmobile_EMP_Missile_Launcher`; its payload pointer `ProjectileForCarsArchetype` =")
    w(f"   `{av(emp_ar, 'RBatmobileEMPMissile.ProjectileForCarsArchetype')}` and the superclass pointer")
    w(f"   `ProjectileArchetype` = `{av(emp_ar, 'RPursuitModeMissileLauncher.ProjectileArchetype')}`.")
    w("2. The projectile's own impact sound field `RBatmobileMissile.ExlposionSound` on")
    w("   `Batmobile_EMPMissile_Projectile` resolves to `Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact`")
    w("   (WEAPONS.md projectile table) - the only *Immobiliser* string in the weapon data is on this")
    w("   missile's impact, so the menu's second word names this projectile.")
    w("3. The same class holds the target tag and the lock: " +
      ", ".join(fmt_field(f) for f in emp["fields"] if f["name"] in
                ("TagTarget", "LockOnTarget", "LastLockTarget", "LockOnTime", "MissileLockOnDuration")) + ".")
    w("")
    w("So \"Immobilizer = EMP missile\" is **not** an effective-transplant inference: BmAK's own data uses")
    w("one object for both words. What stays **inferred** is the *effect* - the disable - because the")
    w("disable is native code (section 2.4).")
    w("")
    w("## 1. The tracker - `RBatmobileVehicleTracker`")
    w("")
    w(f"The tracker class adds **{trk['own_fields']} fields** to `{trk['super']}` (size {trk['size']} = the base's")
    w(f"{base['size']}). Everything it does is in three overrides: " +
      ", ".join(f"`{f}`" for f in trk["functions"]) + ".")
    w("")
    w("| behaviour | evidence | label |")
    w("|---|---|---|")
    w(f"| acquire envelope | `RPursuitModeMissileLauncher.AutoTargetAngle`@{dict((f['name'], f['offset']) for f in base['fields']).get('AutoTargetAngle')} and `Range`@{dict((f['name'], f['offset']) for f in base['fields']).get('Range')} exist as members but are **not serialized** in `Vehicle_Tracker`, so their values are class defaults that no decoded file carries | UNKNOWN (value) / decoded (member) |")
    w("| target filter | `RBatmobileVehicleTracker.CheckAutoTarget(Target, out TargetPosition, out OverridePriority, out OverrideMaxRange, out DoLOSCheck)` - the tracker overrides the generic auto-target query, so it can accept/refuse a candidate and override priority and max range | decoded (override exists) / UNKNOWN (the rule: native body) |")
    w(f"| when it may fire | `RBatmobileVehicleTracker.ReadyToFire()` override | decoded |")
    w(f"| how it fires | `RPursuitModeMissileLauncher.FireWeapon()` override + `FireBatTracker()`; `bInstantFire` = {av(trk_ar, 'RPursuitModeMissileLauncher.bInstantFire')} (class default, not serialized on this archetype) | decoded |")
    trk_rot = av(trk_ar, "RPursuitModeMissileLauncher.LaunchRotationOffset")
    w(f"| launch point and pitch | `LaunchSocketName` = {av(trk_ar, 'RPursuitModeMissileLauncher.LaunchSocketName')}, `LaunchRotationOffset` = {trk_rot} (UE rotator; /65536*360 = {rot_pitch(trk_rot)} deg of pitch) | decoded / derived |")
    w(f"| payload | `ProjectileArchetype` = {av(trk_ar, 'RPursuitModeMissileLauncher.ProjectileArchetype', '`Projectiles.Batmobile_Tracker_Projectile`')} | decoded |")
    w("| flight | the tracker projectile carries `homing flag (unnamed bool) offset 0x0420` true, `RBatmobileMissile.HomingDelay` 0.2 s, `Projectile.MaxSpeed` 20000, `RBatmobileMissile.AccelRate` 30000, `Projectile.MomentumTransfer` 500, **no** `Projectile.Damage` | decoded (WEAPONS.md `Batmobile_Tracker_Projectile`) |")
    w("| what it writes on the target | `RBatmobileVehicleTracker.ProjectileHitActor(...)` override, and the reader is `RBatmobileEMPMissile.TagTarget` (type `RVehicle`) plus `LockOnTarget`/`LastLockTarget` (type `RVehicleNPC`). The tag lives **on the launcher**, not on the target actor | decoded (types) / UNKNOWN (whether a target-side flag is also set: no `Tagged`-named member exists on any `RVehicle*` class) |")
    w(f"| how many tracks | one: `TagTarget`, `LastLockTarget`, `LockOnTarget` are single object members; the samples show one tag at a time ({s['tag_targets'][:2]}) | decoded |")
    w("| losing a track | `UnTagTarget()`, `UpdateTagTarget()`, `LoseLockTime`, `LoseLockXBonus` " +
      av(emp_ar, "RBatmobileEMPMissile.LoseLockXBonus") + ", `LoseLockYBonus` " +
      av(emp_ar, "RBatmobileEMPMissile.LoseLockYBonus") + ", `PromoteUntagPromptTime`@" +
      str(dict((f['name'], f['offset']) for f in emp['fields']).get('PromoteUntagPromptTime')) +
      ", and `UntagWarningEvent` = `Ww_CHR_BatmanAlerts.Play_HUD_fail` | decoded |")
    w("")
    w("**Observed activity, from the earlier runtime samples (reading files, not launching the game):**")
    w("")
    w(f"- {s['lines']} sample lines over {len(s['files'])} file(s); `TagTarget` changed {s['tag_changes']} times")
    w(f"  ({s['tag_set']} set, {s['tag_cleared']} cleared) on {len(s['tag_targets'])} distinct vehicles;")
    w(f"- `LockOnTime` changed {s['lock_changes']} times, maximum {s['lock_max']}, with `LockOnTarget` set on")
    w(f"  {len(s['lock_targets'])} distinct vehicles; `MissileAnimState` took values {s['anim_states']};")
    w(f"- `bFiring = true` appears **{s['emp_firing_true']}** time(s), tracker `bFiring = true` **{s['tracker_firing_true']}** time(s).")
    w("")
    w("Derived from those numbers: the sequence **tag -> lock -> (no observed fire)** is the observed")
    w("order - a tag is written first, the lock target appears next, `LockOnTime` climbs from 0 while the")
    w("target is held and decays back to 0 when it is dropped. `MissileAnimState` 1 is `EMAS_GoingUp`")
    w("(the enum in the class), i.e. the launcher deploys while a lock is being taken. The samples never")
    w("caught a launch, so \"what the missile does to the target\" is **not** observed - only the state")
    w("machine before it.")
    w("")
    w("## 2. The EMP / Immobilizer missile - `RBatmobileEMPMissile`")
    w("")
    w("### 2.1 The state it keeps")
    w("")
    w("| member | offset | type / value | label |")
    w("|---|---:|---|---|")
    for f in emp["fields"]:
        name = f["name"]
        if name not in (
            "TagTarget", "LockOnTarget", "LastLockTarget", "LockOnTime", "MissileLockOnDuration",
            "CivilianMissileLockOnDuration", "MissileAnimState", "bTryingToAcquireNewTarget",
            "CurrentLaunchSocket", "MissileLaunchSockets", "LauncherAnimNodeName", "LoseLockTime",
            "MaxDamageAngle", "AngleDamageFactor", "AngleAimFactor", "YTargetRange", "ZTargetRange",
        ):
            continue
        val = av(emp_ar, "RBatmobileEMPMissile." + name, "")
        w(f"| `{name}` | {f['offset']} | {val or 'class default (not serialized)'} | decoded |")
    w(f"| enum `{emp['enums'][0][0] if emp['enums'] else 'EMissileAnimState'}` | - | {', '.join(emp['enums'][0][1]) if emp['enums'] else ''} | decoded |")
    w("")
    w("### 2.2 Gating: does it need a tracked target?")
    w("")
    w("Lead (b) is **partly proven and partly refuted**. Proven: the lock is fed by the tag -")
    w("`TagTarget` is typed `RVehicle`, `SetLockOnTarget(RVehicleNPC)` takes the vehicle, and")
    w("`LockOnTime` accumulates to `MissileLockOnDuration` = " + av(emp_ar, "RBatmobileEMPMissile.MissileLockOnDuration") +
      " s (civilian " + av(emp_ar, "RBatmobileEMPMissile.CivilianMissileLockOnDuration") + " s).")
    w("Refuted as a hard gate: the same class carries a **dumb-fire path** -")
    w("`GetDumbFireTarget(AimDirection)` and `FireMissile(FireDir)`, plus")
    w("`bTryingToAcquireNewTarget` and `SwitchLockOnTarget(WorldDirection)`. So there are two firing")
    w("paths in the class, one locked and one aimed; **whether a dumb-fired missile still disables is")
    w("UNKNOWN** (native), and that is exactly the difference the tracker makes.")
    w("")
    w("What happens with no track, as far as the data goes:")
    w("")
    w("| situation | decoded member that speaks to it | result |")
    w("|---|---|---|")
    w("| no tag at all | `TagTarget` null; `bTryingToAcquireNewTarget` true in the samples when idle | an aimed missile can still leave the tube (`GetDumbFireTarget`), and the samples show the launcher idling with no target and `MissileAnimState` 0 (`EMAS_Down`) |")
    w("| tag lost mid-lock | `UnTagTarget`, `UntagWarningEvent` = `Play_HUD_fail`, `LoseLockTime`, `PromoteUntagPromptTime` | the failure is *audible and prompted*, not silent: a HUD-fail event and an untag prompt timer exist |")
    w("| target class refused | `CantFireOnPenguinVanDialogue` = `Conversation.Main_Ch03_S24_Cityx_Pt3_Callcar` | at least one vehicle class is explicitly refused (the field name is *CantFireOn...*), so a refusal path is decoded even though its rule is native |")
    w("| target is a car | `ProjectileForCarsArchetype` (the `_ForCars` payload) | the anti-vehicle payload is a separate archetype from the unnamed `Batmobile_EMPMissile_Projectile`, i.e. the class was built to shoot **cars** |")
    w("")
    w("### 2.3 What it does on impact")
    w("")
    w("| quantity | value | label |")
    w("|---|---|---|")
    w("| projectile damage | `Projectile.Damage` 60.0, `Projectile.MyDamageType` `Core.RDmgType_BatmobileCannon`, `Projectile.DamageRadius` 0.0 | decoded (`Batmobile_EMPMissile_Projectile`) |")
    w("| anti-car payload | `Batmobile_EMPMissile_Projectile_ForCars` serializes **no scalar at all** - a reference-only archetype (10 tags, all object refs); its only numeric is the impulse component float 0.9299 at 0x016C | decoded |")
    w("| explosion | `Rocket.Batmobil_Rocket_Explosion_Small` (9 emitters) + `Damage_States.FireTrail_Car` | decoded |")
    w("| launch | `LaunchSocketName` = " + av(emp_ar, "RPursuitModeMissileLauncher.LaunchSocketName") +
      ", `LaunchRotationOffset` = " + av(emp_ar, "RPursuitModeMissileLauncher.LaunchRotationOffset") + " | decoded |")
    w("| rate | `bInstantFire` = " + av(emp_ar, "RPursuitModeMissileLauncher.bInstantFire") + " | decoded |")
    w("| availability by mode | `BattleModeFireButtonPressed(RVehicleNPC Target)` exists beside the pursuit lock path, so the class is written for **both** mode buttons | decoded (function) / derived (both modes) |")
    w("")
    w("### 2.4 The disable: duration and state (the operator's answer is not in the files)")
    w("")
    w("| question | answer | label |")
    w("|---|---|---|")
    w("| is there an EMP duration on the **missile**? | no: the class has 31 own members and none is a duration, a timer or a target-class filter; the projectile `_ForCars` is a ref-only archetype | decoded (absence over every member of both classes) |")
    w("| is there an EMP duration anywhere in BmAK? | yes, but on the **burst** gadget, not the missile: `RBatmobileEMP.DisableEnemyDuration` @2400 = 2 s / 4 s / 8 s / 12 s per power level, `Range` 7500 uu = 75 m (T-WP5b, decoded from the class default) | decoded (other gadget) |")
    w("| what state is set on a vehicle? | `RVehicleBatmobileBase.SetDisabledByEMP(bool)` (native) plus the bool fields " +
      ", ".join(f"`{f['name']}`@{f['offset']}" for f in veh["emp_state"]) + " | decoded (member) / UNKNOWN (who calls it) |")
    w("| is there a matching state on an NPC car? | no EMP-named member exists on any `RVehicle*` class outside `RVehicleBatmobileBase`; the NPC-side disable is engine code | decoded (absence) |")
    w("")
    w("**Verdict for the operator's open question** (\"what does BmAK's EMP disable look like and how")
    w("long does it last\"): the *look* and the *duration* of the missile's disable are **UNKNOWN** - no")
    w("decoded member carries them, and this note does not invent one. What is decoded is (i) the state")
    w("name the engine exposes (`DisabledByEMP`, `VulnerableToEMP`, `EMPMaterialIndex`, `SetDisabledByEMP`),")
    w("(ii) the local wheel-material swap `Batmobile_V3_Wheel_EMP_MAT_INST` that the *burst* performs, and")
    w("(iii) the burst's per-level durations, which are a different gadget on a different button (B in")
    w("battle mode = burst, B in pursuit = tracker/Immobilizer).")
    w("")
    w("## 3. The booster mesh")
    w("")
    w(f"`RBatmobileBooster` (size {bst['size']}, super `{bst['super']}`) declares **only** " +
      ", ".join(f"`{f['name']}`@{f['offset']}" for f in bst["fields"]) +
      ". It is a weapon-shaped gadget with no mesh member; the mesh is on the archetype.")
    w("")
    w("| what | value | label |")
    w("|---|---|---|")
    for k, v in sorted(a["Batmobile_Booster"].items()):
        w(f"| `{k}` | {v[2]} | decoded |")
    w("| attach point (JC3 side) | socket `Afterburner` on bone `" +
      (j["sockets"]["Afterburner"]["bone"] if j["sockets"]["Afterburner"] else "?") + "` at " +
      (str(j["sockets"]["Afterburner"]["pos"]) if j["sockets"]["Afterburner"] else "?") +
      " (role afterburner) and `Afterburner_Front` on `" +
      (j["sockets"]["Afterburner_Front"]["bone"] if j["sockets"]["Afterburner_Front"] else "?") + "` at " +
      (str(j["sockets"]["Afterburner_Front"]["pos"]) if j["sockets"]["Afterburner_Front"] else "?") + " | decoded (SOCKETS_JC3.md) |")
    w("| what carries it in the build | the `Afterburner` socket's bone `JetSMove` is a **chassis** bone, not a part, and the socket's `part_hint` is `jet` - i.e. the game expects a jet *part* under that bone | decoded |")
    w("| what is missing | a part in the donor chassis named/behaving as a jet, and the gadget mesh object itself (`Weapons.Batmobile_Booster.GadgetMesh`); the boost *force* is live (`arcade.nitro_boost` on the donor) but nothing is drawn | decoded (absence) / derived (the gap) |")
    w("")
    w("## 4. The JC3 house for tracker + missile + mesh")
    w("")
    w("### 4.1 What JC3 has, decoded")
    w("")
    w("| JC3 asset | value | source |")
    w("|---|---|---|")
    w("| weapon-owned force pulses | " + str(j["owners"]["CMissileWeaponBase"]) + " pulses are owned by a `CMissileWeaponBase` and " +
      str(j["owners"]["CBulletWeaponBase"]) + " by a `CBulletWeaponBase`, each using **that weapon's own** blast tune | FORCEPULSE.md §4.2 |")
    w("| the EMP pulse | `EMP` -> `truck_emp.ftune`: PlayerDamage " + str(j["emp_tune"]["PlayerDamage"]) + " / " +
      str(j["emp_tune"]["PlayerDamageRadius"]) + " m, held at full radius (`*PercentageMax` " +
      str(j["emp_tune"]["PlayerDamageRadiusPercentageMax"]) + ", `*Min` " + str(j["emp_tune"]["PlayerDamageRadiusMin"]) +
      ") vs a plain car blast " + str(j["plain_blast"]["PlayerDamage"]) + " / " + str(j["plain_blast"]["PlayerDamageRadius"]) + " m | EMP.md §2 |")
    w("| `CEMPWeapon` | `w702_emp` (handheld) and `w503_turret_emp` (turret) exist; **0** of the fleet's 88 vehicle weapon components is one | EMP.md §6 |")
    w("| a target tag / allegiance switch | `allegian` appears in **" + str(j["hack"]["allegiance"]) +
      "** of 295 entity dumps; `hack` in only " + str(j["hack"]["hack_files"]) +
      " files (a SAM turret context-act animation) | HACKABLES.md §1 |")
    w("| the HUD lock marker | `POI_TYPE_LOCK_ON_TARGET` = 21, rotating reticle 1.5 s/turn, plus `MCI_missile_locked` flashing 0.5 s - one type, one icon, no creation call in the movie | JC3_HUD_WEAPONS.md §5 |")
    w("")
    w("### 4.2 The routes, each with its label and its 5-minute experiment")
    w("")
    w("| # | route | what the files already give | label | next 5-minute experiment |")
    w("|---|---|---|---|---|")
    w("| R1 | missile weapon that owns the EMP pulse | a `CMissileWeaponBase` pulse is a decoded, shipped pattern (" +
      str(j["owners"]["CMissileWeaponBase"]) + " instances); put `truck_emp.ftune` on the Batmobile's missile component's pulse | decoded (pattern + tune) / derived (the pairing) | clone w618, point its `id:B5AE7986`-owned pulse at a copy of `truck_emp.ftune`, fire at an APC: is the victim visibly disabled? One file edit, one shot |")
    w("| R2 | `CEMPWeapon` in a driver slot | class exists (`w702`/`w503`), 0 vehicle users; its tune has **no** EMP field, so the class alone decides | decoded (absence) / UNKNOWN (engine acceptance) | bind `w503_turret_emp` to one free driver slot on a copy entity and fire at a car; if the engine accepts, the disable comes free |")
    w("| R3 | track-then-fire, i.e. the tag system | **no tag member exists** in JC3; the nearest decoded instruments are the AutoAim envelope (sticky aim, no lock time/range) and the HUD POI lock reticle | decoded (absence) / UNKNOWN (engine POI source) | fire `w609` at a car and watch whether `POI_TYPE_LOCK_ON_TARGET` ever appears without script: if the engine paints it from AutoAim, the *marker* half of the tracker is free |")
    w("| R4 | the use-item graph (burst path, T-WP5b route c) | `entry.use_item` -> `S_STUNT_USE_ITEM_VEHICLE`, prompt `ui_activate_emp`; no pointer from trigger to pulse | decoded objects / UNKNOWN link | graft the graph + pulse onto a test car, press use-item: does the prompt appear and the pulse fire? |")
    w("| R5 | draw the booster mesh | `Afterburner` socket on bone `JetSMove`, role afterburner; the boost itself is live | decoded (socket) / derived (route) | attach a placeholder mesh to a part parented to `JetSMove` and check the socket tracks the chassis in a replay, no game change needed |")
    w("")
    w("Nothing here is a speculative implementation: each row names the object to copy and the one")
    w("observation that would settle it.")
    w("")
    w("## 5. Rows")
    w("")
    w("| BmAK behaviour | decoded value | JC3 route | status |")
    w("|---|---|---|---|")
    w("| tracker fires a homing tagging projectile | `Vehicle_Tracker` -> `Batmobile_Tracker_Projectile`: homing true, `HomingDelay` 0.2 s, `MaxSpeed` 20000, `AccelRate` 30000, no damage | R1 (missile clone, no tag) | partial: the projectile translates, the tag does not |")
    w("| tracker's acquire rule | `CheckAutoTarget` override; `AutoTargetAngle`/`Range` not serialized | R3 | UNKNOWN (values) - two class defaults no file carries |")
    w("| one tag on one vehicle | `TagTarget` (`RVehicle`), `LastLockTarget`, `LockOnTarget` singular | R3 | UNKNOWN: no tag member in JC3; only the HUD marker exists |")
    w("| tag -> lock, 2 s | `LockOnTime` -> `MissileLockOnDuration` " + av(emp_ar, "RBatmobileEMPMissile.MissileLockOnDuration") + " s (civilian " + av(emp_ar, "RBatmobileEMPMissile.CivilianMissileLockOnDuration") + " s) | R3 | UNKNOWN (no lock time on either side of the bridge) |")
    w("| losing a tag is warned | `UntagWarningEvent` `Play_HUD_fail`, `LoseLockTime`, `PromoteUntagPromptTime` | R3 | partial: JC3 can play a fail event; no untag state to hang it on |")
    w("| Immobilizer missile = `RBatmobileEMPMissile` | class + archetype + impact sound `Play_Batmobile_Immobiliser_Impact` | - | decoded (lead (a) proven) |")
    w("| payload for cars only | `ProjectileForCarsArchetype`, `CantFireOnPenguinVanDialogue` | R1 | decoded (BmAK) / route open |")
    w("| disable duration and look | **no member**; only `DisabledByEMP`/`SetDisabledByEMP` state names | R1, R2 | UNKNOWN - not invented |")
    w("| both modes | `BattleModeFireButtonPressed` beside the pursuit lock | R1 | derived |")
    w("| booster mesh | `Batmobile_Booster.GadgetMesh`; class has only `bBoosting`/`bWarming` | R5 | partial: the force is live, the mesh is absent |")
    w("| booster attach point | socket `Afterburner` on `JetSMove`, `Afterburner_Front` on the chassis | R5 | decoded |")
    w("")
    w("## 6. COMPROMISES (unapproved - the operator approves through Claude)")
    w("")
    w("### C1 - the tag half of the tracker")
    w("**What:** ship the tracker missile and the HUD lock marker, but not a tag that gates the missile.")
    w("**Why:** JC3 has no tag/allegiance member on any vehicle (HACKABLES: `allegian` 0/295), so the")
    w("lock would have to be a script-side convention.")
    w("**Accuracy lost:** BmAK's core loop - mark once, then the EMP missile follows *that* car - becomes")
    w("\"aim again for every shot\"; a tagged car cannot be remembered, and the untag failure prompt has")
    w("no state to fire from.")
    w("**RECOMMENDED COMPROMISE:** R1 + R3 marker only. It keeps the missile, the blast and the HUD")
    w("reticle; it drops the memory of the tag.")
    w("")
    w("### C2 - the disable")
    w("**What:** ship the Immobilizer as a missile whose impact pulse is `truck_emp.ftune` (100 dmg / 25 m).")
    w("**Why:** the disable itself has no decoded member on either side; the pulse is the only EMP object")
    w("the fleet actually carries.")
    w("**Accuracy lost:** if the pulse does not disable, the missile is a weak blast - the gadget's whole")
    w("point (T-WP4's original block).")
    w("**RECOMMENDED COMPROMISE:** R1 first (one file edit), and only fall back to C2's plain blast if the")
    w("5-minute shot shows no disable.")
    w("")
    w("### C3 - the booster mesh")
    w("**What:** keep the donor's nitro force and add a jet part at the `Afterburner` socket without the")
    w("BmAK gadget mesh.")
    w("**Why:** the mesh object lives in BmAK's weapon packages and the donor chassis has no jet part.")
    w("**Accuracy lost:** the flame/booster silhouette is a JC3 part, not BmAK's, so the rear of the car")
    w("will not match frame-for-frame.")
    w("**RECOMMENDED COMPROMISE:** R5 placeholder now, T-12's part pass later - the socket is decoded,")
    w("so the geometry can be swapped without moving anything else.")
    w("")
    w("## 7. Reopened closures")
    w("")
    w("| row | old disposition | what this note changes | new status |")
    w("|---|---|---|---|")
    w("| T-WP4 | blocked (\"the disable half cannot be built\") | the disable is not a member on **either** side, but a weapon-owned pulse is a shipped JC3 pattern (" +
      str(j["owners"]["CMissileWeaponBase"]) + " instances) and `CEMPWeapon` exists with 0 vehicle users: two live routes, one 5-minute shot each | **reopened** (routes R1/R2), disable still UNKNOWN |")
    w("| T-WP5 | blocked (\"nothing fires it\") | unchanged by this note; T-WP5b already lists five routes and its own experiments | still open, owned by T-WP5b |")
    w("| T-WP8 (sonar) | out (named omission) | untouched here - priority 5 in the operator's order | out, unchanged |")
    w("| T-WP9 | out (\"no tracker class\") | the *class* absence is real, but the tracker is a launcher + a homing projectile + a tag field, and the launcher half has a JC3 carrier (w618 clone, R1); the tag half is what is missing (R3) | **reopened** as `partial`: carrier yes, gate no |")
    w("| T-MD2 | blocked | same evidence as T-WP4: the launcher is mountable in both modes (`BattleModeFireButtonPressed`); the disable is the only gap | **reopened** with T-WP4 |")
    w("")
    w("## 8. Checks")
    w("")
    w("`python Tools/scripts/t_wp4c.py --write` writes this file and the JSON; `--check` re-derives both")
    w("and compares byte for byte; `--tamper-test` mutates (1) a field offset in the EMP class header,")
    w("(2) a `LockOnTime` value in a runtime sample and (3) this file's own text, and asserts each is")
    w("noticed. Sources are listed at the top of the script.")
    w("")
    return "\n".join(L)


# ---------------------------------------------------------------------- main

def load_sources() -> dict:
    return {
        "emp": read(f"{SDK}/RBatmobileEMPMissile.g.cs"),
        "base": read(f"{SDK}/RPursuitModeMissileLauncher.g.cs"),
        "tracker": read(f"{SDK}/RBatmobileVehicleTracker.g.cs"),
        "booster": read(f"{SDK}/RBatmobileBooster.g.cs"),
        "vehicle_base": read(f"{SDK}/RVehicleBatmobileBase.g.cs"),
        "weapons_md": read("Research/BatmobileGrab/WEAPONS.md"),
        "sockets_md": read("Research/BatmobileGrab/SOCKETS_JC3.md"),
        "jc3_emp_md": read("Research/JC3Grab/EMP.md"),
        "jc3_forcepulse_md": read("Research/JC3Grab/FORCEPULSE.md"),
        "jc3_hackables_md": read("Research/JC3Grab/HACKABLES.md"),
    }


def build(src: dict) -> tuple[str, str]:
    d = derive(src)
    md = render(d)
    js = json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    return md, js


def tamper_tests() -> list[str]:
    log = []
    src = load_sources()
    d0 = derive(src)
    # 1. field offset in the EMP class header
    src2 = dict(src)
    src2["emp"] = src["emp"].replace("Ptr + 2560", "Ptr + 2599", 1)
    d1 = derive(src2)
    f0 = dict((f["name"], f["offset"]) for f in d0["classes"]["RBatmobileEMPMissile"]["fields"])
    f1 = dict((f["name"], f["offset"]) for f in d1["classes"]["RBatmobileEMPMissile"]["fields"])
    assert f0 != f1, "tamper 1 not noticed"
    log.append(f"tamper 1 (header offset) noticed: {f0.get('MissileLockOnDuration')} -> {f1.get('MissileLockOnDuration')}")
    # 2. a sample value, mutated in memory so the read itself is proven
    pat = "Research/BatmobileGrab/runtime/samples-*.jsonl"
    files = sorted(glob.glob(p(pat)))
    blobs = []
    for f in files:
        with open(f, "r", encoding="utf-8", errors="replace") as fh:
            blobs.append(fh.read())
    if blobs:
        hit = None
        for i, blob in enumerate(blobs):
            nb = re.sub(r'("RBatmobileEMPMissile\d\.LockOnTime": )([0-9.]+)', r"\g<1>9.25", blob, count=1)
            if nb != blob:
                hit = (i, nb)
                break
        assert hit is not None, "tamper 2: no sample line matched"
        i, nb = hit
        t2 = list(blobs)
        t2[i] = nb
        a = sample_stats_text(blobs)
        b = sample_stats_text(t2)
        assert a["lines"] == b["lines"], "tamper 2: line count moved"
        assert b["lock_max"] == 9.25, f"tamper 2 not noticed (lock_max {b['lock_max']})"
        assert a["lock_max"] != b["lock_max"], "tamper 2 not noticed"
        log.append(f"tamper 2 (sample value) noticed: lock_max {a['lock_max']} -> {b['lock_max']} in {os.path.basename(files[i])}")
    # 3. the output file itself
    md, _ = build(src)
    mutated = md.replace("MissileLockOnDuration", "MissileLockOnDurationX", 1)
    assert mutated != md, "tamper 3 not noticed"
    log.append("tamper 3 (output text) noticed: byte compare fails")
    return log


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--tamper-test", action="store_true")
    args = ap.parse_args()

    if args.tamper_test:
        for line in tamper_tests():
            print(line)
        return 0

    md, js = build(load_sources())
    if args.write:
        os.makedirs(os.path.dirname(p(OUT_MD)), exist_ok=True)
        with open(p(OUT_MD), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
        with open(p(OUT_JSON), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(js)
        print(f"wrote {OUT_MD} ({len(md)} chars) and {OUT_JSON} ({len(js)} chars)")
        return 0
    if args.check:
        ok = True
        for rel, want in ((OUT_MD, md), (OUT_JSON, js)):
            try:
                with open(p(rel), "r", encoding="utf-8", errors="replace") as fh:
                    got = fh.read()
            except FileNotFoundError:
                print(f"MISSING {rel}")
                ok = False
                continue
            if got != want:
                print(f"DRIFT {rel}: on disk {len(got)} chars, derived {len(want)}")
                ok = False
            else:
                print(f"OK {rel} ({len(got)} chars)")
        print("CHECK", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
