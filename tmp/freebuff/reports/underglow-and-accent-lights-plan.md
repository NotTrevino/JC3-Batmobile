# Accent and underglow lights — what BmAK actually shows, and the JC3 carrier

**STATUS: done (plan, read-only).** BmAK has **no underglow at all** — no underbody light, no neon,
no `underglow` token anywhere in its 101 light entries, its class defaults or its research. What it
does have is **five accent families**, all steady (no pulse, no flicker), and the wheel accent is a
**material emissive texture, not a lamp**: `Batmobile_V3_Emissive` with
`Emissive_Map = Engine.Batmobile_V3_Wheel_E` and `Material_Separation_Mask =
Batmobile_V3_Wheel_Lights_M`, assigned to the body **and all four wheels**.

JC3's carrier is the **`VehicleDynamicLight` module entry** (the only light class with a part binding
and a `deformable_transform` anchor, so it can sit on a private body node). It carries a **static
`diffuse`** — there is **no mode-switched colour member** in any decoded JC3 class. A mode change has
to be **two entries on the same anchor** with different colours, and the only decoded state carriers
are the `behavior` enum and `blinking`.

---

## 1. Every accent light BmAK ships (base `Playable_Batmobile_SF`)

All values decoded from `LIGHTS.md` §"Component light values (G1-17)" and the matching `LIGHTS.json`
records. `Brightness`, `Radius` in cm, cones in degrees.

| socket | bone / position | type | colour [R,G,B,A] | brightness | radius | inner/outer | falloff | what it is |
|---|---|---|---:|---:|---:|---|---:|---|
| `LWheelLight` | `Wheel_Frnt_Left_Disc` @ [-0.350, 50.689, 26.0] | `VEHLT_HeadLight` | **[160, 180, 255, 0]** | **0.0** | **0.0** | –/0.0 | 1.0 | wheel-arch lamp, **unlit** |
| `RWheelLight` | `Wheel_Frnt_Right_Disc` @ [0.381, 46.332, 25.752] | `VEHLT_HeadLight` | **[160, 180, 255, 0]** | **0.0** | **0.0** | –/0.0 | 1.0 | mirror, **unlit** |
| `LWheelLight_top` | `Wheel_Frnt_Left_Disc` @ [-0.119, 40.600, 40.000] | `VEHLT_HeadLight` | flare only, [1,1,1,1] | – | – | – | – | **lens flare only** |
| `LWheelLight_bottom` | same disc @ [-0.293, 56.499, 10.500] | `VEHLT_HeadLight` | flare only | – | – | – | – | flare only |
| `RWheelLight_top` / `_bottom` | right disc, mirrored | `VEHLT_HeadLight` | flare only | – | – | – | – | flare only |
| `BootLight` | boot/hatch socket | `VEHLT_BootLight` | **[152, 255, 225, 0]** | **5.0** | **400.0** | **50 / 60** | 2.0 | teal boot accent |
| `Dashboard_Light` | dashboard | `VEHLT_Interior` | **[172, 245, 255, 0]** | **5.0** | **80.0** | **20 / 45** | 2.0 | cyan interior accent |
| `Dashboard` (Joker only) | dashboard | `VEHLT_Interior` | **[173, 119, 240, 0]** | **0.2** | **80.0** | point | 2.0 | violet interior accent |
| `BattleModeSpotLight` | `Batmobile_Rig_Weapons_Drone_Decoder` | `VEHLT_BattleModeLight` | **[255, 255, 255, 0]** (Joker **[100, 50, 255]**) | **0.0** | **4500.0** | **5 / 15** | 1.0 | battle spotlight |
| `BattleModeSpotLight` | same | `VEHLT_ForensicsLight` | **[195, 255, 244, 0]** | 0.0 | 0.0 | –/0.0 | 1.0 | forensics (unlit) |
| `HeadLight1/2` | chassis | `VEHLT_BattleModeLight` | **[255, 0, 0, 0]** | **5.0** | **1024.0** | **10 / 35** | 2.0 | red battle headlights |
| `HeadLight1/2` | chassis | `VEHLT_ForensicsLight` | **[255, 0, 0, 255]** | 5.0 | 1024.0 | 10 / 35 | 2.0 | red forensics headlights |
| `ChainGunMuzzle` | `…Machine_Gun_01` | – | [255,255,255] | 1.0 | 4096.0 | –/50 | 1.0 | muzzle, **not an accent** |

### 1.1 The wheel accent is a material, not a lamp

This is the single most important finding for the port. The `LWheelLight`/`RWheelLight` **spot
components are zeroed** (`Brightness 0.0`, `Radius 0.0`, `OuterConeAngle 0.0`, colour alpha 0). What
actually glows on the arch is:

| material slot | material | emissive wiring | where it is used |
|---|---|---|---|
| 5 | `Batmobile_V3_Emissive` → `Engine.Batmobile_V3_Body_MAT` | `Emissive_Map = Engine.Batmobile_V3_Wheel_E`; `Material_Separation_Mask = Textures.Batmobile_V3_Wheel_Lights_M`; `Normal_Map = Textures.Batmobile_V3_Wheel_Lights_N` | **body + wheel_f_l + wheel_f_r + wheel_r_l + wheel_r_r** (`SLOTS.md:30`) |

So the accent is a **texture-driven emissive with a mask**, shipped on the wheels themselves, and it
is the same material in every mode (no colour parameter, no mode variant). The `_top`/`_bottom`
sockets add **lens flares** on top of it.

### 1.2 Underglow: absent

| check | result |
|---|---|
| light sockets with an under/floor name | **0 of 21 distinct sockets** (`LIGHTS.md` per-vehicle tables; sockets are `HeadLight*`, `LWheelLight*`, `RWheelLight*`, `BrakeLight*`, `BootLight`, `Dashboard*`, `BattleModeSpotLight`, `ChainGunMuzzle`) |
| `underglow`/`neon`/`underbody`/`accent` token in BmAK research | **0 hits** (`Research/BatmobileGrab/*.md`) |
| under/glow members in the vehicle class defaults | **0** (`CLASS_DEFAULTS.md` has no `Glow`, `Underglow`, `UnderLight`, `RimLight`) |
| floor-facing spot anywhere | none: the two unlit wheel lamps point sideways from the disc, `BootLight`/`Dashboard` are enclosed |

**Conclusion:** "Batmobile underglow" in BmAK is the **wheel-arch emissive**, seen low and wide; there
is no separate underbody lamp to port. Anyone adding a true underglow is adding a feature.

### 1.3 Pulse: absent

| modulation field | BmAK |
|---|---|
| `blinking` | not a BmAK component field; no light in the 101 entries is blinking |
| flicker / pulse / throb | **0 hits** in `LIGHTS.md`, `LIGHTS.json`, `CLASS_DEFAULTS.md` (`pulse` appears only in **audio** event names, `AUDIO.md:91`) |
| animated brightness | none: every `Brightness` above is a static constant |
| lens flare strength | `MinStrength` ships nowhere (`LIGHTS.md:178-181`), so even the flare cannot pulse from data |

All five accent families are **steady**. The only thing that "changes" per mode is the **colour of the
battle/forensics entries** and the battle **spotlight**, which are separate entries, not a modulation.

## 2. Colour per mode

| accent | normal (pursuit) | battle | forensics |
|---|---|---|---|
| wheel arch lamp | **[160, 180, 255]** blue-violet, unlit | **[255, 0, 0]** red, radius 2048 cm, 5°/15°, brightness **0.0** | not present |
| wheel arch emissive (material) | `Batmobile_V3_Wheel_E`, no colour param | same material | same material |
| boot | **[152, 255, 225]** teal, 5.0 | same entry (no battle variant) | same |
| interior | **[172, 245, 255]** cyan, 5.0 (Joker **[173, 119, 240]** violet, 0.2) | same | same |
| battle spotlight | white [255,255,255], brightness 0.0 | **[255, 255, 255]** white, 4500 cm, 5°/15° (Joker **[100, 50, 255]**) | **[195, 255, 244]** mint, unlit |
| headlights | **[138, 197, 246]** | **[255, 0, 0]**, 5.0, 1024 cm | **[255, 0, 0]**, 5.0, 1024 cm |

The mode vocabulary is BmAK's `VEHLT_*` enum: `HeadLight` 46, `BattleModeLight` 16, `ForensicsLight`
12, `Interior` 4, `BootLight` 3, `TailLight` 8, stripped 12 (`LIGHTS.md` summary). **Battle and
forensics are separate light entries on the same sockets**, not a recolour of one light.

## 3. The JC3 class that can carry this

### 3.1 What can sit on a private body node

**`VehicleDynamicLight` module entry** — the recipe in `LIGHT_SYSTEM.md` §7 is exactly this: 25
members per entry, a `part` + `part_index` binding, and a `deformable_transform` node chain that can
name **any private body node** (the card's example is
`|sportsmuscle_LOD1|wheel_f_l|Wheel_Frnt_Left_Disc|Wheel_Frnt_Left_Disc_LIG`). The fleet ships
**3,217** of these on **223 vehicles**, so the class is proven for per-part lights.

| JC3 member | accent use | note |
|---|---|---|
| `deformable_transform` | **the private body node** | this is the "sit on a body node" member |
| `part`, `part_index`, `part_hash` | binds to the part | must exist in the parts module |
| `diffuse.R/G/B` | **the colour** | static per entry; sRGB 0..1 |
| `range`, `angle` | reach and cone | `range` census 0.5–50; `angle` 10–50 |
| `multiplier` | how hot it reads | 1 is the fleet mode |
| `blinking` | **the only modulation** | 0 steady (2,553), 1 pulsing (664) |
| `behavior` | which state drives it | `HeadLight` 1027, `TailLight` 301, signals, `Reverse` 191 |
| `near_cap`, `falloff_start`, `min_luminosity`, `light_type`, `cast_shadows`, `volume_intensity`, `volumetric_mode`, `uvscale`, `projected_texture_index` | the rest of the lamp | all carry their own values; `preset_id 0` is legal (17 shipped entries) |

The `.epe` side adds **`SVehicleLight`** objects with `enabled`, `radius`, `spot_angle`,
`spot_inner_angle`, `preset_id` as a **string**. That side is where an inner cone lives, but it has
**no part binding** — `LIGHT_SYSTEM.md` §2 records that which side the renderer reads is **UNKNOWN**,
so a body-node accent must be built on the module side.

### 3.2 Mode-switched colour: no native member

| candidate mechanism | verdict |
|---|---|
| one entry, colour changed by mode | **not possible**: `diffuse` is a static member, no mode-conditioned field in any decoded class |
| two entries on the same anchor, one enabled per mode | **possible in data**; the switch itself is **not decoded** (no `enabled` in the module; `.epe` `enabled` exists but is not mode-driven) |
| `behavior` enum as the switch | **decoded**: `HeadLight` → `TailLight` → `Reverse` → signals are the state vocabulary the game drives; battle/forensics modes have **no** JC3 behaviour |
| `blinking` as a pulse | **decoded**: 664 entries pulse; the police siren pair is the only shipped **two-colour pulse**, `SirenLightOnOffFast` red [1, 0.185, 0.185] and `SirenLightOffOnFast` blue [0.185, 0.3132, 1] (`LIGHT_SYSTEM.md:142-147`) |
| `CLightWeaponComponent` | a **light** component (not a gun) that hangs on a weapon — 30 components on **9** entities (`WEAPON_WIRING.md:95,2030`). **Decoded members, from the medium tank's `warning_light` on `w602_mediumtank_canon`:** `Color` **1,1,1,1**, `SpotLight` **1**, `Radius` **0.5**, `Height` **5**, `FalloffStart` **1**, `Priority` **5**, `ProjectedTextureIndex` **12**, plus four `id:`-hashed colour slots that all read **1,0,0,1** (`WEAPON_WIRING.jsonl`, `w602_mediumtank_canon` → `components[0]`). That is a genuine colour + reach + spot light whose state follows the weapon, i.e. a hardware **switch** on a private node — the only decoded accent that can turn itself on |

**Honest answer:** the JC3 class that can **sit on a private body node** with a colour is
`VehicleDynamicLight`; there is **no decoded mode-switched colour** anywhere, so a two-colour accent
is **two entries plus an external toggle**. The only two decoded toggles are the `behavior` state and
`CLightWeaponComponent`'s weapon state. If the accent must pulse, `blinking = 1` is the carrier and
the siren pair is the proven pattern.

**The one class that actually switches colour on demand** is `CLightWeaponComponent`: its shipped
`warning_light` carries `Color 1,1,1,1` **and** `1,0,0,1` in its hashed slots, `SpotLight 1`, a
`Radius 0.5` reach and a `Height 5` — a light bound to a weapon's state. For a mode-switched accent,
that is the only decoded mechanism (the mode would have to drive the weapon/component's active
state). Its caveat is honest: the hashed `id:` slots mean the semantic name of each colour field is
**not** decoded, so the two-colour wiring is inferred from the values (white **and** red on one
light), not from a named member.

## 4. Our values

| accent | our JC3 entry | colour | other members | flag |
|---|---|---|---|---|
| wheel arch, normal | entry A on `|sportsmuscle_LOD1|wheel_f_l|Wheel_Frnt_Left_Disc|Wheel_Frnt_Left_Disc_LIG` | **0.6275 / 0.7059 / 1.0** | `range 2`, `angle 10`, `multiplier 1`, `near_cap 1`, `falloff_start 0`, `blinking 0`, `cast_shadows 0`, `preset_id 0` | colour **M** (÷255 of [160,180,255]); lamp shape **G** (BmAK's own is zeroed) |
| wheel arch, battle | entry B, same anchor | **1.0 / 0.0 / 0.0** | `range 20.48 m`, `angle 15`, `falloff_start 0`, `multiplier 1` | colour/radius **M**; multiplier **G** (BmAK brightness 0.0) |
| boot | entry on the boot node | **0.5961 / 1.0 / 0.8824** | `range 4.0 m`, `angle 60`, `falloff_start 0.8`, `multiplier 1` | colour/reach/cone **M**; falloff **G** |
| interior | entry on the dashboard node | **0.6745 / 0.9608 / 1.0** | `range 0.8 m`, `angle 45`, `falloff_start 0.8`, `multiplier 1` | colour/reach/cone **M**; falloff **G** |
| interior, Joker | alternative entry | **0.6784 / 0.4667 / 0.9412** | point light, `range 0.8 m`, `multiplier 0.2` | colour/brightness **M** |
| battle spotlight | entry on the drone-decoder node | **1.0 / 1.0 / 1.0** (Joker **0.3922 / 0.1961 / 1.0**) | `range 45.0 m`, `angle 15`, `falloff_start 0` | colour/reach/cone **M**; brightness **G** (0.0) |
| underglow | **do not build one** | — | — | BmAK has none; adding it is a feature |

Unit conversions used above: 400 cm = 4.0 m, 80 cm = 0.8 m, 4500 cm = 45.0 m, 2048 cm = 20.48 m.
Every colour is a lossless ÷255 of a decoded byte triple; nothing was invented except the multiplier
and falloff values, which are flagged **G**.

## 5. What this means for the build

1. **Do not add an underglow.** BmAK's low accent is the **wheel emissive material**. Port that
   first: copy the `Batmobile_V3_Emissive` wiring (`Emissive_Map = Batmobile_V3_Wheel_E`, mask
   `Batmobile_V3_Wheel_Lights_M`) into the wheel material, which is where the look actually lives.
2. **The arch lamp is optional and dim.** Its BmAK spot is zeroed; our entry is a deliberate
   fill-in with the decoded colour. Keep `multiplier 1` — BmAK's own brightness is 0.0, so anything
   above 1 is brighter than source.
3. **Battle colour = a second entry, not a recolour.** There is no mode member in JC3; the switch has
   to come from the mode system (`TryToChangeMode` / `DriveMode` 0x3B0) or from a weapon-state light.
4. **No pulse unless asked.** BmAK has no modulation; `blinking = 1` would be an addition. If a pulse
   is wanted, the siren pair is the proven two-colour pattern to copy.
5. **Interior and boot are free wins**: they are real lit lamps in BmAK (brightness 5.0) with decoded
   colour, reach and cones, and they need no mode switch.

## 6. Checks run

| check | result |
|---|---|
| accent rows re-read | `LWheelLight`/`RWheelLight` [160,180,255] 0.0/0.0/0°, `BootLight` [152,255,225] 5.0/400/50-60°, `Dashboard_Light` [172,245,255] 5.0/80/20-45°, `BattleModeSpotLight` 4500/5-15°, battle/forensics headlights [255,0,0] 5.0/1024/10-35° (`LIGHTS.md`, `LIGHTS.json`) |
| wheel light really unlit | `Brightness 0.0`, `Radius 0.0`, `OuterConeAngle 0.0`, colour alpha 0 (`LIGHTS.json` spot components; `LIGHT_SYSTEM.md` §7 states the same) |
| the real wheel glow | `Batmobile_V3_Emissive` slot 5 with `Emissive_Map = Engine.Batmobile_V3_Wheel_E`, mask `..._Wheel_Lights_M`, used on body + 4 wheels (`SLOTS.md:30`) |
| underglow absence | 0 under/floor sockets in 21; 0 `underglow`/`neon` hits; 0 `Glow`/`Under` members in `CLASS_DEFAULTS.md` |
| pulse absence | 0 pulse/flicker fields or hits in BmAK light data (`pulse` only in audio event names) |
| JC3 carrier | `VehicleDynamicLight` 3,217 entries / 223 vehicles, 25 members incl. `diffuse`, `blinking`, `behavior` (`LIGHT_SYSTEM.md` §1, §7) |
| JC3 switches | no mode-conditioned colour member; `blinking` 664 entries; siren pair red/blue with `blinking` 1 (`LIGHT_SYSTEM.md:142-147`) |
| alternate class | `CLightWeaponComponent` = a light on a weapon, 30 components / 9 entities (`WEAPON_WIRING.md:95,2030`) |
| colour arithmetic | 160/255 = 0.6275; 180/255 = 0.7059; 152/255 = 0.5961; 225/255 = 0.8824; 172/255 = 0.6745; 245/255 = 0.9608; 173/255 = 0.6784; 119/255 = 0.4667; 240/255 = 0.9412; 100/255 = 0.3922; 50/255 = 0.1961; 195/255 = 0.7647; 244/255 = 0.9569 |

## 7. Change record (per `AGENTS.md`)

1. **Intended change:** add one report listing BmAK's accent lights, their per-mode colours and pulse
   state, and naming the JC3 class that can carry them on a private body node.
2. **File:** `tmp/freebuff/reports/underglow-and-accent-lights-plan.md` (this file). Correct file
   because the brief names it; the existing `LIGHTS-sockets.md` and `T-15.md` cover socket binding and
   battle-mode carries, not the accent inventory. No `Research/` page, light module or material is
   written.
3. **Revert:** delete this file. Nothing else changed; no light entry, material, part or build was
   modified.

## 8. UNKNOWNs

| # | UNKNOWN | what settles it |
|---|---|---|
| U-1 | what `Batmobile_V3_Wheel_E` looks like and whether it changes with mode | open the texture; `SLOTS.md` records the wiring but not the pixels |
| U-2 | whether BmAK's zeroed wheel spot is deliberately off or a leftover | all four packages ship it zeroed, so treat "off" as intended until footage says otherwise |
| U-3 | the full member list of `CLightWeaponComponent` | not in the files read this pass; needs a direct decode of the 30 components on the 9 entities |
| U-4 | how a mode-switched colour could be driven at runtime | no decoded member; the mode system (`DriveMode` 0x3B0) plus two light entries is the only path |
| U-5 | which side the renderer reads (module vs `.epe`) | `LIGHT_SYSTEM.md` §2, Q-1 probe |
| U-6 | whether an `SVehicleLight.enabled` toggle is honoured at runtime | the `.epe` objects carry `enabled 1` everywhere; no decoded switch path |
