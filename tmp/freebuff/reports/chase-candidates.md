# chase_candidates — SEARCH half of the two-stage G1 value chase

**STATUS: done.** The search half is built and its output verified: `chase_candidates.py` writes a
deterministic JSONL of **235 candidates over 35 live F-rows**, and `--check` re-derives
it byte-identically with all ids unique. Nothing was judged — the judging half is `chase_judge.py`.

- Script: `Tools/scripts/chase/chase_candidates.py` (477 lines)
- Output (outside the repo, game-derived): `E:/Modding/_BmAKgrab/chase/candidates.jsonl`
- Output size: **1,076,332 B** / 235 lines; 160 exe + 75 text candidates
- Judge kit: `Tools/scripts/chase/chase_judge.py` reads these lines as-is (`id, row, member, owner, offset, type, source, snippet`; extra `route` key is ignored)

## What was scanned (read-only)

- `E:/Games/Batman - Arkham Knight/Binaries/Win64/BatmanAK.exe` — 55,101,440 B, opened `rb`, never written.
- Config/INI under `E:/Games/Batman - Arkham Knight/**` plus the decoded packages/script text under
  `E:/Modding/_BmAKgrab/**` — 102 files matched by the text route (the walk skips this tool's own
  output and any `verdicts*` file so a judge run cannot feed back into the search).

## Row plan

`FOOTAGE.md` has 72 F-rows: **35 chased**, 33 already closed in a chase file,
3 not UNKNOWN in FOOTAGE, 1 with no member name (F-4 is a native function).

### Excluded — already FOUND in a chase file (33 rows)

Excluded because the row is no longer a live question: each is marked FOUND in the named chase file,
which is where its value and provenance live. The row text itself is untouched.

| row | member | closed at | evidence in that file |
|---|---|---|---|
| `F-1` | - | `chase/chase-01.md:15` | projectile lifetime |
| `F-7` | AirControl | `chase/chase-01.md:21` | `AirControl` |
| `F-8` | BattleModeCamConfig | `chase/chase-01.md:22` | `BattleModeCamConfig` |
| `F-9` | BattleModeWinchCamConfig | `chase/chase-02.md:112` | STATUS: FOUND. |
| `F-10` | BattleModeAbseilingCamConfig | `chase/chase-02.md:153` | STATUS: FOUND. |
| `F-11` | BattleModeCamFOV | `chase/chase-02.md:188` | STATUS: FOUND. 60.0 deg. |
| `F-12` | BattleModeWinchCamFOV | `chase/chase-02.md:200` | STATUS: FOUND. 60.0 deg. |
| `F-13` | BattleModeHeadOffset | `chase/chase-02.md:206` | STATUS: FOUND. (0, 0, 150) cm = 1.5 m above the camera origin. |
| `F-14` | BattleModeWinchHeadOffset | `chase/chase-02.md:214` | STATUS: FOUND. (0, 0, 300) cm = 3.0 m above the camera origin. |
| `F-15` | BattleModeAbseilingExtraCameraRot | `chase/chase-02.md:221` | STATUS: FOUND. Rotator (1500, 0, 0) = +8.24 deg pitch, 0 yaw, 0 roll. |
| `F-16` | StrafeCooldown | `chase/chase-02.md:230` | STATUS: FOUND. 0.75 s. |
| `F-26` | ImpactRoadAssistMaxAngle | `chase/chase-04.md:139` | STATUS: FOUND. 45.0 deg. `BmGame.upk` export 10923, FloatProperty at 0 |
| `F-27` | ImpactRoadAssistAngVelocityTime | `chase/chase-04.md:145` | STATUS: FOUND. 0.25 s. Same object, FloatProperty at 0x1770 (6000) = ` |
| `F-28` | ImpactRoadAssistSteeringFactor | `chase/chase-04.md:150` | STATUS: FOUND. 30.0 (dimensionless factor, carried as shipped, not res |
| `F-29` | ImpactRoadAssistLookAheadTime | `chase/chase-04.md:156` | STATUS: FOUND. 1.0 s. Same object, FloatProperty at 0x1778 (6008) = `1 |
| `F-30` | BattleModeTransformationAnimName | `chase/chase-04.md:161` | STATUS: FOUND. `Batmobile_V2_Tank_Spread_Open_Game` (FName; the "V2" i |
| `F-31` | BattleModeWidth | `chase/chase-04.md:169` | STATUS: FOUND. 265.0 cm. Same object, FloatProperty at 0x1994 (6548) = |
| `F-32` | BattleModeLength | `chase/chase-04.md:174` | STATUS: FOUND. 430.0 cm. Same object, FloatProperty at 0x1998 (6552) = |
| `F-41` | BattleModeMaxSteering | `chase/chase-06.md:110` | STATUS: FOUND. 80.0 deg. `Default__RVehicleSimBatmobile`, FloatPropert |
| `F-42` | BattleModeRearWheelTorquePower | `chase/chase-06.md:116` | STATUS: FOUND. 0.5. Same object, FloatProperty at 0x2d0 = `0.5`. `MODE |
| `F-43` | BattleModeEngineBrakingFactor | `chase/chase-06.md:123` | STATUS: FOUND. 0.025 (dimensionless factor). Same object, FloatPropert |
| `F-46` | BattleModeMaxSpeed | `chase/chase-06.md:150` | STATUS: FOUND. 1200.0 cm/s. Same object, FloatProperty at 0x2f0 = `120 |
| `F-47` | BattleModeStopAndTurnAngleMoving | `chase/chase-06.md:156` | STATUS: FOUND. 90.0 deg. Same object, FloatProperty at 0x2fc = `90.0`. |
| `F-48` | BattleModeTrailingSteerFactorTurnOnSpot | `chase/chase-06.md:162` | STATUS: FOUND. 1.0 (factor). Same object, FloatProperty at 0x31c = `1. |
| `F-49` | TransformationAnimNode | `chase/chase-07.md:101` | STATUS: FOUND. null reference — no `AnimNodeSequence` is assigned. |
| `F-50` | BattleModeUprightTorqueFactor | `chase/chase-07.md:121` | STATUS: FOUND. 2000.0. `Default__RVehicleSimBatmobile`, FloatProperty  |
| `F-51` | BattleModeUprightMaxTorque | `chase/chase-07.md:132` | STATUS: FOUND. 2000.0 (engine torque; `MODES.md` unit column). Same ob |
| `F-52` | TransformationRotation | `chase/chase-07.md:138` | STATUS: FOUND. 0, 0, 0 (UE3 Rotator: pitch, yaw, roll — 0° on all thre |
| `F-53` | TransformationTurnOnSpotSpeed | `chase/chase-07.md:151` | STATUS: FOUND. 360.0 cm/s. `Default__RVehicleSimBatmobile`, FloatPrope |
| `F-54` | TransformationTurnFactor | `chase/chase-07.md:161` | STATUS: FOUND. 45.0 (factor, `MODES.md` unit column). Same object, Flo |
| `F-55` | BattleModeSteerBiasRate | `chase/chase-07.md:167` | STATUS: FOUND. 3.0. Same object, FloatProperty at 0x3c4 = `3.0`; arche |
| `F-56` | AirControlPitchTorqueFactorMax | `chase/chase-07.md:177` | STATUS: FOUND. 5000.0 (engine torque gain, `MODES.md`). Same object, F |
| `F-67` | BattleModeSteerBias | `chase/chase-09.md:124` | STATUS: FOUND. 0.0 (factor — `MODES.md` unit column says factor for th |

### Excluded — not UNKNOWN in FOOTAGE (3 rows)

- `F-2` — FOOTAGE status is **RESOLVED**
- `F-3` — FOOTAGE status is **RESOLVED**
- `F-6` — FOOTAGE status is **MEASURED**

### Excluded — no member name to chase (1 row)

- `F-5` — no member name in the row text; the row asks how a native function decides, so there is no field to scan for.

## Per-row candidate counts

| row | member | owner | offset | type | candidates |
|---|---|---|---|---|---:|
| `F-4` | ShouldRadialDamageHit | - | - | - | 0 |
| `F-17` | StrafeRight | RVehicleBatmobileBase | 0x11ec | Vector3 | 18 |
| `F-18` | StrafeForce | RVehicleBatmobileBase | 0x11f8 | float | 19 |
| `F-19` | StrafeTorque | RVehicleBatmobileBase | 0x11fc | float | 4 |
| `F-20` | StrafeDuration | RVehicleBatmobileBase | 0x1200 | float | 4 |
| `F-21` | StrafeTime | RVehicleBatmobileBase | 0x1204 | float | 3 |
| `F-22` | StrafeFwdCorrectionForce | RVehicleBatmobileBase | 0x1208 | float | 3 |
| `F-23` | TransformationAnimNode | RVehicleBatmobileBase | 0x1494 | AnimNodeSequence | 4 |
| `F-24` | StrafeTarget | RVehicleBatmobileBase | 0x14e4 | RVehicle | 3 |
| `F-25` | ImpactRoadAssistTimer | RVehicleBatmobileBase | 0x1758 | float | 1 |
| `F-33` | BattleModeHeight | RVehicleBatmobileBase | 0x199c | float | 2 |
| `F-34` | JumpRampUpwardForce | RVehicleBatmobileBase | 0x1a60 | float | 2 |
| `F-35` | ImpactShakeAbandonedVehicleFactor | RVehicleBatmobileBase | 0x1ccc | float | 2 |
| `F-36` | ImpactShakeDestructiblesFactor | RVehicleBatmobileBase | 0x1cd0 | float | 3 |
| `F-37` | ImpactShakeCoolDown | RVehicleBatmobileBase | 0x1cd4 | float | 5 |
| `F-38` | BattleModeSpeedDelta | RVehicleBatmobileBase | 0x1eb4 | float | 2 |
| `F-39` | TurnOnSpotSteeringSpeedCurve | RVehicleSimBatmobile | 0x268 | FInterpCurveFloat | 22 |
| `F-40` | BattleModeMoving | RVehicleSimBatmobile | 0x294 | bool | 22 |
| `F-44` | BattleModeFrontThrottle | RVehicleSimBatmobile | 0x2e4 | float | 17 |
| `F-45` | BattleModeRearThrottle | RVehicleSimBatmobile | 0x2e8 | float | 26 |
| `F-57` | AirControlYawTorqueFactorMin | RVehicleSimBatmobile | 0x4b0 | float | 8 |
| `F-58` | AirControlPitchTorqueFactorMin | RVehicleSimBatmobile | 0x4b4 | float | 7 |
| `F-59` | AirControlInterpTime | RVehicleSimBatmobile | 0x4b8 | float | 4 |
| `F-60` | AirControlTimeInAir | RVehicleSimBatmobile | 0x4bc | float | 6 |
| `F-61` | BattleModeSlopeFactor | RVehicleSimBatmobile | 0x4c0 | float | 4 |
| `F-62` | AirControlTurnTorque | RVehicleSimCar | 0x17c | float | 35 |
| `F-63` | StayUprightRollResistAngle | SVehicle | 0x6d4 | float | 2 |
| `F-64` | StayUprightPitchResistAngle | SVehicle | 0x6d8 | float | 2 |
| `F-65` | StayUprightStiffness | SVehicle | 0x6dc | float | 3 |
| `F-66` | StayUprightDamping | SVehicle | 0x6e0 | float | 1 |
| `F-68` | AirControl | - | - | - | 0 |
| `F-69` | BattleModeYawOffset | - | - | - | 0 |
| `F-70` | ArmourModeDamageReduction | - | - | - | 0 |
| `F-71` | BattleModeThrottleSpeed | - | - | - | 0 |
| `F-72` | BattleModeSteerBiasRate | - | - | - | 1 |
| | | | | **total** | **235** |

**Cap (400/row) never reached:** overflow is 0 on every row, so no candidate was dropped.

### Rows with 0 candidates

- `F-4` ShouldRadialDamageHit — native function, not a field (no offset, and the name appears in no config/script text)
- `F-68` AirControl — row asks for the *unit* of `AirControl`; no offset is given, and the member name does not occur in any config/INI or decoded text file
- `F-69` BattleModeYawOffset — row asks for the *unit* of `BattleModeYawOffset`; no offset in the row, name absent from the text corpus
- `F-70` ArmourModeDamageReduction — row asks for the *unit* of `ArmourModeDamageReduction`; no offset in the row, name absent from the text corpus
- `F-71` BattleModeThrottleSpeed — row asks for the *unit* of `BattleModeThrottleSpeed`; no offset in the row, name absent from the text corpus

These five are unit questions, not value questions: the row carries no field offset, so the EXE route has
nothing to search for, and the member name is not written in any text file. They cannot be answered by more
searching — they need a decode of the owning object (or a measurement), which is judge/card work, not this script's.

## What one candidate looks like

**EXE route** — one candidate per store site, window from the INT3 padding, RIP-relative floats resolved:

```
F-18#0001  StrafeForce @ RVehicleBatmobileBase 0x11f8 (float)
source: exe 0x140058f81
   0x140058f10  push     rbx
   0x140058f12  sub      rsp, 0x40
   0x140058f16  mov      qword ptr [rsp + 0x20], 0xfffffffffffffffe
   0x140058f1f  mov      rdx, rcx
   0x140058f22  xorps    xmm0, xmm0
   0x140058f25  comiss   xmm0, dword ptr [rcx + 0x11e8]
   0x140058f2c  jb       0x14005903e
   0x140058f32  mov      rcx, qword ptr [rcx + 0x38c]
   0x140058f39  movss    xmm5, dword ptr [rcx + 0xc8]
   0x140058f41  movss    xmm4, dword ptr [rcx + 0xc4]
   0x140058f49  movss    xmm0, dword ptr [rcx + 0xc0]
   0x140058f51  movss    dword ptr [rsp + 0x28], xmm0
```

**TEXT route** — one candidate per whole-word occurrence, 20 lines of context, hit line marked `>>>`:

```
F-62#0035  AirControlTurnTorque @ RVehicleSimCar 0x17c (float)
source: E:/Modding/_BmAKgrab/chase/value_cdo_08.json:636
 "package": "E:\\Games\\Batman - Arkham Knight\\BmGame\\CookedPCConsole\\BmGame.upk",
 "rows": {
  "RVehicleSimBatmobile": {
   "AirControlInterpTime": 1208,
   "AirControlPitchTorqueFactorMin": 1204,
   "AirControlTimeInAir": 1212,
   "AirControlYawTorqueFactorMin": 1200,
   "BattleModeSlopeFactor": 1216
```

Snippets are capped at 12 KB (largest emitted: 8,970 chars).

## Full run and `--check`

```
$ python Tools/scripts/chase/chase_candidates.py --write
rows chased 35 | excluded 33 | no member 1 | candidates 235 | text files 102 | exe 55101440 B
| row | candidates | overflow |
|---|---:|---:|
| F-4 | 0 | 0 |
| F-17 | 18 | 0 |
| F-18 | 19 | 0 |
| F-19 | 4 | 0 |
| F-20 | 4 | 0 |
| F-21 | 3 | 0 |
| F-22 | 3 | 0 |
| F-23 | 4 | 0 |
| F-24 | 3 | 0 |
| F-25 | 1 | 0 |
| F-33 | 2 | 0 |
| F-34 | 2 | 0 |
| F-35 | 2 | 0 |
| F-36 | 3 | 0 |
| F-37 | 5 | 0 |
| F-38 | 2 | 0 |
| F-39 | 22 | 0 |
| F-40 | 22 | 0 |
| F-44 | 17 | 0 |
| F-45 | 26 | 0 |
| F-57 | 8 | 0 |
| F-58 | 7 | 0 |
| F-59 | 4 | 0 |
| F-60 | 6 | 0 |
| F-61 | 4 | 0 |
| F-62 | 35 | 0 |
| F-63 | 2 | 0 |
| F-64 | 2 | 0 |
| F-65 | 3 | 0 |
| F-66 | 1 | 0 |
| F-68 | 0 | 0 |
| F-69 | 0 | 0 |
| F-70 | 0 | 0 |
| F-71 | 0 | 0 |
| F-72 | 1 | 0 |
| **total** | **235** | **0** |

**rows with 0 candidates:** F-4, F-68, F-69, F-70, F-71
wrote E:\Modding\_BmAKgrab\chase\candidates.jsonl (1076332 B)
[exit 0]

$ python Tools/scripts/chase/chase_candidates.py --check
rows chased 35 | excluded 33 | no member 1 | candidates 235 | text files 102 | exe 55101440 B
| row | candidates | overflow |
|---|---:|---:|
| F-4 | 0 | 0 |
| F-17 | 18 | 0 |
| F-18 | 19 | 0 |
| F-19 | 4 | 0 |
| F-20 | 4 | 0 |
| F-21 | 3 | 0 |
| F-22 | 3 | 0 |
| F-23 | 4 | 0 |
| F-24 | 3 | 0 |
| F-25 | 1 | 0 |
| F-33 | 2 | 0 |
| F-34 | 2 | 0 |
| F-35 | 2 | 0 |
| F-36 | 3 | 0 |
| F-37 | 5 | 0 |
| F-38 | 2 | 0 |
| F-39 | 22 | 0 |
| F-40 | 22 | 0 |
| F-44 | 17 | 0 |
| F-45 | 26 | 0 |
| F-57 | 8 | 0 |
| F-58 | 7 | 0 |
| F-59 | 4 | 0 |
| F-60 | 6 | 0 |
| F-61 | 4 | 0 |
| F-62 | 35 | 0 |
| F-63 | 2 | 0 |
| F-64 | 2 | 0 |
| F-65 | 3 | 0 |
| F-66 | 1 | 0 |
| F-68 | 0 | 0 |
| F-69 | 0 | 0 |
| F-70 | 0 | 0 |
| F-71 | 0 | 0 |
| F-72 | 1 | 0 |
| **total** | **235** | **0** |

**rows with 0 candidates:** F-4, F-68, F-69, F-70, F-71
check ok: 235 candidates, 235 unique ids, 1076332 B, byte-identical
[exit 0]
```

## Method notes / limits

- `--check` proves determinism *for a fixed corpus*: it re-scans and compares bytes plus id uniqueness.
  `E:/Modding/_BmAKgrab` is still being written by the judging side, so a `--check` run after new decode
  files appear will legitimately report a diff; re-run `--write` in that case. The JSONL carries no
  corpus fingerprint, by design — the diff message names the first differing character.
- Text hits are *name* hits, not value hits: e.g. `F-17`'s `StrafeRight` occurrences are key-binding
  lists (`Command="StrafeRight | ..."`). That is expected — the search half must not pre-judge; the
  judge rejects them cheaply (`>>>` marks the exact line).
- EXE sites are matched on the raw disp32/disp8 bytes, as in `chase09_native.py`; an offset that is also a
  common small constant therefore yields more sites than truly belong to the field. Over-inclusion is
  intentional here (that is the judge's job); it is why counts like `F-62` = 35 are windows, not verdicts.
- Nothing in `Research/BatmobileGrab/` was modified, no chase file was edited, `FOOTAGE.md` was not touched,
  nothing was launched or patched, and nothing was committed.

## Reproduce

```bash
python Tools/scripts/chase/chase_candidates.py --list-rows   # the row plan only
python Tools/scripts/chase/chase_candidates.py --write       # scan + write candidates.jsonl
python Tools/scripts/chase/chase_candidates.py --check       # re-scan, compare, verify unique ids
python Tools/scripts/chase/chase_judge.py --in E:/Modding/_BmAKgrab/chase/candidates.jsonl \
       --out E:/Modding/_BmAKgrab/chase/verdicts.jsonl      # the judging half, not run here
```
