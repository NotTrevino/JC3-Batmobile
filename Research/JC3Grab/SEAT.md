# Driver seat and pose (G2-19)

**Answer: the car does not own the pose.** A JC3 vehicle places the driver with one
interaction-graph object and says nothing else about him; the *pose* is the character state
machine's vehicle state, and its animation set carries one clip family per **vehicle class**.

| question | answer | evidence |
|---|---|---|
| what places Rico | `entry.driver` (`CInteractionGraphEntry`, state `S_ENTER_DRIVER_VEHICLE`) plus its siblings - **34** driver-named objects (entry 10, exit 14, interaction 1, point 3, transition 4, trigger 2) | `INTERACTION.json` (G2-18), donor `.epe` |
| what chooses his pose | `rico_base.afsmb` (state machine) over `rico_base.asb` (animation set), by vehicle class | 327,108 B + 2,614,188 B, 1619 / 6538 strings |
| how many pose families | **40** vehicle classes, 382 clip names | `.asb` string table |
| how high each sits | `Land_Seat` part hull centres v0300 0.855 m, v0300 0.855 m, v0003 0.894 m (3 of 5 candidate parts are a `Land_Seat`) | `.physicsc` hulls |
| what the card's In list promises | `jc_statemachine/vehicles/*` **0 files**, `jc_skeletons/vehicles/*.bsk` **0 files** - both absent; 142 state-machine files are character-side, 3 skeleton files in total, 7 vehicle `.ban` clips | `INDEX.jsonl` |
| candidate for the Batmobile | **v0300_car_kensington_sportsmuscle / `sportsmuscle_f_l_seat`** at 0.855 m vs the `Driver` hip 0.865 m (10 mm) | `SOCKETS_JC3.json` + seat boxes |

## 1. Where Rico is placed - the vehicle side

A JC3 vehicle entity has **no seat, occupant, pose or animation module**. The donor's
container holds 31 `.vmodc` modules and the fleet's module vocabulary is 52 types; none is
about a character. What it does have is the interaction graph:

| object | class | state | verts (Serpente frame) | verdict |
|---|---|---|---|---|
| `entry.driver` | `Entry` | `S_ENTER_DRIVER_VEHICLE` | 0.000, 0.000, 0.000 | n/a (container origin) |
| `point.driver` | `PointNode` | `-` | -0.440, 0.340, 0.200 | inside |
| `exit.driver.default` | `Exit` | `S_EXIT_VEHICLE` | -0.440, 0.340, 0.200 | inside |
| `exit.ai.driver.default` | `Exit` | `S_EXIT_VEHICLE` | -0.440, 0.340, 0.200 | inside |
| `exit.ai.driver.to.hood` | `Exit` | `S_EXIT_DRIVER_TO_HOOD_VEHICLE` | -0.440, 0.340, 0.200 | inside |
| `exit.driver.roll.out` | `Exit` | `S_ROLL_OUT_EXIT_VEHICLE` | -0.440, 0.340, 0.200 | inside |
| `exit.driver.moving.parachute` | `Exit` | `S_EXIT_VEHICLE_PARA` | -0.440, 0.340, 0.200 | inside |
| `exit.ai.driver.default90R` | `Exit` | `S_EXIT_VEHICLE_90R` | -0.440, 0.340, 0.200 | inside |
| `exit.driver.pushed.out` | `Exit` | `S_PUSHED_OUT_VEHICLE` | -0.440, 0.340, 0.200 | inside |
| `exit.ai.driver.default90L` | `Exit` | `S_EXIT_VEHICLE_90L` | -0.440, 0.340, 0.200 | inside |
| `exit.driver.to.fall` | `Exit` | `S_EXIT_VEHICLE_TO_FALL` | -0.440, 0.340, 0.200 | inside |
| `exit.ai.driver.default180` | `Exit` | `S_EXIT_VEHICLE_180` | -0.440, 0.340, 0.200 | inside |
| `exit.driver.to.swim` | `Exit` | `S_EXIT_DRIVER_VEHICLE_IN_WATER` | -0.440, 0.340, 0.200 | inside |
| `exit.ai.driver.default0` | `Exit` | `S_EXIT_VEHICLE_0` | -0.440, 0.340, 0.200 | inside |
| `exit.driver.pulled.out` | `Exit` | `S_PULLED_OUT_VEHICLE` | -0.440, 0.340, 0.200 | inside |
| `exit.driver.upside.down` | `Exit` | `S_EXIT_DRIVER_VEHICLE_UPSIDE_DOWN` | -0.440, 0.340, 0.200 | inside |
| `entry.driver.pull.out.onground.no.door` | `Entry` | `S_ENTER_ON_GROUND_THROW_OUT_NO_DOOR_VEHICLE` | 0.000, 0.000, 0.000 | n/a (container origin) |
| `entry.stunt.to.driver.side.enter.vehicle2` | `Entry` | `S_ENTER_STUNT_TO_DRIVER_SIDE_VEHICLE` | 0.000, 0.000, 0.000 | n/a (container origin) |
| `entry.stunt.to.driver.side.enter.vehicle3` | `Entry` | `S_ENTER_STUNT_TO_DRIVER_SIDE_VEHICLE` | 0.000, 0.000, 0.000 | n/a (container origin) |
| `entry.driver.locked.onground` | `Entry` | `S_ENTER_ON_GROUND_UNLOCK_VEHICLE` | 0.000, 0.000, 0.000 | n/a (container origin) |
| `point.driver.onground` | `PointNode` | `-` | -1.330, 0.000, 0.770 | floating |
| `entry.driver.pull.out.onground` | `Entry` | `S_ENTER_ON_GROUND_THROW_OUT_VEHICLE` | 0.000, 0.000, 0.000 | n/a (container origin) |
| `entry.stunt.to.driver.side.enter.vehicle` | `Entry` | `S_ENTER_STUNT_TO_TRANS_ENTER_VEHICLE_P1` | 0.000, 0.000, 0.000 | n/a (container origin) |
| `entry.ai.driver.left` | `Entry` | `S_ENTER_DRIVER_VEHICLE` | 0.000, 0.000, 0.000 | n/a (container origin) |
| `entry.driver.side.fast` | `Entry` | `S_ON_GROUND_TO_ENTER_DRIVER_SIDE_VEHICLE` | 0.000, 0.000, 0.000 | n/a (container origin) |
| `point.driver.side` | `PointNode` | `-` | -0.260, 1.470, 0.370 | floating |
| `entry.driver.no.door` | `Entry` | `S_ENTER_DRIVER_NO_DOOR_VEHICLE` | 0.000, 0.000, 0.000 | n/a (container origin) |

Those objects are the *attach* half only: a state string plus a transform. The state is
consumed by the character, which is why the pose is not here.

## 2. Where his pose is chosen - the character side

`rico_base.afsmb` (327,108 B) is Rico's state machine. The names that
matter, straight out of its string table:

| kind | count | examples |
|---|---|---|
| entry actions | 4 | `ACT_ENTER_VEHICLE`, `ACT_ENTER_VEHICLE_CARGO_BAY`, `ACT_ENTER_VEHICLE_MOUNTED_WEAPON`, `ACT_ENTER_VEHICLE_STUNT_JUMP` |
| exit actions | 1 | `PACT_EXIT_VEHICLE` |
| vehicle states | 183 | `S_BAY_DRIVER_DOOR_TO_BAY_P1_VEHICLE`, `S_BAY_DRIVER_DOOR_TO_BAY_P2_VEHICLE`, `S_BAY_DRIVER_DOOR_TO_DRIVER_VEHICLE` |
| driver-seat conditions | 9 | `PPC_ARRIVED_AT_DRIVER_SEAT`, `PPC_IS_CURRENT_VEHICLES_DRIVER_SEAT_OCCUPIED`, `PPC_IS_CURRENT_VEHICLES_SHOTGUN_SEAT_OCCUPIED`, `PPC_IS_ENTRY_NODE_DRIVER_SEAT_OCCUPIED` |
| driving IK targets | 4 | `PPikt.driving.left.foot`, `PPikt.driving.left.hand`, `PPikt.driving.right.foot`, `PPikt.driving.right.hand` |
| class selectors (`MOD_*`) | 36 | `ATV`, `BACK`, `BIKE`, `BOAT`, `BOAT_CABIN`, `BOAT_FORWARD` |

So the mode is named in the state name itself: `ANIM_…_VEHICLE_MOD_<CLASS>`. The pose
families come from `rico_base.asb`'s clip paths, which group by class directory:

| class | clips | sample |
|---|---|---|
| `bike` | 12 | `rico_vehi_atv_reel_geton_dir0.ban` |
| `bike/add/head` | 1 | `rico_vehi_standardbike_idle_exist_add_head.ban` |
| `bike/add/larm` | 1 | `rico_vehi_standardbike_idle_exist_add_larm.ban` |
| `bike/add/rarm` | 2 | `rico_vehi_standardbike_slow_noaim_mid_add_rarm.ban` |
| `bike/add/torso` | 1 | `rico_vehi_standardbike_idle_exist_add_torso.ban` |
| `bike/arms` | 14 | `rico_vehi_atv_getoff_lft_noncombat_arms.ban` |
| `bike/fast/larm` | 4 | `rico_vehi_standardbike_fast_unarmed_left_to_mid_add_larm.ban` |
| `bike/fast/lower` | 8 | `rico_vehi_atv_fast_to_slow_lower.ban` |
| `bike/fast/noarms` | 4 | `rico_vehi_standardbike_fast_unarmed_left_to_mid_add_noarms.ban` |
| `bike/fast/rarm` | 4 | `rico_vehi_standardbike_fast_unarmed_left_to_mid_add_rarm.ban` |
| `bike/fast/upper` | 8 | `rico_vehi_atv_fast_to_slow_upper.ban` |
| `bike/hands` | 14 | `rico_vehi_atv_getoff_lft_noncombat_hands.ban` |
| `bike/hijack` | 3 | `rico_vehi_atv_reel_hijack_kick.ban` |
| `bike/noarms` | 3 | `rico_vehi_atv_getoff_lft_noncombat_noarms.ban` |
| `bike/reverse/lower` | 4 | `rico_vehi_atv_reverse_unarmed_lft_lower.ban` |
| `bike/reverse/upper` | 4 | `rico_vehi_atv_reverse_unarmed_lft_upper.ban` |
| `bike/slow/larm` | 6 | `rico_vehi_standardbike_slow_lean_bwd_to_fwd_add_larm.ban` |
| `bike/slow/lower` | 20 | `rico_vehi_atv_slow_aim_mid_lower.ban` |
| `bike/slow/noarms` | 6 | `rico_vehi_standardbike_slow_lean_bwd_to_fwd_add_noarms.ban` |
| `bike/slow/rarm` | 6 | `rico_vehi_standardbike_slow_lean_bwd_to_fwd_add_rarm.ban` |
| `bike/slow/upper` | 19 | `rico_vehi_atv_slow_aim_mid_upper.ban` |
| `bike/stand/lower` | 8 | `rico_vehi_atv_stand_to_slow_lower.ban` |
| `bike/stand/upper` | 8 | `rico_vehi_atv_stand_to_slow_upper.ban` |
| `bike/stationary/arms` | 4 | `rico_vehi_standardbike_exit_lft_noncombat_arms.ban` |
| `bike/stationary/hands` | 4 | `rico_vehi_standardbike_exit_lft_noncombat_hands.ban` |
| `bike/stationary/lower` | 20 | `rico_vehi_atv_aim_mid_to_idle_aim_lower.ban` |
| `bike/stationary/noarms` | 1 | `rico_vehi_standardbike_exit_lft_noncombat_noarms.ban` |
| `bike/stationary/upper` | 12 | `rico_vehi_atv_idle_aim_to_idle_left_upper.ban` |
| `boat` | 33 | `rico_vehi_boat_cabin_drive_left_to_right.ban` |
| `bus` | 8 | `rico_vehi_bus_driver_to_rollout.ban` |
| `car` | 2 | `rico_vehi_car_driver_to_rollout.ban` |
| `car/circuit` | 9 | `rico_vehi_car_circuit_drive_left_to_right.ban` |
| `car/high` | 4 | `rico_vehi_car_high_driver_to_std.ban` |
| `car/low` | 23 | `rico_vehi_car_low_drive_left_to_right.ban` |
| `car/med` | 35 | `rico_vehi_car_med_drive_left_to_right.ban` |
| `helicopter` | 28 | `rico_vehi_heli_assault_driver_to_hang.ban` |
| `plane` | 17 | `rico_vehi_plane_cargo_driver_to_fall.ban` |
| `stunt` | 2 | `rico_vehi_stnt_jump_land.ban` |
| `tank` | 10 | `rico_vehi_tank_apc_driver_to_fall_left.ban` |
| `tractor` | 10 | `rico_vehi_tractor_drive_left_to_right.ban` |

**382 clip paths** across **40** classes. They are
*names inside the `.asb`*, not archive entries: the index lists only 2 of Rico's vehicle `.ban` files
(both `…/rico/vehicle/mech/rico_vehi_mech_driver_to_{std,rollout}.ban`, a mech suit, not a
car) out of 7 `.ban` files under any `…/vehicle/` path, so an animation-set bundle is the
only place a seated car clip is addressable from.

## 3. Seat heights - what each class actually sits on

The seat is a *part*, and a part's collision is a convex hull in the `.physicsc`, so the
seat box is measurable per vehicle. The reference is the Batmobile: `Driver` socket hip
**0.865 m** (`SOCKETS_JC3.json`), and the donor's own seat-box centre is
0.855 m
- within a centimetre, which is what makes a box centre a usable seat height.

| vehicle | part | part class | hulls | box x × y × z (m) | centre y | Δ vs hip |
|---|---|---|---|---|---|---|
| `v0300` | `sportsmuscle_f_l_seat` | `Land_Seat` | 2 | 0.560 × 0.984 × 0.804 | 0.855 | -10 mm |
| `v0300` | `sportsmuscle_f_r_seat` | `Land_Seat` | 2 | 0.559 × 0.984 × 0.804 | 0.855 | -10 mm |
| `v0401_car_mugello_racingsupercar` | no seat hull | - | 0 | - | - | - |
| `v0003` | `racinghothatch_seats` | `Land_Seat` | 2 | 1.554 × 0.898 × 1.783 | 0.894 | +29 mm |
| `v0201` | `mediumtank_hatch` | `Land_Door` | 2 | 0.716 × 0.202 × 0.788 | 2.879 | +2014 mm |

A hull is a part's whole envelope (cushion to headrest for a seat), so its **centre** is
the comparison quantity, not its top. What the table shows, read strictly:

* The 3 **`Land_Seat`** parts sit at 0.855, 0.855, 0.894 m -
  a span of 39 mm, i.e. JC3's car seats ship at one height whatever the class.
* `v0401`'s `racingsupercar_seats` is a real `Land_Seat` part but **no compound
  instance carries its index**, so that car has no seat hull and no measurable height.
* `v0201`'s only candidate is `mediumtank_hatch`, class **`Land_Door`** - a hatch, not a
  seat. Its 2.879 m is a door roof; the tank's seat height is **UNKNOWN**, not that number.

## 4. The candidate pose

Closest seat to the Batmobile's `Driver` hip: **v0300_car_kensington_sportsmuscle / `sportsmuscle_f_l_seat`**,
seat centre **0.855 m**, i.e. **10 mm** from the hip. That
vehicle is a car, so the alternatives the code can pick from are the car families
`car, car/circuit, car/high, car/low, car/med`
(2, 9, 4, 23, 35 clips). The three sub-classes
(`low` 23, `med` 35, `circuit` 9) are alternatives, not a set: only one plays. The bare
`car` family, whose clips are the transfer ones, is shown for completeness:
`animations/jc_characters/main_characters/rico/vehicle/car/rico_vehi_car_driver_to_rollout.ban`
`animations/jc_characters/main_characters/rico/vehicle/car/rico_vehi_car_std_to_turret.ban`

**This is a candidate, not a decision.** The mapping vehicle → class is chosen by native
code: no file in the index maps `v0300` (or any entity) to `car/low`, `car/med` or
`car/circuit`, and none of the three class folders is named inside the vehicle's own
modules. The seat height narrows it; only an in-game look (phase Q) can confirm which
clip plays, and whether the Batmobile's higher hip needs the `car/med` set at all.

## 5. What this means for ANI-9 / APP-3

* **The attach half is translatable.** `entry.driver` is a transform plus a state string, so
  the Batmobile's `Driver` socket (G1-13) can carry it; the state name is the contract.
* **The pose half is not a vehicle member.** Nothing the mod can edit on the car chooses the
  seated clip; it follows from the character state machine plus a class the game derives.
  T-13 can place the entry point, but "Rico sits believably" stays a phase-Q observation
  unless the class can be forced (a Q-1 probe: watch whether the hands land on the
  Batmobile's yoke or far below it).
* **Seat height is a build input** for the cockpit (G1-19 gave the hip; this card gives the
  fleet's range and the nearest shipped seat).

## 6. Files and commands

```
python Tools/scripts/jc3seat.py --write    # this report + SEAT.json
python Tools/scripts/jc3seat.py --check    # re-derive and compare
```

Inputs: `Research/JC3Grab/INTERACTION.json` (G2-18), `PARTS_TABLE.jsonl` (G2-7), each
vehicle's `.physicsc` (`jc3hkx`), `rico_base.afsmb` / `rico_base.asb` (read from the archives,
`D:\Games` read-only), `Research/BatmobileGrab/SOCKETS_JC3.json` + `COCKPIT.md` (G1-13/G1-19).

## 7. UNKNOWNs

1. **The vehicle → pose-class mapping.** Named classes exist (`MOD_TANK`, `MOD_BOAT_SPY`,
   `MOD_SPORTBIKE`, `MOD_HELI`, car `low`/`med`/`circuit`); which class any given entity gets
   is native. UNKNOWN, not guessed from the vehicle's name.
2. **The clip bodies.** The seated `.ban` clips are not separate entries, and the `.asb`
   container format is not decoded here - only its string table is read. Clip lengths,
   tracks and bone lists are UNKNOWN.
3. **The tank's seat height.** `v0201` has no seat part at all - its only driver-ish part is
   `mediumtank_hatch` (part 39, class `Land_Door`). The 2.879 m in the table is a door, so
   the tank's seat height and the `tank` clip family's seated height are UNKNOWN.
4. **The supercar's seat hull.** `v0401` has a `Land_Seat` part (`racingsupercar_seats`,
   index 19) but no compound instance carries index 19 or 22 - either that part has no
   collision at all or it is carried by a shape class `jc3hkx` does not enumerate. UNKNOWN
   which, and it does not affect the candidate (the candidate is the muscle car).
4. **Whether the Batmobile's hip (0.865 m) is inside the shipped range.** The roster spans
   several classes, but a class is chosen by code, so "inside the range" is not the same as
   "will play that class".
