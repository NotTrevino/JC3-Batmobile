#!/usr/bin/env python3
"""t3_fleet.py - what the JC3 heavy class actually ships, for the T-3 rows.

T-3 closes the factors the first table did not name (afterburner, drift, handbrake,
suspension travel, impact damage, tyre effects). None of them has a decoded BmAK
counterpart with compatible units, so each row is evidence by *class*: the median
and interquartile band of the same member across the JC3 land fleet, in the same
mass class as the built Batmobile (6,000 kg).

    python t3_fleet.py            # -> Working/Translation/T3_FLEET.md
    python t3_fleet.py --check    # fails if a member is missing from the fleet
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_JC3grab")
OUT = os.path.join(ROOT, "Working", "Translation", "T3_FLEET.md")

# label -> (module type, member path)
MEMBERS: dict[str, tuple[str, str]] = {
    "suspension front length": ("Suspension", "front.length"),
    "suspension front min_length": ("Suspension", "front.min_length"),
    "suspension front max_length_offset": ("Suspension", "front.max_length_offset"),
    "suspension front damp clamp (m/s)": ("Suspension", "front.max_velocity_for_damp_clamp"),
    "brakes handbrake friction factor": ("Brakes", "handbrake_friction_factor"),
    "brakes front min_time_to_block": ("Brakes", "front.min_time_to_block"),
    "drift max angle (deg)": ("CustomLandGlobal", "drift.max_drift_angle_deg"),
    "drift entry slip (deg)": ("CustomLandGlobal", "drift.drift_entry_slip_angle"),
    "drift min speed (km/h)": ("CustomLandGlobal", "drift.min_speed_to_drift_kmph"),
    "drift steering sensitivity": ("CustomLandGlobal", "drift.steering_sensitivity"),
    "nitro torque multiplier": ("CustomLandGlobal", "arcade.nitro_boost.torque_multiplier"),
    "nitro extra top speed (km/h)": ("CustomLandGlobal", "arcade.nitro_boost.extra_top_speed"),
    "nitro grip multiplier": ("CustomLandGlobal", "arcade.nitro_boost.grip_multiplier"),
    "nitro push force": ("CustomLandGlobal", "arcade.nitro_boost.push_force"),
    "nitro blend time (s)": ("CustomLandGlobal", "arcade.nitro_boost.boost_blend_time"),
    "tire effects skid velocity (m/s)": ("VehicleCommon", "tire_effects.min_skid_velocity_for_skid_ms"),
    "tire effects slip to skid": ("VehicleCommon", "tire_effects.slip_angle_to_peak_to_skid"),
    "tire effects skid velocity scale": ("VehicleCommon", "tire_effects.skid_velocity_scale"),
    "damage impact_damage_factor": ("VehicleDamage", "impact_damage_factor"),
    "damage impact_armor": ("VehicleDamage", "impact_armor"),
    "damage explosion_threshold": ("VehicleDamage", "explosion_threshold"),
}

BUCKETS = {"3-8 t": (3000.0, 8000.0), "6 t+": (6000.0, 1e9)}


def val(mods, typ: str, path: str):
    ms = mods.values() if isinstance(mods, dict) else mods
    for m in ms:
        if not isinstance(m, dict) or m.get("type") != typ:
            continue
        for r in m.get("rows", []):
            if r.get("path") == path:
                return r.get("value")
    return None


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
        for label, (typ, path) in MEMBERS.items():
            v = val(doc["modules"], typ, path)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                rec[label] = float(v)
        rows.append(rec)
    return rows


def fmt(vals: list[float]) -> str:
    if not vals:
        return "n=0"
    q = st.quantiles(vals, n=4) if len(vals) > 3 else [min(vals), st.median(vals), max(vals)]
    return f"n={len(vals)}  **{st.median(vals):.4g}**  ({q[0]:.4g} … {q[2]:.4g})"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    rows = fleet()
    if not rows:
        sys.exit(f"no land entities under {RAW}")
    problems = []
    lines = [
        "# T-3 fleet evidence (heavy class)",
        "",
        f"Computed over **{len(rows)} land vehicles** that carry `rigid_body.mass`. Each cell is",
        "*n*, the **median**, and the interquartile band (p25 … p75). These are the numbers the T-3",
        "rows use where BmAK has no value with compatible units, exactly as T-1 uses `FITS.md`.",
        "",
        "| member | all land | 3-8 t | 6 t+ |",
        "|---|---|---|---|",
    ]
    for label in MEMBERS:
        cells = []
        for lo, hi in [(-1e9, 1e9)] + list(BUCKETS.values()):
            vals = [r[label] for r in rows if label in r and lo <= r["mass"] < hi]
            cells.append(fmt(vals))
            if a.check and not vals:
                problems.append(f"{label}: no value in bucket {lo}-{hi}")
        lines.append(f"| `{label}` | " + " | ".join(cells) + " |")
        if a.check and sum(1 for r in rows if label in r) < 100:
            problems.append(f"{label}: only {sum(1 for r in rows if label in r)} of {len(rows)} carry it")
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"{OUT}: {len(MEMBERS)} members over {len(rows)} vehicles")
    if problems:
        for p in problems:
            print("FAIL", p)
        sys.exit(1)
    print("check ok" if a.check else "ok")


if __name__ == "__main__":
    main()
