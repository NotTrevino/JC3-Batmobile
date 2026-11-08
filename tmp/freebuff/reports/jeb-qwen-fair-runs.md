# Jeb vs Qwen fair runs — raw answer capture

Stage 2 of 3 (corpus -> **runs** -> scoring). This file records what ran. No accuracy,
no per-model score and no verdict is computed or implied here; scoring is the next stage.

Date: 2026-11-08. Project: `E:/Modding/JC3-Batmobile` (JC3 Batmobile mod tree).

## Corpus

`Tools/scripts/chase/fair_cases.jsonl`, 84 frozen cases, unchanged by this run:

| split | positive | negative | cases |
|---|---|---|---|
| tune | 14 | 14 | 28 |
| test | 28 | 28 | 56 |

Tuning was done on the tuning third only. The test two-thirds were run once, after the
shared prompt variant was frozen.

## Task and arms

Both models answer the same question: which of candidates A-F stores the default for the
case member (declared on the owner class, that type, that field offset), or `none`.

* Jeb: `jebadiah_decide` `choice` (one forward pass, probabilities per option),
  `jeb_judge.make()` against `http://127.0.0.1:8081`.
* Qwen: `chase_judge` request settings (temperature 0, `enable_thinking` false) with the
  one-letter constrained answer, `logprobs`/`top_logprobs` on, against :8080.
* Shared wording: `fair_judge.choice_question`/`choice_state`, `PER_CAND_CHARS = 900`.

## Frozen prompt variant

Chosen on the tuning split before any test cell ran: **explicit**.

Tuning-split macro per variant and model (this is the tuning decision only; it is not the
test result and must not be read as one):

| variant | model | pos acc | neg acc | macro | cells |
|---|---|---|---|---|---|
| neutral | jeb | 1.000 | 1.000 | 1.000 | 28 |
| neutral | qwen | 0.929 | 0.643 | 0.786 | 28 |
| explicit | jeb | 1.000 | 1.000 | 1.000 | 28 |
| explicit | qwen | 0.929 | 0.786 | 0.857 | 28 |

Rule (as implemented in `run_fair_judges.tune_choice`): one shared variant for both models,
max sum of the two tuning macros, tie -> neutral. Sums:
`{"explicit": 1.8571428571428572, "neutral": 1.7857142857142858}`.

## Orders

Each test case was run in three shuffled candidate orders from fixed seeds:
`fair_judge.ORDER_SEEDS = (1107, 2711, 3313)`, mixed with the case id as
`Random(seed * 1000 + numeric part of case id)`. Tuning used order 0 only.

## Servers and flags

One model at a time (GTX 1070, 8192 MiB; the two models do not co-reside).

* Jeb :8081 — `E:/AI/llama/llama-server.exe -m E:/AI/models/jebadiah-9b-v2-1-Q5_K_M.gguf
  -t 4 -np 1 -c 4096 --host 127.0.0.1 --port 8081 --alias jebadiah-9b`. Started and stopped
  by this run, as asked.
* Qwen :8080 — `-m E:/AI/models/Qwen3.5-4B-Q6_K.gguf -t 4 -np 1 -c 32768 --host 127.0.0.1
  --port 8080 --jinja --alias qwen3.5-4b`. Left running.

Both flag sets are the ones `tmp/freebuff/srv.sh` reads from `E:/AI/agent_jebadiah-9b-q5.bat`
and `E:/AI/agent_qwen3.5-4b-q6-32k.bat`. `tmp/freebuff/screen-jeb-run.txt` holds only the
output of an earlier 38-case screen, with no command line in it, so it could not supply the
flags; see COMPROMISES.

## Commands

Exact lines, also appended to `tmp/freebuff/smartsearch/fair_runs/commands.log`:

```bash
# (above, if present: an earlier aborted attempt, not part of this run)
# fair judge run (stage: raw answers only), 2026-11-08
cd E:/Modding/JC3-Batmobile
bash tmp/freebuff/srv.sh jeb   # E:/AI/llama/llama-server.exe -m E:/AI/models/jebadiah-9b-v2-1-Q5_K_M.gguf -t 4 -np 1 -c 4096 --host 127.0.0.1 --port 8081 --alias jebadiah-9b
uv run --with jebadiah-decide python tmp/freebuff/smartsearch/run_fair_judges.py tune-jeb --orders 0
bash tmp/freebuff/srv.sh stop-jeb
bash tmp/freebuff/srv.sh qwen   # -m E:/AI/models/Qwen3.5-4B-Q6_K.gguf -t 4 -np 1 -c 32768 --host 127.0.0.1 --port 8080 --jinja --alias qwen3.5-4b
uv run --with jebadiah-decide python tmp/freebuff/smartsearch/run_fair_judges.py tune-qwen --orders 0
uv run --with jebadiah-decide python tmp/freebuff/smartsearch/run_fair_judges.py freeze
uv run --with jebadiah-decide python tmp/freebuff/smartsearch/run_fair_judges.py test-qwen
bash tmp/freebuff/srv.sh stop-qwen
bash tmp/freebuff/srv.sh jeb
uv run --with jebadiah-decide python tmp/freebuff/smartsearch/run_fair_judges.py test-jeb
bash tmp/freebuff/srv.sh stop-jeb
bash tmp/freebuff/srv.sh qwen   # left running
```

## Outputs

Under `tmp/freebuff/smartsearch/fair_runs/`:

```
tune/<variant>/<model>/<case>_o0.json        tuning cells
test/<variant>/<model>/<case>_o<0|1|2>.json  test cells (variant = frozen)
variant_choice.json                          tuning macros and the frozen variant
run.log, commands.log, pipeline.log, tune_jeb.log
```

One JSON per cell, no aggregation. Fields: `model`, `arm`, `variant`, `case`, `kind`,
`split`, `order`, `letters`, `true_letter`, `pick`, `pick_source`, `true_source`,
`probabilities`, `raw`, `seconds`, `prompt_tokens`, `warnings`, `server`.
The `pick`/`pick_source`/`true_letter` fields are the raw answer and the frozen case labels,
written so scoring needs no model call again; no score was computed in this stage.

## Cell counts

| split | variant | model | cells |
|---|---|---|---|
| test | explicit | jeb | 168 |
| test | explicit | qwen | 168 |
| tune | explicit | jeb | 28 |
| tune | explicit | qwen | 28 |
| tune | neutral | jeb | 28 |
| tune | neutral | qwen | 28 |
| **total** | | | **448** |

Expected: 28 tune cases x 2 variants = 56 per model; 56 test cases x 3 orders = 168 per
model. Both models: 112 tuning + 336 test = 448 cells. All present.

## Cost measured

| model | cells | mean s/cell | max s/cell | max prompt tokens | warnings |
|---|---|---|---|---|---|
| jeb | 224 | 3.01 | 3.93 | 1467 | 0 |
| qwen | 224 | 1.92 | 4.80 | 1499 | 0 |

Prompt tokens are the frozen design's own count (limit 2,040); the largest cell is under it,
so no prompt was truncated mid-candidate.

Shape check - one test cell verbatim (`test/explicit/jeb/N57_o0.json`):

```json
{
 "arm": "choice",
 "case": "N57",
 "kind": "negative",
 "letters": [
  "A",
  "B",
  "C",
  "D",
  "E",
  "F"
 ],
 "model": "jeb",
 "order": 0,
 "pick": "none",
 "pick_source": "none",
 "probabilities": {
  "A": 0.018994,
  "B": 0.01635,
  "C": 0.011107,
  "D": 0.016286,
  "E": 0.052713,
  "F": 0.027109,
  "none": 0.857441
 },
 "prompt_tokens": 1358,
 "raw": "none",
 "seconds": 3.22,
 "server": "http://127.0.0.1:8081",
 "split": "test",
 "true_letter": null,
 "true_source": null,
 "variant": "explicit",
 "warnings": []
}
```

## COMPROMISES

1. Jeb flags come from `E:/AI/agent_jebadiah-9b-q5.bat` via `tmp/freebuff/srv.sh`, not from
   `tmp/freebuff/screen-jeb-run.txt`, which contains only screen output (no command line).
   The model path and thread/slot/context/port values match that file's stated setup.
2. Tuning used one candidate order per case and variant (order 0). The three-order repeat was
   applied to the test split, which is where the brief asks for it.
3. The two models cannot be resident together in 8 GB, so tuning and test legs ran
   sequentially, Qwen test then Jeb test, at the same frozen variant.
4. The variant was chosen jointly for both models (one shared wording), so neither model has
   a wording tuned to itself.
5. No ground-truth value was re-derived or checked here; `true_letter`/`true_source` are
   copied from the frozen case file as-is.
6. Nothing was installed beyond the `uv --with jebadiah-decide` environment, no game was
   launched, writes stayed under `tmp/freebuff/smartsearch/` and `tmp/freebuff/reports/`,
   and nothing was committed.

## Next stage

Scoring is deliberately not done here. The cells carry what it needs: the letter picked per
order, the probability map, the seconds, and the frozen true letter/source.
