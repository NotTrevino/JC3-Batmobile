# APP — the emissive mask channel: what JC3 multiplies, measured, and the pack plan

Card: appearance, the two `R2` rows (`Batmobile_V3_Int_Cockpit_E`, `Batmobile_V3_Wheel_E`) that were
left "partial — JC3 emissive mask channel not decoded". **Plan only — no bake, no build, no install,
no game launch.** Every claim is labelled:

* **decoded** — a file in this tree carries the bytes and a project tool (or a quoted source/header)
  reads them;
* **derived** — a rule plus its stated inputs;
* **MEASURED** — pixels/bytes this card decoded itself, command in §10;
* **INFERRED** — a reading of the measurements, with the experiment that would falsify it named;
* **UNKNOWN** — what was tried and what would settle it.

## 0. Change statement (AGENTS.md)

| item | value |
|---|---|
| intended change | add one report: the emissive channel decode, its evidence, the two-mask pack plan, the proofs |
| file | `tmp/freebuff/reports/app-emissive-mask-channel.md` (this file) |
| why this file | the brief names it; every report of this wave lives under `tmp/freebuff/reports/`, and everything it cites is read-only |
| reverted by | deleting this file. Nothing else was written: no edit to `Research/`, `Tools/`, `Working/`, `Builds/`, no texture baked, no `.rbm` re-encoded, no game launched |

---

## 1. Verdict

1. **The mask is carried by the `EmissiveMap`'s RGB, not by its alpha — and that is measured, not
   assumed.** Two shipped car-light atlases exist in this tree. In the Kensington atlas the RGB
   region is **chromatic** (3223 texels, e.g. flat `(0, 0, 0.16)` pure blue, `R = G = 0`; **0 of 3223
   texels are grey within 2/255**), so RGB is a *colour*, not a greyscale mask; its alpha holds a
   disjoint 575-texel mask whose RGB is exactly 0. In the Old Jeep atlas the alpha is **0 on every
   texel** while RGB carries all the emissive content. An alpha-only glow gate would make the Old
   Jeep's lamps permanently dark, so **alpha cannot be the gate.** The shader multiplies the RGB of
   slot 5 by the block's emissive constant; alpha is an optional secondary mask.
2. **`EmissiveMap` exists on exactly one block type: `CarLight` (`s5`).** `CarPaintMM` has **no**
   emissive sampler at all — its emissive is the constant vector `m_Emissive` (`cb2` +48), which the
   shader reads **once per material channel** (`s2` selects the channel per texel). `General` has no
   emissive input; `GeneralMkIII` has `Emissive_1`..`Emissive_4` scalars and **no** emissive map;
   `Window` has neither, and `LightingFrameConsts.EmissiveScale` is `[unused]`. So "per-pixel emissive"
   in JC3 exists **only** on the lamp block, and only as a colour texture.
3. **The block cannot be the per-lamp colour either.** All 44 donor `CarLight` blocks share one
   byte-identical 1,085 B `pre_static` (card B-03 B4, reproduced here), so no per-lamp colour lives in
   the block; the 16 B `mid_static` is one float that varies **per family and per LOD**
   (headlight 1.662 / 1.652 / 1.577, taillight 1.318 / 1.267 / 1.234) — an intensity, not a colour.
   Per-lamp colour therefore has to be in the texture, which is exactly what the chromatic RGB is.
4. **Under the "closest system" rule, the two BmAK masks split two ways.** The lamp parts that already
   exist (`build_lights`, 24 RBMs) can carry the masks **per pixel, 8 bits, in the correct channel** —
   that is an *exact* carrier, currently unused because the built blocks clone the donor's texture
   table and therefore sample the donor's atlas with BmAK UVs. The cockpit instrument cluster is a
   `CarPaintMM` part and has **no per-pixel emissive at all**; its closest carrier is four banded
   levels of `m_Emissive` selected by `s2`, i.e. the same mechanism the per-pixel gloss plan uses —
   and for the same four channels, which makes it a joint solve, not a free one.
5. **`Batmobile_V3_Wheel_E` is not in the grab.** `SLOTS.json` slot 5 names it
   (`Emissive_Map: Engine.Batmobile_V3_Wheel_E`), `appearance_plan.json` has the `R2` row
   `Batmobile_V3_Wheel_E`, and the 115-file grab under `Working/Appearance/grab/*/Texture2D/` does
   **not** contain it (`*_E.tga` present: `Batmobile_V3_Int_Cockpit_E`, `Batmobile_DLC_Tumbler_Glass_E`).
   So half of this card's subject has no source pixels on disk. That is an asset gap, named in §9,
   not something to fill with a plausible-looking mask.
6. **The build's current emissive state is worse than "material-level".** `build_bud1/factors.json`:
   `Batmobile_V3_Emissive` (the wheel-light material) has `static.Emissive = [0,0,0,0]` — *neutral*,
   so its faces emit nothing at all — while `BatmobileV3_Cockpit_Seat` has a flat
   `[15,15,15,15]`, i.e. the whole seat glows uniformly at intensity 15. The one emissive value the
   car does ship is in the wrong place and the one material that should glow is off.

---

## 2. The channel — the evidence chain

### 2.1 The shader interfaces (decoded: the reflection headers on disk)

Source: `Tools/JCMR-src/assets/jc3/shaders/*.fb.txt` (the compiled bodies are **not** on disk — these
files declare the interface only, which is why §2.3/§2.4 are needed).

| block | emitter input | evidence |
|---|---|---|
| `CarLight` | **`s5 EmissiveMap` / `t5`** (`texture float4 2d`) | `carlight.fb.txt`: samplers `s0 DiffuseMap`, `s1 NormalMap`, `s2 PropertyMap`, `s4 NormalDetailMap`, **`s5 EmissiveMap`**; constants `cb2 cbMaterialConsts { float4 MaterialConsts[4]; }` (64 B) |
| `CarPaintMM` | **`m_Emissive` only** — `cb2` +48, `float4`, one component per material channel | `carpaintmm.fb.txt`: samplers `s0..s9` = Diffuse, Normal, Property, Tint, DamageNormal, DamageAlbedo, Dirt, DecalAlbedo, DecalNormal, DecalProperty — **no emissive sampler, no emissive texture** |
| `General` | none | `general.fb.txt`: `s0 DiffuseMap`, `s1 NormalMap`, `s2 PropertiesMap`, `s3 AOBlendMap`; `MaterialConsts[3]` |
| `GeneralMkIII` | `Emissive_1` @16 live; `Emissive_2..4` `[unused]` | `generalmkiii.fb.txt`: textures `t0 Albedo1Map`, `t1 Gloss1Map`, `t2 Metallic1Map`, `t3 Normal1Map`, `t40..t42` weather — **no emissive texture** |
| `Window` | none | `window.fb.txt`: no emissive sampler; `LightingFrameConsts.EmissiveScale` @37316 is `[unused]` |

So the question "which texture channel does the shader multiply by the emissive colour" only has an
answer on `CarLight`, and only if slot 5 is really `t5` in the block. That is the next step.

### 2.2 The block's texture table position 5 is `EmissiveMap` (decoded + derived)

`rbm_geom.decode()` on a built lamp part, `Working/Appearance/build_lights/sportsmuscle_headlight_f_l_lod1.rbm`,
one `CarLight` block, 6 texture names (decoded from the user data):

```
0  .../car_lights_kensington_modern_dif.ddsc                  -> s0 DiffuseMap      (matches)
1  .../car_lights_kensington_modern_nrm.ddsc                  -> s1 NormalMap       (matches)
2  .../car_lights_kensington_modern_mpm.ddsc                  -> s2 PropertyMap     (matches)
3  textures/00_general/dummy/a00_dummy_grey_dif_detail.ddsc   -> s3                (no sampler declared)
4  textures/00_general/dummy/a00_dummy_flat_nrm.ddsc          -> s4 NormalDetailMap (matches, a flat normal)
5  .../car_lights_kensington_modern_emissive_alpha_mpm.ddsc   -> s5 EmissiveMap     (matches)
```

Three independent positions (0, 1, 2) plus position 4 agree, so **table position = sampler index**
on this block type, and position 5 is the emissive atlas. The same table is on all 44 donor blocks
(one distinct table, B-03 B4) and on all 24 built ones — the build clones it.

### 2.3 The shipped atlas, measured (MEASURED)

Instrument: `tex2ddsc.decode_bc3` over the block chain of the `.ddsc` (the files ship a *partial*
mip ladder — the Kensington atlas is a 512² base with 10 mips but only 8 in file, so the top **stored**
mip is 128²; the numbers below are that mip, which is the one the game binds as mip 0 of the shipped
file). Command in §10.

`car_lights_kensington_modern_emissive_alpha_mpm.ddsc` — format 77 (BC3/DXT5), 512² base, 128² stored:

| region | texels | what |
|---|---:|---|
| `RGB.max > 0.15` | 3223 (19.7 %) | channel means inside: **R .102 / G .024 / B .127**; brightest texels are `(0, 0, 0.16)`, `(0, 0, 0.18)` — flat, saturated, **single-channel** swatches |
| grey-within-2/255 inside that region | **0 of 3223** | ⇒ **RGB is chroma, not a mask.** A greyscale glow mask cannot be built out of pure-blue texels |
| `A > 0.15` | 575 (3.5 %) | mean A **0.49**, max **0.86**; **RGB under it is exactly 0.00** |
| intersection RGB-region ∩ A-region | **0 texels** | the two live regions are disjoint |

`v0000_car_autostraad_oldjeep_lights_emissive_alpha_mpm.ddsc` — format 77, the second shipped atlas:

| region | texels | what |
|---|---:|---|
| `RGB.max > 0.15` | 201 | emissive content present |
| `A > 0.15` | **0** | **the alpha is zero on every texel of the whole file** (A mean 0.001) |

**What this pair proves.** The alpha is not a universal gate: one shipped atlas has no alpha at all
and still has emissive content, so the shader cannot be computing `emissive = alpha × colour` — the
Old Jeep would never glow. The RGB is nonzero on both. Therefore the multiply is
**`EmissiveMap.rgb × (block constant)`**, and alpha is a second, optional mask that some lamp families
use and others do not (its role — coverage, glass blend or a secondary glow — is UNKNOWN; see §9).

**Falsifier, stated so the claim can die:** if RGB were the mask and alpha the gate, the Kensington RGB
region would be achromatic (it is: 0 grey texels out of 3223 — it is not) and the Old Jeep would have
nonzero alpha (it has none). Both predictions fail, so that hypothesis is dismissed, not preferred.

### 2.4 The block census corroborates it (decoded, reproduced from card B-03)

| field | measurement over the 44 donor `CarLight` blocks |
|---|---|
| `pre_static` (1,085 B) | **one** distinct value — no per-lamp colour can be stored there |
| `mid_static` (16 B) | 39 distinct values, `(1.662, 65536, 65536, 0)` head LOD1 … `(1.318 / 1.267 / 1.234)` tail LOD1..3, `(0.480)` rear-left mshswap — one float that falls with LOD: an **intensity/fade**, not a colour |
| texture table | 1 distinct value for all 44 |

With no colour in the block and a chromatic, per-texel texture in slot 5, the only place a lamp's
*colour* can come from is the texture's RGB. `cb2 MaterialConsts[4]` (the 64 B whose meaning is
UNKNOWN, MODLOG §102d) is then most plausibly brightness/tint multipliers on top of it — unproven,
and not needed for the pack plan, which never writes those bytes.

### 2.5 What that fixes, and what it leaves open

| question | answer | class |
|---|---|---|
| does JC3 have a per-pixel emissive mask texture? | yes, on `CarLight` only (`s5`) | decoded (header + table) |
| which channel carries the mask/colour the shader multiplies? | **RGB** (colour × constant); alpha is a secondary optional mask, zero on one shipped atlas | MEASURED + INFERRED (§2.3) |
| is `MaterialConsts[4]` the colour, or an intensity? | UNKNOWN — nothing decoded; the pack plan does not need it | UNKNOWN |
| what is alpha's semantic where it is nonzero? | UNKNOWN — 575 texels, disjoint from the colour swatches, mean .49 | UNKNOWN (§9) |
| can `CarPaintMM` carry a per-pixel emissive? | no — constant `m_Emissive` only, 4 values selected by `s2` | decoded |

---

## 3. What the build ships today

| artefact | state | evidence |
|---|---|---|
| `Working/Appearance/build_lights/` | 24 RBMs (8 lamp parts × 3 LODs), one `CarLight` block each; header, 16 B mid-static **and** the 6-name texture table are byte-identical to one donor lamp (all 24 carry the head lamp's LOD1 `mid_static` 1.6621) | card B-03 B4/B6; `spec_check.py --lights` = 0 mismatches |
| lamp texture slot 5 | the **donor's** `car_lights_kensington_modern_emissive_alpha_mpm` — BmAK's own emissive map is never used; the lamp UVs are BmAK's, the atlas is Kensington's | B-03 B5 limit 3 |
| `Batmobile_V3_Emissive` (wheel lights) | `CarPaintMM`; `s2`/`s3` = `Batmobile_V3_Wheel_Lights_M`, `static.Emissive = [0,0,0,0]` — **emits nothing** | `build_bud1/factors.json` |
| `BatmobileV3_Cockpit_Seat` | `CarPaintMM`; `s2`/`s3` = `a00_dummy_black_mpm`, `static.Emissive = [15,15,15,15]` — **whole seat glows** | `build_bud1/factors.json` |
| `Batmobile_V3_Cockpit_MIC` (instruments) | `CarPaintMM`; `s2`/`s3` = `Int_Cockpit_M` (channels 1-3 + tint), `static.Emissive = [0,0,0,0]` | `build_bud1/factors.json` |
| the two `R2` rows | `appearance_plan.json` `.components[]` carries `R2 Batmobile_V3_Int_Cockpit_E` and `R2 Batmobile_V3_Wheel_E` with **no route** | `appearance_plan.json` |
| `Batmobile_V3_Wheel_E` itself | **absent from the grab** — `SLOTS.json` slot 5 names it, no `*_Wheel_E.tga` exists | `ls Working/Appearance/grab/*/Texture2D/*_E.tga` |

So the honest description of the shipped car: the lamp parts are geometry with the *donor's* light
atlas and a *donor* intensity; the cockpit seat emits a flat 15; the wheel-light strip emits 0. No
BmAK emissive pixel reaches the game today.

---

## 4. The BmAK source maps, measured (MEASURED)

8-bit TGAs, `Working/Appearance/grab/Playable_Batmobile_SF/Texture2D/`, channel values 0..1.

| texture | size | R mean / max / coverage | G mean / max / cover | B mean / max / cover | alpha | reading |
|---|---|---|---|---|---|---|
| `Batmobile_V3_Int_Cockpit_E` | 1024² | .001 / **1.00** / 0.4 % | .001 / .71 / 0.4 % | .000 / .15 / 0.4 % | **no alpha channel (3-ch TGA)** | sparse, sparse, **chromatic** — a warm/white cluster mask whose channels are not equal (R reaches 1.0 while B stops at .15): this is already a *colour × coverage* image, the same shape as the JC3 atlas's RGB |
| `Batmobile_DLC_Tumbler_Glass_E` | 2048² | .005 / 1.00 / 2.0 % | .005 / 1.00 / 2.0 % | .005 / 1.00 / 2.0 % | no alpha channel | **achromatic** — a true greyscale mask (all three channels identical); useful as the negative control in T1, and evidence that BmAK authors *both* kinds |
| `Batmobile_V3_Wheel_E` | — | — | — | — | — | **not in the grab** (UNKNOWN, §9) |

The two maps that *are* on disk differ in kind, so the pack plan must state the channel per map rather
than assume one layout (§5).

---

## 5. The packing plan

Nothing is baked here. Three destinations, chosen by what the part's block type can do.

### 5.1 Destination A — `CarLight` slot 5: the exact carrier (lamp parts)

`build_lights` already ships 24 `CarLight` blocks; the only thing missing is that their slot 5 points
at the Kensington atlas instead of at our data. The fix is a texture, not a block-format change.

| step | content |
|---|---|
| A1 atlas geometry | author a **new** emissive atlas in the lamp mesh's own UV space. Not a repaint of the Kensington atlas: our lamp UVs are BmAK UVs (B-03 B5), so the mask must be baked through the same UV set the built lamp geometry carries (the B-03 face list + its UV island layout), or the glow lands on the wrong part of the lens |
| A2 no repeat atlas sharing | one atlas per lamp *family*, at the size the allocator grants; the six-slot table per block is unchanged |
| A3 RGB | `BmAK_E.rgb`, i.e. the colour × coverage image as authored: `Int_Cockpit_E` is already chromatic-sparse (R 1.0 / G .71 / B .15). Where the mask alone is wanted (the `Wheel_E` mask, when it exists), write the mask **replicated across R, G, B** — the shader multiplies RGB, so a greyscale mask in RGB is a neutral mask, and this works even if the runtime colour constant is white |
| A4 alpha | write `max(R,G,B)` as the alpha copy. It costs nothing in BC3 and it survives *both* readings of §2.3: if the real arithmetic is `rgb × a × k`, the result is `mask²` scaled (still monotone, still correct shape); if alpha is a coverage term, it is now consistent with the colour swatches instead of being a disjoint blob |
| A5 format | **BC3/DXT5, format 77**, the vanilla Window/glass and emissive format (`tex2ddsc.convert_image(kind="glass")`); BC1 would drop the alpha block. Linear, **no sRGB flag** on masks (dif flag is 9, mpm/msk 1 — MODLOG §79); the emissive *colour* is the one channel that wants the sRGB flag, so the atlas is written once as colour (flag 9) and the mask rides its RGB with the same encoding the source TGA had — decided at bake time by the allocator's `kind` |
| A6 block side | nothing: the 1,085 B pre-static, the 16 B mid-static and the 6-name table stay the donor's (the clone is the only safe authoring path, MODLOG §102d). Only slot 5's *string* is replaced, which `deploy.py` already registers in `@files.xml` |
| A7 intensity | the per-lamp `mid_static` float is the one number the build should stop cloning: read it per family per LOD from the matching donor block (head 1.662/1.652/1.577, tail 1.318/1.267/1.234 — B-03 B4) so a taillight is not 26 % too bright |

Source → destination, per channel:

| BmAK texture | source channel | JC3 destination | encoding | status today |
|---|---|---|---|---|
| `Batmobile_V3_Int_Cockpit_E` | **R** (peak 1.0; the cluster's brightest emitter) | atlas **R**, and its own value into **G/B** where the authored colour is neutral | BC3 linear, ≤512² | `R2`, routed nowhere |
| `Batmobile_V3_Int_Cockpit_E` | **G .71 / B .15** | atlas **G / B** — they are the colour, not the mask; rescaling them to equal R would flatten a warm cluster to white | same texture | `R2` |
| `Batmobile_V3_Int_Cockpit_E` | derived `max(R,G,B)` | atlas **A** (A4) | BC3 alpha | — |
| `Batmobile_V3_Wheel_E` | — | atlas R/G/B + A | — | **source absent**: UNKNOWN until a grab (§9) |
| `Batmobile_DLC_Tumbler_Glass_E` | R (= G = B) | *not ours* — a different car's asset, kept only as T1's achromatic control | — | reference only |

### 5.2 Destination B — `CarPaintMM`: four bands, the closest carrier (cockpit cluster)

The instrument cluster and the seat are `CarPaintMM` (they have no lamp mesh). On that block there is
**no emissive texture**: `m_Emissive` is a `float4`, one value per material channel, and `s2`
(`PropertyMap`) picks the channel per texel. That is exactly the four-band device the gloss plan uses
(`app-per-pixel-reflectivity.md` §5.1), and it is the closest JC3 system for a per-pixel emissive.

| step | content |
|---|---|
| B1 banding | take the material's emissive mask (`Int_Cockpit_E` where the cluster is, `Wheel_Lights_M` where the wheel strips are), threshold into the same bins the gloss plan chooses for that material, texel-weighted mean per bin |
| B2 `m_Emissive` | `[mean_0, mean_1, mean_2, mean_3] × 15` (15 is the scale the shipped seat uses today: `[15,15,15,15]` — decoding it further needs the shader body) |
| B3 `s2` | the band map from the gloss plan, unchanged; emissive bands ride the *same* selector because both are keyed on the material channel index |
| B4 conflict, stated | the band edges are then shared by **gloss/metallic/clearcoat *and* emissive**: a bin fine enough for the cluster's tiny emitters (0.4 % coverage) will over-quantise the seat's roughness. Two resolutions: (a) accept the joint solve and report the quantisation error for both properties, or (b) move the cluster's faces to a `CarLight` block (Destination A) where the mask is 8-bit, and leave `CarPaintMM` emissive at 0 |
| B5 `s3` | untouched: it is the `TintMap` (per-pixel tint amount), not a property selector |

### 5.3 Destination C — blocks that cannot emit per pixel (named, not wished away)

| block | why not | what the build does instead |
|---|---|---|
| `General` | no emissive input in the header (4 samplers, 3 float4 constants, none named emissive) | never assign an emissive material to a `General` block; keep such faces on `CarPaintMM` (banded) or cut them to a lamp |
| `GeneralMkIII` | `Emissive_1` scalar only, `Emissive_2..4` `[unused]`, no emissive texture | material-level constant; fine for a uniformly glowing part, useless for a cluster |
| `Window` | no emissive sampler; `EmissiveScale` `[unused]` | glass glow must come from the `CarLight` block behind it (the lamp mesh), not from the canopy's `Window` material — that is also how the donor lamps are built (`CarLight` emitter + `Window` lens, LIGHT_SYSTEM §5) |

---

## 6. Where JC3 has no exact carrier — closest system, gap, build action (STAGES.md)

| BmAK feature | closest JC3 system | gap | build action (BUILD stage) |
|---|---|---|---|
| instrument-cluster emissive mask (`Int_Cockpit_E`, 1024², 0.4 % coverage) | `CarLight.s5 EmissiveMap` (8-bit, per pixel) for the lamp geometry; `CarPaintMM.m_Emissive` float4 × `s2` (4 levels) if the faces stay on the cluster's block | if the faces stay `CarPaintMM`: **4 levels instead of 8 bits**, and the bins are shared with gloss; plus the atlas must be re-baked into BmAK UV space | (a) cut/duplicate the cluster's emitter faces into a `CarLight` part (B-03 machinery already exists) and author the atlas (§5.1); or (b) band it (§5.2) and record the per-material quantisation error |
| wheel-light strip mask (`Batmobile_V3_Wheel_E`) | same as above — the `CarLight` blocks for the four arch strips already exist in `build_lights` | **the source texture is not in the grab**, so nothing can be baked from it; and today those blocks emit 0 because the `Batmobile_V3_Emissive` material has `[0,0,0,0]` | new grab of `Batmobile_V3_Wheel_E` (or the master's default), then §5.1; until then the strip stays dark — recorded, not guessed |
| per-lamp emissive **colour** | `EmissiveMap.rgb` (measured §2.3) | `MaterialConsts[4]` is UNKNOWN, so the colour cannot be authored as a constant; it must come from the texture | bake the colour into RGB (A3); leave the 64 B as cloned |
| per-lamp emissive **intensity** | the `CarLight` 16 B `mid_static` float | the build clones one lamp's LOD1 value into all 24 blocks | read it per family per LOD from the donor (A7); the semantics stay UNKNOWN, the numbers stop being wrong |
| emissive mask **channel** on the atlas | RGB (measured); alpha secondary | alpha's meaning is UNKNOWN (zero on one shipped atlas, disjoint blob on the other) | write the mask into RGB **and** copy it to A4's alpha so neither reading fails; the T3 experiment then settles it without a second bake |
| cockpit seat's uniform glow (today `[15,15,15,15]` with a black `s2`) | `CarPaintMM.m_Emissive` | the seat has **no** emissive mask in the grab; BmAK drives it from the material, not a texture | keep material-level 15 (it matches BmAK's material-level value), but move it out of channel 0 so a black `s2` cannot be mistaken for "the whole seat glows" — bands per §5.2 |

---

## 7. Tests that would prove it

Every offline test runs on the current tree. Anything needing the game is gated on
`tmp/freebuff/APPROVED_Q.txt` (STAGES.md test ban).

### T1 — the channel census, with a built-in control (offline, **passes today**)

Decode any candidate emissive atlas and assert, per texture:

```
RGB live region (max>0.15):  texels > 0   AND  grey texels (max-min <= 2/255) < 5 %      -> colour atlas
        or                   chroma spread 0     -> greyscale mask:  the file is a mask, write it to A only
alpha live region: A>0.15 texels; if 0 on a file that has RGB content, alpha is NOT the gate
```

Today: Kensington = 3223 live RGB / 0 grey → colour atlas; Old Jeep = 201 live RGB / 0 alpha → colour
atlas with no alpha mask; `Tumbler_Glass_E` = 2 % coverage, R=G=B → greyscale mask. Pass = each file
lands in the right class, and the class is printed next to the filename so a bake cannot silently pick
the wrong destination.

### T2 — pack round-trip and the A4 copy (offline, after a bake)

1. Decode the written atlas: `A` must equal `max(R,G,B)` per texel (A4), `RGB` must equal the source
   `Int_Cockpit_E` RGB inside its UV islands; PSNR ≥ 40 dB at mip 0.
2. `spec_check.py` on the built lamp RBM: block count, table position 5 = the new atlas, `pre_static`
   and `mid_static` unchanged from the donor; RBM re-encodes **byte-identical** (the gate every other
   block already passes).
3. Negative control: feed the packer a constant mask → the atlas is uniform and the alpha copy is that
   constant; a packer that swaps R and A fails here.

### T3 — which channel the shader multiplies: the falsifier experiment (in-game, 2 runs, gated)

Two builds identical except the atlas's channel layout:

* run A: mask in **RGB** (grey), `A = 1`;
* run B: mask in **A**, `RGB = 1`.

Fixed camera (PILOT card), night, headlights on. Measure the mean luminance inside the lamp's screen
polygon against the same polygon with the lamp off. Predictions: if RGB is the gate, run A glows and
run B does not; if alpha is the gate, the reverse; if both are multiplied, both glow dimmer than the
full mask. Pass = one prediction, written down *before* the run, matches within the measurement's own
noise; the losing layout is recorded as wrong in this report's successor. This is the one experiment
that can overturn §2.3, and it is cheap because §5.1 A4 already ships both channels filled.

### T4 — the banded `CarPaintMM` emissive (offline + in-game)

Offline: `m_Emissive` == per-band mean × 15, and the `s2` band histogram equals the mask's bin
fractions ±1 %. In-game: the cluster's bright texels must land on the band whose value is highest; a
build with the bands reversed is the negative control. Pass: the lit/unlit area ratio on screen
matches the mask's coverage (0.4 %) within 2× — the cluster is tiny, so 2× is the honest tolerance.

### T5 — UV-space check (offline, catches the B-03 B5 trap)

The atlas is authored in the lamp mesh's UV space: rasterise the built lamp's UV triangles, and assert
that ≥ 99 % of the mask's live texels fall inside the union of UV islands and that the mask's
bounding box inside each island matches the BmAK source's bounding box in the same island. A mask
painted for the Kensington layout fails immediately.

### T6 — no-regression gates (offline, every build)

25/25 RBMs byte-identical; `spec_check.py` 0 mismatches / 0 silently inherited template values; every
texture registered in `@files.xml` (SmallPack drops unregistered files, MODLOG §103a); every texture
internal in the `.toc`; model ≤ 4,424 KB, textures ≤ 4,648 KB.

---

## 8. Budget (measured, then derived)

* Current staged build: **3,954 KB of 4,648 KB** textures (MODLOG §103b) → **≈694 KB free**.
* BC3 costs `w·h` bytes: 512² = 256 KB, 256² = 64 KB, 128² = 16 KB. (BC1 would be half but cannot
  carry the alpha copy of A4.)
* One atlas per lamp family at 256² = 64 KB; two families (arch strips, head/tail) = **128 KB**, i.e.
  18 % of the free budget. At 512² it would be 512 KB — the gear box, not a code change.
* Destination B costs **0 new textures**: it reuses the `s2` band map the gloss plan already pays for.

---

## 9. Still UNKNOWN (and what would settle each)

1. **What `EmissiveMap.a` means.** Nonzero on Kensington (575 texels, mean .49, disjoint from the
   colour swatches), zero everywhere on Old Jeep. Tried: the header (declares a `float4` 2d texture,
   no arithmetic), the block census (no relevant field), the neighbouring `dif`/`mpm` of the same
   family (the alpha blob does not coincide with either's bright area). Settled by T3, or by the
   shader body (not on disk — the `.fb.txt` files are reflection headers only).
2. **`CarLight`'s `cb2 MaterialConsts[4]` (64 B).**   Tried: MODLOG §102d, LIGHT_SYSTEM §5 and its line 287 ("which bytes are the emissive
   colour/intensity" — open), the donor census (byte-identical across
   44 blocks, so nothing varies there). Settled by a decoded parameter block or a one-lamp A/B in game
   (T3 with the constant changed, not the texture).
3. **`Batmobile_V3_Wheel_E`.** `SLOTS.json` names it; no file in the 115-file grab; no route in
   `appearance_plan.json`. Settled by extending the grab (the master that owns slot 5's
   `Emissive_Map`), or by the master's default texture name if it is parameterised.
4. **The seat's `[15,15,15,15]` scale.** 15 is what `factors.py` wrote from `Emissive_*`; whether the
   shader multiplies by 15, by `15/255`, or applies a tone-map afterwards is not decoded. It matters
   for B2's absolute values, not for the channel.
5. **Whether `CarPaintMM`'s four `m_Emissive` components are the same index as `s2`'s four channels.**
   The same question the gloss plan raises (`app-per-pixel-reflectivity.md` §9.7). T4's band
   histogram is where it would show up as a systematic mismatch.

---

## 10. Reproduce

```bash
cd "E:/Modding/JustCause3/JC3-Batmobile"

# 1. the interfaces (decoded headers, on disk)
grep -n "sampler\|Emissive\|MaterialConsts" Tools/JCMR-src/assets/jc3/shaders/carlight.fb.txt
grep -n "m_Emissive\|sampler" Tools/JCMR-src/assets/jc3/shaders/carpaintmm.fb.txt
grep -n "Emissive\|SamplerRegular" Tools/JCMR-src/assets/jc3/shaders/generalmkiii.fb.txt

# 2. the block's texture table (position 5 = EmissiveMap)
uv run python - <<'EOF'
import sys; sys.path.insert(0,'Tools/scripts'); import rbm_geom
m=rbm_geom.decode(open('Working/Appearance/build_lights/sportsmuscle_headlight_f_l_lod1.rbm','rb').read())
for b in m.blocks:
    if rbm_geom.BLOCK_NAMES.get(b.type_hash)=='CarLight':
        print(len(b.pre_static), b.mid_static.hex()); [print(i,t) for i,t in enumerate(b.textures)]
EOF

# 3. the shipped atlases, measured (the channel census, T1)
uv run --with pillow --with numpy python - <<'EOF'
import sys,struct; sys.path.insert(0,'Tools/scripts'); import tex2ddsc as TX; import numpy as np
def top(p):
    d=open(p,'rb').read()
    m,v,s0,dim,fmt,w,h,depth,flags,mcf,mc=struct.unpack_from("<4sHBBIHHHHBB",d,0)
    st=mcf-mc; ww,hh=w>>st,h>>st
    n=(max(1,(ww+3)//4))*(max(1,(hh+3)//4))*16
    return (TX.decode_bc3 if fmt==77 else TX.decode_bc1)(d[128:128+n],ww,hh)
for p in ('Working/Serpente/aaf/models/jc_vehicles/00_shared/car_lights/textures/car_lights_kensington_modern_emissive_alpha_mpm.ddsc',
          'Research/VanillaOldJeep/aaf/models/jc_vehicles/01_land/v0000_car_autostraad_oldjeep/textures/v0000_car_autostraad_oldjeep_lights_emissive_alpha_mpm.ddsc'):
    a=top(p).astype(np.float32)/255; RGB=a[:,:,:3]; A=a[:,:,3]; M=RGB.max(2)>0.15
    grey=int(((RGB.max(2)-RGB.min(2))<=2/255)[M].sum())
    print(p.split('/')[-1], 'RGB>0.15 %d grey %d | A>0.15 %d Amean %.2f | both %d'%(
        M.sum(), grey, (A>0.15).sum(), float(A.mean()), int((M&(A>0.15)).sum())))
EOF

# 4. the BmAK side
uv run --with pillow --with numpy python - <<'EOF'
import glob,os; from PIL import Image; import numpy as np
for f in sorted(glob.glob('Working/Appearance/grab/*/Texture2D/*_E.tga')):
    im=Image.open(f); a=np.asarray(im).astype('f4')/(65535.0 if np.asarray(im).dtype==np.uint16 else 255.0)
    print(os.path.basename(f), im.size, a.shape[2] if a.ndim==3 else 1,
          ['%.3f/%.2f/%.1f%%'%(a[:,:,i].mean(), a[:,:,i].max(), 100.0*(a[:,:,i]>0.02).mean()) for i in range(a.shape[2])])
EOF

# 5. what the build shipped (emissive values + slots)
uv run python - <<'EOF'
import json; f=json.load(open('Working/Appearance/build_bud1/factors.json'))
for n,m in f['materials'].items():
    e=(m.get('inputs') or {}).get('static.Emissive')
    if e: print(n, e['value'], str(e['source'])[:60], '| s2', (m.get('textures') or {}).get('s2',{}).get('vanilla') or (m.get('textures') or {}).get('s2',{}).get('tga'))
EOF
```

### Evidence index

| claim | file |
|---|---|
| `CarLight` `s5 EmissiveMap`, `MaterialConsts[4]`, `s4 NormalDetailMap` | `Tools/JCMR-src/assets/jc3/shaders/carlight.fb.txt` |
| `CarPaintMM` has `m_Emissive` and **no** emissive sampler | `Tools/JCMR-src/assets/jc3/shaders/carpaintmm.fb.txt` |
| `GeneralMkIII` `Emissive_1` only, no emissive texture | `Tools/JCMR-src/assets/jc3/shaders/generalmkiii.fb.txt` |
| `Window` has no emissive input; `EmissiveScale` `[unused]` | `Tools/JCMR-src/assets/jc3/shaders/window.fb.txt` |
| block table position 5 = the emissive atlas | `Working/Appearance/build_lights/*.rbm` via `Tools/scripts/rbm_geom.py` |
| 1,085 B `pre_static` × 44 identical; `mid_static` 39 values, one float tracking LOD | `Research/challenge/card-B-03.md` (B4, reproduced in §2.4) |
| `CarLight` parameters undecoded | MODLOG §102d; `Research/JC3Grab/LIGHT_SYSTEM.md` §5 and its line 287 ("which bytes are the emissive colour/intensity") |
| the channel census of the two shipped atlases | `Working/Serpente/.../car_lights_kensington_modern_emissive_alpha_mpm.ddsc`, `Research/VanillaOldJeep/.../v0000_car_autostraad_oldjeep_lights_emissive_alpha_mpm.ddsc` |
| BmAK masks measured here | `Working/Appearance/grab/Playable_Batmobile_SF/Texture2D/Batmobile_V3_Int_Cockpit_E.tga`, `.../Batmobile_DLC_Tumbler_Glass_E.tga` |
| `Wheel_E` named but absent | `Research/BatmobileGrab/SLOTS.json` slot 5; `Working/Appearance/appearance_plan.json` `R2` rows; `ls *_E.tga` |
| today's emissive values and slots | `Working/Appearance/build_bud1/factors.json` |
| 24 built lamp blocks clone the donor table | `Working/Appearance/build_lights/`, `spec_check.py --lights`, card B-03 B4/B6 |
| four-band device and the gloss conflict | `tmp/freebuff/reports/app-per-pixel-reflectivity.md` §5.1 |
| texture budget 3,954/4,648 KB | MODLOG §103b |
