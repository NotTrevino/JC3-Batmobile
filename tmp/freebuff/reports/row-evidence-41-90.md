STATUS: DONE — resolved rows 41..90 audited with the first audit's method and status vocabulary; `--check` green (15/15).

## Files

| file | what it is |
|---|---|
| `Tools/scripts/t_row_evidence2.py` | new script: `--write` / `--check`, slice 2 only (reads the ledger; never writes it) |
| `Working/Translation/ROW_EVIDENCE_AUDIT2.md` | new audit, 197 lines, byte-compared by `--check` |
| `tmp/freebuff/reports/row-evidence-41-90.md` | this report |

Not touched: `Tools/scripts/t_row_evidence.py`, `Working/Translation/T_ROWS.jsonl`
(sha256 `8996b60a5370d932f437fd138d23dc15358d41e24e1026306d7b02172dc0e5f4`, the value the first
audit recorded, re-asserted by this script), `Working/Translation/ROW_EVIDENCE_AUDIT.md`.

## Verbatim commands

```
cd "E:/Modding/JustCause3/JC3-Batmobile" && PYTHONIOENCODING=utf-8 python Tools/scripts/t_row_evidence2.py --write
cd "E:/Modding/JustCause3/JC3-Batmobile" && PYTHONIOENCODING=utf-8 python Tools/scripts/t_row_evidence2.py --check
```

`--write` -> exit 0; `--check` -> exit 0, "PASS document: ROW_EVIDENCE_AUDIT2.md matches the
regenerated text".

## Result

50 rows audited (resolved 41..90 of 145; the ledger holds 198 rows, 145 resolved by
keep/edit/epe/out/superseded):

* **OK 7**, **OK (member name) 2**, **PARTIAL 2**, **VALUE-NOT-FOUND 2**, **DEAD PATH 2**,
  **NO PATH 26**, **NOT-TESTABLE 9**.

Every row with VALUE-NOT-FOUND or NO PATH, by id (also listed in their own sections of the audit):

* VALUE-NOT-FOUND: `T-MA1` (cited `Tools/scripts/verify_install.py`, none of `200` in it),
  `T-MA2` (cited `Research/BatmobileGrab/SLOTS.json`, none of `28` in it).
* NO PATH (26): `T-P1`, `T-MA4`, `T-MA6`, `T-MA7`, `T-PA4`, `T-PA5`, `T-PA6`, `T-PA7`, `T-LG1`,
  `T-LG3`, `T-LG6`, `T-AU1`, `T-AU2`, `T-AU4`, `T-FX1`, `T-FX2`, `T-FX5`, `T-DM2`, `T-DM3`,
  `T-DM4`, `T-DM5`, `T-DM6`, `T-G6`, `T-K4`, `T-EF1`, `T-FX6`.
* PARTIAL: `T-PA1` (cited `Tools/scripts/t2_lg2.py`, absent `6`, `4`), `T-PA2` (cited
  `Tools/scripts/jc3parts.py`, absent `12`).
* DEAD PATH: `T-P2` and `T-PA3`, both citing `PARTS_TABLE.json`.

## The one finding that changes how the two dead paths read (derived, from decoded files)

Both rows actually cite `PARTS_TABLE.jsonl`. The shared path regex lists `json` before `jsonl`, so
it captures `PARTS_TABLE.json`, which does not exist -> DEAD PATH. Re-tried with one more `l`, the
real file is `Research/JC3Grab/PARTS_TABLE.jsonl` (and `Research/JC3Grab/PARTS_TABLE.md`), and the
rows' quoted tokens are present in the `.jsonl` (`T-P2`: 17, 42; `T-PA3`: 0, 1, 7, -1). The
statuses are **left as DEAD PATH** so this slice stays comparable with the first audit; the
caveat and the re-test are written into the audit's "Dead paths" section. The first audit's
`--check` still passes, so nothing there was disturbed.

## UNKNOWNs

* Whether a cited file's same **field** now holds a different number: the ledger names no row/key,
  so this audit proves presence by value, not agreement. UNKNOWN.
* Whether `T-MA1`'s `200` and `T-MA2`'s `28` are wrong values or values that live in a different
  file than the one cited: UNKNOWN. `T-MA1` quotes a count of material blocks over 35 meshes and
  cites the install verifier, which is not the table that would hold it.
* Whether `T-PA1`/`T-PA2`'s absent tokens are wrong, or are compared in a script that computes
  them rather than containing them: UNKNOWN (a script citation is not its output).
* Resolved rows 1..40 and 91..145: out of scope here (1..40 in `ROW_EVIDENCE_AUDIT.md`).
* No game was launched, no test run, no build tree written; the test ban was kept.

## Labels

Decoded: the ledger rows, the referenced file contents, the resolved file paths, the sha256s.
Derived: the statuses, the counts, the rounding comparisons, the `.json`/`.jsonl` truncation
diagnosis. UNKNOWN: everything listed above.
