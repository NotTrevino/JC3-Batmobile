# Tracker ↔ report reconciliation (read-only, 2026-11-07)

PURPOSE: tell the operator which §12 rows in `GRAB_BACKLOG.md` no longer describe the report they
cite, and which reports have no row at all, so rows can be flipped **after** re-running the report's
own `--check`.

WHAT WAS NOT DONE (the brief's constraint): no tracker was edited (`GRAB_BACKLOG.md`,
`Working/Translation/T_ROWS.jsonl`, `STATUS.md`, `BLOCKED_PROPOSALS.*` all untouched), and **no
`--check` was run** — every check command below is quoted from the report that names it, not executed.
Commands that write (`--write`, `status_audit.py --write`, `t_blocked.py --write`, `t22_reopen.py
--write`, `t23_closeout.py --write`) are marked **WRITE — do not run** and are never the check to
re-derive with.

## 1. Baseline (measured off disk, 2026-11-07)

| quantity | value | how |
|---|---:|---|
| rows in §12 (`GRAB_BACKLOG.md:1809-2050`) | 217 | parsed `\| id \| status \| evidence \|` between `## 12.` and `## 13.` |
| reports in `tmp/freebuff/reports/*.md` | 606 at the sweep (608 when re-measured minutes later — the two reports this session wrote are in that delta) | `glob` |
| reports a §12 row cites by name | **17** | substring match of each report basename in a row's evidence cell |
| of those 17, dated before 2026-11-06 | 2 (`G2X.md` 2026-10-28; `stale-status-numbers.md` 2026-11-05) | mtime |
| reports dated **2026-11-07** | 42 at the sweep (44 on re-measure, per the row above) | mtime ≥ 2026-11-07 00:00 |
| of those 42, cited by any row | **0** | same substring test |
| reports dated 2026-11-06 | 144 | mtime |
| of those, cited by any row | 15 | same test |

The single fact the whole table turns on: **the entire 2026-11-07 output (42 reports) is newer than
every row that could describe it, and no row cites one of them.** Where a row's evidence cell already
contains 11-06 numbers, those numbers are one or two passes behind the reports (§3).

Limitation, stated because it cannot be measured here: §12 is one file, so a row has no per-row
mtime and no git history to date it (`total_commits: 2`). "Newer than the row" is therefore judged
from (a) the report's mtime and (b) the date the row's own text states (`REOPENED 2026-11-07`,
`re-run 2026-11-06`, `task 8301`). Where a row states no date, the verdict in §2/§3 is a content
comparison (does the row's claim still hold against the report), not a timestamp comparison.

`QUEUE_MAP.md` read for this pass adds the *why* of the gaps but no per-report rows: it says the
8770-8781 batch was queued 2026-11-07 as "dependency-free fillers for All daily", i.e. the batch was
never given §12 rows by design. That is the cheapest fix in §4 — not a stale row, a missing one.

## 2. Group A — row and cited report still agree (17 rows, 17 reports)

Verdict = the row's status word and evidence claim still describe the report on disk. Nothing to flip;
listed so the operator knows these were checked rather than skipped.

| row id | row status (quoted) | report it cites | report mtime | report's own check | verdict |
|---|---|---|---|---|---|
| `T-17` | `done` | `tmp/freebuff/reports/apply-effects-rows.md` | 2026-11-06 09:10 | `python Tools/scripts/t17_fx.py --check` | current — report says `PASS: 17 rows (17 chosen, 0 named omissions)`, row says "all 17 with a chosen carrier" |
| `B-17` | `todo` | `tmp/freebuff/reports/effc-format-writable.md` | 2026-11-06 08:11 | `python Tools/scripts/effc_writer.py check` (note: `check`, not `--check`) | current — row's "writer proof" claim matches `95/95 carry byte-identical` |
| `T-24` | `todo` | `tmp/freebuff/reports/apply-light-rows.md` | 2026-11-06 09:22 | `python Tools/scripts/t18_lights.py --check` | current — row says "card added by apply-light-rows.md"; report §`t18_lights` line is **PASS**, 14 rows |
| `T-25` | `todo` | `tmp/freebuff/reports/apply-light-rows.md` | 2026-11-06 09:22 | same | current — same report, same PASS |
| `T-26` | `todo` | `tmp/freebuff/reports/apply-suspension-rows.md` | 2026-11-06 21:23 | `python Tools/scripts/status_audit.py --check` | current on its own cell (T-R2 0.1/0.1 because the drag triple has no decoded value); see §3 for the counts it also writes |
| `B-22` | `todo` | `tmp/freebuff/reports/suspension-unit-bridge.md` | 2026-11-06 05:12 | `python Tools/scripts/t_s6_bridge.py --check` | current — droop/travel have no member, `max_length_offset` 0.30 the only carrier, 0 on 166 cars |
| `B-23` | `todo` | `tmp/freebuff/reports/suspension-unit-bridge.md` | 2026-11-06 05:12 | same | current — 750 / 20 / 5 have no per-mode member |
| `T-S6-bridge` | `done` | `tmp/freebuff/reports/suspension-unit-bridge.md` + `keep-audit-suspension-and-mass.md` (06:10) + `apply-suspension-rows.md` (21:23) | 2026-11-06 | `python Tools/scripts/t_s6_bridge.py --check` | current on its own 5 numbers; its "pins 14+4 → 13+4 = 17" line is superseded, §3 |
| `B-19` | `todo` | `tmp/freebuff/reports/hacker-and-tracker-gadgets.md` | 2026-11-06 05:09 | none named (its 7 oracles print `PASS wp7_fields_13` … `allegiance_files_0`) | current |
| `B-21` | `todo` | same | 2026-11-06 05:09 | none named | current — fire position 30.0 deg, no homing member |
| `B-20` | `todo` | `tmp/freebuff/reports/sonar-and-scan-pulse.md` | 2026-11-06 04:57 | none named (prose-only) | current on its claim; no re-derivation exists, so the row cannot be flipped on evidence — see §5 note |
| `T-L10-L23-carriers` | `done (research; ledger rows updated by brief 8203)` | `tmp/freebuff/reports/muzzle-and-forensics-lights.md` | 2026-11-06 04:53 | none named (`t_lights_forensics.py --check 16/16` is quoted inside the report) | current |
| `T-FX13-carrier` | `done (research; ledger row T-FX13 updated by brief 8202)` | `tmp/freebuff/reports/fx13-shell-casings.md` | 2026-11-06 04:43 | `python Tools/scripts/fx13_casings.py --check` | current — report `STATUS: DONE`, 25 checks |
| `T-FX12-16-tracer` | `done (rows T-FX12/T-FX16 flipped to 'next')` | `tmp/freebuff/reports/fx12-16-tracer-and-trail.md` | 2026-11-06 04:38 | `python Tools/scripts/jc3weapons.py --check` | current |
| `G2-35` | `todo` | `tmp/freebuff/reports/carrier-ram-and-dodge.md` | 2026-11-06 03:56 | none named (report §`COMPROMISES`: "none proposed … no ledger row was edited") | current — capability still unbuilt, so `todo` is right |
| `STATUS-stale` | `finding` | `tmp/freebuff/reports/stale-status-numbers.md` | 2026-11-05 21:10 | `python Tools/scripts/status_audit.py --check` | current on content, but `finding` is not a §0.3 status word (see §5) |
| `G2X` | `done` | `tmp/freebuff/reports/G2X.md` | 2026-10-28 05:21 | `python Tools/scripts/g2x_gate.py --check` | current |

## 3. Group B — rows that look stale, with the report that supersedes them

Each entry quotes the row id, the row's current cell, the newer report, and **the exact cell that no
longer holds**. This is the list to work from; §4 is the same list as a flip sheet.

### 3.1 `T-BLOCKED` — blocked count is 15, not 17
- Row says: `| T-BLOCKED | done | … **17** blocked re-derived (13 ledger + 4 T6) of **216** in scope (re-run 2026-11-06) …`
- Newer evidence: `Working/Translation/BLOCKED_PROPOSALS.md` (mtime **2026-11-07 00:32**, its own line
  `STATUS: partial - 15 blocked rows enumerated (11 ledger + 4 T6 = STATUS.md's 15 of 216)`), and
  `tmp/freebuff/reports/apply-collision-and-audio-leads.md` (2026-11-07 00:34) which prints
  `PASS: 15 blocked rows re-derived (11 ledger + 4 T6) of 216 in scope`.
- Contradicted cell: the pair `17` / `13 ledger`. The ledger also moved 198 → **199** rows.
- Check to re-run: `python Tools/scripts/t_blocked.py --check` (read-only; its `--write` is the WRITE half).

### 3.2 `T-MD-D2-reopen` — blocked count is 15, not 18
- Row says: `| T-MD-D2-reopen | done (decision + card + 6 rows) | … `t_blocked.py --write/--check` PASS (**18 blocked of 216**) …`
- Newer evidence: `tmp/freebuff/reports/apply-mode-switch-rows.md` (2026-11-06 11:23) claimed 18 and was
  true at that moment; `tmp/freebuff/reports/apply-suspension-rows.md` (21:23, same day) reconciles to
  `13 ledger + 4 T6 = 17`; `apply-collision-and-audio-leads.md` (2026-11-07 00:34) pins **15**.
- Contradicted cell: `18`. The *decision* half of the row (D-2 reopened, B-12 live with four
  preconditions) still holds — only the count is stale.
- Check: `python Tools/scripts/t_blocked.py --check`.

### 3.3 `T-23` — gate TX and ledger counts are two passes behind
- Row says: `… gate TX: 75/75 §1 codes mapped … **51 carried / 9 named omission / 5 blocked** … **198 ledger rows** `edit 16 next 40 keep 60 epe 26 blocked 13 out 36 superseded 7``.
- Newer evidence: `tmp/freebuff/reports/translation-closeout-t23.md` (2026-11-07 00:38) and
  `apply-keep-audit-fixes-handling.md` (00:19) both print
  `gate TX: 75 codes (**58 carried, 3 named omission, 4 blocked**, 10 documented, 0 unmapped) | **199** ledger rows`
  and `ledger 199 rows | edit 16 next 109 keep 29 epe 26 re-read 0 blocked 11 out 1 superseded 7`.
- Contradicted cells: 51/9/5/10 → 58/3/4/10; 198 → 199 rows; `next 40 / keep 60 / blocked 13 / out 36` →
  `next 109 / keep 29 / blocked 11 / out 1`.
- Check: `python Tools/scripts/t23_closeout.py --check` (read-only; report uses `--write` then `--check`).

### 3.4 `B-12` — precondition 3's evidence file is no longer the newest
- Row says: `| B-12 | todo: D-2 reopened | … a runtime entity swap (**UNKNOWN**, `mode-switch-carriers.md` §7 U1) …`
- Newer evidence: `tmp/freebuff/reports/mode-swap-trigger-closest-system-plan.md` (2026-11-07 17:36).
  U1 is **still UNKNOWN**, so the precondition is unchanged and `todo` stays right; what is stale is the
  pointer — the newer plan names the candidate trigger (`USE_VEHICLE_MOD`), the entity pair (Rebel Drop
  item hash 443190071), what a spawn cannot carry (velocity/gear/health/ammo) and the file that settles
  U1. Row's own `--check` (`b12_variants.py --check`) still PASSes and still refuses to let the card be
  built, so the status is correct and only the evidence cell wants the new path.
- Check: `python Tools/scripts/b12_variants.py --check`.

### 3.5 `B-18` and `T-MD2-EMP-disable` — the EMP plan is not cited
- `B-18` says: `… chain and probes `tmp/freebuff/reports/immobiliser-and-emp-trigger.md` §7-§8; state scan …`
  and `T-MD2-EMP-disable` says: `… the effect half (pulse object) is decoded; closest system for turning an engine off is the engine's own `CEMPWeapon` path …`
- Newer evidence: `tmp/freebuff/reports/emp-effects-closest-system-plan.md` (2026-11-07 17:26) — the
  closest-system build plan for the disable, the effect/particle carrier and the audio event, with the
  numbers from the BmAK data. Neither row mentions it; `B-18`'s card is the one it was written for.
- Neither row's status changes (`B-18` `todo`, `T-MD2-EMP-disable` `done`): the report is a plan, not a
  payload. Verdict: **evidence cell stale, status correct**.
- Checks: `python Tools/scripts/t_md2_emp_state.py --check` (B-18), `python Tools/scripts/jc3forcepulse.py --check` (plan).

### 3.6 The collision family — three rows, one newer plan, and a `done` row that predates it
- `B-10` says `REOPENED 2026-11-07 (its Done rule was the render bbox)` and cites B-10d/B-10e +
  `Working/Translation/T22_REOPEN.md`; `T-22` says `REOPENED 2026-11-07 (drivable asset decoded)` and
  cites `COLLISION_WHERE.md`; `Collision-reopen` says `done` and cites `T22_REOPEN.md` + `t22_reopen.py`.
- Newer evidence: `tmp/freebuff/reports/collision-missing-shapes-closest-system-plan.md` (**2026-11-07
  17:32**) and `tmp/freebuff/reports/apply-collision-and-audio-leads.md` (00:34).
- What no longer holds: all three rows leave the consequence of "2 shapes missing / 0 free hull slots of
  54" open as a blocker. The plan shows box 1 protrudes past box 0 by **3.640 cm** and box 2 lies
  entirely inside box 0, so one body-0 hull to the union (693.945 × 374.536 × 207.500 cm) closes the gap
  inside the 5 cm gate with **no second instance** — the slot count is not the blocker the rows imply.
  The rows' two hard numbers (2 shapes missing, 0 free slots, 14 unbound) are still true; the *reading*
  of them is stale.
- Checks: `python Tools/scripts/t22_reopen.py --check` (read-only half), `python Tools/scripts/t22_collision.py --check`.

### 3.7 `V-01 … V-07` — the aggregate row is an RC2 statement
- Row says: `| V-01 … V-07 | partly done - see the V-xx rows (V-01, V-02, V-03, V-05, V-06 done on **RC2**; V-04 RED/partial; V-06-RC2 FAIL; V-07 not started) | stale placeholder corrected 2026-11-06 |`
- Newer evidence: `verify-v01-file-gates-rc4.md` (2026-11-07 12:27), `verify-v03-wiring-rc4.md` (11:52),
  `verify-v04-audio-rc4.md` (12:55) — three **RC4** verification reports that exist and are cited by no
  row. The row's own word is "placeholder", so this is a placeholder that was corrected before the RC4
  wave landed, not after.
- Checks: `python Tools/scripts/v01_rc4.py --check` (V-01), `python Tools/scripts/bm_audio.py --check` (V-04); `verify-v03-wiring-rc4.md` names none.

### 3.8 Rows that cannot be flipped on evidence at all
`B-20`, `T-L10-L23-carriers`, `G2-35`, `T-FX12-16-tracer` cite reports that name **no `--check` of their
own** (prose-only or checks quoted inside the report). Their `done`/`todo` words are not re-derivable by
a command; the operator would have to re-read the report. Not stale — unflippable as written.

## 4. Group C — the 42 reports dated 2026-11-07 with no §12 row

Columns: report | mtime | the report's own check (quoted; **WRITE** flagged) | cheapest row action.
"new row" = the tracker has no row for this work at all; "attach" = an existing row exists but does not name it.

### 4.1 RC4 build wave — 14 reports, 0 rows
`§12` mentions RC4 only as "no payload in RC4" (B-12, B-17…B-20, B-25, B-26). No row tracks the RC4
build itself, so `B-14`'s `done` still describes **bm-RC1**.

| report | mtime | check | action |
|---|---|---|---|
| `build-d01-scaffold-rc4.md` | 00:47 | `python Tools/scripts/bm_build.py --tag bm-RC4-base --check` | new row (RC4 build step 1) |
| `build-d02-parts-split.md` | 00:55 | `python Tools/scripts/bm_parts.py --check` | new row |
| `build-d03-lights-and-flares.md` | 10:12 | `python Tools/scripts/bm_rc4_lights.py --check` | new row (the card `8302` the watchdog found) |
| `build-d04-materials-textures.md` | 01:47 | none named | new row |
| `build-d05-entity-graph.md` | 01:41 | `python Tools/scripts/bm_entity.py --check` | new row |
| `build-d06-weapons-tunes.md` | 01:52 | `python Tools/scripts/bm_weapons.py --check` | new row |
| `build-d07-effects.md` | 01:45 | `python Tools/scripts/bm_fx.py --check` | new row |
| `build-d08-health-collision.md` | 01:51 | `python Tools/scripts/t22_reopen.py --check` | new row; also the collision content of §3.6 |
| `build-d09-audio.md` | 01:14 | `python Tools/scripts/b11_rc4_audio.py --check` | new row |
| `build-d10-handling-values.md` | 11:58 | `python Tools/scripts/v05_driving.py --check` | new row |
| `build-d11-rebel-drop-text.md` | 01:42 | `python Tools/scripts/bm_rebel.py --check` | new row |
| `build-d12-variants-modes.md` | 01:54 | `python Tools/scripts/bm_build.py … --tag …/battle --check` | new row; also `B-12`'s precondition 2/4 |
| `build-d13-release-candidate-4.md` | 12:25 | `python Tools/scripts/bm_rc4.py --check` | new row; **`B-14` needs an RC4 sibling** |
| `aafdiff-pursuit-battle.md` | 01:53 | none named | new row (or fold into d12) |

### 4.2 Correction wave `8391…8398` — 8 reports, 0 rows
These exist to correct earlier waves and are the reports most likely to invalidate a row cell.

| report | mtime | check | action |
|---|---|---|---|
| `correction-8391-top-speed-label.md` | 12:11 | `python Tools/scripts/b10_handling.py --check` | new row |
| `correction-8392-unfaithful-textures.md` | 12:43 | none named | new row |
| `correction-8393-donor-audio-guids.md` | 12:56 | `python Tools/scripts/b11_rc4_audio.py --check` | new row; touches `B-11`, `B-26` |
| `correction-8394-light-units-domain.md` | 12:11 | `python Tools/scripts/bm_rc4_lights.py --check` | new row; touches `T-18` |
| `correction-8395-twp4-card-citation.md` | 11:39 | `python Tools/scripts/status_audit.py --check` | new row; touches `T-WP4d` |
| `correction-8396-stale-checkers.md` | 12:11 | `python Tools/scripts/v05_driving.py --check` | new row |
| `correction-8397-module-conflict.md` | 12:25 | `python Tools/scripts/bm_rc4.py --check` | new row |
| `correction-8398-unshipped-cards.md` | 12:14 | **WRITE — do not run**: `status_audit.py --write` then `--check`; gate is `python Tools/scripts/bm_rc4.py --check` | new row; this is the report that re-pins STATUS, so it is also the source for §3.1/§3.3 |

### 4.3 Verify and review wave — 5 reports, 0 rows

| report | mtime | check | action |
|---|---|---|---|
| `verify-v01-file-gates-rc4.md` | 12:27 | `python Tools/scripts/v01_rc4.py --check` | attach to `V-01` (§3.7) |
| `verify-v03-wiring-rc4.md` | 11:52 | none named | attach to `V-03` |
| `verify-v04-audio-rc4.md` | 12:55 | `python Tools/scripts/bm_audio.py --check` | attach to `V-04` (row says `RED`) |
| `review-build-wave.md` | 11:52 | `python Tools/scripts/v05_driving.py --check` (+ `status_audit.py --check`) | new row (review 8399 analogue) |
| `review-translation-wave.md` | 00:45 | `python Tools/scripts/t18_lights.py --check` (+ `t7_weapons.py --check`) | new row |

### 4.4 Translation/apply wave — 4 reports; 2 attach, 2 need rows

| report | mtime | check | action |
|---|---|---|---|
| `apply-keep-audit-fixes-handling.md` | 00:19 | `python Tools/scripts/status_audit.py --check` | attach to `T-26`-family; it is the source of the 15/199 counts in §3.1/§3.3 |
| `apply-keep-audit-fixes-systems.md` | 00:24 | `python Tools/scripts/t_blocked.py --check` (+ `t22_collision.py --check`) | new row (it created `B-25`/`B-26`, whose rows exist but do not cite it) |
| `apply-collision-and-audio-leads.md` | 00:34 | `python Tools/scripts/t22_reopen.py --check` | attach to `Collision-reopen` / `B-10` (§3.6) |
| `translation-closeout-t23.md` | 00:38 | `python Tools/scripts/t23_closeout.py --check` | attach to `T-23` (§3.3) |

### 4.5 The 8770-8781 plan wave — 5 reports on disk, 0 rows (`QUEUE_MAP.md` queued them 2026-11-07)
`QUEUE_MAP.md` last line: "queued 8770-8775 (control scheme, EMP, stuck-flip merge, collision missing
shapes, mode-swap trigger, tracker reconcile) - dependency-free fillers", and 8776-8781 for the HUD
cluster / radar / WP5b / MD14b / T-12 / WP13b. Five of those six have landed; 8776-8781 have not.

| report | mtime | check | action |
|---|---|---|---|
| `control-scheme-closest-system-plan.md` | 17:23 | `python -I Tools/scripts/jc3_input.py --check` (+ `bm_entity.py --check`) | new row (D-11 input plan) |
| `emp-effects-closest-system-plan.md` | 17:26 | `python Tools/scripts/jc3forcepulse.py --check` | attach to `B-18` (§3.5) |
| `stuck-flip-build-plan-merge.md` | 17:29 | none named | new row — `§12` contains **no row whose text matches `stuck` or `flip`** (grep of the 217 rows: 0 hits), so the whole stuck/flipped-recovery thread (`reports/stuck-flip-scrape.md`, `stuck-flip-recovery-plan.md`, this merge) has a ledger lead on WPN-4/WPN-5 and **no tracker row** |
| `collision-missing-shapes-closest-system-plan.md` | 17:32 | none named; its gate is `python Tools/scripts/jc3hkx.py check --all` | attach to `B-10` / `T-22` (§3.6) |
| `mode-swap-trigger-closest-system-plan.md` | 17:36 | `python Tools/scripts/bm_rebel.py --check` | attach to `B-12` (§3.4) |

### 4.6 Tooling wave — 6 reports, 0 rows (queued 7992-7994, 8760, 817x)

| report | mtime | check | action |
|---|---|---|---|
| `bmsdk-upstream-gog-research.md` | 08:53 | none named | new row (7992) |
| `bmsdk-gog-address-hunt.md` | 09:24 | none named | new row (7993) |
| `bmsdk-gog-copy-port.md` | 10:10 | none named | new row (7994) |
| `jeb-choice-format-retest.md` | 11:27 | none named | new row (8760) |
| `app-colour-ramp-locate.md` | 10:39 | none named | attach to `T-21` |
| `app-colour-ramp-textures.md` | 10:38 | none named | attach to `T-21` |

Count check: 14 + 8 + 5 + 4 + 5 + 6 = **42**.

## 5. Operator flip sheet

Order: run the read-only check, read the printed line, then edit the named cell. Nothing here edits a
tracker and nothing here writes a file. **Do not run a `--write` to "confirm" a row** — the four writes
in §4.2/§4.4 regenerate `STATUS.md` and `BLOCKED_PROPOSALS.*`, which is exactly what this pass was told
not to do.

| # | row | run this (read-only) | expect | then change |
|---:|---|---|---|---|
| 1 | `T-BLOCKED` | `python Tools/scripts/t_blocked.py --check` | `PASS: 15 blocked rows re-derived (11 ledger + 4 T6) of 216 in scope` | `17` → `15`, `13 ledger` → `11 ledger`, drop "(re-run 2026-11-06)" |
| 2 | `T-MD-D2-reopen` | same | same PASS line | `18 blocked of 216` → `15`; keep the D-2 decision text |
| 3 | `T-23` | `python Tools/scripts/t23_closeout.py --check` | `gate TX ok … 199 ledger rows` | `51 carried / 9 named omission / 5 blocked` → `58 / 3 / 4`; `198` → `199`; refresh the 7 disposition counts |
| 4 | `V-01 … V-07` | `python Tools/scripts/v01_rc4.py --check` | RC4 file gates green | replace the RC2 placeholder with three RC4 rows or one row citing §4.3 |
| 5 | `B-10` | `python Tools/scripts/t22_reopen.py --check` | `10/10 oracles` | add the 2026-11-07 17:32 plan; restate "0 free hull slots" as not blocking the union route |
| 6 | `T-22` | same | same | add the plan path; keep `REOPENED` |
| 7 | `Collision-reopen` | `python Tools/scripts/t22_reopen.py --check` | same | add `apply-collision-and-audio-leads.md` + the plan to the evidence |
| 8 | `B-12` | `python Tools/scripts/b12_variants.py --check` | still `1 variant`, no `--variant`, 0 trees → card live | add `mode-swap-trigger-closest-system-plan.md` beside `mode-switch-carriers.md §7 U1` |
| 9 | `B-18` | `python Tools/scripts/t_md2_emp_state.py --check` | drift-free | add `emp-effects-closest-system-plan.md` |
| 10 | `B-17` | `python Tools/scripts/effc_writer.py check` | `95/95 carry byte-identical` | nothing (already current) |
| 11 | `T-17` | `python Tools/scripts/t17_fx.py --check` | `PASS: 17 rows (17 chosen, 0 named omissions)` | nothing |
| 12 | `T-24`, `T-25` | `python Tools/scripts/t18_lights.py --check` | PASS, 22 assertions | nothing |
| 13 | `B-22`, `B-23`, `T-S6-bridge` | `python Tools/scripts/t_s6_bridge.py --check` | `14/14` | `T-S6-bridge`'s "17 of 216" line → 15 (same edit as #1) |
| 14 | `B-14` | `python Tools/scripts/bm_rc.py --check` | `PASS: bm-RC1` | not stale on its own terms, but it is the row an operator will read as "the release candidate" — the RC is now RC4 (§4.1) |
| 15 | new rows | — | — | add the rows §4 asks for — see the note under this table |

Note on #15, counted from §4's own tables (every report is either a new row or an attach, and the two
halves sum to the 42 of §4, which is the arithmetic check on this section):

| wave | new rows | attaches |
|---|---:|---:|
| §4.1 RC4 build (14 reports) | 14 | 0 |
| §4.2 correction 8391-8398 (8) | 8 | 0 |
| §4.3 verify + review (5) | 2 | 3 |
| §4.4 translation/apply (4) | 1 | 3 |
| §4.5 the 8770-8781 plans (5) | 2 | 3 |
| §4.6 tooling (6) | 4 | 2 |
| **total** | **31** | **11** |

31 + 11 = 42 = the report count in §1. `aafdiff-pursuit-battle.md` may fold into `build-d12`, which
would make it 30 new + 12 attaches; the attaches are the cheap half and should go first.

## 6. Tracker hygiene found on the way (not staleness, but it hides it)

1. **Status words outside §0.3** (allowed: `todo` · `doing` · `done` · `blocked: <reason>` · `skipped:
   <decision id>`). Rows using something else: `finding` (`STATUS-stale`, `V-04-loops`), `open`
   (`G3-07`, `DECISIONS`), `open: operator` (twice), `partial`, `partial (dead end on disk)`,
   `built, Q pending`, `RED`, `needs fixes`, `refuted in review`, `row wrong`, `root cause found`,
   `reports only (no --check)`, `superseded - see …`, `done (copy)`, `queued (Freebuff)`. A row that is
   `RED` or `finding` cannot be flipped by `t_blocked.py`'s own vocabulary, which is why §5 lists them
   separately.
2. **Two rows give the same pin two different values** (17 vs 18, §3.1/§3.2). They were true four
   hours apart. The tracker has no "as of" column, so the only defence is quoting the check line in
   the cell — which `T-S6-bridge` does and `T-MD-D2-reopen` does not.
3. **Nine rows cite a report whose `--check` is `NONE`** (§3.8). Those cells are prose claims with no
   re-derivation, so "flip after re-running the check" has no meaning for them; they need either a
   script or an explicit "verified by reading, no checker" marker.
4. **The tracker has no row for any 2026-11-07 work.** 42 reports, 0 rows. The 8770-8781 batch was
   queued as filler with no row by design (`QUEUE_MAP.md`), but the RC4 build/correction wave was not,
   and it is the wave that decides whether the row `B-14 = done` still means anything.

## 7. Sources for every claim above (all read, none executed)

- `GRAB_BACKLOG.md` §12 (lines 1809-2050), §0.3 status words (45-51).
- `tmp/freebuff/QUEUE_MAP.md` (the 8770-8781 and 7992-7994 queue notes; 2026-11-07 watchdogs).
- 17 cited reports, mtimes as tabulated; 42 uncited 2026-11-07 reports, mtimes as tabulated.
- `Working/Translation/BLOCKED_PROPOSALS.md` (mtime 2026-11-07 00:32, `15 blocked … of 216`).
- `apply-keep-audit-fixes-handling.md`, `apply-keep-audit-fixes-systems.md`,
  `apply-collision-and-audio-leads.md`, `translation-closeout-t23.md` — the four 11-07 reports that
  print the current pins (`15`, `199`, `145/216`).

No `.py --check` was run, no `--write` was run, no tracker file was modified, no game file was touched.
