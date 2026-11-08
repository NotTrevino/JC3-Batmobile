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
| T-MA1 | 19 slots / 13 instances, 3 LODs | material blocks per `.rbm`, one set per LOD | 1 slot → 1 `CarPaintMM` block (`Window` for glass) | **17 blocks per LOD** (16 `CarPaintMM` + 1 `Window`); 200 `CarPaintMM` + 35 `Window` across 35 meshes | keep | decoded | `verify_install.py` reads the deployed pair through its own `.toc` (9/9) |
| T-MA2 | `NEW_Batmobile_V2_BODY_D` 4096×2048 | `CarPaintMM` diffuse texture | identity (DDS, sRGB) | 28 Batmobile textures shipped | keep | decoded | slot→texture list in `SLOTS.json` vs the built RBM |
| T-MA3 | authored base colour `[0.02579, 0.02579, 0.03]` linear | `CarPaintMM` diffuse colour | **linear → sRGB, gain 3.4476** (`VALUES.json`) | effective `[0.056738, 0.05158, 0.06]` (albedo byte 0x83/0x7d/0x86) | keep | derived | noon screenshot: body luminance above the road, not below (078 failed this) |
| T-MA4 | authored gloss 0.6, vanilla caps paint gloss at 0.4 | `CarPaintMM` gloss | clamp to the vanilla cap, then raise | **0.45** in every paint block and in all 10 palette tints | keep 0.45 | derived | dry-road screenshot: satin armour, not wet mirror (079 was the mirror) |
| T-MA5 | `Batmobile_Glass` (8 slots empty), `…GLASS_D/N/MASK` textures present | `Window` block | empty slots → tint only | tint = the authored paint colour (`VALUES.json` glass: `Material0_BaseColour` — the canopy has no colour parameters); opacity = the BmAK opacity map × the authored `Glass_Opacity` scalar (`factors.py`) — no tuned constant anywhere | keep | derived | canopy reads as glass, not paint, at noon |
| T-MA6 | 405 textures grabbed, 38 bound to slots | 28 shipped | selection by slot binding | 28 | keep | decoded | any of the 377 unshipped are decals/Jokerfied/other packages — no row |
| T-MA7 | `Palette` does not exist in UE3 vehicles | `Palette.tints[]` | — | **10 tints**, all `specular_gloss` 0.45, `clear_coat` 1, `metallic` 1 (read from the shipped donor module in the build) | **leave** the donor's palette untouched — JC3's repaint menu is a game system the donor already serves; shrinking it would fight the game | decoded | in-game paint menu shows 10 colours, none of them altering the body beyond gloss |

Fleet check on T-MA4: `Palette.tints[].specular_gloss` is **0 … 1, median 1** over 3,602 tints
(155 names). The donor's 0.45 is already an outlier *on the dark side* — which is why it was chosen
for a matte Batmobile, and why the fleet median is not evidence against it. This is the one
appearance row where the fleet distribution is deliberately overruled.

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
| T-LG1 | 28 entries/rig, 4 rigs | `VehicleDynamicLights.lights[]` | categorical (T-1 T-L1…L7) | 21 entries | keep 21 | decoded | count in the built module |
| T-LG2 | 22 `SVehicleLight` in the donor `.epe` (`ENTITIES.md`, vanilla entity) | same | — | **21 rows / 22 objects**, exactly the donor's — measured in the built entity by `t2_lg2.py` | **closed**: 20 preset ids resolve to graph objects, 1 (`0xc832d6e0`) is a preset the graph does not instantiate, and 2 objects (`Front_Secondary_Head`, `Rear_Break`) are referenced by no row. Both counts differ inside the vanilla entity itself; the build dropped nothing | decoded | `t2_lg2.py` (check ok: row-for-row equal to the donor) |
| T-LG3 | 6 headlight-class entries per rig (2 primary + 4 flares/BattleMode/Forensics) | 2 primary + 1 secondary spot | categorical | 5 spot rows at `range` 30 | keep 5 | derived | dusk screenshot: cones only from the 5, not from the 16 stubs |
| T-LG4 | `LWheelLight`/`RWheelLight` (under-glow) | **no preset in JC3** | — | absent | needs a custom `SVehicleLight` (T-1 T-L4) | blocked | — |
| T-LG5 | battle-mode/forensics rigs (16 + 12 entries) | — | — | absent | out of scope: JC3 has no battle mode | assumed | — |
| T-LG6 | `range`/`angle` authored per entry | `lights[].range` 0.1…50 (med 10), `angle` 10…50 (med 10) | identity | 30 / 40 on the 5 spots; 2 / 10 on 16 | keep — 30 is inside the fleet band, 40 is the fleet max | class | night drive: beams reach the road |

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
| T-AU3 | 90 event rows in 10 absent banks | — | — | donor events | keep donor's banks for those 26 ids | blocked (absent) | — |
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
| T-FX3 | exhaust/afterburner flame | **no usage slot** — the donor has exactly one usage (`HeadLights`) | — | absent | blocked on the usage enum: a hash-name JC3 will accept is unknown | blocked | — |
| T-FX4 | EMP / seismic / tyre smoke | names not in JC3's 17 | — | absent | out of scope | — | — |
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
| T-DM3 | — | `bullet_heavy_armor_strength` | class | 20 | keep (fleet 0…50) | class | heavy MG test |
| T-DM4 | — | `explosion_threshold` / `smoke_threshold` / `burn_threshold` | — | **4000 / 1050 / 250** | keep — all three are at the fleet maximum (med 1000 / 250 / 100) | decoded (fleet) | fire and explosion timing under sustained fire |
| T-DM5 | 32 per-bone bodies | `part_damage_types[]` + `VehicleParts.parts[].damage_type` | join | **24 types** — `Land_Body` 1000, `Land_Wheel` 1020, `Land_Engine` 900, `Land_Window` 50, `Land_Light` 50, `Land_Grill` 200; the 42 parts now carry their type (17 distinct; `c_mirror` uses `Boat_Antenna`, which is not in the table and falls back to `Default`) | keep | decoded | per-part break order in a crash test |
| T-DM6 | — | `deform_scale` | decoded (fleet) | **0** (T2_FACTS, build 083) | **1** — all 156 land vehicles ship 1; the build is the only one at 0 | decoded (fleet) | panel deformation on impact |

**T-DM5 is the correction to T-1 §13.** T-P2 said "blocked (G2-7)" for the whole per-part damage
table. That is only true for the *mapping* (`parts[] → damage_type → collision body`). The
*values* — 24 types with `initial_health`, `damaged_health`, `loosen_health`, break/loosen flags —
are in `VehicleDamage`, which decodes for every vehicle in the fleet.

## 7. Collision — 128 BmAK boxes, and a JC3 chassis we already moved

BmAK (`PHYSICS.json`): **32** `RB_BodySetup` bodies per package (**128** across 4), all **boxes**,
**0 spheres**; largest box extents `[211.5, 51.1, 109.0]` cm, root body a 30.3 cm cube.

JC3: chassis collision is the donor's — `physicsc` quads were moved with the mesh in §70, and 17
of 17 entities' station quads agree with `land_global` (`PHYSICS.md`).

| # | BmAK | JC3 target | transform | now | proposed | conf | verify |
|---|---|---|---|---|---|---|---|
| T-CO1 | 32 boxes (bone, centre, extents) | `.physicsc` collision shapes | — | donor's shapes, stations moved | JC3 shapes now decode (G2-8): the donor's hulls are in `SHAPES.md`; the *write* side is still unproven | read | hull bbox of the built vehicle vs its mesh |
| T-CO2 | largest box 211×51×109 cm | — | scale 1 cm = 1 unit | — | cannot be transferred until T-CO1 is unblocked; the chassis is JC3-side by decision | blocked | no scrape/clip through the drop |
| T-CO3 | — | `parts[].has_world_collision_shape` | — | donor's | blocked (G2-7) | blocked | — |

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
| T-CO1, T-CO2 | the **write** side of `.physicsc` (reading is G2-8, solved) | a working `.physicsc` writer, or keep the donor chassis |
| T-AU3 | 10 banks absent from the install | nothing — the assets do not exist |
| T-FX3 | the `usage_effects[].usage` hash vocabulary | a fleet-wide dump of usage names (12 exist) |
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
  fleet's 17; the Batmobile's signature VFX have no JC3 usage slot (T-FX3), which is a feature
  gap, not a translation gap.
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
