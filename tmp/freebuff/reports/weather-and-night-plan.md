# Night and rain: what BmAK changes, and which JC3 hook can carry it

Card: rain and darkness. Sources read for this report: `Research/BatmobileGrab/LIGHTS.md` +
`LIGHTS.json` (light rig, G1-17), `Research/BatmobileGrab/COLOUR.md` (G3-04 body chain),
`COLOUR_FUNCTIONS.md` (function list), `CLASS_DEFAULTS.md` (car-level lamp colour),
`Research/JC3Grab/LIGHT_SYSTEM.md` (the 3,217-row light module), `DRIVE_CARRIERS.md`
(grip/friction members), `COLOUR.md` (name census of the VFS index),
`Research/JC3Grab/TRAFFIC.json` (scan coverage). Nothing was re-derived from a binary; every
number below is quoted from those files, and every label says which of the three it is.

## 0. The answer in four lines

1. **At night BmAK changes nothing in the data.** There is no day/night member anywhere in the
   light rig: the lamp set is indexed by vehicle *type* (`VEHLT_HeadLight`,
   `VEHLT_BattleModeLight`, `VEHLT_ForensicsLight`, `VEHLT_BootLight`), never by time. What a
   night build can copy is the *geometry of the beam* (radius 6000 / outer cone 70° /
   intensity 0.15 on the MK2 and Funhouse rigs) and the two class-default colour vectors
   (`HeadLightsColourPursuit` white, `HeadLightsColourBattle` [25,0,0,1]).
2. **In rain BmAK changes the material, not the car.** `Wetness_Refl_Fresnel` 0.6,
   `Rain_Size_Multiplier` [2.5, 2, 0, 1], `Batman_Rain_Direction` [0,0,-1,0] on the WheelArchs
   MIC, plus a `rain_effect_V2_Batmobile` function and a *separate NoRain master variant*
   (`Batmobile_V3_Body_NoRain_MAT`). The values are decoded; what they do to the pixel is
   UNKNOWN (the function links are stripped — `COLOUR_FUNCTIONS.md` §"links stripped: every
   slot is 0").
3. **BmAK does not change grip in rain.** A scan of `PHYSICS.md` and `DRIVE_MODES.md` for
   `wet|grip|rain` returns **0 rows**. There is no BmAK wet-grip value to carry, so any rain
   handling on our side would be a JC3 value with no donor number behind it.
4. **JC3 has no decoded weather hook that reaches a vehicle.** The only weather data in the
   index is 7 `environment/weather/*.environc` modules, and `TRAFFIC.json` records
   `.environc` under `scan/not_scanned` — **9 files, 139,380 B, 0 read**. The only time-of-day
   data is `graphs/mission/modules/msub_time_of_day.gdc/.gsc` (2 files, compiled script, no
   reader in `Tools/scripts`). Everything a vehicle can actually receive today is a **static
   authored value**: light rows, material block values, friction tune members.

So the honest deliverable is not "rain mode". It is: **the night look is buildable from lamp
geometry; the rain look is not buildable as a state, only as a baked static appearance; the
weather→vehicle link is an unread file, not an absent feature.**

## 1. BmAK at night — the lamp values, decoded

`Research/BatmobileGrab/LIGHTS.md` §"Component light values (G1-17)". BmAK lengths are
centimetres (project statement: `LIGHT_SYSTEM.md` §7b calls the socket locations "BmAK cm"),
so the radius column below is also the reach in metres / 100 — that division is **derived**.

| rig | socket | class | radius | inner / outer cone | intensity | colour | shadows |
|---|---|---|---|---|---|---|---|
| MK2 + Funhouse | `HeadLight1` | SpotLight | **6000** | 20 / **70** | **0.15** | [138,197,246] | off |
| MK2 + Funhouse | `HeadLight1` (2nd comp) | SpotLight | 1800 | 20 / 70 | 0.15 | [138,197,246] | off |
| MK2 + Funhouse | `HeadLight2` | SpotLight | 0.1 | 10 / 35 | 0.0 | [160,180,255] | off |
| Joker | `HeadLight1/2` | SpotLight | 3072 | 10 / 35 | **4.0** | [160,180,255] | off |
| all rigs | `HeadLight1/2` battle | SpotLight | 1024 | 10 / 35 | **5.0** | **[255,0,0]** | dynamic **on** |
| all rigs | `HeadLight1/2` forensics | SpotLight | 1024 | 10 / 35 | 5.0 | [255,0,0] | dynamic on |
| all rigs | `LWheelLight` battle | SpotLight | 2048 | 5 / 15 | 0.0 | [255,0,0] | dynamic on |
| Funhouse / MK2 | `Dashboard_Light` | SpotLight | 80 | 20 / 45 | 5.0 | [172,245,255] | dynamic on |
| Joker | `Dashboard` | PointLight | 80 | — | 0.2 | [173,119,240] | dynamic on |
| all rigs | `BrakeLightL/R` | PointLight | 150 | — | 1.0 | [255,38,0] | off |
| Funhouse / MK2 | `BootLight` | SpotLight | 400 | 50 / 60 | 5.0 | [152,255,225] | dynamic on |

Three things this table settles, and one it refuses to:

* **The beam is long and dim, not short and bright.** 6000 units at intensity 0.15 for the MK2
  and Funhouse, against the Joker rig's 3072 at 4.0. The two rigs are opposite trade-offs, so a
  single "night reach" number does not exist — the donor has two and they disagree by 26×
  in intensity.
* **The two spots per headlight are a pair, not a duplicate** (6000 with falloff 1.0 and 1800
  with falloff 2.0). A build that writes one row per lamp loses the near-field.
* **Battle and forensics are the same numbers with a red colour** (1024 / 10 / 35 / 5.0), and
  they are dynamic-shadow casters while the pursuit headlights are not. That is why
  `T-MD12` maps them onto `HeadLight` rows rather than a mode.
* **The lamp colour does not come from the component.** `CLASS_DEFAULTS.md:263-264` carries the
  car-level vectors: `HeadLightsColourPursuit` = 4 floats [1,1,1,1] (white) and
  `HeadLightsColourBattle` = [25,0,0,1]. The per-component `LightColor` 138,197,246 is a
  different member on a different object (already noted in `LEDGER_G3C.md` T-L8/T-L9). Which
  one the renderer multiplies is **UNKNOWN**; the build copies the component colour because
  `T-L8/T-L9` already do, and that choice is not proven to be the visible one.

## 2. BmAK in rain — the material values, decoded

`Research/BatmobileGrab/COLOUR.md` §2 (export #767, `Batmobile_V3_WheelArchs_NEW_MIC`) and
`COLOUR_FUNCTIONS.md`.

| BmAK parameter | value | where | class | what it would mean |
|---|---|---|---|---|
| `Wetness_Refl_Fresnel` | **0.6** | WheelArchs MIC, tag 328 | decoded | a Fresnel weight on the reflection term; the effect is UNKNOWN |
| `Rain_Size_Multiplier` | **[2.5, 2, 0, 1]** | WheelArchs MIC, tag 360 | decoded | two non-zero components and a 0 → likely two rain layers; UNKNOWN which |
| `Batman_Rain_Direction` | **[0, 0, -1, 0]** | WheelArchs MIC, tag 360 | decoded | a downward direction vector; the consumer is UNKNOWN |
| `rain_effect_V2_Batmobile` | 181 B expression array | `COLOUR_FUNCTIONS.md:32` | decoded ref | the wetness material function; **links stripped, every slot 0** |
| `BMBL_Rain_Opt` | 198 B expression array | `COLOUR_FUNCTIONS.md:31` | decoded ref | the rain optimisation branch; body not readable |
| `Batmobile_V3_Body_NoRain_MAT` | 57 chains | `COLOUR_FUNCTIONS.md:57` | decoded | a master variant **without** rain — BmAK ships both looks as separate materials |
| `Batmobile_Worn_NoRain` | 13 chains | `COLOUR_FUNCTIONS.md:64` | decoded | the worn variant of the same |
| `RAIN_TemporalSplashPatternName` | `PostProcess.Rain_TemporalSplashPattern` | `COLOUR.md` §5 wetness | decoded (ini) | a **post-process** splash pattern, not a vehicle member |

The important structural fact: **BmAK does the rain in two places, and neither is the car.**
The wetness is a term inside the body material function, and the dry look is a *different
master material*, selected outside the material (the MIC chain is what the vehicle points at).
So "BmAK in rain" = a wetness term plus a swap of the material asset — not a parameter a
vehicle tune can carry. `COLOUR_FUNCTIONS.md:129` names the gap exactly: *"which parameter
feeds which socket (edge mask vs dirt vs wetness): the parameter layer survives but the links
that place it do not"*.

## 3. Grip — the donor has nothing

| check | result |
|---|---|
| `grep -i "wet\|grip\|rain" Research/BatmobileGrab/PHYSICS.md` | **0 rows** |
| `grep -i "wet\|rain" Research/BatmobileGrab/DRIVE_MODES.md` | **0 rows** |
| does the BmAK physics grab expose any tyre-friction member at all? | **UNKNOWN** — no member matched `grip`, and the grab's field census is the file that would say whether one exists under another name |

So the third leg of the card's question has no donor value. A rain grip change here would be
invented numbers, which is the failure mode this project has already refused elsewhere. The
JC3 side does have the members (§4, F1–F5), but nothing in BmAK says what to put in them.

## 4. JC3 hooks that reach a vehicle — one row each, with what it can carry

"Reaches a vehicle" means: a value on the vehicle entity or its modules that the game reads for
that car. Ordered from most proven to least.

| # | hook | file / member | status | carries which BmAK change |
|---|---|---|---|---|
| L1 | vehicle light module row | `lights[]` — 25 members incl. `range`, `angle`, `multiplier`, `near_cap`, `falloff_start`, `diffuse.R/G/B`, `light_type`, `blinking`, `volumetric_mode`, `volume_intensity`; 3,217 rows across the fleet | decoded (`LIGHT_SYSTEM.md` §1) | **headlight reach** → `range`; **outer cone 70°** → `angle`; **colour** → `diffuse`; the near/far pair → two rows |
| L2 | `.epe` `SVehicleLight` object | `enabled`, `radius`, `spot_angle`, `spot_inner_angle`, `multiplier`, `volume_intensity`; 3,972 objects | decoded; **which list the renderer reads is UNKNOWN** (`LIGHT_SYSTEM.md` §8) | the same values, if the graph side is the one that renders |
| L3 | `CarLight` block in the part's `lod1.rbm` | emissive block, 6 material slots | decoded as a block; parameters **UNKNOWN** (`LIGHT_SYSTEM.md` §8, MODLOG §102d) | the **lamp's glow surface** (not its beam) — copy only |
| L4 | `headlight_flare_01.effc` at the socket | 8,079 B, FULL decode (`DECODE_DEPTH.md:206`) | decoded | the donor's `LensFlareComponent` entries (55 of them) — JC3 has no flare member, so this is the carrier |
| L5 | paint/materials block | dynamic float4s, `SpecularGloss` / `Metallic` / `ClearCoat`; `Material2_Reflectivity` 0.9 / `_Roughness` 0.15 / `_Metalicity` 1.0 in the donor | decoded values (`COLOUR.md`); write path per `paint-gaps-closest-system-plan.md` | **a static "wet look"**: raise reflectivity / lower roughness once, baked |
| F1 | `front_wheels.arcade_friction_multiplier` | `LandGlobal`, float, donor 1 (fleet 0.8–4.4, n=145) | decoded (`DRIVE_CARRIERS.md` §9, offset 36) | a **static** grip value — no BmAK donor number for it |
| F2 | `rear_wheels.arcade_friction_multiplier` | same, offset 68, donor 1 (fleet 1–6) | decoded | a static per-axle balance |
| F3 | `wheels_friction_type` | `LandGlobal`, int32, offset 24, donor 0 | decoded | **UNKNOWN semantics** — a type id, not a scale |
| F4 | `front/rear_wheels.arcade_drag_multiplier` | offsets 36 / 68, donor 0.1 | decoded | rolling drag; a rain build would need a donor number first |
| F5 | `arcade.nitro_boost.grip_multiplier` | `CustomLandGlobal`, donor 2 (1.2–2, n=145) | decoded (`DRIVE_CARRIERS.md` §6.2) | grip **while boosting** — not a weather hook |
| W1 | `environment/weather/rain.environc` + `fog`, `thunderstorm`, `la_crima1`, `bav_heist`, `bav_heist_waves`, `skyfortress_clouds` | 7 modules, 1,188–17,140 B each | **NOT SCANNED** — `TRAFFIC.json` → `scan/not_scanned/.environc`: 9 files, 139,380 B | **the only candidate for a real rain state.** Whether it can touch a vehicle's material or lights is UNKNOWN |
| W2 | `graphs/mission/modules/msub_time_of_day.gdc` + `.gsc` | 2 files (`COLOUR.md` §5 census) | compiled script; **no reader in `Tools/scripts`** | the only time-of-day hook. Whether it can drive a lamp or a material is UNKNOWN |
| W3 | `PostProcess.Rain_TemporalSplashPattern` | ini key (`BmEngine.ini:206` in BmAK; JC3 equivalent unknown) | JC3 side: **0 files** named post_process/tonemap/exposure (`COLOUR.md` §5) | the screen-space splash. Not on the car, and not in JC3's data |

## 5. The mapping, answered per BmAK change

| BmAK change at night / in rain | JC3 hook | what the hook actually carries | label |
|---|---|---|---|
| headlight reach 6000 (MK2/Funhouse), 3072 (Joker) | L1 `range` | the fleet's `range` values are 0.5 / 1 / 2 / 2.5 / 3 / 10 / 30 / **50** max, and **no file states the unit** (`LIGHT_SYSTEM.md` §8). 6000 cm = 60 m is derived; 60 m > every shipped value. So the donor reach **exceeds the fleet's authored range** and the mapping needs a unit probe, not a division | derived + UNKNOWN (unit) |
| outer cone 70°, inner 20° | L1 `angle` | fleet `angle` values: 10 / 25 / 30 / 35 / 40 / 45 / **50** max. 70 is above every shipped angle, so a 70° write is an untested out-of-range value | decoded value, derived fit, **clamp risk** |
| beam colour [138,197,246], red battle [255,0,0] | L1 `diffuse` | already carried: `T-L8/T-L9` write `LightColor/255`; `T-L17…T-L20` write the battle reds onto `HeadLight` rows | decoded, already applied |
| near/far spot pair (6000 @ falloff 1.0, 1800 @ 2.0) | L1 (two rows) + L4 flare | JC3 rows carry `falloff_start` per entry, so the pair is representable | decoded |
| dashboard 80 / boot 400 / brake 150 | L1 rows | `T-L24` (dashboard), `T-L35` (boot), `T-L15/T-L16` (brakes) | decoded, already applied |
| **wet shine** `Wetness_Refl_Fresnel` 0.6 | L5 paint block, **statically** | only a fixed reflectivity/roughness change. There is no wetness member on a vehicle, and no weather input to a material block in any decoded file | decoded value → **static approximation only**; the live wetness is UNKNOWN |
| `Rain_Size_Multiplier` [2.5,2,0,1], `Batman_Rain_Direction` | **none** | they feed a material function whose links are stripped; no JC3 member and no readable consumer | **no carrier** |
| the `NoRain` master material swap | **none decoded** | JC3 material variants are per-entity assets; nothing decoded switches an entity's `.rbm`/paint block at runtime | **no carrier**; would need W1 or a script |
| **grip in rain** | F1–F4 | static tune values only, and BmAK supplies **no** number for them (§3) | **no donor value** |
| wet-screen splash | W3 | JC3 ships 0 post-process/tonemap assets (`COLOUR.md` §5) | **no carrier** |

## 6. What is UNKNOWN, and the file that would settle it

| # | UNKNOWN | settler |
|---|---|---|
| U1 | whether `.environc` can set a **vehicle's** wetness or lights at all | a decoder/reader for `environment/weather/rain.environc` (17,140 B, `patch_win64/game1` @ 453519360) — currently `not_scanned`; first output must be its member list, not a guess |
| U2 | whether `msub_time_of_day.gdc` drives any vehicle-side value | a `.gdc` bytecode read (none exists in `Tools/scripts`) + the module's export list |
| U3 | the unit of JC3 `range` / `angle` (m vs cm, deg vs half-deg) | one in-game A/B: two otherwise identical rows at range 2 and 20, screenshot the reach (`LIGHT_SYSTEM.md` §8 already names this probe) |
| U4 | which light list the renderer reads (module rows vs `.epe` objects) | the same probe: change only the module row, look |
| U5 | whether the visible headlight colour is the component `LightColor` or the class default `HeadLightsColourPursuit` | one build with the two made deliberately different |
| U6 | what `Wetness_Refl_Fresnel` 0.6 does to the body pixel | a decode of `rain_effect_V2_Batmobile` (its links are the gap) or a BmAK-free A/B in JC3 (not available) |
| U7 | whether BmAK models tyre grip at all | `PHYSICS.json` field census for a friction/grip member under another name |
| U8 | whether JC3 vehicle lights switch on automatically at night | U2, or a night observation with the light rows set to `blinking` 0 and one row set to a tiny range |

## 7. What a night build can do now, and what a rain build cannot

**Buildable today (all static, all already in the ledger):**
1. The beam geometry of §1 as light rows — this is a *look*, not a state: lamps are on or off
   with the vehicle, at every hour.
2. The two-spot pair per headlight, with the near field restored (`LIGHT_SYSTEM.md` §7 recipe,
   `T-L8`/`T-L9`).
3. The red battle lamps as `HeadLight` rows (`T-L17…T-L20`), already carried.
4. A **baked** wet look via L5 (reflectivity up, roughness down) — one value for all weather.

**Not buildable, and should not be written as if it were:**
* rain-reactive shine (needs U1 or U6),
* rain grip (needs a donor value that does not exist and a weather input that is not decoded),
* lamp-on-at-night (needs U2/U8),
* the screen splash (needs W3, absent from JC3's data).

## 8. If this is accepted, the smallest next step

One experiment, not an implementation: read `environment/weather/rain.environc` far enough to
print its member names (U1). If it exposes anything vehicle-facing — a wetness scalar, a light
multiplier, a material parameter — the rain half of this card becomes a real mapping; if it
only holds fog/sun/sky, then the answer is fixed: **JC3's rain cannot reach a car, and the rain
look is a baked material choice.** Either outcome is one file's worth of work, and both close
the question instead of restating it.

## 9. Evidence index

- `Research/BatmobileGrab/LIGHTS.md` — 101 entries, 129 components, per-component radius / cone
  / intensity / colour table (§"Component light values (G1-17)").
- `Research/BatmobileGrab/CLASS_DEFAULTS.md:263-264` — `HeadLightsColourPursuit` [1,1,1,1],
  `HeadLightsColourBattle` [25,0,0,1].
- `Research/BatmobileGrab/COLOUR.md` §2, §5 — `Wetness_Refl_Fresnel` 0.6,
  `Rain_Size_Multiplier` [2.5,2,0,1], `Batman_Rain_Direction` [0,0,-1,0], the wetness ini keys.
- `Research/BatmobileGrab/COLOUR_FUNCTIONS.md` — `rain_effect_V2_Batmobile` (181 B, links
  stripped), `BMBL_Rain_Opt` (198 B), `Batmobile_V3_Body_NoRain_MAT` (57 chains),
  `Batmobile_Worn_NoRain` (13 chains), and :129 the "which parameter feeds which socket" gap.
- `Research/JC3Grab/LIGHT_SYSTEM.md` §1 (25 members, 3,217 rows, value census), §7b/§8 (unit,
  renderer-list and `preset_id` unknowns).
- `Research/JC3Grab/DRIVE_CARRIERS.md` §6.2, §9 (friction/drag offsets and donor values).
- `Research/JC3Grab/COLOUR.md` §5 — the index-wide name census: `light_profile` 0,
  `time_of_day` 2, `weather` 81 (barks), no tonemap/exposure asset.
- `Research/JC3Grab/TRAFFIC.json` — `scan/not_scanned/.environc`: 9 files, 139,380 B.
- `Research/JC3Grab/INDEX.jsonl` — the 7 `environment/weather/*.environc` paths and sizes.
- `tmp/freebuff/reports/paint-gaps-closest-system-plan.md` — the write path for L5.
- `Working/Translation/T14_LIGHTS.md` — which lamp rows already carry which donor values.
