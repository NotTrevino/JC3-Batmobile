# KEEP-AUDIT — materials and textures: T-MA1…T-MA7 against `progress.md` and the build tree

Card: TRANSLATE, materials/textures (doc `T-2b`). **Audit only — no build, no edit to
`T_ROWS.jsonl`, no texture baked, no install, no game launch.** Classes: **decoded** (a file carries
it and a project tool reads it), **derived** (arithmetic), **MEASURED** (decoded here, command in §10),
**INFERRED**, **UNKNOWN**.

## 0. Change statement (AGENTS.md)

| item | value |
|---|---|
| intended change | add one report: per-row verdict with numbers, the delivered-vs-authored comparison, the open classes |
| file | `tmp/freebuff/reports/keep-audit-materials-textures.md` (this file) |
| why this file | the brief names it; reports of this wave live under `tmp/freebuff/reports/`, all inputs read-only |
| reverted by | deleting this file. Nothing else was written |

---

## 1. Verdicts

**All seven are COMPROMISE.** Two of them (T-MA3, T-MA4) carry a number that is contradicted by the
project's own `VALUES.json`/palette; one (T-MA2) names a source texture that was never in the grab and
was never shipped; one (T-MA1) has block totals that do not match the tree.

| row | what the row claims | what the tree shows (MEASURED) | BmAK's number | verdict |
|---|---|---|---|---|
| **T-MA1** | 17 blocks/LOD (16 `CarPaintMM` + 1 `Window`); 200 `+` 35 across 35 meshes | body LOD1–5 = **17 each** (16+1) ✓; wheels = **5 each** (4+1) → whole car **185 `CarPaintMM` + 25 `Window` = 210 blocks**, not 235 | 19 slots / 13 instances | **COMPROMISE** — carrier exact, totals 25 blocks high, and 19 slots ≠ 17 body blocks unexplained |
| **T-MA2** | body albedo `NEW_Batmobile_V2_BODY_D` 4096×2048, "identity (DDS, sRGB)", 28 textures | **no body albedo texture shipped** — the body's `s0` is a **solid colour**; the grab has no `NEW_Batmobile_V2_BODY_D`; largest shipped albedo **1024²**; **21** Batmobile `.ddsc` per build | body albedo 4096×2048 (8.4 Mpx) | **COMPROMISE** — the biggest map on the car is absent, replaced by one RGB constant |
| **T-MA3** | authored `[0.02579, 0.02579, 0.03]`, ×3.4476 → "effective `[0.0567, 0.0516, 0.06]` (albedo byte 0x83/0x7d/0x86)" | floats written **0.4784 / 0.4588 / 0.4941 sRGB** (bytes **0x7a/0x75/0x7e**) = **0.1946/0.1779/0.2086 linear** = **3.44× BmAK's effective colour**; the row's own 0.0567 is the *pre-gain* value, byte `0x83` a third number | base 0.02579/0.02579/0.03 **× Diffuse_Adjust [2.2, 2.0, 2.0] = 0.0567/0.0516/0.06 linear = sRGB 0.265/0.254/0.272 (0x43/0x41/0x45)** | **COMPROMISE** — this is the white-violet car: the gain was applied to a colour that already carried the adjust |
| **T-MA4** | authored gloss 0.6, "vanilla caps paint gloss at 0.4", ships 0.45 | 0.45 in every paint block ✓, but **the cap is not a cap**: the donor palette ships **8 tints at 0.45** (`Working/Palette/serpente_palette.xml`) and the highest measured paint value is 0.45, not 0.40 | authored **0.600** | **COMPROMISE** — 0.45 = **0.75 × authored**; the 0.4 justification is refuted by the donor's own palette |
| **T-MA5** | `Window` tint from paint colour, opacity = BmAK map × `Glass_Opacity`, "no tuned constant" | delivered: `s0` = `Glass_A` alpha × **1.2**, tint **0.176/0.176/0.188**; **no** reflectivity/roughness; normal written to table position 1 while `Window` samples `s2` | `Glass_Opacity` **1.2**, `Glass_Reflectivity` **0.8**, `Glass_Roughness` **1.1**, `glass_smudges` **0.2** | **COMPROMISE** — 1 of 4 glass members ported, and the one unported pair has a derivable value (§5) |
| **T-MA6** | 405 grabbed, 38 bound, **28 shipped** | **24** distinct BmAK TGAs bound in `factors.json`; **21** Batmobile `.ddsc` in the build dir; **9** slots are solid colour (no texture); **32** `s2`/`s3` slots bound to `a00_dummy_black_mpm` | 405 textures, 38 bound to slots | **COMPROMISE** — three different counts in three files, and every separation-mask slot is neutral |
| **T-MA7** | 10 tints, **all** `specular_gloss` 0.45, keep the donor's palette | palette is the donor's: **8 tints at 0.45, 2 at 0.0**, all `metallic` 1, `clear_coat` 1 | BmAK has **no** palette | **COMPROMISE** — the claim is wrong by 2 tints, and any tint selection overwrites the authored paint colour |

---

## 2. T-MA1 · blocks per LOD — carrier exact, totals wrong

MEASURED by decoding the built RBMs (`Working/Appearance/build/*.rbm`, `rbm_geom.decode`):

```
body_lod1..lod5.rbm   17 blocks = {'CarPaintMM': 16, 'Window': 1}
wheel_f_l_lod1..3.rbm  5 blocks = {'CarPaintMM': 4,  'Window': 1}
```

* The **mechanism** the row asserts (one material slot → one `CarPaintMM`, `Window` for glass) is
  present and correct on every body LOD and every wheel LOD. That half is **LORE-EXACT**.
* The **totals** are not: 5 body LODs × 17 = 85, plus 4 wheels × 5 LODs × 5 = 100 → **185 `CarPaintMM`
  + 25 `Window` = 210 blocks**. The row says **200 + 35 = 235**. The 25-block gap is not explained
  anywhere in the row, and the row's "35 meshes" sits against 5 body + 20 wheel = 25 meshes in the tree.
* **19 slots vs 17 body blocks.** `SLOTS.json` lists 19 slots / 13 instances; `factors.json` carries
  all 19 materials, but the body RBM has 17 blocks. Slots 14–18 (battery ×2, power cell, upgrades,
  `Batmobile_Worn_NoRain`) are plausibly on other meshes — the row does not say which, and the project
  has no slot→mesh map: **UNKNOWN**, one decode away (PSKX material index per mesh vs `SLOTS.json`).

## 3. T-MA2 · the body albedo — 4096×2048 became one RGB constant

| item | value | class |
|---|---|---|
| row's source | `NEW_Batmobile_V2_BODY_D` 4096×2048, "identity (DDS, sRGB)" | row text |
| present in the grab? | **no** — `Working/Appearance/grab/Playable_Batmobile_SF/Texture2D/` holds only `Batmobile_V3_Body_Decals_D`, `Batmobile_V3_Body_N`, `Batmobile_V3_TEXTURES_Body_Damage_ChapterMask` for the body | MEASURED |
| what the body block's `s0` is | `{"solid": [0.4784, 0.4588, 0.4941, 1.0], "source": "generated from bmak:Material0_BaseColour (…WheelArchs…) (x3.45, GRB-6)"}` | MEASURED (`factors.json`) |
| largest shipped texture | `batmobile_v3_textures_wheel_v2_d` **1024²**; body normal 512²; glass 128²; cockpit 128² | MEASURED |
| resolution delivered vs authored | body albedo: **0 px** (no texture) vs 4096×2048; body normal 512² vs `Body_N` 2048² (the grab's TGA is 2048² — a 16× area loss) | MEASURED |

So the row's transform ("identity") describes a texture that was never grabbed, never converted and
never bound. The delivered body colour is one 8-bit constant shared by 16 blocks.

**Verdict: COMPROMISE.** The gap is not "JC3 cannot hold a 4096 map" — JC3 holds what the allocator
allows; the gap is that the *asset* is absent from the grab, so the pipeline substituted a scalar.

## 4. T-MA3 · the base colour — 3.44× too bright, and the row disagrees with itself

`Research/BatmobileGrab/VALUES.json`:

```
paint.base_colour            [0.02579, 0.02579, 0.03, 1.0]
paint.effective_base_colour  [0.056738, 0.05158, 0.06]        # = base × Diffuse_Adjust [2.2, 2.0, 2.0]
paint.albedo_gain            3.4476                            # "vanilla paint tint luma 0.1837 / BmAK authored paint luma 0.0533 (GRB-6)"
```

The arithmetic chains:

| step | value (linear) | sRGB byte |
|---|---|---:|
| BmAK authored base | 0.02579 / 0.02579 / 0.03 | 0x30 / 0x30 / 0x33 |
| × `Diffuse_Adjust` (BmAK's own material adjustment) | **0.0567 / 0.0516 / 0.06** | **0x43 / 0x41 / 0x45** |
| × GRB-6 gain 3.4476 (**what the build did**) | **0.1946 / 0.1779 / 0.2086** | **0x7a / 0x75 / 0x7e** |
| row's cited "effective" numbers | 0.0567 / 0.0516 / 0.06 | — (pre-gain) |
| row's cited bytes | — | 0x83 / 0x7d / 0x86 = 0.514/0.490/0.525 (**a third value**) |

Three numbers for one colour in one cell. The **delivered** one is the third: the write is
`0.4784/0.4588/0.4941`, i.e. `sRGB(0.0567 × 3.4476)` — the gain applied **on top of** the BmAK
effective colour that the row itself calls "effective". That is a 3.44× brightness error in linear
light and exactly the "white-violet" report: at 0.19 linear the body is a mid grey-violet, while BmAK's
paint is 0.057 linear (near-black).

**Proposed replacement: 0x43 / 0x41 / 0x45 (0.0567 / 0.0516 / 0.06 linear), gain 1.0.** The gain's
justification is a luma match against a **vanilla tint vector** (`vanilla/paint_tint = [0.14, 0.19,
0.25]`, luma 0.1837) — a tint that multiplies a bright vanilla albedo texture. Comparing a tint luma to
a flat albedo luma compares two different quantities; that is the error. If JC3's tonemapping genuinely
needs compensation, it must be measured (T-B), not assumed.

## 5. T-MA4 · gloss — 0.45 vs authored 0.6, and the "cap" is not a cap

| quantity | value | source |
|---|---:|---|
| BmAK authored gloss | **0.600** | `VALUES.json` `paint.authored_gloss` |
| vanilla paint block, channel 1 | 0.400 | `VALUES.json` `vanilla.paint_gloss` (sportsmuscle body lod1 block 6) |
| **donor palette, 8 of 10 tints** | **0.450** | MEASURED `Working/Palette/serpente_palette.xml` |
| donor palette, 2 tints | 0.000 | same |
| build | 0.450 in all 16 paint blocks + 10 palette tints | `factors.json`, palette |

The row's chain "clamp to the vanilla cap (0.4), then raise to 0.45" is arithmetically what happened,
but its premise is false: **the donor's own palette ships 0.45 on eight tints**. A value the game's own
paint menu uses cannot be a format cap; 0.4 is one block's channel-1 value. So the ceiling was invented
at 0.4 and the build then broke it by 12.5 %, while landing 25 % below BmAK.

**Proposed replacement: 0.600** in the paint blocks and the palette, with the risk stated: 0.6 is
50 % above the highest value the donor fleet is *seen* to use (0.45), so it is R3 — out of the observed
range, not out of the format. Test: highlight width on the bonnet at noon against the 0.45 build.

## 6. T-MA5 · glass — 1 of 4 members, and a derivable pair

BmAK (`MATERIALS.md:1062`, decoded): `Glass_Opacity` **1.2**, `Glass_Reflectivity` **0.8**,
`Glass_Roughness` **1.1**, `glass_smudges` **0.2**; maps `Glass_S` (mask R=reflect, G=rough, B=fix),
`Glass_N`, `Glass_A` (opacity).

| member | BmAK | delivered | gap |
|---|---:|---|---|
| opacity | 1.2 × map | `Glass_A` alpha × **1.2** | **ported** (decoded constant, no tuning) |
| tint | paint colour | `[0.176, 0.176, 0.188]` | ported (paint colour, sRGB-encoded) |
| reflectivity | 0.8 × `Glass_S.R` | none | `Window.cb1 SpecFresnel` exists; **not written** |
| roughness | 1.1 × `Glass_S.G` | none | `Window.cb1 DiffuseRougness / SpecGloss` exist; **not written** |
| smudges | 0.2 | none | D11 (editor helper) — defensible |

The derivable pair, from the measured maps (`Glass_S`: R mean **0.565**, G mean **0.074**) and BmAK's
multipliers:

```
reflect  = 0.565 × 0.8 = 0.452         -> Window SpecFresnel
rough    = 0.074 × 1.1 = 0.081         -> gloss = 1 - 0.081 = 0.919  -> Window SpecGloss
```

**Proposed: `SpecGloss` 0.92, `SpecFresnel` 0.45** (per-pixel via `s3` is the open question in
`app-per-pixel-reflectivity.md` §7 T5b). Also fix the binding defect the row hides: the build writes
the canopy normal to block table position 1, while `window.fb.txt` samples `NormalMap` at **s2** — the
canopy normal is landing on an unbound slot (same finding, independently, in
`app-per-pixel-reflectivity.md` §7 T5a).

## 7. T-MA6 · texture count — three numbers, none of them 28

| count | value | where |
|---|---:|---|
| textures grabbed | 405 | row / grab |
| slots bound to a BmAK texture | **24** distinct TGAs | MEASURED `factors.json` |
| Batmobile `.ddsc` actually shipped | **21** per build dir | MEASURED `Working/Appearance/build*/…/*.ddsc` |
| slots that are a solid colour, no texture | **9** | MEASURED (`solid` entries) |
| `s2`/`s3` slots bound to `a00_dummy_black_mpm` | **32** (16 materials × 2) | MEASURED |
| row's "28 shipped" | 28 | row / MODLOG §103b |

"28" counts the whole texture set (21 Batmobile + 7 others/dummies), so it is true of the `.ee` and
false of the transfer: only **21** BmAK maps reach the game, and the entire property/tint channel is
neutral black on 16 of 19 materials. The row's rationale ("the 377 unshipped are decals/Jokerfied/other
packages") explains the grab, not the 21-vs-38 bound gap.

**Proposal:** state the count as *24 bound → 21 shipped → 9 substituted by a constant*, and route the
missing separation masks (the body's `WheelArch_MicroMasks` default is not in the grab) — that is the
same asset gap as `app-per-pixel-reflectivity.md` §6's last row.

## 8. T-MA7 · palette — donor values kept, and they overwrite the paint

| item | value | class |
|---|---|---|
| BmAK palette | **does not exist** ("`Palette` does not exist in UE3 vehicles") | decoded |
| donor palette (the build's) | 10 tints; `specular_gloss` **0.45 × 8, 0.0 × 2**; `metallic` 1 × 8, 0 × 2; `clear_coat` 1 × 10 | MEASURED |
| row's claim | "10 tints, **all** `specular_gloss` 0.45" | wrong on 2 |
| behaviour | every tint selection replaces the authored body colour in the paint channel | decoded (palette module is the repaint path) |

Keeping the donor palette is defensible as a *system* (T-MA7's own reasoning: the donor already serves
the game's repaint menu), but as delivered the car's BmAK colour survives only until the player opens
the menu — one click gives a non-lore colour. That is a compromise the row does not state.

**Proposed:** keep the 10-tint menu but set every tint's colour to the BmAK base colour (§4's
`0x43/0x41/0x45`) and every `specular_gloss` to the authored **0.6** (§5). The menu then cannot leave
lore, and the palette stops contradicting the blocks.

---

## 9. STAGES.md — closest system, gap, build action

| BmAK feature | closest JC3 system | gap | build action |
|---|---|---|---|
| body albedo `NEW_Batmobile_V2_BODY_D` 4096×2048 | `CarPaintMM.s0` diffuse texture | **asset absent from the grab** (grab has only `Body_Decals_D`, `Body_N`, chapter mask), so a scalar was substituted | new grab of the body master's `Diffuse_Map`; bake at the allocator's budget (2048² = 2 MB BC1 — over today's 694 KB headroom, so 1024² first); until then record the constant as a substitution, not a translation |
| authored base colour 0.0567/0.0516/0.06 linear | `CarPaintMM` + `s0` | none — the carrier is exact; only the **gain** was wrong | set the albedo to 0x43/0x41/0x45, gain 1.0 (§4) |
| authored gloss 0.600 | `m_SpecularGloss` float4 / palette `specular_gloss` | not a cap — but 0.6 is above every value the donor fleet is seen to use (max 0.45) | set 0.6 and declare R3 (§5) |
| glass reflectivity 0.8, roughness 1.1 | `Window.cb1 SpecFresnel / SpecGloss / DiffuseRougness` | `Window` parameter block not authored today (perpixel §9.3) | write 0.92 / 0.45 (§6); per-pixel via `s3` is a separate test |
| glass `Glass_A` opacity × 1.2 | `Window.s0` alpha — **done** | none | — |
| separation masks (channels 1–3) | `CarPaintMM.s2` + `s3` | the master's default mask asset is not in the grab → 32 slots on dummy black | grab it, then the band plan (§ `app-per-pixel-reflectivity.md` §5.1) |
| per-pixel roughness/reflectivity (4 maps) | `CarPaintMM.s2` bands / `GeneralMkIII.Gloss1Map` | 4 levels / block-type swap | see `app-per-pixel-reflectivity.md` |
| emissive masks | `CarLight.s5` RGB / `m_Emissive` | channel decoded; atlas not authored | see `app-emissive-mask-channel.md` |
| micro-detail (P1–P3) | none on `CarPaintMM` | no detail slot | see `app-microdetail-bake-plan.md` |
| palette (repaint menu) | `Palette.tints[]` — JC3-native | BmAK has none; donor tints overwrite the lore colour | set all 10 tints to the BmAK colour + gloss 0.6 (§8) |

## 10. Open appearance classes (for the briefs)

1. **Body albedo magnitude** — 3.44× too bright, gain never measured (T-MA3). *Highest priority: it is
   the "white-violet car".*
2. **Body albedo asset missing** — 4096×2048 never grabbed; scalar substituted (T-MA2).
3. **Gloss ceiling myth** — 0.4 cap invented, 0.45 shipped by the donor's own palette, 0.6 authored (T-MA4).
4. **Per-pixel property maps** — four D3 rows still dropped (`app-per-pixel-reflectivity.md`).
5. **Micro-detail** — P1/P2/P3 still "bake into s1", not baked (`app-microdetail-bake-plan.md`).
6. **Emissive** — channel decoded, atlas not authored; wheel `_E` map absent (T-MA6 + `app-emissive-mask-channel.md`).
7. **Glass response** — 3 of 4 members unported; normal slot bound at position 1 while the shader samples s2 (T-MA5).
8. **Separation masks** — 32 of 38 slots on `a00_dummy_black_mpm`; the body mask asset is missing.
9. **Palette overwrite** — the repaint menu can take the car out of lore in one click (T-MA7).
10. **Resolution budget** — glass 128², cockpit 128², body normal 512² against 2048² sources; the
    allocator's `--tex-max` is the lever, not a code change (MODLOG §102d).

## 11. Tests

* **T-A (albedo, offline + gated render)** — read back the body blocks' albedo: must be
  `0x43/0x41/0x45`; then a noon screenshot: the body's screen luma must sit **below** the road's
  (T-MA3's own criterion) and within ±15 % of a BmAK reference render of the same panel. Today's build
  fails by construction (0.19 linear vs 0.057).
* **T-B (gain, 2 runs)** — gain 1.0 vs 3.4476 side by side, fixed camera and exposure; pass: the 1.0
  run's body luma ratio to the BmAK reference is closer, and no panel clips to black at noon (the risk
  the gain was hedging).
* **T-C (gloss, 2 runs)** — 0.45 vs 0.6; measure the specular highlight width on the bonnet at 30°
  sun. Pass: the 0.6 highlight is narrower/brighter in the direction the BmAK reference shows; the
  palette must read 0.6 too, or the menu contradicts the blocks.
* **T-D (texture count)** — assert the shipped set is exactly the 24 bound sources → 21 `.ddsc`, and
  that every `s2`/`s3` is either a real mask or a listed gap (no silent dummy).
* **T-E (palette)** — select each of the 10 tints in game; every one must still read as the BmAK body
  colour (hue within 2°, luma within 10 %).
* **T-F (glass)** — `Window` block read-back: `SpecGloss 0.92`, `SpecFresnel 0.45`, normal at the slot
  the shader samples; canopy at noon must read as glass, not paint (T-MA5's own criterion).

## 12. Reproduce

```bash
cd "E:/Modding/JustCause3/JC3-Batmobile"
# 1. rows
grep -E '"id":"T-MA[1-7]"' Working/Translation/T_ROWS.jsonl
# 2. what the build wrote
uv run python - <<'PY'
import json
f=json.load(open('Working/Appearance/build_bud1/factors.json'))
m=f['materials']['Batmobile_V3_Mainbody_NEW_MIC']
print(m['textures']['s0']); print(m['inputs']['static.SpecularGloss'])
print('materials',len(f['materials']))
PY
# 3. what is shipped (21 batmobile ddsc, dims)
uv run python - <<'PY'
import glob,struct,os
ps=[p for p in glob.glob('Working/Appearance/build*/**/*.ddsc',recursive=True) if 'batmobile' in os.path.basename(p).lower()]
seen={}
for p in ps:
    d=open(p,'rb').read()
    if d[:4]!=b'AVTX': continue
    _,_,_,_,fmt,w,h=struct.unpack_from("<4sHBBIHH",d,0); seen[os.path.basename(p)]=(w,h,fmt)
for k in sorted(seen): print(k,'%dx%d fmt %d'%seen[k])
print('unique',len(seen))
PY
# 4. blocks per LOD
uv run python - <<'PY'
import glob,os,sys; sys.path.insert(0,'Tools/scripts'); import rbm_geom
from collections import Counter
for p in sorted(glob.glob('Working/Appearance/build/*.rbm')):
    print(os.path.basename(p), dict(Counter(rbm_geom.BLOCK_NAMES.get(b.type_hash) for b in rbm_geom.decode(open(p,'rb').read()).blocks)))
PY
# 5. the numbers the rows argue about
uv run python - <<'PY'
import json; v=json.load(open('Research/BatmobileGrab/VALUES.json'))
print(v['paint']); print(v['glass']); print(v['vanilla'])
import re; x=open('Working/Palette/serpente_palette.xml',encoding='utf-8',errors='replace').read()
print('palette gloss', re.findall(r'name="specular_gloss" gbltype="Primitive"[^>]*>([^<]+)',x))
PY
```

### Evidence index

| claim | file |
|---|---|
| the seven rows | `Working/Translation/T_ROWS.jsonl` (T-MA1…T-MA7) |
| the plan's own counts (405/38/28, 167 transferred, 7 partial) | `Working/Appearance/progress.md` §summary, §textures, §factors |
| authored base colour, effective colour, gain, gloss 0.6, glass tint | `Research/BatmobileGrab/VALUES.json` (`paint.*`, `glass.*`, `vanilla.*`) |
| BmAK glass members 1.2 / 0.8 / 1.1 / 0.2 | `Research/BatmobileGrab/MATERIALS.md:1062` |
| 19 slots / 13 instances | `Research/BatmobileGrab/SLOTS.json` |
| what the build bound and what it substituted | `Working/Appearance/build_bud1/factors.json` |
| block counts per LOD | `Working/Appearance/build/*.rbm` via `Tools/scripts/rbm_geom.py` |
| shipped texture set and sizes | `Working/Appearance/build*/…/*.ddsc` (AVTX header: w,h,format) |
| donor palette values | `Working/Palette/serpente_palette.xml` |
| `Window` params and the s2 normal slot | `Tools/JCMR-src/assets/jc3/shaders/window.fb.txt` |
| `CarPaintMM` `m_SpecularGloss` float4 | `Tools/JCMR-src/assets/jc3/shaders/carpaintmm.fb.txt` |
| budget 3,954/4,648 KB | MODLOG §103b |
