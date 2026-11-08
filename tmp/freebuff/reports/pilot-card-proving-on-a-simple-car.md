# Q-PILOT step 9 — proving the cards on a stock Serpente

> change 2026-11-07 (review-pilot-cards): the claim that `v05_driving.py --check` did not finish is
> replaced by the measurement (exit 0, 34/34 oracles, run in seconds), and §4.2's B-15 row gained the
> third meaning (the riot card `Research/specs/B-15.md`).

Deliverable: `Working/Q/PILOT/PROVE_CARDS.md` (the prove-set). This report records what it is, why
each step is or is not provable today, and what the run has to produce.

No game was launched, no install was touched, no save was read. The approval file the set gates on
does not exist yet.

---

## 1. The gate, measured

| check | command | output, 2026-11-07 |
|---|---|---|
| approval file | `ls -l tmp/freebuff/APPROVED_Q.txt` | **absent** (`APPROVED_Q absent`) |
| the gate is real in the existing cards | `LAUNCH.md` P1: `test -f tmp/freebuff/APPROVED_Q.txt && echo YES` → `YES` (absent → STOP, the test ban stands) | present in the card |
| the store the run writes to | `ls Working/Q/Q1` | does not exist yet; `P5`/`P6` create `Working/Q/Q1/prove` |

So the prove-set is **written and closed**. Its first line at execution is P1's `YES|STOP`; until
then every card's classifier is "gated", not "failed".

---

## 2. The order of cards

Nine cards, run in this order, one at a time.

| # | card | action | provenance |
|---|---|---|---|
| P1 | `LAUNCH` | saves snapshotted, installer verified, 1600×900 window, PID | existing, **unchanged** |
| P2 | `LOAD_SAVE` | main menu → free roam, profile `76561197960271872` | existing |
| P3 | `SPAWN_SERPENTE` | a stock Serpente within 5 m | **new** (`PROVE_CARDS.md` §2.1) |
| P4 | `ENTER_EXIT_SERPENTE` | enter `E`, HUD frame, exit `E` | **new** (§2.2), derived from `ENTER_EXIT.md` minus canopy |
| P5 | `DRIVE_SERPENTE` | 0→60 km/h hold, capture, HUD trace | **new** (§2.3) |
| P6 | `BRAKE_SERPENTE` | 60→0 km/h stop, trace | **new** (§2.4) |
| P7 | `SCREENSHOT` | one frame + frozen-oracle check | existing, unchanged |
| P8 | `RECORD` | 20 s take with audio, peak measured | existing, unchanged |
| P9 | `KILL` | close by exact PID | existing, unchanged |

Five existing cards are invoked, not edited: `LAUNCH`, `LOAD_SAVE`, `SCREENSHOT`, `RECORD`, `KILL`.
Four are new, because the subject changed and two of them need calibration fields the repo cannot
fill (`SERPENTE_SPAWN`, and `LOAD_SAVE`'s existing `ENTER_KEY` / `SAVE_SLOT_CLICK`).

---

## 3. The acceptance line

```
ACCEPTANCE: a small model completed all steps with no operator help.
```

The set defines each term so the line cannot be reinterpreted after a bad run:

* **small model** — a model reading only the card page, `CONTROLS.md`, and the files the card cites;
* **completed** — every card reaches `RESULT: PASS`, or a `RESULT: STOP` whose `IF NOT` branch was
  followed to a bounded end without a human decision;
* **all steps** — P1–P9 in order, each with its RESULT line and artifact;
* **no operator help** — calibration fields are filled **before** the run, once; anything filled
  during the run is operator help and fails the line. A needed clarification is recorded as
  `ACCEPTANCE: not met — help at <card> step <n> — <question>`, and the answer becomes a card edit.

Two failed runs on the same card rewrite the card, not the pilot — the rule already in
`CARD_FORMAT.md` §2.10 and §"if a card needs the pilot to decide something, the card is wrong".

---

## 4. Review 8299's two constraints, applied

### 4.1 The driving set depends on the re-derived turning circle and the 0.25 s lock

`Working/Q/PREDICTIONS.md` D-4 and D-5 carry the RED: the built full-lock times are **0.80 s low /
0.60 s high**, the ruling goal is **0.250 s / 0.091 s** (55/220 and 20/220 °/s, `T-ST7`), and the
report prints the miss as 3.2× / 6.6×. Measured 2026-11-07: `--check` **exits 0 within seconds with
34/34 oracles**; the RED is the *miss line* (`T-ST7 RED: built 0.80 / 0.60 s vs goal 0.091-0.250 s`),
not a failed check. A green checker is still not test evidence (review 8299) — it compares the
document to its own generator — so a radius or a lock-time number stays unscored until a take
measures it.

Applied to the prove-set:

| step | mechanic | value |
|---|---|---|
| P5 `DRIVE_SERPENTE` | provable (throttle, capture, HUD trace, CSV) | **not-yet-provable** — a stock car's acceleration is the game's, not D-1's |
| P6 `BRAKE_SERPENTE` | provable (brake, stop frame, trace) | **not-yet-provable** — D-3's 101.5–110.2 m belongs to the Batmobile's brake torque (T-K1/T-K2) |
| turning circle / radius | **not scored at all** | no translated lock exists on a stock car; the row is `T-ST7` + D-4 |
| 0.25 s full lock | **not scored at all** | BmAK's 220 °/s is not a property of the Serpente's rack |

The prove-set records these as `not-yet-provable — <the row that settles it>` in the value column.
They are **never** `fail` and never omitted; §3 of `PROVE_CARDS.md` states the rule.

### 4.2 The combat set depends on B-15 / B-18 / B-19 / B-20 / B-21

| card | status in the repo | consequence |
|---|---|---|
| B-18, B-19, B-20, B-21 | `Builds/bm-RC4/receipt.json` `cards_without_payload` includes **B-18, B-19, B-20** (`correction-8398-unshipped-cards.md` §3); `BUILD_BATCHES.md` §4 gives B-18…B-21 zero built values | combat steps **not-yet-provable** |
| B-17 | also in `cards_without_payload` | same |
| B-15 | **number used three times**: the budget card is `done` (`GRAB_BACKLOG.md:1955`), `BUILD_BATCHES.md:234` proposes a HUD step, and `Research/specs/B-15.md` is the riot build card that `T-WP10` cites | a card naming B-15 must say which: HUD rows -> `BUILD_BATCHES.md:234`, riot -> `Research/specs/B-15.md`; the prove-set scores neither |
| B-25 / B-26 | card only (`correction-8398` §1) | flares and per-entity audio stay known gaps |

`FIGHT.md` is therefore **not written** in this step and is not substituted with "fire JC3's own
weapons on the Serpente": that proves JC3's weapon system, not the Batmobile's rows, and would put a
pass on a feature that has no payload.

---

## 5. The failure table

`PROVE_CARDS.md` §5 carries the table and the three allowed classes:

| class | meaning | action |
|---|---|---|
| **card fault** | wrong command, string, path or branch | edit the card after the session, one commit, quote the `SEE` |
| **environment** | mute, focus, window, dump, save state | fix the environment, re-run the card unchanged |
| **build/row** | a member or value the repo does not have | STOP, name the row; card text unchanged |

Columns: `# | card | step | observed SEE | class | smallest card edit | commit | re-run`. The table
starts empty on purpose — a pre-filled row would be a failure invented before the run.

---

## 6. Checks run for this step

| check | result |
|---|---|
| `tmp/freebuff/APPROVED_Q.txt` | absent — the set is gated, and says so in P1 of every card |
| five existing cards read for command fidelity | `LAUNCH` (P1 approval gate, `um win launch`, `size 1600 900`), `LOAD_SAVE` (calibration fields), `SPAWN_BATMOBILE` (template used for `SPAWN_SERPENTE`), `KILL` (PID-only rule), `RECORD`/`SCREENSHOT` (peak and hash checks) |
| every command in the four new cards exists in an existing card or a cited script | `um win shot`, `um win record`, `um win drive`, `um win ps`, `um win kill`, `qa1_hud.py crops/trace` — all quoted from `LAUNCH`/`SCREENSHOT`/`RECORD`/`AIRFIELD` |
| keys used | `0x45` E (rows 1–2), `0x57` W (row 3), `0x53` S (rows 4–5) — all `decoded`; `B` never pressed |
| Serpente identified | `Working/Translation/T1_TRANSLATION.md` donor row `v0300`; `T_WLD6` quotes the car's own blurb ("Kerner's top sports model … 250 km/h") |
| B-card payload status | `correction-8398` §1/§3; `BUILD_BATCHES.md` §4 and `:234`; `GRAB_BACKLOG.md:1955` |
| driving RED | `Working/Q/PREDICTIONS.md` D-4/D-5 (built 0.80/0.60 s vs 0.250/0.091 s goal) |
| files written | `Working/Q/PILOT/PROVE_CARDS.md`, this report; nothing else |
| `Working/Q/Q1` | absent (the run creates `Working/Q/Q1/prove`); no result is pre-filled |

**Limitations**

* `python Tools/scripts/v05_driving.py --check` is **now measured (2026-11-07)**: exit 0,
  `34/34 oracles pass`, ledger 199 rows, `D-4 radius 3.52 m / 13.82 m`, `T-ST7 RED` on the same
  line. The earlier 90 s timeout was the machine, not the script. Green is still not test evidence.
* The stock Serpente's spawn route is `UNKNOWN` in every repo file (no file records JC3's Rebel Drop
  labels or traffic spawns). `SERPENTE_SPAWN` is a calibration field for that reason; the card
  refuses to run on a guess.
* No card was executed, so no `SEE` in this document is an observation of the game.

**Revert:** delete `Working/Q/PILOT/PROVE_CARDS.md` and this report. The five existing cards were
read, not modified.
