# Dropped appearance classes, part B — D7, D8, D10, D11, D12 and the bakes P1/P2/P3

Card: appearance, dropped/baked classes, **part B**. Plan + build step only. Nothing was baked, no
`.rbm`, texture, spec, ledger or `Working/Appearance/progress.md` was written.

Part A (`tmp/freebuff/reports/app-dropped-classes-plans-a.md`) covers D1–D6 and D9. This file covers
the eight classes it does not: **D7 (8 rows), D8 (7), D10 (3), D11 (9), D12 (1), P1 (6), P2 (15),
P3 (2)** = 51 rows. Row counts are read from `Working/Appearance/appearance_plan.json`
`.components[rule]` [decoded], and they match the per-class lists in `progress.md`.

Labels used on **every** row below: **decoded** = a cited file carries the bytes/value; **derived** =
rule + the decoded inputs with the arithmetic shown; **UNKNOWN** = what was searched and the file that
would settle it.

---

## 0. Change statement (AGENTS.md)

| item | value |
|---|---|
| intended change | add one report: D7, D8, D10, D11, D12, P1, P2, P3 — each with the closest JC3 mechanism, the build step, and a label on every line |
| file | `tmp/freebuff/reports/appearance-drops-b.md` (this file) |
| why this file | the brief names it; all report output of this card lives under `tmp/freebuff/reports/`, and every evidence file it reads is read-only |
| reverted by | deleting this one file. No edit to `Working/Appearance/progress.md`, `appearance_plan.json`, `APPEARANCE_PLAN.md`, `TEXTURE_BUILD_PLAN.*`, `Tools/`, `Research/`, `Builds/`; no texture converted, no `.rbm` encoded, no game launched |

---

## 1. The eight classes at a glance

| class | rows | `progress.md` reason (verbatim) | evidence file the row rests on | closest JC3 mechanism | build step | verdict |
|---|---:|---|---|---|---|---|
| D7 | 8 | "JC3 weather" | `app-wetness-and-rain.md` §1, §4.1–§4.2 [decoded] | scene `TEST_WETNESS_FACTOR` @104 + `t40`/`t41` masks; **no** paint member | static streak bake into `s1` at the decoded axis/tiling; scene value is not ours | closest + gap, bake |
| D8 | 7 | "JC3 weather/wetness system" | `app-wetness-and-rain.md` §2.2–§4.2 [decoded] | `Window` `s9`/`t40`, `GeneralMkIII` `t41`; paint keeps the scene factor | `Rain_Constant` = identity (no write); fresnel/roughness static or routed | closest + gap, route |
| D10 | 3 | "colour ramp lookup (and the ramp files are missing-on-disk)" | `app-colour-ramp-locate.md` §6 + `app-colour-ramp-textures.md` §2/§3/§6 [decoded] | `m_TintColor` `cb6[0..2]` @0/16/32 replaces the sampler | write the decoded plateau as the tint; remove the ×3.4476 albedo gain | **the row's reason is false**; route, not drop |
| D11 | 9 | "editor/fake helper or smudge overlay" | `app-cockpit-interior-materials.md` row 14 + `COCKPIT.md:34`; `SKINS.md:240` [decoded] | no member; the one rendered value (`glass_smudges` 0.2) lands in `Window` `t0` alpha | bake 0.2 into the glass alpha; the 8 `Fake`/`fake` rows write nothing | 1 of 9 has a carrier |
| D12 | 1 | "editor helper" | `SKINS.md:239` (`Art Light Mul 1234/5678`) + `LIGHTS_FORENSICS.md:158` [decoded] | `CarLight` block + `*_lights.vmodc` (R1's carrier) | apply the art multiplier as a gain on the donor `CarLight` emissive — **not authorable** | UNKNOWN (block params undecoded) |
| P1 | 6 | "tiling micro-detail (no CarPaintMM detail slot; could be baked into s1)" | `app-microdetail-bake-plan.md` §3.2, §4.3 [decoded] | `CarPaintMM.s1` normal, RNM bake | bake `Batmobile_Microdetail` into `s1` at `T=15`; 4 of 6 tiles absent | bake, 1 of 6 executable today |
| P2 | 15 | "micro-detail tiling size" | `app-microdetail-bake-plan.md` §3.1, §4.2 [decoded] | the `s1` bake's UV multiplier (no block input) | feed `T` into the P1 bake; unit UNKNOWN picks 15 vs `L_uv/0.15` | bake, one number |
| P3 | 2 | "micro-detail → roughness modulation" | `app-microdetail-bake-plan.md` §4.4 [decoded] | `m_SpecularGloss` float4 (mean only) | `gloss' = gloss·(1 − c·s̄·r_k)`; body has no value | bake the mean, record the per-pixel gap |

**One-line reading.** Six of the eight classes are correctly "no member" but three of those still have
a real build step (D7's streak bake, D10's tint, D11's alpha); D10's stated reason is factually wrong
in `progress.md` and `APPEARANCE_PLAN.md`; and P1 is only one-sixth executable because four of its six
source tiles are not in the grab.

---

## 2. What each row actually cites

`progress.md` gives a reason per row but **no file path**. The path comes from the record that
classifies the row:

| source | what it supplies | label |
|---|---|---|
| `Working/Appearance/appearance_plan.json` `.rules[]` | id, `why`, `action`, `target`, `owner`, `note` — the text `progress.md` mirrors | decoded (file) |
| `Working/Appearance/TEXTURE_BUILD_PLAN.json` `.evidence[*]` | explicit per-rule evidence map; **absent for D7, D8, D11, D12, P2, P3** | decoded |
| `appearance_plan.json` D8 `note` / D10 `note` | names `tmp/freebuff/reports/app-wetness-and-rain.md`, `app-colour-ramp-textures.md` | decoded |
| `app-microdetail-bake-plan.md` | the P1/P2/P3 report, cited by `TEXTURE_BUILD_PLAN.json` `.evidence.P1` | decoded |

So for D7, D11, D12 and P2/P3 the report named below is the **only** project file that decodes the
values; it is named in the class section. D7 has no dedicated report — its values are in
`app-wetness-and-rain.md` §4.1, which lists the exact `Batman_Rain_Direction` / `Rain_Size_Multiplier`
rows this class contains [decoded]. This is recorded rather than papered over: the brief's "the
evidence file that row cites" resolves to that report for D7, and to no file at all for the eight
`Fake`/`fake` D11 rows (§7).

---

## 3. D7 — rain direction and rain size (8 rows)

### 3.1 The rows and their decoded values

| # | component (from `appearance_plan.json`) | value | label |
|---:|---|---|---|
| 1 | `Batmobile_V3_Mainbody_NEW_MIC:vec:Batman_Rain_Direction` | `[0, 0, -1, 0]` | decoded — `app-wetness-and-rain.md` §4.1, from `SKINS.md` §§ slots 3–13 / `VEC_DEFAULTS.md` |
| 2 | `Batmobile_V3_Mainbody_NEW_MIC:vec:Rain_Size_Multiplier` | `[2.5, 2, 0, 1]` | decoded — same table |
| 3 | `Batmobile_V3_Turret_NEW_MIC:vec:Batman_Rain_Direction` | `[0, 0, -1, 0]` | decoded |
| 4 | `Batmobile_V3_Turret_NEW_MIC:vec:Rain_Size_Multiplier` | `[2.5, 2, 0, 1]` | decoded |
| 5 | `Batmobile_V3_Undercarriage_NEW_MIC:vec:Batman_Rain_Direction` | `[0, 0, -1, 0]` | decoded |
| 6 | `Batmobile_V3_Undercarriage_NEW_MIC:vec:Rain_Size_Multiplier` | `[2.5, 2, 0, 1]` | decoded |
| 7 | `Batmobile_V3_WheelArchs_NEW_MIC:vec:Batman_Rain_Direction` | `[0, 0, -1, 0]` | decoded |
| 8 | `Batmobile_V3_WheelArchs_NEW_MIC:vec:Rain_Size_Multiplier` | `[2.5, 2, 0, 1]` | decoded |

Variants exist on other skins (`[2,2,0,1]`, `[1,2,0,1]` for size; `[0,0,0,0]` on Body_NoRain/Tyre,
`[0,0,1,0]` for glass) — same table [decoded].

### 3.2 Closest JC3 mechanism

| carrier | what it gives | gap | label |
|---|---|---|---|
| `float TEST_WETNESS_FACTOR` @104 in `deferred_clusteredlightingtunable` | the only wetness strength in the engine, scene-wide | not a material input, not settable by a mod, **value UNKNOWN** | decoded (layout); value UNKNOWN |
| `CarPaintMM` | **nothing** — 0 of 13 headers declare a rain member or rain sampler | direction and tiling have no slot | decoded |
| `Window` `s9 RainOccluderSampler` / `t40` | per-material rain *mask* (on the glass only, 4 of 4 headers) | masks, not direction/tiling | decoded |
| `GeneralMkIII` `t40` + `t41 WetnessNoiseTexture` | per-material mask **and** a UV-tiled noise (55 of 156 headers) | the tiling is in the shader body, no settable member; block swap needs the undecoded payload | decoded (slots) / UNKNOWN (payload) |

### 3.3 The build step that closes the gap

| step | what to write | numbers | label |
|---|---|---|---|
| D7-A | bake a directional streak into the body-family `s1` normal, axis = the decoded direction | world `[0,0,-1]` → streak runs vertically in world space; on the mesh UV it is the UV-space projection of that axis, per chart | decoded value, derived projection |
| D7-B | tile the streak at the decoded size | `[2.5, 2]` repeats on U,V (both non-zero components); the `0`/`1` components are unused/neutral | derived |
| D7-C | keep `m_SpecularGloss` at the dry authored value **or** halve it if the build ships a fixed wet state (D8's `RainRoughnessMul 0.5`) | 0.5× | derived from a decoded D8 value |
| D7-D | do **not** attempt to set the scene factor; record that the body is wetted exactly as a vanilla car | — | decoded (scene is engine-global) |

Streak amplitude is UNKNOWN: no BmAK scalar states it (the MIC carries direction and size only)
[decoded absence]. Settled by `app-microdetail-bake-plan.md`'s C7 blind A/B, or by reading the
master's `Batman_Rain_*` expression defaults in `Research/BatmobileGrab/COLOUR_FUNCTIONS.json`
(no value column today).

---

## 4. D8 — wetness response (7 rows; `route`, not `drop`)

### 4.1 The rows and their decoded values

| # | component | value | label |
|---:|---|---|---|
| 1 | `Batmobile_V3_Emissive:sc:Rain_Constant` | `1` | decoded — `app-wetness-and-rain.md` §4.1 (7 occurrences, all `1`) |
| 2 | `Batmobile_V3_Mainbody_NEW_MIC:sc:Wetness_Refl_Fresnel` | `0.6` | decoded |
| 3 | `Batmobile_V3_Turret_NEW_MIC:sc:Wetness_Refl_Fresnel` | `0.6` | decoded |
| 4 | `Batmobile_V3_Tyre_V2_MIC:sc:RainRoughnessMul` | `0.5` | decoded |
| 5 | `Batmobile_V3_Tyre_V2_MIC:sc:Rain_Constant` | `1` | decoded |
| 6 | `Batmobile_V3_Undercarriage_NEW_MIC:sc:Wetness_Refl_Fresnel` | `0.6` | decoded |
| 7 | `Batmobile_V3_WheelArchs_NEW_MIC:sc:Wetness_Refl_Fresnel` | `0.6` | decoded |

**Conflict with the plan's own note.** `appearance_plan.json` `.rules[D8].note` and
`APPEARANCE_PLAN.md:111` state `RainReflectivityMul 1.6` and `RainRoughnessMul 0.75`; the decode they
point at (`app-wetness-and-rain.md` §4.1) reads **`RainReflectivityMul = 2`** and
**`RainRoughnessMul = 0.5`** [decoded]. The build steps below use the decoded values; the note text is
wrong by 0.4 and 0.25 respectively. `RainReflectivityMul` is not a D8 row at all — `progress.md`
classifies it as `route (D2)`.

### 4.2 Closest mechanism and gap

`Rain_Constant` is `1` on every material that carries it, so it is a **neutral enable normaliser**, not
a look: mapping it to the scene factor introduces no numeric error [derived from the all-1 census].
The paint block cannot opt in or out of wetness at all (0 of 13 headers) [decoded]; the per-material
lever exists only on `Window` (`s9`/`t40`, 4 of 4) and `GeneralMkIII` (`t40`/`t41`, 55 of 156)
[decoded].

### 4.3 The build step

| step | write | numbers | label |
|---|---|---|---|
| D8-A | `Rain_Constant` → no write; the scene factor carries it | identity | decoded (all values are 1) |
| D8-B | `Wetness_Refl_Fresnel` 0.6 on 4 materials → static `m_Metallic` per channel, or `GeneralMkIII.EnableVariableDialecticSpecFresnel` @16 | 0.6 as a fresnel blend | decoded value; member semantics UNKNOWN |
| D8-C | `RainRoughnessMul` 0.5 (tyre) → `m_SpecularGloss` × 0.5, only in a fixed-wet build | ×0.5 | derived |
| D8-D | bind `RainOccluderTexture` `t40` on the `Window` block (glass already supports it) | authored mask | decoded (slot) / UNKNOWN (content) |

The wet-only override cannot be carried: whatever is written is permanent, which is the gap the row
already states.

---

## 5. D10 — colour ramp lookup (3 rows)

### 5.1 The rows, and why the stated reason is false

`progress.md` and `APPEARANCE_PLAN.md:31` say the ramps are "missing-on-disk" and therefore "can be
neither converted nor baked". `app-colour-ramp-locate.md` §6 decodes all three as real `Texture2D`
exports and `app-colour-ramp-textures.md` decodes their pixels [decoded]:

| # | ramp | where it is | pixels | label |
|---:|---|---|---|---|
| 1 | `Batman_BM3_V2_Lacquered_Underlayer_Ramp` | `BmGame` #176227 / `Startup` #171638, 1,894 B | 64×512 DXT1, 129 unique rows | decoded |
| 2 | `Batman_BM3_V2_Leather_Ramp` | 15 exports (e.g. `Playable_Batmobile_SF` #5399), 1,894 B each | 64×512 DXT1, 183 unique rows | decoded |
| 3 | `Batmobile_V3_Body_ColourRamp` | `BmGame` #176233, 1,922 B | 64×512 DXT1, 151 unique rows | decoded |

The Batmobile packages bind them as **imports** (`Playable_Batmobile_SF` #-588, #-594), which is why a
search of the Batmobile packages alone reads as a miss [decoded: `app-colour-ramp-locate.md` §1, §3].

### 5.2 What the pixels say

| ramp | sampled value that matters | source | label |
|---|---|---|---|
| Lacquered | rows 256–511 = `sRGB (49,48,49)` = **0.0307, 0.0294, 0.0307 linear**; plateau is 56 % of the ramp | `app-colour-ramp-textures.md` §2 | decoded |
| Body_ColourRamp | rows 320–511 = `(32,33,32)` = **0.0145, 0.0145, 0.0177** | `app-colour-ramp-textures.md` §3.1 | decoded |
| Leather | luminance only, rows `255 → 238 → 204 → 179 → 114 → 57 → 30 → 27 → 26 → 239` | `app-colour-ramp-textures.md` §3.3 | decoded |

The body's authored constant agrees with the plateau to 3–4/255: `Material0_BaseColour`
`[0.025787, 0.025787, 0.03]` = sRGB (45,45,48) [decoded, `app-colour-ramp-textures.md` §5]. The build
ships `s0 = [0.4784, 0.4588, 0.4941]`, a ×3.4476 gain — ≈6.3× the plateau [decoded: `factors.json`].

### 5.3 Closest JC3 mechanism and build step

`CarPaintMM` has no ramp sampler; the tint is `m_TintColorR/G/B` at `cb6[0..2]` = block bytes
0/16/32, written from block object `+0x168 → +0x178 → +0x188` [decoded: `app-colour-ramp-textures.md`
§6, citing `Research/JC3Grab/TINT_WRITE.md`].

| step | write | numbers | label |
|---|---|---|---|
| D10-A | body/cockpit/disc blocks: `m_TintColor` = the Lacquered plateau | `(0.0307, 0.0294, 0.0307)` = 0x31/0x30/0x31 | decoded plateau; assignment derived |
| D10-B | body `s0`: drop the ×3.4476 gain, write `Material0_BaseColour` | `(0.0258, 0.0258, 0.0300)`; if `Diffuse_Adjust [2.2,2,2]` is kept, `(0.0567, 0.0516, 0.0600)` = 0x43/0x41/0x45 | decoded constants, derived product |
| D10-C | Emissive: `m_Emissive` (`cb2[3]`) carries the Body_ColourRamp plateau as its colour, mask stays `Batmobile_V3_Wheel_E` | `(0.0145, 0.0145, 0.0177)` | decoded plateau; assignment derived |
| D10-D | seat: bake the Leather ramp's luminance into `s0` once, keep `m_TintColor` at 1,1,1 so the bake is not re-tinted | mean of the decoded row sequence | decoded rows, derived mean |
| D10-E | the *per-pixel* lookup is lost — one sampled value per block | n/a | UNKNOWN (index→V mapping; `Coordinates` is expression 0, graph stripped 944/944) |

D10-E is the honest residue: the sampler cannot be carried, only a flat colour. The row should move
from `drop / source absent` to `route / no ramp sampler`, which is what `app-colour-ramp-locate.md` §6
already recommends.

---

## 6. D11 — `Fake` / `fake` scalars and `glass_smudges` (9 rows)

### 6.1 The rows

| # | component | what the grab holds | label |
|---:|---|---|---|
| 1–8 | `BatmobileV3_Cockpit_Seat:sc:Fake`, `:sc:fake`; `Batmobile_V3_Cockpit_MIC:sc:Fake`, `:sc:fake`; `Batmobile_V3_Discbreak_MIC:sc:Fake`, `:sc:fake`; `Batmobile_V3_Emissive:sc:Fake`, `:sc:fake` | **no value found** — no object in `objects.jsonl` carries a `NameProperty` of exactly `Fake` or `fake`; `SKINS.md:240`/`:278`/`:286`/`:298` list only `Fake Aniso Brightness 1/2` and `fake aniso orientation` / `uv magnitude` / `uv shift` | UNKNOWN |
| 9 | `Batmobile_V3_Glass_INST:sc:glass_smudges` | `0.2` | decoded — `COCKPIT.md:34`, `MATERIALS.md:972`, `SKINS.md:197` |

Searches run for the eight: `"Fake"` / `"fake"` over `Research/BatmobileGrab/objects.jsonl` (177 k
objects, **0** exact-name hits), over `Working/Appearance/grab/**/*.txt` (**0**), over
`Research/BatmobileGrab/*.json` and `*.md` (**0**); the only near names are the aniso-fake family,
which is D4's subject and already closed in `app-anisotropic-highlights.md` [decoded search result].

So the most likely reading is **derived**: `Fake`/`fake` are the aniso-fake scalars under a
name-normalised key produced by `Tools/scripts/factors.py`, not a second rendered input. That reading
is not proven; it is marked UNKNOWN and the settler is `Tools/scripts/factors.py` (the resolver that
emitted the key) plus a re-dump of `Playable_Batmobile_SF/MaterialInstanceConstant/*.props.txt`
looking for `ParameterName = Fake`.

### 6.2 Closest JC3 mechanism and build step

| step | write | numbers | label |
|---|---|---|---|
| D11-A | the eight `Fake`/`fake` rows: **no build step** — they resolve to no decoded value, so writing anything would be invention | — | UNKNOWN (value), settled as above |
| D11-B | `glass_smudges` 0.2 → bake a smudge mask into the glass `t0` alpha; `Window` alpha is the slot (`Alpha` / `MinAlpha`) | `alpha' = alpha · (1 − 0.2 · smudge)`, smudge ∈ [0,1] | decoded value; carrier decoded (`app-glass-layers.md`); mask UNKNOWN |
| D11-C | the smudge mask itself: author a 512² greyscale mask, or derive it from `Batmobile_V3_Glass_A` (the OpacityMap) if its non-uniform area is the smudge zone | 0.2 strength cap | derived / UNKNOWN |

Which texture carries the smudge pattern is UNKNOWN: `Batmobile_V2_Textures_NEW.Batmobile_Glass`
binds `Glass_A` (opacity), `Glass_N`, `Glass_S` (mask R=reflect, G=rough, B=normal-fix); no smudge
input is named [decoded: `MATERIALS.md:972`]. Settled by the master's expression list in
`Research/BatmobileGrab/COLOUR_FUNCTIONS.json` (`glass_smudges` appears at line 663, parameter only).

---

## 7. D12 — `vec:Art` (1 row)

| item | value | label |
|---|---|---|
| the row | `Batmobile_V3_Emissive:vec:Art` | decoded (plan) |
| any parameter named exactly `Art` | **0** in `objects.jsonl`, the grab props dumps, `COLOUR_PARAMS.md/json` | UNKNOWN (searched) |
| nearest decoded name | `Art Light Mul 1234 = [90, 1, 90, 150]`, `Art Light Mul 5678 = [150, 30, 1, 30]` on `Batmobile_V3_Emissive` | decoded — `SKINS.md:239` |
| their master defaults | `[1, 1, 1, 1]` on `Batmobile_V3_Body_NoRain_MAT` and `Batmobile_Worn` | decoded — `COLOUR_PARAMS.md:149-150`, `VEC_DEFAULTS.md:73-74` |
| the runtime group multipliers beside them | `LightGroup1234 = [1, 1, 1, 1.5]`, `LightGroup5678 = [1.5, 1, 1, 1]` | decoded — `SKINS.md:239` |
| effective art gain, if component = group | `(90, 1, 90, 225)` for groups 1–4 | derived (component-wise product; the component→group map is derived from the `1234` name, not decoded) |

**Closest JC3 mechanism**: the `CarLight` block plus the `*_lights.vmodc` entry — exactly R1's carrier
(`appearance_plan.json` `.rules[R1].target`), 11,367 blocks in 220 vehicles [decoded:
`LIGHTS_FORENSICS.md:18`].

**Build step**: apply the decoded gain to the donor `CarLight` block's emissive so groups 3 and 4
dominate as they do in BmAK (`90` and `225` against `1` for group 2). **It cannot be written from
numbers**: `CarLight`'s material/emissive parameters are not decoded and the build copies a donor block
byte-exact [decoded: `LIGHTS_FORENSICS.md:158`, MODLOG §102d]. So the executable form of the step is
"choose a donor `CarLight` block whose emissive ratio already matches `90 : 1 : 90 : 225`, or wait for
the `CarLight` parameter decode". UNKNOWN, settled by MODLOG §102d / `LIGHTS_FORENSICS.md`.

---

## 8. P1 — the six micro-detail textures (bake)

### 8.1 Source texture → JC3 slot

| # | source texture | present in grab | JC3 slot that receives it | label |
|---:|---|---|---|---|
| 1 | `Batmobile_Microdetail` 1024² PF_DXT1 | **yes** | `CarPaintMM` `s1` NormalMap, RNM blend, channel 0, weight 1 | decoded |
| 2 | `Batmobile_Micropattern_A` | **no** | `s1` channel 1 (Emissive only) | UNKNOWN (absent; re-grab settles) |
| 3 | `Batmobile_Micropattern_A_Normal` | **no** | `s1`, Material3 detail (body family + Emissive) | UNKNOWN (absent) |
| 4 | `Batmobile_Micropattern_B` | **no** | `s0` albedo multiply + `s1` slope (Emissive base) | UNKNOWN (absent) |
| 5 | `Batmobile_Micropattern_C` | **no** | `s1` channels 2/3 (Cockpit_MIC, Emissive) | UNKNOWN (absent) |
| 6 | `neutral_normal` | n/a — a value, not an asset | nothing: it is a flat normal constant the material points at | decoded |

`Micropattern_D_N` / `E_N` are on disk but bound by **no** V2 MIC, so using them would invent an
assignment [decoded: `app-microdetail-bake-plan.md` §3.2].

### 8.2 Build step

| step | content | numbers | label |
|---|---|---|---|
| P1-A | RNM bake of `Batmobile_Microdetail` into the body family's `s1` | `T = 15`, weight `α₀ = 1`, `k = 1.0`, per LOD, BC5 linear | decoded inputs; `k` an assumption |
| P1-B | leave channels 1–3 unwritten and log them as blocked | 0 of 4 tiles present | decoded |
| P1-C | `neutral_normal` writes nothing | n/a | decoded |
| P1-D | the only dedicated detail sampler in JC3 is `CarLight.s4 NormalDetailMap` — a light-mesh block, `cb2 float4 MaterialConsts[4]` undecoded; not a paint carrier | — | decoded |

Bake geometry: `N = normalize(vec3(N₀.xy + t.xy·w, N₀.z))` with `t` the reoriented tile and `w` as
above [derived: `app-microdetail-bake-plan.md` §4.3]. Cost: body `s1` is re-baked in place, so no new
texture slot and no new file; the allocator must re-run with the new sizes [decoded §4.5].

---

## 9. P2 — the fifteen micro-detail tiling sizes (bake)

| material | parameter | value | label |
|---|---|---|---:|
| `Batmobile_V3_Cockpit_MIC` | `BaseMaterial_Microdetail_Size` | 45 | decoded — `app-microdetail-bake-plan.md` §3.1 |
| | `Material1_Microdetail_Size` | 120 | decoded |
| | `Material2_Microdetail_Size` | 30 | decoded |
| | `Material3_Microdetail_Size` | 30 | decoded |
| `Batmobile_V3_Emissive` | `Material1_Microdetail_Size` | 250 | decoded |
| | `Material2_Microdetail_Size` | 30 | decoded |
| | `Material3_Microdetail_Size` | 30 | decoded |
| `Batmobile_V3_Mainbody_NEW_MIC` | `MicroDetail_size` / `MicroDetail_Material3_Size` | 15 / 250 | decoded |
| `Batmobile_V3_Turret_NEW_MIC` | same | 15 / 250 | decoded |
| `Batmobile_V3_Undercarriage_NEW_MIC` | same | 15 / 250 | decoded |
| `Batmobile_V3_WheelArchs_NEW_MIC` | same | 15 / 250 | decoded |

**JC3 slot**: none — the value is the **UV multiplier of the P1 bake**, not a block input; that is
`appearance_plan.json` `.rules[P2].target` ("s1 Normal UV scale at bake time") [decoded].

**Build step**:

```
T_desired = T                 # reading (a): repeats per UV 0..1
T_desired = L_uv / (T/100)    # reading (b): T is a tile size in cm
T_eff     = max(1, round(T_desired))   # integer, or the tile seam shows
```

[derived]. **Unit is UNKNOWN** — 15/20/30/45/120/250 is consistent with both readings and no file
states it. Settled by C2, the repeat-frequency peak (15 repeats on 1024 px → `f = 0.0146` cycles/texel,
expected within ±1 bin), or by C7's blind A/B [decoded: §5]. Note the turret value: `MATERIALS.md`
quotes 20, but the shipped `Batmobile_V3_Turret_NEW_MIC` dumps **15.0**; the 20 belongs to the
Jokerfied turret — build from the MIC chain [decoded: §3.1].

---

## 10. P3 — `underlayer_Detail_to_Roughness` (bake, 2 rows)

| # | component | value | label |
|---:|---|---|---|
| 1 | `Batmobile_V3_Cockpit_MIC:vec:underlayer_Detail_to_Roughness` | `[0.8, 0.5, 0.1, 1.0]` | decoded — `app-microdetail-bake-plan.md` §3.1, `SKINS.md:277` |
| 2 | `Batmobile_V3_Emissive:vec:underlayer_Detail_to_Roughness` | `[0, 0.44, 0.44, 1.0]` | decoded — same |

**Closest JC3 mechanism**: `m_SpecularGloss` float4 — four bands, i.e. one gloss per material channel,
with no per-pixel roughness on `CarPaintMM` [decoded].

**Build step**: a normal map cannot carry a gloss scalar, so the row's own wording ("folded into the
baked normal") is wrong [derived]. What the pipeline can do:

| step | content | numbers | label |
|---|---|---|---|
| P3-A | measure the tile's mean slope `s̄ = mean(1 − N₁.z)` at `T_eff` | per material | derived |
| P3-B | fold it into the gloss **once**: `gloss' = gloss · (1 − c · s̄ · r_k)`, `r_k` the decoded vector | cockpit `r = 0.8/0.5/0.1/1.0`; emissive `0/0.44/0.44/1.0` | decoded `r`, derived formula |
| P3-C | the body family has **no** value → no coupling at all from this rule | 0 | decoded (absent in the MICs) |
| P3-D | record the per-pixel part as a gap; the exact route is `GeneralMkIII.Gloss1Map` | 4-band ceiling | decoded |

`c` is a single new constant, **UNKNOWN** — pass band: mean gloss change ≤ 0.01 between before and
after (C5), and `c` printed in the build log [decoded: §5]. Settled by that measurement, not by a file.

---

## 11. Conflicts found while checking the rows (reported, files not bent)

| # | what `progress.md` / the plan says | what the cited evidence says | label |
|---:|---|---|---|
| 1 | D10: ramps are "missing-on-disk", "can be neither converted nor baked" (`APPEARANCE_PLAN.md:31`, `:163`) | all three decode as `Texture2D` exports; 1,894 / 1,894 / 1,922 B, 64×512 DXT1 | decoded — `app-colour-ramp-locate.md` §6 |
| 2 | D10 `note`: "the two ramp reports … do not exist on disk" | both exist (`app-colour-ramp-textures.md`, `app-colour-ramp-locate.md`); `ramp-names-quick-search.md` does not | decoded |
| 3 | D8 `note`: `RainReflectivityMul 1.6`, `RainRoughnessMul 0.75` | decoded values are **2** and **0.5** | decoded — `app-wetness-and-rain.md` §4.1 |
| 4 | D8 `note` lists `RainReflectivityMul` as a D8 row | `progress.md` classifies it `route (D2)`; D8 has 7 rows, not 8 | decoded |
| 5 | D11: "editor/fake helper" for 8 rows | no value exists under those names; the nearest family is the aniso-fake scalars (D4) | UNKNOWN |
| 6 | P3: "folded into the baked normal's effect on the gloss" | a normal map carries no gloss; the mean-fold formula above is the honest form | derived |

None of these was edited in place — `progress.md`, `appearance_plan.json` and `APPEARANCE_PLAN.md`
keep their original mtimes.

---

## 12. Every UNKNOWN in this file, with its settler

| class | unknown | file that settles it |
|---|---|---|
| D7 | streak amplitude for the rain-direction bake | BmAK master expression defaults (`Research/BatmobileGrab/COLOUR_FUNCTIONS.json`) or `app-microdetail-bake-plan.md` C7 |
| D7, D8 | value of `TEST_WETNESS_FACTOR`; whether the paint shader reads it | lighting-tuning defaults / a runtime constant dump — not in the grab |
| D8 | what `t40` / `t41` encode (channels, UV convention) | a `.ddsc` decoder for the occluder maps (G3-12 open item) |
| D8 | whether `EnableVariableDialecticSpecFresnel` is the wet-fresnel switch | decompiled `GeneralMkIII` DXBC; `Research/JC3Grab/` has layout only |
| D10 | index → V mapping (which paint index lands on the plateau) | stripped operator graph; `FunctionExpressions` 944 slots, 0 non-zero — needs the uncooked master |
| D11 | value/identity of the 8 `Fake`/`fake` scalars | `Tools/scripts/factors.py` + re-dump of `Playable_Batmobile_SF/MaterialInstanceConstant/*.props.txt` |
| D11 | which texture carries the glass smudges | `COLOUR_FUNCTIONS.json` master expression list for `glass_smudges` |
| D12 | `CarLight` block emissive parameters | MODLOG §102d decode; `Research/JC3Grab/LIGHTS_FORENSICS.md:158` |
| P1 | 4 of 6 source tiles (`Micropattern_A`, `_A_Normal`, `_B`, `_C`) | a re-grab of those `Texture2D` objects (115-file grab today) |
| P1 | normal strength `k` (assumed 1.0) | no scalar in any MIC; a blind A/B or the master graph |
| P2 | unit of `MicroDetail_size` (repeats vs cm) | C2 repeat-frequency peak, `app-microdetail-bake-plan.md` §5 |
| P2, P1 | UV set (`2nd_or_3rd_UV_Ch`) | the master's expression defaults; our UV2 is a Serpente nearest-vertex copy (MODLOG §77) |
| P3 | coupling constant `c` | C5 measurement (`mean(gloss)` within 0.01), printed in the build log |
| P3 | per-pixel roughness on paint | `GeneralMkIII.Gloss1Map` (needs the block serialiser, G3-04e) |

---

## 13. Checks run, and what was left untouched

| # | check | result |
|---:|---|---|
| 1 | row counts per class from `appearance_plan.json` | D7 8, D8 7, D10 3, D11 9, D12 1, P1 6, P2 15, P3 2 = **51** — matches the per-class lists in `progress.md` |
| 2 | exact-name search for `Fake` / `fake` / `Art` over `objects.jsonl` (177 k objects) | 0 hits (only `glass_smudges` ×4) |
| 3 | same over `Working/Appearance/grab/**/*.txt` | 0 hits; only `Art Light Mul 1234/5678` |
| 4 | `factors.json` (`build_bud1`, `build_parts`) keys | no `Fake` / `fake` / `Art` key in either |
| 5 | ramp exports re-read | `app-colour-ramp-locate.md` §6, three exports with sizes |
| 6 | D8 note vs decode | two mismatches found and listed in §11 (1.6→2, 0.75→0.5) |
| 7 | `progress.md` mtime, and the three plan files | unchanged; read-only for this card |
| 8 | game / build | nothing launched, no `.rbm`, texture or archive written |

Untouched by this report: `Working/Appearance/progress.md`, `Working/Appearance/appearance_plan.json`,
`Working/Appearance/APPEARANCE_PLAN.md`, `Working/Appearance/TEXTURE_BUILD_PLAN.json`,
`Research/**`, `Tools/**`, `Builds/**`, and every report cited above.
