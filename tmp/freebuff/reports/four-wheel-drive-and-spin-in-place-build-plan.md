# Four-wheel drive, spin in place, and the four other moves — carriers, values, build steps

Source reports: `tmp/freebuff/reports/G3-08c.md` (carrier hunt, static), `Research/JC3Grab/DRIVE_CARRIERS.md`
(the same data as a generated record), `Research/BatmobileGrab/MODES.md` (BmAK's declared/serialised
values), `Research/BatmobileGrab/DRIVINGMODE.md` (BmAK command bindings and bodies),
`Research/BatmobileGrab/CONTROLS_MENU_SCREENS.md` (BmAK's own button labels),
`tmp/freebuff/reports/mode-switch-carriers.md` (the second-entity route).

Nothing here re-derives what those files already settle; the numbers are quoted from them, and each
claim carries a label:

* **decoded** — read at the file/member/offset named.
* **derived** — arithmetic or a stated rule over decoded inputs.
* **UNKNOWN** — searched and absent, with the file that would settle it.

**Answer in one line:** three of the six moves have a decoded JC3 carrier today (spin → the
`drift` block, Power Slide → the handbrake chain, Afterburner → the nitro chain), three do not
(four-wheel drive and the camera-relative move have 0 members and 0 actions between them, and
Side Swipe / Dodge Thrusters only reach "amendment"), and **exactly one move needs the
second-entity route**: four-wheel drive, because it needs a whole battle-mode handling set that
no in-place state can hold. The pursuit spin's 21.6 km/h gate is the only other thing the entity
split buys.

**What G3-08c found that the cache had dropped:** `LandGlobal.steering_type`, decoded from the
bytes of 54 `*_land_global.vmodc` modules — `FrontSteered` on 51, absent on 3, **no other value
shipped**. The project's cached rows carry `is_all_wheel_steered` / `is_rear_steered` instead,
which are not members of the shipped module (`DRIVE_CARRIERS.md` §5.1). That matters twice here:
it removes the last steering-side hope for four-wheel drive (there is no rear/all-wheel steer
enum a mod could set), and it retires `TANKTURN.md`'s `is_all_wheel_steered = 1` row as a cache
artefact — G3-08c's own conclusion does not rest on it.

---

## 1. The six moves at a glance

| # | move (BmAK button) | carrier the report found / closest system | exact member or file | BmAK numbers behind it | build step closes the gap? |
|---|---|---|---|---|---|
| M1 | **spin in place** at standstill (pursuit, stick from rest) | **found, tune + UNKNOWN behaviour** — `CustomLandGlobal.drift.*` | `drift.constant_drift_torque`, `drift.min_speed_to_drift_kmph`, `drift.max_drift_angle_deg`, `drift.max_drift_torque`, `rear_wheels.arcade_friction_multiplier` | `TurnOnSpot{Front,Rear}TorqueFactor` +0.8 / −0.8, `TurnOnSpotModeEngineBrakingFactor` 2, `BattleModeTurnOnSpotTorqueFactor` 0.3333, `TurningModeMaxSpeed` 600 cm/s, `BattleModeStopAndTurnAngleStationary` 30° | data tune on the donor's own module; rotation at 0 km/h stays UNKNOWN |
| M2a | **camera-relative move** (battle) | **none** — 0 members, 0 keymap actions | 16 land actions, 1 whole-stick binding `LSTICKGENERIC → MOVE_ALL` (on-foot scope) | `BattleModeSteerAngleFactor` 1, `BattleModeYawOffset` 0 | not closable in data; needs the stick→vehicle vector (code bridge) |
| M2b | **four-wheel drive** (battle) | **none** — one `Transmission`, two `Tire` per car, 0 per-wheel members | `Transmission.final_drive`; `front_wheels`/`rear_wheels.arcade_friction_multiplier` are the only per-axle axis | `BattleModeLatSlipScale` 0.75, `LongSlipScale` 1.25, `TrailingSteerFactorMoving` −0.25, `DriveForceFactor` 500, `DrivingForceZOffset` 20 cm, `VSpeedCurve` | **second entity** carries the battle number set; 4WD itself is an amendment |
| M3 | **Side Swipe** (LS+A, pursuit) | **closest system, amendment** — drift velocity-rotation | `drift.keep_velocity_strength`, `drift.velocity_rotation_amount`, `_start_angle`, `_end_angle` | `PMDodge{Torque,Force,Duration}` 6000 / 10000 / 0.15 s (derived pairing) | no discrete shove member; lateral travel only |
| M4 | **Dodge Thrusters** (LS+A, battle) | **closest system, amendment** — `arcade.turbo_jump.*` | `punch_speed_kph`, `f_multiplier`, `top_speed_kph`, `turbo_jump_cooldown` | `BattleDodgeImpulse` 150000; `Strafe*` 8 declared / 0 serialised | fixed-axis punch, no stick direction |
| M5 | **Power Slide** (LS+RT+X) | **found, tune only** | `Brakes.rear.handbrake` + `handbrake_friction_factor` + `CustomVelocityDamper.handbrake_spin_damping` + `drift.counter_steer_torque_handbrake` | none (no handbrake family among the 107 declared fields) | closed by tune; only the input needs a rebind |
| M6 | **Afterburner** (Y) | **found, tune only**, trigger UNKNOWN | `arcade.nitro_boost.*` + `VehicleMisc.full_nitro_use_time` / `_refill_time` | none (no boost family among the 107 declared fields); `TriggerBatmobileBoost` body calls `TriggerBoost()` | closed by tune; the button is the gap |

Two decoded side-findings this plan leans on:

1. **BmAK already splits one button by mode.** `CONTROLS_MENU_SCREENS.md`: LS+A is Side Swipe in
   pursuit and Dodge Thrusters in battle; B is Tracker/Immobilizer in pursuit and EMP in battle.
   JC3 does the same thing on its own LS+A: `DefaultInput.ini` line **:267** binds **both**
   `EjectFromVehicle` and `BattleStrafe` (decoded, `DRIVINGMODE.md` §1). The mode-split is
   therefore BmAK's own model, not a mod compromise.
2. **`BattleStrafe` has a body and no numbers.** export 104979, 94 script bytes, two calls
   (`IsMoveInputIgnored`, `IsButtonInputIgnored`) and no argument (`DRIVINGMODE.md` §2). That is
   why M4 has a command but no value: the `Strafe*` family (8 fields, 0x11e4-0x1208:
   `StrafeForce`, `StrafeTorque`, `StrafeDuration`, `StrafeCooldown`, `StrafeRight`,
   `StrafeFwdCorrectionForce`, `StrafeTime`, `StrafeTarget`) is declared and **serialised in none
   of the four packages** (`MODES.md`).

Build-side mechanics, used by every step below: the module copies live in the build's AAF tree,
confirmed on disk at
`Builds/test-091/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/`
(`*_custom_land_global.vmodc`, `*_land_global.vmodc`, `*_brakes.vmodc`,
`*_custom_velocity_damper.vmodc`, `*_vehicle_misc.vmodc`, `*_transmission.vmodc`,
`*_land_steering.vmodc`, `*_front_tire.vmodc`, `*_rear_tire.vmodc` — all present).
`.vmodc` stats are editable through `ConvertAdf` with a byte-identical round trip (`MODLOG.md`
§0, "Proven in game"). Each build ships the paired `.ee` + `.toc` plus `install.ps1`
(`Builds/test-091/`). **Revert for every step:** restore the module file from the untouched donor
copy (or `git checkout -- Builds/test-0NN/aaf/...`), rebuild, reinstall.

---

## 2. M1 — spin in place at standstill (pursuit)

**Carrier (found):** `CustomLandGlobal.drift.*`, a 20-member block on 145 builds — the only place
in a land car where the body is rotated by a torque rather than by a front-wheel angle
(`DRIVE_CARRIERS.md` §3.1). Runner-up carriers, both rejected by the report: per-axle grip
(`LandGlobal.front_wheels` / `rear_wheels.arcade_friction_multiplier`) shapes a slide but cannot
create rotation; `LandGlobal.steering_type` ships one value and no other exists in the bytes.

| member | donor (fleet min..max; n=145) | why it is in the plan |
|---|---|---|
| `drift.min_speed_to_drift_kmph` | 10 (0..60) | the block's own speed gate; **0 ships on 4 builds, 1 chassis** (`v0400_car_mugello_vintagesports`) |
| `drift.constant_drift_torque` | 0 (0..20000) | the only yaw-torque member that is not slip-gated by name |
| `drift.max_drift_torque` | 5000 (0..35000) | the torque budget |
| `drift.max_drift_angle_deg` | 45 (20..60) | how far the body may deviate |
| `drift.steering_sensitivity` | 4 (0.5..4) | how directly the stick asks for yaw |
| `rear_wheels.arcade_friction_multiplier` | 1 (1..6) | rear stiffer than front on 108 builds, softer on **0** |

**BmAK values (decoded, all four packages, `MODES.md`):** `TurnOnSpotFrontTorqueFactor` 0.8
(0x1c8), `TurnOnSpotRearTorqueFactor` −0.8 (0x1cc) — counter-rotating axles,
`TurnOnSpotModeEngineBrakingFactor` 2 (0x1d0), `BattleModeTurnOnSpotTorqueFactor` 0.333333
(0x2e0), `TurningModeMaxSpeed` 600 cm/s (0x2c4) = **21.6 km/h**, `BattleModeStopAndTurnAngleStationary`
30° (0x2f8).

**Build step (B1).** On the Batmobile's own module copy
`Builds/test-0NN/aaf/editor/entities/jc_vehicles/01_land/<chassis>/modules/default/<chassis>_custom_land_global.vmodc`:

* `drift.min_speed_to_drift_kmph` 10 → **0** — the value is copied from a shipped build
  (`v0400_car_mugello_vintagesports`), not invented.
* `drift.constant_drift_torque` 0 → **20000** — the fleet maximum, again a shipped value; it is the
  only lever that puts torque into the block without a slip angle by name.
* `drift.max_drift_angle_deg` 45 → **30** — BmAK's `BattleModeStopAndTurnAngleStationary`, the one
  BmAK number with the same meaning (max body deviation in a stationary turn). **derived**, and
  the weakest derivation in this document: BmAK gives an angle for the battle mode, the JC3 member
  is the drift block's cap.
* `rear_wheels.arcade_friction_multiplier` (in `<chassis>_land_global.vmodc`) 1 → **4.4** — the
  fleet's front-axle maximum, used as the rear value so the rear is the *looser* axle by BmAK's
  rear-minus-front torque sign; today no build has rear below front, so the sign convention has to
  be tested, not assumed.

Absolute torque from BmAK is **not derivable**: BmAK ships *factors* (±0.8) against a native torque
base, JC3 ships *magnitudes*. The 20000 above is a shipped JC3 magnitude chosen to make the effect
exist, not BmAK's number rescaled.

**UNKNOWN.** Whether yaw torque is applied at 0 km/h: the drift path is slip-angle driven
(`drift_entry_slip_angle`, `drift_exit_slip_angle`, `lat_tire_*` curves) and the arithmetic is
native. **Settling file:** none in the packages — the land-vehicle torque solver in
`JustCause3.exe`; settled in practice by pilot card P1.

**Pilot card P1 — spin in place.**
*In pursuit, stop the car dead (0 km/h), hold the handbrake and full left stick for 2 s: heading changes ≥ 30° within 1.0 s and ≥ 90° within 2.0 s, the car's ground position moves ≤ 5 m over those 2 s, and speed never exceeds 8 km/h; repeat right and get ≥ 90° within 2.0 s. Pass band: 2 of 2 directions inside those limits, else the carrier is UNKNOWN-not-working and the move falls through to the second-entity route.*

---

## 3. M2 — battle mode: move where the stick points, car faces the camera; four-wheel drive

**Carrier (none, twice).**

* Camera-relative control: the regex returns 6 members, **all six in `Propellers`** (two docking
  strafe-angle groups, 38 builds = boats and planes) and **0 in a driving module**; the patch
  keymap has 16 land-vehicle actions, all discrete, and the only whole-stick binding in either
  map is `LSTICKGENERIC → MOVE_ALL`, whose name scope is on-foot (`DRIVE_CARRIERS.md` §4.1).
* Four-wheel drive: 0 members match per-wheel/differential vocabulary anywhere; a `CCar` has one
  `Transmission` (one `final_drive`) and one `Tire` per axle. 4WD is **not expressible as data** —
  this is structural, not a missing name.

**BmAK values (decoded, `MODES.md`) — the battle number set the build has to place somewhere:**

| member | offset | value | note |
|---|---|---|---|
| `BattleModeLatSlipScale` | 0x2d4 | 0.75 | lateral slip reduced a quarter in battle |
| `BattleModeLongSlipScale` | 0x2d8 | 1.25 | longitudinal slip raised a quarter |
| `BattleModeTrailingSteerFactorMoving` | 0x320 | −0.25 | rear axle steers **against** the front while moving — the four-wheel-steer part |
| `BattleModeDriveForceFactor` | 0x2f4 | 500 | drive gain |
| `BattleModeDrivingForceZOffset` | 0x324 | 20 cm | force applied 20 cm above the hub line |
| `BattleModeSteerAngleFactor` | 0x300 | 1 | no steer-angle change |
| `BattleModeThrottleSpeed` | 0x2ec | 10 | rate-sized, unit undocumented |
| `BattleModeVSpeedCurve` | 0x218 | (0→60), (600→40), (1200→30) | top-speed factor vs speed |
| `BattleModeYawOffset` | 0x1910 | 0 | no yaw bias |
| `BattleModeStopAndTurnAngleStationary` | 0x2f8 | 30° | shared with M1 |

**Build step (B2a — the numbers).** Second entity, per `mode-switch-carriers.md` Option A: duplicate
the Batmobile's `.ee` into `batmobile_pursuit.ee` / `batmobile_battle.ee` and put the battle set on
the battle copy:

* `<chassis>_land_steering.vmodc`: lower `steer_angle_max_speed_deg` by the battle/base ratio —
  BmAK's `BattleModeSteerAngleFactor` is 1, so the only honest change is the **speed curve**
  (`min_speed_kmph` 30, `max_speed_kmph` 220, donor values) retuned to BmAK's
  `TurningModeMaxSpeed` cap of 600 cm/s = 21.6 km/h in the *turn* mode; the battle copy keeps the
  donor values.
* `<chassis>_custom_land_global.vmodc`:
  `arcade.heat_boost.*` (the unused duplicate of `nitro_boost_upgraded`, `push_force` 0,
  `blend 0`) becomes the battle multiplier state — `push_force` 0 → **15000** (copy
  `nitro_boost.push_force`), `torque_multiplier` **2.0** (keep), `grip_multiplier` **4.26** (keep,
  the only shipped "more grip" value), `extra_top_speed` **100.92** (keep), `boost_blend_time`
  0.0 → **0.2** (copy `nitro_boost`'s blend). This is `mode-switch-carriers.md` Option B, and it is
  the only in-place runtime handling change JC3 has.
  `front_wheels`/`rear_wheels.arcade_friction_multiplier`: battle copy takes the rear **above** the
  front (fleet max 6 vs 4.4) so the rear drives the slide rather than resisting it — the closest
  data-side statement of "all four wheels push".
* `drift.lat_tire_*` curves exist as the only slip members in a car; they are curves, not a scale,
  so BmAK's 0.75 / 1.25 cannot be written into them. **UNKNOWN** — settling file: the
  `CustomLandGlobal` curve members in the donor module (dump with
  `python Tools/scripts/jc3_drive_carriers.py dump members`), which name the curves but not their
  samples.

**Build step (B2b — the input).** Not closable in data. Ranked options:

1. **`MOVE_ALL` reuse** — bind `LSTICKGENERIC → MOVE_ALL` for the vehicle class and see whether the
   car consumes it. Zero file changes beyond the keymap; **UNKNOWN** whether a vehicle can (settler:
   the native class→action-set selection in `JustCause3.exe`; pilot card P2).
2. **A graph thrust along the stick** — an `.epe` sequence/gadget that applies a force in the camera
   yaw when the stick leaves centre. Direction is the camera, not the stick in world space, so this
   is the closest *data* shape; the camera-relative part becomes "camera yaw", which is what the
   player sees. Cost: a graph per entity, and the trigger must be found.
3. **Amendment** (operator decision): battle mode drops "move where the stick points" and keeps
   "the car turns to face the camera" — the stance and the turn are then pure second-entity values.
   `G3-08c.md` records this as a compromise needing operator approval.

**4WD itself:** not expressible. The honest build claim is "rear-biased, all-axle grip with
counter-rotating rear steer in battle", which is what the values above produce; calling it four-wheel
drive would be a lore claim the files do not support.

**UNKNOWN.** (a) whether a vehicle can consume `MOVE_ALL`/`LSTICKGENERIC` — settler: the exe's
class-to-action-set selection, pilot card P2; (b) whether extrapolating `MOVE_ALL` on foot changes
the on-foot controls too — settler: the same keymap entry, measured in one session.

**Pilot card P2 — camera-relative move + 4WD feel.**
*In battle mode, push the stick 45° right of the camera axis and hold for 3 s: within 0.5 s the velocity vector is within ±15° of the stick's world direction while the nose is within ±20° of the camera axis, and 0→50 km/h takes ≤ 3.0 s from rest with yaw deviation ≤ 5°. Pass band: all three inside their limits on 3 of 3 attempts; a failed stick-vector test means the input route is closed and the amendment applies.*

---

## 4. M3 — Side Swipe (LS + A, pursuit)

**Carrier (closest system, amendment).** The drift block's velocity-keeping members move the car
sideways relative to its heading — lateral travel through a slide, not a discrete shove
(`DRIVE_CARRIERS.md` §6.3).

| member | donor (fleet min..max; n=145) | build value |
|---|---|---|
| `drift.keep_velocity_strength` | 1 (0..1.5) | **1.5** (fleet max) |
| `drift.velocity_rotation_amount` | 80 (20..100) | **100** (fleet max) |
| `drift.velocity_rotation_start_angle` | 15 (0..30) | **30** (fleet max) |
| `drift.velocity_rotation_end_angle` | 40 (25..65) | **65** (fleet max) |

Fleet maxima are used because every one of them increases lateral travel, which is the whole
requirement, and each is a value some shipped car already runs.

**BmAK values.** There is **no `SideSwipe*` member**: `MODES.md`'s family census covers
`BattleMode*` (42), `TurnOnSpot*` (4), `Strafe*` (8), `Transformation*` (9),
`TurningModeMaxSpeed`, `ArmourMode*`, `AirControl*` (8), `JumpRamp*`, `JumpNoRamp`,
`KillFlip*`, `KillKeepyUp*`, `PMDodge*` (3), `BattleDodgeImpulse*`, `StayUpright*`,
`VehicleShovingTorque*`, `ImpactRoadAssist*` (10), `ImpactShake*` (6) — and no swipe family.
**derived** pairing: the only `*Dodge*` block BmAK ships for the pursuit side is `PMDodge*` —
`PMDodgeTorque` 6000 (0x1fdc), `PMDodgeForce` 10000 (0x1fe0), `PMDodgeDuration` 0.15 s (0x1fe4) —
and LS+A is the pursuit dodge button. That is a button-and-mode match, not a decoded binding, so
it is labelled derived and is the weakest number here. `PMDodge*` is serialised in 3 of 4 packages
(no Joker tag → class default, **UNKNOWN**).

**Build step (B3).** Put the four drift values above on the pursuit entity's
`<chassis>_custom_land_global.vmodc`; change nothing else. The 0.15 s duration has **no carrier**
— no drift member counts time, `turbo_jump_cooldown` (5 s) belongs to another block, and there is
no impulse member in a car module. **UNKNOWN**, settling file: `custom_land_global.vmodc` member
list (no duration member exists) plus the exe's drift consumer for any internal duration.

**Pilot card P3 — Side Swipe.**
*At 60 km/h in pursuit, steer left and tap A: the car's lateral displacement reaches ≥ 2.0 m within 0.4 s while heading changes ≤ 20° and forward speed drops ≤ 15 %; repeat right with the same limits. Pass band: 2 of 2, with the lateral figure measured against a straight-line run of the same 0.4 s.*

---

## 5. M4 — Dodge Thrusters (LS + A, battle)

**Carrier (closest system, amendment).** `arcade.turbo_jump.*`, a fixed-direction punch along the
car's own axes, plus its cooldown (`DRIVE_CARRIERS.md` §6.3):

| member | donor | note |
|---|---|---|
| `arcade.turbo_jump.punch_speed_kph` | 50 (50..50; n=145) | the punch |
| `arcade.turbo_jump.f_multiplier` | 15 (12..15) | forward multiplier |
| `arcade.turbo_jump.r_multiplier` | 12 | reverse/backward multiplier (per `mode-switch-carriers.md` §2.4) |
| `arcade.turbo_jump.top_speed_kph` | 200 (200..200) | ceiling during the punch |
| `arcade.turbo_jump.punch_delay_time` | 0.1 | delay before the punch lands |
| `turbo_jump_cooldown` | 5 (5..5; n=232) | the only dodge-shaped cooldown in the fleet |

**BmAK values.** `BattleDodgeImpulse` 150000 (0x1914, engine impulse; **absent in Joker** → class
default, UNKNOWN) is the only battle-dodge magnitude BmAK ships, and the `Strafe*` family that the
`BattleStrafe` command would read is **declared 8 / serialised 0** — so `StrafeForce`,
`StrafeTorque`, `StrafeDuration` (0x11f8 / 0x11fc / 0x1200) have **no value in any package**.
**UNKNOWN**, settling file: `BmGame.upk` CDO (`chase08_cdo.py`), or the `StrafeForce` tag site if a
package outside the four carries it.

**Build step (B4).** Battle entity's `custom_land_global.vmodc`: keep `punch_speed_kph` 50 and
`f_multiplier` 15 (donor), set `turbo_jump_cooldown` to **1.0 s** if the file accepts it (the
fleet ships only 5), and give the punch the car's own **backward** axis for a stick-back dodge via
`r_multiplier` 12 → **15** (mirror the forward value). This yields a discrete 50 km/h punch with a
1 s lockout, fired along the car's axis. The direction from the stick is the same missing input as
M2b and is closed by the same route or not at all.

**UNKNOWN.** What fires `arcade.turbo_jump` — neither keymap has a NITRO/BOOST/DODGE action
(249 bindings searched; only `WINGSUIT_BOOST` matches); settler: the turbo-jump/turbo-pad consumer
in `JustCause3.exe`. Until that is decoded, M4's trigger is unowned and the 5 s cooldown stays.

**Pilot card P4 — Dodge Thrusters.**
*From rest in battle mode, tap LS+A with the stick forward: the car covers ≥ 4 m in the stick's direction within 0.5 s and ≤ 4 m against it, then accepts no second dodge for ≥ 1.0 s. Pass band: 3 of 3 taps forward, 0 of 3 backward; the lockout measured to ±0.2 s.*

---

## 6. M5 — Power Slide (LS + RT + X)

**Carrier (found, tune only).** A rear-axle-only handbrake plus a handbrake-specific yaw torque —
exactly the mechanism a power slide needs (`DRIVE_CARRIERS.md` §6.1):

| member | file | donor | fleet |
|---|---|---|---|
| `Brakes.rear.handbrake` | `<chassis>_brakes.vmodc` | 1 | 1 on 145/145 |
| `Brakes.front.handbrake` | same | 0 | 0 on 145/145 |
| `Brakes.handbrake_friction_factor` | same | 1 | 1..10 |
| `Brakes.rear.max_brake_torque` | same | 10000 | 500..1e7 |
| `CustomVelocityDamper.handbrake_spin_damping` | `<chassis>_custom_velocity_damper.vmodc` | 0 | 0..4 |
| `drift.counter_steer_torque_handbrake` | `<chassis>_custom_land_global.vmodc` | 30000 | 0..100000 |
| `drift.min_speed_to_drift_kmph` | same | 10 | 0..60 |

**BmAK values:** **none** — the 107 declared fields contain no handbrake/slide family, so this move
is carried by BmAK's *input* only (X + RT), and there is no BmAK number to copy. The closest BmAK
numbers are the battle slip scales (`LatSlipScale` 0.75 / `LongSlipScale` 1.25), which belong to
M2 and are not the slide. Stated rather than filled.

**Build step (B5).** `handbrake_friction_factor` 1 → **3** (mid of the shipped 1..10 range, so the
lock is stronger than the donor without going to the fleet max on a car that is heavier than the
donor), `handbrake_spin_damping` 0 → **2** (mid of 0..4, keeps the spin instead of damping it),
`counter_steer_torque_handbrake` 30000 → **60000** (mid of 0..100000, doubles the yaw authority
during the slide). Each is a within-shipped-range choice, labelled **derived** — the number is a
midpoint of a decoded range, not a BmAK value.
Input side: `HANDBRAKE` is `RPADLEFT` in the patch gamepad map (decoded, `DRIVE_CARRIERS.md` §4.1)
and `ACCELERATE` is already `RTRIGGER`, so half of BmAK's chord already matches. Re-pointing
`HANDBRAKE` to the pad's X button needs the physical button token, and the 16 decoded land actions
use only the tokens `RTRIGGER`, `LTRIGGER`, `RSHOULDER`, `LSHOULDER`, `RSTICKBUTTON`, `LSTICKBUTTON`,
`RPADLEFT/RIGHT/UP/DOWN`, `LSTICKLEFT/RIGHT` — no face-button token appears. **UNKNOWN**, settling
file: the full `keymap_gamepad.bin` decode (`jc3_input.parse_keymap` dump of both base and patch
maps) for a face-button input name.

**Pilot card P5 — Power Slide.**
*Enter at 80 km/h in pursuit, hold RT + X and steer: the heading is ≥ 25° off the velocity vector within 0.8 s, the slide holds ≥ 0.6 s without the rear snapping back, and the car exits above 50 km/h. Pass band: 3 of 3 entries, with the exit speed measured 1.0 s after releasing X.*

---

## 7. M6 — Afterburner (Y)

**Carrier (found, tune only; trigger UNKNOWN).** The nitro chain, in the order it acts
(`DRIVE_CARRIERS.md` §6.2):

| member | module | donor | fleet |
|---|---|---|---|
| `arcade.nitro_boost.extra_top_speed` | `custom_land_global` | 40 | 30..60 (n=145) |
| `arcade.nitro_boost.torque_multiplier` | same | 2 | 1.5..40 |
| `arcade.nitro_boost.grip_multiplier` | same | 2 | 1.2..2 |
| `arcade.nitro_boost.push_force` | same | 15000 | fixed |
| `arcade.nitro_boost.boost_blend_time` | same | 0.2 | fixed |
| `arcade.nitro_boost_upgraded.extra_top_speed` | same | 80 | 60..100 |
| `arcade.nitro_boost_upgraded.push_force` | same | 20000 | fixed |
| `Transmission.nitrous_gears` | `transmission` | 0 | 0..2 |
| `VehicleMisc.full_nitro_use_time` | `vehicle_misc` | 4 | 4 (n=232) |
| `VehicleMisc.full_nitro_use_time_upgraded` | same | 8 | 8 |
| `VehicleMisc.full_nitro_refill_time` | same | 2 | 2 |
| `VehicleMisc.nitro_refill_min_speed_kph` | same | 20 | 15..20 |

**BmAK values:** **none** — no boost/afterburner family among the 107 declared fields. What is
decoded is the plumbing: `DrivingMode.TriggerBatmobileBoost` (export 104965, 58 script bytes)
calls `TriggerBoost()` and is **not bound in the binding chain** (`DRIVINGMODE.md` §1/§2), and
BmAK forces the boost while moving in battle (operator statement in
`CONTROLS_MENU_SCREENS.md`). BmAK's afterburner magnitude is therefore **UNKNOWN**; settling file:
the `RVehicle.TriggerBoost` body in `BmGame.upk` (not decoded) plus BmScript's boost values.

**Build step (B6).** `VehicleMisc.full_nitro_use_time` 4 → **8** (the shipped upgraded value, so a
held Y is not cut at 4 s); `full_nitro_refill_time` 2 → **1** (below the shipped 2, still positive,
because BmAK's afterburner is not a driving-refilled budget); `nitro_refill_min_speed_kph` 20 →
**0** (BmAK refills regardless of speed). Keep `push_force` 15000, `torque_multiplier` 2,
`grip_multiplier` 2, `boost_blend_time` 0.2. The trigger is the same missing action as M4: no
NITRO/BOOST action in either keymap.

**One contradiction to settle, not bend.** `DRIVE_CARRIERS.md` gives the donor
`nitro_boost.grip_multiplier` = **2** and `extra_top_speed` = **40**, while
`mode-switch-carriers.md` §2.4 lists the same donor block as `grip_multiplier` **1.0** and
`extra_top_speed` **43.2** (and `nitro_boost_upgraded` grip 4.26 / extra 100.92). Two records,
two donor readings. The build must use one, so the value has to be re-read from the donor module
before writing: **settling file** `Builds/test-0NN/aaf/editor/entities/jc_vehicles/01_land/<chassis>/modules/default/<chassis>_custom_land_global.vmodc`,
dumped member by member (`python Tools/scripts/jc3_drive_carriers.py dump members`, then
`vmodcdiff.py` against the donor). Until then the table above quotes G3-08c's fleet figures.

**Pilot card P6 — Afterburner.**
*Hold Y from 100 km/h in pursuit: speed reaches ≥ 140 km/h within 1.0 s, holds for at least 8 s, and decays to the un-boosted value within 2 s of release; a second press inside the first second changes nothing. Pass band: +40 km/h ±10 % at 1.0 s, burn ≥ 8 s, decay ≤ 2 s.*

---

## 8. Which moves need the second-entity route

From `mode-switch-carriers.md` §3: no JC3 vehicle switches handling at runtime, the boost state is
the only in-place change and it carries roughly a third of one row, and the entity variant is the
only pattern that carries a second complete value set.

| move | needs a second entity? | why |
|---|---|---|
| M1 spin in place | **partly** | the mechanism (`drift.*`) is one block per entity and the spin exists only in pursuit, so the *mechanism* does not need the split; the **21.6 km/h gate** does — one entity cannot have `min_speed_to_drift_kmph` 0 in pursuit and 60 in battle |
| M2a camera-relative move | **no** (input, not values) | the gap is a stick→vehicle vector; an extra entity carries values, not inputs |
| M2b four-wheel drive | **yes** | needs `LatSlipScale` 0.75 / `LongSlipScale` 1.25 / `TrailingSteerFactorMoving` −0.25 / battle grip and force set, and no in-place state holds them; this is the one row that forces Option A |
| M3 Side Swipe | **no** | pursuit-only, drift block on the pursuit entity |
| M4 Dodge Thrusters | **no** | battle-only, `turbo_jump` on the battle entity; the LS+A sharing with M3 is *mode* sharing (decoded at `DefaultInput.ini:267`), not an entity split |
| M5 Power Slide | **no** | pursuit-only, handbrake chain on the pursuit entity |
| M6 Afterburner | **no** | used in both modes; one `nitro_boost` block serves both, and BmAK itself forces the boost in battle |

So: **1 hard yes (M2b), 1 conditional (M1's gate), 4 no.** If the entity split is rejected, M2b
falls back to `heat_boost` (Option B) which buys multipliers but not the slip scales or the
counter-steering rear axle, and M1 keeps its gate at the donor's 10 km/h.

---

## 9. Build order

1. **B5 (Power Slide) and B1 (spin)** first: pure tunes on `brakes`, `custom_velocity_damper`,
   `custom_land_global`; card P1 decides whether the spin exists at all.
2. **B6 (Afterburner)** next: `vehicle_misc` + `custom_land_global`, after settling the donor
   `grip_multiplier` / `extra_top_speed` contradiction (§7).
3. **B3 + B4** together, because both hang off LS+A and the mode split: drift velocity-rotation
   values (pursuit) and the turbo-jump punch + cooldown (battle).
4. **B2a (second entity)** last, because it changes the build shape: two `.ee` files, two `.toc`
   files, two installs. Carry M2b's numbers only here.
5. **B2b (the input)** only if card P2 fails: pick option 2 (camera-yaw graph force) or option 3
   (operator amendment). Do not spend a build cycle on `MOVE_ALL` before P2 has been run.

Every step's evidence: **decoded** for the member names, file paths and donor values; **derived**
for the within-range midpoints, the fleet maxima, and the two BmAK pairings (`PMDodge*` → M3,
`StopAndTurnAngleStationary` → `max_drift_angle_deg`); **UNKNOWN** for the six items in §10.
Nothing was run: no game launched, no build packed, no install written, no git (test ban).

---

## 10. UNKNOWNs, each with the file that settles it

| # | unknown | why it matters | settling file / probe |
|---|---|---|---|
| U1 | does yaw torque act at 0 km/h? | M1 exists or does not | land-vehicle torque solver in `JustCause3.exe` (native); pilot card P1 |
| U2 | can a vehicle consume `MOVE_ALL` / `LSTICKGENERIC`? | M2a and M4's direction | native class→action-set selection in `JustCause3.exe`; pilot card P2 |
| U3 | what fires `arcade.nitro_boost` and `arcade.turbo_jump`? | M6's button, M4's button and cooldown | the boost / turbo-jump consumer in `JustCause3.exe` |
| U4 | `Strafe*` values (8 declared, 0 serialised) | `BattleStrafe`'s magnitude, so M4's BmAK number | `BmGame.upk` CDO (`chase08_cdo.py`); else the `StrafeForce` tag if any package carries it |
| U5 | the pad's face-button input token (BmAK's X) | M5's rebind off `RPADLEFT` | full `keymap_gamepad.bin` decode (base + patch) via `jc3_input.parse_keymap` |
| U6 | donor `nitro_boost` grip / extra top speed — 2/40 or 1.0/43.2? | M6's build values | `<chassis>_custom_land_global.vmodc` member dump + `vmodcdiff.py` |

## 11. Sources and limits

* `tmp/freebuff/reports/G3-08c.md` — carrier hunt; §"Applying each carrier", §UNKNOWNs, §COMPROMISES.
* `Research/JC3Grab/DRIVE_CARRIERS.md` — generated record; §3.1 drift, §3.2 grip, §3.3 steering,
  §4.1 keymap, §5 `steering_type`, §6.1 handbrake, §6.2 nitro, §6.3 Side Swipe / Dodge.
* `Research/BatmobileGrab/MODES.md` — 107 declared fields, 46 serialised, per-package values.
* `Research/BatmobileGrab/DRIVINGMODE.md` — 16 state bodies, 51 call sites, bindings at
  `DefaultInput.ini:252/259/267/268/269/270/272`.
* `Research/BatmobileGrab/CONTROLS_MENU_SCREENS.md` — BmAK's button labels and the operator notes.
* `tmp/freebuff/reports/mode-switch-carriers.md` — §3 (patterns), §5 Option A/B/C, §7 UNKNOWNs.
* `MODLOG.md` §0 — `.vmodc` editable via `ConvertAdf`, byte-identical round trip.
* `Builds/test-091/` — the module tree and `.ee`/`.toc`/`install.ps1` layout the steps address.

**Limits.** Static only: no game launched, nothing packed, no install written. The M3 pairing and
the M1 angle mapping are derivations from a button/mode match and a same-named quantity — they are
the two places where a pilot card, not a file, decides. Four-wheel drive remains an amendment: the
files give no per-wheel drive and this plan does not pretend otherwise.

**Revert:** delete this file. No other file was created, edited or moved; the build steps are
proposals and were not applied.
