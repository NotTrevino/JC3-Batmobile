# Paint plans v2 — the four channels, one row per number, written from one table

**Task.** Rebuild the paint numbers of `tmp/freebuff/reports/paint-gaps-closest-system-plan.md` and
`tmp/freebuff/reports/colour-bmak-wet-look.md` after
`tmp/freebuff/reports/audit-paint-plan-colour-numbers.md` (20 rows: **12 MATCH, 5 MISMATCH,
3 UNSOURCED**). This file is the replacement table: one row per paint number, with channel, member,
planned value, audited value, the rule that produces it, and the file:line the rule reads. The four
channels are then writable from §3 alone.

**Labels.** **decoded** = a tag/value read at the named file and line. **derived** = arithmetic on
decoded values, shown. **SOURCED-ELSEWHERE** = the number exists but not in BmAK. **UNKNOWN** =
searched and absent, with the file/instrument that would settle it.

## 0. Change statement (AGENTS.md)

| item | value |
|---|---|
| intended change | add one report: the v2 paint table, replacing the audited numbers |
| file | `tmp/freebuff/reports/paint-plans-v2.md` (this file) |
| why this file | the brief names it; it is a report, so nothing the game reads changes |
| reverted by | deleting this file. No plan, palette, texture, `.rbm`, `VALUES.json` or build was edited |

## 1. What v2 changes, and why

The audit's five mismatches are fixed here, not restated. Two of them are the ones the brief names:

| # | v1 | v2 | why |
|---|---|---|---|
| M1 | ch3 reflectivity **0.5** (from parent 767) while ch0 takes **0.2** (from body MIC 763) | **0.15** (from 763), F0 **0.0060**, albedo byte **18** | one inheritance rule for every row (§2). `COLOUR_PARAMS.md:37` gives 0.15 on 763; `:55` gives 0.5 on 767 |
| M2 | nearest-MIC rule yields F0 **0.0060**, not the planned **0.0200** | 0.0060 is the plan | same row; the 0.0200 was 767's value wearing 763's rule |
| M3 | albedo **67/65/69** (`0x43/0x41/0x45`) | **67/64/69** (`0x43/0x40/0x45`) | `sRGB(0.05158)=0.2518→64.20→0x40`; `0x41` is 0.052861 linear, 2.5 % high on green |
| M4 | MK2 "0.2 would give 0.132" | **0.162** | `0.04(1−0.2)+0.65×0.2 = 0.032+0.13` |
| M5 | `Wetness_Refl_Fresnel` 0.6 → clearcoat 1.0 | **not written**; clearcoat is 1.0 from the JC3 palette, the Fresnel 0.6 is recorded | 0.6→1.0 is +67 % with no formula |

The three UNSOURCED values are resolved in §4. Four further defects found while building the table
(not in the audit) are fixed in the rows that carry them:

* **D1 — ch1 gloss was 0.60, its own source says 0.75.** `Material1_Roughness` is **0.25** on both
  763 and 767 (`COLOUR_PARAMS.md:35`, `:51`), so `1−0.25 = 0.75`; v1 reused ch0's 0.60. Row 2.
* **D2 — the body base colour was written into `cb6[0..2]`, which carries channels 1–3.** The writer
  maps channel 0 to the generated `s0` and channels 1–3 to `TintColorR/G/B`
  (`factors.py:315`, `:325-329`), and the build on disk holds exactly that (`coverage.md:495-497`).
  v1 left this as a conditional; v2 resolves it: `s0` gets the body colour, the tint gets channels
  1–3. Rows 16–18.
* **D3 — the `cb6[4]` override triple is channel 1's, so it is `[0.75, 0.0, 1.0]`, not `[0.6, 1, 1]`.**
  The writer sets it from `[gloss[1], metal[1], coat[1]]` (`factors.py:330`). The shipped donor's
  `(0.4, 1, 1)` is the *donor's* channel 1, not a BmAK number. Row 19.
* **D4 — the writer cannot emit three of these rows from the BmAK dumps.** `factors.py:256` caps every
  gloss at `gloss_cap` 0.40; `:264-271` sets metallic only from a `Metalicity` name or a
  reflectivity **> 0.5** (ch3's 0.15 would give 0); `:273-274` sets clearcoat only where
  `Normal_Map_Lacquer` is bound (the body has no such map). Rows 1–9 and 20–23 therefore need the
  spec authored explicitly — that is build step 1 in §7, and it is one code change, not a value.

**The audit's own arithmetic slip, corrected.** Its §4/C2 says the ch3 albedo under nearest-wins is
"sRGB **32**". `sRGB(0.0060) = 0.0702 → 17.89 → **18**`; byte 32 is linear 0.0144. The verdict
(wrong MIC) stands; the replacement byte is 18, not 32.

## 2. The inheritance rule, stated once

Every row reads the chain `763 Batmobile_V3_Mainbody_NEW_MIC → 767 Batmobile_V3_WheelArchs_NEW_MIC
→ 359 Batmobile_Worn` (`COLOUR_PARAMS.md:13-17`) by one rule:

> **Nearest MIC that sets the parameter wins; if it does not set it, the parent's value applies; if
> neither sets it, the parameter does not exist and the row says so.**

Applied to the four channels:

| parameter | ch0 | ch1 | ch2 | ch3 |
|---|---|---|---|---|
| roughness, source | 0.4 (763, `:33`) | 0.25 (763, `:35`) | 0.15 (767 only, `:54`) | 0.02 (767 only, `:56`) |
| reflectivity, source | 0.2 (763, `:32`) | 0.2 (763, `:34`) | 0.9 (763, `:36`) | **0.15 (763, `:37`)** |
| metalness, source | absent | absent | 1.0 (767, `:52`) | **absent** |
| base colour, source | 0.025787/0.025787/0.03 (767, `:69`) | 0.01³ (767, `:70`) | 0.215462/0.176446/0.10714 (767, `:71`) | 0,0,0 (767, `:74`) |

763 sets **no** vector and **no** `Material2/3_Roughness` or `Metalicity`; that is why those cells
fall through to 767. It sets all four reflectivities, which is why every reflectivity row is a 763
row — including ch3, the row v1 took from the parent.

## 3. The master table — one row per paint number

`cb2` offsets are from `payload +0x9`; `cb6` from `payload +0x145`
(`CB0_SLOTS.md:79-81`, `:109-115`). Every write value is linear floats unless the row says sRGB byte.

### 3.1 The 26 rows that are written

| # | ch | member (slot @ payload offset) | **v2 value** | v1 | audit | rule | file:line |
|---:|---|---|---|---|---|---|---|
| 1 | 0 | `cb2[0].x` gloss @+0x9 | **0.60** | 0.60 | MATCH | `1 − Material0_Roughness` | `COLOUR_PARAMS.md:33`; `factors.py:250` |
| 2 | 1 | `cb2[0].y` gloss @+0xD | **0.75** | 0.60 | **D1 fix** | `1 − Material1_Roughness 0.25` | `COLOUR_PARAMS.md:35` |
| 3 | 2 | `cb2[0].z` gloss @+0x11 | **0.85** | 0.85 | MATCH | `1 − Material2_Roughness 0.15` (767) | `COLOUR_PARAMS.md:54` |
| 4 | 3 | `cb2[0].w` gloss @+0x15 | **0.98** | 0.98 | MATCH | `1 − Material3_Roughness 0.02` (767) | `COLOUR_PARAMS.md:56` |
| 5 | 0 | `cb2[1].x` metallic @+0x19 | **0.0** | 0.0 | MATCH | no `Material0_Metalicity` → dielectric | `COLOUR_PARAMS.md:32-37` |
| 6 | 1 | `cb2[1].y` metallic @+0x1D | **0.0** | 0.0 | MATCH | no `Material1_Metalicity` | `COLOUR_PARAMS.md:34-35` |
| 7 | 2 | `cb2[1].z` metallic @+0x21 | **1.0** | 1.0 | MATCH | `Material2_Metalicity` | `COLOUR_PARAMS.md:52` |
| 8 | 3 | `cb2[1].w` metallic @+0x25 | **1.0** | 1.0 | UNSOURCED → §4/U2 | no `Material3_Metalicity`; set so the metal branch makes `F0 = albedo` | `COLOUR_PARAMS.md:37`; `factors.py:264-271` |
| 9 | 0–3 | `cb2[2].x/.y/.z/.w` coat @+0x29/+0x2D/+0x31/+0x35 | **1.0** | 1.0 | UNSOURCED → §4/U1 | JC3 palette `clear_coat` 1.000 on 10/10 records | `PALETTE_HASH.md:153-162`; `COLOUR_PARAMS.md:161` (no BmAK clear-coat parameter) |
| 10 | 0 | `s0` DiffuseMap, body region mean (sRGB bytes) | **67/64/69** | 67/65/69 | MISMATCH → fixed | `srgb8(Material0_BaseColour × Diffuse_Adjust)` = `srgb8(0.056731/0.051574/0.06)` | `COLOUR_PARAMS.md:68,69`; `factors.py:169` |
| 11 | 1 | `s0` region mean (sRGB) | **41/41/41** | — | new | `srgb8(0.01 × 2.2 = 0.022)` | `COLOUR_PARAMS.md:70` |
| 12 | 2 | `s0` region mean (sRGB) | **53/53/53** | 53 | MATCH (arith); hue conflict §5.1 | `srgb8(0.04 × Material2_Reflectivity 0.9 = 0.036)` | `COLOUR_PARAMS.md:36`; `audit §3` row 9 |
| 13 | 3 | `s0` region mean (sRGB) | **18/18/18** | 39 | MISMATCH → fixed | `srgb8(0.04 × Material3_Reflectivity 0.15 = 0.0060)` | `COLOUR_PARAMS.md:37` |
| 14 | edge | shell block `s0` (sRGB) | **89/89/89** | 89 | MATCH | `srgb8(EdgeMask_Colour 0.1)` | `COLOUR_PARAMS.md:155` |
| 15 | edge | shell block `cb2[0].x` gloss | **0.97** | 0.97 | MATCH | `1 − EdgeMask_Roughness 0.03` | `COLOUR_PARAMS.md:127` |
| 16 | edge | shell block `cb2[1].x` metallic | **1.0** | 1.0 | MATCH | `EdgeMask_Metalicity 2.0` clamped to the member's 0..1 | `COLOUR_PARAMS.md:47` |
| 17 | MK2 | arch `s0`, MK2 paint texels (sRGB) | **211/211/211** | 211 | MATCH | `srgb8(Paint_Reflectivity-derived albedo 0.65)` | `SKINS.md:548` |
| 18 | 1→R | `cb6[0]` `m_TintColorR` @+0x145 | **[0.022, 0.02, 0.02, 1.0]** | 0.025787×3 | **D2 fix** | `Material1_Basecolour × Diffuse_Adjust` (2.2, 2, 2) | `COLOUR_PARAMS.md:68,70`; `factors.py:325-329` |
| 19 | 2→G | `cb6[1]` `m_TintColorG` @+0x155 | **[0.47402, 0.35289, 0.21428, 1.0]** | 0.025787×3 | **D2 fix** | `Material2_BaseColour × Diffuse_Adjust` | `COLOUR_PARAMS.md:68,71` |
| 20 | 3→B | `cb6[2]` `m_TintColorB` @+0x165 | **[0.0, 0.0, 0.0, 1.0]** | 0.025787×3 | **D2 fix** | `Material3_BaseColour × Diffuse_Adjust` | `COLOUR_PARAMS.md:74` |
| 21 | 1 | `cb6[4].x/.y/.z` overrides @+0x185/+0x189/+0x18D | **[0.75, 0.0, 1.0]** | [0.6, 1.0, 1.0] | MISMATCH → fixed (B8–B10) | `= [gloss[1], metal[1], coat[1]]` | `factors.py:330`; `CB0_SLOTS.md:113-115` |
| 22 | all | palette `tint_r/g/b` (10 records, linear, A=1.0) | **0.025787 / 0.025787 / 0.03** | same | MATCH (arith) | raw `Material0_BaseColour`, **no** `Diffuse_Adjust` | `COLOUR_PARAMS.md:69`; offsets §5 |
| 23 | 0 | palette `specular_gloss` (10 records) | **0.60** | 0.60 | MATCH | `= ch0 gloss` | `PALETTE_HASH.md:153-162` |
| 24 | 2 | palette `metallic` (10 records) | **1.0** | 1.0 | UNSOURCED → §4/U2 | `Material2_Metalicity` | `COLOUR_PARAMS.md:52` |
| 25 | all | palette `clear_coat` (10 records) | **1.0** | 1.0 | UNSOURCED → §4/U1 | palette convention 1.000 | `PALETTE_HASH.md:153-162` |
| 26 | — | `VALUES.json` `paint.gloss_cap` | **1.0** | 0.4 | MATCH (cap must move) | a convention, not a format limit; the donor palette ships 0.45 on 8/10 | `VALUES.json:5`; `factors.py:256` |

**The four channels, as write vectors — this is the whole of §3.1 in one block.**

```
cb2[0] gloss    = [0.60, 0.75, 0.85, 0.98]
cb2[1] metallic = [0.00, 0.00, 1.00, 1.00]
cb2[2] coat     = [1.00, 1.00, 1.00, 1.00]
cb6[0..2]       = [0.022, 0.02, 0.02, 1] / [0.47402, 0.35289, 0.21428, 1] / [0, 0, 0, 1]
cb6[4] override = [0.75, 0.00, 1.00]
s0 body         = 67/64/69 sRGB, with region means 41 (ch1), 53 (ch2), 18 (ch3) by s2 mask
edge shell      = s0 89, gloss 0.97, metallic 1.0   (second material slot)
palette x10     = tint 0.025787/0.025787/0.03 A=1, gloss 0.60, metallic 1.0, coat 1.0
```

`s0` is **one texture per block**, not four: rows 10–13 are region means selected by the `s2`
PropertyMap (R = ch1, G = ch2, B = ch3, black = ch0, `factors.py:20-22`). With no mask baked, the
whole body is row 10.

### 3.2 The 11 rows that are recorded, never written

No member carries these (`cb2` = gloss, metallic, clearcoat; 0 of 13 `carpaintmm*` headers declare
wetness, F0 or anisotropy — card-T-21 A11). They are the gap ledger, not candidates for a guess.

| # | ch | BmAK number | value | rule | file:line |
|---:|---|---|---|---|---|
| 27 | 0 | `Material0_Reflectivity` | 0.2 → F0 **0.0080** | `0.04 × R` (bridge `F0_d = 0.04` **ASSUMED**) | `COLOUR_PARAMS.md:32` |
| 28 | 1 | `Material1_Reflectivity` | 0.2 → F0 **0.0080** | same | `COLOUR_PARAMS.md:34` |
| 29 | 2 | `Material2_Reflectivity` | 0.9 → F0 **0.0360** | same; carried by row 12 | `COLOUR_PARAMS.md:36` |
| 30 | 3 | `Material3_Reflectivity` | **0.15** → F0 **0.0060** | same; **nearest-wins** (v1 used 0.5/0.0200) | `COLOUR_PARAMS.md:37` |
| 31 | wet | `Wetness_Refl_Fresnel` | 0.6 | decoded, no member | `COLOUR_PARAMS.md:65,103` |
| 32 | wet | `Wetness_Reflectivity_Multiplier` | 0.6 | decoded, **no member, no decoded use** → §4/U3 | `COLOUR_PARAMS.md:105` |
| 33 | wet | `RainReflectivityMul` | 1.6 → `R_wet` **0.32** → F0 **0.0128** | `0.2 × 1.6` | `COLOUR_PARAMS.md:110` |
| 34 | wet | `RainRoughnessMul` | 0.75 → wet gloss **0.70** | `1 − 0.4 × 0.75` | `COLOUR_PARAMS.md:114` |
| 35 | wet | wet composite gloss (fallback only) | **0.70 / 0.8125 / 0.8875 / 0.985** | `1 − roughness × 0.75` per channel; ch1 corrected from v1's 0.70 | derived from rows 1–4 |
| 36 | MK2 | `Paint_Reflectivity` 0.5 + `Paint_Metalicity` 0.2 | F0 **0.162** | `0.04(1−0.2) + 0.65×0.2` (v1 said 0.132, which needs albedo 0.5) | `SKINS.md:548` |
| 37 | — | current `s0` solid in the build | **122/117/126** | measured on disk; the retired gain, not a target | `build_bud1/factors.json:2874-2879` |

**Reconciliation with the audit's 20 rows:** all 20 are in the table — 12 MATCH (rows 1, 3–7, 14–17,
23, 26 reach the same numbers), 5 MISMATCH (rows 10, 13, 21, 30, 36), 3 UNSOURCED (rows 8, 9, 32,
resolved in §4). The audit's ch2/ch3 gloss and `RainRoughnessMul` rows are unchanged.

## 4. The three unsourced values, resolved

Each is either sourced or marked UNKNOWN with the file that settles it. None is left as a silent
constant.

### U1 — clear coat 1.0 → **sourced elsewhere (JC3 palette), BmAK side UNKNOWN**

The audit is right that BmAK has no clear-coat parameter: `COLOUR_PARAMS.md` §2/§3 (69 chain
expressions, 52 overrides) contains no `clear_coat`, `ClearCoat` or `Material*_ClearCoat` name, and
`factors.py:273-274` keys the coat off `Normal_Map_Lacquer`, which the body material does not bind.
**The value 1.0 is sourced — from the JC3 side:** every one of the 10 palette records carries
`clear_coat = 1.000000` (`PALETTE_HASH.md:153-162`, the coat column), and the donor paint blocks ship
the same 1 in their override triple (`colour-bmak-wet-look.md` §6.1). So row 9/25 is
**SOURCED-ELSEWHERE**, not invented.

**Still UNKNOWN:** whether a clear-coat *parameter* exists on the BmAK side (it is not in the
serialised parameter names, and the operator graph that would express it is stripped — 944/944
`FunctionExpressions` slots zero, `COLOUR_PARAMS.md` §5). **Would settle it:** the compiled shader
body of `Batmobile_Worn` (a `.usf`/SHEX decode), which is not in the repository; the package itself
cannot answer it.

### U2 — `m_Metallic[3] = 1.0` (and palette `metallic` 1.0) → **derived, not sourced**

There is no `Material3_Metalicity` in any of the 52 overrides or 69 chain expressions
(`COLOUR_PARAMS.md:32-56`, `:100-128`); the only metalness in the whole chain is
`Material2_Metalicity = 1.0` (`:52`, `:128`). Row 8's 1.0 is therefore **derived from a rule**, not
copied: the metal branch gives `F0 = 0.04(1−m) + albedo·m`, so `m = 1` is the only setting that lets
the ch3 albedo byte (row 13, 0.0060) be the F0. With `m = 0` the channel would sit at the fixed
dielectric 0.04, i.e. 6.7× the 0.0060 target.

**Still UNKNOWN:** whether a `Material3_Metalicity` exists on another Batmobile variant.
**Would settle it:** `Tools/scripts/grab_colour_params.py` re-run over
`Playable_BatmobileMK2_SF.upk` and the remaining `Playable_Batmobile*` packages — the tool exists and
was used for `COLOUR_PARAMS.md`, but the MK2 master's own defaults are not decoded anywhere in the
repo (`colour-bmak-wet-look.md` §1, §8 item 4). Also open: whether the SHEX reads
`cb2[1].w` at all (four slots exist; channel use UNKNOWN, `CB0_SLOTS.md:79-81`).

### U3 — `Wetness_Reflectivity_Multiplier` 0.6 → **decoded value, unsourced use**

The number is decoded: 0.6, `FloatProperty @0xcc`, expression 500 (`COLOUR_PARAMS.md:105`). What the
audit calls unsourced is its **role**: v1 used it as a layer weight and v2 keeps it out of the
arithmetic (row 32). The alternative — a second multiplier — gives `R_wet = 0.2 × 0.6 × 1.6 = 0.192`
and F0 0.00768, *below* the dry 0.008, which contradicts the decoded "wet raises reflectivity".
That is a plausibility argument, not a decoded composition order.

**Still UNKNOWN:** the order in which the four wet numbers compose.
**Would settle it:** the BmAK material-function graph, which is stripped in this package
(944/944 slots zero, `COLOUR_PARAMS.md` §5) — so it needs the un-stripped UE3 material source, not
another read of `Playable_Batmobile_SF.upk`. No JC3 member can carry any of the four anyway.

## 5. Two conflicts the table must carry honestly

### 5.1 ch2 holds two decoded numbers that JC3's metal branch cannot separate

`Material2_BaseColour` is **0.215462 / 0.176446 / 0.10714** (sRGB 128/117/92, a dim warm metal,
`COLOUR_PARAMS.md:71`), while row 12 writes **0.036** (byte 53) because `F0 = 0.04 × 0.9`. In the
metal branch `F0 = albedo`, so the channel cannot have both. v2 keeps the F0 value (row 12) because
the reflectance ladder checks F0, and carries the warm hue in `cb6[1]` = 0.47402/0.35289/0.21428
(row 19).

**What that costs, quantified:** if the shader multiplies `s0` by the tint before the metal branch,
ch2's effective F0 is `0.036 × 0.474 = **0.0171**`, 47 % below the 0.0360 target. Whether the multiply
happens is UNKNOWN (the tint/s0 combine rule is not on disk — `colour-bmak-wet-look.md` §8 item 6);
**would settle it:** the `carpaintmm*.fb.txt` SHEX body, not in the repo. If it does multiply, the
ch2 row must move to albedo 53/48/36 (hue-preserved at F0 0.036, derived by scaling 0.036 by
0.215462/0.176446/0.10714) — not adopted here because that scale is invented.

### 5.2 The palette layout: two files, two shapes

The write plan's v1 formula `0x50 + 80i + 20` is wrong in both files (audit §4.1). The two sources do
not even share a layout:

| carrier | first float of record *i* | members after it | evidence |
|---|---|---|---|
| build palette (`scratch/tint/palette.xml`, 920 B) | `tint_r.R = 0x74 + 0x50·i` | `+16` g, `+32` b, `+48` gloss, `+52` metallic, `+56` coat (type offsets 20/36/52/68/72/76) | ADF export, `offset-in-file` on every member |
| vanilla grab (`PALETTE_HASH.md`, 1,897 B) | 7 contiguous floats at `0x94 + 0x50·i` = R, G, B, A, gloss, metallic, coat | contiguous, so its `Tint` type is not the build's | `PALETTE_HASH.md:166-179` |

v2 writes the **build** palette at `0x74 + 0x50·i` and never assumes the grab's `0x94` is the same
member (the audit's formula "GRAB `tint_r.R = 0x94`" cannot hold beside GRAB's own contiguous 7-float
read — `0x94` is where the colour+scalars block starts). Because the layouts differ, the palette edit
is verified by re-export and the 4-byte round trip, not by the formula: `TINT_WRITE.md` §3 (1897 B →
1897 B). The build palette already holds `0.05` on every channel of every record with
`metallic = 1`, `coat = 1` (audit §4.4), so a gloss/metallic/coat read-back cannot distinguish a
correct write from a partial one — only the tint floats can.

## 6. Closest JC3 paint members for each remaining gap

Each row is a gap that survived v2, the nearest real member, and what carrying it costs.

| gap | BmAK number(s) | closest JC3 member (decoded) | exactness | cost |
|---|---|---|---|---|
| reflectivity / F0 (rows 27–30) | 0.2 / 0.2 / 0.9 / 0.15 | `cb2[1]` `m_Metallic` metal branch + `cb2[2]` `m_ClearCoat` as a second lobe | exact on ch2 (0 error); +0.032 (5.0×) on ch0/ch1, +0.014 on ch3 | ch0/ch1 cannot reach 0.008 at any albedo; the residual is the ledger value |
| wet family (rows 31–35) | 0.6 / 0.6 / 1.6 / 0.75 | none on `CarPaintMM`; scene `TEST_WETNESS_FACTOR` @104 (`deferred_clusteredlightingtunable`), `Window` `s9` `RainOccluderSampler`, `GeneralMkIII` `WetnessNoiseTexture` | look-exact only as a fixed bake | the only writeable form is the composite gloss 0.70 (row 35) — ships dry 0.60, so the wet look is the scene's |
| edge mask (rows 14–16) | 0.1 / 0.03 / 2.0 | **extra material slot**: a second `CarPaintMM` block on a duplicated edge shell | exact per value, no channel consumed | +1 block per body LOD; 2–6 % more triangles. The `s2` B-channel fallback is **not** available in v2 — ch3 already owns that channel (row 13) |
| anisotropy | [0.462, 0.734, 0.972] / [0.196, 0.2, 0.33] + ramp | none; baked comb in `s1` + a two-slot gloss split 0.75 / 0.45 | closest: the highlight elongates, the BRDF stays isotropic | 2 slots; 3 px comb at 512² is near Nyquist (4 px if it aliases) |
| four channel colours | Material0–3 base colours | one tint vector per channel (`cb6[0..2]`, rows 18–20) + `s0` for ch0 | exact for 3 of 4 channels; ch0 is texture-only | `cb2` has no four-colour set; ch0's colour exists only as `s0` bytes |
| `Diffuse_Adjust` 2.2/2/2 | no gain member | pre-multiplied into `s0` (row 10) | exact by construction | none — but it is why 67/64/69 and not 45/45/48 |
| mud / damage family | `Mud_*`, `Damage_*` | `cb2[5..7]`, `cb2[15..17]` exist, disabled (`SupportDirt` 0, `SupportDmgBlend` 0) | not carried | chapter-scripted in BmAK; the JC3 dirt path is procedural |

## 7. The build step

Ordered; each step is the tool that does it, with the line that makes it true.

0. **Unblock the writer.** `Research/BatmobileGrab/VALUES.json:5` `gloss_cap` → **1.0**,
   `:18` `albedo_gain` → **1.0**. Until both change, `factors.py:256` caps every gloss to 0.40 and the
   albedo keeps its 3.4× gain whatever the spec says. This is a data edit, not code.
1. **Author the four channels explicitly.** The writer's rules cannot produce rows 1–9, 20–23 from
   the BmAK dumps: `factors.py:256` (cap), `:264-271` (metallic only from a `Metalicity` name or
   reflectivity > 0.5 — ch3's 0.15 gives 0), `:273-274` (coat only where `Normal_Map_Lacquer` is
   bound). Either add `Material3_Metalicity`/lacquer bindings to the props dumps, or patch
   `factors.py`'s `jc3_spec` so the paint material reads the five vectors from this table. One code
   change; without it the pack writes gloss 0.40, metallic `[0,0,1,0]`, coat 0 — the current build
   exactly (`coverage.md:470-472`).
2. **Spec + bake.** `python Tools/scripts/factors.py <model.pskx> <src_dir> -o
   Working/Appearance/build_bud1/factors.json --report Working/Appearance/build_bud1/coverage.md`
   (usage in `factors.py:21`). The `s0` solids/regions of rows 10–17 are written here via
   `factors.srgb8` (`factors.py:169`) — the body region 67/64/69, and **not** the 122/117/126 the
   current `factors.json:2874-2879` holds.
3. **Pack the block.** `python Tools/scripts/bat_assemble.py <model.pskx> …` — `static_params` as
   `pack("<72f", …)` in `FX.STATIC` order (`bat_assemble.py:831`; order `factors.py:42`),
   `dynamic_params` as `pack("<16f3f", …)` (`bat_assemble.py:833-835`), palette via `--palette` /
   `--palette-xml` (`bat_assemble.py:561-562`). The full required argument set is the parser's
   (`bat_assemble.py:534-571`); the paths differ per build and are not reproduced here.
4. **Verify the block.** `python Tools/scripts/spec_check.py <build_dir> <template.rbm> --block 3`
   (`spec_check.py:36-39`): `static_params[0:4]` = `[0.60, 0.75, 0.85, 0.98]`,
   `[4:8]` = `[0,0,1,1]`, `[8:12]` = `[1,1,1,1]`, `dynamic_params[0:12]` = rows 18–20,
   `[16:19]` = `[0.75, 0.0, 1.0]`; zero mismatches, no inherited template value.
5. **Bake and gate.** `python Tools/scripts/appearance_bake.py --out Builds/bm-RC4-appearance`
   (usage `appearance_bake.py:30`; per-material patch `:534-546`). Hard gates, all pre-existing:
   every patched `.rbm` re-encodes byte-identically (`:549-551`), texture total ≤ 4,648 KB, model
   ≤ 4,424 KB, all 185 `CarPaintMM` blocks carry the same five vectors, every new `.ddsc` registered
   in `@files.xml` (`MODLOG` §103a). Any failure stops before deploy.
6. **Palette read-back only after a re-export** (§5.2): the 10 records at `0x74 + 0x50·i` must read
   0.025787 / 0.025787 / 0.03 with A = 1.0, gloss 0.60, metallic 1.0, coat 1.0 — and the read is
   only meaningful on the tint floats, because the build palette already holds 0.05 / 1 / 1.

No test or game run is part of this step; the pass bands that need the probe remain gated
(`tmp/freebuff/APPROVED_Q.txt`).

## 8. Pilot sentence — the body colour, with its measured band

**Pilot:** the body's `s0` region must measure **RGB 67/64/69 with a ±2 code-value band** (linear
0.056731 / 0.051574 / 0.060000 = `Material0_BaseColour` × `Diffuse_Adjust`), against the
**122/117/126** the current solid writes (`Working/Appearance/build_bud1/factors.json:2874-2879`,
measured on disk) and the **45/45/48** of the raw authored base — a reading in the 122 band is the
retired 3.4× gain, a reading in the 45 band is `Diffuse_Adjust` dropped, and the green byte is `0x40`,
not the `0x41` v1 printed.

## 9. Checks run for this report, and revert

| # | check | result |
|---|---|---|
| 1 | every BmAK number re-read at `COLOUR_PARAMS.md` with its line (`:32-37`, `:47-56`, `:65`, `:68-74`, `:100-128`, `:155`) | all present; `Material3_Reflectivity` = **0.15** on 763 (`:37`), 0.5 on 767 (`:55`) |
| 2 | sRGB transfer recomputed on this report's own tooling for 14 linear values | base 45/45/48; effective 67/64/69; 0.036→53; 0.020→39; **0.0060→18** (audit's "32" does not reproduce); 0.1→89; 0.65→211; 0.022→41 |
| 3 | `F0 = 0.04(1−m) + albedo·m` recomputed for 5 rows | 0.0080 / 0.0080 / 0.0360 / 0.0060 / MK2 **0.162**; ch2 tint product 0.0171 recorded |
| 4 | gloss chain recomputed for 4 channels and the wet fallback | 0.60 / **0.75** / 0.85 / 0.98; wet 0.70 / **0.8125** / 0.8875 / 0.985 |
| 5 | writer rules read at the cited lines | `factors.py:250` inversion, `:256` cap, `:264-271` metallic, `:273-274` coat gate, `:315`/`:325-329` channel→carrier, `:330` overrides; `bat_assemble.py:831`, `:833-835`; `spec_check.py:36-39`; `appearance_bake.py:534-546` |
| 6 | current build state re-read | body gloss `[0.4,0.4,0.4,0.4]`, metallic `[0,0,1,0]`, coat 0 (`coverage.md:470-472`), tints `[0.022,0.02,0.02]` / `[0.47402,0.35289,0.21428]` / `[0,0,0]` (`:495-497`), s0 solid `[0.4784,0.4588,0.4941]` (`factors.json:2874-2879`) |
| 7 | palette coat column and record count | `clear_coat` 1.000000 on 10/10 (`PALETTE_HASH.md:153-162`); offsets re-derived from the member layout (§5.2) |

Not run: no `factors.py`/`bat_assemble.py`/`spec_check.py`/`appearance_bake.py` invocation, no
palette edit, no `.rbm`, texture, `VALUES.json` or build change, no game process, no `--check` of
`grab_colour_params.py` or `jc3_palette_hash.py`. Every number above is a file read or arithmetic on
one; the pilot band is a target derived from those reads, not a rendered measurement.

**Revert:** delete this file. Nothing else was written.
