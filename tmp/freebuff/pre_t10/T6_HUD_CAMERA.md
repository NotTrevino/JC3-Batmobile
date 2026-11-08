# T-6 — HUD and camera

T-1/T-2b/T-3 cover the vehicle factors. This table covers the two systems that were still only
indexed when they were written: the Batmobile HUD (now decompiled from `BmGame.upk`) and the camera
(now decoded from `R3rdPersonCamera`). Sources:

- `Research/BatmobileGrab/HUD.md`, `HUD_SPEC.json`, `HUD_INTERFACES.json` — 25 native HUD modules,
  19 carved movies, 252 `UC_*` setters; the Batmobile module alone is 99 scripts / 37 setters.
  `SPEEDOMETER.md` / `SPEEDOMETER.json` — the native speedometer path, its class and fields.
- `Research/BatmobileGrab/CAMERA.md`, `CAMERA.json` — 33 named values, 13 configs.
- `Research/JC3Grab/…` — JC3's `ui/hud.gfx` (260 scripts) and `car_base.ctune`.

No row here was in test-085. The camera rows are now built as **test-091** (§4, Batch F); the HUD
still needs a script hook, so its rows remain proposed, not built.

## 1. HUD rows

| # | BmAK source | JC3 target | transform | now | proposed | conf | verify |
|---|---|---|---|---|---|---|---|
| T-HUD1 | no HUD movie implements speed; the only speedometer is the native debug readout `RPlayerController.bDebugSpeedometer` (off by default) drawn by `RPlayerControllerBase.DrawHUD` (`SPEEDOMETER.md`) | `hud.as` `MCI_speedo`, `SetPrimaryMeterValue` | — | JC3 circular speedometer, 250° sweep, 0.05 s smoothing | **reuse** | decoded | speed reads correctly in a drive |
| T-HUD2 | `UC_SetBoostLevel(level 0…100, upgrade)`; hide at 100, intro/outro | `InitVehicleNitrous(recharge)`, `UpdateVehicleNitrous`, `HideVehicleNitrous` | `recharge = level / 100` | JC3 nitrous meter, 0…1, ready sound at 1 | **map**: boost = nitrous; upgrade badges have no member | decoded | boost fills/drains the nitro meter |
| T-HUD3 | `UC_SetHealth(health, max)`, armour above 1, pulse < 0.2, 2 s timer | vehicle health paint/bar (`hud_code/health/*`) | **identity**: `health` is already 0…1; `max` only selects the armour tier | JC3 vehicle health bar | **map** health; armour is out | decoded | damage paints the bar, heals cleanly |
| T-HUD4 | armour (health > 1) | none | — | — | **out**: JC3 has no armour mode | decoded | n/a |
| T-HUD5 | `UC_SetCannonCoolDown(0…4)`, heavy reticle, special weapon states | `InitVehicleWeapons` / `UpdateVehicleWeapons` (2 slots) | categorical | no weapon component on the mod | **blocked**: the HUD supports it, the entity does not | decoded | fire the cannon, reticle cooldown |
| T-HUD6 | `UC_SetBattleAndZoomMode`, `BattleModeOpacity`, battle/zoom overlay | none | — | — | **out**: no battle mode or zoom in JC3 | decoded | n/a |
| T-HUD7 | `UC_SetWinchMeter`, winch cone/needle | none | — | — | **out**: no vehicle winch | decoded | n/a |
| T-HUD8 | `UC_SetEnergySystemParams` (charges 2…4, fill/target) | none | — | — | **out**: no Batmobile energy system | decoded | n/a |
| T-HUD9 | combo, medals, enemy count, clock | none | — | — | **out**: challenge-only HUD | decoded | n/a |
| T-HUD10 | occupants, virus upload, forensic tracking | none | — | — | **out**: story gadgets/passengers | decoded | n/a |

**The one HUD finding that changes the plan:** JC3 already ships a **nitrous meter** and a **vehicle
weapon slot HUD**, so the Batmobile's boost gauge and cannon reticle do not need a new movie. They
need a caller. The movie's `UC_*` API and JC3's `Init/UpdateVehicle*` API are both named and
public; what is missing is the bridge from the entity to `hud.gfx`, which is game code, not a
`.vmodc` member.

**HUD data contract (corrected):** the HUD is **25 `RHudModule*` classes and 19 movies**, 252
`UC_*` setters, not one movie. The Batmobile module is 99 scripts, 51 frames, 30 fps, 1024×720
stage, 37 setters; constants `TickDeltaTime` 0.033, `MaxHealthChangePerFrame` 0.05, pulse < 0.2,
offscreen 2 s, energy step 0.02, projection FOV 56°. The vehicle health contract is §4.1 of HUD.md;
`HudModuleHealth` is a second contract (Batsuit health, armour type + maxima, adrenaline), not the
same bar. JC3: 260 scripts, 1280×720, speedometer 250°, smoothing 0.05, vehicle types
land/airplane/helicopter/sea.

**The other HUD modules — grabbed, not translatable.** The first pass carved two movies and its
rows could only speak about those two. The roster is now complete; fourteen of the fifteen
movie-bound modules have no JC3 host, and that is recorded rather than hidden:

| native module | what it draws | JC3 host | disposition |
|---|---|---|---|
| `RHudModuleTargets` | lock-on, missile boxes (`VehicleMissileTarget` plain/bomb/EMP/friend/multi/invalid), compass, grapple/winch reticles | none | **out**: no lock-on or target markers in JC3's HUD API |
| `RHudModuleLocalRadar` | local radar, `LockonMeter`, health-of-target meter, heavy-tank radius | none (JC3 minimap is a different system) | **out** |
| `RHudModuleAlertsAndSurveillance` | triple tracker, intercept angle/range, forensic trail, audio alert text | none | **out** |
| `RHudModuleHealthBar` | Batsuit health, ballistic armour, adrenaline, combo, takedowns, XP | `hud_code/health/*` only for health | **out**: no armour/adrenaline/combo members |
| `RHudModuleStoryMode` | threat meter, warning bar/messages, lap counter, intel meter, zoom gizmo, command-beacon charge | none | **out** |
| `RHudModuleBoss` | boss name + health bar (also Firefly via `FireflyIcon`) | none | **out** |
| `RHudModuleScanner` | scan reticle, timeline, case-file/deep-scan views | none | **out** |
| `RHudModuleDetectiveMode` / `…Jamming` | detective vision, evidence/NPC detail, jamming | none | **out** |
| `RHudModuleObjectives`, `…RoomName`, `…CrimeSceneInfo`, `…SuicideCars`, `…DownloadProgress` | objective markers, captions, progress | none | **out** |
| `RadialGadgetSelect` | gadget wheel, per-character icon sets | none | **out** |
| `StoryModeHUD` | 122 `CI_*` prompt classes + `HUD_I*` icons | JC3 prompt system is separate | **out** |

Ten native classes are **unmapped** (HUD.md §2) — including `ChallengeMode`, `ExtraSequence`,
`ForensicBeaconTracking`, `Firefly` and dev-only `PerformanceTest` — their cached function names
exist in no carved movie (HUD.md §8). Nothing is claimed about them; they are listed so the gap
stays visible.

## 2. Camera rows

| # | BmAK source | JC3 target | transform | now | proposed | conf | verify |
|---|---|---|---|---|---|---|---|
| T-CAM1 | `EBatmobileDriveCamera`: `Camera1`, `Camera2`, `Bonnet` | one car camera | — | `car_base.ctune` | **Camera1 is the preset**, using `DrivingCamConfig1`; Camera2 is `DrivingCamConfig2` (5 m sit, same FOV); Bonnet has no car cockpit | decoded | one camera drive |
| T-CAM2 | `DrivingCamFOV` 85 **h**, `BoostingCamFOV` 95 **h**, `MaxExtraFOV` 10 | `FOV [30,55]` over `FOVVelocityRange [5,50]` | UE3 horizontal → JC3 vertical (16:9) | 30…55° v | `FOV [55,63]` v; 68 only if the +10 speed bonus is folded in; **95 boost is a gap** | decoded | wide chase, no fisheye |
| T-CAM3 | `DrivingCamFOVInterpMaxSpeed` 3000 cm/s | `FOVVelocityRange` | 3000 cm/s = 108 km/h | 5…50 km/h | `[5,108]` | decoded | FOV stops changing at 108 |
| T-CAM4 | `DrivingCamMaxExtraTranslation` 50 cm | `FollowCameraRange [-0.5,2]` | 0.5 m | -0.5…2 m | keep | decoded | pull-back at speed |
| T-CAM5 | `DrivingCamConfig1`: sit `[-300,0,-25]` at rest, distance 400/400 cm, pivot `[0,0,155]` | `CameraPosition [0,2,5]`, `LookAtPoint [0,1.25,0]` | native: `Loc = anchor − forward·400 + Rot·Sit`; at rest **700 cm back, 25 cm down** | 5 m / 2 m | **`CameraPosition [0,1.30,7.00]`**, `LookAtPoint [0,1.55,0]` | decoded | distance at rest |
| T-CAM6 | `DrivingCameraLeanFactor` 7.5°, `RollLimit` 20° | `RollWithVehicleAmount 0.3` | 7.5 / 20 | 0.3 | **0.38** | derived | car leans, camera follows |
| T-CAM7 | `DrivingCameraPitchFactor` -20, config `maxPitch` 14500 / `MinPitch` -13000 | `PitchLimit [-70,10]` | rotator units → degrees | -70…10 | keep | derived | look-up/down clamps |
| T-CAM8 | `DrivingHeadImpulseFactor` 0.5, `DrivingCamDriftOrientationFactor` 0.15 | none | — | — | **blocked**: no head-impulse or drift-orientation member | decoded | impact/ drift feel |
| T-CAM9 | `DrivingCamSmoothingStrength` 30 / 12 / 10000; `Airborne` 12 | `Yaw/Pitch/RollSpringStiffness` 0.08 / 0.12 / 1.0 | no unit bridge | keep | keep | blocked | spring feel |
| T-CAM10 | `BattleModeCamFOV` 60, `BattleModeWinchCamFOV` 60, `AntiPersonel` 40 | none | — | — | **out**: no battle mode | decoded | n/a |
| T-CAM11 | `BatmobileBoostCameraShake` 35 / `WheelSpin` 50×50×25, 0.1 s | `AddCameraShake` (game code) | no numeric bridge | — | **blocked** | decoded | boost shake |
| T-CAM12 | `DrivingCamConfig1/2`: `MinFreeCameraDistance = 400`, `MaxFreeCameraDistance = 400` cm; class default 164/200 | `CameraPosition` | the **spring boom** between `0xEF0/0xEF4`; min == max ⇒ fixed 400 cm | 5 m | **400 cm boom, additive to the sit offset** (T-CAM5) | decoded | distance at rest |
| T-CAM13 | body height 2.271 m vs donor 1.41 m | `CollisionStartPoint [0,1,0]` | ×1.61 | 1.0 m | **1.6 m** | derived | no clipping through the taller body |

**What the camera can be, today:** a per-entity `bat_base.ctunec` with T-CAM2–T-CAM6 and T-CAM13.
The reference is **not** missing: the donor `.epe` carries `CCameraRef CarCameraRef` →
`CCameraObject SharedCarCamera` → a `CCameraModifier` whose field is the plain path
`editor/entities/jc_cameras/vehicle_cameras/car_base.ctune`. `car_base.ctune` → `bat_base.ctune` is
the same 14 bytes, so the epe edit changes **2 bytes** and moves nothing. `bmak_camfile.py` emits the
tune and the patched epe outside the repo; `Working/Camera/CAM_REF.md` has the reference and the
tank comparison.
The candidate was **packed, installed and driven** as test-086 (`bmak_cambuild.py`, 12/12 checks). The
drive proves the modifier's tune is live: the car's screen width falls from 36% at 0 km/h to 30% at
103 km/h, which a fixed camera-object FOV could not do. But the values themselves were wrong: the
FOV copied UE3's horizontal 85/95 straight into JC3's vertical angle, and the 7 m boom was body
scaling, not the authored `DrivingCamConfig1`. **The candidate is withdrawn.**

**The distance composition is now decoded** (`CAMERA.md` §2b, checked by
`bmak_camdecode.py --check` 18/18): `SetFreeCameraConfig` (`0x140113480`) maps the struct into the
`State*` fields, `UpdateDrivingCamSettings` (`0x14010AD00`) blends them into `Current*`, and
`UpdateCameraPosition` (`0x140111660`) computes
`Loc = anchor − forward·distance + Rot·SitOffset`, with `distance` the spring value between
`CurrentMin/MaxFreeCameraDistance` (400/400 ⇒ fixed 4.00 m) and `SitOffset` a pitch lerp between the
min vector and the up (45°) or down (90°) vector, raised to power 1.5. At rest that is 3.00 m of sit
plus 4.00 m of boom. The struct's “SitOffsetMax” vector is the native look-**down** offset — there is
no separate down vector. **Still blocked:** the smoothing-strength → JC3-spring bridge (T-CAM9) and
the shake/head-impulse rows; no number is hand-substituted for those.

## 3. Evidence and checks

| check | result |
|---|---|
| `bmak_hud.py check` | 2/2 legacy movies, size + SHA-256 |
| `bmak_hud_inventory.py check` | 25 native modules bound as recorded, 19 movies byte-identical, 61 SwfMovie census, gaps printed |
| `bmak_hud_inventory.py interface` | 252 `UC_*` setters; Boss bound 2/2 by cached-name evidence; 10 classes without a movie |
| `bmak_speedometer.py --check` | 19 movies scanned, zero speed setters; `SpeedMin`/`SpeedMax` are FrameLabels; debug flag off in both configs; one script reference (`DoGadgetsMenu`); `DrawHUD` native 39 B; seven Batmobile speed fields at their offsets |
| `hud_spec.py --check --bmak … --jc3 …` | 99 BmAK scripts, 260 JC3 scripts, constants |
| `bmak_camera.py --check` | 33/33 values |
| `bmak_camdecode.py --check` | 18/18 authored values + boom arithmetic |
| `bmak_camfile.py check` | 8/8 values, 0 collateral ADF rows, 1 epe ref, size unchanged |
| `ffdec` export | 99/99 + 260/260 scripts, no error |
| in-game HUD | **not run** |
| in-game camera | **test-091 installed** (Batch F, 8 values; 13/13 pack + 14/14 verify) — **A15 drive pending**. The old test-086 drive proved the modifier's tune is live (FOV widened with speed); its values were withdrawn and not reused |

## 4. What test-091 carries (Batch F, 2026-10-23)

The corrected camera batch: `bat_base.ctunec` with the eight T6 values (T-CAM2 **55 … 63**
vertical over T-CAM3 **[5, 108]** km/h, T-CAM5 **`CameraPosition [0, 1.30, 7.00]`** /
**`LookAtPoint [0, 1.55, 0]`**, T-CAM6 **0.38**, T-CAM13 **1.6**) plus the 2-byte `.epe` ref
rename, packed by `bmak_cambuild.py` over **test-090** (so the B3/B4 values ride underneath):
13/13 pack checks, `verify` 14/14, installed. `bmak_camfile.py check` re-derives it (8/8 edits,
0 collateral ADF rows) and its `guard()` fails closed unless the 400/400 chase config and
`bmak_camdecode --check` (18/18) both hold. The report is `Working/Camera/CAM_TUNE.json`.

The old probe (test-086) stays withdrawn: its FOV copied UE3's horizontal 85 and its 7 m boom was
body scaling. None of its numbers were reused — the new 7.00 m and 1.30 m come from the decoded
composition instead (`Loc = anchor − forward·400 + Rot·Sit`, sit −300,0,−25 cm, pivot 155 cm).
T-CAM4 and T-CAM7 keep their values (the rows say keep); T-CAM12 is the composition, not a field.
Still blocked regardless: **T-CAM9** (spring bridge) and **T-CAM11** (shake). The gate that opens
with this build is **A15** (camera drive): distance at rest, FOV stops changing at 108 km/h, roll
follows the lean, no clipping through the taller body.

A packaging bug was found and fixed on the way: `bmak_cambuild.py` resolved the donor `.epe`
against the *base* tree, so with a base other than test-085 it wrote the patched file into
`Builds/test-085/aaf` instead of the new build. The stage path is now derived from the aaf
segment of the donor path plus an escape guard; test-085's tree was restored from test-083 and
matches its independent `verify/` copy (sha256 `7385eced…`).
