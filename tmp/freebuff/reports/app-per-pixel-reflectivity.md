# APP — per-pixel reflectivity/roughness: what JC3 reads, and the channel-packing plan

Card: appearance, per-pixel material response. **Plan only — no bake, no build, no install, no game
launch.** Every claim below is labelled:

* **decoded** — a file in this project carries the bytes and a project tool (or a quoted source file)
  reads them;
* **derived** — a rule + its stated inputs;
* **INFERRED** — a reading of artwork statistics or plausibility, no code proof;
* **UNKNOWN** — what was tried, and what would settle it.

## 0. Change statement (AGENTS.md)

| item | value |
|---|---|
| intended change | add one report: the JC3 channel audit + the packing plan + the tests that would prove it |
| file | `tmp/freebuff/reports/app-per-pixel-reflectivity.md` (this file) |
| why this file | the brief names it; every research/report output of this project lives under `tmp/freebuff/reports/`, and the evidence it cites is read-only |
| reverted by | deleting this file. Nothing else was written: no edit to `Research/`, `Tools/`, `Working/`, `Builds/`, no texture baked, no `.rbm` re-encoded, no game launched |

---

## 1. Verdict

1. **"JC3 varies properties only by channel" is wrong as stated.** The sentence in `D3` is about
   `CarPaintMM`'s `s2`, and `s2` *is* sampled per pixel: it selects one of the block's four material
   channels at each texel. The true limitation is **four discrete levels, not eight bits** — exactly
   the counter-example card T-21 (`Research/challenge/card-T-21.md`, A10) already raised against D3.
   So the four maps were dropped for a limitation the block does not have.
2. **`CarPaintMM` cannot carry continuous gloss.** Its static parameters are four 16-byte vectors
   (`m_SpecularGloss`, `m_Metallic`, `m_ClearCoat`, `m_Emissive`), each read once per material
   channel, and there is no reflectance/F0 member at all (T-21 A11, which holds). Four bands is the
   ceiling on this block type.
3. **`GeneralMkIII` has separate per-pixel Gloss and Metallic texture slots** (`Gloss1Map`,
   `Metallic1Map`) — the only explicit per-pixel gloss/metallic carrier found in JC3, and it is used
   on vehicle parts (three `GeneralMkIII` blocks in the donor's own missile-signature meshes). This is
   the exact carrier for the four dropped maps, at the cost of a block-type swap per part.
4. **The current fallback is actively wrong on three of the four maps.** `factors.py` reads
   `R` as roughness and `B` as metalness and skips a map whose `R` channel is dead
   (`Tools/scripts/factors.py:262-278`). Measured now: `Batmobile_V3_Int_Cockpit_S` and
   `Batmobile_V3_Missile_Upgrade_S` have **R = 0 on every texel**, and
   `Nimbus_Power_Cell_S` has **B = 0 on every texel** (§4). Result in the staged build
   (`Working/Appearance/build_bud1/factors.json`): `BatmobileV3_Cockpit_Seat` and
   `BatmobileV3_Upgrades_MAT_INST` get **gloss 0.000, metallic 0.000** — a mirror-matte seat and
   missile pod — while `Nimbus_Power_Cell_Mat` gets gloss 0.5592 / **metallic 0.0 from a dead
   channel**, and `Batmobile_V3_Discbreak_MIC` gets gloss 0.9586 from a channel that is 0 on ~90 % of
   the map.
5. **Two premises in the brief need correcting, with evidence.** (a) The `D3` rule has **4 rows**, not
   "the four maps plus the body masks": `appearance_plan.json` `.components[]` with `rule: "D3"` is
   exactly `Batmobile_V3_BRAKE_DISC_R`, `Batmobile_V3_Int_Cockpit_S`, `Batmobile_V3_Missile_Upgrade_S`,
   `Nimbus_Power_Cell_S`. (b) The **separation masks are not D3 rows** — they are mapped, to `s2`+`s3`
   (`factors.py:292-306`); `Batmobile_V3_Int_Cockpit_M` and `Batmobile_V3_Wheel_Lights_M` are bound
   today. What *is* missing is the **body's own** mask: the master's default
   (`WheelArch_MicroMasks`, MODLOG §79) is not in the grab, so every body/wheel/undercarriage/turret
   block gets `a00_dummy_black_mpm.ddsc` in `s2`/`s3` — a gap in the mask asset, not a channel drop.
6. **A carrier conflict the plan has to design around:** `s2` (`PropertyMap`) and `s3` (`TintMap`) are
   different textures, so packing roughness into `s2` does **not** disturb the tint bands in `s3`.
   That is what makes the four-band scheme possible without giving up per-pixel colour.

---

## 2. What each JC3 block actually reads

Source of every row: the reflection headers shipped in this project at
`Tools/JCMR-src/assets/jc3/shaders/` (the compiled shader bodies are **not** on disk — the headers
declare the interface only, which is why "what a texture's channels mean" is separated in §3).

### 2.1 `CarPaintMM` — `carpaintmm.fb.txt` (7126 B), `carpaintmm_mask.fb.txt`

| slot | sampler (decoded) | texture binding | what it is |
|---|---|---|---|
| `s0` | `DiffuseSampler` | `t0 DiffuseMap` | albedo, sRGB (vanilla dif header flag 8, MODLOG §79) |
| `s1` | `NormalMap` | `t1 NormalMap` | tangent normal (BC5) |
| `s2` | `PropertyMap` | `t2 PropertyMap` | **per-pixel material-channel selector** (see §3) |
| `s3` | `TintMap` | `t3 TintMap` | per-pixel tint amount |
| `s4` | `DamageNormalMap` | `t4` | damage normal — feature off by decision (R1/APP-7) |
| `s5` | `DamageAlbedoMap` | `t5` | damage albedo — off |
| `s6` | `DirtMap` | `t6` | dirt — off (`SupportDirt 0`) |
| `s7` | `DecalAlbedoMap` | `t7` | decal albedo — off (`SupportDecals 0`) |
| `s8` | `DecalNormalMap` | `t8` | decal normal — off |
| `s9` | `DecalPropertyMap` | `t9` | decal property map — off |
| — | *(no sampler declared)* | `t16 LayeredAlbedoMap`, `t17 OverlayAlbedoMap` | layered/overlay albedo are declared as textures but **bound to no sampler** in this header; `SupportLayered`/`SupportOverlay` are 0 |

Constant buffers (decoded, names + offsets verbatim from the header):

```
cb2 CarPaintStaticMaterialParams : 18 float4 + 7 floats (288 B + 28 B)
    m_SpecularGloss@0  m_Metallic@16  m_ClearCoat@32  m_Emissive@48  m_DiffuseWrap@64
    m_DirtParams@80 m_DirtBlend@96 m_DirtColor@112
    m_DecalCount@128[unused] m_DecalWidth@144 m_Decal1..4Color@160..208 m_DecalBlend@224
    m_Damage@240 m_DamageBlend@256 m_DamageColor@272
    SupportDecals@288 SupportDmgBlend@292 SupportLayered@296 SupportOverlay@300
    SupportRotating@304[unused] SupportDirt@308 SupportSoftTint@312
cb6 CarPaintDynamicMaterialParams: m_TintColorR@0 m_TintColorG@16 m_TintColorB@32
    _unused@48 m_SpecularGlossOverride@64 m_MetallicOverride@68 m_ClearCoatOverride@72
cb7 CarPaintDynamicObjectParams: m_DecalIndex@0 m_DirtAmount@16
cb8 RBIInfo: ModelDiffuseColor@128 ...
```

`m_SpecularGloss` is a **float4**, i.e. four gloss values, one per material channel — the exact
structure the four-band scheme exploits. The `_mask` variant adds `cb4 booleans`
(`float2 AlphaMulRef`) and is otherwise the same block.

### 2.2 `Window` — `window.fb.txt`

| slot | sampler | texture | note |
|---|---|---|---|
| `s0` | `DiffuseMap` | `t0` | tinted albedo; alpha is opacity |
| `s2` | `NormalMap` | `t2` | **normal is on `s2`, not `s1`** — the header declares no `s1` sampler |
| `s3` | `PropertyMap` | `t3` | property map exists on glass too |
| `s9` | `RainOccluderSampler` | `t40` | engine weather |
| `s11` | `CubeMapSampler` | `t11 EnvironmentCube` | reflection probe |

`cb1 MaterialConsts`: `SpecGloss@0`, `SpecFresnel@4`, `DiffuseRougness@8`, `TintPower@12`,
`MinAlpha@16`, `UVScale@20`, `unused_@24`, `DamageMaskWeight@32[unused]`, `DamageRampWeight@36[unused]`,
`Alpha@40` — all **scalar** (material level), 11 floats total.

Two consequences the plan must carry:

* **`SpecFresnel` is the only F0-shaped input anywhere in these five blocks.** `CarPaintMM` has none.
  For glass, reflectivity at least has a named carrier; whether it is per-pixel via `s3` is UNKNOWN.
* **The build binds glass's normal to block table position 1** (`factors.json`
  `Batmobile_V3_Glass_INST.textures = {"s0", "s1"}`), while the shader samples the normal at `s2`.
  If block table position == sampler index (true for `CarPaintMM`: COLOUR.md §2 maps position→sampler
  and the suffixes agree), the canopy normal is landing on an unbound sampler. **Derived finding,
  needs the one-line test in §7 T5a.** It does not affect this plan's gloss channel, but it is the
  same class of defect and it is free to check.

### 2.3 `CarLight` — `carlight.fb.txt`

`cb2 cbMaterialConsts`: `float4 MaterialConsts[4]` (64 B, **member meanings undecoded**, MODLOG
§102d). Samplers: `s0 DiffuseMap`, `s1 NormalMap`, `s2 PropertyMap`, `s4 NormalDetailMap`,
`s5 EmissiveMap`. Per-pixel property selection is *structurally* present (`s2`), but with the 64 B
undecoded there is nothing to bind the selected values to.

### 2.4 `General` — `general.fb.txt`

`cb2 cbMaterialConsts`: `float4 MaterialConsts[3]` (48 B, undecoded). Samplers: `s0 DiffuseMap`,
`s1 NormalMap`, `s2 PropertiesMap`, `s3 AOBlendMap`. A per-pixel property map exists; its effect is
not decodable from the header (UNKNOWN), so it is not a target in this plan.

### 2.5 `GeneralMkIII` — `generalmkiii.fb.txt` + `renderblockgeneralmkiii.cc`

Constant buffers:

```
cb1: EnableVariableDialecticSpecFresnel@16, UseMetallicVer2@20          (two per-material switches!)
cb2 MaterialConsts (70 floats): NormalStrength_1[unused] Reflectivity_1[unused]
     Roughness_1@8 DiffuseWrap_1@12 Emissive_1@16 Transmission_1@20 ClearCoat_1@24
     Roughness_2..4 / Reflectivity_2..4 / ... all [unused]   (material 1 only is live)
     Layered*/Decal*/Overlay*/Damage* : 55 more floats, all [unused]
```

Texture slots, from `RenderBlockGeneralMkIIIImpl::draw_ui`'s `texture_names[]`
(`Tools/JCMR-src/src/game/games/justcause3/renderblocks/renderblockgeneralmkiii.cc`), 20 slots:

| idx | JCMR label | live on vehicle parts? |
|---:|---|---|
| 0 | Albedo Map | yes (`t0 Albedo1Map`) |
| 1 | **Gloss Map** | yes (`t1 Gloss1Map`) |
| 2 | **Metallic Map** | yes (`t2 Metallic1Map`) |
| 3 | Normal Map | yes (`t3 Normal1Map`) |
| 4-5 | Layered Mask / Height | `USE_OVERLAY/LAYERED` |
| 6-10 | Layered Albedo/Gloss/Metallic/Normal/UNUSED | `USE_LAYERED` |
| 11-14 | Decal Albedo/Gloss/Metallic/Normal | `USE_DECAL` |
| 15-19 | Damage Albedo/Gloss/Mask/Metallic/Normal | `USE_DAMAGE` |

Block header is **decoded** (DECODE_DEPTH4, G3-19b): `version 5`, `Attributes 0x68`, 70-float
`MaterialConsts2`, a texture table (457 B in the donor's three signature meshes, "slots used 4 of 20"),
then quantized positions + a 20-byte attribute stream + u16 indices, summing to the payload byte-exactly
in all three files.

Two **derived** caveats, both tested in §7:

1. The donor's four used textures are `..._billfire_dif.ddsc`, `..._billfire_mpm.ddsc`,
   `dummy_black.ddsc`, `..._billfire_nrm.ddsc` (DECODE_DEPTH4 §2). Under the JCMR label order that is
   slot0=dif, **slot1(Gloss)=mpm**, **slot2(Metallic)=dummy_black**, slot3=nrm. So JC3's own parts put
   an `mpm` file in the Gloss slot and a black in the Metallic slot — consistent, but it means the
   *file name* `mpm` is not evidence of which slot it is in.
2. Which **channel** of `Gloss1Map` / `Metallic1Map` is read is not in the header (it declares
   samplers, not arithmetic). This is the one number the plan cannot supply offline; §7 T4 names it.

---

## 3. What the channels mean, by evidence class

| block | texture | meaning | class |
|---|---|---|---|
| `CarPaintMM` | `s2` | RGB selects material channel 1/2/3 per texel; black (no channel) → channel 0. Vanilla stats: `body_mpm` R avg 235 (92 % of texels), G/B 3.8 % each; `int_mpm` B 26 %. Block 4-vectors: comp1 gloss .40/metal 1/coat 1, comp2 .374/0/0, comp3 1.0/1/0, comp0 0/0 (MODLOG §78) | **INFERRED** from vanilla pixels — the strongest evidence that exists, because the shader body is not on disk (COLOUR.md §6 item 3) |
| `CarPaintMM` | `s3` | RGB = amount of tint colour R/G/B (vanilla `body_msk` R avg 151, 85 % >128, G/B ~0 → one-colour paint tinted on the red vector) | **INFERRED**, same source |
| `CarPaintMM` | `s0..s3` table order | block table position == sampler index (COLOUR.md §2: dif/nrm/mpm/msk in positions 0-3, suffixes agree) | **decoded** for the donor's paint blocks; **derived** as a general rule |
| `CarPaintMM` | PS input `TEXCOORD6 .y` | one per-vertex scalar is read by the pixel shader (`carpaintmm.fb.txt` input signature: `TEXCOORD 6 xyz NONE float y`). No project doc names it. It is the only unused per-vertex channel that could carry a per-vertex property multiplier | **UNKNOWN** — candidate, not a plan input |
| `Window` | `s3` | a `PropertyMap` exists; whether it selects the same four material channels (and `SpecGloss`/`SpecFresnel`/`DiffuseRougness` are per-channel) is not shown by the header, which declares **scalars** in `cb1` and no float4 of properties | **UNKNOWN** |
| `CarLight` | `s2` | property map declared; consumers undecoded | **UNKNOWN** (MODLOG §102d) |
| `General` | `s2` | `PropertiesMap` declared; consumers undecoded | **UNKNOWN** |
| `GeneralMkIII` | `Gloss1Map`, `Metallic1Map` | separate per-pixel gloss and metallic textures, named by the block's own UI table; `Roughness_1` scalar and `UseMetallicVer2` switch exist alongside them | **decoded** (slots exist and are named) / **UNKNOWN** (channel inside each) |

**Bottom line for the plan:** the only *continuous* per-pixel gloss/metallic carrier with a name is
`GeneralMkIII`; the only carrier available **on the block the car already uses** is `CarPaintMM`'s `s2`
with four levels. Everything else (Window/CarLight/General `s2`/`s3`) is a declared slot whose
consumers are not decoded, and must be tested before it is relied on.

---

## 4. The BmAK source maps, measured

Instrument: Pillow → numpy, 8-bit TGAs from `Working/Appearance/grab/Playable_Batmobile_SF/Texture2D/`,
channel values normalised to 0..1 (command in §10). This is the census `factors.py` never runs — it
looks only at `R`'s standard deviation.

| texture | size | R mean / p50 / std | G mean / p50 / std | B mean / p50 / std | dead channel |
|---|---|---|---|---|---|
| `Batmobile_V3_BRAKE_DISC_R` | 1024×512 | .041 / 0.00 / .197 | .264 / .24 / .091 | .431 / .45 / .307 | none fully, but R = 0 on ~90 % of texels |
| `Batmobile_V3_Int_Cockpit_S` | 1024² | **.000** / 0 / **.000** | .378 / .37 / .092 | .277 / .32 / .100 | **R is exactly 0 everywhere** |
| `Batmobile_V3_Missile_Upgrade_S` | 1024² | **.000** / 0 / **.000** | .453 / .39 / .144 | .337 / .30 / .138 | **R is exactly 0 everywhere** |
| `Nimbus_Power_Cell_S` | 1024² | .441 / .49 / .186 | .626 / .62 / .139 | **.000** / 0 / **.000** | **B is exactly 0 everywhere** |
| `Batmobile_V3_TEXTURES_Tyre_V2_R` | 1024² | .948 / 1.00 / .222 | .205 / .20 / .104 | .118 / .09 / .149 | none |
| `Batmobile_V3_TEXTURES_Wheel_V2_R` | 2048² | .391 / .29 / .206 | .215 / .18 / .089 | .356 / .39 / .252 | none |
| `Batmobile_V3_Glass_S` | 512² | .565 / .86 / .462 | .074 / .11 / .050 | .542 / .94 / .478 | none (G only reaches .19) |
| `Batmobile_V3_Int_Cockpit_M` | 1024² | .081 / 0 / .272 | .009 / 0 / .094 | .250 / 0 / .431 | sparse, all three used |
| `Batmobile_V3_Wheel_Lights_M` | 1024² | .186 / 0 / .388 | .014 / 0 / .115 | .118 / 0 / .320 | sparse |
| `Batmobile_V3_Body_N` | 2048² | .500 / .50 / .097 | .500 / .50 / .100 | .975 / 1.00 / .051 | normal map (not a property map) |

### 4.1 The channel order is not established — and the two candidate orders disagree

Two hypotheses survive on the numbers, and neither is decoded:

* **H1 (what `factors.py` implements): R = roughness, G = reflectivity, B = metalness.**
  Fits tyre (rough .948, non-metal .118) and disc (rough .041, metal .431). **Falsified** by
  `Int_Cockpit_S` and `Missile_Upgrade_S`: roughness 0 everywhere is a mirror, and both are matte
  leather/paint. It is also the reading MODLOG §79 itself labels "physical plausibility", not a decode.
* **H2: R = reflectivity, G = roughness, B = metalness.**
  Fits seat (ref 0 dead, rough .378), missile (rough .453), Nimbus (rough .626, metal 0), disc
  (rough .264, metal .431). **Falsified** by the tyre, whose R = .948 would make rubber the most
  reflective surface on the car.
* **H3 (per-master packing): `_S` maps carry (dead, rough, metal); `_R` maps carry
  (rough, reflect, metal).** Fits all six observed maps, but has no documentary support — it says the
  two masters that author these maps use different layouts, which is unlikely and would be a bug in
  BmAK's own art pipeline.

The one place the layout is written down is the **glass mask's parameter display name** in the BmAK
props, quoted verbatim in `Research/BatmobileGrab/MATERIALS.md:972` and `SLOTS.md:26`:
`Mask (R=Reflect / G=Rough / B=Normal map compression artifacts fix)` → **H2's order** for that
parameter, plus a third channel used as a normal-artifact fix. That is **decoded** (it is the authored
parameter string), but it is a *different* parameter from `Ref_n_Rough_Map`, so it cannot be carried
across without a test.

**Planning decision:** the plan below packs under a single declared order per map and makes the order
itself a one-variable test (§7 T3). Nothing is baked on the strength of H1 or H2.

### 4.2 What the current build actually produced from these maps

From `Working/Appearance/build_bud1/factors.json` (gloss = 1 − mean(R), metallic = mean(B); a map
whose R std ≤ 0.01 is skipped with a warning):

| material | gloss (spec) | metallic | source string |
|---|---|---|---|
| `Batmobile_V3_Discbreak_MIC` | 0.9586 | 0.4310 | `1 - mean(R)` / `mean(B)` of `BRAKE_DISC_R` |
| `BatmobileV3_Wheel_V2_MIC` | 0.6088 | 0.3561 | same, `Wheel_V2_R` |
| `Nimbus_Power_Cell_Mat` | 0.5592 | **0.0000** | `1 - mean(R)` — metallic read from the dead B |
| `BatmobileV3_Cockpit_Seat` | **0.0000** | **0.0000** | *R channel dead (std 0.000); packing unknown, not read* |
| `BatmobileV3_Upgrades_MAT_INST` (missile) | **0.0000** | **0.0000** | same |
| `Batmobile_V3_Mainbody_NEW_MIC` / `WheelArchs` / `Undercarriage` / `Turret` | 0.4000 ×4 | 0,0,1,0 | scalars only; **the painted body never sees its roughness map at all** |
| `Batmobile_V3_Cockpit_MIC`, `Batmobile_V3_Emissive` | 0.4000 ×4 | 0.90 / 0.92 | scalars; `s2`/`s3` hold `Int_Cockpit_M` / `Wheel_Lights_M` |
| `Batmobile_V3_Glass_INST` | — | — | `Window`, only `s0`+`s1`; **no roughness or reflectivity of any kind** |

That table is the "flat plastic car" in numbers: the four maps are either unused, read from a dead
channel, or collapsed to a single material-level value.

---

## 5. The channel-packing plan

Nothing is rebaked here. Each row states what the build stage would write, from which BmAK channel,
into which JC3 slot, under which order hypothesis.

### 5.1 Destination A — `CarPaintMM` four-band (the painted body keeps its block type)

The device: `s2` = `PropertyMap` (per-texel selector, §3) × `m_SpecularGloss`/`m_Metallic` as float4
(per-channel values). One selector, four bands, and **`s3` stays free for tint**.

| step | content |
|---|---|
| A1 banding | from the material's roughness map, fixed bin edges at roughness **0.15 / 0.40 / 0.70** → bins 0..3. For each bin, texel-weighted mean roughness, then `gloss_k = 1 − mean_k`, then the existing `GLOSS_CAP` (0.45, `VALUES.json`) applied per band |
| A2 `s2` | BC1, **linear** (no sRGB flag: vanilla mpm/msk carry flag 1, MODLOG §79). Bin 1 → R=255, bin 2 → G=255, bin 3 → B=255, bin 0 → black. That is the same encoding the vanilla `body_mpm` uses (92 %/3.8 %/3.8 %) |
| A3 gloss vector | `m_SpecularGloss = [gloss_0, gloss_1, gloss_2, gloss_3]`, `source` = `bmak:<map>:<channel> band k (mean r=.)` |
| A4 metallic vector | same four bins, metallic = band mean of the metalness channel, **not** a single global mean |
| A5 `s3` | unchanged: tint texture if a separation mask exists, else `a00_dummy_black_mpm.ddsc` |
| A6 per-block override | `cb6`'s `m_SpecularGlossOverride`/`m_MetallicOverride` stay at the channel-1 value (current behaviour) so the palette path does not flatten the bands |

Textures this destination consumes (source channel per the declared order, H1 shown; H2 is the same
row with the two names swapped, selected by T3):

| BmAK texture | source channel → | JC3 slot | encoding | status today |
|---|---|---|---|---|
| `Batmobile_V3_BRAKE_DISC_R` | R (roughness) → band index; B (metalness) → metallic band | `s2` of `Batmobile_V3_Discbreak_MIC` | BC1 linear, 512² | dropped (D3) |
| `Batmobile_V3_Int_Cockpit_S` | **G** (roughness under H2; H1's R is dead) → band; B → metallic | `s2` of `BatmobileV3_Cockpit_Seat` | BC1 linear, 512² | dropped (D3) |
| `Batmobile_V3_Missile_Upgrade_S` | G → band; B → metallic | `s2` of `BatmobileV3_Upgrades_MAT_INST` | BC1 linear, 256² | dropped (D3) |
| `Nimbus_Power_Cell_S` | R or G → band (B dead, so metallic comes from the scalar 0.0) | `s2` of `Nimbus_Power_Cell_Mat` | BC1 linear, 256² | dropped (D3) |
| `Batmobile_V3_TEXTURES_Tyre_V2_R` | R → band; B → metallic | `s2` of the tyre block | BC1 linear, 512² | collapsed to one value |
| `Batmobile_V3_TEXTURES_Wheel_V2_R` | R → band; B → metallic | `s2` of `BatmobileV3_Wheel_V2_MIC` | BC1 linear, 512² | collapsed to one value |
| body / wheel-arch / undercarriage / turret | **no map on disk** (mask + `_R` absent) | `s2` stays dummy black | — | gap: needs the BmAK body `_S`/mask asset or a scalar band set |

### 5.2 Destination B — `GeneralMkIII` block swap (continuous maps, the exact carrier)

For the parts whose maps are continuous and whose silhouettes are simple (brake disc, cockpit seat,
missile pod, power cell), the exact answer is a block-type change in the RBM:

| BmAK texture | source channel → | JC3 slot | encoding | gap |
|---|---|---|---|---|
| `Batmobile_V3_BRAKE_DISC_R` | R → `Gloss1Map`; B → `Metallic1Map` | GeneralMkIII slot 1 / slot 2 | BC1 linear, full resolution | **which channel of each map** (T4) |
| `Batmobile_V3_Int_Cockpit_S` | G → `Gloss1Map`; B → `Metallic1Map` | same | BC1 linear | same |
| `Batmobile_V3_Missile_Upgrade_S` | G → `Gloss1Map`; B → `Metallic1Map` | same | BC1 linear | same |
| `Nimbus_Power_Cell_S` | R/G → `Gloss1Map` (B dead) | same | BC1 linear | same |
| `Batmobile_V3_Glass_S` | G → not applicable (glass is `Window`) | — | — | `GeneralMkIII` is opaque; glass keeps `Window` (§5.3) |

Supporting scalars: `Roughness_1` (the live member) as the map's multiplier, `ClearCoat_1` from the
lacquer flag (1.0 where `Normal_Map_Lacquer` is bound — seat and missile), `UseMetallicVer2` /
`EnableVariableDialecticSpecFresnel` as the metallic-model switch. `Reflectivity_1` is `[unused]` in
this shader, so **reflectivity per pixel has no scalar on this block either** — it can only ride the
`Metallic1Map` channel. That is the residual gap for BmAK's `Reflectivity` parameter (§6, row 1).

Block-type cost, stated honestly: the RBM writer emits whole blocks; `rbm_geom.py` already names and
frame-decodes `GeneralMkIII` (`RB_GENERALMKIII = 0x2CEC5AD5`, `BLOCK_NAMES`, `rbm_geom.py:75,96`), and
DECODE_DEPTH4 proves the payload frames byte-exactly — but no project writer has emitted one yet
(G3-04e: "the shared codec stops at `GeneralMkIII`, which has no serializer"). Build action: a
`GeneralMkIII` serialiser + a per-part block swap, gated by the byte-identical round trip the other
block types already pass.

### 5.3 Destination C — `Window` (the canopy)

`Glass_S` is the one BmAK map whose two channels are **named in the authored parameter**:
R = Reflect, G = Rough (`MATERIALS.md:972`). Today the build writes none of it.

| BmAK texture | source channel → | JC3 slot / input | encoding | gap |
|---|---|---|---|---|
| `Batmobile_V3_Glass_S` | G (rough, range 0..0.19 only) → `s3 PropertyMap` bands selecting `SpecGloss`; R (reflect, 0..1) → 4 band levels of `SpecFresnel` **if** `s3` selects those too | `Window` `s3` = BC1 linear 256² | `s3` | `Window`'s `s3` consumer is UNKNOWN (header declares scalars only) — T5b |
| `Batmobile_V3_Glass_A` | alpha = opacity | `s0` alpha (already done) | BC3 | — |
| `Batmobile_V3_Glass_N` | N | `s2` (header binding) — the build writes table position 1 | BC5 | T5a: move to the slot the header samples |

If `s3` turns out not to select properties on `Window`, the fallback is material-level:
`SpecGloss = 1 − mean(G) ≈ 0.926`, `SpecFresnel = mean(R) ≈ 0.565`, `DiffuseRougness = mean(G)`, and
the per-pixel part is recorded as a gap.

### 5.4 Destination D/E — `CarLight` and `General` (blocked, named)

Both blocks declare a property map (`CarLight s2`, `General s2 PropertiesMap`) but neither block's
constant buffer is decoded (`float4 MaterialConsts[4]` / `[3]`, MODLOG §102d). They are **not** used by
this plan until those bytes are decoded and a test shows the property map selects them. Concretely,
`CarLight` is where the wheel-light emissive rows land, not where roughness lands.

### 5.5 What stays material-level, and what stays dropped by decision

* **Kept scalar:** `GLOSS_CAP = 0.45` for the paint channel (MAT-1/GRB-6). The bands let four values
  *below* the cap vary; the cap itself is unchanged, and lifting it is a separate one-variable test.
* **Still dropped, with the right reason:** dirt (`s6`, `SupportDirt 0`), damage (`s4`/`s5`,
  `SupportDmgBlend 0`), decals (`s7`-`s9`, `SupportDecals 0`), layered/overlay (`t16`/`t17`, no
  sampler), anisotropy (no input in any of the five blocks), colour ramps (no lookup), micro-detail
  (no detail slot — P1 bakes it into `s1`, unchanged by this plan).
* **Reclassified by this plan:** the four D3 rows go from `drop` to `route` (bands) or `route` with a
  block swap (continuous). `appearance_plan.py` rule `D3` must change text too, because its "cannot
  vary roughness per pixel" is false; the correct statement is "four values per pixel on
  `CarPaintMM`, eight bits per pixel on `GeneralMkIII`".

---

## 6. Where JC3 has no exact carrier — closest system, gap, build action (STAGES.md)

Per `STAGES.md`: never "no system"; name the closest carrier, the gap, and the build step that closes
it.

| BmAK feature | closest JC3 system | gap | build action (BUILD stage) |
|---|---|---|---|
| per-pixel **roughness**, painted body | `CarPaintMM.s2 PropertyMap` × `m_SpecularGloss` float4 | 4 levels, not 8 bits; per-texel error = bin width (measured by T2) | bake banded `s2` + per-band vectors (§5.1); record the residual per material |
| per-pixel **roughness**, disc/seat/missile/cell | `GeneralMkIII.Gloss1Map` | block type not yet written by our RBM writer; channel inside the map UNKNOWN | serialiser + block swap + T4 channel probe (§5.2) |
| per-pixel **reflectivity / F0** | glass: `Window.SpecFresnel` (per-pixel only if `s3` selects it); metal: `GeneralMkIII.Metallic1Map` | `CarPaintMM` has **no F0 input at all**; `GeneralMkIII`'s `Reflectivity_1` is `[unused]` | for paint, reflectivity is carried as metallic banding and the F0 residual is recorded; for glass, T5b |
| per-pixel **metallic** | `m_Metallic` float4 (bands) / `GeneralMkIII.Metallic1Map` | same as roughness | as above |
| **body separation mask** (channels 1-3) | `CarPaintMM.s2` + `s3` (already bound for cockpit and wheel lights) | the body's own mask asset (`WheelArch_MicroMasks`) is not in the grab → `s2`/`s3` are dummy black on body/wheel/undercarriage/turret | new grab of the master's default texture, or author the mask from the material's own channel boundaries; then the same `s2` carries both the mask and the gloss bands? **No** — one texture, one meaning: the mask would take `s2`, so gloss bands would have to move to `s3` and tint to a decal-property slot. Recorded as the ordering conflict to resolve at BUILD time, not assumed away |
| per-vertex property multiplier | `CarPaintMM` PS input `TEXCOORD6.y` | semantics UNKNOWN | T6 probe; if it is a gloss multiplier, one vertex channel can modulate all four bands continuously |

---

## 7. Tests that could prove it

All offline tests are runnable now. Any test that needs the game is gated on
`tmp/freebuff/APPROVED_Q.txt` (STAGES.md test ban) and must use the PILOT camera cards for a fixed
frame.

### T1 — channel census (offline, catches dead-channel reads) — **passes today**
```bash
uv run --with pillow --with numpy python - <<'EOF'
import glob,os; from PIL import Image; import numpy as np
for f in sorted(glob.glob('Working/Appearance/grab/*/Texture2D/*.tga')):
    b=os.path.basename(f)
    if not any(k in b for k in ('_R.tga','_S.tga','_M.tga')): continue
    a=np.asarray(Image.open(f)); sc=65535.0 if a.dtype==np.uint16 else 255.0
    print(b, Image.open(f).size, ['%.3f/%.3f'%(a[:,:,i].mean()/sc,(a[:,:,i].astype('f4')/sc).std()) for i in range(a.shape[2])])
EOF
```
Pass: every channel the plan *reads* for a material has std > 0.01 on that material's map. Fails the
plan (not the code) if a declared source channel is dead → change the declared order, which is the
finding that already forced §4.1.

### T2 — pack round-trip and quantisation error (offline, after a bake)
1. `spec_check.py` on the built RBM: every block's `m_SpecularGloss`/`m_Metallic` == the spec's
   per-band values, and `s2` decodes to the same bin map (histogram of R/G/B/black == the band
   fractions ±1 %).
2. Error metric: per texel, `|gloss_band − (1 − roughness_texel)|`; report mean and p95 **per
   material**. Pass: p95 ≤ 0.15 gloss (the widest bin's half-width) and no material with a dead
   channel read.
3. Negative control: feed the packer a constant map → exactly one band used and the other three
   vectors equal it; a packer bug that swaps bins fails here.

### T3 — the channel order itself, one variable (offline + in-game A/B)
Offline: band the *same* map under H1 and H2; the two `s2` textures must differ (if they are
identical the map has no usable second channel and the order cannot matter for that material).
In-game (gated): two builds identical except the `s2` order, fixed camera, noon; the author's
reference is the BmAK render. Pass: one of the two orders is preferred blind **and** the material's
`gloss_band` ordering matches the authored map's visible direction (rough region → duller highlight).
Prediction band for the A/B: p95−p05 of screen luminance over the disc face ≥ 0.10.

### T4 — `GeneralMkIII` map channel (in-game, 4 runs)
Author one test part with a striped map: run 1 `Gloss1Map` = R-ramp only (G=B=0), run 2 = G-ramp,
run 3 = B-ramp, run 4 = flat. Pass: exactly one run shows the gloss gradient (highlight width follows
the ramp, monotone), the rest are flat. That names the channel; the same 4-run pattern names
`Metallic1Map`'s.

### T5a — `Window` normal slot (offline test, in-game check)
Offline: decode the built body RBM, print the Window block's texture table; the header binds
`NormalMap` at `s2`. Pass (offline): the normal string sits where the shader samples it, or the
table→sampler rule for `Window` is stated and tested. In-game: canopy normal detail visible at
grazing angle vs the current build.

### T5b — `Window.s3` property map (in-game, 2 runs)
Run A: canopy `s3` = dummy black (today). Run B: `s3` = 4-band gloss mask from `Glass_S.G`. Pass:
the specular lobe changes with the band map and alpha is unchanged. Fail: no visible difference →
`Window`'s `s3` does not select properties, and glass falls back to the material-level values in §5.3.

### T6 — `TEXCOORD6.y` per-vertex scalar (in-game, 2 runs)
Set the channel to a linear ramp across one panel (0→255) at fixed gloss. Pass: a gloss gradient
appears that no texture explains. Fail: nothing → the channel is not a property multiplier and the
four-band ceiling stands.

### T7 — no-regression gates (offline, every build)
25/25 RBMs re-encode byte-identical; `spec_check.py` 0 mismatches and 0 silently inherited template
values; texture budget ≤ 4,648 KB; model ≤ 4,424 KB; `@files.xml` registers every new `.ddsc`
(MODLOG §103a step 3). Any failure stops the build before deploy.

---

## 8. Budget and practical constraints (measured)

* Current staged build: **3,954 KB textures of 4,648 KB** (`MODLOG` §103b) → **≈694 KB free**.
* A BC1 mask costs `w·h/2` bytes: 1024² = 512 KB, 512² = 128 KB, 256² = 32 KB.
* Destination A for six materials at the sizes in §5.1 = 128 (disc) + 128 (seat) + 32 (missile) +
  32 (cell) + 128 (tyre) + 128 (wheel) = **576 KB**, inside the headroom with ~118 KB spare.
* Destination B (full-resolution `Gloss1Map` + `Metallic1Map` per swapped part, 1024² each = 512 KB
  per map) does **not** fit for four parts: 4 × 2 × 512 KB = 4 MB. Therefore B is proposed at 512²
  (128 KB/map) first, or A ships first as the cheap carrier and B follows per part as the exact one.
  **This is a derived constraint, not a measured one** — the allocator must confirm it with
  `tex_bytes()` before the bake (T7).
* The maps are linear, BC1, no sRGB flag (vanilla mpm/msk flag = 1; dif flag = 9, MODLOG §79). A mask
  written as sRGB decodes ~2.2× off in the shader.

---

## 9. Still UNKNOWN (with where it would be settled)

1. **The channel order of `Ref_n_Rough_Map` / `_S`.** §4.1 H1/H2/H3 all fit part of the census; only
   T3 separates them. The glass mask's authored string (`R=Reflect / G=Rough`) is the only written
   hint and it is a different parameter.
2. **Which channel `GeneralMkIII.Gloss1Map` / `Metallic1Map` read.** Not in the reflection header, not
   in the block parser, not in DECODE_DEPTH4. T4.
3. **`Window.s3` consumers, and the `Window` table→sampler rule.** T5a/T5b.
4. **`CarLight`'s `float4 MaterialConsts[4]` (64 B) and `General`'s `[3]` (48 B).** MODLOG §102d;
   until decoded those blocks cannot be authored from numbers.
5. **`TEXCOORD6.y` on `CarPaintMM`.** T6, or the shader body (not on disk).
6. **The body's own separation mask asset** (`WheelArch_MicroMasks`) — not in the 115-file grab, so
   body channels 1-3 are all channel 0 today. Needed before banding and tinting can coexist on the
   body (§6 last row).
7. **Whether the four `PropertyMap` channels and the four `SpecularGloss` components are the same index
   for TintMap purposes.** MODLOG §78 reads them as separate maps; if the tint index and property
   index must agree, the band map and the tint mask constrain each other and need a joint solve.

---

## 10. Reproduce

```bash
cd "E:/Modding/JC3-Batmobile"
# 1. the block interfaces (decoded headers, on disk)
grep -n "sampler\|float4 m_\|cbuffer" Tools/JCMR-src/assets/jc3/shaders/carpaintmm.fb.txt
grep -n "sampler\|SpecGloss\|SpecFresnel\|DiffuseRougness" Tools/JCMR-src/assets/jc3/shaders/window.fb.txt
grep -n "sampler\|MaterialConsts\|Gloss1Map\|Metallic1Map" Tools/JCMR-src/assets/jc3/shaders/generalmkiii.fb.txt
sed -n '/texture_names\[\]/,/};/p' Tools/JCMR-src/src/game/games/justcause3/renderblocks/renderblockgeneralmkiii.cc
# 2. the D3 rows (4, not 4+masks) and the mask binding
uv run python - <<'EOF'
import json; p=json.load(open('Working/Appearance/appearance_plan.json'))
print([c['component'] for c in p['components'] if c['rule']=='D3'])
EOF
grep -n "Metalicity_Roughness_Reflectivity\|Ref_n_Rough_Map" Research/BatmobileGrab/MATERIALS.md | head
# 3. the channel census (§4) -- the T1 command
# 4. what the build did with them
uv run python - <<'EOF'
import json; f=json.load(open('Working/Appearance/build_bud1/factors.json'))
for n,m in f['materials'].items():
    i=m['inputs'].get('static.SpecularGloss'); print(n, i and i['value'], i and str(i['source'])[:80])
EOF
```

### Evidence index

| claim | file |
|---|---|
| `CarPaintMM` samplers, 18 float4 + 7 support, `s2`/`s3` roles | `Tools/JCMR-src/assets/jc3/shaders/carpaintmm.fb.txt`; `Research/JC3Grab/COLOUR.md` §2 |
| `PropertyMap`/`TintMap` semantics are INFERRED, not decoded | `Research/JC3Grab/COLOUR.md` §6 item 3; MODLOG §78 |
| no F0/anisotropy/weather input on `CarPaintMM` | `card-T-21.md` A11 (holds) |
| D3's reasoning is self-contradictory | `card-T-21.md` A10 |
| `Window` binds its normal at `s2`, has `SpecFresnel`/`SpecGloss` scalars | `Tools/JCMR-src/assets/jc3/shaders/window.fb.txt` |
| `GeneralMkIII` 20-slot table, Gloss/Metallic at 1/2, 70-float consts | `renderblockgeneralmkiii.cc`; `generalmkiii.fb.txt`; `Research/JC3Grab/DECODE_DEPTH4.md` |
| `CarLight`/`General` params undecoded | MODLOG §102d; `Research/JC3Grab/LIGHT_SYSTEM.md` §5 |
| glass mask channel string `R=Reflect / G=Rough` | `Research/BatmobileGrab/MATERIALS.md:972`; `SLOTS.md:26` |
| current D3 implementation and the dead-R skip | `Tools/scripts/factors.py:117,262-278` |
| 4 D3 rows | `Working/Appearance/appearance_plan.json` (`.rules[id=D3]`, `.components[rule=D3]`) |
| per-material current gloss/metallic/slots | `Working/Appearance/build_bud1/factors.json` |
| texture budget 3,954/4,648 KB | MODLOG §103b |
| `GeneralMkIII` has no writer yet | `tmp/freebuff/reports/G3-04e.md` |
