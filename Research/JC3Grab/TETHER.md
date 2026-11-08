# Tether, airlift and winch carriers (G2-34)

What the JC3 files supply for **WLD-7** (Rico's tether, helicopter airlift and the cargo
plane around a 6 t car) and **WPN-6** (a power winch a car could carry). Every number
below is re-derived by `Tools/scripts/jc3tether.py --check`; no archive is opened and no
game is launched.

| input | value |
|---|---|
| entity caches | 232 |
| `.epe` graphs | 232 |
| parts-table entities | 233 |
| `INDEX.jsonl` rows | 81,952 |

## 1. Vehicle mass - the half of WLD-7 the data does carry

`RigidBody.mass` is on **232 entities**; 231 have one body. The unit is **UNKNOWN** - the file gives a
number and no unit - so every comparison here is a ratio, never a conversion.

| family (model code) | entities | min | median | max |
|---|---|---|---|---|
| `bike` | 19 | 60 | 180 | 750 |
| `boat` | 35 | 500 | 23,500 | 150,000 |
| `car` | 125 | 50 | 2,000 | 550,000 |
| `helicopter` | 23 | 1,000 | 3,000 | 15,000 |
| `plane` | 17 | 800 | 3,000 | 40,000 |
| `train` | 12 | 15,000 | 22,000 | 40,000 |

The `17` single-body planes above exclude the two-body
cargo tank; its row below lists both bodies (plane 40,000 + carried tank 25,000).

- **donor** `v0300_car_kensington_sportsmuscle_civilian_01` = **975**
- **Batmobile** (WLD-7 design value, not a decoded number) = **6,000** = **6.154x** the donor

The three carriers WLD-7 names:

| model | entities | body mass | with a cargo bay |
|---|---|---|---|
| `v4603_plane_urga_cargotransport` | 6 | 25,000 / 40,000 | 6 |
| `v1602_boat_urga_transport` | 4 | 100,000 | 4 |
| `v5602_train_urga_monorailflatbed` | 4 | 15,000 | 2 |

So a 6,000 car is **15.0%** of the cargo plane's own body mass and **6.0%** of the transport boat's; **40.0%** of the flatbed's. Those are the only mass ratios WLD-7 can quote, because the
tether's own strength is in no table (below).

### Tether strength

**UNKNOWN, and provably absent from the tables.** Section 5 lists all 335 `tether` names
in the index: character dialogue, DLC dialogue, two upgrade icons, two upgrade videos, one
challenge decal and the two `dualtether_test_to_vehicle` graph files. No tune, no force,
no break threshold. No vehicle module carries a tether or rope member either (section 4).

## 2. Can a vehicle be carried? Yes - by the cargo plane, boat and flatbed

`CVehicleCargoBay` appears **12 times on 12 entities**, one
per entity, `enabled = 1`, doors empty:

| model | entities with a bay |
|---|---|
| `v4603_plane_urga_cargotransport` | 6 |
| `v1602_boat_urga_transport` | 4 |
| `v5602_train_urga_monorailflatbed` | 2 |

The object has exactly 7 members, and nothing else:

- `_object_id`, `disable`, `enable`, `enabled`, `name`, `name_hash`, `world`

So the bay carries a name hash and a transform, then stops. No capacity, no mass limit,
no attach rule: the fields are the same on all twelve:

| bay world transform | objects |
|---|---|
| `1,0,0,0, 0,1,0,0, 0,0,1,0, 0,1.292236,-2.511719,1` | 4 |
| `1,0,0,0, 0,1,0,0, 0,0,1,0, 0,4.2,5,1` | 6 |
| `1,0,0,0, 0,1,0,0, 0,0,1,0, 0,5.902588,-0.5029297,1` | 1 |
| `1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1` | 1 |

**Helicopters with a cargo bay: 0.** No helicopter in the fleet
has one, so the files give no helicopter that can carry a car (the native helicopter tow,
if it exists, is code - see section 6).

### The proof that a vehicle rides in a bay

`v4603_plane_urga_cargotransport_military_cargo_tank` carries **two vehicle roots** (`CAirPlane` x1, `CCar` x1) and **two bodies**: `25,000, 40,000` - the plane's own plus the carried tank's.
It is the only compound entity in the fleet, and the only decoded evidence that one
vehicle's entity contains another.

Only the planes have bay interaction points; the boat and the flatbed carry the bay and
its door effects without one. Every named bay object in the fleet:

| class · name | objects |
|---|---|
| `CVehicleCargoBay · VehicleCargoBay` | 12 |
| `SAttachedEffect · DoorClosingStartCargoBay` | 10 |
| `SAttachedEffect · DoorClosingEndCargoBay` | 10 |
| `SAttachedEffect · DoorOpeningStartCargoBay` | 10 |
| `SAttachedEffect · DoorOpeningEndCargoBay` | 10 |
| `CInteractionGraphPointNode · point.bay.cargo.doors` | 6 |
| `CInteractionGraphPointNode · point.bay.cargo.hold` | 6 |
| `CInteractionGraphEntry · entry.reel.to.stunt.bay.cargo.hold` | 6 |
| `CInteractionGraphEntry · entry.reel.to.stunt.bay.cargo.doors` | 6 |
| `CPartProp · cargotransport_cargobay` | 6 |
| `CSoundLayerEmitter · SoundLayer_CargoBay` | 6 |
| `CNamedPoint · respawn_point_for_rico_in_cargobay` | 1 |
| `CSpeaker · Speaker_inside_cargobay* (12 names)` | 6 |

Bay point transforms (all six planes, identical):

| point | world |
|---|---|
| `point.bay.cargo.doors` | `1,0,0,0, 0,1,0,0, 0,0,1,0, 0,3.109009,26.59424,1` |
| `point.bay.cargo.hold` | `1,0,0,0, 0,1,0,0, 0,0,1,0, 0,2.360596,1.009766,1` |

## 3. The prop-side tether data (`CGrapplingHookPropData`)

**33 objects on 3 entities** - a cargo truck and a
monorail flatbed's container prop, never a player vehicle:

| entity | objects |
|---|---|
| `v0505_car_solar_oldtruck_commercial_cargo_barrel` | 10 |
| `v0505_car_solar_oldtruck_commercial_cargo_random` | 13 |
| `v5602_train_urga_monorailflatbed_military_containers_rigidobject` | 10 |

| object name | objects |
|---|---|
| `GrapplingHookPropData` | 18 |
| `CGrapplingHookPropData` | 9 |
| `tether_tear` | 2 |
| `tether_tear7` | 2 |
| `tether_yank` | 2 |

| enabled | objects |
|---|---|
| `1` | 33 |

| enable_event | disable_event | objects |
|---|---|---|
| `(empty)` | `(empty)` | 33 |

`tether_tear`, `tether_tear7` and `tether_yank` - the names the card points at - are
object names on the loose cargo of one truck. They mark *which prop may be torn off or
yanked*, with an empty event pair, and carry no force, distance or mass.

## 4. A winch a car could carry (WPN-6)

The transport boat's parts module holds **40 rope/winch part rows on 4 entities** (transport_rope_01x4, transport_rope_02x4, transport_rope_03x4, transport_rope_pontoon_c_lx4, transport_rope_pontoon_c_rx4, transport_rope_pontoon_f_lx4, transport_rope_pontoon_f_rx4, transport_rope_pontoon_r_lx4, transport_rope_pontoon_r_rx4, transport_rope_winchx4):

| part_index | part | damage type | behavior | parent |
|---|---|---|---|---|
| 17 | `transport_rope_01` | `Boat_Generic` | `None` | 0 |
| 18 | `transport_rope_02` | `Boat_Generic` | `None` | 0 |
| 19 | `transport_rope_03` | `Boat_Generic` | `None` | 0 |
| 20 | `transport_rope_pontoon_c_l` | `Boat_Generic` | `None` | 0 |
| 21 | `transport_rope_pontoon_c_r` | `Boat_Generic` | `None` | 0 |
| 22 | `transport_rope_pontoon_f_l` | `Boat_Generic` | `None` | 0 |
| 23 | `transport_rope_pontoon_f_r` | `Boat_Generic` | `None` | 0 |
| 24 | `transport_rope_pontoon_r_l` | `Boat_Generic` | `None` | 0 |
| 25 | `transport_rope_pontoon_r_r` | `Boat_Generic` | `None` | 0 |
| 26 | `transport_rope_winch` | `Boat_Generic` | `None` | 0 |

All 10 distinct names are plain mesh parts: `Boat_Generic`, `behavior = None`,
`parent = 0`, no socket. The winch mesh is real and ships inside the entity - **6 files on one boat**, 12 distinct fleet-wide:

- `transport_rope_winch.lod`
- `transport_rope_winch_lod1.rbm`
- `transport_rope_winch_lod2.rbm`
- `transport_rope_winch_lod3.rbm`
- `transport_rope_winch_lod4.rbm`
- `transport_rope_winch_lod5.rbm`

The mechanic is not there:

- The fleet's 53 module types contain **0 tether/cargo/rope/winch/tow type** (none).
- Parts-module behaviours over all 11,643 fleet part rows: 7,367 `None`, **67 distinct named behaviours**, the
  commonest being `Wheel` x710, `BrakeCalipers` x330, `Windshield` x229, `Flaps` x202, `BrakeDisc` x192, `Engine` x187.
  **None is a winch, rope, tow or reel, so no vehicle part can pull another vehicle.**
  The nearest is `CargoBayDoor` - 28 parts that open a bay
  door and stop.
- Functional winch classes anywhere in the fleet: **0**.

**WPN-6 verdict: a carrier exists for the geometry (copy `transport_rope_winch` - one
part, parent 0, `Boat_Generic`, no behaviour, 5 LOD meshes), and the mechanic is a proven absence.**
Nothing in the vehicle data pulls, reels, tows or winches; JC3's pulling is Rico's
grapple/tether, which belongs to the character, not the vehicle.
BmAK side, quoted not re-derived (MODLOG §86/§87: `RBatmobileWinch` yields at best a force, never a mass). MODLOG §86 shows that bound is an
elevator bound (>= ~2 t class), so even it would not give a vehicle mass.

## 5. Every tether/grapple/rope/winch name in the index

`tether` matches **335 paths**:

| prefix | paths |
|---|---|
| `animations/jc_characters/dialogue` | 124 |
| `sound/dialogue/eng` | 124 |
| `dlc/bavarium_sea_heist/sound` | 60 |
| `dlc/mech_land_assault/sound` | 20 |
| `textures/ui/upgrades` | 2 |
| `editor/entities/jc_props` | 1 |
| `graphs/dualtether_test_to_vehicle.gdc` | 1 |
| `graphs/dualtether_test_to_vehicle.gsc` | 1 |
| `videos/upgrades/upgrade_multitether_count_1.bikc` | 1 |
| `videos/upgrades/upgrade_multitether_count_2.bikc` | 1 |

The 7 that are not dialogue:

- `editor/entities/jc_props/challenge_props/decals/t_challenge_dual_tether_alpha_dif.hmddsc`
- `graphs/dualtether_test_to_vehicle.gdc`
- `graphs/dualtether_test_to_vehicle.gsc`
- `textures/ui/upgrades/upgrade_multitether_1.ddsc`
- `textures/ui/upgrades/upgrade_multitether_2.ddsc`
- `videos/upgrades/upgrade_multitether_count_1.bikc`
- `videos/upgrades/upgrade_multitether_count_2.bikc`

`winch` matches **0 paths** - the word does not occur in the index at
all. That is supporting, not conclusive: the index does not carry parts-module prop
meshes (`transport_propeller` matches 0 paths, and only
196 `.lod` paths are indexed at all), so the parts table - not the index -
is the authority on prop meshes. Both agree that no winch *mechanic* is named anywhere.

## 6. UNKNOWNs and limits

- **Tether strength / break force**: UNKNOWN. Not in any decoded table (section 1, 5).
  Only a Q-1 probe (one variable: attach the car to a fixed object and observe) can
  measure it.
- **Unit of `RigidBody.mass`**: UNKNOWN - the file gives a bare number.
- **Whether a helicopter can airlift a car**: UNKNOWN. No fleet helicopter has a
  `CVehicleCargoBay`; whether a native tow/winch exists is engine code, not entity data.
- **What carries a vehicle into a bay**: UNKNOWN. The bay is a transform with empty
  events; the attach rule (and how the tank is held by the cargo plane) is native.
- **What `graphs/dualtether_test_to_vehicle` does**: UNKNOWN - a `GraphScript`, outside
  the decoded set; its bytes were not read here.
- **Whether the §86 winch-force bound transfers to JC3**: no - it is a BmAK feasibility
  bound, quoted, not a JC3 number.

## 7. Validation

`python Tools/scripts/jc3tether.py --check` rebuilds `TETHER.json` and `TETHER.md` from the
inputs, compares both byte-for-byte, and asserts:

| assertion | measured | expected |
|---|---|---|
| entities with `RigidBody.mass` | 232 | 232 |
| multi-body entities | 1 | 1 |
| donor mass | 975 | 975 |
| Batmobile target | 6000 | 6000 |
| `CVehicleCargoBay` objects | 12 | 12 |
| entities with a bay | 12 | 12 |
| helicopters with a bay | 0 | 0 |
| compound entities | 1 | 1 |
| `CGrapplingHookPropData` objects | 33 | 33 |
| entities carrying them | 3 | 3 |
| `tether_*` object names | 6 | 6 |
| boat rope/winch part rows | 40 | 40 |
| distinct rope/winch part names | 10 | 10 |
| `*rope_winch*` model files, fleet | 12 | 12 |
| `*rope_winch*` files on one boat | 6 | 6 |
| fleet module types | 53 | 53 |
| tether/cargo module types | 0 | 0 |
| functional winch classes | 0 | 0 |
| `tether` paths in the index | 335 | 335 |
| non-dialogue `tether` paths | 7 | 7 |
| `winch` paths in the index | 0 | 0 |
