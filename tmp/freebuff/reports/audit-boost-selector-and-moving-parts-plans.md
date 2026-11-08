# Audit: the boost-selector and moving-parts plans against their source reports

Lane 8014, 2026-11-07. Audits
`tmp/freebuff/reports/boost-block-selector-closest-system-plan.md` against
`tmp/freebuff/reports/T-MD14b.md` (+ the record it wrote, `Working/Translation/T_MD14B_STATES.json`),
and `tmp/freebuff/reports/moving-parts-behaviour-gaps-closest-system-plan.md` against
`tmp/freebuff/reports/T-12.md` (+ `Working/Translation/T8_PARTS.{md,json}`). Every offset, byte size,
count and row id the plans cite is re-read at the source. **Neither plan was edited.**

Method: the JSON records behind both source reports were loaded and printed row by row
(`T_MD14B_STATES.json` blocks/`land_donor`, `T8_PARTS.json` rows + joint candidates), so the check is
against the decoded record, not against the prose summary. Where a plan cites a third file
(`mode-switch-carriers.md`, `MODES.md`, `JOINT_FIELDS.md`, `MOVING_PARTS.md`, `G3-HUD-CLUSTER.md`),
that file was opened too.

## 0. Change statement (AGENTS.md)

| item | value |
|---|---|
| intended change | add one audit report; no plan, row, module or build touched |
| file | `tmp/freebuff/reports/audit-boost-selector-and-moving-parts-plans.md` (this file) |
| why this file | the brief names it; it is a report, so nothing the game reads changes |
| reverted by | deleting this file. No other file was written |

## 1. Verdict summary

48 claims checked: **VERIFIED 38, OVERSTATED 8, UNSUPPORTED 2.**

| plan | rows | VERIFIED | OVERSTATED | UNSUPPORTED |
|---|---:|---:|---:|---:|
| boost-block selector vs T-MD14b | 22 | 17 | 5 | 0 |
| moving-parts gaps vs T-12 | 26 | 21 | 3 | 2 |

**The mechanical claims hold.** All boost offsets (120/132/144 air, 136/156/176 land), all block
sizes (12 B / 20 B), all five `PerformanceBoost` member offsets (0/4/8/12/16), the 145/41/35 build
counts, the nine-block total, and every T-12 row id `P-01…P-15` with its marker are correct. The
failures are at the edges: one shipped-value table is quoted from a **different module copy** than
the one the plan says it takes "as read"; two gate descriptions promise more than the command
asserts (one of them currently exits FAIL); one rate is mis-transcribed; and two attributions point
at a file that does not print the figure.

## 2. Boost-block selector vs T-MD14b

Sources re-read: `T-MD14b.md` (summary + `--check` block), `T_MD14B_STATES.json`
(`blocks` = 9 entries, `land_donor` = 15 values, `bmak` = 8 carriers), `mode-switch-carriers.md`
§2.4/§2.5 (lines 108-127), `MODES.md` (mode table lines 80-112, curve lines 246-254),
`EJECT.md:198-221`, `G3-HUD-CLUSTER.md:56-70`, `HUD.md:165`,
`correction-8390-collision-placement.md:110`.

| # | claim (plan) | source | what the source says | verdict |
|---:|---|---|---|---|
| B1 | land `CustomLandGlobal` **145** builds, air `AirGlobal` **41**, boat `BoatGlobal` **35** | T-MD14b | "Blocks on AirGlobal 41 builds, BoatGlobal 35, CustomLandGlobal 145" | **VERIFIED** |
| B2 | air blocks at **120 / 132 / 144**, `AirPerformanceBoost`, **12 B** | T-MD14b | "`nitro_boost` @120, `nitro_boost_upgraded` @132, `heat_boost` @144, all `AirPerformanceBoost` (12 B, three floats)" | **VERIFIED** |
| B3 | land `arcade` @**136**, `heat_boost` @**136**, `nitro_boost` @**156**, `_upgraded` @**176**, `PerformanceBoost` **20 B**, members torque@0 grip@4 push@8 blend@12 speed@16 | T-MD14b | same offsets; "`arcade` (`ArcadePhysics`) @136, with `heat_boost` @136, `nitro_boost` @156, `nitro_boost_upgraded` @176, each `PerformanceBoost` (torque@0, grip@4, push@8, blend@12, extra_top_speed@16)" | **VERIFIED** |
| B4 | **nine** blocks in total (3 land + 3 air + 3 boat) | T-MD14b `--check` | "blocks 9"; the JSON `blocks` array has exactly 9 | **VERIFIED** |
| B5 | the `arcade`@136 / `heat_boost`@136 clash is flagged as an unresolved caveat | T-MD14b | the report says the same thing and only the `.vmodc` re-read would confirm it; the plan's U6 names `t_md14b.py --check` | **VERIFIED** (the plan does not hide it) |
| B6 | shipped land values: `grip_multiplier` **1.0 / 4.26 / 4.26**, `extra_top_speed` **43.2 / 100.92 / 100.92** | cited `mode-switch-carriers.md` §2.4 | the table at §2.4 (lines 112-118) is **exactly** those numbers | **VERIFIED as a quote, OVERSTATED as "shipped"** — T-MD14b's own indexed donor (`land_donor`, `v0012_car_autostraad_atv`) carries **grip 2 / — / 1.5** and **speed 40 / 80 / 80**. Two module copies, one table, no vehicle named |
| B7 | "Pursuit = `nitro_boost` **unchanged** (15000 / 2.0 / 1.0 / 43.2 / 0.2)" | same | arithmetic is a copy of B6's row | **OVERSTATED** — "unchanged" holds only for §2.4's copy; on the donor T-MD14b decoded, grip is 2 and speed 40, so the same write *changes* that vehicle |
| B8 | `heat_boost` is the rung with no shipped consumer (`push_force` **0**, `boost_blend_time` **0**) | T-MD14b `land_donor` | `arcade.heat_boost.push_force = 0`, `boost_blend_time = 0` | **VERIFIED** (its grip 1.5 / speed 80 are non-zero, so "unused duplicate of `_upgraded`" holds in §2.4's copy only — the plan's claim is limited to push/blend, so it stands) |
| B9 | Battle grip **1.333** = `1 / 0.75`; 4.26 is **3.2×** that | derived | `1/0.75 = 1.3333`; `4.26/1.3333 = 3.196` | **VERIFIED** |
| B10 | `TurningModeMaxSpeed` **600 cm/s = 21.6 km/h**; `BattleModeVSpeedCurve` **0→60, 600→40, 1200→30** | `MODES.md` | line 86: `TurningModeMaxSpeed` 0x2c4 = **600** cm/s, serialised `yes`; lines 250-254: InVal 0/600/1200 → OutVal **60/40/30** | **VERIFIED** (600 cm/s = 6 m/s = 21.6 km/h) |
| B11 | `BattleModeMaxSpeed` **1200 cm/s = 43.2** and `BattleModeMaxSteering` **80** are **not serialised** | `MODES.md` + `DRIVE_MODES.md` | lines 87/96: both `—`, serialised **no**; T-MD14b's DRIVE_MODES quote gives 80 / 1200, and MODES.md line 121 lists both under "not serialised in any shipped archetype" | **VERIFIED** |
| B12 | `LatSlipScale` **0.75** / `LongSlipScale` **1.25** serialised; DRIVE_MODES says **4 / 10** | `MODES.md` | lines 89-90: 0.75 / 1.25, `yes`; T-MD14b quotes DRIVE_MODES' 4/10 | **VERIFIED** (and the plan's declared conflict is real) |
| B13 | `SteerAngleFactor` **1**, `TrailingSteerFactorMoving` **−0.25**, `DriveForceFactor` **500**, `ThrottleSpeed` **10**, `StopAndTurnAngleStationary` **30**, `TurnOnSpotTorqueFactor` **0.333333**, front/rear **0.8 / −0.8**, `EngineBraking` **2**, `TransformationTurn*` **3000 / 24000**, `DrivingForceZOffset` **20 cm** | `MODES.md` | 0x300 = **1**; 0x320 = **−0.25**; 0x2f4 = **500**; 0x2ec = **10**; 0x2f8 = **30**; 0x2e0 = **0.333333**; 0x1c8/0x1cc = **0.8 / −0.8**; 0x1d0 = **2**; 0x390/0x394 = **3000 / 24000**; 0x324 = **20** cm — all serialised `yes` | **VERIFIED** — and note **T-MD14b is stale here** (`SteerAngleFactor` 2.5, counter-torque 0.6/−0.5). One unflagged sibling conflict: `DRIVE_MODES.md:77` gives `DrivingForceZOffset` **10**, not 20 (same class as the MaxSpeed conflict the plan does declare) |
| B14 | `arcade.turbo_jump` / `_upgraded` pair; `VehicleMisc.turbo_jump_cooldown` **5 s** / `_upgraded` **2 s** | `EJECT.md:205-215` | lines 214-215 carry exactly 5 s / 2 s; both `turbo_jump` blocks are in the same table | **VERIFIED** |
| B15 | `UC_SetBoostLevel(level, upgradeLevel)`; `Upgrade1` at `> 0`, `Upgrade2` at `> 1` | `G3-HUD-CLUSTER.md` §2, `HUD.md` §4 | line 58: `UC_SetBoostLevel(level:int, upgradeLevel:int)`; lines 66-67: "`Upgrade1` … visible when `upgradeLevel > 0 / > 1`"; `HUD.md:165` gives the signature | **VERIFIED** |
| B16 | the 51-module scan returns **one** hit, `AirplaneAI.Limit_Pitch_Yaw_Switch` | T-MD14b | "A fleet-wide member scan of 232 vehicle builds / 51 module types … returns **one** member" | **VERIFIED** |
| B17 | gate: `t_md14b.py --check` proves "9 blocks, offsets ascending, the 3 land blocks still present" | T-MD14b `--check` | the check asserts the hit set, that `heat_boost` exists, that the donor carries `arcade.nitro_boost.extra_top_speed`, and that the **air** offsets are ascending (120 < 132 < 144). It does not assert land offset order or "3 land blocks" | **OVERSTATED** (narrow it to the air offsets + block count) |
| B18 | gate: `t11_modes.py --check` proves the **15-row** mode record re-derives | ran it here | prints `FAIL: 15 rows | MOD-1 4 / MOD-2 11 | compromises carried 8, inside band 1, omitted 6 | ledger 15/15` and `FAIL ledger T-WP4 is next, the row cites blocked` — **15 rows is right, the command exits FAIL** | **OVERSTATED** (count verified; not a green gate today) |
| B19 | `bm_rc4.py --check` dies with `MemoryError` on this machine | `correction-8390-collision-placement.md:110` | "**COULD NOT RUN**: `MemoryError` in `tree()` at `bm_rc4.py:118` … Not a data failure" | **VERIFIED** |
| B20 | `b12_variants.py --check` exists as the pair gate | repo | file present at `Tools/scripts/b12_variants.py` | **VERIFIED** (its D-2 precondition was not re-checked) |
| B21 | swap trigger: "candidate 1 `USE_VEHICLE_MOD`, candidate 2 the Rebel Drop item pair" | `mode-swap-trigger-closest-system-plan.md` | line 29 ranks **Rebel Drop** "**closest match**"; line 31 calls `USE_VEHICLE_MOD` "**possible, not proven** — binding it is free, but a consumer must exist" | **OVERSTATED** (the plan lists the weaker candidate first) |
| B22 | Route C: only **2** `ExtendedExposedVariables` expressions in the fleet | `mode-switch-carriers.md` | line 158: "`ExtendedExposedVariables` expressions beyond the speed-ramp pair: **0**" → 2 total | **VERIFIED** |

## 3. Moving-parts plan vs T-12

Sources re-read: `T-12.md` (outputs, done-check, UNKNOWNs), `T8_PARTS.json` (`summary`, all 15 `rows`,
every joint candidate), `T8_PARTS.md:44-59` (the row table) and its per-part notes
(127-128, 139, 155, 168), `JOINT_FIELDS.md` §1-§5, `MOVING_PARTS.md` §1-§3
(lines 24-33, 58-71, 127-173), `P13_STEERING.md:24-28`, `bm_parts.py:503-504`.

| # | claim (plan) | source | what the source says | verdict |
|---:|---|---|---|---|
| M1 | "15 rows = 11 cut parts + 4 items with no part" | `T8_PARTS.json` `summary` / T-12 | `rows: 15`, `parts: 11`; T-12 lists 11 cut parts + canopy, hatches L/R, yoke | **VERIFIED** |
| M2 | `static_rows` are P-02 / P-05 / P-13 | `summary.static_rows` | `["P-02","P-05","P-13"]` | **VERIFIED** |
| M3 | P-01: `constraint_index` **11**, axis `[-0.0, 1.0, -0.0]`, pivot `[1.3e-05, 0.876249, 0.333226]` m, `-1.047198 … 1.047198` rad (−60…60°) | `JOINT_FIELDS` §3-§4, `T8_PARTS.md` P-01 | identical values; 120° span, axis +Y | **VERIFIED** |
| M4 | P-02: index **12**, axis `[1,0,0]`, pivot `[0.000358, 1.702446, 0.017586]`, `-0.087266 … 0.349066` rad (−5…20°) | `JOINT_FIELDS` §3-§4 | identical | **VERIFIED** |
| M5 | "P-02's -5…20° carrier hinge is **already in the row**" | `T8_PARTS.json` P-02 / `JOINT_FIELDS` §3 | the row has `joint: null`; −5…20 appears only in the verify text ("stops at the carrier's own -5..20 deg"); the hinge numbers are `JOINT_FIELDS`' medium-tank column, not a row field | **OVERSTATED** (say "named in the row's verify; the hinge values come from JOINT_FIELDS §3") |
| M6 | P-04: BmAK line `-89.999…0°` about JC3 **−Z**, carrier `+X` −5…20°, part bone spans **6.677°** at 47.21 °/s, `axis_agrees: false` | `T8_PARTS` P-04 | JC3-space axis `[0,-0,-1]`; span 89.999 (−89.999…−0.000) at 315.39; pivot bone `Riot_Suppressor_Root` **6.677°** at **47.21**; `axis_agrees: false` | **VERIFIED** |
| M7 | P-03: "**2160.0° = 6.00 turns over 3.90 s at 1229.51 °/s**"; 357.354° sampled extent is one wrap | `T8_PARTS.md` P-03 | row says "6.00 turns / 2160.0° in 3.90 s", rate **1229.51**, sampled span **357.354** | **VERIFIED as a quote** — but the three numbers cannot all be true (`2160/3.90 = 553.8 °/s`); 1229.51 is a peak, not the average. See C6 |
| M8 | P-03 rotating row axis `[-0.0, 0.0, -1.0]` | `T8_PARTS.md` P-03 | JC3-space axis `[0.000, -0.000, -1.000]` (bone-local +X) | **VERIFIED** |
| M9 | P-05: `JetSMove` translates **40.163 cm**; spin is `engine_rpm`; row is omitted | `T8_PARTS.md:127-128` | "`JetSMove` moves 40.163 cm in `Batmobile_V2_Bat_Tracker`"; `joint: null` | **VERIFIED** |
| M10 | P-06: rotation `-12.492…0.002°` (12.494°), axis `[-1,0,0]`, **136.09 °/s**, translation **72.481 cm** | `T8_PARTS.md` P-06 / T-12 | P-06 axis (JC3) `[-1.000,-0.000,-0.000]`, span 12.494, 136.09; T-12 gives the 72.5 cm lift | **VERIFIED** |
| M11 | P-06 donor carrier: `sportsmuscle_hood_signature`, **0.0…70.0°**, pivot `[0.0, 1.0572, -0.8478]`, `Land_Hood` | `T8_PARTS.md:139` | identical, on `..._signature_preorder.ee`, `hkpLimitedHingeConstraintData` | **VERIFIED** |
| M12 | P-07/P-08: **0.019…15.007°** (14.988°), axis `[-1,0,0]`, top **32.14** / bottom **75.10** °/s, pivots `[-0.616,1.505,-0.465]` / `[0.615,…]`, `10.866 / 10.863 cm` mid-bone | `T8_PARTS` rows + `T8_PARTS.md:155,168` | row + candidates give 0.019…15.007, 32.14 (top) and 75.1 (bottom); the pivots and the two translations match lines 155/168 | **VERIFIED** |
| M13 | P-09…P-12: part-bone spans **20.010°** (37.20) and **29.986 / 30.005°** (56.85 / 56.60); pistons **25.817°** (front) and **54.787 / 54.799°** (rear) at **48.70 / 106.14** °/s | `T8_PARTS` candidates | 20.010@37.20 ✓; 29.986@56.85 ✓; 30.005@**56.60** ✓; 25.817@48.70 ✓; rear pistons **54.79@106.14** and **54.799@105.82** | **UNSUPPORTED** for the last pair: the plan gives one rate (**106.14**) to both rear pistons; P-12's is **105.82** |
| M14 | P-14/P-15 are "**static**: no behaviour of its own, `moves_with` P-07/P-08" | `T8_PARTS` rows | both rows **carry a joint** (`Missiles_*_T`, 0.019…15.007, 32.14) with `behaviour: null` and `moves_with` set; the summary counts `rows_with_joint: 12`, which includes them | **OVERSTATED** (word "static"; the accurate claim is "no behaviour of its own") |
| M15 | `aim_part_constraints[]`: **85 rows in 17 of 78 modules**, all suspension, 0 on the six turreted vehicles | cited `TURRET.md` | every turreted sample prints `aim_part_constraints` rows **0** and the report says the array "is **not** turret aim - it is the suspension linkage"; the **85/17/78** figure is printed only in `bm_parts.py:503-504` ("G2-13 `TURRET.md`: … 85 rows in 17 of 78 modules") | **OVERSTATED** (attribute the totals to `bm_parts.py`'s `aim_note`, which cites TURRET.md; TURRET.md itself never prints them) |
| M16 | hinge object: **304 B** `hkpLimitedHingeConstraintData`, axis `+0x30`, pivot `+0x60`, min/max `+0xFC`/`+0x100` rad | `JOINT_FIELDS.md` §1-§2 | identical table | **VERIFIED** |
| M17 | parts **50/51** currently ship `constraint_index = -1` | `JOINT_FIELDS` §5 | "`bm_parts.py` writes … a literal `-1` at line 645 … the current build ships `constraint_index = -1` on parts 50/51" | **VERIFIED** |
| M18 | `GatlingGun`: `rpm_variable` `weapon_rpm`, rotoscope **0**, `rotoscope_rpm_per_cycle` **20.0**; **24 rows / 12 parts / 3 chassis**, all `CBoat`/`CHelicopter` | `MOVING_PARTS.md` | line 61: `GatlingGun | weapon_rpm | 0 | 0 | 0 | 0 | 20.0`; line 127: "24 | 12 | 3 | `CBoat`, `CHelicopter` | unproven-on-CCar" | **VERIFIED** |
| M19 | `EngineRotatingPart`: `engine_rpm`, rotoscope **1**, 20.0; **3 rows / 3 parts / 1 chassis**, proven on a land vehicle | `MOVING_PARTS.md` | line 67: `1 | 0 | 1 | 0 | 20.0`; line 158: "3 | 3 | 1 | `CCar` | proven-on-CCar" | **VERIFIED** |
| M20 | `Hood` is a name-only door row; `door_parts[]` stores a part index only | `MOVING_PARTS.md` §1/§3 | `Hood` in the name-only `all_door_part_properties` list (line 77); §3 says the array holds the part index | **VERIFIED** |
| M21 | `MissileHatch`: **16 rows, 1 part, 1 chassis** (`v5603_train_urga_monorailmissilecar`, `CTrain`) | `MOVING_PARTS.md:137` | "16 | 1 | 1 | `CTrain` | unproven-on-CCar"; the chassis name is line 173's neighbour (train) | **VERIFIED** |
| M22 | `AirBrake`: **3 parts, one plane** (`v4602_plane_urga_fighterbomber`, `CAirPlane`) | `MOVING_PARTS.md:157,173` | "3 | 3 | 1 | `CAirPlane` | unproven-on-CCar"; line 173 names `v4602_plane_urga_fighterbomber` | **VERIFIED** |
| M23 | `SteeringWheel`: **20 rows / 20 parts / 9 chassis** — "**8 cars + 1 sailboat**" | `MOVING_PARTS.md:132` | "20 | 20 | 9 | `CBoat`, `CCar` | proven-on-CCar" — classes only; no 8+1 split is printed | **UNSUPPORTED** (the 20/20/9 is verified; the 8+1 breakdown is not in the source) |
| M24 | hinge **rate** has no JC3 member (`lod`, `target_position_variable`, `use_target_position_as_angle` only) | `MOVING_PARTS.md` §1 / T-12 UNKNOWN 1 | the hinged table has exactly those three columns; T-12 UNKNOWN 1 says the same | **VERIFIED** |
| M25 | reproduce with `t12_parts.py --check` and `parts_anim_coverage.py --check` | repo | both scripts exist (`Tools/scripts/`) | **VERIFIED** |
| M26 | P-13: 0 yoke faces in the hand box; **0** bone matches over **180** bones and **324** packages | `P13_STEERING.md:24-28` | "180 bones … **0** bones match `steer`/`yoke`"; "**0 name-table entries** … in any of the 324"; "the hand box … holds **4 faces of any material**" | **VERIFIED** |

## 4. Required corrections

**C1 — boost §1/§2: name the module copy, and reconcile it with T-MD14b.**
The shipped-value table is `mode-switch-carriers.md` §2.4 verbatim (`grip 1.0 / 4.26 / 4.26`,
`speed 43.2 / 100.92 / 100.92`). T-MD14b's indexed donor (`land_donor`, `v0012_car_autostraad_atv`)
carries `grip 2 / — / 1.5` and `speed 40 / 80 / 80`. Two copies, two value sets. Either name the
vehicle §2.4's table comes from, or add a row: *"shipped values differ per `CustomLandGlobal` copy;
this plan's baseline is §2.4's copy, T-MD14b's is the ATV"*. Without it, "Pursuit is unchanged" is
false on the donor the card was built from.

**C2 — boost §8, first gate.** `t_md14b.py --check` asserts the hit set, that `heat_boost` exists,
the donor's `extra_top_speed`, and that the **air** offsets ascend. It does not assert land offset
order or "the 3 land blocks still present". Reword to what the command does.

**C3 — boost §8, `t11_modes.py --check`.** Run here: **15 rows confirmed**, exit **FAIL**
(`ledger T-WP4 is next, the row cites blocked`). A gate listed as proof that currently fails must say
so, or the ledger order must be fixed before the card claims it.

**C4 — boost §4 Route A.** The trigger report ranks **Rebel Drop** "closest match" and
`USE_VEHICLE_MOD` "possible, not proven". List them in that order, or state why the plan inverts it.

**C5 — boost §5, `BattleModeDrivingForceZOffset`.** `MODES.md:103` = **20 cm** (serialised);
`DRIVE_MODES.md:77` = **10**. This is the same cross-file conflict the plan already handles for
`BattleModeMaxSpeed`/`MaxSteering`/slip scales; the ZOffset row should carry the same caveat instead
of a bare 20.

**C6 — moving §3 and `T8_PARTS.md` P-03: the spin arithmetic.** "6.00 turns / 2160.0° in 3.90 s at
1229.51 °/s" cannot all hold: `2160 / 3.90 = 553.8 °/s`. 1229.51 is the **peak** rate; either state
the mean (553.8 °/s) beside the peak, or drop the duration. Fix the row and the plan together, since
the plan copies the row.

**C7 — moving §7: P-12's piston rate.** P-11's rear piston-top is **54.79° @ 106.14 °/s**; P-12's is
**54.799° @ 105.82 °/s**. The plan gives 106.14 to both. Write `106.14 / 105.82`.

**C8 — moving §1: P-14/P-15 are not "static".** Their rows carry a joint (the same
`Missiles_*_T` joint as P-07/P-08) and `behaviour: null`; what is absent is a behaviour, not the
joint. Use "no behaviour of its own" so the `rows_with_joint: 12` count is not contradicted.

**C9 — moving §2/§9: the 85/17/78 figure.** `TURRET.md` prints `aim_part_constraints` rows = 0 for
every turreted sample and never prints the fleet totals; the totals live in `bm_parts.py`'s
`aim_note` (lines 503-504), which cites TURRET.md. Attribute it that way, or omit the totals and keep
the (verified) "0 on the six turreted vehicles".

**C10 — moving §8: "8 cars + 1 sailboat".** `MOVING_PARTS.md` gives the 9 chassis' **classes**
(`CBoat`, `CCar`) for the 20 `SteeringWheel` rows; it does not split them 8+1. Drop the split or
source it.

**C11 — moving §2: "already in the row".** The P-02 row is `joint: null`; the −5…20° is its verify
text, and the hinge numbers are `JOINT_FIELDS` §3's medium-tank column. Reword to keep the provenance
straight.

**No correction needed for the T-12 marker mapping.** The plan's list — `static_rows`
P-02/P-05/P-13, the four "no part" rows P-06/P-07/P-08/P-13, the `unproven-on-CCar` rows, P-04's
`axis_agrees: false`, and the `omitted[]` entries — matches `T8_PARTS.json`'s summary and T-12's own
text row for row.

## 5. What this audit did not check

1. **Whether the source reports are right in absolute terms.** Only agreement was audited. If
   `T-MD14b`'s `land_donor` is the wrong module, C1 changes shape.
2. **`B-08` / `B-09` / `B-11` / `B-12` references** in the boost plan's routes — backlog cards, not
   in either source report.
3. **`D-2`'s resolution state** behind `b12_variants.py --check` (the file exists; the precondition
   was not re-read).
4. **`BattleModeVSpeedCurve`'s meaning** — the three points are decoded, what the factor multiplies
   is not (T-MD14b's own UNKNOWN).
5. **Whether `heat_boost` is ever reached** — unchanged UNKNOWN, settler still the exe's boost
   consumer.
6. **`T8_PARTS.md`'s 72.481 cm** for P-06 — the plan and T-12 agree to 72.5 cm; the four-decimal
   figure was not re-derived here.

## 6. Checks run for this report, and revert

| # | check | result |
|---|---|---|
| 1 | `T_MD14B_STATES.json` blocks/`land_donor`/`bmak` printed and compared to the plan's tables | offsets, sizes, counts agree; shipped values diverge (C1) |
| 2 | `MODES.md` mode table (0x1c8-0x394) and curve points re-read | all 13 values in §5 match; T-MD14b's 2.5 / 0.6 / −0.5 are the stale ones |
| 3 | `T8_PARTS.json` summary + all 15 rows + every joint candidate printed | row ids/markers agree; two numeric slips (C7) and one label slip (C8) |
| 4 | `T8_PARTS.md:44-59` row table cross-read against the JSON | axis (JC3 space) and spans agree |
| 5 | `JOINT_FIELDS.md` §1-§5, `MOVING_PARTS.md` §1-§3, `P13_STEERING.md`, `EJECT.md:198-221`, `G3-HUD-CLUSTER.md:56-70`, `HUD.md:165`, `correction-8390:110` opened | every quoted figure found at the cited place |
| 6 | `python Tools/scripts/t11_modes.py --check` (read-only) | 15 rows; exit **FAIL** on ledger order (C3) |

No game process was started; no build, module, row, `.rbm` or plan was written. **Revert:** delete this
file.
