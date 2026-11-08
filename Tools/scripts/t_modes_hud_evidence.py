#!/usr/bin/env python3
"""t_modes_hud_evidence.py - re-derive six T-15 / T-6 numbers from the files they cite.

Six rows, three from `Working/Translation/T11_MODES.md` (T-MD5, T-MD6, T-MD11) and three from
`Working/Translation/T6_HUD_CAMERA.md` (T-CAM2, T-CAM3, T-CAM5). For each: open the cited file,
recompute the number, and compare with what the row prints. A row whose cited path is missing, or
whose printed number the file does not support, is flagged.

Conversions used (stated, not assumed):
  * cm/s -> km/h: x 0.036 (3600 s/h, 100000 cm/km) - the repo's own factor, used by T-MD6/T-CAM3.
  * UE3 horizontal FOV -> JC3 16:9 vertical FOV: v = 2*atan(tan(h/2) * 9/16).
  * camera composition at rest: distance = MinFreeCameraDistance (spring, fixed because min == max)
    + the back component of StateFreeCameraSitOffsetMin; height = CameraPivotOffset.z
    - StateFreeCameraSitOffsetMin.z.

Read-only: the two documents and the JSONs are opened, never written. Output is
`Working/Translation/MODES_HUD_EVIDENCE.md`.

    python Tools/scripts/t_modes_hud_evidence.py --write
    python Tools/scripts/t_modes_hud_evidence.py --check
"""
from __future__ import annotations

import argparse
import difflib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MODES_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "MODES.json")
CAMERA_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "CAMERA.json")
CAM_TUNE = os.path.join(ROOT, "Working", "Camera", "CAM_TUNE.json")
DOC_T11 = os.path.join(ROOT, "Working", "Translation", "T11_MODES.md")
DOC_T6 = os.path.join(ROOT, "Working", "Translation", "T6_HUD_CAMERA.md")
OUT = os.path.join(ROOT, "Working", "Translation", "MODES_HUD_EVIDENCE.md")


def cms_to_kmh(v: float) -> float:
    return v * 0.036


def vertical_from_horizontal(h_deg: float, aspect: float = 16 / 9) -> float:
    return math.degrees(2 * math.atan(math.tan(math.radians(h_deg) / 2) / aspect))


def main(write: bool) -> int:
    checks = []

    def ok(cond, label, detail=""):
        checks.append({"oracle": label, "ok": bool(cond), "detail": detail})
        return bool(cond)

    modes = json.load(open(MODES_JSON, encoding="utf-8"))
    cam = json.load(open(CAMERA_JSON, encoding="utf-8"))
    tune = json.load(open(CAM_TUNE, encoding="utf-8"))
    md11 = open(DOC_T11, encoding="utf-8").read()
    md6 = open(DOC_T6, encoding="utf-8").read()

    fields = {f["field"]: f for f in modes["fields"]}
    cvals = cam["values"]
    cfgs = cam["configs"]

    def cfg(name):
        return dict(zip(cfgs[name]["fields"], cfgs[name]["values"]))

    cfg1 = cfg("DrivingCamConfig1")
    cfgb = cfg("BattleModeCamConfig")
    tune_edits = {(e["row"], e["path"]): e["readback"] for e in tune["edits"]}

    # ------------------------------------------------------------------ T-MD5
    f5 = fields["BattleModeVSpeedCurve"]
    p5 = f5["struct"]["points"]
    ok([list(p) for p in p5] == [[0.0, 60.0], [600.0, 40.0], [1200.0, 30.0]],
       "T-MD5: MODES.json holds the 3-point BattleModeVSpeedCurve", str(p5))
    ok(f5["same_in_all_four"] and len(f5["packages"]) == 4,
       "T-MD5: the curve is identical in all four packages", f'{len(f5["packages"])} pkg')
    ok(f5["offset"] == 536 and f5["declaring_class"] == "RVehicleSimBatmobile",
       "T-MD5: offset 536 on RVehicleSimBatmobile", f'{f5["declaring_class"]}@{f5["offset"]}')
    ok("0 -> 60, 600 -> 40, 1200 -> 30" in md11,
       "T-MD5: T11_MODES.md prints those three points")

    # ------------------------------------------------------------------ T-MD6
    f6 = fields["TurningModeMaxSpeed"]
    v6 = f6["values"]
    ok(f6["unit"] == "cm/s" and f6["unit_basis"] == "conv",
       "T-MD6: the field's own unit is cm/s (conv basis)", f6["unit"])
    ok(set(v6.values()) == {600.0} and len(v6) == 4,
       "T-MD6: 600.0 in all four packages", str(v6))
    kmh = cms_to_kmh(v6["Playable_Batmobile_SF"])
    ok(abs(kmh - 21.6) < 1e-9, "T-MD6: 600 cm/s x 0.036 = 21.6 km/h", f"{kmh:.6g}")
    ok("600 cm/s = **21.6 km/h**" in md11, "T-MD6: T11_MODES.md prints 21.6 km/h")

    # ------------------------------------------------------------------ T-MD11
    ok(cvals["BattleModeCamFOV"] == 60.0 and cvals["BattleModeWinchCamFOV"] == 60.0
       and cvals["AntiPersonelBattleModeCamFOV"] == 40.0,
       "T-MD11: CAMERA.json holds 60 / 60 / 40 deg",
       str((cvals["BattleModeCamFOV"], cvals["BattleModeWinchCamFOV"],
            cvals["AntiPersonelBattleModeCamFOV"])))
    ok(len(cfgs["BattleModeCamConfig"]["fields"]) == 24,
       "T-MD11: BattleModeCamConfig carries 24 named fields",
       str(len(cfgs["BattleModeCamConfig"]["fields"])))
    ok(cfgb["MinFreeCameraDistance"] == 1000.0 and cfgb["MaxFreeCameraDistance"] == 1000.0,
       "T-MD11: Min/MaxFreeCameraDistance = 1000/1000 cm",
       str((cfgb["MinFreeCameraDistance"], cfgb["MaxFreeCameraDistance"])))
    lo, hi = sorted((tune_edits[("T-CAM2", "FOV[0]")], tune_edits[("T-CAM2", "FOV[1]")]))
    ok(lo <= cvals["BattleModeCamFOV"] <= hi,
       f"T-MD11: 60 deg lies inside the delivered tune's {lo:g}..{hi:g} deg FOV band",
       f"{lo}..{hi}")
    ok("`BattleModeCamFOV` 60" in md11 and "`AntiPersonelBattleModeCamFOV` 40" in md11
       and "`MinFreeCameraDistance`/`MaxFreeCameraDistance` 1000/1000 cm" in md11,
       "T-MD11: T11_MODES.md prints 60 / 40 / 1000-1000")

    # ------------------------------------------------------------------ T-CAM2
    ok(cvals["DrivingCamFOV1"] == 85.0 and cvals["BoostingCamFOV1"] == 95.0
       and cvals["DrivingCamMaxExtraFOV1"] == 10.0,
       "T-CAM2: CAMERA.json holds 85 h / 95 h / +10",
       str((cvals["DrivingCamFOV1"], cvals["BoostingCamFOV1"], cvals["DrivingCamMaxExtraFOV1"])))
    v85 = vertical_from_horizontal(cvals["DrivingCamFOV1"])
    v95 = vertical_from_horizontal(cvals["BoostingCamFOV1"])
    v105 = vertical_from_horizontal(cvals["BoostingCamFOV1"] + cvals["DrivingCamMaxExtraFOV1"])
    v100 = vertical_from_horizontal(100.0)
    ok(round(v85) == 55, f"T-CAM2: 85 h -> {v85:.2f} v, rounds to 55")
    ok(round(v95) == 63, f"T-CAM2: 95 h -> {v95:.2f} v, rounds to 63")
    ok(abs(v105 - 72.5) < 0.05,
       f"T-CAM2: 95 h + the 10 deg bonus = 105 h -> {v105:.1f} v, not 68", f"{v105:.2f}")
    ok(abs(v100 - 67.7) < 0.05,
       f"T-CAM2: 68 v is the 16:9 vertical of ~100 h ({v100:.1f}), so the row's '68' clause "
       "does not follow from 85/95/+10", f"{v100:.2f}")
    ok(tune_edits[("T-CAM2", "FOV[0]")] == 55.0 and tune_edits[("T-CAM2", "FOV[1]")] == 63.0,
       "T-CAM2: the delivered tune reads back 55 / 63 vertical",
       str((tune_edits[("T-CAM2", "FOV[0]")], tune_edits[("T-CAM2", "FOV[1]")])))
    ok("`DrivingCamFOV` 85 **h**, `BoostingCamFOV` 95 **h**, `MaxExtraFOV` 10" in md6,
       "T-CAM2: T6_HUD_CAMERA.md prints 85 h / 95 h / 10")

    # ------------------------------------------------------------------ T-CAM3
    ok(cvals["DrivingCamFOVInterpMaxSpeed1"] == 3000.0,
       "T-CAM3: CAMERA.json holds 3000 cm/s",
       str(cvals["DrivingCamFOVInterpMaxSpeed1"]))
    kmh3 = cms_to_kmh(cvals["DrivingCamFOVInterpMaxSpeed1"])
    ok(abs(kmh3 - 108.0) < 1e-9, "T-CAM3: 3000 cm/s x 0.036 = 108 km/h", f"{kmh3!r}")
    ok("3000 cm/s = 108 km/h" in md6, "T-CAM3: T6_HUD_CAMERA.md prints 108 km/h")
    ok(tune_edits[("T-CAM3", "FOVVelocityRange[1]")] == 108.0,
       "T-CAM3: the delivered tune reads back FOVVelocityRange[1] = 108")

    # ------------------------------------------------------------------ T-CAM5
    sit = cfg1["StateFreeCameraSitOffsetMin"]
    pivot = cfg1["CameraPivotOffset"]
    ok(sit == [-300.0, 0.0, -25.0], "T-CAM5: sit offset at rest is [-300, 0, -25] cm", str(sit))
    ok(cfg1["MinFreeCameraDistance"] == 400.0 and cfg1["MaxFreeCameraDistance"] == 400.0,
       "T-CAM5: Min == Max == 400 cm, so the boom is fixed",
       str((cfg1["MinFreeCameraDistance"], cfg1["MaxFreeCameraDistance"])))
    ok(pivot == [0.0, 0.0, 155.0], "T-CAM5: CameraPivotOffset is 155 cm up", str(pivot))
    back_cm = abs(sit[0]) + cfg1["MinFreeCameraDistance"]
    up_cm = pivot[2] + sit[2]
    ok(back_cm == 700.0 and up_cm == 130.0,
       "T-CAM5: 300 + 400 = 700 cm back, 155 - 25 = 130 cm up",
       f"{back_cm:g} / {up_cm:g}")
    ok(tune_edits[("T-CAM5", "CameraPosition[2]")] == 7.0
       and abs(tune_edits[("T-CAM5", "CameraPosition[1]")] - 1.3) < 1e-6
       and abs(tune_edits[("T-CAM5", "LookAtPoint[1]")] - 1.55) < 1e-6,
       "T-CAM5: the delivered tune reads back 7.00 / 1.30 / 1.55 m",
       str([tune_edits[("T-CAM5", k)] for k in ("CameraPosition[2]", "CameraPosition[1]",
                                                "LookAtPoint[1]")]))
    ok("**700 cm back, 25 cm down**" in md6 and "`CameraPosition [0,1.30,7.00]`" in md6
       and "`LookAtPoint [0,1.55,0]`" in md6,
       "T-CAM5: T6_HUD_CAMERA.md prints 700 cm / 1.30 / 7.00 / 1.55")

    # ------------------------------------------------------------------ missing paths
    for p in (MODES_JSON, CAMERA_JSON, CAM_TUNE, DOC_T11, DOC_T6):
        ok(os.path.isfile(p), f"cited input exists: {os.path.relpath(p, ROOT)}")

    # ------------------------------------------------------------------ the document
    rows = [
        ("T-MD5", "T11_MODES.md", "`BattleModeVSpeedCurve` 0->60, 600->40, 1200->30, same in all 4",
         "`MODES.json` field `BattleModeVSpeedCurve` (struct.points), offset 536, 4 packages",
         "holds"),
        ("T-MD6", "T11_MODES.md", "`TurningModeMaxSpeed` 600 cm/s = 21.6 km/h",
         "`MODES.json` field `TurningModeMaxSpeed`, 600.0 in all 4 packages, unit cm/s",
         "holds"),
        ("T-MD11", "T11_MODES.md", "`BattleModeCamFOV` 60, winch 60, AntiPersonel 40; "
         "`BattleModeCamConfig` 24 fields, Min/Max 1000/1000; 60 inside 55-63",
         "`CAMERA.json` values + configs.BattleModeCamConfig; `CAM_TUNE.json` FOV readback",
         "holds"),
        ("T-CAM2", "T6_HUD_CAMERA.md", "`DrivingCamFOV` 85 h, `BoostingCamFOV` 95 h, +10 -> "
         "FOV 55..63 v",
         "`CAMERA.json` `DrivingCamFOV1` 85, `BoostingCamFOV1` 95, "
         "`DrivingCamMaxExtraFOV1` 10; `CAM_TUNE.json` 55/63",
         "**flagged** (values hold; the 68 / \"95 is a gap\" clause does not)"),
        ("T-CAM3", "T6_HUD_CAMERA.md", "`DrivingCamFOVInterpMaxSpeed` 3000 cm/s = 108 km/h",
         "`CAMERA.json` `DrivingCamFOVInterpMaxSpeed1` 3000.0; `CAM_TUNE.json` readback 108",
         "holds"),
        ("T-CAM5", "T6_HUD_CAMERA.md", "700 cm back, 25 cm down; `CameraPosition [0,1.30,7.00]`, "
         "`LookAtPoint [0,1.55,0]`",
         "`CAMERA.json` `DrivingCamConfig1` sit/pivot/distance; `CAM_TUNE.json` 7.00/1.30/1.55",
         "holds"),
    ]

    L: list[str] = []
    ap = L.append
    ap("# Six T-15 / T-6 numbers, re-derived from the files they cite")
    ap("")
    ap("**Verdict: 5 of the 6 rows hold; `T-CAM2` is flagged.** Its proposed 55/63 FOV values are")
    ap("exactly the 16:9 vertical of UE3's 85/95 horizontal, but the same cell also says \"68 only")
    ap("if the +10 speed bonus is folded in\" and \"95 boost is a gap\" - and neither follows from")
    ap("the file: 95 h + 10 = 105 h converts to 72.5 v, and 95 h alone is the very 63 the row")
    ap("proposes, so the boost FOV is not a gap. No cited path is missing; no other number")
    ap("differs from its source.")
    ap("")
    ap("| row | document | what the row prints | re-derived from | verdict |")
    ap("|---|---|---|---|---|")
    for rid, doc, claim, src, verdict in rows:
        ap(f"| `{rid}` | {doc} | {claim} | {src} | {verdict} |")
    ap("")
    ap("Conversions, stated so they can be checked: cm/s -> km/h is x 0.036; UE3 horizontal ->")
    ap("JC3 16:9 vertical is `2*atan(tan(h/2) * 9/16)`; the camera's rest composition is the fixed")
    ap("boom (`MinFreeCameraDistance`, because min == max) plus the back/up components of the sit")
    ap("offset, measured from `CameraPivotOffset`.")
    ap("")
    ap("## T-MD5 - top speed curve (T11_MODES.md)")
    ap("")
    ap("Row text: `BattleModeVSpeedCurve` \"3 points ... 0 -> 60, 600 -> 40, 1200 -> 30;")
    ap("identical in all four packages = True\".")
    ap("")
    ap("`Research/BatmobileGrab/MODES.json`, field `BattleModeVSpeedCurve` "
       f"(`{f5['declaring_class']}`, offset {f5['offset']}, declared `{f5['declared_type']}`):")
    ap("")
    ap(f"* `struct.points` = {json.dumps(p5)} - the three points, verbatim.")
    ap(f"* `packages` = {len(f5['packages'])} entries, `same_in_all_four` = "
       f"{f5['same_in_all_four']}.")
    ap(f"* unit `{f5['unit']}` on the `{f5['unit_basis']}` basis - so the y values are printed raw, "
       "as the row says.")
    ap("")
    ap("Verdict: **holds**.")
    ap("")
    ap("## T-MD6 - turning-mode cap (T11_MODES.md)")
    ap("")
    ap("Row text: `TurningModeMaxSpeed` \"600 cm/s = **21.6 km/h**\".")
    ap("")
    ap(f"* `MODES.json` gives {json.dumps(v6)} (all four packages), declared type "
       f"`{f6['declared_type']}`, unit `{f6['unit']}` on the `{f6['unit_basis']}` basis.")
    ap(f"* 600 x 0.036 = {kmh:g} km/h.")
    ap("")
    ap("Verdict: **holds**.")
    ap("")
    ap("## T-MD11 - battle camera FOV and config (T11_MODES.md)")
    ap("")
    ap("Row text: `BattleModeCamFOV` 60, `BattleModeWinchCamFOV` 60, "
       "`AntiPersonelBattleModeCamFOV` 40; `BattleModeCamConfig` 24 fields with "
       "`MinFreeCameraDistance`/`MaxFreeCameraDistance` 1000/1000 cm; FOV 60 inside the tune's "
       "55-63.")
    ap("")
    ap(f"* `CAMERA.json` values: {cvals['BattleModeCamFOV']:g} / "
       f"{cvals['BattleModeWinchCamFOV']:g} / {cvals['AntiPersonelBattleModeCamFOV']:g} deg.")
    ap(f"* `configs.BattleModeCamConfig` names {len(cfgs['BattleModeCamConfig']['fields'])} fields; "
       f"`MinFreeCameraDistance` = {cfgb['MinFreeCameraDistance']:g}, "
       f"`MaxFreeCameraDistance` = {cfgb['MaxFreeCameraDistance']:g} cm.")
    ap(f"* `Working/Camera/CAM_TUNE.json` reads the delivered FOV back as {lo:g} and {hi:g} deg, "
       f"and 60 lies inside that band.")
    ap("")
    ap("Verdict: **holds**.")
    ap("")
    ap("## T-CAM2 - driving and boost FOV (T6_HUD_CAMERA.md) - FLAGGED")
    ap("")
    ap("Row text: \"`DrivingCamFOV` 85 **h**, `BoostingCamFOV` 95 **h**, `MaxExtraFOV` 10\" ->")
    ap("\"`FOV [55,63]` v; 68 only if the +10 speed bonus is folded in; **95 boost is a gap**\".")
    ap("")
    ap("`CAMERA.json`: `DrivingCamFOV1` = " + f"{cvals['DrivingCamFOV1']:g}" +
       ", `BoostingCamFOV1` = " + f"{cvals['BoostingCamFOV1']:g}" +
       ", `DrivingCamMaxExtraFOV1` = " + f"{cvals['DrivingCamMaxExtraFOV1']:g}" + ".")
    ap("")
    ap("| horizontal | 16:9 vertical | rounded |")
    ap("|---|---:|---:|")
    ap(f"| 85 (driving) | {v85:.2f} | 55 |")
    ap(f"| 95 (boost) | {v95:.2f} | 63 |")
    ap(f"| 105 (95 + the 10 deg bonus) | {v105:.2f} | 72 |")
    ap(f"| 100 (for reference) | {v100:.2f} | 68 |")
    ap("")
    ap(f"* The two values the row proposes, **55 and 63, are exactly 85 and 95 converted** - "
       f"`CAM_TUNE.json` also reads them back as {tune_edits[('T-CAM2','FOV[0]')]:g} and "
       f"{tune_edits[('T-CAM2','FOV[1]')]:g}. Those hold.")
    ap("** * **But the row's own gloss contradicts them.** If 95 h is the 63 the row ships, then")
    ap("  the boost FOV is not \"a gap\"; and folding the +10 in gives 105 h -> 72.5 v, not 68.")
    ap(f"  68 v is the 16:9 vertical of ~100 h ({v100:.2f}), which no quoted BmAK value produces.")
    ap("")
    ap("Verdict: **flagged** - the numbers 55/63 hold; the \"68\" and \"95 boost is a gap\" clauses")
    ap("do not. Either the 63 came from 95 h (and the gap claim is wrong) or the 63 came from")
    ap("somewhere else (and then 95 h is untranslated) - the cell cannot have both.")
    ap("")
    ap("## T-CAM3 - FOV interp speed (T6_HUD_CAMERA.md)")
    ap("")
    ap("Row text: \"`DrivingCamFOVInterpMaxSpeed` 3000 cm/s\" -> \"3000 cm/s = 108 km/h\".")
    ap("")
    ap(f"* `CAMERA.json` `DrivingCamFOVInterpMaxSpeed1` = "
       f"{cvals['DrivingCamFOVInterpMaxSpeed1']:g} cm/s.")
    ap(f"* 3000 x 0.036 = {kmh3:g} km/h; `CAM_TUNE.json` reads `FOVVelocityRange[1]` back as "
       f"{tune_edits[('T-CAM3','FOVVelocityRange[1]')]:g}.")
    ap("")
    ap("Verdict: **holds**.")
    ap("")
    ap("## T-CAM5 - camera composition at rest (T6_HUD_CAMERA.md)")
    ap("")
    ap("Row text: `DrivingCamConfig1` sit `[-300,0,-25]` at rest, distance 400/400, pivot "
       "`[0,0,155]` -> \"**700 cm back, 25 cm down**\", `CameraPosition [0,1.30,7.00]`, "
       "`LookAtPoint [0,1.55,0]`.")
    ap("")
    ap("`CAMERA.json` `configs.DrivingCamConfig1`:")
    ap("")
    ap(f"* `StateFreeCameraSitOffsetMin` = {json.dumps(sit)} cm; "
       f"`MinFreeCameraDistance` = {cfg1['MinFreeCameraDistance']:g}, "
       f"`MaxFreeCameraDistance` = {cfg1['MaxFreeCameraDistance']:g} cm (min == max, so the boom "
       "is fixed at 4.00 m).")
    ap(f"* `CameraPivotOffset` = {json.dumps(pivot)} cm.")
    ap(f"* back = |{sit[0]:g}| + {cfg1['MinFreeCameraDistance']:g} = {back_cm:g} cm = 7.00 m; "
       f"height = {pivot[2]:g} + ({sit[2]:g}) = {up_cm:g} cm = 1.30 m; the look-at pivot stays at "
       f"{pivot[2]:g} cm = 1.55 m.")
    ap(f"* `CAM_TUNE.json` reads back CameraPosition[2] = "
       f"{tune_edits[('T-CAM5','CameraPosition[2]')]:g}, CameraPosition[1] = "
       f"{tune_edits[('T-CAM5','CameraPosition[1]')]:.2f}, LookAtPoint[1] = "
       f"{tune_edits[('T-CAM5','LookAtPoint[1]')]:.2f}.")
    ap("")
    ap("Verdict: **holds** (the \"25 cm down\" in the row is the sit offset's own z; the delivered")
    ap("`CameraPosition[1]` 1.30 is the pivot minus that offset, which is the number the tune")
    ap("carries).")
    ap("")
    ap("## Missing paths")
    ap("")
    ap("None. Every cited file was opened: `Research/BatmobileGrab/MODES.json`,")
    ap("`Research/BatmobileGrab/CAMERA.json`, `Working/Camera/CAM_TUNE.json`,")
    ap("`Working/Translation/T11_MODES.md`, `Working/Translation/T6_HUD_CAMERA.md`.")
    ap("")
    ap("## UNKNOWNs")
    ap("")
    ap("* **What the BmAK boost FOV should become if the +10 bonus is real.** 105 h -> 72.5 v is")
    ap("  arithmetic; whether the bonus applies on top of the boost FOV or is already inside it is")
    ap("  not stated in `CAMERA.json`, and the native camera code that would decide it is not")
    ap("  re-read here. UNKNOWN.")
    ap("* **Whether T-CAM2's 63 was meant to be the boost FOV or the top of a band.** The tune")
    ap("  itself only holds `FOV[0]`/`FOV[1]` (55/63) with no per-source attribution; the cell's")
    ap("  wording is the only place the two readings differ.")
    ap("* **The y axis of `BattleModeVSpeedCurve`** stays unitless (the row says so); nothing here")
    ap("  turns 60/40/30 into a speed.")
    ap("* No game was launched (test ban); the only runtime-adjacent numbers are the `CAM_TUNE.json`")
    ap("  read-backs of the file that was written, not an in-game observation.")
    ap("")
    ap("## Oracles re-run by `--check`")
    ap("")
    for c in checks:
        ap(f"* {'PASS' if c['ok'] else 'FAIL'} {c['oracle']}")
    ap("")
    ap("## Labels")
    ap("")
    ap("Decoded: every JSON value, the tune read-backs, the document strings. Derived: the cm/s ->")
    ap("km/h and horizontal -> vertical conversions, the 700/130 cm composition, the 68-vs-100-h")
    ap("finding. UNKNOWN: the three items above.")
    ap("")
    text = "\n".join(L)

    failed = [c for c in checks if not c["ok"]]
    for c in checks:
        print(f"{'PASS' if c['ok'] else 'FAIL'} {c['oracle']}"
              + (f" [{c['detail']}]" if c["detail"] and not c["ok"] else ""))
    print(f"{len(checks) - len(failed)}/{len(checks)} oracles pass")
    if failed:
        return 1
    if write:
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"wrote {os.path.relpath(OUT, ROOT).replace(os.sep, '/')}")
        return 0
    current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
    if current != text:
        for line in difflib.unified_diff(current.splitlines(), text.splitlines(),
                                         "on-disk", "recomputed", lineterm="", n=1):
            print(line)
        print("FAIL document differs from the regenerated text")
        return 1
    print("PASS document: MODES_HUD_EVIDENCE.md matches the regenerated text")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="write MODES_HUD_EVIDENCE.md")
    ap.add_argument("--check", action="store_true", help="re-derive and compare")
    args = ap.parse_args()
    sys.exit(main(write=args.write))
