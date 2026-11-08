STATUS: done

# Drive-mode torque arithmetic — independent re-derivation of every step (MOD-3 / G3-02l substitute)

Read-only check. No `Research/` file, module, `.epe`, build tree or game binary was touched; only this
report was created.

**Plan checked:** `tmp/freebuff/reports/drive-mode-torque-arithmetic-substitute-plan.md` (347 lines).
**Method:** each numeric line was recomputed from the stated expression with `python -I` (stdlib only),
and each input was traced to the exact line of the file the plan cites. Verdicts:

| verdict | meaning |
|---|---|
| **VERIFIED** | the expression reproduces the printed result, and every input is at the cited file/line |
| **VERIFIED–NOTE** | arithmetic reproduces, but the input is only findable in the cited file with a value the plan does not name (median, donor, etc.) |
| **WRONG SOURCE** | the input is not in the cited member/row; the plan quoted another member's range |
| **ARITHMETIC ERROR** | the printed result does not follow from the printed expression |
| **MISLABEL** | the number is right but the word attached to it (a percentage) is wrong |
| **UNKNOWN** | a constant with no cited source; the grab file that would supply it is named in the row |

Source shorthand: **DM** = `Research/BatmobileGrab/DRIVE_MODES.md`; **VOC** =
`Research/JC3Grab/VOCABULARY.md`; **CAR** = `Research/JC3Grab/DRIVE_CARRIERS.md`; **MODES** =
`Research/BatmobileGrab/MODES.md`; **AC** = `tmp/freebuff/reports/air-control-closest-system-plan.md`;
**4WD** = `tmp/freebuff/reports/four-wheel-drive-and-spin-in-place-build-plan.md`; **PRED** =
`Working/Q/PREDICTIONS.md`.

---

## 1. The spin chain — mode 1 (§2, plan lines 105–144)

| # | step (plan line) | plan's expression | inputs traced to the cited file | independent re-derivation | verdict |
|---:|---|---|---|---|---|
| 1 | engine-braking bridge (109) | `r = 0.1 × 0.01 / 0.003 = 0.333` | 0.1 = donor `resistance_at_optimal_rpm` (VOC 838); 0.01 = `TurnOnSpotModeEngineBrakingFactor` (DM 54); 0.003 = `DriveModeEngineBrakingFactor` (DM 55) | 0.1 × 0.01 / 0.003 = **0.333333** | **VERIFIED** |
| 2 | normaliser sum (107) | `0.6 + 0.5`; `0.8 + 0.8` | 0.6 / −0.5 (DM 52–53); 0.8 / −0.8 = archetype pair (MODES 80–81; 4WD 90–94) | 1.1 / 1.6 | **VERIFIED** |
| 3 | counter-torque base (107) | `T = 20000 × (0.6 + 0.5) / (0.8 + 0.8) = 20000 × 0.6875` | 20 000 = fleet max of `drift.constant_drift_torque` (VOC 467, 0..20000); 0.6875 from row 2 | 20000 × 1.1 / 1.6 = **13 750.0 N·m** | **VERIFIED** |
| 4 | spin rate (108) | `ω = 1.80 / 0.885 = 2.034 rad/s = 116.5 °/s` | 180 cm/s = `DesiredTurnOnSpotSpeed` (DM 56); 0.885 m = `base_wheel_hardpoint_positions[0/1].position[0]` ±0.885 (CAR 426, 429) | 1.80 / 0.885 = **2.03390 rad/s** = **116.534 °/s** | **VERIFIED** (the use of half-track as the spin radius is the plan's stated model, not a file value) |
| 5 | one turn (108) | `one turn in 3.09 s` | ω from row 4 | 2π / 2.03390 = **3.08923 s** | **VERIFIED** |
| 6 | yaw inertia (119) | `I_zz = 6000 × 4.0 = 24 000 kg·m²` | mass 6000, `unit_inertia_yaw` 4.0, `use_calculated_inertia` 1 (AC 71, from `Builds/bm-RC2` `rigid_body.vmodc`) | 6000 × 4.0 = **24 000** | **VERIFIED** arithmetically; conditional on the plan's own U1 (a computed tensor may replace it) |
| 7 | angular acceleration (122) | `α = 13 750 / 24 000 = 0.573 rad/s² = 32.8 °/s²` | 13 750 = row 3; 24 000 = row 6 | 13750 / 24000 = **0.572917 rad/s²** = **32.826 °/s²** | **VERIFIED** |
| 8 | 90° time (123) | `θ(t)=½αt² → 90° in 2.34 s` | α = row 7 | t = √(2·(π/2)/0.572917) = **2.34169 s** | **VERIFIED** |
| 9 | 360° time (123) | `360° in 4.68 s` | α = row 7 | t = √(2·2π/0.572917) = **4.68338 s** | **VERIFIED** |
| 10 | 30° in 1.0 s torque (133) | `α = 1.047 rad/s² → 25 133 N·m` | I_zz = row 6 | α = 2·(π/6)/1 = 1.047198; T = 1.047198 × 24 000 = **25 132.7 N·m** | **VERIFIED** (indeed above the 20 000 fleet max, VOC 467) |
| 11 | 90° in 2.0 s torque (137) | `α = 0.785 rad/s² → 18 850 N·m` | I_zz = row 6 | α = 2·(π/2)/4 = 0.785398; T = **18 849.6 N·m** | **VERIFIED** |
| 12 | 2.0 s at I = 17 600 (143, 248) | "18 850 N·m at I = 17 600 would also give 2.0 s"; "17 600 at t = 2.0 s" | **17 600 has no cited file**; mass/inertia ranges exist at VOC 1044–1060, but no effective tensor | 18850 / 17600 = 1.07102 rad/s² → t = **1.713 s**, not 2.0 s. The torque that actually gives 2.0 s at 17 600 is **13 823.0 N·m** | **ARITHMETIC ERROR + UNKNOWN** — constant unsourced. Grab file that supplies the inputs: `Research/JC3Grab/VOCABULARY.md` §`RigidBody` (`mass`, `unit_inertia_yaw`, `use_calculated_inertia`); the effective tensor itself is native (RigidBody consumer, `JustCause3.exe`) |
| 13 | 35° in 0.5 s torque (162) | `35° in 0.5 s needs 117 286 N·m` | I_zz = row 6 | α = 2·(35π/180)/0.25 = 4.88692; T = **117 286.1 N·m** | **VERIFIED** |
| 14 | rear grip (163) | `grip_rear = grip_front × (1 + f) = 2.8 × 0.5 = 1.4` | f = −0.5 (DM 66); front range 0.8..5 **median 2.8** (VOC 852); rear range 1..6 (VOC 866) | 2.8 × (1 − 0.5) = **1.4** | **VERIFIED–NOTE**: the plan cites only the range; 2.8 is the VOC 852 fleet median, not the donor (donor is 1) and the plan never says so |
| 15 | lateral slip clamps (165) | `12×4 = 48 → 15`; `20×4 = 80 → 25`; "compressed to 1.25× / 1.25×" | 12 / 20 = donor `lat_peak_sa_deg` / `lat_sat_sa_deg` (VOC 1236–1237); 4 = `BattleModeLatSlipScale` (DM 74); maxima 15 / 25 = VOC 1236–1237 | 12×4 = 48 → clamp 15; 20×4 = 80 → clamp 25; 15/12 = **1.25**, 25/20 = **1.25** | **VERIFIED** |
| 16 | longitudinal slip clamps (166) | `0.5×10 = 5.0`; `2×10 = 20 → clamp 10` | 0.5 / 2 = donor `fwd_peak_sr` / `fwd_sat_sr` (VOC 1234–1235); 10 = `BattleModeLongSlipScale` (DM 75); maxima 9 / 10 (VOC 1234–1235) | 0.5×10 = **5.0**; 2×10 = 20 → **10** | **VERIFIED** |
| 17 | battle engine braking (169) | `r = 0.1 × 0.025 / 0.003 = 0.833 → clamp 0.5; shortfall 1.67×` | 0.1 (VOC 838); 0.025 = `BattleModeEngineBrakingFactor` (DM 76); 0.003 (DM 55); max 0.5 (VOC 838) | 0.1×0.025/0.003 = **0.833333**; 0.833333/0.5 = **1.66667** | **VERIFIED** |
| 18 | drive-force gain (168) | `BattleModeDriveForceFactor` 75 → `arcade.heat_boost.torque_multiplier` **40**; `75/40 = 1.88×` | 75 (DM 71) ✓; **but `arcade.heat_boost.torque_multiplier` is 2..4.5, donor 2 (VOC 444)** — 1.5..40 is `arcade.nitro_boost.torque_multiplier` (VOC 449); `nitro_boost_upgraded` reaches 80 (VOC 454) | 75/40 = 1.875 arithmetically, but 40 is outside heat_boost's fleet range by 8.9×. At the correct max: 75/4.5 = **16.667×** | **WRONG SOURCE** — the multiplier's cited range belongs to a different member; the write value 40 is not shipped in `heat_boost` |
| 19 | battle speed cap (171) | `1200 cm/s = 43.2 km/h; 90/43.2 = 2.08×` | 1200 (DM 72); 90 = fleet min `Transmission.top_speed` (VOC 1343, 90..505, donor 320) | 1200 × 0.036 = **43.2 km/h**; 90/43.2 = **2.08333** | **VERIFIED** |
| 20 | Z-offset unit (170) | `10 cm = 0.10 m` | 10 = `BattleModeDrivingForceZOffset` (DM 77); member range 0..0.2 m (VOC 1153, 1167) | 10 cm = **0.10 m** | **VERIFIED** |
| 21 | Z-offset front/rear split (170) | `front 0.05 / rear 0.10` | **0.5 split has no cited constant**; both VOC 1153/1167 only give the 0..0.2 range | 0.10 / 2 = 0.05 — arithmetic is trivial, but the half is an author choice | **UNKNOWN** — no grab file supplies a front/rear force split; `Research/JC3Grab/VOCABULARY.md` §`Suspension` gives the ranges only |

---

## 2. Dodge / strafe (§5, plan lines 192–200)

| # | step (plan line) | plan's expression | inputs traced to the cited file | independent re-derivation | verdict |
|---:|---|---|---|---|---|
| 22 | punch speed (196) | `Δv = 100000 / 6000 = 16.67 m/s = 60.0 km/h` | `BattleDodgeImpulse` 100000 (DM 90); mass 6000 (AC 71) | 100000/6000 = **16.6667 m/s** = **60.0 km/h** | **VERIFIED** |
| 23 | punch shortfall label (196) | "the member's shipped value is fixed at 50 … the 20 % shortfall recorded" | shipped 50 = `arcade.turbo_jump.punch_speed_kph` 50..50, n=145 (VOC 457) | 10 km/h against a 60 km/h target = **16.67 %**, not 20 % (20 % is of the written 50) | **MISLABEL** — number is right, percentage basis is not |
| 24 | mode-2 torque (214, 254) | `4125 (= 0.3 × 13750)`; `13 750 vs 4125 = 3.33×` | 0.3 = `BattleModeTurnOnSpotTorqueFactor` (DM 61); 13 750 = row 3 | 0.3 × 13750 = **4125**; 13750/4125 = **3.33333** | **VERIFIED** |
| 25 | cooldown (197) | `StrafeCooldown` 0.75 s → `turbo_jump_cooldown`; "5..5 on 232 builds" | 0.75 (DM 85); member 5..5 (VOC 1567) | 1:1 seconds, no arithmetic. The member row says **n=233**, not 232 | **VERIFIED–NOTE** (count off by one: 233 builds, not 232) |

---

## 3. Derived bands and the inverse-inertia check (§7, plan lines 237–273)

| # | step (plan line) | plan's expression | inputs traced to the cited file | independent re-derivation | verdict |
|---:|---|---|---|---|---|
| 26 | P-MODE-1 90° band (265) | `2.34 s ±20 % → 1.9–2.8 s` | row 8 | 2.34169 × 0.8 = 1.873; × 1.2 = 2.810. Plan's 1.9–2.8 is rounded **inward** (narrower than ±20 %) | **VERIFIED–NOTE** (rounding narrows the low edge by 0.027 s) |
| 27 | P-MODE-1 360° band (265) | `±20 % → 3.7–5.6 s` | row 9 | 4.68338 × 0.8 = 3.747; × 1.2 = 5.620. Plan's 3.7 is rounded inward by 0.047 s | **VERIFIED–NOTE** (same rounding) |
| 28 | P-MODE-2 yaw ratio (270–271) | `2.5 / 1.5 = 1.667`; band `1.33–2.00×` | 2.5 = `BattleModeSteerAngleFactor` (DM 64); 1.5 = donor `steer_in_speed_factor` (VOC 888) | 2.5/1.5 = **1.66667**; ±20 % = **1.333–2.000** | **VERIFIED** |
| 29 | inverse inertia at 2.34 s (248) | `I_eff = T t²/(2θ)` = 24 000 at t = 2.34 s | T = 13 750, θ = π/2 | 13750 × 2.34169² / π = **24 000** (using the rounded 2.34: 23 965, +0.15 %) | **VERIFIED** |
| 30 | inverse inertia at 2.0 s (248) | `17 600 at t = 2.0 s` | same formula | 13750 × 4 / π = **17 507.0**, not 17 600 (0.53 % off; and 17 600 is unsourced, row 12) | **ARITHMETIC ERROR** (minor); the unsourced constant is the same one as row 12 |
| 31 | coast ratio and clamp (249) | `0.833/0.1 = 8.33×`; clamp `5×`; "measured ratio should land in `1.5–5.0`" | 0.833 = row 17; 0.1 = VOC 838; max 0.5 → 0.5/0.1 = 5 (VOC 838) | 0.833333/0.1 = **8.33333**; 0.5/0.1 = **5.0** | **VERIFIED** for 8.33× and 5×; the **1.5 lower bound is UNKNOWN** — no cited file supplies it (`Research/JC3Grab/VOCABULARY.md` gives only the 0..0.5 member range, i.e. 0..5×) |
| 32 | drive-gain linearity (250) | "40/2 predicts ≈ 20×" | 40 = the value from row 18 (wrong member); 2 = donor `heat_boost.torque_multiplier` (VOC 444) | 40/2 = **20** arithmetically | **VERIFIED** arithmetic, but inherits row 18's wrong 40; at the correct max 4.5/2 = 2.25× |
| 33 | yaw offset (174) | `16384 = 90°` | `BattleModeYawOffset` 16384 (DM 83, 115) | 16384/65536 × 360 = **90.0°** | **VERIFIED** |

---

## 4. Formula constants never given a value (§6, plan lines 204–229)

| # | step (plan line) | plan's expression | what is missing | grab file that would supply it | verdict |
|---:|---|---|---|---|---|
| 34 | per-tick drive force (219) | `F_drive = gain × T_eng(rpm) × gear × final_drive / r_w` | `r_w` (wheel radius) is never valued; `T_eng(rpm)` is native | `Research/JC3Grab/VOCABULARY.md` `front_wheels.radius` 0.2..1.8, med 0.36 (VOC 855) and `rear_wheels.radius` (VOC 869); gear/final-drive ranges at VOC 1329–1332 | **UNKNOWN** (no numeric step is actually evaluated here) |
| 35 | `max_drift_torque` = 20 000 (108) | no formula, no cited derivation | 20 000 duplicates the `constant_drift_torque` fleet max, but `max_drift_torque` is a different member (0..35 000, donor 5000) | `Research/JC3Grab/VOCABULARY.md` drift rows (VOC 467, 479) supply the ranges, not the choice | **UNKNOWN** (unsourced choice, not arithmetic) |

---

## 5. What the recount changes

**Hard defects (fix before the plan is used):**

1. **Row 18 — wrong member.** `arcade.heat_boost.torque_multiplier` is **2..4.5** (VOC 444); the
   plan quotes **1.5..40**, which is `arcade.nitro_boost.torque_multiplier` (VOC 449). The write value
   **40** cannot be held by the cited member, and the recorded "1.88× shortfall" becomes **16.67×** at
   the real maximum (4.5). `BattleModeDriveForceFactor` 75 is unchanged (DM 71).
2. **Row 12 / 30 — the 17 600 figure.** It has no source, and the arithmetic attached to it is false:
   18 850 N·m at I = 17 600 gives **1.71 s**, not 2.0 s; 2.0 s needs **13 823 N·m**. The corrected
   inverse-inertia line at t = 2.0 s is **17 507**, not 17 600.

**Wrong word, right number:** row 23 — 60 → 50 km/h is a **16.7 %** shortfall against the 60 km/h
target (20 % only if measured against 50).

**Unsourced constants (marked UNKNOWN above):** the front/rear 0.05/0.10 Z-offset split (row 21), the
1.5× lower band in the coast test (row 31), and the `max_drift_torque` 20 000 choice (row 35); the
formula's `r_w` is unvalued (row 34). The grab files that carry the inputs are named per row.

**Verified cleanly:** 24 of the 35 rows reproduce exactly, and 4 more (rows 14, 25, 26, 27)
reproduce with a note, for 28 arithmetic-clean rows — including the whole core chain
(13 750 N·m → I 24 000 → α 0.573 → 2.34 s / 4.68 s) and the 117 286 N·m and 43.2 km/h conversions.
Two rows fail their own arithmetic (12 and 30), one cites the wrong member (18), one mislabels a
percentage (23), and the unsourced constants are rows 21, 31 (the 1.5 floor only), 34 and 35.

**Not checked here (out of scope, no arithmetic):** whether `SetDriveMode`'s body does what the
substitute assumes (still UNKNOWN, `REGISTRATION.md` gives only the address); whether the shipped CDO
or the archetype set is what the delivered car runs (the plan's U10); and the native sensor values
behind the BmAK fields.

## 6. Files and revert

| file | change | revert |
|---|---|---|
| `tmp/freebuff/reports/drive-torque-arithmetic-check.md` | **new** (this report) | delete it |

Nothing else was written: no `Research/` file, module, `.epe`, ledger row or build tree was modified,
and no game binary was run.
