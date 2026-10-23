# Compound instance records: hull -> part wiring (G2-8)

Each `hknpStaticCompoundShape` / `hknpDynamicCompoundShape` holds an `hkArray` of
128-byte `hknpShapeInstance` records: a 3x3 basis at +0x00/+0x10/+0x20 with a per-row
norm marker in the w lane, a translation at +0x30, a scale at +0x40 and the child shape
pointer at +0x50. Reading that array is what turns a vehicle's collision from "18,865
hulls somewhere in the file" into "this hull is part 12".

| item | value |
|---|---|
| entities | 233 |
| physics files | 234 |
| compounds | 6,382 |
| instances | 35,499 |
| instances carrying a part index | 25,769 (72.6%) |
| resolved to a part name (`PARTS_TABLE.jsonl`) | 25,769 (72.6%) |

## Child shape classes

| class | instances |
|---|---|
| `hknpConvexPolytopeShape` | 24,071 |
| `hknpExternMeshShape` | 4,791 |
| `hknpStaticCompoundShape` | 3,297 |
| `hknpDynamicCompoundShape` | 3,226 |
| `hknpCompressedMeshShape` | 58 |
| `hknpConvexShape` | 53 |
| `hknpTriangleShape` | 3 |

## Per entity (most instances first)

| entity | instances |
|---|---|
| `v4603_plane_urga_cargotransport_military_cargo_tank.ee` | 540 |
| `v4603_plane_urga_cargotransport_debug.ee` | 424 |
| `v4603_plane_urga_cargotransport_military_01.ee` | 424 |
| `v4603_plane_urga_cargotransport_military_cargo_paratrooper.ee` | 424 |
| `v4603_plane_urga_cargotransport_mm340.ee` | 424 |
| `v4603_plane_urga_cargotransport_rebel_01.ee` | 424 |
| `v1705_boat_na_mediumoldfishing_civilian_01.ee` | 332 |
| `v1705_boat_na_mediumoldfishing_debug.ee` | 332 |
| `v2201_helicopter_capstone_heavytroop_debug.ee` | 280 |
| `v2201_helicopter_capstone_heavytroop_military_01.ee` | 280 |
| `v2201_helicopter_capstone_heavytroop_rebel_01.ee` | 280 |
| `v4202_plane_capstone_fighterjet_debug.ee` | 276 |
| `v4202_plane_capstone_fighterjet_military_01.ee` | 276 |
| `v4202_plane_capstone_fighterjet_rebel_01.ee` | 276 |
| `v0006_car_autostraad_modernbus_commercial_01.ee` | 263 |
| `v0006_car_autostraad_modernbus_debug.ee` | 263 |
| `v0505_car_solar_oldtruck_commercial_01.ee` | 257 |
| `v0505_car_solar_oldtruck_commercial_cargo_barrel.ee` | 257 |
| `v0505_car_solar_oldtruck_commercial_cargo_random.ee` | 257 |
| `v0505_car_solar_oldtruck_commercial_cargo_wine.ee` | 257 |
| `v0505_car_solar_oldtruck_debug.ee` | 257 |
| `v0505_car_solar_oldtruck_military_01.ee` | 257 |
| `v0505_car_solar_oldtruck_rebel_01.ee` | 257 |
| `v0505_car_solar_oldtruck_rebel_emp_01.ee` | 257 |
| `v0505_car_solar_oldtruck_rebel_emp_custom_mm250.ee` | 257 |
| `v1200_boat_capstone_heavypatrol_debug.ee` | 255 |
| `v1200_boat_capstone_heavypatrol_military_01.ee` | 255 |
| `v1200_boat_capstone_heavypatrol_military_01_delivery.ee` | 255 |
| `v1200_boat_capstone_heavypatrol_rebel_01.ee` | 255 |
| `v1200_boat_capstone_heavypatrol_rebel_01_mm210.ee` | 255 |

Top 30 of 233 entities.
