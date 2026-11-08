# T-1 — the translation table (draft 1, proposal only)

**Status:** carried by **test-085** (T-5, `T5_BUILD.md`). The 35 numeric values over 16 rows are in
the live `.ee` and were read back through its `.toc` — 35/35 equal. Two further T-1 rows (T-B3,
T-ST5; 3 values) are queued for the next build, together with T-DM6 in T-2b and T-DM7 in T-3. One
driving take has since measured the launch: **0–60 in 7.4 s, 0–100 in 16.4 s over 257 m, 138 km/h
peak** (`QA1_RESULTS.md`). Braking is sampled but not stopped on tarmac (3.5–3.8 m/s²), and the
corner, kerb and lighting rows are still **unmeasured**. Every row is falsifiable, and every row
that cannot be derived says so instead of inventing a number.

**Coverage** is closed by `T3_COVERAGE.md`: all **423** decoded BmAK fields now map to a row,
machine-checked by `Tools/scripts/bmak_coverage.py --check`. The damage block is **not** a set of
defects to be tidied: the Batmobile's immunity to ramming is a declared switch (`impact_damage_factor`
0, T-DM8), panel deformation is a declared switch (`deform_scale` 0, T-DM6), and small-arms immunity
is blocked because JC3 has no member for it (T-DM9). test-087 tried to move the first toward the
fleet median, turned collision damage on, and was withdrawn — `POSTMORTEM_DAMAGE.md`.

**What changed since the last proposal:** both sides are now decoded. BmAK's simulation curves are
named (`RVehicleSimBatmobile`), and JC3's members are named with a **fleet distribution behind each
one** (`Research/JC3Grab/VOCABULARY.md`, 232 vehicles), a **class profile** (`FLEET.md`), **fitted
mass relationships** (`FITS.md`) and **geometry decoded from meshes and stations**
(`ENTITIES.md`, `PHYSICS.md`). That makes the table a measurement exercise rather than a taste
exercise.

---

## 0. How to read a row

| column | meaning |
|---|---|
| **BmAK** | the source: a named curve/field, an offset-only value, or `—` (no source exists) |
| **JC3 target** | `module.member` as named by the game |
| **transform** | `identity` · `linear` · `curve fit` · `categorical` · `class` (fleet class evidence) · `fit` (mass regression) |
| **now** | what test-083 actually ships (read from `current.json`, not from notes) |
| **proposed** | the target value for the next build |
| **conf** | `decoded` (both sides named) · `derived` (arithmetic on decoded values) · `class` (fleet evidence, no law) · `assumed` (a choice) |
| **verify** | the measurement that confirms or kills the row |

Sources: `current.json` (build 083, via `Tools/scripts/t1_current.py`), `VOCABULARY.md`,
`ENTITIES.md`, `PHYSICS.md`, `FLEET.md`, `FITS.md`, `Research/BatmobileGrab/MECHANICS.md`,
`Research/BatmobileGrab/PHYSICS.md`.

Units used by BmAK curves: UE3 velocity in **cm/s** (2000 units = 20 m/s = 72 km/h), angles in
degrees, rate in °/s. That conversion is decoded, not guessed — `SteerSpeedVsSpeedCurve` is flat at
720 across `0…3500`, i.e. 35 m/s.

---

## 1. T-0 — the donor decision (the first row of every table)

`FLEET.md` ranks 144 land vehicles by shape against the Batmobile (length 7.026, wheelbase 5.029,
track 2.416, tyre radius 0.6826):

| donor | score | L×W×H | wheelbase | track | tyre Ø | mass | what it brings | what it costs |
|---|---|---|---|---|---|---|---|---|
| **Serpente `v0300` (current)** | 0.358 (45/144) | 3.72×2.10×1.41 | 3.003 | 1.770 | 0.76 | 975 | already wired: parts, 22 lights, materials, drop/spawn, all 30 modules decoded, test history | smallest shape in the fleet that still has 4 wheels — every geometry row must be overridden |
| Urga armored transport `v0602` | **0.134** | 6.17×2.53×2.67 | 4.211 | 2.116 | 1.20 | 6,000 | the nearest shape, heavy-vehicle families (rpm, grip, inertia) | new entity wiring: parts list, lights, materials, `.epe`, drop entry |
| Capstone tank `v0201` | 0.164 | 8.19×4.67×2.34 | 4.534 | 3.054 | 1.32 | 25,000 | closest tyre size, track | tracked-vehicle modules; too heavy and too wide; no car-like steering |

**Recommendation: keep `v0300`.** Not because it is the closest shape — it is 45th — but because the
donor's shape is the one thing the project has already replaced: the body mesh, LODs, stations,
`land_global` hardpoints, physics stations and tyre size are all ours, and the remaining donor role is
*wiring* (module set, part list, lights, materials, drop entry). Switching donor re-does Phase 0 and
the drop task to buy shapes we already override. What the donor must **stop** doing is supplying
numeric families: §4–§11 re-base those on the heavy class (armored transport as the reference profile,
6000 kg, rpm 3000/4000, arcade friction 1.28, bead 0.60 m).

If that is rejected, the armored transport is the only defensible alternative — and it must be
evaluated as a *re-do*, not a swap.

---

## 2. Geometry — decoded, no judgement needed

| # | BmAK | JC3 target | transform | now | proposed | conf | verify |
|---|---|---|---|---|---|---|---|
| T-G1 | mesh-measured body 7.026 × 3.495 × 2.271 m (§70) | `land_global.base_wheel_hardpoint_positions[0..3]` | decoded | front z −2.570, rear z +2.459; x ±1.208 front / ±1.285 rear; y 0.7047 | unchanged (wheelbase 5.029, track 2.416/2.569) | decoded | station quads in the built `.ee` equal `stations.json` |
| T-G2 | tyre Ø 1.366 m (mesh) | `land_global.front/rear_wheels.radius` | decoded | 0.68275 / 0.68265 | unchanged | decoded | `rbm` wheel mesh bounds vs `radius` |
| T-G3 | tyre width 0.731 m | `…wheels.width` | decoded | 0.7319 / 0.7316 | unchanged | decoded | same |
| T-G4 | ride height: **no `ground_clearance` member exists** in `SVehicle`/`RVehicleBatmobile`; the measurable lore numbers are hub y 0.7047 front / 0.7027 rear (decoded mesh) and **underbody clearance 0.071 m** = body bbox min y 0.091 − ground 0.02 (derived, `stations.json` `body_bbox`) | `land_global.ground_clearance` | derived (bbox gap, not hub y) | 0.7037 | **next: 0.071 m** — the measured underbody gap, not the hub mean: 0.7037 = mean(0.7047, 0.7027) is the hub height and sits 0.6327 m above the 0.071 gap (9.9×), which is why C09 REFUTED the `derived` class as an assumption; 0.071 is coherent with the tyre contact (hub 0.7047 − radius 0.68275 = 0.0220 m), so a 7.1 cm body gap sits above the 2.2 cm contact; inside the shipped domain 0.05 … 1 (med 0.4, n=271, `VOCABULARY.md:859`) | derived | Q2-A6 kerb/pothole/landing: no scrape and the ride height unchanged against the 0.7037 build (`keep-audit-dimensions-wheels.md` T-G4) |
| T-G5 | — (JC3-side) | `land_global.wheels_friction_type` | categorical | **0** | **2** (heavy class: 17 of 26 vehicles over 6 t use 2; ours inherits the supercar's 0) | class | one build: does low-speed grip/behaviour change? Enum semantics unknown — treat as a probe, not tuning |

## 3. Mass and inertia — no BmAK tag (G1-1 complete), class evidence only

| # | BmAK | JC3 target | transform | now | proposed | conf | verify |
|---|---|---|---|---|---|---|---|
| T-M1 | — (**no absolute mass tag**: the chain's only mass members are neutral multipliers — `BatmobileMassRatio` 1.0, `MassScale` 1.0, `InertiaTensorMultiplier` [1, 1, 1] — so the sim scales a mass the streams never store, `CHAIN.json`) | `rigid_body.mass` | class | **4,000 kg** | **6,000 kg** (armored transport; 3–8 t p75 = 6,000 kg, `T3_FLEET.md`) | class | 0–100 km/h in QA-1 → **16.4 s / 257 m measured**; stopping distance still open |
| T-M2 | — (**no absolute inertia tag**: `InertiaTensorMultiplier` [1, 1, 1] is neutral, so the sim scales an inertia the streams never store, `CHAIN.json`) | `rigid_body.unit_inertia_yaw / pitch / roll` | class | 1.8 / 1.5 / 0.5 | **4.0 / 2.6 / 1.2** (armored transport 4.0; class median at 3–6 t is 2.48; fleet fit R²=0.28, so class not law) | class | yaw rate response in QA-1: does it spin as slowly as a 6 t vehicle should? |
| T-M3 | — (**no centre-of-mass member anywhere**, decoded: the four `RB_BodySetup` exports serialise `PreCachedPhysDataVersion`, a bool, an optional ref and `AggGeom` only — no `Mass` / `Inertia` / `InertiaTensor` tag and no tensor-shaped triple in the payloads, class multipliers neutral (`BatmobileMassRatio` 1.0, `MassScale` 1.0, `InertiaTensorMultiplier` [1, 1, 1]); the only CoM-shaped statement in the grab is geometry — body bbox centre z +0.0925 m vs wheelbase midpoint −0.05555 m = **+0.148 m rearward** — and `Batmobile.RB_StayUprightSetup` is 2 B / 0 tags) | `rigid_body.center_of_mass_bias` | class | −0.3 | **−0.3 (keep, as a declared fleet value)**: the 3–8 t median, band −2 … 0.1 over 233 vehicles (median −0.2). **No BmAK number exists** to replace it, and the derived +0.148 m candidate is **not adopted** — the member's axis convention is UNKNOWN, +0.148 is above the fleet maximum (+0.1), and −0.3 is what QA-1's handling was tuned on. Lever if a weight distribution is ever wanted: the hull mass blocks (`hknpShapeMassProperties`, CoM at `+0x10..0x17`, oracle error 0.0156 m median) and the wheel mass 75/150 = +0.063 m rearward — not the bias (`keep-audit-suspension-and-mass.md` T-M3) | class (compromise) | understeer/oversteer balance in QA-1; a re-weight must be measured, not assumed |
| T-M4 | — (**no wheel-mass member**: the chain over `SVehicleWheel` finds only `MassScale` 1.0, neutral, `CHAIN.json`) | `land_global.front/rear_wheels.mass` | class | 25 / 75 | **75 / 150** (armored transport 75; old truck 200; 25 kg is a supercar wheel on a 6 t car) | class | ride harshness over kerbs in QA-1 |

## 4. Suspension — the fleet has no law; stay inside the band

| # | BmAK | JC3 target | transform | now | proposed | conf | verify |
|---|---|---|---|---|---|---|---|
| T-S1 | BmAK's rate pair exists and is named — `BMWheelSuspensionStiffness` **3000**, `BMWheelSuspensionDamping` **300** (archetype over all four cars, `CHAIN.json`) — but has **no unit bridge** to `strength`; that is T-S6's blocked row, so the fleet supplies the value here | `suspension.front/rear.strength` | class | **80 / 80** | **45 / 45** (fleet median 30, band 4…80; 80 is the stiffest in the game and was set by hand) | class | bottoming on landings, pitch under braking (QA-1) |
| T-S2 | — | `suspension.*.compression / relaxation` | class | 2.5 / 5.0 | 3.0 / 5.0 (armored transport 2.5/5; old truck 2.5/5) | class | same run as T-S1 |
| T-S3 | `SVehicleWheel.SuspensionTravelUp` **30** + `SuspensionTravelDown` **40** (archetype, all four wheels; class default 10/20) → total stroke **70 cm = 0.70 m** — the same physical quantity in the same units (`CHAIN.json`; T-S6 already recorded the pair) | `suspension.*.length` | identity (chain) | 0.25 | **next**: 0.25 → **0.70** — BmAK's own total wheel travel; `length/min_length` carry one stroke (T-S6), so the bridge is cm → m with no assumption. In-domain for the 6 t+ class (0.18 … 0.75, n=26) though 3.9× its 0.18 median — BmAK-first by intent, as T-ST1 is; this car jumps and lands, and the travel is what absorbs it | derived | ride height on a known kerb + a landing: no bottoming, no clipping, stance unchanged |
| T-S4 | — (**no antiroll member in the 41-class dump**: a scan for `AntiRoll` / `Anti-Roll` / `Sway` returns camera sway only. BmAK resists roll with a **native stay-upright constraint**: `StayUprightConstraintSetup` → `RB_StayUprightSetup` is **2 B / 0 tags** in all four packages, `bStayUpright` is false in the class default, and `StayUprightRollResistAngle`, `StayUprightPitchResistAngle`, `StayUprightStiffness`, `StayUprightDamping` are declared and **serialised in no package** — 0 exe store sites for the damping) | `suspension.*.antirollbar_strength` | class | 0 | **0 (keep, and state what it is not)**: 0 is the fleet median (domain 0 … 0.8, median 0, n=167; donor 0) and it reproduces *"no shipped car uses the field"*, not BmAK's mechanism. There is **no replacement value to write** — the constraint's four numbers are absent from every package — so a roll number has to come from a measured take, never from BmAK (`keep-audit-suspension-and-mass.md` T-S4) | class (compromise) | roll angle at 80 km/h in Q-2 A3; the field is not evidence of BmAK roll |
| T-S5 | — (no offset member; the closest decoded quantities are the wheel lateral **slip gains**, and they are asymmetric: rear `LatSlipFactor` **1.6** vs front inherited (tag absent, UNKNOWN), `HandbrakeLatSlipFactor` **1.5 front / 1.1 rear**, plus `BattleModeLatSlipScale` 0.75) | `suspension.*.lateral_tire_force_offset` | — | 0.2 | **0.1 front / 0.05 rear** (replacing the symmetric 0.2): the donor's own asymmetric pair, inside the fleet band (domain 0 … 1.5, median 0.2, IQR 0.1 … 0.3; `VOCABULARY.md` l.1151/1165). Evidence for asymmetry: BmAK's rear 1.6 / handbrake 1.5 front vs 1.1 rear is the **one thing BmAK states about front-vs-rear lateral behaviour**, and the symmetric median discarded it. The slip-gain → force-offset mapping is **UNKNOWN**, so this is a decided pair, not a converted number (`keep-audit-suspension-and-mass.md` T-S5) | decoded (donor) / compromise | Q-2 A3/A4 cornering: rear breaks away first, in that order |

## 5. Grip — the row the understeer lives on

| # | BmAK | JC3 target | transform | now | proposed | conf | verify |
|---|---|---|---|---|---|---|---|
| T-R1 | — (**no friction tag anywhere**: `bmak_chain.py --grep 'Friction|Adhesion'` over the whole chain returns none, `CHAIN.json`) | `land_global.front/rear_wheels.arcade_friction_multiplier` | class | **1.0 / 1.0** | **3.0 / 3.0** (fleet median by mass class is 3.0 in every class: 3.0 at 0–1.5 t, 3.0 at 1.5–3 t, 3.0 at 3–6 t, 2.5 at 6–15 t; Serpente's 1.0 is an outlier, Mugello runs 4.2/4.7) | class | steering-hold test at 60/100 km/h: does the front stop washing out? |
| T-R2 | **three drag members exist on the sim class, no values decoded**: `RVehicleSimBatmobile.Drag` @16, `DragNoLoad` @20, `DriftDrag` @712 (FloatProperty, export 5282) — T-A2's absence proof stops at `SVehicleSimCar`, one class short of where the numbers would be | `…wheels.arcade_drag_multiplier` | — | 0.1 / 0.1 | **0.1 / 0.1 (keep until the triple is decoded)**: 0.1 is the fleet **mode** (domain 0 … 0.5, median 0.1, donor 0.1) and **one multiplier cannot carry a `Drag` / `DragNoLoad` pair**, so no replacement value is derivable — the three BmAK values are UNKNOWN and decoding them is card **T-26** (`keep-audit-suspension-and-mass.md` T-R2) | decoded (fleet) / compromise | Q-2 A2/A9 top speed and coast-down; T-26 gates any change |
| T-R3 | — (**no shape-cast member exists**: a scan for `ShapeCast` / `Shape Cast` returns 0 hits; wheel contact is **raycast** — `Batmobile.SimulationModel` (export 5282, 2328 B) drives the four raycast wheels, radius 64 cm, 30 cm up / 40 cm down front and 40 cm down rear, and the wheels serialise no `RB_BodyInstance` or wheel shape) | `…wheels.use_shape_cast` | decoded | 0 | **0 (keep — LORE-EXACT)**, with `raycast_offset` 0: the same contact model on both sides, so there is **no fit error to report** (BmAK has no number to convert; JC3 0 = raycast on all 26 6 t+ and 35 3–8 t land vehicles, and only the out-of-class 1.2 t cars set 1). Residual: `raycast_offset` 0 puts the ray's start at the hub, so the contact radius is `radius` (T-G6) | decoded | none needed; contact radius = `radius` (T-G6) |

## 6. Steering — BmAK's numbers exist, and the fleet says two of them are out of family

BmAK (`StandardSteeringSpeedCurve`, cm/s → degrees): **0 → 60°, 21.6 → 55°, 39.6 → 55°,
46.8 → 30°, 72 → 20°**. Rate: `SteerSpeedVsSpeedCurve` flat **720 °/s**.

| # | BmAK | JC3 target | transform | now | proposed | conf | verify |
|---|---|---|---|---|---|---|---|
| T-ST1 | steering angle vs speed (above) | `land_steering.steer_angle_min_speed_deg`, `…_max_speed_deg`, `min_speed_kmph`, `max_speed_kmph`, `steer_curve_falloff` | curve fit | 35° @ ≤30 km/h → 15° @ ≥296 km/h, falloff 2 | **55° @ ≤20 km/h → 20° @ ≥72 km/h, falloff 1.5** (BmAK's own decay; 55° is above the fleet's 45° max, so this row is BmAK-first by intent) | derived | lock-to-lock feel at 40/72 km/h; no "steering wheel does nothing" at speed |
| T-ST2 | 720 °/s (`SteerSpeedVsSpeedCurve`), base `SteerSpeed` 220 °/s | `land_steering.t_to_full_steer_s` | rate → time = lock / rate | 0.8 s | **next: 0.25 s** — **operator ruling 2026-11-06 item 1** (`DECISIONS_NEEDED.md`, "T-ST7: A, 0.25 s (BmAK 55 deg / 220 deg/s)"), derivation 55° / 220 °/s = **0.25 s** at BmAK's own base rate (`T_ST7B_FLOOR.md` §3); the old 0.8 s is 75 °/s, 3.4× slower than BmAK, and the 0.0833 s that the 720 °/s curve implies is **not** taken because the ruling fixes the response at 0.25 s; 0.25 s ships on 4 `LandSteering` AI twins so it is in-domain | derived | full-lock timing at standstill (T-A, `steering-st7-apply.md`); T-ST7 now owns both time members |
| T-ST3 | `SteerSpeedVsSpeedCurve` **flat 720 °/s**; the high-speed lock is T-ST1's 20° | `land_steering.max_speed_t_to_full_steer_s` | rate → time = lock / rate | 0.6 s | **next: 0.091 s** = 20° / 220 °/s — operator ruling 2026-11-06 item 1 applied to the high-speed member (T-ST7): a flat rate curve makes the high-speed time the lock angle over the same 220 °/s, so the whole rate is carried; **declared R3** — 0.091 s is below the 0.2 s fleet minimum (0.25 s is the lowest AI value, `T_ST7B_FLOOR.md`) | derived | same run as T-ST2; the two times must differ only by the lock angle (55° vs 20°) |
| T-ST4 | **no input-exponent member**: `DriftCorrectionSteerSpeed`, `SteeringSpeedReCentreMod`, `SteeringReductionFactor`, `CurrentSteeringReduction` all **1.0**, `DriftSteeringAssist` absent (`CHAIN.json`) | `land_steering.steer_input_power_pc/durango/orbis` | identity (absence proof, `T-B3` precedent) | 3 / 3 / 3 | **next: 1 / 1 / 1** — a power of 3 turns half stick into 12.5 % of the rate, which no BmAK number asks for; absence means identity is the project's rule (`T-B3` read 5.68 → 1.0), and 1.0 ships in the fleet (domain 1 … 3, n=145) | derived (absence) | stick linearity: half stick = half rate, and T-ST2's 0.25 s is then reached uniformly (`keep-audit-steering-and-drift.md` §5) |
| T-ST5 | **the members exist** — every steering-rate modifier in the chain reads neutral: `DriftCorrectionSteerSpeed` **1.0** (`RVehicleBatmobileBase`), `SteeringSpeedReCentreMod` **1.0** (`RVehicleSimCar`), `SteeringReductionFactor` / `CurrentSteeringReduction` **1.0**, and `DriftSteeringAssist` / `DriftSteeringBias` are absent → false / 0 (`bmak_chain.py`, `CHAIN.json`). The rates (`SteerSpeed` 220 °/s, `SteerSpeedVsSpeedCurve` 720 °/s flat) and the drift pair (`LatSlipFactor` 1.6, `HandbrakeLatSlipFactor` 1.5/1.1) stay in T-ST7/T-DR1 | `land_steering.countersteer_speed_factor`, `steer_in_speed_factor` | identity (chain) | 2.0 / 1.5 | **next**: 2.0 / 1.5 → **1.0 / 1.0** — BmAK corrects drift at the **base steering rate** (×1.0, no assist gain), so both JC3 rate factors translate to identity. Out of domain on both (countersteer 1.5 … 20, steer_in 1.2 … 10, n=252; land 2 … 5 / 1.5 … 2; donor 2 / 1.5) → **declared R3**: no shipped car has a neutral countersteer, but BmAK's drift correction runs unamplified, and identity is the only value the grab supports. Countersteer's bridge is name-semantic (`DriftCorrectionSteerSpeed` = drift-correction steer speed); steer-in is a kind-match on the chain's only other steering-rate modifier (`SteeringSpeedReCentreMod`, re-centre) — documented as a kind-match, not proven | decoded | **A7**: handbrake drift 40/60 km/h, then release — drift angle holds, no snap-back, countersteer catches |
| T-ST6 | rear `LatSlipFactor` **1.6** (front inherited; no `*Align*` member anywhere — the quantity, not the name, is what translates, `CHAIN.json` 12366/12424) | `land_steering.wheel_drift_aligning_strength` | reciprocal of the rear slip gain | 0.3 | **next: 0.625** = 1 / 1.6 — a rear axle whose lateral slip is scaled 1.6× needs 1/1.6 of the aligning authority to hold the same line; inside the shipped band 0.3 … 0.8 (n=19, median 0.5), so not out-of-domain; **INFERRED** bridge, falsifier: if 0.625 refuses to rotate while 0.3 rotates, the direction is inverted and **0.48 = 0.3 × 1.6** is the value | derived (reciprocal) | 60 km/h handbrake drift: angle holds and the car still rotates (T-C, a two-way discriminator inside the band) |

**Note on T-ST2 — this is the row the old proposal got wrong.** 720 °/s at a 60° lock is a full-lock
time of **0.083 s**.The fleet's fastest `t_to_full_steer_s` is **0.5 s** (median 1.8, max 10 s over 125 land vehicles); 0.083 s is six times below the fastest shipped value, so the parameter is not the same quantity — JC3's
`t_to_full` already includes its own stabilisation. Copying 0.083 s would make the car twitch, not
responsive. The build's 0.8 s is *faster than the armored transport's 2.0 s* already. Steering speed
is therefore **not** the understeer lever; T-R1 is.

## 7. Engine and transmission

BmAK `StandardTorqueVSpeedCurve` (cm/s → torque units): **0 → 200, 27 → 170, 57.6 → 150,
75.6 → 105** — a monotone fall from zero speed, i.e. a heavy-vehicle curve, not a peaky one.

| # | BmAK | JC3 target | transform | now | proposed | conf | verify |
|---|---|---|---|---|---|---|---|
| T-E1 | torque falls with speed (above) | `land_engine.min_rpm / optimal_rpm / max_rpm` | curve fit | 1000 / 5000 / 7300 | **800 / 2800 / 4500** (fleet fit: optimal_rpm = 2.105e4·m^−0.264, R²=0.52 → 2,365 rpm at 4 t, **2,120 rpm at 6 t**; armored transport 3000/4000, old truck 1200/2300) | derived | QA-1: **peak 138 km/h measured** (drag-limited; gearing would allow 240) |
| T-E2 | lore power **1200 bhp**; BmAK has **no absolute torque** (curve only, `CHAIN.json`) | `land_engine.torque_factor_at_optimal_rpm` | power → torque at the **built** rpm band | 1393.5 | **next: 2921 N·m** = 894.8 kW / (471.239 rad/s × 0.65) at `max_rpm` 4500 — the torque the lore 1200 bhp needs at T-E1's 800/2800/4500 band; the 1393.5 × 2.844 was the lore power ratio (1200/422) applied at the **donor's** 5000 rpm and delivers only **572 hp (47.7 %)** at 4500; the 0–60 in 2.7 s route gives **2513 N·m** (59,580 N / 16.19 gearing × 0.683 m); **declared R3** — above the fleet's 95th percentile (2,500); the old "1,121 at 6 t" is not in `FITS.md` (834.1 at 4 t, 1,100 for 6–15 t) | derived | 0–100 km/h and a power pull; QA-1's 16.4 s take was at 4000 kg and Cd 0.139, so it does not cover this value (`keep-audit-engine-boost-aero.md` T-E2) |
| T-E3 | curve shape (fall from peak) | `…_at_min_rpm` / `…_at_max_rpm` | linear on shape | 0.86 / 0.84 | **1.0 / 0.65** (BmAK falls 200→105 = 0.525 across the band; JC3's min/max factors are relative to optimal) | derived | same run |
| T-E4 | 0 → 75.6 km/h over the curve | `transmission.gears`, `gear_ratios`, `upshift_rpm`, `final_drive` | — | 6 gears, 7000 rpm shifts, final 5.14 | **5 gears, 4,200 rpm shifts, keep ratios and final** (armored transport 5 gears; shift point follows T-E1's max_rpm) | derived | QA-1: first knee at **67 km/h = the computed 66.8**; later shifts need an audio take |
| T-E5 | wiki 209 mph (336 km/h) with afterburner; BmAK has **no speed member** | `vehicle_misc.official_top_speed` | terminal-speed balance | 336.4 | **band 300–336 km/h, labelled `assumed`** (the 2026-10-23 sign-off covers the label, not a measured speed): `official_top_speed` stays 336.4 as the top of the band, and the drag is **not** tuned to it — `land_aerodynamics.drag_coefficient` keeps T-A2's class fit **0.55**, so the label and the aero number are two separate decisions, not one translation. At T-E2's 2921 N·m × the 0.65 wash at 4500 rpm = 894.7 kW, Cd·A = 0.55 × 6.634667 = 3.649 m² and rho 1.2, the predicted terminal is (2P/(rho·Cd·A))^(1/3) = 74.2 m/s = **267 km/h** (265 at rho 1.225), and that — not the label — is the number a take compares with. 336.4 km/h (93.44 m/s) at the same power needs Cd·A = 2P/(rho·v³) = 1.828 m², i.e. **Cd 0.276**, which is not written either. The **Cd 0.1213** this cell used to carry was reverse-engineered from the label and is **rejected / not written**: 0.1213 × 6.635 = 0.805 m² is only 394 kW at 93.44 m/s, not the 894.7 kW it cited, and the earlier "260 km/h" did not follow from its own inputs (correction 8391) | assumed | top-speed run at the airfield: it tests **reachability of a label, not fidelity to BmAK** — record the terminal and compare with 267 km/h at Cd 0.55; 300–336 falsifies the Cd 0.55 / T-E2 pair rather than passing the label (whether `official_top_speed` is a cap is UNKNOWN) — signed off 2026-10-23 |

**T-3, closed: absolute torque is not an unknown unit.** `torque_factor_at_optimal_rpm` is the same
class-scaled quantity on both sides of the table, and the fleet measures it: **142 vehicles, 12 …
50,000**, log-log fit `2.153 · mass^0.719` with **R² 0.81** on the value scale (`FITS.md`) — the
second-strongest member-to-mass relation in the fleet after frontal area. By class the medians are
**150 / 550 / 550 / 1,100 / 2,500** at 0–1.5 t / 1.5–3 / 3–6 / 6–15 / 15+ t. The fit predicts
**≈1,121** at 6,000 kg; the build's **1,393.5** is **×1.24** that and **×1.27** the heavy-class
median. That margin is the one row where the Batmobile is deliberately allowed to be above its class
— it is now a measured ratio, not an assumed absolute. The number stays.

## 8. Boost — BmAK gives a *ratio*, not a multiplier

From the curves: standard 200 at 0 m/s vs boost 260 → **×1.30**; at 21 m/s standard 105 vs boost 220 →
**×2.10**; boost then decays to 150 by 30 m/s.

| # | BmAK | JC3 target | transform | now | proposed | conf | verify |
|---|---|---|---|---|---|---|---|
| T-B1 | boost thrust: `FakeExtaSpeedAccel` 600 cu/s² = **6.00 m/s²**, capped by `BoostDuration` 2.0 s → 43.2 km/h; ratio band 1.30 … 2.10 | `custom_land_global.arcade.nitro_boost.torque_multiplier` | thrust → multiplier on the measured low-speed acceleration | **2.0** | **next: 6.3** = 1 + 6.00 / 1.13 — the built car's low-speed acceleration is **1.13 m/s²** (6,777 N / 6,000 kg, QA-1), so a multiplier that adds BmAK's 6 m/s² is 6.3×; 2.0 adds only 1.13 m/s² (18.8 %) and was the speed band's coincidence, not a torque fit; `extra_top_speed` **43.2** and `boost_blend_time` **0.2** are already faithful (43.2 km/h reproduces 1.30–2.10 between 39 and 144 km/h) and stay; inside the shipped domain 1.5 … 40 (med 2, n=145) | derived | 0–100 with and without boost: the added acceleration must read ≈6 m/s² (`keep-audit-engine-boost-aero.md` T-B1) |
| T-B2 | **the additive member exists**: `FakeExtraSpeedMax` **3500** cu, `FakeExtaSpeedAccel` **600** cu/s², `FakeExtaSpeedDecel` 2000, `BoostDuration` **2.0 s** (class default, no archetype override), `InfiniteBoost` false (`Default__RVehicleBatmobileBase` bool word 4194304: bit 29 clear; the sim's `bInfiniteBoost` has no tag → false). A 2 s burst therefore ramps to min(3500, 600 × 2.0) = **1200 cu = 43.2 km/h** on the project's cm/s convention (`CAMERA.md`: 3000 cu = 108 km/h); the 3500 ceiling (= 126 km/h) is reachable only in `BoostDurationDonut` 6 s. The torque band **2100 → 3000 cm/s** (+32.4 km/h, ×1.30 → ×2.10) stays as the lower bound (`bmak_chain.py`, `CHAIN.json`) | `arcade.nitro_boost.extra_top_speed` | min(ceiling, accel × duration) | 50.46 | **next**: 50.46 → **43.2** — min(`FakeExtraSpeedMax`, `FakeExtaSpeedAccel` × `BoostDuration`) = 1200 cu = **43.2 km/h**, inside the shipped domain 30 … 60 (n=145, med 40) and above the curve's +32.4 km/h bound: a computation from four BmAK members, replacing the staged donor 40 (a shipped value, not a translation) | derived | **A2**: airfield top-speed run, boost off then on — terminal speed rises while boosting, delta recorded |
| T-B3 | **absence now proven, and absence means identity**: `OFFSETS.json` (G1-1: 423/423 fields named) carries no `*grip*`/`*traction*` field anywhere, and `bmak_chain.py --grep 'Grip|Traction'` over `RVehicle → RVehicleBatmobileBase → RVehicleSimCar → RVehicleSimBatmobile → SVehicleSimCar` returns none; the boost members that do exist are `BoostTorqueVSpeedCurve` (torque), `BoostDuration`/`BoostCooldown`, `DriftingBoostCooldown` — none touches grip, so BmAK boost is grip-neutral (`CHAIN.json`) | `arcade.nitro_boost.grip_multiplier` | identity (absence proof) | **5.68** (build; unsourced) | **next**: 5.68 → **1.0** — the BmAK-derived value: boost changes no grip member, so the multiplier is identity. Below every shipped car (1.2 … 2, n=145; donor 2) → **declared R3**: no shipped JC3 car has a grip-neutral boost, but BmAK has no boost-grip coupling to translate, so 1.0 is the only value the grab supports. Replaces the staged donor 2.0 | derived | **A9**: 0–100 with and without boost — boost improves 0–100 and there is no grip snap on engage |
| T-B4 | **no BmAK source exists** (chain-proven: no arcade heat-boost or turbo-jump member; `HeatSteam*` is exhaust steam and `Jump*` is landing physics) | `arcade.heat_boost.*`, `arcade.nitro_boost_upgraded.grip_multiplier/extra_top_speed`, `turbo_jump*` | Serpente defaults, with the two inherited scalings derived back out | heat_boost blend 0 / extra **100.92** / grip **4.26** / torque 2; nitro_upgraded extra **100.92** / grip **4.26** | **next: the T-MD14b donor decode, per block** — the ATV donor (`land_donor`/`v0012_car_autostraad_atv`) reads `nitro_boost` grip **2** / speed **40** (already what this build ships), `nitro_boost_upgraded` grip **1.5** / speed **80**, `heat_boost` grip **1.5** / speed **80**; the §2.4 table's 1.0 / 4.26 / 4.26 and 43.2 / 100.92 / 100.92 is a **different `CustomLandGlobal` copy**, so the target module is read before it is written (`boost-selector-and-moving-parts-plans-v2.md` section 0, A-C1) — the bytes carry two scalings that are not BmAK numbers and are not in the row: grip 4.26 = 1.5 × 2.844 (the torque ratio) and extra 100.92 = 80 × 1.2615 (the 336.4/250 tier scale); with T-E2/T-B1 carrying the power ratio, scaling grip by it double-counts, and BmAK states no grip change in boost at all (`T-B3` identity); blend 0, torque 2 and turbo_jump 0.1 s / 50 km/h / top 200 stay as the donor ships them (n=145); the **battle rung** (same plan, section 1.4) writes `heat_boost` grip **1.333** = 1 / `BattleModeLatSlipScale` 0.75 and `extra_top_speed` **0.0**, because battle caps speed and never adds it | decoded (fleet) / derived (the two ratios) | boost take: no wheelspin change against the donor's own heat boost; read-back 1.5 / 80 |

## 9. Aerodynamics — the one fit the fleet actually supports

Fleet fit: `frontal_area = 0.0774 · mass^0.501`, **R² = 0.875** → **4.92 m² at 4 t**.

| # | BmAK | JC3 target | transform | now | proposed | conf | verify |
|---|---|---|---|---|---|---|---|
| T-A1 | body cross-section 3.5 × 2.27 m (mesh) | `land_aerodynamics.frontal_area` | class | 6.63 | 6.63 — inside the heavy-class band (`T3_FLEET.md`: 3–8 t IQR 4 … 6.72, median 6.5; 6 t+ median 6.95, n=144) and consistent with the body's gross cross-section 3.5 × 2.27 = 7.9 m²; the mass fit's 4.92 describes *cars of that mass*, not this body (`FITS.md`) | class | coast-down distance |
| T-A2 | — (**no aero member anywhere**: chain grep `Drag|Lift|Aero|Downforce|Area` finds only `SelfDriveUseTightArea` (self-drive nav) and `UprightLiftStrength` (upright constraint), `CHAIN.json`) | `land_aerodynamics.drag_coefficient` | class | **0.139** | **0.55** (fit at 4 t 0.57, R²=0.13 → class not law; armored transport 0.80, old truck 0.50; 0.139 is a supercar's Cd and was set by hand; **not tuned to T-E5's label** — the 0.1213 that would make 336.4 km/h reachable from 894.7 kW is rejected there, so this class fit is what the build carries and its predicted terminal is 267 km/h) | class | terminal speed with boost off |
| T-A3 | **no drag member in the BmAK chain** (grep for drag / lift / aero / downforce / area tags returns only `SelfDriveUseTightArea` and `UprightLiftStrength`) | `land_aerodynamics.top_speed_drag_coefficient` | identity (absence → 1.0) | 2.0 | **next: 1.0** — the member's consumer is UNKNOWN, and 2.0 would drop the ceiling to 161 km/h under the multiplying reading (Cd·A = 2.0 × 0.55 × 6.635 = 7.30 m²), so identity is the only value that provably changes nothing and is what an absent BmAK member translates to (`T-B3` precedent); inside the shipped domain 1 … 30 (med 2, n=306, `VOCABULARY.md:816`) at its floor | derived (absence) | top-speed run 1.0 vs 2.0: the ceiling moves, or the member is documented inert (`keep-audit-engine-boost-aero.md` T-A3) |
| T-A4 | — (no lift/downforce member either; the chain proof is T-A2's) | `land_aerodynamics.lift_coefficient` | — | −1.95 | **−0.3** (armored transport −0.3, old truck −0.1, tank 0; −1.95 is the Serpente's downforce and is the reason the car sticks at speed) | class | high-speed corner stability |

## 10. Brakes

| # | BmAK | JC3 target | transform | now | proposed | conf | verify |
|---|---|---|---|---|---|---|---|
| T-K1 | `SVehicleSimCar.MaxBrakeTorque` **300** (archetype, all four sims) exists — but the bridge is disproven by magnitude, not assumed: 4 × 300 N·m over 6,000 kg × 0.683 m = **0.29 m/s²**, against the 3.5–3.8 m/s² we measure, so the member's scale is not JC3's (`CHAIN.json`) | `brakes.front/rear.max_brake_torque` | class (bridge disproven) | 10,000 / 10,000 | **5,000 / 5,000** (class median at 3–6 t is 5,000; armored transport 2,500; tank 30,000) | class | 100–0 km/h distance → **3.5–3.8 m/s² measured**, stop still open |
| T-K2 | **no brake-lock member — now proven exhaustively**: `bmak_chain.py` over the full chain (`RVehicle → RVehicleBatmobileBase → RVehicleSimCar → RVehicleSimBatmobile → SVehicleSimCar → SVehicle`) finds `MaxBrakeTorque` 300, `EbrakeTime` 0.75, `EBrakeBrakeForce` 640000, `Handbrake*`, **`HandBrakeOffTime` 0.3 s** (handbrake release time, `Default__RVehicleSimBatmobile`), `BlockThrottleUntilReleased` (throttle, not brake) and `BrakeSpinOut*`; `--grep 'Block|Lock|Abs|Anti'` finds no wheel-lock or anti-lock member anywhere (`CHAIN.json`) | `brakes.*.min_time_to_block` | donor (absence proven) | 5 / 5 | **next**: 5 → **1 / 1** — the **donor's shipped value** (`VOCABULARY.md` donor column); the fleet median −1 reads as the unused sentinel and the land IQR is −1 … 1 (n=271). The build's 5 has no source (Batch C disproved "vanilla Serpente = 5") and the member's own semantics are still not in our record, so no BmAK member can be mapped onto it without guessing: the shipped value of this chassis is the only evidenced choice. `HandBrakeOffTime` 0.3 s is named here so a later semantics pass can use it | decoded (donor) | **A5**: braking 100 → 0 on tarmac, full stop — stop distance ≤ ~100 m (3.5–3.8 m/s²), no lock-up |
| T-K3 | none of `HandbrakeOnSpeed` 10000, `HandbrakeOffSpeed` 1.0, `HandbrakeLatSlipFactor` 1.5/1.1, `HandBrakeOffTime` 0.3 is a friction factor — but `EBrakeBrakeForce` **640,000** is a force whose **class default 160,000** makes it unit-free (`MECHANICS_NAMES.md:32`, `CLASS_DEFAULTS.md:184`) | `brakes.handbrake_friction_factor` | force ratio to the class default | 1 | **next: 4.0** = 640,000 / 160,000 — a ratio cancels Unreal's units, which is why it survives T-K1's disproof of the direct force → torque bridge (0.29 vs 3.5–3.8 m/s²); inside the shipped domain 1 … 10 (n=145) but **above the 6 t band 1 … 2.25**, so **declared R3** (`keep-audit-steering-and-drift.md` §7) | derived (ratio) | handbrake turn at 40 km/h: stop time falls monotonically with the factor and the 1.0 build is the control (T-B) |

## 11. Drift, jump and arcade blocks — JC3-native, no BmAK row

`custom_land_global.drift.*` (23 members), `arcade.turbo_jump.*`, `arcade.nitro_boost_upgraded.*` and
`water_interaction.*` describe systems BmAK does not have. They keep the Serpente's values by
decision, not by translation — except `drift.min_speed_to_drift_kmph` (10) and
`drift.max_drift_angle_deg` (45), which stay because the Batmobile does drift in Arkham Knight.

## 12. Lights — categorical, 28 BmAK entries → 22 JC3 presets

The donor's 22 `SVehicleLight` entries are in `ENTITIES.md` with `preset_id`, `diffuse`, `radius`,
`spot_angle`, `volumetric_mode`. BmAK's rig (`MECHANICS.md`): 28 entries across 4 packages, bones
`HeadLight1/2`, `BrakeLightL/R`, `LWheelLight`/`RWheelLight` (+ `_top`/`_bottom`), `BattleModeSpotLight`,
`HeadLight*` variants, `Dashboard_Light`, `BootLight`.

| # | BmAK bone/type | JC3 preset | transform | conf | verify |
|---|---|---|---|---|---|
| T-L1 | `HeadLight1/2` (VEHLT_HeadLight) | `Front_Left_Point` + `Front_Left_Volumetric` / right pair | categorical | decoded | night screenshot: two cones, volumetric visible |
| T-L2 | `HeadLight1a…2c` (LensFlare only) | same two presets, `radius` 10 (volumetric) | categorical | derived | flare visible on approach |
| T-L3 | `BrakeLightL/R` (VEHLT_TailLight) | the **5 `TailLight` rows** — JC3 has no separate brake row; `Rear_Break` is in the graph but **no module row references it** (measured, `t2_lg2.py`) | categorical | decoded | brake lights under braking |
| T-L4 | `LWheelLight`/`RWheelLight` (+top/bottom) | **closed by T-18**: no preset exists, so a custom `preset_id 0` entry per arch (G2-33 §7); `T-L13`/`T-L14` carry it | categorical | superseded | `T14_LIGHTS.md` §4 |
| T-L5 | `BattleModeSpotLight` | `Front_Secondary_Head` exists in the graph and is **unreferenced** — this rig has no secondary spot row (measured, `t2_lg2.py`) | categorical | decoded | — |
| T-L6 | `Dashboard_Light` | `Dash_Light` | decode (both named) | decoded | interior at night |
| T-L7 | `BootLight` | **corrected by T-18**: `Rear_Point` is not one of this rig's 22 objects, so the boot lamp is a custom `preset_id 0` entry (`T-L35`) | categorical | superseded | `T14_LIGHTS.md` §4 |

## 13. Parts and damage — decoded, shapes excepted

BmAK: 32 collision bodies (`PHYSICS.md`, per-bone: 8 wheels/suspension, cockpit, 2 rear doors, fins,
turret, `Root`, 18 `Object*_frag_*` debris). JC3: 40 `CPartProp` in the graph, **42 parts** in the
parts module (which now decodes: G2-7 solved, `Research/JC3Grab/PARTS.md`).

| # | BmAK | JC3 target | transform | conf | verify |
|---|---|---|---|---|---|
| T-P1 | body / doors / wheels / windows by bone name | `CPartProp.name` + `part_index` | categorical (name match) | decoded | part list in the built `.epe` |
| T-P2 | 42 damage parts (health, damage type) | `VehicleParts.parts[].damage_type` + `VehicleDamage.part_damage_types[]` | join | **decoded** — 17 damage types across the donor's 42 parts; per-type health from `VehicleDamage` (`PARTS_TABLE.jsonl`) | per-part break order in a crash test |
| T-P3 | 32 wreck bodies (boxes) + the **drivable asset 2 bodies / 3 boxes** (`COLLISION_WHERE.md`: chassis 690.305x374.536x207.500 cm at (9, 0, 106.75), chassis 679.585x345.688x103.500 cm at (0, 0, 79); weapons pod 166.177x189.365x39.800 cm at (-30.5, -0, 93.25)) | `.physicsc` shapes | existing hull slots, uniform k per hull (G2-30) | **decoded (asset, 2026-11-07)**: the drivable rigid body is `Physics.Batmobile_V3_Physics` (BmGame.upk export 158266: 2 bodies, 3 boxes, 1 constraint, reached from `Batmobile.SVehicleMesh` property offset 824) - the hull set must be those 2 bodies, not the 11 of 32 wreck boxes G2-30 could reach; the built set still carries 62 donor bodies with body 0's single hull rewritten (bm-009/bm-RC2, B-10e), so 2 shapes are missing (T-22 reopened) | `T22_REOPEN.md` (plan) + `t22_reopen.py --check` |

## 14. Where the build contradicts the fleet

These are the rows that changed since §95, and they are the reason the car feels like several
different vehicles at once:

| row | build 083 | fleet / class | verdict |
|---|---|---|---|
| mass | 4,000 kg | 6,000 kg (armored transport); median 3,000 | light for its size |
| inertia yaw | 1.8 | 2.48 median at 3–6 t, 4.0 armored | rotates like a 1 t supercar |
| suspension strength | 80 / 80 | median 30, band 4…80 | stiffest in the game |
| wheel mass | 25 / 75 | 75 / 200 | supercar unsprung mass on a 6 t car |
| arcade friction | 1.0 / 1.0 | median 3.0 in every class | **the understeer row** |
| friction type | 0 | heavy class 2 (17 of 26) | untested enum |
| rpm band | 1000 / 5000 / 7300 | fit 2,365 optimal at 6 t; armored 3000/4000 | supercar engine |
| drag coefficient | 0.139 | fit 0.57; armored 0.80 | supercar aero on a 7 m body |
| lift coefficient | −1.95 | armored −0.3, old truck −0.1 | downforce car |
| brake torque | 10,000 | class median 5,000 | double |
| nitro grip multiplier | 5.68 | 6 t median and maximum 2.0 | above the fleet |
| steering lock | 35°→15° over 30–296 km/h | BmAK 60°→20° over 0–72 | wrong *shape*, not just values |

## 15. Blocked rows and what unblocks them

| row group | blocked by | unblocks with |
|---|---|---|
| mass, inertia, suspension, friction absolute values | **G1-1 is solved (423 / 423 named), but it does not supply these**: the BmSDK-AK dump has `SVehicle.ChassisMass`, `SVehicle.MassScale`, `SVehicle.InertiaTensorMultiplier` and `SVehicleSimBase.WheelMass` / `WheelInertia`, yet no `RVehicleBatmobile*`, `RVehicleSimBatmobile` or `SVehicleWheel` stream carries a tag at those offsets, so no value reaches this table. Class/fleet evidence remains the only source | keep the class-based values T-1 already uses, or add a data-flow probe for a specific scalar if one is later needed |
| ~~damage part table (T-P2)~~ | **resolved** — G2-7 solved by `jc3adf.py` (ADF v4 read through declared offsets) | 232/232 vehicles decoded |
| collision shapes (T-P3) | the *write* side: nothing in this toolkit writes a `.physicsc` (the read side is G2-8, solved - `SHAPES.md`) | a working `.physicsc` writer, or keep the donor chassis |
| wheel-light preset (T-L4) | JC3 has no such preset | a custom `SVehicleLight` entry in our `.epe` |

## 16. Verification — one build, one measurement pass, per row family

T-1's rows are only worth anything if the next build is measured. QA-1 (the telemetry harness) is the
instrument; the measurements that falsify each family are:

| family | measurement | pass |
|---|---|---|
| T-G* | station/radius values inside the built `.ee` | equal to the table |
| T-M*, T-S*, T-R* | constant-radius cornering at 60/100 km/h, brake pitch, kerb ride | no understeer at 60 km/h; no bottoming |
| T-ST* | lock-to-lock time, steering angle at 40/72 km/h | within 5 % of the table |
| T-E*, T-B* | 0–100 km/h with/without boost, shift points, top speed | 0–100 within 15 % of the target curve |
| T-A* | coast-down from 200 km/h, terminal speed | matches the drag target |
| T-K1 | 100–0 km/h | within 10 % |
| T-L* | dusk screenshot, brake-on screenshot | lights visible and correct |

## 17. What this changes

- **The test-085 build was not a tuning build.** It carried the rows above, with `decoded`
  rows left alone, `class` rows moved to the heavy-vehicle family, and `assumed` rows marked in the
  commit message.
- **The single biggest lever is T-R1** (arcade friction 1.0 → 3.0), not torque, not steering rate.
  It is also the cheapest row to falsify.
- **Steering speed was a false lead** (T-ST2): BmAK's 720 °/s cannot be expressed in JC3's parameter,
  and our 0.8 s is already faster than every heavy vehicle in the fleet.
- **The Batmobile is one vehicle pretending to be three**: supercar engine and aero, truck mass,
  stiffest springs in the game. The table makes that explicit instead of averaging it by feel.
- **T-3 is closed too.** The only "assumed" row left in the engine family was the absolute torque;
  the fleet relates it to mass at R² 0.81 and the build's value is a stated ×1.24 margin over that
  fit, not a number nobody could check. `FITS.md` carries the fit and the class table.

## 18. First translation batch (this pass)

The row audit against the generated fleet table (`T3_FLEET.md`) found labelling and data errors, not
new taste calls:

| what | rows | change |
|---|---|---|
| the row's own transform said `class`, the confidence said `assumed` | T-M1, T-S3, T-DM1 (T-2b) | confidence → `class`; values unchanged |
| invariant in the class | T-R3, T-DM6 (T-2b) | confidence → `decoded (fleet)` |
| exact class median | T-B3, T-K3 | T-B3 **5.68 → 2.0**; T-K3 unchanged |
| 3–8 t median (the Batmobile's 6 t sits at the top of that bucket) | T-M3 | confidence → `class`; −0.3 unchanged |
| outside the class band | T-ST5 | **2.0 / 1.5 → 3.0 / 2.0** |
| overclaimed class | T-DR1 (T-3) | confidence → `assumed`; the drift block is a JC3-native choice |

T-B3 and T-ST5 are queued for the next build (3 values), with T-K2 and T-B2. The two damage rows that
used to complete this batch are gone: **T-DM6** is a declared cosmetic switch (no crumple), and
**T-DM7** was `out` all along — BmAK's impact fields are the ram *attack*, not defence. test-087
shipped them as corrections and broke the car; see `POSTMORTEM_DAMAGE.md`. The four surviving values
are class medians and nothing more, so they are staged, not built, until each has a behaviour and a
take that can fail.
