**STATUS: DONE — 35 rows re-run fresh, 2 HOLD, 0 WRONG VALUE, 33 STILL OPEN.** All seven cited producers exited 0; `g3_20e_rows.py --check` passes 7/7 oracles and the page is byte-identical on re-run.

# G3-20b open rows: the 35 second-half re-derivable rows, re-run fresh

## Scope and selection

`Research/BatmobileGrab/LEDGER_G3B.md` reports 96 of 105 rows OPEN. `Working/Translation/LEDGER_SOURCES.md` §2 marks 69 of those 96 re-derivable (`grabbed` 41 + `grabbed + derived` 28) and 27 not. Sorted by row id and halved, the second half is 35 rows:

`T-FX5 T-FX7 T-FX8 T-FX9 T-K1 T-K2 T-K3 T-M2 T-M3 T-MA2 T-MA5 T-MA6 T-MA7 T-P1 T-P2 T-P3 T-PA1 T-PA2 T-PA4 T-PA5 T-PA7 T-PA8 T-R1 T-R2 T-R3 T-S1 T-S2 T-S3 T-S4 T-S5 T-ST1 T-ST2 T-ST3 T-ST4 T-ST6`

No stored ledger JSON was read. `T_ROWS.jsonl` supplied only the row text; the value every row is graded against is the row's own claim in `LEDGER_SOURCES.md` §2.

## Files written

| file | what |
|---|---|
| `Tools/scripts/g3_20e_rows.py` | selector + fresh producer runner + grader; `--write` / `--check` |
| `Research/BatmobileGrab/LEDGER_G3E.md` | the 35-row verdict page (125 lines) |
| `tmp/freebuff/reports/g3-20b-open-rows.md` | this report |

`tmp/freebuff/scratch/g3e_values.json` and `tmp/freebuff/scratch/g3e_fits.md` are by-products of running `grab_values.py` and `t1_fits.py`; the ledgers and producer artefacts were not touched.

## Verdicts

| verdict | rows |
|---|---:|
| HOLDS | 2 |
| WRONG VALUE | 0 |
| STILL OPEN | 33 |
| **total** | **35** |

### The two that HOLD

- **T-P2** — `ok: donor table has 42 parts, names 42/42 with DeformPoints, lights 12 parts match, wheels 4 match, damage types 17 used` (`jc3parts.py check`). The claim is "17 damage types across the donor's 42 parts"; one printed line carries both 42 and 17 for those quantities.
- **T-PA2** — `ok: 40 part indices agree between .epe and DeformPoints; 4 wheel points -> 4 wheel parts; 21 light points -> 12 parts` (`jc3parts.py check`). The claim is "21 light points → 12 parts"; exact.

### Why 33 are STILL OPEN

The grader marks HOLDS only when a printed line *states the row's own quantity* and carries its number. A coincident count does not count: T-PA7's claim of "20 parts skipped by the deform solver" finds the number 20 in `non_deformable_parts_indices: 20 deform points -> 20 parts`, a different quantity, so it stays open. Same for, e.g., T-MA6's "28" and T-K1's "10,000 / 10,000", whose cited `bmak_chain.py --check` prints `105 objects, 9225 named bindings, 336 cross-checked, 0 conflicts` and no line about the row's value.

This is the pass's finding about the source ledger, not about the rows: **the seven producers validate and print their own check counts, they do not print the per-row values.** So "re-derivable" in `LEDGER_SOURCES.md` means *the artefact the row rests on has a green producer*, and a green producer does not by itself re-print the value. Reading a value out of the stored artefact would be a second step, and the brief excluded stored JSON.

No row is marked WRONG VALUE: no fresh run printed a contradicting number for the same quantity.

## Verbatim commands

```
python Tools/scripts/bmak_chain.py --check
python Tools/scripts/grab_values.py --out tmp/freebuff/scratch/g3e_values.json
python Tools/scripts/jc3grab.py check
python Tools/scripts/jc3parts.py check
python Tools/scripts/jc3parts.py wiring
python Tools/scripts/jc3fx.py report
python Tools/scripts/t3_fleet.py --check
python Tools/scripts/t1_fits.py -o tmp/freebuff/scratch/g3e_fits.md
```

Observed last lines (exit 0 each):

```
PASS: chain record current (105 objects, 9225 named bindings, 336 cross-checked, 0 conflicts, 0 bool words left unnamed)
{ ... }                                   # grab_values.py JSON dump, 1 root level
check ok                                  # jc3grab.py check
ok: donor table has 42 parts, names 42/42 with DeformPoints, lights 12 parts match, wheels 4 match, damage types 17 used   # jc3parts.py check (via its ok line)
parts: 42 (index -> name, from DeformPoints) / wheel_indices: 4 ... / light_indices: 21 ... / constraint_indices: 11 ...   # jc3parts.py wiring
FX.md: 57187 files, 62,504,473 rows, 0 failures
check ok                                  # t3_fleet.py --check
FITS.md: 156 land vehicles, 19 members fitted, 5 usable (R2 >= 0.5) -> tmp/freebuff/scratch/g3e_fits.md
```

```
python Tools/scripts/g3_20e_rows.py --write
# wrote Research/BatmobileGrab/LEDGER_G3E.md: 35 rows, {'still open': 33, 'holds': 2}
python Tools/scripts/g3_20e_rows.py --check
# ok: 35 rows ({'still open': 33, 'holds': 2}); all producers green; page matches
```

## Oracles (`--check`, 7/7 PASS)

`selected_35_second_half`, `all_selected_are_re_derivable`, `ids_are_sorted_and_are_the_upper_half`, `every_row_has_a_verdict`, `every_row_has_evidence`, `every_cited_producer_ran`, `no_stored_ledger_json_read`.

## UNKNOWNs

- **Whether a STILL OPEN row's value is right.** Proved only that the fresh producer does not print it. Answering it needs a producer mode that prints the per-member value; none of the seven has one.
- **The 34 first-half rows.** Someone else's half; not run or graded.
- **`jc3fx.py check`** (the FX artefact's own currency, ~450 s) was not run; `jc3fx.py report` was used as the FX producer and prints only the total, so all four FX rows stay open regardless.

## Revert

Delete the three files listed above and both `tmp/freebuff/scratch/g3e_*` by-products. No ledger, producer artefact or `T_ROWS.jsonl` was modified.
