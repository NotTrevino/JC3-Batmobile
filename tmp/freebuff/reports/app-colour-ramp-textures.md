# The BmAK colour ramps, extracted — pixels, sampled values, and where the near-black body colour comes from

2026-11-06. Static read only: the game was not run, nothing was injected, no package was written.

Extraction uses the existing tool `Tools/scripts/bmak_ramp_hunt.py` (`mip0`: export payload → mip-0
record → `Chunk*.tfc` → `upk_read._dechunk` → PF_DXT1 decode). A record was accepted only if
`sizeOnDisk` equals the DXT1 byte size for its dimensions **and** the cache bytes at `tfcOffset` begin
with the UE3 package tag `c1 83 2a 9e`.

Labels: **decoded** = read from a package offset or a pixel; **derived** = arithmetic or a format rule,
shown; **UNKNOWN** = searched and absent, with the route that would settle it.

---

## 0. The answer in one paragraph

All six ramps decode, and they tell one story: **each is a colour ramp only in its first half, then
flattens into a near-black plateau that occupies the rest of its rows.** The body's ramp
(`Batman_BM3_V2_Lacquered_Underlayer_Ramp`) runs white → blue-grey → dark brown → and then holds
**`[49, 48, 49]` sRGB = 0.0307 linear** for rows 256–511. That is within 4/255 of the body's authored
`Material0_BaseColour` **[0.025787, 0.025787, 0.03] = sRGB (45,45,48)**. The emissive/body-colour ramp
goes further: its plateau is **`[32, 33, 32]` = 0.0145 linear**, nearly an order of magnitude darker
than mid-grey. So the near-black paint is **authored twice over** — as the material constant and as the
ramp plateau — and the build ships neither: it writes one scalar `[0.4784, 0.4588, 0.4941]`, which is
**6.3× the body ramp's plateau** and **13× the body-colour ramp's plateau** in linear light.

---

## 1. What was extracted

All from `BmGame.upk` (84,813 names / 177,031 exports) except the seat ramp:

| texture | package | export | class | size | mip 0 | tfc | offset | stored |
|---|---|---:|---|---:|---|---|---:|---:|
| `Batman_BM3_V2_Lacquered_Underlayer_Ramp` | `BmGame` | **#176227** | `Texture2D` | 1,894 B | 64×512 DXT1 | `Chunk1` | 363,525,127 | 498 B |
| `Batman_BM3_V2_Leather_Ramp` | `Playable_Batmobile_SF` | **#5399** | `Texture2D` | 1,894 B | 64×512 DXT1 | `Chunk1` | 361,837,038 | 683 B |
| `Batmobile_V3_Body_ColourRamp` | `BmGame` | **#176233** | `Texture2D` | 1,922 B | 64×512 DXT1 | `Chunk1` | 236,029,175 | 567 B |
| `Batmobile_V3_Tyre_ColourRamp` | `BmGame` | **#176234** | `Texture2D` | 1,922 B | 64×512 DXT1 | `Chunk1` | 236,893,670 | 664 B |
| `Aniso_ramp_Lacquered` | `BmGame` | **#176254** | `Texture2D` | 11,414 B | 512×512 DXT1 | `Chunk1` | 236,915,953 | 78,715 B |
| `Aniso_ramp_D2` | `BmGame` | **#176251** | `Texture2D` | 11,386 B | 256×256 DXT1 | `Chunk1` | 47,219,880 | 9,874 B |

`decoded` — **cross-check:** the Lacquered ramp decoded from the package matches the umodel grab
`Working/Appearance/grab/Startup/Texture2D/Batman_BM3_V2_Lacquered_Underlayer_Ramp.tga` with a
**maximum absolute channel difference of 1** over all 64×512 px. Two independent readers agree, so the
pixels below are not one decoder's artefact.

PNGs: `Working/Ramp/*.png`. Machine-readable: `Working/Ramp/bmgame_ramps.json`,
`Working/Ramp/lacquered.json`, `Working/Ramp/ramps.json`.

---

## 2. `Batman_BM3_V2_Lacquered_Underlayer_Ramp` — the body ramp

`decoded` — **129 unique rows** of 512; `x` mean variation **0.0216**, `y` mean variation **0.4659**.
It varies along **V only**: a 1-D lookup table, 64 px wide (padding / filter margin), which is what a
colour ramp should look like.

Sampled values, mean over the 64-wide row, sRGB bytes:

| row | V = row/512 | sRGB | linear | reading |
|---:|---:|---|---|---|
| 0 | 0.000 | **255, 255, 255** | 1.000 | white head |
| 32 | 0.063 | 164, 190, 222 | 0.373, 0.523, 0.735 | pale blue |
| 64 | 0.125 | 131, 144, 183 | 0.226, 0.277, 0.473 | blue-grey |
| 96 | 0.188 | 115, 110, 120 | 0.169, 0.153, 0.185 | neutral grey |
| 128 | 0.250 | 106, 75, 52 | 0.143, 0.070, 0.034 | dark brown |
| 160 | 0.313 | 90, 56, 32 | 0.099, 0.039, 0.014 | brown |
| 192 | 0.375 | 70, 52, 32 | 0.058, 0.034, 0.014 | dark brown |
| 224 | 0.438 | 56, 48, 42 | 0.036, 0.027, 0.021 | near-black warm |
| **256** | **0.500** | **49, 48, 49** | **0.0307, 0.0294, 0.0307** | **plateau starts** |
| 320–448 | 0.63–0.88 | 49, 48, 49 | 0.0307 | unchanged |
| 511 | 0.998 | 49, 48, 49 | 0.0307 | plateau to the last row |

**The plateau is the finding.** Rows 256–511 — 56 % of the ramp — are one colour. There is no second
bright stop and no saturation arc past the midpoint: a lookup anywhere in the upper half returns
charcoal.

---

## 3. The other ramps

### 3.1 `Batmobile_V3_Body_ColourRamp` — the emissive/body-colour ramp

`decoded` — 64×512, **151 unique rows**, `x` var 0.0372, `y` var 0.5532. It is the only ramp with a
real hue excursion, and it also ends flat:

| row | V | sRGB | linear | reading |
|---:|---:|---|---|---|
| 0 | 0.000 | 255, 255, 255 | 1.000 | white head |
| 64 | 0.125 | **62, 90, 148** | 0.048, 0.102, 0.297 | strong blue |
| 128 | 0.250 | 34, 56, 115 | 0.016, 0.039, 0.171 | deep blue |
| 192 | 0.375 | 65, 48, 82 | 0.052, 0.030, 0.087 | violet |
| 256 | 0.500 | 46, 39, 52 | 0.027, 0.020, 0.034 | dark violet |
| 320 | 0.625 | 32, 32, 36 | **0.0145, 0.0145, 0.0177** | near-black |
| 384 | 0.750 | 32, 33, 32 | 0.0145 | plateau |
| 448–511 | 0.88–1.0 | 32, 33, 32 | 0.0145 | plateau |

### 3.2 `Batmobile_V3_Tyre_ColourRamp`

`decoded` — 64×512, 161 unique rows. Same shape: white → blue → cool grey → floor.

| row | 0 | 64 | 128 | 192 | 256 | 320 | 384 | 448 | 511 |
|---|---|---|---|---|---|---|---|---|---|
| sRGB | 255,255,255 | 74,105,151 | 65,71,95 | 52,48,57 | 41,39,43 | 32,32,32 | 24,28,27 | 27,27,27 | 27,27,27 |

Its floor `[27,27,27]` = **0.0125 linear** — the darkest of the three colour ramps. This is the ramp
`colour_ramp_intensity` (0.5 default / 0.1 shipped) actually scales.

### 3.3 `Batman_BM3_V2_Leather_Ramp` — the seat ramp, for contrast

`decoded` — 64×512, **183 unique rows**, `x` var 0.0368, `y` var 0.9496. **Fully desaturated**
(R = G = B within 1 LSB on every sampled row):

| row | 0 | 64 | 128 | 192 | 256 | 320 | 384 | 448 | 480 | 511 |
|---|---|---|---|---|---|---|---|---|---|---|
| sRGB | 255 | 238 | 204 | 179 | 114 | 57 | 30 | 27 | 26 | **239** |

`derived` — a pure **luminance** ramp with no hue, plus a light end-cap (239) after a dark floor (26).
It cannot be the source of a body colour; its role is brightness variation on the seat.

### 3.4 The anisotropy LUTs (D5's family)

`decoded` — `Aniso_ramp_Lacquered` is **512×512**, 303 unique rows, `x` var 1.20 / `y` var 7.98, and is
**green-dominant with B ≡ 0** (R 24–47, G 103–124). `Aniso_ramp_D2` is **256×256** with only **3 unique
rows** (≈ `41,141,0`) — effectively a constant pair of lobes. These are 2-D LUTs (both axes vary), not
colour ramps; they carry the highlight lobe, not a tint.

---

## 4. How the body material turns a paint index into a colour

`decoded` — the slot. `Colour_Ramp_Map` is a `MaterialExpressionTextureSampleParameter2D`, guid
**`e9632f4f72e61c418ef58d123890d111`**, one guid shared by the master and every instance. Its
`Coordinates` input is a nested `StructProperty` whose expression index is **0** — sampled on the
**default UV set**, not a custom coordinate expression.
(Sources: `tmp/freebuff/reports/colour-ramp-in-material-members.md` §1, `COLOUR_PARAMS.md`, `SLOTS.md`.)

`decoded` — who binds what on the body chain:

| material | level | bound ramp |
|---|---|---|
| `Batmobile_V3_WheelArchs_NEW_MIC` (#767, body slot 3) | MIC override | `Engine.Batman_BM3_V2_Lacquered_Underlayer_Ramp` (#-588) |
| `Batmobile_Worn` (body master, export 359) | master default | `Engine.Batmobile_V3_Tyre_ColourRamp` |
| `Batmobile_V3_Cockpit_MIC` (#10), `Batmobile_V3_Discbreak` (#13) | MIC / master | `Batman_BM3_V2_Lacquered_Underlayer_Ramp` |
| `BatmobileV3_Cockpit_Seat` (#11) | MIC | `Maps.Batman_BM3_V2_Leather_Ramp` |
| `Batmobile_V3_Emissive` (#5) | MIC | `Engine.Batmobile_V3_Body_ColourRamp` |

`decoded` — **the scale**: there is **no** `colour_ramp_intensity` on the body chain. That scalar exists
only on `Batmobile_V3_Tyre_V2_MAT` (default **0.5**, overridden to **0.1** in
`Batmobile_V3_Tyre_test_INST`). The body's ramp is applied at full strength with no gain knob.

`UNKNOWN` — **the index → V mapping.** Nothing in the cooked data says what the paint index is or how it
becomes V. The sampled `Coordinates` struct is expression `0` (default UVs) and the operator graph that
would combine index and ramp is stripped: **944 `FunctionExpressions` slots, 0 non-zero**; the
shader/uniform dumps have **0 matches for `ramp`**, and `CarPaintMM`'s constant buffer has no ramp
member. Because the default UV is used, V is per-pixel from the mesh's UV layout, not a global index —
consistent with the plateau, not proof of it.

`UNKNOWN` — **the combine rule** (multiply / lerp / tint-by). Same stripped graph. What *is* settled is
the colour set: the ramp can only return the values in §2–§3, and its upper half is one charcoal.

---

## 5. Why the body colour is near-black — two authored sources, and the build's error

`decoded` — the material's own colour, `Batmobile_V3_WheelArchs_NEW_MIC` (#767),
`VectorParameterValues` field `0x168`, item byte 262, guid `f36abc2b` (`COLOUR_PARAMS.md` §2 row 38):

| parameter | value (linear) | sRGB |
|---|---|---|
| `Material0_BaseColour` | **[0.025787, 0.025787, 0.03, 1]** | **(45, 45, 48)** |
| `Material1_Basecolour` | [0.01, 0.01, 0.01, 1] | (26, 26, 26) |
| `Material2_BaseColour` | [0.215462, 0.176446, 0.10714, 1] | dim warm metal |
| `Material3_BaseColour` | [0, 0, 0, 1] | black |
| `Diffuse_Adjust` | [2.2, 2.0, 2.0, 1] | gain on the diffuse |

`derived` — the three authored statements of the same near-black agree far better than the build does:

| | sRGB | linear |
|---|---|---|
| `Material0_BaseColour` | (45, 45, 48) | 0.0258 / 0.0258 / 0.0300 |
| **Lacquered ramp plateau** (rows 256–511) | **(49, 48, 49)** | **0.0307 / 0.0294 / 0.0307** |
| **Body_ColourRamp plateau** (rows 320–511) | **(32, 33, 32)** | **0.0145** |
| Tyre ramp floor | (27, 27, 27) | 0.0125 |

`decoded` — what the build ships: the body block's `s0` is
`{"solid": [0.4784, 0.4588, 0.4941, 1.0]}`, generated from `Material0_BaseColour` with a **×3.4476**
gain (`Working/Appearance/build_parts/factors.json`; `keep-audit-materials-textures.md` §3–§4).

`derived` — the size of the error:

| step | linear | sRGB byte |
|---|---|---|
| BmAK authored base | 0.0258 / 0.0258 / 0.0300 | 0x30 / 0x30 / 0x33 |
| × `Diffuse_Adjust` [2.2, 2, 2] | 0.0567 / 0.0516 / 0.0600 | 0x43 / 0x41 / 0x45 |
| **shipped** (× 3.4476 on top) | **0.1946 / 0.1779 / 0.2086** | **0x7A / 0x75 / 0x7E** |
| body ramp plateau | 0.0307 | 0x31 / 0x30 / 0x31 |
| body-colour ramp plateau | 0.0145 | 0x20 / 0x21 / 0x20 |

The shipped value is **≈6.3× the body ramp's plateau** and **≈13× the body-colour ramp's plateau** in
linear light — a mid grey-violet where the car should be charcoal. **The near-black is not missing from
the data; it is in the plateau and in `Material0_BaseColour`, and the build over-brightens it.**

---

## 6. JC3's closest system, and the gap

`decoded` — JC3's carrier for per-vehicle body colour is the `CarPaintMM` constant buffer
`SCarPaintDynamicMaterialParams`, 76 B, `m_TintColorR/G/B` at **0/16/32**, written from block object
`+0x168 → +0x178 → +0x188` by `0x140289a80`, whose only caller is the block constructor
`0x1402dd36f` (`Research/JC3Grab/TINT_WRITE.md`; `tmp/freebuff/reports/COLOUR-tint.md`).

| question | BmAK | JC3 closest | gap |
|---|---|---|---|
| per-vehicle body colour | `Material0_BaseColour` + ramp plateau | `m_TintColorR/G/B` (3 floats) | **none for one colour** — a tint carries the plateau exactly |
| colour as a function of index | `Colour_Ramp_Map` sampler, default UVs | 3 scalars + 3 overrides, no sampler | **a ramp cannot be carried**; only one sampled value per vehicle |
| per-pixel ramp variation | ramp lookup per pixel | flatten to one constant | no per-pixel tint lookup in `CarPaintMM` |
| ramp strength | none on the body (tyre only 0.5 / 0.1) | the tint is the knob | n/a |
| gloss / metal / clearcoat | `Material0_Roughness` 0.4, `Material0_Reflectivity` 0.2, `Material2_Metalicity` 1.0 | `m_SpecularGlossOverride` @64, `m_MetallicOverride` @68, `m_ClearCoatOverride` @72 | **reflectivity has no member** |
| anisotropy ramp | `Aniso_ramp_Lacquered` (`BmGame` #176254, 512²) | none | already accepted as D5's UV-space fake |

**Build action implied by the pixels:** the ramp is flat where the body uses it, so no sampler is
needed. Write the **plateau** — `sRGB(0.0307, 0.0294, 0.0307)` = **0x31 / 0x30 / 0x31**, or BmAK's own
`0x43/0x41/0x45` if `Diffuse_Adjust` is applied — and **drop the ×3.4476 gain**. Either is faithful; the
current `0x7A/0x75/0x7E` is not.

---

## 7. Checks run

| # | check | result |
|---|---|---|
| 1 | mip-0 oracle per texture (`sizeOnDisk` == DXT1 size, cache tag at `tfcOffset`) | passed for all 6 |
| 2 | decoded Lacquered pixels vs the umodel grab TGA | **max abs channel diff = 1** |
| 3 | ramp axis | `y` var 0.4659 / 0.5532 / 0.5775 / 0.9496 vs `x` var 0.02–0.04 → 1-D along V for the four colour ramps |
| 4 | plateau length | Lacquered rows 256–511 and Body_ColourRamp rows 320–511 identical (checked per row) |
| 5 | plateau vs authored base colour | (49,48,49) vs (45,45,48) sRGB, Δ 3–4/255 |
| 6 | `colour_ramp_intensity` on the body chain | absent (tyre master 0.5 / test INST 0.1 only) |
| 7 | ramp uniform in the shader dumps | 0 matches; 944 `FunctionExpressions` slots, 0 non-zero |

## 8. Limits

- **The index → V mapping is UNKNOWN** — `Coordinates` expression is 0 and the operator graph is
  stripped, so "which paint index lands on the plateau" is not answerable from files.
- **No runtime colour was measured.** The linear figures are the textures' own sRGB bytes converted with
  the standard 2.4-piece transfer; what the engine finally displays is untested.
- **The anisotropy LUTs were sampled by row mean only.** Being 2-D they are not characterised beyond
  their dominant axis and channel; that is D5's subject, not this one.
- The seat ramp was decoded from `Playable_Batmobile_SF` #5399; the other 14 packages carry the same
  1,894 B payload (`app-colour-ramp-locate.md` §2) but were not each re-decoded.
