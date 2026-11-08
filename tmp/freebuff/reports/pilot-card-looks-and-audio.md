# Q-PILOT step 8 — looks and audio cards (Q-1 items 2, 5, 7, 8)

> change 2026-11-07 (review-pilot-cards): four defects fixed in place. (1) `HUD_CHECK` step 2 checked
> `hud_cannon.png` that no step captured — the capture is now step 2b. (2) `HUD_CHECK` step 4 wrote a
> verdict line with the expected values already in it (`reticle=8@-111`), i.e. a measurement table
> pre-filled with the answer; it is now a template that refuses to be submitted while a `<...>`
> survives. (3) `NIGHT` step 2's "visibly darker" is not machine-checkable and is replaced by a hash
> plus the reviewer's crop mean. (4) `AUDIO`'s RESULT named `audio/*.mp4` although no step muxed one;
> it now names the `.mkv` + `.audio.raw` the record step actually writes. `LOOK_CLOSEUPS`'
> `close_<target>.png` placeholder became five literal frames.

Six cards, in the shape fixed by `Working/Q/PILOT/CARD_FORMAT.md` §1–§3: `LOOK_STATIC.md`
(front / side / three-quarter / top), `LOOK_CLOSEUPS.md` (glass, wheel, panel), `NIGHT.md`,
`RAIN.md`, `HUD_CHECK.md`, `AUDIO.md`. They run inside Q-1 session 1 and write frames to
`Working/Q/Q1/shots/` and takes to `Working/Q/Q1/audio/` — the paths `q1_results.py --check`
validates (`Research/specs/Q-1.md` §4 step 2: a recording not under `Working/Q/Q1/` is a FAIL).

Nothing here launches the game. The cards are written, not run: the test ban stands and no
process, save, archive or GraphicSettings value was touched.

---

## 0. What these cards may use, and the one limit that shapes them

| need | what the repo has | consequence for the cards |
|---|---|---|
| a camera you can place | **no free camera.** The only decoded camera rows are `VEHICLE_CAM` = `B` and `LOOK_BEHIND_CAM` = `B` (`Working/Q/PILOT/CONTROLS.md` rows 21–22, from `Research/JC3Grab/INPUT.md`); `B` is three things at once (§2 conflict F) | the four angles are taken **on foot around the parked car** (exit is decoded `E`, row 2). Camera position is stated as where Rico stands; it is a **calibration field**, filled on the first run |
| top-down | nothing. No decoded camera row is an overhead | `TOP_VIEW` is `UNKNOWN` and the top card refuses to run until the field is filled or the gap is accepted. Settling file: `Research/JC3Grab/INPUT.md` (camera targets) + a B-25 light-unit probe |
| night | no decoded time-of-day control; `working`/`G3-09.md` counts **0** tonemap/time-of-day keys | `NIGHT_STATE` is a calibration field: the operator waits for in-game night, the card records how |
| rain | JC3 wetness is scene-global (`TEST_WETNESS_FACTOR`) plus wet road **shader variants**; no vehicle-level control (`tmp/freebuff/reports/app-wetness-and-rain.md` §1) | `RAIN_STATE` is a calibration field; the rain card measures what the scene does, it cannot request a weather state |
| key presses | `um win drive --proc JustCause3 "key 0x.."`; only decoded keys (`CONTROLS.md` §1) | keys actually sent: `0x45` E (exit, row 2) and `0x1B` Esc (row 23). `0x42` B (rows 21/22) is available but **not** sent, because `B` is camera-cycle and look-behind at once (§2 conflict F). Weapon fire is an operator LMB press (row 10, decoded action), not a VK. No `UNKNOWN` row is pressed |
| capture | `um win shot --exe JustCause3.exe <path>` (SCREENSHOT.md), `um win record … --seconds N` (RECORD.md, audio mandatory) | every card's machine check is a file property, a hash difference or the record peak — never "looks right" |

**Pilot thresholds** (values this document declares because no file has one, calibrated on the
first run and written back into the card): standing distance 2.0–3.0 m; night body patch mean
below 60/255; charcoal neutrality ≤ 12/255 spread; panel agreement within 8/255; audio clip
6 s ±1 s. Each is labelled **pilot threshold** at its first use.

---

## 1. The screenshot set

Car stationary, engine off unless a row says otherwise, driver out (so the camera is free).
One frame per row, at 1600×900 (`LAUNCH.md` step 8 sets the window).

| id | frame | camera position (Rico on foot) | expected visible features — and where the expectation comes from | reviewer comparison |
|---|---|---|---|---|
| `L1` **side** | `shots/look_side.png` | left flank, 2.5 m out, eye 1.6 m, lens level with the door | full 5.03 m wheelbase profile, both wheel arches, canopy line, satin armour; 19 material slots on the body (`Working/Q/PREDICTIONS_LOOKS.md` Q1-2) | no missing panel or tear; the body is darker than the road surface behind it; **not** a mirror (a mirror shows a hard reflected skyline; satin shows a soft gradient) |
| `L2` **front** | `shots/look_front.png` | 2.5 m ahead of the nose, centred, eye 1.6 m | two headlight clusters, front splitter, canopy, no plate; 8 lamp parts (`Q1-7`) | both headlight housings present and symmetric; the grille reads as one face, not a gap; panel gaps even left/right |
| `L3` **three-quarter** | `shots/look_three_quarter.png` | 2.8 m out on the front-left diagonal (≈40°), eye 1.6 m | front-left corner, wheel arch, canopy and A-pillar in one frame; the silhouette that Q1-2's 99.97 % measurement describes | the corner is continuous — no crease, no inverted normal; the arch strip is not floating; canopy glass reads as glass, not paint |
| `L4` **top** | `shots/look_top.png` | **`TOP_VIEW` = UNKNOWN** — a ledge/roof 4–6 m above the car, or the gap is recorded | roof liner, canopy, both arches from above; nothing in the repo gives an overhead view | if taken: both sides symmetric, canopy centred, no hole where the roof liner is (`app-cockpit-interior-materials.md` §1.1 lists the liner, y 1.9661) |
| `L5` **interior** | `shots/look_interior.png` | inside, driver's seat, after `VEHICLE_CAM` cycling (`0x42`) | dash, centre screen (0.3188 × 0.1512 m), yoke, seat, canopy overhead; 11 of 15 interior components have **no faithful carrier** (`app-cockpit-interior-materials.md`, short version) | the dash and screen are present and not stretched; the seat is not a flat quad; the roof is closed above Rico's head (clearance 0.151 m, Q1-3) |
| `L6` **night** | `shots/look_night.png` | same as `L1`, lights **on**, `NIGHT_STATE` filled | 18 light entries in the shipped module on 8 lamp parts (`Working/Lights/bm_lightrig.json`: `rows` 18, `lamp_parts` 8, `parts_used` 7, `dropped` 10) | **count the lit lamps and write the number**: the card passes on `count == 18` *or* on a recorded exception from §3.1. **17 lens flares are not among them** — 0 of 17 are carried |
| `L7` **rain** | `shots/look_rain.png` | same as `L1`, `RAIN_STATE` filled, lights on | wet specular on the body, darkening of the paint, rain occlusion on the glass (`Window` block carries `RainOccluderSampler s9`); the road switches to a `…wet` shader variant | body gloss rises **without** the colour changing hue; glass beads water; the road reflects. If the body shows no change at all, the scene factor is not being applied — record it, do not call it a build failure (§4) |

### 1.1 The five close-ups (one card, five frames)

| id | frame | camera | expected | reviewer comparison |
|---|---|---|---|---|
| `C1` **glass** | `shots/close_glass.png` | 0.8 m from the canopy, eye level with the A-pillar | canopy glass with a visible edge, no paint bleed; 3,532 glass faces (`app-cockpit-interior-materials.md` §1.1) | you can see the seat through it; the edge is a line, not a fade; no opaque patch where the windscreen meets the cowl |
| `C2` **wheel** | `shots/close_wheel.png` | 0.9 m from the front-left wheel, eye 0.9 m | tyre, rim, arch strip; wheel-arch lamps are T-L13/T-L14/T-L20 rows (`bm_lightrig.json` rows 12/13/16) | the arch strip sits inside the arch, not on the tyre; rim is round at this angle; no z-fighting between strip and arch |
| `C3` **panel gap** (front-left) | `shots/close_panel_fl.png` | 0.6 m from the front-left fender seam | one continuous seam, even width | seam width constant along its length; no step between fender and door; no black line where two shells overlap |
| `C4` **panel gap** (rear-right) | `shots/close_panel_rr.png` | 0.6 m from the rear-right quarter seam | same, opposite corner | as `C3`, mirrored — a one-sided fault shows here and not there |
| `C5` **lamp face** | `shots/close_lamp.png` | 0.7 m from the right headlight, lights **off** | the housing and its emissive face, unlit | the housing is not a hole; the face is dark but present (a missing emissive face is the B-25 flare symptom, §3.2) |

Close-up distances are **pilot thresholds** (0.6–0.9 m). If the on-foot camera cannot get that
close without clipping the body, the card uses 1.2 m and writes the number back.

---

## 2. The night light count, stated as a number the card can fail

* **18** entries in the shipped module (`Working/Lights/bm_lightrig.json`, `rows`: 18), from 21
  donor rows; **10** donor rows dropped with reasons (`dropped`), **8** lamp parts, **7** used.
* By behaviour: 12 `HeadLight` + 6 `TailLight`; by range: five rows at 30 m / 40°, the rest 2 m /
  10°, one graph-object row (T-L17) at 10 m / 60°.
* **Fleet ceiling**: the shipped census tops out at **range 50 / angle 50**
  (`Working/Q/PREDICTIONS_LOOKS.md` Q1-7b, from `Research/JC3Grab/LIGHT_SYSTEM.json`, 3,217
  entries: 66 rows at range 50, 74 at angle 50). Anything above 50 is writable and unshipped.
* **Review 8299's record** is different from both of the above: it reports **light range 60/45**
  above the fleet max 50 (R3). The three numbers in the repo do not agree —
  review 60/45, `Q1-7b` beam 60 m / 70°, the built module 30 m / 40° max plus the 60° graph
  object. The card therefore **counts entries and reads the beam length off the frame**, and does
  not assert any of the three. A beam visibly cut at 50 m is a clamp, not a defect (Q1-7b's own
  band).

### 2.1 The night card's pass rule

```
PASS  when the number of distinct lit lamp faces counted in look_night.png == 18
      or when the count differs and each difference is named from the `dropped` list
      (indicators, reverse, rear point lamps: 10 rows, all with a stated reason in bm_lightrig.json)
FAIL  when a lamp listed in rows 0-17 is dark with no recorded reason
```

### 2.2 What the night card must not count

17 lens-flare entries are **B-25, card only**: 10 flare-only + 7 riding, **0 of 17 carried**
(`tmp/freebuff/reports/keep-audit-lights.md:153`; `apply-keep-audit-fixes-systems.md:26`;
`correction-8398-unshipped-cards.md` §row B-25). The light-unit probe is unproven. A flare in the
frame is therefore **not** a delivered feature, and its absence is **not** a failure of this
session. The RESULT line carries `flares=0/17 expected`.

---

## 3. The HUD check

Expected values, all from `Working/Q/PREDICTIONS_LOOKS.md` (T-HUD rows), so each is a number the
reviewer can fail rather than an opinion:

| element | expectation | band |
|---|---|---|
| weapon slots | 2 clips, `MCI_vehicle_weapons0/1` | exactly 2; one per bound weapon |
| cannon reticle | shape `E_RETICLE_CANNON` = 8, marker y **−111 px** from centre | marker within ±6 px of −111; shape is the heavy one |
| cooldown ring | 0..1 in four states → 0.00 / 0.25 / 0.50 / 0.75 / 1.00, rotation 0..360° | ring fills and resets between shots; hidden at rest |
| lock-on | POI type 21, one marker, 360°/1.5 s rotation | one marker, rotating, on the locked target only |
| ammo | `infiniteAmmo` true | **no** ammo counter in either slot |
| heat | build ships none (no heat bar) | **no** heat element anywhere |
| reticle size | accuracy frame → 5..30 px | UNKNOWN — no unit map; not scored |

The HUD card takes three frames (rest / cannon equipped / firing) and the reviewer compares each
row above. Frame names: `shots/hud_rest.png`, `shots/hud_cannon.png`, `shots/hud_fire.png`.

---

## 4. The audio session — five slots, and what stays vanilla

The build remaps **five** slots and nothing else (`tmp/freebuff/reports/B-11.md` done criterion 1,
`bm_audio.py --check`: `5 mapped rows, 5 slots in 2 banks`):

| take | event | built slot | evidence | comparison |
|---|---|---|---|---|
| `A1` engine start + idle + rev sweep | **vanilla JC3**, not BmAK | — | `Working/RC/COMPROMISES_B.md:140`: "engine start/idle/rev … remain JC3 samples except five slots" | must be audible and continuous; no gap at the loop seam; peak > 0.001 (RECORD.md step 4) |
| `A2` boost / afterburner | `A-02` → `vehicles` #151 `jc3_veh_land_premium_nitro_loop` | 3.225 s, 1 ch, 48 kHz | `B-11.md` slot table; Q1-8 | the boost take's audio differs from the A1 take's at the same rpm — a slot that did not play yields identical waveforms |
| `A3` door open + close | `A-06` → #7 `jc3_veh_door_tank_open_03` (0.624 s), `A-07` → #98 `jc3_veh_door_tank_close_01` (0.519 s) | 2 slots | `B-11.md` | two distinct transients, open before close, each on its own action |
| `A4` weapon fire (Vulcan) | `W-03` → `weapons` #408 `jc3_wpn_minigun_fire_close_loop_04` | 3.340 s, 2 ch | `B-11.md`; no donor GUID — resolves by slot name | a loop, not a single shot; continues while the trigger is held; stops on release |

Known audio gaps the session records rather than fails: **21 of 45 GUIDs are donor-carried**
(19 effects + 2 character banks not built, Q1-8); loudness and loop gates were already measured
**red** in V-04 (max 2.33 LU against ±1 LU) and are expected to fail again; `jc3_veh_lave_chassis_spin_creaks_loop_fast`
has a seam click (`7202-v04-audio-gates.md`: −17.50 dBFS seam against −46.01 p99 interior).

---

## 5. The comparison against BmAK footage — wet street, dark charcoal

The operator's reference is a **wet street at night, dark charcoal**. "Compare to the footage" is
only executable if it is turned into things a reviewer measures, because the repo cannot produce
BmAK pixels: `Research/BatmobileGrab/COLOUR.md` §6 states outright that *"a screen pixel value
under named lighting: UNKNOWN — no calibrated capture of the body exists in the project"*
(`FOOTAGE.md` measures air time, not colour).

### 5.1 What to photograph

1. `L6` at night with lights on, and `L7` in rain with lights on — the same standing spot as `L1`,
   so the three frames differ only in light and weather.
2. One **reference frame of the road** in the same `L6` frame: the road surface is the wet
   comparison; if it is in frame at the bottom third, no second frame is needed.
3. Three 64×64 crops from `L1`, `L6`, `L7`: bonnet, driver's door, roof. Same crop boxes in all
   three, recorded in `shots/look_crops.json` on the first run.
4. One 64×64 road crop from `L6`.

### 5.2 How to compare

The metrics are ratios and spreads, not absolute pixels, because the tonemap and the lighting sum
are UNKNOWN (`COLOUR.md` §6). Compute each crop's mean sRGB (0–255) and its channel spread
`max(R,G,B) − min(R,G,B)`:

| check | rule | why this rule |
|---|---|---|
| **charcoal, not black, not grey** | crop mean in **8..60** per channel at night; spread **≤ 12** (pilot thresholds) | BmAK's authored base is linear `[0.02579, 0.02579, 0.03]` (`Research/BatmobileGrab/COLOUR.md` §2, export 767 @360) — near-neutral with a 0.004 blue lift. A spread above 12 means a tint leaked in; a mean above 60 means the paint is being read as mid-grey |
| **satin, not mirror** | no crop contains a hard-edged reflected skyline or light source; the brightest 1 % of a body crop is **< 3×** the crop mean | Q1-2's "no mirror" gate; the wet look raises specular, it does not make the body a mirror |
| **panels agree** | the three crops' means differ by **≤ 8/255** | a panel with a different material shows as a brightness step, which is the failure the 23-row texture set predicts (§6) |
| **body below road** | body crop mean **<** road crop mean in `L6` | Q1-2's "body luminance above road" is the noon rule; at night with headlights on the *road* is lit and the body must still read darker than the lit road patch, or the paint is emissive |
| **wet, both ways** | `L7` body mean **<** `L6` body mean, and `L7` body gloss (brightest 1 % / mean) **>** `L6` | wetness darkens diffuse and raises specular; both moving the same way is the only combination that says "wet" rather than "brighter" |

All five are **pilot thresholds**, calibrated on session 1 and written back. A miss is recorded as a
measured value and a FAIL of that row — never reinterpreted (Q-1's rule).

### 5.3 What cannot be compared against the footage, and why

| BmAK term | value | why there is nothing to compare | settling file |
|---|---|---|---|
| `Material0_Reflectivity` | 0.20 | no `CarPaintMM` field; cb2 has no reflectivity slot | `tmp/freebuff/reports/paint-slots-to-bmak-values-apply-plan.md` |
| `Wetness_Refl_Fresnel` / `Wetness_Reflectivity_Multiplier` / `RainReflectivityMul` / `RainRoughnessMul` | 0.6 / 0.6 / 1.6 / 0.75 | **no member** — `cb2` carries no wetness or rain field; JC3's wet state is scene-global | `tmp/freebuff/reports/colour-bmak-wet-look.md` §(wetness table); `app-wetness-and-rain.md` §1 |
| `Material0_Roughness` 0.4, `Material2_Metalicity` 1.0 | written | the values ship; only the rendered result can be compared | `colour-bmak-wet-look.md` |

So the footage comparison is **tone and behaviour**, never "the same pixels": charcoal under a wet
night sky, satin rather than mirror, panels consistent, darker than the lit road, and both wet
signals moving together. That is what the operator's reference can actually adjudicate.

---

## 6. The cards

### 6.1 `LOOK_STATIC.md` — four angles of the parked car

```
GOAL: four named frames of the parked Batmobile at noon, from front, left flank, front-left
      three-quarter and above, with the camera position of each written down.

PRE-CONDITIONS
| # | check | command | must show |
|---|---|---|---|
| P1 | in the car, HUD up | Working/Q/PILOT/ENTER_EXIT.md | RESULT: PASS |
| P2 | capture proven live | Working/Q/PILOT/SCREENSHOT.md | RESULT: PASS |
| P3 | car parked, flat ground, no traffic | operator | car stationary; engine off |
| P4 | angles calibrated | `grep -E "^    (SIDE_STAND|FRONT_STAND|TQ_STAND|TOP_VIEW)=" Working/Q/PILOT/LOOK_STATIC.md` | no output (placeholders filled) |

STEPS
### 1. Exit and take up the side position
    DO   um win drive --proc JustCause3 "key 0x45"
    SEE  `ok`; then a frame at SIDE_STAND differs from the in-car frame (sha256)
    IF NOT  run ENTER_EXIT step 10 (LB/E); still no exit -> STOP

### 2. Side frame
    DO   um win shot --exe JustCause3.exe Working/Q/Q1/shots/look_side.png
    SEE  file exists, > 0 bytes
    IF NOT  STOP — capture dead

### 3. Front frame
    DO   um win shot --exe JustCause3.exe Working/Q/Q1/shots/look_front.png
    SEE  exists and sha256 != look_side.png
    IF NOT  identical -> the camera did not move: STOP

### 4. Three-quarter frame
    DO   um win shot --exe JustCause3.exe Working/Q/Q1/shots/look_three_quarter.png
    SEE  exists and sha256 differs from both earlier frames
    IF NOT  STOP

### 5. Top frame
    DO   um win shot --exe JustCause3.exe Working/Q/Q1/shots/look_top.png
    SEE  exists, > 0 bytes
    IF NOT  TOP_VIEW still UNKNOWN -> write `top=UNKNOWN` on RESULT, skip to step 6

### 6. Record what each frame shows
    DO   ls -l Working/Q/Q1/shots/look_{side,front,three_quarter,top}.png
    SEE  four lines (three if top is UNKNOWN), none 0 bytes
    IF NOT  STOP with the missing name

RESULT
    RESULT: PASS — four angles archived — pid=<pid> — shots/look_{side,front,three_quarter,top}.png
    RESULT: STOP — step <n> — <the SEE that failed, quoted> — <frames so far>

REVIEWER (not a machine check): the four frames are scored against §1 rows L1–L4.
TRAPS: the `B` key is camera-cycle AND look-behind (CONTROLS.md conflict F) — this card never
       presses it; exit uses `E` (decoded), never `Y`; fixed time of day is a calibration field,
       not an assertion.
```

### 6.2 `LOOK_CLOSEUPS.md` — glass, wheel, panel, lamp

```
GOAL: five close frames that show the canopy edge, one wheel/arch, two panel seams and one lamp
      housing, each within the stated distance.

PRE-CONDITIONS: as LOOK_STATIC P1–P3, plus CLOSE_STAND calibrated.

STEPS
### 1. Glass
    DO   um win shot --exe JustCause3.exe Working/Q/Q1/shots/close_glass.png
    SEE  exists, > 0 bytes
    IF NOT  STOP — capture dead

### 2. Wheel
    DO   um win shot --exe JustCause3.exe Working/Q/Q1/shots/close_wheel.png
    SEE  exists and its sha256 differs from `close_glass.png`
    IF NOT  identical -> the pilot did not move: STOP (never re-label a duplicate as a new shot)

### 3. Front-left panel
    DO   um win shot --exe JustCause3.exe Working/Q/Q1/shots/close_panel_fl.png
    SEE  exists and its sha256 differs from both earlier frames
    IF NOT  identical -> STOP

### 4. Rear-right panel
    DO   um win shot --exe JustCause3.exe Working/Q/Q1/shots/close_panel_rr.png
    SEE  exists and its sha256 differs from all three earlier frames
    IF NOT  identical -> STOP

### 5. Lamp face
    DO   um win shot --exe JustCause3.exe Working/Q/Q1/shots/close_lamp.png
    SEE  exists and its sha256 differs from all four earlier frames
    IF NOT  identical -> STOP

### 6. Check the five are five
    DO   ls -l Working/Q/Q1/shots/close_*.png
    SEE  five lines, five distinct sizes or hashes
    IF NOT  a duplicate -> STOP, quote the duplicate pair

RESULT
    RESULT: PASS — five close frames archived — pid=<pid> — shots/close_{glass,wheel,panel_fl,panel_rr,lamp}.png
    RESULT: STOP — step <n> — <the SEE that failed, quoted> — <frames so far>

REVIEWER: §1.1 rows C1–C5. A missing emissive face at C5 is the B-25 symptom, recorded as a
         known gap, not a session failure.
TRAPS: standing closer than 0.6 m clips the camera into the body — the frame will show the
       interior of a panel, which is a position fault, not a model fault.
```

### 6.3 `NIGHT.md` — 18 lamps, 0 flares

```
GOAL: a night frame with the lights on, and a written count of lit lamp faces against the 18
      entries the module ships.

PRE-CONDITIONS
| P1 | LOOK_STATIC PASS | frames 2-4 archived |
| P2 | NIGHT_STATE calibrated | the field holds how night was reached (in-game time, not a console command) |
| P3 | lights on | the headlight control is BmAK's; if the build has no decoded key for it, the field records "always on" |

STEPS
### 1. Reach night
    DO   (operator) reach night by play; record the route in NIGHT_STATE
    SEE  NIGHT_STATE no longer `<...>`
    IF NOT  night not reached -> STOP; a day frame labelled night is the defect this card prevents

### 2. Capture with lights on
    DO   um win shot --exe JustCause3.exe Working/Q/Q1/shots/look_night.png
    SEE  exists, > 0 bytes, and its sha256 differs from `look_side.png`
    IF NOT  identical hash -> nothing changed on screen: STOP
    NOTE  "visibly darker" is not a machine check and was removed on 2026-11-07; the night frame's
    darkness is a NUMBER the reviewer computes with §5.2's crop means, never an eye judgement.

### 3. Capture with lights off (the control)
    DO   um win shot --exe JustCause3.exe Working/Q/Q1/shots/look_night_off.png
    SEE  exists and sha256 differs from look_night.png
    IF NOT  identical -> the lamp state did not change: record `lamps=always-on`, continue

### 4. Write the count
    DO   printf "lit=<n> of 18 flares=0/17\n" >> Working/Q/Q1/shots/look_night.txt
    SEE  the file holds one `lit=` line
    IF NOT  STOP — repo not writable

RESULT
    RESULT: PASS — night frame archived, lit=<n>/18, flares=0/17 expected — pid=<pid> — shots/look_night.png, look_night_off.png
    RESULT: STOP — step <n> — <the SEE that failed, quoted> — <frames so far>

REVIEWER: count lit faces against bm_lightrig.json rows 0-17; a dark row 0-17 with no `dropped`
          reason is a FAIL. A visible flare does not raise the count (0 of 17 carried, B-25).
TRAPS: range 60/45 (review 8299), 60 m/70 deg (Q1-7b) and the built 30 m/40 deg disagree — the
       card reads the beam off the frame and asserts none of them; a beam cut at 50 m is the
       fleet clamp, not a defect.
```

### 6.4 `RAIN.md` — the wet-state frame

```
GOAL: one frame in rain with the lights on, plus one dry frame from the same spot, so the wet
      change can be measured rather than described.

PRE-CONDITIONS: LOOK_STATIC PASS; RAIN_STATE calibrated; DRY_REF = shots/look_side.png.

STEPS
### 1. Reach rain, same standing position
    DO   (operator) reach rain by play; return to SIDE_STAND
    SEE  RAIN_STATE filled
    IF NOT  STOP — no rain, no rain card

### 2. Capture
    DO   um win shot --exe JustCause3.exe Working/Q/Q1/shots/look_rain.png
    SEE  exists, > 0 bytes, sha256 differs from DRY_REF
    IF NOT  identical -> the scene did not change: STOP, the rain state is not live

### 3. Copy the dry reference beside it
    DO   cp Working/Q/Q1/shots/look_side.png Working/Q/Q1/shots/look_dry_ref.png
    SEE  the copy exists
    IF NOT  STOP

RESULT
    RESULT: PASS — rain and dry frames paired — pid=<pid> — shots/look_rain.png, look_dry_ref.png
    RESULT: STOP — step <n> — <the SEE that failed, quoted> — <frames so far>

REVIEWER: §5.2 rows "wet, both ways" and "charcoal, not black": body mean falls, gloss rises.
          No change at all means the scene factor is not reaching the paint — record it; the
          four BmAK wet multipliers have no member and cannot be blamed (colour-bmak-wet-look.md).
TRAPS: JC3 weather is scene-global (TEST_WETNESS_FACTOR) and the road uses a separate wet shader
       variant; a wet road with a dry car is a real possible outcome and is recorded as measured.
```

### 6.5 `HUD_CHECK.md` — the cluster at rest, with the cannon, firing

```
GOAL: three HUD frames and a written verdict against the seven expectations in §3.

PRE-CONDITIONS: ENTER_EXIT PASS; a weapon bound (cannon on primary, CONTROLS row 10 = LMB,
                decoded JC3 action); HUD_CHECK fields calibrated.

STEPS
### 1. Rest frame
    DO   um win shot --exe JustCause3.exe Working/Q/Q1/shots/hud_rest.png
    SEE  exists, > 0 bytes
    IF NOT  STOP

### 2. Reticle frame (operator selects the cannon)
    DO   (operator) press LMB once — JC3 `FIRE_VEHICLE_WEAPON_PRIMARY`, decoded (CONTROLS.md row 10);
         no keyboard VK exists for it in the repo, so the card never sends one
    SEE  the operator states the press was made (recorded as `operator press`); the card's own check
         is step 2b's hash
    IF NOT  the operator reports no cannon in the slot -> record `cannon=unbound`, skip to step 4
         (never substitute a key that is not in CONTROLS.md)

### 2b. Capture the reticle
    DO   um win shot --exe JustCause3.exe Working/Q/Q1/shots/hud_cannon.png
    SEE  the file exists, > 0 bytes, and its sha256 differs from `hud_rest.png`
    IF NOT  identical -> the slot did not change the reticle: record `cannon=unbound`, skip to step 4

### 3. Fire and capture
    DO   um win shot --exe JustCause3.exe Working/Q/Q1/shots/hud_fire.png
    SEE  exists and differs from hud_cannon.png (muzzle flash or ring state)
    IF NOT  identical -> no shot fired or the HUD is frozen: STOP

### 4. Write the verdict table
    DO   printf "slots=<n> reticle_offset_px=<px> cooldown=<state> lock=<state> ammo=<state> heat=<state>\n" > Working/Q/Q1/shots/hud.txt
    SEE  `wc -l` prints `1`, and no `<...>` placeholder survives in the line
    IF NOT  a placeholder survives -> the verdict is a template, not a measurement: STOP (the old
             version shipped the expected values pre-filled, which is the defect this line prevents)

RESULT
    RESULT: PASS — three HUD frames archived — pid=<pid> — shots/hud_{rest,cannon,fire}.png
    RESULT: STOP — step <n> — <the SEE that failed, quoted> — <frames so far>

REVIEWER: §3 table row by row; the pixel offset −111 is measured from the frame centre, so the
          frame must be the same 1600x900 as LAUNCH step 11 printed.
TRAPS: no lock target exists at a standstill in free roam — the lock row is recorded `not
       exercised` (not a FAIL) unless a target is available; T-HUD18 is Q-2's take.
```

### 6.6 `AUDIO.md` — engine, boost, door, weapons

```
GOAL: four takes with the game's own audio, each with a measured peak above 0.001, and a written
      slot verdict against the five mapped slots.

PRE-CONDITIONS
| P1 | LAUNCH PASS, same pid | um win ps | the recorded pid |
| P2 | JC3 not muted in the volume mixer | operator | not muted (a mute is exact silence) |
| P3 | boost binding resolved | CONTROLS.md row 8 is UNKNOWN for JC3 | if still UNKNOWN, the boost take records `boost=UNBOUND`, it is not skipped silently |

STEPS
### 1. Engine take (vanilla)
    DO   um win record --exe JustCause3.exe --pid <pid> --out Working/Q/Q1/audio/engine --seconds 20
    SEE  exit 0; engine.mkv, engine.audio.raw, engine.json exist, none 0 bytes
    IF NOT  no .audio.raw -> STOP; never `--no-audio`

### 2. Engine peak
    DO   python -c "import array;a=array.array('f');a.frombytes(open('Working/Q/Q1/audio/engine.audio.raw','rb').read());print(max(abs(v) for v in a))"
    SEE  a number > 0.001 (write it on the RESULT line)
    IF NOT  re-run steps 1-2 once after unmuting; a second silent take -> STOP

### 3. Boost take, then door take, then weapon take
    DO   repeat step 1 with --out .../boost, .../door, .../weapons
    SEE  for each: three files exist, peak > 0.001
    IF NOT  quote which take is silent; do not proceed to compare a silent take

### 4. Compare the takes are not the same audio
    DO   sha256sum Working/Q/Q1/audio/*.audio.raw
    SEE  four distinct hashes
    IF NOT  two identical -> that slot did not play (the take fell back to the same source): record it

### 5. Slot verdict
    DO   printf "mapped=5 engine=vanilla boost=151 door=7/98 weapons=408 donor=21/45\n" >> Working/Q/Q1/audio/slots.txt
    SEE  one line appended
    IF NOT  STOP

RESULT
    RESULT: PASS — four non-silent takes, four distinct tracks — pid=<pid> — peaks=<n,n,n,n> — audio/{engine,boost,door,weapons}.mkv (+ .audio.raw)
    RESULT: STOP — step <n> — <the SEE that failed, quoted> — <artifacts so far>

REVIEWER: §4 table. Engine is expected to stay JC3 (named omission); the boost take must differ
          from the engine take at equal rpm; door open precedes close; the weapon track loops.
TRAPS: A-1 (`--no-audio` banned — JC3's only rpm channel is audio); per-app mute is exact
       silence; `jc3_veh_lave_chassis_spin_creaks_loop_fast` seam click (−17.50 dBFS) is a
       recorded known gap, not a new failure.
```

---

## 7. Review 8299's known gaps — recorded on the cards, not re-discovered in session

| gap | number | where it is recorded on a card |
|---|---|---|
| texture rows unfaithful | **12 of 23** (4 chapter masks need variants; 8 pixel sets missing) | `LOOK_STATIC` REVIEWER ("no missing panel" is judged against this set), §6 table below |
| chapter damage masks | **4** absent — one static state only; 0 of 961 shader headers name `chapter`; `SupportDmgBlend` 0.0 in all 160 blocks | panel close-ups `C3`/`C4`: a chapter difference is not expected; a permanent damage look is not the build |
| pixel sets missing | **8**: 4 micropatterns, wheel emissive, 3 ramps | `C5` lamp face and `L1`/`L3` panel tone: a missing map shows as flat tone, not as a hole |
| light range | **60/45** recorded against fleet max **50** (R3) | `NIGHT` TRAPS — count entries, read the beam, assert neither 60/45 nor 60/70 |
| lens flares | **17** entries, B-25 card only, **0 carried**, light-unit probe unproven | `NIGHT` step 4 + §2.2 — `flares=0/17 expected` |
| appearance score | **54.6 %** overall, **49.3 %** strict, **91.1 %** of-slotted | §7.1 below; the cards never claim a percentage in a frame |

### 7.1 The percentages, and why no card scores them

`Builds/bm-RC4-appearance/progress.json` (re-run in `correction-8392-unfaithful-textures.md` §4):
geometry 100.0, materials 100.0, textures 53.9, factors 46.9, **overall 54.6**, strict 49.3,
of-transferable 91.1. A screenshot does not move any of these — they count dispositions, not
pixels. The cards therefore **archive frames for the reviewer**; the number on `RESULTS.md` is the
gate's own, copied from `progress.json`, never estimated from a frame.

---

## 8. Checks run for this document

| check | result |
|---|---|
| `Working/Q/PILOT/CARD_FORMAT.md` read; six cards follow §1 (GOAL / PRE-CONDITIONS / STEPS / RESULT / TRAPS) | yes |
| keys used exist as `decoded` rows in `CONTROLS.md` (§1 rows 2, 3, 6, 21, 23) | yes — `E`, `W`, `A`, `B`, `Esc`; `B` deliberately not pressed |
| `Working/Lights/bm_lightrig.json` parsed: `rows` 18, `dropped` 10, `lamp_parts` 8, `parts_used` 7, `unknowns` 4 | 18 / 10 / 8 / 7 / 4 |
| flare count `0 of 17` | `keep-audit-lights.md:153`, `apply-keep-audit-fixes-systems.md:26`, `correction-8398-unshipped-cards.md` |
| audio slots `5` and their names/tunes | `tmp/freebuff/reports/B-11.md` (A-02 #151, A-06 #7, A-05 #279, A-07 #98, W-03 #408) |
| texture refusals `12` + 1 (Leather, sampler only) | `correction-8392-unfaithful-textures.md` §2–§3 |
| appearance `54.6 / 49.3 / 91.1 / 53.9` | `correction-8392-unfaithful-textures.md` §4 gate block |
| `Working/Q/Q1/` does not yet exist | `ls Working/Q` shows only PILOT + PREDICTIONS_*; the card's `mkdir` is in `LOOK_STATIC` P4 path, and `q1_results.py --init` owns the directory per Q-1 §4 step 2 |
| no file edited except this one | `git status` shows no card, script or build file touched by this document |

**Limitations**

* No card was executed: the test ban stands, so every `SEE` is a file property or a peak the
  command prints, not an observation.
* The three light numbers (review 60/45, Q1-7b 60 m/70°, built module 30 m/40° + 60° graph object)
  do not reconcile; the card is written to count and measure instead of choosing one. The file that
  would settle it is `Research/JC3Grab/LIGHT_SYSTEM.json` re-censused against the D-03 beam rows.
* The BmAK side of the comparison has **no calibrated capture** (`COLOUR.md` §6), so §5 is a
  method with pilot thresholds, not a scored gate.
* `TOP_VIEW` and the interior view rest on camera capability the repo does not document; both are
  calibration fields with `UNKNOWN` values, and `Research/JC3Grab/INPUT.md` is the file that
  settles which `VEHICLE_CAM` targets JC3 actually exposes.

**Revert:** delete `tmp/freebuff/reports/pilot-card-looks-and-audio.md`. Nothing else was written.
