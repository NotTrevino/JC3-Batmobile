**STATUS: DONE — mechanism answered as an absence, not a bone.** BmAK has no steering-wheel bone, no steering-wheel geometry and no steering-wheel asset for the Batmobile, and none in the 324 cooked packages searched; the only BmAK steering mechanism is the road-wheel chain (`SVehicleWheel.Steer` → `SVehicleWheel.SkelControlName`/`WheelControl` = `SkelControlWheel`, with `RSkelControlBatmobileWheel` in `BmGame.upk`). Page: `Working/Translation/P13_STEERING.md`.

# P-13 — steering wheel: report

**Answer to the question as asked ("bone name / skeletal control / script rotation / AnimTree node"):**
`UNKNOWN` on the BmAK side in the sense that no such carrier exists for a driver's wheel, and **proven
absent** for the asset. The Batmobile rig has 0 steering/yoke bones, 253 sequences with 0 steering
tracks, 3 AnimTrees whose only skeletal controls are `RSkelControl_FeedConstraint` on three
non-interior bones, and 4 faces of geometry inside the driver hand box. The nearest BmAK mechanism is
the road-wheel one, which does not transfer.

## Evidence chain (each claim, its file)

| claim | evidence |
|---|---|
| no steering bone | `Research/BatmobileGrab/BONES.json` — 180 bones; 0 match `steer|yoke`; the 45 wheel/cockpit/driver matches are road wheels, the cockpit shell and wheel arches |
| no steering animation | `Research/BatmobileGrab/ANIMATIONS.json` — 253 sequences, 13 sets, 3 AnimTrees, 0 steering names, 0 steering track bones |
| no AnimTree/skel-control carrier | `ANIMATIONS.json` `trees[]` — `AnimNodeSequence` children only; controls are 3× `RSkelControl_FeedConstraint` (`Flappy_Rear_Door_Btm_Rot`, `*_Power_Cell`) |
| no yoke geometry | `Research/BatmobileGrab/COCKPIT.md:24,94` — hand box holds 4 faces; nearest driver surface is the instrument panel at z −1.5097 |
| no steering-wheel asset in the cooked packages | `upk_read.Package` over 324 packages (all `Playable_*`, all `Showcase_*`, `BmGame.upk`, `Engine.upk`): 0 name-table entries containing `yoke` or `steeringwheel`; `steer` hits are sim members, audio params, interp tracks, camera/UI and seat transition anims |
| the road-wheel mechanism | `BMSDK_OFFSETS.json`: `SVehicleWheel` `Steer` @100, `SteerFactor` @120, `SkelControlName` @124, `WheelControl` @132 (`SkelControlWheel`), `BoneName` @548; `SVehicleSimCar` `MaxSteerAngleCurve` @200, `SteerSpeed` @220, `ActualSteering` @248. Class inventory: `RSkelControlBatmobileWheel` 5, `SkelControlWheel` 25, `RSkelControlTankTrack` 1 |
| the JC3-side carrier | `Research/JC3Grab/MOVING_PARTS.md:132` (`SteeringWheel`, hinged, `steering_turn`, 20 rows, proven-on-CCar) and `GRAB_BACKLOG.md:306` (9 chassis: 8 cars + `v1302` sailboat) |
| why the T-8 row is static | `Working/Translation/T8_PARTS.md:230-239` (P-13 `no part`, no bone) and `PARTS_ANIM_COVERAGE.md:35,45` |

## Routes tried (all read-only)

1. Local files first: `BONES.json`, `ANIMATIONS.json`, `PARTS_ANIM_COVERAGE.md`, `T8_PARTS.md`,
   `COCKPIT.md`, `MOVING_PARTS.md`, `GRAB_BACKLOG.md`.
2. Cooked packages with `Tools/scripts/upk_read.py`: a scratch probe
   (`tmp/freebuff/scratch/p13_probe.py`) parsed name/export/import tables and class inventories of 324
   packages, 0 errors; JSON at `tmp/freebuff/scratch/p13_upk.json`, log at `…/p13_probe.log`.
3. BmSDK layouts: `BMSDK_OFFSETS.json` (41 classes) — full `SVehicleWheel` property table read, plus a
   sweep of every member whose name contains `steer`/`wheel` across `SVehicle*`, `RVehicle*`,
   `RVehicleSim*`.

## UNKNOWNs

- A yoke asset in an **unscanned** package (3,287 files exist in `CookedPCConsole`; DLC trees not
  searched) would not have been seen. Name tables only were searched, not every property payload.
- Whether BmAK actually binds `RSkelControlBatmobileWheel` to specific wheels (needs an
  `SVehicleWheel` archetype's property payload decoded).
- The rate at which JC3 drives `steering_turn` — code-side, absent from the files.
- `SteerWheelBoneIndex` semantics — belongs to the road-wheel chain by the absence above.

## Deliverables and side effects

- `Working/Translation/P13_STEERING.md` (new page).
- `tmp/freebuff/reports/steering-wheel-p13.md` (this report).
- Scratch only: `tmp/freebuff/scratch/p13_probe.py`, `p13_upk.json`, `p13_probe.log`.
- No script, build, research record or game file was edited; the game packages were opened read-only.
