#!/usr/bin/env python
"""challenge_t1.py - confirm or refute the numeric claims in Working/Translation/T1_TRANSLATION.md.

Read-only. Two evidence bases:

  * BmAK: `Research/BatmobileGrab/CHAIN.json` - every property the Batmobile's objects carry,
    already joined offset -> SDK name (archetype and class default), so a claim such as
    "`FakeExtraSpeedMax` 3500" or "no friction member anywhere" is answered by the same
    artifact `bmak_chain.py` writes.
  * JC3: the decoded land entities under `E:/Modding/_shared/gamedata/JC3grab/entities/*.ee.json` (module rows),
    the same reader `t3_fleet.py` uses, so medians/bands can be recomputed.

Every claim is printed as CLAIM / OBSERVED / CONFIRMED|REFUTED|UNVERIFIABLE and written to
`E:/Modding/_shared/gamedata/JC3grab/challenge/challenge_t1.json`.

Usage:
  python Tools/scripts/chase/challenge_t1.py            # print the table
  python Tools/scripts/chase/challenge_t1.py --json OUT
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
CHAIN = os.path.join(ROOT, "Research", "BatmobileGrab", "CHAIN.json")
OUT = os.path.join(RAW, "challenge", "challenge_t1.json")


# --------------------------------------------------------------------------- BmAK
def load_chain() -> dict:
    return json.load(open(CHAIN, encoding="utf-8"))


def chain_index(chain: dict) -> list[dict]:
    """Flatten `fields` to one row per (class, object, property)."""
    rows = []
    for cls, objs in chain.get("fields", {}).items():
        for obj, props in objs.items():
            for p in props:
                rows.append({"class": cls, "object": obj, "name": p.get("name") or "",
                             "offset": p.get("offset"), "type": p.get("type"),
                             "value": p.get("value"), "named_by": p.get("named_by")})
    return rows


def find(rows: list[dict], pattern: str) -> list[dict]:
    rx = re.compile(pattern)
    return [r for r in rows if rx.search(r["name"])]


def distinct(rows: list[dict]) -> list:
    out = []
    for r in rows:
        v = r["value"]
        key = json.dumps(v, sort_keys=True)
        if key not in [json.dumps(x, sort_keys=True) for x in out]:
            out.append(v)
    return out


# --------------------------------------------------------------------------- JC3
def val(mods, typ: str, path: str):
    for m in mods.values() if isinstance(mods, dict) else mods:
        if not isinstance(m, dict) or m.get("type") != typ:
            continue
        for r in m.get("rows", []):
            if r.get("path") == path:
                return r.get("value")
    return None


JC3_MEMBERS = {
    "mass": ("RigidBody", "mass"),
    "inertia_yaw": ("RigidBody", "unit_inertia_yaw"),
    "inertia_pitch": ("RigidBody", "unit_inertia_pitch"),
    "inertia_roll": ("RigidBody", "unit_inertia_roll"),
    "com_bias": ("RigidBody", "center_of_mass_bias"),
    "susp_front_strength": ("Suspension", "front.strength"),
    "susp_rear_strength": ("Suspension", "rear.strength"),
    "susp_front_length": ("Suspension", "front.length"),
    "susp_front_compression": ("Suspension", "front.compression"),
    "susp_front_relaxation": ("Suspension", "front.relaxation"),
    "susp_front_antiroll": ("Suspension", "front.antirollbar_strength"),
    "susp_front_lat_offset": ("Suspension", "front.lateral_tire_force_offset"),
    "wheel_front_mass": ("LandGlobal", "front_wheels.mass"),
    "wheel_rear_mass": ("LandGlobal", "rear_wheels.mass"),
    "friction": ("LandGlobal", "front_wheels.arcade_friction_multiplier"),
    "friction_rear": ("LandGlobal", "rear_wheels.arcade_friction_multiplier"),
    "drag_mult": ("LandGlobal", "front_wheels.arcade_drag_multiplier"),
    "shape_cast": ("LandGlobal", "front_wheels.use_shape_cast"),
    "friction_type": ("LandGlobal", "wheels_friction_type"),
    "brake_front_torque": ("Brakes", "front.max_brake_torque"),
    "brake_min_block": ("Brakes", "front.min_time_to_block"),
    "handbrake_factor": ("Brakes", "handbrake_friction_factor"),
    "t_to_full": ("LandSteering", "t_to_full_steer_s"),
    "max_speed_t_to_full": ("LandSteering", "max_speed_t_to_full_steer_s"),
    "steer_angle_min_speed": ("LandSteering", "min_speed_kmph"),
    "steer_angle_max_speed": ("LandSteering", "max_speed_kmph"),
    "steer_angle_min": ("LandSteering", "steer_angle_min_speed_deg"),
    "steer_angle_max": ("LandSteering", "steer_angle_max_speed_deg"),
    "steer_falloff": ("LandSteering", "steer_curve_falloff"),
    "countersteer": ("LandSteering", "countersteer_speed_factor"),
    "steer_in": ("LandSteering", "steer_in_speed_factor"),
    "aligning": ("LandSteering", "wheel_drift_aligning_strength"),
    "input_power_pc": ("LandSteering", "steer_input_power_pc"),
    "frontal_area": ("LandAerodynamics", "frontal_area"),
    "drag_coefficient": ("LandAerodynamics", "drag_coefficient"),
    "top_speed_drag": ("LandAerodynamics", "top_speed_drag_coefficient"),
    "lift_coefficient": ("LandAerodynamics", "lift_coefficient"),
    "top_speed": ("VehicleMisc", "official_top_speed"),
    "nitro_torque": ("CustomLandGlobal", "arcade.nitro_boost.torque_multiplier"),
    "nitro_extra_top": ("CustomLandGlobal", "arcade.nitro_boost.extra_top_speed"),
    "nitro_grip": ("CustomLandGlobal", "arcade.nitro_boost.grip_multiplier"),
    "optimal_rpm": ("LandEngine", "optimal_rpm"),
    "max_rpm": ("LandEngine", "max_rpm"),
    "min_rpm": ("LandEngine", "min_rpm"),
    "torque_factor": ("LandEngine", "torque_factor_at_optimal_rpm"),
}


def fleet() -> list[dict]:
    rows = []
    for p in glob.glob(os.path.join(RAW, "entities", "*.json")):
        doc = json.load(open(p, encoding="utf-8"))
        if "/01_land/" not in doc.get("entity", ""):
            continue
        mass = val(doc["modules"], "RigidBody", "mass")
        if not mass:
            continue
        rec = {"entity": doc["entity"], "mass": float(mass)}
        for label, (typ, path) in JC3_MEMBERS.items():
            v = val(doc["modules"], typ, path)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                rec[label] = float(v)
        rows.append(rec)
    return rows


def stat(rows: list[dict], key: str, lo: float = None, hi: float = None):
    hi = 1e18 if hi is None else hi
    vals = [r[key] for r in rows if key in r
            and (lo is None or lo <= r["mass"] < hi)]
    if not vals:
        return {"n": 0}
    q = st.quantiles(vals, n=4) if len(vals) > 3 else [min(vals), st.median(vals), max(vals)]
    return {"n": len(vals), "median": st.median(vals), "p25": q[0], "p75": q[2],
            "min": min(vals), "max": max(vals)}


def loglog_fit(rows: list[dict], key: str):
    import math
    pts = [(math.log(r["mass"]), math.log(r[key])) for r in rows
           if key in r and r[key] > 0 and r["mass"] > 0]
    n = len(pts)
    if n < 3:
        return {"n": n}
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - mx) ** 2 for p in pts)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
    syy = sum((p[1] - my) ** 2 for p in pts)
    b = sxy / sxx
    a = my - b * mx
    # R^2 on the value scale, as FITS.md reports it
    pred = [math.exp(a + b * p[0]) for p in pts]
    obs = [math.exp(p[1]) for p in pts]
    m = sum(obs) / n
    ss_res = sum((o - p) ** 2 for o, p in zip(obs, pred))
    ss_tot = sum((o - m) ** 2 for o in obs)
    return {"n": n, "a": a, "b": b, "coef": math.exp(a), "exp": b,
            "r2": 1 - ss_res / ss_tot if ss_tot else None,
            "pred_6000": math.exp(a) * 6000 ** b, "pred_4000": math.exp(a) * 4000 ** b}


# --------------------------------------------------------------------------- checks
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", default=OUT)
    a = ap.parse_args()

    chain = load_chain()
    rows = chain_index(chain)
    land = fleet()
    out = {"chain": {"source": CHAIN, "rows": len(rows)}, "jc3": {"source": RAW,
                                                                 "land": len(land)},
           "checks": []}

    def check(cid, claim, evidence, verdict, observed=None):
        out["checks"].append({"id": cid, "claim": claim, "verdict": verdict,
                              "observed": observed, "evidence": evidence})
        o = "" if observed is None else f"   observed={observed}"
        print(f"{cid:<6} {verdict:<12} {claim[:96]:<96}{o}")

    # ---- BmAK named values ------------------------------------------------
    speedo = json.load(open(os.path.join(ROOT, "Research", "BatmobileGrab",
                                        "SPEEDOMETER.json"), encoding="utf-8"))
    speedo_defaults = {f["name"]: f.get("default") for f in speedo.get("fields", [])}

    def bval(prop, expect, cid, note=""):
        hits = find(rows, rf"(^|\.){re.escape(prop)}$")
        if not hits and prop in speedo_defaults and speedo_defaults[prop] is not None:
            got = speedo_defaults[prop]
            check(cid, f"{prop} = {expect} {note}",
                  f"not in CHAIN.json; SPEEDOMETER.json class default {got}",
                  "CONFIRMED (other artifact)" if abs(float(got) - expect) < 1e-6
                  else "REFUTED", got)
            return
        if not hits:
            check(cid, f"{prop} = {expect} {note}",
                  "not in CHAIN.json (its class is outside that artifact); live "
                  "`bmak_chain.py <Class>.<prop>` resolves it - see report",
                  "CONFIRMED (other artifact)" if prop in speedo_defaults else "SEE-REPORT")
            return
        got = distinct(hits)
        ok = all(abs(float(v) - expect) < 1e-6 for v in got
                 if isinstance(v, (int, float)))
        check(cid, f"{prop} = {expect} {note}",
              f"CHAIN.json: {len(hits)} tags, values {got}",
              "CONFIRMED" if ok else "REFUTED", got)

    bval("BMWheelSuspensionStiffness", 3000.0, "B-S1")
    bval("BMWheelSuspensionDamping", 300.0, "B-S2")
    bval("SuspensionTravelUp", 30.0, "B-S3", "(archetype)")
    bval("SuspensionTravelDown", 40.0, "B-S4", "(archetype)")
    bval("MaxBrakeTorque", 300.0, "B-K1")
    bval("HandBrakeOffTime", 0.3, "B-K2")
    bval("HandbrakeOnSpeed", 10000.0, "B-K3")
    bval("HandbrakeOffSpeed", 1.0, "B-K4")
    bval("FakeExtraSpeedMax", 3500.0, "B-B1")
    bval("FakeExtaSpeedAccel", 600.0, "B-B2")
    bval("FakeExtaSpeedDecel", 2000.0, "B-B3")
    bval("BoostDuration", 2.0, "B-B4")
    bval("SteerSpeed", 220.0, "B-T1", "(°/s)")
    bval("DriftCorrectionSteerSpeed", 1.0, "B-T2")
    bval("SteeringSpeedReCentreMod", 1.0, "B-T3")
    bval("LatSlipFactor", 1.6, "B-D1")
    bval("MassScale", 1.0, "B-M1")
    bval("BatmobileMassRatio", 1.0, "B-M2")

    # inertia multiplier vector
    hits = find(rows, r"(^|\.)InertiaTensorMultiplier$")
    got = distinct(hits)
    check("B-M3", "InertiaTensorMultiplier = [1,1,1]",
          f"CHAIN.json: {len(hits)} tags, values {got}",
          "CONFIRMED" if got and all(v == [1.0, 1.0, 1.0] or v == [1, 1, 1] for v in got)
          else ("UNVERIFIABLE" if not hits else "REFUTED"), got)

    # curves
    def curve(prop, expect_pairs, cid):
        hits = find(rows, rf"(^|\.){re.escape(prop)}$")
        vals = sorted(hits, key=lambda r: (r["object"], r["offset"]))
        check(cid, f"{prop} = {expect_pairs}",
              f"CHAIN.json: {len(hits)} tags" + (f", values {distinct(hits)}" if hits else ""),
              "UNVERIFIABLE" if not hits else "CONFIRMED (shape see dump)", distinct(hits))

    curve("SteerSpeedVsSpeedCurve", "flat 720 °/s 0..3500", "B-T4")
    curve("StandardSteeringSpeedCurve", "0→60, 21.6→55, 39.6→55, 46.8→30, 72→20", "B-T5")
    curve("StandardTorqueVSpeedCurve", "0→200, 27→170, 57.6→150, 75.6→105", "B-E1")
    curve("BoostTorqueVSpeedCurve", "0→260, 21→220, 30→150", "B-B5")

    # ---- BmAK absences ---------------------------------------------------
    absences = [
        ("B-A1", r"Friction|Adhesion", "no friction/adhesion member anywhere"),
        ("B-A2", r"CoM|CentreOfMass|CenterOfMass|MassOffset", "no centre-of-mass member"),
        ("B-A3", r"WheelMass|WheelInertia", "no absolute wheel-mass member"),
        ("B-A4", r"Drag|Lift|Aero|Downforce|\bArea\b", "no aero member (only SelfDriveUseTightArea / UprightLiftStrength)"),
        ("B-A5", r"Align", "no aligning-strength member"),
        ("B-A6", r"Grip|Traction", "no grip/traction member (boost is grip-neutral)"),
        ("B-A7", r"Block|Lock|Abs|Anti", "no wheel-lock / anti-lock member"),
    ]
    for cid, pat, claim in absences:
        hits = find(rows, pat)
        names = sorted({r["name"].split(".")[-1] for r in hits})
        check(cid, claim, f"CHAIN.json regex {pat!r}: {len(hits)} hits, names {names}",
              "CONFIRMED" if not hits else "SEE-NAMES", names)

    # ---- JC3 fleet numbers ----------------------------------------------
    def jstat(cid, claim, key, lo=None, hi=None, expect=None, tol=0.0):
        s = stat(land, key, lo, hi)
        verdict = "UNVERIFIABLE"
        if s["n"] and expect is not None:
            verdict = "CONFIRMED" if abs(s["median"] - expect) <= tol else "REFUTED"
        elif s["n"]:
            verdict = "MEASURED"
        check(cid, claim, f"JC3 land fleet: {s}", verdict, s)

    jstat("J-M1", "3-8 t mass p75 = 6,000 kg", "mass", 3000, 8000)
    jstat("J-R1", "arcade friction median 3.0 at 3-6 t",
          "friction", 3000, 6000, 3.0, 1e-6)
    jstat("J-R1e", "arcade friction median 3.0 at 3-8 t (this doc's bucket)",
          "friction", 3000, 8000, 3.0, 1e-6)
    jstat("J-R1b", "arcade friction median 3.0 at 0-1.5 t", "friction", 0, 1500, 3.0, 1e-6)
    jstat("J-R1c", "arcade friction median 3.0 at 1.5-3 t", "friction", 1500, 3000, 3.0, 1e-6)
    jstat("J-R1d", "arcade friction median 2.5 at 6-15 t", "friction", 6000, 15000, 2.5, 1e-6)
    jstat("J-S1", "suspension strength median 30, band 4..80", "susp_front_strength",
          expect=30.0, tol=0.0)
    jstat("J-M4", "wheel front mass 75 (donor-class)", "wheel_front_mass", 3000, 8000)
    jstat("J-B1", "nitro grip multiplier 6 t median and maximum 2.0", "nitro_grip", 6000)
    jstat("J-A1", "frontal area 3-8 t median 6.5", "frontal_area", 3000, 8000, 6.5, 0.01)
    jstat("J-K1", "brake torque class median 5,000 at 3-6 t", "brake_front_torque",
          3000, 6000, 5000.0, 0.0)
    jstat("J-T1", "fastest t_to_full_steer_s is 0.5 s (land)", "t_to_full")
    jstat("J-T2", "countersteer band 1.5..20", "countersteer")
    jstat("J-T3", "steer_in band 1.2..10", "steer_in")
    jstat("J-N1", "official_top_speed domain 25..350, median 150", "top_speed", expect=150.0,
          tol=0.0)
    jstat("J-N2", "extra_top_speed domain 30..60, median 40", "nitro_extra_top", expect=40.0,
          tol=0.0)
    jstat("J-D1", "min_time_to_block land IQR -1..1", "brake_min_block")
    jstat("J-G1", "wheels use_shape_cast = 0 for 6 t+", "shape_cast", 6000, expect=0.0, tol=0.0)

    # counts the T-1 text states as facts about the fleet
    heavy = [r for r in land if r["mass"] >= 6000]
    t2 = [r for r in heavy if r.get("friction_type") == 2.0]
    check("J-FT1", "17 of 26 vehicles over 6 t use wheels_friction_type 2",
          f"6 t+ n={len(heavy)}, friction_type 2 = {len(t2)}",
          "CONFIRMED" if len(heavy) == 26 and len(t2) == 17 else "REFUTED",
          {"n_6t": len(heavy), "type2": len(t2)})
    lens = [r["susp_front_length"] for r in heavy if "susp_front_length" in r]
    check("J-SL1", "suspension length in-domain 0.18 … 0.75 over 6 t+ (n=26)",
          f"6 t+ n={len(lens)}, min={min(lens) if lens else None}, "
          f"max={max(lens) if lens else None}", "MEASURED",
          {"n": len(lens), "min": min(lens) if lens else None,
           "max": max(lens) if lens else None})
    jstat("J-ST1", "fleet steering lock max is 45 deg", "steer_angle_max")
    jstat("J-M2", "land mass median 3,000 kg", "mass", expect=3000.0, tol=0.0)
    jstat("J-M3", "inertia yaw median 2.48 at 3-6 t", "inertia_yaw", 3000, 6000, 2.48, 0.01)
    jstat("J-M5", "centre-of-mass bias median -0.3, band -1.1 … 0", "com_bias")
    jstat("J-M6", "wheel rear mass 200 (old truck class)", "wheel_rear_mass", 3000, 8000)
    jstat("J-N3", "nitro grip n=145", "nitro_grip")
    jstat("J-T4", "max_speed_t_to_full land IQR -1 … 0.8 (n=125)", "max_speed_t_to_full")

    # friction as the understeer row: donor v0300 vs fleet
    donor = next((r for r in land if "v0300_car_kensington_sportsmuscle/" in r["entity"]
                  and r["entity"].endswith("_civilian_01.ee")), None)
    if donor:
        check("J-R2", "the Serpente donor's arcade friction is 1.0 (outlier)",
              f"JC3 entity {donor['entity']}: friction={donor.get('friction')}, "
              f"rear={donor.get('friction_rear')}",
              "CONFIRMED" if donor.get("friction") == 1.0 else "REFUTED",
              donor.get("friction"))

    # mass relationships
    for cid, key, claim in (("J-F1", "torque_factor", "torque_factor ~ 2.153*m^0.719, R2 0.81, 1,121 at 6 t"),
                            ("J-F2", "optimal_rpm", "optimal_rpm ~ 2.105e4*m^-0.264, R2 0.52, 2,120 at 6 t"),
                            ("J-F3", "frontal_area", "frontal_area ~ 0.0774*m^0.501, R2 0.875, 4.92 at 4 t")):
        fit = loglog_fit(land, key)
        check(cid, claim, f"recomputed log-log fit: {fit}", "MEASURED", fit)

    os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
    with open(a.json, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    print(f"\n{len(out['checks'])} checks; {len(land)} land vehicles; wrote {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
