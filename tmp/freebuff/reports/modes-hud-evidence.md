STATUS: DONE — six rows re-derived (T-MD5, T-MD6, T-MD11 from T11_MODES.md; T-CAM2, T-CAM3, T-CAM5 from T6_HUD_CAMERA.md): five hold, `T-CAM2` is flagged for a clause its own numbers contradict, no cited path is missing. `--check` green (35/35, exit 0).

## Files

| file | what |
|---|---|
| `Working/Translation/MODES_HUD_EVIDENCE.md` | 165 lines: verdict table, per-row derivation, conversions, the T-CAM2 finding, UNKNOWNs |
| `Tools/scripts/t_modes_hud_evidence.py` | new, `--write` / `--check`; re-reads `MODES.json`, `CAMERA.json`, `CAM_TUNE.json` and both documents |
| `tmp/freebuff/reports/modes-hud-evidence.md` | this report |

Not edited: `T11_MODES.md`, `T6_HUD_CAMERA.md`, `T_ROWS.jsonl`, any JSON input.

## Verbatim commands

```
cd "E:/Modding/JustCause3/JC3-Batmobile" && PYTHONIOENCODING=utf-8 python Tools/scripts/t_modes_hud_evidence.py --write
cd "E:/Modding/JustCause3/JC3-Batmobile" && PYTHONIOENCODING=utf-8 python Tools/scripts/t_modes_hud_evidence.py --check
```

`--write` -> exit 0, 35/35 oracles, doc written. `--check` -> exit 0, doc byte-identical. (First run failed one oracle on float equality `3000*0.036 == 108.0`; the check now uses a tolerance, the value was never in doubt.)

## Results

| row | prints | re-derived | verdict |
|---|---|---|---|
| `T-MD5` | `BattleModeVSpeedCurve` 0->60, 600->40, 1200->30, same in 4 packages | `MODES.json` `struct.points` = [[0,60],[600,40],[1200,30]], `same_in_all_four` true, 4 packages, offset 536 | **holds** |
| `T-MD6` | `TurningModeMaxSpeed` 600 cm/s = 21.6 km/h | 600.0 in all four packages, unit `cm/s` (conv); 600 × 0.036 = 21.6 | **holds** |
| `T-MD11` | FOV 60 / 60 / 40; `BattleModeCamConfig` 24 fields, Min/Max 1000/1000; 60 inside 55–63 | `CAMERA.json` 60.0/60.0/40.0; config has 24 names, Min=Max=1000.0; `CAM_TUNE.json` read-backs 55/63 | **holds** |
| `T-CAM2` | 85 h, 95 h, +10 -> FOV 55..63 v; "68 only if +10 folded"; "95 boost is a gap" | 85 h -> 54.54 v (55), 95 h -> 63.13 v (63), 95+10 = 105 h -> 72.46 v, 100 h -> 67.7 v | **flagged** |
| `T-CAM3` | 3000 cm/s = 108 km/h | `DrivingCamFOVInterpMaxSpeed1` 3000.0; 3000 × 0.036 = 108; tune read-back 108 | **holds** |
| `T-CAM5` | 700 cm back, 25 cm down; `CameraPosition [0,1.30,7.00]`, `LookAtPoint [0,1.55,0]` | sit [-300,0,-25], Min=Max=400, pivot 155: 300+400 = 700 cm, 155-25 = 130 cm, pivot 155 cm; tune read-backs 7.0 / 1.29999995 / 1.54999995 | **holds** |

## The T-CAM2 flag

The two values it proposes are right: 55 and 63 are exactly the 16:9 vertical of UE3's 85 and 95 horizontal, and `CAM_TUNE.json` reads them back as 55/63. But the same cell adds "68 only if the +10 speed bonus is folded in" and "**95 boost is a gap**":

* 95 h + the 10 deg bonus = 105 h -> **72.5 v**, not 68;
* 68 v is the vertical of ~**100 h** (67.7), which no quoted BmAK value produces;
* and 95 h is the **63 the row itself ships**, so the boost FOV cannot also be "a gap".

So the row can have either the 63 (from 95 h, gap claim wrong) or the gap claim (63 from elsewhere, 95 h untranslated), not both. Flagged, not edited.

## UNKNOWNs

- What the boost FOV should become if the +10 bonus is real (105 h -> 72.5 v is arithmetic; whether the bonus stacks on the boost FOV is not stated in `CAMERA.json`, and the native camera code was not re-read).
- Whether T-CAM2's 63 was meant as the boost FOV or the top of a band: the tune holds only `FOV[0]`/`FOV[1]` (55/63) with no per-source attribution.
- `BattleModeVSpeedCurve`'s y axis stays unitless (60/40/30 are printed raw, nothing converts them).
- No game launched; the only near-runtime numbers are `CAM_TUNE.json` read-backs of a written file, not an in-game observation.

## Labels

Decoded: every JSON value, tune read-back and document string. Derived: cm/s -> km/h (×0.036), horizontal -> vertical (16:9), the 700/130 cm composition, the 68-vs-100-h finding. UNKNOWN: the list above.
