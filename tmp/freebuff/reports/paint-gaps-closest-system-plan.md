# Paint gaps as closest systems: reflectivity, wet, edge wear and anisotropy

Lane 8014, 2026-11-06. The colour report (`colour-bmak-wet-look.md`) decoded the look but left four
things at **"not carriable"**: `Reflectivity` 0.2 / 0.15 / 0.9 / 0.5, the wet family
`0.6 / 0.6 / 1.6 / 0.75`, the edge mask (`0.1–0.65 / 0.03 / 2.0`) and the anisotropic ramps
(`[0.462, 0.734, 0.972]` / `[0.196, 0.2, 0.33]`). This report replaces each verdict with the nearest
JC3 mechanism and a build recipe: where the BmAK number goes, what is baked, and what is measured
on the built texture to prove it.

Labels: **decoded** = a tag/value read at the named export, offset or shader slot; **derived** =
arithmetic on decoded values; **ASSUMED** = a constant this project has never decoded (the
`F0_d = 0.04` convention) and the recipe is written so it scales; **UNKNOWN** = searched and absent,
with what would settle it. No game was launched; no texture, `.rbm`, ledger or build was written.

## 0. Change statement (AGENTS.md)

| item | value |
|---|---|
| intended change | add one report: closest-system recipe for the four "not carriable" BmAK look parameters |
| file | `tmp/freebuff/reports/paint-gaps-closest-system-plan.md` (this file) |
| why this file | the brief names it; it is a report, so it changes nothing the game reads |
| reverted by | deleting this file. No other file was written: no bake, no `.rbm` re-encode, no palette edit, no build, no install |

## 1. The ruling on the four gaps

| gap | previous label | closest JC3 system (decoded) | exactness |
|---|---|---|---|
| `Reflectivity` 0.2 / 0.15 / 0.9 / 0.5 | "no F0 member on `CarPaintMM`" | metallic albedo: in the metal branch **F0 = albedo**, so a per-texel albedo bake sets any F0 ≤ 1; plus `m_ClearCoat` as a second lobe for `R > 1` | **exact** where the channel's albedo may change (channels 2 and 3); **closest** on channels 0/1 where the diffuse must stay charcoal |
| wet family `0.6 / 0.6 / 1.6 / 0.75` | "no wetness input on `CarPaintMM`" | scene `TEST_WETNESS_FACTOR` (offset 104) + a **permanent wet bake** of the resulting roughness/reflectivity into the block and `s1` | **look-exact for a fixed wet state**; not switchable at runtime |
| edge mask `0.1 / 0.03 / 2.0` | "edge mask is a BmAK function" | **extra material slot**: a duplicated edge shell with its own `CarPaintMM` block (gloss 0.97, metallic 1, coat 1, albedo 0.1) — or `s2` channel 3 on the same block if the slot budget forbids it | **exact** per value; the mask is authored from curvature |
| anisotropic ramps | "no anisotropy input" | baked tangent-space comb in `s1` + a two-slot gloss split (aligned 0.75 / across 0.45); true anisotropic BRDF is absent | **closest**: the highlight elongates, the BRDF is still isotropic |

The four cannot share one `s2` texture: it has exactly four channels and the four BmAK material
channels already occupy them (`PropertyMap` RGB = channels 1–3, black = 0; `factors.py:20-22`). That
is why two of the four recipes move to a second **material slot**, which is JC3's real "extra
material layer" on this block.

## 2. Where a number lands: the write path

`decoded` — the block chain: `factors.py` writes one JSON spec per material; `bat_assemble.py:831`
packs the 72 floats as `static_params` in `FX.STATIC` order; `rbm_geom.py` frames `CarPaintMM` and
`spec_check.py` reads it back against `assembly.json`. The shader-side offsets are from
`carpaintmm.fb.txt` (`cb2`), not from the payload.

| BmAK quantity | JC3 destination | offset / index |
|---|---|---|
| gloss (= 1 − roughness) | `m_SpecularGloss` float4, one per material channel | `cb2[0]` @ 0; `static_params[0..3]` |
| metalness / F0 | `m_Metallic` float4 | `cb2[1]` @ 16; `static_params[4..7]` |
| clear coat | `m_ClearCoat` float4 | `cb2[2]` @ 32; `static_params[8..11]` |
| per-pixel channel choice | `s2` `PropertyMap`, BC1 **linear** (no sRGB flag) | texture slot 2 |
| per-pixel tint amount | `s3` `TintMap` (stays dummy black on the body) | texture slot 3 |
| albedo / baked colour | `s0` `DiffuseMap`, sRGB | texture slot 0 |
| normal / comb / water streaks | `s1` `NormalMap`, BC5 | texture slot 1 |
| scene wetness | `TEST_WETNESS_FACTOR` (not writable by a material) | `deferred_clusteredlightingtunable` @ 104 |
| extra layer | one more material slot → one more `CarPaintMM` block | block table |

`decoded` — what the current build (`Working/Appearance/build_bud1/factors.json`, 19 materials)
actually holds on the body and arches:

| input | value | source |
|---|---|---|
| `static.SpecularGloss` | `[0.4, 0.4, 0.4, 0.4]` | `Material0_Roughness` 0.4, capped |
| `static.Metallic` | `[0.0, 0.0, 1.0, 0.0]` | channel 2 metal 1.0 |
| `static.ClearCoat` | `[0.0, 0.0, 0.0, 0.0]` | no lacquer flag |
| `s0` | solid `[0.4784, 0.4588, 0.4941]` | base × 3.45 gain (the "white-violet" error) |
| `s2`, `s3` | `a00_dummy_black_mpm.ddsc` | mask missing on disk |
| `s1` | `Batmobile_V3_Body_N.tga` | BmAK body normal |

`decoded` — texture budget: 28 `.ddsc` = **3,953.6 KB** of the 4,648 KB cap (`MODLOG` §103b) →
**694.4 KB free**. The recipe below adds 640 KB and leaves 54.4 KB.

## 3. Reflectivity: make F0 from the albedo

`decoded` — BmAK's values, per material channel, with the channel's roughness and metalness:
`Material0_Reflectivity` **0.2** at roughness 0.4, `Material1_Reflectivity` **0.2** at 0.25,
`Material2_Reflectivity` **0.9** at 0.15 with `Material2_Metalicity` **1.0**,
`Material3_Reflectivity` **0.5** at 0.02, MK2 `Paint_Reflectivity` **0.5** with
`Paint_Metalicity` 0.2, `EdgeMask_Metalicity` **2.0** (COLOUR_PARAMS.md §2–§3; SKINS.md:548).

`ASSUMED` — the project's bridge `F0_bmak = 0.04 × R` (`app-reflectance-f0.md` §3); `F0_d = 0.04` is
not decoded, so every error below scales with it. In the metal branch JC3 computes
`F0 = 0.04(1−m) + albedo·m`; at `m = 1` this is exactly `albedo`.

| channel | R | rough | target F0 | JC3 setting | F0 achieved | error | diffuse cost |
|---|---:|---:|---:|---|---:|---:|---|
| 0 paint | 0.20 | 0.40 | 0.0080 | `m=0`, albedo 0.0258 | 0.0400 | **+0.0320** (5.0×) | none |
| 1 lacquer | 0.20 | 0.25 | 0.0080 | `m=0`, albedo 0.01 | 0.0400 | **+0.0320** (5.0×) | none |
| 2 metal | 0.90 | 0.15 | 0.0360 | `m=1`, baked albedo 0.036 (sRGB 53) | 0.0360 | **0** | none (metal has no diffuse) |
| 3 clear | 0.50 | 0.02 | 0.0200 | `m=1`, baked albedo 0.020 (sRGB 39) | 0.0200 | **0** | +0.02 on a black channel |
| MK2 paint | 0.50 | 0.10 | 0.0200 | `m=0` (0.2 would give 0.132) | 0.0400 | **+0.0200** (2.0×) | none |
| edge | — | 0.03 | — | `m=1`, albedo 0.1 (clamped from 2.0) | 0.1000 | — | shell only |
| wet, ch0 | 0.32 | 0.30 | 0.0128 | `m=0` | 0.0400 | **+0.0272** | none |

**Recipe.**
1. **`s0` bake (512², BC1, sRGB).** Body texels: base `0.025787 / 0.025787 / 0.03` linear →
   sRGB **45 / 45 / 48** (this also fixes the 3.45× gain error, but that fix is T-MA3's, not this
   plan's). Channel-2 texels (selected by `s2` G): **53 / 53 / 53** (0.036). Channel-3 texels
   (`s2` B): **39 / 39 / 39** (0.020). Edge-shell texels: **89 / 89 / 89** (0.1) and MK2 **211**
   (0.65).
2. **`s2` bake (1024², BC1 linear).** Black = channel 0, R = channel 1, G = channel 2, B = channel 3
   — the vanilla encoding (`body_mpm` R 92 %, G/B 3.8 %). The channel-2 mask is the BmAK metal
   underlay; the channel-3 mask is the lacquer/edge region. The body's BmAK separation mask is not
   in the grab (`app-per-pixel-reflectivity.md` §9.6), so these two masks are **authored** from the
   material definitions, not copied.
3. **`static.Metallic`** = `[0, 0, 1, 1]`; **`static.ClearCoat`** = `[1, 1, 1, 1]`; gloss is §3.1.
4. **`R > 1` is not a bake.** `EdgeMask_Metalicity` 2.0 clamps to 1.0 and the Joker hair's
   `Reflectivity_Multiplier` 4.0 (`F0_bmak` 0.16) cannot be reached by albedo above 1. The only
   additive lever is `m_ClearCoat` (a second lobe whose F0 is the scene constant
   `CLEARCOAT_SPECULAR_FRESNEL0`), so those two rows are carried as **clearcoat + gloss**, with the
   residual recorded as "second lobe, F0 fixed by the scene".
5. **`GeneralMkIII` is named, not used.** It declares `Reflectivity_1` and a live
   `EnableVariableDialecticSpecFresnel`, but the shipped variant marks `Reflectivity_1` `[unused]`
   (`app-reflectance-f0.md` §1.2) and our RBM writer does not yet serialize the block. It is the
   exact route only after REFL-WRITE-1.

**Proof, measured on the built material.** Read back with `spec_check.py` / `rbm_geom.decode`:
`static.Metallic == [0,0,1,1]`; `s2` channel histogram (R/G/B/black fractions) equals the authored
mask areas ±1 %; per-region mean of `s0` equals 45/53/39/89 (sRGB) ±1; the recomputed
`F0 = 0.04(1−m) + albedo·m` per region equals the table's "achieved" column to 1e-4. The two
dielectric rows deliberately fail F0 by +0.032; that residual is the ledger value, not a bake error.

### 3.1 Gloss, and the cap that must move

`derived` — gloss = `1 − roughness`: channel 0/1 **0.60**, channel 2 **0.85**, channel 3 **0.98**,
edge **0.97**, wet **0.70**. The current `factors.py:256` clamps every value to `GLOSS_CAP` (`VALUES.json`
`paint.gloss_cap` = **0.40**, and `build_bud1` writes 0.40), which would flatten the lacquer, edge
and wet bands to one value. The recipe requires the cap to be replaced by **explicit per-band
values** in the spec; the cap is a project convention, not a format limit (the donor palette itself
ships **0.45** on 8 of its 10 tints, `Working/Palette/serpente_palette.xml`;
`keep-audit-materials-textures.md` §5).

## 4. Wet: a permanent wet bake plus the scene factor

`decoded` — `Wetness_Refl_Fresnel` **0.6**, `Wetness_Reflectivity_Multiplier` **0.6**,
`RainReflectivityMul` **1.6**, `RainRoughnessMul` **0.75**; `Rain_Constant` **1** on every material
that has it (COLOUR_PARAMS.md §3; 7 occurrences, all 1). `decoded` — no `CarPaintMM` wetness member
or rain sampler exists (0 of 13 headers); the only wet strength is the scene float
`TEST_WETNESS_FACTOR` @104, whose value is UNKNOWN.

`derived` — the wet state of the body:
`roughness_wet = 0.4 × 0.75 = 0.30` → **gloss 0.70**; `R_wet = 0.2 × 1.6 = 0.32` → `F0_bmak` 0.0128.
`Wetness_Reflectivity_Multiplier` 0.6 is treated as a **layer weight**, not a second multiplier: if
it multiplied too, `R_wet` would be 0.192 and the wet F0 0.00768 would be *below* the dry 0.008,
which contradicts the decoded "wet raises reflectivity". The composition rule is UNKNOWN; this is
the one the numbers support.

| BmAK value | JC3 destination | value written | class |
|---|---|---:|---|
| `Rain_Constant` 1 | scene `TEST_WETNESS_FACTOR` | unscaled (1 = neutral) | exact by neutrality |
| `RainRoughnessMul` 0.75 | `m_SpecularGloss` ch 0/1 | **0.70** (from 0.60) | baked |
| `RainReflectivityMul` 1.6 | `m_Metallic` ch 0/1 + `m_ClearCoat` | metallic stays 0; clearcoat 1; F0 residual +0.0272 | closest |
| `Wetness_Refl_Fresnel` 0.6 | `m_ClearCoat` (fixed scene Fresnel) | 1.0 on the wet bands | closest |
| `Rain_Size_Multiplier` [2.5, 2] | `s1` normal UV scale | 5 streaks across the panel, 2:1 | baked |
| `Batman_Rain_Direction` [0,0,−1] | `s1` tangent frame | streaks along the panel's V axis | baked |

**Recipe.**
1. Set `m_SpecularGloss` ch 0/1 to **0.70**, ch 2 to `1 − 0.15×0.75 = 0.8875`, ch 3 to
   `1 − 0.02×0.75 = 0.985`; set `m_ClearCoat` 1 on all four (the palette already ships 1.0).
2. Bake the water micro-normal into **`s1`** (the existing 512² body normal, no new bytes): a
   directional streak pattern at 2:1 (V:U longer), amplitude **0.12** in tangent XY, aligned to the
   BmAK direction vector. This is the only wet term with a real per-pixel home.
3. Do **not** change `s0` for wet: BmAK's rain family leaves base colour untouched, and a colour
   change would be a different look. The wet F0 target (0.0128) is not baked because reaching it
   needs a metallic albedo of 0.0128, which would darken the charcoal 2× and destroy the diffuse.

**Proof.** Read back `static.SpecularGloss` = `[0.70, 0.70, 0.8875, 0.985]` ±0.001 and
`static.ClearCoat` = 1; `s1`'s tangent-XY power spectrum has a peak at the V axis with a 2:1
anisotropy ratio and XY standard deviation 0.06 ± 0.01; the `s0` region means are unchanged from §3
(Δ ≤ 1/255). The runtime scene factor cannot be set by a material, so the wet response in-game is
the scene's; the gated check is a fixed rainy frame vs a dry frame (test ban until
`tmp/freebuff/APPROVED_Q.txt`).

**The dry/wet conflict.** A permanent bake makes the car wet in the desert. If both states are
needed, the second state must be a **second material slot** with a dry gloss 0.60/0.85 and no streaks
— the block cannot switch at runtime. This build's reference is the wet street, so the recipe ships
the wet slot only.

## 5. Edge wear: an extra material slot, not a texture channel

`decoded` — `EdgeMask_Colour` **0.1** (Worn, expr 710) / **0.65** (MK2), `EdgeMask_Roughness`
**0.03**, `EdgeMask_Metalicity` **2.0**; the mask is a BmAK function, not a texture in the grab.

**Closest system: a geometry shell with its own block.** Select the mesh triangles whose baked
curvature exceeds the panel-edge threshold, duplicate them with a **0.5 mm** offset along the normal,
and assign them a second material slot. That slot is a separate `CarPaintMM` block, so its edge
values do not compete for `s2`'s four channels:

| BmAK value | destination | written value |
|---|---|---:|
| `EdgeMask_Colour` 0.1 (Worn) / 0.65 (MK2) | shell block `s0` (solid or 64²) | sRGB **89** / **211** |
| `EdgeMask_Roughness` 0.03 | shell `m_SpecularGloss` | **0.97** |
| `EdgeMask_Metalicity` 2.0 | shell `m_Metallic` | **1.0** (clamped) |
| edge coverage | shell triangles | **2–6 %** of body tris |
| shell offset | vertex positions | **0.0005 m** along the normal |

**Fallback if the slot/geometry budget forbids a shell:** put the mask in `s2` **channel 3**
(B = 255) and set `static.SpecularGloss[3] = 0.97`, `static.Metallic[3] = 1.0`; the edge colour
still has to be painted into `s0` because `CarPaintMM` has no per-channel colour vector. Cost: the
channel-3 slot is then unavailable for the lacquer band, so the lacquer must move to channel 1
(R) and the paint to channel 0.

**Proof.** On the built mask: coverage = 2–6 % of body texels; IoU against the curvature mask
(threshold chosen once, at the 90th percentile of vertex curvature) ≥ 0.85; on the built block:
`static.SpecularGloss[3] = 0.97`, `static.Metallic[3] = 1.0`, `static.ClearCoat[3] = 1.0`; shell
` s0` mean = 89 or 211 ±1; block count per LOD rises from 17 to 18 (`rbm_geom.decode`), and the
model stays under 4,424 KB.

## 6. Anisotropic ramps: bake the direction, split the gloss

`decoded` — `Material3_Anisotropic_broad_Colour` **[0.462, 0.734, 0.972]**,
`Material3_Anisotropic_thin_Colour` **[0.196, 0.2, 0.33]**, plus an anisotropic ramp. No
`CarPaintMM`, `GeneralMkIII`, `Window`, `CarLight` or `General` member is anisotropy; 18 static +
7 support params contain none (`factors.py` STATIC/SUPPORT; card-T-21 A11 holds).

The closest visible result is **a stretched highlight, not a true anisotropic BRDF**: a directional
micro-normal in `s1` widens the specular along the ramp, and a two-slot gloss split makes the
along/across response differ. The ramp's colour contrast sets the normal amplitude:

| BmAK quantity | value | destination | written |
|---|---:|---|---|
| broad colour | [0.462, 0.734, 0.972] | `s0` mix + slot A tint | 8 % mix into the charcoal (linear 0.060/0.083/0.106) |
| thin colour | [0.196, 0.2, 0.33] | `s0` mix + slot B tint | 8 % mix (linear 0.039/0.040/0.054) |
| broad contrast | 0.972 − 0.462 = **0.51** | `s1` tangent-XY amplitude | **0.35** |
| thin contrast | 0.33 − 0.196 = **0.134** | `s1` tangent-XY amplitude | **0.12** |
| ramp direction | authored UV axis | `s1` comb angle | 0° along U, wavelength **3 px @ 512²** |
| along-ramp gloss | 1 − 0.25 | slot A `m_SpecularGloss` | **0.75** |
| across-ramp gloss | 1 − 0.55 | slot B `m_SpecularGloss` | **0.45** |

**Recipe.**
1. Split the brushed panels by the ramp mask into **two material slots** (A along, B across); each
   gets its own `CarPaintMM` block, so the gloss split costs no `s2` channel.
2. Bake a sinusoidal comb into `s1` at 3 px period, oriented along the ramp, amplitude 0.35 (broad)
   / 0.12 (thin). At 512² this is near Nyquist; if the comb aliases, drop to 4 px and record the
   period rather than raising the texture (a 1024² BC5 normal costs +768 KB, over budget).
3. Bake the 8 % colour mix into `s0` (broad in the bright half of the ramp, thin in the dark half).
   `m_TintColor` stays the charcoal; per-pixel colour variation is only possible through `s0`,
   because the block has one tint.

**Proof.** FFT of the built `s1` green channel: the peak angle is within 5° of the ramp axis and the
period is 3 ± 1 px; tangent-XY standard deviation is 0.18 ± 0.03 (broad) / 0.06 ± 0.01 (thin);
`s2` stripe histogram (if the fallback packing is used) is 50 / 50 ± 2 %; `static.SpecularGloss`
reads 0.75 on slot A and 0.45 on slot B. The gated render check is highlight elongation: the
specular lobe's major/minor axis ratio on a brushed panel ≥ 1.6 vs the isotropic build.

## 7. The slot and channel budget

| item | cost | running total |
|---|---:|---:|
| current 28 `.ddsc` | 3,953.6 KB | 3,953.6 / 4,648 |
| body `s0` 512² BC1 | 128 KB | 4,081.6 |
| body `s2` 1024² BC1 | 512 KB | 4,593.6 |
| `s1` edit (existing 512² BC5) | 0 | 4,593.6 |
| **free** | **54.4 KB** | |

`derived` — the edge shell and the aniso split add **blocks**, not textures: +1 `CarPaintMM` per
body LOD for the shell, +1 per brushed panel for the aniso split. The model cap is 4,424 KB; the
shell duplicates 2–6 % of the body triangles and must be measured on the assembled `.rbm`, not
assumed. If the shell pushes the model over, use the `s2` channel-3 fallback (§5) and drop the
lacquer band to channel 1.

`derived` — the four channels after this plan: **0** paint, **1** lacquer, **2** metal, **3** edge
(fallback only); the aniso split uses slots, and the wet bake rides the gloss vector and `s1`.
Nothing is left needing a fifth channel.

## 8. Build order and gates

1. `s0` 512² bake (base, metal, clear, edge, aniso mixes) → `s2` 1024² selector → `s1` edits.
2. `factors.py` spec: per-band gloss values (0.60 / 0.60 / 0.85 / 0.98), metallic `[0,0,1,1]`,
   clearcoat 1; replace the `GLOSS_CAP` clamp with the explicit bands (§3.1).
3. `bat_assemble.py` packs the 72 floats; `spec_check.py` must show 0 mismatches, no silently
   inherited template value, and the vectors of §3/§4/§5.
4. Edge shell + aniso material split in the mesh assembly; re-count blocks and model bytes.
5. Gates: 25/25 RBMs re-encode byte-identical; texture total ≤ 4,648 KB; model ≤ 4,424 KB; every new
   `.ddsc` registered in `@files.xml` (MODLOG §103a step 3). Any failure stops before deploy.

## 9. UNKNOWNs, and what would settle each

1. **`F0_d`** — no readable file holds it; the lighting-tuning default is not on disk. Every F0 above
   scales linearly, so the *ranking* of the settings survives, the absolute errors do not.
2. **The channel order of BmAK's `_S` maps** — H1/H2/H3 disagree (`app-per-pixel-reflectivity.md`
   §4.1); the recipe's masks are authored, so it does not depend on the order, but a future grab of
   the body `_S` would.
3. **`GeneralMkIII`'s `Reflectivity_1`** — declared but `[unused]` in the shipped variant; whether a
   different variant honours it, and whether `EnableVariableDialecticSpecFresnel` is a switch or a
   0..1 blend, are shader-body facts.
4. **The wet composition rule** — `0.6 × 0.6 × 1.6 × 0.75` has no decoded order; §4 picks the one
   the values support and records the alternative.
5. **`TEST_WETNESS_FACTOR`'s value and whether `CarPaintMM` samples it** — layout only; a runtime
   constant dump settles it.
6. **Whether `CarPaintMM`'s `m_SpecularGloss` packs a specular level as well as width** — the single
   highest-value unknown; if it does, §3's dielectric residual collapses into the gloss vector.

## 10. Checks run for this report, and revert

| # | check | result |
|---|---|---|
| 1 | BmAK values re-read at the named sources (COLOUR_PARAMS §2–§3, SKINS:548, MATERIALS:1062) | matches the colour report |
| 2 | current build vectors re-read from `Working/Appearance/build_bud1/factors.json` | gloss 0.4, metallic `[0,0,1,0]`, coat 0, `s2`/`s3` dummy |
| 3 | texture total recomputed over the 28 `.ddsc` | 3,953.6 KB of 4,648 |
| 4 | `s2`/`s3` channel encoding checked against `factors.py:20-22` and vanilla `body_mpm` | 4 channels, linear, no sRGB flag |
| 5 | F0 arithmetic in §3/§4 recomputed from `F0 = 0.04(1−m) + albedo·m` | table is self-consistent |
| 6 | `python Tools/scripts/t_paint_gaps.py --check` | re-derives the anchors and the F0 table |

No game process was started; no bake or build was run. **Revert:** delete this file; nothing else was
written.
