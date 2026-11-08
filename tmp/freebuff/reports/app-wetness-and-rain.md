# BmAK rain / wetness -> JC3 vehicle materials (appearance rule D8)

**Question.** The operator's BmAK reference is a wet street at night and BmAK materials carry
`Rain_Constant` and wetness terms. D8 drops them as "JC3 weather/wetness system". How does JC3's
wet-surface behaviour work for vehicles, can a private material opt in or out, what does
`Rain_Constant` map to, and what does JC3 do to a car in rain by default?

**Verdict.**

* JC3's wet look for a **car body** is **scene-global**: one float, `TEST_WETNESS_FACTOR`, in the
  deferred lighting tuning cbuffer [decoded]. No vehicle material has a wetness strength.
* The paint block (`CarPaintMM`) declares **no** wetness member, **no** rain occluder and **no**
  wetness-noise sampler - 13 of 13 headers [decoded]. A private *paint* material therefore
  **cannot opt in or out** of the wet look.
* Two other vehicle-relevant blocks **do** carry the wet machinery: the **`Window`** block
  (4 of 4 headers declare `RainOccluderSampler s9` + `RainOccluderTexture t40`) and the
  **`GeneralMkIII`** family (55 of 156 `general*` headers), which adds
  `WetnessNoiseTexture t41` [decoded]. So JC3 has a per-material
  wet/occlusion input - just not on the block the Batmobile's paint uses.
* The **world** does not get wet by parameter at all: wet roads are separate **shader variants**
  (`layeredroad1..4wet`, `layeredroadmask1..4wet`) [decoded]. That is the shape of JC3's answer:
  wetness is a scene state plus a shader variant, not an authored material value.
* **D8 is right that the paint row has no carrier**, and wrong to imply JC3 has no per-material
  wetness anywhere: the `Window` and `GeneralMkIII` paths do. Per STAGES.md the row becomes
  `closest + gap + build action`.

---

## 1. What JC3 does to a car in rain, by default

| surface | carrier | evidence | label |
|---|---|---|---|
| **whole scene** | `float TEST_WETNESS_FACTOR` @ offset 104 in `deferred_clusteredlightingtunable` (`_debug`, `_full`, `_indoor`, `_indoor_full` = 5 headers) | shader-reflection cbuffer, `deferred_clusteredlightingtunable.fb.txt:66` | decoded (layout); value UNKNOWN |
| **paint / body** (`CarPaintMM`) | **nothing** - no wetness member, no rain sampler | 0 of 13 `carpaintmm*` headers declare `RainOccluderSampler` or `WetnessNoiseTexture` | decoded |
| **glass** (`Window`) | `RainOccluderSampler` `s9` + `RainOccluderTexture` `t40` (no wetness-noise texture) | 4 of 4 `window*.fb.txt` | decoded |
| **generic / non-paint parts** (`GeneralMkIII*`) | all three: `s9`, `t40`, `t41` | 55 of 156 `general*` headers | decoded |
| **lights** (`CarLight`) | **nothing** | 0 of 3 `carlight*` | decoded |
| **hair / character** (`characterhair*`) | **nothing** | 0 of 4 | decoded |
| **road surface** | separate wet **shader variants**: `layeredroad1..4wet`, `layeredroadmask1..4wet` | 8 headers | decoded |

**Derived reading.** The wet state is authored **once, scene-wide** (`TEST_WETNESS_FACTOR`), and
each *shader variant* decides what to do with it. A material's only lever is *which shader
variant it binds* and, where the variant exposes them, the rain-occluder / wetness-noise textures.
The paint variant is the one variant with neither.

**What that means for a vanilla car in rain:** the body's paint shade is driven by the scene
factor, because the paint block has no per-material wetness at all - there is nothing on the
material that could refuse it [derived from the decoded absence]. Glass and the non-paint parts
can be masked by their occluder textures. The road switches shader variant. No vehicle-level
value participates: the module dumps contain **0** members matching `rain` or `wet` (the only
`*rain*` hits are `CTrain`, `TrainGlobal`, `train_track_width_scale` - a monorail, a homonym)
[decoded: `DRIVE_CARRIERS.json`, `ENTITIES.md`; the 81 "weather" files are NPC barks].

---

## 2. Shader uniforms and per-material members, in full

### 2.1 Scene uniforms (the only wetness *strength*)

[decoded: `deferred_clusteredlightingtunable.fb.txt:63-67`.]

| offset | member | scope |
|---:|---|---|
| 92 | `REFLECTION_AO_HACK_MULTIPLIER` | scene |
| 96 | `CLEARCOAT_SPECULAR_GLOSS` | scene |
| 100 | `CLEARCOAT_SPECULAR_FRESNEL0` | scene |
| **104** | **`TEST_WETNESS_FACTOR`** | **scene** |
| 108 | `MM_ROUGHNESS_HACK_BEND_FACTOR` | scene |

The name says `TEST_`: this is a debug/tuning constant that shipped. **Its value is UNKNOWN** -
the header gives the layout only; no readable file holds the defaults. Whether the paint shader
even samples it is UNKNOWN (body absent), but the paint block carries no other wetness input, so
if wetness reaches paint at all it arrives this way.

### 2.2 Per-material members

`CarPaintMM` [decoded: `carpaintmm.fb.txt`; `CB0_SLOTS.md` §3-§4]:

| member | bind / offset | wet-related? |
|---|---|---|
| `m_DirtParams` | `cb2[5]` @80 | dirt, not water |
| `m_DirtBlend` | `cb2[6]` @96 | dirt |
| `m_DirtColor` | `cb2[7]` @112 | dirt |
| `SupportDirt` | `cb2[19].y` @308 | dirt **enable flag** |
| `m_DirtAmount` | `cb7[1].x` @16 | dirt, dynamic per object |
| `DirtMap` | `s6`/`t6` | dirt |
| **wetness / rain member** | **none** | - |
| **rain occluder / wetness-noise sampler** | **none** | - |

**Sampler census of the paint block** (`s0`-`s11`): Diffuse, Normal, PropertyMap, TintMap,
DamageNormal, DamageAlbedo, DirtMap, Decal albedo/normal/property, 2 unused - plus `t16` Layered,
`t17` Overlay [decoded]. Nothing for rain.

**The 16-byte `material_params` float4** that `rbm_geom` reads after each block's texture table
has no counterpart among the 32 named paint members [decoded: `rbm_geom.py:592`]. Its role is
UNKNOWN and it is the only unexplained scalar space left in the block - it is *not* evidence of a
wetness input, and must not be repurposed on a guess.

### 2.3 Block flags - is there a wetness bit?

[decoded: `rbm_geom.py:114-126`.]

| bit | name |
|---:|---|
| `0x1` | `SUPPORT_DECALS` |
| `0x2` | `SUPPORT_DAMAGE_BLEND` |
| **`0x4`** | **`SUPPORT_DIRT`** |
| `0x8` | `SUPPORT_PALETTE_FILE` |
| `0x10` | `SUPPORT_SOFT_TINT` |
| `0x20` | `SUPPORT_LAYERED` |
| `0x40` | `SUPPORT_OVERLAY` |
| `0x80` | `DISABLE_BACKFACE_CULLING` |
| `0x100` / `0x200` | alpha blending / alpha testing |
| `0x1000` / `0x2000` | `IS_DEFORM` / `IS_SKINNED` |

**There is no wetness or rain flag.** The only environmental bit is `SUPPORT_DIRT`. The
`CarPaintMM` flags on the donor's paint blocks are `0x101F` (decals, damage blend, dirt,
soft-tint, IS_DEFORM) and `0x1000` on the interior blocks [decoded: `COLOUR.md` §1 table] - so
the paint blocks have **dirt on**, not wetness on.

---

## 3. Can a private material opt in or out of the wet look?

| block | opt in | opt out | how | label |
|---|---|---|---|---|
| `CarPaintMM` (all 19 Batmobile materials) | **no** | **no** | no member, no sampler, no flag | decoded |
| `Window` (the Batmobile's glass) | **yes** | **yes** | bind/blank `RainOccluderTexture t40` (`s9`) | decoded (slots) / UNKNOWN (semantics) |
| `GeneralMkIII` (generic parts) | **yes** | **yes** | same slots plus `WetnessNoiseTexture t41`; and `EnableVariableDialecticSpecFresnel` if it is the wet-fresnel path | decoded (slots) / UNKNOWN (payload layout) |
| vehicle module (`.vmodc`) | **no** | **no** | 0 rain/wet members decoded | decoded |
| scene | - | - | `TEST_WETNESS_FACTOR` is global; a mod cannot set it from a material | decoded |

**Answer:** a private *paint* material cannot opt in or out - wetness is applied to it by the
scene or not at all. A private *glass* or *generic-part* material can, by what it binds to
`s9`/`t40`/`t41`. A private *vehicle module* cannot, because no such member exists.

The practical consequence for the build: the Batmobile's lacquered body will be wetted exactly
as much as any vanilla car - never more, never less - and the only way to make the body
*deliberately* wetter (or dry in rain) is to change the block type (→ GeneralMkIII) or to bake
the state into the textures.

---

## 4. BmAK's values, and what `Rain_Constant` maps to

### 4.1 Decoded BmAK wet/rain set

[decoded: `Research/BatmobileGrab/SKINS.md` §§ slots 3-13; `VEC_DEFAULTS.md`; `COLOUR_PARAMS.md`.]

| BmAK parameter | value | where it sits | count |
|---|---|---|---:|
| `Rain_Constant` | **1** | `Batmobile_V3_Emissive` (slot 5) and `Batmobile_V3_Tyre_V2_MIC` (slot 9) | 7 rows / **2 materials** |
| `Rain_Size_Multiplier` | **[2.5, 2, 0, 1]** | WheelArchs, Mainbody, Turret, Undercarriage, Emissive, Tyre (variants: `[2,2,0,1]`, `[1,2,0,1]`) | 8 |
| `Batman_Rain_Direction` | **[0, 0, -1, 0]** | WheelArchs, Mainbody, Turret, Undercarriage; `[0,0,0,0]` default on Body_NoRain / Tyre; `[0,0,1,0]` glass default | 10 |
| `Rain_Mask_Vector` | **[1, 1, 1, 1]** | `Batmobile_Body_MASTER` default (export 659) | 1 |
| `Wetness_Refl_Fresnel` | **0.6** | WheelArchs, Mainbody, Turret, Undercarriage | 6 |
| `Wetness_Reflectivity_Multiplier` | **0.6** / **0.65** | Jokerfied_V2_MAT, Body_NoRain_MAT | 2 |
| `RainReflectivityMul` | **2** | `Batmobile_V3_Tyre_V2_MIC` | 1 |
| `RainRoughnessMul` | **0.5** | `Batmobile_V3_Tyre_V2_MIC` | 1 |

**Derived.** The cluster splits into three kinds of value:

1. **an enable/normaliser** - `Rain_Constant = 1` on every material that has it (7 of 7). A
   value of 1 means "unscaled": it is not a look, it is the *permission* to be rained on.
2. **direction + tiling** - `Batman_Rain_Direction [0,0,-1,0]`, `Rain_Size_Multiplier
   [2.5,2,0,1]`, `Rain_Mask_Vector [1,1,1,1]`: where the streaks run and how dense they are.
3. **wet-response modifiers** - `Wetness_Refl_Fresnel 0.6`, `Wetness_Reflectivity_Multiplier
   0.6/0.65`, `RainReflectivityMul 2`, `RainRoughnessMul 0.5`: how the surface answers water
   (tighter/brighter specular, lower roughness).

### 4.2 Mapping, value by value

| BmAK | nearest JC3 equivalent | match | gap |
|---|---|---|---|
| `Rain_Constant = 1` | `TEST_WETNESS_FACTOR` (scene, one float) | **semantic, not numeric**: both are "how wet", but one is per material and one is per scene | <br>no per-material wetness scalar; the Batmobile cannot be wetter than a van |
| `Wetness_Refl_Fresnel = 0.6` | `EnableVariableDialecticSpecFresnel` (`GeneralMkIII` @16) - *if* that float is a fresnel blend (UNKNOWN) | closest in kind, **wrong block** | paint block has no fresnel input at all; D2's report covers this |
| `Wetness_Reflectivity_Multiplier 0.6` | `m_Metallic` / `m_SpecularGloss` per channel | **partial** - a static stand-in | cannot be *conditional on rain*; the value would be baked in permanently |
| `RainReflectivityMul = 2` | none | **none** | a ×2 wet-only reflectance boost has no slot |
| `RainRoughnessMul = 0.5` | `m_SpecularGloss` per channel | **partial** - static gloss | gloss is per channel and constant; no wet override |
| `Batman_Rain_Direction [0,0,-1,0]` | none (no member in 961 headers) | **none** | rain direction is not a material input in JC3 |
| `Rain_Size_Multiplier [2.5,2,0,1]` | `WetnessNoiseTexture t41` UV scale - in the shader body, no member | **none settable** | the tiling is compiled or scene-side |
| `Rain_Mask_Vector [1,1,1,1]` | `RainOccluderTexture t40` on `Window` / `GeneralMkIII` | **closest**; neutral value means "no masking" | not available on paint |

**`Rain_Constant` in one sentence:** it is a **per-material wet-enable normaliser set to 1
everywhere it appears**, and the closest JC3 thing is the scene-wide `TEST_WETNESS_FACTOR`;
because 1 is the neutral value, mapping it to "the scene's factor, unscaled" introduces **no
numeric error** - the error lives in the other six parameters, which have no carrier.

That is a useful result for the ledger: `Rain_Constant` can be marked **exact-by-neutrality**
(its value is the identity), while the rest of D8 becomes `closest + gap`.

---

## 5. Closest system, gap, and build actions

**Closest systems (in order):**

| rank | system | gives | gap |
|---|---|---|---|
| 1 | scene `TEST_WETNESS_FACTOR` (`deferred_clusteredlightingtunable` @104) | automatic wet response on every car, including the paint | not per material; not settable by a mod's material; value UNKNOWN |
| 2 | `Window` block `s9`/`t40`/`t41` | real per-material rain occlusion + wetness noise, on the Batmobile's glass | paint cannot use it |
| 3 | `GeneralMkIII` family, same three slots | the same for non-paint parts, and it has `Reflectivity_N` / variable fresnel | `.rbm` payload layout undecoded; block swap required |
| 4 | static bake into `s1`/`s2` | a *permanently* wet-looking body - which is what a night-rain screenshot shows | loses the dry state |

**Gap for the build to fill.** JC3 has one wetness scalar for the whole scene and per-material
*masks* (occluders) but **no per-material wet strength, wet gloss, wet fresnel, rain direction or
rain tiling on the paint path**. BmAK has all six, per material.

**Build actions (STAGES.md: compose where the closest system is short):**

1. **D8 row rewrite.** Split D8 into three rows so the exactness is visible:
   * `Rain_Constant` (7 rows, 2 materials) → **exact by neutrality** (value 1 = unscaled; scene
     factor carries it).
   * `Wetness_Refl_Fresnel`, `Wetness_Reflectivity_Multiplier` (×8) → `closest` (channel
     metallic/gloss, static) + **gap** (no wet-only override) + action **WET-1**.
   * `Batman_Rain_Direction`, `Rain_Size_Multiplier`, `Rain_Mask_Vector`, `RainReflectivityMul`,
     `RainRoughnessMul` (×10) → `closest` (scene wetness / occluder) + **gap** (no direction,
     no tiling, no per-material boost) + action **WET-2** / **WET-3**.
2. **WET-1 - bake the wet response into the texture set.** For the night-rain target, bake the
   wet roughness (BmAK `RainRoughnessMul 0.5` → halve the authored gloss) and the wet reflectance
   (`RainReflectivityMul 2`) into the `s2` PropertyMap channel that the body selects, and put the
   water micro-normal into `s1`. This reproduces the *look* of the operator's reference and keeps
   the block type. Cost: the car is always wet - acceptable only if the build ships one fixed
   time-of-day/weather state; otherwise it must be paired with a dry variant.
3. **WET-2 - bind the water mask where JC3 allows it.** Put the `RainOccluderTexture` /
   `WetnessNoiseTexture` on the **Window** block (already supported, 4 of 4 headers) so the
   cockpit glass reads as wet, and treat the paint as scene-wet.
4. **WET-3 - the exact route.** Decode the `GeneralMkIII` `.rbm` payload (the same blocker as
   the F0 report's REFL-WRITE-1), then emit the body as `GeneralMkIII` with a rain occluder and
   `Reflectivity_N`; that is the only path where per-material wet data has a home. It is a
   two-row dependency: **REFL-WRITE-1 and WET-3 share one decoder**.
5. **Scene half - not a mod.** Time of day / rain state is engine-global; the build cannot set
   it from a material. If the deliverable is the night-rain screenshot, the *scene* has to be
   chosen in-game (PILOT/TEST stage), not baked into `.rbm`.

---

## 6. UNKNOWN, with where each would be settled

1. **The value of `TEST_WETNESS_FACTOR`** and whether the paint shader reads it. Layout only.
   Settle by reading the lighting-tuning defaults or a runtime constant dump.
2. **What `RainOccluderTexture` (t40) and `WetnessNoiseTexture` (t41) encode** - channel
   layout, UV convention, whether t40 is a top-down occlusion mask. No `.ddsc` decoder for them
   in this project (G3-12 open item).
3. **Whether `Window`'s `s9`/`t40`/`t41` are wired on the Batmobile's actual glass block.** The
   shader declares them; the shipped `Window` block's texture table was not read in this pass.
4. **Whether `EnableVariableDialecticSpecFresnel` is the wet-fresnel switch.** It is a float,
   not a bool; a 0..1 blend would make it the per-material fresnel input both D2 and D8 need.
5. **The 16-byte `material_params` float4** at the end of each block - unexplained; could be
   anything, and is not claimed here.
6. **Whether any shipped vehicle material binds a rain occluder at all.** The headers say the
   *shader* supports it; no decoded vehicle block was found binding one in this pass.

---

## 7. Checks run for this report

| # | check | result |
|---|---|---|
| 1 | `grep -lE "RainOccluderSampler\|WetnessNoiseTexture" carpaintmm*.fb.txt \| wc -l` | **0 of 13** |
| 2 | `RainOccluderSampler` over `window*.fb.txt` | **4 of 4** (`WetnessNoiseTexture`: 0 of 4) |
| 3 | same over `general*.fb.txt` | **55 of 156** (incl. `generalmkiii*`) |
| 4 | same over `carlight*` / `characterhair*` | **0 of 3** / **0 of 4** |
| 5 | `grep -n "TEST_WETNESS_FACTOR" deferred_clusteredlightingtunable*.fb.txt` | 5 headers, `float @104` |
| 6 | `ls *wet*.fb.txt` | 8 wet road variants |
| 7 | `grep -n "wet\|rain\|dirt" carpaintmm.fb.txt` | dirt members only; no rain/wet |
| 8 | `rbm_geom.py` flags | 13 bits, `SUPPORT_DIRT 0x4`; **no wet bit** |
| 9 | rain/wet members in `DRIVE_CARRIERS.json` + `ENTITIES.md` | only `CTrain`/`TrainGlobal` homonyms; 0 wetness members |
| 10 | BmAK `Rain_Constant` occurrences | 7, all `= 1` |
| 11 | BmAK wet cluster | 8 parameters, values in §4.1 |

No game process was started, attached to or injected into; static read only.

## Reproduce

```bash
cd Tools/JCMR-src/assets/jc3/shaders
grep -lE "RainOccluderSampler|WetnessNoiseTexture" carpaintmm*.fb.txt window*.fb.txt | sort
grep -lE "RainOccluderSampler|WetnessNoiseTexture" general*.fb.txt | wc -l
grep -n "TEST_WETNESS_FACTOR" deferred_clusteredlightingtunable.fb.txt
ls *wet*.fb.txt
grep -n "wet\|rain\|dirt\|SupportDirt" carpaintmm.fb.txt
```
