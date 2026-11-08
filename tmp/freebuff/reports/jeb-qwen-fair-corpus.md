# Fair Jeb-vs-Qwen corpus — test material only

**Status: the corpus is built and frozen; no model was called in this stage.** Both judges remain untouched and no run directory was written. This report exists to freeze the cases, the split and the decision rule before any model sees a case.

## What was read

- `tmp/freebuff/reports/jeb-vs-qwen-calibration.md` — the 38-case calibration and its thresholds.
- `tmp/freebuff/reports/jeb-short-window-retest.md` — short-window retest.
- `tmp/freebuff/reports/jeb-choice-format-retest.md` — `member`/`class` choice retest, including the corpus ceiling (5 answerable cases) and the `calib.jsonl` manifest leak.
- `Tools/scripts/chase/jeb_judge.py` — both judge modes, window and literal reader.
- `Tools/scripts/chase/chase_calibrate.py` — the 38-case `calib.jsonl` builder and run folders.

The three reports agree on two facts that shape this corpus: only 5 of 28 non-negative calibration cases had a candidate that actually stored the default, and the frozen search handed the `calib.jsonl` manifest line — which contains the answer key — to the model as a candidate. Both are removed here.

## Corpus

| fact | value |
|---|---|
| cases | **84** |
| positives | **42** (requirement: ≥30) |
| negatives | **42** (requirement: ≥30) |
| candidates per case | **6** (504 total) |
| positives with exactly one `true` candidate | **42/42** |
| negatives with a `true` candidate | **0/42** |
| duplicates by (member, owner, offset) | **0** |
| corpus sha256 | `a95063972b0d4c2c54035c6d9cb32e403005e50758049cf676d99f4b065937ef` |

Because 42 positives exist, the “fewer than 30 positives” fallback does not apply; no file is needed to top the corpus up.

### Positives — ground truth

| family | cases | ground truth | example evidence path |
|---|---:|---|---|
| `modes` | 39 | decoded tune: `MODES.json`, value on `Playable_Batmobile_SF` (four packages) | `Research/BatmobileGrab/MODES.json:BattleModeDrivingForceZOffset` |
| `decoded` | 3 | decoded CDO record from `BmGame.upk` exported to `chase2_defaults.json` | `E:/Modding/_gamedata/BmAKgrab/chase/chase2_defaults.json` |

Every one of the 42 rows carries an `evidence` string and every path named in it exists on disk (checked 42/42). The build requires a `true_record` whose class/offset/property match the case; the audit also confirms each true candidate's snippet shows the case's `known` value at the case's offset (42/42). No positive relies on a regex label or a model.

### Negatives — the six distractor classes

Every negative list carries **all six** classes named in the old prompt, and every negative has no store candidate:

| class | present in negatives | meaning in the snippet |
|---|---:|---|
| `offset` | 42/42 | an offset map: names and offsets, no values |
| `count` | 42/42 | a search-tool name count: package/ini slots, no value |
| `tool` | 42/42 | a search-tool row record (FOOTAGE status), not game data |
| `register` | 42/42 | disassembly: `[reg+off]` value from register/memory, no visible constant |
| `stack` | 42/42 | disassembly: store into `[rsp+..]` / `[rbp+..]` |
| `frame` | 42/42 | disassembly: per-frame arithmetic (`addss`/`subss`/`mulss`) on the field |

Across the whole corpus the candidate classes are: `offset` 84, `count` 84, `tool` 84, `register` 73, `stack` 66, `frame` 69, `store` 42, `wrong_record` 2. Positives add one `store` and two of the three disassembly shapes (rotated), plus a same-name/wrong-field decoy where one exists; negatives do not get a store.

## Rebuilt candidate lists and exclusion

Candidates are rebuilt from decoded game data and real disassembly. The manifest and every tool-written record are excluded at the source, not filtered after the fact:

```
EXCLUDED = ("calib.jsonl", "candidates.jsonl", "verdicts.jsonl", "verdicts_v2.jsonl",
            "MODES.json", "FOOTAGE.md")
```

The builder never reads `calib.jsonl`, `candidates.jsonl`, `verdicts*`, `cache/` or `calib_runs/`, and the two ground-truth files are used only to author a case — never emitted as a candidate. Audit over all 504 candidate source/snippet/label strings: **0 occurrences** of any excluded name. The judge's output directories are not readable by the search half.

`evidence` is the only place a ground-truth filename appears, because the rule requires the evidence path in each row. That is not a leak: the evidence field is not sent to a model by the corpus reader.

## Frozen split

| split | positives | negatives | share |
|---|---:|---:|---|
| tuning | 14 | 14 | one third |
| test | 28 | 28 | two thirds |
| **total** | **42** | **42** | |

Seeds, fixed before any model call: `SPLIT_SEED_TUNE = 20261107`, `SPLIT_SEED_TEST = 20261108`, negative shuffle `NEG_SEED = 20261109`; candidate-order seeds `1107, 2711, 3313`. The split is written into each case (`split` field) and must be read from the frozen file, not recomputed at run time.

## Decision rule (written before any model call)

Verbatim from `E:/Modding/_gamedata/BmAKgrab/chase/fair/PREREGISTRATION.md` (sha256 prefix `fdcd803d8614`; the same text is `PREREG` in `fair_judge.py`):

```
## Decision rule (written before any model call)

A model is chosen as the smart-search judge only if either
  (a) its Wilson 95% lower bound on test-split macro accuracy is greater than the other model's
      point estimate on the same split and arm, or
  (b) the paired exact-binomial test (McNemar, two-sided) between the two models on the same cases
      gives p < 0.05.
Otherwise the verdict is NO DIFFERENCE, and the cheaper and faster model stays the judge.  Cost is
measured as seconds per case on the shared choice arm; a tie in cost keeps the incumbent
(`chase_judge` on Qwen3.5-4B, the default in `smart_search.py`).

Scoring definitions fixed before the run:
  * a positive case is correct only if the model picks the one candidate whose decoded record
    carries the member's value at the member's class and offset;
  * a negative case is correct only if the model answers `none`; any other answer is a false pick;
  * macro accuracy is the unweighted mean of positive accuracy and negative accuracy (the splits
    are balanced, so it equals overall accuracy);
  * per-case decisions are the majority over the 3 candidate orders (ties -> first order, flagged);
  * the paired test uses the per-case majority decision of the two models on the same cases;
  * Wilson intervals are 95% (z = 1.96);
  * a call that returns no parseable letter is a wrong answer, counted, never dropped.
```

## What was changed to make the build correct

`fair_judge.py` already encoded the corpus rules, seeds and prereg. One builder defect surfaced in the audit: the three `decoded` positives cited `Research/BatmobileGrab/<file>`, which does not exist — the decoded records live outside the repo under `E:/Modding/_gamedata/BmAKgrab/chase/`. The evidence string now emits that real path with forward slashes. No judge, prompt, threshold or run was modified.

## Checks run

- `python Tools/scripts/chase/fair_judge.py --build` → 84 cases (42 positive, 42 negative); tune 14+14, test 28+28; prereg `fdcd803d8614`.
- JSONL re-parsed, 84 lines; 6 candidates per case; 42 cases with exactly one true candidate, 42 with none.
- Every negative has `offset`, `count`, `tool`, `register`, `stack`, `frame`; missing-class count 0.
- Every positive `evidence` path exists (42/42); every true candidate shows the known value at the offset (42/42).
- Excluded-name scan over all 504 candidate strings: 0 leaks.
- Repo copy byte-identical to the rebuilt frozen corpus (`cmp`), sha256 `a9506397…`; 84 lines.
- **No model call:** no server was started or queried, and `fair/runs/` was not written.

## Files

- `Tools/scripts/chase/fair_cases.jsonl` — the frozen corpus (84 lines), requested path.
- `E:/Modding/_gamedata/BmAKgrab/chase/fair/cases.jsonl` — the builder's own copy, byte-identical.
- `E:/Modding/_gamedata/BmAKgrab/chase/fair/PREREGISTRATION.md` — the decision rule, rewritten identically.
- `Tools/scripts/chase/fair_judge.py` — one evidence-path correction in the builder.
- This report, mirrored at `tmp/freebuff/reports/jeb-qwen-fair-corpus.md`.
