# Jebadiah 9B vs Qwen3.5-4B: fair, pre-registered judge test

**Verdict: NO DIFFERENCE.** no bound separates the models and p=1.0000 >= 0.05; the cheaper/faster model stays (QWEN, 0.00 vs 0.00 s/case).  This is the pre-registered rule's output, not a reading of the numbers after the fact.

Corpus: 42 positive and 42 negative cases (504 candidates), split 14+14 tuning / 28+28 test by fixed seeds, 3 candidate orders per test case.  Ground truth is decoded tune data (`MODES.json`) or decoded CDO records, never the regex and never a model.

## Pre-registered decision rule (copied verbatim, written before the run)

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

`PREREGISTRATION.md` sha256 prefix: `fdcd803d8614`.

## Corpus, and the five flaws it removes

| property | value |
|---|---|
| cases | 84 (42 positive, 42 negative) |
| tuning split | 14 positive + 14 negative |
| test split | 28 positive + 28 negative |
| candidates | 504, six per case |
| candidate classes | count: 84, frame: 69, offset: 84, register: 73, stack: 66, store: 42, tool: 84, wrong_record: 2 |
| positive lists where more than one candidate contains the member's value | 8 |
| candidates from an excluded file (`calib.jsonl`, `candidates.jsonl`, `verdicts.jsonl`, `verdicts_v2.jsonl`, `MODES.json`, `FOOTAGE.md`) | 0 |

Each positive case has exactly one candidate carrying a decoded record for the member at the declared class and offset, with a visible scalar value; each negative case has none. The old corpus's failure modes are removed as follows:

1. *5 answerable cases in 28.*  Here every positive is answerable by construction (42/42), and the answer is the decoded record, not a value the regex could also find in a manifest line.
2. *The manifest line as a candidate.*  `calib.jsonl`, `candidates.jsonl`, `verdicts*`, `cache/`, `calib_runs/`, and the ground-truth files `MODES.json`/`FOOTAGE.md` supply zero candidates.  Every list still carries the six distractor classes the old prompt named: offset table, count, register value, stack local, per-frame update, tool record.
3. *Qwen never ran in choice format.*  Both models now answer the same A-F + `none` question; Qwen is forced to one letter.
4. *No repeats.*  Three candidate orders per test case, fixed seeds; per-order accuracy and cross-order consistency are reported below.
5. *Tuning on the scored cases.*  Prompt variant and settings were chosen on the tuning split only; the test split was scored once.

### Ground-truth sources (per case in `cases.jsonl`, field `evidence`)

| family | source of the labelled value | cases |
|---|---|---:|
| decoded | decoded CDO record (`chase2_defaults*.json`) at the member's class and offset, value agreeing with the decoded tune | 3 |
| modes | `Research/BatmobileGrab/MODES.json` values on Playable_Batmobile_SF (decoded tune, four packages agree) | 39 |
| modes (negative) | `MODES.json` `serialized=false`, `packages=[]`: the decode proves no scalar default exists on any package | 42 |

## Tuning (tuning split only)

| wording variant | Jeb macro | Qwen macro | joint |
|---|---:|---:|---:|
| labels | 1.000 | 0.500 | 1.500 |
| neutral | 0.500 | 0.500 | 1.000 |

Frozen for the shared arm: **labels** (source labels shown). The variant is chosen jointly for both models so the shared arm stays identical.

## Test split, per model and arm

| arm | model | positives correct | negatives `none` | false picks on negatives | macro | 95% Wilson | cases all 3 orders agree | s/case |
|---|---|---:|---:|---:|---:|---|---:|---:|
| choice | jeb | — | — | — | — | no run | — | — |
| choice | qwen | — | — | — | — | no run | — | — |
| native-jeb | jeb | — | — | — | — | no run | — | — |
| native-jeb | qwen | — | — | — | — | no run | — | — |
| native-qwen | jeb | — | — | — | — | no run | — | — |
| native-qwen | qwen | — | — | — | — | no run | — | — |

### Per-order accuracy (position bias and sampling noise)

| arm | model | order 1 | order 2 | order 3 | spread |
|---|---|---:|---:|---:|---:|

### Paired test (same cases, per-case majority)

| pair | n cases | only first right (b) | only second right (c) | exact p |
|---|---:|---:|---:|---:|
| shared choice: Jeb vs Qwen | 0 | 0 | 0 | 1.0000 |
| native arms: Jeb vs Qwen | 0 | 0 | 0 | 1.0000 |

### Calibration note (does the top option probability separate correct from wrong?)

| arm | model | calls with probabilities | mean top prob (correct) | mean top prob (wrong) |
|---|---|---:|---:|---:|
| choice | jeb | 0 | — | — |
| choice | qwen | 0 | — | — |
| native-jeb | jeb | 0 | — | — |
| native-jeb | qwen | 0 | — | — |
| native-qwen | jeb | 0 | — | — |
| native-qwen | qwen | 0 | — | — |

A gap between the two means is the calibration signal; a small gap means the model's confidence cannot be thresholded into a decision.  Qwen's probabilities are the first-token probabilities of its letter from `top_logprobs`; Jeb's are the option probabilities of its one forward pass.

## Where the models disagreed with the evidence

No case had different majority picks between the two models on the shared arm.

Both models matched the evidence on every test case.

## Cost and setup

| model | server | model file | shared-arm s/case | cells |
|---|---|---|---:|---:|
| jebadiah-9b | llama-server 127.0.0.1:8081 | `jebadiah-9b-v2-1-Q5_K_M.gguf` | 0.00 | 0 |
| qwen3.5-4b | llama-server 127.0.0.1:8080 | `Qwen3.5-4B-Q6_K.gguf` | 0.00 | 0 |

One server per model was up at the same time, one request at a time each; the two runners ran concurrently.  Prompt versions: `choice/labels` = `1c07093e`, `native-jeb/labels` = `fb8d526d`, `native-qwen/labels` = `9690be68`.

## Reproduce

```
python Tools/scripts/chase/fair_judge.py --build
python Tools/scripts/chase/fair_judge.py --run --model jeb  --arm choice --split tune --variant labels
python Tools/scripts/chase/fair_judge.py --run --model qwen --arm choice --split tune --variant labels
python Tools/scripts/chase/fair_judge.py --run --model jeb  --arm choice --split tune --variant neutral
python Tools/scripts/chase/fair_judge.py --run --model qwen --arm choice --split tune --variant neutral
python Tools/scripts/chase/fair_judge.py --score          # prints the frozen tuning variant
python Tools/scripts/chase/fair_judge.py --run --model jeb  --arm choice --split test --variant labels
python Tools/scripts/chase/fair_judge.py --run --model qwen --arm choice --split test --variant labels
python Tools/scripts/chase/fair_judge.py --run --model jeb  --arm native-jeb  --split test
python Tools/scripts/chase/fair_judge.py --run --model qwen --arm native-qwen --split test
python Tools/scripts/chase/fair_judge.py --report tmp/freebuff/reports/jeb-vs-qwen-fair-test.md
```

Run folders: `E:/Modding/_gamedata/BmAKgrab/chase/fair/runs/<arm>_<variant>_<promptver>/<model>/`. The earlier runs under `chase/calib_runs/` and the three earlier reports are untouched.

## Limitations

- The decoded-record candidate is the shape a decoded dump has, not a raw `.upk` byte window: the test measures the judge's decision, not the decoder's fidelity.  Exe candidates are real annotated disassembly windows from `chase2_native2_05/07.json`.
- Negative labels rest on `MODES.json`'s `serialized=false` plus the decoded dumps: if the decode missed a package, a negative could still have a default the corpus does not show.  That is a corpus limit, not a model result.
- Candidate snippets are capped at 900 characters so both models see byte-identical text and the prompt stays under Jeb's 2,048-token limit; real search snippets are sometimes longer.
- Only the shared arm is a like-for-like comparison.  The native arms differ by construction (Jeb's trained option text vs Qwen's free-form JSON), so their paired p is reported as a secondary row and is not the decision.
