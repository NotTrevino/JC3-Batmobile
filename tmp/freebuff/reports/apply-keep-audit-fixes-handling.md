# Applying the keep-audit COMPROMISE rows — dimensions/wheels, steering/drift, engine/boost/aero

**STATUS: done.** The thirteen rows the three audits mark COMPROMISE are closed in the ledger
(`Working/Translation/T_ROWS.jsonl`) — each now carries either a replacement value with its
derivation or a closest-JC3-system composition that reaches the BmAK number. `T-ST7`, `T-ST2` and
`T-ST3` carry the operator's 0.25 s ruling, cited by name. The fifteen corrected numbers are in a
new build batch, **B-24**, in `Working/Translation/BUILD_BATCHES.md`. All required checks pass
(`t_rows.py check`, `status_audit.py --check`, `t_blocked.py --check`, `damage_predict.py --check`,
`v_wheels.py --check`); three other scripts fail on pins that predate this change (§6).

No game was launched or attached to. Nothing was written under a game install, no existing
`Builds/bm-*` tree was touched, no git commit was made.

## 1. The thirteen COMPROMISE rows, closed

| row | BmAK number | was | **now (ledger cell)** | class | derivation |
|---|---|---|---|---|---|
| `T-G4` | no `ground_clearance` member; underbody gap **0.071 m** (body bbox min y 0.091 − ground 0.02) | 0.7037 (the hub mean) | **0.071** | derived | bbox gap, coherent with the tyre contact 0.7047 − 0.68275 = 0.0220 m; in the shipped 0.05…1 domain (med 0.4, n=271, `VOCABULARY.md:859`) |
| `T-ST2` | `SteerSpeed` 220 °/s, lock 55° | 0.8 s | **0.25 s** | derived, **operator ruling** | 55° / 220 °/s (§2); the 0.0833 s the 720 °/s curve implies is explicitly *not* taken |
| `T-ST3` | flat rate curve, high-speed lock 20° | 0.6 s | **0.091 s** | derived, **operator ruling** | 20° / 220 °/s; R3, below the 0.2 s fleet minimum |
| `T-ST4` | no input exponent; all steering modifiers 1.0, assist absent | 3 / 3 / 3 | **1 / 1 / 1** | derived (absence) | absence → identity, the `T-B3` precedent; 1.0 is the fleet floor (1…3, n=145) |
| `T-ST6` | rear `LatSlipFactor` 1.6 | 0.3 | **0.625** | derived (INFERRED reciprocal) | 1 / 1.6; inside the 0.3…0.8 band (n=19, med 0.5); falsifier 0.48 = 0.3 × 1.6 |
| `T-K3` | `EBrakeBrakeForce` 640,000 vs class default 160,000 | 1 | **4.0** | derived (ratio) | 640000/160000, the only unit-free bridge; in the 1…10 domain, above the 6 t band 1…2.25 → R3 |
| `T-K4` | `HandBrakeOffTime` 0.3 s; `HandbrakeLatSlipFactor` 1.5 f / 1.1 r | rear-only, friction 1, min_time 5 | **min_time 0.3, friction 4.0, front axle as yaw torque** | INFERRED + derived composition | 0.3 s kind-match; front slip 1.5 is the larger and JC3 ships `front.handbrake` 0 on 145/145, so `drift.counter_steer_torque_handbrake` carries it, share 1.1/1.5 = 0.733 |
| `T-DR1` | `HandbrakeOnSpeed` 10,000 cm/s = 360 km/h; `DriftCorrectionSteerSpeed` 1.0, assist absent | 10 km/h, sensitivity 4 | **min speed 0, sensitivity 2** | derived | the gate is above the car's 336 km/h top speed → no effective gate (0 ships in 4 builds); no drift gain → fleet median 2 |
| `T-E2` | lore 1200 bhp; no absolute torque member | 1393.5 | **2921 N·m** | derived, R3 | 894.8 kW / (471.239 rad/s × 0.65) at 4500 rpm; 1393.5 gives only 572 hp at that band; 0–60 in 2.7 s route 2513 N·m |
| `T-A3` | no drag member at all | 2.0 | **1.0** | derived (absence) | identity changes nothing; 2.0 drops the ceiling to 161 km/h; shipped 1…30 domain, floor |
| `T-E5` | wiki 209 mph, assumed + signed off | 336.4 | **336.4 kept, with the balance** | assumed | terminal at 894.8 kW and Cd·A 3.649 is 260 km/h; 336.4 needs Cd·A 0.805 m² = **Cd 0.1213** |
| `T-B1` | `FakeExtaSpeedAccel` 600 cu/s² = 6.00 m/s² | 2.0 | **6.3** | derived | 1 + 6.00/1.13 (measured 1.13 m/s² = 6,777 N / 6,000 kg); extra 43.2 km/h and blend 0.2 stay; shipped 1.5…40 domain |
| `T-B4` | no BmAK source exists | grip 4.26 / extra 100.92 (bytes) | **grip 1.5 / extra 80** | derived | 4.26 = 1.5 × 2.844 (torque ratio) and 100.92 = 80 × 1.2615 (tier scale) are not BmAK numbers; with T-E2/T-B1 carrying the power ratio they double-count |

`T-ST7` was already `next` at 0.25 s / 0.091 s from the ruling; this pass only aligned `T-ST2` and
`T-ST3` with it, so the three steering-time rows now agree.

## 2. The ruling, cited

`Working/Translation/DECISIONS_NEEDED.md`, "OPERATOR RULINGS 2026-11-06", item 1:

> **T-ST7: A, 0.25 s** (BmAK 55 deg / 220 deg/s). Also check the steering-rate / max-speed members
> so the full BmAK rate is carried, not only the lock time. "No player car ships below 0.5 s" is not
> a reason: AI cars ship 0.25 s and bikes 0.3 s.

Both `T-ST2`/`T-ST3` cells cite it by name, and `t_rows.py`'s `DISPO` entries quote it.

## 3. Files changed, and how to revert

| file | change | revert |
|---|---|---|
| `Working/Translation/T1_TRANSLATION.md` | 11 rows rewritten (`T-G4`, `T-ST2`, `T-ST3`, `T-ST4`, `T-ST6`, `T-K3`, `T-E2`, `T-E5`, `T-B1`, `T-B4`, `T-A3`) | restore the old cells (they are quoted in §1's "was" column) |
| `Working/Translation/T3_COVERAGE.md` | 2 rows rewritten (`T-K4`, `T-DR1`) | same |
| `Tools/scripts/t_rows.py` | `DISPO` gains a handling-keep-audit block (11 new entries) and `T-E2`/`T-K4`/`T-DR1` move `keep`→`next` | delete the block, restore the three one-liners |
| `Working/Translation/T_ROWS.jsonl` | **regenerated** (`t_rows.py build`), never hand-edited | revert the two files above and re-run `build` |
| `Working/Translation/t1_handling.json` | **new** payload: 15 edits with derivation and class | delete the file and the B-24 references |
| `GRAB_BACKLOG.md` | new §8 card **B-24** | delete the card |
| `Tools/scripts/t23_closeout.py` | `BATCH_PAYLOADS`/`BATCH_KIND` gain `t1_handling.json` → `B-24` | remove the two lines |
| `Working/Translation/BUILD_BATCHES.md`, `build_batches.json` | **regenerated** (`t23_closeout.py --write`) | re-run `--write` after the revert |
| `STATUS.md` | **regenerated** (`status_audit.py --write`) | same |
| `Working/Translation/BLOCKED_PROPOSALS.{json,md}` | **regenerated and re-pinned** (`t_blocked.py --write`); blocked set unchanged at 15 | same |
| `Working/Translation/COMPROMISES_T.md`, `COMPROMISES_T.json` | **regenerated** (`audit_compromises_t.py --write`) — it re-reads every ledger cell | same |

Ledger effect: `keep 56 → 39`, `next 86 → 99`, every other disposition unchanged (199 rows,
16 edit, 11 blocked, 26 epe, 1 out, 7 superseded).

## 4. The build batch

`BUILD_BATCHES.md` had no step owning the `land_global` / `land_steering` / `land_engine` /
`land_aerodynamics` / `brakes` / drift cells (the existing B steps cover parts, lights, weapons,
audio, world, suspension). So the corrected numbers go into a new batch card **B-24 · Handling
values: the three keep-audits' replacements** (`GRAB_BACKLOG.md` §8), whose payload is
`Working/Translation/t1_handling.json` (15 rows / 15 values) and whose gate is a `.toc` read-back of
all fifteen members:

| # | member | value |
|---|---|---|
| 1 | `land_global.ground_clearance` | 0.071 |
| 2 | `land_steering.t_to_full_steer_s` | 0.25 s |
| 3 | `land_steering.max_speed_t_to_full_steer_s` | 0.091 s |
| 4 | `land_steering.steer_input_power_pc/_durango/_orbis` | 1 / 1 / 1 |
| 5 | `land_steering.wheel_drift_aligning_strength` | 0.625 |
| 6 | `brakes.*.handbrake_friction_factor` | 4.0 |
| 7 | `brakes.*.min_time_to_block` | 0.3 |
| 8 | `drift.counter_steer_torque_handbrake` | 30000 (composition, unchanged) |
| 9 | `drift.min_speed_to_drift_kmph` | 0 |
| 10 | `drift.steering_sensitivity` | 2 |
| 11 | `land_engine.torque_factor_at_optimal_rpm` | 2921 |
| 12 | `land_aerodynamics.top_speed_drag_coefficient` | 1.0 |
| 13 | `land_aerodynamics.drag_coefficient` (owed on T-A2) | 0.1213 |
| 14 | `nitro_boost.torque_multiplier` | 6.3 |
| 15 | `heat_boost` / `nitro_boost_upgraded` `grip_multiplier` / `extra_top_speed` | 1.5 / 80 |

`BUILD_BATCHES.md` now reads `15 artefacts (13 payloads + 2 records) over 22 B steps`, with the
step in the batch table (`| B-24 · Handling values … | Builds/bm-024/ | t1_handling.json (15 / 15) |`)
and in card order (`| B-24 | M | T-1 | T-ST2, T-ST3 … T-G4 |`).

## 5. Checks run, with output

```
$ python Tools/scripts/t_rows.py build
E:\Modding\JC3-Batmobile\Working\Translation\T_ROWS.jsonl: 199 rows, 35 edits over 16 rows

$ python Tools/scripts/t_rows.py check
ledger 199 rows | edit 16 next 99 keep 39 epe 26 re-read 0 blocked 11 out 1 superseded 7 | edits 35 over 16 rows
check ok                                                            (exit 0)

$ python Tools/scripts/status_audit.py --check
STATUS.md is current                                                (exit 0)

$ python Tools/scripts/t_blocked.py --check
PASS: 15 blocked rows re-derived (11 ledger + 4 T6) of 216 in scope; 0 attempts, all evidence markers present; ledger sha256 unchanged   (exit 0)

$ python Tools/scripts/damage_predict.py --check
PASS: 9 arms x 3 vehicles, models H0, H1, H2, finite H0 27 / H1 27 / H2 19, never H1 0 / H2 8
      chain 7 steps, 7 carry an UNKNOWN, 3 Q-1 probes
      donor 700 HP / tank 2000 HP / build 2000 HP, fleet 233 modules, json match True   (exit 0)

$ python Tools/scripts/v_wheels.py --check
WARN: the four wheel parts still carry the shipped Serpente `parent_space_offset` translations (max |hardpoint - part origin| = 1.0130 m); … 
check ok                                                            (exit 0)

$ python Tools/scripts/audit_compromises_t.py --check
72 audited: 1 approved, 71 unapproved; by dispo {'next': 47, 'blocked': 11, 'superseded': 2, 'edit': 10, 'keep': 2}
OK: every approval quote re-read at its cited line; document re-derived identically   (exit 0)

$ python Tools/scripts/bmak_sampler_results.py --check
derive == stored JSON: True | spot pulses missing: []               (exit 0)

$ python Tools/scripts/t23_closeout.py --check
gate TX: 75 codes (58 carried, 3 named omission, 4 blocked, 10 documented, 0 unmapped) | 199 ledger rows |
         assumed 1 (0 unsigned) | decisions 11/10 answered | 15 artefacts (13 payloads + 2 records) over 22 B steps
siblings: t_rows.py check exit 0 | status_audit.py --check exit 0 | bmak_coverage.py --check exit 0
FAIL §11 has 11 decisions, expected D-1...D-10
FAIL B-17: no payload and not declared as a no-payload step
FAIL B-18: no payload and not declared as a no-payload step
FAIL B-19: no payload and not declared as a no-payload step
FAIL B-20: no payload and not declared as a no-payload step
5 problem(s)                                                        (exit 1)
```

The five gate-TX problems are the same five present **before** this change (recorded at the start of
the session, with the ledger at its pre-existing 199 rows). `assumed` is back to **1 (0 unsigned)**
— `T-E5` keeps the `assumed` class and its sign-off phrase — and the three sibling checks, the two
byte comparisons and the new card all pass.

## 6. Checks that fail, and why they are not this change

| script | failure | evidence it predates this pass |
|---|---|---|
| `t_vnf_six.py --check` | `assert len(rows) == 198 and len(resolved) == 145` → AssertionError | the ledger already had **199** rows before any edit here (baseline `t_rows.py check`: "ledger 199 rows"), so the pin was already wrong |
| `t_boost_rows.py --check` | `FAIL T_ROWS still parses as 198 rows` (the *only* remaining failure; the cell-phrase oracles P-B8 "no BmAK source exists" and P-B11 "Serpente defaults" now pass again) | same 199-row pin; its baseline output in this session was identical |
| `v05_driving.py --check` | `FAIL T-ST7 is no longer blocked; the turning circle must be re-derived` | `T-ST7` was moved to `next` on 2026-11-06 by `steering-st7-apply.md`, before this pass; the script is pinned to the blocked state and would next trip on `T-ST2`'s new cell (it parses `**keep 0.8 s**`) |
| `t_row_evidence{,2,3}.py --check` | 10/12 and 9/15 oracles, `ValueError: max() iterable argument is empty` | they read cited BmAK file paths, not ledger cells (`grep "cells["` finds no use), and none of their output mentions any row changed here |
| `checks_sweep.py --check` | `need a letter range, e.g. a g` | usage error — the script was called without its range argument |

None of these were repaired here: re-pinning a row-count assertion or re-deriving the turning circle
is a separate decision, and re-pinning the 198 silently would hide ledger drift.

## 7. COMPROMISES / residuals

Everything is closed as a value or a composition, but four residuals are declared rather than
hidden:

1. **`T-E5` is still a label, not a physics result.** `official_top_speed` 336.4 is the operator's
   signed wiki target; the driveline at 2921 N·m tops out at 260 km/h until `drag_coefficient`
   becomes 0.1213 (T-A2's member, batch item 13). Whether the member is a HUD cap or a physical
   limit is UNKNOWN.
2. **`T-ST6` is an INFERRED reciprocal.** 1/1.6 is a semantic bridge; the falsifier (0.48) is
   recorded in the cell so one take decides the direction.
3. **`T-K4`'s front axle has no member.** The handbrake slip on the front axle (1.5, the larger
   value) is composed as yaw torque through `counter_steer_torque_handbrake`; the 0.733 ratio is
   the number to tune, not a decoded mapping.
4. **Five `T-DR1` cells remain JC3-native** (max 45°, entry 20 / exit 2, two yaw damps, handbrake
   torque) because BmAK has no member for any of them. They are labelled JC3-native in the cell, not
   claimed as translations.

## 8. UNKNOWNs

- What `land_global.ground_clearance` actually controls — no file decodes the consumer; the 0.071
  write is a probe (Q2-A6).
- What `top_speed_drag_coefficient` multiplies — the two readings differ by 42 km/h; B-24's probe
  is 1.0 vs 2.0.
- Whether `official_top_speed` is a cap or a HUD label.
- Whether `t_to_full_steer_s` 0.25 s / 0.091 s are honoured or filtered by the engine — neither is
  measured (test ban); 0.091 s is below the fleet minimum 0.2 s, a declared out-of-domain switch.
- BmAK's `EbrakeTime` 0.75 s and `DriftingBoostCooldown` 1.5 s still have no JC3 member; recorded,
  not translated.

## 9. Reproduce

```bash
cd "E:/Modding/JC3-Batmobile"
python Tools/scripts/t_rows.py build
python Tools/scripts/status_audit.py --write
python Tools/scripts/audit_compromises_t.py --write
python Tools/scripts/t23_closeout.py --write
python Tools/scripts/t_blocked.py --write
python Tools/scripts/t_rows.py check
python Tools/scripts/status_audit.py --check
python Tools/scripts/t_blocked.py --check
python Tools/scripts/damage_predict.py --check
python Tools/scripts/v_wheels.py --check
python Tools/scripts/t23_closeout.py --check
```
