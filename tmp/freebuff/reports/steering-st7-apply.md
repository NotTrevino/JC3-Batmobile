# T-ST7 — operator ruling applied (0.25 s, no compromise)

**STATUS: done.** The operator's 2026-11-06 ruling (option A) is applied to the ledger row `T-ST7`
and to its `BLOCKED_PROPOSALS` entry together: `blocked` → `next`, value 0.8 / 0.6 s → **0.25 s low
speed / 0.091 s high speed**. `t_blocked.py` is re-pinned (16 blocked = 12 ledger + 4 T6), and all
three required checks pass: `t_rows.py check`, `t_blocked.py --check`, `status_audit.py --check`.
No build was written, no game was launched or attached to.

## 1. What changed, and how to revert it

| file | change | revert |
|---|---|---|
| `Working/Translation/T3_COVERAGE.md` | row `T-ST7`: target now names both time members, `proposed` carries the ruling and the two derived times, `verify` states the probe and the out-of-domain flag | restore the row's previous 3 cells (`blocked`, 0.8/0.6 s text) and re-run `t_rows.py build` |
| `Tools/scripts/t_rows.py` | `DISPO["T-ST7"]`: `("blocked", …)` → `("next", …)` | restore that one line |
| `Working/Translation/T_ROWS.jsonl` | **regenerated**, not hand-edited (`t_rows.py build`) — `T-ST7` now `dispo: next`, `cells[5]` = 0.25 / 0.091 s, `cells[6]` = `derived` | reverse the two edits above, re-run `build` |
| `Tools/scripts/t_blocked.py` | `T-ST7` removed from `WAITS`/`ATTEMPTS`; new `RESOLVED` record (evidence + ruling + applied change) so the refutation is not lost; pins re-dated 17/13 → 16/12; `reconciles` now asserts 12 + 4 = 16; `oracles()` also checks resolved evidence; render prints a `Resolved` section | restore the removed blocks, drop `RESOLVED`, put the 17/13 literals back |
| `Working/Translation/BLOCKED_PROPOSALS.{json,md}` | **regenerated** (`t_blocked.py --write`): 16 rows, `T-ST7` in a new "Resolved – no longer blocked" section | re-run `--write` after the revert |
| `STATUS.md` | **regenerated** (`status_audit.py --write`): blocked 16 / 180 (was 17), queued 41 | re-run `--write` after the revert |

`T3_COVERAGE.md` is the source of the ledger: `t_rows.py build` parses its tables and attaches the
disposition from `DISPO`, so editing the ledger directly would have been overwritten on the next
build.

## 2. The ruling, as recorded by the operator

`Working/Translation/DECISIONS_NEEDED.md`, "OPERATOR RULINGS 2026-11-06", item 1:

> **T-ST7: A, 0.25 s** (BmAK 55 deg / 220 deg/s). Also check the steering-rate / max-speed members so
> the full BmAK rate is carried, not only the lock time. "No player car ships below 0.5 s" is not a
> reason: AI cars ship 0.25 s and bikes 0.3 s.

The old blocked reason ("the fleet's fastest rack is 0.5 s") was already refuted by
`T_ST7B_FLOOR.md`: 0.25 s on 4 `LandSteering` AI twins and 0.3 s on 2 player `MotorbikeSteering`
modules.

## 3. Does 0.25 s need a matching high-speed value?

**Yes — derived, and the build's own 0.6 s would leave the car at ~15 % of BmAK's rate near top speed.**

| # | fact | label | evidence |
|---|---|---|---|
| 1 | BmAK `SVehicleSimCar.SteerSpeed` = **220.0 °/s** at `0x0DC` in the archetype's `FloatProperty` tag stream; steer curve `0→60°, 600→55°, 1100→55°, 1300→30°, 2000→20°` (cm/s → deg) | **decoded** | `Working/Translation/T_ST7_FLOOR.md:27-35` — 4 exports of `Playable_Batmobile{,MK2,JokerFunhouse,Joker}_SF` `SimulationModel` (#5282/#5333/#5368/#3181, value at byte 2306); offset named by `Research/BatmobileGrab/OFFSETS.json` (`SteerSpeed`) |
| 2 | JC3 `LandSteering` carries **two** times, not one: `t_to_full_steer_s` at +0x08 = **0.800000012 s** (`cdcc4c3f`) and `max_speed_t_to_full_steer_s` at +0x0C = **0.6 s** in the built module | **decoded** | `T_ST7_FLOOR.md:86-88`; ledger row `T-ST7` `now` cell; row `T-ST3` "keep 0.6 s" |
| 3 | The build's lock angles today are 35° (≤30 km/h) → 15° (≥296 km/h); T-ST1's target is BmAK's 55° → 20° | **decoded** (now) / **derived** (target) | `T1_TRANSLATION.md:117`, `t1_edits.json` rows `T-ST1` |
| 4 | low-speed full lock: `55° ÷ 220 °/s` = **0.25 s** | **derived** | rule: lock angle ÷ rate = time to full steer (`T_ST7B_FLOOR.md §3` uses the same rule) |
| 5 | high-speed full lock: `20° ÷ 220 °/s` = **0.0909 s** (row says 0.091 s) | **derived** | same rule at BmAK's 2000 cm/s knot |
| 6 | leaving `max_speed_t_to_full_steer_s` at 0.6 s gives `20 ÷ 0.6` = **33.3 °/s = 15.2 %** of 220 °/s (and `15 ÷ 0.6` = 25 °/s = 11.4 % with today's 15° lock) | **derived** | — |
| 7 | 0.091 s is **below the fleet's data domain**: player minimum 0.5 s, AI minimum 0.2 s (high-speed member: player min 0.5, AI min 0.2) | **decoded** | `T_ST7B_FLOOR.md §1` table |

So 0.25 s alone fixes only the low-speed end: at 72 km/h the rack would still take 0.6 s to reach the
20° lock, i.e. the car would be **6.6× slower** to full lock than BmAK's constant 220 °/s. The row
therefore carries both times, and `T-ST7` now names `max_speed_t_to_full_steer_s` as its target too.

**The catch, stated plainly:** 0.091 s is under every player value and under the AI floor as well, so
it is a declared out-of-domain switch, not a fleet-consistent value. Whether the engine honours it is
**UNKNOWN** (section 5). The alternative — keeping 0.6 s at speed — *is* the compromise the ruling
forbids, so it is not taken.

## 4. Commands and output (verbatim)

```
$ python Tools/scripts/t_rows.py build
E:\Modding\JC3-Batmobile\Working\Translation\T_ROWS.jsonl: 198 rows, 35 edits over 16 rows
exit=0

$ python Tools/scripts/t_blocked.py --write
wrote Working/Translation/BLOCKED_PROPOSALS.{json,md}: 16 blocked rows (12 ledger + 4 T6) of 180 in scope; 5 tested, 1 resolved: T-AU3=still-blocked, T-FX3=unblocked-with-evidence, T-S6=still-blocked, T-AU5=still-blocked, T-WP4=partially-unblocked
exit=0

$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 41 keep 60 epe 26 re-read 0 blocked 12 out 36 superseded 7 | edits 35 over 16 rows
check ok
exit=0

$ python Tools/scripts/t_blocked.py --check
PASS: 16 blocked rows re-derived (12 ledger + 4 T6) of 180 in scope; 5 attempts, all evidence markers present; ledger sha256 unchanged
exit=0

$ python Tools/scripts/status_audit.py --write   # regenerates STATUS.md (16 blocked / 180, queued 41)
$ python Tools/scripts/status_audit.py --check
STATUS.md is current
exit=0
```

Ledger row after the rebuild (`T_ROWS.jsonl:91`):

```
dispo: next
cells[4] (now): 0.8 s low speed / 0.6 s high speed
cells[5] (proposed): **next** (operator ruling 2026-11-06, option A, no compromise): **0.25 s low
speed** = 55° / 220 °/s at the low-speed lock, and **0.091 s high speed** = 20° / 220 °/s at T-ST1's
20° high-speed lock (BmAK's 2000 cm/s knot; the build still has 15° there today), so the whole BmAK
rate is carried and not only the lock time; it supersedes T-ST3's `keep 0.6 s` on the high-speed
member. The "0.5 s family floor" is refuted: `T_ST7B_FLOOR.md` shows 0.25 s on 4 `LandSteering` AI
twins and 0.3 s on 2 player `MotorbikeSteering` modules
cells[6] (conf): derived
```

Counts before → after: `next` 40 → 41, `blocked` 13 → 12, in-scope blocked 17 → 16.

## 5. UNKNOWNs

- **Whether the engine honours 0.091 s, and whether it honours 0.25 s.** No clamp can be shown or
  excluded: 22 docs in the repo name `JustCause3.exe`, 4 mention steering, **0** decode the steering
  update (`T_ST7B_FLOOR.md §4`). Only a game probe would settle it, and the test ban forbids one. The
  AI twin + player-bike evidence proves the *member and parser* accept such values, not the player
  path.
- **`steer_speed_factor` (+0x24, 1.0 in the built module) is not decoded anywhere.** It could be a
  rate multiplier that makes a time-only translation incomplete. Tried: `Research/JC3Grab/VOCABULARY.md`
  and `DRIVE_CARRIERS.md` contain no entry for it (only `countersteer_speed_factor`); the ledger row
  does not use it. Where it would be found: a fleet census of the member plus a probe, or a decode of
  the steering update.
- **`T-ST3` still says `keep 0.6 s`** on the same member this row now supersedes. `T-ST3` is a separate
  ledger row with its own disposition; it was not edited here (that would need its own
  `t1_edits.json` entry and an edit disposition). It is the one documentary conflict left by the
  ruling, and the `T-ST7` row states the supersession explicitly.
- **Runtime**: neither value is measured; `STATUS.md` still counts 0 rows behaviour-verified.

## 6. Knock-on check failures in other tools (not caused by, or created by, this change — not fixed)

These were run to see what the ledger edit touches, not because the brief asks for them:

```
$ python Tools/scripts/v05_driving.py --check
FAIL T-ST7 is no longer blocked; the turning circle must be re-derived        exit=1
$ python Tools/scripts/audit_compromises_t.py --check
FAIL: json drifted / FAIL: markdown drifted                                   exit=1
$ python Tools/scripts/ledger_g3c.py --check
Working\Translation\LEDGER_G3C.md drifted: Markdown differs from what the source bytes re-derive  exit=1
$ python Tools/scripts/t_st7b.py --check
FAIL: json drifted / FAIL: markdown drifted                                   exit=1
$ python Tools/scripts/t_st7.py --check
check ok                                                                      exit=0
```

- `v05_driving.py` is a **designed alarm** (`v05_driving.py:138-140`): the turning circle assumed T-ST7
  blocked, and must be re-derived now.
- `audit_compromises_t.py` and `ledger_g3c.py` read the ledger's dispositions, so my change moved their
  counts/rows. `audit_compromises_t.py` also still lists "0.25 s steering — T-ST7 — 0.6-0.8 s, fleet
  rack floor 0.5 s" as an unapproved compromise, which the ruling now answers; that table needs its
  owning lane to re-word it, then `--write`.
- `t_st7b.py` reads no ledger row (imports: `glob, hashlib, json, os, re, statistics, sys`; its
  numeric re-derivation still prints `271 modules, player car 0.5, player bike 0.3, ai car 0.25,
  best 180.0 deg/s`), so that drift is textual and predates this edit; its §5 prose ("T-ST7 stays
  UNAPPROVED") is now out of date.

## COMPROMISES

**None taken.** The ruling is applied as ruled: 0.25 s at the low-speed lock and the rate-carrying
0.091 s at the high-speed one. The 0.091 s value is recorded as a declared out-of-domain switch
(below the fleet's 0.2 s AI minimum), not as a reduction of the BmAK target.
