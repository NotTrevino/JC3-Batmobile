# Turrets and cannons - how JC3 moves and aims them

G2-13. The short answer: a turret is **two parts and two Havok hinges**, not a special object. The yaw part carries behaviour `Turret`, the pitch part carries `Cannon`, each is one `hkpLimitedHingeConstraintData` in the vehicle's `.physicsc`, and the weapon's fire point names both parts in two unnamed string properties. The parts module's `aim_part_constraints` array is **not** turret aim - it is the suspension linkage.

## 1. The medium tank (v0201) - the full chain

| | |
|---|---|
| yaw part | `mediumtank_turret`, index 26, behaviour `Turret`, parent 0 (body) |
| yaw hinge | constraint 2, pivot (0, 2.2812, 1.1382), axis +Y, **-179 .. +179 deg** |
| pitch part | `mediumtank_cannon`, index 38, behaviour `Cannon`, parent 26 |
| pitch hinge | constraint 0, pivot (0, 2.5347, 0), axis +X, **-5 .. +20 deg** |
| hatch | `mediumtank_hatch`, index 39, `FrontLeftDoor`, parent 26, constraint 1, pivot (-0.4848, 2.921, 1.4785), axis +X, **0 .. 130 deg** |
| weapon | `w602_mediumtank_canon`, binding `main_weapon` |
| fire point | `fire_position_0` at local (0, 0.3739, -5.8174); names yaw `mediumtank_turret` and pitch `mediumtank_cannon` |
| counts | 42 parts, 3 constraints, all `hkpLimitedHingeConstraintData`, no ragdoll |

The cannon pivots on X 0.25 m above the turret ring and its fire point sits 5.82 m forward, so the muzzle swings with the pitch hinge. `parent_space_offset` is identity on both parts, and the pivots are printed as the packfile stores them: on this vehicle they land exactly where the art puts the ring and the trunnion. Neither part names a rotation speed.

## 2. The sampled vehicles

### v0201 medium tank

`v0201_car_capstone_mediumtank_military_01.ee` - 42 parts, 3 constraint objects (hkpLimitedHingeConstraintData 3); `aim_part_constraints` rows 0, `hinged_parts` rows 0, `rotating_parts` rows 0.

- mount path for `mediumtank_turret`: `mediumtank_body` (None) -> `mediumtank_turret` (Turret)
- mount path for `mediumtank_cannon`: `mediumtank_body` (None) -> `mediumtank_turret` (Turret) -> `mediumtank_cannon` (Cannon)

| part | i | behaviour | parent | constraint | class | pivot (x, y, z) | axis | min..max (deg) |
|---|---|---|---|---|---|---|---|---|
| `mediumtank_cannon` | 38 | Cannon | 26 | 0 | `hkpLimitedHingeConstraintData` | 0, 2.5347, 0 | 1, 0, 0 | -5 .. 20 |
| `mediumtank_hatch` | 39 | FrontLeftDoor | 26 | 1 | `hkpLimitedHingeConstraintData` | -0.4848, 2.921, 1.4785 | 1, 0, 0 | 0 .. 130 |
| `mediumtank_turret` | 26 | Turret | 0 | 2 | `hkpLimitedHingeConstraintData` | 0, 2.2812, 1.1382 | -0, 1, 0 | -179 .. 179 |

Weapon points that name the moving parts:

| weapon | binding | point | yaw part | pitch part | point xyz |
|---|---|---|---|---|---|
| `w602_mediumtank_canon` | main_weapon | `fire_position_0` | `mediumtank_turret` | `mediumtank_cannon` | 0, 0.3739, -5.8174 |

Aim objects:

| class | name | min_aim_distance | xyz |
|---|---|---|---|
| `STargetPoint` | `AutoAimTargetPoint` | -1 | 0, 1, 0 |

### v0202 Bavarium tank

`v0202_car_capstone_bavariumtank_military_01.ee` - 38 parts, 15 constraint objects (hkpLimitedHingeConstraintData 15); `aim_part_constraints` rows 0, `hinged_parts` rows 0, `rotating_parts` rows 0.

- mount path for `bavariumtank_turret`: `bavariumtank_body` (None) -> `bavariumtank_turret` (Turret)
- mount path for `bavariumtank_cannon`: `bavariumtank_body` (None) -> `bavariumtank_turret` (Turret) -> `bavariumtank_cannon` (Cannon)

| part | i | behaviour | parent | constraint | class | pivot (x, y, z) | axis | min..max (deg) |
|---|---|---|---|---|---|---|---|---|
| `bavariumtank_cannon` | 34 | Cannon | 24 | 0 | `hkpLimitedHingeConstraintData` | 0, 2.5347, 0 | 1, 0, 0 | -5 .. 20 |
| `bavariumtank_hatch` | 35 | FrontLeftDoor | 24 | 1 | `hkpLimitedHingeConstraintData` | -0.4921, 2.8222, 1.4826 | 0.9992, -0.0398, 0 | 0 .. 130 |
| `bavariumtank_skirt_l_1` | 8 | None | 0 | 3 | `hkpLimitedHingeConstraintData` | -1.9219, 1.627, -2.1649 | 0, -0, -1 | 0 .. 30 |
| `bavariumtank_skirt_l_2` | 9 | None | 0 | 4 | `hkpLimitedHingeConstraintData` | -1.9235, 1.6314, -0.4543 | 0, -0, -1 | 0 .. 30 |
| `bavariumtank_skirt_l_3` | 10 | None | 0 | 5 | `hkpLimitedHingeConstraintData` | -1.9113, 1.6263, 0.5525 | 0, -0, -1 | 0 .. 30 |
| `bavariumtank_skirt_l_4` | 11 | None | 0 | 6 | `hkpLimitedHingeConstraintData` | -1.9215, 1.6296, 1.2993 | 0, -0, -1 | 0 .. 30 |
| `bavariumtank_skirt_l_5` | 12 | None | 0 | 7 | `hkpLimitedHingeConstraintData` | -1.9171, 1.6275, 2.3494 | 0, -0, -1 | 0 .. 30 |
| `bavariumtank_skirt_l_6` | 13 | None | 0 | 8 | `hkpLimitedHingeConstraintData` | -1.9141, 1.63, 3.1514 | 0, -0, -1 | 0 .. 30 |
| `bavariumtank_skirt_r_1` | 14 | None | 0 | 9 | `hkpLimitedHingeConstraintData` | 1.9199, 1.6297, -2.1873 | 0, 0, 1 | 0 .. 30 |
| `bavariumtank_skirt_r_2` | 15 | None | 0 | 10 | `hkpLimitedHingeConstraintData` | 1.9224, 1.6297, -0.914 | 0, 0, 1 | 0 .. 30 |
| `bavariumtank_skirt_r_3` | 16 | None | 0 | 11 | `hkpLimitedHingeConstraintData` | 1.9246, 1.6328, 0.3749 | 0, 0, 1 | 0 .. 30 |
| `bavariumtank_skirt_r_4` | 17 | None | 0 | 12 | `hkpLimitedHingeConstraintData` | 1.9186, 1.6258, 1.1986 | 0, 0, 1 | 0 .. 30 |
| `bavariumtank_skirt_r_5` | 18 | None | 0 | 13 | `hkpLimitedHingeConstraintData` | 1.9191, 1.629, 2.1732 | 0, 0, 1 | 0 .. 30 |
| `bavariumtank_skirt_r_6` | 19 | None | 0 | 14 | `hkpLimitedHingeConstraintData` | 1.9169, 1.6297, 3.173 | 0, 0, 1 | 0 .. 30 |
| `bavariumtank_turret` | 24 | Turret | 0 | 2 | `hkpLimitedHingeConstraintData` | 0, 2.2812, 1.1382 | -0, 1, 0 | -179 .. 179 |

Weapon points that name the moving parts:

| weapon | binding | point | yaw part | pitch part | point xyz |
|---|---|---|---|---|---|
| `w602_mediumtank_canon` | main_weapon | `fire_position_0` | `bavariumtank_turret` | `bavariumtank_cannon` | 0, 0.3739, -5.8174 |

Aim objects:

| class | name | min_aim_distance | xyz |
|---|---|---|---|
| `STargetPoint` | `AutoAimTargetPoint` | -1 | 0, 1, 0 |

### v0603 small tank

`v0603_car_urga_smalltank_military_01.ee` - 37 parts, 17 constraint objects (hkpLimitedHingeConstraintData 16, hkpRagdollConstraintData 1); `aim_part_constraints` rows 0, `hinged_parts` rows 0, `rotating_parts` rows 0.

- mount path for `smalltank_turret`: `smalltank_body` (None) -> `smalltank_turret` (Turret)
- mount path for `smalltank_cannon`: `smalltank_body` (None) -> `smalltank_turret` (Turret) -> `smalltank_cannon` (Cannon)

| part | i | behaviour | parent | constraint | class | pivot (x, y, z) | axis | min..max (deg) |
|---|---|---|---|---|---|---|---|---|
| `smalltank_cannon` | 32 | Cannon | 10 | 11 | `hkpLimitedHingeConstraintData` | 0, 1.9143, -0.3611 | 1, 0, 0 | -5 .. 25 |
| `smalltank_hatch` | 33 | FrontLeftDoor | 10 | 12 | `hkpLimitedHingeConstraintData` | -0.4558, 2.6627, 1.3729 | 1, 0, 0 | 0 .. 90 |
| `smalltank_bumper_f` | 1 | None | 0 | 0 | `hkpLimitedHingeConstraintData` | 0.5617, 0.8167, -2.33 | 0, 0, 1 | 0 .. 32 |
| `smalltank_cloth_net` | 2 | None | 0 | 1 | `hkpLimitedHingeConstraintData` | -0.0128, 1.3585, 2.3377 | -1, 0, 0 | 0 .. 20 |
| `smalltank_fender_f_l` | 3 | None | 0 | 2 | `hkpLimitedHingeConstraintData` | -0.8483, 1.4454, -1.3336 | 0.1665, 0, -0.986 | -20 .. 0 |
| `smalltank_fender_f_r` | 4 | None | 0 | 4 | `hkpLimitedHingeConstraintData` | 0.8429, 1.442, -1.3369 | 0.1768, 0, 0.9842 | -20 .. 0 |
| `smalltank_hatch_f_c` | 7 | None | 0 | 8 | `hkpLimitedHingeConstraintData` | -0.0395, 1.3521, -1.8345 | 0.9988, 0.0266, 0.0413 | 0 .. 15 |
| `smalltank_hatch_f_l` | 8 | None | 0 | 9 | `hkpLimitedHingeConstraintData` | -0.5226, 1.6458, -0.6675 | 1, -0.0065, -0.0058 | 0 .. 14 |
| `smalltank_hatch_f_r` | 9 | None | 0 | 10 | `hkpLimitedHingeConstraintData` | 0.5751, 1.6458, -0.6675 | 1, -0, 0 | 0 .. 14 |
| `smalltank_mudflap_f_l` | 19 | None | 3 | 3 | `hkpLimitedHingeConstraintData` | -1.1185, 0.5855, -0.6532 | -0.9543, 0, -0.2987 | -7.826 .. 6.622 |
| `smalltank_mudflap_f_r` | 23 | None | 4 | 5 | `hkpLimitedHingeConstraintData` | 1.1444, 0.5855, -0.6647 | -0.9602, 0, 0.2795 | -6.622 .. 6.622 |
| `smalltank_mudflap_r_l` | 25 | None | 5 | 6 | `hkpLimitedHingeConstraintData` | -1.0436, 1.0081, 2.3497 | -1, 0, 0 | -6.622 .. 7.826 |
| `smalltank_mudflap_r_r` | 28 | None | 6 | 7 | `hkpLimitedHingeConstraintData` | 1.024, 1.0081, 2.3497 | -1, 0, 0 | -5.418 .. 5.4 |
| `smalltank_hatch_c` | 34 | None | 10 | 13 | `hkpLimitedHingeConstraintData` | -0.0234, 2.3475, 0.0314 | -1, 0, 0 | 0 .. 12 |
| `smalltank_hatch_r_l` | 35 | None | 10 | 14 | `hkpLimitedHingeConstraintData` | 0.3229, 2.4059, 1.8392 | 1, 0, 0 | 0 .. 12 |
| `smalltank_rack` | 36 | None | 10 | 15 | `hkpRagdollConstraintData` | - | - | - |
| `smalltank_turret` | 10 | Turret | 0 | 16 | `hkpLimitedHingeConstraintData` | 0, 1.8131, 0.5247 | -0, 1, 0 | -179 .. 179 |

Weapon points that name the moving parts:

| weapon | binding | point | yaw part | pitch part | point xyz |
|---|---|---|---|---|---|
| `w605_smalltank_canon` | main_weapon | `fire_position_0` | `smalltank_turret` | `smalltank_cannon` | 0, 0, -3.3 |

Aim objects:

| class | name | min_aim_distance | xyz |
|---|---|---|---|
| `STargetPoint` | `AutoAimTargetPoint` | -1 | 0, 1, 0 |

### v0200 APC

`v0200_car_capstone_apc_military_01.ee` - 45 parts, 16 constraint objects (hkpLimitedHingeConstraintData 16); `aim_part_constraints` rows 0, `hinged_parts` rows 0, `rotating_parts` rows 0.

- mount path for `apc_turret_base`: `apc_body` (Body) -> `apc_turret_base` (Turret)
- mount path for `apc_weapon_mount_vertical`: `apc_body` (Body) -> `apc_turret_base` (Turret) -> `apc_weapon_mount_vertical` (Cannon)

| part | i | behaviour | parent | constraint | class | pivot (x, y, z) | axis | min..max (deg) |
|---|---|---|---|---|---|---|---|---|
| `apc_weapon_mount_vertical` | 44 | Cannon | 30 | 14 | `hkpLimitedHingeConstraintData` | -0, 2.7313, 0.5942 | 1, 0, 0 | -15 .. 50 |
| `apc_door_c_l` | 8 | CenterLeftDoor | 0 | 6 | `hkpLimitedHingeConstraintData` | -1.3462, 1.6462, 0.8936 | 0, -1, 0 | 0 .. 100 |
| `apc_door_c_r` | 9 | CenterRightDoor | 0 | 7 | `hkpLimitedHingeConstraintData` | 1.3462, 1.6438, 0.8936 | 0, 1, 0 | 0 .. 100 |
| `apc_hatch_l` | 12 | FrontLeftDoor | 0 | 9 | `hkpLimitedHingeConstraintData` | -0.5003, 2.0861, -0.2843 | 1, 0, 0 | 0 .. 130 |
| `apc_armor_c_l` | 1 | None | 0 | 0 | `hkpLimitedHingeConstraintData` | -1.3878, 1.708, 2.119 | 0, 0, 1 | -5 .. 3 |
| `apc_armor_c_r` | 2 | None | 0 | 1 | `hkpLimitedHingeConstraintData` | 1.3878, 1.708, 2.121 | 0, 0, 1 | -3 .. 5 |
| `apc_armor_f_l` | 3 | None | 0 | 2 | `hkpLimitedHingeConstraintData` | -1.3878, 1.708, 0.3096 | 0, 0, 1 | -5 .. 3 |
| `apc_armor_f_r` | 4 | None | 0 | 3 | `hkpLimitedHingeConstraintData` | 1.3878, 1.708, 0.3112 | 0, 0, 1 | -3 .. 5 |
| `apc_armor_r_l` | 5 | None | 0 | 4 | `hkpLimitedHingeConstraintData` | -0.668, 1.1062, 2.9625 | -1, 0, 0 | -3 .. 5 |
| `apc_armor_r_r` | 6 | None | 0 | 5 | `hkpLimitedHingeConstraintData` | 0.6714, 1.1062, 2.9625 | -1, 0, 0 | -3 .. 5 |
| `apc_hatch_r` | 13 | None | 0 | 10 | `hkpLimitedHingeConstraintData` | 0.6198, 1.9099, -1.1154 | 1, 0, 0 | 0 .. 130 |
| `apc_ring_f_l` | 20 | None | 0 | 11 | `hkpLimitedHingeConstraintData` | -0.7529, 0.6316, -2.7093 | 1, -0, 0 | -10 .. 10 |
| `apc_ring_f_r` | 21 | None | 0 | 12 | `hkpLimitedHingeConstraintData` | 0.75, 0.6316, -2.7093 | 1, -0, 0 | -10 .. 10 |
| `apc_door_r` | 10 | RearLeftDoor | 0 | 8 | `hkpLimitedHingeConstraintData` | -0.4252, 1.7576, 2.8991 | 0.0012, -1, 0.0022 | 0 .. 95 |
| `apc_turret_base` | 30 | Turret | 0 | 15 | `hkpLimitedHingeConstraintData` | -0.0037, 2.1367, 1.3048 | -0, 1, 0 | -179 .. 179 |
| `apc_turret_hatch` | 42 | TurretDoor | 30 | 13 | `hkpLimitedHingeConstraintData` | -0.0037, 2.2565, 1.7134 | 1, 0, 0 | 0 .. 130 |

Weapon points that name the moving parts:

| weapon | binding | point | yaw part | pitch part | point xyz |
|---|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | mounted_weapon | `attach.vehicle` | `apc_turret_base` | `apc_weapon_mount_vertical` | 0, -0.0541, 0.0021 |

Aim objects:

| class | name | min_aim_distance | xyz |
|---|---|---|---|
| `STargetPoint` | `AutoAimTargetPoint` | -1 | 0, 1, 0 |

### v0600 armoured jeep

`v0600_car_urga_armoredjeep_military_01.ee` - 67 parts, 19 constraint objects (hkpLimitedHingeConstraintData 16, hkpRagdollConstraintData 3); `aim_part_constraints` rows 0, `hinged_parts` rows 0, `rotating_parts` rows 0.

- mount path for `armoredjeep_turret_base`: `armoredjeep_body` (None) -> `armoredjeep_turret_base` (Turret)
- mount path for `armoredjeep_weapon_mount_vertical`: `armoredjeep_body` (None) -> `armoredjeep_turret_base` (Turret) -> `armoredjeep_weapon_mount_horizontal` (None) -> `armoredjeep_weapon_mount_vertical` (Cannon)

| part | i | behaviour | parent | constraint | class | pivot (x, y, z) | axis | min..max (deg) |
|---|---|---|---|---|---|---|---|---|
| `armoredjeep_weapon_mount_vertical` | 66 | Cannon | 59 | 17 | `hkpLimitedHingeConstraintData` | 0.5099, 2.2898, -0.3751 | 1, 0, 0 | -25 .. 50 |
| `armoredjeep_door_f_l` | 3 | FrontLeftDoor | 0 | 0 | `hkpLimitedHingeConstraintData` | -1.0734, 0.9908, -0.2942 | 0, -1, 0 | 0 .. 80 |
| `armoredjeep_door_f_r` | 4 | FrontRightDoor | 0 | 1 | `hkpLimitedHingeConstraintData` | 1.0745, 1.0394, -0.2913 | 0, 1, 0 | 0 .. 80 |
| `armoredjeep_hatch_f_l` | 13 | None | 0 | 8 | `hkpLimitedHingeConstraintData` | -0.5075, 1.9611, 0.5331 | 1, 0, 0 | 0 .. 9 |
| `armoredjeep_hatch_r_l` | 14 | None | 0 | 9 | `hkpLimitedHingeConstraintData` | -0.5046, 1.9596, 1.3653 | 1, 0, 0 | 0 .. 7 |
| `armoredjeep_rack_d_l` | 21 | None | 0 | 10 | `hkpLimitedHingeConstraintData` | -1.0321, 0.4675, 0.4897 | 0, 0, 1 | -30 .. 83.077 |
| `armoredjeep_rack_d_r` | 22 | None | 0 | 11 | `hkpLimitedHingeConstraintData` | 0.9865, 0.4883, 0.4545 | -0, -0, -1 | -30 .. 86 |
| `armoredjeep_rack_t_l` | 23 | None | 0 | 12 | `hkpLimitedHingeConstraintData` | -0.9317, 1.8917, 0.522 | 0, 0, 1 | 0 .. 30 |
| `armoredjeep_rack_t_r` | 24 | None | 0 | 13 | `hkpLimitedHingeConstraintData` | 0.9284, 1.9012, 0.5934 | -0, 0, -1 | 0 .. 30 |
| `armoredjeep_rear_bumper` | 25 | None | 0 | 14 | `hkpLimitedHingeConstraintData` | -0.9394, 0.9378, 2.8386 | 0, -0, -1 | 0 .. 25.714 |
| `armoredjeep_fender_l` | 44 | None | 7 | 4 | `hkpRagdollConstraintData` | - | - | - |
| `armoredjeep_fender_r` | 45 | None | 7 | 5 | `hkpRagdollConstraintData` | - | - | - |
| `armoredjeep_front_bumper` | 46 | None | 7 | 6 | `hkpRagdollConstraintData` | - | - | - |
| `armoredjeep_hood` | 48 | None | 7 | 7 | `hkpLimitedHingeConstraintData` | 0, 1.3945, -0.5246 | 1, 0, 0 | 0 .. 60 |
| `armoredjeep_trunk_hatch` | 57 | None | 33 | 15 | `hkpLimitedHingeConstraintData` | 0.0219, 1.9195, 1.8913 | -1, 0, 0 | 0 .. 60 |
| `armoredjeep_door_r_l` | 5 | RearLeftDoor | 0 | 2 | `hkpLimitedHingeConstraintData` | -1.0751, 0.9502, 0.5609 | 0, -1, 0 | 0 .. 80 |
| `armoredjeep_door_r_r` | 6 | RearRightDoor | 0 | 3 | `hkpLimitedHingeConstraintData` | 1.067, 1.0426, 0.5539 | 0, 1, 0 | 0 .. 80 |
| `armoredjeep_turret_base` | 34 | Turret | 0 | 18 | `hkpLimitedHingeConstraintData` | 0.507, 2, 0.263 | -0, 1, 0 | -179 .. 179 |
| `armoredjeep_turret_hatch` | 58 | TurretDoor | 34 | 16 | `hkpLimitedHingeConstraintData` | 0.5106, 2.0359, 0.5338 | 1, 0, 0 | 0 .. 100 |

Weapon points that name the moving parts:

| weapon | binding | point | yaw part | pitch part | point xyz |
|---|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | mounted_weapon | `mount_attach` | `armoredjeep_turret_base` | `armoredjeep_weapon_mount_vertical` | 0, 0, 0 |

Aim objects:

| class | name | min_aim_distance | xyz |
|---|---|---|---|
| `STargetPoint` | `AutoAimTargetPoint` | -1 | 0, 1, 0 |

### v0504 technical

`v0504_car_solar_technicaljeep_rebel_machinegun.ee` - 56 parts, 13 constraint objects (hkpLimitedHingeConstraintData 13); `aim_part_constraints` rows 0, `hinged_parts` rows 0, `rotating_parts` rows 0.

- mount path for `technicaljeep_rebel_turret`: `technicaljeep_body` (None) -> `technicaljeep_rebel_turret_base` (None) -> `technicaljeep_rebel_turret` (Turret)
- mount path for `technicaljeep_weapon_mount_vertical`: `technicaljeep_body` (None) -> `technicaljeep_rebel_turret_base` (None) -> `technicaljeep_rebel_turret` (Turret) -> `technicaljeep_weapon_mount_horizontal` (None) -> `technicaljeep_weapon_mount_vertical` (Cannon)

| part | i | behaviour | parent | constraint | class | pivot (x, y, z) | axis | min..max (deg) |
|---|---|---|---|---|---|---|---|---|
| `technicaljeep_weapon_mount_vertical` | 55 | Cannon | 54 | 12 | `hkpLimitedHingeConstraintData` | 0, 2.0498, 0.6697 | 1, 0, 0 | -10 .. 45 |
| `technicaljeep_door_f_l` | 9 | FrontLeftDoor | 0 | 3 | `hkpLimitedHingeConstraintData` | -0.9867, 0.9831, -1.1935 | 0, -1, 0 | 0 .. 80 |
| `technicaljeep_door_f_r` | 10 | FrontRightDoor | 0 | 5 | `hkpLimitedHingeConstraintData` | 0.9877, 0.9831, -1.1935 | 0, 1, 0 | 0 .. 80 |
| `technicaljeep_hood` | 41 | Hood | 11 | 10 | `hkpLimitedHingeConstraintData` | 0, 1.2249, -1.3059 | 1, 0, 0 | 0 .. 30 |
| `technicaljeep_ring_r_l` | 25 | None | 8 | 1 | `hkpLimitedHingeConstraintData` | -0.6169, 0.5487, 2.3515 | -1, 0, 0 | 0 .. 45 |
| `technicaljeep_ring_r_r` | 26 | None | 8 | 2 | `hkpLimitedHingeConstraintData` | 0.6216, 0.5487, 2.3515 | -1, 0, 0 | 0 .. 45 |
| `technicaljeep_mirror_l` | 28 | None | 9 | 4 | `hkpLimitedHingeConstraintData` | -0.8663, 1.1811, -1.0626 | -0, 0, -1 | -35 .. 0 |
| `technicaljeep_mirror_r` | 30 | None | 10 | 6 | `hkpLimitedHingeConstraintData` | 0.8663, 1.1811, -1.06 | 0, 0, 1 | -35 .. 0 |
| `technicaljeep_bumper_f` | 35 | None | 11 | 7 | `hkpLimitedHingeConstraintData` | -0.5169, 0.3744, -2.3281 | 0.6868, 0, 0.7269 | -10 .. 0 |
| `technicaljeep_ring_f_l` | 50 | None | 35 | 8 | `hkpLimitedHingeConstraintData` | -0.3157, 0.5324, -2.7077 | 1, -0, 0 | -10 .. 45 |
| `technicaljeep_ring_f_r` | 51 | None | 35 | 9 | `hkpLimitedHingeConstraintData` | 0.3242, 0.5324, -2.7077 | 1, -0, 0 | -10 .. 45 |
| `technicaljeep_back_gate` | 2 | RearDoor | 0 | 0 | `hkpLimitedHingeConstraintData` | 0, 0.5774, 2.2501 | -1, -0, 0 | -90 .. 0 |
| `technicaljeep_rebel_turret` | 46 | Turret | 12 | 11 | `hkpLimitedHingeConstraintData` | 0, 1.3878, 1.2902 | -0, 1, 0 | -179 .. 179 |

Weapon points that name the moving parts:

| weapon | binding | point | yaw part | pitch part | point xyz |
|---|---|---|---|---|---|
| `w206_mounted_capstone_m2hm` | mounted_weapon | `vehicle.attach` | `technicaljeep_rebel_turret` | `technicaljeep_weapon_mount_vertical` | 0, 0, 0 |

Aim objects:

| class | name | min_aim_distance | xyz |
|---|---|---|---|
| `STargetPoint` | `AutoAimTargetPoint` | -1 | 0, 1, 0 |

### v0300 Serpente (donor)

`v0300_car_kensington_sportsmuscle_signature_preorder.ee` - 42 parts, 11 constraint objects (hkpLimitedHingeConstraintData 9, hkpRagdollConstraintData 2); `aim_part_constraints` rows 0, `hinged_parts` rows 0, `rotating_parts` rows 0.

| part | i | behaviour | parent | constraint | class | pivot (x, y, z) | axis | min..max (deg) |
|---|---|---|---|---|---|---|---|---|
| `sportsmuscle_door_f_l` | 1 | FrontLeftDoor | 0 | 0 | `hkpLimitedHingeConstraintData` | -1.0185, 0.6223, -0.7714 | 0, -1, 0 | 0 .. 80 |
| `sportsmuscle_door_f_r` | 2 | FrontRightDoor | 0 | 2 | `hkpLimitedHingeConstraintData` | 1.0185, 0.6223, -0.7714 | 0, 1, 0 | 0 .. 80 |
| `sportsmuscle_hood_signature` | 25 | Hood | 3 | 8 | `hkpLimitedHingeConstraintData` | 0, 1.0572, -0.8478 | 1, 0, 0 | 0 .. 70 |
| `sportsmuscle_engine` | 3 | None | 0 | 4 | `hkpRagdollConstraintData` | - | - | - |
| `sportsmuscle_rear_bumper` | 6 | None | 0 | 9 | `hkpLimitedHingeConstraintData` | -0.5078, 0.7374, 2.4304 | 0.9659, 0, 0.2588 | -15 .. 0 |
| `sportsmuscle_trunk` | 10 | None | 0 | 10 | `hkpLimitedHingeConstraintData` | 0.0035, 1.44, 1.0209 | -1, 0, 0 | 0 .. 90 |
| `sportsmuscle_l_mirror` | 17 | None | 1 | 1 | `hkpLimitedHingeConstraintData` | -0.833, 1.0016, -0.5032 | -0, 0, -1 | -35 .. 0 |
| `sportsmuscle_r_mirror` | 19 | None | 2 | 3 | `hkpLimitedHingeConstraintData` | 0.833, 1.0016, -0.5032 | 0, 0, 1 | -35 .. 0 |
| `sportsmuscle_front_bumper` | 22 | None | 3 | 5 | `hkpLimitedHingeConstraintData` | 0.6508, 0.2089, -0.2296 | -0.4454, -0, -0.8953 | -15 .. 0 |
| `sportsmuscle_grill` | 23 | None | 3 | 6 | `hkpRagdollConstraintData` | - | - | - |
| `sportsmuscle_hood` | 24 | None | 3 | 7 | `hkpLimitedHingeConstraintData` | 0, 1.0572, -0.8478 | 1, 0, 0 | 0 .. 30 |

Aim objects:

| class | name | min_aim_distance | xyz |
|---|---|---|---|
| `STargetPoint` | `AutoAimTargetPoint` | -1 | 0, 1, 0 |
| `CAimPOIWeaponComponent` | `aim.poi` | - | 0, 0, 0 |

### v0604 buggy

`v0604_car_urga_buggy_signature_preorder.ee` - 75 parts, 12 constraint objects (hkpLimitedHingeConstraintData 9, hkpRagdollConstraintData 3); `aim_part_constraints` rows 12, `hinged_parts` rows 0, `rotating_parts` rows 0.

| part | i | behaviour | parent | constraint | class | pivot (x, y, z) | axis | min..max (deg) |
|---|---|---|---|---|---|---|---|---|
| `buggy_door_f_l` | 18 | FrontLeftDoor | 0 | 1 | `hkpLimitedHingeConstraintData` | -0.6486, 0.8076, -0.4864 | 0, -1, 0 | 0 .. 80 |
| `buggy_door_f_r` | 19 | FrontRightDoor | 0 | 2 | `hkpLimitedHingeConstraintData` | 0.6495, 0.8156, -0.4873 | 0, 1, 0 | 0 .. 80 |
| `buggy_hood` | 61 | Hood | 29 | 9 | `hkpLimitedHingeConstraintData` | -0.0263, 1.2257, -0.7015 | 1, -0, 0 | 0 .. 30 |
| `buggy_bumper_f` | 13 | None | 0 | 0 | `hkpRagdollConstraintData` | - | - | - |
| `buggy_fender_f_l` | 21 | None | 0 | 3 | `hkpLimitedHingeConstraintData` | -0.5729, 1.1524, -0.6883 | 0.2576, -0.072, -0.9636 | 0 .. 22.367 |
| `buggy_fender_f_r` | 22 | None | 0 | 4 | `hkpLimitedHingeConstraintData` | 0.5458, 1.1123, -0.7129 | 0.1174, -0.0081, 0.9931 | 0 .. 13.846 |
| `buggy_fender_r_l` | 23 | None | 0 | 5 | `hkpRagdollConstraintData` | - | - | - |
| `buggy_fender_r_r` | 24 | None | 0 | 6 | `hkpRagdollConstraintData` | - | - | - |
| `buggy_mirror_l` | 27 | None | 0 | 7 | `hkpLimitedHingeConstraintData` | -0.5043, 1.5531, -0.3041 | -0.3781, 0, -0.9258 | -25 .. 0 |
| `buggy_mirror_r` | 28 | None | 0 | 8 | `hkpLimitedHingeConstraintData` | 0.4955, 1.5429, -0.2826 | 0, 0, 1 | -50 .. 0 |
| `buggy_hatch_t` | 63 | None | 33 | 11 | `hkpLimitedHingeConstraintData` | 0.2338, 1.7566, 0.3649 | 1, 0, 0 | 0 .. 120 |
| `buggy_trunk` | 62 | Trunk | 30 | 10 | `hkpLimitedHingeConstraintData` | 0.0078, 1.2905, 0.7404 | -1, 0, 0 | 0 .. 80 |

Aim objects:

| class | name | min_aim_distance | xyz |
|---|---|---|---|
| `STargetPoint` | `AutoAimTargetPoint` | -1 | 0, 1, 0 |
| `CAimPOIWeaponComponent` | `aim.poi` | - | 0, 0, 0 |

## 3. The point properties (fleet census)

Across 41 armed entities, **92 fire points** on **52 weapons** name a yaw part (`id:80201E4D`) or a pitch part (`id:5C19E7E0`). The values are part-name strings, not hashes.

| role | part behaviour | count |
|---|---|---|
| yaw | `Cannon` | 13 |
| yaw | `None` | 44 |
| yaw | `Turret` | 18 |
| pitch | `Cannon` | 47 |

Every pitch part is a `Cannon` part. Yaw parts are `Turret` (true turrets), `Cannon` (boat/jeep mounts that yaw and pitch as two Cannon-behaviour parts) or plain parts on aircraft pods. Unresolved names: 0; unexpected behaviours: 0.

2 entries name a part that is not in the host's parts module but in another entity's (`v4603_plane_urga_cargotransport_military_cargo_tank.ee` -> `v0201_car_capstone_mediumtank_debug.ee`): the cargo plane carries the medium tank and mounts its whole weapon, so the weapon's point still names the tank's own turret and cannon parts. Counted here, not unresolved.

## 4. `aim_part_constraints` is suspension, not a turret

Decoded from 78 parts modules in the local cache: every one declares the array, but only **17** have rows (**85** in total). Parts named by behaviour:

| side:behaviour | count |
|---|---|
| `source:Axle` | 2 |
| `source:None` | 70 |
| `source:Spring` | 13 |
| `target:BrakeCalipers` | 6 |
| `target:BrakeDisc` | 12 |
| `target:BrakeDrum` | 34 |
| `target:Engine` | 2 |
| `target:None` | 12 |
| `target:Wheel` | 19 |

Examples:

- `atv_vehicle_parts.vmodc` row 0 source `atv_y_bar_r_r_b` (None)
- `atv_vehicle_parts.vmodc` row 0 target `atv_brake_drum_r_r` (BrakeDrum)
- `atv_vehicle_parts.vmodc` row 1 source `atv_y_bar_f_r_b` (None)
- `atv_vehicle_parts.vmodc` row 1 target `atv_brake_drum_f_r` (BrakeDrum)
- `atv_vehicle_parts.vmodc` row 2 source `atv_y_bar_f_l_t` (None)
- `atv_vehicle_parts.vmodc` row 2 target `atv_brake_drum_f_l` (BrakeDrum)
- `atv_vehicle_parts.vmodc` row 3 source `atv_axle_arm_r_l` (None)
- `atv_vehicle_parts.vmodc` row 3 target `atv_brake_drum_r_l` (BrakeDrum)

No row has a `Turret` or `Cannon` behaviour, and the six turreted vehicles in this sample (medium tank, Bavarium tank, small tank, APC, armoured jeep, technical) have **0** aim constraints each. The array is a part-to-part aim constraint used by suspension and steering links: a U-bar/axle/coilspring source aims at a brake drum, disc, caliper or wheel target.

The module's two other moving-part arrays are empty on all eight samples: `hinged_parts[]` and `rotating_parts[]` carry 0 rows for each (fleet: 28 of 78 modules have `hinged_parts` rows, 22 have `rotating_parts` rows). So for a tank the hinge is not declared in the parts module at all - the part's `constraint_index` points into `.physicsc`, and that is the whole link.

## 5. How the aim target is chosen

Each sampled entity carries exactly one `STargetPoint` named `AutoAimTargetPoint` (`min_aim_distance` -1, so no minimum) plus two unnamed values (a float 2 and an int 1). Its `world` matrix translation is (0, 1, 0) on every sample: the target point is the vehicle origin one metre up at the body centre, not the muzzle and not the turret.

The weapons name autoaim tunes. Both tanks' `w602_mediumtank_canon` and `w603_mediumtank_mgun` and the small tank's `w605_smalltank_canon` use `autoaim_vehicle_mgun`; the mounted M2 (`w206_mounted_capstone_m2hm`) on the APC, armoured jeep and technical uses `autoaim_assault_rifle`.

`autoaim_assault_rifle.wtune` - `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_assault_rifle.wtune`:

| tune member | value |
|---|---|
| `Stunting.AlwaysTargetDistance` | 2.0 |
| `Stunting.AngleThresholdCurrentTarget` | 0.06 |
| `Stunting.AngleThresholdNewTarget` | 0.04 |
| `Stunting.CanTargetCharacters` | 1 |
| `Stunting.CanTargetRigidObjects` | 0 |
| `Stunting.CanTargetVehicles` | 0 |
| `Stunting.MaxAimDistance` | 70.0 |
| `Stunting.MinAimDistance` | 5.0 |
| `Stunting.StickyAimAngleCurrentTarget` | 16.0 |
| `Stunting.StickyAimAngleNewTarget` | 6.0 |
| `Stunting.StickyAimStrength` | 0.4 |
| `Stunting.UseWeaponDirection` | 0 |

`autoaim_vehicle_mgun.wtune` - `editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune`:

| tune member | value |
|---|---|
| `Stunting.AlwaysTargetDistance` | 2.0 |
| `Stunting.AngleThresholdCurrentTarget` | 0.05 |
| `Stunting.AngleThresholdNewTarget` | 0.03 |
| `Stunting.CanTargetCharacters` | 1 |
| `Stunting.CanTargetRigidObjects` | 0 |
| `Stunting.CanTargetVehicles` | 0 |
| `Stunting.MaxAimDistance` | 70.0 |
| `Stunting.MinAimDistance` | 5.0 |
| `Stunting.StickyAimAngleCurrentTarget` | 16.0 |
| `Stunting.StickyAimAngleNewTarget` | 6.0 |
| `Stunting.StickyAimStrength` | 0.4 |
| `Stunting.UseWeaponDirection` | 0 |

`Stunting` is the in-vehicle set. Candidates are considered out to 70 m and never closer than 5 m; a candidate within 0.03 rad (1.7 deg) of the aim line is accepted, or 0.04 rad (2.3 deg) on the rifle tune, and the current target is held until it leaves 0.05 rad (2.9 deg) / 0.06 rad (3.4 deg). Sticky aim then allows 6 deg for a new target and 16 deg for the current one, strength 0.4. `CanTargetCharacters` is 1 while `CanTargetVehicles` and `CanTargetRigidObjects` are 0: the soft aim assist on the tank cannon is for characters, not vehicles.

So no file holds an aim ray or a turret target. The aim system picks a point (the entity's `STargetPoint`, or a soft-aim candidate), and the two hinges are driven to put the cannon on it. The pitch limit stops the cannon elevating further; that is a constraint, not a target check.

## 6. Validation and limits

`jc3turret.py --check` re-reads the eight entities' parts modules and `.physicsc` files, rebuilds every table and compares the json field-for-field and the md byte-for-byte. It asserts: the medium tank's three constraints are the cannon (-5 .. 20 deg), hatch (0 .. 130 deg) and turret (-179 .. 179 deg); every constrained part's `constraint_index` resolves to an object; every Turret and Cannon part sits on a limited hinge with an identity `parent_space_offset`; every pitch part in the fleet is a `Cannon` part; no `aim_part_constraints` row names a Turret or Cannon part; the samples name exactly one `AutoAimTargetPoint` at (0, 1, 0); the six turreted samples have 0 `aim_part_constraints` rows.

**Limits.** Rotation speeds and accelerations are not in the decoded data - a limited hinge carries an axis and two angles, and the turn rate is code-side (UNKNOWN). The hinge transform's frame (body-A local vs vehicle space) is not proven: the medium tank's numbers agree with vehicle space, and on the wheeled mounts the pitch pivot sits above an unconstrained adapter part, so a port should read them the way they are printed. `hkpRagdollConstraintData` objects are counted but not decoded (the armoured jeep and small tank carry them). The two point properties `id:80201E4D`/`id:5C19E7E0` still have no recovered names; their meaning is proven by the part names and behaviours they carry. The `aim_part_constraints` census covers the modules in the local cache, not all 233.

**Not in the files:** a per-vehicle turret turn rate, a turret ring bone, or any aim limit on the weapon itself. A B-05 port must copy the parts, the hinge constraints and the two point strings; there is no single "turret" field to set.
