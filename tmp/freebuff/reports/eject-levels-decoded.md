# Eject levels: what BmAK stores, what JC3 can carry, what the hook must do

**STATUS: done (report only).** No build tree, entity, `.epe`, parts file, ledger row or queue brief was
written or edited; nothing was launched.

**Provenance / revert.** New file `tmp/freebuff/reports/eject-levels-decoded.md`
(= `E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/eject-levels-decoded.md`), the output path the brief names;
every comparable plan lives in `tmp/freebuff/reports/`. **Revert = delete this file.**

Labels: **decoded** (file:line / offset), **derived** (rule + inputs), **UNKNOWN** (tried, where it would be).

---

## 0. The answer in six lines

| question | answer |
|---|---|
| does BmAK have charge levels? | **yes, three** — `EBatmobileEjectType`: `EBET_NormalEject` = 1, `EBET_SuperEject1` = 2, `EBET_SuperEject2` = 3 (plus `EBET_None` = 0). This matches the operator's three outcomes exactly (double-tap lowest, charged tap higher). |
| is the level *chosen* by a charge timer? | **UNKNOWN.** No charge/hold field exists in any decoded class; the only time store in the eject body is `LastEjectFromBatmobileTime` (a timestamp), and the body's float constants are `[1.0, 600.0, 0.0, 1.0, 1.0]` — **no sub-second window**. |
| what is the eject impulse in BmAK? | **not a velocity.** The only velocity write in `DrivingMode.EjectFromVehicle` is `SetRBLinearVelocity((0,0,0), false)` on the **car's** mesh (a *stop*). The launch is `TriggerSpecialMove(self, Loc, …)` into a move called `Eject.*_To_Glide`. Its trajectory numbers are **not in `BmGame.upk`** (UNKNOWN). |
| the one decoded height | `RVehicleBatmobileBase.EjectUpDist` = **1300.0** (f32 @6032 / `0x1790`), class default. Unit statement absent → 13 m only if the class is cm (**derived**, unproven). |
| what JC3 member takes a level? | **none.** 4,832 exits in 232 graphs use 9 keys and **0** carry velocity/impulse/launch/force. The only exit that matches "at speed with a parachute" is `exit.driver.moving.parachute` → `S_EXIT_VEHICLE_PARA`, gate `(5.0, 999.0)` — one state, **not three heights**. |
| who must pick the level at runtime? | **the native hook** — it reads the hold, then either selects one of three authored `point.driver` exit offsets (data exists) or writes the leaving character's vertical velocity itself (no JC3 member exists). §4. |

---

## 1. BmAK side, decoded

### 1.1 The level enum (the "three levels" are real)

`Working/vendor/BmSDK/RVehicleBatmobileBase.g.cs:3839-3843`:

```
EBET_None          = 0
EBET_NormalEject   = 1
EBET_SuperEject1   = 2
EBET_SuperEject2   = 3
EBET_MAX           = 4
```

| member | class | offset | type | value | evidence |
|---|---|---:|---|---|---|
| `MaxEjectType` | `RVehicleBatmobileBase` | 5902 (`0x170e`) | `ByteProperty` (enum) | class default **`EBET_NormalEject`** | `BmSDK…RVehicleBatmobileBase.g.cs:6821-6825`; `CLASS_DEFAULTS.md:220` |
| `BoostingOut` | `RVehicleBatmobileBase` | **5901** (`0x170d`) | same enum | no class default | `…g.cs:6814-6816` |
| `OverrideNextEject` | `RVehicleBatmobileBase` | 5604 | `ObjectProperty` → `BmSDK.BmGame.RSeqAct_OverrideBatmobileEject` | absent | `…g.cs:6373-6375` |
| `EjectUpDist` | `RVehicleBatmobileBase` | 6032 (`0x1790`) | `FloatProperty` | **1300.0** | `…g.cs:7004-7006`; `CLASS_DEFAULTS.md:143`, `:454` |

Two facts fall straight out and both matter:

1. **The shipped Batmobile is capped at the lowest level.** `MaxEjectType`'s class default is
   `EBET_NormalEject` (1), and the archetype carries no override (`bmak_chain` prints
   `archetype=absent`), so **levels 2 and 3 are never reachable in the shipped car** — a build that wants
   the operator's charged eject must raise `MaxEjectType`, which is a BmAK-side *statement of intent*
   (JC3 has no such byte; §5).
2. **`BoostingOut` sits at exactly `MaxEjectType − 1`** (5901 vs 5902) in the same enum. It is the
   per-eject "this eject came from boosting out" flag, and the eject body references it **6 times**
   (`+332, +338, +388, +394, +457, +463`) — a decoded adjacency, its branch role **UNKNOWN**.

### 1.2 The five move references (what each level actually plays)

All are `RSpecialMoveConfigConfigurable` objects, one per eject flavour (`CLASS_DEFAULTS.md:87, 88, 93,
94`; `COLLISION_WHERE.md:101`):

| field | offset | asset | when the field name says it is used |
|---|---:|---|---|
| `EjectUpMove` | 8416 | `Eject.Eject_Up_To_Glide` | straight up |
| `EjectForwardMove` | 8424 | `Eject.Eject_Fwd_To_Glide` | forward |
| `EjectWhenBatmobileVerticalMove` | 8464 | `Eject.Abseil_Eject_To_Glide` | car vertical (wall/abseil) |
| `EjectUpWhenBatmobileVerticalMove` | 8472 | `Eject.Abseil_Eject_Up_To_Glide` | car vertical, upward |
| `EjectToSpotMove` | 8496 | `Eject.Eject_To_Spot` | to a scripted spot; archetype holds object ids **[3178, 5277, 5328, 5363]** — one per Batmobile variant (`JokersBatmobile` 3178, `Playable_Batmobile_SF.Batmobile` 5277, `Batmobile_MK2` 5328, `BatmobileFunhouse` 5363) |

So "hold, then tap to go higher" is expressed as **which move plays** (`Eject_Up_To_Glide` vs a super
variant), not as a stored velocity. **The move's own distance/velocity numbers are not in `BmGame.upk`**
(`EJECT_VELOCITY.md` §5: 50 eject/velocity entries, 0 with a mode id) — UNKNOWN, and it is the same
UNKNOWN the whole MOD-3 work already carries.

### 1.3 The eject body, and what it does *not* contain

`DrivingMode.EjectFromVehicle`, export **104931**, **1297** script bytes (`EJECT_VELOCITY.md` §4):

| at | call | decoded content |
|---|---|---|
| +3 | `CantEjectFromBatmobile` | guard |
| +173 | `CheckSpaceAboveBatmobileCockpit` | space check — the ceiling test the "hold A to go higher" needs |
| +365 | `DriverLeave` | `(true, FFInRange)` — the pawn actually leaves |
| +424 | `RemoveBatmobileBindsAndSetBatmanBinds` | input handover |
| +443 | `PlayCockpitOpenFast` | canopy |
| +513 | `SetRBLinearVelocity` | `(0,0,0)`, `bAddToCurrent=false`, on `Car.Core.Mesh` — **a stop, not a launch** |
| +1103 | `TriggerSpecialMove` | `(self, Loc, <0x4A>)` — the launch |
| +1238 | `ClearTimer` | |
| +1273 | `LastEjectFromBatmobileTime = WorldInfo.TimeSeconds` | a timestamp, not a duration |

**Charge evidence, exhausted.** A hold-charge needs either a float "charge time" field or a sub-second
constant compared against `TimeSeconds`. `bmak_chain.py --grep 'Eject|Launch|Charge|Glide|Jump'` returns
**13 eject-named fields and 0 charge-named ones** (§6 command log), and the body's float constants are
`[1.0, 600.0, 0.0, 1.0, 1.0]` with `600.0` reading as a distance threshold. So:

> **The three levels are decoded; the rule that picks one is UNKNOWN.** The candidate the field names
> support is `MaxEjectType` as a *ceiling* written by gameplay (or by `OverrideNextEject` /
> `RSeqAct_OverrideBatmobileEject`), and `CurrentEjectType` (read at `+343`) as the *choice*. Which input
> gesture sets `CurrentEjectType` is in the input/`RSeqAct` layer, not in `DrivingMode` — no file on this
> machine binds a hold to it (`EJECT_MAP.md` §3.1: 0 hold/duration/tap words in 145 gamepad + 104 keyboard
> bindings + 249 export rows).

**HUD corroboration that a "super" eject is a first-class state:** the HUD setter `UC_SetSuperEject`
exists alongside the Batmobile weapon setters (`Research/JC3Grab/JC3_HUD_WEAPONS.json`, `targets_setter_names`,
`targets_row`). A UI hook for a super eject is decoded; its parameter shape is not read here (**UNKNOWN**).

### 1.4 The operator's three gestures, mapped as far as the files go

| operator gesture | outcome the operator states | BmAK value that can carry it | status |
|---|---|---|---|
| plain **double-tap** A | **lowest** eject | `EBET_NormalEject` (1) | **derived** — the lowest of the three enum values, and the shipped `MaxEjectType` default |
| **hold, then tap** once | eject **higher** | `EBET_SuperEject1` (2) | **derived** (enum order); which threshold selects it is **UNKNOWN** |
| **hold longer**, then tap | highest | `EBET_SuperEject2` (3) | **derived**; threshold **UNKNOWN** |
| the height itself | — | `EjectUpDist` = 1300.0 (the only decoded distance) | decoded value, unit unstated |
| the second-press window | — | none found | **UNKNOWN** (`LastEjectFromBatmobileTime` is the only time field) |

---

## 2. JC3 side, decoded: the donor has no eject

| claim | evidence |
|---|---|
| 4,832 `CInteractionGraphExit` objects in 232 graphs, 61 names, 26 in the donor | `Research/JC3Grab/EJECT.md` §1 |
| every exit's members come from **9 keys**: `_object_id, disable_event, enable_event, enabled, interaction, modifier, name, name_hash, state` | `EJECT.md` §1; keys outside that set, fleet-wide: **0** |
| members named velocity / impulse / launch / force / speed: **0** | `EJECT.md` §1 |
| the only two moving-sounding graph classes are a **condition** and the car's own pulse: `CInteractionGraphParentVelocityCondition` (4,057) and `CForcePulse` | `EJECT.md` §1 |
| module census over 232 entity dumps: `eject` 0, `parachute` 0, `bail` 0, `catapult` 0, `hold_time` 0; `launch` 30 = fighterjet sockets; `impulse` 12 = `TrainGlobal.crashing_impulse` | `EJECT_MAP.md` §3.1 (byte census) |
| the only upward mechanism in the fleet, `arcade.turbo_jump` (145 land vehicles), jumps the **car** and has no vertical-speed member | `MODLOG.md` G2-20 |
| the exit that matches "leave at speed, then parachute" is `exit.driver.moving.parachute` → `S_EXIT_VEHICLE_PARA`, gated by `ParentVelocityCondition (min 5, max 999)`; below 5 it is `exit.driver.default` → `S_EXIT_VEHICLE`; two more share the high gate: `roll.out` (5..999) and `to.fall` (0..5) | `EJECT.md` §2-§3 |
| the exit's only position is its parent point, `point.driver`, at donor-local **(-0.58, 0.60, 0.39) m** (Batmobile-local, from G2-18's bbox mapping) | `EJECT.md` §2 |
| Rico has the animation and the state, not an action: `rico_vehi_car_low_driver_to_parachute.ban` @727306, `PPparachute_vehicle_eject` @180702, `PPparachute_opened` @399106 in `rico_base.asb`; `S_EXIT_VEHICLE_PARA` @254304, `ACT_EXIT_VEHICLE` @106752, `ACT_STUNT_VEHICLE_EXIT` @151986 in `rico_base.afsmb`; **`ACT_EJECT_FROM_VEHICLE` is absent (0 hits)** | `EJECT_MAP.md` §3.2 |
| input: `STUNT_JUMP` and `OPEN_PARACHUTE` share one control in both tables (shipped `RPADDOWN`, export `A`); no binding carries a hold flag or a duration; `parachuteparams.bin` (344 B) carries asset paths only | `EJECT_MAP.md` §3, §3.1 |

### 2.1 Which JC3 member each BmAK level maps to

| BmAK level | JC3 member that matches | what it gives | what it cannot give |
|---|---|---|---|
| level **1** `EBET_NormalEject` | `exit.driver.default` → `S_EXIT_VEHICLE` (gate 0..5) at `point.driver` | the plain exit | no height above the seat |
| levels **2-3** `SuperEject1/2` | **same exit family**: `exit.driver.moving.parachute` → `S_EXIT_VEHICLE_PARA` (gate 5..999) at `point.driver` | the departing state, and the parachute deploy that goes with it | **one state for both levels**; nothing in the exit varies with a charge |
| the upward distance | **no member**; the nearest data-side knob is the exit's **`point.driver` Y**, which is authored per exit | three exits can carry three Y offsets (`0.60 m` today) | an exit point is a **spawn offset**, not an impulse; it cannot express "eject at 13 m/s" |
| the impulse/velocity itself | **no member anywhere** (0 of 4,832 exits; 0 entity modules) | — | must be applied by the hook |

So the honest mapping is: **level → exit *state* for 1 vs 2-3, and level → an authored exit-point offset
for 2 vs 3**, with the actual vertical velocity pushed by native code. Both halves are consistent with
JC3's own architecture (exits are data, motion is native), and neither requires a member that does not
exist.

---

## 3. What the numbers are, and are not

| quantity | value | label | why |
|---|---|---|---|
| number of levels | **3** | decoded | `EBatmobileEjectType` 1..3 (`EBET_MAX` = 4 is the sentinel) |
| `MaxEjectType` on the shipped car | `EBET_NormalEject` (1) | decoded | class default + `archetype=absent` |
| the height constant | `EjectUpDist` = **1300.0** | decoded value; **unit UNKNOWN** | the class is a UE3 float; cm would be 13 m (derived, unproven) |
| hold time to reach level 2 / 3 | **UNKNOWN** | — | no charge field, no sub-second constant, no bound hold anywhere |
| the second-press window | **UNKNOWN** | — | only `LastEjectFromBatmobileTime` (a timestamp) exists |
| the per-level launch speed | **UNKNOWN** | — | it lives in the `Eject.*_To_Glide` special-move assets, not in the packages read |
| JC3 exit height | 0.39 m below/above seat at `point.driver` Y = 0.60 m | decoded | `EJECT.md` §2 |

---

## 4. What the native hook must do

Minimum surface, in order. Items 1-2 are the *only* things BmAK has that JC3 lacks as data; 3-5 are the
push JC3 cannot express.

1. **Hold-duration read + level pick.** Hook the eject input, measure the hold, and classify into 3 levels
   (thresholds are a build constant, because BmAK's are UNKNOWN). This also **replaces** the double-tap:
   the operator's "plain double-tap = lowest" is a zero-hold press, i.e. level 1.
2. **Exit selection.** Level 1 → `exit.driver.default`; levels 2-3 → `exit.driver.moving.parachute`
   (`S_EXIT_VEHICLE_PARA`). Both already exist on the donor, so this is a *choice among existing exits*,
   not new data.
3. **Exit point per level.** Three authored `point.driver` Y offsets (level 1 = donor's 0.60 m; levels 2-3
   higher by a value the build picks — BmAK's `EjectUpDist` 1300.0 is the only number to start from, so the
   offset ladder is a **build constant**, recorded as such).
4. **The vertical push after `DriverLeave`.** No JC3 member exists, so the hook must write the leaving
   character's linear velocity (or call the parachute-deploy push) at the moment of exit. The address to
   write and the character's velocity member are **UNKNOWN** — `Research/RTTI` has no character velocity
   row read here; settler §6 U3.
5. **Suppress the stock choice.** JC3 decides between `S_EXIT_VEHICLE` / `S_EXIT_VEHICLE_PARA` by the speed
   gate alone (both 5..999, so which wins for `roll.out` vs `parachute` is code — `EJECT.md` §3). The hook
   must make the pick deterministic, or the level is ignored whenever the stock gate disagrees.
6. **Timing/camera after the push**: BmAK's car is *stopped* (`(0,0,0)` on the mesh), JC3's exits carry no
   motion — the stop, and the "car breaks after eject" behaviour, are hook-side (already carried by the
   MOD-3 cards, not re-planned here).

**What the hook must NOT do:** it must not try to author a velocity into an exit (`EJECT.md` §1: 0 of 4,832
carry one) and must not look for an `ACT_EJECT_FROM_VEHICLE` state (`EJECT_MAP.md` §3.2: absent, 0 hits).

---

## 5. Consequences for the ledger

| record | effect |
|---|---|
| `T-MD3` / MOD-3 (eject) | unchanged in shape; this report adds that the **level** is a third dimension on top of "exit + launch", and that JC3's carrier for it is *an exit-point ladder + a hook push*, not a member |
| `NEW-MOD-*` eject-level card (does not exist yet) | this report is its input: three levels, two exit states, one hook push, thresholds as build constants |
| `MaxEjectType` note | the shipped car caps at level 1 — worth a line in the design docs, since it explains why the operator sees only one height in vanilla BmAK |

**COMPROMISES: none.** The level ladder is reachable (three exit points + a hook push); nothing here asks
the operator to accept a wrong height. What is missing is *numbers*, not *mechanism*, and the missing
numbers are labelled UNKNOWN above rather than invented.

---

## 6. Commands run this pass (verbatim, trimmed to the results)

```
python Tools/scripts/bmak_chain.py --grep 'Eject|Launch|Charge|Glide|Jump'
  ## RVehicleBatmobile
     EjectForwardMove @ 8424 archetype=absent class-default=absent
     EjectToSpotMove  @ 8496 archetype=[3178, 5277, 5328, 5363] class-default=absent
     EjectUpMove      @ 8416 archetype=absent class-default=absent
     EjectUpWhenBatmobileVerticalMove @ 8472 archetype=absent class-default=absent
     EjectWhenBatmobileVerticalMove   @ 8464 archetype=absent class-default=absent
     GlideBoostInMove @ 8368 archetype=absent class-default=absent
     GlideInMove      @ 8360 archetype=absent class-default=absent
  ## RVehicleBatmobileBase
     EjectUpDist      @ 6032 archetype=absent class-default=absent
     MaxEjectType     @ 5902 archetype=absent class-default='EBET_NormalEject' (Default__RVehicleBatmobileBase)
     OverrideNextEject@ 5604 archetype=absent class-default=absent
  (13 eject-named fields total; 0 charge-named)

grep -rn "EBET_" Working/vendor/BmSDK/
  Working/vendor/BmSDK/RVehicleBatmobileBase.g.cs:3839: EBET_None = 0,
  :3840 EBET_NormalEject = 1,  :3841 EBET_SuperEject1 = 2,  :3842 EBET_SuperEject2 = 3,  :3843 EBET_MAX = 4

grep -n "Charge|SuperEject|CurrentEjectType|LastEject|EjectType|OverrideNextEject|EjectUpDist" <BmSDK dumps>
  :6373-6375 OverrideNextEject ObjectProperty -> RSeqAct_OverrideBatmobileEject
  :6814-6816 BoostingOut (EBatmobileEjectType) at 5901
  :6821-6825 MaxEjectType  at 5902
  :7004-7006 EjectUpDist   at 6032
  (no Charge* member in either class)

grep -rn "Eject\." Research/BatmobileGrab/*.md
  CLASS_DEFAULTS.md:87  EjectUpMove = Eject.Eject_Up_To_Glide
  CLASS_DEFAULTS.md:88  EjectForwardMove = Eject.Eject_Fwd_To_Glide
  CLASS_DEFAULTS.md:93  EjectWhenBatmobileVerticalMove = Eject.Abseil_Eject_To_Glide
  CLASS_DEFAULTS.md:94  EjectUpWhenBatmobileVerticalMove = Eject.Abseil_Eject_Up_To_Glide
  COLLISION_WHERE.md:101 EjectToSpotMove = Eject.Eject_To_Spot
  CLASS_DEFAULTS.md:143 EjectUpDist 1300.0 (f32 @6032)
  CLASS_DEFAULTS.md:220 MaxEjectType 'EBET_NormalEject' (byte @5902)

read Research/BatmobileGrab/EJECT_VELOCITY.md
  §VERDICT: "The vector handed to Core.SetRBLinearVelocity is (0, 0, 0) cm/s with bAddToCurrent = false"
  §4: TriggerSpecialMove at +1103 is the only launch-shaped call; float constants [1.0, 600.0, 0.0, 1.0, 1.0]

grep -rn "exit.driver|parachute|eject" Research/JC3Grab/*.md
  EJECT.md §1: 0 velocity/impulse/launch/force members in 4,832 exits
  EJECT.md §2: exit.driver.moving.parachute -> S_EXIT_VEHICLE_PARA, gate 5..999, point.driver (-0.58,0.60,0.39)
  EJECT_MAP.md §3.1: 0 hold/duration words in 249 + 145 + 104 input rows
  EJECT_MAP.md §3.2: ACT_EJECT_FROM_VEHICLE absent (0 hits)

grep -n "SuperEject" (repo)
  Research/JC3Grab/JC3_HUD_WEAPONS.json:56,70 -> UC_SetSuperEject (Batmobile HUD setter)
```

**Not done:** no `.epe`, entity, `.vmodc`, input table or build tree was written; nothing was installed or
launched (test ban honoured). **Revert = delete this file.**

## 7. UNKNOWNs and their settlers

| # | unknown | what was tried | settler |
|---|---|---|---|
| U1 | the hold thresholds that pick level 2 / 3 | 13 eject-named fields, 0 charge-named; eject-body floats `[1.0, 600.0, 0.0, 1.0, 1.0]`; all input tables have 0 hold words | the input/`RSeqAct` layer (`RSeqAct_OverrideBatmobileEject`'s script), or one recorded session with the game's own telemetry |
| U2 | the second-press window for the double-tap | only `LastEjectFromBatmobileTime` (timestamp) exists | same |
| U3 | the address + member to write a character's vertical velocity after `DriverLeave` | no character-velocity row in `Research/RTTI` read here; JC3 exits carry no member | the next RTTI pass over `CRigidBodyCharacter`/pawn, or the parachute-deploy native that already applies an upward push |
| U4 | the per-level launch speed in BmAK | the moves are `RSpecialMoveConfigConfigurable` assets, not in `BmGame.upk` | the special-move asset package (not in the grab) |
| U5 | `EjectUpDist`'s unit (1300.0 = 13 m only if cm) | the class dump states the type, not the unit; no other use of the field decoded | one call site of `ModifyEjectUpLoc` / `SetBatmobileExit` in the scripts |
| U6 | which of `roll.out` / `moving.parachute` JC3 picks at 5..999 | both gates identical; selection is code | Q1-EJ-B probe (already queued) |
