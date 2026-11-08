# `CForcePulse` - the fleet's blast component

G2-17. **Trigger: explosion, and the owner says which explosion.** Every one of the
307 pulses in 232 vehicle `.ee` files is a
blast: its `SettingsFile` names one of 23 explosion tunes, and no tune path or pulse name in the whole
fleet mentions a horn or a collision. What the card really needs is *which* event
fires it, and that is written as a pointer: 293 of 307 pulses are
pointed at by exactly one owner object through `id:B5AE7986` - the vehicle root
for the vehicle's own blast, the weapon component for that weapon's blast. The
14 without an owner are recorded as **UNKNOWN**, not explained: the
barrel blasts nest under their `CRigidObject` and point out at their own entity,
but nothing points at them, and the EMP pulse has no owner
at all, so "the use-item action fires it" stays an inference from G2-16 and becomes
a Q-1 probe.

## 1. Members - every property of every pulse

A pulse carries 31 distinct members: the 5 named ones below plus 26 Jenkins-hashed `id:*` keys
whose names are in no shipped name table (UNKNOWN; G2-11 recovered six such names,
this hash family matched none). `world` is on every pulse. The members that are not
universal: `id:06A05F33` on 14, `id:73D4D940` on 10, `id:7FD59340` on 1, and `id:593FCDBF`, `id:71446B1A`, `id:879640EA`, `id:9BD6FA33` declared empty on all 307. Values are counted over all
pulses in `FORCEPULSE.json` `entities[].pulses[].props`.

| member | kind | set on | distinct | values / range |
|---|---|---:|---:|---|
| `SettingsFile` | named | 307 | 23 | 23 distinct |
| `_object_id` | named | 307 | 307 | 307 distinct |
| `id:060AAA81` | hashed | 307 | 3 | 5 .. 60 |
| `id:06A05F33` | hashed | 14 | 15 | 15 distinct |
| `id:1AF6FDF0` | hashed | 307 | 1 | 0 .. 0 |
| `id:24872388` | hashed | 307 | 6 | 25 .. 1000 |
| `id:2849C306` | hashed | 307 | 2 | 0 .. 1 |
| `id:34303F77` | hashed | 307 | 2 | 0 .. 1 |
| `id:4912FC04` | hashed | 307 | 2 | 0 .. 1 |
| `id:530046B3` | hashed | 307 | 9 | 0 .. 50 |
| `id:57F1B4E1` | hashed | 307 | 2 | 0.1 .. 0.25 |
| `id:593FCDBF` | hashed | 0 | 1 | `(empty)` |
| `id:5AF29116` | hashed | 307 | 2 | 0 .. 1 |
| `id:6B47B5C3` | hashed | 307 | 1 | 0 .. 0 |
| `id:71446B1A` | hashed | 0 | 1 | `(empty)` |
| `id:73D4D940` | hashed | 10 | 10 | 10 distinct |
| `id:74896A12` | hashed | 307 | 1 | 0 .. 0 |
| `id:7FD59340` | hashed | 1 | 2 | `(empty)`, `77593580=00005CB4, 531120FC=00009CDB` |
| `id:831DAB81` | hashed | 307 | 2 | 0 .. 1 |
| `id:879640EA` | hashed | 0 | 1 | `(empty)` |
| `id:9865E7F2` | hashed | 307 | 5 | 25 .. 250 |
| `id:9BD6FA33` | hashed | 0 | 1 | `(empty)` |
| `id:A1B0DAF9` | hashed | 307 | 4 | -1 .. 3 |
| `id:AE6F7EFF` | hashed | 307 | 2 | 0 .. 1 |
| `id:CF4F7880` | hashed | 307 | 2 | 0 .. 1 |
| `id:D04059E6` | hashed | 307 | 1 | -1.12895e+09 .. -1.12895e+09 |
| `id:D3DDD766` | hashed | 307 | 46 | 46 distinct |
| `id:F39EC6EA` | hashed | 307 | 3 | 0.1 .. 0.8 |
| `name` | named | 307 | 9 | 9 distinct |
| `name_hash` | named | 307 | 9 | -1.90589e+09 .. 1.964e+09 |
| `world` | named | 307 | 6 | `-0.4117212,7.753542E-09,0.9113098,0, 3.599381E-08,1,7.753538E-09,0, -0.9113098,3.599381E-08,-0.4117212,0, -9.615967,-2.375854,-4.269531,1`, `-1,0,-8.742278E-08,0, 0,1,0,0, 8.742278E-08,0,-1,0, 0,4.810059,0,1`, `1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1`, `1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0.261266,5.500241,1`, `1,0,0,0, 0,1,0,0, 0,0,1,0, 0,2.035645,0.6992188,1`, `1,0,0,0, 0,1,0,0, 0,0,1,0, 0.01292753,0.5109417,0,1` |

`_object_id` is of course unique per object; `name` holds 9 spellings; `SettingsFile`
holds 23 tunes; the hashed members are the interesting ones - three
flags (`id:4912FC04`, `id:AE6F7EFF`, `id:CF4F7880`), one object reference to a
`CMaterialEffectTable` (`id:D3DDD766`), and `id:B5AE7986`, which is the *incoming*
pointer from the owner, not a member of the pulse itself (see §4).

Pointers that leave the pulse, resolved against the same graph (empty values such as
`00000000` are not counted):

| member | resolved target class (values) |
|---|---|
| `id:06A05F33` | `(unresolved)` 15 |
| `id:73D4D940` | `CEntityObject` 10 |
| `id:7FD59340` | `(unresolved)` 2 |
| `id:D3DDD766` | `CMaterialEffectTable` 45 |

`id:73D4D940` is the only pointer that leads anywhere: 10 values naming `CEntityObject` - a root-level `CEntityObject` next to the barrel `CRigidObject`, not its parent.
The `vec_events` members hold
event ids whose names are not in the files.

## 2. The fleet

| quantity | count |
|---|---:|
| detail graphs read | 232 |
| entities carrying a pulse | 232 |
| `CForcePulse` objects | 307 |
| chassis | 79 |
| entities with more than one pulse | 41 |
| entities with an `SAttachedEffect horn` | 178 |
| references to a pulse from any other member (besides `id:B5AE7986`) | 1 |
| `FEATURE_CENSUS.json` agrees | objects 307, `.ee` 232, chassis 79 |

By root class: `(none)` 19, `CAirPlane` 18, `CBoat` 35, `CCar` 125, `CHelicopter` 23, `CTrain` 12.

| pulse name | tune | objects |
|---|---|---:|
| `CForcePulse` | `airplane_explosion_medium.ftune` | 18 |
| `CForcePulse` | `bike_explosion_medium.ftune` | 19 |
| `CForcePulse` | `boat_explosion_large.ftune` | 8 |
| `CForcePulse` | `boat_explosion_medium.ftune` | 27 |
| `CForcePulse` | `car_explosion_medium.ftune` | 115 |
| `CForcePulse` | `fuel_tank_spherical_explosion_01.ftune` | 11 |
| `CForcePulse` | `helicopter_explosion_medium.ftune` | 23 |
| `CForcePulse` | `prototype_missile_explosion_sam.ftune` | 1 |
| `CForcePulse` | `rpg_assault_helicopter.ftune` | 23 |
| `CForcePulse` | `train_explosion_medium.ftune` | 12 |
| `CForcePulse` | `w613_bomb.ftune` | 3 |
| `CForcePulse` | `w615_helicopter_heavy_missile.ftune` | 3 |
| `EMP` | `truck_emp.ftune` | 1 |
| `ForcePulse` | `gen_explosion_5m_nodamage.ftune` | 2 |
| `ForcePulse` | `w604_helicopter_mgun_impact.ftune` | 11 |
| `ForcePulse` | `w610_fighterjet_mgun_impact.ftune` | 3 |
| `ForcePulse` | `w617_vintagefighter_mgun_impact.ftune` | 2 |
| `explosion_force_pulse` | `w704_m488.ftune` | 1 |
| `force` | `barrel_explosion.ftune` | 10 |
| `w602_mediumtank_canon` | `w602_mediumtank_canon.ftune` | 7 |
| `w605_smalltank_canon` | `w605_smalltank_canon.ftune` | 3 |
| `w616_corvette_canon` | `w616_corvette_canon.ftune` | 3 |
| `w618_sportsmuscle_missile` | `w618_sportsmuscle_missile.ftune` | 1 |

Positions: `(-9.616, -2.3759, -4.2695)` x1, `(0.0, 0.0, 0.0)` x292, `(0.0, 0.2613, 5.5002)` x2, `(0.0, 2.0356, 0.6992)` x1, `(0.0, 4.8101, 0.0)` x1, `(0.0129, 0.5109, 0.0)` x10.
Everything sits at the entity origin except the EMP pulse (over the flatbed device)
and the barrel/cargo pulses (on the cargo).

## 3. Tunes and fleet ranges

Every `SettingsFile` resolves to an embedded `<tune>.ftunec` in the same `.ee`, eight
`ForcePulseSettings` numbers each, and the same tune decodes identically in every
entity that carries it:

| tune | group | objects | `.ee` | chassis | Player dmg / r | AI dmg / r |
|---|---|---:|---:|---:|---|---|
| `gen_explosion_5m_nodamage.ftune` | explosions | 2 | 1 | 1 | 0 / 5 | 0 / 5 |
| `barrel_explosion.ftune` | structures | 10 | 1 | 1 | 500 / 6.5 | 500 / 6.5 |
| `fuel_tank_spherical_explosion_01.ftune` | structures | 11 | 11 | 10 | 1000 / 50 | 1000 / 50 |
| `airplane_explosion_medium.ftune` | vehicles | 18 | 18 | 6 | 500 / 10 | 500 / 10 |
| `bike_explosion_medium.ftune` | vehicles | 19 | 19 | 9 | 350 / 10 | 350 / 10 |
| `boat_explosion_large.ftune` | vehicles | 8 | 8 | 2 | 500 / 15 | 500 / 15 |
| `boat_explosion_medium.ftune` | vehicles | 27 | 27 | 10 | 500 / 10 | 500 / 10 |
| `car_explosion_medium.ftune` | vehicles | 115 | 115 | 43 | 500 / 5 | 500 / 5 |
| `helicopter_explosion_medium.ftune` | vehicles | 23 | 23 | 7 | 500 / 5 | 500 / 5 |
| `train_explosion_medium.ftune` | vehicles | 12 | 12 | 3 | 100 / 10 | 100 / 10 |
| `truck_emp.ftune` | vehicles | 1 | 1 | 1 | 100 / 25 | 100 / 25 |
| `rpg_assault_helicopter.ftune` | weapons | 23 | 17 | 6 | 1200 / 10 | 500 / 10 |
| `w602_mediumtank_canon.ftune` | weapons | 7 | 7 | 3 | 1500 / 8 | 550 / 6 |
| `w604_helicopter_mgun_impact.ftune` | weapons | 11 | 11 | 3 | 25 / 1.5 | 0 / 0 |
| `w605_smalltank_canon.ftune` | weapons | 3 | 3 | 1 | 1100 / 8 | 500 / 8 |
| `w610_fighterjet_mgun_impact.ftune` | weapons | 3 | 3 | 1 | 100 / 5 | 0 / 0 |
| `w613_bomb.ftune` | weapons | 3 | 3 | 1 | 1500 / 25 | 500 / 10 |
| `w615_helicopter_heavy_missile.ftune` | weapons | 3 | 3 | 1 | 2200 / 20 | 500 / 20 |
| `w616_corvette_canon.ftune` | weapons | 3 | 3 | 1 | 1500 / 8 | 300 / 6 |
| `w617_vintagefighter_mgun_impact.ftune` | weapons | 2 | 2 | 1 | 150 / 5 | 0 / 0 |
| `w618_sportsmuscle_missile.ftune` | weapons | 1 | 1 | 1 | 1100 / 8 | 500 / 8 |
| `w704_m488.ftune` | weapons | 1 | 1 | 1 | 3000 / 50 | 1000 / 25 |
| `prototype_missile_explosion_sam.ftune` | other | 1 | 1 | 1 | 400 / 15 | 400 / 7 |

Fleet ranges over those tunes (the card's "fleet ranges"):

| tune member | min | max | tunes |
|---|---:|---:|---:|
| `AIDamage` | 0 | 1000 | 23 |
| `AIDamageRadius` | 0 | 50 | 23 |
| `AIDamageRadiusMin` | 0 | 1 | 23 |
| `AIDamageRadiusPercentageMax` | 0 | 1 | 23 |
| `PlayerDamage` | 0 | 3000 | 23 |
| `PlayerDamageRadius` | 1.5 | 50 | 23 |
| `PlayerDamageRadiusMin` | 0 | 1 | 23 |
| `PlayerDamageRadiusPercentageMax` | 0 | 1 | 23 |

The spread is the point: the same class runs from `gen_explosion_5m_nodamage`
(0 damage, push only) through the stock car blast (500/5 m) to `w704_m488`
(3000/50 m) and the fuel-tank blast (1000/50 m). `*RadiusPercentageMax`/`*RadiusMin`
say how much of the radius keeps full damage - 0.0/0.0 on the stock vehicle blasts
(damage falls off at once), 1.0/1.0 on the EMP and the bomb.

## 4. What fires a pulse

### 4.1 The card's three candidates, by the files

| candidate | evidence | verdict |
|---|---|---|
| horn | 178 entities carry an `SAttachedEffect` named `horn`; 0 of 23 tune paths and 0 of 9 pulse names mention a horn | horn does not trigger a pulse |
| collision | 0 of 23 tune paths mention collision; no pulse owner is a collision object | collision does not trigger a pulse |
| explosion | 22 of 23 tunes live under `jc_explosions/` and the remaining one is named `prototype_missile_explosion_sam` | every pulse is an explosion blast |

### 4.2 The owner pointer

`id:B5AE7986` is set on the owner object and holds the pulse's `_object_id`.
Owners, counted per pulse:

| owner class | pulses |
|---|---:|
| `(none)` | 14 |
| `CAirPlane` | 18 |
| `CBoat` | 35 |
| `CBulletWeaponBase` | 29 |
| `CCar` | 126 |
| `CHelicopter` | 23 |
| `CMissileWeaponBase` | 25 |
| `CMotorBike` | 19 |
| `CRPGFireLeachWeapon` | 6 |
| `CTrain` | 12 |

- **214 pulses are owned by the vehicle root class** (CAirPlane, CBoat, CCar, CHelicopter, CTrain) and every one of them uses the
  explosion tune for that vehicle's own type - so the vehicle carries *its* blast,
  which is what a destroyed vehicle sets off. The event that reads the pointer is
  code: the files prove the owner and the tune, not the moment (that part of the
  trigger is UNKNOWN and belongs to Q-1).
- **54 pulses are owned by a weapon component** (CBulletWeaponBase, CMissileWeaponBase, CRPGFireLeachWeapon) and each uses that weapon's own
  blast tune (`jc_explosions/weapons/<id>.ftune`) - so the weapon's projectile
  carries the blast. Which instant (fire or impact) is code, but the pairing is
  exact: the pulse only exists on entities that are wired for that weapon id.

Exactly one other reference to a pulse exists in the fleet, and it is a script, not
an owner: `v4603_plane_urga_cargotransport_mm340.ee` `CGraphScriptGameObject` `GraphScript` -> `id:65424AC6` -> `875B9AD5=FFFF75FD`. The target is that build's `BOMB_JEEP` vehicle-rule pulse (tune `w704_m488`), so
the rule's graph is part of how that pulse is used - the graph's bytecode is not
decoded here, so what it does with the pulse is UNKNOWN.

### 4.3 Pulses with no owner

| entity | pulse | tune | nested under |
|---|---|---|---|
| `v0505_car_solar_oldtruck_commercial_cargo_barrel.ee` | `force` | `barrel_explosion.ftune` | `CRigidObject` `barrel` |
| `v0505_car_solar_oldtruck_commercial_cargo_barrel.ee` | `force` | `barrel_explosion.ftune` | `CRigidObject` `barrel` |
| `v0505_car_solar_oldtruck_commercial_cargo_barrel.ee` | `force` | `barrel_explosion.ftune` | `CRigidObject` `barrel` |
| `v0505_car_solar_oldtruck_commercial_cargo_barrel.ee` | `force` | `barrel_explosion.ftune` | `CRigidObject` `barrel` |
| `v0505_car_solar_oldtruck_commercial_cargo_barrel.ee` | `force` | `barrel_explosion.ftune` | `CRigidObject` `barrel` |
| `v0505_car_solar_oldtruck_commercial_cargo_barrel.ee` | `force` | `barrel_explosion.ftune` | `CRigidObject` `barrel` |
| `v0505_car_solar_oldtruck_commercial_cargo_barrel.ee` | `force` | `barrel_explosion.ftune` | `CRigidObject` `barrel` |
| `v0505_car_solar_oldtruck_commercial_cargo_barrel.ee` | `force` | `barrel_explosion.ftune` | `CRigidObject` `barrel` |
| `v0505_car_solar_oldtruck_commercial_cargo_barrel.ee` | `force` | `barrel_explosion.ftune` | `CRigidObject` `barrel` |
| `v0505_car_solar_oldtruck_commercial_cargo_barrel.ee` | `force` | `barrel_explosion.ftune` | `CRigidObject` `barrel` |
| `v0505_car_solar_oldtruck_commercial_cargo_random.ee` | `ForcePulse` | `gen_explosion_5m_nodamage.ftune` | `CRigidObject` `air_conditioner01_01a_big_debris` |
| `v0505_car_solar_oldtruck_commercial_cargo_random.ee` | `ForcePulse` | `gen_explosion_5m_nodamage.ftune` | `CRigidObject` `air_conditioner01_01a_big_debris` |
| `v0505_car_solar_oldtruck_rebel_emp_01.ee` | `EMP` | `truck_emp.ftune` | `CCar` `v0505_car_solar_oldtruck_rebel_emp_01` |
| `v4603_plane_urga_cargotransport_mm340.ee` | `explosion_force_pulse` | `w704_m488.ftune` | `CVehicleRule` `BOMB_JEEP` |

The barrel blasts are children of their own `CRigidObject barrel` and each carries
an outgoing `id:73D4D940` pointer to a `CEntityObject` (10 of 14 unowned pulses), so an `EntityObject` of the cargo build is named in the data - but no
member points *at* the pulse, so the link is nesting plus an outgoing pointer, not
an owner. The **EMP pulse has no owner and no parent but the vehicle
root**: G2-16 showed `entry.use_item` -> `S_STUNT_USE_ITEM_VEHICLE` with prompt
`ui_activate_emp` and no pointer to the pulse, so "use item fires the EMP" remains
an inference and is **UNKNOWN in data -> Q-1 probe**.

## 5. Vehicles that differ in behaviour

| | pulses (name -> tune, owner) |
|---|---|
| donor, civilian | `CForcePulse` -> `car_explosion_medium.ftune` (CCar) |
| donor, armed | `CForcePulse` -> `car_explosion_medium.ftune` (CCar)<br>`w618_sportsmuscle_missile` -> `w618_sportsmuscle_missile.ftune` (CMissileWeaponBase) |
| medium tank | `CForcePulse` -> `car_explosion_medium.ftune` (CCar)<br>`w602_mediumtank_canon` -> `w602_mediumtank_canon.ftune` (CBulletWeaponBase) |
| corvette | `w616_corvette_canon` -> `w616_corvette_canon.ftune` (CBulletWeaponBase)<br>`CForcePulse` -> `boat_explosion_large.ftune` (CBoat) |
| plain oldtruck | `CForcePulse` -> `car_explosion_medium.ftune` (CCar) |
| oldtruck, barrels | `force` -> `barrel_explosion.ftune` (**none**)<br>`force` -> `barrel_explosion.ftune` (**none**)<br>`force` -> `barrel_explosion.ftune` (**none**)<br>`force` -> `barrel_explosion.ftune` (**none**)<br>`force` -> `barrel_explosion.ftune` (**none**)<br>`force` -> `barrel_explosion.ftune` (**none**)<br>`CForcePulse` -> `car_explosion_medium.ftune` (CCar)<br>`force` -> `barrel_explosion.ftune` (**none**)<br>`force` -> `barrel_explosion.ftune` (**none**)<br>`force` -> `barrel_explosion.ftune` (**none**)<br>`force` -> `barrel_explosion.ftune` (**none**) |
| oldtruck, loose cargo | `ForcePulse` -> `gen_explosion_5m_nodamage.ftune` (**none**)<br>`ForcePulse` -> `gen_explosion_5m_nodamage.ftune` (**none**)<br>`CForcePulse` -> `car_explosion_medium.ftune` (CCar) |
| oldtruck, EMP | `CForcePulse` -> `car_explosion_medium.ftune` (CCar)<br>`EMP` -> `truck_emp.ftune` (**none**) |
| assault helicopter | `CForcePulse` -> `w615_helicopter_heavy_missile.ftune` (CMissileWeaponBase)<br>`CForcePulse` -> `rpg_assault_helicopter.ftune` (CMissileWeaponBase)<br>`CForcePulse` -> `helicopter_explosion_medium.ftune` (CHelicopter) |

- **same chassis, armed or not**: the donor's civilian build has one pulse, its own
  car blast; the signature build adds the `w618_sportsmuscle_missile` blast owned by
  its `CMissileWeaponBase`. The weapon is the only difference.
- **two weapons, one blast**: on the medium tank the cannon's `w602` pulse is owned
  by `CBulletWeaponBase w602_mediumtank_canon` while the coax `w603` component's
  `id:B5AE7986` is `00000000` - the machine gun has no force pulse at all.
- **same class, different blast**: the corvette uses `boat_explosion_large` (500/15 m)
  where every other boat uses `boat_explosion_medium` (500/10 m).
- **one chassis, four behaviours**: the oldtruck's plain build has only the car blast;
  the barrel build nests ten `barrel_explosion` pulses under its cargo; the loose-cargo
  build carries two `gen_explosion_5m_nodamage` pulses (0 damage - push only); the
  EMP build adds the unowned EMP pulse (100/25 m at full radius).
- **helicopter**: the assault helicopter's root owns `helicopter_explosion_medium`,
  `CMissileWeaponBase w601_helicopter_missile` owns `rpg_assault_helicopter`
  (1200/10 m) and `CMissileWeaponBase w615_helicopter_heavy_missile` owns its own
  2200/20 m blast - one pulse per wired weapon, plus the vehicle's own.

## 6. Validation and limits

`jc3forcepulse.py --check` re-decodes all 232 entities from the archives, rebuilds
`FORCEPULSE.json` and `FORCEPULSE.md` byte for byte and asserts the invariants:
307 objects over 232 `.ee` and 79 chassis (the numbers P0-2's census printed); the 31 members with exactly the 5 named ones (`world` on all 307); 23 tunes all resolving to a decoded `.ftunec`, grouped explosions 1, other 1, structures 2, vehicles 8, weapons 11; `car_explosion_medium` 500/5/0/0; the EMP pulse at (0, 2.0356, 0.6992) with
100/25/1/1 (G2-16's numbers); the owner census {'(none)': 14, 'CAirPlane': 18, 'CBoat': 35, 'CBulletWeaponBase': 29, 'CCar': 126, 'CHelicopter': 23, 'CMissileWeaponBase': 25, 'CMotorBike': 19, 'CRPGFireLeachWeapon': 6, 'CTrain': 12}; exactly 1 reference that is not the owner
pointer, and it is the mm340 `GraphScript`; 0 horn and 0 collision tunes; and the
census file agreeing object for object. Tamper test: change one pulse member in the json
and `--check` must fail, rebuild and it passes again.

**Limits.** The pointer's *name* is UNKNOWN (a Jenkins hash with no dictionary hit),
so what the engine calls it cannot be stated. The owner pointer proves who carries
the blast, not the code path that fires it - the firing moment for the vehicle blast
and the exact weapon instant are not in any file. Which code runs after
`S_STUNT_USE_ITEM_VEHICLE` is likewise not in the files, so the EMP trigger stays
UNKNOWN (Q-1). The outgoing pointers on the unowned pulses resolve to an object id
only when the target is in the same graph; the mm340 graph's bytecode is not decoded,
so what it does with its pulse is UNKNOWN. The census covers the 232
decoded vehicle graphs, not every `.ee` in the index.
