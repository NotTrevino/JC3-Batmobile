"""t11_modes.py - modes translation (T-15).

`GRAB_BACKLOG.md` §1.6 asks for two cars' worth of behaviour in one: **MOD-1 pursuit** (afterburner,
Immobilizer, ram immunity, high speed) and **MOD-2 battle** (turret weapons, turn on the spot, low
top speed, armour reduction, battle camera, battle lights, transformation, battle audio). Decision
**D-2 was resolved to (b) one hybrid car on 2026-10-28 and was REOPENED on 2026-11-06**: BmAK has
two modes, and a hybrid cannot carry T-MD5/T-MD6/T-MD7/T-MD8/T-MD13/T-MD14, so those rows moved
from `out` to `blocked` and card B-12 is live again (`tmp/freebuff/reports/apply-mode-switch-rows.md`).

So this tool emits **one row set** - what one hybrid car can hold, which is now the *record of the
withdrawn decision*, not the target - and the variant table
(`t11_variants.json`) records, for every row, what the pursuit half and the battle half would each
have used plus what the single car actually gets. A compromise is only ever one of three kinds,
and each row says which:

  carried        the single car carries the value unchanged (mode-independent, or JC3 is always
                 on anyway)
  inside band    the battle value falls inside the band the single car already holds, so no value
                 changes and only a *switch* would be missing
  omitted        the mode needs a switch JC3 does not have, so the battle-only behaviour is a
                 named omission with its BmAK numbers recorded

Every BmAK number is read from a record, never typed: G1-21's `MODES.json` (the 107 declared mode
fields, their units and their per-package values), G1-21's `CAMERA.json` (the camera class and its
config structs, indexed by field *name*), the G1 object stream `objects.jsonl` (the sim class's
`StandardTorqueVSpeedCurve` / `BoostTorqueVSpeedCurve` / `BattleModeVSpeedCurve` points, all four
packages), G1-08's `WEAPONS.json` (the Immobilizer archetype's instance/field counts), G2-22/23's
`USAGES.json` (nitro donor values, carriers and the fleet size), G2-21's `TANKTURN.json`, G2-33's
`LIGHT_SYSTEM.json`, T-18's `t14_lights.json`, T-16's `t12_audio_map.json` (W-08's event and WEM
counts) and CAM-1's read-back `Working/Camera/CAM_TUNE.json` (the delivered `.ctune`'s FOV band and
camera offsets). Every JC3 carrier is cross-checked against `T_ROWS.jsonl` (T-11's weapons, T-14's
damage rows, T-16's audio row, T-18's light rows) so no row claims a carrier another card has
already refused.

The list of behaviours a row set must cover is **not** this tool's opinion: it is parsed from the
T-15 card's own `Do:` parenthetical in `GRAB_BACKLOG.md` (`CARD_ROWS` names the row(s) that answer
each item), so a card item with no row fails `--check`.

Usage:
  python Tools/scripts/t11_modes.py --write
  python Tools/scripts/t11_modes.py --check
  python Tools/scripts/t11_modes.py show T-MD8
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
WORK = os.path.join(ROOT, "Working", "Translation")
BAT = os.path.join(ROOT, "Research", "BatmobileGrab")
JC3 = os.path.join(ROOT, "Research", "JC3Grab")
MODES = os.path.join(BAT, "MODES.json")
CAMERA = os.path.join(BAT, "CAMERA.json")
OBJECTS = os.path.join(BAT, "objects.jsonl")
WEAPONS = os.path.join(BAT, "WEAPONS.json")
TANKTURN = os.path.join(JC3, "TANKTURN.json")
LIGHTS = os.path.join(JC3, "LIGHT_SYSTEM.json")
USAGES = os.path.join(JC3, "USAGES.json")
T14 = os.path.join(WORK, "t14_lights.json")
T12 = os.path.join(WORK, "t12_audio_map.json")
CAMTUNE = os.path.join(ROOT, "Working", "Camera", "CAM_TUNE.json")
LEDGER = os.path.join(WORK, "T_ROWS.jsonl")
BACKLOG = os.path.join(ROOT, "GRAB_BACKLOG.md")
OUT_MD = os.path.join(WORK, "T11_MODES.md")
OUT_JSON = os.path.join(WORK, "t11_variants.json")

# the card's Do list, one row each, plus the hybrid declaration itself
MOD2_BEHAVIOURS = ["turret weapons", "turn on the spot", "top speed curve", "armour reduction",
                   "battle camera", "battle lights", "steering and drive factors",
                   "battle audio", "transformation stance"]
MOD1_BEHAVIOURS = ["afterburner", "Immobilizer (EMP missile)", "ram immunity",
                   "high speed (standard/boost torque curve)"]
COMPROMISES = ["carried", "inside band", "omitted"]
# R4's class column: every built value carries one of these
CONFIDENCES = ("decoded", "decoded (fleet)", "derived", "class", "epe", "read")
# The T-15 card's `Do:` parenthetical - "every row that differs (top speed curve, torque,
# steering/pivot, weapons enabled, camera tune, lights, armour reduction, audio)" - mapped to the
# row(s) that answer each item.  `--check` parses the card from `GRAB_BACKLOG.md` and fails when an
# item is missing here or a row named here does not exist, so the card owns the coverage list.
CARD_ROWS = {"top speed curve": ["T-MD5"],
             "torque": ["T-MD4"],
             "steering/pivot": ["T-MD7", "T-MD8"],
             "weapons enabled": ["T-MD9"],
             "camera tune": ["T-MD11"],
             "lights": ["T-MD12"],
             "armour reduction": ["T-MD10"],
             "audio": ["T-MD14"]}


# --------------------------------------------------------------------------- inputs
def load_json(path):
    return json.load(open(path, encoding="utf-8"))


def field(F: dict, name: str) -> dict:
    for f in F["fields"]:
        if f["field"] == name:
            return f
    raise SystemExit(f"MODES.json has no field {name}")


PKG = {"Playable_Batmobile_SF": "V2", "Playable_BatmobileMK2_SF": "MK2",
       "Playable_BatmobileJoker_SF": "Joker", "Playable_BatmobileFunhouse_SF": "Funhouse"}


def one_value(f: dict) -> str:
    """The value all four packages agree on, or the per-package list when they differ."""
    vals = {k: v for k, v in (f.get("values") or {}).items() if v is not None}
    if not vals:
        return "not serialised"
    uniq = sorted({round(v, 6) if isinstance(v, float) else v for v in vals.values()})
    if len(uniq) == 1:
        return f"{uniq[0]:g}" if isinstance(uniq[0], float) else str(uniq[0])
    return ", ".join(f"{k.replace('Playable_Batmobile', '')}: {v!r}" for k, v in sorted(vals.items()))


def pkg_pairs(F: dict, name: str) -> list[tuple[str, object]]:
    """(short package, value) in the record's package order - the cells print these."""
    f = field(F, name)
    return [(PKG.get(p["package"], p["package"]), f["values"].get(p["package"]))
            for p in F["packages"]]


def fmt_pairs(F: dict, name: str) -> str:
    """A per-package value list, so a row that differs cannot be quoted as one number."""
    pairs = pkg_pairs(F, name)
    missing = [k for k, v in pairs if v is None]
    if missing:
        raise SystemExit(f"{name} has no value for {missing}")
    return ", ".join(f"{k} {v:g}" if isinstance(v, float) else f"{k} {v}" for k, v in pairs)


def sim_curves() -> dict:
    """The sim class's curves, read from the G1 object stream (`objects.jsonl`, 4 packages)."""
    want = ("StandardTorqueVSpeedCurve", "BoostTorqueVSpeedCurve", "BattleModeVSpeedCurve")
    per: dict[str, dict[str, list]] = {}
    for line in open(OBJECTS, encoding="utf-8"):
        if '"RVehicleSimBatmobile"' not in line:
            continue
        o = json.loads(line)
        if o.get("class") != "RVehicleSimBatmobile" or o.get("name") != "SimulationModel":
            continue
        found: dict[str, list] = {}
        for tag in o.get("tags") or []:
            if tag.get("name") not in want:
                continue
            pts: list[list[float]] = []
            for prop in tag.get("props") or []:
                for item in prop.get("items") or []:
                    vals = [t["value"] for t in item if "value" in t]
                    pts.append([float(vals[0]), float(vals[1])])       # InVal, OutVal
            if pts:
                found[tag["name"]] = pts
        per[o["package"]] = found
    out: dict[str, dict] = {}
    for name in sorted({n for c in per.values() for n in c}):
        have = [c[name] for c in per.values() if name in c]
        out[name] = {"points": have[0], "count": len(have[0]),
                     "packages": sorted(p for p, c in per.items() if name in c),
                     "same": len({json.dumps(p) for p in have}) == 1}
    out["packages_read"] = len(per)
    return out


def cam_tune() -> dict:
    """CAM-1's read-back: the delivered `.ctune`'s FOV band and camera offsets, as re-read."""
    T = load_json(CAMTUNE)
    edits = {(e["member"], e["index"]): e for e in T["edits"]}

    def val(member: str, index: int) -> float:
        e = edits.get((member, index))
        if e is None:
            raise SystemExit(f"CAM_TUNE.json has no {member}[{index}] edit")
        return float(e.get("readback", e["new"]))

    return {"fov_lo": val("FOV", 0), "fov_hi": val("FOV", 1),
            "back_m": val("CameraPosition", 2), "up_m": val("CameraPosition", 1),
            "readback_ok": T["readback"]["ok"], "readback_expected": T["readback"]["expected"],
            "sha256": T["output"]["sha256"]}


def card_behaviours(backlog: str) -> list[str]:
    """The T-15 card's `Do:` parenthetical - the items one row set must answer."""
    m = re.search(r"^#### T-15 ·.*?(?=^#### |\Z)", backlog, re.S | re.M)
    if not m:
        raise SystemExit("GRAB_BACKLOG.md has no T-15 card")
    d = re.search(r"every row that differs\s*\(([^)]*)\)", m.group(0))
    if not d:
        raise SystemExit("the T-15 card no longer names 'every row that differs (...)'")
    return [p.strip() for p in d.group(1).split(",") if p.strip()]


def gather() -> dict:
    F = load_json(MODES)
    cam = load_json(CAMERA)
    tank = load_json(TANKTURN)
    lights = load_json(LIGHTS)
    usages = load_json(USAGES)
    l14 = load_json(T14)
    weapons = load_json(WEAPONS)
    audio = load_json(T12)
    ledger = {r["id"]: r for r in (json.loads(l) for l in open(LEDGER, encoding="utf-8")
                                  if l.strip())}
    backlog = open(BACKLOG, encoding="utf-8").read()

    curves = sim_curves()
    tune = cam_tune()
    emp = next(c for c in weapons["classes"] if c["name"] == "RBatmobileEMPMissile")
    w08 = next(r for r in audio["rows"] if r["id"] == "W-08")
    cfg = cam["configs"]["BattleModeCamConfig"]
    cfg_names = cfg["fields"]
    if len(cfg_names) != len(cfg["values"]):
        raise SystemExit("BattleModeCamConfig names and values differ in length")
    cfg_idx = {n: i for i, n in enumerate(cfg_names)}
    serialised = [f for f in F["fields"] if f.get("values")]
    identical = [f["field"] for f in serialised if f.get("same_in_all_four")]
    differing = [f["field"] for f in serialised if not f.get("same_in_all_four")]
    table_fields = ("BattleModeVSpeedCurve", "TurningModeMaxSpeed", "BattleModeDriveForceFactor",
                    "BattleModeLatSlipScale", "BattleModeLongSlipScale",
                    "TurnOnSpotFrontTorqueFactor", "TurnOnSpotRearTorqueFactor",
                    "ArmourModeDamageReduction", "TransformationTurnTorqueFactor",
                    "TransformationTurnDecelTorqueFactor", "TransformationAnimNode",
                    "BattleModeCamFOV")

    curve = field(F, "BattleModeVSpeedCurve")["struct"]
    points = [[float(a), float(b)] for a, b in curve["points"]]
    turning = field(F, "TurningModeMaxSpeed")
    turning_cms = sorted({v for v in turning["values"].values() if v is not None})[0]
    kmh = turning_cms / 100.0 * 3.6          # cm/s -> m/s -> km/h, the unit `conv` basis
    armour = field(F, "ArmourModeDamageReduction")

    battle_lights = [r for r in l14["rows"] if r.get("bmak_type") == "VEHLT_BattleModeLight"]
    behaviours = sorted((lights.get("module") or {}).get("behaviors") or {})

    return {
        "modes": {"declared": F["summary"]["declared"], "serialised": F["summary"]["serialized"],
                  "packages": [p if isinstance(p, str) else p.get("name", str(p))
                               for p in F["packages"]],
                  "same_in_all_four": len(identical), "differing": differing,
                  "curve_points": points,
                  "curve_same": bool(field(F, "BattleModeVSpeedCurve")["same_in_all_four"]),
                  "curve_count": curve["props"][0]["count"],
                  "curve_unit": field(F, "BattleModeVSpeedCurve")["unit"],
                  "curve_unit_basis": field(F, "BattleModeVSpeedCurve")["unit_basis"],
                  "units": {n: {"unit": field(F, n)["unit"],
                                "basis": field(F, n)["unit_basis"]} for n in table_fields},
                  "torque": {n: curves[n] for n in
                             ("StandardTorqueVSpeedCurve", "BoostTorqueVSpeedCurve")},
                  "curves": {k: v for k, v in curves.items() if k != "packages_read"},
                  "curve_packages_read": curves["packages_read"],
                  "turning_cms": turning_cms, "turning_kmh": round(kmh, 1),
                  "armour": {"value": one_value(armour), "unit": armour["unit"],
                             "packages": sorted(armour["values"]),
                             "absent": sorted({p["package"] for p in F["packages"]}
                                              - set(armour["values"]))},
                  "pivot": {n: one_value(field(F, n)) for n in
                            ("TurnOnSpotFrontTorqueFactor", "TurnOnSpotRearTorqueFactor",
                             "TurnOnSpotModeEngineBrakingFactor",
                             "BattleModeTurnOnSpotTorqueFactor")},
                  "drive": {n: one_value(field(F, n)) for n in
                            ("BattleModeDriveForceFactor", "BattleModeLatSlipScale",
                             "BattleModeLongSlipScale", "BattleModeSteerAngleFactor",
                             "BattleModeTrailingSteerFactorMoving",
                             "BattleModeDrivingForceZOffset", "BattleModeThrottleSpeed")},
                  "transform": {n: one_value(field(F, n)) for n in
                                ("TransformationTurnTorqueFactor",
                                 "TransformationTurnDecelTorqueFactor",
                                 "TransformationAnimNode")},
                  "transform_anim_packages": len(field(F, "TransformationAnimNode")["values"]),
                  "not_serialised": F["summary"]["not_serialized"],
                  "sounds": {n: fmt_pairs(F, n) for n in
                             ("TransformationReverseDirectionIntoPursuitModeSound",
                              "TransformationReverseDirectionIntoBattleModeSound")}},
        "camera": {"BattleModeCamFOV": cam["values"].get("BattleModeCamFOV"),
                   "BattleModeWinchCamFOV": cam["values"].get("BattleModeWinchCamFOV"),
                   "AntiPersonelBattleModeCamFOV": cam["values"].get(
                       "AntiPersonelBattleModeCamFOV"),
                   "config_fields": len(cfg_names),
                   "config_min_distance": cfg["values"][cfg_idx["MinFreeCameraDistance"]],
                   "config_max_distance": cfg["values"][cfg_idx["MaxFreeCameraDistance"]],
                   "class": cam["class"]},
        "tankturn": {"candidates": len(tank.get("candidates") or []),
                     "fleet_types": tank["module_types"]["fleet"],
                     "tank_types": tank["module_types"]["tank"],
                     "tank_only": tank["module_types"]["tank_only"]
                     if isinstance(tank["module_types"]["tank_only"], int)
                     else len(tank["module_types"]["tank_only"]),
                     "unique_values": tank["unique"]["total"],
                     "driving_hits": len(tank["unique"]["driving_module_hits"]),
                     "pivot_named_omission": "MOD-2's turn-on-the-spot is a named omission" in
                                             open(os.path.join(JC3, "TANKTURN.md"),
                                                  encoding="utf-8").read()},
        "lights": {"behaviours": behaviours, "behaviour_count": len(behaviours),
                   "battle_behaviour": [b for b in behaviours if "battle" in b.lower()],
                   "battle_rows": [r["id"] for r in battle_lights],
                   "battle_targets": sorted(t["name"] for r in battle_lights
                                            for t in r.get("targets", []))},
        "nitro": usages["nitro"]["arcade"]["donor"]["nitro_boost"],
        "nitro_carriers": usages["nitro"]["arcade"]["carriers"]["nitro_boost"],
        "nitro_entities": usages["nitro"]["arcade"]["entities"],
        "emp": {"instances": emp["instances"], "fields": emp["fields"],
                "objects": len(emp["objects"]),
                "gadget_classes": weapons["counts"]["gadget_classes"]},
        "battle_audio": {"events": len(w08["sources"]),
                         "wems": sum(s.get("wems") or 0 for s in w08["sources"]),
                         "dispo": w08["dispo"], "id": w08["id"]},
        "tune": tune,
        "card_items": card_behaviours(backlog),
        "ledger": {rid: {"dispo": r["dispo"], "why": r["why"]} for rid, r in ledger.items()},
        "decisions": {"D-2": "REOPENED 2026-11-06" in backlog,
                               "D-2_history": "(b) one hybrid car" in backlog,
                      "D-7": "every BmAK weapon in both battle and pursuit modes" in backlog},
        "backlog_d2": "one hybrid car" in backlog,
    }


# --------------------------------------------------------------------------- rows
def build_rows(F: dict) -> list[dict]:
    m, cam, tt, li = F["modes"], F["camera"], F["tankturn"], F["lights"]
    n = F["nitro"]
    emp, aud, tune = F["emp"], F["battle_audio"], F["tune"]
    std, boost = m["torque"]["StandardTorqueVSpeedCurve"], m["torque"]["BoostTorqueVSpeedCurve"]
    pts = ", ".join(f"{int(a)} -> {int(b)}" for a, b in m["curve_points"])
    rows: list[dict] = []

    def curve_text(c: dict) -> str:
        return ", ".join(f"{int(a)} -> {int(b)}" for a, b in c["points"])

    def add(**kw) -> None:
        kw.setdefault("compromise", "carried")
        rows.append(kw)

    # ------------------------------------------------------------------ MOD-1
    add(id="T-MD1", code="MOD-1", behaviour="afterburner",
        bmak=(f"`Batmobile_Booster` gadget: JC3's own nitro is the closest match - the donor's "
              f"`arcade.nitro_boost` carries torque x{int(n['torque_multiplier'])}, grip "
              f"x{int(n['grip_multiplier'])}, push {int(n['push_force']):,}, +{int(n['extra_top_speed'])} "
              f"km/h, {n['boost_blend_time']:g} s blend ({F['nitro_carriers']} of "
              f"{F['nitro_entities']} vehicles)"),
        jc3="`custom_land_global.arcade.nitro_boost` (live since test-091); values T-B2/T-B3",
        hybrid="one nitro, always on tap - the car has no pursuit gate to open it with",
        compromise="carried",
        pursuit="nitro boost, BmAK's afterburner",
        battle="the same boost (no BmAK battle-mode restriction is decoded)",
        dispo="next", confidence="decoded", verify="Q-2 A9: 0-100 with and without boost, A2 top speed",
        why=("the afterburner is JC3 nitro and already live; the hybrid needs no mode gate because "
             "nothing in MODES.json restricts the boost to one mode"))

    add(id="T-MD2", code="MOD-1", behaviour="Immobilizer (EMP missile)",
        bmak=(f"`RBatmobileEMPMissile` `Batmobile_EMP_Missile_Launcher` ({emp['instances']} "
              f"instances, {emp['fields']} fields) + `RBatmobileEMP` `Batmobile_EMP_Burst` (3 "
              f"instances, 36 fields, 12 offsets tagged: `DisableEnemyDuration` @2400, "
              f"`EMPImpulse` @2512 and `EMPVehicleImpulse` @2528 serialise **no value**, so the "
              f"duration is UNKNOWN on BmAK's own side too)"),
        jc3=("**closest chain, end to end**: `w618` missile clone for the launcher (T-WP4) -> the "
             "entity `CForcePulse` `EMP` on `truck_emp.ftune` (100 player/AI damage in 25 m held "
             "at full radius, flags `id:4912FC04` 0 / `id:AE6F7EFF` 1 / `id:CF4F7880` 1, "
             "`id:D3DDD766` -> `CMaterialEffectTable emp_flatbed_table`) -> the engine's own "
             "`CEMPWeapon` class (`.?AVCEMPWeapon@@`, ships as `w702_emp` id 702 / type 6 / 500 "
             "damage / 50 m and `w503_turret_emp` 503 / type 2 / 500 / 750 m) as the disable "
             "writer; `is_disabled_by_emp` (exe 0x24EA080) is engine vocabulary with 0 asset "
             "bindings"),
        hybrid=("carried: one car, one EMP - the launcher, the pulse and the disable chain are "
                "mode-independent (D-7), so nothing in this row is mode-only. BmAK-exact: no - "
                "the disable's writer is B-18's probe build"),
        compromise="carried",
        pursuit="launcher + `CForcePulse` + the `CEMPWeapon` disable chain",
        battle="the same (no mode gate: the EMP is not a mode behaviour)",
        dispo="next", confidence="decoded",
        verify="Q-EMP-1…4 (B-18): does the engine's `w702_emp` stall a stock car, does the pulse "
               "alone, is a `CEMPWeapon` accepted in a car's slot, and how long the state lasts",
        why=("moved off `blocked`: the effect half is decoded (missile tune + pulse + flags + "
             "material table) and the one missing link - the writer of `is_disabled_by_emp` - is "
             "BUILD card B-18 with probes Q-EMP-1…4 (report "
             "`tmp/freebuff/reports/immobiliser-and-emp-trigger.md` §7-§8). The EMP is not "
             "mode-dependent, so the hybrid carries it; BmAK-exact: no"))

    add(id="T-MD3", code="MOD-1", behaviour="ram immunity",
        bmak="BmAK ramming never damages the Batmobile (G1-14 damage rules)",
        jc3="entity `impact_damage_factor` 0 (T-DM8, `keep`); a declared switch, not a value",
        hybrid="one switch, always on - ramming is mode-independent",
        compromise="carried",
        pursuit="no ram damage", battle="no ram damage",
        dispo="keep", confidence="decoded",
        verify="Q-3 #1: ram a wall and cars at 40/80 km/h - no health loss",
        why="the immunity is an entity switch with no mode member, so one car carries it as-is")

    add(id="T-MD4", code="MOD-1", behaviour="high speed (standard/boost torque curve)",
        bmak=("`StandardTorqueVSpeedCurve` (G1 `objects.jsonl`, "
              f"{std['count']} points, identical in all {len(std['packages'])} packages): "
              f"{curve_text(std)}; `BoostTorqueVSpeedCurve` ({boost['count']} points, same in all "
              f"{len(boost['packages'])}): {curve_text(boost)}. Both live on "
              "`RVehicleSimBatmobile`, not in a `MODES.json` mode family, so G1-21's record does not "
              "declare them; x is cm/s by the UE3 convention, y has no documented scale and is "
              "carried raw"),
        jc3="T-E1 (rpm band), T-E3 (torque factors), T-A1/T-B2 (top speed, boost)",
        hybrid="one speed profile for both modes",
        compromise="carried",
        pursuit="the fast profile", battle="`BattleModeVSpeedCurve` would cap it (row T-MD5)",
        dispo="keep", confidence="decoded",
        verify="Q-2 A1/A2: 0-100 and top speed with the boost on/off",
        why=("pursuit speed rests on BmAK's own standard/boost torque curve, read from the G1 "
             "object stream, and the hybrid has one engine profile for both modes; the battle "
             "speed cap is T-MD5's omission"))

    # ------------------------------------------------------------------ MOD-2
    add(id="T-MD5", code="MOD-2", behaviour="top speed curve",
        bmak=(f"`BattleModeVSpeedCurve` `FInterpCurveFloat`, {m['curve_count']} points "
              f"(x cm/s by convention, y raw: the record's unit is `{m['curve_unit']}` on the "
              f"`{m['curve_unit_basis']}` basis, so no percent/factor scale is established): {pts}; "
              f"identical in all four packages = {m['curve_same']}"),
        jc3=("no JC3 member scales top speed by a mode: the engine curve is torque-vs-rpm (T-E3), "
             "the boost is a separate arcade block (T-B2), and the only second value set is another "
             "entity (`arcade.nitro_boost` = multipliers + `extra_top_speed`; "
             "`mode-switch-carriers.md` §2.4/§2.5)"),
        hybrid=("the battle variant's own `arcade`/`CustomLandGlobal` values (one set per entity); "
                "the 3 curve points stay raw because no member takes a curve"),
        compromise="omitted",
        pursuit="uncapped (T-A1/T-B2)",
        battle=(f"capped by the curve - at {int(m['curve_points'][1][0])} cm/s the curve's out "
                f"value is {int(m['curve_points'][1][1])} (unit undocumented, carried raw)"),
        dispo="blocked", confidence="decoded",
        verify="Q-2 A2: top speed in the delivered car - there is no battle cap to observe",
        why=("re-opened by D-2 on 2026-11-06: a hybrid cannot hold a second speed curve, the battle "
             "entity can - the row waits on D-2's re-resolution to two variants (B-12) and on the "
             "runtime swap that is UNKNOWN (`mode-switch-carriers.md` §7 U1)"))

    add(id="T-MD6", code="MOD-2", behaviour="low top speed (turning-mode cap)",
        bmak=(f"`TurningModeMaxSpeed` {int(m['turning_cms'])} cm/s = **{m['turning_kmh']} km/h**, "
              f"with `BattleModeThrottleSpeed` {m['drive']['BattleModeThrottleSpeed']} "
              f"(unit undocumented, carried raw)"),
        jc3=("no turning-mode cap exists in the fleet vocabulary (no member, `VOCABULARY.md`); the "
             "nearest speed members are `vehicle_misc.official_top_speed` (T-E5), "
             "`arcade.nitro_boost.extra_top_speed` (T-B2) and "
             "`land_aerodynamics.top_speed_drag_coefficient` (T-A3), none of them a cap"),
        hybrid=(f"the battle variant holds its own speed values, so {m['turning_kmh']} km/h is a "
                f"per-entity constant - **which** member caps speed is UNKNOWN: "
                f"`mode-switch-carriers.md` §6 reads `LandGlobal`, §2.7 finds no cap member"),
        compromise="omitted",
        pursuit="no cap", battle=f"{m['turning_kmh']} km/h",
        dispo="blocked", confidence="derived",
        verify="Q-2 A2: the car is not speed-limited in the delivered build",
        why=("the cap needs a second value set and a variant supplies one, but no decoded member is "
             "a speed cap - the row waits on D-2 and on B-12's read of the battle copy's modules"))

    add(id="T-MD7", code="MOD-2", behaviour="steering and drive factors",
        bmak=(f"`BattleModeDriveForceFactor` {m['drive']['BattleModeDriveForceFactor']}, "
              f"`BattleModeLatSlipScale` {m['drive']['BattleModeLatSlipScale']}, "
              f"`BattleModeLongSlipScale` {m['drive']['BattleModeLongSlipScale']}, "
              f"`BattleModeSteerAngleFactor` {m['drive']['BattleModeSteerAngleFactor']}, "
              f"`BattleModeTrailingSteerFactorMoving` "
              f"{m['drive']['BattleModeTrailingSteerFactorMoving']}, "
              f"`BattleModeDrivingForceZOffset` "
              f"{m['drive']['BattleModeDrivingForceZOffset']} cm"),
        jc3=("none of these is a mode member in JC3: the single-car equivalents are T-M1 "
             "(`rigid_body.mass`), T-S1 (suspension), T-E3 (torque factors) and the steering rows "
             "(T-ST1 `land_steering.*`); none is mode-keyed"),
        hybrid=("the battle variant's own `land_steering` + torque set: "
                "`BattleModeSteerAngleFactor` 1 leaves the steering angle unchanged and four factors "
                "land on existing members; the two slip scales (0.75 / 1.25) have no decoded member "
                "(partial)"),
        compromise="omitted",
        pursuit="T-E3/T-ST1 values", battle="the same values x the battle factors above",
        dispo="blocked", confidence="decoded",
        verify="Q-2 A3/A4: the car corners and steers as the single set predicts",
        why=("four of the six factors land on the battle entity's own handling modules; the two slip "
             "scales have no member on either side, so the variant carries a partial set - the row "
             "waits on D-2 and on the runtime swap"))

    add(id="T-MD8", code="MOD-2", behaviour="turn on the spot",
        bmak=(f"`TurnOnSpotFrontTorqueFactor` {m['pivot']['TurnOnSpotFrontTorqueFactor']}, "
              f"`TurnOnSpotRearTorqueFactor` {m['pivot']['TurnOnSpotRearTorqueFactor']}, "
              f"`TurnOnSpotModeEngineBrakingFactor` "
              f"{m['pivot']['TurnOnSpotModeEngineBrakingFactor']}, "
              f"`BattleModeTurnOnSpotTorqueFactor` "
              f"{m['pivot']['BattleModeTurnOnSpotTorqueFactor']}"),
        jc3=(f"none - G2-21: {tt['candidates']} candidates refuted, {tt['fleet_types']} module "
             f"types ({tt['tank_types']} on the tanks, {tt['tank_only']} tank-only), "
             f"{tt['unique_values']} tank-unique values with {tt['driving_hits']} in a driving "
             f"module; the pivot is native code keyed to the vehicle"),
        hybrid=("no pivot in either variant: G2-21 refuted the candidates and found "
                f"{tt['tank_only']} tank-only driving members, and a second entity does not create one"),
        compromise="omitted",
        pursuit="none", battle="pivot on the spot",
        dispo="blocked", confidence="decoded",
        verify="Q-1 #4: no pivot on a stationary car (expected absence)",
        why=("G2-21 proved the requirement has no data carrier and a second variant does not change "
             "that, so the pivot stays a named omission in both variants and the row waits on a "
             "native mechanism"))

    add(id="T-MD9", code="MOD-2", behaviour="turret weapons",
        bmak=(f"turret and cannon parts with the {F['emp']['gadget_classes']} BmAK weapon classes "
              f"(G1-08)"),
        jc3=("T-12's turret/cannon part angles carry the aim; T-11's clones carry the weapons - "
             "D-7 resolved that every weapon is available in both modes"),
        hybrid="carried: all weapons on the one car, no mode gate",
        compromise="carried",
        pursuit="weapons available (D-7)", battle="the same weapons",
        dispo="next", confidence="decoded",
        verify="Q-1 #4/#5: turret follows the camera; each weapon fires from its muzzle",
        why=("D-7 removed the per-mode weapon split, so the battle half needs no second row: the "
             "weapons are T-11's and the turret is T-12's"))

    add(id="T-MD10", code="MOD-2", behaviour="armour reduction",
        bmak=(f"`ArmourModeDamageReduction` = **{m['armour']['value']}** ({m['armour']['unit']}), "
              f"identical on the three packages that serialise it "
              f"({', '.join(PKG.get(p, p) for p in m['armour']['packages'])})"),
        jc3="`VehicleDamage` channels + the private health module (T-14); no mode member",
        hybrid="carried: the shipped value is 0, so there is no reduction to carry",
        compromise="carried",
        pursuit="no reduction", battle="no reduction (0 in the files)",
        dispo="keep", confidence="decoded",
        verify="Q-3 #2: hits-to-kill matches T-14's single profile",
        why=("the requirement assumes armour drops in battle mode, but every shipped archetype "
             "stores 0, so the hybrid's one armour profile is already the BmAK value"))

    add(id="T-MD11", code="MOD-2", behaviour="battle camera",
        bmak=(f"`BattleModeCamFOV` {cam['BattleModeCamFOV']:g}, "
              f"`BattleModeWinchCamFOV` {cam['BattleModeWinchCamFOV']:g}, "
              f"`AntiPersonelBattleModeCamFOV` {cam['AntiPersonelBattleModeCamFOV']:g}; "
              f"`BattleModeCamConfig` {cam['config_fields']} fields "
              f"(`MinFreeCameraDistance`/`MaxFreeCameraDistance` "
              f"{cam['config_min_distance']:g}/{cam['config_max_distance']:g} cm, read by name)"),
        jc3=(f"one per-entity `.ctune` (CAM-1, test-091: {tune['back_m']:.2f} m back, "
             f"{tune['up_m']:.2f} m up, FOV {tune['fov_lo']:g}-{tune['fov_hi']:g} as re-read from the "
             f"written file); the spring/distance fields have no unit bridge (T-CAM9 blocked), the "
             f"FOV does"),
        hybrid=(f"inside band: FOV {cam['BattleModeCamFOV']:g} lies in the tune's "
                f"{tune['fov_lo']:g}-{tune['fov_hi']:g}, so no value changes and only the mode switch "
                f"is missing"),
        compromise="inside band",
        pursuit="the drive tune", battle=f"FOV {cam['BattleModeCamFOV']:g} + the battle config",
        dispo="keep", confidence="derived",
        verify="Q-2 A15: the chase camera matches the decoded composition; no battle framing appears",
        why=("T-CAM10 named a second `.ctune` per variant as the carrier and a hybrid has one tune; "
             "the battle FOV falls inside the band the tune already spans"))

    add(id="T-MD12", code="MOD-2", behaviour="battle lights",
        bmak=(f"{len(li['battle_rows'])} `VEHLT_BattleModeLight` entries (T-L17-T-L20): spotlight, "
              f"two heads, one wheel arch"),
        jc3=(f"the fleet's light vocabulary is {li['behaviour_count']} behaviours "
             f"({', '.join(li['behaviours'])}) with {len(li['battle_behaviour'])} battle value, so "
             f"T-18 maps the battle lamps onto `HeadLight`: {', '.join(li['battle_rows'])}"),
        hybrid="carried as headlights: the battle lamps come on with the lights, not on a mode",
        compromise="carried",
        pursuit="the drive lights", battle="the battle lamps lit",
        dispo="next", confidence="decoded",
        verify="Q-1 #7: the battle heads/arch glow with the lights on (and cannot be triggered alone)",
        why=("the battle light type maps onto JC3's `HeadLight` behaviour because no battle "
             "behaviour exists in the fleet's nine; that is the compromise recorded here"))

    add(id="T-MD13", code="MOD-2", behaviour="transformation stance",
        bmak=(f"`TransformationTurnTorqueFactor` {m['transform']['TransformationTurnTorqueFactor']}, "
              f"`TransformationTurnDecelTorqueFactor` "
              f"{m['transform']['TransformationTurnDecelTorqueFactor']}, "
              f"`TransformationAnimNode` {m['transform']['TransformationAnimNode']}"),
        jc3=("the static pose is T-12's part angles (turret, cannon, fins, hatches), and a JC3 pose "
             "is set by the hinged-part table (`all_hinged_part_properties` -> a `*_T` driving "
             "variable, `mode-switch-carriers.md` §2.1); no JC3 anim node drives a transformation "
             f"({m['transform_anim_packages']} `TransformationAnimNode` values in the files)"),
        hybrid=("the battle variant's parts hold the deployed pose as part angles; the animated "
                "transition stays UNKNOWN (`TransformationAnimNode` has no analogue)"),
        compromise="omitted",
        pursuit="parts parked", battle="the battle pose (T-12 angles)",
        dispo="blocked", confidence="decoded",
        verify="Q-1 #4: no transformation animation when the weapons come out",
        why=("re-opened by D-2 on 2026-11-06: the pose is a per-entity constant the battle variant "
             "can hold, the animation is not - the row waits on D-2 and on B-12"))

    add(id="T-MD14", code="MOD-2", behaviour="battle audio",
        bmak=(f"`TransformationReverseDirectionIntoPursuitModeSound` "
              f"{m['sounds']['TransformationReverseDirectionIntoPursuitModeSound']} and "
              f"`TransformationReverseDirectionIntoBattleModeSound` "
              f"{m['sounds']['TransformationReverseDirectionIntoBattleModeSound']} (`AkEvent` refs; "
              f"they differ per package, so every value is printed)"),
        jc3=(f"T-16 row {aud['id']} is `{aud['dispo']}`: the donor's usage names hold no "
             f"mode/battle/transform usage, and its only performance-state usage is `EngineNitro` "
             f"(4197885156, 18 vehicles, 307 objects) - `battle-audio-switch-event.md` §2/§4"),
        hybrid=("the battle variant can carry its own graph + usage and the `BML_Battlemode` set "
                "(7 events / 24 media) with `BML_Batmobile`'s 32 battle events; the entry/exit sting "
                "still needs a transition, not a variant"),
        compromise="omitted",
        pursuit="engine/drive audio (T-16's slots)",
        battle=f"`Play_BattleMode_In/Out*` {aud['events']} events / {aud['wems']} WEMs",
        dispo="blocked", confidence="decoded",
        verify="Q-1 #8: no transformation sound when the car changes mode (there is no change)",
        why=(f"D-2's reopening gives T-16's {aud['events']} battle events a second entity to live "
             f"on, but a new `Usage` hash still needs a consumer (U1) and swapping entities is not an "
             f"audio transition, so the row stays blocked"))

    add(id="T-MD15", code="MOD-2", behaviour="the hybrid itself (D-2)",
        bmak="BmAK ships one car that transforms between pursuit and battle in place",
        jc3=("one entity, one Rebel Drop entry today (`B-12` is `todo: D-2 reopened`, `B-13` ships "
             "a single item); the mode was the car's identity under D-2's 2026-10-28 answer, which "
             "is withdrawn"),
        hybrid="carried: the hybrid is the decision, and every row above is its consequence",
        compromise="carried",
        pursuit="the same car", battle="the same car",
        dispo="next", confidence="decoded",
        verify="Q-1 #1: one drop entry, one car",
        why=("D-2's 2026-10-28 answer chose a single hybrid entry, so the variant table has one row "
             "and the split's values are recorded per row rather than built; D-2 was reopened on "
             "2026-11-06, so whether this row survives is B-12's outcome"))
    return rows


def cells(row: dict) -> list[str]:
    return [row["id"], row["code"], row["behaviour"], row["bmak"], row["jc3"],
            row["hybrid"], row["confidence"], row["verify"]]


# --------------------------------------------------------------------------- payload
def build_payload() -> tuple[dict, list[str]]:
    F = gather()
    rows = build_rows(F)
    problems: list[str] = []
    for row in rows:
        row["cells"] = cells(row)
        if row["compromise"] not in COMPROMISES:
            problems.append(f"{row['id']}: compromise {row['compromise']!r} not in {COMPROMISES}")
        if row["dispo"] not in ("next", "keep", "epe", "blocked", "out"):
            problems.append(f"{row['id']}: disposition {row['dispo']!r}")

    m, cam, tt, li = F["modes"], F["camera"], F["tankturn"], F["lights"]
    tune = F["tune"]
    # ---- derivations the cells rest on -------------------------------------------------
    if m["curve_points"] != [[0.0, 60.0], [600.0, 40.0], [1200.0, 30.0]]:
        problems.append(f"BattleModeVSpeedCurve points changed: {m['curve_points']}")
    if not m["curve_same"]:
        problems.append("BattleModeVSpeedCurve is no longer identical in all four packages")
    # the G1 object stream is the torque curve's source; cross-check it against MODES.json
    std = m["torque"]["StandardTorqueVSpeedCurve"]
    boost = m["torque"]["BoostTorqueVSpeedCurve"]
    if std["points"] != [[-1500.0, 0.0], [-300.0, 200.0], [0.0, 200.0], [750.0, 170.0],
                         [1600.0, 150.0], [2100.0, 105.0]]:
        problems.append(f"StandardTorqueVSpeedCurve changed: {std['points']}")
    if boost["count"] != 7 or len(boost["packages"]) != 4:
        problems.append(f"BoostTorqueVSpeedCurve: {boost['count']} points over "
                        f"{len(boost['packages'])} packages")
    if not std["same"] or not boost["same"]:
        problems.append("a torque curve differs between the four packages")
    if m["curve_packages_read"] != 4:
        problems.append(f"objects.jsonl yielded {m['curve_packages_read']} SimulationModel objects")
    if m["curves"]["BattleModeVSpeedCurve"]["points"] != m["curve_points"]:
        problems.append("objects.jsonl and MODES.json disagree on BattleModeVSpeedCurve")
    if m["turning_cms"] != 600.0:
        problems.append(f"TurningModeMaxSpeed is {m['turning_cms']}, not 600 cm/s")
    if m["turning_kmh"] != 21.6:
        problems.append(f"the cm/s -> km/h conversion gives {m['turning_kmh']}, not 21.6")
    if m["armour"]["value"] != "0":
        problems.append(f"ArmourModeDamageReduction is {m['armour']['value']}, not 0")
    if m["pivot"]["TurnOnSpotRearTorqueFactor"] != "-0.8":
        problems.append("TurnOnSpotRearTorqueFactor changed")
    if li["battle_behaviour"]:
        problems.append(f"the fleet has a battle light behaviour after all: {li['battle_behaviour']}")
    if len(li["battle_rows"]) != 4:
        problems.append(f"{len(li['battle_rows'])} battle light rows, expected 4")
    if cam["BattleModeCamFOV"] != 60.0:
        problems.append(f"BattleModeCamFOV is {cam['BattleModeCamFOV']}, not 60")
    if not (tune["fov_lo"] <= cam["BattleModeCamFOV"] <= tune["fov_hi"]):
        problems.append(f"the battle FOV no longer sits inside the delivered tune's "
                        f"{tune['fov_lo']:g}-{tune['fov_hi']:g} band")
    if tune["readback_ok"] != tune["readback_expected"]:
        problems.append(f"CAM_TUNE.json re-read {tune['readback_ok']} of "
                        f"{tune['readback_expected']} values")
    if not (cam["config_min_distance"] and cam["config_max_distance"]):
        problems.append("BattleModeCamConfig's named distance fields are missing or zero")
    if F["emp"]["instances"] < 1 or F["emp"]["fields"] < 1:
        problems.append(f"WEAPONS.json RBatmobileEMPMissile: {F['emp']}")
    if F["nitro_entities"] < 1 or not F["battle_audio"]["events"] or not F["battle_audio"]["wems"]:
        problems.append(f"USAGES/audio counts empty: {F['nitro_entities']}, {F['battle_audio']}")
    if not tt["pivot_named_omission"]:
        problems.append("TANKTURN.md no longer states the pivot omission")
    if li["behaviour_count"] != 9:
        problems.append(f"the light vocabulary has {li['behaviour_count']} behaviours, not 9")
    if not F["decisions"]["D-2"] or not F["decisions"]["D-2_history"] or not F["decisions"]["D-7"]:
        problems.append("a decision this card rests on is no longer recorded in §11 "
                        "(D-2 must read REOPENED and keep its 2026-10-28 answer as history)")
    for rid, want in (("T-B2", "next"), ("T-B3", "next"), ("T-DM8", "keep"), ("T-M1", "edit"),
                      ("T-E1", "edit"), ("T-E3", "edit"), ("T-WP4", "blocked"),
                      ("T-WP11", "keep")):
        got = (F["ledger"].get(rid) or {}).get("dispo")
        if got != want:
            problems.append(f"ledger {rid} is {got}, the row cites {want}")

    covered2 = sorted({r["behaviour"] for r in rows if r["code"] == "MOD-2"})
    covered1 = sorted({r["behaviour"] for r in rows if r["code"] == "MOD-1"})
    for b in MOD2_BEHAVIOURS:
        if b not in covered2:
            problems.append(f"MOD-2 behaviour {b!r} has no row")
    for b in MOD1_BEHAVIOURS:
        if b not in covered1:
            problems.append(f"MOD-1 behaviour {b!r} has no row")

    # ---- the card owns the coverage list (not this script) -----------------------------
    items = F["card_items"]
    if not items:
        problems.append("the T-15 card's Do: list parsed empty")
    for item in items:
        if item not in CARD_ROWS:
            problems.append(f"card item {item!r} has no row mapped in CARD_ROWS")
    for item, rids in CARD_ROWS.items():
        if item not in items:
            problems.append(f"CARD_ROWS maps {item!r}, which the card no longer lists")
        for rid in rids:
            if rid not in {r["id"] for r in rows}:
                problems.append(f"card item {item!r} maps {rid}, which is not a row")

    # ---- R4: the class column must discriminate, and be a real class ------------------
    classes = {r["confidence"] for r in rows}
    for c in classes:
        if c not in CONFIDENCES:
            problems.append(f"confidence {c!r} is not an R4 class {CONFIDENCES}")
    if classes == {"decoded"}:
        problems.append("every row claims `decoded`: the confidence column carries no information")

    variants = {
        "schema": 1,
        "generated_by": "t11_modes.py",
        "card": "T-15 (GRAB_BACKLOG.md §7)",
        "decision": {"D-2": "REOPENED 2026-11-06: two variants needed, awaiting the operator "
                              "(was resolved 2026-10-28 to (b) one hybrid car)",
                     "D-7": "resolved 2026-10-28 (user): every BmAK weapon in both modes",
                     "source": "GRAB_BACKLOG.md §11"},
        "variants": [{"id": "hybrid", "drop_entries": 1, "entities": 1, "mode_switch": None,
                      "B-12": "todo: D-2 reopened", "B-13": "ships the single entry",
                      "rows": len(rows)}],
        "split": [{"row": r["id"], "code": r["code"], "behaviour": r["behaviour"],
                   "pursuit": r["pursuit"], "battle": r["battle"], "hybrid": r["hybrid"],
                   "compromise": r["compromise"], "disposition": r["dispo"]} for r in rows],
        "counts": {"rows": len(rows),
                   "MOD-1": sum(1 for r in rows if r["code"] == "MOD-1"),
                   "MOD-2": sum(1 for r in rows if r["code"] == "MOD-2"),
                   "compromise": {c: sum(1 for r in rows if r["compromise"] == c)
                                  for c in COMPROMISES},
                   "dispo": {d: sum(1 for r in rows if r["dispo"] == d)
                             for d in ("next", "keep", "epe", "blocked", "out")},
                   "by_compromise_delta": sorted({r["compromise"] for r in rows})},
        "facts": {"modes": m, "camera": cam, "tankturn": tt, "lights": li,
                  "nitro": {k: n for k, n in F["nitro"].items()},
                  "nitro_carriers": F["nitro_carriers"],
                  "nitro_entities": F["nitro_entities"], "emp": F["emp"],
                  "battle_audio": F["battle_audio"], "tune": F["tune"],
                  "card_items": F["card_items"]},
        "rows": rows,
    }
    return {"doc": rows, "variants": variants}, problems


# --------------------------------------------------------------------------- document
def read_doc(payload: dict) -> list[str]:
    rows = payload["doc"]
    v = payload["variants"]
    c = v["counts"]
    m, cam, li = v["facts"]["modes"], v["facts"]["camera"], v["facts"]["lights"]
    tune = v["facts"]["tune"]
    std = m["torque"]["StandardTorqueVSpeedCurve"]
    L: list[str] = []
    a = L.append
    a("# Modes translation (T-15)")
    a("")
    a("Generated by `Tools/scripts/t11_modes.py` from G1-21's `MODES.json` and `CAMERA.json`, the G1")
    a("object stream `objects.jsonl` (the sim class's curves), G1-08's `WEAPONS.json`, G2-21's")
    a("`TANKTURN.json`, G2-33's `LIGHT_SYSTEM.json`, G2-22/23's `USAGES.json`, T-16's")
    a("`t12_audio_map.json`, T-18's `t14_lights.json`, CAM-1's read-back")
    a("`Working/Camera/CAM_TUNE.json`, the ledger and the T-15 card's own `Do:` list; `--check`")
    a("re-reads all of them, re-derives this file and `t11_variants.json`, compares both")
    a("byte-for-byte and cross-checks `T_ROWS.jsonl`.")
    a("")
    a("**D-2 was reopened on 2026-11-06: (b) one hybrid car is withdrawn.** BmAK has two modes and")
    a("the single car cannot carry T-MD5, T-MD6, T-MD7, T-MD8, T-MD13 or T-MD14 - those six rows are")
    a("`blocked` and card B-12 carries the two-variant preconditions. What follows is the **one-hybrid")
    a("record**: one row set with the compromise declared per row, i.e. what the build holds until a")
    a("second entity exists. The variant table (`t11_variants.json`) keeps both halves anyway: for")
    a("every row it records what the pursuit cars would have used, what the battle car would have")
    a("used, what the single car gets, and which of the three compromise kinds that is. B-12's")
    a("precondition 2 re-runs this tool as **two** sets.")
    a("")
    a("| item | value |")
    a("|---|---|")
    a(f"| rows | **{c['rows']}** - MOD-1 {c['MOD-1']}, MOD-2 {c['MOD-2']} |")
    a(f"| compromises | " + ", ".join(f"`{k}` {n}" for k, n in c["compromise"].items()) + " |")
    a(f"| dispositions | " + ", ".join(f"`{k}` {n}" for k, n in c["dispo"].items() if n) + " |")
    a(f"| BmAK record | {m['declared']} declared mode fields, {m['serialised']} serialised, "
      f"{m['not_serialised']} declared but absent from every package |")
    a(f"| battle FOV | {cam['BattleModeCamFOV']:g} deg (`BattleModeCamFOV`, `{cam['class']}`) |")
    a(f"| decision | D-2 **reopened** (two variants needed) · D-7 every weapon in both modes |")
    a("")
    a("## 1. The three compromise kinds")
    a("")
    a("A hybrid is not \"both modes at once\": it is one car that has to pick a value for every")
    a("mode-only behaviour. Each row declares which pick it made.")
    a("")
    a("| kind | meaning | rows |")
    a("|---|---|---:|")
    meaning = {
        "carried": "the single car carries the value unchanged - either the behaviour is "
                   "mode-independent or JC3 is already always-on",
        "inside band": "the battle value falls inside the band the one car already holds, so no "
                       "value changes; only the mode *switch* is missing",
        "omitted": "the requirement needs a member or mode switch JC3 does not have: a named "
                   "omission that keeps the BmAK numbers on the page",
    }
    for k in COMPROMISES:
        a(f"| `{k}` | {meaning[k]} | {c['compromise'][k]} |")
    a("")
    a("## 2. The rows")
    a("")
    a("Cells: id, code, behaviour, BmAK source, JC3 carrier, what the hybrid gets, confidence (R4")
    a("classes), verify (a §9b probe that can fail). The disposition of each row is in")
    a("`t11_variants.json` and in the ledger.")
    a("")
    a("| id | code | behaviour | BmAK source | JC3 carrier | hybrid value | confidence | verify |")
    a("|---|---|---|---|---|---|---|---|")
    for r in rows:
        a("| " + " | ".join(r["cells"]) + " |")
    a("")
    a("## 3. The BmAK numbers, and where each came from")
    a("")
    absent = ", ".join(PKG.get(p, p) for p in m["armour"]["absent"])
    intro = " ".join([
        f"The four packages declare the same {m['declared']} mode fields, but they do **not** carry",
        f"the same values: {m['serialised']} of them are serialised and {m['not_serialised']} are",
        "absent from every package, and of the",
        f"{m['serialised']} serialised only **{m['same_in_all_four']} are identical on all four**.",
        f"The other {len(m['differing'])} differ, so a number quoted without its package set is only",
        "the value the packages that carry the field agree on. The fields that differ are",
        ", ".join(f"`{n}`" for n in m["differing"]) + ".",
        f"`ArmourModeDamageReduction` has no tag in {absent}, so its row prints the per-package",
        "values.",
        f"A declared field that no package serialises is `UNKNOWN`, not zero:",
        f"{m['not_serialised']} of the {m['declared']} are in that state and are named where a row",
        "depends on them."])
    for line in textwrap.wrap(intro, width=95, break_long_words=False, break_on_hyphens=False):
        a(line)
    a("")
    a("| field | value | unit | row |")
    a("|---|---|---|---|")
    for name, rid in (
        ("BattleModeVSpeedCurve", "T-MD5"),
        ("TurningModeMaxSpeed", "T-MD6"),
        ("BattleModeDriveForceFactor", "T-MD7"),
        ("BattleModeLatSlipScale", "T-MD7"),
        ("BattleModeLongSlipScale", "T-MD7"),
        ("TurnOnSpotFrontTorqueFactor", "T-MD8"),
        ("TurnOnSpotRearTorqueFactor", "T-MD8"),
        ("ArmourModeDamageReduction", "T-MD10"),
        ("TransformationTurnTorqueFactor", "T-MD13"),
        ("TransformationTurnDecelTorqueFactor", "T-MD13"),
        ("TransformationAnimNode", "T-MD13"),
        ("BattleModeCamFOV", "T-MD11"),
    ):
        unit = f"{m['units'][name]['unit']} ({m['units'][name]['basis']} basis)"
        if name.startswith("BattleModeCamFOV"):
            value = f"{cam['BattleModeCamFOV']:g}"
        elif name == "BattleModeVSpeedCurve":
            value = ", ".join(f"{int(x)} -> {int(y)}" for x, y in m["curve_points"])
        elif name == "TurningModeMaxSpeed":
            value = f"{int(m['turning_cms'])} = {m['turning_kmh']} km/h"
        elif name.startswith("TurnOnSpot"):
            value = m["pivot"][name]
        elif name.startswith("Transformation"):
            value = m["transform"][name]
        elif name == "ArmourModeDamageReduction":
            value = m["armour"]["value"]
        else:
            value = m["drive"][name]
        a(f"| `{name}` | {value} | {unit} | `{rid}` |")
    a("")
    camera_para = " ".join([
        "The three camera numbers that matter for the hybrid come from the camera class, not the",
        f"vehicle archetype: `BattleModeCamFOV` {cam['BattleModeCamFOV']:g},",
        f"`BattleModeWinchCamFOV` {cam['BattleModeWinchCamFOV']:g} and",
        f"`AntiPersonelBattleModeCamFOV` {cam['AntiPersonelBattleModeCamFOV']:g}",
        f"(`{cam['class']}`), while `BattleModeCamConfig` carries {cam['config_fields']} fields",
        "including `MinFreeCameraDistance`/`MaxFreeCameraDistance`",
        f"{cam['config_min_distance']:g}/{cam['config_max_distance']:g} cm, looked up by name."])
    for line in textwrap.wrap(camera_para, width=95, break_long_words=False,
                              break_on_hyphens=False):
        a(line)
    a("")
    a("## 4. What the split would have carried (the variant table)")
    a("")
    a("`t11_variants.json` holds this table as data: one variant (`hybrid`) and, per row, the")
    a("pursuit value, the battle value and the hybrid compromise.")
    a("")
    a("| row | behaviour | pursuit would carry | battle would carry | hybrid | kind |")
    a("|---|---|---|---|---|---|")
    for s in v["split"]:
        a(f"| `{s['row']}` | {s['behaviour']} | {s['pursuit']} | {s['battle']} | "
          f"{s['hybrid']} | `{s['compromise']}` |")
    a("")
    a("## 5. Named omissions and blocked rows")
    a("")
    a("| row | disposition | what is missing | what carries it instead |")
    a("|---|---|---|---|")
    instead = {
        "T-MD2": "the EMP is `carried` since 2026-11-06: the launcher, the pulse and the "
                  "`CEMPWeapon` disable chain are mode-independent; the missing writer is B-18",
        "T-MD5": "the battle variant's own top-speed values (B-12); the 3 curve points stay raw",
        "T-MD6": "the battle variant's own speed values; which member caps speed is UNKNOWN (B-12)",
        "T-MD7": "the battle variant's own `land_steering`/torque set; the two slip scales have no "
                  "member",
        "T-MD8": "nothing; G2-21 proved the pivot has no data carrier at all, in either variant",
        "T-MD13": "the battle variant's parts hold the end pose; the animation has no carrier",
        "T-MD14": "T-16's drive-audio slots; the 32 battle events need a usage consumer",
    }
    for r in rows:
        if r["dispo"] in ("out", "blocked"):
            a(f"| `{r['id']}` | `{r['dispo']}` | {r['why']} | {instead.get(r['id'], '-')} |")
    a("")
    a("## 6. UNKNOWNs and limits")
    a("")

    def bullet(text: str) -> None:
        for i, line in enumerate(textwrap.wrap(text, width=95, break_long_words=False,
                                               break_on_hyphens=False)):
            a(("- " if i == 0 else "  ") + line)

    bullet(" ".join([
        f"**`StandardTorqueVSpeedCurve` is not one of the {m['declared']} `MODES.json` fields** - it",
        "lives on `RVehicleSimBatmobile`, outside the mode families G1-21 records - so this doc",
        f"reads it from the G1 object stream instead: {std['count']} points, identical in all",
        f"{len(std['packages'])} packages (row `T-MD4`). That is a **record boundary, not an",
        "absence**: the values exist and are quoted in §3."]))
    bullet(" ".join([
        "**The curves' y axis has no documented scale.** `BattleModeVSpeedCurve` is recorded with",
        f"the unit string \"{m['curve_unit']}\" on the \"{m['curve_unit_basis']}\" basis, and the",
        "torque curves carry",
        "no unit declaration at all, so the out values are printed raw:",
        "/".join(str(int(y)) for _, y in m["curve_points"]), "for the battle curve and",
        "/".join(str(int(y)) for _, y in std["points"]),
        "for the standard torque curve, and neither set is asserted to be a factor, a percentage",
        "or a multiplier. Nothing is rescaled."]))
    bullet(" ".join([
        f"**{m['not_serialised']} declared mode fields carry no value** in any package",
        "(`TransformationAnimNode`, `BattleModeMaxSpeed`, `BattleModeSteerBias`, the whole",
        "`Strafe*` family, the battle camera config struct on the *vehicle* class, and others). A",
        "field that declares without serialising is `UNKNOWN`: the engine's or BMScript's default",
        "would run."]))
    bullet(" ".join([
        f"**`ArmourModeDamageReduction` is {m['armour']['value']} on the",
        f"{len(m['armour']['packages'])} packages that serialise it** and its unit is undocumented;",
        "the row therefore carries *no* reduction. A non-zero value would need its own unit",
        "bridge - none exists."]))
    bullet(" ".join([
        f"**`BattleModeThrottleSpeed` ({m['drive']['BattleModeThrottleSpeed']}) is carried raw**:",
        "the field's own unit is undocumented, so nothing is converted from it."]))
    bullet(" ".join([
        "**The battle camera's spring/distance fields are not translatable**: the decoded",
        "composition is in centimetres with no unit bridge to a `.ctune` (T-CAM9 stays blocked);",
        f"only the FOV has a bridge, and {cam['BattleModeCamFOV']:g} deg already sits inside the",
        f"delivered {tune['fov_lo']:g}-{tune['fov_hi']:g} deg band."]))
    bullet(" ".join([
        "**No battle light behaviour exists.** The fleet's",
        f"{li['behaviour_count']} light behaviours have none, so T-18 maps BmAK's",
        "`VEHLT_BattleModeLight` lamps onto `HeadLight`: they light with the headlights."]))
    bullet("**No game was launched** (R6); every `verify` cell is a §9b probe that can fail.")
    a("")
    a("## 7. Outputs and regeneration")
    a("")
    a("| path | what it is |")
    a("|---|---|")
    a("| `Working/Translation/T11_MODES.md` | this file, regenerated by `--write` |")
    a("| `Working/Translation/t11_variants.json` | the variant table + every row's split values |")
    a("| `Tools/scripts/t11_modes.py` | the tool; `--write` / `--check` / `show <id>` |")
    a("")
    a(f"`--check` re-derives {c['rows']} rows over MOD-1/MOD-2, compares both files byte-for-byte,")
    a("cross-checks the ledger and **re-reads every number its own cells print** from the inputs named")
    a("at the top - so a change in `objects.jsonl`, `MODES.json`, `CAMERA.json`, `CAM_TUNE.json`,")
    a("`WEAPONS.json`, `USAGES.json`, `t12_audio_map.json` or `t14_lights.json` turns this check red")
    a("instead of leaving a stale doc green. Values that live in another card's row set (T-11's")
    a("weapon ids, T-12's part angles, B-12/B-13's status) are cited, not re-read.")
    a("")
    return L


# --------------------------------------------------------------------------- commands
def cmd_write() -> int:
    payload, problems = build_payload()
    lines = read_doc(payload)
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload["variants"], fh, indent=1, sort_keys=True)
        fh.write("\n")
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    for p in problems:
        print("FAIL", p)
    c = payload["variants"]["counts"]
    print(f"{OUT_JSON}: {c['rows']} rows (MOD-1 {c['MOD-1']}, MOD-2 {c['MOD-2']}), compromises "
          f"{c['compromise']}")
    print(f"{OUT_MD}: {len(lines)} lines")
    return 1 if problems else 0


def cmd_check() -> int:
    payload, problems = build_payload()
    bad = 0
    if not os.path.exists(OUT_JSON):
        print(f"FAIL: no {OUT_JSON} - run --write first")
        return 1
    on_disk = json.load(open(OUT_JSON, encoding="utf-8"))
    if on_disk != payload["variants"]:
        bad += 1
        print("FAIL: t11_variants.json differs from the re-derived record")
        x, y = json.dumps(on_disk, sort_keys=True), json.dumps(payload["variants"], sort_keys=True)
        for i in range(min(len(x), len(y))):
            if x[i] != y[i]:
                print(f"   first difference at char {i}: {x[max(0, i - 60):i + 60]!r} != "
                      f"{y[max(0, i - 60):i + 60]!r}")
                break
    new_md = "\n".join(read_doc(payload)) + "\n"
    disk_md = open(OUT_MD, encoding="utf-8").read() if os.path.exists(OUT_MD) else ""
    if disk_md != new_md:
        bad += 1
        print("FAIL: T11_MODES.md differs from the re-derived record")
        import difflib
        for line in list(difflib.unified_diff(disk_md.splitlines(), new_md.splitlines(),
                                              "T11_MODES.md", "re-derived", lineterm=""))[:20]:
            print("   " + line)
    led = {}
    if os.path.exists(LEDGER):
        led = {r["id"]: r for r in (json.loads(l) for l in open(LEDGER, encoding="utf-8")
                                    if l.strip())}
    for row in payload["doc"]:
        lr = led.get(row["id"])
        if lr is None:
            bad += 1
            print(f"FAIL {row['id']}: missing from T_ROWS.jsonl - run `t_rows.py build`")
            continue
        if lr["dispo"] != row["dispo"]:
            bad += 1
            print(f"FAIL {row['id']}: ledger dispo {lr['dispo']} != {row['dispo']}")
        if not lr.get("why"):
            bad += 1
            print(f"FAIL {row['id']}: ledger row has no reason")
        if lr["cells"] != row["cells"]:
            bad += 1
            print(f"FAIL {row['id']}: ledger cells differ from the document")
        # a named omission is not live work: an `omitted` row must be out/blocked, and a carried
        # or inside-band row must not be (review finding, R5)
        if row["compromise"] == "omitted" and lr["dispo"] not in ("out", "blocked"):
            bad += 1
            print(f"FAIL {row['id']}: `omitted` but the ledger says {lr['dispo']}")
        if row["compromise"] != "omitted" and lr["dispo"] in ("out", "blocked"):
            bad += 1
            print(f"FAIL {row['id']}: `{row['compromise']}` but the ledger says {lr['dispo']}")
    for p in problems:
        bad += 1
        print("FAIL", p)
    c = payload["variants"]["counts"]
    print(f"{'PASS' if not bad else 'FAIL'}: {c['rows']} rows | MOD-1 {c['MOD-1']} / MOD-2 "
          f"{c['MOD-2']} | compromises " + ", ".join(f"{k} {n}" for k, n in c["compromise"].items())
          + f" | ledger {sum(1 for r in payload['doc'] if r['id'] in led)}/{c['rows']}")
    return 1 if bad else 0


def cmd_show(want: str) -> int:
    payload, _ = build_payload()
    hit = [r for r in payload["doc"] if want.lower() in r["id"].lower()]
    if not hit:
        raise SystemExit(f"no row matches {want!r}")
    print(json.dumps(hit, indent=1))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("show")
    s.add_argument("want")
    a = p.parse_args()
    if a.cmd == "show":
        return cmd_show(a.want)
    if a.write:
        return cmd_write()
    if a.check:
        return cmd_check()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
