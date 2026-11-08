# Canopy glass — BmAK `Batmobile_Glass` vs JC3 `Window`

Status: research + build values. Sources: `Research/BatmobileGrab/SLOTS.md`,
`MATERIALS.md`, `SKINS.md`, `TEXTURES.md`, `COCKPIT.md` §1, `BONES.md`, `MESHES.md`,
`VEC_DEFAULTS.md`; `tmp/freebuff/reports/app-glass-layers.md` (the decoded
`window.fb.txt` / `windowdamage` shader tables and the 13-parameter mapping — reused,
not re-derived here); `Working/Translation/T2_TRANSLATION.md` T-MA5;
`Research/JC3Grab/GEOMETRY.md`, `DOORS.md`, `DAMAGE_MODEL.md` §1/§5,
`tmp/freebuff/reports/app-damage-chapter-masks.md`, `USAGES.md`, `DECODE_DEPTH.md`,
`CLASS_DEFAULTS.md`; `MODLOG.md` §102d, §5200.

## 0. Verdict

| what | BmAK | JC3 | what we set |
|---|---|---|---|
| **tint** | `bat_glass.tint` **linear [0.02579, 0.02579, 0.03]** — the same authored colour as the paint; the glass MIC has *no colour parameters* | `Window` block stores **no tint vector**; colour = `t0` diffuse RGB × `TintPower` (`cb1[12]`) × per-vertex `COLOR0` (template ~(1,1,1)) | bake tint into `t0` RGB: linear **[0.02579, 0.02579, 0.03]** → sRGB **× 3.4476** = **[0.0567, 0.0516, 0.06]**; leave `TintPower` 1.0, vertex tint at template |
| **opacity** | `Glass_Opacity` **1.2000** × `Batmobile_V3_Glass_A` (4K DXT1) | `Alpha` `cb1[40]`, floor `MinAlpha` `cb1[16]`, opacity read from **`t0` alpha** only | repack `V3_Glass_A` into `t0` alpha × **1.2**, clamped — measured result **mean alpha 193/255** vs the vanilla window's **204/255** |
| **reflection** | `Glass_Reflectivity` **0.8000** + `V3_Glass_S` **R** channel (per-pixel), `Glass_Roughness` **1.1000** + **G** channel | `SpecGloss` `cb1[0]`, `SpecFresnel` `cb1[4]`, `DiffuseRougness` `cb1[8]`, `PropertyMap` `t3` — **which member takes which value is UNKNOWN** | 0.8 → `SpecGloss` **and** `SpecFresnel` candidates; 1.1 → `DiffuseRougness` (raw, no documented clamp). Both need the 4-block probe in §7 |
| **crack stages** | **none.** No crack texture, no crack parameter, no glass damage stage anywhere in the material or the MIC. The car breaks by **mesh swap**: `Batmobile_V3_Destroyed` (57,101 verts, **1** material) and `Batmobile_V2_Fire` (1,320 verts, 1 material) | **runtime contact-point cracking**: `windowdamage` `NumPoints` + `PointPositionAndSize[32]` (512 B), weighted by `DamageMaskWeight` `cb1[32]` / `DamageRampWeight` `cb1[36]`, over `window_cracks_bullet_{nrm,mpm}` + `window_cracks_tile_{nrm,mpm}` — **already bound on every shipped window** (`t4`–`t6`) | BmAK has nothing to carry. To *match* BmAK: keep `DamageMaskWeight`/`DamageRampWeight` at **0** and use no damage window variant → a clear canopy until the car dies; the destroyed look stays the mesh swap. To *keep* JC3 cracking: it is free (maps pre-bound), but it is a BmAK invention we do not have |
| **rain** | glass material carries **no rain parameter**; the *liner* does: master `Batmobile_Worn_NoRain` (slot 18, 524 faces = the canopy roof/liner) against the wet `Batmobile_Worn`; body master sibling `Batmobile_V3_Body_NoRain_MAT`; functions `BMBL_Rain_Opt`, `rain_effect_V2_Batmobile` (bodies never read → **UNKNOWN**) | every window shader binds `s9 RainOccluderSampler` / `t40 RainOccluderTexture` — the canopy becomes a rain **occluder**, so no rain draws under it; no per-material wetness scalar | keep the template's `t40` binding (**do not create a `Window` block without it**); nothing else to set. A wiper is not needed — JC3's `WindshieldWiper` behaviour row exists but is unproven and BmAK has no wiper |

## 1. BmAK glass, decoded

**Where it sits.** Slot **1** of the body mesh, `Batmobile_V3_Glass_INST`
(`MaterialInstanceConstant`, export 761, 761 B), **3,532 faces** at LOD0 — of which **1,716
on `CockPit_Mesh`** (`SLOTS.md`, `COCKPIT.md` §1, `BONES.md` material table). One slot, one
MIC, four identical skins (base/MK2/Funhouse/Joker).

**The master is a socket contract with no defaults.** `Batmobile_V2_Textures_NEW.Batmobile_Glass`'s
eight inputs — `DiffuseColor`, `SpecularColor`, `SpecularPower`, `Normal`, `EmissiveColor`,
`Opacity`, `OpacityMask`, `MetalMask` — are **all unconnected** in all four packages. Every
value lives in the MIC.

| MIC parameter | value | class |
|---|---:|---|
| `Glass_Opacity` | **1.2000** | decoded (GUID `72b5400b`) |
| `Glass_Reflectivity` | **0.8000** | decoded (`6b94edbf`) |
| `Glass_Roughness` | **1.1000** | decoded (`05ac6289`) |
| `glass_smudges` | **0.2000** | decoded (`13da4f34`) |
| `bat_glass.tint` | **[0.02579, 0.02579, 0.03]** linear | decoded (`VALUES.json`) |
| `glass.opacity_multiplier` | 1.0 | decoded |

| texture | dims | format | bound as |
|---|---|---|---|
| `Batmobile_V3_Glass_A` | 4096×4096 | PF_DXT1 | `OpacityMap` |
| `Batmobile_V3_Glass_N` | 4096×4096 | **PF_BC5** | `Normal` |
| `Batmobile_V3_Glass_S` | 4096×4096 | PF_DXT1 | `Mask (R=Reflect / G=Rough / B=Normal map compression artifacts fix)` |
| `Batmobile_V2_GLASS_MASK` | 1024×512 | PF_DXT1 | **unbound in every package** — frame mask is UNKNOWN |

The tint is not an inference: `bat_glass.tint` is the authored paint colour, and
`VALUES.json` notes the canopy has no colour parameters of its own.

**Geometry the glass covers** (`COCKPIT.md` §1/§3): windscreen first hit **0.8489 m** ahead of the
mean eye at z **−1.9143**; side windows at x **−0.2942 / 0.2943**, z −1.5925…−0.8349,
y 1.5165…1.8868, **611 faces**; the **roof over the driver is opaque** (liner `Batmobile_Worn_NoRain`
y **1.9661**, skin y 1.9914; 0 of 63 vertical rays hit glass). So the canopy is a windscreen plus
two side panes — not a bubble.

## 2. BmAK crack stages — there are none

Searched, not assumed:

* **No crack texture is bound to the glass.** The only damage-pattern texture in the package,
  `Batmobile_Damagepattern_N` (2048×1024 DXT1), is bound to **nothing** (`—` in `TEXTURES.md`).
* **No crack parameter** exists on the MIC (4 scalars above) or the master (8 empty slots).
* **The body's damage look is a chapter mask, not a stage**: `Batmobile_V3_TEXTURES_Body_Damage_ChapterMask`,
  `…WheelArch…`, `…Undercarriage…`, `…Weaponry…` are bound as `Damage_Chapter_Mask` on the *paint*
  slots (`SLOTS.md` rows 2/3/4/7). Per `app-damage-chapter-masks.md`, JC3's damage blend is one
  static pair of vectors gated by `SupportDmgBlend` (`cb2[18].y`), shipped **0.0**.
* **The only "broken glass" state is a different mesh.** `MESHES.md`: `Batmobile_V3_Destroyed`
  (**57,101** verts, LOD0 36,513, **1** material, 32 bones) and `Batmobile_V2_Fire` (1,320 verts,
  1 material, 179 bones) in all four packages; no `CanopyOpen` mesh, no smashed-canopy mesh.
* `DAMAGE_RULES.md` never mentions glass: the vehicle damage model's thresholds
  (`QuarterHealth`, `LowHealthWarningLevel`, `ArmourLevels`) and `SetDamageLevel` are body-level.

**So**: BmAK's canopy is either pristine or the car is a wreck. There is no chipped, starred or
cracked stage to copy, and no glass-specific hit-point pool — the canopy is not a damage part.

## 3. JC3 glass — the `Window` block and its shaders

**The block** (`app-glass-layers.md` §2.1, decoded from 6 donor window blocks):
40 B per vertex (`x,y,z | u,v | 0,0 | packed normal | tangent | constant packed tint ~(1,1,1)`),
u16 indices, a 7-entry texture table and **no scalar table** — the 16 B between table and buffers
do not decode as four plausible floats. Type hash **0x5B2003F6** (`rbmhdr.py`);
**12,028** `Window` blocks fleet-wide (`GEOMETRY.md`), byte-exact re-encoded.

| texture | donor binding | role |
|---|---|---|
| `t0` | `<car>_glass_alpha_dif.ddsc` (**BC3/DXT5, format 77**) | diffuse **RGB = tint, A = opacity** |
| `t2` | `dummy_nrm.ddsc` | normal (slot exists, empty) |
| `t3` | `<car>_glass_mpm.ddsc` | property map |
| `t4` | `window_cracks_bullet_nrm.ddsc` | **bullet crack normal** |
| `t5` | `window_cracks_bullet_mpm.ddsc` | bullet crack property |
| `t6` | `window_cracks_tile_nrm.ddsc` | tile/impact crack normal |

**The scalars are shader-side** (`window.fb.txt`, `cb1 MaterialConsts`):
`SpecGloss` +0, `SpecFresnel` +4, `DiffuseRougness` +8, `TintPower` +12, `MinAlpha` +16,
`UVScale` +20, `DamageMaskWeight` +32, `DamageRampWeight` +36, `Alpha` +40 — plus
**`windowdamage`'s `cb2`**: `NumPoints` +0, `PointPositionAndSize[32]` +16 (**512 B = 32 crack
points**). No `.rbm` block writes `cb1`/`cb2`, so a private material cannot set them by member —
the value has to arrive through the diffuse texture (or a `CarPaintMM` stand-in, at the cost of
losing the crack path).

**Rain is a sampler, not a scalar**: every window variant binds `s9 RainOccluderSampler` /
`t40 RainOccluderTexture`, plus `s11` environment cube and `t12` falloff. The glass therefore
**occludes rain** — the JC3 mechanism that corresponds to BmAK's `NoRain` liner.

## 4. JC3 break states — part health + attached effect

JC3's "stages" are **per-part health thresholds**, never material stages
(`app-damage-chapter-masks.md` §3):

| layer | values | glass relevance |
|---|---|---|
| `VehicleDamage.part_damage_types[]` (24 rows, 4,820 fleet rows) | `initial_health` **50…10000** (median 300), `damaged_health`, `loosen_health` **0…500** (median 50), `instantly_{damaged,loosened,broken}_by_bullets`, `damages_owning_vehicle` | donor glass rows: **`Land_Window` initial_health 50**, `Land_Stunt_Window` (the donor's `sportsmuscle_window_f`), `Land_Light` 50 — vs `Land_Generic` 200, `Land_Body` 1000, `Land_Wheel` 1020 |
| 8 damage channels | bullet, bullet_heavy, explosion, impact, fire, melee, electricity, grapple_pull, each `_armor` + `_armor_strength` | a window has **no own channel**; it inherits the vehicle's |
| instant overrides | `instantly_broken_by_bullets` is **0 on all 4,820 rows**; `instantly_damaged_by_bullets` 0…1; `instantly_loosened_by_bullets` **0 on all** | **no window in JC3 breaks on a single bullet**; it goes through the 50-point pool |
| part class | `Land_Window` **815 parts**, `Land_Stunt_Window` 67 (fleet); donor windows: `sportsmuscle_window_f` (Windshield, part 13), `_window_r_l` (14), `_window_r_r` (15), `door_f_l_window` (16), `door_f_r_window` (18), `trunk_window` (32, RearWindow) | the class the canopy glass must carry |

**Break is an attached effect on the part's deform point**, not a shader state:
`all_effects[]` (9,230 rows) maps `deform_point` → `effect`, e.g. **`window_r_r` → `window_break`**;
the effect strings are 17 (`burn_base`, `burn_engine`, `burn_roof`, `door_break`, …, `window_break`);
`part_effects[].part` names the part. Usage census (`USAGES.md`):

| effect | objects | resolved effect |
|---|---:|---|
| `window_break` | **184** (182 `SDynamicAttachedEffect`) | `dynamic_break_window` ×182, `dynamic_glass_breaking` ×2 |
| `window_break_sm` | **143** | `dynamic_break_window_sm` ×141 |
| `window_break_front` | 11 | `dynamic_break_window_front` |
| `window_break_small` | 6 | `dynamic_break_window_small` |
| `window_break_back` | 5 | `dynamic_break_window_back` |
| `window_break_tall` | 5 | `dynamic_break_window_tall` |
| `window_break_02` / `window_tint_break` | 2 / 2 | `dynamic_break_window_02` / `dynamic_break_window_tint` |
| `windshield_tint_break` | 2 | `dynamic_break_windshield_tint` |
| `explosion_glass` / `_sm` | 35 / 2 | `dynamic_explosion_glass(_sm)` |

Sound: `dynamic_break_window` and `dynamic_break_window_sm` (`SDynamic`, `JC3_AUDIO.md` #31).
Effect file: `effects/jc_vehicles/damage/dmg_window_break.effc` (**11,455 B**, and `_sm` the
same size, `DECODE_DEPTH.md` #164/165). Debris texture: `t_debris_glass_row_01_s2_alpha_dif.ddsc`.

**One more hook worth knowing**: the donor's deform-point names include
`signal_r_r_glass_break` and `b_l_blkr_glass` (`VOCABULARY.md` `points[].name`), so a breakable
glass point can be addressed by name in the graph.

## 5. The build today

| item | state | source |
|---|---|---|
| `Window` block count | **1 per LOD** (17 blocks = 16 `CarPaintMM` + 1 `Window`) | T2 T-MA1 |
| where the block came from | cloned from `sportsmuscle_door_f_l_window_lod1.rbm`; only geometry replaced | `bat_assemble.py` (Window maker) |
| tint | authored paint colour (`VALUES.json` glass `Material0_BaseColour`) | T-MA5 |
| opacity | BmAK opacity map × `Glass_Opacity` (**1.2**) → **mean 193** vs vanilla **204** | T-MA5, MODLOG §5200 |
| scalars | **none written** — `SpecGloss`/`SpecFresnel`/`DiffuseRougness`/`TintPower`/`MinAlpha`/`Alpha`/`DamageMaskWeight`/`DamageRampWeight` live in `cb1`, which no block stores | T-MA5, `app-glass-layers.md` §5 |
| normal | the block's `t2` still holds `dummy_nrm.ddsc` — `V3_Glass_N` is **not** written yet | `app-glass-layers.md` G4 |
| smudges | not carried (no member) | G5 |
| cracks | not carried; template's `t4`–`t6` come along with the clone | G7 |
| damage blend | `SupportDmgBlend` 0, `m_Damage` (0,0,0,0) — off, donor values | `app-damage-chapter-masks.md` |

## 6. The numbers to set

### 6.1 Look

| # | value | how |
|---|---|---|
| 1 | **tint linear [0.02579, 0.02579, 0.03]**, sRGB ×3.4476 = **[0.0567, 0.0516, 0.06]** | bake into `t0` RGB (multiply the alpha glass texture by the tint); `TintPower` stays at the donor value, vertex tint stays ~(1,1,1) |
| 2 | **opacity = `V3_Glass_A` × 1.2**, mean **193/255** | repack into `t0` **alpha**; keep `MinAlpha` as the floor (donor value, do not invent one) |
| 3 | **normal = `V3_Glass_N`** (4096², **BC5**) | write into `t2` in place of `dummy_nrm.ddsc` |
| 4 | **reflectivity 0.8 / roughness 1.1** | candidate members `SpecGloss` `cb1[0]` + `SpecFresnel` `cb1[4]` for 0.8 and `DiffuseRougness` `cb1[8]` for 1.1 — **UNKNOWN assignment**, settled by the probe in §7; per-pixel R/G of `V3_Glass_S` would need `t3`'s undecoded channel packing |
| 5 | **smudges 0.2** | no member: bake as a dirt layer into `t0` alpha, or drop (recorded as a loss) |
| 6 | frame mask | UNKNOWN whether `Batmobile_V2_GLASS_MASK` is the frame; do not bind it blind |

Sanity target: the build's 193 vs the vanilla window's 204 means our glass is **~5 % more
opaque** than the shipped sports car glass — closer to the BmAK canopy than the template it was
cloned from, which is the intended direction.

### 6.2 Cracks / break

| # | value | why |
|---|---|---|
| 7 | **`DamageMaskWeight` 0, `DamageRampWeight` 0**, and **do not** use a damage `Window` variant | BmAK has no crack stage; 0 is the value that reproduces "clear until it dies". (Both members are `[unused]` in the plain `window` shader and only live in `windowdamage`/`windowsimpledamage`, which the template does not use — so the default is already 0; the instruction is "do not switch it on".) |
| 8 | **part class `Land_Window`** for the canopy glass | the donor's own window class; `Land_Stunt_Window` is used only by its windscreen part |
| 9 | **`initial_health` = 10000** (fleet maximum) for the canopy part, if the glass must survive until the car dies; **50** (the donor's `Land_Window`) if it should shatter early like a normal car window | BmAK's canopy never breaks on its own — the wreck is the `Batmobile_V3_Destroyed` mesh. 10000 keeps the part alive across a full health bar; 50 makes it the first thing to go. Do **not** use `instantly_broken_by_bullets` — it is 0 on all 4,820 shipped rows |
| 10 | break effect = **`window_break`** (or `windshield_tint_break` for a tinted pane) attached to the canopy's deform point | the donor's own mapping (`window_r_r` → `window_break`), 184 objects fleet-wide |
| 11 | destroyed look = **mesh swap** (`Batmobile_V3_Destroyed`, 57,101 verts, 1 material) | BmAK's own mechanism; JC3 vehicles do not carry a second mesh, so this stays a build/entity choice, not a `Window` value |

If the reviewer prefers JC3's cracking to BmAK's single state: leave `t4`–`t6` bound and set
`DamageMaskWeight` 1.0 with `NumPoints` driven by the engine — that is *more* than BmAK, and the
only cost is that the canopy shows bullet stars a pristine Batmobile canopy never shows.

### 6.3 Rain

| # | value | why |
|---|---|---|
| 12 | keep the template's **`s9 RainOccluderSampler` / `t40 RainOccluderTexture`** binding | this is the JC3 equivalent of BmAK's `NoRain` liner: the canopy keeps rain off what is under it. A `Window` block authored without `t40` loses it |
| 13 | no wetness scalar exists on glass | BmAK's own glass has none either (`Glass_Opacity`/`Reflectivity`/`Roughness`/`smudges` only). The BmAK *liner* (`Batmobile_Worn_NoRain`, 524 faces) is the dry variant, and its wet sibling is a **material name**, not a number |
| 14 | no wiper | JC3's `WindshieldWiper` behaviour exists (`MOVING_PARTS.md`: mechanism UNKNOWN) but no shipped car is proven to drive it and BmAK has no wiper |

Audio is out of scope here, but for completeness the rain *sounds* are BmAK's
`Play_Batmobile_Rain_Interior` / `_Exterior` (params `RainDensity`, `Speed`), and
`RVehicleBatmobileBase.HowMuchTheRainAffectsHeatSteam` = **0.5** (`CLASS_DEFAULTS.md` row 131) —
the only rain number on the vehicle class.

## 7. What would close the open values

| gap | experiment |
|---|---|
| which `cb1` member takes 0.8 / 1.1 | one build, four blocks: `SpecGloss` 0.2/1.0 × `DiffuseRougness` 0.2/1.0, screen at noon on a chrome reflection; read which pair changes highlight size vs sharpness (the `t3` channel probe in `app-glass-layers.md` G3 is the per-pixel version) |
| `MinAlpha` floor | render the alpha 193 pane against the dark cockpit: if the interior is invisible the floor is too high; bisect 0.0/0.25/0.5 |
| whether `V2_GLASS_MASK` is the frame | decode its pixels, compare with the canopy frame's UVs (`G6`) |
| glass HP vs vehicle death | one build at `initial_health` 50 vs 10000, full health bar of small-arms fire on the windscreen |

## 8. Reproduce

```
grep -n "Glass_" Research/BatmobileGrab/SKINS.md | head          # the 4 scalars, 4 skins
grep -n "Batmobile_V3_Glass" Research/BatmobileGrab/SLOTS.md     # slot 1, 3,532 faces, Window block
python Tools/scripts/rbm_geom.py info <built rbm>                # Window block + t0..t6 table
python Tools/scripts/spec_check.py <build dir> <template>        # Window block type vs factors.json
```

The shader tables (`window.fb.txt`, `windowdamage`) are quoted in
`tmp/freebuff/reports/app-glass-layers.md` §2.2 with their header hashes; they are **not**
re-decoded in this pass.

## 9. UNKNOWNs

1. **Which `cb1` member receives `Glass_Reflectivity` 0.8 and `Glass_Roughness` 1.1** — two
   candidates for one BmAK scalar (`SpecGloss` + `SpecFresnel`), no documented clamp on 1.1.
2. **`t3`'s channel packing** (`s3` property map) — undecoded, so per-pixel reflect/rough cannot be
   written yet.
3. **The rain material functions.** `BMBL_Rain_Opt` and `rain_effect_V2_Batmobile` are two of the
   12 `MaterialFunction`s whose **bodies have never been read** (`GRAB_BACKLOG.md`: the packages
   were never grabbed). What exactly the `NoRain` variant does on the liner is therefore UNKNOWN;
   the name and the wet/dry master pair are the only evidence.
4. **Whether BmAK cracks glass at all at runtime.** No asset, parameter or texture in the grab does
   it; the destroyed/fire meshes are the only broken state. A runtime-only effect would not be
   visible in these files.
5. **`MinAlpha`'s donor value** — not read in this pass; the build must read it from the template
   block rather than assume.
6. **`Land_Stunt_Window`'s row values** — the donor uses it for the windscreen part; only
   `Land_Window` 50 is quoted from the build record (T-DM5).
7. **Whether the canopy's glass survives the mesh swap.** The `Destroyed` mesh has 1 material, so
   the glass is not a separate material there; whether the swap removes the panes or re-tints them
   is a mesh question, not a material one.
