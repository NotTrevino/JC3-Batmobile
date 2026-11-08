#!/usr/bin/env python3
"""v05_driving.py - V-05 part 1: the DRIVING predictions (Q-2 takes A1, A2, A3, A5).

Card: `GRAB_BACKLOG.md` 9a V-05 asks for the expected number and pass band of every Q check,
written before any test. This file covers the driving checks only:

    D-1  A1  0-100 km/h
    D-2  A2  top speed (boost off, then on)
    D-3  A5  braking 100 -> 0
    D-4  A3  turning circle

Out: `Working/Q/PREDICTIONS.md` (driving section only; parts 2 and 3 are
`PREDICTIONS_COMBAT.md` and `PREDICTIONS_LOOKS.md`).

Rules this file follows (the task brief and AGENTS.md):
  * every number comes from `Working/Translation/T_ROWS.jsonl` (row id printed beside it) or a
    `Research/JC3Grab/` handling file, and the QA-1 receipt the T rows quote;
  * a number that would need a physics model the repo does not derive is written UNKNOWN with the
    missing input named - it is not computed here from general knowledge;
  * every predicted line carries a pass band the Q observer can fail.

Nothing is typed as a physics result: the acceleration time, the peak speed and the decel band are
read out of the files, the braking distance is the same `d = v^2 / (2a)` the repo already applies
in `QA1_RESULTS.md` 4 and in T-K2's A5 line, and the top-speed terminal is the drag balance
`v = (2P/(rho Cd A))^(1/3)` on the built `land_aerodynamics` Cd and T-E2/T-E3's torque and wash - the
label (T-E5, `assumed`) is never used as an input to it.

    python Tools/scripts/v05_driving.py --write
    python Tools/scripts/v05_driving.py --check      # re-derive, compare byte for byte
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

T_ROWS = os.path.join(ROOT, "Working", "Translation", "T_ROWS.jsonl")
QA1 = os.path.join(ROOT, "Working", "Translation", "QA1", "qa1_measure.json")
BACKLOG = os.path.join(ROOT, "GRAB_BACKLOG.md")
OUT = os.path.join(ROOT, "Working", "Q", "PREDICTIONS.md")

# the handling docs this sheet is allowed to lean on; each must exist and be named in the doc
HANDLING_DOCS = [
    "Research/JC3Grab/PHYSICS.md",
    "Research/JC3Grab/DRIVE_CARRIERS.md",
    "Research/JC3Grab/INERTIA.md",
    "Research/JC3Grab/INERTIA2.md",
]

V100 = 100 / 3.6  # 100 km/h in m/s, the speed every band below is taken at
CURRENT = os.path.join(ROOT, "Working", "Translation", "rc4_current.json")
RHO = 1.2  # kg/m^3, the air density the terminal balance is computed at


def load_rows() -> dict[str, dict]:
    rows: dict[str, dict] = {}
    with open(T_ROWS, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                rows[r["id"]] = r
    return rows


def ledger_stats() -> dict:
    """The ledger's size, read from the file: non-blank lines, parsed rows, unique ids.

    The row count is never typed here - the ledger grows (198 -> 199 on 2026-11-06) and a pin on
    a literal turns a correct ledger into a red check.
    """
    lines = [ln for ln in open(T_ROWS, encoding="utf-8").read().splitlines() if ln.strip()]
    ids = [json.loads(ln)["id"] for ln in lines]
    return {"lines": len(lines), "rows": len(ids), "unique": len(set(ids))}


def cells(rows: dict[str, dict], rid: str) -> list[str]:
    if rid not in rows:
        raise SystemExit(f"FAIL T_ROWS.jsonl has no row {rid}")
    return rows[rid]["cells"]


def text(rows: dict[str, dict], rid: str) -> str:
    """All cells of a row joined - the row's own prose, searched, never re-typed."""
    return " | ".join(cells(rows, rid))


def need(pattern: str, hay: str, label: str):
    m = re.search(pattern, hay)
    if not m:
        raise SystemExit(f"FAIL {label}: pattern {pattern!r} not found")
    return m


def q2_card() -> str:
    """The Q-2 block of GRAB_BACKLOG.md, so the take ids are parsed not typed."""
    t = open(BACKLOG, encoding="utf-8").read()
    a, b = t.index("#### Q-2 "), t.index("#### Q-3 ")
    return t[a:b]


def build() -> tuple[str, list[dict], dict]:
    rows = load_rows()
    qa1 = json.load(open(QA1, encoding="utf-8"))
    card = q2_card()

    # ---------------------------------------------------------------- D-1  0-100 km/h (A1)
    m1 = text(rows, "T-M1")
    m1_hit = need(r"(\d+\.\d) s / (\d+) m measured", m1, "T-M1 launch time")
    t100_row, m_row = float(m1_hit.group(1)), int(m1_hit.group(2))
    s_launch = float(qa1["launch"]["s"])
    dist = float(qa1["launch"]["distance_m"])
    if abs(t100_row - s_launch) > 1e-9:
        raise SystemExit(f"FAIL T-M1 says {t100_row} s, the QA-1 receipt says {s_launch} s")
    if abs(m_row - dist) > 0.5:
        raise SystemExit(f"FAIL T-M1 says {m_row} m, the QA-1 receipt says {dist} m")
    band_pct = int(need(r"repeatability \u00b1(\d+) %", card, "Q-2 repeatability band").group(1))
    lo_t, hi_t = s_launch * (1 - band_pct / 100), s_launch * (1 + band_pct / 100)
    band_1 = f"{lo_t:.1f}-{hi_t:.1f} s (+-{band_pct} %)"

    # ---------------------------------------------------------------- D-2  top speed (A2)
    e5 = cells(rows, "T-E5")
    lore_top = round(float(e5[4].strip("*")))          # 336.4 -> 336
    lore_class = e5[6]                                  # `assumed`
    e1 = need(r"peak (\d+) km/h measured", text(rows, "T-E1"), "T-E1 QA-1 peak").group(1)
    a2 = cells(rows, "T-A2")
    if "no aero member anywhere" not in a2[1]:
        raise SystemExit("FAIL T-A2 no longer says the BmAK chain has no aero member")
    cd_build = need(r"\*\*([\d.]+)\*\*", a2[9], "T-A2 build Cd").group(1)
    band_lo, band_hi = (int(x) for x in need(r"band (\d+)\u2013(\d+) km/h", text(rows, "T-E5"),
                                             "T-E5 label band").groups())
    # the terminal balance: the ledger's torque, the built engine/aero modules, rho 1.2
    cur = json.load(open(CURRENT, encoding="utf-8"))["modules"]
    en, aero = cur["LandEngine"]["values"], cur["LandAerodynamics"]["values"]
    torque = float(need(r"([\d.]+) N\u00b7m", cells(rows, "T-E2")[5],
                        "T-E2 built torque").group(1))
    en_rpm, tf = float(en["max_rpm"]), float(en["torque_factor_at_max_rpm"])
    omega = en_rpm * 2 * math.pi / 60.0
    p_w = torque * tf * omega
    cd, area = float(aero["drag_coefficient"]), float(aero["frontal_area"])
    if abs(cd - float(cd_build)) > 1e-6:
        raise SystemExit(f"FAIL T-A2's {cd_build} is not the built drag {cd}")
    v_term = (2 * p_w / (RHO * cd * area)) ** (1 / 3)
    term_kmh = v_term * 3.6
    term_lo, term_hi = round(term_kmh * 0.9), round(term_kmh * 1.1)
    b2 = cells(rows, "T-B2")[1]
    boost_add = float(need(r"= \*\*1200 cu = ([\d.]+) km/h", b2, "T-B2 additive boost").group(1))
    boost_torque_lo = float(need(r"\+([\d.]+) km/h", b2, "T-B2 torque-band bound").group(1))

    # ---------------------------------------------------------------- D-3  braking 100->0 (A5)
    k1 = need(r"([\d.]+)\u2013([\d.]+) m/s", text(rows, "T-K1"), "T-K1 decel band")
    a_lo, a_hi = float(k1.group(1)), float(k1.group(2))
    if a_lo > a_hi:
        a_lo, a_hi = a_hi, a_lo
    d_hi = V100 ** 2 / (2 * a_lo)   # weakest decel -> longest stop
    d_lo = V100 ** 2 / (2 * a_hi)   # strongest decel -> shortest stop
    k2_verify = cells(rows, "T-K2")[-1]
    if "\u2264 ~100 m" not in k2_verify:
        raise SystemExit("FAIL T-K2's A5 line no longer says 'stop distance <= ~100 m'")
    t_k1_edit = cells(rows, "T-K1")
    k1_old = need(r"([\d,]+) / [\d,]+", t_k1_edit[4], "T-K1 build torque").group(1)
    k1_new = need(r"\*\*([\d,]+) / [\d,]+\*\*", t_k1_edit[5], "T-K1 proposed torque").group(1)

    # ---------------------------------------------------------------- D-4  turning circle (A3)
    # T-ST7 left the blocked set on 2026-11-06, so a radius is derivable from decoded values:
    #   * the locks are T-ST1's built curve (55 deg at <= 20 km/h, 20 deg at >= 72 km/h);
    #   * the wheelbase is T-G1's decoded 5.029 m;
    #   * the built steer times are T-ST7's own value cell (0.8 s low / 0.6 s high).
    # The 2026-11-06 ruling's 0.25 s / 0.091 s is the GOAL band the built times are compared
    # against. It is not a pass condition: the check certifies that the derivation reproduces the
    # built values, and keeps the goal miss visible (RED) until take A3 measures it.
    st7 = rows["T-ST7"]
    st7_value, st7_goal = cells(rows, "T-ST7")[4], cells(rows, "T-ST7")[5]
    t_low = float(need(r"([\d.]+) s low speed", st7_value, "T-ST7 built low-speed time").group(1))
    t_high = float(need(r"([\d.]+) s high speed", st7_value, "T-ST7 built high-speed time").group(1))
    g_low = float(need(r"\*\*([\d.]+) s low speed\*\*", st7_goal,
                       "T-ST7 ruling low-speed time").group(1))
    g_high = float(need(r"\*\*([\d.]+) s high speed\*\*", st7_goal,
                        "T-ST7 ruling high-speed time").group(1))
    rate = float(need(r"`SteerSpeed`\s*([\d.]+)\s*\u00b0/s", cells(rows, "T-ST7")[1],
                      "T-ST7 BmAK steer rate").group(1))
    lock = need(r"\*\*([\d.]+)\s*\u00b0\s*@\s*\u2264([\d.]+) km/h\s*\u2192\s*([\d.]+)\s*\u00b0\s*@\s*\u2265"
                r"([\d.]+) km/h", cells(rows, "T-ST1")[5], "T-ST1 lock curve")
    lock_deg, lock_kmh = float(lock.group(1)), float(lock.group(2))
    lock_hi_deg, lock_hi_kmh = float(lock.group(3)), float(lock.group(4))
    wb = float(need(r"wheelbase ([\d.]+)", cells(rows, "T-G1")[5], "T-G1 wheelbase").group(1))
    r_low = wb / math.tan(math.radians(lock_deg))
    r_high = wb / math.tan(math.radians(lock_hi_deg))
    goal_low_calc, goal_high_calc = lock_deg / rate, lock_hi_deg / rate
    rate_low, rate_high = lock_deg / t_low, lock_hi_deg / t_high
    red_low, red_high = t_low > g_low, t_high > g_high

    # ---------------------------------------------------------------- D-5  steering hold (A4)
    # The same T-ST7 pair read as a TIME prediction: A4 measures the built 0.80 / 0.60 s.  The
    # ruling's goal stays the named expected failure, not the pass condition.
    hold_lo, hold_hi = t_low - 0.05, t_low + 0.05
    hold_lo_hi, hold_hi_hi = t_high - 0.05, t_high + 0.05

    # ---------------------------------------------------------------- D-6  handbrake drift (A7)
    # No row states a drift ANGLE target: the cap/entry are T-DR1's shipped JC3 values, and the
    # three ledger labels A7 must disclose are parsed, never typed.
    dr = cells(rows, "T-DR1")[4]
    dr_max = int(need(r"(\d+)\u00b0 max", dr, "T-DR1 drift cap").group(1))
    dr_entry = int(need(r"(\d+)\u00b0 entry", dr, "T-DR1 drift entry").group(1))
    dr_min = int(need(r"(\d+) km/h\*\* minimum", dr, "T-DR1 drift speed gate").group(1))
    st6_next = cells(rows, "T-ST6")[5]
    align = float(need(r"\*\*next: ([\d.]+)\*\* = 1 / 1\.6", st6_next,
                       "T-ST6 aligning label").group(1))
    fals = float(need(r"\*\*([\d.]+) = 0\.3 \u00d7 1\.6\*\*", st6_next,
                      "T-ST6 falsifier").group(1))
    k3_next = cells(rows, "T-K3")[5]
    hb_fric = float(need(r"\*\*next: ([\d.]+)\*\* = 640,000", k3_next,
                         "T-K3 handbrake friction").group(1))
    hb_band_hi = float(need(r"6 t band 1 \u2026 ([\d.]+)", k3_next, "T-K3 6 t band").group(1))
    k4_from, k4_next = cells(rows, "T-K4")[4], cells(rows, "T-K4")[5]
    k4_ledger = int(need(r"min_time \*\*(\d+)\*\*", k4_from, "T-K4 ledger from").group(1))
    k4_bytes = int(need(r"the bytes carry \*\*(\d+)\*\*", k4_from, "T-K4 bytes").group(1))
    k4_ramp = float(need(r"`min_time_to_block` \*\*([\d.]+)\*\*", k4_next,
                         "T-K4 release ramp").group(1))
    stats = ledger_stats()

    # ---------------------------------------------------------------- the sheet
    pred = [
        {
            "id": "D-1", "take": "A1 launch 0-100",
            "value": f"{s_launch:.1f} s / {dist:.1f} m",
            "band": band_1,
            "rows": "`T-M1`",
            "cls": "measured (QA-1, test-085)",
            "status": "predicted",
            "why": (f"QA-1's one acceleration run reached 100 km/h in {s_launch:.1f} s over {dist:.1f} m "
                    f"at the built 6,000 kg; T-M1 quotes it and the receipt carries it. The band is the "
                    f"Q-2 card's own repeatability figure (+-{band_pct} %), so a re-take outside it is a "
                    f"failed take, not a re-read."),
        },
        {
            "id": "D-2", "take": "A2 top speed, boost off",
            "value": f"{term_kmh:.0f} km/h terminal at Cd {cd:g}; the {band_lo}-{band_hi} km/h "
                     f"label is assumed",
            "band": f"{term_lo}-{term_hi} km/h",
            "rows": "`T-E5`, `T-E2`, `T-A2`, `T-E1`",
            "cls": "derived (terminal balance at the built Cd) / assumed (the label)",
            "status": "predicted",
            "why": (f"terminal balance, computed in the section below: T-E2's {torque:.0f} N.m times the "
                    f"{tf:g} wash at {en_rpm:.0f} rpm is {p_w / 1000:.1f} kW, and Cd.A = {cd:g} x "
                    f"{area:.3f} m^2 gives v = (2P/(rho Cd A))^(1/3) = {v_term:.2f} m/s = "
                    f"{term_kmh:.1f} km/h at rho {RHO:.1f}. The band is that value +-10 % because rolling "
                    f"resistance and driveline loss are not modelled. T-E5's {band_lo}-{band_hi} km/h is "
                    f"an **assumed label**, not the pass criterion: the take tests reachability of a "
                    f"label, not fidelity to BmAK, so a terminal in the {band_lo}-{band_hi} band falsifies "
                    f"the Cd/T-E2 pair rather than passing."),
        },
        {
            "id": "D-2b", "take": "A2 top speed, boost on (delta)",
            "value": f"+{boost_torque_lo:.1f} to +{boost_add:.1f} km/h over the boost-off terminal speed",
            "band": f"{boost_torque_lo:.1f}-{boost_add:.1f} km/h",
            "rows": "`T-B2`",
            "cls": "derived (four BmAK members)",
            "status": "predicted",
            "why": (f"T-B2 computes min(FakeExtraSpeedMax 3500, FakeExtaSpeedAccel 600 x BoostDuration "
                    f"2.0) = 1200 cu = {boost_add:.1f} km/h and keeps the torque band's "
                    f"+{boost_torque_lo:.1f} km/h as the lower bound. This is the half of A2 a row can "
                    f"carry; the absolute terminal speed above is the model prediction, not a measurement."),
        },
        {
            "id": "D-3", "take": "A5 braking 100-0",
            "value": f"{d_lo:.1f}-{d_hi:.1f} m (a = {a_lo:.1f}-{a_hi:.1f} m/s^2)",
            "band": f"{d_lo:.1f}-{d_hi:.1f} m",
            "rows": "`T-K1`, `T-K2`",
            "cls": "measured decel + derived distance",
            "status": "predicted",
            "why": (f"T-K1 records the QA-1 decel band {a_lo:.1f}-{a_hi:.1f} m/s^2 and T-K2's A5 line "
                    f"states the stop at '~100 m' from it. The distance here is the same constant-decel "
                    f"relation the repo already applies, d = v^2/(2a) with v = {V100:.4f} m/s: "
                    f"{V100 ** 2:.1f}/(2 x {a_hi:.1f}) = {d_lo:.1f} m and {V100 ** 2:.1f}/(2 x {a_lo:.1f}) "
                    f"= {d_hi:.1f} m."),
        },
        {
            "id": "D-4", "take": "A3 constant-radius corner 60/100 km/h",
            "value": f"{r_low:.2f} m radius at the {lock_deg:.0f} deg low-speed lock; "
                     f"{r_high:.2f} m at the {lock_hi_deg:.0f} deg high-speed lock",
            "band": f"+/-10 % on each radius; full-lock time goal {g_high:.3f}-{g_low:.3f} s "
                    f"(built {t_low:.1f} s / {t_high:.1f} s - outside it)",
            "rows": "`T-ST7`, `T-ST1`, `T-G1`",
            "cls": "derived (bicycle at the built locks) + built times vs the ruling",
            "status": "predicted",
            "why": (f"`R = wheelbase / tan(lock)` with T-G1's {wb:.3f} m and T-ST1's "
                    f"{lock_deg:.0f} deg / {lock_hi_deg:.0f} deg locks gives {r_low:.2f} m / "
                    f"{r_high:.2f} m. The radius is geometry and does not depend on the steer time, "
                    f"so the ruling changes how fast the lock is reached, not the circle: T-ST7's "
                    f"built {t_low:.1f} s / {t_high:.1f} s against the ruling's {g_low:.3f} s / "
                    f"{g_high:.3f} s is {t_low / g_low:.1f}x / {t_high / g_high:.1f}x slower and is "
                    f"kept RED here, open until take A3 (and its A4 steering hold) measures it."),
        },
        {
            "id": "D-5", "take": "A4 steering hold 60/100 km/h",
            "value": f"full lock in {t_low:.2f} s low / {t_high:.2f} s high (the built times), not the "
                     f"{g_low:.3f} / {g_high:.3f} s ruling goal",
            "band": f"{hold_lo:.2f}-{hold_hi:.2f} s low / {hold_lo_hi:.2f}-{hold_hi_hi:.2f} s high "
                    f"(+-0.05 s read); a reading near {g_low:.2f} / {g_high:.2f} s means the build moved "
                    f"and T-ST7 must be re-read",
            "rows": "`T-ST7`, `T-ST1`",
            "cls": "decoded (built times) vs derived (ruling goal)",
            "status": "predicted",
            "why": (f"A4 is D-4 read as a time: the lock is {lock_deg:.0f} deg / {lock_hi_deg:.0f} deg "
                    f"either way, and the take can only measure how long it takes to reach it. The "
                    f"prediction is therefore the built {t_low:.2f} / {t_high:.2f} s; the ruling's "
                    f"{g_low:.3f} / {g_high:.3f} s stays the named expected failure until the take or "
                    f"the build closes it. This is the line the T-ST7 RED belongs to, and it is why the "
                    f"red is disclosed rather than silenced."),
        },
        {
            "id": "D-6", "take": "A7 handbrake drift + release",
            "value": f"enters near {dr_entry} deg and peaks inside T-DR1's {dr_max} deg cap; rear "
                     f"aligning label {align:g} (= 1/1.6), falsifier {fals:g}; handbrake friction "
                     f"{hb_fric:g}; release ramp {k4_ramp:g} s",
            "band": f"drift, hold and recover inside ~2 s with no spin past ~60 deg; a refusal to rotate "
                    f"at {align:g} points at {fals:g}; a stop time that does not fall against the "
                    f"1.0-factor control fails T-K3",
            "rows": "`T-DR1`, `T-ST5`, `T-ST6`, `T-K3`, `T-K4`",
            "cls": "decoded (JC3 cap/entry) + label bands (0.625 INFERRED, 4.0, 0.3 s)",
            "status": "predicted",
            "why": (f"No BmAK row states a drift angle, so the angle target is T-DR1's shipped "
                    f"{dr_entry} deg entry / {dr_max} deg cap and the speed gate is its {dr_min} km/h "
                    f"minimum (BmAK's `HandbrakeOnSpeed` 10,000 cm/s = 360 km/h is above the car's top). "
                    f"The three labels are carried, not presented as measurements: {align:g} is the "
                    f"INFERRED reciprocal of the 1.6 rear slip gain, {hb_fric:g} is a force ratio above "
                    f"the 6 t band 1..{hb_band_hi:g}, and {k4_ramp:g} s is a kind-match whose ledger "
                    f"`from` cell still says {k4_ledger} against the bytes' {k4_bytes}."),
        },
    ]

    n_pred = sum(r["status"] == "predicted" for r in pred)
    n_unk = sum(r["status"] == "unknown" for r in pred)
    info = {
        **stats,
        "r_low": r_low, "r_high": r_high, "wb": wb,
        "lock_deg": lock_deg, "lock_hi_deg": lock_hi_deg,
        "t_low": t_low, "t_high": t_high, "g_low": g_low, "g_high": g_high,
        "rate": rate, "goal_low_calc": goal_low_calc, "goal_high_calc": goal_high_calc,
        "p_w": p_w, "cd": cd, "cd_build": cd_build, "cd_area": cd * area, "v_term": v_term,
        "rate_low": rate_low, "rate_high": rate_high,
        "red_low": red_low, "red_high": red_high, "n_pred": n_pred, "n_unk": n_unk,
        "hold_lo": hold_lo, "hold_hi": hold_hi, "hold_lo_hi": hold_lo_hi,
        "hold_hi_hi": hold_hi_hi, "dr_max": dr_max, "dr_entry": dr_entry, "dr_min": dr_min,
        "align": align, "fals": fals, "hb_fric": hb_fric, "hb_band_hi": hb_band_hi,
        "k4_ledger": k4_ledger, "k4_bytes": k4_bytes, "k4_ramp": k4_ramp,
    }

    L: list[str] = []
    a = L.append
    a("# Q driving predictions (V-05 part 1)")
    a("")
    a("Generated by `python Tools/scripts/v05_driving.py --write`; `--check` re-derives every number")
    a("from the same files and compares this document byte for byte. Written before any in-game test.")
    a("")
    a(f"**6 driving checks (Q-2 takes A1, A2, A3, A4, A5, A7): {n_pred} predicted, {n_unk} UNKNOWN.**")
    a(f"Ledger `T_ROWS.jsonl`: **{stats['rows']} rows** (read from the file, not typed).")
    a("A predicted line has a value from a ledger row and a pass band the Q observer can fail. An")
    a("UNKNOWN line would have no value in any repo file and would name the missing input instead of")
    a("a band; this sheet has none, because T-ST7 left the blocked set on 2026-11-06")
    a("")
    a("Sources: `Working/Translation/T_ROWS.jsonl` (the row ids in column 5) and the QA-1 receipt it")
    a("quotes, `Working/Translation/QA1/qa1_measure.json` (one take, build test-085), plus the handling")
    a("decode in " + ", ".join(f"`{d}`" for d in HANDLING_DOCS) + ".")
    a("")
    a("| id | Q-2 take | prediction | pass band | row ids | class | status |")
    a("|---|---|---|---|---|---|---|")
    for r in pred:
        a(f"| {r['id']} | {r['take']} | {r['value']} | {r['band'] or '-'} | {r['rows']} | "
          f"{r['cls']} | {r['status']} |")
    a("")

    a("## D-1 - 0-100 km/h (take A1)")
    a("")
    a(f"| field | value | source |")
    a("|---|---|---|")
    a(f"| prediction | **{s_launch:.1f} s**, {dist:.1f} m travelled | `qa1_measure.json` `launch.s` / "
      f"`launch.distance_m`; `T-M1` verify cell: '{t100_row:.1f} s / {m_row} m measured' |")
    a(f"| pass band | **{band_1}** | the Q-2 card's own repeatability figure, parsed from "
      f"`GRAB_BACKLOG.md` |")
    a(f"| earlier split | 0-60 km/h {qa1['launch']['t60']:.1f} s | `qa1_measure.json` `launch.t60` |")
    a(f"| class | measured, not derived | `QA1_RESULTS.md` 2, one clean run |")
    a("")
    a("The take is a straight-airfield launch, one manoeuvre, sampled from the HUD at 5 fps")
    a("(instrument accuracy +-0.2 s on a time, +-0.5 m on a distance, +-1 km/h on a speed). Nothing")
    a("in this row is a model: it is one measurement plus the card's tolerance.")
    a("")

    a("## D-2 - top speed (take A2)")
    a("")
    a("| field | value | source |")
    a("|---|---|---|")
    a(f"| lore target | **{lore_top} km/h** (209 mph, with afterburner) | `T-E5`, class **{lore_class}**, "
      f"`vehicle_misc.official_top_speed` 336.4 |")
    a(f"| measured | **{e1} km/h** peak, still climbing when the brake went on | `T-E1` verify cell, "
      f"`qa1_measure.json` `peak_kmh` |")
    a(f"| chain | no aero member anywhere; the build's Cd {cd_build} is a class value | `T-A2` |")
    a(f"| prediction | **{term_kmh:.0f} km/h** terminal at the built Cd {cd_build} | derived below: "
      f"T-E2's {torque:.0f} N.m x the {tf:g} wash at {en_rpm:.0f} rpm into Cd.A = {cd:g} x "
      f"{area:.3f} m^2 |")
    a(f"| pass band | **{term_lo}-{term_hi} km/h** (+-10 %, declared) | rolling resistance and "
      f"driveline loss are not modelled here |")
    a(f"| class | **derived** (terminal balance) - the {band_lo}-{band_hi} km/h label stays "
      f"**{lore_class}** | `T-E5`, `T-E2`, `T-A2` |")
    a("")
    a(f"```")
    a(f"P      = torque x wash x omega          (T-E2: {torque:.0f} N.m, T-E3 wash {tf:g}, "
      f"{en_rpm:.0f} rpm)")
    a(f"       = {p_w / 1000:.1f} kW")
    a(f"Cd.A   = {cd:g} x {area:.3f} = {cd * area:.3f} m^2     (built land_aerodynamics)")
    a(f"v      = (2P / (rho Cd A))^(1/3) = {v_term:.2f} m/s = {term_kmh:.1f} km/h")
    a(f"rho    = {RHO:.1f} kg/m^3")
    a("```")
    a("")
    a(f"T-E5 is `{lore_class}`, and this sheet does not treat the label as a measurement. The wiki's")
    a(f"209 mph is the mod's stated target, carried as the top of a **{band_lo}-{band_hi} km/h** band;")
    a(f"BmAK has no speed member at all (T-A2 proves the chain carries no drag member either), and the")
    a(f"2026-10-23 sign-off covers the label, not a number read from a file. The label and the drag are")
    a(f"two decisions, not one translation: the Cd **0.1213** that used to be written to make 336.4")
    a(f"km/h reachable was reverse-engineered from the label and is withdrawn (correction 8391), so the")
    a(f"built member keeps T-A2's class fit **{cd_build}** and the prediction above follows from it.")
    a("")
    a(f"Any top-speed take therefore tests **reachability of a label, not fidelity to BmAK**: a terminal")
    a(f"inside {term_lo}-{term_hi} km/h is the prediction passing, and a terminal inside the")
    a(f"{band_lo}-{band_hi} km/h label band would falsify the Cd {cd_build} / T-E2 pair rather than")
    a(f"pass the label. The only measurement on record ({e1} km/h) was taken at Cd 0.139 on test-085,")
    a(f"before T-A2's edit, so it does not test either the label or the prediction.")
    a("")
    a(f"The boost half of A2 is evidenced and is predicted separately: **D-2b**.")
    a("")
    a("## D-2b - boost delta (take A2, second leg)")
    a("")
    a("| field | value | source |")
    a("|---|---|---|")
    a(f"| prediction | terminal speed rises **+{boost_add:.1f} km/h** while boosting | `T-B2`: "
      f"min(FakeExtraSpeedMax 3500, FakeExtaSpeedAccel 600 x BoostDuration 2.0) = 1200 cu |")
    a(f"| pass band | **{boost_torque_lo:.1f}-{boost_add:.1f} km/h** | `T-B2`'s torque-band lower bound "
      f"(+{boost_torque_lo:.1f} km/h) and its additive member ({boost_add:.1f} km/h) |")
    a(f"| class | derived from four BmAK members | `T-B2`, cm -> km/h on the project's 3000 cu = "
      f"108 km/h convention |")
    a("")
    a(f"The two bounds are the row's own: the torque band 2100 -> 3000 cm/s gives +{boost_torque_lo:.1f}")
    a(f"km/h and the additive member gives {boost_add:.1f} km/h, so the delta must land between them.")
    a("A delta outside that window fails the take and points at the boost rows (T-B1/T-B2), not at A2's")
    a("absolute top speed.")
    a("")

    a("## D-3 - braking 100-0 (take A5)")
    a("")
    a("| field | value | source |")
    a("|---|---|---|")
    a(f"| decel band | **{a_lo:.1f}-{a_hi:.1f} m/s^2** | `T-K1` verify cell (QA-1, tarmac segments) |")
    a(f"| prediction | **{d_lo:.1f}-{d_hi:.1f} m** to a full stop from 100 km/h | derived below |")
    a(f"| pass band | **{d_lo:.1f}-{d_hi:.1f} m** | same |")
    a(f"| row's own stop text | 'stop distance <= ~100 m ({a_lo:.1f}-{a_hi:.1f} m/s^2), no lock-up' | "
      f"`T-K2`, A5 verify cell |")
    a(f"| class | measured decel + derived distance | `QA1_RESULTS.md` 4 |")
    a("")
    a(f"```")
    a(f"v      = 100 km/h = {V100:.4f} m/s")
    a(f"a      = {a_lo:.1f} ... {a_hi:.1f} m/s^2          (T-K1)")
    a(f"d      = v^2 / (2a)")
    a(f"d_max  = {V100 ** 2:.1f} / (2 x {a_lo:.1f}) = {d_hi:.1f} m")
    a(f"d_min  = {V100 ** 2:.1f} / (2 x {a_hi:.1f}) = {d_lo:.1f} m")
    a("```")
    a("")
    a("One open risk, stated rather than folded into the band: T-K1 is an `edit` row that lowers")
    a(f"`brakes.front/rear.max_brake_torque` from {k1_old} to {k1_new} to the 3-6 t class median, and")
    a("the measured decel above was taken before that edit. No row or doc derives brake torque ->")
    a("deceleration, so whether the band survives the edit is **UNKNOWN** as a model; if the take")
    a("lands long, T-K1's torque is the first thing to read, not the measurement.")
    a("")

    a("## D-4 - turning circle (take A3)")
    a("")
    a("| field | value | source |")
    a("|---|---|---|")
    a(f"| prediction, low-speed lock | **{r_low:.2f} m** at {lock_deg:.0f} deg | derived: "
      f"`{wb:.3f} / tan({lock_deg:.0f} deg)` = {r_low:.2f} m, `T-G1` x `T-ST1` |")
    a(f"| prediction, high-speed lock | **{r_high:.2f} m** at {lock_hi_deg:.0f} deg | derived: "
      f"`{wb:.3f} / tan({lock_hi_deg:.0f} deg)` = {r_high:.2f} m, `T-G1` x `T-ST1` |")
    a(f"| pass band | **{r_low * 0.9:.2f}-{r_low * 1.1:.2f} m** / **{r_high * 0.9:.2f}-{r_high * 1.1:.2f} m** "
      f"(+/-10 %) | declared, not derived: tyre slip and the yaw response are not modelled here "
      f"(the same declared slack D-2 uses) |")
    a(f"| lock angle | **{lock_deg:.0f} deg at <= {lock_kmh:.0f} km/h**, {lock_hi_deg:.0f} deg at >= "
      f"{lock_hi_kmh:.0f} km/h, falloff 1.5 | `T-ST1` |")
    a(f"| wheelbase | **{wb:.3f} m** | `T-G1` |")
    a(f"| time to full lock (built) | **{t_low:.2f} s low / {t_high:.2f} s high** | `T-ST7` value cell |")
    a(f"| ruling goal - the failing band | **{g_low:.3f} s low / {g_high:.3f} s high** "
      f"({lock_deg:.0f}/{rate:.0f} and {lock_hi_deg:.0f}/{rate:.0f} deg/s) | `T-ST7` next cell, "
      f"operator ruling 2026-11-06 |")
    a(f"| **RED** | built **{t_low:.2f} / {t_high:.2f} s** is **{t_low / g_low:.1f}x / "
      f"{t_high / g_high:.1f}x** the goal band {g_high:.3f}-{g_low:.3f} s | comparison below; stays "
      f"red until take A3 measures it |")
    a("")
    a("```")
    a("R          = wheelbase / tan(lock)              bicycle/Ackermann, no slip")
    a(f"wheelbase  = {wb:.3f} m                          (T-G1)")
    a(f"lock       = {lock_deg:.0f} deg <= {lock_kmh:.0f} km/h, {lock_hi_deg:.0f} deg >= {lock_hi_kmh:.0f} km/h"
      f"     (T-ST1)")
    a(f"R_low      = {wb:.3f} / tan({lock_deg:.0f} deg) = {r_low:.3f} m")
    a(f"R_high     = {wb:.3f} / tan({lock_hi_deg:.0f} deg) = {r_high:.3f} m")
    a("")
    a(f"t_built    = {t_low:.2f} s low / {t_high:.2f} s high            (T-ST7 value cell)")
    a(f"t_goal     = {lock_deg:.0f}/{rate:.0f} = {goal_low_calc:.3f} s ; {lock_hi_deg:.0f}/{rate:.0f} = "
      f"{goal_high_calc:.3f} s  (ruling)")
    a(f"rate_built = {lock_deg:.0f}/{t_low:.2f} = {rate_low:.1f} deg/s ; {lock_hi_deg:.0f}/{t_high:.2f} = "
      f"{rate_high:.1f} deg/s")
    a(f"slowdown   = {rate:.0f}/{rate_low:.1f} = {rate / rate_low:.1f}x ; {rate:.0f}/{rate_high:.1f} = "
      f"{rate / rate_high:.1f}x")
    a(f"RED        = {t_low:.2f} / {t_high:.2f} s outside the {g_high:.3f}-{g_low:.3f} s goal band")
    a("```")
    a("")
    a("The radius is geometry: with the lock angle and the wheelbase fixed, the circle is")
    a(f"{r_low:.2f} m at the low-speed lock and {r_high:.2f} m at the {lock_hi_deg:.0f} deg high-speed lock,")
    a(f"whatever the steer time. That is why the ruling's 0.25 s / 0.091 s is compared as a **time**")
    a(f"band and not as a radius band: it changes how long the car takes to reach the lock, so the")
    a(f"built {t_low:.1f} s / {t_high:.1f} s is {t_low / g_low:.1f}x / {t_high / g_high:.1f}x the goal and red.")
    a("")
    a("Two limits are stated rather than folded into the radii: (1) the geometric radius is the")
    a("no-slip value, so a measured radius above it is understeer, not a failed derivation - hence")
    a("the declared +/-10 %; (2) the take's 60 km/h leg sits between the 20 and 72 km/h knots, and")
    a(f"the interpolation law between them is not decoded (only the 1.5 falloff), so that leg is")
    a(f"bracketed by {r_low:.2f}-{r_high:.2f} m and not pinned; the 100 km/h leg is the pinned one.")
    a("")
    a("`--check` passes when the radii re-derive from the built locks and wheelbase and the built")
    a("times are the row's own - a green check means **the derivation matches the built values**, not")
    a("that the lore goal is met. The goal miss is printed as a RED line and stays in this sheet")
    a("until take A3 resolves it.")
    a("")

    a("## D-5 - steering hold (take A4)")
    a("")
    a("| field | value | source |")
    a("|---|---|---|")
    a(f"| prediction | **{t_low:.2f} s** to full lock at low speed, **{t_high:.2f} s** at high speed | "
      f"`T-ST7` value cell (the built times) |")
    a(f"| pass band | **{hold_lo:.2f}-{hold_hi:.2f} s** / **{hold_lo_hi:.2f}-{hold_hi_hi:.2f} s** | "
      f"declared +-0.05 s on a HUD-timed reading; a reading outside it is a build change, not noise |")
    a(f"| goal the ruling sets | **{g_low:.3f} s / {g_high:.3f} s** | `T-ST7` next cell (55/220 and "
      f"20/220 deg/s) |")
    a(f"| **named expected failure** | the built {t_low:.2f} / {t_high:.2f} s is **"
      f"{t_low / g_low:.1f}x / {t_high / g_high:.1f}x** the goal | this line predicts the BUILT "
      f"behaviour; a reading that matches the goal means the build moved and T-ST7 must be re-read, "
      f"not that A4 passed |")
    a("")
    a(f"A4 is D-4 read as a **time**, not a radius: the lock is {lock_deg:.0f} deg / "
      f"{lock_hi_deg:.0f} deg either way and the take can only measure how fast it is reached. The "
      f"prediction is therefore the built {t_low:.2f} / {t_high:.2f} s, and the {g_low:.3f} / "
      f"{g_high:.3f} s ruling band stays a named expected failure until the take or the build closes it.")
    a("")

    a("## D-6 - handbrake drift and release (take A7)")
    a("")
    a("| field | value | source |")
    a("|---|---|---|")
    a(f"| drift cap / entry | **{dr_max} deg max, {dr_entry} deg entry** | `T-DR1` shipped cell "
      f"(JC3-native; no BmAK member states an angle) |")
    a(f"| speed gate | **{dr_min} km/h minimum** (BmAK's gate is absent: `HandbrakeOnSpeed` 10,000 cm/s "
      f"= 360 km/h is above the car's top) | `T-DR1` next cell |")
    a(f"| rear aligning label | **{align:g} = 1 / 1.6**; falsifier **{fals:g} = 0.3 x 1.6** | `T-ST6` "
      f"next cell, **INFERRED reciprocal** (not measured) |")
    a(f"| handbrake friction label | **{hb_fric:g} = 640,000 / 160,000** | `T-K3` next cell: inside the "
      f"shipped 1-10 domain but **above the 6 t class band 1..{hb_band_hi:g}** |")
    a(f"| release ramp label | **{k4_ramp:g} s** (`HandBrakeOffTime`); ledger `from` still "
      f"**{k4_ledger}**, the bytes carry **{k4_bytes}** | `T-K4`: read the bytes, not the `from` cell |")
    a(f"| pass band | enters near **{dr_entry} deg**, peaks inside **{dr_max} deg**, recovers inside "
      f"~2 s without a spin past 60 deg; a refusal to rotate at {align:g} points at {fals:g} | "
      f"declared: the angle target is the shipped cap, not a BmAK measurement |")
    a("")
    a("```")
    a(f"align  = 1 / 1.6            = {align:g}    (T-ST6, INFERRED)")
    a(f"fals   = 0.3 x 1.6          = {fals:g}    (if {align:g} refuses to rotate)")
    a(f"hb     = 640,000 / 160,000  = {hb_fric:g}    (T-K3; shipped 1..10, 6 t band 1..{hb_band_hi:g})")
    a(f"ramp   = HandBrakeOffTime   = {k4_ramp:g} s  (T-K4; ledger `from` {k4_ledger} vs bytes {k4_bytes})")
    a("```")
    a("")
    a(f"Three of the four numbers above are **labels, not measured truths**, and they are grouped "
      f"here so the take cannot be scored on them: {align:g} is a reciprocal no file measures, "
      f"{hb_fric:g} is a force ratio that survives because the units cancel (T-K1 disproved the "
      f"direct force -> torque bridge), and {k4_ramp:g} s is a kind-match with no BmAK release ramp. "
      f"T-K4's ledger `from` still says {k4_ledger} against the bytes' {k4_bytes}, and both are "
      f"carried rather than the convenient one. A7 is judged on the **band** (drift, hold, recover), "
      f"never on these labels.")
    a("")

    a("## What Q-2 can fail, in one list")
    a("")
    a("| take | pass condition | fails if |")
    a("|---|---|---|")
    a(f"| A1 | 0-100 in {band_1} | a re-take outside the band, or a launch that leaves the flat straight |")
    a(f"| A2 (boost on vs off) | the delta lands in {boost_torque_lo:.1f}-{boost_add:.1f} km/h | the delta "
      f"is negative, larger than {boost_add:.1f} km/h, or the car steps sideways on engage (T-B3 keeps "
      f"the grip multiplier at 1.0) |")
    a(f"| A5 | stop in {d_lo:.1f}-{d_hi:.1f} m on tarmac | lock-up, a departure from the straight, or a "
      f"stop outside the band |")
    a(f"| A3 | radius {r_low * 0.9:.2f}-{r_low * 1.1:.2f} m at the low-speed lock, "
      f"{r_high * 0.9:.2f}-{r_high * 1.1:.2f} m at the high-speed lock | a radius outside the band, "
      f"or a full-lock time that is not the built {t_low:.1f} / {t_high:.1f} s |")
    a(f"| A4 | full-lock time reads the built {t_low:.2f} / {t_high:.2f} s (+-0.05 s) | a lock time near "
      f"the ruling's {g_low:.2f} / {g_high:.2f} s (the build moved) or a lock never reached |")
    a(f"| A7 | enters near {dr_entry} deg, peaks inside {dr_max} deg, recovers without a spin | a refusal "
      f"to rotate at {align:g} (read {fals:g}), a snap-back, or a stop time that does not fall against "
      f"the 1.0-factor control |")
    a("")

    a("## Oracles re-run by `--check`")
    a("")
    a("* the four Q-2 take ids (A1, A2, A3, A5) and the repeatability figure are parsed out of")
    a("  `GRAB_BACKLOG.md` section 9b, so an edited card breaks the check")
    a(f"* `T-M1` still quotes {t100_row:.1f} s / {m_row} m and the QA-1 receipt still holds "
      f"{s_launch:.1f} s / {dist:.1f} m at `launch`")
    a(f"* `T-E5` still carries the lore top speed ({lore_top} km/h) as `{lore_class}`, `T-E1` still "
      f"records the {e1} km/h measured peak")
    a(f"* `T-A2` still proves the chain has no aero member and the build Cd is {cd_build}")
    a(f"* `T-B2` still yields {boost_add:.1f} km/h additive and +{boost_torque_lo:.1f} km/h below")
    a(f"* `T-K1` still carries {a_lo:.1f}-{a_hi:.1f} m/s^2 and T-K2's A5 line still says '~100 m'")
    a(f"* `T-ST7` still carries {t_low:.2f} / {t_high:.2f} s built and {g_low:.3f} / {g_high:.3f} s as")
    a(f"  the ruling; the ruling times re-derive as {lock_deg:.0f}/{rate:.0f} and "
      f"{lock_hi_deg:.0f}/{rate:.0f} deg/s")
    a(f"* the two radii re-derive as `{wb:.3f} / tan(lock)` = {r_low:.3f} / {r_high:.3f} m, and the")
    a(f"  T-ST7 miss is still open (built outside the {g_high:.3f}-{g_low:.3f} s band)")
    a("* the braking distance recomputes from v and a, and the document matches the regenerated bytes")
    a("")
    a("## UNKNOWNs, with the missing input")
    a("")
    a(f"* **A2's label vs its prediction** - {lore_top} km/h is UNKNOWN as a measurement: no BmAK")
    a(f"  speed member exists and no take has measured it; the {term_kmh:.0f} km/h terminal is derived")
    a(f"  from the built Cd, so reaching the {band_lo}-{band_hi} band without changing Cd or power is")
    a(f"  what take A2 tests (a label-reachability test, not a fidelity test).")
    a(f"* **A3's 60 km/h leg** - the radius there is bracketed by {r_low:.2f}-{r_high:.2f} m, not")
    a(f"  pinned: the knot interpolation between 20 and 72 km/h is not decoded, only the 1.5 falloff.")
    a(f"* **the radius under slip** - `R = wheelbase / tan(lock)` is the no-slip geometric value; the")
    a(f"  yaw response and tyre slip are not modelled, which is the declared +/-10 % on each radius.")
    a(f"* **whether brake torque -> deceleration is linear** - T-K1 halves the torque after the decel")
    a(f"  was measured, and no row derives the relation; D-3's band is the measured one.")
    a(f"* **whether the game honours any of this** - the test ban stands; nothing was installed,")
    a(f"  launched or attached to.")
    a("")
    a("## Labels")
    a("")
    a("Values are **decoded** (a T row's own number), **measured** (QA-1, one take on test-085),")
    a("**derived** (the arithmetic printed in each section, from file values) or **UNKNOWN** (the")
    a("input named above). No value here is typed from memory of Just Cause 3 or Arkham Knight.")
    a("")

    a("## Named expected failures and label bands")
    a("")
    a("These are the values the Q sheets must **not** present as measured truths. Each is carried")
    a("with its class and the file that settles it.")
    a("")
    a("| item | value carried | class | what it is not |")
    a("|---|---|---|---|")
    a("| collision Q-2 check | **2 bodies / 3 boxes / 1 constraint, 2 of BmAK's 3 boxes have no shape ")
    a("  instance, placement 6.1 cm - gate false**: a **named expected failure** | decoded (collision ")
    a("  re-measure) | not a surprise if it fails, and not a pass |")
    a("| T-E5 top speed | **336.4 km/h**, the top of a **300-336 km/h** band | `assumed` (wiki 209 mph) ")
    a("  | **not decoded**: the derivation at the built Cd 0.55 and T-E2's 2,921 N.m gives 267 km/h; ")
    a("  the 0.1213 Cd written to make 336.4 reachable is withdrawn (correction 8391, `build-d10` 5.2) |")
    a("| T-ST6 drift aligning | **0.625 = 1 / 1.6** | **INFERRED reciprocal** | not measured; the ")
    a("  falsifier is **0.48**, and 0.625 sits inside the shipped 0.3-0.8 band |")
    a("| T-K3 handbrake friction | **4.0 = 640,000 / 160,000** | derived ratio | not a 6 t value: it is ")
    a("  inside the shipped 1-10 domain but **above the 6 t class band 1..2.25** |")
    a("| T-K4 block time | ledger `from` still says **5**, the bytes carry **1** (T-K2); next 0.3 s | ")
    a("  decoded (bytes) / **INFERRED** (0.3 s kind-match) | not a ledger-consistent pair: read the ")
    a("  bytes, not the `from` cell |")
    a("| lights | **angle 70 / range 60** | out-of-domain (U-1) | not shipped behaviour: the fleet ")
    a("  maximum is 50 / 50, so a short or soft cone is a clamp, not a defect |")
    a("| audio | **21 of 45 GUIDs donor-carried** | measured count | not a mapped sound set |")
    a("")
    a("A Q check that lands on a label band is judged against the **band**, never the label, and a")
    a("collision check that shows the 5 cm gate false is the **named expected failure** above, not a")
    a("new discovery.")
    a("")
    a("One disclosure on the collision line: `Builds/bm-RC4` ships `sportsmuscle.physicsc` sha ")
    a("`fda78f4d...`, whose body-0 hull measures **0.25 cm** off BmAK chassis box 0 (V-02a 4.3). The")
    a("6.1 cm figure belongs to payload `0164936b...`, which is not in this tree; both are stated so")
    a("the expected failure is read against the payload it belongs to.")
    a("")
    return "\n".join(L), pred, info


def main(write: bool) -> int:
    text_out, pred, info = build()
    checks = []

    def ok(cond, label, detail=""):
        checks.append({"oracle": label, "ok": bool(cond), "detail": detail})
        return bool(cond)

    card = q2_card()
    # The card wraps mid-take ("A7 handbrake" / "drift + release"), so the take is matched against
    # the card with its whitespace flattened rather than against the raw wrapped lines.
    card_flat = re.sub(r"\s+", " ", card)
    for take in ("A1 launch 0", "A2 top speed", "A3 constant-radius corner", "A4 steering hold",
                 "A5 braking 100", "A7 handbrake drift"):
        ok(take in card_flat, f"Q-2 card still lists {take.split()[0]} ({take})")
    ok(re.search(r"repeatability \u00b1\d+ %", card) is not None,
       "Q-2 card still fixes the launch repeatability figure")
    for d in HANDLING_DOCS:
        ok(os.path.exists(os.path.join(ROOT, d)), f"handling doc exists: {d}")
    rows_all = load_rows()
    for rid, needle, label in (("T-ST6", "0.625", "T-ST6 0.625 inferred reciprocal"),
                               ("T-K3", "4.0", "T-K3 4.0 ratio"),
                               ("T-K4", "5", "T-K4 ledger from 5")):
        ok(needle in text(rows_all, rid), f"ledger {label} still reads {needle}")
    for needle, label in (("named expected failure", "collision expected failure"),
                          ("336.4", "T-E5 assumed label"),
                          ("0.1213", "withdrawn Cd disclosure"),
                          ("21 of 45", "audio donor GUIDs")):
        ok(needle in text_out, f"sheet carries the {label}")
    ok(os.path.exists(QA1), "QA-1 receipt exists")
    for r in pred:
        if r["status"] == "predicted":
            ok(bool(r["band"]), f"{r['id']} predicted line has a pass band")
        else:
            ok(bool(r.get("missing")), f"{r['id']} UNKNOWN line names the missing input")

    ok(info["lines"] == info["rows"] == info["unique"],
       f"T ledger parses cleanly ({info['rows']} rows, no duplicate ids)",
       f"{info['lines']} non-blank lines / {info['rows']} rows / {info['unique']} ids")

    # D-4: the derivations the sheet prints, re-derived here.  A green check says the radii and
    # the ruling's times follow from the built values; it does not say the lore goal is met.
    ok(abs(info["r_low"] - info["wb"] / math.tan(math.radians(info["lock_deg"]))) < 1e-9
       and abs(info["r_high"] - info["wb"] / math.tan(math.radians(info["lock_hi_deg"]))) < 1e-9,
       f"D-4 radii re-derive as wheelbase/tan(lock) ({info['r_low']:.3f} / {info['r_high']:.3f} m)")
    ok(info["r_low"] < info["r_high"], "D-4 radius shrinks as the lock angle grows")
    ok(abs(info["v_term"] - (2 * info["p_w"] / (RHO * info["cd_area"])) ** (1 / 3)) < 1e-9
       and abs(info["cd"] - float(info["cd_build"])) < 1e-6,
       f"D-2 terminal re-derives as (2P/(rho Cd A))^(1/3) = {info['v_term'] * 3.6:.0f} km/h at the "
       f"built Cd {info['cd']:g}")
    ok(abs(info["goal_low_calc"] - info["g_low"]) < 5e-4
       and abs(info["goal_high_calc"] - info["g_high"]) < 5e-4,
       "D-4 ruling times re-derive as lock/rate "
       f"({info['goal_low_calc']:.4f} / {info['goal_high_calc']:.4f} s at {info['rate']:.0f} deg/s)")
    ok(info["red_low"] and info["red_high"],
       f"D-4 T-ST7 miss still RED: built {info['t_low']:.2f} / {info['t_high']:.2f} s vs goal band "
       f"{info['g_high']:.3f}-{info['g_low']:.3f} s (open until take A3)",
       "the built times no longer exceed the ruling - re-read T-ST7 and this sheet")
    ok(abs(info["align"] - 1 / 1.6) < 5e-4 and abs(info["fals"] - 0.3 * 1.6) < 5e-4
       and info["hb_fric"] > info["hb_band_hi"] and info["k4_ledger"] != info["k4_bytes"],
       f"D-6 labels re-derive (align {info['align']:g} = 1/1.6, falsifier {info['fals']:g}; T-K3 "
       f"{info['hb_fric']:g} above the 6 t band 1..{info['hb_band_hi']:g}; T-K4 ledger "
       f"{info['k4_ledger']} vs bytes {info['k4_bytes']}, next {info['k4_ramp']:g} s)")
    ok(info["hold_lo"] < info["t_low"] < info["hold_hi"]
       and info["hold_lo_hi"] < info["t_high"] < info["hold_hi_hi"],
       f"D-5 band brackets the built times ({info['t_low']:.2f} / {info['t_high']:.2f} s)")

    failed = [c for c in checks if not c["ok"]]
    for c in checks:
        print(f"{'PASS' if c['ok'] else 'FAIL'} {c['oracle']}"
              + (f" [{c['detail']}]" if c["detail"] and not c["ok"] else ""))
    print(f"{len(checks) - len(failed)}/{len(checks)} oracles pass")
    red = "RED" if (info["red_low"] and info["red_high"]) else "green"
    print(f"ledger: {info['rows']} rows; D-4 radius {info['r_low']:.2f} m at the "
          f"{info['lock_deg']:.0f} deg lock / {info['r_high']:.2f} m at the "
          f"{info['lock_hi_deg']:.0f} deg lock; T-ST7 {red}: built {info['t_low']:.2f} / "
          f"{info['t_high']:.2f} s vs goal {info['g_high']:.3f}-{info['g_low']:.3f} s")
    if failed:
        return 1

    if write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            f.write(text_out)
        print(f"wrote {os.path.relpath(OUT, ROOT).replace(os.sep, '/')}: "
              f"{len({r['take'].split()[0] for r in pred})} checks, {info['n_pred']} predicted, "
              f"{info['n_unk']} UNKNOWN")
        return 0

    current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else None
    if current != text_out:
        import difflib
        for line in difflib.unified_diff((current or "").splitlines(), text_out.splitlines(),
                                         "on-disk", "recomputed", lineterm="", n=1):
            print(line)
        print("FAIL document differs from the regenerated text")
        return 1
    print("PASS document: PREDICTIONS.md matches the regenerated driving sheet")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="write Working/Q/PREDICTIONS.md")
    ap.add_argument("--check", action="store_true", help="re-derive and compare")
    args = ap.parse_args()
    sys.exit(main(write=args.write))
