# Chase 08 — F-57 … F-64 (air control, slope factor, stay-upright angles)

Scope: `Research/BatmobileGrab/FOOTAGE.md` §6 rows **F-57 … F-64**, all `UNKNOWN` with reason
`VALUE-NATIVE`. Read-only chasing: no existing document edited, no game launched, nothing
committed. Only new files: `Tools/scripts/chase/chase08_cdo.py` and
`E:/Modding/ArkhamKnight/_grab/chase/value_cdo_08.json`.

**Result: 4 of 8 FOUND, 4 STILL UNKNOWN.** Four values are serialised — not in any vehicle
archetype (which is what G1-21 read) but in the **class default object**
`Default__RVehicleSimBatmobile` inside `BmGame.upk`. The four still unknown are the ones that
class does not override: `AirControlTimeInAir` (0x4bc), `AirControlTurnTorque` (0x17c on
`RVehicleSimCar`) and the two `StayUpright*ResistAngle` fields (0x6d4/0x6d8 on `SVehicle`, whose
default object lives in `Engine.upk` and does not carry them either).

| row | field | value | provenance |
|---|---|---|---|
| F-57 | `AirControlYawTorqueFactorMin` | **2000.0** (engine torque gain) | decoded |
| F-58 | `AirControlPitchTorqueFactorMin` | **3000.0** (engine torque gain) | decoded |
| F-59 | `AirControlInterpTime` | **1.5 s** | decoded |
| F-60 | `AirControlTimeInAir` | **STILL UNKNOWN** — not serialised in the class default object either | — |
| F-61 | `BattleModeSlopeFactor` | **0.5** (factor) | decoded |
| F-62 | `AirControlTurnTorque` | **STILL UNKNOWN** — not serialised on `RVehicleSimCar`'s default object | — |
| F-63 | `StayUprightRollResistAngle` | **STILL UNKNOWN** — `Default__SVehicle` (`Engine.upk`) has no such tag; native | — |
| F-64 | `StayUprightPitchResistAngle` | **STILL UNKNOWN** — same | — |

Units are the ones `MODES.md` assigns by field name (`float`, seconds for the two time fields);
nothing is rescaled and no value is converted.

## 1. Route 1 — the class default object (found the four)

The reader is `Tools/scripts/chase/chase08_cdo.py`. It opens the shipped package, walks the
`Default__<Class>` export's property-tag stream and matches the card's BmSDK offsets:

```
$ python Tools/scripts/chase/chase08_cdo.py --dump --json E:/Modding/ArkhamKnight/_grab/chase/value_cdo_08.json
package BmGame.upk: version 863, licensee 32995, 84813 names, 3268 imports, 177031 exports

=== RVehicleSimBatmobile (export 129778, class None, 176 B)
    walked 0 tags, stop=end

=== Default__RVehicleSimBatmobile (export 129779, class RVehicleSimBatmobile, 724 B)
    walked 58 tags, stop=eof
    -- F-57..F-64 offsets on RVehicleSimBatmobile:
       AirControlYawTorqueFactorMin       @0x04b0  SERIALISED 2000.0 (FloatProperty)
       AirControlPitchTorqueFactorMin     @0x04b4  SERIALISED 3000.0 (FloatProperty)
       AirControlInterpTime               @0x04b8  SERIALISED 1.5 (FloatProperty)
       AirControlTimeInAir                @0x04bc  absent
       BattleModeSlopeFactor              @0x04c0  SERIALISED 0.5 (FloatProperty)

=== RVehicleSimCar (export 129608, class None, 104 B)
    walked 0 tags, stop=end

=== Default__RVehicleSimCar (export 129609, class RVehicleSimCar, 122 B)
    walked 15 tags, stop=eof
    -- F-57..F-64 offsets on RVehicleSimCar:
       AirControlTurnTorque               @0x017c  absent

no export named SVehicle or Default__SVehicle
wrote E:/Modding/ArkhamKnight/_grab/chase/value_cdo_08.json
```

Offset identity is not invented: `Research/BatmobileGrab/BMSDK_OFFSETS.json` →
`classes.RVehicleSimBatmobile.properties` gives 0x4b0 `AirControlYawTorqueFactorMin`, 0x4b4
`AirControlPitchTorqueFactorMin`, 0x4b8 `AirControlInterpTime`, 0x4bc `AirControlTimeInAir`,
0x4c0 `BattleModeSlopeFactor` (neighbours 0x4a8/0x4ac `…TorqueFactorMax` = 5000.0 / 5000.0 are in
the same tag stream, which fixes the alignment). The tag is a `FloatProperty` and the value is the
serialised payload, so provenance is **decoded** (R4), not derived: no arithmetic in the way.

Cross-check inside the same object: the stream is monotonic and every neighbour the SDK lists is
present — 0x4a8 5000.0, 0x4ac 5000.0, 0x4b0 2000.0, 0x4b4 3000.0, 0x4b8 1.5, 0x4c0 0.5. The one
gap, 0x4bc, is exactly the field the card asks about (F-60), i.e. the class does not override it.

## 2. Route 1b — can another default object hide the missing four?

`--scan` walks every `Default__*` export whose name looks like a vehicle/sim class and reports any
tag at one of the eight offsets.

```
$ python Tools/scripts/chase/chase08_cdo.py --scan
-- scanning ... Default__*Vehicle*/Batmobile/Sim objects for
   ['0x17c', '0x4b0', '0x4b4', '0x4b8', '0x4bc', '0x4c0', '0x6d4', '0x6d8']
   Default__RVehicleCombatManager (export 12811): [('0x17c', None, 2200.0)]
   Default__RBatmobileAllegianceSwitcher (export 46256): [('0x4b4', None, 'BatmobileAllegianceSwitcher')]
   ... (12 more `RBatmobile*` objects, all 0x4b4 StringProperty names) ...
   Default__RVehicleSimBatmobile (export 129779): [('0x4b0', None, 2000.0), ('0x4b4', None, 3000.0),
                                                    ('0x4b8', None, 1.5), ('0x4c0', None, 0.5)]
   -> 14 object(s) carry any of the eight offsets
```

No object carries 0x4bc. The 0x4b4 hits on the `RBatmobile*` classes are string properties in
*their* layouts (weapon/tracker names), not this field — an offset is only meaningful inside the
class that declares it, so those are rejected, not averaged. 0x17c on `Default__RVehicleCombatManager`
(2200.0) and on `Default__RSeqAct_SpawnVehicle` (bool) are likewise other classes' fields.

`SVehicle` is a `BmSDK.Engine` class, so its default object is in `Engine.upk`, not `BmGame.upk`:

```
$ python Tools/scripts/chase/chase08_cdo.py --package ".../Engine.upk" --dump
package Engine.upk: version 863, licensee 32995, 26790 names, 191 imports, 39080 exports
=== SVehicle (export 11159, class None, 669 B)
    walked 0 tags, stop=end
=== Default__SVehicle (export 11160, class SVehicle, 408 B)
    walked 32 tags, stop=eof
    -- F-57..F-64 offsets on SVehicle:
       StayUprightRollResistAngle         @0x06d4  absent
       StayUprightPitchResistAngle        @0x06d8  absent
```

Its 32 tags are 0x66c, 0x68c, 0x6c8 (`InertiaTensorMultiplier` `[1,1,1]`), 0x6e4/0x6ec (the two
constraint object references), 0x70c (0.5), 0x710 (2500.0) and the `Actor`/`Pawn` tail — the
stream jumps 0x6c8 → 0x6e4, straight over 0x6d4/0x6d8. A scan of `Engine.upk`'s 17
`Default__*Vehicle*` objects for the same offsets returns only one unrelated hit
(`Default__AkPlayerVehicleSoundInfo` 0x6d8 = 37019, a sound-info field). So no default object in
either package sets the two resist angles.

## 3. Route 2 — the executable

`BatmanAK.exe` (55,101,440 B) contains the class names but no property names: `RVehicleSimBatmobile`
appears 6× as ASCII (all `RVehicleSim<Class>exec<Function>` registration strings at 0x1e02b21 …
0x1e02be1, e.g. `RVehicleSimBatmobileexecSkidToStop`) and 1× as UTF-16; `AirControlTimeInAir`,
`AirControlTurnTorque`, `AirControlInterpTime`, `StayUprightRollResistAngle` and
`StayUprightPitchResistAngle` appear **0 times** in either encoding:

```
$ python -c "...data.count(s.encode('utf-16-le')), data.count(s.encode('ascii'))..."
StayUprightRollResistAngle utf16 0 ascii 0
StayUprightPitchResistAngle utf16 0 ascii 0
AirControlTurnTorque utf16 0 ascii 0
AirControlTimeInAir utf16 0 ascii 0
AirControlInterpTime utf16 0 ascii 0
RVehicleSimCar utf16 2 ascii 0
RVehicleSimBatmobile utf16 1 ascii 6
```

That is the honest limit: with no name string in the image there is no anchor to the initialising
code, and scanning 55 MB of x64 for "a float that might be 45.0" would produce a number with no
provenance — the exact thing R4 forbids. No address is claimed for F-60/F-62/F-63/F-64.

## 4. Route 3 — the captures

`C:\Users\User\Videos\Captures` holds the five AK clips (`Air steer down 2-5s`, `Air steer right
3-6s`, `Air steer up 2-5s`, `Battlemode entry_6-20s. Movement 20-29s Boost 30-38s`, `VulcanFire_10s-15s`).
The three air-steer clips show attitude change under a known input, but the four missing fields are
not visible quantities:

* `AirControlTimeInAir` is a threshold (when air control starts applying) — the clips carry no
  input telemetry, so the moment of input cannot be aligned to a frame.
* `AirControlTurnTorque` is a torque; turning it into an observed angular acceleration needs the
  body inertia, and the only inertia datum on the object is a per-axis multiplier
  (`InertiaTensorMultiplier` 0x6c8 = [1,1,1] on `SVehicle`, from the tags above), not the tensor.
* `StayUpright*ResistAngle` are limits enforced by a native constraint (`RB_StayUprightSetup`
  object 11471, no tags — `MODES.md` §“StayUprightConstraintSetup/Instance are object references”).
  No clip tips the car to a measurable lean.

Nothing measurable was extracted; the earlier air-time measurement (`FOOTAGE.md` header: 1.212 s
mean over three ramp jumps) is about F-6, not these rows, and is not reused as a value here.

## 5. Route 4 — published sources (cross-check only)

Two searches, no usable hit: `"RVehicleSimBatmobile" OR "AirControlTimeInAir" Arkham Knight
vehicle defaults UnrealScript` returned **zero organic results**; a broader search on Batmobile air
control / stay-upright modding parameters returned only control-remap articles, a Nexus Batwing
fly-mode mod and the camera-tool page — none documents these fields or their values. No value in
this row set rests on a published source; the four FOUND values rest on the decoded payload alone.

## 6. Why the four found values were invisible to G1-21

G1-21 (`grab_modes.py`, `MODES.md:121`, `:195`, `:215`) compared the declared inventory with
`objects.jsonl`, which covers the 15 `Playable_Batmobile*` archetype packages. A `defaultproperties`
value lives in the class's own default object in the package that *defines* the class
(`BmGame.upk` for `BmGame` classes, `Engine.upk` for `Engine` classes), so an archetype-only census
sees "not serialised" for every field the subclass overrides — which is why these four were filed
`VALUE-NATIVE`. Same conclusion chase-02/04/06/07 recorded for their rows; this is the fifth class
it holds for.

The four that remain unknown are not "the same bug, not yet found": their default objects are read
here and do not carry the offsets, so the effective value comes from native code (or is the
zero-init) and cannot be decoded from the shipped packages.

## 7. Reproduction

```
python Tools/scripts/chase/chase08_cdo.py --dump --json E:/Modding/ArkhamKnight/_grab/chase/value_cdo_08.json
python Tools/scripts/chase/chase08_cdo.py --package "E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole/Engine.upk" --dump
python Tools/scripts/chase/chase08_cdo.py --scan
```

`value_cdo_08.json` holds both classes' decoded default objects, every tag with its offset, type
and value, plus the offset→field table the checks used.

## 8. Limits

* One build only (the installed PC copy, `BmGame.upk` v863, licensee 32995). A different patch
  could serialise F-60/F-62/F-63/F-64 in the CDO; nothing on this machine can show that.
* Tag names come back `None` for most tags (the walker reads offsets, not name indices), so
  identity is by offset against `BMSDK_OFFSETS.json`, cross-checked by the neighbouring offsets
  being present with the SDK's fields in order. For the four found values that alignment is
  monotonic and unambiguous; for the four absences it means "no tag at that offset", not "no
  entry of that name anywhere".
* `AirControlTimeInAir` absent from the CDO means "not overridden by this class", not "0.0". The
  effective value is whatever the parent/native default is, and neither is visible in the
  packages read here. Written as UNKNOWN on purpose.
