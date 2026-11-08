STATUS: DONE — all six VALUE-NOT-FOUND rows explained, classified, and given a proposed corrected row (not applied); `--check` green (78/78, exit 0).

## Files

| file | what |
|---|---|
| `Working/Translation/VALUE_NOT_FOUND_SIX.md` | 404 lines: per-row evidence, classification, proposed row as JSON |
| `Tools/scripts/t_vnf_six.py` | new script, `--write` / `--check`; imports `t_row_evidence.py` so the grading is the first audit's own |
| `tmp/freebuff/reports/value-not-found-six.md` | this report |

Not touched: `Working/Translation/T_ROWS.jsonl` (sha256 `8996b60a…e5f4` before and after),
`Tools/scripts/t_row_evidence.py`, `Working/Translation/ROW_EVIDENCE_AUDIT.md`.

## Verbatim commands

```
cd "E:/Modding/JustCause3/JC3-Batmobile" && PYTHONIOENCODING=utf-8 python Tools/scripts/t_vnf_six.py --write
cd "E:/Modding/JustCause3/JC3-Batmobile" && PYTHONIOENCODING=utf-8 python Tools/scripts/t_vnf_six.py --check
```

`--write` -> exit 0, "78/78 oracles pass", wrote the doc. `--check` -> exit 0, doc byte-identical,
ledger sha unchanged after the run.

## Classification (5 wrong citation, 0 wrong value, 1 unit/format)

| row | quotes | cited | nearest value the file holds | verdict |
|---|---|---|---|---|
| `T-M1` | **4,000 kg** | `CHAIN.json`, `T3_FLEET.md` | `rigid body mass` 3–8 t: 3500 (p25) / 5100 (median) / 6000 (p75) | **wrong citation** — 4000 is `FITS.md` line 8: "the fit evaluated at **4000 kg** (the built Batmobile's mass)" |
| `T-E2` | 1393.5 | `FITS.md` | `torque at optimal rpm`: 834.1 at 4 t; 1100 for 6–15 t; 2500 for 15 t+ | **wrong citation** — 1393.5 is the decoded build value (`current.json` 1393.52454; module 1393.5245361328125). Secondary: the row's base "1,121" is in neither form (`1,121`/`1121` = 0 occurrences); ×1.27 fits 1,100, ×1.24 fits only the missing 1,121 |
| `T-B4` | `arcade.heat_boost.*`, `turbo_jump*` | `VOCABULARY.md` | the ten expanded members, donor column 0 / 80 / 1.5 / 2 | **unit/format difference** — a glob is never a substring; both patterns are 0-occurrence literals, the members are all present |
| `T-A1` | 6.63 | `T3_FLEET.md`, `FITS.md` | `aero frontal area` 3–8 t: 6.5 median, 6.72 p75; 6 t+: 6.95 | **wrong citation** — 6.63 is the decoded `frontal_area` 6.634666919708252 (`LEDGER_AUDIT.json`, `current.json`) |
| `T-L3` | `Rear_Break` | `t2_lg2.py` | the script contains no graph name; it prints `graph_objects_unused` | **wrong citation** — the name is in the donor `.epe` dump: `..._debug.epe@0x2CF9: 'Rear_Break'` (`LEDGER_AUDIT.json`) |
| `T-L5` | `Front_Secondary_Head` | `t2_lg2.py` | same | **wrong citation** — `..._debug.epe@0x4F28: 'Front_Secondary_Head'` (`LEDGER_AUDIT.json`) |

No row needed "wrong value" as its primary verdict: in every numeric case the quoted number exists,
just in a different file than the one cited.

## Extra findings the re-read produced

- **`CHAIN.json` holds no mass member at all** — 0 occurrences of `mass` and 0 of `Mass`. T-M1's
  parenthetical (`BatmobileMassRatio` 1.0, `MassScale` 1.0, `InertiaTensorMultiplier` [1, 1, 1])
  therefore is not evidenced by the file it cites. Where those names are decoded is UNKNOWN; the
  `LEDGER_G3*` files mention them but are derived audits, not the chain grab.
- **T-B4 mixes two vocabularies' counts**: n=145 is the five `arcade.heat_boost` rows; the five
  `turbo_jump` rows are n=35 and have an empty donor column, so their figures (punch 0.1 s /
  50 km/h / top 200 km/h) are fleet medians, not "Serpente defaults".
- **T-E2's ×1.67**: `FITS.md`'s fit at 4,000 kg is 834.1, so 1393.5/834.1 = 1.67 is the comparison
  the file actually supports at the built mass.

## Proposals

One JSON block per row, printed in the document only. Each was re-graded with the first audit's
helpers after the edit: `T-M1` -> OK, `T-E2` -> OK (rounded), `T-B4` -> OK (member name),
`T-A1` -> OK (rounded), `T-L3` / `T-L5` -> OK (member name). Gates also assert each proposal keeps
the ledger's keys, changes only the named cells, and leaves `dispo` / `edits` untouched.

## UNKNOWNs

- Where `BatmobileMassRatio` / `MassScale` / `InertiaTensorMultiplier` are actually decoded (not in
  the cited chain file; not established here).
- Whether `FITS.md` ever carried 1,121 at a different evaluation mass — the file today holds 1,100
  and 834.1 only.
- The runtime half of T-L3/T-L5 ("no module row references it"): only decoded preset ids can be
  checked; no game was run, the test ban stays.
- Whether these citations are the ones to adopt editorially: the proposals move provenance and one
  comparison number; no decided value is changed.
- Rows 41..90 (the separate slice in `ROW_EVIDENCE_AUDIT2.md`) are out of scope here.

## Labels

Decoded: the ledger rows and their cells, every cited/landing file's bytes and line numbers, the
built values in `current.json` / `LEDGER_AUDIT.json`. Derived: the classifications, the ratios,
the nearest-value statements, the proposed rows. UNKNOWN: the list above.
