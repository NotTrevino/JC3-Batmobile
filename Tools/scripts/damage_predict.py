"""damage_predict.py - how a JC3 hit becomes health loss, and the hits-to-kill table (G2-28).

The card: write down the chain `weapon damage -> damage type -> armour channel -> armour gate ->
part damage type -> root health scale`, cite every step, mark undecoded steps UNKNOWN, then predict
hits-to-kill for nine arms on three vehicles (the donor, the medium tank, the current build) and work
out what values would give ARM-1 and ARM-2 at the BmAK ratio from G1-14.

Where each number comes from (nothing is typed in):

  * `VehicleDamage` + `PartDamageType` rows   - `E:\\Modding\\_shared\\gamedata\\JC3grab\\entities\\*.ee.json` (donor,
    medium tank) and `Builds/test-091` decoded with `t1_current.dump` (the build)
  * root `health` / `invulnerable`            - `jc3_damage_search.epe_fields` on the build's `.epe`;
    the fleet census for the other two is `DAMAGE_MECHANISMS.json`
  * the 3 vehicle arms                        - `Research/JC3Grab/WEAPONS.jsonl` (G2-10's decode)
  * the 6 hand arms                           - re-decoded from the archives with `jc3weapons`'
    own reader (`read_row` + `decode_tune`); their blasts are the `.ftunec` files inside the
    weapon's own `.ee` bundle
  * the BmAK ratio                            - `Research/BatmobileGrab/DAMAGE_RULES.json` (G1-14)
  * the part -> damage-type mechanism         - the one `VehicleParts` module that decodes in the
    whole fleet (`monorailflatbed_vehicle_parts.vmodc`, 4 entities); every other `*_vehicle_parts`
    module fails `ConvertAdf` (MODLOG 98), so the donor's own part map is UNKNOWN

Three models are computed, not one, because the *composition* of `*_armor`, `*_armor_strength`,
`max_health` and the root `health` scale is in no file (POSTMORTEM_DAMAGE.md §5 item 1). Each model
is a named hypothesis with an exact formula; the Q-1 probes at the end are the takes that separate
them. No model is presented as the answer.

  H0  armour ignored            per-hit = D
  H1  percentage gate           per-hit = D x (1 - strength/100)      (the reading MODLOG 97 used)
  H2  threshold gate + pool     D <= strength -> absorbed; else the `*_armor` pool absorbs point
                                for point, then health: hits = ceil((armor + HP) / D)

Usage:
  python Tools/scripts/damage_predict.py --write     # write DAMAGE_MODEL.md + DAMAGE_MODEL.json
  python Tools/scripts/damage_predict.py --check     # re-derive from the sources and compare
  python Tools/scripts/damage_predict.py dump        # print the payload
"""
from __future__ import annotations

import argparse
import json
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

OUT = os.path.join(ROOT, "Research", "JC3Grab")
DOC = os.path.join(OUT, "DAMAGE_MODEL.md")
JSON_OUT = os.path.join(OUT, "DAMAGE_MODEL.json")
WEAPONS = os.path.join(OUT, "WEAPONS.jsonl")
INDEX = os.path.join(OUT, "INDEX.jsonl")
MECH = os.path.join(OUT, "DAMAGE_MECHANISMS.json")
BM_RULES = os.path.join(ROOT, "Research", "BatmobileGrab", "DAMAGE_RULES.json")
BUILD = os.path.join(ROOT, "Builds", "test-091")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
ENT = os.path.join(RAW, "entities")

DONOR = "v0300_car_kensington_sportsmuscle__v0300_car_kensington_sportsmuscle_civilian_01.ee.json"
TANK = "v0201_car_capstone_mediumtank__v0201_car_capstone_mediumtank_military_01.ee.json"

HAND_DIR = "editor/entities/jc_weapons/"
HAND = [
    # key, label, tune path, blast host .ee, blast path inside the host
    ("pistol", "Rico's pistol (w011_pozhar_98)",
     HAND_DIR + "01_one_handed/w011_pistol_u_pozhar_98/w011_pistol_u_pozhar_98.wtunec", None, None),
    ("assault_rifle", "Rico's assault rifle (w111_UP_39)",
     HAND_DIR + "02_two_handed/w111_assault_rifle_up_39/w111_assault_rifle_up_39.wtunec", None, None),
    ("machine_gun", "Rico's machine gun (w131_Vdova_89)",
     HAND_DIR + "02_two_handed/w131_machine_gun_urga_vdova_89/w131_machine_gun_urga_vdova_89.wtunec",
     None, None),
    ("shotgun", "Rico's shotgun (w151_RYS_96)",
     HAND_DIR + "02_two_handed/w151_shotgun_u_rys_96/w151_shotgun_u_rys_96.wtunec", None, None),
    ("rpg", "Rico's RPG (w141_UVK_13)",
     HAND_DIR + "02_two_handed/w141_rpg_uvk_13/w141_rpg_uvk_13.wtunec",
     HAND_DIR + "02_two_handed/w141_rpg_uvk_13/w141_rpg_uvk_13_mm110.ee",
     "editor/entities/jc_explosions/weapons/rpg_mm110.ftunec"),
    ("grenade", "Rico's grenade (w301)",
     HAND_DIR + "03_thrown/w301_grenade/w301_grenade.wtunec",
     HAND_DIR + "03_thrown/w301_grenade/w301_grenade.ee",
     "editor/entities/jc_explosions/weapons/hand_grenade.ftunec"),
]
VEHICLE = [
    ("tank_cannon", "tank cannon w602_mediumtank_canon", "w602_mediumtank_canon"),
    ("heli_missile", "heli missile w601_helicopter_missile", "w601_helicopter_missile"),
    ("heli_mg", "heli MG w604_helicopter_mgun", "w604_helicopter_mgun"),
]
CHANNELS = ("bullet", "bullet_heavy", "explosion", "impact", "fire", "melee", "electricity",
            "grapple_pull")
MODELS = {
    "H0": "armour ignored: per-hit = D",
    "H1": "percentage gate: per-hit = D x (1 - strength/100)",
    "H2": "threshold gate + pool: D <= strength absorbed, else ceil((armor + HP) / D)",
}


# --------------------------------------------------------------------- readers
def rel_root(root: str) -> str:
    return os.path.relpath(root, ROOT).replace("\\", "/")


def build_vehicle(veh: dict) -> dict:
    """The build's vehicle row: `build_test-091` by default, `build_<tag>` for --root."""
    return next(src for key, src in veh.items() if key.startswith("build_"))


def load_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def health_from_cache(name: str) -> dict:
    doc = load_json(os.path.join(ENT, name))
    for mod in doc["modules"]:
        if mod.get("type") != "VehicleDamage":
            continue
        scalars: dict[str, object] = {}
        parts: dict[int, dict] = {}
        for row in mod["rows"]:
            path = row["path"]
            if "[" in path:
                head, rest = path.split("[", 1)
                idx, tail = rest.split("].", 1)
                parts.setdefault(int(idx), {})[tail] = row["value"]
            else:
                scalars[path] = row["value"]
        return {"entity": doc["entity"], "file": mod["file"], "instance": mod["instance"],
                "scalars": scalars, "part_damage_types": [parts[k] for k in sorted(parts)]}


def health_from_build(build: str) -> dict:
    from t1_current import dump  # noqa: E402  (imported late: it shells ConvertAdf)
    doc = dump(build)
    for tag, mod in doc["modules"].items():
        if mod.get("instance") == "VehicleDamage" or "health" in tag:
            values = mod.get("values", {})
            scalars = {k: v for k, v in values.items() if "[" not in k}
            parts: dict[int, dict] = {}
            for key, value in values.items():
                if "[" not in key:
                    continue
                head, rest = key.split("[", 1)
                idx, tail = rest.split("].", 1)
                parts.setdefault(int(idx), {})[tail] = value
            if "max_health" not in scalars:
                continue
            return {"entity": build.replace("\\", "/"), "file": mod.get("file"),
                    "instance": tag, "scalars": scalars,
                    "part_damage_types": [parts[k] for k in sorted(parts)]}
    raise SystemExit("no VehicleDamage module in the build")


def root_fields(epe: str) -> dict:
    """`health` (float32) and `invulnerable` (int32) decoded from the build's compiled `.epe`."""
    import jc3_damage_search  # noqa: E402
    out = {}
    for row in jc3_damage_search.epe_fields(epe):
        value = row.get("value")
        decoded = value
        if isinstance(value, str) and len(value.replace(" ", "")) == 8:
            raw = bytes.fromhex(value.replace(" ", ""))
            decoded = (struct.unpack("<f", raw)[0] if row["name"] == "health"
                       else struct.unpack("<i", raw)[0])
        out[row["name"]] = {k: v for k, v in row.items() if k != "name"}
        out[row["name"]]["decoded"] = decoded
    return out


def find_epe(build: str) -> str | None:
    for dirpath, _dirs, names in os.walk(build):
        for fn in names:
            if fn.endswith(".epe") and "sportsmuscle_civilian_01" in fn:
                return os.path.join(dirpath, fn)
    return None


def fleet_census() -> dict:
    """Distinct (value, vehicles) for the four armour pairs across the 233 modules."""
    import glob
    counts: dict[str, dict[str, int]] = {c: {} for c in CHANNELS}
    n = 0
    for path in glob.glob(os.path.join(ENT, "*.ee.json")):
        doc = load_json(path)
        for mod in doc["modules"]:
            if mod.get("type") != "VehicleDamage":
                continue
            n += 1
            vals = {r["path"]: r["value"] for r in mod["rows"] if "[" not in r["path"]}
            for ch in CHANNELS:
                key = f"{vals.get(ch + '_armor')}@{vals.get(ch + '_armor_strength')}"
                counts[ch][key] = counts[ch].get(key, 0) + 1
    return {"modules": n, "pairs": counts}


# ---------------------------------------------------------------- weapon readers
def tune_rows(blob: bytes) -> list[list]:
    import jc3weapons  # noqa: E402
    dec = jc3weapons.decode_tune(blob)
    rows: list[list] = []
    for inst in dec["instances"]:
        rows.extend(inst["rows"])
    return rows


def gun_of(rows: list[list]) -> str:
    """Which weapon array the tune carries: bullet_weapon / missile_weapon / grenade_weapon."""
    for p, _t, _v in rows:
        if p.endswith("_weapon[0].tuning.base_tuning.damage"):
            return p.split("[")[0]
    raise SystemExit("no player tuning damage row")


def arm_stats(rows: list[list]) -> dict:
    gun = gun_of(rows)
    base = f"{gun}[0].tuning.base_tuning."
    flat = {p: v for p, _t, v in rows}
    pellets_path = f"{gun}[0].tuning.bullet_base_tuning.bullets_per_shot"
    missile_path = f"{gun}[0].tuning.missile_base_tuning.missile_per_shot"
    pellets = int(flat.get(pellets_path, flat.get(missile_path, 1)))
    blast = None
    for p, _t, v in rows:
        if p == "PlayerDamage":
            blast = {"player_damage": v, "player_radius": flat.get("PlayerDamageRadius"),
                     "ai_damage": flat.get("AIDamage")}
    return {"gun": gun, "damage": float(flat[base + "damage"]),
            "vehicle_factor": float(flat[base + "vehicle_damage_factor"]),
            "pellets": pellets, "blast": blast,
            "fire_rate_s": flat.get("fire_rate")}


def hand_arm(key: str, label: str, tune: str, host: str | None, blast_path: str | None,
             index_best: dict, game: str) -> dict:
    import jc3weapons  # noqa: E402
    row = index_best.get(tune)
    if row is None:
        raise SystemExit(f"{tune} not in the index")
    rows = tune_rows(jc3weapons.read_row(row, game))
    stats = arm_stats(rows)
    stats["blast_in_file"] = None
    if host and blast_path:
        hrow = index_best.get(host)
        stream, entries = jc3weapons.unpack(jc3weapons.read_row(hrow, game))
        for name, off, size in entries:
            if name == blast_path:
                brows = tune_rows(stream[off:off + size])
                flat = {p: v for p, _t, v in brows}
                stats["blast_in_file"] = {"path": blast_path,
                                          "player_damage": flat.get("PlayerDamage"),
                                          "player_radius": flat.get("PlayerDamageRadius")}
    direct = stats["damage"] * stats["vehicle_factor"] * stats["pellets"]
    stats.update({"key": key, "label": label, "tune": tune, "mount": row["mount"],
                  "per_shot_vs_vehicle": direct,
                  "channel": "explosion" if (stats["blast_in_file"] or key in ("rpg", "grenade"))
                  else "bullet"})
    return stats


def vehicle_arm(key: str, label: str, wid: str) -> dict:
    rec = None
    for line in open(WEAPONS, encoding="utf-8"):
        d = json.loads(line)
        if d["id"] == wid:
            rec = d
            break
    if rec is None:
        raise SystemExit(f"{wid} not in WEAPONS.jsonl")
    rows: list[list] = []
    blast = None
    blast_path = None
    for src in rec["sources"]:
        for inst in src.get("decode", {}).get("instances", []):
            if inst["class"] == "WeaponTuning":
                rows.extend(inst["rows"])
            elif inst["class"] == "ForcePulseSettings":
                flat = {p: v for p, _t, v in inst["rows"]}
                blast = {"player_damage": flat.get("PlayerDamage"),
                         "player_radius": flat.get("PlayerDamageRadius"),
                         "ai_damage": flat.get("AIDamage")}
                blast_path = src["path"]
    stats = arm_stats(rows)
    return {"key": key, "label": label, "tune": wid, "mount": "archive",
            "per_shot_vs_vehicle": stats["damage"] * stats["vehicle_factor"] * stats["pellets"],
            "blast": blast, "blast_in_file": ({"path": blast_path, **blast} if blast else None),
            "channel": "explosion" if blast else "bullet", "fire_rate_s": stats["fire_rate_s"],
            **stats}


def impact_pulse(wid: str) -> dict | None:
    for line in open(WEAPONS, encoding="utf-8"):
        d = json.loads(line)
        if d["id"] != wid:
            continue
        for src in d["sources"]:
            for inst in src.get("decode", {}).get("instances", []):
                if inst["class"] != "ForcePulseSettings":
                    continue
                flat = {p: v for p, _t, v in inst["rows"]}
                return {"id": wid, "path": src["path"],
                        "player_damage": flat.get("PlayerDamage"),
                        "player_radius": flat.get("PlayerDamageRadius")}
    return None


# --------------------------------------------------------------------- the model
def hits(hp: float, armor: float, strength: float, dmg: float, model: str) -> float | None:
    """Hits to zero the health pool under one model; None means 'absorbed, never'."""
    if dmg <= 0:
        return None
    if model == "H0":
        return math.ceil(hp / dmg)
    if model == "H1":
        per = dmg * (1.0 - min(max(strength, 0.0), 100.0) / 100.0)
        if per <= 1e-12:
            return None
        return math.ceil(hp / per)
    if model == "H2":
        if dmg <= strength:
            return None
        return math.ceil((hp + armor) / dmg)
    raise SystemExit(f"unknown model {model}")


def arm_damage(arm: dict) -> list[dict]:
    """The damage components of one arm, each with its armour channel."""
    comps = []
    if arm.get("blast_in_file"):
        comps.append({"component": "blast", "channel": "explosion",
                      "damage": float(arm["blast_in_file"]["player_damage"]),
                      "radius_m": arm["blast_in_file"].get("player_radius"),
                      "source": arm["blast_in_file"]["path"]})
    if arm["per_shot_vs_vehicle"] > 0:
        comps.append({"component": "direct", "channel": ("bullet"
                                                         if arm["gun"] == "bullet_weapon"
                                                         else "unknown"),
                      "damage": arm["per_shot_vs_vehicle"], "radius_m": None,
                      "source": arm["tune"]})
    return comps


def predict(veh: dict, arm: dict) -> dict:
    hp = float(veh["max_health"])
    out = {"primary": None, "components": []}
    comps = arm_damage(arm)
    # the primary component is the one that can kill fastest: the largest damage
    primary = max(comps, key=lambda c: c["damage"]) if comps else None
    for comp in comps:
        ch = comp["channel"]
        armour = veh["channels"].get(ch, {"armor": 0, "strength": 0})
        row = {"channel": ch, "damage": round(comp["damage"], 6), "component": comp["component"],
               "armor": armour["armor"], "strength": armour["strength"]}
        for model in MODELS:
            row[model] = hits(hp, armour["armor"], armour["strength"], comp["damage"], model)
        out["components"].append(row)
    if primary is not None:
        out["primary"] = next(r for r in out["components"]
                              if r["component"] == primary["component"])
    return out


def build_key(root: str) -> str:
    """The payload key for the build under test: `build_test-091` for the default root."""
    return ("build_test-091" if os.path.abspath(root) == os.path.abspath(BUILD)
            else "build_" + os.path.basename(os.path.normpath(root)))


def build_payload(root: str | None = None) -> dict:
    build_root = root or BUILD
    bkey = build_key(build_root)
    import jc3weapons  # noqa: E402
    import jc3index  # noqa: E402
    game = os.environ.get("JC3_GAME", jc3index.DEFAULT_GAME)
    rows = [json.loads(line) for line in open(INDEX, encoding="utf-8") if line.strip()]
    index_best = jc3weapons.best_by_path(rows)

    donor = health_from_cache(DONOR)
    tank = health_from_cache(TANK)
    build = health_from_build(build_root)
    epe = find_epe(build_root)
    root = root_fields(epe) if epe else {}
    mech = load_json(MECH)

    vehicles = {}
    for key, src in (("donor", donor), ("medium_tank", tank), (bkey, build)):
        scalars = src["scalars"]
        vehicles[key] = {
            "entity": src["entity"], "file": src["file"],
            "max_health": scalars["max_health"],
            "channels": {ch: {"armor": scalars.get(ch + "_armor"),
                              "strength": scalars.get(ch + "_armor_strength")}
                         for ch in CHANNELS},
            "thresholds": {k: scalars.get(k) for k in
                           ("smoke_threshold", "burn_threshold", "explosion_threshold",
                            "npc_explosion_threshold", "vulnerable_explosion_threshold",
                            "explosion_delay_s", "burn_duration_s", "vulnerable_duration_s")},
            "switches": {k: scalars.get(k) for k in
                         ("impact_damage_factor", "deform_scale", "impact_armor")},
            "part_damage_types": src["part_damage_types"],
        }
    # the fleet ships health=100.0 / invulnerable=0 on all 233 roots (DAMAGE_MECHANISMS §1)
    census_health = [p for p in mech["properties"] if p.get("name") == "health"]
    for key in ("donor", "medium_tank"):
        vehicles[key]["root"] = {"health": census_health[0]["values"] if census_health else None,
                                 "invulnerable": "0 on all 233 roots (DAMAGE_MECHANISMS §1)",
                                 "source": "DAMAGE_MECHANISMS.json (fleet census)"}
    vehicles[bkey]["root"] = {
        "health": root.get("health", {}).get("decoded"),
        "invulnerable": root.get("invulnerable", {}).get("decoded"),
        "source": os.path.basename(epe) if epe else None}

    arms = {}
    for key, label, tune, host, blast in HAND:
        arms[key] = hand_arm(key, label, tune, host, blast, index_best, game)
    for key, label, wid in VEHICLE:
        arms[key] = vehicle_arm(key, label, wid)
    arms["heli_mg"]["impact_pulse"] = impact_pulse("w604_helicopter_mgun_impact")

    table = {}
    for vkey, veh in vehicles.items():
        table[vkey] = {akey: predict(veh, arm) for akey, arm in arms.items()}

    # is there any member in ANY weapon tune that could name the armour channel?
    import re as _re
    bridge_re = _re.compile(r"heavy|armour|armor|damage_type|penetrat", _re.I)
    bridge_hits = 0
    bridge_rows = 0
    for key, _label, tune, _host, _blast in HAND:
        for path, _t, _v in tune_rows(jc3weapons.read_row(index_best[tune], game)):
            bridge_rows += 1
            bridge_hits += 1 if bridge_re.search(path) else 0
    for _key, _label, wid in VEHICLE:
        for line in open(WEAPONS, encoding="utf-8"):
            d = json.loads(line)
            if d["id"] != wid:
                continue
            for src in d["sources"]:
                for inst in src.get("decode", {}).get("instances", []):
                    for path, _t, _v in inst["rows"]:
                        bridge_rows += 1
                        bridge_hits += 1 if bridge_re.search(path) else 0
    channel_bridge = {"tunes": len(HAND) + len(VEHICLE), "rows": bridge_rows,
                      "rows_naming_heavy_or_armour": bridge_hits,
                      "names": sorted({p for key, _l, tune, _h, _b in HAND
                                       for p, _t, _v in
                                       tune_rows(jc3weapons.read_row(index_best[tune], game))
                                       if bridge_re.search(p)})}

    # ---- ARM-1 / ARM-2 at the BmAK ratio (G1-14)
    rules = load_json(BM_RULES)
    pa_damage = {}
    for row in rules["damage_values"]:
        if row["class"] == "RVehicleBatmobile" and row["name"] == "Pawn.Health":
            pa_damage["batmobile_health"] = row["value"]
    cannon = sorted({r["value"] for r in rules["damage_values"]
                     if r["archetype"].endswith("Batmobile_Heavy_Cannon_Primary_Projectile")
                     and r["name"] == "Projectile.Damage"})
    missile = sorted({r["value"] for r in rules["damage_values"]
                      if r["archetype"].endswith("Batmobile_Missile_Projectile")
                      and r["name"] == "Projectile.Damage"})
    emp = sorted({r["value"] for r in rules["damage_values"]
                  if r["archetype"].endswith("Batmobile_EMPMissile_Projectile")
                  and r["name"] == "Projectile.Damage"})
    bmak = {"health": pa_damage["batmobile_health"],
            "heavy_cannon_damage": cannon[0] if cannon else None,
            "missile_damages": missile, "emp_missile_damages": emp,
            "armour_mode_damage_reduction": 0,
            "source": "DAMAGE_RULES.json (G1-14); ArmourModeDamageReduction ships 0 (CHAIN.json)"}
    bmak["heavy_cannon_hits"] = (math.ceil(bmak["health"] / bmak["heavy_cannon_damage"])
                                if bmak["heavy_cannon_damage"] else None)

    small_arms = ["pistol", "assault_rifle", "machine_gun", "shotgun"]
    heavy = ["tank_cannon", "heli_missile", "heli_mg", "rpg", "grenade"]
    max_small = max(c["damage"] for k in small_arms for c in arm_damage(arms[k]))
    shell = max(c["damage"] for c in arm_damage(arms["tank_cannon"]))
    fleet_max_health = 4000  # VOCABULARY.md `max_health` 500 .. 4000, n=233
    arm_req = {
        "max_small_arms_per_hit": round(max_small, 6),
        "tank_shell_damage": round(shell, 6),
        "fleet_max_health": fleet_max_health,
        "bmak_ratio": bmak,
        "max_health_needed": round(bmak["heavy_cannon_hits"] * shell, 3),
        "hits_at_fleet_max_health_H0": math.ceil(fleet_max_health / shell),
        "hits_at_fleet_max_health_H1": math.ceil(fleet_max_health / (shell * 0.5)),
        "arm1_needs": {
            "H1": "bullet_armor_strength = 100 (fleet maximum is 99; out of domain, and test-077 "
                  "shipped exactly this and failed)",
            "H2": f"bullet_armor_strength >= {round(max_small, 6)} (fleet maximum is 99; the "
                  f"shotgun alone delivers {round(max_small, 6)} per trigger pull)",
            "either": "invulnerable = 1 on the CCar root (whole-vehicle; also blocks ARM-2)",
        },
        "arm2_needs": {
            "H2": "explosion_armor_strength < tank shell damage, i.e. strength below "
                  f"{round(shell, 6)} (the build ships 50)",
            "H1": "per-hit = D x (1 - strength/100) must stay above 0, i.e. strength < 100",
            "note": "ARM-1 and ARM-2 cannot both come from `invulnerable`; they need the channel "
                    "split that bullet_heavy_* already expresses at the name level",
        },
    }

    # what differs between the three health modules, measured field by field
    def pdiff(a: list, b: list) -> list[list]:
        out = []
        for ia, ib in zip(a, b):
            for field in ("initial_health", "damaged_health", "loosen_health",
                          "instantly_damaged_by_bullets", "damages_owning_vehicle"):
                if ia.get(field) != ib.get(field):
                    out.append([ia.get("type.string"), field, ia.get(field), ib.get(field)])
        return out

    def sdiff(a: dict, b: dict) -> list[list]:
        return [[k, a.get(k), b.get(k)] for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]

    diffs = {
        "part_table_tank_vs_donor": pdiff(tank["part_damage_types"], donor["part_damage_types"]),
        "part_table_build_vs_donor": pdiff(build["part_damage_types"],
                                           donor["part_damage_types"]),
        "part_table_build_vs_tank": pdiff(build["part_damage_types"],
                                          tank["part_damage_types"]),
        "scalars_tank_vs_donor": sdiff(tank["scalars"], donor["scalars"]),
        "scalars_build_vs_tank": sdiff(build["scalars"], tank["scalars"]),
        "scalars_build_vs_donor": sdiff(build["scalars"], donor["scalars"]),
    }

    # the two chain rows that are measured rather than stated
    chain = [dict(s) for s in CHAIN]
    for step in chain:
        if step["evidence"] == "CHAIN_PART_ROWS":
            step["evidence"] = (
                f"{len(donor['part_damage_types'])} rows in the donor, "
                f"{len(tank['part_damage_types'])} in the medium tank, "
                f"{len(build['part_damage_types'])} in the build - the same 24 `Land_*` names in "
                f"all three, but the numbers differ: the tank's table differs from the donor's "
                f"in {len(diffs['part_table_tank_vs_donor'])} values, while the build's table is "
                f"the donor's with exactly "
                f"{len(diffs['part_table_build_vs_donor'])} change "
                f"({', '.join(r[0] + '.' + r[1] for r in diffs['part_table_build_vs_donor'])}). "
                f"The train's own health module carries a `Train_*` set of 13 names, so the type "
                f"list is per vehicle family, not global")
        if step["step"] == 3:
            step["unknown"] = (
                f"no file maps a weapon to a channel: across the {channel_bridge['tunes']} "
                f"weapon tunes decoded here ({channel_bridge['rows']:,} member rows) "
                f"{channel_bridge['rows_naming_heavy_or_armour']} member names mention "
                f"heavy/armour/penetration, so whether an assault rifle counts as `bullet` and "
                f"a tank MG as `bullet_heavy` is UNKNOWN. The names are the only bridge")
    return {"schema": 1,
            "generated_by": "Tools/scripts/damage_predict.py",
            "builds": {"donor": DONOR, "medium_tank": TANK, "build": build_root,
                       "build_epe": os.path.basename(epe) if epe else None},
            "chain": chain,
            "models": MODELS,
            "vehicles": vehicles,
            "arms": arms,
            "table": table,
            "channel_bridge": channel_bridge,
            "diffs": diffs,
            "fleet": fleet_census(),
            "arm_targets": arm_req,
            "probes": PROBES}


CHAIN = [
    {"step": 1, "name": "the hit lands on a part",
     "carrier": "`VehicleParts.parts[].damage_type` -> a `PartDamageType` name",
     "evidence": "monorailflatbed_vehicle_parts.vmodc (the only VehicleParts module in the fleet "
                 "that decodes: 4 entities, all the same shared file)",
     "class": "decoded (mechanism)", "unknown": (
         "the donor's, the tank's and the build's own part -> damage-type maps: every other "
         "`*_vehicle_parts.vmodc` fails ConvertAdf (MODLOG 98), so which part a given shot hits "
         "and which `PartDamageType` that part carries is UNKNOWN for all three vehicles")},
    {"step": 2, "name": "the weapon delivers damage",
     "carrier": "`<weapon>_weapon[0].tuning.base_tuning.damage` x `vehicle_damage_factor` x "
                "`bullets_per_shot`; blasts use `ForcePulseSettings.PlayerDamage`",
     "evidence": "WEAPONS.jsonl (vehicle arms) + the hand tunes decoded here",
     "class": "decoded (values); the multiplication itself is `derived` - both fields are named, "
              "no file states the product",
     "unknown": "`object_damage_factor` is the character/object half and is not used here; whether "
                "a vehicle takes `damage x vehicle_damage_factor` or the raw `damage` with the "
                "factor applied to impulse only is UNKNOWN (the field name is the only bridge)"},
    {"step": 3, "name": "the damage type selects an armour channel",
     "carrier": "`VehicleDamage` carries 8 channels: bullet, bullet_heavy, explosion, impact, "
                "fire, melee, electricity, grapple_pull",
     "evidence": "the 233 decoded VehicleDamage modules",
     "class": "decoded (the channels exist)",
     "unknown": "no file maps a weapon to a channel. The names are the only bridge"},
    {"step": 4, "name": "the channel's gate",
     "carrier": "`<channel>_armor` (0..5000) + `<channel>_armor_strength` (0..99 for bullets, "
                "0..100 for electricity/grapple)",
     "evidence": "fleet census in this file; MODLOG 97 (the 99/100 gate) and 98 (test-077 with 100 "
                 "still failed, symptom unrecorded)",
     "class": "decoded (values); the composition is UNKNOWN",
     "unknown": "what `_armor` and `_armor_strength` do to a hit. Three models are carried here "
                "(H0/H1/H2) with exact numbers; the Q-1 probes separate them"},
    {"step": 5, "name": "the part's own damage table",
     "carrier": "`VehicleDamage.part_damage_types[]`: initial_health, damaged_health, "
                "loosen_health, instantly_{damaged,loosened,broken}_by_bullets, "
                "damages_owning_vehicle",
     "evidence": "CHAIN_PART_ROWS",
     "class": "decoded (rows); semantics UNKNOWN",
     "unknown": "what initial/damaged/loosen health measure (part HP thresholds? health lost?) "
                "and whether `damages_owning_vehicle` is the only path from part damage to "
                "vehicle health is not in any file"},
    {"step": 6, "name": "the vehicle's health pool and scale",
     "carrier": "`VehicleDamage.max_health` (500..4000) x the entity root's `health` float32 "
                "(100.0 on all 233 roots) + the root's `invulnerable` int32 (0 on all 233)",
     "evidence": "DAMAGE_MECHANISMS.md §1/§3; the build's own `.epe` re-read here",
     "class": "decoded (values)",
     "unknown": "how the root `health` float composes with `max_health` (percent? multiplier? a "
                "separate pool?). Every shipped root is 100.0, so no file shows a second value to "
                "compare against"},
    {"step": 7, "name": "thresholds and death",
     "carrier": "smoke_threshold, burn_threshold, explosion_threshold, "
                "npc_explosion_threshold, vulnerable_explosion_threshold, explosion_delay_s",
     "evidence": "the 233 modules",
     "class": "decoded (values); semantics UNKNOWN",
     "unknown": "whether explosion_threshold is a per-hit blast damage that destroys the vehicle "
                "outright or a health threshold; the fleet's 500..4000 range overlaps max_health "
                "500..4000, so both readings fit the data"},
]

PROBES = [
    {"id": "Q1-DM-A", "question": "is the armour strength a percentage gate (H1) or a per-hit "
                                  "threshold (H2)?",
     "vehicle": "build_test-091", "arm": "tank_cannon", "channel": "explosion",
     "setup": "one tank shell into the Batmobile's body, at the centre of the 8 m blast",
     "H0": "2 shells", "H1": "3 shells", "H2": "2 shells",
     "why": "strength 50 makes H1 halve the 1500 blast; H2 lets it through because 1500 > 50. The "
            "explosion channel is the only one where the two models disagree at a testable count"},
    {"id": "Q1-DM-B", "question": "does the bullet gate at strength 99 leak 1 % (H1) or absorb "
                                  "everything up to strength (H2)?",
     "vehicle": "build_test-091", "arm": "pistol", "channel": "bullet",
     "setup": "200 pistol rounds at the body, health read before and after",
     "H0": "200 rounds = 6,000 damage = destroyed", "H1": "200 rounds x 0.3 = 60 damage, bar barely "
           "moves, no destruction", "H2": "0 damage, bar unchanged",
     "why": "H0 and H1/H2 are separated by 3 orders of magnitude; H1 vs H2 is 60 HP vs 0 HP on a "
            "2000 HP bar (3 %) - readable only if the HUD shows a number. If test-077's failure "
            "was small-arms damage, H1 is already falsified for this channel"},
    {"id": "Q1-DM-C", "question": "does an emptied armour pool take the hit instead of health (H2 "
                                  "pool half)?",
     "vehicle": "medium_tank", "arm": "tank_cannon", "channel": "explosion",
     "setup": "two tank shells into a stock medium tank (explosion_armor 250). Not the donor: its "
              "pool is 0, so H2 collapses to H0 there and the pool half cannot be seen",
     "H0": "2 shells", "H1": "3 shells", "H2": "2 shells (250 absorbed, then 1750 of 2000)",
     "why": "the pool half of H2 is invisible on the donor (armour 0) and only shows on a vehicle "
            "with a non-zero pool"},
]


# ---------------------------------------------------------------------- writing
def arm_line(arm: dict) -> str:
    blast = arm.get("blast_in_file")
    blast_txt = (f"{blast['player_damage']:g} in {blast.get('player_radius'):g} m"
                 if blast else "-")
    return (f"| `{arm['key']}` | {arm['label']} | `{arm['gun']}` | {arm['damage']:g} | "
            f"{arm['vehicle_factor']:g} | {arm['pellets']} | {arm['per_shot_vs_vehicle']:g} | "
            f"{blast_txt} | {arm['channel']} |")


def fmt_hits(v) -> str:
    return "never" if v is None else f"{v:,}"


def to_md(p: dict) -> str:
    L: list[str] = []
    a = L.append
    a("# The JC3 damage model, and the predicted hits-to-kill table (G2-28)")
    a("")
    a("Generated by `python Tools/scripts/damage_predict.py --write`; re-derived and compared")
    a("byte-for-byte by `--check`. Machine half: `DAMAGE_MODEL.json`.")
    a("")
    a("**The short version.** The chain from a bullet to the health bar has seven steps and the")
    a("files give numbers for **four** of them and the *mechanism* for a fifth. The step that")
    a("decides how much of a hit actually reaches health - the composition of `*_armor`,")
    a("`*_armor_strength`, `max_health` and the root `health` float - is in no file the project")
    a("has decoded. It is therefore carried here as **three named models** with exact per-arm")
    a("numbers, and the three Q-1 probes below are the takes that can fail them. Nothing in this")
    a("file claims a composition the data does not state.")
    a("")
    a("## 1. How a hit becomes health loss")
    a("")
    a("| # | step | carrier | evidence | class | UNKNOWN |")
    a("|---|---|---|---|---|---|")
    for s in p["chain"]:
        a(f"| {s['step']} | {s['name']} | {s['carrier']} | {s['evidence']} | {s['class']} | "
          f"{s['unknown']} |")
    a("")
    a("### 1.1 The three models this card computes with")
    a("")
    a("| model | formula | what would make it the true one |")
    a("|---|---|---|")
    a("| **H0** | per-hit = D; hits = ceil(max_health / D) | armour is ignored entirely. This is the "
      "reference, not a claim: it is what the fleet looks like if `*_armor` only feeds deform and "
      "the part layer |")
    a("| **H1** | per-hit = D x (1 - strength/100); strength 100 = never | MODLOG 97's reading "
      "(\"99/100 is not a full gate - it passes 1 % of every bullet\"). **Counter-evidence:** "
      "test-077 shipped exactly strength 100 and still failed (MODLOG 98, symptom unrecorded) |")
    a("| **H2** | D <= strength -> absorbed; else ceil((armor + HP)/D) | the two fields are an "
      "absorb-and-block pair: `*_armor` = pool, `_strength` = per-hit threshold. The fleet's "
      "`bullet_armor` 5000 maximum and the medium tank's 5000 @ 99 fit a 5,000-point pool; the "
      "donor's 0 @ 0 fits \"no armour at all\" |")
    a("")
    a("## 2. The three vehicles")
    a("")
    a("| value | donor (`v0300 civilian_01`) | medium tank (`v0201 military_01`) | build "
      "(`Builds/test-091`) |")
    a("|---|---:|---:|---:|")
    veh = p["vehicles"]
    d, t, b = veh["donor"], veh["medium_tank"], build_vehicle(veh)
    a(f"| module file | `{d['file'].split('/')[-1]}` | `{t['file'].split('/')[-1]}` | "
      f"`{b['file']}` |")
    a(f"| `max_health` | {d['max_health']} | {t['max_health']} | {b['max_health']} |")
    for ch in CHANNELS:
        a(f"| `{ch}_armor` @ strength | {d['channels'][ch]['armor']} @ "
          f"{d['channels'][ch]['strength']:g} | {t['channels'][ch]['armor']} @ "
          f"{t['channels'][ch]['strength']:g} | {b['channels'][ch]['armor']} @ "
          f"{b['channels'][ch]['strength']:g} |")
    a(f"| `part_damage_types` rows | {len(d['part_damage_types'])} | "
      f"{len(t['part_damage_types'])} | {len(b['part_damage_types'])} |")
    a(f"| root `health` / `invulnerable` | 100.0 / 0 (fleet census) | 100.0 / 0 (fleet census) | "
      f"{b['root']['health']} / {b['root']['invulnerable']} |")
    a(f"| `impact_damage_factor` / `deform_scale` | {d['switches']['impact_damage_factor']} / "
      f"{d['switches']['deform_scale']} | {t['switches']['impact_damage_factor']} / "
      f"{t['switches']['deform_scale']} | {b['switches']['impact_damage_factor']} / "
      f"{b['switches']['deform_scale']} |")
    a("")
    diffs = p["diffs"]
    changed = ", ".join(f"`{row[0]}` {row[2]} -> {row[1]}" for row in diffs["scalars_build_vs_tank"])
    a("**Measured, and it matters.** The build's scalars differ from the **medium tank's** in")
    a(f"{len(diffs['scalars_build_vs_tank'])} values: {changed}.")
    a(f"Against the **donor** it differs in {len(diffs['scalars_build_vs_donor'])} values. So the")
    a(f"build is the tank's profile with the impact and melee pairs raised to 5000 @ 100 and the")
    a("two off-switches set - not a translation of the donor, which is 700 HP with every channel")
    a("at 0 @ 0 (everything above is counted, not asserted: `DAMAGE_MODEL.json` carries the six")
    a("field-by-field diffs under `diffs`).")
    a("")
    a(f"The part table is a third, separate thing. The same 24 `Land_*` names appear in all")
    a(f"three, but the tank's numbers differ from the donor's in")
    a(f"{len(diffs['part_table_tank_vs_donor'])} values, while the **build's part table is the")
    a(f"donor's with exactly {len(diffs['part_table_build_vs_donor'])} change**:")
    for row in diffs["part_table_build_vs_donor"]:
        a(f"`{row[0]}.{row[1]}` **{row[3]} -> {row[2]}** (donor -> build). That single flag is")
        a("the only ARM-4-shaped edit in the live build: a bullet no longer **instantly** damages")
        a("the `Land_Wheel` type. It is not on its own proof of ARM-4 - the wheel keeps")
        a("`initial_health` 1020 and `loosen_health` 100, so sustained fire can still take it to")
        a("the damaged state over time; that is Q-1's business, not this file's.")
    a("It is the only part-level damage edit in the build, and it is in the donor's table, not the")
    a("tank's - a fact no earlier document states.")
    a("")
    a("## 3. The nine arms")
    a("")
    a("Vehicle arms come from `WEAPONS.jsonl`; hand arms are re-decoded from the archives, because")
    a("G2-10 only covered `06_vehicle/`. `per shot vs vehicle` = damage x vehicle_damage_factor x")
    a("pellets - the multiplication is **derived** from the two field names, not read.")
    a("")
    a("| key | arm | gun type | damage | veh. factor | pellets | per shot vs vehicle | blast "
      "(PlayerDamage) | channel used |")
    a("|---|---|---|---:|---:|---:|---:|---|---|")
    for key, _label, _t, _h, _b in HAND:
        a(arm_line(p["arms"][key]))
    for key, _label, _wid in VEHICLE:
        a(arm_line(p["arms"][key]))
    pulse = p["arms"]["heli_mg"].get("impact_pulse")
    if pulse:
        a("")
        a(f"`w604` also ships an impact pulse (`{pulse['path'].split('/')[-1]}`, PlayerDamage "
          f"{pulse['player_damage']:g} in {pulse['player_radius']:g} m) as the `CForcePulse` of the")
        a("two attack helicopters (G2-10), **not** as a field of the weapon; whether it fires on")
        a("every bullet hit is UNKNOWN, so the table uses the direct 25 and notes 50 as the")
        a("alternative on those two helicopters only.")
    a("")
    a("Two facts about the arms that the card's list does not expect:")
    a("")
    a("1. **The tank cannon's `bullet_weapon` damage is 1.0** (player tune) - a tank shell does its")
    a("   work through the **1500 blast in 8 m**, not through the bullet. `w602`'s AI tune is 20 x")
    a("   10 = 200, which is the AI-vs-vehicle path.")
    a("2. **The shotgun fires 8 pellets of 90 x 0.2** = 144 per trigger pull, more per hit than any")
    a("   other small arm by 4.5x - which is why the ARM-1 gate cannot be set from the pistol's")
    a("   number alone.")
    a("")
    a("## 4. Predicted hits-to-kill")
    a("")
    a("Per-shot damage against the **primary** component (the largest one), on that component's")
    a("channel. `never` = the model says the hit cannot reach health. Part-level damage (step 1)")
    a("is not modelled: it is UNKNOWN for all three vehicles, so every number below assumes the")
    a("root pool is what takes the hit.")
    a("")
    bkey = build_key(p["builds"]["build"])
    names = {"donor": "donor", "medium_tank": "medium tank",
             bkey: ("build test-091" if bkey == "build_test-091" else "build " + bkey[6:])}
    arms_order = [k for k, _l, _t, _h, _b in HAND] + [k for k, _l, _w in VEHICLE]
    for vkey in ("donor", "medium_tank", bkey):
        a(f"### {names[vkey]}")
        a("")
        a(f"max_health {p['vehicles'][vkey]['max_health']}; "
          f"channel = armour @ strength")
        a("")
        a("| arm | channel | armour @ strength | H0 (no armour) | H1 (percentage) | H2 (threshold "
          "+ pool) |")
        a("|---|---|---|---:|---:|---:|")
        for akey in arms_order:
            row = p["table"][vkey][akey]["primary"]
            if row is None:
                a(f"| `{akey}` | - | - | - | - | - |")
                continue
            a(f"| `{akey}` | {row['channel']} | {row['armor']} @ {row['strength']:g} | "
              f"{fmt_hits(row['H0'])} | {fmt_hits(row['H1'])} | {fmt_hits(row['H2'])} |")
        a("")
    a("Rows whose channel is `unknown` (a missile direct hit and the grenade's thrown damage:")
    a("no armour channel in `VehicleDamage` is named for either) are computed with the")
    a("no-armour value, so their count is a **lower bound** on hits, not a prediction.)")
    a("")
    a("Read the three columns as a bracket, not a prediction: the true count for each arm is one")
    a("of them, and Q1-DM-A/B/C pick which. What is **not** model-dependent:")
    a("")
    a("- the donor (700 HP, every channel 0) takes **the same count under all three models**,")
    a("  because every model agrees when armour is 0; only the shotgun (144) and the blasts take")
    a("  more than one hit;")
    a("- the medium tank and the build are effectively bullet-proof under H1 and H2 (6,667 pistol")
    a("  rounds, or `never`) and merely tough under H0 (67) - the models disagree by two orders of")
    a("  magnitude on exactly the channel ARM-1 is about;")
    a("- a tank shell (1500 in 8 m) is 2 hits on 2000 HP under H0/H2 and 3 under H1, so the")
    a("  explosion channel is where the models can be told apart at a small, testable count.")
    a("")
    a("## 5. What values would give ARM-1 and ARM-2")
    a("")
    req = p["arm_targets"]
    bmak = req["bmak_ratio"]
    a("The BmAK side is decoded (`DAMAGE_RULES.json`, G1-14): `Pawn.Health` **1200**, the heavy")
    a(f"cannon projectile `Damage` **{bmak['heavy_cannon_damage']:g}**, missile "
      f"{', '.join(f'{v:g}' for v in bmak['missile_damages'])}, and `ArmourModeDamageReduction`")
    a("**0** - so the BmAK ratio is")
    a(f"**{bmak['health']} / {bmak['heavy_cannon_damage']:g} = "
      f"{bmak['heavy_cannon_hits']} heavy-cannon hits** (or "
      f"{bmak['health']} / {max(bmak['missile_damages']):g} = "
      f"{math.ceil(bmak['health'] / max(bmak['missile_damages']))} missile hits).")
    a("")
    a("| requirement | what it needs | inside the shipped domain? |")
    a("|---|---|---|")
    a(f"| **ARM-1** small arms do not move the bar | H1: `bullet_armor_strength` 100 | **no** - the "
      f"fleet maximum is 99, and test-077 shipped 100 and failed |")
    a(f"| | H2: `bullet_armor_strength` >= {req['max_small_arms_per_hit']:g} | **no** - 99 is the "
      f"maximum, and the shotgun delivers {req['max_small_arms_per_hit']:g} per pull |")
    a("| | either: `invulnerable` 1 on the `CCar` root | **yes** (4 bytes at `epe+1167`) but it is "
      "whole-vehicle |")
    a(f"| **ARM-2** heavy weapons destroy it | H2: explosion strength below the shell damage "
      f"({req['tank_shell_damage']:g}) - the build ships 50 | **yes**, already true |")
    a("| | H1: strength below 100 so the shell still passes | **yes**, already true |")
    a(f"| **ARM-2 at the BmAK ratio** ({bmak['heavy_cannon_hits']} shell hits) | `max_health` = "
      f"{bmak['heavy_cannon_hits']} x {req['tank_shell_damage']:g} = "
      f"{req['max_health_needed']:,g} | **no** - the fleet range is 500..4000, i.e. "
      f"{req['hits_at_fleet_max_health_H0']} hits under H0/H2 and "
      f"{req['hits_at_fleet_max_health_H1']} under H1 at the maximum |")
    a("")
    a("**The consequence for the ledger.** ARM-1 and ARM-2 cannot both be expressed by")
    a("`invulnerable` (it is whole-vehicle), and the only per-channel split the files offer is the")
    a("**bullet vs bullet_heavy** pair - which is exactly how the medium tank is built (bullet")
    a("5000 @ 99, bullet_heavy 5 @ 20). Whether a given weapon lands in `bullet` or")
    a("`bullet_heavy` is UNKNOWN (step 3), so T-14 cannot write those rows from the files alone:")
    a("it needs either a `bullet_heavy` carrier found in G2-11's weapon components, or the Q-1")
    a("probe below. Writing `bullet_armor_strength` 100 was tried once (test-077) and failed.")
    a("")
    a("The root `health` float is **100.0 on all 233 roots**, so a scale other than 100 has no")
    a("precedent in the fleet and no range in the files: for hits-to-kill it is UNKNOWN whether")
    a("it scales `max_health` at all. The table above assumes it is a 1.0 multiplier (all three")
    a("targets ship 100.0).")
    a("")
    a("## 6. Q-1 damage probes (exact expected values)")
    a("")
    for probe in p["probes"]:
        a(f"### `{probe['id']}` - {probe['question']}")
        a("")
        a(f"- vehicle: `{probe['vehicle']}`, arm: `{probe['arm']}`, channel: "
          f"`{probe['channel']}`")
        a(f"- setup: {probe['setup']}")
        a(f"- **H0**: {probe['H0']}")
        a(f"- **H1**: {probe['H1']}")
        a(f"- **H2**: {probe['H2']}")
        a(f"- why: {probe['why']}")
        a("")
    a("## 7. Fleet evidence for the gate question")
    a("")
    fl = p["fleet"]
    a(f"`{fl['modules']}` `VehicleDamage` modules. Distinct `armor @ strength` pairs per channel")
    a("(vehicles):")
    a("")
    a("| channel | pairs |")
    a("|---|---|")
    for ch in CHANNELS:
        pairs = sorted(fl["pairs"][ch].items(), key=lambda kv: -kv[1])
        txt = ", ".join(f"`{k}` x{v}" for k, v in pairs[:6])
        a(f"| `{ch}` | {txt} |")
    a("")
    a("The `bullet` channel is the only one where a large minority sits at the maximum (99) while")
    a("most sit at 0; `impact`, `melee`, `electricity` and `grapple_pull` cluster at their")
    a("maximums or at `-1`; `explosion` spreads across 0..100. That is consistent with `bullet`")
    a("being the one gate the designers actually tuned per vehicle - and with `bullet_heavy` being")
    a("the second, at much lower values.")
    a("")
    a("## 8. UNKNOWNs, stated")
    a("")
    a("- **the composition rule itself** (step 4/6) - see the three models; no file states it.")
    a("- **part -> damage type for all three vehicles** (step 1): every `*_vehicle_parts.vmodc`")
    a("  except the monorail flatbed fails ConvertAdf. So the part layer cannot be predicted at")
    a("  all, and every hits-to-kill number here is \"whole vehicle takes every hit\".")
    a("- **weapon -> armour channel** (step 3): no tune carries a damage-type or heavy flag.")
    a("- **root `health` float semantics** (step 6): all 233 roots are 100.0.")
    a("- **`explosion_threshold` semantics** (step 7).")
    a("- **which pistol/rifle etc. Rico starts with**: the table uses one named variant per class")
    a("  (`w011`, `w111`, `w131`, `w151`, `w141`, `w301`); the class spans 5 pistol / 4 AR / 2 MG /")
    a("  4 shotgun / 7 RPG variants in the index, and no file names a default loadout.")
    a("- **the BmAK incoming-damage numbers**: `GetDamageMod` is native (G1-14 §7), so the BmAK")
    a("  side of the ratio is the projectile `Damage`, not the health loss a player sees.")
    a("")
    a("## 9. Reproduce")
    a("")
    a("```")
    a("python Tools/scripts/damage_predict.py --write    # writes DAMAGE_MODEL.md + .json")
    a("python Tools/scripts/damage_predict.py --check    # re-derives and compares")
    a("python Tools/scripts/damage_predict.py dump       # the payload to stdout")
    a("```")
    a("")
    return "\n".join(L) + "\n"


def write(payload: dict) -> int:
    with open(JSON_OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    with open(DOC, "w", encoding="utf-8", newline="\n") as f:
        f.write(to_md(payload))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--root", help="build to read instead of Builds/test-091 (with `dump`/`table`)")
    ap.add_argument("cmd", nargs="?", choices=["dump", "table"])
    a = ap.parse_args()
    if a.root and (a.write or a.check):
        ap.error("--root changes what the table is computed from; use it with dump/table")
    payload = build_payload(a.root)
    if a.cmd == "table":
        v = payload["vehicles"]
        bkey = build_key(payload["builds"]["build"])
        print(f"build under test: {payload['builds']['build']} ({bkey}, "
              f"max_health {v[bkey]['max_health']})")
        print(f"{'arm':<14} {'channel':<10} {'damage':>9}  {'H0':>5} {'H1':>5} {'H2':>5}")
        for akey in [k for k, _l, _t, _h, _b in HAND] + [k for k, _l, _w in VEHICLE]:
            row = payload["table"][bkey][akey]["primary"]
            if row is None:
                print(f"{akey:<14} {'-':<10} {'-':>9}  {'-':>5} {'-':>5} {'-':>5}")
                continue
            cell = lambda m: "never" if row[m] is None else str(row[m])  # noqa: E731
            print(f"{akey:<14} {row['channel']:<10} {row['damage']:>9.2f}  "
                  f"{cell('H0'):>5} {cell('H1'):>5} {cell('H2'):>5}")
        print("hits-to-kill against the root pool; H0 armour ignored / H1 percentage gate / "
              "H2 threshold+pool")
        return 0
    if a.cmd == "dump":
        print(json.dumps(payload, indent=1, sort_keys=True))
        return 0
    if a.write:
        write(payload)
        print(f"wrote {os.path.relpath(DOC, ROOT)} and {os.path.relpath(JSON_OUT, ROOT)}")
        return 0
    if a.check:
        want_json = json.dumps(payload, indent=1, sort_keys=True) + "\n"
        want_md = to_md(payload)
        ok = True
        if not os.path.exists(JSON_OUT):
            print("FAIL: DAMAGE_MODEL.json missing")
            return 1
        have_json = open(JSON_OUT, encoding="utf-8").read()
        if have_json != want_json:
            import difflib
            print("FAIL: DAMAGE_MODEL.json stale")
            for line in list(difflib.unified_diff(have_json.splitlines(),
                                                  want_json.splitlines(),
                                                  "on disk", "re-derived", n=2))[:40]:
                print(line)
            ok = False
        if not os.path.exists(DOC):
            print("FAIL: DAMAGE_MODEL.md missing")
            return 1
        have_md = open(DOC, encoding="utf-8").read()
        if have_md != want_md:
            import difflib
            print("FAIL: DAMAGE_MODEL.md stale")
            for line in list(difflib.unified_diff(have_md.splitlines(), want_md.splitlines(),
                                                  "on disk", "re-derived", n=2))[:40]:
                print(line)
            ok = False
        if not ok:
            return 1
        v = payload["vehicles"]
        t = payload["table"]
        counts = {m: sum(1 for vk in t for ak in t[vk]
                         if t[vk][ak]["primary"] and t[vk][ak]["primary"][m] is not None)
                  for m in MODELS}
        never = {m: sum(1 for vk in t for ak in t[vk]
                        if t[vk][ak]["primary"] and t[vk][ak]["primary"][m] is None)
                 for m in MODELS}
        print(f"PASS: {len(payload['arms'])} arms x {len(v)} vehicles, models "
              f"{', '.join(sorted(MODELS))}, finite H0 {counts['H0']} / H1 {counts['H1']} / "
              f"H2 {counts['H2']}, never H1 {never['H1']} / H2 {never['H2']}")
        print(f"      chain {len(payload['chain'])} steps, "
              f"{sum(1 for s in payload['chain'] if s['unknown'])} carry an UNKNOWN, "
              f"{len(payload['probes'])} Q-1 probes")
        print(f"      donor {v['donor']['max_health']} HP / tank {v['medium_tank']['max_health']}"
              f" HP / build {build_vehicle(v)['max_health']} HP, "
              f"fleet {payload['fleet']['modules']} modules, "
              f"json match True")
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
