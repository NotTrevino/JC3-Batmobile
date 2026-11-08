# Air control — the closest JC3 system and the build that closes it

**Rows:** T-AC1 (air yaw/pitch control, `AirControlYawTorqueFactorMax` 8000) and its companion T-SR1
(righting torque, `JumpRampRightingTorque` / `JumpNoRampRightingTorque` 2000). Both are `out` in
`Working/Translation/T_ROWS.jsonl`; `tmp/freebuff/reports/carrier-air-control.md` ranks the carriers
and states the missing capability. This note turns that statement into a build composition, because
the project rule is that **a gap is closed by the build, not reported** (`STAGES.md`).

**The choice, in one line:** carry **yaw** with the **`CustomLandGlobal.drift` block** (the report's
rank 1, and already present in the Batmobile's own module with 21 members) and **pitch** with an
**`Aerodynamics` surface array** (the report's rank 2, the only member pair with
`turn_steering_factor` *and* `pitch_steering_factor`). `DriverLean.righting_torque` is not a steering
carrier — it is the T-SR1 self-righting leg; `CForcePulse` is rejected as an explosion trigger.

This is a plan, not applied work: no module, `.epe`, receipt or ledger row was changed. Revert =
delete this file.

---

## 1. What the candidates actually are (measured for this plan)

| candidate | member(s) / evidence | yaw? | pitch? | airborne? | verdict here |
|---|---|---|---|---|---|
| **`CustomLandGlobal.drift`** | 21 members in the car's own module (below); fleet n=145; `max_drift_torque` 0..35000, `constant_drift_torque` 0..20000; `DRIVE_CARRIERS.md` C1: "the fleet's only steering-through-torque carrier" | **yes** | no pitch member | **UNKNOWN** — gated on drift state, no file says it survives ground loss | **selected: yaw** |
| **`Aerodynamics.aerodynamic_surfaces[]`** | 77 rows, all three steering factors 0 across the fleet, no car ships the type; surface members `air_density` 0..1.3, `frontal_area` 0..350, `drag_coefficient` 0..4, `lift_coefficient` 0..8, `turn/pitch/roll_steering_factor` 0..0, `center_point[]` −20..36 | **yes** (turn) | **yes** (pitch) | physical (force ∝ air density × speed²; no boolean) | **selected: pitch (+ yaw fallback)** |
| **`DriverLean.righting_torque`** | 1500..4000, n=23 = **18 bikes + 5 boats, 0 aircraft** (`Research/challenge/card-T-10.md` A4); `leaning_torque` 2000..8000 | no (lean/roll) | no (attitude, not steering) | not steering-driven | **not this row; T-SR1 leg** |
| **`CForcePulse`** | 307 pulses, 31 members; only decoded trigger is an explosion (0 of 23 tune paths are collision, `FORCEPULSE.md`); 14 unowned | one-shot impulse only | one-shot only | no | **rejected** |
| `Fins.effective_in_air` | `0` in **200/200** rows; no car; no torque member | no | no | **yes** (the only airborne switch) | not buildable without a fin + a mapping |
| `gravity_multiplier_in_air_*` / `takeoff_pitch_damping` | car module: 1.6 / 1.6 / 0.5 | no | damping only | affects air time | already tuned; not authority |

The car's shipped `land_aerodynamics` module is **not** the array carrier: it is a 5-member
`LandAerodynamics` type (`air_density` 1.29999995, `frontal_area` 6.6346669, `drag_coefficient` 0.55,
`top_speed_drag_coefficient` 2.0, `lift_coefficient` −0.3) with **no steering factor**. The pitch
leg therefore needs the plane's `Aerodynamics` type; the plan replaces the land module rather than
adding a second one (see §3).

---

## 2. The numbers the build must carry

### 2.1 BmAK side (decoded)

| row | member | value | source |
|---|---|---:|---|
| T-AC1 | `AirControlYawTorqueFactorMax` | **8000** | `MECHANICS_NAMES.md`; `MODES.md` 0x4a8, all four packages, serialised |
| T-AC1 | `AirControlPitchTorqueFactorMax` / Min, `AirControlInterpTime`, `AirControlTimeInAir`, `AirControlTurnTorque`, `Pawn.AirControl` | **no value** | `MODES.md` "not serialised in any shipped archetype" (23 fields); `FOOTAGE.md` F-6/F-7 |
| T-SR1 | `JumpRampRightingTorque` / `JumpNoRampRightingTorque` | **2000 / 2000** | `MECHANICS_NAMES.md`, `MODES.md` 0x1a64/0x1a68, serialised |
| window | mean airborne time | **1.212 s** (1.251 / 1.183 / 1.200; 37–38 frames at ~31 fps) | `FOOTAGE.md` F-6 |

F-6 is explicit that this is the airborne **window** and "nothing more": it does not show that
pitch/yaw input changes attitude. The clips' names (`air steer up/down/right`) are the only evidence
for steering, and `bUsedAirControlDuringJump` is a member name, not an observation.

### 2.2 Car side (measured from `Builds/bm-RC2`)

`custom_land_global.vmodc` (3,399 B, `CustomLandGlobal`, 21-member `Drift` block), values now carried:

| member | RC2 | note |
|---|---:|---|
| `drift.max_drift_torque` | **12000** | the yaw authority the build has today |
| `drift.constant_drift_torque` | **0** | no base torque |
| `drift.counter_steer_torque` | 16000 | counter-steer only |
| `drift.counter_steer_torque_handbrake` / `_brake` | 30000 / 15000 | handbrake/brake paths |
| `drift.drift_yaw_vel_damp` / `overdrift` / `exit` | 0.02 / 0.03 / 0.5 | damping |
| `drift.velocity_rotation_amount` / `start` / `end` / `exp` | 80 / 15 / 40 / 0.2 | slide rotation |
| `drift.steering_sensitivity` | 4.0 | input gain |
| `drift.min_speed_to_drift_kmph` | 10.0 | drift-entry gate |
| `gravity_multiplier_in_air_up` / `_down` | 1.6 / 1.6 | already raised (fleet max 2) |
| `takeoff_pitch_damping` | 0.5 | damps, cannot create pitch |

`rigid_body.vmodc`: `mass` 6000, `unit_inertia_yaw` 4.0, `unit_inertia_pitch` 2.6,
`unit_inertia_roll` 1.2, `angular_damping` 0.0, `max_angular_velocity` −1 (unclamped),
`use_calculated_inertia` 1, `center_of_mass` (0.0, 0.6, 0.65).

### 2.3 Derived values

| # | value | derivation | label |
|---|---:|---|---|
| D1 | **8000** | BmAK `AirControlYawTorqueFactorMax` carried max→max into `drift.max_drift_torque` (both are the "maximum yaw torque" of their system; 8000 is inside the member's shipped 0..35000) | decoded value, 1:1 |
| D2 | **0.667** | 8000 / 12000 = 0.667: the new yaw max is two-thirds of the build's current drift max | derived |
| D3 | **9696** | 8000 × 1.212 = 9696 (factor·s): the yaw impulse budget over the measured airborne window | derived |
| D4 | **14544** | 12000 × 1.212 = 14544 (factor·s): the current budget over the same window | derived |
| D5 | **−33.3 %** | (9696 − 14544) / 14544 = −0.333: the change the build makes to its own yaw budget | derived |
| D6 | **4000** | 8000 / 2: the mean of a linear 0→max ramp over the window; **only** an alternate for `constant_drift_torque` if Q-AC-1 shows no authority at zero slip | derived, conditional |
| D7 | **0.2286** | 8000 / 35000 = 0.2286: the BmAK factor's position in the drift-torque domain, used as the dimensionless `turn_steering_factor` / `pitch_steering_factor` because the aero members have **no shipped non-zero value** (0..0, n=77) and no unit bridge exists | derived normaliser, not a physical bridge |
| D8 | **1.538** | `unit_inertia_yaw` / `unit_inertia_pitch` = 4.0 / 2.6 = 1.538: with equal factors, pitch angular acceleration is 1.538× yaw | derived, conditional on unit inertia being the applied inertia (`use_calculated_inertia` 1) |
| D9 | **1.23–1.85** | 1.538 ± 20 % (1.538 × 0.8 = 1.230; × 1.2 = 1.846): the pitch/yaw response band, using the project's ±20 % ratio tolerance (`T10_DAMAGE.md` §0, ARM-2) | derived band |
| D10 | **0.53–0.80** | 0.667 ± 20 % (0.667 × 0.8 = 0.534; × 1.2 = 0.800): the air-yaw / ground-drift heading-change band | derived band |

**Why 8000 is not scaled by 1.212 s.** `AirControlYawTorqueFactorMax` is an engine torque **gain**
(`MODES.md` purpose column), i.e. a per-frame authority; 1.212 s is how long it is allowed to act,
not a divisor. If the factor were a one-shot impulse budget instead, the per-frame value would be
8000 / 1.212 = **6600.7** (a third reading, recorded but not shipped). The build ships the max→max
reading because it is the only one with a named unit class on both sides.

---

## 3. The build composition

New private tree (STAGES: offline, new tree): `Builds/bm-RC4-air/`, based on `Builds/bm-RC2`.
Two independent legs, each removable without touching the other.

### Leg 1 — yaw: retune the car's own `CustomLandGlobal`

**File:** `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/batmobile/v0300_car_kensington_sportsmuscle_custom_land_global.vmodc`
(already the vehicle's private copy; R7 satisfied — no shared `vehicle_common`/`lave_*` file is touched).

| member | from | to | why |
|---|---:|---:|---|
| `drift.max_drift_torque` | 12000 | **8000** | D1: BmAK yaw max carried 1:1 |
| `drift.constant_drift_torque` | 0 | **0** | keep 0 so Q-AC-1 isolates the max; 4000 (D6) is the alternate if the max alone gives no authority at zero slip |
| `drift.min_speed_to_drift_kmph` | 10 | **0** | lets the drift state exist at the ramp lip and at low air speed; declared switch (fleet 0..60, so 0 is in-domain) |
| `drift.steering_sensitivity` | 4.0 | **4.0** | unchanged; it scales the input, not the authority |
| `drift.drift_yaw_vel_damp` | 0.02 | **0.02** | unchanged; damping is what stops the spin on landing |

Write path: the module's own type dictionary is read by `jc3adf.py` (21-member `Drift`, 84 B), the
offset is resolved **by member name at build time**, never copied from the ATV module's 0x48; the
writer is the B-09 pattern (value written at its decoded offset, file size unchanged), then packed
with `eetoc.py patch` so the `.toc` record points inside the `.ee` (R8).

### Leg 2 — pitch: replace `LandAerodynamics` with an `Aerodynamics` surface array

**File:** a new private module
`editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/batmobile/batmobile_aerodynamics.vmodc`,
type `Aerodynamics` (`aerodynamic_surfaces[]`), built from the fleet's plane module
`v4500_plane_solar_smallfloatprop_aerodynamics.vmodc` (the carrier report's decoded source; its full
VFS path is resolved at build time by `jc3index`/`ENTITIES.md`).

| surface member | from (plane donor) | to | why |
|---|---:|---:|---|
| `turn_steering_factor` | 0 | **0.2286** | D7; yaw assist / fallback if the drift state dies on take-off |
| `pitch_steering_factor` | 0 | **0.2286** | D7; BmAK pitch max is unserialised, so this is a **declared symmetry switch** |
| `roll_steering_factor` | 0 | **0** | roll is T-SR1's leg, not T-AC1 |
| `air_density` | plane donor | **1.29999995** | copy the car's shipped `LandAerodynamics.air_density` |
| `frontal_area` | plane donor | **6.6346669** | copy the car's shipped value |
| `drag_coefficient` | plane donor | **0.55** | copy the car's shipped value |
| `top_speed_drag_coefficient` | plane donor | **2.0** | copy the car's shipped value |
| `lift_coefficient` | plane donor | **−0.3** | copy the car's shipped value (negative = downforce) |
| `center_point[]` | plane donor | **(0.0, 0.6, 0.65)** | the car's `rigid_body.center_of_mass`; keeps the force at the COM so no uncontrolled roll lever is added |
| `surface_normal_angles.pitch/roll/yaw_deg` | 0 / 0 / 0 | **0 / 0 / 0** | fleet 0..0; a normal offset would add a fixed moment nobody measured |
| `name` / `physics_component_name` | plane strings | **`AeroSurface` / same** | one of the four shipped strings; the empty string is the alternative if the body binding needs it |

**Entity side:** the `.epe` module entry for `…_land_aerodynamics.vmodc` is repointed to
`batmobile_aerodynamics.vmodc` (a path-hash write of the kind B-09 used for `damage` and B-18 for the
moved modules), and `@files.xml` gets the new file (B-18 pattern). This is a **swap**, not a new
module-table row: the car keeps one aerodynamics module, and the `LandAerodynamics` constants are
copied into the new surface so top speed and downforce do not silently change.

**Fallback if a `CCar` rejects the `Aerodynamics` type:** add the module alongside
`LandAerodynamics` instead of replacing it (grows the module table; B-05 proved the `.epe` graph can
grow, B-07 a module can be registered) and re-run Q-AC-2. Second fallback: revert leg 2 and carry
yaw only.

### Leg 3 — trigger (how the torque is applied while airborne)

There is **no decoded airborne boolean** and no timer member. `AirControlTimeInAir` is
unserialised on the BmAK side (`MODES.md`), and JC3 has no `air_control`/`yaw_torque` member
(`VOCABULARY.md`, 0 rows). The composition uses the two gates the carriers already have:

1. **Yaw — drift state carried through the ramp.** Enter the drift state (handbrake + steer) on the
   run-up, so the state is active at the frame the wheels leave the ground. If the sim keeps the
   state while airborne, `max_drift_torque` applies for the whole 1.212 s window. If it exits on
   ground loss, the state is gone and the yaw leg produces nothing; that is the first thing Q-AC-1
   measures, and the fallback is leg 2's `turn_steering_factor` (always evaluated).
2. **Pitch — airspeed, not a state.** The surface force scales with `air_density` × speed², so it is
   zero at rest and strongest at the ramp's exit speed. It fades as the car slows in the air, which
   is a **compromise** against BmAK: AK's `AirControlYawTorqueFactorMax` is a constant authority for
   the window, not a speed-squared law.

**Hold:** the airborne window itself — mean 1.212 s (1.183–1.251 s), ending on wheel contact. No
timer is written because none exists; the sim's own contact state is the stop condition.

**No `CForcePulse`:** its only decoded trigger is an explosion (`FORCEPULSE.md`: 0 of 23 tune paths
are collision; 14 pulses unowned), so it cannot follow a steering input. A pulse placed off the COM
would produce one impulse, not per-frame authority.

---

## 4. The measurement that confirms it (pilot card)

**Card sentence (one line, ready for `Working/Q/PILOT`):**

> **Q-AC-1** — From the F-6 ramp at the same entry speed, hold full left steer from the frame the
> wheels leave the ground; over the **1.212 s** airborne window the heading must change by
> **0.53–0.80×** the heading change the same input produces in a **1.212 s ground drift** at the same
> speed, the nose must pitch by **1.23–1.85×** the measured yaw change, and the car must touch down
> with **roll ≤ 30°** and **pitch within ±15°** of its take-off attitude.

| element | value | source |
|---|---:|---|
| window | 1.212 s | F-6 mean (1.251 / 1.183 / 1.200) |
| yaw band | 0.53–0.80× ground drift | D10: 8000/12000 = 0.667 ± 20 % |
| pitch band | 1.23–1.85× yaw change | D9: 4.0/2.6 = 1.538 ± 20 % |
| landing roll | ≤ 30° | design tolerance (a car past 30° is not wheels-down); not derived from a file |
| landing pitch | ±15° of take-off | design tolerance; not derived from a file |

**Controls and repeats**

- Same entry speed, same steer input, same 1.212 s measurement window for the ground run; the ground
  run is a handbrake drift so the same `drift` block is the comparator.
- Three jumps, as F-6; report each, pass on the mean and fail if any single jump leaves the band.
- Record with audio and the HUD off; read heading from the minimap arrow (the project's heading
  readout) and attitude from the on-screen vehicle, not by feel.
- **Pass** = all three means inside both bands and both landing tolerances. **Fail** = a leg outside
  its band; the failing leg is reverted by itself (leg 1 or leg 2), not retuned on the spot
  (STAGES: a failure becomes a fix card).

**What each failure means**

| observation | reading | action |
|---|---|---|
| air yaw ≈ 0, ground drift normal | drift state exited on take-off | keep leg 2, revert leg 1's `min_speed` to 10; open the aero-yaw fallback |
| air yaw > 0.80× ground | torque too high or damping gone | reduce `max_drift_torque` 8000 → 6600.7 (the impulse-budget reading, D-note §2.3) |
| pitch ≈ 0 | `Aerodynamics` type not evaluated, or factor too small | confirm the module loaded (Q-AC-2); raise 0.2286 in ×2 steps |
| pitch/yaw ratio far from 1.538 | `use_calculated_inertia` is using a computed inertia, not `unit_inertia_*` | record the measured ratio as the effective inertia; do not change the factor |
| car rolls on landing | `center_point` / normal angle not at the COM | confirm `center_point` = CM and `surface_normal_angles` = 0 |

Q-AC-2 (load probe) is the gate before Q-AC-1: enter the car, confirm the module is present and the
game did not reject it (`Q-AC-2` pass = car spawns and drives; the test ban lifts only when
`tmp/freebuff/APPROVED_Q.txt` exists).

---

## 5. Offline checks before any launch

| check | command | pass |
|---|---|---|
| module decodes, 21 drift members, 57 names | `python Tools/scripts/jc3adf.py info <custom_land_global>` | same type set as RC2 |
| drift value read back | `python Tools/scripts/jc3adf.py dump <module>` | `max_drift_torque 8000.0`, `constant 0.0`, `min_speed 0.0` |
| aero module decodes, one surface, 0.2286 on two factors | `python Tools/scripts/jc3adf.py dump <batmobile_aerodynamics>` | `turn = pitch = 0.2286`, `roll = 0` |
| `.epe` points at the new aero module | `bm_entity.py --check` (B-05 reader) | one module entry, hash = `hash_jenkins(path)` |
| `.toc` record internal | `eetoc.py verify` / `aafdiff` | record offset ≠ 0, size matches |
| receipt | new `receipt.json` + `install.ps1` | sha256, bytes, offset, values table |
| tamper | flip `max_drift_torque` 8000→8001, flip one aero factor, force `.toc` offset 0 | each caught and reverted |

The ledger change this implies (not made here): `T-AC1` `out` → `next` with this build as the action,
and `T-SR1` `out` → `blocked` on `DriverLean` (18 bikes + 5 boats, no car), per
`Research/challenge/card-T-10.md` A4. `T-SR1`'s 2000 / 2000 are in the member's shipped 1500..4000,
so its leg is a value problem, not a carrier problem.

---

## 6. UNKNOWNs, each with the file that would settle it

| # | unknown | why it matters | file that settles it |
|---|---|---|---|
| U1 | does `drift.*` torque apply with no ground contact? | leg 1 is inert if the drift state exits on take-off | no static file; **Q-AC-1** (test ban). Static route: the Drift consumer in `JustCause3.exe` (not decoded) |
| U2 | `AirControlPitchTorqueFactorMax`, `…Min`, `AirControlInterpTime`, `AirControlTimeInAir` | pitch target is a symmetry switch (0.2286 / 8000) until these exist; the 1.212 s is a measurement, not `AirControlTimeInAir` | `BmGame.upk` CDO `Default__RVehicleSimBatmobile` at 0x4ac / 0x4b0 / 0x4b4 / 0x4b8 / 0x4bc — `Tools/scripts/chase08_cdo.py`; if absent, the `BatmanAK.exe` store site (`chase09_native.py`) |
| U3 | does a `CCar` module set accept the `Aerodynamics` type? | leg 2 does not load if it does not | `JustCause3.exe` module-type lookup (not decoded); **Q-AC-2** load probe |
| U4 | what does `turn/pitch_steering_factor` 0.2286 mean in force units? | the aero leg's magnitude is a normaliser, not a physical bridge | `JustCause3.exe` Aerodynamics consumer (not decoded); Q-AC-1 calibrates |
| U5 | is `unit_inertia_yaw/pitch` the applied inertia when `use_calculated_inertia` = 1? | D8's 1.538 (and the 1.23–1.85 band) collapses to UNKNOWN if inertia is computed | `JustCause3.exe` RigidBody consumer (not decoded); Q-AC-1 measures the effective ratio |
| U6 | are `constant_drift_torque` and `max_drift_torque` additive or a base/cap pair? | D6's 4000 alternate would double torque if additive | `JustCause3.exe` Drift consumer (not decoded) |
| U7 | what does `center_point` apply to — force origin or a visual anchor? | an off-COM point adds roll the plan does not want | `JustCause3.exe` Aerodynamics consumer (not decoded); Q-AC-1 landing roll |
| U8 | does the plane's `Aerodynamics` module carry module-level members beyond the 77-row vocabulary (the `drag_c_vs_attack_angle` spline)? | a surface cloned without them may fail to load | the donor module itself: `v4500_plane_solar_smallfloatprop_aerodynamics.vmodc`, read with `jc3adf.py info` / `dump` at build time |
| U9 | is `Fins.effective_in_air` a real airborne gate (0/200)? | it is the only possible boolean and would replace U1 | a fin on a `CCar` + the `Fins` consumer in `JustCause3.exe`; not this build |

---

## 7. Sources

- `tmp/freebuff/reports/carrier-air-control.md` — candidate ranking, offsets, the exact missing
  capability, §9 UNKNOWNs.
- `Research/BatmobileGrab/MECHANICS_NAMES.md`, `MODES.md` — 8000 / 2000 and the unserialised list.
- `Research/BatmobileGrab/FOOTAGE.md` F-6 — 1.212 s mean (1.251 / 1.183 / 1.200).
- `Research/JC3Grab/VOCABULARY.md` — `Aerodynamics` surface ranges (all steering factors 0..0),
  `DriverLean` (23 rows), `drift` block.
- `Research/JC3Grab/DRIVE_CARRIERS.md` C1 — drift is the fleet's only steering-through-torque carrier.
- `Research/challenge/card-T-10.md` A4 — `DriverLean` = 18 bikes + 5 boats, 0 aircraft.
- `Research/JC3Grab/FORCEPULSE.md` — explosion-only trigger.
- `Builds/bm-RC2` modules (dumped for this plan): `custom_land_global` (drift 12000, constant 0,
  min speed 10, gravity 1.6/1.6), `rigid_body` (mass 6000, inertia 4.0 / 2.6 / 1.2,
  `use_calculated_inertia` 1), `land_aerodynamics` (5 members, no steering factors).
- `Research/specs/B-07.md`, `B-09` receipt, `GRAB_BACKLOG.md:1663` — module registration and
  path-hash write precedents.
- `STAGES.md` — a gap is closed by the build; compose systems where the closest one is short.
