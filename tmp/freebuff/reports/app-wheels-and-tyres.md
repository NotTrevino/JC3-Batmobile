# BmAK wheels and tyres -> JC3 (wheel appearance)

**Scope.** `BatmobileV3_Wheel_V2_MIC` (rim/hub/tread block), `Batmobile_V3_Tyre_V2_MIC`
(tyre), `Batmobile_V3_Discbreak_MIC` + `Batmobile_V3_Discbreak` (brake disc, front/rear glow),
`Batmobile_V3_Emissive` with `Wheel_E` / `Wheel_Lights_M` / `Wheel_Lights_N` (hub lights), the
front/rear wheel arches, and the `LWheelLight`…`_bottom` light rows (T-L31..T-L34). Compared
against `Working/Appearance/build_parts` and `Builds/bm-RC2`.

**Verdict.**

* **Geometry is carried and verified**: RC2's `wheels.md` reads radius **0.68275 m front /
  0.68265 m rear** and width **0.73195 / 0.73165 m** straight from `land_global`, matching
  TYRES.md's axle means to 0.05 mm; spin axis `+x` on all four, corners in the fleet's
  FL, FR, RR, RL order, per-corner error ≤ 0.55 mm.
* **Three of the four wheel materials land** as `CarPaintMM` blocks with their diffuse and
  normal maps shipped (`wheel_v2_d/n`, `tyre_v2_d/n`, `brake_disc_d/n`), plus
  `wheel_lights_m_msk/n`.
* **Every per-pixel roughness/metalness map is lost**: the build *reads* `Wheel_V2_R` and
  `Tyre_V2_R` to compute two scalars each and **does not ship either texture**
  (9 ddsc files, neither is one of them).
* **The front/rear split flares are contradictory across the build's own files**:
  `build_lights/lights_manifest.json` marks T-L31..T-L34 `mapped: true`,
  `Working/Translation/COMPROMISES_T.md` lists all four as `out` / *UNAPPROVED*, and BmAK's
  rear wheels carry **no lamp bone at all** (§4).
* **7 of 14 wheel components carry a value no JC3 member reproduces** (rows 2, 3, 4, 5, 7, 8,
  11 in §5), and two further exclusions (the split flares, the mud/wet set) are unsettled in the
  build's own files.

---

## 1. BmAK's wheel components, decoded

| # | component | material / slot | faces | parent master |
|---:|---|---|---:|---|
| 1 | rim / hub / inner wheel | `BatmobileV3_Wheel_V2_MIC`, slot **0** | 62,668 | `Batmobile_V3_Wheel_V2_MAT` |
| 2 | tyre | `Batmobile_V3_Tyre_V2_MIC`, slot **9** | 18,720 | `Batmobile_V3_Tyre_V2_MAT` |
| 3 | brake disc | `Batmobile_V3_Discbreak_MIC`, slot **13** | 3,712 | `Batmobile_V3_Discbreak` |
| 4 | hub lights | `Batmobile_V3_Emissive` (`Wheel_E`, `Wheel_Lights_M/N`) | - | `Batmobile_V3_Emissive` |
| 5 | front arches | body `Batmobile_V3_WheelArchs_NEW_MIC` | - | `Batmobile_Worn` chain |
| 6 | rear arches | body (same material; separate parts) | - | - |

**Factors, decoded** (`build_parts/coverage.md` §§116, 251, 650):

| material | scalars | shipped static values |
|---|---|---|
| Wheel_V2 | `Metalicity_Multiplier` 0.8, `Reflectivity_Multiplier` 1.0, `Roughness_Multiplier` 0.25, Mud 2.0/0.5/1.0/1.0 | `SpecularGloss` **0.6088** (= 1 − mean R of `Wheel_V2_R`), `Metallic` **0.3561** (= mean B), `ClearCoat` 0 |
| Tyre_V2 | `Diffuse_Adjust` 1.3, `Roughness_Multiplier` 1.7, `Reflectivity_Multiplier` 0.2, `RainReflectivityMul` 2.0, `RainRoughnessMul` 0.5, `Rain_Constant` 1.0, `EMP` 0.0, `EMP_Emissive_Multiplier` **350** | `SpecularGloss` **0.052**, `Metallic` **0.1184** |
| Discbreak | `Emissive_Intensity` 1.5, `Metalicity_Multiplier` 0.8, `Reflectivity_Multiplier` 1.0, `Discbreak_front`, `Discbreak_back`, Mud 1.0/0.2/0.0/1.2 | `SpecularGloss` **0.9586**, `Metallic` **0.431** |
| Emissive/wheel lights | `Wheel_E` emissive map, `Wheel_Lights_M` (RGB → channels 1-3), `Wheel_Lights_N` | mapped: s1 N, s2 M, s3 M |

**The chain binds no colour map.** Wheel_V2's `s0`/`s1` are name-match fallbacks
(`fallback:name-match Batmobile_V3_TEXTURES_Wheel_V2_D`, `…_N`), and `s2`/`s3` are the dummy black
mpm - flags `0x0000`, all support floats 0.

---

## 2. Geometry and UV facts

[decoded: `TYRES.md` (vertex-owned measurement through the one transform), `Builds/bm-RC2/verify/wheels.md` (built values), T-G1/T-G2/T-G3 rows.]

| quantity | BmAK measured | JC3 carrier | built value | difference |
|---|---|---|---|---|
| tyre tread Ø | **1.3652-1.3657 m** (headline 1.366) | `land_global.front/rear_wheels.radius` | 0.68275 / 0.68265 → Ø **1.36550 / 1.36530** | ≤ 0.05 mm vs axle mean |
| shoulder Ø (max radial) | 1.3711-1.3714 | none | - | shoulder bulge 5.7-5.9 mm is not modelled |
| tyre width | **0.7314-0.7325 m** (headline 0.731) | `…wheels.width` | 0.73195 / 0.73165 | ≤ 0.55 mm per corner |
| rim / hubcap Ø | **1.0254** (`Wheel_Frnt_Left_Fan`, 32 faces, max radial 0.5127) | `…wheels.rim_radius` | 0.539013 front / 0.538934 rear (**untouched shipped values**) | 0.5127 vs 0.539 → **26 mm**, printed not asserted |
| inner wheel structure Ø | 1.5962 (`Wheel_Frnt_Left_Disc`), lowest vertex y 0.0699 (5.0 cm above ground) | none (geometry only) | carried as geometry | - |
| tyre faces, front / rear | **6,700 / 7,564** | wheel `.rbm` per corner | `wheel_f_*` / `wheel_r_*` files, decimated per LOD | carried, decimation effect UNKNOWN |
| tread-to-ground | rear +0.0000, front +0.0021 | `stations.json` radius | - | ≤ 2.1 mm |
| spin axis | `x` (lateral) | part rotation | identity 3×3 on all four | 0° |
| corner order | - | part order | FL(26), FR(27), RR(12), RL(11) | fleet order |
| hardpoints | - | `base_wheel_hardpoint_positions` | front z −2.570, rear z +2.459; x ±1.208 / ±1.285; y 0.7047 | wheelbase 5.029, track 2.416 / 2.569 |
| tyre bone naming | `Wheel_Front_Left_Vis` (tyre) vs `Wheel_Frnt_Left_Disc` (structure) | - | - | **`Front` vs `Frnt`**: only `*_Vis` is the tyre |

**UV facts.** Both tyre and rim chains bind **no** colour or normal map, so there is no decoded
BmAK UV-to-texture edge: the build's `s0`/`s1` are name-match fallbacks, and `s2`/`s3` are dummies.
`TYRES.md` records no UV data at all; the tyre's UV layout is therefore **UNKNOWN** here, and the
only UV evidence in the build is that the fallback textures are the ones the material is named for
(`Wheel_V2_D/N`, `Tyre_V2_D/N`), which matches the `_R` variants the scalars were derived from.

**The rim radius gap is the number to watch**: the shipped `rim_radius` 0.539 m is 26 mm larger
than BmAK's `Fan` radius 0.5127 m; `TYRES.md` says its 1.0254 m is a *hubcap diameter*, not a rim
measure, so the two are not the same quantity and nothing was asserted either way.

---

## 3. What the build ships

### 3.1 `Working/Appearance/build_parts`

| artefact | content |
|---|---|
| wheel meshes | `wheel_f_l/f_r/r_l/r_r_lod1..5.rbm` = **20 files**, 5 LODs per corner |
| other parts | body_lod1..5, cannon, jet, machine_gun, missile pods, riot suppressor, turret, 4 aero flaps |
| wheel textures | `batmobile_v3_textures_wheel_v2_d/n`, `tyre_v2_d/n`, `brake_disc_d/n`, `wheel_lights_m_msk/n`, `wheelarch_n` |
| **missing** | `Wheel_V2_R`, `Tyre_V2_R`, `BRAKE_DISC_R` (all three were *read* for the scalars, none shipped), `Wheel_Lights_D`, `Tyre_V2_EMP` |

### 3.2 `Builds/bm-RC2`

| what | shipped | note |
|---|---|---|
| wheel LODs | `sportsmuscle_wheel_f_l_lod1/lod3`, `_f_r_lod1/lod3`, `_r_l_lod1/lod2/lod5`, `_r_r_lod1/lod2/lod5` | **lod2/4/5 of the front wheels are `unlisted`** - "the wheel `.lod` never names them" (receipt `unknown`) |
| damage-swap meshes | `…_wheel_*mshswap.lod` + lod1..4 | used by the no-tyre/wheel-explosion effects |
| **wheel arches** | `sportsmuscle_wheel_f_*_arch.lod` + lod1..3, same for rear | **front arches hoisted onto `sportsmuscle_engine`, rear arches onto `sportsmuscle_body`** (receipt `hoisted_off_wheels`) |
| wheel textures | `textures/batmobile/batmobile_v3_{brake_disc_d,n · tyre_v2_d,n · wheel_v2_d,n · wheel_lights_m_msk,n · wheelarch_n}.ddsc` | 9 files, same set as build_parts |
| effects | `effects/jc_vehicles/wheels/{no_tire,rear,trail}/*.effc` (asphalt..water), `wheel_explosion_notiremesh.effc` | closest JC3 system for a bare rim |
| light rig | `v0300_…_lights.vmodc` (generated, from bm-007) + `car_lights_kensington_modern_*.ddsc` | the wheel-lamp rows live here |
| vehicle transform | wheel parts still carry the Serpente translations (max delta **1.0130 m**), **dormant** | wheels are placed from `land_global.base_wheel_hardpoint_positions`; harmless at run time, a real data inconsistency (`wheel_offset_effect.md`) |

---

## 4. Front-versus-rear differences BmAK has

| # | difference | decoded value | carried? |
|---:|---|---|---|
| 1 | **tyre topology** | front 6,700 faces, rear 7,564 (+864) | per-corner `.rbm`, but one texture set; whether the tread pattern difference survives decimation is UNKNOWN |
| 2 | **brake-disc glow split** | `Batmobile_V3_Discbreak` carries `Discbreak_front` and `Discbreak_back` as separate scalars | **no** - `CarPaintMM` has one `m_Emissive` per block, not a front/rear pair |
| 3 | **arch ownership** | front arch parts vs rear arch parts, separate geometry | yes, and RC2 splits them across two parts (`engine` front / `body` rear) |
| 4 | **wheel lamps are front-only** | `LWheelLight`/`RWheelLight` sit on `Wheel_Frnt_Left_Disc` / `Wheel_Frnt_Right_Disc`; the rear wheels have **no lamp bone** - the rear-adjacent lights are `BrakeLightL/R` on `SUSP2_Wheel_Rear_Left/Right` with `VEHLT_TailLight`/`TailLight` | partially (§5 rows 8-10) |
| 5 | **split flares** | `_top` / `_bottom` variants of the front wheel lamps exist only in some archetypes (base, Funhouse, MK2 have them; **Joker has none**) - T-L31..T-L34 | **contradictory** (§5) |

**The rear has no hub light at all** - so "rear-wheel lights" in the ledger are the *rear axle's
brake lights on the suspension bones*, not lamps inside the wheel. That is the fact the T-L31..34
rows assume away.

---

## 5. Component table: carrier or none

| # | component | JC3 carrier | status | reason |
|---:|---|---|---|---|
| 1 | tyre (albedo + normal) | `CarPaintMM` `s0`/`s1` | **transferred** | `tyre_v2_d/n` shipped; `Diffuse_Adjust` 1.3, `Roughness_Multiplier` 1.7 → `SpecularGloss` 0.052 |
| 2 | tyre roughness / metalness (`Tyre_V2_R`) | `m_SpecularGloss`/`m_Metallic` scalars only | **partial** | per-pixel lost; the `_R` texture is not shipped |
| 3 | tyre EMP glow (`EMP` 0.0, `EMP_Emissive_Multiplier` 350) | none | **excluded** (D14) | story EMP effect |
| 4 | rim / hub (albedo + normal) | `s0`/`s1` | **partial** | chain binds no colour map; `s0`/`s1` are name-match fallbacks, not authored bindings |
| 5 | rim roughness / metalness (`Wheel_V2_R`) | `m_SpecularGloss` 0.6088 / `m_Metallic` 0.3561 | **partial** | per-pixel lost |
| 6 | brake disc (albedo + normal) | `s0`/`s1` | **transferred** | `brake_disc_d/n` shipped; `Emissive_Intensity` 1.5 → `m_Emissive` |
| 7 | brake disc roughness (`BRAKE_DISC_R`) | `m_SpecularGloss` 0.9586 / `m_Metallic` 0.431 | **partial** | per-pixel lost (D3) |
| 8 | `Discbreak_front` / `Discbreak_back` | none | **excluded** | no front/rear split in one block |
| 9 | hub lamp `LWheelLight` / `RWheelLight` | JC3 lights module (`vmodc`, `CarLight`), T-L13 / T-L20 | **transferred** | `lights_manifest.json`: `mapped: true`, positions (−1.2076, 0.9627, −2.0630) etc. |
| 10 | split flares `LWheelLight_top/_bottom`, `RWheelLight_top/_bottom` (T-L31..L34) | same module, "flare rides the wheel lamp row" | **excluded / contradictory** | manifest says mapped, `COMPROMISES_T.md` says `out` + *UNAPPROVED*, loss "flare top/bottom colour" |
| 11 | wheel-lights material (`Wheel_E`, `Wheel_Lights_M/N`) | `s1` N, `s2` M channels, `s3` M tint, `m_Emissive` | **partial** | emissive mask channel undecoded |
| 12 | front / rear arches | separate parts + `WheelArch` block/`wheelarch_n` | **transferred** | hoisted to two different parents |
| 13 | tyre tread difference (front 6,700 vs rear 7,564 faces) | geometry | **transferred** (geometry) | one texture set, so the *look* of the difference is UNKNOWN |
| 14 | mud / wet on tyre and rim (`Mud_*`, `Rain_*`) | none (JC3 dirt is dynamic) | **excluded** (D1/D8) | chapter-scripted in BmAK |

**Counts.** 14 rows: **5 transferred** (1, 6, 9, 12, 13), **5 partial** (2, 4, 5, 7, 11),
**4 excluded** (3, 8, 10, 14).

**7 components carry a BmAK value that no JC3 member reproduces: 2, 3, 4, 5, 7, 8, 11.** Of
those, **4 need a bake** (2, 5, 7, 11), **1 needs the authored bindings** rather than a name-match
fallback (4), **1 needs a block split** (8), **1 is dropped by rule** (3, EMP). Two further
exclusions - **10** (the four split flares) and **14** (mud/wet) - are unsettled: one is
self-contradictory inside the build, the other is dropped by rule but still present in BmAK's
material.

---

## 6. Open items, with the fix

| # | open item | fix | needs |
|---:|---|---|---|
| O1 | `Wheel_V2_R` / `Tyre_V2_R` / `BRAKE_DISC_R` never shipped | pack each `_R` into the `s2` PropertyMap (channel map undecoded) or bake into `s0` as a contrast shift; keep the scalars as the fallback | bake + the `s2` channel probe named in `app-cockpit-interior-materials.md` |
| O2 | rim `s0`/`s1` are name-match fallbacks | author the bindings: `Wheel_V2_D/N` are the right textures but were never bound by the chain, so a later reader cannot tell an authored edge from a guess | wiring, 1 line per slot |
| O3 | `rim_radius` 0.539 vs BmAK `Fan` r 0.5127 (26 mm) | decide whether to set `…wheels.rim_radius` from the `Fan` or keep the shipped value; currently printed and not asserted | one decision + a read-back |
| O4 | T-L31..T-L34 contradiction | pick one: either the four split flares are inside the wheel-lamp row (manifest) or they are out (COMPROMISES). The manifest's positions exist (−1.2099/1.1027/−2.1639 top, −1.2082/0.8077/−2.0049 bottom), so carrying them costs two light rows | decision, then a rebuild |
| O5 | `Discbreak_front` / `Discbreak_back` | two `CarPaintMM` blocks for the disc (one per axle) with different `m_Emissive`, since one block cannot hold both | build: split the disc block |
| O6 | rear wheels have no lamp; ledger speaks of "rear-wheel lights" | correct the row language: the rear axle's lamps are `BrakeLightL/R` on the suspension bones, a `TailLight`, not a hub light | doc fix |
| O7 | front LOD2/4/5 unlisted in `@files.xml` | confirmed unused by design (the `.lod` never names them); no action, recorded | - |
| O8 | wheel part `parent_space_offset` stale by up to 1.0130 m | dormant (placement comes from `land_global`); optional clean-up named in `wheel_offset_effect.md` §6 | optional |

---

## 7. Closest system, gap (STAGES.md)

**Closest system:** `CarPaintMM` per wheel part + the JC3 lights module for the hub lamps + the
`no_tire` / `wheel_explosion_notiremesh` effects for a bare rim. That is enough for albedo, normal,
scalar gloss/metal, emissive and a lamp row; it is **not** enough for per-pixel roughness, a
front/rear glow split, or a per-flare colour.

| BmAK input | value | JC3 member | gap |
|---|---|---|---|
| tyre Ø / width | 1.3652-1.3657 / 0.7314-0.7325 | `land_global.*_wheels.radius` / `.width` | **none** (≤ 0.55 mm) |
| rim Ø (`Fan`) | 1.0254 | `…rim_radius` 0.539 | quantity mismatch, 26 mm - decision |
| `Wheel_V2_R`, `Tyre_V2_R`, `BRAKE_DISC_R` | 3 maps | `m_SpecularGloss` / `m_Metallic` scalars | per-pixel |
| `Discbreak_front/back` | 2 scalars | `m_Emissive` (one per block) | needs a block split |
| hub lamps + 4 split flares | 6 light rows | lights `vmodc` | 4 rows contradictory |
| tyre EMP | 0.0 / 350 | none | dropped (D14) |
| mud / rain on wheel | 10 scalars | none | JC3 dirt is dynamic (D1/D8) |

---

## 8. UNKNOWN

1. **The tyre's and rim's UV layout** - no colour/normal map is bound in either chain, so the
   build's `s0`/`s1` are name matches; nothing decoded confirms the mapping.
2. **Whether the front/rear tread topology difference survives decimation** - the LOD budgets are
   per part; no measurement of the rear tread pattern was made here.
3. **Which `s2` channel is roughness vs metalness** - the same undecoded channel map as the
   interior and glass reports.
4. **Whether `Wheel_Lights_M`'s RGB really maps to channels 1-3** - asserted by the build's
   coverage table, not by a BmAK binding read.
5. **Whether the four split flares were carried** - two of the build's own files disagree.
6. **`rim_radius`'s intended meaning** - shipped at 0.539 with no BmAK counterpart; whether it is
   the rim seat, the hubcap or a physics radius is not in any file.

---

## 9. Checks run

| # | check | result |
|---|---|---|
| 1 | `TYRES.md` | tread Ø 1.3652-1.3657, shoulder 1.3711-1.3714, width 0.7314-0.7325; `Fan` Ø 1.0254; `Disc` Ø 1.5962; faces 6,700 / 7,564 |
| 2 | `build_parts` | 20 wheel `.rbm` (5 LODs × 4), 9 wheel `.ddsc`; no `_R` textures |
| 3 | `bm-RC2` receipt | wheel LODs + `mshswap`, front arches → `engine`, rear → `body`, wheel effects, lights vmodc |
| 4 | `bm-RC2/verify/wheels.md` | radius 0.68275/0.68265, width 0.73195/0.73165, axis `+x`, rim_radius 0.539013/0.538934 untouched |
| 5 | `bm-RC2/verify/wheel_offset_effect.md` | stale wheel pso (max 1.0130 m) dormant |
| 6 | `build_parts/coverage.md` | Wheel_V2 0.6088/0.3561, Tyre_V2 0.052/0.1184, Discbreak 0.9586/0.431; s0/s1 fallbacks; flags 0x0000 |
| 7 | `lights_manifest.json` vs `COMPROMISES_T.md` | T-L13/T-L20 mapped; T-L31..34 mapped in the manifest, `out`/UNAPPROVED in COMPROMISES - **conflict recorded** |
| 8 | `LIGHTS.md` | wheel lamps on `Wheel_Frnt_*_Disc` only; `BrakeLightL/R` on `SUSP2_Wheel_Rear_*` |

No game process was started, attached to or injected into; static read only.

## Reproduce

```bash
ls Working/Appearance/build_parts/ddsc | grep -E "wheel|tyre|disc"
grep -n -A12 "BatmobileV3_Wheel_V2_MIC" Working/Appearance/build_parts/coverage.md
sed -n '1,40p' Builds/bm-RC2/verify/wheels.md
grep -n "T-L3[1-4]" Working/Translation/COMPROMISES_T.md Working/Appearance/build_lights/lights_manifest.json
```
