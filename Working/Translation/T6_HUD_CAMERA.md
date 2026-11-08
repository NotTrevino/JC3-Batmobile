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
| T-HUD4 | armour (health > 1) | none | — | — | **out** (T-10): JC3 has no armour bar - the vehicle HUD has no armour field (`Research/JC3Grab/JC3_HUD_WEAPONS.md`) and the damage model's armour is a per-channel number, not a second bar (`DAMAGE_MODEL.md`) | decoded | n/a |
| T-HUD5 | `UC_SetCannonCoolDown(0…4)`, heavy reticle, special weapon states | `InitVehicleWeapons` / `UpdateVehicleWeapons` (2 slots) | categorical | no weapon component on the mod | **blocked**: the HUD supports it (G2-25: 2 slots, `InitVehicleWeapons` / `UpdateVehicleWeapons`, cooldown) but the entity still has no weapon component - T-11/B-05, slots per D-7 (`Research/JC3Grab/JC3_HUD_WEAPONS.md`) | decoded | fire the cannon, reticle cooldown |
| T-HUD6 | `UC_SetBattleAndZoomMode`, `BattleModeOpacity`, battle/zoom overlay | none | — | — | **out** (T-10): no battle or zoom overlay in the in-game HUD - `ui/hud.gfx` carries neither `zoom` nor `BattleMode` - and the mode's pivot is a named omission (`Research/JC3Grab/TANKTURN.md`) | decoded | n/a |
| T-HUD7 | `UC_SetWinchMeter`, winch cone/needle | none | — | — | **out** (T-10): no winch anywhere in the fleet (`Research/JC3Grab/TETHER.md`: 0 winch classes) and no winch widget in `ui/hud.gfx` | decoded | n/a |
| T-HUD8 | `UC_SetEnergySystemParams` (charges 2…4, fill/target) | none | — | — | **out** (T-10): no energy-system widget in `ui/hud.gfx` and no sonar class to drive one (`Research/JC3Grab/ENTITIES.md`) | decoded | n/a |
| T-HUD9 | combo, medals, enemy count, clock | none | — | — | **out** (T-10): no combo, medal or enemy-count widget in `ui/hud.gfx`, and no vehicle-HUD entry point for one (`Research/JC3Grab/JC3_HUD_WEAPONS.md`) | decoded | n/a |
| T-HUD10 | occupants, virus upload, forensic tracking | none | — | — | **out** (T-10): no occupant, virus-upload or forensic widget in `ui/hud.gfx`; the whole vehicle-HUD interface is in `Research/JC3Grab/JC3_HUD_WEAPONS.md` | decoded | n/a |

<!-- T19-HUD-BEGIN -->
### 1a. T-HUD5 completed - one row per HUD element (T-19, generated)

T-HUD5 above is the pre-T-19 record: *"the HUD supports it, the entity still has no weapon
component"*. T-11 has since bound the weapons, so the one blocked row is split here into one
row per element, each cell quoted from a file:
`HUD_INTERFACES.json` (the BmAK setter **and its argument signature**), the G2-25 json (the
JC3 member, the icon ids, the one lock-on POI, and the two zeros that prove the heat bar is
absent on both sides) and `t7_weapons_edits.json` (which weapon the two clips actually show: the cannon on `main_weapon`, the Vulcan on root `id:00568A74`).

10 rows over 5/5 G2-25 elements: **6 map**, **2 partial**, **2 out** (stated absence). Every row carries a proof
that `t19_hud.py --check` re-evaluates (12 proofs); a `map` with no member behind
it fails the check. T-HUD1…3 (HUD-1: speed, nitro, health) stay as they are - **kept**, not
rewritten - and the check asserts they are still in the table above.

| # | element (G2-25) | BmAK source (interface) | JC3 element (decoded) | value / transform | class | now | proposed | verify |
|---|---|---|---|---|---|---|---|---|
| T-HUD11 | weapon slots | `HudModuleBatmobile`: `UC_SetPrimaryWeapon(param1:String)`, `UC_SetSecondaryWeapon(param1:String, param2:Boolean, param3:Boolean)`, `UC_SetSpecialWeapons(param1:int, param2:int, param3:int)` | `InitVehicleWeapons(slot_index 0..1)` -> `MCI_vehicle_weapons0` / `MCI_vehicle_weapons1` (`EVEHICLE_WEAPON_SLOT_MAIN` 0, `..._ALTERNATIVE` 1) in `VehicleConstructor` | slot 0 = the cannon clone of `w602_mediumtank_canon` (`main_weapon`, T-11); slot 1 = the Vulcan clone of `w603_mediumtank_mgun` (root `id:00568A74`, T-11) | decoded | map | 2 slots: the 3 special-weapon states (`UC_SetSpecialWeapons(int, int, int)`) have no member; the missile launcher is bound to no slot (T-WP13's blocked row) | Q-3 #3: two clips show the two bound weapon ids |
| T-HUD12 | weapon slots | `HudModuleBatmobile`: `UC_SetPrimaryWeapon(param1:String)`, `UC_SetSecondaryWeapon(param1:String, param2:Boolean, param3:Boolean)` | `InitVehicleWeapons(weapon_name)` -> `TXT_name` (the label under the slot) | BmAK's weapon name string passes through unchanged | decoded | map | `UpdateVehicleWeapons` cannot change the label: a slot that changes weapon needs `InitVehicleWeapons` again (G2-25 §2) | Q-3 #3: the label reads the bound weapon, not the donor's |
| T-HUD13 | weapon slots | `HudModuleBatmobile`: no setter (the element is not an interface) | `weapon_icons/<weapon_id>.ddsc` - `GetWeaponIconName(weapon_id)`, `_sm.ddsc` for low res, ids -1 and 0 rejected | ids 602, 603, 618, 619: all four are in the shipped icon set, so both slots draw | decoded | map | the icon is a JC3 file named by the weapon id; BmAK has no icon id (0 of `HudModuleBatmobile`'s 37 setters name an icon). Id 614 must not be reused - its icon was never shipped (G2-25 §6) | Q-3 #3: each slot shows its own weapon icon |
| T-HUD14 | reticle | `HudModuleBatmobile`: `UC_SetCannonCoolDown(param1:int)` | `UpdateWeaponReticle(show, weapons_look, reticle_size, reticle_shape)`; shape `E_RETICLE_CANNON = 8`, 5 look states, marker y -111 for shapes 8/11/12 | the heavy vehicle reticle is shape 8 (`E_RETICLE_CANNON`) | decoded | map (shape id UNKNOWN) | no file maps `E_RETICLE_CANNON` to a vehicle cannon - the shape id is the closest named member, not a proven binding (G2-25 §4) | Q-3 #3: the reticle appears with the cannon and hides with it |
| T-HUD15 | reticle | `HudModuleBatmobile`: `UC_SetMachineGunAccuracyFrame(param1:int)` | `UpdateWeaponReticle(reticle_size)` 5..30 px + `weapons_look` 5 states | accuracy frame -> `reticle_size` | UNKNOWN | partial | the BmAK frame is an index with no stated domain or pixel mapping, and `weapons_look` is a target relation, not an accuracy state: the member exists, the scale does not. Nothing is hand-substituted (G2-25 §4) | Q-3 #3: the reticle tightens when the Vulcan settles |
| T-HUD16 | cannon cooldown | `HudModuleBatmobile`: `UC_SetCannonCoolDown(param1:int)` | `weapon_cooldown` 0..1 in `InitVehicleWeapons` / `UpdateVehicleWeapons`; `SetCooldownRotation`: rot = cooldown x 360 over `MCI_mask_0_50` / `MCI_mask_50_100`; -1 hides `MCI_radial_loader_cooldown` | cooldown = BmAK state / 4 (state 0…4 -> 0.00, 0.25, 0.50, 0.75, 1.00) | derived | map | BmAK sends 5 categorical states (Ready / Blank / PreReady*), JC3 takes a fraction: the division by 4 is the only monotone map between the two domains, and its direction is a Q check, not a file fact | Q-3 #3: the loader ring fills 0 -> full between shots and is hidden at rest (`weapon_cooldown = -1`) |
| T-HUD17 | Vulcan heat | `HudModuleBatmobile`: no setter (the element is not an interface) | none: `params_with_heat` empty and `body_mentions` 0 - no vehicle-weapon argument or body mentions heat (the movie's own heat code is the 11-state police wanted level) | named omission | decoded | out (stated absence both sides) | BmAK's heat is `HeatBarStart`/`HeatBarSize` on `Batmobile_Cannon_V2`, a weapon-entity script field with no `UC_*` setter (0 of 252 setters name heat); JC3 shows ammo, a cooldown loader and an overcharge tint, never a heat bar | n/a - nothing to observe |
| T-HUD18 | missile lock | `HudModuleTargets`: `UC_SetBatmobileWeapon(param1:String, param2:Boolean)` | `POI_TYPE_LOCK_ON_TARGET = 21` -> `MCI_lock_on.MCI_reticle`, rotated 360 deg every 1.5 s (`LOCK_ON_TARGET_ROTATION_TIME`), no progress bar | one rotating marker on the locked target | decoded | partial | the marker has no file link from an `AutoAim` tune to the POI (0 `CreatePoi` calls of type 21 in the movie), so who paints it stays UNKNOWN (G2-25 §5) | Q-3 #3: the marker appears on the locked vehicle and rotates |
| T-HUD19 | missile lock | `HudModuleTargets`: `UC_SetBatmobileWeaponHit(param1:Boolean)`, `UC_SetBatmobileWeaponFailure(param1:Boolean, param2:Boolean)` | none for the target-kind family; `MCI_safe_area_bottom_middle.MCI_missile_locked` flashes every 0.5 s - that is the *incoming* warning, a different instrument | named omission (6 kinds: Invalid, bomb, emp, friend, multi, plain) | decoded | out | JC3 ships one lock-on icon and one incoming warning; the missile-box family, the aim box, per-target health and the hit/failure events have no JC3 element (G2-25 §7) | n/a |
| T-HUD20 | weapon slots | `HudModuleBatmobile`: `UC_SetWeaponFeedback(param1:Boolean, param2:Boolean)` | `InitVehicleWeapons(infiniteAmmo = true)` hides the ammo counters and shows `MCI_inventory_infinity` | infiniteAmmo = true | derived | map | BmAK's Batmobile weapon HUD has no ammo setter (0 of the 37 setter names carry ammo/magazine), so there is no count to carry across | Q-3 #3: no ammo counter appears in either slot |

**Proofs.** Each line is re-evaluated by `--check` against `Research/JC3Grab/JC3_HUD_WEAPONS.json`:

| row | proof | what it means |
|---|---|---|
| T-HUD11 | `slots.count` slots.count = 2 (want 2) | holds |
| T-HUD12 | `init.params` init.params has weapon_name: True | holds |
| T-HUD13 | `icons.ids` icons.ids holds [602, 603, 618, 619] | holds |
| T-HUD14 | `reticle.shapes` reticle.shapes[E_RETICLE_CANNON] = 8 | holds |
| T-HUD15 | `reticle.params` reticle.params has reticle_size: True | holds |
| T-HUD16 | `cooldown.rot_degrees` cooldown.rot_degrees = 360 (want 360) | holds |
| T-HUD17 | `heat.params_with_heat` heat.params_with_heat = [] | holds |
| T-HUD17 | `heat.body_mentions` heat.body_mentions = 0 (want 0) | holds |
| T-HUD18 | `lockon.lock_on_type` lockon.lock_on_type = 21 (want 21) | holds |
| T-HUD18 | `lockon.lock_on_rotation_time` lockon.lock_on_rotation_time = 1.5 (want 1.5) | holds |
| T-HUD19 | `bmak.missile_target_kinds` 6 kinds | holds |
| T-HUD20 | `init.params` init.params has infiniteAmmo: True | holds |

**Where the boundary is.** Two elements cannot be finished from the files and are recorded as
such rather than filled: the **heat bar** is absent on both sides (0 JC3 arguments, 0 body
mentions, 0 of 252 BmAK setters), and the **lock-on** is one marker whose painter is native
(0 `CreatePoi` calls of type 21). The Vulcan accuracy frame -> `reticle_size` scale is UNKNOWN
for the same reason: the member exists, the unit does not. Slot capacity (D-7's 11 weapons)
stays T-11's blocked row - this table only says what the HUD can draw: two clips.

<!-- T19-HUD-END -->

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
| T-CAM10 | `BattleModeCamFOV` 60, `BattleModeWinchCamFOV` 60, `AntiPersonel` 40 | none | — | — | **superseded by T-15** (D-2): no battle-camera member, but a second per-entity `.ctune` is the carrier (`bat_base.ctune`, Batch F, test-091) | decoded | T-15's variant table |
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

## 1b. v2 additions - the lock pair, the Vulcan bloom and the reload circle (appended 2026-11-08)

Four rows the ledger lacked, each from a plan that reconciled an older plan:
`tmp/freebuff/reports/lock-hold-salvo-reticle-plan-v2.md` (the pursuit lock circle and the battle
lock diamond are two elements, not one), `vulcan-capture-fire-and-overheat-timing.md` (the bloom
has no lockout), `cannon-60mm-reload-circle-plan.md` (the circle is the cooldown arc) and
`emp-immobiliser-forcepulse-plans-v2.md` (the disable half is a composed route, T-WP15).
Column order is section 1a's, so `status_audit.py` classifies these rows by the same rule.

| # | element (G2-25) | BmAK source (interface) | JC3 element (decoded) | value / transform | class | now | verify |
|---|---|---|---|---|---|---|---|
| T-HUD21 | pursuit lock circle | `HudModuleTargets`: `UC_SetBatmobileWeapon(param1:String, param2:Boolean)`, the same setter the battle mode calls, drawing a second element | `POI_TYPE_LOCK_ON_TARGET` = 21 -> `MCI_lock_on.MCI_reticle`, rotated 360 deg every 1.5 s (`LOCK_ON_TARGET_ROTATION_TIME`) | pursuit lock = the open spinning circle; the lock holds without drawing a diamond | derived | derived | the circle spins on the locked id in pursuit mode and stops when the lock drops (`lock-hold-salvo-reticle-plan-v2.md` row 1) |
| T-HUD22 | battle lock diamond | `HudModuleTargets`: same setter, but no diamond-shaped setter or parameter exists in the 37-setter module | the only lock element decoded is `MCI_lock_on.MCI_reticle` (POI 21); no diamond element is named in `Research/JC3Grab/JC3_HUD_WEAPONS.json` | battle lock = a static diamond on the same POI, not a second setter | UNKNOWN | UNKNOWN | the movie that carries a diamond shape is UNKNOWN; `Research/BatmobileGrab/HUD_SPEC.json` (element list per movie) settles it (`lock-hold-salvo-reticle-plan-v2.md` row 2) |
| T-HUD23 | Vulcan bloom, no lockout | `HudModuleBatmobile`: `UC_SetMachineGunAccuracyFrame(param1:int)`, one int per frame | `UpdateWeaponReticle(reticle_size)` 5..30 px | spread grows with sustained fire and the reticle turns red; there is no lockout and no forced pause | derived | derived | hold the Vulcan 6 s: the reticle grows, reddens, and the gun never stops firing (`vulcan-capture-fire-and-overheat-timing.md`) |
| T-HUD24 | cannon reload circle | `HudModuleBatmobile`: `UC_SetCannonCoolDown(param1:int)` 0..4 | `weapon_cooldown` 0..1 in `InitVehicleWeapons` / `UpdateVehicleWeapons`, `cooldown.rot_degrees` 360 | reload circle = the existing 0..1 cooldown arc swept as a full 360 deg circle on the reticle; its period is T-WP1's fire_rate 1.75 -> 2 s | derived | derived | one cannon shot draws the circle once and it completes exactly when the next shot becomes available (`cannon-60mm-reload-circle-plan.md`) |
