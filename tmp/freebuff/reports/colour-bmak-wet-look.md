# BmAK's look: charcoal, satin, wet — the decoded parameters and the CarPaintMM members that could carry them

Lane 8014, 2026-11-06. Brief: derive how BmAK produces the operator's reference look (dark
charcoal/gunmetal, satin, wet street) from its own materials, name the parameters that set base
colour, roughness/specular and metalness with their decoded values, then list which `CarPaintMM`
members could carry each. No tuning from screenshots: every value below is a file read, and the
combine rule is labelled `UNKNOWN` because the operator graph is stripped.

Labels: **decoded** = one tag/value read at the export/offset or `.rbm` payload offset named;
**derived** = arithmetic on decoded values, shown; **UNKNOWN** = searched and absent, with the route
that would settle it.

---

## 0. Answer in one paragraph

The look is **three decoded parameter sets, not a shader preset**. Base colour is
`Material0_BaseColour` = **[0.025787, 0.025787, 0.03, 1]** (linear; ≈ sRGB **45, 45, 48** — a
near-black neutral with a 2 % blue bias), overridden on `Batmobile_V3_WheelArchs_NEW_MIC`; satin is
`Material0_Roughness` **0.4** with `Material0_Reflectivity` **0.2** and palette `clear_coat` **1.0**;
metalness is `Material2_Metalicity` **1.0** (the body's Material2 channel, a fully metallic underlay)
with the MK2 arch's `Paint_Metalicity` **0.2** over it. "Wet" is a separate four-member rain family on
the same material — `Wetness_Refl_Fresnel` **0.6**, `Wetness_Reflectivity_Multiplier` **0.6**,
`RainReflectivityMul` **1.6**, `RainRoughnessMul` **0.75** — i.e. the wet street does not change the
paint's base colour, it raises reflectivity and lowers roughness. **JC3's `CarPaintMM` has a member for
the colour (tint, `cb6[0..2]`), a member for the satin (gloss, `cb2[0]` / override `cb6[4].x`), a member
for metalness (`cb2[1]`) and a member for clearcoat (`cb2[2]`) — and no member at all for reflectivity,
the wet/rain family, the edge mask or anisotropy.** That last gap is the honest limit of this row.

---

## 1. Where the look lives: the material chain

`decoded` — `Research/BatmobileGrab/COLOUR_PARAMS.md` §1, containment oracle: body slot **2** of
`Batmobile_V2` (mesh export 5284, slot array at 8287) is export **763**, and the chain is walked by
each step's `ObjectNCRProperty` at field `0x84`:

| step | export | class | name | parent |
|---:|---:|---|---|---|
| 1 | 763 | MaterialInstanceConstant | `Batmobile_V3_Mainbody_NEW_MIC` | 767 |
| 2 | 767 | MaterialInstanceConstant | `Batmobile_V3_WheelArchs_NEW_MIC` | 359 |
| 3 | 359 | Material | `Batmobile_Worn` | — |

**Inheritance rule (decoded by the parent field, derived for the winner):** the nearest MIC that sets
a parameter wins. 763 sets `Material0_Reflectivity` 0.2 and `Material0_Roughness` 0.4; 767 sets
`Material0_Reflectivity` 0.15 and `Material0_Roughness` 0.4 and **is the only one that carries vectors**
(12 vector params), so the body's **base colour comes from 767** while its reflectivity comes from 763.

`decoded` — the MK2 body/arch material is a separate chain in `Playable_BatmobileMK2_SF`:
`Batmobile_MK2_WheelArch_MAT` (master) ← `Batmobile_MK2_WheelArchs_MIC_INST` (16 scalars, 3 textures)
and `Batmobile_MK2_Wheel_INST` (2 scalars) — `Research/BatmobileGrab/MATERIALS.md:1024-1025`,
`SKINS.md:527`, `SKINS.md:548`. **The MK2 master's own expression defaults are not decoded in the repo**
(`COLOUR_PARAMS.md` covers the `Batmobile_Worn` chain only), so §3 quotes the MK2 values that exist —
the MIC overrides — and marks the master defaults `UNKNOWN`.

---

## 2. Base colour

`decoded` — `Batmobile_V3_WheelArchs_NEW_MIC` (#767), `VectorParameterValues` field `0x168`, item byte
262, tag @0x8, guid `f36abc2b` (`COLOUR_PARAMS.md` §2 row 38; `COLOUR_FUNCTIONS.md` §3):

| parameter | value | owner | note |
|---|---|---|---|
| `Material0_BaseColour` | **[0.025787, 0.025787, 0.03, 1]** | 767 | linear; the body's base |
| `Material1_Basecolour` | [0.01, 0.01, 0.01, 1] | 767 | near-black, second channel |
| `Material2_BaseColour` | [0.215462, 0.176446, 0.10714, 1] | 767 | dim warm metal |
| `Material3_BaseColour` | [0, 0, 0, 1] | 767 | black |
| `Diffuse_Adjust` | **[2.2, 2.0, 2.0, 1]** | 767 | per-channel gain on the diffuse |
| `EdgeMask_Colour` | [0.1, 0.1, 0.1, 1] | 359 (expr 710) | edge wear tint |
| `Damage_Colour` | [0.302125, 0.230998, 0.163641, 0.098039] | 359 (expr 701) | damage |
| `Damage_Dirt_Colour` | [0.41573, 0.389493, 0.33165, 1] | 359/767 | dirt |
| `Mud_Colour` | [0.263175, 0.14198, 0.067725, 1] | 359 (expr 713) | mud |

`derived` — sRGB of the linear base colour, using the standard 2.4-piece transfer:
0.025787 → **0.1749** (45/255); 0.03 → **0.1898** (48/255). So the authored colour is
**RGB ≈ (45, 45, 48)** — charcoal, not grey and not black, with the blue channel 3 LSB higher. That is
the "gunmetal" half of the reference, and it is a *very* dark neutral, not a blue.

`derived` — the shipped build's effective albedo, as `T2_TRANSLATION.md` T-MA3 records it: base
× `Diffuse_Adjust` = **[0.056738, 0.05158, 0.06]** linear, written to albedo bytes
`0x83/0x7d/0x86` (131, 125, 134) through the project's linear→sRGB gain 3.4476. That is the number the
JC3 side currently ships; this report does not change it.

`UNKNOWN` — **what the authored base colour is before the MIC override.** `Batmobile_Worn`'s own
`Material0_BaseColour` expression (716) carries **no `DefaultValue` tag** (`COLOUR_PARAMS.md` §6
item 2; `VEC_DEFAULTS.md` confirms 0/87 master vector defaults). The only colour in bytes is 767's
[0.025787, 0.025787, 0.03, 1]. And **how `Material0_BaseColour`, `Diffuse_Adjust` and the channel
texture combine is `UNKNOWN`**: all 944 `FunctionExpressions` slots of the 11 Batmobile material
functions are zero (`COLOUR_PARAMS.md` §5, oracle `operator_graph_is_stripped`), so the multiply chain
is not in the package. The `base × adjust` line above is the project's derived reading, not a decoded
operator.

---

## 3. Roughness and specular (the "satin")

`decoded` — scalars on the `Batmobile_Worn` chain; master defaults from `COLOUR_PARAMS.md` §3
(`FloatProperty @0xcc`), MIC overrides from §2:

| parameter | `Batmobile_Worn` default | body MIC (763 / 767) | what it sets |
|---|---|---|---|
| `Material0_Roughness` | 0.25 (expr 506) | **0.4** (763), 0.4 (767) | the paint's roughness |
| `Material0_Reflectivity` | 0.25 (expr 515) | **0.2** (763), 0.15 (767) | its specular level |
| `Material1_Roughness` | 0.25 (510) | 0.25 (763/767) | channel 1 |
| `Material1_Reflectivity` | 0.25 (516) | 0.2 | channel 1 |
| `Material2_Roughness` | 0.25 (507) | **0.15** (767) | channel 2 (metal) |
| `Material2_Reflectivity` | 0.25 (517) | **0.9** (763) | channel 2 |
| `Material3_Roughness` | 0.25 (512) | **0.02** (767) | channel 3 (glass-clear) |
| `Material3_Reflectivity` | 0.25 (518) | 0.5 (763), 0.5 (767) | channel 3 |
| `EdgeMask_Roughness` | **0.03** (expr 522) | — | worn edges: near-mirror |
| `EdgeMask_Metalicity` | **2** (expr 508) | 2 (767) | worn edges: over-metal |
| `Grubbiness` | **0.75** (expr 521) | — | the dirt/grime bias |

`decoded` — MK2 arch (`SKINS.md:548`, `MATERIALS.md:1025`), the second material the brief names:

| parameter | value | what it sets |
|---|---|---|
| `Paint_Roughness` | **0.1** | the MK2 paint is *glossier* than the Worn body |
| `Paint_Reflectivity` | **0.5** | higher specular |
| `Paint_Metalicity` | **0.2** | mostly dielectric paint |
| `Paint_Strength` | **5** | paint layer weight (0 on `Batmobile_MK2_Wheel_INST`) |
| `Roughness_Multiplier` | **0.7** | scales the roughness |
| `Reflectivity_Multiplier` | **1** | no change |
| `Metalicity_Multiplier` | **1** | no change |
| `EdgeMask_Colour` | **0.65** | worn edge brightness (vs 0.1 on Worn) |
| `Damage_dirt` | 0.3 | dirt |
| `Mud_Opacity` | 300 | mud |
| `Grubby_Multiplier` | 1 | grime |

`derived` — "satin" is the ratio that falls out: roughness **0.4** against reflectivity **0.2**, with
`Material3_Roughness` 0.02 behind it (a clear lacquer channel), `clear_coat` **1.0** from the palette
(`Research/JC3Grab/COLOUR.md` §4: every tint record ships `clear_coat` 1.000) and `EdgeMask_Roughness`
0.03 on the wear. A mirror would need roughness near 0 everywhere; a matte would need ~0.7+. 0.4 is the
mid point, and the project already clamped its JC3 gloss to **0.45** for exactly this reason
(`T2_TRANSLATION.md` T-MA4: "authored gloss 0.6, vanilla caps paint gloss at 0.4 … 0.45").

`UNKNOWN` — **what `Material0_Reflectivity` does numerically.** JC3 has no F0/reflectance input
(`Research/challenge/card-T-21.md` A11 holds: "no F0 / no anisotropy / no weather input on CarPaintMM"),
and BmAK's own reflectivity-to-F0 rule is in shader code, not in the package (`COLOUR_PARAMS.md` §6
item 6). "Reflectivity 0.2" is a number with a decoded name and an undecoded effect.

---

## 4. Metalness

`decoded` — the body is metallic in exactly one channel:

| parameter | value | owner | source |
|---|---|---|---|
| `Material2_Metalicity` | **1.0** | `Batmobile_Worn` expr 523, overridden 1.0 by 767 | `COLOUR_PARAMS.md` §3 row 36 / §2 row 21 |
| `EdgeMask_Metalicity` | **2.0** | expr 508 / 767 | §3 row 21 / §2 row 16 |
| `Paint_Metalicity` (MK2) | **0.2** | `Batmobile_MK2_WheelArchs_MIC_INST` | `SKINS.md:548` |
| `Metalicity_Multiplier` (MK2) | **1.0** | same | same |

`derived` — so the body is a **fully metallic channel 2** (the warm `Material2_BaseColour`
[0.215, 0.176, 0.107]) under a **dielectric paint layer** (`Material3_BaseColour` [0,0,0] with
`Material3_Roughness` 0.02 — the lacquer), and the *paint* channel 0 itself carries no metalness
member at all: `Material0` has roughness and reflectivity but **no `Material0_Metalicity`**. The
charcoal reads as metal because channel 2 is metal and the lacquer is clear, not because the paint is
metal. The MK2 arch, by contrast, paints metal at 0.2 — a different look on the same car.

`UNKNOWN` — which channel the per-pixel `s2` PropertyMap selects, i.e. how much of the body is channel
2 at a given pixel. `COLOUR.md` §2 names the sampler (`s2` PropertyMap = channel selectors) but the
selection arithmetic is in the stripped graph.

---

## 5. The wet half

`decoded` — the rain/wetness family on `Batmobile_Worn` and its body MIC (values from
`COLOUR_PARAMS.md` §3 defaults and §2 overrides; the same names are re-checked against the header
`BMBL_Rain_Opt`):

| parameter | value | owner | role (name only) |
|---|---|---|---|
| `Wetness_Refl_Fresnel` | **0.6** | expr 498 / 767 | wet specular Fresnel |
| `Wetness_Reflectivity_Multiplier` | **0.6** | expr 500 | wet reflectivity gain |
| `RainReflectivityMul` | **1.6** | expr 505 | rain reflectivity gain |
| `RainRoughnessMul` | **0.75** | expr 509 | rain roughness scale |
| `Rain_Size_Multiplier` | **[1, 2, 0, 1]** master / **[2.5, 2, 0, 1]** body | expr 700 / 767 | rain streak scale |
| `Batman_Rain_Direction` | **[0, 0, -1, 0]** | expr 706 / 767 | rain vector |
| `Water_Trails_Activated` | **1** | expr 503 | water trails on |
| `Rain_Constant` | no default | expr 492 | — |
| `Mud_WetStreaks` | **1** | expr 491 | wet mud streaks |

`Rain_Size_Multiplier` has two decoded values: `[1, 2, 0, 1]` in the master (expr 700,
`COLOUR_PARAMS.md` §3 row 53) and `[2.5, 2, 0, 1]` in the 767 override (§2 row 46); the MIC value is
the one the body uses.

`derived` — the wet look is **reflectivity and roughness only**: wetness raises specular (×0.6 Fresnel,
`RainReflectivityMul` 1.6) and softens roughness (`RainRoughnessMul` 0.75 × 0.4 = **0.3** effective on
the body while raining). The base colour, metalness and clearcoat are untouched by the rain members.
That is why the same car reads satin on a dry road and glossy on a wet one with no colour change.

`UNKNOWN` — whether the rain family is even evaluated in the shipped Arkham scene settings (no probe;
test ban), and what the wet-street reflection actually is (environment/probe term, not a material
parameter — `COLOUR.md` §5-6).

---

## 6. Which CarPaintMM members could carry each

`decoded` — the member list and slots are from `Research/JC3Grab/CB0_SLOTS.md` (12/12 shader headers
agree; `.rbm` `CarPaintMM` payload carries the same 316 + 76 bytes): `cb2` (`CarPaintStaticMaterialParams`,
18 float4 + 7 floats), `cb6` (`CarPaintDynamicMaterialParams`, 4 float4 + 3 floats), `cb7`
(`CarPaintDynamicObjectParams`, 1 float4 + 1 float), `cb8` (`RBIInfo`).

| BmAK parameter | value | CarPaintMM member that could carry it | verdict |
|---|---|---|---|
| `Material0_BaseColour` | [0.025787, 0.025787, 0.03, 1] | `cb6[0..2]` `m_TintColorR/G/B` (the dynamic tint), or `cb2[4]` `m_DiffuseWrap`, or `cb8[8]` `ModelDiffuseColor` | **decoded names; role UNKNOWN.** Which of the three multiplies `s0` Diffuse is in the SHEX (`CB0_SLOTS.md` §5, §8) |
| `Diffuse_Adjust` | [2.2, 2.0, 2.0, 1] | none — no gain member | **UNKNOWN**; the gain would have to be pre-multiplied into the tint |
| `Material0_Roughness` | 0.4 (body) / 0.1 (MK2 paint) | `cb2[0]` `m_SpecularGloss` (float4), override `cb6[4].x` `m_SpecularGlossOverride` | **decoded name; polarity UNKNOWN** (gloss vs roughness — inverse is the convention, not a decoded fact) |
| `Material0_Reflectivity` | 0.2 / 0.5 | none: `cb2` has `m_SpecularGloss` and `m_Metallic`, no F0/reflectivity | **UNKNOWN / not carriable** (card-T-21 A11: no F0 input holds) |
| `Material2_Metalicity` | 1.0 | `cb2[1]` `m_Metallic`, override `cb6[4].y` `m_MetallicOverride` | **decoded name**; note it is one value for the whole block, not per channel |
| `Paint_Metalicity` (MK2) | 0.2 | the same `m_Metallic` | **decoded name**; a block can carry only one metallic value |
| `clear_coat` (palette) | 1.0 | `cb2[2]` `m_ClearCoat`, override `cb6[4].z` `m_ClearCoatOverride` | **decoded name** |
| `Wetness_Refl_Fresnel` / `Wetness_Reflectivity_Multiplier` / `RainReflectivityMul` / `RainRoughnessMul` | 0.6 / 0.6 / 1.6 / 0.75 | **no member** — `cb2` has no wetness/rain field | **not carriable**; card-T-21 A11's "no weather input" holds |
| `EdgeMask_Colour` / `EdgeMask_Roughness` / `EdgeMask_Metalicity` | 0.1–0.65 / 0.03 / 2 | no member (edge mask is a BmAK function) | **not carriable** |
| `Material3_Anisotropic_broad/thin_Colour` + `Anisotropic Ramp` | [0.462,0.734,0.972] / [0.196,0.2,0.33] | no member | **not carriable** (A11: no anisotropy input) |
| `Damage_Colour` / `Damage_Chapter` / `Damage_dirt` / `Mud_Colour` / `Mud_Opacity` / `Grubbiness` | see §2 | `cb2[5]` `m_DirtParams`, `cb2[6]` `m_DirtBlend`, `cb2[7]` `m_DirtColor`; `cb2[15]` `m_Damage`, `cb2[16]` `m_DamageBlend`, `cb2[17]` `m_DamageColor`; samplers `s4`/`s5`/`s6` | **decoded names**; which channel is dirt vs mud vs damage is the same stripped-graph `UNKNOWN` |
| the base colour per material channel (0..3) | 4 colours | `cb2` has **no** per-channel colour set; the block has one diffuse/tint | **not carriable**; JC3 varies channels by the `s2` PropertyMap, not by four colour members |

`decoded` — what the shipped JC3 paint blocks already hold, for comparison: `static_params[0]`
(`m_SpecularGloss`) is **one distinct value `(0.0, 0.4, 0.3737, 1.0)`** on all 394 blocks
(`Research/JC3Grab/TINT.md` line 44 — the 0.4 is the fleet gloss cap), and the donor's paint blocks
carry dynamic tint **(0.14, 0.19, 0.25, 1)** with overrides **0.4 / 1 / 1**
(`Research/JC3Grab/COLOUR.md` §1; `TINT.md` lines 42-43 — role of the components `UNKNOWN`). So the
tournament car's paint, as shipped, is a mid blue-grey (sRGB ≈ 0.14/0.19/0.25 linear → 104, 119, 134)
with gloss 0.4 — **not** the Batmobile's charcoal.

`derived` — the only way to reach the reference look with these members is: `m_TintColorR/G/B` =
the near-black base colour (or the `base × adjust` product, since there is no gain member),
`m_SpecularGloss` ≈ 1 − 0.4 = **0.6** (satin) or the project's clamped **0.45**, `m_Metallic` = **1.0**,
`m_ClearCoat` = **1.0**. The wet street cannot be carried at all: it is not in `CarPaintMM`.

`UNKNOWN`, and it is the one that matters: **whether the engine writes the palette tints into
`cb6[0..2]` verbatim.** `TINT.md` §42 and `CB0_SLOTS.md` §8 both record that no asset names the palette;
the fill at `0x140289a80` copies float4 0..2 but not from the palette record. A live constant-buffer
dump would settle it (test ban).

---

## 7. What this means, stated without tuning

* **Charcoal:** decoded as linear [0.025787, 0.025787, 0.03], which the project ships as albedo
  `0x83/0x7d/0x86` after `Diffuse_Adjust` [2.2, 2, 2]. The dark value is authored, not a lighting result.
* **Satin:** decoded as roughness 0.4 / reflectivity 0.2 over a clear coat 1.0 with a channel-3
  roughness of 0.02; the MK2 arch is glossier (0.1) and less metallic (0.2) than the Worn body.
* **Metal:** decoded as channel-2 metalicity 1.0, not as a metal paint.
* **Wet:** decoded as a separate reflectivity/roughness multiplier family; no `CarPaintMM` member
  exists for it, so a JC3 build cannot copy the wet response from this material — it can only copy
  the *resulting* gloss/reflectivity look.
* **Nothing here is a directive.** Whether the reference is reproduced is a play test (test ban);
  the numbers above are what BmAK authored.

---

## 8. UNKNOWNs, consolidated

1. **The combine rule** (`base`, `Diffuse_Adjust`, channel textures → final albedo): 0 of 944
   `FunctionExpressions` slots non-zero (`COLOUR_PARAMS.md` §5).
2. **The authored default of `Material0_BaseColour`**: expression 716 has no `DefaultValue`; only the
   MIC value exists in bytes (§6 item 2).
3. **`Material0_Reflectivity`'s meaning**: no F0 member on the JC3 side and no operator on the BmAK
   side; the number is decoded, the effect is not.
4. **The MK2 master's own expression defaults**: the repo decodes the MK2 *instances*
   (`MATERIALS.md:1024-1025`, `SKINS.md:548`), not `Batmobile_MK2_WheelArch_MAT`'s parameter defaults.
   *Would settle:* `grab_colour_params.py` on `Playable_BatmobileMK2_SF.upk`.
5. **Which `CarPaintMM` colour member is albedo** (`m_DiffuseWrap` vs `ModelDiffuseColor` vs the tint):
   SHEX arithmetic, not on disk (`CB0_SLOTS.md` §8).
6. **Whether the palette reaches `cb6[0..2]` verbatim**: no asset names the palette; uploader traced to
   the block, not to the record (`TINT.md` §42, `CB0_SLOTS.md` §8).
7. **Gloss polarity and cap**: 0.4 is the fleet's single authored value and the project clamps to 0.45;
   whether the shader reads that float as gloss or roughness is a shader-code fact, not a file fact.
8. **The wet-street reflection itself**: environment/probe/tonemap, `COLOUR.md` §5-6.

---

## 9. Checks and revert

* All values quoted are one tag read each, at the source named: `COLOUR_PARAMS.md` §2/§3 (exports 763,
  767, 359), `COLOUR_FUNCTIONS.md` §3, `SKINS.md:548`, `MATERIALS.md:1024-1025`, `CB0_SLOTS.md` §3-§5,
  `TINT.md` lines 42-44, `COLOUR.md` §1/§4. No screenshot was read and no value was fitted to one.
* The sRGB conversions in §2 are arithmetic on the decoded linear values, printed with the transfer
  used.
* **Not run:** no `--check` of `grab_colour_params.py` / `jc3_cb0_slots.py` (this report edits neither
  their inputs nor their outputs); no game probe (test ban).
* **Revert:** delete `tmp/freebuff/reports/colour-bmak-wet-look.md`. Nothing else changed.
