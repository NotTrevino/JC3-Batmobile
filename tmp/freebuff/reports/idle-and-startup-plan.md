# Getting in: the enter-and-start sequence

2026-11-06. Question: what happens, in what order and at what times, when the player gets into the
BmAK Batmobile - lights, screens, sounds, engine start - and which JC3 enter hooks can fire each?

**Answer in one paragraph.** BmAK's entry is four measured clips, not one script: the canopy
(`Cockpit_Open`, **0.433 s** / `Batmobile_V2_Cockpit_Open`, **0.300 s**), the seat unfolding
(`Batmobile_V2_Chair_Open`, **2.233 s**), the seat folding back (`Batmobile_V2_Chair_Close`,
**2.267 s**) and the canopy closing (`Cockpit_Close`, **0.500 s** / V2 **0.300 s**). Each clip carries
its sound as an `AnimNotify_Sound` at a known time inside the clip, so the audio is pinned to the
animation, not to a script. The engine is a separate audio transition
(`Play_Batmobile_Engine_Transition_In`) whose `Startup` RTPC curve is **silent at 0, full at 1**, with
a parallel idle bed that is **muted at 1** - i.e. `Startup` is the switch between "cranking" and
"running". The HUD is a module with `Intro` / `In` / `FirstBootUp` labels and a health bar
`Intro`/`IntroDelayed`; which one plays on entry is native. JC3's half is three hooks and none of them
carries a time: `entry.driver` -> `S_ENTER_DRIVER_VEHICLE` (the character state), the door hinge in
`door_parts[]` (no authored curve - "a hinge with no curve, driven by whatever runs after
`S_ENTER_DRIVER_VEHICLE`"), and the native vehicle HUD/audio start. So the **order comes from BmAK's
clip lengths; every JC3 time is UNKNOWN and has to be authored or observed**.

Labels: `decoded` = read in the file cited; `derived` = arithmetic on decoded values; `authored` =
our composition, in neither game.

## 1. What BmAK measures (decoded)

`Research/BatmobileGrab/ANIMATIONS.md` §4 (sequences) and §7 (notifies), identical in all four
Batmobile packages.

| clip | frames | length | notifying sound | notify time | note |
|---|---:|---:|---|---:|---|
| `Cockpit_Open` (`BM_Batmobile_Chassis`) | 14 | **0.433 s** | `Play_CockpitOpen` | 0.007150 s | canopy |
| `Cockpit_Open_Idle` | 2 | 0.033 s | - | - | hold pose |
| `Cockpit_Close` | 16 | **0.500 s** | `Play_CockpitClose` | 0.005950 s | canopy |
| `Batmobile_V2_Cockpit_Open` (`Pose_States`) | 10 | **0.300 s** | `Play_CockpitOpen` | 0.001668 s | pose variant |
| `Batmobile_V2_Cockpit_Close` | 10 | **0.300 s** | `Play_CockpitClose` | 0.000007 s | pose variant |
| `Batmobile_V2_Chair_Open` | 68 | **2.233 s** | `Play_Chairs_Out` | 0.022186 s | seat unfolds |
| `Batmobile_V2_Chair_Close` | 69 | **2.267 s** | `Play_Chairs_In` | 0.092926 s | seat folds |
| `Batmobile_V2_Back_Door_Open` | 31 | 1.000 s | `Play_Boot_Open` | 0.000804 s | rear/boot bay, **not** the entry |
| `Batmobile_V2_Back_Door_Close` | 29 | 0.933 s | `Play_Boot_Close` | 0.000000 s | rear/boot bay |
| `Batmobile_V2_Idle` | 2 | 0.033 s | - | - | seated idle pose |

`derived`: frames / 30 fps. The five sounds are AkEvents in the `Ww_BML_Batmobile` bank, repeated on
all four `Playable_Batmobile*` packages (`AUDIO.md` rows 77-78, 168-169, 256-257, 348-349).

**There is no authored "entry" clip for the player.** The `driver/Batman` set holds exits and
stand-outs (`BatMobile_Stand_Out`, `…_Roof`, `…_Roof_Bak`, 236-245 frames / 7.8-8.1 s), not a get-in.
The get-in is the character's state machine, exactly as in JC3 (`SEAT.md` §2). So BmAK's in-car
sequence is the **car's** half only: canopy, seat, sounds, engine, HUD.

## 2. The order, and the timeline

The clips are independent; what orders them in BmAK is native (anim blueprint / Kismet). The order
below is a **composition from the measured lengths** (`authored`), not a playback trace. Two facts
constrain it: the seat cannot fold while the player is still outside, and the canopy cannot close
before he is in.

| t (s) | event | evidence |
|---:|---|---|
| 0.000 | canopy starts to open | `Cockpit_Open` 0.433 s / V2 0.300 s |
| 0.002 | `Play_CockpitOpen` | notify in V2 clip; 0.007 in the Chassis clip |
| 0.022 | seat starts unfolding, `Play_Chairs_Out` | `Chair_Open` 2.233 s, notify at 0.022 |
| 0.300 / 0.433 | canopy fully open | clip end |
| 2.255 | seat fully unfolded, player seated | `Chair_Open` ends |
| 2.300 | engine transition begins, `Startup = 1` | §3 |
| 2.300 | seat starts folding, `Play_Chairs_In` at 2.393 | `Chair_Close` 2.267 s, notify +0.093 |
| 4.567 | seat locked | `Chair_Close` ends |
| 4.600 | canopy starts to close, `Play_CockpitClose` | `Cockpit_Close` 0.500 s |
| 5.100 | canopy shut, car ready | clip end |

Two variants are legitimate: the **short** one (V2 canopy, 0.300 s) reads 0.000 open / 2.255 seat /
4.567 seat-in / 4.600 close / 5.100 ready; the **long** one (Chassis canopy, 0.433 s) adds 0.133 s to
the first beat only. The rear/boot door (1.000 s / 0.933 s) is not part of entry - it is the engine
bay, and nothing in the files ties it to `S_ENTER_DRIVER_VEHICLE`.

## 3. Engine start

The engine is not an "engine start" one-shot; it is a **transition event plus a running bed**, both
in `BML_Engine` / `VEH_Batmobile_MK2_Engine`:

| event | RTPC | curve | reads as |
|---|---|---|---|
| `Play_Batmobile_Engine_Transition_In` | `Startup` | 0 -> **-1**, 1 -> **0** | silent at `Startup` 0, full at 1 |
| `Play_Batmobile_Engine_Transition_Out` | `Startup` | same | same |
| `Play_BML_Persistent_idles` | `Startup` | 0 -> **0**, 1 -> **-1** | **audible at 0, muted at 1** |
| `Play_Batmobile_Idle` | none | - | running bed, no RTPC |
| `Play_Batmobile_Positional` | `Startup` | 0 -> -1, 1 -> 0 | positional layer follows the switch |

`decoded`: `AUDIO_FEATURES.md` 201-213, `ENGINE_AUDIO_PAIRS.md` §`Play_Batmobile_Engine_Transition_In`
(`Startup` range 0..1, 1 curve) and `AUDIO_BANKS.md` (`BML_Batmobile_Subjective` `Startup` container,
712,059 B). `derived`: the two `Startup` curves are complementary, so the parameter is a **crossfade
between the cranking/idle layer and the transition layer**, not a boolean; setting it to 1 completes
the start, 0 returns to idle.

**How long the transition audio lasts is UNKNOWN.** The event is an actor-mixer over 52 WEMs; the wav
table gives per-sample lengths (1-18 s) but no event length or crossfade time, and no file states
when native sets `Startup`. `Play_Batmobile_Idle` is the only event with no RTPC at all, so it is the
one layer that can be started blind.

## 4. Lights on entry

`LIGHTS.md` gives the lamp inventory and nothing about when they turn on:

| type | entries on the Batmobile packages |
|---|---:|
| `VEHLT_HeadLight` | 46 |
| `VEHLT_BattleModeLight` | 16 |
| `VEHLT_ForensicsLight` | 12 |
| `VEHLT_TailLight` | 8 |
| `VEHLT_Interior` | 4 |
| `VEHLT_BootLight` | 3 |
| type stripped by the cooker | 12 |

The interior entry is real and named: `Dashboard_Light` on `Batmobile_Chassis`,
`VEHLT_Interior` -> `VEHLTMAT_Interior`, bound through the same
`deformable_transform` chain as the headlights (`LIGHTS.md` row 68). The boot lamps are
`VEHLT_BootLight` (3). **No member in the package says "on at entry"**: there is no state machine, no
delay, no auto rule; `enabled` is a component flag, and which state the game starts it in is
**UNKNOWN**.

So the light half of the order is **authored**: dashboard/boot at 0.300 s (canopy open), headlights
with the engine transition at 2.300 s, battle-mode lamps only when battle mode is entered (they are a
separate `VEHLT_BattleModeLight` group with 16 entries - see the `BattleModeSpotLight` row).

## 5. Screens on entry

The HUD is a module, not part of the car, and it carries explicit entry labels:

| thing | value | evidence |
|---|---|---|
| module | `HudModuleBatmobile` / `ModuleStruct_Batmobile`, **51 frames @ 30 fps = 1.700 s** timeline, 1024x768 surface on a 1024x720 stage | `HUD.md` §4 |
| entry labels | `Intro`, `In`, `FirstBootUp`, `Initial`, `Prototype` | same |
| health entry | `Intro`, `IntroDelayed`, plus `Outro`; `Delayed` is the battle-forced variant | `HUD.md` §4 |
| bar sweep | `MaxHealthChangePerFrame = 0.05` at 30 Hz -> **0.667 s** empty to full | `HUD.md` §4.1 |
| bar timeout | `GoOffscreenTimer = 2` s | same |
| module visibility | `UC_SetSelectiveVisibilityModule(name)` in every module; container `ModularHudBm3` loads/unloads | `HUD.md` §4-§5 |

`FirstBootUp` is a distinct label from `Intro`, so the movie distinguishes a first-ever boot from a
normal entry - but **which label the native module plays on a given entry is UNKNOWN** (the setter
that would choose it is not in the 37 `UC_*` names). The 1.700 s is the whole module timeline, not the
length of `Intro`; ffdec gives frame counts, not per-label playback.

Screens in the cabin (dashboard displays) are geometry with `VEHLT_Interior` lighting, not a HUD
element; their power-on is not in any decoded file.

## 6. JC3 hooks that can fire each beat

| beat | JC3 hook | where | what it can carry | timing |
|---|---|---|---|---|
| player commits to entering | input action `ENTER_VEHICLE` | `INPUT.md` 73 (RPADUP / **E**), `DRIVE_CARRIERS.md` 183 | nothing by itself; it runs the interaction | press |
| interaction chosen | `entry.driver` (`CInteractionGraphEntry`, state `S_ENTER_DRIVER_VEHICLE`) | `INTERACTION.md` 40, `SEAT.md` §1 | the state string the character machine consumes; box at container origin | none in file |
| fast/stunt variant | `entry.driver.side.fast` -> `S_ON_GROUND_TO_ENTER_DRIVER_SIDE_VEHICLE`; `entry.stunt.to.driver.side.enter.vehicle` -> `S_ENTER_STUNT_TO_TRANS_ENTER_VEHICLE_P1` | `SEAT.md` §1 | same, different state | none |
| no-door variant | `entry.driver.no.door` -> `S_ENTER_DRIVER_NO_DOOR_VEHICLE` | `DOORS.md` §4 | same | none |
| player lands in seat | `point.driver` = **(-0.440, 0.340, 0.200)** | `SEAT.md` §1, `INTERACTION.md` | the attach transform | none |
| door/canopy motion | `door_parts[]` + `hkpLimitedHingeConstraintData` in the `.physicsc` | `DOORS.md` §1-§4 | a limited hinge with **no authored curve**; opening is code | **UNKNOWN** |
| engine audio | `SAttachedEffect` **`engine_running_sound`** (vehicles/146 bank) | `JC3_AUDIO.md` 62, 214 | the engine bed, started by native | **UNKNOWN** |
| lights on | `SVehicleLight` entries (`behavior` HeadLight/TailLight/..., per-part, 3,217 over 223 vehicles) with `enabled` | `LIGHT_SYSTEM.md` §1-§3 | per-lamp values; the switch is native | **UNKNOWN** |
| HUD appears | `InitPrimaryMeter`, `SetVehicleInfo`, `InitVehicleWeapons`, `InitVehicleNitrous`, `UpdateVehicleTurboJump` | `HUD.md` §6, `JC3_HUD_WEAPONS.md` §1-§3 | cluster + weapons; **0 call sites in the movie** - native drives them | **UNKNOWN** |
| any custom effect on enter | `SAttachedEffect` with a value/event usage (`SValueDrivenEffectUsage` 527, `SEventDrivenEffectUsage` 233 objects); the only decoded usage string is `Fire` (hash 4131019937) | `ENTITIES.md` 34/48/50, `FX13_CASINGS.md` 94-104 | a new enter effect would need an authored usage name; no "Enter" usage is decoded | **UNKNOWN** |

**The pattern:** JC3 has the *event* (`S_ENTER_DRIVER_VEHICLE` via `entry.driver`) and the *carriers*
(attached effect, light entries, HUD setters), but no member that says "at this event, after this
many seconds, do X". Every time in the JC3 column is either absent or native. That is the same gap
`EJECT_MAP.md` records for exit, and why the enter control stays JC3's (`ENTER_VEHICLE`, rule D-11).

## 7. Timing table we use

`measured` = BmAK clip/notify; `authored` = our JC3-side composition; `UNKNOWN` = not in either file.

| beat | time | source | JC3 carrier |
|---|---:|---|---|
| press enter | 0.000 | input | `ENTER_VEHICLE` |
| canopy begins | 0.000 | measured clip start | door part hinge / canopy part |
| `Play_CockpitOpen` | 0.002 | measured notify | audio event on the enter state |
| seat begins | 0.022 | measured (`Chairs_Out` notify) | `point.driver` + character state |
| canopy open done | **0.300** (V2) / **0.433** (Chassis) | measured length | hinge end |
| seated | **2.255** | measured (`Chair_Open` 2.233 + 0.022) | `PPC_ARRIVED_AT_DRIVER_SEAT` (character side) |
| engine transition, `Startup` 1 | 2.300 | authored; event + curve decoded | `engine_running_sound` attached effect |
| seat in begins | 2.300 | authored; notify at +0.093 | seat/harness parts if any |
| seat locked | **4.567** | measured (`Chair_Close` 2.267 from 2.300) | - |
| canopy close begins | 4.600 | authored | hinge |
| canopy shut | **5.100** | measured (`Cockpit_Close` 0.500) | - |
| HUD `Intro` | 0.300 | **authored**; labels decoded, playback native | `InitPrimaryMeter` / `SetVehicleInfo` |
| dashboard light on | 0.300 | **authored**; lamp + material decoded, switch native | `SVehicleLight` `Dashboard` entry |
| headlights on | 2.300 | **authored** | `SVehicleLight` `HeadLight*` entries |

Cross-check the arithmetic: 0.022 + 2.233 = 2.255; 2.300 + 2.267 = 4.567; 4.600 + 0.500 = 5.100.
The 0.043 s between 2.255 and 2.300 is slack, not a measured gap.

## 8. What we set, and what stays out

- **Reuse JC3's enter control and graph**: `ENTER_VEHICLE`, `entry.driver` ->
  `S_ENTER_DRIVER_VEHICLE`, `point.driver` at (-0.440, 0.340, 0.200). No new interaction.
- **Canopy**: the donor has no canopy part; the actionable form is the one `DOORS.md` §4 gives - an
  X-axis limited hinge on a `Hood`/`FrontLeftDoor`-class part listed in `door_parts[]`, plus the
  `entry.driver` path. The 0.300 s / 0.500 s travel is BmAK's animation, not a JC3 curve: JC3 has no
  open angle stored, so the speed is native until proven otherwise.
- **Sounds**: `Play_CockpitOpen` / `Play_CockpitClose` / `Play_Chairs_Out` / `Play_Chairs_In` at their
  measured notify times; engine via the `Startup` crossfade, not a one-shot. All five are BmAK bank
  events and must be authored into the Batmobile's private bank (no JC3 event of those names exists).
- **Lights**: dashboard at 0.300 s, headlights at 2.300 s - both authored, because neither game
  stores an auto-on rule.
- **HUD**: `Intro` on entry, `FirstBootUp` only on the first entry in a session - authored mapping,
  since the movie's own label choice is native.
- **Out**: the rear/boot door (engine bay, not entry), battle-mode lamps (battle mode only), and any
  numeric JC3 enter-camera blend (not decoded anywhere).

## 9. Checks and limits

- clip lengths and notify times: `ANIMATIONS.md` §4/§7, re-derived from frames at 30 fps.
- sounds: `AUDIO.md` (the five events on all four packages), `AUDIO_FEATURES.md` 201-213,
  `ENGINE_AUDIO_PAIRS.md` (Startup curves), `AUDIO_BANKS.md` (`Startup` container).
- lights: `LIGHTS.md` type counts and the `Dashboard_Light` row.
- HUD: `HUD.md` §4/§4.1/§5 (labels, 51 frames, sweep, offscreen).
- JC3: `INTERACTION.md` 40, `SEAT.md` §1, `DOORS.md` §4, `INPUT.md` 73, `JC3_AUDIO.md` 62/214,
  `LIGHT_SYSTEM.md`, `JC3_HUD_WEAPONS.md` §1-§3, `ENTITIES.md`, `FX13_CASINGS.md`.
- **UNKNOWN**: BmAK's actual playback order and blends, the engine transition's length, the HUD
  label the native module picks, every JC3 time (door swing, camera blend, audio start, HUD), and
  whether JC3 accepts an authored enter usage. Nothing was launched; only `Research/` was read.
