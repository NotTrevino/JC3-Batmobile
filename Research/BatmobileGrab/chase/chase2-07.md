# Chase 07, second pass — F-49 … F-56

Read first: `chase-07.md`. It closed **8 of 8** rows, so there is no `STILL UNKNOWN` row to re-chase.
What it left open is its own *Limits / UNKNOWNs* list: (1) the **absence-as-zero** inference behind
F-49 and F-52, (2) **F-50's unit**, (3) **F-55's unit**, (4) the exe scan being no evidence. This pass
takes those four, plus an independent re-derivation of the six serialised values from the raw bytes.

## Result

| row | field | status | value | provenance |
|---|---|---|---|---|
| F-49 | `TransformationAnimNode` | **FOUND** (upgraded) | **null reference** — no `AnimNodeSequence` assigned | `decoded` |
| F-50 | `BattleModeUprightTorqueFactor` | FOUND (confirmed) | **2000.0**, unit **UNKNOWN** (U-1) | `decoded` |
| F-51 | `BattleModeUprightMaxTorque` | FOUND (confirmed) | **2000.0** engine torque | `decoded` |
| F-52 | `TransformationRotation` | **FOUND** (upgraded) | **0, 0, 0** (pitch / yaw / roll) | `decoded` |
| F-53 | `TransformationTurnOnSpotSpeed` | FOUND (confirmed) | **360.0 cm/s** (= 3.6 m/s) | `decoded` |
| F-54 | `TransformationTurnFactor` | FOUND (confirmed) | **45.0** (factor) | `decoded` |
| F-55 | `BattleModeSteerBiasRate` | FOUND (confirmed) | **3.0**, unit **UNKNOWN** (U-2, F-72) | `decoded` |
| F-56 | `AirControlPitchTorqueFactorMax` | FOUND (confirmed) | **5000.0** torque gain | `decoded` |
| **U-1** | unit of F-50 | **STILL UNKNOWN** | value certain, scale not stated by any file | — |
| **U-2** | unit of F-55 | **STILL UNKNOWN** | value certain, scale not stated by any file | — |

No value changed. What changed is that the six numbers are now re-read from their payload bytes by a
different walk, F-49/F-52's "absent ⇒ zero" is now argued from the class size rather than assumed,
and the native route has been run in the form that could actually have produced a value.

## Evidence: the six values, re-derived

`BmGame.upk`, export **129779** `Default__RVehicleSimBatmobile` (class `RVehicleSimBatmobile`,
724 B). This pass walked **all 2,975** `Default__*` exports of the package (the first pass filtered
to `Default__*Vehicle*/Batmobile*`), so an override from any other default object would have shown:

```
$ python Tools/scripts/chase/chase2_defaults.py --offsets 0x354 0x370 0x374 0x384 0x398 0x39c 0x3c4 0x4ac 0x4a8
BmGame.upk: 177031 exports, image 356,085,334 B
walked 2975 Default__ objects, 2975 with a tag stream
-- 262 tag(s) at the card offsets
```

Filtering those 262 to the owning class:

| offset | field | on `Default__RVehicleSimBatmobile` | other default objects at the same offset |
|---|---|---|---|
| 0x354 | F-49 `TransformationAnimNode` | **ABSENT** | 32 (all other classes) |
| 0x370 | F-50 `BattleModeUprightTorqueFactor` | **2000.0** FloatProperty | 29 |
| 0x374 | F-51 `BattleModeUprightMaxTorque` | **2000.0** FloatProperty | 40 |
| 0x384 | F-52 `TransformationRotation` | **ABSENT** | 90 |
| 0x398 | F-53 `TransformationTurnOnSpotSpeed` | **360.0** FloatProperty | 17 |
| 0x39c | F-54 `TransformationTurnFactor` | **45.0** FloatProperty | 17 |
| 0x3c4 | F-55 `BattleModeSteerBiasRate` | **3.0** FloatProperty | 19 |
| 0x4ac | F-56 `AirControlPitchTorqueFactorMax` | **5000.0** FloatProperty | 6 |
| 0x4a8 | *control* `AirControlYawTorqueFactorMax` | **5000.0** FloatProperty | 5 |

The 262 "other class" hits are the low-offset collision `MODES.md` warns about (0x354, 0x384, 0x398,
0x39c, 0x3c4 are offsets dozens of unrelated classes use); **none is on `RVehicleSimBatmobile`**, and
the full list is in `E:/Modding/_BmAKgrab/chase/chase2_defaults_07.json`.

### The archetypes still do not override anything — checked with a second reader

`Research/BatmobileGrab/objects.jsonl` (20,128 exports, walked by a different tool) contains 4
`SimulationModel` exports. Across all four, the only tag in this offset set is the control:

```
$ python - (objects.jsonl, exports with "SimulationModel" in the name)
SimulationModel exports: 4
   Playable_BatmobileFunhouse_SF  [('0x4a8', 8000.0)]
   Playable_BatmobileJoker_SF     [('0x4a8', 8000.0)]
   Playable_BatmobileMK2_SF       [('0x4a8', 8000.0)]
   Playable_Batmobile_SF          [('0x4a8', 8000.0)]
offsets asked: 0x354 0x370 0x374 0x384 0x398 0x39c 0x3c4 0x4a8 0x4ac -> total tags: 4
```

So the four shipped cars override `AirControlYawTorqueFactorMax` (8000.0) and nothing else here: F-50,
F-51, F-53, F-54, F-55, F-56 all run the class default, and F-49/F-52 are not assigned by any
archetype either.

**Ini route — 0 hits.** Not tried at all by the first pass:

```
$ grep -rn -i -E "TransformationAnimNode|BattleModeUpright|TransformationRotation|TransformationTurn|BattleModeSteerBiasRate|AirControlPitchTorqueFactorMax" --include="*.ini" .
(no output)
```

## F-49 · `TransformationAnimNode` — absence-as-zero, now derived not assumed

**STATUS: FOUND. Null object reference.** The first pass's argument was "a cooked default object
serialises every property whose value differs from the zeroed default, so a non-null reference would
appear as a tag". That reasoning needed one missing fact, and it is measurable: **which object is the
diff base.** The class hierarchy in `BmGame.upk`:

```
class RVehicleSimBatmobile export 129778 super -> RVehicleSimCar   (class size 104 B = 0x68)
   Default__RVehicleSimCar: 15 tags, none at 0x354 / 0x384 / 0x370
   class RVehicleSimCar super -> SVehicleSimCar  (no class export in this package)
```

The parent's whole class layout is **104 bytes**, so it cannot carry a member at 0x354 or 0x384: both
properties are declared by `RVehicleSimBatmobile` itself (BMSDK lists them under that class). For a
property declared in the class, the tag write is diffed against the object's zero-initialised state
(the parent has no such member to inherit a value from), so **no tag = the zero value**: a null
`ObjectProperty` for F-49. Measured support for the zero-diff base on this very object:

```
RVehicleSimBatmobile declared properties: 130
Default__RVehicleSimBatmobile: 58 tags, stop=eof, 0 with float value 0.0
```

58 of 130 written, and **not one written tag carries 0.0** — the stream is the non-zero part of the
object, which is exactly what makes "absent" mean zero here and (in the F-33 card) makes "present"
mean a real value. The dense block is unchanged from `chase-07.md`: 0x348 present before, 0x370
present after.

Provenance class: `decoded` (absence ⇒ zeroed default, now with the diff base measured).
Routes tried this pass: (a) 2,975-default sweep — no other default object assigns 0x354 for this
class; (a) archetypes via `objects.jsonl` — 0 tags at 0x354 in all four `SimulationModel` objects;
(a) parent chain — `RVehicleSimCar` 104 B, `Default__RVehicleSimCar` 15 tags, nothing at 0x354;
(a) ini — 0 hits; (b) native — see below, unattributable.

## F-50 · `BattleModeUprightTorqueFactor` — value confirmed, unit STILL UNKNOWN (U-1)

**STATUS: FOUND. 2000.0.** FloatProperty at 0x370, `Default__RVehicleSimBatmobile`; archetypes silent
(re-checked above).
The unit is U-1 below: `MODES.md` says "factor", the magnitude is torque-sized and equals the
sibling `BattleModeUprightMaxTorque` (2000.0 at 0x374). Recorded as shipped, not rescaled.

## F-51 · `BattleModeUprightMaxTorque` — confirmed

**STATUS: FOUND. 2000.0** (engine torque). FloatProperty at 0x374; archetypes silent.

## F-52 · `TransformationRotation` — absence-as-zero, now derived not assumed

**STATUS: FOUND. (0, 0, 0)** — 0° pitch, yaw, roll. Same argument as F-49: no `RotatorProperty` tag
at 0x384, the class declares the field itself, the parent is 104 B, and the zero-diff base is
measured (no 0-valued tag is ever written). A non-zero rotator would have produced a 12-byte
`Rotator` tag; it did not.
Provenance class: `decoded` (absence ⇒ zeroed struct default, diff base measured).

## F-53 · `TransformationTurnOnSpotSpeed` — confirmed

**STATUS: FOUND. 360.0 cm/s** (= 3.6 m/s = 12.96 km/h, arithmetic only). FloatProperty at 0x398;
archetypes silent. *(The first pass's context note "`TurningModeMaxSpeed` 0x2c4 = 300.0" is not
re-checked here — it is context, not the row.)*

## F-54 · `TransformationTurnFactor` — confirmed

**STATUS: FOUND. 45.0** (factor). FloatProperty at 0x39c; archetypes silent.

## F-55 · `BattleModeSteerBiasRate` — value confirmed, unit STILL UNKNOWN (U-2)

**STATUS: FOUND. 3.0.** FloatProperty at 0x3c4; archetypes silent. The **unit** stays open (U-2);
`MODES.md` marks it `undocumented` and row **F-72** (the unit row) is not closed by this pass.

## F-56 · `AirControlPitchTorqueFactorMax` — confirmed

**STATUS: FOUND. 5000.0** (torque gain). FloatProperty at 0x4ac; the archetypes write only the yaw
sibling 0x4a8 = 8000.0, so the shipped car runs pitch 5000 / yaw 8000 — re-checked in `objects.jsonl`.

## U-1 · unit of `BattleModeUprightTorqueFactor` — STILL UNKNOWN

**STATUS: STILL UNKNOWN.** The value 2000.0 is certain (`chase-07.md`'s reading re-derived above).
Nothing on this machine says what one unit of it is, and three routes were run this pass:

* (a) **ini** — 0 hits for `BattleModeUpright*` in BmGame, Engine or any DLC ini.
* (a) **archetypes** — silent, so no authored number with a comment or scale sits anywhere else.
* (b) **native, load *and* store sites** — 312 instructions in `.text` reference displacement 0x370
  and none is attributable: 0x370 is shared by dozens of classes and most hits are
  `movups xmm0,[reg+0x370]` (16-byte vector reads), stack-frame arithmetic
  (`sub dword ptr [rsp+0x370], esi`) or `jmp qword ptr [rax+0x370]` vtable slots. No site loads a
  2000.0 constant into this displacement, so there is no scale factor to read either.

So the magnitude is decoded and the scale is not; a port must treat it as shipped (2000.0) and not
invent a unit.

## U-2 · unit of `BattleModeSteerBiasRate` — STILL UNKNOWN

**STATUS: STILL UNKNOWN.** 3.0 is decoded; the scale is not stated by any file (F-72). Routes tried
this pass: (a) ini 0 hits; (a) archetypes silent; (b) 134 instructions reference 0x3c4, all
unattributable (same low-offset collision; the only RIP-relative float in a window is a 0.2 compare
in unrelated code, `comiss xmm0,[rbx+0x3c4]` at RVA 0x1cbee1). No conversion constant exists to read.

## The native route, in the form that could have worked

The first pass used `chase04_native.py`, which only finds **immediate** stores and reported "9 / 9 / 5
store-form hits, unattributable". This pass searched **loads as well as stores**, required the
disassembly to end exactly on the displacement, and resolved every RIP-relative float in the window
(`chase2_native2.py`):

| offset | instruction sites | RIP-relative constants in the windows |
|---|---|---|
| 0x370 (F-50) | 312 | none that is this field's (1.0 / 2.0 / 40.0 / 0.75 appear near unrelated `movups` copies) |
| 0x398 (F-53) | 252 | a `mulps … 0.017453` (deg↔rad) at RVA 0x4f4d3 on unrelated code |
| 0x3c4 (F-55) | 134 | 0.2 in a `comiss` at 0x1cbee1 |
| 0x354 (F-49) | 32 | none |
| 0x384 (F-52) | 90 | none |

Conclusion unchanged from `chase-07.md`, but now for a measured reason: these are class-layout
offsets too small to be unique, the executable is stripped of property names, and **no site loads a
constant that matches a card value** (2000 / 5000 / 360 / 45 / 3). The native route contributes no
evidence and no unit — recorded, not used.

## What this changes

1. F-49 and F-52 move from "absence-as-zero inference" to a **derived** absence: the diff base is
   measured (58 of 130 properties written, zero 0-valued tags) and the parent class is 104 bytes,
   so no inherited value can exist at 0x354/0x384. Both rows can ship as `RESOLVED` with
   "declared, never assigned (null)" and "(0,0,0)".
2. F-50 and F-55 keep their values and stay unit-UNKNOWN; **F-72 remains the open unit row** for
   `BattleModeSteerBiasRate`, and F-50's "factor" label is not upgraded.
3. Nothing in F-49…F-56 is overridden by any of the four shipped cars: the only override in this
   block is `AirControlYawTorqueFactorMax` 8000.0 (not a row).

## Reproduce

```
python Tools/scripts/chase/chase2_defaults.py --offsets 0x354 0x370 0x374 0x384 0x398 0x39c 0x3c4 0x4ac 0x4a8 \
  --json E:/Modding/_BmAKgrab/chase/chase2_defaults_07.json
python Tools/scripts/chase/chase2_native2.py --disp "F-50=0x370" "F-53=0x398" "F-55=0x3c4" \
  --json E:/Modding/_BmAKgrab/chase/chase2_native2_07.json
grep -rn -i -E "TransformationAnimNode|BattleModeUpright|TransformationRotation|BattleModeSteerBiasRate" \
  --include="*.ini" "E:/Games/Batman - Arkham Knight"
```

Evidence files: `E:/Modding/_BmAKgrab/chase/chase2_defaults_07.json`,
`chase2_native2_07.json`.

`FOOTAGE.md`, `chase-07.md`, `GRAB_BACKLOG.md` and every other existing document were **not edited**
(card rule). Nothing was launched, patched, committed, or written under `D:/Games` or `E:/Games`; the
package and the executable were opened read-only. No secret is in this file.
