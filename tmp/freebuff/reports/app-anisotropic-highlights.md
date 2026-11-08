# BmAK anisotropic highlights -> JC3 (appearance rows D4 / D5)

**Question.** Rows D4 (14 factor rows) and D5 (1 texture row) drop BmAK's anisotropic
highlight set. Does any shipped JC3 material block shade anisotropically, so the drop can be
replaced by a carrier? If not, what can a texture bake reproduce?

**Verdict.** No JC3 shader in the 961 reflection headers declares an anisotropic material
parameter, an anisotropic colour, a tangent-orientation vector, or an anisotropy ramp sampler
[decoded]. The only occurrences of "aniso" in the whole header set are three *texture
filtering* sampler names [decoded]. `CarPaintMM` - the block every Batmobile material uses -
has no member that can carry the effect [decoded]. So D4/D5 cannot become `exact`; they become
`closest + gap + build action` (STAGES.md), with the gap closed by a bake into `s1`/`s2`
[derived].

Everything below is labelled **decoded** (a file was read, path given), **derived** (a rule
plus its inputs), or **UNKNOWN** (what was tried, where the answer would be).

---

## 1. What D4/D5 say today

| row | in `Working/Appearance/progress.md` | count | current disposition |
|---|---|---:|---|
| D4 | `anisotropic highlights` | **14** factor rows over **6** materials | `excluded`, action `drop`, owner `none - no anisotropy input` |
| D5 | `anisotropic highlight ramp` | **1** texture row (`Aniso_ramp_Lacquered`) | `excluded`, action `drop` |

[decoded: `Working/Appearance/progress.md`, rows tagged `drop (D4)` / `drop (D5)`;
rule table `Tools/scripts/appearance_plan.py:139-145`; `Tools/scripts/factors.py:123,141`
send `^Anisotropic$` and `Anisotropic|^Fake_Aniso` to `no-jc3-equivalent`.]

The 14 D4 rows are: `Anisotropic_Channel_Choice` x2 (Emissive, Cockpit), `Fake_Aniso_1_Colour`
x2, `Fake_Aniso_2_Colour` x2, `Material3_Anisotropic_broad_Colour` x4, `Material3_Anisotropic_thin_Colour`
x4 (Mainbody, Turret, Undercarriage, WheelArchs) [decoded: same file].

The word "drop" in that table is the thing this report tests. The check below confirms the
*parameter* has no home in JC3; it does not confirm the *look* is unreachable.

---

## 2. BmAK: the decoded anisotropy parameters and their numbers

Source: `Research/BatmobileGrab/SKINS.md` (MIC overrides, per material) and
`Research/BatmobileGrab/VEC_DEFAULTS.md` (parent-material expression defaults).
All values are **decoded**; the slot each sits in is decoded too.

### 2.1 The four vectors

| parameter | role on the material | value | evidence |
|---|---|---|---|
| `Anisotropic Ramp` | texture: the ramp the highlight width is looked up in | `Engine.Aniso_ramp_Lacquered` | `SKINS.md` slots 3, 5, 10, 13; `COLOUR_PARAMS.md:78` (MIC #767, `TextureParameterValues` @0x158) |
| `Fake_Aniso_1_Colour` | vector4, highlight colour 1 | Emissive `[0.07182, 0.07061, 0.06428, 1]`; Cockpit `[0.6742, 0.6615, 0.534, 1]`; parent default `[0.674157, 0.647211, 0.375439, 1]` | `SKINS.md` slots 5, 10; `VEC_DEFAULTS.md` export 676, guid `c69ef213` |
| `Fake_Aniso_2_Colour` | vector4, highlight colour 2 | Emissive `[0.05607, 0.123, 0.2762, 1]`; Cockpit `[0.5385, 0.5489, 0.7921, 1]`; parent default `[0.131219, 0.153623, 0.674157, 1]` | `SKINS.md` slots 5, 10; `VEC_DEFAULTS.md` export 667, guid `562fe1bc` |
| `Anisotropic_Channel_Choice` | vector4, which mask channel drives the effect | Emissive `[0.9507, 0.9274, 1, 1]`; Cockpit `[0, 0, 1, 0]` | `SKINS.md` slots 5, 10; parent expression 669 has **no serialised default** (`VEC_DEFAULTS.md` §5, 66 B object) |
| `Material3_Anisotropic_thin_Colour` | vector4, the `Master`-chain name for colour 1 | WheelArchs `[0.1957, 0.2, 0.33, 1]`; parent default `[0.674157, 0.647211, 0.375439, 1]` | `SKINS.md` slot 3; `VEC_DEFAULTS.md` export 709 |
| `Material3_Anisotropic_broad_Colour` | vector4, the `Master`-chain name for colour 2 | WheelArchs `[0.462, 0.7335, 0.9723, 1]`; parent default `[0.131219, 0.153623, 0.674157, 1]` | `SKINS.md` slot 3; `VEC_DEFAULTS.md` export 699 |

**Derived (from decoded GUID equality).** `Fake_Aniso_1_Colour` and
`Material3_Anisotropic_thin_Colour` share guid `c69ef213`; `Fake_Aniso_2_Colour` and
`Material3_Anisotropic_broad_Colour` share guid `562fe1bc`. So the two name pairs are one
parameter slot seen through two parent chains - "thin"/"broad" are the Worn-master names for
"1"/"2". The effect is therefore **two coloured highlight lobes**, not four independent ones.

### 2.2 The five scalars

[decoded: `SKINS.md` scalar lists for slots 5, 10, 11, 13; `MATERIALS.md:969-971,1005-1006`.]

| scalar | Emissive | Cockpit | Discbreak | Cockpit_Seat | what it controls (derived from the name) |
|---|---:|---:|---:|---:|---|
| `Fake Aniso Brightness 1` | 0.5 | 2 | 0 | 0.01 | intensity of lobe 1 |
| `Fake Aniso Brightness 2` | 0.1 | 0.1 | 0 | 1 | intensity of lobe 2 |
| `fake aniso orientation` | 1 | 1 | **0** | 1 | rotates the ramp lookup |
| `fake aniso uv magnitude` | 1 | 1 | 1 | 1 | how far the UV is stretched along the streak |
| `fake aniso uv shift` | 0 | 0 | (absent) | 0 | offsets the stretched UV |

**Derived.** The `fake aniso uv magnitude` / `uv shift` / `orientation` trio, applied to a
ramp lookup, is a **UV-space fake**, not a physical tangent-frame BRDF: the highlight is
stretched in texture space, so it does not rotate with the view the way a true anisotropic
lobe does. That is consistent with the parameter being named `Fake_`. It also decides what a
bake can and cannot reproduce (§7).

### 2.3 The Arkham-side direction vector (context, not a JC3 carrier)

`Anisotropic_Direction = [0.0, 1.0, 0.5, 1.0]` on `Gordon_Hair_Master_Mat`
[decoded: `Research/BatmobileGrab/UNIFORM_FORMAT.md` §22, entry at `0x920740b`].
This is BmAK/Arkham data; it shows the source engine had a real direction vector input. It
has no JC3 counterpart (§4).

---

## 3. JC3 side: what the shaders and constant buffers actually declare

### 3.1 Shader-name census

Input: `Tools/JCMR-src/assets/jc3/shaders/*.fb.txt` (**961** files - the same set
`CB0_SLOTS.md` parsed) out of 1551 files in that directory [decoded: `ls *.fb.txt | wc -l`;
`ls | wc -l`].

| test | result | label |
|---|---|---|
| headers declaring a **cbuffer member** whose name contains `aniso` or `brushed` | **0** | decoded |
| headers containing the substring `aniso` at all | **37** | decoded |
| ...and every one of those occurrences | a sampler name: `SamplerStateDiffuseAnisotropic` (21), `SamplerLinearAniso` (12), `LinearWrapAnisoSampler` (4) = 37 | decoded |
| shaders named `car*` / `vehicle*` | 17: `carlight{,_blend,_deform}`, `carpaintmm` + 10 variants, `carpaintmmshadow`, `carpaintrsm` | decoded |
| shaders named `*metal*`, `*brush*`, `*steel*`, `*chrome*` | **0** | decoded |
| shaders named `*hair*` | 4: `characterhair{,_blend,_ilsh,_msk}` | decoded |

The 37 hits are in `nvwater*`, `terraindetail*`, `vegetationfoliage*` and
`volumetricterrain*` headers only [decoded: file list from `grep -ril aniso`]. Those are
**anisotropic texture filtering** states, i.e. a sampler property, not a shading model.
There is no anisotropic-shading shader in JC3's header set.

### 3.2 Constant-buffer census

Unique cbuffer names across all 961 headers [decoded: `grep -oE "^// cbuffer ..." | sort | uniq -c`]:

| cbuffer | headers | relevance to D4/D5 |
|---|---:|---|
| `CarPaintStaticMaterialParams` | 12 | paint block, bind `cb2` - no aniso member |
| `CarPaintDynamicMaterialParams` | 13 | paint block, bind `cb6` - no aniso member |
| `CarPaintDynamicObjectParams` | 12 | bind `cb7` - no aniso member |
| `RBIInfo` | 12 | bind `cb8` - no aniso member |
| `CarPaintOptionalParams` | **2** (`carpaintmm_blend_effects`, `..._stipple`) | **one member: `float m_RadialBlurAmount` @0** [decoded] - not anisotropy |
| `cbMaterialConsts` / `MaterialConsts` | 262 / 241 | generic material block, `float4 MaterialConsts[N]` - **no named members at all** |
| `GlobalConstants` | 618 | frame globals |

`CarPaintOptionalParams` was the last plausible hiding place and it carries one float of
radial blur [decoded]. There is no "optional anisotropy" block.

### 3.3 `CarPaintMM`, the block the Batmobile's 19 materials use

[decoded: `Research/JC3Grab/CB0_SLOTS.md` §3-§4; member list re-read from
`carpaintmm.fb.txt` itself; sizes cross-checked against 399 shipped `.rbm` blocks.]

**Static - `cb2`, 316 B, 25 named slots, none anisotropic:**

`m_SpecularGloss`@0, `m_Metallic`@16, `m_ClearCoat`@32, `m_Emissive`@48, `m_DiffuseWrap`@64,
`m_DirtParams`@80, `m_DirtBlend`@96, `m_DirtColor`@112, `m_DecalCount`@128 `[unused]`,
`m_DecalWidth`@144, `m_Decal1..4Color`@160/176/192/208, `m_DecalBlend`@224, `m_Damage`@240,
`m_DamageBlend`@256, `m_DamageColor`@272, then `SupportDecals`@288, `SupportDmgBlend`@292,
`SupportLayered`@296, `SupportOverlay`@300, `SupportRotating`@304 `[unused]`, `SupportDirt`@308,
`SupportSoftTint`@312.

**Dynamic - `cb6`, 76 B:** `m_TintColorR`@0, `m_TintColorG`@16, `m_TintColorB`@32,
`_unused`@48, `m_SpecularGlossOverride`@64, `m_MetallicOverride`@68, `m_ClearCoatOverride`@72.
**Object - `cb7`, 20 B:** `m_DecalIndex`@0, `m_DirtAmount`@16.

**Samplers:** `s0` Diffuse, `s1` Normal, `s2` PropertyMap (mpm), `s3` TintMap (msk),
`s4` DamageNormal, `s5` DamageAlbedo, `s6` DirtMap, `s7`-`s9` decal albedo/normal/property,
`s10`/`s11` unused by the header, plus `t16` Layered and `t17` Overlay
[decoded: `carpaintmm.fb.txt`; `COLOUR.md` §2].

There is **no** anisotropy direction, magnitude, colour, ramp sampler or tangent-orientation
member anywhere in the 25 + 7 + 2 slots [decoded].

One near-miss worth naming: `SupportRotating` (`cb2[19].x`, offset 304) is the only
"rotating" concept in the block, which would be the natural companion of a spun anisotropic
highlight (a brake disc). The compiler marks it `[unused]` [decoded], so even its role is
UNKNOWN; it is not an anisotropy carrier and must not be repurposed on the strength of its
name alone.

### 3.4 The hair shader, as the "does anything else do it" control

`characterhair.fb.txt` [decoded, read in full]:

| item | value |
|---|---|
| `cb0` `GlobalConstants` | `float4 Globals[95]`, 1520 B |
| `cb1` `cbInstanceConsts` | `float4 InstanceConsts[2]`, 32 B |
| `cb2` `cbMaterialConsts` | **`float4 MaterialConsts[6]`, 96 B - unnamed array** |
| samplers | `DiffuseMap s0/t0`, `NormalMap s1/t1`, `PropertiesMap s2/t2` |
| aniso member / aniso sampler | **none** |
| world/view/tangent members | none declared in the block |

So JC3's hair path is data-driven through a `PropertiesMap`, exactly like the paint path, and
carries no anisotropy parameter either. Note the contrast with BmAK: Arkham's hair master
takes `Anisotropic_Direction` (§2.3); JC3's does not.

---

## 4. JC3 candidates, named, each with its verdict

| # | candidate | block / shader | has an anisotropic carrier? | label |
|---|---|---|---|---|
| 1 | `CarPaintMM` (12 family headers + `carpaintmmshadow`, `carpaintrsm`) | `cb2`/`cb6`/`cb7` | **No** - 34 named slots, none aniso | decoded |
| 2 | `CarPaintOptionalParams` (2 headers) | `carpaintmm_blend_effects*` | **No** - `m_RadialBlurAmount` only | decoded |
| 3 | `characterhair` + `_blend` + `_ilsh` + `_msk` | `cbMaterialConsts[6]` + 3 samplers | **No parameter**; whether the body builds an anisotropic lobe from tangent data is UNKNOWN | decoded layout / UNKNOWN math |
| 4 | `General`, `GeneralJC3`, `GeneralMaskedJC3`, `GeneralMkIII` | generic `cbMaterialConsts` | **No named member** (unnamed `float4` array); no aniso sampler | decoded layout / UNKNOWN math |
| 5 | `Character`, `CharacterSkin` block types | character shaders | exist as block types (hashes `0x9D6E332A`, `0x626F5E3B`) but their `.rbm` payload layout is not decoded by any project script | UNKNOWN |
| 6 | `Window` (glass) | `cb*` | no aniso member in the family headers read | decoded (no member) |
| 7 | water / terrain / vegetation | `nvwater*`, `terraindetail*`, `vegetationfoliage*`, `volumetricterrain*` | only anisotropic *sampler filtering*; wrong domain (terrain/foliage, not a vehicle block) | decoded |
| 8 | brushed-metal / CD-like shader | - | **no such shader exists** by name (0 hits for metal/brush/steel/chrome) | decoded |

**Answer to the question as asked:** no shipped JC3 material block shades anisotropically, in
the sense of declaring an anisotropy parameter or an anisotropy ramp. The blocks a Batmobile
can use (`CarPaintMM`, `Window`, the generic/character families) all top out at
gloss/metallic/clearcoat plus texture maps [decoded]. Whether a *particular* already-compiled
shader body does something anisotropic with vertex tangents and a normal map cannot be settled
from a reflection header, because the SHEX bodies are not on disk [UNKNOWN].

### Why the shader-cache notes do not change this

The "shader-cache notes" in this project are **Arkham's**, not JC3's
[decoded: `Research/JC3Grab/UNIFORM_RECORDS.md` - `CombinedShaderCache-PC-D3D-SM5.upk`,
21,268,515 B]. They do contain anisotropy-named parameters
(`Material3_Anisotropic_thin_Colour`, `Material3_Anisotropic_broad_Colour`,
`Anisotropic_Direction`), but:

* an entry is 32 B = (class FName, parameter FName, RGBA) with **no offset, slot or bind field**;
* `RDEF` is absent from all 40,299 containers, so no Arkham name can be tied to a JC3 slot;
* 0 of the 32 JC3 paint member names appear in them.

[decoded: `CB0_SLOTS.md` §6, oracles O6/O7.] They are evidence about BmAK, not about a JC3
carrier.

---

## 5. Closest JC3 system, and the gap

STAGES.md forbids "JC3 has no system" as an answer; the row must name the closest system, the
gap, and the build action that closes it.

**Closest system: `CarPaintMM`'s per-channel material model.** The paint block does not vary
gloss/metallic/coat per pixel - it varies them per *channel*, and the `PropertyMap` (`s2`, mpm)
selects, per pixel, which of up to four channels is used. Its four vectors (`m_SpecularGloss`
`cb2[0]`, `m_Metallic` `cb2[1]`, `m_ClearCoat` `cb2[2]`, and the `m_SpecularGlossOverride`
`cb6[4].x`) are the only place a highlight can be made hotter or tighter
[decoded: `CB0_SLOTS.md` §3-§4; `MODLOG.md` §78 "PropertyMap RGB selects material channels
1-3" is INFERRED there and stays inferred].

That is structurally the same idea BmAK uses: `Material_Separation_Mask` -> `MaterialN`
{BaseColour, Reflectivity, Roughness} [decoded: `MODLOG.md` §78, BmAK side].

**The gap, stated numerically:**

| BmAK input | value carried | JC3 nearest member | gap |
|---|---|---|---|
| `Anisotropic Ramp` (texture) | `Aniso_ramp_Lacquered` | no aniso sampler in any header (`s0`-`s11` reviewed) | **no slot**; ramp cannot be sampled |
| `Fake_Aniso_1_Colour` | e.g. `[0.6742, 0.6615, 0.534, 1]` | no colour member; nearest are `cb2[0]` gloss and `cb2[1]` metallic vectors | **no colour**; a highlight colour cannot be set on any lobe |
| `Fake_Aniso_2_Colour` | e.g. `[0.5385, 0.5489, 0.7921, 1]` | same | **no colour** |
| `Anisotropic_Channel_Choice` | `[0, 0, 1, 0]` / `[0.9507, 0.9274, 1, 1]` | `s2` PropertyMap channel select | **partial**: JC3 selects channels too, but the choice lives in the mpm texture, not a vector - so it must be baked, not set |
| `fake aniso orientation` | 1 (0 on disc) | none | **no direction** |
| `fake aniso uv magnitude` | 1 | none (UVs are vertex data) | **no UV stretch** |
| `fake aniso uv shift` | 0 | none | **no UV offset** |
| lobe brightness (0.01 .. 2) | - | `cb2[0]` / `cb6[4].x` gloss, constant per channel | **no per-lobe intensity**; only a per-channel gloss level |
| `Anisotropic_Direction [0,1,0.5,1]` (Arkham) | - | none | **no tangent frame** |

**Build action (STAGES.md: "compose several systems where the closest one is short"):**

1. **BAKE-ANISO-1 - bake the ramp into `s1` (NormalMap).** The ramp's profile becomes a
   UV-aligned streak in the normal map: lobe width from the ramp curve, streak direction from
   `fake aniso orientation`, tiling from `fake aniso uv magnitude`, offset from
   `fake aniso uv shift`. This puts a stretched, lacquer-like highlight response into the one
   texture slot the block actually samples per pixel.
2. **BAKE-ANISO-2 - bake the channel choice into `s2` (PropertyMap).** Write the
   `Anisotropic_Channel_Choice` mask into the mpm RGB so the streaked region selects the
   higher-gloss channel (`cb2[0]` / `cb2[1]`), reproducing the "hotter panel" part.
3. **D4 row rewrite:** 14 rows move from `excluded/drop` to
   `closest (CarPaintMM per-channel gloss + PropertyMap) + gap (no aniso direction/ramp/colour)
   + build action (BAKE-ANISO-1/2)`.
4. **D5 row rewrite:** `Aniso_ramp_Lacquered` moves from `excluded/drop` to
   `bake (BAKE-ANISO-1)` - consumed as the source curve, not shipped as a texture.

What this buys and what it does not: the *panel reads as stretched/lacquered under the fixed
key light*, but the highlight **does not travel across the surface as the camera moves**. That
residual is the honest gap and belongs in the ledger as such.

---

## 6. What the bake needs that is not in the tree

`Aniso_ramp_Lacquered` is an **Engine-package** texture reference, not one of the 61 grabbed
`Playable_Batmobile_SF` textures: `Research/BatmobileGrab/TEXTURES.md` contains no `aniso`
entry [decoded: `grep -in aniso` returns nothing]. The reference itself is decoded
(`COLOUR_PARAMS.md:78`), and a sibling ramp `Engine.Aniso_ramp_D` is referenced by
`Batmobile_Jokerfied_Hair_MAT` [decoded: `objects.jsonl` index 677].

| question | answer | label |
|---|---|---|
| is the ramp referenced? | yes, `Aniso_ramp_Lacquered`, and `Aniso_ramp_D` on the hair master | decoded |
| are its pixels in the grabbed package? | no - 0 hits in the 61-texture census | decoded |
| does JC3 ship any texture or asset named `aniso`? | **0** entries in the 78,907-row VFS index | decoded |
| what is its resolution/format/curve? | **UNKNOWN** - nothing on disk to decode; would need the Engine package containing `Aniso_ramp_Lacquered` |

Consequence for the build: BAKE-ANISO-1 must either obtain the ramp from the Engine package on
the Arkham side, or synthesise the curve from the two decoded colour pairs plus the brightness
range. Until the ramp is read, the *shape* of the streak is UNKNOWN; only its existence, the
two lobe colours and the five scalars are known.

---

## 7. What a texture bake can reproduce, precisely

| BmAK feature | baked into | reproducible? | why |
|---|---|---|---|
| ramp profile (stretched highlight width) | `s1` normal streak | **yes, approximately** | a directional normal perturbation gives a stretched specular response under a fixed light | 
| lobe 1 / lobe 2 colours | `s1`/`s2` selection only | **no, not as colour** | `CarPaintMM` has no aniso colour member; colour would have to ride as gloss difference, losing hue |
| `fake aniso orientation` | streak direction in `s1` | **yes** | UV rotation is baked into the texture |
| `fake aniso uv magnitude` | streak tiling in `s1` | **yes** | UV scale is baked |
| `fake aniso uv shift` | streak offset in `s1` | **yes** | UV offset is baked |
| `Anisotropic_Channel_Choice` | `s2` mpm RGB | **yes** | channel selection is what mpm does |
| brightness 0.01 .. 2 | `cb2[0]` gloss level, per channel | **partially** | a constant per channel; cannot fall off along the streak |
| view-dependent highlight travel | - | **no** | needs a tangent-frame BRDF term; no member exists |
| per-pixel gloss/roughness from `Ref_n_Rough_Map` | already a separate D3 row | n/a | tracked separately |

[derived: from the decoded member list in §3.3 and the sampler list in §3.3; the "approximate"
qualifier is because the streak's specular response is a fixed normal perturbation, not a
Smith-GGX anisotropic lobe.]

---

## 8. UNKNOWN, with where each would be settled

1. **Whether any JC3 shader *body* computes an anisotropic lobe from vertex tangents.** The
   reflection headers name no parameter for it, but they do not contain the SHEX. Settle by
   decompiling the `carpaintmm` / `characterhair` DXBC, or by a runtime A/B on one material.
2. **The `Aniso_ramp_Lacquered` curve, resolution and channel layout.** Not in the grabbed
   textures, 0 `aniso` entries in the JC3 VFS, 0 in the grabbed package. Settle by extracting
   the Engine package that holds it on the Arkham side.
3. **What `SupportRotating` (`cb2[19].x`) was meant to do.** Named, offset decoded, marked
   `[unused]` by the compiler. Settle by finding a shipped block with the bit set and
   correlating with the shader body.
4. **The channel semantics of `PropertyMap` / `TintMap`.** INFERRED in `MODLOG.md` §78 from
   vanilla pixel statistics, not decoded; this report's BAKE-ANISO-2 leans on that inference
   and inherits its uncertainty.
5. **`Character` / `CharacterSkin` `.rbm` payload layouts.** Block hashes exist
   (`0x9D6E332A`, `0x626F5E3B`); no project serializer. If JC3 hair anisotropy existed, it
   would be there, and that block is the one place this census cannot fully clear.

---

## 9. Checks run for this report

| # | check | result |
|---|---|---|
| 1 | `ls *.fb.txt \| wc -l` in `Tools/JCMR-src/assets/jc3/shaders` | 961 - matches `CB0_SLOTS.md` |
| 2 | `grep -rilE "//\s+float[0-9]x?[0-9]?\s+\w*(aniso\|brushed)"` over the 961 | 0 headers |
| 3 | `grep -rhoiE "\w*aniso\w*"` unique | only `Anisotropic`, `Aniso`, `AnisoSampler` - all sampler-filter names |
| 4 | `grep -rhoE "^// cbuffer \w+" \| sort \| uniq -c` | `CarPaintOptionalParams` found at 2 headers; its only member is `m_RadialBlurAmount` |
| 5 | `carpaintmm.fb.txt` member list re-read | 25 static + 7 dynamic + 2 object slots; 0 anisotropic |
| 6 | `characterhair.fb.txt` read in full | `float4 MaterialConsts[6]`, 3 samplers, 0 aniso |
| 7 | `grep -oiE '"[^"]*aniso[^"]*"' Research/JC3Grab/INDEX.json` | 0 - JC3 ships no aniso-named asset |
| 8 | `grep -in aniso Research/BatmobileGrab/TEXTURES.md` | 0 - ramp pixels not grabbed |

No game process was started, attached to or injected into; this is a static read of files on
disk.

## Reproduce

```bash
cd Tools/JCMR-src/assets/jc3/shaders
ls *.fb.txt | wc -l
grep -rilE "//\s+float[0-9]x?[0-9]?\s+[A-Za-z0-9_]*(aniso|brushed)" *.fb.txt | wc -l
grep -rhoiE ".{0,40}aniso.{0,40}" *.fb.txt | sort | uniq -c
grep -rhoE "^// cbuffer [A-Za-z0-9_]+" *.fb.txt | sort | uniq -c | sort -rn
grep -l "CarPaintOptionalParams" *.fb.txt
```
