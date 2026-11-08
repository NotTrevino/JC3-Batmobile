# Witness - P-05 `batmobile_jet`: object, bone and driver

**Task:** find the BmAK object that carries the `batmobile_jet` name, and decide whether it has an
`engine_rpm`-driven rotation or a bone named after the jet. Record each property with package and
export index, or UNKNOWN with the packages searched.

**Status: complete. Verdict: a jet-named BONE, no jet-named object, no `engine_rpm` binding.**

| item | where |
|---|---|
| card | `Working/Translation/P05_JET.md` (pre-existing, verified) |
| checker | `Tools/scripts/p05_jet.py --check` (37 facts, 0 failures, exit 0) |
| probe | `tmp/freebuff/scratch/p05_probe.py` -> `p05_upk.json`, `p05_bmgame.json` |
| this witness | `tmp/freebuff/reports/jet-part-bone-driver.md` |

Read-only throughout: no package, build or research file written. Only this witness was created.

## 1. Live name-table lookup (this session, `Tools/scripts/upk_read.py`)

Re-run independently of the cached probe, so the card does not rest on its own cache:

| package | names | exports | jet names | jet exports | exact `batmobile_jet` |
|---|---:|---:|---:|---:|---|
| `Playable_Batmobile_SF.upk` | 3,151 | 5,490 | 28 | **0** | none |
| `Playable_BatmobileMK2_SF.upk` | 3,156 | 5,534 | 28 | **0** | none |
| `Playable_BatmobileFunhouse_SF.upk` | 3,134 | 5,584 | 28 | **0** | none |
| `Playable_BatmobileJoker_SF.upk` | 3,394 | 3,388 | 26 | **0** | none |
| `BmGame.upk` | 84,813 | 177,031 | 10 | 5 | none |
| `Engine.upk` | 26,790 | 39,080 | 14 | 11 | none |

**decoded:** the string `batmobile_jet` occurs in **no** name table and **no** export of the six
packages. It is a JC3 build part name (part 60), not a BmAK object.

**decoded:** every jet-named export in those packages is accounted for and none is the Batmobile
turbine: `BmGame.upk` 94487 `JetpackSound` (ObjectProperty), 143865 `MAT_JetExhaust` (Material),
147870 `INST_JetExhaust` (MaterialInstanceConstant), 175976 `Firefly_JetMesh` (StaticMesh),
**176021 `MESH_Batmobile_Jet_V01` (StaticMesh)**; `Engine.upk` 3464/13562/13565/28594 ApexJet
field/particle classes plus defaults. `MESH_Batmobile_Jet_V01` is the exhaust-particle mesh, cited
by `ParticleModuleTypeDataMesh` 4257 in `Exhaust.batmobileExhaust_burst`, not the turbine.

**decoded:** the four `Playable_Batmobile*` packages hold jet entries only in the **name table**
(28/28/28/26), zero exports: `Jet_Fins001`, `JetSMove`, `MESH_Batmobile_Jet_V01`,
`Batmobile_Rig_Jet_Root`, `Batmobile_Rig_Jet_Thruster`, `Batmobile_Rig_Jet_Fins`,
`Batmobile_Rig_Jet_Nozzle_001..018`, the sequence names `Batmobile_V2_Jet_Boost` /
`Batmobile_V2_Jet_Close`, the imported `INST_JetExhaust` and `Firefly_JetMesh`.

## 2. Bone named after the jet - YES

**decoded** from `Research/BatmobileGrab/BONES.json` (skeleton mesh `Playable_Batmobile_SF`
export 5284, 180 bones):

| bone | index | parent | role |
|---|---:|---|---|
| `JetSMove` | 40 | `Batmobile_Chassis_Mesh` | jet pivot; pivot JC3 `0.000, 0.543, 1.343` m |
| `Batmobile_Rig_Jet_Root` | 41 | `JetSMove` | root of the 20-bone jet assembly |
| `Batmobile_Rig_Jet_Nozzle_001..018` | 42-58, 60 | `Batmobile_Rig_Jet_Root` | nozzle ring |
| `Batmobile_Rig_Jet_Thruster` | 59 | `Batmobile_Rig_Jet_Root` | thruster |
| `Batmobile_Rig_Jet_Fins` | 61 | `Batmobile_Rig_Jet_Root` | fins |

22 jet-named bones in the chain, 18 of them nozzles. **decoded:** the `Afterburner` socket hangs on
`JetSMove` (`SkeletalMeshSocket` export 5386/5351/3196 in Funhouse/MK2/Joker), which is the exact
pivot the JC3 row uses.

## 3. `engine_rpm`-driven rotation - NO EVIDENCE (UNKNOWN)

| fact | value | label |
|---|---|---|
| `EngineRotatingPart` / `engine_rpm` strings in `E:/Modding/_tools/BmSDK-AK` | **0 hits** (grep of `src`, all `.cs`) | decoded |
| BmAK RPM member | `SVehicle.EngineRPM`, FloatProperty, offset **1840** | decoded (`BMSDK_OFFSETS.json`) |
| BmAK RPM curve | `RVehicleSimCar.EngineRPMCurve`, FInterpCurveFloat, offset **280** | decoded (same) |
| member naming the jet | **none**; no member in the 41-class dump contains "jet" | decoded |
| skeletal control on a jet bone | **none**; the AnimTrees carry only `RSkelControl_FeedConstraint` on door/power-cell bones | decoded |
| `JetSMove` rotation across 253 sequences | **0.0 deg** | decoded (`ANIMATIONS.json`) |
| `JetSMove` translation | **40.1633 cm** in `Batmobile_V2_Bat_Tracker` (SF export 229); 51.0594 cm in `Batmobile_V2_Back_Door_Open`/`_Close` (215/234) | decoded |
| largest jet-bone rotation | **20.014 deg**, `Batmobile_Rig_Jet_Nozzle_003`, `Batmobile_V2_Back_Door_Close` | decoded |
| boost-time nozzle rotation | 15.553-16.725 deg, `Batmobile_V2_Jet_Boost` (SF export 214) | decoded |
| "the spin itself is driven by `engine_rpm`" (`PARTS_ANIM_COVERAGE.md:44`) | asserted, no BmAK citation | **derived** |
| what actually spins the jet at runtime | native code not in any searched file | **UNKNOWN** |

The engine's RPM exists in BmAK only as a simulated value (`SVehicle.EngineRPM`), its curve and
audio parameters; nothing binds it to a jet bone. The donor fact in `GRAB_BACKLOG.md:219`
(`EngineRotatingPart` -> `engine_rpm`) is a JC3 fact proven on the `v0506` tractor fan, not a BmAK
one, so P-05's mechanism stays donor-sourced.

## 4. Packages searched

`Playable_Batmobile_SF`, `Playable_BatmobileMK2_SF`, `Playable_BatmobileFunhouse_SF`,
`Playable_BatmobileJoker_SF`, `BmGame.upk`, `Engine.upk` (all under
`E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole`), plus the SDK dump at
`E:/Modding/_tools/BmSDK-AK` and `Research/BatmobileGrab/{BONES,ANIMATIONS,BMSDK_OFFSETS}.json`.
Not searched: DLC trees and other gameplay packages; an object named `batmobile_jet` there is
possible, not observed.

## 5. Commands and results

```
python Tools/scripts/p05_jet.py --check
-> 37 source facts, 0 failure(s)   exit 0
```

The live `upk_read.py` walk above was run this session and agrees with the cached probe
(`28 jet names, 0 jet exports` in SF; `JetSMove` name index 1608; `MESH_Batmobile_Jet_V01` name
index 1857 in SF, 50803 / export 176021 in BmGame).

## 6. Limitations

- The card's `EngineRotatingPart` claim is a JC3 build fact; this witness only establishes that no
  BmAK file supplies an RPM binding to the jet, not what the JC3 runtime does with `engine_rpm`.
- Bone indices and pivots are from the `Batmobile_V2` skeleton in `Playable_Batmobile_SF`; the MK2,
  Funhouse and Joker packages carry the same 22-name jet chain with package-local name indices, not
  a re-derived skeleton.
- Absence of a jet skeletal control is a census of the cooked tables and 3 AnimTrees, not a proof
  about native code.
