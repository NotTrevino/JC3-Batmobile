# T-L25..T-L34 — BmAK lens flares vs how JC3 draws headlight glare

Task: the ten lamp rows T-L25..T-L34 (`HeadLight1a/2a/1b/1c/2b/2c`, `RWheelLight_top/bottom`,
`LWheelLight_top/bottom`) are `LensFlareComponent`s in BmAK and were marked out because the JC3 light
module has no flare member. Look for how JC3 draws headlight glare/halos (emissive-block halo
geometry, light-preset members, additive billboard effects attached to lamps, bloom thresholds), read
how the shipped Serpente lamp parts and their RBMs make their glow, and produce a per-row table of
BmAK flare values against the nearest JC3 carrier, with a closest system and a gap for every row.

**Verdict.**

* **JC3 has no flare member, no halo member and no bloom field in any decoded file.** The light
  module carries 19 named fields / 25 raw members (`LIGHTS.json` → `jc3_fields`; `LIGHT_SYSTEM.md`
  §2) and none of them is a sprite, glow, glare or bloom. The `.effc` member paths likewise contain
  no flare/glow parameter (`FX.md`: `Timelines`, `EmitterTemplates`, `Instantiators`, `Modifiers`,
  `Params` — no flare member). So a flare cannot be transferred as a *member value*.
* **JC3 draws the same look in three separate places, and all three exist in the shipped data:**
  1. **emissive lens geometry** — every Serpente lamp part's `lod1.rbm` is 9 blocks whose **first
     block is `CarLight`**, plus the `Window` lens (`LGT1_FINDINGS.md` §4; 11,367 `CarLight` blocks
     fleet-wide, `LIGHT_SYSTEM.md` §5);
  2. **a volumetric halo** on the light entry — `volumetric_mode` (ships 0/1/2), `volume_intensity`
     (ships 0.001–0.0025), `radius`, `spot_angle`, `projected_texture_index`
     (`LIGHT_SYSTEM.md` §2);
  3. **an additive billboard sprite** — `effects/flare/headlight_flare_01.effc` (8,079 B, 591 rows,
     `EffectRTSystem`) is embedded in **160 vehicle `.ee` bundles**, and the flare texture set
     (`t_flare_headlight_ramp.ddsc` 262,272 B, `t_flare_glow_base/blob_dif.ddsc` 43,832 B each,
     `t_flare_star_01_dif.ddsc` 699,192 B) is in the install.
* **The ten BmAK rows themselves carry no flare values.** All ten serialise only the class-default
  `SourceColor` **[1,1,1,1]**, with `Radius` and `MinStrength` **null** (not serialised anywhere in
  the install). The look lives in three *shared* `LensFlare` assets, so the ten rows do not have ten
  distinct flare looks to map — they have three.
* **Closest system per cluster:** headlight rows → `CarLight` lens + `HeadLight` volumetric entry +
  optional `headlight_flare_01.effc` billboard; orphan headlight rows → the donor's **body-hosted**
  `HeadLight` entries; wheel rows → a new `CarLight` emitter on the wheel part plus a `HeadLight`
  entry on the wheel bone. The gap is the same everywhere: **no member binds a sprite to a lamp**, and
  the `CarLight` emissive parameters are undecoded (§102d), so only byte-copied glow is available.

---

## 1. What the ten BmAK rows actually contain

Decoded from `Research/BatmobileGrab/LIGHTS.json` (vehicle list, entries whose `socket` is one of the
ten) and `Research/BatmobileGrab/objects.jsonl` (`LensFlareComponent` exports of
`Vehicle.Batmobile_MK2`). Component indices below are the MK2 package's; the other three packages
(`BatmobileFunhouse`, `Batmobile`, `JokersBatmobile`) carry the same ten rows with their own indices.

| row | socket | socket_location (BmAK uu = cm) | bone | MK2 comp idx | template `LensFlare` asset | decoded component values | unnamed floats on the component |
|---|---|---|---|---|---|---|---|
| T-L25 | `HeadLight1a` | [311.264343, 45.2658, 67.0] | `Batmobile_Chassis` | 336 | `Batmobile.Batmobile_headlights_small` (export 328) | `SourceColor` [1,1,1,1] (class default), `Radius` null, `MinStrength` null | -0.686850, 0.079470 |
| T-L26 | `HeadLight2a` | [311.418518, -44.789246, 67.0] | `Batmobile_Chassis` | 345 | `Batmobile.Batmobile_headlights_small` (328) | same | -0.098544, 0.578265 |
| T-L27 | `HeadLight1b` | [316.322937, 41.71352, 58.75] | `Batmobile_Chassis` | 332 | `Batmobile.Batmobile_headlights_small` (328) | same | -0.807276, 0.774102 |
| T-L28 | `HeadLight1c` | **null (orphan socket)** | **null** | 333 | `Batmobile.Batmobile_headlights_small` (328) | same | -0.094852, 0.574511 |
| T-L29 | `HeadLight2b` | [314.919037, -41.464466, 58.75] | `Batmobile_Chassis` | 334 | `Batmobile.Batmobile_headlights_small` (328) | same | -0.813379, 0.116367 |
| T-L30 | `HeadLight2c` | **null (orphan socket)** | **null** | 335 | `Batmobile.Batmobile_headlights_small` (328) | same | -0.176000, 0.840571 |
| T-L31 | `RWheelLight_top` | [0.380923, 40.638508, 40.000805] | `Wheel_Frnt_Right_Disc` | 341 | `Batmobile.Batmobile_headlights_wheels` (329) | same | -0.122532, 0.581072 |
| T-L32 | `RWheelLight_bottom` | [0.347289, 53.81432, 10.002043] | `Wheel_Frnt_Right_Disc` | 342 | `Batmobile.Batmobile_headlights_wheels` (329) | same | -0.452132, 0.233009 |
| T-L33 | `LWheelLight_top` | [-0.118559, 40.599998, 40.0] | `Wheel_Frnt_Left_Disc` | 343 | `Batmobile.Batmobile_headlights_wheels` (329) | same | -0.936216, 0.318430 |
| T-L34 | `LWheelLight_bottom` | [-0.292692, 56.499176, 10.5] | `Wheel_Frnt_Left_Disc` | 344 | `Batmobile.Batmobile_headlights_wheels` (329) | same | -0.675375, 0.453536 |

Field sources (all from `LIGHTS.json` entry `field_sources`): `SourceColor` → *class default
`Default__LensFlareComponent` (Engine.upk)*; `Radius` and `MinStrength` → *not serialised anywhere in
the install (native default)*. The component tags in `objects.jsonl` are one `ObjectNCRProperty` (the `LensFlare` template, at
offset 540 in the Funhouse exports) plus two `FloatProperty` tags (the first at offset 636); **the
decoder has no name for those two floats**, so their meaning is `UNKNOWN` — they are not evidence of
size or fade.

### 1a. The three shared flare assets (where size/colour/fade actually live)

`objects.jsonl`, class `LensFlare`, package `Playable_BatmobileFunhouse_SF`:

| asset | export | size | decoded shape | leading `Reflections[]` values |
|---|---|---|---|---|
| `Batmobile_headlights_small` | 325 | 13,931 B | `SourceElement` StructProperty @84 (310 B) naming `Scaling`, `AxisScaling`, `Rotation`, `Color`, `Alpha`, `Offset`, `DistMap_Scale/Color/Alpha`; `Reflections` ArrayProperty @660 (13,340 B); `ScreenPercentageMap` @700; `FixedRelativeBoundingBox` @736 | 50.0, 45.0, 0.75, 20000.0, true (floats @676/680/684/688, bool @692) |
| `Batmobile_headlights_wheels` | 326 | 20,735 B | same layout | 70.0, 50.0, 1.05, 20000.0, true |

`Reflections[]` is a struct array and the decoder does not name its members, so **which of 50/45/0.75
is size, angle or fade is `UNKNOWN`**. What is decodable is the *structure* BmAK's flare is built
from: a source element with scale/axis-scale/rotation/colour/alpha/offset plus a per-reflection list
and a screen-percentage curve. That is exactly the "sprite with a size, colour and fade" the task
describes — and it is **asset-level, shared by six headlight rows or four wheel rows**, not per row.

---

## 2. How JC3 draws the same glare

### 2.1 No flare/halo/bloom field anywhere in the light module

`LIGHTS.json` → `jc3_fields` lists exactly:
`behavior, part, part_index, diffuse, range, falloff_start, near_cap, multiplier, min_luminosity,
light_type, blinking, angle, cast_shadows, projected_texture_index, volumetric_mode,
volume_intensity, uvscale, deformable_transform, preset_id` — 19 names, no sprite/glow/flare/bloom.
The raw module rows carry 25 members (`LIGHT_SYSTEM.md` §2 table: `diffuse`, `enabled`,
`falloff_start`, `is_shadow_caster`, `min_luminosity`, `multiplier`, `near_cap`, `preset_id`,
`radius`, `spot_angle`, `spot_inner_angle`, `volume_intensity`, `volumetric_mode`, …), again with no
flare member. `LIGHTS.md` marks every flare row "LensFlareComponent -> none (no-jc3-equivalent: JC3
light module has no flare)". So T-L25..T-L34 have **no member to land in**.

### 2.2 The emissive lens: `CarLight` block + `Window`

Shipped Serpente lamp parts, from `Research/RBM/serpente_rbm_headers.json` (paths under
`models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/`):

| part family | LODs | blocks per RBM | first block |
|---|---|---|---|
| `sportsmuscle_headlight_f_l_01`, `_f_l_02`, `_f_r_01`, `_f_r_02` (+ `mshswap` variants) | lod1–lod3 each | **9** | **`CarLight`** |
| `sportsmuscle_taillight_r_c`, `_r_l`, `_r_r` (+ `mshswap`) | lod1–lod4 each | **9** | **`CarLight`** |

`Working/Lights/LGT1_FINDINGS.md` §4 decodes one of them: `sportsmuscle_taillight_r_l.lod` lists 4
RBMs; `…_lod1.rbm` is **2 blocks, `CarLight` and `Window`** — an emissive material and the lens
glass. The same section records that these light parts are **unrigged** (`flags 0x0`, no deform
weights), while the body is rigged (`CarPaintMM`, flags `0x1004`, `IS_DEFORM`).

What the `CarLight` block can and cannot give (`LIGHT_SYSTEM.md` §5): 11,367 blocks in 11,367 meshes
/ 220 vehicles; vertex stride 12 B; index width 2 B; exactly 6 material slots; static header
**1,085 B**; buffers `[12, 24, 2]`; round-trip byte-exact on 190/193 blocks. **The material/emissive
parameter bytes are not decoded (MODLOG §102d)**, so a `CarLight` block can be copied byte-exact but
not authored from numbers — "which bytes are the emissive colour/intensity" is the open line in
`LIGHT_SYSTEM.md` §5.

The emissive texture family that goes with it exists in the install:
`models/jc_vehicles/00_shared/car_lights/textures/car_lights_kensington_modern_emissive_alpha_mpm.ddsc`
(22,000 B, container accounted, payload format-id 77 not decoded — `DECODE_DEPTH.md` row 74).

### 2.3 The volumetric halo members

The halo is a **light-entry** effect, not geometry. Members available on every one of the 3,972
light entries, with shipped value ranges (`LIGHT_SYSTEM.md` §2):

| member | shipped values | use as a glare carrier |
|---|---|---|
| `volumetric_mode` | 0, 1, 2 | 1 = volumetric cone/haze in the shipped data (0 = plain) |
| `volume_intensity` | 0.001, 0.0015, 0.002, 0.0025 | strength of that haze |
| `radius` | 0.2, 0.3, 0.5, 0.6 (m; `range` on the same rows is 2.0) | halo/near-field size |
| `spot_angle` / `spot_inner_angle` | 15/20/25/30, 0/10/20/30 | cone shape |
| `multiplier` | 0, 0.2, 0.3, 0.4 | brightness scale |
| `min_luminosity` | 0 | floor |
| `near_cap` | 0, 0.1, 0.2, 0.26 | near clamp (fade shape) |
| `projected_texture_index` | -1 (none) | cookie/projected texture slot — the only texture slot on a light |

Donor `HeadLight` values (`LIGHTS.json` → `vanilla_by_behavior.HeadLight`, the donor
`v0300_car_kensington_sportsmuscle` module): `diffuse` **[1.0, 1.0, 1.0]**, `range` **2.0**,
`falloff_start` **0.0**, `near_cap` **1.0**, `multiplier` **1.0**, `min_luminosity` **0.0**,
`light_type` **0**, `blinking` **0**, `angle` **10.0**, `cast_shadows` **0**,
`projected_texture_index` **-1**, `volumetric_mode` **0**, `volume_intensity` **1.0**,
`preset_id` **2763198432**. So the donor's shipped headlight is a plain spot with **no** volumetric
halo (`volumetric_mode 0`); a halo look must be authored from the members above — they exist and
ship, but the donor does not use them on headlights.

The wheel-arch recipe in `LIGHT_SYSTEM.md` §7 shows the BmAK wheel socket already mapped to a
`HeadLight` entry on `sportsmuscle_wheel_f_l` (part_index 26) with the same 25 members, plus
`LightColor` [160, 180, 255, 0] / 255 as `diffuse` — that is the entry a wheel glare would hang on.

### 2.4 The additive billboard sprite

JC3 *does* ship a headlight lens-flare effect, it is just not in the light module:

| fact | value | evidence |
|---|---|---|
| effect | `effects/flare/headlight_flare_01.effc` | `FX_TABLE.jsonl` |
| size / rows / arrays / types | **8,079 B / 591 / 67 / 36** | `FX_TABLE.jsonl`; `DECODE_DEPTH.md` row 136 (FULL) |
| root class | `EffectRTSystem` | `FX.md` |
| `.ee` bundles containing it | **160** (first: `v0000_car_autostraad_oldjeep_blackhand_01.ee`) | `FX_TABLE.jsonl` |
| standalone sibling with byte offsets | `effects/flare/headlight_flare_round_01.effc`, archive `patch_win64/game1`, offset **442,472,448**, size **8,079** | `INDEX.jsonl:38738` |
| flare textures | `t_flare_headlight_ramp.ddsc` 262,272 B; `t_flare_glow_base_dif.ddsc` 43,832 B; `t_flare_glow_blob_dif.ddsc` 43,832 B; `t_flare_star_01_dif.ddsc` 699,192 B | `DECODE_DEPTH.md` rows 40–43 |
| texture binding | `.effc` carries **0 strings** in all 955 files, so an effect cannot name its texture; identity is `RenderBlockTypeHash` (8 distinct) and `.trim` | `FX9_HAZE.md` §2, §4 |

That is the nearest thing in the game to a `LensFlareComponent`: an additive sprite effect that is
already attached to 160 vehicle entities. What it does **not** have is a light-module binding: no
member in the 25 points at it, so "attach at this lamp" is entity/effect wiring, not a tune value.

### 2.5 Bloom threshold

`UNKNOWN`. No bloom threshold, tone-map exposure or post-process setting is decoded anywhere in the
corpus: a case-insensitive search of `Research/JC3Grab/*.md` for `bloom` returns only weapon bloom
(`WEAPONS.md:452`; `Working/Translation/T7_WEAPONS.md:161`), and the light/FX/geometry reports never
name a bloom parameter. Renderer settings live in engine code/config that was not grabbed, so bloom
cannot be used as a carrier and no threshold can be quoted.

---

## 3. Per-row table — BmAK flare vs nearest JC3 carrier

"Closest carrier" is the system the build would use; "gap" is what JC3 does not supply and the build
must add (STAGES.md BUILD).

| row | BmAK flare values | closest JC3 carrier | gap the build must close |
|---|---|---|---|
| **T-L25** `HeadLight1a` | white [1,1,1,1]; radius null; min-strength null; asset `headlights_small` (50/45/0.75 leading floats, unnamed) | `CarLight` emissive lens in `sportsmuscle_headlight_f_l_01_lod1.rbm` (9 blocks, first `CarLight`) + `HeadLight` entry on `sportsmuscle_body` (`diffuse` [1,1,1], `range` 2.0, `angle` 10.0, `volumetric_mode` 0) + optional `headlight_flare_01.effc` billboard | no flare member; `CarLight` colour/intensity bytes undecoded (§102d); the `.effc` has no light-module binding — the build must spawn it at the socket. Copying the block gives glow, not the sprite |
| **T-L26** `HeadLight2a` | identical | same, mirrored: `sportsmuscle_headlight_f_r_01_lod1.rbm` (`CarLight` first of 9) + `HeadLight` entry | same as T-L25 |
| **T-L27** `HeadLight1b` | identical | the **same** `CarLight` lens mesh as T-L25 (JC3 has one emissive block per mesh; the second flare row has no separate geometry) + a second `HeadLight` entry on the same part is legal (donor's left tail part hosts TailLight + LeftSignal + Reverse, `LIGHT_SYSTEM.md` §4) | the two-element flare stack (source + reflection list) collapses to one glow + one light; per-element scale/fade is lost |
| **T-L28** `HeadLight1c` (**orphan**) | identical, but no socket and no bone | donor **body-hosted** `HeadLight` entries: donor lights module rows 3 and 10 hang `HeadLight` on `sportsmuscle_body` (part_index 0) through `\|sportsmuscle_LOD1\|body\|dashboard_LIG` and `…\|front_primary_LIG` (`LGT1_FINDINGS.md` §2) | our body part has no `_LIG` node and no `CarLight` block — the assembled 25 RBMs are `{CarPaintMM: 160, Window: 25}`, **0 `CarLight`** (`LGT1_FINDINGS.md` §4). Build must add the node and the emitter, or drop the row |
| **T-L29** `HeadLight2b` | identical | same as T-L27, right side (`sportsmuscle_headlight_f_r_01`) | same as T-L27 |
| **T-L30** `HeadLight2c` (**orphan**) | identical, no socket/bone | same body-hosted `HeadLight` pattern as T-L28 | same as T-L28 |
| **T-L31** `RWheelLight_top` | identical; asset `headlights_wheels` (70/50/1.05) | `LIGHT_SYSTEM.md` §7 wheel-arch recipe: `HeadLight` entry on `sportsmuscle_wheel_f_r` (part_index 26/27), bone `Wheel_Frnt_Right_Disc`, material `VEHLTMAT_Special1`, plus a `CarLight` emitter mesh in the wheel `lod1.rbm` | Serpente's wheel `lod1.rbm` is 9 blocks with **first block `CarPaintMM`** (no `CarLight`), and the donor's 21 light entries contain **no wheel light** (`LGT1_FINDINGS.md` §2). Build must author the emitter and the entry; wheel parts also carry no rig |
| **T-L32** `RWheelLight_bottom` | identical | same wheel-arch entry, second socket on the same bone | same as T-L31; the two stacked flare elements have one shared geometry slot |
| **T-L33** `LWheelLight_top` | identical | same wheel-arch recipe, left: `sportsmuscle_wheel_f_l`, bone `Wheel_Frnt_Left_Disc`, material `VEHLTMAT_Special3` | same as T-L31 (left wheel RBM also `CarPaintMM`-first) |
| **T-L34** `LWheelLight_bottom` | identical | same left wheel entry, second socket | same as T-L31 |

No row is left without a closest system: the four socketed headlight rows (T-L25/26/27/29) land on
the donor headlight `CarLight`+`HeadLight` pair, the two orphan headlights (T-L28/30) land on the
donor's body-hosted headlight pattern, and the four wheel rows (T-L31..T-L34) land on the wheel-arch
recipe. The two orphan rows and the four
wheel rows are the expensive ones — each needs geometry that the build does not have.

---

## 4. Unit bridge and transfer boundary

| quantity | BmAK | JC3 | bridge |
|---|---|---|---|
| socket position | uu = **cm** (`[-0.349729, 50.689182, 26.0]` cm — `LIGHT_SYSTEM.md` §7) | metres | `m = cm / 100` |
| colour | `SourceColor` 0..1 (here class default [1,1,1,1]) | `diffuse` 0..1 (`HeadLight` [1,1,1]) | same scale, direct |
| size | `Radius` null; asset `Scaling`/`AxisScaling` structs, values unnamed | `radius`/`range` in m (0.2–0.6 / 2.0) | **cannot convert** — no named BmAK number |
| fade | `MinStrength` null; asset `Alpha` struct + `Reflections[]` floats unnamed | `falloff_start` 0..1, `near_cap` 0..1, `min_luminosity` 0 | **cannot convert** — no named BmAK number |
| screen behaviour | `ScreenPercentageMap` (134 B struct), `FixedRelativeBoundingBox` | none (no screen-space member) | JC3 has no equivalent carrier |

**What can be carried:** the *look class* — a glowing lens (`CarLight` byte-copy), a volumetric halo
(`volumetric_mode` / `volume_intensity` / `radius`), and an additive sprite (`headlight_flare_01.effc`,
already present in 160 vehicle bundles). The headlight/taillight meshes to copy from exist for all
eight Serpente lamp part families.

**What cannot:** (a) per-row flare colour — BmAK's ten components are all the white class default and
the assets are shared three ways, so there is no per-row colour to move; (b) the flare element stack
(`Reflections[]`, `SourceElement` scale/axis-scale/rotation/alpha) — no JC3 member and no decoded
effect parameter to express it; (c) screen-space scaling/occlusion (`ScreenPercentageMap`,
`FixedRelativeBoundingBox`) — no JC3 carrier; (d) bloom-driven glare — no bloom setting decoded;
(e) authoring the `CarLight` emissive values — blocked by §102d (copy-only).

---

## 5. Gaps the build must fill (STAGES.md BUILD)

1. **Headlight glow (T-L25/26/27/29).** Copy a `CarLight`+`Window` block pair from
   `sportsmuscle_headlight_f_l_01_lod1.rbm` into our headlight meshes and add `HeadLight` entries on
   `sportsmuscle_body` at the four real sockets. Cheap: the donor block round-trips byte-exact.
2. **Headlight sprite.** Attach `headlight_flare_01.effc` (or a private copy named for the Batmobile)
   at the four sockets via the entity/effect side. This is the only route to a real lens flare, and
   the attachment is the part JC3 does not model as a member.
3. **Orphan headlights (T-L28/30).** Either add the `_LIG` body nodes the donor uses
   (`dashboard_LIG`/`front_primary_LIG` pattern) or drop the rows; the body currently has neither a
   node nor a `CarLight` block.
4. **Wheel glare (T-L31..T-L34).** Author a `CarLight` emitter in the wheel `lod1.rbm` (today
   `CarPaintMM`-first, no emissive block) and add the two `HeadLight` entries on
   `sportsmuscle_wheel_f_l/r` (part_index 26/27) at `Wheel_Frnt_*_Disc`. This is new geometry, not a
   copy — the most expensive of the five gaps.
5. **Emissive authoring.** Until the `CarLight` parameter bytes are decoded (MODLOG §102d), the glow
   colour/intensity can only be borrowed from a donor block, not tuned to BmAK's white flare.

## Evidence index

- `Research/BatmobileGrab/LIGHTS.json` — ten entries (`socket`, `socket_location`, `bone`,
  `material_type`, `components[].path/index/fields`); `vanilla_by_behavior.HeadLight`;
  `jc3_fields`; `field_sources` (`SourceColor` class default, `Radius`/`MinStrength` not serialised).
- `Research/BatmobileGrab/objects.jsonl` — `LensFlareComponent` exports (MK2 indices 332–345, refs at
  offset 540, floats at 636/604); `LensFlare` exports 325/326 (`SourceElement` @84, `Reflections`
  @660, `ScreenPercentageMap` @700, `FixedRelativeBoundingBox` @736; floats @676–688).
- `Research/BatmobileGrab/LIGHTS.md:23,52–90,124–140` — component-class census and the
  "no-jc3-equivalent: JC3 light module has no flare" disposition on every flare row.
- `Working/Lights/LGT1_FINDINGS.md` §2 (donor's 21 entries, body-hosted rows 3/10), §4 (vanilla lamp
  part = `CarLight`+`Window`; our build = 0 `CarLight` in 25 RBMs).
- `Research/JC3Grab/LIGHT_SYSTEM.md` §2 (member table and ranges), §5 (CarLight layout, §102d
  blockage), §7 (wheel-arch recipe, BmAK cm → JC3 m).
- `Research/RBM/serpente_rbm_headers.json` — 8 headlight and 3 taillight part families, 9 blocks,
  first block `CarLight`; wheel parts, first block `CarPaintMM`.
- `Research/JC3Grab/FX_TABLE.jsonl` — `effects/flare/headlight_flare_01.effc`, 8,079 B, 591 rows,
  67 arrays, 36 types, 160 `.ee` containers.
- `Research/JC3Grab/INDEX.jsonl:38738` — `headlight_flare_round_01.effc` @ `patch_win64/game1`
  442,472,448, 8,079 B.
- `Research/JC3Grab/DECODE_DEPTH.md` rows 40–43, 74, 136 — flare textures, emissive texture,
  headlight effect FULL decode.
- `Research/JC3Grab/FX9_HAZE.md` §2 — 0 strings across 955 `.effc`, so no effect names a texture.
- `Working/Appearance/build_lights/lights_manifest.json` (14 `LensFlare` mentions) and the copied
  headlight RBMs (no `CarLight` block, grep 0).
