# FX-12 / FX-16 — the JC3 tracer carrier and the BmAK round trail

Task: decode the `WeaponTuning` members that set a vehicle weapon's tracer texture, colour, length,
width and speed; give the real values on the tank cannon, the Vulcan-like minigun and the APC gun;
map every `Batmobile_CanonTrail` parameter onto a member with the unit bridge shown; say which part
of the trail look a private tune copy can reach and which it cannot; and name the closest JC3 system
plus the gap for the build (STAGES.md rule).

**Verdict.**

* The tracer carrier is real and it is a tune, not an effect: **eight members** under
  `bullet_weapon[].tuning.bullet_base_tuning` (player) and the same eight under
  `bullet_weapon[].ai_tuning.bullet_base_tuning` (AI). Texture, length, width, speed, TTL and three
  smoke-trail companions are floats/uint8s; **colour does not exist in any of the three decoded ADF
  weapon classes** (0 of 97 member names in the tank cannon's class instance; 0 of the 22 fleet ids
  in `WEAPONS.md` §12). The texture is an **enum byte** (`tracer_texture_type` = 1 on every vehicle
  bullet weapon), not a path, and which `.ddsc` enum 1 selects is **UNKNOWN** — no data file names it.
* Real values, player block, absolute byte offset in the extracted `.wtunec`:
  tank cannon `tracer_fire_velocity` 900.0 @0x180, `tracer_fire_length` 30.0 @0x184,
  `tracer_fire_width` 0.5 @0x188; minigun 750.0 @0x180, 20.0 @0x184, 0.05 @0x188;
  APC gun 600.0 @0x180, 15.0 @0x184, 0.03 @0x188. Full tables in §4.
* A private `.wtunec` copy **can** reach the trail's *linear* half: a 0.5 m wide streak (the BmAK
  ribbon is 50 uu = 0.50 m — already an exact match on the tank cannon), its length, its stretch
  speed, a 1.25 s life and a smoke ribbon on the tracer. It **cannot** reach the trail's *art* half:
  two emitters (ribbon + sprite), two StartColors with alphas, `ColorScaleOverLife`
  `(0,1,1)→(4,3,1)`, per-emitter lifetimes 0.035–0.05 s vs 1.25 s, spawn rates 1/s and 8/s, the
  −50 uu sprite offset, ribbon tiling, or the two materials `Engine.Rocket_Trail` /
  `Engine.fx_Glowinglow_m`. None of those has a tune member, and BmAK binds the system to the
  **projectile** (`RBasicProjectile.ProjectileTrail`) while JC3's bullet tune has no such member.
* Closest JC3 system for that half: the `.effc` effect system (`EffectRTSystem`, 25,025 files)
  carried inside a weapon `.ee` — the fleet's own projectile-trail example is
  `effects/jc_weapons/missile/missile_trail_car.effc`, shipped in `w618_sportsmuscle_missile.ee`.
  Gap: no decoded JC3 carrier attaches a particle system to a **bullet** in flight. Build action
  (STAGES.md BUILD: "compose several systems where the closest one is short"): author a private
  `.effc` reproducing the two emitters and bind it where a weapon bundle can, or carry the trail
  look in the tracer streak and accept that the two-emitter composition is not a tune value.

---

## 1. Method and how to read the offsets

* **JC3 side.** `Tools/scripts/jc3weapons.py` already extracts every tune and decodes every member
  (`WEAPONS.md`, `WEAPONS.jsonl`, `WEAPONS_SHARED.json`). It decodes values, not positions, so this
  report re-walks the same ADF v4 files with a position-tracking copy of `jc3adf._read`
  (`tmp/fx12_probe.py`, imports `jc3adf`/`jc3weapons`, adds no reader).
  **Offset = absolute byte in the extracted `.wtunec` file.** In all three files the root instance
  starts at **0x50 (80)**, which is also the data block start; array elements live at
  `data_off + the 16-byte array header's data-relative pointer`, so they are absolute too.
  Mount precedence is patch > dlc > base (`jc3weapons.MOUNT_RANK`), so the patch `.wtunec` is the
  authoritative copy of a weapon that ships one.
* **BmAK side.** Numbers come from the G1-6 grab tables. Offsets there are of two kinds and both are
  quoted as the grab stores them: **export property-tag offsets** from
  `Research/BatmobileGrab/objects.jsonl` (`offset`, within the export payload; `size` is the export
  size) and the **class field offsets** in `Research/BatmobileGrab/WEAPONS.md` §0 (hex, within the
  export).
* Nothing here was measured in game (TEST stage not lifted): every value is a file read.

## 2. The three tunes read

| weapon | role here | authoritative file | archive location | bytes | sha1 |
|---|---|---|---:|---:|---|
| `w602_mediumtank_canon` | tank cannon (BmAK cannon) | `editor/entities/jc_weapons/06_vehicle/w602_mediumtank_canon/w602_mediumtank_canon.wtunec`, mount **patch** | `patch_win64/game1` @441,880,576 (`INDEX.jsonl:38665`) | 14,224 | `1a8c072ab67e65d5d5620f4e3441b19bd75554b6` |
| `w603_mediumtank_mgun` | Vulcan-like minigun | `editor/entities/jc_weapons/06_vehicle/w603_mediumtank_mgun/w603_mediumtank_mgun.wtunec`, mount **patch** | `patch_win64/game1` @441,894,912 (`INDEX.jsonl:38666`) | 14,223 | `d9f58989839c371729e8268e47406a4fda4ccea1` |
| `w206_mounted_capstone_m2hm` | APC gun (APC has **0 driver slots**, 1 gunner slot: `WEAPON_WIRING.md:188`) | inner tune of `editor/entities/jc_vehicles/01_land/v0200_car_capstone_apc/v0200_car_capstone_apc_debug.ee`, mount **base** | `.ee` at `archives_win64/game35` @160,751,616 +6,093,712 B (`INDEX.jsonl:37237`); inner entry at stream offset **14,517,720**, 12,677 B | 12,677 | `20f90fb24b9d18ffd814fa84202876e34f34ba55` |

Root instance size: **824 B** (w602, w603), **736 B** (w206 — it carries fewer optional members, which
is why its `ai_tuning` block starts at 0x294 instead of 0x2C0).

## 3. The carrier: the eight tracer members

Path: `bullet_weapon[0].{tuning|ai_tuning}.bullet_base_tuning.*` in class `WeaponTuning`
(ADF v4). The player block is `tuning`, the AI block is `ai_tuning` (`WEAPONS.md` §10 labels them
"player" and "ai"). A driver-fired shot is the player block.

| member | type | sets | unit | reachable by tune copy |
|---|---|---|---|---|
| `tracer_texture_type` | uint8 | which tracer texture the engine draws | enum (1 on all 22 ids) | value yes, *binding* no (see §5) |
| `tracer_fire_velocity` | float | stretch speed of the streak | m/s | yes |
| `tracer_fire_length` | float | streak length | m | yes |
| `tracer_fire_width` | float | streak width | m | yes |
| `tracer_expand_width` | float | width growth (closest JC3 analogue of size-over-life) | UNKNOWN (m? m/s?) | yes |
| `tracer_time_to_live` | float | how long the streak lives | s | yes |
| `smoke_trail_tile_size` | float | tile size of the smoke ribbon on the tracer | m | yes |
| `tracer_per_smoke_trail` | uint8 | how often a tracer gets a smoke ribbon (0 = off) | count/interval, semantics UNKNOWN | yes |
| `bullets_per_tracer` | uint8 | 1 tracer per N bullets | count | yes |

**Colour: no member.** The whole `WeaponTuning` class as decoded over all 22 ids (`WEAPONS.md` §12)
has **no** member whose name contains colour/color/tint, and no material path. The only
texture-related member in the class is `tracer_texture_type`.

## 4. Real values, with byte offsets

### 4.1 `w602_mediumtank_canon` — tank cannon

| member | player block value @offset | AI block value @offset |
|---|---|---|
| `tracer_fire_velocity` | **900.0** @0x180 (384) | 750.0 @0x2C0 (704) |
| `tracer_fire_length` | **30.0** @0x184 (388) | 0.5 @0x2C4 (708) |
| `tracer_fire_width` | **0.5** @0x188 (392) | 0.1 @0x2C8 (712) |
| `tracer_expand_width` | 0.0 @0x18C (396) | 2.0 @0x2CC (716) |
| `tracer_time_to_live` | **0.0** @0x190 (400) | 0.4 @0x2D0 (720) |
| `smoke_trail_tile_size` | 5.0 @0x198 (408) | 5.0 @0x2D8 (728) |
| `tracer_per_smoke_trail` | 1 @0x19C (412) | 1 @0x2DC (732) |
| `bullets_per_tracer` | 1 @0x19D (413) | 1 @0x2DD (733) |
| `tracer_texture_type` | **1** @0x1A0 (416) | 1 @0x2E0 (736) |

Round, same file: `velocity` **500.0** @0x9C (156), `fire_rate` **1.75** @0xA0 (160) — s/shot.

### 4.2 `w603_mediumtank_mgun` — Vulcan-like minigun

| member | player block value @offset | AI block value @offset |
|---|---|---|
| `tracer_fire_velocity` | **750.0** @384 | 750.0 @704 |
| `tracer_fire_length` | **20.0** @388 | 40.0 @708 |
| `tracer_fire_width` | **0.05** @392 | 0.05 @712 |
| `tracer_expand_width` | 2.0 @396 | 2.0 @716 |
| `tracer_time_to_live` | **0.25** @400 | 0.25 @720 |
| `smoke_trail_tile_size` | 0.0 @408 | 5.0 @728 |
| `tracer_per_smoke_trail` | **0** @412 (off) | 1 @732 |
| `bullets_per_tracer` | 1 @413 | 1 @733 |
| `tracer_texture_type` | **1** @416 | 1 @736 |

### 4.3 `w206_mounted_capstone_m2hm` — APC gun (inner tune, offsets inside the 12,677 B `.wtunec`)

| member | player block value @offset | AI block value @offset |
|---|---|---|
| `tracer_fire_velocity` | **600.0** @384 | 900.0 @660 |
| `tracer_fire_length` | **15.0** @388 | 5.0 @664 |
| `tracer_fire_width` | **0.03** @392 | 0.02 @668 |
| `tracer_expand_width` | 2.0 @396 | 2.0 @672 |
| `tracer_time_to_live` | **0.0** @400 | 0.5 @676 |
| `smoke_trail_tile_size` | 5.0 @408 | 5.0 @684 |
| `tracer_per_smoke_trail` | **3** @412 | 4 @688 |
| `bullets_per_tracer` | 1 @413 | 1 @689 |
| `tracer_texture_type` | **1** @416 | 1 @692 |

Cross-checks against the pre-existing decode: `WEAPONS.md` §6 prints 900/30/0, 750/20/0.25 and
100/30/0 for w602/w603/w616 — the 18,000-word fleet table rows agree with the player block here
(w616 corvette canon is the outlier with tracer velocity 100 and length 30).

## 5. Texture and colour: what the data does and does not carry

**Texture.** `tracer_texture_type` is a `uint8` = **1** on every one of the 11 fleet bullet weapons
(both blocks; `WEAPONS.md` §12: uint8, 11 ids, min 1, max 1) and 1 on the APC gun. Three tracer
textures exist in the archives, none referenced by any tune member (so the enum→asset mapping is
engine-side):

| asset | archive | offset | size |
|---|---|---:|---:|
| `textures/bullet_tracer_dif.ddsc` | `archives_win64/game5` | 406,405,120 | 11,152 |
| `textures/bullet_tracer_noise_dif.ddsc` | `archives_win64/game1` | 512,380,928 | 87,536 |
| `textures/bullet_tracer_smoke_dif.ddsc` | `archives_win64/game1` | 512,491,520 | 22,000 |

(`Research/JC3Grab/INDEX.jsonl:80483`, `:80484`, `:80485`.) **UNKNOWN:** which of the three
enum 1 selects, and what values 2…n do; no decoded file names the mapping. What would settle it:
the material the engine binds for enum 1 (a shader/material dump), or a one-shot in-game probe that
swaps a `.ddsc` and watches the streak.

**Colour.** Absent three ways, all checkable:
1. `WeaponTuning` member vocabulary over all 22 ids: 0 colour/color/tint names (`WEAPONS.md` §12).
2. The tank cannon's own class instance exposes **97** distinct member names; the only
   texture/material-ish one is `tracer_texture_type` (`tmp/fx12_probe.py` output `hit_terms`).
3. The particle side is no better: `.effc` (25,025 files) publishes **700** collapsed member paths
   (`FX.md` §"What is inside") and none is colour-named; `.ctunec`/`.trim` vocabulary likewise
   (`FX_VOCAB.json`, 0 matches for `Colour|Color|Tint|Tracer`).

So a JC3 tracer's colour arrives with the texture art, not with a value. That is the honest ceiling
of the tune.

## 6. Unit bridge

JC3 world units are metres and the project's established transform is `uu * 0.01`:
`Research/BatmobileGrab/SOCKETS_JC3.md:10` ("`to_jc3_rot(p) * 0.01 + offset`"), with the same
"1 uu = 1 cm" stated for BmAK data in `PHYSICS.md:3` and `WEAPONS.md:15` (cm for positions, cm/s for
speeds, 16-bit rotators). Corroboration on this task's own numbers: BmAK cannon round
`Projectile.Speed` = 40000.0 cm/s = **400 m/s**, and the build's private cannon tune already carries
`velocity` = **400.0** m/s (`Builds/bm-RC3-parts/.../w602_batmobile_cannon.wtunec`).

| quantity | BmAK | JC3 member unit | bridge | error |
|---|---|---|---|---|
| width / length / offset | uu | m | `m = uu / 100` | exact (integer uu → 2 dp) |
| speed | cm/s | m/s | `m/s = cm/s / 100` | exact |
| lifetime / TTL | s | s | 1:1 | none |
| spawn / fire rate | 1/s | `fire_rate` = s per shot | `s = 1 / Hz` | only for shots, not trail particles |
| colour | linear RGBA float | — | **no member** | — |

## 7. `Batmobile_CanonTrail` decoded (BmAK side)

Source: `Particles.Rocket.Batmobile_CanonTrail`, package **`Playable_Batmobile_SF`**, export **4978**,
export size **193 B**, `ParticleSystem`, 2 emitters, 2 LOD levels
(`PARTICLES.json`; tables at `PARTICLES.md:510` and `PARTICLES.md:3769–3773`;
summary `PARTICLES_FEATURES.md:158`).

| parameter | value | evidence (export / property-tag offset) |
|---|---|---|
| emitter count / kinds | 2 — 1 **ribbon**, 1 **sprite**, both `ParticleSpriteEmitter` | `PARTICLES.json` system 4978; `Emitters` ArrayProperty @104 |
| emissive binding | `RBasicProjectile.ProjectileTrail` → `…Primary_Projectile.RocketTrail` → system `Particles.Rocket.Batmobile_CanonTrail` (2 emitters), packages Batmobile / MK2 / Funhouse | `Research/BatmobileGrab/WEAPONS.md:368` |
| round speed (the thing the trail follows) | **40000.0** cm/s (max 48000.0) → 400 m/s | `Playable_Batmobile_SF` export **15** `Batmobile_Heavy_Cannon_Primary_Projectile`, `FloatProperty` tag @668 = 40000.0, @672 = 48000.0 |
| **ribbon** emitter 4870 (level 1214) | | |
| ribbon StartSize | **[50.0, 0.0, 0.0]** uu → **0.50 m** | `ParticleModuleSize` export 3480, `StartSize` @96; `PARTICLES.md:3769` |
| ribbon Lifetime | **1.25 s** | `ParticleModuleLifetime` export 2241, `Lifetime` @96 |
| ribbon Spawn Rate | **8.0 /s** | `ParticleModuleSpawn` export 4048, `Rate` @100, `RateScale` @136 |
| ribbon type data | int **250** @104, int **50** @108, bool **true** @112, float **800.0** @124; grab labels 104 "beam length", 112 "tiles" | `ParticleModuleTypeDataRibbon` export 4274 (`grab_particles.py:247–248` maps 0x68/0x70/0x74/0x78) |
| ribbon modules | Size, SizeMultiplyLife, Lifetime, Spawn, **VelocityOverLifetime**, Color, ColorScaleOverLife, TypeDataRibbon | `PARTICLES.json` emitter 4870 |
| **sprite** emitter 4871 (level 1215) | | |
| sprite StartLocation | **[-50.0, 0.0, 0.0]** uu → **−0.50 m** (behind the round) | `ParticleModuleLocation` export 2410, `StartLocation` @96; `PARTICLES.md:3773` |
| sprite Lifetime | **0.035 … 0.05 s** (uniform min/max) | `ParticleModuleLifetime` export 2242, `Lifetime` @96 (`size` 121 vs 50 = two-point distribution) |
| sprite Spawn Rate | **1.0 /s** | `ParticleModuleSpawn` export 4049, `Rate` @100, `BurstList` @176 |
| sprite modules | Size, SizeMultiplyLife, Lifetime, Spawn, Location, Rotation, Color (**no** Velocity) | `PARTICLES.json` emitter 4871 |
| **colour** (system) | `StartColor (0.5, 1.0, 0.5)` alpha **0.5**; `StartColor (3.0, 1.0, 0.5)` alpha **0.3**; `ColorScaleOverLife` min `(0,1,1)` max `(4,3,1)` | `ParticleModuleColor` exports **1678, 1679**, `StartColor` @96, `StartAlpha` @160; `PARTICLES_FEATURES.md:158` |
| materials | **`Engine.Rocket_Trail`**, **`Engine.fx_Glowinglow_m`** | `PARTICLES_FEATURES.json` (system 4978 `materials`) |

Two honest limits on the BmAK side: (a) which of the two `ParticleModuleColor` exports belongs to the
ribbon and which to the sprite is **not recorded** by the grab (both have outer
`Rocket.Batmobile_CanonTrail`), so the per-emitter colour assignment is **UNKNOWN**; (b) the ribbon's
`VelocityOverLifetime` curve values are **not decoded** by G1-6, so the trail's own particle speed is
**UNKNOWN** — only the round speed it follows is known (400 m/s). Also, the int at tag @104 = 250 is
labelled "beam length" by the grab, but the UE property name behind that tag was not recovered: whether
250 is a distance in uu (2.50 m) or a segment count is **UNKNOWN**, so §8 bridges it as "no exact
member" rather than converting it.

## 8. Mapping every trail parameter onto a member

| BmAK trail parameter | value | JC3 member | unit bridge | verdict |
|---|---|---|---|---|
| trail bound to the round | `ProjectileTrail` on the projectile archetype | **none** — no effect/trail member in `WeaponTuning`'s 97 members | — | **gap** (§10) |
| ribbon StartSize (width) | 50 uu = 0.50 m | `…bullet_base_tuning.tracer_fire_width` | `50/100 = 0.50 m` | **exact**, w602 is already **0.5** @0x188 |
| ribbon Lifetime | 1.25 s | `tracer_time_to_live` | 1:1 | **reachable** (w602 0.0 @0x190 → 1.25; fleet max 2.0) |
| sprite Lifetime | 0.035–0.05 s | `tracer_time_to_live` only | 1:1 but one value | **partial**: JC3 has no second, distributed lifetime |
| ribbon Spawn Rate | 8.0 /s | none; closest `tracer_per_smoke_trail` (uint8) | — | **partial**: smoke ribbon on/off, not a particle rate |
| sprite Spawn Rate | 1.0 /s | none | — | **gap** |
| sprite StartLocation | −50 uu = −0.50 m | none | — | **gap** (no offset member; the streak is centred on the bullet) |
| StartColor ×2 + alphas + ColorScaleOverLife | (0.5,1,0.5) α0.5; (3,1,0.5) α0.3; (0,1,1)→(4,3,1) | **none** | — | **gap**: colour rides the texture art |
| materials `Engine.Rocket_Trail` / `Engine.fx_Glowinglow_m` | 2 | `tracer_texture_type` = 1 (enum) | none | **gap**: enum value only; mapping UNKNOWN |
| ribbon beam length / tiles | int 250, bool true (+int 50, float 800.0) | closest `tracer_fire_length` = 30 m | uu→m only if 250 is a distance | **partial/UNKNOWN** |
| `VelocityOverLifetime` (ribbon only) | values not decoded | closest `tracer_fire_velocity` = 900 m/s | cm/s → m/s | **partial**: stretch speed, not trail-particle motion |
| size over life (`SizeMultiplyLife`, both emitters) | curve not decoded | `tracer_expand_width` (0.0 on w602) | UNKNOWN | **partial** |
| round speed the trail follows | 40000 cm/s = 400 m/s | `velocity` (w602 vanilla 500.0 @0x9C; private copy 400.0) | `/100` | **exact**, already matched in the build |

Counting the user's five facets explicitly:

| facet | member | exists? | tank cannon | minigun | APC gun |
|---|---|---|---|---|---|
| texture | `tracer_texture_type` (uint8) | yes, **enum only** | 1 @0x1A0 | 1 @0x1A0 | 1 @0x1A0 |
| colour | — | **no** | — | — | — |
| length | `tracer_fire_length` (+ `tracer_expand_width`) | yes | 30.0 @0x184 | 20.0 @0x184 | 15.0 @0x184 |
| width | `tracer_fire_width` | yes | 0.5 @0x188 | 0.05 @0x188 | 0.03 @0x188 |
| speed | `tracer_fire_velocity` | yes | 900.0 @0x180 | 750.0 @0x180 | 600.0 @0x180 |

## 9. What a private tune copy reaches, and what it does not

**The route is already proven in this repo.** The build ships private copies of these very tunes:

* `Builds/bm-RC3-parts/aaf/editor/entities/jc_weapons/06_vehicle/w602_batmobile_cannon/w602_batmobile_cannon.wtunec`
  — instance name `w602_mediumtank_canon.wtune`, 824 B, `velocity` **400.0**, `fire_rate` **2.0**,
  tracer members untouched (900/30/0.5/0/0/1/1/1).
* `Builds/bm-RC3-parts/aaf/editor/entities/jc_weapons/06_vehicle/w603_batmobile_vulcan/w603_batmobile_vulcan.wtunec`
  — `fire_rate` **0.138**, `velocity` **750.0**, tracer members untouched (750/20/0.05/2/0.25/0/1/1).

Because a patch-mount `.wtunec` outranks the base copy (`jc3weapons.MOUNT_RANK`; `WEAPONS.md` §1:
"loose patch `.wtunec` overrides"), editing these eight members in a private tree is a real lever.

**Reachable by editing a private tune copy**

1. Width: `tracer_fire_width` → **0.5 m** already equals the 50 uu ribbon width. No edit needed on
   the cannon; the minigun (0.05) and APC (0.03) would need it if they must match the trail.
2. Length: `tracer_fire_length` (30 m on the cannon; the ribbon's own 250-uu number cannot be
   converted with confidence — §7).
3. Speed: `tracer_fire_velocity` (900 m/s) — the streak's stretch rate, independent of the round's
   `velocity` (500 m/s).
4. Life: `tracer_time_to_live` → **1.25 s** matches the ribbon lifetime exactly.
5. Smoke ribbon: `tracer_per_smoke_trail` (currently **1** on the cannon, **0** on the minigun,
   **3** on the APC) and `smoke_trail_tile_size` (5.0 m) — a real smoke trail *on the tracer*, and the
   closest thing the tune has to the BmAK trail.
6. Tracer ratio: `bullets_per_tracer`.
7. The texture enum *value* (`tracer_texture_type`), with the caveat that only `1` is observed in the
   fleet, so no claim is made about what other values would draw.

**Not reachable — and this is the part the build must add**

* Colour of any kind (two StartColors, two alphas, the `ColorScaleOverLife` ramp).
* Material / texture identity: the tune carries an enum, not `Engine.Rocket_Trail`,
  `Engine.fx_Glowinglow_m`, or `bullet_tracer_dif`.
* Two-emitter composition: one ribbon **and** one sprite with different lifetimes (1.25 s vs
  0.035–0.05 s) and different spawn rates (8/s vs 1/s). The tracer is a single stretched texture per
  bullet.
* The sprite's −50 uu lead-in offset, ribbon tiling/segment properties, the ribbon's
  velocity-over-lifetime curve, and the per-emitter size-over-life curves.

## 10. Closest JC3 system and the gap (STAGES.md)

STAGES.md is explicit: **"'JC3 has no system' is never an answer. Find the closest JC3 system, record
it with member paths and values, and name the gap; the build stage closes the gap (compose, clone,
author, repack)."** (`STAGES.md:4`), and BUILD works "offline, into NEW private trees
(`Builds/bm-RC4*`): edit private copies of tunes/modules/entities/effects, author
geometry/textures/banks, **compose several systems where the closest one is short**"
(`STAGES.md:10`).

* **Closest system (look carrier):** the `.effc` effect system — root class `EffectRTSystem`, 25,025
  files in the game (`FX.md`), carried inside weapon `.ee` bundles. The fleet's own projectile-trail
  example is `effects/jc_weapons/missile/missile_trail_car.effc` (11,199 B; 1,412 value rows;
  179 arrays; 36 types), which ships **inside** `w618_sportsmuscle_missile.ee`
  (`FX_TABLE.jsonl:56822`) and inside the donor's signature `.ee` (`FX_TABLE.jsonl:27583`).
  That is the system type that can hold the two emitters, their colours and materials.
* **Closest system (tune carrier):** `bullet_base_tuning` smoke-trail members
  (`tracer_per_smoke_trail`, `smoke_trail_tile_size`) — the only tune values that make a bullet leave
  a ribbon at all.
* **The gap, stated exactly:** BmAK binds the trail to the **round** (`RBasicProjectile.ProjectileTrail`
  on the projectile archetype). JC3's bullet tune has **no** effect/trail member (0 of 97), and the
  only trail effect shipped in a weapon bundle belongs to a **missile** weapon and is attached at
  vehicle sockets (`MissileL/R`, `MODLOG.md:12349`), not proven on a flying bullet. So no decoded
  JC3 carrier reproduces "a two-emitter ribbon+sprite trail that follows the cannon round".
* **Build action:** in a `Builds/bm-RC4*` tree, author a private `.effc` that reproduces the two
  `Batmobile_CanonTrail` emitters (ribbon 0.5 m wide, 1.25 s, 8/s, tiled; sprite 0.035–0.05 s, 1/s,
  −0.5 m; the two StartColors and the `(0,1,1)→(4,3,1)` ramp; `Engine.Rocket_Trail` /
  `Engine.fx_Glowinglow_m` art), ship it in the cannon's weapon bundle next to the tune, and bind it
  where the bundle can; carry the linear half in the tracer members so the round still reads as a
  streak if the effect binding is not reachable. If a `.ddsc` swap is chosen for the streak art, the
  three tracer textures in §5 are the files to carry, ordered by the texture's role (dif / noise /
  smoke) with the enum mapping still UNKNOWN.
* **What must not be done:** no donor value "for character", no row dropped. The linear parameters
  are `exact`; the art half is `closest + gap + build action` per the TRANSLATE contract
  (`STAGES.md:9`).

## 11. Evidence index

| # | path | what it proves |
|---|---|---|
| 1 | `E:/Modding/_shared/gamedata/JC3grab/weapons/w602_mediumtank_canon/w602_mediumtank_canon.wtunec` (patch @441,880,576) | tank cannon tune, all §4.1 values at their offsets |
| 2 | `…/w603_mediumtank_mgun/w603_mediumtank_mgun.wtunec` (patch @441,894,912) | minigun tune, §4.2 |
| 3 | `…/v0200_car_capstone_apc_debug.ee` inner `w206_mounted_capstone_m2hm.wtunec` (stream 14,517,720) | APC tune, §4.3 |
| 4 | `Research/JC3Grab/WEAPONS.md` §6, §10, §12 | fleet tracer table, player/AI block naming, member vocabulary (colour absent) |
| 5 | `Research/JC3Grab/WEAPONS.jsonl`, `WEAPONS_SHARED.json` | the same decode in machine form (w206 is a shared tune) |
| 6 | `Research/JC3Grab/INDEX.jsonl:38665`, `:38666`, `:37237` | archive offsets/sizes of the three files |
| 7 | `Research/JC3Grab/INDEX.jsonl` tracer-texture rows | `bullet_tracer_{dif,noise_dif,smoke_dif}.ddsc` paths/offsets |
| 8 | `Research/JC3Grab/FX_TABLE.jsonl:56822`, `:27583` | `missile_trail_car.effc` shipped in w618's and the donor's `.ee` |
| 9 | `Research/JC3Grab/FX.md`, `FX_VOCAB.json` | 25,025 `.effc` / 700 member paths, 0 colour-named |
| 10 | `Research/BatmobileGrab/PARTICLES.json` (`Playable_Batmobile_SF` 4978, emitters 4870/4871) | CanonTrail graph, module lists, beam dict |
| 11 | `Research/BatmobileGrab/PARTICLES.md:510`, `:3769–3773` | system row and per-emitter start_size / beam / start_location |
| 12 | `Research/BatmobileGrab/PARTICLES_FEATURES.md:158`, `PARTICLES_FEATURES.json` | lifetimes, spawn rates, colours, materials |
| 13 | `Research/BatmobileGrab/objects.jsonl` (SF 5069; modules 1678/1679, 2241/2242, 2410, 3479/3480, 4048/4049, 4274; projectile 15) | property-tag byte offsets used in §7 |
| 14 | `Research/BatmobileGrab/WEAPONS.md:368` (Flight and impact FX), §0 | `ProjectileTrail` binding, speed 40000.0 @668, units cm/cm-per-s |
| 15 | `Research/BatmobileGrab/SOCKETS_JC3.md:10`, `PHYSICS.md:3`, `WEAPONS.md:15` | the 1 uu = 1 cm ↔ JC3 metre bridge (`×0.01`) |
| 16 | `STAGES.md:4`, `:9`, `:10` | closest-system rule, TRANSLATE row contract, BUILD compose/author mandate |
| 17 | `Builds/bm-RC3-parts/…/w602_batmobile_cannon.wtunec`, `…/w603_batmobile_vulcan.wtunec` | private-copy route already in use; tracer values still vanilla |
| 18 | `tmp/fx12_probe.py` | the offset walker that produced every JC3 offset here |

## 12. UNKNOWN / limits

1. **Enum → texture**: `tracer_texture_type` = 1 on all 11 bullet weapons; no decoded file maps 1 to
   `bullet_tracer_dif` / `_noise_dif` / `_smoke_dif`. Settle with the material the engine binds, or a
   texture-swap probe.
2. **`tracer_expand_width` unit**: a float (0…2); no file states whether it is metres, m/s or a
   multiplier. It is the closest analogue of size-over-life, but the bridge is not derived.
3. **`tracer_per_smoke_trail` semantics**: values 0…4 across the fleet; the name implies an interval
   or a count between smoke-carrying tracers, but no doc says which. Not converted.
4. **Ribbon tag @104 = 250**: grab-labelled "beam length"; the UE property name was not recovered, so
   250 may be uu (2.50 m) or a segment count. Not bridged.
5. **Ribbon `VelocityOverLifetime` curve**: module present, values not captured by G1-6. The trail's
   own particle speed is UNKNOWN.
6. **Per-emitter colour assignment**: the two `ParticleModuleColor` exports (1678, 1679) are not keyed
   to emitter 4870/4871 in the grab; both StartColors are system-level facts only.
7. **No in-game look** (R6/TEST not lifted): that the edited values produce the intended streak is a
   Q-1 #5 probe, not a measurement.
8. **Evidence-scope note:** the `WeaponTuning` vocabulary is the 22 `06_vehicle` ids plus the shared
   w206 tune; a bullet tune outside those (if any) is uncovered.

## 13. Reproduction

```
python tmp/fx12_probe.py           # every JC3 offset/value in §4 (walks w602/w603 + w206's inner tune)
python Tools/scripts/jc3weapons.py --check   # the underlying decode and the doc are unchanged
```

`tmp/fx12_probe.py` adds no reader: it imports `jc3adf`/`jc3weapons`, walks the same ADF v4 files and
prints `(member, type, value, absolute byte offset)` for the tracer block, plus the class's member-name
inventory that proves the colour/material absence.
