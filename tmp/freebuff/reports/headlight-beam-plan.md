# Headlight beam — BmAK's cone, reach, colour and flicker against a JC3 spot light

**STATUS: done (plan, read-only).** BmAK's headlight is **two `SpotLightComponent`s per socket**:
a **wide 70° outer cone, 20° inner, 60.0 m reach**, colour **[138,197,246]**, Brightness **0.15**,
falloff 1.0; plus a **narrower repeat at 18.0 m, falloff 2.0** on the same socket and same colour.
JC3's module has **one cone (`angle`), one reach (`range`), an RGB triple and no colour temperature
and no flicker field**; the `.epe` side adds `spot_inner_angle`, which is where BmAK's 20° inner
cone can live.

Legend used on every number below: **M** = measured (decoded from a shipped file), **D** = derived
(arithmetic on measurements, method printed), **G** = guess (no decoded basis — the first thing to
tune).

---

## 1. BmAK's numbers, per socket

Source: `LIGHTS.md` §"Component light values (G1-17)", the `Playable_Batmobile_SF` rows (identical
in `Playable_BatmobileMK2_SF` and `Playable_BatmobileFunhouse_SF`; the Joker variant is listed in §6).

| BmAK field | value | flag | where |
|---|---:|---|---|
| socket | `HeadLight1` (+ `HeadLight2` mirrored) | **M** | `LIGHTS.md` per-vehicle table |
| attachment | `Batmobile_Chassis` bone, socket at **[320.68, 38.58, 51.0] cm** | **M** | `LIGHTS.json` `socket_location` |
| component | `SpotLightComponent` ×2 per socket (plus a `LensFlareComponent`) | **M** | `LIGHTS.md:183+` |
| **outer cone** | **70.0°** | **M** | `LIGHTS.md` row `Playable_Batmobile_SF HeadLight1` |
| **inner cone** | **20.0°** | **M** | same row |
| **reach (radius)** | **6000.0 cm = 60.0 m** | **M** (conversion **D**) | same row |
| second spot's reach | **1800.0 cm = 18.0 m** | **M** (conversion **D**) | same socket, second `SpotLightComponent` row |
| **colour** | **[138, 197, 246, 255]** | **M** | same row, `colour from = component` |
| **intensity (Brightness)** | **0.15** | **M** | same row |
| falloff (spot 1 / spot 2) | **1.0 / 2.0** | **M** | same row |
| cast shadows | `False` / `CastDynamicShadows` `False` | **M** | same row |
| **flicker** | **none: no flicker field, no blinking field, steady lamp** | **M** (absence) | component table carries no such column; `LIGHTS.md:178-181` documents the only near-miss (`LensFlareComponent.MinStrength`) as not shipped |
| lens flare | `LensFlareComponent`, colour [1,1,1,1], **intensity not serialised anywhere in the install** | **M** | `LIGHTS.md:178-181` |
| battle variant | colour **[255,0,0]**, Brightness **5.0**, radius **1024 cm**, inner **10°**, outer **35°** | **M** | `LIGHTS.md` `VEHLT_BattleModeLight` rows |
| Joker variant | **[160,180,255]**, Brightness **4.0**, radius **3072 cm (30.72 m)**, inner **10°**, outer **35°** | **M** | `LIGHTS.md:240-241` |

**Two things this settles.** First, the beam is **not a single cone**: two spots share the socket, one
long and wide (60 m / 70°) and one short and hard-edged (18 m / 70°, falloff 2.0). Second, the car's
headlights are **dim by design** (Brightness 0.15) — the visible punch comes from the lens flare and
the emissive material, not from a bright light.

**Colour temperature: there is none.** Neither BmAK nor JC3 carries a Kelvin field. Converting the
RGB through sRGB→XYZ→McCamy gives **≈17,600 K** for [138,197,246], but that is **outside McCamy's
stated validity (2856–6504 K)** and the same method gives 6,504 K for pure white — so the 17.6 kK
figure is a **G**, not a measurement. What *is* measured is the RGB triple; ship that, not a Kelvin
number.

## 2. JC3's spot light members (module side)

Source: `Research/JC3Grab/LIGHT_SYSTEM.md` §1 (`VehicleDynamicLight` module, 3,217 entries) and §2
(`SVehicleLight` on the `.epe` side, 3,972 objects).

| JC3 member | type | census of shipped values | flag |
|---|---|---|---|
| `range` | float | `10`×1667, `2`×669, `30`×351, `1`×332, `50`×66, `3`×39, `0.5`×34, `2.5`×12 | **M** |
| `angle` | float (cone, degrees) | `10`×2494, `40`×628, `50`×74, `45`×12, `30`×4, `25`×3, `35`×2 | **M** |
| `falloff_start` | float | `0.8`×2210, `0`×744, `0.3`×170, `0.1`×63, `0.6`×30 | **M** |
| `multiplier` | float | `1`×2188, `2`×792, `0.5`×174, `0.7`×30, `3`×12, `5`×12 | **M** |
| `near_cap` | float | `1`×2044, `0`×1173 | **M** |
| `min_luminosity` | float | `0`×3217 | **M** |
| `light_type` | int32 | `0`×2494, `1`×723 | **M** |
| `blinking` | int | `0`×2553, `1`×664 | **M** |
| `cast_shadows` | int | `0`×3215, `1`×2 | **M** |
| `volumetric_mode` | int16 | `0`×3215, `1`×2 | **M** |
| `volume_intensity` | float | `1`×2044, `0.01`×1171, `0.02`×2 | **M** |
| `diffuse.R/G/B` | float | per entry | **M** |
| `projected_texture_index` | int8 | `-1`×3215, `0`×2 | **M** |
| `uvscale.u/v` | float | `1`×3217 | **M** |
| `.epe` `radius`, `spot_angle`, `spot_inner_angle` | floats | radius 0.2–0.6; spot_angle 15/20/25/30; **spot_inner_angle 0/10/20/30** | **M** |
| which side the renderer reads (module vs `.epe`) | — | **UNKNOWN** (`LIGHT_SYSTEM.md` §2) | — |
| colour temperature | — | **does not exist** | — |
| flicker | — | **does not exist**; `blinking` 0/1 is the only on/off-modulated member | — |

Behaviour vocabulary the beam must sit inside: `HeadLight` **1027** entries, `TailLight` 301,
signals 253+253, `Reverse` 191 (`LIGHT_SYSTEM.md` §1).

**The mapping limits are visible in the censuses.** BmAK asks for **70°** and **60 m**; JC3's
shipped `angle` tops out at **50** and its shipped `range` at **50**. Both are plain floats, so 70 and
60 are *writable*, but no vanilla entry ships either — that is a compile-and-look decision, not a
decoded one.

## 3. The mapping, and our values

| BmAK field | JC3 member | our value | flag on *our* value | note |
|---|---|---:|---|---|
| outer cone **70°** | `angle` | **70** (fallback **50**) | **M** copied, but **G** for JC3 compatibility | 70 is BmAK's measured cone; 50 is the largest angle any vanilla light ships, so if 70 renders as a hard-edged circle, drop to 50 |
| inner cone **20°** | `.epe` `spot_inner_angle` | **20** | **M** copied | exactly one of the shipped `.epe` values (0/10/20/30); the module side has no inner cone at all |
| reach **60.0 m** | `range` | **60** (fallback **50**) | **M** converted (6000 cm ÷ 100), **G** for JC3 compatibility | same caveat as the angle: 60 is a legal float, not a shipped one |
| second spot **18.0 m** | second entry `range` | **18** | **M** converted | keep it as a **separate entry** on the same anchor, with `falloff_start` 0 |
| **colour [138,197,246]** | `diffuse.R/G/B` | **0.5412 / 0.7725 / 0.9647** | **D** from **M** (÷255) | the one number pair that ports with no judgement |
| **Brightness 0.15** | `multiplier` | **1.0** | **G** | no decoded Brightness→multiplier conversion exists; 1.0 is the fleet mode (2,188 of 3,217). Tune down if the beam reads too hot |
| falloff 1.0 / 2.0 | `falloff_start` | **0.8** / **0.0** | **G** | BmAK's falloff is a spot exponent; JC3's is the fraction where falloff begins. Not the same quantity, so this is a look-alike, not a port |
| near cap | `near_cap` | **1** | **M** (donor steady lamp uses 1) | keeps the lamp from washing the bumper |
| min luminosity | `min_luminosity` | **0** | **M** (0 in all 3,217) | |
| light type | `light_type` | **0** | **M** (donor uses 0) | 0 = the normal spot kind in the fleet census |
| **flicker** | `blinking` | **0** | **M** for BmAK (no flicker); **G** that JC3 needs none | if a flicker is ever wanted, `blinking` 1 is the only shipped carrier (664 entries) |
| shadows | `cast_shadows` | **0** | **M** both sides | BmAK ships `CastShadows` False |
| volumetric | `volumetric_mode` / `volume_intensity` | **0** / **1.0** | **M** (donor values) | |
| projected texture | `projected_texture_index` | **-1** | **M** (no gobo in BmAK) | BmAK's beam has no projection texture |
| lens flare | — | **drop** | **M** | JC3's light module has no flare; the 55 BmAK `LensFlareComponent`s have no carrier (`LIGHTS.md` per-row "no-jc3-equivalent") |

**Round-trip check on the derived colour:** 0.5412×255 = 138.0, 0.7725×255 = 197.0, 0.9647×255 = 246.0
— exactly BmAK's bytes, so the RGB port is lossless. Every other value is either a unit conversion
(÷100 for cm→m) or a stated guess.

## 4. What this means for the build

1. **Two entries per headlight socket**, not one: 60 m / 70° / falloff_start 0.8, and 18 m / 70° /
   falloff_start 0.0, both on `|sportsmuscle_LOD1|body|Batmobile_Chassis|Batmobile_Chassis_LIG`,
   colour 0.5412/0.7725/0.9647.
2. **The inner cone cannot go in the module**; it needs the `.epe` `SVehicleLight` `spot_inner_angle`
   20. Because `LIGHT_SYSTEM.md` §2 records that *which* side the renderer reads is UNKNOWN, the safe
   play is to set both and check in game.
3. **Expect the beam to read dim.** Brightness 0.15 with no flare carrier means the JC3 lamp will look
   weaker than BmAK's, whose punch is the flare. Raising `multiplier` is the knob, and that number is
   a **G**.
4. **Battle mode has a real carrier**: `VEHLT_BattleModeLight` → the same `HeadLight` behaviour with
   red 5.0 / 1024 cm / 10°-35°. Our build already ships a red battle arch light
   (`card-B-07.md:476`), so the red beam is a second entry, not a new system.
5. **Do not add a flicker** unless asked: BmAK has none, and inventing one would be a feature, not a
   port.

## 5. Checks run

| check | result |
|---|---|
| BmAK headlight rows re-read | `Playable_Batmobile_SF` / `MK2` / `Funhouse`: [138,197,246,255], 0.15, 6000 cm, 20°/70°, falloff 1.0; second spot 1800 cm, falloff 2.0 (`LIGHTS.md:235+`) |
| BmAK absence of flicker | no flicker/blinking column in the component table; `MinStrength` documented as unshipped (`LIGHTS.md:178-181`) |
| JC3 member census | `range` 0.5–50, `angle` 10–50, `falloff_start` 0–0.8, `multiplier` 0.3–5, `blinking` 0/1 (`LIGHT_SYSTEM.md` §1) |
| JC3 inner cone | only on `.epe` `SVehicleLight` (0/10/20/30); module has none |
| unit conversions | 6000 cm = 60.0 m; 1800 cm = 18.0 m; 3072 cm = 30.72 m |
| colour derivation | 138/255 = 0.5412, 197/255 = 0.7725, 246/255 = 0.9647; ×255 round-trips exactly |
| temperature attempt | McCamy on [138,197,246] → ≈17,574 K, **outside** valid range 2856–6504 K; white control gives 6,504 K, so the figure is not usable as a Kelvin value |
| headlight deliverables elsewhere | `tmp/freebuff/reports/LIGHTS-sockets.md`, `T-15.md`, `G2-22.md` cover the socket/anchor side; this page adds the beam numbers only |

## 6. Change record (per `AGENTS.md`)

1. **Intended change:** add one report mapping BmAK's headlight beam to JC3 spot-light members, with
   each value flagged measured/derived/guess.
2. **File:** `tmp/freebuff/reports/headlight-beam-plan.md` (this file). Correct file because the brief
   names it and the other light deliverables (`LIGHTS-sockets.md`, `T-15.md`) are separate cards; no
   `Research/` page and no `.epe`/`.vmodc` is written.
3. **Revert:** delete this file. Nothing else changed; no light entry, entity or build was modified.

## 7. UNKNOWNs

| # | UNKNOWN | what settles it |
|---|---|---|
| U-1 | whether `angle` 70 and `range` 60 render correctly outside the shipped value set | one in-game look; both are floats, no vanilla entry ships either |
| U-2 | Brightness 0.15 → JC3 `multiplier` | no conversion is decoded; needs a side-by-side look (start at 1.0) |
| U-3 | BmAK falloff 1.0/2.0 → JC3 `falloff_start` | the two are different quantities (spot exponent vs start fraction); only a look settles it |
| U-4 | which light side the renderer reads (module vs `.epe`) | `LIGHT_SYSTEM.md` §2, Q-1 probe |
| U-5 | whether the two-spot stack is deliberate or one spot is a legacy leftover | both ship in all three Batmobile packages, so treat it as deliberate until footage says otherwise |
| U-6 | what the flare contributes (its `MinStrength` ships nowhere) | not decodable from the install |
