# G1-21 rework — modes and transformation values

Date 2026-10-29. Input: `tmp/freebuff/reports/review-G1-21.md` (verdict `needs rework`, 7 issues).
Every issue was re-checked against the data and the generator *before* anything was edited; the
commands and their output are quoted below. Nothing in `Working/Translation/` changed, no game was
launched, nothing under `D:/Games` was written, no shared module was edited, nothing was committed.
Only `tmp/freebuff/reports/` files were written outside the card's own artifacts.

## STATUS: **done — 7/7 issues CONFIRMED and fixed in the generator; 0 rejected**

`Tools/scripts/grab_modes.py` was changed, `--write` regenerated `MODES.md` + `MODES.json`;
neither file was hand-edited. The gate went from red (`STALE`, exit 1) to green
(`29/29 checks; md byte-identical`, exit 0), and two tamper tests plus two ledger-contamination
tests show the gate now bites on exactly the failures the review named.

## State before the fix (verbatim)

```
$ python Tools/scripts/grab_modes.py --check
STALE: MODES.json does not match a fresh build (run --write)
EXIT=1
```

Read-only diagnosis (`build()` re-run in memory, compared with the stored artifact):

```
summary equal True
checks equal True
fields equal True 107 107
ledger fresh [('T-BM1', 'superseded'), ('T-AC1', 'out'), ('T-RA1', 'out'), ('T-SR1', 'out')]
ledger disk  [('T-BM1', 'out'),        ('T-AC1', 'out'), ('T-RA1', 'out'), ('T-SR1', 'out')]
md identical to fresh render True
```

So the red gate was the embedded ledger disposition, not the mode data.

## Per issue

### 1. `--check` red; the card's own verification no longer passes — CONFIRMED (blocking)

Evidence: the two blocks above — `STALE`, exit 1; the only difference between the artifact and a
fresh `build()` is `ledger_rows[].dispo` / `.why` (`T-BM1` `out` on 2026-10-25 →
`superseded` today). `Working/Translation/T_ROWS.jsonl` is the source of that field, i.e. another
card's decision record.

Fix (`grab_modes.py`, `build()`): the ledger block keeps `id`, `tokens`, `numbers`, `counts` and no
longer stores `dispo` / `why`, so a later translation decision cannot stale this artifact. The
comment above the block now says so. The whole Done line only ever needed tokens/numbers/counts.

### 2. The note names the wrong field at 0x0320 — CONFIRMED (blocking)

Evidence, from the artifact the sentence describes:

```
MODES.md:89   | `BattleModeLatSlipScale` | 0x2d4 | ...
MODES.md:102  | `BattleModeTrailingSteerFactorMoving` | 0x320 | ... | -0.25 ×4
MODES.md:203  | `BattleModeSteerBias` | 0x320 | `SVehicleWheel` | ... | no
```

Raw stream scan (`objects.jsonl`): 13 `RBasicProjectile` rows, **0** tags at 0x320 or 0x2d4
(`RBasicProjectile tags at 0x320/0x2d4: []`); the only other owner of 0x320 in the record is
`SVehicleWheel.BattleModeSteerBias`.

Fix: the sentence is derived in `write_markdown`. The renderer groups the record by offset, picks an
offset two declaring classes share, and prints the members from the data. Today:

```
The lookup is class-scoped on purpose: offset 0x320 is `BattleModeTrailingSteerFactorMoving` on
`RVehicleSimBatmobile` and `BattleModeSteerBias` on `SVehicleWheel` - one offset, 2 members - so
a bare offset match would read one field's number as another's.
```

No field name and no class is typed; `RBasicProjectile` is gone from the prose because it was never
in the data.

### 3. `--check` never reads `MODES.md` — CONFIRMED

Evidence: `main()` tested only `os.path.isfile(md_path)` and diffed the JSON; a hand-edited note
passed. (The note happened to equal a fresh render at the time — `md identical to fresh render True`
— so nothing was wrong in the output, only in the gate.)

Fix: `--check` renders `write_markdown(doc)` and compares it with the file, failing with
`STALE: MODES.md does not match a fresh render (run --write)`; the green line now ends
`; md byte-identical`.

### 4. The check proves "declared", not "appears with its value" — CONFIRMED

Evidence (old code): a single-name token passed on `bool(hits)` and merely *printed*
`serialized=False`; a wildcard token passed on `bool(hits)`; the ledger's parenthetical counts were
printed next to the derived numbers but never asserted.

Fix, three new assertions (26 → 29 checks):

* single-name token: requires `hits` **and** `serialized`; failure detail reads
  `serialized=False (declared only, no value in the files)`.
* wildcard token: requires at least one serialised match.
* each parenthetical count: equals the serialised non-curve members on the simulation class
  (`9 / 3 / 2`), which is what the ledger's numbers actually are — the curve member
  (`BattleModeVSpeedCurve`) is the documented extra, and the prose now says so from the data.

Proof the assertions bite (temp ledger copies, repo untouched):

```
A wrong count          -> [('T-BM1: count BattleMode* = 8', '9 serialised simulation scalars')]
B declared-only token  -> [('T-AC1: BattleModeMaxSpeed', 'serialized=False (declared only, no value in the files)')]
restored: failing [] of 29
```

### 5. The Joker behaviour claim goes beyond the tag stream — CONFIRMED (journal)

Evidence: `MODLOG.md` said the Joker archetype "does not serialise them at all … so the Joker car has
no armoured-mode damage reduction and no pursuit/battle dodge in its archetype". The absence is real
(`BattleDodgeImpulse`, `ArmourModeDamageReduction`, `PMDodge*` carry 3 of 4 packages), but a cooked
archetype omits a property equal to its class default, so absence means "the default runs", not
"zero" and not "no feature". The note already says this in its Gaps; the journal did not.

Fix: the sentence now states the absence and the consequence —
"the value running in the Joker car is a `Default__*`/CDO number the grab does not hold — **UNKNOWN**
from the files, not 0 and not 'no feature'". A derived Gaps bullet was added to the note for the same
five fields:

```
- **5 serialised fields are missing from at least one archetype**: `BattleDodgeImpulse` (Joker),
  `ArmourModeDamageReduction` (Joker), `PMDodgeTorque` (Joker), `PMDodgeForce` (Joker),
  `PMDodgeDuration` (Joker). A missing tag is not a zero: …
```

and the `ArmourModeDamageReduction` bullet now says "ships **0** in the 3 packages that carry the
tag … The Joker archetype has no tag there, so its running value is the class default - UNKNOWN",
instead of the blanket "reduces incoming damage by nothing as shipped".

### 6. Typed numbers in the generated prose — CONFIRMED (R11)

Evidence: `BattleModeThrottleSpeed` (10) / `BattleModeYawOffset` (0), "the nine scalars … the tenth
serialised member", and "T-BM1 writes `BattleMode*` (9), `TurnOnSpot*` (3), `TransformationTurn*`
(2)" were string literals in `write_markdown`; they agreed with the record only by coincidence.

Fix: all three read from `doc` now — `one_value()` for the two undocumented fields, the counted
token list is built from `counted`, and the scalar/curve sentence computes its own numbers:

```
The ledger's (9) counts the scalars; the record carries 9 of them plus 1 curve member
(`BattleModeVSpeedCurve`, `FInterpCurveFloat`), so the serialised total on the simulation class
is 10.
```

### 7. The "in this record" column collapses four packages into one — CONFIRMED

Evidence: `describe()` returned `next(iter(f["values"].values()))`, so the ledger table printed
`value 0` for `ArmourModeDamageReduction` and `value 150000` for `BattleDodgeImpulse` while the
Joker archetype has no tag for either — the reading issue 5 grew out of.

Fix: the column names every package's value and the packages with no tag:

```
| `T-BM1` | `ArmourModeDamageReduction` | value 0 (int, undocumented scale) in 3 of 4 packages;
  no tag in Joker, so the class default runs, **UNKNOWN** |
| `T-SR1` | `StayUprightConstraintSetup/Instance` | V2 5106, MK2 5157, Joker 3123,
  Funhouse 5196 (object ref), all 4 packages |
```

## Files changed

| file | change |
|---|---|
| `Tools/scripts/grab_modes.py` | the 7 fixes above (ledger fields, derived offset sentence, derived prose numbers, per-package coverage column, md gate, serialised+count assertions, derived Gaps bullet); `import textwrap` for the wrapped sentences |
| `Research/BatmobileGrab/MODES.md` | regenerated with `--write` (was 26/26 → 29/29; all values unchanged) |
| `Research/BatmobileGrab/MODES.json` | regenerated; `ledger_rows` no longer carries `dispo`/`why` |
| `Research/BatmobileGrab/README.md` | one row: "the 26 checks" → "the 29 checks" |
| `GRAB_BACKLOG.md` §12 `G1-21` row | one line: `29/29, JSON and md both byte-compared`, and the counts are now asserted rather than reconciled |
| `MODLOG.md` | intended-change entry, the corrected Joker sentence, and the "G1-21 rework — done" entry |

Revert: restore `MODES.md`/`MODES.json` from
`tmp/freebuff/reports/MODES.before-g1-21-rework.{md,json}`, revert `grab_modes.py`, restore the
tracker line and the README row, drop the two MODLOG entries.

## `--check` output (verbatim)

```
$ python -m py_compile Tools/scripts/grab_modes.py
(clean)

$ python Tools/scripts/grab_modes.py --check
OK: 107 declared, 46 serialised, 61 not serialised; 29/29 checks; md byte-identical
EXIT=0

$ python Tools/scripts/grab_footage_gaps.py --check
OK: 72 rows, 2 file-resolved, 1 measured (3 samples), reasons {'FILE-VALUE': 2, 'MEASURED': 1, 'NOT-IN-CLIP': 2, 'VALUE-NATIVE': 53, 'UNDOCUMENTED': 5, 'WRONG-SCOPE': 8, 'NATIVE': 1}; 23/23 checks
EXIT=0

$ python Tools/scripts/status_audit.py --check
STATUS.md is current
EXIT=0
```

`grab_footage_gaps.py` reads `MODES.json`, so it was re-run: its digests (61 not serialised, 5
undocumented units) still hold after the artifact change. `t_rows.py` was not needed — no
`T_ROWS.jsonl` row was touched.

## Tamper tests

```
$ printf '\nhand edit\n' >> Research/BatmobileGrab/MODES.md
$ python Tools/scripts/grab_modes.py --check
STALE: MODES.md does not match a fresh render (run --write)
EXIT=1

$ # set TurningModeMaxSpeed / Playable_Batmobile_SF to 601.0 in MODES.json
$ python Tools/scripts/grab_modes.py --check
STALE: MODES.json does not match a fresh build (run --write)
EXIT=1

$ # restored
$ python Tools/scripts/grab_modes.py --check
OK: 107 declared, 46 serialised, 61 not serialised; 29/29 checks; md byte-identical
EXIT=0
```

Plus the two ledger-contamination runs quoted under issue 4 (wrong count; declared-only token) — both
fail, and the restored `build()` reports 0 failing checks of 29.

## Values re-verified against the raw stream after regeneration

| value in `MODES.md` | where | raw tag stream |
|---|---|---|
| `TurningModeMaxSpeed` 600 ×4 | `:86` | `RVehicleSimBatmobile` 0x2c4, `FloatProperty` 600.0 in all four packages |
| `BattleModeTrailingSteerFactorMoving` -0.25 ×4 | `:102` | `RVehicleSimBatmobile` 0x320, `FloatProperty` -0.25 in all four |
| `BattleModeSteerBias` not serialised, 0x320 | `:203` | `SVehicleWheel` 0x320 carries no tag in any package |
| `ArmourModeDamageReduction` 0 in 3 of 4, no Joker tag | ledger table | 3 package values `0`, `Playable_BatmobileJoker_SF` absent |
