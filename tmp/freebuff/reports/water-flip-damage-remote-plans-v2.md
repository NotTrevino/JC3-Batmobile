# Water, righting, death and remote — four operator facts, plans v2

Card: water-flip-damage-remote-plans-v2. 2026-11-08. Four operator observations of 2026-11-08, each
reconciled against the older plan it contradicts and against the fresh plan written for it. One
section per fact: what survives, what is overturned (named), the single reconciled plan with its
closest JC3 system, members, gap and build step.

Labels: **decoded** = value read at the cited file:line; **derived** = arithmetic or a stated rule
over decoded values; **chosen** = a design number no file carries; **UNKNOWN** = searched and absent,
settler named in §5.

Source plans: `water-and-terrain-handling-plan.md`, `water-crossing-batmobile-build-plan.md`,
`stuck-flip-recovery-plan.md`, `stuck-flip-build-plan-merge.md`, `health-damage-states-plan.md`,
`armour-plates-and-deformation-plan.md`, `remote-and-autonomous-drive-plan.md`, and the four fresh
reports `water-entry-teleport-closest-system-plan.md`, `flip-recovery-idle-timer-and-thruster-plan.md`,
`health-to-explosion-no-crash-damage-plan.md`, `remote-control-range-static-overlay-plan.md`.

---

## 1. Water entry teleports the car to land

**Operator fact:** the Batmobile cannot swim. Driving into water **teleports it to land**, the way
Batman swimming does, and **the engine does not fail**.

### 1.1 What survives from the older plans

| survives | value | source |
|---|---|---|
| the water module block the build already carries | `WaterInteraction.will_sink` **1**; `pressure_drag` 5000 / `_2` 20000; `suction_drag` 5000 / `_2` 20000; `depth_full_drag` 0.1; `anti_penetration_max_accel` 15 / `_multiplier` 2; 1 hull element | decoded — `WATER.md` §2, `water-and-terrain-handling-plan.md:209–226`, `water-crossing-batmobile-build-plan.md` §2.2 |
| the float body | `Buoyancy.buoyancy` **2**, `drag` 100, `radius` 0.55, `side_area` 1.85, `bottom_area` 3, `up_velocity_cap` 20 | decoded — same |
| the shared engine/death timers | `car_common.engine_shut_down_delay_s` **30**; `vehicle_damage.min_water_entry_ms` 10, `fatal_water_entry_ms` 20, floating 20 / 50 | decoded values, **unit of the `_ms` pair UNKNOWN** — `WATER.md` §2.3 |
| "no depth exists in metres anywhere in the fleet" | 0 members | decoded absence — `WATER.md` §9 |
| "do not add `BoatBuoyancy`" | — | decoded design rule, APC precedent `will_sink` 0 |
| the build carries the donor's water modules byte-for-byte | — | decoded — `WATER.md` §8 |

### 1.2 What the observation overturns — named

| # | old claim | where | why it dies |
|---|---|---|---|
| W-O1 | **`will_sink` = keep 1** ("sinks, like the donor and 189/232") | `water-and-terrain-handling-plan.md:213` (§3.2 row) | the operator's target is a car that does **not** go down; keeping 1 is the sink path |
| W-O2 | **"sink and stall is what the build already does — touching the values *is* the change"**, recorded as the verdict that no water edit is needed for the lore route | `water-crossing-batmobile-build-plan.md:125` | that is precisely the behaviour being replaced: the build must **suppress** the sink and add a return-to-land move |
| W-O3 | the water pilot cards that accept sinking as pass | `water-crossing-batmobile-build-plan.md` §5 | a card may no longer pass on "the car sinks and the engine cuts" |

### 1.3 The reconciled plan

| part | value / member | label |
|---|---|---|
| BmAK reference: water flags | `BatmobileHitWater` 4572 mask **0x8000**; `BatmobileAboutToHitWater` **0x20000**; `BatmobileAboveOceanLevel` **0x10000**; `BatmobileAboutToAboveOceanLevel` **0x40000** | decoded — `BMSDK_OFFSETS.json` |
| BmAK reference: the only reset-shaped number | `BatmobileStuckTimeMax` **2.0**, `BatmobileStuckTimeFlip` **0.5**, `BatmobileStuckTime` 0x1d18 (**value UNKNOWN**) | decoded / UNKNOWN |
| **closest JC3 system** | **`CHALLENGE_RESET_VEHICLE`** re-pointed at nearest land — the only shipped land-vehicle reset | decoded action: gamepad **LPADDOWN**, keyboard **P**, scope `land-vehicle` (`INPUT.md:61`, `:223`) |
| trigger vocabulary | `sinking_progress` 0x24e9db8; `is_safe_to_teleport` 0x24e9f50; `height_above_highest_ground` 0x24e9d80; `is_despawnable` 0x24e9ef0; `in_cargo_bay` 0x24e9f68 | decoded names + addresses; **types/ranges UNKNOWN** (`EMP_DISABLE.json` `exe.variable_name_block`) |
| second trigger source | in-water exit state `S_EXIT_DRIVER_VEHICLE_IN_WATER` via `exit.driver.to.swim`, **191** vehicles | decoded — `EJECT.md:75`, recount |
| sink suppression | `will_sink` **1 → 0** on the build's own `..._water_interaction.vmodc` | decoded member, APC precedent |
| **gap** | **no destination member**: nothing in JC3 computes "nearest land", and the reset's own destination rule is UNKNOWN | decoded absence (`WATER.md` §9) |
| **build step** | one edit + one script: (a) `will_sink` 0; (b) keep `Buoyancy` as shipped; (c) water watcher on `sinking_progress` ≥ **0.30** (chosen) or the in-water state, dwell **0.15 s** (chosen), cooldown **3.0 s** (chosen); (d) nearest-land ring search 8→40 m, 2 m step, 16 bearings, slope ≤ **20°**, clearance 1.5 m / 2.5 m (all chosen), place upright 1.5 m above ground with velocities zeroed; (e) `vehicle_common` **untouched** (30 s engine timer stays) | chosen + decoded mix, each labelled |

**Pilot (W8):** into a lake at 40 km/h → car on dry ground **within 15 m** of the entry point, upright,
heading kept, **engine running**, **≤ 2.0 s** from first contact, 3/3, no repeat teleport.

---

## 2. A stuck or flipped car rights itself with its thrusters after a while

**Operator fact:** rest on the roof or side for a while → thrusters fire → the car rights itself.

### 2.1 What survives

| survives | value | source |
|---|---|---|
| **no roll-angle field** gates the flip | 0 hits for any `*Roll*Angle*` / `RightingAngle` / `MaxTilt` on the vehicle | decoded absence, re-tested — `flip-recovery-idle-timer-and-thruster-plan.md` §1.3 |
| **no speed gate** | 0 hits | decoded absence, re-tested — same |
| the flip does **not** share the strafe kick | `TryRightingFlip` 10572 / `FlipVehicle` 10596 reference no `KickStrafe` / `SideExhaust*`; field sets disjoint | decoded — same |
| the physics the righting needs | **230,300 N·m for 0.5 s**, or **57,600 N·m·s**, damped at **0.985** (10°) of world up | derived — `stuck-flip-recovery-plan.md:212`, merge §3.2 |
| the upright test JC3 does have | `CInteractionGraphParentIsUpRightCondition`, **6,761** instances | decoded — `ENTITIES.md:11` |
| the thruster effect carrier | usage **`EngineTurboJump`**, **349** objects / **164** entities | decoded — `USAGES.md` |

### 2.2 What the observation overturns — named

| # | old claim | where | why it dies |
|---|---|---|---|
| F-O1 | **the flip is bound to B** (`XboxTypeS_B` → `QuickGadgetB` chain), treated as the input to settle | `stuck-flip-recovery-plan.md:47`, §1.2, §2.2 ("the B conflict") | B is **Tracker / Immobiliser** in pursuit and **EMP** in battle (`CONTROLS_MENU_SCREENS.md:16`, `:32`; `CONTROLS_CONSUMERS.md:28`). The controls scheme is fixed by the operator, and the flip **has no key** in BmAK's menu at all |
| F-O2 | the righting is a **manual** action whose trigger must be decoded from an input | `stuck-flip-recovery-plan.md` §1.2–§1.3, `stuck-flip-build-plan-merge.md` §1 | the operator's fact is that it fires **by itself, after a rest**. The trigger source changes from a key to a timer pair — the one thing both older plans did not model |
| F-O3 | the "give-up" route (respawn/reset) is the primary answer | `stuck-flip-build-plan-merge.md:64` (§3.1) | the car rights **in place with thrusters**; `CHALLENGE_RESET_VEHICLE` is the fallback, not the mechanism |

### 2.3 The reconciled plan

| part | value / member | label |
|---|---|---|
| the timer pair | `BatmobileStuckTimeMax` **2.0** (7452), `BatmobileStuckTimeFlip` **0.5** (7456); accumulator `BatmobileStuckTime` 0x1d18 has **no tag** | decoded values — `CLASS_DEFAULTS.md:287–288`; unit **seconds is derived**, not annotated; accumulator value **UNKNOWN** |
| the only decoded consumer | `0x140063e90`: mode change refused beyond **135°** off upright, and beyond **45°** unless `BatmobileStuckTimeFlip < BatmobileStuckTime`; constants ±0.707 | decoded — `PAWNMESH_D8.md:10`, `:61–62` |
| **closest JC3 system** | the interaction-graph **`CInteractionGraphParentIsUpRightCondition`** as the gate, plus **`EngineTurboJump`** as the plume | decoded |
| what pushes the car over | `FlipVehicle` = `AddTorqueOverTime` + `AddKeepyUpForce` (literals **1000.0** / **2.0**) | decoded (BmAK body) / derived literals |
| the nearest torque member | `DriverLean.righting_torque` **1500…4000 (med 3000, n=23)** — **0 cars**, 18 bikes + 5 boats | decoded — `VOCABULARY.md:566`, `card-T-10.md` A4 |
| the lift member | `turbo_jump.punch_speed_kph` **50…60**, `punch_delay_time` **0…0.1**, `up_multiplier` **12…25** (n=35) | decoded — `VOCABULARY.md:357–358` |
| the stay-upright path | `RB_StayUprightSetup` → **2 bytes, 0 tags**: no serialised tuning | decoded — `COLLISION_WHERE.md:130` |
| **gap** | **no roll torque on a car**: JC3 has the trigger and the lift, and no member that turns a car about its long axis | decoded absence |
| **build step** | graph node gated on upright **0.707** (45°), rest **0.5 s**, give up **2.0 s**; `turbo_jump` **50 / 0.0 / 12**; fire the **`EngineTurboJump`** usage on the thruster part; probe `DriverLean.righting_torque` 3000 (accepts → data; refuses → 230,300 N·m for 0.5 s hook); `CHALLENGE_RESET_VEHICLE` after 2.0 s as fallback | decoded values, chosen use |

**Pilot:** nothing fires before **0.5 s** of rest; thrusters fire; wheels-down by **2.0 s**; settles
within **10°** of vertical (0.985) and ~0 rad/s residual roll; same card on the side case must not roll
past vertical onto the other flank.

---

## 3. Health runs to zero, the car explodes, no crash damage

**Operator fact:** no visible damage stages; **crashes never damage, scratch or dent** it; the bar
falls to zero from **weapon** damage; then it **explodes violently and kills the passengers**; it does
**not** remain a drivable wreck.

### 3.1 What survives

| survives | value | source |
|---|---|---|
| BmAK's hit-point model | `Pawn.Health` **1200** on all 3 archetypes; `ArmourLevels` **`[0, 300, 600, 900, 1200]`** | decoded — `DAMAGE_RULES.md` §4, `CLASS_DEFAULTS.md:143` |
| the JC3 landing model | `smoke_threshold` / `burn_threshold` / `explosion_threshold` + `explosion_delay_s` + `deform_scale` | decoded — `VOCABULARY.md`, `DAMAGE_MODEL.md` |
| collision is already off in the build | `impact_damage_factor` **0** (fleet 1…12), `deform_scale` **0** (fleet 1…2) | decoded build values — `DAMAGE_MODEL.md` §2, §7 |
| the death blast | root `CForcePulse` → `car_explosion_medium.ftune`: `PlayerDamage` **500** / `PlayerDamageRadius` **5 m**, AI the same, radius factors **0/0** | decoded — `FORCEPULSE.md` §3 (identical in all 115 carriers) |
| blast placement | pulse sits at the entity origin — **292 of 307** pulses | decoded — `FORCEPULSE.md` §2 |
| wrecks are scenery, not a car state | `bus_wreck.ee`, `tank_wreck.ee`, … 11 entities under `world_at_war/encounters/ambient/` | decoded — `STANDALONE.json`, `REBELDROP.md:142` |

### 3.2 What the observation overturns — named

| # | old claim | where | why it dies |
|---|---|---|---|
| H-O1 | **"the visible damage stages BmAK proves"** — a staged ladder (intact → smoke at 1050 → burn at 250 → explosion) mapped by health fraction | `health-damage-states-plan.md:125` (§2) and §6's fraction mapping | the operator: **no visible damage stages**. The thresholds stay in the file but the build targets **no smoke, no fire** on the player car |
| H-O2 | **panel damage / deformation on the player car** — per-part health, `deform_scale`, `mshswap` alternates, "scratch and dent" reproduction | `armour-plates-and-deformation-plan.md` §2.2, §3, §4 | the operator: crashes never scratch or dent. BmAK's own "panel damage" is a **texture-mask look with no per-panel mesh** (`armour-plates-and-deformation-plan.md:74`, `:96–98`), so there is nothing to port even if it were wanted |
| H-O3 | the wreck/fire continuation (`burn_duration_s` 20, burning car) as the death state | `health-damage-states-plan.md` §2, §4 | the operator: it **explodes and is gone**; no drivable hulk, no lingering fire on the player car |

### 3.3 The reconciled plan

| part | value / member | label |
|---|---|---|
| **closest JC3 system** | the vehicle root's **`CForcePulse` + `car_explosion_medium.ftune`** as the death blast; `VehicleDamage`'s collision multiplier as the off-switch | decoded |
| what must **not** change | `invulnerable` **0**, `max_health` **2000**, channels `bullet` 5000@99 / `bullet_heavy` 5@20 / `explosion` 250@50, `part_damage_types[]` unchanged | decoded build values |
| the "no damage stages" probe | `smoke_threshold` **0** → fallback **200** (in-domain min 200…1050); `burn_threshold` **0** → fallback **50** (min 50…250) | decoded values, **semantics UNKNOWN** (health-remaining vs per-hit) |
| explosion timing | `explosion_threshold` **4000** kept (fleet 500…4000); `explosion_delay_s` **8** kept (fleet 5…10); only if HP 0 does not explode: **1** / **1** | decoded values, semantics UNKNOWN |
| occupant kill | seated at `point.driver` **(−0.44, 0.34, 0.20)** inside a **5 m** radius → receives **500**; is 500 ≥ player health? | geometry **derived**; player-health value **UNKNOWN** |
| health bar | JC3's decoded vehicle HUD has **no health element** (`JC3_HUD_WEAPONS.md`, 0 hits) | decoded absence — the bar is carried by our own `hud.gfx` work (`hud-radar-dash-plans-v2.md`), not by a JC3 member |
| **gap** | the HUD bar's carrier (JC3 side), the pulse's presence in the Batmobile's own `.ee`, and the blast's firing instant | UNKNOWN, §5 |
| **build step** | (a) verify `CForcePulse` + `car_explosion_medium` survived into the Batmobile `.ee` (`jc3forcepulse.py` dump) — present → touch no threshold; (b) probe `smoke_threshold`/`burn_threshold` 0 with the 200/50 fallback; (c) do **not** wire a destroyed-mesh `mshswap` | decoded members, probe-gated |

**Pilot:** seven full-boost rams (wall ×3, traffic ×3, flatbed ×1) → health read identical, **Δ = 0**,
no smoke/fire/dent, still drivable; then tank shell / RPG / 200 rifle rounds → bar moves, reaches 0,
explosion within **0–1 s**, seated player dead within **1 s**, **no drivable wreck**, a pedestrian at
**≤ 5 m** dies and one at **≥ 8 m** does not.

---

## 4. Remote control (static 100 → 150 m) and LB homing

**Operator fact:** remote control needs Batman standing still with the gadget; the driving is identical
to normal apart from a **static overlay** that begins around **100 m**; at **150 m** the car cannot move
further; the car is **empty**. **LB** makes the car drive itself to the player.

### 4.1 What survives

| survives | value | source |
|---|---|---|
| BmAK's remote numbers | `JammingRange` **10000.0 cm = 100 m**, `JammerTime` 1.5 s, cursor 3.0 / 5.0 / 10.0, return 2.0 / 2.0 s, `MaxAimX` 0.9 | decoded — `GADGET_PARAMS.md:51–59`, `:246` |
| the mode is one native bit | `bRemoteDrive` = bit **0x1000000** of `[+0x11d8]`, **one** writer in `.text` | decoded — `CONTROLS_NATIVE2.md:35`, `:69` |
| the autonomous tune | `CarAI.Limit_Speed.y_max` **35**, `.y_min` **5**, `Input_Speed.x_max` **15**, `Input_Turn.x_max` **0.5** | decoded — `VOCABULARY.md` §`CarAI`, `remote-and-autonomous-drive-plan.md` §3.2 |
| the gadget-as-data pattern | `entry.use_item` → `S_STUNT_USE_ITEM_VEHICLE`, `trigger.use_item` box, prompt string | decoded — `EMP.md:80–82` |
| the 100 m is a *gadget float*, not a world range | — | decoded |

### 4.2 What the observation overturns — named

| # | old claim | where | why it dies |
|---|---|---|---|
| R-O1 | **"destination / route over a road network — 0 members"** ⇒ homing has no carrier | `remote-and-autonomous-drive-plan.md:212` (§3.3) | true of *members*, wrong about *files*: `ai/bts/01_micro_behaviors/vehicle/car_drive_to_point.btc` **80,366 B** ships, one of **26** vehicle micro-behaviours (`INDEX.jsonl:30–55`, line 36) |
| R-O2 | **LB is available as the homing key** | implied by `remote-and-autonomous-drive-plan.md` §3.1–§3.2 (button unspecified) and the operator's "LB" | **LB is spent**: `LSHOULDER → EXIT_VEHICLE` is the exit binding in `controls-entry-exit-eject-plans-v2.md` row 5. One button cannot both leave the car and call it |
| R-O3 | the remote *cursor* drive is a buildable mode ("code bridge, plus a keymap rebind") | `remote-and-autonomous-drive-plan.md:215` | there is nothing to rebind: the land-vehicle action set has **no aim/stick/cursor action** (`INPUT.md:223`), there is no 2D vehicle stick (`DRIVE_CARRIERS.md` §4), and the gadget route is a **proximity** interaction with **0 range/radius/distance members** (`HACKABLES.md:32`) |

### 4.3 The reconciled plan

| part | verdict | basis |
|---|---|---|
| **remote control** | **HALTED** | no input carrier (§4.2 R-O3); BmAK's mode is a native bit with one writer; `JammingRange` is a gadget float |
| **static overlay 100 → 150 m** | **HALTED** | 0 hits for `static`/`noise`/`jam`/`overlay`/`fullscreen` in the only decoded vehicle-HUD element table; the only size parameter is `reticle_size` **5…30 px** (`JC3_HUD_WEAPONS.md` §7) |
| **hard limit at 150 m** | **HALTED** | needs a distance-to-player read; no vehicle, HUD or interaction member carries one (`HACKABLES.md:32`; traffic rules carry tag selectors, not distances) |
| **homing** | **BUILD, partial, probe-gated** | carrier: `car_drive_to_point.btc`; tune: `CarAI` HOM-1…HOM-5; **trigger** must not be LB |
| **closest JC3 system** | the shipped vehicle micro-behaviour tree + the entity's own `…_land_global_ai.vmodc` | decoded files, **`.btc` body UNKNOWN** (`traffic-ai-claims-audit.md` U4) |
| **gap** | whether a mod can bind a `.btc` tree to a **specific** vehicle instance (trees are named by province-wide `global.blo` rules), and whether the tree takes a **target point** | UNKNOWN, §5 |

### 4.4 The written reason: why remote and homing are halted while the project uses Rebel Drop

This is the reason to write down, and it is not "JC3 can't":

1. **The car's arrival is already a Rebel Drop item, in this build.** `profile/item.onlinec` holds an
   `Item` whose **`Name` is the 32-bit Jenkins hash of the entity leaf** — that hash *is* the spawn
   binding (`REBELDROP.md:3`, `:57`) — and `bm_rc4.py:69–72` ships `profile/item.onlinec`,
   `profile/onlinec`/`task.onlinec`, `online.stringlookup`, `settings/spawn_vehicle_defs.bin` and the
   vehicle icon from `bm-RC4-rebel`. The mod's own added entries carry `RebelDropTimer` **0**
   (`REBELDROP.md:67`), so the drop is available on demand.
2. **A homing drive is a second arrival path for the same entity.** The drop **spawns a fresh copy**
   at the player's chosen drop point; homing **drives an existing instance** to the player. Nothing in
   the data arbitrates which instance is "the Batmobile": two can coexist (one dropped, one driven),
   and the only debounce in data is `RebelDropTimer` — a property of the drop, not of the drive.
3. **The homing trigger has no free button.** LB is exit (§4.2 R-O2). The remaining candidates are
   `USE_VEHICLE_MOD` (RPADRIGHT) or `USE_ITEM` (RPADUP), both already allocated in
   `controls-entry-exit-eject-plans-v2.md` (afterburner / weapon slot 4).
4. **The remote half has neither input nor output.** No input carrier (§4.3), and the overlay that
   makes remote *feel* like remote has no HUD element and no distance read.

**Therefore:** keep **Rebel Drop as the summon** (data, shipped, no AI binding needed), **halt remote
control and the overlay/limit outright**, and hold homing at the probe gate — if `car_drive_to_point.btc`
proves a per-entity binding **and** a target parameter, homing may be built **on its own key**, with
the drop explicitly designated as the other, separate route. Until then, "LB sends the car to the
player" is answered by the drop item, not by a drive.

**If homing is un-halted, the build is:** `CarAI` 35 / 5 / 15 / 0.5; `Limit_IsLargeVehicle` 0 then 1
(the car is 4.69 m wide in battle); tree reference `car_drive_to_point.btc`; trigger on a free key,
never LB. Fallback if the probe fails: `Item` `RebelDropTimer` 1800 or 0 (`REBELDROP.md:67`).

**Pilot (if un-halted):** car 30 m away on a clear road → moves within **1 s**, arrives within **5 m**
in **≤ 15 s** at **≤ 35**, overshoot **≤ 2 m**, no clip/stall, pressing again is idempotent.

---

## 5. UNKNOWN register — each with its settler

| # | UNKNOWN | settles with |
|---|---|---|
| U1 | what BmAK does when `BatmobileHitWater` is set, and where "land" is | the flag's consumer in `BatmanAK.exe`; no destination member exists |
| U2 | who consumes `CHALLENGE_RESET_VEHICLE`, and its destination rule | the graph binding the action (`INPUT.json` gives the binding only), or a vanilla `P` press on a flipped car |
| U3 | `sinking_progress` / `is_safe_to_teleport` type, range, writer | the executable's variable table (`EMP_DISABLE.json` holds names + addresses) |
| U4 | the unit of `vehicle_damage.*_water_entry_ms` (10/20/20/50) | the water-entry consumer in `JustCause3.exe` |
| U5 | the unit of `BatmobileStuckTimeMax` 2.0 / `Flip` 0.5 (seconds is **derived**) | the `.g.cs` doc (none) or a live read of the accumulator's rate |
| U6 | `BatmobileStuckTime` (0x1d18) and `NumFlipTries` (7460) runtime values | native constructor, or a live property dump |
| U7 | which `Exhaust.*` object a shipped flip plays (CDO vs archetype conflict) | `Playable_Batmobile_SF.upk` re-read |
| U8 | whether a `CCar` accepts `DriverLean` (`righting_torque` 3000) | one build + the module loader |
| U9 | the health bar's JC3-side carrier | the vehicle HUD movie / `hud_code` module list — **not** `JC3_HUD_WEAPONS.md` (0 hits) |
| U10 | is the Batmobile's own `.ee` carrying `CForcePulse` + `car_explosion_medium` | its graph dump via `jc3forcepulse.py` |
| U11 | the player's health value (is 500 enough to kill the occupant) | the player `CPawn` module — not decoded in this repo |
| U12 | `explosion_threshold` / `smoke_threshold` / `burn_threshold` semantics | `DAMAGE_MODEL.md` step 7; probes |
| U13 | whether a mod can bind `car_drive_to_point.btc` to one vehicle, and whether it takes a target point | the `.btc` body + `…_land_global_ai.vmodc` fields (`traffic-ai-claims-audit.md` U4) |
| U14 | BmAK's remote boundary value (`GetDistanceToRemoteControlBoundary`) | the native body / a runtime sample |

---

## 6. Checks run for this page

| check | result |
|---|---|
| older plans re-read for the claims named | 7 files: headings + the specific overturn lines (`water-and-terrain-handling-plan.md:209–226`, `water-crossing-batmobile-build-plan.md:125`, `stuck-flip-recovery-plan.md:47`, `:212`, `stuck-flip-build-plan-merge.md:64`, `health-damage-states-plan.md:125`, `armour-plates-and-deformation-plan.md:74`, `remote-and-autonomous-drive-plan.md:206–232`) |
| fresh plans re-read | the 4 reports named in the header, in full |
| every number labelled | decoded / derived / chosen / UNKNOWN; the three "seconds" readings (stuck timer, dwell, cooldown) are labelled derived/chosen, not decoded |
| the Rebel Drop reason | traced to `REBELDROP.md:3`, `:57`, `:67` and `bm_rc4.py:69–72`; the cross-conflict with LB-exit traced to `controls-entry-exit-eject-plans-v2.md` row 5 |
| contradictions kept, not smoothed | `BattleModeUprightTorqueFactor` 2000 vs unset; `SideExhaust` CDO vs archetype; both already recorded in the fresh flip plan |
| files written | this page only |
| game launched / data or build written | **no** |

Revert: delete this file. No plan, module, `.epe`, HUD or build was modified.
