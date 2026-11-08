# Remote control and homing — buildable, or halted with a written reason

**Scope.** Two driverless functions in the operator's 2026-11-08 facts, decided against the JC3 files:
whether each can be **built** from JC3 systems or must be **halted**, and what the nearest JC3 mechanism
and values are. Plus the static overlay that grows from 100 m to 150 m and the hard limit at 150 m.

**The operator's facts, as given:**

- **Remote control** — Batman must **stand still** and use the gadget. The driving is **identical to
  normal** apart from a **static overlay** on the view. The static **begins around 100 m**, and at
  **150 m the car cannot move further**. The car is **empty** while driven.
- **Homing** — pressing **LB** makes the car **drive itself to the player**.

**Verdicts, up front.**

| function | verdict | one line |
|---|---|---|
| **Remote control** (drive the empty car from a gadget) | **HALTED** | the gadget half exists (`entry.use_item`), the *driving* half has no carrier — and the gadget route that does exist is a **proximity** interaction with **0 range members**, so "stand 100 m away" is the exact thing JC3 cannot express |
| **Homing** (LB calls the car, it drives to you) | **BUILD, partial, probe-gated** | the destination carrier the earlier plan reported missing **does ship**: `ai/bts/01_micro_behaviors/vehicle/car_drive_to_point.btc`, 80,366 B, one of 26 vehicle micro-behaviours |
| **Static overlay 100 → 150 m** | **HALTED** | **0 hits** for a static / noise / full-screen overlay in the only decoded vehicle-HUD file; the only size parameter in the HUD API is the **reticle size (5…30 px)**, not a view effect |
| **Hard limit at 150 m** | **HALTED** | stopping a car by distance needs a distance read, and no JC3 vehicle, HUD or rule object carries one |

Each halt is written as an accept-or-reject item in §6, with the reason and what would un-halt it.

**Evidence levels:** *decoded* (read from the file at the line/member cited), *derived* (arithmetic or
mapping over decoded values), *UNKNOWN* (searched and absent, settler named).

---

## 1. Evidence base

| source | what it gave |
|---|---|
| `tmp/freebuff/reports/remote-and-autonomous-drive-plan.md` | BmAK's two systems and every decoded value; the `CarAI` tune; **its §3.3 "destination / route = 0 members" claim, which §5 below corrects** |
| `Research/BatmobileGrab/GADGET_PARAMS.md` §2, lines 51-59, 246 | `RBatmobileRemoteBm` — `JammingRange` **10000.0**, `JammerTime` 1.5, cursor 3.0/5.0/10.0/2.0/2.0 s/0.9 |
| `Research/BatmobileGrab/CONTROLS_NATIVE2.md` lines 35-39, 69 | `bRemoteDrive` = bit **0x1000000** of the `0x11d8` word; **one** writer in `.text` |
| `Research/JC3Grab/INDEX.jsonl` lines 30-55 | **26** `ai/bts/01_micro_behaviors/vehicle/*.btc`, incl. `car_drive_to_point.btc` line 36 |
| `tmp/freebuff/reports/traffic-ai-claims-audit.md` C14, C40, U4 | the tree count and directory correction; the `…_land_global_ai.vmodc` AI module; the bodies are UNKNOWN |
| `Research/JC3Grab/TRAFFIC.md` §3, §6 | `global.blo`: 31 rules, 41 selectors, **10** `.bts` paths; the entity ships its own AI module |
| `Research/JC3Grab/DRIVE_CARRIERS.md` §4, §6.2 | no 2D vehicle stick, no per-wheel drive path; `USE_ITEM` = RPADUP / E |
| `Research/JC3Grab/INPUT.md` line 195-223 | the land-vehicle action set — **no aim / stick / cursor action** |
| `Research/JC3Grab/EMP.md` §80-86, 192; `FORCEPULSE.md` §4.3 | `entry.use_item` → `S_STUNT_USE_ITEM_VEHICLE`, `trigger.use_item` box, prompt `ui_activate_emp` — the gadget-as-data mechanism |
| `Research/JC3Grab/HACKABLES.md` lines 30-32, 103 | the interaction graph carries **no range, radius or distance member** |
| `Research/JC3Grab/JC3_HUD_WEAPONS.md` §7 (lines 170-199) | the vehicle HUD element table: slots, reticle (14 shapes, size 5…30 px), cooldown 0..1, lock-on POI, `MCI_missile_locked` 0.5 s flash |
| `Research/JC3Grab/REBELDROP.md` §4, §7 | the item recipe and the leaf-hash binding — the "deliver the car" route |

---

## 2. What BmAK does, so the target is on the record

| member | value | evidence |
|---|---:|---|
| `RBatmobileRemoteBm.JammingRange` | **10000.0** cm = **100 m** | `GADGET_PARAMS.md:58` |
| `JammerTime` | 1.5 s | `:52`-range rows |
| `CursorSpeed` / `CursorAccel` / `CursorDecel` | 3.0 / 5.0 / 10.0 | `:55`, `:54`, `:53` |
| `CursorReturnFactor` / `CursorReturnDelay` | 2.0 / 2.0 s | `:51`, `:52` |
| `MaxAimX` | 0.9 | `GADGET_PARAMS.md` row list |
| `bRemoteDrive` | bit **0x1000000** of `[+0x11d8]` | `CONTROLS_NATIVE2.md:35`, `:69` |
| `GetDistanceToRemoteControlBoundary`, `BatmobileOutOfRemoteRange`, `DrivingModeTimeRemoteBatmobileOutOfRange` | the range gate + a thought timer | plan §1.2 |

Two things follow, and they matter for the decision: the remote mode is **one native bit with one
writer in the executable**, and the 100 m is a **gadget float**, not a world-system range. Both are code,
not entity data. The operator's 150 m hard stop is a second, separate boundary —
`GetDistanceToRemoteControlBoundary`'s numeric value is **UNKNOWN** (plan U4), so 100 and 150 are two
different numbers in BmAK and neither is serialised as entity data here.

---

## 3. Remote control — **HALTED**

### 3.1 What JC3 does carry

| piece | JC3 carrier | evidence | fits? |
|---|---|---|---|
| stand still, use a gadget | `CInteractionGraphEntry` `entry.use_item` → state `S_STUNT_USE_ITEM_VEHICLE`, `CInteractionTrigger` box, prompt string | `EMP.md` §80-86 on the flatbed; `FORCEPULSE.md` §4.3 | **yes** — the "press a gadget while stationary" half is a solved pattern |
| the gadget being *the car's* controller | — | 0 members in 232 decoded vehicle graphs; `INPUT.md:223` land-vehicle actions are `ACCELERATE, CHALLENGE_RESET_VEHICLE, ENTER_VEHICLE, EXIT_VEHICLE, FIRE_VEHICLE_WEAPON_PRIMARY/SECONDARY, HANDBRAKE, PRECISION_AIM, REVERSE, SOUND_HORN_SIREN, TURN_LEFT, TURN_RIGHT, USE_ITEM, USE_VEHICLE_MOD, VEHICLE_CAM, VEHICLE_RELEASE_GRAPPLE` | **no** |
| aiming a cursor from 100 m | — | `DRIVE_CARRIERS.md` §4: **no 2D vehicle stick action**, no per-wheel drive; `INPUT.md` has no aim action for a vehicle | **no** |
| firing the drive from a distance | `CInteractionTrigger` boxes | `HACKABLES.md:32`, `:103`: **no range, radius or distance member** on any interaction object — the player must be *at* the object | **no** |

### 3.2 The written reason (for §6, item R-1)

> **Remote control is halted because the control input has no carrier in JC3's data.** Driving in JC3 is
> the occupant controller's input: the land-vehicle action set (`INPUT.md:223`) has no aim, stick or
> cursor action, and `DRIVE_CARRIERS.md` §4 records no 2D vehicle stick and no per-wheel drive path. The
> one gadget-as-data mechanism JC3 has — `entry.use_item` → `S_STUNT_USE_ITEM_VEHICLE` (`EMP.md` §80-86)
> — is a **proximity** interaction: the interaction graph carries **no range, radius or distance member**
> (`HACKABLES.md:32`), so it cannot be fired from 100 m. BmAK's own mode is a single native bit
> (`bRemoteDrive` 0x1000000, **one** writer in `.text`, `CONTROLS_NATIVE2.md:69`) with the range held in a
> gadget float (`JammingRange` 10000.0). Rebuilding it needs an engine-side input route, which this
> project's rules exclude.

### 3.3 What is still shippable from this half

The **gadget itself**, with no driving: a `USE_ITEM` (RPADUP / E, `INPUT.md:195`) binding on the car's
interaction graph, a prompt string, and one state. That is the same shape as the EMP flatbed and costs
one interaction-graph copy. It buys the *animation and the button*, not the *function* — so it should only
be built if a different behaviour is hung on it.

---

## 4. Homing — **BUILD, partial, probe-gated**

### 4.1 The carrier that does ship

The earlier plan (`remote-and-autonomous-drive-plan.md` §3.3) records "destination / route over a road
network — **0 members**". That is true of **members** and wrong about **files**: the index carries a
whole directory of shipped vehicle micro-behaviours, and one of them is exactly the behaviour the
operator describes.

| tree | size | what it is |
|---|---:|---|
| **`ai/bts/01_micro_behaviors/vehicle/car_drive_to_point.btc`** | **80,366 B** | the car drives to a point |
| `car_follow_target.btc` | — | the car follows a moving target |
| `car_point_to_point_patroller.btc` | — | patrol between points |
| `car_drive_on_spline.btc` | — | drive a fixed spline |
| `external_behavior_with_never_exit.btc` | — | an externally driven behaviour that does not release |
| `exit_vehicle.btc` | — | the exit leg |

Count: **26** files under `ai/bts/01_micro_behaviors/vehicle/` (`INDEX.jsonl:30-55`; the directory
correction is `traffic-ai-claims-audit.md` C14). `car_drive_to_point.btc` is at `INDEX.jsonl:36`,
`patch_win64/game0`.

**Why this is the right tree and not `car_follow_target`:** the operator's LB does not follow a moving
player continuously — it makes the car come to the player. "Drive to a point" is the smaller behaviour and
the one whose name states the goal; follow-target is the fallback if a player who keeps moving is
required.

The rest of the stack exists too:

| piece | carrier | evidence |
|---|---|---|
| the car's AI module | the entity ships `…_land_global_ai.vmodc` in its own `modules/` tree | `TRAFFIC.md:138` |
| throttle / steer curves | `CarAI` — 25 members, **3 builds / 3 instances** | plan §3.2, `VOCABULARY.md` §`CarAI` |
| an owner to sit in | a `Driver` seat; `global.blo` pairs each rule with a `Driver` seat **and** a tree | `TRAFFIC.md:105` |

### 4.2 Values to write

| # | member | write | why |
|---|---|---:|---|
| HOM-1 | `CarAI.Limit_Speed.y_max` | **35** | the donor's ceiling (fleet 22…45); BmAK's own autonomous ceiling is UNKNOWN, so the fleet number is the only defensible one |
| HOM-2 | `CarAI.Limit_Speed.y_min` | **5** | donor |
| HOM-3 | `CarAI.Input_Speed.x_max` | **15** | donor (fleet 12…25) |
| HOM-4 | `CarAI.Input_Turn.x_max` | **0.5** | donor |
| HOM-5 | `CarAI.Limit_IsLargeVehicle` | **0**, then **1** if it clips spans | the Batmobile is 4.69 m wide in battle (`POSES.md`, quoted in the plan) |
| HOM-6 | the tree reference | `ai/bts/01_micro_behaviors/vehicle/car_drive_to_point.btc` | the shipped behaviour |
| HOM-7 | `Item.RebelDropTimer` | **1800** (or 0) | only if the fallback in §4.4 is used |

### 4.3 The three things that are still UNKNOWN — and the probe that decides

| # | unknown | settler |
|---|---|---|
| H1 | whether a **mod** can bind a `.btc` micro-behaviour to a specific vehicle instance at runtime (trees are named by the **global** `global.blo` rules, which are province-wide and tag-matched) | `global.blo` rule layout + the entity's AI module: does the module carry a tree name, or only curves? |
| H2 | what "the point" is — the player's position is a **target**, and no vehicle member names a target (the tree takes it from its owner, or from a level `CVehicleRule`) | `car_drive_to_point.btc`'s parameter list (the `.btc` body is **undecoded**, audit U4) |
| H3 | the **trigger** — LB. JC3 has no `LB`-style vehicle action outside the occupant set; the nearest is `USE_VEHICLE_MOD` (RPADRIGHT/MOUSE3) or `USE_ITEM` (RPADUP/E) | `INPUT.md:195-196`; the binding is a keymap edit either way |

**The 5-minute probe, before any build:** unpack `car_drive_to_point.btc`, list its node names and its
parameter slots; read the entity's `…_land_global_ai.vmodc` for a tree-name field. Two reads decide H1 and
H2 with no game launch.
- **If the module carries a tree name and the tree takes a target:** build HOM-1…HOM-6 + the keymap
  binding. The behaviour is "press a button, the car drives to you".
- **If the module carries only curves:** homing goes to §6 item R-2 as a second halt, for the reason
  "the tree is bound by a global rule, not by the entity".

### 4.4 The data-only fallback if the probe fails

Rebel Drop: the car is **delivered** near the player instead of driving to him (`profile/item.onlinec`,
one `Item` whose `Name` is the Jenkins hash of the entity leaf — `REBELDROP.md` §4, §7). That is a
different fiction ("called in", not "homing"), and it is the only route that needs no AI binding at all.

---

## 5. The static overlay, 100 → 150 m — **HALTED**

### 5.1 What the JC3 vehicle HUD actually has

`JC3_HUD_WEAPONS.md` §7 is the only decoded vehicle-HUD element table in the repository. Its complete
element list, with the parameters the movie accepts:

| element | parameter | range |
|---|---|---|
| weapon slots | `InitVehicleWeapons(slot_index 0..1)` | 2 slots |
| reticle | `UpdateWeaponReticle(show, look, reticle_size, reticle_shape)` | **14 shapes**, 5 look states, **size 5…30 px** |
| cannon cooldown | `SetCooldownRotation` | 0..1 → 360° |
| lock-on | `POI_TYPE_LOCK_ON_TARGET` 21, rotates 1.5 s | one icon |
| incoming missile | `ShowMissileLocked` / `HideMissileLocked` | flashes at **0.5 s** |

A case-insensitive search of that file for `static`, `noise`, `jam`, `overlay`, `fullscreen` returns
**0 hits**. The only "size" parameter in the whole API is `reticle_size` (5…30 px), and it sizes the
**reticle**, not the view.

### 5.2 The written reason (for §6, item R-3)

> **The static overlay and its 100 → 150 m gradient are halted because neither half exists in the decoded
> HUD.** There is no static, noise, jam or full-screen overlay element in `JC3_HUD_WEAPONS.md` §7 (0 hits
> for those names); the only size parameter the vehicle HUD accepts is `reticle_size` 5…30 px, which sizes
> the aiming reticle, not the view. A gradient also needs a distance read, and no JC3 vehicle, HUD or
> interaction object carries a distance-to-player member (`HACKABLES.md:32`; the traffic rules carry tag
> selectors, not distances). The HUD itself is `hud.gfx`, a GFx movie: the project decodes its API but has
> no authored-movie path, so adding an element is a new asset pipeline, not a value.

### 5.3 What can be done instead, honestly

| option | carrier | what it gives | what it is not |
|---|---|---|---|
| reticle grows with distance | `UpdateWeaponReticle` `reticle_size` 5…30 px | a visible size cue | a *reticle* change, not a static view effect; and still needs the distance read (HALT R-4) |
| warning flash | `ShowMissileLocked`, 0.5 s flash | the nearest shipped "signal" cue | triggered by a missile lock, not by distance |
| full-screen `.effc` | `effects/jc_*` packages | a screen-space effect | `.effc` is world-space particle data; no HUD-space emitter is decoded — **UNKNOWN** |

None of these reproduces "static that thickens on the view". They are listed so the operator can choose a
substitute, not presented as the feature.

---

## 6. Halt register — accept or reject

| # | item | reason | what would un-halt it | if accepted |
|---|---|---|---|---|
| **R-1** | **Remote control** (stand still, gadget, drive the empty car) | no input carrier: land-vehicle actions have no aim/stick action (`INPUT.md:223`), no 2D vehicle stick (`DRIVE_CARRIERS.md` §4); the gadget route is a proximity interaction with **0 range members** (`HACKABLES.md:32`); BmAK's mode is one native bit with one writer (`CONTROLS_NATIVE2.md:69`) | an engine-side input route (excluded by project rules) | the car stays occupant-driven; the gadget may exist as animation only (§3.3) |
| **R-2** | **Homing**, *only if probe H1/H2 fails* | the tree is bound by `global.blo`'s province-wide rules; no entity member names a tree or a target | a `.btc` parameter list + an AI-module tree field proving a per-entity binding | Rebel Drop re-delivery (§4.4) — the car appears near the player |
| **R-3** | **Static overlay 100 → 150 m** | 0 hits for static/noise/overlay in the decoded vehicle HUD; only `reticle_size` 5…30 px exists; no distance member anywhere | an authored `hud.gfx` element + a distance source | the reticle-growth or warning-flash substitute (§5.3) |
| **R-4** | **Hard limit at 150 m** (the car cannot move further) | needs the same distance read as R-3, plus a way to stop a car by radius; neither exists. BmAK's boundary is `GetDistanceToRemoteControlBoundary`, whose value is **UNKNOWN** (plan U4) | same as R-3 | nothing: with R-1 halted there is no remote drive to limit |

**Rejecting R-1** means building the engine-side input route, which the project's rules exclude; rejecting
R-3/R-4 means authoring HUD content, which the project has never shipped. Both are the operator's call, and
the reasons above are the whole of the case.

---

## 7. What the build actually changes

| # | file | change | revert |
|---|---|---|---|
| 1 | private entity `.ee` — the `CarAI` module instance | HOM-1…HOM-5 values | rebuild from the build manifest |
| 2 | private entity `.ee` — `…_land_global_ai.vmodc` | HOM-6 tree reference, **only if probe H2 passes** | same |
| 3 | keymap — the `USE_VEHICLE_MOD` / `USE_ITEM` binding | the trigger for HOM-6 | restore the layer |
| — | `hud.gfx` | **no edit** (R-3 halted) | n/a |
| — | the interaction graph | **no edit** unless §3.3 is chosen | n/a |

---

## 8. Pilot cards

### PR-1 — remote at 100 m: the static begins

*(Runnable only if R-1 is un-halted. Written now so the halt has a measurable alternative.)*

**Do:** park the car, walk Batman to **exactly 100 m**, use the gadget, drive forward.

**Pass band:** the car moves with the stick **identically to normal** (same top speed within **±5 %**,
same steering response); the static overlay is **present and light** at 100 m and **visibly denser** at
125 m; **nothing else** on the HUD changes; the car is **empty** (no driver pose, no occupant).
**Fail:** no static at 100 m, static at 90 m, or any change in the driving feel.

### PR-2 — remote at 150 m: the car stops

**Do:** keep driving until the distance reads **150 m**, then hold forward for 5 s.

**Pass band:** the car makes **no further ground** (position change **≤ 1 m** over the 5 s) while the
input is still held; the static is **at its densest**; at **149 m** the car still drives (a **1 m**
hysteresis band, so the limit is a distance and not a timer); releasing the gadget returns control with
**no** residual motion. **Fail:** the car creeps past 150 m, or the stop is a timer (it stops at the same
*time* from different distances).

### PR-3 — homing (the buildable one)

**Do:** stand still, press the bound button with the car **30 m** away and a clear road.

**Pass band:** the car starts moving within **1 s**, arrives within **5 m** of Batman within **15 s** at
**≤ 35** (`Limit_Speed.y_max`), stops without overshooting more than **2 m**, and does not clip or stall on
a span; pressing the button again while it is en route is **idempotent** (no second car, no reset).
**Fail:** it does not move (H1 failed), it drives past (H2 failed), or it drives but never stops.

---

## 9. UNKNOWN register

| # | unknown | settler |
|---|---|---|
| U1 | whether a mod can bind a `.btc` tree to a vehicle instance (H1) | `global.blo` rule layout + the entity's `…_land_global_ai.vmodc` fields |
| U2 | `car_drive_to_point.btc`'s parameters, incl. whether it takes a target point (H2) | the `.btc` body — undecoded (`traffic-ai-claims-audit.md` U4) |
| U3 | whether the micro-behaviour set is reachable from a player vehicle at all | probe PR-3 |
| U4 | BmAK's remote boundary value (`GetDistanceToRemoteControlBoundary`) and the out-of-range grace timer | the native body / a runtime sample (plan U4, U5) |
| U5 | whether the HUD can host a new element at all | `hud.gfx` import/export tooling — the project has decoded the API, never authored the movie |
| U6 | whether any `.effc` can render in HUD space | `.effc` decode: no HUD-space emitter found so far |
| U7 | which three builds carry `CarAI` | plan U6 (counts decoded 3/3, names not) |

---

## 10. Change record

- **Intended change:** none to game data. This document decides build vs halt for two functions.
- **File written:** `tmp/freebuff/reports/remote-control-range-static-overlay-plan.md`.
- **Why this file:** the request names it as the deliverable.
- **Revert:** delete the file. No other file was touched.

## 11. Checks run

| # | check | result |
|---|---|---|
| 1 | `remote-and-autonomous-drive-plan.md` §1-§3 | every BmAK value re-quoted with its file; its §3.3 "0 destination members" claim re-tested and **corrected in §4** |
| 2 | `INDEX.jsonl` lines 30-55 | **26** vehicle micro-behaviours; `car_drive_to_point.btc` 80,366 B at line 36 |
| 3 | `traffic-ai-claims-audit.md` C14, C40, U4 | the directory correction and "bodies undecoded" both used, not overridden |
| 4 | `TRAFFIC.md:105`, `:138` | 10 `.bts` paths in `global.blo`; the entity's own `…_land_global_ai.vmodc` |
| 5 | `INPUT.md:195-196`, `:223` | `USE_ITEM` RPADUP/E, `USE_VEHICLE_MOD` RPADRIGHT/MOUSE3; the land-vehicle action list has **no aim action** |
| 6 | `HACKABLES.md:32`, `:103` | **0** range/radius/distance members on the interaction graph |
| 7 | `JC3_HUD_WEAPONS.md` §7 | the full element list; `reticle_size` 5…30 px is the only size parameter |
| 8 | negative search `static|noise|jam|overlay|fullscreen` in `JC3_HUD_WEAPONS.md` | **0 hits** — reported as "no such element decoded", not as "no such element exists in the game" |
| 9 | `EMP.md` §80-86 | `entry.use_item` → `S_STUNT_USE_ITEM_VEHICLE` with the `trigger.use_item` box — the gadget pattern the halt rests on |

No game process was started, attached to or injected into; static read only.
