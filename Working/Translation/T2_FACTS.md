# T-2 facts — generated, do not edit

`Tools/scripts/t2_facts.py` · inputs: `current.json`, `Research/BatmobileGrab/*.json`, `Research/JC3Grab/VOCABULARY.md`. Any number in `T2_TRANSLATION.md` that is not here is marked as an assumption there.

## Build 083 — the modules T-2 translates

| module | values | what it holds |
|---|---|---|
| `VehicleDamage` | 246 | health profile + 24 part damage types |
| `VehicleDynamicLights` | 526 | lights |
| `EffectAttachments` | 628 | effect table |
| `Palette` | 181 | paint tints |
| `LandAudio` | 2 | audio |
| `Decals` | 10 | decals |
| `DeformPoints` | 7083 | deform points |
| `VehicleMisc` | 33 | misc |
| `WaterInteraction` | 734 | water interaction |
| `sportsmuscle_vehicle_parts` | **decode failed** | parts (G2-7) — convertadf-failed |

### Damage (build 083)

| member | value |
|---|---|
| `max_health` | 2000 |
| `bullet_armor_strength` | 100 |
| `bullet_heavy_armor_strength` | 20 |
| `explosion_threshold` | 4000 |
| `smoke_threshold` | 1050 |
| `burn_threshold` | 250 |
| `burn_duration_s` | 20 |
| `explosion_delay_s` | 10 |
| `deform_scale` | 0 |

`part_damage_types`: **24** entries

| # | type | initial_health | damaged_health | loosen_health |
|---|---|---|---|---|
| 0 | `Default` | 50 | 30 | 20 |
| 1 | `Land_Generic` | 200 | 0 | 50 |
| 2 | `Land_Body` | 1000 | 0 | 0 |
| 3 | `Land_Wheel` | 1020 | 400 | 100 |
| 4 | `Land_Door` | 300 | 50 | 200 |
| 5 | `Land_Light` | 50 | 30 | 20 |
| 6 | `Land_Window` | 50 | 30 | 20 |
| 7 | `Land_Stunt_Window` | 700 | 0 | 0 |
| 8 | `Land_Engine` | 900 | 100 | 150 |
| 9 | `Land_Axle` | 50 | 30 | 20 |
| 10 | `Land_Spring` | 50 | 30 | 20 |
| 11 | `Land_Seat` | 50 | 30 | 20 |
| 12 | `Land_Wing_Mirror` | 50 | 30 | 20 |
| 13 | `Land_Steering_Wheel` | 50 | 30 | 20 |
| 14 | `Land_Roof_Rack` | 500 | 0 | 50 |
| 15 | `Land_Mud_Flap` | 50 | 30 | 20 |
| 16 | `Land_Bumper` | 200 | 30 | 50 |
| 17 | `Land_Undercarriage` | 800 | 0 | 0 |
| 18 | `Land_Fender` | 200 | 0 | 50 |
| 19 | `Land_Hood` | 350 | 0 | 100 |
| 20 | `Land_Trunk` | 350 | 0 | 100 |
| 21 | `Land_Back_Gate` | 200 | 0 | 50 |
| 22 | `Land_Antenna` | 50 | 30 | 20 |
| 23 | `Land_Grill` | 200 | 0 | 50 |

### Lights (build 083) — **21** entries

| # | behavior | preset_id | range | angle | diffuse R,G,B |
|---|---|---|---|---|---|
| 0 | `TailLight` | 1435191809 | 2 | 10 | 1, 0.247850001, 0.0789999962 |
| 1 | `LeftSignal` | 1358616627 | 2 | 10 | 1, 0.267999977, 0.0849999785 |
| 2 | `HeadLight` | 2763198432 | 2 | 10 | 0.802999973, 0.90806669, 1 |
| 3 | `TailLight` | 3358775008 | 2 | 10 | 1, 0.247850001, 0.0789999962 |
| 4 | `TailLight` | 3048938132 | 2 | 10 | 1, 0.247850001, 0.0789999962 |
| 5 | `LeftSignal` | 891622622 | 2 | 10 | 1, 0.714999974, 0.185000002 |
| 6 | `RightSignal` | 521093305 | 2 | 10 | 1, 0.714999974, 0.185000002 |
| 7 | `TailLight` | 4016595472 | 2 | 10 | 1, 0.247850001, 0.0789999962 |
| 8 | `HeadLight` | 625235815 | 30 | 40 | 0.713, 0.913900018, 1 |
| 9 | `HeadLight` | 4272096469 | 30 | 40 | 0.713, 0.913999975, 1 |
| 10 | `RightSignal` | 1271816577 | 2 | 10 | 1, 0.247850001, 0.0789999962 |
| 11 | `HeadLight` | 4276153710 | 2 | 10 | 1, 1, 1 |
| 12 | `HeadLight` | 1814273923 | 30 | 40 | 0.713, 0.913900018, 1 |
| 13 | `HeadLight` | 1754632929 | 2 | 10 | 1, 1, 1 |
| 14 | `HeadLight` | 3407385576 | 30 | 40 | 0.713, 0.913999975, 1 |
| 15 | `Reverse` | 3815211005 | 2 | 10 | 1, 1, 1 |
| 16 | `Reverse` | 937754529 | 2 | 10 | 1, 1, 1 |
| 17 | `HeadLight` | 2877751723 | 2 | 10 | 1, 1, 1 |
| 18 | `TailLight` | 1700993006 | 2 | 10 | 1, 0.247850001, 0.0789999962 |
| 19 | `HeadLight` | 126093807 | 2 | 10 | 1, 1, 1 |
| 20 | `HeadLight` | 1729670457 | 30 | 40 | 0.713, 0.913999975, 1 |

### Effects (build 083) — **51** effect rows over **29** parts, **1** usage rows

distinct effects (11): `burn_base`, `burn_engine`, `burn_roof`, `dynamic_headlight`, `electric_break`, `large_break`, `medium_break`, `small_break`, `taillight_break`, `window_break`, `window_break_sm`

usages: `HeadLights`

### Palette (build 083) — **10** tints

| # | name | specular_gloss | clear_coat | metallic |
|---|---|---|---|---|
| 0 | `White` | 0.449999988 | 1 | 1 |
| 1 | `Evergreen Pearl` | 0.449999988 | 1 | 1 |
| 2 | `Garnet Red Metallic` | 0.449999988 | 1 | 1 |
| 3 | `Black` | 0.449999988 | 1 | 1 |
| 4 | `Grey` | 0.449999988 | 1 | 1 |
| 5 | `Silver` | 0.449999988 | 1 | 1 |
| 6 | `Blue` | 0.449999988 | 1 | 1 |
| 7 | `Brown` | 0.449999988 | 1 | 1 |
| 8 | `Red` | 0.449999988 | 1 | 1 |
| 9 | `Green` | 0.449999988 | 1 | 1 |

### Misc that T-2 touches

| member | value |
|---|---|
| `official_top_speed` | 336.399994 |
| `max_landing_speed_kmph` | 170 |
| `full_nitro_use_time` | 4 |
| `full_nitro_refill_time` | 2 |

`LandAudio` members: `max_rpm` = 10000, `min_rpm` = 1000

## BmAK — what T-2 has to translate from

### Materials and textures (`SLOTS.json`)

| item | value |
|---|---|
| slots | 19 |
| instances | 13 |
| textures | 38 |
| lod0_faces | 299837 |
| slots_with_geometry | 19 |
| slots_without_geometry | 0 |
| lods | 3 |
| lod_maps_identity | 3 |

### Lights (`LIGHTS.json`)

entries **101** across **4** rigs; orphan sockets **6**; missing bones **0**

| by type | n |
|---|---|
| `VEHLT_HeadLight` | 46 |
| `VEHLT_BattleModeLight` | 16 |
| `(stripped)` | 12 |
| `VEHLT_ForensicsLight` | 12 |
| `VEHLT_TailLight` | 8 |
| `VEHLT_Interior` | 4 |
| `VEHLT_BootLight` | 3 |

| disposition | n |
|---|---|
| mapped | 54 |
| approximated | 23 |
| no-jc3-equivalent | 16 |
| inferred from socket name (type stripped by the cooker) | 8 |

| part the light names | n |
|---|---|
| `sportsmuscle_body` | 77 |
| `sportsmuscle_wheel_f_l` | 14 |
| `sportsmuscle_wheel_f_r` | 10 |

### Collision bodies (`PHYSICS.json`)

| package | bodies | boxes | spheres |
|---|---|---|---|
| Playable_BatmobileFunhouse_SF | 32 | 32 | 0 |
| Playable_BatmobileJoker_SF | 32 | 32 | 0 |
| Playable_BatmobileMK2_SF | 32 | 32 | 0 |
| Playable_Batmobile_SF | 32 | 32 | 0 |

total bodies **128**; largest body box [317.942, 64.552, 97.966] cm (bone `Root` is [30.3, 30.3, 30.3] cm)

### Audio (`AUDIO_MAP.json`)

| item | value |
|---|---|
| banks | 27 |
| bytes | 34409121 |
| rows | 361 |
| unique_event_ids | 118 |
| resolved_rows | 239 |
| resolved_ids | 74 |
| streamed_rows | 24 |
| no_media_rows | 8 |
| missing_rows | 90 |
| missing_ids | 26 |
| media | 447 |
| media_bytes | 18176431 |

missing banks: `Engine.BML_Batmobile_Subjective`, `Engine.BML_Impacts`, `Engine.BML_Sonar`, `Engine.CHR_BatmanAlerts`, `Engine.CHR_BatmanDisruptor`, `Engine.OBJ_Rolling_Objects`, `Engine.UI_InGame`, `Engine.VEH_Tank_Heavy`, `Engine.VEH_Tank_Missiles`, `Engine.VFX_Tank_Explosion`

## JC3 fleet — the shipped range behind each T-2 row

Rows are quoted from `VOCABULARY.md`; the range column keeps its `(n=…)` sample size.

| member | type | fleet range | donor |
|---|---|---|---|
| `VehicleDamage.max_health` | int32 | 500 .. 4000 (med 700, n=233) | 700 |
| `VehicleDamage.bullet_armor_strength` | float | 0 .. 99 (med 0, n=233) | 0 |
| `VehicleDamage.bullet_heavy_armor_strength` | float | 0 .. 50 (med 0, n=233) | 0 |
| `VehicleDamage.explosion_threshold` | int32 | 500 .. 4000 (med 1000, n=233) | 700 |
| `VehicleDamage.smoke_threshold` | uint16 | 200 .. 1050 (med 250, n=233) | 200 |
| `VehicleDamage.burn_threshold` | uint16 | 50 .. 250 (med 100, n=233) | 80 |
| `VehicleDamage.part_damage_types[].initial_health` | int32 | 50 .. 10000 (med 300, n=4820) | 200 |
| `VehicleDamage.part_damage_types[].damaged_health` | int32 | 0 .. 1500 (med 30, n=4820) | 0 |
| `VehicleDamage.part_damage_types[].loosen_health` | int32 | 0 .. 500 (med 50, n=4820) | 50 |
| `VehicleDamage.part_damage_types[].type.string` | string | 24 strings: Default, Land_Antenna, Land_Axle, Land_Back_Gate (+20) | Land_Grill |
| `VehicleDynamicLights.lights[].range` | float | 0.1 .. 50 (med 10, n=3217) | 30 |
| `VehicleDynamicLights.lights[].angle` | float | 10 .. 50 (med 10, n=3217) | 40 |
| `VehicleDynamicLights.lights[].multiplier` | float | 0.3 .. 5 (med 1, n=3217) | 2 |
| `VehicleDynamicLights.lights[].behavior` | string | 6 strings: HeadLight, LeftSignal, None, Reverse (+2) | HeadLight |
| `Palette.tints[].specular_gloss` | float | 0 .. 1 (med 1, n=3602) | 0.449999988 |
| `EffectAttachments.all_effects[].effect.string` | string | 17 strings: burn_base, burn_engine, burn_roof, door_break (+13) | window_break |
| `EffectAttachments.part_effects[].effects_count` | int32 | 1 .. 19 (med 2, n=5280) | 1 |
| `VehicleMisc.official_top_speed` | float | 25 .. 350 (med 150, n=233) | 250 |
| `VehicleParts.parts[].has_world_collision_shape` | int8 | 0 .. 1 (med 1, n=100) | — |
| `VehicleParts.parts[].world_collision_body_id` | int16 | -1 .. 25 (med 13, n=100) | — |
