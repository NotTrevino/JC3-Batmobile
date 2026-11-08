# Chase 07 — F-49 … F-56 (G1-21 sim fields with no archetype value)

Scope: `Research/BatmobileGrab/FOOTAGE.md` rows **F-49 … F-56**, all `UNKNOWN` with reason
`VALUE-NATIVE`. Read-only chasing: no existing document edited, no game launched, nothing
committed, nothing written under the game folder.

**Result: 8 of 8 FOUND, 0 STILL UNKNOWN.** Six values are serialised in the class default object
`Default__RVehicleSimBatmobile` in `BmGame.upk` — the same layer chase-02/04/06 opened and G1-21
never read (its `objects.jsonl` holds only the 15 `Playable_Batmobile*` packages). The other two
(`TransformationAnimNode`, `TransformationRotation`) are **genuinely absent from the default
object**, and an absent property in a cooked default object means *the zero value was in place at
cook time*: a null object reference and a `(0,0,0)` Rotator. Those are values, not gaps — the
evidence for each is the dense tag block around it plus the absence of any override in the four
shipped `SimulationModel` archetypes.

| row | field | value | provenance |
|---|---|---|---|
| F-49 | `TransformationAnimNode` | **none — null `AnimNodeSequence` reference** (no tag in the default object, no tag in any archetype, and no `AnimNodeSequence` is wired to the sim) | decoded |
| F-50 | `BattleModeUprightTorqueFactor` | **2000.0** (unit as `MODES.md`: factor — see the note, the number is torque-sized) | decoded |
| F-51 | `BattleModeUprightMaxTorque` | **2000.0** (engine torque) | decoded |
| F-52 | `TransformationRotation` | **0, 0, 0** (Rotator = 0° pitch / yaw / roll) | decoded |
| F-53 | `TransformationTurnOnSpotSpeed` | **360.0 cm/s** (= 3.6 m/s, 12.96 km/h — arithmetic only) | decoded |
| F-54 | `TransformationTurnFactor` | **45.0** (factor) | decoded |
| F-55 | `BattleModeSteerBiasRate` | **3.0** (unit undocumented — `MODES.md`, and F-72 stays open) | decoded |
| F-56 | `AirControlPitchTorqueFactorMax` | **5000.0** (engine torque gain) | decoded |

Units are the ones `MODES.md` assigns by field name; nothing is rescaled. `decoded` is R4's class
for a value read out of a shipped file; no row here is `derived`, `class` or `assumed`.

## Evidence (one place for all eight)

`E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\BmGame.upk`, export **129779
`Default__RVehicleSimBatmobile`** (class `RVehicleSimBatmobile`, 724 B, **58 tags**, walk stops at
`eof`). Offsets are the BmSDK absolute ones declared in `Research/BatmobileGrab/BMSDK_OFFSETS.json`
→ `classes.RVehicleSimBatmobile.properties` (0x354 = 852, 0x370 = 880, 0x374 = 884, 0x384 = 900,
0x398 = 920, 0x39c = 924, 0x3c4 = 964, 0x4ac = 1196).

The tag block around the two absences is dense, so "absent" is a property of the file, not of the
parse:

```
0x0340  1000.0
0x0344  40.0
0x0348  40.0
0x0354  absent            <- F-49 TransformationAnimNode
0x0370  2000.0            <- F-50
0x0374  2000.0            <- F-51
0x0384  absent            <- F-52 TransformationRotation
0x0390  2000.0            (TransformationTurnTorqueFactor; archetypes override to 3000)
0x0394  8000.0            (TransformationTurnDecelTorqueFactor; archetypes override to 24000)
0x0398  360.0             <- F-53
0x039c  45.0              <- F-54
0x03b0  DriveMode 'None'  (ByteProperty, the one named tag in this block)
0x03b8  1.0
0x03c0  0.3
0x03c4  3.0               <- F-55
...
0x04a8  5000.0            (AirControlYawTorqueFactorMax; archetypes override to 8000)
0x04ac  5000.0            <- F-56
0x04b0  2000.0            (AirControlYawTorqueFactorMin)
0x04b4  3000.0            (AirControlPitchTorqueFactorMin)
0x04b8  1.5               (AirControlInterpTime)
```

Command and output (verbatim summary lines):

```
$ python Tools/scripts/chase/chase07_cdo.py --dump --json E:/Modding/ArkhamKnight/_grab/chase/sim_cdo_07.json
package BmGame.upk: version 863, licensee 32995, 84813 names, 3268 imports, 177031 exports
=== Default__RVehicleSimBatmobile (export 129779, class RVehicleSimBatmobile, 724 B)
    walked 58 tags, stop=eof
    -- F-49..F-56 offsets on RVehicleSimBatmobile:
       TransformationAnimNode             @0x0354  absent
       BattleModeUprightTorqueFactor      @0x0370  SERIALISED 2000.0 (FloatProperty)
       BattleModeUprightMaxTorque         @0x0374  SERIALISED 2000.0 (FloatProperty)
       TransformationRotation             @0x0384  absent
       TransformationTurnOnSpotSpeed      @0x0398  SERIALISED 360.0 (FloatProperty)
       TransformationTurnFactor           @0x039c  SERIALISED 45.0 (FloatProperty)
       BattleModeSteerBiasRate            @0x03c4  SERIALISED 3.0 (FloatProperty)
       AirControlPitchTorqueFactorMax     @0x04ac  SERIALISED 5000.0 (FloatProperty)
wrote E:/Modding/ArkhamKnight/_grab/chase/sim_cdo_07.json
```

(Version/licensee/name counts are the package header; the exact numbers are in the json.)

**The archetypes do not override any of the eight.** All four shipped `SimulationModel` objects
(`Playable_Batmobile_SF`, `_MK2_SF`, `_Joker_SF`, `_Funhouse_SF`; class `RVehicleSimBatmobile`,
2,328 B, 37 tags each) were checked offset by offset from `objects.jsonl`: none carries 0x354,
0x370, 0x374, 0x384, 0x398, 0x39c, 0x3c4 or 0x4ac, while 0x4a8 (`AirControlYawTorqueFactorMax`)
*is* present at 8000.0 in all four — a positive control that the block is serialised where it is
overridden and left at the class default where it is not.

**No other default object carries these offsets for this class.** `chase07_cdo.py --scan` over the
`Default__*Vehicle*/Batmobile*` exports finds the same offsets on other classes only (e.g.
`Default__RVehicleBehaviour_Wander` 0x354 = 0.0, `Default__RBatmobileWinchProjectile` 0x370 = 8000.0,
0x374 = 24.0) — class-scoped offsets, the lookalike trap chase-06 recorded, and none of them is an
`RVehicleSimBatmobile`.

## F-49 · `TransformationAnimNode`

**STATUS: FOUND. null reference — no `AnimNodeSequence` is assigned.**
Evidence: no tag at 0x354 in `Default__RVehicleSimBatmobile` (58 tags, 0x348 before and 0x370 after
both present), and no tag at 0x354 in any of the four `SimulationModel` archetypes. A cooked default
object serialises every property whose value differs from the zeroed default, so a non-null object
reference would appear as an `ObjectProperty` tag; it does not. The three `AnimNodeSequence` objects
that exist in the Batmobile packages (`Playable_Batmobile_SF`, `_MK2_SF`, `_Joker_SF`, one each,
default-named) are reachable from no sim object.
Meaning for the port: **transformation is not driven by this member in the shipped car** — an anim
node kept at null means nothing to translate; the field is declared and unused.
Provenance: `decoded`. Routes tried: (1) class default object + archetype scan + AnimNodeSequence
inventory — found (as null). (2) exe: `chase04_native.py 0x354` → **9 store-form hit(s)**
(`movss [reg+0x354], xmm` at file offsets 0x0088a579, 0x00dac032, …) — not adopted: 0x354 is a small
offset shared by dozens of classes, the exe is stripped and carries no `TransformationAnimNode`
string, so no store can be attributed. (3)(4) not applicable (an object reference is not measurable
from footage, and no published source outranks a file value — R4).
Residual risk: BmScript or a level script could assign the node at runtime; nothing in the shipped
packages does.

## F-50 · `BattleModeUprightTorqueFactor`

**STATUS: FOUND. 2000.0.** `Default__RVehicleSimBatmobile`, FloatProperty at 0x370 = `2000.0`; not
overridden by any of the four archetypes.
The number is recorded exactly as shipped. **The unit is not settled by the files**: `MODES.md`'s
unit column says "factor" while the magnitude is torque-sized and identical to
`BattleModeUprightMaxTorque` (2000.0). The field name says *factor*; the value is not rescaled or
reinterpreted here, and a port must not invent the scale.
Provenance: `decoded`. Routes tried: (1) found. (2) not claimed: `0x370` has 9 store sites, all
unattributable for the same reason as F-49.

## F-51 · `BattleModeUprightMaxTorque`

**STATUS: FOUND. 2000.0** (engine torque; `MODES.md` unit column). Same object, FloatProperty at
0x374 = `2000.0`; archetypes silent.
Provenance: `decoded`. Routes tried: (1) found.

## F-52 · `TransformationRotation`

**STATUS: FOUND. 0, 0, 0** (UE3 Rotator: pitch, yaw, roll — 0° on all three axes).
Evidence: no `StructProperty` tag at 0x384 in `Default__RVehicleSimBatmobile` (dense block: 0x374
before, 0x390 after) and none in the four archetypes. The cooked default object omits a struct whose
bytes equal zero, so the cooked value is the zeroed rotator. This is the same inference as F-49, and
it is the only reading the data supports: a non-zero rotator would have produced a 12-byte
`Rotator` tag.
Provenance: `decoded` (absence ⇒ zeroed struct default, reasoned above). Routes tried: (1) found.
(2) `chase04_native.py 0x384` → **5 store-form hit(s)** (0x001701a1, 0x00788bfd, 0x0088a88c,
0x00a1db6a, 0x0158a9ea); a Rotator is written as three consecutive ints, not one `movss`, so these
are other classes' float fields at the same displacement — recorded as attempted, not evidence.

## F-53 · `TransformationTurnOnSpotSpeed`

**STATUS: FOUND. 360.0 cm/s.** `Default__RVehicleSimBatmobile`, FloatProperty at 0x398 = `360.0`;
archetypes silent, so the class default is what runs. In SI that is 3.6 m/s = 12.96 km/h
(arithmetic conversion only, no measurement). Context from the same object, not a rule and not a
relationship the files state: `TurningModeMaxSpeed` at 0x2c4 is 300.0 cm/s in the default object
and 600.0 cm/s in all four archetypes.
Provenance: `decoded`. Routes tried: (1) found. (3) not needed: a file value outranks footage (R4),
and a turn-on-spot rate is not separable from steering input in the captures.

## F-54 · `TransformationTurnFactor`

**STATUS: FOUND. 45.0** (factor, `MODES.md` unit column). Same object, FloatProperty at 0x39c =
`45.0`; archetypes silent.
Provenance: `decoded`. Routes tried: (1) found.

## F-55 · `BattleModeSteerBiasRate`

**STATUS: FOUND. 3.0.** Same object, FloatProperty at 0x3c4 = `3.0`; archetypes silent. **The unit
stays undocumented** — `MODES.md` records it as `undocumented`, and F-72 (the unit row) is not
closed by this chase: a number whose scale is unknown must not be treated as a buildable value
(R4). What is proven here is only that the shipped default is 3.0, next to `FrontWheelSteerPct`
0x3b8 = 1.0 and 0x3c0 = 0.3 in the same block (context).
Provenance: `decoded`. Routes tried: (1) found — the *number*; (2) not attempted for the unit (a
unit is not a constant in the exe); (3) the rate is a per-tick blend, not a visible frame quantity.

## F-56 · `AirControlPitchTorqueFactorMax`

**STATUS: FOUND. 5000.0** (engine torque gain, `MODES.md`). Same object, FloatProperty at 0x4ac =
`5000.0`. The archetypes do **not** write it, while the yaw sibling 0x4a8 *is* written at 8000.0 in
all four — so the shipped car runs pitch 5000 / yaw 8000 from the same block, and the pitch cap is
the class default.
Context from the same block (not part of the row): `AirControlYawTorqueFactorMin` 0x4b0 = 2000.0,
`AirControlPitchTorqueFactorMin` 0x4b4 = 3000.0, `AirControlInterpTime` 0x4b8 = 1.5 s.
Provenance: `decoded`. Routes tried: (1) found. (3) a torque gain is not measurable from the
captures (the ramp air time 1.212 s in FOOTAGE.md is a different quantity).

---

## Why G1-21 missed these, and what it means for FOOTAGE.md (read-only here)

`grab_modes.py` compares the BmSDK declaration inventory against `objects.jsonl`, which covers only
the 15 `Playable_Batmobile*` packages. `Default__RVehicleSimBatmobile` lives in `BmGame.upk`, which
no G1 reader opened — the same gap chase-02, chase-04 and chase-06 closed for other classes. The
whole F-49…F-56 block is in that one object; six fields are serialised there with a value, and two
are serialised as the zero value (no tag).

Suggested status change (not applied): F-49…F-56 → `RESOLVED` / `FILE-VALUE`, with F-49 recorded as
"declared, never assigned (null reference)", F-52 as "0,0,0", and F-55's *unit* left open (F-72
unchanged).

## Limits / UNKNOWNs of this chase

1. **Absence-as-zero** (F-49, F-52) rests on the standard cooked-default-object behaviour: every
   property whose value differs from the zeroed default is serialised, so a field with no tag held
   the zero value when the object was cooked. The dense neighbourhood is the control. The residual
   risk is a runtime assignment (BmScript/level script), not a file value — nothing in the shipped
   packages assigns either field.
2. **F-50's unit.** The value 2000.0 is certain; whether `MODES.md`'s "factor" is right (it is
   torque-sized and equal to the max-torque sibling) is not settled by the files. Not rescaled.
3. **F-55's unit** is undocumented (F-72). Only the number is proven.
4. **The exe scan is not evidence** for any row: offsets 0x354/0x370/0x384 are small, shared by
   many classes, the exe is stripped and contains no property-name strings (9 / 9 / 5 store-form
   hits respectively, unattributable).
5. Extracted decode: `E:/Modding/ArkhamKnight/_grab/chase/sim_cdo_07.json`. Script:
   `Tools/scripts/chase/chase07_cdo.py --dump | --scan`. Nothing was written under the game
   folder, the game was not launched, and no existing document was edited.
