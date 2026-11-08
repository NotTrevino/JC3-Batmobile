STATUS: done - 34 prediction lines (25 predicted, 9 UNKNOWN), 27/27 source oracles pass, `--check` green.

# V-05 part 3 - look/static, mode, HUD and camera predictions

## Result

`Working/Q/PREDICTIONS_LOOKS.md` is a new sheet, separate from `PREDICTIONS.md` and the
non-existent `PREDICTIONS_COMBAT.md`. Every line carries its source row, the expected value and a
pass band; nine lines are UNKNOWN because no row gives a number (listed below, each with what is
missing).

Sections: Q-1 static/looks (8 rows), moving parts at standstill (7), mode transition values (5),
HUD element positions (6), camera distance/FOV (8). Build under test: `Builds/bm-RC2`, wiring
re-read from `Builds/bm-RC2/verify/wiring.json`.

Key predicted values (all re-derived by the check):

* camera: `CameraPosition [0,1.30,7.00]` (7.0 m +-0.5), `LookAtPoint [0,1.55,0]`,
  FOV 55 -> 63, FOV stops at 108 +-5 km/h, roll 0.38, collision point 1.6 m;
* HUD: 2 clips, cooldown 0/0.25/0.50/0.75/1.00 over 360 deg, reticle shape 8 with marker y -111,
  lock-on POI 21 rotating once per 1.5 s, infinite ammo, no heat bar;
* modes: battle FOV 60 lies inside the delivered 55-63 band (no value change), `ArmourModeDamageReduction`
  0, battle speed curve 0->60 / 600->40 / 1200->30 raw, `TurningModeMaxSpeed` 21.6 km/h omitted
  (observable = the car passes 25 km/h), turn-on-spot is a named omission (0 driving-module hits);
* moving parts: fleet yaw spans 150/300/358 deg, pitch spans 25-100 deg, 0 full-rotation turret
  hinges in 233 entities;
* lights: 8 lamp parts, manifest hosts 21 T-18 rows (B-07 packed 18 entries);
* audio: 5 slots, 4/5 within +-1 LU (max 2.33 LU), 3 loop slots, 1 loop click - V-04 already
  measured the loudness and loop gates red, so Q1-8 says to expect those two to fail.

## Files written

| file | sha256 |
|---|---|
| `Tools/scripts/v05_looks.py` | `d63a2631c82301ee18219b3591007d8752a6167d67b2ab6c8609a1b6c106e3a5` |
| `Working/Q/PREDICTIONS_LOOKS.md` | `dad5fc6bbebc37997a557b6973f103236f0eb48a1d4a70ce84ce6610cc7a09c7` |
| `tmp/freebuff/reports/v05-predictions-part3.md` | this report |

`PREDICTIONS.md` / `predictions.json` and `PREDICTIONS_COMBAT.md` were not touched.

## Commands and verbatim output

```
$ python Tools/scripts/v05_looks.py --write
PASS CAM_TUNE CameraPosition [1]=1.3 [2]=7.0
PASS CAM_TUNE LookAtPoint[1]=1.55
PASS CAM_TUNE FOV 55/63
PASS CAM_TUNE FOVVelocityRange[1]=108
PASS CAM_TUNE roll 0.38
PASS CAM_TUNE collision 1.6
PASS CAM_TUNE 8/8 readback
PASS T-15 tune 7.0/1.3/55-63
PASS BattleModeVSpeedCurve 3 points
PASS battle curve identical in 4 packages
PASS ArmourModeDamageReduction 0
PASS battle camera FOV 60/60/40
PASS battle camera config 1000/1000 cm
PASS turn-on-spot named omission
PASS turn-on-spot 0 driving-module hits
PASS T-19 10 rows 6/2/2
PASS T-19 reticle marker y -111
PASS T-19 cooldown 360 deg
PASS T-19 lock-on rotation 1.5 s
PASS T-19 lock-on POI type 21
PASS T-19 two weapon clips
PASS TURRET_LIMITS yaw spans 150/300/358
PASS TURRET_LIMITS pitch spans 25..100
PASS no full-rotation turret in the fleet
PASS bm-RC2 9 SWeaponPoints, 0 dangling
PASS 21 hosted T-18 rows on 8 lamp parts
PASS 5 audio slots
27/27 oracles pass
wrote Working/Q/PREDICTIONS_LOOKS.md
write_exit=0
```

```
$ python Tools/scripts/v05_looks.py --check
PASS CAM_TUNE CameraPosition [1]=1.3 [2]=7.0
PASS CAM_TUNE LookAtPoint[1]=1.55
PASS CAM_TUNE FOV 55/63
PASS CAM_TUNE FOVVelocityRange[1]=108
PASS CAM_TUNE roll 0.38
PASS CAM_TUNE collision 1.6
PASS CAM_TUNE 8/8 readback
PASS T-15 tune 7.0/1.3/55-63
PASS BattleModeVSpeedCurve 3 points
PASS battle curve identical in 4 packages
PASS ArmourModeDamageReduction 0
PASS battle camera FOV 60/60/40
PASS battle camera config 1000/1000 cm
PASS turn-on-spot named omission
PASS turn-on-spot 0 driving-module hits
PASS T-19 10 rows 6/2/2
PASS T-19 reticle marker y -111
PASS T-19 cooldown 360 deg
PASS T-19 lock-on rotation 1.5 s
PASS T-19 lock-on POI type 21
PASS T-19 two weapon clips
PASS TURRET_LIMITS yaw spans 150/300/358
PASS TURRET_LIMITS pitch spans 25..100
PASS no full-rotation turret in the fleet
PASS bm-RC2 9 SWeaponPoints, 0 dangling
PASS 21 hosted T-18 rows on 8 lamp parts
PASS 5 audio slots
27/27 oracles pass
PASS document: PREDICTIONS_LOOKS.md matches the regenerated text
check_exit=0
```

Earlier failing draft (kept for honesty): the first run failed 2 oracles because the light and
audio JSONs do not use the keys I first assumed (`lights["entries"]`, `audio["slots"]`). I
re-read both files (`lamps` 8 + `t18_hosting.rows_hosted_count` 21; `summary.slots` 5 + `rows` 5)
and pointed the oracles at the real fields; no band was loosened.

## UNKNOWNs (no row gives a number)

* `ANI-7` steering yoke angle - the row says the yoke turns, no row states a rotation.
* `ANI-4` turbine spin rate - spin is named, no rate/angle in any row.
* `ANI-2b` the build's own cannon pitch min/max - only the fleet band (25-100 deg) is decoded.
* `ANI-3` Vulcan barrel spin angle/rate - named behaviour, no number.
* `ANI-6` missile hatch open angle - named behaviour, no number.
* `ANI-5` air-brake fins - the row is itself a one-variable probe (do they move at all?).
* `T-HUD15` BmAK accuracy frame -> `reticle_size` (5..30 px) - the member exists, the pixel map does not.
* `T-CAM9` spring stiffness bridge - no unit bridge from BmAK smoothing to JC3 springs (T-CAM9 blocked).
* `T-CAM11` boost/wheelspin shake - no numeric bridge.

Also UNKNOWN: whether the game honours any predicted value at runtime; the test ban stays, nothing
was installed or launched.

## Label

Values are **decoded** from the named JSON/MD sources or **derived** by the stated arithmetic
(e.g. 600 cm/s = 21.6 km/h); the nine items above are **UNKNOWN**, not filled in.
