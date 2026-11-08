# T-AC1 / T-SR1 — every JC3 carrier for rotating a land vehicle in the air

STATUS: done — 12 candidates opened, 5 decoded with file offsets, 1 ledger claim refuted
(T-SR1's "aircraft only"), no candidate proven to reproduce BmAK air control; the exact missing
capability is stated in §9. Nothing was tuned; nothing was tested (test ban).

Lane: air-control carrier search, 2026-11-06. Brief: T-AC1 (`AirControlYawTorqueFactorMax` 8000 and
the rest of the row) and T-SR1 (`JumpRampRightingTorque` 2000, `JumpNoRampRightingTorque` 2000,
`StayUprightConstraintSetup/Instance`) are marked `out`; a row that says "JC3 has no system" is a
to-do. Find ANY way a JC3 land vehicle can be rotated while airborne.

Labels: **decoded** = a member, value or byte read at the file/offset named; **derived** = arithmetic
or a stated rule over decoded inputs; **UNKNOWN** = searched and absent, with where it would be found.

---

## 1. The BmAK numbers the carriers must reach

`decoded` — `Research/BatmobileGrab/MECHANICS_NAMES.md` (export offsets, all four packages) and
`Research/BatmobileGrab/MODES.md` (values, serialised column):

| row | member | offset | type | value | serialised |
|---|---|---|---:|---|---|
| T-AC1 | `AirControlYawTorqueFactorMax` | `0x4A8` | float | **8000** (all 4 packages) | yes |
| T-AC1 | `AirControlPitchTorqueFactorMax` | `0x4AC` | float | — | no |
| T-AC1 | `AirControlYawTorqueFactorMin` | `0x4B0` | float | — | no |
| T-AC1 | `AirControlPitchTorqueFactorMin` | `0x4B4` | float | — | no |
| T-AC1 | `AirControlInterpTime` | `0x4B8` | float | — | no |
| T-AC1 | `AirControlTimeInAir` | `0x4BC` | float | — | no |
| T-AC1 | `AirControlTurnTorque` (`RVehicleSimCar`) | `0x17C` | float | — | no |
| T-AC1 | `AirControl` (`Pawn`) | `0x448` | float | — | no |
| T-SR1 | `JumpRampRightingTorque` | `0x1A64` | float | **2000** (all 4) | yes |
| T-SR1 | `JumpNoRampRightingTorque` | `0x1A68` | float | **2000** | yes |
| T-SR1 | `StayUprightConstraintSetup` | `0x6E4` | object ref `RB_StayUprightSetup` | 5106 / 5157 / 3123 / 5196 | yes |
| T-SR1 | `StayUprightConstraintInstance` | `0x6EC` | object ref `RB_ConstraintInstance` | 5098 / 5149 / 3120 / 5188 | yes |
| T-SR1 | `StayUprightRollResistAngle` | `0x6D4` | deg | — | no |
| T-SR1 | `StayUprightPitchResistAngle` | `0x6D8` | deg | — | no |
| T-SR1 | `StayUprightStiffness` | `0x6DC` | engine stiffness | — | no |
| T-SR1 | `StayUprightDamping` | `0x6E0` | engine damping | — | no |
| T-SR1 | `BattleModeUprightTorqueFactor` | `0x370` | factor | — | no |
| T-SR1 | `BattleModeUprightMaxTorque` | `0x374` | engine torque | — | no |

Measured window the air-control numbers run in: **1.212 s mean airborne** over three ramp jumps
(`Research/BatmobileGrab/FOOTAGE.md` F-6, 1.251 / 1.183 / 1.200 s). So a carrier must accept a
per-frame yaw/pitch torque for ~1.2 s with no ground contact.

---

## 2. What the land modules actually contain

`decoded` — re-decoded this session with `Tools/scripts/jc3adf.py` (ADF v4 type dictionary; offsets
are absolute within the module struct, as the reader's own docstring states). Two module roots the
155-value vocabulary reports at n=145 (`CustomLandGlobal`) and the base `LandGlobal`:

### 2.1 `CustomLandGlobal` — `v0012_car_autostraad_atv_custom_land_global.vmodc`, type size 256 B

| member path | type | size | offset | fleet (VOCABULARY) | donor |
|---|---|---:|---:|---|---|
| `gravity_multiplier_grounded` | float | 4 | **0x0C** | 1..1.5 (med 1, n=145) | 1 |
| `gravity_multiplier_in_air_up` | float | 4 | **0x10** | 1..2 (med 1.5, n=145) | 1 |
| `gravity_multiplier_in_air_down` | float | 4 | **0x14** | 1..2 (med 1.5, n=145) | 1 |
| `takeoff_pitch_damping` | float | 4 | **0x18** | 0.2..0.8 (med 0.5, n=145) | 0.5 |
| `drift.drift_entry_slip_angle` | float | 4 | 0x34 | 10..180 | 20 |
| `drift.constant_drift_torque` | float | 4 | **0x44** | 0..20000 (med 2000) | 0 |
| `drift.max_drift_torque` | float | 4 | **0x48** | 0..35000 (med 12000) | 5000 |
| `drift.counter_steer_torque` | float | 4 | **0x4C** | 0..60000 (med 10000) | 3000 |
| `drift.counter_steer_torque_handbrake` | float | 4 | 0x50 | 0..100000 (med 36000) | 30000 |
| `drift.counter_steer_torque_brake` | float | 4 | 0x54 | 0..45000 (med 10000) | 5000 |
| `drift.drift_yaw_vel_damp` | float | 4 | 0x58 | 0.01..0.05 | 0.02 |
| `drift.overdrift_yaw_vel_damp` | float | 4 | 0x5C | 0..1 | 0.03 |
| `drift.exit_drift_yaw_vel_damp` | float | 4 | 0x60 | 0.2..0.8 | 0.5 |
| `drift.velocity_rotation_*` (4) | float | 4 | 0x64-0x70 | 0..100 | 80 / 0.2 / 40 / 15 |
| `drift.counter_steer_rot_factor` | float | 4 | 0x74 | 0..0.6 | 0 |
| `drift.steering_sensitivity` | float | 4 | 0x78 | 0.5..4 | 4 |
| `drift.min_speed_to_drift_kmph` | float | 4 | 0x7C | 0..60 | 10 |
| `drift.keep_velocity_strength` | float | 4 | 0x80 | 0..1.5 | 1 |
| `arcade.turbo_jump.f_multiplier` | float | 4 | 0xC4 | 12..15 | 15 |
| `arcade.turbo_jump.r_multiplier` | float | 4 | 0xC8 | 12..15 | 12 |
| `arcade.turbo_jump.punch_delay_time` | float | 4 | 0xCC | 0.1 | 0.1 |
| `arcade.turbo_jump.punch_speed_kph` | float | 4 | 0xD0 | 50 | 50 |
| `arcade.turbo_jump.top_speed_kph` | float | 4 | 0xD4 | 200 | 200 |
| `arcade.turbo_jump.top_speed_jump_multiplier` | float | 4 | 0xD8 | 2 | 2 |

`decoded` — the base `LandGlobal` root shipped by the donor
(`v0300_car_kensington_sportsmuscle_land_global.vmodc`, 192 B) carries **no** torque, air or takeoff
member beyond `front_wheels.arcade_drag_multiplier` (0x3C) / `rear_wheels…` (0x5C); the air/torque
vocabulary lives in the 145 `CustomLandGlobal` modules, which the donor does not have.

### 2.2 `RigidBody` — `v0012_car_autostraad_atv_rigid_body.vmodc`, 92 B

| member | type | offset | role |
|---|---|---:|---|
| `unit_inertia_yaw` | float | **0x14** | yaw inertia (what a torque acts on) |
| `unit_inertia_pitch` | float | **0x18** | pitch inertia |
| `unit_inertia_roll` | float | **0x1C** | roll inertia |
| `angular_damping` | float | **0x24** | angular damping |
| `max_angular_velocity` | float | **0x28** | angular clamp |
| `center_of_mass` | IA[float] | 0x04 | where a force applies |
| `driver_center_of_mass` | IA[float] | 0x38 | driver CM |

`derived` — BmAK's 8000 is an "engine torque gain" (`MODES.md` purpose column) acting on the sim's
inertia. JC3's land inertia is a float per axis, so the pair (torque 8000, `unit_inertia_yaw`) is the
same physical shape; whether the units agree is `UNKNOWN` (no JC3 unit is named).

---

## 3. Candidate 1 — the drift yaw-torque block (the only yaw authority on a land module)

**Member path / type / offset:** `CustomLandGlobal.drift.max_drift_torque`, float, 0x48;
`…constant_drift_torque` 0x44; `…counter_steer_torque` 0x4C. All n=145.
**BmAK number it would carry:** `AirControlYawTorqueFactorMax` **8000** — inside the fleet range this
member already spans (0..35000, median 12000), so the value is not an extrapolation.
**Verdict:** the fleet's only yaw-torque member on a land vehicle is `drift.*`
(`Research/JC3Grab/DRIVE_CARRIERS.md` C1 already calls it "the fleet's only steering-through-torque
carrier"). It is gated on drift state, not on ground contact per se — but **no file says it applies
while airborne** (`UNKNOWN`). If it does, T-AC1 is a tune (8000) plus a state condition.

---

## 4. Candidate 2 — aerodynamic surfaces (yaw/pitch/roll authority from air itself)

**Member path / type / offset:** `AerodynamicSurface.turn_steering_factor` float **0x38**,
`…pitch_steering_factor` **0x3C**, `…roll_steering_factor` **0x40**, `…lift_coefficient` 0x58,
`…air_density` 0x44, `…center_point` IA[float] 0x20 — type size 96 B, decoded in
`v4500_plane_solar_smallfloatprop_aerodynamics.vmodc`.
**Fleet:** n=77 rows, **all three steering factors 0 across the fleet** (`VOCABULARY.md` lines 22-24;
`card-T-10.md` A6). They are non-zero nowhere, so a car would be the first.
**BmAK number it would carry:** `AirControlYawTorqueFactorMax` 8000 → `turn_steering_factor`;
`AirControlPitchTorqueFactorMax` → `pitch_steering_factor`. `AirControlTurnTorque` (0x17C) has no
counterpart at all.
**Verdict:** this is the only member whose *name* is literally "steering by aerodynamic surface", and
it is the physically right mechanism for a car in the air. Blocked by: no land vehicle in the fleet
ships the module, and every shipped value is 0. `UNKNOWN`: whether a `CCar` module set accepts an
`AerodynamicSurface` array (no car ships one) and whether the engine evaluates it airborne.

---

## 5. Candidate 3 — fins (`effective_in_air`)

**Member path / type / offset:** `Fins.fins` `IA[Fin]` **0xB0**, `Fins.number_of_fins` uint8 0x218,
`Fins.max_steering_vs_speed_ms` Spline5 0x50 (`v1400_boat_mugello_spyspeedboat_fins.vmodc`, type size
544 B); `Fin.effective_in_air` uint8 **0 in 200/200** rows (`VOCABULARY.md` line 625).
**BmAK number:** `AirControlYawTorqueFactorMax` 8000 would have to reach a per-fin steering parameter;
no member in `Fin` carries a torque or a yaw factor (`UNKNOWN` offset for the element — the element
type is inside the `IA[Fin]` stride, not dumped as a named member here).
**Verdict:** `effective_in_air` is a switch that does exactly what T-AC1 needs — a control surface that
works only off the ground — and the fleet sets it **0 on every row**, i.e. the capability exists and
is switched off. Whether the switch is honest (a real airborne gate) or a leftover is `UNKNOWN`.

---

## 6. Candidate 4 — `DriverLean` (land self-righting, and T-SR1's refuted premise)

**Member path / type:** `DriverLean.righting_torque` float; `…leaning_torque` float;
`…drift_leaning_torque` float; `…max_lean_angle_deg` float. **Offset: UNKNOWN in this report** — the
type is not declared by any of the 408 standalone `*_vmodc` vehicle modules (a scan of every type
dictionary found no `DriverLean`), so it lives in an `.ee`-embedded module the reader was not pointed
at here.
**Fleet:** `righting_torque` 1500..4000 (median 3000, n=23); `leaning_torque` 2000..8000 (median 5000).
**Who carries it:** `decoded` by `card-T-10.md` A4 (re-run over the 232 caches): **18 motorcycles +
5 jet-skis/amphibious quads, 0 aircraft.** T-SR1's ledger `why` says "only in `DriverLean` on 23
aircraft and the donor has none - no land carrier": the n=23 is right, **"aircraft" is wrong**, and the
row's whole reason is built on that word.
**BmAK number it would carry:** `JumpRampRightingTorque` **2000** and `JumpNoRampRightingTorque`
**2000** are inside the member's shipped range (1500..4000) — the Batmobile's own number already
exists on JC3 land vehicles.
**Verdict:** T-SR1 **cannot stay `out`**. It becomes `blocked`/UNKNOWN on one question: whether a
`CCar` module set accepts `DriverLean` (no car ships it; 23 two-wheelers and jet-skis do). BmAK's
`StayUprightStiffness/Damping/RollResistAngle/PitchResistAngle` have no named counterparts in the 16
`DriverLean` members — the block has lean angle, not resist angles (`UNKNOWN`).

---

## 7. Candidate 5 — the Havok stabilizer atom (the structural StayUpright)

**Member path / type / offset:** `hkpLimitedHingeConstraintData` → atom type **23**
`TYPE_SETUP_STABILIZATION`, 16 B at **+0x0B0** of the object; hinge angular limit min/max at
**+0x0FC / +0x100** (radians). `decoded`, 419/419 hinges and 71/71 ragdolls carry the atom
(`Research/JC3Grab/PHYSICS_LIMITS_REVIEW.md` lines 45-63; exe enum checked, so 23 is the 2014
`SETUP_STABILIZATION`, not the 2009 soft-contact modifier).
**BmAK number it would carry:** the `StayUprightConstraintSetup` object reference (`RB_StayUprightSetup`,
0x6E4) and `StayUprightConstraintInstance` (0x6EC); the numeric targets would be
`StayUprightStiffness/Damping` (no JC3 member name, `UNKNOWN`) — the atom's own floats are not named.
**Verdict:** this is the closest thing to BmAK's `StayUprightConstraintSetup` that exists anywhere in
JC3: a *stabilization constraint atom* is already inside every vehicle's hinge data. Whether a hinge
object can be attached to the car body rather than a door is `UNKNOWN` and would be a `.physicsc`
writer, not a module tune.

---

## 8. Candidates that were checked and do not carry it

| candidate | member / evidence (offset) | why not |
|---|---|---|
| gravity multipliers | `CustomLandGlobal.gravity_multiplier_in_air_up` 0x10, `…down` 0x14 (n=145, donor 1/1) | scale gravity, not torque; they change how long the car is airborne, not whether it can turn |
| takeoff pitch damping | `CustomLandGlobal.takeoff_pitch_damping` 0x18 (donor 0.5) | a *damping* of pitch at takeoff; it suppresses rotation, it cannot create it |
| turbo jump | `CustomLandGlobal.arcade.turbo_jump.f/r_multiplier` 0xC4/0xC8, `up_multiplier` (35-row vocab) | a fixed-axis translation punch (`DRIVE_CARRIERS.md` C7); no torque member in `TurboJump` |
| rig inertia | `RigidBody.unit_inertia_yaw` 0x14, `angular_damping` 0x24, `max_angular_velocity` 0x28 | the target a torque acts on, and a clamp; not authority |
| helicopter air steering | `HelicopterSteering.air_steering.max_steering_angle`, `pitch_return`, `roll_return`, `YawAxisTiming.*` (n=23; offsets `UNKNOWN`, module embedded in the helicopter `.ee`) and `HelicopterModel.yaw_input_power` 0x10 / `yaw_p/i/d` 0xE8/0xEC/0xF0 / `yaw_max_amplitude` 0xF4 | a complete 3-axis airborne authority — but on `CAirPlane`/helicopter chassis only; 0 land builds carry `HelicopterSteering` |
| `LandSteering` | `max_speed_t_to_full_steer_s` 0x0C, `steer_angle_max_speed_deg` 0x1C, `steer_input_power_pc` 0x2C (n=2 standalone, inner-`.ee` on the rest) | steers the front wheels; needs ground contact by construction |
| `CForcePulse` | 307 pulses, 31 members; `SettingsFile` → 23 ftune; `world` transform; 14 unowned | an explosion blast. A pulse placed off the COM would produce torque, but the only decoded trigger is an explosion (`FORCEPULSE.md` §1, `FORCEPULSE.md:181` "collision 0 of 23"), and the trigger for the 14 unowned pulses is `UNKNOWN` |
| `VehicleParts.rotating_parts` | `A[RotatingPart]` 0x30 (116 builds) | animates a part (radar, wheel); writes no body torque |
| explicit `AirControl` name | `grep -i "air_control\|yaw_torque" VOCABULARY.md` = 0 rows; `upright`/`stayupright` = 0 rows | the exact names are absent — the row's negative was right, its conclusion was not |
| script layer | entity graphs: `CGraphScriptGameObject` on 13 builds; exit graphs 0 of 4,832 carry a velocity/impulse/force member (`EJECT.md` §1); Rebel Drop items are spawn records with no physics fields (`REBELDROP.md` §2) | nothing in the decoded script/entity layer applies a rotation |
| `CInteraction` / graph conditions | `ParentIsUpRightCondition` (`ENTITIES.md`, `EJECT.md`) | a condition, not a torque |

---

## 9. End statement

### Which candidate reproduces BmAK air control?

**None is proven to.** By mechanism, the ranking is:

1. `CustomLandGlobal.drift.*` (torque 0x48, n=145) — the only **yaw torque on a land vehicle**;
   BmAK's 8000 fits inside its shipped 0..35000, and it is the same class of member. Missing piece:
   proof that it is evaluated with no ground contact.
2. `AerodynamicSurface.turn_steering_factor` 0x38 / `pitch_steering_factor` 0x3C — the only **air
   authority** member that is not helicopter-specific; every shipped value is 0 and no car ships the
   module. Missing piece: a car-bound `AerodynamicSurface` array and an airborne evaluation.
3. `Fins.fins[].effective_in_air` 0xB0/inside the element — the only **airborne-only switch**;
   0/200 rows on. Missing piece: a fin on a car, and a steering input mapped to it.

For T-SR1 the answer is stronger: **`DriverLean.righting_torque` is a land-vehicle self-righting
torque on 18 bikes + 5 boats**, value range 1500..4000 contains BmAK's 2000, and the Havok
`TYPE_SETUP_STABILIZATION` atom at +0x0B0 is the constraint-layer equivalent of
`StayUprightConstraintSetup`. The row's `out` is not supported by its own evidence.

### What is still UNKNOWN

1. **Whether `drift.*` torque applies airborne.** No file states the gate; a probe (drive off a ramp,
   hold steer) would settle it — test ban.
2. **Whether a `CCar` module set accepts `AerodynamicSurface`, `Fins` or `DriverLean`.** 0 cars ship
   any of the three; nothing decoded says the module table is closed.
3. **The offsets of `DriverLean` and `HelicopterSteering`.** They are not declared in any standalone
   `*_vmodc` (both live in `.ee`-embedded modules); a decode of those inner files would give them.
4. **The numeric meaning of `AirControlYawTorqueFactorMax` 8000** vs JC3's torque units — no JC3 unit
   is named for `max_drift_torque`.
5. **Whether the `TYPE_SETUP_STABILIZATION` atom can be instantiated on a car body** instead of a door
   hinge, and with what stiffness/damping.
6. **The six `AirControl*` values other than 8000, and all four `StayUpright*` values** — not
   serialised in any BmAK archetype (`MODES.md` "not serialised" list), so the target numbers for
   interpolation time, time-in-air, resist angles and stiffness do not exist in bytes.

### The exact missing capability, if no candidate does

> A JC3 land-vehicle module member that applies **yaw and pitch torque as a function of steering input
> while the vehicle has no ground contact**, with a start/stop window (`AirControlTimeInAir` 1.2 s,
> `AirControlInterpTime`) and a min/max factor pair — i.e. a per-frame angular impulse on a `CCar`
> body gated on `airborne` state. The fleet's three nearest mechanisms each lack exactly one leg:
> `drift.*` has the torque but no airborne gate; `AerodynamicSurface.*` has the air and the input but
> no car and 0 values; `Fins.*` has the airborne switch but 0 values and no car. That gap is a
> **new capability card**, not a tuning row — and it should be filed as T-AC1b, with T-SR1 moved to
> `blocked` on `DriverLean` rather than `out`.

`COMPROMISES`: none proposed. No value was tuned and no row was edited by this brief.

---

## 10. Files and commands

**Written:** `tmp/freebuff/reports/carrier-air-control.md` (this file). No other file created or
edited.

**Commands run (verbatim), with their relevant output:**

```
$ grep -n "T-AC1\|T-SR1" Working/Translation/T_ROWS.jsonl
102:{"id":"T-AC1", … "dispo":"out","why":"stays `out`, re-checked as the card asks: `gravity_multiplier_*` and `takeoff_pitch_damping` do exist (145 land vehicles; donor 1/1/1 and 0.5) but neither is a yaw torque - no `air_control`/`yaw_torque` member exists in `Research/JC3Grab/VOCABULARY.md`","edits":0}
104:{"id":"T-SR1", … "dispo":"out","why":"stays `out`: `righting_torque` exists but only in `DriverLean` on 23 aircraft and the donor has none - no land carrier (`Research/JC3Grab/VOCABULARY.md`, G2X HDL-6)","edits":0}

$ grep -rn "AirControl" Research/BatmobileGrab/*.md
Research/BatmobileGrab/MODES.md:113:| `AirControlYawTorqueFactorMax` | 0x4a8 | `float` | engine torque gain | 8000 | 8000 | 8000 | 8000 | yes |
Research/BatmobileGrab/MODES.md:121:Not serialised in any shipped archetype (23): … `AirControlPitchTorqueFactorMax` `AirControlYawTorqueFactorMin` `AirControlPitchTorqueFactorMin` `AirControlInterpTime` `AirControlTimeInAir` …
Research/BatmobileGrab/FOOTAGE.md:168:| F-6 | … **measured: 1.212 s mean** across three ramp jumps …

$ grep -rn "JumpRampRightingTorque\|JumpNoRampRightingTorque\|StayUpright" Research/BatmobileGrab/*.md
Research/BatmobileGrab/MECHANICS_NAMES.md:39:| 76 | `0x1A64` | 2000 | `JumpRampRightingTorque` | FloatProperty | `RVehicleBatmobileBase` |
Research/BatmobileGrab/MECHANICS_NAMES.md:40:| 77 | `0x1A68` | 2000 | `JumpNoRampRightingTorque` | FloatProperty | `RVehicleBatmobileBase` |
Research/BatmobileGrab/MODES.md:192:| `StayUprightConstraintSetup` | 0x6e4 | `RB_StayUprightSetup` | object ref | 5106 | 5157 | 3123 | 5196 | yes |

$ cd Tools/scripts && python - <<'PY'   # jc3adf type-dictionary dump, 408 *.vmodc under jc_vehicles
… print(f'{tn}.{n} | {d["type"]} | size {d["size"]} | off 0x{d["off"]:x} | n={d["count"]}')
… (member-name regex: rotat|torque|upright|pitch|yaw|roll|air|stabil|lean|steer|flight|ballist)
vmodc rows 408
decode failures 0
CustomLandGlobal.gravity_multiplier_in_air_down | float | size 4 | off 0x14 | n=3
CustomLandGlobal.gravity_multiplier_in_air_up | float | size 4 | off 0x10 | n=3
CustomLandGlobal.takeoff_pitch_damping | float | size 4 | off 0x18 | n=3
RigidBody.unit_inertia_yaw | float | size 4 | off 0x14 | n=2
RigidBody.unit_inertia_pitch | float | size 4 | off 0x18 | n=2
RigidBody.unit_inertia_roll | float | size 4 | off 0x1c | n=2
HelicopterModel.yaw_input_power | float | size 4 | off 0x10 | n=5
HelicopterModel.yaw_p / yaw_i / yaw_d / yaw_max_amplitude | float | 4 | 0xe8 / 0xec / 0xf0 / 0xf4 | n=5
AerodynamicSurface.turn_steering_factor | float | size 4 | off 0x38 | n=(aero module, v4500_plane_solar_smallfloatprop)
AerodynamicSurface.pitch_steering_factor | float | size 4 | off 0x3c
Fins.fins | IA[Fin] | size 8 | off 0xb0  (type size 544)

$ (same reader, recursive, on v0012_car_autostraad_atv_custom_land_global.vmodc)
 root CustomLandGlobal size 256
   gravity_multiplier_grounded | float | 0xc
   gravity_multiplier_in_air_up | float | 0x10
   gravity_multiplier_in_air_down | float | 0x14
   takeoff_pitch_damping | float | 0x18
   drift.max_drift_torque | float | 0x48
   drift.constant_drift_torque | float | 0x44
   drift.counter_steer_torque | float | 0x4c
   arcade.turbo_jump.f_multiplier | float | 0xc4
   arcade.turbo_jump.r_multiplier | float | 0xc8

$ (same reader, on v0012_car_autostraad_atv_rigid_body.vmodc, 92 B)
   unit_inertia_yaw 0x14 | unit_inertia_pitch 0x18 | unit_inertia_roll 0x1c | angular_damping 0x24 | max_angular_velocity 0x28

$ grep -n "hkp\|hknp" Research/JC3Grab/PHYSICS_ROLES*.md
Research/JC3Grab/PHYSICS_LIMITS_REVIEW.md:56:| hinge | +0x0B0 | 23 | `TYPE_SETUP_STABILIZATION` | 16 B | n/a | 2014-only | 419/419 |
Research/JC3Grab/PHYSICS_LIMITS_REVIEW.md:63:| ragdoll | +0x0B0 | 23 | `TYPE_SETUP_STABILIZATION` | 16 B | n/a | 2014-only | 71/71 |

$ cd Research/BatmobileGrab && grep -rn "righting_torque" ../challenge/card-T-10.md
Research/challenge/card-T-10.md:58:| A4 | `righting_torque` is "only in `DriverLean`, n=23 **aircraft**" ⇒ no land carrier | **BROKEN** — 18 bikes + 5 boats, 0 aircraft |
Research/challenge/card-T-10.md:217:| `righting_torque` | float | 1500 .. 4000 (med 3000, n=23) |

$ grep -n "upright\|stayupright\|air_control\|yaw_torque" Research/JC3Grab/VOCABULARY.md
(no rows for air_control / yaw_torque / upright / stayupright; `air_steering.*` 18 rows, all HelicopterSteering)
```

**UNKNOWNs:** §9 lists six; each names what was tried and where the answer would be found. The two
that matter for a row edit: `drift.*`'s airborne gate (probe) and a `CCar` accepting `DriverLean`
(module-table probe).

**Revert:** delete `tmp/freebuff/reports/carrier-air-control.md`. Nothing else changed.
