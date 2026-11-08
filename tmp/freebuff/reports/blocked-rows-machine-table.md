# Blocked rows, machine table

Source list: `tmp/freebuff/reports/7210-t-blocked-rows.md` (prose, 17 rows). Cross-checked against
`Working/Translation/BLOCKED_PROPOSALS.json` and `Working/Translation/DECISIONS_NEEDED.md`.

**SUMMARY: 17 named, 12 kept, 5 dropped.** `DECISIONS_NEEDED.md` names all 17 rows; the JSON names
only 12 of them. The kept set is the intersection, and it is written to
`Working/Prep/blocked_rows.json` — one object per row with `row_id`, `blocker_text`,
`blocker_source_path`, `blocker_source_line`, `proposal_status`, `decision_needed` (plus
`blocker_source_span`, `proposal_source_line`, `decision_state` so a consumer can act on the ruling
without re-reading prose).

Nothing here was edited: the report, `BLOCKED_PROPOSALS.json` and `DECISIONS_NEEDED.md` are unchanged.

## 1. How the 12 were chosen

| step | result |
|---|---|
| rows named in the report's "The 17, one line each" table (parsed, not hand-copied) | **17** |
| ids present in `BLOCKED_PROPOSALS.json` (`rows` 15 + `resolved` 7 = 22 ids, `attempted` empty) | 22 ids, of which **12** are in the report |
| ids marked as `T-…` in `DECISIONS_NEEDED.md` | **17** — all of the report's rows |
| intersection of both source files | **12** |
| dropped: in the report and in `DECISIONS_NEEDED.md`, **absent** from the JSON | **5** |

The drop is not a judgement about the rows: `T-WP5`, `T-WLD4`, `T-WLD6`, `T-WLD11` and `T-MD2` are
named by the report and by `DECISIONS_NEEDED.md` (lines 180, 15, 16, 16 and 181), but
`BLOCKED_PROPOSALS.json` contains no entry for any of them — `rows` lists `T-MD5…T-MD8`, `T-MD13`,
`T-MD14` but no `T-MD2`, and the three `T-WLD` ids were closed in the ledger on 2026-11-06 (see the
exception paragraph at `DECISIONS_NEEDED.md:17-20`). They are recorded under `dropped` in the JSON
with that reason rather than silently omitted.

**No row needed `blocker_source_path: UNKNOWN`** — every kept row's blocker is written verbatim in one
of the two source files, so the UNKNOWN branch of the brief is empty. The file that *would* have to
name a dropped row's blocker is `Working/Translation/BLOCKED_PROPOSALS.json` (its `rows` or
`resolved` array), which is the only one of the two that omits them.

## 2. The 12 rows

| row_id | blocker_source_path:line | proposal_status | decision_needed |
|---|---|---|---:|
| `T-AU3` | `DECISIONS_NEEDED.md:177` | resolved-by-evidence | false |
| `T-FX3` | `DECISIONS_NEEDED.md:83-84` | resolved-by-operator-approval | true |
| `T-S6` | `DECISIONS_NEEDED.md:179` | resolved-by-derived-bridge | false |
| `T-ST7` | `DECISIONS_NEEDED.md:37-38` | resolved-by-operator-ruling | true |
| `T-AU5` | `DECISIONS_NEEDED.md:178` | resolved-by-evidence | false |
| `T-WP4` | `DECISIONS_NEEDED.md:150-151` | resolved-by-operator-ruling-and-donor | true |
| `T-WP13` | `DECISIONS_NEEDED.md:118-119` | resolved-by-operator-ruling | true |
| `T-MD14` | `BLOCKED_PROPOSALS.json:115` | blocked-listed | false |
| `T-HUD5` | `BLOCKED_PROPOSALS.json:122` | blocked-listed | false |
| `T-CAM8` | `BLOCKED_PROPOSALS.json:129` | blocked-listed | false |
| `T-CAM9` | `BLOCKED_PROPOSALS.json:136` | blocked-listed | false |
| `T-CAM11` | `BLOCKED_PROPOSALS.json:143` | blocked-listed | false |

`proposal_status` is the JSON's own `verdict` where the row is in its `resolved` array
(`BLOCKED_PROPOSALS.json:151, 175, 199, 223, 247, 271, 295`); for the five rows that sit in its
`rows` array the entry carries `"attempt": null` and no verdict, recorded here as `blocked-listed`.

## 3. What `decision_needed` means here

It records **membership of `DECISIONS_NEEDED.md`'s decision list**, not whether the choice is still
open. The four `true` rows are the file's numbered items (`DECISIONS_NEEDED.md:24-27`):

```
| 1 | `T-ST7` | T-3 steering | choose 0.25 s (BmAK's value) or keep 0.8 / 0.6 s |
| 2 | `T-FX3` | T-2b effects | approve the decoded afterburner-flame edit, or keep the omission |
| 3 | `T-WP13` | T-7 weapons | accept JC3's 2 driver slots, or leave the row blocked |
| 4 | `T-WP4` | T-7 weapons | approve splitting it so the missile launcher can ship |
```

All four were answered in the same file’s `## OPERATOR RULINGS 2026-11-06` block, which is why their
`proposal_status` is a `resolved-by-…` verdict; `decision_state` carries `ruled-2026-11-06` for them so
a build step does not read "on the decision list" as "still waiting". The eight `false` rows are the
file's evidence-only list, whose own heading states the distinction (`DECISIONS_NEEDED.md:171-173`):

```
Listed so the distinction is explicit: **there is nothing for you to choose here** - each needs a
file that does not exist yet, or a decode that has not been done. They are not on this sheet's
decision list.
```

## 4. Quotes the table relies on

- `T-ST7` — `DECISIONS_NEEDED.md:37-38`: "`**blocked**: 55° lock at 220 °/s is 0.25 s, and the fleet's
  fastest rack is 0.5 s; JC3's steering model cannot be that quick, so the table keeps 0.8 s inside the
  family`".
- `T-FX3` — `DECISIONS_NEEDED.md:83-84`: "it ships no exhaust/boost flame, on the stated ground that
  JC3 has no carrier for one."
- `T-WP13` — `DECISIONS_NEEDED.md:118-119`: "D-7 asks for **every weapon in both modes**. JC3 has
  **at most 2 driver weapon slots** and no way to switch between more."
- `T-WP4` — `DECISIONS_NEEDED.md:150-151`: "the disable half has no member on either side - \"no
  EMP-named member exists on any NPC `RVehicle*` class\"".
- `T-AU3` / `T-AU5` / `T-S6` — the section-5 cells at lines 177-179; `T-MD14`, `T-HUD5`, `T-CAM8`,
  `T-CAM9`, `T-CAM11` — the `waits_for` strings at `BLOCKED_PROPOSALS.json:115, 122, 129, 136, 143`.
  The full verbatim text of each is the `blocker_text` value in `Working/Prep/blocked_rows.json`.

## 5. Checks

- `Working/Prep/blocked_rows.json` parses; 12 objects, each with all six required fields, ids unique
  and equal to the computed intersection (scripted set comparison against both source files).
- `decision_needed` is `true` on exactly the 4 ids in `DECISIONS_NEEDED.md:24-27`; the other 8 are
  `false`.
- No `blocker_source_path` is `UNKNOWN`; every path is one of the two source files and every line
  number was read back and matched to the quoted text by the check script.
- The report and both source files were opened read-only; no write touched them.

## 6. Revert

Delete `Working/Prep/blocked_rows.json` and this report. Nothing else changed.

## 7. Limitation

The two source files disagree with the older report about the set's size: the report says 13 ledger +
4 T6 = 17 blocked of 180 in scope, while the current `BLOCKED_PROPOSALS.json` stores 11 + 4 = 15 of
216 (`counts`, after regenerating over the 199-row ledger). That drift is why five of the report's
rows are absent from the JSON; it is reported, not resolved, here — reconciling the counts is outside
this lookup.
