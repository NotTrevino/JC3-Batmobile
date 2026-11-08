# V-05 - prediction sheets refreshed for RC4, three reds fixed and disclosed

**STATUS: done.** Every check in `GRAB_BACKLOG.md` §9b now carries an expected number and a pass
band: **28 checks parsed, 27 predicted, 0 blocked, 1 excluded** (the battle variant, excluded by the
reopened D-2). The three checkers named in 8396 are green on the 199-row ledger, **without deleting
or weakening an assertion** - `t_boost_rows` 21/21, `t_vnf_six` 87/87 with the sha pin updated, and
`v05_driving` 34/34 with the T-ST7 miss still printed as RED on every run. Nothing was tested in
game; the test ban stands.

---

## 1. What changed and where

| file | change | why it is the right file | revert |
|---|---|---|---|
| `Tools/scripts/v05_predictions.py` | `Q2-A7` and `Q3-5` turned from `blocked` (no value, no band) into predicted lines with bands; the "a blocked row has NO band" sentence is now conditional | it is the generator of `PREDICTIONS_ALL.md`, the coverage index that parses §9b; a blocked row there is exactly "a Q check without a prediction" | restore the two `(None, None, ...)` tuples |
| `Tools/scripts/v05_driving.py` | new **D-5** (A4 steering hold) and **D-6** (A7 handbrake drift) lines, sections, fail-list rows and two oracles; header count 5 -> 7 predicted; the A7 take is matched with the card's line-wrap flattened | it generates `Working/Q/PREDICTIONS.md`, the driving sheet A1-A7 belong to | delete the two `pred` dicts and the two `a(...)` blocks |
| `Tools/scripts/v05_looks.py` | `Q1-8` now states **21 of 45** donor GUIDs, with an oracle reading `Builds/bm-RC4-audio/events.json` (`total` 45 / `resolved` 24 / `donor_bank_not_built` 21) | it generates `PREDICTIONS_LOOKS.md`; the audio split is a looks-session claim | drop the oracle and the row's extra clause |

Regenerated: `Working/Q/PREDICTIONS.md`, `Working/Q/PREDICTIONS_ALL.md`,
`Working/Q/PREDICTIONS_COMBAT.md` (unchanged, `--check` passes), `Working/Q/PREDICTIONS_LOOKS.md`,
`Working/Q/predictions.json`. No build tree, ledger or research file was edited.

## 2. The three reds - exact failure, then state

| checker | failure as reported | what the files actually hold | fix | now |
|---|---|---|---|---|
| `v05_driving.py --check` | `FAIL T-ST7 is 'next'; the turning circle must be re-derived` (gate `dispo in ("blocked","next")`; the take was unblocked by the 2026-11-06 ruling) | T-ST7: built **0.80 s low / 0.60 s high**, goal **0.250 / 0.091 s**, `SteerSpeed` 220 deg/s; T-G1 wheelbase 5.029 m; T-ST1 locks 55 deg @ <= 20 km/h, 20 deg @ >= 72 km/h | the gate is gone; D-4 is **derived** from those cells (none typed), and D-5 carries the built times as the prediction while the goal stays a named expected failure | **34/34, exit 0**, `T-ST7 miss still RED` asserted |
| `t_boost_rows.py` | 20/21: `T_ROWS still parses as 198 rows` | the ledger has **199** rows, 199 unique ids | the oracle now reads the ledger: every non-blank line is one row, ids unique; no literal | **21/21, exit 0** |
| `t_vnf_six.py` | `AssertionError`: `assert len(rows) == 198 and len(resolved) == 145` | 199 rows, **79** resolved under the first audit's rule | the assert checks the file parses whole (count printed, not pinned); sha pin `220dead9...`; the six are asserted **by name** (`T-E2`/`T-B4` left the resolved set by ledger edit; `CURRENT_SIX` = T-A1, T-L3, T-L5, T-M1, T-MA1, T-MA2) | **87/87, exit 0**, `PASS ledger sha unchanged` |

`220dead9b019863a9d3113de5e29cf6d0040e01c2df84da5090d67f8865d5b7a` - unchanged before and after
every run above.

## 3. Turning circle re-derived from the built values (D-4)

```
R       = wheelbase / tan(lock)              (bicycle/Ackermann, no slip)
wb      = 5.029 m                            T-G1
lock    = 55 deg (<= 20 km/h) / 20 deg (>= 72 km/h)   T-ST1
R_low   = 5.029 / tan(55)  = 3.521 m        band 3.17-3.87 m  (+-10 %, declared)
R_high  = 5.029 / tan(20)  = 13.817 m       band 12.44-15.20 m

built times  0.80 / 0.60 s                   T-ST7 value cell
goal times   55/220 = 0.2500 s ; 20/220 = 0.0909 s      T-ST7 next cell (ruling 2026-11-06)
built rates  55/0.80 = 68.75 deg/s ; 20/0.60 = 33.33 deg/s
slowdown     220/68.75 = 3.2x ; 220/33.33 = 6.6x
RED          0.80 / 0.60 s is outside 0.091-0.250 s
```

The radius is geometry and does not depend on the steer time, so the ruling is compared as a
**time** band. Two domain facts are disclosed rather than smoothed: **0.091 s sits below the fleet's
0.2 s minimum** (T-ST7's own verify cell calls it a declared out-of-domain switch), and the
high-speed lock is contested inside the ledger - T-ST7's next cell says the build still carries
**15 deg** there, which would make the high-speed radius **5.029 / tan(15) = 18.77 m**, not 13.82 m.
This sheet uses T-ST1's 20 deg because that is the input the briefing names; a read-back settles it.

## 4. Coverage - nothing in Q is judged without a prediction

`PREDICTIONS_ALL.md`: **28 parsed / 27 predicted / 0 blocked / 1 excluded.** The two rows converted
from `blocked` are the only substantive change:

* **Q2-A7 (handbrake drift)** - expected: enters near **20 deg**, peaks inside T-DR1's **45 deg**
  cap, recovers without snap-back; rear aligning **0.625** (falsifier **0.48**), handbrake friction
  **4.0**, release ramp **0.3 s**. Band: drift, hold and recover inside ~2 s with no spin past
  ~60 deg; a refusal to rotate at 0.625 points at 0.48; a stop time that does not fall against the
  1.0-factor control fails T-K3. Class: **decoded (JC3 cap/entry) + label bands**.
* **Q3-5 (tether/airlift)** - expected: the tether attaches and holds a **6,000 kg** car (6.154x the
  donor's 975); airlift cannot lift it - 6,000 is **40.0 %** of the flatbed's 15,000 body, 15.0 % of
  the cargo plane's 40,000 and 6.0 % of the transport boat's 100,000 (`TETHER.md`). Band: grabs and
  drags/holds without detaching, no carrier lifts it; a clean lift fails the line.
* The excluded row is **Q2-battle** - a decision, not a test (D-2 reopened 2026-11-06), so it has no
  band by design and is not counted as an unjudged check.

Driving sheet now carries **A1, A2, A3, A4, A5, A7** in 7 lines (D-2b is the boost delta), each with
a band the observer can fail:

| id | expected | band |
|---|---|---|
| D-5 (A4) | full lock in **0.80 / 0.60 s** (built) | 0.75-0.85 / 0.55-0.65 s (+-0.05 s); a reading near 0.25 / 0.09 s means the build moved |
| D-6 (A7) | 20 deg entry, 45 deg cap, 0.625 aligning | drift/hold/recover ~2 s, no spin past 60 deg; 0.48 falsifies 0.625 |

## 5. Label bands, not measured truths (carried by every sheet that quotes them)

| item | value carried | class | what it is not |
|---|---|---|---|
| **T-E5 top speed** | **336.4 km/h**, top of a **300-336 km/h** band | `assumed` (wiki 209 mph) | **not decoded**: at the built Cd **0.55** and T-E2's 2,921 N.m the terminal is **267 km/h**; the **0.1213** Cd written to make 336.4 reachable is **withdrawn** (correction 8391, build-d10 §5.2). The sheet prints both the label and the derivation and predicts 240-294 km/h, so a take inside 300-336 falsifies the Cd/power pair rather than passing |
| **T-ST6 drift aligning** | **0.625 = 1 / 1.6** | **INFERRED reciprocal** | not measured; falsifier **0.48 = 0.3 x 1.6**; 0.625 sits inside the shipped 0.3-0.8 band (n=19) |
| **T-K3 handbrake friction** | **4.0 = 640,000 / 160,000** | derived ratio | inside the shipped 1-10 domain but **above the 6 t class band 1..2.25** - declared, not a 6 t value |
| **T-K4 block time** | ledger `from` still **5**, bytes carry **1** (T-K2); next **0.3 s** | decoded (bytes) / INFERRED (0.3 s kind-match) | not a ledger-consistent pair: read the bytes, not the `from` cell |
| **collision Q-2** | **2 bodies / 3 boxes / 1 constraint, 2 of BmAK's 3 boxes have no shape instance, placement 6.1 cm - gate false** | **named expected failure** | not a surprise if it fails, not a pass. Disclosure: RC4's `sportsmuscle.physicsc` (`fda78f4d...`) hull is **0.25 cm** off chassis box 0; the **6.1 cm** figure belongs to payload `0164936b...`, which is not in this tree |
| **lights** | **angle 70 / range 60** | out-of-domain (U-1) | not shipped behaviour: the 3,217-entry fleet census tops out at **50 m / 50 deg**, so a clamp reads as a short or soft cone, not a defect (Q1-7b; fallback 50/50) |
| **audio** | **21 of 45 GUIDs donor** | measured count | not a mapped sound set: 24 resolve in `vehicles.bank`, the 21 lack a carrier (19 effects + 2 character banks not built, 8393 option b) |

## 6. Commands run, with the result line

```
python Tools/scripts/v05_driving.py --write     -> 34/34 oracles pass; wrote Working/Q/PREDICTIONS.md
python Tools/scripts/v05_driving.py --check      -> exit 0; 34/34; PASS document: PREDICTIONS.md
                                                   matches the regenerated driving sheet
python Tools/scripts/v05_looks.py --check        -> exit 0; 33/33; PASS document (PREDICTIONS_LOOKS.md)
python Tools/scripts/v05_combat.py --check       -> exit 0; 54/54; PASS document (PREDICTIONS_COMBAT.md)
python Tools/scripts/v05_predictions.py --check  -> exit 0; 28 parsed, 27 predicted, 0 blocked,
                                                   1 excluded, 0 without a row
python Tools/scripts/t_boost_rows.py --check     -> exit 0; 21/21; PASS T_ROWS parses cleanly (199 rows)
python Tools/scripts/t_vnf_six.py --check        -> exit 0; 87/87; PASS document; PASS ledger sha unchanged
python Tools/scripts/damage_predict.py --check   -> exit 0; 9 arms x 3 vehicles, json match True
wc -l Working/Translation/T_ROWS.jsonl           -> 199
sha256sum Working/Translation/T_ROWS.jsonl      -> 220dead9b019863a9d3113de5e29cf6d0040e01c2df84da5090d67f8865d5b7a
```

New driving oracles that make the labels fail loudly rather than drift:

```
PASS D-6 labels re-derive (align 0.625 = 1/1.6, falsifier 0.48; T-K3 4 above the 6 t band 1..2.25;
     T-K4 ledger 5 vs bytes 1, next 0.3 s)
PASS D-5 band brackets the built times (0.80 / 0.60 s)
PASS D-4 ruling times re-derive as lock/rate (0.2500 / 0.0909 s at 220 deg/s)
PASS D-4 T-ST7 miss still RED: built 0.80 / 0.60 s vs goal band 0.091-0.250 s (open until take A3)
```

## 7. UNKNOWNs (each with what would settle it)

* **Whether the engine honours 0.091-0.250 s** - no test; take A3/A4 measures it. The red stays open.
* **Which high-speed lock the build carries** (20 deg or the 15 deg T-ST7 names) - a read-back of the
  built steering curve; 20 deg gives 13.82 m, 15 deg gives 18.77 m.
* **The 60 km/h corner leg** - bracketed 3.52-13.82 m; the knot interpolation between 20 and 72 km/h
  is not decoded (only the 1.5 falloff).
* **Drift angle at the car** - no BmAK row states one; A7 is judged on T-DR1's shipped cap and the
  band, not on a lore number, and 0.625 vs 0.48 is the only discriminator the files offer.
* **Tether behaviour on a 6,000 kg car** - `TETHER.md` gives the mass ratios, not a runtime force
  limit; the take measures it.
* **The 21 donor audio GUIDs' effect** - no carrier is decoded, so their silence or absence cannot be
  scored as a defect (8393 option b).
* **Nothing was run in game** - no install, no launch, no attach; all of the above is static.
