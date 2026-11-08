# Air control and ram assist — plans v2, every number rebuilt from its cited source

**Provenance / reversibility.** New file, `tmp/freebuff/reports/air-control-and-ram-assist-plans-v2.md`
= `E:/Modding/JC3-Batmobile/tmp/freebuff/reports/air-control-and-ram-assist-plans-v2.md`. Intended
change: rebuild the numbers of the two closest-system plans **row by row** after
`tmp/freebuff/reports/audit-air-control-plan-numbers.md` (five MISMATCH rows) and
`tmp/freebuff/reports/audit-ram-assist-plan-numbers.md` (the `KillFlipTorque` family). It is the
correct file because it is the requested output path and consumes both audits. **The originals stay
untouched** — `air-control-closest-system-plan.md`, `ram-assist-closest-system-plan.md`,
`carrier-air-control.md`, `carrier-ram-and-dodge.md`, `force-pulse-as-boost-and-shove-carrier-plan.md`
and `force-pulse-carrier-recount.md` are read only. **Revert = delete this file.**

Labels, used in every table below: **decoded** = a member/value/offset read from the named file:line;
**measurement** = read off footage, not a file; **derived** = arithmetic over decoded or measured
inputs; **derived band** = a stated tolerance around a derived ratio; **class default** = the CDO value
in `CLASS_DEFAULTS.md` (what the *base class* is authored with, which no playable archetype has to
ship); **archetype** = the value a shipped playable batmobile actually serialises in
`DAMAGE_RULES.md`; **declared** = a chosen value with no file behind it, stated as such;
**UNKNOWN** = searched and absent, with the file that would settle it.

**One rule this file applies to itself.** Where the old plan and the audit disagree, the source file
wins, and where the source is a measurement the *unrounded* sample is what gets multiplied — a pin
that rounds before multiplying is how 9696 was born.

---

## 0. What changed, in one table

| behaviour | rows rebuilt | rows changed | largest change | what it means for the build |
|---|---:|---:|---|---|
| air control (T-AC1 + T-SR1) | 26 | **8** | the airborne window: **1.212 → 1.211 s**, and its two products D3/D4 | the *carried value* (8000) and both steering bands (0.53–0.80×, 1.23–1.85×) do not move — only the window, the two factor·s products, the alternate 6604.3, the fps line and two citations |
| ram assist (T-DM7 + T-RA1) | 24 | **7** | `KillFlipTorque` **−2,000,000 → −200 shipped** (−2,000,000 is the class default) | the "impossible / 57× short / 2000× out of domain" verdict is **void**; the kill-flip is a value that fits a real torque member and fails only on duration and target selection. Separately, `ImpactMaxDamage` **is** authored (100.0), so the ram rate is no longer a reference case |

Two corrections below are **not in either audit** — they surfaced while rebuilding and are marked
`†` with their own line citations:

* `†1` `ImpactRoadAssistEnemyDuration` archetype is **0.333 s**, not the 1.5 s the ram plan's Q-RA-1
  band quotes (`Research/BatmobileGrab/DAMAGE_RULES.md:587`).
* `†2` `ImpactMaxDamage` is **100.0** in the class default (`Research/BatmobileGrab/CLASS_DEFAULTS.md:255`),
  so the ram plan's "the missing absolute" row is wrong for the CDO; it is missing only from the
  archetypes (`DAMAGE_RULES.md:149`).

---

## 1. Air control — row by row

### 1.1 Source values

| # | plan location | old value | corrected value | label | file:line (evidence) | verdict |
|---|---|---|---|---:|---|---|
| A1 | §2.1 row 1, §0, title | `AirControlYawTorqueFactorMax` **8000** | **8000** | decoded | `Research/BatmobileGrab/MODES.md:113` (0x4a8, all four packages, serialised); `MECHANICS_NAMES.md:94` | MATCH — unchanged |
| A2 | §2.1 row 3 | `JumpRampRightingTorque` / `JumpNoRampRightingTorque` **2000 / 2000** | **2000 / 2000** | decoded | `MODES.md:159-160` (0x1a64 / 0x1a68) | MATCH — unchanged |
| A3 | §2.1 row 1, §6 U2 | offsets 0x4a8 / 4ac / 4b0 / 4b4 / 4b8 / 4bc | same | decoded | `MODES.md:113-118`; `FOOTAGE.md:218-222` | MATCH — unchanged |
| **A4** | §2.1 row 4 (:48), §4 card (:184-191), §5 (:170), §6 U2 (:248), §7 (:264) | mean **1.212 s** | **1.211 s** | measurement | samples `FOOTAGE.md:89-91` → (1.251 + 1.183 + 1.199) / 3 = **1.211333 s**; the literals 1.212 sit at `FOOTAGE.md:27` and `:93` | **MISMATCH** (+0.000667 s, +0.055 %) — **upstream**, see §1.3 |
| **A5** | §2.1 row 4 | samples 1.251 / 1.183 / **1.200** | 1.251 / 1.183 / **1.199** | measurement | `FOOTAGE.md:91` prints 1.200; the row's own PTS are 149 / 5.006 s → 186 / 6.205 s = **1.199 s** | **MISMATCH** (−0.001 s) |
| A6 | §4 card | spread 1.183–1.251 | same (0.068 s) | measurement | `FOOTAGE.md:27`, `:93` | MATCH |
| **A7** | §2.1 row 4 (:48) | "**37–38 frames at ~31 fps**" | "**36 / 37 / 37 intervals, 28.8 / 31.3 / 30.9 fps, 29–31 fps**" | measurement | `FOOTAGE.md:89-91`: frame indices 97→133, 96→133, 149→186 are **inclusive counts**; intervals are one fewer, and 36/1.251 = 28.78 fps | **PARTIAL** — "~31" is wrong for clip 1 |
| A8 | §2.3 D1 note | 8000 ∈ `drift.max_drift_torque` shipped 0..35000 | same | decoded | `Research/JC3Grab/VOCABULARY.md` (`drift.max_drift_torque`, n=145) | MATCH |

### 1.2 Derived numbers

| # | plan :line | old value | corrected value | label | derivation on the corrected input | verdict |
|---|---:|---:|---:|---|---|---|
| D1 | :79 | 8000 | **8000** | decoded, 1:1 | A1 max→max | MATCH |
| D2 | :80 | 0.667 | **0.667** | derived | 8000 / 12000 | MATCH |
| **D3** | :81 | 9696 | **9691** (9690.67) | derived | 8000 × 1.211333 = **9690.7**; × 1.211 (rounded window) = 9688 | **MISMATCH** **−5.33** (−0.055 %) |
| **D4** | :82 | 14544 | **14536** | derived | 12000 × 1.211333 = **14536.0** | **MISMATCH** **−8.0** (−0.055 %) |
| D5 | :83 | −33.3 % | **−33.3 %** | derived | (9690.7 − 14536.0) / 14536.0 = −0.3333 | MATCH — the ratio is invariant to the window error |
| D6 | :85 | 4000 | **4000** | declared alternate | 8000 / 2, a stated linear-ramp assumption (not a file value) | MATCH |
| D7 | :86 | 0.2286 | **0.2286** | derived normaliser | 8000 / 35000 = 0.228571 | MATCH |
| D8 | :87 | 1.538 | **1.538** | derived | 4.0 / 2.5999999 | MATCH |
| D9 | :88 | 1.23–1.85 | **1.23–1.85** | derived band | 1.5384 × 0.8 / × 1.2 | MATCH |
| D10 | :89 | 0.53–0.80 | **0.53–0.80** | derived band | 0.6667 × 0.8 / × 1.2 | MATCH |
| **alt** | :93, :213 | 6600.7 | **6604.3** | derived | 8000 / 1.211333 = **6604.3**; / 1.212 = 6600.66 | **MISMATCH** (+3.6) |

**Which D3 to ship.** Three values are now in play: **9696** (old, 8000 × the printed 1.212),
**9691** (8000 × the unrounded 1.211333 — the value the samples give) and **9688** (8000 × the
*rounded* 1.211). The audit's own correction, "D3 → 9691 (8000 × 1.211)", mixes the two: 8000 × 1.211
is 9688. Carry **9691 / 14536**, and compute both from the unrounded samples — rounding the window
first and multiplying second is exactly the error being repaired. This is arithmetic, not a pin:
nothing downstream consumes D3/D4 except the narrative budget in §2.3, so no build value changes.

### 1.3 The stale literal, and why the plan cannot fix it alone

The wrong number lives in the measurement file, not the plan: `Research/BatmobileGrab/FOOTAGE.md:27`
("air time … **1.212 s** mean") and `:93` ("Mean **1.212 s**"). The plan quotes the file faithfully,
so one upstream literal propagated into three documents. The two fixes are (a) correct both FOOTAGE
lines to 1.211 and the third sample at `:91` to 1.199, or (b) keep them and have every consumer print
"mean 1.211 (FOOTAGE prints 1.212)". **This file takes route (b)** because the originals stay
untouched; whoever owns `FOOTAGE.md` should apply (a), after which D3 = 9691, D4 = 14536, alt = 6604.3
and the window sentence become single-sourced.

### 1.4 Car-side numbers (all re-verified, none changed)

| # | rows | value | label | file:line | verdict |
|---|---|---|---|---|---|
| B1 | `custom_land_global.vmodc` size | 3,399 B | decoded | the car's private module, `Builds/bm-RC2/…/batmobile/` | MATCH |
| B2 | `Drift` block | 21 members | decoded | same (`grep -c "drift\."`) | MATCH |
| B3 | `max_drift_torque` / `constant_drift_torque` | 12000 / 0 | decoded | same | MATCH |
| B4 | `counter_steer_torque` / `_handbrake` / `_brake` | 16000 / 30000 / 15000 | decoded | same | MATCH |
| B5 | `drift_yaw_vel_damp` / `overdrift` / `exit` | 0.02 / 0.03 / 0.5 | decoded | same | MATCH |
| B6 | `velocity_rotation_amount` / start / end / exp | 80 / 15 / 40 / 0.2 | decoded | same | MATCH |
| B7 | `steering_sensitivity` / `min_speed_to_drift_kmph` | 4.0 / 10.0 | decoded | same | MATCH |
| B8 | `gravity_multiplier_in_air_up/down` / `takeoff_pitch_damping` | 1.6 / 1.6 / 0.5 | decoded | same | MATCH |
| B9 | `rigid_body`: mass, inertia yaw/pitch/roll, damping, max ω, `use_calculated_inertia`, COM | 6000, 4.0/2.6/1.2, 0.0, −1, 1, (0.0, 0.6, 0.65) | decoded | `…_rigid_body.vmodc` | MATCH (all eight) |
| B10 | `land_aerodynamics` 5 members | 1.29999995 / 6.6346669 / 0.55 / 2.0 / −0.3 | decoded | `…_land_aerodynamics.vmodc` | MATCH (all five) |

### 1.5 JC3-side and citation rows

| # | plan :line | old claim | corrected claim | label | file:line | verdict |
|---|---|---|---|---|---|---|
| C1 | §1 | `AerodynamicSurface` 77 rows; turn/pitch/roll **0..0** | same | decoded | `VOCABULARY.md:12-25`; `DRIVE_CARRIERS.md` §2/§4.1 | MATCH |
| C2 | §1 | `air_density` 0..1.3, `frontal_area` 0..350, `drag_coefficient` 0..4, `lift_coefficient` 0..8, `center_point` −20..36 | same | decoded | same | MATCH |
| C4 | §1 | `DriverLean.righting_torque` 1500..4000, n=23 = 18 bikes + 5 boats, 0 aircraft | same | decoded | `VOCABULARY.md:566`; `Research/challenge/card-T-10.md:58` | MATCH |
| C5 | §1 | `Fins.effective_in_air` 0 in 200/200 | same | decoded | `VOCABULARY.md:625` | MATCH |
| **C6** | §1 (:26), §3 (:152) | "307 pulses, 31 members, **0 of 23 tune paths are collision**, 14 unowned" | "**307 pulses / 79 chassis / 31 members (5 named + 26 hashed) / 14 unowned**; trigger **explosion** (`FORCEPULSE.md:3`), **23 tunes** (`:59`)" — drop "0 of 23" | decoded | `FORCEPULSE.md:3, :10, :59`; `force-pulse-carrier-recount.md` §0 (recounted from `FORCEPULSE.json`) | **PARTIAL** — counts MATCH, the "0 of 23" phrase is nowhere in `FORCEPULSE.md` |
| **C7** | §3 leg 2 | donor plane module `v4500_plane_solar_smallfloatprop_aerodynamics.vmodc` | **UNKNOWN path in this workspace** — `Builds/bm-RC2/aaf/editor/entities/jc_vehicles/` contains only `00_shared` and `01_land` | UNKNOWN | would be settled by the asset cache the carrier read (outside the workspace: `E:/Modding/_gamedata`, not read) | **UNSOURCED path** — leg 2 cannot be built from this tree as written |
| **C8** | §4 (:189) | "±20 % — the project's ratio tolerance (`T10_DAMAGE.md` §0, ARM-2)" | "±20 % — **ARM-2's heavy-weapon hit band**, used here as a **declared** band, not a decoded tolerance" | declared band | `Working/Translation/T10_DAMAGE.md:20` (there is no "§0" and no general ratio tolerance) | **MISMATCH** (citation scope) |
| **G2** | §3 leg 1 (:120) | "the ATV module's **0x48**" | `CustomLandGlobal.drift.max_drift_torque` **float 0x48** on **`v0012_car_autostraad_atv_custom_land_global.vmodc`** | decoded | `carrier-air-control.md` §2.1 / §3 | **UNSOURCED → partly fixed**: the module is now named; the file itself is not in `bm-RC2`, so the offset must still be resolved **by member name** at build time, never copied |
| G1/G3/G5/G6/G7 | §3, §4 | B-05/B-07/B-09/B-18 ids, `jc3index`/`ENTITIES.md` resolver, test-060, minimap arrow, landing 30°/15° | keep the two tolerances **labelled** as pilot thresholds; `Research/specs/B-0N.md` exist for B-04…B-16 and B-22…B-25, so cite `Research/specs/B-0N.md` **and** the receipt, and drop "B-18" (no such spec) | declared | `Research/specs/` listing | PARTIAL — cosmetic for the build except "B-18" |

---

## 2. Air control — the closest JC3 system, restated

**The mechanism BmAK uses** is a per-frame angular impulse on the car body while it has no ground
contact, gated on airborne state, with a yaw factor (`AirControlYawTorqueFactorMax` 8000) and an
unserialised pitch pair (`MODES.md:113-118`).

**Closest JC3 system — three members, each one leg short** (`carrier-air-control.md` §3-§9):

| rank | member path | type / offset | fleet | holds | lacks |
|---|---|---|---|---|---|
| 1 | `CustomLandGlobal.drift.max_drift_torque` (with `…constant_drift_torque` 0x44, `…counter_steer_torque` 0x4C) | float **0x48**, n=145; same block on the car | 0..35000 (median 12000) — **8000 is in-domain** | the yaw torque, on the car already | **any airborne gate**; no pitch member; 0.2286-style normaliser not needed |
| 2 | `AerodynamicSurface.turn_steering_factor` / `pitch_steering_factor` / `roll_steering_factor` | float **0x38 / 0x3C / 0x40**; also `air_density` 0x44, `lift_coefficient` 0x58, `center_point` IA 0x20; type 96 B | **n=77 rows, all three factors 0..0**; no car ships the type | the only member whose *name* is air-steering authority, yaw **and** pitch | a car-bound instance, and the donor module is **not in this workspace** (C7) |
| 3 | `Fins.fins` `IA[Fin]` 0xB0 / `number_of_fins` 0x218 → `Fin.effective_in_air` | uint8, **0 in 200/200** | the only airborne-only switch in the fleet | the airborne gate | any value, any car, any mapping from steering input |
| — | `DriverLean.righting_torque` 1500..4000 (n=23 = 18 bikes + 5 boats) | offset UNKNOWN (inner-`.ee`) | 2000 is in-domain | T-**SR1** self-righting, not T-AC1 steering | a car that ships it |
| — | **`CForcePulse`** | 307 pulses / 31 members; 292/307 at the entity origin | rejected | — | **cannot push its own carrier**: a radial blast about a body's own centre gives a zero-length vector (`force-pulse-as-boost-and-shove-carrier-plan.md` §3.1); trigger is an explosion (`FORCEPULSE.md:3`); no duration member |

`force-pulse-carrier-recount.md` confirms the pulse census used above is exact (307 / 79 / 31 = 5
named + 26 hashed, from `FORCEPULSE.json`, not from prose), so the rejection is not resting on a
miscounted population.

**Remaining gap (unchanged by this rebuild):** a JC3 member that applies **yaw and pitch torque as a
function of steering input with no ground contact**, plus a start/stop window. `drift.*` has the
torque and no gate; `AerodynamicSurface.*` has the air and the input, no car and 0 values;
`Fins.*` has the gate and nothing else. That is capability card **T-AC1b** (`carrier-air-control.md`
§9), not a tuning row.

**One build step, sized for a single session** — *yaw only, leg 1*:

| field | value |
|---|---|
| tree | `Builds/bm-RC5-air/`, copied from `Builds/bm-RC2` (offline, new tree; nothing in `bm-004c` or `bm-RC4` is touched) |
| file it writes | `…/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/batmobile/v0300_car_kensington_sportsmuscle_custom_land_global.vmodc` (3,399 B, the car's private copy) |
| member it writes | **`drift.max_drift_torque`, 12000 → 8000** — one float at its decoded offset, resolved **by member name**, file size unchanged; `.toc` re-pointed with `eetoc.py patch` |
| nothing else | `constant_drift_torque` stays 0; `min_speed_to_drift_kmph` stays 10; `steering_sensitivity` stays 4.0 — one variable so the session's result is readable |
| session proof | `jc3adf.py dump` shows 8000.0; `eetoc.py verify` passes; new `receipt.json` + `install.ps1`; tamper flip 8000→8001 caught |
| why it fits one session | one value, one repack, one receipt — the aero leg (leg 2) is a **separate** session because its donor module is not even in this workspace (C7) |

`T-SR1` stays out of this step: its 2000/2000 are in `DriverLean`'s 1500..4000, so it is a carrier
question (no car ships the type), not a value question.

---

## 3. Ram assist — row by row

### 3.1 The kill-flip family (the audit's C1/C4, and what it voids)

| # | plan :line | old value | corrected value | label | file:line | verdict |
|---|---|---|---|---:|---|---|
| K1 | §0 (:47-48), §1 (:72), §5.4 (:301) | `KillFlipTorque` **−2,000,000** | **class default −2,000,000**; **shipped archetype −200** (V2 / MK2 / Funhouse), **−400** (Joker) | class default vs archetype | `CLASS_DEFAULTS.md:270` (0x0588, off 7192, `-2000000.0`); `DAMAGE_RULES.md:594`, `:647`, `:674` (−200), `:618` (−400) | **MISMATCH** as *the* value — the plan quoted the CDO and then reasoned about it as if it shipped |
| K2 | §1 (:72), §5.4 (:303) | `KillFlipTorqueDuration` **1.5 s** | **class default 1.5 s**; **shipped 0.5 s** (V2 / MK2 / Funhouse), **0.75 s** (Joker) | class default vs archetype | `CLASS_DEFAULTS.md:271` (0x0590, off 7196); `DAMAGE_RULES.md:595`, `:648`, `:675`, `:619` | **MISMATCH** as shipped |
| K3 | §0 (:47-48), §5.4 (:301) | "cannot go into any torque member — the drift torque ceiling is 35000, **57× short**" | **the shipped −200 fits**: 200 is **175× inside** the 0..35000 ceiling; **57.1× is the CDO's** ratio, not a shipped one | derived | `VOCABULARY.md:479` (`max_drift_torque` 0..35000, n=145); arithmetic 2 000 000 / 35 000 = 57.14, 35 000 / 200 = 175 | **MISMATCH** — the "impossible" verdict is void for −200 |
| K4 | §5.4 (:302, :308, :324), §6 (:341) | pulse impulse "**2000× the fleet max (1000)** — out of domain" | on **−200** the pulse value is **0.2× the fleet *minimum* (25)** — *below* the decoded floor, opposite sign of out-of-domain; on the CDO it is 2000× the max | derived | `FORCEPULSE.md:31` (hashed impulse 25..1000); 2 000 000 / 1000 = 2000; 200 / 25 = 8 | **MISMATCH** on the shipped value; **the pulse verdict still stands, for shape** — no angular member, no duration, no target selection (`force-pulse-as-boost-and-shove-carrier-plan.md` §3.3) |
| K5 | §5.4 (:305-306), Q-KF-1 (:311) | "−2,000,000 over 1.5 s, pulse beside a moving car → roll > 90° within 1.5 s" | target is **−200 for 0.5 s** on the shipped car; the pulse cannot deliver either (K4), so the leg becomes a **native torque-over-time** card, not a pulse build | archetype + derived | K1, K2, `force-pulse-as-boost-and-shove-carrier-plan.md` §3.3/§5 | **MISMATCH** — stage 4 (`bm-RC4-pulse2`) should not be built as written |

**What survives.** `KillFlipTorque` is still the row's hardest number, but for two reasons that have
nothing to do with magnitude: (a) **duration** — BmAK applies the torque for 0.5 s and JC3's nearest
member (`drift.*`) is a continuous state torque with no timer; (b) **target selection** — it applies
to the car the Batmobile hits, and no JC3 impulse/torque member selects a target
(`carrier-ram-and-dodge.md` §8-§9). The correct carrier is therefore `drift.max_drift_torque`
(0x48) holding **−200**, with the duration supplied by native code (`FlipVehicle` is
`AddTorqueOverTime` + `AddKeepyUpForce` in BmAK itself — `force-pulse-as-boost-and-shove-carrier-plan.md`
§2.3/§5).

### 3.2 Values the audits confirmed (unchanged, listed so the rebuild is complete)

| # | row | value | label | file:line |
|---|---|---|---:|---|
| 1 | `rotor_collision.damage_to_other_per_second`, donor included | **100000/s**, n=232 module sets | decoded | `VOCABULARY.md:1415` |
| 2 | population: 232 vehicles vs 233 roots | **232** (one train entity carries two roots) | decoded | `DAMAGE_MECHANISMS.md:28` |
| 3 | siblings `min_rpm` / `light_object_mass_ratio` / `mass_ratio_when_no_mass` | 30 / 0.02 / 0.1 | decoded | `VOCABULARY.md:1416-1418` |
| 4 | band floor / ceiling as archetype | **20 / 150** | archetype | `DAMAGE_RULES.md:151-152`; `:584-585`, `:637-638`, `:664-665` |
| 5 | class defaults for the same pair | **60 / 200** | class default | `CLASS_DEFAULTS.md:256-257` |
| 6 | `ImpactStrafeMod` archetype / class | **2.25 / 1.5** | archetype, class default | `DAMAGE_RULES.md:153`, `:593`, `:646`, `:673`; `CLASS_DEFAULTS.md:258` |
| 7 | `ImpactBoostMod` archetype / class | **2.0 / 1.5** | archetype, class default | `DAMAGE_RULES.md:147`, `:583`, `:636`, `:663`; `CLASS_DEFAULTS.md:260`; the old `BOOST_COVERAGE.md:120` citation **does not exist** — replaced |
| 8 | drift torque ceiling | **35000** | decoded | `VOCABULARY.md:479` |
| 9 | pulse impulse slot fleet range | **25..1000** | decoded | `FORCEPULSE.md:31` |
| 10 | rotor block offsets | `min_rpm` **0x130**, `mass_ratio_when_no_mass` 0x134, `damage_to_other_per_second` **0x138**, `light_object_mass_ratio` 0x13C | decoded | in-plan re-read (`ram` §8): 30.0 / 0.1 / 100000.0 / 0.02 |
| 11 | road assist already carried | `counter_steer_torque_brake` **15000** = class default; `counter_steer_torque_handbrake` **30000** = archetype; `max_drift_angle_deg` **45** | decoded, exact | `CLASS_DEFAULTS.md:229`; `DAMAGE_RULES.md:589`, `:613`, `:642`, `:669` |
| **12 †1** | `ImpactRoadAssistSceneryDuration` / `EnemyDuration` | plan: **0.75 / 1.5 s**; **corrected: class default 0.75 / 1.5 s, archetype 0 / 0.333 s** (Joker 0.33 / 0.75) | class default + archetype | `CLASS_DEFAULTS.md:227-228`; `DAMAGE_RULES.md:587`, `:590` (Funhouse), `:640`, `:643` (MK2), `:667`, `:670` (V2), `:611`, `:614` (Joker) |
| **13 †2** | `ImpactMaxDamage` / `ImpactMinDamage` / `ImpactMaxDamagePow` — plan: "**no value** … the missing absolute" | **`ImpactMaxDamage` 100.0** (CDO, off 6856), `ImpactMaxDamagePow` **0.666**; the **archetypes** do not serialise any of the three | class default vs archetype | `CLASS_DEFAULTS.md:255`, `:261`; `DAMAGE_RULES.md:149-150` ("—") |

`†1` moves **Q-RA-1's band**: the plan's "heading returns … in **≤ 1.5 s** (the `EnemyDuration`
value)" is the CDO; the shipped assist lasts **0.333 s**. A card that allows 1.5 s cannot fail a
system that only ever acts for a third of a second.

`†2` changes a **label, not a number**: the ram plan set its rate from a *reference case* ("target
health 100") because it believed no absolute existed; BmAK authors **`ImpactMaxDamage` = 100.0**, so
the 2000/s rate is now aligned with a decoded authoring value (100 / 0.05 s = 2000) instead of a
coincidence. The rate itself does not move.

### 3.3 The rate, restated on the corrected labels

```
ImpactMaxDamage (CDO, decoded, CLASS_DEFAULTS.md:255)   = 100.0
contact time at 80 km/h (derived, 1.1 m / 22.222 m/s)   = 0.0495 s ≈ 0.05 s
rate = 100 / 0.05                                        = 2000 / s
predicted loss = 2000 × (1.1 / (v / 3.6))  →  20 km/h 396 (capped 100) · 80 km/h 100 · 150 km/h 52.8
```

The channel is **speed-inverse** (constant rate × shorter contact), which is the honest core of
T-DM7 and is unchanged by the label fix; the 20 km/h floor rides on `min_rpm` 1260 (engine rpm at
20 km/h in 1st: 77.7133 × 5.1401253 × 3.15 = **1257.8**), and there is still **no** 150 km/h
ceiling because the block has no max-rpm member.

---

## 4. Ram assist — the closest JC3 system, restated

**The mechanism BmAK uses:** a per-impact curve (band 20→150 km/h, strafe ×2.25, boost ×2.0, absolute
100), evaluated on the *outgoing* side; plus a triggered assist/dodge/shove/flip family with
durations and target selection (`DAMAGE_RULES.md` §3.3; `carrier-ram-and-dodge.md` §1).

**Closest JC3 system** (`carrier-ram-and-dodge.md` §2, §8-§9):

| behaviour | closest member path | carrier file / offset | fleet | what it gives | what is missing |
|---|---|---|---|---|---|
| ram damage (T-DM7) | `VehicleCommon.rotor_collision.damage_to_other_per_second` | `00_shared/modules/vehicle_common.vmodc`, 12,271 B; instance 0x50, size 5,012; float **0x138** (`min_rpm` 0x130, `mass_ratio_when_no_mass` 0x134, `light_object_mass_ratio` 0x13C) | **100000/s on 232 module sets**, donor car included | an outgoing rate + two mass ratios + one RPM gate, already in every vehicle's module set | **the speed band, the ×2.25 / ×2.0 modifiers, and a max-speed gate** — none exists; and whether the consumer runs on a `CCar` with no rotor is UNKNOWN |
| road assist (T-RA1) | `CustomLandGlobal.drift.counter_steer_torque` (0x4C), `…_brake` 15000, `…_handbrake` 30000, `max_drift_angle_deg` 45 | the car's private `custom_land_global.vmodc` | n=145 | the torque, angle and magnitudes **already exact** | the **trigger** (post-impact vs in-drift) and the **duration** (0.333 s archetype) |
| dodge | `CustomLandGlobal.arcade.nitro_boost.push_force` (15000) / `boost_blend_time` (0.2); `arcade.turbo_jump.*` floats **0xC4-0xD8** | same module | 12..15 / 50 / 200 km/h / ×2 | a force and a time, both continuous | a **lateral, event-triggered** impulse; the force unit is UNKNOWN (6000 N on 6 t = 1 m/s²) |
| shove / kill-flip | `CForcePulse` hashed impulse `id:24872388` | 307 pulses / 31 members (5 named + 26 hashed); owner pointer `id:B5AE7986`; 292/307 at origin; 14 unowned | 25..1000 | radius, flat falloff, 0-damage tunes | **no angular member, no duration, no target selection**; a body at the pulse transform receives a zero-length vector (`force-pulse…plan.md` §3.1, §3.3). Confirmed population: `force-pulse-carrier-recount.md` §0 |

**Remaining gap (restated on the corrected numbers):** JC3 has the ram **rate** but not the ram
**curve**; it has road-assist **values** but not the road-assist **event**; it has a **torque** that
can hold −200 but no **timer** and no **target**; and its only impulse primitive is radial, one-frame
and untargeted. That is two capability cards (T-DM7-curve, T-RA1-triggered-impulse), not one tuning
pass — and the −200 finding removes the "out-of-domain magnitude" excuse for not carrying
`KillFlipTorque` in `drift.max_drift_torque`.

**One build step, sized for a single session** — *T-DM7 stage A, the channel probe*:

| field | value |
|---|---|
| tree | `Builds/bm-RC5-ramA/`, offline, new tree (a failed probe is deleted, never retuned in place) |
| file it writes | **private copy** of `00_shared/modules/vehicle_common.vmodc` → the Batmobile's own `modules/default/batmobile/batmobile_vehicle_common.vmodc`; the shared original is never edited |
| members it writes | `rotor_collision.damage_to_other_per_second` **@0x138: 100000 → 2000**; `rotor_collision.min_rpm` **@0x130: 30 → 0** (removes the rotor gate so the consumer is tested unconditionally) |
| entity side | repoint the `.epe` module entry from the shared path to the private path (build-time path hash) and add the file to `@files.xml` |
| kept | `light_object_mass_ratio` 0.02, `mass_ratio_when_no_mass` 0.1, `vehicledamage.impact_damage_factor` 0 |
| session proof | `jc3adf.py dump` reads 2000.0 / 0.0; `eetoc.py verify`; `bm_entity.py --check` sees one module entry; new receipt + `install.ps1`; tamper flip 2000→2001 caught |
| why it fits one session | two floats, one private copy, one repoint — stage B (`min_rpm` 1260) is a second session against the same base |

---

## 5. Pilot cards (one sentence per behaviour, measured number + band)

**Air control — T-AC1 (yaw leg, `drift.max_drift_torque` 8000).**

> **Q-AC-1** — From the F-6 ramp at the same entry speed, hold full left steer from the frame the
> wheels leave the ground: over the **1.211 s** airborne window (1.183–1.251 s, three jumps) the
> heading must change by **0.53–0.80×** the heading change the same input produces in a 1.211 s ground
> drift at the same speed, and the car must touch down with **roll ≤ 30°** and pitch within **±15°**
> of take-off.

| element | value | source |
|---|---:|---|
| window | **1.211 s** (1.251 / 1.183 / 1.199) | measurement, `FOOTAGE.md:89-91`; `FOOTAGE.md:27`/`:93` print 1.212 — corrected |
| yaw band | **0.53–0.80×** ground drift | derived band, 8000/12000 = 0.667 ± 20 % (declared, ARM-2 band) |
| landing tolerances | roll ≤ 30°, pitch ±15° | **declared** pilot thresholds, calibrated on the first run |
| pass | 3 of 3 jumps inside the band, no single jump outside | — |

**Ram assist — T-DM7 (stage A, `rotor_collision.damage_to_other_per_second` 2000/s, gate off).**

> **Q-RAM-1A** — Ram a parked NPC car head-on at **80 km/h**: the contact must remove **40–100 %** of
> the victim's health bar; at **150 km/h** **40–65 %**; at **20 km/h** **100 %** (the inverted ramp is
> expected — the gate is off in stage A); the Batmobile's own bar must not move at any of the three
> speeds.

| element | value | source |
|---|---:|---|
| rate | **2000 / s** | derived: `ImpactMaxDamage` 100.0 (`CLASS_DEFAULTS.md:255`) / 0.05 s contact at 80 km/h |
| model | 2000 × (1.1 m / v) → 396 / 100 / 52.8 | derived |
| band | **±20 %** on each row, on the victim's 100-point bar | declared (ARM-2 band) |
| pass | the three rows in band **and** zero self-damage | — |

---

## 6. Limits and what this file did not do

* **No original was edited.** The two plans, the two carrier reports, the force-pulse plan and its
  recount, `FOOTAGE.md`, `DAMAGE_RULES.md`, `CLASS_DEFAULTS.md` and `VOCABULARY.md` are read only.
  Revert = delete this file.
* **`FOOTAGE.md:27`/`:93` still print 1.212 s.** This file carries 1.211 everywhere and marks the
  stale literal; correcting the measurement file is its owner's edit, not this one's.
* **The audit's "D3 → 9691 (8000 × 1.211)" is internally off by 3** — 8000 × 1.211 = 9688. Carry
  9691 (unrounded 1.211333) or 9688 (rounded), never 9696.
* **`v4500_plane_solar_smallfloatprop_aerodynamics.vmodc` and `v0012_car_autostraad_atv_custom_land_global.vmodc`
  are not in this workspace** (`Builds/bm-RC2/.../jc_vehicles/` holds `00_shared` and `01_land` only).
  The aero leg's donor path is therefore UNKNOWN here, and the drift offset must be resolved by member
  name — both stated in §1.5 and §2. The asset cache lives outside the project (`E:/Modding/_gamedata`)
  and was not read.
* **Still UNKNOWN, unchanged:** whether `drift.*` torque applies airborne (U1, needs Q-AC-1); whether
  the `rotor_collision` consumer runs on a car and what `min_rpm` compares against (U1/U2, needs
  Q-RAM-1A/1B); the engine-unit bridge for every BmAK torque (no file names a JC3 unit); the names of
  the 26 hashed pulse members (no shipped table).
* **Nothing was built, launched or measured in-game.** Static reads and arithmetic only; the two
  build steps are compositions, not applied work.
