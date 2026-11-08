# Independent review — T-23 · Ledger close-out and build batches

Reviewer: Freebuff (did not write this card). Date: 2026-10-29.
Scope: `GRAB_BACKLOG.md` §0.5 (R1–R14), the T-23 card (§7, line 974), the §12 `T-23` row (1332),
`MODLOG.md` §"T-23 · Ledger close-out and build batches — done" (14043–14176), the outputs
(`Working/Translation/BUILD_BATCHES.md`, `build_batches.json`, `STATUS.md`,
`Research/BatmobileGrab/COVERAGE.{md,json}`) and the scripts (`Tools/scripts/t23_closeout.py`,
`Tools/scripts/bmak_coverage.py`).
Read-only: nothing under `Research/`, `Tools/`, `Working/`, `GRAB_BACKLOG.md`, `MODLOG.md` or the
game install was written; no game launched. This report is the only file written.

## VERDICT: **needs rework**

The card's own gate is **red on disk**: `python Tools/scripts/t23_closeout.py --check` exits **1**
with two FAILs (`BUILD_BATCHES.md` and `build_batches.json` differ from the re-derived record),
while §12 says `T-23 | done` and the MODLOG ends "T-23 done". The diff shows why and it is not
cosmetic — three feature codes changed verdict and two counts moved, because the artefacts embed
live ledger dispositions that later cards edited. Separately, two numbers the MODLOG states do not
reproduce (`14 payloads`, the four "blocked" codes), and the `documented` fallback counts a bare
mention as *carried*, which contradicts the MODLOG's own description of how document rows are read.

What is solid: the 777-row feature census (0 unassigned), the assumed-row gate (1 of 180, `T-E5`
signed off), D-1…D-10 (10/10 answered with dates), the 14 B steps, and the finding that the HUD
has no build step (no B card body mentions `hud.gfx`). The tool is honest about its limits.

## Check output (verbatim)

```
$ python Tools/scripts/t23_closeout.py --check
gate TX: 75 codes (62 carried, 9 named omission, 4 blocked, 0 unmapped) | 198 ledger rows | assumed 1 (0 unsigned) | decisions 10/10 answered | 14 payloads over 14 B steps
FAIL BUILD_BATCHES.md differs from the re-derived record
FAIL build_batches.json differs from the re-derived record
2 problem(s)
EXIT=1
```

The other three checks the card names are green now:

```
$ python Tools/scripts/bmak_coverage.py --check
423 fields -> 19 rows; E:\Modding\JustCause3\JC3-Batmobile\Research\BatmobileGrab\COVERAGE.md
  … (17 rows)
777 feature rows -> 34 rows (0 unassigned)
  animation   253 rows ->  9 T rows, 0 unassigned
  audio       361 rows ->  8 T rows, 0 unassigned
  lights      101 rows ->  8 T rows, 0 unassigned
  weapons      62 rows -> 10 T rows, 0 unassigned
check ok
EXIT=0
$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 40 keep 60 epe 26 re-read 0 blocked 13 out 36 superseded 7 | edits 35 over 16 rows
check ok
EXIT=0
$ python Tools/scripts/status_audit.py --check
STATUS.md is current
EXIT=0
```

Note `t_rows` now prints `next 40 keep 60`; the MODLOG quotes `next 39 keep 61`. That one row
moving is the witness for issue 1.

## Issues

### 1. The gate fails: both artefacts are stale, and three codes flipped verdict
`t23_closeout.py --check` rejects both files. Re-deriving in memory and diffing (read-only) gives
the whole drift:

```
-| ledger rows | 198 = blocked 13, edit 16, epe 26, keep 61, next 39, out 36, superseded 7 |
+| ledger rows | 198 = blocked 13, edit 16, epe 26, keep 60, next 40, out 36, superseded 7 |
-| ARM-1 | blocked | `T-DM9` (blocked) | T-14 |
-| ARM-2 | carried | `T-DM1` (keep); `T-DM4` (keep) | T-14 |
+| ARM-1 | carried | `T-DM9` (next) | T-14 |
+| ARM-2 | carried | `T-DM1` (next); `T-DM4` (keep) | T-14 |
-| AUD-1 | carried | `A-01` (carried (document row)) | T-16 |
+| AUD-1 | blocked | `A-01` (blocked) | T-16 |
-| MOD-1 | carried | `T-MD1` (next); `T-MD2` (next); `T-MD3` (keep) | T-15 |
+| MOD-1 | carried | `T-MD1` (next); `T-MD2` (blocked); `T-MD3` (keep) | T-15 |
```

and in the JSON, besides those states: `/gate/assumed/evidenced` 127 → 126,
`/gate/dispositions/keep` 61 → 60, `/gate/dispositions/next` 39 → 40, and decision D-1's data cell
(the older text "was an assembly envelope, not rubber" → "has no source and what it measured is
UNKNOWN"). Cause: `T-DM9` moved blocked→next, `T-DM1` keep→next, `T-MD2` next→blocked, `A-01`'s
line now reads `blocked`, and §11 D-1's cell was edited — all after 00:36, when the artefacts were
written. §12 still says `done`.

Why this matters beyond "regenerate": a code's verdict is a function of a disposition **word**
(`blocked`/`next`/`keep`), so `ARM-1` became "carried" and `AUD-1` became "blocked" with no new
evidence about either requirement. That is R5 in its pure form — the member's status label standing
in for the behaviour. And because the artefacts embed the ledger's per-disposition counts, **every
later ledger edit turns this done card red**; nothing in the card or the MODLOG says so.

### 2. The four "blocked" codes in the MODLOG are not the four derived now
MODLOG "UNKNOWNs and limits" item 2: "`ARM-1` (T-DM9 needs the `CCar.invulnerable` write), `WPN-4`/
`WPN-5` (no disable/duration member…), `AUD-4` (a hybrid car has no mode switch…)". Re-derived
blocked set: **`AUD-1`, `AUD-4`, `WPN-4`, `WPN-5`**. `ARM-1` is now "carried" (its only anchor
`T-DM9` reads `next`, and `next` is in the carried set) and `AUD-1` is now blocked (`A-01` reads
`blocked`). The §12 row's "4 blocked" is right in count, wrong in membership.

### 3. `documented` counts as *carried*, contradicting the MODLOG
`doc_row_state()` returns `documented` when an anchor's line carries none of the disposition words;
`feature_gate()` then includes `"documented"` in the carried set. 17 document rows land in that
state, and **12 codes are carried on nothing but that fallback**: `ANI-2`, `ANI-3`, `ANI-4`,
`ANI-5`, `ANI-6`, `ANI-7`, `ANI-8`, `ANI-9`, `AUD-2`, `AUD-7`, `CAM-1`, `HUD-1`. Example:
`ANI-5`'s only anchor is `P-09` in `T8_PARTS.md:54`, a part row (`batmobile_aero_flap_l_f`, the
air-brake flap) with no disposition at all — the code is "carried" because the string is there.
The MODLOG says the opposite: "a document-only row is read from its own disposition words rather
than reported as carried". It is reported as carried precisely when it has none.

### 4. "24 of the 75 codes are carried … by rows that live in the phase-T documents" — actual 22
Measured: 22 of the 62 carried codes have at least one document-sourced anchor; 27 codes touch a
document row at all. The MODLOG's 24 reproduces neither number (and the four doc rows that are
`blocked` — `AUD-1`, `AUD-4`, `HUD-2`, `WPN-12` — are not carried at all).

### 5. "14 payloads" is 12 payloads + 2 records, and three artefacts have no step
The tool's own `kind` field: `{'payload': 12, 'record': 2}`. The sentence "14 payloads over the 14 B
steps, `t19_hud.json` the one payload no step writes" therefore mixes its nouns; and "the one" is
true only for `kind == payload`. Unassigned in the re-derivation:

```
t19_hud.json          payload  []  10 rows
T10_OPEN_ROWS.json    record   []  16 rows
damage_switches.json  record   []   0 rows
```

Two of those are empty-step *records* rather than edit payloads, so the sentence is defensible if
read as "payload", but as printed it hides two unassigned artefacts — one of them 16 rows of
record — behind "the one".

### 6. The Done criterion and what `--check` verifies
The card's Done is "all checks green; every §1 feature code maps to ≥ 1 row; decisions D-1…D-10 are
answered or their rows are `blocked: D-n` with the user informed". `--check` verifies the 75-code
map, the assumed row, the decisions, the batch list and the two artefacts — but **none of the four
checks** (`t_rows`, `status_audit`, `bmak_coverage`, and itself) is run from inside it, so "all
checks green" is a human claim stitched from six commands. They are green when run individually
(above), so Done is met on that axis today; the artefact diff in issue 1 is what breaks it.

### 7. Minor: "§12 still counts it `todo`" is not literally true
§12 has no `B-12` row: the build tracker is one range row `| B-04 … B-14 | todo | |` (line 1336).
`B-12` is inside that range, so the statement is morally right, but a reader looking for the row
will not find it.

### 8. Not an issue — verified
- **777 feature rows, 0 unassigned** ✓ — 253 animation + 361 audio + 101 lights + 62 weapons, per
  the check's own per-family lines.
- **198 ledger rows** ✓ (`t_rows.py check`).
- **assumed 1 of 180, and it is `T-E5` signed off** ✓ (`gate()["assumed"]`: count 1, in_scope 180,
  rows `[("T-E5", True)]`, `unsigned: []`).
- **D-1…D-10 10/10 answered** ✓ (ten decisions, each with a `resolved 2026-…` date).
- **14 B steps** ✓ (`#### B-01` … `#### B-14`), and **no B card writes `hud.gfx`** ✓ — `hud.gfx`
  appears only in §1's HUD-1 row and T-19's card body, so the HUD gap the MODLOG reports is real.
- **`WPN-6…10` as named omissions** ✓ is faithful to the source: `T7_WEAPONS.md:81` states "WPN-6 is
  a named omission (proof `Research/JC3Grab/TETHER.md`: 0 functional winch classes)".

## Spot-checks

| value in the doc | where verified | result |
|---|---|---|
| **777** feature rows (253 / 361 / 101 / 62) | `bmak_coverage.py --check` per-family lines; sum = 777 | agree |
| **198** ledger rows | `t_rows.py check` output, and `ledger()` length | agree |
| **1** assumed row of **180** in scope, `T-E5` | `t23_closeout.gate()["assumed"]` (count 1, in_scope 180, `[("T-E5", True)]`) | agree |
| **10/10** decisions answered | `gate()["decisions"]`: 10 items, all with a resolved date | agree |
| **14** payloads over **14** B steps | `gate()["batches"]`: 14 steps; entries split 12 `payload` + 2 `record` | count right, noun wrong (issue 5) |
| `ARM-1` **blocked** (MODLOG) | `gate()["features"]["ARM-1"]` → `carried`, `T-DM9` now `next` | **no longer true** (issue 2) |

Not verified: the MODLOG's tamper table (6/6). `tmp/t23_tamper.sh` exists (2,920 B) and
`tmp/t23_tamper.log` (1,631 B) with it, but running it edits and restores `BUILD_BATCHES.md`,
`build_batches.json`, `COVERAGE.*` and `t23_closeout.py` — outside this review's read-only terms,
so the six results are taken as reported. The drift in issue 1 does show the artefact diff firing,
which is the mechanism those tampers rely on.
