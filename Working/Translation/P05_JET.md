# P-05 — what carries the Batmobile jet, and whether BmAK drives it by `engine_rpm`

**Question.** P-05 is `batmobile_jet`: `EngineRotatingPart`, driving variable `engine_rpm`, `static`
with no hinge, and the only T-8 row (with P-02 and P-13, now answered) without a mechanism. Does
BmAK carry an object with that name, and does that object have an `engine_rpm`-driven rotation or a
bone named after the jet?

**Verdict.** BmAK carries **a bone named after the jet and no object named `batmobile_jet`**, and it
carries **no `engine_rpm`-driven rotation** for that bone. The name `batmobile_jet` is the *JC3 build
part* (part 60), not a BmAK object: across the four cooked Batmobile packages there are 28 jet
name-table entries and **0 jet exports**, and all 28 are bone names, sequence names, socket names or
imported asset names. The jet bone chain is real and decoded — `JetSMove` (#40) → `Batmobile_Rig_Jet_Root`
(#41) → 18 nozzle bones + `Jet_Thruster` + `Jet_Fins` — but the only motion any of the 253 cooked
sequences gives it is **translation** (`JetSMove` 40.1633 cm in `Batmobile_V2_Bat_Tracker`) and
**bounded nozzle rotation** (max 20.014°); nothing spins it. The `engine_rpm` half of the row is the
donor translation ANI-4 (`v0506` tractor fan), and its words "the spin itself is driven by
`engine_rpm`" in `PARTS_ANIM_COVERAGE.md:44` are **DERIVED, not decoded** — no BmAK file binds an RPM
value to this bone.

## 1. The JC3 row, decoded

| item | value | label | source |
|---|---|---|---|
| row | `P-05 \| batmobile_jet \| EngineRotatingPart \| — \| 0.000, 0.543, 1.343 \| — \| — \| static \| — \| — \| no hinge \| Land_Generic` | decoded | `Working/Translation/T8_PARTS.md:50` |
| mesh row | `batmobile_jet \| body \| JetSMove \| 6272 \| [1133, 160, 73, 41, 41]` | decoded | `Working/Translation/T8_PARTS.md:32` |
| pivot bone | `JetSMove` (#40), parent `Batmobile_Chassis_Mesh`, origin 0.000 / 0.543 / 1.343 | decoded | `Research/BatmobileGrab/BONES.md:82`, `BONES.json` |
| joint | `null` — no hinge, no joint bone | decoded | `Working/Translation/T8_PARTS.json` `parts[P-05].joint` |
| behaviour / variable | `EngineRotatingPart`, channel `rotating`, variable `engine_rpm` | decoded | `Working/Translation/T8_PARTS.json` P-05 |
| claimed proof | `proven-on-CCar`, carrier `v0506_car_solar_oldtractor` | decoded | `Working/Translation/T8_PARTS.json` P-05 `proof`, `carrier_chassis` |
| sequences | none (`animation_sequences: []`) | decoded | `Working/Translation/T8_PARTS.json` P-05; `PARTS_ANIM_COVERAGE.md:27` |
| build record | part_index 60, parent `sportsmuscle_body`, behaviour `EngineRotatingPart`, hash 1813315288 | decoded | `Working/Parts/bm_vehicle_parts.json` `parts[batmobile_jet]` |
| "spin is driven by `engine_rpm`" | asserted, no BmAK citation | **derived** | `PARTS_ANIM_COVERAGE.md:44` |
| ANI-4 donor | `EngineRotatingPart` → `engine_rpm`, "proven on a land vehicle: `v0506 oldtractor_fan`" | decoded donor fact, not BmAK | `GRAB_BACKLOG.md:219` |
| JC3 carrier census | `EngineRotatingPart \| rotating, engine_rpm \| 3 rows \| CCar \| proven-on-CCar` | decoded | `Research/JC3Grab/MOVING_PARTS.md:158` |

## 2. The BmAK objects that carry the jet name — decoded

The chain is 22 bones (#40–#61): `JetSMove` → `Batmobile_Rig_Jet_Root` → 18 nozzles, `Jet_Thruster`
and `Jet_Fins`. The cooked name tables hold the jet only as bones, sockets, sequence names and
imported assets. There is **no export whose object name contains "jet"** in any of `Playable_Batmobile_SF`,
`Playable_BatmobileMK2_SF`, `Playable_BatmobileFunhouse_SF`, `Playable_BatmobileJoker_SF`
(0 exports in each; the `Playable_Batmobile*_Std_*.upk` variant packages have 0 jet names at all).

| object | package | name index | export index | class | label | source |
|---|---|---:|---:|---|---|---|
| `JetSMove` (bone) | `Playable_Batmobile_SF` | 1608 | — (bone, not an export) | bone #40 | decoded | `tmp/freebuff/scratch/p05_upk.json` |
| `Batmobile_Rig_Jet_Root` (bone) | `Playable_Batmobile_SF` | 1624 | — | bone #41 | decoded | same |
| `Batmobile_Rig_Jet_Nozzle_001` … `_018` (18 bones) | `Playable_Batmobile_SF` | 1613–1630 | — | bones #42–#60 | decoded | `BONES.md:84-101` |
| `Batmobile_Rig_Jet_Thruster` (bone) | `Playable_Batmobile_SF` | 1631 | — | bone #59 | decoded | `BONES.md:100` |
| `Batmobile_Rig_Jet_Fins` (bone) | `Playable_Batmobile_SF` | 1626 | — | bone #61 | decoded | `BONES.md:102` |
| `Afterburner` socket, on `JetSMove` | `Playable_Batmobile_SF` | — | 5386 (`Funhouse`); 5351 (`MK2`); 3196 (`Joker`) | `SkeletalMeshSocket` | decoded | `objects.jsonl:5386,14331,8784`; `SOCKETS_JC3.md:73` |
| `MESH_Batmobile_Jet_V01` | import path `Engine.*`; defined in `BmGame.upk` | 50803 | **176021** | `StaticMesh` | decoded | `tmp/freebuff/scratch/p05_bmgame.json`; name index 1857 in `Playable_Batmobile_SF` |
| `INST_JetExhaust` | import path `Engine.*` | 1588 (SF) | — (import) | `MaterialInstanceConstant` | decoded | `objects.jsonl:17414` |
| `batmobile_jet` | **absent from BmAK** | — | — | — | **UNKNOWN / absent** | probe below |

`MESH_Batmobile_Jet_V01` is an *exhaust-particle* mesh, not the turbine: it is referenced by
`ParticleModuleTypeDataMesh` export 4257 in `Exhaust.batmobileExhaust_burst` (`objects.jsonl:18779`)
and by the `SideExhaust_Boost` required module (`INST_JetExhaust`, `objects.jsonl:17414`). The jet
geometry the build cuts (6272 faces) belongs to the body mesh and follows the `JetSMove` bone.

Package totals from the probe (all decoded): `Playable_Batmobile_SF.upk` — 28 jet names, 0 jet
exports, 5,490 exports; `MK2`, `Funhouse`, `Joker` — 28, 28, 26 jet names, 0 jet exports each;
`Engine.upk` (26,790 names, 39,080 exports) has **no** `MESH_Batmobile_Jet_V01` name or export;
`BmGame.upk` (84,813 names, 177,031 exports) holds name 46114 `JetSMove`, name 50803
`MESH_Batmobile_Jet_V01` and export 176021 `StaticMesh`.

## 3. Does anything rotate the jet? — decoded animation census

`Research/BatmobileGrab/ANIMATIONS.json` (253 sequences, 13 anim sets, 4 packages):

| measurement | value | label | source |
|---|---|---|---|
| `JetSMove` largest rotation, all sequences | **0.0°** (it never rotates) | decoded | `ANIMATIONS.json` |
| `JetSMove` largest translation | **40.1633 cm** in `Batmobile_V2_Bat_Tracker` (`Playable_Batmobile_SF` export 229) | decoded | same |
| `JetSMove` other translation | 51.0594 cm in `Batmobile_V2_Back_Door_Open` (export 215) and `_Close` (234) | decoded | same |
| largest jet-bone rotation | **20.014°** (`Batmobile_Rig_Jet_Nozzle_003`, `Batmobile_V2_Back_Door_Close`) | decoded | same |
| boost-time nozzle rotation | 15.553°–16.725° in `Batmobile_V2_Jet_Boost` (export 214) | decoded | same |
| jet nodes in the 3 AnimTrees | **none** — controls are `RSkelControl_FeedConstraint` on `Flappy_Rear_Door_Btm_Rot` and the two `*_Power_Cell` bones | decoded | `ANIMATIONS.json` `trees[]`, `P02_CANNON.md` §3 |
| jet skeletal-control class in BmAK | **none** — the vehicle controls are `RSkelControlBatmobileWheel`, `RSkelControlDeformVehicle`, `RSkelControlTankTrack` (plus constraint controls) | decoded | `E:/Modding/_shared/tools/BmSDK-AK/.../RBatmobileBooster` family listing |
| spin animation for the jet | **none** — every jet motion is bounded (≤20.014°) or translational | decoded | census above |
| "spin driven by `engine_rpm`" | donor inference, no BmAK driver found | **derived** | `PARTS_ANIM_COVERAGE.md:44` |

The 15–20° nozzle motion is flap/cover travel on state changes (`Jet_Boost`, door and turret
sequences), not a turbine spin: it is bounded, returns, and no control node or RPM member feeds it.

## 4. Is there an `engine_rpm` path at all? — decoded and absent

| fact | value | label | source |
|---|---|---|---|
| BmAK sim RPM member | `SVehicle.EngineRPM`, `FloatProperty`, offset **1840** | decoded | `Research/BatmobileGrab/BMSDK_OFFSETS.json` (class `SVehicle`, file `SVehicle.g.cs`) |
| BmAK RPM curve | `RVehicleSimCar.EngineRPMCurve`, `FInterpCurveFloat`, offset **280** | decoded | same (class `RVehicleSimCar`) |
| member naming the jet | **none** — no `BMSDK_OFFSETS.json` member contains "jet" | decoded | grep of the 41-class dump |
| `engine_rpm` / `EngineRotatingPart` in the BmAK SDK | **absent** — neither string exists in `BmSDK-AK` | decoded | `grep -rn "engine_rpm\|EngineRotatingPart" E:/Modding/_shared/tools/BmSDK-AK` (0 hits) |
| RPM consumers in BmAK | audio only (`AudioGetAlternateRPM`, `AudioGetAlternateRPMVector`, `NormalRPMParamArray`) plus the sim curves | decoded | `RBatmobileBooster.g.cs`, `RVehicleBatmobileBase.g.cs` |
| what would spin a jet bone | nothing in the cooked tables or the SDK dump | **UNKNOWN** (native code not in these files) | see §7 |

## 5. Verdict on the row

- The row's **bone** is right: `JetSMove` is the jet's pivot bone (#40, parent `Batmobile_Chassis_Mesh`),
  and the `Afterburner` socket hangs off it. That part is **DECODED**.
- The row's **mechanism** (`EngineRotatingPart` + `engine_rpm`) is **DECODED on the JC3 side**
  (`MOVING_PARTS.md:158`: 3 vehicle rows, all `CCar`, proven-on-CCar) and **donor-proven on `v0506`**
  (`GRAB_BACKLOG.md:219`) — not derived from BmAK.
- The claim that BmAK's own jet spin is "driven by `engine_rpm`" is **DERIVED and unsupported**: BmAK
  has no jet export, no jet skeletal control, no jet member, and no RPM binding. Without a
  driver, the build's rotating part has JC3's `engine_rpm` as its only source of truth.
- **No edit is needed to `T8_PARTS.md` or the part module.** P-05 keeps `EngineRotatingPart`,
  `engine_rpm`, `Land_Generic`, no hinge, and the `JetSMove` pivot; the mechanism is donor-sourced,
  and that is now stated rather than implied to be BmAK's.

## 6. What the jet cannot reproduce

- `JetSMove` translates 40.1633 cm in `Batmobile_V2_Bat_Tracker`; a JC3 rotating part can only spin
  about its axis, so that travel is **not reproducible** and stays a T-8 note.
- The axis for P-05 is **UNKNOWN**: the T-8 row's axis columns are `—`, `T8_PARTS.json` has no
  `axis`, and `EngineRotatingPart`'s axis field is not decoded in this card.

## 7. UNKNOWNs

1. **What actually spins the jet in BmAK, if anything.** No cooked object, skeletal control, AnimTree
   node, or SDK member binds RPM to the jet; whether native code turns the bone by name is **UNKNOWN**
   — it is not in `BmGame.upk`, `Engine.upk`, the four Batmobile packages, or the `BmSDK-AK` dump.
   The file that would settle it is a shipped script/native table that references `JetSMove` with an
   RPM argument; none exists in the packages searched.
2. **Packages not searched.** All `Playable_Batmobile*`, `Engine.upk` and `BmGame.upk` name/export
   tables were searched; DLC trees and gameplay packages beyond those were not. An object named
   `batmobile_jet` there is possible, not observed.
3. **P-05's rotation axis and rate in JC3** — no file value; the `rotoscope_rpm_per_cycle` field is
   20.0 for `EngineRotatingPart` (`MOVING_PARTS.md:67`) but its meaning is itself **UNKNOWN**.
4. **The `v0506` proof's shape** — `GRAB_BACKLOG.md:219` names `oldtractor_fan`; this card did not
   re-open that entity, so its bone/axis is taken as the donor report states.

## 8. Reproduce

```
python tmp/freebuff/scratch/p05_probe.py --json tmp/freebuff/scratch/p05_upk.json \
  "E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole/Playable_Batmobile*.upk"
python Tools/scripts/p05_jet.py --check
```

The probe writes `tmp/freebuff/scratch/p05_upk.json`; the BmGame name/export indices are in
`tmp/freebuff/scratch/p05_bmgame.json`. `--check` re-derives every figure above from
`T8_PARTS.json`, `bm_vehicle_parts.json`, `BONES.json`, `ANIMATIONS.json`, `BMSDK_OFFSETS.json`, the
two probe caches and the cited line numbers, and fails on drift. Read-only throughout: no package,
build or research file was written.
