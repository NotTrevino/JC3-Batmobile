# The car that drives itself to the player — closest JC3 carrier, members, and the build recipe

**STATUS: done (plan, read-only probe).** JC3 ships a **self-driving car**: every land vehicle carries an
**AI tune set** (`modules/default/ai/*_ai.vmodc`) whose members set the AI's **speed limit curve**,
**brake torque / lock time / handbrake factor** and **steer rate**, and a **traffic rule** gives that car a
**Driver seat bound to an AI behaviour tree** (`ai/bts/civilian/civilian_std.bts`). The mission side has a
**`graphs/random_encounters/vehicle_delivery`** graph and a **Rebel Drop** entry that spawns the car. What is
**not** decoded is the one member that says "drive to *this* coordinate": the car's AI modules are **input
curves**, not goals, and the goal lives in the behaviour tree (`.bts` — **0 entries in the index**, so its
members cannot be read). §6 gives the recipe that reproduces BmAK's arrival with the members we *do* have,
and §7 names the one probe that settles the goal member.

This report replaces §8.4 item 5 of `tmp/freebuff/reports/summon-and-arrival-plan.md` ("drive-in remains
blocked"). The blocked framing was wrong: the carrier exists, only its destination parameter is unread.

---

## 1. BmAK's arrival, the numbers we must reproduce

| element | BmAK value | source |
|---|---|---|
| travel mode | navmesh **self-drive** (`ESelfDriveMode`, `SelfDriveMode`, `SetSelfDriveMode`) on `RVehicle` | `CONTROLS.md:135-142`; `COLLISION_SELECTOR.md:79` |
| speed ceiling | `SVehicle.MaxSpeed` = **4000.0 cm/s = 40.0 m/s = 144 km/h** | `CLASS_DEFAULTS.md:163` |
| boost allowed | `SelfDriveAllowBoost = True` | `CLASS_DEFAULTS.md:179` |
| can drop ledges / U-turn | `SelfDriveCanJumpDown = True`; `SelfDriveUturn` bit `0x800000` | `CLASS_DEFAULTS.md:152`; `CONTROLS_NATIVE2.md:34` |
| stop style | **skid stop** — `bSkidToStop`, native `SkidToStop` writes `SkidToStopDir` (0x3B1), `DestReachedSkidToStop` | `NATIVE.md:119,134`; `PACKAGES_G305.md:565` |
| stop radius / call delay | **UNKNOWN** — the 25 `RBatmobileRemoteBm` behaviour bodies ship with no bytecode | `GADGET_PARAMS.md` §"25 behaviour members" |
| after arrival | `GetInRemoteMoveFront` / `_Back`, `JumpInBatmobileSkidStopMove` | `CLASS_DEFAULTS.md:89,90,91` |

So the arrival we must reproduce is: **40 m/s on the road, decelerate hard, stop beside the player with the
rear locked, engine running.** The only numbers BmAK gives are the ceiling (40 m/s) and the stop *style*.

---

## 2. Closest carrier A — the car's own AI tune set (the self-drive itself)

Each land vehicle ships **five** AI modules beside the player-driven ones. For the donor `v0300` they are
`DECODE_DEPTH.md:539-543` (all graded **FULL**), and their member rows are in the entity grab
(`E:/Modding/_gamedata/JC3grab/entities/v0300_car_kensington_sportsmuscle__v0300_car_kensington_sportsmuscle_civilian_01.ee.json`):

| AI module | instance | rows | what it is |
|---|---|---:|---|
| `v0300_car_kensington_sportsmuscle_ai.vmodc` | `v0300_car_kensington_sportsmusc…` | 61 | the **AI input curves**: `Input_Speed`, `Input_Turn`, `Limit_Speed` |
| `v0300_car_kensington_sportsmuscle_land_global_ai.vmodc` | `LandGlobal` | 36 | wheel/friction set for AI driving |
| `v0300_car_kensington_sportsmuscle_brakes_ai.vmodc` | `brakes` | 7 | **AI brake torque, lock time, handbrake factor** |
| `v0300_car_kensington_sportsmuscle_land_steering_ai.vmodc` | `car_lamborghini_land_steering.v…` | 15 | **AI steer rate and angle limits** |
| `v0300_car_kensington_sportsmuscle_land_aerodynamics_ai.vmodc` | `LandAerodynamics` | 5 | AI drag / lift (the AI's speed governor, physically) |

### 2.1 The speed member — `Limit_Speed` (this is the AI's speed ceiling)

`v0300_..._ai.vmodc`, decoded values:

| member | value | meaning |
|---|---:|---|
| `Limit_Speed.x_min` | **0.1** | curve input range |
| `Limit_Speed.x_max` | **1.0** | |
| `Limit_Speed.y_min` | **5** | curve output range |
| `Limit_Speed.y_max` | **35** | **the ceiling the AI may drive at** |
| `Limit_Speed.number_of_control_points` | 4 | |
| `Limit_Speed.control_points[0]` | x 0, y **1.0**, y2 0 | x is clamped to 0.1, so the top of the curve is the ceiling |
| `Limit_Speed.control_points[1]` | x 0.2114, y **0.9167**, y2 -7.7047 | |
| `Limit_Speed.control_points[2]` | x 0.6443, y **0.2361**, y2 6.6097 | |
| `Limit_Speed.control_points[3]` | x 1.0, y **0.0972**, y2 0 | the low end of the curve |

That curve read against its own `y_min 5 / y_max 35` gives the usable band **≈7.9 … 35** (y = 0.0972 → 5 +
0.0972×30 = 7.9; y = 1.0 → 35). `Input_Speed` is the second, finer one (`x 1..15`, `y 0..1`, 3 points), and it
maps a desired speed onto throttle.

**Proof that this curve is the per-car AI speed ceiling, not a coincidence:** the same member on other cars
(decoded from each entity's grab JSON):

| entity | `Limit_Speed.y_min` | `Limit_Speed.y_max` | its own top speed |
|---|---:|---:|---|
| `v0300` sports muscle (the donor) | 5 | **35** | `official_top_speed` 250, `transmission.top_speed` 320 |
| `v0201` medium tank | 5 | **40** | — |
| `v0401` racing supercar | 5 | **35** | — |
| `v0604` Urga buggy | 8 | **35** | — |
| `v0803` monster truck | 5 | **30** | — |
| `v0507` old bus | 2 | **22** | — |

The ordering (bus 22 < monster truck 30 < car/supercar/buggy 35 < tank 40) is a traffic-safety ordering, and
every value sits far below the car's own 250 km/h `official_top_speed`. **Unit is UNKNOWN** — no file states
it; if it is m/s, 35 = 126 km/h, which is the shape a civilian traffic AI would use. Any unit claim beyond
"below `official_top_speed`" is an inference and is labelled as one.

### 2.2 The stopping members — `brakes_ai`

| member | player `…_brakes.vmodc` | **AI `…_brakes_ai.vmodc`** | effect |
|---|---:|---:|---|
| `front.max_brake_torque` | 10000 | **14000** | 1.4× brake torque |
| `rear.max_brake_torque` | 10000 | **14000** | |
| `front.min_time_to_block` | 5 | **1** | locks 5× sooner |
| `rear.min_time_to_block` | 5 | **1** | |
| `rear.handbrake` | 1 | 1 | rear is the handbrake axle |
| `front.handbrake` | 0 | 0 | |
| `handbrake_friction_factor` | 1 | **2** | twice the skid friction |

This is the closest thing JC3 has to BmAK's `bSkidToStop`: an AI brake set with **rear handbrake at 2×
friction and a 1 s lock time**. A metric stopping distance is not derivable from these seven members alone
(they are torques; distance needs mass and wheel radius — `front_wheels.radius` is 0.38 m, mass lives in
`rigid_body`, not read in this pass), so §6 treats the stop as **authored by the curve**, not computed.

### 2.3 The steering member — `land_steering_ai` (how fast the AI may turn in)

| member | player | **AI** |
|---|---:|---:|
| `t_to_full_steer_s` | 1.2 | **2.0** |
| `max_speed_t_to_full_steer_s` | 0.85 | **-1** (no speed ramp) |
| `min_speed_kmph` / `max_speed_kmph` | 30 / 220 | **10 / 100** |
| `steer_angle_min_speed_deg` | 35 | **45** |
| `steer_angle_max_speed_deg` | 15 | **10** |
| `saturation_zone` | 1.0 | **0.95** |
| `steer_input_power_pc/durango/orbis` | 3 | **1** |
| `wheel_drift_aligning_strength` | 0.30 | **0.50** |

The AI steers **slower to full lock (2 s) but to a larger low-speed angle (45°)**, with a **100 km/h** steer
speed window instead of the player's 220 km/h — i.e. the AI is tuned for road following, not for a
handbrake turn.

### 2.4 The AI wheel and aero set (why the AI car is not the player car)

| member | player module | AI module |
|---|---:|---:|
| `wheels_friction_type` (`land_global`) | 0 | **1** |
| `front_wheels.mass` (`land_global`) | 25 | **75** |
| `drag_coefficient` (`land_aerodynamics`) | 0.33 | **0.80** |
| `frontal_area` | 2.4 | **2.5** |
| `lift_coefficient` | -1.95 | **-0.30** |

Rear wheel mass is 75 on both. Front wheel mass tripled and drag 2.4× are what keep an AI car planted at its
`Limit_Speed` instead of behaving like the player's car.

**Carrier A verdict:** this is the JC3 system that **sets a car's destination-approach speed and its stopping
behaviour** for a car with no human in it. Ported to the Batmobile it gives the drive-in its 40 m/s leg and its
skid stop. It does **not** carry the goal (§4, §5).

---

## 3. Closest carrier B — the traffic rule that puts a driver in the car

`global/global.blo` (patch, 79,340 B) carries **31 traffic-rule names, 41 tag selectors, Driver seats and 10
AI behaviour-tree paths** (`TRAFFIC.md` §3). The behaviour-tree list, read out of the file this pass
(printable strings ≥8 chars containing `ai/`), is:

```
ai/bts/civilian/civilian_std.bts
ai/bts/vehicle/boat/civilian_roam_in_boat.bts
ai/bts/vehicle/boat/military_boat_driver_2.bts
ai/bts/vehicle/airplane/airplane_roam.bts
ai/bts/enemies/01_shared/soldier_tank_driver.bts
ai/bts/enemies/01_shared/boat_gunner.bts
ai/bts/enemies/gen_soldier/gen_soldier.bts
ai/bts/enemies/machinegunner/machinegunner.bts
ai/bts/enemies/demolition/demolition_rpg.bts
ai/bts/enemies/shock_trooper/shock_trooper.bts
```

The donor's tags (`vehicle, ground, car, civilian, racing, modern, muscle, kensington, sports, unarmed,
unarmored, ambient, liberated`) satisfy exactly one selector, `ambient,ground,car,liberated,-highend`, whose
rule is **`03_CivilianCarLiberatedProvince`** (`TRAFFIC.md` §3). That rule is what pairs the car with
`ai/bts/civilian/civilian_std.bts` and a `Driver` seat.

**Carrier B verdict:** `civilian_std.bts` is the **goal-seeking carrier** — a roaming driver that takes the car
around the road network. It is the only decoded entity in JC3 that makes a *car* drive to places on its own.
Its members are **UNKNOWN**: the index has **0 `.bts` entries** (`grep -c '\.bts"' Research/JC3Grab/INDEX.jsonl`
= 0), so the tree's nodes and their destination parameter cannot be read here.

---

## 4. Closest carrier C — the mission graph that delivers a vehicle

The archive index names a random-encounter graph family whose job is exactly "a vehicle is delivered":

| graph | size | nodes | class hashes | data-name hashes |
|---|---:|---:|---:|---:|
| `graphs/random_encounters/vehicle_delivery.gsc` | 35,799 B | 56 | 24 | 96 |
| `graphs/random_encounters/vehicle_delivery_timer.gsc` | 6,599 B | 13 | 10 | 33 |
| `graphs/random_encounters/convoy_rescue.gsc` | 47,271 B | 86 | 27 | 136 |
| `graphs/random_encounters/rebel_vehicle_breakout.gsc` | 16,535 B | 37 | 21 | 63 |
| `graphs/mission/modules/msub_vehicle_controller.gsc` | 67,143 B | 137 | 23 | 158 |
| `graphs/spawners/vehiclerule_save_self_to_spawn_slot.gsc` | 4,055 B | 7 | 7 | 15 |

All seven are **ADF v4** (`magic b' FDA'`), not Lua text: node and parameter names are **32-bit Jenkins
hashes** with no string table (`Tools/scripts/jc3adf.py dump` prints `Nodes[i].Class uint32 1870858653` and
`Nodes[i].DataSet.Data[j].Name uint32 …`). To name anything, each hash was matched against 35,681 candidate
tokens taken from `Research/JC3Grab/*.md`, `Research/specs/*.md`, `tmp/freebuff/reports/*.md` and
`Working/**/*.md`, hashed with `rbmhdr.hash_jenkins`. Recovered names only:

| graph | recovered `Class` names | recovered `Data` names |
|---|---|---|
| `vehicle_delivery` | `Block` ×4, `Main` ×1, `Health` ×2 | `Name`, `Value`, `size`, `time`, `started`, `Time`, `paused`, `loop`, `Operator`, `health`, `Seat`, `operator` |
| `vehicle_delivery_timer` | — | `Name`, `Value`, `Time`, `paused`, `loop`, `instructions`, `scope` |
| `convoy_rescue` | `Block` ×4, `Main` ×1, `Heat` ×2 | `Name`, `Value`, `Operator`, `size`, `time`, `started`, `Time`, `paused`, `loop`, `Seat`, `Level`, `hint`, `silent`, `threshold` |
| `rebel_vehicle_breakout` | `Block`, `Main` | `Name`, `Value`, `threshold`, `Time`, `paused`, `loop` |
| `msub_vehicle_controller` | **`EnterVehicle` ×11**, `Block` ×3 | `Name`, `Value`, `Operator`, **`Graph` ×17**, **`Seat` ×11**, `Door` |
| `vehiclerule_save_self_to_spawn_slot` | `Exit` | `Name`, `Value` |

Read honestly: `msub_vehicle_controller` is a **vehicle sub-graph runner** (11 `EnterVehicle` nodes, 17 `Graph`
parameters, 11 `Seat` parameters, 1 `Door`) — it is the mission-side "put someone in a vehicle and run a
sub-graph" carrier. `vehicle_delivery` is a **56-node encounter with `Seat` and `operator` data and a 6-value
time table in its timer twin** — the delivery/arrival event exists as a graph, but **no destination, speed or
distance parameter surfaced by name** in it.

**Carrier C verdict:** the closest *mission* carrier for "the car arrives for the player" — it is a named,
shipped, spawn+seat+time graph. Its drive parameters are hash-hidden; §7 names the probe that opens them.

---

## 5. Closest carrier D — the spawn anchor: Rebel Drop and `CVehicleRule`

| system | what it sets | what it does not have |
|---|---|---|
| **Rebel Drop** (`profile/item.onlinec`, 26-member `Item`, 128 B) | `Name` = 32-bit Jenkins hash of the entity **leaf** — the whole spawn binding; `RebelDropTimer` = the only time field (vanilla 60–2700; the build uses **1800**); `UIImagePath` = leaf name | **no position, no offset, no destination field** — the car appears at the **drop marker's transform** (`REBELDROP.md` §2; `bm_rebel.py` header) |
| **`CVehicleRule`** (59 objects in 8 entities, level `.blo`) | `chance`, `heat_level`, `spawn_event`, `health`, `invulnerable` — **all 0** | any route, goal or speed (`DAMAGE_MECHANISMS.md:46-47`) |

`REBELDROP.md:359` states the delivery side plainly: *"(menu, pricing, delivery animation) is code"*. So the
landing is not a data path we can retune; the marker transform is the only anchor the tables give.

**Carrier D verdict:** this is the **teleport-and-stop** leg — spawn the car at a marker transform with zero
velocity. It reproduces BmAK's arrival *state* (car beside the player, standing, engine on) in one frame, not
the travel.

---

## 6. The build recipe — BmAK's arrival path and timing, in JC3 terms

BmAK's call delay and stop radius are UNKNOWN (§1), so the timing below is **derived from the one decoded
ceiling**, with the arithmetic printed. It is the only defensible bridge and is labelled as a derivation.

### 6.1 The path, in four legs

| leg | JC3 carrier | what we write |
|---|---|---|
| 1. the call spawns the car | **Rebel Drop entry, already built (B-13)**: `Name`/`UIName` = 443190071, `UIDescription` = 1805638565, `UIDisplayOrder` 12, `UIImagePath` = `v0300_car_kensington_sportsmuscle_batmobile`, `RebelDropTimer` 1800 | keep as built; it is the only menu path that spawns a chosen `.ee` |
| 2. the car appears | drop-marker transform (Carrier D) — spawn at the marker, velocity 0 | place the marker on the road **80 m** from the player (default; any distance in §6.3) |
| 3. the car drives | **Carrier A + B**: the five `_ai.vmodc` modules are already inside the donor `.ee` (`DECODE_DEPTH.md:539-543`); add a `Driver` seat bound to `ai/bts/civilian/civilian_std.bts` the way `03_CivilianCarLiberatedProvince` does | `Limit_Speed.y_max` = **40** (BmAK 4000 cm/s); `Limit_Speed.x_min` 0.1, `x_max` 1.0 kept; `Input_Speed` kept (x 1..15) |
| 4. the car stops | **skid stop**: `brakes_ai` rear handbrake, 2× friction, 1 s lock | `rear.handbrake` 1, `handbrake_friction_factor` **2**, `rear.max_brake_torque` **14000**, `rear.min_time_to_block` **1**; taper the approach with `Limit_Speed.control_points[3].y` = **0.0972** (≈7.9 units) so the last metres are slow |

### 6.2 The exact member values to set

| file (in the built entity's `modules/default/ai/`) | member | donor value | **set to** | why |
|---|---|---:|---:|---|
| `…_ai.vmodc` | `Limit_Speed.y_max` | 35 | **40** | BmAK `SVehicle.MaxSpeed` = 4000 cm/s = 40 m/s |
| `…_ai.vmodc` | `Limit_Speed.x_min` / `x_max` | 0.1 / 1.0 | 0.1 / 1.0 | keep the curve domain |
| `…_ai.vmodc` | `Limit_Speed.control_points[0].y` | 1.0 | **1.0** | full ceiling at the clamp |
| `…_ai.vmodc` | `Limit_Speed.control_points[2].y` | 0.2361 | **0.30** | eases the mid-approach |
| `…_ai.vmodc` | `Limit_Speed.control_points[3].y` | 0.0972 | **0.0972** | the slow tail ≈7.9 units |
| `…_ai.vmodc` | `Input_Speed.x_max` | 15 | **15** | keep (input→throttle gain) |
| `…_ai.vmodc` | `Limit_IsLargeVehicle` | 0 | **0** | Batmobile is car-sized |
| `…_brakes_ai.vmodc` | `rear.max_brake_torque` | 14000 | **14000** | skid stop |
| `…_brakes_ai.vmodc` | `front.max_brake_torque` | 14000 | **14000** | |
| `…_brakes_ai.vmodc` | `rear.min_time_to_block` / `front.…` | 1 / 1 | **1 / 1** | 5× sooner than the player set |
| `…_brakes_ai.vmodc` | `handbrake_friction_factor` | 2 | **2** | 2× skid friction |
| `…_brakes_ai.vmodc` | `rear.handbrake` | 1 | **1** | rear axle locks |
| `…_land_steering_ai.vmodc` | `t_to_full_steer_s` | 2.0 | **2.0** | road following, not handbrake turns |
| `…_land_steering_ai.vmodc` | `steer_angle_min_speed_deg` | 45 | **45** | |
| `…_land_steering_ai.vmodc` | `max_speed_kmph` | 100 | **100** | steer window |
| `…_land_aerodynamics_ai.vmodc` | `drag_coefficient` | 0.80 | **0.80** | keeps it planted at 40 m/s |
| `…_land_global_ai.vmodc` | `wheels_friction_type` | 1 | **1** | AI friction index |
| `…_land_global_ai.vmodc` | `front_wheels.mass` | 75 | **75** | AI front axle mass |

The car's own caps stay above the AI limit: `vehicle_misc.official_top_speed` **250** and
`transmission.top_speed` **320** (km/h-shaped), with 6 `gears`, `max_rpm` **7300**, `optimal_rpm` **5000** —
so a 40 m/s AI ceiling is reachable in the top gear without touching the drivetrain.

### 6.3 The timing

```
ceiling v = 40.0 m/s            (BmAK SVehicle.MaxSpeed 4000 cm/s)
t = d / v                        (no acceleration, no skid ramp - both unquantified)

d =  30 m -> 0.75 s      d =  80 m -> 2.00 s      d = 150 m -> 3.75 s
d =  60 m -> 1.50 s      d = 100 m -> 2.50 s      d = 250 m -> 6.25 s
                          d = 400 m -> 10.00 s
```

Recommended default: **marker at 80 m on the road the player is facing → 2.0 s of travel** at the 40 m/s
ceiling, then the `Limit_Speed` tail (≈7.9 units) and the 14000 N·m rear handbrake for the stop. BmAK's own
boost usage during a call is undecoded, so the boost (`SelfDriveAllowBoost=True`) is **not** in this schedule.

### 6.4 The teleport-and-brake fallback (the arrival state without travel)

If the drive leg cannot be aimed (§7), the honest minimal build is Carrier D alone:

1. drop marker **on the player's road, 6–8 m ahead, facing the player**;
2. spawn the `.ee` there at velocity 0 — the marker transform *is* the arrival pose;
3. `brakes_ai` as §6.2 (`rear.handbrake` 1, `handbrake_friction_factor` 2) so the car stands locked, which is
   what BmAK's `bSkidToStop` + `DestReachedSkidToStop` state ends in;
4. headlights per the existing plan (`VehicleDynamicLights` `HeadLight`), engine bed as the approach sound.

That reproduces **where it stops and in what state**; it does not reproduce 2 s of travel, and the report says
so rather than implying the drive-in exists in the tables.

---

## 7. The one probe that settles the destination member

The gap is exactly one datum: **which parameter of `civilian_std.bts` (or of `vehicle_delivery.gsc`) is the
goal**, and whether it accepts a player coordinate. Five-minute experiments, in cost order:

| # | probe | what it settles | cost |
|---|---|---|---|
| P-1 | replace `civilian_01` (already the current B-13b entity path) and walk in front of a spawned Batmobile in a liberated province | whether `civilian_std.bts` chases/avoids the player at all | one play session, no data edit |
| P-2 | hash-match the **unmatched** class hashes of `vehicle_delivery.gsc` against the 44 other `_ai.vmodc`/graph names and the string table of `profile/online.stringlookup` | whether a `SetDestination`-class node exists in that graph | minutes, no game launch |
| P-3 | dump `graphs/random_encounters/vehicle_delivery_timer.gsc`'s six `time` values and run the encounter once | the arrival's own timer (the graph already models a wait) | one encounter |
| P-4 | read the `.bts` payloads: the index has **0 `.bts` entries**, so they live inside a package (`.blo`/`.ee` inner file) — locate the container, then decode | the behaviour tree's goal node and its parameter names | the real fix |

P-4 is the one that turns the §6 recipe from "drive with the AI tune set + authored goal" into a translation.

---

## 8. What this changes in the earlier plan

| old text (`summon-and-arrival-plan.md`) | replacement |
|---|---|
| §8.4 item 5 — the earlier "blocked" verdict, now withdrawn | **Carrier A** (five `_ai.vmodc` modules: `Limit_Speed` 35→40, `brakes_ai` 14000/1/2, `land_steering_ai` 2 s/45°) + **Carrier B** (`ai/bts/civilian/civilian_std.bts` via `03_CivilianCarLiberatedProvince`) + **Carrier C** (`vehicle_delivery` / `msub_vehicle_controller` graphs) give the self-drive, its speed and its skid stop; the goal parameter is unread, not absent (§7) |
| §8.2 row "drive-in route … no reuse" | **partial reuse**: the AI tune set and the traffic driver are reusable as-is; the goal is the one authored/probed value |
| §8.3 "the honest JC3 behaviour is the drop at a marker near the player" | still the **fallback** (§6.4), no longer the only option |

---

## 9. Checks run

| check | result |
|---|---|
| five AI modules exist on the donor and are graded FULL | `DECODE_DEPTH.md:539-543` (1345 / 523 / 445 / 1494 / 1073 B) |
| AI module rows re-read | `v0300_..._ai.vmodc` 61 rows, `_brakes_ai` 7, `_land_steering_ai` 15, `_land_global_ai` 36, `_land_aerodynamics_ai` 5 |
| `Limit_Speed` fleet comparison | 6 vehicles: 22 / 30 / 35 / 35 / 35 / 40 (`y_max`), `y_min` 2 / 5 / 8 |
| brake/steer/aero player-vs-AI pairs | 10000→14000, 5→1, 1→2; 1.2→2.0 s, 35/15→45/10 deg; 0.33→0.80 drag |
| drivetrain caps | `official_top_speed` 250, `transmission.top_speed` 320, 6 gears, `max_rpm` 7300 |
| traffic-rule behaviour trees | 10 `ai/bts/…` paths printed from `global/global.blo` (patch, 79,340 B, `RTPC`) |
| `.bts` readability | `grep -c '\.bts"' Research/JC3Grab/INDEX.jsonl` → **0** |
| graph carriers | 7 graphs extracted, all `ADF ` v4; node/data hash counts in §4 |
| hash recovery | 35,681 candidate tokens → only Block/Main/Health/Heat/EnterVehicle/Graph/Seat/Door recovered |
| drop/spawn-rule fields | `Item` (26 members, no position); `CVehicleRule` chance/heat_level/spawn_event/health/invulnerable all 0 |
| timing arithmetic | `t = d/40 m/s` at seven distances — 0.75, 1.50, 2.00, 2.50, 3.75, 6.25, 10.00 s |

Probe artefacts (outside the repo's research tree): `tmp/freebuff/probe/global.blo`,
`tmp/freebuff/probe/gsc/*.gsc` + `*.txt`. Nothing in `Research/`, `Builds/`, `Working/` or the install was
modified.

---

## 10. Change record (per `AGENTS.md`)

1. **Intended change:** add one report that replaces the earlier "blocked" verdict with the named carriers,
   their members and a build recipe for BmAK's drive-in arrival.
2. **File:** `tmp/freebuff/reports/summon-drive-in-closest-system.md` (this file). Correct file because the
   brief names it and every comparable plan lives in `tmp/freebuff/reports/`; no `Research/` table, build,
   entity, module, graph or install is regenerated.
3. **Revert:** delete this file and `tmp/freebuff/probe/` (the extracted `global.blo` and five graphs).
   Nothing else changed.

---

## 11. UNKNOWNs

| # | UNKNOWN | what settles it |
|---|---|---|
| U-1 | the unit of `Limit_Speed` (value 5..40) and of `Input_Speed` (1..15) | no file states it; P-1 measures the car's road speed against the limit |
| U-2 | the destination parameter of `civilian_std.bts` and its accepted target type | P-4: locate and decode the `.bts` container (0 entries in the index) |
| U-3 | whether `vehicle_delivery.gsc`'s unmatched class hashes include a set-destination node | P-2 (hash-match against the full string table `profile/online.stringlookup`) |
| U-4 | BmAK's call delay, stop radius and whether the call boosts | the 25 `RBatmobileRemoteBm` behaviour bodies (no bytecode) |
| U-5 | the metric stopping distance from 14000 N·m at 0.38 m wheel radius | needs `rigid_body` mass, not read in this pass |
| U-6 | whether `Limit_Speed` is read by the traffic AI only, or also by mission-driven vehicles | P-1 / P-3 |
