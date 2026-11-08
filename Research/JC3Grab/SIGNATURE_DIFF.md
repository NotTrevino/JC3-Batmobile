# The armed Serpente: civilian → signature_preorder

The exact difference between `v0300_car_kensington_sportsmuscle_civilian_01` and `..._signature_preorder` (G2-12), read from the two `.ee` containers: every inner member, the `.epe` object graph and its weapon subtree, the parts modules, the mesh headers and the `w618` tunes. The point is to separate the *wiring* (what B-05/B-06 import) from the *art* (what the signature body kit is).

## 1. Sources

| | civilian | signature_preorder |
|---|---|---|
| entity | `v0300_car_kensington_sportsmuscle_civilian_01.ee` | `v0300_car_kensington_sportsmuscle_signature_preorder.ee` |
| container size | 5539952 | 5802496 |
| container sha1 | 8e8ac6fd9ecdfb02d47372176c34220a422a442d | 985e8479eef222703f3e106815e4188a1f36b236 |
| inner `.epe` | 109526 B `d4570984eb607013fd1ad66cfe81267f8b78ad6e` | 114962 B `cbafe09ef30f920886b77534411829b2671708a9` |
| loose `.epe` entry | 109766 B `201426a8b6cd97e0b46412d869b265a37e891648` | 115378 B `5dd120dccb7fe666e7530d74c901ff53f1e2fdb8` |

The container member is the graph the game builds. The loose `.epe` entry next to it is a different build (both sizes/hashes above), so it is not used for the diff and not quoted as authoritative.

## 2. Container diff

566 members vs 601: **167 added** (**108 of them a same-role replacement**, a `signature/` path for the base path), **132 removed**, **0 changed by name**.

| kind | added | removed |
|---|---|---|
| effect | 11 | 0 |
| graph | 1 | 1 |
| lod | 24 | 23 |
| mesh | 89 | 84 |
| meta | 2 | 2 |
| module | 2 | 3 |
| other | 6 | 0 |
| physics | 1 | 0 |
| texture | 27 | 19 |
| tune | 4 | 0 |

Same-role replacements (base asset → signature asset):

| stem | before | after | Δ bytes |
|---|---|---|---|
| `sportsmuscle_body.lod` | 450 | 550 | +100 |
| `sportsmuscle_body_lod1.rbm` | 403514 | 403373 | -141 |
| `sportsmuscle_body_lod2.rbm` | 284214 | 284073 | -141 |
| `sportsmuscle_body_lod3.rbm` | 182381 | 182240 | -141 |
| `sportsmuscle_body_lod4.rbm` | 202321 | 202300 | -21 |
| `sportsmuscle_body_lod5.rbm` | 105269 | 105254 | -15 |
| `sportsmuscle_c_mirror.lod` | 470 | 570 | +100 |
| `sportsmuscle_c_mirror_lod1.rbm` | 14211 | 14164 | -47 |
| `sportsmuscle_c_mirror_lod2.rbm` | 5247 | 5200 | -47 |
| `sportsmuscle_c_mirror_lod3.rbm` | 4035 | 3988 | -47 |
| `sportsmuscle_c_mirror_lod4.rbm` | 2775 | 2728 | -47 |
| `sportsmuscle_door_f_l.lod` | 470 | 570 | +100 |
| `sportsmuscle_door_f_l_lod1.rbm` | 65526 | 65479 | -47 |
| `sportsmuscle_door_f_l_lod2.rbm` | 37064 | 37017 | -47 |
| `sportsmuscle_door_f_l_lod3.rbm` | 22609 | 22562 | -47 |
| `sportsmuscle_door_f_l_lod4.rbm` | 13225 | 13218 | -7 |
| `sportsmuscle_door_f_r.lod` | 470 | 570 | +100 |
| `sportsmuscle_door_f_r_lod1.rbm` | 65526 | 65479 | -47 |
| `sportsmuscle_door_f_r_lod2.rbm` | 37220 | 37173 | -47 |
| `sportsmuscle_door_f_r_lod3.rbm` | 23109 | 23062 | -47 |
| `sportsmuscle_door_f_r_lod4.rbm` | 12475 | 12468 | -7 |
| `sportsmuscle_fender_l.lod` | 470 | 570 | +100 |
| `sportsmuscle_fender_l_lod1.rbm` | 63679 | 63632 | -47 |
| `sportsmuscle_fender_l_lod2.rbm` | 36167 | 36120 | -47 |
| `sportsmuscle_fender_l_lod3.rbm` | 20127 | 20080 | -47 |
| `sportsmuscle_fender_r.lod` | 470 | 570 | +100 |
| `sportsmuscle_fender_r_lod1.rbm` | 63623 | 63576 | -47 |
| `sportsmuscle_fender_r_lod2.rbm` | 34775 | 34728 | -47 |
| `sportsmuscle_fender_r_lod3.rbm` | 18423 | 18376 | -47 |
| `sportsmuscle_front_bumper.lod` | 490 | 590 | +100 |
| `sportsmuscle_front_bumper_lod1.rbm` | 64919 | 64872 | -47 |
| `sportsmuscle_front_bumper_lod2.rbm` | 29887 | 29840 | -47 |
| `sportsmuscle_front_bumper_lod3.rbm` | 19131 | 19084 | -47 |
| `sportsmuscle_grill.lod` | 455 | 555 | +100 |
| `sportsmuscle_grill_lod1.rbm` | 31023 | 30976 | -47 |
| `sportsmuscle_grill_lod2.rbm` | 16339 | 16292 | -47 |
| `sportsmuscle_grill_lod3.rbm` | 11407 | 11360 | -47 |
| `sportsmuscle_hood.lod` | 450 | 550 | +100 |
| `sportsmuscle_hood_lod1.rbm` | 47415 | 47368 | -47 |
| `sportsmuscle_hood_lod2.rbm` | 26531 | 26484 | -47 |
| `sportsmuscle_hood_lod3.rbm` | 13091 | 13044 | -47 |
| `sportsmuscle_hood_signature.lod` | 500 | 600 | +100 |
| `sportsmuscle_hood_signature_lod1.rbm` | 170710 | 170663 | -47 |
| `sportsmuscle_hood_signature_lod2.rbm` | 40502 | 40455 | -47 |
| `sportsmuscle_hood_signature_lod3.rbm` | 25592 | 25545 | -47 |
| `sportsmuscle_l_mirror.lod` | 470 | 570 | +100 |
| `sportsmuscle_l_mirror_lod1.rbm` | 11979 | 11932 | -47 |
| `sportsmuscle_l_mirror_lod2.rbm` | 5115 | 5068 | -47 |
| `sportsmuscle_l_mirror_lod3.rbm` | 4347 | 4300 | -47 |
| `sportsmuscle_l_mirror_lod4.rbm` | 3159 | 3112 | -47 |
| `sportsmuscle_missile_base_signature.lod` | 540 | 640 | +100 |
| `sportsmuscle_missile_base_signature_lod1.rbm` | 45912 | 45865 | -47 |
| `sportsmuscle_missile_base_signature_lod2.rbm` | 21842 | 21795 | -47 |
| `sportsmuscle_missile_base_signature_lod3.rbm` | 14590 | 14543 | -47 |
| `sportsmuscle_r_mirror.lod` | 470 | 570 | +100 |
| `sportsmuscle_r_mirror_lod1.rbm` | 11979 | 11932 | -47 |
| `sportsmuscle_r_mirror_lod2.rbm` | 4767 | 4720 | -47 |
| `sportsmuscle_r_mirror_lod3.rbm` | 4299 | 4252 | -47 |
| `sportsmuscle_r_mirror_lod4.rbm` | 3411 | 3364 | -47 |
| `sportsmuscle_rear_bumper.lod` | 485 | 585 | +100 |
| `sportsmuscle_rear_bumper_lod1.rbm` | 59335 | 59288 | -47 |
| `sportsmuscle_rear_bumper_lod2.rbm` | 32483 | 32436 | -47 |
| `sportsmuscle_rear_bumper_lod3.rbm` | 15415 | 15368 | -47 |
| `sportsmuscle_rear_bumper_lod4.rbm` | 8119 | 8072 | -47 |
| `sportsmuscle_trunk.lod` | 455 | 555 | +100 |
| `sportsmuscle_trunk_lod1.rbm` | 61114 | 61067 | -47 |
| `sportsmuscle_trunk_lod2.rbm` | 36430 | 36383 | -47 |
| `sportsmuscle_trunk_lod3.rbm` | 22334 | 22287 | -47 |
| `sportsmuscle_trunk_lod4.rbm` | 13461 | 13457 | -4 |
| `sportsmuscle_wheel_f_l.lod` | 475 | 575 | +100 |
| `sportsmuscle_wheel_f_l_lod1.rbm` | 43886 | 43930 | +44 |
| `sportsmuscle_wheel_f_l_lod2.rbm` | 22142 | 22186 | +44 |
| `sportsmuscle_wheel_f_l_lod3.rbm` | 14042 | 14086 | +44 |
| `sportsmuscle_wheel_f_lmshswap.lod` | 422 | 502 | +80 |
| `sportsmuscle_wheel_f_lmshswap_lod1.rbm` | 29198 | 29242 | +44 |
| `sportsmuscle_wheel_f_lmshswap_lod2.rbm` | 17942 | 17986 | +44 |
| `sportsmuscle_wheel_f_lmshswap_lod3.rbm` | 11750 | 11794 | +44 |
| `sportsmuscle_wheel_f_r.lod` | 475 | 575 | +100 |
| `sportsmuscle_wheel_f_r_lod1.rbm` | 41414 | 41458 | +44 |
| `sportsmuscle_wheel_f_r_lod2.rbm` | 23234 | 23278 | +44 |
| `sportsmuscle_wheel_f_r_lod3.rbm` | 13502 | 13546 | +44 |
| `sportsmuscle_wheel_f_rmshswap.lod` | 422 | 502 | +80 |
| `sportsmuscle_wheel_f_rmshswap_lod1.rbm` | 29198 | 29242 | +44 |
| `sportsmuscle_wheel_f_rmshswap_lod2.rbm` | 18302 | 18346 | +44 |
| `sportsmuscle_wheel_f_rmshswap_lod3.rbm` | 11774 | 11818 | +44 |
| `sportsmuscle_wheel_r_l.lod` | 475 | 575 | +100 |
| `sportsmuscle_wheel_r_l_lod1.rbm` | 41486 | 41530 | +44 |
| `sportsmuscle_wheel_r_l_lod2.rbm` | 21830 | 21874 | +44 |
| `sportsmuscle_wheel_r_l_lod3.rbm` | 14366 | 14410 | +44 |
| `sportsmuscle_wheel_r_l_lod4.rbm` | 10382 | 10426 | +44 |
| `sportsmuscle_wheel_r_l_lod5.rbm` | 7442 | 7486 | +44 |
| `sportsmuscle_wheel_r_lmshswap.lod` | 422 | 502 | +80 |
| `sportsmuscle_wheel_r_lmshswap_lod1.rbm` | 29198 | 29242 | +44 |
| `sportsmuscle_wheel_r_lmshswap_lod2.rbm` | 17834 | 17878 | +44 |
| `sportsmuscle_wheel_r_lmshswap_lod3.rbm` | 11966 | 12010 | +44 |
| `sportsmuscle_wheel_r_lmshswap_lod4.rbm` | 8222 | 8266 | +44 |
| `sportsmuscle_wheel_r_r.lod` | 475 | 575 | +100 |
| `sportsmuscle_wheel_r_r_lod1.rbm` | 41414 | 41458 | +44 |
| `sportsmuscle_wheel_r_r_lod2.rbm` | 23210 | 23254 | +44 |
| `sportsmuscle_wheel_r_r_lod3.rbm` | 13610 | 13654 | +44 |
| `sportsmuscle_wheel_r_r_lod4.rbm` | 10478 | 10522 | +44 |
| `sportsmuscle_wheel_r_r_lod5.rbm` | 6026 | 6070 | +44 |
| `sportsmuscle_wheel_r_rmshswap.lod` | 422 | 502 | +80 |
| `sportsmuscle_wheel_r_rmshswap_lod1.rbm` | 29198 | 29242 | +44 |
| `sportsmuscle_wheel_r_rmshswap_lod2.rbm` | 18038 | 18082 | +44 |
| `sportsmuscle_wheel_r_rmshswap_lod3.rbm` | 11642 | 11686 | +44 |
| `sportsmuscle_wheel_r_rmshswap_lod4.rbm` | 8078 | 8122 | +44 |
| `sportsmuscle_vehicle_parts.vmodc` | 29886 | 30382 | +496 |

Added and not a rename (grouped by kind and directory):

- **effect** in `effects/jc_weapons/missile` (1): `missile_trail_car.effc`
- **effect** in `effects/jc_weapons/muzzle_flash` (1): `sportsmuscle_missile_muzzleflash.effc`
- **effect** in `effects/jc_weapons/tank_explosive` (7): `tank_explosive_concrete.effc`, `tank_explosive_default.effc`, `tank_explosive_dirt.effc`, `tank_explosive_grass.effc`, `tank_explosive_metal.effc`, `tank_explosive_sand.effc`, `tank_explosive_snow.effc`
- **effect** in `effects/trails` (2): `smoke_trail_05.effc`, `spark_trail_03.effc`
- **graph** in `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle` (1): `v0300_car_kensington_sportsmuscle_signature_preorder.epe`
- **lod** in `models/jc_weapons/02_two_handed/w143_rpg_fire_leach` (1): `w143_rpg_fire_leach_projectile_body.lod`
- **mesh** in `models/jc_weapons/02_two_handed/w143_rpg_fire_leach` (5): `w143_rpg_fire_leach_projectile_body_lod1.rbm`, `w143_rpg_fire_leach_projectile_body_lod2.rbm`, `w143_rpg_fire_leach_projectile_body_lod3.rbm`, `w143_rpg_fire_leach_projectile_body_lod4.rbm`, `w143_rpg_fire_leach_projectile_body_lod5.rbm`
- **meta** in `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle` (2): `v0300_car_kensington_sportsmuscle_signature_preorder.ee.fmod_guids`, `v0300_car_kensington_sportsmuscle_signature_preorder.stringlookup`
- **module** in `editor/entities/jc_vehicles/00_shared/modules/decals` (1): `default_decals.vmodc`
- **other** in `effects/textures` (6): `t_bullet_impact_s2_dif.tga.1_1a.trim`, `t_explosiongrid_fume_07_whitesmoke_alpha_dif.tga.8_8b.trim`, `t_explosiongrid_fumeblur_01_alpha_dif.tga.4_8bb.trim`, `t_flare_base_02_dif.tga.1_1a.trim`, `t_grit_01_s2_alpha_dif.tga.1_2b.trim`, `t_weap_star_01_alpha_dif.tga.1_4a.trim`
- **physics** in `models/jc_weapons/02_two_handed/w143_rpg_fire_leach` (1): `w143_rpg_fire_leach_projectile_body_col.pfxc`
- **texture** in `effects/textures` (8): `t_bullet_impact_s2_dif.ddsc`, `t_debris_stone_row_01_nrm.ddsc`, `t_explosiongrid_fume_06_top_gold_alpha_dif.ddsc`, `t_explosiongrid_fume_07_whitesmoke_alpha_dif.ddsc`, `t_explosiongrid_fumeblur_01_alpha_dif.ddsc`, `t_flare_base_02_dif.ddsc`, `t_grit_01_s2_alpha_dif.ddsc`, `t_weap_star_01_alpha_dif.ddsc`
- **texture** in `effects/textures/erosion` (1): `erosion_03_smallcurve_dif.ddsc`
- **texture** in `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/signature` (14): `body_aggregate_signature_decal_alpha_dif.ddsc`, `body_aggregate_signature_dif.ddsc`, `body_aggregate_signature_mpm.ddsc`, `car_tire_sport02_signature_dif.ddsc`, `door_f_l_aggregate_signature_decal_alpha_dif.ddsc`, `door_f_l_aggregate_signature_dif.ddsc`, `door_f_l_aggregate_signature_mpm.ddsc`, `door_f_r_aggregate_signature_decal_alpha_dif.ddsc`, `door_f_r_aggregate_signature_dif.ddsc`, `door_f_r_aggregate_signature_mpm.ddsc`, `trunk_aggregate_signature_decal_alpha_dif.ddsc`, `trunk_aggregate_signature_dif.ddsc`, `trunk_aggregate_signature_mpm.ddsc`, `v0300_car_kensington_sportsmuscle_body_signature_dif.ddsc`
- **texture** in `models/jc_weapons/02_two_handed/w143_rpg_fire_leach/textures` (4): `w143_rpg_fire_leach_projectile_dif.ddsc`, `w143_rpg_fire_leach_projectile_met.ddsc`, `w143_rpg_fire_leach_projectile_mpm.ddsc`, `w143_rpg_fire_leach_projectile_nrm.ddsc`
- **tune** in `editor/entities/jc_environments/shared` (1): `rigid_object_effect_settings_default.etunec`
- **tune** in `editor/entities/jc_explosions/weapons` (1): `w618_sportsmuscle_missile.ftunec`
- **tune** in `editor/entities/jc_weapons/00_shared/autoaim_tuning` (1): `autoaim_vehicle_no_lockon_missile.wtunec`
- **tune** in `editor/entities/jc_weapons/06_vehicle/w618_sportsmuscle_missile` (1): `w618_sportsmuscle_missile.wtunec`

Removed and not replaced 1:1:

- **module** `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_decals.vmodc` (392 B)
- **module** `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_palette.vmodc` (1897 B)
- **meta** `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.ee.fmod_guids` (758 B)
- **graph** `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.epe` (109526 B)
- **meta** `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.stringlookup` (2210 B)
- **texture** `models/jc_vehicles/00_shared/car_tire/texture/car_tire_sport02_dif.ddsc` (21984 B)
- **texture** `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/body_aggregate_base_decal_alpha_dif.ddsc` (22000 B)
- **texture** `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/body_aggregate_base_dif.ddsc` (43832 B)
- **texture** `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/body_aggregate_base_mpm.ddsc` (43832 B)
- **texture** `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/body_aggregate_base_msk.ddsc` (43832 B)
- **texture** `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/door_f_l_aggregate_base_decal_alpha_dif.ddsc` (22000 B)
- **texture** `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/door_f_l_aggregate_base_dif.ddsc` (43832 B)
- **texture** `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/door_f_l_aggregate_base_mpm.ddsc` (43832 B)
- **texture** `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/door_f_l_aggregate_base_msk.ddsc` (43832 B)
- **texture** `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/door_f_r_aggregate_base_decal_alpha_dif.ddsc` (22000 B)
- **texture** `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/door_f_r_aggregate_base_dif.ddsc` (43832 B)
- **texture** `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/door_f_r_aggregate_base_mpm.ddsc` (43832 B)
- **texture** `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/door_f_r_aggregate_base_msk.ddsc` (43832 B)
- **texture** `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/trunk_aggregate_base_decal_alpha_dif.ddsc` (22000 B)
- **texture** `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/trunk_aggregate_base_dif.ddsc` (43832 B)
- **texture** `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/trunk_aggregate_base_mpm.ddsc` (43832 B)
- **texture** `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/trunk_aggregate_base_msk.ddsc` (43832 B)
- **texture** `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/v0300_car_kensington_sportsmuscle_body_dif.ddsc` (43832 B)
- **texture** `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/v0300_car_kensington_sportsmuscle_body_msk.ddsc` (43832 B)

## 3. Entity graph (`epe`)

450 objects vs 464. The raw id diff marks all 450 objects changed; resolving references by semantic path and ignoring `vec_events` leaves **2 changed objects**, plus **4 added** and **1 removed** subtrees (51 reference values resolved to the same path, 603 `vec_events` values and 1245 identity fields discarded).

### Added

| path | class | name | objects | contents |
|---|---|---|---|---|
| `root/CCar/CParts:Parts/CPartProp:sportsmuscle_body/CPartProp:sportsmuscle_engine/CPartProp:sportsmuscle_hood_signature` | `CPartProp` | `sportsmuscle_hood_signature` | 2 | CPartProp×2 |
| `root/CForcePulse:w618_sportsmuscle_missile` | `CForcePulse` | `w618_sportsmuscle_missile` | 1 | CForcePulse×1 |
| `root/CMaterialEffectTable:tank_explosion_effect_table` | `CMaterialEffectTable` | `tank_explosion_effect_table` | 1 | CMaterialEffectTable×1 |
| `root/CMissileWeaponBase:w618_sportsmuscle_missile` | `CMissileWeaponBase` | `w618_sportsmuscle_missile` | 11 | CAimPOIWeaponComponent×1, CMissileWeaponBase×1, SAttachedEffect×4, SEffects×1, SWeaponPoint×4 |

### Removed

| path | class | name | objects |
|---|---|---|---|
| `root/CCar/CParts:Parts/CPartProp:sportsmuscle_body/CPartProp:sportsmuscle_engine/CPartProp:sportsmuscle_hood` | `CPartProp` | `sportsmuscle_hood` | 1 |

### Changed properties

Identity-only churn is excluded; a reference is shown by the semantic path it resolves to. `->` is a link, `00000000` is null.

**`CCar`** `v0300_car_kensington_sportsmuscle_civilian_01` — `root/CCar`

| property | type | before | after |
|---|---|---|---|
| `decals` | int | 1732285335 → `default/v0300_car_kensington_sportsmuscle_decals.vmodc` | -211122583 → `decals/default_decals.vmodc` |
| `id:851CAABE` (unnamed) | objectid | 00000000 | ->root/CMissileWeaponBase:w618_sportsmuscle_missile |
| `id:EA011E72` (unnamed) | float | 0.3 | 1 |
| `id:FFE31EE1` (unnamed) | int | 1 | 0 |
| `name` | string | v0300_car_kensington_sportsmuscle_civilian_01 | v0300_car_kensington_sportsmuscle_signature_preorder |
| `palette` | int | -1071400364 → `default/v0300_car_kensington_sportsmuscle_palette.vmodc` | None |
| `vehicle_parts` | int | 1526043305 → `v0300_car_kensington_sportsmuscle/sportsmuscle_vehicle_parts.vmodc` | 402479768 → `signature/sportsmuscle_vehicle_parts.vmodc` |

**`CInteractionGraphPointNode`** `point.stunt.hood` — `root/CInteractionContext:context/CInteractionGraph:graph/CInteractionGraphPointNode:point.stunt.hood`

| property | type | before | after |
|---|---|---|---|
| `id:ED4F648C` (unnamed) | string | front_area | front_signature_area |

Class counts that moved:

| class | civilian | variant |
|---|---|---|
| `CAimPOIWeaponComponent` | 0 | 1 |
| `CForcePulse` | 1 | 2 |
| `CMaterialEffectTable` | 0 | 1 |
| `CMissileWeaponBase` | 0 | 1 |
| `CPartProp` | 40 | 41 |
| `SAttachedEffect` | 27 | 31 |
| `SEffects` | 1 | 2 |
| `SWeaponPoint` | 0 | 4 |

### The added weapon, point by point

`CMissileWeaponBase` `w618_sportsmuscle_missile` — object `A7E417D5=FFFF20AF`, `weapon_id` 618, `weapon_type` 2.

| property | value |
|---|---|
| model | `models/jc_weapons/02_two_handed/w143_rpg_fire_leach/w143_rpg_fire_leach_projectile_body.model_xml` |
| tune | `editor/entities/jc_weapons/06_vehicle/w618_sportsmuscle_missile/w618_sportsmuscle_missile.wtune` |
| autoaim | `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtune` |
| collision | `models/jc_weapons/02_two_handed/w143_rpg_fire_leach/w143_rpg_fire_leach_projectile_body_col.pfx` |
| rigid-object effects | `editor/entities/jc_environments/shared/rigid_object_effect_settings_default.etune` |

Slots: `main_weapon` (`id:851CAABE`) → this component; `id:00568A74`, `mounted_weapon`, `id:AC0BC788` → null.

The component carries 4 `SWeaponPoint`s and 4 `SAttachedEffect` muzzles under one `SEffects`. Each point's position equals its muzzle's position; `--check` asserts the pairing.

| point | type | fire_effect | position (x, y, z) | muzzle |
|---|---|---|---|---|
| `internal.fire_point.0` | 2 | 0 | 0.182, 1.085, -1.566 | `fire` |
| `internal.fire_point.1` | 2 | 1 | 0.058, 1.085, -1.566 | `fire2` |
| `internal.fire_point.2` | 2 | 2 | -0.063, 1.085, -1.566 | `fire3` |
| `internal.fire_point.3` | 2 | 3 | -0.19, 1.085, -1.566 | `fire4` |

All muzzles share effect hash `667364510` → `effects/jc_weapons/muzzle_flash/sportsmuscle_missile_muzzleflash.effc`.

Aim: `CAimPOIWeaponComponent` `aim.poi`, `id:2D0B3C09` = 50.


## 4. Parts modules

| | civilian | signature_preorder |
|---|---|---|
| module | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_vehicle_parts.vmodc` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/sportsmuscle_vehicle_parts.vmodc` |
| size / sha1 | 29886 B `23f0bcc8ff57` | 30382 B `627fd438e6fd` |
| parts defined | 42 | 42 |
| parts instantiated by the `epe` | 40 | 41 |

The two modules are the same part set: 42 names at the same indices, no part only in one of them. Changed fields across the shared parts: `model`, `model_swap`.

The instantiated tree is the difference, not the definitions. Each `epe` builds only the hood branch it needs: the civilian tree holds 40 of the 42 parts and leaves out `25`, `41`; the signature tree holds 41 and leaves out `24`. Everything else is shared.

| index | name | field | civilian | variant |
|---|---|---|---|---|
| 0 | `sportsmuscle_body` | `model` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_body.lod` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/signature_sportsmuscle_body.lod` |
| 1 | `sportsmuscle_door_f_l` | `model` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_door_f_l.lod` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/signature_sportsmuscle_door_f_l.lod` |
| 2 | `sportsmuscle_door_f_r` | `model` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_door_f_r.lod` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/signature_sportsmuscle_door_f_r.lod` |
| 6 | `sportsmuscle_rear_bumper` | `model` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_rear_bumper.lod` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/signature_sportsmuscle_rear_bumper.lod` |
| 10 | `sportsmuscle_trunk` | `model` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_trunk.lod` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/signature_sportsmuscle_trunk.lod` |
| 11 | `sportsmuscle_wheel_r_l` | `model` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_l.lod` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/signature_sportsmuscle_wheel_r_l.lod` |
| 11 | `sportsmuscle_wheel_r_l` | `model_swap` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_lmshswap.lod` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/signature_sportsmuscle_wheel_r_lmshswap.lod` |
| 12 | `sportsmuscle_wheel_r_r` | `model` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_r.lod` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/signature_sportsmuscle_wheel_r_r.lod` |
| 12 | `sportsmuscle_wheel_r_r` | `model_swap` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_rmshswap.lod` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/signature_sportsmuscle_wheel_r_rmshswap.lod` |
| 17 | `sportsmuscle_l_mirror` | `model` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_l_mirror.lod` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/signature_sportsmuscle_l_mirror.lod` |
| 19 | `sportsmuscle_r_mirror` | `model` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_r_mirror.lod` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/signature_sportsmuscle_r_mirror.lod` |
| 20 | `sportsmuscle_fender_l` | `model` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_fender_l.lod` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/signature_sportsmuscle_fender_l.lod` |
| 21 | `sportsmuscle_fender_r` | `model` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_fender_r.lod` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/signature_sportsmuscle_fender_r.lod` |
| 22 | `sportsmuscle_front_bumper` | `model` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_front_bumper.lod` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/signature_sportsmuscle_front_bumper.lod` |
| 23 | `sportsmuscle_grill` | `model` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_grill.lod` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/signature_sportsmuscle_grill.lod` |
| 24 | `sportsmuscle_hood` | `model` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_hood.lod` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/signature_sportsmuscle_hood.lod` |
| 25 | `sportsmuscle_hood_signature` | `model` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_hood_signature.lod` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/signature_sportsmuscle_hood_signature.lod` |
| 26 | `sportsmuscle_wheel_f_l` | `model` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_f_l.lod` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/signature_sportsmuscle_wheel_f_l.lod` |
| 26 | `sportsmuscle_wheel_f_l` | `model_swap` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_f_lmshswap.lod` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/signature_sportsmuscle_wheel_f_lmshswap.lod` |
| 27 | `sportsmuscle_wheel_f_r` | `model` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_f_r.lod` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/signature_sportsmuscle_wheel_f_r.lod` |
| 27 | `sportsmuscle_wheel_f_r` | `model_swap` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_f_rmshswap.lod` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/signature_sportsmuscle_wheel_f_rmshswap.lod` |
| 33 | `sportsmuscle_c_mirror` | `model` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_c_mirror.lod` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/signature_sportsmuscle_c_mirror.lod` |
| 41 | `sportsmuscle_missile_base_signature` | `model` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_missile_base_signature.lod` | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/signature_sportsmuscle_missile_base_signature.lod` |

The signature module's part rows (this is the definition the `epe` instantiates from):

| i | part | behaviour | damage type | parent | model |
|---|---|---|---|---|---|
| 0 | `sportsmuscle_body` | None | Land_Body | -1 | `signature/signature_sportsmuscle_body.lod` |
| 1 | `sportsmuscle_door_f_l` | FrontLeftDoor | Land_Door | 0 | `signature/signature_sportsmuscle_door_f_l.lod` |
| 2 | `sportsmuscle_door_f_r` | FrontRightDoor | Land_Door | 0 | `signature/signature_sportsmuscle_door_f_r.lod` |
| 3 | `sportsmuscle_engine` | None | Land_Engine | 0 | `sportsmuscle_engine.lod` |
| 4 | `sportsmuscle_f_l_seat` | None | Land_Seat | 0 | `sportsmuscle_f_l_seat.lod` |
| 5 | `sportsmuscle_f_r_seat` | None | Land_Seat | 0 | `sportsmuscle_f_r_seat.lod` |
| 6 | `sportsmuscle_rear_bumper` | None | Land_Bumper | 0 | `signature/signature_sportsmuscle_rear_bumper.lod` |
| 7 | `sportsmuscle_steeringwheel` | None | Land_Steering_Wheel | 0 | `sportsmuscle_steeringwheel.lod` |
| 8 | `sportsmuscle_taillight_r_l` | None | Land_Light | 0 | `sportsmuscle_taillight_r_l.lod` |
| 9 | `sportsmuscle_taillight_r_r` | None | Land_Light | 0 | `sportsmuscle_taillight_r_r.lod` |
| 10 | `sportsmuscle_trunk` | None | Land_Trunk | 0 | `signature/signature_sportsmuscle_trunk.lod` |
| 11 | `sportsmuscle_wheel_r_l` | Wheel | Land_Wheel | 0 | `signature/signature_sportsmuscle_wheel_r_l.lod` |
| 12 | `sportsmuscle_wheel_r_r` | Wheel | Land_Wheel | 0 | `signature/signature_sportsmuscle_wheel_r_r.lod` |
| 13 | `sportsmuscle_window_f` | Windshield | Land_Stunt_Window | 0 | `sportsmuscle_window_f.lod` |
| 14 | `sportsmuscle_window_r_l` | RearLeftWindow | Land_Window | 0 | `sportsmuscle_window_r_l.lod` |
| 15 | `sportsmuscle_window_r_r` | RearRightWindow | Land_Window | 0 | `sportsmuscle_window_r_r.lod` |
| 16 | `sportsmuscle_door_f_l_window` | FrontLeftWindow | Land_Window | 1 | `sportsmuscle_door_f_l_window.lod` |
| 17 | `sportsmuscle_l_mirror` | None | Land_Wing_Mirror | 1 | `signature/signature_sportsmuscle_l_mirror.lod` |
| 18 | `sportsmuscle_door_f_r_window` | FrontRightWindow | Land_Window | 2 | `sportsmuscle_door_f_r_window.lod` |
| 19 | `sportsmuscle_r_mirror` | None | Land_Wing_Mirror | 2 | `signature/signature_sportsmuscle_r_mirror.lod` |
| 20 | `sportsmuscle_fender_l` | None | Land_Fender | 3 | `signature/signature_sportsmuscle_fender_l.lod` |
| 21 | `sportsmuscle_fender_r` | None | Land_Fender | 3 | `signature/signature_sportsmuscle_fender_r.lod` |
| 22 | `sportsmuscle_front_bumper` | None | Land_Bumper | 3 | `signature/signature_sportsmuscle_front_bumper.lod` |
| 23 | `sportsmuscle_grill` | None | Land_Grill | 3 | `signature/signature_sportsmuscle_grill.lod` |
| 24 | `sportsmuscle_hood` | None | Land_Generic | 3 | `signature/signature_sportsmuscle_hood.lod` |
| 25 | `sportsmuscle_hood_signature` | Hood | Land_Hood | 3 | `signature/signature_sportsmuscle_hood_signature.lod` |
| 26 | `sportsmuscle_wheel_f_l` | Wheel | Land_Wheel | 3 | `signature/signature_sportsmuscle_wheel_f_l.lod` |
| 27 | `sportsmuscle_wheel_f_r` | Wheel | Land_Wheel | 3 | `signature/signature_sportsmuscle_wheel_f_r.lod` |
| 28 | `sportsmuscle_plate_r` | None | Land_Generic | 10 | `sportsmuscle_plate_r.lod` |
| 29 | `sportsmuscle_signal_r_l` | None | Land_Light | 10 | `sportsmuscle_signal_r_l.lod` |
| 30 | `sportsmuscle_signal_r_r` | None | Land_Light | 10 | `sportsmuscle_signal_r_r.lod` |
| 31 | `sportsmuscle_taillight_r_c` | None | Land_Generic | 10 | `sportsmuscle_taillight_r_c.lod` |
| 32 | `sportsmuscle_trunk_window` | RearWindow | Land_Stunt_Window | 10 | `sportsmuscle_trunk_window.lod` |
| 33 | `sportsmuscle_c_mirror` | None | Boat_Antenna | 13 | `signature/signature_sportsmuscle_c_mirror.lod` |
| 34 | `sportsmuscle_headlight_f_l_01` | None | Land_Light | 20 | `sportsmuscle_headlight_f_l_01.lod` |
| 35 | `sportsmuscle_headlight_f_l_02` | None | Land_Light | 20 | `sportsmuscle_headlight_f_l_02.lod` |
| 36 | `sportsmuscle_signal_f_l` | None | Land_Light | 20 | `sportsmuscle_signal_f_l.lod` |
| 37 | `sportsmuscle_headlight_f_r_01` | None | Land_Light | 21 | `sportsmuscle_headlight_f_r_01.lod` |
| 38 | `sportsmuscle_headlight_f_r_02` | None | Land_Light | 21 | `sportsmuscle_headlight_f_r_02.lod` |
| 39 | `sportsmuscle_signal_f_r` | None | Land_Light | 21 | `sportsmuscle_signal_f_r.lod` |
| 40 | `sportsmuscle_plate_f` | None | Land_Generic | 22 | `sportsmuscle_plate_f.lod` |
| 41 | `sportsmuscle_missile_base_signature` | None | Land_Generic | 25 | `signature/signature_sportsmuscle_missile_base_signature.lod` |

`PARTS_TABLE.jsonl` cross-check: both rows match the decoded modules (42 and 42 parts, same names and models).


## 5. Meshes

198 `.rbm` vs 203. **84 pairs** share a stem (base path → `signature/` path); **84** have the same block count and the same AABB. Size deltas: [-141, -47, -21, -15, -7, -4, 44].

| stem | blocks | Δ bytes | AABB equal |
|---|---|---|---|
| `sportsmuscle_body_lod1.rbm` | 9→9 | -141 | yes |
| `sportsmuscle_body_lod2.rbm` | 9→9 | -141 | yes |
| `sportsmuscle_body_lod3.rbm` | 9→9 | -141 | yes |
| `sportsmuscle_body_lod4.rbm` | 9→9 | -21 | yes |
| `sportsmuscle_body_lod5.rbm` | 9→9 | -15 | yes |
| `sportsmuscle_c_mirror_lod1.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_c_mirror_lod2.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_c_mirror_lod3.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_c_mirror_lod4.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_door_f_l_lod1.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_door_f_l_lod2.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_door_f_l_lod3.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_door_f_l_lod4.rbm` | 9→9 | -7 | yes |
| `sportsmuscle_door_f_r_lod1.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_door_f_r_lod2.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_door_f_r_lod3.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_door_f_r_lod4.rbm` | 9→9 | -7 | yes |
| `sportsmuscle_fender_l_lod1.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_fender_l_lod2.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_fender_l_lod3.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_fender_r_lod1.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_fender_r_lod2.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_fender_r_lod3.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_front_bumper_lod1.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_front_bumper_lod2.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_front_bumper_lod3.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_grill_lod1.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_grill_lod2.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_grill_lod3.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_hood_lod1.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_hood_lod2.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_hood_lod3.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_hood_signature_lod1.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_hood_signature_lod2.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_hood_signature_lod3.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_l_mirror_lod1.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_l_mirror_lod2.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_l_mirror_lod3.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_l_mirror_lod4.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_missile_base_signature_lod1.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_missile_base_signature_lod2.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_missile_base_signature_lod3.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_r_mirror_lod1.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_r_mirror_lod2.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_r_mirror_lod3.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_r_mirror_lod4.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_rear_bumper_lod1.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_rear_bumper_lod2.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_rear_bumper_lod3.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_rear_bumper_lod4.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_trunk_lod1.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_trunk_lod2.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_trunk_lod3.rbm` | 9→9 | -47 | yes |
| `sportsmuscle_trunk_lod4.rbm` | 9→9 | -4 | yes |
| `sportsmuscle_wheel_f_l_lod1.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_f_l_lod2.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_f_l_lod3.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_f_lmshswap_lod1.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_f_lmshswap_lod2.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_f_lmshswap_lod3.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_f_r_lod1.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_f_r_lod2.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_f_r_lod3.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_f_rmshswap_lod1.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_f_rmshswap_lod2.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_f_rmshswap_lod3.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_r_l_lod1.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_r_l_lod2.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_r_l_lod3.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_r_l_lod4.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_r_l_lod5.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_r_lmshswap_lod1.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_r_lmshswap_lod2.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_r_lmshswap_lod3.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_r_lmshswap_lod4.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_r_r_lod1.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_r_r_lod2.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_r_r_lod3.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_r_r_lod4.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_r_r_lod5.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_r_rmshswap_lod1.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_r_rmshswap_lod2.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_r_rmshswap_lod3.rbm` | 9→9 | +44 | yes |
| `sportsmuscle_wheel_r_rmshswap_lod4.rbm` | 9→9 | +44 | yes |

Added meshes with no base counterpart:

| mesh | size | blocks |
|---|---|---|
| `w143_rpg_fire_leach_projectile_body_lod1.rbm` | 58438 | 8 |
| `w143_rpg_fire_leach_projectile_body_lod2.rbm` | 23958 | 8 |
| `w143_rpg_fire_leach_projectile_body_lod3.rbm` | 13830 | 8 |
| `w143_rpg_fire_leach_projectile_body_lod4.rbm` | 8494 | 8 |
| `w143_rpg_fire_leach_projectile_body_lod5.rbm` | 5286 | 8 |

## 6. The `w618` tune and the blast

The weapon component stores its tune under the hashed property `AA7096C9` (`tuning_file`): `editor/entities/jc_weapons/06_vehicle/w618_sportsmuscle_missile/w618_sportsmuscle_missile.wtune`. Autoaim: `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtune`.

| tune member | value |
|---|---|
| `tuning.base_tuning.damage` | 1500 |
| `tuning.base_tuning.impulse` | 350 |
| `tuning.base_tuning.vehicle_damage_factor` | 1 |
| `tuning.base_tuning.object_damage_factor` | 1 |
| `tuning.missile_base_tuning.missile_turning_speed` | 0 |
| `tuning.missile_base_tuning.missile_loose_lock_distance` | 0 |
| `tuning.missile_base_tuning.gravity` | -9.82 |
| `ai_tuning.base_tuning.damage` | 30 |
| `ai_tuning.ai_base_tuning.range[0]` | 10 |
| `ai_tuning.ai_base_tuning.range[1]` | 100 |
| `magazine_size` | -1 |
| `max_range` | 300 |
| `fire_rate` | 0.5 |
| `burst_count` | 1 |
| `unlimited_ammo` | 1 |

The signature container embeds a **12773 B** copy of the wire tune; the VFS path resolves to the patch entry at **14244 B** (`patch`). Decoded, the patch copy has 155 rows and the embedded copy 148; the diff is **7 fields**, all absent from the embedded copy:

- `ai_tuning.missile_base_tuning.meters_proximity_self_detonate`: VFS `0`, embedded absent
- `ai_tuning.missile_base_tuning.meters_times_speed_in_front_of_target`: VFS `0`, embedded absent
- `ai_tuning.missile_base_tuning.random_detonation_offset`: VFS `0`, embedded absent
- `fire_rate_level_2`: VFS `0.12`, embedded absent
- `tuning.missile_base_tuning.meters_proximity_self_detonate`: VFS `0`, embedded absent
- `tuning.missile_base_tuning.meters_times_speed_in_front_of_target`: VFS `0`, embedded absent
- `tuning.missile_base_tuning.random_detonation_offset`: VFS `0`, embedded absent

Blast (`w618_sportsmuscle_missile.ftunec`, only embedded, no VFS entry):

| field | value |
|---|---|
| `PlayerDamage` | 1100 |
| `PlayerDamageRadius` | 8 |
| `PlayerDamageRadiusPercentageMax` | 0.15 |
| `AIDamage` | 500 |
| `AIDamageRadius` | 8 |


## 7. `.ee.toc` (the load list)

468 records vs 498, of which 30 / 38 are offset-0 (load from the global archives, not from this container). Added 162, removed 132.

| kind | added | removed |
|---|---|---|
| effect | 11 | 0 |
| graph | 1 | 1 |
| lod | 24 | 23 |
| mesh | 89 | 84 |
| meta | 2 | 2 |
| module | 2 | 3 |
| other | 4 | 0 |
| physics | 1 | 0 |
| texture | 25 | 19 |
| tune | 3 | 0 |

## 8. What B-05/B-06 must carry

* **Two `CPartProp` nodes, not a new parts module.** The signature `epe` drops the plain `sportsmuscle_hood` part and adds `sportsmuscle_hood_signature` (index 25) with `sportsmuscle_missile_base_signature` (index 41) as its child. The parts module already defines both at every index in both variants; the instantiated tree is what changes.
* **Part indices are stable**: the modules define the same 42 parts at the same indices, and the two `epe`s differ only by which hood branch they build, so the port keeps every index and adds nothing at the end.
* **The art is a path swap on the parts the kit restyles.** 19 of the 42 parts point at `signature/signature_*.lod`; the rest keep the base model. The paired `.rbm` files have the same block counts and the same AABBs, i.e. the kit is the same shell recompiled against the signature textures, not new geometry. A port should copy the part *links* and its own meshes, not assume a new shape.
* **The root's content ids follow the kit.** `vehicle_parts` switches to the signature module hash (the one decoded in section 4), `decals` to a different hash, and `palette` is cleared to null in the variant, so the signature look is not a palette swap.
* **The weapon is a four-tube missile pod on the hood.** One `CMissileWeaponBase` (`w618_sportsmuscle_missile`) with four type-2 `internal.fire_point.N` points, one `CAimPOIWeaponComponent`, four `SAttachedEffect` muzzle flashes (all `sportsmuscle_missile_muzzleflash.effc`, one per tube, at the tube positions), one `CForcePulse` (`...w618...ftune`) and one `CMaterialEffectTable` (`tank_explosion_effect_table`). The root `main_weapon` (`851CAABE`) is the only slot it uses; the other three are null.
* **The missile reuses the RPG fire-leach projectile**, not a unique mesh: the component's model is `w143_rpg_fire_leach_projectile_body.model_xml`, and the signature container adds that mesh's five LODs and four textures.
* **The tune is unguided and unlimited**: `missile_turning_speed` 0, no lock-on, `magazine_size` -1, `fire_rate` 0.5 s, `damage` 1500, `max_range` 300 m, blast 1100 player / 500 AI in 8 m. Copy the tune values, not only the wiring.
* **The interaction graph is unchanged.** Only the stunt-hood area name changes (`front_area` → `front_signature_area`). No seat, entry, exit or trigger is added, so the port does not need a new seat or action.
* **Two root scalars remain unnamed** (`id:EA011E72` float 0.3→1, `id:FFE31EE1` int 1→0); no Jenkins candidate in the shipped vocabulary matched either. They are recorded, not guessed, and neither is a weapon slot.
* **The VFS tune is the authoritative copy.** The container embeds an older 148-row `wtunec`; the patch path has 155 rows. The seven extras are six zero-valued schema members plus `fire_rate_level_2` = 0.12; values on the shared rows are identical.


## 9. Validation and limits

`jc3sigdiff.py --check` re-reads both `.ee`s out of the archives, converts the inner `.epe`s again, rebuilds every section and compares `SIGNATURE_DIFF.json` field-for-field and `SIGNATURE_DIFF.md` byte-for-byte. It also asserts: the civilian has 0 weapon slots and the variant 1; every variant part model the kit restyles points at `signature/` and no civilian part does; the changed part fields are only model, model_swap; the two `epe`s instantiate 40 and 41 parts and differ only by the hood branch they build; the weapon has four fire points, each paired by position with its own muzzle, all four naming one effect path; all 84 mesh pairs keep their block count and AABB (84 of 84); the tune path in the graph exists as a VFS entry.

**Limits.** The mesh comparison is header-level (block count, AABB, size); it does not decode vertex data, so `aabb_equal` means the same bounds, not the same vertices. `CMaterialEffectTable` is an opaque 30-byte hash blob (class `CMaterialEffectTable`); its contents are not decoded. The two unnamed root scalars are reported without a name. The diff is between these two entity builds only; no other v0300 variant is compared.
