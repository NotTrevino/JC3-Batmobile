# BmAK glass -> JC3 `Window` block (T-21 follow-up, POL-1)

**Question.** `Batmobile_Glass` has 8 empty slots and `Batmobile_V3_Glass_S` (the glass layer mask)
is carried only as a tint (route R4). BmAK glass has tint, reflectivity, dirt and a frame mask.
Read the decoded glass rows and the JC3 `Window` block, table every parameter, check whether the
canopy's two shapes share the material, and say where the glass is not yet faithful.

**Verdict.**

* **The BmAK master is empty.** `Batmobile_Glass`'s eight named inputs - `DiffuseColor`,
  `SpecularColor`, `SpecularPower`, `Normal`, `EmissiveColor`, `Opacity`, `OpacityMask`,
  `MetalMask` - are all unconnected (`—`) in **all four** packages [decoded]. Everything the glass
  looks like comes from the MIC plus three textures.
* **The JC3 `Window` block stores no glass scalars.** The block is 40 B/vertex position, UV, two
  zeros, a packed normal, a tangent and a **constant packed ~(1,1,1) tint**, plus a texture table
  - and nothing else [decoded: strides (40,2); the 16 B between the table and the buffers does not
  decode as four plausible floats]. The scalars live in the *shader's* `MaterialConsts` (`cb1`),
  which no `.rbm` block carries.
* **JC3 therefore has the parameters but not per-material values; BmAK has values but not the
  slots.** The tint, opacity, reflectivity and roughness all exist as named shader members yet
  there is no decoded way for a private material to set them - the shipped vehicles get their look
  from the diffuse texture's RGB/alpha and the vertex tint.
* **Cracking is a runtime contact-point system in JC3, not a texture swap**: `windowdamage`'s
  `cb2 WindowContactPoints` carries `NumPoints` + `PointPositionAndSize[32]`, weighted by
  `DamageMaskWeight` / `DamageRampWeight`, over the `window_cracks_bullet_*` and
  `window_cracks_tile_*` maps that every shipped glass block already binds [decoded].
* **Both canopy shapes share one material** in BmAK (one skin, one slot, animation moves the
  geometry), while JC3's canopy open/close is a material/part switch [decoded source, derived JC3].
* **9 of 13 glass parameters are not faithful** (§4).

---

## 1. BmAK glass, decoded

### 1.1 The master has nothing

[decoded: `MATERIALS.md` rows for all four packages (Funhouse, Joker, MK2, base) - identical.]

| master input | connected |
|---|---|
| `DiffuseColor` | `—` |
| `SpecularColor` | `—` |
| `SpecularPower` | `—` |
| `Normal` | `—` |
| `EmissiveColor` | `—` |
| `Opacity` | `—` |
| `OpacityMask` | `—` |
| `MetalMask` | `—` |

That is the "8 empty slots": the master is a **socket contract with no defaults**, so rule
"the glass is vanilla glass" cannot be justified by the master - every value is in the MIC.

### 1.2 The MIC

| item | value | class |
|---|---|---|
| `Glass_Opacity` | **1.2000** | decoded (GUID `72b5400b`) |
| `Glass_Reflectivity` | **0.8000** | decoded (GUID `6b94edbf`) |
| `Glass_Roughness` | **1.1000** | decoded (GUID `05ac6289`) |
| `glass_smudges` | **0.2000** | decoded (GUID `13da4f34`) |
| `bat_glass.tint` | **[0.02579, 0.02579, 0.03]** | decoded (`VALUES.json`; "same authored paint colour as the body - canopy has no colour parameters") |
| `glass.opacity_multiplier` | 1.0 | decoded |

| texture | dims | format | bound as |
|---|---|---|---|
| `Batmobile_V3_Glass_A` | 4096x4096 | PF_DXT1 | `OpacityMap` |
| `Batmobile_V3_Glass_N` | 4096x4096 | **PF_BC5** | `Normal` |
| `Batmobile_V3_Glass_S` | 4096x4096 | PF_DXT1 | `Mask (R=Reflect / G=Rough / B=Normal map compression artifacts fix)` |
| `Batmobile_V2_GLASS_MASK` | 1024x512 | PF_DXT1 | **`—` (unbound in every package)** |

The `V3_Glass_S` packing is not an inference: it is the parameter's own decoded name -
**R = reflectivity, G = roughness, B = a normal-map compression-artifact fix**.

**The frame mask is UNKNOWN.** No decoded binding in any package names a frame mask. The one
candidate is `Batmobile_V2_GLASS_MASK` (1024x512 DXT1), which ships in all four packages and is
bound to **nothing** - a mask with no material. Whether it is the canopy frame is not stated
anywhere on disk; §6 item 3 says what would settle it.

---

## 2. The JC3 `Window` block and its shaders, decoded

### 2.1 The block

[decoded this pass: `sportsmuscle_window_f_lod1.rbm`, `door_f_l_window`, `door_f_r_window`,
`trunk_window`, `window_r_l`, `window_r_r` - 6 blocks, identical structure.]

| field | value |
|---|---|
| strides | `(40, 2)` - 40 B per vertex, u16 indices |
| vertex layout | `x, y, z` \| `u, v` \| `0, 0` \| packed normal \| tangent \| constant packed tint |
| positional/param bytes between texture table and buffers | 16 B; does **not** read as four plausible floats (denormal garbage) - **no scalar table** |
| textures (t0..t6) | `<car>_glass_alpha_dif.ddsc`, `dummy_nrm.ddsc`, `<car>_glass_mpm.ddsc`, `window_cracks_bullet_nrm.ddsc`, `window_cracks_bullet_mpm.ddsc`, `window_cracks_tile_nrm.ddsc`, `window_cracks_tile_mpm.ddsc` |

Two facts worth stating plainly: **the shipped glass normal slot holds `dummy_nrm.ddsc`** (the slot
exists and is empty), and **the crack maps are bound on every vanilla window**.

### 2.2 `window.fb.txt` - `cb1 MaterialConsts`

[decoded: header, all 4 window variants agree on the struct.]

| member | offset | used in `window` | used in `windowdamage` / `windowsimpledamage` |
|---|---:|---|---|
| `SpecGloss` | 0 | yes | yes |
| `SpecFresnel` | 4 | yes | yes |
| `DiffuseRougness` | 8 | yes | yes |
| `TintPower` | 12 | yes | yes |
| `MinAlpha` | 16 | yes | yes |
| `UVScale` | 20 | yes | yes |
| `unused_` (float2) | 24 | - | - |
| `DamageMaskWeight` | 32 | **[unused]** | yes |
| `DamageRampWeight` | 36 | **[unused]** | yes |
| `Alpha` | 40 | yes | yes |

`windowdamage` adds a second cbuffer:

| member | offset | meaning |
|---|---|---|
| `NumPoints` | 0 | how many contact points are live |
| `pad_` | 4 | - |
| `PointPositionAndSize[32]` | 16 (512 B) | **up to 32 crack points, each a position and a size** |

Samplers: `s0` `DiffuseMap`/`t0`, `s2` `NormalMap`/`t2`, `s3` `PropertyMap`/`t3`; the damage
variants add `s4` `DamagePointNormalMap`/`t4` and `s5` `DamagePointPropertyMap`/`t5`;
`windowsimpledamage` keeps only `t0`/`t4`/`t5`. All variants bind `s9` `RainOccluderSampler`
(`t40 RainOccluderTexture`), `s11` `CubeMapSampler` (`t11 EnvironmentCube`), `t12 Falloff`.

**So the glass tint is per-vertex** (the `COLOR0` input the shader signature declares, weighted by
`TintPower`) **and in the diffuse texture** - which is why the shipped vehicles' windows differ in
tint without any scalar being stored: the colour is in `*_glass_alpha_dif.ddsc`, the vertex colour
is the constant ~(1,1,1) template.

---

## 3. Per-parameter table

`equal` = the JC3 member means the same thing and the value can be carried; `partial` = a member
exists but a value is lost; `not equal` = no member means that thing.

| # | BmAK parameter | BmAK value | JC3 member | verdict |
|---:|---|---|---|---|
| 1 | tint | `[0.02579, 0.02579, 0.03]` | `DiffuseMap` `t0`/`s0` RGB x `TintPower` `cb1[12]`; per-vertex `COLOR0` | **not equal** - no tint vector; must be baked into `t0` or the vertex colour |
| 2 | `Glass_Opacity` | 1.2 | `Alpha` `cb1[40]`, floor `MinAlpha` `cb1[16]`, and `t0` alpha | **partial** - the member exists, no decoded per-material write path |
| 3 | `Glass_Reflectivity` | 0.8 | `SpecGloss` `cb1[0]` **and** `SpecFresnel` `cb1[4]` | **partial** - one BmAK scalar, two JC3 members, assignment UNKNOWN |
| 4 | `Glass_Roughness` | 1.1 | `DiffuseRougness` `cb1[8]` | **partial** - name match, but a value of 1.1 has no documented clamp; the bridge is underived |
| 5 | `V3_Glass_S` **R** (reflect) | per-pixel 4096x4096 | `PropertyMap` `t3`/`s3` channel | **not equal** - `s3` channel packing undecoded |
| 6 | `V3_Glass_S` **G** (rough) | per-pixel | `PropertyMap` `t3`/`s3` channel | **not equal** - same |
| 7 | `V3_Glass_S` **B** (normal fix) | per-pixel | none | **not equal** - an offline fix channel; JC3 has no equivalent and needs none if the normal is re-baked |
| 8 | `V3_Glass_N` | 4096x4096 BC5 | `NormalMap` `t2`/`s2` | **equal** (role) - and the slot ships empty (`dummy_nrm`), so it is free |
| 9 | `V3_Glass_A` opacity map | 4096x4096 DXT1 | `t0` alpha (no separate opacity sampler) | **partial** - same data, different slot; needs a repack into `t0`'s alpha |
| 10 | `glass_smudges` (dirt) | 0.2 | none for glass; nearest `s9`/`t40` `RainOccluderTexture` or a `t3` property channel | **not equal** |
| 11 | frame mask `V2_GLASS_MASK` | 1024x512 DXT1, unbound | none | **not equal** - bake into `t0` alpha or the property map |
| 12 | cracking | **absent in BmAK** | `DamagePointNormalMap` `t4`/`s4` + `DamagePointPropertyMap` `t5`/`s5` + `WindowContactPoints` (32 points) + `DamageMaskWeight`/`DamageRampWeight` | **JC3 has more** - nothing to carry, something to use |
| 13 | canopy open + closed share the material | yes (one skin, slot 1, 3,532 faces) | JC3 canopy open/close = material switch / second block | **equal in source, gap in JC3** |

**Counts.** 13 rows: **2 equal** (8, 13), **4 partial** (2, 3, 4, 9), **7 not equal**
(1, 5, 6, 7, 10, 11, 12-as-source-gap). **9 of 13 not faithful** (4 partial + 5 not-equal rows
that carry a BmAK value: 1, 5, 6, 7, 10, 11 → that is 4 + 5 = 9; row 12 has no BmAK value).

---

## 4. The canopy's two shapes

[decoded: `ANIMATIONS.md` §canopy (20 clips), `COCKPIT.md` §1, `MESHES.md` (12 exports),
`Working/Translation/T8_PARTS.md:275` (canopy opens by translation), `G2X.md` (JC3 canopy = material switch).]

| question | answer | evidence |
|---|---|---|
| is there a separate open-canopy mesh? | **no** | `MESHES.md` lists 12 exports: `Batmobile_V2` plus the Destroyed/Fire variants, MK2 and Jokerfied skins and the Batwing carrier. No `CanopyOpen`. |
| how does it open? | **by translation**, 72.481 cm, driven by `CockPit_Mesh` (544 faces of slot 11, 1,716 of slot 1) and `Batmobile_Nose_Mesh` 39.7-45.4 cm | `ANIMATIONS.md` (20 canopy clips, e.g. `Cockpit_Open` 14 frames / 0.433 s), `T8_PARTS.md:275` |
| do both shapes share the material? | **yes** - one slot, one MIC (`Batmobile_V3_Glass_INST`), one set of textures; the animation moves the geometry, it does not swap a material | `COCKPIT.md` §1 (slot 1, 3,532 faces, 1,716 on `CockPit_Mesh`) |
| what does JC3 do? | the canopy is a **material switch**, and a shipped JC3 vehicle has no retractable canopy; the closest driver is the `Hood` part (+X 0..70 deg) | `G2X.md` APP-3 row; `T8_PARTS.md:277` |

**Derived.** BmAK needs no second material for the open canopy; JC3 needs a second
`Window` block (or a `Hood`-driven part) because its glass is geometry-bound. That asymmetry is the
whole MOD-4/ANI-8 cost on the glass side, and it is a *part* problem, not a material problem: the
material is shared in the source, so it must be shared in the build too - two blocks pointing at
the same texture set.

---

## 5. Where the glass is not faithful, and exactly what fixes it

| # | gap | fix (exact) | needs |
|---:|---|---|---|
| G1 | **tint** has no vector | bake `[0.02579, 0.02579, 0.03]` into `t0`'s RGB (multiply the alpha glass texture by the tint), keep `TintPower` at 1.0, leave the vertex tint at the template's ~(1,1,1) | bake |
| G2 | **opacity** lives in a separate 4K map | repack `V3_Glass_A` into `t0`'s alpha (JC3 reads opacity from the diffuse alpha); keep `MinAlpha` as the floor | repack |
| G3 | **reflectivity / roughness** per-pixel lost | split `V3_Glass_S`: R -> `SpecGloss` `cb1[0]`, G -> `DiffuseRougness` `cb1[8]` as material-level averages, **plus** a 4-block probe (R=0/1, G=0/1 into `t3` channels) to learn which `s3` channel is roughness and which is reflectivity; then pack per-pixel into `t3` | bake + one probe |
| G4 | **normal** slot exists but ships a dummy | write `V3_Glass_N` (BC5) into the block's `t2` slot in place of `dummy_nrm.ddsc`; drop `V3_Glass_S`'s B fix channel (it exists only to repair Arkham's DXT-compressed normal) | repack |
| G5 | **smudges** have no member | bake `glass_smudges` 0.2 as a dirt layer into `t0`'s alpha (or the `t3` property channel if G3's probe finds a dirt channel); the `RainOccluderTexture` `t40` is the wrong thing (it is rain occlusion, not dirt) | bake |
| G6 | **frame mask** unbound and unidentified | decode `V2_GLASS_MASK`'s pixels, compare against the canopy frame's UVs; if it is the frame, bake it as an opaque border into `t0`'s alpha | decode + bake |
| G7 | **cracking** absent in BmAK but present in JC3 | use JC3's own system: the crack maps are **already bound** on every shipped window (`t4`/`t5`), and `DamageMaskWeight`/`DamageRampWeight` weight them; the build's job is the damaged-window variant and the `Land_Window` part thresholds, not new textures | wiring |
| G8 | **canopy open/closed** | two `Window` blocks (closed + open) pointing at the same texture set, driven by the closest part mechanism (`Hood` +X 0..70 deg), since the source shares one material | build |

**What cannot be fixed on the material at all:** the glass scalars have **no per-block storage**.
Whatever the build does, `SpecGloss`, `SpecFresnel`, `DiffuseRougness`, `TintPower`, `MinAlpha`,
`Alpha`, `DamageMaskWeight` and `DamageRampWeight` are read from `cb1`, which no `.rbm` block
writes. So G3's "material-level averages" are themselves a bake into textures, not a member write,
unless a `CarPaintMM` stand-in is used instead of `Window` (then `m_SpecularGloss` `cb2[0]`,
`m_ClearCoat` `cb2[2]`, `m_Metallic` `cb2[1]` are writable, at the cost of losing the crack
system).

---

## 6. Closest system, gap, UNKNOWN

**Closest system:** the JC3 `Window` block + `windowdamage` shader. It is not a fallback - it is
a stronger system than BmAK's for damage (32 runtime crack points vs a static smudge), and it
already binds the crack maps. Its weakness is the opposite of BmAK's: **the parameters are named
but not writable per material, and the tint lives in the diffuse texture**.

| BmAK input | value | JC3 member | gap |
|---|---|---|---|
| tint | `[0.02579, 0.02579, 0.03]` | `t0` RGB x `TintPower` | no vector; bake |
| `Glass_Opacity` | 1.2 | `Alpha` / `MinAlpha` / `t0` alpha | no per-block write; repack |
| `Glass_Reflectivity` | 0.8 | `SpecGloss`, `SpecFresnel` | one-to-two split, UNKNOWN |
| `Glass_Roughness` | 1.1 | `DiffuseRougness` | value bridge underived |
| `V3_Glass_S` R/G | per-pixel | `t3` channels | channel map undecoded |
| `V3_Glass_A` | 4K map | `t0` alpha | repack |
| `glass_smudges` | 0.2 | none | bake |
| frame mask | 1024x512, unbound | none | identity UNKNOWN, then bake |
| cracking | none | `WindowContactPoints` + `t4`/`t5` | JC3 is ahead |

**UNKNOWN, with what settles each**

1. **Which `s3` channel is roughness vs reflectivity** - 4-block probe.
2. **Whether `cb1` values are ever written by the material path at all** - a runtime constant-buffer
   dump on a shipped car; if nothing writes them, G3 stays a bake.
3. **Whether `V2_GLASS_MASK` is the canopy frame** - read its pixels and compare with the frame's UV
   islands in `Batmobile_V3_Glass_A`.
4. **Whether the 40 B vertex tint is ever non-(1,1,1) on a shipped vehicle** - a vertex-colour
   census over the window blocks (my sample had the template constant only).
5. **`Glass_Roughness` 1.1's clamp** - `DiffuseRougness` is a float; whether >1 is clamped, and
   whether BmAK's own 1.1 was itself a multiplier rather than an absolute, is not in any file.

---

## 7. Checks run

| # | check | result |
|---|---|---|
| 1 | `MATERIALS.md` all 4 packages, `Batmobile_Glass` | 8 inputs, all `—` (empty) |
| 2 | `SKINS.md` / `MATERIALS.md` MIC rows | Opacity 1.2, Reflectivity 0.8, Roughness 1.1, smudges 0.2 |
| 3 | `TEXTURES.md` | A 4096² DXT1, N 4096² BC5, S 4096² DXT1 (R/G/B packing named), `V2_GLASS_MASK` 1024x512 unbound |
| 4 | decode of 6 shipped window `.rbm`s | strides (40,2); t0..t6 incl. `dummy_nrm` + 4 crack maps; 16 B pre-static not four floats |
| 5 | `window.fb.txt` / `windowdamage` / `windowsimple*` | `cb1` 7 used scalars + 2 damage weights; `cb2 WindowContactPoints` 32 points; s0/s2/s3 + s4/s5 on damage variants |
| 6 | `VALUES.json` | glass tint `[0.02579, 0.02579, 0.03]`, opacity_multiplier 1.0 |
| 7 | `ANIMATIONS.md` / `T8_PARTS.md` / `MESHES.md` | 20 canopy clips, translation 72.481 cm, no open-canopy mesh |

No game process was started, attached to or injected into; static read only.

## Reproduce

```bash
python - <<'EOF'
import sys,glob,struct,os
sys.path.insert(0,'Tools/scripts'); import rbm_geom as R
for f in sorted(glob.glob('E:/Modding/_shared/gamedata/JC3grab/b13b/unpacked/models/jc_vehicles/01_land/*/sportsmuscle_window_f_lod1.rbm'))[:1]:
    m=R.decode(open(f,'rb').read())
    for b in m.blocks:
        if R.BLOCK_NAMES.get(b.type_hash)!='Window': continue
        print(b.strides, [t.split('/')[-1] for t in b.textures])
        print('pre_static', b.pre_static[:16].hex())
EOF
sed -n '30,70p' Tools/JCMR-src/assets/jc3/shaders/windowdamage.fb.txt
```
