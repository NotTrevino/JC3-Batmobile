# EJECT_MOVE - G3-02k

What `DrivingMode.EjectFromVehicle`'s `TriggerSpecialMove` starts, what that move is
made of, and the numbers that produce the launch.

- package: `BmGame.upk` (sha1 `36b5903579b80e7e0d3036a605cbf803c64e5b32`)
- package: `Startup.upk` (sha1 `36c84699dec17740976f383c9cd7e2b7edd1da66`)
- body: `DrivingMode.EjectFromVehicle` export 104931, script 1297 bytes

## VERDICT

**The eject triggers a glide kick, and the kick's own animation is what moves
Batman.** The call at `+1103` is a *virtual* `TriggerSpecialMove` dispatched on the
Context object `Car.ShortRangeGlideKick` - the vehicle's class default for that
member is the move asset `GlideKick.GlideKickShort_FromBatmobile`
(`RSpecialMoveConfigConfigurable` wrapping an `RSpecialMoveConfig_GlideKick`). That
config names anim set `BM_Batmobile` and two animations; the short-range one
`Batmobile_Short_Range_Glide_Kick` carries a root-motion translation of (764.945, 0, 0) cm over 113 frames at
30 fps. The launch is therefore:

| quantity | value | source |
|---|---|---|
| forward distance | **764.95 cm (7.649 m)** | `Batmobile_Short_Range_Glide_Kick` field 108 |
| vertical rise | **0 cm** | same field, Z component |
| duration | **3.7333 s** (113 frames @ 30 fps) | fields 156 / 160 / 168 |
| mean speed | **204.9 cm/s** (2.049 m/s) | distance / duration |
| per-frame step | **6.83 cm** | distance / (frames - 1) |
| target range the move is offered at | **2500 cm (25 m)** | `RVehicleBatmobileBase.ShortRangeGlideKickRange` default |

The same config's other animation `Batmobile_Mid_Range_Glide_Kick` (mid range) carries (949.433, 0, 0) cm over
114 frames - 3.7667 s, mean 252.1 cm/s. Which of the two is played is chosen at run time
(`AnimName` is an array and `PickRandomAnim` is called in the parent instance body),
so the *pair* bounds the launch: 764.95 - 949.43 cm forward.

There is **no scripted velocity and no class-default velocity** anywhere on the
chain: the config's own defaults carry an `InstanceClass` and two bools, nothing
numeric, and neither the GlideKick instance body nor its parent contains a velocity
call. The `(0, 0, 0)` `SetRBLinearVelocity` of G3-02j stops the car; this animation
moves Batman.

## 1. The call and the move it names

`TriggerSpecialMove` at script `+1103` is `0x1b` - a *virtual* call token, so the callee is an FName
(`TriggerSpecialMove`, name index 79525) and the target class is whatever the receiver's class resolves
it to. Argument bytes (from the callee to the terminator):

```
17 00 e0 99 01 00 4a 16
```

| arg | kind | value |
|---|---|---|
| 0 | Self | `Self` |
| 1 | LocalVariable | `EjectFromVehicle.Loc` |
| 2 | <0x4A unnamed 1-byte token> | `<0x4A unnamed 1-byte token>` |

Its receiver is the Context chain that ends on the callee byte and re-serialises to the
original bytes (`receiver_retiles: True`):

```
  level 0: object = "EjectFromVehicle.Car"   prop = RVehicleBatmobileBase.ShortRangeGlideKick   skip=9 flag=0
  level 1: object = "Context"   prop = None   skip=17 flag=0
```

The outermost Context is the "call a virtual function on this expression" form - its
`prop_index` is 0 (no property), so `TriggerSpecialMove` is dispatched on the object the
inner Context produced: `Car.ShortRangeGlideKick`.

The parameter order matches the config class's own forwarding body:
`RSpecialMoveConfigConfigurable.TriggerSpecialMove` (export 20377, 41 bytes) reads its own
locals in the order `Controller, MoveLocation, ForceReplicateToClient` and forwards them
to `Config.TriggerSpecialMove`:

- `+18 TriggerSpecialMove(TriggerSpecialMove.Controller, TriggerSpecialMove.MoveLocation, TriggerSpecialMove.ForceReplicateToClient)`

## 2. From the move asset to the animation

`Research/BatmobileGrab/CLASS_DEFAULTS.json` (`Research\BatmobileGrab\CLASS_DEFAULTS.json`) gives the vehicle's default for the
member the call receives:

| member | value |
|---|---|
| `ShortRangeGlideKick` | `GlideKick.GlideKickShort_FromBatmobile` |
| `ShortRangeGlideKickRange` | `2500` cm |

In `Startup.upk` that asset is export 169053 `GlideKickShort_FromBatmobile` (RSpecialMoveConfigConfigurable), 10 bytes, outered to `Batman_Batmobile_Moves.GlideKick`:

| property | field | target |
|---|---|---|
| `Config` | 400 | `GlideKickShort_FromBatmobile.RSpecialMoveConfig_GlideKick` |

So the wrapper is a one-property shim: `RSpecialMoveConfigConfigurable` exists to hold an
inner `RSpecialMoveConfig` (its own `TriggerSpecialMove` does nothing but forward). The
inner config is export 168882 `GlideKickShort_FromBatmobile.RSpecialMoveConfig_GlideKick` (RSpecialMoveConfig_GlideKick), 122 bytes:

| property | field | value |
|---|---|---|
| `AnimName` | 400 | `Batmobile_Short_Range_Glide_Kick`, `Batmobile_Mid_Range_Glide_Kick` |
| `AnimSet` | 124 | `Code.BM_Batmobile` (export 81597) |

The anim set holds 55 sequences; each `AnimSequence` export is literally named
`AnimSequence`, so the human name is its `SequenceName` field (offset 84). Both names in
`AnimName` resolve to exports of that set:

| AnimName | export | bytes | tags | root translation |
|---|---|---|---|---|
| `Batmobile_Short_Range_Glide_Kick` | 75836 | 29672 | 19 | [764.945007, 0.0, 0.0] |
| `Batmobile_Mid_Range_Glide_Kick` | 75835 | 29452 | 19 | [949.433167, 0.0, 0.0] |

Who runs the move: the config class's own default names the instance class
(`Default__RSpecialMoveConfig_GlideKick`, export 31678, field 140):

| tag | value |
|---|---|
| ObjectNCRProperty @512 | `Default__RSpecialMoveConfig_GlideKick.SmashRumble0` |
| BoolProperty @472 | `True` |
| BoolProperty @420 | `True` |
| ObjectNCRProperty @140 | `RSpecialMoveInstance_GlideKick` |

## 3. What the move's code does - and does not - do

`RSpecialMoveInstance_GlideKick.TriggerSpecialMove` (export 32146, 111 bytes) starts by
calling its parent, then does window-villain bookkeeping; it assigns no speed:

```
1c 52 7d 00 00 00 91 7d 00 00 16 0f 00 90 7d 00 00 2e b7 27 01 00 35 14 2a 00 00 1e 2a 00 00 00 00 01 eb 7b 00 00 07 b2 00 82 77 00 90 7d 00 00 2a 16 18 0d 00 77 01 cf 7b 00 00 2a 16 16 0f 01
```

- `+0 RSpecialMoveInstance_RunningRelativeAnimMove.TriggerSpecialMove(TriggerSpecialMove.Loc)`
- `+81 RPlayerController.GetGlideKickThrougWindowTarget(TriggerSpecialMove.WindowTarget, Context)`

The parent `RSpecialMoveInstance_RelativeAnimMove.TriggerSpecialMove` (export 31918, 3256 bytes) sets up the reference location/rotation, copies `OverrideGlideSpeed` from the
config, picks the animation, pushes the controller state and the camera. Its call
inventory in byte order, filtered to nothing - this is the whole list:

- `+64 RSpecialMoveInstance.TriggerSpecialMove(TriggerSpecialMove.MoveLocation)`
- `+153 GetEndMovementStance()`
- `+666 GetAnimSet()`
- `+838 PickRandomAnim()`
- `+1013 GetAnimSet()`
- `+1101 OnPlayerHasBeenMoved()`
- `+1146 RPawnCharacter.BeginQueuedChangePose()`
- `+1207 RPawnCharacter.BeginChangePose()`
- `+1213 FinalAnimStarted()`
- `+2154 GetAnimSet()`
- `+2197 GetCustomIdle()`
- `+2222 RPawnCharacter.EndChangePose()`
- `+2263 GetAnimSet()`
- `+2711 Core.ActivateOutputLink(3)`
- `+2991 RSpecialMoveInstance_RelativeAnimMove.TunnelCamera()`
- `+3249 SetCameraState()`

No `SetVelocity` / `SetRBLinearVelocity` / `AddForce` / impulse call appears in either
body, and the config class's defaults carry no numeric field (the check list asserts
this mechanically). What is left is the animation.

## 4. The animation's root motion

A cooked `AnimSequence` stores its simple properties inline with **no name**, only the
field offset. The offsets below are read off this package and identified by content,
not by name:

| field | type | identified as | evidence |
|---|---|---|---|
| 84 | FName | `SequenceName` | equals the name the anim set/config use |
| 108 | Vector (12 B) | root-motion translation | absent on the 39 sequences that stay in place, present on the 16 that travel (section 5) |
| 124 | Rotator | root-motion rotation | pairs with the vector; non-zero only where the sequence turns |
| 156 | Float | `SequenceLength` (s) | equals (NumFrames-1)/Rate on all 55 sequences |
| 160 | Int | `NumFrames` | 3.7333 s x 30 fps + 1 = 113 |
| 168 | Float | `Rate` (fps) | 30.0 on every sequence of the set |

For `Batmobile_Short_Range_Glide_Kick`:

| measure | value |
|---|---|
| root translation | `(764.945, 0, 0)` cm |
| root rotation | `[0, 0, 0]` |
| frames / rate | 113 @ 30 fps |
| length | 3.733333 s |
| horizontal distance | 764.945 cm = 7.6495 m |
| vertical rise | 0 cm |
| mean horizontal speed | 204.9 cm/s |
| mean step per frame | 6.8299 cm |

The translation is `+X` only: the kick travels straight along the character's
facing direction and does not rise. Per-frame *samples* are not reported: the
sequence's keyframes are stored in the zip-compressed block that follows the tag
stream: 28812 of the export's 29672 bytes - so the mean
step above is exact; the distribution across the 113 frames is **UNKNOWN** here.

`AnimZip_LinearMotion` (field 992) is recorded verbatim for the next pass:

| prop | type | value |
|---|---|---|
| @0 | BoolProperty | `True` |
| @4 | VectorProperty | `[313.805267, 10.643361, 58.19133]` |
| @16 | VectorProperty | `[531.536682, -43.152721, -18.314209]` |
| @32 | StructProperty | `0000000000000000000070330000803f` |

## 5. Cross-check: the field across the whole anim set

Field 108 is not a constant and not a bounding box: it is **absent on 39 of the 55
sequences** and present on the other 16 - exactly the ones whose name says they move
the character (abseil, grapple, step-onto, glide-90, the two kicks, the remote
in/out poses). All 55 sequences of `BM_Batmobile`:

| sequence | field 108 | rot 124 | length s | frames | rate |
|---|---|---|---|---|---|
| `BatMobile_Glide_Boost_In_Back` | - | [0, 0, 0] | 2.3333 | 71 | 30 |
| `BatMobile_Stand_In` | - | [0, 0, 0] | 1.7333 | 53 | 30 |
| `BatMobile_Stand_Out` | - | [0, 0, 0] | 2.0667 | 63 | 30 |
| `BatMobile_Sit_Idle` | - | [0, 0, 0] | 3.3333 | 101 | 30 |
| `BatMobile_Stand_In_Back` | - | [0, 0, 0] | 2.1 | 64 | 30 |
| `BatMobile_Stand_In_Fast_Remote` | - | [0, 0, 0] | 1.6667 | 51 | 30 |
| `BatMobile_Stand_In_Above` | - | [0, 0, 0] | 1.7667 | 54 | 30 |
| `BatMobile_Stand_In_Right_Fast_Remote` | - | [0, 0, 0] | 1.6333 | 50 | 30 |
| `In_Back_Remote_Batmobile` | `[142.25, 38.75, 128.0]` | [0, 0, 0] | 1.8333 | 56 | 30 |
| `BatMobile_Glide_Out_Land_Back` | - | [0, 0, 0] | 3.5333 | 107 | 30 |
| `Batmobile_Mid_Range_Glide_Kick` | `[949.433167, 0.0, 0.0]` | [0, 0, 0] | 3.7667 | 114 | 30 |
| `Batmobile_Short_Range_Glide_Kick` | `[764.945007, 0.0, 0.0]` | [0, 0, 0] | 3.7333 | 113 | 30 |
| `Drive_Idle` | `[118.459198, -1.815986, -6e-06]` | [0, 0, 0] | 3.3333 | 101 | 30 |
| `Steering_Left_To_Right` | `[160.384644, -32.109482, 0.0]` | [0, 0, 0] | 1.4 | 43 | 30 |
| `BatMobile_Glide_Out_Land_Back_02` | - | [0, 0, 0] | 3.3 | 100 | 30 |
| `BatMobile_Stand_In_02` | - | [0, 0, 0] | 1.6667 | 51 | 30 |
| `BatMobile_Stand_In_Back_02` | - | [0, 0, 0] | 1.7333 | 53 | 30 |
| `BatMobile_Stand_In_Front_02` | - | [0, 0, 0] | 1.6667 | 51 | 30 |
| `BatMobile_Stand_In_Right_02` | - | [0, 0, 0] | 1.6667 | 51 | 30 |
| `In_Front_Remote_Batmobile` | `[142.25, 38.75, 128.0]` | [0, 0, 0] | 2 | 61 | 30 |
| `BatMobile_Drift_In_01` | - | [0, 0, 0] | 1.6 | 49 | 30 |
| `BatMobile_Fall_In_01` | - | [0, 0, 0] | 2.0667 | 63 | 30 |
| `BatMobile_Glide_Boost_In_Front` | - | [0, 0, 0] | 1.6333 | 50 | 30 |
| `BatMobile_Glide_Boost_In_Right` | - | [0, 0, 0] | 1.5333 | 47 | 30 |
| `BatMobile_Glide_Boost_In_Left` | - | [0, 0, 0] | 1.6 | 49 | 30 |
| `BatMobile_Glide_In` | - | [0, 0, 0] | 2 | 61 | 30 |
| `BatMobile_Glide_In_Front` | - | [0, 0, 0] | 1.8 | 55 | 30 |
| `BatMobile_Glide_In_Left` | - | [0, 0, 0] | 1.8333 | 56 | 30 |
| `BatMobile_Glide_In_Right` | - | [0, 0, 0] | 1.9 | 58 | 30 |
| `BatMobile_Boost_In_01` | - | [0, 0, 0] | 1.5333 | 47 | 30 |
| `BatMobile_Glide_Out_Front` | - | [0, 0, 0] | 1.2667 | 39 | 30 |
| `BatMobile_Glide_Abseil_In_01` | `[110.000008, 0.0, 344.25]` | [16384, 0, 0] | 1.5333 | 47 | 30 |
| `BatMobile_Glide_Abseil_Out` | `[0.0, 0.0, 500.0]` | [0, 32768, 0] | 1.0333 | 32 | 30 |
| `Run_Jump_In_Back` | - | [0, 0, 0] | 1.8333 | 56 | 30 |
| `Abseiling_Boost_Out` | `[233.0, 0.0, 0.0]` | [0, -32768, 0] | 1.6 | 49 | 30 |
| `BatMobile_Stand_In_Left_Far` | - | [0, 0, 0] | 2.0667 | 63 | 30 |
| `BatMobile_Stand_In_Back_Far` | - | [0, 0, 0] | 2.3333 | 71 | 30 |
| `BatMobile_Stand_In_Front_Far` | - | [0, 0, 0] | 2.2333 | 68 | 30 |
| `grapple_In` | `[11.999965, 0.0, 401.25]` | [16384, 0, 0] | 1.7667 | 54 | 30 |
| `BatMobile_Glide_Out` | - | [0, 0, 0] | 1.4333 | 44 | 30 |
| `Abseiling_Fall_In` | `[211.250031, 0.0, -2.5]` | [16384, 0, 0] | 1.3333 | 41 | 30 |
| `BatMobile_Stand_Out_Roof` | - | [0, 0, 0] | 3 | 91 | 30 |
| `BatMobile_Stand_In_Top_Back` | - | [0, 0, 0] | 1.6667 | 51 | 30 |
| `BatMobile_Stand_In_Top_Front` | - | [0, 0, 0] | 1.5 | 46 | 30 |
| `BatMobile_Stand_In_Back_Right` | - | [0, 0, 0] | 1.7667 | 54 | 30 |
| `BatMobile_Use_Gauntlet` | - | [0, 0, 0] | 5 | 151 | 30 |
| `Abseiling_Swing_In` | `[211.250031, 0.0, -2.5]` | [16384, 0, 0] | 1.6333 | 50 | 30 |
| `BatMobile_Stand_In_Back_Right_Far` | - | [0, 0, 0] | 2.7 | 82 | 30 |
| `BatMobile_Glide_Out_02` | - | [0, 0, 0] | 2 | 61 | 30 |
| `BatMobile_90_Stand_In_Close` | `[0.0, 0.0, 155.169006]` | [0, 0, -16384] | 1.6667 | 51 | 30 |
| `BatMobile_90_Stand_In_Far` | `[0.0, 0.0, 155.169006]` | [0, 0, -16384] | 2.0667 | 63 | 30 |
| `BatMobile_90_Stand_Out` | `[0.0, 0.0, 155.169006]` | [0, 0, 0] | 0.7 | 22 | 30 |
| `BatMobile_Stand_Out_Roof` | `[59.635162, 0.0, 75.5]` | [0, 0, 0] | 2.8333 | 86 | 30 |
| `BatMobile_Stand_In_Front` | - | [0, 0, 0] | 1.6667 | 51 | 30 |
| `BatMobile_Stand_In_Right` | - | [0, 0, 0] | 1.6333 | 50 | 30 |

## 6. What is UNKNOWN

- The *name* of field 108: the cooked tag is a simple property and stores no FName.
  Its content is identified by the census above, not by a name string.
- The per-frame root translation curve: the keyframe block is zip-compressed and its
  format is not decoded here. Only the total and the mean are given.
- The blob at `AnimZip_LinearMotion` (field 992): recorded, not interpreted.
- Which of the two animations plays for a given eject: `AnimName` is an array and the
  parent body calls `PickRandomAnim`; the choice logic is not decoded.
- The token `0x4a` used as the third argument (G3-02j reports it too): a one-byte token
  whose meaning is not established. It is passed through as `ForceReplicateToClient`
  only because the forwarding body's third parameter is that name - not because the
  token was decoded.

STATUS: DONE - the move is named, its asset and instance class are read from the
packages, and the launch is the short-range glide kick animation's root translation
(764.95 cm forward, 0 cm rise, 3.7333 s). Per-frame samples and field names the cooked
packages do not store are marked UNKNOWN.

