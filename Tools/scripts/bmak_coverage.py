#!/usr/bin/env python3
"""bmak_coverage.py - every BmAK Batmobile field, accounted for.

The translation tables answer "what does this BmAK value become in JC3". They do
not, on their own, answer "did we look at everything". This does: it reads the
423 fields of the decoded Arkham Knight Batmobile classes
(`Research/BatmobileGrab/OFFSETS.json`) and assigns each one a T-row, so a factor
that never reached the tables is a build failure, not a gap someone notices later.

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


def row_ids() -> set[str]:
    ids = set()
    for p in DOCS:
        if not os.path.exists(p):
            sys.exit(f"missing {p}")
        for line in open(p, encoding="utf-8"):
            m = re.match(r"^\|\s*(T-[A-Z]{1,3}\d+)\s*\|", line)
            if m:
                ids.add(m.group(1))
    return ids


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
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"fields": len(rows), "by_row": dict(by_row), "by_class": dict(by_class),
                   "rows": rows}, fh, indent=1, ensure_ascii=False)

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
    lines += ["", "## By class", "", "| class | fields | rows it feeds |", "|---|---|---|"]
    for cls, n in sorted(by_class.items(), key=lambda kv: -kv[1]):
        rws = sorted({r["row"] for r in rows if r["class"] == cls})
        lines.append(f"| `{cls}` | {n} | {', '.join('`%s`' % r for r in rws)} |")
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")

    print(f"{len(rows)} fields -> {len(by_row)} rows; {OUT_MD}")
    for row, n in sorted(by_row.items(), key=lambda kv: -kv[1]):
        print(f"  {row:6} {n:4}")
    if a.check:
        if problems:
            for p in problems:
                print("FAIL", p)
            print(f"{len(problems)} problem(s)")
            sys.exit(1)
        print("check ok")


if __name__ == "__main__":
    main()
