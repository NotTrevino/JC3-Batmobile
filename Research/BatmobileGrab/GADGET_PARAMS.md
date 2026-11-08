# GADGET_PARAMS - the 48 `RBatmobileRemoteBm` parameters, valued

**Card:** GADGET-params (closes the second half of the G3-05 open item). **Gadget class:**
`BmScript.RBatmobileRemoteBm` in `Startup.upk` / `StartupPatch.upk`. Values come from its **class default
object** (`Default__RBatmobileRemoteBm`), not from an archetype: this class ships no archetype
in either package, and the CDO is where the cooked defaults live.

**Result:** of the 48 members, **23 hold a value** (11 floats, 10 object pointers, 2 bools)
and **25 are behaviour** (22 functions, 3 states). The CDO serialises **16** of the
23 value slots; the other **7** carry no tag, so their values are not in the
stream and are marked UNKNOWN rather than assumed to be None/false.

## 1. What was read (decoded)

| role | package | export | object | class | payload | tags | walk |
|---|---|---|---|---|---:|---:|---|
| CDO | `Startup.upk` | 536 | `BmScript.Default__RBatmobileRemoteBm` | `RBatmobileRemoteBm` | 364 | 33 | `eof` at 362 |
| CDO | `StartupPatch.upk` | 520 | `BmScript.Default__RBatmobileRemoteBm` | `RBatmobileRemoteBm` | 364 | 33 | `eof` at 362 |
| class | `Startup.upk` | 535 | `BmScript.RBatmobileRemoteBm` | `RBatmobileRemoteBm` | - | - | - |

Class size: **2456** bytes (`RBatmobileRemoteBm.g.cs` line with `(size = 2456)`); every tag offset is inside it. The CDO payload sha1 is `2b569423633ab837a085cdf2a07453fb283b0856` in `Startup.upk` and `0a5b9b2a2948b862ea53b53da26eb8cc755b9ea6` in `StartupPatch.upk` — different bytes (the object
index tables differ), identical decoded values (oracle `packages_agree`).

**Layout chain** used for naming, from the bindings (`RBatmobileRemoteBm.g.cs` etc.):

| class | declared properties | source |
|---|---:|---|
| `RBatmobileRemoteBm` | 23 | `RBatmobileRemoteBm.g.cs` |
| `RBatmobileRemote` | 18 | `RBatmobileRemote.g.cs` |
| `RInventoryGadget` | 153 | `RInventoryGadget.g.cs` |
| `Inventory` | 15 | `Inventory.g.cs` |
| `Actor` | 212 | `Actor.g.cs` |
| `StateObject` | 1 | `StateObject.g.cs` |
| `GameObject` | 14 | `GameObject.g.cs` |
| `IGameObject` | 0 | `-` |

A tag is named only by a member declared at **exactly** its offset with a compatible kind
(`same_kind`: a cooked pointer is `ObjectNCRProperty` whatever the declared subclass; a native
vector is `StructProperty` in the bindings). Nothing is named by resemblance. All **95** tags resolve.

## 2. The 23 value parameters (the table to translate from)

`class` is the declaring class; `off` the class slot; `source` the package/export/payload
offset of the tag, so any row can be re-read without a tool.

| class | field | type | value | source | label |
|---|---|---|---|---|---|
| `RBatmobileRemoteBm` | `RelativeAimingCurvePower` | FloatProperty | 1.0 | `Startup.upk` 536 @0x7c (class 0x994; `RBatmobileRemoteBm.g.cs:534`) | decoded |
| `RBatmobileRemoteBm` | `MaxAimY` | FloatProperty | 0.899999976 | `Startup.upk` 536 @0x74 (class 0x990; `RBatmobileRemoteBm.g.cs:525`) | decoded |
| `RBatmobileRemoteBm` | `MaxAimX` | FloatProperty | 0.899999976 | `Startup.upk` 536 @0x6c (class 0x98c; `RBatmobileRemoteBm.g.cs:516`) | decoded |
| `RBatmobileRemoteBm` | `CursorReturnDelay` | FloatProperty | 2.0 | `Startup.upk` 536 @0x64 (class 0x988; `RBatmobileRemoteBm.g.cs:507`) | decoded |
| `RBatmobileRemoteBm` | `CursorReturnFactor` | FloatProperty | 2.0 | `Startup.upk` 536 @0x5c (class 0x984; `RBatmobileRemoteBm.g.cs:498`) | decoded |
| `RBatmobileRemoteBm` | `CursorDecel` | FloatProperty | 10.0 | `Startup.upk` 536 @0x54 (class 0x980; `RBatmobileRemoteBm.g.cs:489`) | decoded |
| `RBatmobileRemoteBm` | `CursorAccel` | FloatProperty | 5.0 | `Startup.upk` 536 @0x4c (class 0x97c; `RBatmobileRemoteBm.g.cs:480`) | decoded |
| `RBatmobileRemoteBm` | `CursorSpeed` | FloatProperty | 3.0 | `Startup.upk` 536 @0x44 (class 0x978; `RBatmobileRemoteBm.g.cs:471`) | decoded |
| `RBatmobileRemoteBm` | `CurrentJam` | FloatProperty | -1.0 | `Startup.upk` 536 @0x3c (class 0x974; `RBatmobileRemoteBm.g.cs:462`) | decoded |
| `RBatmobileRemoteBm` | `JammerTime` | FloatProperty | 1.5 | `Startup.upk` 536 @0x34 (class 0x970; `RBatmobileRemoteBm.g.cs:453`) | decoded |
| `RBatmobileRemoteBm` | `JammingRange` | FloatProperty | 10000.0 | `Startup.upk` 536 @0x2c (class 0x968; `RBatmobileRemoteBm.g.cs:426`) | decoded |
| `RBatmobileRemoteBm` | `RemoteControlBatmobileMove` | ObjectProperty | `Batmobile_Remote.RemoteControlBatmobile` (RSpecialMoveConfigConfigurable) | `Startup.upk` 536 @0x24 (class 0x958; `RBatmobileRemoteBm.g.cs:408`) | decoded |
| `RBatmobileRemoteBm` | `CallSound` | ObjectProperty | `Engine.Play_Gauntlet_Batmobile_Call` (AkEvent) | `Startup.upk` 536 @0x1c (class 0x948; `RBatmobileRemoteBm.g.cs:390`) | decoded |
| `RBatmobileRemoteBm` | `CancelSound2` | ObjectProperty | `Engine.Play_Remote_Gadget_Off` (AkEvent) | `Startup.upk` 536 @0x14 (class 0x940; `RBatmobileRemoteBm.g.cs:381`) | decoded |
| `RBatmobileRemoteBm` | `CancelSound` | ObjectProperty | `Ww_CHR_RemoteGadget.Play_Remote_Gadget` (AkEvent) | `Startup.upk` 536 @0xc (class 0x938; `RBatmobileRemoteBm.g.cs:372`) | decoded |
| `RBatmobileRemoteBm` | `FireSound` | ObjectProperty | `Ww_CHR_RemoteGadget.Play_Remote_Gadget` (AkEvent) | `Startup.upk` 536 @0x4 (class 0x930; `RBatmobileRemoteBm.g.cs:363`) | decoded |

## 3. The 7 value slots the CDO does not serialise (UNKNOWN value)

A cooked stream omits a property only when it equals the class's own initial value, so these
are almost certainly `None`/`false` — but that is a **hypothesis about the cooker, not a byte
fact**, and it is not used. Their offsets and types are decoded from the bindings.

| class | field | type | class off | bindings | label |
|---|---|---|---|---|---|
| `RBatmobileRemoteBm` | `bRelativeAiming` | BoolProperty | 0x96c | RBatmobileRemoteBm.g.cs:444 | UNKNOWN (no tag in either CDO) |
| `RBatmobileRemoteBm` | `ScreenOn` | BoolProperty | 0x96c | RBatmobileRemoteBm.g.cs:435 | UNKNOWN (no tag in either CDO) |
| `RBatmobileRemoteBm` | `ReachedRemoteHardLimitThought` | ObjectProperty | 0x960 | RBatmobileRemoteBm.g.cs:417 | UNKNOWN (no tag in either CDO) |
| `RBatmobileRemoteBm` | `CurrentRiotSuppressorTarget` | ObjectProperty | 0x950 | RBatmobileRemoteBm.g.cs:399 | UNKNOWN (no tag in either CDO) |
| `RBatmobileRemoteBm` | `NpcBatmobileTarget` | ObjectProperty | 0x928 | RBatmobileRemoteBm.g.cs:354 | UNKNOWN (no tag in either CDO) |
| `RBatmobileRemoteBm` | `CallingVehicle` | ObjectProperty | 0x920 | RBatmobileRemoteBm.g.cs:345 | UNKNOWN (no tag in either CDO) |
| `RBatmobileRemoteBm` | `RiotSuppressorBatmobile` | ObjectProperty | 0x918 | RBatmobileRemoteBm.g.cs:336 | UNKNOWN (no tag in either CDO) |

## 4. The 25 behaviour members (no default value exists)

| class | field | export | payload | why there is no value |
|---|---|---:|---:|---|
| `Function` | `GetPromptName` | 422 | 49 | Function export: behaviour, not a parameter |
| `Function` | `GetHelpPrompt` | 426 | 45 | Function export: behaviour, not a parameter |
| `Function` | `GetPrimedPose` | 434 | 316 | Function export: behaviour, not a parameter |
| `Function` | `GetFireAnim` | 442 | 788 | Function export: behaviour, not a parameter |
| `Function` | `PlayerTick` | 444 | 96 | Function export: behaviour, not a parameter |
| `Function` | `CallBatmobile` | 445 | 70 | Function export: behaviour, not a parameter |
| `Function` | `CancelCallBatmobile` | 446 | 66 | Function export: behaviour, not a parameter |
| `Function` | `DrawTarget` | 448 | 490 | Function export: behaviour, not a parameter |
| `Function` | `ShowFailIcon` | 449 | 39 | Function export: behaviour, not a parameter |
| `Function` | `ClearTarget` | 450 | 39 | Function export: behaviour, not a parameter |
| `Function` | `GetAimAtRotation` | 452 | 65 | Function export: behaviour, not a parameter |
| `State` | `Holstered` | 457 | 59 | State export: behaviour, not a parameter |
| `State` | `Primed` | 470 | 107 | State export: behaviour, not a parameter |
| `State` | `ControlBatmobileRiotSuppressor` | 516 | 155 | State export: behaviour, not a parameter |
| `Function` | `DontMoveCursor` | 517 | 39 | Function export: behaviour, not a parameter |
| `Function` | `PowerOnScreen` | 518 | 134 | Function export: behaviour, not a parameter |
| `Function` | `PowerOffScreen` | 519 | 83 | Function export: behaviour, not a parameter |
| `Function` | `NotifyCallBatmobileToMe` | 520 | 76 | Function export: behaviour, not a parameter |
| `Function` | `NotifyRemoteDriveCancelled` | 521 | 113 | Function export: behaviour, not a parameter |
| `Function` | `NotifyBatmanPickedUp` | 522 | 49 | Function export: behaviour, not a parameter |
| `Function` | `StartChargingJammer` | 523 | 50 | Function export: behaviour, not a parameter |
| `Function` | `GetFiringAnimationOverlay` | 525 | 49 | Function export: behaviour, not a parameter |
| `Function` | `GetPC` | 528 | 119 | Function export: behaviour, not a parameter |
| `Function` | `OnGadgetWheelSelected` | 533 | 668 | Function export: behaviour, not a parameter |
| `Function` | `NotifyReachedHardRemoteLimit` | 534 | 52 | Function export: behaviour, not a parameter |

Their bodies are **stripped** (the payloads are untagged 30-byte records per `PACKAGES_G305.md` §4), so any constant a function would use is UNKNOWN — that is where the
remaining remote-gadget behaviour lives.

## 5. Inherited tags the CDO also serialises (decoded)

These are not in the 48, but they identify and shape the gadget, so the translation needs them
next to the table: the enum that names the gadget and its HUD slot, the mesh component, the
aim config, and the inherited bool word.

| class | field | type | value | source |
|---|---|---|---|---|
| `RBatmobileRemote` | `AimPosition` | StructProperty | [0.5, 0.5, 0.0] | `Startup.upk` 536 @0x84 (class 0x824; `RBatmobileRemote.g.cs:159`) |
| `RInventoryGadget` | `GadgetType` | ByteProperty | `GA_Gadget_JammerGadget` (enum `GadgetType`) | `Startup.upk` 536 @0xa4 (class 0x311; `RInventoryGadget.g.cs:1968`) |
| `RInventoryGadget` | `HudGadgetId` | ByteProperty | `FGID_BatarangMulti2` (enum `HudGadgetId`) | `Startup.upk` 536 @0xc0 (class 0x314; `RInventoryGadget.g.cs:1995`) |
| `RInventoryGadget` | `Mesh` | ComponentProperty | `Default__RBatmobileRemoteBm.GadgetMesh` (SkeletalMeshComponent) | `Startup.upk` 536 @0xcc (class 0x318; `RInventoryGadget.g.cs:2022`) |
| `RInventoryGadget` | `EquipBoneName` | NameProperty | `Gundummy` | `Startup.upk` 536 @0xd4 (class 0x378; `RInventoryGadget.g.cs:2130`) |
| `RInventoryGadget` | `EquipBoneName2` | NameProperty | `Gundummy02` | `Startup.upk` 536 @0xe0 (class 0x380; `RInventoryGadget.g.cs:2139`) |
| `RInventoryGadget` | `bSelectable` | BoolProperty | false | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2377`) |
| `RInventoryGadget` | `bAiming` | BoolProperty | false | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2386`) |
| `RInventoryGadget` | `bAutomaticAiming` | BoolProperty | false | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2395`) |
| `RInventoryGadget` | `bNoQuickFire` | BoolProperty | false | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2404`) |
| `RInventoryGadget` | `bUnequipToSocket` | BoolProperty | true | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2413`) |
| `RInventoryGadget` | `bCanUseXRay` | BoolProperty | true | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2422`) |
| `RInventoryGadget` | `bCanRechargeFromZeroAmmo` | BoolProperty | false | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2431`) |
| `RInventoryGadget` | `bUsableFromVantagePoints` | BoolProperty | true | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2440`) |
| `RInventoryGadget` | `bUsableFromCornerCover` | BoolProperty | true | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2449`) |
| `RInventoryGadget` | `bUsableFromCrawlSpace` | BoolProperty | true | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2458`) |
| `RInventoryGadget` | `bNotUsableFromWire` | BoolProperty | false | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2467`) |
| `RInventoryGadget` | `bLeaveCoverAfterThrow` | BoolProperty | false | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2476`) |
| `RInventoryGadget` | `bCanUseFromSilentPredator` | BoolProperty | false | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2485`) |
| `RInventoryGadget` | `bDontLockCornerAiming` | BoolProperty | false | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2494`) |
| `RInventoryGadget` | `bForceShowGadget` | BoolProperty | false | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2503`) |
| `RInventoryGadget` | `bRunningThrow` | BoolProperty | false | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2512`) |
| `RInventoryGadget` | `bCanEquipWhileRecharging` | BoolProperty | false | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2521`) |
| `RInventoryGadget` | `bCanEquipWhileFlying` | BoolProperty | false | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2530`) |
| `RInventoryGadget` | `bSelectableLast` | BoolProperty | false | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2539`) |
| `RInventoryGadget` | `AutoTargetRequiresLOS` | BoolProperty | true | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2548`) |
| `RInventoryGadget` | `MustAutoTarget` | BoolProperty | false | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2557`) |
| `RInventoryGadget` | `bUseAbsoluteTurnForGetOut` | BoolProperty | false | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2566`) |
| `RInventoryGadget` | `bUseRechargeDisplay` | BoolProperty | true | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2575`) |
| `RInventoryGadget` | `bDoLOSCheckFromPawn` | BoolProperty | false | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2584`) |
| `RInventoryGadget` | `bGadgetCanBeMirrored` | BoolProperty | true | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2593`) |
| `RInventoryGadget` | `bRecharging` | BoolProperty | true | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2602`) |
| `RInventoryGadget` | `bHighlighted` | BoolProperty | false | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2611`) |
| `RInventoryGadget` | `bXRayMode` | BoolProperty | false | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2620`) |
| `RInventoryGadget` | `bAllowGrappleUse` | BoolProperty | false | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2629`) |
| `RInventoryGadget` | `bReverseButtonControlsOnPS3` | BoolProperty | false | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2638`) |
| `RInventoryGadget` | `bEmergencyFire` | BoolProperty | false | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2647`) |
| `RInventoryGadget` | `bOverriddenCombatMove` | BoolProperty | false | `Startup.upk` 536 @0xec (class 0x460; `RInventoryGadget.g.cs:2656`) |
| `RInventoryGadget` | `TargetClass` | NameProperty | `AntiPersonelGun` | `Startup.upk` 536 @0xf4 (class 0x4b4; `RInventoryGadget.g.cs:2938`) |
| `RInventoryGadget` | `GadgetListEnum` | IntProperty | 13 | `Startup.upk` 536 @0x100 (class 0x514; `RInventoryGadget.g.cs:3034`) |
| `RInventoryGadget` | `WireLeftTurn` | NameProperty | `Omnitron_Wire_180_Left` | `Startup.upk` 536 @0x108 (class 0x530; `RInventoryGadget.g.cs:3067`) |
| `RInventoryGadget` | `WireRightTurn` | NameProperty | `Omnitron_Wire_180_Right` | `Startup.upk` 536 @0x114 (class 0x538; `RInventoryGadget.g.cs:3076`) |
| `RInventoryGadget` | `RailingLeftTurn` | NameProperty | `Omnitron_Railing_180_Left` | `Startup.upk` 536 @0x120 (class 0x540; `RInventoryGadget.g.cs:3085`) |
| `RInventoryGadget` | `RailingRightTurn` | NameProperty | `Omnitron_Railing_180_Right` | `Startup.upk` 536 @0x12c (class 0x548; `RInventoryGadget.g.cs:3094`) |
| `RInventoryGadget` | `AssociatedGadgetFlagName` | StrProperty | "Equip_BatmobileRemote" | `Startup.upk` 536 @0x13c (class 0x558; `RInventoryGadget.g.cs:3112`) |
| `RInventoryGadget` | `fLastPlayedGadgetSpeechTime` | FloatProperty | -60.0 | `Startup.upk` 536 @0x156 (class 0x5c8; `RInventoryGadget.g.cs:3208`) |
| `RInventoryGadget` | `fGadgetSpeechCooldownTime` | FloatProperty | 60.0 | `Startup.upk` 536 @0x15e (class 0x5cc; `RInventoryGadget.g.cs:3217`) |
| `Actor` | `bUpdateSimulatedPosition` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:6834`) |
| `Actor` | `bTearOff` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:6843`) |
| `Actor` | `bOnlyDirtyReplication` | BoolProperty | true | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:6852`) |
| `Actor` | `bAllowFluidSurfaceInteraction` | BoolProperty | true | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:6861`) |
| `Actor` | `bDemoRecording` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:6870`) |
| `Actor` | `bDemoOwner` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:6879`) |
| `Actor` | `bForceDemoRelevant` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:6888`) |
| `Actor` | `bNetInitialRotation` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:6897`) |
| `Actor` | `bReplicateRigidBodyLocation` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:6906`) |
| `Actor` | `bKillDuringLevelTransition` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:6915`) |
| `Actor` | `bExchangedRoles` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:6924`) |
| `Actor` | `bConsiderAllStaticMeshComponentsForStreaming` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:6933`) |
| `Actor` | `bDebug` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:6942`) |
| `Actor` | `bPostRenderIfNotVisible` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:6951`) |
| `Actor` | `bAllowActorThoughts` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:6960`) |
| `Actor` | `bAllowTwoWayEncroach` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:6969`) |
| `Actor` | `bAllowDisableRigidBody` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:6978`) |
| `Actor` | `bEnableOptionalRBCollision` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:6987`) |
| `Actor` | `bForceSetAnimPositionInMatinee` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:6996`) |
| `Actor` | `bIsRoad` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:7005`) |
| `Actor` | `bIsTunnel` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:7014`) |
| `Actor` | `bIsTrainTracks` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:7023`) |
| `Actor` | `bIsVehicleJumpRamp` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:7032`) |
| `Actor` | `bNoBatmobileImpactSparks` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:7041`) |
| `Actor` | `bForceNetUpdate` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:7050`) |
| `Actor` | `bLightsUpdateLastRenderTime` | BoolProperty | true | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:7059`) |
| `Actor` | `bManualPerformPhysics` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:7068`) |
| `Actor` | `bHardAttach` | BoolProperty | true | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:7077`) |
| `Actor` | `bSnapAttach` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:7086`) |
| `Actor` | `bIgnoreBaseRotation` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:7095`) |
| `Actor` | `bBasedActorsNoMove` | BoolProperty | false | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:7104`) |
| `Actor` | `bSkipAttachedMoves` | BoolProperty | true | `Startup.upk` 536 @0x166 (class 0x104; `Actor.g.cs:7113`) |

### Inherited bool word `0x460` (decoded: bit splitting)

The tag carries the whole word `0x034803b0` = 55051184; the members it turns on are
`bUnequipToSocket`, `bCanUseXRay`, `bUsableFromVantagePoints`, `bUsableFromCornerCover`, `bUsableFromCrawlSpace`, `AutoTargetRequiresLOS`, `bUseRechargeDisplay`, `bGadgetCanBeMirrored`, `bRecharging`. The other members at this offset are false.

## 6. Object references, followed one level (decoded)

| field | target | target class | target export | target payload | one level further |
|---|---|---|---:|---:|---|
| `FireSound` | `Ww_CHR_RemoteGadget.Play_Remote_Gadget` | AkEvent | 46245 | 18 | decoded (2 tags) |
| `CancelSound` | `Ww_CHR_RemoteGadget.Play_Remote_Gadget` | AkEvent | 46245 | 18 | decoded (2 tags) |
| `CancelSound2` | `Engine.Play_Remote_Gadget_Off` | AkEvent | - | - | UNKNOWN (import: the object is not in this package) |
| `CallSound` | `Engine.Play_Gauntlet_Batmobile_Call` | AkEvent | - | - | UNKNOWN (import: the object is not in this package) |
| `RemoteControlBatmobileMove` | `Batmobile_Remote.RemoteControlBatmobile` | RSpecialMoveConfigConfigurable | 169080 | 10 | decoded (1 tags) |
| `Mesh` | `Default__RBatmobileRemoteBm.GadgetMesh` | SkeletalMeshComponent | 166735 | 58 | UNKNOWN (payload has no property tags: 58 B, stop=end) |

The component targets are the class-default components themselves (`GadgetMesh`): their own
payloads carry **no property tags**, so the mesh asset, materials and transform behind them
are UNKNOWN here. The `AkEvent` and `RSpecialMoveConfigConfigurable` targets are imports or
exports of other packages and are reported by path, not opened.

## 7. Startup vs StartupPatch (derived: the same decode on both)

**95** decoded rows compared per package. Scalar, name, string, vector and enum
values: **0** differences. Object references: **2** rows
differ, every one of them in the package-qualified path of the target rather than its class:

| field | class off | `Startup.upk` target | `StartupPatch.upk` target | target class |
|---|---|---|---|---|
| `CancelSound2` | 0x940 | `Engine.Play_Remote_Gadget_Off` (AkEvent) | `Ww_CHR_RemoteGadget.Play_Remote_Gadget_Off` (AkEvent) | `AkEvent` |
| `CallSound` | 0x948 | `Engine.Play_Gauntlet_Batmobile_Call` (AkEvent) | `Ww_CHR_BatmanGauntlet.Play_Gauntlet_Batmobile_Call` (AkEvent) | `AkEvent` |

Both indices resolve through their own package's tables, so this is a real byte difference
between the two CDOs: the same sound member points at the same *kind* of object, under a
differently named outer package (`Engine` in one, `Ww_CHR_RemoteGadget` in the other). Which
of the two an installed build uses depends on package load order, which is UNKNOWN here.

## 8. Oracles (`--check` re-runs each)

| oracle | ok | detail |
|---|---|---|
| `cdo_identity` | True | `{"Startup.upk": {"export": 536, "payload": 364, "sha1": "2b569423633ab837", "stop": "eof", "tags": 33}, "StartupPatch.upk": {"export": 520, "payload": 364, "sha1": "0a5b9b2a2948b862", "stop": "eof", "tags": 33}}` |
| `class_size_matches_bindings` | True | `{"max_tag_offset": 2452, "size": 2456}` |
| `doc_list_matches_export_table` | True | `{"doc": 48, "doc_only": [], "export_only": [], "exports": 48}` |
| `eleven_floats_named_in_order` | True | `{"0x968": "JammingRange", "0x970": "JammerTime", "0x974": "CurrentJam", "0x978": "CursorSpeed", "0x97c": "CursorAccel", "0x980": "CursorDecel", "0x984": "CursorReturnFactor", "0x988": "CursorReturnDelay", "0x98c": "MaxAimX", "0x990": "MaxAi` |
| `every_tag_named` | True | `{"distinct_tags": 33, "rows_after_bool_split": 95, "unnamed": []}` |
| `member_census_48` | True | `{"BoolProperty": 2, "FloatProperty": 11, "Function": 22, "ObjectProperty": 10, "State": 3}` |
| `object_refs_resolve` | True | `{"CallSound": "Engine.Play_Gauntlet_Batmobile_Call", "CancelSound": "Ww_CHR_RemoteGadget.Play_Remote_Gadget", "CancelSound2": "Engine.Play_Remote_Gadget_Off", "FireSound": "Ww_CHR_RemoteGadget.Play_Remote_Gadget", "Mesh": "Default__RBatmobi` |
| `packages_agree` | True | `{"compared": 95, "object_path_diffs": [["CancelSound2", "`Engine.Play_Remote_Gadget_Off` (AkEvent)", "`Ww_CHR_RemoteGadget.Play_Remote_Gadget_Off` (AkEvent)"], ["CallSound", "`Engine.Play_Gauntlet_Batmobile_Call` (AkEvent)", "`Ww_CHR_Batman` |
| `value_slots_23` | True | `{"tagged": 16, "untagged": ["bRelativeAiming", "ScreenOn", "ReachedRemoteHardLimitThought", "CurrentRiotSuppressorTarget", "NpcBatmobileTarget", "CallingVehicle", "RiotSuppressorBatmobile"], "value_members": 23}` |

## 9. Result

- the class has **48** members: BoolProperty 2, FloatProperty 11, Function 22, ObjectProperty 10, State 3 [decoded]
- value parameters: **23**; decoded values: **16**; UNKNOWN (no tag): **7**
- `GadgetType` = `GA_Gadget_JammerGadget`, `HudGadgetId` = `FGID_BatarangMulti2` [decoded: inherited tags 0x311/0x314]
- every value above carries its package, export, payload offset and class offset, so it can be re-read directly [decoded]
- function/state bodies: **UNKNOWN** (stripped)
- JC3 mapping: **not decided here** (out of scope by the brief)

## 10. UNKNOWN

1. **The 7 value slots with no tag** (§3). Tried: both CDOs, every start offset 0 (the walk
   closes at 362 with 0 unexplained bytes, so no tag is being skipped); checked the other
   package; checked the class's other exports for an archetype (none). Would be settled only
   by the cooker's omission rule, which the packages do not state.
2. **Values inside the followed component targets** (§6). Tried: walked each target's payload;
   untagged, so nothing is readable.
3. **Behaviour of the 25 function/state members.** Their 30-byte payloads are untagged; no
   bytecode and no constants survive.
