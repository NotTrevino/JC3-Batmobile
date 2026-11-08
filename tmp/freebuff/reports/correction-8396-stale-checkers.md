# Correction 8396 - the three stale checkers (2026-11-07)

Review 8399 confirmed all three reds verbatim. Each was a **stale assumption in the checker**, not a
build regression. This report records what the files actually hold, what changed, and what is still
red on purpose.

Files touched (scripts only): `Tools/scripts/v05_driving.py`, `Tools/scripts/t_boost_rows.py`,
`Tools/scripts/t_vnf_six.py`. No build tree, no ledger, no research file was edited.

## 0. The ledger the pins were compared against

Read from `Working/Translation/T_ROWS.jsonl` at fix time:

```
non-blank lines 199   parsed rows 199   unique ids 199
sha256 220dead9b019863a9d3113de5e29cf6d0040e01c2df84da5090d67f8865d5b7a
dispositions: next 109, keep 29, epe 26, edit 16, blocked 11, superseded 7, out 1
resolved under the first audit's rule (keep/edit/epe/out/superseded): 79
```

The old pins were 198 rows (and `t_vnf_six` also pinned 145 resolved). Neither number is in the
file any more, so both pins failed on a **correct** ledger.

## 1. `Tools/scripts/v05_driving.py --check`

**Was:** the file passed its own oracles only by declaring D-4 UNKNOWN, behind a T-ST7 gate
(`dispo in ("blocked","next")`) left over from when T-ST7 was blocked. Once T-ST7 was unblocked
(operator ruling 2026-11-06) the precondition was meaningless, and nothing derived a radius - so the
green said "no value", not "the value is right". A run against the older gate failed with
`FAIL T-ST7 is 'next'; the turning circle must be re-derived`.

**Now:** D-4 is **derived** from decoded values, all parsed from the ledger (none typed):

| input | value | source |
|---|---|---|
| wheelbase | 5.029 m | `T-G1` cell 5 |
| low-speed lock | 55 deg @ <= 20 km/h | `T-ST1` cell 5 |
| high-speed lock | 20 deg @ >= 72 km/h | `T-ST1` cell 5 |
| built steer times | 0.80 s low / 0.60 s high | `T-ST7` value cell |
| BmAK rate | 220 deg/s (`SteerSpeed`) | `T-ST7` cell 1 |
| ruling goal (failing band) | 0.250 s low / 0.091 s high | `T-ST7` next cell, operator ruling 2026-11-06 |

Derivation (bicycle/Ackermann, no slip, printed in `Working/Q/PREDICTIONS.md` D-4):

```
R = wheelbase / tan(lock)
R_low  = 5.029 / tan(55 deg) = 3.521 m
R_high = 5.029 / tan(20 deg) = 13.817 m
t_goal = 55/220 = 0.250 s ; 20/220 = 0.091 s
rate_built = 55/0.80 = 68.8 deg/s ; 20/0.60 = 33.3 deg/s
slowdown = 220/68.8 = 3.2x ; 220/33.3 = 6.6x
RED: 0.80 / 0.60 s is outside the 0.091-0.250 s goal band
```

The pass band is a **declared** +/-10 % on each radius (3.17-3.87 m / 12.44-15.20 m) because tyre
slip and the yaw response are not modelled - the same declared slack D-2 already uses.

**The T-ST7 red stays visible.** The checker prints it on every run and asserts it:

```
RED ... T-ST7: built 0.80 / 0.60 s vs goal 0.091-0.250 s
```

The oracle `D-4 T-ST7 miss still RED` is true only while the built times exceed the ruling band. It
is printed as `PASS` for the *derivation* and the red line carries the shortfall, so a green
`--check` means "the radii and the goal times follow from the built values", **not** "the lore goal
is met". When the build/take closes the gap, that oracle fails loudly and forces the row and sheet
to be re-read rather than silently staying green.

The ledger count is now read from the file (`ledger_stats()`) and the summary prints it:

```
ledger: 199 rows; D-4 radius 3.52 m at the 55 deg lock / 13.82 m at the 20 deg lock;
T-ST7 RED: built 0.80 / 0.60 s vs goal 0.091-0.250 s
```

## 2. `Tools/scripts/t_boost_rows.py` (was 20/21)

**Was:** `add("T_ROWS still parses as 198 rows", len(rows) == 198)`.

**Now:** the count is read from the ledger and the oracle checks file integrity instead of a literal:

```python
nonblank = [ln for ln in read(ROWS).splitlines() if ln.strip()]
add(f"T_ROWS parses cleanly ({len(rows)} rows, no duplicate ids)",
    len(nonblank) == len(rows) == len({r["id"] for r in rows}))
```

Result: `PASS T_ROWS parses cleanly (199 rows, no duplicate ids)`, **21/21**, exit 0. The oracle's
real job - "this proposal sheet did not add a row" - is still covered by `t_rows_edited is false` and
`no proposal id already exists in T_ROWS`, both unchanged.

## 3. `Tools/scripts/t_vnf_six.py` (was AssertionError)

**Was:** `assert len(rows) == 198 and len(resolved) == 145` (hard-coded; the ledger is 199 / 79) and
`LEDGER_SHA` pinned to the 198-row file.

**Now:** the ledger must parse whole - every non-blank line is one row and no id repeats - with the
count printed, not asserted against a literal:

```
PASS T_ROWS.jsonl parses cleanly: 199 rows, 79 resolved, no duplicate ids
```

The sha pin is updated to `220dead9...` and reworded to "the ledger this sheet was built from"; it
still fails if the ledger moves after the sheet is written (and `--check` keeps its after-run sha
comparison).

**A second stale assumption surfaced once the assert was gone** (found by running, not assumed): the
first audit's six no longer re-derive from the current ledger. The first 40 resolved rows now yield:

```
T-A1, T-L3, T-L5, T-M1, T-MA1, T-MA2
```

`T-E2` and `T-B4` left the resolved set - both are `dispo: next` today and their citations were
edited after the audit (`T-E2` now cites `keep-audit-engine-boost-aero.md` and grades OK). So the
old aggregate oracle `vnf == sorted(SIX)` was false for a correct ledger, and `T-MA1`/`T-MA2` are new
VNF rows outside this sheet's subject.

Fix, without loosening the check:

* each of the audit's six is now asserted **by name** to its current status (`NOW` table): the four
  still resolved must still grade `VALUE-NOT-FOUND`; `T-E2`/`T-B4` must still be outside the resolved
  set. A row changing again fails by name;
* the window's actual six are pinned as `CURRENT_SIX = [T-A1, T-L3, T-L5, T-M1, T-MA1, T-MA2]`;
* the document gains a **"Drift since the first audit"** section stating the 199-row / 79-resolved
  facts, that `T-E2`/`T-B4` were closed by ledger edits, and that `T-MA1`/`T-MA2` are recorded but
  not analysed (they are not the audit's subject);
* each row section now prints its grade against today's ledger.

Result: **87/87**, document regenerated, `PASS document`, `PASS ledger: sha256 unchanged after the
run`, exit 0.

## 4. Checks run (all exit 0)

```
python Tools/scripts/v05_driving.py --write   -> 21/21, wrote Working/Q/PREDICTIONS.md (5 predicted, 0 UNKNOWN)
python Tools/scripts/v05_driving.py --check   -> 21/21, PASS document
python Tools/scripts/t_vnf_six.py --write     -> 87/87, wrote Working/Translation/VALUE_NOT_FOUND_SIX.md
python Tools/scripts/t_vnf_six.py --check     -> 87/87, PASS document, PASS ledger sha unchanged
python Tools/scripts/t_boost_rows.py --check  -> 21/21
```

Generated artifacts updated because their pins changed: `Working/Q/PREDICTIONS.md` (D-4 section now
derived, header now 199 rows) and `Working/Translation/VALUE_NOT_FOUND_SIX.md` (sha, counts, drift
section). Neither is a build tree.

## 5. Limits and open items (UNKNOWN, not smoothed over)

* **`git checkout` cannot revert these three scripts.** They are untracked in this repository
  (`git status` shows `?? Tools/scripts/v05_driving.py` etc.), so a checkout restores nothing.
  Revert by restoring the pre-edit copies (`git stash -u` keeps them, or delete and re-create).
* **The high-speed lock is contested inside the ledger.** This derivation uses `T-ST1`'s 20 deg (the
  input named in the task). `T-ST7`'s own next cell says "the build still has 15 deg there today"; at
  15 deg the high-speed radius would be 5.029/tan(15 deg) = 18.77 m, not 13.82 m. Which angle the
  current build actually carries is **UNKNOWN** without a read-back, and no file here settles it.
* **The take's 60 km/h leg is bracketed, not pinned** (3.52-13.82 m): the falloff is decoded as 1.5,
  but the interpolation law between the 20 and 72 km/h knots is not.
* **Whether the engine honours 0.25 s / 0.091 s** remains UNKNOWN: the test ban stands, no build was
  launched or installed, and the red stays open until take A3 measures it.
* **Stale prose left deliberately:** `Working/Translation/BOOST_ROWS_PROPOSAL.md` line 3 still says
  "(198 rows, read-only)". It is an input page, not a checker, and editing it would widen this
  correction past the three scripts; it is recorded here instead.
