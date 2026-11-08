# Jebadiah 9B choice-format retest — was 0/28 the question shape?

**Verdict up front: yes, the 0/28 was mostly the question shape and the threshold, and the trained
`choice` shape fixes it — but the corpus caps the score at 5/28, so read the new numbers as "4 of the
5 answerable cases", not as 4/28 of real recall.** Same model (`jebadiah-9b` on `:8081`), same frozen
`chase_candidates_v1` lists, same 38 cases: the old `noul` question at 0.5 gets **0/28**; the
per-member `choice` over A–F + `none` picks the candidate that stores the default in **4 of the 5
cases where such a candidate exists** (4/28 overall, 7/10 negatives correctly `none`); the
per-candidate class `choice` scores the same 4/5 (4/28). Qwen's stored run gets **1/28** (F35 only,
1 of the 5). The old 0/28 was not a broken model: the same stored `P(true)` ranks positives above
negatives at **AUC 0.665–0.743**, it just never reaches a usable threshold — the 0.5 cut was one half
of the problem and the long open `noul` framing was the other.

**Which format to use: `member` (one `choice` per case over A–F + `none`).** It is one model call
per case (10.8 s/case on 38 calls, against 11.5 s/case on the 190 `noul` calls — five times fewer
calls), it has no threshold to tune, it
abstains on 7/10 negatives, and it reaches the same 4/5 answerable cases as the 190-call class mode.
Keep `class` as a diagnostic only. Neither number can be trusted as recall until the candidate
corpus is fixed (below): **70 of Jeb's 74 "default" labels in class mode are wrong**, because the
frozen search hands the `calib.jsonl` manifest line to the model as a candidate.

## What "the format the model was trained on" is

Read from the installed package, `site-packages/jebadiah_decide/defaults.py`, `EXAMPLE` (the shipped
example-request, with its per-runtime expected values in `EXPECTED`):

```python
"urgent": {"type": "noul", "instructions": "The customer is blocked from working.",
           "criteria": {"true": "work has stopped", "false": "it can wait"}}
"route":  {"type": "choice", "instructions": "Which team should take this ticket?",
           "criteria": {"billing": "an invoice, a charge or a refund",
                        "support": "a product question", "sales": "a quote or a renewal"}}
```

`EXPECTED["9b"]` gives `urgent` = **0.171** (and 0.153 / 0.203 on 4b/27b): the *correct* answer to a
`noul` scores about **0.15–0.20**, not 0.5. A `noul` is a short statement plus two one-line
criteria; a `choice` is a short question plus one short criterion per labelled option. `client.py`
renders both through `_contract.Renderer` and takes `argmax` for `choice` (`answer_from_probs`), so a
`choice` has no threshold at all.

The two earlier runs used the other shape: a 6-line instruction paragraph naming the member, owner,
type and offset, a 7-part negative list, and "a literal default is visibly stored into the member's
field in initialisation code" as one criterion, answered as `P(true)` and cut at 0.5. `defaults.py`
itself says that shape's correct answer scores ~0.17.

## What was added to `jeb_judge.py` (noul mode untouched)

- **Backups.** `jeb_judge.py.bak-20261107` is the noul-only file (no `CLASS_KEYS`, no
  `judge_class`/`judge_member`); `jeb_judge.py.bak-20261106` is the pre-window file.
- **`class` mode, prompt `413d82b5`** — one `choice` per candidate, options exactly the seven classes
  the old prompt's negative list named, one short criterion each:

  ```python
  CLASS_INSTRUCTIONS = "What is this snippet showing for `{member}` (field offset {offset})?"
  CLASS_CRITERIA = {
      "default": "a literal stored into the member's field, in initialisation code",
      "offset":  "a number equal to the field offset, from an offset table",
      "count":   "how many files or packages contain the name",
      "runtime": "a value from a register or memory, no constant visible",
      "stack":   "a store into a stack local ([rsp+..] or [rbp+..])",
      "frame":   "the field is changed by arithmetic every frame",
      "tool":    "a record written by the search tool, not the game"}
  ```
- **`member` mode, prompt `8991a512`** — one `choice` per case over the candidates:

  ```python
  MEMBER_INSTRUCTIONS = ("Which snippet shows the default value of `{member}` "
                         "(declared on `{owner}`, type {type}, field offset {offset})?")
  criteria = {"A": "snippet A from <source>", ..., "F": "snippet F from <source>",
              "none": "no snippet stores a literal default for the member"}
  ```
- **Window inside 2,048 tokens.** `class` reuses `window()` (12 lines / 2,400 chars); `member` shows
  each candidate at 1,100 chars and shrinks to 350 if the rendered prompt goes over. Measured with
  the model's own tokenizer (`_tokens` → `renderer.render` → `_encode`): class max **1,205** tokens,
  member max **2,037**, truncated **0** in both runs.
- **Separate run folders and versions:** `jeb_class_413d82b5_v1search/`,
  `jeb_member_8991a512_v1search/`, alongside the untouched `jeb_9440028e_v1search/` (noul, window)
  and `jeb_340c7b55_v1search/` (noul, whole snippet).
- **Scoring separated from the literal.** `choice` correctness is scored on its own (`hit`,
  `reach_hit`); the regex literal (`literal`, `literal_matches`) is reported separately. Two labels
  are printed: the **store label** (`_stores_default`: the literal on a line that addresses the
  member's offset, or a text record's `value` key — the intended meaning of "default") and the old
  **literal-present label** (`literal_in(snippet, known)`, what the earlier runs called reachable).

## Numbers

| format | prompt | calls | max prompt tokens | truncated | right, store label | right, old literal-present label | regex literal matched |
|---|---|---:|---:|---:|---:|---:|---:|
| noul, threshold 0.5 (stored) | `9440028e` | 190 | whole snippet/window | 0 | **0/28** | 0/28 | — (nothing fired) |
| **member choice** | `8991a512` | **38** | 2,037 | 0 | **4/28** = 4/5 answerable, 7/10 negatives `none` | 27/28, **3/10 negatives wrong** | **2/38** |
| class choice | `413d82b5` | 190 | 1,205 | 0 | **4/28** = 4/5 answerable | 27/28, 0/10 negatives wrong | n/a (no literal) |
| qwen, stored run | `51c8dd3c` | 186 | — | — | **1/28** = 1/5 answerable | — | 1 |

- **Candidate-level class accuracy: 119/190 (62.6%).** `default` class: TP 4, FP **70**, FN 1,
  TN 115 → precision **0.054**, recall **0.800**. Jeb labels everything with a literal `default`:
  `default` 74, `runtime` 57, `stack` 36, `offset` 12, `count` 10, `frame` 1, `tool` **0**. It never
  once used `tool`, which is the class that should take the manifest line.
- **Cost:** class 4.41 s/candidate (837 s for 190 calls); member 10.78 s/case (410 s for 38 calls,
  ~2.7 s per shown candidate); noul stored 2.29 s/candidate, 190 verdicts over 38 cases → ~11.5 s/case;
  Qwen 5.63 s/candidate, 186 verdicts → ~28 s/case.
- Server: `E:/AI/agent_jebadiah-9b-q5.bat` → `127.0.0.1:8081`, `/health` ok, `/v1/models`
  `jebadiah-9b`. `:8080` was closed for the whole retest (`curl` rc=28), so the Qwen numbers are the
  stored `51c8dd3c_v1search` run.

## The corpus ceiling: only 5 cases have a candidate that stores the default

`_stores_default` over all 190 frozen candidates finds **5 true stores**, in 5 cases:

| case | kind | known | store candidate |
|---|---|---|---|
| P03 | positive | 2 | **E** (Jeb's member pick: B → miss; class: E = `runtime`) |
| F11 | found | 60.0 | **B** (member: B ✓, class: B = `default` ✓) |
| F16 | found | 0.75 | **B** (✓) |
| F33 | found | 250.0 | **B** (✓) |
| F35 | found | 3.0 | **B** (`chase2_defaults.json:151`, the case Qwen also gets) |

Every other non-negative case has **no candidate that stores its default** — the exe candidates carry
no literal for the member at all (`literal_in` is False on all of them; see P14: candidates C–F).
What made the old runs "reachable 28/28" is that the frozen search returns the **`calib.jsonl`
manifest line** itself as the first candidate, and that line contains `"known": "0.8"` / `"offset":
"0x1c8"`. So the old literal-present label is satisfied by the search tool's own record, and a model
that calls that record "default" is rewarded. That is the precision 0.054 above.

This is the part the retest cannot fix: the question shape is now right, but 23 of the 28 non-negative
cases are unanswerable with this candidate list, and the manifest leak makes the old label say 27/28.
**First fix `calib.jsonl` out of the v1 candidate lists**, then rerun both modes — only then does
"right candidate" mean "found the default".

## Per case — `member` choice (`8991a512`)

`pick` is Jeb's letter (`none` = abstain); `store right` is the strict label; `literal` is the regex
read off the picked snippet, independently of whether the pick was right.

| id | kind | known | pick | store right | literal | literal-present |
|---|---|---|---:|---:|---:|---:|
| P01 | positive | 0.8 | A | no (manifest) | 0.8 | yes |
| P02 | positive | -0.8 | B | no (manifest) | -0.8 | yes |
| P03 | positive | 2 | B | **no — store was E** | -0.8 | yes |
| P04 | positive | 600 | A | no (manifest) | -0.8 | yes |
| P05 | positive | 0.75 | A | no (manifest) | -0.8 | yes |
| P06 | positive | 1.25 | A | no (manifest) | -0.8 | yes |
| P07 | positive | 0.333333 | A | no (manifest) | -0.8 | yes |
| P08 | positive | 10 | A | no (manifest) | -0.8 | yes |
| P09 | positive | 500 | A | no (manifest) | -0.8 | yes |
| P10 | positive | 30 | A | no (manifest) | -0.8 | yes |
| P11 | positive | 1 | A | no (manifest) | -0.8 | yes |
| P12 | positive | -0.25 | A | no (manifest) | -0.8 | yes |
| P13 | positive | 20 | A | no (manifest) | 2 | yes |
| P14 | positive | 3000 | A | no (manifest) | 600 | yes |
| P15 | positive | 24000 | A | no (manifest) | 0.75 | yes |
| P16 | positive | 8000 | A | no (manifest) | 1.25 | yes |
| P17 | positive | 90000 | A | no (manifest) | 0.333333 | yes |
| P18 | positive | 30000 | A | no (manifest) | 10 | yes |
| P19 | positive | 2000 | B | no (manifest) | 500 | yes |
| P20 | positive | 0 | B | no (manifest) | 30 | yes |
| F7 | found | 0.05 | A | no (manifest) | 1 | **no** |
| F11 | found | 60.0 | B | **yes** | — | yes |
| F16 | found | 0.75 | B | **yes** | 0 | yes |
| F18 | found | 0.0 | none | no | — | no |
| F22 | found | 3000.0 | A | no (manifest) | 24000 | yes |
| F31 | found | 265.0 | A | no (manifest) | 8000 | yes |
| F33 | found | 250.0 | B | **yes** | — | yes |
| F35 | found | 3.0 | B | **yes** | — | yes |
| N01 | negative | — | B | no | — | no |
| N02 | negative | — | F | no | — | no |
| N03 | negative | — | none | **yes** | — | yes |
| N04 | negative | — | none | **yes** | — | yes |
| N05 | negative | — | none | **yes** | — | yes |
| N06 | negative | — | none | **yes** | — | yes |
| N07 | negative | — | none | **yes** | — | yes |
| N08 | negative | — | C | no | 0.0 | no |
| N09 | negative | — | none | **yes** | — | yes |
| N10 | negative | — | none | **yes** | — | yes |

Note the literal column: 2/38 matched. On the four right picks it is `—` three times (F11, F33, F35
pick a JSON record whose value is `"value": 3.0`, which `jeb_judge._NUM` cannot read) and `0` once.
Under the old coupled scoring those four correct picks would have counted **0** right; the coupled
run is exactly the bug the request names. F35 is the clean example: Jeb picks the right candidate
(`chase2_defaults.json:151`) and the regex reads nothing.

## Per case — class `choice` (`413d82b5`)

`labelled default` is how many of the case's candidates Jeb called `default`; `manifest class` is
what it called the `calib.jsonl` line; `store hit` is the strict score.

| id | kind | candidates | labelled default | manifest class | store candidate | store hit | literal-present |
|---|---|---:|---:|---|---|---:|---:|
| P01 | positive | 6 | 2 | default | - | — | yes |
| P02 | positive | 6 | 2 | default | - | — | yes |
| P03 | positive | 6 | 2 | default | E:runtime | **no** | yes |
| P04 | positive | 6 | 2 | default | - | — | yes |
| P05 | positive | 6 | 2 | default | - | — | yes |
| P06 | positive | 6 | 2 | default | - | — | yes |
| P07 | positive | 6 | 2 | default | - | — | yes |
| P08 | positive | 6 | 2 | default | - | — | yes |
| P09 | positive | 6 | 2 | default | - | — | yes |
| P10 | positive | 6 | 2 | default | - | — | yes |
| P11 | positive | 6 | 2 | default | - | — | yes |
| P12 | positive | 6 | 2 | default | - | — | yes |
| P13 | positive | 6 | 2 | default | - | — | yes |
| P14 | positive | 6 | 2 | default | - | — | yes |
| P15 | positive | 6 | 2 | default | - | — | yes |
| P16 | positive | 6 | 2 | default | - | — | yes |
| P17 | positive | 2 | 2 | default | - | — | yes |
| P18 | positive | 2 | 2 | default | - | — | yes |
| P19 | positive | 2 | 2 | default | - | — | yes |
| P20 | positive | 4 | 2 | default | - | — | yes |
| F7 | found | 6 | 1 | offset | - | — | **no** |
| F11 | found | 3 | 2 | default | B:default | **yes** | yes |
| F16 | found | 5 | 3 | default | B:default | **yes** | yes |
| F18 | found | 6 | 1 | default | - | — | yes |
| F22 | found | 4 | 3 | default | - | — | yes |
| F31 | found | 3 | 2 | default | - | — | yes |
| F33 | found | 4 | 4 | default | B:default | **yes** | yes |
| F35 | found | 4 | 4 | default | B:default | **yes** | yes |
| N01 | negative | 6 | 5 | runtime | - | — | no |
| N02 | negative | 6 | 5 | runtime | - | — | no |
| N03 | negative | 2 | 0 | runtime | - | — | no |
| N04 | negative | 1 | 0 | runtime | - | — | no |
| N05 | negative | 6 | 1 | runtime | - | — | no |
| N06 | negative | 6 | 0 | runtime | - | — | no |
| N07 | negative | 4 | 2 | runtime | - | — | no |
| N08 | negative | 6 | 1 | offset | - | — | no |
| N09 | negative | 6 | 0 | offset | - | — | no |
| N10 | negative | 6 | 0 | offset | - | — | no |

The class mode sees the manifest line and calls it `default` on 27 of the 28 non-negative cases (and
`runtime`/`offset` on the negatives, whose manifest line carries no `known`). It never says `tool`.
So the 27/28 literal-present figure is a *shape* win purchase on a label that rewards the leak; on the
strict label the class mode is 4/28 with 70 false `default` labels.

## Old `noul` runs — the rank-based view the earlier reports never gave

`python Tools/scripts/chase/jeb_judge.py --rank <dir>` — per-case best `P(true)` (no model call):

```
E:/Modding/_gamedata/BmAKgrab/chase/calib_runs/jeb_340c7b55_v1search   (whole snippet)
AUC P(true) positive-vs-negative 0.665
AUC P(true) (positive+found)-vs-negative 0.707
| threshold | positive hit | found hit | negative FP |
| 0.05 | 20/20 | 8/8 | 7/10 |
| 0.10 | 19/20 | 7/8 | 5/10 |
| 0.15 | 15/20 | 7/8 | 3/10 |
| 0.20 |  8/20 | 7/8 | 3/10 |
| 0.25 |  3/20 | 7/8 | 3/10 |
| 0.30 |  1/20 | 5/8 | 3/10 |
| 0.35 |  0/20 | 4/8 | 1/10 |
| 0.40 |  0/20 | 3/8 | 1/10 |
| 0.45 |  0/20 | 1/8 | 0/10 |
| 0.50 |  0/20 | 0/8 | 0/10 |
```

```
E:/Modding/_gamedata/BmAKgrab/chase/calib_runs/jeb_9440028e_v1search   (short window)
AUC P(true) positive-vs-negative 0.675
AUC P(true) (positive+found)-vs-negative 0.743
| threshold | positive hit | found hit | negative FP |
| 0.05 | 20/20 | 8/8 | 6/10 |
| 0.10 | 20/20 | 8/8 | 5/10 |
| 0.15 | 17/20 | 8/8 | 4/10 |
| 0.20 | 10/20 | 8/8 | 4/10 |
| 0.25 |  5/20 | 8/8 | 3/10 |
| 0.30 |  4/20 | 7/8 | 3/10 |
| 0.35 |  3/20 | 6/8 | 1/10 |
| 0.40 |  2/20 | 5/8 | 1/10 |
| 0.45 |  2/20 | 3/8 | 0/10 |
| 0.50 |  2/20 | 2/8 | 0/10 |
```

Read both tables: the model **does** rank a real case above a negative (AUC 0.67–0.74, well above
chance), which is why "the model is broken" was the wrong conclusion. But the ranking is not clean:
at the only zero-false-positive points (0.45 / 0.5) the noul format finds 0–2 of 28, and the four
verdicts the window run fires above 0.5 quote the wrong literal (`50.0` for P07's 0.333333, `100.0`
for P06's 1.25, `89.0` for F7's 0.05, `2.0` for F18's 0.0). At 0.15 you get 22/28 recalled for 3/10
negatives firing — the best the open shape does at the member shape's 3-negative level, which the
member shape beats 27/28 to 22/28. So: **the 0.5 cut was wrong, but lowering it does not rescue the
noul shape; the shape itself was the larger half of the 0/28.**

## Verdict

1. **The 0/28 was not the model.** Same weights, same server, same candidates: the trained `choice`
   shape reaches 4/5 answerable cases where `noul` at 0.5 reached 0/5, and the stored `noul` scores
   rank at AUC 0.665–0.743. A `noul` whose correct answer is ~0.17 by the package's own calibration
   cannot be read at 0.5.
2. **The threshold was a co-cause, not the cause.** Sweeping 0.05–0.5 never gives recall with clean
   negatives in the noul format; the best zero-FP point finds 0–2 of 28, and those quote wrong
   literals. `choice` sidesteps thresholds entirely (argmax).
3. **Use `member` (`8991a512`): 4/28, 4/5 answerable, 7/10 negatives abstain, 1 call and 10.8 s per
   case.** `class` (`413d82b5`) is a diagnostic — same 4/5 for 5× the calls, and its per-candidate
   labels quantify why: 74 `default` calls, 70 of them wrong, `tool` never used.
4. **Qwen is still ahead on precision but not on this count:** stored Qwen 1/28 (F35, precision
   1.000, 0/10 negatives, ~28 s/case). Jeb `member` gets F11, F16, F33, F35 — three more answerable
   cases than Qwen — while also abstaining on 7/10 negatives; its three negative misses (N01, N02,
   N08) are cases Qwen leaves alone. On five answerable cases 4 vs 1 is suggestive, not significant.
5. **Before any of this is recall, fix the corpus:** drop the `calib.jsonl` manifest from the search
   index (the `tool` class exists for it), otherwise the literal-present label stays 27/28 no matter
   what the model does, and 23 of 28 non-negative cases remain unanswerable.

## Reproduce and revert

```
E:/AI/agent_jebadiah-9b-q5.bat                      # one server: :8081, jebadiah-9b; :8080 stays closed
python Tools/scripts/chase/jeb_judge.py --versions  # noul 9440028e, class 413d82b5, member 8991a512
python Tools/scripts/chase/jeb_judge.py --calib class  --max 6 --search v1   # 38/38, resumes on disk
python Tools/scripts/chase/jeb_judge.py --calib member --max 6 --search v1   # 38/38, resumes on disk
python Tools/scripts/chase/jeb_judge.py --summary   # both modes, both labels, per-case tables
python Tools/scripts/chase/jeb_judge.py --rank E:/Modding/_gamedata/BmAKgrab/chase/calib_runs/jeb_340c7b55_v1search
python Tools/scripts/chase/jeb_judge.py --rank E:/Modding/_gamedata/BmAKgrab/chase/calib_runs/jeb_9440028e_v1search
```

`--calib` skips a case whose `<id>.json` already exists, so a restart never re-asks the model.
Revert the choice modes: `cp Tools/scripts/chase/jeb_judge.py.bak-20261107
Tools/scripts/chase/jeb_judge.py` (noul only, keeps the short window). Revert the window as well:
`cp Tools/scripts/chase/jeb_judge.py.bak-20261106 Tools/scripts/chase/jeb_judge.py`. All four run
folders stay on disk under `calib_runs/`; none overwrites another.

## Limitations

- The strict store label is a regex/heuristic (`_stores_default`), not a ground-truth dump: it needs
  the literal on the line that addresses the offset, or a `value` key beside the member name. It
  found 5 stores in 190 candidates; with the manifest in the list, that number is a floor.
- The member question names each candidate's source in its option text (`snippet A from exe
  0x140172731`), so the model can see `calib.jsonl` vs `exe`. That is a leak the trained shape does
  not need; it is kept because the source is what makes A–F traceable in the report.
- `n = 5` answerable cases. The 4/5 vs 1/5 comparison with Qwen is directionally consistent with the
  AUC view but far too small for a significance claim.
- The class-mode literal-present figure (27/28) is not a capability result; it is the manifest leak
  measured.
