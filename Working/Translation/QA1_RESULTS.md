# QA-1 — the driving take, measured

**Status:** one take, one clean acceleration run, one partial braking sample. The instrument now
exists (`Tools/scripts/qa1_hud.py`) and produces a full speed trace from the HUD, so every later
take is a re-run of four commands instead of a manual frame hunt.

```
take        E:/Modding/JustCause3/_grab/qa1/take1.mkv   (outside the repo: it is gameplay footage)
            3:42.13, 30 fps, 1920x1080 with the game at 1280x720 top-left
recorded    2026-10-22 17:42:44 - 17:52:44
build       test-085 (35 edits, installed and verified 9/9 before the run)
instrument  Tools/scripts/qa1_hud.py   (crops -> build -> trace -> measure)
trace       Working/Translation/QA1/tail_trace.csv     234 samples, 167.4-214.0 s at 5 fps
receipt     Working/Translation/QA1/qa1_measure.json
```

## 1. How the HUD becomes a number

JC3 exposes no telemetry. The speedometer is drawn at a fixed position with a fixed font, so the
take is sampled at 5 fps into 190x120 crops of the gauge, the digit band is isolated, and the ten
digit shapes are learned from frames the operator read by eye (`Working/Translation/QA1/known.json`,
22 frames). The whole take then decodes without a single hand-read frame.

Accuracy: **±0.2 s** (one sample) on times, **±0.5 m** on distances from the trapezoid integral,
**±1 km/h** from the HUD's own rounding. Everything below is inside those bounds.

## 2. The run

| t (s) | 168 | 170 | 172 | 174 | 176 | 178 | 180 | 182 | 184 | 186 | 188 | 190 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| km/h | 0 | 0 | 6 | 24 | 41 | 59 | 68 | 76 | 85 | 94 | 106 | 117 |

| t (s) | 192 | 194 | 196 | 198 | 200 | 202 | 204 | 206 | 208 | 210 | 212 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| km/h | 126 | 133 | 137 | 125 | 103 | 105 | 106 | 92 | 83 | 61 | 30 |

| measurement | value |
|---|---|
| 0-60 km/h | **7.4 s** |
| 0-100 km/h | **16.4 s** (moving at 170.8 s, 100 at 187.2 s) |
| distance to 100 km/h | **257 m** |
| peak | **138 km/h** at 196.2 s, still climbing when the brake went on |
| peak acceleration | **3.06 m/s²** at 21-26 km/h, then decaying |

Acceleration by speed: 2.4 m/s² at 43 km/h, 1.8 at 60, 1.1 at 71, 1.25 at 80-89, 0.83 at 93,
2.36 at 102, 1.5 at 127, 0.28 at 133. The step **up** to 2.36 at 102 km/h cannot be an upshift
(an upshift lowers wheel torque), so it is road profile or a boost — the take does not separate them.

## 3. The gearbox cross-check (T-E4)

Shift speeds computed from the built gearbox — ratios 3.15/1.94/1.44/1.15/0.94, final drive 5.1401,
rolling radius 0.68275 m — at the edited 4,200 rpm:

| gear | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| km/h at 4,200 rpm | 66.8 | 108.4 | 146.1 | 182.9 | 223.7 |

The acceleration trace has its first knee at **67 km/h**, which is the gear-1 shift point to within
the sampling error. Later knees at 94 and 133 km/h sit below the predicted 108 and 146 and are not
separated from the road's crests and dips. **Conclusion:** the 4,200 rpm schedule is active in first
gear; a full shift-point check needs an engine-rpm channel, and JC3's only one is audio, which this
take does not have (`um win record --no-audio`).

## 4. Braking (T-K1)

| segment | time | distance | deceleration |
|---|---|---|---|
| 138 → 100 km/h, tarmac | 3.0 s | ~99 m | **3.5 m/s² average** (the last 122 → 100 at 3.82) |
| 83 → 61 km/h, on grass | 1.6 s | 32 m | 3.82 m/s² |
| 64 → 0 km/h, t=211.4-212.6 | 1.2 s | 9.8 m | 14.8 m/s² — an **impact**, not braking |

The car left the road at ~106 km/h around t=203 (frames 203-211 are vegetation), so **100 → 0 on
tarmac was not captured**. At the measured 3.5-3.8 m/s² a 100 km/h stop needs ~100 m; test-083 carried
10,000 Nm of brake torque at 4,000 kg, roughly a third of that deceleration, so T-K1's direction is
visible but its pass condition ("shorter than test-083 at the same pedal") is unmeasured.

## 5. What this take closes, and what it does not

| row | verify cell | state after this take |
|---|---|---|
| T-M1 | 0-100 km/h time | **measured**: 16.4 s, 257 m at the built 6,000 kg |
| T-E1 | top speed in the rpm band 800/2800/4500 | **measured**: 138 km/h, drag-limited (gearing would allow 240) |
| T-E4 | shift points at 4,200, no hunting | **partial**: first shift at 67 km/h matches; no hunting seen; later shifts unresolved |
| T-K1 | stopping distance from 100 km/h | **partial**: 3.5-3.8 m/s² measured; stop distance contaminated by the off-road exit |
| T-M2, T-M3 | yaw response / balance | not tested — no controlled steering input in this take |
| T-S1, T-S2, T-M4 | kerb, pothole, landing | not tested |
| T-G5 | low-speed grip probe | not tested |
| T-LG*, T-AU*, T-FX*, T-DM* | night beams, pitch, window break, pursuit | not tested |

The take is one continuous run from a standstill to 138 km/h and off the road, so it answers the
acceleration question and half the braking question, and nothing else. The remaining cells each
need a prescribed manoeuvre — the list is in `T5_BUILD.md` §3 and is unchanged except for the two
rows above.

## 6. Reproduce

```
cd E:/Modding/JustCause3/_grab/qa1
python ../../JC3-Batmobile/Tools/scripts/qa1_hud.py crops --video take1.mkv --out work --fps 5
python ../../JC3-Batmobile/Tools/scripts/qa1_hud.py build --crops work/hud \
       --known ../../JC3-Batmobile/Working/Translation/QA1/known.json
python ../../JC3-Batmobile/Tools/scripts/qa1_hud.py trace --crops work/hud --csv trace.csv \
       --fps 5 --from 160 --to 220
python ../../JC3-Batmobile/Tools/scripts/qa1_hud.py measure --csv trace.csv --json measure.json
```

`build` refuses to trace until every glyph in the take has a label, so a take with an unseen digit
fails loudly instead of producing a wrong number.

## 7. Queue — testing is last; the first take is written down, not run (2026-10-23)

Nothing below has been driven. Stage S5 is last in this project on purpose; this entry only pins
the **first** take while it is fresh, so the queue cannot drift into work being reported as done.

| field | value |
|---|---|
| take | **A2 — airfield top-speed run, boost off then on** (first in queue) |
| rows it can fail | **T-B2** (test-088's `extra_top_speed` 40), T-E5, T-A1 |
| build when run | test-088 (live; 4/4 read back through the `.toc`) |
| entry conditions | flat airfield, straight, dry, no traffic; one manoeuvre per take (§9) |
| legs | (1) full throttle, **boost off**, hold the straight until the number stops rising — terminal speed and the distance from the threshold line; (2) reset below the entry speed, repeat with **boost on**; (3) coast down without input for the coast-down distance |
| exit conditions | straight exhausted, or the number drops twice without an input |
| pass (quoted from T-B2's `verify` cell) | "A2: airfield top-speed run, boost off then on — terminal speed rises while boosting, delta recorded" — the measured delta is then compared against the built 40 km/h |
| instrument | `qa1_hud.py crops → build → trace → measure` (four commands, §6) |
| on a missed window | **re-take**; the data is never reinterpreted (§9) |

Queued behind it, in `T_PLAN.md` §5.A order: A5 (braking 100 → 0), A9 (0–100 with and without
boost), A7 (drift release, the gate for T-ST5 which needs no build). A8 requires a take recorded
**with audio**.
