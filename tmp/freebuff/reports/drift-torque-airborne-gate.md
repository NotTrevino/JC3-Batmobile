# Is the drift torque gated on ground contact? — the `CustomLandGlobal.drift` block decoded

Scope: the drift module's members and inputs only. T-AC1's yaw leg and the composed pair are closed in
`Working/Translation/T_ROWS.jsonl`; `tmp/freebuff/reports/air-control-closest-system-plan.md` §1 (candidate
table) and §6 (U1–U9) are cited, not redone. **Q-AC-1 is not touched** — it needs the game running.

**Verdict: NO.** No member of the 21-member `drift` block reads a ground, wheel-contact or airborne flag.
The block's only gates are **speed** (`min_speed_to_drift_kmph`) and **slip angle**
(`drift_entry_slip_angle` / `drift_exit_slip_angle`); the torque members are unconditional within those
gates. So the data contains **no airborne gate** — nothing in the module would stop `max_drift_torque`
from applying in mid-air, provided the drift state is active and the sim still evaluates the block.
Whether the native consumer *does* evaluate it airborne is U1, and stays UNKNOWN.

## 1. Every member of the drift block, and what it reads

Source: `Research/JC3Grab/VOCABULARY.md:467-487` (21 rows, fleet n=145) plus the build's own
`custom_land_global.vmodc` values from the plan §2.2. "Input" = a value the consumer reads from vehicle
state; "torque" = an authority it writes.

| # | member | fleet range (n=145) | RC2 value | kind | reads a ground/wheel contact flag? |
|---:|---|---|---:|---|---|
| 1 | `drift.max_drift_torque` | 0 .. 35000 | 12000 | **torque (cap)** | **no** |
| 2 | `drift.constant_drift_torque` | 0 .. 20000 | 0 | **torque (base)** | **no** |
| 3 | `drift.counter_steer_torque` | 0 .. 60000 | 16000 | torque | no |
| 4 | `drift.counter_steer_torque_brake` | 0 .. 45000 | 15000 | torque | no |
| 5 | `drift.counter_steer_torque_handbrake` | 0 .. 100000 | 30000 | torque | no |
| 6 | `drift.min_speed_to_drift_kmph` | 0 .. 60 | 10 | **input — speed gate** | **no** (speed, not contact) |
| 7 | `drift.drift_entry_slip_angle` | 10 .. 180 | 20 (default) | **input — slip gate** | **no** |
| 8 | `drift.drift_exit_slip_angle` | 1 .. 180 | 2 (default) | **input — slip gate** | **no** |
| 9 | `drift.max_drift_angle_deg` | 20 .. 60 | 45 | input — limit | no |
| 10 | `drift.drift_limit_spread_angle_deg` | 10 .. 15 | 15 (default) | input — limit | no |
| 11 | `drift.steering_sensitivity` | 0.5 .. 4 | 4.0 | **input — steering gain** | **no** |
| 12 | `drift.counter_steer_rot_factor` | 0 .. 0.6 | 0 (default) | input — steering sign | no |
| 13 | `drift.keep_velocity_strength` | 0 .. 1.5 | 1 (default) | input — velocity shaping | no |
| 14 | `drift.velocity_rotation_amount` | 20 .. 100 | 80 | input — velocity shaping | no |
| 15 | `drift.velocity_rotation_start_angle` | 0 .. 30 | 15 | input | no |
| 16 | `drift.velocity_rotation_end_angle` | 25 .. 65 | 40 | input | no |
| 17 | `drift.velocity_rotation_angle_exp` | 0.2 .. 8 | 0.2 | input | no |
| 18 | `drift.max_keep_velocity_acceleration_g` | 2 .. 2 | 2 | input — limit | no |
| 19 | `drift.drift_yaw_vel_damp` | 0.01 .. 0.05 | 0.02 | damping | no |
| 20 | `drift.exit_drift_yaw_vel_damp` | 0.2 .. 0.8 | 0.5 | damping | no |
| 21 | `drift.overdrift_yaw_vel_damp` | 0 .. 1 | 0.03 | damping | no |

**Count: 0 of 21 members is a ground, wheel-contact or airborne flag.** Six members are gates/inputs the
consumer reads (rows 6–12), five are torque authorities (1–5), and the rest limit, shape or damp.

## 2. The nearest air/ground members in JC3 — and why none of them is this gate

Search terms over `Research/JC3Grab/VOCABULARY.md` for `airborne|in_air|is_ground|on_ground|grounded|wheel_contact|contact|num_wheels|wheels_on` (case-insensitive):

| member | where | range | in the drift block? | a gate? |
|---|---|---|---|---|
| `gravity_multiplier_grounded` | `CustomLandGlobal` level, `VOCABULARY.md:491` | 1 .. 1.5 | **no** — module level, beside the block | no, a gravity multiplier |
| `gravity_multiplier_in_air_up` / `_down` | `VOCABULARY.md:492-493` | 1 .. 2 | **no** | no, multipliers |
| `fins[].effective_in_air` | `VOCABULARY.md:625` | **0 .. 0, n=200** (never on) | no | not usable — zero fleet-wide |
| `all_vehicles_common.high_up_in_air_height` | `:1379` | 10 | no | height threshold for a different system |
| `car_common.crash_in_air_min_vel_change_ms` | `:1388` | 5 | no | crash detection |
| `vehicle_damage.in_air_vulnerability_duration` | `:1449` | 2 | no | damage |

The module *knows* whether it is grounded — the two gravity multipliers imply a grounded/airborne state
exists at module level — but that state is **not passed to the drift block**: no drift member is a bool,
and the drift rows are all floats with physical meanings (torque, degrees, km/h, seconds⁻¹).

## 3. Path census (`Research/JC3Grab/INDEX.jsonl`, 81,952 paths)

The class census is path-level only, so it can count modules and classes but not members; the member
answers above come from the vocabulary. Counts for the terms run:

| term | matching paths | what they are |
|---|---:|---|
| `drift` | **0** | no file is named for the drift block — the members live inside `.ee`-embedded `.vmodc` modules |
| `custom_land_global` | **3** (3 unique) | the only loose module files: `v0012_car_autostraad_atv`, `v0504_car_solar_technicaljeep`, `v3502_bike_solar_modernroad` (the rest are embedded in `.ee` bundles) |
| `contact` | **23** | all dialogue/animation names (`mission_mm210_dial_gameplay_contact…`) — **0** physics or module hits |
| `grounded` | **135** | art/level names; **0** drift or module hits |
| `on_ground` | **1** | one path, not a drift module |
| `in_air` | **0** | — |
| `airborne` | **0** | — |
| `wheel_contact` | **0** | — |
| `is_ground` | **0** | — |
| `ground` (broad control) | 208 | terrain/art |
| `wheel` (broad control) | 388 | wheel meshes/parts |
| `grip` / `traction` | 100 / 167 | tire/art names |

So: **no path in the index names a contact-gated drift consumer, and no member in the drift block is a
contact input.** The zero counts for `in_air`, `airborne`, `wheel_contact` and `is_ground` are real
negatives (each term run over the full index), not term-selection artefacts — `contact` and `grounded`
do have hits, so the search was live.

## 4. What this settles for the plan, and what it does not

* **Settled (decoded absence):** the drift block has no contact gate. The plan's leg 1 therefore does not
  have to defeat a data-level "wheels must touch" test — there isn't one. Its stated risk ("gated on
  drift state, no file says it survives ground loss", plan §1) is narrowed to the **state**, not the gate.
* **Still UNKNOWN (unchanged, U1):** whether the native consumer keeps evaluating the block once the
  wheels leave the ground. The gate that matters is `drift_entry_slip_angle` 20° /
  `drift_exit_slip_angle` 2° and `min_speed_to_drift_kmph` 10: in the air, slip angle is
  velocity-vs-heading and can exceed 20° with no tire force at all, so the *inputs* to the gate remain
  satisfiable airborne — which is consistent with the torque acting, but does not prove the consumer runs.
  `JustCause3.exe`'s Drift consumer is the file that would settle it; Q-AC-1 is the measurement, and it
  is left alone here.
* **Not this brief:** whether `constant_drift_torque` and `max_drift_torque` are additive (U6), and the
  pitch leg (U3/U4).

## 5. Limits

Static read of `Research/JC3Grab/VOCABULARY.md` (the 21 drift rows and the air/ground rows),
`Research/JC3Grab/INDEX.jsonl` (path census only — it cannot show members) and
`Research/JC3Grab/DRIVE_CARRIERS.md` C1/§3.1, plus the plan's §1/§2.2/§6. The 145-build `n` and every
range are the vocabulary's own counts. No module, `.epe`, build or ledger row was written; nothing was
launched; no file outside `tmp/freebuff/reports` was touched.
