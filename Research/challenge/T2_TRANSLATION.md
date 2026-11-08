# Assumption challenge — `Working/Translation/T2_TRANSLATION.md`

Read-only challenge of the T-2 translation table. Target: `Working/Translation/T2_TRANSLATION.md`
(229 lines). Rules applied: `GRAB_BACKLOG.md` §0.5 (R4 = no value without provenance, R5 = behaviour
before member) and `Working/Translation/POSTMORTEM_DAMAGE.md` (§2, §8: a fleet median is not a
bridge, and a member whose name sounds right can carry the wrong behaviour).

Method: every claim below was re-derived from files on disk, never from another doc's summary,
using one read-only chaser, `Tools/scripts/chase/ch_t2_claims.py` (sub-commands `damage`, `lights`,
`parts`, `physics`, `audio`, `build`, `index`), plus the card's own checkers
(`python Tools/scripts/t2_lg2.py`, `python Tools/scripts/t22_collision.py --check`). No game was
launched; nothing was edited except this report; `D:/Games` was not read.

Classes: **assumed** (no source), **inferred** (source exists but the step is a judgement),
**name-only** (a member/class name stands in for a behaviour), **unsourced** (a number no file
produces). Verdicts: CONFIRMED / REFUTED / UNVERIFIABLE.

---

## C01 · "185 materials, 405 textures" — CONFIRMED

- **Where:** line 21 (section heading).
- **Claim:** the grab holds 185 materials and 405 textures.
- **Class:** unsourced as written (the heading gives no table).
- **Verdict:** **CONFIRMED.**
- **Evidence:** `Research/BatmobileGrab/grab.json` `classes` — `Material: 185`, `Texture2D: 401`,
  `TextureFlipBook: 4` → 405. `MODDING_PLAN.md:518` states the same pair from GRB-3. Note the grab
  also holds **130** `MaterialInstanceConstant`; the section's "13 material instances" (line 24) is
  `SLOTS.json`'s bodies-only count, not the grab's. Both are true, but the two numbers are different
  scopes under one word.

## C02 · "28 Batmobile textures shipped" — CONFIRMED (documented), UNVERIFIABLE from the build tree

- **Where:** lines 34 (T-MA2) and 38 (T-MA6).
- **Claim:** 28 of the 405 grabbed textures are shipped; 38 slots-bound textures exist in BmAK.
- **Class:** inferred (the selection rule "by slot binding" is never applied to the 405).
- **Verdict:** **CONFIRMED** as a build fact, **UNVERIFIABLE** as a re-derivable count.
- **Evidence:** `MODDING_PLAN.md:87` ("28 textures converted (BC1/BC5/BC3)"), `MODDING_PLAN.md:528`
  (DEP-1: "aafdiff 28 added", `verify_install.py` "28/28 textures used and internal in the `.toc`"),
  `SLOTS.json` `summary.textures = 38`. On disk `Builds/test-091/.../textures/batmobile/` holds
  **42** `.ddsc` — the 28 converted plus 13 `solid_<rrggbb>` palette placeholders, `nimbus_power_cell_n`
  and `stagg_battery_01_d/n` — so the 28 cannot be recounted from the tree without the conversion
  manifest. `t2_facts.py` prints 38 (BmAK side) and never prints 28.
- **Secondary (R4):** "any of the 377 unshipped are decals/Jokerfied/other packages — no row" (line 38)
  is an **assumed** classification: no file lists those 377 or their reason. The subtraction
  405 − 28 = 377 is arithmetic; the *why* is not filed.

## C03 · T-MA3 "linear → sRGB, gain 3.4476" — REFUTED

- **Where:** line 35 (T-MA3), transform and "now" cells.
- **Claim:** base colour `[0.02579, 0.02579, 0.03]` goes to `[0.056738, 0.05158, 0.06]` by an
  sRGB conversion with gain 3.4476, giving "albedo byte 0x83/0x7d/0x86".
- **Class:** derived — and derived from the wrong constant.
- **Verdict:** **REFUTED** (the three numbers in the cell are inconsistent with each other).
- **Evidence:** `Research/BatmobileGrab/VALUES.json`:
  - `paint.effective_base_colour = [0.056738, 0.05158, 0.06]`,
  - `paint.albedo_gain = 3.4476`, sourced as *"vanilla paint tint luma 0.1837 / BmAK authored paint
    luma 0.0533 (GRB-6)"* — a **luma ratio between two palettes**, not a per-channel multiplier,
  - `paint.base_colour` source: *"Material0_BaseColour … × Diffuse_Adjust [2.2, 2.0, 2.0]"*.
  Arithmetic: `0.02579 × 3.4476 = 0.0889` ≠ 0.056738; `0.02579 × 2.2 = 0.056738` and
  `0.02579 × 2.0 = 0.05158` and `0.03 × 2.0 = 0.06` — every effective channel is the **Diffuse_Adjust**
  product. The gain 3.4476 plays no part in the cell it is quoted in.
  The parenthetical is worse: byte `0x83 = 131/255 = 0.5137` sRGB ≈ 0.226 linear, not 0.0567; 0.0567
  sRGB-encoded is byte `0x3E`. `0x83/0x7d/0x86` is the **RBM albedo byte** documented in
  `MODDING_PLAN.md:56` (linear ×4), a different quantity again.
- **Fix:** state the transform as `× Diffuse_Adjust [2.2, 2.0, 2.0]`, drop the gain from this cell,
  and put the albedo bytes in their own cell with their own source.

## C04 · T-MA4 "vanilla caps paint gloss at 0.4" — REFUTED (name-only reading of a value)

- **Where:** line 36 (T-MA4), BmAK and transform cells; contradicted by the prose at lines 41-44.
- **Claim:** the game caps `CarPaintMM` gloss at 0.4, so 0.6 → clamp to 0.4 → raise to 0.45.
- **Class:** **name-only / inferred** — a single vanilla material value read as an engine ceiling.
- **Verdict:** **REFUTED.**
- **Evidence:** `VALUES.json` `paint.gloss_cap` source: *"vanilla paint channel 1 of
  `sportsmuscle_body_lod1.rbm` block 6 (0.400)"* — that is **the donor mesh's authored gloss in one
  block**, not a cap. The document's own fleet check (line 41) says
  `Palette.tints[].specular_gloss` is **0 … 1, median 1** over 3,602 tints; re-derived here:
  3,602 values, min 0, max 1, median 1, with 2,303 at exactly 1.0 and only 144 at 0.4. A value the
  fleet exceeds 20× cannot be a cap, so "clamp to the vanilla cap" describes a choice as a constraint.
  The same paragraph also reports the donor's 0.45 in 319 tints fleet-wide, i.e. 0.45 is a shipped
  value, not an edited outlier.
- **Fix:** rename the transform to "match the donor block's 0.4, then raise" and mark it `derived`
  from a taste decision (it is the one row the doc admits overrules the fleet; say so in the cell).

## C05 · T-MA7 "`Palette` does not exist in UE3 vehicles" — UNVERIFIABLE

- **Where:** line 39 (T-MA7), BmAK cell.
- **Claim:** the BmAK vehicle has no palette concept.
- **Class:** **assumed** (argument from absence in a grab).
- **Verdict:** **UNVERIFIABLE.**
- **Evidence:** `Research/BatmobileGrab/MATERIALS.md` / `grab.json` hold `Material`,
  `MaterialInstanceConstant` and 864 scalar / 379 vector material parameters — a repaint system in
  UE3 *could* be built from those, and nothing on disk enumerates whether BmAK has a paint menu. What
  is verifiable is narrower and already proven: the **JC3** `Palette` module has 10 tints in the build
  (`Working/Translation/current.json`, `Palette.tints[0..9]`, all `specular_gloss` 0.449999988,
  `clear_coat` 1, `metallic` 1) and T-MA7's "leave it" needs no BmAK statement to stand.
- **Fix:** claim only what is known — "BmAK's paint channels are material parameters; no palette
  class was found in the grab" — and drop the universal negative.

## C06 · "40 `CPartProp` … agree 40/40 with the 42-row parts module" — CONFIRMED

- **Where:** lines 51-58 (section 2 prose), and the assessment it feeds.
- **Claim:** the vanilla donor's `.epe` names 40 parts and the decoded parts module has 42 rows, the
  extras being `hood_signature` and `missile_base_signature`.
- **Class:** decoded.
- **Verdict:** **CONFIRMED.**
- **Evidence:** `E:/Modding/_JC3grab/detail/v0300_car_kensington_sportsmuscle__…_civilian_01.ee.json`
  → `epe.objects`, class counts: **`CPartProp` 40**, `SVehicleLight` 22, `SAttachedEffect` 27.
  `Research/JC3Grab/PARTS_TABLE.jsonl` (donor row, `parts`): 42 rows. Name sets: intersection **40**,
  graph-only **0**, table-only **{`sportsmuscle_hood_signature`, `sportsmuscle_missile_base_signature`}**
  — exactly the two the document names. Fleet context from the same source: 11,041 `CPartProp` across
  the 232 graphs.

## C07 · T-PA1 "6 `CPartProp` in the built `.epe` … measured by `t2_lg2.py`" — UNVERIFIABLE

- **Where:** line 60 (T-PA1), "now" and "verify" cells.
- **Claim:** the built entity's graph holds 6 `CPartProp` (body, `taillight_r_l`, four wheels) and
  `Tools/scripts/t2_lg2.py` measured it.
- **Class:** unsourced number; the verify cell names a tool that cannot produce it.
- **Verdict:** **UNVERIFIABLE.**
- **Evidence:** `Tools/scripts/t2_lg2.py`'s docstring and code handle **`SVehicleLight` only**
  (`grep -n "CPartProp" t2_lg2.py` → no match); running it prints light rows/objects, never parts.
  No json carries "6 `CPartProp`". `MODDING_PLAN.md:57` records the same entity as **7 parts
  (body, 4 wheels, 2 doors)** while T-PA1 says 6 (`body, taillight_r_l, 4 wheels`) — the two
  descriptions disagree on which parts exist, and neither is produced by a command.
- **Fix:** measure the built graph with a checker that reads it (the same `jc3detail` path
  `t2_lg2.py` already uses) and put that command in the verify cell, or write `UNKNOWN`.

## C08 · T-PA2 "21 light points → 12 parts" — CONFIRMED

- **Where:** line 61 (T-PA2).
- **Claim:** `DeformPoints.light_indices` holds 21 entries naming 12 parts.
- **Class:** decoded.
- **Verdict:** **CONFIRMED** (with one wording caveat).
- **Evidence:** donor `DeformPoints` module: `light_indices[0..20]` → **21** rows.
  `PARTS_TABLE.jsonl` donor row: exactly **12** parts carry the lights flag —
  `sportsmuscle_body`, `taillight_r_l`, `taillight_r_r`, `taillight_r_c`, `signal_r_l`, `signal_r_r`,
  `headlight_f_l_01`, `headlight_f_l_02`, `headlight_f_r_01`, `headlight_f_r_02`,
  `signal_f_l`, `signal_f_r`. That is 12, but the parenthetical ("body ×2, both front lamps ×2 each,
  tail lamps, signals") describes the *points*, not the parts; the parts list above is the file's.
- **Note:** the module's `lights` flag is what the parts table exposes; the mapping point → part is
  `from_part_index`, so "→ 12 parts" is the count of distinct flag-1 parts, not of `from_part_index`
  values. Both give 12 here; the doc does not say which it used.

## C09 · T-PA4 wheels → slots / spokes / spins — CONFIRMED

- **Where:** line 63 (T-PA4).
- **Claim:** parts 11, 12, 26, 27 map to slots 3, 2, 0, 1 with 1 spoke and `spins = 1`.
- **Verdict:** **CONFIRMED.**
- **Evidence:** `PARTS_TABLE.jsonl` donor `wheels` = `[{part 11, slot 3, spokes 1, spins 1},
  {part 12, slot 2, spokes 1, spins 1}, {part 26, slot 0, spokes 1, spins 1},
  {part 27, slot 1, spokes 1, spins 1}]` — identical, in the same order.

## C10 · T-PA6 11 constraints and T-PA7 20 non-deformable parts — CONFIRMED

- **Where:** lines 65-66.
- **Claim:** `constraint_indices` has 11 points naming 11 parts; `non_deformable_parts_indices`
  skips 20 parts.
- **Verdict:** **CONFIRMED** (first number; the "11 parts" half is an inference, see below).
- **Evidence:** donor `DeformPoints`: `constraint_indices[0..10]` → **11** rows;
  `non_deformable_parts_indices[0..19]` → **20** rows. The document's "11 points → 11 parts" assumes
  eleven distinct part indices; the file gives eleven *indices*, and nothing on disk states they are
  distinct. Cheap to close: the distinct count is one `len(set(...))` away.

## C11 · "101 entries over 4 packages … Per rig that is 28 entries" — REFUTED (one rig has 17)

- **Where:** lines 76-82 (section 3 prose) and the T-LG1 row (line 86, "28 entries/rig, 4 rigs").
- **Claim:** the 101 BmAK lights are 28 per rig across four rigs.
- **Class:** unsourced rounding.
- **Verdict:** **REFUTED** as arithmetic; the 101 itself is right.
- **Evidence:** `Research/BatmobileGrab/LIGHTS.json` `vehicles` (list of 4): **28, 17, 28, 28**
  = 101 (`Playable_BatmobileFunhouse_SF` 28, **`Playable_BatmobileJoker_SF` 17**,
  `Playable_BatmobileMK2_SF` 28, `Playable_Batmobile_SF` 28). `MECHANICS.md`'s "Light rig (28 entries)"
  line is about the three full rigs. 28 × 4 = 112 ≠ 101, so "28 entries/rig" cannot describe all four.
- **Fix:** "28 entries on three rigs, 17 on the Joker rig (101 in total)".

## C12 · T-LG2 "21 rows / 22 objects … 20 resolve, 0xc832d6e0, 2 unused objects" — CONFIRMED

- **Where:** line 87 (T-LG2).
- **Claim:** the build's light module has 21 rows against the donor graph's 22 `SVehicleLight`
  objects; 20 preset ids resolve, one (`0xc832d6e0`) does not exist in the graph, and two objects
  (`Front_Secondary_Head`, `Rear_Break`) are referenced by no row — both counts already differ
  inside the vanilla entity.
- **Class:** decoded.
- **Verdict:** **CONFIRMED** by the card's own checker.
- **Evidence:** `python Tools/scripts/t2_lg2.py` →
  `build rows 21 objects 22 matched 20 unused-objects 2 presets-not-in-graph 1` /
  `vanilla rows 21 objects 22 matched 20 unused-objects 2 presets-not-in-graph 1` /
  `row presets the graph does not instantiate: ['0xc832d6e0']` /
  `graph objects no row references: ['Front_Secondary_Head', 'Rear_Break']` /
  `check ok: the build's rig is the donor's, row for row`. Independent count from the detail cache:
  `SVehicleLight` = 22; 3,972 fleet-wide.

## C13 · T-LG3 "6 headlight-class entries per rig (2 primary + 4 flares/BattleMode/Forensics)" — REFUTED

- **Where:** line 88 (T-LG3), BmAK cell.
- **Claim:** six headlight-class entries per rig, of which two are primary heads.
- **Class:** **name-only / unsourced**: the counts are not in `LIGHTS.json`.
- **Verdict:** **REFUTED.**
- **Evidence:** `LIGHTS.json` `vehicles` — `VEHLT_HeadLight` per rig is **14** on the Funhouse, MK2 and
  SF rigs and **4** on the Joker rig (46 total, which the same file's `summary.by_type` prints);
  `VEHLT_BattleModeLight` 4 per rig, `VEHLT_ForensicsLight` 3. Neither 6 nor "2 primary" appears
  anywhere in the file. The evaluative half of the row ("2 primary + 1 secondary spot" in JC3, "5
  spot rows") is separately true (C14), so only the BmAK column is wrong.
- **Fix:** print the per-rig type counts the json already has instead of a rounded "6".

## C14 · Section 3's build numbers (21 lights, 10/5/2/2/2, 5 spots, 16 stubs, 12/9 multipliers) — CONFIRMED

- **Where:** lines 83-85.
- **Verdict:** **CONFIRMED** from `Working/Translation/current.json` (build **test-091**).
- **Evidence:** `VehicleDynamicLights.lights[0..20]` → 21 rows. `behavior`: HeadLight 10, TailLight 5,
  LeftSignal 2, RightSignal 2, Reverse 2. `range`: 30 ×5 and 2 ×16; `angle`: 40 ×5 and 10 ×16;
  `multiplier`: 2 ×12 and 1 ×9. `T2_FACTS.md` prints the same 21-row table (values identical).
  Caveat for the doc: `current.json` now points at **test-091**, while the row cells say "now (083)".

## C15 · T-LG6 "30 is inside the fleet band, 40 is the fleet max" — CONFIRMED

- **Where:** line 91 (T-LG6).
- **Verdict:** **CONFIRMED.**
- **Evidence:** re-derived from the entity cache, 3,217 light rows: `range` min 0.100000001, max 50,
  median 10; `angle` min 10, max 50, median 10; `multiplier` 0.3 … 5, median 1. Same as
  `T2_FACTS.md`'s VOCABULARY quotes. 30 lies inside `range`, and 40 equals the `angle` maximum.
- **Provenance note (R4):** the row's confidence is `class`, but the two values are the donor's
  (`range` 30 / `angle` 40 on five rows), i.e. `decoded`, not a fleet-class choice.

## C16 · T-AU2 "210,781,376 B bank installed" — UNVERIFIABLE (the number is the archive's size)

- **Where:** line 108 (T-AU2), "now" cell.
- **Claim:** a 210,781,376-byte `vehicles.bank` is installed.
- **Class:** unsourced for "installed"; the size itself is decoded.
- **Verdict:** **UNVERIFIABLE.**
- **Evidence:** the size is the **archive entry**:
  `Research/JC3Grab/INDEX.jsonl` → `{"path":"sound/fmod_banks/vehicles.bank","archive":"patch_win64/game5","size":210781376}`,
  repeated in `Research/JC3Grab/JC3_AUDIO.md:32` and `JC3_AUDIO_EVENTS.json:910`. No `vehicles.bank`
  exists under `E:/Modding/_JC3grab` (`find` → only `audio/weapons.bank`), and the dropzone
  (`D:/Games`) was not read in this challenge. `MODDING_PLAN.md:54` records the swap as a dropzone
  extra file of that size, which is the only support for "installed".
- **Fix:** cite the dropzone path or `verify_install`-style read; otherwise "vanilla bank is
  210,781,376 B in the patch archive; the dropzone copy was swapped in test-060".

## C17 · T-AU4 "LandAudio 10000 vs engine 7300 → 4,500" — CONFIRMED

- **Where:** line 110 (T-AU4).
- **Class:** decoded + derived.
- **Verdict:** **CONFIRMED.**
- **Evidence:** donor `LandAudio` module = `{min_rpm: 1000, max_rpm: 10000}` (2 members, matching
  T-AU1); donor `LandEngine.max_rpm` = **7300**. `T1_TRANSLATION.md:137` (T-E1) proposes
  `800 / 2800 / 4500`, so "4,500 with T-1 T-E1" is the row it claims. The build has caught up:
  `current.json` (test-091) `LandAudio.max_rpm` = **4500**, i.e. the "now" cell describes 083, not 091.

## C18 · Section 4's audio census (27 banks, 34.4 MB, 361 rows, 118 ids, 239 resolved, 447 media, 90/26 missing) — CONFIRMED

- **Where:** lines 94-100.
- **Verdict:** **CONFIRMED.**
- **Evidence:** `Research/BatmobileGrab/AUDIO_MAP.json` `summary`: `rows 361`, `unique_event_ids 118`,
  `resolved_rows 239`, `resolved_ids 74`, `missing_rows 90`, `missing_ids 26`, `media 447`,
  `media_bytes 18176431`, `bytes 34409121`, `banks 27`, and `missing_banks` = exactly the ten names
  the document lists (order differs: `OBJ_Rolling_Objects` is last in the json).
- **Caveat (R4):** "missing **because** 10 banks are not shipped" is a causal reading; the json shows
  the 90 rows reference 10 absent banks, which is strong but is still an inference, not a field.

## C19 · Section 5's effect numbers (51 rows, 51 deform points, 29 parts, 1 usage, 11 names) — CONFIRMED

- **Where:** lines 116-122.
- **Verdict:** **CONFIRMED.**
- **Evidence:** `current.json` `EffectAttachments` (test-091): `all_effects[0..50]` → **51** rows,
  **51** distinct `deform_point.string` values, `part_effects[0..28]` → **29**, and exactly one
  `usage_effects[0].usage.string` = `HeadLights`. Distinct effects: `burn_base` 1, `burn_engine` 1,
  `burn_roof` 1, `dynamic_headlight` 4, `electric_break` 8, `large_break` 6, `medium_break` 8,
  `small_break` 8, `taillight_break` 4, `window_break` 6, `window_break_sm` 4 = **11** names, 51 rows.

## C20 · T-DM1 "all land 500…2,000, median 700; 6 t p75; 6 t+ median 1,600" — REFUTED in two numbers

- **Where:** line 145 (T-DM1), "proposed" cell.
- **Claim:** every land vehicle's `max_health` lies in 500…2,000 with median 700; the 6 t+ median is
  1,600 and "the 6 t p75" justifies 2,000.
- **Class:** derived (fleet), with the mass grouping unstated.
- **Verdict:** **REFUTED** on the low bound and on 1,600; the 2,000 (p75) and the median 700 are right.
- **Evidence:** re-derived over 232 entities (`ch_t2_claims.py damage`): distinct
  `max_health` values are 500, 700, 1400, 1500, 1800, 2000, 4000. The 500s are **19 bikes**
  (`v3000_bike_*`); every entity that is a car/truck/tank by name has **700 … 2000, median 700** —
  so "all land 500…2,000" borrows the bike minimum. The 4000s are 3 `v1202_boat_capstone_corvette`
  builds, so "the land-vehicle maximum 2,000" is right. Joining `RigidBody.mass` (donor 975 kg) to
  `max_health`: mass ≥ 6,000 kg → 76 entities, **median 1,500**, p75 **2,000**; no mass threshold
  ≥ 3,000 kg yields a median of 1,600 (3,000 → 1400; 4,000/5,000/6,000/7,000/10,000 → 1500).
- **Fix:** "all land 700…2,000 (median 700; 6 t+ median 1,500, p75 2,000; bikes 500)".

## C21 · T-DM2 "99 is the fleet maximum; 100 is one above every shipped vehicle" — CONFIRMED

- **Where:** line 146 (T-DM2).
- **Class:** decoded (fleet).
- **Verdict:** **CONFIRMED.**
- **Evidence:** `bullet_armor_strength` over 232 entities: min 0, **max 99**, median 0, with 18
  entities at 99 — no shipped vehicle has 100. `T2_FACTS.md` quotes the same VOCABULARY range
  (0..99, n=233). Note that `current.json` (test-091) already carries **99**, so the row's "now = 100"
  is a build-083 statement; `POSTMORTEM_DAMAGE.md` §3 lists 100 under a *different* range quote
  (0…100) in its own table, which is where the "at the maximum" wording there comes from.

## C22 · T-DM4 "all three thresholds are at the fleet maximum (med 1000 / 250 / 100)" — CONFIRMED

- **Where:** line 148 (T-DM4).
- **Verdict:** **CONFIRMED.**
- **Evidence:** 232 entities: `explosion_threshold` 500…4000, median 1000 (build 4000 = max, 67
  entities at max); `smoke_threshold` 200…1050, median 250 (build 1050 = max, 12 at max);
  `burn_threshold` 50…250, median 100 (build 250 = max, 78 at max).

## C23 · T-DM5 "24 types … `c_mirror` uses `Boat_Antenna`, which is not in the table and falls back to `Default`" — REFUTED in part

- **Where:** line 149 (T-DM5).
- **Claim:** the damage type table is 24 types; the part table gives 17 distinct types; `c_mirror`'s
  type is not in the table, so it falls back to `Default`.
- **Class:** decoded for the counts, **inferred** for the fallback (engine behaviour from a name).
- **Verdict:** **REFUTED** for "the table" (fleet-wide there are 79) and for the fallback as a fact;
  the 24-entry *build* table and the 17-part count are right.
- **Evidence:** `part_damage_types` in the build has **24** entries (`T2_FACTS.md`, `current.json`).
  Fleet-wide the per-vehicle tables declare **79 distinct strings** (`ch_t2_claims.py damage`) —
  24 `Land_*` on 145 entities, 15 `Boat_*` on 35, 13 `Heli_*` on 23, 15 `Plane_*` on 18,
  12 `Train_*` on 12 — and **`Boat_Antenna` is declared by all 35 boat entities**, so the type is in
  the game's table, just not in the land table the donor carries. Donor parts: 42 rows, **17**
  distinct `dt`, with `sportsmuscle_c_mirror → Boat_Antenna` and the two `*_mirror` parts →
  `Land_Wing_Mirror`.
- **Fix:** "`Boat_Antenna` is not in the land table this vehicle carries; whether the engine then
  applies `Default` is UNKNOWN (the miss is real, the fallback is not decoded)".

## C24 · T-DM6 "all 156 land vehicles ship 1" — REFUTED (number) and in conflict with the postmortem decision

- **Where:** line 150 (T-DM6), and the header (line 4: the queued change).
- **Claim:** `deform_scale` is 0 in the build, every land vehicle ships 1, so the build is the only
  one at 0; the next build should carry 0 → 1.
- **Class:** derived (fleet), but the denominator is wrong.
- **Verdict:** **REFUTED** on 156; the qualitative claim (build 0, land fleet 1) is true, and the
  **action** contradicts a written decision.
- **Evidence:** `deform_scale` over 232 entities: **1 on 197 and 2 on 35** — the 2s are exactly the
  35 boats. Every name-classified land entity (125) ships 1, and so do 19 bikes, 23 helicopters,
  19 planes and 12 trains. **156 appears in none of these counts** (125 land / 197 at 1 / 232 total).
  `POSTMORTEM_DAMAGE.md` §3 prints the shipped range as **1 … 2** and §9 resolves
  **"T-DM6 → `keep` (`deform_scale` 0, declared cosmetic switch: no crumple)"** — the opposite of
  this row's 0 → 1. `current.json` (test-091) still reads `deform_scale: 0`, so no build has carried
  the change yet, but the ledger and the postmortem disagree on what should happen.
- **Fix:** decide the behaviour first (R5: "no crumple" was a deliberate switch) and state it; then
  write "197 of 232 ship 1, the 35 at 2 are all boats, land 125/125 at 1".

## C25 · Section 7's BmAK collision numbers (32/pkg, 128 boxes, 0 spheres, largest box, 30.3 cm root) — CONFIRMED

- **Where:** lines 160-166.
- **Verdict:** **CONFIRMED**, with one ambiguity.
- **Evidence:** `Research/BatmobileGrab/PHYSICS.json`, four packages × 32 `RB_BodySetup` bodies, all
  `boxes: 1`, `spheres: 0`; root body `Root` extents `[30.3, 30.3, 30.3]`. Largest box by **volume**
  = `[316.155, 63.418, 109.881]` (the document's 316.15 × 63.42 × 109.88); largest by **max axis** =
  `[317.942, 64.552, 97.966]`, which is what `T2_FACTS.md` quotes. The document does not say which
  criterion it used, so a reader comparing it with T2_FACTS sees a mismatch that is not one.

## C26 · T-CO2 / T-CO3 — CONFIRMED

- **Where:** lines 168-169.
- **Verdict:** **CONFIRMED.**
- **Evidence:** `python Tools/scripts/t22_collision.py --check` →
  `PASS: 32 BmAK bodies | 7 mapped / 21 unmapped | 54 donor hull slots, one per part | 38/42 parts collide | rows 3 (next 2, keep 1) | stations unchanged`.
  Donor parts: 42 rows, `world_collision_body_id = -1` on exactly the **4 wheels** (11, 12, 26, 27)
  → 38/42 collide. The 3.679 m hull axis is documented in `MODLOG.md:13697`
  ("box 2.085 x 1.212 x 3.679 m, r 0.01"), so "fits one donor hull" is supported.
- **Note:** the row's verify cell says `t22_collision.py --check` while `t_rows.py:121` points at
  `t16_collision.json`; only `t22_collision.py` exists, so the ledger's tool name is stale.

## C27 · Section 8's fleet counts (300 `SWeaponPoint`, 5,796 `CCameraModifier`, 4,477 `CCameraTransition`, 5,535 interaction entries) — CONFIRMED

- **Where:** lines 174-184.
- **Verdict:** **CONFIRMED.**
- **Evidence:** direct count over the 232 detail graphs: `SWeaponPoint` 300, `CCameraModifier` 5796,
  `CCameraTransition` 4477, `CInteractionGraphEntry` 5535 (all `CInteractionGraph*` classes
  together: 41,102 over 21). The "no JC3 car fires missiles from a turret" sentence is a
  **name-only** generalisation about behaviour, and should stay marked as a design decision.

---

## Tally

| verdict | claims |
|---|---|
| CONFIRMED | C01 C02(as documented) C06 C08 C09 C10 C12 C14 C15 C17 C18 C19 C21 C22 C25 C26 C27 |
| REFUTED | C03 C04 C11 C13 C20 C23 C24 |
| UNVERIFIABLE | C05 C07 C16 |

What the refutations have in common: four of the seven (C11, C13, C20, C24) are **fleet counts with
the wrong denominator** — a per-rig figure applied to four rigs, a rounded headlight count, a bike
minimum quoted as the land minimum, and "156 land vehicles" for a fleet that has 125 land builds
(197 of 232 at that value). C03 mis-attributes one cell's gain constant, C04 turns the donor mesh's
single authored value into an engine cap, and C23/C24 present engine behaviour ("falls back to
`Default`", "0 is a defect") that no file states — exactly the R4/R5 failure mode
`POSTMORTEM_DAMAGE.md` §8 records for T-DM7.

Two of the corrections matter to a build decision rather than to prose:

1. **T-DM6 is contested.** This document queues `deform_scale 0 → 1`; `POSTMORTEM_DAMAGE.md` §9
   resolved the same row to `keep` 0 as a declared cosmetic switch. One of the two is wrong and the
   ledger cannot tell which, because both cite "the fleet" — with different denominators (156 vs the
   measured 197/232, land 125/125).
2. **T-DM1's 6 t+ median is 1,500, not 1,600** (p75 2,000, which does support the proposed 2,000);
   the proposal survives, its stated reason needs the corrected number.

Claims not chased (no artefact on disk to chase them with): T-MA1/T-MA5's block and glass details
(documented in `MODDING_PLAN.md`/MODLOG §107, not re-decoded here), T-DM1's BmAK `Health` = 1,200
(G1h's grab), T-AU1's two-member `LandAudio` (confirmed twice incidentally, C17), and the BmAK
weapon/turret sentences in §8.

## How to re-run this

```
python Tools/scripts/chase/ch_t2_claims.py damage    # C20-C24
python Tools/scripts/chase/ch_t2_claims.py lights    # C11, C13, C15
python Tools/scripts/chase/ch_t2_claims.py parts     # C06-C10
python Tools/scripts/chase/ch_t2_claims.py physics   # C25
python Tools/scripts/chase/ch_t2_claims.py audio     # C16-C18
python Tools/scripts/chase/ch_t2_claims.py build     # C14, C19
python Tools/scripts/t2_lg2.py                       # C12
python Tools/scripts/t22_collision.py --check        # C26
```

Read-only throughout: the chaser writes nothing, opens no archive and never touches `D:/Games`; this
report is the only file it was used to produce. No game was launched, nothing was committed.
