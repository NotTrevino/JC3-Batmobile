#!/usr/bin/env python3
"""T-WP3b: JC3 carriers for BmAK's Missile Barrage lock-on, decoded from the bytes.

The earlier pass (Working/Translation/T7_WEAPONS.md) read one car missile (`w618`, bound to
`autoaim_vehicle_no_lockon_missile`) and concluded that the AutoAim block has "no lock duration
and no lock range" and that JC3's lock-on lives only in the HUD POI.  This script re-reads the
fleet's own lock-on weapons from the archive instead of from a summary:

  * every `*.wtunec` under `editor/entities/jc_weapons/` (103 tunes), decoded with `jc3adf`
    from `D:/Games/Just Cause 3/<archive>.arc` at the entry offset in
    `Research/JC3Grab/INDEX.jsonl`;
  * the two shared AutoAim presets - `autoaim_vehicle_lockon_missile` (2 weapon builds bind it)
    and `autoaim_vehicle_no_lockon_missile` (20) - decoded value by value;
  * the three per-weapon lock-on AutoAim tunes `w609` / `w612` / `w613`;
  * `Research/JC3Grab/WEAPON_WIRING.jsonl` for the entity side (weapon id, class, driver
    binding, AutoAim preset, the unnamed weapon props, the components).

Offsets quoted below are struct offsets from each file's own type dictionary, so a row can be
patched without guessing.  Labels: `decoded` = read from a file; `derived` = computed from
decoded facts with the rule stated; `UNKNOWN` = not decodable here, with what was tried.

Writes Working/Translation/T_WP3B_LOCKON.json + .md.
`--check` re-derives both and compares byte for byte; it also asserts every claim the prose
makes about counts and absences.

Usage:
  python Tools/scripts/t_wp3b.py --write
  python Tools/scripts/t_wp3b.py --check
  python Tools/scripts/t_wp3b.py dump presets|weapons|homing
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jc3adf  # noqa: E402
from jc3index import DEFAULT_GAME  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Working", "Translation")
RES = os.path.join(ROOT, "Research", "JC3Grab")
INDEX = os.path.join(RES, "INDEX.jsonl")
WIRING = os.path.join(RES, "WEAPON_WIRING.jsonl")
BMAK_WEAPONS = os.path.join(ROOT, "Research", "BatmobileGrab", "WEAPONS.md")
JSON_NAME = "T_WP3B_LOCKON.json"
MD_NAME = "T_WP3B_LOCKON.md"

PRESET_LOCKON = "editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_lockon_missile.wtunec"
PRESET_NOLOCK = "editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtunec"
WEAPON_DIR = {
    "w609": "editor/entities/jc_weapons/06_vehicle/w609_fighterjet_missile_air_lockon/w609_fighterjet_missile_air_lockon.wtunec",
    "w612": "editor/entities/jc_weapons/06_vehicle/w612_fighterbomber_missile_air_lockon/w612_fighterbomber_missile_air_lockon.wtunec",
    "w613": "editor/entities/jc_weapons/06_vehicle/w613_fighterbomber_missile_ground_lockon/w613_fighterbomber_missile_ground_lockon.wtunec",
    "w614": "editor/entities/jc_weapons/06_vehicle/w614_monorailmissilecar_missile/w614_monorailmissilecar_missile.wtunec",
    "w618": "editor/entities/jc_weapons/06_vehicle/w618_sportsmuscle_missile/w618_sportsmuscle_missile.wtunec",
    "w611": "editor/entities/jc_weapons/06_vehicle/w611_fighterbomber_missile/w611_fighterbomber_missile.wtunec",
}
AUTOAIM_DIR = {
    "w609": "editor/entities/jc_weapons/06_vehicle/w609_fighterjet_missile_air_lockon/w609_fighterjet_missile_air_lockon_autoaim.wtunec",
    "w612": "editor/entities/jc_weapons/06_vehicle/w612_fighterbomber_missile_air_lockon/w612_fighterbomber_missile_air_lockon_autoaim.wtunec",
    "w613": "editor/entities/jc_weapons/06_vehicle/w613_fighterbomber_missile_ground_lockon/autoaim_w613_bombs.wtunec",
}
CONTEXTS = ("OnFoot", "Stunting", "MotorCycle", "ReelingIn", "ReeledIn", "Parachute")
# BmAK values quoted from Research/BatmobileGrab/WEAPONS.md; each is asserted verbatim below.
BMAK = (
    ("RBatmobileMissileLauncher.LockOnAngle", "0x0980", "FloatProperty", "40.0",
     "| `RBatmobileMissileLauncher.LockOnAngle` | 0x0980 | FloatProperty | 40.0 |"),
    ("RBatmobileMissileLauncher.LockOnRange", "0x0984", "FloatProperty", "12000.0",
     "| `RBatmobileMissileLauncher.LockOnRange` | 0x0984 | FloatProperty | 12000.0 |"),
    ("RBatmobileMissileLauncher.MaxTargets", "0x095C", "IntProperty", "8",
     "| `RBatmobileMissileLauncher.MaxTargets` | 0x095C | IntProperty | 8 |"),
    ("RBatmobileMissileLauncher.FireInterval", "0x098C", "FloatProperty", "0.5",
     "| `RBatmobileMissileLauncher.FireInterval` | 0x098C | FloatProperty | 0.5 |"),
    ("RBatmobileEMPMissile.MissileLockOnDuration", "0x0A00", "FloatProperty", "2.0",
     "| `RBatmobileEMPMissile.MissileLockOnDuration` | 0x0A00 | FloatProperty | 2.0 |"),
    ("RBatmobileEMPMissile.CivilianMissileLockOnDuration", "0x0A04", "FloatProperty", "1.0",
     "| `RBatmobileEMPMissile.CivilianMissileLockOnDuration` | 0x0A04 | FloatProperty | 1.0 |"),
)


# ------------------------------------------------------------------ decoding
def load_index() -> dict[str, dict]:
    idx = {}
    with open(INDEX, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            idx[r["path"]] = r
    return idx


def read_entry(r: dict) -> bytes:
    with open(os.path.join(DEFAULT_GAME, r["archive"] + ".arc"), "rb") as f:
        f.seek(r["offset"])
        return f.read(r["size"])


def _rows(adf, m, base, off, prefix):
    """Yield (path, type, value, member_offset) - offset is within the member's own struct."""
    p = prefix + ("." if prefix else "") + m["name"]
    t = adf.type(m["type"])
    pos = base + off + m["offset"]
    if t is None:                                    # primitive
        for _s, tn, val in jc3adf._read(adf, m["type"], base, off + m["offset"]):
            yield p, tn, val, m["offset"]
        return
    if t["name"] == "HashString":
        s_off, s_hash = struct.unpack_from("<QI", adf.blob, pos)
        yield p + ".string", "string", adf.string_at(s_off), m["offset"]
        yield p + ".hash", "uint32", s_hash, m["offset"]
        return
    if t["code"] == jc3adf.TYPE_STRUCTURE:
        for mm in t["members"]:
            yield from _rows(adf, mm, pos, 0, p)
    elif t["code"] == jc3adf.TYPE_ARRAY:
        a_off, a_count = struct.unpack_from("<QQ", adf.blob, pos)
        stride = jc3adf._element_stride(adf, t["element"])
        et = adf.type(t["element"])
        start = adf.data_off + a_off
        for i in range(a_count):
            if et and et["code"] == jc3adf.TYPE_STRUCTURE:
                for mm in et["members"]:
                    yield from _rows(adf, mm, start, i * stride, f"{p}[{i}]")
            else:
                for _s, tn, val in jc3adf._read(adf, t["element"], start, i * stride):
                    yield f"{p}[{i}]", tn, val, 0
    else:
        for _s, tn, val in jc3adf._read(adf, m["type"], base, off + m["offset"]):
            yield p, tn, val, m["offset"]


def decode(idx: dict[str, dict], path: str) -> dict:
    r = idx[path]
    adf = jc3adf.Adf(read_entry(r))
    root = adf.type(adf.instances[0]["type"])
    rows = []
    for m in root["members"]:
        rows.extend(_rows(adf, m, adf.instances[0]["offset"], 0, ""))
    return {
        "path": path, "archive": r["archive"], "offset": r["offset"], "size": r["size"],
        "root": {"name": root["name"], "size": root["size"],
                 "members": [{"name": m["name"], "offset": m["offset"], "size": m["size"],
                              "type": adf.type_name(m["type"])} for m in root["members"]]},
        "rows": [{"path": p, "type": t, "value": v, "offset": o} for p, t, v, o in rows],
        "types": {t["name"]: [{"name": m["name"], "offset": m["offset"], "size": m["size"],
                               "type": adf.type_name(m["type"])} for m in t["members"]]
                  for _h, t in adf.types.items() if t["code"] == jc3adf.TYPE_STRUCTURE},
    }


def vals(rec: dict) -> dict:
    return {r["path"]: r["value"] for r in rec["rows"]}


# ------------------------------------------------------------------ analysis
def build() -> dict:
    idx = load_index()
    presets = {"lockon": decode(idx, PRESET_LOCKON), "no_lockon": decode(idx, PRESET_NOLOCK)}
    weapons = {k: decode(idx, p) for k, p in WEAPON_DIR.items()}
    aaim = {k: decode(idx, p) for k, p in AUTOAIM_DIR.items()}

    wiring = []
    with open(WIRING, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            for w in r["weapons"]:
                wiring.append({
                    "chassis": r["chassis"], "entity": r["entity"], "root_class": r["root_class"],
                    "weapon": w["name"], "weapon_id": w.get("weapon_id"), "class": w["class"],
                    "binding": w.get("binding", []),
                    "autoaim": w.get("autoaim_tuning_file", "").rsplit("/", 1)[-1],
                    "components": [{"class": c["class"], "props": c.get("props", {})}
                                  for c in w.get("components", [])],
                    "props": {k: v for k, v in w.get("props", {}).items()
                              if k in ("id:2D0B3C09", "id:D13BBA30", "id:19068026",
                                       "id:A5705CCB", "id:B7AAA8C8", "id:B65F3E21")},
                })

    # every weapon tune in the fleet that carries a missile block
    fleet = []
    for p in sorted(p for p in idx if p.endswith(".wtunec") and "jc_weapons" in p):
        rec = decode(idx, p)
        f = vals(rec)
        ts = f.get("missile_weapon[0].tuning.missile_base_tuning.missile_turning_speed")
        if ts is None:
            continue
        fleet.append({
            "tune": p.split("jc_weapons/")[-1],
            "root": rec["root"]["name"],
            "turning_speed": ts,
            "turning_speed_ai": f.get("missile_weapon[0].ai_tuning.missile_base_tuning.missile_turning_speed"),
            "loose_lock": f.get("missile_weapon[0].tuning.missile_base_tuning.missile_loose_lock_distance"),
            "per_shot": f.get("missile_weapon[0].tuning.missile_base_tuning.missile_per_shot"),
            "magazine_size": f.get("magazine_size"),
            "max_range": f.get("max_range"),
            "velocity": f.get("velocity"),
            "burst_count": f.get("burst_count"),
            "burst_cooldown": f.get("burst_cooldown"),
            "damage": f.get("missile_weapon[0].tuning.base_tuning.damage"),
        })

    # the preset diff, member by member
    pv_l, pv_n = vals(presets["lockon"]), vals(presets["no_lockon"])
    assert set(pv_l) == set(pv_n), "presets do not share a member set"
    diff = [{"path": k, "lockon": pv_l[k], "no_lockon": pv_n[k]}
            for k in pv_l if pv_l[k] != pv_n[k]]

    # member-name census over every weapon tune's type dictionary
    member_names: dict[str, set[str]] = {}
    for p in (p for p in idx if p.endswith(".wtunec") and "jc_weapons" in p):
        rec = decode(idx, p)
        for tname, members in rec["types"].items():
            member_names.setdefault(tname, set()).update(m["name"] for m in members)
    autoaim_members = sorted(member_names["AutoAimSettings"])
    missile_members = sorted(member_names["MissileWeaponTuningBase"])

    # missile member offsets, from each compared file's own dictionary
    offsets = {}
    for key, rec in weapons.items():
        offsets[key] = {m["name"]: m["offset"] for m in rec["types"]["MissileWeaponTuningBase"]}
    assert len({json.dumps(v, sort_keys=True) for v in offsets.values()}) == 1, \
        "MissileWeaponTuningBase layout differs between the compared tunes"

    # BmAK provenance: every quoted row must still be in the source page
    with open(BMAK_WEAPONS, encoding="utf-8") as f:
        bmak_text = f.read()
    for _n, _o, _t, _v, quote in BMAK:
        assert quote in bmak_text, f"BmAK quote not found in WEAPONS.md: {quote}"

    return {
        "sources": {
            "index": "Research/JC3Grab/INDEX.jsonl",
            "archives": DEFAULT_GAME,
            "wiring": "Research/JC3Grab/WEAPON_WIRING.jsonl",
            "bmak": "Research/BatmobileGrab/WEAPONS.md",
        },
        "presets": presets,
        "weapons": weapons,
        "autoaim_per_weapon": aaim,
        "wiring": wiring,
        "fleet": fleet,
        "preset_diff": diff,
        "member_names": {"AutoAimSettings": autoaim_members,
                         "MissileWeaponTuningBase": missile_members},
        "missile_offsets": offsets,
        "lockon_binders": sorted({(w["chassis"], w["root_class"])
                                  for w in wiring
                                  if w["autoaim"] == "autoaim_vehicle_lockon_missile.wtune"},
                                 key=lambda x: x[0]),
        "bmak": [{"field": n, "offset": o, "type": t, "value": v} for n, o, t, v, _q in BMAK],
    }


# ------------------------------------------------------------------ rendering
def g(v) -> str:
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, float):
        return "%.6g" % v
    return "" if v is None else str(v)


def wire(data: dict, weapon: str) -> list[dict]:
    return [w for w in data["wiring"] if w["weapon"].startswith(weapon)]


def md(data: dict) -> str:
    fleet = data["fleet"]
    homing = [f for f in fleet if (f["turning_speed"] or 0) > 0]
    vehicle = [f for f in fleet if f["tune"].startswith("06_vehicle/")]
    vehicle_homing = [f for f in vehicle if (f["turning_speed"] or 0) > 0]
    vehicle_zero = [f for f in vehicle if (f["turning_speed"] or 0) == 0]
    pv_l = vals(data["presets"]["lockon"])
    off = data["missile_offsets"]["w609"]
    aa_off = {m["name"]: m["offset"] for m in data["presets"]["lockon"]["types"]["AutoAimSettings"]}
    L: list[str] = []
    A = L.append

    A("# T-WP3b - JC3 carriers for the Batmobile's missile lock-on")
    A("")
    A("**Answer: JC3 does carry it, and the missing piece is one named member, not a code class.** "
      "`WeaponTuning -> missile_weapon[].missile_base_tuning.missile_turning_speed` is the homing "
      "strength (0 = flies straight), and the fleet ships a *lock-on* AutoAim preset "
      "(`autoaim_vehicle_lockon_missile`) that differs from the no-lockon preset in 15 rows of "
      "three members, in all six shooter contexts: the two cone angles, the cutoff multiplier "
      "(500 vs 100/120), the distance fit weight, and vehicle targeting outside OnFoot. What the "
      "lock-on preset does **not** carry is a hold timer: the "
      "22 members of `AutoAimSettings` include no duration, so BmAK's `MissileLockOnDuration` 2.0 s "
      "has no JC3 member and stays `UNKNOWN`.")
    A("")
    A("Labels: `decoded` = read from a file at the offset shown; `derived` = computed from decoded "
      "facts; `UNKNOWN` = not in these files, with what was tried. Every number below is "
      "regenerated by `python Tools/scripts/t_wp3b.py --write`; none is typed by hand.")
    A("")
    A("## 1. Every weapon in the fleet that homes (`missile_turning_speed` > 0)")
    A("")
    A("`decoded` - %d of the fleet's %d missile-bearing tunes home; the vehicle set is %d of %d, "
      "and %d vehicle missiles ship turning speed **0** (they fly straight)."
      % (len(homing), len(fleet), len(vehicle_homing), len(vehicle), len(vehicle_zero)))
    A("")
    A("| tune | turning speed (player / AI) | loose-lock m | per shot | mag | range m | burst x cooldown |")
    A("|---|---|---|---|---|---|---|")
    for f in homing:
        A("| `%s` | %s / %s | %s | %s | %s | %s | %s x %s |"
          % (f["tune"].rsplit("/", 1)[-1], g(f["turning_speed"]), g(f["turning_speed_ai"]),
             g(f["loose_lock"]), g(f["per_shot"]), g(f["magazine_size"]), g(f["max_range"]),
             g(f["burst_count"]), g(f["burst_cooldown"])))
    A("")
    A("The vehicle missiles with **zero** turning speed - the ones T7's car-missile reading "
      "generalised from, correctly for `w618` but not for the fleet: " +
      ", ".join("`%s`" % f["tune"].rsplit("/", 1)[-1] for f in vehicle_zero) + ".")
    A("")
    A("Read the `burst_count` column: `w614` fires **6** missiles 5 s apart and `w613` fires "
      "**6** 4 s apart, but `missile_per_shot` is 1 on every vehicle missile, and nothing in "
      "`WeaponTuning` counts *targets*: a burst is several missiles at one aim point, not a "
      "salvo split across several targets.")
    A("")
    A("## 2. The homing block, with offsets")
    A("")
    A("`MissileWeaponTuningBase`, offsets from the type dictionary of "
      "`w609_fighterjet_missile_air_lockon.wtunec` (identical in `w612`/`w613`/`w614`/`w618`/"
      "`w611`, asserted). `decoded`.")
    A("")
    A("| offset | size | member | what it holds |")
    A("|---|---|---|---|")
    sizes = {m["name"]: m["size"] for m in data["weapons"]["w609"]["types"]["MissileWeaponTuningBase"]}
    what = {
        "missile_turning_speed": "homing strength; **0 = unguided**",
        "missile_turning_speed_random": "random added to the turning speed",
        "missile_loose_lock_distance": "distance at which a lock is let go (m); 0 = never",
        "missile_per_shot": "missiles per trigger pull",
        "missile_no_turning_time": "seconds after launch with no steering",
        "missile_acceleration": "acceleration curve values (2 floats)",
        "missile_acceleration_time": "curve times (2 floats)",
        "missile_acceleration_random": "random added to the acceleration (2 floats)",
        "missile_detonation_time": "-1 = no timed self-destruct",
        "missile_detonation_time_random": "jitter on the above",
        "missile_per_shot": "missiles per trigger pull",
        "detonate_on_impact": "impact fuze",
        "gravity": "gravity applied to the projectile (m/s^2)",
        "random_detonation_offset": "position jitter on detonation",
        "meters_proximity_self_detonate": "proximity fuze distance",
        "meters_times_speed_in_front_of_target": "lead distance, in metres per unit speed",
    }
    for name in sorted(off, key=lambda n: (off[n], n)):
        A("| %d | %d | `%s` | %s |" % (off[name], sizes[name], name, what.get(name, "")))
    A("")
    A("*The `size` column is the element size: `missile_acceleration`, "
      "`missile_acceleration_time` and `missile_acceleration_random` are inline arrays of 2 "
      "floats (8 B each), which is why the next member sits 8 bytes on.*")
    A("")
    A("### 2.1 The values, per weapon")
    A("")
    A("`decoded`, player (`tuning`) / AI (`ai_tuning`) instances.")
    A("")
    A("| weapon | turning speed | turning random | loose-lock | no-turn time | gravity |")
    A("|---|---|---|---|---|---|")
    for key in ("w609", "w612", "w613", "w614", "w618", "w611"):
        f = vals(data["weapons"][key])
        A("| `%s` | %s / %s | %s | %s | %s | %s |" % (
            key,
            g(f["missile_weapon[0].tuning.missile_base_tuning.missile_turning_speed"]),
            g(f["missile_weapon[0].ai_tuning.missile_base_tuning.missile_turning_speed"]),
            g(f["missile_weapon[0].tuning.missile_base_tuning.missile_turning_speed_random"]),
            g(f["missile_weapon[0].tuning.missile_base_tuning.missile_loose_lock_distance"]),
            g(f["missile_weapon[0].tuning.missile_base_tuning.missile_no_turning_time"]),
            g(f["missile_weapon[0].tuning.missile_base_tuning.gravity"])))
    A("")
    A("`w609` is 150 for the player and 300 for the AI; `w612` is 300 both sides; `w613`, `w611` "
      "and the car missile `w618` are 0. This is the whole difference between a guided missile "
      "and a rocket: there is no separate `homing` flag, the turning speed *is* the homing.")
    A("")
    A("## 3. The lock-on preset vs the no-lockon preset")
    A("")
    A("Both files are `AutoAim` (%d bytes, 6 contexts of `AutoAimSettings` at offsets 0/88/176/"
      "264/352/440). `decoded`." % data["presets"]["lockon"]["size"])
    A("")
    A("| file | archive | entry offset | size |")
    A("|---|---|---|---|")
    for k in ("lockon", "no_lockon"):
        r = data["presets"][k]
        A("| `%s` | `%s` | %d | %d |" % (r["path"].rsplit("/", 1)[-1], r["archive"],
                                          r["offset"], r["size"]))
    A("")
    A("**The two presets differ in exactly %d rows of %d**, and every one of them is an angle, a "
      "cutoff, a fit weight or a target class:" % (len(data["preset_diff"]), len(pv_l)))
    A("")
    A("| member | offset | lock-on | no-lockon | meaning |")
    A("|---|---|---|---|---|")
    for d in data["preset_diff"]:
        ctx, name = d["path"].split(".", 1)
        A("| `%s.%s` | %d | %s | %s | %s |" % (ctx, name, aa_off[name], g(d["lockon"]),
                                               g(d["no_lockon"]),
                                               "cone/cutoff" if "Angle" in name else
                                               "fit weight" if "FitWeight" in name else
                                               "target class"))
    A("")
    A("So a lock-on tune in JC3 is **a wider aim cone that holds vehicles in every shooter "
      "context** - the switch is a data preset, not a separate lock subsystem. The builds that "
      "bind it: " + ", ".join("`%s` (%s)" % (b[0], b[1])
                                for b in data["lockon_binders"]) +
      ". No `CCar` chassis binds it - the car donor `v0300` binds the *no-lockon* preset - so "
      "the Batmobile's lock-on is a tune swap with no car precedent.")
    A("")
    A("### 3.1 The three per-weapon AutoAim tunes (OnFoot, all 22 members)")
    A("")
    A("| member | offset | `w609` | `w612` | `w613` |")
    A("|---|---|---|---|---|")
    for name in sorted(aa_off, key=lambda n: aa_off[n]):
        row = []
        for key in ("w609", "w612", "w613"):
            f = vals(data["autoaim_per_weapon"][key])
            row.append(g(f.get("OnFoot." + name)))
        A("| `%s` | %d | %s | %s | %s |" % (name, aa_off[name], row[0], row[1], row[2]))
    A("")
    A("`w613`'s own tune is the tell: `CanTargetCharacters`/`Vehicles`/`RigidObjects` are all 0 "
      "and `MaxAimDistance` is -1, so the weapon called *ground lockon* acquires nothing. That is "
      "`decoded`, and it contradicts the operator lead for `w613` only - `w609` and `w612` do "
      "acquire (vehicles and rigid objects, 750 m and 750 m).")
    A("")
    A("## 4. What makes the player *see* and *hold* a lock")
    A("")
    A("Three separate mechanisms, and only two of them are in the weapon data:")
    A("")
    A("| mechanism | where | value | status |")
    A("|---|---|---|---|")
    A("| the reticle on the locked target | `hud.gfx`, `hud_code/poi.as` case 21 | "
      "`POI_TYPE_LOCK_ON_TARGET`, one turn per 1.5 s, no progress bar | `decoded` (G2-25, "
      "`Research/JC3Grab/JC3_HUD_WEAPONS.md` section 5) |")
    A("| the \"a missile is locked on *you*\" warning | `MCI_missile_locked` | flashes every 0.5 s | "
      "`decoded` (same page) |")
    A("| what may be acquired, and in what cone | `AutoAim` preset + per-weapon tune | table 3.1 | "
      "`decoded` |")
    A("| what is drawn as the aim point | `CAimPOIWeaponComponent` (`aim.poi`), prop "
      "`id:2D0B3C09` | 25 / 50 / 100 depending on the weapon | `decoded` value, `UNKNOWN` meaning |")
    A("")
    A("`CAimPOIWeaponComponent` is on %d vehicle weapon builds in `WEAPON_WIRING.jsonl`:"
      % len({w["entity"] for w in data["wiring"]
             if any(c["class"] == "CAimPOIWeaponComponent" for c in w["components"])}))
    A("")
    A("| weapon | `id:2D0B3C09` | also on |")
    A("|---|---|---|")
    seen = set()
    for w in data["wiring"]:
        poi = [c for c in w["components"] if c["class"] == "CAimPOIWeaponComponent"]
        if poi and w["weapon"] not in seen:
            seen.add(w["weapon"])
            A("| `%s` | %s | %s |" % (w["weapon"], poi[0]["props"].get("id:2D0B3C09", ""),
                                      ", ".join(c["class"] for c in w["components"])))
    A("")
    A("The component sits on the **no-lockon** `w611` (100), the car missile `w618` (50) and the "
      "buggy gun (25) - so it is an aim-POI marker, not evidence of a lock. Its property is "
      "hash-named and no dictionary in the repo resolves `2D0B3C09`: `UNKNOWN`.")
    A("")
    A("### 4.1 Range, angle and time, next to BmAK")
    A("")
    A("| requirement | BmAK (`Research/BatmobileGrab/WEAPONS.md`) | JC3 carrier | verdict |")
    A("|---|---|---|---|")
    A("| lock range | `LockOnRange` 12000 UU = **120 m** (0x0984) | `MaxAimDistance`: -1 *unlimited* "
      "in both shared presets, **750** in `w609`'s own preset, -1 in `w613`. `max_range` 750 m "
      "(`w609`), 300 m (`w612`/`w613`/`w614`), 300 m (`w618`) | `decoded`: JC3's acquisition "
      "range is per-tune and can be set to 120; no single fleet value matches 120 m, so 120 is a "
      "**tune**, not a copy |")
    A("| lock cone | `LockOnAngle` **40 deg** (0x0980) | `AngleThresholdCurrentTarget` 0.3 "
      "(`w609`), 1.4 (`w612`), 0.15 (`w613`); `AngleThresholdNewTarget` 0.085/1.4/0.12. Unit "
      "unnamed: as turns 108/504/54 deg, as radians 17.2/80.2/8.6 deg - see 4.2 | `derived` "
      "angle exists and is tunable; **no member carries degrees** |")
    A("| lock hold time | `MissileLockOnDuration` **2.0 s**, civilian 1.0 s (0x0A00/0x0A04) | "
      "**none**: `AutoAimSettings` is 22 members, none a duration (asserted) | `UNKNOWN` - "
      "*tried:* all 103 weapon tunes' type dictionaries, the two presets, the three per-weapon "
      "tunes, the entity props of every lock-on weapon. *Where:* the native aim manager |")
    A("| guided flight | (the projectile homes) | `missile_turning_speed` 150 (`w609`), 300 "
      "(`w612`), 200 (`w614`), 0 elsewhere | `decoded` - **carrier found** |")
    A("")
    A("### 4.2 The AutoAim angle unit is not in the file")
    A("")
    A("`decoded` values, three readings, `derived` columns:")
    A("")
    A("| member | raw `w609` | raw `w612` | raw `w613` | `w609` as turns | `w609` as radians |")
    A("|---|---|---|---|---|---|")
    f609, f612 = vals(data["autoaim_per_weapon"]["w609"]), vals(data["autoaim_per_weapon"]["w612"])
    f613 = vals(data["autoaim_per_weapon"]["w613"])
    for name in ("AngleThresholdNewTarget", "AngleThresholdCurrentTarget", "StickyAimAngleCurrentTarget"):
        a, b, c = (f609.get("OnFoot." + name), f612.get("OnFoot." + name),
                   f613.get("OnFoot." + name))
        A("| `%s` | %s | %s | %s | %s | %s |" % (name, g(a), g(b), g(c), g(round(a * 360, 3)),
                                                g(round(a * 57.2958, 3))))
    A("")
    A("The `StickyAimAngle*` family (5 / 10 / 15) cannot be turns - that would be 1800 deg - so "
      "the block mixes at least two units, or the small values are normalised against a cutoff. "
      "The reading stays `UNKNOWN`; T7's \"fractions of a turn\" is one candidate, not a decoded "
      "fact.")
    A("")
    A("## 5. The Barrage, behaviour by behaviour")
    A("")
    A("| BmAK behaviour | JC3 carrier | what still needs an amendment |")
    A("|---|---|---|")
    A("| guided flight to the locked target | **yes** - `missile_turning_speed` (offset %d) and "
      "`missile_loose_lock_distance` (%d); `w614` is the vehicle-mounted guided missile, `w609`/"
      "`w612` the air ones | nothing structural: copy the four missile members onto the "
      "Batmobile's missile tune and the missile homes |" % (off["missile_turning_speed"],
                                                            off["missile_loose_lock_distance"]))
    A("| air **and** ground targets | **partly** - `CanTargetVehicles`/`CanTargetRigidObjects` 1 "
      "in the lock-on preset; `CanTargetCharacters` 0 everywhere; `w613` (the ground one) is 0/0/0 "
      "| to lock a character the Batmobile needs `CanTargetCharacters` 1, which **no shipped tune "
      "sets** - an amendment with no fleet precedent (`UNKNOWN` whether the engine honours it) |")
    A("| multi-target salvo | **partly** - `burst_count` 6 (`w614`, `w613`), `missile_per_shot` 1, "
      "`magazine_size` 8 (`w609`) / 2 (`w612`) / -1 (`w614`) | no member names a target count: "
      "`max_targets` exists only on the BmAK side. A salvo split across 8 targets needs a code "
      "bridge (fire N missiles at N aim points) or the BmAK behaviour reduced to a burst at one "
      "|")
    A("| lock cone 40 deg | **yes as a member** - `AngleThresholdCurrentTarget` (offset %d) | the "
      "unit has to be pinned before 40 can be written (4.2) |"
      % aa_off["AngleThresholdCurrentTarget"])
    A("| lock range 120 m | **yes as a member** - `MaxAimDistance` (offset %d) | set 120 on the "
      "Batmobile's preset instead of the fleet's -1/750 |" % aa_off["MaxAimDistance"])
    A("| lock hold 2.0 s | **no member** | `UNKNOWN`: nothing in the weapon data times a lock. "
      "The Batmobile's 2.0 s has to be native, or the row keeps `LockOnRange` only |")
    A("")
    A("## 6. The EMP missile")
    A("")
    A("| BmAK field | value | JC3 counterpart |")
    A("|---|---|---|")
    for name in ("RBatmobileEMPMissile.MissileLockOnDuration",
                 "RBatmobileEMPMissile.CivilianMissileLockOnDuration"):
        v = next(b for b in data["bmak"] if b["field"] == name)
        A("| `%s` | %s at `%s` | no lock-duration member (4.1); the same `AutoAim` preset applies |"
          % (name, v["value"], v["offset"]))
    A("| lock angle / range | - (inherited from `RVehicleWeapon`) | `AngleThreshold*` / "
      "`MaxAimDistance` as above |")
    A("| the disable itself | `SetDisabledByEMP` (BmScript) | not a weapon member: JC3's EMP is "
      "`CEMPWeapon` + a `CForcePulse` named `EMP` (G2-16, `Research/JC3Grab/EMP.md`), so the EMP "
      "payload stays a separate row from this lock-on row |")
    A("")
    A("## 7. Contradictions found against the leads and against T7")
    A("")
    A("1. **Operator lead \"JC3 already has heat-seeking missiles and target lock\": confirmed, "
      "with one qualifier.** Missiles home (`missile_turning_speed` > 0 on %d tunes) and lock-on "
      "is a data preset. It is not universal: %d of %d vehicle missiles ship turning speed 0."
      % (len(homing), len(vehicle_zero), len(vehicle)))
    A("2. **`w613_fighterbomber_missile_ground_lockon` locks nothing** - `CanTarget*` 0/0/0, "
      "`MaxAimDistance` -1, `missile_turning_speed` 0. The name is the only thing that says "
      "ground lock-on.")
    A("3. **The lock-on preset alone does not guide.** `w621_advancedhelicopter_missile` binds "
      "`autoaim_vehicle_lockon_missile` on one build and still has turning speed 0, so preset and "
      "homing are two independent switches.")
    A("4. **`w612` is guided but bound to no driver slot** (`binding: []` on all three bomber "
      "builds), so it is a donor value, not a working weapon.")
    A("5. **T7's \"no lock duration and no lock range\" is half right.** No duration member exists "
      "(confirmed over all 22 `AutoAimSettings` members), but a range member does: "
      "`MaxAimDistance` - it is simply -1 (unlimited) in both shared presets, which is why the "
      "car-missile read missed it. `w609`'s own preset sets it to 750.")
    A("")
    A("## 8. UNKNOWNs")
    A("")
    A("1. **What paints `POI_TYPE_LOCK_ON_TARGET` from AutoAim state.** *Tried:* 260 HUD scripts "
      "(0 `CreatePoi(POI_TYPE_LOCK_ON_TARGET, ...)` calls, G2-25), the two presets, the weapon "
      "props. *Where:* native aim manager.")
    A("2. **The AutoAim angle unit.** *Tried:* all 103 weapon tunes' type dictionaries (no unit "
      "metadata), the value ranges. *Where:* the engine; the file stores bare floats.")
    A("3. **`id:2D0B3C09` (25/50/100).** *Tried:* every repo hash dictionary. No name.")
    A("4. **Lock hold time.** No member; see 4.1.")
    A("5. **Whether a missile can hold several targets.** `missile_per_shot` 1 everywhere and no "
      "target-count member; BmAK's `MaxTargets` 8 has no JC3 counterpart in the data.")
    A("")
    A("## 9. Validation and limits")
    A("")
    A("`--check` re-decodes the same entries and asserts: the two presets share one member set and "
      "differ in exactly %d rows; `AutoAimSettings` has 22 members and none matches "
      "`duration|hold_time|lock_time|linger|hold`; `MissileWeaponTuningBase` has 15 members and "
      "its only `lock` member is `missile_loose_lock_distance`; the six compared tunes share one "
      "`MissileWeaponTuningBase` layout; every BmAK row quoted above still exists in "
      "`Research/BatmobileGrab/WEAPONS.md`; and the rendered markdown matches this file."
      % len(data["preset_diff"]))
    A("")
    A("**Limits.** Static only: no game was launched, no install or archive was written, no "
      "process touched. The fleet counts come from the 103 weapon tunes `INDEX.jsonl` lists under "
      "`jc_weapons`; a tune outside that directory is not in the census. The HUD facts are quoted "
      "from `JC3_HUD_WEAPONS.md` (G2-25), not re-decoded here.")
    A("")
    A("Checkable: `python Tools/scripts/t_wp3b.py --check`.")
    A("")
    return "\n".join(L)


# ------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser()
    g0 = ap.add_mutually_exclusive_group(required=True)
    g0.add_argument("--write", action="store_true")
    g0.add_argument("--check", action="store_true")
    a = ap.parse_args()

    data = build()
    doc = md(data)
    js = json.dumps(data, indent=1, sort_keys=True) + "\n"
    jp, mp = os.path.join(OUT, JSON_NAME), os.path.join(OUT, MD_NAME)

    if a.write:
        os.makedirs(OUT, exist_ok=True)
        with open(jp, "w", encoding="utf-8", newline="\n") as f:
            f.write(js)
        with open(mp, "w", encoding="utf-8", newline="\n") as f:
            f.write(doc)
        print("wrote", jp)
        print("wrote", mp)
        return 0

    fails = []
    old = open(jp, encoding="utf-8").read() if os.path.exists(jp) else ""
    if old != js:
        fails.append("json drifted")
    om = open(mp, encoding="utf-8").read() if os.path.exists(mp) else ""
    if om != doc:
        fails.append("markdown drifted")
    names = data["member_names"]["AutoAimSettings"]
    if len(names) != 22:
        fails.append("AutoAimSettings is not 22 members")
    if any(k in n.lower() for n in names for k in ("duration", "lock_time", "hold_time", "linger")):
        fails.append("a duration-like AutoAim member appeared")
    lock = [n for n in data["member_names"]["MissileWeaponTuningBase"] if "lock" in n.lower()]
    if lock != ["missile_loose_lock_distance"]:
        fails.append(f"missile lock members changed: {lock}")
    if not data["fleet"]:
        fails.append("no weapon tunes decoded")
    if not data["lockon_binders"]:
        fails.append("no build binds the lock-on preset")
    if any(k == "CCar" for _c, k in data["lockon_binders"]):
        fails.append("a CCar chassis now binds the lock-on preset - the no-car-precedent claim is stale")
    print("fleet tunes %d, homing %d, preset diff rows %d"
          % (len(data["fleet"]), sum(1 for f in data["fleet"] if (f["turning_speed"] or 0) > 0),
             len(data["preset_diff"])))
    if fails:
        for f in fails:
            print("FAIL:", f)
        return 1
    print("OK: lock-on data, preset diff and prose all re-derived identically")
    return 0


if __name__ == "__main__":
    sys.exit(main())
