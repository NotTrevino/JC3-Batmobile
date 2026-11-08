# Landmark map: HANDLING, PHYSICS & COLLISION

Date of map: 2026-11-08. Read-only survey; no project file edited, no game launched.
Convention: paths are relative to `E:\Modding\JC3-Batmobile`. Statuses are copied from the project's own ledgers, not judged by me, except where I mark "(map)". UNKNOWN = not found in the files I read.

## 0. Ground truth in five lines (read first)

1. Nothing in this landmark has ever been behaviour-verified in game. `STATUS.md`: "0 / 221 rows fully behaviour-verified"; 4 rows have partial QA-1 numbers (one take, test-085, `Working/Translation/QA1_RESULTS.md`: 0-100 km/h 16.4 s, peak 138 km/h at Cd 0.139, braking 3.5-3.8 m/s^2, first shift 67 km/h).
2. The test ban stands: `tmp/freebuff/APPROVED_Q.txt` does not exist (checked). `Working/Q/APPROVAL_REQUEST.md` is for bm-RC4, and RC4 is frozen/incomplete (`receipt.complete=false`, pursuit set only, `STATUS.md`).
3. The handling build card B-24 (queue 9120) was never built. That is why RC4 still carries T-ST7 steer times 0.80 / 0.60 s against the operator ruling 0.25 / 0.091 s (`tmp/freebuff/queue/9120-rc5-handling-values.txt`, v05_driving red on T-ST7 per `MODLOG.md` VX entry).
4. Queue 9120, 9121, 9122, 9123, 9124, 9130, 9141 are all queued; none of their DONE reports exists (`tmp/freebuff/reports/rc5-*.md` absent, checked). Only `Builds/bm-RC5-audio` and `Builds/bm-RC5-entity` exist as RC5 trees.
5. No JC3 runtime oracle exists: `Tools/scripts/jc3oracle.py` and `Research/JC3Grab/ORACLE.md` absent (checked). Only the static layout RUNTIME_LAYOUT*.md exists. The BmAK-side sampler (`bmak_runtime_sampler.py`) did run live (G3-02d) but reads BmAK, not JC3.

## 1. Task table

Legend: stage GRAB/TRANSLATE/BUILD/VERIFY/PILOT/TEST/RELEASE. Size S<=1 session, M 1-3, L 1-2 wk (L here is mostly wall-clock with the operator).
"Q-2 take" ids A1..A9 are the pilot driving cards in `tmp/freebuff/reports/pilot-card-driving-takes.md` (A2 top speed, A5 braking, A6 kerb/landing, A7 handbrake drift, A9 boost 0-100, A1 0-100, A3 constant-radius corner, A4 steering lock time). NOTE: the `| A2 | ... 258 km/h | PASS |` row at line 94 of that file is a worked example in a template, not a result.

### 1A. GRAB (BmAK side and JC3 side evidence)

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| G1-1 | Name all 423 BmAK offset fields (engine, steering, suspension, drift members) | GRAB | done | - | all T-E/ST/S rows | - | `STATUS.md` (423/423), `Research/BatmobileGrab/BMSDK_OFFSETS.json` |
| G1-18 | Tyre diameter reconciliation (1.366 m PSKX, D-1 keep) | GRAB | done | - | T-G2 | - | `Research/BatmobileGrab/TYRES.md` |
| G2-21 | Tank pivot / turn-on-the-spot carrier: none exists in driving modules | GRAB | done (negative) | - | T-MD8 named omission | - | `Research/JC3Grab/TANKTURN.md` |
| G2-30 | `.physicsc` write spike (round trip byte-identical, hull rewrite re-reads clean) | GRAB | done | - | T-22, B-10 | - | `Research/JC3Grab/PHYSICS_WRITE.md`, `Tools/scripts/jc3hkx.py` |
| G3-01 | BmAK drivable collision: class defaults, 7 objects | GRAB | done | - | G3-01b | - | `Research/BatmobileGrab/COLLISION.md` |
| G3-01b | BmAK AggGeom + Batmobile_V3_Physics | GRAB | partial | open: box rotations, 0x4C tag, extents convention, active mesh | frame closure | S | `Research/BatmobileGrab/COLLISION_GEOM.md`; GRAB_BACKLOG tracker row G3-01b |
| G3-01c | Convex elements 43 battle / 13 pursuit | GRAB | done | - | - | - | `Research/BatmobileGrab/COLLISION_CONVEX.md` |
| G3-01d | Collision-to-render frame link (+5 cm X, min +0.22 cm) | GRAB | done | - | - | - | `Research/BatmobileGrab/COLLISION_FRAME.md` |
| G3-01e / e-fix | Active collision mesh per mode (0 none / 1 pursuit / 2 battle) | GRAB | done (adjudicated; WinchPullType/IsVehicleAsleep unconfirmed) | - | mode-pair collision | - | `Research/BatmobileGrab/COLLISION_SELECTOR.md`, `COLLISION_SELECTOR2.md` |
| G3-16 | Where the drivable asset really is: `Physics.Batmobile_V3_Physics` = 2 bodies / 3 boxes / 1 constraint | GRAB | done | - | T-22 reopen | - | `Research/BatmobileGrab/COLLISION_WHERE.md` |
| G3-box0x4C | Identify packed bool at 0x4C of each FKBoxElem | GRAB | done? (report exists; consumer is 9141) (map: unverified) | - | 9141 | S | `tmp/freebuff/reports/box-flag-0x4c-witness.md` |
| G3-06 / 06b / 06c | 925 untagged objects accounted; class defaults named; none carries a vehicle number | GRAB | done | - | - | - | `Research/BatmobileGrab/REMAINDER.md`, `CLASS_DEFAULTS.md`, `NATIVE_TRIAGE.md` |
| G3-06f | Interaction/threat/physics components (17 objects incl. 1 CylinderComponent) | GRAB | todo | G3-10 depth | DIM-4 completeness | S | GRAB_BACKLOG tracker G3-06f |
| G3-06 handling classes | The R-6 intent "decode handling/upright/damage/material classes" was NOT delivered; `REMAINDER.md` has byte accounting only | GRAB | partial (map) | - | self-right fidelity, T-SR1 | M | `Research/BatmobileGrab/REMAINDER_SAMPLE_AUDIT.md` (R-6-sample row) |
| G3-07 | JC3 runtime oracle (read-only ReadProcessMemory sampler: loaded resources, live body transforms) | GRAB | open (never started as a tool) | - | every in-game check, T-22 acceptance, "does the game read our .physicsc" | L | GRAB_BACKLOG §6b G3-07; `Tools/scripts/jc3oracle.py` absent |
| G3-07a | Static runtime layout (part node, body-slot array, slot record, shape decoded; root global, transform-vs-AABB, render, resources UNKNOWN) | GRAB | done (partial UNKNOWNs) | - | G3-07b | - | `Research/JC3Grab/RUNTIME_LAYOUT.md` .. `RUNTIME_LAYOUT5.md` |
| G3-07b | Close G3-07a UNKNOWNs (task 2030) | GRAB | queued | - | G3-07 | M | GRAB_BACKLOG tracker G3-07b |
| G3-10 / 10b / 10c | JC3 physics roles, constraints, mass properties, body entries | GRAB | partial (static done; inertia UNKNOWN; partner-body REFUTED, best candidate 51%) | runtime part needs G3-07 | mass/inertia translation certainty | M | `Research/JC3Grab/PHYSICS_ROLES.md`..`PHYSICS_ROLES6.md` |
| G3-10c2 | BmAK cooked physics has no mass/tensor; box/hull inertia oracle refuted 0/107 | GRAB | done (UNKNOWN stays) | - | T-M1, T-M2 remain declared, not decoded | - | `Research/BatmobileGrab/INERTIA.md` |
| G3-10e/f/g/h | Hinge limits, ray id space, bodyB sentinel | GRAB | done | - | - | - | `Research/JC3Grab/PHYSICS_LIMITS.md`, `PHYSICS_ROLES5.md`, `PHYSICS_ROLES6.md` |
| G3-12f | `.physicsc` extents/AABB decoded, 5 files | GRAB | done | - | B-10 | - | `Research/JC3Grab/PHYSICSC_EXTENTS.md` |
| G3-08 / DRIVE_CARRIERS | JC3 vehicle input model and drive carriers (`steering_type` FrontSteered 51 / absent 3; no rear/all-wheel enum; keymap global) | GRAB | done | - | 4WD feasibility | - | `Research/JC3Grab/INPUT.md`, `DRIVE_CARRIERS.md` |
| G3-02g | BmAK drive-mode arithmetic: `RVehicleSimBatmobile.SetDriveMode` body is a native stub (exe) | GRAB | done as UNKNOWN | exe decompile not attempted | exact battle torque split, camera->aim resolution | M | `Research/BatmobileGrab/DRIVE_MODES.md` section 7; `tmp/freebuff/reports/drive-mode-torque-arithmetic-substitute-plan.md` |
| T-26 | Decode the drag triple (`Drag`@16, `DragNoLoad`@20, `DriftDrag`@712): serialised or code-side | GRAB | todo | - | T-R2, top-speed honesty | S | GRAB_BACKLOG T-26 (line ~1271) |
| NEW-HDL-1 | Walk the same tag list for the remaining unvalued handling members the plans call UNKNOWN: which of `BatmobileStuckTimeMax`/`Flip` the righting code reads, `BattleModeSteerBiasRate` consumer, `AirControl*` window source; list each as serialised/declared/exe-only | GRAB | todo | - | flip, air-control, battle-yaw builds | S | `tmp/freebuff/reports/stuck-flip-build-plan-merge.md` S2, `bm-moving-yaw-toward-aim.md` |
| NEW-HDL-2 | BmAK ground-truth numbers a file cannot give (0-100, top speed, turn radius, spin-in-place rate, flip delay) via captured BmAK footage with the QA-1 style reader. Needs operator capture. | GRAB | todo | operator capture session | calibration of all "assumed" and "derived" targets | M | `OPERATOR_PRIORITIES.md`; `GRAB_BACKLOG.md` G1-23 (footage card); `Tools/scripts/qa1_hud.py` |
| NEW-HDL-3 | BmAK runtime read of the sim (Drag, torque, effective speed cap, DriftDrag) through the existing BmSDK sampler if the repack/GOG port lands | GRAB | todo | 7994/7995 BmSDK port (queued; hook offset 0x5B7220 invalid on this exe per QUEUE_MAP) | T-26 if code-side, T-E5 | M | `tmp/freebuff/queue/7995-bmsdk-port-to-repack-exe.txt`, `Tools/scripts/bmak_runtime_sampler.py` |
| NEW-HDL-4 | Fleet census of JC3 wheel/tyre grip members and their domains so T-R1 (arcade friction 3.0) and T-G5 (friction_type 2) are checked as a range, not a single value | GRAB | todo (map: row cites a probe, not a census) | - | tyre grip tune | S | `Working/Translation/T_ROWS.jsonl` T-R1, T-G5 |

### 1B. TRANSLATE (ledger rows; "queued" = resolved from evidence but not taken)

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| T-G1/G2/G3/G6 | Dimensions, wheelbase, tyre radius/width, sim radius (keep) | TRANSLATE | done, queued for take | - | A6 | - | `Working/Translation/T_ROWS.jsonl` |
| T-G4 | Ground clearance 0.071 m (derived underbody; `ground_clearance` member does not exist in BmAK) | TRANSLATE | next (resolved, unbuilt) | B-24 | A6 | S | T_ROWS T-G4 |
| T-G5 | Wheel friction_type 0->2 probe | TRANSLATE | edit (carried test-085) | - | grip tune | - | T_ROWS T-G5 |
| T-M1 | Mass 4000->6000 kg (BmAK has no absolute mass; armored-class pick) | TRANSLATE | edit; only measure is 0-100 16.4 s at 6 t | no lore source (G3-10c2) | A1 | - | T_ROWS T-M1, `QA1_RESULTS.md` |
| T-M2 | Inertia 4.0/2.6/1.2 (BmAK has only neutral multiplier) | TRANSLATE | edit; declared, unverified | UNKNOWN inertia | A3, A4 | - | T_ROWS T-M2 |
| T-M3 / T-M4 | CoM -0.3 keep (declared); wheel mass 75/150 | TRANSLATE | next / edit | - | A6 | - | T_ROWS |
| T-E1 | rpm band 800/2800/4500 | TRANSLATE | edit; measured partially (QA-1) | - | A1, A2 | - | `QA1_RESULTS.md` section 5 |
| T-E2 | Torque 2921 N.m (from 1200 bhp lore via 894.8 kW) | TRANSLATE | next | - | B-24 | - | T_ROWS T-E2 |
| T-E3 | Torque factors 1.0/0.65 | TRANSLATE | edit | - | - | - | T_ROWS |
| T-E4 | 5-gear box at 4200 rpm | TRANSLATE | edit; first shift 67 km/h confirmed | later shifts need rpm channel | A2 | - | `QA1_RESULTS.md` section 3 |
| T-E5 | Top speed 336.4 km/h (209 mph w/ afterburner) | TRANSLATE | next, class ASSUMED (wiki label; no BmAK member) | no honest carrier (see NEW-HDL-10) | A2 | M | `tmp/freebuff/reports/correction-8391-top-speed-label.md`, `Working/Q/PREDICTIONS.md` D-2 |
| T-B1/B2/B3/B4 | Nitro/afterburner: torque mult 6.3, extra top speed 43.2 km/h, grip 1.0, heat_boost restore | TRANSLATE | next (B2 live test-088, B3 test-089, B4 test-090) | - | A2 boost leg, A9 | - | `STATUS.md` batch note, T_ROWS |
| T-A1..A4 | Aero: cross-section, Cd 0.55 class fit, lift -0.3 | TRANSLATE | keep / edit / next (A3 -> 1.0 identity) | T-26 | A2 | - | T_ROWS, `QA1_RESULTS.md` |
| T-R1 | Arcade friction 1.0->3.0 | TRANSLATE | edit | no BmAK friction tag (absence proven) | A3 | - | T_ROWS T-R1 |
| T-R2 | Drag 0.1/0.1 keep until the triple is decoded | TRANSLATE | next (keep) | T-26 | top speed | - | T_ROWS T-R2 |
| T-R3 | Raycast wheels, no shape-cast (LORE-EXACT) | TRANSLATE | keep | - | - | - | T_ROWS T-R3 |
| T-ST1 | Steer 55 deg low speed to 20 deg at 72 km/h | TRANSLATE | edit | - | A3 | - | T_ROWS |
| T-ST2/ST3/ST7 | Full-lock time 0.25 s low / 0.091 s high (operator ruling 2026-11-06, option A). Old "blocked as JC3 limit" REFUTED: player bikes ship 0.3 s, AI cars 0.25 s | TRANSLATE | next (resolved, unbuilt; RC4 module still 0.8/0.6) | B-24 | A4, V-05 green | - | `Working/Translation/T_ST7_EVIDENCE.md`, `DECISIONS_NEEDED.md`, `T_ROWS.jsonl` T-ST7 |
| T-ST4/ST5/ST6 | Steer input exponent identity; countersteer 1.0/1.0; rear aligning 0.625 | TRANSLATE | next | B-24 | A7 | - | T_ROWS |
| T-K1 | Brake torque 5000 (BmAK 300 N.m bridge refuted by magnitude: 0.29 vs 3.5 m/s^2) | TRANSLATE | edit; half-measured | - | A5 | - | `QA1_RESULTS.md` section 4, `tmp/freebuff/reports/brake-decel-bridge-derivation.md` |
| T-K2/K3/K4 | Brake lock time, handbrake friction 4.0 (the "5" is unsourced), block time 0.3 | TRANSLATE | next | reconcile with `handbrake-friction-and-block-time.md` | A7, A5 | - | T_ROWS, 9120 brief |
| T-DR1 | Drift min speed 0, sensitivity 2 | TRANSLATE | next | B-24 | A7 | - | T_ROWS T-DR1 |
| T-S1/S2/S3/S4/S5 | Suspension strength 45, compression 3.0, length, antiroll 0, slip pair 0.1/0.05 | TRANSLATE | edit/next | T-S3 vs bridge conflict (0.70 vs 0.40 m) | A6 | S | T_ROWS, `tmp/freebuff/reports/suspension-unit-bridge.md` |
| T-S6 | Droop 100 cm, up-travel 30, stiffness 3000/750, damping 300/20, bias 50/10/5: bridge derived (length 0.40, strength 13.5 s^-2, damping 1/2, front bias -0.10) | TRANSLATE | next (was blocked; moved) | B-22, B-23 | A6 | - | `tmp/freebuff/reports/apply-suspension-rows.md`, `t_s6_bridge.py` |
| T-AC1 | Air control: `drift.max_drift_torque` 8000 + aero turn/pitch factor 0.2286; airborne window 1.211 s | TRANSLATE | next (closest system, gate absent in JC3) | 9123 | A-air take | - | `tmp/freebuff/reports/air-control-and-ram-assist-plans-v2.md` |
| T-SR1 | Self-right: `DriverLean.righting_torque` 2000 + stabilizer atom (no car ships DriverLean); BmAK stuck 2.0 s / flip 0.5 s, 0.707 test | TRANSLATE | next | 9124; StuckTime variant UNKNOWN | flip take | - | `tmp/freebuff/reports/stuck-flip-build-plan-merge.md` |
| T-DM7 / T-RA1 | Contact damage speed band; ram assist (`ImpactRoadAssist*`, `PMDodge*`, `KillFlipTorque` -200 shipped) | TRANSLATE | next / blocked (no member at any layer) | 9123 composition | ram take | M | `ledger T_ROWS T-RA1`; `tmp/freebuff/reports/audit-ram-assist-plan-numbers.md` |
| T-MD5 / T-MD6 | Battle speed curve / cap (needs second value set = variant) | TRANSLATE | blocked (waits on D-2/second entity) | 9130 | battle takes | - | T_ROWS |
| T-MD7 | Six battle drive/slip factors (drive 500, lat slip 0.75, long 1.25, steer 1, trailing -0.25, Z 20 cm); two slip scales have no member | TRANSLATE | blocked | 9122 | battle drive | - | T_ROWS T-MD7 |
| T-MD8 | Turn on the spot: no data carrier (TANKTURN) | TRANSLATE | blocked / named omission (conflicts with the project rule "never JC3 has no system") | closest-system rule | battle pivot | M | T_ROWS T-MD8; `tank-pivot-values-for-battle-mode-turn-plan.md` |
| T-MD13 | Transformation pose | TRANSLATE | blocked | 9130 | - | - | T_ROWS |
| T-22 / T-P3 / T-CO1..3 | Collision translation re-pinned on the drivable asset: 2 bodies / 3 boxes / 1 constraint; chassis 690.305x374.536x207.5 cm, 679.585x345.688x103.5, pod 166.177x189.365x39.8 at 4 deg | TRANSLATE | REOPENED 2026-11-07 (rows re-pinned, plan done, not built) | 9141 | B-10, Q kerb/ram | M | `Working/Translation/T22_REOPEN.md`, `Research/BatmobileGrab/COLLISION_WHERE.md` |
| NEW-HDL-5 | Ledger rows for handling facts only in plans: flip idle timer, 4WD, spin-in-place gate (21.6 km/h), battle yaw-toward-aim (`BattleModeSteerAngleFactor`, `BattleModeMaxSteering` 80, `BattleModeStopAndTurnAngleMoving` 90, YawOffset 0), remote/water/flip rows | TRANSLATE | todo (map: not in T_ROWS handling ids) | 9033 review of v2 apply | build cards | S | `tmp/freebuff/reports/bm-moving-yaw-toward-aim.md`, `four-wheel-drive-and-spin-in-place-build-plan.md` |
| NEW-HDL-6 | Explicit 4WD decision: JC3 has no steering_type enum beyond FrontSteered and one driveline; define the closest composition (per-axle slip/grip asymmetry + drift yaw block) and state the residual gap. No "JC3 has no system" | TRANSLATE | todo | 9122 | battle drive | S | `four-wheel-drive-and-spin-in-place-build-plan.md` |
| NEW-HDL-7 | Re-derive T-E5 honestly: today Cd 0.55 predicts 267 km/h terminal (+32 to +43 km/h boost -> about 300-310), so the 336 km/h lore number is not reached without a back-solved drag (withdrawn, correction 8391). Choose a legitimate lever set (final drive, rpm band, boost thrust) and record which values are lore and which are tune | TRANSLATE | todo; needs operator ruling | operator ruling | A2 pass meaning | M | `Working/Q/PREDICTIONS.md` D-2, `correction-8391-top-speed-label.md` |
| NEW-HDL-8 | Pursuit-vs-battle value-set table (all per-mode members: stiffness 3000/750, damping 300/20, bias, speed cap 600 cm/s turning mode, `BattleModeVSpeedCurve`) as one generated ledger for the mode-pair build | TRANSLATE | todo | 9121, 9122 | 9130 | S | `Research/BatmobileGrab/MODES.md`, `DRIVE_MODES.md` |
| NEW-HDL-9 | Pivot / spin handling in pursuit: the stick-spins-the-car rule at 21.6 km/h gate vs JC3 drift block; predicted yaw rate stored for pilot | TRANSLATE | todo | 9122 | pilot cards | S | `four-wheel-drive-and-spin-in-place-build-plan.md` M1 |

### 1C. BUILD (the RC5 chain; private trees; RC4 never edited)

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| 9100 | RC5 scaffold and branch-merge script `bm_rc5.py` (branch records, receipt derived not hand-written) | BUILD | queued | 9001-9004 repairs, review-v2-apply-wave | everything below | M | `tmp/freebuff/queue/9100-rc5-scaffold-and-merge-script.txt` |
| B-24 / 9120 | Write the 14-15 handling cells into `Builds/bm-RC5-handling` with `rc5_handling.py --write/--check`, read back through the `.toc` | BUILD | queued | 9100, review-v2-apply-wave | 9121-9124, 9130, V-05 | M | `GRAB_BACKLOG.md` B-24, queue 9120 |
| NEW-HDL-10 | Reconcile brake/handbrake cells first: `min_time_to_block` "5 unsourced, 1 belongs elsewhere" per 9120 brief | BUILD | todo (inside 9120) | - | 9120 | S | queue 9120 |
| B-22 / 9121a | Droop and up-travel: length 0.40, `max_length_offset` 0.30 both axles, min_length 0, droop 100 cm composed (not dropped) | BUILD | queued (todo card) | 9120 | A6 | S | `GRAB_BACKLOG.md` B-22, `Research/specs/B-22.md` |
| B-23 / 9121b | Pursuit spring 750, damping 20, stationary bias 5 as a variant table (750 rejected as strength: 172% sag) | BUILD | queued | 9121a, mode pair | 9130 | S | `GRAB_BACKLOG.md` B-23, `Research/specs/B-23.md` |
| 9122 | Drive modes: 4WD, spin-in-place, battle auto-turn to camera, per-mode variant table, torque substitute checker, predicted yaw rates | BUILD | queued | 9120 | 9130 | M | queue 9122 |
| 9123 | Air control + ram assist (AirControl members, dodge, ram damage, kill flip; force-pulse boost/shove; authored script graph where JC3 is short) | BUILD | queued | 9120, air-control v2 plans | air/ram takes | M | queue 9123, `force-pulse-as-boost-and-shove-carrier-plan.md` |
| 9124 | Flip recovery (idle timer + thrusters), water-entry teleport, remote range 100/150 m and LB homing | BUILD | queued (remote/homing may be halted with written reason) | 9120 | survival takes | M | queue 9124, `flip-recovery-idle-timer-and-thruster-plan.md` |
| 9130 / B-12 | Mode pair and swap: rebuild pursuit+battle on RC5 base, T-MD13 stance, T-MD8 turn, T-MD14 audio switch, entity-swap trigger from exe study | BUILD | queued; B-12 `todo` | 9121, 9122, 9050 (exe entity swap), collision-mode plan | battle takes | L | queue 9130, `Research/JC3Grab/ENTITY_SWAP.md` (9050 queued) |
| 9050 | Exe study: who consumes an entity swap | GRAB/BUILD | queued | - | 9130 | M | queue 9050 |
| B-10 / 9141 | Collision: add the 2 missing boxes (chassis box 1, pod) at decoded centres within 5 cm, reclaim hull slots from 14 unbound bumper-compound instances, carry or name the constraint writer | BUILD | queued; B-10 REOPENED | 9100, box-flag, 9130 for mode meshes | Q-3 ram/kerb, V-02 | M | queue 9141, `Working/Translation/T22_REOPEN.md` |
| B-10b / B-10c | LOD2 world hull / convex hull of render mesh | BUILD | built, Q pending; superseded in intent by the reopen (map) | - | - | - | GRAB_BACKLOG tracker B-10b/c |
| HINGES | Hinged physicsc copy (13 constraints) for turret/cannon hinge indices | BUILD | done (copy) | - | RC3-parts | - | `Working/Collision/batmobile_hinged.physicsc` |
| NEW-HDL-11 | Mass and inertia re-check once G3-07 can read live bodies: the built `hknpShapeMassProperties` after adding boxes is consistent with 6000 kg and chosen inertia | BUILD | todo | G3-07 | A3/A4 trust | M | `Research/BatmobileGrab/INERTIA.md` |
| NEW-HDL-12 | Wheel/tyre grip tuning branch (T-R1 3.0, T-G5, slip pair) as its own tree so tyre retunes do not touch the handling merge | BUILD | todo | 9120 | tune loop | S | T_ROWS |
| NEW-HDL-13 | Afterburner physics glue: boost duration 2.0 s, cooldowns (quick-recharge), boost-to-drift interaction (`DriftingBoostCooldown` 1.5 s), shared with the weapons/FX landmark | BUILD | todo | 9120 | A2/A9 | S | T_ROWS T-B*, `Research/BatmobileGrab/MODES.md` |
| 9190 | Merge all RC5 branches into `Builds/bm-RC5` (module overlaps, e.g. `custom_land_global` carries wheel skew_health AND handling set) | BUILD | queued | all branches | 9191/9192 | M | queue 9190 |

### 1D. VERIFY (offline only)

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| V-05 / v05_driving | Driving predictions, 6 checks (D-1..D-6) | VERIFY | done as document; red on T-ST7 until handling built | 9120 | Q-2 | S | `Working/Q/PREDICTIONS.md`, `Tools/scripts/v05_driving.py` |
| V-02 | Geometry / collision census (post 9141: 3 of 3 boxes within 5 cm) | VERIFY | partial: 2 of 3 boxes missing today; shipped file placement 0.25 cm | 9141 | gate | S | `tmp/freebuff/reports/verify-v02a-silhouette-census-collision.md` |
| B-10-extents / CO-audit | Shipped hull 349.5x227.1x702.5 cm; 3 collision rows carried wreck-vs-drivable error | VERIFY | done | - | - | - | `Working/Collision/BM_EXTENTS_CHECK.md`, `Working/Translation/COLLISION_SOURCES_AUDIT.md` |
| 9191 / 9192 | RC5 verify groups A and B (readback, wiring, geometry, predictions, install dry runs) | VERIFY | queued | 9190 | 9193 | M | queue 9191, 9192 |
| NEW-HDL-14 | Stale-checker repair already done as 8396; re-run for RC5 and add an A9 row to `v05_driving.py` (no D-row exists for A9) | VERIFY | todo | - | A9 band | S | `pilot-card-driving-takes.md` section 5.5 |
| NEW-HDL-15 | A "yaw tool": frame-based yaw/turn-radius measurement so A3/A4 stop being UNKNOWN for radius and sub-0.2 s lock time | VERIFY | todo | - | A3, A4 | M | `pilot-card-driving-takes.md` (A3 UNKNOWN until yaw tool) |
| NEW-HDL-16 | Height/bounce channel so A6 landing bounce is not UNKNOWN (no height channel) | VERIFY | todo (depends on oracle) | G3-07 | A6 | M | `pilot-card-driving-takes.md` section 7 |
| 9193 | Gate VX for RC5 + `APPROVAL_REQUEST_RC5.md` | VERIFY | queued | 9191/9192 | operator approval | S | queue 9193 |
| 9194 / 9199 | Refresh pilot cards for RC5 (flip, water, remote, controls); final desk review | VERIFY | queued | 9193 | operator | S+S | queue 9194, 9199 |

### 1E. PILOT / TEST (needs the operator; in game)

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| NEW-HDL-17 | Operator writes `tmp/freebuff/APPROVED_Q.txt` (the only unlock) | PILOT | todo | 9199 | every TEST row | S | `Working/Q/APPROVAL_REQUEST.md`, `tmp/freebuff/queue/8600-*` |
| Q-1 | Static session: spawn, enter/exit, looks, standstill checks | TEST | queued | approval | Q-2 | M (~45 min) | `tmp/freebuff/queue/8601-*`, APPROVAL_REQUEST |
| Q-2 A1 | 0-100 baseline (16.4 s +/-5%) | TEST | queued (one prior measurement on test-085, build since changed) | approval | - | S | `pilot-card-driving-takes.md` |
| Q-2 A2 | Top speed, boost off then on | TEST | queued (take A2) | approval, NEW-HDL-7 | T-E5/T-B2 | S | `QA1_RESULTS.md` section 7 |
| Q-2 A3 | Constant-radius corner 60/100 km/h (3.52 m / 13.82 m predicted) | TEST | queued (radius UNKNOWN w/o yaw tool) | approval, NEW-HDL-15 | T-ST1 | S | `Working/Q/PREDICTIONS.md` D-4 |
| Q-2 A4 | Steering lock time (0.25 s / 0.091 s ruling) | TEST | queued | approval, 9120 | T-ST7 | S | `PREDICTIONS.md` D-5 |
| Q-2 A5 | Braking 100-0 (101.5-110.2 m) | TEST | queued (partial QA-1) | approval | T-K1 | S | `PREDICTIONS.md` D-3 |
| Q-2 A6 | Kerb/pothole/landing at 3 speeds (<=1 rebound) | TEST | queued | approval, 9121 | T-S* | S | `pilot-card-driving-takes.md` 5.3 |
| Q-2 A7 | Handbrake drift + release (friction 4, ramp 0.3 s, 0.625 aligning) | TEST | queued | approval, 9120 | T-DR1/K3/K4/ST5/ST6 | S | `PREDICTIONS.md` D-6 |
| Q-2 A9 | 0-100 with boost (6.00 m/s^2 +/-25%) | TEST | queued | approval; no D-row | T-B1/B3 | S | `pilot-card-driving-takes.md` 5.5 |
| NEW-HDL-18 | Battle-mode takes: nose swings to camera with no steer input; stick-direction movement; 4WD feel; spin-in-place; battle speed curve | TEST | todo | 9130, 9122 | mode sign-off | M | `bm-moving-yaw-toward-aim.md`, memory `bmak-gameplay-facts.md` |
| NEW-HDL-19 | Air-control take (airborne rotation rate band) and ram-assist take (impulse band) | TEST | todo | 9123 | - | S | queue 9123 |
| NEW-HDL-20 | Flip-recovery take (roof/side idle -> thrusters right the car after delay) and water-teleport take | TEST | todo | 9124 | - | S | queue 9124, memory facts |
| NEW-HDL-21 | Collision take: curb, wall, traffic car side/front/back vs expected hull; O-box scale; ram | TEST | todo | 9141, oracle ideally | B-10 close | S | `RESET_FINDINGS.md` sections 4, 6 (R-3) |
| Q-3 | World and combat session (ram, 5-star, water, tether, traffic) | TEST | queued | approval, Q-2 | Q-4 | M (~45 min) | queue 8603 |
| Q-4 | Fix-loop triage: failed bands -> fix cards, no compromise fixes | TEST | queued | Q-1..Q-3 | rebuilds | M per round | queue 8604 |
| NEW-HDL-22 | Tune loop (the iterative core): fix card -> new branch tree -> merge -> verify -> install -> retake -> compare; repeat per failing band | TEST | todo | Q-4 | release | L | `GRAB_BACKLOG.md` section 9b Q-4 |
| NEW-HDL-23 | Player-feel sign-off: operator, who has played BmAK, drives pursuit and battle and confirms feel row by row | TEST | todo | tune loop | release | M | `OPERATOR_PRIORITIES.md`, memory `lore-accuracy-priority.md` |
| Q-5 | Showcase recording | TEST | queued | Q-4 | release | S | queue 8605 |

### 1F. RELEASE

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| NEW-HDL-24 | Freeze final handling/collision values into `COMPROMISES_T.md` with LORE-EXACT vs COMPROMISE per row and operator sign-off | RELEASE | todo | tune loop | RC final | S | `Working/Translation/COMPROMISES_T.md` |
| NEW-HDL-25 | Final RC packaging (`bm_rc5.py` receipt `complete:true` only when not_done empty by derivation), install/rollback proven on a copy, save-backup note | RELEASE | todo | all | ship | M | queue 9190; `Builds/bm-RC4/install.ps1` |
| NEW-HDL-26 | Release notes: values with their source class (decoded/derived/assumed), the assumed 336 km/h label, any remote/homing halt reasons | RELEASE | todo | NEW-HDL-24 | ship | S | `STATUS.md` |

## 2. (a) DONE with evidence

- Grab side of collision: G3-01, 01c, 01d, 01e, 16 (drivable asset = 2 bodies / 3 boxes / 1 constraint), `Research/BatmobileGrab/COLLISION*.md`. G2-30 writer proven byte-identical: `Research/JC3Grab/PHYSICS_WRITE.md`.
- G1-1 offsets 423/423; BmAK engine, steering, suspension, drift, battle-mode members named (`BMSDK_OFFSETS.json`, `MECHANICS.md`, `MODES.md`, `DRIVE_MODES.md`).
- Absence proofs (no friction, antiroll, CoM, aero, brake-lock, input-exponent member in BmAK): T-R1, T-S4, T-M3, T-A2, T-K2, T-ST4 rows.
- T-ST7 un-blocked: refutation (`Working/Translation/T_ST7_EVIDENCE.md`), operator ruling 0.25 s / 0.091 s (`DECISIONS_NEEDED.md`, T_ROWS).
- T-S6 bridge: length 0.40 m, strength 13.5 s^-2, 14/14 oracles (`t_s6_bridge.py`, `suspension-unit-bridge.md`).
- Plans v2 for air control, ram assist, stuck-flip, 4WD/spin, battle yaw, tank pivot (all in `tmp/freebuff/reports/`, desk-only).
- Prediction sheet for 6 driving checks (`Working/Q/PREDICTIONS.md`), pilot cards for A1-A9 (`pilot-card-driving-takes.md`).
- QA-1 partial: 0-100 16.4 s, brake 3.5-3.8 m/s^2, gear-1 shift 67 km/h (test-085 only, now superseded builds).
- Collision file-level: shipped hull 349.5 x 227.1 x 702.5 cm, 1232 child verts inside AABBs; placement 0.25 cm on payload `fda78f4d` (file vs file only).
- Hinged physicsc copy with 13 constraints.

## 3. (b) BLOCKERS, root first

1. **No operator approval + test ban** (`APPROVED_Q.txt` absent). Nothing TEST can start. Root of all verification. Even with approval, RC4 is the wrong payload; RC5 does not exist.
2. **9100 RC5 scaffold** (and its repairs 9001-9004, 9033 review) gates every BUILD row. Not started.
3. **B-24 / 9120 handling cells unbuilt** gates 9121-9124, 9130, V-05 green, A4/A7/A5/A6.
4. **Mode pair (B-12 / 9130)** gates every battle-mode value (T-MD5/6/7/13/14, battle speed curve, B-23 pursuit spring) and relies on 9050 (does the exe let an entity swap on LT?). The earlier refusal to merge rested on a second entity "nothing could select" (queue 9130).
5. **No runtime oracle (G3-07 open)**: cannot answer "does the game read our .physicsc", frame equality, live mass; blocks honest collision close (RESET_FINDINGS section 4: "None of these may be answered by another build-and-look") and A6 bounce, A3 radius.
6. **Collision shapes**: 2 of 3 boxes without a shape instance, 0 free hull slots of 54, constraint writer absent (`T22_REOPEN.md`). 9141 plans reclaiming 14 unbound instances; unproven.
7. **JC3 limits that need a closest-system composition, not an omission**: turn-on-the-spot (T-MD8 blocked, TANKTURN no carrier), 4WD, per-mode torque split, droop (no member), airborne gate, ram assist (no member at any layer, T-RA1 blocked). Native stub `SetDriveMode` is UNKNOWN.
8. **Top speed 209 mph**: label assumed; honest model gives ~267 km/h boost off. Needs an operator ruling on lever set (NEW-HDL-7). No BmAK member.
9. **Human-in-loop bottleneck**: BmAK ground truth (0-100, turn radius, flip delay) not in files; operator footage or live sampler needed (NEW-HDL-2/3). BmSDK hook offset invalid on this exe (QUEUE_MAP).
10. Process: serial apply chain (ledger races), lane limits, similarity-guard stripping of boilerplate briefs (QUEUE_MAP 15:45Z), short sessions (7-15 min) so large cards may die before writing reports (8134, 8158 precedent).

## 4. (c) Open questions only a player can answer (BmAK vs JC3 driving feel)

Already answered (memory `bmak-gameplay-facts.md`): battle nose swings to camera; flip recovery thrusters fire after resting; water teleports; no crash damage; steering response at speed is NOT known by operator.
Still open:
1. Pursuit mode: does the left stick at standstill spin the car in place (BmAK "Power Slide"/spin)? At what speed does that stop and normal steering begin (decoded gate 21.6 km/h)?
2. How long after the car lands on its roof/side before the thrusters fire (decoded `BatmobileStuckTimeMax` 2.0 s vs `BatmobileStuckTimeFlip` 0.5 s, which one is read is UNKNOWN)?
3. Is 209 mph reached only with the afterburner held, how long does a full boost last (decoded BoostDuration 2.0 s), and does speed stay near that after release?
4. How hard is braking at 100 mph: does it stop in about 100 m (derived 3.5-3.8 m/s^2) or feel stronger (BmAK brakes are known to be very heavy)?
5. Does the car feel heavy or planted in corners (lateral grip) versus drifty; how much does the handbrake slide, and does it snap back after release?
6. Landing from ramps: does the car bounce or stick? Does the nose pitch on hard braking and launch?
7. Battle mode: how fast is the strafe at top (600 cm/s turning-mode cap decoded), is movement instant or does it ramp (BattleModeVSpeedCurve), does the car turn in place when stick is released?
8. Air control: how much yaw can you apply mid-air; can you pitch it?
9. Ram assist/dodge: what actually triggers it (dodge thrusters via stick+button), how far does it shove?
10. Steering response at speed (operator "does not know"): can anyone confirm high-speed steering reduction, e.g. from a capture?
11. Accept/reject: if JC3's tyre model cannot reproduce BmAK's grip, which of "grippy", "drifty", or "heavy" matters most to you? (Rule says lore wins; this is only to order tuning.)

## 5. (d) Risks

- **Tune loop in game (largest risk).** Every iteration = fix card -> branch tree -> `bm_rc5` merge -> V-01..V-06 -> install of a 383 MiB drop (receipt: 9 files, 401.7 MB) -> operator drive -> numbers -> back. Operator-limited at roughly 1-3 loops per day, each 45-90 min. Handling has about 15 interacting members; one change (grip) moves A3, A4, A5, A7.
- **Verification is instrument-limited.** No yaw tool, no height channel, no rpm channel, speedometer is HUD-only; A3/A4/A6/A7-angle are UNKNOWN by design. Passing a band does not equal BmAK feel.
- **Targets are partly invented.** Mass 6000 kg, inertia 4/2.6/1.2, CoM -0.3, Cd 0.55, 336 km/h are declared/assumed, not BmAK-decoded (G3-10c2). Violates lore-accuracy priority; each tune can only match a guessed target.
- **Predictions already known wrong or red:** top speed prediction 267 km/h vs 336 label; v05 D-4/D-5 show the RC4 steering times outside the ruled goal; T-S3 0.70 vs 0.40 m conflict.
- **Status drift.** STATUS says test-090 is the live pair; GRAB_BACKLOG says test-091 holds A/B2/B3/B4; bm-RC4 handling tree is not the same as installed tests. The ledger has 199 rows vs "198"/"216"/"221" denominators in different files. Reconcile before trusting counts.
- **Collision is a coupled unknown**: unknown whether the game reads our `.physicsc` at all (RESET_FINDINGS section 4); user reported collision off on sides, front, back before the reopen; fixing 3 boxes may not change that.
- **Exe-resident behaviour** (SetDriveMode, camera->aim, righting) is not serialised; closest-system substitutes may not reproduce the feel regardless of numbers.
- **Mode swap on an unproven trigger** (9050/9130). If no clean trigger, B-12 fails and every battle-mode value has no home.
- **Hybrid car / Rebel Drop**: entity replaces `v0300` sportsmuscle debug; AI/traffic share vehicle modules, so a handling edit might leak (flagged only; see world landmark).
- **Process fragility**: the apply chain is serial; briefs run 7-15 min, large builds (9130, 9190) may exceed one session and need splitting.
- **Remote/homing/summon boundaries**: halting them needs written reasons (memory); otherwise they extend scope.

## 6. (e) Remaining effort

Assumptions: ~100 small-model briefs/day, one brief approx one agent-session, ~35% rework/split rate given history (stripped, re-split briefs); human operator for every TEST row.

| phase | agent-sessions | calendar days | operator hours |
|---|---:|---:|---:|
| GRAB leftovers (T-26, NEW-HDL-1/4, G3-07b, G3-06f, G3-01b, oracle tool build G3-07 as ~15 sessions incl. memory tooling) | 35-45 | 1 (oracle itself is the long pole: 3-5 days with operator-side runs) | 2-4 (JC3 runs for oracle validation) |
| TRANSLATE leftovers (NEW-HDL-5..9, 7 ruling, T-S3 conflict, mode-value table) | 12-18 | 1 | 0.5 (rulings) |
| BUILD: 9100, 9120, 9121-9124, 9130, 9141, 9190 plus NEW-HDL-11..13 and rework | 30-45 | 3-5 (chain depth ~9 serial steps; ledger-race serialisation) | 0 |
| VERIFY: 9191-9194, 9199, NEW-HDL-14..16 | 12-18 | 1-2 | 0.5 |
| First TEST pass Q-1/Q-2/Q-3 | 5 (cards, result entry) | 1-2 (after approval) | about 2.5-3 h |
| Tune loop (NEW-HDL-22), estimated 5-10 rounds for handling+collision | 10-20 sessions per round (triage, fix card, branch, merge, verify) = 50-200 | 14-28 (operator-bound, 1-2 rounds/day best case; plan 3-4 weeks) | 10-25 h |
| Feel sign-off, release prep (NEW-HDL-23..26) | 8-12 | 2-3 | 3-4 h |
| **Total (this landmark only)** | **about 150-350 sessions** | **about 4-6 weeks, of which roughly 5-7 days is desk and the rest the in-game tune loop** | **about 20-40 h operator** |

Fastest honest path: approve test ban lift immediately after RC5 passes VX; run A1-A9 once on a first RC5 install; then a tight loop. Desk work can stay ahead (about 1 week) but cannot shorten the loop.

## 7. Source map (read)

`GRAB_BACKLOG.md` sections 1.2, 1.5, 6 (G2-21, G2-30), 6b (G3-*), 7 (T-22, T-26), 8 (B-10, B-22..B-24), tracker lines ~1809-2100; `STATUS.md`; `RESET_FINDINGS.md`; `Working/Translation/T_ROWS.jsonl`, `QA1_RESULTS.md`, `COMPROMISES_T.md`, `DECISIONS_NEEDED.md`, `T22_REOPEN.md`; `Working/Q/PREDICTIONS.md`, `APPROVAL_REQUEST.md`; `tmp/freebuff/QUEUE_MAP.md`, `tmp/freebuff/queue/9100..9199, 8600-8605`; `tmp/freebuff/reports/` (air-control-and-ram-assist-plans-v2, stuck-flip-build-plan-merge, tank-pivot-values..., four-wheel-drive..., bm-moving-yaw-toward-aim, drive-mode-torque..., collision-missing-shapes-recount, pilot-card-driving-takes); `Research/BatmobileGrab/MODES.md`; memory `bmak-gameplay-facts.md`; tail of `MODLOG.md`. Not read in full: PHYSICS.md (BmAK), Working/Collision*, T1_TRANSLATION.md, T_S6B.md, BLOCKED_PROPOSALS.md, T_ST7*.md beyond quotes. Counts for T-rows not individually verified against builds (the ledger is known to drift from the builds, `Working/Translation/LEDGER_AUDIT.md`).
