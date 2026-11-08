# Water entry: the closest JC3 system that puts a vehicle back on land

**The behaviour to build (operator, 2026-11-08).** The Batmobile cannot swim. Driving it into water
**teleports it to land** — the same thing that happens when Batman tries to swim — and **the engine does not
fail**. Sinking-and-stalling is *not* the target. So the previous water plan's conclusion
(`water-crossing-batmobile-build-plan.md`: "sink and stall is already what ships, change nothing") is the
wrong behaviour for this decision: the build must suppress the sink and add a return-to-land move.

**Answer in one line.** JC3 has **no member that carries "vehicle in water → move to land"**; what it has is
(a) a **native teleport gate** named `is_safe_to_teleport` in the executable's variable-name block, (b) a
**native `sinking_progress`** variable beside it, (c) a player-triggered vehicle reset action
**`CHALLENGE_RESET_VEHICLE`** (LPADDOWN / `P`, scope `land-vehicle`), and (d) a vehicle-in-water exit state
**`S_EXIT_DRIVER_VEHICLE_IN_WATER`** reached from `exit.driver.to.swim` on 191 vehicles. The build therefore
takes the **`CHALLENGE_RESET_VEHICLE` route re-pointed at a nearest-land destination**: the reset exists, its
*player* trigger is a key, its destination rule is **UNKNOWN**, and the automatic water trigger plus the
nearest-land pick are what this build adds.

Evidence levels: **decoded** = read at the cited file/line; **derived** = arithmetic or a stated rule over
decoded inputs; **chosen** = a design number this plan picks because no file carries one (never presented as
decoded); **UNKNOWN** = searched and absent, with the file that would settle it.

---

## 1. The reference behaviour, and what BmAK's own data carries

The operator's fact is the specification: water contact → car reappears on land, engine intact. BmAK's data
does carry water state, which is what makes a "teleport on hit" plausible there:

| member | offset | mask | value | evidence |
|---|---:|---|---|---|
| `BatmobileHitWater` | 4572 (0x11dc) | 0x8000 | bool | decoded — `Research/BatmobileGrab/BMSDK_OFFSETS.json` |
| `BatmobileAboutToHitWater` | 4572 (0x11dc) | 0x20000 | bool | decoded — same |
| `BatmobileAboveOceanLevel` | 4572 (0x11dc) | 0x10000 | bool | decoded — same |
| `BatmobileAboutToAboveOceanLevel` | 4572 (0x11dc) | 0x40000 | bool | decoded — same |
| `BatmobileStuckTime` | 7448 (0x1d18) | — | float, current | decoded — `CONTROLS_NATIVE2.md` line 109 |
| `BatmobileStuckTimeMax` | 7452 (0x1d24) | — | **2.0** | decoded — `Research/BatmobileGrab/CLASS_DEFAULTS.md` row 109 |
| `BatmobileStuckTimeFlip` | 7456 (0x1d28) | — | **0.5** | decoded — same, row 110 |

So BmAK has a **water-hit flag**, an **about-to-hit** flag, an **ocean-level** pair, and a **stuck timer with a
2.0 s ceiling**. What BmAK *does* with `BatmobileHitWater` is in the executable, not in the object →
**UNKNOWN** (settler: the consumer of `BatmobileHitWater` in `BatmanAK.exe`; the repo decodes the flag sites
but not the branch body). `BatmobileStuckTimeMax` 2.0 s is the only reset-shaped *number* either game's data
carries, and it is a stuck timer, not a water timer — it is cited here as a ceiling for the build's own
water dwell, not as BmAK's water delay.

Also present in the BmAK name set and worth naming because the operator's sentence is about Batman swimming:
`bCanSwim` exists as a member name in `BMSDK_OFFSETS.json`. Its class and value were **not** read in this
pass → **UNKNOWN**, and nothing below depends on it.

---

## 2. JC3: every mechanism that could move a vehicle out of water

### 2.1 The water modules (what the car does *by itself*) — decoded

From `Research/JC3Grab/WATER.md` (G2-31), the build `Builds/test-091/v0300_car_kensington_sportsmuscle_civilian_01.ee`
carries the donor's modules **identical** to the donor cache:

| module | file inside the `.ee` | key values |
|---|---|---|
| `WaterInteraction` | `v0300_car_kensington_sportsmuscle_water_interaction.vmodc` | `will_sink` **1**; `pressure_drag` 5000; `suction_drag` 5000; `depth_full_drag` 0.1; `anti_penetration_max_accel` 15; `anti_penetration_multiplier` 2; 1 hull element |
| `Buoyancy` | `v0300_car_kensington_sportsmuscle_buoyancy.vmodc` | `buoyancy` **2**; `drag` 100; `radius` 0.55; `side_area` 1.85; `bottom_area` 3; `up_velocity_cap` 20 |
| `VehicleCommon` (shared) | `00_shared/modules/vehicle_common.vmodc` | `vehicle_damage.min_water_entry_ms` 10, `fatal_water_entry_ms` 20, `min_water_entry_floating_ms` 20, `fatal_water_entry_floating_ms` 50; `car_common.engine_shut_down_delay_s` **30** |

This is the **sink-and-stall** path, and it is exactly the path this decision rejects: `will_sink` 1 makes the
hull go down, the 30 s car timer cuts the engine, and `fatal_water_entry_ms` 20 (unit **UNKNOWN** — 10/20 ms
cannot be a drown timer) is the fleet-wide kill. `WATER.md` §9 records **no member anywhere** that makes a
hull dive and stay drivable, and none that returns a vehicle to land.

### 2.2 The teleport gate and the sinking variable — decoded names, native semantics

`Research/JC3Grab/EMP_DISABLE.json`, section `exe` → `variable_name_block` (the executable's own variable-name
strings, **not** an entity module), carries these members with their addresses:

| name | address | why it matters here |
|---|---:|---|
| `is_safe_to_teleport` | 0x24e9f50 | **the only teleport-named variable in either game's research set** — a gate the engine consults before moving a vehicle |
| `sinking_progress` | 0x24e9db8 | the sink ramp as a **progress** value — the natural trigger for "the car is in the water far enough" |
| `height_above_highest_ground` | 0x24e9d80 | ground-relative height — the natural test for "landed on land, not on water" |
| `is_despawnable` | 0x24e9ef0 | whether the vehicle may be removed at all |
| `in_cargo_bay` | 0x24e9f68 | the cargo-bay exclusion (`CVehicleCargoBay` on 12 entities, `Research/JC3Grab/TETHER.md` §2) |

Types, ranges and writers of all five are **not** decoded (the block is a name/address list) → the numbers
below never claim to be their defaults. What this settles is the *vocabulary*: the engine has a sink progress
and a teleport safety gate, which is precisely the pair a water-to-land move needs.

### 2.3 The player reset — `CHALLENGE_RESET_VEHICLE` — decoded

`Research/JC3Grab/INPUT.md` line 61 and the `land-vehicle` action set (line 223):

| action | gamepad | keyboard | scope |
|---|---|---|---|
| `CHALLENGE_RESET_VEHICLE` | **LPADDOWN** | **P** | `land-vehicle` |

It ships in the land-vehicle action set at both the gamepad and keyboard layers
(`INPUT.json` nodes 75, 82, 49, 52 — base and patch). It is the closest shipped **vehicle reset**: a
land vehicle is put back on the road on demand. Two things are not in the data: **who consumes the action**
(0 `.gsc`/`.bl` consumer found by name scan) and **how the destination is chosen** → **UNKNOWN**, settler =
the graph/state machine that binds `CHALLENGE_RESET_VEHICLE`, or a live test on `P` in a challenge.

### 2.4 The vehicle-in-water occupant state — decoded

`Research/JC3Grab/EJECT.md` line 75 / §"exit states": `exit.driver.to.swim` → **`S_EXIT_DRIVER_VEHICLE_IN_WATER`**,
present on **191 vehicles** (with `S_EXIT_IN_WATER_MOTORBIKE` as a second in-water exit state, line 138). So
JC3 already **classifies "vehicle in water"** in its exit state machine. That is a usable trigger source that
does not invent a depth.

### 2.5 What does **not** exist (searched, absent)

| searched | result | evidence |
|---|---|---|
| a `nearest_land` / `reset_vehicle` / `unstuck` member in any vehicle module | **none** | `WATER.md` §9 keyword scan (38 water paths, 232 entities × 52 module types) |
| a `drown`/`submerge`/`flood`/`swim`/`underwater` member | **none** | same |
| a water→land teleport in the levels | **none by name**; the only teleports in the index are the easter-egg/outpost/mission-exit graphs (`graphs/easter_eggs/majestic_3_rico_teleporter.gsc`, `graphs/military/outpost_post_liberation_teleport.gsc`, `graphs/mission/modules/msub_teleport_on_mission_exit.gsc`) | `INDEX.jsonl` path scan |
| road geometry to aim at | **present as data**: `settings/road_logic.bin`, `settings/road_presets.bin`, `settings/road_rendering.bin`, `settings/roaddecorationtypes.bin`, `settings/spawn_road_decoration_defs.bin`, and a level `dlc/mech_land_assault/locations/roads/roads_01.bl` | `INDEX.jsonl` |

So the honest split is: **the reset exists, the destination does not**. Every `road*.bin` above is a road
*definition* (presets, logic, rendering), none of them a decoded "nearest road node" query.

---

## 3. The mechanism to adopt

**`CHALLENGE_RESET_VEHICLE`, re-pointed.** The build watches water contact, and on contact performs the same
kind of reset the challenge action performs — but with a **nearest-land destination** and **without** touching
the engine state. That is the one route that (a) is a shipped JC3 concept, (b) does not require a buoyancy or
sink edit that would change the hull's water behaviour everywhere, and (c) leaves the engine running, which is
the operator's explicit requirement.

| step | what happens | member / file that carries it | evidence |
|---|---|---|---|
| 1 | water contact is detected | `sinking_progress` (exe var 0x24e9db8) **or** the in-water exit state `S_EXIT_DRIVER_VEHICLE_IN_WATER` / `exit.driver.to.swim` (191 vehicles) **or** `WaterInteraction` hull contact via `number_of_water_collision_sensors` | decoded names; which of the three fires first is UNKNOWN |
| 2 | the move is authorised | `is_safe_to_teleport` (exe var 0x24e9f50); `is_despawnable` (0x24e9ef0) and `in_cargo_bay` (0x24e9f68) as exclusions | decoded names |
| 3 | a destination is found | **no member** — computed by the build (§5) | UNKNOWN, this is the added part |
| 4 | the car is placed | `CHALLENGE_RESET_VEHICLE` semantics (LPADDOWN / `P`, `land-vehicle`) — the reset the game already ships | decoded action |
| 5 | the sink is suppressed | `WaterInteraction.will_sink` **1 → 0** on the build's own `..._water_interaction.vmodc` | decoded value, one-line edit |

Step 5 is the only data edit in the whole design, and it is the one that turns "sink and stall" into "cannot
swim" at the hull level: with `will_sink` **0** the donor precedent is the **APC**
(`v0200_car_capstone_apc_*`: `will_sink` 0, plain `Buoyancy` 2, **no** `BoatBuoyancy`, `WATER.md` §5). The
build then needs **no new module** — the float body it already has (`buoyancy` 2) becomes active, exactly as
on the APC. **Do not** add `BoatBuoyancy`: that is the amphibious route D-8 rejected and would make it a boat.

---

## 4. The trigger

**There is no depth member anywhere in the fleet** (`WATER.md` §9: no metre value for a waterline, wade depth
or submersion limit; the geometric members `radius` 0.55 / `side_area` 1.85 / `bottom_area` 3 are float-model
quantities). So the trigger must be a **progress or state**, never "depth in metres".

| trigger option | member | value to write | evidence |
|---|---|---|---|
| A (preferred) | `sinking_progress` (exe var 0x24e9db8) | fire at **≥ 0.30** of the variable's full range | name decoded, **range UNKNOWN** → the 0.30 is **chosen**, not decoded; it is one third of the ramp, so it fires well before the hull is submerged |
| B (fallback) | in-water exit state `S_EXIT_DRIVER_VEHICLE_IN_WATER` | fire on that state becoming true | decoded state name, 191 vehicles |
| C (geometric) | hull submersion from `WaterInteraction.part_elements[]` | fire when the hull's lowest point is **> 0.25 m** below the water plane | **chosen**; `part_elements` is the water-plane collider (`WATER.md` §2.2), the 0.25 m is a design number |
| not usable | `vehicle_damage.fatal_water_entry_ms` 20 / `min_water_entry_ms` 10 | — | **unit UNKNOWN** (10/20 ms cannot be a dwell timer), so it must not be read as seconds |

**Trigger depth, stated plainly: UNKNOWN as a number.** The only file-backed statement is qualitative —
`will_sink` decides whether the hull goes down, and the entry thresholds exist with an undecoded unit. The
build therefore uses a **progress threshold** (option A/B) and a **geometric backstop** (option C), and the
depth in metres is measured at runtime, not written.

Two guards belong to the trigger and are **chosen**:

* **dwell** 0.15 s of continuous water contact before firing — stops a splash or a puddle flicker from
  teleporting the car (and matches `BatmobileAboutToHitWater`'s existence in BmAK: the reference distinguishes
  "about to" from "hit").
* **cooldown** 3.0 s after a teleport, so a car that lands beside the water cannot loop.

---

## 5. The destination rule

BmAK puts the car "on land". **How BmAK picks the point is UNKNOWN** (settler: the `BatmobileHitWater`
consumer in `BatmanAK.exe`). The build therefore needs an explicit rule, and the one that matches "teleported
to land, the same as Batman swimming" is: **nearest dry, drivable ground to the entry point**, searched
outward from the car's own position, preferring a road when one is within reach.

| step | rule | value | evidence |
|---|---|---|---|
| 1 | search origin = the car's position **at the moment of contact**, not its live (sinking) position | — | derived: a sinking car drifts; the entry point is the stable anchor |
| 2 | rings 8 m → 40 m, step 2 m, 16 bearings per ring | 8/40/2/16 | **chosen** |
| 3 | accept a candidate only if a downward trace hits ground with surface normal ≤ **20°** from up | 20° | **chosen** |
| 4 | reject any candidate whose ground height is **below the water plane** at that point (the dry test) | water plane + 0.05 m | **chosen** |
| 5 | reject if the car's box is obstructed at the candidate (**1.5 m** clearance above ground, 2.5 m radius) | 1.5 / 2.5 m | **chosen** |
| 6 | prefer a road: if `settings/road_logic.bin` / `road_presets.bin` yields a road point inside the searched disc, take the nearest road point instead of the nearest ground | — | files exist (`INDEX.jsonl`); **the query API is UNKNOWN** → this sub-step is optional and must degrade to step 5 |
| 7 | place: same heading, upright, **1.5 m** above the found ground, linear velocity and angular velocity zeroed | 1.5 m | **chosen** |
| 8 | fail-safe: if no candidate passes, place at the **entry-side shore** — step back along the car's travel vector in 2 m increments until the dry test passes, up to **60 m** | 2/60 m | **chosen**; guarantees a deterministic outcome over "no teleport" |

**Why "nearest land" and not "last road node":** nothing in either grab stores a road node on a vehicle, and
the reset action's own destination is UNKNOWN (§2.3). A ring search over the physics world needs no new data,
degrades to the fail-safe, and can be replaced by a road query the day `road_logic.bin` is decoded.

---

## 6. What the build adds

| # | add | where | values | evidence |
|---|---|---|---|---|
| A1 | `will_sink` **1 → 0** on the build's own copy | `Builds/test-091/.../v0300_car_kensington_sportsmuscle_water_interaction.vmodc` | 0 | decoded member, APC precedent (`WATER.md` §5) |
| A2 | keep `Buoyancy` as-is (do **not** add `BoatBuoyancy`) | `..._buoyancy.vmodc` | `buoyancy` 2, `drag` 100, `radius` 0.55, `side_area` 1.85, `bottom_area` 3, `up_velocity_cap` 20 | decoded |
| A3 | water-contact watcher + teleport driver | a per-vehicle script/graph bound to the build's entity (the layer `CHALLENGE_RESET_VEHICLE` is bound in) | dwell 0.15 s, cooldown 3.0 s | chosen; the binding layer is **UNKNOWN** (§2.3) |
| A4 | nearest-land search | same script | 16 bearings × 16 rings (8–40 m, 2 m step), slope 20°, clearance 1.5 m / 2.5 m, fail-safe 2 m × 60 m | chosen |
| A5 | placement | same script | heading kept, upright, 1.5 m above ground, velocities zeroed | chosen |
| A6 | engine untouched | `vehicle_common.vmodc` **not** edited | `car_common.engine_shut_down_delay_s` stays 30, `fatal_water_entry_ms` stays 20 | decoded; editing it is fleet-wide (all 232 entities share it) and would change every car — explicitly **not** part of this build |
| A7 | audio/visual cue on the move | effect/audio table, not a water member | — | **UNKNOWN**; settles in `Research/JC3Grab/FX.md` / `JC3_AUDIO.md` |

**Revert.** A1: restore `..._water_interaction.vmodc` from the donor copy in the build's AAF tree
(`Builds/test-091/aaf/.../modules/default/`), repack, reinstall. A3–A5: remove the script/graph binding.
A6: nothing to revert (no edit).

---

## 7. Pilot card

**W8 — water entry teleports to land.**
*Drive the Batmobile into a lake at 40 km/h and hold the throttle: within **2.0 s** of the hull first
contacting water the car is standing upright on dry, drivable ground **within 15 m** of the entry point, heading
unchanged, engine still running, and it drives away under its own power.*
**Pass band:** 3/3 attempts; teleport latency ≤ 2.0 s measured frame-to-frame; landing point ≤ 15 m from the
entry point and **above** the water plane; **zero** engine-cut entries in the damage log; **zero** repeat
teleports (no more than one per entry). *Fail conditions:* the car sinks below the waterline at all (A1 not
read), the engine cuts (A6 leaked), the car lands in water again (A4 dry test), or it teleports twice in a row
(cooldown/dwell).

---

## 8. THEORY — sea-floor driving (not the build, recorded because it was asked for)

> **Status: theory.** Nothing here is measured, nothing here is proposed for this build, and `WATER.md` §9
> states the reason: **no member in any of the 52 module types makes a hull dive and stay drivable.** A
> submerged-but-driving car is therefore native behaviour that is not in the data. The rows below are the
> members that *would* be involved if the idea were ever pursued.

| behaviour needed | member | build value now | what a sea-floor mode would want | evidence |
|---|---|---:|---|---|
| stop the hull sinking | `WaterInteraction.will_sink` | 1 | **0**, and keep it out of the `BoatBuoyancy` path | decoded |
| remove lift so it stays down | `Buoyancy.buoyancy` | 2 | **0** (the multiplier, not a switch — `WATER.md` §5) | decoded |
| keep the hull from being pushed out by the water plane | `WaterInteraction.anti_penetration_max_accel` / `anti_penetration_multiplier` | 15 / 2 | lower both, or the anti-penetration term fights the dive | decoded |
| cap the upward push | `Buoyancy.up_velocity_cap` | 20 | small (e.g. 1–2) | decoded, value **chosen** |
| heavy fluid drag | `WaterInteraction.pressure_drag` / `pressure_drag_2` / `suction_drag` / `depth_full_drag` | 5000 / 20000 / 5000 / 0.1 | raise `depth_full_drag` so full drag applies sooner; `reference_drag_speed_ms` 20 sets the speed the drags are referenced to | decoded |
| keep it moving with wheels on the bottom | `Fins.fins[].effective_in_water` | present (1 path fleet-wide) | — | decoded name only; per-entity values not read |
| water sensors on rotating parts | `VehicleCommon.all_rotating_part_properties[].number_of_water_collision_sensors` | 5 on index 0; 3 on 1, 6, 7, 8, 10, 11; 0 elsewhere | these are what make contact *and* what would stall the engine | decoded |
| not die while submerged | `vehicle_damage.fatal_water_entry_ms` / `_floating_` | 20 / 50 | would have to be neutralised in a **private** `vehicle_common.vmodc` (shared by all 232 entities) | decoded values, **unit UNKNOWN** |

Two blockers make this theory rather than a plan: the `_ms` unit is undecoded, so "neutralise the fatal
timer" cannot be expressed as a number; and the engine's behaviour after that timer is **UNKNOWN**
(`WATER.md` §9). The nearest evidence that anything like it ships is `v2603_helicopter_urga_seascout`
(`will_sink` 0, `buoyancy` 0.25) — a sea *scout*, not a sea-floor driver.

---

## 9. UNKNOWNs, each with the settling file

| # | UNKNOWN | settler |
|---|---|---|
| U1 | what BmAK does when `BatmobileHitWater` is set (teleport? eject? damage?) | the consumer of `BatmobileHitWater` in `BatmanAK.exe` — `CONTROLS_NATIVE2.md` maps the flag sites, not the branch body |
| U2 | BmAK's destination rule ("where is land") | the same consumer; no destination member exists in the grab |
| U3 | who consumes `CHALLENGE_RESET_VEHICLE`, and its destination | the graph/state machine binding the action (`INPUT.json` gives the binding, not the consumer); or a live `P` press in a challenge |
| U4 | type, range and writer of `sinking_progress` | the executable's variable table (`EMP_DISABLE.json` holds names + addresses only) |
| U5 | type/semantics of `is_safe_to_teleport` (bool? float? per-frame?) | same |
| U6 | the unit behind `vehicle_damage.*_water_entry_ms` (10/20/20/50) | water-entry consumer in `JustCause3.exe` (`WATER.md` §7) |
| U7 | whether a nearest-road query exists at runtime for `road_logic.bin` / `road_presets.bin` | those `.bin` decodes; until then step 6 of §5 degrades to pure nearest-ground |
| U8 | the wade depth in metres | no metre member exists (`WATER.md`); measure on the built car |

---

## 10. Change record (per `AGENTS.md`)

1. **Intended change:** add one plan naming the closest JC3 mechanism for "vehicle in water → land", its
   member/file, the trigger, the destination rule, the values to write, and the sea-floor idea as separate
   theory.
2. **File:** `tmp/freebuff/reports/water-entry-teleport-closest-system-plan.md` — the brief names this path;
   every comparable plan lives in `tmp/freebuff/reports/`. No `Research/` card regenerated, no `Builds/` file
   touched, no archive or shared game module edited, no game launched.
3. **Why this file:** `WATER.md` (G2-31) is the water source and is cited by section; the JC3 mechanism names
   come from `INPUT.md`, `EJECT.md`, `TETHER.md` and the `exe` block of `EMP_DISABLE.json`; the BmAK flags come
   from `BMSDK_OFFSETS.json`, `CLASS_DEFAULTS.md` and `CONTROLS_NATIVE2.md`.
4. **Revert:** delete this file. Nothing else changed.

## 11. Checks run

| check | result |
|---|---|
| the behaviour asked for is a teleport, not a sink | PASS — §0 states it, and §6 A6 leaves the sink timers untouched |
| `will_sink` value re-read from the build | PASS — 1 today (`WATER.md` §8), 0 is the proposed edit (APC precedent) |
| no `BoatBuoyancy` added | PASS — §6 A2 |
| a teleport-named member exists in JC3 | PASS — `is_safe_to_teleport` (exe var 0x24e9f50), cited with its section |
| a sink-progress member exists | PASS — `sinking_progress` (exe var 0x24e9db8) |
| a vehicle reset exists in JC3 | PASS — `CHALLENGE_RESET_VEHICLE`, LPADDOWN / `P`, scope `land-vehicle` |
| the reset's destination rule is known | FAIL (as expected) — U3; the plan supplies its own rule in §5 |
| a "nearest land" member exists | FAIL (searched) — none; §5 computes it |
| trigger depth in metres | FAIL (searched) — no metre member; §4 uses progress/state + geometric backstop |
| every written number is labelled decoded / chosen / UNKNOWN | PASS — §4, §5, §6 |
| road data exists to prefer later | PASS — `settings/road_logic.bin`, `road_presets.bin`, `road_rendering.bin`, `locations/roads/roads_01.bl` |
| sea-floor driving kept separate and marked theory | PASS — §8 |
| pilot card carries a pass band | PASS — W8, 3/3, ≤ 2.0 s, ≤ 15 m |
