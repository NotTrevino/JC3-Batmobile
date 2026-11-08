# Driverless driving — BmAK's remote & autonomous drive, and the JC3 carrier

**Question:** what does BmAK's remote and autonomous drive do (speed ceiling, avoidance,
destination logic) per the BmSDK members and animations; and what is the nearest JC3 AI vehicle
behaviour (convoy, pursuit, mission follow), with the entity and tune values that reproduce it.

**Verdict.** BmAK has **two separate driverless systems**, and neither is a speed-capped "AI car":
1. **Remote control** — a gadget (`RBatmobileRemoteBm`) that aims a **cursor**; the car drives
   itself toward the cursor point. Decoded values: `JammingRange` **10000.0 cm = 100 m**,
   `JammerTime` **1.5 s**, `CursorSpeed` **3.0**, `CursorAccel` **5.0**, `CursorDecel` **10.0**,
   `CursorReturnFactor` 2.0, `CursorReturnDelay` **2.0 s**, `MaxAimX` 0.9. Range exit is a
   **thought + a timer** (`NotifyReachedHardRemoteLimit`, `DrivingModeTimeRemoteBatmobileOutOfRange`),
   not a hard stop. The car's last safe spot is stored (`RemoteSafePointLocation/Rotation/Blocked`).
2. **Self-drive** — a **road-network route follower** on `RVehicle`: 47 `SelfDrive*` members plus
   6 natives (`SelfDrive`, `SelfDriveAsync`, `SelfDriveAsyncAll`, `SelfDriveDirect`,
   `SelfDriveRescue`, `SetSelfDriveMode`, `SetSelfDriveNextSpanToNearest`). It routes over
   `RRoadNetwork` **spans** to a **target location**, stops for obstacles using
   `NPCCheckExtents` **`[400, 300, 1000]` cm**, recovers from being stuck
   (`SelfDriveStuckTime`, `SelfDriveReverseTime`, `SelfDriveUturn`), and throttles by a **scale**,
   not a cap.
   **There is no maximum-speed member anywhere in the self-drive set** — the ceiling is the car's
   own driveline, and the numeric ceiling is **UNKNOWN** (the one speed-shaped datum,
   `SelfDriveSteeringSpeedCurve`, is an `FInterpCurveFloat` whose points were not decoded).
   Animations add nothing: driverless driving plays the **same** pursuit locomotion clips; what
   changes is the **entry** move (`Get_In_Batmobile_Remote_Front/_Back/_Fast_Remote`) and the
   absence of a driver.
3. **JC3's nearest carrier is `CarAI`** — a 25-member module on **3 builds** that turns
   *Input_Speed / Input_Turn / Limit_Speed* curves into throttle and steering. Its decoded tune is
   `Limit_Speed.y_max` **35** (fleet 22..45), `y_min` **5** (2..10), `Input_Speed.x_max` **15**
   (12..25), `Input_Turn.x_max` **0.5**. JC3 has **no obstacle-avoidance member, no destination
   member and no convoy/pursuit/follow action**; ambient AI is instead a **traffic rule + Driver
   seat + `.bts` behaviour tree** (`global/global.blo`). So JC3 can carry "an AI drives this car at
   up to 35", and cannot carry "drive to that point and stop" without a code bridge.

Labels: **decoded** = read from the cited file at the cited member/offset; **derived** = arithmetic
or mapping; **UNKNOWN** = searched and absent, with where it would be settled.

---

## 1. BmAK remote control (the aim-a-cursor mode)

### 1.1 The gadget and its decoded values

`RBatmobileRemoteBm` — `GADGET_PARAMS.md` §2, `Startup.upk` export 536, `RBatmobileRemoteBm.g.cs`
line refs given per row:

| member | type | value | offset |
|---|---|---:|---|
| `JammingRange` | float | **10000.0** (= **100 m**, cm units) | 0x2c |
| `JammerTime` | float | **1.5 s** | 0x34 |
| `CurrentJam` | float | -1.0 (none) | 0x3c |
| `CursorSpeed` | float | **3.0** | 0x44 |
| `CursorAccel` | float | **5.0** | 0x4c |
| `CursorDecel` | float | **10.0** | 0x54 |
| `CursorReturnFactor` | float | 2.0 | 0x5c |
| `CursorReturnDelay` | float | **2.0 s** | 0x64 |
| `MaxAimX` | float | 0.9 | 0x6c |
| `MaxAimY` | float | (gadget table) | 0x70 |
| `RemoteControlBatmobileMove` | object | `Batmobile_Remote.RemoteControlBatmobile` (`RSpecialMoveConfigConfigurable`) | 0x24 |
| `FireSound` / `CancelSound` / `CancelSound2` / `CallSound` | objects | `Ww_CHR_RemoteGadget.Play_Remote_Gadget`, `Engine.Play_Remote_Gadget_Off`, `Engine.Play_Gauntlet_Batmobile_Call` | 0x4 / 0xc / 0x14 / 0x1c |

So the remote is **cursor-velocity** control (`CursorSpeed` 3.0, accel 5.0, decel 10.0, clamp 0.9
of the aim box), with the cursor **returning to centre** after 2.0 s at 2× rate — the car
therefore *stops* when the player lets go, rather than continuing to a destination.

### 1.2 State and limits

| symbol | where | meaning |
|---|---|---|
| `bRemoteDrive` | `RVehicleBatmobileBase` word `0x11d8`, **bit 0x1000000** | remote mode on; only **one** writer in `.text` (`0x14046c670`, `and …, 0xfeffffff` — clear) |
| `bFakeRemoteDrive` | bit 0x2000000 | remote *without* the gadget (scripted) |
| `bRemoteScoopUp` | bit 0x4000000 | the car drives under Batman and scoops him up |
| `bWasRemoteDriving` | bit 0x8000000 | read by `DriverLeft` to pick its branch (`COLLISION_SELECTOR3.md`, `DRIVERLEFT_7400.md`) |
| `bRemoteDriveBatmanTrackerDisabled` | bit 0x10000000 | disables the tracker while remote |
| `DoNotBreakRemoteControlIfBatmanInCombat` | bool @4572 | remote survives Batman entering combat |
| `RemoteSafePointLocation` / `RemoteSafePointRotation` / `RemoteSafePointBlocked` | @6512 / @6524 / @4572 | the fallback parking spot |
| `GetDistanceToRemoteControlBoundary`, `RPlayerController.BatmobileOutOfRemoteRange`, `DrivingModeTimeRemoteBatmobileOutOfRange` | natives / float | the range gate and the "thought" timer |
| `NotifyReachedHardRemoteLimit`, `NotifyRemoteDriveCancelled` | functions on `RBatmobileRemoteBm` | feedback hooks |
| global flag `Batman_Remote_Control_Batmobile` | flag block, `SetGlobalFlag(…, false)` | the level-side latch for "is the player remote driving" |

`GetDistanceToRemoteControlBoundary`'s **numeric** boundary and the out-of-range **delay** are not
serialised in any CDO here — **UNKNOWN**; `JammingRange` 100 m is the gadget's own range number, and
whether the *drive* boundary equals it is not stated in any file.

### 1.3 What it is not

There is **no path, no destination and no avoidance** in the remote gadget: the "destination" is
the cursor point, refreshed each tick, and the car's job is to steer toward it. Avoidance is the
player's (and `NPCCheck*`, §2.2).

---

## 2. BmAK self-drive (the autonomous mode)

### 2.1 The member set (`RVehicle`, offsets from `BMSDK_OFFSETS.json`)

| group | members | evidence |
|---|---|---|
| **mode / state** | `SelfDriveMode` (`ESelfDriveMode` @2154), `SelfDrive`/`SelfDriveAsync`*/`SelfDriveDirect`/`SelfDriveRescue` natives, `SetSelfDriveMode`, `UpdateSelfDriveStuckTime` | `CONTROLS.md` 135/1642/1797/1798, `NATIVE.md` |
| **destination** | `SelfDriveStartLocation` @2464, `SelfDriveTargetLocation` @2476, `SelfDriveEndPointDist` @2384, `SelfDriveEndPointDistNeutralLine` @2432, `SelfDriveArrived` (object, `RVehicleBehaviour` @2196), `SelfDriveAction` (`RSeqAct_VehicleSelfDrive` @2204) | `BMSDK_OFFSETS.json`, `NATIVE.md` `OnSelfDriveArrived` |
| **route** | `SelfDriveRoads` (`RRoadNetwork` @2188), `SelfDriveRoute` @2316, `SelfDriveRouteSpans` (`FRoadNetworkSpan[]` @2332), `SelfDriveRouteLine` (`FRacingLineSeg[]` @2348), `SelfDriveRouteSplinePoints` @2364, `SelfDriveNextSpan` @2380, `SelfDriveForwardTargetLoc` @2392, `SelfDriveForwardRoadDir` @2404, `GetSelfDriveNextLink` / `NextRoadLink` / `PrevRoadLink` / `SetSelfDriveNextSpanToNearest` / `IsInsideSelfDriveSpans` | decoded member types; native names |
| **spline / patrol** | `SelfDriveIsSpline`, `SelfDriveLoop`, `SelfDriveSplineDontStopAtEnd` (all bool in the word @2180) | `CLASS_DEFAULTS.json` |
| **throttle** | `SelfDriveThrottleScale` @2416, `SelfDriveThrottleMin` @2420, `SelfDriveThrottleEaseDistance` @2440 | decoded offsets |
| **line keeping** | `SelfDriveLineMin` @2424, `SelfDriveLineMax` @2428, `SelfDriveKeepToSide` @2444, `SelfDriveExtraWidth` @2460, `SelfDriveMinSpanWidth` @2436 | decoded offsets |
| **obstacles** | `SelfDriveStopForObstacles`, `SelfDriveUseFootpathToAvoidObstacles`, `SelfDriveRoadObstacleTypes` (`FRoadObstacleTypes` @6852), `SelfDriveAvoidedObstacle` (`Actor` @2220), `SelfDriveExtraWidth` | decoded |
| **tight area** | `SelfDriveUseTightArea`, `SelfDriveTightArea` (`FRoadNetworkTightArea` @2516), `SelfDriveTightAreaDest` @2488, `SelfDriveTightAreaRoute` @2500 | decoded |
| **stuck / turn** | `SelfDriveStuckTime` @6400, `SelfDriveReverseTime` @6404, `SelfDriveUturn` (bit 0x800000), `SelfDriveTurnOnSpot`, `SelfDriveCanDriveBackwards`, `SelfDriveBackwards`, `SelfDriveCanJumpUp`/`Down`, `SelfDriveErratic`, `SelfDriveWheelspinTime` @2448, `SelfDriveSkidToStopTime` @2456, `SelfDriveBrakeLights` @2452 | `BMSDK_OFFSETS.json`, `CONTROLS_NATIVE2.md` |
| **steering vs speed** | `SelfDriveSteeringSpeedCurve` — `FInterpCurveFloat` at **0x27c** on `RVehicleSimBatmobile` | `BMSDK_OFFSETS.json` |

Three members are serialised with values (`CLASS_DEFAULTS.md`): `SelfDriveCanJumpDown=True` and
`bAddNavMeshObstacle=True` (same 32-bit word @2180), `SelfDriveAllowBoost=True`
(`RVehicleBatmobileBase` @4568, mask 0x2000), `SelfDriveRoadObstacleTypes` (1 nested prop, `0xfe`),
`NPCCheckExtents` `[400.0, 300.0, 1000.0]`, `NPCCheckOffset` `[-50.0, 0.0, 0.0]`. Every other
`SelfDrive*` numeric (throttle scale/min/ease, line min/max, stuck/reverse times, span width) has
its **offset decoded but no value** — they are per-instance, and no CDO in this grab carries them:
**UNKNOWN values, known slots.**

### 2.2 Speed ceiling — the honest answer

* **No member caps speed.** `SelfDriveThrottleScale` multiplies the driveline request;
  `SelfDriveThrottleMin` is a floor so the car does not stall in a turn; neither is a limit.
* The only speed-shaped autonomous datum is `SelfDriveSteeringSpeedCurve` (steering amount vs
  speed), an `FInterpCurveFloat` whose **points were not decoded** (`DRIVE_MODES.json` has the
  member, `null` for the curve body).
* Therefore the autonomous ceiling is **the car's own top speed**, and the autonomous *number* is
  **UNKNOWN**. It is not `TurningModeMaxSpeed` 600 cm/s (21.6 km/h) — that is the battle-mode
  turning clamp (`MODES.json`, `modes-hud-evidence.md`), and not `BattleModeVSpeedCurve`.

### 2.3 Avoidance

Two layers, both decoded as **symbols**:

1. **Extent test** — `NPCCheckExtents [400, 300, 1000]` cm, offset `[-50, 0, 0]` cm ahead of the
   actor: a 8 m × 6 m × 20 m probe box, nudged 0.5 m forward. This is the "is something in front"
   primitive (`CheckForNPCCollisionWarning`, `TraceEmptyVehicleNPC`, `TraceAbandonedVehicle`).
2. **Road obstacle classification** — `SelfDriveRoadObstacleTypes` (`0xfe` word in the CDO) plus
   `SelfDriveStopForObstacles` (stop) and `SelfDriveUseFootpathToAvoidObstacles` (route around via
   the footpath network), with `SelfDriveAvoidedObstacle` set to the actor that was dodged and
   `SelfDriveExtraWidth` padding the span so the car does not clip.
3. **Recovery** — `UpdateSelfDriveStuckTime` accumulates `SelfDriveStuckTime`; past the threshold
   the car reverses for `SelfDriveReverseTime` (with `SelfDriveUturn` allowed to flip the heading)
   and regains the span. Values UNKNOWN (above).

### 2.4 Destination logic

A route is **built over the road network**, not planned freely:
`SelfDriveRoads` (the `RRoadNetwork`) → `SelfDriveRouteSpans` (the span list) →
`SelfDriveNextSpan` advanced by `GetSelfDriveNextLink`/`NextRoadLink` until
`SelfDriveEndPointDist` is inside tolerance, then `SelfDriveArrived` (an `RVehicleBehaviour`) fires
and `OnSelfDriveArrived` runs. `SelfDriveIsSpline` + `SelfDriveRouteSplinePoints` switch the same
machinery to a **spline** route; `SelfDriveLoop` + `SelfDriveSplineDontStopAtEnd` make it a patrol
that never ends; `SelfDriveTightArea*` handles the last metres where the span width is below
`SelfDriveMinSpanWidth`. `SelfDriveAction` (`RSeqAct_VehicleSelfDrive`) is the Kismet action that
hands a target to the car — i.e. **the level, not the car, chooses the destination**.

### 2.5 Animations — what actually changes

Self-drive adds **no new driving clip**: the car plays its normal pursuit locomotion
(`ANIMATIONS.md` — the `Batmobile_V2_*` set; there is no `SelfDrive` or `AutoDrive` clip in the
1,387-line inventory). The driverless signature is in the **entry** moves:
`Batman_Batmobile_Moves.Get_In_Batmobile_Remote_Front` / `_Remote_Back` / `_Fast_Remote`
(`CLASS_DEFAULTS.md` rows, `RSpecialMoveConfigConfigurable`), plus the stand-in variants
`BatMobile_Stand_In_Fast_Remote`, `BatMobile_Stand_In_Right_Fast_Remote`,
`In_Front_Remote_Batmobile`, `In_Back_Remote_Batmobile` (`EJECT_MOVE.json`), and the special move
`Batmobile_Remote.RemoteControlBatmobile` that the gadget fires. The cockpit seat bone is simply
empty — `Batmobile_Bone_Chair_*` still moves with the rig (`POSES.md`).

---

## 3. JC3's nearest AI vehicle behaviour

### 3.1 The candidate table

| JC3 thing | what it is | is it BmAK's self-drive? |
|---|---|---|
| **`CarAI` module** | 25 members: `Input_Speed`, `Input_Turn`, `Limit_Speed` curves + `Limit_IsLargeVehicle`; **3 builds, 3 instances** (`DRIVE_CARRIERS.json` `modules.types`) | **closest**: curve→throttle/steer AI driving. No route, no target, no avoidance member. |
| **traffic rules** (`global/global.blo`) | 31 rule names, 41 tag selectors, `Driver` seats bound to **10 `ai/bts/*.bts` trees** (`ai/bts/civilian/civilian_std.bts`, `…/soldier_tank_driver.bts`, …) | convoy/ambient: AI drives **because a rule spawned a driver**, not because the car was told to go somewhere |
| `AITrafficImpostorSystem` / `PCAITrafficImpostorSystem` | named objects in `global.blo` | LOD impostor traffic, not a behaviour |
| **convoy / pursuit / mission-follow** | search for `convoy`, `follow`, `AddFollower`, `GetOffsetBehindFollowVehicle` in JC3 members | **absent**: 0 members; those names are BmAK's (`NATIVE.md`). JC3 mission follow would be a graph/`.bts` behaviour, not a vehicle member — **UNKNOWN** |
| **remote/summon** | **Rebel Drop**: an `Item` whose `Name` is the 32-bit Jenkins hash of the entity leaf; the game spawns that `.ee` | the *summon* half of BmAK's remote gadget, with no driving |

### 3.2 `CarAI`'s decoded tune (`VOCABULARY.md` §`CarAI`)

| member | type | fleet range | donor |
|---|---|---|---:|
| `Limit_Speed.y_max` | float | 22 .. 45 | **35** |
| `Limit_Speed.y_min` | float | 2 .. 10 | **5** |
| `Limit_Speed.x_min` | float | 0 .. 0.2 | **0.1** |
| `Limit_Speed.x_max` | float | 1 .. 1 | **1** |
| `Limit_Speed.number_of_control_points` | int8 | 4 .. 5 | **4** |
| `Input_Speed.x_max` | float | 12 .. 25 | **15** |
| `Input_Speed.x_min` | float | 0 .. 1 | **1** |
| `Input_Speed.y_max` / `y_min` | float | 1 / 0 | **1 / 0** |
| `Input_Speed.number_of_control_points` | int8 | 3 .. 4 | **3** |
| `Input_Turn.x_max` | float | 0.15 .. 1 | **0.5** |
| `Input_Turn.number_of_control_points` | int8 | 4 | **4** |
| `Limit_IsLargeVehicle` | uint8 | 0 .. 1 | **0** |

(All twenty-five rows are in `VOCABULARY.md` §`CarAI`; the curve point arrays are the donor's
three-value sets, not reproduced here.)

Read: `Limit_Speed` is a **speed cap as a function of steering/curvature**, topping at **35** — this
is the one place JC3 *does* hold a ceiling, which BmAK's self-drive does not have as data. `Input_Turn`
clamps steering to **0.5**, and `Input_Speed` maps a normalised demand to 0..15.

### 3.3 What JC3 cannot carry

| BmAK behaviour | JC3 member? | verdict |
|---|---|---|
| speed ceiling | `CarAI.Limit_Speed.y_max` 35 | **carrier found** (tune) |
| throttle shaping | `CarAI.Input_Speed` / `Input_Turn` curves | **carrier found** (tune) |
| destination / route over a road network | **0 members** (`CarAI` has no target/route/span) | **UNKNOWN / code bridge** — JC3's equivalent is the `.bts` tree + `global.blo` rule, neither of which takes a target from a mod |
| obstacle probe `[400,300,1000]` cm | **0 members** | **UNKNOWN / code bridge**; the nearest shipped behaviour is `SelfDrive`-less: JC3 path following is native |
| stuck → reverse → u-turn | **0 members**; nearest is `arcade.turbo_jump` (an impulse, not a recovery) | no carrier |
| remote aim-a-cursor at 100 m | 0 members; and the keymap has no 2D vehicle stick action (`DRIVE_CARRIERS.md` §4) | **code bridge**, plus a keymap rebind |
| summon the car to the player | **Rebel Drop item** (`item.onlinec`) | **carrier found** (data, no driving) |

---

## 4. The build: entity and tune values that reproduce it

**Entity.** The private Batmobile `.ee` (standalone, per `TRAFFIC.md` §7 route 2 so it inherits no
civilian traffic record), plus **one `CarAI` module** copied from one of the three builds that ship
it (the counts are decoded — 3 builds / 3 instances — but that file does not list which builds,
so naming them is U6 and the first thing the experiment in §5 settles), plus **a Driver seat** on
the entity's second seat so a `.bts` tree has somewhere to sit, plus **a Rebel Drop item** for the
summon.

**Tune, with the values and their provenance:**

| target | member | value | why |
|---|---|---:|---|
| ceiling | `CarAI.Limit_Speed.y_max` | **35** | donor; BmAK's own ceiling is UNKNOWN, so the fleet's curve is the only defensible number |
| low-speed floor | `CarAI.Limit_Speed.y_min` | **5** | donor |
| speed demand map | `CarAI.Input_Speed.x_max` | **15** | donor (fleet 12..25) |
| steer clamp | `CarAI.Input_Turn.x_max` | **0.5** | donor |
| large-vehicle flag | `CarAI.Limit_IsLargeVehicle` | **0** | the Batmobile is 4.7 m wide in battle (4.69 m bbox, `POSES.md`) — set **1** only after a test shows it clips spans |
| boost discipline | `CAR` `arcade.nitro_boost.extra_top_speed` | keep 40 | `SelfDriveAllowBoost=True` is BmAK's only autonomous boost datum; JC3's boost needs a trigger JC3 does not name (`DRIVE_CARRIERS.md` §6.2) |
| summon delay | `Item.RebelDropTimer` | **1800** | the donor vehicle drop's value; 0 for no cooldown (`REBELDROP.md` §7) |

**What the build is honest about:** with `CarAI` + a Driver seat the car will **drive itself at up
to 35** — that reproduces BmAK's *feel* of an autonomous car, and nothing more. It will **not**
drive to a point you choose, will **not** probe 8×6×20 m ahead, and will **not** recover from being
stuck, because no member exists for any of those and no `.bts` accepts a mod-supplied target. Those
three are the code-bridge boundary, same wall as `DRIVE_CARRIERS.md` §4 (no 2D stick, no per-wheel
drive).

---

## 5. The cheapest experiment (5 minutes, read-only)

1. `CarAI` is on **3 builds** — open those three `.ee` files and diff their `car_ai` module
   against the `v0803_car_na_monstertruck` rows in `VOCABULARY.md`. If all three are byte-identical
   the module is a stock import and can be copied into the private entity with confidence.
2. Then check the **Driver seat** the module expects: `global/global.blo` pairs each traffic rule
   with a character selector + a `.bts`. The private entity needs the same pair, or the AI has no
   owner. Reading the donor's `.epe` seat list answers this without a launch.
3. Only then write anything: a copied module with no seat is a no-op, and a seat with no tree is a
   parked car.

Acceptance, once built: spawn the entity, watch whether it moves at all, and measure its top speed
against `Limit_Speed.y_max` 35. Anything beyond "it moves" needs the code bridge named in §4.

---

## 6. If files are touched later — change, file, revert

Nothing was modified for this report.

| intended change | file | why it is the right file | revert |
|---|---|---|---|
| add AI driving | private `.ee`'s module list — a `CarAI` module instance | `CarAI` is the only module that maps curves to throttle/steer (3 builds) | rebuild from the build manifest |
| give the AI an owner | private `.ee`'s Driver seat + the tree path | `global.blo` traffic rules pair a vehicle with a `Driver` seat and a `.bts` | same |
| summon to the player | `profile/item.onlinec` — one `Item` whose `Name` = Jenkins hash of the entity leaf | the drop binds by leaf hash, no path field exists (`REBELDROP.md` §4) | remove the record; restore the file from the layer |
| nothing at all for remote/route/avoidance | — | no JC3 member exists | — |

## 7. UNKNOWNs, each with its settler

| # | unknown | settler |
|---|---|---|
| U1 | BmAK's autonomous **speed ceiling** | `SelfDriveSteeringSpeedCurve` points (0x27c on `RVehicleSimBatmobile`) are not in the grab; a live sample of the sim's target speed, or the curve bytes |
| U2 | `ESelfDriveMode` value domain | named only as an enum (export 1425); values not decoded |
| U3 | every numeric `SelfDrive*` slot (throttle scale/min, line min/max, stuck/reverse, span width, extra width) | offsets are decoded; the per-instance values are not in any CDO here — read the live object or a level-placed instance |
| U4 | whether `JammingRange` 100 m is the *drive* boundary | `GetDistanceToRemoteControlBoundary` body / a runtime sample |
| U5 | the out-of-range grace timer | `DrivingModeTimeRemoteBatmobileOutOfRange` value (per-instance) |
| U6 | which three JC3 builds carry `CarAI` | `DRIVE_CARRIERS.json` records counts (3/3) but not the build list; the `.ee` module tree names them |
| U7 | whether `CarAI` on a player-driven entity is honoured | runtime test; the module is shipped for ambient traffic |
| U8 | JC3 convoy/pursuit/follow | 0 members named; would be a `.bts`/graph behaviour, and no file names one for a mod-supplied vehicle |
| U9 | whether a dropzone `.ee` can carry a `.bts` reference | `global.blo` is global; no entity-scoped tree reference was found |

## 8. Sources

**BmAK:** `Research/BatmobileGrab/GADGET_PARAMS.md` §2 (every `RBatmobileRemoteBm` value and
offset cited above), `BMSDK_OFFSETS.json` (`RVehicle` / `RVehicleBatmobileBase` /
`RVehicleSimBatmobile` self-drive member offsets), `CLASS_DEFAULTS.md` (the three serialised
`SelfDrive*` values, `NPCCheckExtents`/`NPCCheckOffset`), `CONTROLS_NATIVE2.md` (the `0x11d8` word
and its 23 bits, including `bRemoteDrive` 0x1000000 and `SelfDriveUturn` 0x800000), `NATIVE.md`
(`SelfDrive`, `SelfDriveAsync*`, `SelfDriveDirect`, `SelfDriveRescue`, `SetSelfDriveMode`,
`SetSelfDriveNextSpanToNearest`, `IsInsideSelfDriveSpans`, `GetSelfDriveNextLink`,
`ComputeSelfDriveEndPointDistance`, `ComputeSelfDriveRouteLengthNeutralDelta`,
`UpdateSelfDriveStuckTime`, `AdvanceSelfDriveNextSpan`, `CancelSelfDrive`), `CONTROLS.md`
(135/1642/1797/1798 `ESelfDriveMode` and `SetSelfDriveMode`), `CONTROLS_CONSUMERS.md`
(`GetDistanceToRemoteControlBoundary`, `BatmobileOutOfRemoteRange`,
`DrivingModeTimeRemoteBatmobileOutOfRange`, `RemoteSafePoint*`, `DoNotBreakRemoteControl…`,
`bFakeRemoteDrive`, `bRemoteDrive`), `COLLISION_SELECTOR3.md` / `DRIVERLEFT_7400.md`
(`bWasRemoteDriving`, the `Batman_Remote_Control_Batmobile` flag), `DRIVE_MODES.md` (the
`BMDM_*` enum and `SetDriveMode` sites), `ANIMATIONS.md` (no self-drive clip),
`EJECT_MOVE.json` + `CLASS_DEFAULTS.md` (the remote entry moves).

**JC3:** `Research/JC3Grab/DRIVE_CARRIERS.json` (`CarAI` = 3 builds / 3 instances; the no-stick,
no-per-wheel results), `VOCABULARY.md` §`CarAI` (the 25 members and their fleet ranges/donor),
`TRAFFIC.md` (§3 the 31 rules / 41 selectors / `Driver` seats / 10 `.bts` paths;
§6 the entity's own `…_land_global_ai.vmodc`; §7 the standalone-vs-replace decision),
`TRAFFIC.json` (the `.bts` path list), `REBELDROP.md` (§4 the leaf-hash binding; §7 the item
recipe), `INPUT.md` (no vehicle 2D stick action).
