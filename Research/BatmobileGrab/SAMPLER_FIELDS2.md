# BmSDK offsets for the BmAK sampler - X (barrage), Y (boost), missiles, booster, A (eject)

**Card:** G3-02f. **Source:** `E:/Modding/_shared/tools/BmSDK-AK/src/BmSDK/Generated` (BmSDK-AK, MIT),
read from the `/// <Type>Property:` comment and the `Ptr + N` getter of each field.
Every offset below is `decoded` at the `.g.cs` file and line in its row; the line number is the
comment line. `Width` is `derived` (distance to the next field, last field to the class size).

| class | .g.cs | size | fields parsed |
|---|---|---|---|
| `RPlayerInput` | `BmSDK/Generated/BmGame/RPlayerInput.g.cs` | 872 | 79 |
| `RVehicleWeapon` | `BmSDK/Generated/BmGame/RVehicleWeapon.g.cs` | 2396 | 57 |
| `RBatmobileMissileLauncher` | `BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs` | 2648 | 30 |
| `RBatmobileBooster` | `BmSDK/Generated/BmGame/RBatmobileBooster.g.cs` | 2400 | 2 |
| `RVehicleBatmobileBase` | `BmSDK/Generated/BmGame/RVehicleBatmobileBase.g.cs` | 8352 | 518 |
| `RPlayerController` | `BmSDK/Generated/BmGame/RPlayerController.g.cs` | 7440 | 998 |

## How to read each kind live

| kind | read |
|---|---|
| `u8` | byte at offset |
| `i32` | int32 at offset |
| `f32` | float32 at offset |
| `bit` | int32 at offset & mask != 0 |
| `ptr` | pointer at offset |
| `fname` | int32 index at offset (and int32 number at offset+4) |
| `tarray` | count = int32 at offset+8 |
| `struct` | raw bytes at offset |

`tarray`: pointer at +0, **count at +8**, Max at +12 - `BmSDK/Classes/Core/TArray.cs:24-26`
(`AllocatorInstance`, `Num`, `Max` in a sequential struct, so x64 offsets 0/8/12).

## 1. Inputs - `RPlayerInput` (Y decoded; X and A UNKNOWN)

| role | field | offset | kind | mask | width | .g.cs line | label |
|---|---|---|---|---|---|---|---|
| Y held (boost) - the digital button byte | `RPlayerInput.bVehicleBoostButton` | 781 (0x30d) | `u8` | - | 1 | `BmSDK/Generated/BmGame/RPlayerInput.g.cs:944` | decoded (BmSDK/Generated/BmGame/RPlayerInput.g.cs:944, u8 @781) |
| Y context - throttle/brake for a boost make/break comparison | `RPlayerInput.bThrottleButton` | 780 (0x30c) | `u8` | - | 1 | `BmSDK/Generated/BmGame/RPlayerInput.g.cs:935` | decoded (BmSDK/Generated/BmGame/RPlayerInput.g.cs:935, u8 @780) |
| Y context - brake | `RPlayerInput.bBrakeButton` | 782 (0x30e) | `u8` | - | 1 | `BmSDK/Generated/BmGame/RPlayerInput.g.cs:953` | decoded (BmSDK/Generated/BmGame/RPlayerInput.g.cs:953, u8 @782) |
| Y context - analog throttle | `RPlayerInput.aThrottleAxis` | 840 (0x348) | `f32` | - | 4 | `BmSDK/Generated/BmGame/RPlayerInput.g.cs:1124` | decoded (BmSDK/Generated/BmGame/RPlayerInput.g.cs:1124, f32 @840) |
| Y context - analog brake | `RPlayerInput.aBrakeAxis` | 844 (0x34c) | `f32` | - | 4 | `BmSDK/Generated/BmGame/RPlayerInput.g.cs:1133` | decoded (BmSDK/Generated/BmGame/RPlayerInput.g.cs:1133, f32 @844) |
| combat context - primary fire | `RPlayerInput.bFireVehicleWeapon` | 778 (0x30a) | `u8` | - | 1 | `BmSDK/Generated/BmGame/RPlayerInput.g.cs:917` | decoded (BmSDK/Generated/BmGame/RPlayerInput.g.cs:917, u8 @778) |
| combat context - secondary fire | `RPlayerInput.bFireVehicleSecondaryWeapon` | 779 (0x30b) | `u8` | - | 1 | `BmSDK/Generated/BmGame/RPlayerInput.g.cs:926` | decoded (BmSDK/Generated/BmGame/RPlayerInput.g.cs:926, u8 @779) |
| eject - modifier byte beside the eject | `RPlayerInput.bBatmobileEjectModifier` | 786 (0x312) | `u8` | - | 1 | `BmSDK/Generated/BmGame/RPlayerInput.g.cs:989` | decoded (BmSDK/Generated/BmGame/RPlayerInput.g.cs:989, u8 @786) |
| handbrake (control sample, unchanged behaviour) | `RPlayerInput.bHandBrakeButton` | 776 (0x308) | `u8` | - | 1 | `BmSDK/Generated/BmGame/RPlayerInput.g.cs:899` | decoded (BmSDK/Generated/BmGame/RPlayerInput.g.cs:899, u8 @776) |

- `RPlayerInput.bVehicleBoostButton`: D-11 user mapping: Y = boost in pursuit; the field name is the only RPlayerInput member that names the vehicle boost
- `RPlayerInput.bThrottleButton`: read with bBrakeButton/aThrottleAxis to tell a boost from a coast
- `RPlayerInput.bBatmobileEjectModifier`: the only eject-named input field in RPlayerInput; what button it modifies is not in the layout

## 2. Missile launcher - `RBatmobileMissileLauncher` and its base `RVehicleWeapon`

| role | field | offset | kind | mask | width | .g.cs line | label |
|---|---|---|---|---|---|---|---|
| target count ceiling | `RBatmobileMissileLauncher.MaxTargets` | 2396 (0x95c) | `i32` | - | 4 | `BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:291` | decoded (BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:291, i32 @2396) |
| targets currently held (array; read Num at +8) | `RBatmobileMissileLauncher.CurrentTargets` | 2400 (0x960) | `tarray` | - | 16 | `BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:300` | decoded (BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:300, tarray @2400) |
| targets on the previous frame (array) | `RBatmobileMissileLauncher.LastTargets` | 2416 (0x970) | `tarray` | - | 16 | `BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:309` | decoded (BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:309, tarray @2416) |
| firing flag | `RVehicleWeapon.bFiring` | 2084 (0x824) | `bit` | 2 | 4 | `BmSDK/Generated/BmGame/RVehicleWeapon.g.cs:637` | decoded (BmSDK/Generated/BmGame/RVehicleWeapon.g.cs:637, bit @2084, mask 0x2) |
| continuous-fire flag (same word as bFiring) | `RVehicleWeapon.ContinuousFire` | 2084 (0x824) | `bit` | 1 | 4 | `BmSDK/Generated/BmGame/RVehicleWeapon.g.cs:628` | decoded (BmSDK/Generated/BmGame/RVehicleWeapon.g.cs:628, bit @2084, mask 0x1) |
| cooldown remaining | `RVehicleWeapon.CoolDown` | 2092 (0x82c) | `f32` | - | 4 | `BmSDK/Generated/BmGame/RVehicleWeapon.g.cs:727` | decoded (BmSDK/Generated/BmGame/RVehicleWeapon.g.cs:727, f32 @2092) |
| weapon cooldown (second timer) | `RVehicleWeapon.WeaponCoolDown` | 2096 (0x830) | `f32` | - | 4 | `BmSDK/Generated/BmGame/RVehicleWeapon.g.cs:736` | decoded (BmSDK/Generated/BmGame/RVehicleWeapon.g.cs:736, f32 @2096) |
| fire interval | `RVehicleWeapon.FiringInterval` | 2088 (0x828) | `f32` | - | 4 | `BmSDK/Generated/BmGame/RVehicleWeapon.g.cs:718` | decoded (BmSDK/Generated/BmGame/RVehicleWeapon.g.cs:718, f32 @2088) |
| cooldown configured for the launcher | `RBatmobileMissileLauncher.CooldownDelay` | 2448 (0x990) | `f32` | - | 4 | `BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:354` | decoded (BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:354, f32 @2448) |
| initial delay before the first missile | `RBatmobileMissileLauncher.InitialFireDelay` | 2440 (0x988) | `f32` | - | 4 | `BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:336` | decoded (BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:336, f32 @2440) |
| spacing between missiles in a volley | `RBatmobileMissileLauncher.FireInterval` | 2444 (0x98c) | `f32` | - | 4 | `BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:345` | decoded (BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:345, f32 @2444) |
| index of the next target to fire at | `RBatmobileMissileLauncher.NthTarget` | 2560 (0xa00) | `i32` | - | 4 | `BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:477` | decoded (BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:477, i32 @2560) |
| launcher state name | `RBatmobileMissileLauncher.LastState` | 2564 (0xa04) | `fname` | - | 8 | `BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:486` | decoded (BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:486, fname @2564) |
| current target level | `RBatmobileMissileLauncher.CurrentLevel` | 2588 (0xa1c) | `i32` | - | 4 | `BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:504` | decoded (BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:504, i32 @2588) |
| per-level target cap (array) | `RBatmobileMissileLauncher.MaxTargetsPerLevel` | 2592 (0xa20) | `tarray` | - | 16 | `BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:513` | decoded (BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:513, tarray @2592) |
| missile sockets (array) | `RBatmobileMissileLauncher.MissileSockets` | 2608 (0xa30) | `tarray` | - | 16 | `BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:522` | decoded (BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:522, tarray @2608) |
| socket index in use | `RBatmobileMissileLauncher.CurrentMissileSocket` | 2624 (0xa40) | `i32` | - | 4 | `BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:531` | decoded (BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:531, i32 @2624) |
| unlimited-missiles window | `RBatmobileMissileLauncher.InfinitMissilesTime` | 2628 (0xa44) | `f32` | - | 4 | `BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:540` | decoded (BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:540, f32 @2628) |
| missiles in flight (array) | `RBatmobileMissileLauncher.FiredProjectiles` | 2632 (0xa48) | `tarray` | - | 16 | `BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:549` | decoded (BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:549, tarray @2632) |
| lock-on cone | `RBatmobileMissileLauncher.LockOnAngle` | 2432 (0x980) | `f32` | - | 4 | `BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:318` | decoded (BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:318, f32 @2432) |
| lock-on range | `RBatmobileMissileLauncher.LockOnRange` | 2436 (0x984) | `f32` | - | 4 | `BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:327` | decoded (BmSDK/Generated/BmGame/RBatmobileMissileLauncher.g.cs:327, f32 @2436) |
| aim target inherited from the weapon base | `RVehicleWeapon.AimTarget` | 2168 (0x878) | `ptr` | - | 8 | `BmSDK/Generated/BmGame/RVehicleWeapon.g.cs:835` | decoded (BmSDK/Generated/BmGame/RVehicleWeapon.g.cs:835, ptr @2168) |

- `RBatmobileMissileLauncher.MaxTargets`: the array Max may exceed this; compare Num against it
- `RBatmobileMissileLauncher.CurrentTargets`: pointer +0, Num +8, Max +12
- `RBatmobileMissileLauncher.LastTargets`: compare with CurrentTargets to see a re-target
- `RVehicleWeapon.bFiring`: inherited by both missile and booster: RBatmobileBooster : RVehicleWeapon
- `RVehicleWeapon.CoolDown`: per-weapon timer
- `RVehicleWeapon.WeaponCoolDown`: distinct from CoolDown; which one gates the barrage is UNKNOWN
- `RBatmobileMissileLauncher.FireInterval`: note: a different field from RVehicleWeapon.FiringInterval
- `RBatmobileMissileLauncher.LastState`: FName: read index and number; resolve through GNames
- `RBatmobileMissileLauncher.CurrentLevel`: with MaxTargetsPerLevel, the per-level target cap
- `RBatmobileMissileLauncher.InfinitMissilesTime`: seconds of free fire; 0 when inactive

## 3. Booster - `RBatmobileBooster` and the vehicle's boost flags

| role | field | offset | kind | mask | width | .g.cs line | label |
|---|---|---|---|---|---|---|---|
| boost active | `RBatmobileBooster.bBoosting` | 2396 (0x95c) | `bit` | 1 | 4 | `BmSDK/Generated/BmGame/RBatmobileBooster.g.cs:82` | decoded (BmSDK/Generated/BmGame/RBatmobileBooster.g.cs:82, bit @2396, mask 0x1) |
| boost warming up | `RBatmobileBooster.bWarming` | 2396 (0x95c) | `bit` | 2 | 4 | `BmSDK/Generated/BmGame/RBatmobileBooster.g.cs:91` | decoded (BmSDK/Generated/BmGame/RBatmobileBooster.g.cs:91, bit @2396, mask 0x2) |
| boost locked (cannot engage) | `RVehicleBatmobileBase.bBoostLocked` | 4568 (0x11d8) | `bit` | 16384 | 4 | `BmSDK/Generated/BmGame/RVehicleBatmobileBase.g.cs:4581` | decoded (BmSDK/Generated/BmGame/RVehicleBatmobileBase.g.cs:4581, bit @4568, mask 0x4000) |
| boost permanently allowed | `RVehicleBatmobileBase.InfiniteBoost` | 4568 (0x11d8) | `bit` | 536870912 | 4 | `BmSDK/Generated/BmGame/RVehicleBatmobileBase.g.cs:4716` | decoded (BmSDK/Generated/BmGame/RVehicleBatmobileBase.g.cs:4716, bit @4568, mask 0x20000000) |
| afterburner particle component | `RVehicleBatmobileBase.AfterburnerSystem` | 4636 (0x121c) | `ptr` | - | 8 | `BmSDK/Generated/BmGame/RVehicleBatmobileBase.g.cs:5298` | decoded (BmSDK/Generated/BmGame/RVehicleBatmobileBase.g.cs:5298, ptr @4636) |
| last boost pickup time | `RVehicleBatmobileBase.LastBoostPickupTime` | 6580 (0x19b4) | `f32` | - | 4 | `BmSDK/Generated/BmGame/RVehicleBatmobileBase.g.cs:7527` | decoded (BmSDK/Generated/BmGame/RVehicleBatmobileBase.g.cs:7527, f32 @6580) |
| boosting-out state byte | `RVehicleBatmobileBase.BoostingOut` | 5901 (0x170d) | `u8` | - | 1 | `BmSDK/Generated/BmGame/RVehicleBatmobileBase.g.cs:6812` | decoded (BmSDK/Generated/BmGame/RVehicleBatmobileBase.g.cs:6812, u8 @5901) |

- `RBatmobileBooster.bBoosting`: the booster object's own flag; setter is the afterburner code
- `RBatmobileBooster.bWarming`: same int word as bBoosting
- `RVehicleBatmobileBase.bBoostLocked`: same int word as InfiniteBoost
- `RVehicleBatmobileBase.AfterburnerSystem`: non-null while the effect exists; not an activity flag
- `RVehicleBatmobileBase.LastBoostPickupTime`: a timestamp, not a duration
- `RVehicleBatmobileBase.BoostingOut`: byte, not the bBoosting bit

## 4. Eject - vehicle and player-controller side

| role | field | offset | kind | mask | width | .g.cs line | label |
|---|---|---|---|---|---|---|---|
| eject type configured | `RVehicleBatmobileBase.MaxEjectType` | 5902 (0x170e) | `u8` | - | 2 | `BmSDK/Generated/BmGame/RVehicleBatmobileBase.g.cs:6821` | decoded (BmSDK/Generated/BmGame/RVehicleBatmobileBase.g.cs:6821, u8 @5902) |
| eject upward distance | `RVehicleBatmobileBase.EjectUpDist` | 6032 (0x1790) | `f32` | - | 4 | `BmSDK/Generated/BmGame/RVehicleBatmobileBase.g.cs:7004` | decoded (BmSDK/Generated/BmGame/RVehicleBatmobileBase.g.cs:7004, f32 @6032) |
| forced next eject | `RVehicleBatmobileBase.OverrideNextEject` | 5604 (0x15e4) | `ptr` | - | 8 | `BmSDK/Generated/BmGame/RVehicleBatmobileBase.g.cs:6373` | decoded (BmSDK/Generated/BmGame/RVehicleBatmobileBase.g.cs:6373, ptr @5604) |
| eject type chosen at the last eject | `RPlayerController.CurrentEjectType` | 3502 (0xdae) | `u8` | - | 2 | `BmSDK/Generated/BmGame/RPlayerController.g.cs:28120` | decoded (BmSDK/Generated/BmGame/RPlayerController.g.cs:28120, u8 @3502) |
| time of the last eject from the Batmobile | `RPlayerController.LastEjectFromBatmobileTime` | 7188 (0x1c14) | `f32` | - | 4 | `BmSDK/Generated/BmGame/RPlayerController.g.cs:31720` | decoded (BmSDK/Generated/BmGame/RPlayerController.g.cs:31720, f32 @7188) |
| last eject/exit time comparison for X use | `RPlayerController.UsedQuickGadget` | 3452 (0xd7c) | `bit` | 524288 | 4 | `BmSDK/Generated/BmGame/RPlayerController.g.cs:26194` | decoded (BmSDK/Generated/BmGame/RPlayerController.g.cs:26194, bit @3452, mask 0x80000) |

- `RVehicleBatmobileBase.OverrideNextEject`: object pointer; non-null forces a scripted eject
- `RPlayerController.CurrentEjectType`: player-controller side; offset resolved here, value observed live
- `RPlayerController.UsedQuickGadget`: bit; the QuickGadgetX handler sets it, but no per-button field exists

## 5. Candidates - the field exists, the binding does not

| field | offset | why it is not claimed |
|---|---|---|
| `RPlayerInput.bReadyGadgetButton` | 773 | a gadget button byte, but the layout does not say it is X (could be the gadget-wheel open) |
| `RPlayerInput.bGadgetSelectWheel` | 784 | the gadget wheel input, not the X action |
| `RPlayerInput.bCancelButton` | 774 | cancel; the live sampler already watches this one |
| `RPlayerController.UsedQuickGadget` | - | set by the QuickGadgetX handler; a consequence of X, not the input byte |

## 6. UNKNOWN - no such field in these layouts

1. **X (missile barrage) input byte** - tried: all 79 top-level property blocks of RPlayerInput were parsed; there is no field named *QuickGadgetX*, *XButton*, *Barrage* or similar. RPlayerController.QuickGadgetX is a Function (BmSDK/Generated/BmGame/RPlayerController.g.cs:491), not a field, so the byte the X binding writes is not in the layout. Where it would be: answer from RPlayerInput's bind table or BmGame/Config/BmInput.ini - neither is in these files.
2. **A (eject) input byte** - tried: RPlayerInput has bBatmobileEjectModifier (786) and no bAButton / bActionButton / bEjectButton; grep over the whole Generated tree finds no such property. Where it would be: same place as X: the bind table / BmInput.ini; the modifier byte at 786 is decoded but its trigger button is not.
3. **boost duration / boost time field** - tried: RBatmobileBooster has only bBoosting and bWarming (2 fields, size 2400); RVehicleBatmobileBase.GetBoostPct is a Function (g.cs:3084), not a field, and LastBoostPickupTime (6580) is a timestamp. grep over Generated finds no BoostTimer/BoostTime field. Where it would be: observe bBoosting transitions and measure the interval instead of reading a timer.
4. **TArray element stride for CurrentTargets / FiredProjectiles** - tried: the layouts give the array offset and the element type but not the element size; BmSDK MarshalUtil.GetSizeUnmanaged<T> would, and is not in the generated tree. Where it would be: needed only to walk the targets, not to count them.

## 7. Oracles (`--check` re-runs all of them)

| oracle | ok | detail |
|---|---|---|
| `expected_offsets` | True | {"checked": 53, "failures": []} |
| `line_points_at_comment` | True | {"failures": [], "count": 0} |
| `widths_fit_class` | True | {"failures": []} |
| `mask_uniqueness` | True | {"failures": []} |
| `offsets_ascending` | True | {"failures": []} |
| `class_sizes` | True | {"expected": {"RPlayerInput": 872, "RVehicleWeapon": 2396, "RBatmobileMissileLauncher": 2648, "RBatmobileBooster": 2400, "RVehicleBatmobileBase": 8352}, "mismatch": {}} |
| `tarray_layout` | True | {"lines": [24, 25, 26], "offsets": {"data": 0, "count": 8, "max": 12}, "rule": "IntPtr,int,int sequential -> 0/8/12 (x64)"} |
| `observables_resolve` | True | {"count": 44, "missing": []} |
| `observables_unique` | True | {"count": 44, "unique": 44} |
| `unknowns_present` | True | {"unknowns": ["X (missile barrage) input byte", "A (eject) input byte", "boost duration / boost time field", "TArray element stride for CurrentTargets / FiredProjectiles"]} |
| `booster_inherits_weapon` | True | {"rule": "RBatmobileBooster : RVehicleWeapon, so bFiring/CoolDown are inherited at the same offsets", "bFiring": 2084} |
| `collision_mode_offset_matches_sampler` | True | {"layout": 5895, "sampler": 5895, "note": "bmak_runtime_sampler.py VEH uses 0x1707; the layout says 5895"} |
