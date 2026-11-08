# DONE — T-row evidence audit, resolved rows 91..145

**STATUS: done. `python Tools/scripts/t_row_evidence3.py --check` PASS — 25/25 oracles, exit 0.**
`Working/Translation/T_ROWS.jsonl` was opened read-only and is unchanged
(sha256 `8996b60a5370d932f437fd138d23dc15358d41e24e1026306d7b02172dc0e5f4`); the two earlier
scripts and their two audits were read and hashed, never written.

## Files

| file | bytes | sha256 |
|---|---:|---|
| `Working/Translation/ROW_EVIDENCE_AUDIT3.md` | 31,222 | `30ff7ea8266ad97c913eb7e7ffb5153809fb88974bb766fe6ec7c291cfc8a143` |
| `Tools/scripts/t_row_evidence3.py` | 39,457 | `8e79052906eb6a564ac205497cbff1d31bbd096562f6b4623d2da9471691b9b9` |

No other file was written. No ledger edit, no test was skipped, nothing was launched or attached (§3).

## Result — 55 rows (resolved 91..145)

2 OK, 2 OK (member name), 4 PARTIAL, 1 VALUE-NOT-FOUND, 7 NOT-TESTABLE, 39 NO PATH, **0 DEAD PATH**.
Every path any of the 16 citing rows names exists on disk.

**NO PATH, split honestly.** 39 rows are NO PATH under the inherited text-only reading. Ten of
them do cite something — an `.effc` (9, all T-13) or `settings/spawn_vehicle_defs.bin` (1) — which a
text resolver cannot open; 29 name nothing at all.

**Grouped by document (slice of 55):**

| doc | rows | NO PATH | only an artefact | names nothing | names-nothing share |
|---|---:|---:|---:|---:|---:|
| T-3 | 1 | 0 | 0 | 0 | 0% |
| T-13 | 13 | 13 | 9 | 4 | 31% |
| T-14 | 14 | 8 | 0 | 8 | 57% |
| T-7 | 7 | 1 | 0 | 1 | 14% |
| T-20 | 11 | 10 | 1 | 9 | 82% |
| T-15 | 9 | 7 | 0 | 7 | 78% |

* **By the letter of the rule (text or binary): T-13**, 13 of 13 audited rows (100%).
* **Counting only rows that name nothing: T-20 is the worst**, 9 of 11 (82%), then T-15 7/9 (78%),
  T-14 8/14 (57%), T-13 4/13 (31%), T-7 1/7 (14%), T-3 0/1.
* Context over all 145 resolved rows (derived, not this slice's finding): T-1 22/43 has the largest
  absolute count; T-13 has the largest share (100%); T-2b 21/35, T-20 10/11, T-15 7/9, T-14 8/14,
  T-3 4/13, T-7 1/7.

**Three corrections the slice forced, all recorded in the document:**

1. **Value column per document, not `cells[4]`.** The first two audits read the value from
   `cells[4]` unconditionally. Here it is right for T-7, T-20 and T-14, but wrong for T-3 and T-13
   (index 4 is `now`) and T-15 (index 4 is `JC3 carrier`; the value is 3). The audit now reads the
   column from the table header the row sits under in its own document; 4 rows change status under
   the old fixed-column reading (T-L28, T-L30, T-WP6, T-MD6).
2. **`.jsonl` was being truncated to `.json`.** The inherited pattern lists `json` before `jsonl`,
   so `T-MD4`'s `objects.jsonl` read as `objects.json` and would have been reported a dead path.
   With the longer suffix first it resolves to `Research/BatmobileGrab/objects.jsonl` and
   `T-MD4` is **OK** — all 14 quoted numbers found. This slice has no dead path.
3. **Colour quadruples are not a value test.** `norm()` strips commas, so `255,255,255,0` becomes
   the token `2552552550`, which no file contains. Four rows quote one (T-L10, T-L21, T-L22,
   T-L23); the single VALUE-NOT-FOUND and 3 of the 4 PARTIALs are this artefact, not absent data.
   The one genuine PARTIAL is `T-MD6` (`TurningModeMaxSpeed` 600 cm/s = 21.6 km/h; 21.6 is not in
   `Research/JC3Grab/VOCABULARY.md`).

## Commands (verbatim)

```
$ python Tools/scripts/t_row_evidence3.py --write; echo "write_exit=$?"
PASS ledger holds 198 rows (198)
PASS 145 rows are resolved under the stated rule (keep/edit/epe/out/superseded; next and blocked excluded)
PASS resolved rows 91..145 selected (55)
PASS every audited row is resolved
PASS no audited id appears among rows 1..90
PASS T_ROWS.jsonl sha256 equals the one the first audit recorded (8996b60a5370d932...)
PASS every audited row was found under a table header in its own document
PASS every row's header has the same column count as the row
PASS the two earlier scripts and their two audits all exist (read, never written)
PASS every selected row has an audit line (55)
PASS statuses sum to 55
PASS no OK row has a quoted number absent
PASS every PARTIAL row names at least one absent number
PASS every non-dead citation opened a real file
PASS 0 same-name path(s) left ambiguous, each with its candidate count
PASS 0 same-name path(s) resolved by content, candidates recorded
PASS every audited row quotes a number/member, names no file, or is not testable
PASS every value column index lies inside its own table header
PASS every row's colour-quadruple flag matches its own value cell
PASS the per-document groups cover every audited row
PASS the per-document NO PATH counts sum to the NO PATH total
PASS the artefact/nothing split sums to the NO PATH total
PASS no NO PATH row also resolved a text citation
PASS every NO PATH note naming an artefact has one recorded
PASS all 8 documents of the ledger appear in the context table (8)
25/25 oracles pass
statuses: NO PATH 39, NOT-TESTABLE 7, OK 2, OK (member name) 2, PARTIAL 4, VALUE-NOT-FOUND 1
no-path by doc: T-3 0/1, T-13 13/13, T-14 8/14, T-7 1/7, T-20 10/11, T-15 7/9
worst by count T-13 (13), worst by share T-13 (100%)
wrote Working/Translation/ROW_EVIDENCE_AUDIT3.md
write_exit=0

$ python Tools/scripts/t_row_evidence3.py --check; echo "check_exit=$?"
... (same 25 PASS lines) ...
25/25 oracles pass
statuses: NO PATH 39, NOT-TESTABLE 7, OK 2, OK (member name) 2, PARTIAL 4, VALUE-NOT-FOUND 1
no-path by doc: T-3 0/1, T-13 13/13, T-14 8/14, T-7 1/7, T-20 10/11, T-15 7/9
worst by count T-13 (13), worst by share T-13 (100%)
PASS document: ROW_EVIDENCE_AUDIT3.md matches the regenerated text
check_exit=0

$ sha256sum Tools/scripts/t_row_evidence3.py Working/Translation/ROW_EVIDENCE_AUDIT3.md Working/Translation/T_ROWS.jsonl
8e79052906eb6a564ac205497cbff1d31bbd096562f6b4623d2da9471691b9b9 *Tools/scripts/t_row_evidence3.py
30ff7ea8266ad97c913eb7e7ffb5153809fb88974bb766fe6ec7c291cfc8a143 *Working/Translation/ROW_EVIDENCE_AUDIT3.md
8996b60a5370d932f437fd138d23dc15358d41e24e1026306d7b02172dc0e5f4 *Working/Translation/T_ROWS.jsonl

$ find . -name "objects.jsonl" -not -path "./.git/*"
./Research/BatmobileGrab/objects.jsonl
```

## UNKNOWNs

1. **A field holding a different number.** The ledger names no field/key, so "the file disagrees"
   cannot be proven — only that a quoted value is or is not present.
2. **Why a document's rows cite nothing.** The grouping counts the ledger's own claim; it cannot
   tell an omitted citation from an uncitable row (T-14's `out` rows and T-20's world rows are the
   bulk of the 29).
3. **Whether an `.effc`-only citation is adequate evidence.** T-13's nine rows name a real effect
   package path, but neither the package nor its contents were opened here.
4. **Colour equality.** Components are never compared (the quadruple is concatenated), so no row's
   colour is confirmed or refuted by this audit; that is `v_lights_rc2.py`'s and T-18's ground.
5. **Whether 21.6 is expressed elsewhere** for `T-MD6` — only `VOCABULARY.md` was searched for it.
6. **Rows 1..90** were not re-run; their published verdicts stand as they are, including whatever
   the `cells[4]` and `.json`/`.jsonl` artefacts did to them.
