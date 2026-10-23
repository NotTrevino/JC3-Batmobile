# JC3 vehicle entities — structure and shape

Derived from **232** decoded `.epe` graphs and their `.rbm` headers by
`Tools/scripts/jc3detail.py`. Raw decodes stay outside the repo.

## Class inventory (all entities)

| class | occurrences |
|---|---|
| `CPartProp` | 11041 |
| `CInteractionGraphParentIsUpRightCondition` | 6761 |
| `CCameraModifier` | 5796 |
| `CInteractionGraphEntry` | 5535 |
| `SAttachedEffect` | 5342 |
| `CInteractionGraphExit` | 4832 |
| `CCameraTransition` | 4477 |
| `SDynamicAttachedEffect` | 4344 |
| `CInteractionGraphParentVelocityCondition` | 4057 |
| `SVehicleLight` | 3972 |
| `CInteractionGraphNodeAboveWaterCondition` | 3914 |
| `CInteractionGraphVehicleSeatPlayerUsableCondition` | 3202 |
| `CInteractionGraphTransition` | 2904 |
| `CInteractionGraphParentPlayerLockedCondition` | 2453 |
| `CInteractionGraphNodeOccupiedCondition` | 2306 |
| `CInteractionGraphPointNode` | 1843 |
| `SAttachedEffectTable` | 1678 |
| `CInteractionTrigger` | 1374 |
| `CInteractionComponentSetNode` | 1284 |
| `SDynamicAttachedEffectTable` | 1212 |
| `CCameraObject` | 1203 |
| `CCameraTransitionCollection` | 1197 |
| `CInteractionGraphExitObstructedCondition` | 865 |
| `CInteraction` | 675 |
| `SValueDrivenEffectUsage` | 527 |
| `CInteractionGraphUserIsPlayerCondition` | 464 |
| `SVehicleLightList` | 412 |
| `CInteractionGraphDeformableLineNode` | 382 |
| `SEffects` | 359 |
| `CSpeaker` | 350 |
| `CInteractionGraphEntryIsFacingParentCondition` | 342 |
| `CInteractionGraphStuntTransitionValidCondition` | 310 |
| `CForcePulse` | 307 |
| `SWeaponPoint` | 300 |
| `CRigidObject` | 280 |
| `SPhysicsParams` | 280 |
| `CParts` | 233 |
| `SDynamicExpressions` | 233 |
| `SValueDrivenEffectUsages` | 233 |
| `SVehicleLights` | 233 |
| `SEventDrivenEffectUsages` | 233 |
| `CInteractionContext` | 233 |
| `CInteractionGraph` | 233 |
| `CInteractionGraphStuntExitValidCondition` | 232 |
| `CCameraRef` | 214 |
| `STargetPoint` | 212 |
| `CEffectPointEmitter` | 181 |
| `CInteractionGraphIsAttachedCondition` | 171 |
| `CInteractionGraphNodeEntryAngleCondition` | 165 |
| `CCar` | 126 |
| `CInteractionGraphDeformableIKTarget` | 112 |
| `CDamageController` | 104 |
| `SAttachedEffectParam` | 90 |
| `SDCRef` | 82 |
| `CMaterialEffectTable` | 72 |
| `CVehicleRule` | 59 |
| `CCameraLookAtTargetModifier` | 57 |
| `CBulletWeaponBase` | 57 |
| `CTimeTrigger` | 49 |
| `CDynamicNavMeshCutter` | 46 |
| `CShapeTriggerComponent` | 38 |
| `CCoverPoint` | 36 |
| `SEventTriggerComponent` | 36 |
| `CBoat` | 35 |
| `CGrapplingHookPropData` | 33 |
| `CShapeTrigger` | 32 |
| `CAOVolumeObject` | 32 |
| `CLightWeaponComponent` | 30 |
| `CPOI` | 29 |
| `SPhysicsBuoy` | 26 |
| `CMissileWeaponBase` | 25 |
| `CHelicopter` | 23 |
| `STimerComponent` | 22 |
| `CAIEntityProxy` | 19 |
| `CInteractionGraphTransitionTargetCondition` | 19 |
| `CMotorBike` | 19 |
| `CEventTrigger` | 18 |
| `CAirPlane` | 18 |
| `CConstraint` | 16 |
| `CNamedPoint` | 14 |
| `CGraphScriptGameObject` | 13 |
| `CBarrelSpinWeaponComponent` | 12 |
| `CVehicleCargoBay` | 12 |
| `CTrain` | 12 |
| `CPrimarySounds` | 12 |
| `CPrimarySound` | 12 |
| `SDynamicExpressionFile` | 11 |
| `CAimPOIWeaponComponent` | 11 |
| `CEntityObject` | 10 |
| `SObjectMovementTrigger` | 9 |
| `CConstraintFixedData` | 8 |
| `CConstraintBreakableDecoratorData` | 8 |
| `CConstraintLimitedHingeData` | 8 |
| `CRPGFireLeachWeapon` | 6 |
| `CSoundLayerEmitter` | 6 |
| `SSpawnPoint` | 5 |
| `CLaserBeamWeaponComponent` | 3 |
| `CMusicTrack` | 2 |
| `CExternalBehaviorTree` | 1 |
| `CCombatantRule` | 1 |
| `CEventRouter` | 1 |
| `SSpawnSeat` | 1 |
| `CTurretWeaponComponent` | 1 |

## Parts

`CPartProp` per entity: min **3**, median **48**, max **161** (n=232).

### Donor parts — `v0300_car_kensington_sportsmuscle_civilian_01.ee`

| part_index | name |
|---|---|
| 0 | `sportsmuscle_body` |
| 1 | `sportsmuscle_door_f_l` |
| 2 | `sportsmuscle_door_f_r` |
| 3 | `sportsmuscle_engine` |
| 4 | `sportsmuscle_f_l_seat` |
| 5 | `sportsmuscle_f_r_seat` |
| 6 | `sportsmuscle_rear_bumper` |
| 7 | `sportsmuscle_steeringwheel` |
| 8 | `sportsmuscle_taillight_r_l` |
| 9 | `sportsmuscle_taillight_r_r` |
| 10 | `sportsmuscle_trunk` |
| 11 | `sportsmuscle_wheel_r_l` |
| 12 | `sportsmuscle_wheel_r_r` |
| 13 | `sportsmuscle_window_f` |
| 14 | `sportsmuscle_window_r_l` |
| 15 | `sportsmuscle_window_r_r` |
| 16 | `sportsmuscle_door_f_l_window` |
| 17 | `sportsmuscle_l_mirror` |
| 18 | `sportsmuscle_door_f_r_window` |
| 19 | `sportsmuscle_r_mirror` |
| 20 | `sportsmuscle_fender_l` |
| 21 | `sportsmuscle_fender_r` |
| 22 | `sportsmuscle_front_bumper` |
| 23 | `sportsmuscle_grill` |
| 24 | `sportsmuscle_hood` |
| 26 | `sportsmuscle_wheel_f_l` |
| 27 | `sportsmuscle_wheel_f_r` |
| 28 | `sportsmuscle_plate_r` |
| 29 | `sportsmuscle_signal_r_l` |
| 30 | `sportsmuscle_signal_r_r` |
| 31 | `sportsmuscle_taillight_r_c` |
| 32 | `sportsmuscle_trunk_window` |
| 33 | `sportsmuscle_c_mirror` |
| 34 | `sportsmuscle_headlight_f_l_01` |
| 35 | `sportsmuscle_headlight_f_l_02` |
| 36 | `sportsmuscle_signal_f_l` |
| 37 | `sportsmuscle_headlight_f_r_01` |
| 38 | `sportsmuscle_headlight_f_r_02` |
| 39 | `sportsmuscle_signal_f_r` |
| 40 | `sportsmuscle_plate_f` |

## Lights (`SVehicleLight`)

Lights per entity: min **4**, median **16**, max **54** (n=232).

### Preset vocabulary (fleet)

| preset_id | uses |
|---|---|
| `Dash_Light` | 221 |
| `Front_Right_Turn` | 145 |
| `Rear_Left_Reverse` | 145 |
| `Rear_Left_Turn` | 145 |
| `Rear_Right_Turn` | 145 |
| `Front_Primary_Head` | 145 |
| `Rear_Brake` | 145 |
| `Front_Left_Turn` | 145 |
| `Front_Left_Point` | 126 |
| `Front_Left_Volumetric` | 126 |
| `Front_Right_Point` | 126 |
| `Front_Right_Volumetric` | 126 |
| `Rear_Left_Point` | 126 |
| `Rear_Right_Point` | 126 |
| `Rear_Right_Reverse` | 126 |
| `Front_Secondary_Head` | 126 |
| `Nav_Right_Point` | 35 |
| `Nav_Left_Point` | 35 |
| `Stern_Point` | 35 |
| `Left_Point` | 23 |
| `Rear_Point` | 23 |
| `Right_Point` | 23 |
| `Front_Primary_Volumetric` | 19 |
| `Right_Wing_Point` | 18 |

### Donor lights — 22 entries

| name | preset | diffuse | radius | spot | volumetric |
|---|---|---|---|---|---|
| `Front_Left_Point` | `Front_Left_Point` | 0.6039,0.6039,0.9529 | 1.5 | 60 | 0 |
| `Front_Left_Volumetric` | `Front_Left_Volumetric` | 0.6039,0.6039,0.9529 | 10 | 15 | 1 |
| `Front_Right_Point` | `Front_Right_Point` | 0.6039,0.6039,0.9529 | 1.5 | 60 | 0 |
| `Front_Right_Turn` | `Front_Right_Turn` | 1,0.5,0 | 2 | 60 | 0 |
| `Front_Right_Volumetric` | `Front_Right_Volumetric` | 0.6039,0.6039,0.9529 | 10 | 15 | 1 |
| `Rear_Left_Point` | `Rear_Left_Point` | 1,0.1,0 | 1 | 60 | 0 |
| `Rear_Left_Reverse` | `Rear_Left_Reverse` | 1,1,1 | 3 | 60 | 0 |
| `Rear_Left_Turn` | `Rear_Left_Turn` | 1,0.5,0 | 2 | 60 | 0 |
| `Rear_Right_Point` | `Rear_Right_Point` | 1,0.1,0 | 1 | 60 | 0 |
| `Rear_Right_Reverse` | `Rear_Right_Reverse` | 1,1,1 | 2 | 60 | 0 |
| `Rear_Right_Turn` | `Rear_Right_Turn` | 1,0.5,0 | 2 | 60 | 0 |
| `Front_Primary_Head` | `Front_Primary_Head` | 0.6039,0.6039,0.9529 | 60 | 40 | 0 |
| `Rear_Break` | `Rear_Brake` | 1,0.1,0 | 1 | 60 | 0 |
| `Front_Left_Turn` | `Front_Left_Turn` | 1,0.5,0 | 2 | 60 | 0 |
| `Front_Secondary_Head` | `Front_Secondary_Head` | 0.6039,0.6039,0.9529 | 10 | 60 | 0 |
| `Dash_Light` | `Dash_Light` | 1,0.9765,0.9176 | 1 | 60 | 0 |
| `Sport_Muscle_Headlight_Volume_Right` | `Sport_Muscle_Headlight_Volume_Right` | 0.6039,0.6039,0.9529 | 7.5 | 15 | 1 |
| `Sport_Muscle_Headlight_Volume_Left` | `Sport_Muscle_Headlight_Volume_Left` | 0.6039,0.6039,0.9529 | 7.5 | 15 | 1 |
| `Sport_Muscle_Headlight_Point_Left` | `Sport_Muscle_Headlight_Point_Left` | 0.6039,0.6039,0.9529 | 1.5 | 60 | 0 |
| `Sport_Muscle_Rear_Break_Right` | `Sport_Muscle_Rear_Break_Right` | 1,0.1,0 | 1.5 | 60 | 0 |
| `Sport_Muscle_Rear_Break_Left` | `Sport_Muscle_Rear_Break_Left` | 1,0.1,0 | 1.5 | 60 | 0 |
| `Sport_Muscle_Headlight_Point_Right` | `Sport_Muscle_Headlight_Point_Right` | 0.6039,0.6039,0.9529 | 1.5 | 60 | 0 |

## Meshes

| item | value |
|---|---|
| meshes per entity | min 11 / median 229 / max 807 |
| longest mesh (z) per entity | max 66.877 m |
| RBM versions | 1.16.0 |

### Largest mesh per entity (top 15)

| entity | mesh | size x×y×z (m) |
|---|---|---|
| `v4603_plane_urga_cargotransport/v4603_plane_urga_cargotransport_debug.ee` | `cargotransport_fuselage_lod5.rbm` | 12.4549 × 11.8405 × 66.8772 |
| `v4603_plane_urga_cargotransport/v4603_plane_urga_cargotransport_military_01.ee` | `cargotransport_fuselage_lod5.rbm` | 12.4549 × 11.8405 × 66.8772 |
| `v4603_plane_urga_cargotransport/v4603_plane_urga_cargotransport_military_cargo_paratrooper.ee` | `cargotransport_fuselage_lod5.rbm` | 12.4549 × 11.8405 × 66.8772 |
| `v4603_plane_urga_cargotransport/v4603_plane_urga_cargotransport_military_cargo_tank.ee` | `cargotransport_fuselage_lod5.rbm` | 12.4549 × 11.8405 × 66.8772 |
| `v4603_plane_urga_cargotransport/v4603_plane_urga_cargotransport_mm340.ee` | `cargotransport_fuselage_lod5.rbm` | 12.4549 × 11.8405 × 66.8772 |
| `v4603_plane_urga_cargotransport/v4603_plane_urga_cargotransport_rebel_01.ee` | `rebel_cargotransport_fuselage_lod5.rbm` | 12.4549 × 11.8405 × 66.8772 |
| `v2601_helicopter_urga_heavyassault/v2601_helicopter_urga_heavyassault_debug.ee` | `heavyassault_shield_lod1.rbm` | 24.3444 × 12.784 × 31.0121 |
| `v2601_helicopter_urga_heavyassault/v2601_helicopter_urga_heavyassault_military_01.ee` | `heavyassault_shield_lod1.rbm` | 24.3444 × 12.784 × 31.0121 |
| `v2601_helicopter_urga_heavyassault/v2601_helicopter_urga_heavyassault_rebel_01.ee` | `heavyassault_shield_lod1.rbm` | 24.3444 × 12.784 × 31.0121 |
| `v1705_boat_na_mediumoldfishing/v1705_boat_na_mediumoldfishing_civilian_01.ee` | `mediumoldfishing_ropes_lod4.rbm` | 9.6708 × 9.9216 × 21.7748 |
| `v1705_boat_na_mediumoldfishing/v1705_boat_na_mediumoldfishing_debug.ee` | `mediumoldfishing_ropes_lod4.rbm` | 9.6708 × 9.9216 × 21.7748 |
| `v1202_boat_capstone_corvette/v1202_boat_capstone_corvette_debug.ee` | `corvette_body_lod5.rbm` | 6.7946 × 4.7802 × 41.42 |
| `v1202_boat_capstone_corvette/v1202_boat_capstone_corvette_military_01.ee` | `corvette_body_lod5.rbm` | 6.7946 × 4.7802 × 41.42 |
| `v1202_boat_capstone_corvette/v1202_boat_capstone_corvette_rebel_01.ee` | `rebel_corvette_body_lod5.rbm` | 6.7946 × 4.7802 × 41.42 |
| `v2604_helicopter_urga_advancedassault/v2604_helicopter_urga_advancedassault_debug.ee` | `advancedassault_shield_main_lod5.rbm` | 12.7748 × 5.3227 × 16.5279 |

## `.physicsc` (now decoded - G2-8)

233 files across 232 entities; every one starts with the Havok 2014 packfile tag `57E0E057` and carries `__classnames__` / `__types__` / `__data__` sections. That is a Havok binary packfile, not an RTPC property file, so `ConvertProperty` cannot read it - but it is not opaque either: `Tools/scripts/jc3hkx.py` types every object from the virtual fixup table and decodes the hulls, collision meshes and geometries. Counts and invariants: `SHAPES.md`.
