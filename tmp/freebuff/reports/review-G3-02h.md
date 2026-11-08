# review-G3-02h — keyboard bindings that reach the Batmobile

VERDICT: **needs rework.** Inside the four-file `BasedOn` input chain the parse is sound and
`C → ToggleDrivingCamera` (DefaultInput.ini:186) is indeed the only vehicle-specific key — I
re-derived that. But the card's headline ("the only vehicle-specific keyboard binding is C") and
its whole §2 answer table are false for the game, because the driving keybinds are not in that
chain at all: they are the `DefaultPursuitKeyMap` / `DefaultBattleKeyMap` arrays under
`[BmGame.RGameInfo]` in `BmGame/Config/BmGame.ini` (mirrored in `BmGame/Config/PC/PCGame.ini`),
which bind **F → ToggleDrivingCamera**, W → `aThrottleAxis`, S → `bBrakeButton`,
LeftMouseButton → `bVehicleBoostButton`, SpaceBar → `EjectFromVehicle`,
MiddleMouseButton → `bFireVehicleWeapon`, RightMouseButton → `ToggleBattleMode`,
R → `bLookBehindVehicle`, and 1/2/3/X → `SelectVehicleWeapon`. That is exactly the
"bindings array on a Bm* class" case. The card's §2 rows for brake, boost, fire, battle mode,
eject and accelerate are each contradicted by a line in that file.

## 1. What holds (re-read, not assumed)

`uv run python Tools/scripts/grab_keyboard_bindings.py --check` → `OK 7/7 oracles, 367 live
bindings, 21 keyboard/mouse vehicle rows (1 specific), 14 gamepad rows, md+json byte-identical`.
Spot-read from the bytes under `E:/Games/Batman - Arkham Knight`:

- DefaultInput.ini:186 `.Bindings=(Name="C",Command="ToggleDrivingCamera | DebugLevelLoad
  Combat",Control=false)` — exact.
- The other three vehicle Names in DefaultInput.ini are **alias definitions**, not keys, and the
  card says so: 177 `Name="BrakeButton"`, 178 `Name="ExitVehicle"`, 184
  `Name="BatmobileSonar"`. None of them has a physical key, so they cannot be a missed keyboard
  binding inside the chain.
- W/S/A/D and the arrows arrive through `Axis aBaseY` / `Axis aStrafe` / `Axis aBaseX`; the
  merge-conflict table (§5) reproduces: the same key is bound in BaseInput.ini and
  DefaultInput.ini in `[Engine.PlayerInput]` with different commands.
- PCInput.ini has no vehicle token (I catted all 30 lines: TAB/map, EditorViewport, debug camera,
  six SIXAXIS axes, LeftMouseButton→SkipCutscene). So the chain-level "only C" claim survives
  exactly as written.

## 2. The miss: `[BmGame.RGameInfo]` key-map arrays

`BmGame/Config/BmGame.ini` is not in the `BasedOn` chain (CONTROLS.md itself lists it as "453
(NOT in PC chain)"), but it is a live PC config and its arrays are the driving-mode keybinds. Each
line is `DefaultPursuitKeyMap=(Ability="$GFxUI.KeyboardControls.X",PrimaryKeyName="$PC.Keys.K",
SecondaryKeyName=...,Command="...",Icon="CI_Batmobile...")`. Keyboard-bound vehicle tokens:

| key | file:line | ability | vehicle token(s) |
|---|---|---|---|
| `F` | `BmGame.ini:4011` (PCGame.ini:140) | CycleView | **`ToggleDrivingCamera`** |
| `W` | `BmGame.ini:4004` (PCGame.ini:133) | Accelerate | `Axis aThrottleAxis` |
| `S` | `BmGame.ini:4005` (PCGame.ini:134) | ReverseBreak | `Button bBrakeButton` |
| `LeftMouseButton` | `BmGame.ini:4008` (PCGame.ini:137) | Afterburner | `Button bVehicleBoostButton` |
| `SpaceBar` | `BmGame.ini:4009` (PCGame.ini:138) | EjectToGlide | `EjectFromVehicle`, `SelectVehicleWeapon 0`, `OnRelease ReleaseVehicleWeapon 0` |
| `LeftShift` | `BmGame.ini:4010` (PCGame.ini:139) | Powerslide | `Button bHandBrakeButton` |
| `RightMouseButton` | `BmGame.ini:4012` (PCGame.ini:141) | BattleMode | **`ToggleBattleMode`** |
| `R` | `BmGame.ini:4014` (PCGame.ini:143) | ReverseCamera | `Button bLookBehindVehicle` |
| `LeftMouseButton` | `BmGame.ini:4021` (PCGame.ini:152) | RotaryCannon | `Button bFireVehicleSecondaryWeapon`, `SecondaryFireVehicleWeapon` |
| `MiddleMouseButton` | `BmGame.ini:4022` (PCGame.ini:153) | HeavyCannonFire | `Button bFireVehicleWeapon` |
| `One` | `BmGame.ini:4023` (PCGame.ini:154) | MissileBarrage | `SelectVehicleWeapon 2`, `ReleaseVehicleWeapon 2` |
| `Two` | `BmGame.ini:4024` (PCGame.ini:155) | DroneHacker | `SelectVehicleWeapon 3`, `ReleaseVehicleWeapon 3` |
| `Three` | `BmGame.ini:4025` (PCGame.ini:156) | EMPBlast | `SelectVehicleWeapon 1`, `ReleaseVehicleWeapon 1` |
| `F` | `BmGame.ini:4026` (PCGame.ini:157) | Sonar | `BatmobileSonar` |
| `X` | `BmGame.ini:4027` (PCGame.ini:158) | ForensicScanner | `SelectVehicleWeapon 4`, `ReleaseVehicleWeapon 4` |
| `W` | `BmGame.ini:4015` (PCGame.ini:146, Battle) | Forward | `Axis aThrottleAxis` |

The rows at 3888–3976 are the **per-character** maps (`DefaultBatgirlKeyMap`,
`DefaultRedHoodKeyMap`, `DefaultHarleyKeyMap`, `DefaultBatmanKeyMap`) and also carry vehicle
tokens on keys (SpaceBar → `EjectFromVehicle`, LeftControl → `bFireVehicleWeapon`,
LeftMouseButton → `BrakeButton`, F → `BatmobileSonar`). They are on-foot character maps, so I
count them as ambiguous rather than as the primary miss; the two `Default*KeyMap` driving arrays
above are not ambiguous — their icons are `CI_BatmobileThrottle/Brake/Boost/Eject/Sonar/...`.

**`F → ToggleDrivingCamera` alone refutes the headline**, before any of the other tokens: it is a
second physical key for the exact same vehicle-specific command, at a line the card never looked
at. The claim "only C" is only true if it is restated as "only C *in the four-file input chain*".

## 3. Each §2 answer row, re-checked

| card says | bytes say |
|---|---|
| accelerate: "none specific; W/S via `Axis aBaseY`" | `W → Axis aThrottleAxis` (BmGame.ini:4004, 4015) — a vehicle-specific axis on a keyboard key |
| brake: "none; gamepad X only" | `S → Button bBrakeButton` (4005), `LeftShift → bHandBrakeButton` (4010) |
| steer: `A`/`D`, arrows via generic axes | holds in the chain; BmGame.ini's A/D rows add `aRawLHJoyRight` only, no new vehicle-specific steer token |
| battle mode: "none" | `RightMouseButton → ToggleBattleMode` (4012) |
| boost: "none" | `LeftMouseButton → bVehicleBoostButton` (4008) |
| fire: "none" | `LeftMouseButton → bFireVehicleSecondaryWeapon` (4021), `MiddleMouseButton → bFireVehicleWeapon` (4022) |
| exit: "none; `ExitVehicle` bound to nothing" | true for the alias; but `E` is the `ExitBatmobile` ability (4013) whose Command does **not** carry `ExitVehicle` — a derived near-miss worth stating, not a binding |
| eject: "none" | `SpaceBar → EjectFromVehicle` (4009, 4019) |
| driving camera: "`C`" | `C` (chain) **and `F`** (4011) |

## 4. Two further defects

1. **Stale sentence.** The header says "`BINDINGS_MERGED.json` does not exist, so this is the raw
   chain." It exists: `Research/BatmobileGrab/BINDINGS_MERGED.json` (87,270 B) and `.md` (9,111 B),
   both dated Nov 3 08:15 (G3-02g). Neither mentions `DefaultPursuitKeyMap` or
   `DefaultBattleKeyMap` (grep count 0/0), so the merged card shares the same blind spot — the
   sentence is wrong and the gap is not confined to G3-02h.
2. **The oracle cannot fail on the miss.** `P3-keyboard-specific` compares the found set to the
   hard-coded `[("C", "DefaultInput.ini", 186, "ToggleDrivingCamera")]`, and `TARGETS` omits
   `ToggleBattleMode`, `BatmobileSonar`, `bLookBehindVehicle`, `bHandBrakeButton` and
   `bBrakeButton`. A keyboard binding to any of those would not even be classified as a vehicle
   token. P3 is therefore a restatement of the scan's inputs, not an independent check of the
   claim's scope.

## 5. Is `BmGame.ini` "the same ini chain"?

No — it has no `BasedOn` link to PCInput/UserInput/DefaultInput/BaseInput, and CONTROLS.md marks it
"NOT in PC chain". So the card's chain-scoped statements are accurate. But the card's title, §2
("Answer") and the backlog line claim something about keyboard bindings that reach the Batmobile,
and those arrays are precisely that: G3-02b decoded `RGameInfo.SetPursuitModeKeyBinds` /
`SetPCBinds` call sites, and the card's own UNKNOWN 4 says "Where it would be found: the keybinds
those calls install at runtime." They are in the file the card already had. Two acceptable fixes:
include `[BmGame.RGameInfo]` in the scan, or retitle and re-scope every claim to "the input chain"
and hand the arrays to the controls card.

## 6. Commands run (verbatim)

```
cd /e/Modding/JC3-Batmobile && uv run python Tools/scripts/grab_keyboard_bindings.py --check
OK 7/7 oracles, 367 live bindings, 21 keyboard/mouse vehicle rows (1 specific), 14 gamepad rows, md+json byte-identical
CHECK_EXIT=0
```

```
cd /e/Modding/JC3-Batmobile && sed -n '4000,4030p' "E:/Games/Batman - Arkham Knight/BmGame/Config/BmGame.ini"
DefaultBatmanKeyMap=(Ability="$GFxUI.KeyboardControls.QuickfireExplosiveGel",PrimaryKeyName="$PC.Keys.UNASSIGNED",...)
... (three Quickfire lines, all UNASSIGNED) ...
DefaultPursuitKeyMap=(Ability="$GFxUI.KeyboardControls.Accelerate",PrimaryKeyName="$PC.Keys.W",SecondaryKeyName="$PC.Keys.Up",Command="DebugMenuUpPressed | OnRelease DebugMenuUpReleased | Axis aThrottleAxis Speed=1.0 DeadZone=0.0 | Axis aRightTrigger Speed=1.0 DeadZone=0.2 | Axis aUp Speed=1.0 DeadZone=0.1", Icon="CI_BatmobileThrottle")
DefaultPursuitKeyMap=(Ability="$GFxUI.KeyboardControls.ReverseBreak",PrimaryKeyName="$PC.Keys.S",SecondaryKeyName="$PC.Keys.Down",Command="DebugMenuDownPressed | OnRelease DebugMenuDownReleased | MoveBackward | Axis aRawLHJoyUp Speed=-1.0 | Button bBrakeButton", Icon="CI_BatmobileBrake")
DefaultPursuitKeyMap=(Ability="$GFxUI.KeyboardControls.Left",PrimaryKeyName="$PC.Keys.A",SecondaryKeyName="$PC.Keys.Left",Command="StrafeLeft | DebugMenuLeftPressed | OnRelease DebugMenuLeftReleased | Axis aRawLHJoyRight Speed=-1.0", Icon="")
DefaultPursuitKeyMap=(Ability="$GFxUI.KeyboardControls.Right",PrimaryKeyName="$PC.Keys.D",SecondaryKeyName="$PC.Keys.Right",Command="StrafeRight | DebugMenuRightPressed | OnRelease DebugMenuRightReleased | Axis aRawLHJoyRight Speed=1.0", Icon="")
DefaultPursuitKeyMap=(Ability="$GFxUI.KeyboardControls.Afterburner",PrimaryKeyName="$PC.Keys.LeftMouseButton",SecondaryKeyName="$PC.Keys.UNASSIGNED",Command="Button bVehicleBoostButton | SkipCutscene", Icon="CI_BatmobileBoost")
DefaultPursuitKeyMap=(Ability="$GFxUI.KeyboardControls.EjectToGlide",PrimaryKeyName="$PC.Keys.SpaceBar",SecondaryKeyName="$PC.Keys.UNASSIGNED",Command="DebugCamSingleFrameStep | EjectFromVehicle | BattleStrafe  | ContextSensitive | Run | CapeGlide | AcceptConversation | SelectVehicleWeapon 0 | OnRelease ReleaseVehicleWeapon 0 | Evade | DebugMenuSelectA | CancelBatarangCamera | TriggerPhysImpact", Icon="CI_BatmobileEject,CI_ContinuePromptBatmobile")
DefaultPursuitKeyMap=(Ability="$GFxUI.KeyboardControls.Powerslide",PrimaryKeyName="$PC.Keys.LeftShift",SecondaryKeyName="$PC.Keys.UNASSIGNED",Command="Button bHandBrakeButton", Icon="")
DefaultPursuitKeyMap=(Ability="$GFxUI.KeyboardControls.CycleView",PrimaryKeyName="$PC.Keys.F",SecondaryKeyName="$PC.Keys.UNASSIGNED",Command="ToggleDrivingCamera", Icon="CI_ToggleBatmobileCamera")
DefaultPursuitKeyMap=(Ability="$GFxUI.KeyboardControls.BattleMode",PrimaryKeyName="$PC.Keys.RightMouseButton",SecondaryKeyName="$PC.Keys.UNASSIGNED",Command="HoldToZoom | ToggleBattleMode", Icon="")
DefaultPursuitKeyMap=(Ability="$GFxUI.KeyboardControls.ExitBatmobile",PrimaryKeyName="$PC.Keys.E",SecondaryKeyName="$PC.Keys.UNASSIGNED",Command="DebugMenuStepUp | DebugMenuNextPage | DualPlay | ThermalMode | Button aLeftShoulder | SlowDownSpectatorCamera", Icon="CI_ExitRemoteBatmobile")
DefaultPursuitKeyMap=(Ability="$GFxUI.KeyboardControls.ReverseCamera",PrimaryKeyName="$PC.Keys.R",SecondaryKeyName="$PC.Keys.UNASSIGNED",Command="Button bLookBehindVehicle", Icon="CI_LookBehind")
DefaultBattleKeyMap=(Ability="$GFxUI.KeyboardControls.Forward",PrimaryKeyName="$PC.Keys.W",SecondaryKeyName="$PC.Keys.Up",Command="DebugMenuUpPressed | OnRelease DebugMenuUpReleased | MoveForward  | Axis aRawLHJoyUp Speed=1.0 | Axis aRightTrigger Speed=1.0 DeadZone=0.2 | Axis aUp Speed=1.0 DeadZone=0.1 | Axis aThrottleAxis Speed=1.0 DeadZone=0.0", Icon="")
DefaultBattleKeyMap=(Ability="$GFxUI.KeyboardControls.Back",PrimaryKeyName="$PC.Keys.S",SecondaryKeyName="$PC.Keys.Down",Command="DebugMenuDownPressed | OnRelease DebugMenuDownReleased | MoveBackward | Axis aRawLHJoyUp Speed=-1.0", Icon="")
DefaultBattleKeyMap=(Ability="$GFxUI.KeyboardControls.StrafeLeft",PrimaryKeyName="$PC.Keys.A",...)
DefaultBattleKeyMap=(Ability="$GFxUI.KeyboardControls.StrafeRight",PrimaryKeyName="$PC.Keys.D",...)
DefaultBattleKeyMap=(Ability="$GFxUI.KeyboardControls.EjectToGlideThrusters",PrimaryKeyName="$PC.Keys.SpaceBar",SecondaryKeyName="$PC.Keys.UNASSIGNED",Command="DebugCamSingleFrameStep | EjectFromVehicle | BattleStrafe  | ... | SelectVehicleWeapon 0 | OnRelease ReleaseVehicleWeapon 0 | ...", Icon="CI_BatmobileInteract")
DefaultBattleKeyMap=(Ability="$GFxUI.KeyboardControls.Zoom",PrimaryKeyName="$PC.Keys.Z",...)
DefaultBattleKeyMap=(Ability="$GFxUI.KeyboardControls.RotaryCannon",PrimaryKeyName="$PC.Keys.LeftMouseButton",SecondaryKeyName="$PC.Keys.UNASSIGNED",Command="Button bFireVehicleSecondaryWeapon | SecondaryFireVehicleWeapon | SkipCutscene", Icon="CI_BatmobileSecondaryFire")
DefaultBattleKeyMap=(Ability="$GFxUI.KeyboardControls.HeavyCannonFire",PrimaryKeyName="$PC.Keys.MiddleMouseButton",SecondaryKeyName="$PC.Keys.Q",Command="Button bFireVehicleWeapon | FireGun DebugMenuQualifyOnT | OnRelease DebugMenuQualifyOffT | DebugMenuPrevPage", Icon="CI_BatmobileFire")
DefaultBattleKeyMap=(Ability="$GFxUI.KeyboardControls.MissileBarrage",PrimaryKeyName="$PC.Keys.One",SecondaryKeyName="$PC.Keys.UNASSIGNED",Command="SelectVehicleWeapon 2  | OnRelease ReleaseVehicleWeapon 2 | DebugMenuNumber 1", Icon="CI_BatmobileMissileBarrage")
DefaultBattleKeyMap=(Ability="$GFxUI.KeyboardControls.DroneHacker",PrimaryKeyName="$PC.Keys.Two",SecondaryKeyName="$PC.Keys.UNASSIGNED",Command="SelectVehicleWeapon 3 | OnRelease ReleaseVehicleWeapon 3 | DebugMenuNumber 2", Icon="")
DefaultBattleKeyMap=(Ability="$GFxUI.KeyboardControls.EMPBlast",PrimaryKeyName="$PC.Keys.Three",SecondaryKeyName="$PC.Keys.LeftControl",Command="... SelectVehicleWeapon 1 | OnRelease ReleaseVehicleWeapon 1 | ...", Icon="... CI_BatmobileEMPLv1 ...")
DefaultBattleKeyMap=(Ability="$GFxUI.KeyboardControls.Sonar",PrimaryKeyName="$PC.Keys.F",SecondaryKeyName="$PC.Keys.UNASSIGNED",Command="BatmobileSonar", Icon="CI_BatmobileSonarBlast,CI_BatmobileSonar")
DefaultBattleKeyMap=(Ability="$GFxUI.KeyboardControls.ForensicScanner",PrimaryKeyName="$PC.Keys.X",SecondaryKeyName="$PC.Keys.UNASSIGNED",Command="TelemetryTogglePause | ForensicMode | SelectVehicleWeapon 4 | OnRelease ReleaseVehicleWeapon 4", Icon="CI_VisionModes")
```

```
cd /e/Modding/JC3-Batmobile && sed -n '130,160p' "E:/Games/Batman - Arkham Knight/BmGame/Config/PC/PCGame.ini"
[Engine.PlayerInput] ... [BmGame.RGameInfo]
.DefaultPursuitKeyMap=(... "Accelerate",PrimaryKeyName="$PC.Keys.W" ... Axis aThrottleAxis ...)
... the same 11 Pursuit + 13 Battle entries, with a leading dot:
.DefaultPursuitKeyMap=(... "CycleView",PrimaryKeyName="$PC.Keys.F" ... Command="ToggleDrivingCamera" ...)
.DefaultBattleKeyMap=(... "HeavyCannonFire",PrimaryKeyName="$PC.Keys.MiddleMouseButton" ...)
```

```
cd /e/Modding/JC3-Batmobile && PYTHONIOENCODING=utf-8 uv run python tmp/freebuff/scratch/g02h_review.py

=== BmGame/Config/PC/PCInput.ini (30 lines) ===

=== BmGame/Config/UserInput.ini (3 lines) ===

=== BmGame/Config/DefaultInput.ini (325 lines) ===
  BrakeButton      BmGame/Config/DefaultInput.ini:177  BrakePressed, bHandbrakeOrBrake
  ExitVehicle      BmGame/Config/DefaultInput.ini:178  ExitVehiclePressed, ExitVehicleReleased
  BatmobileSonar   BmGame/Config/DefaultInput.ini:184  BatmobileSonarPressed, BatmobileSonarReleased
  C                BmGame/Config/DefaultInput.ini:186  ToggleDrivingCamera
  K                BmGame/Config/DefaultInput.ini:207  KillVehicles
  B                BmGame/Config/DefaultInput.ini:242  SpawnPlayerCar

=== Engine/Config/BaseInput.ini (334 lines) ===

=== BmGame/Config/BmGame.ini (7147 lines) ===
  $PC.Keys.SpaceBar BmGame/Config/BmGame.ini:3888  EjectFromVehicle, BattleStrafe, SelectVehicleWeapon, ReleaseVehicleWeapon
  $PC.Keys.LeftControl BmGame/Config/BmGame.ini:3889  bFireVehicleWeapon
  $PC.Keys.RightMouseButton BmGame/Config/BmGame.ini:3892  SelectVehicleWeapon, ReleaseVehicleWeapon, bVehicleBoostButton
  $PC.Keys.LeftMouseButton BmGame/Config/BmGame.ini:3893  BrakeButton
  $PC.Keys.MiddleMouseButton BmGame/Config/BmGame.ini:3894  SelectVehicleWeapon, ReleaseVehicleWeapon, HoldForLineLaunchStop
  $PC.Keys.F       BmGame/Config/BmGame.ini:3895  BatmobileSonar, PursuitModeTagGun
  $PC.Keys.X       BmGame/Config/BmGame.ini:3896  SelectVehicleWeapon, ReleaseVehicleWeapon
  ... (the same seven rows repeat for RedHood 3917-3925, Harley 3942-3950, Batman 3967-3976) ...
  $PC.Keys.W       BmGame/Config/BmGame.ini:4004  aThrottleAxis
  $PC.Keys.S       BmGame/Config/BmGame.ini:4005  bBrakeButton
  $PC.Keys.LeftMouseButton BmGame/Config/BmGame.ini:4008  bVehicleBoostButton
  $PC.Keys.SpaceBar BmGame/Config/BmGame.ini:4009  EjectFromVehicle, BattleStrafe, SelectVehicleWeapon, ReleaseVehicleWeapon
  $PC.Keys.LeftShift BmGame/Config/BmGame.ini:4010  bHandBrakeButton
  $PC.Keys.F       BmGame/Config/BmGame.ini:4011  ToggleDrivingCamera
  $PC.Keys.RightMouseButton BmGame/Config/BmGame.ini:4012  ToggleBattleMode
  $PC.Keys.R       BmGame/Config/BmGame.ini:4014  bLookBehindVehicle
  $PC.Keys.W       BmGame/Config/BmGame.ini:4015  aThrottleAxis
  $PC.Keys.SpaceBar BmGame/Config/BmGame.ini:4019  EjectFromVehicle, BattleStrafe, SelectVehicleWeapon, ReleaseVehicleWeapon
  $PC.Keys.LeftMouseButton BmGame/Config/BmGame.ini:4021  bFireVehicleSecondaryWeapon, SecondaryFireVehicleWeapon
  $PC.Keys.MiddleMouseButton BmGame/Config/BmGame.ini:4022  bFireVehicleWeapon
  $PC.Keys.One     BmGame/Config/BmGame.ini:4023  SelectVehicleWeapon, ReleaseVehicleWeapon
  $PC.Keys.Two     BmGame/Config/BmGame.ini:4024  SelectVehicleWeapon, ReleaseVehicleWeapon
  $PC.Keys.Three   BmGame/Config/BmGame.ini:4025  SelectVehicleWeapon, ReleaseVehicleWeapon, HoldForLineLaunchStop
  $PC.Keys.F       BmGame/Config/BmGame.ini:4026  BatmobileSonar
  $PC.Keys.X       BmGame/Config/BmGame.ini:4027  SelectVehicleWeapon, ReleaseVehicleWeapon

=== BmGame/Config/PC/PCGame.ini (416 lines) ===
  $PC.Keys.W ...:133, LeftMouseButton ...:137, SpaceBar ...:138, LeftShift ...:139,
  F ...:140 ToggleDrivingCamera, RightMouseButton ...:141 ToggleBattleMode, R ...:143 bLookBehindVehicle,
  SpaceBar ...:150, LeftMouseButton ...:152, MiddleMouseButton ...:153, One/Two/Three ...:154-156,
  F ...:157 BatmobileSonar, X ...:158
EXIT=0
```

```
cd /e/Modding/JC3-Batmobile && ls -l Research/BatmobileGrab/BINDINGS_MERGED.*
-rw-r--r-- 1 User 197121 87270 Nov  3 08:15 Research/BatmobileGrab/BINDINGS_MERGED.json
-rw-r--r-- 1 User 197121  9111 Nov  3 08:15 Research/BatmobileGrab/BINDINGS_MERGED.md
=== merged mentions of KeyMap ===
Research/BatmobileGrab/BINDINGS_MERGED.md:0
Research/BatmobileGrab/BINDINGS_MERGED.json:0
```

```
cd /e/Modding/JC3-Batmobile && grep -n "ToggleBattleMode\|BatmobileSonar\|bLookBehindVehicle\|bHandBrakeButton\|BatmobileFireButton\|ExitVehicle" <each chain file>
--- BmGame/Config/PC/PCInput.ini        (no match)
--- BmGame/Config/DefaultInput.ini      178 ExitVehicle (alias) / 184 BatmobileSonar (alias) / 252 XboxTypeS_RightTrigger / 255,256 gamepad
--- Engine/Config/BaseInput.ini         (no match)
```

Scratch probe (read-only): `tmp/freebuff/scratch/g02h_review.py`. No project file was edited; the
game install was only read.

## 7. What I could not check

- **Which key map wins at runtime.** `DefaultPursuitKeyMap` (Pursuit), `DefaultBattleKeyMap`
  (Battle), the per-character maps and `[Engine.PlayerInput]` all bind the same keys; no text file
  states the active map per mode, and `BmGame.ini` vs `PCGame.ini` precedence is not documented in
  either card. Whether `F` beats `C`, or `C` is only the out-of-vehicle fallback, stays UNKNOWN.
- **Whether `SetPursuitModeKeyBinds` actually consumes these arrays.** G3-02b decoded the call
  sites (BattleMode.EndState, RGameInfo.SetPCBinds, DrivingMode.BeginState) by name; the
  name→array binding is still name-match only.
- **The per-character maps' in-vehicle relevance.** SpaceBar/LeftControl/MiddleMouseButton rows in
  the Batgirl/RedHood/Harley/Batman maps carry vehicle tokens, but those maps are for on-foot
  characters; I did not establish whether they apply while driving.
- **`E` → `ExitBatmobile`.** The ability is named for the exit function, but its Command has no
  `ExitVehicle` token; whether exit is triggered by the ability wrapper elsewhere is not decoded.
