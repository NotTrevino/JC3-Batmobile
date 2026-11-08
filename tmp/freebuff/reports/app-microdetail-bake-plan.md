# APP — micro-detail: what ships today, and the bake procedure

Card: appearance `P1`/`P2`/`P3` (micro-detail baked into `s1`). **Plan + verification report — nothing was
baked, no build was written, no game launched.** Labels as in the rest of the research tree:
**decoded** (file + bytes/offset, read by a project tool or quoted source), **derived** (rule + inputs),
**INFERRED** (plausibility / artwork statistics), **UNKNOWN** (what was tried, what would settle it).

## 0. Change statement (AGENTS.md)

| item | value |
|---|---|
| intended change | add one report: what the shipped build actually contains, the decoded micro-detail numbers, the bake procedure, and the check that measures it |
| file | `tmp/freebuff/reports/app-microdetail-bake-plan.md` (this file) |
| why this file | the brief names it; all report output for this project lives under `tmp/freebuff/reports/` and its inputs were read-only |
| reverted by | deleting this file. No edit to `Research/`, `Tools/`, `Working/`, `Builds/`; no texture converted; no `.rbm` written |

---

## 1. Verdict

1. **The shipped build contains no micro-detail at all.** `Working/Appearance/build_bud1/ddsc/` holds 28
   textures and **none** is a micro-detail or micropattern map; every body block's `s1` is the plain
   authored normal (`batmobile_v3_body_n.ddsc`, `batmobile_v3_wheelarch_n.ddsc`, …) or a flat dummy;
   `s2`/`s3` are `a00_dummy_black_mpm.ddsc` except on the two materials that own a separation mask.
2. **`Working/Appearance/bodytex` is not a bake output.** It holds exactly one file,
   `Playable_Batmobile_SF/Texture2D/NEW_Batmobile_V2_BODY_D.tga` (4096×2048, 832 KB) — a **V2 body
   albedo**, not a normal, not micro-detail, and not referenced by any build tool (the only mentions in
   the tree are `Tools/scripts/review_g3b_claims.py`, which quotes a doc claim about it). It is a stray
   asset from an earlier experiment.
3. **`P1`'s "bake into s1" exists only as a rule string.** There is no bake step in the pipeline: a
   search of `Tools/scripts/*.py` for a bake function returns nothing, and `appearance_plan.py`'s owner
   field (`appearance_pipeline.py -> bat_assemble.py texture convert`) describes work neither file does.
   The rule's *action* is aspirational; only its *classification* is real.
4. **Half the input is missing from the grab.** `Batmobile_Microdetail` and `Micropattern_D_N`/`E_N` are
   on disk; **`Batmobile_Micropattern_A`, `_B`, `_C` and `_A_Normal` are not** — and those are the tiles
   the two materials with the most micro-detail parameters actually bind (§3). So a bake today can only
   use the base tile on the body, not the per-channel patterns.
5. **Two inputs the bake needs are UNKNOWN, not derivable:** the **unit of `MicroDetail_size`**
   (15 / 20 / 30 / 45 / 120 / 250 — repeat count across UV 0..1, or tile size in cm) and the **UV set**
   (the material graph carries a `2nd_or_3rd_UV_Ch` scalar whose value is not in any MIC, and our mesh's
   UV2 is a nearest-vertex copy from the Serpente, so it cannot carry a real tile). §4 states both
   readings; §5 gives the one test that separates them.
6. **The obvious check does not work, and the measurement says so.** At equal 1024² scale the
   micro-detail tile is *smoother* than the body normal (mean |high-pass| R 0.0129 vs 0.0237), so
   "high-frequency energy must go up" would pass or fail for reasons unrelated to the bake. §5 defines a
   **difference-spectrum + repeat-frequency-peak** check instead, with the measured baselines for both
   the pass and the fail case.

---

## 2. What the build does today — evidence

| check | command | result |
|---|---|---|
| micro-detail texture in the build | `ls Working/Appearance/build_bud1/ddsc \| grep -i micro` | **no match** (exit 1) — 28 textures, none micro-detail |
| what each body block's `s1` binds | `rbm_geom.decode(body_lod1.rbm)` → block textures | 17 blocks: `batmobile_v3_body_n` (body), `…_wheelarch_n`, `…_undercarriage_n`, `…_wheel_lights_n`, `…_weaponry_turret_v2_n`, `…_int_cockpit_n` ×2, `stagg_battery_01_n` ×2, `nimbus_power_cell_n`, `…_missile_upgrade_n`, and `a00_dummy_flat_nrm` on blocks 8, 11, 16 (decals, flip data, one shell) |
| separation/property maps | same decode | `s2`=`s3`=`a00_dummy_black_mpm.ddsc` on 15 of 17 blocks; `batmobile_v3_int_cockpit_m_msk.ddsc` (block 9) and `batmobile_v3_wheel_lights_m_msk.ddsc` (block 5) are the only real ones |
| `bodytex` contents | `find Working/Appearance/bodytex -type f` | **1 file**: `NEW_Batmobile_V2_BODY_D.tga` |
| does anything consume it | `grep -rn NEW_Batmobile_V2_BODY_D Tools/scripts Working/Appearance` | only `review_g3b_claims.py` (a doc-quote checker); no build tool |
| any bake implementation | `grep -rln "def .*bake\|bake(" Tools/scripts/*.py` | **no match** |
| window normal slot (adjacent defect) | `body_lod1.rbm` block 1 | `Window` slots: `batmobile_v3_glass_a_glass.ddsc`, `batmobile_v3_glass_n.ddsc`, `v0300_…_glass_mpm.ddsc`, `window_cracks_bullet_nrm.ddsc` — the build's normal sits in table position 1 while `window.fb.txt` samples `NormalMap` at `s2` (see the companion report §2.2) |

So the honest statement for the appearance ledger is: **micro-detail contributes 0 % of the shipped body
surface today**; the body differs from BmAK only by its albedo and its four authored normals.

---

## 3. Decoded inputs

All values below come from the dumped BmAK property files through `factors.resolve()` — the same parent
chain resolution the build uses (`Tools/scripts/factors.py`), run read-only for this report.

### 3.1 Parameters per material (decoded)

| material (MIC) | micro-detail scalars | textures bound | roughness coupling vector |
|---|---|---|---|
| `Batmobile_V3_Mainbody_NEW_MIC` | `MicroDetail_size` = **15.0**, `MicroDetail_Material3_Size` = **250.0** | `Material_Microdetail` → `Batmobile_Microdetail`; `Material3_Microdetail_N` → `Batmobile_Micropattern_A_Normal` (**absent from grab**) | — |
| `Batmobile_V3_WheelArchs_NEW_MIC` | `MicroDetail_size` = **15.0**, `MicroDetail_Material3_Size` = **250.0** | same as body | — |
| `Batmobile_V3_Undercarriage_NEW_MIC` | `MicroDetail_size` = **15.0**, `MicroDetail_Material3_Size` = **250.0** | same as body | — |
| `Batmobile_V3_Turret_NEW_MIC` | `MicroDetail_size` = **15.0**, `MicroDetail_Material3_Size` = **250.0** | same as body | — |
| `Batmobile_V3_Cockpit_MIC` | `BaseMaterial_Microdetail_Size` = **45.0**, `Material1` = **120.0**, `Material2` = **30.0**, `Material3` = **30.0** | `Material1_Microdetail_N` → `neutral_normal`; `Material2/3_Microdetail` → `Batmobile_Micropattern_C` (**absent**); `Material2/3_Microdetail_N` → `neutral_normal` | `underlayer_Detail_to_Roughness` = **[0.8, 0.5, 0.1, 1.0]** |
| `Batmobile_V3_Emissive` | `Material1` = **250.0**, `Material2` = **30.0**, `Material3` = **30.0** | `BaseMaterial_Microdetail` → `Batmobile_Micropattern_B` (**absent**); `Material1_Microdetail` → `Batmobile_Micropattern_A` (**absent**), `Material1_Microdetail_N` → `Batmobile_Micropattern_A_Normal` (**absent**); `Material2/3` → `C` (**absent**), `_N` → `neutral_normal` | `underlayer_Detail_to_Roughness` = **[0.0, 0.44, 0.44, 1.0]** |
| `BatmobileV3_Cockpit_Seat`, `Batmobile_V3_Discbreak_MIC`, `BatmobileV3_Wheel_V2_MIC`, `Nimbus_Power_Cell_Mat`, `Stagg_Battery_01_MAT`, `Stagg_Battery_Energy_01_MAT`, `Cockpit_Master_Flip_Data` | **none** | none | none |

Two consequences the plan has to carry:

* `P1`'s "6 micro-detail textures" is a texture census, not a material census: **6 materials** carry
  micro-detail parameters, and only the **body family (4 MICs) binds a tile that exists on disk**.
* The turret material in `MATERIALS.md` is quoted with `MicroDetail_size=20`, but the shipped
  `Batmobile_V3_Turret_NEW_MIC` dumps **15.0** (same as the body). The 20 belongs to
  `Batmobile_V3_Turret_Jokerfied_MIC` (another skin). **Build from the MIC chain, not the doc table.**

### 3.2 Tiles on disk (decoded from the grab)

| tile | size | format | present | bound by |
|---|---|---|---|---|
| `Batmobile_Microdetail` | 1024×1024 | PF_DXT1 (TGA on disk) | **yes** | Mainbody, WheelArchs, Undercarriage, Turret (`Material_Microdetail`) |
| `Batmobile_Micropattern_D_N` | 1024×1024 | PF_DXT1 | yes | **no MIC in the V2 car binds it** |
| `Batmobile_Micropattern_E_N` | 1024×1024 | PF_DXT1 | yes | not bound by the V2 car |
| `Batmobile_Micropattern_A`, `_B`, `_C` | — | — | **absent** | Cockpit_MIC (C), Emissive (B, A) |
| `Batmobile_Micropattern_A_Normal` | — | — | **absent** | Emissive, body family (`Material3_Microdetail_N`) |
| `neutral_normal` | — | — | value, not an asset | Cockpit_MIC, Emissive |

`P1`'s bake is therefore executable **today only as: body family ← `Batmobile_Microdetail` at the base
channel**. `D_N`/`E_N` are on disk but unbound in this car; using them would be inventing an assignment
BmAK does not make.

### 3.3 High-frequency baseline (measured, equal scale)

Metric `E = mean |I − gaussian(I, σ=2 px)|` on the normal's R and G at **1024×1024** (LANCZOS resize),
plus the FFT radial split of the RG mean.

| texture | R | G | low band (<0.25) | high band (≥0.75) |
|---|---|---|---|---|
| `Batmobile_V3_Body_N` (the shipped body `s1`) | 0.0237 | 0.0226 | 0.709 | 0.043 |
| `Batmobile_Microdetail` (the base tile) | 0.0129 | 0.0282 | 0.926 | 0.018 |
| `Batmobile_Micropattern_D_N` | 0.0094 | 0.0139 | 0.681 | 0.042 |
| `Batmobile_V3_WheelArch_N` | 0.0212 | 0.0275 | 0.638 | 0.069 |
| `Batmobile_V3_Undercarriage_N` | 0.0309 | 0.0331 | 0.641 | 0.035 |

**Read this carefully:** the base tile's absolute HF energy is *below* the body normal's. A check of the
form "baked HF > source HF" would be measuring the resize and the BC5 quantisation, not the bake. §5
uses the *difference* spectrum and the repeat-frequency peak instead.

---

## 4. The bake procedure

### 4.1 Inputs

| input | value | source |
|---|---|---|
| base normal | the material's authored `s1` (`Batmobile_V3_Body_N` etc.) | the shipped conversion |
| detail tile | `Batmobile_Microdetail` (1024², tangent-space normal, BC1 on disk) | grab, decoded |
| tiling `T` | `MicroDetail_size` = **15** (body family) — **unit UNKNOWN**, two readings in §4.2 | MIC, decoded |
| UV set | `UV1` — **forced**, because `2nd_or_3rd_UV_Ch`'s value is not in any MIC and our UV2 is a nearest-vertex copy from the Serpente (MODLOG §77) | derived + UNKNOWN |
| channel weight `α_k` | the material's separation-mask channel `k` (0..1); **no mask on the body → α₀ = 1, α₁..₃ = 0** | inferred structure (mask missing-on-disk) |
| normal strength `k` | **1.0**, recorded as an assumption — BmAK's microdetail nodes carry a *Size* scalar only, no strength in the MIC | UNKNOWN |
| roughness coupling | `underlayer_Detail_to_Roughness` = [0.8, 0.5, 0.1, 1.0] (cockpit) / [0, 0.44, 0.44, 1.0] (emissive); body has none | MIC, decoded |
| output | BC5 normal (linear, no sRGB flag), at the allocator's cap for that material (`tex2ddsc` `kind="normal"`) | pipeline |

### 4.2 Tiling — both readings, and the rule that keeps them seam-free

`MicroDetail_size` is either

* **(a) repeats across UV 0..1** (so 15 = the tile repeats 15× across the material's chart), or
* **(b) tile size in cm** (so 15 = a 15 cm tile in world space).

The value set (15 body / 20 turret-Jokerfied / 30, 45, 120, 250 on the cockpit and wheel-light
materials) is consistent with either; no file states the unit. The bake is written so that **only one
number changes** when the test settles it:

```
T_desired = T                     (reading a: repeats per UV)
T_desired = L_uv / (T/100)        (reading b: L_uv = surface length in metres per one UV unit,
                                   measured from the assembled mesh's UV density)

T_eff = max(1, round(T_desired))          # integer repeats: no seam at the UV borders
```

`T_eff` must be an integer *and* the output resolution must be a multiple of `T_eff × tile_period`;
otherwise the tile boundary lands mid-texel and shows as a grid line (the seam test in §5 catches it).

### 4.3 Blend (reoriented normal mapping, one pass per channel)

For each texel, with `N₀` the base tangent normal and `N₁` the tile sampled at `UV1 × T_eff`:

```
w   = α_k · k                              # α from the mask channel, k = 1.0 (assumption)
t   = normalize(vec3(N₁.xy + vec3(0,0,1), N₁.z))   # RNM: reorient the detail by the base
N   = normalize(vec3(N₀.xy + t.xy·w, N₀.z))
```

Why RNM and not a lerp: a lerp flattens the base normal where the detail is strong (visible as a wipe on
the panel edges); RNM preserves the base's silhouette response, which is the whole point of micro-detail
on a matte panel.

Channel application, exactly as the mask says:

| channel | weight source | tile | applies when |
|---|---|---|---|
| 0 (base) | always 1 (no mask on the body) | `Batmobile_Microdetail` | body family, turret, undercarriage, wheel arch |
| 1 | mask R | `Micropattern_A` (absent) | Emissive only |
| 2 | mask G | `Micropattern_C` (absent) | Cockpit_MIC, Emissive |
| 3 | mask B | `Micropattern_C` / `A_Normal` (absent) | Cockpit_MIC, Emissive |

So on today's assets the bake reduces to **channel 0 with weight 1**; channels 1-3 stay unwritten and are
recorded as blocked on the missing tiles, not silently baked with a substitute.

### 4.4 Roughness coupling

`P3` says the detail's effect on roughness is "folded into the baked normal's effect on the gloss
vector". That cannot be right: a normal map changes the shading normal, not the gloss scalar. What the
pipeline can honestly do:

1. compute the detail's **mean slope** `s̄ = mean(1 − N₁.z)` over the tile at `T_eff`;
2. fold it into the material's gloss **once**: `gloss' = gloss · (1 − c·s̄·r_k)` with `c` a single new
   constant and `r_k` = `underlayer_Detail_to_Roughness[k]` (0.8/0.5/0.1/1.0 cockpit, 0/0.44/0.44/1
   emissive, 0 for the body — so **the body gets no roughness coupling from this rule at all**);
3. record the per-pixel part as a **gap** (four-band ceiling on `CarPaintMM`; see
   `app-per-pixel-reflectivity.md` §5-§6). `P3`'s wording must change from "cannot be stored" to "stored
   as a mean on `CarPaintMM`, per pixel only on `GeneralMkIII`".

### 4.5 Resolution and LODs

`s1` is capped per material by the texture budget (body 1024, undercarriage/wheel arch 512, small parts
256 — `allocate_caps`). The bake must run **per LOD**, because `T_eff` is defined on the LOD's own UV
chart: baking `lod1` and reusing it on `lod4` would mis-tile. Cost: 5 bakes per body material (17 body
blocks across 5 LODs), which is why the bake belongs in the same Blender pass that already decimates.

---

## 5. The check that measures it

The failure mode of a bake is not "no detail" (the tile is right there); it is **detail at the wrong
scale or a visible seam**. The checks are ordered by what they can catch.

### C1 — difference-spectrum energy (offline, after a bake)

```
D = N_baked − N_source            # per texel, RG
E_diff = mean|D − gaussian(D, σ=2)|
E_tile = mean|N_tile − gaussian(N_tile, σ=2)|   at the same 1024²
```

Pass: `E_diff ≥ 0.5 · E_tile` on the channels the mask enables, and `E_diff = 0` exactly on channels
whose weight is 0 (a bake that ignores the mask fails here). Baselines from §3.3: body tile
`E_tile` = 0.0129 (R) / 0.0282 (G); so the body's `E_diff` must be ≥ 0.0065 / 0.0141.
Fail case to guard against: a resize-only "bake" should give a much lower `E_diff`; the threshold is calibrated on the first control run (source converted, tile not applied) — if that control exceeds 0.5 · `E_tile`, the metric is measuring resampling and must be tightened, not the bake accepted.

### C2 — repeat-frequency peak (offline)

Take the FFT of the baked normal's RG, radially average, and look for the **peak at the tile frequency**:
`f = T_eff / W` cycles per texel (e.g. 15 repeats on 1024 px → f = 0.0146). Pass: a local maximum within
±1 bin of `f` whose power is ≥ 2× the median of its neighbourhood, and **no** comparable peak in the
source normal. This is the only check that proves the *scale* is right, and it is the check that
distinguishes reading (a) from reading (b) — when the unit is settled, the expected `f` is known in
advance and the two readings predict peaks 15 vs `L_uv/0.15` apart.

### C3 — seam / grid test (offline)

At every tile boundary (multiples of `W/T_eff`), take the column/row gradient of the baked normal and
compare to the interior distribution. Pass: boundary gradient ≤ p99 of the interior. A non-integer
`T_eff`, or a resize that does not align the tile, produces a line of outlying gradients.

### C4 — low-band preservation (offline)

`low` band share (§3.3) of the baked normal must be within 5 % of the source's; the bake must not shift
the panel's large-scale shading. Body source: 0.709.

### C5 — roughness mean preservation (offline)

`mean(gloss)` before and after §4.4 step 2 within 0.01, and the recorded `c` printed in the build log.
A change larger than that means the coupling constant is doing the work the texture should do.

### C6 — round-trip and budget gates (offline, every build)

25/25 RBMs re-encode byte-identical; `spec_check.py` 0 mismatches; every new `.ddsc` registered in
`@files.xml`; texture budget ≤ 4,648 KB (body `s1` re-bake does not add a file, only bytes — so the
allocator must be re-run with the new sizes); model budget unchanged.

### C7 — blind A/B (in-game, gated on `tmp/freebuff/APPROVED_Q.txt`)

Three fixed-camera renders of the body side panel at noon: (i) today's build, (ii) baked at `T_eff = 15`,
(iii) baked at the other reading's `T_eff`. The operator picks the closest to the BmAK reference without
being told which is which. Pass: (ii) or (iii) wins by a clear margin **and** the winner matches the
reading the file evidence predicts; a tie means the tile scale is below the screen's Nyquist at that
camera distance and the test needs a closer frame.

---

## 6. Where JC3 has no exact carrier — closest system, gap, build action (STAGES.md)

| BmAK feature | closest JC3 system | gap | build action (BUILD stage) |
|---|---|---|---|
| tiled micro-detail normal (base channel) | `CarPaintMM.s1` (normal) — bake the tile into it | tiling becomes part of the atlas: **no UV-scale / detail-repeat input** on `CarPaintMM`; must be baked per LOD (5 per material) | add the bake pass (§4) to the existing Blender/convert step; `T_eff` from §4.2 |
| micro-detail **as its own sampler** | `CarLight.s4 NormalDetailMap` — the only block in these five with a dedicated detail-normal sampler | it is a *light-mesh* block; its `cb2 float4 MaterialConsts[4]` is undecoded (§102d), and the car's paint is not a light mesh | decode `CarLight`'s 64 B, then re-test whether a light block can carry a panel's detail; until then, bake |
| layered micro-detail (gloss/metallic/normal layers, `USE_LAYERED`) | `GeneralMkIII` slots 6-10 (`Layered Albedo/Gloss/Metallic/Normal`) + `LayeredMaskInfluence` etc. | the layered flags/params are `[unused]` in the shipped shader header, and no project writer emits `GeneralMkIII` (G3-04e) | serialiser + `USE_LAYERED` flag study; strictly later than the bake |
| per-channel micro-detail weights | `CarPaintMM.s2 PropertyMap` selects one of four channels per pixel | the *weights* come from BmAK's separation mask, which is **missing-on-disk** for the body; and `s2` is also the per-pixel gloss carrier (companion report §5.1) — one texture, one meaning, so mask and gloss bands compete for it | grab the body mask (master default `WheelArch_MicroMasks`) or author it; then decide `s2` = mask, gloss bands on `s3`, tint elsewhere |
| micro-detail's roughness modulation | `m_SpecularGloss` float4 (bands) / `GeneralMkIII.Gloss1Map` | no per-pixel roughness on `CarPaintMM`; the body has **no** `underlayer_Detail_to_Roughness` value at all | fold the mean into gloss (§4.4 step 2), record the per-pixel gap |
| UV set for the tile (`2nd_or_3rd_UV_Ch`) | `CarPaintMM` samples `s1` on the mesh's UV set — same set as the normal | the set is a material-graph scalar not present in any MIC; our UV2 is a copied Serpente layout | bake on UV1 and record the gap; if the graph value can be recovered from the master's expression defaults, re-run the bake on that set |

---

## 7. Still UNKNOWN (and what settles each)

1. **Unit of `MicroDetail_size`.** 15 body / 45 base cockpit / 30 / 120 / 250 / 20 (Jokerfied turret).
   Settled by C2 (the repeat-frequency peak) or C7 (blind A/B).
2. **UV set of the micro-detail sample.** `2nd_or_3rd_UV_Ch` exists in the expression list
   (`COLOUR_FUNCTIONS.json`, `in_expressions_not_in_mic`) with no value in the MICs; the graph's
   connections are not recoverable (MODLOG §78). Settled by reading the master's expression defaults, or
   by C2 on a chart with a known UV2.
3. **Normal strength `k`.** No scalar in any MIC; `k = 1.0` is an assumption.
4. **The tiles for channels 1-3** (`Micropattern_A/B/C`, `A_Normal`) are absent from the 115-file grab.
   Settled by a re-grab of those Texture2D objects.
5. **The body's own separation mask** (`WheelArch_MicroMasks`, master default) — absent, so channel
   weights on the body are all-or-nothing. Settled by a re-grab.
6. **Whether the micro-detail is applied before or after the base normal's mip chain** (i.e. whether
   BmAK's detail fades with distance — there is a `Roughness_Microdetail_fadeout` expression name but no
   value). Settled by a distant-view A/B; until then the bake is distance-independent and the LOD bake
   provides the only fade.

---

## 8. Reproduce

```bash
cd "E:/Modding/JC3-Batmobile"
# what ships today
ls Working/Appearance/build_bud1/ddsc | grep -i micro || echo "no micro-detail texture in the build"
find Working/Appearance/bodytex -type f
uv run python - <<'EOF'
import sys; sys.path.insert(0,'Tools/scripts'); import rbm_geom
m=rbm_geom.decode(open('Working/Appearance/build_bud1/body_lod1.rbm','rb').read())
for i,b in enumerate(m.blocks):
    print(i, rbm_geom.BLOCK_NAMES.get(b.type_hash), [t.split('/')[-1] for t in (b.textures or [])][:4])
EOF
# the decoded micro-detail parameters, through the same chain resolve the build uses
cd Tools/scripts && uv run --with numpy --with pillow python - <<'EOF'
import sys; sys.path.insert(0,'.'); import factors as FA
props, files = FA.load_bmak('../../Working/Appearance/grab')
for m in ['Batmobile_V3_Mainbody_NEW_MIC','Batmobile_V3_Cockpit_MIC','Batmobile_V3_Emissive']:
    r=FA.resolve(m,props)
    print(m, {k:v for k,v in r['sc'].items() if 'icrodetail' in k.lower() or 'icroDetail' in k},
             {k:v for k,v in r['tex'].items() if 'icrodetail' in k.lower() or 'icroDetail' in k},
             {k:v for k,v in r['vec'].items() if 'etail' in k})
EOF
# the C1/C2/C4 baselines
uv run --with pillow --with numpy python - <<'EOF'
from PIL import Image, ImageFilter; import numpy as np
def hf(p,size=1024):
    im=Image.open(p).convert('RGB').resize((size,size),Image.LANCZOS); a=np.asarray(im,np.float32)/255
    return {c: round(float(np.abs(a[:,:,i]-np.asarray(im.filter(ImageFilter.GaussianBlur(2)),np.float32)[:,:,i]/255).mean()),4)
            for i,c in enumerate('RG')}
print(hf('Working/Appearance/grab/Playable_Batmobile_SF/Texture2D/Batmobile_V3_Body_N.tga'))
print(hf('Working/Appearance/grab/Playable_Batmobile_SF/Texture2D/Batmobile_Microdetail.tga'))
EOF
```

### Evidence index

| claim | file |
|---|---|
| `P1`/`P2`/`P3` text and their owner field | `Tools/scripts/appearance_plan.py:78-99` |
| the four D3 rows (separate card) | `Working/Appearance/appearance_plan.json`, `.rules[id=D3]` |
| T-21's audit of P1 (5 of 6 tiles absent; `neutral_normal` is a value) | `Research/challenge/card-T-21.md` A6 |
| micro-detail scalars/textures per material | `Working/Appearance/grab/Playable_Batmobile_SF/MaterialInstanceConstant/*.props.txt` (via `factors.resolve`) |
| tile sizes and formats | `Research/BatmobileGrab/TEXTURES.md` (`Batmobile_Microdetail` 1024² PF_DXT1) |
| `underlayer_Detail_to_Roughness` values | the two MIC props dumps (`Cockpit_MIC`, `Emissive`) |
| `2nd_or_3rd_UV_Ch` has no MIC value | `Research/BatmobileGrab/COLOUR_FUNCTIONS.json` (`in_expressions_not_in_mic`) |
| UV2 is a Serpente nearest-vertex copy | MODLOG §77 ("the decal layer samples UV2, which our writers copy from the NEAREST SERPENTE vertex") |
| `CarLight` detail-normal sampler / undecoded params | `Tools/JCMR-src/assets/jc3/shaders/carlight.fb.txt`; MODLOG §102d |
| `GeneralMkIII` layered slots, no writer | `renderblockgeneralmkiii.cc`; `tmp/freebuff/reports/G3-04e.md` |
| texture budget 3,954 / 4,648 KB | MODLOG §103b |
