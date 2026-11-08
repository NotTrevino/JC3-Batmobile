# Audit: the colour and material numbers in the two paint plans

Lane 8014, 2026-11-07. Audits `tmp/freebuff/reports/paint-gaps-closest-system-plan.md` and
`tmp/freebuff/reports/colour-bmak-wet-look.md`. For each number the brief lists — base
`0.025787 / 0.025787 / 0.03`, roughness `0.4`, reflectivity `0.2`, metalness `1.0`, clear coat `1.0`,
wet `0.6 / 0.6 / 1.6 / 0.75` — this file re-reads the BmAK source, names the JC3 slot and offset the
plan sends it to, and recomputes the conversion (sRGB transfer, gain, clamp, unit). **Neither plan was
edited.** `AGENTS.md` is followed: every row cites a file read in this session; where a conversion has
no stated arithmetic the verdict is `UNSOURCED`, not "probably fine".

## 0. Change statement (AGENTS.md)

| item | value |
|---|---|
| intended change | add one audit report; no plan, texture, `.rbm`, ledger or build touched |
| file | `tmp/freebuff/reports/audit-paint-plan-colour-numbers.md` (this file) |
| why this file | the brief names it; it is a report, so nothing the game reads changes |
| reverted by | deleting this file. No other file was written |

## 1. Verdict summary

20 audited rows: **MATCH 12, MISMATCH 5, UNSOURCED 3.**

| verdict | rows |
|---|---|
| MATCH | base R/G/B → sRGB 45/45/48; gloss 0.60 / 0.85 / 0.98; wet gloss 0.70 / 0.8875 / 0.985; `R` 0.2 → F0 0.0080 with residual +0.0320 (5.0×); channel-2 `R` 0.9 → 0.0360; edge metal 2.0 → 1.0 clamp; channel-2 metal 1.0; `RainReflectivityMul` 1.6 → 0.32 / 0.0128 / +0.0272; `RainRoughnessMul` 0.75 → ×0.75 |
| MISMATCH | the `0x83/0x7d/0x86` byte attribution; the current `s0` solid's stated derivation; channel-3 `R` 0.5 vs the nearest-MIC 0.15; MK2 "0.2 would give 0.132"; `Wetness_Refl_Fresnel` 0.6 → clearcoat 1.0 |
| UNSOURCED | clear coat 1.0 (its source is the JC3 palette, not BmAK); `m_Metallic[3] = 1`; `Wetness_Reflectivity_Multiplier` 0.6 |

The three UNSOURCED rows are **choices the plans make to reach a target**, not copied values; two of
the five MISMATCHes are arithmetic that does not reproduce the number printed beside it, and one is a
source read from the wrong MIC.

## 2. Sources re-read for this audit

| read | what it gave | result |
|---|---|---|
| `Research/BatmobileGrab/COLOUR_PARAMS.md` §2 rows 32-56, 69; §3 rows 11-19, 21-22, 28-36 | the MIC overrides and master defaults | all values the plans quote exist, **except** `Material3_Reflectivity` on 763 (§4 C2) |
| same §3 row 69 / §2 row 38 | `Material0_BaseColour` = `[0.025787, 0.025787, 0.03, 1]`, `Diffuse_Adjust` = `[2.2, 2, 2, 1]` (VectorParameterValues 0x168, items 262 / 176) | confirmed |
| `Research/BatmobileGrab/VALUES.json` lines 4-23 | `gloss_cap` 0.4, `authored_gloss` 0.6, `base_colour`, `effective_base_colour`, `albedo_gain` 3.4476 with its own source string | confirms `effective = base × Diffuse_Adjust` and that 3.4476 is a **luma ratio** |
| `Research/BatmobileGrab/SKINS.md:548` | MK2 `Paint_Reflectivity` 0.5, `Paint_Metalicity` 0.2, `Paint_Roughness` 0.1 | confirmed |
| `Research/JC3Grab/CB0_SLOTS.md` §3-§5 | `cb2[0]` @0 `m_SpecularGloss` (float4), `cb2[1]` @16 `m_Metallic` (float4), `cb2[2]` @32 `m_ClearCoat` (float4); tint is `cb6[0..2]`, **not** `cb0` | slots and offsets used below |
| `Tools/scripts/factors.py` (disposition table line 125, reflectivity line 127, base colour line 137, `GLOSS_CAP` clamp line 256) | gloss = `1 − roughness × mul`; reflectivity only becomes metallic above 0.5; base colour → `s0` solid; every gloss `min(g, 0.4)` | the plan's gloss inversion and its "cap must move" claim are real |
| `Working/Appearance/build_bud1/factors.json` (`Batmobile_V3_Mainbody_NEW_MIC`) | gloss `[0.4,0.4,0.4,0.4]`, metallic `[0,0,1,0]`, coat `[0,0,0,0]`, `s0` solid `[0.4784314, 0.4588235, 0.4941176]` | **exactly** the plan's §2 "decoded" table; 122/117/126 of 255 |
| `Working/Palette/serpente_palette.xml` | 10 tints: **8 × 0.449999988**, 2 × 0 | the plan's "0.45 on 8 of its 10 tints" is right |
| `Research/challenge/T2_TRANSLATION.md` C03, C04 | prior refutations of the same 3.4476 / gloss-cap claims | one of them is repeated in the colour report (§4 C1) |

## 3. The audit table

`static_params` indices are the plan's own (`§2`: gloss `[0..3]`, metallic `[4..7]`, coat `[8..11]`);
`cb2` offsets are `CB0_SLOTS.md` §3. "Recomputed" is this audit's arithmetic, shown in the cell.

| # | value as written | BmAK source | JC3 slot / offset | plan's converted value | recomputed | verdict |
|---:|---|---|---|---|---|---|
| 1 | base R/G `0.025787` | `Material0_BaseColour` on 767, `COLOUR_PARAMS` §2 row 38 | `s0` DiffuseMap, slot 0 (sRGB) | sRGB **45** | `1.055·0.025787^(1/2.4)−0.055 = 0.17479` → ×255 = **44.6 → 45** | **MATCH** |
| 2 | base B `0.03` | same row 38 | `s0`, slot 0 | sRGB **48** | `0.18968` → ×255 = **48.4 → 48** | **MATCH** |
| 3 | effective base `0.056738 / 0.05158 / 0.06` and "albedo byte `0x83/0x7d/0x86`" (colour §2, §7) | base × `Diffuse_Adjust` `[2.2, 2.0, 2.0]`, row 37 | `s0` (claimed) | "through the project's linear→sRGB gain 3.4476" | `0.025787×2.2 = 0.056731`, `×2.0 = 0.051574`, `0.03×2 = 0.06` → **MATCH** as a product; `sRGB(0.056738) = 0.2642` → **byte 67 (0x43)**, and `0.0258×3.4476 = 0.0889 ≠ 0.056738` | **MISMATCH** (the gain sentence) |
| 4 | current `s0` solid `[0.4784, 0.4588, 0.4941]` "base × 3.45 gain" (paint plan §2) | base + `Diffuse_Adjust`, row 38/37 | `s0` solid, slot 0 | 3.45× the base | on disk **verified** (`factors.json`), but `0.4784 = 122/255` is sRGB of linear **0.1946** = **3.43× the effective** colour (G 3.45×, B 3.48×) — or **7.55×** the base; base × 3.45 in linear is `0.08897` → **byte 84**, not 122 | **MISMATCH** (derivation only; value is real) |
| 5 | roughness `0.4` → gloss | `Material0_Roughness` 0.4, rows 33 (763) / 48 (767) | `cb2[0]` @0, `static_params[0..3]` | **0.60** | `1 − 0.4 = 0.60`; `factors.py:125` implements exactly this inversion | **MATCH** |
| 6 | ch2 roughness `0.15` → 0.85 | `Material2_Roughness` 0.15, row 54 | `cb2[0].z` @8 | **0.85** | `1 − 0.15 = 0.85` | **MATCH** |
| 7 | ch3 roughness `0.02` → 0.98 | `Material3_Roughness` 0.02, row 55 | `cb2[0].w` @12 | **0.98** | `1 − 0.02 = 0.98` | **MATCH** |
| 8 | reflectivity `0.2` → F0 | `Material0_Reflectivity` 0.2, row 32 (763) | no F0 member: `m_Metallic` `cb2[1]` @16 + `s0` metal-branch albedo | target **0.0080**; achieved `m=0` → **0.0400**, error **+0.0320 (5.0×)** | `0.04×0.2 = 0.008`; `0.040−0.008 = 0.032`; `0.040/0.008 = 5.0` | **MATCH** (bridge `F0_d = 0.04` **ASSUMED**, correctly labelled) |
| 9 | ch2 reflectivity `0.9` → albedo `0.036` | `Material2_Reflectivity` 0.9, rows 36/53 | `cb2[1].z` = 1, `s0` texel 53 | **0.0360**, error 0 | `0.04×0.9 = 0.036`; `sRGB(0.036) = 0.2091` → **53.3 → 53** | **MATCH** |
| 10 | ch3 reflectivity `0.5` → F0 `0.0200` | `Material3_Reflectivity` — **0.15** on 763 (row 6), 0.5 on 767 (row 24) | `cb2[1].w` + `s0` texel 39 | **0.0200** | the plan's own nearest-MIC rule (which takes ch0's 0.2 from 763, not 0.15 from 767) gives **0.15** → `0.04×0.15 = 0.0060`; 0.5 is the **parent** value | **MISMATCH** (wrong MIC) |
| 11 | MK2 paint `R` 0.5, "`m=0` (0.2 would give **0.132**)" | `Paint_Reflectivity` 0.5 / `Paint_Metalicity` 0.2, `SKINS.md:548` | `cb2[1]` + `s0` (MK2 texels 211 = 0.65) | 0.132 | `0.04(1−0.2) + 0.65×0.2 = 0.032 + 0.13 = **0.162**`; 0.132 needs an albedo of **0.5**, which contradicts the plan's own `0.65` row | **MISMATCH** |
| 12 | `EdgeMask_Metalicity` 2.0 → 1.0 | rows 16 / §3 row 21 | `cb2[1]` ch3 (or shell block) | **1.0** | clamp to the member's 0..1 domain; declared as a clamp, not a fit | **MATCH** |
| 13 | metalness `1.0` (ch2) | `Material2_Metalicity` 1.0, row 21 (expr 523) | `cb2[1].z` @24, `static_params[6]` | **1.0** | direct copy, no unit change | **MATCH** |
| 14 | metalness `-> [0, 0, 1, 1]` (ch3 = 1) | **no `Material3_Metalicity` exists** in any dump | `cb2[1].w` @28 | **1.0** | set so the metal branch yields `F0 = albedo = 0.020`; BmAK gives no number here | **UNSOURCED** |
| 15 | clear coat `1.0` | **none** — BmAK has no clear-coat parameter; the plan's stated source is `COLOUR.md` §4 (every **JC3** tint ships 1.000) | `cb2[2]` @32, `static_params[8..11]` | **1.0** | 1.0 → 1.0, no conversion. But the value is **JC3's palette convention**, not BmAK's | **UNSOURCED** (on the BmAK side) |
| 16 | `Wetness_Refl_Fresnel` 0.6 → clearcoat | expr 498 / row 34, 0.6 | `cb2[2]` @32 | **1.0** | 0.6 → 1.0 is **+67 %** with no formula; the plan itself says the wet composition order is UNKNOWN | **MISMATCH** |
| 17 | `Wetness_Reflectivity_Multiplier` 0.6 | expr 500, 0.6 | no member; treated as "layer weight" | discarded as a multiplier | no arithmetic at all — the 0.192 branch is rejected by a plausibility argument, which the plan states | **UNSOURCED** |
| 18 | `RainReflectivityMul` 1.6 → `R_wet` 0.32 | expr 505, 1.6 | `cb2[1]` stays 0 + `cb2[2]` = 1 | **0.32** → F0 **0.0128**; residual **+0.0272** | `0.2×1.6 = 0.32`; `0.04×0.32 = 0.0128`; `0.040−0.0128 = 0.0272`; alternative `×0.6 = 0.192` → `0.00768 < 0.008` dry | **MATCH** |
| 19 | `RainRoughnessMul` 0.75 → gloss 0.70 | expr 509, 0.75 | `cb2[0].x/.y` @0/@4 | **0.70** (from 0.60); ch2 **0.8875**, ch3 **0.985** | `1 − 0.4×0.75 = 0.70`; `1 − 0.15×0.75 = 0.8875`; `1 − 0.02×0.75 = 0.985` | **MATCH** |
| 20 | gloss cap "replaced by 0.60 / 0.60 / 0.85 / 0.98", cap 0.40 is a convention | `VALUES.json:5` 0.4 from `sportsmuscle_body_lod1.rbm` block 6; `factors.py:256` clamps every band | `cb2[0]` whole vector | cap removed, explicit bands | palette check: 8 of 10 tints at 0.449999988, 2 at 0 → the ship value is 0.45, and 0.40 is one donor block's authored value | **MATCH** |

## 4. Corrections (for whoever edits the plans; this report changes nothing)

**C1 — colour report §2 and §7: the `0x83/0x7d/0x86` sentence.**
The effective colour is `base × Diffuse_Adjust`, not "through the project's linear→sRGB gain 3.4476":
`0.025787×2.2 = 0.056731`, `×2.0 = 0.051574`, `0.03×2 = 0.06`. And 0.056738 sRGB-encodes to
**0.2642 → byte 67 (0x43)**, while `0x83 = 131/255 = 0.5137` is `linear 0.2269 ≈ 4× 0.0567` — the
**RBM albedo byte** of `MODDING_PLAN.md:56`, a different quantity. This is `T2_TRANSLATION.md` C03
REFUTED, restated. Replacement wording: *"`base × Diffuse_Adjust` = [0.056738, 0.05158, 0.06] linear (sRGB 67/64/69); the shipped RBM albedo byte `0x7a757e` is the luma-matched palette solid, a different quantity (T-MA3 C03)."*

**C2 — colour report §3 table and paint plan §3 table (ch3): `Material3_Reflectivity` is 0.15 on 763.**
`COLOUR_PARAMS.md` §2 **row 6**: `Batmobile_V3_Mainbody_NEW_MIC` `Material3_Reflectivity` = **0.15**;
row 24 gives 0.5 on 767. The colour report's cell "(0.5 (763), 0.5 (767))" is wrong on the 763 half, and
the plan's ch3 row uses the **parent** value while its ch0 row uses the **nearest** value — the two
rows apply different inheritance rules. Under one rule the ch3 target is `0.04×0.15 = 0.0060`, its albedo
is sRGB **32** (not 39), and the "error 0" cell becomes +0.034 if 0.020 is kept. Fix: either state
"ch3 takes 0.5 from 767, a deliberate exception to nearest-wins", or move the row to 0.15 / 0.0060 / 32.

**C3 — paint plan §3 MK2 row: "0.2 would give 0.132".**
`0.04(1−0.2) + 0.65×0.2 = 0.162`. 0.132 = `0.04×0.8 + 0.5×0.2`, i.e. an albedo of 0.5, which is not the
0.65 the plan bakes at byte 211. Fix the cell to **0.162 (8.1×)** or change the MK2 albedo to 0.5 (byte 188)
and keep 0.132.

**C4 — clear coat 1.0 has no BmAK source.**
The colour report's `clear_coat` 1.0 comes from `COLOUR.md` §4, a **JC3** palette field. On the BmAK side
there is no clear-coat parameter; the nearest evidence is `Material3_BaseColour` black with
`Material3_Roughness` 0.02 (the lacquer channel). Label it *"JC3 convention, palette 1.000"* rather than
"decoded from BmAK", and note that `factors.py` sets `static.ClearCoat` from the presence of
`Normal_Map_Lacquer`, which the body material does **not** carry — so the plan's coat 1.0 is not reachable
by the current tool without a code change, and the plan does not say so.

**C5 — `Wetness_Refl_Fresnel` 0.6 → clearcoat 1.0.**
Two different BmAK numbers (`clear_coat` convention 1.0 and the Fresnel 0.6) land in one slot, and the
0.6→1.0 step has no arithmetic. The plan calls the wet composition UNKNOWN, which is honest, but the table
cell is labelled "closest" — it should be `ASSUMED`, with the +67 % visible. If the two must be
distinguished, the only spare lever is `cb6[4].z` `m_ClearCoatOverride` (a runtime override), and whether
the engine writes it is UNKNOWN (`CB0_SLOTS.md` §4).

**C6 — `m_Metallic` per-channel: the two reports disagree.**
Colour report §6 says `m_Metallic` "is one value for the whole block, not per channel"; the paint plan
writes `[0, 0, 1, 1]`. `CB0_SLOTS.md` §3 lists `cb2[1]` as a **16-byte float4** sourced from
`static_params[4..7]`, and `factors.py`'s `STATIC` list carries `Metallic` as a float4 — so four slots
**exist**. Whether the SHEX reads all four is UNKNOWN. Delete the "one value" parenthetical; keep
"four slots exist, channel use is UNKNOWN".

**C7 — `CLEARCOAT_SPECULAR_FRESNEL0` is not in the repo.**
Paint plan §3.4 names it as the F0 of the second lobe. A search over `Research/` returns **0** matches;
only `Tools/scripts/appearance_plan.py` mentions the wetness tunable. Mark the constant `UNSOURCED` or
drop the name and keep "second lobe, F0 fixed by the scene".

## 5. Bonus checks done in passing (not in the brief)

| claim | recomputed | verdict |
|---|---|---|
| channel-2 albedo `0.036` → sRGB 53 | 0.2091 ×255 = 53.3 | MATCH |
| channel-3 albedo `0.020` → sRGB 39 | 0.1517 ×255 = 38.7 | MATCH |
| edge `0.1` → 89, MK2 `0.65` → 211 | 89.0 / 210.8 | MATCH |
| aniso 8 % mixes `0.060/0.083/0.106` and `0.039/0.040/0.054` | `0.08·c + 0.92·base` = 0.0607/0.0824/0.1054 and 0.0394/0.0397/0.0539 | MATCH |
| aniso contrasts 0.51 / 0.134 | `0.972−0.462`, `0.33−0.196` | MATCH |
| `s1` amplitude 0.35 / 0.12 from those contrasts | no formula given | UNSOURCED (a chosen scale) |
| along/across gloss 0.75 / 0.45 from `1 − 0.25` / `1 − 0.55` | arithmetic right; 0.25 and 0.55 appear in no dump | UNSOURCED (chosen) |
| palette "0.45 on 8 of 10 tints" | `serpente_palette.xml`: 8 × 0.449999988, 2 × 0 | MATCH |
| budget: 3,953.6 → free 694.4 → +128 +512 → 54.4 KB | 4648−3953.6 = 694.4; 694.4−640 = 54.4; and the 28 converted `.ddsc` measured on `Builds/test-091/.../textures/batmobile` = **3,953.6 KiB** (37 files − 9 `solid_*` of 184 B) | MATCH (total now measured) |
| a 1024² BC5 normal "costs +768 KB" | 1024² = 1,048,576 B = 1024 KB; 512² = 256 KB; **delta 768 KB** | MATCH (delta from the existing map, correctly stated) |
| `0.6 × 0.6 × 1.6` alternative = 0.192, F0 0.00768 < dry 0.008 | `0.2×1.92 = 0.192`; `×0.04 = 0.00768` | MATCH |

## 6. What this audit could not check

1. ~~**The 28 `.ddsc` total of 3,953.6 KB**~~ — **closed by this audit:** the shipped `textures/batmobile`
   holds 37 `.ddsc` = 3955.2 KiB; the nine `solid_<rrggbb>.ddsc` placeholders are 184 B each (1.6 KiB), so
   the 28 converted = **3953.6 KiB**. The plan's total is exact (`T2_TRANSLATION.md` C02's 42 is an older tree).
   Remaining sub-question: whether the new body `s0` *replaces* the existing solid (see item 2).
2. **Whether `s0`'s 128 KB is an add or a replacement** — the body already has a generated solid
   `s0` on disk; if it is replaced the +128 KB is over-counted and free space is 182.4 KB, not 54.4.
   *Would settle:* the size of the existing body dif in `Builds/<latest>/textures/`.
3. **The meaning of `Material0_Reflectivity`** (F0? specular level? a blend weight?) — the value is
   decoded, the effect is not (`COLOUR_PARAMS.md` §6 item 6). Every F0 row inherits `0.04`.
4. **Gloss polarity** — `1 − roughness` is `factors.py`'s implementation and the plan's assumption, not a
   decoded fact (colour report §8 item 7). If the member is roughness, every gloss row inverts.
5. **The wet composition order** — the plan picks one of several; both are arithmetically checked here,
   neither is decoded.
6. **Whether clearcoat has a scene F0** — the named constant is absent from the repo (§4 C7).

## 7. Checks run for this report, and revert

| # | check | result |
|---|---|---|
| 1 | every BmAK value re-read at `COLOUR_PARAMS.md` row number / `SKINS.md:548` / `VALUES.json` | 1 mismatch found, at 763 `Material3_Reflectivity` (0.15, not 0.5) |
| 2 | build state re-read from `Working/Appearance/build_bud1/factors.json`, body + arches | gloss 0.4, metallic `[0,0,1,0]`, coat 0, `s0` 122/117/126 — plan's table is exact |
| 3 | sRGB transfer recomputed for every albedo byte (base, 0.036, 0.020, 0.1, 0.65, effective) | 45/48, 53, 39, 89, 211, 67/64/69 |
| 4 | `F0 = 0.04(1−m) + albedo·m` recomputed for all 7 plan rows | 6 match, MK2 0.132→0.162 |
| 5 | gloss chain recomputed for ch0/1/2/3 and the wet state | 0.60, 0.85, 0.98, 0.70, 0.8875, 0.985 |
| 6 | palette 0.45 count and `GLOSS_CAP` clamp read at `factors.py:256` / `VALUES.json:5` | both confirmed |

No game process was started; no bake, `.rbm` re-encode, texture or build was written; neither audited
plan was edited. **Revert:** delete this file.
