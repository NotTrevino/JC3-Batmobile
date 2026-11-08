# Jebadiah 9B short-window retest — does a window that fits beat Qwen?

**Verdict up front: no. Jeb with short windows does not beat Qwen, and Qwen stays the default judge.**
Cutting the state to a window that fits Jeb's 2,048-token training limit removes the truncation
entirely (118 cut verdicts → **0 of 190**) and doubles Jeb's confidence — its best P(true) rises from
0.333 to **0.781** on a positive and from 0.472 to **0.682** on a found case — but it buys **no recall
at any threshold that keeps the negatives clean**: at 0.5 and above Jeb scores **0/20 positives, 0/8
found**, the same zeros as the whole-snippet run, against Qwen's **1/28** (F35 = 3.0). The four
verdicts Jeb now calls true at 0.5 all quote a literal that is not the member's value (`50.0` for
P07's known `0.333333`, `100.0` for P06's `1.25`, `89.0` for F7's `0.05`, `2.0` for F18's `0.0`).
The window fixed the truncation, not the discrimination. Keep `chase_judge` (Qwen) as the default;
`jeb_judge.py` keeps the window because it is strictly cheaper (2.29 s/candidate vs 4.18) and no
longer loses evidence, but it is not the judge to run.

## What changed in `jeb_judge.py`

Backup first, as required: `Tools/scripts/chase/jeb_judge.py.bak-20261106` is the pre-retest file
(whole snippet as the state). Reverting is
`cp Tools/scripts/chase/jeb_judge.py.bak-20261106 Tools/scripts/chase/jeb_judge.py`.

`state()` now builds the candidate from `window(snippet, offset, member)` instead of the whole
snippet:

- **Budget** `WINDOW_CHARS = 2400` (~600 tokens at ~4 chars/token) and `WINDOW_LINES = 12` for the
  disassembly shape. A snippet already inside the character budget is passed **unchanged** — the
  budget is tokens, so a short text record (e.g. a 21-line / 556-char JSON default block) is not
  line-trimmed for nothing. That distinction matters: trimming those by line count is what would
  throw away the `"value": 3.0` line.
- **Anchor** `_anchor()` picks, in order: the line that stores into the member's offset
  (`[reg+0x2d8]`), the line that **names the member** (a text record's field key), the annotate
  comment (`; [0x..] = float X`), then a float literal. The window grows outward from that line,
  one line at a time, while it stays inside 12 lines / 2400 chars. The annotate comment survives
  because it sits on the store's own line.
- **Versioning** `WINDOW_LINES`, `WINDOW_CHARS` and a new `WINDOW_SPEC` string are folded into
  `prompt_version()`, so this run has its own folder (`jeb_9440028e_v1search`) and nothing overwrites
  the whole-snippet calibration (`jeb_340c7b55_v1search`).

Worked example, F35 `ImpactShakeAbandonedVehicleFactor` (the case Qwen wins): the
`chase2_defaults.json:151` candidate is 21 lines / 556 chars, so it is now passed whole and keeps
`"field": "F-35 ImpactShakeAbandonedVehicleFactor"` … `"value": 3.0`; the 21-line / 5,623-char
`calib.jsonl:28` candidate is trimmed to 9 lines / 2,317 chars anchored on the member's own record
and also keeps `3.0`. Before the anchor fix the same record was trimmed from line 0 and the `3.0`
line fell outside the window.

## Method

- **38 calibration cases**, the same `calib.jsonl` (20 positive, 8 found, 10 negative), frozen
  `chase_candidates_v1` search half, `--max 6` — the same search half and cap the stored Qwen run and
  the stored whole-snippet Jeb run used, so the difference measured is the window, not the list. The
  lists are near-identical but not byte-identical: the `v1` search output has drifted slightly between
  runs (Qwen judged 186 verdicts, both Jeb runs 190; P20 has 2 candidates for Qwen and 4 for Jeb), so
  the comparison is the same frozen list and cap, not a replayed hand-off.
- **One judge server at a time.** Jeb's llama-server on `:8081`
  (`E:\AI\agent_jebadiah-9b-q5.bat`, `/health` → `{"status":"ok"}`, `/v1/models` → `jebadiah-9b`,
  `jebadiah-9b-v2-1-Q5_K_M.gguf`) was the only one listening; `:8080` was checked and closed for the
  whole run, so the Qwen numbers below are the stored `51c8dd3c_v1search` run, not a new call.
- Scoring is `chase_calibrate.py`'s: a `found=true` counts as right only when the value equals the
  known value (1e-6); any `found=true` on a negative is a false positive; `unparsable` is a verdict
  with no answer.
- Thresholds are swept on the **stored P(true)** (`--sweep`), no model call, and the literal compared
  at a new threshold is the `lit` the window itself shows.

## Recall and false positives next to Qwen

| judge | prompt | search | cases | reachable | positive recall | found recall | precision | negative FP (cases / verdicts) | unparsable | s/candidate | cut verdicts |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen (default) | `51c8dd3c` | v1 | 38/38 | 28/28 | 0.000 (0/20) | 0.125 (1/8) | 1.000 | 0/10 / 0 | 0 | 5.63 | — |
| jeb, whole snippet | `340c7b55` | v1 | 38/38 | 28/28 | 0.000 (0/20) | 0.000 (0/8) | 0.000 | 0/10 / 0 | 0 | 4.18 | 118/190 |
| jeb, short window | `9440028e` | v1 | 38/38 | 28/28 | 0.000 (0/20) | 0.000 (0/8) | 0.000 | 0/10 / 0 | 0 | 2.29 | **0/190** |

Read the last column with the first row: the window did exactly what it was asked to do — it removed
every truncation (0 warnings at all across 190 verdicts) and made Jeb 1.8× faster — and the recall
columns did not move. Qwen still finds F35 = 3.0 and Jeb still does not.

## Threshold sweep on the stored P(true) (verbatim)

`python Tools/scripts/chase/chase_calibrate.py --sweep 0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9`

```
sweep of stored P(true) in E:\Modding\_gamedata\BmAKgrab\chase\calib_runs\jeb_9440028e_v1search (no model call)

| threshold | positive recall | found recall | negatives with a false positive | false-positive verdicts | found=true total |
|---:|---:|---:|---:|---:|---:|
| 0.1 | 2/20 | 0/8 | 5/10 | 11 | 79 |
| 0.2 | 1/20 | 0/8 | 4/10 | 7 | 43 |
| 0.3 | 0/20 | 0/8 | 3/10 | 3 | 17 |
| 0.4 | 0/20 | 0/8 | 1/10 | 1 | 8 |
| 0.5 | 0/20 | 0/8 | 0/10 | 0 | 4 |
| 0.6 | 0/20 | 0/8 | 0/10 | 0 | 4 |
| 0.7 | 0/20 | 0/8 | 0/10 | 0 | 1 |
| 0.8 | 0/20 | 0/8 | 0/10 | 0 | 0 |
| 0.9 | 0/20 | 0/8 | 0/10 | 0 | 0 |

best at zero false positives: threshold 0.5 -> positive recall 0/20, found recall 0/8, false positives 0/10

stored verdicts 190; with warnings 0, of them snippet cut to Jeb's 2,048-token limit 0
- positive: 106 verdicts, max P(true) 0.781 (P07 exe 0x14016b9d8), verdicts at or above 0.5: 2
- found: 35 verdicts, max P(true) 0.682 (F7 exe 0x140c93074), verdicts at or above 0.5: 2
- negative: 49 verdicts, max P(true) 0.407 (N05 E:/Modding/_gamedata/BmAKgrab/chase/sim_cdo_07.json:494), verdicts at or above 0.5: 0
```

There is no threshold that both finds something and stays clean:

- **0.5 and above** is clean (0/10 negative cases) but productively empty — 4 `found=true`, none right.
  This is the setting to keep if Jeb were ever used, and at it Jeb returns nothing Qwen does not
  also get wrong.
- **0.4** starts firing a negative (N05, p=0.4066 — unchanged from the whole-snippet run) and still
  finds nothing right.
- **0.1–0.2** finally recalls two positives, at the price of a false positive in 5 of 10 negative
  cases (11 verdicts at 0.1). A judge that trades three negative cases for one positive is not a
  judge; that is the same failure the whole-snippet run showed at 0.3.

## What the window did to the scores

The four verdicts Jeb calls true at 0.5, with the literal the window gives it:

| case | kind | known | P(true) | literal | source |
|---|---|---|---:|---:|---|
| P07 | positive | 0.333333 | 0.7806 | `50.0` | `exe 0x14016b9d8` |
| F7 | found | 0.05 | 0.6821 | `89.0` | `exe 0x140c93074` |
| F18 | found | 0.0 | 0.6653 | `2.0` | `exe 0x1403ffc53` |
| P06 | positive | 1.25 | 0.6586 | `100.0` | `exe 0x140124b63` |

Best P(true) per case moved the way a shorter, cleaner state should move it — and the ordering did
not become usable. Per kind (best verdict in the case, threshold 0.5):

- positive: 20 cases, max 0.781 (P07), 2 cases at or above 0.5 — both the wrong literal;
- found: 8 cases, max 0.682 (F7), 2 cases at or above 0.5 — both the wrong literal;
- negative: 10 cases, max 0.407 (N05), 0 cases at or above 0.5.

The top negative (0.407) still sits above 18 of the 20 positives, and the positive range
(0.102–0.781) still overlaps the negative range (0.013–0.407). Short windows raise confidence
unevenly, and mostly not on the negatives: the mean best P(true) per case goes 0.187 → 0.255 on the
positives and 0.333 → 0.452 on the found cases, but only 0.154 → 0.157 on the negatives — N05 is
0.4066 now against 0.4066 before, N02 0.3304 against 0.3304, N01 0.3223 against 0.3223. Confidence
up on the cases Jeb should fire on, flat on the ones it should not — and still 0/28 right at 0.5.

`--compare` against Qwen, verbatim:

```
| case | kind | known | qwen found=true (value) | jeb found=true (p, value) | provenance says |
|---|---|---|---|---|---|
| P06 | positive | 1.25 | - | exe 0x140124b63 p=0.6586 = '100.0' | neither right (known 1.25) |
| P07 | positive | 0.333333 | - | exe 0x14016b9d8 p=0.7806 = '50.0' | neither right (known 0.333333) |
| F7 | found | 0.05 | - | exe 0x140c93074 p=0.6821 = '89.0' | neither right (known 0.05) |
| F18 | found | 0.0 | - | exe 0x1403ffc53 p=0.6653 = '2.0' | neither right (known 0.0) |
| F35 | found | 3.0 | E:/Modding/_BmAKgrab/chase/chase2_defaults.json:151 = '3.0' | - | qwen right (3.0) |

5 case(s) where the two judges disagree
```

Five disagreements now (one before): Jeb has started answering, and every new answer is wrong; the
one answer that is right is still Qwen's. That is a worse relative position than the whole-snippet
run, where Jeb at least abstained, not a better one.

## Why short windows do not close the gap

1. **The window fixes the input; the decision is still not the question.** Jeb answers "is the
   nearest literal in this window the member's default", and it says yes to `50.0`, `100.0`, `89.0`,
   `2.0` when the member's defaults are `0.333333`, `1.25`, `0.05`, `0.0`. Cutting to one store makes
   the wrong store look more like the only store — the confidence gain is on the wrong line.
2. **Jeb cannot read `value` out of a record.** `literal()` is a regex over the window, so on the
   JSON candidates it returns the first number it sees even when the verdict is right, and on
   `": 3.0`-style forms it returns nothing. F35 is the case that matters and it is a text record.
3. **No separation at the top.** The best negative is still 0.407 and the positives' median is below
   it. A threshold of 0.5 keeps the negatives clean only because it also throws away everything.

## Is Qwen still the default?

Yes. `chase_calibrate.py`'s default judge is `qwen` and this retest does not give a reason to change
it: Qwen's 1/8 found recall (F35 = 3.0, precision 1.000, 0 false positives) beats Jeb's 0/28 at every
threshold that keeps the negatives clean. The judge choice remains the second problem anyway — the
live search half still returns 0 candidates for these members, so `store_verdict` in
`chase_candidates.py` is still the first thing to fix.

What Jeb has going for it, unchanged: no unparsable verdicts, half Qwen's latency with the trimmed
window (2.29 vs 5.63 s/candidate), and a clean 0 false positives on the negatives at 0.5.

## Reproduce and revert

```
python Tools/scripts/chase/chase_calibrate.py --run   --judge jeb --threshold 0.5 --search v1 --max 6
python Tools/scripts/chase/chase_calibrate.py --score
python Tools/scripts/chase/chase_calibrate.py --sweep 0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9
python Tools/scripts/chase/chase_calibrate.py --compare
python Tools/scripts/chase/chase_calibrate.py --render --report tmp/freebuff/reports/jeb-short-window-retest.md
python Tools/scripts/chase/chase_calibrate.py --check  --report tmp/freebuff/reports/jeb-short-window-retest.md
```

Revert the window: `cp Tools/scripts/chase/jeb_judge.py.bak-20261106 Tools/scripts/chase/jeb_judge.py`
(brings back the whole-snippet state and prompt version `340c7b55`; the whole-snippet run is still on
disk under `jeb_340c7b55_v1search`). The short-window run stays under
`jeb_9440028e_v1search`, so neither calibration overwrites the other.

## Calibration (generated)

<!-- CALIB-BEGIN -->
<!-- generated by Tools/scripts/chase/chase_calibrate.py --render; do not hand-edit -->

| judge | prompt | search | cases run | reachable | positive recall | found recall | precision | negative FP (cases / verdicts) | unparsable | s/candidate |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen | `51c8dd3c` | current | 38/38 | 0/28 | 0.000 (0/20) | 0.000 (0/8) | 0.000 | 0/10 / 0 | 0 (0.000) | 0.00 |
| qwen | `51c8dd3c` | v1 | 38/38 | 28/28 | 0.000 (0/20) | 0.125 (1/8) | 1.000 | 0/10 / 0 | 0 (0.000) | 5.63 |
| jeb | `340c7b55` | v1 | 38/38 | 28/28 | 0.000 (0/20) | 0.000 (0/8) | 0.000 | 0/10 / 0 | 0 (0.000) | 4.18 |
| jeb | `9440028e` | v1 | 38/38 | 28/28 | 0.000 (0/20) | 0.000 (0/8) | 0.000 | 0/10 / 0 | 0 (0.000) | 2.29 |

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

### Cases — jeb prompt `9440028e` (search v1)

| id | kind | member | owner | offset | type | known | candidates | value in a candidate | found=true | right | wrong | unparsable |
|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| P01 | positive | `TurnOnSpotFrontTorqueFactor` | RVehicleSimBatmobile | 0x1c8 | float | 0.8 | 6 | yes | 0 | 0 | 0 | 0 |
| P02 | positive | `TurnOnSpotRearTorqueFactor` | RVehicleSimBatmobile | 0x1cc | float | -0.8 | 6 | yes | 0 | 0 | 0 | 0 |
| P03 | positive | `TurnOnSpotModeEngineBrakingFactor` | RVehicleSimBatmobile | 0x1d0 | float | 2 | 6 | yes | 0 | 0 | 0 | 0 |
| P04 | positive | `TurningModeMaxSpeed` | RVehicleSimBatmobile | 0x2c4 | float | 600 | 6 | yes | 0 | 0 | 0 | 0 |
| P05 | positive | `BattleModeLatSlipScale` | RVehicleSimBatmobile | 0x2d4 | float | 0.75 | 6 | yes | 0 | 0 | 0 | 0 |
| P06 | positive | `BattleModeLongSlipScale` | RVehicleSimBatmobile | 0x2d8 | float | 1.25 | 6 | yes | 1 | 0 | 1 | 0 |
| P07 | positive | `BattleModeTurnOnSpotTorqueFactor` | RVehicleSimBatmobile | 0x2e0 | float | 0.333333 | 6 | yes | 1 | 0 | 1 | 0 |
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
| F7 | found | `AirControl` | Pawn | 0x448 | float | 0.05 | 6 | yes | 1 | 0 | 1 | 0 |
| F11 | found | `BattleModeCamFOV` | R3rdPersonCamera | 0x4fd0 | float | 60.0 | 3 | yes | 0 | 0 | 0 | 0 |
| F16 | found | `StrafeCooldown` | RVehicleBatmobileBase | 0x11e4 | float | 0.75 | 5 | yes | 0 | 0 | 0 | 0 |
| F18 | found | `StrafeForce` | RVehicleBatmobileBase | 0x11f8 | float | 0.0 | 6 | yes | 1 | 0 | 1 | 0 |
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

Per family (jeb `9440028e`): a: 20 cases, 0 recalled, 2 found=true (0 right), b: 8 cases, 0 recalled, 2 found=true (0 right), c: 10 cases, 0 recalled, 0 found=true (0 right)
<!-- CALIB-END -->
