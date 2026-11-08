# DONE — GADGET-params (the 48 `RBatmobileRemoteBm` parameters)

STATUS: **done** — the 48 remote-gadget parameters are located (`BmScript.RBatmobileRemoteBm`,
48 member exports in `Startup.upk` and `StartupPatch.upk`) and their values are read from the class
default object `BmScript.Default__RBatmobileRemoteBm` (`Startup.upk` 536, `StartupPatch.upk` 520;
364 B payload, 33 tags each). Of the 48, **23 are value slots** (11 floats, 10 object pointers,
2 bools) and **25 are behaviour** (22 functions, 3 states). **16** of the 23 values are decoded from
tag payloads; **7** carry no tag in either package and are marked **UNKNOWN**, not assumed.
Every decoded value carries package, export, payload offset, class offset and the bindings line, so
the translation can use the table without another lookup. No JC3 mapping is decided.

## Files written (the only files touched)

| path | what |
|---|---|
| `Tools/scripts/grab_gadget_params.py` | new script, `--write` / `--check`; reads both packages + the BmSDK bindings |
| `Research/BatmobileGrab/GADGET_PARAMS.md` | generated report (25,936 chars) |
| `tmp/freebuff/reports/GADGET-params.md` | this DONE report |

Read-only: `Startup.upk`, `StartupPatch.upk`, `E:/Modding/_shared/tools/BmSDK-AK/src/BmSDK/Generated/**`
(MIT), `Research/BatmobileGrab/PACKAGES_G305.md` (the 48-name list, cross-checked against the export
table), `Tools/scripts/upk_read.py` and `Tools/scripts/grab_class_defaults.py` (imported unmodified —
its `Layout`/`same_kind` helpers, the proven namer from G3-06b). No game ran, nothing under
`E:/Games` was written, no build, no git.

## The values (decoded)

Declaring class `RBatmobileRemoteBm`, CDO export 536, source = payload offset @ tag.

| field | type | value | class off | payload @ | bindings |
|---|---|---|---:|---:|---|
| `JammingRange` | FloatProperty | 10000.0 | 0x968 | 0x2c | :426 |
| `JammerTime` | FloatProperty | 1.5 | 0x970 | 0x34 | :453 |
| `CurrentJam` | FloatProperty | -1.0 | 0x974 | 0x3c | :462 |
| `CursorSpeed` | FloatProperty | 3.0 | 0x978 | 0x44 | :471 |
| `CursorAccel` | FloatProperty | 5.0 | 0x97c | 0x4c | :480 |
| `CursorDecel` | FloatProperty | 10.0 | 0x980 | 0x54 | :489 |
| `CursorReturnFactor` | FloatProperty | 2.0 | 0x984 | 0x5c | :498 |
| `CursorReturnDelay` | FloatProperty | 2.0 | 0x988 | 0x64 | :507 |
| `MaxAimX` | FloatProperty | 0.899999976 (stored 32-bit) | 0x98c | 0x6c | :516 |
| `MaxAimY` | FloatProperty | 0.899999976 | 0x990 | 0x74 | :525 |
| `RelativeAimingCurvePower` | FloatProperty | 1.0 | 0x994 | 0x7c | :534 |
| `FireSound` | ObjectProperty | `Ww_CHR_RemoteGadget.Play_Remote_Gadget` (AkEvent) | 0x930 | 0x4 | :363 |
| `CancelSound` | ObjectProperty | `Ww_CHR_RemoteGadget.Play_Remote_Gadget` (AkEvent) | 0x938 | 0xc | :372 |
| `CancelSound2` | ObjectProperty | `Engine.Play_Remote_Gadget_Off` (AkEvent) | 0x940 | 0x14 | :381 |
| `CallSound` | ObjectProperty | `Engine.Play_Gauntlet_Batmobile_Call` (AkEvent) | 0x948 | 0x1c | :390 |
| `RemoteControlBatmobileMove` | ObjectProperty | `Batmobile_Remote.RemoteControlBatmobile` (RSpecialMoveConfigConfigurable) | 0x958 | 0x24 | :408 |

(`bindings` = `RBatmobileRemoteBm.g.cs:<line>`, the doc block that declares the field at that offset.)

## UNKNOWN — the 7 value slots with no tag in either CDO

`bRelativeAiming` (0x96c), `ScreenOn` (0x96c), `ReachedRemoteHardLimitThought` (0x960),
`CurrentRiotSuppressorTarget` (0x950), `NpcBatmobileTarget` (0x928), `CallingVehicle` (0x920),
`RiotSuppressorBatmobile` (0x918).

A cooked stream omits a property that equals the class's initial value, so these are probably
`false`/`None` — but that is a hypothesis about the cooker, not a byte fact, and it is not used.
Tried: both packages (identical omission), the whole 364 B payload (walk closes at 362 with 0
unexplained bytes, so no tag is being skipped), and a search for an archetype of this class in
either package (none). Would be settled only by the cooker's omission rule.

## The 25 behaviour members (no value exists)

`Function` × 22 and `State` × 3 exports under the class: `GetPromptName`, `GetHelpPrompt`,
`GetPrimedPose`, `GetFireAnim`, `PlayerTick`, `CallBatmobile`, `CancelCallBatmobile`, `DrawTarget`,
`ShowFailIcon`, `ClearTarget`, `GetAimAtRotation`, `Holstered`, `Primed`,
`ControlBatmobileRiotSuppressor`, `DontMoveCursor`, `PowerOnScreen`, `PowerOffScreen`,
`NotifyCallBatmobileToMe`, `NotifyRemoteDriveCancelled`, `NotifyBatmanPickedUp`,
`StartChargingJammer`, `GetFiringAnimationOverlay`, `GetPC`, `OnGadgetWheelSelected`,
`NotifyReachedHardRemoteLimit`. Their payloads are untagged 30-byte records (`PACKAGES_G305.md` §4),
so bodies and constants are stripped: behaviour is UNKNOWN.

## Inherited defaults the CDO also carries (decoded, needed with the table)

`GadgetType` = `GA_Gadget_JammerGadget` (0x311), `HudGadgetId` = `FGID_BatarangMulti2` (0x314),
`Mesh` = `Default__RBatmobileRemoteBm.GadgetMesh` (SkeletalMeshComponent, 0x318),
`AimPosition` = [0.5, 0.5, 0.0] (0x824), `EquipBoneName` = `Gundummy`, `EquipBoneName2` =
`Gundummy02` (0x378/0x380), `TargetClass` = `AntiPersonelGun` (0x4b4), `GadgetListEnum` = 13 (0x514),
`AssociatedGadgetFlagName` = "Equip_BatmobileRemote" (0x558), wire/railing turn bones
`Omnitron_Wire_180_Left/Right`, `Omnitron_Railing_180_Left/Right` (0x530–0x548),
`fLastPlayedGadgetSpeechTime` = -60.0 / `fGadgetSpeechCooldownTime` = 60.0 (0x5c8/0x5cc), the
`RInventoryGadget` bool word `0x034803b0` (0x460, 9 bits set) and the `Actor` bool word `0x8a00_...`
at 0x104.

Object references followed one level: `FireSound`/`CancelSound` → export 46245 (18 B, 2 tags),
`RemoteControlBatmobileMove` → export 169080 (10 B, 1 tag), `Mesh` → export 166735 (58 B, no tags →
mesh asset/materials UNKNOWN), `CancelSound2`/`CallSound` → imports of other packages (reported by
path only).

## Startup vs StartupPatch (derived)

95 decoded rows compared: **0** differences in float/int/bool/name/string/vector/enum values, and
**2** object rows differ only in the target's package-qualified path at the same class:
`CancelSound2` `Engine.Play_Remote_Gadget_Off` vs `Ww_CHR_RemoteGadget.Play_Remote_Gadget_Off`;
`CallSound` `Engine.Play_Gauntlet_Batmobile_Call` vs `Ww_CHR_BatmanGauntlet.Play_Gauntlet_Batmobile_Call`.
Both resolve through their own package's tables, so this is a real byte difference; which one an
installed build uses is a load-order question (UNKNOWN, not investigated).

## Commands run, with output

Probe that located the class and CDO in both packages and dumped the tag stream:

```
$ python - <<'PYEOF'  # find Default__RBatmobileRemoteBm, walk tags, list CDO refs
== Startup.upk 434869146
CDO exports [(536, 'BmScript.Default__RBatmobileRemoteBm', 'RBatmobileRemoteBm', 364)]
 payload 364 10 00 30 09 a5 b4 00 00 10 00 38 09 a5 b4 00 00 10 00 40 09 97 fe ff ff 10 00 48 09 bd fe ff ff 10 00 58 09 78 94 02 00 04 00 68 09 00 40 1c 46 04 00 70 09 00 00 c0 3f 04 00 74 09 00 00 80 bf
 tags 33 end 362 stop eof
    ObjectNCRProperty off 0x930 None size None at 4
    ...
    FloatProperty off 0x968 ... at 44 ... FloatProperty off 0x994 ... at 124
    VectorProperty off 0x824 ... at 132
    ByteProperty off 0x311 GadgetType size 8 at 164
    ByteProperty off 0x314 HudGadgetId size 8 at 192
    ...
== StartupPatch.upk 248812096
CDO exports [(520, 'BmScript.Default__RBatmobileRemoteBm', 'RBatmobileRemoteBm', 364)]
 tags 33 end 362 stop eof
```

Probe of the class chain and the 48 member exports (`OWNED-UNDER-CLASS 0` was my own prefix bug:
`object_path` joins one level, so members are `RBatmobileRemoteBm.<name>`; the script matches by
`outer_index` instead):

```
CHAIN ['RBatmobileRemoteBm', 'RBatmobileRemote', 'RInventoryGadget', 'Inventory', 'Actor', 'StateObject', 'GameObject', 'IGameObject']
== RBatmobileRemoteBm props 23
    0x918 ObjectProperty RiotSuppressorBatmobile ... 0x994 FloatProperty RelativeAimingCurvePower line 534
== RBatmobileRemote props 18
== RInventoryGadget props 153
== Inventory props 15
== Actor props 212
```

The deliverable's runs, including the two failures that pinned the reader's shape:

```
$ PYTHONIOENCODING=utf-8 python Tools/scripts/grab_gadget_params.py --write
WRITE_EXIT=1
class export BmScript.RBatmobileRemoteBm not found in Startup.upk
```

```
$ PYTHONIOENCODING=utf-8 python Tools/scripts/grab_gadget_params.py --write
WRITE_EXIT=1
  File "...grab_gadget_params.py", line 456, in build
    f"{tgt.get('export', '-')} | {tgt.get('export_bytes', '-')} | {tgt['inner_label']} |")
KeyError: 'inner_label'
```

(The first: a class object's own class is `Class`, so the identity test had to be the path plus the
name. The second: import targets have no in-package payload, so they now carry an explicit
`UNKNOWN (import)` label.)

```
$ PYTHONIOENCODING=utf-8 python Tools/scripts/grab_gadget_params.py --write; echo "WRITE_EXIT=$?"; ... sed -n '/## 8\./,/## 9\./p' ...
wrote Research/BatmobileGrab/GADGET_PARAMS.md (24,995 chars)
WRITE_EXIT=0
| `packages_agree` | False | {"compared": 95, "differences": [["CancelSound2", 2368, "ObjectNCRProperty", "`Engine.Play_Remote_Gadget_Off` (AkEvent)", null], ...
```

That failure was a real finding, not a bug: two sound references resolve to different outer packages
in the two startup packages. The oracle was replaced by the split in §7 (scalars must match exactly;
object rows must match in class), and §7 now reports the two paths.

```
$ PYTHONIOENCODING=utf-8 python Tools/scripts/grab_gadget_params.py --write; echo "WRITE_EXIT=$?"; PYTHONIOENCODING=utf-8 python Tools/scripts/grab_gadget_params.py --check; echo "CHECK_EXIT=$?"; ... sed -n '/## 7\./,/## 8\./p' ...
wrote Research/BatmobileGrab/GADGET_PARAMS.md (25,875 chars)
WRITE_EXIT=0
OK rebuilt byte-identical from Startup.upk, StartupPatch.upk and the BmSDK bindings
CHECK_EXIT=0
## 7. ...
**95** decoded rows compared per package. Scalar, name, string, vector and enum
values: **0** differences. Object references: **2** rows
differ, every one of them in the package-qualified path of the target rather than its class:
| `CancelSound2` | 0x940 | `Engine.Play_Remote_Gadget_Off` (AkEvent) | `Ww_CHR_RemoteGadget.Play_Remote_Gadget_Off` (AkEvent) | `AkEvent` |
| `CallSound` | 0x948 | `Engine.Play_Gauntlet_Batmobile_Call` (AkEvent) | `Ww_CHR_BatmanGauntlet.Play_Gauntlet_Batmobile_Call` (AkEvent) | `AkEvent` |
```

```
$ PYTHONIOENCODING=utf-8 python Tools/scripts/grab_gadget_params.py --write; echo "WRITE_EXIT=$?"; PYTHONIOENCODING=utf-8 python Tools/scripts/grab_gadget_params.py --check; echo "CHECK_EXIT=$?"; ... grep -c "| False |" ...
wrote Research/BatmobileGrab/GADGET_PARAMS.md (25,936 chars)
WRITE_EXIT=0
OK rebuilt byte-identical from Startup.upk, StartupPatch.upk and the BmSDK bindings
CHECK_EXIT=0
| `RInventoryGadget` | `GadgetType` | ByteProperty | `GA_Gadget_JammerGadget` (enum `GadgetType`) | `Startup.upk` 536 @0xa4 (class 0x311; `RInventoryGadget.g.cs:1968`) | ...
| `RInventoryGadget` | `HudGadgetId` | ByteProperty | `FGID_BatarangMulti2` (enum `HudGadgetId`) | `Startup.upk` 536 @0xc0 (class 0x314; `RInventoryGadget.g.cs:1995`) | ...
0
```

`grep -c "| False |"` prints `0`: no oracle row is false. (The shell's last status 1 is grep finding
no match, which is the desired result.)

## Labels

**decoded** — the class/CDO exports and their sizes, sha1s and tag counts; all 33 tags and their
offsets; every value in the table above; the enum entries; the object target paths and classes;
`GadgetType`, `HudGadgetId`, the mesh component and the inherited names/numbers; the bool-word
bit splits; the 48-member census; all 9 oracle values.
**derived** — "23 value slots"; the tagged/untagged split; the Startup↔StartupPatch comparison
(0 scalar diffs, 2 object-path diffs); the bool bit extraction rule; "the 25 behaviour members have
no value".
**UNKNOWN** — the 7 untagged value slots; the component-target interiors; the function/state bodies;
which startup package's sound reference an installed build uses.

## UNKNOWNs (with what was tried)

1. **7 value slots with no tag** — tried both CDOs, the full payload walk (closes, 0 unexplained),
   and an archetype search. Need the cooker's omission rule, which the files do not state.
2. **Interiors of the followed component target** (`GadgetMesh`, 58 B, no tags) — nothing readable.
3. **The 25 function/state bodies** — 30-byte untagged payloads; no bytecode, no constants.
4. **Which startup package's sound paths are live** — `Startup.upk` and `StartupPatch.upk` name
   different outer packages for the same two sounds; load order decides, and it is not recorded in
   the files read here.

## Housekeeping

- `--check` passes and re-derives every number from the two packages and the bindings (9 oracles).
- The brief named its DONE path, so there is no `manual/claimed/` task file to move.
- Earlier cards on this branch remain green: `grab_driverleft_regions.py --check`,
  `grab_vecdefaults.py --check` and `sampler_unknowns.py --check` all rebuild byte-identically.
