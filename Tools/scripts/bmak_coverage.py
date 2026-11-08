#!/usr/bin/env python3
"""bmak_coverage.py - every BmAK Batmobile field, accounted for.

The translation tables answer "what does this BmAK value become in JC3". They do
not, on their own, answer "did we look at everything". This does: it reads the
423 fields of the decoded Arkham Knight Batmobile classes
(`Research/BatmobileGrab/OFFSETS.json`) and assigns each one a T-row, so a factor
that never reached the tables is a build failure, not a gap someone notices later.

T-23 adds the **G1 feature rows**: the 62 weapon objects, 253 animation
sequences, 361 audio events and 101 light entries of the four feature records
(`WEAPONS.json`, `ANIMATIONS.json`, `AUDIO_FEATURES.json`, `LIGHTS.json`) are
assigned to a T-row by the same rule - an unmatched row is a FAIL, never a
silent default. A field census cannot see a weapon object, an AnimSequence or an
AkEvent, so without this block those features were covered only by hand-written
prose in the G1 docs.

Assignment is deliberately blunt about the two kinds of "not translated":

  * `out`     - BmAK has the system, JC3 has no expression for it (no vehicle
                weapons, no battle mode, no self-righting constraint);
  * `plumbing`- the field is Unreal actor composition (components, sockets,
                archetypes, tags), not a vehicle factor; the donor's wiring
                carries it and T-PA9 records that.

Usage:
  python bmak_coverage.py            # -> Research/BatmobileGrab/COVERAGE.{json,md}
  python bmak_coverage.py --check    # fails on an unassigned field or a missing row
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OFFSETS = os.path.join(ROOT, "Research", "BatmobileGrab", "OFFSETS.json")
DOCS = [os.path.join(ROOT, "Working", "Translation", n)
        for n in ("T1_TRANSLATION.md", "T2_TRANSLATION.md", "T3_COVERAGE.md")]
# T-23: every phase-T document a G1 row may be assigned to.  The first column of these
# tables is either a T- id or a short row id (`P-01` cut parts, `A-01`/`W-01` audio).
ROW_DOCS = [os.path.join(ROOT, "Working", "Translation", n) for n in (
    "T1_TRANSLATION.md", "T2_TRANSLATION.md", "T3_COVERAGE.md", "T6_HUD_CAMERA.md",
    "T7_WEAPONS.md", "T8_PARTS.md", "T10_DAMAGE.md", "T11_MODES.md", "T12_AUDIO.md",
    "T13_FX.md", "T14_LIGHTS.md", "T15_WORLD.md")]
G1 = os.path.join(ROOT, "Research", "BatmobileGrab")
OUT_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "COVERAGE.json")
OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "COVERAGE.md")

WEAPONS = {
    "RBatmobileCannon", "RBatmobileHeavyCannon", "RBatmobileMissile",
    "RBatmobileMissileLauncher", "RBatmobileMissileLauncherJoker",
    "RBatmobileEMPMissile", "RBatmobileEMP", "RBatmobileSonar", "RBatmobileWinch",
    "RBatmobileVehicleTracker", "RBatmobileAllegianceSwitcher",
}
SIM_EXPLICIT = {"RVehicleSimBatmobile", "SVehicleWheel"}


def assign(cls: str, name: str | None) -> tuple[str, str]:
    """field -> (T-row, one-line reason). Never returns an empty row."""
    n = name or ""
    if cls in WEAPONS:
        return "T-W1", "weapon system: JC3 has no player-fired car weapons"
    if cls == "RBatmobileBooster":
        return "T-B1", "afterburner actor; the boost itself is JC3 nitro_boost"
    if cls == "SVehicleWheel":
        if n == "WheelRadius":
            return "T-G6", "wheel radius: BmAK 0.64 m vs the mesh 0.683 m"
        if n in ("SuspensionTravelUp", "SuspensionTravelDown"):
            return "T-S6", "suspension travel/droop"
        if n in ("SuspensionSpeedUp", "SuspensionSpeedDown"):
            return "T-S6", "suspension rate and bias"
        if n in ("LatSlipFactor", "HandbrakeLatSlipFactor"):
            return "T-DR1", "tyre lateral slip under drift/handbrake"
        if "Particle" in n or "SkidMark" in n or "Wetness" in n:
            return "T-FX6", "wheel particle/skid effect, not a vehicle number"
        return "", ""  # a new wheel field must be looked at, not defaulted
    if cls == "RVehicleSimBatmobile":
        if n.startswith(("TurnOnSpot", "BattleMode", "Transformation")) or n == "TurningModeMaxSpeed":
            return "T-BM1", "battle mode / turn-on-spot / transformation"
        if "SuspensionStiffness" in n or "SuspensionDamping" in n or "SuspensionBias" in n \
                or n == "BMRearWheelMaxDroop" or n == "UseFrontWheelSuspensionBias":
            return "T-S6", "suspension rate/bias/droop"
        if n == "DriftingBoostCooldown":
            return "T-DR1", "drift boost cooldown"
        if n == "AirControlYawTorqueFactorMax":
            return "T-AC1", "mid-air yaw authority"
        if n.startswith("Handbrake"):
            return "T-K4", "handbrake blend speeds"
        if n in ("SteerSpeed", "SpinSteeringFactor", "InVal", "OutVal",
                 "ArriveTangent", "LeaveTangent"):
            return "T-ST7", "steering rate and its curve"
        if n == "MaxBrakeTorque":
            return "T-K1", "brake torque, already a T-1 row"
        return "", ""
    if cls == "RVehicleBatmobile":
        if n.startswith(("Afterburner", "SideExhaust", "ExhaustBurst")):
            return "T-B1", "afterburner plumbing and boost effects"
        if n.startswith(("BrakeLightTrail", "RearFinTrail", "SpeedLines", "WallScrapeSparks")) \
                or n == "HeatSteam":
            return "T-FX6", "vehicle effect system, not a physics number"
        if n.startswith(("Weapon", "PursuitMode", "BattleModePrimaryWeapon")) \
                or n == "VehicleWeaponFlags":
            return "T-W1", "weapon slot / generator"
        if n == "ArmourModeDamageReduction":
            return "T-BM1", "battle-mode armour"
        if n.startswith("Ebrake") or n.startswith("EBrake"):
            return "T-K4", "handbrake force and duration"
        if n.startswith("Jump") or n.startswith("StayUpright"):
            return "T-SR1", "self-righting torque / upright constraint"
        if n.startswith(("ImpactRoadAssist", "BattleDodge", "PMDodge", "VehicleShoving",
                         "KillFlip", "KillKeepyUp", "ImpactShake")):
            return "T-RA1", "combat/collision assist torque"
        if n.startswith(("ImpactMaxDamageSpeed", "ImpactMinDamageSpeed", "BattleModeImpact",
                         "ImpactStrafe", "ImpactBoost", "ImpactMaxDamagePow")):
            return "T-DM7", "impact damage thresholds"
        if n.startswith("Squeal"):
            return "T-EF1", "tyre squeal threshold"
        if n.startswith("Transformation") or n in ("TaserSound", "VehicleSound"):
            return "T-AU5", "Batmobile sound event"
        if n in ("XrayLight", "LightComponent", "LensFlareComponent"):
            return "T-L1", "light rig preset, already a T-1 row"
        if n == "Health":
            return "T-DM1", "health block, already a T-1 row"
        return "T-PA9", "Unreal actor plumbing (component/socket/archetype/tag)"
    return "T-W1", "default: an actor class with no vehicle dynamics"


ROW_ID_RE = re.compile(r"^\|\s*(T-[A-Z]{1,3}\d+|[APW]-\d\d)\s*\|")


def row_ids() -> set[str]:
    ids = set()
    for p in ROW_DOCS:
        if not os.path.exists(p):
            sys.exit(f"missing {p}")
        for line in open(p, encoding="utf-8"):
            m = ROW_ID_RE.match(line)
            if m:
                ids.add(m.group(1))
    return ids


# --------------------------------------------------------------------------- G1 feature rows
# T-23.  A field census cannot see a weapon object, an AnimSequence, an AkEvent or a light
# entry, so the four feature records get their own census: one row of the G1 file = one T row.
# Every rule is stated here and an unmatched row is a FAIL, the same contract as `assign()`.

WEAPON_ROWS = {
    "RBatmobileHeavyCannon": ("T-WP1", "WPN-1 heavy cannon (60 mm)"),
    "RBatmobileCannon": ("T-WP2", "WPN-2 Vulcan chain gun"),
    "RBatmobileMissileLauncher": ("T-WP3", "WPN-3 missile launcher"),
    "RBatmobileMissileLauncherJoker": ("T-WP3", "WPN-3 missile launcher, Joker package"),
    "RBatmobileEMPMissile": ("T-WP4", "WPN-4 EMP missile (Immobilizer)"),
    "RBatmobileEMP": ("T-WP5", "WPN-5 EMP burst"),
    "RBatmobileWinch": ("T-WP6", "WPN-6 winch"),
    "RBatmobileAllegianceSwitcher": ("T-WP7", "WPN-7 drone hacker"),
    "RBatmobileSonar": ("T-WP8", "WPN-8 sonar"),
    "RBatmobileVehicleTracker": ("T-WP9", "WPN-9 vehicle tracker"),
    "RBatmobileBooster": ("T-WP11", "WPN-11 booster"),
}
# projectile objects carry their launcher's row; the name is the only owner left in the record
PROJECTILE_TOKENS = (("EMPMissile", "T-WP4", "WPN-4's projectile"),
                     ("Tracker", "T-WP9", "WPN-9's projectile"),
                     ("Missile", "T-WP3", "WPN-3's projectile"),
                     ("Heavy_Cannon", "T-WP1", "WPN-1's projectile"))

ANIM_ROWS = {
    "turret": ("P-01", "turret yaw (ANI-2); the cannon row is P-02"),
    "cannon": ("P-02", "cannon pitch (ANI-2)"),
    "Vulcan": ("P-03", "Vulcan barrel spin (ANI-3)"),
    "missile bays": ("P-07", "missile hatch (ANI-6); the right bay is P-08 and the pods P-14/P-15"),
    "fins/air-brakes": ("P-09", "air-brake flaps (ANI-5); the family is P-09...P-12"),
    "canopy": ("P-06", "canopy hinge (MOD-4, ANI-8)"),
    "wheels/strafe": ("T-PA4", "wheel parts (ANI-1)"),
    "transformation": ("T-MD13", "transformation pose - named omission, no JC3 carrier"),
    "driver/Batman": ("T-PA9", "driver animation: actor plumbing, not a vehicle factor"),
    "other": ("T-PA9", "no cut part moves (body / seat / rear door / jet nozzle / camera): "
                        "the motion stays in the parts that are not cut"),
}

# audio: a missing bank outranks the group (90 of the 361 events)
AUDIO_ROWS = {
    "battle-mode": ("W-08", "AUD-4: the 30 battle-mode events need a mode switch a hybrid has not"),
    "engine": ("A-01", "AUD-1 engine start/idle/rev"),
    "afterburner": ("A-02", "AUD-2 nitro roar"),
    "burnout": ("A-05", "AUD-6 tyre/skid family; A-05 is its one mapped row"),
    "interior": ("A-11", "AUD-3 interior layer - named omission"),
    "movement": ("A-12", "jump/dodge one-shots - named omission"),
    "impacts": ("A-14", "impact/explosion one-shots - named omission"),
    "weapons": ("W-03", "AUD-5: MShot is the Vulcan row"),
    "voice": ("T-PA9", "character/cutscene dialogue - not a Batmobile feature"),
    "other": ("T-PA9", "world rain / Batwing cutscene - not a Batmobile feature"),
}

# lights: the record's own `behavior_disposition` decides, so no name guessing
LIGHT_ROWS = {
    ("HeadLight", "mapped"): ("T-L8", "head lamp rows (T-L8/T-L9); the stripped pair is T-L11/T-L12"),
    ("HeadLight", "inferred from socket name (type stripped by the cooker)"):
        ("T-L11", "head lamp whose type the cooker stripped (T-L11/T-L12)"),
    ("HeadLight", "approximated: battle-mode spotlight has no JC3 behavior"):
        ("T-L17", "battle-mode spot (T-L17...T-L20)"),
    ("TailLight", "mapped"): ("T-L15", "tail/brake rows (T-L15/T-L16)"),
    ("TailLight", "approximated: interior accent, no JC3 behavior"):
        ("T-L24", "dashboard light"),
    ("TailLight", "approximated: boot light, no JC3 behavior"): ("T-L35", "boot light"),
    (None, "no-jc3-equivalent: crime-scene scan light"): ("T-L21", "forensics rig - named omission"),
    (None, "no-jc3-equivalent: type stripped and socket name carries no behavior"):
        ("T-L10", "muzzle spot: no gun-light behaviour in the fleet"),
}


def weapon_row(cls: str, name: str) -> tuple[str, str]:
    if cls in WEAPON_ROWS:
        return WEAPON_ROWS[cls]
    if cls in ("RBasicProjectile", "RBatmobileMissile"):
        for token, row, why in PROJECTILE_TOKENS:
            if token in name:
                return row, why
        return "", ""
    return "", ""


def audio_row(ev: dict) -> tuple[str, str]:
    if ev.get("status") == "missing-bank":
        return "T-AU3", "the bank is absent from the install"
    if ev.get("group") in AUDIO_ROWS:
        return AUDIO_ROWS[ev["group"]]
    return "", ""


def light_row(entry: dict) -> tuple[str, str]:
    return LIGHT_ROWS.get((entry.get("behavior"), entry.get("behavior_disposition")), ("", ""))


def g1_rows() -> list[dict]:
    """(row of a G1 feature record -> T row) for weapons, animation, audio and lights."""
    rows: list[dict] = []

    def add(feature, record, key, group, row, why):
        rows.append({"feature": feature, "record": record, "key": key, "group": group,
                     "row": row, "why": why})

    w = json.load(open(os.path.join(G1, "WEAPONS.json"), encoding="utf-8"))
    for o in w["objects"]:
        row, why = weapon_row(o["class"], o["name"])
        add("weapons", "WEAPONS.json", f"{o['package']}.{o['name']}", o["class"], row, why)
    a = json.load(open(os.path.join(G1, "ANIMATIONS.json"), encoding="utf-8"))
    for s in a["sequences"]:
        row, why = ANIM_ROWS.get(s["mechanism"], ("", ""))
        add("animation", "ANIMATIONS.json", f"{s['package']}.{s['set']}.{s['name']}",
            s["mechanism"], row, why)
    au = json.load(open(os.path.join(G1, "AUDIO_FEATURES.json"), encoding="utf-8"))
    for e in au["events"]:
        row, why = audio_row(e)
        add("audio", "AUDIO_FEATURES.json", f"{e['package']}.{e['name']}",
            f"{e['group']}/{e['status']}", row, why)
    li = json.load(open(os.path.join(G1, "LIGHTS.json"), encoding="utf-8"))
    for v in li["vehicles"]:
        for e in v["entries"]:
            row, why = light_row(e)
            add("audio" if False else "lights", "LIGHTS.json", f"{v['package']}.{v['owner']}.{e['socket']}",
                f"{e.get('behavior')}/{e.get('behavior_disposition')}", row, why)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = json.load(open(OFFSETS, encoding="utf-8"))
    known = row_ids()
    rows, problems = [], []
    for f in doc["fields"]:
        row, why = assign(f["class"], f.get("field_name"))
        if not row:
            problems.append(f"{f['class']}.{f.get('field_name') or '<unnamed@%s>' % f['offset']}: unassigned")
        elif row not in known:
            problems.append(f"{row}: assigned but not a row in the tables")
        rows.append({"class": f["class"], "field": f.get("field_name"),
                     "offset": f["offset"], "row": row, "why": why})

    by_row = collections.Counter(r["row"] for r in rows)
    by_class = collections.Counter(r["class"] for r in rows)

    # T-23: the four G1 feature records, one row of the file per T row
    g1 = g1_rows()
    for r in g1:
        if not r["row"]:
            problems.append(f"{r['record']} {r['key']} ({r['group']}): unassigned")
        elif r["row"] not in known:
            problems.append(f"{r['row']}: assigned to {r['record']} {r['key']} but is not a row "
                            f"in the tables")
    g1_by_feature = {}
    for r in g1:
        g1_by_feature.setdefault(r["feature"], collections.Counter())[r["row"] or "-"] += 1
    g1_summary = {f: {"rows": sum(c.values()), "t_rows": len([k for k in c if k != "-"]),
                      "unassigned": c.get("-", 0), "by_row": dict(sorted(c.items()))}
                  for f, c in sorted(g1_by_feature.items())}
    g1_cnt = collections.Counter(r["row"] for r in g1 if r["row"])

    json_text = json.dumps({"fields": len(rows), "by_row": dict(by_row), "by_class": dict(by_class),
                            "rows": rows, "g1_rows": {"summary": g1_summary, "rows": g1}},
                           indent=1, ensure_ascii=False) + "\n"

    lines = ["# BmAK field coverage", "",
             f"All **{len(rows)}** decoded fields of the Arkham Knight Batmobile classes, each assigned",
             "to the T-row that accounts for it. Generated by `Tools/scripts/bmak_coverage.py`;",
             "`--check` fails if a field is unassigned or names a row the tables do not have.", "",
             "| T-row | fields | what it accounts for |", "|---|---|---|"]
    seen = {}
    for r in rows:
        seen.setdefault(r["row"], r["why"])
    for row, n in sorted(by_row.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"| `{row}` | {n} | {seen[row].split(':')[0]} |")

    # T-23: the G1 feature records
    lines += ["", "## G1 feature rows (T-23)", "",
              "One row of each feature record, assigned to the T row that accounts for it. The",
              "field census above is blind to weapon objects, AnimSequences, AkEvents and light",
              "entries; this block covers them, and `--check` fails on an unassigned row.",
              "", "| record | rows | T rows | unassigned |", "|---|---:|---:|---:|"]
    for feat, s in g1_summary.items():
        rec = {"weapons": "WEAPONS.json", "animation": "ANIMATIONS.json",
               "audio": "AUDIO_FEATURES.json", "lights": "LIGHTS.json"}[feat]
        lines.append(f"| `{rec}` | {s['rows']} | {s['t_rows']} | {s['unassigned']} |")
    lines += ["", f"**{len(g1)} feature rows** in total, "
              f"**{sum(1 for r in g1 if r['row'])} assigned**, "
              f"**{sum(1 for r in g1 if not r['row'])} unassigned**.", "",
              "| T row | feature rows | what it accounts for |", "|---|---:|---|"]
    seen_g1 = {}
    for r in g1:
        if r["row"]:
            seen_g1.setdefault(r["row"], r["why"])
    for row, n in sorted(g1_cnt.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"| `{row}` | {n} | {seen_g1[row]} |")

    lines += ["", "## By class", "", "| class | fields | rows it feeds |", "|---|---|---|"]
    for cls, n in sorted(by_class.items(), key=lambda kv: -kv[1]):
        rws = sorted({r["row"] for r in rows if r["class"] == cls})
        lines.append(f"| `{cls}` | {n} | {', '.join('`%s`' % r for r in rws)} |")
    md_text = "\n".join(lines) + "\n"

    if a.check:
        # T-23: a hand edit to either file is a failure, not something this run silently fixes
        if not os.path.exists(OUT_JSON) or open(OUT_JSON, encoding="utf-8").read() != json_text:
            problems.append(f"{os.path.basename(OUT_JSON)} differs from the re-derived record")
        if not os.path.exists(OUT_MD) or open(OUT_MD, encoding="utf-8").read() != md_text:
            problems.append(f"{os.path.basename(OUT_MD)} differs from the re-derived record")
    else:
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json_text)
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md_text)

    print(f"{len(rows)} fields -> {len(by_row)} rows; {OUT_MD}")
    for row, n in sorted(by_row.items(), key=lambda kv: -kv[1]):
        print(f"  {row:6} {n:4}")
    print(f"{len(g1)} feature rows -> {len(g1_cnt)} rows"
          f" ({sum(1 for r in g1 if not r['row'])} unassigned)")
    for feat, s in g1_summary.items():
        print(f"  {feat:10} {s['rows']:4} rows -> {s['t_rows']:2} T rows, "
              f"{s['unassigned']} unassigned")
    if a.check:
        if problems:
            for p in problems:
                print("FAIL", p)
            print(f"{len(problems)} problem(s)")
            sys.exit(1)
        print("check ok")


if __name__ == "__main__":
    main()
