# 7207 - G3-02f: the 7 SAMPLER_RESULTS UNKNOWNs, closed from files (no more in-game testing)

STATUS: **done**. 4 of 7 UNKNOWNs are fully answered from files, 3 are partly answered with the
missing input named, none was left untried. `Tools/scripts/bmak_sampler_unknowns.py --check` exits 0
with 12/12 oracles and a byte-identical rebuild of `Research/BatmobileGrab/SAMPLER_UNKNOWNS.md`.

The headline answers:

* **The flag-word bits are all named** (U1). Every bit the sampler saw toggling is a masked
  `BoolProperty` of `RVehicleBatmobileBase` at +4568, with its getter line - e.g. `0x2 ArmouredMode`,
  `0x8 bTransforming`, `0x10 bWeaponsReady`, `0x80 WallScrapeL`, `0x100 WallScrapeR`,
  `0x400 AudioPlayingIn`, `0x100000 AudioClutch`, and the already-known `0x80000 bCockpitOpen`.
* **Byte 783 is X, and that is decoded, not timing** (U3/U6): `DefaultInput.ini:269` binds `XboxTypeS_X`
  to a list containing the token `BrakeButton`; the named binding `BrakeButton` is
  `BrakePressed | Button bHandbrakeOrBrake`, so an X press writes `RPlayerInput.bHandbrakeOrBrake` +783
  *before* any gameplay gate. 771 = `bRunButton` (A's `Run` token) and 772 = `bCrouchButton` (RT's
  `StealthOrGadget` token).
* **RT sets 778 and 772 and cannot set 780** (U4): the RT line carries `Button bFireVehicleWeapon` and
  the named binding `StealthOrGadget` (whose body writes the crouch byte); `bThrottleButton` +780 is
  not in the resolved writer set, and the throttle axis is written only by the separate
  `XboxTypeS_RightTriggerAxis` line - so 0.0 on `aThrottleAxis` is the expected result, not an anomaly.
* **The controller was a method gap, not a data gap** (U5): `Game.FindObjects<T>()`
  (`Framework/Game.cs:127`) and `PlayerController.PlayerInput` (`+1240`) both exist; the six eject /
  quick-gadget fields are decoded with offset, width and line.
* **TArray strides are 8** for `CurrentTargets` / `LastTargets` / `FiredProjectiles` (U6): the element
  types are `Actor` / `RProjectile`, classes derived from `GameObject`, and
  `MarshalUtil.GetSizeUnmanaged<T>()` returns `sizeof(IntPtr)` for those.
* Still not answerable from files: why `BoostingOut` (+5901) pulsed on eject (U2 - the UFunction body
  that writes it is not in the tree) and what produced the ~0.1 s `774 bCancelButton` taps (U7 - only
  the B line can write that byte, and B was not pressed).

`bmak_runtime_sampler.py`, `bmak_runtime_sampler2.py`, `bmak_sampler_results.py`, `SAMPLER_RESULTS.md`,
`SAMPLER_FIELDS2.*` and `SAMPLER_UNKNOWNS_G3-02f.md` were **not** edited (the last is a byte-exact
copy of the file this card replaces, checked by sha256). Nothing was launched, attached to, or read
from a game; nothing was written under `E:/Games` or `D:/Games`.

## Files written

| file | size | what |
|---|---:|---|
| `Tools/scripts/bmak_sampler_unknowns.py` | 38,943 B | rebuilds the document from the BmSDK layouts, the bind tables and the two samples2 logs; `--write` / `--check` |
| `Research/BatmobileGrab/SAMPLER_UNKNOWNS.md` | 18,369 B, 294 lines | the 7 verdicts, the offsets/bytes behind each, the missing inputs |
| `Research/BatmobileGrab/SAMPLER_UNKNOWNS_G3-02f.md` | 17,416 B | verbatim preservation of the previous `SAMPLER_UNKNOWNS.md` (sha256 `970e948a...c929085`), so this card destroys no other card's output |
| `tmp/freebuff/reports/7207-g3-02f-sampler-unknowns.md` | this report | |

Read-only inputs: `E:/Modding/_shared/tools/BmSDK-AK/src/BmSDK/{Generated,Framework,Classes/Core}`,
`Research/BatmobileGrab/{CONTROLS.md,CONTROLS_CONSUMERS.json,BINDINGS_MERGED.json,SAMPLER_RESULTS.md}`,
`Research/BatmobileGrab/runtime/samples2-20261105T073917Z.jsonl`,
`.../samples2-20261105T075011Z.jsonl`.

## The seven UNKNOWNs and their verdicts

| # | UNKNOWN (`SAMPLER_RESULTS.md` §UNKNOWN / mapping table) | verdict | what the files give |
|---|---|---|---|
| 1 | meaning of flag bits `0x100000 0x100 0x80 0x400 0x10 0x8 0x2` | **ANSWERED** | `RVehicleBatmobileBase` +4568, one masked `BoolProperty` per bit, getter + comment line each |
| 2 | why `BoostingOut` (+5901) pulsed on eject | **UNKNOWN** | byte and offset decoded; no decoded writer exists |
| 3 | does X register on 783 with the meter empty | **PARTLY** | 783 is X by bind chain; the charge gate is inside `QuickGadgetX`'s body |
| 4 | RT pair 772+778, never 780; axes 0.0 | **ANSWERED** | RT command list + named bindings + the separate axis bind |
| 5 | `RPlayerController` never sampled | **ANSWERED** | `Game.FindObjects<T>()`, `PlayerInput` +1240, six fields with offsets |
| 6 | names of 783/771/772 and the TArray strides | **ANSWERED** | `bHandbrakeOrBrake`/`bRunButton`/`bCrouchButton`; stride 8 |
| 7 | what produces the 774 taps | **PARTLY** | 774 = `bCancelButton`, only the B line can write it; producer unknown |

The count is stated in the document itself, with an oracle for it: `SAMPLER_RESULTS.md` numbers six
items in its UNKNOWN section, and the 774 row of its mapping table is the seventh.

## Evidence, per answer (offset/bytes as the brief asks)

**U1 - flag bits, decoded.** Word at +4568, 31 masked bools. Observed set:

| bit | field | offset | getter | comment |
|---:|---|---:|---|---:|
| `0x2` | `ArmouredMode` | 4568 | `RVehicleBatmobileBase.g.cs:4468` | 4464 |
| `0x4` | `ArmouredModeOld` | 4568 | `:4477` | 4473 |
| `0x8` | `bTransforming` | 4568 | `:4486` | 4482 |
| `0x10` | `bWeaponsReady` | 4568 | `:4495` | 4491 |
| `0x80` | `WallScrapeL` | 4568 | `:4522` | 4518 |
| `0x100` | `WallScrapeR` | 4568 | `:4531` | 4527 |
| `0x400` | `AudioPlayingIn` | 4568 | `:4549` | 4545 |
| `0x80000` | `bCockpitOpen` | 4568 | `:4630` | 4626 |
| `0x100000` | `AudioClutch` | 4568 | `:4639` | 4635 |
| `0x400000` | `SelfDriveAllowBoost` | 4568 | `:4657` | 4653 |

Two transitions now read as *expected* rather than mysterious, derived from the same records that
carried them: the eject record `07:56:04.263Z 0x400000 -> 0x480000` gains exactly `bCockpitOpen`, and
the LT hold `07:51:40.489Z` gains `ArmouredMode`+`ArmouredModeOld`+`bWeaponsReady`+`AudioPlayingIn`
(the LT battle-mode link D-11 recorded live). `0x400000` was already set in the first record of both
logs, so it is a baseline, not a boost signal.

**U3 - X on 783, decoded chain** (`DefaultInput.ini:269`):
`XboxTypeS_X` -> `... | BrakeButton | ...`; named binding `BrakeButton` -> `BrakePressed | Button
bHandbrakeOrBrake`; `RPlayerInput.bHandbrakeOrBrake` at **+783** (`RPlayerInput.g.cs:962`).
`RPlayerController.QuickGadgetX` is a `Function` (`RPlayerController.g.cs:489`), i.e. a
`ProcessEvent` wrapper with no body in the tree - that is the missing piece for the "meter empty"
half. No record sampled `WeaponGeneratorPower` (0x1EE8) or `WeaponUnavailableReason` (0x170B), so the
charge at each 783 edge is not observable in these logs.

**U4 - RT, decoded.** RT line `DefaultInput.ini:252`:
`StealthOrGadget | DebugMenuQualifyOnT | OnRelease DebugMenuQualifyOffT | DebugMenuNextPage |
AttackThrow | BatmobileFireButton | Button bFireVehicleWeapon | FireGun | DeepScanIn`.
Resolved writers: `bFireVehicleWeapon` +778 (direct `Button` token) and `bCrouchButton` +772 (via the
named binding `StealthOrGadget`, body `...|ButtonbCrouchButton|...`). `bThrottleButton` +780 is absent
from that set. The throttle axis (+840) is written only by the `XboxTypeS_RightTriggerAxis` line
(`Axis aRightTrigger ... | Axis aUp ... | Axis aThrottleAxis ...`), which the digital trigger never
fires. The vehicle-side value is `CurrentThrottle` **+6408** (`RVehicleBatmobileBase.g.cs:7254`).

**U5 - controller, decoded route.** `Game.FindObjects<T>()` at `Framework/Game.cs:127`;
`PlayerController.PlayerInput` `ObjectProperty` at `Engine/PlayerController.g.cs:5458`, offset +1240.
Fields: `CurrentEjectType` +3502 (`:28120`), `LastEjectFromBatmobileTime` +7188 (`:31720`),
`UsedQuickGadget` +3452 `&0x80000` (`:26194`), `QuickGadgetOnRT` +3452 `&0x100000` (`:26203`),
`bGadgetButtonHeld` +3448 `&0x200` (`:25816`), `QuickGadgetTrigger` +5956 (`:30382`). Values in the
runs stay unobserved - that is a capture gap, not a decode gap.

**U6 - names and strides, decoded.** 783 `bHandbrakeOrBrake` (`:962`), 771 `bRunButton` (`:854`),
772 `bCrouchButton` (`:863`). `TArray<T>` = pointer +0, count +8, max +12 (`Classes/Core/TArray.cs`);
stride from `MarshalUtil.GetSizeUnmanaged<T>()` (`Framework/MarshalUtil.cs`): value type ->
`Marshal.SizeOf`, interface -> `FScriptInterface` (two `IntPtr`), `GameObject` subclass ->
`sizeof(IntPtr)`. `Actor : StateObject` (`Generated/Engine/Actor.g.cs`) and `StateObject : GameObject`
(`Generated/Core/StateObject.g.cs`) are classes, `CurrentTargets` +2400 / `LastTargets` +2416 are
`TArray<Actor>`, `FiredProjectiles` +2632 is `TArray<RProjectile>` - all stride **8**.

A naming correction fell out of the oracle: `in0.b788..b799` are not fields at all, they are bytes
inside the four raw axis floats (`RawLeftY` +788, `RawLeftX` +792, `RawRightY` +796,
`RawRightX` +800), so a moving `in0.b788` is a changed *byte of a float*, not a boolean field.

## Commands and output (verbatim)

Layout masks at +4568 and the marshalling size rule:

```
cd "E:/Modding/JustCause3/JC3-Batmobile" && uv run python - <<'EOF'
... parse RVehicleBatmobileBase.g.cs for Bool properties at 4568 ...
EOF
sed -n '250,300p' E:/Modding/_shared/tools/BmSDK-AK/src/BmSDK/Framework/MarshalUtil.cs
```

```
== bools at 4568 whose mask is one the sampler saw toggling
   0x000002  ArmouredMode                             mask=0x2        comment=4464 getter=4468
   0x000008  bTransforming                            mask=0x8        comment=4482 getter=4486
   0x000010  bWeaponsReady                            mask=0x10       comment=4491 getter=4495
   0x000080  WallScrapeL                              mask=0x80       comment=4518 getter=4522
   0x000100  WallScrapeR                              mask=0x100      comment=4527 getter=4531
   0x000400  AudioPlayingIn                           mask=0x400      comment=4545 getter=4549
   0x080000  bCockpitOpen                             mask=0x80000    comment=4626 getter=4630
   0x100000  AudioClutch                              mask=0x100000   comment=4635 getter=4639
== every bool at 4568 with a mask (count)
   masks 31 of 32
   [('0x1', 'RollingStart'), ('0x2', 'ArmouredMode'), ('0x4', 'ArmouredModeOld'), ('0x8', 'bTransforming'), ('0x10', 'bWeaponsReady'), ('0x20', 'KismetForceWheelspin'), ('0x40', 'StopBoxForceWheelspin'), ('0x80', 'WallScrapeL'), ('0x100', 'WallScrapeR'), ('0x200', 'EnemyTaunt_DebugVisualisation'), ('0x400', 'AudioPlayingIn'), ('0x800', 'bIsPrototypeBatmobile'), ('0x1000', 'bIsJokerfiedBatmobile'), ('0x2000', 'AbseilBlocked'), ('0x4000', 'bBoostLocked'), ('0x8000', 'bBattleModeLocked'), ('0x10000', 'bLockInBattleMode'), ('0x20000', 'ForceHeadlightsSwitchedOn'), ('0x40000', 'bFailedWeaponFlag'), ('0x80000', 'bCockpitOpen'), ('0x100000', 'AudioClutch'), ('0x200000', 'SatNavChallengeActive'), ('0x400000', 'SelfDriveAllowBoost'), ('0x800000', 'SelfDriveUturn'), ('0x1000000', 'bRemoteDrive'), ('0x2000000', 'bFakeRemoteDrive'), ('0x4000000', 'bRemoteScoopUp'), ('0x8000000', 'bWasRemoteDriving'), ('0x10000000', 'bRemoteDriveBatmanTrackerDisabled'), ('0x20000000', 'InfiniteBoost'), ('0x40000000', 'DisabledByEMP')]
=== MarshalUtil ===
    internal static int GetSizeUnmanaged<TManaged>()
    {
        // Try to use managed size directly (for struct, primitive types)
        if (typeof(TManaged).IsValueType)
        {
            return Marshal.SizeOf<TManaged>();
        }
        // Return UE3 internal interface wrapper size
        else if (typeof(TManaged).IsInterface)
        {
            return sizeof(FScriptInterface);
        }
        // Return size of UObject pointer
        else if (typeof(TManaged).IsAssignableTo(typeof(GameObject)))
        {
            return sizeof(IntPtr);
        }
```

Byte names 760-800 and the RT bind line:

```
cd "E:/Modding/JustCause3/JC3-Batmobile" && uv run python - <<'EOF'
... print RPlayerInput properties with 760<=offset<=800, then every RightTrigger bind string ...
EOF
```

```
 760 aLeftShoulder                  Byte           comment=755
 761 aRightShoulder                 Byte           comment=764
 762 aTakedownButton                Byte           comment=773
 763 aQuickStrike                   Byte           comment=782
 764 aHeavyStrike                   Byte           comment=791
 765 aChargeStrike                  Byte           comment=800
 766 aGrappleButton                 Byte           comment=809
 767 bRawDpadUp                     Byte           comment=818
 768 bRawDpadDown                   Byte           comment=827
 769 bRawDpadLeft                   Byte           comment=836
 770 bRawDpadRight                  Byte           comment=845
 771 bRunButton                     Byte           comment=854
 772 bCrouchButton                  Byte           comment=863
 773 bReadyGadgetButton             Byte           comment=872
 774 bCancelButton                  Byte           comment=881
 775 bForensicsButton               Byte           comment=890
 776 bHandBrakeButton               Byte           comment=899
 777 bArmouredMode                  Byte           comment=908
 778 bFireVehicleWeapon             Byte           comment=917
 779 bFireVehicleSecondaryWeapon    Byte           comment=926
 780 bThrottleButton                Byte           comment=935
 781 bVehicleBoostButton            Byte           comment=944
 782 bBrakeButton                   Byte           comment=953
 783 bHandbrakeOrBrake              Byte           comment=962
 784 bGadgetSelectWheel             Byte           comment=971
 785 bLookBehindVehicle             Byte           comment=980
 786 bBatmobileEjectModifier        Byte           comment=989
 787 bLeftStickDown                 Byte           comment=998
 788 RawLeftY                       Float          comment=1007
 792 RawLeftX                       Float          comment=1016
 796 RawRightY                     Float          comment=1025
 800 RawRightX                     Float          comment=1034
=== right trigger bind lines ===
   .Bindings=(Name="XboxTypeS_RightTrigger",Command="StealthOrGadget | DebugMenuQualifyOnT | OnRelease DebugMenuQualifyOffT | DebugMenuNextPage | AttackThrow | BatmobileFireButton | Button bFireVehicleWeapon | FireGun | DeepScanIn ")
```

Where the token -> field mapping is recorded, and the array element types:

```
cd "E:/Modding/JustCause3/JC3-Batmobile" && grep -n "bRunButton\|bCrouchButton" Research/BatmobileGrab/CONTROLS.md | head -8
grep -rn "Button bCancelButton" Research/BatmobileGrab/*.json Research/BatmobileGrab/*.md | head -8
grep -rn "aThrottleAxis\|RightTriggerAxis" Research/BatmobileGrab/*.json | head -6
grep -rn "StealthOrGadget" Research/BatmobileGrab/BINDINGS_MERGED.json | head -3
```

```
524:| `bCrouchButton` | True | 1 | `RPlayerInput.bCrouchButton` (ByteProperty) |
538:| `bRunButton` | True | 1 | `RPlayerInput.bRunButton` (ByteProperty) |
Research/BatmobileGrab/BINDINGS_KEYBOARD.json:804:   "command": "ExitAgilityMode | QuickGadgetB | OnRelease ReleaseQuickGadgetB | Cover | BlockBreaker | SkipCutscene | CancelGadget | DebugMenuSelectB | CancelBatarangCamera | Button bCancelButton",
Research/BatmobileGrab/BINDINGS_MERGED.json:2981:    "line": ".Bindings=(Name=\"XboxTypeS_B\",Command=\"ExitAgilityMode | QuickGadgetB | OnRelease ReleaseQuickGadgetB | Cover | BlockBreaker | SkipCutscene | CancelGadget | DebugMenuSelectB | CancelBatarangCamera | Button bCancelButton\")"
Research/BatmobileGrab/BINDINGS_MERGED.json:1248:    "body": "Name=\"XboxTypeS_RightTriggerAxis\",Command=\"AxisaRightTriggerSpeed=1.0DeadZone=0.2|AxisaUpSpeed=1.0DeadZone=0.1|AxisaThrottleAxisSpeed=1.0DeadZone=0.0\""
Research/BatmobileGrab/BINDINGS_MERGED.json:768:    "body": "Name=\"StealthOrGadget\",Command=\"StealthOrGadgetPressed|OnReleaseEndStealthMove|OnReleaseGadgetReleased|ButtonbCrouchButton|FloorTakedownModifierPressed|OnReleaseFloorTakedownModifierReleased|LedgeToCeilingPressed|LandPressed\""
```

```
203 /// Function: ClearLastTargets
205 public unsafe virtual void ClearLastTargets()
300 /// ArrayProperty: CurrentTargets
302 public unsafe BmSDK.TArray<BmSDK.Engine.Actor> CurrentTargets
309 /// ArrayProperty: LastTargets
311 public unsafe BmSDK.TArray<BmSDK.Engine.Actor> LastTargets
549 /// ArrayProperty: FiredProjectiles
551 public unsafe BmSDK.TArray<BmSDK.BmGame.RProjectile> FiredProjectiles
=== Actor class decl ===
Engine/Actor.g.cs ['public partial class Actor : BmSDK.StateObject, BmSDK.IGameObject']
Core/GameObject.g.cs ['public partial class GameObject : BmSDK.IGameObject']
=== FScriptInterface ===
E:/Modding/_shared/tools/BmSDK-AK/src/BmSDK/Framework/MarshalUtil.cs:12:    private struct FScriptInterface
E:/Modding/_shared/tools/BmSDK-AK/src/BmSDK/Framework/MarshalUtil.cs-14-        public IntPtr ObjectPointer;
E:/Modding/_shared/tools/BmSDK-AK/src/BmSDK/Framework/MarshalUtil.cs-15-        public IntPtr InterfacePointer;
```

Preserving the previous document before overwriting the path the brief names:

```
cd "E:/Modding/JustCause3/JC3-Batmobile" && cp Research/BatmobileGrab/SAMPLER_UNKNOWNS.md Research/BatmobileGrab/SAMPLER_UNKNOWNS_G3-02f.md && sha256sum Research/BatmobileGrab/SAMPLER_UNKNOWNS_G3-02f.md
```

```
970e948a60fd6b247be014b1975e73fd26615df0e635e593418744e93c929085 *Research/BatmobileGrab/SAMPLER_UNKNOWNS_G3-02f.md
```

The generator, then its check (final run):

```
cd "E:/Modding/JustCause3/JC3-Batmobile" && set -o pipefail && PYTHONIOENCODING=utf-8 uv run python Tools/scripts/bmak_sampler_unknowns.py --write; echo "WRITE_EXIT=$?"; echo "=== CHECK ==="; PYTHONIOENCODING=utf-8 uv run python Tools/scripts/bmak_sampler_unknowns.py --check; echo "CHECK_EXIT=$?"
```

```
wrote Research\BatmobileGrab\SAMPLER_UNKNOWNS.md
answer verdicts: 4 answered, 3 partly, 7 total; bytes observed 32, flag words 2, logs 2/67 records
oracles: {"a_bind_chain": true, "axis_bind_separate": true, "bytes_named": true, "controller_reachable": true, "eject_cockpit_bit": true, "flag_bits_named": true, "prev_preserved": true, "results_unknown_count": true, "rt_bind_chain": true, "stride_rule": true, "tarray_count_offset": true, "x_bind_chain": true}
  a_bind_chain: OK - 771=771, via named binding "Run" on this line
  axis_bind_separate: OK - throttle-axis writers ['XboxTypeS_RightTriggerAxis'], RT line has no Axis token
  bytes_named: OK - 32 observed byte offsets, 12 inside a wider field, unresolved []
  controller_reachable: OK - FindObjects at Game.cs:127, PlayerInput member +1240
  eject_cockpit_bit: OK - 2026-11-05T07:56:04.263Z gained 0x80000 bCockpitOpen
  flag_bits_named: OK - 31 masked bools at +4568, unresolved []
  prev_preserved: OK - sha256 970e948a60fd6b24
  results_unknown_count: OK - numbered UNKNOWNs in SAMPLER_RESULTS.md = 6 (plus the 774 mapping row = 7)
  rt_bind_chain: OK - 778 in=True, 772 in=True, 780 in=False
  stride_rule: OK - actor base BmSDK.StateObject, rule gameobject=True, stride 8
  tarray_count_offset: OK - AllocatorInstance/Num/Max present; count at +8
  x_bind_chain: OK - 783=783, via named binding "BrakeButton" on this line
WRITE_EXIT=0
=== CHECK ===
OK Research\BatmobileGrab\SAMPLER_UNKNOWNS.md byte-identical to a fresh rebuild
answer verdicts: 4 answered, 3 partly, 7 total; bytes observed 32, flag words 2, logs 2/67 records
oracles: {"a_bind_chain": true, "axis_bind_separate": true, "bytes_named": true, "controller_reachable": true, "eject_cockpit_bit": true, "flag_bits_named": true, "prev_preserved": true, "results_unknown_count": true, "rt_bind_chain": true, "stride_rule": true, "tarray_count_offset": true, "x_bind_chain": true}
  ... (same 12 lines) ...
CHECK_EXIT=0
```

The earlier card still checks clean (this is the G3-10c regression run; my first attempt used
`--with numpy` only and raised `ModuleNotFoundError: scipy`, a flag error on my side, not a drift):

```
cd "E:/Modding/JustCause3/JC3-Batmobile" && PYTHONIOENCODING=utf-8 uv run --with numpy --with scipy python Tools/scripts/grab_inertia.py --check 2>&1 | tail -4; echo "INERTIA_CHECK_EXIT=${PIPESTATUS[0]}"
```

```
oracle jc3_box_formula_reproduced (reported, not a drift): ok=False {"hits_1pct": 0, "of": 107, "median_ratio": [1.275178, 1.287701, 1.276702]}
oracle jc3_hull_formula_reproduced (reported, not a drift): ok=False {"hits_1pct": 0, "of": 107, "median_ratio": [1.275178, 1.287701, 1.276702], "all_bodies_hits_1pct": 0}
OK: bmak tags no mass/inertia; jc3 blocks 56, boxes 107, box-oracle 0/107, bias 111, com median 0.0156
INERTIA.md/json current
INERTIA_CHECK_EXIT=0
```

## UNKNOWNs (still open, with what was tried)

1. **Why `BoostingOut` (+5901) is 1 for ~0.05 s at the eject.** Tried: the generated class (offset and
   comments only, no bodies), the eject documents (`EJECT_VELOCITY.md`, `EJECT_MOVE.md` - kinematics,
   no mention), `PHYSICS.md` / `COLLISION_GEOM.md` (collision only), and a search over all of
   `Research/` (`BoostingOut` appears only in sampler notes). Where it would be found: the UFunction
   body that writes +5901, i.e. the eject/animation path's bytecode, which no card has decoded yet.
2. **What consumes the barrage charge on an X press.** Tried: the bind chain (decoded, 783 is X) and
   `RPlayerController.QuickGadgetX`, which is a `ProcessEvent` wrapper (`:489`) with no body in the
   tree. Where: the `QuickGadgetX` body, or a capture that reads `WeaponGeneratorPower` (0x1EE8) in
   the same frame as a 783 edge.
3. **What produced the five `774 bCancelButton` taps.** Tried: every decoded bind string that writes
   `Button bCancelButton` (only `XboxTypeS_B`, `DefaultInput.ini:268`; the X and A lines carry
   `CancelBatarangCamera`, not the Button token), and the tap times against the stated presses
   (gaps 0.718 / 1.131 / 11.203 / 1.489 / 1.130 s to the next other rise - see the document's table). No
   keyboard binding writes it and B was not part of the stated script. Where: a device-level trace,
   or a keyboard `Button bCancelButton` binding if one exists in a config this project has not dumped.
4. **Whether U2's pulse is the boost being cancelled by the eject** - the plausible story, recorded as
   unproven, not as a finding.

Nothing above was filled in from general knowledge of Arkham Knight or UE3; the document labels every
row decoded / derived / UNKNOWN.
