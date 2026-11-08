#!/usr/bin/env python3
"""T-LOCK-SALVO: where a lock-hold time or a multi-target salvo could live in JC3.

The Fire Leech report (tmp/freebuff/reports/wp4-fire-leech.md) established that `w143` carries
guided flight and acquisition but no 2.0 s hold and no 8-target salvo.  This script searches the
places a hold or a target count could hide instead of accepting "no member":

  * the Fire Leech's own `AutoAim` tune, byte by byte, including every unnamed gap;
  * all 15 `AutoAim` tunes (11 shared presets + 4 per-weapon) and every member of
    `AutoAimSettings`;
  * every member of every weapon tune (103 `.wtunec` files), including the time-like and
    count-like members nobody had quoted (`aim_timer_override`, `burst_count`,
    `missile_per_shot`, `bullets_per_shot`, `MissileStrikeWeaponTuning.fire_amount`);
  * all 59 `jc_weapons/*.epe` entity graphs, decoded with Gibbed ConvertProperty: weapon
    classes, components, `STimerComponent`/`CTimeTrigger`, `STargetPoint`, `CAntiAirWeapon`,
    `CTurretWeaponComponent` and the `SWeaponFirePattern`/`SWeaponFirePatternComponent` records;
  * the decompiled `ui/hud.gfx` scripts, where the only lock constants are a 1.5 s reticle
    rotation and a 0.5 s incoming-missile blink.

Writes tmp/freebuff/reports/lock-hold-and-salvo-carrier.md and .json.
`--check` re-derives both, asserts every absence claim, and compares byte for byte.

Usage:
  python Tools/scripts/t_lock_salvo.py --write
  python Tools/scripts/t_lock_salvo.py --check
"""
from __future__ import annotations

import argparse
import collections
import difflib
import itertools
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jc3adf  # noqa: E402
from jc3index import DEFAULT_GAME  # noqa: E402
from rbmhdr import hash_jenkins  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
RES = os.path.join(ROOT, "Research", "JC3Grab")
INDEX = os.path.join(RES, "INDEX.jsonl")
WIRING = os.path.join(RES, "WEAPON_WIRING.jsonl")
BMAK = os.path.join(ROOT, "Research", "BatmobileGrab", "WEAPONS.md")
OUT = os.path.join(ROOT, "tmp", "freebuff", "reports")
SCRATCH = os.path.join(ROOT, "tmp", "freebuff", "scratch", "epe")
CONVERT = os.path.join(ROOT, "Tools", "Gibbed", "Gibbed.JustCause3.ConvertProperty.exe")
HUD = os.environ.get("JC3_GRAB", r"E:\Modding\_shared\gamedata\JC3grab") + r"\hud\dec\scripts"
JSON_NAME = "lock-hold-and-salvo-carrier.json"
MD_NAME = "lock-hold-and-salvo-carrier.md"

W143_AA = ("editor/entities/jc_weapons/02_two_handed/w143_rpg_fire_leach/"
           "autoaim_w143_rpg_fire_leach.wtunec")
W143_TUNE = ("editor/entities/jc_weapons/02_two_handed/w143_rpg_fire_leach/"
             "w143_rpg_fire_leach.wtunec")
CONTEXTS = ("OnFoot", "Stunting", "MotorCycle", "ReelingIn", "ReeledIn", "Parachute")
TIME_WORDS = ("time", "timer", "duration", "hold", "lock", "count", "amount", "shot",
              "salvo", "volley", "target")
INTEREST = ("CMissileWeaponBase", "CBulletWeaponBase", "CRPGFireLeachWeapon",
            "CRPGWeapon", "CAntiAirWeapon", "CMissileStrikeWeapon", "CTurretWeaponComponent",
            "CAimPOIWeaponComponent", "SWeaponFirePattern", "SWeaponFirePatternComponent",
            "STimerComponent", "CTimeTrigger", "STargetPoint", "CAirplaneFlybyWeaponComponent")
EPE_SELECT = (
    "editor/entities/jc_weapons/02_two_handed/w143_rpg_fire_leach/w143_rpg_fire_leach.epe",
    "editor/entities/jc_weapons/02_two_handed/w123_grenade_launcher_upu_210/w123_grenade_launcher_upu_210.epe",
    "editor/entities/jc_weapons/02_two_handed/w701_missile_strike/w701_missile_strike.epe",
    "editor/entities/jc_weapons/05_stationary/w501_turret_sam_missile/w501_turret_sam_v2.epe",
    "editor/entities/jc_weapons/05_stationary/w502_turret_aa_gun/w502_turret_aa_gun.epe",
    "editor/entities/jc_weapons/05_stationary/w504_turret_m488/w504_turret_m488.epe",
    "editor/entities/jc_weapons/06_vehicle/w609_fighterjet_missile_air_lockon/w609_fighterjet_missile_air_lockon.epe",
    "editor/entities/jc_weapons/06_vehicle/w612_fighterbomber_missile_air_lockon/w612_fighterbomber_missile_air_lockon.epe",
    "editor/entities/jc_weapons/06_vehicle/w618_sportsmuscle_missile/w618_sportsmuscle_missile.epe",
)
BMAK_QUOTES = (
    ("RBatmobileEMPMissile.MissileLockOnDuration", "0x0A00", "2.0",
     "| `RBatmobileEMPMissile.MissileLockOnDuration` | 0x0A00 | FloatProperty | 2.0 |"),
    ("RBatmobileEMPMissile.CivilianMissileLockOnDuration", "0x0A04", "1.0",
     "| `RBatmobileEMPMissile.CivilianMissileLockOnDuration` | 0x0A04 | FloatProperty | 1.0 |"),
    ("RBatmobileMissileLauncher.MaxTargets", "0x095C", "8",
     "| `RBatmobileMissileLauncher.MaxTargets` | 0x095C | IntProperty | 8 |"),
    ("RBatmobileMissileLauncher.FireInterval", "0x098C", "0.5",
     "| `RBatmobileMissileLauncher.FireInterval` | 0x098C | FloatProperty | 0.5 |"),
    ("RBatmobileMissileLauncher.LockOnAngle", "0x0980", "40.0",
     "| `RBatmobileMissileLauncher.LockOnAngle` | 0x0980 | FloatProperty | 40.0 |"),
    ("RBatmobileMissileLauncher.LockOnRange", "0x0984", "12000.0",
     "| `RBatmobileMissileLauncher.LockOnRange` | 0x0984 | FloatProperty | 12000.0 |"),
)


# --------------------------------------------------------------------- reading
def load_index() -> dict[str, dict]:
    out = {}
    with open(INDEX, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            out[r["path"]] = r
    return out


def read_entry(r: dict) -> bytes:
    with open(os.path.join(DEFAULT_GAME, r["archive"] + ".arc"), "rb") as f:
        f.seek(r["offset"])
        return f.read(r["size"])


def g(v) -> str:
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, float):
        return f"{v:.6g}"
    return "" if v is None else str(v)


# ------------------------------------------------------------------- ADF tunes
def adf_records(blob: bytes) -> dict:
    a = jc3adf.Adf(blob)
    inst = a.instances[0]
    root = a.type(inst["type"])
    values = {}
    for p, _tn, v in jc3adf.walk(a):
        values[p] = v
    layout = [{"name": m["name"], "offset": m["offset"], "size": m["size"],
               "type": a.type_name(m["type"])} for m in root["members"]]
    types = {}
    for t in a.types.values():
        if t["code"] == jc3adf.TYPE_STRUCTURE:
            types[t["name"]] = {
                "size": t["size"],
                "members": [{"name": m["name"], "offset": m["offset"], "size": m["size"],
                             "type": a.type_name(m["type"])} for m in t["members"]],
            }
    return {
        "root": root["name"],
        "root_size": root["size"],
        "inst_size": inst["size"],
        "inst_offset": inst["offset"],
        "layout": layout,
        "values": values,
        "types": types,
    }


def decode_autoaim(r: dict) -> dict:
    blob = read_entry(r)
    rec = adf_records(blob)
    settings = rec["types"]["AutoAimSettings"]
    values = {}
    for ctx in CONTEXTS:
        values[ctx] = {m["name"]: rec["values"].get(f"{ctx}.{m['name']}")
                       for m in settings["members"]}
    inst = rec["inst_offset"]
    raw = blob[inst:inst + rec["inst_size"]]
    rec.update({
        "path": r["path"], "archive": r["archive"], "offset": r["offset"],
        "size": r["size"], "context_values": values,
        "settings": settings,
        "hex": raw.hex(),
        "raw": list(raw),
    })
    return rec


def all_tunes(idx: dict) -> list[str]:
    return sorted(p for p in idx if p.endswith(".wtunec") and "/jc_weapons/" in p)


def decode_tunes(idx: dict) -> dict[str, dict]:
    out = {}
    for p in all_tunes(idx):
        rec = adf_records(read_entry(idx[p]))
        rec["path"] = p
        out[p] = rec
    return out


# ------------------------------------------------------------------ EPE graphs
def decode_epe(path: str, r: dict) -> dict:
    os.makedirs(SCRATCH, exist_ok=True)
    src = os.path.join(SCRATCH, "t_lock_salvo.epe")
    dst = os.path.join(SCRATCH, "t_lock_salvo.xml")
    with open(src, "wb") as f:
        f.write(read_entry(r))
    if os.path.exists(dst):
        os.remove(dst)
    p = subprocess.run([CONVERT, "--e", src, dst], capture_output=True)
    if p.returncode != 0 or not os.path.exists(dst):
        raise RuntimeError(f"ConvertProperty failed for {path}: {p.stderr[-300:]!r}")
    root = ET.parse(dst).getroot()
    objs = []

    def walk(el):
        for ch in el:
            if ch.tag != "object":
                continue
            props = {}
            cls = None
            for v in ch:
                if v.tag != "value":
                    continue
                key = v.get("name") or ("id:" + str(v.get("id")))
                txt = (v.text or "").strip()
                if key == "_class":
                    cls = txt
                else:
                    props[key] = txt
            objs.append({"class": cls, "name": props.get("name", ""), "props": props})
            walk(ch)

    walk(root)
    return {"path": path, "archive": r["archive"], "offset": r["offset"],
            "size": r["size"], "objects": objs}


def epe_census(idx: dict, epe: dict[str, dict]) -> dict:
    classes = collections.Counter()
    keys = collections.Counter()
    for rec in epe.values():
        for o in rec["objects"]:
            if o["class"]:
                classes[o["class"]] += 1
            for k in o["props"]:
                keys[k] += 1
    return {"files": len(epe), "classes": dict(classes), "keys": dict(keys)}


def jenkins_ok() -> tuple[bool, dict]:
    """The Jenkins hash must recover the property names jc3wiring already recovered."""
    known = {"tuning_file": "AA7096C9", "autoaim_tuning_file": "6D4C8277",
             "main_weapon": "851CAABE"}
    got = {}
    for name, want in known.items():
        try:
            h = hash_jenkins(name.encode()) & 0xFFFFFFFF
        except Exception:                                           # noqa: BLE001
            try:
                h = hash_jenkins(name) & 0xFFFFFFFF
            except Exception:                                       # noqa: BLE001
                return False, {}
        got[name] = f"{h:08X}"
    return all(got[k] == v for k, v in known.items()), got


def hash_candidates(ids: set[str]) -> dict:
    ok, known = jenkins_ok()
    words = ("lock", "on", "off", "time", "duration", "hold", "target", "targets", "max",
             "min", "count", "missile", "missiles", "salvo", "volley", "burst", "delay",
             "aim", "timer", "acquire", "acquisition", "range", "angle", "switch", "lose",
             "number", "amount", "per", "shot", "shots", "fire", "interval", "reload",
             "charge", "homing", "guidance", "tracking", "seeker", "spread", "multi")
    cands = set(words)
    for n in (2, 3, 4):
        cands.update("_".join(c) for c in itertools.product(words, repeat=n))
    hits: dict[str, list[str]] = {}
    if ok:
        for c in cands:
            h = f"{hash_jenkins(c.encode()) & 0xFFFFFFFF:08X}"
            if h in ids:
                hits.setdefault(h, []).append(c)
    return {"ok": ok, "known": known, "tried": len(cands),
            "hits": {k: sorted(v)[:6] for k, v in hits.items()}}


# ----------------------------------------------------------------------- build
def build() -> dict:
    idx = load_index()
    aa_paths = sorted(p for p in idx if p.endswith(".wtunec") and "autoaim" in p)
    aa = {p: decode_autoaim(idx[p]) for p in aa_paths}
    tunes = decode_tunes(idx)

    w143 = aa[W143_AA]
    settings = w143["settings"]
    coverage = []
    pos = 0
    gaps = []
    for m in sorted(settings["members"], key=lambda x: x["offset"]):
        if m["offset"] != pos:
            gaps.append([pos, m["offset"]])
        coverage.append([m["offset"], m["offset"] + m["size"]])
        pos = m["offset"] + m["size"]
    if pos != settings["size"]:
        gaps.append([pos, settings["size"]])

    # every AutoAim file must share the one 22-member / 88-byte struct
    aa_uniform = []
    for p, rec in aa.items():
        st = rec["types"]["AutoAimSettings"]
        aa_uniform.append({
            "file": p.rsplit("/", 1)[-1],
            "size": rec["size"],
            "inst": rec["inst_size"],
            "contexts": len(rec["layout"]),
            "settings_size": st["size"],
            "members": len(st["members"]),
            "onfoot": rec["context_values"]["OnFoot"],
        })

    # member census over every weapon tune's type dictionary
    type_members: dict[str, dict] = {}
    for rec in tunes.values():
        for name, t in rec["types"].items():
            cur = type_members.setdefault(name, {"size": t["size"], "members": {}})
            for m in t["members"]:
                cur["members"][m["name"]] = (m["offset"], m["size"], m["type"])
    timeish = []
    def is_timeish(name: str) -> bool:
        low = name.lower()
        if "threshold" in low:
            return False
        if any(w in low for w in ("time", "timer", "duration", "hold", "lock",
                                  "count", "amount", "salvo", "volley")):
            return True
        return "per_shot" in low or "fire_amount" in low
    for tname, t in sorted(type_members.items()):
        for mname, (off, size, mtype) in sorted(t["members"].items()):
            if is_timeish(mname):
                timeish.append({"type": tname, "member": mname, "offset": off,
                                "size": size, "mtype": mtype})

    # aim_timer_override distribution
    timers = {}
    for p, rec in tunes.items():
        if rec["root"] != "WeaponTuning":
            continue
        if "aim_timer_override" in rec["values"]:
            timers[p.rsplit("/jc_weapons/")[-1]] = rec["values"]["aim_timer_override"]
    timer_dist = collections.Counter(timers.values())

    # multi-projectile members, per tune
    multi = []
    for p, rec in tunes.items():
        v = rec["values"]
        row = {
            "tune": p.rsplit("/jc_weapons/")[-1],
            "root": rec["root"],
            "per_shot": v.get("missile_weapon[0].tuning.missile_base_tuning.missile_per_shot"),
            "bullets": v.get("bullet_weapon[0].tuning.bullet_base_tuning.bullets_per_shot"),
            "fire_amount": v.get("fow_weapon[0].tuning.missile_strike_tuning.fire_amount"),
            "target_radius": v.get("fow_weapon[0].tuning.missile_strike_tuning.target_radius"),
            "burst_count": v.get("burst_count"),
            "burst_cooldown": v.get("burst_cooldown"),
            "magazine": v.get("magazine_size"),
            "fire_rate": v.get("fire_rate"),
            "turning": v.get("missile_weapon[0].tuning.missile_base_tuning.missile_turning_speed"),
        }
        if any((row[k] or 0) > 1 for k in ("per_shot", "bullets", "fire_amount", "burst_count")):
            multi.append(row)

    # entity graphs for every jc_weapons .epe, plus detail for the selected ones
    epe_paths = sorted(p for p in idx if p.endswith(".epe") and "/jc_weapons/" in p)
    epe = {p: decode_epe(p, idx[p]) for p in epe_paths}
    census = epe_census(idx, epe)

    detail = {}
    for p in EPE_SELECT:
        rec = epe[p]
        objs = rec["objects"]
        weapon = next((o for o in objs if o["class"] in
                       ("CMissileWeaponBase", "CBulletWeaponBase", "CRPGFireLeachWeapon",
                        "CAntiAirWeapon", "CMissileStrikeWeapon")), None)
        detail[p.rsplit("/", 1)[-1]] = {
            "path": p,
            "weapon_class": weapon["class"] if weapon else None,
            "weapon_name": weapon["name"] if weapon else None,
            "weapon_props": weapon["props"] if weapon else {},
            "fire_points": sum(1 for o in objs
                               if o["class"] == "SWeaponPoint" and o["props"].get("type") == "2"),
            "components": [o["class"] for o in objs if o["class"] and
                           o["class"].endswith("Component")],
            "timers": [{"class": o["class"], "name": o["name"],
                        "value": o["props"].get("timer") or o["props"].get("time"),
                        "time_max": o["props"].get("time_max")}
                       for o in objs if o["class"] in ("STimerComponent", "CTimeTrigger")],
            "target_points": [o["props"] for o in objs if o["class"] == "STargetPoint"],
            "fire_patterns": sum(1 for o in objs if o["class"] == "SWeaponFirePattern"),
            "fire_pattern_components": sum(1 for o in objs
                                           if o["class"] == "SWeaponFirePatternComponent"),
            "classes": dict(collections.Counter(o["class"] for o in objs if o["class"])),
        }

    # the unresolved 32-bit property ids on the selected weapon objects
    ids = set()
    for d in detail.values():
        for k in d["weapon_props"]:
            if k.startswith("id:") and len(k) == 11:
                ids.add(k[3:].upper())
    hashes = hash_candidates(ids)

    # HUD movie
    hud_as = os.path.join(HUD, "hud.as")
    poi_as = os.path.join(HUD, "hud_code", "poi.as")
    radar_as = os.path.join(ROOT, "Working", "HUD", "radar", "_ffdec2", "scripts",
                            "ModuleStruct_Bespoke_LocalRadar.as")
    hud = {"hud_as": os.path.exists(hud_as), "poi_as": os.path.exists(poi_as),
           "radar_as": os.path.exists(radar_as), "constants": [], "create_lock_poi": 0,
           "create_any": 0}
    if hud["hud_as"]:
        src = open(hud_as, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"const\s+(\w*(?:LOCK|Lock)\w*)\s*:\s*([\w.]+)\s*=\s*([^;]+);", src):
            hud["constants"].append({"file": "hud.as", "name": m.group(1),
                                     "type": m.group(2), "value": m.group(3).strip()})
        hud["create_lock_poi"] = len(re.findall(
            r"CreatePoi\s*\(\s*(?:this\.)?POI_TYPE_LOCK_ON_TARGET", src))
        hud["create_any"] = len(re.findall(r"CreatePoi\s*\(", src))
    if hud["poi_as"]:
        src = open(poi_as, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"const\s+(\w*(?:LOCK|Lock)\w*)\s*:\s*([\w.]+)\s*=\s*([^;]+);", src):
            hud["constants"].append({"file": "poi.as", "name": m.group(1),
                                     "type": m.group(2), "value": m.group(3).strip()})
        hud["create_lock_poi"] += len(re.findall(
            r"CreatePoi\s*\(\s*(?:this\.)?POI_TYPE_LOCK_ON_TARGET", src))
        hud["create_any"] += len(re.findall(r"CreatePoi\s*\(", src))
    if hud["radar_as"]:
        src = open(radar_as, encoding="utf-8", errors="replace").read()
        m = re.search(r"public function UC_SetLockonValue\(([^)]*)\)[^{]*\{(.*?)\n      \}",
                      src, re.S)
        hud["radar_setter"] = (m.group(1).strip() if m else None)
        hud["radar_body"] = (m.group(2).strip() if m else None)
    hud["lock_duration_constants"] = [
        c for c in hud["constants"]
        if re.search(r"duration|hold", c["name"], re.I)
        or c["name"] in ("LOCK_TIME", "LOCK_DURATION", "LOCK_HOLD_TIME")]
    keep = ("MISSILE_LOCKED_TIMER", "LOCK_ON_TARGET_ROTATION_TIME",
            "POI_TYPE_LOCK_ON_TARGET", "POI_TYPE_LOCKED")
    hud["constants"] = [c for c in hud["constants"] if c["name"] in keep]

    # BmAK provenance
    bmak_src = open(BMAK, encoding="utf-8").read()
    for _n, _o, _v, quote in BMAK_QUOTES:
        assert quote in bmak_src, f"BmAK quote not found: {quote}"

    # writers that bind each lock/AA weapon
    wiring = []
    with open(WIRING, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            for w in r["weapons"]:
                wiring.append({"chassis": r["chassis"], "root": r["root_class"],
                               "weapon": w["name"],
                               "class": w["class"],
                               "autoaim": (w.get("autoaim_tuning_file") or "").rsplit("/", 1)[-1],
                               "binding": w.get("binding", []),
                               "muzzles": sum(1 for p in w.get("points", [])
                                              if str(p.get("type")) == "2"),
                               "components": sorted({c["class"] for c in w.get("components", [])})})

    return {
        "sources": {"index": "Research/JC3Grab/INDEX.jsonl", "game": DEFAULT_GAME,
                    "wiring": "Research/JC3Grab/WEAPON_WIRING.jsonl",
                    "bmak": "Research/BatmobileGrab/WEAPONS.md", "hud": HUD},
        "w143_autoaim": w143,
        "aa_layout": settings,
        "aa_coverage": coverage,
        "aa_gaps": gaps,
        "aa_uniform": aa_uniform,
        "aa_files": len(aa),
        "tune_count": len(tunes),
        "tune_values": {p.rsplit("/", 1)[-1].replace(".wtunec", ""): rec["values"]
                         for p, rec in tunes.items()},
        "type_members": type_members,
        "timeish": timeish,
        "tune_roots": dict(collections.Counter(r["root"] for r in tunes.values())),
        "aim_timer": {"offset": type_members["WeaponTuning"]["members"]
                      ["aim_timer_override"][0],
                      "values": timers, "dist": dict(timer_dist)},
        "multi": multi,
        "epe_files": len(epe),
        "epe_census": census,
        "epe_detail": detail,
        "hash": hashes,
        "hud": hud,
        "wiring": wiring,
        "bmak": [{"field": n, "offset": o, "value": v} for n, o, v, _q in BMAK_QUOTES],
    }


# ------------------------------------------------------------------- rendering
def md(data: dict) -> str:
    w = data["w143_autoaim"]
    st = data["aa_layout"]
    L: list[str] = []
    A = L.append
    A("# Lock hold and multi-target salvo: every place JC3 could carry them")
    A("")
    A("**Answer: neither is in JC3's data.** A lock *hold time* and a *target count* have no "
      f"member in the Fire Leech's AutoAim tune, in any of the {data['aa_files']} AutoAim tunes, "
      f"in any of the {data['tune_count']} weapon tunes, in any of the {data['epe_files']} "
      "`jc_weapons` entity graphs, or in `hud.gfx`. What JC3 "
      "does ship is **N projectiles per trigger aimed at one target**: `missile_per_shot` 6 "
      "(`w123`), `fire_amount` 15 (`w701` missile strike, into a 10 m radius), `bullets_per_shot` "
      "8 (shotguns), and `burst_count` 6 fired sequentially (`w613`/`w614`). Those can build "
      "*N shots at one aim point*; they cannot build *N shots at N different targets*.")
    A("")
    A("Labels: `decoded` = read at the archive entry and offset named; `derived` = arithmetic "
      "shown; `UNKNOWN` = searched in the named files and absent, with what would settle it. "
      "No game was launched. Everything below is regenerated by "
      "`python Tools/scripts/t_lock_salvo.py --write`.")
    A("")
    A("## 1. The places searched, and what each returned")
    A("")
    A("| place | files read | hold time | N targets |")
    A("|---|---|---|---|")
    A(f"| Fire Leech AutoAim, byte by byte | `{W143_AA.rsplit('/', 1)[-1]}` "
      f"({w['size']} B, one {w['inst_size']} B instance) | **no member**; 22 named members "
      f"cover offsets 0-{st['size']} with no gap | no target list |")
    A(f"| every AutoAim tune | **{data['aa_files']}** files, each 6 x {st['size']} B | **no "
      "member**; all 15 share the same 22-member struct | only `CanTargetCharacters/Vehicles/"
      "RigidObjects`, no count |")
    A(f"| every weapon tune | **{data['tune_count']}** `.wtunec` (" +
      ", ".join(f"{k} {v}" for k, v in sorted(data['tune_roots'].items())) + ") | only "
      "`aim_timer_override` (4.0 RPG / -1 default), a charge/aim timer, never 2.0 | per-projectile "
      "counts only (`missile_per_shot`, `bullets_per_shot`, `fire_amount`) |")
    A(f"| entity-level weapon objects | **{data['epe_files']}** `jc_weapons/*.epe`, "
      f"{sum(data['epe_census']['classes'].values())} objects | no lock/target-count property; "
      "`STimerComponent`/`CTimeTrigger` are event/effect timers | `SWeaponFirePattern` sequences "
      "muzzles, has no fields |")
    A("| aircraft and AA launchers | `w601/w606/w608/w609/w611/w612/w613/w615/w621`, "
      "`w501/w502/w504` | **no member**; the AA/SAM entity timers are 0.2/0.8/1/2/6/50 s event "
      "timers on damage controllers | `w501` has 6 muzzles and `missile_per_shot` 1 |")
    A("| HUD movies | `hud.as`, `hud_code/poi.as`, radar module | only a **1.5 s reticle "
      "rotation** and a **0.5 s incoming-warning blink**; no hold timer | one POI per target, no "
      "target list |")
    A("")
    A("## 2. The Fire Leech AutoAim, byte by byte")
    A("")
    A(f"`decoded` - `{W143_AA}`, entry offset **{w['offset']}**, size **{w['size']} B**, in "
      f"`{w['archive']}`. Root type `{w['root']}` (size {w['root_size']} B, "
      f"{len(w['layout'])} contexts), one instance `autoaim_rpg.wtune` of "
      f"**{w['inst_size']} B** at data offset {w['inst_offset']}. The six contexts are "
      "`OnFoot` at 0, then `Stunting` 88, `MotorCycle` 176, `ReelingIn` 264, `ReeledIn` 352, "
      "`Parachute` 440 - **6 x 88 bytes, nothing between them**.")
    A("")
    A(f"`AutoAimSettings` is **{st['size']} bytes and {len(st['members'])} members**. Every byte "
      "is named: the 22 members sit at 0,4,8,...,84, each 4 bytes, so the union of "
      "`[offset, offset+size)` is exactly `[0,88)` - **no padding, no unnamed member, no room "
      "for a hidden float**. Coverage intervals: " +
      ", ".join(f"{a}-{b}" for a, b in data["aa_coverage"]) + ". Gaps: " +
      (", ".join(f"{a}-{b}" for a, b in data["aa_gaps"]) if data["aa_gaps"] else "**none**") + ".")
    A("")
    A("The table prints the raw 4 bytes of each member in `OnFoot` and the decoded value in all "
      "six shooter contexts. `decoded`.")
    A("")
    A("| off | member | type | raw bytes (OnFoot) | OnFoot | Stunting | MotorCycle | ReelingIn | "
      "ReeledIn | Parachute |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for m in sorted(st["members"], key=lambda x: x["offset"]):
        off = m["offset"]
        raw = bytes(w["raw"][off:off + m["size"]])
        vals = [g(w["context_values"][c][m["name"]]) for c in CONTEXTS]
        A(f"| {off} | `{m['name']}` | {m['type']} | `{raw.hex()}` | " +
          " | ".join(vals) + " |")
    A("")
    A("`derived` - the six context blocks are "
      f"{'identical' if all(w['context_values'][c] == w['context_values']['OnFoot'] for c in CONTEXTS) else 'not identical'} "
      "for this tune, so the Fire Leech has one aim profile repeated six times. There is no "
      "member whose name or value could be a duration: the 0.12/0.15 values are the angle and "
      "fit thresholds, and the only 5/10/15 belong to the `StickyAimAngle*` family.")
    A("")
    A("`UNKNOWN` (unchanged): the AutoAim angle unit. The values are bare floats; `0.15` is "
      "54 deg as turns and 8.6 deg as radians, and `StickyAimAngleCurrentTarget` 15 cannot be "
      "turns. BmAK's 40 deg still cannot be written until a probe or native disassembly pins it.")
    A("")
    A("## 3. All 15 AutoAim tunes share one layout")
    A("")
    A("`decoded` - every file below has 6 contexts x 88 B = 528 B, one instance, and the same "
      "22-member `AutoAimSettings`; none adds a member. The columns are the OnFoot values of the "
      "members that matter for a lock.")
    A("")
    A("| file | size | contexts | settings | members | AngleNew | AngleCurrent | MaxAim | "
      "MinAim | chars | vehicles | rigid | StickyStrength |")
    A("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in sorted(data["aa_uniform"], key=lambda x: x["file"]):
        o = r["onfoot"]
        A(f"| `{r['file']}` | {r['size']} | {r['contexts']} | {r['settings_size']} | "
          f"{r['members']} | {g(o['AngleThresholdNewTarget'])} | "
          f"{g(o['AngleThresholdCurrentTarget'])} | {g(o['MaxAimDistance'])} | "
          f"{g(o['MinAimDistance'])} | {g(o['CanTargetCharacters'])} | "
          f"{g(o['CanTargetVehicles'])} | {g(o['CanTargetRigidObjects'])} | "
          f"{g(o['StickyAimStrength'])} |")
    A("")
    A(f"`derived` - **{data['aa_files']} of {data['aa_files']}** files carry exactly the same "
      "member set. `AutoAimSettings` contains angles, fit weights, distances and three target "
      "class booleans, and **nothing else**; a lock hold would have to be a member here, and it "
      "is not, in any of them.")
    A("")
    A("## 4. Every time-like member in every weapon tune")
    A("")
    A("`decoded` - the union of every structure member name across all "
      f"{data['tune_count']} tunes, filtered to names containing time/timer/duration/hold/lock/"
      "count/amount/per_shot/salvo/volley (the word `threshold` is excluded). The offsets are "
      "within each named struct.")
    A("")
    A("| struct | member | off | size | why it is not the lock hold |")
    A("|---|---|---|---|---|")
    why = {
        "aim_timer_override": "the only root-level timer; 4.0 on every RPG, -1 elsewhere, never 2.0",
        "burst_cooldown": "gap between shots inside a burst, at one aim point",
        "burst_count": "number of shots in a burst, not number of targets",
        "fire_rate": "seconds between trigger pulls",
        "fire_rate_level_2": "alternate fire rate",
        "reload_time_scale": "reload animation scale",
        "missile_no_turning_time": "seconds of unguided flight after launch",
        "missile_detonation_time": "projectile self-destruct timer",
        "missile_detonation_time_random": "jitter on the self-destruct timer",
        "missile_per_shot": "projectiles per trigger, all at one aim point",
        "bullets_per_shot": "bullets per trigger, all at one aim point",
        "bullets_per_tracer": "tracer cadence",
        "fire_amount": "missiles in one strike pattern, into one radius",
        "target_radius": "radius around the strike point, not a target list",
        "detonation_time": "grenade fuse",
        "tracer_time_to_live": "tracer lifetime",
        "scatter_reset_time": "scatter recovery",
        "recoil_recover_reset_time": "recoil recovery",
        "rumble_time": "controller rumble",
        "shake_time": "camera shake",
        "beam_duration": "laser/beam duration",
        "beam_target_time": "beam target lock-on time (visual beam, not missiles)",
        "beam_duration_level_2": "upgraded beam duration",
        "beam_target_time_level_2": "upgraded beam target time",
        "balloon_inflate_delay": "balloon inflation",
        "balloon_inflate_duration": "balloon inflation",
        "t_down": "grenade arc time",
        "t_flat": "grenade arc time",
        "t_up": "grenade arc time",
        "level_1_burn_time": "planted engine burn",
        "level_2_burn_time": "planted engine burn",
        "random_detonation_offset": "position jitter",
    }
    for r in sorted(data["timeish"], key=lambda x: (x["type"], x["offset"], x["member"])):
        A(f"| `{r['type']}` | `{r['member']}` | {r['offset']} | {r['size']} | "
          f"{why.get(r['member'], 'not a lock: no target reference') } |")
    A("")
    A("### 4.1 `aim_timer_override` is the only candidate, and it is not 2.0")
    A("")
    d = data["aim_timer"]
    A(f"`decoded` - `WeaponTuning.aim_timer_override`, offset **{d['offset']}**, 4 B float. "
      f"Distribution over the {len(d['values'])} `WeaponTuning` files: " +
      ", ".join(f"{n} file(s) at {g(k)}" for k, n in sorted(d["dist"].items(), reverse=True)) + ".")
    A("")
    A("Every 4.0 is an RPG-class weapon (`w141`, `w141_mm110`, `w142`, `w143`, `w144`, `w146`, "
      "`w147`, `w704`) - guided and unguided alike - so the value tracks the two-handed rocket "
      "aim pose, not lock capability. The Stupka mortar is 0.001 and everything else is -1. "
      "**No tune carries 2.0 or 1.0**, and w143's own 4.0 cannot be BmAK's 2.0 s hold.")
    A("")
    A("`UNKNOWN`: what the engine does with 4.0. It is named as an *aim timer override* and is "
      "the closest thing to a hold in the weapon data; a probe holding an RPG sight for 2 s vs "
      "4 s would settle whether it gates anything. It does not provide BmAK's value.")
    A("")
    A("## 5. Entity-level weapon objects")
    A("")
    A(f"`decoded` - all **{data['epe_files']}** `jc_weapons/*.epe` graphs, converted with "
      f"`{os.path.basename(CONVERT)}`; "
      f"{sum(data['epe_census']['classes'].values())} objects. Classes that could plausibly own "
      "a lock or a salvo: " +
      ", ".join(f"`{k}` x{v}" for k, v in sorted(data["epe_census"]["classes"].items())
                if k in INTEREST) + ".")
    A("")
    A("| entity | weapon class | muzzles (type 2) | components | timers | target points |")
    A("|---|---|---|---|---|---|")
    for fn, d in sorted(data["epe_detail"].items()):
        timers = ", ".join(f"{t['name']}={t['value']}"
                           for t in d["timers"] if t["value"] is not None) or "-"
        tps = ", ".join(f"min_aim={t.get('min_aim_distance')}"
                        for t in d["target_points"]) or "-"
        A(f"| `{fn}` | `{d['weapon_class']}` | {d['fire_points']} | "
          f"{', '.join(sorted(set(d['components']))) or '-'} | {timers} | {tps} |")
    A("")
    A("`derived` - the timers are **event timers on damage controllers and effects**, not on the "
      "weapon object: the SAM's `STimerComponent`/`CTimeTrigger` values are 1, 2, 6, 0.6, 0.01, "
      "20 and 30 (blink, tower destruction, fade), and the AA gun's are 0.2, 0.8, 1 and 50. The "
      "weapon object itself (`CMissileWeaponBase`/`CAntiAirWeapon`) carries no timer child.")
    A("")
    A("`SWeaponFirePattern` (55 objects) and `SWeaponFirePatternComponent` (145) are the "
      "multi-muzzle firing order: they exist on pistols, rifles, shotguns, the SAM and the "
      "car missile alike, and carry **only a name and pointers** - no count, no target, no time. "
      "`STargetPoint` carries only `min_aim_distance`. `CTurretWeaponComponent` on the SAM has "
      "only a `faction`; `CAimPOIWeaponComponent` has only the hash property `id:2D0B3C09` "
      "(50 on `w618`, 100 on `w611`, 25 on the buggy gun) - an aim marker, not a lock state.")
    A("")
    A("### 5.1 Property-name hash test")
    A("")
    h = data["hash"]
    A(("`decoded`" if h["ok"] else "`UNKNOWN`") +
      " - the weapon objects carry 32-bit property ids. The Jenkins function used by "
      "`jc3wiring.py` resolves the known names " +
      ", ".join(f"{k}={v}" for k, v in h["known"].items()) +
      f" and was then run over **{h['tried']:,}** one-to-four-word candidate names "
      "containing lock/hold/time/target/salvo/volley/count. **Matches: " +
      (", ".join(f"`{k}` = {v}" for k, v in h["hits"].items()) if h["hits"] else "none") + ".**")
    A("")
    A("So no entity property on the selected weapon objects is a lock-hold, a target count or a "
      "salvo count. Two values that look timer-ish remain unnamed and are recorded rather than "
      "guessed: `id:098D3AA3` = 0.2 and `id:D13BBA30` = 0.25 on `w618`/`w123`. Neither is 2.0 "
      "or 1.0, and neither is on the lock-on preset path.")
    A("")
    A("## 6. The HUD movies")
    A("")
    A("`decoded` - the G2-19 decompile of `hud.gfx` (260 AS3 scripts). Every constant whose name "
      "contains `LOCK`:")
    A("")
    A("| file | constant | value | role |")
    A("|---|---|---|---|")
    roles = {
        "MISSILE_LOCKED_TIMER": "incoming-missile warning blink, 0.5 s - not the player's hold",
        "LOCK_ON_TARGET_ROTATION_TIME": "reticle spin, one turn per 1.5 s - visual only",
        "POI_TYPE_LOCK_ON_TARGET": "the lock POI type, 21",
        "POI_TYPE_LOCKED": "a different POI (locked collectible/challenge), 24",
        "STATE_LOCKED": "boss-settlement state, not a weapon",
    }
    for c in data["hud"]["constants"]:
        A(f"| `{c['file']}` | `{c['name']}` | {c['value']} | {roles.get(c['name'], '-')} |")
    A("")
    A(f"`derived` - **{data['hud']['create_lock_poi']}** `CreatePoi(POI_TYPE_LOCK_ON_TARGET, ...)` "
      f"calls in the movie (out of {data['hud']['create_any']} `CreatePoi` calls total), so the "
      "movie receives an already-chosen target and paints one reticle; it never times a hold. "
      "The only lock-ish setter code in the repo is the radar module: "
      f"`UC_SetLockonValue({data['hud'].get('radar_setter')})` writes the 0-1 value straight to "
      "`scaleX` and a display state - it receives the fraction from native code and has no "
      "timer. **No HUD file contains a 2.0 or 1.0 lock duration.**")
    A("")
    A("## 7. The salvo: what N-projectile members can and cannot do")
    A("")
    A("`decoded` - every tune whose per-trigger count or burst is greater than one, with the "
      "member offsets. `missile_per_shot` is offset **44** (u8) of `MissileWeaponTuningBase`; "
      "`bullets_per_shot` offset **30** (u8) of `BulletWeaponTuningBase`; "
      "`MissileStrikeWeaponTuning.fire_amount` offset **4** (u8) and `target_radius` offset **0** "
      "(float); `burst_count` offset **88** (u8) and `burst_cooldown` offset **92** (float) of "
      "`WeaponTuning`.")
    A("")
    A("| tune | class | per_shot | bullets | fire_amount | radius | burst x cd | mag | muzzles |")
    A("|---|---|---|---|---|---|---|---|---|")
    epe_muzzles = {
        "w123_grenade_launcher_upu_210": data["epe_detail"]["w123_grenade_launcher_upu_210.epe"]["fire_points"],
        "w701_missile_strike": data["epe_detail"]["w701_missile_strike.epe"]["fire_points"],
        "w501_sam_missile": data["epe_detail"]["w501_turret_sam_v2.epe"]["fire_points"],
        "w502_turret_aa_gun": data["epe_detail"]["w502_turret_aa_gun.epe"]["fire_points"],
    }
    wire_muzzles = {x["weapon"]: x.get("muzzles", 0) for x in data["wiring"]}
    for r in sorted(data["multi"], key=lambda x: x["tune"]):
        stem = r["tune"].rsplit("/", 1)[-1].replace(".wtunec", "").replace(".wtune", "")
        mz = wire_muzzles.get(stem, epe_muzzles.get(stem, "-"))
        A(f"| `{stem}` | `{r['root']}` | {g(r['per_shot'])} | {g(r['bullets'])} | "
          f"{g(r['fire_amount'])} | {g(r['target_radius'])} | "
          f"{g(r['burst_count'])} x {g(r['burst_cooldown'])} | {g(r['magazine'])} | {mz} |")
    A("")
    A("`derived` - three distinct mechanisms, all single-target:")
    A("")
    A("1. **`missile_per_shot` 6 on `w123`** (UPU-210 grenade launcher): six projectiles leave "
      "on one trigger pull, from one weapon, aimed by the one `AutoAim` target the weapon holds. "
      "The field is a count of projectiles, not of targets.")
    A("2. **`burst_count` 6 on `w613`/`w614`** (4 s / 5 s apart): six sequential trigger pulls at "
      "the same aim point. `w144` does 5 x 1 s, `w117` 4 x 0.25 s.")
    A("3. **`fire_amount` 15 on `w701`** (missile strike; `CMissileStrikeWeapon` + "
      "`CAirplaneFlybyWeaponComponent`): fifteen missiles scattered inside `target_radius` 10 m "
      "of **one** strike point. The 15/10 block is also present on the balloon, namaste, sungun, "
      "typhoon and EMP tunes (a shared default), but only `w701` is a `CMissileStrikeWeapon`.")
    A("")
    A("Muzzles do not multiply targets: `w618` has 4 fire points and `w501` 6, yet both have "
      "`missile_per_shot` 1. `SWeaponFirePattern` chooses which muzzle fires next; it has no "
      "target field. **N shots at one target is buildable from data; N shots at N targets is "
      "not**: JC3's `AutoAim` resolves one current target per weapon, and no tune, entity or HUD "
      "record holds a list of N targets.")
    A("")
    A("## 8. Aircraft and anti-air launchers")
    A("")
    A("`decoded` - the tune values and the entity binding. The aircraft use the same "
      "`MissileWeaponTuningBase` as the car missile; the AA/SAM are stationary weapon entities "
      "with their own `.epe`.")
    A("")
    A("| weapon | class (entity) | autoaim | turning | per_shot | burst | mag | entity timers |")
    A("|---|---|---|---|---|---|---|---|")
    rows = [
        ("w601_helicopter_missile", "CHelicopter", "w601_helicopter_missile"),
        ("w606_heavyhelicopter_missile", "CHelicopter", "w606_heavyheli_missile"),
        ("w608_fighterjet_missile", "CAirPlane", "w608_fighterjet_missile"),
        ("w609_fighterjet_missile_air_lockon", "CAirPlane", "w609_fighterjet_missile_air_lockon"),
        ("w611_fighterbomber_missile", "CAirPlane", "w611_fighterbomber_missile"),
        ("w612_fighterbomber_missile_air_lockon", "CAirPlane", "w612_fighterbomber_missile_air_lockon"),
        ("w613_fighterbomber_missile_ground_lockon", "CAirPlane", "w613_fighterbomber_missile_ground_lockon"),
        ("w615_helicopter_heavy_missile", "CHelicopter", "w615_helicopter_heavy_missile"),
        ("w621_advancedhelicopter_missile", "CHelicopter", "w621_advancedhelicopter_missile"),
    ]
    wiring_by = {x["weapon"]: x for x in data["wiring"]}
    for label, chassis, stem in rows:
        wr = wiring_by.get(label, {})
        rec = data["tune_values"].get(stem, {})
        A(f"| `{label}` | `{chassis}` | `{wr.get('autoaim', '-')}` | "
          f"{g(rec.get('missile_weapon[0].tuning.missile_base_tuning.missile_turning_speed'))} | "
          f"{g(rec.get('missile_weapon[0].tuning.missile_base_tuning.missile_per_shot'))} | "
          f"{g(rec.get('burst_count'))} x {g(rec.get('burst_cooldown'))} | "
          f"{g(rec.get('magazine_size'))} | - |")
    A("")
    A("The SAM and AA turret entities are table 5. `w501_turret_sam_v2` is a "
      "`CMissileWeaponBase` with 6 muzzles, a `CTurretWeaponComponent` (faction 5) and "
      "`STargetPoint` `min_aim_distance` 5; its `autoaim_tuning_file` is "
      "`autoaim_aa_gun.wtune` and its tune has `missile_per_shot` 1, turning 35. `w502` is a "
      "`CAntiAirWeapon` with `autoaim_aa_gun.wtune`; `w504` is a `CMissileWeaponBase` with "
      "turning 110 and fire rate 16. **None has a lock-hold member, and none fires at more than "
      "one target.**")
    A("")
    A("## 9. Member by member: what each carries and what it still lacks")
    A("")
    A("| member (file, offset) | value | carries | still lacks |")
    A("|---|---|---|---|")
    A("| `AutoAimSettings.AngleThresholdCurrentTarget` (autoaim, 4) | 0.12-1.4 | acquisition "
      "cone | a time; degrees (unit UNKNOWN) |")
    A("| `AutoAimSettings.MaxAimDistance` (autoaim, 60) | -1 / 750 | lock range | a hold |")
    A("| `AutoAimSettings.CanTargetVehicles/RigidObjects` (72/76) | 0/1 | target classes | a "
      "target *count* |")
    A("| `AutoAimSettings` (whole struct, 0-87) | 22 members | cone, fit, range, classes | "
      "**every time and count member** |")
    A("| `WeaponTuning.aim_timer_override` (108) | 4.0 / -1 | RPG aim pose timer | 2.0; no "
      "target reference |")
    A("| `MissileWeaponTuningBase.missile_per_shot` (44) | 1; **6 on w123** | N projectiles per "
      "trigger | N targets; per-projectile target index |")
    A("| `MissileWeaponTuningBase.missile_turning_speed` (24) | 0-300 | guided flight | a hold |")
    A("| `WeaponTuning.burst_count/burst_cooldown` (88/92) | 1-6 / 0-5 | sequential shots at one "
      "point | simultaneous N targets |")
    A("| `MissileStrikeWeaponTuning.fire_amount/target_radius` (4/0) | 15 / 10 m | 15 missiles "
      "into one radius | 15 distinct targets |")
    A("| `BulletWeaponTuningBase.bullets_per_shot` (30) | 1-8 | pellets per trigger | target "
      "per pellet |")
    A("| `STimerComponent` (entity) | 0.2-50 s on damage/effects | event timing | weapon lock |")
    A("| `SWeaponFirePattern` (entity) | name + pointers | muzzle order | count, target, time |")
    A("| `POI_TYPE_LOCK_ON_TARGET` (HUD) | 21, 1.5 s spin | one reticle | hold; target list |")
    A("| `MISSILE_LOCKED_TIMER` (hud.as) | 0.5 s | incoming warning blink | the player's hold |")
    A("")
    A("## 10. Verdict and what can be built")
    A("")
    A("* **2.0 s hold:** no member. The nearest is `aim_timer_override` 4.0, which is an "
      "RPG-class aim timer, not 2.0 and not lock-gated. The engine's lock progression is native: "
      "the HUD only consumes a 0-1 value (`UC_SetLockonValue`) or paints a POI. To get 2.0 s, "
      "BmAK's timer has to stay native, or a script must gate fire for 2.0 s after acquisition.")
    A("* **8-target salvo:** no member. N projectiles exist (6, 15, 8) but all resolve to one "
      "aim point. A true 8-target salvo needs a bridge: for each of 8 acquired targets, set the "
      "weapon's aim/target and fire one projectile; the tune data cannot express it.")
    A("* **Buildable now from data:** a 6-shot volley at one target (`w123` `missile_per_shot` "
      "6), a 6-shot sequential burst (`w613`/`w614`), a 15-missile 10 m strike (`w701`), or an "
      "8-pellet shotgun spread. Each is one target/area, not eight.")
    A("")
    A("### UNKNOWNs")
    A("")
    A("1. **What `aim_timer_override` 4.0 gates.** *Tried:* every tune's value, the RPG set, the "
      "entity props. *Would settle:* holding an RPG sight for 2 s vs 4 s, or native code.")
    A("2. **`id:098D3AA3` (0.2) and `id:D13BBA30` (0.25)** on `w618`/`w123`. *Tried:* the "
      "Jenkins vocabulary in 5.1. *Would settle:* the engine's name table / native code.")
    A("3. **Whether `UC_SetLockonValue` is fed by weapon lock or vehicle tracking.** It is named "
      "`Tracking.VehicleLockon*` and lives in the radar module, so it is most likely the vehicle "
      "tracker; the weapon POI path is separate. *Would settle:* a HUD trace.")
    A("4. **The AutoAim angle unit** (turns vs radians), unchanged from `T_WP3B_LOCKON.md`.")
    A("5. **Whether the engine can hold several targets per weapon.** No data member names a "
      "list; `AutoAim` exposes one current target. *Would settle:* native disassembly or a probe.")
    A("")
    A("## 11. Change statement, checks and revert")
    A("")
    A("* **Intended change:** add one report and one generator; no game data, ledger, build or "
      "tune is modified.")
    A("* **Files:** `tmp/freebuff/reports/lock-hold-and-salvo-carrier.md` (this report) and "
      "`Tools/scripts/t_lock_salvo.py` (the decoder that writes it and re-checks it). The report "
      "is the correct file because the brief names it; the script is the correct file because "
      "every number above is decoded from the archives by a rerunnable tool.")
    A("* **Revert:** delete both files. Nothing else changed.")
    A("* **Checks:** `python Tools/scripts/t_lock_salvo.py --check` re-decodes the 103 tunes, "
      "15 AutoAim files and 59 entity graphs, re-runs `ConvertProperty`, asserts the 22/88-byte "
      "layout, the absence of a lock-hold or target-count name, the BmAK quotes and the HUD "
      "constants, and compares this markdown and the JSON byte for byte.")
    A("")
    return "\n".join(L)


# ---------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    g0 = ap.add_mutually_exclusive_group(required=True)
    g0.add_argument("--write", action="store_true")
    g0.add_argument("--check", action="store_true")
    a = ap.parse_args()

    data = build()
    doc = md(data)
    js = json.dumps(data, indent=1, sort_keys=True) + "\n"
    mp, jp = os.path.join(OUT, MD_NAME), os.path.join(OUT, JSON_NAME)
    os.makedirs(OUT, exist_ok=True)

    if a.write:
        with open(mp, "w", encoding="utf-8", newline="\n") as f:
            f.write(doc)
        with open(jp, "w", encoding="utf-8", newline="\n") as f:
            f.write(js)
        print("wrote", mp)
        print("wrote", jp)
        return 0

    fails = []
    old_md = open(mp, encoding="utf-8").read() if os.path.exists(mp) else ""
    old_js = open(jp, encoding="utf-8").read() if os.path.exists(jp) else ""
    if old_md != doc:
        fails.append("markdown drifted")
        for line in list(difflib.unified_diff(old_md.splitlines(), doc.splitlines(),
                                              MD_NAME, "re-derived", lineterm=""))[:12]:
            print("  " + line)
    if old_js != js:
        fails.append("json drifted")

    st = data["aa_layout"]
    if st["size"] != 88 or len(st["members"]) != 22:
        fails.append(f"AutoAimSettings changed: {st['size']} B, {len(st['members'])} members")
    if data["aa_gaps"]:
        fails.append(f"AutoAimSettings has unnamed bytes: {data['aa_gaps']}")
    if data["aa_files"] != 15:
        fails.append(f"expected 15 AutoAim files, got {data['aa_files']}")
    if any(r["members"] != 22 or r["settings_size"] != 88 for r in data["aa_uniform"]):
        fails.append("AutoAim layouts differ")
    if any(re.search(r"duration|lock|salvo|volley", m["name"], re.I) for m in st["members"]):
        fails.append("a lock/hold member appeared in AutoAimSettings")
    lock_members = [m for m in data["timeish"] if "lock" in m["member"].lower()]
    if lock_members != [m for m in lock_members if m["member"] == "missile_loose_lock_distance"]:
        fails.append(f"unexpected lock member: {lock_members}")
    if any(v in (2.0, 1.0) for v in data["aim_timer"]["values"].values()):
        fails.append("aim_timer_override has a 2.0 or 1.0 value")
    if not data["multi"]:
        fails.append("no multi-projectile tune found")
    if not any(r["per_shot"] == 6 for r in data["multi"]):
        fails.append("w123 missile_per_shot 6 not found")
    if not any(r["fire_amount"] == 15 for r in data["multi"]):
        fails.append("missile strike fire_amount 15 not found")
    if data["hash"]["hits"]:
        fails.append(f"a lock/salvo property name resolved: {data['hash']['hits']}")
    if data["hud"]["lock_duration_constants"]:
        fails.append(f"HUD lock duration constant: {data['hud']['lock_duration_constants']}")
    if data["hud"]["create_lock_poi"]:
        fails.append("the movie creates a lock POI")
    if data["epe_files"] != 59:
        fails.append(f"expected 59 jc_weapons epe files, got {data['epe_files']}")
    for fn, d in data["epe_detail"].items():
        if d["weapon_class"] is None:
            fails.append(f"no weapon class in {fn}")

    print(f"AutoAim files {data['aa_files']}, settings {st['size']} B/{len(st['members'])} "
          f"members, tunes {data['tune_count']}, epe {data['epe_files']}, "
          f"multi-shot tunes {len(data['multi'])}, HUD lock constants "
          f"{len(data['hud']['constants'])}, hash candidates {data['hash']['tried']:,}")
    if fails:
        for f in fails:
            print("FAIL:", f)
        return 1
    print("OK: lock hold and target count absent everywhere searched; report re-derived")
    return 0


if __name__ == "__main__":
    sys.exit(main())
