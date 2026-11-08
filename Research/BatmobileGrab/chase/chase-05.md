# Chase 05 - F-33…F-40 (`RVehicleBatmobileBase` battle-mode sizes/speeds, ramp force, impact shake; `RVehicleSimBatmobile` curve and flag)

Rows: `Research/BatmobileGrab/FOOTAGE.md` §6, F-33…F-40, all eight `UNKNOWN` with reason
`VALUE-NATIVE`. Read-only: no existing doc, package or game file was modified. The writes are two
scripts under `Tools/scripts/chase/`, the extracted evidence under `E:\Modding\_BmAKgrab\chase\`,
and this file. No game was launched, nothing was committed.

**Result: 0 of 8 found.** All eight stay `UNKNOWN`, and the reason is now measured three ways:
no archetype in the install tags them, the one package that names them is the class **schema**
with **no CDO override**, and the executable has **no initialiser for either class**. There is
no number on this machine to copy - and one of the eight is not a number at all (F-39 is a curve,
F-40 a bool, so "the value" for those would be a list of points and a flag).

Tools used (both already in the repo from chase-03, reused as-is):

| tool | role here |
|---|---|
| `Tools/scripts/chase/chase_g1_values.py scan` | PE section table + displacement-store scan (`C7` `mov r/m32, imm32`, `F3 0F 11` `movss`, `mod=10` → disp32) over `BatmanAK.exe`, per field offset |
| `Tools/scripts/chase/chase_g1_values.py dump <rva> <len>` | hex+ASCII of a code window with the offset stores it contains |
| `Tools/scripts/chase/chase_namescan_b.py` (new) | one pass over all **3,266** `.upk` in `BmGame\CookedPCConsole` (11.71 GB) for the eleven names below |

Evidence files: `E:\Modding\_BmAKgrab\chase\namescan_b.json` (package scan),
`E:\Modding\_BmAKgrab\chase\g1_chase_native.json` (the displacement scan of chase-03, same reader).

---

## The five measurements that decide all eight rows

### 1. No cooked archetype carries any of them

`objects.jsonl` (20,128 exports over the 20 `Playable_Batmobile*` packages, the four Batmobile
archetypes included) has **0 tags** named `BattleModeHeight`, `JumpRampUpwardForce`,
`ImpactShakeAbandonedVehicleFactor`, `ImpactShakeDestructiblesFactor`, `ImpactShakeCoolDown`,
`BattleModeSpeedDelta`, `TurnOnSpotSteeringSpeedCurve`, `BattleModeMoving` - and also 0 for the
three controls `BattleModeWidth`, `BattleModeLength`, `ImpactShakeVehicleFactor`. MODES.md's
"not serialised in any shipped archetype" is confirmed for the eight.

### 2. Exactly one package in the whole install names them - as schema, not as values

```
> python Tools/scripts/chase/chase_namescan_b.py
{"files": 3266, "bytes": 11709428859, "seconds": 285.9, "hit_count": 1}
HIT GlobalPersistentCookerData.upk {'ImpactShakeCoolDown': 1, 'ImpactShakeVehicleFactor': 1,
 'ImpactShakeAbandonedVehicleFactor': 1, 'ImpactShakeDestructiblesFactor': 1,
 'BattleModeWidth': 1, 'BattleModeLength': 1, 'BattleModeHeight': 1, 'JumpRampUpwardForce': 1,
 'BattleModeSpeedDelta': 1, 'BattleModeMoving': 1, 'TurnOnSpotSteeringSpeedCurve': 1}
```

`GlobalPersistentCookerData.upk` (109,590,691 B) carries each name exactly once, as the
class-qualified **typed schema record** the cooker writes for every declared property:

| row | record in the package | type | file offset |
|---|---|---|---|
| F-33 | `FloatProperty BmGame.RVehicleBatmobileBase:BattleModeHeight` | float | 0x5424F2 |
| F-34 | `FloatProperty BmGame.RVehicleBatmobileBase:JumpRampUpwardForce` | float | 0x54279F |
| F-35 | `FloatProperty BmGame.RVehicleBatmobileBase:ImpactShakeAbandonedVehicleFactor` | float | 0x52DBCC |
| F-36 | `FloatProperty BmGame.RVehicleBatmobileBase:ImpactShakeDestructiblesFactor` | float | 0x52DC81 |
| F-37 | `FloatProperty BmGame.RVehicleBatmobileBase:ImpactShakeCoolDown` | float | 0x52DA5B |
| F-38 | `FloatProperty BmGame.RVehicleBatmobileBase:BattleModeSpeedDelta` | float | 0x544214 |
| F-39 | `StructProperty BmGame.RVehicleSimBatmobile:TurnOnSpotSteeringSpeedCurve` | FInterpCurveFloat | 0xCC1C62 |
| F-40 | `BoolProperty BmGame.RVehicleSimBatmobile:BattleModeMoving` | bool | 0xCC0ABD |

The types are the ones the rows claim, from the file: `TurnOnSpotSteeringSpeedCurve` really is a
**struct** property, `BattleModeMoving` a **bool**.

### 3. The class default object does not override any of them

The same package holds the class's CDO name stream - 1,424 `…BmGame.Default__RVehicleBatmobileBase:…`
records (e.g. `SkeletalMeshComponent BmGame.Default__RVehicleBatmobileBase:SVehicleMesh`). For all
eleven names below, the CDO-qualified form occurs **0** times:

```
BattleModeHeight                   CDO-qual 0
JumpRampUpwardForce                CDO-qual 0
ImpactShakeAbandonedVehicleFactor  CDO-qual 0
ImpactShakeDestructiblesFactor     CDO-qual 0
ImpactShakeCoolDown                CDO-qual 0
BattleModeSpeedDelta               CDO-qual 0
TurnOnSpotSteeringSpeedCurve       CDO-qual 0   (sim class)
BattleModeMoving                   CDO-qual 0   (sim class)
```

**Control, and why this alone is not the proof:** `ImpactShakeVehicleFactor` (0x1CC8, the
neighbour of F-35/F-36/F-37) is serialised **1.5** in all four archetypes (MODES.md) and it too has
0 CDO records - its value lives in the archetype tag, not the CDO. So a missing CDO record only
means "no CDO override"; the value would then have to come from an archetype tag, and measurement 1
shows it does not. For these eight both sources are empty.

### 4. The executable has no initialiser for either class

A compiled default shows up as an immediate store at the field's displacement. The test is a
*class-mate whose shipped value is known* - if the class were initialised in code, it would set it:

```
0x1CC8 ImpactShakeVehicleFactor (1.5 in all four archetypes)   immediate stores: 0
0x1CF8 VehicleShovingTorque     (10000 in all four)            immediate stores: 0
0x1FE0 PMDodgeForce             (10000)                        immediate stores: 0
0x1FE4 PMDodgeDuration          (0.15)                         immediate stores: 0
```

**Zero** at every one of them, in the whole 55,101,440-byte image. Whatever writes
`ImpactShakeVehicleFactor` = 1.5, it is the data stream, not code - so this class is never
initialised by a compiled constructor, and none of the displacement hits in measurement 5 can be
its default.

### 5. The displacement hits that exist cannot be bound to these classes

`MODES.md`'s own rule applies: the same offset means different members in different classes, and
0x0268/0x0294 are low offsets that thousands of structs share. What the scan found:

| row | offset | stores | what they are |
|---|---|---:|---|
| F-33 `BattleModeHeight` | 0x199C | 1 | `mov dword [r?+199Ch], imm` at RVA 0x1A17F5 whose bytes read as float `-9.01e27` - a pointer-sized constant, not a height |
| F-34 `JumpRampUpwardForce` | 0x1A60 | **0** | nothing to read |
| F-35 `ImpactShakeAbandonedVehicleFactor` | 0x1CCC | **0** | nothing to read |
| F-36 `ImpactShakeDestructiblesFactor` | 0x1CD0 | 1 | a `movss` at RVA 0xAD403 from a register (no immediate) |
| F-37 `ImpactShakeCoolDown` | 0x1CD4 | 3 | `movss` at 0x6B3C2/0xAD677/0xAD777, all from registers |
| F-38 `BattleModeSpeedDelta` | 0x1EB4 | **0** | nothing to read |
| F-39 `TurnOnSpotSteeringSpeedCurve` | 0x0268 | 34 | mixed 0.0/1.0/int ones - a curve is a TArray + mode, not a storable immediate |
| F-40 `BattleModeMoving` | 0x0294 | 25 | mixed 0.0/0.5/1.0/int ones - a bool is a byte in a bitfield, not an imm32 |
| *control* `BattleModeWidth` | 0x1990 | 1 | `movss` from a register |
| *control* `BattleModeLength` | 0x1994 | **0** | - |
| *control* `ImpactShakeVehicleFactor` | 0x1CC8 | **0** | its 1.5 comes from the package (see 4) |

The controls are the argument: `BattleModeWidth`/`BattleModeLength` are class-mates declared next
to F-33 and they behave exactly like it (0-1 register stores), so the store counts carry no value
information at all.

---

## Row by row

### F-33 · `BattleModeHeight` (0x199C, `float`, cm) - **STILL UNKNOWN**

* **Value:** none from this machine.
* **Provenance:** would be `decoded` (a tag value) or `derived` (a mesh measurement); neither exists.
* **Evidence:** schema record at `GlobalPersistentCookerData.upk` 0x5424F2 (`FloatProperty …:BattleModeHeight`);
  CDO-qualified 0; **0** archetype tags in 20,128 objects; 1 immediate store at RVA 0x1A17F5 whose
  float reading is `-9.01e27` (not a height); class-mate `BattleModeWidth` behaves identically.
* **Routes tried:** (1) archetypes + CDO - negative, measured; (1b) all 3,266 packages - schema
  only; (2) exe displacement scan - 1 unbindable store; (3) footage - a battle-mode *height*
  (cm) needs a calibrated reference in frame and there is none, and the capture that shows battle
  mode (Battlemode entry/movement/boost, 1,096 f / 40.042 s) has no measuring stick; (4) web - 0
  results.

### F-34 · `JumpRampUpwardForce` (0x1A60, `float`, engine force) - **STILL UNKNOWN**

* **Value:** none. The *behaviour* is real and already measured - ramp jumps give an air time of
  **1.212 s mean** (1.183-1.251 s, three clips, PTS-based; FOOTAGE.md §3) - but an engine force has
  no bridge to that air time (mass and gravity conversion are undocumented), so the measurement
  cannot be turned into this field's number.
* **Provenance:** would be `decoded`; none found.
* **Evidence:** schema record at 0x54279F; CDO 0; 0 archetype tags; **0** immediate stores at
  0x1A60 in the image.
* **Routes tried:** (1) 1b negative; (2) 0 stores; (3) the three air-steer clips (189/202/267
  frames, 6.388/7.153/8.882 s) prove the field is live but cannot give a force; (4) web - 0 results.

### F-35 · `ImpactShakeAbandonedVehicleFactor` (0x1CCC, `float`, factor) - **STILL UNKNOWN**

* **Value:** none. Note the *shape* of the block: the class serialises `ImpactShakeForceFactor`
  0x1CC4 = **0.01333** and `ImpactShakeVehicleFactor` 0x1CC8 = **1.5** in all four archetypes, then
  skips exactly 0x1CCC/0x1CD0/0x1CD4 - the three rows F-35/F-36/F-37.
* **Provenance:** would be `decoded`; none found.
* **Evidence:** schema record at 0x52DBCC; CDO 0; 0 tags; **0** stores at 0x1CCC.
* **Routes tried:** 1, 1b, 2 (0 stores), 3 (a screen-shake multiplier is not visible), 4.

### F-36 · `ImpactShakeDestructiblesFactor` (0x1CD0, `float`, factor) - **STILL UNKNOWN**

* **Value:** none.
* **Provenance:** would be `decoded`; none found.
* **Evidence:** schema record at 0x52DC81; CDO 0; 0 tags; 1 `movss` at RVA 0xAD403 with no
  immediate, and the class has no initialiser (control 0x1CC8 = 0 stores).
* **Routes tried:** 1, 1b, 2, 3, 4 - all negative.

### F-37 · `ImpactShakeCoolDown` (0x1CD4, `float`, s) - **STILL UNKNOWN**

* **Value:** none. This is the one of the three that a Q-1 probe could bound cheaply (shake
  re-trigger rate when scraping several cars in a row), but a probe is not a file value and this
  card is a file chase.
* **Provenance:** would be `decoded`; none found.
* **Evidence:** schema record at 0x52DA5B; CDO 0; 0 tags; 3 `movss` stores (0x6B3C2/0xAD677/0xAD777),
  all from registers.
* **Routes tried:** 1, 1b, 2, 3 (a cooldown in seconds is not visible in the five captures - none
  shows repeated impacts), 4 - all negative.

### F-38 · `BattleModeSpeedDelta` (0x1EB4, `float`, cm/s) - **STILL UNKNOWN**

* **Value:** none. A speed *delta* would need two controlled top-speed runs (normal vs battle
  mode) in one capture; the battle-mode clip has one mode only.
* **Provenance:** would be `decoded` or `derived` (PTS speed); neither exists.
* **Evidence:** schema record at 0x544214; CDO 0; 0 tags; **0** stores at 0x1EB4; the class-mate at
  0x1EB0 (`BattleModeSpeed`) has 1 register `movss`, again no value.
* **Routes tried:** 1, 1b, 2, 3 (no comparative run), 4.

### F-39 · `TurnOnSpotSteeringSpeedCurve` (0x0268, `FInterpCurveFloat`, deg/s over something) - **STILL UNKNOWN**

* **Value:** none, and it is not a scalar: the field is a **curve** (TArray of `FInterpCurvePointFloat`
  + interp mode). "Finding the value" means finding its points.
* **Provenance:** would be `decoded` (serialised curve) or `derived` (samples); neither exists.
* **Evidence:** schema record at 0xCC1C62 (`StructProperty …RVehicleSimBatmobile:TurnOnSpotSteeringSpeedCurve`);
  CDO 0; 0 archetype tags; the 34 immediate stores that touch +0268h are 0.0/1.0/int ones spread
  over unrelated functions - a curve is heap-allocated, so it cannot appear as an imm32 store.
* **Routes tried:** 1, 1b, 2 (structurally impossible to read this way), 3 (turn-on-the-spot is not
  in any capture; G2-21 already found no tank pivot member either), 4 - all negative.

### F-40 · `BattleModeMoving` (0x0294, `bool`) - **STILL UNKNOWN**

* **Value:** none. A bool "is the car moving in battle mode" is a runtime state, not an authored
  default; a default would only exist as a CDO bit, and there is none.
* **Provenance:** would be `decoded`; none found.
* **Evidence:** schema record at 0xCC0ABD (`BoolProperty …RVehicleSimBatmobile:BattleModeMoving`);
  CDO 0; 0 archetype tags; 25 immediate stores at +0294h, all 0.0/0.5/1.0/int ones in unrelated
  code.
* **Routes tried:** 1, 1b, 2, 3 (a flag is not visible), 4.

---

## What this changes for the project

1. **The eight `VALUE-NATIVE` reasons are now three measurements, not an assumption**: 0 archetype
   tags out of 20,128 objects, one schema-only package, and no compiled initialiser (proved with
   class-mates whose shipped values are known).
2. **The three neighbours matter for the translation.** `ImpactShakeForceFactor` 0.01333 and
   `ImpactShakeVehicleFactor` 1.5 *are* file values; F-35/F-36/F-37 sit between them and have none.
   A shake implementation for JC3 can use the two that exist and must choose its own values for the
   three that do not - declared as our design, never as Arkham's.
3. **F-39 and F-40 should stop being listed as "values to find".** One is a curve, the other a
   runtime flag: neither can be "chased" without running the game, and G2-21 already established
   that turn-on-the-spot has no JC3 carrier at all, so the curve would have nothing to drive.
4. **Do not re-run this route.** The remaining sources are a reader for
   `GlobalPersistentCookerData.upk`'s object stream (which per measurement 3 cannot carry a value
   for these fields) and a Q-1 probe (shake cooldown is the cheapest of the eight). Everything else
   is exhausted, and the 3,266-package scan (11.71 GB, 4 min 46 s) is not worth repeating.

## Reproduce

```
python Tools/scripts/chase/chase_g1_values.py scan          # all offsets, one pass, 3 s
python Tools/scripts/chase/chase_g1_values.py dump 0x1A17F5 0x40
python Tools/scripts/chase/chase_namescan_b.py              # 3,266 packages, 11.71 GB, ~5 min
python -c "import json;d=json.load(open(r'E:\\Modding\\_BmAKgrab\\chase\\namescan_b.json'));print(d['hit_count'],d['packages_with_a_hit'])"
```
