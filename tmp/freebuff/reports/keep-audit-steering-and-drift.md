# KEEP-AUDIT — steering and drift: the seven `keep` rows, re-derived from BmAK's numbers

Card: TRANSLATE (T-1 §6/§10, T-3 §1). **Audit only — no build, no edit to `T_ROWS.jsonl`, no install,
no game launch.** Classes: **decoded** (a file carries the number and a project tool reads it),
**derived** (arithmetic on decoded numbers), **INFERRED** (a stated semantic bridge with a falsifier),
**UNKNOWN**.

## 0. Change statement (AGENTS.md)

| item | value |
|---|---|
| intended change | add one report: per-row verdict + numbers + proposed replacement + the no-member list |
| file | `tmp/freebuff/reports/keep-audit-steering-and-drift.md` (this file) |
| why this file | the brief names it; every report of this wave lives under `tmp/freebuff/reports/`, and all inputs are read-only |
| reverted by | deleting this file. Nothing else was written: no `T_ROWS.jsonl` edit, no module patched, no build, no game |

---

## 1. Verdicts

**None of the seven is LORE-EXACT. Seven of seven are COMPROMISE**, and in five of them the ledger's
own justification is a family/domain argument ("out of class", "donor character") rather than a
statement about what BmAK's number is. `T-DR1` is the only row that says the word "character"; the
other six say "keep" without naming the compromise.

| row | member | build carries (verified) | BmAK number | re-derived JC3 value | verdict | delta |
|---|---|---|---|---|---|---|
| T-ST2 | `land_steering.t_to_full_steer_s` | **0.8 s** | `SteerSpeedVsSpeedCurve` **720 °/s** flat, lock **60°** (`StandardSteeringSpeedCurve` 0 → 60°) | **0.0833 s** = 60/720 | **COMPROMISE** | build is **9.6× slower** than BmAK |
| T-ST3 | `max_speed_t_to_full_steer_s` | **0.6 s** | the same curve is **flat** in speed, so the high-speed full-lock time is the same | **0.0833 s** | **COMPROMISE** | **7.2× slower** |
| T-ST4 | `steer_input_power_pc / _durango / _orbis` | **3 / 3 / 3** | no input-curve exponent exists; every steering modifier in the chain is **1.0** and `DriftSteeringAssist` is absent | **1 / 1 / 1** (identity: absence → identity, the `T-B3` precedent) | **COMPROMISE** | cubic input response vs linear |
| T-ST6 | `wheel_drift_aligning_strength` | **0.3** | rear `LatSlipFactor` **1.6** (no `*Align*` member anywhere) | **0.625** = 1/1.6 | **COMPROMISE** (bridge INFERRED) | **0.325** below the slip-derived value |
| T-K3 | `brakes.handbrake_friction_factor` | **1** | `EBrakeBrakeForce` **640,000** vs its class default **160,000** (`CLASS_DEFAULTS.md` §5) | **4.0** = 640000/160000 | **COMPROMISE** (R3: above the 6 t band 1…2.25, inside the shipped domain 1…10) | **×4** short |
| T-K4 | `brakes.*.min_time_to_block`, rear-only handbrake | **1** (bytes; the ledger says 5 — see §5) | `HandBrakeOffTime` **0.3 s**; four wheels carry `HandbrakeLatSlipFactor` (front 1.5, rear 1.1) | **0.3** (kind-match) + friction **4.0**; front-axle modulation has **no member** | **COMPROMISE** | timing wrong, one axle missing |
| T-DR1 | `custom_land_global.drift.*` | 45° / 20° / **10 km/h** / **sens 4** / 0.02, 0.03 | handbrake speed gate `HandbrakeOnSpeed` **10,000 cm/s = 360 km/h**; drift steering gain **×1.0** (no assist) | min speed **0**, sensitivity **2**; angle/entry/damping have no BmAK member | **COMPROMISE** ("for character" — the row is honest about it) | gate 10 km/h too high, sensitivity 2× too strong |

---

## 2. The BmAK numbers, decoded

| member | value | class default | source |
|---|---:|---:|---|
| `SteerSpeed` | 220 °/s | — | `CHAIN.json` (via T-ST5) |
| `SteerSpeedVsSpeedCurve` | **720 °/s, flat** | — | `CHAIN.json` (via T-ST5) |
| `StandardSteeringSpeedCurve` | 0 → 60°, 21.6 → 55°, 39.6 → 55°, 46.8 → 30°, 72 → 20° (cm/s) | — | `Working/Translation/T1_TRANSLATION.md` §6 |
| `DriftCorrectionSteerSpeed` | **1.0** | — | `CHAIN.json` (T-ST5) |
| `SteeringSpeedReCentreMod`, `SteeringReductionFactor`, `CurrentSteeringReduction` | **1.0** | — | `CHAIN.json` (T-ST5) |
| `DriftSteeringAssist` / `DriftSteeringBias` | **absent → false / 0** | — | `CHAIN.json` (T-ST5) |
| `SVehicleWheel.LatSlipFactor` | **1.6** on WheelRL/RR; **absent** (class default) on FL/FR | 1.0 | `CHAIN.json` 12366/12424; `COLLISION_WHERE.md:110-113` |
| `SVehicleWheel.HandbrakeLatSlipFactor` | **1.5** FL/FR, **1.1** RL/RR | 1.5 | `CHAIN.json` 12250-12431; `COLLISION_WHERE.md:110-113` |
| `HandbrakeOnSpeed` / `HandbrakeOffSpeed` | **10,000** / **1** cm/s | — | `MECHANICS_NAMES.md:67-68` (`RVehicleSimCar`) |
| `HandBrakeOffTime` | **0.3 s** | — | `CHAIN.json` (T-K2) |
| `EbrakeTime` | **0.75 s** | **1.0** | `MECHANICS_NAMES.md:31`; `CLASS_DEFAULTS.md:183` |
| `EBrakeBrakeForce` | **640,000** | **160,000** | `MECHANICS_NAMES.md:32`; `CLASS_DEFAULTS.md:184` |
| `DriftingBoostCooldown` | **1.5 s** | — | `MECHANICS_NAMES.md:73` (`RVehicleSimBatmobile`) |

Unit bridges used below, each labelled:

* **cm/s → km/h**: ×0.036. `10,000 cm/s = 360 km/h`; `1 cm/s = 0.036 km/h` (**derived**, the project's
  own convention — `CAMERA.md`: 3000 cu = 108 km/h).
* **°/s rate → full-lock time**: `t = lock / rate` (**derived**, kinematics).
* **force ratio → dimensionless factor**: `instance / class default` (**derived**, the only ratio that
  removes Unreal's units — the same device `T-B3` uses for absence and `T-K1` disproves the naive one).
* **slip gain → aligning strength**: `1 / LatSlipFactor` (**INFERRED** — the direction is a reading of
  the name; the falsifier is §7 T-C).

---

## 3. T-ST2 · `t_to_full_steer_s` — 0.8 s vs 0.0833 s

**BmAK's quantity is a rate, and a rate is a time when divided by the lock.** The row rejected 720 °/s
"as a rate" and then kept 0.8 s — but 0.8 s *is* a rate in disguise: `60° / 0.8 s = 75 °/s`. BmAK's
`60° / 0.0833 s = 720 °/s`. The two are the same kind of number, so the rejection ("the parameter is
not the same quantity") is the one claim in the row that the arithmetic does not support.

| quantity | value | how |
|---|---:|---|
| BmAK full-lock time at the speed curve's rate | **0.0833 s** | 60° / 720 °/s |
| BmAK full-lock time at the base rate | 0.273 s | 60° / 220 °/s |
| build | 0.8 s | `Working/Movement/batmobile_075_yaw.json` (old 1.2 → new 0.8), byte-verified in `Builds/test-091` |
| build as a rate | 75 °/s | 60 / 0.8 |

The two BmAK rates disagree by 3.27×; the one that is *speed-dependent in name* (`…VsSpeedCurve`) is
flat at 720, and the one that is a plain `SteerSpeed` is 220. The row's own note says the fleet's
fastest shipped `t_to_full_steer_s` is 0.5 s and calls 0.083 s "six times below" it — that is true and
it is a statement about the fleet, not about BmAK.

**Proposed replacement: 0.0833 s**, declared **R3** (outside every shipped vehicle: domain 0.25 … 10,
median 1.2, n=252). The gap that closes it is JC3's missing rate member: JC3 has one time, BmAK has a
speed curve, so the build buys the low-speed rate and loses the speed dependence (T-ST1's
`steer_curve_falloff` is the only thing that then shapes the response).

**Falsifier**: if the in-game lock-to-lock is still 0.8 s-worth of wheel travel at 0.0833 s (i.e. the
member is filtered and the wheel does not arrive), the member is not the rate and the row's rejection
was right. Measurable: §7 T-A.

## 4. T-ST3 · `max_speed_t_to_full_steer_s` — 0.6 s vs 0.0833 s

**BmAK's rate curve is flat in speed**, so its high-speed full-lock time equals its low-speed one. JC3
carries two times (low-speed and high-speed) to describe a curve BmAK describes with one flat number;
the exact translation of a flat curve is **both times equal to 0.0833 s**.

The row kept 0.6 s because it sits inside the land IQR (−1 … 0.8, n=125) — a domain argument, and
"inside the IQR" here includes the sentinel −1, whose median the row itself calls a sentinel. That is
not evidence about BmAK.

**Proposed replacement: 0.0833 s**, and with T-ST2 that makes the pair equal, which is the measurable
signature of BmAK's flat curve (the car's lock time must not change between 20 and 72 km/h — T-A).

## 5. T-ST4 · `steer_input_power_*` — 3 / 3 / 3 vs 1 / 1 / 1

BmAK has **no input-exponent member**: what its chain has is three steering *rate* modifiers, all
**1.0**, plus a drift assist that is absent (`CHAIN.json`, T-ST5). A power of 3 on the pad curve turns
a linear stick into a cubic one: half stick = 12.5 % of the rate, which no BmAK number asks for.

The project already has the rule for this case: `T-B3` (boost grip) reads "absence now proven, and
absence means identity" and drops 5.68 → 1.0. Applying the same rule:

**Proposed replacement: 1 / 1 / 1** (identity), **derived from the absence proof**. Fleet domain
1 … 3–4, so 1.0 is a shipped value (the low end). This also removes a hidden interaction: with a cubic
curve, T-ST2's 0.0833 s is only reached at full stick — the identity curve is what makes the rate
uniform.

## 6. T-ST6 · `wheel_drift_aligning_strength` — 0.3 vs 0.625

The row keeps 0.3 because "there is no aligning-strength counterpart". True as a name; false as a
quantity. BmAK does not have an aligning member, but it does have the thing that *does the same job*:
the rear wheels' lateral slip gain `LatSlipFactor` **1.6**. A rear axle whose lateral slip is scaled
1.6× needs **1/1.6 = 0.625** of the aligning authority to hold the same line; that is the reciprocal,
and it lands inside the shipped land band (0.3 … 0.8, n=19, median 0.5) on a real value rather than on
the donor's floor.

| quantity | value |
|---|---:|
| rear `LatSlipFactor` | 1.6 |
| reciprocal (proposed) | **0.625** |
| build | 0.3 (the donor's own, i.e. the band's floor) |
| land band | 0.3 … 0.8, median 0.5 |

**Class: INFERRED** — the reciprocal is a semantic bridge, not a decode. **Falsifier** (§7 T-C): if
0.625 makes the car refuse to rotate on the handbrake while 0.3 rotates, the direction is inverted and
the value should be `0.3 × 1.6 = 0.48` instead. Both candidates are inside the band, so the experiment
distinguishes them without leaving the domain.

## 7. T-K3 · `handbrake_friction_factor` — 1 vs 4.0

The row is right that none of `HandbrakeOnSpeed` / `HandbrakeOffSpeed` / `HandbrakeLatSlipFactor` /
`HandBrakeOffTime` is a friction factor. It is wrong that "there is nothing to translate": BmAK carries
the e-brake as a **force**, and forces are comparable *as ratios to their own class default*.

```
EBrakeBrakeForce        640,000   (instance, MECHANICS_NAMES.md:32)
class default           160,000   (CLASS_DEFAULTS.md:184)
ratio                   ×4.0
```

**Proposed replacement: 4.0** (=×4 over BmAK's class default). Declared **R3**: inside the shipped
domain (1 … 10, n=145) but above the 6 t band the row itself quotes (1 … 2.25). The bridge is a force
ratio, not a torque — `T-K1` disproved the direct force→`max_brake_torque` bridge by magnitude (0.29
vs 3.5–3.8 m/s²), and a ratio survives that disproof because it cancels the unit.

## 8. T-K4 · the handbrake block — rear-only, `min_time_to_block`, `EbrakeTime`

Three separate findings.

**(a) Rear-only is not what BmAK does.** All four wheels carry `HandbrakeLatSlipFactor`
(`COLLISION_WHERE.md:110-113`: FL 1.5, FR 1.5, RL 1.1, RR 1.1) — the handbrake changes lateral slip on
**both** axles, and the front value is the *larger* one. JC3 by contrast has `front.handbrake = 0` on
**145 of 145** builds (`DRIVE_CARRIERS.md` §6.1). So "rear-only" is a carrier limit, not a translation.

| axle | BmAK handbrake slip | JC3 member | build |
|---|---:|---|---|
| front | 1.5 | `brakes.front.handbrake` (0 on every shipped build) | 0 |
| rear | 1.1 | `brakes.rear.handbrake` (1 on every shipped build) | 1 |

**Gap**: front-axle handbrake modulation has no carrier; the closest system is the rear axle plus
`drift.counter_steer_torque_handbrake` (build 30000, fleet 0 … 100000, median 36000). Build action:
tune the rear factor to the *combined* BmAK effect (friction 4.0, §7) and let the drift block's
handbrake torque produce the rotation the front slip would have produced. Front/rear slip ratio BmAK
1.1/1.5 = **0.733** is the number that says how much of the rotation must come from the drift torque.

**(b) `min_time_to_block`.** The ledger's "now" is **5** (T-K2's row), but the shipped bytes carry **1**:

```
$ python - test-091/.../brakes.vmodc  ->  {1.0: 4, 5.0: 0, 2.0: 3, 10000.0: 0}
```

i.e. four 1.0 floats (front/rear `min_time_to_block` and `handbrake_friction_factor` among them) and no
5.0 anywhere. T-K2's proposed 1/1 is what `test-091` holds; the T-K4 cell is stale. BmAK's only
handbrake *time* is `HandBrakeOffTime` **0.3 s** (a release ramp, not a lock time) and `EbrakeTime`
**0.75 s** (a ramp to full e-brake force). The closest JC3 quantity is `min_time_to_block` (a minimum
time the brake is held) — a **kind-match at best**, so:

**Proposed**: `min_time_to_block` **0.3** (from `HandBrakeOffTime`), class INFERRED, and record that
`EbrakeTime` 0.75 s has **no** member (§9 item 1).

**(c)** `EbrakeTime` 0.75 vs its class default 1.0 (×0.75) has nothing to land on: JC3 has no e-brake
ramp. It is in the no-member list, not in the row.

## 9. T-DR1 · the drift block — "kept for character" is a compromise, and two cells can be derived

The row is the only honest one of the seven, and it is still a compromise. Two of its cells are
derivable from BmAK; the rest are JC3-native and have no BmAK counterpart at all.

| cell | build | derived from BmAK | verdict |
|---|---:|---|---|
| `drift.min_speed_to_drift_kmph` | **10** | `HandbrakeOnSpeed` 10,000 cm/s = **360 km/h**, `HandbrakeOffSpeed` 1 cm/s ≈ 0.036 km/h → the handbrake has **no effective speed gate** (360 km/h is above the car's 336 km/h top speed = 9,333 cm/s) | **COMPROMISE → propose 0** (a shipped value: 4 builds, `DRIVE_CARRIERS.md` §3.1) |
| `drift.steering_sensitivity` | **4** | `DriftCorrectionSteerSpeed` **1.0** and `DriftSteeringAssist` absent → BmAK applies **no** drift steering gain beyond the base rate; the fleet median is 2 | **COMPROMISE → propose 2** |
| `drift.max_drift_angle_deg` | 45 | no member; BmAK's limits are the 60° lock and the slip gains | COMPROMISE (no source; fleet median at 6 t is also 45 — coincidence, not evidence) |
| `drift.drift_entry_slip_angle` | 20 | no member (BmAK has no slip-angle entry) | COMPROMISE (JC3-native; fleet median 25, 6 t median 180) |
| `drift.drift_exit_slip_angle` | 2 | no member | COMPROMISE (JC3-native) |
| `drift.drift_yaw_vel_damp` / `overdrift` / `exit` | 0.02 / 0.03 / 0.5 | no member | COMPROMISE (JC3-native) |
| `drift.counter_steer_torque_handbrake` | 30000 | the only BmAK-adjacent quantity is the handbrake slip pair (§8a) | COMPROMISE (fleet median 36000) |
| `DriftingBoostCooldown` 1.5 s | — | **no member** | no-member list (§10 item 7) |

**Proposed**: `min_speed_to_drift_kmph` **0**, `steering_sensitivity` **2**. With those two the block
stops being "character": the car may start a slide from walking pace (BmAK's gate is effectively
absent) and the drift steering is unamplified (BmAK's gain is ×1.0). The remaining five cells stay
JC3-native and are labelled as such.

Byte check that the build really carries these cells (`Builds/test-091/...custom_land_global.vmodc`):
`{45.0: 3, 20.0: 2, 10.0: 2, 4.0: 1, 0.02: 2, 0.03: 1, 30000.0: 1}` — angle, entry, min speed,
sensitivity, both damps and the handbrake torque are all present as floats.

---

## 10. BmAK numbers that still have **no** JC3 member

Each row: what was tried, and the closest system (STAGES rule — never "no system").

| # | BmAK member | value | why no member | closest JC3 system | gap the build fills |
|---|---|---:|---|---|---|
| 1 | `EbrakeTime` | **0.75 s** (class 1.0) | JC3 has no ramp time for the e-brake; `min_time_to_block` is a hold, not a ramp | `brakes.*.min_time_to_block` (kind-match) | ramp must be accepted instantaneous; record the 0.75 s |
| 2 | `HandBrakeOffTime` | **0.3 s** | no release time anywhere in `Brakes`/`CustomLandGlobal` (`VOCABULARY.md` §Brakes) | `brakes.*.min_time_to_block` 0.3 (INFERRED kind-match) | release is whatever the engine does; the number is carried as the hold |
| 3 | `EBrakeBrakeForce` | **640,000** | a force; `max_brake_torque`'s bridge is disproved by magnitude (T-K1: 0.29 vs 3.5–3.8 m/s²) | force **ratio** → `handbrake_friction_factor` 4.0 (§7) | absolute force is not carried; the ratio is |
| 4 | `SVehicleWheel.LatSlipFactor` | **1.6** (rear only) | JC3's grip knobs are **per axle** (`arcade_friction_multiplier`) and there is no per-wheel or slip-gain member (`DRIVE_CARRIERS.md` §3.2) | `wheel_drift_aligning_strength` 0.625 (§6) + `rear_wheels.arcade_friction_multiplier` | per-wheel slip authority cannot be expressed; the reciprocal aligning strength stands in |
| 5 | `SVehicleWheel.HandbrakeLatSlipFactor` | **1.5 front / 1.1 rear** | per-wheel, and the **front** axle is handbraked in BmAK while JC3's `front.handbrake` is 0 on 145/145 builds | `brakes.rear.handbrake` + `drift.counter_steer_torque_handbrake` | front-axle handbrake modulation missing; ratio 0.733 must be recovered as yaw torque (§8a) |
| 6 | `HandbrakeOnSpeed` / `HandbrakeOffSpeed` | **10,000 / 1 cm/s** | no speed-gated handbrake; `drift.min_speed_to_drift_kmph` gates *drift entry*, a different event | `drift.min_speed_to_drift_kmph` 0 (§9) | the gate is effectively absent on both sides, so 0 is the exact expression |
| 7 | `DriftingBoostCooldown` | **1.5 s** | the only `*cooldown*` members in the fleet are `turbo_jump_cooldown` 5 / `_upgraded` 2 (`VOCABULARY.md:1567-1568`) — a jump cooldown, not a drift one | `arcade.nitro_boost.boost_blend_time` (0.2 s) is the nearest time in the boost chain | cooldown has no carrier; the 1.5 s is recorded, not translated |
| 8 | `SteerSpeed` **220 °/s** and `SteerSpeedVsSpeedCurve` **720 °/s** | rate | JC3 has a **time**, not a rate, and only two of them (low/high speed) | `t_to_full_steer_s` = lock/rate (§3) | the *rate* is not stored; the derived time is |
| 9 | `StandardSteeringSpeedCurve` plateau | 55° from 21.6 to 39.6 cm/s (78–143 km/h), knee to 30° at 46.8 cm/s | JC3 fits two angles + a falloff exponent; the plateau cannot be exact | `steer_angle_*_speed_deg` + `steer_curve_falloff` (T-ST1, 0.8 s build has 35°/15°/falloff 2 still) | curve shape is a fit, not a copy |
| 10 | `DriftSteeringBias` / `DriftSteeringAssist` | **0 / absent** | no bias or assist member in `LandSteering` | `countersteer_speed_factor` (build 2.0; T-ST5 proposes 1.0) | carried as the identity factor, documented as an absence proof |

---

## 11. What the build actually carries (byte-verified, not the ledger)

`Builds/test-091/.../modules/default/*.vmodc`, float-pattern census:

| module | observed | reads as |
|---|---|---|
| `land_steering` | `0.8 ×1`, `0.6 ×1`, `3.0 ×3`, `0.3 ×1`; **no** 1.2, no 0.85 | T-ST2/T-ST3/T-ST4/T-ST6 cells confirmed |
| `brakes` | `1.0 ×4`, **`5.0 ×0`**, `2.0 ×3` | friction 1 confirmed; **`min_time_to_block` is not 5** — the T-K4/T-K2 ledger cell is stale |
| `custom_land_global` | `45 ×3`, `20 ×2`, `10 ×2`, `4.0 ×1`, `0.02 ×2`, `0.03 ×1`, `30000 ×1` | T-DR1 cells confirmed |

Two corrections to the record that the audit turned up:

1. **`Working/Movement/live/` is not the build.** Its `land_steering` carries the donor's 1.2 / 0.85
   (`{1.2: 1, 0.8: 0, 0.85: 1, 0.6: 0}`) and its `custom_land_global` the donor's 45/20/10/4. Any card
   that reads `live/` as "what ships" will report donor values. The built entity is `Builds/test-091`.
2. **The ledger's brakes cell disagrees with the bytes** (5 vs 1). A ledger is only worth its
   read-back; §12 T-E makes that a check.

---

## 12. Tests that would prove each replacement

All read-back tests are offline and runnable now; anything that needs driving is gated on
`tmp/freebuff/APPROVED_Q.txt` (STAGES.md test ban).

### T-A — lock time (T-ST2, T-ST3, T-ST4)
Offline: assert `t_to_full_steer_s` and `max_speed_t_to_full_steer_s` both read **0.0833** in the built
module, and the three `steer_input_power_*` read **1.0** (module read-back through the built `.toc`,
the same route `deploy.py verify` uses).
In-game: hold full left from centre at 30 and at 90 km/h and record the time to the wheel's stop (HUD
steer channel or a front-wheel bone angle from the replay). Pass: both times equal within 1 frame and
≤3× the member (0.0833 s nominal); a 0.8 s-style arrival fails the row outright.

### T-B — handbrake force (T-K3, T-K4)
Offline: `handbrake_friction_factor` reads **4.0**, `front.handbrake` **0**, `rear.handbrake` **1**,
`min_time_to_block` **0.3**.
In-game: 40 km/h, handbrake only, measure time-to-stop and yaw rate. Prediction with factor 4 and the
drift handbrake torque 30000: stop time ≤ 1/3 of the build's current 1.0-factor stop (same mass, same
tyres), yaw rate rises. Pass: monotone in the factor, and the 1.0 build is the control.

### T-C — aligning strength direction (T-ST6)
Two builds: 0.3 (today) and 0.625. 60 km/h handbrake drift, same input script. Pass: the value for
which the drift angle **holds** (no snap-back) and the car still rotates is the right direction; if
0.625 refuses to rotate, the bridge is inverted and 0.48 (`0.3 × 1.6`) is the replacement — both inside
the 0.3 … 0.8 band, so the test is a two-way discriminator, not a directional guess.

### T-D — drift gate and sensitivity (T-DR1)
Build `min_speed_to_drift_kmph` 0 and `steering_sensitivity` 2. In-game: (i) at **5 km/h**,
handbrake + full lock — does the car rotate? (BmAK's gate is 360 km/h, so it should); (ii) at 60 km/h,
the same steer input on 2 and on 4 — the peak drift angle ratio should be ≈2 if the member is a linear
gain. Pass: (i) rotates; (ii) ratio 2 ± 0.3.

### T-E — ledger read-back (the check this audit was missing)
For every row whose "now" cell names a JC3 member, read that member's value from
`Builds/<tag>/…/*.vmodc` and compare to the cell. Pass: 7/7 equal. Today it fails **T-K4** (ledger 5,
bytes 1) — which is exactly the class of error that let "keep" stand for a year.

### T-F — no regression
`deploy.py verify` unchanged: 25/25 RBMs byte-identical, `.toc` internal set, module budget, and the
`spec_check` arms still 0 mismatches.

---

## 13. Reproduce

```bash
cd "E:/Modding/JC3-Batmobile"

# 1. the seven rows as the ledger states them
grep -E '"id":"T-(ST2|ST3|ST4|ST6|K3|K4|DR1)"' Working/Translation/T_ROWS.jsonl

# 2. the BmAK numbers
grep -n "HandbrakeOnSpeed\|HandbrakeOffSpeed\|EbrakeTime\|EBrakeBrakeForce\|DriftingBoostCooldown" \
     Research/BatmobileGrab/MECHANICS_NAMES.md | head
sed -n '180,190p' Research/BatmobileGrab/CLASS_DEFAULTS.md          # class defaults 160000 / 1.0
sed -n '108,114p' Research/BatmobileGrab/COLLISION_WHERE.md         # per-wheel slip factors
grep -n "LatSlipFactor\|HandbrakeLatSlipFactor" Research/BatmobileGrab/CHAIN.json | head

# 3. fleet bands
grep -nE "steering|drift|handbrake" Working/Translation/T3_FLEET.md | head -25

# 4. what the build really carries (byte census; T-E's instrument)
uv run python - <<'EOF'
import struct
b='Builds/test-091/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/'
def c(f,v):
    d=open(b+f,'rb').read(); return {x: d.count(struct.pack('<f',x)) for x in v}
print(c('v0300_car_kensington_sportsmuscle_land_steering.vmodc',[1.2,0.8,0.85,0.6,3.0,0.3]))
print(c('v0300_car_kensington_sportsmuscle_brakes.vmodc',[1.0,5.0,0.3,4.0]))
print(c('v0300_car_kensington_sportsmuscle_custom_land_global.vmodc',[45.0,20.0,10.0,4.0,2.0,0.0]))
EOF
```

### Evidence index

| claim | file |
|---|---|
| the seven rows, their "now" and their rationale | `Working/Translation/T_ROWS.jsonl` lines 19-23, 39, 92-93 |
| the same rows in prose + T-ST5's identity chain | `Working/Translation/T1_TRANSLATION.md` §6, §10 |
| T-K4 / T-DR1 prose | `Working/Translation/T3_COVERAGE.md:29-30` |
| BmAK handbrake/e-brake/drift values | `Research/BatmobileGrab/MECHANICS_NAMES.md:31-32,67-68,73` |
| BmAK class defaults 160,000 / 1.0 | `Research/BatmobileGrab/CLASS_DEFAULTS.md:183-184` |
| per-wheel slip factors | `Research/BatmobileGrab/COLLISION_WHERE.md:110-113`; `CHAIN.json` 12250-12431 |
| 720 °/s flat, lock 60°, modifiers 1.0 | `CHAIN.json` via `T1_TRANSLATION.md` §6 (T-ST5) |
| JC3 members, domains, donor column | `Research/JC3Grab/VOCABULARY.md` (LandSteering, CustomLandGlobal drift, Brakes) |
| fleet medians/IQRs | `Working/Translation/T3_FLEET.md` lines 29-41 |
| handbrake is rear-only on 145/145 builds | `Research/JC3Grab/DRIVE_CARRIERS.md` §6.1 |
| drift gate 0 exists (4 builds) | `Research/JC3Grab/DRIVE_CARRIERS.md` §3.1 |
| only `*cooldown*` members are turbo-jump | `Research/JC3Grab/VOCABULARY.md:1567-1568` |
| build cell values, byte-verified | `Builds/test-091/.../modules/default/*.vmodc` |
| `live/` is a donor snapshot, not the build | `Working/Movement/live/...land_steering.vmodc` (1.2 / 0.85) |
