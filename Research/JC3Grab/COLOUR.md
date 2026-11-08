# JC3 paint and colour pipeline (G3-09, desk part)

What makes a JC3 car the colour it is, read out of the donor entity's own bytes. Card: `GRAB_BACKLOG.md` §6b `G3-09`. Evidence is labelled the project's way:

* **decoded** - a project decoder read it; the file and offset/path is given;
* **derived** - a rule plus its inputs, stated;
* **UNKNOWN** - what was tried and where the answer would be.

No value below comes from a shader source that is not on disk: the only shader evidence in the project is the reflection header quoted in MODLOG §78 (`jc-model-renderer`'s `carpaintmm.fb.txt`), which names the parameters and samplers but does not contain the shader body.

## 1. The CarPaintMM block, as decoded

`rbm_geom.decode` reads it and `rbm_geom`'s re-encode of every block of `sportsmuscle_body_lod1.rbm` is **byte-identical** - that round trip is the oracle for the field order, field sizes and every payload offset below.

| payload offset | field | bytes | source of the name |
|---|---|---|---|
| `0x0` | `version` | 1 | decoder field order |
| `0x1` | `flags` | 4 | decoder field order |
| `0x5` | `unknown` | 4 | decoder field order |
| `0x9` | `static_params` | 288 | decoder field order |
| `0x129` | `static_support` | 28 | decoder field order |
| `0x145` | `dynamic_params` | 76 | decoder field order |
| `0x191` | `deform_table` | 1024 | decoder field order |

`static_params` is 18 float4 (288 B) and `static_support` 7 floats (28 B) - both **exactly** the sizes the reflection header's `CarPaintStaticMaterialParams` and its 7 support floats declare, which is why the header's names are used for the members but not for any value's meaning. `dynamic_params` is 76 B = 4 float4 + 3 floats, i.e. one float4 more than `TintColorR/G/B` + the three overrides.

### Per block (all 9 blocks of `sportsmuscle_body_lod1.rbm`)

| block | flags | bits | verts | tris | textures | dynamic 19 floats |
|---|---|---|---|---|---|---|
| 0 | `0x1004` | damage blend, IS_DEFORM (vertex weights) | 1024 | 1056 | car_undercarriage_sport01_dif.ddsc<br>car_undercarriage_sport01_nrm.ddsc<br>car_undercarriage_sport01_mpm.ddsc<br>a00_dummy_black_mpm.ddsc<br>damage2_nrm.ddsc<br>vehicle_metal_alpha_dif.ddsc<br>vehicle_dirt_msk.ddsc<br>a00_dummy_grey_dif.ddsc<br>a00_dummy_flat_nrm.ddsc<br>a00_dummy_black_mpm.ddsc<br>dummy_layered_dif.ddsc<br>dummy_layered_dif.ddsc | 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0.6, 0.2, 0 |
| 1 | `0x1004` | damage blend, IS_DEFORM (vertex weights) | 1061 | 1146 | car_undercarriage_sport01_dif.ddsc<br>car_undercarriage_sport01_nrm.ddsc<br>car_undercarriage_sport01_mpm.ddsc<br>a00_dummy_black_mpm.ddsc<br>damage2_nrm.ddsc<br>vehicle_metal_alpha_dif.ddsc<br>vehicle_dirt_msk.ddsc<br>a00_dummy_grey_dif.ddsc<br>a00_dummy_flat_nrm.ddsc<br>a00_dummy_black_mpm.ddsc<br>dummy_layered_dif.ddsc<br>dummy_layered_dif.ddsc | 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0.6, 0.2, 0 |
| 2 | `0x1004` | damage blend, IS_DEFORM (vertex weights) | 40 | 20 | car_undercarriage_sport01_dif.ddsc<br>car_undercarriage_sport01_nrm.ddsc<br>car_undercarriage_sport01_mpm.ddsc<br>a00_dummy_black_mpm.ddsc<br>damage2_nrm.ddsc<br>vehicle_metal_alpha_dif.ddsc<br>vehicle_dirt_msk.ddsc<br>a00_dummy_grey_dif.ddsc<br>a00_dummy_flat_nrm.ddsc<br>a00_dummy_black_mpm.ddsc<br>dummy_layered_dif.ddsc<br>dummy_layered_dif.ddsc | 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0.6, 0.2, 0 |
| 3 | `0x1000` | IS_DEFORM (vertex weights) | 636 | 792 | v0300_car_kensington_sportsmuscle_int_dif.ddsc<br>v0300_car_kensington_sportsmuscle_int_nrm.ddsc<br>v0300_car_kensington_sportsmuscle_int_mpm.ddsc<br>a00_dummy_black_mpm.ddsc<br>damage2_nrm.ddsc<br>vehicle_metal_alpha_dif.ddsc<br>vehicle_dirt_msk.ddsc<br>a00_dummy_grey_dif.ddsc<br>a00_dummy_flat_nrm.ddsc<br>a00_dummy_black_mpm.ddsc<br>dummy_layered_dif.ddsc<br>dummy_layered_dif.ddsc | 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0.6, 0.04, 0 |
| 4 | `0x1000` | IS_DEFORM (vertex weights) | 786 | 941 | v0300_car_kensington_sportsmuscle_int_dif.ddsc<br>v0300_car_kensington_sportsmuscle_int_nrm.ddsc<br>v0300_car_kensington_sportsmuscle_int_mpm.ddsc<br>a00_dummy_black_mpm.ddsc<br>damage2_nrm.ddsc<br>vehicle_metal_alpha_dif.ddsc<br>vehicle_dirt_msk.ddsc<br>a00_dummy_grey_dif.ddsc<br>a00_dummy_flat_nrm.ddsc<br>a00_dummy_black_mpm.ddsc<br>dummy_layered_dif.ddsc<br>dummy_layered_dif.ddsc | 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0.6, 0.04, 0 |
| 5 | `0x1000` | IS_DEFORM (vertex weights) | 343 | 395 | v0300_car_kensington_sportsmuscle_int_dif.ddsc<br>v0300_car_kensington_sportsmuscle_int_nrm.ddsc<br>v0300_car_kensington_sportsmuscle_int_mpm.ddsc<br>a00_dummy_black_mpm.ddsc<br>damage2_nrm.ddsc<br>vehicle_metal_alpha_dif.ddsc<br>vehicle_dirt_msk.ddsc<br>a00_dummy_grey_dif.ddsc<br>a00_dummy_flat_nrm.ddsc<br>a00_dummy_black_mpm.ddsc<br>dummy_layered_dif.ddsc<br>dummy_layered_dif.ddsc | 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0.6, 0.04, 0 |
| 6 | `0x101F` | decals, damage blend, dirt, IS_DEFORM (vertex weights) | 1081 | 1471 | v0300_car_kensington_sportsmuscle_body_dif.ddsc<br>v0300_car_kensington_sportsmuscle_body_nrm.ddsc<br>v0300_car_kensington_sportsmuscle_body_mpm.ddsc<br>v0300_car_kensington_sportsmuscle_body_msk.ddsc<br>damage2_alpha_nrm.ddsc<br>vehicle_metal_alpha_dif.ddsc<br>vehicle_dirt_msk.ddsc<br>vehicles_atlas_alpha_dif.ddsc<br>a00_dummy_flat_nrm.ddsc<br>a00_dummy_black_mpm.ddsc<br>dummy_layered_dif.ddsc<br>dummy_layered_dif.ddsc | 0.14, 0.19, 0.25, 1, 0, 1, 0, 0, 0, 0, 1, 0, 2, 0, 1, 1, 0.4, 1, 1 |
| 7 | `0x101F` | decals, damage blend, dirt, IS_DEFORM (vertex weights) | 823 | 1007 | v0300_car_kensington_sportsmuscle_body_dif.ddsc<br>v0300_car_kensington_sportsmuscle_body_nrm.ddsc<br>v0300_car_kensington_sportsmuscle_body_mpm.ddsc<br>v0300_car_kensington_sportsmuscle_body_msk.ddsc<br>damage2_alpha_nrm.ddsc<br>vehicle_metal_alpha_dif.ddsc<br>vehicle_dirt_msk.ddsc<br>vehicles_atlas_alpha_dif.ddsc<br>a00_dummy_flat_nrm.ddsc<br>a00_dummy_black_mpm.ddsc<br>dummy_layered_dif.ddsc<br>dummy_layered_dif.ddsc | 0.14, 0.19, 0.25, 1, 0, 1, 0, 0, 0, 0, 1, 0, 2, 0, 1, 1, 0.4, 1, 1 |
| 8 | `0x101F` | decals, damage blend, dirt, IS_DEFORM (vertex weights) | 281 | 235 | v0300_car_kensington_sportsmuscle_body_dif.ddsc<br>v0300_car_kensington_sportsmuscle_body_nrm.ddsc<br>v0300_car_kensington_sportsmuscle_body_mpm.ddsc<br>v0300_car_kensington_sportsmuscle_body_msk.ddsc<br>damage2_alpha_nrm.ddsc<br>vehicle_metal_alpha_dif.ddsc<br>vehicle_dirt_msk.ddsc<br>vehicles_atlas_alpha_dif.ddsc<br>a00_dummy_flat_nrm.ddsc<br>a00_dummy_black_mpm.ddsc<br>dummy_layered_dif.ddsc<br>dummy_layered_dif.ddsc | 0.14, 0.19, 0.25, 1, 0, 1, 0, 0, 0, 0, 1, 0, 2, 0, 1, 1, 0.4, 1, 1 |

The 3 blocks whose textures are the body's own `_body_dif` / `_body_nrm` / `_body_mpm` / `_body_msk` set are the paint zones: **blocks 6, 7, 8**. Their dynamic float4s are `(0.14, 0.19, 0.25, 1, 0, 1, 0, 0, 0, 0, 1, 0, 2, 0, 1, 1, 0.4, 1, 1), (0.14, 0.19, 0.25, 1, 0, 1, 0, 0, 0, 0, 1, 0, 2, 0, 1, 1, 0.4, 1, 1), (0.14, 0.19, 0.25, 1, 0, 1, 0, 0, 0, 0, 1, 0, 2, 0, 1, 1, 0.4, 1, 1)`; every non-paint block carries an identity first float4 instead (`1,0,0,0`).

## 2. Sampler slots

The block's texture table is a plain list; the slot index is the position. Mapped by the reflection header (MODLOG §78) and corroborated by the suffix of the texture each slot actually names on the paint blocks:

| slot | shader sampler | paint-block texture | role |
|---|---|---|---|
| 0 | s0 Diffuse | `v0300_car_kensington_sportsmuscle_body_dif.ddsc` | albedo (sRGB) |
| 1 | s1 Normal | `v0300_car_kensington_sportsmuscle_body_nrm.ddsc` | normal |
| 2 | s2 PropertyMap (mpm) | `v0300_car_kensington_sportsmuscle_body_mpm.ddsc` | PropertyMap: channel selectors |
| 3 | s3 TintMap (msk) | `v0300_car_kensington_sportsmuscle_body_msk.ddsc` | TintMap: per-channel tint amount |
| 4 | s4 DamageNormal | `damage2_alpha_nrm.ddsc` | shared, feature off |
| 5 | s5 DamageAlbedo | `vehicle_metal_alpha_dif.ddsc` | shared, feature off |
| 6 | s6 DirtMap | `vehicle_dirt_msk.ddsc` | shared, feature off |
| 7 | s7 Decal albedo | `vehicles_atlas_alpha_dif.ddsc` | shared, feature off |
| 8 | s8 Decal normal | `a00_dummy_flat_nrm.ddsc` | shared, feature off |
| 9 | s9 Decal property | `a00_dummy_black_mpm.ddsc` | shared, feature off |
| 10 | s10 (unused by the header) | `dummy_layered_dif.ddsc` | shared, feature off |
| 11 | s11 (unused by the header) | `dummy_layered_dif.ddsc` | shared, feature off |

`s0`-`s3` are per-material; `s4`-`s11` are the shared damage/dirt/decal slots. The paint blocks' flags include the dirt/damage/soft-tint bits, so those samplers are live on the body - the paint colour is not `s0` alone.

## 3. Static versus dynamic

**Static** (per block, authored, cannot change without rewriting the `.rbm`): the 18 float4 named `SpecularGloss`, `Metallic`, `ClearCoat`, `Emissive`, ... and the 7 support floats `Decals`, `DmgBlend`, `Layered`, `Overlay`, `Rotating`, `Dirt`, `SoftTint`.

**Dynamic** (the 4 float4 + 3 floats at payload `0x145`, 76 B): the fields the engine can drive per spawn. The reflection header names three colour vectors `TintColorR/G/B` plus gloss/metallic/clearcoat overrides, which accounts for 60 of the 76 bytes; **which of the four float4 is which is UNKNOWN** - see §6.

## 4. How a vanilla car's paint colour is chosen

**The palette module.** `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_palette.vmodc` (1897 B, ADF v4 types `A[Tint]`, `ColorRGBA`, `HashString`, `Palette`, `Tint`) holds **10 tint records**:

| # | name | occurrence | tint_r = tint_g = tint_b (RGB) | A | gloss | metallic | clear coat |
|---|---|---|---|---|---|---|---|
| 0 | White | 100 | (0.8800, 0.8800, 0.8800) | 1.00 | 0.000 | 0.000 | 1.000 |
| 1 | Evergreen Pearl | 100 | (0.0941, 0.2294, 0.1647) | 1.00 | 0.450 | 1.000 | 1.000 |
| 2 | Garnet Red Metallic | 100 | (0.4265, 0.0500, 0.0500) | 1.00 | 0.450 | 1.000 | 1.000 |
| 3 | Black | 100 | (0.2000, 0.2000, 0.2000) | 1.00 | 0.000 | 0.000 | 1.000 |
| 4 | Grey | 100 | (0.4107, 0.4107, 0.4107) | 1.00 | 0.450 | 1.000 | 1.000 |
| 5 | Silver | 100 | (0.4240, 0.4240, 0.4240) | 1.00 | 0.450 | 1.000 | 1.000 |
| 6 | Blue | 100 | (0.2187, 0.3227, 0.4587) | 1.00 | 0.450 | 1.000 | 1.000 |
| 7 | Brown | 100 | (0.4320, 0.3893, 0.3840) | 1.00 | 0.450 | 1.000 | 1.000 |
| 8 | Red | 100 | (0.5387, 0.2000, 0.2000) | 1.00 | 0.450 | 1.000 | 1.000 |
| 9 | Green | 100 | (0.2000, 0.4240, 0.2000) | 1.00 | 0.450 | 1.000 | 1.000 |

Decoded facts about the table:

* every one of the 10 records holds the **same colour** in `tint_r`, `tint_g` and `tint_b` (10 of 10 measured), so the three vectors are not three paint colours; they are the same RGB carried three times.
* all ten `occurrence` values are 100, so the table is uniformly weighted as written. DERIVED (unproven): if `occurrence` is a spawn weight, every tint is equally likely. The selecting code is not in this entity.
* the five 'metallic' tints all carry gloss 0.45 / metallic 1.0 / coat 1.0, and the matte ones (White, Black) gloss 0.0 / metallic 0.0 / coat 1.0 - the palette carries the *look*, not only the colour.
* the file offsets are decoded, not assumed: ConvertAdf's `offset-in-file` on the same bytes gives `tints[0].R` at `0x94`, and 77 floats in all - **7 per record** (R/G/B/A + specular_gloss/metallic/clear_coat) for the 10 tints plus the palette root's own default record (`palette.*`). `tint_g` and `tint_b` are separate bytes in the file (jc3adf reads them: equal to `tint_r` 10/10) but ConvertAdf exports only one ColorRGBA per record, so they have no exported offset - which is why `palette_black.py` patches R/G/B/A and the three scalars only.

**How the palette reaches the material: UNKNOWN, and measured to be so.** A scan of all **566** inner files for the byte string `palette` finds it in **1** file(s): `v0300_car_kensington_sportsmuscle_palette.vmodc` (1). No `.rbm`, `.epe` or `.vmodc` of the entity names the palette, so the binding is engine-side (spawn/vehicle-system), not an asset reference. DERIVED, therefore, not decoded: the visible paint is the block's own dynamic tint modulated by the TintMap (`body_msk`) channels, and the palette is what the engine writes into that dynamic slot for the chosen variant.

## 5. Exposure, tonemap, time of day: what JC3 data holds

Name search over the whole VFS index (**78907** rows), case-insensitive substring, counted per term:

| term | files | example |
|---|---|---|
| `tonemap` | 0 | - |
| `tone_map` | 0 | - |
| `exposure` | 1 | `textures/color_curves/color_correction_neutral_exposure.ddsc` |
| `postfx` | 0 | - |
| `post_process` | 0 | - |
| `lightprofile` | 0 | - |
| `light_profile` | 0 | - |
| `time_of_day` | 2 | `graphs/mission/modules/msub_time_of_day.gdc` |
| `sky` | 3364 | `dlc/bavarium_sea_heist/models/jc_weapons/05_stationary/w508_sam_capstone_skyshield/textures/air_engine_dif.hmddsc` |
| `sun` | 31 | `animations/jc_characters/dialogue/archive/eng/mission_mm210_dial_gameplay_boatsunk_01.ban` |
| `weather` | 81 | `animations/jc_characters/dialogue/archive/eng/bark_civ_female01_weather_change_01.ban` |
| `color_curves` | 4 | `textures/color_curves/color_correction_calibration_v01.ddsc` |

So: **no file in JC3's index is named for a tonemap, a post-process chain, a light profile or a time of day**. The only exposure-named asset is `textures/color_curves/color_correction_neutral_exposure.ddsc`, a colour-curve texture with no readable settings (its `.ddsc` payload is in the PARTIAL column of G3-12). Exposure and tonemapping are therefore **UNKNOWN** as data: they are either engine constants or live in the executable, and neither was read.

## 6. What is still UNKNOWN, and where it would be answered

1. **Which dynamic float4 is `TintColorR`, which is G, which is B, and what the fourth is.** The reflection header gives three names and the struct has four vectors; on the paint blocks the values are `(0.14, 0.19, 0.25, 1.0)`, `(0, 1, 0, 0)`, `(0, 0, 1, 0)`, `(2, 0, 1, 1)`, which reads more like a channel-to-tint matrix than three colours - but that is a hypothesis, not a decode. Where: the shader body (not on disk) or an in-game A/B write of one float4 with a screenshot readback.
2. **How the engine picks a tint and whether it writes the palette's rgb, gloss, metallic and coat into the dynamic slot.** The palette -> block binding is not in any of the 566 files (§4). Where: the vehicle spawn/variant code (executable), or a runtime oracle that dumps the material's dynamic constants after a spawn.
3. **The channel semantics of `PropertyMap` and `TintMap`.** MODLOG §78 reads them as 'PropertyMap RGB selects material channels 1-3, TintMap RGB = tint amount', from vanilla pixel statistics - INFERRED there, and the `.ddsc` payload is not decoded by any project script (G3-12). Where: a `.ddsc` reader (G3-12 open item) plus a decode of the four material channels.
4. **The on-screen transfer function.** No project file states an exposure, a tonemap curve or a lighting model (§5). Where: a runtime oracle.

## 7. What an on-screen calibration needs

The card's Done asks for `JC3 on-screen colour as a function of named terms, calibrated on >=3 vanilla paints, error stated`. None of that can be produced by reading files - it needs pixels. The minimum set, in the order it has to happen:

1. **A fixed frame** (G3-07): one camera pose, one time of day, one weather state, HUD off, and the paint zone filling a known screen region. Without a fixed frame two screenshots are not comparable.
2. **>=3 vanilla cars whose palette record is known from the file side** - the donor's own 10 tints are already decoded here (`White, Evergreen Pearl, Garnet Red Metallic`, White / Black / Garnet Red Metallic are the most separable), so the same entity at three tints is a valid calibration set, and three different vanilla entities is a stronger one.
3. **A readback with a known encoding**: screenshot in a lossless format, the paint-zone pixel average in linear light (the `.ddsc` flags say bit 8 = sRGB for colour textures, MODLOG §79), and the same for a neutral reference in frame.
4. **The authored terms for each sample**, which this tool now prints per block: the dynamic float4s, the static SpecularGloss/Metallic/ClearCoat float4s, and the palette record's rgb/gloss/metallic/coat.
5. Then fit `screen = f(tint, gloss, metallic, coat, TintMap, PropertyMap, exposure)` and report the residual per sample. Without (1)-(4) any such fit is the ALB-2 mistake again: a gain chosen from screenshots.

## Reproduce

```
python Tools/scripts/jc3_colour.py --write
python Tools/scripts/jc3_colour.py --check
```
