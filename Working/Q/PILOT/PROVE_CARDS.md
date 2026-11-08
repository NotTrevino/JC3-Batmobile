# PROVE_CARDS — prove the pilot cards on a stock Serpente

> change 2026-11-07 (review-pilot-cards): §3 claimed `v05_driving.py --check` "is not green". It is
> green — exit 0, 34/34 oracles — and the RED it prints is the built-vs-goal miss, not a failed
> check. The row now states both, plus why a green checker is still not test evidence. §4's B-15
> note gained the third meaning (the riot card).

**What this is.** The Q-PILOT cards have been written against the Batmobile, but no card has ever
been executed. This set runs the same nine steps on a **shipped JC3 car** — the Serpente
(`v0300_car_kensington_sportsmuscle`, the build's own donor chassis) — so the cards are proven on a
vehicle the game already ships before the Batmobile touches it.

**Approval gate.** Nothing here runs until `tmp/freebuff/APPROVED_Q.txt` exists. Every card's P1 is
that file; absent, the card STOPs at step 0 and the session is recorded as *not run*, never as a
failure. On 2026-11-08 the file **exists**, scoped to Q-0 (this set) and the L0 RC4 probe session,
so this set is runnable; the scope line is read in P1, not assumed.

**Subject.** Serpente, stock, no mod payload installed. It is the donor of the Batmobile's entity
tree (`Working/Translation/T1_TRANSLATION.md` §"Serpente `v0300` (current)"), it has four wheels,
a door, a horn-free cabin and a stock HUD, and it needs none of the Batmobile's blocked rows. It is
also the only car in the fleet whose size and modules are already decoded here, so a failure can be
attributed to a card rather than to the car.

**Why prove on it.**
* Entry, exit, camera, HUD, capture and kill are the same code paths for any `CCar`; the Batmobile
  adds only blocked rows (canopy, canopy interaction, Rebel Drop leaf, 9 SWeaponPoints).
* A card that fails on the Serpente fails for a reason the pilot can see; a card that fails on the
  Batmobile could be the build, the row, or the card.
* The stock car's behaviour is the game's, so a `SEE` that fires wrongly is a **card** defect by
  construction — the one thing this run exists to find.

---

## 1. The order of cards

Run in this order, one card at a time, no skipping, no re-ordering. P1–P2 are pre-existing cards
run unchanged; P3–P6 are the prove-set cards written here; P7–P9 are pre-existing cards run against
the Serpente instead of the Batmobile.

| # | card | action | card file | provable today? |
|---|---|---|---|---|
| P1 | `LAUNCH` | saves snapshotted, installer verified, window 1600×900, PID read | `Working/Q/PILOT/LAUNCH.md` (existing, unchanged) | **gated** — P1 needs `APPROVED_Q.txt`; every step after it is unmodified |
| P2 | `LOAD_SAVE` | main menu → free roam on profile `76561197960271872` | `Working/Q/PILOT/LOAD_SAVE.md` (existing) | **gated + calibration** — `ENTER_KEY`, `SAVE_SLOT_CLICK` are `UNKNOWN` until first run |
| P3 | `SPAWN_SERPENTE` | a stock Serpente is in front of Rico | this file, §2.1 | **gated** — console hint first (`SERPENTE_HINT`, `pilot-cards-wheel-check.md` §3 P5); the `SERPENTE_SPAWN` calibration is fallback-only |
| P4 | `ENTER_EXIT_SERPENTE` | enter (`E`), camera/HUD frame, exit (`E`), both frames archived | this file, §2.2 | **gated** — keys are `decoded` (`CONTROLS.md` rows 1–2); no calibration needed |
| P5 | `DRIVE_SERPENTE` | accelerate to 60 km/h and hold; note the steering response | this file, §2.3 | **mechanic provable; value NOT-YET-PROVABLE** (§3) |
| P6 | `BRAKE_SERPENTE` | 60→0 km/h stop, one take, no lock-up claim | this file, §2.4 | **mechanic provable; value NOT-YET-PROVABLE** (§3) |
| P7 | `SCREENSHOT` | one frame on disk + frozen-oracle check | `Working/Q/PILOT/SCREENSHOT.md` (existing) | **gated** — unchanged; the subject is only what is in frame |
| P8 | `RECORD` | 20 s take with audio, peak measured | `Working/Q/PILOT/RECORD.md` (existing) | **gated** — unchanged |
| P9 | `KILL` | end the session by exact PID | `Working/Q/PILOT/KILL.md` (existing) | **gated** — unchanged |

**Combat set: not in this run.** `FIGHT.md` does not exist yet and the features it would exercise
are not built (§4). It is listed here as **not-yet-provable**, not as a card to write today.

---

## 2. The acceptance line

```
ACCEPTANCE: a small model completed all steps with no operator help.
```

Scored on the run log, not on the car:

| term | definition used for scoring |
|---|---|
| **small model** | a model reading only the card page, `CONTROLS.md`, and the three source files the cards cite |
| **completed** | every card reaches a `RESULT: PASS` line, or a `RESULT: STOP` whose `IF NOT` branch was followed to its bounded end without needing a human decision |
| **all steps** | P1–P9 executed in order, each with its RESULT line and its artifact |
| **no operator help** | no key, click, menu label, coordinate, distance or "what does this mean" question answered during the run. Calibration fields are filled **before** the run, once, and are part of the card thereafter; anything filled during the run is operator help and fails this line |

A run that needs one clarification is recorded as `ACCEPTANCE: not met — help at <card> step <n> —
<question>`, and the answer becomes a card edit (§5). Two failed runs on the same card = the card is
rewritten, not the pilot (§4 of `CARD_FORMAT.md`: "if a card needs the pilot to decide something,
the card is wrong").

---

## 2.1 `SPAWN_SERPENTE` — a stock Serpente in front of Rico

```
GOAL: a stock Serpente is within 5 m of Rico, stationary, and the frame proves which car it is.

WHY THIS CARD EXISTS: the prove-set needs a shipped car, not the Batmobile.

ROUTE A (primary): the console. `jc3-console-thingy`, spawn by name (evidence and DLL receipt:
`Working/Q/PILOT/CONSOLE_RECEIPT.md`). `spawn` takes a model name, forwarded as `model_name.c_str()`
(decoded: `src/commands/spawn.h`, `src/game/spawn_system.h`). The hint is read off the console's own
list once and recorded here:
    SERPENTE_HINT=<the hint the console lists for v0300_car_kensington_sportsmuscle_civilian_01>

ROUTE B (fallback): the stock route, calibrated by the operator — used only if the DLL is absent or
the console does not open. No repo file records JC3's stock spawn routes, so this is a calibration
field, never a guessed menu path.
    SERPENTE_SPAWN=<the route the operator used: Rebel Drop entry label, or "drive/steal one at <place>">
    SERPENTE_SHOT=Working/Q/PILOT/shots/serpente_spawn.png

PRE-CONDITIONS
| # | check | command | must show |
|---|---|---|---|
| P1 | approval to launch | `test -f tmp/freebuff/APPROVED_Q.txt && echo YES` | `YES` (absent -> STOP, the test ban stands) |
| P2 | LOAD_SAVE PASS | `Working/Q/PILOT/LOAD_SAVE.md` RESULT line | `RESULT: PASS`, same pid |
| P3 | a route is filled | `grep -E "^    (SERPENTE_HINT|SERPENTE_SPAWN)=<" Working/Q/PILOT/PROVE_CARDS.md` | no output (whichever route this run uses is filled) |

STEPS

### 1. Capture the screen before the car arrives
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/serpente_00.png
    SEE  the file exists, larger than 0 bytes
    IF NOT  STOP — capture dead, run SCREENSHOT step 7

### 2. Bring the car in: console first
    DO   um win drive --proc JustCause3 "key 0xC0"
    SEE  `ok`; step 2b's frame differs from `serpente_00.png` (the console is drawn)
    IF NOT  `fail` -> STOP, the game is not foreground
    IF NOT  the frame is identical and `~` (0xC0) does nothing -> try `key 0x70` (F1) once, then
    go to 2F

### 2b. Prove the console opened
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/serpente_console.png
    SEE  sha256 differs from `serpente_00.png`
    IF NOT  identical -> close with the same key, go to 2F (record `console=no-ui`)

### 2c. Spawn by name
    DO   um win drive --proc JustCause3 "type spawn <SERPENTE_HINT>"
    SEE  `ok`
    IF NOT  `fail` or the WinDrive build has no `type` command -> the operator types it once; the
    run is then recorded as `ACCEPTANCE: not met — console typing needed`, and the take continues
    NOTE  the car appears at the crosshair, 1.0 m up (spawn.h replaces the transform translation with
    `m_aimPos`). Aim at open ground before typing.

### 2F. FALLBACK - the calibrated stock route (only if 2/2b/2c are refused)
    DO   um win drive --proc JustCause3 "<SERPENTE_SPAWN>"
    SEE  `ok`
    IF NOT  `fail` -> STOP, the game is not foreground

### 3. Wait for the delivery / approach
    DO   sleep 10
    SEE  the command returns, exit 0
    IF NOT  re-run once

### 4. Capture the car
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/serpente_spawn.png
    SEE  the file exists and its sha256 differs from `serpente_00.png`
    IF NOT  identical -> nothing arrived: STOP, the route is wrong (record the frame)

### 5. Confirm it is the Serpente and not another car
    DO   ls -l Working/Q/PILOT/shots/serpente_spawn.png
    SEE  one line, size larger than 0; the frame shows the low two-door coupe, not a truck or a buggy
    IF NOT  wrong car in frame -> repeat step 2 once, then STOP and name what arrived

### 6. Confirm the process and the dump folder
    DO   ls -t "$LOCALAPPDATA/CrashDumps" | grep -i justcause3 | head -1
    SEE  no output
    IF NOT  a dump name -> STOP with it on the RESULT line

RESULT
    RESULT: PASS — stock Serpente within 5 m, stationary — pid=<pid> — shots/serpente_00.png, shots/serpente_spawn.png
    RESULT: STOP — step <n> — <the SEE that failed, quoted> — <frames so far>

TRAPS: a listed vehicle is not necessarily spawnable (E-3); the Batmobile's Rebel Drop leaf does
       not exist in a stock install, so this card must not use SPAWN_BATMOBILE's fields. Route A's
       DLL is a second in-process hook: a crash after 2c must be attributed by removing it
       (`CONSOLE_RECEIPT.md` undo) and repeating the take, before the card is blamed. UNKNOWN: the
       console's hint for this leaf and whether WinDrive can type (`type ...`) - both are recorded
       on the first run, neither is guessed here.
```

## 2.2 `ENTER_EXIT_SERPENTE` — the same entry card, no canopy

```
GOAL: Rico is in the Serpente, the driving HUD is on screen, and he is out again, with the frames
      archived and the key that worked on the RESULT line.

PRE-CONDITIONS
| P1 | SPAWN_SERPENTE PASS | card above | RESULT: PASS |
| P2 | the same pid | `um win ps \| grep -i justcause3` | the recorded pid |

STEPS

### 1. Capture the approach
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/serpente_enter_00.png
    SEE  the file exists, larger than 0 bytes
    IF NOT  STOP

### 2. Press E once (decoded ENTER_VEHICLE, CONTROLS.md row 1)
    DO   um win drive --proc JustCause3 "key 0x45"
    SEE  `ok`
    IF NOT  `fail` -> STOP, not foreground

### 3. Wait, then capture
    DO   sleep 2
    SEE  the command returns, exit 0
    IF NOT  re-run once

### 4. Capture after entering
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/serpente_enter_01.png
    SEE  the file exists and differs from `serpente_enter_00.png`
    IF NOT  identical -> run step 2 once more, then STOP (the approach side may be wrong: E-1/E-2)

### 5. Check the HUD is the driving HUD
    DO   cp Working/Q/PILOT/shots/serpente_enter_01.png Working/Q/PILOT/shots/serpente_hud_ref.png
    SEE  the copy exists; the frame shows speed/gear, not the on-foot HUD
    IF NOT  on-foot HUD -> the entry did not happen: STOP

### 6. Press E to exit (decoded EXIT_VEHICLE, row 2)
    DO   um win drive --proc JustCause3 "key 0x45"
    SEE  `ok`
    IF NOT  `fail` -> STOP

### 7. Wait, then capture the exit
    DO   sleep 2
    SEE  the command returns, exit 0
    IF NOT  re-run once

### 8. Capture after exiting
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/serpente_exit_00.png
    SEE  the file exists and differs from `serpente_hud_ref.png`
    IF NOT  identical -> repeat step 6 once, then STOP

RESULT
    RESULT: PASS — entered and exited with E — pid=<pid> — shots/serpente_enter_00/01, serpente_hud_ref, serpente_exit_00.png
    RESULT: STOP — step <n> — <the SEE that failed, quoted> — <frames so far>

TRAPS: E-1/E-2 (entry is a volume, not a point — approach from the left); no canopy on this car, so
       a canopy check would be a Batmobile row and is deliberately absent; `B` is never pressed.
```

## 2.3 `DRIVE_SERPENTE` — accelerate and hold 60 km/h

```
GOAL: one take in which the car accelerates from rest to 60 km/h, holds it for 3 s, and the frames
      and the HUD trace exist. The card proves the instrument, not the Batmobile's tune.

PRE-CONDITIONS
| P1 | ENTER_EXIT_SERPENTE PASS | the card above | RESULT: PASS |
| P2 | the strip is straight and clear | Working/Q/PILOT/AIRFIELD.md (if already proven) or operator | `RESULT: PASS` / stated on the RESULT line |
| P3 | a take directory exists | `mkdir -p Working/Q/Q1/prove` | exit 0 |

STEPS

### 1. Start the recording WITH audio
    DO   um win record --exe JustCause3.exe --pid <pid> --out Working/Q/Q1/prove/drive1 --seconds 25
    SEE  exit 0; drive1.mkv, drive1.audio.raw, drive1.json exist, none 0 bytes
    IF NOT  no `.audio.raw` -> STOP; `--no-audio` is banned (RECORD, A-1)

### 2. Hold throttle (W, decoded ACCELERATE, CONTROLS.md row 3)
    DO   um win drive --proc JustCause3 "key 0x57"
    SEE  `ok`
    IF NOT  `fail` -> STOP, not foreground

### 3. Wait for the speed to build, then capture
    DO   sleep 6
    SEE  the command returns, exit 0
    IF NOT  re-run once

### 4. Capture the moving frame
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/serpente_drive60.png
    SEE  the file exists, > 0 bytes, and the HUD reads a speed above 0
    IF NOT  speed 0 -> the car did not move: STOP (record the frame)

### 5. Tap throttle again to hold, then release
    DO   um win drive --proc JustCause3 "key 0x57"
    SEE  `ok`
    IF NOT  STOP

### 6. Read the speed trace from the HUD
    DO   python Tools/scripts/qa1_hud.py crops --video Working/Q/Q1/prove/drive1.mkv --out Working/Q/Q1/prove/work --fps 5
    SEE  exit 0 and a crop directory with frames
    IF NOT  non-zero -> STOP and quote the error (path or fps wrong)

### 7. Trace it
    DO   python Tools/scripts/qa1_hud.py trace --crops Working/Q/Q1/prove/work/hud --csv Working/Q/Q1/prove/drive1.csv --fps 5
    SEE  exit 0 and a CSV with more than 20 rows
    IF NOT  an unlabelled-glyph refusal -> STOP and label the glyph (the instrument protecting the
             number, QA1_RESULTS.md §1); do not hand-read the digits

### 8. Write the measured peak
    DO   python -c "import csv;r=[float(x['kmh']) for x in csv.DictReader(open('Working/Q/Q1/prove/drive1.csv'))];print(max(r))"
    SEE  a number printed; write it on the RESULT line
    IF NOT  a parse error -> STOP (the CSV schema is not what the card expects)

RESULT
    RESULT: PASS — 0→<n> km/h, trace <rows> rows — pid=<pid> — prove/drive1.mkv + .csv, shots/serpente_drive60.png
    RESULT: STOP — step <n> — <the SEE that failed, quoted> — <artifacts so far>

TRAPS: D-1 (a free run leaves the road — the strip must be straight); no speed value is asserted:
       the stock car's acceleration is not a Batmobile prediction, and comparing it to D-1 would be
       reading a stock car against a translated tune.
```

## 2.4 `BRAKE_SERPENTE` — stop from 60 km/h

```
GOAL: one take from 60 km/h to a full stop on tarmac, with the frame at rest and the trace, and no
      claim about the Batmobile's stopping distance.

PRE-CONDITIONS: DRIVE_SERPENTE PASS; the car is moving at 60 km/h; the strip is clear.

STEPS

### 1. Start the recording
    DO   um win record --exe JustCause3.exe --pid <pid> --out Working/Q/Q1/prove/brake1 --seconds 20
    SEE  exit 0; brake1.mkv, brake1.audio.raw, brake1.json exist
    IF NOT  no `.audio.raw` -> STOP

### 2. Brake (S, decoded REVERSE/BRAKE, CONTROLS.md rows 4–5)
    DO   um win drive --proc JustCause3 "key 0x53"
    SEE  `ok`
    IF NOT  `fail` -> STOP

### 3. Wait for the stop
    DO   sleep 6
    SEE  the command returns, exit 0
    IF NOT  re-run once

### 4. Capture the stop
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/serpente_stop.png
    SEE  the file exists and the HUD reads 0 km/h
    IF NOT  speed above 0 -> the car did not stop: repeat step 2 once, then STOP

### 5. Trace the speed
    DO   python Tools/scripts/qa1_hud.py trace --crops Working/Q/Q1/prove/work/hud --csv Working/Q/Q1/prove/brake1.csv --fps 5
    SEE  exit 0 and a CSV whose first row is > 40 km/h and last row is 0
    IF NOT  unlabelled glyph -> STOP and label it; a CSV that does not fall -> STOP (wrong take)

### 6. Write the stop time
    DO   python -c "import csv;r=list(csv.DictReader(open('Working/Q/Q1/prove/brake1.csv')));print(len(r),r[0]['kmh'],r[-1]['kmh'])"
    SEE  three values printed; write them on the RESULT line
    IF NOT  STOP

RESULT
    RESULT: PASS — 60→0 km/h in <n> frames — pid=<pid> — prove/brake1.mkv + .csv, shots/serpente_stop.png
    RESULT: STOP — step <n> — <the SEE that failed, quoted> — <artifacts so far>

TRAPS: no distance band is asserted. D-3's 101.5–110.2 m belongs to the Batmobile's brake torque
       (T-K1/T-K2) and cannot be scored on a stock car without repeating the same category error
       the plan already corrected.
```

---

## 3. What this run may and may not score

| item | scored? | why |
|---|---|---|
| every `DO` command runs and prints `ok` / exit 0 | **yes** | that is the card mechanic |
| every `SEE` string is the one the tool prints | **yes** | §2 rule 3 of `CARD_FORMAT.md` |
| every `IF NOT` reaches a bounded end | **yes** | no "try a few things" survives |
| RESULT line produced, PID on it | **yes** | the handover contract |
| turning circle / radius | **NO — not-yet-provable** | the Batmobile's radius comes from its lock and wheelbase. Measured 2026-11-07: `v05_driving.py --check` **exits 0 with 34/34 oracles** and prints `PASS D-5 band brackets the built times (0.80 / 0.60 s)`; the `T-ST7 RED` on the ledger line is the *built-vs-goal miss*, not a failed check. A green checker is still not test evidence (review 8299): it compares a document to its own generator. On a stock Serpente there is no translated lock to read |
| 0.25 s full-lock time | **NO — not-yet-provable** | same row: the target is BmAK's 220 °/s; the stock car's rack is the game's own and says nothing about it |
| 0–100 time, top speed, braking distance | **NO** | these are translated values (D-1/D-2/D-3); a stock car measures the stock car |
| capture / HUD / audio / kill mechanics | **yes** | identical on any `CCar` |

**How to record a not-yet-provable step**: the step is executed for the *mechanic*, and its value
column in `RESULTS.md` carries `not-yet-provable — <the row that settles it>` (here `T-ST7`, D-4,
D-5). It is **never** entered as `fail`, and never omitted.

---

## 4. The combat set is not-yet-provable

`FIGHT.md` does not exist, and the features behind it have no payload: `Builds/bm-RC4/receipt.json`
lists `cards_without_payload` = **B-12, B-17, B-18, B-19, B-20, B-25, B-26**
(`tmp/freebuff/reports/correction-8398-unshipped-cards.md` §3), and `BUILD_BATCHES.md` §4 gives
B-18…B-21 zero built values. B-15 has **three** meanings in the repo — the budget card is `done`
(`GRAB_BACKLOG.md:1955`), while `BUILD_BATCHES.md:234` proposes "a step B-15 (or a clause in B-13)"
for the HUD rows — so a card that names B-15 must point at `BUILD_BATCHES.md:234`, not at the done
row, and not at the riot card `Research/specs/B-15.md` (which `T-WP10` cites, and which is the one a
combat card means).

Consequence for this prove-set: combat steps are **not-yet-provable**, not failed, and `FIGHT.md`
is written only after those cards ship. A stock Serpente can fire JC3's own vehicle weapons, but
that proves JC3's weapons, not the Batmobile's rows — so it is not substituted here.

---

## 5. The failure log — one row per failure, one edit per row

Rules: a failure is recorded **during** the run with the exact `SEE` text; the card is **not** edited
mid-run (`CARD_FORMAT.md` §2.10); the edit is made after the session, one commit per card, with the
observation quoted in the commit. Nothing is marked "fixed" without a re-run.

| # | card | step | observed (`SEE` text) | class | smallest card edit | commit | re-run |
|---:|---|---|---|---|---|---|---|
| 1 | | | | | | | |
| 2 | | | | | | | |
| 3 | | | | | | | |

**Class definitions** (the only three allowed):

* **card fault** — the command, string, path or branch was wrong; edit the card.
* **environment** — mute, focus, window, dump, save state; fix the environment, re-run unchanged.
* **build/row** — a value or member the repo does not have; the card STOPs and the row is named;
  the card text does not change.

---

## 6. Run log (filled during the session, never before)

```
RUN: prove-serpente-1        date=<YYYY-MM-DD>   pid=<pid>
APPROVED_Q.txt: present? <yes|no>
P1 LAUNCH            RESULT: <line>
P2 LOAD_SAVE         RESULT: <line>
P3 SPAWN_SERPENTE    RESULT: <line>
P4 ENTER_EXIT        RESULT: <line>
P5 DRIVE             RESULT: <line>   peak=<n> km/h
P6 BRAKE             RESULT: <line>   <n> frames, <a>→<b> km/h
P7 SCREENSHOT        RESULT: <line>
P8 RECORD            RESULT: <line>   peak=<n>
P9 KILL              RESULT: <line>
ACCEPTANCE: <the line from §2, or "not met — help at <card> step <n> — <question>">
```

---

## 7. Revert

Deleting this file removes the prove-set cards. The five pre-existing cards it invokes
(`LAUNCH`, `LOAD_SAVE`, `SCREENSHOT`, `RECORD`, `KILL`) are **not** edited by this document; if a
run forces an edit, that edit names its own revert in the commit.
