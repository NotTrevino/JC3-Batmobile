# Chase 06 — F-41 … F-48 (G1-21 sim fields with no archetype value)

Scope: `Research/BatmobileGrab/FOOTAGE.md` §6 rows **F-41 … F-48**, all `UNKNOWN` with reason
`VALUE-NATIVE`. Read-only chasing: no existing document edited, no game launched, nothing
committed.

**Result: 6 of 8 FOUND, 2 STILL UNKNOWN.** The six values live in the class default object
`Default__RVehicleSimBatmobile` in `BmGame.upk` — the layer G1-21 never read (`objects.jsonl` holds
only the 15 `Playable_Batmobile*` packages). `BattleModeFrontThrottle` and `BattleModeRearThrottle`
are genuinely not serialised anywhere, including the default object, and no attributable constant
in the executable was found for them.

| row | field | value | provenance |
|---|---|---|---|
| F-41 | `BattleModeMaxSteering` | **80.0 deg** | decoded |
| F-42 | `BattleModeRearWheelTorquePower` | **0.5** (as shipped; `MODES.md` unit column: engine torque) | decoded |
| F-43 | `BattleModeEngineBrakingFactor` | **0.025** (factor) | decoded |
| F-44 | `BattleModeFrontThrottle` | **STILL UNKNOWN** — no serialised value in any layer | — |
| F-45 | `BattleModeRearThrottle` | **STILL UNKNOWN** — no serialised value in any layer | — |
| F-46 | `BattleModeMaxSpeed` | **1200.0 cm/s** (= 12.0 m/s, 43.2 km/h, unit conversion derived) | decoded |
| F-47 | `BattleModeStopAndTurnAngleMoving` | **90.0 deg** | decoded |
| F-48 | `BattleModeTrailingSteerFactorTurnOnSpot` | **1.0** (factor) | decoded |

Units are the ones `MODES.md` already assigns by field name; nothing is rescaled.

## Evidence (one place for F-41 … F-48)

`E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\BmGame.upk`, export
**`Default__RVehicleSimBatmobile`** (class `RVehicleSimBatmobile`). The walk covers the whole object.

| field | BmSDK offset | tag in the default object |
|---|---|---|
| `BattleModeMaxSteering` | 0x2cc = 716 | FloatProperty `80.0` |
| `BattleModeRearWheelTorquePower` | 0x2d0 = 720 | FloatProperty `0.5` |
| `BattleModeEngineBrakingFactor` | 0x2dc = 732 | FloatProperty `0.02500000037252903` (= float32 0.025) |
| `BattleModeFrontThrottle` | 0x2e4 = 740 | **no tag** |
| `BattleModeRearThrottle` | 0x2e8 = 744 | **no tag** |
| `BattleModeMaxSpeed` | 0x2f0 = 752 | FloatProperty `1200.0` |
| `BattleModeStopAndTurnAngleMoving` | 0x2fc = 764 | FloatProperty `90.0` |
| `BattleModeTrailingSteerFactorTurnOnSpot` | 0x31c = 796 | FloatProperty `1.0` |

Command and output (verbatim):

```
$ python Tools/scripts/chase/chase02_cdo.py --class RVehicleSimBatmobile --json E:/Modding/_BmAKgrab/chase/sim_cdo.json
...
    -- card offsets on RVehicleSimBatmobile:
       BattleModeMaxSteering              @0x02cc  SERIALISED 80.0
       BattleModeRearWheelTorquePower     @0x02d0  SERIALISED 0.5
       BattleModeEngineBrakingFactor      @0x02dc  SERIALISED 0.02500000037252903
       BattleModeFrontThrottle            @0x02e4  absent
       BattleModeRearThrottle             @0x02e8  absent
       BattleModeMaxSpeed                 @0x02f0  SERIALISED 1200.0
       BattleModeStopAndTurnAngleMoving   @0x02fc  SERIALISED 90.0
       BattleModeTrailingSteerFactorTurnOnSpot @0x031c  SERIALISED 1.0
wrote E:/Modding/_BmAKgrab/chase/sim_cdo.json
```

Offset identities come from `BMSDK_OFFSETS.json` → `classes.RVehicleSimBatmobile.properties`:
0x2cc `BattleModeMaxSteering`, 0x2d0 `BattleModeRearWheelTorquePower`, 0x2d4 `…LatSlipScale`,
0x2d8 `…LongSlipScale`, 0x2dc `…EngineBrakingFactor`, 0x2e0 `…TurnOnSpotTorqueFactor`,
0x2e4 `…FrontThrottle`, 0x2e8 `…RearThrottle`, 0x2ec `…ThrottleSpeed`, 0x2f0 `…MaxSpeed`,
0x2f4 `…DriveForceFactor`, 0x2f8 `…StopAndTurnAngleStationary`, 0x2fc `…StopAndTurnAngleMoving`,
0x300 `…SteerAngleFactor`, 0x31c `…TrailingSteerFactorTurnOnSpot`, 0x320 `…TrailingSteerFactorMoving`.

**Control — the absence of 0x2e4/0x2e8 is real, not a parse failure.** The default object's tag
stream is dense in exactly this block:

```
0x2b0 BoostDurationDonut                6.0
0x2c4 TurningModeMaxSpeed               300.0
0x2cc BattleModeMaxSteering             80.0
0x2d0 BattleModeRearWheelTorquePower    0.5
0x2d4 BattleModeLatSlipScale            4.0
0x2d8 BattleModeLongSlipScale           10.0
0x2dc BattleModeEngineBrakingFactor     0.02500000037252903
0x2e0 BattleModeTurnOnSpotTorqueFactor  0.30000001192092896
0x2ec BattleModeThrottleSpeed           5.0
0x2f0 BattleModeMaxSpeed                1200.0
0x2f4 BattleModeDriveForceFactor        75.0
0x2f8 BattleModeStopAndTurnAngleStationary 60.0
0x2fc BattleModeStopAndTurnAngleMoving   90.0
0x300 BattleModeSteerAngleFactor         2.5
0x314 BMFrontWheelMaxDroop               40.0
0x318 BMRearWheelMaxDroop                40.0
0x31c BattleModeTrailingSteerFactorTurnOnSpot 1.0
0x320 BattleModeTrailingSteerFactorMoving -0.5
0x324 BattleModeDrivingForceZOffset      10.0
0x328 CurrentBoostTimer                  1.0
```

The reader sees every field on both sides of 0x2e4/0x2e8 (0x2e0 before, 0x2ec after) — those two
are simply not written.

**The archetype does not override the ones that are present.** The shipped `SimulationModel` object
in `Playable_Batmobile_SF` (`Vehicle.Batmobile`, class `RVehicleSimBatmobile`, 37 tags) serialises
this block densely too: 0x2c4, 0x2d4, 0x2d8, 0x2e0, 0x2ec, 0x2f4, 0x2f8, 0x300, 0x304, 0x308,
0x30c, 0x310, 0x318, 0x320, 0x324, 0x32c. It does **not** write 0x2cc, 0x2d0, 0x2dc, 0x2e4,
0x2e8, 0x2f0, 0x2fc, 0x31c, so the class default values above are the ones the sim inherits.
(None of the four `SimulationModel` objects carries any of the eight offsets.)

**Rejected lookalike (class-scoped offsets).** A naive offset search over `objects.jsonl` finds
`0x2e4 = 2.0` and `0x2e8 = 1.0` (plus `0x2dc = 0.2`, `0x2e0 = 0.1`, `0x2ec = 0.7`, `0x2fc = 0.8`)
under `VEH_Player` — but those tags belong to `AkPlayerVehicleSoundInfo`, an audio object whose own
layout reuses the same offsets. They are **not** the sim's throttles and are not adopted. The same
trap makes the executable scan unusable for these offsets (below).

## F-41 · `BattleModeMaxSteering`

**STATUS: FOUND. 80.0 deg.** `Default__RVehicleSimBatmobile`, FloatProperty at 0x2cc = `80.0`;
unit deg per `MODES.md`. Not overridden by any shipped `SimulationModel`.
Provenance: `decoded`. Routes tried: (1) class default object — found; (2)(3)(4) not needed.

## F-42 · `BattleModeRearWheelTorquePower`

**STATUS: FOUND. 0.5.** Same object, FloatProperty at 0x2d0 = `0.5`. `MODES.md` records the unit
column as "engine torque"; the field name says *power*, so **the unit is not settled by the files**
— the number 0.5 is shipped as-is and is not rescaled or reinterpreted.
Provenance: `decoded`. Routes tried: (1) found.

## F-43 · `BattleModeEngineBrakingFactor`

**STATUS: FOUND. 0.025** (dimensionless factor). Same object, FloatProperty at 0x2dc =
`0.02500000037252903`, i.e. the float32 nearest 0.025. Provenance: `decoded`. Routes tried: (1) found.

## F-44 · `BattleModeFrontThrottle`

**STATUS: STILL UNKNOWN — no serialised value exists.** Absent from
`Default__RVehicleSimBatmobile` (control: 0x2e0 and 0x2ec on either side are present) and from all
four `SimulationModel` archetypes.
Route 2 was attempted and is **inconclusive by construction**: the direct-store scan
(`chase04_native.py 0x2e4` → `17 store-form hit(s)`; `0x2e8` → `26`) finds many
`movss [reg+0x2e4], xmm` sites, but 0x2e4 is a small,
common field offset shared by many classes, the exe is stripped, and the exe contains no
`BattleModeFrontThrottle` string — so no store can be attributed to `RVehicleSimBatmobile`.
Route 3 is not applicable (a throttle factor written per tick is not a measurable frame quantity);
route 4 was not used and could not outrank a file value (R4).
**What is proven:** the field has no default in the shipped packages, so a port must not claim a
number for it; the runtime value is whatever the throttle code writes, which this chase did not
identify.

## F-45 · `BattleModeRearThrottle`

**STATUS: STILL UNKNOWN — no serialised value exists.** Same evidence and same limits as F-44
(absent at 0x2e8, archetypes silent, 0x2e8 stores in the exe unattributable). The only 1.0/2.0
values found at these offsets belong to `AkPlayerVehicleSoundInfo` (rejected lookalike, above).

## F-46 · `BattleModeMaxSpeed`

**STATUS: FOUND. 1200.0 cm/s.** Same object, FloatProperty at 0x2f0 = `1200.0`; unit cm/s per
`MODES.md`. In SI that is 12.0 m/s = 43.2 km/h (arithmetic conversion only, no measurement).
Provenance: `decoded`. Routes tried: (1) found.

## F-47 · `BattleModeStopAndTurnAngleMoving`

**STATUS: FOUND. 90.0 deg.** Same object, FloatProperty at 0x2fc = `90.0`. Provenance: `decoded`.
Routes tried: (1) found. Note the stationary sibling 0x2f8 is 60.0 deg in the same default object
(context, not part of the row).

## F-48 · `BattleModeTrailingSteerFactorTurnOnSpot`

**STATUS: FOUND. 1.0** (factor). Same object, FloatProperty at 0x31c = `1.0`. The moving sibling
0x320 is `-0.5` (context). Provenance: `decoded`. Routes tried: (1) found.

---

## Why G1-21 missed these, and what it means for FOOTAGE.md (read-only here)

`grab_modes.py` compares the BmSDK declaration inventory against `objects.jsonl`, and
`objects.jsonl` only covers the 15 `Playable_Batmobile*` packages. `Default__RVehicleSimBatmobile`
lives in `BmGame.upk`, which no G1 reader opened — the same gap that chase-02 and chase-04 closed
for the camera and vehicle classes.

Suggested status change (not applied): F-41, F-42, F-43, F-46, F-47, F-48 → `RESOLVED` /
`FILE-VALUE`; F-44, F-45 → `UNKNOWN` with the reason narrowed from `VALUE-NATIVE` to "no shipped
default; runtime throttle factor, exe store unattributable".

## Limits / UNKNOWNs of this chase

1. F-44/F-45 are the only rows here without a value; that is a property of the data (the field was
   never written in any package), not of the reader.
2. F-42's unit is ambiguous between the name ("power") and `MODES.md` ("engine torque"); the
   number is unaffected.
3. The executable scan cannot attribute any of these stores (small offsets, no symbols, no property
   strings in the exe); it is recorded as attempted, not as evidence.
4. Class-default values are the inherited defaults; the shipped archetypes do not override any of
   the six found fields, which was checked offset by offset with the neighbouring block as control.
5. Extracted decodes: `E:/Modding/_BmAKgrab/chase/sim_cdo.json`. Script:
   `Tools/scripts/chase/chase02_cdo.py --class RVehicleSimBatmobile` (and `--scan`), and
   `Tools/scripts/chase/chase04_native.py` for the exe scan. Nothing was written under the game
   folder; the game was not launched.
