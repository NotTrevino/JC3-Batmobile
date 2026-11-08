# Challenge — `Working/Translation/T1_TRANSLATION.md`

Read-only challenge of every claim in the T-1 translation table that is assumed, inferred, carried
by a member name rather than a behaviour, or numerically unsourced. No existing document was
edited; the only new files are `Tools/scripts/chase/challenge_t1.py` and
`E:/Modding/_JC3grab/challenge/challenge_t1.json`.

Rules applied: `GRAB_BACKLOG.md` §0.5 — R4 (no value without provenance; `assumed` is not
buildable) and R5 (behaviour before member). `POSTMORTEM_DAMAGE.md` is the reference for why
name-matching fails.

**Verdict summary: 39 claims examined — 17 CONFIRMED, 14 REFUTED, 3 CONFIRMED-AS-EVIDENCED-BUT-
MIS-CITED, 2 UNVERIFIABLE, 3 PARTIAL.**

The three findings that matter most:

1. **The "class median" rows are wrong in the direction that changes decisions.** Arcade friction
   is not 3.0 in every class (it is 3.0 / 2.8 / 2.2 / 2.0), and `max_brake_torque` is not 5,000 at
   3–6 t (it is 9,000, with 5,000 the class *minimum*). T-R1's target stays defensible as a p75
   choice; T-K1's proposed 5,000 would put the car at the bottom of its class, not the middle.
2. **The `now` column and §14 describe a build that is no longer current.** `current.json` points
   at **test-091**, not test-083, and test-091 already ships the "proposed" values (mass 6,000,
   friction 3.0, strength 45, brake 5,000, boost grip 1.0, 55°/20° steering). §17's "the next
   build carries them" and §14's "where the build contradicts the fleet" are both stale.
3. **Seven BmAK values are real but cited to an artifact that does not contain them.**
   `CHAIN.json` has no `FakeExtraSpeedMax`, `BoostDuration`, `HandBrakeOffTime`, `MassScale`,
   `BatmobileMassRatio`, `DriftCorrectionSteerSpeed` or `SteeringSpeedReCentreMod`: its `fields`
   cover only 20 classes and not `RVehicleBatmobileBase` / `RVehicleSimCar`. The values resolve
   correctly through the live lookup (`bmak_chain.py <Class>.<prop>`) and, for three of them,
   through `SPEEDOMETER.json`. The values are right; the citation is not, which is the one thing
   R4 exists to prevent.

Reproduce everything below with:

```
python Tools/scripts/chase/challenge_t1.py        # 61 checks -> E:/Modding/_JC3grab/challenge/challenge_t1.json
```

---

## A. Header and provenance claims

### C01 — "carried by test-085; the 35 numeric values over 16 rows … 35/35 equal"
*Class:* inferred. *Location:* `T1_TRANSLATION.md:3-6`.
**Verdict: UNVERIFIABLE.**
No artifact in the repo records that read-back as a machine result: `Working/Translation/current.json`
is a dump of the *current* build, and nothing in `T_ROWS.jsonl`/`T5_BUILD.md` carries a "35/35"
row. `T5_BUILD.md` describes test-085 by hand. The claim is plausible and harmless; it is simply
not evidence-backed at the granularity stated (16 rows, 35 values).

### C02 — "0–60 in 7.4 s, 0–100 in 16.4 s over 257 m, 138 km/h peak"
*Class:* read. *Location:* `T1_TRANSLATION.md:6-8`.
**Verdict: CONFIRMED** — `QA1_RESULTS.md:39-42` states exactly 7.4 s / 16.4 s / 257 m / 138 km/h
at 196.2 s from `Working/Translation/QA1/tail_trace.csv` (234 samples at 5 fps).
**Caveat (see C35):** the same file says the run was made "at the built 6,000 kg" while T-M1's
`now` column says 4,000 kg. The measurement and the `now` column therefore describe different
builds, which the table does not say.

### C03 — "all 423 decoded BmAK fields now map to a row, machine-checked by `bmak_coverage.py --check`"
*Class:* derived. *Location:* `T1_TRANSLATION.md:12-14`.
**Verdict: CONFIRMED.** `python Tools/scripts/bmak_coverage.py --check` → `check ok`
(the only output lines are per-row counts, e.g. `T-K1 1`).

### C04 — "2000 units = 20 m/s = 72 km/h"
*Class:* derived. *Location:* §0 units paragraph.
**Verdict: CONFIRMED** — 2000 cm/s = 20 m/s, ×3.6 = 72 km/h. Arithmetic only, no data needed.

### C05 — "`SteerSpeedVsSpeedCurve` is flat at 720 across 0…3500, i.e. 35 m/s"
*Class:* decoded/derived. *Location:* §0.
**Verdict: CONFIRMED** — `Research/BatmobileGrab/MECHANICS.md:118`:
`SteerSpeedVsSpeedCurve = 0.0 → 720.0  3500.0 → 720.0`; 3500 cm/s = 35 m/s.

---

## B. §1 — the donor decision

### C06 — "`FLEET.md` ranks 144 land vehicles; v0300 scores 0.358 (45/144)"
*Class:* decoded/derived. *Location:* §1, first table row.
**Verdict: PARTIAL.** 144 and 45/144 are CONFIRMED (`Research/JC3Grab/FLEET.md:4`: "**145**
vehicles have a `land_global` station set; **144** of them are …"; `:38`: "ranks **45 of 144**").
The score 0.358 is not in the sentence that states the rank and the all-vehicle table carries no
score column, so 0.358 is UNVERIFIABLE from FLEET.md alone. v0602 0.134 and v0201 0.164 are
CONFIRMED against the ranked table (`FLEET.md:15` 0.1336, `:18` 0.1643).

### C07 — Serpente "3.72 × 2.10 × 1.41" m
*Class:* decoded (claimed). *Location:* §1, first table row.
**Verdict: REFUTED against the cited source.** `FLEET.md:84` gives the donor as
`4.9999 | 2.1121 | 1.4051` (L | W | H). W and H match (2.10 / 1.41 rounded); **L does not**
(3.72 vs 5.00). Either the row uses a different length measure without saying so, or it is a
transcription error. Wheelbase 3.003, track 1.770, tyre Ø 0.76 and mass 975 all match FLEET.md.

### C08 — "the donor's shape is the one thing the project has already replaced"
*Class:* inferred. **Verdict: CONFIRMED as intent, not as measurement** — the geometry rows
(T-G1…T-G3) do override stations/tyres, and `Working/TrueScale/stations.json` exists. This is a
design statement, correctly labelled as a recommendation.

---

## C. §2 — geometry

### C09 — T-G4: ride height "derived (hub y; §70 assumed clearance = hub height)"
*Class:* **assumed, labelled `derived`.** *Location:* §2, T-G4.
**Verdict: REFUTED as `derived`** (R4). The row's own text admits the bridge is an assumption
("assumed clearance = hub height") yet the `conf` column says `derived` and §18 later relies on
`derived` rows being safe. Under R4 this row is `assumed`; it is honest in the transform column
and wrong in the confidence column. No file in the grab says a JC3 `ground_clearance` equals hub
height — FLEET.md's `hub y` is a station property, not the module's clearance.

### C10 — T-G5: "17 of 26 vehicles over 6 t use friction type 2"
*Class:* decoded (fleet). *Location:* §2, T-G5.
**Verdict: CONFIRMED.** Recomputed: 26 land vehicles ≥ 6 t carry
`wheels_friction_type`; 17 of them are 2 (`challenge_t1.py` J-FT1).

---

## D. §3 — mass and inertia

### C11 — T-M1: "3–8 t p75 = 6,000 kg"
*Class:* decoded (fleet). **Verdict: CONFIRMED** — 3–8 t n=35, median 5,100, **p75 6,000**
(J-M1).

### C12 — T-M1 basis: "no absolute mass tag … the sim scales a mass the streams never store"
*Class:* decoded (absence). *Location:* §3, T-M1.
**Verdict: CONFIRMED, and stronger than claimed.** `bmak_chain.py SVehicle.ChassisMass` →
`@1688 archetype=absent class-default=absent`; `SVehicleSimBase.WheelMass` → `@188 archetype=absent
class-default=absent`. The absence holds even in the class default object, which is the layer
chase-06/08 showed *does* carry other fields — so this is a real absence, not an unread layer.

### C13 — T-M2: "class median at 3–6 t is 2.48"
*Class:* decoded (fleet). **Verdict: CONFIRMED** — `unit_inertia_yaw` 3–6 t n=26, median 2.48
(J-M3).

### C14 — T-M3: "3–8 t median −0.3, band −1.1…0"
*Class:* decoded (fleet), claimed band. **Verdict: PARTIAL / band REFUTED.** Median is exactly
−0.3 (n=156) and p75 is 0.0, but the lower end is **−2.0**, not −1.1 (p25 −0.45). The band as
written is not what the fleet contains; the *value* −0.3 is a median and unaffected.

### C15 — T-M4: "the chain over `SVehicleWheel` finds only `MassScale` 1.0"
*Class:* decoded (absence), mis-attributed member. **Verdict: REFUTED as worded.**
`SVehicleWheel`'s SDK layout has 125 properties and **no `MassScale`** (checked against
`BMSDK_OFFSETS.json`); `MassScale` belongs to `SVehicle` @2068 = 1.0. The conclusion the row
draws — that no absolute wheel mass exists — is CONFIRMED (`SVehicleSimBase.WheelMass` absent in
archetype *and* class default). A reader checking the citation would find nothing there.

### C16 — T-M4: "armored transport 75; old truck 200; 25 kg is a supercar wheel"
*Class:* read. *Location:* §3, T-M4.
**Verdict: PARTIAL.** 3–8 t n=35: median 150, p25 75, p75 150, max 350 (front). So 75 is the
class *p25*, not a median, and 200 exists only as an individual vehicle (the old truck, 3,000 kg
class). The proposal 75/150 is inside the class band either way; the sentence's rhetorical
"supercar wheel" is an inference, not a measurement.

---

## E. §4 — suspension

### C17 — T-S1: "fleet median 30, band 4…80; 80 is the stiffest in the game and was set by hand"
*Class:* decoded (fleet). **Verdict: CONFIRMED exactly** — `front.strength` n=125, median 30,
min 4, max 80 (J-S1). The build's 80 really is the fleet maximum.

### C18 — T-S3: "In-domain for the 6 t+ class (0.18 … 0.75, n=26)"
*Class:* decoded (fleet). **Verdict: REFUTED (upper bound).** 6 t+ `front.length`: n=26,
min 0.18, **max 1.50** (J-SL1). The fleet's 6 t+ median is 0.18, not 0.75; the row's proposed
0.70 is still inside the real domain, but "0.18 … 0.75" understates the band by half.
The companion claim "3.9× its 0.18 median" is arithmetically right against the median.

### C19 — T-S3: "BmAK's own total wheel travel 30 + 40 = 70 cm = 0.70 m … the bridge is cm → m with no assumption"
*Class:* decoded + identity. **Verdict: CONFIRMED for the BmAK side, the *bridge* is an
inference.** `SuspensionTravelUp` 30.0 and `SuspensionTravelDown` 40.0 are in `CHAIN.json` as
claimed (B-S3/B-S4). That JC3's `suspension.length` is the *sum* of a BmAK up/down pair is a
kind-match on a name, not a decoded identity — the row labels it `identity (chain)`, which
overstates it under R5. It is the most defensible reading available; the wording should say so.

### C20 — T-S5: lateral tyre offset "fleet median 0.2 (`T3_FLEET.md` n=125, IQR 0.1…0.3;
`VOCABULARY.md` n=167 median 0.2)"
*Class:* class. **Verdict: UNVERIFIABLE as cited.** `t3_fleet.py` *does* compute
`front.lateral_tire_force_offset`, so T3_FLEET.md should carry it — but the second citation
(`VOCABULARY.md` n=167) is a different population and cannot both be the same fleet. Not resolvable
inside this challenge without re-deriving VOCABULARY; the value 0.2 is in the right band under
either reading.

---

## F. §5 — grip (the row the document calls the lever)

### C21 — T-R1: "fleet median by mass class is 3.0 in every class: 3.0 at 0–1.5 t, 3.0 at 1.5–3 t,
3.0 at 3–6 t, 2.5 at 6–15 t"
*Class:* class — **numerically unsourced.** *Location:* §5, T-R1; repeated in §14
("median 3.0 in every class").
**Verdict: REFUTED (three of four medians).** Recomputed from the decoded land fleet
(`front_wheels.arcade_friction_multiplier`):

| bucket | n | median | p25 … p75 |
|---|---|---|---|
| 0–1.5 t | 67 | **3.0** | 2.2 … 3.5 |
| 1.5–3 t | 25 | **2.8** | 2.75 … 3.0 |
| 3–6 t | 26 | **2.2** | 2.2 … 3.0 |
| 6–15 t | 18 | **2.0** | 1.5 … 3.0 |

Only the lightest class is 3.0. The heavy classes the Batmobile belongs to sit at 2.2 and 2.0.
The target 3.0 is still the **p75 of the 3–6 t class**, so "3.0 is defensible" survives — but as a
p75 choice, not as a median, and the sentence as written is false.
Additionally: `T3_FLEET.md` **has no arcade-friction row at all** (`t3_fleet.py`'s `MEMBERS` does
not include the member), so this row's numbers are not from the artifact it implies. That is the
R11 failure the table is supposed to have left behind.

### C22 — T-R1: "Serpente's 1.0 is an outlier"
*Class:* decoded. **Verdict: CONFIRMED** — the donor's `front_wheels.arcade_friction_multiplier`
is 1.0 (J-R2), below the 0–1.5 t p25 of 2.2. It is an outlier.

### C23 — T-R3: "all 26 6 t+ and 35 3–8 t land vehicles use 0 (`use_shape_cast`)"
*Class:* decoded (fleet). **Verdict: CONFIRMED** — 6 t+ n=26, all 0.0; the 3–8 t set is the same
population here (J-G1).

---

## G. §6 — steering

### C24 — "BmAK `StandardSteeringSpeedCurve` (cm/s → degrees): 0→60, 21.6→55, 39.6→55, 46.8→30, 72→20"
*Class:* decoded + converted. **Verdict: CONFIRMED.** `MECHANICS.md:116`:
`0.0 → 60.0  600.0 → 55.0  1100.0 → 55.0  1300.0 → 30.0  2000.0 → 20.0` — 600 cm/s = 21.6 km/h,
1100 = 39.6, 1300 = 46.8, 2000 = 72. Every conversion is exact.

### C25 — T-ST1: "55° is above the fleet's 45° max"
*Class:* decoded (fleet). **Verdict: CONFIRMED** — `steer_angle_min_speed_deg` (the lock) has
n=125, median 35, **max 45**; the 55° target is above every shipped car.

### C26 — T-ST2 note: "the fleet's fastest `t_to_full_steer_s` is 0.5 s (median 1.8, max 10 s over
125 land vehicles)"
*Class:* decoded (fleet). **Verdict: REFUTED in two of three numbers.** n=125 ✓, max 10.0 ✓, but
the **median is 2.0**, not 1.8, and the **minimum is 0.25 s**, not 0.5. The row's argument
("0.083 s is six times below the fastest shipped value") still holds with 0.25 s (3× below), so the
conclusion — do not copy BmAK's 720 °/s into `t_to_full_steer_s` — stands; the supporting numbers
do not.

### C27 — T-ST3: "land IQR (−1 … 0.8, n=125); the median −1 is the game's unused sentinel"
*Class:* class. **Verdict: CONFIRMED** — `max_speed_t_to_full_steer_s` n=125, p25 −1, p75 0.8,
median −1 (J-T4). The sentinel reading is an inference, correctly flagged as such.

### C28 — T-ST5: "Out of domain on both (countersteer 1.5 … 20, steer_in 1.2 … 10, n=252)"
*Class:* decoded (fleet). **Verdict: PARTIAL — bands CONFIRMED, n REFUTED.** countersteer min 1.5
max 20 ✓; steer_in min 1.2 max 10 ✓; **n=125, not 252.** 252 is not a population this fleet has
(156 land entities with mass; 125 with the steering members). The "declared R3" conclusion is
unaffected (1.0 is below both minima).

### C29 — T-ST6: "the chain has no `*Align*` member at all"
*Class:* decoded (absence). **Verdict: CONFIRMED** — `CHAIN.json` regex `Align` → 0 hits (B-A5).

---

## H. §7 — engine and transmission

### C30 — T-E1: "fleet fit `optimal_rpm = 2.105e4·m^−0.264`, R²=0.52 → 2,120 rpm at 6 t"
*Class:* derived (fit). **Verdict: CONFIRMED.** Recomputed over 144 land vehicles:
coefficient **21,046**, exponent **−0.2635**, R² **0.516**, prediction at 6,000 kg **2,126 rpm**
(J-F2). The doc's 2,120 is the same fit rounded.

### C31 — T-E2: "torque fit `2.153 · mass^0.719`, R² 0.81, ≈1,121 at 6,000 kg"
*Class:* derived (fit). **Verdict: CONFIRMED.** Recomputed: coefficient **2.1530**, exponent
**0.71852**, R² **0.8077**, prediction at 6 t **1,116** (J-F1). The 1,121 vs 1,116 difference is
rounding in the published coefficients; the ×1.24 margin the document claims (1,393.5 / 1,121)
becomes ×1.25 against 1,116 — immaterial.

### C32 — T-E4: "armored transport 5 gears"
*Class:* read. **Verdict: UNVERIFIABLE in this pass** — `transmission.gears` is not among the
members `challenge_t1.py` reads and the value was not re-derived. Not contradicted, not confirmed.

### C33 — T-E5: "336 sits inside the shipped domain `official_top_speed` 25 … 350 (n=233, median 150)"
*Class:* class. **Verdict: PARTIAL — domain and median CONFIRMED, n REFUTED.**
`official_top_speed`: n=**156**, min 25, max 350, median 150 (J-N1). 233 is the vehicle-entity
count, not the number of vehicles carrying the member. The conclusion (336 is in-domain) holds.

---

## I. §8 — boost

### C34 — T-B1: "standard 200 at 0 m/s vs boost 260 → ×1.30; at 21 m/s standard 105 vs boost 220 → ×2.10;
boost then decays to 150 by 30 m/s"
*Class:* decoded. **Verdict: CONFIRMED.** `MECHANICS.md:113-114`: boost points `0 → 260`,
`2100 → 220`, `3000 → 150`; standard `0 → 200`, `2100 → 105`. 260/200 = 1.30, 220/105 = 2.095,
3000 cm/s = 30 m/s, 2100 cm/s = 21 m/s.

### C35 — T-B2: "`FakeExtraSpeedMax` 3500, `FakeExtaSpeedAccel` 600, `FakeExtaSpeedDecel` 2000,
`BoostDuration` 2.0 s (class default, no archetype override) … min(3500, 600×2.0) = 1200 cu =
43.2 km/h"
*Class:* decoded (claimed via `CHAIN.json`). **Verdict: CONFIRMED AS VALUES, MIS-CITED.**
* Values: `Research/BatmobileGrab/SPEEDOMETER.json` fields (class `RVehicleBatmobileBase`) give
  `FakeExtraSpeedMax` default **3500.0**, `FakeExtaSpeedAccel` **600.0**, `FakeExtaSpeedDecel`
  **2000.0**. `python Tools/scripts/bmak_chain.py RVehicleSimBatmobile.BoostDuration` →
  `@664 archetype=absent class-default=2.0 (Default__RVehicleSimBatmobile)`.
* Citation: `CHAIN.json` contains **none** of these four names — its `fields` cover 20 classes,
  and `RVehicleBatmobileBase` / the boost members are not among them. The value is right; the
  cited artifact cannot produce it.
* Arithmetic: 600 × 2.0 = 1200 cu; 1200 × 0.036 = 43.2 km/h ✓; 3500 cu = 126 km/h ✓.
* Sub-claim "`InfiniteBoost` false (bool word 4194304, bit 29 clear)": **arithmetically
  inconsistent** — 4,194,304 = 2^22, so a "bit 29" statement about that word cannot be right. The
  conclusion (false) rests on the property having no tag, which is absence, not a read bit.
  Labelled `decoded` in the row; it is `inferred` at best.

### C36 — T-B3: "boost-grip 5.68 → 1.0" vs §18 "T-B3 5.68 → 2.0"
*Class:* derived / internally contradictory. *Locations:* §8 T-B3, §18 row 3.
**Verdict: REFUTED as one document.** The table proposes **1.0**; the batch table says the change
is **5.68 → 2.0**. They cannot both be the plan. The current build (`current.json`, test-091)
ships **1.0**, i.e. the table's value, so §18 is stale — but §18 is the section a builder reads
for "what changed in this pass".
Supporting fleet fact the row cites ("below every shipped car, 1.2 … 2") is **CONFIRMED**:
6 t+ `nitro_boost.grip_multiplier` n=26, median 2.0, min 1.2, max 2.0 (J-B1); doc's n=145 is 144.

### C37 — T-B4: "heat_boost blend 0 / extra 80 / grip 1.5 / torque 2; turbo_jump punch 0.1 s /
50 km/h / top 200 km/h (VOCABULARY.md n=145, donor column)"
*Class:* read. **Verdict: UNVERIFIABLE in this pass** (VOCABULARY donor column not re-read).
Not contradicted.

---

## J. §9 — aerodynamics

### C38 — T-A1: "3–8 t IQR 4 … 6.72, median 6.5"
*Class:* decoded (fleet). **Verdict: CONFIRMED exactly** — n=35, median **6.5**, p25 **4.0**,
p75 **6.72** (J-A1). The gross cross-section 3.5 × 2.27 = 7.945 is arithmetic.

### C39 — T-A2: "fit at 4 t 0.57, R²=0.13 → class not law; armored transport 0.80, old truck 0.50"
*Class:* class. **Verdict: CONFIRMED.** Recomputed log-log fit over 141 land vehicles:
coefficient **0.264**, exponent **0.090**, R² **0.130**, prediction at 4,000 kg **0.556**.
`drag_coefficient` for `v0602_…_military_01` = **0.80**, for `v0505_…_military_01` = **0.50**.
The 3–8 t band is 0.5 … 0.8 (median 0.6), so the proposed 0.55 is inside it.

### C40 — T-A4: "armored transport −0.3, old truck −0.1, tank 0"
*Class:* class. **Verdict: CONFIRMED** — the three entities carry `lift_coefficient`
−0.300000012, −0.100000001, 0.0 respectively.

---

## K. §10 — brakes

### C41 — T-K1: "class median at 3–6 t is 5,000; armored transport 2,500; tank 30,000" → proposed
5,000 / 5,000
*Class:* class — **numerically unsourced.** *Location:* §10 T-K1; repeated in §14 ("class median
5,000 … double").
**Verdict: REFUTED.** `front.max_brake_torque` at 3–6 t: n=26, **median 9,000**, p25 7,250,
p75 10,250, **min 5,000**, max 15,000. The armored transport is **14,000** front and rear, not
2,500. The tank at 30,000 is right.
Consequences: (a) the build's 10,000 was *at* the class median, not double it — §14's "double"
verdict is wrong; (b) the proposed 5,000 is the class **minimum**, which would make a 6 t car brake
worse than every shipped heavy vehicle; (c) `T3_FLEET.md` has no brake-torque row, so these numbers
are not from a generated table.
This is the single most decision-changing refutation in the document, and it points the opposite
way from the text.

### C42 — T-K1 bridge check: "4 × 300 N·m over 6,000 kg × 0.683 m = 0.29 m/s², against 3.5–3.8
measured, so the member's scale is not JC3's"
*Class:* derived. **Verdict: CONFIRMED (arithmetic).** 4 × 300 / (6000 × 0.683) = 0.293 m/s².
`MaxBrakeTorque` 300 is in `CHAIN.json` (B-K1). The inference "not the same quantity" follows
from a 12× gap and is correctly labelled a disproof by magnitude, not an assumption.

### C43 — T-K2: "fleet median −1 reads as the unused sentinel and the land IQR is −1 … 1 (n=271)"
*Class:* class. **Verdict: PARTIAL — IQR CONFIRMED, n REFUTED.** `min_time_to_block`: n=**144**,
p25 −1, p75 1, median −1, max 20. The sentinel reading is plausible (144 of 144 at −1 or ≥1? the
median and p25 both −1) and is labelled as a reading, not a value.

### C44 — T-K2: "the donor's shipped value is 1"
*Class:* read. **Verdict: CONFIRMED via the build** — `current.json` (test-091) ships
`front.min_time_to_block` 1 and `rear.min_time_to_block` 1, i.e. the value became live, so
"donor's shipped value" now describes the mod's own build rather than the vanilla donor. Wording
drift, value fine.

---

## L. §11–§13 — native blocks, lights, parts

### C45 — §11: "`drift.min_speed_to_drift_kmph` (10) and `drift.max_drift_angle_deg` (45) stay
because the Batmobile does drift in Arkham Knight"
*Class:* inferred (behaviour from a name). **Verdict: PARTIAL.** BmAK does carry a slip-gain pair
(`LatSlipFactor` **1.6** — `CHAIN.json` B-D1) and a handbrake slip factor, which is behavioural
evidence that drift exists; no BmAK member names a drift *angle* or speed. Keeping the donor's two
values is a JC3-native choice (as §11 itself says), not a translation — correct as written, but the
sentence "because the Batmobile does drift" is behaviour-talk over name-matched numbers (R5).

### C46 — §12: "the donor's 22 `SVehicleLight` entries" and "28 BmAK entries across 4 packages"
*Class:* decoded. **Verdict: UNVERIFIABLE in this pass** — the light counts need `ENTITIES.md` /
`LIGHTS.json` tabulation; not re-derived here. The JC3 side is the donor's own graph (test-091
inherits it), so a miscount would not change a value, only the coverage claim.
### C47 — §13 T-P3: "11 driveable boxes map onto 7 donor hull slots; 21 are not driveable
collision; 11 T-8 parts have no slot"
*Class:* decoded. **Verdict: UNVERIFIABLE here** — these come from `t16_collision.json` (T-22),
not re-read in this pass. Flagged because the row's `conf` column says `written (G2-30)` while the
doc's §0 legend has no `written` class: a fifth provenance word that R4 does not define, inside the
table whose job is to define them.

---

## M. §14–§18 — the build comparison and the batch

### C48 — §14: "build 083: mass 4,000; inertia yaw 1.8; strength 80/80; wheel mass 25/75;
friction 1.0; friction type 0; rpm 1000/5000/7300; drag 0.139; lift −1.95; brake 10,000;
nitro grip 5.68; steering 35°→15°"
*Class:* read (claimed `current.json`). **Verdict: REFUTED as "the build".**
`Working/Translation/current.json` reports `build: E:\Modding\JC3-Batmobile\Builds\test-091` and its
values are **mass 6,000; inertia 4 / 2.6 / 1.2; strength 45/45; wheel mass 75/150; friction 3.0;
friction type 2; rpm 800–1000 / 2,800 / 4,500; suspension length 0.70; drag 0.55; lift −0.30;
brake 5,000/5,000; min_time_to_block 1; nitro grip 1; extra top speed 43.2; steering 55°→20°;
frontal area 6.63; official top speed 336.4.**
Every "build 083" figure in §14 and in the `now` column of the row tables is therefore a historical
value presented as current. The table's own §0 says `now` is "read from `current.json`, not from
notes" — `current.json` no longer says these numbers.

### C49 — §17: "The test-085 build was not a tuning build. It carried the rows above …"
*Class:* inferred. **Verdict: REFUTED by the same evidence as C48** — those rows are already in
test-091, and test-085 predates test-091, so "carried by test-085" cannot be checked from
`current.json` at all. The section narrates a build the repo no longer dumps.

### C50 — §18: "T-B3 5.68 → 2.0" (see C36) and "T-ST5 2.0/1.5 → 3.0/2.0"
*Class:* derived. **Verdict: REFUTED.** The table (§6 T-ST5) proposes **1.0 / 1.0**; §18 says
**3.0 / 2.0**; the build ships **1.0 / 1.0** (`current.json`). Three different numbers for one row
in one document, and §18 matches neither the table nor the build.

### C51a — §15 blocked row: "collision shapes (T-P3) | the *write* side: nothing in this toolkit
writes a `.physicsc`"
*Class:* tooling claim. *Location:* §15, row 3.
**Verdict: REFUTED (stale).** `Tools/scripts/jc3hkx.py:2125` records T-P3 as "unblocked for
hull-based collision" and its `--write` emits `.physicsc` blobs
(`open(… name + ".physicsc", "wb")`, `:2199`, then `wrote N .physicsc blobs`). A `.physicsc`
writer therefore exists in this toolkit; what remains open is shape fidelity (BmAK boxes vs JC3
hulls), not the ability to write.

### C51 — §15: "G1-1 is solved … but it does not supply these: no stream carries a tag at those
offsets, so no value reaches this table"
*Class:* decoded (absence). **Verdict: CONFIRMED for the four mass members, and the challenge
strengthens it**: the absence also holds in the class default objects
(`SVehicle.ChassisMass` archetype=absent **class-default=absent**; `SVehicleSimBase.WheelMass`
archetype=absent class-default=absent), which is the layer G1-1 never read and where other fields
(`InertiaTensorMultiplier` [1,1,1], `MassScale` 1.0) *are* present. So this limitation is genuine,
unlike several other claims of the same kind in this document.

---

## Summary table

| id | claim | verdict |
|---|---|---|
| C01 | 35/35 read-back of test-085 | UNVERIFIABLE |
| C02 | 0–100 16.4 s / 257 m / 138 km/h | CONFIRMED (different build than `now`) |
| C03 | 423 fields mapped | CONFIRMED |
| C04 | 2000 cu = 72 km/h | CONFIRMED |
| C05 | 720 °/s flat, 0…3500 | CONFIRMED |
| C06 | 144 land vehicles, 45/144, score 0.358 | PARTIAL |
| C07 | donor 3.72 × 2.10 × 1.41 | REFUTED (L) |
| C09 | T-G4 ride height `derived` | REFUTED as class (it is assumed) |
| C10 | 17 of 26 over 6 t friction type 2 | CONFIRMED |
| C11 | 3–8 t mass p75 6,000 | CONFIRMED |
| C12 | no absolute mass tag | CONFIRMED |
| C13 | inertia 2.48 at 3–6 t | CONFIRMED |
| C14 | CoM −0.3, band −1.1…0 | PARTIAL (band) |
| C15 | SVehicleWheel MassScale | REFUTED (wrong class) |
| C16 | wheel mass 75 / 200 | PARTIAL |
| C17 | strength median 30, band 4…80 | CONFIRMED |
| C18 | suspension length 0.18…0.75 at 6 t+ | REFUTED (max 1.5) |
| C19 | travel 30+40 → 0.70 m "no assumption" | PARTIAL (bridge is a kind-match) |
| C20 | lateral offset 0.2, two populations | UNVERIFIABLE |
| C21 | friction 3.0 in every class | **REFUTED** |
| C22 | donor friction 1.0 is an outlier | CONFIRMED |
| C23 | shape cast 0 for heavy | CONFIRMED |
| C24 | steering curve conversions | CONFIRMED |
| C25 | fleet lock max 45° | CONFIRMED |
| C26 | fastest t_to_full 0.5, median 1.8 | REFUTED (0.25 / 2.0) |
| C27 | max_speed_t_to_full IQR −1…0.8 | CONFIRMED |
| C28 | countersteer/steer_in n=252 | PARTIAL (n=125) |
| C29 | no `*Align*` member | CONFIRMED |
| C30 | optimal_rpm fit → 2,120 | CONFIRMED |
| C31 | torque fit → 1,121 | CONFIRMED |
| C33 | top-speed domain n=233 | PARTIAL (n=156) |
| C34 | boost ratios 1.30 / 2.10 | CONFIRMED |
| C35 | boost members 3500/600/2000/2.0 | CONFIRMED, MIS-CITED |
| C36 | nitro grip target 1.0 vs 2.0 | REFUTED (internal) |
| C38 | frontal area median 6.5, IQR 4…6.72 | CONFIRMED |
| C39 | drag fit 0.57 at 4 t, R² 0.13 | CONFIRMED |
| C40 | lift −0.3 / −0.1 / 0 | CONFIRMED |
| C41 | brake torque median 5,000; armored 2,500 | **REFUTED** (9,000; 14,000) |
| C42 | 300 N·m → 0.29 m/s² | CONFIRMED |
| C43 | min_time_to_block IQR −1…1, n=271 | PARTIAL (n=144) |
| C45 | drift values kept "because it drifts" | PARTIAL (name→behaviour) |
| C48 | §14 / `now` = build 083 values | **REFUTED** (current is test-091) |
| C49 | "carried by test-085" | REFUTED by C48 |
| C50 | §18 T-ST5 3.0/2.0 | REFUTED (table 1.0/1.0) |
| C51 | no mass value reaches the table | CONFIRMED |

## Method and limits

* Every JC3 number is recomputed by `Tools/scripts/chase/challenge_t1.py` from the decoded
  `entities/*.ee.json` (the same reader `t3_fleet.py` uses), not copied from `T3_FLEET.md`.
  `current.json` is read directly for the build comparison.
* BmAK numbers come from `Research/BatmobileGrab/CHAIN.json` (checked current by
  `bmak_chain.py --check` → `PASS: chain record current (105 objects, 9225 named bindings, 336
  cross-checked, 0 conflicts, 0 bool words left unnamed)`), from `MECHANICS.md` for the curves
  (`CHAIN.json` stores curve structs with `value: null`), and from live
  `bmak_chain.py <Class>.<prop>` lookups for the seven members the chain file does not carry.
* Counts the document states as fleet facts were recomputed over **156 land entities that carry
  `rigid_body.mass`** (144 of those also have a `land_global` station set — the population
  `FLEET.md` scores). Where the document's n differs (233, 252, 271), the claim above names the
  bucket, so the difference is not a definitional one.
* Not attempted: re-deriving the `VOCABULARY.md` populations (C20, C37), the light census (C46),
  the collision-slot mapping (C47), transmission gears (C32). Each is marked UNVERIFIABLE rather
  than guessed.
* No game was launched; the JC3 install was not opened for this challenge (the decoded cache
  sufficed); nothing outside `E:/Modding/_JC3grab/challenge/` and these two new repo files was
  written.
