# Drive-mode torque/steer arithmetic — the closest-JC3 substitute

**Replaces:** the one UNKNOWN this task names — `RVehicleSimBatmobile.SetDriveMode`'s body
(`Research/BatmobileGrab/DRIVE_MODES.md` §7 item 1; `tmp/freebuff/reports/G3-02l.md` UNKNOWN 1:
"export 129767 is a native declaration … the per-mode torque/steer arithmetic therefore lives in
the executable"). This note does not claim to have decoded that body. It takes every field the
report *did* decode, gives each one the JC3 member that plays the same role, the value to write,
and the formula that stands in for the missing arithmetic, with the in-game measurement that
would confirm or falsify each formula.

**Labels:** **decoded** = read at the file/offset named; **derived** = the stated arithmetic over
decoded inputs; **UNKNOWN** = searched and absent, with the file or probe that settles it.

**Why a substitute is legitimate here.** BmAK's per-mode numbers are *factors*
(`BattleModeDriveForceFactor` 75, `TurnOnSpotFrontTorqueFactor` 0.6, `BattleModeSteerAngleFactor`
2.5), applied by native code to an absolute base (engine torque, tyre force) that is not
serialised in any package. JC3 exposes drive torque the same way — as factors and ratios, never as
an absolute drive torque: `LandEngine.torque_factor_at_{min,optimal,max}_rpm` (0.86 / 490 / 0.84 on
the donor), `LandEngine.engine_max_damage_torque` (a 0.25..0.75 fraction), `Transmission.final_drive`
(a ratio); the only absolute torque member in the fleet is `Brakes.*.max_brake_torque`
(`Research/JC3Grab/VOCABULARY.md`, `LandEngine` / `Transmission` / `Brakes`). So the substitute
carries **ratios and angles**, never a torque-in-N·m claimed as BmAK's.

**Revert:** delete this file. Nothing else is written: this is a plan, no module, `.epe`, ledger
row or build tree is touched, and no game is launched (`tmp/freebuff/INSTRUCTIONS.md` §3, test ban).

---

## 0. The three rules every value below follows

| # | rule | why |
|---|---|---|
| **R1 — ratio, not magnitude** | a BmAK factor is carried as the *ratio between modes*, written onto a JC3 gain that multiplies JC3's own base (`r_m = r₀ × f_m / f₀`) | BmAK's base is inside `BatmanAK.exe`; JC3's base is inside `JustCause3.exe`; neither is a file, so only the ratio survives |
| **R2 — angles and lengths are 1:1** | degrees, metres and cm/s cross the boundary unchanged (80° is 80°; 10 cm = 0.10 m; 1200 cm/s = 43.2 km/h) | both sims use degrees and centimetres: BmAK `BattleModeYawOffset` 16384 = 90° in UE3 rotator units (decoded, `DRIVE_MODES.md` §5), JC3 `Suspension.*.longitudinal_tire_force_offset` 0..0.2 **m** (decoded, `VOCABULARY.md`) |
| **R3 — clamp, and record the clamp** | when the ratio or angle leaves the target member's shipped fleet range, write the fleet bound and record the shortfall as a compromise | a value outside the shipped set is a guess about the consumer; the fleet bound is decoded (`VOCABULARY.md` ranges, n per member) |

A fourth rule is a consequence of the mode structure, not a choice: **one static module cannot
hold two modes.** JC3 has no runtime handling switch (`tmp/freebuff/reports/mode-swap-trigger-closest-system-plan.md`
§0; `DRIVE_CARRIERS.md` §0 "the fleet has no per-wheel drive … no camera-relative vehicle
control"), so a per-mode value set is carried by **two entity variants** (pursuit / battle). The
tables below are therefore per-entity, and each row says which entity it lands in.

**Which BmAK number set is operative.** `DRIVE_MODES.md` §3 reads the shipped sim
(`Startup.upk` 169320), the sim CDO (`BmGame.upk` 129779) and the vehicle CDO (`BmGame.upk` 10923).
The shipped `SimulationModel` carries **no tag** at the turn-on-spot / battle offsets, so it
inherits the **class CDO** values — 0.6 / −0.5, 0.3, 60 / 90, 2.5, 80, 0.5, 75, 1200, 5, 4, 10,
0.025, 10. `MODES.md`'s playable-archetype readings (0.8 / −0.8, 0.3333, 600 cm/s, 150000) are a
*different object set* and are quoted here only where a ratio needs a normaliser; every build must
re-read the object it ships before writing (`Tools/scripts/grab_drive_modes.py --check` re-derives
the CDO numbers from the bytes).

---

## 1. Mode 0 — `BMDM_Drive` (pursuit)

**What is decoded:** the mode itself is the enum value `0` (`EBatmobileDriveMode`, export 129610);
`DriveMode` is a `ByteProperty` at **0x03b0** whose CDO tag is `None` = 0, and the shipped sim
inherits it (`DRIVE_MODES.md` §1, oracle `O7`). `SetDriveMode(0)` is called by
`RVehicleBatmobileBase.PursuitMode.BeginState` (export 10515) at script offset **69**, and by the
NPC twin (export 129841) at **58** (§2). The only mode-0-specific scalar in the packages is
`DriveModeEngineBrakingFactor` **0.003** at **0x01d4** (shipped override, `Startup.upk` 169320).

| BmAK field | offset | value | role in the missing arithmetic | JC3 member (module) | value to write | formula / rule | label |
|---|---|---:|---|---|---:|---|---|
| `DriveMode` | 0x03b0 | 0 | selects the pursuit set | none — the mode *is* the entity variant (pursuit leaf) | — | mode 0 = the donor entity unchanged; the battle leaf is the other variant | decoded + `mode-swap-trigger…md` §3.1 |
| `DriveModeEngineBrakingFactor` | 0x01d4 | 0.003 | coast torque as a fraction of engine torque | `LandEngine.resistance_at_optimal_rpm` (`land_engine`) | **0.1** (donor, unchanged) | this *is* r₀, the baseline of R1: `r = 0.1 × f / 0.003` | decoded value, derived bridge |
| `FrontWheelSteerPct` | 0x03b8 | 1.0 | front axle takes all of the steer | `LandGlobal.steering_type` (`land_global`, bytes-only) | `FrontSteered` (unchanged) | 1.0 front / 0 rear = JC3's only shipped steering mode | decoded (`DRIVE_CARRIERS.md` §5, 51 of 54 modules) |
| `AbsoluteMoveDirection` | 0x0378 | struct | the move direction the sim steers along | none — native heading state | — | pursuit steering stays on `LandSteering` alone | decoded field, carrier UNKNOWN (§8 U4) |
| `PMDodge*` (side swipe) | 0x1fdc / 0x1fe0 / 0x1fe4 | 5000 / 6000 / 0.25 s | lateral shove | `drift.keep_velocity_strength` / `velocity_rotation_*` + `arcade.turbo_jump.*` | see §5 | duration has no member (§8 U7) | decoded values, carrier amendment |

**The honest statement for mode 0:** JC3's own driving model *is* the pursuit substitute. Nothing
in mode 0 needs a torque figure — the pursuit mode is "the car, as shipped" — and writing a battle
value into a shared member is the only way to break it. That is the whole argument for the entity
split, and it is why mode 0's row count is one (engine braking) rather than fifteen.

---

## 2. Mode 1 — `BMDM_TurnOnSpot` (the station-keeping spin)

**What is decoded:** enum 1 exists and **no script body passes it** — four `SetDriveMode` sites,
values 0 and 2 only (`DRIVE_MODES.md` §7 item 2, oracle `O4`). The mechanism is present as fields:
`TurnOnSpotFrontTorqueFactor` **0.6** at **0x01c8** and `TurnOnSpotRearTorqueFactor` **−0.5** at
**0x01cc** (sim CDO), `DesiredTurnOnSpotSpeed` **180** at **0x01d8**, `TurningModeMaxSpeed` **300**
at **0x02c4**, `TurnOnSpotModeEngineBrakingFactor` **0.01** at **0x01d0** (shipped),
`BattleModeTurnOnSpotTorqueFactor` **0.3** at **0x02e0**, `BattleModeStopAndTurnAngleStationary`
**60** at **0x02f8**, `TurnOnSpotSteeringSpeedCurve` at **0x0268** (struct, no shipped value).

**What the pair means (derived, and the core of the substitute):** two factors of *opposite sign*
on the two axles cannot be a steering angle — a steer angle has no sign per axle. They are a
front/rear **counter-torque**: the front axle drives forward at 0.6 of the base torque while the
rear drives backward at 0.5, and the two moments add instead of cancelling because the axles sit on
opposite sides of the centre of mass. The yaw moment is therefore

```
M_yaw  =  ( |f_front| + |f_rear| ) × T_base × half_track / 2
       ∝  ( |f_front| + |f_rear| )                      … the pair's sum, not its difference
```

JC3 cannot reproduce the pair (no per-axle drive: `DRIVE_CARRIERS.md` §0, §4.1 — one
`Transmission`, one `Tire` per axle, 0 per-wheel members). What it *does* have is a single signed
yaw torque with exactly this role: the `CustomLandGlobal.drift` block, "the only place in a land
vehicle where the car is rotated by a torque rather than by a front wheel angle"
(`DRIVE_CARRIERS.md` §3.1).

| BmAK field | offset | value | role | JC3 member (`custom_land_global`) | value to write | formula / rule | label |
|---|---|---:|---|---|---:|---|---|
| `TurnOnSpotFrontTorqueFactor` + `TurnOnSpotRearTorqueFactor` | 0x01c8 / 0x01cc | 0.6 / −0.5 | counter-torque, summed | `drift.constant_drift_torque` (fleet 0..20000, donor 0) | **13750** | `T = 20000 × (0.6 + 0.5) / (0.8 + 0.8)` = 20000 × 0.6875. 20000 is the fleet max; 1.6 is the archetype pair's sum (`MODES.md`, `four-wheel-drive…md` §2) used only as the normaliser | decoded inputs, derived normaliser |
| `DesiredTurnOnSpotSpeed` | 0x01d8 | 180 cm/s | the tangential speed the spin is driven to | `drift.max_drift_torque` (0..35000, donor 5000) | **20000** | `ω = v / half_track = 1.80 / 0.885 = 2.034 rad/s = 116.5 °/s`; 0.885 m is `LandGlobal.base_wheel_hardpoint_positions[0].position[0]` (decoded, `DRIVE_CARRIERS.md` §9). One turn in **3.09 s** | derived (unit bridge: m/s ÷ m) |
| `TurnOnSpotModeEngineBrakingFactor` | 0x01d0 | 0.01 | coast torque while spinning | `LandEngine.resistance_at_optimal_rpm` (0..0.5, donor 0.1) | **0.333** | `r = 0.1 × 0.01 / 0.003` = 0.333 (R1; in range) | derived |
| `TurningModeMaxSpeed` | 0x02c4 | 300 cm/s = 10.8 km/h | upper speed bound of the spin | none — no member caps a drift state's speed | — | lower bound only: `drift.min_speed_to_drift_kmph` **0** (a shipped value: 4 builds, `v0400_car_mugello_vintagesports`) | UNKNOWN (§8 U2) |
| `BattleModeStopAndTurnAngleStationary` | 0x02f8 | 60° | how far the body may deviate | `drift.max_drift_angle_deg` (20..60, donor 45) | **60** | 1:1, fleet max — the member's shipped maximum is the same quantity | decoded value, 1:1 |
| `drift.steering_sensitivity` (no BmAK twin) | — | — | input gain into the block | `drift.steering_sensitivity` (0.5..4, donor 4) | **4** (unchanged) | the spin is driven by the state, not by a stick gain; leaving 4 keeps BmAK's "full authority when the mode is on" reading | decoded |
| `ForceTurnOnSpotMode` | 0x0294 (Bool) | **no tag** | the flag that would enter the mode | — | — | no value exists to carry; the entity is the switch | UNKNOWN (§8 U3) |

**Why the spin is torque-limited, not rate-limited (derived — this is the arithmetic that
`SetDriveMode` hides):**

```
I_zz  = mass × unit_inertia_yaw = 6000 × 4.0 = 24 000 kg·m²   (Builds/bm-RC2 rigid_body, read in
                                                              air-control-closest-system-plan.md §2.2)
T     = 13 750 N·m
α     = T / I_zz = 0.573 rad/s² = 32.8 °/s²
θ(t)  = ½ α t²   →   90° in 2.34 s ; 360° in 4.68 s (torque-limited, i.e. slower than the 3.09 s
                      the 116.5 °/s target implies)
```

That inversion is the substitute for the hidden body: `SetDriveMode(1)`'s job is to apply the
counter-torque pair; the JC3 version applies one torque and lets the rigid body integrate it.

**Cross-check that changes an existing band.** `four-wheel-drive-and-spin-in-place-build-plan.md`
P1 asks for "≥ 30° within 1.0 s, ≥ 90° within 2.0 s". Inverting `θ = ½ α t²` at I_zz = 24 000:

* **30° in 1.0 s** needs α = 1.047 rad/s² → **25 133 N·m**, which is above
  `drift.constant_drift_torque`'s fleet maximum (20 000) and only reachable if `max_drift_torque`
  (fleet 0..35 000) adds on top — additivity is UNKNOWN (`air-control…md` §6 U6 asks the same of the
  same block);
* **90° in 2.0 s** needs α = 0.785 rad/s² → **18 850 N·m**, which *is* inside the fleet range: the
  archetype pair (20 000 → 1.94 s) passes, the CDO pair (13 750 → 2.34 s) does not.

So P1's fast half is not reachable from the values the shipped sim actually inherits, and its 2.0 s
half is reachable only at the archetype pair. Either the effective inertia is below 24 000 (the
module ships `use_calculated_inertia` 1, so `unit_inertia_yaw` may be ignored and the
collision-derived tensor used — 18 850 N·m at I = 17 600 would also give 2.0 s), or the spin needs a
second torque source. P-MODE-1 measures exactly this (§8 U1).

---

## 3. Mode 2 — `BMDM_BattleMode`

**What is decoded:** `SetDriveMode(2)` at offset **88** (export 10529) and **103** (export 129848),
guarded by a read of `DriveMode` at 59 / 74 whose comparison operator is UNKNOWN; the battle value
set is the `BattleMode*` family at 0x02cc–0x0324, the vehicle-side `BattleModeYawOffset` **16384**
at **0x1910**, and the dodge fields at 0x11e4 / 0x1208 / 0x1914 / 0x1fdc–0x1fe4.

Battle mode is where the native body does the most work (script has *no* steering call at all:
`BattleMode.Tick` "handles audio state, the winch, stuck-flip recovery" only, `DRIVE_MODES.md` §4).
Every row below is therefore a substitute, and four of them are clamped.

| BmAK field | offset | value | role | JC3 member (module) | value to write | formula / rule | label |
|---|---|---:|---|---|---:|---|---|
| `BattleModeSteerAngleFactor` | 0x0300 | 2.5 | steer-input gain | `LandSteering.steer_in_speed_factor` (`land_steering`, 1.2..10, donor 1.5) | **2.5** | 1:1 — the BmAK value is inside the fleet range, and both are a gain on steer input | decoded |
| `BattleModeMaxSteering` | 0x02cc | 80° | the lock the body turns to | `LandSteering.steer_angle_min_speed_deg` (20..45, donor 35) | **45** | `θ_ws = min(80, 45)`; deficit `80 − 45 = 35°` goes to yaw torque (§2's 13 750 N·m is not enough: 35° in 0.5 s needs 117 286 N·m) — so the deficit is carried by **grip**, not torque | decoded, clamped (R3) |
| `BattleModeTrailingSteerFactorMoving` | 0x0320 | −0.5 | rear axle steers against the front | `LandGlobal.rear_wheels.arcade_friction_multiplier` (`land_global`, 1..6) + `front_wheels…` (0.8..5) | front **2.8**, rear **1.4** | `grip_rear = grip_front × (1 + f) = 2.8 × 0.5 = 1.4`; the fleet's rear/front ratio is ≥ 1 on all 145 builds, so 0.5 is the *inversion* the factor asks for | derived (no rear-steer member: `steering_type` is `FrontSteered` everywhere) |
| `BattleModeTrailingSteerFactorTurnOnSpot` | 0x031c | 1.0 | rear "steers with" the front at rest | same two members | not written | conflicts with −0.5 in one static module: the moving value is written, the stationary case is produced by the drift torque | UNKNOWN by construction (§8 U5) |
| `BattleModeLatSlipScale` | 0x02d4 | 4 | lateral slip scale | `Tire.lat_peak_sa_deg` (8..15, donor 12), `lat_sat_sa_deg` (15..25, donor 20) | **15** / **25** | `θ' = min(fleet_max, θ × s)`: 12×4 = 48 → 15; 20×4 = 80 → 25. Both clamps hit; the members are angles, so the scale arrives compressed to 1.25× / 1.25× | decoded inputs, clamped, **direction** UNKNOWN (§8 U6) |
| `BattleModeLongSlipScale` | 0x02d8 | 10 | longitudinal slip scale | `Tire.fwd_peak_sr` (0.4..9, donor 0.5), `fwd_sat_sr` (1..10, donor 2) | **5.0** / **10** | 0.5×10 = 5.0 (in range); 2×10 = 20 → clamp 10 | derived, clamped |
| `BattleModeRearWheelTorquePower` | 0x02d0 | 0.5 | half the drive to the rear axle | `arcade.heat_boost.grip_multiplier` (`custom_land_global`, 1.3..4.5, donor 1.5) | **4.5** (fleet max) | 4WD is not expressible (`DRIVE_CARRIERS.md` §0/§4.1: 0 per-wheel members, one driveline); the closest statement is "all four tyres are pulling", i.e. maximum arcade grip. `mode-switch-carriers.md` §2.4 reads the donor as 4.26 — **re-read the shipped module before writing** (that is the same contradiction the 4WD plan §7 records) | amendment, clamped |
| `BattleModeDriveForceFactor` | 0x02f4 | 75 | drive-force gain | `arcade.heat_boost.torque_multiplier` (1.5..40, donor 2) | **40** (fleet max) | 75 is a gain on a native force expression with no unit; 40 is the largest shipped multiplier. Shortfall **1.88×** — recorded, not hidden | decoded, clamped (R3) |
| `BattleModeEngineBrakingFactor` | 0x02dc | 0.025 | coast torque | `LandEngine.resistance_at_optimal_rpm` (0..0.5, donor 0.1) | **0.5** (fleet max) | `r = 0.1 × 0.025 / 0.003 = 0.833` → clamp 0.5; shortfall **1.67×** | derived, clamped |
| `BattleModeDrivingForceZOffset` | 0x0324 | 10 cm | drive force applied above the hub line (anti-squat/pitch) | `Suspension.{front,rear}.longitudinal_tire_force_offset` (`suspension`, 0..0.2 **m**, donor 0) | **0.05 / 0.10** | 10 cm = **0.10 m**, 1:1 (R2); front takes half because the moment is shared with the suspension's own geometry. Moment `M = F × 0.10` | decoded value, unit bridge |
| `BattleModeMaxSpeed` | 0x02f0 | 1200 cm/s = 43.2 km/h | battle speed ceiling | `Transmission.top_speed` (`transmission`, 90..505 km/h, donor 320) | **90** (fleet min) | 43.2 is below every shipped car (fleet min 90): the cap can only be set to 90, i.e. **2.08× over**. The residual 46.8 km/h has no member | decoded, clamped — the largest compromise in this plan |
| `BattleModeThrottleSpeed` | 0x02ec | 5 | throttle ramp, **unit undocumented** (`four-wheel-drive…md` §3 labels it "rate-sized") | `Transmission.clutch_delay` (`transmission`, 0.05..0.5 s, donor 0.1) | **0.1** (unchanged) | no unit bridge exists: 5 is neither seconds nor a fraction. Recorded, measured by the 0→50 km/h probe | UNKNOWN unit (§8 U8) |
| `BattleModeVSpeedCurve` | 0x0218 | 3-point curve (0→60, 600→40, 1200→30 per `MODES.md`) | force multiplier vs speed | none — no drive-force-vs-speed member in `LandEngine`/`Transmission` (the only `*_vs_speed` curves are `Tire`'s and `TrainAudio`'s) | — | the curve's shape is not writable; its *effect* is measured (top speed at 3 s) | UNKNOWN (§8 U9) |
| `BattleModeYawOffset` | 0x1910 (vehicle) | 16384 = 90° | facing offset from the movement direction | none — 0 data members, 0 keymap actions (`DRIVE_CARRIERS.md` §4.1) | — | camera-relative control stays a code bridge; 90° is the target, not a writable value | UNKNOWN (§8 U4) |
| `bForceBattleModeMovement` | 0x11dc (Bool) | no tag | forces movement in battle | — | — | no writer in the corpus scan either (`DRIVE_MODES.md` §5) | UNKNOWN (§8 U4) |
| `AbsoluteMoveDirection` | 0x0378 | struct | the direction the car moves while facing elsewhere | — | — | same gap | UNKNOWN (§8 U4) |

---

## 4. What the substitute does *not* reproduce (stated as arithmetic, not as a shrug)

| native step | the substitute's stand-in | the error it introduces |
|---|---|---|
| `F = T_eng(rpm) × gear × final_drive / r_w` with `BattleModeDriveForceFactor` scaling `F` | JC3 computes the same expression natively from `LandEngine` + `Transmission`; the factor is carried as `heat_boost.torque_multiplier` 40 | JC3's base torque and gear set are its own; only the *gain* is BmAK's, and 40 < 75 |
| per-axle torque signs producing counter-torque | one signed torque, `drift.constant_drift_torque` 13 750 | the front/rear split is lost: the car yaws without the "front pulls, rear pushes" wheel behaviour |
| slip scales multiplying tyre force | tyre curve angles moved to their fleet maxima | a scale is not an angle; the clamp compresses 4× to ~1.25× |
| force applied 10 cm above the hub line | `longitudinal_tire_force_offset` 0.10 m | exact in metres, but JC3 applies it per axle (two quarter-forces) rather than one central force |
| a 43.2 km/h battle ceiling | `top_speed` 90 | 2.08× too fast; nothing in data fixes it |

---

## 5. The dodge / strafe fields (mode 0 and mode 2, one block)

| BmAK field | offset | value | JC3 member | value to write | formula | label |
|---|---|---:|---|---:|---|---|
| `BattleDodgeImpulse` | 0x1914 | 100000 | `arcade.turbo_jump.punch_speed_kph` (`custom_land_global`, 50..50 on 145 builds) | **50** | `Δv = 100000 / 6000 = 16.67 m/s = 60.0 km/h`; the member's shipped value is fixed at 50, so 50 is written and the 20 % shortfall recorded | derived, 1 value shipped |
| `StrafeCooldown` | 0x11e4 | 0.75 s | `turbo_jump_cooldown` (`vehicle_misc`, 5..5 on 232 builds) | **0.75** | 1:1 seconds (R2). Leaves the shipped set (5 is the only shipped value); the 0.75 s is BmAK's decoded cooldown, so it wins the semantic and loses the family | decoded value, out-of-family |
| `PMDodgeDuration` | 0x1fe4 | 0.25 s | `arcade.turbo_jump.punch_delay_time` (0.1..0.1) / `nitro_boost.boost_blend_time` (0.2) | **0.2** | no burn-duration member exists; 0.2 s is the only shipped blend time. A 0.25 s thrust is not expressible | UNKNOWN (§8 U7) |
| `PMDodgeTorque` / `PMDodgeForce` | 0x1fdc / 0x1fe0 | 5000 / 6000 | `turbo_jump.f_multiplier` (12..15, donor 15) | **15** (unchanged) | torque/force have no per-axis member; the multiplier is the nearest gain | decoded values, amendment |
| `StrafeFwdCorrectionForce` | 0x1208 | 3000 | `drift.keep_velocity_strength` (0..1.5, donor 1) | **1.5** (fleet max) | keeps velocity through the slide, which is the correction force's role | derived (fleet max) |

---

## 6. The reconstructed per-tick arithmetic (the thing the native body hid)

Written as the substitute's model, with each line naming the JC3 member that supplies it. This is
**derived** from the decoded fields and is the exact claim the pilot cards test.

```
on SetDriveMode(m)            # the native thunk G3-02l could not read
    m = 0  → load the pursuit entity's module set        (drive mode 0 = the donor)
    m = 1  → constant_drift_torque 13750, min_speed_to_drift_kmph 0,
             max_drift_angle_deg 60, resistance_at_optimal_rpm 0.333
    m = 2  → constant_drift_torque 4125 (= 0.3 × 13750, BattleModeTurnOnSpotTorqueFactor),
             steer_in_speed_factor 2.5, steer_angle_min_speed_deg 45,
             rear grip 1.4 / front 2.8, resistance_at_optimal_rpm 0.5

per tick, mode m:
    F_drive   = gain_m × T_eng(rpm) × gear × final_drive / r_w      gain: heat_boost.torque_multiplier
                                                                    (mode 2: 40; mode 0: 1.0)
    M_pitch   = F_drive × 0.10                                      longitudinal_tire_force_offset
    B_eng     = r_m × T_eng(rpm)                                    resistance_at_optimal_rpm
    θ_wheel   = min(lock_m, steer_angle_min_speed_deg) × steer_in_speed_factor × input
    M_yaw     = (mode 1 or stationary)  constant_drift_torque
                (mode 2, moving)        grip asymmetry: rear 1.4 vs front 2.8 → oversteer moment
    slip      = tyre curve evaluated at lat_peak/lat_sat and fwd_peak/fwd_sat angles written above
    ω(t+dt)   = ω + (M_yaw / I_zz) dt        with I_zz = mass × unit_inertia_yaw (24 000, or the
                                             collision-derived tensor when use_calculated_inertia=1)
```

Everything above is one line per member in §2–§3; nothing in it is a BmAK implementation invented
from memory. The two places the model is *known* to differ are the per-axle split and the battle
speed cap (§4).

---

## 7. The measurements that fit each formula, and the pilot cards

The pass bands below are the only numbers in this plan that a take can fail. Each is a derived
band (±20 % is the project's ratio tolerance, `T10_DAMAGE.md` §0 as used by
`air-control-closest-system-plan.md` D9) except where a measured repeatability figure exists.

### 7.1 What each formula needs measured

| formula | measurement | why it fits |
|---|---|---|
| `ω = v_turn / half_track` (§2) | heading change per second at full spin, from the minimap arrow | both sides are yaw rate; the 116.5 °/s target is a prediction, not a setting |
| `θ(t) = ½ α t²` (§2) | time from 0 to 90° | inverts to the **effective** inertia: `I_eff = T t² / (2θ)`; with T = 13 750 and θ = π/2 this is 24 000 at t = 2.34 s and 17 600 at t = 2.0 s — the take *is* the inertia measurement (§8 U1) |
| `r = 0.1 × f/0.003` (§1, §2, §3) | coast-down deceleration at 100 km/h, pursuit vs battle | the ratio 0.833/0.1 is 8.33×; the clamp caps it at 5×, so the measured ratio should land in 1.5–5.0 |
| `gain 40` (§3) | 0→50 km/h time, battle vs pursuit | a force ratio shows as a time ratio; 40/2 predicts ≈ 20× if the multiplier were linear, so the take also tests linearity |
| `grip_rear/grip_front = 0.5` (§3) | rear tyre slip angle vs front at 60 km/h full stick | rear-slip lead is the observable the member controls |
| `top_speed 90` (§3) | speed at 3 s of full throttle in battle | a cap is a plateau; 90 is the only value the member can hold |
| `16.67 m/s` punch (§5) | displacement in 0.5 s after LS+A | Δv = impulse/mass is the member's own definition |
| `T = 20000 × pair/1.6` (§2) | heading rate at a known steer input, mode 1 vs mode 2 (13 750 vs 4125 = 3.33×) | the pair ratio is the only BmAK relation that survives |

### 7.2 The three pilot-card sentences (one per mode, each with its band)

> **P-MODE-0 (Drive).** On the airfield, from rest to 100 km/h in **15.6–17.2 s** (the measured
> QA-1 band, `Working/Q/PREDICTIONS.md` D-1), then lift off at 100 km/h: the car must lose speed
> **at most 1/1.5** as fast in this entity as the battle entity does at the same speed, and must not
> decelerate faster than **2.0 km/h per second** in the first second — the two together separate the
> 0.003 / 0.025 engine-braking pair through a 5× clamp.

> **P-MODE-1 (TurnOnSpot).** In pursuit, stop dead (0 km/h), engage the mode, apply full stick one
> way: **90° of heading in 1.9–2.8 s** (derived 2.34 s, ±20 %), **360° in 3.7–5.6 s**, ground position
> moved **≤ 5 m**, speed never above **8 km/h**; repeat the other way and get the same four numbers.
> Pass on **2 of 2** directions; a pass below 1.9 s means the effective inertia is lighter than the
> 24 000 kg·m² this plan assumes and the band is rewritten from the take, never the reverse.

> **P-MODE-2 (Battle).** From 60 km/h, full stick held 1 s: the yaw rate must be **1.33–2.00×** the
> pursuit entity's yaw rate for the same input at the same speed (the 2.5 / 1.5 steer-gain ratio),
> the **rear tyre slip must lead the front by ≥ 1.5×**, and from 0 km/h at full throttle the speed
> must plateau at **≤ 90 km/h** by 3 s and not at **43.2 km/h** (the cap the data cannot express).

Each sentence uses only: a decoded QA-1 measurement (`D-1`), a derived ±20 % band, and a member's
own ratio. None names a key or a menu item; the keys come from `Working/Q/PILOT/CONTROLS.md` when
`Working/Q/PILOT/DRIVE.md` is written (`CARD_FORMAT.md` rule 6), and `DRIVE.md` is still
`not written` in that file's §4 table, so these three sentences are the card's *SEE* lines, not yet
a runnable card.

---

## 8. UNKNOWNs — each with the file or probe that settles it

| # | UNKNOWN | what was tried here | settles it |
|---|---|---|---|
| **U1** | the effective yaw inertia `I_zz` (24 000 assumes `unit_inertia_yaw` is used) | read `Builds/bm-RC2` `rigid_body`: mass 6000, `unit_inertia_yaw` 4.0, `use_calculated_inertia` **1** (which may ignore the unit inertia) | **probe P-MODE-1**: `I_eff = T t²/(2θ)`; static route = the `RigidBody` consumer in `JustCause3.exe` (not decoded) |
| **U2** | whether `drift.*` torque acts at 0 km/h at all | `DRIVE_CARRIERS.md` §3.1: the block is slip-angle driven; `min_speed_to_drift_kmph` 0 ships on 4 builds, which proves the gate opens, not that torque exists | **probe P-MODE-1** (first observation: does the car rotate, or just sit?); static route = the Drift consumer in `JustCause3.exe` |
| **U3** | what selects `BMDM_TurnOnSpot` in BmAK | four `SetDriveMode` sites, 0 and 2 only (`DRIVE_MODES.md` §7 item 2); `ForceTurnOnSpotMode` carries no tag in any of the three objects | the native `SetDriveMode` body at `BatmanAK.exe` `0x1404AB050` (`REGISTRATION.md`:29-30) — the address is decoded, the body is not; or a live BmAK probe on the sim tick (needs a Steam copy, `OPERATOR_PRIORITIES.md`) |
| **U4** | the camera-relative move (16384 = 90°, `AbsoluteMoveDirection`, `bForceBattleModeMovement`) | 0 data members and 0 keymap actions match (`DRIVE_CARRIERS.md` §2, §4.1); only `LSTICKGENERIC → MOVE_ALL` takes a whole stick, on-foot scope | **probe P-MODE-2**'s stick-vector half; static route = the native class→action-set selection in `JustCause3.exe`, or a `.epe` force along camera yaw (`air-control…md` §3 leg 3 pattern) |
| **U5** | `TrailingSteerFactorTurnOnSpot` 1.0 vs `…Moving` −0.5 in one static module | both are decoded and both cannot be written; one entity, one value | the **second entity** (already required for the battle set, `mode-swap-trigger…md` §3.1) — still cannot hold two speeds; settled by the P-MODE-2 stationary half and recorded as a limit |
| **U6** | the **direction** of `BattleModeLatSlipScale` 4 / `LongSlipScale` 10 (multiplier on tolerated slip, or divisor on force) | the fields are named only by scale; no consumer is decoded. Written multiplicatively (angles × s, clamped) | **probe P-MODE-2** rear-slip lead; if the car grips harder instead of sliding, the reading is ÷ and the four members flip to their minima (8 / 15 / 0.4 / 1) |
| **U7** | a thrust *duration* (`PMDodgeDuration` 0.25 s) | no drift member counts time; `turbo_jump` is instantaneous; `boost_blend_time` 0.2 is the only shipped blend | the `arcade.turbo_jump` consumer in `JustCause3.exe`; measured by the P-MODE-0/§5 displacement take (0.5 s window) |
| **U8** | the unit of `BattleModeThrottleSpeed` 5 | undecoded: `four-wheel-drive…md` §3 calls it "rate-sized"; no member in `LandEngine`/`Transmission` is a throttle ramp | **probe**: 0→50 km/h in battle vs pursuit; the ratio is the ramp's observable, the unit falls out |
| **U9** | the shape of `BattleModeVSpeedCurve` (0→60, 600→40, 1200→30) | no drive-force-vs-speed curve exists in a land module (`VOCABULARY.md`: `LandEngine` has `rpm_power_band`, no curve; the only `*_vs_speed` rows are `Tire` and `TrainAudio`) | the `Transmission`/`LandEngine` consumer in `JustCause3.exe`; or a `Tire.fwd_long_tire_*` curve rebuild, which is not a scale and is out of scope here |
| **U10** | whether the shipped sim's CDO set (0.6 / −0.5 / 75 / 1200) or the archetype set (0.8 / −0.8 / 500 / 600) is what the delivered car runs | both are decoded; the shipped object carries no tag at those offsets, so it inherits the CDO (`DRIVE_MODES.md` §1 oracle `O7`) — but `MODES.md`'s archetypes are the playable packages | `Tools/scripts/grab_drive_modes.py --check` on the exact object the build names; re-derive before writing any of §2's normalisers |

---

## 9. Sources, with the offsets that make each row checkable

| what | where |
|---|---|
| drive-mode enum, call sites, field table, defaults, oracle ids | `Research/BatmobileGrab/DRIVE_MODES.md` §1–§3, §5, §9 (generated by `Tools/scripts/grab_drive_modes.py`, `--check` re-derives) |
| the UNKNOWN this plan answers | `Research/BatmobileGrab/DRIVE_MODES.md` §7 item 1; `tmp/freebuff/reports/G3-02l.md` UNKNOWN 1 |
| BmAK class offsets 0x01c8 … 0x03b8, 0x1910, 0x11dc, 0x1fdc | `DRIVE_MODES.md` §3 table (offsets from the BmSDK-AK layout, `BMSDK_OFFSETS.json`) |
| `0x3B0` written by `SetDriveMode`; `SetDriveMode` at `0x1404AB050`; `SetSuspensionForDriveMode` at `0x14051B260`; `SkidToStop` → `0x3B1` | `Research/BatmobileGrab/REGISTRATION.md`:29-30, 53-54, 127-128 |
| the native function list (`SetDriveMode` is one of 5 `URVehicleSimBatmobile` natives) | `Research/BatmobileGrab/NATIVE.md` ("`URVehicleSimBatmobile` — 5: Boost, ForceUpdateTyreFriction, SetDriveMode, SetSuspensionForDriveMode, SkidToStop") |
| JC3 member names, fleet ranges, donor values (all members quoted above) | `Research/JC3Grab/VOCABULARY.md` §`LandEngine`, `LandGlobal`, `LandSteering`, `Transmission`, `Suspension`, `Tire`, `Brakes`, `CustomLandGlobal`, `VehicleMisc` |
| no 4WD / no rear steer / no camera-relative control; drift block is the only yaw-torque carrier; `steering_type` `FrontSteered` | `Research/JC3Grab/DRIVE_CARRIERS.md` §0, §2, §3.1, §4.1, §5 |
| half-track 0.885 m (the ω derivation) | `Research/JC3Grab/DRIVE_CARRIERS.md` §9 (`base_wheel_hardpoint_positions[0].position` ±0.885) |
| mass 6000, `unit_inertia_yaw` 4.0, `use_calculated_inertia` 1 (the I_zz derivation) | `tmp/freebuff/reports/air-control-closest-system-plan.md` §2.2 (read from `Builds/bm-RC2` `rigid_body.vmodc`) |
| the existing spin band this plan corrects; the archetype pair 0.8/−0.8; the module tree the edits land in | `tmp/freebuff/reports/four-wheel-drive-and-spin-in-place-build-plan.md` §2, §8, §11 |
| two entities are required for a per-mode value set | `tmp/freebuff/reports/mode-swap-trigger-closest-system-plan.md` §0, §3.1 |
| D-1's measured 0–100 band (P-MODE-0) | `Working/Q/PREDICTIONS.md` D-1 (15.6–17.2 s, QA-1 test-085) |
| pilot-card grammar, `SEE` rules, the `DRIVE.md` gap | `Working/Q/PILOT/CARD_FORMAT.md` §1–§4 |
| test ban, label rule, output rules | `tmp/freebuff/INSTRUCTIONS.md` §3–§4 |

---

## 10. What was checked for this plan

| check | result |
|---|---|
| every BmAK number quoted exists in `DRIVE_MODES.md` §3 at the offset given | all **40** field rows of §3 were read (the generator's own count: "enum 4, fields 40"); the enum (0/1/2/3) and the four call sites match §1–§2 |
| every JC3 member name quoted exists in `VOCABULARY.md` with the range stated | 22 members cross-read (`LandEngine` 4, `LandGlobal` 3, `LandSteering` 2, `Transmission` 2, `Suspension` 1, `Tire` 4, `CustomLandGlobal` 4, `Brakes` 1, `VehicleMisc` 1) |
| the derived numbers | recomputed in one pass: ω 2.0339 rad/s = 116.53 °/s, 360° in 3.09 s; I_zz 24 000; T 13 750; α 0.5729 rad/s² = 32.8 °/s²; 90° in 2.34 s (band 1.87–2.81); 30° in 1.0 s needs 25 133 N·m; 90° in 2.0 s needs 18 850 N·m; 35° in 0.5 s needs 117 286 N·m; engine-braking 0.1 / 0.333 / 0.833→cap 0.5; 75/40 = 1.88×; 90/43.2 = 2.08×; 100000/6000 = 16.67 m/s = 60.0 km/h; rear grip 1.4; slip clamps 48→15, 80→25, 5.0, 20→10; 10 cm = 0.10 m; steer gain 2.5/1.5 = 1.667 (band 1.33–2.00) |
| no value was invented from general knowledge of UE3, BmAK or JC3 | every row carries a file/offset or is labelled derived with its inputs; the two out-of-family writes (cooldown 0.75, top speed 90) are labelled as clamps/out-of-family, not as shipped values |
| nothing was written outside this report | `ls tmp/freebuff/reports/drive-mode-torque-arithmetic-substitute-plan.md` was absent before (`No such file or directory`) and exists after; no module, `.epe`, `.toc`, ledger row or build tree was touched |

**Limits.** Static only: no game launched, attached to or installed to. `SetDriveMode`'s body is
still not decoded — `REGISTRATION.md` gives its address (`0x1404AB050`), not its instructions — so
every formula here is a **substitute**, and each one is paired with the take that would falsify it.
The one measurement that would replace the largest guess (U1, effective inertia) is a single
2.3-second spin in the pursuit entity, which is why P-MODE-1 is written as a time band rather than
as a torque.

**COMPROMISES** (each needs the operator, per `tmp/freebuff/INSTRUCTIONS.md` §3):

1. `BattleModeMaxSpeed` 43.2 km/h cannot be expressed: the closest member bottoms out at 90 km/h
   (2.08× too fast).
2. `BattleModeDriveForceFactor` 75 cannot be carried above 40 (1.88× short).
3. `BattleModeEngineBrakingFactor`'s 8.33× ratio is clamped to 5× by `resistance_at_optimal_rpm`'s
   fleet maximum.
4. Four-wheel drive and the camera-relative move remain code bridges: no data member exists, so
   `BattleModeRearWheelTorquePower` 0.5 becomes a grip multiplier and the 90° yaw offset becomes an
   outside-the-module job.
