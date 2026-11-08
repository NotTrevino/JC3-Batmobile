# FX-20 — BmAK brake-light trail vs JC3 tail lamps, boost trails and motion blur

Task: find what JC3 does with tail lamps under braking or boost (light presets, streak/ribbon
emitters on vehicles, nitro/boost trails, motion-blur flags), read the decoded tail-light rows of the
Batmobile in `Working/Appearance` (`build_lights`), and say whether the BmAK brake streak can be
carried by a ribbon emitter, a light member, or neither — with member paths and BmAK values side by
side. Where JC3 has no exact carrier, name the closest system and the gap for the build (STAGES.md).

**Verdict.**

* **Neither a ribbon member nor a light member carries the streak in the decoded JC3 data.**
  JC3 lights have 25 members (`range`, `angle`, `diffuse.R/G/B`, `multiplier`, `min_luminosity`,
  `behavior`, …) and **none** names a trail, streak, ribbon, beam or effect (`LIGHT_SYSTEM.md` §1).
  The behaviour vocabulary is `None / HeadLight / TailLight / LeftSignal / RightSignal / Reverse /
  Siren*` — there is **no Brake behaviour**, so a brake state is not a decoded input at all.
  The `.effc` effect format's 94 member paths likewise contain **no** `Ribbon`/`Beam`/`Streak`
  member (`FX.md` `.effc` table), so "set the ribbon emitter's width" is not a thing any tune exposes.
* **The BmAK brake trail exists, but only as an empty component.** The four packages carry
  `BrakeTrail0` / `BrakeTrail1` as `ParticleSystemComponent` exports (Playable_BatmobileFunhouse_SF
  exports **5096 / 5097**, size 38 B each) with **no serialised ParticleSystem template** — only
  `ReplacementPrimitive` @316 = 0 and one float @364 = **0.9102755784988403** / **0.7530137300491333**.
  That is why G1-16's 206 `ParticleSystem` exports contain no brake system: the component's system is
  assigned in code, so no trail parameters exist in the grabbed files. The trail's look cannot be
  quantified from the data; the lamps that go with it can (below).
* **What the Batmobile actually shows** is the two brake *lamps*: `BrakeLightL/R` are
  `PointLightComponent`s, `LightColor` **[255, 38, 0, 0]**, brightness **1.0**, radius **150 uu =
  1.5 m**, falloff **6.0**, plus a `LensFlareComponent` on the `Engine.Batmobile_brakelights` flare
  (`LIGHTS.md:197–200`, `t14_lights.json` T-L15/T-L16). JC3's closest row is the donor's `TailLight`
  entry: diffuse **[1.0, 0.247850001, 0.0789999962]**, range **2.0 m**, angle **10°**, multiplier
  **2.0**, preset `Rear_Left_Point` (hash **1435191809**) on part `sportsmuscle_taillight_r_l`
  (`t14_lights.json` donor module row 0; `LIGHT_SYSTEM.md` TailLight census).
* **Closest JC3 system for the streak:** the `.effc` effect system plus its **texture-strip**
  (`.trim`) format — the fleet's velocity-streak texture `t_velocity_streak_alpha_dif.dds.1_1b.trim`
  is already inside the donor's `.ee` (657 B, 28 rows), and the donor also carries
  `car_cycle_base_dual_nitrous.effc` (20,671 B, 3,161 rows, 337 arrays) for boost glow. **Gap:** no
  member binds any effect to a light or to the brake input, and no brake-triggered effect path exists
  in the 955 `.effc` (T-FX20's 0-of-955 holds). Build action per STAGES.md BUILD: author a private
  `.effc` streak at the tail socket and author the trigger — the trigger is the part JC3 does not
  carry.

---

## 1. What was read, and how offsets are quoted

| side | inputs |
|---|---|
| BmAK | `Research/BatmobileGrab/LIGHTS.md` / `LIGHTS.json` (G1-17 light rig), `objects.jsonl` (export + property-tag byte offsets), `ASSETS.md` (class census), `PARTICLES_FEATURES.json` (the G1-16 206-system list), `CONFIG.md` (MotionBlur system settings) |
| JC3 | `Research/JC3Grab/LIGHT_SYSTEM.md` / `.json` (G2-33), `FX.md` / `FX_VOCAB.json` (G2-9), `FX_TABLE.jsonl` (every `.effc`/`.ctunec`/`.trim` and its container), `Working/Translation/t14_lights.json` (T-18 donor + build rows), `Working/Appearance/build_lights/lights_manifest.json` (B-03 lamp geometry) |
| delivery | `Working/Translation/T13_FX.md` + `Tools/scripts/t17_fx.py` (T-FX20 row as it stands) |

BmAK offsets are **export property-tag offsets** from `objects.jsonl` (`offset` within the export
payload; `size` is the export size). JC3 light values are the members listed in `LIGHT_SYSTEM.md` §1;
JC3 effects have no per-value offsets published by G2-9 (`FX.md` reports counts and ranges), so the
effect evidence is given by path + bytes + row/array counts, which is what the decode records.

## 2. T-FX20 as it stands, and the one claim that does not survive

`t17_fx.py:193–202` and `T13_FX.md:70`:

> T-FX20 brake-light trails — no system in G1-16's 206 — **no effect path** in the 955 `.effc` —
> socket `BrakeTrailL` — "named omission: the donor's own `BrakeLightTrailSystemL/R` stays as the
> entity graph carries it (T-FX6), there is no JC3 brake-trail effect" — dispo `out`.

The 0-of-955 negative is sound (needle `brake`, and the wider `trail` returns 84 paths, 46
vehicle-carried, none brake — `FX16_TERM.md`). Two things in the row are not:

1. **No object named `BrakeLightTrailSystem*` exists anywhere in the grab.** `objects.jsonl` has
   `BrakeTrail0` / `BrakeTrail1` components (§3), and no `ParticleSystem` named brake; the 206
   systems have no brake entry (`PARTICLES_FEATURES.json`: 0 rows matching `brake`).
2. **The JC3 donor's graph has no brake trail to "keep".** In the donor `.epe`
   (`v0300_car_kensington_sportsmuscle_signature_preorder.ee.json`) the only brake-named object is
   the light behaviour string `Rear_Brake` (1 occurrence); there is no `BrakeTrail` and no
   `SpeedLine` object. So T-FX20's disposition "stays as the entity graph carries it" is **not
   supported by the donor** — the row is right that JC3 has no brake-trail effect, and wrong about
   who carries one.

## 3. BmAK side: what the brake trail and lamps actually are

| item | evidence | value |
|---|---|---|
| `BrakeTrail0/1` | `objects.jsonl`, class `ParticleSystemComponent`, size **38 B** each in Funhouse/Joker/MK2, **30 B** in Batmobile; outer `Vehicle.Batmobile*` | **8 objects, 2 per package**: Funhouse **5096/5097**, Joker **2946/2947**, MK2 **5056/5057**, Batmobile **4995/4996**. `ReplacementPrimitive` @316 = 0; `FloatProperty` @364 = Funhouse **0.9102755784988403 / 0.7530137300491333**, Joker **0.7800225615501404 / 0.9793389439582825**, MK2 **0.2716757655143738 / 0.2055421620607376**; the Batmobile pair (30 B) carries no float |
| trail system | no template tag is serialised on either component; no `ParticleSystem` named brake in the 4 packages (`ASSETS.md` system census, `PARTICLES*.json`) | **UNKNOWN** — assigned in code |
| `BrakeLightL/R` | `LIGHTS.md:197`, `:199` (Playable_Batmobile_SF rows `:290`, `:292`) | `VEHLT_TailLight`, material `VEHLTMAT_TailLightLeft/Right`, behaviour `TailLight`, parts `SUSP2_Wheel_Rear_Left/Right`, anchor `\|sportsmuscle_LOD1\|body\|SUSP2_Wheel_Rear_Left\|SUSP2_Wheel_Rear_Left_LIG` |
| brake lamp light | `PointLightComponent`, `LightColor [255, 38, 0, 0]`, brightness **1.0**, radius **150.0 uu**, falloff **6.0** (`LIGHTS.md:197/199`; T-L15/T-L16 `bmak` block) | 1.5 m radius |
| brake flare | `LensFlareComponent` → `Engine.Batmobile_brakelights` (objects: index 336/337/343, ref tag @540) | no JC3 equivalent (JC3 light module has no flare; `LIGHTS.md:59–60`) |
| the only trail *primitive* decoded | `ParticleModuleTypeDataTrail2`, Joker package exports **2612/2613**, outer `Particles.Batwing_Exhaust_P`, size **55 B** | int **6** @96, float **50.0** @104, int **100** @120, bool **true** @124 — a jet-exhaust trail, **not** the brake trail |
| brake-light group in the build's own light rows | `t14_lights.json` T-L15 (`group: brake-left`), T-L16 (`brake-right`) | BmAK values above mapped onto donor rows `Sport_Muscle_Rear_Break_Left/Right` (hash **1700993006** / **4016595472**) |

So the BmAK brake state is a **lamp plus a code-driven component**, not a decoded ribbon: there are no
emitter values to copy, which is the correct reason the FX card turned into an omission — but the
omission should say "component with no serialised system", not "donor keeps a trail system".

## 4. JC3 side: what a tail lamp is, and what it can carry

### 4.1 The light entry (`VehicleDynamicLights`), 25 members

3,217 entries over 223 vehicles (`LIGHT_SYSTEM.md` §1). Every entry carries its own numbers; a
preset does **not** fix them (34 presets appear with more than one value tuple, `:128`).

| member | type | census (`LIGHT_SYSTEM.md:73–88`) |
|---|---|---|
| `range` | float | 10 ×1667, 2 ×669, 30 ×351, 1 ×332, 50 ×66, 3 ×39, 0.5 ×34, 2.5 ×12 |
| `angle` | float | 10 ×2494, 40 ×628, 50 ×74, 45 ×12, 30 ×4, 25 ×3, 35 ×2 |
| `diffuse.R/G/B` | float | per entry (the tail colour) |
| `multiplier` | float | 1 ×2188, 2 ×792, 0.5 ×174, 0.7 ×30, 3 ×12, 5 ×12, 0.3 ×6, 0.4 ×3 |
| `min_luminosity` | float | 0 ×3217 |
| `falloff_start` | float | 0.8 ×2210, 0 ×744, 0.3 ×170, 0.1 ×63, 0.6 ×30 |
| `near_cap` | float | 1 ×2044, 0 ×1173 |
| `volume_intensity` / `volumetric_mode` | float / int16 | 1 ×2044, 0.01 ×1171 / 0 ×3215 |
| `light_type`, `blinking`, `cast_shadows`, `projected_texture_index`, `uvscale.u/v` | int/float | see §1 table |
| `behavior` + `behavior_hash` | string + uint32 | the state name (below) |
| `part`, `part_hash`, `part_index`, `deformable_transform` | string/uint32 | what the lamp hangs on |

**Behaviour vocabulary** (`LIGHT_SYSTEM.md:58–66`): `None` 1177, `HeadLight` 1027, `TailLight` 301,
`LeftSignal` 253, `RightSignal` 253, `Reverse` 191, `SirenLightOn` 9, `SirenLightOffOnFast` 3,
`SirenLightOnOffFast` 3. There is **no `Brake` behaviour** and no member that ramps brightness on an
input; the closest carrier of "the lamp gets brighter" is `multiplier` (a static per-entry number),
and the closest state is `TailLight`.

### 4.2 The donor's tail-lamp rows (the ones the build inherits)

`t14_lights.json` donor module row 0:

| field | value |
|---|---|
| `behavior` | `TailLight` |
| `part` / `part_index` | `sportsmuscle_taillight_r_l` / 8 |
| `preset_id` / `preset` | **1435191809** / `Rear_Left_Point` |
| `diffuse` | **[1.0, 0.247850001, 0.0789999962]** (TailLight fleet default, `LIGHTS.md:46`) |
| `range` / `angle` / `multiplier` | **2.0 m** / **10°** / **2.0** |
| `light_type` | 0 |
| `deformable_transform` | `\|sportsmuscle_LOD1\|body\|taillight_r_l\|taillight_r_l_LIG` |
| sibling row (signal) | `LeftSignal`, preset **1358616627** `Rear_Left_Turn`, diffuse **[1.0, 0.268, 0.085]**, multiplier 2.0, same part |

The build's own mapping (T-18) sends BmAK `BrakeLightL/R` onto donor rows
`Sport_Muscle_Rear_Break_Left` (hash 1700993006, object diffuse **[1.0, 0.1, 0.0]**, radius 1.5,
spot_angle 60, spot_inner 0, multiplier 0.5, volume 0.25, near_cap 0.1) and
`Sport_Muscle_Rear_Break_Right` (hash 4016595472, same numbers), with proposed diffuse
**[1.0, 0.14902, 0.0]** (T-L15/T-L16).

### 4.3 The build's tail lamps (`Working/Appearance/build_lights`)

`lights_manifest.json` (B-03, generator `bm_lights.py --write`) carries **8 lamp parts**, each with
`lamp_elements`, `bones`, `clusters`, `faces_lod0`, `face_indices`, `pivot_m` and the
`to_jc3_rot * 0.01 + offset` transform:

| part | kind | parent | faces_lod0 | pivot_m |
|---|---|---|---:|---|
| `sportsmuscle_headlight_f_l` | head-lamp lens | body | 378 | [0,0,0] |
| `sportsmuscle_headlight_f_r` | head-lamp lens | body | 378 | [0,0,0] |
| `sportsmuscle_wheel_f_l_arch` | wheel-arch light | wheel_f_l | 612 | [−1.208, 0.7047, −2.5699] |
| `sportsmuscle_wheel_f_r_arch` | wheel-arch light | wheel_f_r | 612 | [1.208, 0.7047, −2.5699] |
| `sportsmuscle_wheel_r_l_arch` | wheel-arch light | wheel_r_l | 1146 | [−1.2845, 0.7027, 2.4589] |
| `sportsmuscle_wheel_r_r_arch` | wheel-arch light | wheel_r_r | 1146 | [1.2845, 0.7027, 2.4589] |
| **`sportsmuscle_tailstrip_r_l`** | **tail strip** | body | 152 | [0,0,0] |
| **`sportsmuscle_tailstrip_r_r`** | **tail strip** | body | 152 | [0,0,0] |

Two facts matter here:

* The tail lamps in the build are **geometry** (emissive strip meshes, 152 faces each), not light
  entries: the light rows T-L15/T-L16 anchor to `sportsmuscle_body` / `SUSP2_Wheel_Rear_*` bones, so
  no dynamic-light entry hangs on `sportsmuscle_tailstrip_*`. A streak emitter added to the build has
  no tail-strip part to parent to unless B-04 gives one a part index.
* `block_values.status` is **UNKNOWN**: "the CarLight material parameters are undecoded (MODLOG §102d),
  so the header/mid-static/texture table are cloned byte-exact from the template and no T-18 number is
  written into the block". The emissive strip's own brightness is therefore not a decoded value.

## 5. Boost / nitro and motion blur in JC3

| question | answer | evidence |
|---|---|---|
| boost trail effect | **exhaust flame, not a tail streak**: `effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc` — 17 vehicles (its non-dual sibling 130); the donor `.ee` carries it (20,671 B, 3,161 rows, 337 arrays, root `EffectRTSystem`) | `FX_TABLE.jsonl`; FX-1/T-FX7 row |
| any brake/boost *trail* .effc | **0** of 955 paths match `brake`; `trail` gives 84 paths (46 vehicle-carried) — dust, missile, spark, explosion trails | `FX16_TERM.md` table; T-FX20 negative |
| streak texture | `effects/textures/t_velocity_streak_alpha_dif.dds.1_1a.trim` **162** containers, `…1_1b.trim` **377** containers; donor carries **1_1b** (657 B, 28 rows, 3 arrays). `.trim` root `EffectTrimData`, members `Vertices[]Array[]`, `AnimFramesX/Y` (1…15) — a strip texture, i.e. the closest thing JC3 has to a glowing streak asset | `FX.md` `.trim` table; `FX_TABLE.jsonl` donor rows |
| ribbon/beam emitter type in `.effc` | **no member name** contains ribbon/beam/streak; `.effc` root `EffectRTSystem` exposes `Emitters[]`, `EmitterTemplates[].EmitterParams[]`, `Timelines[]`, `Modifiers[]` — parameter arrays, not named emitter kinds | `FX.md` `.effc` table (94 member paths); `FX_VOCAB.json` (0 matches for `Ribbon|Beam|Streak|Trail`) |
| motion blur | **camera-side only**: `.ctunec` root classes include `MotionBlurModifierParams` and `RadialBlurParams`; the donor `.ee` ships 17 camera tunes (`car_base.ctunec`, `vehicle_motion.ctunec`, `full_screen_effect.ctunec`, …). No vehicle, light or weapon member carries a motion-blur flag, and no brake/boost trigger is decoded | `FX.md:66`; `FX_TABLE.jsonl` donor `.ctunec` rows |
| BmAK's own motion blur (for contrast) | `BmSystemSettings.ini` `SystemSettings.MotionBlur` 1, `MotionBlurSkinning` 1, `DefaultMotionBlur` True — a **global** renderer setting, not a per-vehicle flag | `CONFIG.md:641–651` |

## 6. Side by side: the brake look

| quantity | BmAK | JC3 closest member | bridge | verdict |
|---|---|---|---|---|
| lamp colour | `LightColor` **[255, 38, 0, 0]** (8-bit RGBA) | `diffuse.R/G/B` on a `TailLight` entry | sRGB byte → float /255: **1.0, 0.14902, 0.0** (T-18 `proposal_diffuse`) | **exact carrier** for the glow |
| lamp brightness | brightness **1.0** | `multiplier` **2.0** on the donor TailLight row | scalar 1:1 (meaning of multiplier vs UE brightness not derived) | **partial** — value exists, unit not proven |
| lamp radius | **150 uu = 1.5 m** | `range` **2.0 m** | `/100` | **partial** — closest row is 2.0, not 1.5 (BmAK 150 uu is the point light's radius) |
| falloff | **6.0** | `falloff_start` 0.8 | no derived mapping (UE falloff exponent vs JC3 fraction) | **gap** |
| flare | `LensFlareComponent` → `Engine.Batmobile_brakelights` | — (JC3 light module has no flare: `LIGHTS.md:59–60`) | — | **gap**, out of this card's scope |
| brake state (brighter when braking) | behaviour `TailLight` on `VEHLT_TailLight` | behaviour `TailLight` **is** the only tail state; no `Brake`, no input member | — | **gap**: trigger |
| glowing streak behind the lamps | `BrakeTrail0/1` components, no serialised system | **no** light member, **no** ribbon member; closest asset `t_velocity_streak_alpha_dif` `.trim` inside an authored `.effc` | — | **gap**: carrier + trigger |
| trail width/length/colour | **UNKNOWN** — component has no template | — | — | **UNKNOWN**, would be settled by the code that assigns the template |

## 7. Answer to the question asked

* **Ribbon emitter?** No — there is no ribbon emitter member in JC3's effect format or light module to
  set. An `.effc` can be *authored* to look like a streak (the `t_velocity_streak_alpha_dif` trim is
  the asset for it), but nothing in the decoded data is "a ribbon emitter" with parameters.
* **Light member?** No — the 25 light members describe a lamp (`range`, `angle`, `diffuse`,
  `multiplier`, `volume_intensity`, …). None attaches geometry, a trail or an effect, and the
  behaviour set has no brake state.
* **Neither, as data.** The streak needs a new effect plus a brake trigger; both are build work.

## 8. Closest system + gap + build action (STAGES.md)

STAGES.md: **"JC3 has no system" is never an answer** — record the closest system with member paths
and values, name the gap, and let BUILD close it (`STAGES.md:4`); BUILD may "compose several systems
where the closest one is short" and "author geometry/textures/banks" (`STAGES.md:10`).

* **Closest carrier for the streak:** an `.effc` (`EffectRTSystem`) using the existing
  `t_velocity_streak_alpha_dif.dds.1_1b.trim` strip (already shipped in the donor `.ee`), attached at
  the tail socket. The donor already demonstrates the pattern: `car_cycle_base_dual_nitrous.effc`
  (20,671 B, 3,161 rows) is a boost-glow effect carried by the vehicle `.ee`.
* **Closest carrier for the glow:** the donor `TailLight` entry (`range` 2.0, `angle` 10,
  `multiplier` 2.0, diffuse [1.0, 0.24785, 0.079], preset `Rear_Left_Point`), which the build already
  re-points at `Sport_Muscle_Rear_Break_Left/Right`.
* **The gap, exactly:** (a) no member binds an effect to a light or to a part for a brake event;
  (b) no brake input/behaviour is decoded (behaviour vocabulary has 9 states, no Brake);
  (c) BmAK's own trail component has no serialised system, so its width/length/colour are UNKNOWN.
* **Build action:** in `Builds/bm-RC4*`, author a private `.effc` streak (ribbon-like appearance built
  from the `.trim` strip) parented at the rear lamp parts, and author the trigger with the vehicle's
  available state machine — then read the values back through the built `.toc` like any other row.
  Until the trigger exists, the row must stay `closest + gap + build action`, not `out`.
* **Correction to file:** T-FX20's "donor's own BrakeLightTrailSystemL/R stays (T-FX6)" should read
  "BmAK `BrakeTrail0/1` components have no serialised system; the JC3 donor has no brake-trail object
  (`Rear_Brake` light only); 0 of 955 `.effc` paths is a brake trail." That is the defensible version
  of the same omission.

## 9. Evidence index

| # | path | proves |
|---|---|---|
| 1 | `Research/BatmobileGrab/objects.jsonl` (Playable_BatmobileFunhouse_SF 5096/5097; Joker 2612/2613; LensFlare 336/337/343) | `BrakeTrail0/1` component with no template; `ParticleModuleTypeDataTrail2` values; flare reference |
| 2 | `Research/BatmobileGrab/LIGHTS.md:46`, `:59–60`, `:197–200`, `:290–292` | TailLight defaults; brake lamp components, colour, radius, falloff, flare |
| 3 | `Research/BatmobileGrab/LIGHTS.json`, `LIGHT_SOCKETS.json` | the same rows in machine form (socket `BrakeLightL/R`) |
| 4 | `Research/BatmobileGrab/ASSETS.md:309–310`, `:475–476` | `BrakeTrail0/1` in the `ParticleSystemComponent` class census; no brake system in the `ParticleSystem` lists |
| 5 | `Research/BatmobileGrab/PARTICLES_FEATURES.json` | 0 of the 206 systems match `brake` |
| 6 | `Research/JC3Grab/LIGHT_SYSTEM.md` §1–§4 | the 25 light members, behaviour vocabulary, preset census, donor rows |
| 7 | `Research/JC3Grab/FX.md:26`, `:66`, `.effc`/`.trim` tables | 25,707 `.trim` files; `MotionBlurModifierParams`/`RadialBlurParams`; 94 `.effc` member paths |
| 8 | `Research/JC3Grab/FX_TABLE.jsonl` | donor carrying `car_cycle_base_dual_nitrous.effc` (20,671 B) and `t_velocity_streak_alpha_dif.dds.1_1b.trim` (657 B); 17 donor `.ctunec` rows |
| 9 | `Research/JC3Grab/FX_VOCAB.json` | 0 member names matching `Ribbon|Beam|Streak|Trail` |
| 10 | `Working/Translation/t14_lights.json` (donor row 0, T-L15, T-L16; summary: 28 rows, 22 mapped, 6 omitted) | the Batmobile tail rows and the brake-lamp mapping |
| 11 | `Working/Translation/T13_FX.md:70`, `Tools/scripts/t17_fx.py:193` | T-FX20 as filed, and the claim corrected in §2 |
| 12 | `Working/Translation/FX16_TERM.md` | `trail` = 84 of 955 (46 vehicle-carried), `brake` = 0 |
| 13 | `Working/Appearance/build_lights/lights_manifest.json` | 8 lamp parts incl. two 152-face tail strips; `block_values` UNKNOWN |
| 14 | `Research/BatmobileGrab/CONFIG.md:641–651` | BmAK motion blur is a global `SystemSettings` flag |
| 15 | `STAGES.md:4`, `:9`, `:10` | closest-system rule, TRANSLATE contract, BUILD compose/author mandate |

## 10. UNKNOWN / limits

1. **BmAK trail parameters** — `BrakeTrail0/1` serialise no `Template`, so the system (and its
   width/length/colour/rate) is not in the grabbed packages. Settle by finding the code or a
   different package that assigns the component's template.
2. **What the component floats mean** (@364: Funhouse 0.9102755784988403 / 0.7530137300491333,
   Joker 0.7800225615501404 / 0.9793389439582825, MK2 0.2716757655143738 / 0.2055421620607376) —
   the tag is unnamed in the stream and no SDK field maps it; not interpreted.
3. **Brake behaviour in JC3** — no member and no state is named brake; whether the engine brightens a
   `TailLight` entry on the brake input is a Q-2 A5 probe, not a decode.
4. **`multiplier` vs UE brightness** — both are scalars but no file states the unit or range
   correspondence; the 1.0 → 2.0 line in §6 is a value pairing, not a derived conversion.
5. **Lens flare** — JC3's light module has no flare, and `Working/Appearance/build_lights` clones the
   CarLight block byte-exact because its material parameters are undecoded (`MODLOG §102d`).
6. **No in-game look** — the streak's appearance under braking is a TEST-stage question; the test ban
   holds until `tmp/freebuff/APPROVED_Q.txt`.
