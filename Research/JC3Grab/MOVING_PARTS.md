# Moving parts - who drives each behaviour

G2-14. Every part carries one `behavior` string. That string is the key into the shared
`vehicle_common.vmodc` module, which holds five behaviour tables: `all_hinged_`,
`all_rotating_`, `all_door_`, `all_fin_` and `all_spring_part_properties`. Only the first
two name a driving variable; the other three are name-only, and 29 behaviours used by shipped vehicles have no row at all.

## 1. The five tables

| table | rows | used by a part | members |
|---|---|---|---|
| `all_fin_part_properties` | 1 | 0 | `name` only |
| `all_spring_part_properties` | 1 | 1 | `name` only |
| `all_door_part_properties` | 14 | 14 | `name` only |
| `all_hinged_part_properties` | 25 | 11 | `lod`, `target_position_variable`, `use_target_position_as_angle` |
| `all_rotating_part_properties` | 12 | 12 | `inverted`, `number_of_water_collision_sensors`, `rotoscope_enabled`, `rotoscope_rpm_per_cycle`, `rpm_variable`, `special_collision_enabled` |

Source: `vehicle_common.vmodc`, the only copy in the fleet, carried as an
inner file of the Serpente civilian `.ee`.

### Hinged parts - a variable, a LOD flag and an angle flag

| behaviour | `target_position_variable` | `lod` | `use_target_position_as_angle` |
|---|---|---|---|
| `LeftAileron` | `steering_roll` | 1 | 0 |
| `RightAileron` | `steering_roll_inverted` | 1 | 0 |
| `LeftElevon` | `elevon_left_T` | 1 | 0 |
| `RightElevon` | `elevon_right_T` | 1 | 0 |
| `Elevator` | `steering_pitch` | 1 | 0 |
| `Rudder` | `steering_yaw` | 1 | 0 |
| `Flaps` | `flaps_T` | 1 | 0 |
| `AirBrake` | `air_brakes_T` | 1 | 0 |
| `LandingGear` | `landing_gears_T` | 0 | 0 |
| `LandingGearHatch` | `hatches_T` | 0 | 0 |
| `BoatEngine` | `steering_turn` | 1 | 0 |
| `SteeringWheel` | `steering_turn` | 1 | 0 |
| `SteeringFork` | `steering_angle_inverted` | 0 | 1 |
| `RearLeftCoxa` | `rear_left_coxa_t` | 1 | 0 |
| `RearRightCoxa` | `rear_right_coxa_t` | 1 | 0 |
| `RearLeftFemur` | `rear_left_femur_t` | 1 | 0 |
| `RearRightFemur` | `rear_right_femur_t` | 1 | 0 |
| `RearLeftTibia` | `rear_left_tibia_t` | 1 | 0 |
| `RearRightTibia` | `rear_right_tibia_t` | 1 | 0 |
| `FrontLeftCoxa` | `front_left_coxa_t` | 1 | 0 |
| `FrontLeftFemur` | `front_left_femur_t` | 1 | 0 |
| `FrontLeftTibia` | `front_left_tibia_t` | 1 | 0 |
| `FrontRightCoxa` | `front_right_coxa_t` | 1 | 0 |
| `FrontRightFemur` | `front_right_femur_t` | 1 | 0 |
| `FrontRightTibia` | `front_right_tibia_t` | 1 | 0 |

The variable is a float in the vehicle's own state: the animation system writes it,
the behaviour reads it. `SteeringFork` is the only row that sets `use_target_position_as_angle`; every other row takes the variable as a 0..1 position.

### Rotating parts - an rpm variable and rotoscope flags

| behaviour | `rpm_variable` | rotoscope | inverted | special collision | water sensors | rpm/cycle |
|---|---|---|---|---|---|---|
| `MainRotor` | `main_rotor_rpm` | 1 | 0 | 1 | 5 | 20.0 |
| `TailRotor` | `tail_rotor_rpm` | 1 | 0 | 1 | 3 | 20.0 |
| `Propeller` | `propeller_rpm` | 1 | 0 | 1 | 0 | 20.0 |
| `GatlingGun` | `weapon_rpm` | 0 | 0 | 0 | 0 | 20.0 |
| `RadarSlow` | `radar_slow_rpm` | 0 | 0 | 0 | 0 | 20.0 |
| `RadarFast` | `radar_fast_rpm` | 0 | 0 | 0 | 0 | 20.0 |
| `LeftRotor` | `rotor_rpm` | 1 | 1 | 1 | 3 | 50.0 |
| `RightRotor` | `rotor_rpm` | 1 | 0 | 1 | 3 | 50.0 |
| `Rotor` | `rotor_rpm` | 1 | 0 | 1 | 3 | 50.0 |
| `EngineRotatingPart` | `engine_rpm` | 1 | 0 | 1 | 0 | 20.0 |
| `OuterLeftRotor` | `rotor_rpm` | 1 | 0 | 1 | 3 | 50.0 |
| `OuterRightRotor` | `rotor_rpm` | 1 | 0 | 1 | 3 | 50.0 |

`rpm_variable` names the vehicle's rpm state. `rotoscope_rpm_per_cycle` holds 20.0 on 7 (MainRotor, TailRotor, Propeller, GatlingGun, RadarSlow, RadarFast, EngineRotatingPart); 50.0 on 5 (LeftRotor, RightRotor, Rotor, OuterLeftRotor, OuterRightRotor). What the field drives is not defined in any file read here: the name suggests a per-cycle strobe rate, which is this record's inference, not a decoded definition - the value itself is decoded, the meaning is UNKNOWN.

### Doors, fins and springs - name only

| table | names |
|---|---|
| `all_door_part_properties` | `FrontLeftDoor`, `FrontRightDoor`, `CenterLeftDoor`, `CenterRightDoor`, `RearLeftDoor`, `RearRightDoor`, `TurretDoor`, `Trunk`, `Hood`, `RearDoor`, `CargoBayDoor`, `LeftWing`, `RightWing`, `MissileHatch` |
| `all_fin_part_properties` | `BoatRudder` |
| `all_spring_part_properties` | `Spring` |

These rows carry nothing but the name and its hash. A door's angle is the part's
Havok hinge (G2-13: `mediumtank_hatch` is a `FrontLeftDoor` on a 0..130 deg
limited hinge), and the parts module's `door_parts[]` only lists the part index -
so the door's travel is in `.physicsc`, not in `vehicle_common`.

## 2. Behaviour -> vehicles -> proof

`parts`/`entities`/`chassis` come from `FEATURE_CENSUS.json` (232 entities, of the 233 records in `PARTS_TABLE.jsonl`);
the root class comes from each entity's `.epe` class histogram. `proven-on-CCar`
means at least one `CCar` chassis ships a part with that behaviour.

| behaviour | channel / variable | parts | entities | chassis | classes | proof |
|---|---|---|---|---|---|---|
| `Wheel` | no vehicle_common row | 710 | 174 | 60 | `CAirPlane`, `CCar`, `CHelicopter`, `CMotorBike` | proven-on-CCar |
| `BrakeCalipers` | no vehicle_common row | 330 | 85 | 30 | `CAirPlane`, `CCar`, `CMotorBike` | proven-on-CCar |
| `Windshield` | no vehicle_common row | 229 | 151 | 51 | `CAirPlane`, `CBoat`, `CCar`, `CHelicopter`, `CMotorBike` | proven-on-CCar |
| `Flaps` | hinged, `flaps_T` | 202 | 23 | 8 | `CAirPlane`, `CCar` | proven-on-CCar |
| `BrakeDisc` | no vehicle_common row | 192 | 48 | 16 | `CCar` | proven-on-CCar |
| `Engine` | no vehicle_common row | 187 | 150 | 50 | `CAirPlane`, `CBoat`, `CCar`, `CHelicopter`, `CMotorBike`, `CTrain` | proven-on-CCar |
| `FrontLeftDoor` | door (name only) | 173 | 173 | 56 | `CAirPlane`, `CBoat`, `CCar`, `CHelicopter` | proven-on-CCar |
| `FrontLeftWindow` | no vehicle_common row | 145 | 137 | 47 | `CAirPlane`, `CBoat`, `CCar`, `CHelicopter` | proven-on-CCar |
| `FrontRightDoor` | door (name only) | 132 | 132 | 42 | `CAirPlane`, `CCar`, `CHelicopter` | proven-on-CCar |
| `FrontRightWindow` | no vehicle_common row | 130 | 122 | 41 | `CAirPlane`, `CBoat`, `CCar`, `CHelicopter` | proven-on-CCar |
| `RearRightWindow` | no vehicle_common row | 119 | 110 | 36 | `CAirPlane`, `CBoat`, `CCar`, `CHelicopter` | proven-on-CCar |
| `LandingGear` | hinged, `landing_gears_T` | 114 | 25 | 7 | `CAirPlane`, `CHelicopter` | unproven-on-CCar |
| `RearWindow` | no vehicle_common row | 112 | 99 | 33 | `CAirPlane`, `CBoat`, `CCar`, `CHelicopter` | proven-on-CCar |
| `RearLeftWindow` | no vehicle_common row | 103 | 98 | 33 | `CAirPlane`, `CCar`, `CHelicopter` | proven-on-CCar |
| `Body` | no vehicle_common row | 83 | 83 | 31 | `CAirPlane`, `CBoat`, `CCar`, `CHelicopter`, `CMotorBike` | proven-on-CCar |
| `BrakeDrum` | no vehicle_common row | 78 | 24 | 7 | `CCar`, `CMotorBike` | proven-on-CCar |
| `Hood` | door (name only) | 78 | 78 | 27 | `CCar`, `CMotorBike` | proven-on-CCar |
| `LandingGearHatch` | hinged, `hatches_T` | 76 | 19 | 5 | `CAirPlane`, `CHelicopter` | unproven-on-CCar |
| `Cannon` | no vehicle_common row | 68 | 40 | 11 | `CBoat`, `CCar`, `CHelicopter` | proven-on-CCar |
| `RearRightDoor` | door (name only) | 62 | 56 | 18 | `CAirPlane`, `CCar`, `CHelicopter` | proven-on-CCar |
| `Spring` | spring (name only) | 61 | 23 | 7 | `CCar`, `CMotorBike` | proven-on-CCar |
| `TrainCargo` | no vehicle_common row | 60 | 4 | 1 | `CTrain` | unproven-on-CCar |
| `Trunk` | door (name only) | 58 | 58 | 20 | `CCar` | proven-on-CCar |
| `CenterLeftWindow` | no vehicle_common row | 53 | 29 | 10 | `CAirPlane`, `CCar`, `CHelicopter` | proven-on-CCar |
| `RearLeftDoor` | door (name only) | 50 | 50 | 16 | `CAirPlane`, `CCar`, `CHelicopter` | proven-on-CCar |
| `Propeller` | rotating, `propeller_rpm` | 47 | 25 | 9 | `CBoat` | unproven-on-CCar |
| `CenterRightWindow` | no vehicle_common row | 43 | 29 | 9 | `CAirPlane`, `CBoat`, `CCar`, `CHelicopter` | proven-on-CCar |
| `Rudder` | hinged, `steering_yaw` | 41 | 20 | 7 | `CAirPlane`, `CBoat` | unproven-on-CCar |
| `BoatEngine` | hinged, `steering_turn` | 38 | 22 | 8 | `CBoat` | unproven-on-CCar |
| `Elevator` | hinged, `steering_pitch` | 36 | 18 | 6 | `CAirPlane` | unproven-on-CCar |
| `CargoBayDoor` | door (name only) | 28 | 10 | 2 | `CAirPlane`, `CBoat` | unproven-on-CCar |
| `SteeringFork` | hinged, `steering_angle_inverted` | 27 | 27 | 11 | `CBoat`, `CCar`, `CMotorBike` | proven-on-CCar |
| `BavariumShield` | no vehicle_common row | 26 | 14 | 4 | `CCar`, `CHelicopter` | proven-on-CCar |
| `GatlingGun` | rotating, `weapon_rpm` | 24 | 12 | 3 | `CBoat`, `CHelicopter` | unproven-on-CCar |
| `MainRotor` | rotating, `main_rotor_rpm` | 24 | 24 | 7 | `CHelicopter` | unproven-on-CCar |
| `Turret` | no vehicle_common row | 22 | 22 | 7 | `CBoat`, `CCar` | proven-on-CCar |
| `CenterRightDoor` | door (name only) | 21 | 19 | 5 | `CAirPlane`, `CCar` | proven-on-CCar |
| `LandingSkid` | no vehicle_common row | 21 | 12 | 4 | `CAirPlane`, `CHelicopter` | unproven-on-CCar |
| `SteeringWheel` | hinged, `steering_turn` | 20 | 20 | 9 | `CBoat`, `CCar` | proven-on-CCar |
| `TailRotor` | rotating, `tail_rotor_rpm` | 19 | 19 | 6 | `CHelicopter` | unproven-on-CCar |
| `LeftAileron` | hinged, `steering_roll` | 18 | 18 | 6 | `CAirPlane` | unproven-on-CCar |
| `RightAileron` | hinged, `steering_roll_inverted` | 18 | 18 | 6 | `CAirPlane` | unproven-on-CCar |
| `CenterLeftDoor` | door (name only) | 17 | 17 | 4 | `CAirPlane`, `CCar` | proven-on-CCar |
| `MissileHatch` | door (name only) | 16 | 1 | 1 | `CTrain` | unproven-on-CCar |
| `Tail` | no vehicle_common row | 16 | 16 | 5 | `CAirPlane`, `CHelicopter` | unproven-on-CCar |
| `RearDoor` | door (name only) | 14 | 9 | 3 | `CCar` | proven-on-CCar |
| `Rotor` | rotating, `rotor_rpm` | 13 | 13 | 3 | `CAirPlane`, `CCar` | proven-on-CCar |
| `RearWagonCoupling` | no vehicle_common row | 12 | 12 | 3 | `CTrain` | unproven-on-CCar |
| `LeftWing` | door (name only) | 9 | 9 | 4 | `CAirPlane` | unproven-on-CCar |
| `RightWing` | door (name only) | 9 | 9 | 4 | `CAirPlane` | unproven-on-CCar |
| `LeftRotor` | rotating, `rotor_rpm` | 8 | 8 | 2 | `CAirPlane` | unproven-on-CCar |
| `RightRotor` | rotating, `rotor_rpm` | 8 | 8 | 2 | `CAirPlane` | unproven-on-CCar |
| `TailWing` | no vehicle_common row | 8 | 4 | 2 | `CAirPlane` | unproven-on-CCar |
| `Antenna` | no vehicle_common row | 7 | 5 | 2 | `CCar` | proven-on-CCar |
| `Axle` | no vehicle_common row | 6 | 3 | 1 | `CCar` | proven-on-CCar |
| `OuterLeftRotor` | rotating, `rotor_rpm` | 6 | 6 | 1 | `CAirPlane` | unproven-on-CCar |
| `OuterRightRotor` | rotating, `rotor_rpm` | 6 | 6 | 1 | `CAirPlane` | unproven-on-CCar |
| `TrimTab` | no vehicle_common row | 6 | 6 | 1 | `CCar` | proven-on-CCar |
| `TurretDoor` | door (name only) | 6 | 6 | 2 | `CCar` | proven-on-CCar |
| `FrontWagonCoupling` | no vehicle_common row | 5 | 5 | 2 | `CTrain` | unproven-on-CCar |
| `FrontWagonCouplingLinked` | no vehicle_common row | 5 | 5 | 2 | `CTrain` | unproven-on-CCar |
| `Stabilizer` | no vehicle_common row | 5 | 5 | 2 | `CAirPlane` | unproven-on-CCar |
| `WindshieldWiper` | no vehicle_common row | 4 | 2 | 1 | `CCar` | proven-on-CCar |
| `AirBrake` | hinged, `air_brakes_T` | 3 | 3 | 1 | `CAirPlane` | unproven-on-CCar |
| `EngineRotatingPart` | rotating, `engine_rpm` | 3 | 3 | 1 | `CCar` | proven-on-CCar |
| `RadarFast` | rotating, `radar_fast_rpm` | 3 | 3 | 1 | `CBoat` | unproven-on-CCar |
| `RadarSlow` | rotating, `radar_slow_rpm` | 3 | 3 | 1 | `CBoat` | unproven-on-CCar |

**67 behaviours** in use, **38** of them with a `vehicle_common` row. The **29** without one group like this in this record's reading - an inference, because none of them has a row to prove it:

* a Havok constraint or physics body (G2-13/G2-8): `Turret`, `Cannon`, `Axle`
* the deform and wheel system: `Wheel`, `Body`, `BrakeDrum`, `BrakeDisc`, `Engine`
* windows and couplings: `Windshield`, `FrontLeftWindow`, `FrontRightWindow`, `RearLeftWindow`, `RearRightWindow`, `RearWindow`, `CenterLeftWindow`, `CenterRightWindow`, `FrontWagonCoupling`, `FrontWagonCouplingLinked`, `RearWagonCoupling`

The remaining **10** are named by shipped parts but no G2 record read here names what moves them - `BrakeCalipers`, `TrainCargo`, `BavariumShield`, `LandingSkid`, `Tail`, `TailWing`, `Antenna`, `TrimTab`, `Stabilizer`, `WindshieldWiper` - so their mechanism is UNKNOWN. None of the 29 is evidence for a writer.

**Unproven on a car (30):** `LandingGear`, `LandingGearHatch`, `TrainCargo`, `Propeller`, `Rudder`, `BoatEngine`, `Elevator`, `CargoBayDoor`, `GatlingGun`, `MainRotor`, `LandingSkid`, `TailRotor`, `LeftAileron`, `RightAileron`, `MissileHatch`, `Tail`, `RearWagonCoupling`, `LeftWing`, `RightWing`, `LeftRotor`, `RightRotor`, `TailWing`, `OuterLeftRotor`, `OuterRightRotor`, `FrontWagonCoupling`, `FrontWagonCouplingLinked`, `Stabilizer`, `AirBrake`, `RadarFast`, `RadarSlow`.

Those are the behaviours a B-05 port cannot copy from another `CCar`: every user is
an aircraft, boat, helicopter, bike or train. `AirBrake` is the only behaviour the card names as a Q-1 probe: 3 parts on 1 chassis (v4602_plane_urga_fighterbomber; CAirPlane) and nothing on land.

## 3. The per-part arrays

| array | modules with rows (of 78) | rows | what a row stores |
|---|---|---|---|
| `door_parts[]` | 56 | 224 | `part_index` |
| `hinged_parts[]` | 28 | 148 | `part_index` |
| `rotating_parts[]` | 22 | 47 | `max_rpm_visible`, `min_rpm_visible`, `number_of_blades`, `part_index`, `position[0]`, `position[1]`, `position[2]`, `rotation_axis[0]`, `rotation_axis[1]`, `rotation_axis[2]`, `rpm_multiplier`, `rpm_opacity_transition` |

`door_parts[]` and `hinged_parts[]` store **only** a part index: the Serpente's
3 doors and the APC's 5 are indices, nothing else, and the 148 hinged rows
across 28 modules carry no axis or limit either - those come from `.physicsc`
(G2-13). `rotating_parts[]` is the one array with its own geometry: a part index
plus `max_rpm_visible`, `min_rpm_visible`, `number_of_blades`, `position[0]`, `position[1]`, `position[2]`, `rotation_axis[0]`, `rotation_axis[1]`, `rotation_axis[2]`, `rpm_multiplier`, `rpm_opacity_transition`.
The six G2-13 turreted samples (`TURRET.md` §3) fill `door_parts[]` - v0200 APC 5, v0201 medium tank 1, v0202 Bavarium tank 1, v0504 technical 4, v0600 armoured jeep 5, v0603 small tank 1 - and none fills `hinged_parts[]` or `rotating_parts[]` (max 0 / 0); their aim is the `.physicsc` hinge (G2-13), not these arrays.

## 4. Validation and limits

`jc3moving.py --check` re-reads the module and the census, rebuilds both files and
compares them: table row counts are 14 doors / 25 hinged / 12 rotating / 1 fin / 1 spring; every hinged row has a non-empty `target_position_variable` and every
rotating row an `rpm_variable`; every name in the door/fin/spring tables has no
members besides `name`; `Turret` and `Cannon` have no `vehicle_common` row; every
behaviour's proof follows from its chassis classes and every behaviour has a class;
the six turreted samples have no `hinged_parts[]`/`rotating_parts[]` rows; `AirBrake`
is on one `CAirPlane` chassis and unproven on a car.

**Limits.** The `vehicle_common` copy is read from one entity's container (the
Serpente civilian); no second copy exists in the index to diff against. The 15 declared-but-unused names (12 spider-leg parts, 2 elevons, `BoatRudder`)
have no user in the fleet, so their variables are declared, not exercised. The
array census covers the 78 parts modules in the local cache, not all 233 vehicle records.
The class map resolves 231 of the 233 records: 232 entities have a detail JSON and one of them
(`v4603_plane_urga_cargotransport_military_cargo_tank.ee`) declares both `CCar` and
`CAirPlane`, so it is dropped; every chassis that carries a behaviour still resolves
to one class (79 chassis, 0 with an empty list). Which
*code* writes a given variable (`steering_roll`, `hood_angle`) is not in any file
read here - the table proves the binding, not the writer.
