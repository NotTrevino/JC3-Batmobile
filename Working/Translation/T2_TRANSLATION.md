# T-2 — the appearance, assembly, audio, effect and damage table (draft 1)

**Status:** carried by test-085 (T-5); the 35 module edits that carry T-1 are live and read back
through the `.toc` — see `T5_BUILD.md`. One T-2b value is queued for the next build: T-DM6
(`deform_scale` 0 → 1), a field the build disables and every land vehicle in the fleet enables.
Every count below was re-read from the build this pass; the lights section's 21-row/22-object
mismatch is resolved by `t2_lg2.py`.
[T-1](T1_TRANSLATION.md) translates **motion** (mass → brakes). This document translates the other
half of the grab: **what the car is made of and what happens to it** — materials, textures, parts,
sockets, lights, audio, effects, damage, collision, weapons.

Every number below is printed by `Tools/scripts/t2_facts.py` into
[T2_FACTS.md](T2_FACTS.md) from files on disk. A value that is not in that file is marked
`assumed` here, in the row, not in a footnote.

**Column meanings are T-1's** (§0 there): `BmAK` source · `JC3 target` · `transform` · `now`
(what test-083 actually ships, read from `current.json`) · `proposed` · `conf` · `verify`.

---

## 1. Appearance — 185 materials, 405 textures, 19 slots

BmAK: `SLOTS.json` — **19** material slots, **13** material instances, **38** textures bound,
3 LODs with identity material maps, LOD0 **299,837** faces. The body master
`Batmobile_Body_MASTER` binds Diffuse/`NEW_Batmobile_V2_BODY_D` (4096×2048 DXT1), Normal
(`…_BODY_N`, BC5) and SpecularPower (`…_BODY_S`).

JC3: no material *instances*. A vehicle mesh carries per-LOD material blocks, and the only
paint-capable one is `CarPaintMM` (a scalar/colour set: diffuse tint, gloss, normal).

| # | BmAK | JC3 target | transform | now (083) | proposed | conf | verify |
|---|---|---|---|---|---|---|---|
| T-MA1 | 19 slots / 13 instances, 3 LODs | material blocks per `.rbm`, one set per LOD | 1 slot → 1 `CarPaintMM` block (`Window` for glass) | **185 `CarPaintMM` + 25 `Window` = 210 blocks** (re-decoded this pass from `Working/Appearance/build/*.rbm`: body LOD1-5 = 17 each, wheel LOD1-5 = 5 each × 4 wheels = 25 meshes); the 200 + 35 over "35 meshes" was 25 blocks high | keep | decoded | `verify_install.py` reads the deployed pair through its own `.toc` (9/9), then the block count per RBM |
| T-MA2 | `NEW_Batmobile_V2_BODY_D` 4096×2048 — **not in the grab** (the grab holds only `Body_Decals_D`, `Body_N`, the chapter mask) | `CarPaintMM` `s0` albedo | texture if one existed, else the T-MA3 constant, gain 1.0 | **solid colour** `[0.4784, 0.4588, 0.4941]` sRGB = 0.1946/0.1779/0.2086 linear = **3.44×** BmAK; **21** Batmobile `.ddsc` shipped, largest 1024² | the T-MA3 colour `0x43/0x41/0x45`; a body albedo at 1024² first (2048² BC1 = 2 MB, over the 694 KB headroom) — the asset gap is a grab, not a JC3 limit | decoded / UNKNOWN | `factors.json` `s0` == `0x43/0x41/0x45` and 21 `.ddsc` registered in `@files.xml` |
| T-MA3 | authored base `[0.025787, 0.025787, 0.03, 1]` linear × `Diffuse_Adjust` `[2.2, 2.0, 2.0]` = `[0.0567, 0.0516, 0.06]` (`COLOUR_PARAMS.md` §2/§3) | `CarPaintMM` diffuse colour | **gain 1.0** — GRB-6's 3.4476 is withdrawn: it matched a vanilla *tint* luma to a flat *albedo* luma | 0.4784/0.4588/0.4941 sRGB = 0.1946/0.1779/0.2086 linear (bytes 0x7a/0x75/0x7e) = **3.44×** BmAK | **0x43/0x40/0x45** = 0.0566/0.051574/0.0600 linear (sRGB 0.265/0.2518/0.272) — the green byte is **0x40**, not 0x41 (`paint-plans-v2.md` M3: 0x41 is 0.052861 linear, 2.5 % high; `srgb8(0.051574)` = 64.20) | derived | `factors.json` `solid` bytes == 0x43/0x41/0x45; noon screenshot: body luminance above the road, not below (078) |
| T-MA4 | authored gloss **0.600** (`VALUES.json` `paint.authored_gloss`), palette `clear_coat` 1.0 | `CarPaintMM` `m_SpecularGloss` `cb2[0]` + palette `specular_gloss` | identity — 0.45 was never a cap: the donor palette ships **8 of 10 tints at 0.45** (measured), 0.4 is one block's channel-1 value | **0.450** in 16 paint blocks and 10 palette tints = **0.75 ×** authored | **0.600** in both, declared R3 (33 % above the highest shipped 0.45) | derived | `spec_check.py` gloss == 0.600; dry-road screenshot satin armour, not wet mirror (079) |
| T-MA5 | `Glass_Opacity` **1.2**, `Glass_Reflectivity` **0.8**, `Glass_Roughness` **1.1**, `glass_smudges` 0.2; maps `Glass_S` (R reflect 0.565 / G rough 0.074), `Glass_N`, `Glass_A` | `Window` `cb1`: `SpecFresnel`@4, `SpecGloss`@0, `DiffuseRougness`@8, `Alpha`@40, plus `s0` alpha | `SpecFresnel` = 0.565 × 0.8 = **0.452**; `SpecGloss` = 1 − (0.074 × 1.1 = 0.081) = **0.919** | opacity × 1.2 ported (`Glass_A` alpha); tint 0.176/0.176/0.188; **no** reflectivity or roughness written; canopy normal at block table position 1 while `window.fb.txt` samples it at `s2` | `SpecGloss` **0.92**, `SpecFresnel` **0.45**, normal moved to `s2`; per-pixel via `s3` is UNKNOWN (test T5b) | derived | canopy reads as glass at noon, highlight width between paint and mirror; normal detail visible at grazing angle |
| T-MA6 | 405 textures grabbed, 38 bound to slots | the `.ee` texture set | selection by slot binding | **24** distinct TGAs bound → **21** Batmobile `.ddsc` shipped → **9** slots a solid colour → **32** `s2`/`s3` on `a00_dummy_black_mpm`; "28 shipped" counts the whole set (21 + 7 others) | state the three counts separately and route the missing separation masks (body `WheelArch_MicroMasks` absent from the grab) | decoded | `.ddsc` count per build dir and the `spec_check.py` texture list |
| T-MA7 | no `Palette` in UE3 vehicles | `Palette.tints[]` | — | 10 tints: `specular_gloss` **0.45 × 8 / 0.0 × 2**, `metallic` 1 × 8 / 0 × 2, `clear_coat` 1 × 10; any tint selection **replaces** the authored body colour | keep the 10-tint menu but set every tint's colour to the T-MA3 `0x43/0x40/0x45` and every `specular_gloss` to 0.600, so the menu cannot leave the lore colour | decoded | paint menu shows 10 colours and none leaves the lore colour or contradicts the blocks |

Fleet check on T-MA4: `Palette.tints[].specular_gloss` is **0 … 1, median 1** over 3,602 tints
(155 names), and the highest value the donor fleet is *seen* to use is the donor palette's own
**0.45** (8 of 10 tints, measured in `Working/Palette/serpente_palette.xml`). The authored 0.600 is
therefore 33 % above anything shipped: it is declared **R3** — out of the observed range, not out of
the format — and is the one appearance row where the fleet distribution is deliberately overruled.
The 0.45 the build ships today is **0.75 × authored** and rests on "vanilla caps paint gloss at 0.4",
which is one block's channel-1 value, not a cap (`keep-audit-materials-textures.md` §5).

## 2. Assembly — parts, sockets, hardpoints

BmAK: 247 sockets across 12 skeletal meshes; wheels on `SUSP1_*`/`SUSP2_*` plus `*_Vis_Mesh`
bones; light rig names **3 parts** (body 77 entries, `wheel_f_l` 14, `wheel_f_r` 10 — that is
`LIGHTS.json`'s `by_part`, and it is the only place BmAK says which part a light belongs to).
JC3: 40 `CPartProp` in the **vanilla donor's** `.epe`, which agree 40/40 with the 42-row parts module
(plus `hood_signature` and `missile_base_signature`). The **built** entity's graph is smaller — **6**
`CPartProp` (body, `taillight_r_l`, four wheels), measured by `t2_lg2.py`; the 42-row parts module is
carried unchanged from the donor, so a part exists in `VehicleParts` whether or not the graph names it. The parts module itself now
decodes ([PARTS.md](../../Research/JC3Grab/PARTS.md), G2-7 solved): 232/232 vehicles, 11,599 parts,
and the donor's full 42-row table in [PARTS_TABLE.md](../../Research/JC3Grab/PARTS_TABLE.md).

| # | BmAK | JC3 target | transform | now | proposed | conf | verify |
|---|---|---|---|---|---|---|---|
| T-PA1 | wheel bones `SUSP1/2_*`, `*_Vis_Mesh` | `CPartProp` `wheel_f_l/f_r/r_l/r_r` | categorical (name) | **6 `CPartProp`** in the built `.epe`: body, `taillight_r_l`, 4 wheels (measured, `t2_lg2.py`) | keep — the 42-row parts module is unchanged and does not need a graph object per part | decoded | `t2_lg2.py` |
| T-PA2 | 3 parts carry lights (body + both front wheels) | `DeformPoints.light_indices` → `points[].from_part` | index map | 21 light points → **12 parts** (body ×2, both front lamps ×2 each, tail lamps, signals) | keep | decoded | `jc3parts.py check` |
| T-PA3 | per-bone body ↔ part | `parts[].world_collision_body_id` / `raycast_body_id` | index map | decoded — e.g. `body` → 0, `door_f_l` → 1, `engine` → 7, wheels → −1 (`PARTS_TABLE.jsonl`) | keep | decoded | part ids vs the collision bodies in QA-1 |
| T-PA4 | 4 wheels | `VehicleParts.wheel_parts[]` | index map | parts 11, 12, 26, 27 → slots 3, 2, 0, 1; 1 spoke, spins 1 | keep | decoded | wheel spin/steer in QA-1 |
| T-PA5 | doors | `VehicleParts.door_parts[]` | index map | parts 1, 2, 25 | keep | decoded | door animation |
| T-PA6 | hinged parts (doors, hood, mirrors, bumper, grill) | `DeformPoints.constraint_indices` | index map | 11 points → **11 parts** | keep | decoded | door/hood animation in QA-1 |
| T-PA7 | — | `DeformPoints.non_deformable_parts_indices` | index list | 20 parts skipped by the deform solver | keep | decoded | no crumple on lamps/plates/seats |
| T-PA8 | 6 orphan sockets in the light rig (named in `VehicleLights`, absent from the mesh) | — | — | — | drop; they cannot be driven | decoded | `LIGHTS.json` `problems` |

## 3. Lights — 101 BmAK entries, 21 JC3 rows, mismatch resolved

T-1 §12 already mapped the rig categorically. What this section adds is the **shipped state** and
the numbers behind it.

BmAK (`LIGHTS.json`): **101** entries over 4 packages — 46 `VEHLT_HeadLight`, 16
`VEHLT_BattleModeLight`, 12 `VEHLT_ForensicsLight`, 8 `VEHLT_TailLight`, 12 stripped-type, 4
interior, 3 boot. Disposition: 54 mapped, 23 approximated, 16 with no JC3 equivalent, 8 inferred
from socket name. Per rig that is **28** entries (`MECHANICS.md`).

JC3 build (`T2_FACTS.md`, re-read from `current.json`): **21** lights — **10 `HeadLight`, 5
`TailLight`, 2 `LeftSignal`, 2 `RightSignal`, 2 `Reverse`**. Five are real headlight spot rows
(`range` 30, `angle` 40), sixteen are `range` 2 / `angle` 10 stubs; multipliers are 2 on 12 rows and
1 on 9.

| # | BmAK | JC3 target | transform | now | proposed | conf | verify |
|---|---|---|---|---|---|---|---|
| T-LG1 | 28 entries/rig, 4 rigs (101 over 4 rigs, `LIGHTS.json`) | `VehicleDynamicLights.lights[]` | categorical (T-1 T-L1…L7) | **18** rows in the built module (21 − 10 dropped + 7 added, `bm_lightrig.plan()`) | **next: recount 18** — the row's own evidence line is "count in the built module" and that count is 18, not 21; the 21 predates B-07 | decoded | B-07's read-back: `lights[]` row count = 18 |
| T-LG2 | 22 `SVehicleLight` in the donor `.epe` (`ENTITIES.md`, vanilla entity) | same | — | **21 rows / 22 objects** in the built entity | **closed, for the donor join only** — `t2_lg2.py` proves the graph match; it says nothing about BmAK, and B-07 did drop 10 donor rows and add 7, so the module is no longer row-for-row the donor either. The BmAK-side test is T-LG1/T-LG3/T-LG6 and `keep-audit-lights.md` §1 (0 of 28 entries reproduced) | decoded | `t2_lg2.py` (donor join) |
| T-LG3 | 6 headlight-class entries per rig (2 primary + 4 flares/BattleMode/Forensics) | 2 primary + 1 secondary spot | categorical | **4** rows at `range` 30 / `angle` 40 (rows 2, 4, 6, 10), 1 at 10/60 (T-L17), 13 at 2/10 | **next: recount 4** (not 5) | decoded | B-07 read-back: 4 rows at 30/40 |
| T-LG4 | `LWheelLight`/`RWheelLight` (under-glow) | **no preset in JC3** | — | absent | **superseded by T-18**: a custom `preset_id 0` entry on a new `sportsmuscle_wheel_f_*_arch` part (G2-33 §7), rows `T-L13`/`T-L14` | superseded | `T14_LIGHTS.md` §4 |
| T-LG5 | battle-mode/forensics rigs (16 + 12 entries) | — | — | absent | **superseded by T-18** (D-2): the battle spotlight is a decoded behaviour value, `VEHLT_BattleModeLight` on the same light part (`Research/JC3Grab/LIGHT_SYSTEM.md`); the forensics rig stays a named omission | decoded | T-18's rows carry the verify |
| T-LG6 | `range`/`angle` authored per entry: `Radius` 6000 / 4500 / 4096 / 2048 / 1024 / 400 / 150 / 80 / 0.1 (cm), `OuterConeAngle` 70 / 60 / 50 / 44 / 35 / 15, `Brightness` 0.15 / 1.0 / 5.0, **0 entries blink** | `lights[].range` 0.1…50 (med 10), `angle` 10…50 (med 10), `multiplier`, `blinking` | unit bridge (cm→m) + angle identity | 30 / 40 on 4 rows; 2 / 10 on 13; `multiplier` 1–2 (donor); `blinking` 1 on rows 3, 5, 7, 9 | **next — derived per lamp**: `range = Radius_cm / 100` → 60, 45, 40.96, 20.48, 10.24, 4, 1.5, 0.8, 0.001 (60 and 45 exceed the fleet max 50 by 20 % and 10 % — declared R3, not rounded down to the band); `angle = OuterConeAngle` → 70, 60, 50, 44, 35, 15; `multiplier = clamp(5 × Brightness, 0.5, 5)` → 0.75 (0.15), 5 (1.0 and 5.0, clipped); **`blinking = 0` on the four cloned rows** — no BmAK entry authors a blink, so the flicker is a donor artefact inventing behaviour. `InnerConeAngle` has no member: closest composition is a second row on the same part with the narrow angle and the higher `multiplier` | derived (unit bridge) / declared (multiplier, units UNKNOWN) | Q-1 night drive, stock vs modified: reach, cone and steady (non-blinking) beam; `range`/`angle`/`multiplier` units are UNKNOWN (`LIGHT_SYSTEM.md` §8) |

## 4. Audio — the one subsystem JC3 does not expose in the entity

BmAK (`AUDIO_MAP.json`): **27** banks, 34.4 MB, **361** event rows, 118 unique event ids,
**239 resolved**, **447 media** (18.2 MB), 90 rows / 26 ids missing because **10 banks are not
shipped** (`BML_Batmobile_Subjective`, `BML_Impacts`, `BML_Sonar`, `CHR_BatmanAlerts`,
`CHR_BatmanDisruptor`, `OBJ_Rolling_Objects`, `UI_InGame`, `VEH_Tank_Heavy`,
`VEH_Tank_Missiles`, `VFX_Tank_Explosion`).

JC3: `LandAudio` has exactly **two members** — `min_rpm` 1000, `max_rpm` 10000. The vehicle's
sound is not in the entity module; it is in the FMOD bank that the vehicle's event names point
at.

| # | BmAK | JC3 target | transform | now | proposed | conf | verify |
|---|---|---|---|---|---|---|---|
| T-AU1 | 361 events / 447 media | `LandAudio` module | **not expressible** — 2 members only | `min_rpm` 1000, `max_rpm` 10000 | keep the module, move the mapping to the bank | decoded | — |
| T-AU2 | engine start/loop (decoded) | `sound/fmod_banks/vehicles.bank` | sample swap (proven, test-060) | 210,781,376 B bank installed | keep | decoded | engine note on start |
| T-AU3 | 90 event rows / 26 ids in 10 banks — all 10 **found** in the BmAK install (117 payloads, 447 media rows) | JC3 vehicle audio events on the donor's audio carrier (JC3 has no authorable bank) | epe / build | donor events | **next** (2026-11-06, evidence): the banks are present, so bind the 26 ids to JC3 vehicle event slots from the decoded media rows; where JC3 has no sample, a token-matched substitute must be auditioned (`T_AU3B` §4) | decoded (banks) / UNKNOWN (JC3 event binding) | each event fires in its context; audition needed |
| T-AU4 | — | `LandAudio.max_rpm` | follow `LandEngine.max_rpm` | **10000 vs engine 7300** — the two disagree in the build | **4,500** with T-1 T-E1 | derived | engine pitch stops climbing at the shift point |

T-AU4 is the only audio row that is a *number*; the rest are bank-level and cannot be edited as
module values. That is why the nitro swap was a sample replacement and not a parameter change.

## 5. Effects — 51 rows in the build, 17 names in the game

BmAK: 206 `ParticleSystem` tag streams read (G1-6), no semantic pass — the Batmobile's signature
VFX (afterburner flame, EMP buildup, seismic sonar, tyre smoke) exist as assets, not as named
vehicle bindings.

JC3 build 083: **51** `all_effects` rows over **51** deform points, **29** parts with effect
slices, **1** usage row (`HeadLights`). The effect vocabulary is 17 names fleet-wide; the build
uses 11: `burn_base`, `burn_engine`, `burn_roof`, `dynamic_headlight`, `electric_break`,
`large_break`, `medium_break`, `small_break`, `taillight_break`, `window_break`,
`window_break_sm`.

| # | BmAK | JC3 target | transform | now | proposed | conf | verify |
|---|---|---|---|---|---|---|---|
| T-FX1 | glass/lamp break VFX | `all_effects[].effect` = `window_break`, `taillight_break`, `electric_break` | categorical | present | keep | decoded | break a window in QA-1: shards spawn |
| T-FX2 | engine/roof fire | `burn_engine`, `burn_roof`, `burn_base` | categorical | present | keep | decoded | fire after the health threshold |
| T-FX3 | exhaust/afterburner flame | entity-graph `SAttachedEffect` on the donor's two emitters (`exhaust_upgrade_nitrous2`, `exhaust_upgrade_nitrous`), `usage` 4197885156 `EngineNitro` | epe — placement only | already carried: both emitters are `EngineNitro` in the donor graph; only their `world` mat was the Serpente's exhaust | **next** (operator ruling 2026-11-06, item 2): keep `EngineNitro` and place both emitters at `Afterburner` (bone `JetSMove`, [-0.009578, 0.537762, 3.393177] m) — the two `SAttachedEffect.world` matrices in `Working/Effects/bm_fx_edits.json` `edits[]`, compiled by `Tools/scripts/bm_fx.py` into `Builds/bm-008/.../v0300_car_kensington_sportsmuscle_civilian_01.epe`; flame `effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc` | decoded | boost: flame at the jet nozzle, loops while nitro is held; 32/32 effect hashes resolve (`T_FX3B.md`) |
| T-FX4 | EMP / seismic / tyre smoke | names not in JC3's 17 | — | absent | **superseded by T-11 + T-17** (D-7): EMP is an entity-level `CForcePulse` copy (`Research/JC3Grab/EMP.md`), tyre smoke is FX-3 `tire_effects`; seismic sonar stays a named omission (no sonar class) | decoded | T-11/T-17 rows carry the verify |
| T-FX5 | — | 74 `.effc` in the donor `.ee` | — | 23 unreferenced by the 51 rows | leave (they belong to the donor's own parts) | decoded | — |

## 6. Damage — decoded for all 233 vehicles, including the 24 types the parts module hides

BmAK **does** name a health field now: `RVehicleBatmobile.Health` = **1,200** in all three grabbed
archetypes (G1h, 423/423 fields). It is the donor's own hit-point pool, measured against Arkham
Knight's weapon damage; there is no bridge to JC3's damage scale, so the JC3 class distribution is
still the usable evidence. The rest of the damage block is a JC3-side choice, but the fleet
distribution is real.

| # | BmAK | JC3 target | transform | now | proposed | conf | verify |
|---|---|---|---|---|---|---|---|
| T-DM1 | `RVehicleBatmobile.Health` = **1,200** (3 archetypes) | `VehicleDamage.max_health` | class | **2,000** | keep 2,000: the 6 t p75 and the land-vehicle maximum (all land 500…2,000, median 700; 6 t+ median 1,600). BmAK's 1,200 is lower but has no unit bridge | class | survives a 5-star pursuit for >2 min in QA-1 |
| T-DM2 | — | `bullet_armor_strength` | — | **100** | **99** — the fleet maximum; 100 is one above every shipped vehicle | decoded (fleet) | reduces nothing measurable, but keeps the value inside the domain the game was tested with |
| T-DM3 | **no per-channel armour exists** — one `TakeDamage` path, `ArmourModeDamageReduction` 0, a weapon-generator shield; the only heavy/light distinction is projectile damage 75 body / 50 primary / 250 missile (`DAMAGE_RULES.md` §3.1, §3.5) | `bullet_heavy_armor` 5 @ `_strength` 20 | donor carry (medium tank's profile) | 5 @ 20 | **next: keep 5 @ 20, labelled a donor carry** — no decoded JC3 weapon writes `bullet_heavy` (`DAMAGE_MODEL.md` step 3), so the pair reproduces nothing measurable until a `bullet_heavy` carrier is decoded; the value is not a translation and no replacement number exists | derived (donor) | B-09's channel decode, then the heavy-MG take |
| T-DM4 | no threshold field decoded (destruction is the 1200 pool + generator shield + radial falloff 0.0/0.1/0.5/1.0/1500.0, `DAMAGE_RULES.md` §3.2) | `explosion_threshold` / `npc_explosion_threshold` / `smoke_threshold` / `burn_threshold` | fleet maximum (four values, not three) | **4000 / 4000 / 1050 / 250** | **next: record all four** — the ledger named three (`explosion` / `smoke` / `burn`), the module carries four; every one is at the top of its shipped domain (med 1000 / 250 / 100), so this is a fleet maximum, not a BmAK figure, and the BmAK timing is UNKNOWN | decoded (fleet) | fire and explosion timing under sustained fire (Q-1) |
| T-DM5 | **no per-part health table**: the 32 boxes are `RB_BodySetup` collision geometry on the **destroyed** asset (`PHYSICS.md`), and `RVisualDamageComponent` is 6 B with no decodable value (`REMAINDER.md:1102`) | `part_damage_types[]` + `VehicleParts.parts[].damage_type` | join (donor table) | **24 types** — `Land_Body` 1000, `Land_Wheel` 1020, `Land_Engine` 900, `Land_Window` 50, `Land_Light` 50, `Land_Grill` 200; **42 parts in bm-009, 61 in bm-RC2** (17 / 19 distinct types) | **next**: keep the donor rows; correct the `Boat_Antenna` reason — it **is** a real `PartDamageType`, declared by all 35 boat entities (`T2_TRANSLATION.md` C23), it is simply not in this vehicle's 24-row land table, so the `Default` fallback is real | decoded | Q-1 crash test for break order (no BmAK per-part HP exists to compare) |
| T-DM6 | **UNKNOWN** whether AK deforms panels: the record proves a destroyed mesh, damage masks and a `Damage_States` package, not panel deformation (`card-G1X.md` §6c) | `deform_scale` | project rule R1 (declared switch) | **0** (build 083) | **next: keep 0** — the earlier "**1** — all 156 land vehicles ship 1" proposal is withdrawn: 1 is the fleet rule, which R1 forbids importing, and the BmAK evidence is UNKNOWN, not "no deform"; `damage_switches.json` declares the 0 | decoded (switch) / UNKNOWN (BmAK evidence) | Q-1 impact observation; the damage-state mask path is the carrier if the operator wants AK's damaged look |

**T-DM5 is the correction to T-1 §13.** T-P2 said "blocked (G2-7)" for the whole per-part damage
table. That is only true for the *mapping* (`parts[] → damage_type → collision body`). The
*values* — 24 types with `initial_health`, `damaged_health`, `loosen_health`, break/loosen flags —
are in `VehicleDamage`, which decodes for every vehicle in the fleet.

## 7. Collision — 128 wreck boxes, and the drivable asset we only just found

BmAK (`PHYSICS.json`): **32** `RB_BodySetup` bodies per package (**128** across 4), all **boxes**,
**0 spheres**; largest box extents `[316.2, 63.4, 109.9]` cm, root body a 30.3 cm cube. That is the
**wreck** asset. The car the player drives is a different asset: `Physics.Batmobile_V3_Physics`
(BmGame.upk export 158266) — **2 bodies, 3 boxes, 1 constraint** — reached from
`Batmobile.SVehicleMesh` property offset 824 (`COLLISION_WHERE.md`, G3-16). Its largest box is the
chassis 690.305×374.536×207.5 cm, so the 316 cm box above is a wreck wheel, not the car.

JC3: chassis collision is the donor's — `physicsc` quads were moved with the mesh in §70, and 17
of 17 entities' station quads agree with `land_global` (`PHYSICS.md`).

| # | BmAK | JC3 target | transform | now | proposed | conf | verify |
|---|---|---|---|---|---|---|---|
| T-CO1 | **the drivable asset is `Physics.Batmobile_V3_Physics`** (BmGame.upk export 158266, 194 B): **2 bodies / 3 boxes / 1 constraint**, reached from `Batmobile.SVehicleMesh` property offset 824 (`COLLISION_WHERE.md`, G3-16) — chassis `Batmobile_Chassis` 690.305×374.536×207.5 at (9.0, 0, 106.75) **and** 679.585×345.688×103.5 at (0,0,79.0) (TMs identity), weapons pod `Batmobile_Rig_Weapons_Trans` 166.177×189.365×39.8 at (−30.5,0,93.25) at 4.000° about y, constraint export 171462 (chassis ↔ pod); the **32-body set is the destroyed wreck** (`PHYSICS.md`) | `.physicsc` collision shapes | — | donor hulls: bm-009 untouched donor (54 hulls), bm-RC2 donor topology re-cut to the body mesh (54 hulls, bounds 3.499×2.283×7.037 m); **62 donor body entries, body 0's single hull rewritten** (B-10e) | **reopened 2026-11-07: author the 2 BmAK bodies / 3 boxes into the donor's hull slots — box 0 into body 0's slot, box 1 + the pod into shape instances (0 free slots: the 14 unbound hulls are the donor bumpers) — and carry the 1 constraint where a slot exists; the donor's other 61 bodies stay as JC3's per-part contact (BmAK has none), a declared difference** — plan `Working/Translation/T22_REOPEN.md`, `t22_reopen.py --check`; the live convex mesh per mode is UNKNOWN (`BatmanVsBatmobileCollisionMode` is not serialised) | decoded (asset) / UNKNOWN (constraint parent, pod simulation) | `jc3hkx.py check --all --file` on the rebuilt set + shape union vs the 3 boxes + a Q-2 kerb/ram take |
| T-CO2 | largest **wreck** box 316.15x63.42x109.88 cm; the drivable car's largest is the chassis box 690.305x374.536x207.500 cm | — | 1 cm = 0.01 m; JC3 hull space is metres | 3.1615x0.6342x1.0988 m fits one donor hull (longest hull axis 3.679 m) - a wreck wheel, not the car's collision | next: keep the wreck-set maximum and do not author it as the car; the car's target is T-P3's chassis body (690.305x374.536x207.500 cm) | decoded (COLLISION_WHERE) / measured (T-22) | `t22_reopen.py --check` |
| T-CO3 | **no per-part world-collision flag**: the drivable asset is **2 bodies / 3 boxes + 1 constraint** (`COLLISION_WHERE.md`): one `Batmobile_Chassis` body and one `Batmobile_Rig_Weapons_Trans` body; the two Batman-vs-Batmobile meshes are separate components and the wreck has 32 bodies | `parts[].has_world_collision_shape` | donor carry (restated) | donor's: 38/42 = 1, the 4 wheels = 0 (`world_collision_body_id` -1); bm-RC2 has 61 parts, so the 42-part denominator is stale | next: keep the donor's flags and restate the reason - BmAK's 2 bodies prove the car has no per-part world bodies while the donor gives 38 parts their own, a declared difference; the chassis hull covers the wheels, so a player should not notice | decoded (asset) / measured (T-22) | `t22_collision.py --check` re-read at the RC2 part count |

## 8. Weapons, camera, interaction — no row, by decision

- **Weapons.** BmAK has 3 weapon generator meshes, an `RBatmobileMissile` class with 10 object
  refs, a turret bone and missile hardpoints. JC3's donor is unarmed; `SWeaponPoint` exists in the
  graph (300 fleet-wide) but the donor has none wired, and no JC3 car in the base game fires
  missiles from a turret. **No row** — this is a feature, not a translation, and it needs its own
  design (RD-2).
- **Camera.** 5,796 `CCameraModifier` and 4,477 `CCameraTransition` objects across the fleet graphs
  describe UE3's cinematic camera; JC3's car camera is engine-side. It is **no longer a blind row**:
  `R3rdPersonCamera`'s defaults are decoded (85°/95° FOV, smoothing, lean, battle-mode FOVs) and
  JC3's `car_base.ctune` is decoded too. See `T6_HUD_CAMERA.md` §2 and
  `Research/BatmobileGrab/CAMERA.md`.
- **Interaction.** 5,535 interaction-graph entries are the UE3 entry/exit puzzle (QTE doors, seat
  prompts). JC3's equivalent is its own vehicle interaction. **No row** — keeping the donor keeps
  the working one.

## 9. Blocked rows and what unblocks them

| row group | blocked by | unblocks with |
|---|---|---|
| ~~T-CO1, T-CO2~~ (writer proven 2026-10-28, reopened 2026-11-07) | the **write** side of `.physicsc` (reading is G2-8, solved) | nothing — `jc3hkx write` proved the writer (G2-30) and `COLLISION_WHERE.md` decoded the drivable asset (2 bodies / 3 boxes / 1 constraint), so T-22/B-10 are reopened to author it (`T22_REOPEN.md`); the 1 constraint has no decoded writer and is a named omission |
| ~~T-AU3~~ (unblocked 2026-11-06) | 10 banks were reported absent by a 3-package scan | nothing — all 10 are found in the BmAK install (`AUDIO_BANKS.md`: 10 found / 0 absent); what remains is the JC3 event binding |
| ~~T-FX3~~ (unblocked 2026-11-06) | the `usage_effects[].usage` hash vocabulary was the stated blocker | nothing — the donor entity graph already carries `EngineNitro`; the approved edit is B-08's placement (`T_FX3B.md`) |
| T-LG4 | JC3 has no wheel-light preset | a custom `SVehicleLight` in our `.epe` |

## 10. Verification — the same one build, different instruments

| family | measurement | pass |
|---|---|---|
| T-MA* | `verify_install.py` (9 checks) + noon screenshot luminance | body brighter than the road it sits on |
| T-LG* | dusk/night screenshot, beams on and off | 5 cones, correct colours, brake rows red |
| T-AU* | engine start, shift points, boost | pitch rises to the shift point and resets |
| T-FX* | break a window, set the engine alight | the right effect spawns on the right part |
| T-DM* | 5-star pursuit, crash test, per-part break order | survives minutes, not magazines |

## 11. What this changes

- **T-P2 was mislabelled blocked, and is now fully decoded.** The 24-type damage table is
  `VehicleDamage.part_damage_types[]` for all 233 vehicles, and the part→type mapping arrived with
  G2-7: `PARTS_TABLE.jsonl` now carries every part's damage type, collision body and children.
  Damage work can start now.
- **Audio cannot be a module row.** `LandAudio` has two members; everything else is the FMOD bank.
  Any future "engine sound" task is a bank task, and the 10 absent banks cap what is possible.
- **The build is at the fleet maximum on three damage thresholds** and **one above the maximum on
  bullet armour** — which is why "a couple of mags" does not kill it via thresholds, and why the
  remaining lever is `max_health` (T-DM1), not more armour.
- **Effects translate only where JC3 has the effect name.** 11 of the build's names come from the
  fleet's 17. The afterburner flame is *not* a gap: the donor graph already fires it under
  `EngineNitro` and the approved edit only moves its two emitters to the `Afterburner` socket
  (T-FX3, `T_FX3B.md`). Heat haze and the weapon FX remain the feature gaps.
- **The parts module is decoded.** Its format was measured and then read: member offsets are
  declared in the type dictionary, so `jc3adf.py` needs no extent guess. 232/232 vehicles and
  11,599 parts are in `PARTS_TABLE.jsonl`; the donor's 42 parts, 12 light parts and 4 wheels match
  `DeformPoints` exactly. Collision *shapes* now read too (G2-8): 18,797 hulls and 4,774 collision
  meshes across all 233 packfiles, every invariant passing — the open part is **writing** one, not
  reading it.
- **`deform_scale` is a build defect, not a translation unknown.** `T2_FACTS` reads **0** from build
  083; all 156 land vehicles ship **1**. The next build carries 0 → 1 (T-DM6). The old table said 1
  and "keep" — it had not read the build value, which is exactly the kind of error the row audit
  was meant to catch.
