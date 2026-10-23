# Batmobile camera — the rules, and the JC3 translation

The G1 class dump has **no camera class**, and the two native helpers on
`ARVehicleBatmobileBase` are wrappers, not the rules:

| function | what the disassembly actually does |
|---|---|
| `GetCameraTrackingOffset` | 18 instructions; calls a helper at `0x14004CD00` and copies three floats into the out-vector. It returns the tracking point, not a distance or a spring. |
| `ShouldCameraZFollowVehicleUp` | 15 instructions; calls a virtual at vtable `+0x1030` and returns its bool. It is a policy query, not a value. |

The rules live in **`R3rdPersonCamera`** in `BmGame.upk`: 741 `UProperty` children, 447 serialized
tags in `Default__R3rdPersonCamera`. `bmak_camera.py` reads them and writes
`Research/BatmobileGrab/CAMERA.json` (33 named values + 13 `CameraConfig` structs; the two default
distances 164/200 are included so a zeroed config can never be mistaken for the active one). `--check`
re-reads the game and compares every value.

## 1. The three Batmobile camera states

`EBatmobileDriveCamera` (the class's own enum, in serialized order):

| index | name | meaning |
|---:|---|---|
| 0 | `EBDC_Camera1` | first chase camera |
| 1 | `EBDC_Camera2` | second chase camera |
| 2 | `EBDC_BonnetCamera` | bonnet/cockpit view |
| 3 | `EBDC_MAX` | sentinel |

Camera 1 and camera 2 are **two chase presets**, not two vehicles. That is why the class carries
`DrivingCam*1` and `DrivingCam*2` pairs; the shared `DrivingCam*` values are the common base.

## 2. The values

Units: FOV is degrees; `*InterpMaxSpeed` is UE3 cm/s (3000 = 30 m/s = 108 km/h); `*MaxExtraTranslation`
is centimetres; the `DrivingCamera*Factor` fields are scalars.

| member | value | what it controls |
|---|---:|---|
| `DrivingCamFOV1` | 85 **h** | chase camera 1, normal drive (UE3 horizontal) |
| `BoostingCamFOV1` | 95 **h** | chase camera 1, boost |
| `DrivingCamFOV2` | 85 **h** | chase camera 2, normal drive |
| `BoostingCamFOV2` | 95 **h** | chase camera 2, boost |
| `DrivingCamMaxExtraFOV1/2` | 10 **h** | extra FOV at speed |
| `DrivingCamMaxExtraTranslation1/2` | 50 | extra camera pull at speed (0.5 m) |
| `DrivingCamFOVInterpMaxSpeed1/2` | 3000 | speed at which the FOV interpolation is complete |
| `DrivingCamSmoothingStrength1` | 30 | chase 1 smoothing |
| `DrivingCamSmoothingStrength2` | 12 | chase 2 smoothing (smoother) |
| `BoostingCamSmoothingStrength1` | 10000 | boost smoothing, chase 1 (as serialized) |
| `BoostingCamSmoothingStrength2` | 12 | boost smoothing, chase 2 |
| `AirborneCamSmoothingStrength1/2` | 12 | airborne smoothing |
| `DrivingCameraLeanFactor1/2` | 7.5 | roll/lean with the car |
| `DrivingCameraPitchFactor1/2` | -20 | pitch response |
| `DrivingHeadImpulseFactor1/2` | 0.5 | head impulse on bumps |
| `DrivingCamDriftOrientationFactor1/2` | 0.15 | drift orientation blend |
| `BattleModeCamFOV` | 60 | battle mode |
| `BattleModeWinchCamFOV` | 60 | battle mode while winching |
| `AntiPersonelBattleModeCamFOV` | 40 | anti-personnel battle mode |
| `ChasingCamFOV` | 80 | chasing camera |
| `BatmobileConversationCamFOV` | 45 | conversation camera |
| `RidingCarCamFOV` | 60 | riding-car camera |
| `JumpSmoothingStrength` | 0.4 | jump camera smoothing |
| `HelicopterCameraFOVAngle` | 70 | shared helicopter camera |

### CameraConfig structs

`DrivingCamConfig`, `BoostingCamConfig`, `BattleModeCamConfig`, `BattleModeWinchCamConfig`,
`BattleModeAbseilingCamConfig`, `ChasingCamConfig`, `GlideInBatmobileCamConfig`,
`DiveToBatmobilePickupCamConfig`, `BatmobileConversationCamConfig`, and the `1`/`2` chase copies are
all a 168-byte `FreeCameraConfig`. Its fields are named by the struct's own declaration:

```text
0x00 StateFreeCameraSitOffsetMin     0x54 MinFreeCameraDistance
0x0c StateFreeCameraSitOffsetMax     0x58 MaxFreeCameraDistance
0x18 UseStateFreeCameraSitOffsetUp   0x5c ShortCamSpringConst
0x1c StateFreeCameraSitOffsetUp      0x60 LongCamSpringConst
0x28 StateFreeCameraPullOffset       0x64 DefaultCameraPitch
0x34 CameraPivotOffset               0x68 CameraSitOffsetPower
0x40 ZoomedOffset                    0x6c CameraSitOffsetMin
0x4c maxPitch                        0x70 CameraSitOffsetMax
0x50 MinPitch                        0x74 bUseSeparate43Settings
0x78 StateFreeCamera43SitOffsetMax    0x9c bDontModifySitOffsetWhenLookingUp
0x84 StateFreeCamera43SitOffsetMin    0xa0 MinCameraSmoothingAngle
0x90 StateFreeCamera43SitOffsetLookUp 0xa4 MaxCameraSmoothingAngle
```

The values are in `CAMERA.json` (`configs`), positionally because the nested tags drop names. **The
earlier reading that every chase config carries `MinFreeCameraDistance = 0` was wrong.** It came
from `DrivingCamConfig`, which is a zeroed template; the configs the camera actually uses are the
`1`/`2` copies, and both carry an authored **400 cm**:

| config | sit offset min → max (cm) | Min/MaxFreeCameraDistance | pivot | FOV source |
|---|---|---:|---|---|
| `DrivingCamConfig1` | `[-300, 0, -25]` → `[-400, 0, -25]` | **400 / 400** | `[0, 0, 155]` | 85 / 95 h |
| `DrivingCamConfig2` | `[-500, 0, 0]` → `[-500, 0, 0]` | **400 / 400** | `[0, 0, 155]` | 85 / 95 h |
| `BoostingCamConfig1/2` | `[-200, 0, -75]` etc. | **400 / 400** | `[0, 0, 155]` | 95 h |
| `BattleModeCamConfig` | `[-350, 0, 200]` → `[-500, 0, 200]` | 1000 / 1000 | `[0, 0, 5]` | 60 h |

So the camera **distance value is authored**; it is not supplied by native defaults. Two cautions,
because the first version of this page got both wrong. The **class default object** carries
`MinFreeCameraDistance = 164` / `MaxFreeCameraDistance = 200` (a different range), so the field is a
configurable range that the active config overrides, not a constant. And a field named “distance”
being 400 does not by itself say how it lands in the world — that composition is now decoded from
the executable in §2b: **the 400 cm is the spring boom, the sit offset is rotated and added on top.**
The previous candidate's `7.0 m` was a body-length ratio, not this data — although the native answer
turns out to give the same 7.0 m at rest, for a different reason (400 boom + 300 sit), so the
withdrawal stands as a *method* correction, not a value one.

**FOV units.** The `85`/`95` values are UE3 horizontal FOV. JC3's `FOV` is a vertical angle (the
test-086 recording calibrates it: the car's 2.27 m body at ~3.5 m reads 36% of a 55° view, which is
~86° horizontal). Copying 85° straight into JC3 produced a ~114° horizontal view at boost. The
conversion for 16:9 is `v = 2·atan(tan(h/2) / (16/9))`: **85 h → 54.5 v**, **95 h → 63.1 v**, and
95+10 h → 68.4 v. The correct JC3 range is therefore **55…63** for normal→boost (68 only if the
speed bonus is folded in).

## 2b. The composition, decoded from the executable

The three natives are in `BatmanAK.exe` and were read with capstone (listings kept in
`Working/Camera/`; the arithmetic is reproduced and checked by `Tools/scripts/bmak_camdecode.py`):

| native | address | what it does |
|---|---|---|
| `SetFreeCameraConfig` | `0x140113480` | config struct → `State*` fields (and a 168-byte copy into `CurrentCameraConfig` at `0x4730`) |
| `UpdateDrivingCamSettings` | `0x14010AD00` | `State*` → `Current*` blend (`0xF40..`→`0xF04..`, `0xF70..`→`0xF34..`, `0xD74/0xD78`→`0xEF0/0xEF4`), per-frame |
| `UpdateCameraPosition` | `0x140111660` | `Current*` → camera location |

The offsets in that table are the ones the running game links (BmSDK class dump), not the drifted
cooked-tag offsets: `MinFreeCameraDistance 0xD74`, `MaxFreeCameraDistance 0xD78`,
`CurrentMin/MaxFreeCameraDistance 0xEF0/0xEF4`, `FreeCameraSitOffsetMin/Up/Down/Pull
0xF04/0xF10/0xF1C/0xF28`, `StateFreeCameraSitOffsetMin/Up/Down/Pull 0xF40/0xF4C/0xF58/0xF64`,
`StateSitOffsetPower/Min/Max 0xF70/0xF74/0xF78`, `CameraPivotOffset 0x6F0`.

`SetFreeCameraConfig` is the piece that names the struct fields, and it corrects one of them:

```text
cfg+0x00 -> StateFreeCameraSitOffsetMin   [-300, 0, -25]
cfg+0x0C -> StateFreeCameraSitOffsetDown   [-400, 0, -25]   <- the field the header calls "SitOffsetMax"
cfg+0x1C -> StateFreeCameraSitOffsetUp     [-500, 0, 500]    (only if cfg+0x18 & 1; else Down again)
cfg+0x28 -> StateFreeCameraPullOffset      [0, 0, 0]
cfg+0x34 -> CameraPivotOffset              [0, 0, 155]
cfg+0x68 -> StateSitOffsetPower            1.5
cfg+0x6C -> StateSitOffsetMin              16384   (= 90 deg of pitch)
cfg+0x70 -> StateSitOffsetMax              8192    (= 45 deg of pitch)
cfg+0x54/0x58 -> Min/MaxFreeCameraDistance 400 / 400
cfg+0x5C/0x60 -> Short/LongCamSpringConst  10000 / 10000
```

So there is no separate “down” vector in the 168-byte struct: the vector at `0x0C` — documented as
`StateFreeCameraSitOffsetMax` — *is* the look-down offset. And `CameraSitOffsetMin/Max` are not
distances at all: they are **pitch angles in UE rotator units** at which the sit offset reaches the
down/up vector.

`UpdateCameraPosition` then composes, with `pitch` in rotator units (65536 = 360°):

```text
t   = clamp(|pitch| / (pitch > 0 ? CurrentSitOffsetMax : CurrentSitOffsetMin), 0, 1)
t   = t ** CurrentSitOffsetPower                      (skipped when t == 0 or power == 1)
Sit = lerp(FreeCameraSitOffsetMin,
           pitch > 0 ? FreeCameraSitOffsetUp : FreeCameraSitOffsetDown, t)
Loc = anchor - RotToVector(Rotator) * distance + RotateVector(Rotator, Sit)
```

The `distance` is loaded at `0x140111BE2` from `0xEF0`/`0xEF4` (the current min/max, i.e. 400/400),
and `0x140111C75` does `candidate = base + unit_direction * distance`; the collision branch smooths
it with `CurrentShort/LongCamSpringConst` (`0xD90/0xD94`). The sit offset is added afterwards at
`0x1401124B3..0x1401127A2`, which lerps it by pitch exactly as above and adds the rotated vector to
the already-computed camera position. **The answer to the old open question is “additive”.**

At rest (pitch 0) `t = 0`, so the sit offset is the authored min vector:

| state | t | sit offset (cm) | boom (cm) | camera vs pivot (cm) |
|---|---:|---|---:|---|
| level (rest) | 0.00 | −300, 0, −25 | 400 | **−700, 0, −25** |
| default pitch −5.5° | 0.02 | −301.5, 0, −25 | 400 | −701.5, 0, −25 |
| looking up 45° | 1.00 | −500, 0, +500 | 400 | −900, 0, +500 |
| looking down 90° | 1.00 | −400, 0, −25 | 400 | −800, 0, −25 |

With `CameraPivotOffset` 155 cm the camera therefore sits **7.00 m behind and 1.30 m above the car's
origin** at rest, 9.00 m / 2.05 m when looking fully up, and 8.00 m / 1.30 m looking fully down.
`DrivingCamConfig2` is the flat variant: sit `[-500,0,0]` at rest and no look-down pull, i.e. a fixed
9.00 m boom.

## 3. What the camera does, in words

- The chase camera is **wide**: 85° base, 95° on boost, +10° more by speed, interpolated to 108 km/h.
- Camera 2 is the smooth preset (12 vs 30); camera 1 is the snappier one. Both share FOV and lean.
- The camera leans with the car (`LeanFactor` 7.5), pitches with acceleration (`PitchFactor` -20),
  and adds a small head impulse (`0.5`) on impacts.
- Battle mode narrows the view to 60° (40° anti-personnel, 60° while winching); the winch camera is
  the same 60° but with its own framing config.
- Boost adds a 35-unit shake (`BatmobileBoostCameraShake`); wheelspin adds 50×50×25; the
  `AdvancedOptions` child carries a 0.1 s interval and 2,000/10,000 limits.

## 4. JC3's camera, for comparison

JC3's car camera is a `GenericVehicleCamera`, an 800-byte ADF struct. The base tune is
`car_base.ctune`; eight per-class tunes ship with the game (`car_base`, `bike_base`, `boat_base`,
`big_boat_base`, three helicopters, `mediumtank`). The Serpente's entity references `DrivingCamera`,
which uses this base. Values from `Working/Audio/car_base.xml`:

| member | value | note |
|---|---|---|
| `CameraPosition` | `[0, 2, 5]` m | 5 m behind, 2 m up |
| `CrashingCameraPosition` | `[0, 4.5, 5]` | |
| `RotationPoint` | `[0, 1.5, 0]` | |
| `LookAtPoint` | `[0, 1.25, 0]` | |
| `FollowCameraRange` | `[-0.5, 2]` m | camera follow band |
| `FOV` | `[30, 55]`° | at `FOVVelocityRange = [5, 50]` km/h |
| `FOVZoomAdjustment` | `-5`° | |
| `YawSpringStiffness` | 0.08 | |
| `PitchSpringStiffness` | 0.12 | |
| `RollSpringStiffness` | 1.0 | |
| `RollWithVehicleAmount` | 0.3 | |
| `PitchLimit` | `[-70, 10]`° | |
| `RollLimit` | `[-20, 20]`° | |
| `MinTimeForHalfTurn` | 2 s | |
| `LagCameraRelativity` / `LagVelocityScale` | 1 / 30 | |
| `ReCenterDelay` / `ReCenterSpeed` | 0 / 0.5 | |
| `CollisionFudgeFactor` | 0.1 | |
| `CollisionPitchDistance` | 0.3 | |

### The per-entity reference exists

The vehicle `.epe` carries both ends of the reference: `CCameraRef` `CarCameraRef` → `CCameraObject`
`SharedCarCamera` → `CCameraModifier` path
`editor/entities/jc_cameras/vehicle_cameras/car_base.ctune`. The path is a plain NUL-terminated
ASCII string in the binary `.epe`. `car_base.ctune` and `bat_base.ctune` are the same 14 bytes, so a
same-length rename points one entity at its own tune and leaves every other car alone.
`Working/Camera/CAM_REF.md` has the mechanism, the tank comparison and the candidate;
`bmak_camfile.py` emits and checks it.

## 5. Translation

`T6_HUD_CAMERA.md` carries the full row table. The short version:

| JC3 member | now | BmAK source | proposal | confidence | verify |
|---|---:|---|---|---|---|
| `CameraPosition` | `[0, 2, 5]` | `DrivingCamConfig1`: sit `-3.00 m` at rest, distance **400 cm**, pivot `1.55 m` | **`[0, 1.30, 7.00]`** = pivot 1.55 + sit z −0.25, boom 4.00 + sit x 3.00 (§2b) | decoded | distance at rest |
| `LookAtPoint` | `[0, 1.25, 0]` | `CameraPivotOffset` z 155 cm | `[0, 1.55, 0]` | decoded | the horizon sits mid-screen |
| `FollowCameraRange` | `[-0.5, 2]` | `DrivingCamMaxExtraTranslation` 50 cm | keep | decoded | pull-back at 100 km/h |
| `FOV` | `[30, 55]` | 85 h normal / 95 h boost, +10 by speed | `[55, 63]` (68 with the +10) | decoded | wide chase, no fisheye |
| `FOVVelocityRange` | `[5, 50]` | interp complete at 3000 cm/s = 108 km/h | `[5, 108]` | decoded | FOV stops changing at 108 |
| `RollWithVehicleAmount` | 0.3 | `DrivingCameraLeanFactor` 7.5° / `RollLimit` 20° | 0.38 | derived | car leans, camera follows |
| `Yaw/Pitch/RollSpringStiffness` | 0.08 / 0.12 / 1.0 | smoothing 30/12 (no unit bridge) | keep | blocked | feel test |
| `FOVZoomAdjustment` | -5 | none (no zoom in drive) | keep | n/a | — |
| `PitchLimit` / `RollLimit` | `[-70,10]` / `[-20,20]` | config `maxPitch` 14500, `MinPitch` -13000 | keep | decoded | look up/down clamps |
| `MinTimeForHalfTurn` | 2 s | none | keep | n/a | — |
| `CollisionStartPoint` | `[0,1,0]` | body 2.271 m vs donor 1.41 m; tank starts its ray at 3.4 m | `[0,1.6,0]` | derived | no clipping through the taller body |

`BoostingCamFOV` 95 cannot be expressed by a single JC3 `FOV` range; the table uses the normal 85 and
records the boost +10 as a gap. JC3's `FOV` is a min/max pair over speed, not a per-state value.

**What is still unresolved:** the mapping from BmAK's smoothing strengths (30/12/10000) to JC3's
0.08/0.12/1.0 springs, and the camera shake/head-impulse bridges. Those need a unit bridge the files
do not carry, and are marked blocked rather than guessed. The boom composition is **closed** (§2b);
the spring constants themselves are authored (10000/10000 for `DrivingCamConfig1/2`) but their units
are still not comparable to JC3's stiffness scalars. The second tune was found
(`mediumtank.ctunec`, rigid 1.0 yaw) but it does not supply that bridge either, so T-CAM9 stays
blocked.

## 6. Verification and limits

- `bmak_camera.py --check`: 33/33 values re-read from `BmGame.upk`.
- The class layout drifts by a constant in regions because some native struct sizes are not
  `ScriptStruct`-backed. The tool **anchors on the named struct tags**, interpolates the local delta,
  and only binds a scalar when the corrected offset has the matching property type; unbound values
  are omitted. `CAMERA.json` records exactly what was bound.
- `bmak_camfile.py check`: 8/8 values re-read from the emitted `bat_base.ctunec`, all other 179 ADF
  rows unchanged, one `car_base.ctune` → `bat_base.ctune` reference (2 bytes), `.epe` size unchanged.
- **test-086 drove the old candidate, and the result invalidates its values.** The tune loaded and
the FOV widened with speed (routing works), but the player read the view as too wide and the
  distance had been body-scaled, not config-derived. The candidate is **withdrawn**; no new camera
  build is generated while T-CAM5 is blocked. The source values (400 cm, pivot 155 cm, FOV 85/95 h)
  are in `CAMERA.json`, not in a hand-written table.

## 7. Reproduce

```bash
python Tools/scripts/bmak_camera.py --write
python Tools/scripts/bmak_camera.py --check
python Tools/scripts/bmak_camera.py --report
python Tools/scripts/bmak_camdecode.py            # the boom composition, config by config
python Tools/scripts/bmak_camdecode.py --check    # 17/17 authored values + arithmetic
python Tools/scripts/bmak_camfile.py build    # bat_base.ctunec + patched donor .epe
python Tools/scripts/bmak_camfile.py check    # 8/8 values, 0 collateral rows, 1 ref
```

Native evidence: `Working/Camera/dis_UpdateCameraPosition_full.txt` (0x140111660-0x1401127A1),
`dis_14010ad00_full.txt` (settings/blend), `dis_140113480.txt` (`SetFreeCameraConfig`), plus the
per-block listings in the same folder.
