# AIRFIELD — find and prove the straight test strip

> change 2026-11-07 (review-pilot-cards): step 7 printed `max()` of the sample-to-sample deltas, so
> a positive gain always satisfied `> -5` and the check could not fail. It now prints `min()` and
> passes only when no delta is below -5 km/h. Nothing else changed.

GOAL: a repeatable straight, flat, dry, traffic-free strip where a take can run 600 m or more
without leaving the road, with its start point archived so the next session returns to the same spot.

WHERE THE STRIP IS — AND WHAT THE REPO DOES NOT SAY
* QA-1's take was driven at "the airfield" (`Research/specs/Q-2.md`, card Q-2: "driving takes at the
  airfield"; `GRAB_BACKLOG.md:1473`), and the take conditions are stated: "flat airfield, straight,
  dry, no traffic; one manoeuvre per take" (`QA1_RESULTS.md` §7, A2 entry conditions).
* **The coordinates are not in this repo.** `grep -i "airfield|airstrip|falco|coordinate"` over
  `MODLOG.md` gives no location row, and `QA1_RESULTS.md` has no location field — it records the
  take time, build, instrument and measurements only. **The airfield coordinates used by QA-1 are
  UNKNOWN here.**
* The only airfield asset named anywhere in the repo is a DLC location,
  `dlc/mech_land_assault/locations/island/dlc2_processing_facility_airstrip.*`
  (`Research/JC3Grab/INDEX.jsonl`). Whether that is QA-1's airfield is **UNKNOWN** — it is a
  `dlc_win64` map asset, nothing ties it to the 2026-10-22 take.
* Therefore this card does **not** navigate by coordinates. It navigates once (calibration), then
  proves the strip **numerically from the take itself**, which is the only location fact the repo can
  produce: a straight run holds throttle without a speed collapse, and D-1's off-road signature is
  exactly a collapse (64 → 0 km/h in 1.2 s, `QA1_RESULTS.md` §4).

CALIBRATION (fill on the first run; blank in a fresh checkout)
    STRIP_START=<how to reach it: the map marker / fast-travel route the operator used>
    STRIP_START_SHOT=Working/Q/PILOT/shots/airfield_start.png
    STRIP_MAP_SHOT=Working/Q/PILOT/shots/airfield_map.png
    STRIP_LENGTH_M=<the length the operator measured, or `>=600`>

PRE-CONDITIONS
| # | check | command | must show |
|---|---|---|---|
| P1 | in the car | `Working/Q/PILOT/ENTER_EXIT.md` | `RESULT: PASS` |
| P2 | capture proven live this session | `Working/Q/PILOT/SCREENSHOT.md` | `RESULT: PASS` |
| P3 | calibration done | `grep -E "^    (STRIP_START|STRIP_LENGTH_M)=<" Working/Q/PILOT/AIRFIELD.md` | no output (the placeholders are gone) |

STEPS

### 1. Capture the map at the chosen strip
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/airfield_map.png
    SEE  the file exists, larger than 0 bytes
    IF NOT  STOP — capture dead

### 2. Drive to the start point
    DO   um win shot --exe JustCause3.exe Working/Q/PILOT/shots/airfield_start.png
    SEE  the file exists and differs from `airfield_map.png`
    IF NOT  identical -> STOP: the screen did not change, the route was not taken

### 3. Record the strip run WITH audio
    DO   um win record --exe JustCause3.exe --pid <pid> --out tmp/freebuff/caps/airfield1 --seconds 90
    SEE  exit 0, and `airfield1.mkv` / `.audio.raw` / `.json` exist
    IF NOT  no `.audio.raw` -> STOP; never `--no-audio` (RECORD card, A-1)

### 4. Cut the HUD crops
    DO   python Tools/scripts/qa1_hud.py crops --video tmp/freebuff/caps/airfield1.mkv --out tmp/freebuff/caps/work --fps 5
    SEE  exit 0 and a crop directory with frames
    IF NOT  non-zero -> STOP and quote the error (the video path or fps is wrong)

### 5. Build the digit templates
    DO   python Tools/scripts/qa1_hud.py build --crops tmp/freebuff/caps/work/hud --known Working/Translation/QA1/known.json
    SEE  exit 0 (the 22-frame template set from QA-1 is reused)
    IF NOT  an "unlabelled glyph" refusal -> the take contains a digit shape the templates lack: STOP and label it (that refusal is the instrument protecting the number, `QA1_RESULTS.md` §1)

### 6. Trace the whole take
    DO   python Tools/scripts/qa1_hud.py trace --crops tmp/freebuff/caps/work/hud --csv tmp/freebuff/caps/airfield1.csv --fps 5
    SEE  exit 0 and a CSV with more than 100 rows
    IF NOT  STOP

### 7. Check the speed never collapses under held throttle
    DO   python -c "import csv;r=[float(x['kmh']) for x in csv.DictReader(open('tmp/freebuff/caps/airfield1.csv'))];print(min(b-a for a,b in zip(r,r[1:])))"
    SEE  the printed number is `>= -5` — the worst single-step change is not a drop of more than 5 km/h
    IF NOT  a number below -5 -> a kerb, corner or road edge was hit (D-1: 64->0 in 1.2 s is an impact)
    IF NOT  a drop beyond that -> the run hit a kerb, a corner or the road edge (D-1: 64→0 in 1.2 s is an impact): move to the next candidate strip, repeat steps 1-7 once, then STOP

### 8. Check the length
    DO   python -c "import csv;r=[float(x['kmh'])/3.6 for x in csv.DictReader(open('tmp/freebuff/caps/airfield1.csv'))];print(sum(r)/5*0.2)"
    SEE  a distance `>= <STRIP_LENGTH_M>` (integral of the trace at 5 fps: one sample is 0.2 s)
    IF NOT  shorter -> the strip is too short for the take: STOP and record the measured length

### 9. Record the strip on the RESULT line
    DO   ls -l Working/Q/PILOT/shots/airfield_start.png Working/Q/PILOT/shots/airfield_map.png
    SEE  both files listed, non-empty
    IF NOT  STOP

### 10. Confirm the process and the dump folder
    DO   ls -t "$LOCALAPPDATA/CrashDumps" | grep -i justcause3 | head -1
    SEE  no output
    IF NOT  a dump name -> STOP with it on the RESULT line

RESULT
    RESULT: PASS — strip proven: max drop <n> km/h, length <m> m — pid=<pid> — shots/airfield_start.png, shots/airfield_map.png, caps/airfield1.mkv + .csv
    RESULT: STOP — step <n> — <the SEE that failed, quoted> — <artifacts so far>

TRAPS: D-1 (a free run leaves the road at ~106 km/h — the strip must be long and straight, and the
take is one manoeuvre), D-2 (103 km/h reached where the gate wanted 300 — a short strip silently caps
the take), A-1 (audio always, the rpm channel is the only one JC3 has). Coordinates: **UNKNOWN** in
this repo — the card refuses to invent them and proves the strip from the trace instead; the first
run's start frame becomes the canonical reference ("this is the spot"), which is what Q-2 needs.
Note on the numbers: `known.json` was learned on the test-085 HUD; if `build` refuses, the take needs
re-labelling — that is a real cost of the instrument, not a card failure.
