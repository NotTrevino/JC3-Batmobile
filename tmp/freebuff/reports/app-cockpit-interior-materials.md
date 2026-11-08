# BmAK cockpit / interior materials -> JC3 (T-21, POL-1)

**Scope.** `Batmobile_V3_Cockpit_MIC` (cockpit tub, dash, cowl), `BatmobileV3_Cockpit_Seat`,
`Batmobile_V3_Glass_INST` (canopy), `Cockpit_Master_Flip_Data` (centre screen), the
`Batmobile_Worn_NoRain` roof liner, and the yoke. What BmAK authors, what
`Working/Appearance/build_bud1` currently gives the interior, and the route for everything that
does not land.

**Short version.** The interior's **material identity** transfers - all three interior MICs map
onto JC3 `CarPaintMM` blocks, and `build_bud1` already carries `cockpit_d`, `cockpit_m_msk` and
`cockpit_n` as `.ddsc`. What does not transfer is the **look those materials are built from**:
BmAK's interior albedo is a *ramp lookup* (`Colour_Ramp_Map`), its highlight is *anisotropic*, its
roughness is *per-pixel*, and its centre screen ships *no texture at all*. Geometry transfers
except the yoke, which **does not exist in BmAK** (4 faces in the hand box).

**11 of 15 interior components have no faithful carrier** (§5).

---

## 1. What BmAK authors - decoded

[decoded: `COCKPIT.md` §1 (slots, face counts, material rows), `TEXTURES.md` (dims/formats),
`SKINS.md`/`COLOUR_PARAMS.md` (parameter values).]

### 1.1 Geometry, by material slot

| component | slot | faces (LOD0) | bbox, JC3 metres |
|---|---|---:|---|
| cockpit tub, dash, cowl | **10** `Batmobile_V3_Cockpit_MIC` | 27,334 | x -0.4042..0.4044, y 0.6761..2.0286, z -2.2319..-0.5269 |
| driver-facing instrument panel (subset of slot 10) | 10 | 1,043 (720.3 cm2) | x -0.3456..0.3457, y 1.3148..1.6005, z -1.8981..-1.5097 |
| seat - cushion, bolsters, rear lip | **11** `BatmobileV3_Cockpit_Seat` | 13,014 | x -0.3759..0.376, y 0.8041..1.913, z -1.7041..-0.6319 |
| centre screen | **12** `Cockpit_Master_Flip_Data` | 100 | 0.3188 x 0.1512 m; centre (0, 1.4857, -1.7552) |
| canopy glass - windscreen + side windows | **1** `Batmobile_V3_Glass_INST` | 3,532 (1,716 on `CockPit_Mesh`) | windscreen z -1.9143; side x -0.2942 / 0.2943 |
| roof inner liner | **18** `Batmobile_Worn_NoRain` | 524 | liner y 1.9661 over the driver |
| yoke / steering control | - | **absent** | hand box \|x\|<0.17, y 1.00..1.30, z -1.60..-1.10 holds **4 faces of any material** |

### 1.2 Materials and their maps

| material | parent master | maps (decoded) | scalars |
|---|---|---|---|
| `Batmobile_V3_Cockpit_MIC` | `Batmobile_V3_Body_NoRain_MAT` | `Colour_Ramp_Map` = `Batman_BM3_V2_Lacquered_Underlayer_Ramp`; `Material_Separation_Mask` = `Int_Cockpit_M`; `Normal_Map` = `Int_Cockpit_N`; `Anisotropic` = `Aniso_ramp_Lacquered`; `Material1_Microdetail_N` = `neutral_normal` | Metalicity 0.9000 |
| `BatmobileV3_Cockpit_Seat` | `Batmobile_Hardleather_Master_MAT` | `Colour_Map` = `Int_Cockpit_D`; `Colour_Ramp_Map` = `Batman_BM3_V2_Leather_Ramp`; `Emissive` = `Int_Cockpit_E`; `Ref_n_Rough_Map` = `Int_Cockpit_S`; `Normal_Map_Lacquer` = `Int_Cockpit_N` | EmissiveMultiply 15.0, Reflectivity_Multiplier 1.2, ClearCoat [1,1,1,1], Fake 1.0, fake 0.0 |
| `Batmobile_V3_Glass_INST` | `Batmobile_Glass` | `Normal` = `V3_Glass_N`; `OpacityMap` = `V3_Glass_A` | Glass_Opacity 1.2, Glass_Reflectivity 0.8, Glass_Roughness 1.1, glass_smudges 0.2 |
| `Cockpit_Master_Flip_Data` | master `Material` | **none** - no Diffuse/Specular/Power/Emissive, no texture parameters | - |

| texture | dims | format | note |
|---|---|---|---|
| `Batmobile_V3_Int_Cockpit_D` | 4096x4096 | PF_DXT1 | seat albedo |
| `Batmobile_V3_Int_Cockpit_N` | 4096x4096 | PF_DXT1 | normal (both materials) |
| `Batmobile_V3_Int_Cockpit_M` | 4096x4096 | PF_DXT1 | material separation mask |
| `Batmobile_V3_Int_Cockpit_S` | 4096x4096 | PF_DXT1 | reflectivity/roughness - **R channel dead (std 0.000), packing unknown** (`coverage.md:60`) |
| `Batmobile_V3_Int_Cockpit_E` | 1024x1024 | PF_DXT1 | emissive mask |
| `Batman_BM3_V2_Leather_Ramp` | 64x512 | PF_DXT1 | colour ramp |
| `Batman_BM3_V2_Lacquered_Underlayer_Ramp` | - | - | colour ramp; **file missing on disk** (`progress.md` D10 note) |

**Derived.** The interior's colour is not in a diffuse texture on the tub side at all: slot 10 has
**no `Colour_Map`**, only a ramp plus a separation mask. Two 4096 px maps (`M`, `N`) carry the
look, the albedo is a lookup. That single fact is why the interior is harder than the body paint,
which at least ships `_body_dif`.

---

## 2. What `build_bud1` gives the interior today - decoded

[decoded: `Working/Appearance/build_bud1/assembly.json`, `coverage.md`, `ddsc/`, `progress.md`.]

| artefact | present | evidence |
|---|---|---|
| `Cockpit_MIC`, `Cockpit_Seat`, `Cockpit_Master_Flip_Data` material entries | yes | `assembly.json` names all three |
| `cockpit_d.ddsc` | yes | `ddsc/batmobile_v3_int_cockpit_d.ddsc` |
| `cockpit_n.ddsc` | yes | `ddsc/batmobile_v3_int_cockpit_n.ddsc` |
| `cockpit_m_msk.ddsc` | yes | `ddsc/batmobile_v3_int_cockpit_m_msk.ddsc` |
| `cockpit_s.ddsc` (roughness/reflectivity) | **no** | only 28 ddsc files ship; no `_s` |
| `cockpit_e.ddsc` (emissive) | **no** | same |
| cockpit `.rbm` | **no** | `build_bud1/` holds `body_lod1..5.rbm` + 20 wheel `.rbm`; the interior geometry is not packaged |
| seat material chain | `BatmobileV3_Cockpit_Seat -> Batmobile_Hardleather_Master_MAT (no dump)` | `coverage.md:4` |
| tub material chain | `Batmobile_V3_Cockpit_MIC -> Batmobile_V3_Body_NoRain_MAT (no dump)` | `coverage.md:173` |

`progress.md` overall: materials 19/19 transferred, textures 17 transferred / 7 partial /
14 excluded. The interior's two named partials are `Int_Cockpit_E` (`route R2`) and
`Int_Cockpit_S` (`drop D3`).

**Derived, and it matters.** The interior is transferred **as material entries and three of its
five maps**, but there is no interior `.rbm` in the build at all. So the interior currently
"exists" as data that has nowhere to render: no mesh, no cockpit block, no emissive.

---

## 3. The JC3 carrier, precisely

[decoded: `Research/JC3Grab/CB0_SLOTS.md` §3-§4, `COLOUR.md` §2, `GEOMETRY.md`.]

`CarPaintMM` is one block type with 18 float4 + 7 support floats (`cb2`), 4 float4 + 3 floats
(`cb6`) and 12 texture slots:

| JC3 member | bind/offset | what the interior needs it for |
|---|---|---|
| `m_SpecularGloss` | `cb2[0]` @0 | gloss scalar - stands in for the un-transferred `Int_Cockpit_S` |
| `m_Metallic` | `cb2[1]` @16 | tub Metalicity 0.9000 |
| `m_ClearCoat` | `cb2[2]` @32 | seat ClearCoat [1,1,1,1] |
| `m_Emissive` | `cb2[3]` @48 | seat emissive (EmissiveMultiply 15.0) |
| `m_DiffuseWrap` | `cb2[4]` @64 | albedo modulator - **role UNKNOWN** (`CB0_SLOTS.md` §5) |
| `m_TintColorR/G/B` | `cb6[0..2]` @0/16/32 | dynamic tint - must stay 1,1,1 if albedo is pre-baked |
| gloss/metallic/coat overrides | `cb6[4].x/.y/.z` | per-spawn overrides |
| `s0` DiffuseMap | `t0` | baked interior albedo |
| `s1` NormalMap | `t1` | `Int_Cockpit_N` |
| `s2` PropertyMap | `t2` | the only per-pixel material channel family (`COLOUR.md` §2: "channel selectors") |
| `s3` TintMap | `t3` | `Int_Cockpit_M` separation mask |
| `s4`/`s5` damage, `s6` dirt, `s7`-`s11` decals | - | not interior |

Adjacent JC3 systems the interior needs:

* **`Window` block** - 12,028 glass blocks decoded byte-exact (`GEOMETRY.md:25`), "the canopy is a
  material switch" (`G2X.md`). Its *members are not decoded* - that is gap R3.
* **`VehicleParts` part types** - `Land_Seat`, `Land_Window`, `Land_Steering_Wheel` all exist in
  the shipped part tables (`PARTS_TABLE.md`; e.g. `oldjeep_steeringwheel -> Land_Steering_Wheel`,
  `oldjeep_f_l_seat -> Land_Seat`). This is how interior furniture becomes a damageable part.
* **`CarLight` block** - emissive/lamp geometry, 23,395 blocks (`GEOMETRY.md:25`).

---

## 4. Classification, component by component

Status vocabulary: **transferred** = the decoded value reaches a JC3 member that means the same
thing; **partial** = a carrier exists but a value is lost; **excluded** = no carrier today.

| # | interior component | source value | `build_bud1` today | status | reason |
|---:|---|---|---|---|---|
| 1 | cockpit tub / cowl / dash shell | slot 10, 27,334 faces, Metalicity 0.9 | material entry only, no `.rbm` | **partial** | geometry not packaged; albedo is a ramp lookup, highlight is aniso |
| 2 | driver-facing instrument panel | slot 10 subset, 1,043 faces, 720.3 cm2 | same block | **transferred** | same material as the tub; no separate BmAK material to lose |
| 3 | seat base | slot 11, 13,014 faces; D + N + ClearCoat | `cockpit_d`, `cockpit_n` shipped | **transferred** | albedo and normal land; `Reflectivity_Multiplier 1.2` is dropped by D2 (see `app-reflectance-f0.md`) |
| 4 | separation mask | `Int_Cockpit_M` 4096x4096 DXT1 | `cockpit_m_msk.ddsc` | **transferred** | bound as `s3` TintMap |
| 5 | seat roughness / reflectivity map | `Int_Cockpit_S` 4096x4096, R channel dead | not shipped | **partial** | no per-pixel roughness in `CarPaintMM`; only `m_SpecularGloss` |
| 6 | seat emissive | `Int_Cockpit_E` 1024x1024 x 15.0 | not shipped | **partial** | `m_Emissive` exists but the emissive **mask channel is not decoded** |
| 7 | leather colour ramp | `Batman_BM3_V2_Leather_Ramp` 64x512 | excluded (D10) | **excluded** | no ramp slot; ramp files also missing on disk |
| 8 | lacquered underlayer ramp | `Batman_BM3_V2_Lacquered_Underlayer_Ramp` | excluded (D10) | **excluded** | same; this is the tub's *only* albedo input |
| 9 | anisotropic ramp | `Aniso_ramp_Lacquered` | excluded (D4/D5) | **excluded** | no anisotropy member anywhere in JC3 (see `app-anisotropic-highlights.md`) |
| 10 | interior micro-detail | `neutral_normal`, `Material1_Microdetail_N`, sizes | excluded (bake P1/P2) | **excluded** | no detail-tiling slot; must be baked into `s1` |
| 11 | centre screen content | slot 12, 100 faces; **no textures at all** | material entry only | **excluded** | BmAK ships the panel, not the picture; nothing to transfer |
| 12 | yoke / steering control | **absent in BmAK** | absent | **excluded** | 4 faces in the hand box; the source has no yoke |
| 13 | canopy glass response | Opacity 1.2, Reflectivity 0.8, Roughness 1.1 | material entry only | **partial** | `Window` block members undecoded (R3); carried as material-level tint |
| 14 | glass smudges | `glass_smudges` 0.2 | excluded (D11) | **excluded** | no smudge member; would need a mask baked into the glass alpha |
| 15 | roof inner liner | slot 18, 524 faces, `Batmobile_Worn_NoRain` | body paint block | **transferred** | ordinary `CarPaintMM` block |

**Counts.** 15 components: **4 transferred** (2, 3, 4, 15), **4 partial** (1, 5, 6, 13),
**7 excluded** (7, 8, 9, 10, 11, 12, 14).

---

## 5. Routes for everything not transferred - with member paths

### 5.1 The four partials

**#1 tub albedo (ramp) -> bake to `s0`.** Sample `Batman_BM3_V2_Lacquered_Underlayer_Ramp`
against the tub's base colour offline and write a 4K albedo into `CarPaintMM` `s0`
(`textures[0]`, `t0 DiffuseMap`). Hold `cb6[0..2]` (`m_TintColorR/G/B`) at 1,1,1 so the bake is
not re-tinted, and leave `cb2[4]` (`m_DiffuseWrap`) at the donor's value - its role is UNKNOWN
(`CB0_SLOTS.md` §5), so changing it would be a blind edit. **Gap closed:** albedo. **Gap left:**
the ramp's hue shift vs view angle is gone.

**#5 seat roughness -> `s2` channel packing, fallback `cb2[0]`.** The `Int_Cockpit_S` payload is
4096x4096 DXT1, so one 4-channel target is enough: pack roughness into one channel of the
`PropertyMap` (`s2`, `t2`) and keep reflectivity in another. **But** which `s2` channel is which is
not decoded (`COLOUR.md` §2 calls the map "channel selectors" and stops there), so the honest
route is two steps: (a) ship `m_SpecularGloss` `cb2[0].x` as the material-level average now;
(b) one probe - write R=0/1, G=0/1, B=0/1, A=0/1 into four otherwise identical blocks and read
back which slot moves. **Gap left:** per-pixel variation until (b) lands.

**#6 seat emissive -> `m_Emissive` + `SupportSoftTint`, mask baked.** `m_Emissive` is `cb2[3]`
(float4), intensity is carried by that vector's magnitude; `SupportSoftTint` is `cb2[19].z`.
`Int_Cockpit_E` is a 1024 px mask, and no JC3 emissive-mask channel is decoded, so bake it: either
multiply the mask into the albedo's emissive region (a dark leather with a glow baked in) or write
a 1-channel mask into `s0`'s alpha if `SupportSoftTint` turns out to read it. **Gap left:** a
runtime-switchable glow (BmAK's is on/off with the interior lights).

**#13 canopy glass -> `Window` block, or `CarPaintMM` in the interim.** `Window` is the correct
carrier (12,028 blocks decoded byte-exact, canopy is a material switch), but its members are not
decoded, so today glass can only be a `CarPaintMM` block with `m_SpecularGloss`/`m_ClearCoat`/
`m_Metallic` approximating Opacity 1.2 / Reflectivity 0.8 / Roughness 1.1. **Gap left:** the three
glass scalars have no named member until the `Window` layout is decoded - that is the R3 card's
job, and it is a decode task, not a build task.

### 5.2 The seven excluded

| # | component | route | member path | what closes it |
|---:|---|---|---|---|
| 7 | leather ramp | bake the 64x512 lookup into the seat albedo `s0` at the leather base colour | `CarPaintMM` `s0` + `cb6[0..2]` at 1 | bake (offline) |
| 8 | lacquered underlayer ramp | same, into the tub's `s0`; the ramp file is missing on disk, so re-extract it from the package or author it from `Material3_Anisotropic_*_Colour` | `s0` | re-extract + bake |
| 9 | anisotropic ramp | bake the stretched highlight into `s1` (normal) as a directional smear, per `app-anisotropic-highlights.md` | `s1` `NormalMap` | bake |
| 10 | micro-detail | bake `neutral_normal`/`Micropattern_A_Normal` into `s1` at `MicroDetail_size` 15 and `MicroDetail_Material3_Size` 250 tiling | `s1` | bake |
| 11 | screen content | **author** a 0.3188 x 0.1512 m emissive texture (BmAK has none) and bind `s0` + `m_Emissive`, or make the panel a `CarLight` block | `s0` / `cb2[3]` / `CarLight` | author |
| 12 | yoke | **author** the geometry as a `VehicleParts` part with `damage_type = Land_Steering_Wheel` (shipped type, `PARTS_TABLE.md`), grip pose from the `Driver` socket (hip (-0.0025, 0.8647, -1.0654), cushion 24 mm below) | `VehicleParts.parts[].damage_type` | author |
| 14 | glass smudges | bake into the glass opacity mask (`V3_Glass_A`) as a dirt layer, or into `s2`'s dirt channel if the dirt path is on | glass opacity map / `s2` | bake |

### 5.3 Two build-level fixes that are not per-component

1. **There is no interior `.rbm`.** `build_bud1` ships body and wheels only. Slots 10/11/12/18 need
   their own block set in the mesh's `.rbm` - that is a packaging action, and without it every row
   above is data with no surface.
2. **`Land_Seat` is the damage type to use for slots 11 and 10**, not `Land_Body`:
   the part table already has `Land_Seat` (and `Land_Steering_Wheel` for #12), so the interior
   becomes a damageable part through a shipped type rather than a new one.

---

## 6. Closest system, gap, and the number

**Closest system for the interior as a whole:** `CarPaintMM` - 12 texture slots and 25 named
constant slots, enough for albedo, normal, mask, gloss, metallic, clearcoat and emissive, which is
exactly the set the interior needs. BmAK's interior is *also* a CarPaint-family material (its tub
even inherits the body's `Batmobile_V3_Body_NoRain_MAT`), so the mapping is structurally right;
only the ramp-driven inputs have nowhere to live.

| BmAK input | value | JC3 slot | gap |
|---|---|---|---|
| `Colour_Ramp_Map` x2 | 64x512 + missing file | none | colour-by-lookup has no carrier; bake |
| `Aniso_ramp_Lacquered` | texture | none | no anisotropy member in any of 961 headers |
| `Int_Cockpit_S` | 4096x4096 DXT1, R channel dead | `m_SpecularGloss` scalar only | per-pixel roughness |
| `Int_Cockpit_E` x 15.0 | 1024x1024 mask | `m_Emissive` float4 | mask channel |
| Glass_Opacity / Reflectivity / Roughness | 1.2 / 0.8 / 1.1 | `Window` block | members undecoded |
| `Material_Separation_Mask` | 4096x4096 | `s3` TintMap | **none** |
| seat albedo / normal, liner | D, N | `s0`, `s1` | **none** |
| yoke | absent in source | `Land_Steering_Wheel` part type | author geometry |
| screen | absent in source | `m_Emissive` / `CarLight` | author texture |

**Components still without a faithful carrier: 11** (partials #1, #5, #6, #13 + excluded #7, #8,
#9, #10, #11, #12, #14). Of those, **6 need only a bake** (1, 7, 8, 9, 10, 14), **2 need authoring**
(11, 12), **2 need a decode** (5, 6 - the `s2` channel map and the emissive mask channel), and
**1 needs the `Window` layout** (13).

---

## 7. UNKNOWN

1. **`s2` PropertyMap channel semantics** - which channel is roughness, reflectivity, dirt and
   mask. Settle with a 4-block probe (§5.1 #5).
2. **The emissive mask channel** - `SupportSoftTint` reads something; no header names it.
3. **`Window` block members** - the block decodes byte-exact but no member is named (R3).
4. **`m_DiffuseWrap` vs `ModelDiffuseColor`** - which multiplies `s0` (`CB0_SLOTS.md` §5).
5. **Whether a `CarPaintMM` block inside a cockpit mesh needs `IS_DEFORM`** - the body blocks are
   deform blocks; the interior is rigid, and no shipped interior-like block was measured here.
6. **`Batman_BM3_V2_Lacquered_Underlayer_Ramp`** - the file is not on disk, so the tub's albedo
   cannot be baked faithfully until it is re-extracted or re-authored from
   `Material3_Anisotropic_broad/thin_Colour`.

---

## 8. Checks run

| # | check | result |
|---|---|---|
| 1 | `COCKPIT.md` slots/faces/bboxes | 5 interior slots + yoke absent (4 faces in hand box) |
| 2 | `TEXTURES.md` dims | D/N/M/S 4096x4096 DXT1, E 1024x1024 DXT1, Leather_Ramp 64x512 DXT1 |
| 3 | `build_bud1/assembly.json` | `Cockpit_MIC`, `Cockpit_Seat`, `Cockpit_Master_Flip_Data`, `cockpit_d/m_msk/n.ddsc` present |
| 4 | `build_bud1/ddsc` | 28 files; **no** `cockpit_s`, **no** `cockpit_e` |
| 5 | `build_bud1` mesh list | `body_lod1..5` + 20 wheel rbms; **no cockpit rbm** |
| 6 | `coverage.md` | seat and tub chains exist with "no dump" masters; `Int_Cockpit_S` R channel dead |
| 7 | JC3 carriers | `CarPaintMM` cb2/cb6 slots; `Window` 12,028 blocks; `Land_Seat`/`Land_Steering_Wheel` part types |

No game process was started, attached to or injected into; static read only.

## Reproduce

```bash
ls Working/Appearance/build_bud1/ddsc | grep cockpit      # d, m_msk, n only
grep -n "Cockpit" Working/Appearance/build_bud1/assembly.json | head
sed -n '1,40p;170,200p' Working/Appearance/build_bud1/coverage.md
sed -n '1,40p' Research/BatmobileGrab/COCKPIT.md
```
