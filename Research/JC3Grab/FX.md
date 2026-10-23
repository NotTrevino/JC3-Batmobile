# JC3 effects, camera tunes and trim data (G2-9)

Every `.effc`, `.ctunec` and `.trim` in the game, decoded by
`Tools/scripts/jc3fx.py` with the same ADF v4 reader the vehicle modules use
(`jc3adf.py`). The files are ADF v4 containers (`' FDA'`, version 4) -- inside
`.ee` bundles and as standalone archive entries alike -- so nothing had to be
reverse engineered for them beyond four type kinds the modules never use:
pointer (code 2), `String` (`0x8955583E`, a data-relative offset to a
NUL-terminated string), StringHash (code 9) and inline arrays of primitives.

| item | value |
|---|---|
| files decoded | **57187** |
| standalone archive entries | 104 |
| files inside `.ee` bundles | 57083 |
| value rows | **62,504,473** |
| member paths (indices collapsed) | 700 |
| failures | 0 |

## By extension

| ext | files | rows | root classes |
|---|---|---|---|
| `.effc` | 25,025 | 48,799,123 | `EffectRTSystem` 25025 |
| `.ctunec` | 6,455 | 344,010 | `CameraTransitionParams` 2388, `SphericalCoordinateFramingParams` 1312, `AuxiliaryMotionModifierParams` 590, `CameraCollisionParams` 339, `GenericVehicleCamera` 321, `ListenerPositionParams` 318 |
| `.trim` | 25,707 | 13,361,340 | `EffectTrimData` 25707 |

## What is inside

### `.effc` - effects

Root classes: `EffectRTSystem`.

| member path | type | rows | min | max | sample |
|---|---|---|---|---|---|
| `Timelines[].ControlPointsY[]` | int8 | 9,512,336 | -128 | 127 |  |
| `EmitterTemplates[].EmitterParams[]` | uint16 | 5,833,712 | 1 | 132 |  |
| `Instantiators[].Parameters.FloatParamIndices[]` | uint16 | 3,609,666 | 1 | 119 |  |
| `Instantiators[].RenderInfos[].RenderBlockData[]` | uint32 | 2,780,765 | 0 | 4.29423e+09 |  |
| `Instantiators[].Parameters.Int32Params[]` | int32 | 2,701,361 | -2.12756e+09 | 2.06379e+09 |  |
| `Timelines[].EndX[]` | float | 2,378,084 | 0 | 1 |  |
| `Timelines[].StartX[]` | float | 2,378,084 | 0 | 0.996999 |  |
| `Timelines[].XScaleRecip[]` | float | 2,378,084 | 0 | 337.132 |  |
| `Modifiers[].Parameters.FloatParamIndices[]` | uint16 | 1,972,514 | 1 | 126 |  |
| `Params[]` | float | 1,300,498 | -10000 | 100000 |  |
| `Modifiers[].Flags` | uint32 | 611,286 | 0 | 3 |  |
| `Modifiers[].Parameters.FloatParamIndices` | A[uint16] | 611,286 |  |  |  |
| `Modifiers[].Parameters.Int32Params` | A[int32] | 611,286 |  |  |  |
| `Modifiers[].Parameters.LocalParams` | A[EffectRTLocalParam] | 611,286 |  |  |  |
| `Modifiers[].Parameters.LocalParamsSize` | uint32 | 611,286 | 0 | 32 |  |
| `Modifiers[].Parameters.TimelineConnections` | A[uint32] | 611,286 |  |  |  |
| `Modifiers[].TypeHash` | uint32 | 611,286 | 2.37954e+07 | 4.22772e+09 |  |
| `EmitterTemplates[].ParticleModifiers[]` | uint8 | 463,557 | 0 | 84 |  |
| `Modifiers[].Parameters.Int32Params[]` | int32 | 412,106 | 0 | 5 |  |
| `Emitters[].EmitterModifiers[]` | uint8 | 348,711 | 0 | 81 |  |
| `Modifiers[].Parameters.TimelineConnections[]` | uint32 | 299,358 | 1.34218e+08 | 2.15161e+09 |  |
| `Modifiers[].Parameters.LocalParams[].Hash` | uint32 | 243,061 | 1.33407e+07 | 4.28225e+09 |  |
| `Modifiers[].Parameters.LocalParams[].Index` | uint16 | 243,061 | 0 | 36 |  |
| `Modifiers[].Parameters.LocalParams[].NumParams` | uint16 | 243,061 | 1 | 2 |  |
| `NamedParameters[].Hash` | uint32 | 194,860 | 7.14669e+06 | 4.28225e+09 |  |

Top 25 of 94 member paths, most rows first.

### `.ctunec` - camera tunes

Root classes: `AlignToVelocityParams`, `AutoPitchParams`, `AuxiliaryMotionModifierParams`, `CameraBaseSmoothingModifierParams`, `CameraCollisionParams`, `CameraShakeModifierParams`, `CameraTransitionParams`, `DofModifierParams`, `DynamicZParams`, `FocusDofModifierParams`, `FollowSpringModifierParams`, `FullScreenEffectModifierParams`, `GenericVehicleCamera`, `IgnoreParentRotationModifierParams`, `InputToOrbitModifierParams`, `ListenerPositionParams`, `LocalAngleLimitsModifierParams`, `MotionBlurModifierParams`, `MoveInputOffsetParams`, `MoveInputPitchParams`, `MoveInputYawParams`, `ParachuteAttachmentModifierParams`, `ParachuteCameraCollisionModifierParams`, `PlayerCollisionModifierParams`, `RadialBlurParams`, `RollParams`, `SequenceDofModifierParams`, `SphericalCoordinateFramingParams`, `SplineFuncOfPitchParams`, `SplineFuncOfYawParams`, `TrackPlayerModifierParams`, `WeaponCameraParams`, `WingsuitAttachmentModifierParams`, `ZOverTimeParams`.

| member path | type | rows | min | max | sample |
|---|---|---|---|---|---|
| `PivotPosition[]` | float | 3,936 | -18 | 12 |  |
| `SplineFuncOfPitchParams.DollySpline.control_points[]x` | float | 3,210 | -3.88194e-34 | 3.49539e+22 |  |
| `SplineFuncOfPitchParams.DollySpline.control_points[]y` | float | 3,210 | -3.88194e-34 | 3.49539e+22 |  |
| `SplineFuncOfPitchParams.DollySpline.control_points[]y2` | float | 3,210 | -3.88194e-34 | 3.49539e+22 |  |
| `SplineFuncOfPitchParams.FOVSpline.control_points[]x` | float | 3,210 | -2.52437e-29 | 3.16119e+22 |  |
| `SplineFuncOfPitchParams.FOVSpline.control_points[]y` | float | 3,210 | -2.52437e-29 | 3.16119e+22 |  |
| `SplineFuncOfPitchParams.FOVSpline.control_points[]y2` | float | 3,210 | -6.51277e-27 | 3.16119e+22 |  |
| `SplineFuncOfPitchParams.PedestalSpline.control_points[]x` | float | 3,210 | -3.88194e-34 | 3.49539e+22 |  |
| `SplineFuncOfPitchParams.PedestalSpline.control_points[]y` | float | 3,210 | -1 | 3.49539e+22 |  |
| `SplineFuncOfPitchParams.PedestalSpline.control_points[]y2` | float | 3,210 | -1 | 3.49539e+22 |  |
| `SplineAnimations[].DollySpline.control_points[]x` | float | 2,970 | -2.52442e-29 | 1.79992e+38 |  |
| `SplineAnimations[].DollySpline.control_points[]y` | float | 2,970 | -2.52437e-29 | 1.79992e+38 |  |
| `SplineAnimations[].DollySpline.control_points[]y2` | float | 2,970 | -144.829 | 1.79991e+38 |  |
| `SplineAnimations[].DutchSpline.control_points[]x` | float | 2,970 | -3.85196e-34 | 1.8006e+38 |  |
| `SplineAnimations[].DutchSpline.control_points[]y` | float | 2,970 | -3.85196e-34 | 1.8006e+38 |  |
| `SplineAnimations[].DutchSpline.control_points[]y2` | float | 2,970 | -180.929 | 1.8006e+38 |  |
| `SplineAnimations[].FOVSpline.control_points[]x` | float | 2,970 | -4.05152e-28 | 2.88222e+26 |  |
| `SplineAnimations[].FOVSpline.control_points[]y` | float | 2,970 | -9.87064e-32 | 93.1727 |  |
| `SplineAnimations[].FOVSpline.control_points[]y2` | float | 2,970 | -427.576 | 93.1727 |  |
| `SplineAnimations[].PanSpline.control_points[]x` | float | 2,970 | 0 | 1 |  |
| `SplineAnimations[].PanSpline.control_points[]y` | float | 2,970 | 0 | 1 |  |
| `SplineAnimations[].PanSpline.control_points[]y2` | float | 2,970 | 0 | 1 |  |
| `SplineAnimations[].PedistalSpline.control_points[]x` | float | 2,970 | -6.46251e-27 | 1.79991e+38 |  |
| `SplineAnimations[].PedistalSpline.control_points[]y` | float | 2,970 | -2.52442e-29 | 1.79991e+38 |  |
| `SplineAnimations[].PedistalSpline.control_points[]y2` | float | 2,970 | -106.563 | 1.79992e+38 |  |

Top 25 of 602 member paths, most rows first.

### `.trim` - effect trim data

Root classes: `EffectTrimData`.

| member path | type | rows | min | max | sample |
|---|---|---|---|---|---|
| `Vertices[]Array[]` | float | 13,258,512 | -0.69618 | 1.7185 |  |
| `Vertices[]Array` | A[float] | 51,414 |  |  |  |
| `AnimFramesX` | uint8 | 25,707 | 1 | 15 |  |
| `AnimFramesY` | uint8 | 25,707 | 1 | 15 |  |

Top 25 of 4 member paths, most rows first.

## Validation

`jc3fx.py check` re-reads every file out of the archives and recomputes its
row digest and object census; both must equal the row stored here. The census
is the array structure of the file (e.g. `emitters` = 3), so a decode that
silently stopped early cannot pass. Each `.ee` is opened once and dropped, so
the whole game is re-read without holding it; standalone entries are re-read
from the archive path in their `source` field.
