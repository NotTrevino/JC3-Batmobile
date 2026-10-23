# Batmobile — mechanics

Every row is read from the package; offset-only values are primitives whose property name was stripped by the cooker (the value is real, the field name is not in the file).

## Vehicle and simulation objects

### BatmobileFunhouse — `RVehicleBatmobile` (Playable_BatmobileFunhouse_SF, 3905 B)

| property | type | offset | value |
|---|---|---|---|
| `ExplosiveImpactScreenShake` | StructProperty | 0x19C4 | {5 props} |
| `ImpactShake` | StructProperty | 0x1C28 | {7 props} |
| `DeathExplosionSoundArray` | ArrayProperty | 0x1D08 | 2 items |
| `WeaponGeneratorMeshPackage` | ArrayProperty | 0x1FF8 | 3 items |
| `WeaponGeneratorMesh` | ArrayProperty | 0x2008 | 3 items [0.0, 0.0, 0.0] |
| `InteriorLightsSwitchedOn` | ByteProperty | 0x86D | 1 |
| `Wheels` | ArrayProperty | 0x6AC | 4 items |

Light rig (28 entries, each a `VehicleLights` struct):

| # | bone | Type | MaterialType | components |
|---|---|---|---|---|
| 0 | `HeadLight1` | VEHLT_HeadLight | VEHLTMAT_HeadLightRight | `BatmobileFunhouse.SpotLightComponent`; `BatmobileFunhouse.LensFlareComponent`; `BatmobileFunhouse.SpotLightComponent` |
| 1 | `HeadLight2` | VEHLT_HeadLight | VEHLTMAT_HeadLightLeft | `BatmobileFunhouse.SpotLightComponent`; `BatmobileFunhouse.LensFlareComponent` |
| 2 | `ChainGunMuzzle` | None | — | `BatmobileFunhouse.SpotLightComponent` |
| 3 | `HeadLight1` | None | VEHLTMAT_HeadLightRight | `BatmobileFunhouse.SpotLightComponent` |
| 4 | `HeadLight2` | None | VEHLTMAT_HeadLightLeft | `BatmobileFunhouse.SpotLightComponent` |
| 5 | `LWheelLight` | VEHLT_HeadLight | VEHLTMAT_Special3 | `BatmobileFunhouse.SpotLightComponent`; `BatmobileFunhouse.LensFlareComponent` |
| 6 | `RWheelLight` | VEHLT_HeadLight | VEHLTMAT_Special1 | `BatmobileFunhouse.SpotLightComponent`; `BatmobileFunhouse.LensFlareComponent` |
| 7 | `BrakeLightL` | VEHLT_TailLight | VEHLTMAT_TailLightLeft | `BatmobileFunhouse.PointLightComponent`; `BatmobileFunhouse.LensFlareComponent` |
| 8 | `BrakeLightR` | VEHLT_TailLight | VEHLTMAT_TailLightRight | `BatmobileFunhouse.PointLightComponent`; `BatmobileFunhouse.LensFlareComponent` |
| 9 | `BattleModeSpotLight` | VEHLT_BattleModeLight | — | `BatmobileFunhouse.SpotLightComponent` |
| 10 | `HeadLight1` | VEHLT_BattleModeLight | VEHLTMAT_HeadLightRight | `BatmobileFunhouse.SpotLightComponent` |
| 11 | `HeadLight2` | VEHLT_BattleModeLight | VEHLTMAT_HeadLightLeft | `BatmobileFunhouse.SpotLightComponent` |
| 12 | `LWheelLight` | VEHLT_BattleModeLight | VEHLTMAT_Special3 | `BatmobileFunhouse.SpotLightComponent` |
| 13 | `BattleModeSpotLight` | VEHLT_ForensicsLight | — | `BatmobileFunhouse.RHelicopterSpotLightComponent` |
| 14 | `HeadLight1` | VEHLT_ForensicsLight | VEHLTMAT_HeadLightRight | `BatmobileFunhouse.SpotLightComponent` |
| 15 | `HeadLight2` | VEHLT_ForensicsLight | VEHLTMAT_HeadLightLeft | `BatmobileFunhouse.SpotLightComponent` |
| 16 | `Dashboard_Light` | VEHLT_Interior | VEHLTMAT_Interior | `BatmobileFunhouse.SpotLightComponent` |
| 17 | `HeadLight1a` | VEHLT_HeadLight | — | `BatmobileFunhouse.LensFlareComponent` |
| 18 | `HeadLight2a` | VEHLT_HeadLight | — | `BatmobileFunhouse.LensFlareComponent` |
| 19 | `HeadLight1b` | VEHLT_HeadLight | — | `BatmobileFunhouse.LensFlareComponent` |
| 20 | `HeadLight1c` | VEHLT_HeadLight | — | `BatmobileFunhouse.LensFlareComponent` |
| 21 | `HeadLight2b` | VEHLT_HeadLight | — | `BatmobileFunhouse.LensFlareComponent` |
| 22 | `HeadLight2c` | VEHLT_HeadLight | — | `BatmobileFunhouse.LensFlareComponent` |
| 23 | `RWheelLight_top` | VEHLT_HeadLight | VEHLTMAT_Special1 | `BatmobileFunhouse.LensFlareComponent` |
| 24 | `RWheelLight_bottom` | VEHLT_HeadLight | VEHLTMAT_Special1 | `BatmobileFunhouse.LensFlareComponent` |
| 25 | `LWheelLight_top` | VEHLT_HeadLight | VEHLTMAT_Special3 | `BatmobileFunhouse.LensFlareComponent` |
| 26 | `LWheelLight_bottom` | VEHLT_HeadLight | VEHLTMAT_Special3 | `BatmobileFunhouse.LensFlareComponent` |
| 27 | `BootLight` | VEHLT_BootLight | — | `BatmobileFunhouse.SpotLightComponent`; `BatmobileFunhouse.LensFlareComponent` |

Audio referenced by this object:

| object | class | property |
|---|---|---|
| `Engine.Play_Batmobile_Tazer_Fire` | AkEvent | offset-only |
| `Ww_BML_Batmobile.Play_BattleMode_In_Rev` | AkEvent | offset-only |
| `Ww_BML_Batmobile.Play_BattleMode_Out_Rev` | AkEvent | offset-only |
| `Ww_UI_InGame.Play_HUD_Missile_Lock` | AkEvent | offset-only |
| `VEH_Player.Batmobile_MK2` | AkPlayerVehicleSoundInfo | offset-only |
| `BatmobileFunhouse.VehicleSound` | AkVehicleSound | offset-only |

Offset-only floats, sorted by class offset (the property name was stripped by the cooker; the value is real):

```
offset 0x744  0.2000
offset 0x748  0.2000
offset 0x1210  0.7500
offset 0x1214  640000.0000
offset 0x175C  0.0000
offset 0x1760  0.3330
offset 0x1764  90000.0000
offset 0x1768  30000.0000
offset 0x177C  2000.0000
offset 0x1914  150000.0000
offset 0x1A64  2000.0000
offset 0x1A68  2000.0000
offset 0x1ACC  150.0000
offset 0x1AD0  20.0000
offset 0x1AD4  2.2500
offset 0x1ADC  2.0000
offset 0x1AE4  540.0000
offset 0x1AE8  120.0000
offset 0x1AEC  0.5000
offset 0x1C18  -200.0000
offset 0x1C1C  0.5000
offset 0x1C20  10.0000
offset 0x1C24  0.7500
offset 0x1CC4  0.0133
offset 0x1CC8  1.5000
offset 0x1CF8  10000.0000
offset 0x1EEC  2.0000
offset 0x1F24  -1.0000
offset 0x1FDC  6000.0000
offset 0x1FE0  10000.0000
offset 0x1FE4  0.1500
```

### SimulationModel — `RVehicleSimBatmobile` (Playable_BatmobileFunhouse_SF, 2328 B)

| property | type | offset | value |
|---|---|---|---|
| `BoostTorqueVSpeedCurve` | StructProperty | 0x1DC | 7 curve points |
| `StandardTorqueVSpeedCurve` | StructProperty | 0x1F0 | 6 curve points |
| `BattleModeVSpeedCurve` | StructProperty | 0x218 | 3 curve points |
| `StandardSteeringSpeedCurve` | StructProperty | 0x240 | 5 curve points |
| `TorqueVSpeedCurve` | StructProperty | 0x104 | 6 curve points |
| `SteerSpeedVsSpeedCurve` | StructProperty | 0x194 | 2 curve points |

Curves (x → y), decoded from the nested `Points` array:

```
BoostTorqueVSpeedCurve = -1500.0 → 0.0  -300.0 → 200.0  0.0 → 260.0  1500.0 → 260.0  2100.0 → 220.0  2800.0 → 200.0  3000.0 → 150.0
StandardTorqueVSpeedCurve = -1500.0 → 0.0  -300.0 → 200.0  0.0 → 200.0  750.0 → 170.0  1600.0 → 150.0  2100.0 → 105.0
BattleModeVSpeedCurve = 0.0 → 60.0  600.0 → 40.0  1200.0 → 30.0
StandardSteeringSpeedCurve = 0.0 → 60.0  600.0 → 55.0  1100.0 → 55.0  1300.0 → 30.0  2000.0 → 20.0
TorqueVSpeedCurve = -1500.0 → 0.0  -300.0 → 200.0  0.0 → 130.0  750.0 → 130.0  1050.0 → 60.0  1100.0 → 0.0
SteerSpeedVsSpeedCurve = 0.0 → 720.0  3500.0 → 720.0
```

Offset-only floats, sorted by class offset (the property name was stripped by the cooker; the value is real):

```
offset 0x0DC  220.0000
offset 0x0EC  300.0000
offset 0x164  10000.0000
offset 0x168  1.0000
offset 0x190  100000.0000
offset 0x1C8  0.8000
offset 0x1CC  -0.8000
offset 0x1D0  2.0000
offset 0x2AC  1.5000
offset 0x2C4  600.0000
offset 0x2D4  0.7500
offset 0x2D8  1.2500
offset 0x2E0  0.3333
offset 0x2EC  10.0000
offset 0x2F4  500.0000
offset 0x2F8  30.0000
offset 0x300  1.0000
offset 0x304  3000.0000
offset 0x308  300.0000
offset 0x30C  50.0000
offset 0x310  10.0000
offset 0x318  100.0000
offset 0x320  -0.2500
offset 0x324  20.0000
offset 0x32C  750.0000
offset 0x334  20.0000
offset 0x33C  5.0000
offset 0x390  3000.0000
offset 0x394  24000.0000
offset 0x4A8  8000.0000
```

### JokersBatmobile — `RVehicleBatmobile` (Playable_BatmobileJoker_SF, 2239 B)

| property | type | offset | value |
|---|---|---|---|
| `UpgradedGeneratorBonus` | ArrayProperty | 0x21A0 | 2 items [1.0, 1.0] |
| `ExplosiveImpactScreenShake` | StructProperty | 0x19C4 | {5 props} |
| `ImpactShake` | StructProperty | 0x1C28 | {7 props} |
| `DeathExplosionSoundArray` | ArrayProperty | 0x1D08 | 2 items |
| `Wheels` | ArrayProperty | 0x6AC | 4 items |

Light rig (17 entries, each a `VehicleLights` struct):

| # | bone | Type | MaterialType | components |
|---|---|---|---|---|
| 0 | `HeadLight1` | VEHLT_HeadLight | — | `JokersBatmobile.SpotLightComponent`; `JokersBatmobile.LensFlareComponent` |
| 1 | `HeadLight2` | VEHLT_HeadLight | — | `JokersBatmobile.SpotLightComponent`; `JokersBatmobile.LensFlareComponent` |
| 2 | `ChainGunMuzzle` | None | — | `JokersBatmobile.SpotLightComponent` |
| 3 | `HeadLight1` | None | — | `JokersBatmobile.SpotLightComponent` |
| 4 | `HeadLight2` | None | — | `JokersBatmobile.SpotLightComponent` |
| 5 | `LWheelLight` | VEHLT_HeadLight | — | `JokersBatmobile.SpotLightComponent`; `JokersBatmobile.LensFlareComponent` |
| 6 | `RWheelLight` | VEHLT_HeadLight | — | `JokersBatmobile.SpotLightComponent`; `JokersBatmobile.LensFlareComponent` |
| 7 | `BrakeLightL` | VEHLT_TailLight | — | `JokersBatmobile.PointLightComponent` |
| 8 | `BrakeLightR` | VEHLT_TailLight | — | `JokersBatmobile.PointLightComponent` |
| 9 | `BattleModeSpotLight` | VEHLT_BattleModeLight | — | `JokersBatmobile.SpotLightComponent` |
| 10 | `HeadLight1` | VEHLT_BattleModeLight | — | `JokersBatmobile.SpotLightComponent` |
| 11 | `HeadLight2` | VEHLT_BattleModeLight | — | `JokersBatmobile.SpotLightComponent` |
| 12 | `LWheelLight` | VEHLT_BattleModeLight | — | `JokersBatmobile.SpotLightComponent` |
| 13 | `BattleModeSpotLight` | VEHLT_ForensicsLight | — | `JokersBatmobile.RHelicopterSpotLightComponent` |
| 14 | `HeadLight1` | VEHLT_ForensicsLight | — | `JokersBatmobile.SpotLightComponent` |
| 15 | `HeadLight2` | VEHLT_ForensicsLight | — | `JokersBatmobile.SpotLightComponent` |
| 16 | `Dashboard` | VEHLT_Interior | — | `JokersBatmobile.PointLightComponent` |

Audio referenced by this object:

| object | class | property |
|---|---|---|
| `Engine.Play_Batmobile_Tazer_Fire` | AkEvent | offset-only |
| `Ww_BML_Batmobile.Play_BattleMode_In_Rev` | AkEvent | offset-only |
| `Ww_BML_Batmobile.Play_BattleMode_Out_Rev` | AkEvent | offset-only |
| `Ww_UI_InGame.Play_HUD_Missile_Lock` | AkEvent | offset-only |
| `VEH_Player.Batmobile_Joker` | AkPlayerVehicleSoundInfo | offset-only |
| `JokersBatmobile.VehicleSound` | AkVehicleSound | offset-only |

Offset-only floats, sorted by class offset (the property name was stripped by the cooker; the value is real):

```
offset 0x744  0.2000
offset 0x748  0.2000
offset 0x1210  0.7500
offset 0x1214  640000.0000
offset 0x175C  0.3300
offset 0x1760  0.7500
offset 0x1764  90000.0000
offset 0x1768  30000.0000
offset 0x177C  2000.0000
offset 0x1A64  2000.0000
offset 0x1A68  2000.0000
offset 0x1ACC  180.0000
offset 0x1AD0  40.0000
offset 0x1AD4  0.8000
offset 0x1AE4  540.0000
offset 0x1AE8  120.0000
offset 0x1AEC  0.6660
offset 0x1C18  -400.0000
offset 0x1C1C  0.7500
offset 0x1C20  10.0000
offset 0x1C24  0.7500
offset 0x1CC4  0.0133
offset 0x1CC8  1.5000
offset 0x1CF8  10000.0000
offset 0x1EEC  0.0000
offset 0x1F00  0.0000
offset 0x1F08  0.0300
offset 0x1F18  0.0000
offset 0x1F20  0.0000
offset 0x1F24  -1.0000
offset 0x1F28  1.0000
```

### SimulationModel — `RVehicleSimBatmobile` (Playable_BatmobileJoker_SF, 2328 B)

| property | type | offset | value |
|---|---|---|---|
| `BoostTorqueVSpeedCurve` | StructProperty | 0x1DC | 7 curve points |
| `StandardTorqueVSpeedCurve` | StructProperty | 0x1F0 | 6 curve points |
| `BattleModeVSpeedCurve` | StructProperty | 0x218 | 3 curve points |
| `StandardSteeringSpeedCurve` | StructProperty | 0x240 | 5 curve points |
| `TorqueVSpeedCurve` | StructProperty | 0x104 | 6 curve points |
| `SteerSpeedVsSpeedCurve` | StructProperty | 0x194 | 2 curve points |

Curves (x → y), decoded from the nested `Points` array:

```
BoostTorqueVSpeedCurve = -1500.0 → 0.0  -300.0 → 200.0  0.0 → 260.0  1500.0 → 260.0  2100.0 → 220.0  2800.0 → 200.0  3000.0 → 150.0
StandardTorqueVSpeedCurve = -1500.0 → 0.0  -300.0 → 200.0  0.0 → 200.0  750.0 → 170.0  1600.0 → 150.0  2100.0 → 105.0
BattleModeVSpeedCurve = 0.0 → 60.0  600.0 → 40.0  1200.0 → 30.0
StandardSteeringSpeedCurve = 0.0 → 60.0  600.0 → 55.0  1100.0 → 50.0  1300.0 → 35.0  2000.0 → 15.0
TorqueVSpeedCurve = -1500.0 → 0.0  -300.0 → 200.0  0.0 → 130.0  750.0 → 130.0  1050.0 → 60.0  1100.0 → 0.0
SteerSpeedVsSpeedCurve = 0.0 → 220.0  3500.0 → 20.0
```

Offset-only floats, sorted by class offset (the property name was stripped by the cooker; the value is real):

```
offset 0x0DC  220.0000
offset 0x0EC  300.0000
offset 0x164  10000.0000
offset 0x168  1.0000
offset 0x190  100000.0000
offset 0x1C8  0.8000
offset 0x1CC  -0.8000
offset 0x1D0  2.0000
offset 0x2AC  1.5000
offset 0x2C4  600.0000
offset 0x2D4  0.7500
offset 0x2D8  1.2500
offset 0x2E0  0.3333
offset 0x2EC  10.0000
offset 0x2F4  500.0000
offset 0x2F8  30.0000
offset 0x300  1.0000
offset 0x304  3000.0000
offset 0x308  300.0000
offset 0x30C  50.0000
offset 0x310  10.0000
offset 0x318  100.0000
offset 0x320  -0.2500
offset 0x324  20.0000
offset 0x32C  750.0000
offset 0x334  20.0000
offset 0x33C  5.0000
offset 0x390  3000.0000
offset 0x394  24000.0000
offset 0x4A8  8000.0000
```

### Batmobile_MK2 — `RVehicleBatmobile` (Playable_BatmobileMK2_SF, 3905 B)

| property | type | offset | value |
|---|---|---|---|
| `ExplosiveImpactScreenShake` | StructProperty | 0x19C4 | {5 props} |
| `ImpactShake` | StructProperty | 0x1C28 | {7 props} |
| `DeathExplosionSoundArray` | ArrayProperty | 0x1D08 | 2 items |
| `WeaponGeneratorMeshPackage` | ArrayProperty | 0x1FF8 | 3 items |
| `WeaponGeneratorMesh` | ArrayProperty | 0x2008 | 3 items [0.0, 0.0, 0.0] |
| `InteriorLightsSwitchedOn` | ByteProperty | 0x86D | 1 |
| `Wheels` | ArrayProperty | 0x6AC | 4 items |

Light rig (28 entries, each a `VehicleLights` struct):

| # | bone | Type | MaterialType | components |
|---|---|---|---|---|
| 0 | `HeadLight1` | VEHLT_HeadLight | VEHLTMAT_HeadLightRight | `Batmobile_MK2.SpotLightComponent`; `Batmobile_MK2.LensFlareComponent`; `Batmobile_MK2.SpotLightComponent` |
| 1 | `HeadLight2` | VEHLT_HeadLight | VEHLTMAT_HeadLightLeft | `Batmobile_MK2.SpotLightComponent`; `Batmobile_MK2.LensFlareComponent` |
| 2 | `ChainGunMuzzle` | None | — | `Batmobile_MK2.SpotLightComponent` |
| 3 | `HeadLight1` | None | VEHLTMAT_HeadLightRight | `Batmobile_MK2.SpotLightComponent` |
| 4 | `HeadLight2` | None | VEHLTMAT_HeadLightLeft | `Batmobile_MK2.SpotLightComponent` |
| 5 | `LWheelLight` | VEHLT_HeadLight | VEHLTMAT_Special3 | `Batmobile_MK2.SpotLightComponent`; `Batmobile_MK2.LensFlareComponent` |
| 6 | `RWheelLight` | VEHLT_HeadLight | VEHLTMAT_Special1 | `Batmobile_MK2.SpotLightComponent`; `Batmobile_MK2.LensFlareComponent` |
| 7 | `BrakeLightL` | VEHLT_TailLight | VEHLTMAT_TailLightLeft | `Batmobile_MK2.PointLightComponent`; `Batmobile_MK2.LensFlareComponent` |
| 8 | `BrakeLightR` | VEHLT_TailLight | VEHLTMAT_TailLightRight | `Batmobile_MK2.PointLightComponent`; `Batmobile_MK2.LensFlareComponent` |
| 9 | `BattleModeSpotLight` | VEHLT_BattleModeLight | — | `Batmobile_MK2.SpotLightComponent` |
| 10 | `HeadLight1` | VEHLT_BattleModeLight | VEHLTMAT_HeadLightRight | `Batmobile_MK2.SpotLightComponent` |
| 11 | `HeadLight2` | VEHLT_BattleModeLight | VEHLTMAT_HeadLightLeft | `Batmobile_MK2.SpotLightComponent` |
| 12 | `LWheelLight` | VEHLT_BattleModeLight | VEHLTMAT_Special3 | `Batmobile_MK2.SpotLightComponent` |
| 13 | `BattleModeSpotLight` | VEHLT_ForensicsLight | — | `Batmobile_MK2.RHelicopterSpotLightComponent` |
| 14 | `HeadLight1` | VEHLT_ForensicsLight | VEHLTMAT_HeadLightRight | `Batmobile_MK2.SpotLightComponent` |
| 15 | `HeadLight2` | VEHLT_ForensicsLight | VEHLTMAT_HeadLightLeft | `Batmobile_MK2.SpotLightComponent` |
| 16 | `Dashboard_Light` | VEHLT_Interior | VEHLTMAT_Interior | `Batmobile_MK2.SpotLightComponent` |
| 17 | `HeadLight1a` | VEHLT_HeadLight | — | `Batmobile_MK2.LensFlareComponent` |
| 18 | `HeadLight2a` | VEHLT_HeadLight | — | `Batmobile_MK2.LensFlareComponent` |
| 19 | `HeadLight1b` | VEHLT_HeadLight | — | `Batmobile_MK2.LensFlareComponent` |
| 20 | `HeadLight1c` | VEHLT_HeadLight | — | `Batmobile_MK2.LensFlareComponent` |
| 21 | `HeadLight2b` | VEHLT_HeadLight | — | `Batmobile_MK2.LensFlareComponent` |
| 22 | `HeadLight2c` | VEHLT_HeadLight | — | `Batmobile_MK2.LensFlareComponent` |
| 23 | `RWheelLight_top` | VEHLT_HeadLight | VEHLTMAT_Special1 | `Batmobile_MK2.LensFlareComponent` |
| 24 | `RWheelLight_bottom` | VEHLT_HeadLight | VEHLTMAT_Special1 | `Batmobile_MK2.LensFlareComponent` |
| 25 | `LWheelLight_top` | VEHLT_HeadLight | VEHLTMAT_Special3 | `Batmobile_MK2.LensFlareComponent` |
| 26 | `LWheelLight_bottom` | VEHLT_HeadLight | VEHLTMAT_Special3 | `Batmobile_MK2.LensFlareComponent` |
| 27 | `BootLight` | VEHLT_BootLight | — | `Batmobile_MK2.SpotLightComponent`; `Batmobile_MK2.LensFlareComponent` |

Audio referenced by this object:

| object | class | property |
|---|---|---|
| `Engine.Play_Batmobile_Tazer_Fire` | AkEvent | offset-only |
| `Ww_BML_Batmobile.Play_BattleMode_In_Rev` | AkEvent | offset-only |
| `Ww_BML_Batmobile.Play_BattleMode_Out_Rev` | AkEvent | offset-only |
| `Ww_UI_InGame.Play_HUD_Missile_Lock` | AkEvent | offset-only |
| `VEH_Player.Batmobile_MK2` | AkPlayerVehicleSoundInfo | offset-only |
| `Batmobile_MK2.VehicleSound` | AkVehicleSound | offset-only |

Offset-only floats, sorted by class offset (the property name was stripped by the cooker; the value is real):

```
offset 0x744  0.2000
offset 0x748  0.2000
offset 0x1210  0.7500
offset 0x1214  640000.0000
offset 0x175C  0.0000
offset 0x1760  0.3330
offset 0x1764  90000.0000
offset 0x1768  30000.0000
offset 0x177C  2000.0000
offset 0x1914  150000.0000
offset 0x1A64  2000.0000
offset 0x1A68  2000.0000
offset 0x1ACC  150.0000
offset 0x1AD0  20.0000
offset 0x1AD4  2.2500
offset 0x1ADC  2.0000
offset 0x1AE4  540.0000
offset 0x1AE8  120.0000
offset 0x1AEC  0.5000
offset 0x1C18  -200.0000
offset 0x1C1C  0.5000
offset 0x1C20  10.0000
offset 0x1C24  0.7500
offset 0x1CC4  0.0133
offset 0x1CC8  1.5000
offset 0x1CF8  10000.0000
offset 0x1EEC  2.0000
offset 0x1F24  -1.0000
offset 0x1FDC  6000.0000
offset 0x1FE0  10000.0000
offset 0x1FE4  0.1500
```

### SimulationModel — `RVehicleSimBatmobile` (Playable_BatmobileMK2_SF, 2328 B)

| property | type | offset | value |
|---|---|---|---|
| `BoostTorqueVSpeedCurve` | StructProperty | 0x1DC | 7 curve points |
| `StandardTorqueVSpeedCurve` | StructProperty | 0x1F0 | 6 curve points |
| `BattleModeVSpeedCurve` | StructProperty | 0x218 | 3 curve points |
| `StandardSteeringSpeedCurve` | StructProperty | 0x240 | 5 curve points |
| `TorqueVSpeedCurve` | StructProperty | 0x104 | 6 curve points |
| `SteerSpeedVsSpeedCurve` | StructProperty | 0x194 | 2 curve points |

Curves (x → y), decoded from the nested `Points` array:

```
BoostTorqueVSpeedCurve = -1500.0 → 0.0  -300.0 → 200.0  0.0 → 260.0  1500.0 → 260.0  2100.0 → 220.0  2800.0 → 200.0  3000.0 → 150.0
StandardTorqueVSpeedCurve = -1500.0 → 0.0  -300.0 → 200.0  0.0 → 200.0  750.0 → 170.0  1600.0 → 150.0  2100.0 → 105.0
BattleModeVSpeedCurve = 0.0 → 60.0  600.0 → 40.0  1200.0 → 30.0
StandardSteeringSpeedCurve = 0.0 → 60.0  600.0 → 55.0  1100.0 → 55.0  1300.0 → 30.0  2000.0 → 20.0
TorqueVSpeedCurve = -1500.0 → 0.0  -300.0 → 200.0  0.0 → 130.0  750.0 → 130.0  1050.0 → 60.0  1100.0 → 0.0
SteerSpeedVsSpeedCurve = 0.0 → 720.0  3500.0 → 720.0
```

Offset-only floats, sorted by class offset (the property name was stripped by the cooker; the value is real):

```
offset 0x0DC  220.0000
offset 0x0EC  300.0000
offset 0x164  10000.0000
offset 0x168  1.0000
offset 0x190  100000.0000
offset 0x1C8  0.8000
offset 0x1CC  -0.8000
offset 0x1D0  2.0000
offset 0x2AC  1.5000
offset 0x2C4  600.0000
offset 0x2D4  0.7500
offset 0x2D8  1.2500
offset 0x2E0  0.3333
offset 0x2EC  10.0000
offset 0x2F4  500.0000
offset 0x2F8  30.0000
offset 0x300  1.0000
offset 0x304  3000.0000
offset 0x308  300.0000
offset 0x30C  50.0000
offset 0x310  10.0000
offset 0x318  100.0000
offset 0x320  -0.2500
offset 0x324  20.0000
offset 0x32C  750.0000
offset 0x334  20.0000
offset 0x33C  5.0000
offset 0x390  3000.0000
offset 0x394  24000.0000
offset 0x4A8  8000.0000
```

### Batmobile — `RVehicleBatmobile` (Playable_Batmobile_SF, 3905 B)

| property | type | offset | value |
|---|---|---|---|
| `ExplosiveImpactScreenShake` | StructProperty | 0x19C4 | {5 props} |
| `ImpactShake` | StructProperty | 0x1C28 | {7 props} |
| `DeathExplosionSoundArray` | ArrayProperty | 0x1D08 | 2 items |
| `WeaponGeneratorMeshPackage` | ArrayProperty | 0x1FF8 | 3 items |
| `WeaponGeneratorMesh` | ArrayProperty | 0x2008 | 3 items [0.0, 0.0, 0.0] |
| `InteriorLightsSwitchedOn` | ByteProperty | 0x86D | 1 |
| `Wheels` | ArrayProperty | 0x6AC | 4 items |

Light rig (28 entries, each a `VehicleLights` struct):

| # | bone | Type | MaterialType | components |
|---|---|---|---|---|
| 0 | `HeadLight1` | VEHLT_HeadLight | VEHLTMAT_HeadLightRight | `Batmobile.SpotLightComponent`; `Batmobile.LensFlareComponent`; `Batmobile.SpotLightComponent` |
| 1 | `HeadLight2` | VEHLT_HeadLight | VEHLTMAT_HeadLightLeft | `Batmobile.SpotLightComponent`; `Batmobile.LensFlareComponent` |
| 2 | `ChainGunMuzzle` | None | — | `Batmobile.SpotLightComponent` |
| 3 | `HeadLight1` | None | VEHLTMAT_HeadLightRight | `Batmobile.SpotLightComponent` |
| 4 | `HeadLight2` | None | VEHLTMAT_HeadLightLeft | `Batmobile.SpotLightComponent` |
| 5 | `LWheelLight` | VEHLT_HeadLight | VEHLTMAT_Special3 | `Batmobile.SpotLightComponent`; `Batmobile.LensFlareComponent` |
| 6 | `RWheelLight` | VEHLT_HeadLight | VEHLTMAT_Special1 | `Batmobile.SpotLightComponent`; `Batmobile.LensFlareComponent` |
| 7 | `BrakeLightL` | VEHLT_TailLight | VEHLTMAT_TailLightLeft | `Batmobile.PointLightComponent`; `Batmobile.LensFlareComponent` |
| 8 | `BrakeLightR` | VEHLT_TailLight | VEHLTMAT_TailLightRight | `Batmobile.PointLightComponent`; `Batmobile.LensFlareComponent` |
| 9 | `BattleModeSpotLight` | VEHLT_BattleModeLight | — | `Batmobile.SpotLightComponent` |
| 10 | `HeadLight1` | VEHLT_BattleModeLight | VEHLTMAT_HeadLightRight | `Batmobile.SpotLightComponent` |
| 11 | `HeadLight2` | VEHLT_BattleModeLight | VEHLTMAT_HeadLightLeft | `Batmobile.SpotLightComponent` |
| 12 | `LWheelLight` | VEHLT_BattleModeLight | VEHLTMAT_Special3 | `Batmobile.SpotLightComponent` |
| 13 | `BattleModeSpotLight` | VEHLT_ForensicsLight | — | `Batmobile.RHelicopterSpotLightComponent` |
| 14 | `HeadLight1` | VEHLT_ForensicsLight | VEHLTMAT_HeadLightRight | `Batmobile.SpotLightComponent` |
| 15 | `HeadLight2` | VEHLT_ForensicsLight | VEHLTMAT_HeadLightLeft | `Batmobile.SpotLightComponent` |
| 16 | `Dashboard_Light` | VEHLT_Interior | VEHLTMAT_Interior | `Batmobile.SpotLightComponent` |
| 17 | `HeadLight1a` | VEHLT_HeadLight | — | `Batmobile.LensFlareComponent` |
| 18 | `HeadLight2a` | VEHLT_HeadLight | — | `Batmobile.LensFlareComponent` |
| 19 | `HeadLight1b` | VEHLT_HeadLight | — | `Batmobile.LensFlareComponent` |
| 20 | `HeadLight1c` | VEHLT_HeadLight | — | `Batmobile.LensFlareComponent` |
| 21 | `HeadLight2b` | VEHLT_HeadLight | — | `Batmobile.LensFlareComponent` |
| 22 | `HeadLight2c` | VEHLT_HeadLight | — | `Batmobile.LensFlareComponent` |
| 23 | `RWheelLight_top` | VEHLT_HeadLight | VEHLTMAT_Special1 | `Batmobile.LensFlareComponent` |
| 24 | `RWheelLight_bottom` | VEHLT_HeadLight | VEHLTMAT_Special1 | `Batmobile.LensFlareComponent` |
| 25 | `LWheelLight_top` | VEHLT_HeadLight | VEHLTMAT_Special3 | `Batmobile.LensFlareComponent` |
| 26 | `LWheelLight_bottom` | VEHLT_HeadLight | VEHLTMAT_Special3 | `Batmobile.LensFlareComponent` |
| 27 | `BootLight` | VEHLT_BootLight | — | `Batmobile.SpotLightComponent`; `Batmobile.LensFlareComponent` |

Audio referenced by this object:

| object | class | property |
|---|---|---|
| `Engine.Play_Batmobile_Tazer_Fire` | AkEvent | offset-only |
| `Ww_BML_Batmobile.Play_BattleMode_In_Rev` | AkEvent | offset-only |
| `Ww_BML_Batmobile.Play_BattleMode_Out_Rev` | AkEvent | offset-only |
| `Ww_UI_InGame.Play_HUD_Missile_Lock` | AkEvent | offset-only |
| `VEH_Player.Batmobile` | AkPlayerVehicleSoundInfo | offset-only |
| `Batmobile.VehicleSound` | AkVehicleSound | offset-only |

Offset-only floats, sorted by class offset (the property name was stripped by the cooker; the value is real):

```
offset 0x744  0.2000
offset 0x748  0.2000
offset 0x1210  0.7500
offset 0x1214  640000.0000
offset 0x175C  0.0000
offset 0x1760  0.3330
offset 0x1764  90000.0000
offset 0x1768  30000.0000
offset 0x177C  2000.0000
offset 0x1914  150000.0000
offset 0x1A64  2000.0000
offset 0x1A68  2000.0000
offset 0x1ACC  150.0000
offset 0x1AD0  20.0000
offset 0x1AD4  2.2500
offset 0x1ADC  2.0000
offset 0x1AE4  540.0000
offset 0x1AE8  120.0000
offset 0x1AEC  0.5000
offset 0x1C18  -200.0000
offset 0x1C1C  0.5000
offset 0x1C20  10.0000
offset 0x1C24  0.7500
offset 0x1CC4  0.0133
offset 0x1CC8  1.5000
offset 0x1CF8  10000.0000
offset 0x1EEC  2.0000
offset 0x1F24  -1.0000
offset 0x1FDC  6000.0000
offset 0x1FE0  10000.0000
offset 0x1FE4  0.1500
```

### SimulationModel — `RVehicleSimBatmobile` (Playable_Batmobile_SF, 2328 B)

| property | type | offset | value |
|---|---|---|---|
| `BoostTorqueVSpeedCurve` | StructProperty | 0x1DC | 7 curve points |
| `StandardTorqueVSpeedCurve` | StructProperty | 0x1F0 | 6 curve points |
| `BattleModeVSpeedCurve` | StructProperty | 0x218 | 3 curve points |
| `StandardSteeringSpeedCurve` | StructProperty | 0x240 | 5 curve points |
| `TorqueVSpeedCurve` | StructProperty | 0x104 | 6 curve points |
| `SteerSpeedVsSpeedCurve` | StructProperty | 0x194 | 2 curve points |

Curves (x → y), decoded from the nested `Points` array:

```
BoostTorqueVSpeedCurve = -1500.0 → 0.0  -300.0 → 200.0  0.0 → 260.0  1500.0 → 260.0  2100.0 → 220.0  2800.0 → 200.0  3000.0 → 150.0
StandardTorqueVSpeedCurve = -1500.0 → 0.0  -300.0 → 200.0  0.0 → 200.0  750.0 → 170.0  1600.0 → 150.0  2100.0 → 105.0
BattleModeVSpeedCurve = 0.0 → 60.0  600.0 → 40.0  1200.0 → 30.0
StandardSteeringSpeedCurve = 0.0 → 60.0  600.0 → 55.0  1100.0 → 55.0  1300.0 → 30.0  2000.0 → 20.0
TorqueVSpeedCurve = -1500.0 → 0.0  -300.0 → 200.0  0.0 → 130.0  750.0 → 130.0  1050.0 → 60.0  1100.0 → 0.0
SteerSpeedVsSpeedCurve = 0.0 → 720.0  3500.0 → 720.0
```

Offset-only floats, sorted by class offset (the property name was stripped by the cooker; the value is real):

```
offset 0x0DC  220.0000
offset 0x0EC  300.0000
offset 0x164  10000.0000
offset 0x168  1.0000
offset 0x190  100000.0000
offset 0x1C8  0.8000
offset 0x1CC  -0.8000
offset 0x1D0  2.0000
offset 0x2AC  1.5000
offset 0x2C4  600.0000
offset 0x2D4  0.7500
offset 0x2D8  1.2500
offset 0x2E0  0.3333
offset 0x2EC  10.0000
offset 0x2F4  500.0000
offset 0x2F8  30.0000
offset 0x300  1.0000
offset 0x304  3000.0000
offset 0x308  300.0000
offset 0x30C  50.0000
offset 0x310  10.0000
offset 0x318  100.0000
offset 0x320  -0.2500
offset 0x324  20.0000
offset 0x32C  750.0000
offset 0x334  20.0000
offset 0x33C  5.0000
offset 0x390  3000.0000
offset 0x394  24000.0000
offset 0x4A8  8000.0000
```

## Wheels and components

| package | component | bytes | reference classes | first references |
|---|---|---|---|---|
| Playable_BatmobileFunhouse_SF | `WheelFL` | 191 | ParticleSystem ×12 | `Engine.Batmobile_Burnout`; `Engine.Water_Splash`; `Engine.tyreMarks_ribbonTest`; `Impacts.Batmobile_Wheels_Wood_Collision`; `Mud.Batmobile_Mud_Trail`; `Particles.Batmobile_Burnout_MUD` |
| Playable_BatmobileFunhouse_SF | `WheelFR` | 191 | ParticleSystem ×12 | `Engine.Batmobile_Burnout`; `Engine.Water_Splash`; `Engine.tyreMarks_ribbonTest`; `Impacts.Batmobile_Wheels_Wood_Collision`; `Mud.Batmobile_Mud_Trail`; `Particles.Batmobile_Burnout_MUD` |
| Playable_BatmobileFunhouse_SF | `WheelRL` | 178 | ParticleSystem ×13 | `Engine.Batmobile_Burnout`; `Engine.Water_Splash`; `Engine.tyreMarks_ribbonTest`; `Impacts.Batmobile_Wheels_Wood_Collision`; `Mud.Batmobile_Mud_Trail`; `Particles.Batmobile_Burnout_MUD` |
| Playable_BatmobileFunhouse_SF | `WheelRR` | 166 | ParticleSystem ×13 | `Engine.Batmobile_Burnout`; `Engine.Water_Splash`; `Engine.tyreMarks_ribbonTest`; `Impacts.Batmobile_Wheels_Wood_Collision`; `Mud.Batmobile_Mud_Trail`; `Particles.Batmobile_Burnout_MUD` |
| Playable_BatmobileJoker_SF | `WheelFL` | 78 | ParticleSystem ×4 | `Engine.Batmobile_Burnout`; `Mud.Batmobile_Mud_Trail`; `Particles.Batmobile_FearGas_Burnout`; `Particles.Batmobile_FearGas_KickUp` |
| Playable_BatmobileJoker_SF | `WheelFR` | 46 | — | — |
| Playable_BatmobileJoker_SF | `WheelRL` | 54 | — | — |
| Playable_BatmobileJoker_SF | `WheelRR` | 54 | — | — |
| Playable_BatmobileMK2_SF | `WheelFL` | 191 | ParticleSystem ×12 | `Engine.Batmobile_Burnout`; `Engine.Water_Splash`; `Engine.tyreMarks_ribbonTest`; `Impacts.Batmobile_Wheels_Wood_Collision`; `Mud.Batmobile_Mud_Trail`; `Particles.Batmobile_Burnout_MUD` |
| Playable_BatmobileMK2_SF | `WheelFR` | 191 | ParticleSystem ×12 | `Engine.Batmobile_Burnout`; `Engine.Water_Splash`; `Engine.tyreMarks_ribbonTest`; `Impacts.Batmobile_Wheels_Wood_Collision`; `Mud.Batmobile_Mud_Trail`; `Particles.Batmobile_Burnout_MUD` |
| Playable_BatmobileMK2_SF | `WheelRL` | 178 | ParticleSystem ×13 | `Engine.Batmobile_Burnout`; `Engine.Water_Splash`; `Engine.tyreMarks_ribbonTest`; `Impacts.Batmobile_Wheels_Wood_Collision`; `Mud.Batmobile_Mud_Trail`; `Particles.Batmobile_Burnout_MUD` |
| Playable_BatmobileMK2_SF | `WheelRR` | 166 | ParticleSystem ×13 | `Engine.Batmobile_Burnout`; `Engine.Water_Splash`; `Engine.tyreMarks_ribbonTest`; `Impacts.Batmobile_Wheels_Wood_Collision`; `Mud.Batmobile_Mud_Trail`; `Particles.Batmobile_Burnout_MUD` |
| Playable_Batmobile_SF | `WheelFL` | 191 | ParticleSystem ×12 | `Engine.Batmobile_Burnout`; `Engine.Water_Splash`; `Engine.tyreMarks_ribbonTest`; `Impacts.Batmobile_Wheels_Wood_Collision`; `Mud.Batmobile_Mud_Trail`; `Particles.Batmobile_Burnout_MUD` |
| Playable_Batmobile_SF | `WheelFR` | 191 | ParticleSystem ×12 | `Engine.Batmobile_Burnout`; `Engine.Water_Splash`; `Engine.tyreMarks_ribbonTest`; `Impacts.Batmobile_Wheels_Wood_Collision`; `Mud.Batmobile_Mud_Trail`; `Particles.Batmobile_Burnout_MUD` |
| Playable_Batmobile_SF | `WheelRL` | 178 | ParticleSystem ×13 | `Engine.Batmobile_Burnout`; `Engine.Water_Splash`; `Engine.tyreMarks_ribbonTest`; `Impacts.Batmobile_Wheels_Wood_Collision`; `Mud.Batmobile_Mud_Trail`; `Particles.Batmobile_Burnout_MUD` |
| Playable_Batmobile_SF | `WheelRR` | 166 | ParticleSystem ×13 | `Engine.Batmobile_Burnout`; `Engine.Water_Splash`; `Engine.tyreMarks_ribbonTest`; `Impacts.Batmobile_Wheels_Wood_Collision`; `Mud.Batmobile_Mud_Trail`; `Particles.Batmobile_Burnout_MUD` |

## Physics

| package | physics asset | bytes | bodies |
|---|---|---|---|
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Destroyed_Physics` | 1426 | 32 |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Destroyed_Physics` | 1426 | 32 |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Destroyed_Physics` | 1426 | 32 |
| Playable_Batmobile_SF | `Batmobile_V3_Destroyed_Physics` | 1426 | 32 |

## Meshes

| package | mesh | bytes | LODs | sockets | parse |
|---|---|---|---|---|---|
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Destroyed` | 3637836 | 2 | — | end |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Skin` | 20385512 | 3 | 63 | truncated_walk(end) |
| Playable_BatmobileFunhouse_SF | `Batmobile_V2_Fire` | 100628 | 2 | — | end |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Destroyed` | 3637836 | 2 | — | end |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Skin` | 20385512 | 3 | 63 | truncated_walk(end) |
| Playable_BatmobileJoker_SF | `Batwing_Carrier` | 836016 | 2 | 1 | end |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Destroyed` | 3637836 | 2 | — | end |
| Playable_BatmobileMK2_SF | `Batmobile_MK2_Skin` | 20034142 | 3 | 55 | truncated_walk(end) |
| Playable_BatmobileMK2_SF | `Batmobile_V2_Fire` | 100628 | 2 | — | end |
| Playable_Batmobile_SF | `Batmobile_V2` | 20151210 | 3 | 65 | truncated_walk(end) |
| Playable_Batmobile_SF | `Batmobile_V3_Destroyed` | 3637836 | 2 | — | end |
| Playable_Batmobile_SF | `Batmobile_V2_Fire` | 100628 | 2 | — | end |

### Mesh components

| package | component | owner | mesh | anim sets |
|---|---|---|---|---|
| Playable_BatmobileFunhouse_SF | `SkeletalMeshComponent0` | DeadVehicle.Dead_Batmobile | `Batmobile_V2_Mesh.Batmobile_V3_Destroyed` | — |
| Playable_BatmobileFunhouse_SF | `GadgetMesh` | Weapons.Batmobile_Booster | — | — |
| Playable_BatmobileFunhouse_SF | `GadgetMesh` | Weapons.Batmobile_Cannon_V2 | — | — |
| Playable_BatmobileFunhouse_SF | `GadgetMesh` | Weapons.Batmobile_EMP_Burst | — | — |
| Playable_BatmobileFunhouse_SF | `GadgetMesh` | Weapons.Batmobile_EMP_Missile_Launcher | — | — |
| Playable_BatmobileFunhouse_SF | `GadgetMesh` | Weapons.Batmobile_Heavy_Cannon_Primary | — | — |
| Playable_BatmobileFunhouse_SF | `GadgetMesh` | Weapons.Batmobile_Missile_Launcher | — | — |
| Playable_BatmobileFunhouse_SF | `GadgetMesh` | Weapons.Batmobile_Sonar | — | — |
| Playable_BatmobileFunhouse_SF | `GadgetMesh` | Weapons.Batmobile_Winch | — | — |
| Playable_BatmobileFunhouse_SF | `GadgetMesh` | Weapons.Drone_Hacker | — | — |
| Playable_BatmobileFunhouse_SF | `GadgetMesh` | Weapons.Vehicle_Tracker | — | — |
| Playable_BatmobileFunhouse_SF | `BatmobileOnFireMeshComp0` | Vehicle.BatmobileFunhouse | `Meshes.Batmobile_V2_Fire` | — |
| Playable_BatmobileFunhouse_SF | `SVehicleMesh` | Vehicle.BatmobileFunhouse | `Mesh.Batmobile_Jokerfied_Skin` | — |
| Playable_BatmobileJoker_SF | `GadgetMesh` | Weapons.Batmobile_Cannon_V2 | — | — |
| Playable_BatmobileJoker_SF | `GadgetMesh` | BmScript.Default__RBatmobileMissileLauncherJoker | — | — |
| Playable_BatmobileJoker_SF | `SkeletalMeshComponent0` | DeadVehicle.Dead_Batmobile | `Batmobile_V2_Mesh.Batmobile_V3_Destroyed` | — |
| Playable_BatmobileJoker_SF | `GadgetMesh` | Weapons.Batmobile_Booster | — | — |
| Playable_BatmobileJoker_SF | `BatmobileOnFireMeshComp0` | Vehicle.JokersBatmobile | — | — |
| Playable_BatmobileJoker_SF | `SVehicleMesh` | Vehicle.JokersBatmobile | `Mesh.Batmobile_Jokerfied_Skin` | — |
| Playable_BatmobileJoker_SF | `GadgetMesh` | Weapons.Batmobile_JokerCannon_V2 | — | — |
| Playable_BatmobileJoker_SF | `GadgetMesh` | Weapons.Batmobile_JokerHeavy_Cannon | — | — |
| Playable_BatmobileJoker_SF | `GadgetMesh` | Weapons.Batmobile_JokerMissile_Launcher | — | — |
| Playable_BatmobileJoker_SF | `SkeletalMeshComponent0` | Vehicle.Batwing_Rescue_Batmobile | `Batwing_Carrier.Batwing_Carrier` | `Anims.Batwing_Vehicle_AnimTree` |
| Playable_BatmobileJoker_SF | `Mesh` | BmScript.Default__RPawnVillainThugJokerWarehouse | — | — |
| Playable_BatmobileMK2_SF | `SkeletalMeshComponent0` | DeadVehicle.Dead_Batmobile | `Batmobile_V2_Mesh.Batmobile_V3_Destroyed` | — |
| Playable_BatmobileMK2_SF | `GadgetMesh` | Weapons.Batmobile_Booster | — | — |
| Playable_BatmobileMK2_SF | `GadgetMesh` | Weapons.Batmobile_Cannon_V2 | — | — |
| Playable_BatmobileMK2_SF | `GadgetMesh` | Weapons.Batmobile_EMP_Burst | — | — |
| Playable_BatmobileMK2_SF | `GadgetMesh` | Weapons.Batmobile_EMP_Missile_Launcher | — | — |
| Playable_BatmobileMK2_SF | `GadgetMesh` | Weapons.Batmobile_Heavy_Cannon_Primary | — | — |
| Playable_BatmobileMK2_SF | `GadgetMesh` | Weapons.Batmobile_Missile_Launcher | — | — |
| Playable_BatmobileMK2_SF | `GadgetMesh` | Weapons.Batmobile_Sonar | — | — |
| Playable_BatmobileMK2_SF | `GadgetMesh` | Weapons.Batmobile_Winch | — | — |
| Playable_BatmobileMK2_SF | `GadgetMesh` | Weapons.Drone_Hacker | — | — |
| Playable_BatmobileMK2_SF | `GadgetMesh` | Weapons.Vehicle_Tracker | — | — |
| Playable_BatmobileMK2_SF | `BatmobileOnFireMeshComp0` | Vehicle.Batmobile_MK2 | `Meshes.Batmobile_V2_Fire` | — |
| Playable_BatmobileMK2_SF | `SVehicleMesh` | Vehicle.Batmobile_MK2 | `Mesh.Batmobile_MK2_Skin` | — |
| Playable_Batmobile_SF | `SkeletalMeshComponent0` | DeadVehicle.Dead_Batmobile | `Batmobile_V2_Mesh.Batmobile_V3_Destroyed` | — |
| Playable_Batmobile_SF | `BatmobileOnFireMeshComp0` | Vehicle.Batmobile | `Meshes.Batmobile_V2_Fire` | — |
| Playable_Batmobile_SF | `SVehicleMesh` | Vehicle.Batmobile | `Batmobile_V2_Mesh.Batmobile_V2` | — |
| Playable_Batmobile_SF | `GadgetMesh` | Weapons.Batmobile_Booster | — | — |
| Playable_Batmobile_SF | `GadgetMesh` | Weapons.Batmobile_Cannon_V2 | — | — |
| Playable_Batmobile_SF | `GadgetMesh` | Weapons.Batmobile_EMP_Burst | — | — |
| Playable_Batmobile_SF | `GadgetMesh` | Weapons.Batmobile_EMP_Missile_Launcher | — | — |
| Playable_Batmobile_SF | `GadgetMesh` | Weapons.Batmobile_Heavy_Cannon_Primary | — | — |
| Playable_Batmobile_SF | `GadgetMesh` | Weapons.Batmobile_Missile_Launcher | — | — |
| Playable_Batmobile_SF | `GadgetMesh` | Weapons.Batmobile_Sonar | — | — |
| Playable_Batmobile_SF | `GadgetMesh` | Weapons.Batmobile_Winch | — | — |
| Playable_Batmobile_SF | `GadgetMesh` | Weapons.Drone_Hacker | — | — |
| Playable_Batmobile_SF | `GadgetMesh` | Weapons.Vehicle_Tracker | — | — |

## Sockets

Socket objects carry the bone name and the relative location; they are the attach points for lights, muzzles, missiles, afterburners and the driver. The full bone hierarchy lives in the exported mesh (`Working/Appearance/grab/Playable_Batmobile_SF/SkeletalMesh3/Batmobile_V2.pskx`), which is the same mesh these sockets sit on.

| package | socket | bone | relative location |
|---|---|---|---|
| Playable_BatmobileFunhouse_SF | Afterburner | JetSMove | (-205.06, 0.97, -0.50) |
| Playable_BatmobileFunhouse_SF | Afterburner_Front | Batmobile_Chassis_Mesh | (308.46, 0.00, 66.75) |
| Playable_BatmobileFunhouse_SF | RWheelLight | Wheel_Frnt_Right_Disc | (0.38, 46.33, 25.75) |
| Playable_BatmobileFunhouse_SF | LWheelLight | Wheel_Frnt_Left_Disc | (-0.35, 50.69, 26.00) |
| Playable_BatmobileFunhouse_SF | HeadLight2a | Batmobile_Chassis | (311.42, -44.79, 67.00) |
| Playable_BatmobileFunhouse_SF | HeadLight2b | Batmobile_Chassis | (314.92, -41.46, 58.75) |
| Playable_BatmobileFunhouse_SF | RiotSuppressorMuzzle | Batmobile_Rig_Weapons_Riot_Sup_Main | (26.79, 0.00, 0.00) |
| Playable_BatmobileFunhouse_SF | ChainGunMuzzle | Batmobile_Rig_Weapons_Machine_Gun_01 | (97.66, 0.00, -6.75) |
| Playable_BatmobileFunhouse_SF | CannonMuzzle | Batmobile_Rig_Weapons_Heavy_Cannon_Barrrel_02 | (47.35, 0.00, 0.00) |
| Playable_BatmobileFunhouse_SF | BattleModeSpotLight | Batmobile_Rig_Weapons_Drone_Decoder | (14.65, 0.00, 2.50) |
| Playable_BatmobileFunhouse_SF | MissileL | Batmobile_Chassis | (130.11, -59.38, 146.25) |
| Playable_BatmobileFunhouse_SF | MissileR | Batmobile_Chassis | (130.11, 58.88, 146.75) |
| Playable_BatmobileFunhouse_SF | BrakeLightL | SUSP2_Wheel_Rear_Left | (-273.69, -40.90, -15.19) |
| Playable_BatmobileFunhouse_SF | Driver | Batmobile_Chassis | (121.97, 0.25, 84.25) |
| Playable_BatmobileFunhouse_SF | DriverAnimOrigin | Batmobile_Chassis | — |
| Playable_BatmobileFunhouse_SF | ChainGunShells | Batmobile_Rig_Weapons_Machine_Gun_01 | (0.00, 16.59, -0.00) |
| Playable_BatmobileFunhouse_SF | RiotSuppressorShells | Batmobile_Rig_Weapons_Riot_Sup_Main | (0.00, 3.49, -9.29) |
| Playable_BatmobileFunhouse_SF | WinchOrigin | Batmobile_Chassis | (286.55, 0.00, 69.00) |
| Playable_BatmobileFunhouse_SF | HangFromRope_Front_Right | Wheel_Front_Right | (-38.19, -2.09, 460.50) |
| Playable_BatmobileFunhouse_SF | HangFromRope_Rear_Right | Wheel_Rear_Right | (-31.12, -18.33, 460.50) |
| Playable_BatmobileFunhouse_SF | HangFromRope_Front_Left | Wheel_Front_Left | (36.69, -2.41, 460.50) |
| Playable_BatmobileFunhouse_SF | HangFromRope_Rear_Left | Wheel_Rear_Left | (29.24, -17.23, 460.50) |
| Playable_BatmobileFunhouse_SF | LeftGasVent | Batmobile_Chassis | (78.95, -61.96, 147.25) |
| Playable_BatmobileFunhouse_SF | BrakeLightR | SUSP2_Wheel_Rear_Right | (272.57, -40.84, -14.44) |
| Playable_BatmobileFunhouse_SF | RightGasVent | Batmobile_Chassis | (78.95, 61.96, 147.25) |
| Playable_BatmobileFunhouse_SF | BatterySocket | Batmobile_Chassis | (-49.77, -143.37, 119.00) |
| Playable_BatmobileFunhouse_SF | Dashboard | Batmobile_Chassis | (189.17, 0.00, 145.75) |
| Playable_BatmobileFunhouse_SF | RWheelLight_top | Wheel_Frnt_Right_Disc | (0.38, 40.64, 40.00) |
| Playable_BatmobileFunhouse_SF | RWheelLight_bottom | Wheel_Frnt_Right_Disc | (0.35, 53.81, 10.00) |
| Playable_BatmobileFunhouse_SF | LWheelLight_top | Wheel_Frnt_Left_Disc | (-0.12, 40.60, 40.00) |
| Playable_BatmobileFunhouse_SF | LWheelLight_bottom | Wheel_Frnt_Left_Disc | (-0.29, 56.50, 10.50) |
| Playable_BatmobileFunhouse_SF | Mine1 | Batmobile_Rig_Weapons_Projectile_Mine_01 | (2.04, -16.13, 7.32) |
| Playable_BatmobileFunhouse_SF | Mine2 | Batmobile_Rig_Weapons_Projectile_Mine_01 | (2.04, 17.80, 7.32) |
| Playable_BatmobileFunhouse_SF | Mine3 | Batmobile_Rig_Weapons_Projectile_Mine_02 | (2.04, -16.13, 7.32) |
| Playable_BatmobileFunhouse_SF | SpeedLines | Batmobile_Chassis_Mesh | (-323.00, 0.00, 40.00) |
| Playable_BatmobileFunhouse_SF | Mine4 | Batmobile_Rig_Weapons_Projectile_Mine_02 | (2.04, 17.80, 7.32) |
| Playable_BatmobileFunhouse_SF | Mine5 | Batmobile_Rig_Weapons_Projectile_Mine_03 | (2.04, -16.13, 7.32) |
| Playable_BatmobileFunhouse_SF | Mine6 | Batmobile_Rig_Weapons_Projectile_Mine_03 | (2.04, 17.80, 7.32) |
| Playable_BatmobileFunhouse_SF | Mine7 | Batmobile_Rig_Weapons_Projectile_Mine_04 | (2.04, -16.13, 7.32) |
| Playable_BatmobileFunhouse_SF | Mine8 | Batmobile_Rig_Weapons_Projectile_Mine_04 | (2.04, 17.80, 7.32) |
| Playable_BatmobileFunhouse_SF | CockpitRain | Batmobile_Chassis | (143.95, 0.00, 194.25) |
| Playable_BatmobileFunhouse_SF | FearGasTrailL | Batmobile_Chassis | (-230.00, -68.00, 185.00) |
| Playable_BatmobileFunhouse_SF | FearGasTrailR | Batmobile_Chassis | (-230.00, 68.00, 185.00) |
| Playable_BatmobileFunhouse_SF | FearGasTrail2L | Batmobile_Chassis | (-221.61, -63.15, 186.50) |
| Playable_BatmobileFunhouse_SF | FearGasTrail2R | Batmobile_Chassis | (-225.26, 63.20, 194.75) |
| Playable_BatmobileFunhouse_SF | WinchAttach | Batmobile_Chassis | (339.22, 0.00, 70.75) |
| Playable_BatmobileFunhouse_SF | BootLight | Batmobile_Chassis | (-174.50, 2.01, 197.75) |
| Playable_BatmobileFunhouse_SF | ZapperFL | SUSP2_Wheel_Front_Left | (187.62, 0.00, 57.00) |
| Playable_BatmobileFunhouse_SF | ZapperFR | SUSP2_Wheel_Front_Right | (187.62, 0.00, 57.00) |
| Playable_BatmobileFunhouse_SF | ZapperRR | SUSP2_Wheel_Rear_Right | (277.00, -41.00, 65.90) |
| Playable_BatmobileFunhouse_SF | ZapperRL | SUSP2_Wheel_Rear_Left | (-277.00, -41.00, 65.90) |
| Playable_BatmobileFunhouse_SF | BrakeTrailL | SUSP2_Wheel_Rear_Left | (-165.20, -40.55, -16.28) |
| Playable_BatmobileFunhouse_SF | BrakeTrailR | SUSP2_Wheel_Rear_Right | (165.86, -37.49, -19.97) |
| Playable_BatmobileFunhouse_SF | SideExhaustR | Batmobile_Chassis | (18.08, 117.27, 134.44) |
| Playable_BatmobileFunhouse_SF | SideExhaustL | Batmobile_Chassis | (14.60, -117.39, 119.24) |
| Playable_BatmobileFunhouse_SF | Cockpit_Hologram | Batmobile_Chassis | (180.31, -0.29, 163.87) |
| Playable_BatmobileFunhouse_SF | HeadLight1 | Batmobile_Chassis | (320.68, 38.58, 51.00) |
| Playable_BatmobileFunhouse_SF | HydraSocket | Batmobile_Rig_Weapons_Projectile_Mine_02 | (0.00, 0.00, 10.25) |
| Playable_BatmobileFunhouse_SF | ScrapeSparksL | Batmobile_Chassis | (-178.00, -172.00, 103.00) |
| Playable_BatmobileFunhouse_SF | ScrapeSparksR | Batmobile_Chassis | (-178.00, 172.00, 103.00) |
| Playable_BatmobileFunhouse_SF | HeadLight2 | Batmobile_Chassis | (319.19, -38.50, 51.00) |
| Playable_BatmobileFunhouse_SF | HeadLight1a | Batmobile_Chassis | (311.26, 45.27, 67.00) |
| Playable_BatmobileFunhouse_SF | HeadLight1b | Batmobile_Chassis | (316.32, 41.71, 58.75) |
| Playable_BatmobileJoker_SF | Afterburner | JetSMove | (-205.06, 0.97, -0.50) |
| Playable_BatmobileJoker_SF | Afterburner_Front | Batmobile_Chassis_Mesh | (308.46, 0.00, 66.75) |
| Playable_BatmobileJoker_SF | RWheelLight | Wheel_Frnt_Right_Disc | (0.38, 46.33, 25.75) |
| Playable_BatmobileJoker_SF | LWheelLight | Wheel_Frnt_Left_Disc | (-0.35, 50.69, 26.00) |
| Playable_BatmobileJoker_SF | HeadLight2a | Batmobile_Chassis | (311.42, -44.79, 67.00) |
| Playable_BatmobileJoker_SF | HeadLight2b | Batmobile_Chassis | (314.92, -41.46, 58.75) |
| Playable_BatmobileJoker_SF | RiotSuppressorMuzzle | Batmobile_Rig_Weapons_Riot_Sup_Main | (26.79, 0.00, 0.00) |
| Playable_BatmobileJoker_SF | ChainGunMuzzle | Batmobile_Rig_Weapons_Machine_Gun_01 | (97.66, 0.00, -6.75) |
| Playable_BatmobileJoker_SF | CannonMuzzle | Batmobile_Rig_Weapons_Heavy_Cannon_Barrrel_02 | (47.35, 0.00, 0.00) |
| Playable_BatmobileJoker_SF | BattleModeSpotLight | Batmobile_Rig_Weapons_Drone_Decoder | (14.65, 0.00, 2.50) |
| Playable_BatmobileJoker_SF | MissileL | Batmobile_Chassis | (130.11, -59.38, 146.25) |
| Playable_BatmobileJoker_SF | MissileR | Batmobile_Chassis | (130.11, 58.88, 146.75) |
| Playable_BatmobileJoker_SF | BrakeLightL | SUSP2_Wheel_Rear_Left | (-273.69, -40.90, -15.19) |
| Playable_BatmobileJoker_SF | Driver | Batmobile_Chassis | (121.97, 0.25, 84.25) |
| Playable_BatmobileJoker_SF | DriverAnimOrigin | Batmobile_Chassis | — |
| Playable_BatmobileJoker_SF | ChainGunShells | Batmobile_Rig_Weapons_Machine_Gun_01 | (0.00, 16.59, -0.00) |
| Playable_BatmobileJoker_SF | RiotSuppressorShells | Batmobile_Rig_Weapons_Riot_Sup_Main | (0.00, 3.49, -9.29) |
| Playable_BatmobileJoker_SF | WinchOrigin | Batmobile_Chassis | (286.55, 0.00, 69.00) |
| Playable_BatmobileJoker_SF | HangFromRope_Front_Right | Wheel_Front_Right | (-38.19, -2.09, 460.50) |
| Playable_BatmobileJoker_SF | HangFromRope_Rear_Right | Wheel_Rear_Right | (-31.12, -18.33, 460.50) |
| Playable_BatmobileJoker_SF | HangFromRope_Front_Left | Wheel_Front_Left | (36.69, -2.41, 460.50) |
| Playable_BatmobileJoker_SF | HangFromRope_Rear_Left | Wheel_Rear_Left | (29.24, -17.23, 460.50) |
| Playable_BatmobileJoker_SF | LeftGasVent | Batmobile_Chassis | (78.95, -61.96, 147.25) |
| Playable_BatmobileJoker_SF | BrakeLightR | SUSP2_Wheel_Rear_Right | (272.57, -40.84, -14.44) |
| Playable_BatmobileJoker_SF | RightGasVent | Batmobile_Chassis | (78.95, 61.96, 147.25) |
| Playable_BatmobileJoker_SF | BatterySocket | Batmobile_Chassis | (-49.77, -143.37, 119.00) |
| Playable_BatmobileJoker_SF | Dashboard | Batmobile_Chassis | (189.17, 0.00, 145.75) |
| Playable_BatmobileJoker_SF | RWheelLight_top | Wheel_Frnt_Right_Disc | (0.38, 40.64, 40.00) |
| Playable_BatmobileJoker_SF | RWheelLight_bottom | Wheel_Frnt_Right_Disc | (0.35, 53.81, 10.00) |
| Playable_BatmobileJoker_SF | LWheelLight_top | Wheel_Frnt_Left_Disc | (-0.12, 40.60, 40.00) |
| Playable_BatmobileJoker_SF | LWheelLight_bottom | Wheel_Frnt_Left_Disc | (-0.29, 56.50, 10.50) |
| Playable_BatmobileJoker_SF | Mine1 | Batmobile_Rig_Weapons_Projectile_Mine_01 | (2.04, -16.13, 7.32) |
| Playable_BatmobileJoker_SF | Mine2 | Batmobile_Rig_Weapons_Projectile_Mine_01 | (2.04, 17.80, 7.32) |
| Playable_BatmobileJoker_SF | Mine3 | Batmobile_Rig_Weapons_Projectile_Mine_02 | (2.04, -16.13, 7.32) |
| Playable_BatmobileJoker_SF | SpeedLines | Batmobile_Chassis_Mesh | (-323.00, 0.00, 40.00) |
| Playable_BatmobileJoker_SF | Mine4 | Batmobile_Rig_Weapons_Projectile_Mine_02 | (2.04, 17.80, 7.32) |
| Playable_BatmobileJoker_SF | Mine5 | Batmobile_Rig_Weapons_Projectile_Mine_03 | (2.04, -16.13, 7.32) |
| Playable_BatmobileJoker_SF | Mine6 | Batmobile_Rig_Weapons_Projectile_Mine_03 | (2.04, 17.80, 7.32) |
| Playable_BatmobileJoker_SF | Mine7 | Batmobile_Rig_Weapons_Projectile_Mine_04 | (2.04, -16.13, 7.32) |
| Playable_BatmobileJoker_SF | Mine8 | Batmobile_Rig_Weapons_Projectile_Mine_04 | (2.04, 17.80, 7.32) |
| Playable_BatmobileJoker_SF | CockpitRain | Batmobile_Chassis | (143.95, 0.00, 194.25) |
| Playable_BatmobileJoker_SF | FearGasTrailL | Batmobile_Chassis | (-230.00, -68.00, 185.00) |
| Playable_BatmobileJoker_SF | FearGasTrailR | Batmobile_Chassis | (-230.00, 68.00, 185.00) |
| Playable_BatmobileJoker_SF | FearGasTrail2L | Batmobile_Chassis | (-221.61, -63.15, 186.50) |
| Playable_BatmobileJoker_SF | FearGasTrail2R | Batmobile_Chassis | (-225.26, 63.20, 194.75) |
| Playable_BatmobileJoker_SF | WinchAttach | Batmobile_Chassis | (339.22, 0.00, 70.75) |
| Playable_BatmobileJoker_SF | BootLight | Batmobile_Chassis | (-174.50, 2.01, 197.75) |
| Playable_BatmobileJoker_SF | ZapperFL | SUSP2_Wheel_Front_Left | (187.62, 0.00, 57.00) |
| Playable_BatmobileJoker_SF | ZapperFR | SUSP2_Wheel_Front_Right | (187.62, 0.00, 57.00) |
| Playable_BatmobileJoker_SF | ZapperRR | SUSP2_Wheel_Rear_Right | (277.00, -41.00, 65.90) |
| Playable_BatmobileJoker_SF | ZapperRL | SUSP2_Wheel_Rear_Left | (-277.00, -41.00, 65.90) |
| Playable_BatmobileJoker_SF | BrakeTrailL | SUSP2_Wheel_Rear_Left | (-165.20, -40.55, -16.28) |
| Playable_BatmobileJoker_SF | BrakeTrailR | SUSP2_Wheel_Rear_Right | (165.86, -37.49, -19.97) |
| Playable_BatmobileJoker_SF | SideExhaustR | Batmobile_Chassis | (18.08, 117.27, 134.44) |
| Playable_BatmobileJoker_SF | SideExhaustL | Batmobile_Chassis | (14.60, -117.39, 119.24) |
| Playable_BatmobileJoker_SF | Cockpit_Hologram | Batmobile_Chassis | (180.31, -0.29, 163.87) |
| Playable_BatmobileJoker_SF | HeadLight1 | Batmobile_Chassis | (320.68, 38.58, 51.00) |
| Playable_BatmobileJoker_SF | HydraSocket | Batmobile_Rig_Weapons_Projectile_Mine_02 | (0.00, 0.00, 10.25) |
| Playable_BatmobileJoker_SF | ScrapeSparksL | Batmobile_Chassis | (-178.00, -172.00, 103.00) |
| Playable_BatmobileJoker_SF | ScrapeSparksR | Batmobile_Chassis | (-178.00, 172.00, 103.00) |
| Playable_BatmobileJoker_SF | HeadLight2 | Batmobile_Chassis | (319.19, -38.50, 51.00) |
| Playable_BatmobileJoker_SF | HeadLight1a | Batmobile_Chassis | (311.26, 45.27, 67.00) |
| Playable_BatmobileJoker_SF | HeadLight1b | Batmobile_Chassis | (316.32, 41.71, 58.75) |
| Playable_BatmobileJoker_SF | BatmobileAttach | Batwing_Carrier | (-0.00, 179.02, -183.25) |
| Playable_BatmobileMK2_SF | Afterburner | JetSMove | (-205.06, 0.97, -0.50) |
| Playable_BatmobileMK2_SF | Afterburner_Front | Batmobile_Chassis_Mesh | (308.46, 0.00, 66.75) |
| Playable_BatmobileMK2_SF | ScrapeSparksL | Batmobile_Chassis | (-178.00, -172.00, 103.00) |
| Playable_BatmobileMK2_SF | ScrapeSparksR | Batmobile_Chassis | (-178.00, 172.00, 103.00) |
| Playable_BatmobileMK2_SF | HeadLight2a | Batmobile_Chassis | (311.42, -44.79, 67.00) |
| Playable_BatmobileMK2_SF | HeadLight2b | Batmobile_Chassis | (314.92, -41.46, 58.75) |
| Playable_BatmobileMK2_SF | RiotSuppressorMuzzle | Batmobile_Rig_Weapons_Riot_Sup_Main | (26.79, 0.00, 0.00) |
| Playable_BatmobileMK2_SF | ChainGunMuzzle | Batmobile_Rig_Weapons_Machine_Gun_01 | (97.66, 0.00, -6.75) |
| Playable_BatmobileMK2_SF | CannonMuzzle | Batmobile_Rig_Weapons_Heavy_Cannon_Barrrel_02 | (47.35, 0.00, 0.00) |
| Playable_BatmobileMK2_SF | BattleModeSpotLight | Batmobile_Rig_Weapons_Drone_Decoder | (14.65, 0.00, 2.50) |
| Playable_BatmobileMK2_SF | MissileL | Batmobile_Chassis | (130.11, -59.38, 146.25) |
| Playable_BatmobileMK2_SF | MissileR | Batmobile_Chassis | (130.11, 58.88, 146.75) |
| Playable_BatmobileMK2_SF | BrakeLightL | SUSP2_Wheel_Rear_Left | (-273.69, -40.90, -15.19) |
| Playable_BatmobileMK2_SF | Driver | Batmobile_Chassis | (121.97, 0.25, 84.25) |
| Playable_BatmobileMK2_SF | DriverAnimOrigin | Batmobile_Chassis | — |
| Playable_BatmobileMK2_SF | ChainGunShells | Batmobile_Rig_Weapons_Machine_Gun_01 | (0.00, 16.59, -0.00) |
| Playable_BatmobileMK2_SF | RiotSuppressorShells | Batmobile_Rig_Weapons_Riot_Sup_Main | (0.00, 3.49, -9.29) |
| Playable_BatmobileMK2_SF | WinchOrigin | Batmobile_Chassis | (286.55, 0.00, 69.00) |
| Playable_BatmobileMK2_SF | HangFromRope_Front_Right | Wheel_Front_Right | (-38.19, -2.09, 460.50) |
| Playable_BatmobileMK2_SF | HangFromRope_Rear_Right | Wheel_Rear_Right | (-31.12, -18.33, 460.50) |
| Playable_BatmobileMK2_SF | HangFromRope_Front_Left | Wheel_Front_Left | (36.69, -2.41, 460.50) |
| Playable_BatmobileMK2_SF | HangFromRope_Rear_Left | Wheel_Rear_Left | (29.24, -17.23, 460.50) |
| Playable_BatmobileMK2_SF | LeftGasVent | Batmobile_Chassis | (78.95, -61.96, 147.25) |
| Playable_BatmobileMK2_SF | BrakeLightR | SUSP2_Wheel_Rear_Right | (272.57, -40.84, -14.44) |
| Playable_BatmobileMK2_SF | RightGasVent | Batmobile_Chassis | (78.95, 61.96, 147.25) |
| Playable_BatmobileMK2_SF | BatterySocket | Batmobile_Chassis | (-49.77, -143.37, 119.00) |
| Playable_BatmobileMK2_SF | Dashboard | Batmobile_Chassis | (189.17, 0.00, 145.75) |
| Playable_BatmobileMK2_SF | Mine1 | Batmobile_Rig_Weapons_Projectile_Mine_01 | (2.04, -16.13, 7.32) |
| Playable_BatmobileMK2_SF | Mine2 | Batmobile_Rig_Weapons_Projectile_Mine_01 | (2.04, 17.80, 7.32) |
| Playable_BatmobileMK2_SF | Mine3 | Batmobile_Rig_Weapons_Projectile_Mine_02 | (2.04, -16.13, 7.32) |
| Playable_BatmobileMK2_SF | SpeedLines | Batmobile_Chassis_Mesh | (-323.00, 0.00, 40.00) |
| Playable_BatmobileMK2_SF | Mine4 | Batmobile_Rig_Weapons_Projectile_Mine_02 | (2.04, 17.80, 7.32) |
| Playable_BatmobileMK2_SF | Mine5 | Batmobile_Rig_Weapons_Projectile_Mine_03 | (2.04, -16.13, 7.32) |
| Playable_BatmobileMK2_SF | Mine6 | Batmobile_Rig_Weapons_Projectile_Mine_03 | (2.04, 17.80, 7.32) |
| Playable_BatmobileMK2_SF | Mine7 | Batmobile_Rig_Weapons_Projectile_Mine_04 | (2.04, -16.13, 7.32) |
| Playable_BatmobileMK2_SF | Mine8 | Batmobile_Rig_Weapons_Projectile_Mine_04 | (2.04, 17.80, 7.32) |
| Playable_BatmobileMK2_SF | CockpitRain | Batmobile_Chassis | (143.95, 0.00, 194.25) |
| Playable_BatmobileMK2_SF | FearGasTrailL | Batmobile_Chassis | (-230.00, -68.00, 185.00) |
| Playable_BatmobileMK2_SF | FearGasTrailR | Batmobile_Chassis | (-230.00, 68.00, 185.00) |
| Playable_BatmobileMK2_SF | FearGasTrail2L | Batmobile_Chassis | (-221.61, -63.15, 186.50) |
| Playable_BatmobileMK2_SF | FearGasTrail2R | Batmobile_Chassis | (-225.26, 63.20, 194.75) |
| Playable_BatmobileMK2_SF | WinchAttach | Batmobile_Chassis | (339.22, 0.00, 70.75) |
| Playable_BatmobileMK2_SF | BootLight | Batmobile_Chassis | (-174.50, 2.01, 197.75) |
| Playable_BatmobileMK2_SF | ZapperFL | SUSP2_Wheel_Front_Left | (187.62, 0.00, 57.00) |
| Playable_BatmobileMK2_SF | ZapperFR | SUSP2_Wheel_Front_Right | (187.62, 0.00, 57.00) |
| Playable_BatmobileMK2_SF | ZapperRR | SUSP2_Wheel_Rear_Right | (277.00, -41.00, 65.90) |
| Playable_BatmobileMK2_SF | ZapperRL | SUSP2_Wheel_Rear_Left | (-277.00, -41.00, 65.90) |
| Playable_BatmobileMK2_SF | SideExhaustR | Batmobile_Chassis | (18.08, 117.27, 134.44) |
| Playable_BatmobileMK2_SF | SideExhaustL | Batmobile_Chassis | (14.60, -117.39, 119.24) |
| Playable_BatmobileMK2_SF | Cockpit_Hologram | Batmobile_Chassis | (180.31, -0.29, 163.87) |
| Playable_BatmobileMK2_SF | HeadLight1 | Batmobile_Chassis | (320.68, 38.58, 51.00) |
| Playable_BatmobileMK2_SF | PassengerNoiseOrigin | Batmobile_Chassis | (-238.51, 0.00, 122.75) |
| Playable_BatmobileMK2_SF | HeadLight2 | Batmobile_Chassis | (319.19, -38.50, 51.00) |
| Playable_BatmobileMK2_SF | HeadLight1a | Batmobile_Chassis | (311.26, 45.27, 67.00) |
| Playable_BatmobileMK2_SF | HeadLight1b | Batmobile_Chassis | (316.32, 41.71, 58.75) |
| Playable_Batmobile_SF | Afterburner | JetSMove | (-205.06, 0.97, -0.50) |
| Playable_Batmobile_SF | Afterburner_Front | Batmobile_Chassis_Mesh | (308.46, 0.00, 66.75) |
| Playable_Batmobile_SF | ZapperFL | SUSP2_Wheel_Front_Left | (187.62, 0.00, 57.00) |
| Playable_Batmobile_SF | RWheelLight | Wheel_Frnt_Right_Disc | (0.38, 46.33, 25.75) |
| Playable_Batmobile_SF | LWheelLight | Wheel_Frnt_Left_Disc | (-0.35, 50.69, 26.00) |
| Playable_Batmobile_SF | HeadLight2a | Winch_DOOR_Mesh | (21.29, -44.77, -44.25) |
| Playable_Batmobile_SF | HeadLight2b | Winch_DOOR_Mesh | (24.30, -41.63, -52.50) |
| Playable_Batmobile_SF | ZapperFR | SUSP2_Wheel_Front_Right | (187.62, 0.00, 57.00) |
| Playable_Batmobile_SF | RiotSuppressorMuzzle | Batmobile_Rig_Weapons_Riot_Sup_Main | (26.79, 0.00, 0.00) |
| Playable_Batmobile_SF | ChainGunMuzzle | Batmobile_Rig_Weapons_Machine_Gun_01 | (97.66, 0.00, -6.75) |
| Playable_Batmobile_SF | CannonMuzzle | Batmobile_Rig_Weapons_Heavy_Cannon_Barrrel_02 | (47.35, 0.00, 0.00) |
| Playable_Batmobile_SF | BattleModeSpotLight | Batmobile_Rig_Weapons_Drone_Decoder | (14.65, 0.00, 2.50) |
| Playable_Batmobile_SF | BrakeLightL | SUSP2_Wheel_Rear_Left | (-273.69, -40.90, -15.19) |
| Playable_Batmobile_SF | MissileL | Batmobile_Chassis | (130.11, -59.38, 146.25) |
| Playable_Batmobile_SF | MissileR | Batmobile_Chassis | (130.11, 58.88, 146.75) |
| Playable_Batmobile_SF | Driver | Batmobile_Chassis | (121.97, 0.25, 84.25) |
| Playable_Batmobile_SF | DriverAnimOrigin | Batmobile_Chassis | — |
| Playable_Batmobile_SF | ChainGunShells | Batmobile_Rig_Weapons_Machine_Gun_01 | (0.00, 16.59, -0.00) |
| Playable_Batmobile_SF | RiotSuppressorShells | Batmobile_Rig_Weapons_Riot_Sup_Main | (0.00, 3.49, -9.29) |
| Playable_Batmobile_SF | WinchOrigin | Batmobile_Chassis | (286.55, 0.00, 59.00) |
| Playable_Batmobile_SF | HangFromRope_Front_Right | Wheel_Front_Right | (-38.19, -2.09, 460.50) |
| Playable_Batmobile_SF | HangFromRope_Rear_Right | Wheel_Rear_Right | (-31.12, -18.33, 460.50) |
| Playable_Batmobile_SF | HangFromRope_Front_Left | Wheel_Front_Left | (36.69, -2.41, 460.50) |
| Playable_Batmobile_SF | BrakeLightR | SUSP2_Wheel_Rear_Right | (272.57, -40.84, -14.44) |
| Playable_Batmobile_SF | HangFromRope_Rear_Left | Wheel_Rear_Left | (29.24, -17.23, 460.50) |
| Playable_Batmobile_SF | LeftGasVent | Batmobile_Chassis | (78.95, -61.96, 147.25) |
| Playable_Batmobile_SF | RightGasVent | Batmobile_Chassis | (78.95, 61.96, 147.25) |
| Playable_Batmobile_SF | BatterySocket | Batmobile_Chassis | (-49.77, -143.37, 119.00) |
| Playable_Batmobile_SF | Dashboard | Batmobile_Chassis | (189.17, 0.00, 145.75) |
| Playable_Batmobile_SF | RWheelLight_top | Wheel_Frnt_Right_Disc | (0.38, 40.64, 40.00) |
| Playable_Batmobile_SF | RWheelLight_bottom | Wheel_Frnt_Right_Disc | (0.35, 53.81, 10.00) |
| Playable_Batmobile_SF | LWheelLight_top | Wheel_Frnt_Left_Disc | (-0.12, 40.60, 40.00) |
| Playable_Batmobile_SF | LWheelLight_bottom | Wheel_Frnt_Left_Disc | (-0.29, 56.50, 10.50) |
| Playable_Batmobile_SF | Mine1 | Batmobile_Rig_Weapons_Projectile_Mine_01 | (2.04, -16.13, 7.32) |
| Playable_Batmobile_SF | SpeedLines | Batmobile_Chassis_Mesh | (-323.00, 0.00, 40.00) |
| Playable_Batmobile_SF | Mine2 | Batmobile_Rig_Weapons_Projectile_Mine_01 | (2.04, 17.80, 7.32) |
| Playable_Batmobile_SF | Mine3 | Batmobile_Rig_Weapons_Projectile_Mine_02 | (2.04, -16.13, 7.32) |
| Playable_Batmobile_SF | Mine4 | Batmobile_Rig_Weapons_Projectile_Mine_02 | (2.04, 17.80, 7.32) |
| Playable_Batmobile_SF | Mine5 | Batmobile_Rig_Weapons_Projectile_Mine_03 | (2.04, -16.13, 7.32) |
| Playable_Batmobile_SF | Mine6 | Batmobile_Rig_Weapons_Projectile_Mine_03 | (2.04, 17.80, 7.32) |
| Playable_Batmobile_SF | Mine7 | Batmobile_Rig_Weapons_Projectile_Mine_04 | (2.04, -16.13, 7.32) |
| Playable_Batmobile_SF | Mine8 | Batmobile_Rig_Weapons_Projectile_Mine_04 | (2.04, 17.80, 7.32) |
| Playable_Batmobile_SF | CockpitRain | Batmobile_Chassis | (143.95, 0.00, 194.25) |
| Playable_Batmobile_SF | FearGasTrailL | Batmobile_Chassis | (-230.00, -68.00, 185.00) |
| Playable_Batmobile_SF | FearGasTrailR | Batmobile_Chassis | (-230.00, 68.00, 185.00) |
| Playable_Batmobile_SF | WinchAttach | Batmobile_Chassis | (339.22, 0.00, 70.75) |
| Playable_Batmobile_SF | FearGasTrail2L | Batmobile_Chassis | (-221.61, -63.15, 186.50) |
| Playable_Batmobile_SF | FearGasTrail2R | Batmobile_Chassis | (-225.26, 63.20, 194.75) |
| Playable_Batmobile_SF | BootLight | Batmobile_Chassis | (-174.50, 2.01, 197.75) |
| Playable_Batmobile_SF | ZapperRR | SUSP2_Wheel_Rear_Right | (277.00, -41.00, 65.90) |
| Playable_Batmobile_SF | ZapperRL | SUSP2_Wheel_Rear_Left | (-277.00, -41.00, 65.90) |
| Playable_Batmobile_SF | BrakeTrailL | SUSP2_Wheel_Rear_Left | (-165.20, -40.55, -16.28) |
| Playable_Batmobile_SF | BrakeTrailR | SUSP2_Wheel_Rear_Right | (165.86, -37.49, -19.97) |
| Playable_Batmobile_SF | SideExhaustR | Batmobile_Chassis | (18.08, 117.27, 134.44) |
| Playable_Batmobile_SF | SideExhaustL | Batmobile_Chassis | (14.60, -117.39, 119.24) |
| Playable_Batmobile_SF | Cockpit_Hologram | Batmobile_Chassis | (180.31, -0.29, 163.87) |
| Playable_Batmobile_SF | HeadLight1 | Winch_DOOR_Mesh | (21.29, 45.19, -44.25) |
| Playable_Batmobile_SF | Headlight_Centre | Batmobile_Chassis | (331.42, 0.00, 63.25) |
| Playable_Batmobile_SF | Dashboard_Light | Batmobile_Chassis | (182.95, 0.00, 144.25) |
| Playable_Batmobile_SF | ScrapeSparksL | Batmobile_Chassis | (-178.69, -172.12, 103.50) |
| Playable_Batmobile_SF | ScrapeSparksR | Batmobile_Chassis | (-178.69, 172.12, 103.50) |
| Playable_Batmobile_SF | PassengerNoiseOrigin | Batmobile_Chassis | (-236.32, 0.00, 129.25) |
| Playable_Batmobile_SF | HeadLight2 | Winch_DOOR_Mesh | (28.22, -38.59, -61.00) |
| Playable_Batmobile_SF | HeadLight1a | Winch_DOOR_Mesh | (24.30, 42.02, -52.50) |
| Playable_Batmobile_SF | HeadLight1b | Winch_DOOR_Mesh | (28.22, 38.30, -61.00) |

## Animation

| package | name | class | bytes | first float | first int |
|---|---|---|---|---|---|
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 18 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 24783 | 2.0 | 61 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 17745 | 3.1666667461395264 | 96 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 1010 | 0.5 | 16 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 668 | 0.03333333507180214 | 2 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 994 | 0.4333333373069763 | 14 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 11352 | 4.566666603088379 | 138 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 1229 | 0.30000001192092896 | 10 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 568 | 0.30000001192092896 | 10 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 6742 | 2.700000047683716 | 82 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 2034 | 0.6000000238418579 | 19 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 4142 | 1.0 | 31 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 2908 | 0.699999988079071 | 22 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 1633 | 1.7666666507720947 | 54 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 2000 | 3.933333396911621 | 119 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 1864 | 0.6000000238418579 | 19 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 24688 | 2.0 | 61 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 1270 | 0.03333333507180214 | 2 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 25167 | 2.0 | 61 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 7812 | 2.5999999046325684 | 79 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 281 | 0.03333333507180214 | 2 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 22948 | 2.0 | 61 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 22781 | 2.0 | 61 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 2344 | 3.3333332538604736 | 101 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 344 | 0.6666666865348816 | 21 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 10951 | 1.2000000476837158 | 37 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 3248 | 0.8333333134651184 | 26 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 1083 | 0.8333333134651184 | 26 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 1115 | 0.8333333134651184 | 26 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 1128 | 0.8333333134651184 | 26 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 3883 | 0.9333333373069763 | 29 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 3738 | 2.2666666507720947 | 69 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 3584 | 2.2333333492279053 | 68 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 985 | 0.8333333134651184 | 26 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 2611 | 0.8333333134651184 | 26 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 1178 | 0.8333333134651184 | 26 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 2355 | 0.46666666865348816 | 15 |
| Playable_BatmobileFunhouse_SF | `AnimSequence` | AnimSequence | 2440 | 0.46666666865348816 | 15 |
| Playable_BatmobileFunhouse_SF | `BM_Batmobile_Chassis` | AnimSet | 1194 | — | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V2_Pose_States` | AnimSet | 1598 | — | — |
| Playable_BatmobileFunhouse_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileFunhouse_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileFunhouse_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 2 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 18 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileJoker_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 24783 | 2.0 | 61 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 17745 | 3.1666667461395264 | 96 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1010 | 0.5 | 16 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 668 | 0.03333333507180214 | 2 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 994 | 0.4333333373069763 | 14 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 9834 | 12.166666984558105 | 366 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 2678 | 3.0333333015441895 | 92 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 2600 | 2.933333396911621 | 89 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 852 | 0.8999999761581421 | 28 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 284 | 0.03333333507180214 | 2 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 8128 | 10.0 | 301 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1420 | 1.399999976158142 | 43 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 5124 | 7.333333492279053 | 221 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 6424 | 7.833333492279053 | 236 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 4202 | 4.9666666984558105 | 150 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 2304 | 2.5333333015441895 | 77 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 6048 | 7.333333492279053 | 221 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 5476 | 7.866666793823242 | 237 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 2976 | 12.600000381469727 | 379 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 9184 | 12.600000381469727 | 379 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 35360 | 44.93333435058594 | 1349 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 51366 | 65.4000015258789 | 1963 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 25897 | 32.79999923706055 | 985 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 6188 | 7.5333333015441895 | 227 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 2002 | 2.1666667461395264 | 66 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 6864 | 8.133333206176758 | 245 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 15748 | 20.66666603088379 | 621 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1602 | 1.6333333253860474 | 50 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1436 | 9.233333587646484 | 278 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 6864 | 8.133333206176758 | 245 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1040 | 0.9333333373069763 | 29 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1212 | 3.0 | 91 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 910 | 0.7666666507720947 | 24 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 5542 | 7.9666666984558105 | 240 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 858 | 0.699999988079071 | 22 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 6048 | 7.333333492279053 | 221 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 4678 | 6.633333206176758 | 200 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 26469 | 33.53333282470703 | 1007 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 46098 | 58.70000076293945 | 1762 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 27119 | 34.36666488647461 | 1032 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 6188 | 7.5333333015441895 | 227 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 19968 | 25.200000762939453 | 757 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 9548 | 11.800000190734863 | 355 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 994 | 0.8333333134651184 | 26 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 33982 | 43.16666793823242 | 1296 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 4992 | 6.0 | 181 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 9548 | 11.800000190734863 | 355 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1140 | 6.900000095367432 | 208 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 2600 | 2.933333396911621 | 89 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 11040 | 13.733333587646484 | 413 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 26052 | 33.0 | 991 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 3562 | 4.166666507720947 | 126 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 4852 | 5.800000190734863 | 175 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 3432 | 4.0 | 121 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1300 | 1.2666666507720947 | 39 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 8840 | 10.933333396911621 | 329 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 4186 | 4.9666666984558105 | 150 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1966 | 2.0999999046325684 | 64 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 672 | 3.0 | 91 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1810 | 1.899999976158142 | 58 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 3796 | 4.4666666984558105 | 135 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 8586 | 10.566666603088379 | 318 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 10686 | 13.300000190734863 | 400 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1482 | 1.5 | 46 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 7702 | 9.433333396911621 | 284 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 3932 | 4.599999904632568 | 139 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 942 | 0.7666666507720947 | 24 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 52468 | 66.86666870117188 | 2007 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1456 | 1.4666666984558105 | 45 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 2028 | 2.200000047683716 | 67 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1730 | 2.1666667461395264 | 66 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 524 | 1.7666666507720947 | 54 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 30629 | 38.86666488647461 | 1167 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 27768 | 35.20000076293945 | 1057 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 936 | 0.800000011920929 | 25 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 283482 | 8.133333206176758 | 245 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 209186 | 7.833333492279053 | 236 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 2344948 | 65.4000015258789 | 1963 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 295192 | 8.133333206176758 | 245 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 150260 | 7.866666793823242 | 237 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 182382 | 4.9666666984558105 | 150 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 662718 | 44.93333435058594 | 1349 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 95792 | 2.5333333015441895 | 77 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 2462274 | 66.86666870117188 | 2007 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 136244 | 9.233333587646484 | 278 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 8604 | 1.7666666507720947 | 54 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 69378 | 4.4666666984558105 | 135 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 2344948 | 65.4000015258789 | 1963 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 115524 | 6.699999809265137 | 202 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1296 | 66.86666870117188 | 2007 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 443587 | 49.733333587646484 | 1493 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 605756 | 66.86666870117188 | 2007 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1209 | 1.2666666507720947 | 39 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 8934 | 1.5 | 46 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1002 | 1.5 | 46 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 7859 | 1.5 | 46 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1079 | 1.2666666507720947 | 39 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 6962 | 1.2666666507720947 | 39 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1076 | 1.5 | 46 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1150 | 2.6666667461395264 | 81 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 16919 | 2.6666667461395264 | 81 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 7583 | 1.5 | 46 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 6984 | 1.2666666507720947 | 39 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1081 | 1.5 | 46 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1033 | 3.2666666507720947 | 99 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 20246 | 3.2666666507720947 | 99 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 11352 | 4.566666603088379 | 138 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1229 | 0.30000001192092896 | 10 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 568 | 0.30000001192092896 | 10 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 6742 | 2.700000047683716 | 82 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 2034 | 0.6000000238418579 | 19 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 4142 | 1.0 | 31 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 2908 | 0.699999988079071 | 22 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1633 | 1.7666666507720947 | 54 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 2000 | 3.933333396911621 | 119 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1864 | 0.6000000238418579 | 19 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 24688 | 2.0 | 61 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1270 | 0.03333333507180214 | 2 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 25167 | 2.0 | 61 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 7812 | 2.5999999046325684 | 79 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 281 | 0.03333333507180214 | 2 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 22948 | 2.0 | 61 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 22781 | 2.0 | 61 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 2344 | 3.3333332538604736 | 101 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 344 | 0.6666666865348816 | 21 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 10951 | 1.2000000476837158 | 37 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 3248 | 0.8333333134651184 | 26 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1083 | 0.8333333134651184 | 26 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1115 | 0.8333333134651184 | 26 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1128 | 0.8333333134651184 | 26 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 3883 | 0.9333333373069763 | 29 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 3738 | 2.2666666507720947 | 69 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 3584 | 2.2333333492279053 | 68 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 985 | 0.8333333134651184 | 26 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 2611 | 0.8333333134651184 | 26 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1178 | 0.8333333134651184 | 26 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 2355 | 0.46666666865348816 | 15 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 2440 | 0.46666666865348816 | 15 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 6162 | 4.933333396911621 | 149 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 5302 | 4.400000095367432 | 133 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 1829 | 3.7333333492279053 | 113 |
| Playable_BatmobileJoker_SF | `AnimSequence` | AnimSequence | 3071 | 7.233333110809326 | 218 |
| Playable_BatmobileJoker_SF | `BM_Batmobile_Chassis` | AnimSet | 1194 | — | — |
| Playable_BatmobileJoker_SF | `Camera` | AnimSet | 350 | — | — |
| Playable_BatmobileJoker_SF | `Phase2_JK` | AnimSet | 1238 | — | — |
| Playable_BatmobileJoker_SF | `Phase2_JK_FACE` | AnimSet | 1262 | — | — |
| Playable_BatmobileJoker_SF | `Phase2_TG` | AnimSet | 830 | — | — |
| Playable_BatmobileJoker_SF | `Batmobile_V2_Pose_States` | AnimSet | 1598 | — | — |
| Playable_BatmobileJoker_SF | `Batwing_Rescue` | AnimSet | 278 | — | — |
| Playable_BatmobileJoker_SF | `Batwing_Vehicle_AnimTree` | AnimTree | 112 | 1.0 | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileJoker_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 18 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileMK2_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 24783 | 2.0 | 61 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 17745 | 3.1666667461395264 | 96 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 1010 | 0.5 | 16 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 668 | 0.03333333507180214 | 2 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 994 | 0.4333333373069763 | 14 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 11352 | 4.566666603088379 | 138 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 1229 | 0.30000001192092896 | 10 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 568 | 0.30000001192092896 | 10 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 6742 | 2.700000047683716 | 82 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 2034 | 0.6000000238418579 | 19 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 4142 | 1.0 | 31 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 2908 | 0.699999988079071 | 22 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 1633 | 1.7666666507720947 | 54 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 2000 | 3.933333396911621 | 119 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 1864 | 0.6000000238418579 | 19 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 24688 | 2.0 | 61 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 1270 | 0.03333333507180214 | 2 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 25167 | 2.0 | 61 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 7812 | 2.5999999046325684 | 79 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 281 | 0.03333333507180214 | 2 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 22948 | 2.0 | 61 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 22781 | 2.0 | 61 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 2344 | 3.3333332538604736 | 101 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 344 | 0.6666666865348816 | 21 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 10951 | 1.2000000476837158 | 37 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 3248 | 0.8333333134651184 | 26 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 1083 | 0.8333333134651184 | 26 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 1115 | 0.8333333134651184 | 26 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 1128 | 0.8333333134651184 | 26 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 3883 | 0.9333333373069763 | 29 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 3738 | 2.2666666507720947 | 69 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 3584 | 2.2333333492279053 | 68 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 985 | 0.8333333134651184 | 26 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 2611 | 0.8333333134651184 | 26 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 1178 | 0.8333333134651184 | 26 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 2355 | 0.46666666865348816 | 15 |
| Playable_BatmobileMK2_SF | `AnimSequence` | AnimSequence | 2440 | 0.46666666865348816 | 15 |
| Playable_BatmobileMK2_SF | `BM_Batmobile_Chassis` | AnimSet | 1194 | — | — |
| Playable_BatmobileMK2_SF | `Batmobile_V2_Pose_States` | AnimSet | 1598 | — | — |
| Playable_BatmobileMK2_SF | `Batmobile_Skel_Ctrl_Door` | AnimTree | 202 | 1.0 | — |
| Playable_BatmobileMK2_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileMK2_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_BatmobileMK2_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 18 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 30 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 22 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_Batmobile_SF | `AnimNotify_Sound` | AnimNotify_Sound | 10 | — | — |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 24783 | 2.0 | 61 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 17745 | 3.1666667461395264 | 96 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 1010 | 0.5 | 16 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 668 | 0.03333333507180214 | 2 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 994 | 0.4333333373069763 | 14 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 11352 | 4.566666603088379 | 138 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 1229 | 0.30000001192092896 | 10 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 568 | 0.30000001192092896 | 10 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 6742 | 2.700000047683716 | 82 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 2034 | 0.6000000238418579 | 19 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 4142 | 1.0 | 31 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 2908 | 0.699999988079071 | 22 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 1633 | 1.7666666507720947 | 54 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 2000 | 3.933333396911621 | 119 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 1864 | 0.6000000238418579 | 19 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 24688 | 2.0 | 61 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 1270 | 0.03333333507180214 | 2 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 25167 | 2.0 | 61 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 7812 | 2.5999999046325684 | 79 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 281 | 0.03333333507180214 | 2 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 22948 | 2.0 | 61 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 22781 | 2.0 | 61 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 2344 | 3.3333332538604736 | 101 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 344 | 0.6666666865348816 | 21 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 10951 | 1.2000000476837158 | 37 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 3248 | 0.8333333134651184 | 26 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 1083 | 0.8333333134651184 | 26 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 1115 | 0.8333333134651184 | 26 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 1128 | 0.8333333134651184 | 26 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 3883 | 0.9333333373069763 | 29 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 3738 | 2.2666666507720947 | 69 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 3584 | 2.2333333492279053 | 68 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 985 | 0.8333333134651184 | 26 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 2611 | 0.8333333134651184 | 26 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 1178 | 0.8333333134651184 | 26 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 2355 | 0.46666666865348816 | 15 |
| Playable_Batmobile_SF | `AnimSequence` | AnimSequence | 2440 | 0.46666666865348816 | 15 |
| Playable_Batmobile_SF | `BM_Batmobile_Chassis` | AnimSet | 1194 | — | — |
| Playable_Batmobile_SF | `Batmobile_V2_Pose_States` | AnimSet | 1598 | — | — |
| Playable_Batmobile_SF | `Batmobile_Skel_Ctrl_Door` | AnimTree | 202 | 1.0 | — |
| Playable_Batmobile_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_Batmobile_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |
| Playable_Batmobile_SF | `RAnimNotify_Script` | RAnimNotify_Script | 14 | — | — |

## Weapons and projectiles

| package | object | class | named props | properties | references |
|---|---|---|---|---|---|
| Playable_BatmobileFunhouse_SF | `Batmobile_Heavy_Cannon_Primary_Projectile` | RBasicProjectile | 0 | — | `Batmobile_Heavy_Cannon_Primary_Projectile.Mesh0`; `Batmobile_Heavy_Cannon_Primary_Projectile.RocketTrail`; `Particles.Batmobile_HeavyCannon_Impact`; `Particles.Batmobile_HeavyCannon_Impact`; `Ww_VFX_Tank_Explosion.Play_Batmobile_HeavyCannon_Explosion` |
| Playable_BatmobileFunhouse_SF | `Batmobile_EMPMissile_Projectile` | RBatmobileMissile | 0 | — | `Rocket.Batmobil_Rocket_Explosion`; `Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact`; `Engine.Play_Batmobile_ApRocket_Up`; `Engine.Play_Batmobile_ApRocket_Flight`; `Batmobile_EMPMissile_Projectile.RocketTrail` |
| Playable_BatmobileFunhouse_SF | `Batmobile_Heavy_Cannon_BodyShot_Projectile` | RBasicProjectile | 0 | — | `Batmobile_Heavy_Cannon_BodyShot_Projectile.Mesh0`; `Batmobile_Heavy_Cannon_BodyShot_Projectile.RocketTrail`; `Cannon_Upgrades.Impact_Body_UPGR`; `Cannon_Upgrades.Muzzle_Body_UPGR`; `Batmobile_Heavy_Cannon_BodyShot_Projectile.ImpulseComponent0` |
| Playable_BatmobileFunhouse_SF | `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` | RBasicProjectile | 0 | — | `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.Mesh0`; `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.RocketTrail`; `Cannon_Upgrades.Impact_Full_UPGR`; `Cannon_Upgrades.Muzzle_Full_UPGR`; `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.ImpulseComponent0` |
| Playable_BatmobileFunhouse_SF | `Batmobile_Heavy_Cannon_HeadShot_Projectile` | RBasicProjectile | 0 | — | `Batmobile_Heavy_Cannon_HeadShot_Projectile.Mesh0`; `Batmobile_Heavy_Cannon_HeadShot_Projectile.RocketTrail`; `Cannon_Upgrades.Impact_Head_UPGR`; `Cannon_Upgrades.Muzzle_Head_UPGR`; `Batmobile_Heavy_Cannon_HeadShot_Projectile.ImpulseComponent0` |
| Playable_BatmobileFunhouse_SF | `Drone_Hacker` | RBatmobileAllegianceSwitcher | 1 | `HackerEffect` | `Particles.DroneHacker_Beam`; `Particles.DroneHacker_Success`; `Particles.CobraHacker_Beam`; `Particles.CobraHacker_Success`; `Materials.DroneHacker_Beam_INST` |
| Playable_BatmobileFunhouse_SF | `Batmobile_Booster` | RBatmobileBooster | 0 | — | `Batmobile_Booster.GadgetMesh` |
| Playable_BatmobileFunhouse_SF | `Batmobile_Cannon_V2` | RBatmobileCannon | 6 | `HeatBarStart`, `HeatBarSize`, `RiotSuppressorFireScreenShake`, `ChainGunScreenShake`, `InaccuracyVsTime`, `InaccuracyVs | `Particles.Batmobile_Muzzleflash_NoTracer`; `Riot_Suppressor.Anti_firearm_gel_Miss`; `Particles.Batmobile_RiotSuppressor_Tracer`; `Particles.Batmobile_Muzzleflash_Tracer`; `Particles.ChainGun_BulletCasing` |
| Playable_BatmobileFunhouse_SF | `Batmobile_EMP_Burst` | RBatmobileEMP | 2 | `FireParticle`, `EMPFireSwitch` | `Batmobile_EMP_Burst.ChargeParticle0`; `Batmobile_EMP_Burst.ImpulseComponent0`; `Engine.Play_Batmobile_EMP`; `Engine.Play_Batmobile_EMP`; `Material_MASTERS.Batmobile_V3_Wheel_EMP_MAT_INST` |
| Playable_BatmobileFunhouse_SF | `Batmobile_EMP_Missile_Launcher` | RBatmobileEMPMissile | 1 | `MissileLaunchSockets` | `Projectiles.Batmobile_EMPMissile_Projectile_ForCars`; `Ww_CHR_BatmanAlerts.Play_HUD_fail`; `Conversation.Main_Ch03_S24_Cityx_Pt3_Callcar`; `Projectiles.Batmobile_EMPMissile_Projectile_ForCars`; `Engine.Play_Batmobile_ApRocket_Fire` |
| Playable_BatmobileFunhouse_SF | `Batmobile_Heavy_Cannon_Primary` | RBatmobileHeavyCannon | 3 | `FireScreenShake`, `ChargingScreenShake`, `BonesToHideWhenNotPresent` | `Projectiles.Batmobile_Heavy_Cannon_Primary_Projectile`; `Projectiles.Batmobile_Heavy_Cannon_BodyShot_Projectile`; `Projectiles.Batmobile_Heavy_Cannon_HeadShot_Projectile`; `Projectiles.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile`; `Particles.Batmobile_canonMuzzleflash` |
| Playable_BatmobileFunhouse_SF | `Batmobile_EMPMissile_Projectile_ForCars` | RBatmobileMissile | 0 | — | `Rocket.Batmobil_Rocket_Explosion_Small`; `Batmobile_EMPMissile_Projectile_ForCars.RocketTrail`; `Batmobile_EMPMissile_Projectile_ForCars.Mesh0`; `Batmobile_EMPMissile_Projectile_ForCars.Mesh0`; `Batmobile_EMPMissile_Projectile_ForCars.RocketTrail` |
| Playable_BatmobileFunhouse_SF | `Batmobile_Missile_Projectile` | RBatmobileMissile | 0 | — | `Rocket.Batmobil_Rocket_Explosion`; `Engine.Play_Explosion_3D`; `Ww_VEH_Tank_Missiles.Play_Batmobile_RocketTails`; `Engine.Play_Batmobile_ApRocket_Flight`; `Ww_VEH_Tank_Missiles.Stop_Batmobile_RocketTails` |
| Playable_BatmobileFunhouse_SF | `Batmobile_Tracker_Projectile` | RBatmobileMissile | 0 | — | `Batmobile_Tracker_Projectile.RocketTrail`; `Batmobile_Tracker_Projectile.Mesh0`; `Batmobile_Tracker_Projectile.Mesh0`; `Batmobile_Tracker_Projectile.RocketTrail`; `Batmobile_Tracker_Projectile.ImpulseComponent0` |
| Playable_BatmobileFunhouse_SF | `Batmobile_Missile_Launcher` | RBatmobileMissileLauncher | 0 | — | `Projectiles.Batmobile_Missile_Projectile`; `Rocket.Batmobile_Rocket_Muzzle`; `Engine.Play_RiotSuppressor_Select`; `Ww_Batmobile_Target.Batmobile_Target`; `Ww_Batmobile_Target.Batmobile_Target_Last` |
| Playable_BatmobileFunhouse_SF | `Batmobile_Sonar` | RBatmobileSonar | 2 | `ChargingScreenShake`, `BlastScreenShake` | `Particles.Batmobile_Seismic_Sonar`; `Ww_BML_Sonar.Play_BML_Sonar_Pulse_Search`; `Ww_BML_Sonar.Play_BML_Sonar_Rumble_Lp`; `Ww_BML_Sonar.Stop_BML_Sonar_Rumble_Lp`; `Particles.Batmobile_Seismic_Sonar_Charged` |
| Playable_BatmobileFunhouse_SF | `Vehicle_Tracker` | RBatmobileVehicleTracker | 0 | — | `Projectiles.Batmobile_Tracker_Projectile`; `ww_chr_batmandisruptor.Play_BatSniperRifle_Vehicle_Tracking_Fire`; `ww_chr_batmandisruptor.Play_BatSniperRifle_Vehicle_Tracking_Fire`; `Vehicle_Tracker.GadgetMesh` |
| Playable_BatmobileFunhouse_SF | `Batmobile_Winch` | RBatmobileWinch | 3 | `FireScreenShake`, `BonesToHideWhenNotPresent`, `CollisionFilter` | `Winch.Winch_Muzzle`; `VFX_Batmobile.winch_latched`; `Engine.Play_BML_WinchFire`; `Engine.Play_BML_Winch_Attatch`; `Engine.Play_BML_WinchDetach` |
| Playable_BatmobileJoker_SF | `Batmobile_Cannon_V2` | RBatmobileCannon | 6 | `HeatBarStart`, `HeatBarSize`, `RiotSuppressorFireScreenShake`, `ChainGunScreenShake`, `InaccuracyVsTime`, `InaccuracyVs | `Particles.Batmobile_Muzzleflash_NoTracer`; `Riot_Suppressor.Anti_firearm_gel_Miss`; `Particles.Batmobile_RiotSuppressor_Tracer`; `Particles.Batmobile_Muzzleflash_Tracer`; `Particles.ChainGun_BulletCasing` |
| Playable_BatmobileJoker_SF | `Batmobile_JokerHeavy_Cannon_Projectile` | RBasicProjectile | 0 | — | `Batmobile_JokerHeavy_Cannon_Projectile.Mesh0`; `Batmobile_JokerHeavy_Cannon_Projectile.RocketTrail`; `Engine.Batmobile_rocketExplosion_TEMP`; `Ww_VFX_Tank_Explosion.Play_Batmobile_HeavyCannon_Explosion`; `Batmobile_JokerHeavy_Cannon_Projectile.ImpulseComponent0` |
| Playable_BatmobileJoker_SF | `Batmobile_Booster` | RBatmobileBooster | 0 | — | `Batmobile_Booster.GadgetMesh` |
| Playable_BatmobileJoker_SF | `Batmobile_JokerCannon_V2` | RBatmobileCannon | 0 | — | `Batmobile_JokerCannon_V2.ChainGunShells0`; `Batmobile_JokerCannon_V2.GadgetMesh` |
| Playable_BatmobileJoker_SF | `Batmobile_JokerHeavy_Cannon` | RBatmobileHeavyCannon | 3 | `FireScreenShake`, `ChargingScreenShake`, `BonesToHideWhenNotPresent` | `Projectiles.Batmobile_JokerHeavy_Cannon_Projectile`; `Particles.Batmobile_canonMuzzleflash`; `Engine.Play_BML_HeavyCannon_Fire`; `ww_veh_tank_heavy.Play_Tank_Heavy_LockBeep`; `Ww_Parameters.VEH_Tank_Heavy_LockOn` |
| Playable_BatmobileJoker_SF | `Batmobile_JokerMissile_Projectile` | RBatmobileMissile | 0 | — | `Rocket.Batmobil_Rocket_Explosion`; `Engine.Play_Explosion_3D`; `Engine.Play_Batmobile_ApRocket_Up`; `Engine.Play_Batmobile_ApRocket_Flight`; `Batmobile_JokerMissile_Projectile.RocketTrail` |
| Playable_BatmobileMK2_SF | `Batmobile_Heavy_Cannon_Primary_Projectile` | RBasicProjectile | 0 | — | `Batmobile_Heavy_Cannon_Primary_Projectile.Mesh0`; `Batmobile_Heavy_Cannon_Primary_Projectile.RocketTrail`; `Particles.Batmobile_HeavyCannon_Impact`; `Particles.Batmobile_HeavyCannon_Impact`; `Ww_VFX_Tank_Explosion.Play_Batmobile_HeavyCannon_Explosion` |
| Playable_BatmobileMK2_SF | `Batmobile_EMPMissile_Projectile` | RBatmobileMissile | 0 | — | `Rocket.Batmobil_Rocket_Explosion`; `Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact`; `Engine.Play_Batmobile_ApRocket_Up`; `Engine.Play_Batmobile_ApRocket_Flight`; `Batmobile_EMPMissile_Projectile.RocketTrail` |
| Playable_BatmobileMK2_SF | `Batmobile_Heavy_Cannon_BodyShot_Projectile` | RBasicProjectile | 0 | — | `Batmobile_Heavy_Cannon_BodyShot_Projectile.Mesh0`; `Batmobile_Heavy_Cannon_BodyShot_Projectile.RocketTrail`; `Cannon_Upgrades.Impact_Body_UPGR`; `Cannon_Upgrades.Muzzle_Body_UPGR`; `Batmobile_Heavy_Cannon_BodyShot_Projectile.ImpulseComponent0` |
| Playable_BatmobileMK2_SF | `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` | RBasicProjectile | 0 | — | `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.Mesh0`; `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.RocketTrail`; `Cannon_Upgrades.Impact_Full_UPGR`; `Cannon_Upgrades.Muzzle_Full_UPGR`; `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.ImpulseComponent0` |
| Playable_BatmobileMK2_SF | `Batmobile_Heavy_Cannon_HeadShot_Projectile` | RBasicProjectile | 0 | — | `Batmobile_Heavy_Cannon_HeadShot_Projectile.Mesh0`; `Batmobile_Heavy_Cannon_HeadShot_Projectile.RocketTrail`; `Cannon_Upgrades.Impact_Head_UPGR`; `Cannon_Upgrades.Muzzle_Head_UPGR`; `Batmobile_Heavy_Cannon_HeadShot_Projectile.ImpulseComponent0` |
| Playable_BatmobileMK2_SF | `Drone_Hacker` | RBatmobileAllegianceSwitcher | 1 | `HackerEffect` | `Particles.DroneHacker_Beam`; `Particles.DroneHacker_Success`; `Particles.CobraHacker_Beam`; `Particles.CobraHacker_Success`; `Materials.DroneHacker_Beam_INST` |
| Playable_BatmobileMK2_SF | `Batmobile_Booster` | RBatmobileBooster | 0 | — | `Batmobile_Booster.GadgetMesh` |
| Playable_BatmobileMK2_SF | `Batmobile_Cannon_V2` | RBatmobileCannon | 6 | `HeatBarStart`, `HeatBarSize`, `RiotSuppressorFireScreenShake`, `ChainGunScreenShake`, `InaccuracyVsTime`, `InaccuracyVs | `Particles.Batmobile_Muzzleflash_NoTracer`; `Riot_Suppressor.Anti_firearm_gel_Miss`; `Particles.Batmobile_RiotSuppressor_Tracer`; `Particles.Batmobile_Muzzleflash_Tracer`; `Particles.ChainGun_BulletCasing` |
| Playable_BatmobileMK2_SF | `Batmobile_EMP_Burst` | RBatmobileEMP | 2 | `FireParticle`, `EMPFireSwitch` | `Batmobile_EMP_Burst.ChargeParticle0`; `Batmobile_EMP_Burst.ImpulseComponent0`; `Engine.Play_Batmobile_EMP`; `Engine.Play_Batmobile_EMP`; `Material_MASTERS.Batmobile_V3_Wheel_EMP_MAT_INST` |
| Playable_BatmobileMK2_SF | `Batmobile_EMP_Missile_Launcher` | RBatmobileEMPMissile | 1 | `MissileLaunchSockets` | `Projectiles.Batmobile_EMPMissile_Projectile_ForCars`; `Ww_CHR_BatmanAlerts.Play_HUD_fail`; `Conversation.Main_Ch03_S24_Cityx_Pt3_Callcar`; `Projectiles.Batmobile_EMPMissile_Projectile_ForCars`; `Engine.Play_Batmobile_ApRocket_Fire` |
| Playable_BatmobileMK2_SF | `Batmobile_Heavy_Cannon_Primary` | RBatmobileHeavyCannon | 3 | `FireScreenShake`, `ChargingScreenShake`, `BonesToHideWhenNotPresent` | `Projectiles.Batmobile_Heavy_Cannon_Primary_Projectile`; `Projectiles.Batmobile_Heavy_Cannon_BodyShot_Projectile`; `Projectiles.Batmobile_Heavy_Cannon_HeadShot_Projectile`; `Projectiles.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile`; `Particles.Batmobile_canonMuzzleflash` |
| Playable_BatmobileMK2_SF | `Batmobile_EMPMissile_Projectile_ForCars` | RBatmobileMissile | 0 | — | `Rocket.Batmobil_Rocket_Explosion_Small`; `Batmobile_EMPMissile_Projectile_ForCars.RocketTrail`; `Batmobile_EMPMissile_Projectile_ForCars.Mesh0`; `Batmobile_EMPMissile_Projectile_ForCars.Mesh0`; `Batmobile_EMPMissile_Projectile_ForCars.RocketTrail` |
| Playable_BatmobileMK2_SF | `Batmobile_Missile_Projectile` | RBatmobileMissile | 0 | — | `Rocket.Batmobil_Rocket_Explosion`; `Engine.Play_Explosion_3D`; `Ww_VEH_Tank_Missiles.Play_Batmobile_RocketTails`; `Engine.Play_Batmobile_ApRocket_Flight`; `Ww_VEH_Tank_Missiles.Stop_Batmobile_RocketTails` |
| Playable_BatmobileMK2_SF | `Batmobile_Tracker_Projectile` | RBatmobileMissile | 0 | — | `Batmobile_Tracker_Projectile.RocketTrail`; `Batmobile_Tracker_Projectile.Mesh0`; `Batmobile_Tracker_Projectile.Mesh0`; `Batmobile_Tracker_Projectile.RocketTrail`; `Batmobile_Tracker_Projectile.ImpulseComponent0` |
| Playable_BatmobileMK2_SF | `Batmobile_Missile_Launcher` | RBatmobileMissileLauncher | 0 | — | `Projectiles.Batmobile_Missile_Projectile`; `Rocket.Batmobile_Rocket_Muzzle`; `Engine.Play_RiotSuppressor_Select`; `Ww_Batmobile_Target.Batmobile_Target`; `Ww_Batmobile_Target.Batmobile_Target_Last` |
| Playable_BatmobileMK2_SF | `Batmobile_Sonar` | RBatmobileSonar | 2 | `ChargingScreenShake`, `BlastScreenShake` | `Particles.Batmobile_Seismic_Sonar`; `Ww_BML_Sonar.Play_BML_Sonar_Pulse_Search`; `Ww_BML_Sonar.Play_BML_Sonar_Rumble_Lp`; `Ww_BML_Sonar.Stop_BML_Sonar_Rumble_Lp`; `Particles.Batmobile_Seismic_Sonar_Charged` |
| Playable_BatmobileMK2_SF | `Vehicle_Tracker` | RBatmobileVehicleTracker | 0 | — | `Projectiles.Batmobile_Tracker_Projectile`; `ww_chr_batmandisruptor.Play_BatSniperRifle_Vehicle_Tracking_Fire`; `ww_chr_batmandisruptor.Play_BatSniperRifle_Vehicle_Tracking_Fire`; `Vehicle_Tracker.GadgetMesh` |
| Playable_BatmobileMK2_SF | `Batmobile_Winch` | RBatmobileWinch | 3 | `FireScreenShake`, `BonesToHideWhenNotPresent`, `CollisionFilter` | `Winch.Winch_Muzzle`; `VFX_Batmobile.winch_latched`; `Engine.Play_BML_WinchFire`; `Engine.Play_BML_Winch_Attatch`; `Engine.Play_BML_WinchDetach` |
| Playable_Batmobile_SF | `Batmobile_Heavy_Cannon_Primary_Projectile` | RBasicProjectile | 0 | — | `Batmobile_Heavy_Cannon_Primary_Projectile.Mesh0`; `Batmobile_Heavy_Cannon_Primary_Projectile.RocketTrail`; `Particles.Batmobile_HeavyCannon_Impact`; `Particles.Batmobile_HeavyCannon_Impact`; `Ww_VFX_Tank_Explosion.Play_Batmobile_HeavyCannon_Explosion` |
| Playable_Batmobile_SF | `Batmobile_EMPMissile_Projectile` | RBatmobileMissile | 0 | — | `Rocket.Batmobil_Rocket_Explosion`; `Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact`; `Engine.Play_Batmobile_ApRocket_Up`; `Engine.Play_Batmobile_ApRocket_Flight`; `Batmobile_EMPMissile_Projectile.RocketTrail` |
| Playable_Batmobile_SF | `Batmobile_Heavy_Cannon_BodyShot_Projectile` | RBasicProjectile | 0 | — | `Batmobile_Heavy_Cannon_BodyShot_Projectile.Mesh0`; `Batmobile_Heavy_Cannon_BodyShot_Projectile.RocketTrail`; `Cannon_Upgrades.Impact_Body_UPGR`; `Cannon_Upgrades.Muzzle_Body_UPGR`; `Batmobile_Heavy_Cannon_BodyShot_Projectile.ImpulseComponent0` |
| Playable_Batmobile_SF | `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` | RBasicProjectile | 0 | — | `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.Mesh0`; `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.RocketTrail`; `Cannon_Upgrades.Impact_Full_UPGR`; `Cannon_Upgrades.Muzzle_Full_UPGR`; `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.ImpulseComponent0` |
| Playable_Batmobile_SF | `Batmobile_Heavy_Cannon_HeadShot_Projectile` | RBasicProjectile | 0 | — | `Batmobile_Heavy_Cannon_HeadShot_Projectile.Mesh0`; `Batmobile_Heavy_Cannon_HeadShot_Projectile.RocketTrail`; `Cannon_Upgrades.Impact_Head_UPGR`; `Cannon_Upgrades.Muzzle_Head_UPGR`; `Batmobile_Heavy_Cannon_HeadShot_Projectile.ImpulseComponent0` |
| Playable_Batmobile_SF | `Drone_Hacker` | RBatmobileAllegianceSwitcher | 1 | `HackerEffect` | `Particles.DroneHacker_Beam`; `Particles.DroneHacker_Success`; `Particles.CobraHacker_Beam`; `Particles.CobraHacker_Success`; `Materials.DroneHacker_Beam_INST` |
| Playable_Batmobile_SF | `Batmobile_Booster` | RBatmobileBooster | 0 | — | `Batmobile_Booster.GadgetMesh` |
| Playable_Batmobile_SF | `Batmobile_Cannon_V2` | RBatmobileCannon | 6 | `HeatBarStart`, `HeatBarSize`, `RiotSuppressorFireScreenShake`, `ChainGunScreenShake`, `InaccuracyVsTime`, `InaccuracyVs | `Particles.Batmobile_Muzzleflash_NoTracer`; `Riot_Suppressor.Anti_firearm_gel_Miss`; `Particles.Batmobile_RiotSuppressor_Tracer`; `Particles.Batmobile_Muzzleflash_Tracer`; `Particles.ChainGun_BulletCasing` |
| Playable_Batmobile_SF | `Batmobile_EMP_Burst` | RBatmobileEMP | 2 | `FireParticle`, `EMPFireSwitch` | `Batmobile_EMP_Burst.ChargeParticle0`; `Batmobile_EMP_Burst.ImpulseComponent0`; `Engine.Play_Batmobile_EMP`; `Engine.Play_Batmobile_EMP`; `Material_MASTERS.Batmobile_V3_Wheel_EMP_MAT_INST` |
| Playable_Batmobile_SF | `Batmobile_EMP_Missile_Launcher` | RBatmobileEMPMissile | 1 | `MissileLaunchSockets` | `Projectiles.Batmobile_EMPMissile_Projectile_ForCars`; `Ww_CHR_BatmanAlerts.Play_HUD_fail`; `Conversation.Main_Ch03_S24_Cityx_Pt3_Callcar`; `Projectiles.Batmobile_EMPMissile_Projectile_ForCars`; `Engine.Play_Batmobile_ApRocket_Fire` |
| Playable_Batmobile_SF | `Batmobile_Heavy_Cannon_Primary` | RBatmobileHeavyCannon | 3 | `FireScreenShake`, `ChargingScreenShake`, `BonesToHideWhenNotPresent` | `Projectiles.Batmobile_Heavy_Cannon_Primary_Projectile`; `Projectiles.Batmobile_Heavy_Cannon_BodyShot_Projectile`; `Projectiles.Batmobile_Heavy_Cannon_HeadShot_Projectile`; `Projectiles.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile`; `Particles.Batmobile_canonMuzzleflash` |
| Playable_Batmobile_SF | `Batmobile_EMPMissile_Projectile_ForCars` | RBatmobileMissile | 0 | — | `Rocket.Batmobil_Rocket_Explosion_Small`; `Batmobile_EMPMissile_Projectile_ForCars.RocketTrail`; `Batmobile_EMPMissile_Projectile_ForCars.Mesh0`; `Batmobile_EMPMissile_Projectile_ForCars.Mesh0`; `Batmobile_EMPMissile_Projectile_ForCars.RocketTrail` |
| Playable_Batmobile_SF | `Batmobile_Missile_Projectile` | RBatmobileMissile | 0 | — | `Rocket.Batmobil_Rocket_Explosion`; `Engine.Play_Explosion_3D`; `Ww_VEH_Tank_Missiles.Play_Batmobile_RocketTails`; `Engine.Play_Batmobile_ApRocket_Flight`; `Ww_VEH_Tank_Missiles.Stop_Batmobile_RocketTails` |
| Playable_Batmobile_SF | `Batmobile_Tracker_Projectile` | RBatmobileMissile | 0 | — | `Batmobile_Tracker_Projectile.RocketTrail`; `Batmobile_Tracker_Projectile.Mesh0`; `Batmobile_Tracker_Projectile.Mesh0`; `Batmobile_Tracker_Projectile.RocketTrail`; `Batmobile_Tracker_Projectile.ImpulseComponent0` |
| Playable_Batmobile_SF | `Batmobile_Missile_Launcher` | RBatmobileMissileLauncher | 0 | — | `Projectiles.Batmobile_Missile_Projectile`; `Rocket.Batmobile_Rocket_Muzzle`; `Engine.Play_RiotSuppressor_Select`; `Ww_Batmobile_Target.Batmobile_Target`; `Ww_Batmobile_Target.Batmobile_Target_Last` |
| Playable_Batmobile_SF | `Batmobile_Sonar` | RBatmobileSonar | 2 | `ChargingScreenShake`, `BlastScreenShake` | `Particles.Batmobile_Seismic_Sonar`; `Ww_BML_Sonar.Play_BML_Sonar_Pulse_Search`; `Ww_BML_Sonar.Play_BML_Sonar_Rumble_Lp`; `Ww_BML_Sonar.Stop_BML_Sonar_Rumble_Lp`; `Particles.Batmobile_Seismic_Sonar_Charged` |
| Playable_Batmobile_SF | `Vehicle_Tracker` | RBatmobileVehicleTracker | 0 | — | `Projectiles.Batmobile_Tracker_Projectile`; `ww_chr_batmandisruptor.Play_BatSniperRifle_Vehicle_Tracking_Fire`; `ww_chr_batmandisruptor.Play_BatSniperRifle_Vehicle_Tracking_Fire`; `Vehicle_Tracker.GadgetMesh` |
| Playable_Batmobile_SF | `Batmobile_Winch` | RBatmobileWinch | 3 | `FireScreenShake`, `BonesToHideWhenNotPresent`, `CollisionFilter` | `Winch.Winch_Muzzle`; `VFX_Batmobile.winch_latched`; `Engine.Play_BML_WinchFire`; `Engine.Play_BML_Winch_Attatch`; `Engine.Play_BML_WinchDetach` |