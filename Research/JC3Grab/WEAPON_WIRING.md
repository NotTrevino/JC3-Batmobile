# JC3 vehicle weapon wiring (G2-11)

How each armed vehicle binds its weapons: the root slot pointers, every weapon component and its properties, the fire points, aim components, the seat that owns it, and the moving parts on the chassis. Decoded by `Tools/scripts/jc3wiring.py` from the entity `.epe` inside each `.ee` (Gibbed `ConvertProperty`), joined with `PARTS_TABLE.jsonl` (parts module) and `FEATURE_CENSUS.json` (the armed list). The weapon tunes themselves are in `WEAPONS.md` (G2-10).

## 1. The slot properties (and how their names were recovered)

Each root class (`CCar`, `CAirPlane`, `CBoat`, `CHelicopter`, `CTrain`) carries all four pointers; unused ones are `00000000`. RTPC writes a property's 32-bit name hash when the entity's name table does not carry the string, so two slots only have ids. Hashing candidates with the archive-path Jenkins function (`rbmhdr.hash_jenkins`) recovers a name only when the exact 32-bit value lands - six did:

| slot | property in the `.epe` | Jenkins(name) | who fires it |
|---|---|---|---|
| 1st driver | `id:851CAABE` | `main_weapon` = `851CAABE` | driver |
| 2nd driver | `id:00568A74` | **no name found** | driver |
| 1st gunner | `mounted_weapon` | named in the file | gunner seat |
| 2nd gunner | `id:AC0BC788` | `mounted_weapon_2` = `AC0BC788` | gunner seat |

Other recovered property names used below: `tuning_file` = `AA7096C9`, `autoaim_tuning_file` = `6D4C8277`, `impact_usage` = `D075017A`, `weapon_category` = `19068026`. `id:D04059E6` is the Jenkins hash of every object's class name (checked on every decoded object by `--check`). The 2nd driver slot resisted a 1.1-million-string vocabulary search (57 weapon/mount words in 2- and 3-word combinations, numeric suffixes); its id is the name of record.

`--check` also confirms the two trailing pointer properties (`id:8580BA42`, `id:CA86AA17`) are null on all 53 armed entities and never resolve to a weapon; they are recorded per root in the jsonl as `other_pointers`.

The unarmed buggy and the civilian Serpente sampled for this check carry all four properties too, each set to `00000000` - the pointers exist on the class, not on the variant.

## 2. The questions the card asks

**(a) Most driver-fired weapons on a land vehicle: 2.**

Two driver slots are wired on `v0201_car_capstone_mediumtank`, `v0202_car_capstone_bavariumtank`. Every other land vehicle has one or none.
Across all 53 armed entities the maximum is 2; no file has a third driver slot.

**(b) How two weapons are bound to primary/secondary fire.**

The root class carries two separate object pointers, not a list with an order. `id:851CAABE` is the first (`main_weapon`), `id:00568A74` the second. Each points at a weapon component by `_object_id`; a component with no pointer is dead weight (the fighter jet ships one). The component itself has no slot property, its `weapon_type` is `2` for every weapon, and the G2-10 tunes contain no slot or input member - so the only slot data in the game files is these two root pointers. Which button each maps to is not encoded in the entity - `action_1`/`action_2` are `1`/`2` on armed and unarmed cars alike - and neither is switching: there is no active-slot index, no next/previous weapon action and no weapon group anywhere in the `.epe`. Both slots are simply available.

**(c) Any vehicle that switches between three or more weapons?**

No. The most bound weapons on one entity is 2 (two driver, or two gunner); the most weapon components carried is 3.
Components outnumber bound weapons here (the extra is never referenced by a slot):

| entity | components | bound | unbound |
|---|---|---|---|
| `v4202_plane_capstone_fighterjet_debug.ee` | 3 | 2 | `w608_fighterjet_missile` |
| `v4202_plane_capstone_fighterjet_military_01.ee` | 3 | 2 | `w608_fighterjet_missile` |
| `v4202_plane_capstone_fighterjet_rebel_01.ee` | 3 | 2 | `w608_fighterjet_missile` |
| `v4602_plane_urga_fighterbomber_debug.ee` | 3 | 2 | `w612_fighterbomber_missile_air_lockon` |
| `v4602_plane_urga_fighterbomber_military_01.ee` | 3 | 2 | `w612_fighterbomber_missile_air_lockon` |
| `v4602_plane_urga_fighterbomber_rebel_01.ee` | 3 | 2 | `w612_fighterbomber_missile_air_lockon` |
| `v5603_train_urga_monorailmissilecar_military_01.ee` | 1 | 0 | `w614_monorailmissilecar_missile` |

**(d) Which wiring is driver-fired on a `CCar`?**

| entity | chassis | driver slots | weapons | gunner seats |
|---|---|---|---|---|
| `v0201_car_capstone_mediumtank_debug.ee` | `v0201_car_capstone_mediumtank` | 2 | `w603_mediumtank_mgun`, `w602_mediumtank_canon` | - |
| `v0201_car_capstone_mediumtank_military_01.ee` | `v0201_car_capstone_mediumtank` | 2 | `w603_mediumtank_mgun`, `w602_mediumtank_canon` | - |
| `v0201_car_capstone_mediumtank_rebel_01.ee` | `v0201_car_capstone_mediumtank` | 2 | `w603_mediumtank_mgun`, `w602_mediumtank_canon` | - |
| `v0202_car_capstone_bavariumtank_debug.ee` | `v0202_car_capstone_bavariumtank` | 2 | `w603_mediumtank_mgun`, `w602_mediumtank_canon` | - |
| `v0202_car_capstone_bavariumtank_military_01.ee` | `v0202_car_capstone_bavariumtank` | 2 | `w603_mediumtank_mgun`, `w602_mediumtank_canon` | - |
| `v0202_car_capstone_bavariumtank_rebel_01.ee` | `v0202_car_capstone_bavariumtank` | 2 | `w603_mediumtank_mgun`, `w602_mediumtank_canon` | - |
| `v0300_car_kensington_sportsmuscle_signature_preorder.ee` | `v0300_car_kensington_sportsmuscle` | 1 | `w618_sportsmuscle_missile` | - |
| `v0603_car_urga_smalltank_debug.ee` | `v0603_car_urga_smalltank` | 1 | `w605_smalltank_canon` | - |
| `v0603_car_urga_smalltank_military_01.ee` | `v0603_car_urga_smalltank` | 1 | `w605_smalltank_canon` | - |
| `v0603_car_urga_smalltank_rebel_01.ee` | `v0603_car_urga_smalltank` | 1 | `w605_smalltank_canon` | - |
| `v0604_car_urga_buggy_signature_preorder.ee` | `v0604_car_urga_buggy` | 1 | `w619_buggy_mgun` | - |
| `v0200_car_capstone_apc_debug.ee` | `v0200_car_capstone_apc` | 0 | - | `w206_mounted_capstone_m2hm` |
| `v0200_car_capstone_apc_military_01.ee` | `v0200_car_capstone_apc` | 0 | - | `w206_mounted_capstone_m2hm` |
| `v0200_car_capstone_apc_rebel_01.ee` | `v0200_car_capstone_apc` | 0 | - | `w206_mounted_capstone_m2hm` |
| `v0504_car_solar_technicaljeep_rebel_machinegun.ee` | `v0504_car_solar_technicaljeep` | 0 | - | `w206_mounted_capstone_m2hm` |
| `v0600_car_urga_armoredjeep_military_01.ee` | `v0600_car_urga_armoredjeep` | 0 | - | `w206_mounted_capstone_m2hm` |
| `v0600_car_urga_armoredjeep_rebel_01.ee` | `v0600_car_urga_armoredjeep` | 0 | - | `w206_mounted_capstone_m2hm` |

The last row is the cargo-plane variant: its driver slots belong to the tank carried in its hold, not to the plane. On an actual land `.ee`, the two CCars with two driver slots are the medium tank and the Bavarium tank; the small tank, the signature Serpente and the signature buggy have one; every other land vehicle is gunner-only or unarmed.

## 3. Fleet summary

| item | value |
|---|---|
| armed entities | **53** |
| chassis | **21** |
| primary root `CCar` | 17 |
| primary root `CAirPlane` | 9 |
| primary root `CBoat` | 12 |
| primary root `CHelicopter` | 14 |
| primary root `CTrain` | 1 |
| weapon components | **88** |
| bound to a slot | 81 |
| unbound | 7 |

| weapon class | components |
|---|---|
| `CBulletWeaponBase` | 57 |
| `CMissileWeaponBase` | 25 |
| `CRPGFireLeachWeapon` | 6 |

Counts above are components and roots, not vehicles. The cargo-tank variant carries a full `CCar` (tank) next to its `CAirPlane`, so the {len(rows)} entities hold 54 root objects; the table counts each entity's primary root only, and that entity's tank slots are counted where its CCar is.

`CLightWeaponComponent` is in the census as a weapon class but is a warning *light* attached to a weapon (30 components on 9 entities); it is listed as a subcomponent, not counted as a weapon.

Seat states found in the armed fleet:

| state | seats |
|---|---|
| `S_IDLE` | 57 |
| `S_IDLE_DRIVER_VEHICLE` | 53 |
| `S_IDLE_PASSENGER_VEHICLE` | 50 |
| `S_DRIVER_SIDE_TO_HANG_VEHICLE` | 14 |
| `S_VEHICLE_FIXED_MOUNTED_WEAPON` | 13 |
| `S_IDLE_PASSENGER_INNER` | 9 |
| `S_IDLE_VEHICLE_SPINNING_MOUNTED_WEAPON` | 6 |
| `S_MOUNTED_WEAPON` | 3 |

Unbound weapon components (present, no slot points at them):

- `v4202_plane_capstone_fighterjet_debug.ee`: `w608_fighterjet_missile`
- `v4202_plane_capstone_fighterjet_military_01.ee`: `w608_fighterjet_missile`
- `v4202_plane_capstone_fighterjet_rebel_01.ee`: `w608_fighterjet_missile`
- `v4602_plane_urga_fighterbomber_debug.ee`: `w612_fighterbomber_missile_air_lockon`
- `v4602_plane_urga_fighterbomber_military_01.ee`: `w612_fighterbomber_missile_air_lockon`
- `v4602_plane_urga_fighterbomber_rebel_01.ee`: `w612_fighterbomber_missile_air_lockon`
- `v5603_train_urga_monorailmissilecar_military_01.ee`: `w614_monorailmissilecar_missile`

### The mounted M2, and why it is not in `WEAPONS.md`

`w206_mounted_capstone_m2hm` is the fleet's most common gunner weapon: 19 components over 5 chassis (`v0200_car_capstone_apc`, `v0504_car_solar_technicaljeep`, `v0600_car_urga_armoredjeep`, `v1200_boat_capstone_heavypatrol`, `v1704_boat_na_lightpatrol`). It sits in `editor/entities/jc_weapons/04_mounted/`, outside the `06_vehicle` filter G2-10 used, so it has no row there. Its tune and its two `GripPointSettings` variants are already in `WEAPONS_SHARED.json` (G2-10's shared list); this script records the per-entity `tuning_file` path and the grip-point/mount wiring that G2-10 left out.

## 4. Entity index

| entity | class | chassis | driver | gunner | weapons |
|---|---|---|---|---|---|
| `v0200_car_capstone_apc_debug.ee` | `CCar` | `v0200_car_capstone_apc` | 0 | 1 | `w206_mounted_capstone_m2hm` |
| `v0200_car_capstone_apc_military_01.ee` | `CCar` | `v0200_car_capstone_apc` | 0 | 1 | `w206_mounted_capstone_m2hm` |
| `v0200_car_capstone_apc_rebel_01.ee` | `CCar` | `v0200_car_capstone_apc` | 0 | 1 | `w206_mounted_capstone_m2hm` |
| `v0201_car_capstone_mediumtank_debug.ee` | `CCar` | `v0201_car_capstone_mediumtank` | 2 | 0 | `w603_mediumtank_mgun`, `w602_mediumtank_canon` |
| `v0201_car_capstone_mediumtank_military_01.ee` | `CCar` | `v0201_car_capstone_mediumtank` | 2 | 0 | `w603_mediumtank_mgun`, `w602_mediumtank_canon` |
| `v0201_car_capstone_mediumtank_rebel_01.ee` | `CCar` | `v0201_car_capstone_mediumtank` | 2 | 0 | `w603_mediumtank_mgun`, `w602_mediumtank_canon` |
| `v0202_car_capstone_bavariumtank_debug.ee` | `CCar` | `v0202_car_capstone_bavariumtank` | 2 | 0 | `w603_mediumtank_mgun`, `w602_mediumtank_canon` |
| `v0202_car_capstone_bavariumtank_military_01.ee` | `CCar` | `v0202_car_capstone_bavariumtank` | 2 | 0 | `w603_mediumtank_mgun`, `w602_mediumtank_canon` |
| `v0202_car_capstone_bavariumtank_rebel_01.ee` | `CCar` | `v0202_car_capstone_bavariumtank` | 2 | 0 | `w603_mediumtank_mgun`, `w602_mediumtank_canon` |
| `v0300_car_kensington_sportsmuscle_signature_preorder.ee` | `CCar` | `v0300_car_kensington_sportsmuscle` | 1 | 0 | `w618_sportsmuscle_missile` |
| `v0504_car_solar_technicaljeep_rebel_machinegun.ee` | `CCar` | `v0504_car_solar_technicaljeep` | 0 | 1 | `w206_mounted_capstone_m2hm` |
| `v0600_car_urga_armoredjeep_military_01.ee` | `CCar` | `v0600_car_urga_armoredjeep` | 0 | 1 | `w206_mounted_capstone_m2hm` |
| `v0600_car_urga_armoredjeep_rebel_01.ee` | `CCar` | `v0600_car_urga_armoredjeep` | 0 | 1 | `w206_mounted_capstone_m2hm` |
| `v0603_car_urga_smalltank_debug.ee` | `CCar` | `v0603_car_urga_smalltank` | 1 | 0 | `w605_smalltank_canon` |
| `v0603_car_urga_smalltank_military_01.ee` | `CCar` | `v0603_car_urga_smalltank` | 1 | 0 | `w605_smalltank_canon` |
| `v0603_car_urga_smalltank_rebel_01.ee` | `CCar` | `v0603_car_urga_smalltank` | 1 | 0 | `w605_smalltank_canon` |
| `v0604_car_urga_buggy_signature_preorder.ee` | `CCar` | `v0604_car_urga_buggy` | 1 | 0 | `w619_buggy_mgun` |
| `v1200_boat_capstone_heavypatrol_debug.ee` | `CBoat` | `v1200_boat_capstone_heavypatrol` | 0 | 2 | `w206_mounted_capstone_m2hm`, `w206_mounted_capstone_m2hm` |
| `v1200_boat_capstone_heavypatrol_military_01.ee` | `CBoat` | `v1200_boat_capstone_heavypatrol` | 0 | 2 | `w206_mounted_capstone_m2hm`, `w206_mounted_capstone_m2hm` |
| `v1200_boat_capstone_heavypatrol_military_01_delivery.ee` | `CBoat` | `v1200_boat_capstone_heavypatrol` | 0 | 2 | `w206_mounted_capstone_m2hm`, `w206_mounted_capstone_m2hm` |
| `v1200_boat_capstone_heavypatrol_rebel_01.ee` | `CBoat` | `v1200_boat_capstone_heavypatrol` | 0 | 2 | `w206_mounted_capstone_m2hm`, `w206_mounted_capstone_m2hm` |
| `v1200_boat_capstone_heavypatrol_rebel_01_mm210.ee` | `CBoat` | `v1200_boat_capstone_heavypatrol` | 0 | 2 | `w206_mounted_capstone_m2hm`, `w206_mounted_capstone_m2hm` |
| `v1202_boat_capstone_corvette_debug.ee` | `CBoat` | `v1202_boat_capstone_corvette` | 1 | 0 | `w616_corvette_canon` |
| `v1202_boat_capstone_corvette_military_01.ee` | `CBoat` | `v1202_boat_capstone_corvette` | 1 | 0 | `w616_corvette_canon` |
| `v1202_boat_capstone_corvette_rebel_01.ee` | `CBoat` | `v1202_boat_capstone_corvette` | 1 | 0 | `w616_corvette_canon` |
| `v1401_boat_mugello_racingboat_signature_preorder.ee` | `CBoat` | `v1401_boat_mugello_racingboat` | 1 | 0 | `w620_racingboat_mgun` |
| `v1704_boat_na_lightpatrol_debug.ee` | `CBoat` | `v1704_boat_na_lightpatrol` | 0 | 1 | `w206_mounted_capstone_m2hm` |
| `v1704_boat_na_lightpatrol_military_01.ee` | `CBoat` | `v1704_boat_na_lightpatrol` | 0 | 1 | `w206_mounted_capstone_m2hm` |
| `v1704_boat_na_lightpatrol_rebel_01.ee` | `CBoat` | `v1704_boat_na_lightpatrol` | 0 | 1 | `w206_mounted_capstone_m2hm` |
| `v2200_helicopter_capstone_assault_debug.ee` | `CHelicopter` | `v2200_helicopter_capstone_assault` | 2 | 0 | `w615_helicopter_heavy_missile`, `w601_helicopter_missile` |
| `v2200_helicopter_capstone_assault_military_01.ee` | `CHelicopter` | `v2200_helicopter_capstone_assault` | 2 | 0 | `w615_helicopter_heavy_missile`, `w601_helicopter_missile` |
| `v2200_helicopter_capstone_assault_rebel_01.ee` | `CHelicopter` | `v2200_helicopter_capstone_assault` | 2 | 0 | `w615_helicopter_heavy_missile`, `w601_helicopter_missile` |
| `v2601_helicopter_urga_heavyassault_debug.ee` | `CHelicopter` | `v2601_helicopter_urga_heavyassault` | 2 | 0 | `w607_heavyhelicopter_mgun`, `w606_heavyhelicopter_missile` |
| `v2601_helicopter_urga_heavyassault_military_01.ee` | `CHelicopter` | `v2601_helicopter_urga_heavyassault` | 2 | 0 | `w607_heavyhelicopter_mgun`, `w606_heavyhelicopter_missile` |
| `v2601_helicopter_urga_heavyassault_rebel_01.ee` | `CHelicopter` | `v2601_helicopter_urga_heavyassault` | 2 | 0 | `w607_heavyhelicopter_mgun`, `w606_heavyhelicopter_missile` |
| `v2602_helicopter_urga_lightassault_debug.ee` | `CHelicopter` | `v2602_helicopter_urga_lightassault` | 1 | 0 | `w604_helicopter_mgun` |
| `v2602_helicopter_urga_lightassault_military_01.ee` | `CHelicopter` | `v2602_helicopter_urga_lightassault` | 1 | 0 | `w604_helicopter_mgun` |
| `v2602_helicopter_urga_lightassault_rebel_01.ee` | `CHelicopter` | `v2602_helicopter_urga_lightassault` | 1 | 0 | `w604_helicopter_mgun` |
| `v2604_helicopter_urga_advancedassault_debug.ee` | `CHelicopter` | `v2604_helicopter_urga_advancedassault` | 2 | 0 | `w621_advancedhelicopter_missile`, `w622_advancedhelicopter_mgun` |
| `v2604_helicopter_urga_advancedassault_military_01.ee` | `CHelicopter` | `v2604_helicopter_urga_advancedassault` | 2 | 0 | `w621_advancedhelicopter_missile`, `w622_advancedhelicopter_mgun` |
| `v2604_helicopter_urga_advancedassault_rebel_01.ee` | `CHelicopter` | `v2604_helicopter_urga_advancedassault` | 2 | 0 | `w621_advancedhelicopter_missile`, `w622_advancedhelicopter_mgun` |
| `v2604_helicopter_urga_advancedassault_signature_shielded.ee` | `CHelicopter` | `v2604_helicopter_urga_advancedassault` | 2 | 0 | `w621_advancedhelicopter_missile`, `w622_advancedhelicopter_mgun` |
| `v2604_helicopter_urga_advancedassault_signature_shielded_di_ravello.ee` | `CHelicopter` | `v2604_helicopter_urga_advancedassault` | 2 | 0 | `w621_advancedhelicopter_missile`, `w622_advancedhelicopter_mgun` |
| `v4202_plane_capstone_fighterjet_debug.ee` | `CAirPlane` | `v4202_plane_capstone_fighterjet` | 2 | 0 | `w608_fighterjet_missile`, `w610_fighterjet_mgun`, `w609_fighterjet_missile_air_lockon` |
| `v4202_plane_capstone_fighterjet_military_01.ee` | `CAirPlane` | `v4202_plane_capstone_fighterjet` | 2 | 0 | `w608_fighterjet_missile`, `w610_fighterjet_mgun`, `w609_fighterjet_missile_air_lockon` |
| `v4202_plane_capstone_fighterjet_rebel_01.ee` | `CAirPlane` | `v4202_plane_capstone_fighterjet` | 2 | 0 | `w608_fighterjet_missile`, `w610_fighterjet_mgun`, `w609_fighterjet_missile_air_lockon` |
| `v4602_plane_urga_fighterbomber_debug.ee` | `CAirPlane` | `v4602_plane_urga_fighterbomber` | 2 | 0 | `w612_fighterbomber_missile_air_lockon`, `w611_fighterbomber_missile`, `w613_fighterbomber_missile_ground_lockon` |
| `v4602_plane_urga_fighterbomber_military_01.ee` | `CAirPlane` | `v4602_plane_urga_fighterbomber` | 2 | 0 | `w612_fighterbomber_missile_air_lockon`, `w611_fighterbomber_missile`, `w613_fighterbomber_missile_ground_lockon` |
| `v4602_plane_urga_fighterbomber_rebel_01.ee` | `CAirPlane` | `v4602_plane_urga_fighterbomber` | 2 | 0 | `w612_fighterbomber_missile_air_lockon`, `w611_fighterbomber_missile`, `w613_fighterbomber_missile_ground_lockon` |
| `v4603_plane_urga_cargotransport_military_cargo_tank.ee` | `CAirPlane/CCar` | `v4603_plane_urga_cargotransport` | 2 | 0 | `w602_mediumtank_canon`, `w603_mediumtank_mgun` |
| `v4800_plane_brothers_vintagefighter_debug.ee` | `CAirPlane` | `v4800_plane_brothers_vintagefighter` | 1 | 0 | `w617_vintagefighter_mgun` |
| `v4800_plane_brothers_vintagefighter_rebel_01.ee` | `CAirPlane` | `v4800_plane_brothers_vintagefighter` | 1 | 0 | `w617_vintagefighter_mgun` |
| `v5603_train_urga_monorailmissilecar_military_01.ee` | `CTrain` | `v5603_train_urga_monorailmissilecar` | 0 | 0 | `w614_monorailmissilecar_missile` |

## 5. Entities

### `v0200_car_capstone_apc_debug.ee`

`CCar` · chassis `v0200_car_capstone_apc` · source `archives_win64/game35` @160,751,616 +6,093,712 B · 1 weapon component(s), 0 driver slot(s), 1 gunner slot(s)

slots on `CCar` `v0200_car_capstone_apc_generated`: main_weapon - · secondary (id:00568A74) - · mounted_weapon `w206_mounted_capstone_m2hm` · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `mounted_weapon` | `CBulletWeaponBase` | `w206_mounted_capstone_m2hm` | 206 | 1 | - | `apc_turret_base`, `apc_weapon_mount_vertical` |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `FirePosition` | 2 | 0 | 0 | 0.141 | -1.0041 |
| `w206_mounted_capstone_m2hm` | `attach.vehicle` | 4 | 0 | 0 | -0.0541 | 0.0021 |
| `w206_mounted_capstone_m2hm` | `LeftHandMountedAttach` | 1 | 0 | -0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `RightHandMountedAttach` | 1 | 0 | 0.1 | 0.08 | 0.3 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `editor/entities/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_assault_rifle.wtune` | 1011 | 50CalBulletImpact |

- `w206_mounted_capstone_m2hm` (mounted_weapon) is mounted nearest `interaction.seat.gunner1` (seat index `6`, point `point.mounted_weapon`, 1.529 m).

seats on `CCar` `v0200_car_capstone_apc_generated`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.passenger2` | 2 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger2` |
| `interaction.seat.gunner1` | 6 | `S_IDLE_VEHICLE_SPINNING_MOUNTED_WEAPON` | `point.mounted_weapon` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.passenger6` | 24 | `S_IDLE_PASSENGER_INNER`, `S_IDLE_PASSENGER_VEHICLE` | `point.passenger6` |
| `interaction.seat.passenger5` | 5 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger5` |
| `interaction.seat.passenger4` | 4 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger4` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_INNER`, `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |
| `interaction.seat.passenger3` | 3 | `S_IDLE_PASSENGER_INNER`, `S_IDLE_PASSENGER_VEHICLE` | `point.passenger3` |

moving parts on the chassis: `apc_turret_base` (Turret, 30 ← `apc_body`), `apc_weapon_mount_vertical` (Cannon, 44 ← `apc_turret_base`)

### `v0200_car_capstone_apc_military_01.ee`

`CCar` · chassis `v0200_car_capstone_apc` · source `archives_win64/game35` @166,850,560 +6,093,744 B · 1 weapon component(s), 0 driver slot(s), 1 gunner slot(s)

slots on `CCar` `v0200_car_capstone_apc_military_01`: main_weapon - · secondary (id:00568A74) - · mounted_weapon `w206_mounted_capstone_m2hm` · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `mounted_weapon` | `CBulletWeaponBase` | `w206_mounted_capstone_m2hm` | 206 | 1 | - | `apc_turret_base`, `apc_weapon_mount_vertical` |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `FirePosition` | 2 | 0 | 0 | 0.141 | -1.0041 |
| `w206_mounted_capstone_m2hm` | `attach.vehicle` | 4 | 0 | 0 | -0.0541 | 0.0021 |
| `w206_mounted_capstone_m2hm` | `LeftHandMountedAttach` | 1 | 0 | -0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `RightHandMountedAttach` | 1 | 0 | 0.1 | 0.08 | 0.3 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `editor/entities/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_assault_rifle.wtune` | 1011 | 50CalBulletImpact |

- `w206_mounted_capstone_m2hm` (mounted_weapon) is mounted nearest `interaction.seat.gunner1` (seat index `6`, point `point.mounted_weapon`, 1.529 m).

seats on `CCar` `v0200_car_capstone_apc_military_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.passenger2` | 2 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger2` |
| `interaction.seat.gunner1` | 6 | `S_IDLE_VEHICLE_SPINNING_MOUNTED_WEAPON` | `point.mounted_weapon` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.passenger6` | 24 | `S_IDLE_PASSENGER_INNER`, `S_IDLE_PASSENGER_VEHICLE` | `point.passenger6` |
| `interaction.seat.passenger5` | 5 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger5` |
| `interaction.seat.passenger4` | 4 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger4` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_INNER`, `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |
| `interaction.seat.passenger3` | 3 | `S_IDLE_PASSENGER_INNER`, `S_IDLE_PASSENGER_VEHICLE` | `point.passenger3` |

moving parts on the chassis: `apc_turret_base` (Turret, 30 ← `apc_body`), `apc_weapon_mount_vertical` (Cannon, 44 ← `apc_turret_base`)

### `v0200_car_capstone_apc_rebel_01.ee`

`CCar` · chassis `v0200_car_capstone_apc` · source `archives_win64/game35` @172,949,504 +5,826,336 B · 1 weapon component(s), 0 driver slot(s), 1 gunner slot(s)

slots on `CCar` `v0200_car_capstone_apc_rebel_01`: main_weapon - · secondary (id:00568A74) - · mounted_weapon `w206_mounted_capstone_m2hm` · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `mounted_weapon` | `CBulletWeaponBase` | `w206_mounted_capstone_m2hm` | 206 | 1 | - | `apc_turret_base`, `apc_weapon_mount_vertical` |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `FirePosition` | 2 | 0 | 0 | 0.141 | -1.0041 |
| `w206_mounted_capstone_m2hm` | `attach.vehicle` | 4 | 0 | 0 | -0.0541 | 0.0021 |
| `w206_mounted_capstone_m2hm` | `LeftHandMountedAttach` | 1 | 0 | -0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `RightHandMountedAttach` | 1 | 0 | 0.1 | 0.08 | 0.3 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `editor/entities/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_assault_rifle.wtune` | 1011 | 50CalBulletImpact |

- `w206_mounted_capstone_m2hm` (mounted_weapon) is mounted nearest `interaction.seat.gunner1` (seat index `6`, point `point.mounted_weapon`, 1.529 m).

seats on `CCar` `v0200_car_capstone_apc_rebel_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.passenger2` | 2 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger2` |
| `interaction.seat.gunner1` | 6 | `S_IDLE_VEHICLE_SPINNING_MOUNTED_WEAPON` | `point.mounted_weapon` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.passenger6` | 24 | `S_IDLE_PASSENGER_INNER`, `S_IDLE_PASSENGER_VEHICLE` | `point.passenger6` |
| `interaction.seat.passenger5` | 5 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger5` |
| `interaction.seat.passenger4` | 4 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger4` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_INNER`, `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |
| `interaction.seat.passenger3` | 3 | `S_IDLE_PASSENGER_INNER`, `S_IDLE_PASSENGER_VEHICLE` | `point.passenger3` |

moving parts on the chassis: `apc_turret_base` (Turret, 30 ← `apc_body`), `apc_weapon_mount_vertical` (Cannon, 44 ← `apc_turret_base`)

### `v0201_car_capstone_mediumtank_debug.ee`

`CCar` · chassis `v0201_car_capstone_mediumtank` · source `archives_win64/game35` @178,780,160 +5,058,224 B · 2 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CCar` `v0201_car_capstone_mediumtank_generated`: main_weapon `w602_mediumtank_canon` · secondary (id:00568A74) `w603_mediumtank_mgun` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `secondary (id:00568A74)` | `CBulletWeaponBase` | `w603_mediumtank_mgun` | 603 | 1 | - | - |
| `main_weapon` | `CBulletWeaponBase` | `w602_mediumtank_canon` | 602 | 1 | `warning_light` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w603_mediumtank_mgun` | `fire_position_0` | 2 | 0 | 0.247 | 0.485 | -2.018 |
| `w602_mediumtank_canon` | `fire_position_0` | 2 | 0 | 0 | 0.3739 | -5.8174 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w603_mediumtank_mgun` | `editor/entities/jc_weapons/06_vehicle/w603_mediumtank_mgun/w603_mediumtank_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | 50CalBulletImpact |
| `w602_mediumtank_canon` | `editor/entities/jc_weapons/06_vehicle/w602_mediumtank_canon/w602_mediumtank_canon.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | AAGunImpact |

seats on `CCar` `v0201_car_capstone_mediumtank_generated`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

moving parts on the chassis: `mediumtank_turret` (Turret, 26 ← `mediumtank_body`), `mediumtank_cannon` (Cannon, 38 ← `mediumtank_turret`)

### `v0201_car_capstone_mediumtank_military_01.ee`

`CCar` · chassis `v0201_car_capstone_mediumtank` · source `archives_win64/game35` @183,842,816 +5,058,192 B · 2 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CCar` `v0201_car_capstone_mediumtank_military_01`: main_weapon `w602_mediumtank_canon` · secondary (id:00568A74) `w603_mediumtank_mgun` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `secondary (id:00568A74)` | `CBulletWeaponBase` | `w603_mediumtank_mgun` | 603 | 1 | - | - |
| `main_weapon` | `CBulletWeaponBase` | `w602_mediumtank_canon` | 602 | 1 | `warning_light` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w603_mediumtank_mgun` | `fire_position_0` | 2 | 0 | 0.247 | 0.485 | -2.018 |
| `w602_mediumtank_canon` | `fire_position_0` | 2 | 0 | 0 | 0.3739 | -5.8174 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w603_mediumtank_mgun` | `editor/entities/jc_weapons/06_vehicle/w603_mediumtank_mgun/w603_mediumtank_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | 50CalBulletImpact |
| `w602_mediumtank_canon` | `editor/entities/jc_weapons/06_vehicle/w602_mediumtank_canon/w602_mediumtank_canon.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | AAGunImpact |

seats on `CCar` `v0201_car_capstone_mediumtank_military_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

moving parts on the chassis: `mediumtank_turret` (Turret, 26 ← `mediumtank_body`), `mediumtank_cannon` (Cannon, 38 ← `mediumtank_turret`)

### `v0201_car_capstone_mediumtank_rebel_01.ee`

`CCar` · chassis `v0201_car_capstone_mediumtank` · source `archives_win64/game35` @188,905,472 +5,110,192 B · 2 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CCar` `v0201_car_capstone_mediumtank_rebel_01`: main_weapon `w602_mediumtank_canon` · secondary (id:00568A74) `w603_mediumtank_mgun` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `secondary (id:00568A74)` | `CBulletWeaponBase` | `w603_mediumtank_mgun` | 603 | 1 | - | - |
| `main_weapon` | `CBulletWeaponBase` | `w602_mediumtank_canon` | 602 | 1 | `warning_light` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w603_mediumtank_mgun` | `fire_position_0` | 2 | 0 | 0.247 | 0.485 | -2.018 |
| `w602_mediumtank_canon` | `fire_position_0` | 2 | 0 | 0 | 0.3739 | -5.8174 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w603_mediumtank_mgun` | `editor/entities/jc_weapons/06_vehicle/w603_mediumtank_mgun/w603_mediumtank_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | 50CalBulletImpact |
| `w602_mediumtank_canon` | `editor/entities/jc_weapons/06_vehicle/w602_mediumtank_canon/w602_mediumtank_canon.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | AAGunImpact |

seats on `CCar` `v0201_car_capstone_mediumtank_rebel_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

moving parts on the chassis: `mediumtank_turret` (Turret, 26 ← `mediumtank_body`), `mediumtank_cannon` (Cannon, 38 ← `mediumtank_turret`)

### `v0202_car_capstone_bavariumtank_debug.ee`

`CCar` · chassis `v0202_car_capstone_bavariumtank` · source `archives_win64/game35` @194,021,376 +4,828,064 B · 2 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CCar` `v0202_car_capstone_bavariumtank_generated`: main_weapon `w602_mediumtank_canon` · secondary (id:00568A74) `w603_mediumtank_mgun` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `secondary (id:00568A74)` | `CBulletWeaponBase` | `w603_mediumtank_mgun` | 603 | 1 | - | - |
| `main_weapon` | `CBulletWeaponBase` | `w602_mediumtank_canon` | 602 | 1 | `warning_light` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w603_mediumtank_mgun` | `fire_position_0` | 2 | 0 | 0.469 | 0.558 | -1.876 |
| `w602_mediumtank_canon` | `fire_position_0` | 2 | 0 | 0 | 0.3739 | -5.8174 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w603_mediumtank_mgun` | `editor/entities/jc_weapons/06_vehicle/w603_mediumtank_mgun/w603_mediumtank_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | 50CalBulletImpact |
| `w602_mediumtank_canon` | `editor/entities/jc_weapons/06_vehicle/w602_mediumtank_canon/w602_mediumtank_canon.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | AAGunImpact |

seats on `CCar` `v0202_car_capstone_bavariumtank_generated`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

moving parts on the chassis: `bavariumtank_turret` (Turret, 24 ← `bavariumtank_body`), `bavariumtank_cannon` (Cannon, 34 ← `bavariumtank_turret`)

### `v0202_car_capstone_bavariumtank_military_01.ee`

`CCar` · chassis `v0202_car_capstone_bavariumtank` · source `archives_win64/game35` @198,854,656 +4,831,456 B · 2 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CCar` `v0202_car_capstone_bavariumtank_military_01`: main_weapon `w602_mediumtank_canon` · secondary (id:00568A74) `w603_mediumtank_mgun` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `secondary (id:00568A74)` | `CBulletWeaponBase` | `w603_mediumtank_mgun` | 603 | 1 | - | - |
| `main_weapon` | `CBulletWeaponBase` | `w602_mediumtank_canon` | 602 | 1 | `warning_light` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w603_mediumtank_mgun` | `fire_position_0` | 2 | 0 | 0.469 | 0.558 | -1.876 |
| `w602_mediumtank_canon` | `fire_position_0` | 2 | 0 | 0 | 0.3739 | -5.8174 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w603_mediumtank_mgun` | `editor/entities/jc_weapons/06_vehicle/w603_mediumtank_mgun/w603_mediumtank_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | 50CalBulletImpact |
| `w602_mediumtank_canon` | `editor/entities/jc_weapons/06_vehicle/w602_mediumtank_canon/w602_mediumtank_canon.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | AAGunImpact |

seats on `CCar` `v0202_car_capstone_bavariumtank_military_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

moving parts on the chassis: `bavariumtank_turret` (Turret, 24 ← `bavariumtank_body`), `bavariumtank_cannon` (Cannon, 34 ← `bavariumtank_turret`)

### `v0202_car_capstone_bavariumtank_rebel_01.ee`

`CCar` · chassis `v0202_car_capstone_bavariumtank` · source `archives_win64/game35` @203,692,032 +4,891,072 B · 2 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CCar` `v0202_car_capstone_bavariumtank_rebel_01`: main_weapon `w602_mediumtank_canon` · secondary (id:00568A74) `w603_mediumtank_mgun` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `secondary (id:00568A74)` | `CBulletWeaponBase` | `w603_mediumtank_mgun` | 603 | 1 | - | - |
| `main_weapon` | `CBulletWeaponBase` | `w602_mediumtank_canon` | 602 | 1 | `warning_light` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w603_mediumtank_mgun` | `fire_position_0` | 2 | 0 | 0.469 | 0.558 | -1.876 |
| `w602_mediumtank_canon` | `fire_position_0` | 2 | 0 | 0 | 0.3739 | -5.8174 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w603_mediumtank_mgun` | `editor/entities/jc_weapons/06_vehicle/w603_mediumtank_mgun/w603_mediumtank_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | 50CalBulletImpact |
| `w602_mediumtank_canon` | `editor/entities/jc_weapons/06_vehicle/w602_mediumtank_canon/w602_mediumtank_canon.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | AAGunImpact |

seats on `CCar` `v0202_car_capstone_bavariumtank_rebel_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

moving parts on the chassis: `bavariumtank_turret` (Turret, 24 ← `bavariumtank_body`), `bavariumtank_cannon` (Cannon, 34 ← `bavariumtank_turret`)

### `v0300_car_kensington_sportsmuscle_signature_preorder.ee`

`CCar` · chassis `v0300_car_kensington_sportsmuscle` · source `archives_win64/game35` @219,678,720 +5,802,496 B · 1 weapon component(s), 1 driver slot(s), 0 gunner slot(s)

slots on `CCar` `v0300_car_kensington_sportsmuscle_signature_preorder`: main_weapon `w618_sportsmuscle_missile` · secondary (id:00568A74) - · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `main_weapon` | `CMissileWeaponBase` | `w618_sportsmuscle_missile` | 618 | 4 | `aim.poi` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w618_sportsmuscle_missile` | `internal.fire_point.2` | 2 | 2 | -0.063 | 1.085 | -1.566 |
| `w618_sportsmuscle_missile` | `internal.fire_point.0` | 2 | 0 | 0.182 | 1.085 | -1.566 |
| `w618_sportsmuscle_missile` | `internal.fire_point.1` | 2 | 1 | 0.058 | 1.085 | -1.566 |
| `w618_sportsmuscle_missile` | `internal.fire_point.3` | 2 | 3 | -0.19 | 1.085 | -1.566 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w618_sportsmuscle_missile` | `editor/entities/jc_weapons/06_vehicle/w618_sportsmuscle_missile/w618_sportsmuscle_missile.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtune` | 0 | - |

seats on `CCar` `v0300_car_kensington_sportsmuscle_signature_preorder`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |

### `v0504_car_solar_technicaljeep_rebel_machinegun.ee`

`CCar` · chassis `v0504_car_solar_technicaljeep` · source `archives_win64/game35` @397,623,296 +6,011,856 B · 1 weapon component(s), 0 driver slot(s), 1 gunner slot(s)

slots on `CCar` `v0504_car_solar_technicaljeep_rebel_machinegun`: main_weapon - · secondary (id:00568A74) - · mounted_weapon `w206_mounted_capstone_m2hm` · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `mounted_weapon` | `CBulletWeaponBase` | `w206_mounted_capstone_m2hm` | 206 | 1 | - | `technicaljeep_rebel_turret`, `technicaljeep_weapon_mount_vertical` |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `FirePosition` | 2 | 0 | 0 | 0.141 | -1.0041 |
| `w206_mounted_capstone_m2hm` | `LeftHandMountedAttach` | 1 | 0 | -0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `vehicle.attach` | 4 | 0 | 0 | 0 | 0 |
| `w206_mounted_capstone_m2hm` | `RightHandMountedAttach` | 1 | 0 | 0.1 | 0.08 | 0.3 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `editor/entities/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_assault_rifle.wtune` | 1011 | 50CalBulletImpact |

- `w206_mounted_capstone_m2hm` (mounted_weapon) is mounted nearest `interaction.seat.gunner1` (seat index `6`, point `point.mounted_weapon`, 1.398 m).

seats on `CCar` `v0504_car_solar_technicaljeep_rebel_machinegun`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.gunner1` | 6 | `S_IDLE_VEHICLE_SPINNING_MOUNTED_WEAPON` | `point.mounted_weapon` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |

moving parts on the chassis: `technicaljeep_rebel_turret` (Turret, 46 ← `technicaljeep_rebel_turret_base`), `technicaljeep_weapon_mount_vertical` (Cannon, 55 ← `technicaljeep_weapon_mount_horizontal`)

### `v0600_car_urga_armoredjeep_military_01.ee`

`CCar` · chassis `v0600_car_urga_armoredjeep` · source `archives_win64/game35` @565,245,952 +5,880,320 B · 1 weapon component(s), 0 driver slot(s), 1 gunner slot(s)

slots on `CCar` `v0600_car_urga_armoredjeep_military_01`: main_weapon - · secondary (id:00568A74) - · mounted_weapon `w206_mounted_capstone_m2hm` · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `mounted_weapon` | `CBulletWeaponBase` | `w206_mounted_capstone_m2hm` | 206 | 1 | - | `armoredjeep_turret_base`, `armoredjeep_weapon_mount_vertical` |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `FirePosition` | 2 | 0 | 0 | 0.141 | -1.0041 |
| `w206_mounted_capstone_m2hm` | `LeftHandMountedAttach` | 1 | 0 | -0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `mount_attach` | 4 | 0 | 0 | 0 | 0 |
| `w206_mounted_capstone_m2hm` | `RightHandMountedAttach` | 1 | 0 | 0.1 | 0.08 | 0.3 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `editor/entities/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_assault_rifle.wtune` | 1011 | 50CalBulletImpact |

- `w206_mounted_capstone_m2hm` (mounted_weapon) is mounted nearest `interaction.seat.gunner1` (seat index `6`, point `point.mounted_weapon`, 1.258 m).

seats on `CCar` `v0600_car_urga_armoredjeep_military_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.passenger2` | 2 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger2` |
| `interaction.seat.gunner1` | 6 | `S_IDLE_VEHICLE_SPINNING_MOUNTED_WEAPON` | `point.mounted_weapon` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |
| `interaction.seat.passenger3` | 3 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger3` |

moving parts on the chassis: `armoredjeep_turret_base` (Turret, 34 ← `armoredjeep_body`), `armoredjeep_weapon_mount_vertical` (Cannon, 66 ← `armoredjeep_weapon_mount_horizontal`)

### `v0600_car_urga_armoredjeep_rebel_01.ee`

`CCar` · chassis `v0600_car_urga_armoredjeep` · source `archives_win64/game35` @571,131,904 +5,992,720 B · 1 weapon component(s), 0 driver slot(s), 1 gunner slot(s)

slots on `CCar` `v0600_car_urga_armoredjeep_rebel_01`: main_weapon - · secondary (id:00568A74) - · mounted_weapon `w206_mounted_capstone_m2hm` · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `mounted_weapon` | `CBulletWeaponBase` | `w206_mounted_capstone_m2hm` | 206 | 1 | - | `armoredjeep_turret_base`, `armoredjeep_weapon_mount_vertical` |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `FirePosition` | 2 | 0 | 0 | 0.141 | -1.0041 |
| `w206_mounted_capstone_m2hm` | `LeftHandMountedAttach` | 1 | 0 | -0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `mount_attach` | 4 | 0 | 0 | 0 | 0 |
| `w206_mounted_capstone_m2hm` | `RightHandMountedAttach` | 1 | 0 | 0.1 | 0.08 | 0.3 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `editor/entities/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_assault_rifle.wtune` | 1011 | 50CalBulletImpact |

- `w206_mounted_capstone_m2hm` (mounted_weapon) is mounted nearest `interaction.seat.gunner1` (seat index `6`, point `point.mounted_weapon`, 1.258 m).

seats on `CCar` `v0600_car_urga_armoredjeep_rebel_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.passenger2` | 2 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger2` |
| `interaction.seat.gunner1` | 6 | `S_IDLE_VEHICLE_SPINNING_MOUNTED_WEAPON` | `point.mounted_weapon` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |
| `interaction.seat.passenger3` | 3 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger3` |

moving parts on the chassis: `armoredjeep_turret_base` (Turret, 34 ← `armoredjeep_body`), `armoredjeep_weapon_mount_vertical` (Cannon, 66 ← `armoredjeep_weapon_mount_horizontal`)

### `v0603_car_urga_smalltank_debug.ee`

`CCar` · chassis `v0603_car_urga_smalltank` · source `archives_win64/game35` @591,261,696 +4,762,656 B · 1 weapon component(s), 1 driver slot(s), 0 gunner slot(s)

slots on `CCar` `v0603_car_urga_smalltank_generated`: main_weapon `w605_smalltank_canon` · secondary (id:00568A74) - · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `main_weapon` | `CBulletWeaponBase` | `w605_smalltank_canon` | 605 | 1 | `warning_light` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w605_smalltank_canon` | `fire_position_0` | 2 | 0 | 0 | 0 | -3.3 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w605_smalltank_canon` | `editor/entities/jc_weapons/06_vehicle/w605_smalltank_canon/w605_smalltank_canon.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | AAGunImpact |

seats on `CCar` `v0603_car_urga_smalltank_generated`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

moving parts on the chassis: `smalltank_turret` (Turret, 10 ← `smalltank_body`), `smalltank_cannon` (Cannon, 32 ← `smalltank_turret`)

### `v0603_car_urga_smalltank_military_01.ee`

`CCar` · chassis `v0603_car_urga_smalltank` · source `archives_win64/game35` @596,029,440 +4,762,192 B · 1 weapon component(s), 1 driver slot(s), 0 gunner slot(s)

slots on `CCar` `v0603_car_urga_smalltank_military_01`: main_weapon `w605_smalltank_canon` · secondary (id:00568A74) - · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `main_weapon` | `CBulletWeaponBase` | `w605_smalltank_canon` | 605 | 1 | `warning_light` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w605_smalltank_canon` | `fire_position_0` | 2 | 0 | 0 | 0 | -3.3 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w605_smalltank_canon` | `editor/entities/jc_weapons/06_vehicle/w605_smalltank_canon/w605_smalltank_canon.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | AAGunImpact |

seats on `CCar` `v0603_car_urga_smalltank_military_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

moving parts on the chassis: `smalltank_turret` (Turret, 10 ← `smalltank_body`), `smalltank_cannon` (Cannon, 32 ← `smalltank_turret`)

### `v0603_car_urga_smalltank_rebel_01.ee`

`CCar` · chassis `v0603_car_urga_smalltank` · source `archives_win64/game35` @600,797,184 +4,851,616 B · 1 weapon component(s), 1 driver slot(s), 0 gunner slot(s)

slots on `CCar` `v0603_car_urga_smalltank_rebel_01`: main_weapon `w605_smalltank_canon` · secondary (id:00568A74) - · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `main_weapon` | `CBulletWeaponBase` | `w605_smalltank_canon` | 605 | 1 | `warning_light` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w605_smalltank_canon` | `fire_position_0` | 2 | 0 | 0 | 0 | -3.3 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w605_smalltank_canon` | `editor/entities/jc_weapons/06_vehicle/w605_smalltank_canon/w605_smalltank_canon.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | AAGunImpact |

seats on `CCar` `v0603_car_urga_smalltank_rebel_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

moving parts on the chassis: `smalltank_turret` (Turret, 10 ← `smalltank_body`), `smalltank_cannon` (Cannon, 32 ← `smalltank_turret`)

### `v0604_car_urga_buggy_signature_preorder.ee`

`CCar` · chassis `v0604_car_urga_buggy` · source `archives_win64/game3` @320,501,760 +5,637,008 B · 1 weapon component(s), 1 driver slot(s), 0 gunner slot(s)

slots on `CCar` `v0604_car_urga_buggy_signature_preorder`: main_weapon `w619_buggy_mgun` · secondary (id:00568A74) - · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `main_weapon` | `CBulletWeaponBase` | `w619_buggy_mgun` | 619 | 2 | `aim.poi` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w619_buggy_mgun` | `internal.fire_point.1` | 2 | 1 | -0.6118 | 1.2224 | -1.748 |
| `w619_buggy_mgun` | `internal.fire_point.0` | 2 | 0 | 0.6118 | 1.2224 | -1.748 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w619_buggy_mgun` | `editor/entities/jc_weapons/06_vehicle/w619_buggy_mgun/w619_buggy_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | 50CalBulletImpact |

seats on `CCar` `v0604_car_urga_buggy_signature_preorder`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |

### `v1200_boat_capstone_heavypatrol_debug.ee`

`CBoat` · chassis `v1200_boat_capstone_heavypatrol` · source `archives_win64/game36` @124,971,008 +4,858,384 B · 2 weapon component(s), 0 driver slot(s), 2 gunner slot(s)

slots on `CBoat` `v1200_boat_capstone_heavypatrol_generated`: main_weapon - · secondary (id:00568A74) - · mounted_weapon `w206_mounted_capstone_m2hm` · mounted_weapon_2 `w206_mounted_capstone_m2hm`

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `mounted_weapon` | `CBulletWeaponBase` | `w206_mounted_capstone_m2hm` | 206 | 1 | - | `heavypatrol_weapon_mount_r_horizontal`, `heavypatrol_weapon_mount_r_vertical` |
| `mounted_weapon_2` | `CBulletWeaponBase` | `w206_mounted_capstone_m2hm` | 206 | 1 | - | `heavypatrol_weapon_mount_l_horizontal`, `heavypatrol_weapon_mount_l_vertical` |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `FirePosition` | 2 | 0 | 0 | 0.141 | -1.0041 |
| `w206_mounted_capstone_m2hm` | `LeftHandMountedAttach` | 1 | 0 | -0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `RightHandMountedAttach` | 1 | 0 | 0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `MountAttach` | 4 | 0 | 0 | 0 | 0 |
| `w206_mounted_capstone_m2hm` | `FirePosition` | 2 | 0 | 0 | 0.141 | -1.0041 |
| `w206_mounted_capstone_m2hm` | `MountAttach` | 4 | 0 | 0 | 0 | 0 |
| `w206_mounted_capstone_m2hm` | `LeftHandMountedAttach` | 1 | 0 | -0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `RightHandMountedAttach` | 1 | 0 | 0.1 | 0.08 | 0.3 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `editor/entities/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_assault_rifle.wtune` | 1011 | 50CalBulletImpact |
| `w206_mounted_capstone_m2hm` | `editor/entities/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_assault_rifle.wtune` | 1011 | 50CalBulletImpact |

- `w206_mounted_capstone_m2hm` (mounted_weapon) is mounted nearest `interaction.seat.gunner2` (seat index `7`, point `point.gunner.right`, 1.052 m).
- `w206_mounted_capstone_m2hm` (mounted_weapon_2) is mounted nearest `interaction.seat.gunner1` (seat index `6`, point `point.gunner.left`, 1.054 m).

seats on `CBoat` `v1200_boat_capstone_heavypatrol_generated`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.gunner1` | 6 | `S_VEHICLE_FIXED_MOUNTED_WEAPON` | `point.gunner.left` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.gunner2` | 7 | `S_VEHICLE_FIXED_MOUNTED_WEAPON` | `point.gunner.right` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |

moving parts on the chassis: `heavypatrol_weapon_mount_l_horizontal` (Cannon, 66 ← `heavypatrol_weapon_mount_l`), `heavypatrol_weapon_mount_r_horizontal` (Cannon, 67 ← `heavypatrol_weapon_mount_r`), `heavypatrol_weapon_mount_l_vertical` (Cannon, 68 ← `heavypatrol_weapon_mount_l_horizontal`), `heavypatrol_weapon_mount_r_vertical` (Cannon, 69 ← `heavypatrol_weapon_mount_r_horizontal`)

### `v1200_boat_capstone_heavypatrol_military_01.ee`

`CBoat` · chassis `v1200_boat_capstone_heavypatrol` · source `archives_win64/game36` @129,835,008 +4,858,544 B · 2 weapon component(s), 0 driver slot(s), 2 gunner slot(s)

slots on `CBoat` `v1200_boat_capstone_heavypatrol_military_01`: main_weapon - · secondary (id:00568A74) - · mounted_weapon `w206_mounted_capstone_m2hm` · mounted_weapon_2 `w206_mounted_capstone_m2hm`

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `mounted_weapon` | `CBulletWeaponBase` | `w206_mounted_capstone_m2hm` | 206 | 1 | - | `heavypatrol_weapon_mount_r_horizontal`, `heavypatrol_weapon_mount_r_vertical` |
| `mounted_weapon_2` | `CBulletWeaponBase` | `w206_mounted_capstone_m2hm` | 206 | 1 | - | `heavypatrol_weapon_mount_l_horizontal`, `heavypatrol_weapon_mount_l_vertical` |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `FirePosition` | 2 | 0 | 0 | 0.141 | -1.0041 |
| `w206_mounted_capstone_m2hm` | `LeftHandMountedAttach` | 1 | 0 | -0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `RightHandMountedAttach` | 1 | 0 | 0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `MountAttach` | 4 | 0 | 0 | 0 | 0 |
| `w206_mounted_capstone_m2hm` | `FirePosition` | 2 | 0 | 0 | 0.141 | -1.0041 |
| `w206_mounted_capstone_m2hm` | `MountAttach` | 4 | 0 | 0 | 0 | 0 |
| `w206_mounted_capstone_m2hm` | `LeftHandMountedAttach` | 1 | 0 | -0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `RightHandMountedAttach` | 1 | 0 | 0.1 | 0.08 | 0.3 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `editor/entities/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_assault_rifle.wtune` | 1011 | 50CalBulletImpact |
| `w206_mounted_capstone_m2hm` | `editor/entities/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_assault_rifle.wtune` | 1011 | 50CalBulletImpact |

- `w206_mounted_capstone_m2hm` (mounted_weapon) is mounted nearest `interaction.seat.gunner2` (seat index `7`, point `point.gunner.right`, 1.052 m).
- `w206_mounted_capstone_m2hm` (mounted_weapon_2) is mounted nearest `interaction.seat.gunner1` (seat index `6`, point `point.gunner.left`, 1.054 m).

seats on `CBoat` `v1200_boat_capstone_heavypatrol_military_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.gunner1` | 6 | `S_VEHICLE_FIXED_MOUNTED_WEAPON` | `point.gunner.left` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.gunner2` | 7 | `S_VEHICLE_FIXED_MOUNTED_WEAPON` | `point.gunner.right` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |

moving parts on the chassis: `heavypatrol_weapon_mount_l_horizontal` (Cannon, 66 ← `heavypatrol_weapon_mount_l`), `heavypatrol_weapon_mount_r_horizontal` (Cannon, 67 ← `heavypatrol_weapon_mount_r`), `heavypatrol_weapon_mount_l_vertical` (Cannon, 68 ← `heavypatrol_weapon_mount_l_horizontal`), `heavypatrol_weapon_mount_r_vertical` (Cannon, 69 ← `heavypatrol_weapon_mount_r_horizontal`)

### `v1200_boat_capstone_heavypatrol_military_01_delivery.ee`

`CBoat` · chassis `v1200_boat_capstone_heavypatrol` · source `archives_win64/game36` @134,699,008 +4,858,752 B · 2 weapon component(s), 0 driver slot(s), 2 gunner slot(s)

slots on `CBoat` `v1200_boat_capstone_heavypatrol_military_01_delivery`: main_weapon - · secondary (id:00568A74) - · mounted_weapon `w206_mounted_capstone_m2hm` · mounted_weapon_2 `w206_mounted_capstone_m2hm`

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `mounted_weapon` | `CBulletWeaponBase` | `w206_mounted_capstone_m2hm` | 206 | 1 | - | `heavypatrol_weapon_mount_r_horizontal`, `heavypatrol_weapon_mount_r_vertical` |
| `mounted_weapon_2` | `CBulletWeaponBase` | `w206_mounted_capstone_m2hm` | 206 | 1 | - | `heavypatrol_weapon_mount_l_horizontal`, `heavypatrol_weapon_mount_l_vertical` |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `FirePosition` | 2 | 0 | 0 | 0.141 | -1.0041 |
| `w206_mounted_capstone_m2hm` | `LeftHandMountedAttach` | 1 | 0 | -0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `RightHandMountedAttach` | 1 | 0 | 0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `MountAttach` | 4 | 0 | 0 | 0 | 0 |
| `w206_mounted_capstone_m2hm` | `FirePosition` | 2 | 0 | 0 | 0.141 | -1.0041 |
| `w206_mounted_capstone_m2hm` | `MountAttach` | 4 | 0 | 0 | 0 | 0 |
| `w206_mounted_capstone_m2hm` | `LeftHandMountedAttach` | 1 | 0 | -0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `RightHandMountedAttach` | 1 | 0 | 0.1 | 0.08 | 0.3 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `editor/entities/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_assault_rifle.wtune` | 1011 | 50CalBulletImpact |
| `w206_mounted_capstone_m2hm` | `editor/entities/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_assault_rifle.wtune` | 1011 | 50CalBulletImpact |

- `w206_mounted_capstone_m2hm` (mounted_weapon) is mounted nearest `interaction.seat.gunner2` (seat index `7`, point `point.gunner.right`, 1.052 m).
- `w206_mounted_capstone_m2hm` (mounted_weapon_2) is mounted nearest `interaction.seat.gunner1` (seat index `6`, point `point.gunner.left`, 1.054 m).

seats on `CBoat` `v1200_boat_capstone_heavypatrol_military_01_delivery`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.gunner1` | 6 | `S_VEHICLE_FIXED_MOUNTED_WEAPON` | `point.gunner.left` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.gunner2` | 7 | `S_VEHICLE_FIXED_MOUNTED_WEAPON` | `point.gunner.right` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |

moving parts on the chassis: `heavypatrol_weapon_mount_l_horizontal` (Cannon, 66 ← `heavypatrol_weapon_mount_l`), `heavypatrol_weapon_mount_r_horizontal` (Cannon, 67 ← `heavypatrol_weapon_mount_r`), `heavypatrol_weapon_mount_l_vertical` (Cannon, 68 ← `heavypatrol_weapon_mount_l_horizontal`), `heavypatrol_weapon_mount_r_vertical` (Cannon, 69 ← `heavypatrol_weapon_mount_r_horizontal`)

### `v1200_boat_capstone_heavypatrol_rebel_01.ee`

`CBoat` · chassis `v1200_boat_capstone_heavypatrol` · source `archives_win64/game36` @139,563,008 +4,881,456 B · 2 weapon component(s), 0 driver slot(s), 2 gunner slot(s)

slots on `CBoat` `v1200_boat_capstone_heavypatrol_rebel_01`: main_weapon - · secondary (id:00568A74) - · mounted_weapon `w206_mounted_capstone_m2hm` · mounted_weapon_2 `w206_mounted_capstone_m2hm`

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `mounted_weapon` | `CBulletWeaponBase` | `w206_mounted_capstone_m2hm` | 206 | 1 | - | `heavypatrol_weapon_mount_r_horizontal`, `heavypatrol_weapon_mount_r_vertical` |
| `mounted_weapon_2` | `CBulletWeaponBase` | `w206_mounted_capstone_m2hm` | 206 | 1 | - | `heavypatrol_weapon_mount_l_horizontal`, `heavypatrol_weapon_mount_l_vertical` |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `FirePosition` | 2 | 0 | 0 | 0.141 | -1.0041 |
| `w206_mounted_capstone_m2hm` | `LeftHandMountedAttach` | 1 | 0 | -0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `RightHandMountedAttach` | 1 | 0 | 0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `MountAttach` | 4 | 0 | 0 | 0 | 0 |
| `w206_mounted_capstone_m2hm` | `FirePosition` | 2 | 0 | 0 | 0.141 | -1.0041 |
| `w206_mounted_capstone_m2hm` | `MountAttach` | 4 | 0 | 0 | 0 | 0 |
| `w206_mounted_capstone_m2hm` | `LeftHandMountedAttach` | 1 | 0 | -0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `RightHandMountedAttach` | 1 | 0 | 0.1 | 0.08 | 0.3 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `editor/entities/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_assault_rifle.wtune` | 1011 | 50CalBulletImpact |
| `w206_mounted_capstone_m2hm` | `editor/entities/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_assault_rifle.wtune` | 1011 | 50CalBulletImpact |

- `w206_mounted_capstone_m2hm` (mounted_weapon) is mounted nearest `interaction.seat.gunner2` (seat index `7`, point `point.gunner.right`, 1.052 m).
- `w206_mounted_capstone_m2hm` (mounted_weapon_2) is mounted nearest `interaction.seat.gunner1` (seat index `6`, point `point.gunner.left`, 1.054 m).

seats on `CBoat` `v1200_boat_capstone_heavypatrol_rebel_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.gunner1` | 6 | `S_VEHICLE_FIXED_MOUNTED_WEAPON` | `point.gunner.left` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.gunner2` | 7 | `S_VEHICLE_FIXED_MOUNTED_WEAPON` | `point.gunner.right` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |

moving parts on the chassis: `heavypatrol_weapon_mount_l_horizontal` (Cannon, 66 ← `heavypatrol_weapon_mount_l`), `heavypatrol_weapon_mount_r_horizontal` (Cannon, 67 ← `heavypatrol_weapon_mount_r`), `heavypatrol_weapon_mount_l_vertical` (Cannon, 68 ← `heavypatrol_weapon_mount_l_horizontal`), `heavypatrol_weapon_mount_r_vertical` (Cannon, 69 ← `heavypatrol_weapon_mount_r_horizontal`)

### `v1200_boat_capstone_heavypatrol_rebel_01_mm210.ee`

`CBoat` · chassis `v1200_boat_capstone_heavypatrol` · source `archives_win64/game36` @144,449,536 +4,881,456 B · 2 weapon component(s), 0 driver slot(s), 2 gunner slot(s)

slots on `CBoat` `v1200_boat_capstone_heavypatrol_rebel_01_mm210`: main_weapon - · secondary (id:00568A74) - · mounted_weapon `w206_mounted_capstone_m2hm` · mounted_weapon_2 `w206_mounted_capstone_m2hm`

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `mounted_weapon` | `CBulletWeaponBase` | `w206_mounted_capstone_m2hm` | 206 | 1 | - | `heavypatrol_weapon_mount_r_horizontal`, `heavypatrol_weapon_mount_r_vertical` |
| `mounted_weapon_2` | `CBulletWeaponBase` | `w206_mounted_capstone_m2hm` | 206 | 1 | - | `heavypatrol_weapon_mount_l_horizontal`, `heavypatrol_weapon_mount_l_vertical` |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `FirePosition` | 2 | 0 | 0 | 0.141 | -1.0041 |
| `w206_mounted_capstone_m2hm` | `LeftHandMountedAttach` | 1 | 0 | -0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `RightHandMountedAttach` | 1 | 0 | 0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `MountAttach` | 4 | 0 | 0 | 0 | 0 |
| `w206_mounted_capstone_m2hm` | `FirePosition` | 2 | 0 | 0 | 0.141 | -1.0041 |
| `w206_mounted_capstone_m2hm` | `MountAttach` | 4 | 0 | 0 | 0 | 0 |
| `w206_mounted_capstone_m2hm` | `LeftHandMountedAttach` | 1 | 0 | -0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `RightHandMountedAttach` | 1 | 0 | 0.1 | 0.08 | 0.3 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `editor/entities/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_assault_rifle.wtune` | 1011 | 50CalBulletImpact |
| `w206_mounted_capstone_m2hm` | `editor/entities/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_assault_rifle.wtune` | 1011 | 50CalBulletImpact |

- `w206_mounted_capstone_m2hm` (mounted_weapon) is mounted nearest `interaction.seat.gunner2` (seat index `7`, point `point.gunner.right`, 1.052 m).
- `w206_mounted_capstone_m2hm` (mounted_weapon_2) is mounted nearest `interaction.seat.gunner1` (seat index `6`, point `point.gunner.left`, 1.054 m).

seats on `CBoat` `v1200_boat_capstone_heavypatrol_rebel_01_mm210`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.gunner1` | 6 | `S_VEHICLE_FIXED_MOUNTED_WEAPON` | `point.gunner.left` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.gunner2` | 7 | `S_VEHICLE_FIXED_MOUNTED_WEAPON` | `point.gunner.right` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |

moving parts on the chassis: `heavypatrol_weapon_mount_l_horizontal` (Cannon, 66 ← `heavypatrol_weapon_mount_l`), `heavypatrol_weapon_mount_r_horizontal` (Cannon, 67 ← `heavypatrol_weapon_mount_r`), `heavypatrol_weapon_mount_l_vertical` (Cannon, 68 ← `heavypatrol_weapon_mount_l_horizontal`), `heavypatrol_weapon_mount_r_vertical` (Cannon, 69 ← `heavypatrol_weapon_mount_r_horizontal`)

### `v1202_boat_capstone_corvette_debug.ee`

`CBoat` · chassis `v1202_boat_capstone_corvette` · source `archives_win64/game36` @149,336,064 +5,796,976 B · 1 weapon component(s), 1 driver slot(s), 0 gunner slot(s)

slots on `CBoat` `v1202_boat_capstone_corvette_generated`: main_weapon `w616_corvette_canon` · secondary (id:00568A74) - · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `main_weapon` | `CBulletWeaponBase` | `w616_corvette_canon` | 616 | 1 | `warning_light` | `corvette_gun`, `corvette_turret` |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w616_corvette_canon` | `fire_position_0` | 4 | 0 | 0 | 0 | 0 |
| `w616_corvette_canon` | `internal.fire_position_0` | 2 | 0 | 0 | 1.2 | -4.7 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w616_corvette_canon` | `editor/entities/jc_weapons/06_vehicle/w616_corvette_canon/w616_corvette_canon.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | AAGunImpact |

seats on `CBoat` `v1202_boat_capstone_corvette_generated`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

moving parts on the chassis: `corvette_turret` (Turret, 24 ← `corvette_body`), `corvette_gun` (Cannon, 51 ← `corvette_turret`)

### `v1202_boat_capstone_corvette_military_01.ee`

`CBoat` · chassis `v1202_boat_capstone_corvette` · source `archives_win64/game36` @155,138,048 +5,797,024 B · 1 weapon component(s), 1 driver slot(s), 0 gunner slot(s)

slots on `CBoat` `v1202_boat_capstone_corvette_military_01`: main_weapon `w616_corvette_canon` · secondary (id:00568A74) - · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `main_weapon` | `CBulletWeaponBase` | `w616_corvette_canon` | 616 | 1 | `warning_light` | `corvette_gun`, `corvette_turret` |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w616_corvette_canon` | `fire_position_0` | 4 | 0 | 0 | 0 | 0 |
| `w616_corvette_canon` | `internal.fire_position_0` | 2 | 0 | 0 | 1.2 | -4.7 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w616_corvette_canon` | `editor/entities/jc_weapons/06_vehicle/w616_corvette_canon/w616_corvette_canon.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | AAGunImpact |

seats on `CBoat` `v1202_boat_capstone_corvette_military_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

moving parts on the chassis: `corvette_turret` (Turret, 24 ← `corvette_body`), `corvette_gun` (Cannon, 51 ← `corvette_turret`)

### `v1202_boat_capstone_corvette_rebel_01.ee`

`CBoat` · chassis `v1202_boat_capstone_corvette` · source `archives_win64/game36` @160,940,032 +5,624,336 B · 1 weapon component(s), 1 driver slot(s), 0 gunner slot(s)

slots on `CBoat` `v1202_boat_capstone_corvette_rebel_01`: main_weapon `w616_corvette_canon` · secondary (id:00568A74) - · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `main_weapon` | `CBulletWeaponBase` | `w616_corvette_canon` | 616 | 1 | `warning_light` | `corvette_gun`, `corvette_turret` |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w616_corvette_canon` | `fire_position_0` | 4 | 0 | 0 | 0 | 0 |
| `w616_corvette_canon` | `internal.fire_position_0` | 2 | 0 | 0 | 1.2 | -4.7 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w616_corvette_canon` | `editor/entities/jc_weapons/06_vehicle/w616_corvette_canon/w616_corvette_canon.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | AAGunImpact |

seats on `CBoat` `v1202_boat_capstone_corvette_rebel_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

moving parts on the chassis: `corvette_turret` (Turret, 24 ← `corvette_body`), `corvette_gun` (Cannon, 51 ← `corvette_turret`)

### `v1401_boat_mugello_racingboat_signature_preorder.ee`

`CBoat` · chassis `v1401_boat_mugello_racingboat` · source `archives_win64/game36` @204,881,920 +4,392,992 B · 1 weapon component(s), 1 driver slot(s), 0 gunner slot(s)

slots on `CBoat` `v1401_boat_mugello_racingboat_signature_preorder`: main_weapon `w620_racingboat_mgun` · secondary (id:00568A74) - · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `main_weapon` | `CBulletWeaponBase` | `w620_racingboat_mgun` | 620 | 2 | `BarrelSpinWeaponComponent`, `aim.poi` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w620_racingboat_mgun` | `internal.fire_point.0` | 2 | 0 | 1.167 | 0.986 | -4.199 |
| `w620_racingboat_mgun` | `internal.fire_point.1` | 2 | 1 | -1.167 | 0.986 | -4.199 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w620_racingboat_mgun` | `editor/entities/jc_weapons/06_vehicle/w620_racingboat_mgun/w620_racingboat_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | MinigunImpact |

seats on `CBoat` `v1401_boat_mugello_racingboat_signature_preorder`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

moving parts on the chassis: `racingboat_minigun_l_barrel_signature` (GatlingGun, 21 ← `racingboat_minigun_l_base_signature`), `racingboat_minigun_r_barrel_signature` (GatlingGun, 22 ← `racingboat_minigun_r_base_signature`)

### `v1704_boat_na_lightpatrol_debug.ee`

`CBoat` · chassis `v1704_boat_na_lightpatrol` · source `archives_win64/game36` @244,484,096 +4,634,368 B · 1 weapon component(s), 0 driver slot(s), 1 gunner slot(s)

slots on `CBoat` `v1704_boat_na_lightpatrol_generated`: main_weapon - · secondary (id:00568A74) - · mounted_weapon `w206_mounted_capstone_m2hm` · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `mounted_weapon` | `CBulletWeaponBase` | `w206_mounted_capstone_m2hm` | 206 | 1 | - | `lightpatrol_weapon_mount_horizontal`, `lightpatrol_weapon_mount_vertical` |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `FirePosition` | 2 | 0 | 0 | 0.141 | -1.0041 |
| `w206_mounted_capstone_m2hm` | `LeftHandMountedAttach` | 1 | 0 | -0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `MountAttach` | 4 | 0 | 0 | 0 | 0 |
| `w206_mounted_capstone_m2hm` | `RightHandMountedAttach` | 1 | 0 | 0.1 | 0.08 | 0.3 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `editor/entities/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_assault_rifle.wtune` | 1011 | 50CalBulletImpact |

- `w206_mounted_capstone_m2hm` (mounted_weapon) is mounted nearest `interaction.seat.gunner1` (seat index `6`, point `point.mounted_weapon`, 1.352 m).

seats on `CBoat` `v1704_boat_na_lightpatrol_generated`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.gunner1` | 6 | `S_VEHICLE_FIXED_MOUNTED_WEAPON`, `S_MOUNTED_WEAPON` | `point.mounted_weapon` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

moving parts on the chassis: `lightpatrol_weapon_mount_horizontal` (Cannon, 29 ← `lightpatrol_weapon_mount`), `lightpatrol_weapon_mount_vertical` (Cannon, 30 ← `lightpatrol_weapon_mount_horizontal`)

### `v1704_boat_na_lightpatrol_military_01.ee`

`CBoat` · chassis `v1704_boat_na_lightpatrol` · source `archives_win64/game36` @249,122,816 +4,634,368 B · 1 weapon component(s), 0 driver slot(s), 1 gunner slot(s)

slots on `CBoat` `v1704_boat_na_lightpatrol_military_01`: main_weapon - · secondary (id:00568A74) - · mounted_weapon `w206_mounted_capstone_m2hm` · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `mounted_weapon` | `CBulletWeaponBase` | `w206_mounted_capstone_m2hm` | 206 | 1 | - | `lightpatrol_weapon_mount_horizontal`, `lightpatrol_weapon_mount_vertical` |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `FirePosition` | 2 | 0 | 0 | 0.141 | -1.0041 |
| `w206_mounted_capstone_m2hm` | `LeftHandMountedAttach` | 1 | 0 | -0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `MountAttach` | 4 | 0 | 0 | 0 | 0 |
| `w206_mounted_capstone_m2hm` | `RightHandMountedAttach` | 1 | 0 | 0.1 | 0.08 | 0.3 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `editor/entities/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_assault_rifle.wtune` | 1011 | 50CalBulletImpact |

- `w206_mounted_capstone_m2hm` (mounted_weapon) is mounted nearest `interaction.seat.gunner1` (seat index `6`, point `point.mounted_weapon`, 1.352 m).

seats on `CBoat` `v1704_boat_na_lightpatrol_military_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.gunner1` | 6 | `S_VEHICLE_FIXED_MOUNTED_WEAPON`, `S_MOUNTED_WEAPON` | `point.mounted_weapon` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

moving parts on the chassis: `lightpatrol_weapon_mount_horizontal` (Cannon, 29 ← `lightpatrol_weapon_mount`), `lightpatrol_weapon_mount_vertical` (Cannon, 30 ← `lightpatrol_weapon_mount_horizontal`)

### `v1704_boat_na_lightpatrol_rebel_01.ee`

`CBoat` · chassis `v1704_boat_na_lightpatrol` · source `archives_win64/game36` @253,761,536 +4,635,232 B · 1 weapon component(s), 0 driver slot(s), 1 gunner slot(s)

slots on `CBoat` `v1704_boat_na_lightpatrol_rebel_01`: main_weapon - · secondary (id:00568A74) - · mounted_weapon `w206_mounted_capstone_m2hm` · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `mounted_weapon` | `CBulletWeaponBase` | `w206_mounted_capstone_m2hm` | 206 | 1 | - | `lightpatrol_weapon_mount_horizontal`, `lightpatrol_weapon_mount_vertical` |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `FirePosition` | 2 | 0 | 0 | 0.141 | -1.0041 |
| `w206_mounted_capstone_m2hm` | `LeftHandMountedAttach` | 1 | 0 | -0.1 | 0.08 | 0.3 |
| `w206_mounted_capstone_m2hm` | `MountAttach` | 4 | 0 | 0 | 0 | 0 |
| `w206_mounted_capstone_m2hm` | `RightHandMountedAttach` | 1 | 0 | 0.1 | 0.08 | 0.3 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | `editor/entities/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_assault_rifle.wtune` | 1011 | 50CalBulletImpact |

- `w206_mounted_capstone_m2hm` (mounted_weapon) is mounted nearest `interaction.seat.gunner1` (seat index `6`, point `point.mounted_weapon`, 1.352 m).

seats on `CBoat` `v1704_boat_na_lightpatrol_rebel_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.gunner1` | 6 | `S_VEHICLE_FIXED_MOUNTED_WEAPON`, `S_MOUNTED_WEAPON` | `point.mounted_weapon` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

moving parts on the chassis: `lightpatrol_weapon_mount_horizontal` (Cannon, 29 ← `lightpatrol_weapon_mount`), `lightpatrol_weapon_mount_vertical` (Cannon, 30 ← `lightpatrol_weapon_mount_horizontal`)

### `v2200_helicopter_capstone_assault_debug.ee`

`CHelicopter` · chassis `v2200_helicopter_capstone_assault` · source `archives_win64/game35` @760,956,928 +5,743,952 B · 2 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CHelicopter` `v2200_helicopter_capstone_assault_base`: main_weapon `w601_helicopter_missile` · secondary (id:00568A74) `w615_helicopter_heavy_missile` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `secondary (id:00568A74)` | `CMissileWeaponBase` | `w615_helicopter_heavy_missile` | 615 | 4 | `warning_light` | - |
| `main_weapon` | `CMissileWeaponBase` | `w601_helicopter_missile` | 601 | 2 | `warning_light` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w615_helicopter_heavy_missile` | `internal_fire_position_1` | 2 | 0 | 0.1639 | 0.2313 | 0.0052 |
| `w615_helicopter_heavy_missile` | `fire_position_r` | 0 | 0 | 2.3101 | 0.796 | -2.6284 |
| `w615_helicopter_heavy_missile` | `internal_fire_position_2` | 2 | 1 | -0.1455 | 0.2343 | 0.0052 |
| `w615_helicopter_heavy_missile` | `fire_position_l` | 0 | 0 | -2.3462 | 0.8445 | -2.6094 |
| `w615_helicopter_heavy_missile` | `internal_fire_position_3` | 2 | 3 | 0.1646 | -0.0903 | 0.0052 |
| `w615_helicopter_heavy_missile` | `internal_fire_position_4` | 2 | 2 | -0.1505 | -0.0903 | 0.0052 |
| `w601_helicopter_missile` | `fire_position_r` | 2 | 1 | 1.534 | 0.964 | -2.554 |
| `w601_helicopter_missile` | `fire_position_l` | 2 | 0 | -1.534 | 0.964 | -2.554 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w615_helicopter_heavy_missile` | `editor/entities/jc_weapons/06_vehicle/w615_helicopter_heavy_missile/w615_helicopter_heavy_missile.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtune` | 0 | - |
| `w601_helicopter_missile` | `editor/entities/jc_weapons/06_vehicle/w601_helicopter_missile/w601_helicopter_missile.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtune` | 0 | - |

seats on `CHelicopter` `v2200_helicopter_capstone_assault_base`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt_hang` | 9 | `S_DRIVER_SIDE_TO_HANG_VEHICLE` | `point.driver.side` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

### `v2200_helicopter_capstone_assault_military_01.ee`

`CHelicopter` · chassis `v2200_helicopter_capstone_assault` · source `archives_win64/game35` @766,705,664 +5,744,432 B · 2 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CHelicopter` `v2200_helicopter_capstone_assault_military_01`: main_weapon `w601_helicopter_missile` · secondary (id:00568A74) `w615_helicopter_heavy_missile` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `secondary (id:00568A74)` | `CMissileWeaponBase` | `w615_helicopter_heavy_missile` | 615 | 4 | `warning_light` | - |
| `main_weapon` | `CMissileWeaponBase` | `w601_helicopter_missile` | 601 | 2 | `warning_light` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w615_helicopter_heavy_missile` | `internal_fire_position_1` | 2 | 0 | 0.1639 | 0.2313 | 0.0052 |
| `w615_helicopter_heavy_missile` | `fire_position_r` | 0 | 0 | 2.3101 | 0.796 | -2.6284 |
| `w615_helicopter_heavy_missile` | `internal_fire_position_2` | 2 | 1 | -0.1455 | 0.2343 | 0.0052 |
| `w615_helicopter_heavy_missile` | `fire_position_l` | 0 | 0 | -2.3462 | 0.8445 | -2.6094 |
| `w615_helicopter_heavy_missile` | `internal_fire_position_3` | 2 | 3 | 0.1646 | -0.0903 | 0.0052 |
| `w615_helicopter_heavy_missile` | `internal_fire_position_4` | 2 | 2 | -0.1505 | -0.0903 | 0.0052 |
| `w601_helicopter_missile` | `fire_position_r` | 2 | 1 | 1.534 | 0.964 | -2.554 |
| `w601_helicopter_missile` | `fire_position_l` | 2 | 0 | -1.534 | 0.964 | -2.554 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w615_helicopter_heavy_missile` | `editor/entities/jc_weapons/06_vehicle/w615_helicopter_heavy_missile/w615_helicopter_heavy_missile.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtune` | 0 | - |
| `w601_helicopter_missile` | `editor/entities/jc_weapons/06_vehicle/w601_helicopter_missile/w601_helicopter_missile.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtune` | 0 | - |

seats on `CHelicopter` `v2200_helicopter_capstone_assault_military_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt_hang` | 9 | `S_DRIVER_SIDE_TO_HANG_VEHICLE` | `point.driver.side` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

### `v2200_helicopter_capstone_assault_rebel_01.ee`

`CHelicopter` · chassis `v2200_helicopter_capstone_assault` · source `archives_win64/game35` @772,454,400 +5,792,928 B · 2 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CHelicopter` `v2200_helicopter_capstone_assault_rebel_01`: main_weapon `w601_helicopter_missile` · secondary (id:00568A74) `w615_helicopter_heavy_missile` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `secondary (id:00568A74)` | `CMissileWeaponBase` | `w615_helicopter_heavy_missile` | 615 | 4 | `warning_light` | - |
| `main_weapon` | `CMissileWeaponBase` | `w601_helicopter_missile` | 601 | 2 | `warning_light` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w615_helicopter_heavy_missile` | `internal_fire_position_1` | 2 | 0 | 0.1639 | 0.2313 | 0.0052 |
| `w615_helicopter_heavy_missile` | `fire_position_r` | 0 | 0 | 2.3101 | 0.796 | -2.6284 |
| `w615_helicopter_heavy_missile` | `internal_fire_position_2` | 2 | 1 | -0.1455 | 0.2343 | 0.0052 |
| `w615_helicopter_heavy_missile` | `fire_position_l` | 0 | 0 | -2.3462 | 0.8445 | -2.6094 |
| `w615_helicopter_heavy_missile` | `internal_fire_position_3` | 2 | 3 | 0.1646 | -0.0903 | 0.0052 |
| `w615_helicopter_heavy_missile` | `internal_fire_position_4` | 2 | 2 | -0.1505 | -0.0903 | 0.0052 |
| `w601_helicopter_missile` | `fire_position_r` | 2 | 1 | 1.534 | 0.964 | -2.554 |
| `w601_helicopter_missile` | `fire_position_l` | 2 | 0 | -1.534 | 0.964 | -2.554 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w615_helicopter_heavy_missile` | `editor/entities/jc_weapons/06_vehicle/w615_helicopter_heavy_missile/w615_helicopter_heavy_missile.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtune` | 0 | - |
| `w601_helicopter_missile` | `editor/entities/jc_weapons/06_vehicle/w601_helicopter_missile/w601_helicopter_missile.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtune` | 0 | - |

seats on `CHelicopter` `v2200_helicopter_capstone_assault_rebel_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt_hang` | 9 | `S_DRIVER_SIDE_TO_HANG_VEHICLE` | `point.driver.side` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

### `v2601_helicopter_urga_heavyassault_debug.ee`

`CHelicopter` · chassis `v2601_helicopter_urga_heavyassault` · source `archives_win64/game35` @794,128,384 +6,741,392 B · 2 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CHelicopter` `v2601_helicopter_urga_heavyassault_generated`: main_weapon `w607_heavyhelicopter_mgun` · secondary (id:00568A74) `w606_heavyhelicopter_missile` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `main_weapon` | `CBulletWeaponBase` | `w607_heavyhelicopter_mgun` | 607 | 0 | `BarrelSpinWeaponComponent` | - |
| `secondary (id:00568A74)` | `CMissileWeaponBase` | `w606_heavyhelicopter_missile` | 606 | 4 | `warning_light` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w607_heavyhelicopter_mgun` | `fire.point2` | 0 | 0 | -2.09 | 0.89 | -2.28 |
| `w607_heavyhelicopter_mgun` | `fire.point1` | 0 | 0 | 2.09 | 0.89 | -2.28 |
| `w606_heavyhelicopter_missile` | `internal_fire_position_1` | 2 | 0 | 0.1639 | 0.2313 | 0.0052 |
| `w606_heavyhelicopter_missile` | `fire.point1` | 0 | 0 | 3.65 | 0.86 | -1.33 |
| `w606_heavyhelicopter_missile` | `internal_fire_position_2` | 2 | 1 | -0.1455 | 0.2343 | 0.0052 |
| `w606_heavyhelicopter_missile` | `internal_fire_position_3` | 2 | 3 | 0.1646 | -0.0903 | 0.0052 |
| `w606_heavyhelicopter_missile` | `internal_fire_position_4` | 2 | 2 | -0.1505 | -0.0903 | 0.0052 |
| `w606_heavyhelicopter_missile` | `fire.point2` | 0 | 0 | -3.65 | 0.86 | -1.33 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w607_heavyhelicopter_mgun` | `editor/entities/jc_weapons/06_vehicle/w607_heavyhelicopter_mgun/w607_heavyheli_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | MinigunImpact |
| `w606_heavyhelicopter_missile` | `editor/entities/jc_weapons/06_vehicle/w606_heavyhelicopter_missile/w606_heavyheli_missile.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtune` | 0 | - |

seats on `CHelicopter` `v2601_helicopter_urga_heavyassault_generated`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt_hang` | 9 | `S_DRIVER_SIDE_TO_HANG_VEHICLE` | `point.driver.side` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |

### `v2601_helicopter_urga_heavyassault_military_01.ee`

`CHelicopter` · chassis `v2601_helicopter_urga_heavyassault` · source `archives_win64/game35` @800,874,496 +6,741,344 B · 2 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CHelicopter` `v2601_helicopter_urga_heavyassault_military_01`: main_weapon `w607_heavyhelicopter_mgun` · secondary (id:00568A74) `w606_heavyhelicopter_missile` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `main_weapon` | `CBulletWeaponBase` | `w607_heavyhelicopter_mgun` | 607 | 0 | `BarrelSpinWeaponComponent` | - |
| `secondary (id:00568A74)` | `CMissileWeaponBase` | `w606_heavyhelicopter_missile` | 606 | 4 | `warning_light` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w607_heavyhelicopter_mgun` | `fire.point2` | 0 | 0 | -2.09 | 0.89 | -2.28 |
| `w607_heavyhelicopter_mgun` | `fire.point1` | 0 | 0 | 2.09 | 0.89 | -2.28 |
| `w606_heavyhelicopter_missile` | `internal_fire_position_1` | 2 | 0 | 0.1639 | 0.2313 | 0.0052 |
| `w606_heavyhelicopter_missile` | `fire.point1` | 0 | 0 | 3.65 | 0.86 | -1.33 |
| `w606_heavyhelicopter_missile` | `internal_fire_position_2` | 2 | 1 | -0.1455 | 0.2343 | 0.0052 |
| `w606_heavyhelicopter_missile` | `internal_fire_position_3` | 2 | 3 | 0.1646 | -0.0903 | 0.0052 |
| `w606_heavyhelicopter_missile` | `internal_fire_position_4` | 2 | 2 | -0.1505 | -0.0903 | 0.0052 |
| `w606_heavyhelicopter_missile` | `fire.point2` | 0 | 0 | -3.65 | 0.86 | -1.33 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w607_heavyhelicopter_mgun` | `editor/entities/jc_weapons/06_vehicle/w607_heavyhelicopter_mgun/w607_heavyheli_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | MinigunImpact |
| `w606_heavyhelicopter_missile` | `editor/entities/jc_weapons/06_vehicle/w606_heavyhelicopter_missile/w606_heavyheli_missile.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtune` | 0 | - |

seats on `CHelicopter` `v2601_helicopter_urga_heavyassault_military_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt_hang` | 9 | `S_DRIVER_SIDE_TO_HANG_VEHICLE` | `point.driver.side` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |

### `v2601_helicopter_urga_heavyassault_rebel_01.ee`

`CHelicopter` · chassis `v2601_helicopter_urga_heavyassault` · source `archives_win64/game35` @807,620,608 +6,786,512 B · 2 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CHelicopter` `v2601_helicopter_urga_heavyassault_rebel_01`: main_weapon `w607_heavyhelicopter_mgun` · secondary (id:00568A74) `w606_heavyhelicopter_missile` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `main_weapon` | `CBulletWeaponBase` | `w607_heavyhelicopter_mgun` | 607 | 0 | `BarrelSpinWeaponComponent` | - |
| `secondary (id:00568A74)` | `CMissileWeaponBase` | `w606_heavyhelicopter_missile` | 606 | 4 | `warning_light` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w607_heavyhelicopter_mgun` | `fire.point2` | 0 | 0 | -2.09 | 0.89 | -2.28 |
| `w607_heavyhelicopter_mgun` | `fire.point1` | 0 | 0 | 2.09 | 0.89 | -2.28 |
| `w606_heavyhelicopter_missile` | `internal_fire_position_1` | 2 | 0 | 0.1639 | 0.2313 | 0.0052 |
| `w606_heavyhelicopter_missile` | `fire.point1` | 0 | 0 | 3.65 | 0.86 | -1.33 |
| `w606_heavyhelicopter_missile` | `internal_fire_position_2` | 2 | 1 | -0.1455 | 0.2343 | 0.0052 |
| `w606_heavyhelicopter_missile` | `internal_fire_position_3` | 2 | 3 | 0.1646 | -0.0903 | 0.0052 |
| `w606_heavyhelicopter_missile` | `internal_fire_position_4` | 2 | 2 | -0.1505 | -0.0903 | 0.0052 |
| `w606_heavyhelicopter_missile` | `fire.point2` | 0 | 0 | -3.65 | 0.86 | -1.33 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w607_heavyhelicopter_mgun` | `editor/entities/jc_weapons/06_vehicle/w607_heavyhelicopter_mgun/w607_heavyheli_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | MinigunImpact |
| `w606_heavyhelicopter_missile` | `editor/entities/jc_weapons/06_vehicle/w606_heavyhelicopter_missile/w606_heavyheli_missile.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtune` | 0 | - |

seats on `CHelicopter` `v2601_helicopter_urga_heavyassault_rebel_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt_hang` | 9 | `S_DRIVER_SIDE_TO_HANG_VEHICLE` | `point.driver.side` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |

### `v2602_helicopter_urga_lightassault_debug.ee`

`CHelicopter` · chassis `v2602_helicopter_urga_lightassault` · source `archives_win64/game35` @814,411,776 +6,314,432 B · 1 weapon component(s), 1 driver slot(s), 0 gunner slot(s)

slots on `CHelicopter` `v2602_helicopter_urga_lightassault_generated`: main_weapon `w604_helicopter_mgun` · secondary (id:00568A74) - · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `main_weapon` | `CBulletWeaponBase` | `w604_helicopter_mgun` | 604 | 1 | `BarrelSpinWeaponComponent` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w604_helicopter_mgun` | `internal.fire.point` | 2 | 0 | 0 | -0.44 | -1.3 |
| `w604_helicopter_mgun` | `weapon.point.right` | 0 | 0 | 2.18 | 1.11 | 1.09 |
| `w604_helicopter_mgun` | `weapon.point.left` | 0 | 0 | -2.18 | 1.11 | 1.09 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w604_helicopter_mgun` | `editor/entities/jc_weapons/06_vehicle/w604_helicopter_mgun/w604_helicopter_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | MinigunImpact |

seats on `CHelicopter` `v2602_helicopter_urga_lightassault_generated`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt_hang` | 9 | `S_DRIVER_SIDE_TO_HANG_VEHICLE` | `point.driver.side` |
| `interaction.seat.passenger2` | 2 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger2` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |
| `interaction.seat.passenger3` | 3 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger3` |

moving parts on the chassis: `lightassault_minigun_mount_l_vertical` (Cannon, 30 ← `lightassault_minigun_mount_l_base`), `lightassault_minigun_mount_r_vertical` (Cannon, 31 ← `lightassault_minigun_mount_r_base`), `lightassault_minigun_l_barrel` (GatlingGun, 42 ← `lightassault_minigun_l_base`), `lightassault_minigun_r_barrel` (GatlingGun, 43 ← `lightassault_minigun_r_base`)

### `v2602_helicopter_urga_lightassault_military_01.ee`

`CHelicopter` · chassis `v2602_helicopter_urga_lightassault` · source `archives_win64/game35` @820,731,904 +6,314,848 B · 1 weapon component(s), 1 driver slot(s), 0 gunner slot(s)

slots on `CHelicopter` `v2602_helicopter_urga_lightassault_military_01`: main_weapon `w604_helicopter_mgun` · secondary (id:00568A74) - · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `main_weapon` | `CBulletWeaponBase` | `w604_helicopter_mgun` | 604 | 1 | `BarrelSpinWeaponComponent` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w604_helicopter_mgun` | `internal.fire.point` | 2 | 0 | 0 | -0.44 | -1.3 |
| `w604_helicopter_mgun` | `weapon.point.right` | 0 | 0 | 2.18 | 1.11 | 1.09 |
| `w604_helicopter_mgun` | `weapon.point.left` | 0 | 0 | -2.18 | 1.11 | 1.09 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w604_helicopter_mgun` | `editor/entities/jc_weapons/06_vehicle/w604_helicopter_mgun/w604_helicopter_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | MinigunImpact |

seats on `CHelicopter` `v2602_helicopter_urga_lightassault_military_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt_hang` | 9 | `S_DRIVER_SIDE_TO_HANG_VEHICLE` | `point.driver.side` |
| `interaction.seat.passenger2` | 2 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger2` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |
| `interaction.seat.passenger3` | 3 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger3` |

moving parts on the chassis: `lightassault_minigun_mount_l_vertical` (Cannon, 30 ← `lightassault_minigun_mount_l_base`), `lightassault_minigun_mount_r_vertical` (Cannon, 31 ← `lightassault_minigun_mount_r_base`), `lightassault_minigun_l_barrel` (GatlingGun, 42 ← `lightassault_minigun_l_base`), `lightassault_minigun_r_barrel` (GatlingGun, 43 ← `lightassault_minigun_r_base`)

### `v2602_helicopter_urga_lightassault_rebel_01.ee`

`CHelicopter` · chassis `v2602_helicopter_urga_lightassault` · source `archives_win64/game35` @827,052,032 +6,344,144 B · 1 weapon component(s), 1 driver slot(s), 0 gunner slot(s)

slots on `CHelicopter` `v2602_helicopter_urga_lightassault_rebel_01`: main_weapon `w604_helicopter_mgun` · secondary (id:00568A74) - · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `main_weapon` | `CBulletWeaponBase` | `w604_helicopter_mgun` | 604 | 1 | `BarrelSpinWeaponComponent` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w604_helicopter_mgun` | `internal.fire.point` | 2 | 0 | 0 | -0.44 | -1.3 |
| `w604_helicopter_mgun` | `weapon.point.right` | 0 | 0 | 2.18 | 1.11 | 1.09 |
| `w604_helicopter_mgun` | `weapon.point.left` | 0 | 0 | -2.18 | 1.11 | 1.09 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w604_helicopter_mgun` | `editor/entities/jc_weapons/06_vehicle/w604_helicopter_mgun/w604_helicopter_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | MinigunImpact |

seats on `CHelicopter` `v2602_helicopter_urga_lightassault_rebel_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt_hang` | 9 | `S_DRIVER_SIDE_TO_HANG_VEHICLE` | `point.driver.side` |
| `interaction.seat.passenger2` | 2 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger2` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |
| `interaction.seat.passenger3` | 3 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger3` |

moving parts on the chassis: `lightassault_minigun_mount_l_vertical` (Cannon, 30 ← `lightassault_minigun_mount_l_base`), `lightassault_minigun_mount_r_vertical` (Cannon, 31 ← `lightassault_minigun_mount_r_base`), `lightassault_minigun_l_barrel` (GatlingGun, 42 ← `lightassault_minigun_l_base`), `lightassault_minigun_r_barrel` (GatlingGun, 43 ← `lightassault_minigun_r_base`)

### `v2604_helicopter_urga_advancedassault_debug.ee`

`CHelicopter` · chassis `v2604_helicopter_urga_advancedassault` · source `archives_win64/game35` @849,199,104 +6,188,256 B · 2 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CHelicopter` `v2604_helicopter_urga_advancedassault_generated`: main_weapon `w622_advancedhelicopter_mgun` · secondary (id:00568A74) `w621_advancedhelicopter_missile` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `secondary (id:00568A74)` | `CMissileWeaponBase` | `w621_advancedhelicopter_missile` | 621 | 4 | `warning_light` | - |
| `main_weapon` | `CBulletWeaponBase` | `w622_advancedhelicopter_mgun` | 622 | 1 | `BarrelSpinWeaponComponent` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w621_advancedhelicopter_missile` | `fire_position_4` | 0 | 0 | 4.1797 | 1.0753 | -1.3047 |
| `w621_advancedhelicopter_missile` | `internal_fire_position_4` | 2 | 2 | -0.1504 | -0.0902 | 0.0054 |
| `w621_advancedhelicopter_missile` | `fire_position_2` | 0 | 0 | 2.9453 | 1.1497 | -1.3237 |
| `w621_advancedhelicopter_missile` | `fire_position_3` | 0 | 0 | -4.189 | 1.0887 | -1.3237 |
| `w621_advancedhelicopter_missile` | `internal_fire_position_3` | 2 | 3 | 0.1646 | -0.0902 | 0.0054 |
| `w621_advancedhelicopter_missile` | `internal_fire_position_2` | 2 | 1 | -0.1455 | 0.2343 | 0.0054 |
| `w621_advancedhelicopter_missile` | `fire_position_1` | 0 | 0 | -2.936 | 1.1372 | -1.3047 |
| `w621_advancedhelicopter_missile` | `internal_fire_position_1` | 2 | 0 | 0.1641 | 0.2312 | 0.0054 |
| `w622_advancedhelicopter_mgun` | `internal.fire.point` | 2 | 0 | 0 | -0.2 | -2.9 |
| `w622_advancedhelicopter_mgun` | `weapon.point.left` | 0 | 0 | -1.201 | 1.419 | 0.014 |
| `w622_advancedhelicopter_mgun` | `weapon.point.right` | 0 | 0 | 1.201 | 1.419 | 0.014 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w621_advancedhelicopter_missile` | `editor/entities/jc_weapons/06_vehicle/w621_advancedhelicopter_missile/w621_advancedhelicopter_missile.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtune` | 0 | - |
| `w622_advancedhelicopter_mgun` | `editor/entities/jc_weapons/06_vehicle/w622_advancedhelicopter_mgun/w622_advancedhelicopter_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | MinigunImpact |

seats on `CHelicopter` `v2604_helicopter_urga_advancedassault_generated`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt_hang` | 9 | `S_DRIVER_SIDE_TO_HANG_VEHICLE` | `point.driver.side` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |

moving parts on the chassis: `advancedassault_gatling_l_mount` (Cannon, 7 ← `advancedassault_body`), `advancedassault_gatling_r_mount` (Cannon, 8 ← `advancedassault_body`), `advancedassault_gatling_l_barrels` (GatlingGun, 39 ← `advancedassault_gatling_l_base`), `advancedassault_gatling_r_barrels` (GatlingGun, 40 ← `advancedassault_gatling_r_base`)

### `v2604_helicopter_urga_advancedassault_military_01.ee`

`CHelicopter` · chassis `v2604_helicopter_urga_advancedassault` · source `archives_win64/game35` @855,392,256 +6,188,448 B · 2 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CHelicopter` `v2604_helicopter_urga_advancedassault_military_01`: main_weapon `w622_advancedhelicopter_mgun` · secondary (id:00568A74) `w621_advancedhelicopter_missile` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `secondary (id:00568A74)` | `CMissileWeaponBase` | `w621_advancedhelicopter_missile` | 621 | 4 | `warning_light` | - |
| `main_weapon` | `CBulletWeaponBase` | `w622_advancedhelicopter_mgun` | 622 | 1 | `BarrelSpinWeaponComponent` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w621_advancedhelicopter_missile` | `fire_position_4` | 0 | 0 | 4.1797 | 1.0753 | -1.3047 |
| `w621_advancedhelicopter_missile` | `internal_fire_position_4` | 2 | 2 | -0.1504 | -0.0902 | 0.0054 |
| `w621_advancedhelicopter_missile` | `fire_position_2` | 0 | 0 | 2.9453 | 1.1497 | -1.3237 |
| `w621_advancedhelicopter_missile` | `fire_position_3` | 0 | 0 | -4.189 | 1.0887 | -1.3237 |
| `w621_advancedhelicopter_missile` | `internal_fire_position_3` | 2 | 3 | 0.1646 | -0.0902 | 0.0054 |
| `w621_advancedhelicopter_missile` | `internal_fire_position_2` | 2 | 1 | -0.1455 | 0.2343 | 0.0054 |
| `w621_advancedhelicopter_missile` | `fire_position_1` | 0 | 0 | -2.936 | 1.1372 | -1.3047 |
| `w621_advancedhelicopter_missile` | `internal_fire_position_1` | 2 | 0 | 0.1641 | 0.2312 | 0.0054 |
| `w622_advancedhelicopter_mgun` | `internal.fire.point` | 2 | 0 | 0 | -0.2 | -2.9 |
| `w622_advancedhelicopter_mgun` | `weapon.point.left` | 0 | 0 | -1.201 | 1.419 | 0.014 |
| `w622_advancedhelicopter_mgun` | `weapon.point.right` | 0 | 0 | 1.201 | 1.419 | 0.014 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w621_advancedhelicopter_missile` | `editor/entities/jc_weapons/06_vehicle/w621_advancedhelicopter_missile/w621_advancedhelicopter_missile.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtune` | 0 | - |
| `w622_advancedhelicopter_mgun` | `editor/entities/jc_weapons/06_vehicle/w622_advancedhelicopter_mgun/w622_advancedhelicopter_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | MinigunImpact |

seats on `CHelicopter` `v2604_helicopter_urga_advancedassault_military_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt_hang` | 9 | `S_DRIVER_SIDE_TO_HANG_VEHICLE` | `point.driver.side` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |

moving parts on the chassis: `advancedassault_gatling_l_mount` (Cannon, 7 ← `advancedassault_body`), `advancedassault_gatling_r_mount` (Cannon, 8 ← `advancedassault_body`), `advancedassault_gatling_l_barrels` (GatlingGun, 39 ← `advancedassault_gatling_l_base`), `advancedassault_gatling_r_barrels` (GatlingGun, 40 ← `advancedassault_gatling_r_base`)

### `v2604_helicopter_urga_advancedassault_rebel_01.ee`

`CHelicopter` · chassis `v2604_helicopter_urga_advancedassault` · source `archives_win64/game35` @861,585,408 +6,164,752 B · 2 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CHelicopter` `v2604_helicopter_urga_advancedassault_rebel_01`: main_weapon `w622_advancedhelicopter_mgun` · secondary (id:00568A74) `w621_advancedhelicopter_missile` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `secondary (id:00568A74)` | `CMissileWeaponBase` | `w621_advancedhelicopter_missile` | 621 | 4 | `warning_light` | - |
| `main_weapon` | `CBulletWeaponBase` | `w622_advancedhelicopter_mgun` | 622 | 1 | `BarrelSpinWeaponComponent` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w621_advancedhelicopter_missile` | `fire_position_4` | 0 | 0 | 4.1797 | 1.0753 | -1.3047 |
| `w621_advancedhelicopter_missile` | `internal_fire_position_4` | 2 | 2 | -0.1504 | -0.0902 | 0.0054 |
| `w621_advancedhelicopter_missile` | `fire_position_2` | 0 | 0 | 2.9453 | 1.1497 | -1.3237 |
| `w621_advancedhelicopter_missile` | `fire_position_3` | 0 | 0 | -4.189 | 1.0887 | -1.3237 |
| `w621_advancedhelicopter_missile` | `internal_fire_position_3` | 2 | 3 | 0.1646 | -0.0902 | 0.0054 |
| `w621_advancedhelicopter_missile` | `internal_fire_position_2` | 2 | 1 | -0.1455 | 0.2343 | 0.0054 |
| `w621_advancedhelicopter_missile` | `fire_position_1` | 0 | 0 | -2.936 | 1.1372 | -1.3047 |
| `w621_advancedhelicopter_missile` | `internal_fire_position_1` | 2 | 0 | 0.1641 | 0.2312 | 0.0054 |
| `w622_advancedhelicopter_mgun` | `internal.fire.point` | 2 | 0 | 0 | -0.2 | -2.9 |
| `w622_advancedhelicopter_mgun` | `weapon.point.left` | 0 | 0 | -1.201 | 1.419 | 0.014 |
| `w622_advancedhelicopter_mgun` | `weapon.point.right` | 0 | 0 | 1.201 | 1.419 | 0.014 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w621_advancedhelicopter_missile` | `editor/entities/jc_weapons/06_vehicle/w621_advancedhelicopter_missile/w621_advancedhelicopter_missile.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtune` | 0 | - |
| `w622_advancedhelicopter_mgun` | `editor/entities/jc_weapons/06_vehicle/w622_advancedhelicopter_mgun/w622_advancedhelicopter_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | MinigunImpact |

seats on `CHelicopter` `v2604_helicopter_urga_advancedassault_rebel_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt_hang` | 9 | `S_DRIVER_SIDE_TO_HANG_VEHICLE` | `point.driver.side` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |

moving parts on the chassis: `advancedassault_gatling_l_mount` (Cannon, 7 ← `advancedassault_body`), `advancedassault_gatling_r_mount` (Cannon, 8 ← `advancedassault_body`), `advancedassault_gatling_l_barrels` (GatlingGun, 39 ← `advancedassault_gatling_l_base`), `advancedassault_gatling_r_barrels` (GatlingGun, 40 ← `advancedassault_gatling_r_base`)

### `v2604_helicopter_urga_advancedassault_signature_shielded.ee`

`CHelicopter` · chassis `v2604_helicopter_urga_advancedassault` · source `archives_win64/game35` @867,756,032 +6,189,616 B · 2 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CHelicopter` `v2604_helicopter_urga_advancedassault_signature_shielded`: main_weapon `w622_advancedhelicopter_mgun` · secondary (id:00568A74) `w621_advancedhelicopter_missile` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `secondary (id:00568A74)` | `CMissileWeaponBase` | `w621_advancedhelicopter_missile` | 621 | 4 | `warning_light` | - |
| `main_weapon` | `CBulletWeaponBase` | `w622_advancedhelicopter_mgun` | 622 | 1 | `BarrelSpinWeaponComponent` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w621_advancedhelicopter_missile` | `fire_position_4` | 0 | 0 | 4.1797 | 1.0753 | -1.3047 |
| `w621_advancedhelicopter_missile` | `internal_fire_position_4` | 2 | 2 | -0.1504 | -0.0902 | 0.0054 |
| `w621_advancedhelicopter_missile` | `fire_position_2` | 0 | 0 | 2.9453 | 1.1497 | -1.3237 |
| `w621_advancedhelicopter_missile` | `fire_position_3` | 0 | 0 | -4.189 | 1.0887 | -1.3237 |
| `w621_advancedhelicopter_missile` | `internal_fire_position_3` | 2 | 3 | 0.1646 | -0.0902 | 0.0054 |
| `w621_advancedhelicopter_missile` | `internal_fire_position_2` | 2 | 1 | -0.1455 | 0.2343 | 0.0054 |
| `w621_advancedhelicopter_missile` | `fire_position_1` | 0 | 0 | -2.936 | 1.1372 | -1.3047 |
| `w621_advancedhelicopter_missile` | `internal_fire_position_1` | 2 | 0 | 0.1641 | 0.2312 | 0.0054 |
| `w622_advancedhelicopter_mgun` | `internal.fire.point` | 2 | 0 | 0 | -0.2 | -2.9 |
| `w622_advancedhelicopter_mgun` | `weapon.point.left` | 0 | 0 | -1.201 | 1.419 | 0.014 |
| `w622_advancedhelicopter_mgun` | `weapon.point.right` | 0 | 0 | 1.201 | 1.419 | 0.014 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w621_advancedhelicopter_missile` | `editor/entities/jc_weapons/06_vehicle/w621_advancedhelicopter_missile/w621_advancedhelicopter_missile.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtune` | 0 | - |
| `w622_advancedhelicopter_mgun` | `editor/entities/jc_weapons/06_vehicle/w622_advancedhelicopter_mgun/w622_advancedhelicopter_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | MinigunImpact |

seats on `CHelicopter` `v2604_helicopter_urga_advancedassault_signature_shielded`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt_hang` | 9 | `S_DRIVER_SIDE_TO_HANG_VEHICLE` | `point.driver.side` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |

moving parts on the chassis: `advancedassault_gatling_l_mount` (Cannon, 7 ← `advancedassault_body`), `advancedassault_gatling_r_mount` (Cannon, 8 ← `advancedassault_body`), `advancedassault_gatling_l_barrels` (GatlingGun, 39 ← `advancedassault_gatling_l_base`), `advancedassault_gatling_r_barrels` (GatlingGun, 40 ← `advancedassault_gatling_r_base`)

### `v2604_helicopter_urga_advancedassault_signature_shielded_di_ravello.ee`

`CHelicopter` · chassis `v2604_helicopter_urga_advancedassault` · source `archives_win64/game35` @873,951,232 +6,281,904 B · 2 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CHelicopter` `v2604_helicopter_urga_advancedassault_signature_shielded_di_ravello`: main_weapon `w622_advancedhelicopter_mgun` · secondary (id:00568A74) `w621_advancedhelicopter_missile` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `secondary (id:00568A74)` | `CMissileWeaponBase` | `w621_advancedhelicopter_missile` | 621 | 4 | `warning_light` | - |
| `main_weapon` | `CBulletWeaponBase` | `w622_advancedhelicopter_mgun` | 622 | 1 | `BarrelSpinWeaponComponent` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w621_advancedhelicopter_missile` | `fire_position_4` | 0 | 0 | -4.189 | 1.089 | -1.324 |
| `w621_advancedhelicopter_missile` | `internal_fire_position_4` | 2 | 2 | -0.1504 | -0.0902 | 0.0054 |
| `w621_advancedhelicopter_missile` | `fire_position_2` | 0 | 0 | 2.945 | 1.15 | -1.324 |
| `w621_advancedhelicopter_missile` | `fire_position_3` | 0 | 0 | -4.189 | 1.089 | -1.324 |
| `w621_advancedhelicopter_missile` | `internal_fire_position_3` | 2 | 3 | 0.1646 | -0.0902 | 0.0054 |
| `w621_advancedhelicopter_missile` | `internal_fire_position_2` | 2 | 1 | -0.1455 | 0.2343 | 0.0054 |
| `w621_advancedhelicopter_missile` | `fire_position_1` | 0 | 0 | -2.936 | 1.137 | -1.305 |
| `w621_advancedhelicopter_missile` | `internal_fire_position_1` | 2 | 0 | 0.1641 | 0.2312 | 0.0054 |
| `w622_advancedhelicopter_mgun` | `internal.fire.point` | 2 | 0 | 0 | -0.2 | -2.9 |
| `w622_advancedhelicopter_mgun` | `weapon.point.left` | 0 | 0 | -1.201 | 1.419 | 0.014 |
| `w622_advancedhelicopter_mgun` | `weapon.point.right` | 0 | 0 | 1.201 | 1.419 | 0.014 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w621_advancedhelicopter_missile` | `editor/entities/jc_prototype/bossfight/prototype_helicopter_missiles.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_lockon_missile.wtune` | 0 | - |
| `w622_advancedhelicopter_mgun` | `editor/entities/jc_prototype/bossfight/prototype_heavyheli_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | MinigunImpact |

seats on `CHelicopter` `v2604_helicopter_urga_advancedassault_signature_shielded_di_ravello`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt_hang` | 9 | `S_DRIVER_SIDE_TO_HANG_VEHICLE` | `point.driver.side` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |

moving parts on the chassis: `advancedassault_gatling_l_mount` (Cannon, 7 ← `advancedassault_body`), `advancedassault_gatling_r_mount` (Cannon, 8 ← `advancedassault_body`), `advancedassault_gatling_l_barrels` (GatlingGun, 39 ← `advancedassault_gatling_l_base`), `advancedassault_gatling_r_barrels` (GatlingGun, 40 ← `advancedassault_gatling_r_base`)

### `v4202_plane_capstone_fighterjet_debug.ee`

`CAirPlane` · chassis `v4202_plane_capstone_fighterjet` · source `archives_win64/game35` @880,238,592 +6,332,816 B · 3 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CAirPlane` `v4202_plane_capstone_fighterjet_generated`: main_weapon `w610_fighterjet_mgun` · secondary (id:00568A74) `w609_fighterjet_missile_air_lockon` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| *unbound* | `CMissileWeaponBase` | `w608_fighterjet_missile` | 608 | 2 | - | - |
| `main_weapon` | `CBulletWeaponBase` | `w610_fighterjet_mgun` | 610 | 1 | `Aim POI` | - |
| `secondary (id:00568A74)` | `CRPGFireLeachWeapon` | `w609_fighterjet_missile_air_lockon` | 609 | 8 | `LaserBeamWeaponComponent` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w608_fighterjet_missile` | `internal_fire_position_1` | 2 | 0 | 3.949 | 1.18 | 2.998 |
| `w608_fighterjet_missile` | `internal_fire_position_2` | 2 | 1 | -3.949 | 1.18 | 2.998 |
| `w610_fighterjet_mgun` | `fire_point.0` | 2 | 0 | 0 | 2.025 | -4.542 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.5` | 2 | 5 | 2.627 | 1.357 | 3.441 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.7` | 2 | 7 | 1.938 | 1.357 | 2.959 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.2` | 2 | 2 | -3.277 | 1.357 | 3.943 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.1` | 2 | 1 | 4.958 | 1.75 | 4.517 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.0` | 2 | 0 | -4.958 | 1.75 | 4.517 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.4` | 2 | 4 | -2.627 | 1.357 | 3.441 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.3` | 2 | 3 | 3.277 | 1.357 | 3.943 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.6` | 2 | 6 | -1.938 | 1.357 | 2.959 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w608_fighterjet_missile` | `editor/entities/jc_weapons/06_vehicle/w608_fighterjet_missile/w608_fighterjet_missile.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtune` | 1000 | - |
| `w610_fighterjet_mgun` | `editor/entities/jc_weapons/06_vehicle/w610_fighterjet_mgun/w610_fighterjet_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | MinigunImpact |
| `w609_fighterjet_missile_air_lockon` | `editor/entities/jc_weapons/06_vehicle/w609_fighterjet_missile_air_lockon/w609_fighterjet_missile_air_lockon.wtune` | `editor/entities/jc_weapons/06_vehicle/w609_fighterjet_missile_air_lockon/w609_fighterjet_missile_air_lockon_autoaim.wtune` | 1012 | - |

seats on `CAirPlane` `v4202_plane_capstone_fighterjet_generated`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

### `v4202_plane_capstone_fighterjet_military_01.ee`

`CAirPlane` · chassis `v4202_plane_capstone_fighterjet` · source `archives_win64/game36` @0 +6,332,832 B · 3 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CAirPlane` `v4202_plane_capstone_fighterjet_military_01`: main_weapon `w610_fighterjet_mgun` · secondary (id:00568A74) `w609_fighterjet_missile_air_lockon` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| *unbound* | `CMissileWeaponBase` | `w608_fighterjet_missile` | 608 | 2 | - | - |
| `main_weapon` | `CBulletWeaponBase` | `w610_fighterjet_mgun` | 610 | 1 | `Aim POI` | - |
| `secondary (id:00568A74)` | `CRPGFireLeachWeapon` | `w609_fighterjet_missile_air_lockon` | 609 | 8 | `LaserBeamWeaponComponent` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w608_fighterjet_missile` | `internal_fire_position_1` | 2 | 0 | 3.949 | 1.18 | 2.998 |
| `w608_fighterjet_missile` | `internal_fire_position_2` | 2 | 1 | -3.949 | 1.18 | 2.998 |
| `w610_fighterjet_mgun` | `fire_point.0` | 2 | 0 | 0 | 2.025 | -4.542 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.5` | 2 | 5 | 2.627 | 1.357 | 3.441 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.7` | 2 | 7 | 1.938 | 1.357 | 2.959 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.2` | 2 | 2 | -3.277 | 1.357 | 3.943 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.1` | 2 | 1 | 4.958 | 1.75 | 4.517 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.0` | 2 | 0 | -4.958 | 1.75 | 4.517 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.4` | 2 | 4 | -2.627 | 1.357 | 3.441 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.3` | 2 | 3 | 3.277 | 1.357 | 3.943 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.6` | 2 | 6 | -1.938 | 1.357 | 2.959 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w608_fighterjet_missile` | `editor/entities/jc_weapons/06_vehicle/w608_fighterjet_missile/w608_fighterjet_missile.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtune` | 1000 | - |
| `w610_fighterjet_mgun` | `editor/entities/jc_weapons/06_vehicle/w610_fighterjet_mgun/w610_fighterjet_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | MinigunImpact |
| `w609_fighterjet_missile_air_lockon` | `editor/entities/jc_weapons/06_vehicle/w609_fighterjet_missile_air_lockon/w609_fighterjet_missile_air_lockon.wtune` | `editor/entities/jc_weapons/06_vehicle/w609_fighterjet_missile_air_lockon/w609_fighterjet_missile_air_lockon_autoaim.wtune` | 1012 | - |

seats on `CAirPlane` `v4202_plane_capstone_fighterjet_military_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

### `v4202_plane_capstone_fighterjet_rebel_01.ee`

`CAirPlane` · chassis `v4202_plane_capstone_fighterjet` · source `archives_win64/game36` @6,338,560 +5,226,752 B · 3 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CAirPlane` `v4202_plane_capstone_fighterjet_rebel_01`: main_weapon `w610_fighterjet_mgun` · secondary (id:00568A74) `w609_fighterjet_missile_air_lockon` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| *unbound* | `CMissileWeaponBase` | `w608_fighterjet_missile` | 608 | 2 | - | - |
| `main_weapon` | `CBulletWeaponBase` | `w610_fighterjet_mgun` | 610 | 1 | `Aim POI` | - |
| `secondary (id:00568A74)` | `CRPGFireLeachWeapon` | `w609_fighterjet_missile_air_lockon` | 609 | 8 | `LaserBeamWeaponComponent` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w608_fighterjet_missile` | `internal_fire_position_1` | 2 | 0 | 3.949 | 1.18 | 2.998 |
| `w608_fighterjet_missile` | `internal_fire_position_2` | 2 | 1 | -3.949 | 1.18 | 2.998 |
| `w610_fighterjet_mgun` | `fire_point.0` | 2 | 0 | 0 | 2.025 | -4.542 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.5` | 2 | 5 | 2.627 | 1.357 | 3.441 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.7` | 2 | 7 | 1.938 | 1.357 | 2.959 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.2` | 2 | 2 | -3.277 | 1.357 | 3.943 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.1` | 2 | 1 | 4.958 | 1.75 | 4.517 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.0` | 2 | 0 | -4.958 | 1.75 | 4.517 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.4` | 2 | 4 | -2.627 | 1.357 | 3.441 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.3` | 2 | 3 | 3.277 | 1.357 | 3.943 |
| `w609_fighterjet_missile_air_lockon` | `fire_point.6` | 2 | 6 | -1.938 | 1.357 | 2.959 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w608_fighterjet_missile` | `editor/entities/jc_weapons/06_vehicle/w608_fighterjet_missile/w608_fighterjet_missile.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtune` | 1000 | - |
| `w610_fighterjet_mgun` | `editor/entities/jc_weapons/06_vehicle/w610_fighterjet_mgun/w610_fighterjet_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | MinigunImpact |
| `w609_fighterjet_missile_air_lockon` | `editor/entities/jc_weapons/06_vehicle/w609_fighterjet_missile_air_lockon/w609_fighterjet_missile_air_lockon.wtune` | `editor/entities/jc_weapons/06_vehicle/w609_fighterjet_missile_air_lockon/w609_fighterjet_missile_air_lockon_autoaim.wtune` | 1012 | - |

seats on `CAirPlane` `v4202_plane_capstone_fighterjet_rebel_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

### `v4602_plane_urga_fighterbomber_debug.ee`

`CAirPlane` · chassis `v4602_plane_urga_fighterbomber` · source `archives_win64/game36` @31,002,624 +6,136,144 B · 3 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CAirPlane` `v4602_plane_urga_fighterbomber_generated`: main_weapon `w611_fighterbomber_missile` · secondary (id:00568A74) `w613_fighterbomber_missile_ground_lockon` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| *unbound* | `CRPGFireLeachWeapon` | `w612_fighterbomber_missile_air_lockon` | 612 | 2 | - | - |
| `main_weapon` | `CMissileWeaponBase` | `w611_fighterbomber_missile` | 611 | 2 | `Aim Pos` | - |
| `secondary (id:00568A74)` | `CMissileWeaponBase` | `w613_fighterbomber_missile_ground_lockon` | 613 | 6 | `warning_light` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w612_fighterbomber_missile_air_lockon` | `fire_point.1` | 2 | 1 | 5.516 | 1.962 | 4.63 |
| `w612_fighterbomber_missile_air_lockon` | `fire_point.0` | 2 | 0 | -5.516 | 1.962 | 4.63 |
| `w611_fighterbomber_missile` | `fire_point.1` | 2 | 1 | 4.695 | 1.218 | 2.382 |
| `w611_fighterbomber_missile` | `fire_point.0` | 2 | 0 | -4.695 | 1.218 | 2.382 |
| `w613_fighterbomber_missile_ground_lockon` | `fire_point.1` | 2 | 1 | 3.986 | 1.392 | 3.35 |
| `w613_fighterbomber_missile_ground_lockon` | `fire_point.0` | 2 | 0 | -3.986 | 1.392 | 3.35 |
| `w613_fighterbomber_missile_ground_lockon` | `fire_point.2` | 2 | 2 | -3.174 | 1.392 | 2.664 |
| `w613_fighterbomber_missile_ground_lockon` | `fire_point.3` | 2 | 3 | 3.174 | 1.392 | 2.664 |
| `w613_fighterbomber_missile_ground_lockon` | `fire_point.4` | 2 | 4 | -2.367 | 1.392 | 2.08 |
| `w613_fighterbomber_missile_ground_lockon` | `fire_point.5` | 2 | 5 | 2.367 | 1.392 | 2.08 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w612_fighterbomber_missile_air_lockon` | `editor/entities/jc_weapons/06_vehicle/w612_fighterbomber_missile_air_lockon/w612_fighterbomber_missile_air_lockon.wtune` | `editor/entities/jc_weapons/06_vehicle/w612_fighterbomber_missile_air_lockon/w612_fighterbomber_missile_air_lockon_autoaim.wtune` | 1012 | - |
| `w611_fighterbomber_missile` | `editor/entities/jc_weapons/06_vehicle/w611_fighterbomber_missile/w611_fighterbomber_missile.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtune` | 0 | - |
| `w613_fighterbomber_missile_ground_lockon` | `editor/entities/jc_weapons/06_vehicle/w613_fighterbomber_missile_ground_lockon/w613_fighterbomber_missile_ground_lockon.wtune` | `editor/entities/jc_weapons/06_vehicle/w613_fighterbomber_missile_ground_lockon/autoaim_w613_bombs.wtune` | 0 | - |

seats on `CAirPlane` `v4602_plane_urga_fighterbomber_generated`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

### `v4602_plane_urga_fighterbomber_military_01.ee`

`CAirPlane` · chassis `v4602_plane_urga_fighterbomber` · source `archives_win64/game36` @37,144,576 +6,137,168 B · 3 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CAirPlane` `v4602_plane_urga_fighterbomber_military_01`: main_weapon `w611_fighterbomber_missile` · secondary (id:00568A74) `w613_fighterbomber_missile_ground_lockon` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| *unbound* | `CRPGFireLeachWeapon` | `w612_fighterbomber_missile_air_lockon` | 612 | 2 | - | - |
| `main_weapon` | `CMissileWeaponBase` | `w611_fighterbomber_missile` | 611 | 2 | `Aim Pos` | - |
| `secondary (id:00568A74)` | `CMissileWeaponBase` | `w613_fighterbomber_missile_ground_lockon` | 613 | 6 | `warning_light` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w612_fighterbomber_missile_air_lockon` | `fire_point.1` | 2 | 1 | 5.516 | 1.962 | 4.63 |
| `w612_fighterbomber_missile_air_lockon` | `fire_point.0` | 2 | 0 | -5.516 | 1.962 | 4.63 |
| `w611_fighterbomber_missile` | `fire_point.1` | 2 | 1 | 4.695 | 1.218 | 2.382 |
| `w611_fighterbomber_missile` | `fire_point.0` | 2 | 0 | -4.695 | 1.218 | 2.382 |
| `w613_fighterbomber_missile_ground_lockon` | `fire_point.1` | 2 | 1 | 3.986 | 1.392 | 3.35 |
| `w613_fighterbomber_missile_ground_lockon` | `fire_point.0` | 2 | 0 | -3.986 | 1.392 | 3.35 |
| `w613_fighterbomber_missile_ground_lockon` | `fire_point.2` | 2 | 2 | -3.174 | 1.392 | 2.664 |
| `w613_fighterbomber_missile_ground_lockon` | `fire_point.3` | 2 | 3 | 3.174 | 1.392 | 2.664 |
| `w613_fighterbomber_missile_ground_lockon` | `fire_point.4` | 2 | 4 | -2.367 | 1.392 | 2.08 |
| `w613_fighterbomber_missile_ground_lockon` | `fire_point.5` | 2 | 5 | 2.367 | 1.392 | 2.08 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w612_fighterbomber_missile_air_lockon` | `editor/entities/jc_weapons/06_vehicle/w612_fighterbomber_missile_air_lockon/w612_fighterbomber_missile_air_lockon.wtune` | `editor/entities/jc_weapons/06_vehicle/w612_fighterbomber_missile_air_lockon/w612_fighterbomber_missile_air_lockon_autoaim.wtune` | 1012 | - |
| `w611_fighterbomber_missile` | `editor/entities/jc_weapons/06_vehicle/w611_fighterbomber_missile/w611_fighterbomber_missile.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtune` | 0 | - |
| `w613_fighterbomber_missile_ground_lockon` | `editor/entities/jc_weapons/06_vehicle/w613_fighterbomber_missile_ground_lockon/w613_fighterbomber_missile_ground_lockon.wtune` | `editor/entities/jc_weapons/06_vehicle/w613_fighterbomber_missile_ground_lockon/autoaim_w613_bombs.wtune` | 0 | - |

seats on `CAirPlane` `v4602_plane_urga_fighterbomber_military_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

### `v4602_plane_urga_fighterbomber_rebel_01.ee`

`CAirPlane` · chassis `v4602_plane_urga_fighterbomber` · source `archives_win64/game36` @43,286,528 +6,187,472 B · 3 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CAirPlane` `v4602_plane_urga_fighterbomber_rebel_01`: main_weapon `w611_fighterbomber_missile` · secondary (id:00568A74) `w613_fighterbomber_missile_ground_lockon` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| *unbound* | `CRPGFireLeachWeapon` | `w612_fighterbomber_missile_air_lockon` | 612 | 2 | - | - |
| `main_weapon` | `CMissileWeaponBase` | `w611_fighterbomber_missile` | 611 | 2 | `Aim Pos` | - |
| `secondary (id:00568A74)` | `CMissileWeaponBase` | `w613_fighterbomber_missile_ground_lockon` | 613 | 6 | `warning_light` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w612_fighterbomber_missile_air_lockon` | `fire_point.1` | 2 | 1 | 5.516 | 1.962 | 4.63 |
| `w612_fighterbomber_missile_air_lockon` | `fire_point.0` | 2 | 0 | -5.516 | 1.962 | 4.63 |
| `w611_fighterbomber_missile` | `fire_point.1` | 2 | 1 | 4.695 | 1.218 | 2.382 |
| `w611_fighterbomber_missile` | `fire_point.0` | 2 | 0 | -4.695 | 1.218 | 2.382 |
| `w613_fighterbomber_missile_ground_lockon` | `fire_point.1` | 2 | 1 | 3.986 | 1.392 | 3.35 |
| `w613_fighterbomber_missile_ground_lockon` | `fire_point.0` | 2 | 0 | -3.986 | 1.392 | 3.35 |
| `w613_fighterbomber_missile_ground_lockon` | `fire_point.2` | 2 | 2 | -3.174 | 1.392 | 2.664 |
| `w613_fighterbomber_missile_ground_lockon` | `fire_point.3` | 2 | 3 | 3.174 | 1.392 | 2.664 |
| `w613_fighterbomber_missile_ground_lockon` | `fire_point.4` | 2 | 4 | -2.367 | 1.392 | 2.08 |
| `w613_fighterbomber_missile_ground_lockon` | `fire_point.5` | 2 | 5 | 2.367 | 1.392 | 2.08 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w612_fighterbomber_missile_air_lockon` | `editor/entities/jc_weapons/06_vehicle/w612_fighterbomber_missile_air_lockon/w612_fighterbomber_missile_air_lockon.wtune` | `editor/entities/jc_weapons/06_vehicle/w612_fighterbomber_missile_air_lockon/w612_fighterbomber_missile_air_lockon_autoaim.wtune` | 1012 | - |
| `w611_fighterbomber_missile` | `editor/entities/jc_weapons/06_vehicle/w611_fighterbomber_missile/w611_fighterbomber_missile.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtune` | 0 | - |
| `w613_fighterbomber_missile_ground_lockon` | `editor/entities/jc_weapons/06_vehicle/w613_fighterbomber_missile_ground_lockon/w613_fighterbomber_missile_ground_lockon.wtune` | `editor/entities/jc_weapons/06_vehicle/w613_fighterbomber_missile_ground_lockon/autoaim_w613_bombs.wtune` | 0 | - |

seats on `CAirPlane` `v4602_plane_urga_fighterbomber_rebel_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

### `v4603_plane_urga_cargotransport_military_cargo_tank.ee`

`CAirPlane` + `CCar` · chassis `v4603_plane_urga_cargotransport` · source `archives_win64/game36` @78,338,048 +13,296,720 B · 2 weapon component(s), 2 driver slot(s), 0 gunner slot(s)

slots on `CAirPlane` `v4603_plane_urga_cargotransport_military_01`: main_weapon - · secondary (id:00568A74) - · mounted_weapon - · mounted_weapon_2 -

slots on `CCar` `v0201_car_capstone_mediumtank_military_01`: main_weapon `w602_mediumtank_canon` · secondary (id:00568A74) `w603_mediumtank_mgun` · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `CCar::main_weapon` | `CBulletWeaponBase` | `w602_mediumtank_canon` | 602 | 1 | `warning_light` | - |
| `CCar::secondary (id:00568A74)` | `CBulletWeaponBase` | `w603_mediumtank_mgun` | 603 | 1 | - | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w602_mediumtank_canon` | `fire_position_0` | 2 | 0 | 0 | 0.3739 | -5.8174 |
| `w603_mediumtank_mgun` | `fire_position_0` | 2 | 0 | 0.247 | 0.485 | -2.018 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w602_mediumtank_canon` | `editor/entities/jc_weapons/06_vehicle/w602_mediumtank_canon/w602_mediumtank_canon.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | AAGunImpact |
| `w603_mediumtank_mgun` | `editor/entities/jc_weapons/06_vehicle/w603_mediumtank_mgun/w603_mediumtank_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | 50CalBulletImpact |

seats on `CAirPlane` `v4603_plane_urga_cargotransport_military_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.gunner.left.detached_ai` | 39 | `S_IDLE` | `point.gunner.left.detached_ai` |
| `interaction.seat.fake.stunt_ai` | 41 | `S_IDLE` | `point.fake.stunt.ai` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |
| `interaction.seat.passenger1` | 1 | `S_IDLE_PASSENGER_VEHICLE` | `point.passenger1` |
| `interaction.seat.gunner.right.detached_ai` | 40 | `S_IDLE` | `point.gunner.right.detached_ai` |

seats on `CCar` `v0201_car_capstone_mediumtank_military_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

### `v4800_plane_brothers_vintagefighter_debug.ee`

`CAirPlane` · chassis `v4800_plane_brothers_vintagefighter` · source `archives_win64/game36` @110,966,784 +6,997,808 B · 1 weapon component(s), 1 driver slot(s), 0 gunner slot(s)

slots on `CAirPlane` `v4800_plane_brothers_vintagefighter_generated`: main_weapon `w617_vintagefighter_mgun` · secondary (id:00568A74) - · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `main_weapon` | `CBulletWeaponBase` | `w617_vintagefighter_mgun` | 617 | 6 | `Aim POI` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w617_vintagefighter_mgun` | `internal.fire_point.4` | 2 | 4 | -3.125 | 1.843 | -3.553 |
| `w617_vintagefighter_mgun` | `internal.fire_point.5` | 2 | 5 | 3.125 | 1.843 | -3.553 |
| `w617_vintagefighter_mgun` | `internal.fire_point.2` | 2 | 2 | -2.849 | 1.845 | -3.694 |
| `w617_vintagefighter_mgun` | `internal.fire_point.3` | 2 | 3 | 2.849 | 1.845 | -3.694 |
| `w617_vintagefighter_mgun` | `internal.fire_point.1` | 2 | 1 | 2.584 | 1.845 | -3.834 |
| `w617_vintagefighter_mgun` | `internal.fire_point.0` | 2 | 0 | -2.584 | 1.845 | -3.834 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w617_vintagefighter_mgun` | `editor/entities/jc_weapons/06_vehicle/w617_vintagefighter_mgun/w617_vintagefighter_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | MinigunImpact |

seats on `CAirPlane` `v4800_plane_brothers_vintagefighter_generated`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

### `v4800_plane_brothers_vintagefighter_rebel_01.ee`

`CAirPlane` · chassis `v4800_plane_brothers_vintagefighter` · source `archives_win64/game36` @117,968,896 +6,997,856 B · 1 weapon component(s), 1 driver slot(s), 0 gunner slot(s)

slots on `CAirPlane` `v4800_plane_brothers_vintagefighter_rebel_01`: main_weapon `w617_vintagefighter_mgun` · secondary (id:00568A74) - · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| `main_weapon` | `CBulletWeaponBase` | `w617_vintagefighter_mgun` | 617 | 6 | `Aim POI` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w617_vintagefighter_mgun` | `internal.fire_point.4` | 2 | 4 | -3.125 | 1.843 | -3.553 |
| `w617_vintagefighter_mgun` | `internal.fire_point.5` | 2 | 5 | 3.125 | 1.843 | -3.553 |
| `w617_vintagefighter_mgun` | `internal.fire_point.2` | 2 | 2 | -2.849 | 1.845 | -3.694 |
| `w617_vintagefighter_mgun` | `internal.fire_point.3` | 2 | 3 | 2.849 | 1.845 | -3.694 |
| `w617_vintagefighter_mgun` | `internal.fire_point.1` | 2 | 1 | 2.584 | 1.845 | -3.834 |
| `w617_vintagefighter_mgun` | `internal.fire_point.0` | 2 | 0 | -2.584 | 1.845 | -3.834 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w617_vintagefighter_mgun` | `editor/entities/jc_weapons/06_vehicle/w617_vintagefighter_mgun/w617_vintagefighter_mgun.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune` | 0 | MinigunImpact |

seats on `CAirPlane` `v4800_plane_brothers_vintagefighter_rebel_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.driver` | 0 | `S_IDLE_DRIVER_VEHICLE` | `point.driver` |
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

### `v5603_train_urga_monorailmissilecar_military_01.ee`

`CTrain` · chassis `v5603_train_urga_monorailmissilecar` · source `archives_win64/game35` @738,861,056 +3,803,760 B · 1 weapon component(s), 0 driver slot(s), 0 gunner slot(s)

slots on `CTrain` `v5603_train_urga_monorailmissilecar_military_01`: main_weapon - · secondary (id:00568A74) - · mounted_weapon - · mounted_weapon_2 -

| slot | class | weapon | id | muzzles | aim / aux components | mount parts |
|---|---|---|---|---|---|---|
| *unbound* | `CMissileWeaponBase` | `w614_monorailmissilecar_missile` | 614 | 6 | `TurretWeaponComponent` | - |

| weapon | point | type | fire_effect | x | y | z |
|---|---|---|---|---|---|---|
| `w614_monorailmissilecar_missile` | `InternalFirePosition_0` | 2 | 0 | -2.0386 | 2.4922 | 0.9648 |
| `w614_monorailmissilecar_missile` | `InternalFirePosition_2` | 2 | 2 | -2.0386 | 2.4922 | -0.6616 |
| `w614_monorailmissilecar_missile` | `InternalFirePosition_1` | 2 | 1 | 1.8506 | 2.4924 | 0.9424 |
| `w614_monorailmissilecar_missile` | `InternalFirePosition_3` | 2 | 3 | 1.8506 | 2.4924 | -0.9058 |
| `w614_monorailmissilecar_missile` | `InternalFirePosition_4` | 2 | 4 | -2.0386 | 2.4922 | -2.3276 |
| `w614_monorailmissilecar_missile` | `InternalFirePosition_5` | 2 | 5 | 1.8506 | 2.4924 | -2.5288 |

| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |
|---|---|---|---|---|
| `w614_monorailmissilecar_missile` | `editor/entities/jc_weapons/06_vehicle/w614_monorailmissilecar_missile/w614_monorailmissilecar_missile.wtune` | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_lockon_missile.wtune` | 0 | - |

seats on `CTrain` `v5603_train_urga_monorailmissilecar_military_01`:

| seat | index | state(s) | point |
|---|---|---|---|
| `interaction.seat.stunt` | 8 | `S_IDLE` | `point.stunt` |

moving parts on the chassis: `monorailmissilecar_missile_hatch_l_01` (MissileHatch, 20 ← `monorailmissilecar_missile_base_l`), `monorailmissilecar_missile_hatch_l_02` (MissileHatch, 21 ← `monorailmissilecar_missile_base_l`), `monorailmissilecar_missile_hatch_l_03` (MissileHatch, 22 ← `monorailmissilecar_missile_base_l`), `monorailmissilecar_missile_hatch_l_04` (MissileHatch, 23 ← `monorailmissilecar_missile_base_l`), `monorailmissilecar_missile_hatch_l_05` (MissileHatch, 24 ← `monorailmissilecar_missile_base_l`), `monorailmissilecar_missile_hatch_l_06` (MissileHatch, 25 ← `monorailmissilecar_missile_base_l`), `monorailmissilecar_missile_hatch_l_07` (MissileHatch, 26 ← `monorailmissilecar_missile_base_l`), `monorailmissilecar_missile_hatch_l_08` (MissileHatch, 27 ← `monorailmissilecar_missile_base_l`) … and 8 more

## 6. Limits of what the entity says

- **Driver vs gunner is structural, not per-weapon.** No weapon component points at a seat. The distinction is the slot set: the two driver pointers coexist with no gunner seat, while mounted weapons always sit on a seat whose state is `S_IDLE_VEHICLE_SPINNING_MOUNTED_WEAPON` (APC, technical, armoured jeep), `S_VEHICLE_FIXED_MOUNTED_WEAPON` (heavy patrol boat) or `S_MOUNTED_WEAPON` (light patrol boat). No entity mixes a driver slot with a gunner slot. The nearest-gunner-seat line is a geometric join between the weapon's world translation and the seat point, not a pointer.
- **No button mapping.** The entity does not say which input fires which slot; the G2-10 tunes have no input member either. Primary/secondary below means first/second pointer, which is the evidence the files carry.
- **Most driver weapons name no part.** 22 of 88 weapons carry a type-4 `MountAttach`: all 19 gunner weapons (two parts each) and the corvette's driver cannon (`corvette_gun`, `corvette_turret`). The other 59 driver weapons have no part pointer; their chassis part list is recorded, but the turret/cannon -> weapon link is not in the `.epe`.
- **`CLightWeaponComponent` is a light**, not a gun: colour/radius/spot data, usually a child of a cannon (e.g. the medium tank's `warning_light`).
- **The monorail missile car has no slot at all.** Its only weapon sits under a `CTurretWeaponComponent` and the entity exposes only `interaction.seat.stunt`; it is an AI/script turret, not a driver weapon.
- **Two all-null pointers** (`id:8580BA42`, `id:CA86AA17`) are on every root class and never resolve to a weapon on the 53 armed entities; their names are not in the shipped name tables and no candidate hashed to them.

## 7. Validation

`jc3wiring.py --check` re-reads all 53 entities out of the archives, decodes the `.epe` again, rebuilds every row and compares it field-for-field with the jsonl, then regenerates this file and diffs it. It also re-checks:

- the census list (53 armed entities) matches the decoded rows one-for-one;
- every object whose `id:D04059E6` property is present hashes to its own class name (the property is a class-name hash, so this also proves the parser read the right bytes);
- every non-null slot resolves to a decoded weapon component;
- the weapon names and SWeaponPoint counts match `FEATURE_CENSUS.json` (a different decode path, P0-2) for every entity;
- the summary totals (81 bound, 7 unbound).

Decoded: **53 entities**, 88 weapon components, 193 seats, 112 moving-part rows, 300 weapon points.

