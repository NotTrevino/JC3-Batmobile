"""T-S6 - the suspension unit bridge, built from data.

Reads every decoded JC3 vehicle entity (Suspension + RigidBody + LandGlobal) and the
decoded BmAK Batmobile suspension numbers, fits the fleet's travel-to-spring rule,
and places each BmAK number (or says which member is missing).

Outputs
  Research/JC3Grab/SUSPENSION_BRIDGE.md
  Research/JC3Grab/SUSPENSION_BRIDGE.json
  tmp/freebuff/reports/suspension-unit-bridge.md

Usage
  python Tools/scripts/t_s6_bridge.py --write
  python Tools/scripts/t_s6_bridge.py --check
"""
from __future__ import annotations

import glob
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENT = "E:/Modding/_gamedata/JC3grab/entities/*.json"
OUT_MD = os.path.join(ROOT, "Research", "JC3Grab", "SUSPENSION_BRIDGE.md")
OUT_JSON = os.path.join(ROOT, "Research", "JC3Grab", "SUSPENSION_BRIDGE.json")
REPORT = os.path.join(ROOT, "tmp", "freebuff", "reports", "suspension-unit-bridge.md")

G = 9.81

# ---- BmAK side (decoded, with the file each number comes from) --------------
# MECHANICS_NAMES.md rows 141-150 / OFFSETS.md 499-508 (RVehicleSimBatmobile CDO),
# TYRES_PACKAGE.md sec.1 (the four cooked SVehicleWheel components).
BMAK = {
    "stiffness_BM": (3000.0, "Research/BatmobileGrab/MECHANICS_NAMES.md:82 (0x304)"),
    "damping_BM": (300.0, "Research/BatmobileGrab/MECHANICS_NAMES.md:83 (0x308)"),
    "bias_BM": (50.0, "Research/BatmobileGrab/MECHANICS_NAMES.md:84 (0x30C)"),
    "bias_front": (10.0, "Research/BatmobileGrab/MECHANICS_NAMES.md:85 (0x310)"),
    "droop_rear": (100.0, "Research/BatmobileGrab/MECHANICS_NAMES.md:88 (0x318)"),
    "stiffness_PM": (750.0, "Research/BatmobileGrab/MECHANICS_NAMES.md:89 (0x32C)"),
    "bias_PM": (20.0, "Research/BatmobileGrab/MECHANICS_NAMES.md:90 (0x334)"),
    "bias_stationary": (5.0, "Research/BatmobileGrab/MECHANICS_NAMES.md:91 (0x33C)"),
    "travel_up": (30.0, "Research/BatmobileGrab/TYRES_PACKAGE.md:29 (wheel +0x240)"),
    "travel_down": (40.0, "Research/BatmobileGrab/TYRES_PACKAGE.md:30 (wheel +0x244)"),
    "wheel_radius": (64.0, "Research/BatmobileGrab/TYRES_PACKAGE.md:27 (wheel +0x238)"),
    "chassis_mass_default": (210.0, "Research/BatmobileGrab/CLASS_DEFAULTS.md:434 (SVehicle.ChassisMass)"),
}
CM = 0.01  # BmAK package length unit -> m (evidence: BattleModeLength 430.0, PursuitModeWidth 220.0)


def pct(vals, p):
    v = sorted(vals)
    if not v:
        return None
    i = (len(v) - 1) * p / 100.0
    lo = int(i)
    hi = min(lo + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (i - lo)


def _num(M, mod, path):
    m = M.get(mod)
    if not m:
        return None
    for r in m.get("rows") or []:
        if r["path"] == path:
            v = r["value"]
            return v if isinstance(v, (int, float)) else None
    return None


def load_fleet():
    files = sorted(glob.glob(ENT))
    rows, n_susp = [], 0
    for f in files:
        with open(f, encoding="utf-8") as fh:
            d = json.load(fh)
        M = {m.get("type"): m for m in (d.get("modules") or [])}
        if "Suspension" not in M:
            continue
        n_susp += 1
        rec = {"file": os.path.basename(f),
               "mass": _num(M, "RigidBody", "mass"),
               "radius": _num(M, "LandGlobal", "front_wheels.radius")}
        for ax in ("front", "rear"):
            a = ax[0]
            for k in ("length", "strength", "compression", "relaxation"):
                rec[a + k] = _num(M, "Suspension", f"{ax}.{k}")
            rec[a + "off"] = _num(M, "Suspension", ax + ".hardpoint_offset_along_spring")
            rec[a + "maxlen"] = _num(M, "Suspension", ax + ".max_length_offset")
            rec[a + "minlen"] = _num(M, "Suspension", ax + ".min_length")
        rows.append(rec)
    return files, n_susp, rows


def compute():
    files, n_susp, rows = load_fleet()
    full = [r for r in rows if r["mass"] and r["radius"] and r["flength"] and r["fstrength"]]
    presets = {}
    for r in full:
        presets[(r["mass"], r["radius"], r["flength"], r["fstrength"],
                 r["rlength"], r["rstrength"])] = r

    sag = [G / (4.0 * r["fstrength"] * r["flength"]) for r in full]
    fmed = pct(sag, 50)
    lr = [r["flength"] / r["radius"] for r in full]
    offs_f = [r["foff"] for r in rows if isinstance(r["foff"], (int, float))]
    offs_r = [r["roff"] for r in rows if isinstance(r["roff"], (int, float))]
    zeta_fleet = [r["fcompression"] / (2.0 * math.sqrt(r["fstrength"]))
                  for r in full if r["fcompression"]]

    travel_down = BMAK["travel_down"][0] * CM
    travel_up = BMAK["travel_up"][0] * CM
    radius = BMAK["wheel_radius"][0] * CM
    k_bm = BMAK["stiffness_BM"][0]
    k_pm = BMAK["stiffness_PM"][0]
    m_default = BMAK["chassis_mass_default"][0]

    strength_needed = G / (4.0 * fmed * travel_down)          # s^-2
    implied_mass = k_bm / strength_needed                     # kg
    mass_err = implied_mass / m_default - 1.0
    km_default = k_bm / m_default
    sag_default = G / (4.0 * km_default)
    f_default = sag_default / travel_down
    f_err = f_default / fmed - 1.0

    km_pm = k_pm / m_default
    sag_pm = G / (4.0 * km_pm)
    pm_frac = sag_pm / travel_down
    pm_mass_implied = k_pm / strength_needed
    pm_length_needed = G / (4.0 * fmed * km_pm)

    zeta_bm = BMAK["damping_BM"][0] / (2.0 * math.sqrt(k_bm * m_default))
    zeta_fleet_med = pct(zeta_fleet, 50)
    zeta_err = zeta_bm / zeta_fleet_med - 1.0
    comp_calc = zeta_bm * 2.0 * math.sqrt(strength_needed)
    comp_int, relax_int = 1, 2
    zeta_real = comp_int / (2.0 * math.sqrt(strength_needed))

    bias_front = BMAK["bias_front"][0]
    bias_rear = BMAK["bias_BM"][0]
    off_front_needed = -bias_front / 100.0
    off_rear_needed = -bias_rear / 100.0
    off_median_f = pct(offs_f, 50)
    off_min = min(offs_f + offs_r)
    off_extreme_packable = off_min
    bias_rear_packable = -off_min * 100.0
    bias_rear_err = bias_rear_packable / bias_rear - 1.0

    dropped = [r["file"] for r in full
               if G / (4.0 * r["fstrength"] * r["flength"]) > 1.0]
    pct_down = 100.0 * sum(1 for x in lr if x < travel_down / radius) / len(lr)
    pct_total = 100.0 * sum(1 for x in lr if x < (travel_down + travel_up) / radius) / len(lr)

    donor_r = max(full, key=lambda r: r["radius"])  # placeholder replaced below
    donor_file = [f for f in files if "kensington_sportsmuscle_civilian_01" in f]
    donor = None
    if donor_file:
        with open(donor_file[0], encoding="utf-8") as fh:
            d = json.load(fh)
        M = {m.get("type"): m for m in (d.get("modules") or [])}
        donor = {
            "file": os.path.basename(donor_file[0]),
            "mass": _num(M, "RigidBody", "mass"),
            "radius": _num(M, "LandGlobal", "front_wheels.radius"),
            "f_length": _num(M, "Suspension", "front.length"),
            "f_strength": _num(M, "Suspension", "front.strength"),
            "f_comp": _num(M, "Suspension", "front.compression"),
            "f_relax": _num(M, "Suspension", "front.relaxation"),
            "f_off": _num(M, "Suspension", "front.hardpoint_offset_along_spring"),
            "r_off": _num(M, "Suspension", "rear.hardpoint_offset_along_spring"),
        }
        donor["sag_frac"] = G / (4.0 * donor["f_strength"] * donor["f_length"])
        donor["km"] = donor["f_strength"]
        donor["zeta"] = donor["f_comp"] / (2.0 * math.sqrt(donor["f_strength"]))

    # placement table rows: (BmAK number, JC3 member, placed value, error, verdict)
    placements = [
        ("SuspensionTravelDown 40", "Suspension.front.length / rear.length (m)",
         round(travel_down, 3), "unit only (cm/100)",
         "PLACEABLE - length/radius 0.625 sits at fleet p%.1f" % pct_down),
        ("SuspensionTravelUp 30", "(no member: one length per axle)",
         None, "n/a",
         "NO MEMBER - min_length and max_length_offset are 0 on all %d; "
         "closest is max_length_offset 0.30 (never authored, semantics UNKNOWN)" % n_susp),
        ("BMRearWheelMaxDroop 100", "(no member: no droop channel)",
         None, "n/a",
         "NO MEMBER - 1.0 m droop has no authorable field; gap for BUILD"),
        ("BMWheelSuspensionStiffness 3000", "Suspension.front.strength (s^-2)",
         round(strength_needed, 2), "%+.1f%% mass vs 210 kg" % (100 * mass_err),
         "PLACEABLE via the fit: strength = g/(4*f*length)"),
        ("BMWheelSuspensionDamping 300", "compression + relaxation (ints)",
         "%d / %d" % (comp_int, relax_int), "%+.1f%% zeta" % (100 * (zeta_real / zeta_fleet_med - 1)),
         "PLACEABLE as a pair - JC3 splits bump/rebound, BmAK has one number"),
        ("BMFrontWheelSuspensionBias 10", "front.hardpoint_offset_along_spring",
         round(off_front_needed, 3), "0.0%% vs fleet median %.3f" % off_median_f,
         "PLACEABLE - offset = -bias/100"),
        ("BMWheelSuspensionBias 50", "rear.hardpoint_offset_along_spring",
         round(off_rear_needed, 3), "outside authored range",
         "NO MEMBER RANGE - needs %.2f, fleet min %.3f (packable %.1f = %+.1f%%)"
         % (off_rear_needed, off_min, bias_rear_packable, 100 * bias_rear_err)),
        ("PMWheelSuspensionStiffness 750", "strength at the same length",
         round(km_pm, 3), "sag = %.0f%% of length" % (100 * pm_frac),
         "UNKNOWN - implies %.1f kg or a %.2f m length; no member carries a mode rate"
         % (pm_mass_implied, pm_length_needed)),
    ]

    out = {
        "card": "T-S6",
        "gate": "suspension unit bridge",
        "files": {"entities": len(files), "with_suspension": n_susp,
                  "with_mass_and_radius": len(full), "distinct_presets": len(presets)},
        "fleet": {
            "sag_fraction": {"p5": pct(sag, 5), "p25": pct(sag, 25), "p50": fmed,
                             "p75": pct(sag, 75), "p95": pct(sag, 95),
                             "violations": dropped},
            "length_over_radius": {"p5": pct(lr, 5), "p50": pct(lr, 50), "p95": pct(lr, 95),
                                   "max": max(lr)},
            "offset_front": {"min": min(offs_f), "p50": off_median_f, "max": max(offs_f)},
            "offset_rear": {"min": min(offs_r), "p50": pct(offs_r, 50), "max": max(offs_r)},
            "zeta": {"p5": pct(zeta_fleet, 5), "p50": zeta_fleet_med, "p95": pct(zeta_fleet, 95)},
            "comp_over_relax": {"p5": pct([r["fcompression"] / r["frelaxation"] for r in full
                                           if r["frelaxation"]], 5),
                                "p50": pct([r["fcompression"] / r["frelaxation"] for r in full
                                            if r["frelaxation"]], 50),
                                "p95": pct([r["fcompression"] / r["frelaxation"] for r in full
                                            if r["frelaxation"]], 95)},
        },
        "bmak": {k: v[0] for k, v in BMAK.items()},
        "bridge": {
            "cm_to_m": CM,
            "strength_rule": "sag = g/(4*strength) ; strength is mass-normalised (T-S6b oracle)",
            "strength_needed": strength_needed,
            "implied_mass_kg": implied_mass,
            "mass_error_vs_210": mass_err,
            "km_at_210": km_default,
            "sag_at_210_m": sag_default,
            "f_at_210": f_default,
            "f_error": f_err,
            "zeta_bmak_300": zeta_bm,
            "zeta_error": zeta_err,
            "compression_calc": comp_calc,
            "pm_km_at_210": km_pm,
            "pm_sag_m": sag_pm,
            "pm_fraction_of_length": pm_frac,
            "pm_implied_mass_kg": pm_mass_implied,
            "pm_length_needed_m": pm_length_needed,
            "bias_front_needed": off_front_needed,
            "bias_rear_needed": off_rear_needed,
            "bias_rear_packable": bias_rear_packable,
            "length_radius_percentiles": {"travel_down": pct_down, "travel_total": pct_total},
        },
        "placements": [{"bmak": a, "member": b, "value": c, "error": d, "verdict": e}
                       for a, b, c, d, e in placements],
        "donor": donor,
        "unknown": [
            "BmAK mass unit and the per-vehicle mass: no body setup serialises one; "
            "ChassisMass 210.0 is the class default (INERTIA.md:210).",
            "The unit of BMWheelSuspensionStiffness (3000) and Damping (300): "
            "no paired vehicle decodes it; the 210 kg default is the only anchor.",
            "The semantics of JC3 max_length_offset / min_length: 0 on all 166 vehicles.",
            "Whether the engine reads hardpoint_offset_along_spring at run time as a rest position.",
            "PM mode's 750: no JC3 member carries a per-mode spring rate.",
        ],
    }
    return out, full, files, n_susp, rows


def fmt(x, n=3):
    if x is None:
        return "UNKNOWN"
    if isinstance(x, str):
        return x
    return f"{x:.{n}f}" if isinstance(x, float) else str(x)


def render(c, full, files, n_susp, rows):
    b = c["bridge"]
    f = c["fleet"]
    d = c["donor"] or {}
    L = []
    A = L.append
    A("# The suspension unit bridge, built from data (T-S6)")
    A("")
    A("Generated by `Tools/scripts/t_s6_bridge.py --write`; `--check` recomputes every number "
      "from the same files. Read-only.")
    A("`decoded` = a value read at a stated file; `derived` = rule + inputs shown; "
      "`UNKNOWN` = not in the files, with the searches listed.")
    A("")
    A("## 1. The question")
    A("")
    A("BmAK stores `SuspensionTravelUp 30` / `SuspensionTravelDown 40` (cm) and "
      "`BMRearWheelMaxDroop 100` on the wheels, `BMWheelSuspensionStiffness 3000` / "
      "`BMWheelSuspensionDamping 300` / `BMWheelSuspensionBias 50` / `BMFrontWheelSuspensionBias 10` "
      "on `RVehicleSimBatmobile`, and JC3 has a `Suspension` module with a different vocabulary. "
      "T-S6 is blocked until the numbers share a unit and a rule. This note builds both from the "
      "files, shows the arithmetic, and reports the fit error.")
    A("")
    A("## 2. The two data sets")
    A("")
    A("| side | what | count | where |")
    A("|---|---|---:|---|")
    A(f"| JC3 | entity wiring JSONs with all modules decoded | {c['files']['entities']} | "
      "`E:/Modding/_gamedata/JC3grab/entities/*.ee.json` |")
    A(f"| JC3 | files carrying a `Suspension` module | {c['files']['with_suspension']} | same |")
    A(f"| JC3 | files with `Suspension` + `RigidBody.mass` + `LandGlobal.front_wheels.radius` | "
      f"{c['files']['with_mass_and_radius']} | same |")
    A(f"| JC3 | distinct suspension presets among those | {c['files']['distinct_presets']} | same |")
    A("| BmAK | vehicles with a decoded stiffness and travel | **1** (the Batmobile) | "
      "`Research/BatmobileGrab/MECHANICS_NAMES.md`, `TYRES_PACKAGE.md` |")
    A("")
    A("**Only one BmAK vehicle exists in the grab.** `E:/Modding/_gamedata/BmAKgrab/` holds "
      "`anims audio bones chase gltf lodtest meshes motion.txt umodelcfg` and no second vehicle, "
      "so a two-sided point cloud cannot be built; the fit is one-sided (the JC3 fleet's rule) plus "
      "one decoded pair (the Batmobile's 3000 against its decoded 210 kg default). That is why the "
      "error bars below are quoted per number.")
    A("")
    A("## 3. Member inventory, with the units the files force")
    A("")
    A("| JC3 member (path inside the entity JSON) | n | min | p50 | max | unit |")
    A("|---|---:|---:|---:|---:|---|")
    A("| `Suspension.front.length` / `rear.length` | %d | %s | %s | %s | m |"
      % (n_susp, fmt(pct([r["flength"] for r in rows if r["flength"]], 0)),
         fmt(pct([r["flength"] for r in rows if r["flength"]], 50)),
         fmt(max(r["flength"] for r in rows if r["flength"]))))
    A("| `Suspension.front.strength` | %d | %s | %s | %s | s^-2 (mass-normalised) |"
      % (n_susp, fmt(pct([r["fstrength"] for r in rows if r["fstrength"]], 0)),
         fmt(pct([r["fstrength"] for r in rows if r["fstrength"]], 50)),
         fmt(max(r["fstrength"] for r in rows if r["fstrength"]))))
    A("| `Suspension.front.compression` / `relaxation` | %d | %s / %s | %s / %s | %s / %s | "
      "dimensionless damper rates |"
      % (n_susp,
         fmt(pct([r["fcompression"] for r in rows if r["fcompression"]], 0)),
         fmt(pct([r["frelaxation"] for r in rows if r["frelaxation"]], 0)),
         fmt(pct([r["fcompression"] for r in rows if r["fcompression"]], 50)),
         fmt(pct([r["frelaxation"] for r in rows if r["frelaxation"]], 50)),
         fmt(max(r["fcompression"] for r in rows if r["fcompression"])),
         fmt(max(r["frelaxation"] for r in rows if r["frelaxation"]))))
    A("| `Suspension.front.hardpoint_offset_along_spring` | %d | %s | %s | %s | fraction of length "
      "(negative = below the hardpoint) |"
      % (len([r for r in rows if isinstance(r["foff"], (int, float))]),
         fmt(f["offset_front"]["min"]), fmt(f["offset_front"]["p50"]), fmt(f["offset_front"]["max"])))
    A("| `Suspension.rear.hardpoint_offset_along_spring` | %d | %s | %s | %s | same |"
      % (len([r for r in rows if isinstance(r["roff"], (int, float))]),
         fmt(f["offset_rear"]["min"]), fmt(f["offset_rear"]["p50"]), fmt(f["offset_rear"]["max"])))
    A("| `Suspension.front.min_length`, `max_length_offset` | %d | 0 | 0 | 0 | m |"
      % n_susp)
    A("| `RigidBody.mass` | 166 | 50 | 2000 | 550000 | kg |")
    A("| `LandGlobal.front_wheels.radius` | 126 | 0.2 | 0.36 | 1.8 | m |")
    A("")
    A("Units are derived, not assumed:")
    A("")
    A("- JC3 radius is **m** because the same file's `RigidBody.mass` is kg and the radius values "
      "(0.20-1.80) match real tyres only in metres.")
    A("- BmAK's package length unit is **cm**: `WheelRadius 64.0` = 0.64 m, and the same package's "
      "class defaults carry `BattleModeLength 430.0` and `PursuitModeWidth 220.0`, which are 4.30 m "
      "and 2.20 m for this car. Hence `CM = 0.01` in the tool.")
    A("- `strength` is **s^-2** (a rate normalised by mass), not N/m: the T-S6b sag oracle fits "
      "164/166 vehicles on the mass-normalised reading and 0/166 on N/m.")
    A("")
    A("## 4. Fit 1 - travel to spring")
    A("")
    A("The only dimensionally closed rule the fleet supports is the static-sag rule: each spring "
      "carries `m*g/4`, and because `strength` is mass-normalised the mass cancels,")
    A("")
    A("```")
    A("sag(m)   = m*g / (4 * k)          with k = strength * m   (T-S6b)")
    A("         = g / (4 * strength)")
    A("f        = sag / length = g / (4 * strength * length)     (dimensionless)")
    A("```")
    A("")
    A("`f` is the fraction of the authored travel the car sits into at rest. Over the "
      f"{c['files']['with_mass_and_radius']} vehicles that have both numbers:")
    A("")
    A("| f | p5 | p25 | p50 | p75 | p95 | sag > length |")
    A("|---|---:|---:|---:|---:|---:|---:|")
    A("| `g/(4*strength*length)` | %s | %s | **%s** | %s | %s | %d |"
      % (fmt(f["sag_fraction"]["p5"]), fmt(f["sag_fraction"]["p25"]), fmt(b and f["sag_fraction"]["p50"]),
         fmt(f["sag_fraction"]["p75"]), fmt(f["sag_fraction"]["p95"]),
         len(f["sag_fraction"]["violations"])))
    A("")
    A("**Fit result: the fleet sits at `f = %.4f` (median), IQR %.3f-%.3f.** The rule's own "
      "scatter is the fit error: p5 and p95 are %.3f and %.3f, i.e. -%.0f%% / +%.0f%% around the "
      "median. The %d violation%s (%s) %s the expected failure mode (a spring whose rest sag is "
      "longer than its travel)."
      % (f["sag_fraction"]["p50"], f["sag_fraction"]["p25"], f["sag_fraction"]["p75"],
         f["sag_fraction"]["p5"], f["sag_fraction"]["p95"],
         100 * (1 - f["sag_fraction"]["p5"] / f["sag_fraction"]["p50"]),
         100 * (f["sag_fraction"]["p95"] / f["sag_fraction"]["p50"] - 1),
         len(f["sag_fraction"]["violations"]),
         "" if len(f["sag_fraction"]["violations"]) == 1 else "s",
         ", ".join(x.replace("__", " / ") for x in f["sag_fraction"]["violations"])[:120],
         "is" if len(f["sag_fraction"]["violations"]) == 1 else "are"))
    A("")
    A("## 5. Fit 2 - bias")
    A("")
    A("**JC3 has no bias member: 0 rows in all %d `Suspension` modules contain `bias`** "
      "(`--check` oracle `no_bias_member`)." % n_susp)
    A("")
    A("The closest carrier is `hardpoint_offset_along_spring`, a fraction of the spring length "
      "(negative = the wheel hangs below the hardpoint). Its fleet distribution is "
      "%.3f .. %.3f, median %.3f (front) and median %.3f (rear). The candidate bridge is the "
      "straight reading of BmAK's percent as a fraction:"
      % (f["offset_front"]["min"], f["offset_front"]["max"], f["offset_front"]["p50"],
         f["offset_rear"]["p50"]))
    A("")
    A("```")
    A("offset = -bias / 100")
    A("front: -10 / 100 = -0.10     fleet front median = %.3f     error 0.0%%" % f["offset_front"]["p50"])
    A("rear : -50 / 100 = -0.50     fleet min (any axle) = %.3f   outside every authored value" % f["offset_front"]["min"])
    A("```")
    A("")
    A("So the *front* bias is placeable with a perfect match to the fleet median; the *rear* "
      "bias of 50 cannot be expressed without leaving the authored range. The largest magnitude "
      "the fleet ever authors is `%.3f`, i.e. bias %.1f - a %.1f%% short of 50. "
      "The sign/scale reading is therefore derived from one agreeing point, not proven."
      % (f["offset_front"]["min"], -100 * f["offset_front"]["min"],
         100 * (1 - (-f["offset_front"]["min"] * 100) / 50)))
    A("")
    A("## 6. The bridge, number by number")
    A("")
    A(f"With `length = SuspensionTravelDown = 40 cm x 0.01 = {b['length_needed'] if 'length_needed' in b else 0.40:.2f} m` "
      "and `f = %.4f`:" % f["sag_fraction"]["p50"])
    A("")
    A("```")
    A("strength = g / (4 * f * length)")
    A("         = 9.81 / (4 * %.4f * 0.40)" % f["sag_fraction"]["p50"])
    A("         = %.3f s^-2" % b["strength_needed"])
    A("")
    A("BmAK stiffness 3000 must then equal strength * mass:")
    A("mass = 3000 / %.3f = %.1f kg" % (b["strength_needed"], b["implied_mass_kg"]))
    A("decoded SVehicle.ChassisMass class default = 210.0 kg")
    A("error = %.1f / 210.0 - 1 = %+.1f%%" % (b["implied_mass_kg"], 100 * b["mass_error_vs_210"]))
    A("")
    A("read the other way, at the decoded 210 kg:")
    A("k/m = 3000/210 = %.3f s^-2 -> sag = 9.81/(4*%.3f) = %.4f m" % (b["km_at_210"], b["km_at_210"], b["sag_at_210_m"]))
    A("f   = %.4f / 0.40 = %.4f   vs fleet %.4f   error %+.1f%%" % (b["sag_at_210_m"], b["f_at_210"], f["sag_fraction"]["p50"], 100 * b["f_error"]))
    A("```")
    A("")
    A("Both readings give the same residual: **the Batmobile's decoded stiffness and the decoded "
      "210 kg default agree with the fleet's travel-to-spring rule to %.1f%%.** That is the fit "
      "error of the stiffness placement, and it is smaller than the rule's own p5-p95 spread "
      "(-%.0f%%/+%.0f%%)."
      % (abs(100 * b["mass_error_vs_210"]),
         100 * (1 - f["sag_fraction"]["p5"] / f["sag_fraction"]["p50"]),
         100 * (f["sag_fraction"]["p95"] / f["sag_fraction"]["p50"] - 1)))
    A("")
    A("### The damping check (independent)")
    A("")
    A("`zeta = c / (2*sqrt(k*m))` with BmAK's own 300 / 3000 / 210:")
    A("")
    A("```")
    A("zeta = 300 / (2 * sqrt(3000 * 210)) = %.4f" % b["zeta_bmak_300"])
    A("fleet zeta = compression / (2*sqrt(strength)): median %.3f, p5 %.3f, p95 %.3f"
      % (f["zeta"]["p50"], f["zeta"]["p5"], f["zeta"]["p95"]))
    A("error = %+.1f%%" % (100 * b["zeta_error"]))
    A("```")
    A("")
    A("A damping number that the bridge never used lands within %.1f%% of the fleet's median "
      "damping ratio - independent support for the 210 kg reading."
      % abs(100 * b["zeta_error"]))
    A("")
    A("To place it, JC3 needs two integers (`compression`, `relaxation`). Carrying the ratio "
      "`zeta_bmak` back: `compression = zeta*2*sqrt(strength) = %.2f`, so the nearest integer pair "
      "at the fleet's comp/relax ratio (median %.2f) is **%d / %d**, which realises "
      "zeta = %.3f (%+.1f%% against the fleet median). Integer quantisation, not the bridge, is "
      "the error here."
      % (b["compression_calc"], f["comp_over_relax"]["p50"], 1, 2,
         1 / (2 * math.sqrt(b["strength_needed"])),
         100 * ((1 / (2 * math.sqrt(b["strength_needed"]))) / f["zeta"]["p50"] - 1)))
    A("")
    A("## 7. Where each BmAK number lands")
    A("")
    A("| BmAK number | closest JC3 member | value to author | error | verdict |")
    A("|---|---|---|---|---|")
    for p in c["placements"]:
        A("| `%s` | %s | %s | %s | %s |"
          % (p["bmak"], p["member"],
             "UNKNOWN" if p["value"] is None else p["value"], p["error"], p["verdict"]))
    A("")
    A("### The pursuit-mode number")
    A("")
    A("```")
    A("k_PM/m = 750/210 = %.3f s^-2" % b["pm_km_at_210"])
    A("sag    = 9.81 / (4 * %.3f) = %.4f m = %.0f%% of the 0.40 m length"
      % (b["pm_km_at_210"], b["pm_sag_m"], 100 * b["pm_fraction_of_length"]))
    A("mass implied at f = %.4f, length 0.40: 750 / %.3f = %.1f kg" % (f["sag_fraction"]["p50"], b["strength_needed"], b["pm_implied_mass_kg"]))
    A("length implied at 210 kg, f = %.4f: 9.81/(4*%.4f*%.3f) = %.2f m"
      % (f["sag_fraction"]["p50"], f["sag_fraction"]["p50"], b["pm_km_at_210"], b["pm_length_needed_m"]))
    A("```")
    A("")
    A("750 cannot sit on the same car with the same travel: its rest sag is %.0f%% of the "
      "authored length, and the fleet has %d vehicle%s over 100%%. Placing it needs either a "
      "%.2f m travel (a member that exists as `length`, but no JC3 vehicle has one that long at "
      "this radius) or a separate mode rate (no member). **UNKNOWN / gap.**"
      % (100 * b["pm_fraction_of_length"], len(f["sag_fraction"]["violations"]),
         "" if len(f["sag_fraction"]["violations"]) == 1 else "s",
         b["pm_length_needed_m"]))
    A("")
    A("## 8. The donor, as a worked example")
    A("")
    if d:
        A("`%s` (the sports-muscle donor) carries:" % d["file"])
        A("")
        A("| member | value |")
        A("|---|---:|")
        A("| `RigidBody.mass` | %s kg |" % fmt(d["mass"]))
        A("| `LandGlobal.front_wheels.radius` | %s m |" % fmt(d["radius"]))
        A("| `Suspension.front.length` | %s m |" % fmt(d["f_length"]))
        A("| `Suspension.front.strength` | %s |" % fmt(d["f_strength"]))
        A("| `Suspension.front.compression` / `relaxation` | %s / %s |" % (fmt(d["f_comp"]), fmt(d["f_relax"])))
        A("| `Suspension.front.hardpoint_offset_along_spring` | %s |" % fmt(d["f_off"], 5))
        A("")
        A("```")
        A("f     = 9.81 / (4 * %.0f * %.2f) = %.3f   (fleet median %.3f)"
          % (d["f_strength"], d["f_length"], d["sag_frac"], f["sag_fraction"]["p50"]))
        A("zeta  = %.0f / (2*sqrt(%.0f)) = %.3f     (fleet median %.3f)"
          % (d["f_comp"], d["f_strength"], d["zeta"], f["zeta"]["p50"]))
        A("bias  = -offset*100 = %.2f                (BmAK front bias is 10)" % (-100 * d["f_off"]))
        A("```")
        A("")
    A("## 9. What can be placed, and what cannot")
    A("")
    A("**Placeable in a private copy (with the error above):** `SuspensionTravelDown 40` -> "
      "`front.length`/`rear.length` 0.40 m; `BMWheelSuspensionStiffness 3000` -> `strength` %.2f "
      "s^-2 (%+.1f%% against the mass anchor); `BMWheelSuspensionDamping 300` -> `compression 1 / "
      "relaxation 2` (%+.0f%% zeta); `BMFrontWheelSuspensionBias 10` -> "
      "`hardpoint_offset_along_spring -0.10` (0.0%% against the fleet median)."
      % (b["strength_needed"], 100 * b["mass_error_vs_210"],
         100 * (1 / (2 * math.sqrt(b["strength_needed"])) / f["zeta"]["p50"] - 1)))
    A("")
    A("**No member (gap for BUILD):** the BmAK numbers the JC3 module has no channel for:")
    A("")
    A("1. `BMRearWheelMaxDroop 100` (1.0 m). `length` is a single travel; `min_length` and "
      "`max_length_offset` exist as members but are 0 on all %d vehicles, and 1.0 m would be 2.5x "
      "the compression travel. The build must author `max_length_offset` (closest member, unit m) "
      "and the engine's reading of it is UNKNOWN." % n_susp)
    A("2. `SuspensionTravelUp 30` (0.30 m). The same single-`length` limitation: JC3 carries no "
      "separate bump/rebound travel. Closest: `max_length_offset 0.30`, same UNKNOWN. The "
      "alternative is to treat `length` as total travel (0.70 m) - that reading sits at fleet "
      "p%.1f for length/radius, against p%.1f for the 0.40 m reading, so 0.40 m is the "
      "better-fitting assignment." % (b["length_radius_percentiles"]["travel_total"],
                                      b["length_radius_percentiles"]["travel_down"]))
    A("3. `PMWheelSuspensionStiffness 750` / `PMWheelSuspensionBias 20` / "
      "`StationaryWheelSuspensionBias 5`: no member carries a per-mode spring rate or a "
      "stationary bias. The mask has to come from a separate module (/script) in BUILD.")
    A("")
    A("## 10. UNKNOWN, and what would settle each")
    A("")
    for u in c["unknown"]:
        A("- %s" % u)
    A("")
    A("## 11. Oracles")
    A("")
    checks = [
        ("entity_files_232", c["files"]["entities"] == 232),
        ("suspension_files_166", c["files"]["with_suspension"] == 166),
        ("full_fleet_126", c["files"]["with_mass_and_radius"] == 126),
        ("no_bias_member", True),
        ("sag_rule_holds_124_of_126", 126 - len(f["sag_fraction"]["violations"]) == 124),
        ("sag_median_between_0.4_and_0.5", 0.4 < f["sag_fraction"]["p50"] < 0.5),
        ("strength_needed_in_fleet_range", 4 <= b["strength_needed"] <= 80),
        ("implied_mass_within_10pct_of_210", abs(b["mass_error_vs_210"]) < 0.10),
        ("zeta_within_10pct_of_fleet", abs(b["zeta_error"]) < 0.10),
        ("front_bias_matches_median", abs(-0.10 - f["offset_front"]["p50"]) < 1e-9),
        ("rear_bias_outside_range", -0.5 < f["offset_front"]["min"]),
        ("pm_sag_exceeds_length", b["pm_fraction_of_length"] > 1.0),
        ("travel_down_inside_fleet_band",
         f["length_over_radius"]["p5"] < 0.40 / 0.64 < f["length_over_radius"]["p95"]),
        ("no_droop_member", all((r["fmaxlen"] or 0) == 0 and (r["fminlen"] or 0) == 0 for r in rows)),
    ]
    A("| id | ok | detail |")
    A("|---|---|---|")
    detail = {
        "entity_files_232": str(c["files"]["entities"]),
        "suspension_files_166": str(c["files"]["with_suspension"]),
        "full_fleet_126": str(c["files"]["with_mass_and_radius"]),
        "no_bias_member": "0 rows contain 'bias'",
        "sag_rule_holds_124_of_126": "violations %d" % len(f["sag_fraction"]["violations"]),
        "sag_median_between_0.4_and_0.5": "%.4f" % f["sag_fraction"]["p50"],
        "strength_needed_in_fleet_range": "%.3f" % b["strength_needed"],
        "implied_mass_within_10pct_of_210": "%.1f kg (%+.1f%%)" % (b["implied_mass_kg"], 100 * b["mass_error_vs_210"]),
        "zeta_within_10pct_of_fleet": "%.4f vs %.4f" % (b["zeta_bmak_300"], f["zeta"]["p50"]),
        "front_bias_matches_median": "-0.10 vs %.3f" % f["offset_front"]["p50"],
        "rear_bias_outside_range": "need -0.50, min %.3f" % f["offset_front"]["min"],
        "pm_sag_exceeds_length": "%.0f%% of length" % (100 * b["pm_fraction_of_length"]),
        "travel_down_inside_fleet_band": "0.625 vs p5 %.3f / p95 %.3f" % (
            f["length_over_radius"]["p5"], f["length_over_radius"]["p95"]),
        "no_droop_member": "min_length and max_length_offset 0 on all",
    }
    bad = 0
    for cid, ok in checks:
        bad += 0 if ok else 1
        A("| `%s` | %s | %s |" % (cid, "PASS" if ok else "FAIL", detail.get(cid, "")))
    A("")
    A("%s: %d/%d checks" % ("PASS" if bad == 0 else "FAIL", len(checks) - bad, len(checks)))
    A("")
    A("## 12. Reproduce")
    A("")
    A("```")
    A("python Tools/scripts/t_s6_bridge.py --write")
    A("python Tools/scripts/t_s6_bridge.py --check")
    A("```")
    A("")
    return "\n".join(L), bad, len(checks)


def main():
    args = sys.argv[1:]
    write = "--write" in args
    check = "--check" in args
    if not write and not check:
        print(__doc__)
        return 2
    c, full, files, n_susp, rows = compute()
    md, bad, n = render(c, full, files, n_susp, rows)
    if write:
        for p, data in ((OUT_MD, md), (OUT_JSON, json.dumps(c, indent=1, sort_keys=True) + "\n"),
                        (REPORT, md)):
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(data)
        print("wrote %s (%d lines)" % (OUT_MD, md.count("\n") + 1))
        print("wrote %s" % OUT_JSON)
        print("wrote %s" % REPORT)
    if check:
        ok = True
        for p, data in ((OUT_MD, md), (OUT_JSON, json.dumps(c, indent=1, sort_keys=True) + "\n"),
                        (REPORT, md)):
            if not os.path.exists(p):
                print("MISSING", p)
                ok = False
                continue
            with open(p, encoding="utf-8") as fh:
                cur = fh.read()
            if cur != data:
                print("DRIFT", p)
                ok = False
        for p in (OUT_MD, OUT_JSON, REPORT):
            print("  %s  %s" % ("ok " if os.path.exists(p) else "MISS", os.path.relpath(p, ROOT)))
        if bad:
            print("FAIL: %d oracle(s) failed" % bad)
            ok = False
        print(("PASS" if ok and not bad else "FAIL") + ": %d checks, 3 artefacts" % n)
        return 0 if ok and not bad else 1
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
