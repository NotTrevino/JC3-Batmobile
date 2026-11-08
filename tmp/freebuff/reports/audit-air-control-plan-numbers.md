# Audit — every number in `air-control-closest-system-plan.md`, recomputed

**Target:** `tmp/freebuff/reports/air-control-closest-system-plan.md` (the operator path
`reports/air-control-closest-system-plan.md` does not exist; the plan lives under `tmp/freebuff/`).
**Rule:** each number is recomputed from the file the plan cites, not from the plan.
**Verdicts:** MATCH = recomputed value equals the plan's within its stated precision; MISMATCH =
differs; PARTIAL = the number is right for some of its inputs or the citation does not say it.

**The plan was not edited.** Revert = delete this file.

---

## 1. Source values (inputs to everything else)

| # | plan value | plan location | source file:line | what the source actually says | verdict |
|---|---|---|---|---|---:|
| A1 | `AirControlYawTorqueFactorMax` **8000** (T-AC1) | §2.1 row 1, §0, title | `Research/BatmobileGrab/MODES.md:113`; `MECHANICS_NAMES.md:94` | \| `AirControlYawTorqueFactorMax` \| 0x4a8 \| `float` \| engine torque gain \| 8000 \| 8000 \| 8000 \| 8000 \| yes \| — 8000 in all four packages | **MATCH** |
| A2 | `JumpRampRightingTorque` / `JumpNoRampRightingTorque` **2000 / 2000** (T-SR1) | §2.1 row 3 | `MODES.md:159-160`; `MECHANICS_NAMES.md:39-40` | 0x1a64 = 2000, 0x1a68 = 2000, both serialised in all four packages | **MATCH** |
| A3 | offsets **0x4a8 / 0x4ac / 0x4b0 / 0x4b4 / 0x4b8 / 0x4bc** | §2.1 row 1, §6 U2 | `MODES.md:113-118`; `FOOTAGE.md:218-222` (F-56…F-60) | the six `AirControl*` fields sit at those offsets, declared, **not serialised** except 0x4a8 | **MATCH** |
| A4 | airborne mean **1.212 s** | §2.1 row 4, §4 card, §5 | `FOOTAGE.md:27`, `:93`, `:168` (F-6) | three samples 1.251 / 1.183 / 1.200 s | **MISMATCH** — see §2 below |
| A5 | samples **1.251 / 1.183 / 1.200** | §2.1 row 4 | `FOOTAGE.md:89-91` | row values 1.251 s, 1.183 s, 1.200 s | **MATCH** (1.200 is itself rounded from 1.199 — see §2) |
| A6 | spread (implicit) **1.183–1.251** | §4 card | `FOOTAGE.md:27`, `:93` | "spread 0.068 s" = 1.251 − 1.183 | **MATCH** |
| A7 | "37–38 unique frames … ~31 fps cadence" | §2.1 row 4 | `FOOTAGE.md:89-91` + `:84` | frames 37 / 38 / 38; "contact sheets at 15 fps, then snapped to the nearest decoded frame"; PTS diffs are 36 / 37 / 37 intervals | **PARTIAL** — 29–31 fps, not a uniform ~31 (§2.3) |
| A8 | 8000 lies inside `drift.max_drift_torque`'s shipped **0..35000** | §2.3 D1 note | `VOCABULARY.md` `CustomLandGlobal`: `drift.max_drift_torque` 0..35000 (n=145) | range confirmed | **MATCH** |

---

## 2. Where the airborne numbers do not close

### 2.1 The mean is 1.211, not 1.212

```
(1.251 + 1.183 + 1.200) / 3 = 3.634 / 3 = 1.211333…  → 1.211 s (3 d.p.)
plan and FOOTAGE.md:27/:93                        → 1.212 s
difference                                        → +0.000667 s  (+0.055 %)
```

**MISMATCH**, and it is upstream: `FOOTAGE.md:27` and `:93` both print 1.212. The plan quotes the
file faithfully, so this is one error propagated through three documents. It matters only because
every product of the mean (D3, D4, the card's window) inherits it.

### 2.2 The third sample is 1.199, printed as 1.200

```
clip 3: 6.205 − 5.006 = 1.199 s   →  FOOTAGE.md:91 prints 1.200 s
mean with the raw diffs: (1.251 + 1.183 + 1.199)/3 = 1.211 s
```
A 1 ms rounding, same direction as 2.1. **MISMATCH** (0.001 s) if the raw PTS are taken as the
measurement.

### 2.3 The frame counts and the "~31 fps"

```
clip 1: frames 97→133 = 36 intervals over 1.251 s = 28.78 fps
clip 2: frames 96→133 = 37 intervals over 1.183 s = 31.28 fps
clip 3: frames 149→186 = 37 intervals over 1.199 s = 30.86 fps
mean of the three                              = 30.31 fps
```
The printed "37 / 38 / 38" are **inclusive** counts (intervals + 1). "~31 fps" is right for clips
2 and 3 and wrong for clip 1 (28.8). **PARTIAL**; the plan should say **29–31 fps** and give the
number of intervals, not frames.

---

## 3. Derived numbers (D1–D10 and the two alternates)

| # | plan value | formula as written | source of the inputs | recomputed | verdict / difference |
|---|---|---|---|---|---:|
| D1 | **8000** into `drift.max_drift_torque` | max→max 1:1 | A1; RC2 `max_drift_torque` = 12000 (`Builds/bm-RC2/.../custom_land_global.vmodc`, dumped) | 8000 | **MATCH** (8000 ∈ 0..35000) |
| D2 | **0.667** | 8000 / 12000 | A1 + RC2 dump (12000.0) | 0.666667 | **MATCH** (0.667 at 3 d.p.) |
| D3 | **9696** (factor·s) | 8000 × 1.212 | A1 + A4 | 8000 × 1.211333 = **9690.67** | **MISMATCH** −5.33 (−0.055 %) |
| D4 | **14544** (factor·s) | 12000 × 1.212 | RC2 12000 + A4 | 12000 × 1.211333 = **14536.0** | **MISMATCH** −8.0 (−0.055 %) |
| D5 | **−33.3 %** | (9696 − 14544) / 14544 | D3, D4 | −0.33333 | **MATCH** (−33.33 %; invariant to the 1.212 error) |
| D6 | **4000** | 8000 / 2 (linear ramp mean) | A1 | 4000 | **MATCH** (the "/2" is a stated assumption, not a file value) |
| D7 | **0.2286** | 8000 / 35000 | A1 + A8 | 0.2285714 | **MATCH** (0.2286) |
| D8 | **1.538** | `unit_inertia_yaw` / `unit_inertia_pitch` = 4.0 / 2.6 | RC2 `rigid_body` dump: 4.0 and 2.5999999 | 1.5384615 | **MATCH** |
| D9 | **1.23–1.85** | 1.538 × 0.8 / × 1.2 | D8 | 1.2308 / 1.8462 | **MATCH** (upper 1.846 → 1.85) |
| D10 | **0.53–0.80** | 0.667 × 0.8 / × 1.2 | D2 | 0.5333 / 0.8004 | **MATCH** |
| alt | **6600.7** | 8000 / 1.212 | A1 + A4 | 8000 / 1.212 = 6600.66; with A4 corrected = 6604.30 | **MATCH on its own input, MISMATCH after §2.1** (+3.6) |
| alt | **9696 / 14544** "budget over the window" | D3 / D4 | — | 9690.7 / 14536.0 | inherits §3 |

**Joining of D3/D4 to the card.** The plan's §4 card uses "**1.212 s** airborne window" and the
blanket "0.53–0.80×" / "1.23–1.85×" bands. The bands are ratio-derived and survive the mean error;
only the stated window (1.212) and the two factor·s products move.

---

## 4. Car-side numbers the plan says it measured from `Builds/bm-RC2`

All re-read for this audit with `uv run python Tools/scripts/jc3adf.py dump` on
`Builds/bm-RC2/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/batmobile/`.

| # | plan claim | file | verified value | verdict |
|---|---|---|---|---:|
| B1 | `custom_land_global.vmodc` **3,399 B** | `…_custom_land_global.vmodc` | `stat` = **3399** | **MATCH** |
| B2 | **21-member** `Drift` block | same | `grep -c "drift\."` = **21** | **MATCH** |
| B3 | `drift.max_drift_torque` **12000**; `constant_drift_torque` **0** | same | 12000.0 / 0.0 | **MATCH** |
| B4 | `counter_steer_torque` **16000**; `_handbrake` **30000**; `_brake` **15000** | same | 16000 / 30000 / 15000 | **MATCH** |
| B5 | `drift_yaw_vel_damp` **0.02** / `overdrift` **0.03** / `exit` **0.5** | same | 0.02 / 0.03 / 0.5 | **MATCH** |
| B6 | `velocity_rotation` **80 / 15 / 40 / 0.2** | same | 80 / 15 / 40 / 0.2 | **MATCH** |
| B7 | `steering_sensitivity` **4.0**; `min_speed_to_drift_kmph` **10.0** | same | 4.0 / 10.0 | **MATCH** |
| B8 | `gravity_multiplier_in_air_up/down` **1.6 / 1.6**; `takeoff_pitch_damping` **0.5** | same | 1.6 / 1.6 / 0.5 | **MATCH** |
| B9 | `rigid_body`: mass **6000**, `unit_inertia_yaw` **4.0** / pitch **2.6** / roll **1.2**, `angular_damping` **0.0**, `max_angular_velocity` **−1**, `use_calculated_inertia` **1**, COM **(0.0, 0.6, 0.65)** | `…_rigid_body.vmodc` | 6000 / 4.0 / 2.6 / 1.2 / 0.0 / −1 / 1 / (0, 0.6, 0.65) | **MATCH** all eight |
| B10 | `land_aerodynamics` **5-member** type: `air_density` **1.29999995**, `frontal_area` **6.6346669**, `drag_coefficient` **0.55**, `top_speed_drag_coefficient` **2.0**, `lift_coefficient` **−0.3** | `…_land_aerodynamics.vmodc` | 1.29999995 / 6.6346669 / 0.55 / 2.0 / −0.3, five members | **MATCH** all five |

---

## 5. JC3-side numbers in the carrier ranking

| # | plan claim | source | verified | verdict |
|---|---|---|---|---:|
| C1 | `Aerodynamics.aerodynamic_surfaces[]` **77 rows**; `turn`/`pitch`/`roll_steering_factor` **0..0** | `VOCABULARY.md:12-25` | n=77 on every surface row; pitch 0..0, roll 0..0 (and turn 0..0 per `DRIVE_CARRIERS.md` §2/§4.1) | **MATCH** |
| C2 | `air_density` 0..1.3, `frontal_area` 0..350, `drag_coefficient` 0..4, `lift_coefficient` 0..8, `center_point` −20..36 | same | 0..1.3 / 0..350 / 0..4 / 0..8 / −20..36 | **MATCH** |
| C3 | "**no car ships the type**" | none cited directly | the type census per build is not in the lines the plan cites | **UNSOURCED** (see §6 G4) |
| C4 | `DriverLean.righting_torque` **1500..4000, n=23 = 18 bikes + 5 boats, 0 aircraft** | `VOCABULARY.md:566`; `Research/challenge/card-T-10.md:58` (A4) | range n=23 confirmed; A4: "18 bikes + 5 boats, 0 aircraft" | **MATCH** |
| C5 | `Fins.effective_in_air` **0 in 200/200** | `VOCABULARY.md:625` | 0..0 (med 0, n=200) | **MATCH** |
| C6 | `CForcePulse` **307 pulses, 31 members**, "**0 of 23** tune paths are collision", **14 unowned** | `FORCEPULSE.md` | 307 ✓ (`:4`), "31 distinct members" ✓ (`:18`), "14 without an owner" ✓ (`:10`), "holds **23** tunes" ✓ (`:59`); the exact phrase "0 of 23 tune paths are collision" is **not** in the file | **PARTIAL** — counts MATCH, the "0 of 23" is an inference from `:3` ("Trigger: explosion, and the owner says which explosion") |
| C7 | donor plane module `v4500_plane_solar_smallfloatprop_aerodynamics.vmodc` | "the carrier report's decoded source" | `tmp/freebuff/reports/carrier-air-control.md` exists; the module path itself is not quoted from a line | **UNSOURCED path** (§6 G3) |
| C8 | `±20 %` is "the project's ratio tolerance (`T10_DAMAGE.md` §0, ARM-2)" | `Working/Translation/T10_DAMAGE.md:20` | the ±20 % there is **heavy-weapon hits vs the BmAK ratio** in ARM-2, a damage-model band; the file has no general ratio tolerance and the line is not in a "§0" | **MISMATCH (citation scope)** |

---

## 6. Claims that cite no source

| # | claim (plan location) | why it is unsourced | fix |
|---|---|---|---|
| G1 | "the **B-09** pattern", "**B-05** proved the `.epe` graph can grow", "**B-07** a module can be registered", "**B-18** pattern", "R7 satisfied", "(R8)" | card ids and rule ids with no path or line; only `Research/specs/B-07.md` exists among those named explicitly | cite `Research/specs/B-0N.md` + the receipt path for each, or drop the id |
| G2 | "the ATV module's **0x48**" (§3 leg 1) | an offset attributed to a module that is not named | name the ATV module file and the member's decoded offset |
| G3 | "its full VFS path is resolved at build time by `jc3index`/`ENTITIES.md`" (§3 leg 2) | neither file is cited by section; `ENTITIES.md` is a class/entity census, not a VFS resolver | cite the `INDEX.jsonl` entry the path comes from |
| G4 | "no car ships the [`Aerodynamics`] type" (§1) | a fleet-wide census claim with no file | cite the per-build module-type census (or `FEATURE_CENSUS.md`) |
| G5 | "same-size PCM swap precedent (**test-060**)" (§4 audiotable) | a build id with no path | `Builds/test-060` receipt line |
| G6 | "read heading from the **minimap arrow** (the project's heading readout)" (§4) | a presentation claim with no source | cite the HUD/radar doc that names the arrow, or mark it a pilot convention |
| G7 | landing **roll ≤ 30°**, **pitch ±15°** (§4) | the plan *labels* them design tolerances ("not derived from a file") — correct labelling, but they are still unsourced numbers | keep the label, and say they are pilot thresholds to be calibrated on the first run (`CARD_FORMAT.md` rule 7) |
| G8 | "the **1.212 s** airborne window" as a measurement window | inherits A4 | fix after A4 |

---

## 7. Corrections the plan owner must apply

1. **Fix the mean at its source first.** `FOOTAGE.md:27` and `:93` print 1.212 s; the three samples
   give **1.211 s**. Either change both FOOTAGE lines to 1.211 (and the third sample at `:91` to
   1.199), or keep 1.212 and add "(mean 1.211, printed 1.212 in FOOTAGE)" where the plan quotes it.
   Correcting only the plan would leave the two documents disagreeing.
2. **D3 → 9691** (8000 × 1.211) and **D4 → 14536** (12000 × 1.211), with the products' unit
   "factor·s" unchanged. D5 stays **−33.3 %** (the ratio is invariant).
3. **The alternate reading → 6604.3**, not 6600.7 (8000 / 1.211).
4. **"~31 fps" → "29–31 fps"**, and quote **intervals** (36 / 37 / 37) rather than frame indices
   (37 / 38 / 38, which are inclusive counts).
5. **Re-cite the ±20 %.** It is ARM-2's heavy-weapon hit band (`T10_DAMAGE.md:20`), not a general
   "ratio tolerance". Say "±20 %, the ARM-2 damage band, used here as a declared band (not a
   decoded tolerance)" — or use a different, stated band.
6. **C6**: the "0 of 23 tune paths are collision" count is not in `FORCEPULSE.md`; cite `:3` and
   `:59` (trigger = explosion; 23 tunes) and drop the "0 of 23", or recount it and write the count
   with its line.
7. **Name the unsourced ids and paths** in G1–G6 above, or delete those clauses. The two that
   matter for the build are G3 (the plane module's path) and G2 (the 0x48 offset), because both are
   instructions a builder would follow.
8. Nothing else changes: all ten D-rows' *derivations* are arithmetically correct on their stated
   inputs, and every RC2/`VOCABULARY.md`/`MODES.md` value the plan quotes is exactly what those
   files say (B1–B10, C1–C2, C4–C5).

---

## 8. Commands run for this audit

```
grep -n "1.212\|1.251\|1.183\|1.200\|F-6\|airborne" Research/BatmobileGrab/FOOTAGE.md
sed -n '84,96p' Research/BatmobileGrab/FOOTAGE.md
grep -rn "AirControlYawTorqueFactorMax\|JumpRampRightingTorque\|JumpNoRampRightingTorque" \
     Research/BatmobileGrab/MECHANICS_NAMES.md Research/BatmobileGrab/MODES.md
sed -n '108,118p' Research/BatmobileGrab/MODES.md
uv run python Tools/scripts/jc3adf.py dump Builds/bm-RC2/.../batmobile/…_custom_land_global.vmodc
uv run python Tools/scripts/jc3adf.py dump Builds/bm-RC2/.../batmobile/…_rigid_body.vmodc
uv run python Tools/scripts/jc3adf.py dump Builds/bm-RC2/.../batmobile/…_land_aerodynamics.vmodc
grep -c "drift\." <the custom_land_global dump>          → 21
stat -c%s <the custom_land_global file>                  → 3399
grep -nE "member|unowned|owner" Research/JC3Grab/FORCEPULSE.md
sed -n '12,26p' Research/JC3Grab/VOCABULARY.md           (Aerodynamics surface rows)
grep -n "effective_in_air\|righting_torque" Research/JC3Grab/VOCABULARY.md  → :625, :566
grep -n "righting_torque\|A4" Research/challenge/card-T-10.md
sed -n '18,22p' Working/Translation/T10_DAMAGE.md
ls tmp/freebuff/reports/carrier-air-control.md Research/specs/B-07.md       → both exist
```

**Limits.** Static reads only; no game launched. The two claims this audit could not settle from
the cited lines are the per-build `Aerodynamics` census (G4) and the plane module's VFS path (G3);
both are named with the file that would settle them. The frame-rate reading depends on how the
capture's PTS map to frames — the arithmetic above uses the PTS diffs as printed in `FOOTAGE.md`
and says so.
