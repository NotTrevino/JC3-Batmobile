# EJECT_VELOCITY - G3-02j

The eject chain's launch call, decoded from the cooked bytecode, and the jump
tokens that place the mode calls in their branches.

- package: `BmGame.upk` (sha1 `36b5903579b80e7e0d3036a605cbf803c64e5b32`)
- body: `DrivingMode.EjectFromVehicle` export 104931, script 1297 bytes
- body: `DrivingMode.ToggleBattleMode` export 105028, script 200 bytes

## VERDICT

**The vector handed to `Core.SetRBLinearVelocity` is `(0, 0, 0)` cm/s with
`bAddToCurrent = false`. It is applied to `EjectFromVehicle.Car.Mesh` - the Batmobile's mesh
component, not Batman - and its effect is to *clear* that body's linear
velocity.** The call does not throw Batman out; the card's premise that this
call is the launch is refuted by its own argument bytes. The only launch-
shaped call in the body is `TriggerSpecialMove` (see below), an animation
special move whose numeric parameters are not in this package (UNKNOWN).

## 1. The call and its argument bytes

The callee token is `Core.SetRBLinearVelocity` (ref -2300); it sits at script `+513` (byte `0x201`).

```
args @518..532 : 23 00 00 00 00 00 00 00 00 00 00 00 00 28 16
```

| arg | token | bytes | value |
|---|---|---|---|
| 0 | `0x23` VectorConst | 13 | `(0, 0, 0)` |
| 1 | `0x28` False | 1 | `False` |

Byte accounting: 13 (vector) + 1 (bool) = 14 argument bytes, plus the `0x16`
terminator at `+532` = 15 bytes from the callee to `0x16` inclusive, which is exactly
what the token widths claim. No byte between the callee and the terminator is left
unaccounted, so a wrong width could not hide here.

### Why `0x23` is a 13-byte vector literal

Measured over every Function script in the package:

| measure | count |
|---|---|
| `0x23` occurrences | 6116 |
| decode as three finite floats | 4409 |
| follow directly by `0x16` (end of parms) | 934 |
| all-zero vector | 786 |

Samples (vector reads end exactly on the argument boundary):

| function | at | vector | next |
|---|---|---|---|
| `GatherPointsFromCenter` | +25 | `(0, 0, 100)` | `0x16` |
| `SetSmokeScreen` | +187 | `(0, 0, 150)` | `0x16` |
| `StartGatherPointsFromCenter` | +246 | `(0, 0, 100)` | `0x16` |
| `StartGatherPointsFromCenter` | +370 | `(0, 0, -2000)` | `0x16` |
| `StartGatherPointsFromCenter` | +403 | `(0, 0, 100)` | `0x16` |
| `GatherPointsFromCenter` | +177 | `(0, 0, -2000)` | `0x16` |

## 2. What object it is applied to

The receiver is the Context chain that ends exactly on the callee token and
re-serialises to the original bytes:

```
  Context(object = Context(object = LocalVariable "EjectFromVehicle.Car",
          skip=9, prop="Core.Mesh", flag=0, func={"kind": "InstanceVariable", "at": 501, "ref": "Core.Mesh", "index": -1125})
      , skip=24, prop=null, flag=0)
  -> Core.SetRBLinearVelocity((0,0,0), false)
```

So the receiver is the `Mesh` component of `EjectFromVehicle.Car` - the
Batmobile's rigid body - not the pawn Batman is riding. `Car` holds the
vehicle; `Core.Mesh` is the component whose native moves the body.

## 3. Where the call sits

It is the first statement of the `then` block of the `if` token at `+478`
(operand `0x034f`, condition bytes `481..487`, re-serialises: True).

```
{
 "kind": "BoolVariable",
 "at": 481,
 "ref": "EjectFromVehicle.FFInRange",
 "index": 104926,
 "flag": 0
}
```

The condition is a stored bool variable, i.e. under the conditional-jump reading
the car stops only on the path where that flag holds - not on every eject. (The
token's u16 operand itself is not decodable here, section 6; the *direction* of
the guard does not depend on it: a `0x07 <expr> <block>` layout executes the block
only when the expression holds.)

## 4. The order of calls in the body (byte order)

| at | call | args |
|---|---|---|
| +3 | `CantEjectFromBatmobile` | <0x4A unnamed 1-byte token>, <0x4A unnamed 1-byte token> |
| +173 | `RVehicleBatmobileBase.CheckSpaceAboveBatmobileCockpit` | - |
| +365 | `DriverLeave` | True, EjectFromVehicle.FFInRange |
| +424 | `RemoveBatmobileBindsAndSetBatmanBinds` | - |
| +443 | `PlayCockpitOpenFast` | - |
| +513 | `Core.SetRBLinearVelocity` | VectorConst, False |
| +1103 | `TriggerSpecialMove` | Self, EjectFromVehicle.Loc, <0x4A unnamed 1-byte token> |

`TriggerSpecialMove` is the only call after the velocity call that can move the
pawn: an animation special move (`RSpecialMoveConfigConfigurable`), so the launch
is authored as a move, not as a stored velocity. Its numeric parameters are not
in BmGame.upk. UNKNOWN: the special-move asset and its distances/velocities.

## 5. Class defaults

`Research/BatmobileGrab/CLASS_DEFAULTS.json` was searched for any key or value
mentioning eject / velocity / launch: **50 entries**. Entries carrying the mode
ids 5269 / 61474: **0**.
Entries whose *key* is a velocity: **0**.

Special-move configs named by those entries: `Eject.Abseil_Eject_To_Glide`, `Eject.Abseil_Eject_Up_To_Glide`, `Eject.Eject_Fwd_To_Glide`, `Eject.Eject_Up_To_Glide`

These are `RSpecialMoveConfigConfigurable` references, i.e. the moves that
`TriggerSpecialMove` can start - they carry the trajectory, and their numbers
live in the special-move asset, not in this package (UNKNOWN here).

| path | value |
|---|---|
| `/cdo/subclass/tags[6]/candidates[0]/member` | `EjectUpMove` |
| `/cdo/subclass/tags[6]/members[0]/member` | `EjectUpMove` |
| `/cdo/subclass/tags[6]/name` | `EjectUpMove` |
| `/cdo/subclass/tags[6]/value_text` | `Eject.Eject_Up_To_Glide (RSpecialMoveConfigConfigurable)` |
| `/cdo/subclass/tags[6]/ref` | `Eject.Eject_Up_To_Glide` |
| `/cdo/subclass/tags[7]/candidates[0]/member` | `EjectForwardMove` |
| `/cdo/subclass/tags[7]/members[0]/member` | `EjectForwardMove` |
| `/cdo/subclass/tags[7]/name` | `EjectForwardMove` |
| `/cdo/subclass/tags[7]/value_text` | `Eject.Eject_Fwd_To_Glide (RSpecialMoveConfigConfigurable)` |
| `/cdo/subclass/tags[7]/ref` | `Eject.Eject_Fwd_To_Glide` |
| `/cdo/subclass/tags[12]/candidates[0]/member` | `EjectWhenBatmobileVerticalMove` |
| `/cdo/subclass/tags[12]/members[0]/member` | `EjectWhenBatmobileVerticalMove` |

So the eject launch has **no class default velocity** to fall back on: the
`(0, 0, 0)` above is not a default being overridden elsewhere - it is a stop.

## 6. Jump tokens and the branch each mode call sits in

### ToggleBattleMode (5 jump-shaped tokens)

| at | token | u16 operand | u32 read | next byte |
|---|---|---|---|---|
| +0 | `0x07` | 15 | 1931214863 | `0x1c` |
| +11 | `0x07` | 115 | -1702756237 | `0x82` |
| +79 | `0x07` | 255 | -2122186497 | `0x82` |
| +129 | `0x07` | 252 | 18415868 | `0x19` |
| +172 | `0x06` | 291 | 18415907 | `0x19` |

Candidate encodings, measured (how many of the tokens, read as one offset,
land inside the body / on a token that can open a statement):

| base | inside body | on a statement start | of |
|---|---|---|---|
| operand_end | 2 | 2 | 5 |
| token | 2 | 0 | 5 |
| operand_start | 2 | 1 | 5 |

### EjectFromVehicle (20 jump-shaped tokens)

| at | token | u16 operand | u32 read | next byte |
|---|---|---|---|---|
| +0 | `0x07` | 13 | 1511718925 | `0x1b` |
| +75 | `0x07` | 240 | 763494640 | `0x82` |
| +156 | `0x07` | 278 | 427884822 | `0x81` |
| +209 | `0x07` | 485 | 7799269 | `0x77` |
| +220 | `0x07` | 485 | 1638885 | `0x19` |
| +260 | `0x07` | 483 | 1638883 | `0x19` |
| +308 | `0x06` | 485 | 184812005 | `0x04` |
| +348 | `0x07` | 635 | 435290747 | `0xf2` |
| +417 | `0x06` | 0 | 0 | `0x00` |
| +436 | `0x06` | 0 | 0 | `0x00` |
| +478 | `0x07` | 847 | 2949967 | `0x2d` |
| +605 | `0x06` | 1814 | 130025238 | `0xc0` |
| +607 | `0x07` | 1984 | 2005010368 | `0x82` |
| +609 | `0x07` | 30594 | -520063102 | `0x00` |
| +631 | `0x07` | 1953 | -2105407583 | `0x82` |
| +633 | `0x07` | 33410 | 2005041794 | `0x82` |
| +1140 | `0x07` | 1950 | 896665502 | `0x72` |
| +1142 | `0x07` | 13682 | -180079246 | `0x44` |
| +1250 | `0x06` | 1984 | 17762240 | `0x0f` |
| +1252 | `0x07` | 271 | -1733623537 | `0xab` |

Candidate encodings, measured (how many of the tokens, read as one offset,
land inside the body / on a token that can open a statement):

| base | inside body | on a statement start | of |
|---|---|---|---|
| operand_end | 10 | 0 | 20 |
| token | 10 | 3 | 20 |
| operand_start | 10 | 1 | 20 |

**No encoding places every operand inside the body** (every scheme above has
`inside_body < of`), so the absolute target of these tokens is **UNKNOWN**: the
u16 after a `0x06`/`0x07` is not proved to be an in-body byte offset in this
build. Branch membership below therefore rests on block structure and symbols,
not on offset arithmetic, and is labelled as such.

### ToggleBattleMode: 5269 vs 61474

| at | mode id | enclosing jump before | jump after |
|---|---|---|---|
| +145 | 5269 | +129 (`0x07` op 252) | +172 (`0x06` op 291) |
| +188 | 61474 | +172 (`0x06` op 291) | - |

The `if` at `+129` (operand `0x00fc`) has this condition, re-serialised
byte-exactly from the decoded tree (True):

```
{
 "kind": "Context",
 "at": 132,
 "object": {
  "kind": "InstanceVariable",
  "at": 133,
  "ref": "RPlayerController.BatmobilePawn",
  "index": 104683
 },
 "skip": 15,
 "prop": "TryToChangeMode.ReturnValue",
 "flag": 0,
 "function": {
  "kind": "FinalFunction",
  "at": 145,
  "call": "RVehicleBatmobileBase.TryToChangeMode",
  "args": [
   {
    "kind": "IntConst2B",
    "at": 150,
    "value": 5269
   }
  ]
 }
}
```

The condition's Context property is `TryToChangeMode.ReturnValue` - the **ReturnValue of
`TryToChangeMode`** - so the branch is selected by that function's result,
and its argument `5269` decides which mode is attempted.

Then-block statements, tiled sequentially from the end of that condition
(`+156`) to `+175`, where the second mode call's own receiver expression begins -
the whole gap is covered, no byte of it is unexplained:

| at | bytes | statement |
|---|---|---|
| +156 | 8 | `{"kind": "LetBool", "at": 156, "lhs": {"kind": "BoolVariable", "at": 157, "ref": "RPlayerController.bWaitingToDebounceRun", "index": 104307, "flag": 1` |
| +164 | 8 | `{"kind": "LetBool", "at": 164, "lhs": {"kind": "BoolVariable", "at": 165, "ref": "RPlayerController.bWaitingToDebounceAimGadget", "index": 104305, "fl` |
| +172 | 3 | `{"kind": "Jump", "at": 172, "operand_u16": 291}` |

A single `0x06` at `+172` (operand `291`) separates the two mode calls, so they
are mutually exclusive: `5269` is attempted inside the conditional block, and
`61474` is evaluated on the path that block jumps over - i.e. **when
`TryToChangeMode(5269)` returns false**. The second call ends at `+199` and is
followed immediately by `0x04` (return), so nothing retries after it.

STATUS: DONE for the vector and the receiver; the branch placement is derived
from block structure (offsets UNKNOWN); the special-move parameters are UNKNOWN.

