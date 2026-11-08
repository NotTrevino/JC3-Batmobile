# Assumption challenge — G2-20 · Exit, bail-out and eject

**Scope.** Finished card `GRAB_BACKLOG.md:691-697` (S, deps G2-18), its §12 row (`:1303`),
MODLOG §"G2-20 · Exit, bail-out and eject — done" (`:11852`, intended change `:11682`) and the
outputs it names: `Research/JC3Grab/EJECT.md` (327 lines), `EJECT.json`, `Tools/scripts/jc3eject.py`
(733 lines). Rules read first: `GRAB_BACKLOG.md` §0.5 R1–R14.

**Method.** Re-ran the card's check, then attacked each claim with the data on disk: the 232 decoded
`detail/*.ee.json` graphs, the 232 `entities/*.ee.json` module caches, the nested donor
`Research/Epe/serpente_civilian.xml`, `Research/BatmobileGrab/BMSDK_OFFSETS.json`, and — read-only —
the vehicle containers at `D:\Games\Just Cause 3` (inner-file listing only; nothing written there,
no game launched, nothing committed).

**Change record (AGENTS.md).** One file written: this one, `Research/challenge/card-G2-20.md` —
the path the task names, beside the existing `card-G1-*.md` / `card-G2-*.md`. Revert: delete it.

**The card's own check, re-run:**

```
$ python Tools/scripts/jc3eject.py --check
PASS: 4832 exits in 232 graphs (61 names) | donor 26 exits, 7 speed-gated, 5 unconditional |
launch members: exits 0, graph classes 2, vehicle modules 1 | BmAK eject props 19,
json match True, md match True
EXIT=0
```

The census is intact and reproducible. Everything below is about what it is taken to mean, and what
the two "no carrier" claims actually searched.

---

## VERDICT

| # | assumption | verdict |
|---|---|---|
| A1 | "there is no vehicle state machine — the index has 0 `jc_statemachine/vehicles/`" | **BROKEN** as evidence — 26 containers ship `vehicles/vehicle_null.asb`; the *conclusion* survives |
| A2 | the other 231 `.epe` "are not kept as XML", so per-vehicle gates are unrecoverable | **BROKEN** — all 233 containers carry exactly one `.epe`; the nesting is one converter run away |
| A3 | "no vertical speed member exists" (fleet-wide) | **BROKEN** — `up_velocity_cap` on 197 cars + 35 boats and `BoatGlobal.turbo_jump.up_multiplier` = 25 on 35 |
| A4 | 4,832 exits / 232 graphs / 61 names, 9-key set, `enabled` 1, `interaction` 0 | **HOLDS** |
| A5 | "the graph vocabulary is 104 classes" | **BROKEN** (103 classes + the empty class) |
| A6 | "an exit is a state name … the state is the actual contract" | **WEAK** — 23 exits carry no state, and the doc never says so |
| A7 | the donor's gates: 7 gated, 5 unconditional, 0..5 / 5..999 / 0..3 / 3..999 | **HOLDS** |
| A8 | "both high-speed exits have the same gate and no other condition … which wins is code" | **WEAK** — the parachute exit also carries an obstructed check |
| A9 | a state string appears twice: the exit and its `ExitObstructedCondition` (`id:A3CC001A`) | **HOLDS** |
| A10 | the fleet: `moving.parachute` on 221/232 with 125/35/23/19/19 by class | **HOLDS** |
| A11 | 15 modifiers, `MOD_RIGHT` 1136 on 1,399 exits | **HOLDS** |
| A12 | `arcade.turbo_jump` values and the 145/232 carrier counts | **HOLDS** for the numbers, **WEAK** for "jumps the car" |
| A13 | BmAK eject = 19 properties at the quoted offsets | **HOLDS** |
| A14 | the 142 state machines are character-side | **HOLDS** |
| A15 | 0 launch members in exits; 2 of 104 classes; 1 module name | **HOLDS** within its keyword filter (see A3) |
| A16 | `--check` re-derives everything | **HOLDS** for the tables; two gate numbers are typed prose |

**One-line summary.** The exit census is excellent — every one of the 4,832 objects, its nine keys,
its gates, its states, its modifiers and the fleet class split reproduce exactly, and the BmAK
offset table is right to the byte. The trouble is in the two places the card reasons from absence:
"there is no vehicle state machine" is true of the *index* but 26 vehicles ship
`animations/jc_statemachine/vehicles/vehicle_null.{asb,afsmb}` (a null machine — the conclusion
holds, the citation does not), and "no vertical speed member exists" is contradicted by
`Buoyancy.up_velocity_cap` (197 vehicles) and the boats' `BoatGlobal.turbo_jump.up_multiplier = 25` (35 boats), a key
the card's own JSON contains and its prose table omits. The donor-side split and the two fast exits are
almost right: `moving.parachute` carries an `ExitObstructedCondition` that `roll.out` does not, so
the data — not just code — already discriminates them when the door is blocked.

---

## A1 · "there is no vehicle state machine" — **BROKEN** as evidence

**Claim.**

```
EJECT.md:44-46   "There is no vehicle state machine to carry it - the index has 0
                  `jc_statemachine/vehicles/` files, and the 142 state machines it does carry are
                  character-side (G2-19, `SEAT.md`)."
MODLOG:11858-9   "no vehicle state machine exists (0 `jc_statemachine/vehicles/`)"
```

**Assumption.** "No index row" = "no such file in the game".

**Test 1 — the index.** Confirm the 142 and their side:

```
index rows with jc_statemachine: 142
  by top dir: [('animations/jc_statemachine/npc', 124), ('animations/jc_statemachine/main_characters', 9),
               ('animations/jc_statemachine/animals', 7), ('animations/jc_statemachine/aero', 2)]
  vehicles: []
  extensions: {'.afsmb': 123, '.asb': 19}
```

**Test 2 — the containers.** List every inner file under `jc_statemachine` in the 233 vehicle `.ee`:

```
containers: 233  errors: 0
distinct jc_statemachine inner paths in vehicle containers: 2
   animations/jc_statemachine/vehicles/vehicle_null.asb    containers=26  distinct hashes=1
   animations/jc_statemachine/vehicles/vehicle_null.afsmb  containers=26  distinct hashes=1
```

26 containers (25 land, 1 air) ship that exact path. Its content:

```
first container: .../v0000_car_autostraad_oldjeep_civilian_01.ee
ASB bytes: 420   ascii runs: ['RTPC', 'ANIM_NULL', 'PPB/', 'PPS_NULL']
AFSMB bytes: 227 ascii runs: ['RTPC', 'StateMachine', '4ACT_UPDATE', 'S_NULL']
```

**Result.** A vehicle state machine **does** exist, is byte-identical in all 26 copies, and is a
*null* machine: one state `S_NULL`, one animation `ANIM_NULL`, one blend `PPS_NULL`. So the
conclusion the card needs — nothing in a vehicle state machine carries `S_EXIT_VEHICLE_PARA` — is
correct, and now has direct evidence instead of an index count. The sentence as written ("there is
no vehicle state machine") is false, and the citation ("the index has 0") is the reason it went
unnoticed: inner files are not in the VFS index.

> **Verdict: BROKEN** as evidence; the conclusion survives on stronger data.

---

## A2 · "the other 231 `.epe` files are not kept as XML … nesting cannot be recovered" — **BROKEN**

**Claim.**

```
EJECT.md:308-312  "The fleet's condition→exit mapping. It is decoded for the donor only: the detail
                   JSON sorts objects by id and ids repeat, so nesting cannot be recovered from it,
                   and the other 231 `.epe` files are not kept as XML."
MODLOG:11897-9    "the G2-18 detail JSON sorts objects by id and ids repeat, so nesting
                   (exit → its child conditions) cannot be recovered from it, and the other 231
                   `.epe` files are not on disk."
```

**Assumption.** Only the donor can ever be decoded as nested XML, so "per-vehicle gates" is a
permanent scope limit.

**Test.** Every vehicle container's inner files:

```
containers: 233  with a .epe inner file: 233  | count distribution: {1: 233}
```

and the donor XML is the output of exactly that path — `jc3detail.decode_epe()` writes the inner
`.epe` to a temp file and runs the same converter that produced
`Research/Epe/serpente_civilian.xml`.

**Result.** The raw nested `.epe` for all 232 graphs (233 containers, one each) is one converter run
away, on the same machine, with the same tool that made the donor file. What is true is that the
*decoded JSON* is lossy (ids repeat, 409 `?` node paths) and that only one `.epe` was kept as XML —
a choice, not a data limit. The report frames a shortcut as an impossibility, and the next card
(T-13) reads that framing as settled.

> **Verdict: BROKEN.** The scope statement is honest; the reason given for it is not.

---

## A3 · "no vertical speed member exists" — **BROKEN** (fleet-wide)

**Claim.**

```
EJECT.md:200-203  "`arcade.turbo_jump` is on **145** land vehicles, `VehicleMisc.turbo_jump_cooldown`
                   on **232**. Its members are speed punches and multipliers - **no vertical speed
                   member exists**, so even the car's rise is derived by code (UNKNOWN magnitude)."
MODLOG:11856-7    "one upward mechanism, `arcade.turbo_jump` (145 land vehicles), which jumps the
                   **car** and has no vertical-speed member."
```

**Assumption.** A keyword sweep for `eject|launch|catapult|impulse|parachute|wingsuit` plus the jump
vocabulary is a complete search for vertical motion.

**Test 1 — the sweep's own output.** `EJECT.json → launch.jump` (what the script found, not what
the prose printed):

```
CustomLandGlobal.arcade.turbo_jump.*               145 files
VehicleMisc.turbo_jump_cooldown / _upgraded        232 files
BoatGlobal.turbo_jump.up_multiplier                35 files
BoatGlobal.turbo_jump_upgraded.up_multiplier       35 files
BoatGlobal.turbo_jump.punch_speed_kph              35 files
BoatAI.Limit_Path_Jump_Scalar                      35 files
HelicopterAI.Limit_Path_Jump_Scalar                23 files
AirplaneAI.Limit_Path_Jump_Scalar_Flight/Taxi      18 files
VehicleCommon.all_vehicles_common.high_up_in_air_height 232 files
```

**Test 2 — every member whose name is up/vertical/jump.** Across the 232 module caches:

```
members with up/jump/vertical in the name: 15
   Buoyancy.up_velocity_cap                 x198  files=197
   BoatBuoyancy.up_velocity_cap             x35   files=35
   BoatGlobal.turbo_jump.up_multiplier      x35   files=35
   BoatGlobal.turbo_jump_upgraded.up_multiplier x35 files=35
   BoatBuoyancy.buoyancy_modules[N].vertical_drag …
   HelicopterModel.vertical_drag / vertical_drag_no_input  23 files
```

with the boat jump's value:

```
== BoatGlobal
    punch_delay_time = 0          punch_speed_kph = 80
    top_speed_kph = 200           top_speed_jump_multiplier = 2
    up_multiplier = 25
```

**Result.** Three vertical members exist that the sentence denies: `Buoyancy.up_velocity_cap`
(197 vehicles, and the donor's value is 20 — G2-31 already quotes it), `BoatBuoyancy.up_velocity_cap`
(35), and `BoatGlobal.turbo_jump.up_multiplier = 25` (35 boats, plus its upgraded twin). The card's
JSON records the boat keys; the prose table in §5 prints only the `CustomLandGlobal` row set and
drops them. None of these moves a *seated driver* — the conclusion ("no vehicle launches the driver
upward") is unaffected — but the stated mechanism ("no vertical speed member exists, so the rise is
code") is false: a boat jump has a vertical multiplier, and every vehicle has a vertical velocity
cap. For a car the claim holds (no `up` member in `CustomLandGlobal.arcade.turbo_jump`).

> **Verdict: BROKEN** for the fleet-wide sentence; the driver conclusion is untouched.

---

## A4 · the exit census — **HOLDS**

**Claim.** `EJECT.md:20-36`: 4,832 exits in 232 graphs, 61 names, 26 in the donor, every member from
a 9-key set, `enabled` 1 and `interaction` `00000000` on all.

**Test.** Re-count from the 232 detail JSONs:

```
detail files: 232
exits: 4832 distinct names: 61
exit value keys: {'_object_id': 4832, 'disable_event': 4832, 'enable_event': 4832,
                  'enabled': 4832, 'interaction': 4832, 'name': 4832, 'name_hash': 4832,
                  'state': 4809, 'modifier': 1399}
enabled: {'1': 4832} | interaction: {'00000000': 4832}
```

**Result.** Every figure is exact: 4,832, 232, 61, 9 keys, no `enabled` 0, no non-null pointer. The
only nuance the doc leaves unsaid is that `state` is present on 4,809 (A6) and `modifier` on 1,399.

> **Verdict: HOLDS.**

---

## A5 · "the graph vocabulary is 104 classes" — **BROKEN**

**Claim.** `EJECT.md:38` ("The graph vocabulary is **104** classes").

**Test.** Count distinct classes over the same 232 graphs, and ask what the generator counts:

```
graph classes: 103
```

```
jc3eject.py:150-153
for o in objs:
    cls = o.get("class") or ""
    classes[cls] += 1          ← the empty string is counted as a class
```

and the root object of every file has `"class": null`:

```
fleet classes incl '': 104   empty-class count: 232
```

**Result.** 103 named classes plus one bucket for "no class" (one `/root` object per graph). The
name-filtered count ("2 with Velocity/Impulse/Launch/Eject/Force") is unaffected, but the
denominator is one too high and the "104" is printed twice.

> **Verdict: BROKEN** (small, but it is a number quoted as a vocabulary size).

---

## A6 · "an exit is a state name" — **WEAK**

**Claim.**

```
EJECT.md:4-7     "An exit in this game is a *state name* plus a set of gates, and the only numbers
                  any exit carries are the gates."
EJECT.md:31      "| `state` | the state string the player enters (`S_EXIT_VEHICLE_PARA`) — the
                  actual contract |"
```

**Test.** How many exits carry no `state`?

```
exits without a state: 23
{'exit.stunt_to_reel': 23}
   v2102_helicopter_eubus_utility_civilian_01.ee.json  exit.stunt_to_reel
   v2200_helicopter_capstone_assault_military_01.ee.json  exit.stunt_to_reel
   …
```

**Result.** One exit name (`exit.stunt_to_reel`, on 23 helicopters) has no state string at all, so
for those the "actual contract" is not in the object — the exit presumably does nothing visible or
is wired elsewhere. The doc never mentions the exception, and its member table reads as if `state`
were universal. 23 of 4,832 is small, but it is exactly the class of exit ("stunt to reel") a port
would ask about.

> **Verdict: WEAK** — the model is right for 99.5 %; the exception is silent.

---

## A7 · the donor's gates — **HOLDS**

**Claim.** `EJECT.md:50-93`: 26 exits, 7 speed-gated (0..5 ×2, 5..999 ×2, 0..3, 3..999), 5 with no
condition at all.

**Test.** Parse the donor XML tree, find each exit's child conditions, and read the
`ParentVelocityCondition` `min`/`max`:

```
donor exits: 26   gated: 7   ungated: 19
   exit.driver.default            S_EXIT_VEHICLE           {'max': '5', 'min': '0'}
   exit.ai.driver.default         S_EXIT_VEHICLE           {'max': '5', 'min': '0'}
   exit.driver.roll.out           S_ROLL_OUT_EXIT_VEHICLE  {'max': '999', 'min': '5'}
   exit.driver.moving.parachute   S_EXIT_VEHICLE_PARA      {'max': '999', 'min': '5'}
   exit.driver.to.fall            S_EXIT_VEHICLE_TO_FALL   {'max': '5', 'min': '0'}
   exit.passenger1.roll.out       S_ROLL_OUT_EXIT_VEHICLE  {'max': '999', 'min': '3'}
   exit.passenger1.pulled.out     S_PULLED_OUT_VEHICLE     {'max': '3', 'min': '0'}
ungated with no condition at all:
   exit.driver.pushed.out, exit.driver.to.swim, exit.driver.pulled.out,
   exit.driver.upside.down, exit.passenger1.upside.down
```

**Result.** Exactly 7 gated, exactly the 5 named unconditional exits, exactly the four gate pairs
the doc prints, and every other exit's condition is a non-velocity one
(`ParentIsUpRightCondition`, `UserIsPlayerCondition`, `StuntExitValidCondition`). The "5" split
(0..5 vs 5..999) is the data.

> **Verdict: HOLDS.**

---

## A8 · "both high-speed exits have the same gate … which wins is code" — **WEAK**

**Claim.**

```
EJECT.md:100-103  "Both high-speed exits have the same gate and no other condition on the donor's
                   `point.driver`, so **which one wins is not in the data** — UNKNOWN, probe Q1-EJ-B."
```

**Test.** The two exits' complete condition lists (from A7's parse):

```
exit.driver.roll.out          conds: ['CInteractionGraphParentVelocityCondition']
exit.driver.moving.parachute  conds: ['CInteractionGraphParentVelocityCondition',
                                      'CInteractionGraphExitObstructedCondition']
```

and the obstructed condition's own switch:

```
CInteractionGraphExitObstructedCondition  id:A3CC001A = S_EXIT_VEHICLE_PARA   (check 0)
CInteractionGraphExitObstructedCondition  id:A3CC001A = S_EXIT_VEHICLE        (×4, check 0)
```

**Result.** The velocity gates are identical (5..999), but the condition sets are not: the
parachute exit additionally requires "not obstructed" (check 0), while roll.out has no such
condition. So the data *does* discriminate them in one case — when the door is obstructed, only
`roll.out` can fire — and the obstructed condition even names the state it falls back to
(`A3CC001A`, the same string). The doc's §2 table prints the condition (so the information is on
the page) while §3 denies it. Q1-EJ-B remains a valid probe for the *unobstructed* case, but the
blanket "no other condition" is wrong.

> **Verdict: WEAK** — the probe stands; the reasoning overstates what the data leaves open.

---

## A9 · the state string appears twice — **HOLDS**

**Claim.** `EJECT.md:47-49` ("as the exit's own `state`, and inside its `ExitObstructedCondition`
… under the hashed key `id:A3CC001A`").

**Test.**

```
S_EXIT_VEHICLE_PARA occurrences in the donor XML: 2
   → CInteractionGraphExit  exit.driver.moving.parachute
   → CInteractionGraphExitObstructedCondition   id:A3CC001A = S_EXIT_VEHICLE_PARA
S_ROLL_OUT_EXIT_VEHICLE occurrences: 2   (the two roll-out exits)
S_EXIT_VEHICLE occurrences: 19
```

All five `A3CC001A` values in the donor:

```
CInteractionGraphExitObstructedCondition  id:A3CC001A = S_EXIT_VEHICLE      ×4
CInteractionGraphExitObstructedCondition  id:A3CC001A = S_EXIT_VEHICLE_PARA ×1
```

**Result.** The count, the hashed key and the placement are all exactly as stated: each obstructed
condition repeats its parent exit's state under `A3CC001A`. This is the only place a state string is
duplicated.

> **Verdict: HOLDS.**

---

## A10 · the fleet split — **HOLDS**

**Claim.** `EJECT.md:120-124`, `:145-147`: `exit.driver.moving.parachute` on 221/232 vehicles,
125 cars / 35 boats / 23 helicopters / 19 jets / 19 bikes; the other universal driver exits.

**Test.** Recount from `EJECT.json → fleet.names`:

```
exit.driver.moving.parachute: count=221 states={'S_EXIT_VEHICLE_PARA': 221}
   roots={'CCar': 125, 'CBoat': 35, 'CHelicopter': 23, 'CMotorBike': 19, 'CAirPlane': 19}
exit.driver.roll.out: count=183 roots={'CCar': 112, 'CBoat': 30, 'CHelicopter': 23, 'CAirPlane': 18}
exit.driver.default:  count=161 roots={'CCar': 119, 'CHelicopter': 23, 'CAirPlane': 19}
exit.driver.to.swim:  count=191 states={'S_EXIT_DRIVER_VEHICLE_IN_WATER': 163,
                                        'S_EXIT_IN_WATER_MOTORBIKE': 28}
                      roots={'CCar': 125, 'CBoat': 5, 'CHelicopter': 23, 'CMotorBike': 19,
                             'CAirPlane': 19}
```

125 + 35 + 23 + 19 + 19 = 221 ✓, and the totals on the "universal" rows match the table. The
motorbike note ("every `exit.ai.*` row reads 0 for motorbikes") is consistent with the
`CMotorBike: 0` cells.

> **Verdict: HOLDS.**

---

## A11 · the modifier table — **HOLDS**

**Claim.** `EJECT.md:160-178`: 15 distinct `MOD_*` values, `MOD_RIGHT` 1136, `MOD_LOW_RIGHT` 182, …

**Test.** Count non-null `modifier` values across all 4,832 exits:

```
distinct modifiers: 15   total exits with one: 1399
   MOD_RIGHT 1136   MOD_LOW_RIGHT 182   MOD_HELI_ASSAULT 16   MOD_CAR_EXIT_RIGHT_ROLL 9
   MOD_CAR_EXIT_ROLL 9   MOD_JET_BEHIND 8   MOD_CAR_MOUNTED_WEAPON_PARA 7   MOD_TRACTOR 6
   MOD_BOAT_SPY 6   MOD_TECHNICAL_JEEP 4   MOD_RIGHT_TECHNICAL_JEEP 4   MOD_LOW 3
   MOD_ARMORED_JEEP 3   MOD_RIGHT_ARMORED_JEEP 3   MOD_HIGH 3
```

**Result.** Every row reproduces, including the two big ones. The reading "a class selector the game
derives, not the exit's name" is an inference (the values are opaque hashes-to-names), but the
counts are exact and the G2-19 cross-reference is consistent.

> **Verdict: HOLDS** (counts); the selector semantics stay an inference.

---

## A12 · `arcade.turbo_jump` values and carriers — **HOLDS**, with "jumps the car" **WEAK**

**Claim.** `EJECT.md:185-201` table (15 / 12 / 50 / 200 / 0.1 / 2 and the upgraded 30 / 25 / 80);
`turbo_jump_cooldown` 5 and upgraded 2; 145 land vehicles, cooldown on 232.

**Test.** Read the donor's `CustomLandGlobal` and `VehicleMisc` rows, and the per-file counts:

```
CustomLandGlobal.turbo_jump.f_multiplier = 15   .r_multiplier = 12
CustomLandGlobal.turbo_jump.punch_speed_kph = 50   .top_speed_kph = 200
CustomLandGlobal.turbo_jump.punch_delay_time = 0.1   .top_speed_jump_multiplier = 2
CustomLandGlobal.turbo_jump_upgraded.f = 30  .r = 25  .punch = 80  .top = 200  .delay = 0.1
VehicleMisc.turbo_jump_cooldown = 5   _upgraded = 2
files: CustomLandGlobal.arcade.turbo_jump.* 145 | VehicleMisc.turbo_jump_cooldown 232
```

**Result.** Every value and both counts reproduce. Two caveats: (a) the label "the speed the jump
punches to" for `punch_speed_kph`, and "the speed cap while airborne" for `top_speed_kph`, are name
readings — no file states them, and the doc prints them as roles; (b) "jumps the **car**" is
inferred from the module being `CustomLandGlobal`, which is a reasonable but name-level link
(nothing decoded says the jump applies on the ground vs. in the air; `top_speed_kph 200` with
`top_speed_jump_multiplier 2` would be 400). Also, the boat jump (A3) is a second, unreported
mechanism.

> **Verdict: HOLDS** for the numbers; **WEAK** for the role labels.

---

## A13 · BmAK eject = 19 properties at those offsets — **HOLDS**

**Claim.** `EJECT.md:230-266`: 19 properties, `EjectUpMove` `0x20e0`, `EjectForwardMove` `0x20e8`,
`EjectWhenBatmobileVerticalMove` `0x2110`, `EjectUpWhenBatmobileVerticalMove` `0x2118`,
`EjectToSpotMove` `0x2130`, `OverrideNextEject` `0x15e4`, `MaxEjectType` `0x170e`,
`EjectUpDist` `0x1790`, plus the natives `ModifyEjectUpLoc` / `SetBatmobileExit`.

**Test.** Read `Research/BatmobileGrab/BMSDK_OFFSETS.json`:

```
EjectUpMove                      8416  0x20e0  ObjectProperty  RSpecialMoveConfig
EjectForwardMove                 8424  0x20e8  ObjectProperty  RSpecialMoveConfig
EjectWhenBatmobileVerticalMove   8464  0x2110  ObjectProperty  RSpecialMoveConfig
EjectUpWhenBatmobileVerticalMove 8472  0x2118  ObjectProperty  RSpecialMoveConfig
EjectToSpotMove                  8496  0x2130  ObjectProperty  RSpecialMoveConfig
OverrideNextEject                5604  0x15e4  ObjectProperty  RSeqAct_OverrideBatmobileEject
MaxEjectType                     5902  0x170e  ByteProperty    EBatmobileEjectType
EjectUpDist                      6032  0x1790  FloatProperty   float
eject props in EJECT.json: 19
```

**Result.** Every offset in the table matches the SDK dump, the 19-property set is the same set,
and the two natives are correctly attributed to `NATIVE.md` rather than to the offsets file. The
doc's own honesty about `EjectUpDist` (no value, meaning is a name reading) is exactly right.

> **Verdict: HOLDS.**

---

## A14 · the 142 state machines are character-side — **HOLDS**

**Test.** A1's census:

```
animations/jc_statemachine/npc 124 | main_characters 9 | animals 7 | aero 2  (total 142)
vehicles: []
```

**Result.** Exactly 142, none of them a vehicle path. (The vehicle-side file from A1 is not in the
index, which is why this count is clean — and why the card's conclusion about it needed the
container check instead.)

> **Verdict: HOLDS.**

---

## A15 · 0 launch members in exits; 2 of 104 classes; 1 module name — **HOLDS** within the filter

**Test.** The exit key union (A4) contains no `velocity`/`impulse`/`launch`/`force`/`speed` key —
0 of 4,832. The class filter returns exactly two names:

```
classes matching Veloc/Impulse/Launch/Eject/Force: ['CForcePulse',
  'CInteractionGraphParentVelocityCondition']
```

and the module sweep:

```
LAUNCH_RE = eject|launch|catapult|impulse|parachute|wingsuit
launch: {'TrainGlobal.crashing_impulse': 12}
```

**Result.** All three statements are true as computed. The caveat is that this is a *name* filter:
it cannot see `up_multiplier` (A3), `up_velocity_cap`, or any member whose name does not contain
one of eight words. The doc presents the sweep as the third of "three sweeps, all negative on the
driver" — the negativity is right, the completeness claim rests on a vocabulary it chose.

> **Verdict: HOLDS** for the counts; the filter's limits are A3's finding.

---

## A16 · `--check` re-derives everything — **HOLDS** (two typed numbers)

**Test 1.** Re-run: `PASS … json match True, md match True`, exit 0. The build re-reads the XML and
the 232+232 JSON caches — it is not comparing a file with itself.

**Test 2.** Grep the renderer for gate numbers that are not read from `donor.gates`:

```
jc3eject.py:477  a("same lower down: `pulled.out` 0..3, `roll.out` 3..999.")
jc3eject.py:634  a("4. **The gate's unit.** `min 5` / `max 999` are game speed units. …")
```

Both are correct today (A7 verified 0..3, 3..999, 5, 999), but they are prose literals: change the
donor's gate and `--check` still passes.

**Result.** The tables and the JSON are genuinely re-derived (the tamper tests in MODLOG are
plausible and the code path matches); the two sentences above are the only numbers that are not.

> **Verdict: HOLDS** with a small typed-literal caveat.

---

## What this does and does not change

* **Confirmed:** 4,832 exits in 232 graphs, 61 names, the exact nine-key member set, `enabled` 1 /
  `interaction` 00000000 everywhere, the donor's 7 gates and 5 unconditional exits with their exact
  min/max, the obstruction→state duplication under `A3CC001A`, 221/232 parachute exits with the
  class split, 15 modifiers with exact counts, the land `turbo_jump` values and 145/232 carriers,
  the 19 BmAK properties at the printed offsets, and 142 character-side state machines.
* **Broken or weakened by a wider search:** "no vehicle state machine" (26 containers ship a null
  one), "the other `.epe` are unrecoverable" (all 233 ship one), "no vertical speed member exists"
  (`up_velocity_cap` ×232, boat `up_multiplier` 25), "104 classes" (103 + the empty class), "both
  fast exits have the same conditions" (the parachute exit has an obstructed check the roll-out does
  not), and "an exit is a state name" (23 `exit.stunt_to_reel` have none).
* **Not done here:** no game launched, no archive opened beyond the cached data and the read-only
  inner-file listing, nothing written into `D:\Games`, nothing committed.
