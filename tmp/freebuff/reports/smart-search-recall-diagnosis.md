# smart_search recall: why both judges score 0/20, and the route change that recovers 22/28

2026-11-06. `jeb-vs-qwen-calibration.md` scored Qwen 0/20 positive, 1/8 found, and Jeb 0/20, 0/8,
on the same frozen `v1` candidate list. This report classifies every one of the 38 misses from the
stored `calib_runs`, shows the snippets, and tests the one change that matters: the **route**.

**Answer.** The judges are not the bottleneck. `reach = true` on all 28 known-value cases is
**contaminated**: the `v1` candidates for 23 of the 28 are the project's own calibration/analysis
files (`calib.jsonl`, `chase2_verify.json`, `namescan*.json`) or raw exe hits — the literal is there
because the answer key is there. The judge rejects them ("JSON analysis record, not a game file")
and that rejection is **correct**. The 19 positive values live in a decoded table,
`Research/BatmobileGrab/MODES.md`, which the text route never read; the other three are in
`g1_chase_native.json` / `chase2_defaults.json`, which it read only for some cases. Adding the
table as a row-trimmed route raises known-value retrieval from **1/28 to 22/28** (positive
retrieval 19/20) with **0/10** negative rows carrying a literal. The judge re-run could not be
completed because the Qwen server stopped accepting connections (WinError 10061); the route change
is therefore **tested at the retrieval layer and not applied to code**.

Labels: **decoded** = read from the stored run/source named; **derived** = arithmetic on it;
**UNKNOWN** = absent, with what settles it.

## 0. Change statement (AGENTS.md)

| item | value |
|---|---|
| intended change | add one diagnosis report; no tool or judge is modified |
| file | `tmp/freebuff/reports/smart-search-recall-diagnosis.md` (this file) |
| why this file | the brief names it; every number is re-derived from the stored runs by `Tools/scripts/chase/t_smart_diag.py --check` |
| reverted by | deleting this file. No source, prompt, run or game file was edited, so no backup was needed |

## 1. Classification method

For each of the 38 cases, the stored record (`calib_runs/<run>/<id>.json`) carries `reach`,
`reach_sources`, `verdicts[]` with `source`, `why`, `warnings`, and (Jeb) `p`/`lit`.

A case is a **SEARCH** miss when none of its candidate sources is a decoded game-data file. It is a
**WINDOW** miss when the value is in a game-data source but outside the snippet the judge saw. It is
a **PROMPT** miss when a prompt rule (offset-table, stack-local, per-frame, JSON-record) rejects a
true default in a decoded file. Otherwise it is a **JUDGE** miss.

Game-data sources: `sim_cdo*.json`, `chase2_defaults*.json`, `g1_chase_native.json`,
`svehicle_cdo.json`, `value_cdo_08*.json`, `camera_cdo.json`, `wheel_cdo.json`,
`vehiclebase_cdo.json`, `chase2_native2*.json`. Tool sources: `calib.jsonl`,
`chase2_verify.json`, `namescan*.json`, `verdicts*.jsonl`, `pkg_*`, `chase2_04*`.

`decoded` — result, per judge:

| class | qwen | jeb | which cases |
|---|---:|---:|---|
| (a) SEARCH | **23** | **23** | all 20 positives except P12, plus F7, F18, F31 (and F35 for Jeb) |
| (b) WINDOW | **0** | **0** | none at case level; see §4 |
| (c) JUDGE | **1** | **5** | qwen F16; jeb F11, F16, F22, F33, F35 |
| (d) PROMPT | **3** | **0** | qwen F11, F22, F33 |
| correct | 11 | 10 | F35 (qwen) + 10 negatives; 10 negatives for jeb |

`derived` — total 38 each: qwen 23+0+1+3+11 = 38; jeb 23+0+5+10 = 38. The 0/20 is therefore a
**route** failure, not a judge failure: 23 of 28 have no game-data candidate to judge.

## 2. Why `reach` was misleading

`smart_search.literal_in(snippet, expect)` (line 102) only asks whether the literal appears in a
candidate snippet. The `v1` route returned the calibration file itself for P01-P20:

`decoded` — `calib_runs/51c8dd3c_v1search/P01.json`:
`reach_sources = ["E:/Modding/_BmAKgrab/chase/calib.jsonl:1", "E:/Modding/_BmAKgrab/chase/calib.jsonl:1"]`,
and `calib.jsonl:1` is the answer key:

```
{"family": "a", "id": "P01", "kind": "positive", "known": "0.8", "member": "TurnOnSpotFrontTorqueFactor",
 "offset": "0x1c8", "owner": "RVehicleSimBatmobile", ...}
```

The judge's reply on that candidate is exactly right:

> "The snippet is a JSON analysis record describing field metadata, not a code snippet showing the
> actual initialization or assignment of the value."

So `reach = 28/28` measures the answer key, not the corpus. The calibration's headline "reachable
28/28" must be retired.

## 3. Worked examples

### (a) SEARCH — 23 cases

**P07 `BattleModeTurnOnSpotTorqueFactor` = 0.333333.** No candidate source is a game file; the two
text candidates are `calib.jsonl:7`, the four exe candidates are register arithmetic. The value is
in the decoded table the route never read — `MODES.md`, exact row:

```
| `BattleModeTurnOnSpotTorqueFactor` | 0x2e0 | `float` | factor | 0.333333 | 0.333333 | 0.333333 | 0.333333 | yes |
```

**P10 `BattleModeStopAndTurnAngleStationary` = 30.** Candidates: `calib.jsonl:10` twice. Exact
`MODES.md` row:

```
| `BattleModeStopAndTurnAngleStationary` | 0x2f8 | `float` | deg | 30 | 30 | 30 | 30 | yes |
```

**P17 `ImpactRoadAssistFactor` = 90000.** Candidates: `calib.jsonl:17` twice. Exact `MODES.md` row:

```
| `ImpactRoadAssistFactor` | 0x1764 | `float` | engine gain | 90000 | 90000 | 90000 | 90000 | yes |
```

`decoded` — `MODES.md` (22,283 B) contains a row with the literal for **19 of the 20 positives**
(all but P12); `SKINS.md`/`MATERIALS.md` contain 0. This is the missing route.

### (b) WINDOW — 0 cases

Jeb's 2,048-token training limit is real: **118 of 190** verdicts carry
`"the state was cut to 2048 prompt tokens"`; **12** of 38 cases have every verdict cut, **22** have
some cut, **4** none. But no cut candidate is a game-data source with the value, so expanding the
window changes no case. Example, P09 `BattleModeDriveForceFactor` = 500: all **6/6** verdicts cut,
sources are `calib.jsonl:9` twice and four exe addresses; the value is not in any of them. The cut
is a capacity defect, not the recall cause. **0.**

### (c) JUDGE — qwen 1, jeb 5

**F16 `StrafeCooldown` = 0.75.** A game-data candidate exists, and Qwen answers:

> "The snippet shows a default value of 0.75, but the literal 1500 from the preceding entry is not
> explicitly linked to the `StrafeCooldown` field in this specific record."

The value is right there; the model imported the previous row's literal. **JUDGE.**

**Jeb F35 `ImpactShakeAbandonedVehicleFactor` = 3.0.** The one case Qwen gets. Jeb's verdict:
`p = 0.405`, `lit = ''`, `warnings` cut; it cannot read the JSON `"field": "F-35 …"` / `"value": 3.0`
form, and 0.405 is below its 0.5 threshold. **JUDGE.** Jeb's max P(true) over all 8 found cases is
0.472 (F22), below its threshold; that is a model-ranking failure, not a window one.

**Jeb F22 `StrafeFwdCorrectionForce` = 3000.0.** `p = 0.4716`, `lit = ''`, one candidate cut; the
game-data candidate is present and still below 0.5. **JUDGE.**

### (d) PROMPT — qwen 3

**F22.** Qwen on `g1_chase_native.json:372`:

> "The snippet shows a memory load from an offset table rather than a store of a literal value into
> the field."

The file is a decoded field table, not an offset table; the prompt's offset-table rule fires on the
word "offset". **PROMPT.**

**F33 `BattleModeHeight` = 250.0.** Qwen on `chase2_defaults.json:129`:

> "The snippet is a JSON analysis record listing field metadata, not a game file containing
> executable code that sets the value."

`chase2_defaults.json` **is** decoded game data — the same file whose line 151 Qwen accepts for F35.
The "JSON analysis record" rule is too broad. **PROMPT.**

**F11 `BattleModeCamFOV` = 60.0.** Qwen on `chase2_verify.json:918`:

> "The snippet is a JSON analysis record showing a default value of 60.0, but it does not contain the
> actual code or script that sets this value."

`chase2_verify` is a tool file, so this rejection is correct; it is listed to show the boundary —
the rule is right on tool output and wrong on decoded dumps. F11's game-data candidate is not the
literal source.

## 4. The changes, and what was tested

### Change 1 — route (dominant, 23 cases): **tested at retrieval, not applied**

Add the decoded markdown tables under `Research/BatmobileGrab/` to the text route, trimmed to the
single table row that names the member; exclude the search tool's own outputs (`calib.jsonl`,
`chase2_verify.json`, `namescan*.json`, `verdicts*.jsonl`, `pkg_*`, `chase2_04*`) from candidates.

Test on the stored case set, no model call (the deterministic half of the judge's input):

| metric | before | after |
|---|---:|---:|
| known value reachable in a game-data source | **1/28** | **22/28** |
| positive reachable (20) | 0/20 | **19/20** (P12 missing) |
| found rows reachable (8) | 1/8 | **3/8** (F18, F33, F35) |
| negatives with a numeric literal in their row (10) | 0/10 | **0/10** |

`decoded` — union: 19 `MODES.md` rows (P01-P11, P13-P20) + F18 (`g1_chase_native.json`) + F33/F35
(`chase2_defaults.json`) = 22. P12 `BattleModeTrailingSteerFactorMoving` = −0.25 is absent from all
routes; it stays `UNKNOWN`.

**Was the judge re-run?** Only partially: a 6-case pilot (P07, P10, P17, N01, N02, N05) was
attempted against Qwen at `127.0.0.1:8080`; the connection was refused
(`ConnectionRefusedError: [WinError 10061]`). The server had answered `/health` earlier in the same
session and stopped. **No judge-level after-recall or after-FP can be claimed.** Because the change
therefore has no measured 0-FP judge result, it is **not applied**; `smart_search.py` is untouched.

### Change 2 — prompt (qwen 3 cases): **proposed, not tested, not applied**

Narrow the JSON rule from "a JSON/analysis record written by the search tool" to "a file the search
tool itself wrote (`chase/calib*`, `chase2_verify*`, `namescan*`, `verdicts*`, `pkg_*`)"; allow a
decoded data table/JSON row that names the member and shows the literal. This targets F22/F33
without touching the tool-record rejection that is correct today.

The same server outage blocks the test. It is **not applied**; `chase_judge.py` is untouched, so no
backup was needed. If it is ever applied, the backup is
`cp Tools/scripts/chase/chase_judge.py Tools/scripts/chase/chase_judge.py.bak-20261106`.

## 5. What this means for the calibration verdict

* **Keep Qwen as the judge.** Its 0/20 was not a capability result: 23 of 28 had no game-data
  candidate, and its rejections of the answer key were correct.
* **Retire `reach` as the denominator.** Replace it with "reachable in a game-data source", which is
  1/28 before and 22/28 after the route change.
* **Do not tune the threshold on this set.** Jeb's maximum P(true) on a real game-data candidate is
  0.472 (F22) and 0.405 on F35; below 0.5 it gains negatives, and at 0.5 it finds nothing.
* **The next run must use the new route and re-score both judges.** Until then, the honest status is
  "recall cause identified, route fix retrieval-tested, judge effect unmeasured".

## 6. Checks

| # | check | result |
|---|---|---|
| 1 | 38 case records read for both judges | 38/38 each |
| 2 | class counts re-derived | qwen 23/0/1/3/11, jeb 23/0/5/0/10 |
| 3 | Jeb cut counts | 118/190 verdicts, 12 all-cut, 22 some, 4 none |
| 4 | `MODES.md` row recovery | 19/20 positives |
| 5 | route union | 22/28 known values, 0/10 negative literals |
| 6 | judge pilot | **not run**: Qwen server refused connection (WinError 10061) |
| 7 | `python Tools/scripts/chase/t_smart_diag.py --check` | re-derives 1-5 and the report numbers |

No game launch, no install, no prompt or tool edit. **Revert:** delete this file.
