# BmAK chapter damage masks -> JC3 damage blend (appearance rule D9)

**Question.** BmAK keeps four chapter damage-reveal masks (Body, Weaponry, WheelArch,
Undercarriage) that make the Batmobile look battle-worn differently per story chapter. D9 drops
them because JC3 damage is hit-driven (`SupportDmgBlend 0`). What does JC3's damage blend
actually do, how many damage stages exist, where is the damage texture slot, and can a private
material carry a pre-damaged look - fixed, or as hit-driven stages driven by BmAK's mask?

**Verdict.**

* JC3 has **one** damage texture pair per material - `s4` damage normal, `s5` damage albedo -
  and **one** blend pair of static vectors (`m_Damage` `cb2[15]`, `m_DamageBlend` `cb2[16]`)
  gated by a single support float, `SupportDmgBlend` (`cb2[18].y`) [decoded].
* In the donor's shipped blocks the gate is **0.0** and both vectors are `(0,0,0,0)`, so the
  blend is off and the look is carried by the shared damage texture plus per-part health
  [decoded]. D9's premise is confirmed for the shipped data.
* JC3's "stages" are **per-part health thresholds**, not chapters: `initial_health` ->
  `damaged_health` -> `loosen_health` -> broken, with three `instantly_*` overrides, over a
  24-row part table and 8 damage channels [decoded]. There is no chapter state anywhere.
* **A private material can carry a pre-damaged look as a fixed state.** `SupportDmgBlend` and
  `m_Damage` are *static per block*, so setting the gate to 1 with a non-zero `m_Damage` is an
  authored, always-on damage - and BmAK's chapter mask is exactly the right kind of texture for
  `s5` [derived from decoded members].
* **It cannot carry four chapter states.** There is one `s5` slot, not four; a chapter change
  therefore has to be a **material/entity variant set** (4 variants), not a runtime switch, unless
  the engine rewrites `m_Damage` - which no file shows.
* Per STAGES.md the row becomes `closest (static damage blend + shared damage textures) + gap
  (one state, no chapter selector) + build action`.

---

## 1. What JC3's damage blend is - decoded members

[decoded: `carpaintmm.fb.txt`; `CB0_SLOTS.md` §3-§4; layout cross-checked against the `.rbm`
block sizes 288 + 28 + 76 = 392 B.]

| member | bind / offset | size | role |
|---|---|---:|---|
| `m_Damage` | `cb2[15]` @ 240 | 16 | damage blend weights (4 channels) |
| `m_DamageBlend` | `cb2[16]` @ 256 | 16 | blend shaping per channel |
| `m_DamageColor` | `cb2[17]` @ 272 | 16 | tint of the damage layer |
| **`SupportDmgBlend`** | **`cb2[18].y` @ 292** | 4 | **the gate float: is damage blending on** |
| `DamageNormalMap` | `s4` / `t4` | sampler | damage **normal** |
| `DamageAlbedoMap` | `s5` / `t5` | sampler | damage **albedo** |
| `SUPPORT_DAMAGE_BLEND` | flag bit `0x2` | - | block-level companion of the gate |

The block's flags carry `SUPPORT_DAMAGE_BLEND = 0x2` alongside `SUPPORT_DECALS 0x1`,
`SUPPORT_DIRT 0x4`, `SUPPORT_SOFT_TINT 0x10` [decoded: `rbm_geom.py:114-126`].

**Two independent switches exist**: the flag bit (block-level, decides whether the feature is
compiled/serialised) and the `SupportDmgBlend` float (shader-level). Both must be on for the
blend to be visible [derived: the flag gates the support field's meaning, as `SupportDirt` does
for dirt].

---

## 2. Where the damage texture slot is

[decoded: `COLOUR.md` §2 sampler table + `carpaintmm.fb.txt` bindings.]

| slot | sampler | texture bound on the donor's blocks | role |
|---|---|---|---|
| `s4` | `DamageNormalMap` / `t4` | `damage2_nrm.ddsc` (measured: all 17 blocks of `sportsmuscle_body_lod1.rbm`) | damage normal |
| `s5` | `DamageAlbedoMap` / `t5` | `vehicle_metal_alpha_dif.ddsc` | damage albedo (scratches/metal) |
| `s6` | `DirtMap` / `t6` | `vehicle_dirt_msk.ddsc` | dirt (separate system, D1) |

`COLOUR.md` §2 lists `s4` as `damage2_alpha_nrm.ddsc` **on paint blocks**; the current decode of
the same file returns `damage2_nrm.ddsc` on all 17 blocks. That is a **discrepancy to re-check**,
not resolved here - reported rather than papered over. The slot *position* (`s4`/`s5`) is not in
doubt; only which shared normal file a paint block binds.

All three textures are `00_shared` - they are **not per material**. The only per-material damage
data is the three static vectors.

---

## 3. How many damage stages JC3 has

[decoded: `Research/JC3Grab/DAMAGE_MODEL.md` §1 steps 1-7; `DAMAGE_MECHANISMS.md` §1.]

| layer | values | count |
|---|---|---|
| part damage table (`VehicleDamage.part_damage_types[]`) | same 24 `Land_*` names in donor and tank | **24 rows** |
| per-part health thresholds | `initial_health`, `damaged_health`, `loosen_health` | **3 numeric states** |
| per-part instant overrides | `instantly_damaged_by_bullets`, `instantly_loosened_by_bullets`, `instantly_broken_by_bullets`, `damages_owning_vehicle` | **4 flags** |
| damage channels | bullet, bullet_heavy, explosion, impact, fire, melee, electricity, grapple_pull (each `_armor` + `_armor_strength`) | **8 channels** |
| vehicle thresholds | `smoke_threshold`, `burn_threshold`, `explosion_threshold`, `npc_explosion_threshold`, `vulnerable_explosion_threshold`, `explosion_delay_s` | **6 scalars** |
| vehicle pool | `max_health` 500..4000; root `health` 100.0; `invulnerable` 0 on all 233 roots | - |
| **chapter / story stage** | **none in any file** | **0** |

So JC3's visual damage advances through **3 part states (+ broken) driven by accumulated hit
damage**, and the material side has **one** damage layer. There is no numbered damage stage, no
chapter parameter and no per-stage mask in JC3.

**Derived.** The two systems are not commensurable: BmAK's chapter is *story time*, JC3's is
*health*. A mapping chapter -> health threshold is possible (`chapter N ≈ damaged_health state`)
but it is an authored bridge, and the error is "the car looks chapter-N worn while its health is
chapter-M".

---

## 4. What the shipped data actually measures

[decoded: this pass, `python` + `rbm_geom.decode` on
`E:/Modding/_gamedata/JC3grab/b13b/unpacked/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_body_lod1.rbm`.]

| quantity | measured | note |
|---|---|---|
| `static_support` on every decoded block | all seven floats `0.0` | `SupportDmgBlend` = **0.0** everywhere |
| `m_Damage` | `[0, 0, 0, 0]` on every block | blend weight zero |
| `m_DamageBlend` | `[0, 0, 0, 0]` on every block | |
| `m_DamageColor` | `[0.416, 0.389, 0.332, 1.0]` on the paint blocks, `[0, 0, 0, 1]` elsewhere | a dirt-brown value - **authored even with the gate off** |
| `s4` / `s5` on every block | `damage2_nrm.ddsc` / `vehicle_metal_alpha_dif.ddsc` | shared, not per-material |

**Flag bit vs gate float - the one place my re-decode and `COLOUR.md` disagree, and it does not
change the conclusion.** `COLOUR.md` §1 decodes the three paint blocks as `0x101F` - which
*includes* `0x2` `SUPPORT_DAMAGE_BLEND` - while a re-run of `rbm_geom.decode` on the same path in
this pass returned `0x0`/`0x100`/`0x200` and 16 `CarPaintMM` blocks against `COLOUR.md`'s 9
(unresolved: likely a stale unpack or a shifted block walk; see §8 item 5). Both reads agree on
the load-bearing number: **the `SupportDmgBlend` float is 0.0**, and `COLOUR.md` §2 annotates
`s4`/`s5` as "shared, feature off" independently of my run. The conclusion therefore stands on
the support float, not on the flag numeral.

**Derived.** The donor ships damage *authored but disabled*: the colour is there, the gate and
the weights are zero. The block-level flag bit may well be set (COLOUR.md says it is), which is
consistent with "the feature is compiled in and switched off by a float" - and that is exactly
the cheap probe DMG-1 exploits.

---

## 5. The chapter-state data BmAK holds

### 5.1 The four masks

[decoded: `Research/BatmobileGrab/TEXTURES.md` (dims/format/binding), `SKINS.md` (material rows).]

| mask | dimensions | format | export | bound by |
|---|---|---|---:|---|
| `Batmobile_V3_TEXTURES_Body_Damage_ChapterMask` | 4096 x 4096 | `PF_DXT1` | 11526 | `Batmobile_V3_Mainbody_NEW_MIC` (`Damage_Chapter_Mask`) |
| `Batmobile_V3_TEXTURES_Weaponry_Damage_ChapterMask` | 4096 x 4096 | `PF_DXT1` | 11498 | `Batmobile_V3_Turret_NEW_MIC` |
| `Batmobile_V3_TEXTURES_WheelArch_Damage_ChapterMask` | 4096 x 4096 | `PF_DXT1` | 11526 | `Batmobile_V3_WheelArchs_NEW_MIC` |
| `Batmobile_V3_Undercarriage_Damage_ChapterMask` | 4096 x 4096 | `PF_DXT1` | 11526 | `Batmobile_V3_Undercarriage_NEW_MIC` |

All four are **4096 x 4096 DXT1** - i.e. single-channel-friendly masks of the same class as a
damage albedo, which is why `s5` is the natural host.

### 5.2 The chapter selector values

[decoded: `Research/BatmobileGrab/SKINS.md`; `COLOUR_PARAMS.md:153` (parent expression 708,
guid `4614e464`, `float4`, no material override on the Worn master).]

| material | `Damage_Chapter` | reading |
|---|---|---|
| `Batmobile_Worn` expression 708 (default) | `[0, 0, 0, 0]` | no chapter |
| MIC (SKINS.md:526) | `[0, 0, 0, 1]` | chapter index in **A** |
| MIC (SKINS.md:543) | `[0, 0, 0, 1]` | same |
| MIC (SKINS.md:547/556) | `[1, 1, 1, 0.5]` | RGB = 1, A = 0.5 |
| `Joker_Damage_Chapter` (SKINS.md:727) | `[0, 0, 1, 0.5]` | B = 1, A = 0.5 |
| `Joker_Damage_Chapter` (SKINS.md:762) | `[0, 0, 0, 1]` | A = 1 |

**Derived.** The selector is a `float4`, and the four masks are number-matched to it: a `float4`
has four components and there are four masks. The A component carries 1 or 0.5, the RGB carries
0/1 patterns - consistent with "which chapter band, with a blend weight", but **nothing on disk
states the encoding** (the material graph is stripped, `VEC_DEFAULTS.md` §8). So: four masks,
selector with four components, chapter->mask assignment **UNKNOWN**.

### 5.3 The stage packages (a second, independent staging axis)

[decoded: `Research/BatmobileGrab/*.md` package census.]

Six upgrade stages ship as separate packages: `Batmobile_Std_1_SF` … `Batmobile_Std_6_SF`
(17/17/17/17/17/51 mentions), plus `Batmobile_Std_SF`. These are the Batmobile *upgrade* stages
(5 levels + final), not story chapters. They are the closest thing BmAK has to "the car changes
over the game" as a **whole-entity variant**, which matters for the build action below.

---

## 6. Can a private material carry it?

| question | answer | why |
|---|---|---|
| **fixed pre-damaged look** | **yes** | `SupportDmgBlend` is a static float per block; `m_Damage`/`m_DamageColor` are static vectors; `s5` takes any texture. Set the gate to 1, weights to 1, bind the chapter mask to `s5` and a derived normal to `s4` [derived from decoded members] |
| **all four chapter masks at once** | **no** | one `s5` and one `s4` slot; the other two masks have nowhere to be sampled |
| **switch chapter at runtime via the material** | **no** | no chapter member exists in `CarPaintMM` (34 named slots reviewed); `Damage_Chapter` is a BmAK parameter, not a JC3 one |
| **switch chapter by entity variant** | **yes, as a build** | 4 `.rbm` variants, one per mask; the engine picks by spawn. BmAK already does exactly this for stages (`Batmobile_Std_1..6_SF`) |
| **hit-driven stages using BmAK's mask** | **yes, partially** | bind the mask as `s5` damage albedo and let JC3's part-health thresholds reveal it. The *shape* is BmAK's, the *timing* is JC3's health; the mask cannot be re-selected mid-fight |
| **the gate to be honoured** | **UNKNOWN** | no shipped block sets `SupportDmgBlend` to 1 in the measured file, and the SHEX body is absent - the first build that sets it is the probe |

The important asymmetry: **fixed state is a value change; chapter switching is an asset-count
change.** The first is cheap and offline; the second multiplies the material set by four.

---

## 7. Closest system, gap, build actions

**Closest system:** `CarPaintMM`'s static damage blend - `SupportDmgBlend` (`cb2[18].y`) +
`m_Damage` (`cb2[15]`) + `m_DamageColor` (`cb2[17]`) + the shared `s4`/`s5` pair. It is a
per-material, authored damage layer, applied on top of the paint, tintable, with a normal and an
albedo input: structurally the same thing BmAK's chapter masks feed.

**Gap, stated as numbers:**

| BmAK input | value | JC3 slot | gap |
|---|---|---|---|
| 4 chapter masks, 4096x4096 DXT1 | Body/Weaponry/WheelArch/Undercarriage | **1** pair `s4`/`s5` | 3 masks have no slot |
| `Damage_Chapter` `float4` | `[0,0,0,1]`, `[1,1,1,0.5]`, `[0,0,1,0.5]` | none | no chapter selector |
| chapter = story time | 4 states over the campaign | part health thresholds | wrong driver (health, not story) |
| `SupportDmgBlend` in JC3 | 0.0 shipped, authored colour present | `cb2[18].y` | gate never observed at 1 |

**Build actions:**

1. **D9 row rewrite.** Three rows instead of one:
   * *fixed pre-damaged look* -> `closest` (static damage blend), gap "one state", action **DMG-1**;
   * *four chapter states* -> `closest` (4 material variants / entity variants), gap "no runtime
     chapter selector", action **DMG-2**;
   * *lore chapter timing* -> `closest` (part health thresholds), gap "story time vs health",
     action **DMG-3**.
2. **DMG-1 - turn the authored damage on.** In a private `.rbm`: set `SupportDmgBlend = 1.0`,
   `m_Damage = (1,1,1,1)`, `m_DamageBlend` as authored, keep `m_DamageColor`
   `(0.416, 0.389, 0.332, 1.0)` (the value the donor already ships), bind the body chapter mask
   to `s5` and a normal derived from it to `s4`. This is a pure value + texture edit and is the
   cheapest probe of whether the gate is honoured.
3. **DMG-2 - chapter variants.** Ship four `.rbm`/entity variants, one per mask, selected by the
   spawn path. Model the packaging on BmAK's own `Batmobile_Std_1..6_SF`, which proves the
   approach: BmAK changes the whole entity per stage rather than switching a mask at runtime.
4. **DMG-3 - hit-driven with BmAK's shape.** Keep the shipped gate at 0, bind the chapter mask as
   `s5` so whatever damage JC3 reveals is BmAK-shaped, and tune `VehicleDamage.part_damage_types`
   thresholds so the reveal lands at the chapter-appropriate point. This is the only action that
   gives "you can hit it and it degrades like the lore", and it is the one D9 originally ruled
   out with a single word.
5. **What not to attempt:** a runtime chapter switch through the material. It needs a scalar the
   block does not have and a shader body that is not on disk; four variants cost one asset set
   and no engine reverse-engineering.

---

## 8. UNKNOWN, with where each would be settled

1. **Whether `SupportDmgBlend = 1` with static `m_Damage` produces a permanent damage layer.**
   No shipped block sets it in the measured file; the SHEX is absent. DMG-1 is the probe.
2. **Whether the engine writes `m_Damage` per hit** (which would make hit-driven staging native
   and D9 unnecessary). Settle by a runtime constant-buffer dump on a damaged car.
3. **The encoding of `Damage_Chapter` and the chapter -> mask assignment.** Four masks and a
   `float4` selector exist; no file maps component -> mask or chapter number -> texel. Settle by
   reading the four mask pixels per chapter state (the textures are on disk) and matching the
   regions to in-game chapter screenshots.
4. **The channel meaning of the masks** (are they one mask with a blend weight in A, or four
   independent chapter bands?). Same route.
5. **The block-count and `s4` texture discrepancies** against `COLOUR.md` (17 blocks measured vs
   9 tabulated; `damage2_nrm` vs `damage2_alpha_nrm`). Settle by re-running `jc3_colour.py
   --check` - the file may have been regenerated from a different unpack.
6. **Whether damage blending survives `IS_DEFORM` vertex weights** - the donor's paint blocks are
   deform blocks, and the damage layer may be driven by vertex channels rather than the static
   vector. Relevant to DMG-1's success.

---

## 9. Checks run for this report

| # | check | result |
|---|---|---|
| 1 | `carpaintmm.fb.txt` damage members | `m_Damage` @240, `m_DamageBlend` @256, `m_DamageColor` @272, `SupportDmgBlend` @292, `s4`/`s5` |
| 2 | `rbm_geom.py` flags | `SUPPORT_DAMAGE_BLEND = 0x2` |
| 3 | decode of `sportsmuscle_body_lod1.rbm` | support floats all `0.0`; `m_Damage` all `0`; `m_DamageColor` `[0.416,0.389,0.332,1]` on paint blocks, `[0,0,0,1]` elsewhere; `s4`/`s5` = `damage2_nrm` / `vehicle_metal_alpha_dif` |
| 4 | `COLOUR.md` §1/§2 cross-check | COLOUR.md: 9 blocks, paint flags `0x101F` (includes `0x2`), paint `s4` = `damage2_alpha_nrm`; this re-run: 16 blocks, flags `0x0/0x100/0x200`, `s4` = `damage2_nrm` - **flagged, unresolved**; both agree the `SupportDmgBlend` float is `0.0` |
| 5 | `DAMAGE_MODEL.md` | 24 part rows, 3 health states, 4 instant flags, 8 channels, 6 thresholds |
| 6 | `TEXTURES.md` | 4 chapter masks, all 4096x4096 `PF_DXT1` |
| 7 | `SKINS.md` / `COLOUR_PARAMS.md` | `Damage_Chapter` values `[0,0,0,0]` default, `[0,0,0,1]`, `[1,1,1,0.5]`, `[0,0,1,0.5]` |
| 8 | package census | 6 `Batmobile_Std_1..6_SF` stage packages |

No game process was started, attached to or injected into; static read only.

## Reproduce

```bash
python - <<'EOF'
import sys, struct
sys.path.insert(0,'Tools/scripts'); import rbm_geom
f='E:/Modding/_gamedata/JC3grab/b13b/unpacked/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_body_lod1.rbm'
r=rbm_geom.decode(open(f,'rb').read())
for i,b in enumerate(r.blocks):
    if type(b).__name__!='CarPaintMM': continue
    sp=struct.unpack('<72f',b.static_params); sup=struct.unpack('<7f',b.static_support)
    print(i, hex(b.flags), sup, sp[60:72])
EOF
grep -n "SupportDmgBlend\|m_Damage\|DamageNormalMap\|DamageAlbedoMap" Tools/JCMR-src/assets/jc3/shaders/carpaintmm.fb.txt
```
