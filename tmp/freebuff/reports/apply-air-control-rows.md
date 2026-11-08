# T-AC1 / T-SR1 applied — closest JC3 carriers, and the build that composes the gap

**What was done:** both rows left `out`. Neither has an *exact* carrier (`carrier-air-control.md`
§9: none of the 12 candidates is proven to reproduce BmAK air control), so each row now names the
**closest JC3 system as its carrier**, carries the values from BmAK's own members, and points at a
build card for the gap between the JC3 carrier and BmAK. No row says "no JC3 system".

- **T-AC1** — `out` → **`next`**: yaw from `CustomLandGlobal.drift.max_drift_torque` **8000**
  (0x48), pitch from an `Aerodynamics` surface with `turn`/`pitch_steering_factor` **0.2286**.
- **T-SR1** — `out` → **`next`**: `DriverLean.righting_torque` **2000** plus the Havok
  `TYPE_SETUP_STABILIZATION` atom (+0x0B0) for the `StayUprightConstraintSetup` leg. The old
  `why` ("only in `DriverLean` on 23 aircraft - no land carrier") was **false on its own
  evidence**: those 23 rows are 18 bikes + 5 jet-skis and **0 aircraft**
  (`Research/challenge/card-T-10.md` A4).

Build card: `tmp/freebuff/reports/air-control-closest-system-plan.md`. Carrier ranking and offsets:
`tmp/freebuff/reports/carrier-air-control.md`. No game file, build or module was touched.

## 1. What the carrier report gave the rows

| row | closest JC3 system (member path · offset) | value BmAK must reach | what the carrier already is |
|---|---|---|---|
| T-AC1 yaw | `CustomLandGlobal.drift.max_drift_torque` · **0x48** · float; n=145 land vehicles, shipped **0..35000** | `AirControlYawTorqueFactorMax` **8000** (0x4A8, serialised, all four packages) | the fleet's only yaw torque on a land vehicle (`DRIVE_CARRIERS.md` C1); 8000 is inside its shipped range |
| T-AC1 pitch | `AerodynamicSurface.pitch_steering_factor` · **0x3C** (turn 0x38, roll 0x40); type 96 B | `AirControlPitchTorqueFactorMax` (no value — not serialised) | the only air authority outside helicopters; every shipped value 0, no car ships the module |
| T-SR1 torque | `DriverLean.righting_torque` · shipped **1500..4000** | `JumpRampRightingTorque` / `JumpNoRampRightingTorque` **2000 / 2000** (0x1A64/0x1A68) | 23 rows = 18 bikes + 5 jet-skis; 2000 sits inside the shipped band |
| T-SR1 constraint | Havok `hkpLimitedHingeConstraintData` atom type **23** `TYPE_SETUP_STABILIZATION`, 16 B at **+0x0B0** | `StayUprightConstraintSetup` / `Instance` (0x6E4/0x6EC) | present in 419/419 vehicle hinges and 71/71 ragdolls (`PHYSICS_LIMITS_REVIEW.md`) |

Two numbers the rows could not take from bytes, and how they are declared instead: BmAK's
`AirControlPitchTorqueFactorMax`, `AirControlInterpTime` and `AirControlTimeInAir` are not
serialised in any shipped archetype (`MODES.md`), so pitch is a **declared symmetry** to yaw, and
the 1.212 s "window" is the measured F-6 mean, not a member.

## 2. The rows as they now read in `T_ROWS.jsonl`

Both have 8 cells, `dispo: "next"`, `edits: 0` (nothing applied).

**T-AC1**

| cell | text |
|---|---|
| 2 · BmAK source | `AirControlYawTorqueFactorMax` 8000 (mid-air yaw authority; the 1.212 s airborne window is F-6) |
| 3 · JC3 target | **closest, composed:** `CustomLandGlobal.drift.max_drift_torque` 0x48 (the fleet's only yaw torque on a land vehicle, shipped 0..35000) **+** `AerodynamicSurface.turn_steering_factor` 0x38 / `pitch_steering_factor` 0x3C (the only air authority outside helicopters) |
| 4 · transform | **composed pair** — yaw from the drift torque, pitch from the aero surface; no exact airborne-gated torque member exists (`VOCABULARY.md` has 0 `air_control`/`yaw_torque` rows) |
| 5 · now | drift max 12000, constant 0, min speed 10; the car ships no aero module, fleet aero factors 0 |
| 6 · proposed | **next** (2026-11-06, closest system): `max_drift_torque` 12000 → 8000, `min_speed_to_drift_kmph` 10 → 0, plus a car `Aerodynamics` surface with `turn`/`pitch_steering_factor` 0 → 0.2286 (8000/35000 normaliser). The gap the build composes is the airborne gate. Carrier `carrier-air-control.md` §3/§4, build card `air-control-closest-system-plan.md` |
| 7 · conf | decoded (BmAK) + decoded (carrier offsets) + derived (0.2286 bridge) |
| 8 · verify | Q-AC-1: ramp jump at F-6 entry speed, full left steer for 1.212 s → heading change 0.53–0.80× the same-input ground drift, pitch 1.23–1.85× yaw, landing roll ≤ 30° |

**T-SR1**

| cell | text |
|---|---|
| 2 · BmAK source | `JumpRampRightingTorque` 2000, `JumpNoRampRightingTorque` 2000, `StayUprightConstraintSetup/Instance` |
| 3 · JC3 target | **closest, composed:** `DriverLean.righting_torque` (shipped 1500..4000; 23 rows = 18 bikes + 5 jet-skis/amphibious quads, **0 aircraft**) **+** the Havok `TYPE_SETUP_STABILIZATION` atom type 23 at +0x0B0 (419/419 hinges) |
| 4 · transform | **composed pair** — `righting_torque` 2000 for the self-righting torque, the stabilizer atom for the upright constraint; the row's old "23 aircraft, no land carrier" reason is refuted (`card-T-10.md` A4) |
| 5 · now | no car ships `DriverLean`; 2000 sits inside the shipped 1500..4000; stiffness/damping/resist angles have no JC3 member |
| 6 · proposed | **next** (2026-11-06, closest system): carry `righting_torque` 2000 on the car's `DriverLean` block and take the upright constraint from the stabilizer atom; a `CCar` accepting `DriverLean` is UNKNOWN (0 cars ship it), which the build's load probe answers |
| 7 · conf | decoded (BmAK + fleet) + UNKNOWN (a CCar accepting DriverLean) |
| 8 · verify | land the F-6 ramp on its roof: the car returns wheels-down within 0.5 s with no input |

Evidence is carried in three places, each re-read by a checker: the cells above (cell 6 names both
report files), the `DISPO` `why` in `Tools/scripts/t_rows.py`, and the T-10 evidence triples in
`Tools/scripts/t10_reopen.py` (needles on `carrier-air-control.md`, the build card,
`card-T-10.md`'s "18 bikes + 5 boats, 0 aircraft", `PHYSICS_LIMITS_REVIEW.md`'s
`TYPE_SETUP_STABILIZATION`, plus the `absent` proof that no `air_control`/`upright` member exists).

## 3. The build card — what the build composes on top

The gap is not a value. It is **a per-frame yaw/pitch torque gated on "no ground contact"**, and JC3
has no such boolean (`VOCABULARY.md`: 0 `air_control`/`yaw_torque` rows). The card composes it:

- **Leg 1 — yaw, in the car's own module.** `drift.max_drift_torque` 12000 → **8000** (BmAK max
  carried 1:1), `drift.constant_drift_torque` stays 0, `drift.min_speed_to_drift_kmph` 10 → **0**
  so the drift state exists at the ramp lip and at low air speed. The trigger is the state itself:
  if the sim keeps the drift state while airborne, the torque runs for the whole 1.212 s; if it
  exits on ground loss, leg 2 takes over.
- **Leg 2 — pitch, a new private `Aerodynamics` module** (replaces the car's 5-member
  `LandAerodynamics`, copying its air density 1.3 / frontal area 6.63 / drag 0.55 / top-speed drag
  2.0 / lift −0.3 so top speed and downforce do not change): `turn_steering_factor` and
  `pitch_steering_factor` 0 → **0.2286** = 8000/35000, the only bridge that exists because the aero
  members have no shipped non-zero value and no unit link. `roll_steering_factor` stays 0 (roll is
  T-SR1's leg).
- **T-SR1 leg.** `DriverLean.righting_torque` **2000** on the car's block, and the upright
  constraint from the stabilizer atom rather than a `StayUpright*` member (none exists on the JC3
  side).
- **Measurement.** Q-AC-1 (T-AC1) and the roof-landing recovery (T-SR1); the card also lists the
  load probe Q-AC-2 that decides whether a `CCar` accepts the aero module or `DriverLean` at all,
  and the offline checks (`jc3adf.py dump`, `.epe` repoint, `.toc` verify, receipt, tamper).

The plan is a plan: no module, `.epe`, receipt or build was written, and `edits: 0` on both rows.

## 4. Files changed, and the pins regenerated

Edited (superseding the `out` claim wherever it was written):

| file | change |
|---|---|
| `Working/Translation/T3_COVERAGE.md` | T-AC1 and T-SR1 rows rewritten (carrier, transform, now, proposed, conf, verify); the "no expression" total 298 → **293** (T-SR1 4 + T-AC1 1 fields now have carriers) |
| `Tools/scripts/t_rows.py` | `DISPO["T-AC1"]` and `["T-SR1"]`: `out` → `next`, with the new `why` |
| `Tools/scripts/t10_reopen.py` | the T-10 re-decision entries: `now` `out` → `next`, `why` rewritten, carrier/plan/card-T-10 evidence added |
| `Tools/scripts/audit_compromises_t.py` | the two compromise entries: "no air-control member" / "no land righting carrier" replaced by the composed carriers and what is still lost |
| `Tools/scripts/t23_closeout.py` | HDL-6 mapping text: "air control - out" / "self-righting - out" → closest system |
| `Tools/scripts/t_blocked.py` | the `reconciles` pin `in_scope == 185` → **187** (two rows left `out`) |

Regenerated from those sources (the re-pin):

- `Working/Translation/T_ROWS.jsonl` — `t_rows.py build`, 198 rows, `next` 52, `out` 29, blocked 8.
- `Working/Translation/BLOCKED_PROPOSALS.json` + `.md` — `t_blocked.py --write`; the ledger sha256
  pin is refreshed (12 blocked rows, 8 ledger + 4 T6, of **187** in scope).
- `Working/Translation/T10_OPEN_ROWS.json` + `.md` — `t10_reopen.py --write` (16 rows: 5
  superseded, 8 out, 1 blocked).
- `Working/Translation/COMPROMISES_T.json` + `.md` — `audit_compromises_t.py --write` (72 audited).
- `Working/Translation/BUILD_BATCHES.md` + `build_batches.json`, `STATUS.md` — `t23_closeout.py
  --write`, `status_audit.py --write`.

## 5. Checks (verbatim)

```
$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 52 keep 60 epe 26 re-read 0 blocked 8 out 29 superseded 7 | edits 35 over 16 rows
check ok                                                        exit=0

$ python Tools/scripts/t_blocked.py --check
PASS: 12 blocked rows re-derived (8 ledger + 4 T6) of 187 in scope; 2 attempts, all evidence marks present; ledger sha256 unchanged   exit=0

$ python Tools/scripts/status_audit.py --check
STATUS.md is current                                            exit=0

$ python Tools/scripts/t10_reopen.py --check
PASS: 16 rows (5 superseded, 8 out, 1 blocked) | 8/8 out rows this card owns carry a proof file | ... json match True, md match True   exit=0

$ python Tools/scripts/audit_compromises_t.py --check
72 audited: 1 approved, 71 unapproved; by dispo {'blocked': 7, 'out': 27, 'superseded': 2, 'next': 15, 'edit': 10, 'keep': 11}
OK: every approval quote re-read at its cited line; document re-derived identically   exit=0
```

Two limitations, both recorded rather than hidden:

1. **`status_audit.py --write` exits 1 with a console `UnicodeEncodeError`** (cp1252 cannot print the
   `→` at position 3630) *after* it has written `STATUS.md`; `--check` then reports "STATUS.md is
   current". The write succeeded; only the final `print(text)` to the Windows console failed. Not
   caused by this edit — the arrow sits in prose this change does not touch.
2. **`t23_closeout.py --check` still fails one gate:** "¶11 has 11 decisions, expected D-1...D-10".
   No decisions file was touched here (`DECISIONS_NEEDED.md` contains no `D-11`; the 11th decision
   lives in another lane's record), and the row edits add or remove no decision. The gate's other
   numbers are clean: 75 codes, 53 carried, 6 named omission, 6 blocked, 10 documented, 0 unmapped,
   198 ledger rows.

## 6. Revert

Each file is a one-line or one-row edit; revert in dependency order and regenerate:

```
cp Working/Translation/T_ROWS.jsonl.bak-b13 ...            # only if reverting the whole ledger
# else: put T-AC1/T-SR1 back to ("out", <old why>) in Tools/scripts/t_rows.py and in T3_COVERAGE.md,
# restore the t10_reopen / audit_compromises_t / t23_closeout entries, set t_blocked in_scope back to 185, then
python Tools/scripts/t_rows.py build
python Tools/scripts/t_blocked.py --write
python Tools/scripts/t10_reopen.py --write
python Tools/scripts/audit_compromises_t.py --write
python Tools/scripts/status_audit.py --write
python Tools/scripts/t23_closeout.py --write
```

Nothing outside `Working/Translation/`, `Tools/scripts/` and this report was written; no build,
game file or `.epe` was touched.
