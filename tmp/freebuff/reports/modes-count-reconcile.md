# 29 checks vs 107 fields — different units of account, not a conflict

**Task.** `Research/BatmobileGrab/MODES.md` reports 29 of 29 checks; the `MODLOG.md` section headed
"G1-21 · Modes and transformation values — done" mentions 107 declared fields. Reconcile the two numbers
by reading the MODES.md table and the MODLOG section, say what each count measures, and whether the two
statements conflict.

**Answer: they do not conflict.** The two numbers count different kinds of thing and neither constrains the
other. **107 is a population of fields** — every `BattleMode*`/`Strafe*`/`Transformation*`-family member the
BmAK classes *declare*. **29 is the size of an assertion battery** — how many PASS rows the generator's
self-test prints while proving that `MODES.md` and `MODES.json` still match the data they were built from.
A document can hold 107 fields and 29 checks, or 107 fields and 3 checks; the numbers are independent.

There is, however, a **third number that does differ**: the 2026-10-25 done entry records **26/26** checks,
not 29/29. That one is a stale record, and the same file explains it — §4 below.

---

## 1. The two sentences, quoted exactly

`Research/BatmobileGrab/MODES.md:330` — the last line of the `### Checks` table:

> 29/29 checks passed.

`MODLOG.md:8750` — the first line of the section's **Result** paragraph:

> **Result: 107 declared family fields, 46 serialised, 61 with no value in the files.** Declared

For completeness, the same figure appears in MODES.md's own summary table (`MODES.md:13`):

> | declared family fields | **107** |

and in the section's **Verified** line (`MODLOG.md:8802`, the pre-rework entry):

> **Verified:** `grab_modes.py --check` → **OK: 107 declared, 46 serialised, 61 not serialised;
> 26/26 checks**

---

## 2. What 107 measures

**107 = the declared field population**, counted from `BMSDK_OFFSETS.json` — "what the classes *declare*:
name, absolute offset, declared type" (`MODLOG.md:8741-8743`, `MODES.md:3-6`). It is an inventory of the
family's API surface, not of values found.

It is internally reconciled three ways in the two documents:

| reconciliation | arithmetic | source |
|---|---|---|
| declared vs serialised | **46 + 61 = 107** | `MODES.md:13-15` — 107 declared / 46 serialised / 61 "declared but not serialised anywhere"; `MODLOG.md:8750` — "107 declared family fields, 46 serialised, 61 with no value in the files" |
| the 17-family coverage table | 42+4+8+9+1+1+8+2+1+2+2+3+1+6+1+10+6 = **107** | `MODES.md:29-47` |
| the same table's serialised column | 15+3+0+4+1+1+1+1+1+2+2+3+1+2+1+5+3 = **46**; remaining 61 | `MODES.md:29-47`, and `MODLOG.md:8750-8756` lists the same per-family pairs |

So 107 is a **count of names in a class hierarchy**, split by whether each name carries a value in the four
shipped archetypes. One useful nuance, stated by the document itself (`MODES.md:344`): the 8 `BattleModeCam*`
fields "belong to the camera cards; [they are] listed here only so the `BattleMode*` prefix is complete", so
the card's own simulation/vehicle scope is **99** of the 107 — the number 107 is the *prefix-complete* figure.

## 3. What 29 measures

**29 = the number of PASS rows in the `### Checks` table** (`MODES.md:298-330`) — one per assertion that
`grab_modes.py --check` makes before it will print its OK line. It counts **assertions**, not fields, and the
rows are of three different kinds:

| kind of assertion | rows | example |
|---|---:|---|
| family / field-presence, incl. 3 ledger-count rows | 20 | `T-BM1: BattleMode*` → `PASS \| 42 fields, 15 serialized`; `T-BM1: count BattleMode* = 9` → `PASS \| 9 serialised simulation scalars` |
| quoted-number lookups | 7 | `T-RA1: value 90000` → `PASS`; `T-AC1: value 8000` → `PASS` |
| meta-check on the document | 2 | `GRB-11 cross-check` → `PASS \| 44/44 named fields agree`; `units assigned` → `PASS \| 5 undocumented` |
| **total** | **29** | `MODES.md:330` |

That breakdown is why 29 cannot be read as a field count in either direction: **one** row covers **42**
fields (`T-BM1: BattleMode*`), while **seven** rows cover a single number each, and **two** cover no field
at all. Note also that `GRB-11 cross-check` asserts on 44 *named* fields — a fourth number, measuring the
GRB-11 naming evidence, not the family.

## 4. The number that *does* differ: 26 vs 29 — and why it is not a conflict either

The 2026-10-25 done entry says `26/26 checks` (`MODLOG.md:8802`). MODES.md says 29/29. Both are truthful at
their own timestamp, and the same file records the transition (`MODLOG.md:15817`, "G1-21 rework — done
(no build, 2026-10-29)"), item 4:

> **Done line not actually asserted.** A single-name token must now resolve to a *serialised* field
> (`serialized=False (declared only, no value in the files)` fails), and each parenthetical ledger count must
> equal the serialised non-curve members on the simulation class (9 / 3 / 2). **Three new checks; 26 → 29.**

The rework's own verification block gives the current state:

> ```
> $ python Tools/scripts/grab_modes.py --check
> OK: 107 declared, 46 serialised, 61 not serialised; 29/29 checks; md byte-identical   (exit 0)
> ```

and it records that `Research/BatmobileGrab/README.md` was edited "one row: 26 → 29 checks"
(`MODLOG.md:15845`). So the 26 is a **superseded snapshot of the battery size**, left in place because the
MODLOG is append-only history; the 29 is the live figure, and the three added rows are exactly the three
`T-BM1: count …` assertions visible at `MODES.md:305-307`. The 107 is unchanged by the rework — the rework
added *assertions*, not fields.

**Summary of the three numbers:**

| number | what it counts | where | current? |
|---:|---|---|---|
| **107** | declared family fields across 17 families (46 serialised + 61 declared-only; 99 excluding the 8 camera fields) | `MODES.md:13`, `MODLOG.md:8750` | yes, and unchanged by the rework |
| **29** | PASS rows in the generator's self-test table (20 field/family, 7 number lookups, 2 meta) | `MODES.md:330`, `MODLOG.md:15857` | yes |
| 26 | the same battery before the 2026-10-29 rework added 3 assertions | `MODLOG.md:8802` | no — superseded, kept as history |

## 5. Verdict

**No conflict between "29 of 29 checks" and "107 declared fields".** They are counts of different
categories — assertions versus fields — produced by the same generator in the same run, and both are
re-derived from the same three inputs (`BMSDK_OFFSETS.json` declarations, `objects.jsonl` serialisation,
`OFFSETS.json` naming). The only mismatch in the two documents is **26 vs 29 within the check count
itself**, and it is fully explained by the documented 2026-10-29 rework: "Three new checks; 26 → 29."

Nothing was edited in `MODES.md`, `MODLOG.md` or any generator. Revert: delete this file.

**Limits.** Static reads of `Research/BatmobileGrab/MODES.md` (lines 1-60, 292-346) and `MODLOG.md`
(lines 8733-8812, 15817-15866). `grab_modes.py --check` was **not** re-run, so the 29/29 figure is quoted
from the two documents rather than re-measured; the arithmetic behind 107 / 46 / 61 was recomputed from the
family table by hand and reconciles exactly.
