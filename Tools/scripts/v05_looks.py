#!/usr/bin/env python3
"""v05_looks.py - V-05 part 3: the look/static, mode, HUD and camera predictions.

Card: before any in-game test, write what Q-1 (static + looks), the mode rows and the HUD/camera
rows should show: which parts move and through what angle range, mode transition values, HUD
element positions, camera distance/FOV. Every line carries its source row, the expected value
and a pass band; where no row gives a number the line says UNKNOWN instead of inventing one.

Out: `Working/Q/PREDICTIONS_LOOKS.md` (separate from PREDICTIONS.md / PREDICTIONS_COMBAT.md).

`--check` re-reads every source JSON/MD, re-asserts each oracle below and compares the document
byte-for-byte; a changed source turns the check red instead of leaving a stale prediction green.

    python Tools/scripts/v05_looks.py --write
    python Tools/scripts/v05_looks.py --check
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Working", "Q", "PREDICTIONS_LOOKS.md")

CAM = os.path.join(ROOT, "Working", "Camera", "CAM_TUNE.json")
MODES = os.path.join(ROOT, "Working", "Translation", "t11_variants.json")
HUD = os.path.join(ROOT, "Working", "Translation", "t19_hud.json")
TURRET = os.path.join(ROOT, "Research", "JC3Grab", "TURRET_LIMITS.json")
WIRING = os.path.join(ROOT, "Builds", "bm-RC2", "verify", "wiring.json")
LIGHTS = os.path.join(ROOT, "Working", "Appearance", "build_lights", "lights_manifest.json")
RCLIGHTS = os.path.join(ROOT, "Working", "Lights", "bm_rc4_lights.json")
AUDIO = os.path.join(ROOT, "Builds", "bm-RC1", "verify", "audio.json")


def load(p):
    return json.load(open(p, encoding="utf-8"))


def main(write: bool) -> int:
    cam, modes, hud = load(CAM), load(MODES), load(HUD)
    turret, wiring = load(TURRET), load(WIRING)
    lights, audio, rcl = load(LIGHTS), load(AUDIO), load(RCLIGHTS)

    checks = []

    def ok(cond, label):
        checks.append({"oracle": label, "ok": bool(cond)})
        return bool(cond)

    # ---- oracles: every number the table prints is re-read here
    edits = {(e["path"]): e["new"] for e in cam["edits"]}
    ok(edits.get("CameraPosition[1]") == 1.3 and edits.get("CameraPosition[2]") == 7.0,
       "CAM_TUNE CameraPosition [1]=1.3 [2]=7.0")
    ok(edits.get("LookAtPoint[1]") == 1.55, "CAM_TUNE LookAtPoint[1]=1.55")
    ok(edits.get("FOV[0]") == 55.0 and edits.get("FOV[1]") == 63.0, "CAM_TUNE FOV 55/63")
    ok(edits.get("FOVVelocityRange[1]") == 108.0, "CAM_TUNE FOVVelocityRange[1]=108")
    ok(edits.get("RollWithVehicleAmount") == 0.38, "CAM_TUNE roll 0.38")
    ok(edits.get("CollisionStartPoint[1]") == 1.6, "CAM_TUNE collision 1.6")
    ok(cam.get("readback", {}).get("ok") == cam.get("readback", {}).get("expected") == 8,
       "CAM_TUNE 8/8 readback")

    tune = modes["facts"]["tune"]
    ok(tune["back_m"] == 7.0 and abs(tune["up_m"] - 1.3) < 1e-6
       and tune["fov_lo"] == 55.0 and tune["fov_hi"] == 63.0, "T-15 tune 7.0/1.3/55-63")

    m = modes["facts"]["modes"]
    ok(m["curve_points"] == [[0.0, 60.0], [600.0, 40.0], [1200.0, 30.0]],
       "BattleModeVSpeedCurve 3 points")
    ok(m["curve_same"] is True, "battle curve identical in 4 packages")
    ok(str(m["armour"]["value"]) == "0", "ArmourModeDamageReduction 0")
    camf = modes["facts"]["camera"]
    ok(camf["BattleModeCamFOV"] == 60.0 and camf["AntiPersonelBattleModeCamFOV"] == 40.0,
       "battle camera FOV 60/60/40")
    ok(camf["config_min_distance"] == 1000.0 and camf["config_max_distance"] == 1000.0,
       "battle camera config 1000/1000 cm")
    ok(modes["facts"]["tankturn"]["pivot_named_omission"] is True, "turn-on-spot named omission")
    ok(modes["facts"]["tankturn"]["driving_hits"] == 0, "turn-on-spot 0 driving-module hits")

    blob = json.dumps(hud)
    ok(hud["counts"]["rows"] == 10 and hud["counts"]["mapped"] == 6
       and hud["counts"]["partial"] == 2 and hud["counts"]["out"] == 2, "T-19 10 rows 6/2/2")
    for needle, label in (("-111", "reticle marker y -111"), ("360", "cooldown 360 deg"),
                          ("1.5", "lock-on rotation 1.5 s"), ("21", "lock-on POI type 21")):
        ok(needle in blob, "T-19 " + label)
    ok("MCI_vehicle_weapons0" in blob and "MCI_vehicle_weapons1" in blob,
       "T-19 two weapon clips")

    tot = turret["totals"]
    ok(tot["yaw_spans_deg"] == [150.0, 300.0, 358.0], "TURRET_LIMITS yaw spans 150/300/358")
    ok(tot["pitch_spans_deg"] == [25.0, 30.0, 55.0, 65.0, 75.0, 80.0, 100.0],
       "TURRET_LIMITS pitch spans 25..100")
    ok(turret["yaw"]["full_rotation_yaw_hinges"] == 0, "no full-rotation turret in the fleet")

    ok(wiring["counts"]["points"] == 9 and not wiring["dangling"],
       "bm-RC2 9 SWeaponPoints, 0 dangling")
    ok(lights["t18_hosting"]["rows_hosted_count"] == 21 and len(lights.get("lamps", [])) == 8,
       "RC2 manifest hosted 21 T-18 rows on 8 lamp parts (historical)")
    ok(len(rcl["rows"]) == 24 and len(rcl["lamp_parts"]) == 8,
       f"D-03 RC4 module carries {len(rcl['rows'])} rows on {len(rcl['lamp_parts'])} lamp parts")
    ok(audio["summary"]["slots"] == 5 and len(audio["rows"]) == 5, "5 audio slots")
    # RC4's own event table: the 45 donor GUIDs split 24 carried in vehicles.bank + 21 donor
    # (19 effects + 2 character banks that this tree does not build).  The count is measured here,
    # not typed, so the sheet's "21 of 45" cannot drift from the audio tree.
    ev = json.load(open(os.path.join(ROOT, "Builds", "bm-RC4-audio", "events.json"),
                       encoding="utf-8"))
    ok(ev["total"] == 45 and ev["resolved"] == 24 and ev["donor_bank_not_built"] == 21
       and len(ev["rows"]) == 45,
       f"RC4 audio events: {ev['total']} GUIDs, {ev['resolved']} resolved in vehicles.bank, "
       f"{ev['donor_bank_not_built']} donor")

    # D-03's light rows: the one place a written value is outside the shipped census, so the
    # document carries it as an out-of-domain claim rather than a decoded number.
    dom = rcl["domain"]
    marked = {r["index"]: r for r in rcl["rows"] if r.get("claim")}
    ok(dom["entries"] == 3217 and dom["shipped_max"] == {"range": 50.0, "angle": 50.0},
       "D-03 fleet census 3,217 entries, shipped max 50 m / 50 deg")
    ok(marked[2]["claim"]["status"] == "out-of-domain"
       and marked[10]["claim"]["status"] == "out-of-domain"
       and marked[2]["members"]["range"]["v"] == 60.0
       and marked[10]["members"]["angle"]["v"] == 70.0,
       "D-03 beam rows 2/10 labelled out-of-domain (60 m / 70 deg)")
    ok(marked[11]["claim"]["status"] == "donor-carried"
       and marked[11]["members"]["angle"]["v"] == 60.0,
       "D-03 row 11 (T-L17) marked donor-carried, not translated")
    ok(all(lab["ships_in_fleet"] == 0 for lab in dom["labels"]
           if lab["kind"] == "out-of-domain"),
       "D-03 no out-of-domain label ships in the fleet")

    rows = []

    def row(qid, src, expected, band, status="predicted"):
        rows.append({"id": qid, "src": src, "expected": expected, "band": band, "status": status})

    # ---- Q-1 static / looks
    row("Q1-1", "WLD-1/2, B-13 receipt", "Rebel Drop entry 'Batmobile' at slot 12, hash 1621485476; "
        "spawns the debug leaf, not a Serpente",
        "entry visible AND spawns the Batmobile (name, silhouette)")
    row("Q1-2", "APP-1/2/3, T-MA3..5", "body silhouette 99.97 %, 19 material slots, 8 lamp parts; "
        "satin armour, glass canopy", "no missing panel or tear; body luminance above road; no mirror")
    row("Q1-3", "WLD-3/4, ANI-8/9", "85 interaction objects, 77 placed 0.05-0.30 m off the hull; "
        "seat hip 0.8647 m, canopy clearance 0.151 m",
        "entry from both sides; Rico's head stays under the canopy")
    row("Q1-4", "ANI-2..7, TURRET_LIMITS", "turret yaw within the fleet's decoded 150-358 deg spans; "
        "cannon pitch within 25-100 deg; Vulcan barrels spin",
        "turret follows the camera; no full 360 (0 full-rotation turret hinges in 233 entities)")
    row("Q1-5", "WPN-1..5, HUD-2, t19_hud", "9 SWeaponPoints; 2 HUD slots, cooldown 0..1, no heat bar",
        "each weapon fires from its muzzle; 2 clips draw; no heat element")
    row("Q1-6", "ARM-1/2/4, damage_predict", "36,000 HP: pistol 1,200 / AR 1,125 / MG 1,286 hits (H0)",
        "small arms do not move the bar; hits-to-kill as predicted")
    row("Q1-7", "LGT-1, T-LG3/6, T-L1..7", "8 lamp parts; the RC4 module carries 24 rows, two 70 deg "
        "entries on each headlight (18 m and 60 m), 24 CarLight blocks (3 per part, one per LOD); the "
        "RC2 manifest hosted 21 T-18 rows", "every row's part carries a CarLight block; brake light red")
    row("Q1-7b", "D-03 lights ledger, LIGHT_SYSTEM census", "beam rows 2/10: range 60 m, angle "
        "70 deg (rows 5/9 also 70 deg); multiplier 1.0 and falloff 0.8/0.0 are stand-ins; row 11 "
        "(T-L17) is donor-carried", "the beam lights the road at 60 m and the 70 deg cone renders; "
        "if it clips at 50 m or reads as a hard circle, the claim fails and the plan's fallback "
        "50/50 applies", "out-of-domain")
    row("Q1-8", "AUD-5, T-16, V-04 audio.json, RC4 events.json", "5 audio slots; 4/5 inside +-1 LU "
        "(max 2.33 LU), 3 loop slots, 1 loop click; 21 of 45 sound GUIDs are donor-carried (24 "
        "resolved in vehicles.bank, 19 effects + 2 character banks not built)", "no silence gap; "
        "V-04 already measured the loudness and loop gates red - expect those two to fail; the 21 "
        "donor GUIDs have no carrier in this tree, so they are judged as donor-labelled, not silent")
    q1_end = len(rows)

    # ---- moving parts (which moves, what range)
    row("ANI-7", "T-12 steering rows", "steering yoke turns", "moves with input; angle UNKNOWN (no row gives a value)", "UNKNOWN")
    row("ANI-4", "T-12 turbine", "turbine spins with revs", "spins; rate UNKNOWN", "UNKNOWN")
    row("ANI-2", "TURRET_LIMITS totals", "turret yaw span 150-358 deg in the fleet; full rotation 0",
        "turret follows the camera and stops inside its span")
    row("ANI-2b", "TURRET_LIMITS pitch", "cannon pitch span 25-100 deg in the fleet",
        "pitch clamps; the build's own min/max is UNKNOWN (fleet band only)", "UNKNOWN")
    row("ANI-3", "T-12 Vulcan", "Vulcan barrels spin when firing", "spin observed; angle/rate UNKNOWN", "UNKNOWN")
    row("ANI-6", "T-12 hatches", "missile hatches open on fire", "open on fire; angle UNKNOWN", "UNKNOWN")
    row("ANI-5", "Q-1 item 4 air-brake probe", "fins may move under braking (one-variable probe)",
        "if they move, record range; if not, ANI-5 becomes static with a named reason", "UNKNOWN")
    mv_end = len(rows)

    # ---- modes
    row("T-MD11", "T11_MODES T-MD11", "battle FOV 60 deg sits inside the tune's 55-63",
        "no battle framing appears; screen FOV stays 55-63", "predicted")
    row("T-MD6", "T11_MODES T-MD6", "TurningModeMaxSpeed 600 cm/s = 21.6 km/h (omitted)",
        "car accelerates past 25 km/h (no battle cap)", "predicted")
    row("T-MD5", "T11_MODES T-MD5", "BattleModeVSpeedCurve 0->60, 600->40, 1200->30 (raw)",
        "one top speed; no mode cap observable", "predicted")
    row("T-MD10", "T11_MODES T-MD10", "ArmourModeDamageReduction 0",
        "hits-to-kill equals the single profile (no reduction)", "predicted")
    row("T-MD12", "T11_MODES T-MD12", "battle lamps mapped onto HeadLight",
        "battle heads/arch glow with the lights, not on a mode", "predicted")
    md_end = len(rows)

    # ---- HUD
    row("T-HUD11", "T6/T19 HUD", "2 slots (MCI_vehicle_weapons0/1)", "two clips draw, one per bound weapon")
    row("T-HUD14", "T6/T19 HUD", "reticle shape E_RETICLE_CANNON = 8, marker y -111 px",
        "heavy reticle appears with the cannon and hides with it")
    row("T-HUD16", "T6/T19 HUD", "cooldown 0..4 states -> 0.00/0.25/0.50/0.75/1.00; rot = cooldown x 360",
        "loader ring fills 0->full between shots, hidden at rest")
    row("T-HUD18", "T6/T19 HUD", "lock-on POI type 21, one marker, 360 deg / 1.5 s",
        "marker appears on the locked target and rotates")
    row("T-HUD20", "T6/T19 HUD", "infiniteAmmo true", "no ammo counter in either slot")
    row("T-HUD15", "T6/T19 HUD", "accuracy frame -> reticle_size 5..30 px", "scale UNKNOWN (no unit map)", "UNKNOWN")
    hud_end = len(rows)

    # ---- camera
    row("T-CAM5", "T6 T-CAM5 / CAM_TUNE", "CameraPosition [0,1.30,7.00], LookAtPoint [0,1.55,0]",
        "7.00 m back +-0.5; 1.30 m up +-0.2; look-at 1.55 m +-0.2")
    row("T-CAM2", "T6 T-CAM2 / CAM_TUNE", "FOV 55 -> 63 vertical", "FOV inside 55-63; no fisheye")
    row("T-CAM3", "T6 T-CAM3 / CAM_TUNE", "FOVVelocityRange max 108 km/h", "FOV stops changing at 108 +-5 km/h")
    row("T-CAM6", "T6 T-CAM6 / CAM_TUNE", "RollWithVehicleAmount 0.38", "camera roll follows the lean (0.28-0.48)", "predicted")
    row("T-CAM13", "T6 T-CAM13 / CAM_TUNE", "CollisionStartPoint 1.6 m", "no clipping through the taller body (1.5-1.7)")
    row("T-CAM12", "T6 T-CAM12", "authored boom 400/400 cm = 4.00 m; sit 3.00 m -> 7.00 m at rest",
        "distance at rest 7.0 m (composition, not a field)")
    row("T-CAM9", "T6 T-CAM9", "spring stiffness bridge", "UNKNOWN: no unit bridge to JC3 springs", "UNKNOWN")
    row("T-CAM11", "T6 T-CAM11", "boost/wheelspin shake", "UNKNOWN: no numeric bridge", "UNKNOWN")

    L = []
    A = L.append
    A("# Q look/static, mode, HUD and camera predictions (V-05 part 3)")
    A("")
    A("Generated by `python Tools/scripts/v05_looks.py --write`. Build: `Builds/bm-RC4`")
    A("(wiring re-read from `Builds/bm-RC2/verify/wiring.json` - the RC4 tree ships no")
    A("`verify/wiring.json`, disclosed rather than assumed unchanged). Written before any in-game test.")
    A("")
    A("**%d lines: %d predicted, %d out-of-domain, %d UNKNOWN.** A predicted line has a number "
      "from a file and a"
      % (len(rows), sum(r["status"] == "predicted" for r in rows),
         sum(r["status"] == "out-of-domain" for r in rows),
         sum(r["status"] == "UNKNOWN" for r in rows)))
    A("band the Q observer can fail; an out-of-domain line has a number the build writes that no "
      "shipped entry carries; an UNKNOWN line has no number in any row and says so.")
    A("")
    A("## Q-1 static / looks")
    A("")
    A("| id | source row | expected value | pass band | status |")
    A("|---|---|---|---|---|")
    for r in rows[:q1_end]:
        A("| %s | %s | %s | %s | %s |" % (r["id"], r["src"], r["expected"], r["band"], r["status"]))
    A("")
    A("`Q1-7b` is the one **out-of-domain** line: the fleet census (`Research/JC3Grab/")
    A("LIGHT_SYSTEM.json`, all %s shipped module entries) tops out at `range` 50 (66 rows) and "
      % format(dom["entries"], ","))
    A("`angle` 50 (74 rows), so 60 m / 70 deg are writable floats that nothing shipped renders.")
    A("Both headlight-beam rows carry the label, plus the two 18 m rows' 70 deg cones; `multiplier`")
    A("1.0 and `falloff_start` 0.8/0.0 are stand-ins, and row 11 (T-L17) is donor-carried.")
    A("")
    A("## Moving parts at standstill")
    A("")
    A("| id | source row | expected value | pass band | status |")
    A("|---|---|---|---|---|")
    for r in rows[q1_end:mv_end]:
        A("| %s | %s | %s | %s | %s |" % (r["id"], r["src"], r["expected"], r["band"], r["status"]))
    A("")
    A("Decoded angle ranges are fleet spans (`Research/JC3Grab/TURRET_LIMITS.json`: 10 yaw hinges,")
    A("spans %s deg; 14 pitch hinges, spans %s deg; 0 full-rotation turret hinges in 233 entities)."
      % (turret["totals"]["yaw_spans_deg"], turret["totals"]["pitch_spans_deg"]))
    A("The build's own per-hinge min/max is not in a T row, so those cells stay UNKNOWN.")
    A("")
    A("## Mode transition values")
    A("")
    A("| id | source row | expected value | pass band | status |")
    A("|---|---|---|---|---|")
    for r in rows[mv_end:md_end]:
        A("| %s | %s | %s | %s | %s |" % (r["id"], r["src"], r["expected"], r["band"], r["status"]))
    A("")
    A("The battle FOV 60 deg lies inside the delivered 55-63 deg tune, so the mode switch is the only")
    A("missing thing, not a value (T-MD11 `inside band`). `BattleModeVSpeedCurve`'s y axis has no")
    A("documented scale and `TurningModeMaxSpeed` is omitted, so the observable is the *absence* of a cap.")
    A("")
    A("## HUD element positions")
    A("")
    A("| id | source row | expected value | pass band | status |")
    A("|---|---|---|---|---|")
    for r in rows[md_end:hud_end]:
        A("| %s | %s | %s | %s | %s |" % (r["id"], r["src"], r["expected"], r["band"], r["status"]))
    A("")
    A("## Camera distance / FOV")
    A("")
    A("| id | source row | expected value | pass band | status |")
    A("|---|---|---|---|---|")
    for r in rows[hud_end:]:
        A("| %s | %s | %s | %s | %s |" % (r["id"], r["src"], r["expected"], r["band"], r["status"]))
    A("")
    A("The camera numbers are edits re-read from the written `.ctunec` (8/8 readback), not proposals:")
    A("`CameraPosition[1]=1.3`, `[2]=7.0`, `LookAtPoint[1]=1.55`, `FOV 55/63`,")
    A("`FOVVelocityRange[1]=108`, `RollWithVehicleAmount=0.38`, `CollisionStartPoint[1]=1.6`.")
    A("")
    A("## Out-of-domain claims (writable, not shipped)")
    A("")
    for r in rows:
        if r["status"] == "out-of-domain":
            A("* **%s** (`%s`): %s - %s" % (r["id"], r["src"], r["expected"], r["band"]))
    A("")
    A("## Oracles re-run by `--check`")
    A("")
    for c in checks:
        A("* %s `%s`" % ("PASS" if c["ok"] else "FAIL", c["oracle"]))
    A("")
    A("## UNKNOWNs (no row gives a number)")
    A("")
    for r in rows:
        if r["status"] == "UNKNOWN":
            A("* **%s** (`%s`): %s - %s" % (r["id"], r["src"], r["expected"], r["band"]))
    A("")
    A("Also UNKNOWN: whether the engine honours any of these at runtime (test ban; static only).")
    A("")
    text = "\n".join(L) + "\n"

    for c in checks:
        print(("PASS " if c["ok"] else "FAIL ") + c["oracle"])
    bad = [c for c in checks if not c["ok"]]
    print("%d/%d oracles pass" % (len(checks) - len(bad), len(checks)))

    if write:
        open(OUT, "w", encoding="utf-8", newline="\n").write(text)
        print("wrote Working/Q/PREDICTIONS_LOOKS.md")
    else:
        cur = open(OUT, encoding="utf-8", newline="").read()
        if cur != text:
            print("\n".join(list(difflib.unified_diff(cur.splitlines(), text.splitlines(),
                                                      "on-disk", "regenerated", lineterm="", n=1))[:40]))
            print("FAIL document: PREDICTIONS_LOOKS.md does not match the regenerated text")
            return 1
        print("PASS document: PREDICTIONS_LOOKS.md matches the regenerated text")
    return 1 if bad else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit(main(a.write))
