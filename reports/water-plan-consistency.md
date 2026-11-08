# Two water plans, one grab: 12 shared thresholds agree exactly, 1 claim disagrees (splash), 10 thresholds have no counterpart

**Task.** Compare every **depth**, **speed** and **time** threshold in
`tmp/freebuff/reports/water-crossing-batmobile-build-plan.md` (**A**) and
`tmp/freebuff/reports/water-and-terrain-handling-plan.md` (**B**), list the pairs that disagree, and for
each disagreement check which value cites a grab file, quoting that file's line. Neither plan was edited.

**Result.** 23 threshold rows: **13 agree, 0 disagree, 10 exist in only one plan**. All 12 shared
numbers agree exactly — same member, same value, same `WATER.md` line, because both plans cite the same
grab — and the 13th agreement is a shared *negative* (both plans conclude no wade-depth member exists).
**No depth, speed or time value in the two plans conflicts.**

The single disagreement is not a threshold: A says the donor carries no water-entry splash and records it
as UNKNOWN; B says "keep donor" because the fleet has water-entry effects. The grab settles it for B —
the donor's own `.ee` ships `effects/jc_vehicles/traversal_water/boat_splash_jetski.effc` — while A's
narrower claim (no *water module* names a splash) is also true. That pair is §5.

The practical reading: the two plans are numerically compatible. They can be merged as-is on every
depth, speed and time value; only the splash paragraph needs rewriting, and A's is the one that
understates what ships.

**Labels.** **decoded** = a number read at the `WATER.md` / `FX_TABLE.jsonl` line quoted. **derived** =
arithmetic on decoded values, shown. **UNKNOWN** = absent from the grab, with the file that settles it.

---

## 1. Method

A row is one *(member, quantity)* pair. "Shared" means both plans state a value for the same member or
the same named quantity. Verdicts:

| verdict | meaning |
|---|---|
| **agree** | both plans state the same value for the same member/quantity |
| (no **disagree** rows) | every shared threshold agrees; the one disagreeing pair is the non-numeric splash claim in §5 |
| **disagree** | both state a value and the values differ |
| **A only** / **B only** | one plan states it; there is nothing to compare, and this is recorded so the inventory is complete |

Population: every number in either plan whose role is a **depth**, a **speed** or a **time** — including
the physical quantities that only *look* like them (hull radii/areas, entry timers, shut-down delays).
Excluded as out of class: forces and drag coefficients (`pressure_drag` 5000, `suction_drag` 5000,
`anti_penetration_multiplier` 2, `add_skin_friction_turbulent` 3), masses (975 / 25 / 75), suspension
rates (40 / 35), stiffness, inertia, counts (189 / 8 / 35 / 232, hull elements, water sensors) — those
appear in §4 as agreed context, not as thresholds.

Grab files consulted, both in-project: `Research/JC3Grab/WATER.md` (the source both plans cite) and
`Research/JC3Grab/FX_TABLE.jsonl` (the effect-binding table, used only for the splash question).

---

## 2. Depth thresholds

| # | member / quantity | A (water-crossing) | B (water-and-terrain) | grab line | verdict |
|---:|---|---|---|---|---|
| 1 | `WaterInteraction.depth_full_drag` | **0.1** (§2.2, line 58) | **0.1** (§2.2, "depth at which drag is full") | `WATER.md:58` `\| \`depth_full_drag\` \| float \| 233 \| 0 .. 0.2 (4 distinct) \| 0.1 \|` | **agree** |
| 2 | `depth_full_anti_penetration` | — (gives only `anti_penetration_multiplier` 2, line 63) | **0.1** (§2.2) | `WATER.md:64` donor 0.1 | **B only** |
| 3 | `Buoyancy.radius` | **0.55** (§2.1, line 35) | **0.55** (§2.2) | `WATER.md:35` donor `0.55 .. 0.55` | **agree** |
| 4 | `Buoyancy.side_area` | **1.85** (line 36) | **1.85** | `WATER.md:36` donor `1.85 .. 1.85` | **agree** |
| 5 | `Buoyancy.bottom_area` | **3** (line 37) | **3** | `WATER.md:37` donor `3 .. 3` | **agree** |
| 6 | **wade depth** (metres, where lift starts) | **no member exists** — "no number exists … WATER.md carries no metre figure for a waterline, wade depth or submersion limit" (§3) | stated nowhere; only the 0.1 drag depths above | `WATER.md:35-42` carries no metre waterline; both conclusions match | **agree** (both: no such member) |
| 7 | pilot-card water depths | **0.25 m** ford (W1), **0.3 m** puddle (W4), **0.4 m** (W5), "bumper depth" (W2), roof (W3) | — | n/a — test scenarios, not data | **A only** |

Rows 3–5 are hull geometry, not depth limits; they are included because both plans quote them as the
closest thing to a waterline and because they are identical. **No depth disagreement exists.**

---

## 3. Speed thresholds

| # | member / quantity | A | B | grab line | verdict |
|---:|---|---|---|---|---|
| 8 | `planing_vs_forward_speed_ms.x_max` | **20** m/s ("the only 'how fast before the hull lifts' data", line 67) | **x 0…20** (§2.2, 5 control points) | `WATER.md:67` `\| \`planing_vs_forward_speed_ms.x_max\` \| float \| 233 \| 20 .. 20 \| 20 \|` | **agree** |
| 9 | `Buoyancy.up_velocity_cap` | **20** (line 38) | **20** | `WATER.md:38` donor `20 .. 20` | **agree** |
| 10 | `reference_drag_speed_ms` | — | **20** | `WATER.md:57` donor 20 | **B only** |
| 11 | `flat_water_vs_speed_ms` | — | **x 0…30, y 0…1, 3 points; 1 → 0.3568 at 30** | `WATER.md:80-84` x_max donor 30, y_max 1, 3 points (the 0.3568 is from the entity grab, not WATER.md) | **B only** |
| 12 | `angular_drag_ref_speed_kmph` | — | **50** | `WATER.md:50` donor 50 | **B only** |
| 13 | `buoyancy_factor_vs_speed_ms.x_max` | — | **x 0…20, y 0…1, 2 points (flat 1)** | `WATER.md:72` donor 20 | **B only** |
| 14 | `vehicle_misc.official_top_speed` / `max_landing_speed_kmph` / `max_take_off_speed_kmph` | — | **250 / 170 / 150 km/h** | not in `WATER.md` (entity grab) | **B only** |
| 15 | `BattleModeMaxSpeed` (BmAK) | — | **1200 cm/s** | `Working/vendor/BmSDK/RVehicleSimBatmobile.g.cs:1200` | **B only** |
| 16 | pilot-card speeds | **30 km/h** (W1, W5, W6), **40 km/h** (W4), **60 km/h** brake (W7) | — | n/a — test scenarios | **A only** |

**No speed disagreement exists.** The only shared speed members (rows 8, 9) are identical.

---

## 4. Time thresholds

| # | member / quantity | A | B | grab line | verdict |
|---:|---|---:|---:|---|---|
| 17 | `car_common.engine_shut_down_delay_s` | **30** (line 230) | **30** | `WATER.md:230` `\| \`car_common.engine_shut_down_delay_s\` \| \`30\` x232 \|` | **agree** |
| 18 | `boat_common` / `helicopter_common` / `motorbike_common` / `plane_common.engine_shut_down_delay_s` | **5** each (229, 231-233) | **5** ("5 for every other class") | `WATER.md:229` `\| \`boat_common.engine_shut_down_delay_s\` \| \`5\` x232 \|` (+231-233) | **agree** |
| 19 | `vehicle_damage.min_water_entry_ms` | **10** (line 237) | **10** | `WATER.md:237` `10` x232 | **agree** |
| 20 | `vehicle_damage.fatal_water_entry_ms` | **20** (line 235) | **20** | `WATER.md:235` `\| \`vehicle_damage.fatal_water_entry_ms\` \| \`20\` x232 \|` | **agree** |
| 21 | `vehicle_damage.min_water_entry_floating_ms` | **20** (line 236) | **20** | `WATER.md:236` `20` x232 | **agree** |
| 22 | `vehicle_damage.fatal_water_entry_floating_ms` | **50** (line 234) | **50** | `WATER.md:234` `50` x232 | **agree** |
| 23 | pilot-card times | cut **5–35 s** (W2), destroyed **≤ 10 s** (W3), splash **≤ 0.2 s** / gone **≤ 1.5 s** (W4), **3 s** in water / wake gone **≤ 2 s** (W5), audio **≤ 0.5 s** (W6) | — | n/a — test scenarios | **A only** |

Both plans also carry the same unit caveat, from the same line — `WATER.md:239`:

> So the *kill* side is fleet-wide: `min_water_entry_ms` 10 and `fatal_water_entry_ms` 20, with the `_floating_` pair at 20 / 50, and the engine shut-down delay is 30 s for cars and 5 s for every other class. **No vehicle overrides any of them** … the unit behind the `_ms` suffix is not decoded here (`UNKNOWN`): 10/20 ms is too short to be a drown timer, so the name is the only evidence of what the numbers mean.

**No time disagreement exists.** All six shared timers agree to the digit.

---

## 5. The one disagreement: does the donor ship a water-entry splash?

### 5.1 What each plan says

**A** (§2.4, and its B3/B4/B5 rows) — the absence claim, with a citation:

> There is **no** member named splash, wake, spray, foam, ripple or entry-effect (265).
> … So a splash or a wake is not authored by any water module. What plausibly carries it is the
> per-vehicle effect graph (`SEffects` / `SAttachedEffect` objects, 359 + 5342 across the fleet) driven
> by the water collision sensor counts above (217-228). That is **UNKNOWN from WATER.md**; it settles in
> `Research/JC3Grab/FX.md` (the effect-table decode) and the donor's `.epe` effect objects.

and its B3 row: splash "**not copyable from a car** — no water module carries it".

**B** (§3.2) — the keep-it claim, with **no** citation on the row:

> | splash on entry | `SpawnWaterImpactEffect` analogue — the fleet's water entry effects | keep donor |

B's §2.2 preamble says only "Source: entity grab for the module rows; `Research/JC3Grab/WATER.md` §2,
§7 for the fleet ranges" — neither covers an effect file, so **the splash row is the one row in either
plan with no grab line behind it.**

### 5.2 Which value cites a grab, and what the grab says

A's clause cites `WATER.md:265`, and on its own terms it is correct:

> There is no `drown`, `submerge`, `flood`, `swim` or `underwater` path anywhere in the 232 entities, and no member that could make a hull dive and stay drivable: the only `dive_*` terms are `HelicopterModel` flight (`max_speed_dive_kmph`, `add_dive_pitch_deg`). A submerged vehicle is therefore whatever the engine does with `will_sink` plus the `vehicle_damage` timers -> `UNKNOWN`.

Also relevant, `WATER.md:254`, the scope of that scan — it is a scan of **member paths**, not of assets:

> 38 distinct member paths fleet-wide mention water/drown/sink/float/dive/submerge/buoyancy. Grouped by the module they live in:

So A proves "no *member* is called splash". It does not prove "the donor has no splash effect", and the
effect table says the opposite. `Research/JC3Grab/FX_TABLE.jsonl:27259`, the donor entity:

> `{"container":"editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.ee","source":"editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.ee","path":"effects/jc_vehicles/traversal_water/boat_splash_jetski.effc","ext":".effc","size":12527,"mount":"base","root":"EffectRTSystem","rows":1481,"arrays":183,"objects_digest":"1c14e81d056f8523","digest":"9c48817da964720efe72439e946c17a85f1b9bb5","types":36}`

with the three splash textures bound in the same `.ee` (`FX_TABLE.jsonl:27343-27345`,
`effects/textures/t_water_splash_01/02/03_alpha_dif.tga.*.trim`). The `debug` and `signature_preorder`
donor builds carry the same `boat_splash_jetski.effc` binding (`:27410`, `:27561`), so it is not a
one-build artefact.

**Verdict on the pair.** B's operational answer ("keep donor") is the one the grab supports; A's
statement is true only at the module level and its **B3 row** ("not copyable from a car", "settles in
FX.md") is wrong as an operational consequence — the effect is already in the donor `.ee` and ships with
the build. A also cites 359 + 5342 `SEffects`/`SAttachedEffect` objects as the plausible carrier, which
is consistent with this binding rather than in conflict with it. The two plans are one sentence apart:
A should say "no water *member*; the donor already binds `boat_splash_jetski.effc`", and B should cite
`FX_TABLE.jsonl:27259` on its splash row.

This is the only row in the comparison where a plan states a value with no grab line, and it is the row
that is wrong.

---

## 6. Secondary findings, stated as such

**S1 — Coverage asymmetry, not conflict.** B carries 10 thresholds A omits (rows 2, 10, 11, 12, 13, 14,
15) and A carries 10 test-band numbers B omits (rows 7, 16, 23). Where the members overlap, the values
are identical. A merge should take B's member inventory and A's pilot cards.

**S2 — Internal tension in A, not a cross-plan disagreement.** A's W3 expects destruction "within 10 s"
while A itself quotes `fatal_water_entry_ms` **20** with the unit UNKNOWN. If the unit were seconds, the
20 timer contradicts a 10 s band. B avoids this by carrying the 20/50 pair and the UNKNOWN unit with no
pilot band. Worth fixing in A's W3 wording, not in any number.

**S3 — Internal tension in A, minor.** A §3 states "no number exists" for a wade depth, then W1 tests a
**0.25 m** ford. The 0.25 m is a test scenario, not a data claim; no action needed beyond a word of
framing.

**S4 — Population denominators differ but do not conflict.** A counts **232** entities throughout; B
reports `wheels_friction_type` over **n=271** and `LandGlobal` rows. Different measurements (entity
census vs module census over a superset), and B never attaches its 271 to a water claim.

---

## 7. Agreed context (identical in both, for the record)

`will_sink` 1 · `buoyancy` 2 · `drag` 100 · hull 1 element from `sportsmuscle_body` ·
`angular_drag_pitch` 0.05 · `pressure_drag` 5000 · `suction_drag` 5000 · `anti_penetration_multiplier` 2 ·
fleet split 189 sink / 8 amphibious / 35 boats of 232 · `car_common` 30 s vs 5 s other classes ·
water timers 10 / 20 / 20 / 50 · `will_sink` is the only scalar separating sinkers from the amphibious
eight (`WATER.md:130`) · the build already carries the donor's water modules byte-identically
(`WATER.md` §8).

## 8. Limits

* Static reads only. Neither plan was modified; nothing was built, packed, installed or launched.
* `WATER.md` is the sole grab for rows 1–22 because it is the grab both plans cite; where a plan cites an
  **entity grab instead** (B's rows 11, 14, and the 0.3568 flat-water point), that file lives outside
  the repository at `E:/Modding/_gamedata/JC3grab/…` and was **not** read here. Those rows are `B only`,
  so no verdict depends on them.
* B's BmAK-side numbers (`SquealThreshold` 0.2, `DefaultTyreUpdates` 16.5, `SlopeTorqueScale` offset 64)
  are not depth/speed/time thresholds in water and are out of scope by §1.
* The splash verdict rests on one table (`FX_TABLE.jsonl`) plus `WATER.md`'s scan scope. It does not
  prove the effect *fires* in game — only that the donor `.ee` binds it, which is all "keep donor" needs.

## 9. Revert

Delete this file. Nothing else was created or changed.
