STATUS: done - `Working/Translation/ROW_EVIDENCE_AUDIT.md` and `Tools/scripts/t_row_evidence.py` exist; the audit covers the first 40 resolved rows (of 145) in file order; `--check` passes 12/12 oracles and the document is byte-identical to the regenerated text. `T_ROWS.jsonl` was opened read-only and its sha256 is recorded in the output. No dead path; 21 of the 40 rows cite no file at all, 6 cite a file that does not carry the quoted value, 1 is partial.

# T-row evidence audit - first 40 resolved rows

## What the card asked, and the reading it needed

`Working/Translation/T_ROWS.jsonl` has no `evidence` field. Its rows are
`{id, doc, section, cells[8], dispo, why, edits}`, and the evidence is spread across the cells: the
source member is `cells[2]`, the value is `cells[4]`, the verify text is `cells[-1]`. So "the
evidence path named in the row" is read as **the file the row names anywhere in its cells or
`why`**, and "resolved" as **a settled disposition** (`keep`, `edit`, `epe`, `out`, `superseded` =
145 rows) - `next` (40, still queued) and `blocked` (13, no outcome yet) are not resolved. Both
readings are printed in the output so the operator can overrule them.

Test per row: every named `.md/.json/.jsonl/.py/.csv/.txt` path is resolved (directly, by unique
basename, or by content when a basename occurs more than once); the numbers quoted in `cells[4]` are
then compared **by value** against the file in three grades - exact, rounded at the quoted precision
(`2.4589` for a quoted `2.459`), absent - and, when a row quotes no number, the backticked member
names from `cells[2]` are compared as substrings. Numbers under 3 digits are weak and used only when
a row has no strong number.

## Result

40 audited: **9 fully found** (7 exact, 1 by rounding, 1 on a member name), **1 partial**,
**6 with no quoted value in the file**, **0 dead paths**, **21 citing no file**, **3 not testable**.

* **No evidence path (21 rows).** `T-G2`, `T-G3`, `T-G4`, `T-G5`, `T-S2`, `T-S4`, `T-R2`, `T-R3`,
  `T-ST1`, `T-ST2`, `T-ST3`, `T-E1`, `T-E3`, `T-E4`, `T-E5`, `T-B1`, `T-A3`, `T-A4`, `T-L1`,
  `T-L2`, `T-L6`. These rows carry a decoded value and a member path, no citation - so nothing can
  be re-tested from the ledger alone. This is the dominant finding and the reason the report is
  named `t-rows-no-evidence.md`.
* **Value absent from the cited file (6).** `T-M1` quotes `4,000 kg` but `CHAIN.json` and
  `T3_FLEET.md` carry no 4000 (CHAIN.json does carry 6000). `T-E2` quotes `1393.5`, absent from
  `FITS.md`. `T-A1` quotes `6.63`, absent from both `T3_FLEET.md` and `FITS.md`. `T-B4` quotes the
  patterns `arcade.heat_boost.*` / `turbo_jump*`, absent from `VOCABULARY.md` - **expected**, those
  are absence claims, see the caveat below. `T-L3` and `T-L5` cite `Tools/scripts/t2_lg2.py` and
  quote `Rear_Break` / `Front_Secondary_Head`, which the script does not contain.
* **Partial (1).** `T-M2` quotes `1.8 / 1.5 / 0.5`; `CHAIN.json` accounts for 1.5 and 0.5, and for
  1.8 only at no precision - 2 of 3 found.
* **Same-name citation (1).** `T-G1` cites `stations.json`; **7** files carry that name. Content
  resolved it to `Working/TrueScale/stations.json` (3 of the 5 quoted values exact, the other 2 by
  rounding: `-2.570` -> `-2.57`, `2.459` -> `2.4589`, `1.285` -> `1.2845`). The other six carry
  only 1.208 / 0.7047, so the pick is evidence-based, not alphabetical.
* **Dead paths: none.** Every path cited by the 19 rows that cite something exists on disk.

## Files written

| file | lines | sha256 |
|---|---|---|
| `Tools/scripts/t_row_evidence.py` | 441 | `7770690223c3faf4daa118ac1a261068f16020cc5360918d62bb4e96270d98dd` |
| `Working/Translation/ROW_EVIDENCE_AUDIT.md` | 153 | `c4b42c560bb224dc7e1b96bfabb961cf875adc3387ccf94f1a0af7ea7b46d1a4` |
| `tmp/freebuff/reports/t-rows-no-evidence.md` | this report | - |

`Working/Translation/T_ROWS.jsonl` was **not** edited: sha256
`8996b60a5370d932f437fd138d23dc15358d41e24e1026306d7b02172dc0e5f4`, and `--check` re-asserts that
hash so a later edit to the ledger turns the check red instead of leaving the audit stale. No other
task's file was touched; no build, archive, game install or process was opened (the test ban stays).

## Commands and verbatim output

```
$ PYTHONIOENCODING=utf-8 python Tools/scripts/t_row_evidence.py --write
PASS ledger holds 198 rows (198)
PASS 145 rows are resolved under the stated rule (keep/edit/epe/out/superseded; next and blocked excluded)
PASS first 40 resolved rows selected (40)
PASS every selected row has an audit line
PASS statuses sum to 40
PASS no OK row has a quoted number absent
PASS every PARTIAL row names at least one absent number
PASS every non-dead citation opened a real file
PASS 0 same-name path(s) left ambiguous, each with its candidate count
PASS 1 same-name path(s) resolved by content, candidates recorded
PASS every audited row quotes a number/member, names no file, or is not testable
PASS ledger sha256 8996b60a5370d932...
12/12 oracles pass
statuses: NO PATH 21, NOT-TESTABLE 3, OK 7, OK (member name) 1, OK (rounded) 1, PARTIAL 1, VALUE-NOT-FOUND 6
wrote Working/Translation/ROW_EVIDENCE_AUDIT.md
```

```
$ PYTHONIOENCODING=utf-8 python Tools/scripts/t_row_evidence.py --check
check_exit=0
12/12 oracles pass
statuses: NO PATH 21, NOT-TESTABLE 3, OK 7, OK (member name) 1, OK (rounded) 1, PARTIAL 1, VALUE-NOT-FOUND 6
PASS document: ROW_EVIDENCE_AUDIT.md matches the regenerated text
```

```
$ sha256sum Tools/scripts/t_row_evidence.py Working/Translation/ROW_EVIDENCE_AUDIT.md
7770690223c3faf4daa118ac1a261068f16020cc5360918d62bb4e96270d98dd *Tools/scripts/t_row_evidence.py
c4b42c560bb224dc7e1b96bfabb961cf875adc3387ccf94f1a0af7ea7b46d1a4 *Working/Translation/ROW_EVIDENCE_AUDIT.md
```

Corrections made during the run, kept for honesty (the data did not change; my tests were wrong):

1. first matcher: the number regex was `[-]\d+`, requiring a literal hyphen, so almost every value
   fell to "weak"; fixed to `-?\d+`.
2. second: rows could be "OK (partial) - 0 of 1 found", a contradiction; the status ladder now has a
   separate PARTIAL and a VALUE-NOT-FOUND branch, and an oracle asserts no OK row has an absent
   number.
3. third: disambiguating `stations.json` by total matches made all seven files tie (rounded matches
   are cheap); scoring now counts exact matches first, which picks `Working/TrueScale` on 3 exact
   values.
4. `T-B4` is quoted in the "value absent" list with its caveat: its strings are patterns the row
   asserts are absent, so absence agrees with the row.

## UNKNOWNs

* **A field holding a different number.** Proving `CHAIN.json` or `VOCABULARY.md` disagrees needs
  the field's row/key, which the ledger does not name. The audit proves presence (by value, with a
  rounding grade), never that the file still means what the row says - the six "absent" rows above
  are the only disagreement it can prove, and even those could be quoted from a decode step rather
  than from the cited file.
* **`T-L3` / `T-L5`** cite a **script**, not its output; a script need not contain the row names it
  compares, so their "not found" is a citation weakness of the row, not proof the value is wrong.
  What would close it: the script's generated JSON, named in the row.
* **Rows 41..145 of the resolved set** are out of scope by the card; `next` (40) and `blocked`
  (13) are excluded by the resolved rule and were not audited at all.
* **Whether the cited decode is still what the build ships** - that is `t_rows.py check` and the
  per-card `--check` scripts, not this audit.

## Labels

Decoded: the ledger rows, the cited files' contents, every resolved path. Derived: the statuses,
the found/absent counts, the rounding comparison, the content-disambiguation scores (3 exact for
`Working/TrueScale/stations.json` against 1 for the other six). UNKNOWN: the four items above.
Nothing was filled in from general knowledge, and no value was repaired - the rows are the other
tasks' files.
