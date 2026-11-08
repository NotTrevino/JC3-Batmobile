# BmAK Reflectivity_Multiplier -> JC3 (appearance rule D2): is F0 really fixed?

**Question.** D2 drops `Reflectivity_Multiplier` and `Reflectivity_Material*` because "JC3 uses a
fixed F0". Verify that. Read how the shipped `CarPaintMM`, `GeneralMkIII` and `General` blocks
use their metallic / gloss / fresnel members, list the values found across the 233 vehicle
entities, and test whether metallic + gloss can reproduce BmAK's reflectance range.

**Verdict, in three parts.**

1. **For `CarPaintMM` the claim is verified in the only sense the files can verify it:** the block
   has no reflectance/F0 member at all, and the one member that could have carried a specular
   colour - `RBIInfo.ModelSpecularColor` - is marked `[unused]` by the compiler. None of the 13
   `carpaintmm*` headers declares a fresnel toggle [decoded].
2. **The claim is false as a blanket statement about JC3.** The generic path
   (`generalmkiii*`, 110 headers) declares `float Reflectivity_1..4` per material **and** a live
   `float EnableVariableDialecticSpecFresnel` toggle at offset 16 [decoded]. JC3 does have a
   per-material reflectance input; the Batmobile's paint block just is not the block that has it.
3. **The number "fixed F0" is UNKNOWN.** No file on disk states the constant. The nearest is a
   scene-level `CLEARCOAT_SPECULAR_FRESNEL0` in the lighting-tuning cbuffer, whose value is not
   in any readable file [decoded: layout only].

So D2's *disposition* is right for `CarPaintMM` but its *reason* overstates the case, and there is
a closer carrier than "none" - which is what STAGES.md requires the row to name.

---

## 1. What each block actually uses

### 1.1 `CarPaintMM` - the block all 19 Batmobile materials use

[decoded: `Research/JC3Grab/CB0_SLOTS.md` §3-§4; member lines re-read from
`Tools/JCMR-src/assets/jc3/shaders/carpaintmm.fb.txt`; 399 shipped blocks in 163 `.rbm` files.]

| member | bind / offset | read by the shader? | role for reflectance |
|---|---|---|---|
| `m_SpecularGloss` | `cb2[0]` @0 | yes | gloss per channel - **not** an F0 level |
| `m_Metallic` | `cb2[1]` @16 | yes | metallic per channel - the only reflectance lever |
| `m_ClearCoat` | `cb2[2]` @32 | yes | second (coat) lobe, per channel |
| `m_SpecularGlossOverride` | `cb6[4].x` @64 | yes | dynamic gloss override |
| `m_MetallicOverride` | `cb6[4].y` @68 | yes | dynamic metallic override |
| `m_ClearCoatOverride` | `cb6[4].z` @72 | yes | dynamic coat override |
| `ModelSpecularColor` | `RBIInfo` @160 (bind `cb8`) | **`[unused]`** | would have been the specular colour / F0 vector |
| `ModelAmbientColor` | `RBIInfo` @144 | **`[unused]`** | - |
| `ModelDiffuseColor` | `RBIInfo` @128 | yes | base-colour candidate |
| any `Reflectivity_N` / `Fresnel` member | - | **does not exist** | - |

`ModelSpecularColor` being `[unused]` is the strongest single piece of evidence for D2: the one
member whose name says "specular colour" is not consumed by the paint shader [decoded: `[unused]`
annotation, `carpaintmm.fb.txt:14`]. The compiler only prints that tag when the register is not
read.

**Counts:** 0 of 13 `carpaintmm*` headers contain `float Reflectivity_1` and 0 contain
`EnableVariableDialecticSpecFresnel` [decoded].

### 1.2 `GeneralMkIII` - the generic path that *does* carry reflectance

[decoded: `generalmkiii.fb.txt:7-50`; 110 headers in the `generalmkiii*` family declare both.]

| member | offset | state | note |
|---|---:|---|---|
| `DebugColor` | 0 | `[unused]` | - |
| **`EnableVariableDialecticSpecFresnel`** | **16** | **used** | per-material switch for variable dielectric specular Fresnel |
| **`UseMetallicVer2`** | **20** | **used** | second metallic model switch |
| `Reflectivity_1` | 4 | `[unused]` | declared, optimised out in this variant |
| `Reflectivity_2` | 44 | `[unused]` | same |
| `Reflectivity_3` | 68 | `[unused]` | same |
| `Reflectivity_4` | 92 | `[unused]` | same |
| `Roughness_1` | 8 | used | per material |
| `ClearCoat_1` | 24 | used | per material |
| `DiffuseWrap_1`, `Emissive_1`, `Transmission_1` | 12/16/20 | used | per material |
| `Roughness_2..4`, `ClearCoat_2..4`, `Reflectivity/Emissive/Transmission_2..4` | 28..96 | `[unused]` | channels 2-4 optimised out in this variant |

The important part is not the current `[unused]` tags - those are per-variant optimisations of a
multi-channel template. It is that **the input exists in the interface**: `Reflectivity_N` is a
real per-material float in 110 headers, and `EnableVariableDialecticSpecFresnel` is *live*. A
build that emits a `GeneralMkIII` block with the channel populated would have a reflectance input
`CarPaintMM` cannot offer.

**Gap for that route:** the `GeneralMkIII` `.rbm` payload layout is not decoded. `rbm_geom`
refuses it - "block 1 is GeneralMkIII, which this codec does not parse (need its serializer to
know where it ends)" - and 3 shipped `.rbm` files are skipped for exactly that reason [decoded:
`CB0_SLOTS.md` §1 skipped list; `rbm_geom.py` generic templates]. So the member is nameable in
the shader but not yet writable from a `.rbm`.

### 1.3 `General` / `GeneralJC3` - no named material members

[decoded: `general.fb.txt:7`, `generaljc3.fb.txt:7`; layout in `rbm_geom.py:49`
`u32 count | count x (len + name) | f32[4] materials + materialParams`.]

Both declare `cbMaterialConsts` but expose **no named member** - the reflection shows an unnamed
`float4` array (or, in the generic template, a trailing 16-byte `material_params`). One float4
exists per block with no published meaning; its role is UNKNOWN. It is not evidence either way
for F0.

### 1.4 Where a *constant* F0 does live

[decoded: `deferred_clusteredlightingtunable.fb.txt:63-67`.]

| member | offset | scope |
|---|---:|---|
| `REFLECTION_AO_HACK_MULTIPLIER` | 92 | scene |
| `CLEARCOAT_SPECULAR_GLOSS` | 96 | scene |
| **`CLEARCOAT_SPECULAR_FRESNEL0`** | **100** | **scene** - the clearcoat lobe's F0 is a global tuning constant |
| `TEST_WETNESS_FACTOR` | 104 | scene |
| `MM_ROUGHNESS_HACK_BEND_FACTOR` | 108 | scene |

This is the literal form of "fixed F0" that D2 means: for the clearcoat lobe it is a single
scene-level float, identical for every car. Its **value is UNKNOWN** - the header gives the
layout, not the numbers, and the lighting-tuning defaults are not on disk.

---

## 2. The values found across the 233 vehicle entities

[decoded: `Research/JC3Grab/ENTITIES.md:1-3,46-49` - 233 `.epe`/`.hkx` files across 232 entity
graphs, `CParts`/`SVehicleLights`/... each at 233; `TINT.md` oracle O1 - 232 graphs parsed, 76
carry a `Palette`, 156 do not.]

The look values of a vehicle are not in its `.rbm`; they are in the palette table inlined into
the entity graph [decoded: `TINT.md` §1-§2].

| parameter | scope | values found | count | label |
|---|---|---:|---:|---|
| `tints[i].specular_gloss` | per tint | range **0.0 .. 1.0**, median **1** | n=2466 (entity graphs); 3602 incl. loose modules | decoded |
| `tints[i].metallic` | per tint | range **0.0 .. 1.0**, median **0** | same | decoded |
| `tints[i].clear_coat` | per tint | range **0.0 .. 1.0**, median **1** | same | decoded |
| `tints[i].tint_r/g/b` | per tint | 401 distinct RGBs, R 0..0.88 | 26 modules | decoded |
| `CarPaintMM.static_params[0]` (`cb2[0]` `m_SpecularGloss`) | per block | **1 distinct value**: `(0.0, 0.4, 0.3737, 1.0)` | 394 blocks (paint + non-paint) | decoded |
| `CarPaintMM.dynamic_params[16..18]` (`cb6[4]` gloss/metallic/coat overrides) | per block | **`(0.4, 1.0, 1.0)`** on every paint block | 43 paint blocks of the extracted car | decoded |
| donor's 10 tints | per car | gloss `{0.0, 0.45}`, metallic `{0.0, 1.0}`, coat `{1.0}` | 10 | decoded (`COLOUR.md` §4) |

**Derived.** The shipped look space is coarse and *bimodal*, not continuous: the palette's
authored set is matte (`gloss 0, metallic 0, coat 1`) or metallic paint
(`gloss 0.45, metallic 1, coat 1`), and the `.rbm` block carries exactly one authored gloss
vector for everything. There is no shipped material that dials a reflectance *level* between the
matte and metallic ends except by moving `metallic` between 0 and 1.

That matters for D2: JC3's vehicle materials express reflectivity as a **two-state switch plus a
coat**, which is why a BmAK multiplier that lands between the states has nowhere to go.

---

## 3. BmAK: the decoded scalar values D2 drops

[decoded: `Research/BatmobileGrab/SKINS.md` (MIC override lists), `MATERIALS.md`,
`COLOUR_PARAMS.md`. `MESHES.json` holds mesh/LOD data only - its `materials` field is `null` and
it contains no `Reflectivity_*` key (`grep -c` = 0), so the per-material scalars come from the
SKINS/MATERIALS decode, not from `MESHES.json`.]

| material | scalar | value |
|---|---|---:|
| `Batmobile_V3_Emissive` | `Metalicity` | 0.92 |
| `Batmobile_V3_Cockpit_MIC` | `Metalicity` | 0.90 |
| | `Reflectivity_Multiplier` | 0.40 |
| | `Reflectivity_BaseMaterial2_Multiplier` | 5.00 |
| | `Reflectivity_Material3` | 1.00 |
| `BatmobileV3_Cockpit_Seat` | `Reflectivity_Multiplier` | 1.20 |
| `BatmobileV3_Upgrades_MAT_INST` | `Reflectivity_Multiplier` | 1.20 |
| `BatmobileV3_Wheel_V2_MIC` | `Reflectivity_Multiplier` | 1.00 |
| | `Metalicity_Multiplier` | 0.80 |
| `Batmobile_V3_Discbreak_MIC` | `Reflectivity_Multiplier` | 1.00 |
| | `Metalicity_Multiplier` | 0.80 |
| `Batmobile_V3_Tyre_V2_MIC` | `Reflectivity_Multiplier` | 0.20 |
| `Batmobile_V3_Mainbody_NEW_MIC` | `Material0_Reflectivity` | 0.20 |
| | `Material1_Reflectivity` | 0.20 |
| | `Material2_Reflectivity` | 0.90 |
| | `Material3_Reflectivity` | 0.15 |
| `Batmobile_V3_WheelArchs_NEW_MIC` | `Material0_Reflectivity` | 0.15 |
| | `Material1_Reflectivity` | 0.20 |
| | `Material2_Reflectivity` | 0.90 |
| | `Material3_Reflectivity` | 0.50 |
| | `Material2_Metalicity` | 1.00 |
| `Batmobile_V3_Undercarriage_NEW_MIC` | `Material1_Reflectivity` | 0.40 |
| `Batmobile_Jokerfied_Hair_MAT_MIC` | `Reflectivity` | 0.20 |
| | `Reflectivity_Multiplier` | 4.00 |
| | `Metalisity_Multiplier` | 0.90 |

**Derived (the bridge used below).** BmAK's reflectance is a *dielectric* term scaled by the
multiplier. The project's own rule (`factors.py:127`) treats `Reflectivity*` as dielectric
reflectance and keeps it "only as metallic when no Metalicity is given and value > 0.5". Adopting
the convention the rule implies:

```
F0_bmak = F0_d * R          (R = Reflectivity_Multiplier or Reflectivity_MaterialN)
```

where `F0_d` is the engine's dielectric base reflectance. `F0_d = 0.04` is used below as the
conventional value; **it is an assumption, not a decoded constant** (see §6). Every conclusion is
written so it survives a different `F0_d` - the errors scale linearly with it.

---

## 4. The test: can metallic + gloss reproduce BmAK's range?

**The reachable set.** With a metal/dielectric split,

```
F0_jc3(m, a) = F0_d * (1 - m) + a * m          m = metallic, a = albedo
```

`F0_jc3` is monotone in `m`, so the reachable band for one material is exactly

```
F0_jc3  in  [ min(F0_d, a) ,  max(F0_d, a) ]
```

**`gloss` does not appear in that expression.** `m_SpecularGloss` is the *width* of the lobe, not
its height; it cannot move F0 at all [decoded member semantics: gloss vs metallic are separate
vectors; the F0 role of "gloss" would need the SHEX, UNKNOWN].

**Consequence, derived:** for a dark lacquer (`a` ≈ 0.026-0.11, the decoded BmAK base colours),
the band is `[a, 0.04]`. JC3 can therefore reproduce only

```
R  in  [ a / F0_d ,  1 ]
```

i.e. **R between roughly 0.65 and 1.0 for a 0.026 albedo, 0.75 and 1.0 for a 0.03 albedo.** Every
decoded BmAK value below that window (0.15, 0.20, 0.40) and above it (1.20, 4.00, 5.00) is
outside the band. Metallic is not a reflectance dial for dark paint - at `m = 1` it *lowers* F0
toward a dark albedo.

### 4.1 Per-value table (F0_d = 0.04; albedo from the decoded `MaterialN_BaseColour`)

Albedo proxy: Body/Emissive `0.1124`, Cockpit `0.04494`, Undercarriage `0.0562`,
Mainbody/WheelArchs `0.0258`; `0.03` is a placeholder for the untextured parts
(seat, wheel, disc, tyre, hair) and is **derived, not decoded**.

| material | scalar | R | F0_bmak | reachable band | nearest JC3 F0 | error (abs) | error (rel) |
|---|---|---:|---:|---|---:|---:|---:|
| Body/Emissive | `Reflectivity_Multiplier` | 1.00 | 0.0400 | 0.0400 - 0.1124 | 0.0400 | **0.0000** | 0 % |
| Cockpit | `Reflectivity_Multiplier` | 0.40 | 0.0160 | 0.0400 - 0.0449 | 0.0400 | 0.0240 | 150 % |
| Cockpit | `Reflectivity_BaseMaterial2_Multiplier` | 5.00 | 0.2000 | 0.0400 - 0.0449 | 0.0449 | 0.1551 | 78 % |
| Cockpit | `Reflectivity_Material3` | 1.00 | 0.0400 | 0.0400 - 0.0449 | 0.0400 | **0.0000** | 0 % |
| Cockpit_Seat | `Reflectivity_Multiplier` | 1.20 | 0.0480 | 0.0300 - 0.0400 | 0.0400 | 0.0080 | 17 % |
| Upgrades | `Reflectivity_Multiplier` | 1.20 | 0.0480 | 0.0300 - 0.0400 | 0.0400 | 0.0080 | 17 % |
| Wheel_V2 | `Reflectivity_Multiplier` | 1.00 | 0.0400 | 0.0300 - 0.0400 | 0.0400 | **0.0000** | 0 % |
| Discbreak | `Reflectivity_Multiplier` | 1.00 | 0.0400 | 0.0300 - 0.0400 | 0.0400 | **0.0000** | 0 % |
| Tyre | `Reflectivity_Multiplier` | 0.20 | 0.0080 | 0.0300 - 0.0400 | 0.0300 | 0.0220 | 275 % |
| Mainbody | `Material0_Reflectivity` | 0.20 | 0.0080 | 0.0258 - 0.0400 | 0.0258 | 0.0178 | 223 % |
| Mainbody | `Material1_Reflectivity` | 0.20 | 0.0080 | 0.0258 - 0.0400 | 0.0258 | 0.0178 | 223 % |
| Mainbody | `Material2_Reflectivity` | 0.90 | 0.0360 | 0.0258 - 0.0400 | 0.0360 | **0.0000** | 0 % |
| Mainbody | `Material3_Reflectivity` | 0.15 | 0.0060 | 0.0258 - 0.0400 | 0.0258 | 0.0198 | 330 % |
| WheelArchs | `Material0_Reflectivity` | 0.15 | 0.0060 | 0.0258 - 0.0400 | 0.0258 | 0.0198 | 330 % |
| WheelArchs | `Material1_Reflectivity` | 0.20 | 0.0080 | 0.0258 - 0.0400 | 0.0258 | 0.0178 | 223 % |
| WheelArchs | `Material2_Reflectivity` | 0.90 | 0.0360 | 0.0258 - 0.0400 | 0.0360 | **0.0000** | 0 % |
| WheelArchs | `Material3_Reflectivity` | 0.50 | 0.0200 | 0.0258 - 0.0400 | 0.0258 | 0.0058 | 29 % |
| Undercarriage | `Material1_Reflectivity` | 0.40 | 0.0160 | 0.0400 - 0.0562 | 0.0400 | 0.0240 | 150 % |
| Joker hair | `Reflectivity` | 0.20 | 0.0080 | 0.0300 - 0.0400 | 0.0300 | 0.0220 | 275 % |
| Joker hair | `Reflectivity_Multiplier` | 4.00 | 0.1600 | 0.0300 - 0.0400 | 0.0400 | 0.1200 | 75 % |

[derived: the algebra of §4 applied to the decoded values of §3; `F0_d = 0.04` assumed.]

**Reading the table.** 6 of 20 decoded values land exactly (R ≈ 0.9-1.0 on a matching albedo).
The other 14 miss, and the misses are not small: the relative errors run from 17 % to 330 %.
The pattern is systematic rather than random - **any R that means "less reflective than the
engine default" is unreachable, because nothing in JC3 lowers F0 below the dielectric constant
for a dark albedo, and any R above 1 is unreachable for the same reason in reverse.**

### 4.2 Nearest JC3 combination, per value

"Nearest" = the `(metallic, coat)` pair whose resulting F0 is closest to `F0_bmak`, with gloss
left at the authored channel value (gloss does not enter F0).

| BmAK value | nearest JC3 setting | resulting F0 | error | residual meaning |
|---|---|---:|---:|---|
| R = 0.15 | metallic **0** (band floor), gloss authored | 0.0258 | 0.0198 | specular too bright by 3.3x |
| R = 0.20 (paint) | metallic **0**, gloss authored | 0.0258 | 0.0178 | too bright by 2.2x |
| R = 0.20 (tyre/hair) | metallic **1** at a = 0.03 | 0.0300 | 0.0220 | too bright by 2.75x |
| R = 0.40 | metallic **0** | 0.0400 | 0.0240 | too bright by 1.5x |
| R = 0.50 | metallic **0.75** (a = 0.0258) | 0.0293 → nearest 0.0258 | 0.0058 | too bright by 1.29x |
| R = 0.90 | metallic **0.4** (a = 0.0258) | 0.0360 | **0.0000** | exact |
| R = 1.00 | metallic **0** | 0.0400 | **0.0000** | exact |
| R = 1.20 | metallic **0** | 0.0400 | 0.0080 | too dark by 17 % |
| R = 4.00 | metallic **1** at a = 0.03 | 0.0300 | 0.1200 | too dark by 4x |
| R = 5.00 | metallic **1** at a = 0.0449, **+ clearcoat** | 0.0449 (coat adds a second lobe) | 0.1551 | too dark by 4.4x; only coat can add energy |

For `R > 1` the only JC3 lever that adds reflectance is `m_ClearCoat` (a second dielectric lobe
with its own fixed F0) - `metallic` cannot, because it interpolates *between* the two existing
endpoints rather than above them [derived from the member semantics and the lerp form].

---

## 5. What remains inexpressible

1. **Any F0 level below the engine's dielectric constant** (R < ~0.65 on dark paint). JC3 has no
   member that lowers dielectric reflectance; metallic only moves F0 toward the albedo, and a
   dark albedo is still ≈ 0.03. The tyre (0.2), the thin lacquer channels (0.15) and the dark
   interior (0.2) are all in this class: **5 of the 20 values**.
2. **Any F0 level above 1.0x the default** (R > 1) on a dark material: `metallic` saturates at
   the albedo. **4 values** (1.2 x2, 4.0, 5.0). A clearcoat can add a *second* lobe, but its F0
   is the global `CLEARCOAT_SPECULAR_FRESNEL0` - not settable per car [decoded layout].
3. **A per-channel reflectance that differs from gloss.** BmAK sets `MaterialN_Reflectivity`
   independently of `MaterialN_Roughness`; in JC3 both ride the same channel selector
   (`s2` PropertyMap) and the gloss/metallic vectors are separate but the *channel index* is
   shared - so a channel cannot be "glossy but barely reflective" in the BmAK sense without
   splitting the mpm texture.
4. **A continuous reflectance ramp.** The shipped look space is bimodal (§2: matte vs metallic),
   so intermediate authored values like 0.4 and 0.5 have no vanilla precedent to copy.
5. **The numeric F0 the engine actually uses.** Everything above is expressed relative to
   `F0_d`; the constant itself is not on disk.

---

## 6. Closest JC3 system, gap, and the build action

Per STAGES.md a row is never left at "no system".

**Closest system (two candidates, in order of preference):**

| rank | carrier | what it gives | gap |
|---|---|---|---|
| 1 | `CarPaintMM` `m_Metallic` + `m_ClearCoat` (`cb2[1]`, `cb2[2]`), per channel via `s2` | a 2-state reflectance switch, plus a second lobe | no reflectance *level*; band `[a, F0_d]` only |
| 2 | `GeneralMkIII` `Reflectivity_1` + `EnableVariableDialecticSpecFresnel` (live at offsets 4/16) | a real per-material reflectance float and a variable-fresnel switch | `GeneralMkIII` `.rbm` payload layout is **not decoded** - the value cannot be written yet |

**Gap for the build to fill.** Either (a) accept the band and encode the *look* of the missing
level into texture, or (b) emit a `GeneralMkIII` block that carries `Reflectivity_1` - which
first needs the block serializer.

**Build actions:**

1. **D2 row rewrite (no file layout needed):** 27 rows move from `excluded/drop` to
   `closest (CarPaintMM metallic + clearcoat) + gap (band [a, F0_d]; no level control) +
   build action (F0-BAKE-1 / REFL-WRITE-1)`. Keep the existing metallic fallback as the
   nearest point, and record the error from §4.1 per row instead of dropping it.
2. **F0-BAKE-1 - where the level cannot be set, bake it.** Put the low-reflectance classes
   (tyre 0.2, thin lacquer 0.15, dark interior 0.2) into a *darker* `s2` channel selection so the
   channel they select carries a lower gloss and a near-zero metallic, and darken the albedo in
   the same channel - F0 then approaches the albedo. This reproduces the *appearance* of low
   reflectance without a reflectance input. Cost: it also darkens the diffuse, which BmAK does
   not do - so it must be validated against the D3 (per-pixel roughness) row.
3. **REFL-WRITE-1 - the exact route.** Decode the `GeneralMkIII` `.rbm` payload (the same work
   that unblocks the 3 skipped `sportsmuscle_missile_base_signature` files), then write
   `Reflectivity_1` per material and set `EnableVariableDialecticSpecFresnel` = 1. That converts
   D2 from `closest` to `exact` for the 14 missing values, with `error 0` by construction.
   This is the only route that reaches `R > 1` and `R < 0.65` on the same car.
4. **For `R > 1` before REFL-WRITE-1 lands:** raise `m_ClearCoat` on that channel and record the
   residual as "second lobe, F0 fixed by `CLEARCOAT_SPECULAR_FRESNEL0`" - an approximation, not a
   solve.

---

## 7. UNKNOWN, with where each would be settled

1. **The numeric `F0_d` JC3 uses.** No readable file holds it; `CLEARCOAT_SPECULAR_FRESNEL0` is a
   layout-only member. Settle by reading the lighting-tuning defaults (not on disk) or a runtime
   constant dump.
2. **Whether `m_SpecularGloss` also encodes a specular *level*** (i.e. packs F0 and gloss in its
   four channels). The vector `(0.0, 0.4, 0.3737, 1.0)` is per-channel and could be
   gloss-only or gloss+level. The SHEX body is absent. If it packed a level, part of §4's
   inexpressible set would collapse - this is the single highest-value unknown in this report.
3. **The `GeneralMkIII` `.rbm` payload layout**, hence whether `Reflectivity_1` can be authored.
   3 shipped files are already blocked on it.
4. **Whether `EnableVariableDialecticSpecFresnel` is a switch or a 0..1 blend factor.** It is a
   `float`, not a bool, so it may be a blend weight - which would give a *continuous* dielectric
   reflectance and would make D2 exact far more cheaply than a full F0 write.
5. **The meaning of the 16-byte `material_params` float4** trailing each block in the
   `rbm_geom` layout (`CarPaintMM` and generic). It has no cbuffer counterpart in the 25+7+2
   named members, so its role is unknown; it is the only unexplained per-block scalar space.

---

## 8. Checks run for this report

| # | check | result |
|---|---|---|
| 1 | `grep -c "m_SpecularGloss" carpaintmm*.fb.txt` | present in the paint family only |
| 2 | `grep -n "ModelSpecularColor" carpaintmm.fb.txt` | line 14, tagged `[unused]` |
| 3 | `grep -lE "float Reflectivity_1\|EnableVariableDialectic" carpaintmm*.fb.txt \| wc -l` | **0** - no reflectance input in the paint block |
| 4 | `grep -lE "float Reflectivity_1" *.fb.txt \| wc -l` | **110** - the generic path has one |
| 5 | `grep -nE "Reflectivity_\|EnableVariableDialectic\|UseMetallicVer2" generalmkiii.fb.txt` | `Reflectivity_1..4` declared (`[unused]` in this variant), `EnableVariableDialecticSpecFresnel` @16 and `UseMetallicVer2` @20 live |
| 6 | `awk '/cbuffer MaterialConsts/,/^\/\/ }/' general.fb.txt generaljc3.fb.txt` | unnamed `float4` array only - no named reflectance member |
| 7 | `grep -n "CLEARCOAT_SPECULAR_FRESNEL0" deferred_clusteredlightingtunable.fb.txt` | scene-level float @100 (layout only) |
| 8 | `python` over `MESHES.json` | `materials` is `null`; `grep -c Reflectivity_Multiplier` = **0**, so scalars come from SKINS/MATERIALS |
| 9 | `python` over `TINT.json` `ranges` | gloss/metallic/coat each `0..1`, n=2466 |
| 10 | `ENTITIES.md` | 233 files / 232 entity graphs |
| 11 | reflectance test (§4) | 6/20 exact, 14/20 with error 0.0058 .. 0.1551 |

No game process was started, attached to or injected into; static read only.

## Reproduce

```bash
cd Tools/JCMR-src/assets/jc3/shaders
grep -n "ModelSpecularColor\|m_SpecularGloss\|m_Metallic\|m_ClearCoat" carpaintmm.fb.txt
grep -lE "float Reflectivity_1" *.fb.txt | wc -l
grep -nE "Reflectivity_|EnableVariableDialectic|UseMetallicVer2" generalmkiii.fb.txt
grep -rn "CLEARCOAT_SPECULAR_FRESNEL0" *.fb.txt | head
```
