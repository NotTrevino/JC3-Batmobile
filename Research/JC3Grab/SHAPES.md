# JC3 collision shapes from `.physicsc` (G2-8)

Decoded by `Tools/scripts/jc3hkx.py` - a type-aware Havok 2014 packfile reader.
**233 vehicle entities / 234 `.physicsc` files**, 130513 objects, 18865 convex hulls (18865 verified convex), 302576 hull vertices, 238476 planes, 972642 hull indices, 1806301 collision-mesh vertices, and **6,382 compounds / 35,499 instance records** (25,769 with a part index).

The physics file lives **inside the entity's `.ee` bundle**, as for `jc3phys.py`.
A bundle entry whose `offset` is `0` is a *reference*, not data: the member is
not embedded and its name is the VFS path, so `models/.../x.physicsc` is read
from the archives instead: 33 of the 233 bundles keep their 400-680 KB physics
file that way, and reading offset 0 there returns the bundle header - which is
what made those entities look empty.

## What the file is

Every file starts `57E0E057 10C0C010` with version string `hk_2014.1.0-r1`,
file version 11, layout rules `0x01000108`, three sections:

| section | content | evidence |
|---|---|---|
| `__classnames__` | hash + name records | every entry parses |
| `__types__` | **empty** | `end == data` in every file |
| `__data__` | objects, arrays, fixup tables | virtual fixups type every object |

The type library is stripped - the engine's own reflection knows these classes.
This reader carries the layouts instead, and stays *type-aware*: the **virtual
fixup table** names the class of every object, exactly as the game's loader does.

Packfile mechanics pinned by the files:

* pointers are **8 bytes** (64-bit build), the fixup writes the low half;
* `hkArray` is **16 bytes**: `{T* data; int size; u32 capacityAndFlags}`;
* local fixups are `(from, to)`, global `(from, section, to)`, virtual
  `(offset, 0, class-name offset)`, all data-section relative;
* unused table slots and section tails are `0xFF`, object tails `0x7F`;
* the root variant chain is `hkRootLevelContainer` -> `NPhysicsData` ->
  `hknpPhysicsSceneData` -> `hknpPhysicsSystemData`, names as `hkStringPtr`.

## The shape blob

`hknpConvexPolytopeShape` is not a pointer-filled class: it is one packed block.

```
+0x00  base (16 B)                       hknpShape
+0x10  u32 shape_flags                  0x01000143 on every hull
+0x14  f32 convex_radius
+0x18  u32 shape_tag
+0x20  hkRefCountedProperties*
+0x30  u16 vertex_count, u16 0x20
+0x40  u16 face_count, u16 unused;  u16 ?, u16 ?;  u16 index_count, u16 ?
+0x50  hkVector4 vertices[vertex_count]   w = 0.5 + rank/2^23, rank ascending
       hkVector4 planes[plane_count]      unit normal + distance, n.v + d <= 0
       face table                         4-byte records
       u8 indices[index_count]            every byte < vertex_count
       pad to 16 with 0x7F
```

`vertex_count` is the low u16 at `+0x30`, `plane_count` the low u16 at `+0x44`,
`index_count` the low u16 at `+0x48`; `face_count` is the low u16 at `+0x40`.
The high u16s do not line up with block offsets and are not named. The index
block is located from the tail - the last `index_count` bytes before the `0x7F`
padding - which is what makes the whole layout checkable:

```
0x50 + 16*V + 16*P + face_bytes + I + pad == object extent
```

**Plane convention (measured, not assumed).** The stored distance is not a
standard `n·v - d <= 0` offset: for every hull and every plane,
`max(n·v) + d == 0` at the contact vertex and `<= 0` for all the others.
So the stored normal points **inward** (or, equivalently, the outward plane
is `-n·v - d = 0`). The residual is bounded by the shape's own `convex_radius`,
which is what rounds the hull: the innermost corners sit up to `r` inside the
outermost plane. That single relation pins the vertex base, the plane base and
the p-count together - a layout off by one record cannot satisfy it.

## Invariants (every vehicle, no exceptions)

Measured by `jc3hkx.py check --all`, which exits non-zero on one violation;
the counts below come from the same `shape_checks()` pass, not from a guess.

| check | result |
|---|---|
| `.physicsc` decoded | 234 / 234 |
| classes named by the virtual fixup table | every object, 0 unresolved |
| hull blocks account for the object extent | 18865 / 18865 |
| vertex `w` = `0.5 + rank/2^23`, rank non-decreasing | 18865 / 18865 |
| planes unit length, unused sentinel excluded | 18865 / 18865 |
| every hull index `< vertex_count` | 18865 / 18865 |
| **every plane is a supporting plane** (`abs(max n.v + d) <= r`) | 18865 / 18865 |
| `hkGeometry` arrays fill the object | 9582 / 9582 |
| compound instances resolve to a typed shape | 35,499 / 35,499 |
| compound child AABBs inside the parent AABB | 6,382 / 6,382 compounds |
| parent AABB explained by the children's union | 6,341 / 6,382 (6,338 exact to the convex radius) |
| instances carrying a part index | 25,769 / 35,499 |
| violation(s) | 0 |
| wheel stations vs `land_global` | **17 agree**, 0 disagree, 216 file(s) without a set |

## Vehicles

| entity | hulls | hull verts | planes | mesh verts | hull bbox x×y×z (m) | wheelbase |
|---|---|---|---|---|---|---|
| `v4603_plane_urga_cargotransport/v4603_plane_urga_cargotransport_debug.ee` | 245 | 3416 | 3200 | 2023 | 89.26 × 21.01 × 81.55 |  |
| `v4603_plane_urga_cargotransport/v4603_plane_urga_cargotransport_military_01.ee` | 245 | 3416 | 3200 | 2023 | 89.26 × 21.01 × 81.55 |  |
| `v4603_plane_urga_cargotransport/v4603_plane_urga_cargotransport_military_cargo_paratrooper.ee` | 245 | 3416 | 3200 | 2023 | 89.26 × 21.01 × 81.55 |  |
| `v4603_plane_urga_cargotransport/v4603_plane_urga_cargotransport_military_cargo_tank.ee` | 245 | 3416 | 3200 | 2023 | 89.26 × 21.01 × 81.55 |  |
| `v4603_plane_urga_cargotransport/v4603_plane_urga_cargotransport_mm340.ee` | 245 | 3416 | 3200 | 2023 | 89.26 × 21.01 × 81.55 |  |
| `v4603_plane_urga_cargotransport/v4603_plane_urga_cargotransport_rebel_01.ee` | 245 | 3416 | 3200 | 2023 | 89.26 × 21.01 × 81.55 |  |
| `v1202_boat_capstone_corvette/v1202_boat_capstone_corvette_debug.ee` | 90 | 1068 | 836 | 1013 | 6.91 × 13.47 × 42.29 |  |
| `v1202_boat_capstone_corvette/v1202_boat_capstone_corvette_military_01.ee` | 90 | 1068 | 836 | 1013 | 6.91 × 13.47 × 42.29 |  |
| `v1202_boat_capstone_corvette/v1202_boat_capstone_corvette_rebel_01.ee` | 90 | 1068 | 836 | 1013 | 6.91 × 13.47 × 42.29 |  |
| `v2601_helicopter_urga_heavyassault/v2601_helicopter_urga_heavyassault_debug.ee` | 96 | 1988 | 1836 | 1023 | 24.45 × 21.68 × 31.43 |  |
| `v2601_helicopter_urga_heavyassault/v2601_helicopter_urga_heavyassault_military_01.ee` | 96 | 1988 | 1836 | 1023 | 24.45 × 21.68 × 31.43 |  |
| `v2601_helicopter_urga_heavyassault/v2601_helicopter_urga_heavyassault_rebel_01.ee` | 96 | 1988 | 1836 | 1023 | 24.45 × 21.68 × 31.43 |  |
| `v1705_boat_na_mediumoldfishing/v1705_boat_na_mediumoldfishing_civilian_01.ee` | 162 | 3580 | 2822 | 2159 | 10.15 × 15.71 × 22.74 |  |
| `v1705_boat_na_mediumoldfishing/v1705_boat_na_mediumoldfishing_debug.ee` | 162 | 3580 | 2822 | 2159 | 10.15 × 15.71 × 22.74 |  |
| `v1602_boat_urga_transport/v1602_boat_urga_transport_debug.ee` | 76 | 1144 | 912 | 687 | 8.30 × 8.01 × 22.27 |  |
| `v1602_boat_urga_transport/v1602_boat_urga_transport_military_01.ee` | 76 | 1144 | 912 | 687 | 8.30 × 8.01 × 22.27 |  |
| `v1602_boat_urga_transport/v1602_boat_urga_transport_military_01_delivery.ee` | 76 | 1144 | 912 | 687 | 8.30 × 8.01 × 22.27 |  |
| `v1602_boat_urga_transport/v1602_boat_urga_transport_rebel_01.ee` | 76 | 1144 | 912 | 687 | 8.30 × 8.01 × 22.27 |  |
| `v5603_train_urga_monorailmissilecar/v5603_train_urga_monorailmissilecar_military_01.ee` | 64 | 640 | 483 | 577 | 4.88 × 5.84 × 20.06 |  |
| `v5602_train_urga_monorailflatbed/v5602_train_urga_monorailflatbed_military_catwalk.ee` | 36 | 604 | 489 | 1019 | 4.38 × 4.89 × 20.02 |  |
| `v5602_train_urga_monorailflatbed/v5602_train_urga_monorailflatbed_military_containers.ee` | 36 | 604 | 489 | 1019 | 4.38 × 4.89 × 20.02 |  |
| `v5602_train_urga_monorailflatbed/v5602_train_urga_monorailflatbed_military_containers_rigidobject.ee` | 36 | 604 | 489 | 1019 | 4.38 × 4.89 × 20.02 |  |
| `v5602_train_urga_monorailflatbed/v5602_train_urga_monorailflatbed_military_empty.ee` | 36 | 604 | 489 | 1019 | 4.38 × 4.89 × 20.02 |  |
| `v2604_helicopter_urga_advancedassault/v2604_helicopter_urga_advancedassault_debug.ee` | 53 | 1004 | 967 | 1023 | 12.73 × 15.72 × 19.31 |  |
| `v2604_helicopter_urga_advancedassault/v2604_helicopter_urga_advancedassault_military_01.ee` | 53 | 1004 | 967 | 1023 | 12.73 × 15.72 × 19.31 |  |
| `v2604_helicopter_urga_advancedassault/v2604_helicopter_urga_advancedassault_rebel_01.ee` | 53 | 1004 | 967 | 1023 | 12.73 × 15.72 × 19.31 |  |
| `v2604_helicopter_urga_advancedassault/v2604_helicopter_urga_advancedassault_signature_shielded.ee` | 53 | 1004 | 967 | 1023 | 12.73 × 15.72 × 19.31 |  |
| `v2604_helicopter_urga_advancedassault/v2604_helicopter_urga_advancedassault_signature_shielded_di_ravello.ee` | 53 | 1004 | 967 | 1023 | 12.73 × 15.72 × 19.31 |  |
| `v1200_boat_capstone_heavypatrol/v1200_boat_capstone_heavypatrol_debug.ee` | 158 | 1840 | 1343 | 2909 | 6.12 × 6.75 × 18.34 |  |
| `v1200_boat_capstone_heavypatrol/v1200_boat_capstone_heavypatrol_military_01.ee` | 158 | 1840 | 1343 | 2909 | 6.12 × 6.75 × 18.34 |  |
| `v1200_boat_capstone_heavypatrol/v1200_boat_capstone_heavypatrol_military_01_delivery.ee` | 158 | 1840 | 1343 | 2909 | 6.12 × 6.75 × 18.34 |  |
| `v1200_boat_capstone_heavypatrol/v1200_boat_capstone_heavypatrol_rebel_01.ee` | 158 | 1840 | 1343 | 2909 | 6.12 × 6.75 × 18.34 |  |
| `v1200_boat_capstone_heavypatrol/v1200_boat_capstone_heavypatrol_rebel_01_mm210.ee` | 158 | 1840 | 1343 | 2909 | 6.12 × 6.75 × 18.34 |  |
| `v5601_train_urga_monorailcargoengine/v5601_train_urga_monorailcargoengine_military_01.ee` | 89 | 1472 | 1106 | 1127 | 5.02 × 5.46 × 18.04 |  |
| `v5601_train_urga_monorailcargoengine/v5601_train_urga_monorailcargoengine_military_02.ee` | 89 | 1472 | 1106 | 1127 | 5.02 × 5.46 × 18.04 |  |
| `v5601_train_urga_monorailcargoengine/v5601_train_urga_monorailcargoengine_military_03.ee` | 89 | 1472 | 1106 | 1127 | 5.02 × 5.46 × 18.04 |  |
| `v5601_train_urga_monorailcargoengine/v5601_train_urga_monorailcargoengine_military_04.ee` | 89 | 1472 | 1106 | 1127 | 5.02 × 5.46 × 18.04 |  |
| `v5601_train_urga_monorailcargoengine/v5601_train_urga_monorailcargoengine_military_mission_mm320_boss_train.ee` | 89 | 1472 | 1106 | 1127 | 5.02 × 5.46 × 18.04 |  |
| `v5601_train_urga_monorailcargoengine/v5601_train_urga_monorailcargoengine_military_mission_mm320_train.ee` | 89 | 1472 | 1106 | 1127 | 5.02 × 5.46 × 18.04 |  |
| `v5601_train_urga_monorailcargoengine/v5601_train_urga_monorailcargoengine_military_mission_mm320_train_rammer.ee` | 89 | 1472 | 1106 | 1127 | 5.02 × 5.46 × 18.04 |  |
| `v2201_helicopter_capstone_heavytroop/v2201_helicopter_capstone_heavytroop_debug.ee` | 174 | 2668 | 2106 | 921 | 4.24 × 15.75 × 17.60 |  |
| `v2201_helicopter_capstone_heavytroop/v2201_helicopter_capstone_heavytroop_military_01.ee` | 174 | 2668 | 2106 | 921 | 4.24 × 15.75 × 17.60 |  |
| `v2201_helicopter_capstone_heavytroop/v2201_helicopter_capstone_heavytroop_rebel_01.ee` | 174 | 2668 | 2106 | 921 | 4.24 × 15.75 × 17.60 |  |
| `v1300_boat_kensington_motoryacht/v1300_boat_kensington_motoryacht_civilian_01.ee` | 103 | 1812 | 1531 | 2241 | 4.02 × 6.50 × 16.17 |  |
| `v1300_boat_kensington_motoryacht/v1300_boat_kensington_motoryacht_debug.ee` | 103 | 1812 | 1531 | 2241 | 4.02 × 6.50 × 16.17 |  |
| `v2603_helicopter_urga_seascout/v2603_helicopter_urga_seascout_debug.ee` | 75 | 1108 | 925 | 1019 | 3.21 × 10.58 × 15.63 |  |
| `v2603_helicopter_urga_seascout/v2603_helicopter_urga_seascout_military_01.ee` | 75 | 1108 | 925 | 1019 | 3.21 × 10.58 × 15.63 |  |
| `v2603_helicopter_urga_seascout/v2603_helicopter_urga_seascout_rebel_01.ee` | 75 | 1108 | 925 | 1019 | 3.21 × 10.58 × 15.63 |  |
| `v1400_boat_mugello_spyspeedboat/v1400_boat_mugello_spyspeedboat_civilian_01.ee` | 43 | 760 | 650 | 967 | 4.62 × 3.12 × 15.09 |  |
| `v1400_boat_mugello_spyspeedboat/v1400_boat_mugello_spyspeedboat_debug.ee` | 43 | 760 | 650 | 967 | 4.62 × 3.12 × 15.09 |  |
| `v1400_boat_mugello_spyspeedboat/v1400_boat_mugello_spyspeedboat_premium_01.ee` | 43 | 760 | 650 | 967 | 4.62 × 3.12 × 15.09 |  |
| `v4602_plane_urga_fighterbomber/v4602_plane_urga_fighterbomber_debug.ee` | 131 | 2384 | 2103 | 1023 | 10.94 × 5.23 × 14.81 |  |
| `v4602_plane_urga_fighterbomber/v4602_plane_urga_fighterbomber_military_01.ee` | 131 | 2384 | 2103 | 1023 | 10.94 × 5.23 × 14.81 |  |
| `v4602_plane_urga_fighterbomber/v4602_plane_urga_fighterbomber_rebel_01.ee` | 131 | 2384 | 2103 | 1023 | 10.94 × 5.23 × 14.81 |  |
| `v2200_helicopter_capstone_assault/v2200_helicopter_capstone_assault_debug.ee` | 67 | 1264 | 1174 | 887 | 5.39 × 14.20 × 14.03 |  |
| `v2200_helicopter_capstone_assault/v2200_helicopter_capstone_assault_military_01.ee` | 67 | 1264 | 1174 | 887 | 5.39 × 14.20 × 14.03 |  |
| `v2200_helicopter_capstone_assault/v2200_helicopter_capstone_assault_rebel_01.ee` | 67 | 1264 | 1174 | 887 | 5.39 × 14.20 × 14.03 |  |
| `v4202_plane_capstone_fighterjet/v4202_plane_capstone_fighterjet_debug.ee` | 195 | 2736 | 2068 | 1001 | 10.44 × 4.82 × 13.96 |  |
| `v4202_plane_capstone_fighterjet/v4202_plane_capstone_fighterjet_military_01.ee` | 195 | 2736 | 2068 | 1001 | 10.44 × 4.82 × 13.96 |  |
| `v4202_plane_capstone_fighterjet/v4202_plane_capstone_fighterjet_rebel_01.ee` | 195 | 2736 | 2068 | 1001 | 10.44 × 4.82 × 13.96 |  |
| `v0005_car_autostraad_minetruck/v0005_car_autostraad_minetruck_commercial_01.ee` | 62 | 904 | 706 | 1023 | 11.00 × 9.04 × 13.86 |  |
| `v0005_car_autostraad_minetruck/v0005_car_autostraad_minetruck_debug.ee` | 62 | 904 | 706 | 1023 | 11.00 × 9.04 × 13.86 |  |
| `v2602_helicopter_urga_lightassault/v2602_helicopter_urga_lightassault_debug.ee` | 68 | 1460 | 1192 | 975 | 5.03 × 11.20 × 13.76 |  |
| `v2602_helicopter_urga_lightassault/v2602_helicopter_urga_lightassault_military_01.ee` | 68 | 1460 | 1192 | 975 | 5.03 × 11.20 × 13.76 |  |
| `v2602_helicopter_urga_lightassault/v2602_helicopter_urga_lightassault_military_01_custom_mm230.ee` | 68 | 1460 | 1192 | 975 | 5.03 × 11.20 × 13.76 |  |
| `v2602_helicopter_urga_lightassault/v2602_helicopter_urga_lightassault_rebel_01.ee` | 68 | 1460 | 1192 | 975 | 5.03 × 11.20 × 13.76 |  |
| `v4600_plane_urga_privatepropeller/v4600_plane_urga_privatepropeller_civilian_01.ee` | 58 | 1452 | 1139 | 1013 | 16.55 × 5.91 × 12.86 |  |
| `v4600_plane_urga_privatepropeller/v4600_plane_urga_privatepropeller_debug.ee` | 58 | 1452 | 1139 | 1013 | 16.55 × 5.91 × 12.86 |  |
| `v1401_boat_mugello_racingboat/v1401_boat_mugello_racingboat_civilian_01.ee` | 58 | 968 | 730 | 463 | 2.73 × 1.90 × 11.06 |  |
| `v1401_boat_mugello_racingboat/v1401_boat_mugello_racingboat_debug.ee` | 58 | 968 | 730 | 463 | 2.73 × 1.90 × 11.06 |  |
| `v1401_boat_mugello_racingboat/v1401_boat_mugello_racingboat_signature_preorder.ee` | 58 | 968 | 730 | 463 | 2.73 × 1.90 × 11.06 |  |
| `v2102_helicopter_eubus_utility/v2102_helicopter_eubus_utility_civilian_01.ee` | 69 | 1284 | 1078 | 2043 | 2.08 × 9.61 × 10.74 |  |
| `v2102_helicopter_eubus_utility/v2102_helicopter_eubus_utility_commercial_news.ee` | 69 | 1284 | 1078 | 2043 | 2.08 × 9.61 × 10.74 |  |
| `v2102_helicopter_eubus_utility/v2102_helicopter_eubus_utility_debug.ee` | 69 | 1284 | 1078 | 2043 | 2.08 × 9.61 × 10.74 |  |
| `v0006_car_autostraad_modernbus/v0006_car_autostraad_modernbus_commercial_01.ee` | 140 | 1716 | 1255 | 1089 | 2.96 × 3.87 × 10.62 |  |
| `v0006_car_autostraad_modernbus/v0006_car_autostraad_modernbus_debug.ee` | 140 | 1716 | 1255 | 1089 | 2.96 × 3.87 × 10.62 |  |
| `v1302_boat_kensington_sailboat/v1302_boat_kensington_sailboat_civilian_01.ee` | 53 | 616 | 553 | 995 | 4.08 × 15.77 × 10.31 |  |
| `v1302_boat_kensington_sailboat/v1302_boat_kensington_sailboat_debug.ee` | 53 | 616 | 553 | 995 | 4.08 × 15.77 × 10.31 |  |
| `v4500_plane_solar_smallfloatprop/v4500_plane_solar_smallfloatprop_civilian_01.ee` | 47 | 808 | 660 | 1021 | 10.74 × 4.61 × 10.07 |  |
| `v4500_plane_solar_smallfloatprop/v4500_plane_solar_smallfloatprop_debug.ee` | 47 | 808 | 660 | 1021 | 10.74 × 4.61 × 10.07 |  |

First 80 of 233 entities, largest hull bbox first. Full per-entity
JSON (every hull vertex, plane and index) is in `_JC3grab/hkx/out/`.

## Reading of the numbers

* A vehicle's collision is a compound: one or more `hknpExternMeshShape`s (chassis
  panels, vertices copied from the render mesh - which is why a 7 m body got 7 m
  collision with no physics edit) plus `hknpConvexPolytopeShape` hulls for wheels
  and props.
* The hull bbox is the union of every hull's local vertices: a physics bounding
  volume, not the body size - hulls are authored in their own frames.
* The wheel hardpoints are read from a known field now: `+0x30` of the 96-byte
  entries in `hknpPhysicsSystemData`'s fourth array, an `hkVector4` with `w == 1.0`.
  That typed field only yields a full four-station set on some vehicles, so it
  **confirms** `jc3phys.py` where it fires (no disagreements) but does not
  replace the raw-quad scan as the station source.

## Compound instance records (the hull -> part wiring)

A vehicle's collision is a tree, not a pile: `hknpStaticCompoundShape` /
`hknpDynamicCompoundShape` hold an `hkArray` at `+0x60` of 128-byte
`hknpShapeInstance` records, and each record is

| offset | field |
|---|---|
| `+0x00` / `+0x10` / `+0x20` | 3x3 basis, three `float4` rows (the `w` lane carries a per-row norm marker, `0.5` on a unit row) |
| `+0x30` | translation, `float4` |
| `+0x40` | scale, `float4` (`1,1,1,1` everywhere observed) |
| `+0x50` | child shape pointer (virtual fixup) |
| `+0x60` / `+0x70` | zero |

The array is **inline at `+0xD0`** on the static class (so the object's extent covers
header + instances) and a **separate allocation** on the dynamic one; the header at
`+0x60` says which, and element stride `128` is confirmed by the gap to the next
target, `count x 128` exactly.

**Placement is `p' = M^T p + t`.** That is not a guess either: the Serpente's doors
and roof carry 0.94/0.34 rotations, and under this reading every rotated child lands
inside its compound's own AABB, while the other reading ( `M p` ) puts them up to
0.14 m outside. Identity placements - the majority - cannot tell the two apart.

**Wiring.** A child shape's `ref_counted_properties` (`+0x20`) reaches a
`CPfxPartIndexProperty`, whose part index is a u32 at `+0x10`. Joined to
`PARTS_TABLE.jsonl` that is a part *name*, which is what `WIRING.md` tabulates:
**6,382 compounds, 35,499 instances,
25,769 with a part index**, and the AABB checks above as the proof
that the record layout is right rather than merely plausible.

`wiring` writes `WIRING.jsonl` (one row per instance: entity, file, compound,
instance, child class, AABB, part index, part name).

## Still open

* **Body -> shape wiring.** The 80-byte body entries and 64-byte motion entries are
  counted and sized but their fields are not pinned; the compound instances carry
  the shape -> part wiring (`WIRING.md`), which is what the mod needed.
* **Quantized mesh vertices.** `hknpExternMeshShapeData` stores 3 × u16 per vertex
  (6-byte stride, confirmed by the gap to the next array); dequantizing against the
  shape AABB reproduces the minimum corner but not the extent, so the frame is
  chunk-relative and not yet pinned. Counts and AABBs are exact; positions are not.
* **Face table semantics.** 4-byte records (`u16 first, u8 count, u8 min` reads
  plausibly for the first records); only the index block is validated, so faces are
  reported as bytes.
* **Writing.** Nothing here writes a `.physicsc` - reading only.
