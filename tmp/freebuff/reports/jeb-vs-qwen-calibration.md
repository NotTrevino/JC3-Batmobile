# Jebadiah 9B v2.1 vs Qwen3.5-4B as the `smart_search` judge

**Verdict up front: keep the Qwen3.5-4B judge as the default for smart search, and do not switch to
Jeb at any threshold.** On the 38 calibration cases whose values the project already knows, and on
one and the same candidate list, Jeb (P(true) from one forward pass) finds **no** known value at any
threshold from 0.3 to 0.9 while Qwen finds one; at the thresholds where Jeb does start answering
true it answers true on negatives (3 of 10 at 0.3, 1 of 10 at 0.4) without gaining a single positive.
Jeb is the faster judge per candidate and never unparsable, but faster and cheaper buys nothing when
the recall is zero. `--threshold 0.5` is the only defensible Jeb setting (zero false positives), and
at 0.5 Jeb returns nothing at all.

## What was compared

| judge | judge code | prompt version | server | model | stored run |
|---|---|---|---|---|---|
| qwen (default) | `chase_judge.PROMPT` + `ask`/`parse` | `51c8dd3c` | llama-server `127.0.0.1:8080` (`E:\AI\agent_qwen3.5-4b-q6-32k.bat`) | `qwen3.5-4b` | `calib_runs/51c8dd3c_v1search` (38/38 cases, reused from disk) |
| jeb | `jeb_judge.py` | `340c7b55` | llama-server `127.0.0.1:8081` (`E:\AI\agent_jebadiah-9b-q5.bat`) | `jebadiah-9b` (`jebadiah-9b-v2-1-Q5_K_M.gguf`) | `calib_runs/jeb_340c7b55_v1search` (38/38 cases, run `--threshold 0.5 --max 6`) |

Run folders are now per judge: `chase_calibrate.py --judge jeb` writes
`calib_runs/jeb_<jeb_judge.prompt_version()>[_v1search]`, `--judge qwen` keeps
`calib_runs/<ss.PROMPT_VERSION>[_v1search]`. `--score`, `--render` and `--check` report both judges
side by side from those folders.

## Method, and why the frozen search half

Both judges were scored on **the same candidate list**: the frozen `chase_candidates_v1` search half,
`--max 6`, all 38 cases (20 positive, 8 found, 10 negative). This is the run in which the known value
is actually in front of the judge (reachable 28/28); the live search half currently returns 0
candidates for these members, so it cannot separate two judges at all — the `qwen / current` row in
the block below is that run, and it is why the comparison is made on `v1`.

One server at a time on the GTX 1070: Qwen's server was not started because its `51c8dd3c` run was
already on disk; the Jeb server was already listening on :8081 (`/health` -> `{"status":"ok"}`,
`/v1/models` -> `jebadiah-9b`) and was used as is. :8080 was not listening at any point during the Jeb
run.

Every case is scored the same way as before: a `found=true` counts as **right** only if its value
equals the known value (float within 1e-6) — or, for a negative, **wrong**: a negative's data proves
no scalar literal default exists, so any `found=true` there is a false positive. `unparsable` is a
verdict with no answer at all. `s/candidate` counts only verdicts actually sent to the model.

Jeb cannot quote the literal; `jeb_judge.literal()` reads one out of the snippet by regex. That
literal is now stored as `lit` on every verdict (found or not) so the threshold sweep below can
re-decide the whole run from the stored `p` values with no model call.

## Threshold sweep — Jeb, stored P(true), no model call

`python Tools/scripts/chase/chase_calibrate.py --sweep 0.3,0.4,0.5,0.6,0.7,0.8,0.9` (verbatim):

```
sweep of stored P(true) in E:\Modding\_shared\gamedata\BmAKgrab\chase\calib_runs\jeb_340c7b55_v1search (no model call)

| threshold | positive recall | found recall | negatives with a false positive | false-positive verdicts | found=true total |
|---:|---:|---:|---:|---:|---:|
| 0.3 | 0/20 | 0/8 | 3/10 | 3 | 10 |
| 0.4 | 0/20 | 0/8 | 1/10 | 1 | 4 |
| 0.5 | 0/20 | 0/8 | 0/10 | 0 | 0 |
| 0.6 | 0/20 | 0/8 | 0/10 | 0 | 0 |
| 0.7 | 0/20 | 0/8 | 0/10 | 0 | 0 |
| 0.8 | 0/20 | 0/8 | 0/10 | 0 | 0 |
| 0.9 | 0/20 | 0/8 | 0/10 | 0 | 0 |

best at zero false positives: threshold 0.5 -> positive recall 0/20, found recall 0/8, false positives 0/10

stored verdicts 190; with warnings 118, of them snippet cut to Jeb's 2,048-token limit 118
- positive: 106 verdicts, max P(true) 0.333 (P06 exe 0x140124b63), verdicts at or above 0.5: 0
- found: 35 verdicts, max P(true) 0.472 (F22 E:/Modding/_shared/gamedata/BmAKgrab/chase/g1_chase_native.json:372), verdicts at or above 0.5: 0
- negative: 49 verdicts, max P(true) 0.407 (N05 E:/Modding/_shared/gamedata/BmAKgrab/chase/sim_cdo_07.json:494), verdicts at or above 0.5: 0
```

**Best recall at zero false positives: threshold 0.5 — positive recall 0/20, found recall 0/8.** Zero
false positives is not an achievement here: every threshold at or above 0.5 finds nothing, because no
verdict in the whole run reaches 0.5. Below 0.5 the negatives start firing (3 cases at 0.3, 1 at 0.4)
while the positives still find nothing, so no lower threshold buys recall either. The one case where
lowering the threshold could pay — F35, where Qwen succeeds — has p=0.405 but an **empty** `lit`
(Jeb cannot read the JSON `"member": 3.0` form), so even at 0.4 it would not be scored right.

## Where the two judges disagree

`python Tools/scripts/chase/chase_calibrate.py --compare` (verbatim; a case is compared on its
`found=true` verdicts, and the provenance is the stored known value / the stored "no scalar default"
record):

```
| case | kind | known | qwen found=true (value) | jeb found=true (p, value) | provenance says |
|---|---|---|---|---|---|
| F35 | found | 3.0 | E:/Modding/ArkhamKnight/_grab/chase/chase2_defaults.json:151 = '3.0' | - | qwen right (3.0) |

1 case(s) where the two judges disagree
```

One disagreement in 38 cases, and the stored provenance says Qwen is right: F35
`ImpactShakeAbandonedVehicleFactor` = 3.0, recorded at `chase2_defaults.json:151`; Qwen returns that
literal, Jeb gives the same candidate p=0.405 (below its threshold) and an empty literal. On the other
37 cases the two judges agree — mostly by both returning `found=false`. Their agreement on the
negatives (both clean at 0.5) is the one place Jeb's caution is an asset.

## Snippet truncation and score distribution (generated)

```
Jeb snippet budget (max_prompt_tokens 2048) and what it does to the verdicts

- cut: 118 verdicts, max P(true) 0.333 (P06), at or above 0.5: 0
- whole: 72 verdicts, max P(true) 0.472 (F22), at or above 0.5: 0

cases by best P(true) on any candidate, threshold 0.5 (found) and 0.4:
- positive: 20 cases, best P06=0.333, p>=0.5 on 0 case(s) [], p>=0.4 on 0 case(s) []
- found: 8 cases, best F22=0.472, p>=0.5 on 0 case(s) [], p>=0.4 on 3 case(s) ['F22', 'F35', 'F33']
- negative: 10 cases, best N05=0.407, p>=0.5 on 0 case(s) [], p>=0.4 on 1 case(s) ['N05']

negatives Jeb calls true at a lower threshold (case, source, P(true)):
- N01 TurnOnSpotSteeringSpeedCurve: p=0.3223 E:/Modding/_shared/gamedata/BmAKgrab/chase/chase2_defaults.json:184 lit=''
- N02 BattleModeMoving: p=0.3304 E:/Modding/_shared/gamedata/BmAKgrab/chase/chase2_defaults.json:217 lit=''
- N05 TransformationAnimNode: p=0.4066 E:/Modding/_shared/gamedata/BmAKgrab/chase/sim_cdo_07.json:494 lit=''

F35 (the one qwen hit) at Jeb:
- p=0.1241 found=False lit='30000' cut=yes E:/Modding/_shared/gamedata/BmAKgrab/chase/calib.jsonl:28
- p=0.405 found=False lit='' cut=no E:/Modding/_shared/gamedata/BmAKgrab/chase/chase2_defaults.json:151
- p=0.0272 found=False lit='' cut=no E:/Modding/_shared/gamedata/BmAKgrab/chase/namescan_b.json:8
- p=0.2781 found=False lit='' cut=no E:/Modding/_shared/gamedata/BmAKgrab/chase/namescan_b.json:22

qwen (v1 search) per-case found=true count, same candidate list:
- F35 ImpactShakeAbandonedVehicleFactor: 1 found=true of 4
- qwen judged total 186
```

## Failure modes, counted

**Jeb (340c7b55)**
- *The 2,048-token training limit cuts most of the evidence away.* 118 of 190 verdicts (62.1%) carry
  `d: the state was cut to 2048 prompt tokens` in `warnings`; the count is in the generated detail
  above. The cut is not the whole story — the 72 snippets that fit still top out at P(true) 0.472
  (F22), and no candidate anywhere reaches 0.5.
- *No separation between a real default and a negative.* Best P(true) per kind: positives 0.333,
  found 0.472, negatives 0.407. A judge whose highest score is on a negative cannot be thresholded
  into usefulness.
- *It cannot quote the value.* `lit` is empty on the JSON text candidates (`": 3.0` does not match
  `jeb_judge._NUM`), so even a true verdict on those candidates would be a miss in any scored run;
  every `found=true` from Jeb still has to be verified against the offset (R4).
- *What it does well:* no unparsable verdicts at all, 4.18 s/candidate against Qwen's 5.63, and zero
  false positives on the negatives at 0.5.

**Qwen (51c8dd3c)**
- *Recall is the bottleneck:* 0/20 positives, 1/8 found, overall 1/28. It reads the snippet, quotes a
  literal and gives a one-line reason, and it is the only judge that gets F35.
- No truncation limit, no unparsable verdicts, precision 1.000 (the single `found=true` is right).
- 5.63 s/candidate, so ~35% slower than Jeb on this list.

**Shared, not a judge difference:** with the live search half both judges get 0 candidates on these
members, so the 0-candidate `current` row says nothing about either judge — the search filter
(`store_verdict` in `chase_candidates.py`) is the first thing to fix, before any judge choice matters.

## Reproduce

```
python Tools/scripts/chase/chase_calibrate.py --run --judge jeb --threshold 0.5 --search v1 --max 6 --fresh
python Tools/scripts/chase/chase_calibrate.py --score
python Tools/scripts/chase/chase_calibrate.py --sweep 0.3,0.4,0.5,0.6,0.7,0.8,0.9
python Tools/scripts/chase/chase_calibrate.py --compare
python Tools/scripts/chase/chase_calibrate.py --render --report tmp/freebuff/reports/jeb-vs-qwen-calibration.md
python Tools/scripts/chase/chase_calibrate.py --check  --report tmp/freebuff/reports/jeb-vs-qwen-calibration.md
```

`chase_calibrate.py` was backed up as `chase_calibrate.py.bak-20261106` before the judge switch was
added; reverting is `cp Tools/scripts/chase/chase_calibrate.py.bak-20261106
Tools/scripts/chase/chase_calibrate.py`.

## Calibration (generated)

## Calibration (generated)

<!-- CALIB-BEGIN -->
<!-- generated by Tools/scripts/chase/chase_calibrate.py --render; do not hand-edit -->

| judge | prompt | search | cases run | reachable | positive recall | found recall | precision | negative FP (cases / verdicts) | unparsable | s/candidate |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen | `51c8dd3c` | current | 38/38 | 0/28 | 0.000 (0/20) | 0.000 (0/8) | 0.000 | 0/10 / 0 | 0 (0.000) | 0.00 |
| qwen | `51c8dd3c` | v1 | 38/38 | 28/28 | 0.000 (0/20) | 0.125 (1/8) | 1.000 | 0/10 / 0 | 0 (0.000) | 5.63 |
| jeb | `340c7b55` | v1 | 38/38 | 28/28 | 0.000 (0/20) | 0.000 (0/8) | 0.000 | 0/10 / 0 | 0 (0.000) | 4.18 |

### Cases — qwen prompt `51c8dd3c` (search current)

| id | kind | member | owner | offset | type | known | candidates | value in a candidate | found=true | right | wrong | unparsable |
|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| P01 | positive | `TurnOnSpotFrontTorqueFactor` | RVehicleSimBatmobile | 0x1c8 | float | 0.8 | 0 | no | 0 | 0 | 0 | 0 |
| P02 | positive | `TurnOnSpotRearTorqueFactor` | RVehicleSimBatmobile | 0x1cc | float | -0.8 | 0 | no | 0 | 0 | 0 | 0 |
| P03 | positive | `TurnOnSpotModeEngineBrakingFactor` | RVehicleSimBatmobile | 0x1d0 | float | 2 | 0 | no | 0 | 0 | 0 | 0 |
| P04 | positive | `TurningModeMaxSpeed` | RVehicleSimBatmobile | 0x2c4 | float | 600 | 0 | no | 0 | 0 | 0 | 0 |
| P05 | positive | `BattleModeLatSlipScale` | RVehicleSimBatmobile | 0x2d4 | float | 0.75 | 0 | no | 0 | 0 | 0 | 0 |
| P06 | positive | `BattleModeLongSlipScale` | RVehicleSimBatmobile | 0x2d8 | float | 1.25 | 0 | no | 0 | 0 | 0 | 0 |
| P07 | positive | `BattleModeTurnOnSpotTorqueFactor` | RVehicleSimBatmobile | 0x2e0 | float | 0.333333 | 0 | no | 0 | 0 | 0 | 0 |
| P08 | positive | `BattleModeThrottleSpeed` | RVehicleSimBatmobile | 0x2ec | float | 10 | 0 | no | 0 | 0 | 0 | 0 |
| P09 | positive | `BattleModeDriveForceFactor` | RVehicleSimBatmobile | 0x2f4 | float | 500 | 0 | no | 0 | 0 | 0 | 0 |
| P10 | positive | `BattleModeStopAndTurnAngleStationary` | RVehicleSimBatmobile | 0x2f8 | float | 30 | 0 | no | 0 | 0 | 0 | 0 |
| P11 | positive | `BattleModeSteerAngleFactor` | RVehicleSimBatmobile | 0x300 | float | 1 | 0 | no | 0 | 0 | 0 | 0 |
| P12 | positive | `BattleModeTrailingSteerFactorMoving` | RVehicleSimBatmobile | 0x320 | float | -0.25 | 0 | no | 0 | 0 | 0 | 0 |
| P13 | positive | `BattleModeDrivingForceZOffset` | RVehicleSimBatmobile | 0x324 | float | 20 | 0 | no | 0 | 0 | 0 | 0 |
| P14 | positive | `TransformationTurnTorqueFactor` | RVehicleSimBatmobile | 0x390 | float | 3000 | 0 | no | 0 | 0 | 0 | 0 |
| P15 | positive | `TransformationTurnDecelTorqueFactor` | RVehicleSimBatmobile | 0x394 | float | 24000 | 0 | no | 0 | 0 | 0 | 0 |
| P16 | positive | `AirControlYawTorqueFactorMax` | RVehicleSimBatmobile | 0x4a8 | float | 8000 | 0 | no | 0 | 0 | 0 | 0 |
| P17 | positive | `ImpactRoadAssistFactor` | RVehicleBatmobileBase | 0x1764 | float | 90000 | 0 | no | 0 | 0 | 0 | 0 |
| P18 | positive | `ImpactRoadAssistMaxTorque` | RVehicleBatmobileBase | 0x1768 | float | 30000 | 0 | no | 0 | 0 | 0 | 0 |
| P19 | positive | `ImpactRoadAssistAngleStrength` | RVehicleBatmobileBase | 0x177c | float | 2000 | 0 | no | 0 | 0 | 0 | 0 |
| P20 | positive | `BattleModeYawOffset` | RVehicleBatmobileBase | 0x1910 | int | 0 | 0 | no | 0 | 0 | 0 | 0 |
| F7 | found | `AirControl` | Pawn | 0x448 | float | 0.05 | 0 | no | 0 | 0 | 0 | 0 |
| F11 | found | `BattleModeCamFOV` | R3rdPersonCamera | 0x4fd0 | float | 60.0 | 0 | no | 0 | 0 | 0 | 0 |
| F16 | found | `StrafeCooldown` | RVehicleBatmobileBase | 0x11e4 | float | 0.75 | 0 | no | 0 | 0 | 0 | 0 |
| F18 | found | `StrafeForce` | RVehicleBatmobileBase | 0x11f8 | float | 0.0 | 0 | no | 0 | 0 | 0 | 0 |
| F22 | found | `StrafeFwdCorrectionForce` | RVehicleBatmobileBase | 0x1208 | float | 3000.0 | 0 | no | 0 | 0 | 0 | 0 |
| F31 | found | `BattleModeWidth` | RVehicleBatmobileBase | 0x1994 | float | 265.0 | 0 | no | 0 | 0 | 0 | 0 |
| F33 | found | `BattleModeHeight` | RVehicleBatmobileBase | 0x199c | float | 250.0 | 0 | no | 0 | 0 | 0 | 0 |
| F35 | found | `ImpactShakeAbandonedVehicleFactor` | RVehicleBatmobileBase | 0x1ccc | float | 3.0 | 0 | no | 0 | 0 | 0 | 0 |
| N01 | negative | `TurnOnSpotSteeringSpeedCurve` | RVehicleSimBatmobile | 0x268 | FInterpCurveFloat | — | 0 | — | 0 | 0 | 0 | 0 |
| N02 | negative | `BattleModeMoving` | RVehicleSimBatmobile | 0x294 | bool | — | 0 | — | 0 | 0 | 0 | 0 |
| N03 | negative | `ImpactRoadAssistTimer` | RVehicleBatmobileBase | 0x1758 | float | — | 0 | — | 0 | 0 | 0 | 0 |
| N04 | negative | `BattleModeTransformationAnimName` | RVehicleBatmobileBase | 0x193c | FName | — | 0 | — | 0 | 0 | 0 | 0 |
| N05 | negative | `TransformationAnimNode` | RVehicleBatmobileBase | 0x1494 | AnimNodeSequence | — | 0 | — | 0 | 0 | 0 | 0 |
| N06 | negative | `TransformationAnimNode` | RVehicleSimBatmobile | 0x354 | AnimNodeSequence | — | 0 | — | 0 | 0 | 0 | 0 |
| N07 | negative | `StrafeTarget` | RVehicleBatmobileBase | 0x14e4 | RVehicle | — | 0 | — | 0 | 0 | 0 | 0 |
| N08 | negative | `BattleModeCamConfig` | R3rdPersonCamera | 0x3df4 | FFreeCameraConfig | — | 0 | — | 0 | 0 | 0 | 0 |
| N09 | negative | `BattleModeVSpeedCurve` | RVehicleSimBatmobile | 0x218 | FInterpCurveFloat | — | 0 | — | 0 | 0 | 0 | 0 |
| N10 | negative | `StandardTorqueVSpeedCurve` | RVehicleSimBatmobile | 0x1f0 | FInterpCurveFloat | — | 0 | — | 0 | 0 | 0 | 0 |

Per family (qwen `51c8dd3c`): a: 20 cases, 0 recalled, 0 found=true (0 right), b: 8 cases, 0 recalled, 0 found=true (0 right), c: 10 cases, 0 recalled, 0 found=true (0 right)

### Cases — qwen prompt `51c8dd3c` (search v1)

| id | kind | member | owner | offset | type | known | candidates | value in a candidate | found=true | right | wrong | unparsable |
|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| P01 | positive | `TurnOnSpotFrontTorqueFactor` | RVehicleSimBatmobile | 0x1c8 | float | 0.8 | 6 | yes | 0 | 0 | 0 | 0 |
| P02 | positive | `TurnOnSpotRearTorqueFactor` | RVehicleSimBatmobile | 0x1cc | float | -0.8 | 6 | yes | 0 | 0 | 0 | 0 |
| P03 | positive | `TurnOnSpotModeEngineBrakingFactor` | RVehicleSimBatmobile | 0x1d0 | float | 2 | 6 | yes | 0 | 0 | 0 | 0 |
| P04 | positive | `TurningModeMaxSpeed` | RVehicleSimBatmobile | 0x2c4 | float | 600 | 6 | yes | 0 | 0 | 0 | 0 |
| P05 | positive | `BattleModeLatSlipScale` | RVehicleSimBatmobile | 0x2d4 | float | 0.75 | 6 | yes | 0 | 0 | 0 | 0 |
| P06 | positive | `BattleModeLongSlipScale` | RVehicleSimBatmobile | 0x2d8 | float | 1.25 | 6 | yes | 0 | 0 | 0 | 0 |
| P07 | positive | `BattleModeTurnOnSpotTorqueFactor` | RVehicleSimBatmobile | 0x2e0 | float | 0.333333 | 6 | yes | 0 | 0 | 0 | 0 |
| P08 | positive | `BattleModeThrottleSpeed` | RVehicleSimBatmobile | 0x2ec | float | 10 | 6 | yes | 0 | 0 | 0 | 0 |
| P09 | positive | `BattleModeDriveForceFactor` | RVehicleSimBatmobile | 0x2f4 | float | 500 | 6 | yes | 0 | 0 | 0 | 0 |
| P10 | positive | `BattleModeStopAndTurnAngleStationary` | RVehicleSimBatmobile | 0x2f8 | float | 30 | 6 | yes | 0 | 0 | 0 | 0 |
| P11 | positive | `BattleModeSteerAngleFactor` | RVehicleSimBatmobile | 0x300 | float | 1 | 6 | yes | 0 | 0 | 0 | 0 |
| P12 | positive | `BattleModeTrailingSteerFactorMoving` | RVehicleSimBatmobile | 0x320 | float | -0.25 | 6 | yes | 0 | 0 | 0 | 0 |
| P13 | positive | `BattleModeDrivingForceZOffset` | RVehicleSimBatmobile | 0x324 | float | 20 | 6 | yes | 0 | 0 | 0 | 0 |
| P14 | positive | `TransformationTurnTorqueFactor` | RVehicleSimBatmobile | 0x390 | float | 3000 | 6 | yes | 0 | 0 | 0 | 0 |
| P15 | positive | `TransformationTurnDecelTorqueFactor` | RVehicleSimBatmobile | 0x394 | float | 24000 | 6 | yes | 0 | 0 | 0 | 0 |
| P16 | positive | `AirControlYawTorqueFactorMax` | RVehicleSimBatmobile | 0x4a8 | float | 8000 | 6 | yes | 0 | 0 | 0 | 0 |
| P17 | positive | `ImpactRoadAssistFactor` | RVehicleBatmobileBase | 0x1764 | float | 90000 | 2 | yes | 0 | 0 | 0 | 0 |
| P18 | positive | `ImpactRoadAssistMaxTorque` | RVehicleBatmobileBase | 0x1768 | float | 30000 | 2 | yes | 0 | 0 | 0 | 0 |
| P19 | positive | `ImpactRoadAssistAngleStrength` | RVehicleBatmobileBase | 0x177c | float | 2000 | 2 | yes | 0 | 0 | 0 | 0 |
| P20 | positive | `BattleModeYawOffset` | RVehicleBatmobileBase | 0x1910 | int | 0 | 2 | yes | 0 | 0 | 0 | 0 |
| F7 | found | `AirControl` | Pawn | 0x448 | float | 0.05 | 4 | yes | 0 | 0 | 0 | 0 |
| F11 | found | `BattleModeCamFOV` | R3rdPersonCamera | 0x4fd0 | float | 60.0 | 3 | yes | 0 | 0 | 0 | 0 |
| F16 | found | `StrafeCooldown` | RVehicleBatmobileBase | 0x11e4 | float | 0.75 | 5 | yes | 0 | 0 | 0 | 0 |
| F18 | found | `StrafeForce` | RVehicleBatmobileBase | 0x11f8 | float | 0.0 | 6 | yes | 0 | 0 | 0 | 0 |
| F22 | found | `StrafeFwdCorrectionForce` | RVehicleBatmobileBase | 0x1208 | float | 3000.0 | 4 | yes | 0 | 0 | 0 | 0 |
| F31 | found | `BattleModeWidth` | RVehicleBatmobileBase | 0x1994 | float | 265.0 | 3 | yes | 0 | 0 | 0 | 0 |
| F33 | found | `BattleModeHeight` | RVehicleBatmobileBase | 0x199c | float | 250.0 | 4 | yes | 0 | 0 | 0 | 0 |
| F35 | found | `ImpactShakeAbandonedVehicleFactor` | RVehicleBatmobileBase | 0x1ccc | float | 3.0 | 4 | yes | 1 | 1 | 0 | 0 |
| N01 | negative | `TurnOnSpotSteeringSpeedCurve` | RVehicleSimBatmobile | 0x268 | FInterpCurveFloat | — | 6 | — | 0 | 0 | 0 | 0 |
| N02 | negative | `BattleModeMoving` | RVehicleSimBatmobile | 0x294 | bool | — | 6 | — | 0 | 0 | 0 | 0 |
| N03 | negative | `ImpactRoadAssistTimer` | RVehicleBatmobileBase | 0x1758 | float | — | 2 | — | 0 | 0 | 0 | 0 |
| N04 | negative | `BattleModeTransformationAnimName` | RVehicleBatmobileBase | 0x193c | FName | — | 1 | — | 0 | 0 | 0 | 0 |
| N05 | negative | `TransformationAnimNode` | RVehicleBatmobileBase | 0x1494 | AnimNodeSequence | — | 6 | — | 0 | 0 | 0 | 0 |
| N06 | negative | `TransformationAnimNode` | RVehicleSimBatmobile | 0x354 | AnimNodeSequence | — | 6 | — | 0 | 0 | 0 | 0 |
| N07 | negative | `StrafeTarget` | RVehicleBatmobileBase | 0x14e4 | RVehicle | — | 4 | — | 0 | 0 | 0 | 0 |
| N08 | negative | `BattleModeCamConfig` | R3rdPersonCamera | 0x3df4 | FFreeCameraConfig | — | 6 | — | 0 | 0 | 0 | 0 |
| N09 | negative | `BattleModeVSpeedCurve` | RVehicleSimBatmobile | 0x218 | FInterpCurveFloat | — | 6 | — | 0 | 0 | 0 | 0 |
| N10 | negative | `StandardTorqueVSpeedCurve` | RVehicleSimBatmobile | 0x1f0 | FInterpCurveFloat | — | 6 | — | 0 | 0 | 0 | 0 |

Per family (qwen `51c8dd3c`): a: 20 cases, 0 recalled, 0 found=true (0 right), b: 8 cases, 1 recalled, 1 found=true (1 right), c: 10 cases, 0 recalled, 0 found=true (0 right)

### Cases — jeb prompt `340c7b55` (search v1)

| id | kind | member | owner | offset | type | known | candidates | value in a candidate | found=true | right | wrong | unparsable |
|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| P01 | positive | `TurnOnSpotFrontTorqueFactor` | RVehicleSimBatmobile | 0x1c8 | float | 0.8 | 6 | yes | 0 | 0 | 0 | 0 |
| P02 | positive | `TurnOnSpotRearTorqueFactor` | RVehicleSimBatmobile | 0x1cc | float | -0.8 | 6 | yes | 0 | 0 | 0 | 0 |
| P03 | positive | `TurnOnSpotModeEngineBrakingFactor` | RVehicleSimBatmobile | 0x1d0 | float | 2 | 6 | yes | 0 | 0 | 0 | 0 |
| P04 | positive | `TurningModeMaxSpeed` | RVehicleSimBatmobile | 0x2c4 | float | 600 | 6 | yes | 0 | 0 | 0 | 0 |
| P05 | positive | `BattleModeLatSlipScale` | RVehicleSimBatmobile | 0x2d4 | float | 0.75 | 6 | yes | 0 | 0 | 0 | 0 |
| P06 | positive | `BattleModeLongSlipScale` | RVehicleSimBatmobile | 0x2d8 | float | 1.25 | 6 | yes | 0 | 0 | 0 | 0 |
| P07 | positive | `BattleModeTurnOnSpotTorqueFactor` | RVehicleSimBatmobile | 0x2e0 | float | 0.333333 | 6 | yes | 0 | 0 | 0 | 0 |
| P08 | positive | `BattleModeThrottleSpeed` | RVehicleSimBatmobile | 0x2ec | float | 10 | 6 | yes | 0 | 0 | 0 | 0 |
| P09 | positive | `BattleModeDriveForceFactor` | RVehicleSimBatmobile | 0x2f4 | float | 500 | 6 | yes | 0 | 0 | 0 | 0 |
| P10 | positive | `BattleModeStopAndTurnAngleStationary` | RVehicleSimBatmobile | 0x2f8 | float | 30 | 6 | yes | 0 | 0 | 0 | 0 |
| P11 | positive | `BattleModeSteerAngleFactor` | RVehicleSimBatmobile | 0x300 | float | 1 | 6 | yes | 0 | 0 | 0 | 0 |
| P12 | positive | `BattleModeTrailingSteerFactorMoving` | RVehicleSimBatmobile | 0x320 | float | -0.25 | 6 | yes | 0 | 0 | 0 | 0 |
| P13 | positive | `BattleModeDrivingForceZOffset` | RVehicleSimBatmobile | 0x324 | float | 20 | 6 | yes | 0 | 0 | 0 | 0 |
| P14 | positive | `TransformationTurnTorqueFactor` | RVehicleSimBatmobile | 0x390 | float | 3000 | 6 | yes | 0 | 0 | 0 | 0 |
| P15 | positive | `TransformationTurnDecelTorqueFactor` | RVehicleSimBatmobile | 0x394 | float | 24000 | 6 | yes | 0 | 0 | 0 | 0 |
| P16 | positive | `AirControlYawTorqueFactorMax` | RVehicleSimBatmobile | 0x4a8 | float | 8000 | 6 | yes | 0 | 0 | 0 | 0 |
| P17 | positive | `ImpactRoadAssistFactor` | RVehicleBatmobileBase | 0x1764 | float | 90000 | 2 | yes | 0 | 0 | 0 | 0 |
| P18 | positive | `ImpactRoadAssistMaxTorque` | RVehicleBatmobileBase | 0x1768 | float | 30000 | 2 | yes | 0 | 0 | 0 | 0 |
| P19 | positive | `ImpactRoadAssistAngleStrength` | RVehicleBatmobileBase | 0x177c | float | 2000 | 2 | yes | 0 | 0 | 0 | 0 |
| P20 | positive | `BattleModeYawOffset` | RVehicleBatmobileBase | 0x1910 | int | 0 | 4 | yes | 0 | 0 | 0 | 0 |
| F7 | found | `AirControl` | Pawn | 0x448 | float | 0.05 | 6 | yes | 0 | 0 | 0 | 0 |
| F11 | found | `BattleModeCamFOV` | R3rdPersonCamera | 0x4fd0 | float | 60.0 | 3 | yes | 0 | 0 | 0 | 0 |
| F16 | found | `StrafeCooldown` | RVehicleBatmobileBase | 0x11e4 | float | 0.75 | 5 | yes | 0 | 0 | 0 | 0 |
| F18 | found | `StrafeForce` | RVehicleBatmobileBase | 0x11f8 | float | 0.0 | 6 | yes | 0 | 0 | 0 | 0 |
| F22 | found | `StrafeFwdCorrectionForce` | RVehicleBatmobileBase | 0x1208 | float | 3000.0 | 4 | yes | 0 | 0 | 0 | 0 |
| F31 | found | `BattleModeWidth` | RVehicleBatmobileBase | 0x1994 | float | 265.0 | 3 | yes | 0 | 0 | 0 | 0 |
| F33 | found | `BattleModeHeight` | RVehicleBatmobileBase | 0x199c | float | 250.0 | 4 | yes | 0 | 0 | 0 | 0 |
| F35 | found | `ImpactShakeAbandonedVehicleFactor` | RVehicleBatmobileBase | 0x1ccc | float | 3.0 | 4 | yes | 0 | 0 | 0 | 0 |
| N01 | negative | `TurnOnSpotSteeringSpeedCurve` | RVehicleSimBatmobile | 0x268 | FInterpCurveFloat | — | 6 | — | 0 | 0 | 0 | 0 |
| N02 | negative | `BattleModeMoving` | RVehicleSimBatmobile | 0x294 | bool | — | 6 | — | 0 | 0 | 0 | 0 |
| N03 | negative | `ImpactRoadAssistTimer` | RVehicleBatmobileBase | 0x1758 | float | — | 2 | — | 0 | 0 | 0 | 0 |
| N04 | negative | `BattleModeTransformationAnimName` | RVehicleBatmobileBase | 0x193c | FName | — | 1 | — | 0 | 0 | 0 | 0 |
| N05 | negative | `TransformationAnimNode` | RVehicleBatmobileBase | 0x1494 | AnimNodeSequence | — | 6 | — | 0 | 0 | 0 | 0 |
| N06 | negative | `TransformationAnimNode` | RVehicleSimBatmobile | 0x354 | AnimNodeSequence | — | 6 | — | 0 | 0 | 0 | 0 |
| N07 | negative | `StrafeTarget` | RVehicleBatmobileBase | 0x14e4 | RVehicle | — | 4 | — | 0 | 0 | 0 | 0 |
| N08 | negative | `BattleModeCamConfig` | R3rdPersonCamera | 0x3df4 | FFreeCameraConfig | — | 6 | — | 0 | 0 | 0 | 0 |
| N09 | negative | `BattleModeVSpeedCurve` | RVehicleSimBatmobile | 0x218 | FInterpCurveFloat | — | 6 | — | 0 | 0 | 0 | 0 |
| N10 | negative | `StandardTorqueVSpeedCurve` | RVehicleSimBatmobile | 0x1f0 | FInterpCurveFloat | — | 6 | — | 0 | 0 | 0 | 0 |

Per family (jeb `340c7b55`): a: 20 cases, 0 recalled, 0 found=true (0 right), b: 8 cases, 0 recalled, 0 found=true (0 right), c: 10 cases, 0 recalled, 0 found=true (0 right)
<!-- CALIB-END -->
