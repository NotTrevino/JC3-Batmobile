# Interaction points and stunt areas (G2-18)

Every interaction object in the Serpente donor `.epe`, its animation/state strings, and the
`StuntAreas` module decoded from the entity cache - then each object placed on the
**Batmobile** body with a surface verdict. Rebuilt by
`python Tools/scripts/jc3interact.py --check`; no archive is opened and no game is launched.

## 1. The two frames

| frame | x | y | z | source |
|---|---|---|---|---|
| Serpente deform envelope | -1.330 … 1.330 | 0.000 … 1.524 | -2.560 … 2.527 | `DeformPoints.points[i].start_transform[12..14]`, 135 points |
| Serpente mesh union | -1.062 … 1.062 | -0.429 … 1.511 | -2.570 … 2.564 | union of the 198 part-mesh AABBs |
| Batmobile body | -1.747 … 1.748 | 0.091 … 2.362 | -3.420 … 3.605 | `Working/TrueScale/stations.json` |

The deform envelope and the mesh union agree in **z** (the longitudinal axis) and the
envelope is the wider in x because bumper corners deform; the envelope is used as the
Serpente frame because all 135 points are provably in one space (they carry part bindings).

| wheel stations | Serpente | Batmobile |
|---|---|---|
| wheelbase | 3.003 m | 5.0289 m |
| track | 1.77 m | 2.416 / 2.569 m |

Mapping (analysis only, **not** the R2 build transform): `u = (p - serpente_min) / (serpente_size); p' = bat_min + u * bat_size` - per-axis scale **1.3139 / 1.49 / 1.3809**. The build keeps one transform for assets
(`bat_assemble.py` `T(p)`); nothing here moves a mesh.

## 2. Every interaction object

**85 objects** in the donor `.epe` match the six prefixes: `entry.*` 29, `exit.*` 26, `interaction.*` 3, `point.*` 8, `transition.*` 12, `trigger.*` 7.

Only `point.*` and `trigger.*` carry their own `world` matrix (15 of 85); the rest **inherit** the transform of the graph node they hang under (70), which is
recorded per object as `world_source` / `world_from`. 0 objects have no transform at all.

### Positions, Serpente space and Batmobile verdict

| object | class | state | transform | Serpente xyz | Batmobile xyz | wheelfrac | surface m | verdict |
|---|---|---|---|---|---|---|---|---|
| `interaction.seat.driver` | `CInteraction` | `-` | inherited: `context` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.driver` | `CInteractionGraphEntry` | `S_ENTER_DRIVER_VEHICLE` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `point.driver` | `CInteractionGraphPointNode` | `-` | own | -0.440, 0.340, 0.200 | -0.578, 0.598, 0.392 | 0.585 | 0.0428 | **inside** |
| `exit.driver.default` | `CInteractionGraphExit` | `S_EXIT_VEHICLE` | inherited: `point.driver` | -0.440, 0.340, 0.200 | -0.578, 0.598, 0.392 | 0.585 | 0.0428 | **inside** |
| `exit.ai.driver.default` | `CInteractionGraphExit` | `S_EXIT_VEHICLE` | inherited: `point.driver` | -0.440, 0.340, 0.200 | -0.578, 0.598, 0.392 | 0.585 | 0.0428 | **inside** |
| `transition.passenger1` | `CInteractionGraphTransition` | `-` | inherited: `point.driver` | -0.440, 0.340, 0.200 | -0.578, 0.598, 0.392 | 0.585 | 0.0428 | **inside** |
| `exit.ai.driver.to.hood` | `CInteractionGraphExit` | `S_EXIT_DRIVER_TO_HOOD_VEHICLE` | inherited: `point.driver` | -0.440, 0.340, 0.200 | -0.578, 0.598, 0.392 | 0.585 | 0.0428 | **inside** |
| `exit.driver.roll.out` | `CInteractionGraphExit` | `S_ROLL_OUT_EXIT_VEHICLE` | inherited: `point.driver` | -0.440, 0.340, 0.200 | -0.578, 0.598, 0.392 | 0.585 | 0.0428 | **inside** |
| `exit.driver.moving.parachute` | `CInteractionGraphExit` | `S_EXIT_VEHICLE_PARA` | inherited: `point.driver` | -0.440, 0.340, 0.200 | -0.578, 0.598, 0.392 | 0.585 | 0.0428 | **inside** |
| `exit.ai.driver.default90R` | `CInteractionGraphExit` | `S_EXIT_VEHICLE_90R` | inherited: `point.driver` | -0.440, 0.340, 0.200 | -0.578, 0.598, 0.392 | 0.585 | 0.0428 | **inside** |
| `exit.driver.pushed.out` | `CInteractionGraphExit` | `S_PUSHED_OUT_VEHICLE` | inherited: `point.driver` | -0.440, 0.340, 0.200 | -0.578, 0.598, 0.392 | 0.585 | 0.0428 | **inside** |
| `exit.ai.driver.default90L` | `CInteractionGraphExit` | `S_EXIT_VEHICLE_90L` | inherited: `point.driver` | -0.440, 0.340, 0.200 | -0.578, 0.598, 0.392 | 0.585 | 0.0428 | **inside** |
| `exit.driver.to.fall` | `CInteractionGraphExit` | `S_EXIT_VEHICLE_TO_FALL` | inherited: `point.driver` | -0.440, 0.340, 0.200 | -0.578, 0.598, 0.392 | 0.585 | 0.0428 | **inside** |
| `exit.ai.driver.default180` | `CInteractionGraphExit` | `S_EXIT_VEHICLE_180` | inherited: `point.driver` | -0.440, 0.340, 0.200 | -0.578, 0.598, 0.392 | 0.585 | 0.0428 | **inside** |
| `exit.driver.to.swim` | `CInteractionGraphExit` | `S_EXIT_DRIVER_VEHICLE_IN_WATER` | inherited: `point.driver` | -0.440, 0.340, 0.200 | -0.578, 0.598, 0.392 | 0.585 | 0.0428 | **inside** |
| `transition.stunt` | `CInteractionGraphTransition` | `-` | inherited: `point.driver` | -0.440, 0.340, 0.200 | -0.578, 0.598, 0.392 | 0.585 | 0.0428 | **inside** |
| `exit.ai.driver.default0` | `CInteractionGraphExit` | `S_EXIT_VEHICLE_0` | inherited: `point.driver` | -0.440, 0.340, 0.200 | -0.578, 0.598, 0.392 | 0.585 | 0.0428 | **inside** |
| `exit.driver.pulled.out` | `CInteractionGraphExit` | `S_PULLED_OUT_VEHICLE` | inherited: `point.driver` | -0.440, 0.340, 0.200 | -0.578, 0.598, 0.392 | 0.585 | 0.0428 | **inside** |
| `transition.passenger1.exit` | `CInteractionGraphTransition` | `-` | inherited: `point.driver` | -0.440, 0.340, 0.200 | -0.578, 0.598, 0.392 | 0.585 | 0.0428 | **inside** |
| `exit.driver.upside.down` | `CInteractionGraphExit` | `S_EXIT_DRIVER_VEHICLE_UPSIDE_DOWN` | inherited: `point.driver` | -0.440, 0.340, 0.200 | -0.578, 0.598, 0.392 | 0.585 | 0.0428 | **inside** |
| `point.passenger1.onground` | `CInteractionGraphPointNode` | `-` | own | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | 0.518 | 0.333 | **floating** |
| `transition.passenger1` | `CInteractionGraphTransition` | `-` | inherited: `point.passenger1.onground` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | 0.518 | 0.333 | **floating** |
| `transition.passenger1.side` | `CInteractionGraphTransition` | `-` | inherited: `point.passenger1.onground` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | 0.518 | 0.333 | **floating** |
| `entry.ai.passenger1` | `CInteractionGraphEntry` | `S_ENTER_PASSENGER_VEHICLE` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.jump_to_stunt_vehicle_to_vehicle` | `CInteractionGraphEntry` | `S_STUNT_TO_JUMP_VEHICLE_TO_VEHICLE` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.driver.pull.out.onground.no.door` | `CInteractionGraphEntry` | `S_ENTER_ON_GROUND_THROW_OUT_NO_DOOR_VEHICLE` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `point.stunt` | `CInteractionGraphPointNode` | `-` | own | 0.000, 1.488, 0.422 | 0.001, 2.307, 0.698 | 0.659 | 0.3494 | **floating** |
| `exit.from.stunt` | `CInteractionGraphExit` | `S_STUNT_EXIT_VEHICLE` | inherited: `point.stunt` | 0.000, 1.488, 0.422 | 0.001, 2.307, 0.698 | 0.659 | 0.3494 | **floating** |
| `point.passenger1.side` | `CInteractionGraphPointNode` | `-` | own | -0.180, 1.490, 1.010 | -0.236, 2.311, 1.510 | 0.855 | 0.1887 | **floating** |
| `transition.passenger1` | `CInteractionGraphTransition` | `-` | inherited: `point.passenger1.side` | -0.180, 1.490, 1.010 | -0.236, 2.311, 1.510 | 0.855 | 0.1887 | **floating** |
| `transition.stunt` | `CInteractionGraphTransition` | `-` | inherited: `point.passenger1.side` | -0.180, 1.490, 1.010 | -0.236, 2.311, 1.510 | 0.855 | 0.1887 | **floating** |
| `entry.pull.up.to.stunt.hood.close` | `CInteractionGraphEntry` | `S_PULL_UP_TO_STUNT_CLOSE_VEHICLE` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.stunt.to.driver.side.enter.vehicle2` | `CInteractionGraphEntry` | `S_ENTER_STUNT_TO_DRIVER_SIDE_VEHICLE` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.stunt.to.driver.side.enter.vehicle3` | `CInteractionGraphEntry` | `S_ENTER_STUNT_TO_DRIVER_SIDE_VEHICLE` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.passenger1.no.door` | `CInteractionGraphEntry` | `S_ENTER_PASSENGER_NO_DOOR_VEHICLE` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.reel.to.stunt.hood` | `CInteractionGraphEntry` | `S_GRAPPLE_REEL_TO_STUNT_LAND` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.reel.to.stunt.main` | `CInteractionGraphEntry` | `S_GRAPPLE_REEL_TO_STUNT_LAND` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.passenger1.pull.out.onground` | `CInteractionGraphEntry` | `S_ENTER_PASSENGER_ON_GROUND_THROW_OUT_VEHICLE` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.pull.up.to.stunt.hood.far` | `CInteractionGraphEntry` | `S_PULL_UP_TO_STUNT_FAR_VEHICLE` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.passenger1.side.fast` | `CInteractionGraphEntry` | `S_PASSENGER_ON_GROUND_TO_ENTER_SIDE_VEHICLE` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.step.over.low.stunt.hood` | `CInteractionGraphEntry` | `S_STEP_OVER_LOW_TO_STUNT_VEHICLE_P1` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.pull.up.to.stunt.close` | `CInteractionGraphEntry` | `S_PULL_UP_TO_STUNT_CLOSE_VEHICLE` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.jump_to_stunt` | `CInteractionGraphEntry` | `S_JUMP_TO_STUNT_VEHICLE` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.driver.locked.onground` | `CInteractionGraphEntry` | `S_ENTER_ON_GROUND_UNLOCK_VEHICLE` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `point.passenger1` | `CInteractionGraphPointNode` | `-` | own | 0.442, 0.340, 0.200 | 0.582, 0.598, 0.392 | 0.585 | 0.0483 | **inside** |
| `exit.passenger1.default` | `CInteractionGraphExit` | `S_EXIT_VEHICLE` | inherited: `point.passenger1` | 0.442, 0.340, 0.200 | 0.582, 0.598, 0.392 | 0.585 | 0.0483 | **inside** |
| `exit.passenger1.roll.out` | `CInteractionGraphExit` | `S_ROLL_OUT_EXIT_VEHICLE` | inherited: `point.passenger1` | 0.442, 0.340, 0.200 | 0.582, 0.598, 0.392 | 0.585 | 0.0483 | **inside** |
| `exit.ai.passenger1.default90L` | `CInteractionGraphExit` | `S_EXIT_VEHICLE_90L` | inherited: `point.passenger1` | 0.442, 0.340, 0.200 | 0.582, 0.598, 0.392 | 0.585 | 0.0483 | **inside** |
| `exit.ai.passenger1.default180` | `CInteractionGraphExit` | `S_EXIT_VEHICLE_180` | inherited: `point.passenger1` | 0.442, 0.340, 0.200 | 0.582, 0.598, 0.392 | 0.585 | 0.0483 | **inside** |
| `exit.ai.passenger1.default` | `CInteractionGraphExit` | `S_EXIT_VEHICLE` | inherited: `point.passenger1` | 0.442, 0.340, 0.200 | 0.582, 0.598, 0.392 | 0.585 | 0.0483 | **inside** |
| `transition.driver` | `CInteractionGraphTransition` | `-` | inherited: `point.passenger1` | 0.442, 0.340, 0.200 | 0.582, 0.598, 0.392 | 0.585 | 0.0483 | **inside** |
| `exit.passenger1.upside.down` | `CInteractionGraphExit` | `S_EXIT_PASSENGER_VEHICLE_UPSIDE_DOWN` | inherited: `point.passenger1` | 0.442, 0.340, 0.200 | 0.582, 0.598, 0.392 | 0.585 | 0.0483 | **inside** |
| `exit.ai.passenger1.default0` | `CInteractionGraphExit` | `S_EXIT_VEHICLE_0` | inherited: `point.passenger1` | 0.442, 0.340, 0.200 | 0.582, 0.598, 0.392 | 0.585 | 0.0483 | **inside** |
| `exit.passenger1.pulled.out` | `CInteractionGraphExit` | `S_PULLED_OUT_VEHICLE` | inherited: `point.passenger1` | 0.442, 0.340, 0.200 | 0.582, 0.598, 0.392 | 0.585 | 0.0483 | **inside** |
| `exit.ai.passenger1.to.hood` | `CInteractionGraphExit` | `S_EXIT_DRIVER_TO_HOOD_VEHICLE` | inherited: `point.passenger1` | 0.442, 0.340, 0.200 | 0.582, 0.598, 0.392 | 0.585 | 0.0483 | **inside** |
| `exit.ai.passenger1.default90R` | `CInteractionGraphExit` | `S_EXIT_VEHICLE_90R` | inherited: `point.passenger1` | 0.442, 0.340, 0.200 | 0.582, 0.598, 0.392 | 0.585 | 0.0483 | **inside** |
| `entry.passenger1.pull.out.onground.no.door` | `CInteractionGraphEntry` | `S_ENTER_PASSENGER_ON_GROUND_THROW_OUT_NO_DOOR_VEHICLE` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.passenger1` | `CInteractionGraphEntry` | `S_ENTER_PASSENGER_VEHICLE` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.step.over.high.stunt` | `CInteractionGraphEntry` | `S_STEP_OVER_HIGH_TO_STUNT_VEHICLE_P1` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `point.stunt.hood` | `CInteractionGraphPointNode` | `-` | own | 0.000, 1.051, -1.505 | 0.001, 1.656, -1.963 | 0.017 | 0.0405 | **floating** |
| `exit.from.stunt.hood` | `CInteractionGraphExit` | `S_STUNT_EXIT_VEHICLE` | inherited: `point.stunt.hood` | 0.000, 1.051, -1.505 | 0.001, 1.656, -1.963 | 0.017 | 0.0405 | **floating** |
| `point.driver.onground` | `CInteractionGraphPointNode` | `-` | own | -1.330, 0.000, 0.770 | -1.747, 0.091, 1.179 | 0.775 | 0.4448 | **floating** |
| `transition.driver` | `CInteractionGraphTransition` | `-` | inherited: `point.driver.onground` | -1.330, 0.000, 0.770 | -1.747, 0.091, 1.179 | 0.775 | 0.4448 | **floating** |
| `transition.driver.side` | `CInteractionGraphTransition` | `-` | inherited: `point.driver.onground` | -1.330, 0.000, 0.770 | -1.747, 0.091, 1.179 | 0.775 | 0.4448 | **floating** |
| `entry.driver.pull.out.onground` | `CInteractionGraphEntry` | `S_ENTER_ON_GROUND_THROW_OUT_VEHICLE` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.stunt.to.driver.side.enter.vehicle` | `CInteractionGraphEntry` | `S_ENTER_STUNT_TO_TRANS_ENTER_VEHICLE_P1` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.step.over.low.stunt` | `CInteractionGraphEntry` | `S_STEP_OVER_LOW_TO_STUNT_VEHICLE_P1` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.passenger1.locked.onground` | `CInteractionGraphEntry` | `S_ENTER_PASSENGER_ON_GROUND_UNLOCK_VEHICLE` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.step.over.high.stunt.hood` | `CInteractionGraphEntry` | `S_STEP_OVER_HIGH_TO_STUNT_VEHICLE_P1` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.ai.driver.left` | `CInteractionGraphEntry` | `S_ENTER_DRIVER_VEHICLE` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.pull.up.to.stunt.far` | `CInteractionGraphEntry` | `S_PULL_UP_TO_STUNT_FAR_VEHICLE` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `entry.driver.side.fast` | `CInteractionGraphEntry` | `S_ON_GROUND_TO_ENTER_DRIVER_SIDE_VEHICLE` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `point.driver.side` | `CInteractionGraphPointNode` | `-` | own | -0.260, 1.470, 0.370 | -0.341, 2.281, 0.626 | 0.642 | 0.3779 | **floating** |
| `transition.driver` | `CInteractionGraphTransition` | `-` | inherited: `point.driver.side` | -0.260, 1.470, 0.370 | -0.341, 2.281, 0.626 | 0.642 | 0.3779 | **floating** |
| `transition.stunt` | `CInteractionGraphTransition` | `-` | inherited: `point.driver.side` | -0.260, 1.470, 0.370 | -0.341, 2.281, 0.626 | 0.642 | 0.3779 | **floating** |
| `entry.driver.no.door` | `CInteractionGraphEntry` | `S_ENTER_DRIVER_NO_DOOR_VEHICLE` | inherited: `graph` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `trigger.driver` | `CInteractionTrigger` | `-` | own | -1.480, -0.117, 0.287 | -1.944, -0.083, 0.512 | 0.614 | 0.7832 | **floating** |
| `trigger.step.to.stunt` | `CInteractionTrigger` | `-` | own | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | 0.518 | 0.333 | **floating** |
| `trigger.driver.fast` | `CInteractionTrigger` | `-` | own | -1.621, -0.161, 0.896 | -2.129, -0.148, 1.353 | 0.817 | 0.8435 | **floating** |
| `interaction.seat.stunt` | `CInteraction` | `-` | inherited: `context` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `trigger.passenger1` | `CInteractionTrigger` | `-` | own | 1.480, -0.117, 0.287 | 1.945, -0.083, 0.512 | 0.614 | 0.7839 | **floating** |
| `trigger.stunt.vehicle.to.vehicle` | `CInteractionTrigger` | `-` | own | -0.410, 1.650, -0.090 | -0.538, 2.549, -0.009 | 0.489 | 0.6704 | **floating** |
| `interaction.seat.passenger1` | `CInteraction` | `-` | inherited: `context` | 0.000, 0.000, 0.000 | 0.001, 0.091, 0.115 | - | - | **n/a (container origin)** |
| `trigger.stationary.stunt` | `CInteractionTrigger` | `-` | own | -0.028, 1.268, -0.097 | -0.037, 1.980, -0.018 | 0.486 | 0.0646 | **floating** |
| `trigger.stunt` | `CInteractionTrigger` | `-` | own | -0.410, 1.650, -0.090 | -0.538, 2.549, -0.009 | 0.489 | 0.6704 | **floating** |

Verdict rule: **on-surface** = nearest Batmobile triangle ≤ 0.03 m; otherwise **inside** if three-ray parity says the point
is within the shell, else **floating**. An object that only inherits the identity matrix of
the `graph` or `context` container has **no position of its own** - its placement is defined
by the point it transitions from - so it is marked `n/a (container origin)` rather than
given a fake verdict at 0,0,0.
`wheelbase_fraction` is 0 at the front axle and 1 at
the rear axle (negative = ahead of the front axle); `surface_m` is unsigned distance to the
nearest triangle.

### Triggers

`trigger.*` is the only class with a **scaled** transform, i.e. a volume rather than a point:

| trigger | scale (half-extent x,y,z) | position | note |
|---|---|---|---|
| `trigger.driver` | 2.650, 1.910, 2.830 | -1.480, -0.117, 0.287 |  |
| `trigger.step.to.stunt` | 10.000, 10.000, 10.000 | 0.000, 0.000, 0.000 |  |
| `trigger.driver.fast` | 3.690, 1.776, 6.748 | -1.621, -0.161, 0.896 |  |
| `trigger.passenger1` | 2.650, 1.910, 2.830 | 1.480, -0.117, 0.287 |  |
| `trigger.stunt.vehicle.to.vehicle` | 19.120, 14.110, 23.410 | -0.410, 1.650, -0.090 |  |
| `trigger.stationary.stunt` | 1.948, 1.596, 5.116 | -0.028, 1.268, -0.097 |  |
| `trigger.stunt` | 14.320, 9.310, 18.610 | -0.410, 1.650, -0.090 |  |

### States and interaction names

| state string | objects |
|---|---|
| `S_EXIT_VEHICLE` | 4 |
| `S_ENTER_DRIVER_VEHICLE` | 2 |
| `S_ENTER_PASSENGER_VEHICLE` | 2 |
| `S_ENTER_STUNT_TO_DRIVER_SIDE_VEHICLE` | 2 |
| `S_EXIT_DRIVER_TO_HOOD_VEHICLE` | 2 |
| `S_EXIT_VEHICLE_0` | 2 |
| `S_EXIT_VEHICLE_180` | 2 |
| `S_EXIT_VEHICLE_90L` | 2 |
| `S_EXIT_VEHICLE_90R` | 2 |
| `S_GRAPPLE_REEL_TO_STUNT_LAND` | 2 |
| `S_PULLED_OUT_VEHICLE` | 2 |
| `S_PULL_UP_TO_STUNT_CLOSE_VEHICLE` | 2 |
| `S_PULL_UP_TO_STUNT_FAR_VEHICLE` | 2 |
| `S_ROLL_OUT_EXIT_VEHICLE` | 2 |
| `S_STEP_OVER_HIGH_TO_STUNT_VEHICLE_P1` | 2 |
| `S_STEP_OVER_LOW_TO_STUNT_VEHICLE_P1` | 2 |
| `S_STUNT_EXIT_VEHICLE` | 2 |
| `S_ENTER_DRIVER_NO_DOOR_VEHICLE` | 1 |
| `S_ENTER_ON_GROUND_THROW_OUT_NO_DOOR_VEHICLE` | 1 |
| `S_ENTER_ON_GROUND_THROW_OUT_VEHICLE` | 1 |
| `S_ENTER_ON_GROUND_UNLOCK_VEHICLE` | 1 |
| `S_ENTER_PASSENGER_NO_DOOR_VEHICLE` | 1 |
| `S_ENTER_PASSENGER_ON_GROUND_THROW_OUT_NO_DOOR_VEHICLE` | 1 |
| `S_ENTER_PASSENGER_ON_GROUND_THROW_OUT_VEHICLE` | 1 |
| `S_ENTER_PASSENGER_ON_GROUND_UNLOCK_VEHICLE` | 1 |
| `S_ENTER_STUNT_TO_TRANS_ENTER_VEHICLE_P1` | 1 |
| `S_EXIT_DRIVER_VEHICLE_IN_WATER` | 1 |
| `S_EXIT_DRIVER_VEHICLE_UPSIDE_DOWN` | 1 |
| `S_EXIT_PASSENGER_VEHICLE_UPSIDE_DOWN` | 1 |
| `S_EXIT_VEHICLE_PARA` | 1 |
| `S_EXIT_VEHICLE_TO_FALL` | 1 |
| `S_JUMP_TO_STUNT_VEHICLE` | 1 |
| `S_ON_GROUND_TO_ENTER_DRIVER_SIDE_VEHICLE` | 1 |
| `S_PASSENGER_ON_GROUND_TO_ENTER_SIDE_VEHICLE` | 1 |
| `S_PUSHED_OUT_VEHICLE` | 1 |
| `S_STUNT_TO_JUMP_VEHICLE_TO_VEHICLE` | 1 |

`interaction` is an object hash (`00000000` on every entry/exit), and 9 exits carry a
`modifier`; both are recorded verbatim in `INTERACTION.json`.

### Source and cross-check

The hierarchy comes from `Research/Epe/serpente_civilian.xml` (nested `<object>` elements =
the real tree). The decoded `detail/*.ee.json` is the **value cross-check**:
**79** distinct prefixed names on the JSON side (fewer than 85
objects because `transition.passenger1` / `transition.stunt` / `transition.driver` each
appear under more than one point node). World and state strings agree for every object:
**True**, and JSON lacks a `world` the XML has for
`trigger.driver.fast`, `trigger.stationary.stunt`.
they collapse unnamed siblings into `?` (26 duplicate paths over 450 objects), which is why
the XML tree is authoritative here.

## 3. Stunt areas - the surfaces Rico can stand on

`StuntAreas` declares **3 areas** (`number_of_stunt_areas`) inside a
**32-slot** array; 29 slots are empty `NoName` placeholders. The
module also carries 64 `welding_info` rows, of which only
**8 are real welds** (the rest are `-1` filler) joining
areas 0/1 x6, areas 0/2 x1, areas 1/2 x1. Each active area is a real triangle surface
(`vertices3D_local` + `triangle_indices`), not an AABB:

| slot | name | part | points | triangles | valid edges | size x,y,z (m) | centre |
|---|---|---|---|---|---|---|---|
| 0 | `front_area` | `sportsmuscle_hood` | 6 | 4 | 6 | 1.673, 0.186, 1.330 | -0.000, 1.022, -1.588 |
| 1 | `front_signature_area` | `sportsmuscle_hood_signature` | 6 | 4 | 6 | 1.673, 0.186, 1.330 | -0.000, 1.022, -1.588 |
| 2 | `main_area` | `sportsmuscle_body` | 10 | 8 | 10 | 1.646, 0.420, 3.337 | 0.000, 1.314, 0.746 |

Where each surface lands on the Batmobile:

Two centres, because the module ships one and the vertices give another: `center_local`
is the file's own field, the geometric centroid is what the surface actually spans, and
they sit up to 0.1474 m apart.

| area | `center_local` on Batmobile | verdict | m | vertex centroid on Batmobile | verdict | m | vertices on-surface | worst vertex m |
|---|---|---|---|---|---|---|---|---|
| `front_area` | 0.001, 1.614, -2.077 | **floating** | 0.1035 | 0.001, 1.639, -2.140 | **floating** | 0.1512 | 0/6 | 0.374 |
| `front_signature_area` | 0.001, 1.614, -2.077 | **floating** | 0.1035 | 0.001, 1.639, -2.140 | **floating** | 0.1512 | 0/6 | 0.374 |
| `main_area` | 0.001, 2.049, 1.145 | **on-surface** | 0.0197 | 0.001, 1.982, 1.339 | **floating** | 0.0746 | 0/10 | 0.5955 |

The `front_area` and `front_signature_area` slots are **coincident** (identical vertices,
triangles and bbox) - they differ only in which part they bind (`sportsmuscle_hood` vs
`sportsmuscle_hood_signature`), so one hood surface serves two part ids. The
`main_area` is the roof/trunk deck. Read the two verdict columns together:

- `front_area`: `center_local` -> **floating** (0.1035 m); vertex centroid -> **floating** (0.1512 m); worst vertex 0.374 m - the surface is *tilted* against the shell,
  not uniformly lifted.
- `front_signature_area`: `center_local` -> **floating** (0.1035 m); vertex centroid -> **floating** (0.1512 m); worst vertex 0.374 m - the surface is *tilted* against the shell,
  not uniformly lifted.
- `main_area`: `center_local` -> **on-surface** (0.0197 m); vertex centroid -> **floating** (0.0746 m); worst vertex 0.5955 m - the surface is *tilted* against the shell,
  not uniformly lifted.

The gap is the point of the exercise: a bbox-scaled copy lands close enough to *look* right
at the centre and is tens of centimetres out at its edges. A build has to re-fit the
vertices against the Batmobile mesh, not scale them.

## 4. What WLD-3/4 and MOD-3/4 can use

- The **graph** is portable: `entry.*` → `point.*` → `exit.*` with a `state` string each,
  so a rebuilt graph keeps the vanilla state names and the animation wiring stays valid.
- The **positions** are not: every one of the 8 points is a Serpente-space translation, and
  bbox-scaled onto the Batmobile they do **not** land on its shell - the counts are
  30 inside the shell, 23 floating, 0 on-surface and 32 with no position of their own.
  Geometry has to be re-fitted to the Batmobile, not scaled; the seven `trigger.*` volumes
  and the three `point.stunt*` nodes are the ones ANI-9 needs first.
- The **stunt areas** are a small triangle set bound to part names, and they too scale
  *away* from the shell:

| area | vertices | on the shell | worst clearance |
|---|---|---|---|
| `front_area` | 6 | 0 | 0.374 m |
| `front_signature_area` | 6 | 0 | 0.374 m |
| `main_area` | 10 | 0 | 0.5955 m |

  The Batmobile is proportionally **taller** (y scale 1.49) than it is long or wide, so a hood surface copied by bbox scaling
  ends up floating above the real hood. The build must rebind the areas to the Batmobile's
  own part indices and remeasure its vertices against the Batmobile mesh (a G3 job); the
  decoded vertices, triangles and welds here are the source for that rewrite.

## 5. UNKNOWNs and limits

- **Body watertightness**: the Batmobile body mesh is a shell with wheel-arch and window
  gaps, so the three-ray parity test can disagree with itself; the majority vote is
  recorded but an `inside` verdict near an opening is weak.
- **A JSON-side gap, not a data gap**: the decoded `detail/*.ee.json` drops the `world` of
  2 of 7 triggers (trigger.driver.fast, trigger.stationary.stunt); the
  XML has them, so all 7 positions are measured - but a reader that trusts only the JSON
  would report those two as UNKNOWN.
- **What the scale in a trigger transform means**: read as a half-extent because the
  translation is in the last row; no file states it, so the box size is *derived*.
- **Animation names**: only the `state` strings are in the files; the `.asb` state machine
  that consumes them was not decoded here, so "which animation plays" stays UNKNOWN.
- **Whether Rico can stand on a mapped area in game**: not testable offline; the geometry
  match is the only evidence.

## 6. Validation

| assertion | measured | expected |
|---|---|---|
| interaction objects | 85 | 85 |
| `entry.*` | 29 | 29 |
| `exit.*` | 26 | 26 |
| `point.*` | 8 | 8 |
| `transition.*` | 12 | 12 |
| `trigger.*` | 7 | 7 |
| `interaction.*` | 3 | 3 |
| objects with own `world` | 15 | 15 |
| objects with inherited transform | 70 | 70 |
| objects with no transform | 0 | 0 |
| objects with a position | 85 | 85 |
| deform points | 135 | 135 |
| stunt-area slots | 32 | 32 |
| active stunt areas | 3 | 3 |
| declared stunt areas | 3 | 3 |
| weld rows | 64 | 64 |
| real welds (both areas >= 0) | 8 | 8 |
| Batmobile mesh vertices | 28940 | 28940 |
| Batmobile mesh triangles | 20000 | 20000 |
| XML/JSON value agreement | True | True |
| `world` present in XML only | 2 | 2 |
| Batmobile wheelbase | 5.0289 | 5.0289 |
| Serpente wheelbase | 3.003 | 3.003 |
