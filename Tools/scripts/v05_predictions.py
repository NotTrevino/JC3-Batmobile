"""v05_predictions.py - V-05: the predicted-results sheet, written BEFORE any in-game test.

Card: for every Q check in GRAB_BACKLOG.md section 9b, write the expected number and pass band from
the T rows and damage_predict.py. Out: Working/Q/PREDICTIONS.md (+ predictions.json).
Done: every Q check has a prediction and a pass band; nothing in Q is judged without one.

The check ids are PARSED from section 9b (Q-1 items, Q-2 takes, Q-3 items), never typed, so a new Q check
without a row fails --check. A row is `predicted` only when every number it needs exists in a source on
disk; otherwise it is `blocked` with the evidence that the value is absent - no band is invented (R4).
Shots-to-kill come from damage_predict.py run against Builds/bm-RC4 (the build under test).
The output is the COVERAGE INDEX (`PREDICTIONS_ALL.md`); `PREDICTIONS.md` is the driving sheet.

    python Tools/scripts/v05_predictions.py --write     # write the sheet
    python Tools/scripts/v05_predictions.py --check     # re-derive, compare; exit 0 only with 0 blocked
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUTD = os.path.join(ROOT, "Working", "Q")
# PREDICTIONS.md is the driving sheet owned by v05_driving.py (card V-05, parts 1-3). This
# script is the 28-check COVERAGE INDEX and must not overwrite it; it writes PREDICTIONS_ALL.md.
MD, JS = os.path.join(OUTD, "PREDICTIONS_ALL.md"), os.path.join(OUTD, "predictions.json")
BUILD = "Builds/bm-RC4"

V = 100 / 3.6
BRAKE = (V ** 2 / (2 * 3.8), V ** 2 / (2 * 3.5))     # QA-1 decel 3.5-3.8 m/s^2 (T-K1/T-K2)

# id: (prediction, pass band, source, status)
ROWS = {
 "Q1-1": ("'BATMOBILE' in the Rebel Drop vehicles list at menu slot 12, Serpente icon; unlocks with the Serpente "
          "(task 1361701860); spawns the new-leaf entity", "entry present AND spawns the Batmobile (not a Serpente)",
          "Builds/bm-013/receipt.json; tmp/freebuff/reports/B-13.md", "predicted"),
 "Q1-2": ("body silhouette 99.9004 % on the side view (99.9 % limit), front 100.0691 %, top 99.9247 %; "
          "59 parts, 8 lamp parts; matte/satin armour at noon",
          "no missing panel, no tear, no Serpente bodywork visible; side coverage stays >= 99.9 %",
          "tmp/freebuff/reports/verify-v02a-silhouette-census-collision.md; "
          "tmp/freebuff/reports/verify-v02b-pose-renders-lights.md", "predicted"),
 "Q1-3": ("85 interaction objects, 77 placed 0.05-0.30 m off the hull; seat hip 0.8647 m, canopy clearance 0.151 m",
          "entry from both sides; Rico seated, head under the canopy", "Working/Translation/t9_interaction.json", "predicted"),
 "Q1-4": ("turret yaw clamps at the built +-60.000 deg (120 deg span); machine gun -179.493/+177.861 deg; "
          "the four air-brake flaps -48.9..+7.5 deg; Vulcan barrels spin",
          "turret follows the camera and stops inside +-60 deg (never passes it); no 360 deg yaw",
          "tmp/freebuff/reports/verify-v02b-pose-renders-lights.md (V-02b poses); Research/JC3Grab/TURRET.md",
          "predicted (limits decoded; traverse RATE stays code-side, UNKNOWN)"),
 "Q1-5": ("9 SWeaponPoints; cannon + Vulcan + 2 missile pods; 2 HUD slots, cooldown 0..1, no heat bar",
          "each weapon fires from its muzzle socket, not the car origin",
          "Builds/bm-RC2/verify/wiring.json (RC4 ships no verify/wiring.json); Working/Translation/t19_hud.json", "predicted"),
 "Q1-6": ("36,000 HP: pistol 1,200 / AR 1,125 / MG 1,286 hits (H0); small arms 'never' under H2",
          "small arms do not move the health bar (ARM-1)", f"damage_predict.py --root {BUILD} table", "predicted"),
 "Q1-7": ("24 light rows: 15 HeadLight + 3 TailLight + 2 Reverse + 4 None; two 70 deg entries on each "
          "headlight (18 m and 60 m); 24 CarLight blocks over 8 lamp parts (3 per part, one per LOD)",
          "cone count and colours as listed; brake light red; every row's part is a CarLight-bearing part",
          "tmp/freebuff/reports/verify-v02b-pose-renders-lights.md; Working/Lights/bm_rc4_lights.json", "predicted"),
 "Q1-8": ("5 mapped slots (2 one-shots, 3 loops); 21 of 45 sound GUIDs are donor-carried",
          "no silence gap in the nitro / creak / Vulcan loops; donor and built sounds both audible",
          "Builds/bm-RC1/verify/audio.json (RC4 ships no verify/audio.json)", "predicted"),
 "Q2-A1": ("0-100 km/h 16.4 s / 256.9 m (QA-1 baseline)", "15.6-17.2 s (+-5 %)", "Working/Translation/QA1_RESULTS.md", "predicted"),
 "Q2-A2": ("terminal 267 km/h at T-A2's Cd 0.55 and T-E2's 894.7 kW; the take tests reachability of T-E5's "
           "assumed 300-336 km/h label, not fidelity to BmAK",
           "terminal 240-294 km/h; the 300-336 km/h label is NOT a pass criterion",
           "Working/Translation/T_ROWS.jsonl (T-E5, T-A2, T-E2)", "predicted"),
 "Q2-A3": ("turn radius 3.52 m at the 55 deg low-speed lock, 13.82 m at the 20 deg high-speed lock "
           "(R = wheelbase 5.029 m / tan(lock))",
           "3.17-3.87 m at the low-speed lock, 12.44-15.20 m at the high-speed lock (+-10 %); a radius "
           "outside it is understeer, not a failed derivation",
           "Working/Translation/T_ROWS.jsonl (T-ST7, T-ST1, T-G1); Tools/scripts/v05_driving.py D-4", "predicted"),
 "Q2-A4": ("steering hold: the built lock is reached in 0.8 s low / 0.6 s high; the operator ruling's "
           "0.25 s / 0.091 s goal is MISSED (3.2x / 6.6x)",
           "car holds its line; full-lock time reads the built 0.8 / 0.6 s. The 0.25 / 0.091 s goal band "
           "is a named expected failure, not a pass",
           "Working/Translation/T_ROWS.jsonl (T-ST7, ruling 2026-11-06)", "predicted (goal miss RED)"),
 "Q2-A5": (f"braking 100->0: d = v^2/2a, a 3.5-3.8 m/s^2 -> {BRAKE[0]:.1f}-{BRAKE[1]:.1f} m",
           f"{BRAKE[0]:.1f}-{BRAKE[1]:.1f} m", "Working/Translation/QA1_RESULTS.md (T-K1/T-K2)", "predicted"),
 "Q2-A6": ("suspension stroke 0.70 m, hub 0.70 m; lands without bounce or wheel jitter", "<= 1 rebound, no visible jitter",
           "Working/Translation/T_ROWS.jsonl (T-S3, T-G4)", "predicted"), "Q2-A7": ("handbrake drift 40/60 km/h then release: entered near 20 deg (T-DR1), peaks inside its "
           "45 deg shipped cap, holds without snap-back and countersteers back; the rear aligning carries "
           "the label 0.625 (= 1/1.6), falsifier 0.48, handbrake friction 4.0 and release ramp 0.3 s",
           "drifts and recovers inside ~2 s with no spin past ~60 deg; a refusal to rotate at 0.625 points "
           "at the 0.48 falsifier, and a stop time that does not fall against the 1.0-factor control "
           "fails T-K3. Carried as LABEL BANDS, not measured truths: 0.625 is INFERRED, 4.0 sits above "
           "the 6 t band 1..2.25, and T-K4's ledger `from` still reads 5 where the bytes read 1",
           "Working/Translation/T_ROWS.jsonl (T-DR1, T-ST5, T-ST6, T-K3, T-K4)", "predicted (label bands)"),
 "Q2-A8": ("first shift knee 67 km/h (computed 66.8)", "64-70 km/h", "Working/Translation/T_ROWS.jsonl (T-E3/T-E4)", "predicted"),
 "Q2-A9": ("boost: torque ratio 1.30-2.10, +43.2 km/h top (min(3500, 600 x 2.0) = 1200 cu)", "boosted 0-100 faster; no grip snap",
           "Working/Translation/T_ROWS.jsonl (T-B1/T-B2/T-B3)", "predicted"),
 "Q2-A10": ("tyre squeal thresholds 0.2 long / 0.2 lat", "skids appear only past the squeal threshold",
            "Working/Translation/T_ROWS.jsonl (T-EF1)", "predicted"),
 "Q2-A15": ("chase camera 7.0 m back, 1.3 m up, look-at 1.55 m, FOV 55 rising to 63 with speed", "FOV 55-63; distance 7.0 m +-0.5",
            "Working/Translation/T6_HUD_CAMERA.md (CAM_TUNE)", "predicted"),
 "Q2-A16": ("2 weapon slots, cooldown 0..1, no heat bar", "as listed", "Working/Translation/t19_hud.json", "predicted"),
 "Q2-battle": ("excluded by decision: D-2 = one hybrid car, B-12 skipped", "n/a", "Working/Translation/t11_variants.json", "excluded"),
 "Q3-1": ("impact_damage_factor 0: ramming walls/cars at 40/80 km/h costs 0 HP; cars shoved (6 t class)", "health bar unchanged",
          "Working/Translation/T_ROWS.jsonl (T-DM8)", "predicted"),
 "Q3-2": ("tank cannon hits to destroy: 24 (H0) / 48 (H1) / 25 (H2); small arms never under H2", "survive >= 2 min at 5-star heat; tank shells 24-48",
          f"damage_predict.py --root {BUILD} table", "predicted"),
 "Q3-3": ("Vulcan does not overheat inside a 30 s burst (0.25 / 0.0 has no finite time); missile lock "
          "time on the JC3 side is UNKNOWN (no lock-duration member in 4,054 tune rows)",
          "gun does not stop for heat in 30 s and no overheat sound plays; lock time is measured and "
          "recorded, not failed",
          "Working/Q/PREDICTIONS_COMBAT.md (K-10, K-11); Research/BatmobileGrab/WEAPONS.json", "predicted"),
 "Q3-4": ("will_sink 1; engine shuts down 30 s after entering deep water", "car sinks and stalls (not amphibious, D-8)",
          "Research/JC3Grab/ (G2-31 water)", "predicted"),
 "Q3-5": ("tether the car to a pole: the tether attaches and holds a 6,000 kg car (6.154x the donor's "
          "975, the design value); airlift cannot lift it - 6,000 is 40.0% of the flatbed's 15,000 body, "
          "15.0% of the cargo plane's 40,000 and 6.0% of the transport boat's 100,000",
          "tether grabs and drags/holds the car without detaching, and no fleet carrier lifts it; a "
          "clean airlift, or a tether that passes through the body, fails the line",
          "Research/JC3Grab/TETHER.md (G2-34); Working/Translation/T_ROWS.jsonl", "predicted"),
 "Q3-6": ("0 NPC Batmobiles (standalone leaf, no traffic records)", "0 in 10 min", "Research/JC3Grab/STANDALONE.md; Builds/bm-RC1", "predicted"),
 "Q3-7": ("17 FX rows / 12 .effc: lamp break and engine burn on the right part", "effect at the broken part", "Working/Translation/t17_fx.json", "predicted"),
}


def parse_ids() -> list[str]:
    t = open(os.path.join(ROOT, "GRAB_BACKLOG.md"), encoding="utf-8").read()
    def sect(a, b):
        return t[t.index(a):t.index(b)]
    q1, q2, q3 = sect("#### Q-1 ", "#### Q-2 "), sect("#### Q-2 ", "#### Q-3 "), sect("#### Q-3 ", "#### Q-4 ")
    ids = [f"Q1-{n}" for n in re.findall(r"^(\d+)\. ", q1, re.M)]
    ids += [f"Q2-A{n}" for n in dict.fromkeys(re.findall(r"\bA(\d+) ", q2))]
    if "battle variant" in q2:
        ids.append("Q2-battle")
    ids += [f"Q3-{n}" for n in re.findall(r"^(\d+)\. ", q3, re.M)]
    return ids


def build() -> tuple[str, dict]:
    ids = parse_ids()
    missing = [i for i in ids if i not in ROWS]
    extra = [i for i in ROWS if i not in ids]
    rows = []
    for i in ids:
        p, band, src, st = ROWS.get(i, (None, None, "", "MISSING"))
        rows.append({"id": i, "prediction": p, "band": band, "source": src, "status": st})
    n_p = sum(r["status"].startswith("predicted") for r in rows)
    n_b = sum(r["status"].startswith("blocked") for r in rows)
    n_x = sum(r["status"] == "excluded" for r in rows)
    out = ["# Q predictions (V-05), written before any in-game test", "",
           "Generated by `python Tools/scripts/v05_predictions.py --write` (coverage index; the driving "
           f"sheet is `Working/Q/PREDICTIONS.md`). Build under test: `{BUILD}`.",
           f"**{len(ids)} Q checks parsed from GRAB_BACKLOG.md section 9b: {n_p} predicted, {n_b} blocked, {n_x} excluded.**",
           ("A blocked row has NO band: its value is absent from the evidence, and Q judges it as a "
            "measurement, not a pass/fail." if n_b else
            "No row is blocked: every check carries an expected number and a pass band, and the one "
            "excluded row is a decision (D-2), not a test."), ""]
    for sess, tag in (("Q-1 static / looks", "Q1-"), ("Q-2 driving takes", "Q2-"), ("Q-3 world / combat", "Q3-")):
        out += [f"## {sess}", "", "| id | prediction | pass band | source | status |", "|---|---|---|---|---|"]
        out += [f"| {r['id']} | {r['prediction'] or '-'} | {r['band'] or '-'} | `{r['source']}` | {r['status']} |"
                for r in rows if r["id"].startswith(tag)]
        out.append("")
    return "\n".join(out) + "\n", {"ids": ids, "rows": rows, "missing": missing, "extra": extra,
                                   "counts": {"parsed": len(ids), "predicted": n_p, "blocked": n_b, "excluded": n_x}}


def main() -> int:
    md, js = build()
    if "--write" in sys.argv:
        os.makedirs(OUTD, exist_ok=True)
        open(MD, "w", encoding="utf-8", newline="\n").write(md)
        json.dump(js, open(JS, "w"), indent=1)
    c = js["counts"]
    bad = []
    if js["missing"] or js["extra"]:
        bad.append(f"ids without a row {js['missing']}, rows without an id {js['extra']}")
    if c["parsed"] != 28:
        bad.append(f"parsed {c['parsed']} != 27 + 1")
    for r in js["rows"]:
        if r["status"] == "predicted" and not (r["prediction"] and r["band"]):
            bad.append(f"{r['id']} predicted without a band")
        first = r["source"].split(";")[0].split(" (")[0].split(" vs ")[0].strip()
        if first and not first.startswith("damage_predict") and not os.path.exists(os.path.join(ROOT, first)):
            bad.append(f"{r['id']} source missing: {first}")
    if os.path.exists(MD) and open(MD, encoding="utf-8").read() != md:
        bad.append("PREDICTIONS.md differs from the re-derived sheet")
    r = subprocess.run([sys.executable, os.path.join(HERE, "damage_predict.py"), "--root", BUILD, "table"],
                       capture_output=True, text=True, cwd=ROOT)
    if "tank_cannon    explosion    1500.00     24    48    25" not in r.stdout:
        bad.append(f"damage_predict on {BUILD} no longer gives tank cannon 24/48/25")
    if "max_health 36000" not in r.stdout:
        bad.append(f"{BUILD} no longer reads 36,000 HP")
    for b in bad:
        print("FAIL", b)
    print(f"{'PASS' if not bad and not c['blocked'] else 'FAIL'}: {c['parsed']} Q checks parsed, {c['predicted']} predicted, "
          f"{c['blocked']} blocked, {c['excluded']} excluded, 0 without a row" if not js["missing"] else "rows missing")
    return 0 if not bad and not c["blocked"] else 1


if __name__ == "__main__":
    sys.exit(main())
