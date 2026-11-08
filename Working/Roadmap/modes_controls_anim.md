# Landmark map: MODES, CONTROLS & ANIMATION (as of 2026-11-08)

Read-only mapping. Nothing in the project was edited. Evidence labels: decoded = a project file says it;
UNKNOWN = no file settles it (named settler given). Pretrained JC3 knowledge was not used as evidence.

Path abbreviations: GB = `E:/Modding/JC3-Batmobile/GRAB_BACKLOG.md`; BG = `Research/BatmobileGrab/`; JG = `Research/JC3Grab/`;
R = `tmp/freebuff/reports/`; Q = `tmp/freebuff/queue/`; WT = `Working/Translation/`; MEM = `C:/Users/User/.claude/projects/E--Modding-JC3-Batmobile/memory/`.

## 0. Where this landmark stands in one paragraph

GRAB and TRANSLATE are desk-complete for modes/controls/animation (every G1/G2/G3-02 card done, T-12/T-13/T-15 done, 15 T-8 part rows,
85 interaction objects placed). BUILD produced RC4 as the **pursuit set only**: no joints on turret/cannon (RC4 did not use `bm_parts_v2.py`,
`R/build-d02-parts-split.md` line 52), no mode pair merged (`Builds/bm-RC4-modes/{pursuit,battle}` differ in exactly 2 `.vmodc`,
`R/aafdiff-pursuit-battle.md`), no keymap shipped (the RC4 drop manifest has one `settings/` entry, `spawn_vehicle_defs.bin`;
`R/controls-entry-exit-eject-plans-v2.md` section 4), canopy/hatches/yoke/jet are not cut as parts (P-06/07/08/13 have no joint,
`R/verify-v02b-pose-renders-lights.md`). The RC5 campaign (briefs 9100-9199) is where these get built; of this landmark's briefs 9122, 9130, 9170, 9172
**all four are queued, none has a report** (no `R/rc5-drive-modes-and-yaw.md`, `rc5-mode-pair-and-swap.md`, `rc5-controls-entry-exit-eject.md`,
`rc5-moving-parts-animation.md`). Nothing has been tested in game for any of it (`tmp/freebuff/APPROVED_Q.txt` absent; `STATUS.md`: 0 of 216 rows behaviour-verified).
The two structural unknowns that can sink the landmark are: **(1) can JC3 switch a vehicle's mode at runtime** and **(2) can a mod remap/scope vehicle input**; section (b) separates evidenced from UNKNOWN.

## 1. Task table

Status words: done / partial / queued (a brief exists in `Q`) / todo (no brief) / blocked. Sizes: S <=1 session, M 1-3, L 1-2 weeks.

### 1A. Decisions and gates (operator)

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| D-2 | Re-resolve pursuit/battle architecture: (a) two Rebel Drop entities, (b) hybrid, (c) runtime selector. Hybrid withdrawn 2026-11-06; operator answer not recorded in the tracker (brief 9130 presumes (a)) | TRANSLATE | blocked (operator) | operator | B-12, 9130, T-MD5/6/7/8/13/14, NEW-MOD-10 | S | GB 11 D-2; `R/apply-mode-switch-rows.md` |
| D-11 | Controls rule: enter = JC3 Y; exit = LB; all else BmAK; pause + commlink keep JC3 | TRANSLATE | done | - | G3-02*, 9170 | S | GB 11 D-11; `MEM/control-priority.md`; `BG/CONTROLS_MENU_SCREENS.md` |
| NEW-MOD-1 | Operator ruling on whether a JC3 native hook (R17, DLL proxy) is allowed. Today "R17 is not a build route under the current rules"; it is the only route the files name for an in-place LT-hold mode switch and for vehicle-scoped input | TRANSLATE | blocked (operator) | operator | NEW-MOD-11, NEW-MOD-12, NEW-MOD-13 | S | `R/new-behaviour-routes-survey.md` lines 58, 316, 328, 356 |
| NEW-MOD-2 | Operator: confirm eject input (BmAK double-press A "Eject Into Glide" per menu screenshot vs the older "hold A" wording in `MEM/eject-mechanic-scope.md` and GB MOD-3 "hold-to-eject"); fix the stale text | TRANSLATE | todo | operator | 9170, T-13 refresh | S | `BG/CONTROLS_MENU_SCREENS.md` foot; `MEM/lore-accuracy-priority.md` update note; GB 1.6 MOD-3 |
| APPROVED_Q | Operator writes `tmp/freebuff/APPROVED_Q.txt` (lifts the test ban); Q briefs 8600-8605 still point at RC4 and need repointing (9193 recommends) | TEST | blocked (operator) | RC5 gate VX | every in-game row below | S | `Working/Q/APPROVAL_REQUEST.md`; `tmp/freebuff/QUEUE_MAP.md` RC5 section |

### 1B. GRAB

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| G1-10 | Animation sequences (253/253, bones, lengths, mechanism class) | GRAB | done | - | T-12 | M | `BG/ANIMATIONS.md`, `.json` |
| G1-11 | Skeleton + vertex-to-bone ownership (180 bones) | GRAB | done | - | B-02 | M | `BG/BONES.md` |
| G1-12 | Pursuit vs battle pose deltas (bone world deltas, transform clip 2.000 s / 61 frames) | GRAB | done | - | T-MD13 | S | `BG/POSES.md`; `R/battle-mode-transform-plan.md` |
| G1-13 / G1-19 | Sockets in JC3 space; cockpit + `Driver` placement | GRAB | done | - | T-13 | S | `BG/SOCKETS_JC3.md`, `BG/COCKPIT.md` |
| G1-21 | Modes and transformation values (107 declared / 46 serialised / 61 no value) | GRAB | done | - | T-15, T-MD* | S | `BG/MODES.md`; GB tracker G1-21 |
| G2-13 | Turret and cannon mechanics of JC3 tanks | GRAB | done | - | T-12 | S | `JG/TURRET.md` |
| G2-14 / G2-15 | Moving-part behaviours (who drives each variable) / door parts | GRAB | done | - | T-12 | S | `JG/MOVING_PARTS.md`, `JG/DOORS.md` |
| G2-18 / G2-19 / G2-20 | Interaction points; driver seat + pose; exit/bail/eject (0 launch members in 4,832 exits) | GRAB | done | - | T-13 | M | `JG/INTERACTION.md`, `JG/SEAT.md`, `JG/EJECT.md` |
| G2-21 | Turn-on-the-spot: 5 candidates refuted; no tank-only driving member; pivot code-side | GRAB | done (pivot itself UNKNOWN) | - | T-MD8 | S | `JG/TANKTURN.md` |
| G3-02 / 02b / 02c / 02d | BmAK controls: ini bindings, script consumers, native path, live runtime (LT hold = battle, LB exit+enter, A eject, B immobiliser CONFIRMED live) | GRAB | done (X/Y not sampled; thresholds UNKNOWN) | - | 9170, 9130 | M | `BG/CONTROLS.md`, `CONTROLS_CONSUMERS.md`, `CONTROLS_NATIVE.md`; GB tracker G3-02d |
| G3-02e | Who writes mode flags `[vehicle+0x11d8]`, meaning of 0.707, native route input->exit | GRAB | partial | needs running BmAK | NEW-MOD-4 | M | `BG/CONTROLS_NATIVE2.md` (0.707 = `[Pawn.Mesh+0xd8]`; no native input->exit route) |
| G3-02f / f2 / f3 / g / h / i / j | Sampler fields, unknowns, merged bindings, keyboard, DrivingMode bodies, eject velocity = (0,0,0) on the car | GRAB | done (2 UNKNOWN stay: U2 writer, U7 producer) | - | 9170 | M | `BG/SAMPLER_FIELDS2.md`, `BINDINGS_MERGED.md`, `DRIVINGMODE.md`, `EJECT_VELOCITY.md` |
| G3-08 | JC3 vehicle input model: keymap is global; no entity references it; BmAK-only actions have no JC3 action (verdicts are name-level) | GRAB | done (caveat) | - | 9170 | M | `JG/INPUT.md`, `JG/INPUT_D11.md`, `JG/EJECT_MAP.md` |
| 9050 | JustCause3.exe static analysis: runtime vehicle entity replace/spawn path (U1) | GRAB | queued | - | 9130, NEW-MOD-11 | M | `Q/9050-exe-entity-swap-consumer.txt`; `R/mode-toggle-runtime-swap.md` |
| NEW-MOD-3 | JC3 exe static decode of the vehicle-action consumers: who reads `USE_VEHICLE_MOD`, `ENTER/EXIT_VEHICLE`, `OPEN_PARACHUTE`; any hold/double-press field in the input layer (0 hold/duration words in 145+104+249 rows) | GRAB | todo | - | NEW-MOD-11, NEW-MOD-12, 9170 | M | `R/controls-entry-exit-eject-plans-v2.md` U2/U3/U4; `R/mode-swap-trigger-closest-system-plan.md` U3 |
| NEW-MOD-4 | BmAK LT hold-time/threshold and the +-0.707 compare; mode-change timing (U6) | GRAB | todo (needs runtime) | Steam copy or BmSDK GOG port | NEW-MOD-11 pilot band | M | `R/mode-swap-trigger-closest-system-plan.md` U6; `OPERATOR_PRIORITIES.md` Steam-copy section; `R/bmsdk-gog-copy-port.md` (22 addresses UNKNOWN) |
| NEW-MOD-5 | BmAK double-press window for A (`LastEjectFromBatmobileTime`; no constant in the body) | GRAB | todo (needs runtime) | same as NEW-MOD-4 | 9170 eject card | S | `R/eject-and-glider-landing-plan.md` row 2 |
| NEW-MOD-6 | BmAK post-exit car motion: pursuit breaks right, battle straight (no decoded member) | GRAB | todo | runtime | 9170 | S | `R/controls-entry-exit-eject-plans-v2.md` U1 |
| NEW-MOD-7 | BmAK turret yaw limit from code: P-01 +-60 is the extent of `Turret_Spin` (60.001 deg), possibly not a limit (Vulcan precedent: wrapped extent); cannon pitch is code-side (`MinTurretPitch` 0.0 / `MaxTurretPitch` 18.0), T-8 stores JC3 tank -5..20 | GRAB | todo | - | 9172, V-RC2-turret | S | `WT/P02_CANNON.md`; `R/turret-limits-check.md`; `WT/T8_PARTS.md` P-01/P-02 |
| NEW-MOD-8 | BmAK steering response curve / lock (`aTurn`=RightX vs menu "left stick"; curve undecoded) | GRAB | todo (partly handling landmark) | runtime | steering pilot card | S | `R/controls-entry-exit-eject-plans-v2.md` C3, U6 |
| NEW-MOD-9 | BmAK summon/remote values: `RBatmobileRemoteBm` 25 behaviours are untagged 30-byte records (call delay, spawn distance, stop radius UNKNOWN); remote 100 m static / 150 m stop is player-observed | GRAB | todo (runtime-only) | Steam copy | NEW-MOD-22 | M | `R/summon-and-arrival-plan.md`; `MEM/bmak-gameplay-facts.md` |
| G3-07 | JC3 runtime oracle (read-only memory inspector) to verify positions/bodies in Q | GRAB | open | - | position-type pilot checks (T-13 points, joints) | L | GB G3-07; `JG/RUNTIME_LAYOUT*.md` (root global, transform vs AABB, render: UNKNOWN) |
| NEW-MOD-10 | Operator task: Steam copy of BmAK (BmSDK supports Steam only; GOG port runs managed code but 22 UObject/FName addresses UNKNOWN) so the sampler can read LT/A/X/Y/summon/remote numbers | GRAB | blocked (operator) | operator | NEW-MOD-4, 5, 6, 8, 9 | S | `OPERATOR_PRIORITIES.md`; `R/bmsdk-gog-copy-port.md` |

### 1C. TRANSLATE

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| T-12 | Moving-parts translation, 15 rows P-01..P-15 (12 with an animated joint, 4 shipped hinge, 3 static: P-02, P-05, P-13) | TRANSLATE | done (v2 refresh needed) | - | B-02, B-04, 9172 | M | `WT/T8_PARTS.md`; `WT/PARTS_ANIM_COVERAGE.md` |
| T-13 | Interaction translation, 85 objects (77 placed 0.05-0.30 m from hull, 6 hijack dropped per D-9, `interaction.seat.passenger1` UNKNOWN) | TRANSLATE | done | - | B-05, 9101, 9170 | M | `WT/T9_INTERACTION.md`, `t9_interaction.json` |
| T-15 | Modes translation (hybrid one-set, 15 rows) | TRANSLATE | done but stale (D-2 reopened) | D-2 | NEW-MOD-11 | M | `WT/T11_MODES.md`, `t11_variants.json` (1 variant "hybrid") |
| T-MD1 | Afterburner = JC3 nitro `arcade.nitro_boost` (live since test-091) | TRANSLATE | done (next; no pursuit gate) | D-2 for gating | - | S | `Working/Translation/T_ROWS.jsonl` T-MD1 |
| T-MD2 | Immobiliser (EMP missile) disable chain; writer of `is_disabled_by_emp` UNKNOWN | TRANSLATE | partial | B-18 | - | S | T_ROWS T-MD2; `R/immobiliser-and-emp-trigger.md` |
| T-MD3 / T-MD4 / T-MD10 / T-MD11 | Ram immunity (`impact_damage_factor` 0); standard/boost torque curves; `ArmourModeDamageReduction` = 0; battle camera FOV 60 | TRANSLATE | done (keep) ; T-MD11 needs 2nd tune per variant | D-2 (T-MD11) | - | S | T_ROWS |
| T-MD5 | Battle top-speed curve (0->60, 600->40, 1200->30) | TRANSLATE | blocked | D-2, U1 | B-12 | M | T_ROWS T-MD5; `R/mode-switch-carriers.md` |
| T-MD6 | Turning-mode cap 600 cm/s = 21.6 km/h (no decoded cap member) | TRANSLATE | blocked | D-2 | B-12 | M | T_ROWS T-MD6 |
| T-MD7 | Battle steering/drive factors (6; two slip scales have no member) | TRANSLATE | blocked | D-2 | B-12 | M | T_ROWS T-MD7; `R/drive-mode-torque-arithmetic-substitute-plan.md` |
| T-MD8 | Turn on the spot (also T-BM1): backlog calls it "named omission"; STAGES.md forbids that | TRANSLATE | blocked | closest-system plan (NEW-MOD-12) | B-12 | M | T_ROWS T-MD8; `R/tank-pivot-values-for-battle-mode-turn-plan.md` (3 of 6 members have a receiver) |
| T-MD9 | Turret weapons in both modes (D-7: all weapons both modes) | TRANSLATE | done (next) | - | B-06 | S | T_ROWS T-MD9 |
| T-MD12 | Battle lamps -> `HeadLight` behaviour (T-L17..L20) | TRANSLATE | done (next) | - | B-03 | S | T_ROWS T-MD12 |
| T-MD13 | Transformation stance: part angles yes, animation no (2.000 s clip, mast +0.633 m translation not hinge-reachable) | TRANSLATE | blocked | D-2 | B-12 | M | T_ROWS T-MD13; `R/battle-mode-transform-plan.md` |
| T-MD14 | Battle audio (32 events + steering bed `0xD28CAFB1`; entry/exit stings need a transition consumer) | TRANSLATE | blocked | D-2, U1 | B-12, B-26 | M | T_ROWS T-MD14; `R/battle-audio-switch-event.md` |
| T-MD15 | The hybrid row (survives only if D-2 = b) | TRANSLATE | queued (disposition next) | D-2 | - | S | T_ROWS T-MD15 |
| T-PA1..T-PA9 | Parts in the built graph: wheel parts, light points, collision ids, `wheel_parts[]`, `door_parts[]`, constraint points, non-deformable list, orphan sockets, actor plumbing | TRANSLATE | done (epe/keep) ; T-PA5/T-PA6 stale after B-04 removed donor doors | - | B-05 | S | T_ROWS T-PA* |
| T-WLD8 / T-WLD9 / T-WLD10 / T-WLD11 | Entry points, exit points, stunt point nodes, stunt areas (roof/deck, press A) | TRANSLATE | done (epe/next) | - | 9101 | S | T_ROWS T-WLD8..11; `WT/T9_INTERACTION.md` |
| NEW-MOD-11 | Re-run `t11_modes.py` into schema 2: `pursuit` + `battle` row sets (B-12 precondition 2) | TRANSLATE | todo | D-2, 9050, NEW-MOD-1/3 | B-12, 9130 | M | GB B-12 preconditions; `Tools/scripts/b12_variants.py --check` |
| NEW-MOD-12 | Close "named omission" rows with composed closest systems: T-MD8 pivot (per-axle grip asymmetry + drift yaw-torque block, only 3 of 6 members have receivers); T-MD14 transitions; document the composition | TRANSLATE | partial (plans exist) | NEW-MOD-3 (native consumer) | 9122, 9130 | M | `R/tank-pivot-values-for-battle-mode-turn-plan.md`; `R/tank-pivot-donor-trace.md` |
| NEW-MOD-13 | Controls are not in the ledger: `T_ROWS.jsonl` has no T-IN* rows. Add one row per button (18 in the plan) with closest JC3 action + gap + build action | TRANSLATE | todo (9031 "driving and world rows" may cover part) | NEW-MOD-2 | 9170, T-23 counts | M | `R/controls-entry-exit-eject-plans-v2.md` section 1; `Q/9031-apply-v2-driving-and-world-rows.txt` |
| NEW-MOD-14 | T-12 v2: parts with no cut/joint yet: canopy P-06 (slides 72.48 cm + turns 12.493; hinge reproduces only rotation), hatches P-07/08, cannon P-02 (code-driven pitch), jet P-05, rear door, winch door; cannon recoil | TRANSLATE | partial (plans exist, not in ledger) | NEW-MOD-7 | B-02 extension, 9172 | M | `R/doors-canopy-trunk-plan.md`; `R/weapon-bay-animation-plan.md`; `WT/P02_CANNON.md`, `P05_JET.md` |
| NEW-MOD-15 | Reconcile requirements ANI-4 (turbine fan) and ANI-7 (steering yoke) with BmAK: P-13 says no yoke asset/bone in any of 324 packages; P-05 says a jet bone exists but no `engine_rpm` binding. Lore rule = do not invent | TRANSLATE | todo | - | 9172, Q-1 item 4 | S | `WT/P13_STEERING.md`; `R/jet-part-bone-driver.md`; GB 1.8 ANI-4/ANI-7 |
| NEW-MOD-16 | Eject translation to a build recipe: launch 13.0 m (`EjectUpDist` 1300 cm, node edit on `point.driver`-derived eject point), kick 7.649 m / 3.7333 s / 2.049 m/s forward; JC3 exits carry 0 velocity members; glide via parachute/wingsuit state | TRANSLATE | partial | NEW-MOD-2, NEW-MOD-5 | 9170 | M | `R/eject-and-glider-landing-plan.md`; `R/eject-sequence-build-steps-from-donor-exits.md` |
| NEW-MOD-17 | Update stale water rows: T-WLD13/T-WLD14 say "sinks / engine stalls"; operator says car teleports to land, engine fine | TRANSLATE | todo | - | 9124 | S | T_ROWS T-WLD13/14; `MEM/bmak-gameplay-facts.md`; `R/water-entry-teleport-closest-system-plan.md` |
| NEW-MOD-18 | Summon / remote / homing decision: operator memory allows halting remote + homing "with explicit written reasons" (Rebel Drop is the spawn; remote needs a separate gadget); either write the reasons or build summon via the AI-drive recipe | TRANSLATE | partial | operator confirm | 9124, 9173 | S | `MEM/bmak-gameplay-facts.md`; `R/summon-drive-in-closest-system.md`; `R/remote-and-autonomous-drive-plan.md`; `R/remote-control-range-static-overlay-plan.md` |

### 1D. BUILD

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| B-02 | Split body into movable parts (11 cut parts + 8 lamps; 99.97 % silhouette, 4791/4915 KB) | BUILD | done | - | B-04 | L | `Working/Appearance/build_parts/parts_manifest.json`; GB tracker B-02 |
| B-04 | Parts module: 42 -> 59 parts; turret/cannon `constraint_index` = -1 (no joint member in manifest) | BUILD | done (joint defect) | - | V-RC2-turret | M | `Working/Parts/bm_vehicle_parts.json`; `R/turret-joint-trace.md` |
| JOINTS-v2 | Manifest with joints (P-01 -> 11, P-02 -> 12) built in `Builds/bm-RC3-parts` (forward ref until physicsc has constraints 11/12) | BUILD | done but NOT in RC4 | - | 9172 | M | GB tracker JOINTS-v2; `Working/Parts/bm_vehicle_parts_v2.json` |
| HINGES-physicsc | `.physicsc` copy with 2 new hinges at 11/12 (13 constraint objects) | BUILD | done (copy, not merged, never loaded in game) | - | 9172, V-joint-in-game | M | `Working/Collision/batmobile_hinged.physicsc`; GB tracker HINGES-physicsc |
| TURRET-joint | Root cause: joints die at B-04 manifest | BUILD | done (diagnosis); fix unmerged | - | 9172 | S | `Builds/bm-RC2/verify/joint_trace.md` |
| B-05 | Entity graph; 69 interaction objects B-05 skipped; 3 roots without children; 2 pulses at graph origin | BUILD | done (RC4) / partial for interaction | 9101 | 9170 | L | GB tracker B-05; `Q/9101-rc5-entity-roots-and-slots.txt` |
| 9100 / 9101 | RC5 scaffold + branch records; entity roots, slots, interaction objects present (needed for Y/LB enter-exit) | BUILD | queued | 9033 | all RC5 branches | M | `Q/9100-...`, `Q/9101-...` |
| 9120 | Handling values (pre-req of drive modes) | BUILD | queued | 9033 | 9122, 9124 | M | `Q/9120-rc5-handling-values.txt` |
| 9121 | Suspension travel (pre-req of mode pair; B-22/B-23 per-mode spring has no member) | BUILD | queued | 9120 | 9130 | M | `Q/9121-...`; GB B-22/B-23 |
| 9122 | Drive modes + yaw-toward-aim: 4WD, pursuit stick spins car, battle stick moves in direction and auto-turns to camera (`AbsoluteMoveDirection` 0x378, `BattleModeSteerAngleFactor`, `BattleModeMaxSteering` 80), torque substitute, per-mode variant tables in `Builds/bm-RC5-drive` | BUILD | queued | 9120 | 9130 | M | `Q/9122-rc5-drive-modes-and-yaw.txt`; `R/bm-moving-yaw-toward-aim.md` |
| 9130 / B-12 | Mode pair + swap: variants on RC5 base, T-MD13 stance, T-MD8 pivot, T-MD14 audio, trigger from the exe study or a composed route; `bm_build.py --variant`; `Builds/bm-RC5-modes` | BUILD | queued (hard dependency on 9050 result and D-2) | D-2, 9050, 9121, 9122 | 9190 merge | L | `Q/9130-rc5-mode-pair-and-swap.txt`; GB B-12; `Tools/scripts/b12_variants.py` |
| 9170 | Controls branch: keymap edits (enter on Y, LB exit, A->exit, RB secondary, X reverse, RPADRIGHT winch), exit/enter graphs, eject, `Builds/bm-RC5-controls` | BUILD | queued | 9101, keymap writer | 9190 | L | `Q/9170-rc5-controls-entry-exit-eject.txt`; `R/controls-entry-exit-eject-plans-v2.md` |
| NEW-MOD-19 | Write the keymap writer: serialise 12-B binding records + 18-B property records into the patch gamepad file (7,207 B, offset 610,914,304, 145 bindings, sha `0944e37d8588feed`); re-parse check. None exists in 575 scripts | BUILD | todo (first step of 9170) | - | 9170, all keymap rows | M | `R/controls-entry-exit-eject-plans-v2.md` section 4; `JG/INPUT.md` lines 13-29 |
| 9172 | Moving parts: wheel spin/steer, doors/canopy/trunk, aero surfaces, weapon bays, cannon recoil, jet driver; joints included; `Builds/bm-RC5-parts` (>= 59 parts resolve) | BUILD | queued | 9101 | 9190 | L | `Q/9172-rc5-moving-parts-animation.txt` |
| NEW-MOD-20 | B-02 extension: cut canopy (CockPit_Mesh), 2 missile hatches, rear door, winch door, cannon barrel, steering/dash parts as separate parts (T-8 lists "—" as part for P-06/07/08) | BUILD | todo | NEW-MOD-14 | 9172 | L | `R/verify-v02b-pose-renders-lights.md` lines 92-101; `WT/PARTS_ANIM_COVERAGE.md` |
| NEW-MOD-21 | Build the battle-stance static pose set (hinge angles at rest) for the battle entity: turret/cannon/flaps/hatches/riot suppressor/machine gun; mast lift +0.633 m approximated by hinge arc (declare error) | BUILD | todo | NEW-MOD-11, 9172 | 9130 | M | `R/battle-mode-transform-plan.md` sections 4-5 |
| NEW-MOD-22 | Summon/remote/homing build or written halt, plus `rc5_survival.py` (water teleport, flip thrusters, remote range) | BUILD | queued (9124 for water/flip/remote; 9173 for summon) | 9120, NEW-MOD-18 | 9190 | M | `Q/9124-rc5-flip-water-remote.txt`; `Q/9173-rc5-world-spawn-traffic-summon.txt` |
| NEW-MOD-23 | Second Rebel Drop leaf + item for the battle entity (`UIDisplayOrder` 13, hash binding UNKNOWN for new leaf) and string rows; or spawn-swap trigger payload | BUILD | todo (inside 9130/9173) | 9050, D-2 | 9130 | M | `R/mode-swap-trigger-closest-system-plan.md` section 3.1/4; `JG/STANDALONE.md` |
| NEW-MOD-24 | Native hook payload (only if NEW-MOD-1 = yes): in-place LT-hold mode swap with state carry, vehicle-scoped input remap, canopy/eject triggers; JC3 hook addresses none decoded | BUILD | blocked (operator, decoded addresses) | NEW-MOD-1, NEW-MOD-3, 9050 | NEW-MOD-30, RELEASE | L | `R/new-behaviour-routes-survey.md` R17, section 13, line 349 |
| 9190 | Merge all RC5 branches (three-way `.epe`, module merges, budgets 4,915 KB model / 7,065 KB texture) | BUILD | queued | 9122..9173 | 9191, 9192 | M | `Q/9190-rc5-merge-release-candidate.txt` |
| 9179 / 9199 | Review of body/world branches (modes, controls, parts included); final desk review | BUILD | queued | branches | 9190 / approval | M | `Q/9179-...`, `Q/9199-...` |

### 1E. VERIFY (offline)

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| V-RC2-turret | Turret/cannon ranges vs BmAK: FAIL "no joint" (yaw missing 120 deg, pitch 25 deg) | VERIFY | FAIL (RC2); not re-run on RC4/RC5 | 9172 | - | S | `Builds/bm-RC2/verify/turret_ranges.md` |
| V-02 (RC4) | Geometry + poses: 18 of 24 pose renders PASS; UNKNOWN for P-02, P-05, P-06, P-07, P-08, P-13 | VERIFY | partial | NEW-MOD-20 | - | M | `R/verify-v02-geometry-poses-rc4.md`, `verify-v02b-pose-renders-lights.md` |
| V-RC2-mounts / V-RC2-wheels | Weapon mount markers (4 unanchored, JC3 MountAttach); stale wheel offset harmless | VERIFY | done (4 UNKNOWN) | - | - | S | `Builds/bm-RC2/verify/mount_markers.md`, `wheel_offset_effect.md` |
| V-03 (RC4) | Wiring: interaction objects present; dangling fire refs | VERIFY | partial (9001/9002 done, RC5 recheck) | 9101 | 9193 | S | `R/verify-v03-wiring-rc4.md`, `R/rc5-dangling-fire-refs.md` |
| NEW-MOD-25 | Offline verifier `rc5_modes.py --check` + `rc5_controls.py --check` + `rc5_parts.py --check`: aafdiff between variants lists only table-named files; every keymap row reparses; 59+ parts resolve; animation times == BmAK key times within one frame | VERIFY | queued inside 9130/9170/9172 | those briefs | 9191/9192 | M | brief text of 9130/9170/9172 |
| 9191 / 9192 / 9193 | RC5 verify (files/wiring/audio; geometry/predictions/install) and gate VX + approval request RC5 | VERIFY | queued | 9190 | APPROVED_Q | M | `Q/9191-...`, `Q/9192-...`, `Q/9193-...` |

### 1F. PILOT

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| Q-PILOT | 34 cards written + reviewed on RC4 (driving 8, combat 11 incl. mode switch, looks 6, prove-on-simple-car 9); ENTER_EXIT, CONTROLS cards exist | PILOT | done (RC4) | - | 9194 | M | `Working/Q/PILOT/*.md`; `R/operator-digest-pilot-cards-status.md` |
| 9194 | Refresh cards for RC5 (controls, flip, water, remote, health) with numeric bands | PILOT | queued | 9193 | Q-0 | M | `Q/9194-rc5-pilot-cards-refresh.txt` |
| NEW-MOD-26 | Pilot cards specific to this landmark: mode hold (0.40 s hold, 0.5 m / 5 deg / <=1 km/h / 0.20 s audio), keymap-honoured probe, `USE_VEHICLE_MOD` press probe, LB exit pursuit/battle motion 3x, A-A eject, canopy open on entry, turret traverse time, Vulcan spin, hatch open on fire, 4 air-brake probe | PILOT | partial (bands in plan reports; not cards) | NEW-MOD-11 | Q-1/Q-3 | M | `R/mode-swap-trigger-closest-system-plan.md` section 6; `R/controls-entry-exit-eject-plans-v2.md` section 5 |
| Q-0 | Prove cards on a stock car (small model drives game without help) | PILOT | queued (gated) | APPROVED_Q | Q-1.. | M | `Q/8600-q0-prove-pilot-cards.txt` |

### 1G. TEST (needs the human operator; every row below is in-game)

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| NEW-MOD-27 | **Day-1 probe batch (5-minute experiments, do before any variant build)**: (1) does a dropzone `settings/keymap_*.bin` change take effect, (2) press `USE_VEHICLE_MOD`/RPADRIGHT in a vanilla car, does anything happen, (3) spawn two Rebel Drop leaves, (4) drop a car while driving one and read speed/health carry, (5) hold R3 tap-vs-hold | TEST | todo | APPROVED_Q, NEW-MOD-19 | NEW-MOD-11, 9130, 9170 | M | `R/mode-swap-trigger-closest-system-plan.md` G5/G6/U2-U4; `R/controls-entry-exit-eject-plans-v2.md` U4; `Working/Q/PILOT/CONTROLS.md` lines 108-119 |
| Q-1 (modes/controls/anim items) | Spawn, walk-around entry from both sides, canopy opens (MOD-4/ANI-8), seat pose + head under canopy (ANI-9), exit at 30 km/h (MOD-3), roof/hood/rear stand (WLD-4), steering yoke / turbine / turret follows camera / Vulcan spin / hatches / air-brake probe (ANI-2..7) | TEST | todo (gated) | APPROVED_Q, RC5 | Q-4 fixes | L | GB 9b Q-1 items 3-4; `Working/Q/PREDICTIONS_LOOKS.md` |
| Q-2 (battle variant) | Turn on the spot, top speed per battle curve, camera FOV 60, yaw-toward-camera while moving, pursuit stick-spin | TEST | todo (gated) | Q-1, B-12 | Q-4 | M | GB 9b Q-2 last bullet; `Working/Q/PREDICTIONS.md` |
| Q-3 (modes/summon/remote) | Mode switch card (C6, threshold "0.05 or 0.2" UNKNOWN), water teleport, flip recovery, remote range, summon arrival | TEST | todo (gated) | Q-2 | Q-4 | M | `R/operator-digest-pilot-cards-status.md` combat C6 |
| Q-4 / NEW-MOD-28 | Fix loop for this landmark: expect hinge-joint load failures, keymap not honoured, swap not working, canopy slide missing; one extra session max per session | TEST | todo | Q-1..Q-3 | Q-5, RELEASE | L | GB Q-4 rules |
| NEW-MOD-29 | Native-hook iteration with the operator (only if NEW-MOD-1 = yes): build/install/crash-recover loop, version drift, no offline oracle | TEST | blocked | NEW-MOD-24 | NEW-MOD-30 | L | `R/new-behaviour-routes-survey.md` R17 |
| NEW-MOD-30 | Operator BmAK-vs-mod comparison drives for modes/controls (side by side, same actions) | TEST | todo | Q-3 | RELEASE | M | GB Q-PILOT item 2 |
| Q-5 | Showcase recording (pursuit run, battle weapons, eject, canopy) | TEST | todo (optional) | QX | RELEASE | S | GB Q-5 |

### 1H. RELEASE

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| QX | Gate: every Q check passed or named omission accepted by operator (only operator accepts; lore rule forbids lowering bands) | RELEASE | todo | Q-1..Q-4 | R-1 | S | GB 9b |
| R-1 | Release as pipeline (scripts + edit specs), not assets: BmAK meshes/audio cannot be published; `um publish check`; README; credits; AI disclosure. Keymap writer + hook DLL (if any) must be reviewable source | RELEASE | todo | QX | R-2 | M | GB 10 R-1 |
| R-2 | Knowledge-base field note (route, versions, gotchas including keymap/swap findings) | RELEASE | todo | R-1 | - | S | GB 10 R-2 |

## 2. (a) Done, with evidence

- Every BmAK grab for this landmark except runtime-only values: animations (253/253), bones (180), pose deltas, sockets, cockpit, modes (107 fields), controls (ini, script, native, live sampler): `BG/ANIMATIONS.md`, `BONES.md`, `POSES.md`, `COCKPIT.md`, `MODES.md`, `CONTROLS*.md`, `DRIVINGMODE.md`.
- Live-confirmed in BmAK: LT hold = battle, release = pursuit; LB = exit and enter; A = eject (exit confirmed, glide part UNKNOWN); B = immobiliser on an auto-tagged target (GB tracker G3-02d, D-11 text). Static: native switch at `TryToChangeMode` 0x140063e90 called with `BattleMode` 0x240 / `PursuitMode` 0x241 from `DrivingPlayerMove` 0x140254560 (`BG/CONTROLS_NATIVE.md`).
- Every JC3 grab: turret/cannon (`JG/TURRET.md`), moving parts (67 behaviours), doors (224 rows, 60 on X), interaction (`INTERACTION.md`), seat (candidate `sportsmuscle_f_l_seat` 0.855 m), eject (0 launch members in 4,832 exits), tank turn (pivot code-side), input (154 actions, 474 bindings, keymap global).
- Translation: T-12 (15 rows), T-13 (85 objects, all 0.05-0.30 m from hull), T-15 hybrid (stale), T-MD1/3/4/9/10/11/12 carried as designed.
- Build offline: B-02 split (99.97 %), B-04 59 parts, B-05 entity (466 classed), B-13 Rebel Drop (leaf 1621485476, item hash 443190071 per plans), `Builds/bm-RC4-modes` pair built unmerged, JOINTS-v2 + HINGES-physicsc as separate trees.
- Verify: 18 of 24 pose renders pass; V-RC2-turret FAIL root-caused.
- Pilot: 34 cards reviewed on RC4.
- In-game history relevant here: only earlier files-level loads (test-003 .ee override loads, test-060 audio swap, test-091 nitro/camera). Nothing for modes/controls/anim (`STATUS.md` "0 / 221 fully behaviour-verified").

## 3. (b) BLOCKERS, root first

**B1 (root). Can JC3 switch a vehicle's mode at runtime?**
- Evidenced NO-DATA-CARRIER: 0 selector in 52 module types (`R/mode-switch-carriers.md` 2.7); 0 spawn/replace/teleport action classes in 5,535 entry / 4,832 exit graph nodes (`JG/ENTITIES.md` via `R/mode-swap-trigger-closest-system-plan.md` section 0); INDEX has 0 "replace"/"respawn"/"despawn" paths and the only entity-addressing consumers are 11 teleport scripts (`R/mode-toggle-runtime-swap.md`); every "variant" is a separate `.ee`; no vehicle has animation/skeleton modules (`R/battle-mode-transform-plan.md` 3.1); JC3 has no battle/pursuit/transform keymap action (0 regex hits in 4 keymap copies, `JG/INPUT_D11.md:20-23`).
- Evidenced CAN-DO (partial): a second entity as a second `.ee` leaf + Rebel Drop item (`JG/REBELDROP.md` section 7, 128-B items, `UIDisplayOrder` 12 free, leaf hash recipe), with loss of speed, gear, health, ammo on spawn. A static battle pose can be carried as fixed part angles in the battle entity.
- UNKNOWN (and the only things that can unblock an in-place swap): U1 exe consumer that replaces a vehicle entity (settler: brief 9050, `JustCause3.exe` static, not yet run); U2 whether a Rebel Drop spawn carries speed/health; U3 consumer of `USE_VEHICLE_MOD` (RPADRIGHT) on a mod vehicle; U8 whether a modified `settings/*.bin` is honoured from the dropzone (RC4 ships `spawn_vehicle_defs.bin`, honouring untested); U7 whether any JC3 vehicle (mech) changes shape and handling in place. A true LT-hold toggle needs code: the survey states "true toggle is R17 and unprovable today" (`R/new-behaviour-routes-survey.md:328`).
- Fallback within data: single entity + `heat_boost` as in-place multiplier (carries about one third of one row, continuous state) vs two entities (all five handling rows, but spawn-swap = pit stop). Lore accuracy ranks neither as exact.

**B2. Can JC3 remap/scope vehicle input?**
- Evidenced: input is a global map, `settings/keymap_gamepad.bin` + `keymap_keyboard.bin` (base + patch layer, patch wins), 154 actions, 474 bindings; 0 of 232 vehicle `.ee` dumps and 0 of 134 vehicle modules name a keymap or action (`JG/INPUT_D11.md:5,70,72`). So rebinding is a game-wide edit (on foot too), and Y cannot be suppressed per entity. No hold/duration/double-tap field exists in any of 145+104+249 rows. No `BOOST`, `SONAR`, `EJECT`, mode, weapon-select action (only `WINGSUIT_BOOST`). The shipped pad binds 0 face buttons, so Y/A/X/B additions displace nothing but export Y, A, B, X already carry on-foot actions (`JG/EJECT_MAP.md`).
- UNKNOWN: whether a dropzone keymap file is honoured at all (U4; probe: add one action id, drop in, press); consumer of RPADRIGHT; double-press A and LT hold cannot be expressed by the data format as decoded.
- Missing tool: no keymap writer exists (`R/controls-entry-exit-eject-plans-v2.md` section 4).
- Consequence for D-11: "BmAK controls win inside the car, JC3 outside" is not expressible by a global keymap alone; either the global rebind is accepted on foot (needs operator ruling) or the scoping needs R17 code.

**B3. Operator decisions: D-2 re-resolution (blocks B-12, T-MD5/6/7/8/13/14) and NEW-MOD-1 (native route yes/no).** Everything on the mode pair and exact input scoping sits behind these.

**B4. 9050 (exe entity-swap study)**: 9130 has it in its AFTER list; if the report returns U1 = UNKNOWN, 9130 stalls or must compose with Rebel Drop only (brief explicitly allows "a composed script route").

**B5. Joint chain for turret/cannon/hatches/canopy**: RC4 has no joints; JOINTS-v2 + HINGES-physicsc exist but never loaded in game (new `hkpLimitedHingeConstraintData` objects appended to a copy; `.physicsc` write is proven for existing hulls only, "adding a new hull" is the unproven part; constraints appended = not proven in game). Also: JC3 hinges have no rate member and the variable writers (`flaps_T`, `air_brakes_T`, door open) are code-side and not read; canopy slide, mast lift (+0.633 m) and cannon recoil are translations, no prismatic behaviour exists in the 25 rows (`R/battle-mode-transform-plan.md:198,254`). So moving parts that BmAK animates (2.000 s transform clip, 0.433 s canopy) have no authored-duration carrier.

**B6. Runtime-only BmAK values** (LT hold time, +-0.707 meaning, A-A window, steering curve, summon/remote numbers, post-exit motion): need a Steam copy or finishing the GOG BmSDK port (22 addresses UNKNOWN). Operator task.

**B7. Test ban**: `APPROVED_Q.txt` absent; Q briefs 8600-8605 gated on RC4 gate report and need repointing to RC5.

**B8. Serial queue**: apply wave 9030 -> 9031 -> 9032 -> 9033 edits one ledger file serially and gates 9100+; the whole RC5 branch set waits for 9033.

## 4. (c) Open questions for the operator (only a player can answer)

BmAK controls/modes:
1. LT hold: is there a dead zone or delay before battle mode starts (a tap vs a hold)? Does the stance animation (about 2 s) block steering/firing? Can you cancel it by releasing mid-transform?
2. Is the speed at which battle mode can be entered limited, or does the car decelerate (`TransformationTurnDecelTorqueFactor`)? Does the car keep its velocity through the switch?
3. A-A eject: how close together must the presses be? Is a single A in pursuit anything (e.g. strafe with the stick, "Side Swipe")? In battle mode while moving, does the second A really force a boost instead of ejecting?
4. LB exit while moving: in pursuit Batman jumps out and the car breaks right, in battle straight. Does LB work at full speed or only below some speed?
5. Does the canopy open the moment you press LB, and close on entry? Does Batman glide in from outside (summon "Remote_Front/Back") or the canopy open with you outside?
6. Turret: does the turret rotate 360 degrees to follow the camera in battle mode, and what is the cannon's visible pitch range? Is it visible in pursuit mode (turret stowed)?
7. Do the rear fins / air-brakes move when braking or only during transformation/jumps?
8. Is there a visible turbine fan or steering yoke in the cockpit? (BmAK has no yoke asset in 324 packages per `WT/P13_STEERING.md`.)
9. Summon: do you call the car with LB-hold or a gadget? How long until it arrives, and does it drive over rough terrain or only roads?
10. Remote: does the Batmobile keep its battle/pursuit mode while remote-driven? Is homing (LB) a separate action from the remote cursor?
JC3-side decisions:
11. Is a game-wide controller change acceptable (e.g. Y enters, LB exits for all vehicles; RB becomes secondary fire everywhere), or must the scheme apply only inside the Batmobile (then a native hook is needed)?
12. Should the mode pair appear as two Rebel Drop entries (pit-stop swap, resets speed/health) if no in-place swap is found? Or hold the mode pair until a hook exists?
13. May an agent attempt a native hook (DLL proxy) after the exe study, given no offline oracle? If yes, which build/version of JC3 is installed (addresses are per-build)?
14. May the operator provide a Steam BmAK copy for live scraping (summon/remote/threshold numbers)?
15. Confirm halting remote and homing with written reasons (`MEM/bmak-gameplay-facts.md` allows it) or ask for the closest-system build.

## 5. (d) Risks

1. **Largest**: the two-mode requirement may have no fully lore-exact solution without code. Even the two-entity route loses speed/gear/health/ammo and cannot make the transition audio, animation, or turn-on-the-spot (pivot code-side). If the operator refuses R17, several rows end at "closest + gap", which STAGES.md forbids as an answer; expect a decision conflict.
2. Global keymap side effects (on-foot A = STUNT_JUMP + OPEN_PARACHUTE, export Y = ENTER/EXIT/WINGSUIT/USE_ITEM): remapping LB/Y/X/B breaks Rico's normal play unless scoped; the "A hold = parachute" JC3 counterpart sits on the same button.
3. A bad keymap can lock the player out of controls; rollback needs a backup (install.ps1 snapshots by diff).
4. Joints: new hinge constraints may not load (never run in game); mismatch between `.physicsc` constraint indices and part `constraint_index` crashes or freezes the part (forward-reference defect already hit in RC3-parts).
5. The T-8 ranges are partly animation extents, not limits (Vulcan 2160 deg wrapped; turret +-60 may not be BmAK's limit); the cannon pitch is code-driven so -5..20 is JC3's tank value.
6. Doc inconsistencies that could mislead small models: GB MOD-3 says "hold-to-eject"; GB B-12 says T-MD8/T-MD14 "stay named omissions" (STAGES.md forbids); T-WLD13/14 contradict the operator's water facts; GB 1.8 ANI-4/ANI-7 may describe parts BmAK lacks; `t11_variants.json` still says 1 variant; T-PA5 lists doors that B-04 removed.
7. Brief 9130 depends on four reports (one not yet produced, 9050) and 9122->9121->9120; a single stalled brief (8401 used two sessions) cascades. Similar-text stripping (`low/too-similar`) has killed template-style briefs before.
8. RC4 ships `_debug.ee` replacing the Serpente; the standalone-leaf hash binding for a SECOND entity is UNKNOWN (`JG/STANDALONE.md`: load YES, hash UNKNOWN). Rebel Drop leaf has never loaded in game on RC4.
9. Hardware/timing: all in-game tests need the operator; BmAK runtime numbers need a Steam copy.
10. Release scope: BmAK-derived assets cannot be shipped (R-1); a hook DLL is a legal/AV/stability risk and cannot be validated offline.
11. Memory/agent discipline: AGENTS.md demands change statements before edits; local small models must not fill UNKNOWNs (e.g. 0.40 s hold is "an authored pass band", not a BmAK value).

## 6. (e) Remaining effort

Assumptions: S = 1 session, M = 2, L = 8 agent-sessions; ~100 small-model briefs/day but a dependency chain with serial ledger edits (9030 -> 9033), ~15 min per brief, some briefs needing 2 sessions; in-game rows need the human (45-min sessions).

Agent (desk) sessions still to run for this landmark, by row groups:
- RC5 briefs owned directly: 9050 (2), 9122 (2), 9130 (8), 9170 (8), 9172 (8), plus its share of 9101 (2), 9120/9121 (4), 9124 (2), 9173 (2), 9031/9032 (2) = about 40 sessions.
- NEW-MOD desk rows: -2,-3,-5,-6,-7,-8,-9, -11,-12,-13,-14,-15,-16,-17,-18,-19,-20,-21,-22,-23,-25,-26 = about 45 sessions.
- Review/merge/verify shares (9179, 9190-9194, 9199, V reruns): about 10 sessions.
- Fix-loop desk work after tests (Q-4): about 15 sessions.
- If the native-hook route is approved (NEW-MOD-24): +25 to 40 sessions, and it cannot be verified offline.
- Release R-1/R-2/QX: about 4 sessions.
Total about 115 agent-sessions without the hook route; about 150-160 with it.

Calendar days (desk): with the serial ledger chain and ~100 briefs/day, desk work reaches "approval-ready RC5" in about 4-6 days; the hard-dependent chain 9033 -> 9100 -> 9101 -> 9120 -> 9121 -> 9122 -> 9130 -> 9190 -> 9191/9192 -> 9193 alone is 10 serial briefs, about 3-4 days at ~15 min each plus review lags.

Operator in-game sessions: day-1 probe batch (1 session, 1 h, NEW-MOD-27), then Q-1, Q-2, Q-3 (about 45 min each) = 4 sessions minimum; Q-4 fix loop adds up to one extra per session = about 8 sessions; a native-hook route adds an estimated 5-10 iterative sessions. Roughly 8-18 operator sessions (about 6-14 operator hours), 2-4 per day at most, so 3-8 operator days; real-time calendar gating by briefs that depend on probe results (the probe batch outcome decides B-12) makes it sequential: desk 4-6 days -> probe day -> second desk pass 2-4 days -> Q-1..Q-3 over 3-5 days -> fix loop 3-7 days -> release 1-2 days.

Estimate to a released product for this landmark: about 3 to 5 calendar weeks (best case, no hook, probes succeed), 6 to 10 weeks if the native-hook route is required or the keymap is not honoured. These are estimates from the row sizes above, not measurements.
