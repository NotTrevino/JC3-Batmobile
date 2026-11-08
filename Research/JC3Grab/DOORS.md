# Doors, canopies and missile hatches

G2-15. A door is a behaviour name in `vehicle_common.all_door_part_properties`, an
entry in the parts module's `door_parts[]` array (a bare `part_index`), and a
`hkpLimitedHingeConstraintData` in `.physicsc`. The module stores **no** open angle,
speed, animation name or interaction: the travel is the hinge's two limits, and
whatever drives it is code-side.

## 1. The four sampled vehicles

| vehicle | part | behaviour | axis | limits | pivot | parent |
|---|---|---|---|---|---|---|
| v0300 Serpente (civilian) | `sportsmuscle_door_f_l` | FrontLeftDoor | (0, -1, 0) | 0 .. 80 deg | (-1.018, 0.622, -0.771) | 0 |
| v0300 Serpente (civilian) | `sportsmuscle_door_f_r` | FrontRightDoor | (0, 1, 0) | 0 .. 80 deg | (1.018, 0.622, -0.771) | 0 |
| v0300 Serpente (civilian) | `sportsmuscle_hood_signature` | Hood | (1, 0, 0) | 0 .. 70 deg | (0, 1.057, -0.848) | 3 |
| v0200 APC (military) | `apc_door_c_l` | CenterLeftDoor | (0, -1, 0) | 0 .. 100 deg | (-1.346, 1.646, 0.894) | 0 |
| v0200 APC (military) | `apc_door_c_r` | CenterRightDoor | (0, 1, 0) | 0 .. 100 deg | (1.346, 1.644, 0.894) | 0 |
| v0200 APC (military) | `apc_door_r` | RearLeftDoor | (0.001, -1, 0.002) | 0 .. 95 deg | (-0.425, 1.758, 2.899) | 0 |
| v0200 APC (military) | `apc_hatch_l` | FrontLeftDoor | (1, 0, 0) | 0 .. 130 deg | (-0.5, 2.086, -0.284) | 0 |
| v0200 APC (military) | `apc_turret_hatch` | TurretDoor | (1, 0, 0) | 0 .. 130 deg | (-0.004, 2.257, 1.713) | 30 |
| v5603 monorail missile car | `monorailmissilecar_missile_hatch_l_01` | MissileHatch | (0, -0, -1) | 0 .. 150 deg | (-1.35, 3.35, -6.117) | 7 |
| v5603 monorail missile car | `monorailmissilecar_missile_hatch_l_02` | MissileHatch | (0, -0, -1) | 0 .. 150 deg | (-1.35, 3.35, -4.391) | 7 |
| v5603 monorail missile car | `monorailmissilecar_missile_hatch_l_03` | MissileHatch | (0, -0, -1) | 0 .. 150 deg | (-1.35, 3.35, -2.612) | 7 |
| v5603 monorail missile car | `monorailmissilecar_missile_hatch_l_04` | MissileHatch | (0, -0, -1) | 0 .. 150 deg | (-1.35, 3.35, -0.855) | 7 |
| v5603 monorail missile car | `monorailmissilecar_missile_hatch_l_05` | MissileHatch | (0, -0, -1) | 0 .. 150 deg | (-1.35, 3.35, 0.851) | 7 |
| v5603 monorail missile car | `monorailmissilecar_missile_hatch_l_06` | MissileHatch | (0, -0, -1) | 0 .. 150 deg | (-1.35, 3.35, 2.612) | 7 |
| v5603 monorail missile car | `monorailmissilecar_missile_hatch_l_07` | MissileHatch | (0, -0, -1) | 0 .. 150 deg | (-1.35, 3.35, 4.364) | 7 |
| v5603 monorail missile car | `monorailmissilecar_missile_hatch_l_08` | MissileHatch | (0, -0, -1) | 0 .. 150 deg | (-1.35, 3.35, 6.086) | 7 |
| v5603 monorail missile car | `monorailmissilecar_missile_hatch_r_01` | MissileHatch | (0, 0, 1) | 0 .. 150 deg | (1.35, 3.35, -6.102) | 8 |
| v5603 monorail missile car | `monorailmissilecar_missile_hatch_r_02` | MissileHatch | (0, 0, 1) | 0 .. 150 deg | (1.35, 3.35, -4.348) | 8 |
| v5603 monorail missile car | `monorailmissilecar_missile_hatch_r_03` | MissileHatch | (0, 0, 1) | 0 .. 150 deg | (1.35, 3.35, -2.574) | 8 |
| v5603 monorail missile car | `monorailmissilecar_missile_hatch_r_04` | MissileHatch | (0, 0, 1) | 0 .. 150 deg | (1.35, 3.35, -0.864) | 8 |
| v5603 monorail missile car | `monorailmissilecar_missile_hatch_r_05` | MissileHatch | (0, 0, 1) | 0 .. 150 deg | (1.35, 3.35, 0.87) | 8 |
| v5603 monorail missile car | `monorailmissilecar_missile_hatch_r_06` | MissileHatch | (0, 0, 1) | 0 .. 150 deg | (1.35, 3.35, 2.628) | 8 |
| v5603 monorail missile car | `monorailmissilecar_missile_hatch_r_07` | MissileHatch | (0, 0, 1) | 0 .. 150 deg | (1.35, 3.35, 4.372) | 8 |
| v5603 monorail missile car | `monorailmissilecar_missile_hatch_r_08` | MissileHatch | (0, 0, 1) | 0 .. 150 deg | (1.358, 3.318, 6.109) | 8 |
| v0201 medium tank | `mediumtank_hatch` | FrontLeftDoor | (1, 0, 0) | 0 .. 130 deg | (-0.485, 2.921, 1.479) | 26 |

The donor's three `door_parts[]` entries are its two side doors and
`sportsmuscle_hood_signature`; the APC's five are two centre doors, a rear-left
door, the front-left hatch and the turret hatch; the monorail car's sixteen are
the missile bay covers (eight per side).

## 2. (a) Can a door hinge about a transverse axis?

Yes. 60 of the 220 hinged door parts across 56 modules rotate about **X** - hoods, roof hatches and canopies; 132 rotate about **Y** (side doors) and 28 about **Z** (the monorail bay covers). A door that tilts forward is therefore an ordinary `FrontLeftDoor`/`Hood` part on an X-axis hinge, e.g. `mediumtank_hatch` (0..130 deg) or `sportsmuscle_hood_signature` (0..70 deg).

| axis | parts |
|---|---|
| X (transverse) | 60 |
| Y (vertical) | 132 |
| Z (longitudinal) | 28 |

Transverse-axis examples:

| module | part | behaviour | axis | limits |
|---|---|---|---|---|
| `apc_vehicle_parts.vmodc` | `apc_hatch_l` | FrontLeftDoor | (1, 0, 0) | 0 .. 130 deg |
| `apc_vehicle_parts.vmodc` | `apc_turret_hatch` | TurretDoor | (1, 0, 0) | 0 .. 130 deg |
| `armoredjeep_vehicle_parts.vmodc` | `armoredjeep_turret_hatch` | TurretDoor | (1, 0, 0) | 0 .. 100 deg |
| `armoredtransport_vehicle_parts.vmodc` | `armoredtransport_hood` | Hood | (1, 0, 0) | 0 .. 80 deg |
| `armoredtruck_vehicle_parts.vmodc` | `armoredtruck_hood` | Hood | (1, -0, 0) | 0 .. 30 deg |
| `bavariumtank_vehicle_parts.vmodc` | `bavariumtank_hatch` | FrontLeftDoor | (0.999, -0.04, 0) | 0 .. 130 deg |
| `buggy_vehicle_parts.vmodc` | `buggy_hood` | Hood | (1, -0, 0) | 0 .. 30 deg |
| `buggy_vehicle_parts.vmodc` | `buggy_trunk` | Trunk | (-1, 0, 0) | 0 .. 80 deg |
| `cargotransport_vehicle_parts.vmodc` | `cargotransport_cargodoor_c_exterior` | CargoBayDoor | (1, 0, 0) | 0 .. 43 deg |
| `cargotransport_vehicle_parts.vmodc` | `cargotransport_cargodoor_c_interior` | CargoBayDoor | (1, 0, -0) | 0 .. 43 deg |
| `cargotransport_vehicle_parts.vmodc` | `cargotransport_cargodoor_r_exterior` | CargoBayDoor | (1, -0, 0) | 0 .. 15 deg |
| `cargotransport_vehicle_parts.vmodc` | `cargotransport_cargodoor_r_interior` | CargoBayDoor | (1, -0, 0) | 0 .. 15 deg |

By behaviour:

| behaviour | rows | axes | limits |
|---|---|---|---|
| `FrontLeftDoor` | 55 | X 5, Y 44, Z 6 | 0 .. 160 deg |
| `FrontRightDoor` | 41 | Y 39, Z 2 | 0 .. 120 deg |
| `Hood` | 26 | X 26 | 0 .. 90 deg |
| `RearRightDoor` | 20 | Y 20 | -90 .. 90 deg |
| `Trunk` | 20 | X 19, Y 1 | -90 .. 110 deg |
| `RearLeftDoor` | 16 | Y 16 | -1 .. 95 deg |
| `MissileHatch` | 16 | Z 16 | 0 .. 150 deg |
| `CenterRightDoor` | 6 | X 1, Y 5 | -0.5 .. 100 deg |
| `RearDoor` | 5 | X 1, Y 4 | -90 .. 80 deg |
| `CargoBayDoor` | 5 | X 5 | 0 .. 90 deg |
| `CenterLeftDoor` | 4 | X 1, Y 3 | -0.5 .. 100 deg |
| `LeftWing` | 4 | Z 2 | 0 .. 90 deg |
| `RightWing` | 4 | Z 2 | 0 .. 90 deg |
| `TurretDoor` | 2 | X 2 | 0 .. 130 deg |

4 door rows have `constraint_index` -1 and therefore no hinge at all (propeller-wing parts with a door behaviour); every other row is a `hkpLimitedHingeConstraintData`.


## 3. (b) What opens a `MissileHatch`?

The monorail car has 16 `MissileHatch` parts, all on
limited hinges of 0..150 deg about ±Z, listed in `door_parts[]`. Its only weapon is:

| class | name | tuning |
|---|---|---|
| `CMissileWeaponBase` | `w614_monorailmissilecar_missile` | `editor/entities/jc_weapons/06_vehicle/w614_monorailmissilecar_missile/w614_monorailmissilecar_missile.wtune` |

Its 6 fire points are named `InternalFirePosition_0…5` - the missiles leave from *inside* the bay the covers close over. The only other weapon class on it is `CTurretWeaponComponent`.

**Nothing in the entity opens them.** No object other than `CPartProp` names a
hatch part; there is no interaction entry for a hatch, no attached effect on one,
and no member on the weapon that names a door. The behaviour name and the
`door_parts[]` entry are the only links, so the opening is decided in code (almost
certainly on fire, given the `Internal*` fire positions and the 150 deg travel) -
that inference is not in the files.

## 4. (c) Does the driver's entry open the driver door part?

The interaction graph carries two entry paths, and the state names say what they
do:

| entity | `entry.driver` | `entry.driver.no.door` | `S_ENTER_DRIVER_VEHICLE` | `S_ENTER_DRIVER_NO_DOOR_VEHICLE` |
|---|---|---|---|---|
| v0300 Serpente (civilian) | yes | yes | yes | yes |
| v0200 APC (military) | - | - | - | - |
| v5603 monorail missile car | - | - | - | - |

Across 55 cached entity graphs, 21 carry **both** paths,
0 only the door path, 4 only the no-door path,
and 30 neither (military vehicles, trains and aircraft whose entry
nodes carry other names).
The donor is in the `both` group: the driver can enter through the door
(`entry.driver` → `S_ENTER_DRIVER_VEHICLE`) or without it
(`entry.driver.no.door` → `S_ENTER_DRIVER_NO_DOOR_VEHICLE`).

The donor's container is 566 members and holds 0 animation files: the swing is not
authored in the entity. So the file proves the *branch* exists and which
interaction the door path belongs to, but not that the part visibly moves - it
is a hinge with no curve, driven by whatever runs after `S_ENTER_DRIVER_VEHICLE`.
For a B-05 canopy the actionable
form is: X-axis limited hinge on a `Hood`/`FrontLeftDoor` part, listed in
`door_parts[]`, plus the `entry.driver` path if the door is meant to be used.

## 5. Validation and limits

`jc3doors.py --check` re-reads the four entities, the cached modules and the
cached `.epe` graphs, rebuilds both files and compares them. It asserts: the
donor's door array is `door_f_l`, `door_f_r`, `hood_signature`; its two doors
hinge about ±Y and the hood about +X; the monorail's 16 hatches are all limited
hinges of 0..150 deg about ±Z; no object outside `CPartProp` names a monorail
hatch; the donor has both entry paths and the APC has neither driver entry;
every door part with a constraint is a limited hinge (or is listed as an
exception with its class).

**Limits.** An angle is the hinge's authored limit, not a measured swing - nothing
in the files says the door reaches it. Speed is absent everywhere (no rate field,
no animation curve), so it stays UNKNOWN. The census covers the 78 cached parts
modules (56 with doors) and the 55 cached `.epe` graphs, not all 233 entities.
The `MissileHatch` firing trigger is an inference from the fire-point names and
the bay geometry; the entity contains no link. Which code runs after an entry
state is not in any file read here.
