# Chase 02 — F-9 … F-16 (G1-21 mode fields with no archetype value)

Scope: `Research/BatmobileGrab/FOOTAGE.md` §6 rows **F-9 … F-16**, all `UNKNOWN` with reason
`WRONG-SCOPE` (the seven camera fields) or `VALUE-NATIVE` (`StrafeCooldown`). Read-only chasing:
no existing document was edited, no game was launched, nothing was committed.

**Result: 8 of 8 rows FOUND, all from one place G1-21 never opened — the class *default object* in
`BmGame.upk`.** `objects.jsonl` holds only the 15 `Playable_Batmobile*` packages, so "not serialised
in any shipped archetype" was true and yet the values do exist: a property that the Batmobile
archetypes do not override still ships with a value in `Default__<Class>` inside the package that
declares the class. `BmGame.upk` (214 757 637 B, `E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole`)
holds both default objects.

| row | field | value | provenance |
|---|---|---|---|
| F-9 | `BattleModeWinchCamConfig` | `FFreeCameraConfig` struct, 266 B tag at field 0x3e9c — see table below | decoded |
| F-10 | `BattleModeAbseilingCamConfig` | `FFreeCameraConfig` struct, 266 B tag at field 0x3f44 — see table below | decoded |
| F-11 | `BattleModeCamFOV` | **60.0 deg** | decoded |
| F-12 | `BattleModeWinchCamFOV` | **60.0 deg** | decoded |
| F-13 | `BattleModeHeadOffset` | **(0, 0, 150) cm** (= 1.5 m up) | decoded |
| F-14 | `BattleModeWinchHeadOffset` | **(0, 0, 300) cm** (= 3.0 m up) | decoded |
| F-15 | `BattleModeAbseilingExtraCameraRot` | rotator **(1500, 0, 0)** = **+8.24 deg pitch** (0 yaw, 0 roll) | decoded value, degree conversion derived |
| F-16 | `StrafeCooldown` | **0.75 s** | decoded |

Nothing here is `assumed`: every number below is a property tag read out of the shipped package,
at the exact field offset the BmSDK inventory names for it.

## Evidence (one place for all eight)

`BmGame.upk`, export **34970** `Default__R3rdPersonCamera` (class `R3rdPersonCamera`, 34 362 B,
447 property tags, walk stops at `eof`) and export **10923** `Default__RVehicleBatmobileBase`
(class `RVehicleBatmobileBase`, 3 186 B).

| field | BmSDK offset | tag in the default object | decoded value |
|---|---|---|---|
| `BattleModeCamConfig` (F-8, same finding) | 0x3df4 = 15860 | StructProperty, 266 B | `StateFreeCameraSitOffsetMin` [-350, 0, 200] … (not requested here) |
| `BattleModeWinchCamConfig` | 0x3e9c = 16028 | StructProperty, 266 B | 24 members, table below |
| `BattleModeAbseilingCamConfig` | 0x3f44 = 16196 | StructProperty, 266 B | 24 members, table below |
| `BattleModeCamFOV` | 0x4fd0 = 20432 | FloatProperty | `60.0` |
| `BattleModeWinchCamFOV` | 0x4fd4 = 20436 | FloatProperty | `60.0` |
| `BattleModeHeadOffset` | 0x4fdc = 20444 | VectorProperty | `[0.0, 0.0, 150.0]` |
| `BattleModeWinchHeadOffset` | 0x4ff8 = 20472 | VectorProperty | `[0.0, 0.0, 300.0]` |
| `BattleModeAbseilingExtraCameraRot` | 0x5034 = 20532 | RotatorProperty | `[1500, 0, 0]` |
| `StrafeCooldown` | 0x11e4 = 4580 | FloatProperty | `0.75` |

The offsets are not inferred: `BMSDK_OFFSETS.json` → `classes.R3rdPersonCamera.properties` gives
`BattleModeCamConfig` 15860, `BattleModeCamFOV` 20432, `BattleModeWinchCamFOV` 20436,
`BattleModeHeadOffset` 20444, `BattleModeWinchHeadOffset` 20472,
`BattleModeAbseilingExtraCameraRot` 20532, and `classes.RVehicleBatmobileBase.properties.StrafeCooldown`
4580 — the same numbers the decoded tags carry, so the tag at 0x4fd0 is that field and not a neighbour.

Command and output (verbatim, wrapped):

```
$ python Tools/scripts/chase/chase02_cdo.py --class R3rdPersonCamera --json E:/Modding/ArkhamKnight/_grab/chase/camera_cdo.json
package BmGame.upk: version 863, licensee 32995, 84813 names, 3268 imports, 177031 exports

=== R3rdPersonCamera (export 34969, class None, 1568 B)
    walked 0 tags, stop=end
    -- card offsets on R3rdPersonCamera:
       BattleModeCamConfig                @0x3df4  absent
       ...
=== Default__R3rdPersonCamera (export 34970, class R3rdPersonCamera, 34362 B)
    walked 447 tags, stop=eof
    ...
    -- card offsets on R3rdPersonCamera:
       BattleModeCamConfig                @0x3df4  SERIALISED None
       BattleModeWinchCamConfig           @0x3e9c  SERIALISED None
       BattleModeAbseilingCamConfig       @0x3f44  SERIALISED None
       BattleModeCamFOV                   @0x4fd0  SERIALISED 60.0
       BattleModeWinchCamFOV              @0x4fd4  SERIALISED 60.0
       BattleModeHeadOffset               @0x4fdc  SERIALISED [0.0, 0.0, 150.0]
       BattleModeWinchHeadOffset          @0x4ff8  SERIALISED [0.0, 0.0, 300.0]
       BattleModeAbseilingExtraCameraRot  @0x5034  SERIALISED [1500, 0, 0]
wrote E:/Modding/ArkhamKnight/_grab/chase/camera_cdo.json
```

```
$ python Tools/scripts/chase/chase02_cdo.py --class RVehicleBatmobileBase --json E:/Modding/ArkhamKnight/_grab/chase/vehiclebase_cdo.json
...
    -- card offsets on RVehicleBatmobileBase:
       StrafeCooldown                     @0x11e4  SERIALISED 0.75
wrote E:/Modding/ArkhamKnight/_grab/chase/vehiclebase_cdo.json
```

(The `SERIALISED None` on the three struct tags is the walker's placeholder for a struct's own
`value`; the struct payload is in each tag's `props`, listed below. The first `=== R3rdPersonCamera`
hit is the class object, which ships no defaults — the default object is the second hit.)

No subclass overrides them: scanning all 235 `Default__*Camera*` / `*Batmobile*` / `*Vehicle*`
objects in the same package for the nine offsets finds exactly these two objects.

```
$ python Tools/scripts/chase/chase02_cdo.py --scan
-- scanning 235 Default__*Camera/Batmobile/Vehicle objects for offsets ['0x11e4', '0x3df4', '0x3e9c', '0x3f44', '0x4fd0', '0x4fd4', '0x4fdc', '0x4ff8', '0x5034']
   Default__RVehicleBatmobileBase (export 10923): [(4580, None, 0.75)]
   Default__R3rdPersonCamera (export 34970): [(15860, None, None), (16028, None, None), (16196, None, None), (20432, None, 60.0), (20436, None, 60.0), (20444, None, [0.0, 0.0, 150.0]), (20472, None, [0.0, 0.0, 300.0]), (20532, None, [1500, 0, 0])]
   -> 2 object(s) carry any of the card offsets
```

Scripts and extracted data (not in the workspace docs):

- `Tools/scripts/chase/chase02_cdo.py` — `--list`, `--class <name> [--json OUT]`, `--scan`;
  reuses `Tools/scripts/upk_read.py` (`Package`, `best_walk`) and writes only the `--json` path.
- `E:/Modding/ArkhamKnight/_grab/chase/camera_cdo.json`, `E:/Modding/ArkhamKnight/_grab/chase/vehiclebase_cdo.json` —
  every tag of the two default objects.

---

## F-9 · `BattleModeWinchCamConfig`

**STATUS: FOUND.**
Value: `FFreeCameraConfig` struct, serialised tag offset 0x3e9c (16028), 266 B, decoded member by
member (member names and offsets from `BMSDK_OFFSETS.json` →
`classes.R3rdPersonCamera.structs.FFreeCameraConfig`, whose 24 member offsets 0/12/24/28/40/52/64/
76/80/84/88/92/96/100/104/108/112/116/120/132/144/156/160/164 match the decoded sub-tags one to one):

| FFreeCameraConfig member | offset | value (winch config) |
|---|---|---|
| `StateFreeCameraSitOffsetMin` | 0 | `[-650.0, 0.0, 400.0]` cm |
| `StateFreeCameraSitOffsetMax` | 12 | `[-800.0, 0.0, 400.0]` cm |
| `UseStateFreeCameraSitOffsetUp` | 24 | `true` |
| `StateFreeCameraSitOffsetUp` | 28 | `[-900.0, 0.0, 2800.0]` cm |
| `StateFreeCameraPullOffset` | 40 | `[0.0, 0.0, 0.0]` cm |
| `CameraPivotOffset` | 52 | `[400.0, 0.0, 5.0]` cm |
| `ZoomedOffset` | 64 | `[50.0, 0.0, -30.0]` cm |
| `maxPitch` | 76 | `6000.0` (as shipped, unit not documented) |
| `MinPitch` | 80 | `-8000.0` (as shipped) |
| `MinFreeCameraDistance` | 84 | `1000.0` cm |
| `MaxFreeCameraDistance` | 88 | `1000.0` cm |
| `ShortCamSpringConst` | 92 | `24.0` |
| `LongCamSpringConst` | 96 | `8.0` |
| `DefaultCameraPitch` | 100 | `0.0` |
| `CameraSitOffsetPower` | 104 | `1.5` |
| `CameraSitOffsetMin` | 108 | `16384.0` |
| `CameraSitOffsetMax` | 112 | `16384.0` |
| `bUseSeparate43Settings` | 116 | `false` |
| `StateFreeCamera43SitOffsetMax` | 120 | `[0.0, 0.0, 0.0]` |
| `StateFreeCamera43SitOffsetMin` | 132 | `[0.0, 0.0, 0.0]` |
| `StateFreeCamera43SitOffsetLookUp` | 144 | `[0.0, 0.0, 0.0]` |
| `bDontModifySitOffsetWhenLookingUp` | 156 | `false` |
| `MinCameraSmoothingAngle` | 160 | `10.0` |
| `MaxCameraSmoothingAngle` | 164 | `10.0` |

Provenance class: `decoded` (cooked property tags, `BmGame.upk` export 34970).
Routes tried: (1) class default object — **found**; (2) native executable, (3) captures,
(4) published sources — not attempted, route 1 answered with a file value (R4: a file value wins).
Note: the struct's `maxPitch`/`MinPitch` are carried as shipped; the BmSDK names them, nothing
defines their unit, so no degree conversion is claimed for them.

## F-10 · `BattleModeAbseilingCamConfig`

**STATUS: FOUND.**
Value: `FFreeCameraConfig` struct, tag 0x3f44 (16196), 266 B:

| FFreeCameraConfig member | offset | value (abseiling config) |
|---|---|---|
| `StateFreeCameraSitOffsetMin` | 0 | `[-1000.0, 0.0, 0.0]` cm |
| `StateFreeCameraSitOffsetMax` | 12 | `[-300.0, 0.0, -200.0]` cm |
| `UseStateFreeCameraSitOffsetUp` | 24 | `false` |
| `StateFreeCameraSitOffsetUp` | 28 | `[0.0, 0.0, 0.0]` cm |
| `StateFreeCameraPullOffset` | 40 | `[0.0, 0.0, 0.0]` cm |
| `CameraPivotOffset` | 52 | `[-100.0, 0.0, 700.0]` cm |
| `ZoomedOffset` | 64 | `[50.0, 0.0, -30.0]` cm |
| `maxPitch` | 76 | `14500.0` (as shipped) |
| `MinPitch` | 80 | `-14000.0` (as shipped) |
| `MinFreeCameraDistance` | 84 | `400.0` cm |
| `MaxFreeCameraDistance` | 88 | `400.0` cm |
| `ShortCamSpringConst` | 92 | `24.0` |
| `LongCamSpringConst` | 96 | `8.0` |
| `DefaultCameraPitch` | 100 | `0.0` |
| `CameraSitOffsetPower` | 104 | `1.0` |
| `CameraSitOffsetMin` | 108 | `16384.0` |
| `CameraSitOffsetMax` | 112 | `16384.0` |
| `bUseSeparate43Settings` | 116 | `false` |
| `StateFreeCamera43SitOffsetMax` | 120 | `[0.0, 0.0, 0.0]` |
| `StateFreeCamera43SitOffsetMin` | 132 | `[0.0, 0.0, 0.0]` |
| `StateFreeCamera43SitOffsetLookUp` | 144 | `[0.0, 0.0, 0.0]` |
| `bDontModifySitOffsetWhenLookingUp` | 156 | `false` |
| `MinCameraSmoothingAngle` | 160 | `10.0` |
| `MaxCameraSmoothingAngle` | 164 | `10.0` |

Provenance class: `decoded`, same evidence as F-9.
Routes tried: same; found at route 1.

## F-11 · `BattleModeCamFOV`

**STATUS: FOUND.** **60.0 deg.**
Evidence: `BmGame.upk` export 34970 `Default__R3rdPersonCamera`, FloatProperty tag at field offset
0x4fd0 (20432) = `60.0`; BmSDK `R3rdPersonCamera.BattleModeCamFOV` offset 20432. Unit deg from the
field name and the engine's FOV convention (`MODES.md` unit column already carried `deg`).
Provenance class: `decoded`.
Routes tried: (1) found; the rest not needed.
Why G1-21 missed it: the field is absent from the four `Playable_Batmobile*` archetypes, and
`objects.jsonl` never reads `BmGame.upk`. A camera instance that does not override inherits this
class default.

## F-12 · `BattleModeWinchCamFOV`

**STATUS: FOUND.** **60.0 deg.**
Evidence: same object, FloatProperty at 0x4fd4 (20436) = `60.0`; BmSDK offset 20436.
Provenance class: `decoded`. Routes tried: (1) found.

## F-13 · `BattleModeHeadOffset`

**STATUS: FOUND.** **(0, 0, 150) cm = 1.5 m above the camera origin.**
Evidence: same object, VectorProperty at 0x4fdc (20444) = `[0.0, 0.0, 150.0]`; BmSDK offset 20444,
`Vector3`. UE3 length unit is cm, which is how `MODES.md` already labelled the field.
Provenance class: `decoded`. Routes tried: (1) found.
The metre figure is a unit conversion (150 cm), not a separate measurement.

## F-14 · `BattleModeWinchHeadOffset`

**STATUS: FOUND.** **(0, 0, 300) cm = 3.0 m above the camera origin.**
Evidence: same object, VectorProperty at 0x4ff8 (20472) = `[0.0, 0.0, 300.0]`; BmSDK offset 20472,
`Vector3`.
Provenance class: `decoded`. Routes tried: (1) found.

## F-15 · `BattleModeAbseilingExtraCameraRot`

**STATUS: FOUND.** **Rotator (1500, 0, 0) = +8.24 deg pitch, 0 yaw, 0 roll.**
Evidence: same object, RotatorProperty at 0x5034 (20532) = `[1500, 0, 0]`; BmSDK offset 20532,
`Rotator`. 1500 × 360/65536 = 8.2397 deg — the signed-to-degree step is `derived` (UE3 rotator
units, 65536 per revolution); the stored value 1500 is `decoded`.
Provenance class: `decoded` (value), `derived` (the degree figure).
Routes tried: (1) found.

## F-16 · `StrafeCooldown`

**STATUS: FOUND.** **0.75 s.**
Evidence: `BmGame.upk` export 10923 `Default__RVehicleBatmobileBase` (class `RVehicleBatmobileBase`,
3 186 B), FloatProperty at field offset 0x11e4 (4580) = `0.75`; BmSDK
`RVehicleBatmobileBase.StrafeCooldown` offset 4580. Unit s from the name convention already in
`MODES.md`; the field is not rescaled.
Provenance class: `decoded`.
Routes tried: (1) found — the vehicle archetypes do not override it, so every Batmobile instance
inherits 0.75. (2)/(3)/(4) not needed.
Consistency: the neighbouring `CurrentStrafeCooldown` (0x11e8) is a *runtime* member and is not
serialised, which fits: `StrafeCooldown` is the configured 0.75 s, the current value is computed.

---

## What this changes in FOOTAGE.md (not edited here — read-only)

Rows F-9 … F-16 should move from `UNKNOWN` / `WRONG-SCOPE` / `VALUE-NATIVE` to **RESOLVED** with
reason `FILE-VALUE`, and the §6 preamble "61 fields … no value exists" needs the qualifier
"no value in the 15 `Playable_Batmobile*` packages"; the class default objects in `BmGame.upk`
carry values for at least these eight. `grab_modes.py` reads `objects.jsonl` only, which is why the
gap survived G1-21 and G1-23.

## Limits / UNKNOWNs of this chase

1. These are **class defaults**, which is what a non-overriding camera/vehicle instance runs. The
   chase proved no `Default__*Camera*`/`*Batmobile*`/`*Vehicle*` object in `BmGame.upk` overrides
   them, and the only camera config file the game ships (`BmGame/Config/BmCamera.ini` →
   `[BmGame.R3rdPersonCamera]`) sets just `EnableCameraAssist=True`, so nothing overrides them at
   load either. A level script or code could still change FOV at runtime (dynamic FOV, speed FOV);
   that is not in any file read here — UNKNOWN, and no number is claimed for it.
2. `maxPitch` / `MinPitch` inside the two structs are reported as shipped (6000 / −8000 and
   14500 / −14000). No documented unit exists, so no degree conversion is offered.
3. `BattleModeCamConfig` (F-8, outside this row set) is in the same default object and now likewise
   decodable (tag at 0x3df4, `StateFreeCameraSitOffsetMin` `[-350, 0, 200]` …) — noted, not chased.
4. `BmGame.upk` is 214 MB and its name table is read in memory; the chase script opens it read-only
   and writes nothing under the game folder.
5. No published source was used, and no capture was needed: every row is a file value, so footage
   cannot override them (R4).
