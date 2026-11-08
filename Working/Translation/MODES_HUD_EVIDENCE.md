# Six T-15 / T-6 numbers, re-derived from the files they cite

**Verdict: 5 of the 6 rows hold; `T-CAM2` is flagged.** Its proposed 55/63 FOV values are
exactly the 16:9 vertical of UE3's 85/95 horizontal, but the same cell also says "68 only
if the +10 speed bonus is folded in" and "95 boost is a gap" - and neither follows from
the file: 95 h + 10 = 105 h converts to 72.5 v, and 95 h alone is the very 63 the row
proposes, so the boost FOV is not a gap. No cited path is missing; no other number
differs from its source.

| row | document | what the row prints | re-derived from | verdict |
|---|---|---|---|---|
| `T-MD5` | T11_MODES.md | `BattleModeVSpeedCurve` 0->60, 600->40, 1200->30, same in all 4 | `MODES.json` field `BattleModeVSpeedCurve` (struct.points), offset 536, 4 packages | holds |
| `T-MD6` | T11_MODES.md | `TurningModeMaxSpeed` 600 cm/s = 21.6 km/h | `MODES.json` field `TurningModeMaxSpeed`, 600.0 in all 4 packages, unit cm/s | holds |
| `T-MD11` | T11_MODES.md | `BattleModeCamFOV` 60, winch 60, AntiPersonel 40; `BattleModeCamConfig` 24 fields, Min/Max 1000/1000; 60 inside 55-63 | `CAMERA.json` values + configs.BattleModeCamConfig; `CAM_TUNE.json` FOV readback | holds |
| `T-CAM2` | T6_HUD_CAMERA.md | `DrivingCamFOV` 85 h, `BoostingCamFOV` 95 h, +10 -> FOV 55..63 v | `CAMERA.json` `DrivingCamFOV1` 85, `BoostingCamFOV1` 95, `DrivingCamMaxExtraFOV1` 10; `CAM_TUNE.json` 55/63 | **flagged** (values hold; the 68 / "95 is a gap" clause does not) |
| `T-CAM3` | T6_HUD_CAMERA.md | `DrivingCamFOVInterpMaxSpeed` 3000 cm/s = 108 km/h | `CAMERA.json` `DrivingCamFOVInterpMaxSpeed1` 3000.0; `CAM_TUNE.json` readback 108 | holds |
| `T-CAM5` | T6_HUD_CAMERA.md | 700 cm back, 25 cm down; `CameraPosition [0,1.30,7.00]`, `LookAtPoint [0,1.55,0]` | `CAMERA.json` `DrivingCamConfig1` sit/pivot/distance; `CAM_TUNE.json` 7.00/1.30/1.55 | holds |

Conversions, stated so they can be checked: cm/s -> km/h is x 0.036; UE3 horizontal ->
JC3 16:9 vertical is `2*atan(tan(h/2) * 9/16)`; the camera's rest composition is the fixed
boom (`MinFreeCameraDistance`, because min == max) plus the back/up components of the sit
offset, measured from `CameraPivotOffset`.

## T-MD5 - top speed curve (T11_MODES.md)

Row text: `BattleModeVSpeedCurve` "3 points ... 0 -> 60, 600 -> 40, 1200 -> 30;
identical in all four packages = True".

`Research/BatmobileGrab/MODES.json`, field `BattleModeVSpeedCurve` (`RVehicleSimBatmobile`, offset 536, declared `FInterpCurveFloat`):

* `struct.points` = [[0.0, 60.0], [600.0, 40.0], [1200.0, 30.0]] - the three points, verbatim.
* `packages` = 4 entries, `same_in_all_four` = True.
* unit `curve (cm/s -> factor)` on the `type` basis - so the y values are printed raw, as the row says.

Verdict: **holds**.

## T-MD6 - turning-mode cap (T11_MODES.md)

Row text: `TurningModeMaxSpeed` "600 cm/s = **21.6 km/h**".

* `MODES.json` gives {"Playable_BatmobileFunhouse_SF": 600.0, "Playable_BatmobileJoker_SF": 600.0, "Playable_BatmobileMK2_SF": 600.0, "Playable_Batmobile_SF": 600.0} (all four packages), declared type `float`, unit `cm/s` on the `conv` basis.
* 600 x 0.036 = 21.6 km/h.

Verdict: **holds**.

## T-MD11 - battle camera FOV and config (T11_MODES.md)

Row text: `BattleModeCamFOV` 60, `BattleModeWinchCamFOV` 60, `AntiPersonelBattleModeCamFOV` 40; `BattleModeCamConfig` 24 fields with `MinFreeCameraDistance`/`MaxFreeCameraDistance` 1000/1000 cm; FOV 60 inside the tune's 55-63.

* `CAMERA.json` values: 60 / 60 / 40 deg.
* `configs.BattleModeCamConfig` names 24 fields; `MinFreeCameraDistance` = 1000, `MaxFreeCameraDistance` = 1000 cm.
* `Working/Camera/CAM_TUNE.json` reads the delivered FOV back as 55 and 63 deg, and 60 lies inside that band.

Verdict: **holds**.

## T-CAM2 - driving and boost FOV (T6_HUD_CAMERA.md) - FLAGGED

Row text: "`DrivingCamFOV` 85 **h**, `BoostingCamFOV` 95 **h**, `MaxExtraFOV` 10" ->
"`FOV [55,63]` v; 68 only if the +10 speed bonus is folded in; **95 boost is a gap**".

`CAMERA.json`: `DrivingCamFOV1` = 85, `BoostingCamFOV1` = 95, `DrivingCamMaxExtraFOV1` = 10.

| horizontal | 16:9 vertical | rounded |
|---|---:|---:|
| 85 (driving) | 54.54 | 55 |
| 95 (boost) | 63.09 | 63 |
| 105 (95 + the 10 deg bonus) | 72.49 | 72 |
| 100 (for reference) | 67.67 | 68 |

* The two values the row proposes, **55 and 63, are exactly 85 and 95 converted** - `CAM_TUNE.json` also reads them back as 55 and 63. Those hold.
** * **But the row's own gloss contradicts them.** If 95 h is the 63 the row ships, then
  the boost FOV is not "a gap"; and folding the +10 in gives 105 h -> 72.5 v, not 68.
  68 v is the 16:9 vertical of ~100 h (67.67), which no quoted BmAK value produces.

Verdict: **flagged** - the numbers 55/63 hold; the "68" and "95 boost is a gap" clauses
do not. Either the 63 came from 95 h (and the gap claim is wrong) or the 63 came from
somewhere else (and then 95 h is untranslated) - the cell cannot have both.

## T-CAM3 - FOV interp speed (T6_HUD_CAMERA.md)

Row text: "`DrivingCamFOVInterpMaxSpeed` 3000 cm/s" -> "3000 cm/s = 108 km/h".

* `CAMERA.json` `DrivingCamFOVInterpMaxSpeed1` = 3000 cm/s.
* 3000 x 0.036 = 108 km/h; `CAM_TUNE.json` reads `FOVVelocityRange[1]` back as 108.

Verdict: **holds**.

## T-CAM5 - camera composition at rest (T6_HUD_CAMERA.md)

Row text: `DrivingCamConfig1` sit `[-300,0,-25]` at rest, distance 400/400, pivot `[0,0,155]` -> "**700 cm back, 25 cm down**", `CameraPosition [0,1.30,7.00]`, `LookAtPoint [0,1.55,0]`.

`CAMERA.json` `configs.DrivingCamConfig1`:

* `StateFreeCameraSitOffsetMin` = [-300.0, 0.0, -25.0] cm; `MinFreeCameraDistance` = 400, `MaxFreeCameraDistance` = 400 cm (min == max, so the boom is fixed at 4.00 m).
* `CameraPivotOffset` = [0.0, 0.0, 155.0] cm.
* back = |-300| + 400 = 700 cm = 7.00 m; height = 155 + (-25) = 130 cm = 1.30 m; the look-at pivot stays at 155 cm = 1.55 m.
* `CAM_TUNE.json` reads back CameraPosition[2] = 7, CameraPosition[1] = 1.30, LookAtPoint[1] = 1.55.

Verdict: **holds** (the "25 cm down" in the row is the sit offset's own z; the delivered
`CameraPosition[1]` 1.30 is the pivot minus that offset, which is the number the tune
carries).

## Missing paths

None. Every cited file was opened: `Research/BatmobileGrab/MODES.json`,
`Research/BatmobileGrab/CAMERA.json`, `Working/Camera/CAM_TUNE.json`,
`Working/Translation/T11_MODES.md`, `Working/Translation/T6_HUD_CAMERA.md`.

## UNKNOWNs

* **What the BmAK boost FOV should become if the +10 bonus is real.** 105 h -> 72.5 v is
  arithmetic; whether the bonus applies on top of the boost FOV or is already inside it is
  not stated in `CAMERA.json`, and the native camera code that would decide it is not
  re-read here. UNKNOWN.
* **Whether T-CAM2's 63 was meant to be the boost FOV or the top of a band.** The tune
  itself only holds `FOV[0]`/`FOV[1]` (55/63) with no per-source attribution; the cell's
  wording is the only place the two readings differ.
* **The y axis of `BattleModeVSpeedCurve`** stays unitless (the row says so); nothing here
  turns 60/40/30 into a speed.
* No game was launched (test ban); the only runtime-adjacent numbers are the `CAM_TUNE.json`
  read-backs of the file that was written, not an in-game observation.

## Oracles re-run by `--check`

* PASS T-MD5: MODES.json holds the 3-point BattleModeVSpeedCurve
* PASS T-MD5: the curve is identical in all four packages
* PASS T-MD5: offset 536 on RVehicleSimBatmobile
* PASS T-MD5: T11_MODES.md prints those three points
* PASS T-MD6: the field's own unit is cm/s (conv basis)
* PASS T-MD6: 600.0 in all four packages
* PASS T-MD6: 600 cm/s x 0.036 = 21.6 km/h
* PASS T-MD6: T11_MODES.md prints 21.6 km/h
* PASS T-MD11: CAMERA.json holds 60 / 60 / 40 deg
* PASS T-MD11: BattleModeCamConfig carries 24 named fields
* PASS T-MD11: Min/MaxFreeCameraDistance = 1000/1000 cm
* PASS T-MD11: 60 deg lies inside the delivered tune's 55..63 deg FOV band
* PASS T-MD11: T11_MODES.md prints 60 / 40 / 1000-1000
* PASS T-CAM2: CAMERA.json holds 85 h / 95 h / +10
* PASS T-CAM2: 85 h -> 54.54 v, rounds to 55
* PASS T-CAM2: 95 h -> 63.09 v, rounds to 63
* PASS T-CAM2: 95 h + the 10 deg bonus = 105 h -> 72.5 v, not 68
* PASS T-CAM2: 68 v is the 16:9 vertical of ~100 h (67.7), so the row's '68' clause does not follow from 85/95/+10
* PASS T-CAM2: the delivered tune reads back 55 / 63 vertical
* PASS T-CAM2: T6_HUD_CAMERA.md prints 85 h / 95 h / 10
* PASS T-CAM3: CAMERA.json holds 3000 cm/s
* PASS T-CAM3: 3000 cm/s x 0.036 = 108 km/h
* PASS T-CAM3: T6_HUD_CAMERA.md prints 108 km/h
* PASS T-CAM3: the delivered tune reads back FOVVelocityRange[1] = 108
* PASS T-CAM5: sit offset at rest is [-300, 0, -25] cm
* PASS T-CAM5: Min == Max == 400 cm, so the boom is fixed
* PASS T-CAM5: CameraPivotOffset is 155 cm up
* PASS T-CAM5: 300 + 400 = 700 cm back, 155 - 25 = 130 cm up
* PASS T-CAM5: the delivered tune reads back 7.00 / 1.30 / 1.55 m
* PASS T-CAM5: T6_HUD_CAMERA.md prints 700 cm / 1.30 / 7.00 / 1.55
* PASS cited input exists: Research\BatmobileGrab\MODES.json
* PASS cited input exists: Research\BatmobileGrab\CAMERA.json
* PASS cited input exists: Working\Camera\CAM_TUNE.json
* PASS cited input exists: Working\Translation\T11_MODES.md
* PASS cited input exists: Working\Translation\T6_HUD_CAMERA.md

## Labels

Decoded: every JSON value, the tune read-backs, the document strings. Derived: the cm/s ->
km/h and horizontal -> vertical conversions, the 700/130 cm composition, the 68-vs-100-h
finding. UNKNOWN: the three items above.
