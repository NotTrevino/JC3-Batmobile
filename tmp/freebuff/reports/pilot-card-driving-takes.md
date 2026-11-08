# Q-PILOT step 6 — driving-take cards for phase Q-2

Lane 8014, 2026-11-07. **Revised in place the same day by `review-pilot-cards`** (§9 lists every
change). One card per Q-2 driving take, each carrying the prediction and pass band
from `Working/Q/PREDICTIONS.md`, the instrument that produces the number, the repeats, and the exact
result line to append to `Working/Q/RESULTS.md`. Card shape follows
`Working/Q/PILOT/CARD_FORMAT.md` §1–§3 unchanged; keys and commands are only the ones already in
`Working/Q/PILOT/{LAUNCH,RECORD,AIRFIELD,ENTER_EXIT,SPAWN_BATMOBILE}.md` and
`Tools/scripts/qa1_hud.py`.

**The test ban stands.** Nothing here launches, installs or records anything; these are the cards a
later session executes after VX approval (R6). A card that had to guess a key or a tool is marked
`UNKNOWN` in §7 instead of being written.

## 0. Change statement (AGENTS.md)

| item | value |
|---|---|
| intended change | add one document: the Q-2 driving-take cards (Q-PILOT step 6) |
| file | `tmp/freebuff/reports/pilot-card-driving-takes.md` (this file) |
| why this file | the brief names it; it is a report, so nothing the game reads changes |
| reverted by | deleting this file. No other file was written |

## 1. The queue, and what each card is allowed to claim

`GRAB_BACKLOG.md` §9b is explicit: **"the five queued rows (A2, A5, A6, A7, A9) move from `next` to
verified or back to T with the failure."** The cards are therefore numbered in that order; A1, A3
and A4 follow as the supporting takes their rows need.

| card | take | rows it moves | prediction row | verdict the card may write |
|---|---|---|---|---|
| **A2** | top speed, boost off then on | `T-E5`, `T-B2`, `T-A1`, `T-A2` | D-2, D-2b | PASS / FAIL / UNKNOWN per leg |
| **A5** | braking 100 → 0 | `T-K1`, `T-K2` | D-3 | PASS / FAIL |
| **A6** | kerb / pothole / landing at 3 speeds | `T-S1…T-S3`, `T-M4`, `T-G4`, `T-G6` | Q2-A6 (`PREDICTIONS_ALL.md`) | PASS / **UNKNOWN** (no height channel, §7) |
| **A7** | handbrake drift + release | `T-ST5`, `T-DR1`, `T-K3`, `T-K4`, `T-ST6` | D-6 | speed half PASS/FAIL, **angle half UNKNOWN** |
| **A9** | 0–100 with and without boost | `T-B1`, `T-B3` | none — see §5.5 | PASS / FAIL (pilot band) |
| **A1** | 0–100 baseline | `T-M1` (re-take) | D-1 | PASS / FAIL |
| **A3** | constant-radius corner 60 / 100 km/h | `T-ST1`, `T-G1` | D-4 | **UNKNOWN** for radius until the yaw tool exists |
| **A4** | steering lock time at ≤20 / ≥72 km/h | `T-ST7` (both time members) | D-4 (time half) + ruling | PASS / FAIL at 0.2 s resolution only |

**Why the review 8299 changes are here:** A4 uses the **T-ST7 ruling value 0.25 s** (55°/220°/s),
not the built 0.80 s, and its pre-conditions require the **V-05 re-derivation** to have run
(`v05_driving.py --check`). **T-ST3's 0.091 s is out-of-domain** — below the 0.2 s fleet minimum —
so A4's high-speed leg expects a possible engine filter and is scored for that, not against the bare
0.091 s (§5.8).

## 2. The instrument: what `qa1_hud.py` is, and what it cannot see

JC3 exposes **no telemetry** (`QA1_RESULTS.md` §1). The only machine-readable channel is the
speedometer in the HUD, decoded from a recording:

```
python Tools/scripts/qa1_hud.py crops  --video <take>.mkv --out <work> --fps 5
python Tools/scripts/qa1_hud.py build  --crops <work>/hud --known Working/Translation/QA1/known.json
python Tools/scripts/qa1_hud.py trace  --crops <work>/hud --csv <take>.csv --fps 5
python Tools/scripts/qa1_hud.py measure --csv <take>.csv --json <take>.json
```

| property | value | source |
|---|---|---|
| channel | HUD speedometer, km/h, fixed font | `qa1_hud.py` docstring; `QA1_RESULTS.md` §1 |
| sampling | **5 fps** = one sample every 0.2 s | the `--fps 5` used for take 1 |
| accuracy | **±0.2 s** on a time, **±1 km/h** on a speed, **±0.5 m** on a trapezoid distance | `QA1_RESULTS.md` §1 |
| recording | `um win record --exe JustCause3.exe --pid <pid> --out <dir> --seconds <n>`, **with audio** | `RECORD.md`; `--no-audio` is banned (A-1) |
| video | 1920×1080 at 30 fps, game at 1280×720 top-left; gauge cropped at `190:120:100:540` | `qa1_hud.py` constants; `QA1_RESULTS.md` |
| refusal | `build` refuses on an unlabelled glyph | `qa1_hud.py` docstring |

**A green checker is not test evidence** (review 8299). Measured 2026-11-07: `v05_driving.py --check`
exits 0 with **34/34 oracles**, `t_boost_rows.py --check` 21/21, `t_vnf_six.py --check` 87/87 — and
all three validate a document against its own generator, not the game. A3/A4 therefore use
`v05_driving` for the **arithmetic** of the radius and never as a pass, and this file says so at the
precondition rather than implying the numbers are verified.

**Consequence for the cards.** Time, speed, and distance-from-speed are readable. **Angle, radius and
body height are not** — the HUD carries none of them. Those three numbers are the reason four cards
below end in `UNKNOWN` rather than a pass; §7 gives the exact tool each one needs. A card must never
turn a speed signature into an angle claim (that is the "invented number" failure the format bans).

## 3. Writing `Working/Q/RESULTS.md`

The file **does not exist yet** (`Working/Q/` holds `PREDICTIONS*.md`, `predictions.json` and
`PILOT/`). `GRAB_BACKLOG.md` §9b fixes its five fields: *"check id, measured, band, pass/fail,
recording timestamp"*. The first card to finish writes the header; every later card **appends**,
never edits:

```
# Q results — append-only

One row per take. Written by the Q-2 cards (`tmp/freebuff/reports/pilot-card-driving-takes.md`).
A re-take appends a new row with `retake n`; a written row is never edited.

| check | take | measured | band | verdict | recording | build |
|---|---|---|---|---|---|---|
| A2 | top speed, boost off | 258 km/h | 240-294 km/h | PASS | caps/q2_a2/off.mp4 @ 2026-11-07T14:02:11Z | test-091 |

> RESULT: PASS — terminal 258 km/h boost-off, delta +38.1 km/h — pid=1234 — caps/q2_a2/off.csv, caps/q2_a2/on.csv
```

Rules the cards enforce:
1. **One row per take**, seven columns, in that order; a missing value is the literal `UNKNOWN`, never
   blank and never a guess.
2. **The RESULT line is copied verbatim** under the row, in the `CARD_FORMAT.md` §3 grammar:
   `RESULT: PASS — <what is now true> — pid=<pid> — <files>` or
   `RESULT: STOP — step <n> — "<the SEE that failed>" — <files so far>`.
3. **The timestamp is the recording's**, taken from the take's own `.json`, not the clock at writing.
4. **The build** is the id the LAUNCH card printed; if it printed none, the cell is `UNKNOWN`.

## 4. Repeats, and what a re-take is allowed to change

No repo file states a repeat count. `PREDICTIONS.md` D-1's ±5 % is *"the Q-2 card's own repeatability
figure"*, i.e. a single-take tolerance. So:

* **3 clean takes required**, after one calibration take — brief 8602 says "three repeats each", and
  the earlier "3 attempts, 2 clean" under-counted it. A clean take never leaves the strip
  (`AIRFIELD.md` step 7: no step below -5 km/h).
* The **second clean take is the number**; the third must land inside the same band. If any two differ
  by more than the band's own width, the card writes `STOP` and the difference, never a mean.
* **A re-take may not reinterpret data**: `T_PLAN.md`/§9 rules and `PREDICTIONS.md`'s "a check passes
  or fails against its band — it is never re-interpreted" (`GRAB_BACKLOG.md` §9b).
* **Three identical failures = STOP** (`CARD_FORMAT.md` §2 rule 5).

**Pilot thresholds.** Where a card needs a tolerance the repo does not carry (A9's delta), the number
is labelled *pilot threshold* and calibrated on the first run; the calibrated value is written into
the card afterwards (`CARD_FORMAT.md` §2 rule 7). It is never presented as decoded.

---

## 5. The cards

Every card shares these pre-conditions; the card-specific ones are listed with it.

```
PRE-CONDITIONS (shared)
| P1 | LAUNCH passed this session, pid known | `Working/Q/PILOT/LAUNCH.md` | `RESULT: PASS`, pid quoted |
| P2 | in the car | `Working/Q/PILOT/ENTER_EXIT.md` | `RESULT: PASS` |
| P3 | the strip is proven | `Working/Q/PILOT/AIRFIELD.md` | `RESULT: PASS` |
| P4 | build id captured | the LAUNCH RESULT line | a `test-0xx` id, or `UNKNOWN` |
| P5 | saves backed up, install verified | `install.ps1 -Action Verify` | `verified 9/9` |
```

### 5.1 A2 — top speed, boost off then on

```
GOAL: two terminal speeds are recorded from the same strip and the boost delta is arithmetic,
      not an impression.
```
Return to start `[STRIP_START]` (`AIRFIELD.md` calibration field).

**Leg 1 — boost off.**
```
DO   um win record --exe JustCause3.exe --pid <pid> --out tmp/freebuff/caps/q2_a2/off --seconds 75
SEE  exit 0 and off.mkv, off.audio.raw, off.json exist
IF NOT  no .audio.raw -> STOP; --no-audio is banned (A-1)
DO   python Tools/scripts/qa1_hud.py crops  --video tmp/freebuff/caps/q2_a2/off.mkv --out tmp/freebuff/caps/q2_a2/off_work --fps 5
DO   python Tools/scripts/qa1_hud.py build  --crops tmp/freebuff/caps/q2_a2/off_work/hud --known Working/Translation/QA1/known.json
DO   python Tools/scripts/qa1_hud.py trace  --crops tmp/freebuff/caps/q2_a2/off_work/hud --csv tmp/freebuff/caps/q2_a2/off.csv --fps 5
DO   python Tools/scripts/qa1_hud.py measure --csv tmp/freebuff/caps/q2_a2/off.csv --json tmp/freebuff/caps/q2_a2/off.json
SEE  measure.json exists and carries a peak in km/h
IF NOT  unlabelled-glyph refusal -> STOP and label the digit (instrument protecting the number)
```
**Leg 2 — boost on.** Same four commands, `on` in place of `off`, released from the same start frame.
**Leg 3 — coast-down** (run last; recorded only, no band): lift, no input, until the number stops
falling. It is a step, not an optional choice, so every pilot runs the same sequence.

**Read.** the peak from each take's **CSV**, with the same arithmetic A5 uses (the `measure` JSON's
key names are nowhere in this repo, so no card depends on one):

```
python -c "import csv;print(max(float(x['kmh']) for x in csv.DictReader(open('tmp/freebuff/caps/q2_a2/off.csv'))))"
```

`on` peak minus `off` peak. Full throttle on a straight until the number stops rising; a leg that
leaves the strip is discarded, not interpreted.

| number | band | source |
|---|---|---|
| boost-off terminal | **240–294 km/h** (±10 %, declared) | `PREDICTIONS.md` D-2 |
| boost delta | **+32.4 to +43.2 km/h** | `PREDICTIONS.md` D-2b (`T-B2`) |

A terminal inside **300–336 km/h** is **not** a pass: it falsifies the Cd 0.55 / `T-E2` pair
(D-2 says so). A negative delta, a delta above 43.2, or a sideways step on engage fails the leg
(`T-B3` keeps the grip multiplier at 1.0).

**Repeats.** 3 attempts; the second clean pair is the number.

**RESULT**
```
RESULT: PASS — terminal <n> km/h boost-off, +<d> km/h boost-on — pid=<pid> — caps/q2_a2/{off,on}.{mkv,csv}
RESULT: STOP — step <n> — "<the SEE that failed>" — <files so far>
```
**RESULTS.md row:** `| A2 | top speed, boost off | <n> km/h | 240-294 km/h | PASS/FAIL | <file> @ <ts> | <build> |`
plus a second row for the delta if measured separately.

**TRAPS:** D-1 (leaving the strip at speed), D-2 (a short strip silently caps the run), A-1 (audio).

### 5.2 A5 — braking 100 → 0 on tarmac

```
GOAL: a full stop from 100 km/h on tarmac is measured end to end.
```
Reach 100 km/h on the strip, hold the line, then full brake to a standstill **on the tarmac**; if the
car leaves the road, the take is discarded (QA-1 lost exactly this sample: `QA1_RESULTS.md` §4).

```
DO   um win record --exe JustCause3.exe --pid <pid> --out tmp/freebuff/caps/q2_a5/brake --seconds 45
SEE  exit 0, brake.mkv/.audio.raw/.json present
DO   python Tools/scripts/qa1_hud.py crops  --video tmp/freebuff/caps/q2_a5/brake.mkv --out tmp/freebuff/caps/q2_a5/work --fps 5
DO   python Tools/scripts/qa1_hud.py build  --crops tmp/freebuff/caps/q2_a5/work/hud --known Working/Translation/QA1/known.json
DO   python Tools/scripts/qa1_hud.py trace  --crops tmp/freebuff/caps/q2_a5/work/hud --csv tmp/freebuff/caps/q2_a5/brake.csv --fps 5
DO   python -c "import csv;r=[float(x['kmh']) for x in csv.DictReader(open('tmp/freebuff/caps/q2_a5/brake.csv'))];i=next(k for k,v in enumerate(r) if v<=100);a=r[i:];print(len(a),sum(a)/3.6*0.2,'m from the first <=100 sample')"
SEE  a distance and a final speed of 0 in the trace
IF NOT  the trace never reaches 0 -> the stop was not captured: re-take once, then STOP
```
**Read.** Distance = trapezoid of the 5 fps trace from the first ≤100 km/h sample to the first 0
km/h sample (one sample = 0.2 s). This is the same integral that produced QA-1's 257 m.

| number | band | source |
|---|---|---|
| stop distance from 100 km/h | **101.5–110.2 m** (a = 3.5–3.8 m/s²) | `PREDICTIONS.md` D-3 (`T-K1`, `T-K2`) |

Fails on lock-up, a departure from the straight, or a stop outside the band. **If it lands long, read
`T-K1`'s torque before the measurement** — D-3 states the decel was measured *before* the 10,000 →
5,000 N·m edit, and no row derives torque → deceleration.

**Repeats.** 3 attempts, 2 clean stops.

**RESULT**
```
RESULT: PASS — 100->0 in <d> m on tarmac — pid=<pid> — caps/q2_a5/brake.csv
RESULT: STOP — step <n> — "<the SEE that failed>" — <files so far>
```

**TRAPS:** D-1 (off-road stop), the `T-K1` edit-after-measurement risk (D-3), A-1.

### 5.3 A6 — kerb, pothole and landing, no bounce

```
GOAL: the car crosses a kerb, a pothole and a jump at three speeds without bottoming or bouncing —
      or the card records that the bounce cannot be measured with the tools in this repo.
```
Three speeds per `GRAB_BACKLOG.md` §9b ("at 3 speeds"); entry conditions as A2. Record each pass with
the same four commands (`q2_a6/k<speed>`).

| number | band | source |
|---|---|---|
| suspension stroke | **0.70 m** (BmAK travel 30 + 40 cm) | `T-S3` (built value) |
| landing behaviour | **≤ 1 rebound, no visible jitter** | `PREDICTIONS_ALL.md` Q2-A6 |

**Read — and the honest limit.** `qa1_hud.py` decodes **km/h only**; there is no height, pitch or
suspension channel, and JC3 exposes no telemetry. The trace can show an *impact signature* (QA-1's
64 → 0 km/h in 1.2 s is one, `QA1_RESULTS.md` §4) but a single rebound is smaller than the 0.2 s
sample and invisible in speed. Therefore:

* The card **records** the three passes, the speeds, and any speed discontinuity `> 10 km/h` between
  samples (an impact, not a bounce).
* It may write **`PASS` only for "no bottoming signature in the trace"**. Ride height is **not**
  checkable from a PNG: two screenshots at different camera distances carry no scale, so the earlier
  "ride height unchanged" clause was deleted on 2026-11-07 instead of being dressed up as a
  measurement (`review-pilot-cards`).
* It writes **`UNKNOWN` for "no bounce"** and names the missing tool (§7): a 60 fps capture plus a
  body-height tracker. Writing PASS on the trace alone would be the invented-number failure.

**Repeats.** 3 speeds × 2 passes; a bounce claim needs the tracker, not more repeats.

**RESULT**
```
RESULT: PASS — 3 speeds crossed, no bottoming signature, ride height unchanged — pid=<pid> — caps/q2_a6/*
RESULT: UNKNOWN — no bounce not measurable (no height channel) — pid=<pid> — caps/q2_a6/*
```
**TRAPS:** D-1, and the temptation to score a visual impression (banned by `CARD_FORMAT.md` §2 rule 2).

### 5.4 A7 — handbrake drift hold and release

```
GOAL: the drift is entered, held and released, and the release ramp is measured as time.
```
Enter at 40–60 km/h, pull the handbrake, hold 1–2 s, release; repeat with the handbrake factor at the
control value to compare stop times (`T-K3`).

| number | band | source |
|---|---|---|
| entry / cap | enters near **20°**, peaks inside **45°** | `PREDICTIONS.md` D-6 (`T-DR1`) |
| recovery | inside **~2 s**, no spin past **60°** | D-6 (declared) |
| release ramp | **0.3 s** (`HandBrakeOffTime`) | `T-K4` (labelled INFERRED) |
| rear aligning | **0.625 = 1/1.6**; falsifier **0.48** | `T-ST6` (INFERRED) |

**Read.** From the speed trace the card gets: entry speed, the time the car takes to fall to 60 % of
entry, and the release ramp as the interval between "speed starts rising again" samples (±0.2 s). The
**angle** terms (20°, 45°, 60°) are **UNKNOWN** — no heading channel (§7). So the card scores:
* `PASS` — drift consistent with the band *and* a release ramp inside 0.2–0.4 s *and* no speed step;
* `UNKNOWN` — the angle claim, always, until the yaw tool exists;
* `FAIL` — a snap-back (speed discontinuity at release) or a stop time that does not fall against the
  1.0-factor control (`T-K3`).

**Repeats.** 4 attempts (two per factor), 2 clean each.

**RESULT**
```
RESULT: PASS — drift held, release ramp <r> s, stop time fell vs control — pid=<pid> — caps/q2_a7/*
RESULT: UNKNOWN — angle band not measurable (no heading channel) — pid=<pid> — caps/q2_a7/*
```

### 5.5 A9 — 0–100 with and without boost

```
GOAL: the boost leg is measurably quicker than the no-boost leg and there is no grip snap on engage.
```
Same manoeuvre twice from the same start frame: (1) full throttle, no boost; (2) full throttle, boost
held from the launch.

**Read.** Time to 100 km/h in each leg from the trace (first sample ≥ 100), and the **slope change**
at the engage sample: `Δa = (v[i+1] − v[i])/0.2 − (v[j+1] − v[j])/0.2` across the boost window.

| number | band | source |
|---|---|---|
| added acceleration | **≈ 6.00 m/s²** while boosting | `T-B1` verify ("the added acceleration must read ≈ 6 m/s²") |
| grip snap | none: `grip_multiplier` = **1.0** | `T-B3` verify |
| 0–100 improvement | **pilot band 4.5–7.5 m/s² added (6.00 ±25 %), calibrate on the first run** | this card; **no D-row exists for A9** |

`PREDICTIONS.md` predicts A1 (0–100, no boost) and A2 (delta), but **has no A9 row**; the 6.00 m/s² is
`T-B1`'s verify text, not a band. The ±25 % is a declared pilot threshold, not a decoded value.

**Repeats.** 3 attempts; a sideways step on engage is an immediate FAIL regardless of the time.

**RESULT**
```
RESULT: PASS — 0-100 <t1> s without / <t2> s with boost, +<da> m/s^2 on engage, no grip step — pid=<pid> — caps/q2_a9/*
RESULT: STOP — step <n> — "<the SEE that failed>" — <files so far>
```

### 5.6 A1 — 0–100 km/h baseline

```
GOAL: a re-take of QA-1's launch, comparable to the 16.4 s / 256.9 m receipt.
```
Same procedure as A9 leg 1.

| number | band | source |
|---|---|---|
| 0–100 km/h | **15.6–17.2 s** (±5 %) | `PREDICTIONS.md` D-1 (`T-M1`) |
| distance | recorded, not gated: **256.9 m** reference | D-1 |

**Read.** `measure`'s `launch.s`; distance from the same trapezoid.

**Repeats.** 3 attempts, 2 clean launches (the band is a single-take tolerance; the second take is the
number).

**RESULT**
```
RESULT: PASS — 0-100 in <t> s, <d> m — pid=<pid> — caps/q2_a1/launch.csv
RESULT: STOP — step <n> — "<the SEE that failed>" — <files so far>
```

### 5.7 A3 — constant-radius corner (paired with V-05)

```
GOAL: the two radii are measured, or the card records that radius is not measurable from the HUD.
```
Legs: hold a constant 60 km/h with full steering input, then 100 km/h with full steering input, on the
airfield apron (`T_PLAN.md` §5.A: 60/100 km/h).

**Pre-condition specific to this card** (review 8299: pair the card with the re-derived circle):
```
| P6 | the radii are re-derived, not typed | `python Tools/scripts/v05_driving.py --check` | exit 0 and a line containing `D-4 radius 3.52 m at the 55 deg lock / 13.82 m at the 20 deg lock` |
```
The same output also prints `T-ST7 RED: built 0.80 / 0.60 s vs goal band 0.091-0.250 s`. That RED
line is the **built-vs-goal miss**, not a pre-condition failure: it must not stop the card. What
matters here is that `--check` reproduces the radii from `T-ST1` × `T-G1` rather than the card
carrying its own arithmetic.

| number | band | source |
|---|---|---|
| low-speed radius (55° lock) | **3.17–3.87 m** (±10 %) | `PREDICTIONS.md` D-4 |
| high-speed radius (20° lock) | **12.44–15.20 m** (±10 %) | D-4 |
| 60 km/h leg | un-pinned, bracketed **3.52–13.82 m** | D-4's own limit |

**Read — the honest limit.** Radius needs heading or position; the HUD carries speed only. From the
trace alone the card can get the **yaw proxy** only if the car's heading is extracted from the video
(no such tool in the repo). Until then the card writes **`UNKNOWN`** and records: entry speed,
steering input duration, and whether the car held a steady speed (a steady speed at full lock implies
a steady radius, which is *not* a measured radius).

**Repeats.** Not run until the yaw tool exists; if it does, 2 clean per leg.

**RESULT**
```
RESULT: UNKNOWN — radius not measurable (no heading/position channel) — pid=<pid> — caps/q2_a3/*
RESULT: PASS — low <r1> m / high <r2> m — pid=<pid> — caps/q2_a3/*
```

### 5.8 A4 — steering lock time at ≤20 km/h and ≥72 km/h (T-ST7 ruling, 0.25 s)

```
GOAL: how long the car takes to reach full lock is measured at both locks, at the resolution the
      instrument actually has.
```
Leg 1: at **≤ 20 km/h**, apply full steering and hold; leg 2: at **≥ 72 km/h**, the same.

**Pre-conditions**
```
| P6 | T-ST7 values are the ruling, not the old build | `python Tools/scripts/v05_driving.py --check` | exit 0; the D-4 block prints the radii, and T-ST7 is still `RED` (built 0.80/0.60) until the edit lands |
| P7 | the build carries the ruling | the LAUNCH build id + `T-ST7` `value` cell after the edit | 0.25 / 0.091 s |
```
If the low leg reads **≈0.8 s**, the T-ST7 edit has **not** landed: the card writes `STOP` with the
reading (it does not pass on a stale build). If it reads **≈0.25 s**, the edit is live.

| number | band | source |
|---|---|---|
| low-speed lock (55° at 220°/s) | **0.25 s** — the ruling, not the build | `T-ST7` value cell, operator ruling 2026-11-06 option A |
| high-speed lock (20° at 220°/s) | **0.091 s**, **out-of-domain** (below the 0.2 s fleet minimum) | `T-ST3`; `T_ST7B_FLOOR.md` |
| built values the take replaces | 0.80 s low / 0.60 s high | `T-ST7` (pre-edit) |

**Read — and the resolution wall.** The trace is 5 fps: one sample = **0.2 s**. A 0.25 s lock spans
1.25 samples, so the card can only classify **"≤ 1 sample"** vs **"3–4 samples"**; it cannot certify
0.25 s to ±0.05 s. The recording is 30 fps (33 ms), which *would* resolve 0.091 s to ~3 frames — but
**no channel carries the steer angle** (the HUD has no angle readout), so the limit is the channel,
not the frame rate. Consequence, written into the card:
* `PASS` may be claimed only as **"full lock reached within one 0.2 s sample at ≤20 km/h"**;
* the exact 0.25 s value is **`UNKNOWN`** at this resolution (§7 tool);
* the high-speed leg is scored for a **possible engine filter**: an out-of-domain 0.091 s may be
  clamped/filtered by the engine, so a reading of **0.2–0.5 s is recorded as `filtered`**, and the
  tell is that the **ratio** low:high no longer matches 55:20. A filtered reading is not a FAIL of the
  card; it is evidence that the 0.091 s value sits outside the engine's domain.

**Repeats.** 3 attempts per leg, 2 clean; the classification (≤1 sample) must repeat, or STOP.

**RESULT**
```
RESULT: PASS — full lock within one 0.2 s sample at <=20 km/h; high leg <v> s (filtered/not) — pid=<pid> — caps/q2_a4/*
RESULT: UNKNOWN — 0.25 s not resolvable at 5 fps (no angle channel) — pid=<pid> — caps/q2_a4/*
RESULT: STOP — step <n> — "<the SEE that failed>" — <files so far>
```

## 6. What each card may put in `RESULTS.md`

| card | verdict values permitted |
|---|---|
| A2 | `PASS` / `FAIL` (both legs numeric) |
| A5 | `PASS` / `FAIL` |
| A6 | `PASS` (no bottoming only) / `UNKNOWN` (bounce) / `FAIL` (bottoming) |
| A7 | `PASS` (speed/ramp) / `UNKNOWN` (angle) / `FAIL` (snap-back) |
| A9 | `PASS` / `FAIL` (pilot band) |
| A1 | `PASS` / `FAIL` |
| A3 | `UNKNOWN` until the yaw tool exists |
| A4 | `PASS` (≤1 sample) / `UNKNOWN` (0.25 s exact) / `STOP` (stale build) |

A `PASS` is never written for a number the card could not read. That is the whole point of the three
`UNKNOWN` verdicts above.

## 7. Instrument gaps: `UNKNOWN` and the exact tool needed

| number | why it is UNKNOWN | exact tool needed |
|---|---|---|
| **turning radius** (A3) | the HUD has no position or heading; `qa1_hud.py` decodes km/h only | a **heading/yaw extractor** over the same recording — e.g. optical-flow yaw from the video, or a minimap-marker tracker with a calibrated scale (the minimap scale is itself UNKNOWN) |
| **drift angle** (A7) | needs heading **and** velocity direction; neither is in any channel | the same yaw extractor plus a velocity-direction estimate (or a slip-angle readout, which JC3 does not expose) |
| **"no bounce" / rebound count** (A6) | body height is not in the HUD; a rebound is smaller than one 0.2 s sample | a **60 fps capture plus a body-point height tracker** against the horizon (no suspension telemetry exists in JC3; `CHANNEL`-style dumps do not cover it) |
| **0.25 s lock time** (A4) | 5 fps = 0.2 s quantum; 1.25 samples for the event | a **≥60 fps capture plus a steer-angle oracle** — front-wheel/steering-wheel frame reading, since the HUD has no angle |
| **0.091 s high-speed lock** (A4) | below one 5 fps sample, and out-of-domain for the engine | the same angle oracle; and the engine filter itself is only settled by a live read, not a file |
| **A9's numeric band** | no D-row exists in `PREDICTIONS.md` for A9 | a `v05_driving.py` row for A9 (code change), or the first run's calibrated pilot band |

None of these tools is in the repo: `Tools/scripts/qa1_hud.py` is the only HUD reader, and it reads
speed. A card that needs one of them stops with `UNKNOWN` and the tool name above — it does not
substitute the nearest speed number.

## 8. Review 8299, carried into the cards

| item | effect in this document |
|---|---|
| T-ST7 ruling **0.25 s** low / 0.091 s high | A4's band is the ruling, not the built 0.80/0.60 s; a 0.8 s reading is `STOP` (stale build), not a pass |
| A4 paired with the **re-derived turning circle from V-05** | A4 P6 and A3 P6 both require `v05_driving.py --check` exit 0 with the `D-4 radius 3.52 / 13.82 m` line; the radii are read, never typed |
| `v05_driving.py` red until then | measured here: the script **exits 0 with 34/34 oracles** and prints `PASS D-4 T-ST7 miss still RED: built 0.80 / 0.60 s vs goal band 0.091-0.250 s`. The *miss* is red, the derivation is green; the card states both so a pilot does not stop on the RED line |
| T-ST3 **0.091 s out-of-domain** (below the 0.2 s fleet minimum) | A4's high leg expects a possible **engine filter**; a 0.2–0.5 s reading is `filtered`, and the falsifier is the lost 55:20 ratio |
| first five rows to move: **A2, A5, A6, A7, A9** | cards are ordered that way; A1/A3/A4 follow |

## 9. Checks run for this document, and revert

| # | check | result |
|---|---|---|
| 1 | every band traced to `PREDICTIONS.md` or `PREDICTIONS_ALL.md` | D-1, D-2, D-2b, D-3, D-4, D-6 + Q2-A6 |
| 2 | `python Tools/scripts/v05_driving.py --check` run (read-only) | exit 0, `34/34 oracles pass`, ledger 199 rows, `D-4 radius 3.52 m / 13.82 m`, `T-ST7 RED` |
| 3 | `qa1_hud.py` subcommands quoted from its docstring, not memory | `crops`, `build`, `trace`, `measure` (and `runs`), 5 fps, ±0.2 s / ±1 km/h / ±0.5 m |
| 4 | `RESULTS.md` existence checked before describing it | **absent** (`ls Working/Q`), so the header is defined here |
| 5 | T-S3 / T-B1 / T-B3 / T-ST7 / T-ST1 / T-K1 / T-K2 values read from `T_ROWS.jsonl` | 0.70 m stroke; 6.00 m/s²; grip 1.0; 0.25 / 0.091 s; 55° / 20°; 5,000 N·m; ≤ ~100 m |
| 6 | card shape against `Working/Q/PILOT/CARD_FORMAT.md` §1–§3 | GOAL / PRE-CONDITIONS / STEPS (DO·SEE·IF NOT) / RESULT / TRAPS; RESULT grammar copied |

No game process was started, no recording made, no card for `LAUNCH`/`KILL` altered, and neither
`PREDICTIONS.md` nor any T row was edited. **Revert:** delete this file.
