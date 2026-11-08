STATUS: done — the Vulcan fire event in the operator's capture is measured from presentation timestamps; the spread is the time-based `InaccuracyVsTime` curve (dead 0.5 s, ramp to max at 2.5 s, hold), `HeatUpPerSecond` 0.0 is consistent with 38.05 s of uninterrupted fire, and rounds/second is UNKNOWN because the muzzle is in no frame.

# Vulcan capture frame timing (BmAK, operator brief 2026-11-08)

Source: `C:/Users/User/Videos/Captures/Batman™_ Arkham Knight VulcanFire_10s-15s.mp4`
— 1352 frames, last PTS 49.205 s, nominal 60000/1001, **variable framerate**
(frame durations 0.0077 s … 0.0585 s, ~27.5 frames/s average). Every number below is a
PTS difference, never a frame count (the method in `Research/BatmobileGrab/FOOTAGE.md` §1).

## 1. What the HUD actually does (measured, not assumed)

The battle-mode reticle is drawn as a **fixed ring + four radial arms at N/E/S/W**:

| element | measurement |
|---|---|
| ring | fixed circle, radius **25 px**, screen (961, 378) — it never moves and never grows |
| arms | slide **outward through the ring**: tip **18.5 px** at rest (arms inside the ring, r 6–20), tip **41.0 px** fully out (r 29–41) — **2.216×** |
| colour | the arms' tips fade white → red as they travel out; the ring itself never changes colour |

The first metric I tried (ring radius) is a trap: the ring is constant, so a ring-radius probe
reports "no bloom" while the reticle visibly blooms. The probe is now the arm tip in a
±4° wedge (inside the ring's cardinal gaps, so neither ring nor green arc is sampled), with the
arm colour read from the same contiguous run.

## 2. The table

| quantity | value | PTS | frame | how it was read |
|---|---|---|---|---|
| **trigger** (firing starts) | — | **11.156 s** | — | audio onset: 2 ms high-pass envelope `0.002689 → 0.008523` (threshold 0.009909). The muzzle is out of frame, so the trigger instant comes from the audio stream's PTS, on the same timeline as the video PTS (container start 0.000, video start 0.047) |
| last frame at the narrow reticle | — | 11.697 s | 305 | arm tip 18.5 px |
| **trigger → first visible spread** | **0.576 s** | 11.732 s | 306 | arm tip leaves 18.5 px (→ 20.5 px) |
| **trigger → full spread** | **2.545 s** | 13.701 s | 357 | arm tip reaches 41.0 px and holds to the last frame |
| **trigger → crosshair turns red** | **2.374 s** | 13.530 s | 352 | all four arm tips flip white → red inside one frame interval (0.033 s) |
| spread onset → full spread | 1.969 s | | | |
| spread onset → red | 1.797 s | | | |
| **cool-down back to narrow after release** | **UNKNOWN — not in this clip** | — | — | arm tip is still 41.0 px at the last frame (49.205 s); the only dips (39.5 px at 26.829 s and 31.688 s) are single-frame HUD jitter, not a collapse |
| **rounds per second, from muzzle flashes** | **UNKNOWN — muzzle not in frame** | — | — | see §4 |
| continuous fire recorded, no interruption | **38.049 s** | 11.156 → 49.205 s | 1045 frames | |

Red is **not** the "fully spread" marker: it arrives at arm tip 39.0/41.0 px — 91 % of the
travel — 0.171 s *before* the plateau.

## 3. Against the decoded curve (`InaccuracyVsTime`, `HeatUpPerSecond` 0.0)

Decoded points (G1-23 / `Research/BatmobileGrab/WEAPONS.md`): 0 s → 0.0, 0.5 s → 0.0,
1.5 s → 1.5, 2.5 s → 3.0, linear between, on top of `InaccuracyAngle` 0.1.

| curve feature | curve | measured from the trigger | difference |
|---|---|---|---|
| dead segment ends (first growth) | 0.5 s | 0.576 s | **+0.076 s** |
| maximum reached | 2.5 s | 2.545 s | **+0.045 s** |
| holds at maximum after 2.5 s | yes (last point) | yes: 41.0 px from 13.701 s to the clip end | — |
| red state | **no curve point** | 2.374 s | — |

**Verdict: the curve explains the spread.** The two things the curve predicts — a flat
0.5 s before any growth, then a monotone ramp to a maximum at 2.5 s — are both in the footage
within **±0.08 s (~2.5 frames** at the capture's 0.033 s cadence, and inside the ±0.03 s A/V
uncertainty), and the maximum then holds exactly as the curve's last point implies. The
*dead segment* is the part a naive reading would miss: the first 0.58 s of the burst looks
identical to not firing at all, which is why the arms had to be measured, not eyeballed.

`HeatUpPerSecond` 0.0 is **consistent and nothing contradicts it**: 38.049 s of continuous
fire, no interruption, no overheat lockout, and no heat element changes on the HUD. What the
curve does **not** explain is the white → red state: the curve has no colour axis, so red is a
separate HUD threshold at 91 % of the bloom.

## 4. Rounds per second — UNKNOWN, and why

The operator asked for rounds/second from muzzle flashes. **The muzzle and the car are in no
frame of this clip**: the capture is a fixed battle-mode aim at a tower, five scene frames
sampled at 12 / 20 / 30 / 40 / 48 s show HUD + skyline only (`vulcan_scene_*.png`), and no
impact flash train is visible on the target either. What the audio can say:

| audio measurement (secondary, **not** a round count) | value |
|---|---|
| envelope autocorrelation peak, 13.5–16.0 s | 0.028 s (35.71 /s, ac 0.386) |
| correlation at the decoded 0.138 s fire interval | 0.211 |
| track still active at 48–49 s | 0.015275 |

The audible cadence is the minigun **loop's grain**, not a resolved round train, so it cannot
be turned into rounds/s. Per R4 the file value stands: `FiringInterval` **0.138 s = 7.25
rounds/s** (`Research/BatmobileGrab/WEAPONS.md`, T-WP2). The capture neither confirms nor
refutes it.

## 5. What this means for the HUD and the T-WP rows

### Vulcan bloom HUD (`T-HUD15`, `T-HUD14`, `T-HUD16`, `T-HUD17`)

1. **The size half fits JC3 as it is.** The bloom's whole travel is **22.5 px** (18.5 → 41.0),
   and JC3's `reticle_size` domain is **5…30 px** (`t19_hud.json` T-HUD15). The BmAK travel is
   0.90 of JC3's domain, so a *derived* map exists with no new member:
   `reticle_size = 5 + 25 · (tip − 18.5) / 22.5` — 0.576 s of nothing, then 2.0 s of ramp.
2. **But T-HUD14 currently forecloses T-HUD15.** `Research/challenge/card-T-19.md` §A2 proves
   `E_RETICLE_CANNON` (shape 8) sits in the fall-through group of `UpdateWeaponReticle` with no
   assignment to `new_width`: on shape 8, `reticle_size` is inert. The footage makes the cost
   concrete — this BmAK reticle *is* size-rigged (2.216× over 2.0 s), so the JC3 side needs a
   shape that consumes `reticle_size` (single-shot/auto, circle, flak, rocket) or a custom clip.
   The row pair cannot ship as written.
3. **The red state has no carrier in the rows we hold.** T-HUD14/15/16 name shape, size and the
   0…4 cooldown state only; no tint/colour member is named on the reticle path, and the capture
   shows the red as a discrete threshold at 91 % of the bloom, 0.171 s before the plateau. This
   is a **named omission or a new card**, not a value to hand-substitute; whether a tint member
   exists elsewhere in the HUD is UNKNOWN (not searched here).
4. **T-HUD16 (cannon cooldown) stays unverified.** The clip has no release, so the 5-state
   `UC_SetCannonCoolDown` → `weapon_cooldown` map has no footage check from this capture. The
   operator's "the cool-down only brings the spread back" remains an observation, not a
   measurement.
5. **T-HUD17 (Vulcan heat, named omission) is now positively supported**: 38.049 s of fire with
   no interruption is the longest no-overheat sample in the project, and no heat element moves.

### Weapon rows (`Working/Translation/T7_WEAPONS.md` §T-WP2)

| row / aspect | before | now |
|---|---|---|
| **spread curve** (`shape maps, numbers do not`) | shape only: "0 for the first second, then a ramp" | **numbers**: 0 for **0.576 s**, linear to max at **2.545 s**, then hold; **2.216×** radius, red at 2.374 s. The shape and its timing are now measured |
| carrier for that shape | `scatter` 0.6/0.6, per-shot 0, recover 0.4, reset 1.15 | **the mismatch is now explicit**: JC3 grows scatter **per shot** and recovers with `scatter_recover_rate` / `_reset_time`; BmAK grows it with **held-trigger time** and never recovers while held. A faithful cut is either a native hook feeding scatter from held-trigger time (permitted 2026-11-08) or a per-shot approximation: at 7.25 rounds/s ≈ **18 rounds** to full and **≈ 4 rounds** of dead time — and JC3 has **no dead-zone member** (UNKNOWN / named omission) |
| **fire rate** 0.1 → 0.138 s | decoded, Q-3 #3 wants 14 ± 1 impacts in 2 s | **unchanged**: footage cannot confirm it (no muzzle, no impacts in frame); the file value stays (R4) |
| **heat / overheat** (`HeatUpPerSecond` 0, `OverheatOffValue` 0.25) | file value + operator observation | **footage-backed**: 38.049 s continuous, no lockout, no visible heat change |
| Q-3 #3 verify sentence | "14 ± 1 impacts and no overheat" | the **no-overheat half is now evidenced**; the impacts half is untestable in this capture. The verify sentence should say which half this footage covers |

No value here overrides a file value (R4): every footage number closes only what no file answers
(the shapes of the bloom, the red threshold, the trigger→bloom timing, the no-overheat window).

## 6. Files written

| file | what |
|---|---|
| `Tools/scripts/vulcan_capture_timing.py` | new; `--probe` prints the per-frame table, `--write` regenerates the two records below + the PNGs, `--check` re-decodes and recomputes every value |
| `Research/BatmobileGrab/VULCAN_CAPTURE.json` | the machine record (1352 frames' measurements, events, audio, PNG list) |
| `Research/BatmobileGrab/VULCAN_CAPTURE.md` | the same, readable, with the per-frame table 11.5–17.5 s |
| `E:/Modding/ArkhamKnight/_grab/footage/vulcan/` | 15 PNGs, below |

Key frames (full frame + 600×600 reticle crop, 2× nearest):

| key | frame | PTS | file |
|---|---:|---:|---|
| narrow_last | 305 | 11.697 | `vulcan_narrow_last_f0305_t11.697s.png` (+ `_reticle.png`) |
| spread_on | 306 | 11.732 | `vulcan_spread_on_f0306_t11.732s.png` (+ `_reticle.png`) |
| red_on | 352 | 13.530 | `vulcan_red_on_f0352_t13.530s.png` (+ `_reticle.png`) |
| full_on | 357 | 13.701 | `vulcan_full_on_f0357_t13.701s.png` (+ `_reticle.png`) |
| last_wide | 1351 | 49.205 | `vulcan_last_wide_f1351_t49.205s.png` (+ `_reticle.png`) |
| scene | — | 12 / 20 / 30 / 40 / 48 | `vulcan_scene_t012.0s.png` … `vulcan_scene_t048.0s.png` (the muzzle/car check) |

## 7. Commands and their output (verbatim)

```
$ ffprobe -v error -show_streams -show_format -of json "…VulcanFire_10s-15s.mp4"
    "codec_name": "h264", "width": 1920, "height": 1080,
    "r_frame_rate": "60000/1001", "avg_frame_rate": "20280000/737497",
    "nb_frames": "1352", "duration": "49.166467", "start_time": "0.047000"
  audio: "codec_name": "aac", "sample_rate": "48000", "channels": 2, "duration": "49.151979"
```

```
$ ffprobe -v error -select_streams v:0 -show_entries frame=pts_time,duration_time -of csv=p=0 …mp4 | head -3
0.047000,0.008967
0.054700,0.007700
0.062833,0.008133
```

```
$ uv run --with numpy python Tools/scripts/vulcan_capture_timing.py --write
{
 "baseline_arm": 18.5,
 "peak_arm": 41.0,
 "narrow_last": 11.697,
 "spread_on": 11.732,
 "full_on": 13.701,
 "red_on": 13.53,
 "last_wide": 49.205,
 "narrow_back": null,
 "idx": {
  "narrow_last": 305,
  "spread_on": 306,
  "full_on": 357,
  "red_on": 352,
  "last_wide": 1351,
  "narrow_back": null
 },
 "t_spread_from_narrow": 0.036,
 "t_full_from_spread": 1.969,
 "t_full_from_narrow": 2.005,
 "t_red_from_spread": 1.797,
 "t_red_from_narrow": 1.833,
 "t_full_to_narrow_back": null,
 "t_wide_total": 37.508,
 "wide_at_clip_end": true,
 "clip_end_pts": 49.205,
 "growth_ratio": 2.216,
 "trigger": 11.156,
 "t_spread_from_trigger": 0.576,
 "t_full_from_trigger": 2.545,
 "t_red_from_trigger": 2.374,
 "fired_until": 49.205,
 "continuous_fire_s": 38.049
}
{"lookback_from": 10.532, "quiet_median": 0.001982, "threshold": 0.009909, "trigger_pts": 11.156, "pre_trigger_env": 0.002689, "post_trigger_env": 0.008523, "period_s": 0.028, "period_ac": 0.386, "per_s": 35.71, "ac_at_0_138": 0.211, "tail_env_48_49": 0.015275}
```

```
$ uv run --with numpy python Tools/scripts/vulcan_capture_timing.py --check
PASS 25 event values, 10 key frames, 1352 frames re-decoded
check exit=0
```

Per-frame evidence (arm tip / red score), from `--probe`, in the report body's source record
`Research/BatmobileGrab/VULCAN_CAPTURE.md` §"Per-frame table 11.5-17.5 s":

```
305 11.697 tip=18.5 red=-14.2   <- last narrow frame
306 11.732 tip=20.5 red=-14.8   <- first visible spread
351 13.495 tip=37.5 red=-14.6
352 13.530 tip=39.0 red=+57.7   <- arms turn red (4/4 directions)
357 13.701 tip=41.0 red=+68.6   <- full spread, holds
1351 49.205 tip=41.0            <- still fully spread at the last frame
```

## 8. UNKNOWNs

| # | unknown | what I tried | why it is still unknown |
|---|---|---|---|
| 1 | **rounds per second from muzzle flashes** | scanned all 1352 frames' aim region and the lower third for a periodic flash train; sampled 5 scene frames; measured the audio's transient cadence | the muzzle, the car and any impact flash are outside the frame for the whole clip; the audio's cadence (0.028 s) is the mix's grain, and its 0.138 s lag correlates at only 0.211, so no per-round transient can be separated. Would need a capture that includes the barrels |
| 2 | **cool-down time back to the narrow crosshair** | probed arm tip for every frame from 13.7 s to the clip end | the trigger is never released inside the clip (tip 41.0 px at 49.205 s), so there is no release → narrow transition to time; only a longer capture with a release can close it |
| 3 | **exact trigger instant** | audio onset at 2 ms resolution | the video shows no muzzle/ammo/impact cue, so the trigger is known only from the audio track, ±0.002 s in the audio plus the unknown capture A/V offset (video starts 0.047 s after the audio). If a later capture shows the muzzle, the trigger can be confirmed against it |
| 4 | **whether the red state has a JC3 carrier** | searched the decoded reticle rows (`t19_hud.json` T-HUD14/15/16) and `Research/JC3Grab/WEAPONS.md` reticle numbers | those rows name shape, size and cooldown state only; a tint member elsewhere in `hud.gfx` was not searched here, so this is UNKNOWN rather than "absent" |
| 5 | **whether the bloom is one continuous HUD value or a stepped accuracy frame** | per-frame arm tip | the tip moves 18.5 → 41.0 in 0.5 px steps with no visible quantisation (no plateau at intermediate values), which is consistent with a continuous `reticle_size`; the `UC_SetMachineGunAccuracyFrame(int)` domain is not decoded, so the exact input cannot be named |

## 9. COMPROMISES

None. No value in this report replaces a file value; nothing was proposed as a substitute for a
missing capability (the closest JC3 systems are named, with their gaps, in §5).
