# Water behaviour: what sinks, what floats, what drowns

G2-31. **The data has one bit for it, plus a module switch, plus one shared timer table - and the Batmobile already behaves the lore way.** A vehicle's `WaterInteraction.will_sink` is `1` on 189 of the 232 vehicle entities and `0` on the other 43; the 43 split cleanly by module: 35 boats carry `BoatBuoyancy`, and 8 land/air vehicles (`v0200` APC, `v2603` sea scout, `v4500` floatplane) keep a plain `Buoyancy` module and simply do not sink. The donor is one of the 189 (`will_sink` 1, buoyancy 2, drag 100, one hull element), so **the current build - which is the donor's own `.ee` with the Batmobile modules inside - sinks and stalls by default**: D-8's lore route needs no water edit, and the float route would need `will_sink` 0 plus a `BoatBuoyancy` block that the donor does not have.

**"Drives underwater" has no member in any of the 52 module types.** The keyword scan of every member path in the fleet (§7) returns only the three water modules, four `vehicle_damage.*_water_entry_ms` timers, five `*_engine_shut_down_delay_s` rows, `number_of_water_collision_sensors`, `fins[].effective_in_water` and the helicopter's flight `dive_*` terms. What a submerged car actually does after the timer runs is native code -> `UNKNOWN` (Q-1 probe).

## 1. The three behaviours, member by member

| behaviour | entities | what the files say makes it so | members and values |
|---|---|---|---|
| **sinks and stalls** | 189 | `WaterInteraction.will_sink = 1`; the hull is a `part_elements[]` triangle mesh the game pushes through the water plane; the kill/stall side is the shared `vehicle_damage` timer block | donor: `will_sink` 1, `buoyancy` 2, `drag` 100, `radius` 0.55, `side_area` 1.85, `bottom_area` 3, `up_velocity_cap` 20, 1 hull element(s) |
| **floats (boat)** | 35 | `WaterInteraction.will_sink = 0` **and** a `BoatBuoyancy` module: `base_buoyancy` plus per-pontoon `buoyancy_modules[]` with `radius`/`forward_drag`/`lateral_drag`/`vertical_drag`/`air_drag` | `base_buoyancy` 0.1..1.45 over the 35 boats, 6..9 pontoon modules each |
| **floats (amphibious)** | 8 | `will_sink = 0` with the ordinary car `Buoyancy` module and no `BoatBuoyancy`: the lift comes from the same `buoyancy` scalar the sinking cars carry | see §5 for all 8 |
| **drives underwater** | 0 | **no member expresses it** - see §7 | `UNKNOWN`, native code |

## 2. The modules, whole

Three module types carry every water member in the fleet: `Buoyancy` on 198 entities, `WaterInteraction` on 233 module instances, `BoatBuoyancy` on 35 boats.

One entity carries a water module twice, and it is a copy-paste worth knowing about:

| entity | type | instances | files |
|---|---|---|---|
| `v4603_plane_urga_cargotransport_military_cargo_tank.ee` | `Buoyancy` | 2 | `v0201_car_capstone_mediumtank_buoyancy.vmodc`<br>`v4603_plane_urga_cargotransport_buoyancy.vmodc` |
| `v4603_plane_urga_cargotransport_military_cargo_tank.ee` | `WaterInteraction` | 2 | `v4603_plane_urga_cargotransport_water_interaction.vmodc`<br>`v0201_car_capstone_mediumtank_water_interaction.vmodc` |

The cargo plane carries the **medium tank's** water module next to its own, which is why the fleet total is one more than the entity count. It changes no verdict: both copies say `will_sink` 1.

### `Buoyancy` (8 member paths)

| member | type | on n modules | fleet range | donor |
|---|---|---|---|---|
| `buoyancy` | float | 198 | 0 .. 2 (4 distinct) | 2 |
| `drag` | float | 198 | 100 .. 100 | 100 |
| `radius` | float | 198 | 0.55 .. 0.55 | 0.55 |
| `side_area` | float | 198 | 1.85 .. 1.85 | 1.85 |
| `bottom_area` | float | 198 | 3 .. 3 | 3 |
| `up_velocity_cap` | float | 198 | 20 .. 20 | 20 |
| `buoyancy_modules` | A[BuoyancyModule] | 198 | - | - |
| `buoyancy_modules[].position[]` | float | 594 | array | - |

### `WaterInteraction` (52 member paths)

| member | type | on n modules | fleet range | donor |
|---|---|---|---|---|
| `part_elements` | A[PartWaterInteractionElement] | 233 | - | - |
| `will_sink` | int32 | 233 | 0 .. 1 (2 distinct) | 1 |
| `angular_drag_pitch` | float | 233 | 0.05 .. 0.05 | 0.05 |
| `angular_drag_yaw` | float | 233 | 0.05 .. 0.15 (2 distinct) | 0.05 |
| `angular_drag_roll` | float | 233 | 0.05 .. 0.2 (4 distinct) | 0.05 |
| `angular_drag_roll_at_speed` | float | 233 | 0.05 .. 0.85 (4 distinct) | 0.05 |
| `angular_drag_ref_speed_kmph` | float | 233 | 50 .. 150 (3 distinct) | 50 |
| `drag_falloff_power` | float | 233 | 0.4 .. 1 (4 distinct) | 1 |
| `pressure_drag` | float | 233 | 100 .. 5000 (4 distinct) | 5000 |
| `pressure_drag_2` | float | 233 | 10000 .. 30000 (4 distinct) | 20000 |
| `suction_drag` | float | 233 | 100 .. 5000 (4 distinct) | 5000 |
| `suction_drag_2` | float | 233 | 2000 .. 30000 (5 distinct) | 20000 |
| `depth_full_drag` | float | 233 | 0 .. 0.2 (4 distinct) | 0.1 |
| `add_skin_friction_laminar` | float | 233 | -0.8 .. 0 (4 distinct) | -0.8 |
| `add_skin_friction_turbulent` | float | 233 | 1 .. 5 (5 distinct) | 3 |
| `reference_drag_speed_ms` | float | 233 | 20 .. 20 | 20 |
| `anti_penetration_max_accel` | float | 233 | 15 .. 30 (2 distinct) | 15 |
| `anti_penetration_multiplier` | float | 233 | 1 .. 3 (4 distinct) | 2 |
| `anti_penetration_power` | float | 233 | 1 .. 3 (3 distinct) | 1 |
| `depth_full_anti_penetration` | float | 233 | 0 .. 0.1 (3 distinct) | 0.1 |
| `planing_vs_forward_speed_ms.x_min` | float | 233 | 0 .. 0 | 0 |
| `planing_vs_forward_speed_ms.x_max` | float | 233 | 20 .. 20 | 20 |
| `planing_vs_forward_speed_ms.y_min` | float | 233 | 0 .. 0 | 0 |
| `planing_vs_forward_speed_ms.y_max` | float | 233 | 0 .. 0.1 (2 distinct) | 0.1 |
| `planing_vs_forward_speed_ms.number_of_control_points` | int8 | 233 | 2 .. 5 (2 distinct) | 5 |
| `planing_vs_forward_speed_ms.control_points[].x` | float | 1165 | -9.89578e-32 .. 2.35051e+34 (34 distinct) | - |
| `planing_vs_forward_speed_ms.control_points[].y` | float | 1165 | -3.88027e-34 .. 2.35051e+34 (34 distinct) | - |
| `planing_vs_forward_speed_ms.control_points[].y2` | float | 1165 | -7.04484 .. 2.35051e+34 (41 distinct) | - |
| `buoyancy_factor_vs_speed_ms.x_min` | float | 233 | 0 .. 0 | 0 |
| `buoyancy_factor_vs_speed_ms.x_max` | float | 233 | 1 .. 40 (4 distinct) | 20 |
| `buoyancy_factor_vs_speed_ms.y_min` | float | 233 | 0 .. 0 | 0 |
| `buoyancy_factor_vs_speed_ms.y_max` | float | 233 | 1 .. 1 | 1 |
| `buoyancy_factor_vs_speed_ms.number_of_control_points` | int8 | 233 | 2 .. 5 (3 distinct) | 2 |
| `buoyancy_factor_vs_speed_ms.control_points[].x` | float | 1165 | -3.86542e-34 .. 7.84867 (22 distinct) | - |
| `buoyancy_factor_vs_speed_ms.control_points[].y` | float | 1165 | -3.86332e-34 .. 7.84867 (27 distinct) | - |
| `buoyancy_factor_vs_speed_ms.control_points[].y2` | float | 1165 | -7.9548 .. 7.84867 (24 distinct) | - |
| `flat_water_vs_speed_ms.x_min` | float | 233 | 0 .. 0 | 0 |
| `flat_water_vs_speed_ms.x_max` | float | 233 | 20 .. 30 (2 distinct) | 30 |
| `flat_water_vs_speed_ms.y_min` | float | 233 | 0 .. 0 | 0 |
| `flat_water_vs_speed_ms.y_max` | float | 233 | 1 .. 1 | 1 |
| `flat_water_vs_speed_ms.number_of_control_points` | int8 | 233 | 2 .. 3 (2 distinct) | 3 |
| `flat_water_vs_speed_ms.control_points[].x` | float | 1165 | -3.41917e-43 .. 4.56927e+19 (12 distinct) | - |
| `flat_water_vs_speed_ms.control_points[].y` | float | 1165 | -3.41917e-43 .. 4.56921e+19 (17 distinct) | - |
| `flat_water_vs_speed_ms.control_points[].y2` | float | 1165 | -3.85197e-34 .. 4.56921e+19 (12 distinct) | - |
| `part_elements[].name.string` | string | 223 | - | - |
| `part_elements[].name.hash` | uint32 | 223 | 836339401 .. 2682837062 (2 distinct) | - |
| `part_elements[].from_part.string` | string | 223 | - | - |
| `part_elements[].from_part.hash` | uint32 | 223 | 22903980 .. 4280572320 (74 distinct) | - |
| `part_elements[].hull.vertices` | A[float] | 223 | - | - |
| `part_elements[].hull.triangles` | A[uint8] | 223 | - | - |
| `vertices[]` | float | 47064 | array | - |
| `triangles[]` | uint8 | 65220 | array | - |

### `BoatBuoyancy` (16 member paths)

| member | type | on n modules | fleet range | donor |
|---|---|---|---|---|
| `base_position[]` | float | 105 | array | - |
| `base_radius` | float | 35 | 0.8 .. 1.5 (4 distinct) | - |
| `base_buoyancy` | float | 35 | 0.1 .. 1.45 (3 distinct) | - |
| `base_forward_drag` | float | 35 | 30 .. 500 (4 distinct) | - |
| `base_lateral_drag` | float | 35 | 100 .. 500 (4 distinct) | - |
| `base_vertical_drag` | float | 35 | 100 .. 2000 (5 distinct) | - |
| `base_air_drag` | float | 35 | 0 .. 50 (5 distinct) | - |
| `up_velocity_cap` | float | 35 | 5 .. 100 (4 distinct) | - |
| `buoyancy_modules` | A[BoatBuoyancyModule] | 35 | - | - |
| `buoyancy_modules[].position[]` | float | 882 | array | - |
| `buoyancy_modules[].radius` | float | 294 | 0.5 .. 1.2 (7 distinct) | - |
| `buoyancy_modules[].buoyancy` | float | 294 | 1 .. 1 | - |
| `buoyancy_modules[].forward_drag` | float | 294 | 1 .. 1 | - |
| `buoyancy_modules[].lateral_drag` | float | 294 | 1 .. 1 | - |
| `buoyancy_modules[].vertical_drag` | float | 294 | 1 .. 2 (2 distinct) | - |
| `buoyancy_modules[].air_drag` | float | 294 | 0 .. 1 (2 distinct) | - |

## 3. The fleet, counted

| group | entities | hull elements per entity (`part_elements[]`) |
|---|---|---|
| sinks and stalls | 189 | 0 -> 10, 1 -> 179 |
| floats (amphibious) | 8 | 1 -> 8 |
| floats (boat) | 35 | 1 -> 35 |

Ten of the sinking entities ship an **empty** `part_elements[]` - no hull mesh at all (`v0009_car_autostraad_modernsaloon_civilian_01.ee`, `v0009_car_autostraad_modernsaloon_debug.ee`, `v0009_car_autostraad_modernsaloon_premium_01.ee`, `v0866_car_na_ladbil_civilian_01.ee`, `v0866_car_na_ladbil_debug.ee`, `v3001_bike_autostraad_snowmobile_debug.ee`, `v3600_bike_urga_combatdirt_debug.ee`, `v3600_bike_urga_combatdirt_military_01.ee`, `v3600_bike_urga_combatdirt_rebel_01.ee`, `v9999_car_mugello_dlctestcar_debug.ee`). They still set `will_sink` 1, which is why the hull mesh must be read as the shape the water plane pushes against, not as the sink switch: the switch is the scalar.

`will_sink` is the only scalar that separates the sinking cars from the amphibious eight: both groups carry the same `angular_drag_*` 0.05, `pressure_drag` 5000 / `pressure_drag_2` 20000, `suction_drag` 5000, `depth_full_drag` 0.1 and `reference_drag_speed_ms` 20. The boats differ from both in every drag: `pressure_drag` 100..5000, `depth_full_drag` 0..0.2, and `angular_drag_ref_speed_kmph` 100..150.

## 4. The card's roster

| vehicle | group | will_sink | hull elems | buoyancy | drag | radius / side / bottom | base_buoyancy | pontoons |
|---|---|---|---|---|---|---|---|---|
| donor, civilian (traffic build) | sink | 1 | 1 | 2 | 100 | 0.55 / 1.85 / 3 | - | - |
| donor, `debug` build | sink | 1 | 1 | 2 | 100 | 0.55 / 1.85 / 3 | - | - |
| donor, `signature_preorder` build | sink | 1 | 1 | 2 | 100 | 0.55 / 1.85 / 3 | - | - |
| armoured transport `military_01` | sink | 1 | 1 | 2 | 100 | 0.55 / 1.85 / 3 | - | - |
| armoured transport `rebel_01` | sink | 1 | 1 | 2 | 100 | 0.55 / 1.85 / 3 | - | - |
| medium tank `v0201` | sink | 1 | 1 | 0 | 100 | 0.55 / 1.85 / 3 | - | - |
| Bavarium tank `v0202` | sink | 1 | 1 | 0 | 100 | 0.55 / 1.85 / 3 | - | - |
| small tank `v0603` | sink | 1 | 1 | 2 | 100 | 0.55 / 1.85 / 3 | - | - |
| APC `v0200` (amphibious car) | floating | 0 | 1 | 2 | 100 | 0.55 / 1.85 / 3 | - | - |
| `v1717` duck (amphibious boat) | boat | 0 | 1 | - | - | - / - / - | 1.45 | 9 |
| heavy patrol boat `v1200` | boat | 0 | 1 | - | - | - / - / - | 1 | 9 |
| racing boat `v1401` | boat | 0 | 1 | - | - | - / - / - | 1 | 9 |
| jetski `v1500` | boat | 0 | 1 | - | - | - / - / - | 1 | 6 |
| floatplane `v4500` | floating | 0 | 1 | 1.5 | 100 | 0.55 / 1.85 / 3 | - | - |
| sea scout helicopter `v2603` | floating | 0 | 1 | 0.25 | 100 | 0.55 / 1.85 / 3 | - | - |

The three donor builds, both armoured-transport builds and all three tanks are `will_sink` 1 with the same `Buoyancy` numbers - the tank roster does not get a water exception. The APC is the one land vehicle in the roster that floats without a boat module, and the duck is a full boat (BoatBuoyancy + `BoatEngine` + `Fins` + `BoatSteering`, class `BoatGlobal`).

## 5. The eight floaters that are not boats

| entity | will_sink | buoyancy |
|---|---|---|
| `v0200_car_capstone_apc_debug.ee` | 0 | 2 |
| `v0200_car_capstone_apc_military_01.ee` | 0 | 2 |
| `v0200_car_capstone_apc_rebel_01.ee` | 0 | 2 |
| `v2603_helicopter_urga_seascout_debug.ee` | 0 | 0.25 |
| `v2603_helicopter_urga_seascout_military_01.ee` | 0 | 0.25 |
| `v2603_helicopter_urga_seascout_rebel_01.ee` | 0 | 0.25 |
| `v4500_plane_solar_smallfloatprop_civilian_01.ee` | 0 | 1.5 |
| `v4500_plane_solar_smallfloatprop_debug.ee` | 0 | 1.5 |

`buoyancy` is a multiplier, not a switch (the fleet's sinking cars carry 0, 0.25, 1.5 or 2 as well), so these eight float because `will_sink` is 0, not because their lift differs.

## 6. The boats

| entity | base_buoyancy | pontoon modules |
|---|---|---|
| `v1200_boat_capstone_heavypatrol_debug.ee` | 1 | 9 |
| `v1200_boat_capstone_heavypatrol_military_01.ee` | 1 | 9 |
| `v1200_boat_capstone_heavypatrol_military_01_delivery.ee` | 1 | 9 |
| `v1200_boat_capstone_heavypatrol_rebel_01.ee` | 1 | 9 |
| `v1200_boat_capstone_heavypatrol_rebel_01_mm210.ee` | 1 | 9 |
| `v1202_boat_capstone_corvette_debug.ee` | 1.45 | 9 |
| `v1202_boat_capstone_corvette_military_01.ee` | 1.45 | 9 |
| `v1202_boat_capstone_corvette_rebel_01.ee` | 1.45 | 9 |
| `v1300_boat_kensington_motoryacht_civilian_01.ee` | 1 | 9 |
| `v1300_boat_kensington_motoryacht_debug.ee` | 1 | 9 |
| `v1302_boat_kensington_sailboat_civilian_01.ee` | 1.45 | 9 |
| `v1302_boat_kensington_sailboat_debug.ee` | 1.45 | 9 |
| `v1400_boat_mugello_spyspeedboat_civilian_01.ee` | 1 | 9 |
| `v1400_boat_mugello_spyspeedboat_debug.ee` | 1 | 9 |
| `v1400_boat_mugello_spyspeedboat_premium_01.ee` | 1 | 9 |
| `v1401_boat_mugello_racingboat_civilian_01.ee` | 1 | 9 |
| `v1401_boat_mugello_racingboat_debug.ee` | 1 | 9 |
| `v1401_boat_mugello_racingboat_signature_preorder.ee` | 1 | 9 |
| `v1500_boat_solar_jetski_civilian_01.ee` | 1 | 6 |
| `v1500_boat_solar_jetski_debug.ee` | 1 | 6 |
| `v1500_boat_solar_jetski_signature_01.ee` | 1 | 6 |
| `v1602_boat_urga_transport_debug.ee` | 1 | 9 |
| `v1602_boat_urga_transport_military_01.ee` | 1 | 9 |
| `v1602_boat_urga_transport_military_01_delivery.ee` | 1 | 9 |
| `v1602_boat_urga_transport_rebel_01.ee` | 1 | 9 |
| `v1701_boat_na_smalloldfishing_civilian_01.ee` | 0.1 | 9 |
| `v1701_boat_na_smalloldfishing_debug.ee` | 0.1 | 9 |
| `v1704_boat_na_lightpatrol_civic_police_01.ee` | 1 | 6 |
| `v1704_boat_na_lightpatrol_debug.ee` | 1 | 6 |
| `v1704_boat_na_lightpatrol_military_01.ee` | 1 | 6 |
| `v1704_boat_na_lightpatrol_rebel_01.ee` | 1 | 6 |
| `v1705_boat_na_mediumoldfishing_civilian_01.ee` | 1.45 | 9 |
| `v1705_boat_na_mediumoldfishing_debug.ee` | 1.45 | 9 |
| `v1717_boat_na_duck_civilian_01.ee` | 1.45 | 9 |
| `v1717_boat_na_duck_debug.ee` | 1.45 | 9 |

## 7. Drown and stall: the shared constants

All 232 entities point their `VehicleCommon` module at the same file:

- `editor/entities/jc_vehicles/00_shared/modules/vehicle_common.vmodc` — 232 entities

| member | values (all entities) |
|---|---|
| `all_rotating_part_properties[0].number_of_water_collision_sensors` | `5` x232 |
| `all_rotating_part_properties[10].number_of_water_collision_sensors` | `3` x232 |
| `all_rotating_part_properties[11].number_of_water_collision_sensors` | `3` x232 |
| `all_rotating_part_properties[1].number_of_water_collision_sensors` | `3` x232 |
| `all_rotating_part_properties[2].number_of_water_collision_sensors` | `0` x232 |
| `all_rotating_part_properties[3].number_of_water_collision_sensors` | `0` x232 |
| `all_rotating_part_properties[4].number_of_water_collision_sensors` | `0` x232 |
| `all_rotating_part_properties[5].number_of_water_collision_sensors` | `0` x232 |
| `all_rotating_part_properties[6].number_of_water_collision_sensors` | `3` x232 |
| `all_rotating_part_properties[7].number_of_water_collision_sensors` | `3` x232 |
| `all_rotating_part_properties[8].number_of_water_collision_sensors` | `3` x232 |
| `all_rotating_part_properties[9].number_of_water_collision_sensors` | `0` x232 |
| `boat_common.engine_shut_down_delay_s` | `5` x232 |
| `car_common.engine_shut_down_delay_s` | `30` x232 |
| `helicopter_common.engine_shut_down_delay_s` | `5` x232 |
| `motorbike_common.engine_shut_down_delay_s` | `5` x232 |
| `plane_common.engine_shut_down_delay_s` | `5` x232 |
| `vehicle_damage.fatal_water_entry_floating_ms` | `50` x232 |
| `vehicle_damage.fatal_water_entry_ms` | `20` x232 |
| `vehicle_damage.min_water_entry_floating_ms` | `20` x232 |
| `vehicle_damage.min_water_entry_ms` | `10` x232 |

So the *kill* side is fleet-wide: `min_water_entry_ms` 10 and `fatal_water_entry_ms` 20, with the `_floating_` pair at 20 / 50, and the engine shut-down delay is 30 s for cars and 5 s for every other class. **No vehicle overrides any of them** - the module is shared, so changing them means a private copy of `vehicle_common.vmodc` (R7), and the unit behind the `_ms` suffix is not decoded here (`UNKNOWN`): 10/20 ms is too short to be a drown timer, so the name is the only evidence of what the numbers mean.

## 8. The live build

`Builds/test-091/v0300_car_kensington_sportsmuscle_civilian_01.ee` (604 inner files) carries the donor's own water modules:

| module | file | rows | will_sink | buoyancy | drag | radius / side / bottom | hull elems |
|---|---|---|---|---|---|---|---|
| `WaterInteraction` | `v0300_car_kensington_sportsmuscle_water_interaction.vmodc` | 734 | 1 | - | - | - / - / - | 1 |
| `Buoyancy` | `v0300_car_kensington_sportsmuscle_buoyancy.vmodc` | 10 | - | 2 | 100 | 0.55 / 1.85 / 3 | - |

Comparison against the donor cache: **identical**. Every compared member matches, so the build sinks exactly like the donor - the lore route of D-8 is already what ships.

## 9. The keyword scan (what is *not* there)

38 distinct member paths fleet-wide mention water/drown/sink/float/dive/submerge/buoyancy. Grouped by the module they live in:

| module | paths | examples |
|---|---|---|
| `WaterInteraction` | 17 | `buoyancy_factor_vs_speed_ms.control_points[].x`, `buoyancy_factor_vs_speed_ms.control_points[].y`, `buoyancy_factor_vs_speed_ms.control_points[].y2`, `buoyancy_factor_vs_speed_ms.number_of_control_points` |
| `BoatBuoyancy` | 9 | `base_buoyancy`, `buoyancy_modules`, `buoyancy_modules[].air_drag`, `buoyancy_modules[].buoyancy` |
| `HelicopterModel` | 5 | `add_dive_pitch_deg`, `dive_speed_low_speed_kmph`, `max_speed_dive_kmph`, `min_speed_dive_kmph` |
| `VehicleCommon` | 5 | `all_rotating_part_properties[].number_of_water_collision_sensors`, `vehicle_damage.fatal_water_entry_floating_ms`, `vehicle_damage.fatal_water_entry_ms`, `vehicle_damage.min_water_entry_floating_ms` |
| `Buoyancy` | 3 | `buoyancy`, `buoyancy_modules`, `buoyancy_modules[].position[]` |
| `Fins` | 1 | `fins[].effective_in_water` |

There is no `drown`, `submerge`, `flood`, `swim` or `underwater` path anywhere in the 232 entities, and no member that could make a hull dive and stay drivable: the only `dive_*` terms are `HelicopterModel` flight (`max_speed_dive_kmph`, `add_dive_pitch_deg`). A submerged vehicle is therefore whatever the engine does with `will_sink` plus the `vehicle_damage` timers -> `UNKNOWN`.

## 10. What this means for the build (WLD-6, D-8)

| question | answer |
|---|---|
| does the build sink like a car today? | **yes** - the build's `will_sink` is 1, inherited from the donor (§8) |
| does it need any water edit for the lore route? | **no** - the donor's values are already the non-amphibious car behaviour; touching them would be the change |
| could it float instead? | only by `will_sink` 0, and for a boat-like ride a `BoatBuoyancy` block the donor does not have - that is the amphibious route D-8 rejected |
| can it drown its own engine at depth? | the only death-on-water member in the fleet is `vehicle_damage.fatal_water_entry_ms` = 20 (with `_floating_` 50); the build shares it and no vehicle overrides it (§7). What the number measures is `UNKNOWN` - do not quote it as seconds or as damage |
| anything to change for R3 (physics follows the asset)? | no: the hull mesh in `WaterInteraction.part_elements[]` is built from the donor body part `sportsmuscle_body` and is a water-plane collider, not a physics station |

## 11. Checks

| check | result |
|---|---|
| `python Tools/scripts/jc3water.py --check` | rebuilds both files and asserts every number above |
| entities | 232 |
| groups | sink 189 / floating 8 / boat 35 |
| module types with water members | 3 |
| shared-constant rows | 21 |
| build identical to donor | True |

Every number here is regenerated by the script from the decoded cache and the build's own `.ee`; none is typed by hand.
