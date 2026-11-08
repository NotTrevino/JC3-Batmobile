# 8863's deadlock: a reworded producer, and 8906's gate repointed

STATUS: done — the producer exists again in fresh wording, the overlap is measured, and 8906 no longer
waits on a report that nothing produces. Nothing was moved into or out of `tmp/freebuff/low/`.

## What the deadlock was

| fact | evidence |
|---|---|
| `8863-jeb-qwen-fair-test.txt` sits in `tmp/freebuff/low/too-similar/` because the similarity guard moved it there | `ls tmp/freebuff/low/too-similar` → `8863-jeb-qwen-fair-test.txt`, `8734-tyre-grip-surface-plan.txt`, `8214-apply-keep-audit-fixes-handling.txt.orig` |
| its producer is therefore gone: nothing in the queue declares `DONE: …/reports/jeb-qwen-fair-test.md` | producer map (below) → that path has **0** producers |
| `8906-smart-search-route-after-jeb.txt` waited on exactly that report | its `AFTER:` line before this task |
| so 8906 could never start, although its own inputs are fine | `reports/smart-search-recall-diagnosis.md` is cited in the body; `reports/jeb-qwen-fair-runs.md` and `reports/jeb-qwen-fair-corpus.md` exist |
| the *original* brief (8761) had been split into 8861/8863, and 8863 is the scoring stage whose inputs are already on disk | `low/archived-has-report/8761-jeb-vs-qwen-fair-test.txt.split-into-8861-8863`; `smartsearch/fair_runs/` holds `run.log`, `tune/`, `test/` |

So the queue had a hole in the middle of a three-stage chain: the corpus and the runs exist, the scoring
brief does not.

## What was written

| file | change |
|---|---|
| `Working/Queue/rewrites/8863-rewrite.txt` | **new**. The same goal and the same done-check as 8863, every sentence re-worded, and its own report path `reports/jeb-qwen-fair-score-verdict.md` so the rewritten stage is identifiable and cannot collide with the parked original |
| `tmp/freebuff/queue/8906-smart-search-route-after-jeb.txt` | **two lines edited**: `AFTER:` now names the rewrite's report, and the body sentence that read "keep Qwen as the judge unless reports/jeb-qwen-fair-test.md says otherwise" now names the same new path (the body line was the same dead reference as the gate, one line below it) |
| `Tools/scripts/trigram_overlap.py` | **new**. `--write` / `--check`; `--check` recomputes the whole comparison and fails if the stored record disagrees |
| `Working/Queue/rewrites/8863-rewrite-overlap.json` | generated record of the measurement |

Nothing in `low/` was touched, the original 8863 file stays where the guard put it, and the rewrite is a
**new** artifact rather than an edit of a parked one (project rule: never edit another task's files).

## The overlap, and the number

Definition (stated so the figure means one thing):
`token = [a-z0-9']+ after lowercasing`, `trigram = three consecutive tokens`,
`overlap = |A ∩ B| / min(|A|, |B|)` (containment), with `jaccard = |A ∩ B| / |A ∪ B|` reported as the
stricter second view. Pass = both maxima under 0.30.

```
$ uv run python Tools/scripts/trigram_overlap.py --rewrite Working/Queue/rewrites/8863-rewrite.txt --queue tmp/freebuff/queue --max 0.30 --write
rewrite            Working/Queue/rewrites/8863-rewrite.txt  (305 trigrams)
compared against   527 files in tmp/freebuff/queue   (526 on the final re-run; the queue is live)
  0.099 contain / 0.036 jaccard /   16 shared   8906-smart-search-route-after-jeb.txt
  0.082 contain / 0.026 jaccard /   11 shared   7963-booster-nozzle-mesh.txt
  0.081 contain / 0.027 jaccard /   12 shared   7961-sam-hack-jc3-carrier.txt
  0.080 contain / 0.029 jaccard /   13 shared   9576-cam-ref-and-doc-verify.txt
  0.079 contain / 0.027 jaccard /   12 shared   8607-l0-probe-triage.txt
  0.077 contain / 0.028 jaccard /   13 shared   9575-cam-chasing-remote-plan.txt
  0.077 contain / 0.027 jaccard /   12 shared   9501-audio-fix-retest.txt
  0.077 contain / 0.027 jaccard /   12 shared   9574-cam-battle-yaw-coupling-spec.txt
max containment    0.0994  (8906-smart-search-route-after-jeb.txt)
max jaccard        0.0356  (8906-smart-search-route-after-jeb.txt)
threshold          0.30
verdict            PASS
record written     Working\Queue\rewrites\8863-rewrite-overlap.json
```

```
$ uv run python Tools/scripts/trigram_overlap.py --rewrite Working/Queue/rewrites/8863-rewrite.txt --queue tmp/freebuff/queue --max 0.30 --check
… same table …
verdict            PASS
record match       yes
```

`--check` compares the rewrite length and the two maxima, not the file count — the queue gained/lost a brief
between the first write and the last check (527 → 526), which moved nothing but that count. That is why the
check's key list was narrowed in `Tools/scripts/trigram_overlap.py`.

**Maximum pairwise word-trigram overlap against `queue/*.txt` = 0.0994** (containment, vs
`8906-smart-search-route-after-jeb.txt`), **0.0356** by Jaccard — both well under the 0.30 ceiling. The
shared 16 trigrams are the queue's own header furniture (`DONE: E:/Modding/…/tmp/freebuff/reports/…`),
which every brief carries; the task text itself shares nothing.

## The producer check, before and after

Producer map = every `DONE:` path declared by `queue/*.txt`, `queue/held/*.txt` and
`Working/Queue/rewrites/*.txt`. An `AFTER` target is satisfied when the artifact exists **or** a declared
producer exists.

```
$ python - <<'EOF'   (inline, reproduced in §Commands)
briefs scanned                  528
declared producers (DONE paths) 528
AFTER targets with no artifact and no producer: 7
  9325-lock-duration-and-sort-key.txt -> …/reports/lock-markers-spec.md
  9548-hud-ledger-rows-apply.txt -> …/reports/lock-markers-spec.md
  9553-hud-cannon-circle-tracker-spec.txt -> …/reports/lock-markers-spec.md
  9554-hud-radar-driver-route-decision.txt -> …/reports/radar-icon-set-extract.md
  9558-hud-radar-icon-assets-build.txt -> …/reports/radar-icon-set-extract.md
  9559-hud-lock-markers-build.txt -> …/reports/lock-markers-spec.md
  9640-other-name-sites-hud-map-notifications.txt -> …/reports/radar-icon-set-extract.md

8906 AFTER line      : E:/Modding/JC3-Batmobile/tmp/freebuff/reports/jeb-qwen-fair-score-verdict.md
producer of that path: ['8863-rewrite.txt']
old path producer now: None
```

- **8906 is no longer in the list**: its gate now resolves to the rewrite, which declares that `DONE`.
- The old path `reports/jeb-qwen-fair-test.md` has **no** producer, which is exactly why it had to be
  dropped from the gate rather than kept.
- **7 other `AFTER` orphans remain** (two missing reports, `lock-markers-spec.md` with 4 dependants and
  `radar-icon-set-extract.md` with 3). They are outside this task's scope — the brief said to edit 8906
  only — and are listed here so they are not mistaken for newly created damage. `9553` is the HUD
  cannon-circle tracker, which is adjacent to this session's cannon work.
- The 1,230 other unsatisfied `AFTER` targets are ordinary queue ordering: the artifact does not exist yet
  but its producer is queued, so they resolve in order.

## Commands run

```
$ ls tmp/freebuff/low/too-similar
$ grep -ln "jeb-qwen-fair-test" queue/*.txt done/*.txt     -> queue/8906-smart-search-route-after-jeb.txt
$ uv run python Tools/scripts/trigram_overlap.py … --write  -> PASS 0.0994 / 0.0356
$ uv run python Tools/scripts/trigram_overlap.py … --check   -> PASS, record match yes
$ python - <<'EOF'  (producer map)
import glob, os, re
def header(path, key):
    txt = open(path, encoding="utf-8", errors="replace").read()
    m = re.search(rf"^{key}:\s*(.+)$", txt, re.M)
    return m.group(1).strip() if m else None
briefs = sorted(glob.glob("tmp/freebuff/queue/*.txt")) + sorted(glob.glob("tmp/freebuff/queue/held/*.txt")) \
       + sorted(glob.glob("Working/Queue/rewrites/*.txt"))
producers = {}
for b in briefs:
    d = header(b, "DONE")
    if d: producers.setdefault(d.replace("/", os.sep), []).append(os.path.basename(b))
for b in briefs:
    after = header(b, "AFTER")
    for p in [x.strip() for x in (after or "").split(",") if x.strip()]:
        k = p.replace("/", os.sep)
        if not (os.path.exists(k) or k in producers):
            print(os.path.basename(b), "->", p)
EOF
```

## UNKNOWNs

| # | unknown | why it stays unknown |
|---|---|---|
| U1 | the guard's own similarity metric (ratio, shingle size, threshold) | the guard is not in this checkout; the 0.30 ceiling in the brief is the only stated number, and the metric used here is declared rather than assumed to match |
| U2 | whether the rewrite is picked up by the queue runner | `Working/Queue/rewrites/` is where the brief asked for it; moving it into `queue/` is the operator's/queue's step, not this task's |
| U3 | whether the scoring stage will actually pass its own gates | it depends on `fair_runs/` contents, which this task does not inspect beyond existence |
| U4 | who authors the two missing HUD reports behind the 7 remaining orphans | not this brief; listed in §The producer check |

## Revert

- Delete `Working/Queue/rewrites/8863-rewrite.txt` and `Working/Queue/rewrites/8863-rewrite-overlap.json`.
- Delete `Tools/scripts/trigram_overlap.py`.
- Put `8906-smart-search-route-after-jeb.txt` back: `AFTER: E:/Modding/JC3-Batmobile/tmp/freebuff/reports/jeb-qwen-fair-test.md`
  and the body clause `unless reports/jeb-qwen-fair-test.md says otherwise`.
- Nothing in `tmp/freebuff/low/` was modified, so no restore step is needed there.
