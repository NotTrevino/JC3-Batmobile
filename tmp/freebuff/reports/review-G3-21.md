# review-G3-21 — the card census of `RESET_STATUS.md`, tested against the files

VERDICT: **needs rework**

`Research/RESET_STATUS.md` makes **24** statements of the form "card X has no report" (19 census rows, 5 prose sentences, 0 UNKNOWN-list lines). Tested against `tmp/freebuff/reports/` and against each card's tracker row in `GRAB_BACKLOG.md` §6b: **14 false**, **6 true**, **12 true-but-misleading**.

And the document's own gate no longer passes: `reset_status.py --check` exits **1** (FAIL;   - Research/RESET_STATUS.md is stale), so G3-21's line "`--check` is green (exit 0)" is no longer true of the file on disk.

| # | where | the statement | verdict |
|---|---|---|---|
| S1 | line 56, census row | / `G3-01` (supporting) / _no report_ / BmAK drivable collision (class defaults) / | **true-but-misleading** |
| S2 | line 80, prose | * `G3-01` and `G3-01b` themselves have no report file — their facts live in `COLLISION.md` / `COLLISION_GEOM.md` and were carried forward by the `G3-01b-*`, `G3-01c`, `G3-01e` repo | **false in part** |
| S3 | line 94, census row | / `G3-02` / _no report_ / BmAK controls and input / | **true-but-misleading** |
| S4 | line 95, census row | / `G3-02b` / _no report_ / BmAK driving-state input code (the meaning of LT/B/LB/A) / | **true-but-misleading** |
| S5 | line 96, census row | / `G3-02c` / _no report_ / BmAK native input path (BatmanAK.exe) / | **true-but-misleading** |
| S6 | line 99, census row | / `G3-02d` (supporting) / _no report_ / BmAK runtime observation of the controls (read-only) / | **true** |
| S7 | line 120, prose | * `G3-02`, `G3-02b`, `G3-02c`, `G3-02d`, `G3-02f` have no report files, so the config→script→native chain is evidenced only by its outputs (`CONFIG.md`, `CONTROLS.md`, `CONTROLS_CO | **false in part** |
| S8 | line 137, census row | / `G3-07` / _no report_ / JC3 runtime oracle (read-only) / | **true** |
| S9 | line 155, prose | * `G3-07` and `G3-07a` have no reports, and `Research/JC3Grab/RUNTIME_LAYOUT.md` does not exist — the sampler's layout has no oracle-backed document. | **false in part** |
| S10 | line 215, census row | / `G3-20` (supporting) / _no report_ / Ledger rows sourced from G3 results (synthesis) / | **false** |
| S11 | line 231, prose | * `G3-20` (which G3 file supplies/corrects/refutes each row, open rows named) has no report and no `Working/Translation/LEDGER_G3.md`; the per-row G3 sourcing is not yet written. | **false** |
| S12 | line 250, census row | / `G3-19` (supporting) / _no report_ / JC3 partial .rbm / .epe to FULL / | **false** |
| S13 | line 272, prose | * `G3-19` (partial `.rbm`/`.epe` to FULL) has no report, so the donor is classified but not fully decoded. | **false** |
| S14 | line 284, census row | / `G3-01` / M / DIM-4, WLD-4, R-1 / — / _no report_ / — / | **true-but-misleading** |
| S15 | line 287, census row | / `G3-02` / M / D-11, MOD-1/2, WPN, R-2 / — / _no report_ / — / | **true-but-misleading** |
| S16 | line 288, census row | / `G3-02b` / M / D-11, MOD-1/2, WPN-3/4, R-2 / — / _no report_ / — / | **true-but-misleading** |
| S17 | line 289, census row | / `G3-02c` / M / D-11, MOD-1/2, R-2 / — / _no report_ / — / | **true-but-misleading** |
| S18 | line 290, census row | / `G3-02d` / M / D-11, MOD-1/2, R-2 / — / _no report_ / — / | **true** |
| S19 | line 296, census row | / `G3-07` / L / every Q check, R-3 / — / _no report_ / — / | **true** |
| S20 | line 310, census row | / `G3-10c` / M / DIM-4 / — / _no report_ / — / | **false** |
| S21 | line 311, census row | / `G3-14` / S / AUD, T-AU3/5 / — / _no report_ / — / | **false** |
| S22 | line 312, census row | / `G3-19` / M / R-6 / — / _no report_ / — / | **false** |
| S23 | line 313, census row | / `G3-20` / M / R-5, T / — / _no report_ / — / | **false** |
| S24 | line 314, census row | / `G3-21` / S / all / — / _no report_ / — / | **false** |

## Card by card

| card | verdict | why | report file(s) found | tracker row STATUS |
|---|---|---|---|---|
| `G3-01` | **true-but-misleading** | no report, but the tracker row declares `done (geometry open -> G3-01b)` and its Out files exist (COLLISION.md) | - | done (geometry open -> G3-01b) |
| `G3-01b` | **false** | report file(s) on disk: G3-01b-boxes.md, G3-01b-cyl.md, G3-01b-mode.md | G3-01b-boxes.md, G3-01b-cyl.md, G3-01b-mode.md | partial |
| `G3-01c` | **false** | report file(s) on disk: G3-01c.md | G3-01c.md | done |
| `G3-01e` | **false** | report file(s) on disk: G3-01e.md | G3-01e.md | done |
| `G3-02` | **true-but-misleading** | no report, but the tracker row declares `done (12 UNKNOWN open)` and its Out files exist (CONTROLS.md) | - | done (12 UNKNOWN open) |
| `G3-02b` | **true-but-misleading** | no report, but the tracker row declares `done (5/5 UNKNOWN; next: native)` and its Out files exist (CONTROLS_CONSUMERS.md) | - | done (5/5 UNKNOWN; next: native) |
| `G3-02c` | **true-but-misleading** | no report, but the tracker row declares `done (5/5 UNKNOWN; switch located)` and its Out files exist (CONTROLS_NATIVE.md) | - | done (5/5 UNKNOWN; switch located) |
| `G3-02d` | **true** | no report file and no completed Out file in the tracker row | - | done (X/Y not sampled) |
| `G3-02f` | **false** | report file(s) on disk: G3-02f.md | G3-02f.md | done |
| `G3-07` | **true** | no report file and no completed Out file in the tracker row | - | open |
| `G3-07a` | **false** | report file(s) on disk: G3-07a.md | G3-07a.md | done |
| `G3-20` | **false** | report file(s) on disk: G3-20.md | G3-20.md | partial (keyword pass) |
| `G3-19` | **false** | report file(s) on disk: G3-19.md | G3-19.md | done |
| `G3-10c` | **false** | report file(s) on disk: G3-10c.md | G3-10c.md | partial |
| `G3-14` | **false** | report file(s) on disk: G3-14.md | G3-14.md | done |
| `G3-21` | **false** | report file(s) on disk: G3-21.md | G3-21.md | done (snapshot) |

A card is **false** here only when a report for it exists. It is **true-but-misleading** when no report exists but the tracker row already declares a non-open STATUS and its Out files are on disk - then "no report" understates the card: its status is declared in the backlog, not inferred from filings, and the document's own line "their STATUS is inferred" is what is wrong.

## The two existence side-claims

| claim in the text | tested | verdict |
|---|---|---|
| Research/JC3Grab/RUNTIME_LAYOUT.md does not exist | `Research/JC3Grab/RUNTIME_LAYOUT.md` exists | **false** |
| Working/Translation/LEDGER_G3.md does not exist | `Working/Translation/LEDGER_G3.md` exists | **false** |

## "Reports that have no card of their own"

| report | has a `GRAB_BACKLOG.md` §6b row | verdict |
|---|---|---|
| `G3-01b-boxes` | no | **true** |
| `G3-01b-cyl` | no | **true** |
| `G3-01b-mode` | no | **true** |
| `G3-01e` | yes | **false** |
| `G3-01e-fix` | yes | **false** |
| `G3-04c` | yes | **false** |

## The census arithmetic


The verdicts line says **0 RESOLVED / 6 PARTIAL / 0 OPEN of 6**, and the item rows re-read as R-1 PARTIAL, R-2 PARTIAL, R-3 PARTIAL, R-4 PARTIAL, R-5 PARTIAL, R-6 PARTIAL. Those six verdicts are not what this review re-tests; they are quoted so a reader can see the part of G3-21 that still stands.

## The 20 evidence probes

`reset_status.py`'s own probe list was re-executed by importing the module and calling its `build()`; `--check` was also run as a subprocess.

- probes declared and run: **20**; held: **20**; failed: **0**.
- probe rows printed in `RESET_STATUS.md`: **20** (all marked `PASS -`).
- `reset_status.py --check`: exit **1**.

All 20 probes still hold on disk.

Why `--check` is red: the generator re-parses `GRAB_BACKLOG.md` and the report folder and renders the census from them, so once `G3-10c.md`, `G3-14.md`, `G3-19.md`, `G3-20.md`, `G3-21.md` (and the already-present `G3-02f.md`/`G3-07a.md`) existed, the stored text no longer matched a fresh build. The file was not edited by this review.

## What this review could not check

- **The R-1..R-6 verdicts themselves** (0 RESOLVED / 6 PARTIAL / 0 OPEN). Testing those means re-adjudicating every core card's report, which is the cards' own `--check` and the `review-G3-*` files' job. This review tested only the census claims about which files exist.
- **Whether a *missing* report is a defect.** No rule in this repository says every card must file one; the backlog rows for `G3-01`, `G3-02`, `G3-02b`, `G3-02c`, `G3-02d` declare `done` and point at `Research/` outputs plus a green `--check`, so the absence of a report is a filing gap, not a missing result.
- **Reports written after the document.** Six of the false statements are false only because a report appeared later (`G3-10c`, `G3-14`, `G3-19`, `G3-20`, `G3-21` and the pre-existing `G3-02f`/`G3-07a`). Whether they were absent when G3-21 ran cannot be recovered from the files; `G3-02f.md` and `G3-07a.md` are the two the document's *own census* already lists as `done` with a report, so those two are internal contradictions rather than drift.

## Commands run

```
$ uv run python Tools/scripts/reset_status.py --check; echo "CHECK_EXIT=$?"
FAIL
  - Research/RESET_STATUS.md is stale
CHECK_EXIT=1
```

```
$ uv run python Tools/scripts/review_g321.py --write
verdict needs rework | statements 24 | false 14 | true 6 | true-but-misleading 12
probes 20/20 | check exit 1 | reports on disk 58
```

## Files written

- `Tools/scripts/review_g321.py` — `--write` / `--check`.
- `tmp/freebuff/reports/review-G3-21.md` (this file) and `review-G3-21.json`.
- `RESET_STATUS.md`, `GRAB_BACKLOG.md`, `G3-21.md` and every Research/ file were read only.

## Oracles

| oracle | ok |
|---|---|
| `every_statement_was_tested` | PASS |
| `statement_count_matches_the_md` | PASS |
| `twenty_probes_all_hold` | PASS |
| `check_exit_reported` | PASS |
| `side_claims_tested` | PASS |
| `reports_without_a_card_tested` | PASS |
| `no_card_list_has_entries` | PASS |

7/7 pass.
