# Audit — `collision-impact-effects-plan.md` and `mode-switch-carriers.md` against their primary files

**Targets:** `tmp/freebuff/reports/collision-impact-effects-plan.md` (C) and
`tmp/freebuff/reports/mode-switch-carriers.md` (M). The operator paths `reports/…` do not exist; both
live under `tmp/freebuff/`. Neither report was edited — revert = delete this file.

**Method:** every decoded value, offset, count and carrier name was looked up in the file the report
cites, and where the citation is a census the count was recomputed by grep over that census.
**Verdicts:** VERIFIED = the source says exactly that; OVERSTATED = the number/claim is larger or
stronger than the source; UNSUPPORTED = the cited file does not carry it (it may exist elsewhere —
said so when it does); MIS-CITED = right fact, wrong file; UNDERSTATED = the source has more than the
report shows.

---

## 1. Counts at a glance (the numbers most likely to drift)

| # | count claim | report | recalculated | verdict |
|---|---|---|---:|---|
| 1 | `Impact_Body_UPGR` emitters | **39** (C §2.1) | **13** (`PARTICLES.md:125`) | **OVERSTATED ×3.0** |
| 2 | `Impact_Full_UPGR` emitters | **42** | **15** (`PARTICLES.md:126`) | **OVERSTATED ×2.8** |
| 3 | `Impact_Head_UPGR` emitters | **33** | **13** (`PARTICLES.md:127`) | **OVERSTATED ×2.5** |
| 4 | `Batmobile_HeavyCannon_Impact_Px` emitters | 11 | 11 (`PARTICLES.md:107`) | VERIFIED |
| 5 | particle systems / emitters | 206 / 1,433 | 206 / 1,433 (`PARTICLES.md:12-14`) | VERIFIED |
| 6 | `part_impact` entities | 168 | 168 (`USAGES.md:227`) | VERIFIED |
| 7 | `chassis_impact` entities | 41 (+19) | 41 at `2963579072`, 19 at `1770819418` (`USAGES.md:329,274`) | VERIFIED |
| 8 | `chassis_impact_vfx` / `_default_sfx` | 171 / 128 | 171 / 128, same hash `2963579072` (`:329`) | VERIFIED |
| 9 | `chassis_undercarriage_impact` | 180 | 180 (`:290`) | VERIFIED |
| 10 | `chassis_sliding` | 214 (+19) | 214 at `2303147823`, 19 at `3370375413` (`:297,344`) | VERIFIED |
| 11 | `chassis_undercarriage_slide_sfx` | 159 | 159 (`:328`) | VERIFIED |
| 12 | `wheel_suspension_car_materials` / `landing_wheel_impact_sound` | 101 / 41 | 101 / 41 (`:340`) | VERIFIED |
| 13 | `wheel_suspension_bottom_out_materials` / `_sound` | 107 / 6 | 107 / 6 (`:362`) | VERIFIED |
| 14 | effect-table objects | 1,212 / 1,678 | 1,212 / 1,678 (`USAGES.md:209`) | VERIFIED |
| 15 | `chassis_impact_default` rows / types | 2,669 / 36 | rows **2,669** (`FX_TABLE.jsonl`); `types` not reproduced | rows VERIFIED, types **UNVERIFIED** |
| 16 | BmAK `BattleMode*` declared / serialised | 42 / 15 | 42 / 15 (`MODES.md:36`) | VERIFIED |
| 17 | `TurnOnSpot*` / `Transformation*` | 4/3, 9/4 | 4/3, 9/4 (`MODES.md:38,40`) | VERIFIED |
| 18 | fields with no value | 61 | 61 (`MODES.md:15,334`) | VERIFIED |
| 19 | JC3 module types / vocabulary rows | 52 / 1,421 | 52 sections / 1,421 rows (`VOCABULARY.md`) | VERIFIED |
| 20 | JC3 part behaviours | **66** | **67** (`FEATURE_CENSUS.md:34`) | **MISMATCH (off by one)** |
| 21 | `all_hinged_part_properties` rows | 25 | 25 strings (`VOCABULARY.md:1359`) | VERIFIED |
| 22 | `ExtendedExposedVariables` expressions | 2 | 2 (`VOCABULARY.md:616`) | VERIFIED |
| 23 | `DriverLean` fleet n | 23 | 23 (`VOCABULARY.md:566`), but **18 bikes + 5 boats, 0 aircraft** (`card-T-10.md:58`) | count VERIFIED, **"aircraft" OVERSTATED** |
| 24 | mode/transform hits in the vocabulary | **42** (M §2.7) | not reproducible — no regex or script named | **UNSUPPORTED** |
| 25 | `Fins.effective_in_air` = 1 anywhere | 0 of 200 | 0..0, n=200 (`VOCABULARY.md:625`) | VERIFIED |

---

## 2. Collision plan — statement by statement

| # | statement | cited source | what the source says | verdict |
|---|---|---|---|---:|
| C1 | `ImpactSparks` 0x0144 / 4708 = `Engine.Batmobile_Impact_02` | `CLASS_DEFAULTS.md` (plan §2) | row 35: `0x0144` / 4708, same object (`:115`) | **VERIFIED** |
| C2 | `SpinningSpikesImpactFX` 0x014c / 4812 = `SpikeAsset_Impact_P` | same | row 36 identical (`:116`) | **VERIFIED** |
| C3 | `SpinningSpikesImpactSound` 0x0154 / 4820 = `…Spike_Hit_Batmobile_CODE` | same | row 37 identical (`:117`) | **VERIFIED** |
| C4 | `CollisionFFWaveForm` 0x019c / 5596 | same | row 46 identical (`:126`); a **CDO** copy also exists at 0x00cc / 5596 (`:204`) which the report omits | VERIFIED (incomplete) |
| C5 | `WallScrapeSparksSystemR/L` 0x020c / 5868, 0x0214 / 5876 | same | rows 60-61 identical (`:140-141`) | **VERIFIED** |
| C6 | CDO scrape offsets 0x013c, 0x0144 | same | rows 40-41 identical (`:218-219`) | **VERIFIED** |
| C7 | `JumpLandSparksEffectL/R` 0x007c / 4716, 0x0084 / 4724 | same | rows 16-17 identical (`:194-195`) | **VERIFIED** |
| C8 | `ImpactSparksSizeName` 0x0168 / 5904 = `'Size'` | same | row 43 identical (`:221`) | **VERIFIED** |
| C9 | `ExplosiveImpactScreenShake` "**18** nested props", then lists **5** | same | row 75: 18 props, and the omitted values include `0x38 [150,150,150]`, `0x68 1.0`, `0x70 5.0` (`:253`) | **UNDERSTATED** (claims 18, shows 5) |
| C10 | `ImpactMinDamageSpeed` 20 / 40 / **60** base CDO | `DAMAGE_RULES.md` §3.3 | `:152` has **two** columns, 20 / 40; no base-CDO column | 20/40 VERIFIED; **60 UNSUPPORTED as cited** |
| C11 | `ImpactMaxDamageSpeed` 150 / 180 / **200** | same | `:151` 150 / 180 | 150/180 VERIFIED; **200 UNSUPPORTED** |
| C12 | `ImpactMaxDamage` — / — / **100** | same | `:149` — / — | **UNSUPPORTED** (base value) |
| C13 | `ImpactMaxDamagePow` **0.666** / **0.666** / 0.666000009 | same | `:150` is **— / —**; the 0.666 pair belongs to **`BattleModeImpactMaxDamagePow`** (`:144`, shipped 0.5 / Joker 0.666) | **MISMATCH** — another field's value moved into this row |
| C14 | `ImpactStrafeMod` 2.25 / 0.8 / 1.5 | same | `:153` 2.25 / 0.8 | 2.25/0.8 VERIFIED; **1.5 UNSUPPORTED** |
| C15 | `ImpactBoostMod` 2 / — / 1.5 | same | `:147` 2 / — | base 1.5 **UNSUPPORTED** |
| C16 | `StafeImpactImpulse` — / — / 100000 | same | `:154` — / — | **UNSUPPORTED** |
| C17 | `BattleModeImpact*` 120 / 540, Pow 0.5 / 0.666 | same | `:144-146` identical | **VERIFIED** |
| C18 | "every field the body reads is listed there" (§3.3) | same | `:142` says 11 fields, two columns | **OVERSTATED** (the base column is not in it) |
| C19 | `3500` UE units = 126 km/h | `SPEEDOMETER.md` | `:58` value 3500; `:69` "in Unreal units (cm/s): 126 km/h" | **VERIFIED** |
| C20 | `CAMERA.md:33` unit rule and `:206` `FOVVelocityRange` [5, 50] km/h | `CAMERA.md` | both lines quoted verbatim | **VERIFIED** |
| C21 | `BML_Impacts` = 4 events, all `Play_Batmobile_Destroyed` | `AUDIO_FEATURES.md` | `:729-731`: four identical names | **VERIFIED** |
| C22 | no `Batmobile_Impact_02`, `Landing_Sparks`, `WallScrape`, `Debris` in the particle census | `PARTICLES.md` | grep counts **0 / 0 / 0 / 0** | **VERIFIED** |
| C23 | no dent / deform member, mesh or morph target | `Research/BatmobileGrab/*.md` | the only "dent" hits are substring matches inside **"identity"** (`BOX_FLAGS.md:165-167`); no deform member | **VERIFIED** (word the search to exclude `identity`) |
| C24 | collision package sizes 18,767 … 9,631 / 13,535, `break_impact_*` 14,527 each, `break_electric_sm` 11,535 | `DECODE_DEPTH.md` | rows 138-154 identical, including 11,535 (`:208-224`) | **VERIFIED** |
| C25 | palette keys `0x6568 / 0x65b8 / 0x657c / 0x6608 / 0xc2e0 / 0x6658` | `PALETTE_HASH.md` | `:70,76,89,90,93,94` identical | **VERIFIED** |
| C26 | `chassis_slide_default` palette key "—" | same | `:71` key **0x74c4**; the four material slides also carry keys (`:96-99`) | **UNDERSTATED** |
| C27 | a `cargo_chassis_impact_{default,dirt,sand,snow,water}` set exists | listed with the collision packages | **no** `cargo_chassis` row in `DECODE_DEPTH.md`; the set is in `FX_TABLE.jsonl` | **MIS-CITED** (exists, wrong source) |
| C28 | "0 hits" for a speed field, across USAGES / DAMAGE_MODEL / DAMAGE_MECHANISMS / ARMOR_STEP | those four | `speed` appears **7×** in `USAGES.md` (`speedwind_sound_player` `:368`, `z80_speed_threshold` `:388`, `car_speedrom_*` `:442-443`), 0 in the other three | **OVERSTATED wording** — conclusion holds: none is a speed field on a collision table |
| C29 | `HeavyCannon_Impact_Px` "11 (4645–4655)" | `PARTICLES.md` | count 11 ✓; no index range `4645–4655` in the file | count VERIFIED, range **UNSUPPORTED** |
| C30 | the `.effc` string table is "0 values across 955 files, per the exhaust report" | "the exhaust report" | unnamed | **UNSUPPORTED citation** |

---

## 3. Mode-switch plan — statement by statement

| # | statement | cited source | what the source says | verdict |
|---|---|---|---|---:|
| M1 | `BattleMode*` 42 declared / 15 serialised; `TurnOnSpot*` 4/3; `Transformation*` 9/4 | `MODES.md` §1 | `:36,38,40`: 42/15, 4/3, 9/4 | **VERIFIED** |
| M2 | `TurningModeMaxSpeed` 1/1, 600 cm/s = 21.6 km/h | `MODES.md` | `:41` 1/1/0; `:86` 600 in all four packages; 600/27.78 = 21.6 | **VERIFIED** |
| M3 | `ArmourModeDamageReduction` 1/1, 0 shipped | `MODES.md` | `:42` 1/1/0; `:153` value 0 at 0x1918 | **VERIFIED** |
| M4 | 61 unserialised fields | `MODES.md` | `:15`, `:334` | **VERIFIED** |
| M5 | offsets 0x218, 0x2c4, 0x2cc, 0x300, 0x320, 0x1c8, 0x1cc, 0x1d0, 0x2e0, 0x384, 0x354 | `MODES.md` | `:80-107` all identical | **VERIFIED** |
| M6 | `TurnOnSpot` 0.8 / −0.8, engine-braking 2 | `MODES.md` | `:80-82` identical | VERIFIED, but these are the **serialised archetypes**; the shipped sim inherits CDO 0.6 / −0.5 / 0.01 (`DRIVE_MODES.md` §3) — the report does not say which car |
| M7 | `BattleModeTurnOnSpotTorqueFactor` 0.333333 | `MODES.md` | `:92` identical | **VERIFIED** |
| M8 | 52 module types / 1,421 paths | `VOCABULARY.md` | 52 `##` sections, 1,421 member rows | **VERIFIED** |
| M9 | `all_hinged_part_properties` 25 rows | `VOCABULARY.md` | `:1359` "25 strings" | **VERIFIED** |
| M10 | `LandingGear` 7 chassis (25 entities, 114 parts); `LandingGearHatch` 5 (76 parts); `AirBrake` 1 (3 parts); `Flaps` 8 (202 parts) | `FEATURE_CENSUS.md` | `:183,184,156,174` identical | **VERIFIED** |
| M11 | `TurretDoor` 2 (6 parts, 6 entities); `MissileHatch` 1 (16 parts) | same | `:219,190` identical | **VERIFIED** |
| M12 | `Aileron` L/R → `steering_roll` / `_inverted`, 6 chassis | same | `:186,203,257-258`: `LeftAileron` 18/18/**6**, `RightAileron` 18/18/6, variables as stated | **VERIFIED** |
| M13 | `Elevator`/`Rudder`/`SteeringWheel`/`BoatEngine` 6/7/9/8 | same | `:171,207,211,160` identical | **VERIFIED** |
| M14 | `TurretDoor` and `MissileHatch` have no driving variable ("-") | same | `:238`, `:245` both `-` | **VERIFIED** |
| M15 | `BavariumShield` 26 parts / 14 entities / 4 chassis | same | `:159` identical | **VERIFIED** |
| M16 | **66** part behaviours | same | `:34` "part behaviours | **67**" | **MISMATCH** |
| M17 | "`DriverLean` (**23 aircraft**)" | `VOCABULARY.md` | n=23 ✓, but `Research/challenge/card-T-10.md:58` A4: **18 bikes + 5 boats, 0 aircraft** — the exact label A4 refuted | **OVERSTATED** |
| M18 | `righting_torque` 1500..4000, `leaning_torque` 2000..8000 | `VOCABULARY.md` | `:566`, `:563` identical | **VERIFIED** |
| M19 | `Fins.effective_in_air` 0 in 200/200; `effective_in_water` 0..1 | same | `:625-626` identical | **VERIFIED** |
| M20 | `Limit_Speed_Hover` 20..60; `Limit_Pitch_Yaw_Switch` −1..0.82 | same | `:706`, `:202` identical | **VERIFIED** |
| M21 | boost blocks: nitro 15000 / 2.0 / 1.0 / 43.2 / 0.2; upgraded 20000 / 2.0 / 4.26 / 100.92 / 0.2; heat 0 / 2.0 / 4.26 / 100.92 / 0.0 | "the car's own module, decoded" | `Builds/bm-RC2/...custom_land_global.vmodc` dump matches **all fifteen** | **VERIFIED** |
| M22 | `turbo_jump` 15 / 12 / 0.1 / 50 / 200 / 2.0 and upgraded 30 / 25 / 0.1 / 80 / 200 / 2.0 | same | dump identical | **VERIFIED** |
| M23 | `ExtendedExposedVariables` = 2 expressions (the two `speed_rom_*` strings) | `VOCABULARY.md` | `:616` the same two strings | **VERIFIED** |
| M24 | `model_swap` "string, one fleet value, **0..0 in the 100 rows** decoded" | `VOCABULARY.md` | `:1606` string = 1 distinct; `:1605` **hash** = 0..0, n=100 | **OVERSTATED** (the string is not the 0..0 member) |
| M25 | entity variants incl. `_signature_shielded`, `_signature_shielded_di_ravello`, cited to `ENTITIES.md`, `FORCEPULSE.json` | those two | `ENTITIES.md` has **0** hits; `FORCEPULSE.json` has **6**; `_di_ravello` not found in either | **MIS-CITED**, one name **UNSUPPORTED** |
| M26 | `FLEET.md` rows 7-9 = the three bavarium-tank entities | `FLEET.md` | `:21-23` exactly those three | **VERIFIED** |
| M27 | "every armed chassis … `_civilian_01`" | `FEATURE_CENSUS.md` | the cited rows show `debug` / `military_01` / `rebel_01`; `_civilian_01` not shown there | **PARTIAL** |
| M28 | no `*Mode*` / `*Transform*` module type in the 52 | `VOCABULARY.md` | no section name matches; the only "Mode" hit is `HelicopterModel` (`:708`), a model name | **VERIFIED** |
| M29 | no animation-node member on a JC3 car (U5) | `VOCABULARY.md` | 4 "animation" hits, all `motorbike_common.animation_*` (`:1402-1405`); no `AnimNode` | **VERIFIED** |
| M30 | "**0 handling members**; the 42 hits are deform points …" | no file, no regex | not reproducible from the report | **UNSUPPORTED** (count); the *conclusion* is consistent with `DRIVE_CARRIERS.md` §0/§4.1 and `TANKTURN.md` |
| M31 | "no selector member / no per-mode table" | searches | no counter-example found in `VOCABULARY.md`; consistent with `DRIVE_CARRIERS.md` §0 | **VERIFIED** in substance |
| M32 | "the only in-place runtime handling change is the boost state" | `CustomLandGlobal` | consistent: the three boost blocks are the only handling multipliers with a state gate; `DRIVE_CARRIERS.md` §6.2 agrees | **VERIFIED** |
| M33 | `TransformationRotation` 0x384 / `TransformationAnimNode` 0x354 not serialised | `MODES.md` | `:104,107` both "no"; also listed unserialised at `:121` | **VERIFIED** |

---

## 4. Every "no JC3 member" statement, judged separately

| statement | where | support | verdict |
|---|---|---|---:|
| "no JC3 vehicle switches its handling at runtime" | M title, §0 | no selector member in `VOCABULARY.md`; `DRIVE_CARRIERS.md` §0 same conclusion | **VERIFIED in substance** |
| "no module named `*Mode*`/`*Transform*`" | M §2.7 | 52 sections, only `HelicopterModel` matches "Mode" | **VERIFIED** |
| "no per-mode value table; no selector member" | M §2.7 | no counter-example found | **VERIFIED** |
| "0 handling members (42 hits are other things)" | M §2.7 | no regex/script; count not reproducible | **UNSUPPORTED count**, conclusion stands |
| "`Fins.effective_in_air` = 1 anywhere: 0 of 200" | M §2.7 | `VOCABULARY.md:625` 0..0, n=200 | **VERIFIED** |
| "`ExtendedExposedVariables` beyond the speed-ramp pair: 0" | M §2.7 | `:616` exactly 2 expressions | **VERIFIED** |
| "no animation-node member on a car" | M §7 U5 | no `AnimNode` in the vocabulary | **VERIFIED** |
| "JC3 keys collision effects by part and material, not by speed" | C §5.1 | the six-material family and the part usages in `USAGES.md`; no speed member | **VERIFIED** |
| "0 hits for a speed/velocity field" | C §5.1 | 7 `speed` lines in `USAGES.md`, none on a collision table | **OVERSTATED wording**, conclusion holds |
| "no dent or deformation member/mesh/morph" | C §3 | no such member; "dent" hits are `identity` substrings | **VERIFIED** (with the false-positive note) |
| no `Batmobile_Impact_02` / `Landing_Sparks` / `WallScrape` / `Debris` in the census | C §2.1 | grep 0/0/0/0 | **VERIFIED** |
| "no speed axis in the collision effects" → band gate is "our own selection logic" | C §6 | correct and correctly labelled a proposal | **VERIFIED** |
| "the `.effc` string table is 0 values across 955 files" | C §7.3 | "the exhaust report" is not named | **UNSUPPORTED citation** |

---

## 5. Corrections — collision plan

1. **`Impact_Body_UPGR` 39 → 13, `Impact_Full_UPGR` 42 → 15, `Impact_Head_UPGR` 33 → 13**
   (`PARTICLES.md:125-127`). If 39/42/33 came from a different column (the module-row table at
   `:335` shows 14 for one build), say which column and build; as written they are 2.5–3× the census.
2. **`ImpactMaxDamagePow` row**: the two serialised archetypes carry **no value** (`DAMAGE_RULES.md:150`);
   the 0.666 values belong to `BattleModeImpactMaxDamagePow` (`:144`). Put `—` in the first two cells
   and keep 0.666 where it belongs.
3. **The base-CDO column (60 / 200 / 100 / 1.5 / 1.5 / 1.0 / 100000)** is not in §3.3, which has two
   columns. Cite `CHAIN.json` / `CLASS_DEFAULTS.md` for those cells (the report's §1 lists `CHAIN.json`
   nowhere) or delete the column; the sentence "every field the body reads is listed there" also needs
   narrowing to "11 fields, two serialised columns".
4. **`ExplosiveImpactScreenShake`**: either print all 18 values or write "18 (5 shown)"; the omitted
   `0x38 [150,150,150]` is the largest number in the struct and the one the band table would use.
5. **Palette column**: `chassis_slide_default` has key **0x74c4** and the material slides have
   0x7528/0x74d8/0x7564/0x7500 — replace the "—" cells (`PALETTE_HASH.md:71,96-99`).
6. **`cargo_chassis_impact_*`**: cite `FX_TABLE.jsonl`, not the `DECODE_DEPTH` collision rows.
7. **"0 hits" for speed**: say "0 collision-table speed members; `USAGES.md`'s 7 `speed` hits are
   `speedwind`/`speedrom`/nitro names" — otherwise a reader who greps will think the report is wrong.
8. **`(4645–4655)`** on the heavy-cannon system has no source in `PARTICLES.md`; drop the range or cite
   the index column it came from.
9. **Name "the exhaust report"** (path + line) or drop the 955-file claim.

## 6. Corrections — mode-switch plan

1. **66 → 67 part behaviours** (`FEATURE_CENSUS.md:34`).
2. **"23 aircraft" → "23 bikes and boats (18 bikes + 5 boats, 0 aircraft)"** — this is exactly the
   inference `card-T-10.md` A4 marks BROKEN, and re-using it re-breaks the argument it refuted.
3. **`model_swap`**: split the sentence — the **string** has 1 distinct value; the **hash** is 0..0 over
   n=100 (`VOCABULARY.md:1605-1606`). As written it says the string is 0..0.
4. **`_signature_shielded`**: `ENTITIES.md` does not carry the name (0 hits); cite `FORCEPULSE.json`
   (6 hits) or `SHAPES.md`/`USAGES.md`. `_signature_shielded_di_ravello` has no source in either file
   the report cites — name the file that has it or drop it.
5. **The "42 hits"** in §2.7 needs the search named (file, regex, or the script that ran it); without it
   the number is a claim, not a census. The conclusion (0 handling members) does not depend on it.
6. **`_civilian_01`**: the cited `FLEET.md` rows show `debug` / `military_01` / `rebel_01`; either cite
   where `_civilian_01` is counted or narrow "every armed chassis".
7. **Say which object the 0.8 / −0.8 / 2 belong to.** `MODES.md:80-82` are the serialised archetypes;
   the shipped `SimulationModel` inherits the CDO 0.6 / −0.5 / `TurnOnSpotModeEngineBrakingFactor` 0.01
   (`DRIVE_MODES.md` §3). Both readings are in the corpus and the report does not choose.

---

## 7. Commands run

```
grep -nE "ImpactSparks|SpinningSpikes|JumpLandSparks|WallScrape|ImpactSparksSizeName|CollisionFFWaveForm|ExplosiveImpactScreenShake" Research/BatmobileGrab/CLASS_DEFAULTS.md
grep -nE "ImpactMinDamageSpeed|ImpactMaxDamageSpeed|ImpactMaxDamage|ImpactStrafeMod|ImpactBoostMod|StafeImpactImpulse|BattleModeImpact" Research/BatmobileGrab/DAMAGE_RULES.md
sed -n '128,156p' Research/BatmobileGrab/DAMAGE_RULES.md          # §3.3 has two columns
grep -nE "206 systems|1433|Impact_Body_UPGR|Impact_Full_UPGR|Impact_Head_UPGR|HeavyCannon_Impact" Research/BatmobileGrab/PARTICLES.md
grep -n "BML_Impacts" Research/BatmobileGrab/AUDIO_FEATURES.md ; sed -n '729,731p' …
grep -n "3500\|126" Research/BatmobileGrab/SPEEDOMETER.md ; sed -n '33p;206p' Research/BatmobileGrab/CAMERA.md
grep -ricE "dent|deform" Research/BatmobileGrab/*.md ; grep -ni "dent" Research/BatmobileGrab/BOX_FLAGS.md
grep -nE "SDynamicAttachedEffectTable|SAttachedEffectTable|part_impact|chassis_impact|chassis_sliding|wheel_suspension|landing_wheel_impact_sound|2963579072" Research/JC3Grab/USAGES.md
grep -nE "chassis_impact|chassis_slide|break_impact|headlight_break" Research/JC3Grab/DECODE_DEPTH.md
grep -nE "chassis_impact|chassis_slide|break_impact|break_electric|headlight_break" Research/JC3Grab/PALETTE_HASH.md
grep "chassis_impact_default" Research/JC3Grab/FX_TABLE.jsonl | grep -o '"rows":[0-9]*'      → 2669
for f in USAGES DAMAGE_MODEL DAMAGE_MECHANISMS ARMOR_STEP; do grep -ci speed Research/JC3Grab/$f.md; done  → 7/0/0/0
grep -rl "cargo_chassis" Research/JC3Grab/                                   → FX_TABLE.jsonl only
sed -n '34,46p' Research/BatmobileGrab/MODES.md ; grep -n "61" … ; grep -n "ArmourModeDamageReduction" …
grep -c "^## \`" Research/JC3Grab/VOCABULARY.md ; grep -c "^| \`" …            → 52 / 1421
grep -nE "effective_in_water|leaning_torque|Limit_Speed_Hover|Limit_Pitch_Yaw_Switch" Research/JC3Grab/VOCABULARY.md
grep -n "model_swap" Research/JC3Grab/VOCABULARY.md ; sed -n '612,616p' …
grep -nE "^## \`.*(Mode|Transform|State|Switch|Tilt)" Research/JC3Grab/VOCABULARY.md  → HelicopterModel only
grep -ni "animnode|animation" Research/JC3Grab/VOCABULARY.md                 → 4, all motorbike_common
grep -nE "66|BavariumShield|TurretDoor|LandingGear|MissileHatch|AirBrake|Flaps" Research/JC3Grab/FEATURE_CENSUS.md
grep -nE "Aileron" Research/JC3Grab/FEATURE_CENSUS.md ; sed -n '235,247p' …
grep -c "signature_shielded" Research/JC3Grab/ENTITIES.md Research/JC3Grab/FORCEPULSE.json   → 0 / 6
sed -n '1,23p' Research/JC3Grab/FLEET.md
uv run python Tools/scripts/jc3adf.py dump Builds/bm-RC2/.../batmobile/…_custom_land_global.vmodc | grep -E "nitro_boost|heat_boost|turbo_jump"
```

**Limits.** Static reads only; no game launched. Counts that depend on an unstated regex (the "42
mode hits", "0 handling members") cannot be reproduced from the reports as written — that is what
corrections C/M 5 above are for. The `types: 36` field of the `FX_TABLE` row was not reproduced because
the record's field order differs from the report's phrasing; the `rows: 2669` field was.
