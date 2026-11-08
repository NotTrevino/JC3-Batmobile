# P-13 — how BmAK carries the steering wheel

**Question.** P-13 is the steering wheel. `PARTS_ANIM_COVERAGE.md` lists it as `no-sequence`, and
`T8_PARTS.md` records no joint bone. Which BmAK mechanism turns it: a bone, a skeletal control, a
script-driven rotation or an AnimTree node?

**Verdict — `UNKNOWN` for a wheel-turning bone, and `ABSENT` for the asset itself.** BmAK has **no
steering-wheel geometry, no steering-wheel asset and no steering-wheel bone for the Batmobile**, and
none in any of the 324 packages searched. The Batmobile does not model a yoke at all. What BmAK does
have is a *road-wheel* steering chain: the simulation's steer value drives `SVehicleWheel.Steer`, and
the visual wheel is placed by a **skeletal control named on the wheel**
(`SVehicleWheel.SkelControlName` + `SVehicleWheel.WheelControl` → `SkelControlWheel`, with
`RSkelControlBatmobileWheel` as the Batmobile-specific class in `BmGame.upk`). That mechanism is for
the four wheels, not for a driver's yoke, and nothing in it can be reused for P-13 as-is.

So the T-8 row's `—` bone and its static reason are correct, and the ANI-7 expectation ("yoke turns
with steering") has **nothing on the BmAK side to copy**. The JC3-side carrier that does exist is the
`SteeringWheel` moving-part behaviour driven by `steering_turn` — also a variable, not an animation.

## 1. Routes tried, and what each returned

| # | route | command / file | result |
|---|---|---|---|
| 1 | skeleton | `Research/BatmobileGrab/BONES.json` (180 bones, `Batmobile_V2` skeleton, `Playable_Batmobile_SF` export 5284) | **0** bones match `steer`/`yoke`. 45 bones match wheel/steer/yoke/cockpit/driver/hand, and every one is a road wheel (`SUSP1_Wheel_*`, `Wheel_Parent_*`, `Wheel_*_Disc/Fan`), the cockpit shell (`CockPit_Mesh`, `Batmobile_Rig_Cockpit_Armor_*`) or a wheel arch — no driver control |
| 2 | animation | `Research/BatmobileGrab/ANIMATIONS.json` (253 sequences, 13 sets, 3 AnimTrees, 4 packages) | **0** sequences with a steering name; **0** track bones matching steer/yoke; `mechanism_counts` has no steering class |
| 3 | AnimTree | same file, `trees[]` | 3 trees: `Batmobile_Skel_Ctrl_Door` (SF, export 244), the same in MK2 (243), and `Batwing_Vehicle_AnimTree` (Joker, 485). Each child is `AnimNodeSequence`; the only skeletal controls are **3× `RSkelControl_FeedConstraint`** on `Flappy_Rear_Door_Btm_Rot` and the two `*_Power_Cell` bones. No yoke node, no steering control |
| 4 | interior geometry | `Research/BatmobileGrab/COCKPIT.md:24,94` | **no yoke**: the hand box `|x| < 0.17, y 1.00..1.30, z -1.60..-1.10` holds **4 faces of any material** (y 1.20..1.30: 4, all other bands 0). The nearest driver-facing surface is the instrument panel at z −1.5097. `MESHES.md`'s 12 mesh exports are the body, damaged/fire variants, MK2/Jokerified skins and the Batwing carrier |
| 5 | cooked packages — name tables | `python Tools/scripts/upk_read.py` API (`Package`) over **324 packages**: every `Playable_*.upk`, every `Showcase_*.upk`, `BmGame.upk` (214,757,637 B) and `Engine.upk`; probe `tmp/freebuff/scratch/p13_probe.py`, output `tmp/freebuff/scratch/p13_upk.json` | **0 name-table entries containing `yoke` or `steeringwheel`**, in any of the 324. `steer` hits are simulation members, audio parameters and interp tracks (list in §2) |
| 6 | cooked packages — class inventory | same probe (`anim_class_counts`) | `AnimTree` 368, `AnimSet` 1209, `AnimSequence` 18,479, `RSkelControl_FeedConstraint` 18,002, `RSkelControl_PositionConstraint` 2,101, `RSkelControl_LimitConstraint` 288, `SkelControlWheel` 25, `RSkelControlBatmobileWheel` 5, `RSkelControlDeformVehicle` 7, `RSkelControlTankTrack` 1, `SkelControlSingleBone` 40 — the vehicle-visual controls are wheel/track classes; no steering-wheel control class exists |
| 7 | BmSDK layouts | `Research/BatmobileGrab/BMSDK_OFFSETS.json` | `SVehicleWheel` carries `Steer` @100, `SteerFactor` @120, `SkelControlName` @124, `WheelControl` @132 (`SkelControlWheel`), `BoneName` @548, `WheelSteering`/`WheelSteeringAxis`/`SteerWheelBoneIndex` (Engine). `SVehicleSimCar` carries `MaxSteerAngleCurve` @200, `SteerSpeed` @220, `ActualSteering` @248, `ActualSteeringOrigin` @256. `RVehicleSimBatmobile` carries the battle-mode steering curves. **No class or member for a driver's yoke** |

## 2. What the `steer` hits actually are

Across the 324 packages the only `steer`-named entries are:

- **simulation parameters** — `SVehicleWheel.Steer`, `SteerFactor`, `bSteerable`, `SteerWheelBoneIndex`,
  `WheelSteering`, `WheelSteeringAxis`, `WheelSteeringVisualLimitDeg`, `bInvertWheelSteering`;
  `SVehicleSimCar.ActualSteering`, `ActualSteeringOrigin`, `SteerSpeed`, `MaxSteerAngleCurve`;
  `RVehicleSimBatmobile.StandardSteeringSpeedCurve`, `BattleModeMaxSteering`,
  `BattleModeSteerAngleFactor`, `BattleModeTrailingSteerFactor*`, `FrontWheelSteerPct`,
  `RearWheelSteerPct`, `BattleModeSteerBiasRate`; `RVehicleSimCar.NumWheelsForFullSteering`,
  `SteeringReductionFactor`, `SteerSpeedVsSpeedCurve`; `SVehicle.OutputSteering`,
  `NoVisualSteeringFront/Rear`; `Vehicle.Steering`, `OldSteering`, `OnlySteeringStartTime`;
- **audio** — `Play_Batmobile_Steering_Bed` (`AkEvent`), `BML_Steering`,
  `BML_Steering_Cornering`, `BML_Steering_Rotation`, `Speed_Steering` (`AkParameterName`);
- **cinematic/interp** — `RInterpTrackVehicleSteering`, `RInterpTrackInstVehicleSteering`;
- **camera and UI/tutorial** — `DrivingModeSteeringCamFactor*`, `SteerLR`/`SteerUD`, glide-prompt
  counters, `bDisplaySixaxisSteerTutorial`;
- **driver/passenger transition anims on a seat, not a wheel** — `Car_Driver_Steering_Right_To_Left`,
  `Car_Passenger_Steering_Right_To_Left`, `Car_BackLeftSeat_Steering_Right_To_Left`,
  `Steering_Left_To_Right` (body animations of a character turning, not a wheel mesh).

`Playable_Batmobile_SF.upk` itself (17,916,421 B, 3,151 names, 5,490 exports) holds 12 `steer` names —
all sim curves, AkEvents/AkParameterNames and `SteeringArray` — and its only skeletal-control names are
`RSkelControl_FeedConstraint`, `SkelControlLists`, `SkelControls`.

## 3. How BmAK's road wheels are actually turned (the nearest real mechanism)

1. The sim computes a steer value: `SVehicleSimCar.ActualSteering` (BmSDK offset 248) from
   `SteerSpeed` (220) and `MaxSteerAngleCurve` (200); `RVehicleSimBatmobile` adds the battle-mode
   curves and `FrontWheelSteerPct`/`RearWheelSteerPct` (948/952).
2. Each wheel is an `SVehicleWheel` with `Steer` (100) and `SteerFactor` (120), and its **visual** is
   bound through `SkelControlName` (124) and `WheelControl` (132, class `SkelControlWheel`), acting on
   `BoneName` (548).
3. BmAK's Batmobile-specific control class for that is `RSkelControlBatmobileWheel` — present as a
   class default in `BmGame.upk` and as 5 exports across the scanned packages.

That is a **named skeletal control per wheel**, driven by a sim float. It is not an AnimTree node
animation, it is not script-driven per bone, and there is no equivalent for a driver's steering wheel:
no control class, no bone, no mesh.

## 4. Consequence for P-13 in the build

- The T-8 row stands as written: **no joint bone** (`—`), **static**, reason "no bone carries this
  part". The Batmobile also has **no yoke geometry** to carry, so there is nothing to animate even if a
  bone existed (COCKPIT.md).
- The JC3-side mechanism a yoke *would* use is the shipped `SteeringWheel` moving-part behaviour with
  `target_position_variable` = `steering_turn`: 20 rows over `CBoat`/`CCar`, proven-on-CCar
  (`Research/JC3Grab/MOVING_PARTS.md:132`), carried by 9 chassis — 8 cars plus `v1302` sailboat
  (`GRAB_BACKLOG.md:306`). It is a **variable-driven hinge**, not an animation, mirroring BmAK's
  sim-float approach rather than any BmAK animation.
- Therefore ANI-7 ("steering yoke turns with steering") cannot be satisfied from BmAK files. It needs a
  new part, a pivot/bone in the body mesh and a `SteeringWheel` behaviour row bound to `steering_turn` —
  a build decision, not a translation this card can make. Nothing here was changed.

## 5. UNKNOWNs and coverage limits

1. **Coverage of the package search.** 324 packages searched (all `Playable_*`, all `Showcase_*`,
   `BmGame.upk`, `Engine.upk`) out of 3,287 files in `BmGame/CookedPCConsole`, plus DLC trees not
   searched. A yoke asset in an unscanned gameplay/DLC package would not have been seen. Name tables
   only were searched, not every object's property payload.
2. **Whether BmAK binds `RSkelControlBatmobileWheel` to specific wheels** — that needs the property
   payload of an `SVehicleWheel` archetype decoded; this page only proves the class, the members and
   the binding fields exist.
3. **The rate** at which JC3 drives `steering_turn` — code-side, not in the files (T-8 §UNKNOWN 1).
4. **`SteerWheelBoneIndex`'s semantics** (which wheel/bone it names) is not decoded here; it belongs to
   the road-wheel chain in `Engine.upk`, not to a driver yoke, by the absence in §1.

## 6. Reproduce

```
python -c "import sys;sys.path.insert(0,'Tools/scripts');import upk_read as U;p=U.Package(r'E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole/Playable_Batmobile_SF.upk');print([n for n in p.names if 'steer' in n.lower() or 'yoke' in n.lower()])"
python tmp/freebuff/scratch/p13_probe.py --json tmp/freebuff/scratch/p13_upk.json \
  "E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole/Playable_*.upk" \
  "E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole/Showcase_*.upk" \
  "E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole/BmGame.upk" \
  "E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole/Engine.upk"
```

Read-only throughout: `upk_read.Package` opens the packages and parses their tables; no package, build
or research file was written.
