# Boost selector and moving parts — plans v2

Supersedes the contested rows of `tmp/freebuff/reports/boost-block-selector-closest-system-plan.md` (B)
and `tmp/freebuff/reports/moving-parts-behaviour-gaps-closest-system-plan.md` (M). Audit:
`tmp/freebuff/reports/audit-boost-selector-and-moving-parts-plans.md` (A): 48 claims, **38 verified,
8 overstated, 2 unsupported**. Folded in: `jet-part-bone-driver.md`, `rotor-block-gate-input.md`,
`cargo-bay-attach-rule.md`, `drift-torque-airborne-gate.md`,
`handbrake-friction-and-block-time.md`, `brake-decel-bridge-derivation.md`.

**The originals stay as they are.** Both plans and every source report are unmodified; this file is the
only write. Revert = delete it.

Labels: **decoded** = read at the cited file/line; **derived** = arithmetic over decoded inputs;
**UNKNOWN** = absent, with the file that would settle it.

---

## 0. The boost correction (A-C1) — two module copies, one table

B §1/§2 quotes a shipped-value table and calls it "as read". It is `mode-switch-carriers.md` **§2.4
(lines 112-118)** verbatim — `grip 1.0 / 4.26 / 4.26`, `extra_top_speed 43.2 / 100.92 / 100.92`
(B `:33-34`). The donor **T-MD14b** indexes (`land_donor`, `v0012_car_autostraad_atv`) decodes
**`grip 2 / — / 1.5`** and **`speed 40 / 80 / 80`**. Both tables are real; they are **different
`CustomLandGlobal` copies**, and neither plan names a vehicle.

**Consequence, stated plainly:** "Pursuit = `nitro_boost` **unchanged**" (B `:46`) is true of §2.4's copy
and **false for the donor the card was built from** — writing 15000 / 2.0 / 1.0 / 43.2 / 0.2 onto the ATV
*changes* its grip (2 → 1.0) and its top speed (40 → 43.2). v2 therefore carries the copy as a column,
not as a fact, and any build step must read the target module's own values first.

| member (`arcade.nitro_boost`, `PerformanceBoost` @156) | offset in block | §2.4 copy | **T-MD14b donor (ATV)** |
|---|---:|---:|---:|
| `torque_multiplier` | 0 | 2.0 | **2.0** |
| `grip_multiplier` | 4 | 1.0 | **2** |
| `push_force` | 8 | 15000 | (not in the audit's pair — read before writing) |
| `boost_blend_time` | 12 | 0.2 | — |
| `extra_top_speed` (km/h) | 16 | 43.2 | **40** |

Same shape for `nitro_boost_upgraded` (@176): §2.4 `4.26` / `100.92`, donor **`1.5` / `80`**; and for
`heat_boost` (@136): `push_force 0`, `blend 0` in both, but grip **1.5** and speed **80** on the donor —
so "unused duplicate" holds **only** for push/blend, which is exactly the claim B limits itself to
(A-B8).

### 0.1 The rest of the audit's corrections, applied

| # | v1 | v2 |
|---|---|---|
| C2 | `t_md14b.py --check` proves "9 blocks, offsets ascending, the 3 land blocks still present" | it asserts the hit set, that `heat_boost` exists, the donor's `extra_top_speed`, and that the **air** offsets ascend (120 < 132 < 144). Say that |
| C3 | `t11_modes.py --check` is a green gate | run here: **15 rows confirmed, exit FAIL** (`ledger T-WP4 is next, the row cites blocked`). A gate that fails must say so |
| C4 | trigger order: candidate 1 `USE_VEHICLE_MOD`, 2 Rebel Drop | invert: **Rebel Drop is ranked "closest match"**, `USE_VEHICLE_MOD` is "possible, not proven" |
| C5 | `BattleModeDrivingForceZOffset` **20 cm**, bare | **`MODES.md:103` = 20 (serialised)** vs **`DRIVE_MODES.md:77` = 10** — carry the same cross-file caveat as MaxSpeed/MaxSteering |
| C6 | P-03 "6.00 turns / 2160° in 3.90 s at 1229.51 °/s" | cannot all hold: 2160/3.90 = **553.8 °/s mean**; 1229.51 is the **peak**. State both |
| C7 | rear piston rate 106.14 for P-11 **and** P-12 | **P-11 106.14, P-12 105.82** |
| C8 | P-14/P-15 "**static**" | they carry the `Missiles_*_T` joint (`rows_with_joint: 12`); what is absent is a **behaviour**. Say "no behaviour of its own" |
| C9 | `aim_part_constraints` "85 rows in 17 of 78 modules", cited to `TURRET.md` | `TURRET.md` prints **0** rows for every turreted sample and never prints fleet totals; the totals live in **`Tools/scripts/bm_parts.py:503-504`** (`aim_note`) |
| C10 | `SteeringWheel` "8 cars + 1 sailboat" | `MOVING_PARTS.md:132` gives **20 rows / 20 parts / 9 chassis** with classes `CBoat, CCar` only — no 8+1 split. Split = **UNKNOWN** |
| C11 | P-02's −5…20° "already in the row" | the row is `joint: null`; −5…20 appears in its **verify text**, and the hinge numbers are **`JOINT_FIELDS.md` §3** medium-tank column |
| B17-B21 | see above | gates and trigger order corrected |

---

## 1. Boost selector

### 1.1 Corrected facts

| fact | value | source |
|---|---|---:|
| copies of the block group | **9 blocks**: land `CustomLandGlobal` **145** builds, air `AirGlobal` **41**, boat `BoatGlobal` **35** | T-MD14b (`--check`: blocks 9) |
| air blocks | `nitro_boost` @**120**, `_upgraded` @**132**, `heat_boost` @**144**, `AirPerformanceBoost` **12 B** (3 floats) | T-MD14b |
| land blocks | `arcade` @**136** with `heat_boost` @136, `nitro_boost` @**156**, `_upgraded` @**176**, `PerformanceBoost` **20 B**, members torque@0 grip@4 push@8 blend@12 speed@16 | T-MD14b |
| caveat kept | the `arcade`@136 / `heat_boost`@136 clash is unresolved; only a `.vmodc` re-read confirms it | T-MD14b, B-U6 |
| battle grip target | **1.333 = 1 / 0.75** (`BattleModeLatSlipScale` 0.75); 4.26 is **3.2×** that | derived, B `:56` |
| battle speed add | **0.0** — Battle never adds speed, it caps it | derived, B `:57` |
| battle cap | `TurningModeMaxSpeed` **600 cm/s = 21.6 km/h** (serialised); `BattleModeVSpeedCurve` 0→60, 600→40, 1200→30 | `MODES.md:86`, `:250-254` |
| `BattleModeMaxSpeed` 1200 / `MaxSteering` 80 | **not serialised** in any archetype | `MODES.md:87,96,121` |
| fleet selector scan | **one** member in 232 builds / 51 module types: `AirplaneAI.Limit_Pitch_Yaw_Switch` — not a selector | T-MD14b |
| HUD rung readout | `UC_SetBoostLevel(level:int, upgradeLevel:int)`; `Upgrade1` visible at `> 0`, `Upgrade2` at `> 1` | `G3-HUD-CLUSTER.md:58,66-67`; `HUD.md:165` |

### 1.2 Closest JC3 mechanism

A **`PerformanceBoost` block applied while a state is active** — the only decoded case of handling members
taking a different value at runtime, and it already ships three rungs per module (`nitro_boost`,
`_upgraded`, `heat_boost`) across nine blocks. Members: `torque_multiplier`, `grip_multiplier`,
`push_force`, `boost_blend_time`, `extra_top_speed` at **0/4/8/12/16** of a 20 B block.

### 1.3 Gap

**There is no selector.** No member in 51 module types chooses a rung; the fleet's only boost gate is the
held input the engine already reads, and `heat_boost` has no shipped consumer (`push_force` 0,
`blend` 0). So the build can rewrite a rung and cannot choose one. Route A (two entities) carries the
values; Route B (`heat_boost`) buys a state only if something outside data fires it.

### 1.4 Build step

1. **Read the target copy first** (this is the C1 fix): dump `CustomLandGlobal` of the actual Batmobile
   build and record its five `nitro_boost` values. Do not assume §2.4's table.
2. **Write `heat_boost` as the battle rung**: torque **2.0** (as shipped), grip **1.333**, push **15000**
   (copy `nitro_boost`'s), blend **0.2**, `extra_top_speed` **0.0**.
3. **Leave `nitro_boost` and `_upgraded` alone**, and say in the log that "unchanged" is relative to the
   module that was read.
4. **Put the 21.6 km/h cap on the entity**, not the block — `PerformanceBoost` has no cap member.
5. **Gate honestly**: `t_md14b.py --check` proves block structure only; `t11_modes.py --check` currently
   exits FAIL (C3), so it is not cited as proof until the ledger order is fixed.

**Pilot sentence:** *Battle mode must raise grip to the derived 1.333 without adding top speed (`+0
km/h`, band ±1), and the car's speed cap in battle must read 21.6 km/h ±0.5.*

---

## 2. Moving parts — P-01 to P-15, corrected

All fifteen rows keep their T-12 ids. "Mechanism" = the closest JC3 member set; "gap" is what has no
member; "build" is the one step that closes or declares it.

| row | corrected fact | closest JC3 mechanism | gap | build step |
|---|---|---|---|---|
| **P-01** `batmobile_turret` | hinge `constraint_index` **11**, axis `[0,1,0]`, pivot `[1.3e-05, 0.876249, 0.333226]` m, **−1.047198…1.047198 rad (−60…60°)** | `all_hinged_part_properties` → `Turret` hinge, donor `-179…179°` | range differs from donor; axis agrees | write ci **11** + the −60…60° limits (B-04 step 3) |
| **P-02** `batmobile_cannon` | **`joint: null`**; no rotation animated; bones translate **53.376 / 36.129 cm**; the −5…20° is the **carrier's** hinge (`JOINT_FIELDS.md` §3, medium-tank column) — it is named in the row's verify text, **not** stored in the row (C11) | `Cannon` channel `none` on the donor turret chain | a hinge cannot reproduce translation | declare static; do not write a joint the row does not carry |
| **P-03** `batmobile_machine_gun` | 2160.0° = 6.00 turns, sampled span 357.354° (one wrap), **peak 1229.51 °/s, mean 553.8 °/s** (C6); axis `[0,0,−1]` | `GatlingGun` → `weapon_rpm`, rotoscope 0, `rotoscope_rpm_per_cycle` 20.0 | `GatlingGun` is **24 rows / 12 parts / 3 chassis, all CBoat/CHelicopter — `unproven-on-CCar`** (`MOVING_PARTS.md:127,170`) | write the rotating row (part 52) with peak/mean both stated; treat the car case as a probe |
| **P-04** `batmobile_riot_suppressor` | BmAK line −89.999…0° about JC3 **−Z**; carrier **+X** −5…20°; part bone spans **6.677° at 47.21 °/s**; `axis_agrees: false` | donor `Cannon` hinge | two different lines, one row — a decision, not a value | pick one line in the row text before writing: BmAK axis `[0,0,−1]` −1.570778…0 rad at 315.39 °/s, or the carrier's +X −5…20° |
| **P-05** `batmobile_jet` | `JetSMove` **translates 40.163 cm** in `Batmobile_V2_Bat_Tracker`; row omitted; the spin is **not** bound to `engine_rpm`: exact string `batmobile_jet` is in **no name table and no export** of the six packages (it is the JC3 part name, part 60), and every jet-named export is accounted for | `EngineRotatingPart` → `engine_rpm`, rotoscope 1, 20.0 (**3 rows / 3 parts / 1 chassis, proven on a CCar**, `MOVING_PARTS.md:67,158`) — the only land-proven rotating behaviour | no bone to drive, no binding: the driver is code → **UNKNOWN** | omit the row; use `EngineRotatingPart` only if a spinning part is ever added |
| **P-06** canopy | **no part**; rotation **−12.492…0.002° (12.494°)** at **136.09 °/s**, axis `[−1,0,0]`; translation **72.481 cm**; donor `sportsmuscle_hood_signature` **0…70°**, pivot `[0, 1.0572, −0.8478]`, `Land_Hood` | `Hood` door channel (`door_parts[]` = part index) | geometry stays in the body shell; JC3 door parts **rotate only**, never translate | declare no-part; do not fake the 72.481 cm with a hinge |
| **P-07** left cover | 14.988° (0.019…15.007°), axis `[−1,0,0]`, **32.14 °/s**, pivot `[−0.616,1.505,−0.465]`, mid-bone **10.866 cm**; no part + omitted `door_parts` row | `MissileHatch` (16 rows / 1 part / 1 chassis, `CTrain`, `unproven-on-CCar`) | no hatch bone and no hatch part | keep the omitted row; pod bones carry the lift (P-14/P-15 joint) |
| **P-08** right cover | same numbers mirror: pivot `[0.615,…]`, mid-bone **10.863 cm**, **75.10 °/s** bottom | same | same | mirror of P-07 |
| **P-09** flap L front | part-bone **20.010° at 37.20 °/s**; row headline **25.817° at 48.70 °/s** (two different bones) | `AirBrake` → `air_brakes_T` (3 parts, 1 plane, `unproven-on-CCar`) | no hinge; carrier limits absent from the 8-entity sample | write the flap row against `air_brakes_T`; state which bone the 25.817° belongs to |
| **P-10** flap R front | mirror of P-09 | same | same | same |
| **P-11** flap L rear | piston **54.787° at 106.14 °/s**; part bone 29.986° at 56.85 | same | same | as P-09 |
| **P-12** flap R rear | piston **54.799° at 105.82 °/s** (not 106.14 — C7); part bone 30.005° at 56.60 | same | same | write 105.82 |
| **P-13** yoke | `joint: null`, **no part**; **0** yoke faces in the hand box; **0** bone matches over **180** bones and **324** packages | none — nothing carries the part | nothing to animate | declare no-part, no joint |
| **P-14** pod L | carries the **`Missiles_*_T` joint** (0.019…15.007°, 32.14 °/s) with `behaviour: null`, `moves_with: P-07`; **not "static"** (C8) — `rows_with_joint: 12` includes it | the same `MissileHatch`/`Hood` families | no behaviour of its own | no joint of its own; moves with P-07's cover |
| **P-15** pod R | same joint, `moves_with: P-08` | same | same | mirror of P-14 |

### 2.1 Row markers and gate facts (unchanged, re-stated)

`static_rows` = **P-02 / P-05 / P-13**; the four "no part" rows = **P-06 / P-07 / P-08 / P-13**;
`rows_with_joint` = **12**; `unproven-on-CCar` behaviour rows = **P-03, P-07, P-08, P-09…P-12**;
**P-04** is the only `axis_agrees: false`. Gates: `t12_parts.py --check` and
`parts_anim_coverage.py --check` both exist and pass; hinge **rate** has no JC3 member — the hinge table
carries only `lod`, `target_position_variable`, `use_target_position_as_angle`.

---

## 3. The six folded-in reports, and what each one changes

| report | answer | changes |
|---|---|---|
| `jet-part-bone-driver.md` | exact `batmobile_jet`: **0 name-table hits, 0 exports** in six packages (3,151/3,156/3,134/3,394 names); jet-named exports exist but none is the Batmobile part; **no `engine_rpm` binding** | P-05: the "spin is `engine_rpm`" claim loses its binding — mark the driver **UNKNOWN**, keep `EngineRotatingPart` as a candidate only |
| `rotor-block-gate-input.md` | **UNKNOWN**: `RotorCollision` is **four floats, no input** — `min_rpm` @0x130 = **30**, `mass_ratio_when_no_mass` 0.1, `damage_to_other_per_second` **100000**, `light_object_mass_ratio` 0.02, identical on 232 builds | the contact channel used by the collision plan: if the gate reads **engine** RPM a car always passes (idle 800 ≥ 30); if **rotor** RPM a car reads 0 and the gate never opens. Settler: `JustCause3.exe`'s RotorCollision consumer |
| `cargo-bay-attach-rule.md` | 12 objects on 12 entities, **7 members**; `enabled = 1` on all, `enable`/`disable` **empty on all 12**; no capacity, no mass limit, no attach-state; `VehicleCargoBay` has **0** INDEX hits | the cargo attach has no data path; the consumer is native → UNKNOWN, not buildable from a bay member |
| `drift-torque-airborne-gate.md` | **NO ground/wheel/airborne flag** in the 21-member `drift` block; gates are **speed** (`min_speed_to_drift_kmph` 10) and **slip** (entry 20 / exit 2); RC2 `max_drift_torque` **12000** | any "torque only on the ground" claim is **false in the data**; whether the native consumer evaluates it airborne is U1 |
| `handbrake-friction-and-block-time.md` | `EBrakeBrakeForce` **640,000** @4628 vs class default **160,000** → ratio **4.0** exact; **`min_time_to_block` has no BmAK member** — the ledger's 5 is unsourced, the "1" is the JC3 donor's, and 0.3 is `HandBrakeOffTime` **0.3 s @960**, a **release** time | the handbrake row keeps 4.0 and loses the block time; JC3 receivers are `brakes.handbrake_friction_factor` (fleet 1..10) and `brakes.<f/r>.min_time_to_block` (time by name, unit unstated) |
| `brake-decel-bridge-derivation.md` | BmAK **300 N·m** over 6000 kg × 0.68275 m × 4 wheels = **0.2929 m/s²**; measured **3.5–3.82 m/s²** = **12×**; JC3 torque for 3.5 = **3,584**, for 3.8 = **3,892**; built **5000** → **4.882 m/s²** | the brake bridge is disproven by magnitude, not units; 5000 is a class value that **overshoots** the footage band by ~28 % |

---

## 4. UNKNOWN rows, each with its settler

| # | UNKNOWN | settles it |
|---|---|---|
| U-B1 | which `CustomLandGlobal` copy each boost table describes | the build's own `custom_land_global.vmodc` dump (do this before any write — §0) |
| U-B2 | whether `heat_boost` is ever reached | the exe's boost consumer; `t_md14b.py` can only prove the block exists |
| U-B3 | what `BattleModeVSpeedCurve`'s factor multiplies | T-MD14b's own UNKNOWN; no decoded reader |
| U-M1 | P-05's spin driver (no `engine_rpm` binding, no bone) | `jet-part-bone-driver.md` §1 name tables + the native `EngineRotatingPart` reader |
| U-M2 | `SteeringWheel` chassis split (8 cars + 1 boat is not printed) | `MOVING_PARTS.md:132` rows, or a chassis-by-chassis dump |
| U-M3 | hinge **rate** (no member) | the exe's hinge driver; JC3 exposes position only |
| U-M4 | P-04's line choice (BmAK −Z vs carrier +X) | an operator decision, then the row text |
| U-M5 | `rotor_collision` gate input on a car | `JustCause3.exe` |
| U-M6 | cargo-bay enable consumer | `JustCause3.exe` (0 INDEX hits for the object name) |
| U-M7 | airborne evaluation of the drift torque | U1 of `air-control-closest-system-plan.md`; Q-AC-1 probe |
| U-M8 | BmAK block time for the handbrake | no member exists; `HandBrakeOffTime` 0.3 s is release, not block |

---

## 5. Build order the two plans imply (no new ranking)

1. **Read the target boost module** and record its five values (§1.4 step 1). Everything else in the
   boost lane depends on which copy is in front of us.
2. **Write the battle rung into `heat_boost`** (grip 1.333, speed 0) and the **cap on the entity**
   (21.6 km/h). Nothing waits on a selector.
3. **Parts lane: the five joint writes** — P-01 (ci 11, −60…60°), P-04 (decision first), and P-09…P-12
   against `air_brakes_T`. P-02/P-05/P-13 are declarations, not writes; P-06/P-07/P-08/P-14/P-15 keep
   their omitted rows.
4. **The car-case probes**: `GatlingGun` on a `CCar` (P-03), `EngineRotatingPart` if a spinning part is
   added (P-05), and the hinge-rate question (U-M3) — all three are one-session probes, not builds.

---

## 6. Checks run, and revert

```
read  tmp/freebuff/reports/audit-boost-selector-and-moving-parts-plans.md   (48 claims, C1-C11)
head  the six folded-in reports                                            (their stated verdicts)
grep  tmp/freebuff/reports/boost-block-selector-closest-system-plan.md:33-34,46,48,56,57,102,117
      → grip 1.0/4.26/4.26, speed 43.2/100.92/100.92; Pursuit "unchanged"; battle grip 1.333; speed 0.0
grep  moving-parts rows P-01…P-15 (plan :27-38, :62-64)                     → row markers match T-12
```

Not re-derived here, and carried from the audit's own re-read: the 48 claim verdicts, the
`T_MD14B_STATES.json` donor values, the P-12 105.82 °/s figure and the `bm_parts.py:503-504` totals.
No game process was started; no module, part, joint, tune or plan was written. Original B and M plans are
unchanged. **Revert:** delete this file.
