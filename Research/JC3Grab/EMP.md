# The EMP truck

G2-16. **Answer: yes for the effect, no as a weapon-slot copy.** Everything the truck's EMP
is - three parts, a `CForcePulse`, its explosion tune, an effect file and a use-item
trigger - lives inside the truck's own `.ee`. Any vehicle entity that carries the same
objects gets the same device; nothing in the files says whether the pulse actually fires
when the action runs (that is code), and no vehicle weapon slot in the game currently
holds the engine's EMP weapon class (`CEMPWeapon`).

## 1. The device

`rebel_emp_01` is a 794-member container with 454 objects; the device is
3 chassis parts on the flatbed:

| part | index | behaviour | parent | model |
|---|---|---|---|---|
| `oldtruck_emp_device_rebel` | 5 | None | 0 | `oldtruck_emp_device_rebel.lod` |
| `oldtruck_emp_device_core_rebel` | 46 | Rotor | 5 | `oldtruck_emp_device_core_rebel.lod` |
| `oldtruck_emp_device_core_rebel_partswap` | 47 | None | 5 | `oldtruck_emp_device_core_rebel_partswap.lod` |

The core is a `Rotor`: its `rotating_parts[]` row in the parts module names part 46, 6 blades, axis (0, 0, 1), `rpm_multiplier` 1, no visibility window (-1..-1).
`Rotor` takes its `rpm_variable` from `vehicle_common` (G2-14), so the spinning core is
the stock rotating-part mechanism, not a new one.

## 2. The pulse and its tune

The truck carries **two** force pulses - the ordinary explosion pulse every car has, and
the EMP:

| pulse | settings | position |
|---|---|---|
| `CForcePulse` | `car_explosion_medium.ftune` | (0, 0, 0) |
| `EMP` | `truck_emp.ftune` | (0, 2.0356, 0.6992) |

`truck_emp.ftunec` is 8 numbers and nothing else:

| member | EMP (`truck_emp`) | plain car blast (`car_explosion_medium`) |
|---|---|---|
| `PlayerDamage` | 100 | 500 |
| `PlayerDamageRadius` | 25 | 5 |
| `PlayerDamageRadiusPercentageMax` | 1 | 0 |
| `PlayerDamageRadiusMin` | 1 | 0 |
| `AIDamage` | 100 | 500 |
| `AIDamageRadius` | 25 | 5 |
| `AIDamageRadiusPercentageMax` | 1 | 0 |
| `AIDamageRadiusMin` | 1 | 0 |

So the data-side difference from a normal car explosion is **100 damage in 25 m instead
of 500 in 5 m, with the damage held at full for the whole radius**
(`*RadiusPercentageMax` 1.0 here, 0.0 on the plain blast; `*RadiusMin` 1.0 vs 0.0).

**Duration and what it disables are not in the files.** The tune has no duration, no
target class and no "disable" member; the disable semantics (engines, electronics, AI)
are in code. The pulse's other members are object-id properties, and only
5 of them differ from the plain explosion pulse:

| member | EMP | plain |
|---|---|---|
| `id:06A05F33` | 5FED74E7=FFFF7F53 | - |
| `id:4912FC04` | 0 | 1 |
| `id:AE6F7EFF` | 1 | 0 |
| `id:CF4F7880` | 1 | 0 |
| `id:D3DDD766` | EE5AEE78=FFFFD9E6 | 00000000 |

So besides the radius, an EMP is 3 flags and the `emp_flatbed_table`
material-effect table. What the flags mean is not named anywhere in the container; the
radius and the table's effect file are the only EMP-specific data with a readable name.

The pulse's object references:

| member | points at |
|---|---|
| `id:06A05F33` | `5FED74E7=FFFF7F53` - **no such object in the entity** |
| `id:D3DDD766` | `EE5AEE78=FFFFD9E6` - CMaterialEffectTable emp_flatbed_table |

## 3. Trigger

| object | value |
|---|---|
| `entry.use_item` (`CInteractionGraphEntry`) - state | `S_STUNT_USE_ITEM_VEHICLE` |
| prompt | `ui_activate_emp` |
| `trigger.use_item` (`CInteractionTrigger`) position | `(0, 1.3507, 2.396)` |
| trigger refs | `6D433019=FFFF8C71`, `E880D61A=0000CAE5` |

`trigger.use_item` is a 2x-scaled box over the flatbed, and `entry.use_item` runs the
state `S_STUNT_USE_ITEM_VEHICLE` with the prompt `ui_activate_emp`. There is **no object
reference from the trigger, the entry or the vehicle to the `EMP` pulse**, and the
trigger's own refs do not resolve inside the entity: the pulse is fired by whatever
executes that state, and the files prove only the action and its label.

The truck has **no weapon component at all** (no `CBulletWeaponBase`, no missile weapon,
no turret), so the EMP is not on any fire button.

## 4. Effects and sound

| file | size | in |
|---|---|---|
| `car_explosion_medium.ftunec` | 644 | emp_01 |
| `truck_emp.ftunec` | 633 | emp_01 |
| `explosion_emp_flatbed.effc` | 24015 | emp_01 |
| `rpg_explosion_water.effc` | 17231 | emp_01 |
| `wheel_explosion_notiremesh.effc` | 16879 | emp_01 |
| `explosion_template_trail.effc` | 11295 | emp_01 |
| `emp_active.effc` | 8783 | mm250 |

Only 3 of those are EMP files (`truck_emp.ftunec`, `explosion_emp_flatbed.effc`, `emp_active.effc`);
the rest are the stock explosion effects every car carries.

`emp_flatbed_table` maps every material slot to one effect hash, which is the embedded
`explosion_emp_flatbed.effc`; the entity also embeds the camera
`full_screen_effect.ctunec`. **No EMP sound**: the container's attached effects are the
ordinary vehicle set (engine, horn, gear change, damage fires, exhaust) - there is no
`SAttachedEffect` naming emp, and the only weapon-side EMP sounds are on `w702`'s
charging/charged/fire effects.

## 5. The two builds, and every other oldtruck variant

| | `rebel_emp_01` | `rebel_emp_custom_mm250` |
|---|---|---|
| container members | 794 | 794 |
| objects | 454 | 454 |
| parts (module) | 78 | 78 |
| EMP parts | 3 | 3 |
| `CForcePulse` named EMP | 1 | 0 |
| `truck_emp.ftunec` | yes | no |
| `emp_active.effc` | no | yes |
| EMP emitters | - | epe_emp_powering_up |
| use-item prompt | ui_activate_emp | ui_activate_emp |
| weapon classes | none | none |

Same members, same parts, same trigger, same prompt; the mm250 build **drops the pulse
and its tune** and adds the charging prop: `CEffectPointEmitter epe_emp_powering_up`
(effect hash -1458959942, `enabled` 0) over the device at (-0.011, 2.448, 0.07),
which is the mission prop (`mm250` is the escort mission's EMP truck). The blast in
that mission is the script's.

| oldtruck variant | parts | device parts in module | `CPartProp`s | EMP pulse |
|---|---|---|---|---|
| `v0505_car_solar_oldtruck_commercial_01.ee` | 78 | 3 | 0 | 0 |
| `v0505_car_solar_oldtruck_commercial_cargo_barrel.ee` | 78 | 3 | 0 | 0 |
| `v0505_car_solar_oldtruck_commercial_cargo_random.ee` | 78 | 3 | 0 | 0 |
| `v0505_car_solar_oldtruck_commercial_cargo_wine.ee` | 78 | 3 | 0 | 0 |
| `v0505_car_solar_oldtruck_debug.ee` | 78 | 3 | 0 | 0 |
| `v0505_car_solar_oldtruck_military_01.ee` | 78 | 3 | 0 | 0 |
| `v0505_car_solar_oldtruck_rebel_01.ee` | 78 | 3 | 0 | 0 |
| `v0505_car_solar_oldtruck_rebel_emp_01.ee` | 78 | 3 | 3 | 1 |
| `v0505_car_solar_oldtruck_rebel_emp_custom_mm250.ee` | 78 | 3 | 3 | 0 |

The parts module is **shared by all 9 variants** - the three device
parts and the spinning core are compiled into every oldtruck, which is why the mesh list
of the civilian truck contains `oldtruck_emp_device_*.rbm`. What the EMP builds add is
the three `CPartProp` objects (2 variants), the `EMP` pulse and its tune
(2 variants), the trigger and the prompt; the other 7
variants have the geometry but no props, no pulse and no trigger, so nothing calls
it.

## 6. The weaponised EMP

The engine does have an EMP weapon class, in two files:

| | `w702_emp` | `w503_turret_emp` |
|---|---|---|
| kind | handheld | static turret |
| class | CEMPWeapon | CEMPWeapon |
| weapon id / type | 702 / 6 | 503 / 2 |
| fire point | `FirePosition` (0, 0.13, -0.69) | `fire_position_1` (0, 3.762, -9.708) |
| components | CBarrelSpinWeaponComponent x3, CInteractionComponentPickup x1, CWallPenetrationWeaponComponent x1 | CTurretWeaponComponent x1 |
| tune | w702_emp.wtunec | w503_turret_emp.wtunec |
| tune EMP fields | **none** | **none** |
| damage / range | 500 / 50 m | 500 / 750 m |

Both use the stock `fow_weapon` tune: the EMP table has **no EMP-specific field in
either file** - the tune carries damage, range, recoil and magazine, and the EMP
behaviour is keyed entirely off the `CEMPWeapon` class in code. `w702` is the handheld
two-handed variant (spin-up dials via three `CBarrelSpinWeaponComponent`s, wall
penetration, charging/charged/fire effects and sounds); `w503` is the static prop with
its own rigid objects, hinge and a `CTurretWeaponComponent`.

## 7. Copy list - what the Batmobile would need

| what | value |
|---|---|
| part | `oldtruck_emp_device_rebel` (None, index 5, parent 0) |
| part | `oldtruck_emp_device_core_rebel` (Rotor, index 46, parent 5) |
| part | `oldtruck_emp_device_core_rebel_partswap` (None, index 47, parent 5) |
| file | `editor/entities/jc_explosions/vehicles/truck_emp.ftunec` |
| file | `effects/destruction/explosion_emp_flatbed.effc` |
| file | `effects/props/emp_active.effc` |
| pulse ref | `id:D3DDD766` -> `CMaterialEffectTable` `emp_flatbed_table` |
| pulse | `CForcePulse` `EMP`, `truck_emp.ftune` |
| parts entry | `CPartProp` per part, and the module's `rotating_parts[]` row for the core |
| trigger | `trigger.use_item` box + `entry.use_item` -> `S_STUNT_USE_ITEM_VEHICLE`, prompt `ui_activate_emp` |

`car_explosion_medium.ftunec` is the stock blast every car carries and needs no copy.

Models live under `models/jc_vehicles/01_land/v0505_car_solar_oldtruck/
oldtruck_emp_device_*`; the textures are under
`models/jc_environments/structures/rebel/dimahs_lab/emp_device_01/`. The device also
needs the vehicle's interaction graph (a stunt-vehicle graph in this entity), so on a
entity without one the trigger has nothing to run.

## 8. Validation and limits

`jc3emp.py --check` rebuilds both files from the game archives and asserts: both builds
are 794-member containers with 454 objects; `emp_01` has the
plain pulse plus `EMP` on `truck_emp.ftune` at (0, 2.0356, 0.6992), whose 8 tune values are
100/25/1/1 for players and AI; the plain blast tune is 500/5/0/0; the 3 EMP parts exist,
the core is `Rotor` at index 46 with a 6-blade +Z `rotating_parts[]` row; `entry.use_item`
is `S_STUNT_USE_ITEM_VEHICLE` with prompt `ui_activate_emp` and `trigger.use_item` sits on the
flatbed; no weapon component is on the truck; only the EMP build carries `truck_emp.ftunec`
while both embed `explosion_emp_flatbed.effc`; `mm250` has the powered-up emitter and no
pulse; every oldtruck variant carries the 3 device parts in its module but only the two
EMP builds carry the `CPartProp`s and the pulse; `w702`/`w503` are
`CEMPWeapon` with types 6/2, `w503` carrying a `CTurretWeaponComponent`, and neither tune
has an EMP-named field; no `CEMPWeapon` appears among the fleet's vehicle weapon
components.

**Limits.** Duration, the disable effect and the meaning of the three flags are not in
any decoded member - they are code. The link from the use-item state to the pulse is
likewise absent, so "the driver presses use item and the pulse fires" is inferred from
the shared entity plus the `ui_activate_emp` prompt, not read from a pointer. Whether the
engine accepts `CEMPWeapon` in a vehicle slot cannot be decided from data; the two
existing users are a handheld and a static prop, and the 88 vehicle weapon components in
`WEAPON_WIRING` include none. The device also needs the stunt-vehicle interaction graph;
the donor's graph is what supplies `entry.use_item`.
