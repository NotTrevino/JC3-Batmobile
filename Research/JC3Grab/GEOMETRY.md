# JC3 render meshes - payload grab (G2-5)

Every mesh block in the 233 vehicle entities, decoded from the `.ee` bundles by
`Tools/scripts/jc3geom.py`. Raw payloads (positions as float32 x3, indices as
uint16/uint32) live in `_JC3grab/geom/*.bin`, one pair per entity; this table is
the derived summary.

| item | value |
|---|---|
| entities | 233 |
| meshes | 56136 |
| mesh blocks | 77611 |
| decoded blocks | 77611 |
| framed (materials + faces, vertices opaque) | 0 |
| failed | 0 |
| vertices (decoded + framed) | 20818841 |
| triangles | 19214751 |
| material slots | 806529 |

## Decoders

| decoder | blocks | oracle |
|---|---|---|
| `CarPaintMM` | 52902 | byte-exact re-encode (`rbm_geom`) |
| `Window` / `CarLight` | 23395 | byte-exact re-encode |
| `GeneralMkIII`, `General`, `GeneralJC3`, `Prop` quantized | 1054 | s16 span x the block's own scale; GeneralMkIII/General checked against the block AABB, GeneralJC3/Prop against the mesh AABB |
| `BavariumShield`, `WaterDisplacementOverride`, `0x90FE086C` float | 260 | 12/28-byte float positions inside the mesh AABB, buffers ending at the checksum |
| framed, no vertex layout | 0 | texture table self-locating; index buffer ends at the block checksum |

`GeneralMkIII` quantization: one scale per axis, axes agree to **0.29%** worst case over 940 blocks; each block's positions are mapped onto its own Attributes AABB.

## Block types

| block | meshes |
|---|---|
| `CarPaintMM` | 52902 |
| `Window` | 12028 |
| `CarLight` | 11367 |
| `GeneralMkIII` | 940 |
| `WaterDisplacementOverride` | 181 |
| `General` | 78 |
| `BavariumShield` | 49 |
| `GeneralJC3` | 35 |
| `0x90FE086C` | 30 |
| `Prop` | 1 |

## Vehicles

| entity | meshes | vertices | triangles |
|---|---|---|---|
| `v4603_plane_urga_cargotransport_military_cargo_tank.ee` | 807 | 359307 | 327394 |
| `v4603_plane_urga_cargotransport_debug.ee` | 582 | 284953 | 259066 |
| `v4603_plane_urga_cargotransport_military_01.ee` | 582 | 284953 | 259066 |
| `v4603_plane_urga_cargotransport_military_cargo_paratrooper.ee` | 582 | 284953 | 259066 |
| `v4603_plane_urga_cargotransport_mm340.ee` | 582 | 284953 | 259066 |
| `v4603_plane_urga_cargotransport_rebel_01.ee` | 582 | 284953 | 259066 |
| `v2601_helicopter_urga_heavyassault_rebel_01.ee` | 269 | 167885 | 151719 |
| `v2601_helicopter_urga_heavyassault_debug.ee` | 261 | 167363 | 151261 |
| `v2601_helicopter_urga_heavyassault_military_01.ee` | 261 | 167363 | 151261 |
| `v0505_car_solar_oldtruck_commercial_cargo_random.ee` | 424 | 164981 | 148238 |
| `v0505_car_solar_oldtruck_commercial_cargo_wine.ee` | 394 | 157380 | 140256 |
| `v0505_car_solar_oldtruck_commercial_cargo_barrel.ee` | 392 | 149511 | 131426 |
| `v0505_car_solar_oldtruck_commercial_01.ee` | 387 | 148542 | 130556 |
| `v0505_car_solar_oldtruck_debug.ee` | 387 | 148542 | 130556 |
| `v0505_car_solar_oldtruck_rebel_01.ee` | 387 | 148542 | 130556 |
| `v0505_car_solar_oldtruck_rebel_emp_01.ee` | 387 | 148542 | 130556 |
| `v0505_car_solar_oldtruck_rebel_emp_custom_mm250.ee` | 387 | 148542 | 130556 |
| `v0505_car_solar_oldtruck_military_01.ee` | 381 | 148282 | 130384 |
| `v2603_helicopter_urga_seascout_debug.ee` | 145 | 141084 | 130158 |
| `v2603_helicopter_urga_seascout_military_01.ee` | 145 | 141084 | 130158 |
| `v2603_helicopter_urga_seascout_rebel_01.ee` | 145 | 140904 | 130158 |
| `v4800_plane_brothers_vintagefighter_debug.ee` | 334 | 136538 | 130911 |
| `v4800_plane_brothers_vintagefighter_rebel_01.ee` | 334 | 136538 | 130911 |
| `v1705_boat_na_mediumoldfishing_civilian_01.ee` | 456 | 131754 | 133146 |
| `v1705_boat_na_mediumoldfishing_debug.ee` | 456 | 131754 | 133146 |
| `v1202_boat_capstone_corvette_debug.ee` | 284 | 131475 | 110739 |
| `v1202_boat_capstone_corvette_military_01.ee` | 284 | 131475 | 110739 |
| `v1202_boat_capstone_corvette_rebel_01.ee` | 278 | 127864 | 107617 |
| `v2602_helicopter_urga_lightassault_debug.ee` | 228 | 124082 | 111201 |
| `v2602_helicopter_urga_lightassault_military_01.ee` | 228 | 124082 | 111201 |
| `v2602_helicopter_urga_lightassault_military_01_custom_mm230.ee` | 228 | 124082 | 111201 |
| `v2602_helicopter_urga_lightassault_rebel_01.ee` | 228 | 124082 | 111201 |
| `v0005_car_autostraad_minetruck_commercial_01.ee` | 229 | 122528 | 110342 |
| `v0005_car_autostraad_minetruck_debug.ee` | 229 | 122528 | 110342 |
| `v4602_plane_urga_fighterbomber_debug.ee` | 326 | 122144 | 110470 |
| `v4602_plane_urga_fighterbomber_military_01.ee` | 326 | 122144 | 110470 |
| `v4602_plane_urga_fighterbomber_rebel_01.ee` | 326 | 122144 | 110470 |
| `v1302_boat_kensington_sailboat_civilian_01.ee` | 136 | 114817 | 120795 |
| `v1302_boat_kensington_sailboat_debug.ee` | 136 | 114817 | 120795 |
| `v2604_helicopter_urga_advancedassault_debug.ee` | 146 | 113805 | 90261 |

Top 40 of 233 entities, most vertices first.
