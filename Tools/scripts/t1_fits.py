"""t1_fits.py - what the JC3 fleet does and does not relate, for the translation table (T-1).

The translation table has three kinds of row:

  1. **decoded** - both sides named, the transform is arithmetic (geometry, tyre size);
  2. **fitted**  - JC3 has no BmAK counterpart, but the fleet relates the parameter to mass
     or size well enough to interpolate (low-R^2 fits are reported as *not usable*);
  3. **assumed** - neither side has a number, so the row is a choice and must say so.

This script produces the evidence for (2) and the negative result that makes (3) honest:
a log-log fit of `<member>` against `rigid_body.mass` across every land vehicle.

Usage:
  python t1_fits.py [-o Working/Translation/FITS.md]
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
OUT = os.path.join(ROOT, "Working", "Translation", "FITS.md")
TARGET_MASS = 4000.0

# member -> (module type, member path, human label)
MEMBERS = {
    "s_f": ("Suspension", "front.strength", "suspension front strength"),
    "s_r": ("Suspension", "rear.strength", "suspension rear strength"),
    "c_f": ("Suspension", "front.compression", "suspension front compression"),
    "r_f": ("Suspension", "front.relaxation", "suspension front relaxation"),
    "br": ("Brakes", "front.max_brake_torque", "front max brake torque"),
    "rad": ("LandGlobal", "front_wheels.radius", "front tyre radius"),
    "wid": ("LandGlobal", "front_wheels.width", "front tyre width"),
    "wm": ("LandGlobal", "front_wheels.mass", "front wheel mass"),
    "iy": ("RigidBody", "unit_inertia_yaw", "unit inertia yaw"),
    "ir": ("RigidBody", "unit_inertia_roll", "unit inertia roll"),
    "bias": ("RigidBody", "center_of_mass_bias", "centre-of-mass bias"),
    "rpm": ("LandEngine", "optimal_rpm", "optimal rpm"),
    "trq": ("LandEngine", "torque_factor_at_optimal_rpm", "torque at optimal rpm"),
    "mrpm": ("LandEngine", "max_rpm", "max rpm"),
    "ts": ("Transmission", "top_speed", "transmission top speed"),
    "area": ("LandAerodynamics", "frontal_area", "frontal area"),
    "cd": ("LandAerodynamics", "drag_coefficient", "drag coefficient"),
    "lift": ("LandAerodynamics", "lift_coefficient", "lift coefficient"),
    "stt": ("LandSteering", "t_to_full_steer_s", "time to full steer"),
    "smin": ("LandSteering", "steer_angle_min_speed_deg", "steer angle at min speed"),
    "smax": ("LandSteering", "steer_angle_max_speed_deg", "steer angle at max speed"),
}


def pick(mods: list[dict], typ: str) -> dict | None:
    c = [m for m in mods if m.get("type") == typ and not m["file"].endswith("_ai.vmodc")]
    if not c:
        return None
    c.sort(key=lambda m: ("00_shared" in m["file"], m["file"]))
    return c[0]


def val(mod: dict | None, path: str):
    if not mod:
        return None
    for r in mod["rows"]:
        if r["path"] == path:
            return r["value"]
    return None


def records() -> list[dict]:
    out = []
    for p in glob.glob(os.path.join(RAW, "entities", "*.json")):
        doc = json.load(open(p, encoding="utf-8"))
        if "/01_land/" not in doc["entity"]:
            continue
        mods = doc["modules"]
        mass = val(pick(mods, "RigidBody"), "mass")
        if not mass:
            continue
        rec = {"entity": doc["entity"], "mass": float(mass)}
        for key, (typ, path, _label) in MEMBERS.items():
            v = val(pick(mods, typ), path)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                rec[key] = float(v)
        out.append(rec)
    return out


def fit(rows: list[dict], key: str):
    pts = [(r["mass"], r[key]) for r in rows if key in r and r[key] > 0 and r["mass"] > 0]
    if len(pts) < 10:
        return None
    xs = [math.log(a) for a, _ in pts]
    ys = [math.log(b) for _, b in pts]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    b = sxy / sxx
    a = math.exp(my - b * mx)
    ybar = sum(y for _, y in pts) / n
    ss_res = sum((y - a * x ** b) ** 2 for x, y in pts)
    ss_tot = sum((y - ybar) ** 2 for _, y in pts)
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
    return {"a": a, "b": b, "r2": r2, "n": n, "at_4000": a * TARGET_MASS ** b,
            "min": min(y for _, y in pts), "max": max(y for _, y in pts)}


def bucket_medians(rows: list[dict], key: str) -> dict[str, tuple[int, float]]:
    edges = [(0, 1500), (1500, 3000), (3000, 6000), (6000, 15000), (15000, 10**9)]
    out = {}
    for lo, hi in edges:
        vals = sorted(r[key] for r in rows if key in r and lo <= r["mass"] < hi)
        if vals:
            out[f"{lo}-{hi if hi < 10**9 else '∞'}"] = (len(vals), vals[len(vals) // 2])
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--out", default=OUT)
    a = ap.parse_args()
    rows = records()
    lines = ["# JC3 fleet relationships (T-1 evidence)", "",
             f"Fitted over **{len(rows)}** land vehicles that carry both `rigid_body.mass` and the",
             "member, by log-log least squares: `value = a * mass^b`. `R²` is on the log scale; a",
             "value near 0 means **the fleet does not relate these two numbers**, so the translation",
             "table must not pretend it does.", "",
             f"Predicted column is the fit evaluated at **{TARGET_MASS:.0f} kg** (the built",
             "Batmobile's mass).", "",
             "| member | a | b | R² | n | fleet min…max | at 4,000 kg |",
             "|---|---|---|---|---|---|---|"]
    fits = {}
    for key, (_typ, _path, label) in MEMBERS.items():
        f = fit(rows, key)
        if not f:
            continue
        fits[key] = f
        lines.append(f"| `{label}` | {f['a']:.4g} | {f['b']:+.3f} | {f['r2']:+.3f} | {f['n']} | "
                     f"{f['min']:.4g} … {f['max']:.4g} | {f['at_4000']:.4g} |")
    lines.append("")

    usable = [k for k, f in fits.items() if f["r2"] >= 0.5]
    unusable = [k for k, f in fits.items() if f["r2"] < 0.2]
    lines += ["## What the fleet decides", ""]
    if usable:
        lines.append("Fits strong enough to interpolate (R² ≥ 0.5): " +
                     ", ".join(f"`{MEMBERS[k][2]}` ({fits[k]['r2']:.2f})" for k in usable) + ".")
    else:
        lines.append("No fit reaches R² 0.5 — the fleet does not set any of these by mass alone.")
    if unusable:
        lines.append("")
        lines.append("Fits that are noise (R² < 0.2) and must be treated as **per-vehicle art**, "
                     "not a law: " +
                     ", ".join(f"`{MEMBERS[k][2]}`" for k in unusable) + ".")
    lines.append("")

    lines += ["## Median by mass class", "",
              "Where the fit is noise, this is what the fleet actually does — a band to stay inside,",
              "not a target.", ""]
    for key in ("s_f", "br", "iy", "rad", "trq"):
        if key not in MEMBERS:
            continue
        med = bucket_medians(rows, key)
        if not med:
            continue
        lines.append(f"**`{MEMBERS[key][2]}`**")
        lines.append("")
        lines.append("| mass class (kg) | n | median |")
        lines.append("|---|---|---|")
        for k, (n, m) in med.items():
            lines.append(f"| {k} | {n} | {m:.4g} |")
        lines.append("")

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"FITS.md: {len(rows)} land vehicles, {len(fits)} members fitted, "
          f"{len(usable)} usable (R2 >= 0.5) -> {a.out}")


if __name__ == "__main__":
    main()
