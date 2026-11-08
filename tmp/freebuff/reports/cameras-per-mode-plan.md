# Camera per mode — BmAK values, JC3 carriers, and the number to set

Scope: pull the Batmobile chase distance, height, FOV, lag and boost shake **per mode** out of
`Working/Camera/` and the BmAK grab, find the same quantities in JC3's `GenericVehicleCamera` tune,
state the value to write for each mode, and name the JC3 camera that has **no boost shake member**
plus how to add one.

Companions: `Research/BatmobileGrab/CAMERA.md` (rules + decoded boom composition),
`Research/BatmobileGrab/CAMERA_HELPER.md` (the native tracking helper), `Working/Camera/CAM_REF.md`
(per-entity reference, eight class tunes, tank comparison), `Working/Camera/CAM_TUNE.json` (the exact
edits), `Working/Audio/car_base.xml` (the full 800-byte JC3 camera struct), `Working/Translation/T6_HUD_CAMERA.md`
(rows T-CAM1…T-CAM13).

Two corrections carried in from the existing notes, not re-argued here: test-086 rejected the **old**
candidate because it copied UE3's **horizontal** 85/95° into JC3's **vertical** FOV and body-scaled the
boom (`CAM_REF.md` §4/§5, `CAMERA.md` §6). Everything below uses the decoded composition and the
16:9 conversion, so the values are the corrected set (T6's `T-CAM2`, `3`, `5`, `6`, `12`, `13`).

---

## 1. How BmAK's number becomes a JC3 number

`UpdateCameraPosition` (decoded, `CAMERA.md` §2b) composes:

```text
Loc = anchor − RotToVector(Rotator)·distance + RotateVector(Rotator, Sit)      (+ CameraPivotOffset)
Sit = lerp(SitOffsetMin, pitch > 0 ? SitOffsetUp : SitOffsetDown, (|pitch|/SitOffsetMin|Max)^power)
```

Because `MinFreeCameraDistance == MaxFreeCameraDistance` in every driving config (400/400, 1000/1000),
the boom is **fixed**, and the sit offset is **added on top**. At rest (pitch 0) the camera therefore
sits `boom + |sit.x|` behind the pivot and `pivot.z + sit.z` above the hull origin.

JC3's camera is a `GenericVehicleCamera`, an 800-byte ADF struct (`Working/Audio/car_base.xml`), read
through one `CCameraModifier` path per entity: `CCameraRef CarCameraRef` → `CCameraObject SharedCarCamera`
→ `editor/entities/jc_cameras/vehicle_cameras/car_base.ctune` (`CAM_REF.md` §1). Its geometry is
`CameraPosition` (metres, `+z` = behind), `RotationPoint`, `LookAtPoint`; its view is `FOV` as a
**min/max pair over `FOVVelocityRange` (km/h)**, not a per-state value; its lag is
`Yaw/Pitch/RollSpringStiffness` + `LagSpring`/`LagVelocityScale`.

**FOV conversion** (16:9, `v = 2·atan(tan(h/2)/(16/9))`), the same rule that turns 85 h → 54.5 v and
95 h → 63.1 v:

| BmAK horizontal | 40 | 45 | 60 | 70 | 80 | 85 | 95 | 100 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| JC3 vertical | 23.2 | 26.2 | 36.0 | 43.0 | 50.5 | 54.5 | 63.1 | 67.7 |

(Arithmetic, not a new decode. Note `CAMERA.md` §"FOV units" quotes **68.4 v** for "95+10"; 105 h
actually converts to **72.5 v** and 100 h to **67.7 v** — the 68.4 figure does not reproduce from +10
and is the one number in that paragraph I do not carry forward.)

---

## 2. BmAK per-mode values (decoded)

`EBatmobileDriveCamera` = `EBDC_Camera1`, `EBDC_Camera2`, `EBDC_BonnetCamera` (`CAMERA.md` §1) — two
chase presets, not two vehicles. All values from `CAMERA.md` §2/§2b and `CAMERA.json` `configs`.

| mode | BmAK config | sit min → max (cm) | boom (cm) | pivot (cm) | at-rest camera vs origin | FOV | smoothing | other |
|---|---|---|---|---:|---|---|---|---|
| **Chase 1** (pursuit default) | `DrivingCamConfig1` | `[-300,0,-25]` → `[-400,0,-25]` | 400/400 | `[0,0,155]` | 700 back, 130 up | 85 h / 95 h boost, +10 by speed | `DrivingCamSmoothingStrength1` 30 | lean 7.5°, pitch −20, head impulse 0.5, drift 0.15, max extra translation 50 cm, FOV interp done at 3000 cm/s = 108 km/h |
| **Chase 2** (smooth preset) | `DrivingCamConfig2` | `[-500,0,0]` | 400/400 | `[0,0,155]` | 900 back, 155 up | 85 h / 95 h | `…Strength2` **12** | same lean/pitch; flat, no look-down vector |
| **Boost** (per chase) | `BoostingCamConfig1/2` | `[-200,0,-75]` | 400/400 | `[0,0,155]` | 600 back, 80 up | **95 h** | `BoostingCamSmoothingStrength1` **10000**, `…2` **12** | `BatmobileBoostCameraShake` **35**, wheelspin **50×50×25**, `AdvancedOptions` interval **0.1 s**, limits **2000 / 10000** |
| **Airborne / jump** | (active chase) | — | — | — | — | — | `AirborneCamSmoothingStrength1/2` 12, `JumpSmoothingStrength` **0.4** | no separate geometry |
| **Battle** | `BattleModeCamConfig` | `[-350,0,200]` → `[-500,0,200]` | **1000/1000** | `[0,0,5]` | 1350 back, 205 up | **60 h** | (config springs 10000/10000) | — |
| **Battle + winch** | `BattleModeWinchCamConfig` | `[-650,0,400]` → `[-800,0,400]`, up `[-900,0,2800]` | **1000/1000** | `[400,0,5]` | 1650 back / 400 up before pivot; **1250 back, 405 up** after pivot x +400 | **60 h** | springs 24 / 8 | `maxPitch` 6000, `MinPitch` −8000, sit power 1.5 |
| **Anti-personnel battle** | `BattleModeCamConfig` | as battle | 1000/1000 | as battle | as battle | **40 h** | as battle | — |
| **Chasing** (takedown / pursuit chase) | `ChasingCamConfig` | `[-2000,0,100]` | 400–600 (a range, unlike the drivers) | `[0,0,-300]` | 2400–2600 back, **−200 up** | **80 h** | springs 16 / 4 | `DefaultCameraPitch` −12000 rotator = **−65.9°** (the low camera only makes sense pitched down) |
| **Bonnet / cockpit** | `EBDC_BonnetCamera` | — | — | — | — | — | — | **no JC3 cockpit camera** (`T6` T-CAM1) |
| **Conversation** | `BatmobileConversationCamConfig` | values not read this pass | — | — | — | **45 h** | — | geometry **UNKNOWN** |
| **Riding-car** | `RidingCarCamFOV` only | — | — | — | — | **60 h** | — | geometry **UNKNOWN** |

Rotor units: `65536 = 360°`, so `maxPitch` 14500 = 79.6°, `MinPitch` −13000 = −71.4° for the drivers;
the winch config is 6000 / −8000 = 33.0° / −44.0°.

---

## 3. JC3's quantities (decoded, `car_base.xml`)

| JC3 member | car | tank (second point) |
|---|---:|---:|
| `CameraPosition` | `[0, 2, 5]` m | `[0, 2, 10]` |
| `CrashingCameraPosition` | `[0, 4.5, 5]` | `[0, 2, 15]` |
| `RotationPoint` | `[0, 1.5, 0]` | `[0, 0, 0]` |
| `LookAtPoint` | `[0, 1.25, 0]` | `[0, 0, -100]` |
| `FOV` / `FOVVelocityRange` | `[30, 55]` over `[5, 50]` km/h | `[30, 45]` over `[2, 30]` |
| `FOVBlendSpring` | 1.9 / 4 / 1.1 (speed/constant/damping) | — |
| `YawSpringStiffness` / `Max` / `DriftYaw` | 0.08 / 0.4 / 0.08 | 1.0 / 1.0 |
| `YawSpringAngleLimit` / `LimitStiffnessPower` | 1° / 0.2 | 180° |
| `PitchSpringStiffness` / `PitchLimit` | 0.12 / `[-70, 10]` | 0.2 / `[-25, 20]` |
| `RollSpringStiffness` / `RollLimit` / `RollWithVehicleAmount` | 1.0 / `[-20, 20]` / 0.3 | 1.0 / 1.0 |
| `LagSpring` | speed 1 / const 5 / damping 1 | 2 / 1 |
| `LagCameraRelativity` / `LagVelocityScale` | 1 / 30 | 0.1 |
| `CameraVelocitySpring` / `LookAtVelocitySpring` | 2/1/2 and 2/1/1.2 | — |
| `FollowCameraRange` | `[-0.5, 2]` | `[-0.5, 1.5]` |
| `ReCenterDelay` / `ReCenterSpeed` | 0 / 0.5 | 1 / 2 |
| `CollisionStartPoint` / `CollisionFudgeFactor` / `CollisionPitchDistance` | `[0,1,0]` / 0.1 / 0.3 | `[0, 3.4, 1.2]` |
| `MinTimeForHalfTurn` | 2 s | — |

**There is no shake member in this struct at all.** The 800-byte definition
(`Working/Audio/car_base.xml`, `<type … GenericVehicleCamera size="800">`) ends at
`SplineFuncOfPitchParams`; no amplitude, frequency, impulse or message field exists. That is the
member the boost shake has to come from somewhere else.

---

## 4. The value to set, per mode

Write these into `bat_base.ctunec` (a byte-for-byte copy of `car_base.ctunec`, 5,968 B, referenced by
renaming the donor `.epe`'s `car_base.ctune` → `bat_base.ctune`: same 14 bytes, 2 bytes differ,
`CAM_REF.md` §1, `CAM_TUNE.json`). Values in metres / degrees.

| mode | `CameraPosition` | `LookAtPoint` | `FOV` (v) | `FOVVelocityRange` | `RollWithVehicleAmount` | lag rows |
|---|---|---|---|---|---|---|
| **Chase 1** | **`[0, 1.30, 7.00]`** | **`[0, 1.55, 0]`** | **`[55, 63]`** | **`[5, 108]`** | **0.38** | `YawSpringStiffness` 0.12, `YawSpringStiffnessMax` 0.6 (derived from 30 > 12; unit bridge still **blocked**, T-CAM9) |
| **Chase 2** | **`[0, 1.55, 9.00]`** | `[0, 1.55, 0]` | `[55, 63]` | `[5, 108]` | 0.38 | keep 0.08 / 0.4 — this is the smooth preset |
| **Boost (chase 1)** | `[0, 1.30, 7.00]` | `[0, 1.55, 0]` | **`[63, 67.7]`** (95 h → 100 h) | `[5, 108]` | 0.38 | keep; BmAK's 10000 smoothing has no JC3 state to set (**blocked**) |
| **Boost (chase 2)** | `[0, 1.55, 9.00]` | `[0, 1.55, 0]` | `[63, 67.7]` | `[5, 108]` | 0.38 | keep 12-equivalent (0.08) |
| **Battle** | **`[0, 2.05, 13.50]`** | **`[0, 0.05, 0]`** | **`[36, 36]`** (60 h) | keep `[5, 50]` | keep 0.38 | keep; battle wants a rigid pivot — `YawSpringStiffnessMax` 1.0 as the tank does (derived) |
| **Battle + winch** | **`[0, 4.05, 12.50]`** | `[0, 0.05, 0]` | `[36, 36]` | keep | keep | keep |
| **Anti-personnel** | as battle | `[0, 0.05, 0]` | **`[23.2, 23.2]`** (40 h) | keep | keep | keep |
| **Chasing** | **`[0, -2.00, 25.00]`** (boom 24.0–26.0; mid 25.0) | `[0, -3.00, 0]` | **`[50.5, 50.5]`** (80 h) | keep | keep | keep; needs the −65.9° default pitch, which JC3 does not expose as a member (see §6) |
| **Airborne / jump** | active chase | active chase | active chase | — | — | **blocked** (BmAK 12 / 0.4 has no member) |
| **Conversation** | UNKNOWN (config values unread) | — | **`[26.2, 26.2]`** (45 h) | — | — | — |
| **Riding-car** | UNKNOWN | — | **`[36.0, 36.0]`** (60 h) | — | — | — |
| **Bonnet** | no carrier — JC3 car has no cockpit camera | — | — | — | — | — |

Derivations, stated: `7.00 = 4.00 boom + 3.00 sit`, `1.30 = 1.55 pivot − 0.25 sit` (T-CAM5/12);
`9.00 = 4.00 + 5.00`, `1.55 = 1.55 + 0`; `13.50 = 10.00 + 3.50`, `2.05 = 0.05 + 2.00`;
`12.50 = 10.00 + 6.50 − 4.00 pivot x`, `4.05 = 0.05 + 4.00`.
The winch/chasing/battle numbers apply the **drive-config formula** that §2b decoded; the formula is
decoded, its application to other configs is arithmetic and labelled `derived`, not decoded.

**One tune per mode is not free.** JC3's entity carries exactly one `CCameraRef` / `CCameraModifier`
(`CAM_REF.md` §1), and no decoded JC3 vehicle mode switch exists. So:

- **Chase 1 / Chase 2 / Boost** are one tune's *behaviour* in BmAK (BmAK switches preset); in JC3 they
  are **three tune files**. Shipping chase 1 only (the default ride) is what `bat_base.ctunec` can do;
  a second preset needs a second camera object on the entity, which is **UNKNOWN** in JC3.
- Battle requires its own tune file **and** a way to select it — recorded as CW-1's open question, not
  assumed here. The two-drop-variant route (one entity per mode) avoids the switch entirely.

---

## 5. Lag — what is comparable and what is not

| BmAK | value | JC3 counterpart | verdict |
|---|---:|---|---|
| `DrivingCamSmoothingStrength1` / `2` | 30 / 12 | `YawSpringStiffness` 0.08, `YawSpringStiffnessMax` 0.4 | **no unit bridge** (T-CAM9). Only the *ordering* transfers: preset 1 is the snappier. |
| `BoostingCamSmoothingStrength1` / `2` | 10000 / 12 | none — JC3 springs are per-tune, not per-state | **blocked** |
| `AirborneCamSmoothingStrength1/2`, `JumpSmoothingStrength` | 12, 0.4 | none | **blocked** |
| `Short/LongCamSpringConst` (config) | 10000 / 10000 | `CameraVelocitySpring` 2/1/2, `LookAtVelocitySpring` 2/1/1.2 | different law, **blocked** |
| `DrivingCameraLeanFactor` 7.5°, `RollLimit` 20° | 7.5 / 20 | `RollWithVehicleAmount` 0.3 → **0.38** | `derived` (T-CAM6), the one lag-family row with a real bridge |
| `DrivingCameraPitchFactor` −20, `maxPitch` 79.6°, `MinPitch` −71.4° | — | `PitchLimit [-70, 10]` | keep (T-CAM7) |
| `DrivingHeadImpulseFactor` 0.5, `DrivingCamDriftOrientationFactor` 0.15 | — | none | **blocked** (T-CAM8) |

So the only lag value the files justify writing is `RollWithVehicleAmount 0.38`. The spring rows are a
felt test, not a translation; the ordering-derived 0.12/0.6 above is offered as a *candidate* with the
bridge marked blocked, and the take must be one-variable.

---

## 6. The boost shake: which camera lacks it, and how to add one

**Which camera has no boost shake member.** `GenericVehicleCamera` — the struct behind **all eight**
shipped vehicle tunes (`car_base`, `bike_base`, `boat_base`, `big_boat_base`, three helicopters,
`mediumtank`; `CAM_REF.md` §2). Its 800 bytes (`car_base.xml`) contain no amplitude, frequency,
impulse or message field, so there is nothing in a vehicle tune to shake. The file whose *name* promises
it, `editor/entities/jc_cameras/vehicle_cameras/shake/vehicle_camera_shake.ctunec` (405 B), carries
`BlurScale 0.05` and per-layer on/off flags — **not** shake amplitude (`CAM_REF.md` §5). BmAK, by
contrast, has `BatmobileBoostCameraShake` amplitude **35**, wheelspin **50×50×25**, a **0.1 s**
`AdvancedOptions` interval and **2000 / 10000** limits (`CAMERA.md` §3; T-CAM11 = blocked for lack of a
numeric bridge).

**Where a shake can live in JC3.** The `.ctunec` root-class list includes
**`CameraShakeModifierParams`** (`Research/JC3Grab/FX.md` §".ctunec"), and its members are in the
decoded vocabulary (`Research/JC3Grab/FX_VOCAB.json`):

```text
ShakeAnimations[]                                  A[ShakeAnimation]
  Control.Duration / EaseInTime / EaseOutTime      float
  Control.Looping / AutoStart                      bool
  Control.StartMessage / StopMessage / ParameterMessage   HashString
  Control.EnableHorizonStabilization / DrawDebug   bool
  RotationAmplitudeScale / RotationMaxAmplitude    float
  RotationFrequencyScale / RotationMaxFrequency    float
  MasterAmplitudeScaleBBKey / MasterFrequencyScaleBBKey   blackboard key
  RotationAmplitudeScaleSpline / RotationFrequencyScaleSpline / SpeedScaleSpline  CameraSpline10
```

**How to add one (recipe, in order):**

1. Copy `car_base.ctunec` → `bat_base.ctunec` and point the donor `.epe` at it (`bmak_camfile.py build`;
   8/8 values asserted, 179 other ADF rows unchanged).
2. Add a **new instance** of `CameraShakeModifierParams` to that file (type dictionary entry + instance
   row). This is beyond `bmak_camfile.py`, which only rewrites existing rows — it needs an ADF writer
   that appends a type and an instance; that is the real work item, and `jc3adf` already reads the
   layout it has to emit (`DECODE_DEPTH.md` `.ctunec` 17/17 FULL).
3. Fill it so the shake is boost-shaped:
   - `Control.Looping = true`, `Control.Duration = 0.1` (BmAK's interval), `AutoStart = false`;
   - `RotationAmplitudeScale = 1.0`, `RotationMaxAmplitude` = **blocked** (no unit bridge: BmAK's 35 is
     an `AddCameraShake` amplitude against 2000/10000 limits, and no JC3 magnitude exists to compare
     with). It needs a three-point take: 0.5° / 1.5° / 3.0°, chosen by feel — labelled **assumed**, not
     a translation (project rule R4);
   - `RotationMaxFrequency` = same status;
   - `SpeedScaleSpline` control points `0→0`, `1→1` (x range 0…1) so the shake grows with speed —
     an **approximation**, because BmAK's shake is *boost-gated*, not speed-gated;
   - the faithful route is `Control.StartMessage` / `StopMessage`, keyed to the boost event. **No boost
     camera message is decoded**: the effect vocabulary names `EngineNitro` as the nitrous *effect*
     usage (`Research/JC3Grab/README.md` §"Effect usage vocabulary"), and 85 of 155 `.epe` usage ints
     have no name at all, so the message hash is **UNKNOWN** and cannot be written from the files.
4. Verify with a take: boost at 100 km/h into a straight — the horizon should jitter by the chosen
   amplitude and settle within `EaseOutTime`; then confirm no shake at idle and none in battle mode.

---

## 7. Status, gates, and what not to repeat

- **Values ready to write:** T-CAM2 `[55, 63]`, T-CAM3 `[5, 108]`, T-CAM5 `[0, 1.30, 7.00]` /
  `[0, 1.55, 0]`, T-CAM6 `0.38`, T-CAM13 `1.6` — exactly the eight edits recorded in `CAM_TUNE.json`,
  all re-read 8/8, `.epe` 2 bytes.
- **Withdrawn, do not reuse:** test-086's set — horizontal 85/95 copied as vertical, 7.0 m boom derived
  from body length (`CAM_REF.md` §4; `CAMERA.md` §6). Its *routing* result stands: the
  `CCameraModifier` tune wins over the `.epe`'s own `FOV = 50`, and the view widens with speed.
- **Blocked:** T-CAM9 (smoothing → spring), T-CAM11 (shake amplitude/frequency), T-CAM8 (head impulse /
  drift orientation), airborne smoothing, per-mode camera switching in JC3, boost message hashes.
- **Probe order:** one variable per take — (a) drive-1 geometry at rest, (b) FOV stops changing at
  108 km/h, (c) roll 0.38 through a corner, (d) collision start point at the taller hull, (e) shake
  amplitude sweep.

## 8. UNKNOWN register

1. The native consumer of `DrivingCamSmoothingStrength` (no units, no bridge).
2. `JumpSmoothingStrength` 0.4 and airborne smoothing in any JC3 unit.
3. Shake amplitude/frequency mapping; BmAK's `AddCameraShake` units.
4. The boost camera message hash (no decoded name).
5. JC3 per-mode camera switching (no decoded vehicle camera state machine).
6. `BatmobileConversationCamConfig` / `GlideInBatmobileCamConfig` / `BattleModeAbseilingCamConfig`
   geometry (fields present in `CAMERA.json`, values not read in this pass).
7. Which BmAK preset (`EBDC_Camera1` vs `2`) the player sees by default — the enum exists, the default
   is not in the files.
