# The Vulcan crosshair: fire timing, bloom and the red state, measured from the capture

**Question.** The operator reports that the Vulcan never locks out: while firing, the crosshairs spread and
then turn red; the cool-down only brings the spread back down, and firing is never interrupted. Does the
capture match the time-based bloom in `FOOTAGE.md` §2 / row F-2 (`InaccuracyAngle` 0.1 + `InaccuracyVsTime`
0.0→0, 0.5→0, 1.5→1.5, 2.5→3.0, and `HeatUpPerSecond` 0.0), and where do the **red colour** and
`OverheatOffValue` **0.25** come in?

**Verdict.**

1. **The firing window in this clip is 11.120 s → the end of the file (49.14 s), not 10–15 s.** The trigger
   is never released: the broadband fire band steps up 24 dB at **11.120 s** (measured, audio) and is still
   up at 49.14 s, while the reticle stays fully bloomed and red to the last frame (measured, video).
2. **The spread is a ramp, not a step, and it finishes 2.51 s after the trigger goes down** — the
   `InaccuracyVsTime` end point is 2.5 s. Time to first *visible* movement **+1.56 s**; full bloom
   **+2.51 s** (derived from measured absolute timestamps). The 0–1.5 s half of the curve is **not
   resolvable** here: at rest the four tick marks sit *inside* the ring, and they only clear it once the
   bloom is ~50 %, which is exactly what the curve puts at 1.5 s.
3. **Red is a threshold, not a ramp.** It flips in **one frame** at **13.457 s** — `mean(R−G)` over the tick
   annulus goes −19.8 → +14.3 and the red fraction 0.000 → 1.000 in a single 34 ms frame, in two independent
   threshold sets. That is **0.17 s before** the spread plateaus, at ≈**92 %** of the curve's peak.
4. **The player behaviour matches the bloom table in shape and in its end time, and cannot be distinguished
   from a heat model by this clip.** `HeatUpPerSecond` 0.0 is consistent with "never locks out"; but red is
   monotonic with fire time and never clears, so (a) "HUD colour state on a spread threshold" and (b) "heat
   state that never returns below `OverheatOffValue` 0.25" predict the same pixels. **Which one it is, is
   UNKNOWN**; §8 gives the one-clip test that separates them.

Labels throughout: **measured** = read off frames or audio samples, with the frame/sample index given;
**derived** = arithmetic over measured or decoded inputs, with the assumption stated; **UNKNOWN** = searched
and absent, with the settler named.

---

## 1. Sources, and the commands that produce them

| item | path |
|---|---|
| capture (read in place, **never copied into the repo**) | `C:\Users\User\Videos\Captures\Batman™_ Arkham Knight VulcanFire_10s-15s.mp4` |
| ffprobe / ffmpeg | `C:\Users\User\Downloads\ffmpeg-2026-03-09-git-9b7439c31b-full_build\ffmpeg-2026-03-09-git-9b7439c31b-full_build\bin\` |
| derived data (audio, frame tables, montages) | `tmp/vulcan-capture/` |
| file-side claims | `Research/BatmobileGrab/FOOTAGE.md` §2 and row F-2; `tmp/freebuff/reports/vulcan-spinup-and-heat-plan.md` §2, §4 |

```bash
FF="C:/Users/User/Downloads/ffmpeg-2026-03-09-git-9b7439c31b-full_build/ffmpeg-2026-03-09-git-9b7439c31b-full_build/bin"
V="C:/Users/User/Videos/Captures/Batman™_ Arkham Knight VulcanFire_10s-15s.mp4"

# stream geometry, frame count, PTS base
"$FF/ffprobe.exe" -v error -show_streams -show_format "$V"

# per-frame presentation timestamps (the clip is VFR: every index below maps to a PTS)
"$FF/ffprobe.exe" -v error -select_streams v:0 \
  -show_entries frame=best_effort_timestamp_time -of csv=p=0 "$V" > tmp/vulcan-capture/pts_video.txt

# audio track, mono 48 kHz, for the fire window
"$FF/ffmpeg.exe" -v error -y -i "$V" -vn -ac 1 -ar 48000 -c:a pcm_s16le tmp/vulcan-capture/audio/vulcan.wav

# a full frame at a given time (used for the crop survey)
"$FF/ffmpeg.exe" -v error -y -ss 12.0 -i "$V" -frames:v 1 tmp/vulcan-capture/frames/full_12.png

# exact frames by index (used for the raw radial profiles)
"$FF/ffmpeg.exe" -v error -y -i "$V" -vf "select='eq(n,316)+eq(n,341)+eq(n,359)+eq(n,370)'" \
  -vsync 0 tmp/vulcan-capture/seq_full/full_%04d.png

# the two measurement passes
python tmp/vulcan-capture/measure2.py   # threshold set A
python tmp/vulcan-capture/measure3.py   # threshold set B (thresholds taken from a raw pixel dump)
```

**Stream facts (measured).** 1920×1080, h.264 yuv420p, nominal `r_frame_rate` 60000/1001, **1352 frames**,
duration 49.166 s, audio AAC 48 kHz stereo 49.152 s. PTS are **variable**: frame 0 at 0.047 s, spacing
0.007–0.035 s around the transition (13.457 → 13.492 s = 0.035 s). Every timestamp below is a PTS, and the
frame index is given beside it — a frame count alone would be wrong (the clip averages ~27.5 decoded
frames/s, not 60).

---

## 2. Audio: fire start and fire stop

Method: 48 kHz mono, first-difference high-pass (broadband transient band, which is where gunfire sits and
where the engine does not), 5 ms RMS frames in dB. Baseline = median of 0–8 s. Threshold = baseline + 12 dB.
Sample index *i* → *t* = 0.005·*i*.

| quantity | value | label |
|---|---|---|
| baseline 0–8 s | **−62.6 dB** | measured |
| threshold | −50.6 dB | derived (baseline + 12) |
| **fire start** | **11.120 s** (sample 2224); the 25 dB step begins in the 5 ms bin at 11.115 s | **measured** |
| level while firing | −38 … −41 dB (peaks −26.7 dB full-band at 16.5 s) | measured |
| **fire stop** | **none in the clip** — last above-threshold run 48.890 → 49.140 s, file ends 49.14 s | **measured** |
| pre-fire quiet | 10.00–11.11 s reads −66 … −68 dB (car moving, no gun) | measured |

The earlier 2.9–6.25 s transients are ambient (rotor/impacts), 30–40 dB below the gun; they do not pass the
12 dB-above-baseline gate at the same level and are excluded by the 0.08 s minimum run.

**This contradicts the brief's "firing between about 10 s and 15 s".** On this evidence the trigger is held
from 11.120 s to the end of the file. Consequence: **the cool-down is not in this clip**, so the
time-to-return is not observable here (§6).

---

## 3. Video: what the reticle actually is

Cropped survey (`tmp/vulcan-capture/frames/contact_small.jpg`, 8–18 s; `tmp/vulcan-capture/frames/zoom.png`,
12.0/12.6/13.0/13.4/14.0/16.0) shows a **fixed-size ring with four gaps at N/E/S/W**, and **four arrow ticks
that travel outward along those gaps**. The ring does not move; the ticks do. Colour is white until the ticks
have passed the ring, then red. The green arc below is a separate lock/progress element and is excluded.

So two numbers are measurable per frame:

* `r_ring` — radius of the white ring, the reticle's own reference scale (px, from a circle fit);
* `r_spread` — radius of the tick tips from the reticle centre (px) = the spread the operator sees;
* `mean_RG` — mean (R−G) over the lit pixels of the outer annulus (30–52 px): the **red level**, in 8-bit
  code values, independent of any colour classifier.

**Method (and why it is the method).** The reticle centre and ring radius come from an iterative trimmed
algebraic (Kasa) circle fit on ring pixels, not from a fixed screen guess: v1 used a fixed centre and the
estimate drifted 5–10 px, which dragged the radius with it and produced a fake frame-to-frame alternation.
The tick tips are the median of four axis scans (a ±8° sector around each cardinal direction, which lies in
the ring's gaps). The median, not the max, is used because a HUD glyph or a lit window can sit on one axis
only. Both threshold sets agree on every headline below:

| set | white | red |
|---|---|---|
| A (`measure2.py`) | min(R,G,B) > 150, neutral | R > 110, R−G > 50, R−B > 50 |
| B (`measure3.py`) | min(R,G,B) ≥ 185, neutral | R ≥ 150, R−G ≥ 40, R−B ≥ 40 |

Set B's thresholds were taken from a raw dump along the axes (frame 316/341/359): ring pixels read
(197,221,225)…(241,242) min-channel, the background building 46–108, red tick cores (219,162,143)/(255,175,164).
Set A admitted lit windows; that is the only difference between the sets, and it changes no timestamp.

**Known limit.** While the ticks are inside the ring the annulus scan runs along the ring's gap, so the tick
is measured down to ~10 px but the ring itself sits at 22–26 px in the same sector; the two are not separable
below ~50 % bloom (see §7).

---

## 4. The per-frame table (frames 332–361, the whole transition)

`fr` = decoded frame index, `t` = its PTS, `r_ring`/`r_spread` in px, `red` = red fraction of lit pixels in
the tick annulus, `RG` = mean (R−G) there. Full tables: `tmp/vulcan-capture/table_v3.txt`,
`tmp/vulcan-capture/reticle_frames_v3.json`.

| fr | t (s) | r_ring | r_spread | tips U/D/L/R | red | RG | state |
|---:|---:|---:|---:|---|---:|---:|---|
| 332 | 12.548 | 25.5 | 26.0 | 33.7 / 21.6 / – / 30.4 | 0.000 | −21.0 | spread at rest |
| 334 | 12.682 | 25.9 | 25.7 | 32.7 / 21.6 / – / 29.8 | 0.000 | −21.5 | **first departure (>2 px), measured** |
| 335 | 12.717 | 26.1 | 30.2 | 34.6 / 21.6 / 29.7 / 30.6 | 0.000 | −21.1 | rising |
| 336 | 12.750 | 26.0 | 32.7 | 34.7 / 54.4 / 29.7 / 30.7 | 0.000 | −20.7 | rising (54.4 = scene edge on the down axis, outlier) |
| 338 | 12.875 | 26.3 | 31.8 | 37.5 / 22.6 / 30.8 / 32.7 | 0.000 | −18.9 | rising |
| 341 | 12.999 | 26.6 | 32.7 | 39.6 / 22.6 / 31.6 / 33.7 | 0.000 | −20.7 | rising (zoom at 13.0: ticks at the ring) |
| 346 | 13.217 | 27.3 | 34.6 | 41.3 / 22.9 / 33.4 / 35.7 | 0.000 | −21.3 | rising |
| 348 | 13.322 | 29.1 | 35.5 | 43.4 / 24.8 / 35.2 / 35.8 | 0.000 | −20.0 | ticks crossing the ring |
| 351 | 13.424 | 28.7 | 35.5 | 43.4 / 24.8 / 35.3 / 35.7 | 0.000 | −19.8 | **last all-white frame, measured** |
| 352 | 13.457 | 25.1 | 37.2 | 40.0 / 36.0 / 38.3 / 35.9 | **1.000** | **+14.3** | **red on, one-frame switch, measured** |
| 353 | 13.492 | 25.1 | 37.1 | 40.1 / 35.9 / 38.3 / 35.9 | 1.000 | +13.1 | red, still opening |
| 356 | 13.590 | 25.0 | 37.4 | 40.0 / 36.0 / 38.8 / 35.9 | 1.000 | +13.3 | red, still opening |
| 357 | 13.633 | 25.0 | **39.8** | 42.1 / 39.0 / 40.6 / 38.9 | 0.985 | +30.4 | **plateau reached, measured** |
| 359 | 13.689 | 25.0 | 40.1 | 42.1 / 39.0 / 41.3 / 38.9 | 0.958 | +30.8 | plateau |
| 370 | 14.059 | 25.3 | 40.3 | 42.7 / 39.7 / 40.8 / 39.6 | 1.000 | +59.3 | plateau, red at full brightness |

After 14.1 s every frame to the end of the file reads `r_spread` 39.9–41.6 px, `red` 0.74–1.00, `RG` +17…+68:
per-second medians are in `tmp/vulcan-capture/reticle_frames_v3.json`, and the last analysed frame
(frame 1351, PTS 49.133 s) reads **41.6 px / red 4-of-4 axes / RG +24**.

`r_ring` is **25.0–25.3 px** on every clean frame (11.0–12.6 s and 13.63 s onward); the 27–29 values in
13.2–13.4 s are the fit being pulled by the ticks as they cross the ring, not the ring growing.

---

## 5. The measured timeline

Fire start = 11.120 s (audio, §2). Relatives are derived from it; the absolute times are measured.

| event | abs. time (measured) | frame | rel. to fire start (derived) | spread px | label |
|---|---:|---:|---:|---:|---|
| trigger down (audio step) | **11.120 s** | between 290 / 291 | 0.00 s | ~10–22 (inside ring) | measured |
| ticks first clear the ring, spread measurably departs | **12.682 s** | 334 | **+1.56 s** | 25.7 → 30.2 | measured (onset) / derived (relative) |
| ticks fully outside the ring | 13.424 s | 351 | +2.30 s | 35.5 | measured |
| **colour turns red** | **13.457 s** | 352 | **+2.34 s** | 37.2 | measured |
| **spread plateaus** | **13.633 s** | 357 | **+2.51 s** | 39.8 → 40.6 | measured |
| trigger released | **not in clip** | – | – | – | not observed |
| spread returns to rest | **not in clip** | – | – | – | **UNKNOWN** |
| red returns to white | **not in clip** | – | – | – | **UNKNOWN** |

**Spread amplitude.** Rest: the ticks sit inside the ring (10–22 px by axis scan; unresolved below the ring
radius). Plateau: **40.6 px median** over 13.633–49.133 s (41.5 px under threshold set A; spread of the
per-second medians 39.9–41.6). Reference: ring radius **25.0 px**. So the ticks travel to **1.62× the ring
radius** — the plateau is not "the ring", it is a fixed outer limit the ticks reach and hold.

**Red level.** `RG` = −19…−22 before the switch, +13…+14 in the three frames right after it, +17…+68 from
14.0 s (the red saturates over ~0.5 s *after* the switch). Colour, not size, is what changes first at the
transition.

---

## 6. Does the player behaviour match `InaccuracyVsTime`?

File values (`FOOTAGE.md` §2, re-read from `WEAPONS.json` there): `InaccuracyAngle` **0.1**, curve
**0.0 s→0.0, 0.5 s→0.0, 1.5 s→1.5, 2.5 s→3.0** (linear, `CIM_Linear`), upgraded curve 0→0, 1→0, 3→1.5,
5→3.0; `HeatUpPerSecond` **0.0**.

| check | expectation from the file | measurement | verdict |
|---|---|---|---|
| no fire-rate ramp | interval constant 0.138 s | not measurable from this clip (no muzzle in frame; `FOOTAGE.md` §1 stands) | **UNKNOWN** |
| bloom holds ~flat for the first 0.5 s | no movement before +0.50 s | ticks inside the ring, unmeasurable 0–1.5 s | **consistent, not proven** |
| bloom reaches 50 % at 1.5 s | ticks halfway out | first *visible* departure at **+1.56 s**, right where the ticks clear the ring (~50 % of 40.6 px ≈ 20 px, ring at 25 px) | **match, within one frame** |
| bloom complete at 2.5 s | movement stops | plateau at **+2.51 s** (13.633 s) | **match to 0.01 s** |
| nothing interrupts fire | `HeatUpPerSecond` 0.0 → no overheat | fire continuous 11.12 → 49.14 s, reticle never drops | **match** |
| cool-down returns spread | curve decays when fire stops | trigger never released in this clip | **UNKNOWN** |

**Reading.** The two endpoints the curve pins down are exactly the two the capture can resolve without
ambiguity, and both land: half-bloom at +1.56 s against 1.5 s, full bloom at +2.51 s against 2.5 s. The
0.5→1.5 s segment is predicted but **not measurable in this clip**, because the tick marks are inside the
ring for the first half of the travel. That is a property of the reticle art, not a contradiction: the
measured onset is the first moment the bloom is *visible*, not the first moment it is non-zero.

So: **the capture is consistent with the time-based bloom and adds nothing that contradicts it.** It does not
prove the curve's shape — a per-shot ramp tuned to the same endpoints would look identical at 31 fps.

---

## 7. Where the red comes in, and what `OverheatOffValue` 0.25 can and cannot explain

**What the capture settles (measured):**

1. Red is a **binary switch on one frame** (13.457 s), not a fade: `red` 0.000 → 1.000, `RG` −19.8 → +14.3,
   in both threshold sets. A continuous heat bar filling would produce a ramp, not a step. A **threshold
   test** on some scalar produces exactly this.
2. The switch happens **0.17 s before** the spread stops growing, at 37.2 px = **1.49 × r_ring** (92 % of the
   40.6 px plateau) — i.e. just after the ticks have fully cleared the ring (13.424 s, 1.39 × r_ring).
3. Every sample after it is red; there is no sample that reverts.

**What the file side offers (decoded, from `vulcan-spinup-and-heat-plan.md` §4 / `FOOTAGE.md` §2):**
`HeatUpPerSecond` **0.0** (no per-second heat), `OverheatOffValue` **0.25** (the value heat must fall to
before the weapon is usable again), `bOverheating` False, `HeatBarStart` [0.79, 0.68], `HeatBarSize`
[0.125, 0.03], `ChainGunOverheatSound`/`ChainGunCooledSound` present — and **no heat cap and no cool rate
anywhere in the object**.

**So `OverheatOffValue` 0.25 cannot be the red trigger.** It is a *release* threshold: the value the heat must
drop **to** before the gun is usable again, paired with a cool-down. It says nothing about where heat starts
or what colour the reticle is. On the shipped defaults it is unreachable, because `HeatUpPerSecond` is 0.0 —
which is precisely the "never locks out" the operator reports.

**Two readings of the red survive this evidence, and this clip cannot separate them:**

| # | reading | predicts | status |
|---|---|---|---|
| R-a | a HUD colour state switched by the **spread** crossing a threshold (~92 % of bloom) | red follows the bloom, clears with it | consistent; no member in the grab names reticle colour |
| R-b | a **heat** scalar accumulating during fire, with red at full heat and 0.25 as the clear value | red clears only when heat ≤ 0.25, i.e. later than the spread | also consistent; requires a per-shot heat input that is not in the files (`HeatUpPerSecond` 0.0) |

They diverge only on **release**: R-a clears red when spread returns; R-b clears it later, after heat falls
through 0.25. The capture never releases the trigger, so neither is excluded, and neither is proven.
**Mechanism: UNKNOWN.** Settler: one clip that fires ~3 s, releases, and holds still — if red clears with the
spread, R-a; if red stays after the ticks are back at rest and then clears, R-b, and the extra delay is the
heat decay to 0.25.

---

## 8. The closest JC3 system, and the values to write

Two separate asks: the **spread tune** and the **HUD crosshair colour**.

### 8.1 Spread tune — `WeaponTuning.bullet_weapon[].tuning.base_tuning.scatter.*`

This is JC3's only spread model: `scatter_minimum`, `scatter_maximum`, `scatter_per_shot`,
`scatter_recover_rate`, `scatter_reset_time`, `scatter_multiplier_movement`, `scatter_multiplier_aiming`,
`scatter_clamp_horizontal/vertical` (`Research/JC3Grab/WEAPONS.md` §4). It has **no time-based bloom** — the
growth axis is *per shot*, so the BmAK curve has to be re-expressed as shots at the 0.138 s interval.

The right donor is **`w620_racingboat_mgun`**, the only gatling in the fleet with a growing spread:
`scatter 0.2 / 1.85 / 0.1`, recover 0.35, reset 1.0 (player side). `w604`/`w607`/`w622` ship a *fixed*
0.75/0.75/0 and `w610` 0.25/0.25/0 — no bloom at all.

Shots to full bloom: 2.51 s ÷ 0.138 s = **18.2 rounds** (derived; fire interval from
`vulcan-spinup-and-heat-plan.md` §2).

| BmAK quantity | value | JC3 member | value to write | label |
|---|---:|---|---:|---|
| base spread | `InaccuracyAngle` 0.1 | `scatter.scatter_minimum` | **0.1** | derived (same-unit assumption, see below) |
| full bloom | `InaccuracyVsTime` p3 = 3.0 | `scatter.scatter_maximum` | **3.0** | derived |
| bloom over 2.51 s / 18.2 rounds | (3.0 − 0.1) / 18.2 | `scatter.scatter_per_shot` | **0.159** | derived |
| recover | not observable here | `scatter.scatter_recover_rate` | **0.35** (keep `w620`) | UNKNOWN-driven |
| reset | – | `scatter.scatter_reset_time` | **1.0** (keep `w620`) | donor |
| fire interval | 0.138 s | `fire_rate` | **0.138** | file value |
| reticle scale | 40.6 px / 25.0 px = **1.62×** | `UISettings.scatter_at_smallest/biggest`, `reticle_size_smallest/biggest` | **0.1 / 3.0** and **0 / 1** | derived (matches the tune's endpoints, as `w620` does with 0/1.85 and 0/1) |

**Donor-preserving alternative** if the 0.1→3.0 scale is not wanted: keep `scatter_minimum` 0.2 and
`scatter_maximum` 1.85 from `w620` and set `scatter_per_shot` = 1.65 / 18.2 = **0.091**. Same 2.5 s ramp,
`w620`'s own amplitude.

**Unit caveat (do not skip).** Neither `WEAPONS.md` §4 nor the BmAK side names the unit of `scatter.*` or of
`InaccuracyAngle`; both are bare floats. Writing 0.1/3.0 assumes the two are the same measure (an angular
deviation in the same scale). If they are not, keep the donor's amplitude (the alternative above) — it
reproduces the **timing**, which is what the capture measured.

### 8.2 HUD crosshair colour — there is no member

From `Research/JC3Grab/JC3_HUD_WEAPONS.md` §4–§7:

* The reticle is drawn by `UpdateWeaponReticle(show, weapons_look, reticle_size, reticle_shape)`; the colour
  input is `weapons_look`, one of **five relationship states**: `ECrosshairLook_InRangeTargetNeutral` 0,
  `...Allied` 1, `...Hostile` 2, `...InRangeNoTarget` 3, `...OutOfRange` 4 (the last also sets alpha 0.4).
  **None of them is a heat or bloom state** — they say *what you are pointing at*, not *how long you have
  fired*.
* `E_RETICLE_CANNON` = 8 is the cannon shape, and it is in the **fall-through group**: only 5 of the 14 shapes
  compute a width, so `reticle_size` has **no effect** on shape 8 (T-19 A2, `challenge/card-T-19.md`). A port
  that hopes to show spread by growing a shape-8 reticle will show nothing.
* The only tint the movie animates is the cooldown/overcharge one (`SetCooldownRotation` 0..1 → 360°,
  `AnimateOvercharged`, overcharge sound `dlc_wingsuit_weapon_ready`), and its colour values are not decoded.

**So the finished answer to "where does the red come from" on the JC3 side: it does not exist.** The nearest
two hooks, neither of which is a red-on-sustained-fire crosshair:

| need | JC3 hook | what you actually get | verdict |
|---|---|---|---|
| crosshair that grows with spread | `UISettings.scatter_at_smallest/biggest` + `reticle_size_smallest/biggest` on a shape that has a size rig (`E_RETICLE_AUTO` 4, `..._CIRCLE`, `..._FLAK`, `..._ROCKET`, `..._SINGLE_SHOT`) | size follows scatter | **works, but not on shape 8** |
| crosshair that turns red with fire | none; only the 5 `ECrosshairLook_*` relationship colours and the overcharge tint | red only for hostile targets, or an undecoded overcharge tint | **stated absence** |

If the red has to be reproduced, it is a **new UI element** (a custom movie/`MCI` clip driven by the scatter
value), not a tune — and BmAK's own numbers say the switch belongs at **~92 %** of `scatter_maximum`
(measured, §5), with the clear value left at `scatter` back to rest since the capture does not contain the
release.

---

## 9. UNKNOWNs

| # | UNKNOWN | settler |
|---|---|---|
| U-1 | time for the spread to return after the trigger is released | a clip that releases the trigger; this capture holds it to 49.14 s |
| U-2 | whether red is a spread threshold (R-a) or a heat state (R-b) | the same clip, judged on *order*: red clears with the ticks (R-a) or after them (R-b) |
| U-3 | the unit of `scatter.*` and of `InaccuracyAngle` | no member or doc in either grab names it; only a live A/B where scatter is changed and the group size measured |
| U-4 | the curve's shape between 0.5 s and 1.5 s | not measurable here — the ticks are inside the ring below ~50 % bloom |
| U-5 | whether a per-shot heat input exists in native code | not excluded by the grab (`FOOTAGE.md` §2 keeps it open); would show as red clearing later than the spread |
| U-6 | actual reticle colour values in `hud.gfx` | the 5 look states have names, not decoded RGB |

---

## 10. Change record (per `AGENTS.md`)

1. **Intended change:** add this one measurement report; add the measurement scripts that produce its tables;
   extract audio/frames into `tmp/` (the capture itself is read in place and **not** copied in).
2. **Files:** `tmp/freebuff/reports/vulcan-capture-fire-and-overheat-timing.md` (this report, the path the
   brief names); `tmp/vulcan-capture/measure2.py`, `measure3.py` (measurement), `tmp/vulcan-capture/*.json`,
   `*.txt`, `frames/*.png|jpg`, `audio/vulcan.wav` (derived data cited above). No `Research/` card was
   regenerated; no build, tune or archive file was written; no game process was started.
3. **Why these files:** every comparable plan/report lives in `tmp/freebuff/reports/`; the measurement
   artefacts are derived data, so they belong under `tmp/` and not in `Research/`.
4. **Revert:** delete those paths (`rm -rf tmp/vulcan-capture tmp/freebuff/reports/vulcan-capture-fire-and-overheat-timing.md`).
   Nothing else changed — the reads were `ffprobe`, `ffmpeg`, `cv2` and text queries.

## 11. Checks run

| check | result |
|---|---|
| ffprobe reads the capture in place | PASS — 1920×1080, 1352 frames, 49.166 s, VFR |
| the capture is not inside the workspace | PASS — read from `C:\Users\User\Videos\Captures`, only derived data in `tmp/vulcan-capture` |
| audio fire start reproducible | PASS — one 24 dB step, 11.115 s bin, threshold crossing 11.120 s |
| audio shows a fire stop | FAIL (as expected) — level stays up to 49.140 s, so U-1 stands |
| every reported timestamp is a PTS with its frame index | PASS — §4/§5 tables |
| red onset reproducible across two threshold sets | PASS — both give frame 352 / 13.457 s |
| red onset is a single-frame switch, not a ramp | PASS — red 0.000 → 1.000, RG −19.8 → +14.3 |
| ring radius constant on clean frames | PASS — 25.0–25.3 px |
| plateau value stable to the end of the clip | PASS — 39.9–41.6 px per second, last frame 41.6 px |
| bloom end vs curve end | PASS on the measurement: +2.51 s vs 2.5 s |
| bloom start vs curve start (0.5 s) | NOT TESTABLE here — ticks inside the ring; recorded as U-4 |
| `HeatUpPerSecond` 0.0 in the grab, re-read | PASS — `FOOTAGE.md` §2 |
| `OverheatOffValue` 0.25 re-read and its role stated | PASS — release threshold, unreachable at 0.0 heat/s |
| JC3 spread members exist with values | PASS — `scatter.*`, `w620` donor 0.2/1.85/0.1 |
| JC3 reticle_size on shape 8 | FAIL (documented) — shape 8 has no size rig; noted so the port does not rely on it |
