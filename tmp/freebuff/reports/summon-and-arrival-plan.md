# Calling the car — the BmAK summon, element by element, and the JC3 carriers

**STATUS: done (plan, read-only).** The BmAK summon is a **gadget on LB / E** that fires
`CallSound` (`Engine.Play_Gauntlet_Batmobile_Call`) and puts the Batmobile into **self-drive**; it
arrives on the road network under `SVehicle.MaxSpeed` (**4000 cm/s = 40 m/s = 144 km/h**), may
**boost** (`SelfDriveAllowBoost=True`), **jump down** (`SelfDriveCanJumpDown=True`) and **U-turn**,
then **skid-stops** at the player (`bSkidToStop`, `DestReachedSkidToStop`) so a `Remote_Front` /
`Remote_Back` entry move can finish. **JC3 reuses the already-built Rebel Drop entry** (B-13,
item hash **443190071**) for the *existence* of the called car and **`VehicleDynamicLights`
`HeadLight`** for its arrival lights, but **no JC3 system spawns a vehicle at the player and drives
it in**, and JC3 has **no call sound**.

The one hard limit, stated before any table: **BmAK's call timing is not decoded.** The 25
behaviour members of `RBatmobileRemoteBm` (including `CallBatmobile`, `CancelCallBatmobile`,
`NotifyCallBatmobileToMe`) ship as **untagged 30-byte records with no bytecode and no constants**
(`GADGET_PARAMS.md` §"the 25 behaviour members"), so call delay, spawn distance and stop radius are
**UNKNOWN**. The only arrival-adjacent timing values BmAK decodes are on the *Batwing vertical drop*
path (§7), and those are used only for that path.

---

## 1. Evidence base

| element | decoded fact | source |
|---|---|---|
| keyboard bind | `EnterCallBatmobile` on **E** (`kCallBatmobile` = `[E]`) | `CONFIG2.md:284,319,394,397` (`BmGame.ini` / `PC/PCGame.ini`, `DefaultBatmanKeyMap`) |
| pad bind | `pCallBatmobile` = **{PAD_LB}** | `CONFIG2.md:291,359` (`BmGame.ini`, `DefaultGame.ini` `Engine.PlayerTags`) |
| gadget class | `BmScript.RBatmobileRemoteBm`, 48 members / 23 value slots / 25 behaviour members | `GADGET_PARAMS.md` §1; `GADGET-params.md` |
| call sound | `CallSound` = `Engine.Play_Gauntlet_Batmobile_Call` (AkEvent), tag 0x948 @0x1c | `GADGET_PARAMS.md:60`; `GADGET-params.md:46` |
| cancel sounds | `CancelSound` = `Ww_CHR_RemoteGadget.Play_Remote_Gadget`; `CancelSound2` = `Engine.Play_Remote_Gadget_Off` | `GADGET_PARAMS.md:61,62` |
| call functions | `CallBatmobile`, `CancelCallBatmobile`, `NotifyCallBatmobileToMe`, `ShowFailIcon`, `DrawTarget`, `GetPromptName`, `GetHelpPrompt` | `GADGET_PARAMS.md` §"25 behaviour members" |
| call target slot | `CallingVehicle` (object ref, **value UNKNOWN** — no tag in either CDO) | `GADGET_PARAMS.md` §UNKNOWN |
| prompt gate | `BmScript.RLevelTransitionShutterDoors.ShouldShowCallBatmobilePrompt` | `PACKAGES_G305.md:560` |
| self-drive state | `ESelfDriveMode` (enum), `SelfDriveMode` (byte), `SetSelfDriveMode` (function) on `RVehicle` | `CONTROLS.md:135,139,141,142` |
| self-drive entry | native `RVehicleBatmobileBase.StartSelfDrive` (export 10701) | `COLLISION_SELECTOR.md:79`; `NATIVE.md:71` |
| self-drive capability | `SelfDriveAllowBoost=True` (bool word at offset 4568) | `CLASS_DEFAULTS.md:179,508` |
| self-drive capability | `SelfDriveCanJumpDown=True` (byte 2180, `RVehicle`) | `CLASS_DEFAULTS.md:152,439` |
| self-drive flags | `SelfDriveUturn` (0x800000), `SelfDriveUseTightArea`, `SelfDriveRoadObstacleTypes` (struct, word `0xfe`) | `CONTROLS_NATIVE2.md:34`; `CLASS_DEFAULTS.json`; `CLASS_DEFAULTS.md:254,561` |
| speed ceiling | `SVehicle.MaxSpeed` = **4000.0 cm/s** (class default, 0x358) | `CLASS_DEFAULTS.md:163,436` |
| stop behaviour | `bSkidToStop` on `RVehicleSimBatmobile`; native `SkidToStop` writes `SkidToStopDir` at 0x3B1 | `NATIVE.md:119,134`; `DRIVE_MODES.md:122` |
| stop at destination | `DestReachedSkidToStop`, `SkidToStopJumpIn` functions on `RVehicleBatmobile` | `PACKAGES_G305.md:565,570`; `REMAINDER.md:1841-1842` |
| post-arrival entry | `GetInRemoteMoveFront` = `Get_In_Batmobile_Remote_Front`; `GetInRemoteMoveBack` = `Get_In_Batmobile_Remote_Back`; `HighSpeedPickupMove` = `Get_In_Batmobile_Fast_Remote`; `JumpInBatmobileSkidStopMove` = `Jump_In_Batmobile_Skid_Stop` | `CLASS_DEFAULTS.md:89,90,99,91` |
| remote-drive flag | global flag `"Batman_Remote_Control_Batmobile"` set false when the driver enters | `COLLISION_SELECTOR3.md:268,316` |
| lights (on the car) | `ForceHeadlightsSwitchedOn` (bool 0x20000); `HeadlightsSwitchedOn` read in Pursuit/Battle Tick; `HeadLightsColourPursuit` (1,1,1,1); `HeadLightsColourBattle` (25,0,0,1); `HeadLightMaterialIndex` 5 | `CONTROLS_NATIVE2.md:28`; `DRIVE_MODES.md:180,255`; `CLASS_DEFAULTS.md:263,264,142` |
| lights (left with car) | `InteriorLightsSwitchedOn` cleared on driver-left logic | `DRIVERLEFT_REGIONS.md:59,92`; `COLLISION_SELECTOR3.md:53` |
| **not decoded** | call delay, spawn offset, stop radius, self-drive speed cap, arrival animation timing | the 25 behaviour bodies (no bytecode), §9 |

## 2. Trigger

| step | BmAK | value / evidence |
|---|---|---|
| player is on foot | prompt only shows where the game allows a call | `ShouldShowCallBatmobilePrompt` (`PACKAGES_G305.md:560`) |
| press | pad **LB**, keyboard **E** | `pCallBatmobile` {PAD_LB}; `kCallBatmobile` [E] (`CONFIG2.md:291,319,359,397`) |
| gadget check | `RBatmobileRemoteBm` is the gadget that owns the call; `AssociatedGadgetFlagName` = `"Equip_BatmobileRemote"` | `GADGET_PARAMS.md` inherited defaults |
| sound | `CallSound` = `Engine.Play_Gauntlet_Batmobile_Call` | `GADGET_PARAMS.md:60` |
| cancel path | `CancelCallBatmobile` + `CancelSound` / `CancelSound2` | `GADGET_PARAMS.md:61,62` |
| car begins self-drive | `StartSelfDrive` on the car; `SelfDriveMode` set via `SetSelfDriveMode` | `COLLISION_SELECTOR.md:79`; `CONTROLS.md:135-142` |
| start gate | `CallingVehicle` (the car being called) — **value UNKNOWN** | `GADGET_PARAMS.md` §UNKNOWN |

The call is **one press**, with no charge-up: the only call-time number decoded anywhere near the
gadget is `CallSound`, an event path (duration not decoded). `JammerTime` 1.5 s / `JammingRange`
10000.0 belong to the *remote-piloting* half of the same gadget, not the summon (`GADGET-params.md`).

## 3. Route

| leg | BmAK mechanism | evidence |
|---|---|---|
| spawn / wake | the car is a live actor that `StartSelfDrive`s; no teleport is decoded for the call (teleport is a level-volume flag, `CanTeleportBatmobile=false` in `Ace_A1`) | `CONFIG2.md:273`; `COLLISION_SELECTOR.md:79` |
| pathing | navmesh self-drive (`ESelfDriveMode`/`SelfDriveMode`), road obstacles `SelfDriveRoadObstacleTypes` (0xfe word), tight-area handling `SelfDriveUseTightArea` | `CONTROLS.md:135-142`; `CLASS_DEFAULTS.md:254,561`; `CLASS_DEFAULTS.json` |
| vertical | may drop off ledges: `SelfDriveCanJumpDown=True` | `CLASS_DEFAULTS.md:152,439` |
| turn-around | `SelfDriveUturn` bit 0x800000 | `CONTROLS_NATIVE2.md:34,66,98` |
| speed | allowed to boost: `SelfDriveAllowBoost=True`; ceiling `SVehicle.MaxSpeed` 4000 cm/s | `CLASS_DEFAULTS.md:179,163` |
| avoidance | `GetAdjustedAvoidanceDirection`, `bDebugAdjustedAvoidanceDirection` in the pursuit tick | `DRIVE_MODES.md:180` |
| arrival | destination reached → skid stop (`DestReachedSkidToStop`, `bSkidToStop`, `SkidToStopJumpIn`) | `PACKAGES_G305.md:565,570`; `NATIVE.md:119` |

So BmAK's route is **driven, not dropped**: it wakes where it is parked, uses the navmesh and the
road-obstacle mask, may boost and jump down, and stops by skidding when it reaches the destination.
There is **no teleport-to-player** in the summon path (the only teleport token in the config is a
per-level `CanTeleportBatmobile` volume flag, false in the sampled level).

## 4. Speed

| number | value | status |
|---|---:|---|
| `SVehicle.MaxSpeed` (class default) | **4000 cm/s = 40 m/s = 144 km/h** | decoded (`CLASS_DEFAULTS.md:163`) |
| boost | allowed (`SelfDriveAllowBoost=True`); BmAK boost thrust 6 m/s², speed add 43.2 km/h, 2.0 s, 12 s cooldown | decoded capability + decoded boost chain (`keep-audit-engine-boost-aero.md`) |
| self-drive cap | **UNKNOWN** | no decoded field; the sim's own cap would be in the behaviour bodies |
| arrival speed (at the skid) | **UNKNOWN** | no decoded deceleration ramp |

`BattleModeMaxSpeed` 1200 cm/s (43.2 km/h) is **not** the summon speed — it is the battle-mode cap
(`MODES.md:96`; `chase-06.md:148`). The only defensible ceiling for the drive-in is therefore
**40 m/s**, and any arrival schedule derived from it is a **distance/speed derivation**, not a BmAK
value (§8).

## 5. Lights on arrival

| light element | BmAK | status |
|---|---|---|
| headlights forced on | `ForceHeadlightsSwitchedOn` (bool bit 0x20000) exists on `RVehicle` | decoded member; **whether the call sets it is UNKNOWN** |
| headlights read by mode | `HeadlightsSwitchedOn` referenced in Pursuit and Battle ticks | decoded reference (`DRIVE_MODES.md:180,255`) |
| headlight colour, pursuit | `HeadLightsColourPursuit` = **(1.0, 1.0, 1.0, 1.0)** white | decoded (`CLASS_DEFAULTS.md:263`) |
| headlight colour, battle | `HeadLightsColourBattle` = **(25.0, 0.0, 0.0, 1.0)** red | decoded (`CLASS_DEFAULTS.md:264`) |
| headlight material slot | `HeadLightMaterialIndex` = **5** | decoded (`CLASS_DEFAULTS.md:142`) |
| tail lights | lens flares `Batmobile_brakelights`, `Batmobile_brakelights_alwaysOn` exist | decoded asset names (`CLASS_DEFAULTS.md:122,123`) |
| interior light after exit | `InteriorLightsSwitchedOn = 0` on the driver-left path | decoded (`COLLISION_SELECTOR3.md:53`) |
| arrival-specific light cue | **none decoded** | — |

The honest reading: the car has **forcible headlights** and **two colour presets**, and the mode
ticks drive them; **no file says the summon switches them on**, so an "arrival lights" cue in JC3
would be a **new choice**, not a translation.

## 6. Sound on arrival

| moment | BmAK event | evidence |
|---|---|---|
| press | `Engine.Play_Gauntlet_Batmobile_Call` | `GADGET_PARAMS.md:60` |
| cancel | `Play_Remote_Gadget` / `Play_Remote_Gadget_Off` | `GADGET_PARAMS.md:61,62` |
| approach | the engine bed itself: `Play_Batmobile_Positional` (55 WEMs), `Play_Batmobile_DistantRev` (5), `Play_Batmobile_Clutch` (5), reverse bed when backing | `AUDIO_FEATURES.md` §engine; `engine-audio-layers-plan.md` §3 |
| the stop | `Play_Batmobile_Skid_OneShot_Brakes` / `_Burnout` (4 rows each) | `AUDIO_FEATURES.md` §movement/burnout |
| engine running after arrival | `Play_Batmobile_Idle` (5 WEMs), `Play_BML_Persistent_idles` (2) | `AUDIO_FEATURES.md` §engine |
| a dedicated arrival sting | **none** in the 18 engine events or any other group | `AUDIO_FEATURES.md` §engine/§other |

There is **no horn and no arrival chime** in BmAK's audio map (`horn` group = 0 rows,
`AUDIO_FEATURES.md` §Feature groups), so the arrival sound is the engine bed plus the brake skid,
nothing else.

## 7. Where it stops

| question | decoded answer | status |
|---|---|---|
| stop style | skid stop: `bSkidToStop`; native `SkidToStop` writes `SkidToStopDir` (0x3B1) | decoded field/native (`NATIVE.md:119,134`) |
| stop trigger | `DestReachedSkidToStop` (function on `RVehicleBatmobile`) | decoded name (`PACKAGES_G305.md:565`) |
| stop purpose | the player can then use `GetInRemoteMoveFront` / `GetInRemoteMoveBack` / `HighSpeedPickupMove` / `JumpInBatmobileSkidStopMove` | decoded move names (`CLASS_DEFAULTS.md:89,90,99,91`) |
| stop distance / radius | **UNKNOWN** | behaviour bodies, no values |
| stop orientation | front/back entry moves imply it presents a side/front to the player; angle **UNKNOWN** | move names only |
| car left running? | the remote flag `Batman_Remote_Control_Batmobile` is cleared on driver enter, i.e. the call state ends when the player gets in | decoded flag write (`COLLISION_SELECTOR3.md:268,316`) |

So BmAK stops **beside the player, skidding, with the remote-call flag still set** until the player
enters. The numeric standoff is not in the data.

---

## 8. JC3 comparison and the reuse decision

### 8.1 The two JC3 spawn systems

| system | what it does | decoded facts |
|---|---|---|
| **Rebel Drop** | a menu item spawns the entity **at a drop marker** | `Item.Name` = 32-bit Jenkins hash of the entity **leaf**; that hash is the whole spawn binding; 196 vanilla items / 80 vehicle drops; `RebelDropTimer` 60/600/900/1200/1500/1800/2400/2700 (unit UNKNOWN, consistent with seconds); no cost field; 185/196 items resolve to an `.ee` (`REBELDROP.md` §§2-4) |
| **mission / world spawn** | spawn tables + mission spawners place vehicles in the world | `settings/spawn_vehicle_defs.bin` = **86 records** (entity path + tag list + name), pool table names it *Ground Vehicles*; `spawn_budget_pools.bin`; `CVehicleRule` carries `chance`, `heat_level`, `spawn_event` (all 0); mission graphs include `graphs/spawner_group_tracker.gdc/.gsc` and 37 random-encounter graphs (`TRAFFIC.md` §2; `DAMAGE_MECHANISMS.md:46-47`; `GADGETS_HACK_TRACK.md:137`) |

Neither system **drives a vehicle to the player**. JC3 has no decoded call-to-player, and the
Rebel Drop delivery is anchored to the marker, not to Rico.

### 8.2 Element-by-element reuse

| BmAK element | JC3 carrier | reuse? | the values to write |
|---|---|---|---|
| "the called car exists" | **Rebel Drop entry, already built** (B-13): `Name = UIName = 443190071`, `UIDescription = 1805638565`, `UIDisplayOrder 12`, `UIImagePath = v0300_car_kensington_sportsmuscle_batmobile`, task `1361701860` reward | **REUSE (built)** | keep `Type 1`, `UIType 3`, `UIFlag 5`, `Rewardable 1`; **`RebelDropTimer 1800`** as the call cooldown (the only seconds-shaped field) |
| trigger (LB / E) | JC3 has no gadget-wheel call; the closest existing inputs are the drop menu and `ACCELERATE/REVERSE/TURN` pads | **no reuse** — needs a new input path (native hook or a menu entry) | none decoded; the call press has no JC3 equivalent |
| call sound `Play_Gauntlet_Batmobile_Call` | JC3 `vehicles` bank has **no call event**; horn is a per-model `SAttachedEffect` (178/178 donor vehicles, 19 GUIDs) | **no reuse**; the sound must be a donor sample or a new bank entry (blocked: no FSB5 writer — `engine-audio-layers-plan.md` §6.3) | — |
| drive-in route | JC3 AI vehicles exist (traffic rules, `CVehicleRule`), but **no "drive to player" path** is decoded; `spawner_group_tracker` spawns groups, not pursuits | **no reuse** — blocked on AI orders | — |
| avatar hand-off | JC3 has no remote entry move; the player enters a spawned car normally | **no reuse** | — |
| stop-beside-player | the drop marker's spawn transform is the closest anchor (B-13 has no offset field; position is the marker's) | **partial** — the marker is the only anchor | marker transform; offset **UNKNOWN** |
| arrival lights | `VehicleDynamicLights`: **3,217 entries / 223 vehicles**, behaviours `HeadLight` 1027 / `TailLight` 301; `SVehicleLights` on 5 entities | **REUSE** — copy a donor's headlight entry onto the Batmobile | `HeadLight` behaviour; the BmAK colour presets have no JC3 member (JC3 entry carries `diffuse.RGB`, no "pursuit/battle" pair) |
| approach + stop sound | `vehicles` bank engine/skid samples; the project already maps engine layers (`engine-audio-layers-plan.md`) | **REUSE (payload swaps only)** | engine bed slots (§6.1 there); skid sample slot by name |
| call prompt / HUD | JC3 frontend list entry + notification; no decoded prompt hook | **no reuse** | — |
| cooldown | **`RebelDropTimer`** is the only time field in the whole drop system | **REUSE** | **1800 s** (B-13's value; vanilla range 60–2700) |

### 8.3 What "matching BmAK's timing" can mean, with the arithmetic

BmAK's call delay is **UNKNOWN**, so the schedule below is **derived from the one decoded speed
ceiling**, not quoted from BmAK. It is the only defensible timing bridge:

```
ceiling v = SVehicle.MaxSpeed = 4000 cm/s = 40.0 m/s
t_arrive = d / v          (ignore acceleration, ignore the skid ramp)

d =  30 m -> 0.75 s     d = 100 m -> 2.50 s
d =  60 m -> 1.50 s     d = 150 m -> 3.75 s
d = 250 m -> 6.25 s     d = 400 m -> 10.00 s
```

With the boost allowed (`SelfDriveAllowBoost=True`) the approach could be shorter, but BmAK gives
no self-drive boost usage, so the **40 m/s** figure is the floor on arrival time, not a target.

The only **decoded arrival-adjacent timing in BmAK** is the *Batwing vertical drop* (a different
delivery, named as a separately-proposed row, T-WLD22):

| event | timing | source |
|---|---:|---|
| `Batmobile_Vertical_Rescue_In` sequence | **7.233 s** | `ANIMATIONS.md:333-336` |
| `Batwing_Rescue_01` sequence | **4.933 s** | same |
| `Batmobile_Vertical_Rescue_Out` sequence | **4.400 s** | same |
| notify `DropBatmobile` | **0.488 s** | `ANIMATIONS.md:1260-1268` |
| notify `CheckDropBatmobile` | **1.868 s** | same |

If the port uses the **drop** instead of the drive-in, these are the values to match (the car is
released at 0.488 s and its landing is checked at 1.868 s, inside a 7.233 s in-animation). They do
**not** apply to the ground summon, and mixing them in would be inventing timing.

### 8.4 Which JC3 system to actually use

1. **Keep B-13's Rebel Drop entry as the summon's identity and cooldown** — it is already built and
   checked (197 items, hash 443190071, task 1361701860), and it is the only JC3 path that spawns a
   chosen `.ee` from a menu.
2. **Do not add a `spawn_vehicle_defs.bin` record for the Batmobile.** That table is the *traffic*
   roster (86 records, `civilian_01` only for `v0300`); a drop binds by leaf hash and needs no spawn
   record (`REBELDROP.md` §7; `TRAFFIC.md` §2). Adding one would put AI Batmobiles on the roads.
3. **Lights: reuse `VehicleDynamicLights` `HeadLight`** (3,217 entries, 1,027 `HeadLight`), not a
   new light system; the colour stays the donor's because JC3 has no pursuit/battle preset pair.
4. **Audio: reuse the engine bed** and the brake skid one-shot; the call sound has no JC3 carrier
   and cannot be added without an FSB5 writer.
5. **Drive-in arrival remains blocked**: no JC3 system takes an AI vehicle order to a player
   coordinate. Until that exists, the honest JC3 behaviour is the **drop at a marker near the
   player**, not the BmAK drive-in.

---

## 9. Checks run

| check | result |
|---|---|
| bind names re-read (`EnterCallBatmobile`, `pCallBatmobile`, `kCallBatmobile`) | E and {PAD_LB}, `CONFIG2.md:284,291,319,359,394,397` |
| gadget class census re-read | 48 members; 23 value slots; 25 behaviour; `CallSound` at 0x948 |
| self-drive capability values re-read | `SelfDriveAllowBoost=True`, `SelfDriveCanJumpDown=True`, `SelfDriveRoadObstacleTypes` word 0xfe |
| speed ceiling | `SVehicle.MaxSpeed` 4000.0 cm/s; `BattleModeMaxSpeed` 1200.0 (excluded) |
| stop fields | `bSkidToStop`, `SkidToStop` → 0x3B1, `DestReachedSkidToStop`, `SkidToStopJumpIn` |
| light fields | `ForceHeadlightsSwitchedOn` 0x20000; pursuit 1,1,1,1; battle 25,0,0,1; `HeadLightMaterialIndex` 5 |
| JC3 drop facts | 196 items / 80 vehicle drops / `RebelDropTimer` set 60–2700 / hash binding / 185 resolve |
| JC3 spawn facts | 86 records, entity path + tag list + name, pool table *Ground Vehicles* |
| built entry facts | 197 items, 443190071, timer 1800, reward task 1361701860 (B-13) |
| §8.3 arithmetic | `t = d/40 m/s` at six distances — 0.75, 1.50, 2.50, 3.75, 6.25, 10.00 s |
| delivery timings | 7.233 / 4.933 / 4.400 s, notifies 0.488 / 1.868 s |

## 10. Change record (per `AGENTS.md`)

1. **Intended change:** add one report documenting the BmAK summon and the JC3 carriers, with the
   reuse decision and the timing values.
2. **File:** `tmp/freebuff/reports/summon-and-arrival-plan.md` (this file). Correct file because the
   brief names it and every comparable plan lives in `tmp/freebuff/reports/`; no `Research/` file is
   regenerated and no build/table is written.
3. **Revert:** delete this file. Nothing else changed: no `item.onlinec`, spawn table, entity,
   bank, module, ledger or install was modified.

## 11. UNKNOWNs

| # | UNKNOWN | what settles it |
|---|---|---|
| U-1 | call delay, spawn distance, stop radius, self-drive speed cap | the 25 `RBatmobileRemoteBm` behaviour bodies (`GADGET_PARAMS.md` §"25 behaviour members"): untagged, no bytecode, no constants in the shipped packages |
| U-2 | whether the call switches the headlights on (`ForceHeadlightsSwitchedOn`) | the same function bodies, or a frame-by-frame look at a call in footage |
| U-3 | the call sound's duration/WEM and whether it exists in the grabbed banks | `Engine.Play_Gauntlet_Batmobile_Call` outer package is not in the bank grab (`GADGET_PARAMS.md` §"7 UNKNOWN"); needs the `Ww_CHR_BatmanGauntlet` bank |
| U-4 | whether a `RebelDropTimer` value is seconds | the field name and 60–2700 shape only; `REBELDROP.md` §8 |
| U-5 | whether JC3 can spawn a vehicle at the player at all | untested; closest documented path is the drop marker (`bmak-feature-completeness-audit.md` §2 U-1) |
| U-6 | whether a mission spawner can be ordered to drive to a coordinate | no decoded member carries a destination for an AI vehicle (`GADGETS_HACK_TRACK.md:137`) |
| U-7 | which startup package's call-sound path is live (`Engine.` vs `Ww_CHR_BatmanGauntlet.`) | load order, not recorded in the files read (`GADGET-params.md` §UNKNOWN 4) |

No game process was started; no install, dropzone, bank, build, profile table or ledger was written.
All values above are static decodes, or derivations whose arithmetic is printed.
