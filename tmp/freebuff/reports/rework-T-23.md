# Rework — T-23 · Ledger close-out and build batches

**STATUS: PASS — reworked, gate green, 7 of 7 issues CONFIRMED (0 rejected), one of them with
corrected numbers (`documented` codes: 10, not 12). `python Tools/scripts/t23_closeout.py --check`
exits 0 and runs the three sibling checks itself. Nothing was hand-edited in a generated file, no
ledger row was changed, no game was launched, nothing under `D:/Games` was touched, nothing was
committed.**

Input: `tmp/freebuff/reports/review-T-23.md`. The review is treated as evidence: every issue was
re-checked against the files with the commands quoted below before anything was edited.

Date: 2026-10-29. Card: `GRAB_BACKLOG.md` §7 T-23 (line 974), rules §0.5 R1–R14.

---

## 1. Issue 1 — the gate is red on disk; both artefacts are stale — **CONFIRMED**

Reproduced exactly as reported, before any edit:

```
$ python Tools/scripts/t23_closeout.py --check
gate TX: 75 codes (62 carried, 9 named omission, 4 blocked, 0 unmapped) | 198 ledger rows | assumed 1 (0 unsigned) | decisions 10/10 answered | 14 payloads over 14 B steps
FAIL BUILD_BATCHES.md differs from the re-derived record
FAIL build_batches.json differs from the re-derived record
2 problem(s)
EXIT=1
```

The drift is the ledger's, not a fresh judgement: `T-DM9` blocked→next (T-14's option B),
`T-DM1` keep→next, `T-MD2` next→blocked, `A-01` →blocked, and §11 D-1's cell edited — all after the
00:36 `--write`. Stale versus regenerated, from the two files themselves:

```
--- stale artefact (before) ---
| ledger rows | 198 = blocked 13, edit 16, epe 26, keep 61, next 39, out 36, superseded 7 | `T_ROWS.jsonl` |
| ARM-1 | blocked | `T-DM9` (blocked) | T-14 |
| ARM-2 | carried | `T-DM1` (keep); `T-DM4` (keep) | T-14 |
| AUD-1 | carried | `A-01` (carried (document row)) | T-16 |
| MOD-1 | carried | `T-MD1` (next); `T-MD2` (next); `T-MD3` (keep) | T-15 |
--- regenerated (after) ---
| ledger rows | 198 = blocked 13, edit 16, epe 26, keep 60, next 40, out 36, superseded 7 | `T_ROWS.jsonl` |
| ARM-1 | carried | `T-DM9` (next) | T-14 |
| ARM-2 | carried | `T-DM1` (next); `T-DM4` (keep) | T-14 |
| AUD-1 | blocked | `A-01` (blocked) | T-16 |
| MOD-1 | carried | `T-MD1` (next); `T-MD2` (blocked); `T-MD3` (keep) | T-15 |
```

and the review's other witnesses reproduce too: `t_rows.py check` prints `next 40 keep 60` (the old
MODLOG quoted `next 39 keep 61`), and the JSON's `/gate/dispositions/keep` 61→60, `next` 39→40.

**Fix (generator, then `--write`).** The two files were regenerated from the current ledger — that
is what R11 requires (counts generated, never typed) and it is why the fix is a regeneration and not
a hand edit. To stop the same confusion recurring, the page and the FAIL text now say the numbers are
**live** and that any ledger/§1/§7/§8/§11 edit must be followed by `--write`:

* `BUILD_BATCHES.md` header: "**Every disposition on this page is live.** … `--check` then fails
  until `python Tools/scripts/t23_closeout.py --write` is re-run. This page is not frozen by the card
  being `done`, and it is not the gate - the command is."
* `--check` FAIL text: `… differs from the re-derived record (regenerate with --write: every
  disposition on it is live)`.

The verdict flip itself is not re-litigated here: a code's state is its carrying row's disposition,
and T-14/T-15/T-16 changed those dispositions. Inventing a second state rule would be the R4/R5
failure the review warns about, in the other direction.

## 2. Issue 2 — the MODLOG's four "blocked" codes are not the derived four — **CONFIRMED**

```
$ python -c "… t23_closeout.gate() …"   # pre-fix state
blocked: ['AUD-1', 'AUD-4', 'WPN-4', 'WPN-5']
```

So the old log's `ARM-1` no longer blocked and `AUD-1` now is; §12's "4 blocked" was right in count,
wrong in membership — exactly as the review says.

**Fix.** Membership is now printed by the script instead of being typed into prose:
`BUILD_BATCHES.md` §1 carries a `| blocked codes |` row. Post-fix (after issue 3, `HUD-2` also
becomes blocked):

```
blocked: ['AUD-1', 'AUD-4', 'HUD-2', 'WPN-4', 'WPN-5']
documented: ['ANI-2', 'ANI-3', 'ANI-4', 'ANI-5', 'ANI-6', 'ANI-7', 'ANI-8', 'ANI-9', 'CAM-1', 'HUD-1']
```

The MODLOG is append-only, so the old sentence is corrected in the `T-23 rework — done` entry rather
than edited. §12's `T-23` line now names the five blocked codes.

## 3. Issue 3 — `documented` counts as *carried*, contradicting the MODLOG — **CONFIRMED, with two wrong numbers in the review**

The mechanism is real: `feature_gate()` had
`carried = states & (DISPO_CARRIED | {"carried (document row)", "documented"})`, while
`doc_row_state()`'s own docstring says a document-only row "is reported as `documented` with its
doc, never as carried". Proof that a code is carried on nothing but that fallback:

```
as built:  ANI-5 = documented [('T8_PARTS.md', 'P-09', 'documented')]
```

(`ANI-5`'s only anchor is the `P-09` behaviour row — behaviour `AirBrake`, joint bone, axis, extent,
rate, `no hinge`, damage type — which states no disposition word, so under R4 it states no
*direction* for the build.)

Two of the review's numbers do not reproduce: the fallback carries **10** codes, not 12, and the
state occurs on **27** anchor occurrences (**21** distinct anchors), not 17.

```
carried on documented-only: 10 ['ANI-2', 'ANI-3', 'ANI-4', 'ANI-5', 'ANI-6', 'ANI-7', 'ANI-8', 'ANI-9', 'CAM-1', 'HUD-1']
AUD-2 carried [('A-02', 'carried (document row)', 'doc')]
AUD-7 carried [('A-13', 'carried (document row)', 'doc')]
doc-sourced anchors by state: Counter({'documented': 27, 'named omission': 6, 'blocked': 5, 'carried (document row)': 3})
distinct doc anchors: 34
```

`AUD-2` is carried by its own word (`A-02` says `mapped`) and `AUD-7` by `A-13`'s `remove`; neither
ever used the fallback. So `AUD-2`/`AUD-7` in the reviewer's list are wrong, the issue is not.

**Fix.** `documented` is out of the carried set and gets its own state and its own §1 row; a code
with a blocked anchor and nothing carried reads `blocked`; a mixed state that fits nothing now fails
the gate (`rows exist but none of them states a disposition (R4)`) instead of passing as `unknown`.
Rule demo, in memory, no file written (`tmp/t23rework/rule_demo.py`):

```
as built:  ANI-5 = documented [('T8_PARTS.md', 'P-09', 'documented')]
as built:  WPN-1 = carried [('T-WP1', 'next')]
demo: P-09 read as blocked       -> ANI-5 = blocked
demo: T-WP1 read as documented   -> WPN-1 = documented
restored: ANI-5 = documented | WPN-1 = carried
```

Result: 62 carried / 9 omission / 4 blocked / 0 documented becomes **51 carried / 9 named omission /
5 blocked / 10 documented** (the tenth blocked is `HUD-2`: `T-HUD5` and `T-HUD11` blocked,
`T-HUD14`/`T-HUD18` documented, nothing carried — it had been called carried for the same reason).
Tamper 4 in §6 puts the old rule back and the gate goes red.

## 4. Issue 4 — "24 of the 75 codes" reproduces neither 22 nor 27 — **CONFIRMED**

Pre-fix measurement of the review's two numbers:

```
carried codes with >=1 doc-sourced anchor: 22
codes touching a doc-sourced anchor at all: 27
```

Both reproduce on the pre-fix code; `24` is in neither. **Fix:** the census is now rendered from the
re-derivation, so no log has to type it: §1 prints
`| document rows | 34 distinct anchors - 4 blocked, 3 carried (document row), 21 documented, 6 named omission; 11 of the 51 carried codes take one, 27 codes touch one |`.
The "11 of 51" (not 22 of 62) is the same fact after issue 3 removed 10 codes from the carried set
and moved `HUD-2` to blocked; `22`/`27` are the pre-fix values and are recorded here as such.

## 5. Issue 5 — "14 payloads" is 12 payloads + 2 records, and three artefacts have no step — **CONFIRMED**

```
artefacts: 14 Counter({'payload': 12, 'record': 2})
  T10_OPEN_ROWS.json       record   steps=[] rows=16
  damage_switches.json     record   steps=[] rows=0
  t19_hud.json             payload  steps=[] rows=10
  … (11 more payloads, each with >=1 step)
```

**Fix.** The status line now reads `14 artefacts (12 payloads + 2 records) over 14 B steps`, and §5
("Artefacts no phase-B step names") lists **all three** with their kind instead of hiding the two
records behind "the one":

```
- `t19_hud.json` - payload, 10 rows / 10 values, `Working/Translation/t19_hud.json`: no B-01...B-14 card writes `hud.gfx`, so the HUD rows need a step B-15 (or a clause in B-13) before phase V can gate them.
- `T10_OPEN_ROWS.json` - record, 16 rows / 16 values, `Working/Translation/T10_OPEN_ROWS.json`: a record, not an edit file: no step is missing by design.
- `damage_switches.json` - record, 5 rows / 5 values, `Working/Translation/damage_switches.json`: a record, not an edit file: no step is missing by design.

3 artefact(s) with no step: 1 payload(s), 2 record(s).
```

`damage_switches.json` also stops printing `0 rows`: `payload_rows()` now reads its `switches` key
(5), which is the honest count — the old `0` was a reader gap, not an empty file.

## 6. Issue 6 — the Done criterion is stitched from six commands — **CONFIRMED (as stated); fixed**

`main()` did only the two byte comparisons; `t_rows`, `status_audit`, `bmak_coverage` and the gate
itself were four separate human claims. **Fix:** `--check` now runs
`t_rows.py check`, `status_audit.py --check` and `bmak_coverage.py --check` as subprocesses and
appends a `FAIL` for any non-zero exit, so gate TX is one command and cannot be green while a
sibling is red. `--gate` stays the light status-only mode. Proved by tamper 6 (§6): a stale
`STATUS.md` now fails `--check` with
`siblings: t_rows.py check exit 0 | status_audit.py --check exit 1 | bmak_coverage.py --check exit 0`
and `FAIL status_audit.py --check exits 1: STATUS.md is stale; run --write`.

## 7. Issue 7 — "§12 still counts it `todo`" is not literally true — **CONFIRMED**

```
$ grep -n 'B-12\|B-04 … B-14' GRAB_BACKLOG.md
1081:#### B-12 · Variants (only if D-2 = two variants)   S · deps: B-05…B-11, T-15 · serves: MOD-1/2
1258:| D-2 | … **resolved 2026-10-28 (user): (b) one hybrid car** … (B-12 `skipped: D-2`) | … | B-12 |
1336:| B-04 … B-14 | todo | |
```

There is no `B-12` tracker row: it is inside the range row `| B-04 … B-14 | todo | |`, and §11 D-2
already records `B-12 skipped: D-2`. It is a MODLOG wording error, not a generator defect, and the
log is append-only — corrected in the `T-23 rework — done` entry. §12 was touched on the `T-23` line
only, as instructed, so the range row still reads `todo` for `B-12`; that tracker wart is recorded as
a limit, not silently changed.

## 8. Issue 8 ("not an issue") — **re-verified, no action**

```
$ python Tools/scripts/bmak_coverage.py --check
777 feature rows -> 34 rows (0 unassigned)
  animation   253 rows ->  9 T rows, 0 unassigned
  audio       361 rows ->  8 T rows, 0 unassigned
  lights      101 rows ->  8 T rows, 0 unassigned
  weapons      62 rows -> 10 T rows, 0 unassigned
check ok
$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 40 keep 60 epe 26 re-read 0 blocked 13 out 36 superseded 7 | edits 35 over 16 rows
check ok
$ grep -n 'hud.gfx' GRAB_BACKLOG.md | head -3
172:| WPN-12 | HUD: … | `hud.gfx` `InitVehicleWeapons`/`UpdateVehicleWeapons` (T-HUD5) |
246:| HUD-1 | Speed, nitro meter (afterburner), health bar | `hud.gfx` (T-HUD1…3) |
733:In: decompiled `ui/hud.gfx` (260 scripts), `T6_HUD_CAMERA.md`.
```

777 = 253 + 361 + 101 + 62 ✓; 198 ledger rows ✓; `hud.gfx` appears only in §1's two rows and T-19's
card body, so no B card writes it ✓. The review's one unverified item — the old MODLOG's tamper
table — is replaced by an independently run 6/6 set (§6), not taken on trust.

---

## 9. Files changed

| file | change |
|---|---|
| `Tools/scripts/t23_closeout.py` | the only edited script: carried set drops `documented`; state cascade adds `documented`/`unmapped`/R4 `unknown` failure; `doc_stats()` + `codes_documented`/`codes_unknown`/`blocked_codes`/`documented_codes`/`doc_rows` (schema 1→2); `payload_rows()` reads `switches`; §1 blocked/documented/document-row lines; §2 note; §5 lists every step-less artefact by kind; §7 command block; `sibling_checks()` wired into `--check`; live-disposition note in the header and in the FAIL text |
| `Working/Translation/BUILD_BATCHES.md` | regenerated by `--write` (not hand-edited) |
| `Working/Translation/build_batches.json` | regenerated by `--write` (not hand-edited), schema 2 |
| `GRAB_BACKLOG.md` §12 | the `T-23` line only: new counts, the five blocked codes, the ten documented codes, 12 payloads + 2 records, 3 step-less artefacts, both MODLOG sections |
| `MODLOG.md` | appended `T-23 rework — intended change` (before any edit) and `T-23 rework — done` |
| `tmp/t23rework/{before/*,tamper.py,tamper.log,rule_demo.py}` | pre-rework copies and the two test harnesses |

Not touched: `T_ROWS.jsonl` or any other card's output, `STATUS.md` (already current), any build,
any game file, `D:/Games`, any shared game module, git (no commit, no push).

## 10. `--check` output, verbatim (final state)

```
$ python Tools/scripts/t23_closeout.py --check
gate TX: 75 codes (51 carried, 9 named omission, 5 blocked, 10 documented, 0 unmapped) | 198 ledger rows | assumed 1 (0 unsigned) | decisions 10/10 answered | 14 artefacts (12 payloads + 2 records) over 14 B steps
siblings: t_rows.py check exit 0 | status_audit.py --check exit 0 | bmak_coverage.py --check exit 0
gate TX ok: every §1 code maps to a row, assumed rows are signed off, D-1...D-10 answered
EXIT=0
```

The three checks `--check` now runs itself, run directly:

```
$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 40 keep 60 epe 26 re-read 0 blocked 13 out 36 superseded 7 | edits 35 over 16 rows
check ok
EXIT=0

$ python Tools/scripts/status_audit.py --check
STATUS.md is current
EXIT=0

$ python Tools/scripts/bmak_coverage.py --check
423 fields -> 19 rows; E:\Modding\JC3-Batmobile\Research\BatmobileGrab\COVERAGE.md
  … (17 rows)
777 feature rows -> 34 rows (0 unassigned)
  animation   253 rows ->  9 T rows, 0 unassigned
  audio       361 rows ->  8 T rows, 0 unassigned
  lights      101 rows ->  8 T rows, 0 unassigned
  weapons      62 rows -> 10 T rows, 0 unassigned
check ok
EXIT=0
```

## 11. Tamper test — 6/6 caught, every file restored byte-exactly

`python tmp/t23rework/tamper.py` (log `tmp/t23rework/tamper.log`), each tamper applied, the check
run, the file restored from a byte copy and verified by sha256, then the check re-run to `EXIT=0`:

```
### 1 md hand-edit (ledger rows 198 -> 197)
  tampered: exit=1
    FAIL BUILD_BATCHES.md differs from the re-derived record (regenerate with --write: every disposition on it is live)
  restored (sha256 match): exit=0
### 2 json hand-edit (gate.codes 75 -> 74)
  tampered: exit=1
    FAIL build_batches.json differs from the re-derived record (regenerate with --write: every disposition in it is live)
  restored (sha256 match): exit=0
### 3 gate anchor (WPN-1 -> a row the doc does not have)
  tampered: exit=1
    gate TX: 75 codes (50 carried, 9 named omission, 5 blocked, 10 documented, 1 unmapped) | …
    FAIL WPN-1: T7_WEAPONS.md has no `T-WP99`
  restored (sha256 match): exit=0
### 4 'documented' counted as carried again (review issue 3)
  tampered: exit=1
    gate TX: 75 codes (61 carried, 9 named omission, 5 blocked, 0 documented, 0 unmapped) | …
    FAIL BUILD_BATCHES.md differs from the re-derived record …
  restored (sha256 match): exit=0
### 5 'next' dropped from the carried dispositions
  tampered: exit=1
    FAIL APP-4: rows exist but none of them states a disposition (R4)
    … (13 codes)
  restored (sha256 match): exit=0
### 6 STATUS.md stale (sibling check wired in by issue 6)
  tampered: exit=1
    siblings: t_rows.py check exit 0 | status_audit.py --check exit 1 | bmak_coverage.py --check exit 0
    FAIL status_audit.py --check exits 1: STATUS.md is stale; run --write
  restored (sha256 match): exit=0

tamper result: 6/6 caught, all restored byte-exactly
```

Tamper 4 is the issue-3 regression test: with the old rule restored the gate prints
`61 carried … 0 documented` (the review measured 62 because `HUD-2` was still counted as carried
then too) and `--check` goes red.

## 12. Limits this rework does not remove

1. **Ten codes are `documented`, not carried.** `ANI-2`…`ANI-9`, `CAM-1`, `HUD-1` rest on
   document rows that state no disposition (`T8_PARTS.md` P-rows, `T9_INTERACTION.md` object rows,
   `T6_HUD_CAMERA.md` T-HUD/T-CAM rows). The card's Done asks only that every code map to ≥ 1 row,
   and it does — but the page now says plainly that no disposition exists for these ten, instead of
   counting them carried. Absorbing those rows into the ledger is a decision this card does not make.
2. **`t19_hud.json` still has no phase-B step**; the HUD hole is named, not filled.
3. **The payload → step mapping is declared glue**, checked for existence on both sides, not derived.
4. **`B-12` is inside the §12 range row `B-04 … B-14 | todo`** while §11 D-2 records it as
   `skipped: D-2`. Out of scope for a single-line §12 edit.
5. **Nothing has been run in JC3.** Gate TX is a file-level gate.
