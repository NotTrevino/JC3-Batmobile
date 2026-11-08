# Batmobile skins and variants (G1-20)

A "variant" here is one of the four **full vehicle packages** in the grab, each of which ships its
own mesh, materials, sockets, weapons and `RVehicleBatmobile`. Everything below is read from
`objects.jsonl` (the machine source) joined with `MESHES.md` (LOD counts), `MATERIALS.md` (graphs)
and `MECHANICS.md` (named per-package properties). The reference is always
`Playable_Batmobile_SF` / `Batmobile_V2`.

| variant | package | vehicle object | records | archetype |
|---|---|---|---|---|
| **V2** (reference) | `Playable_Batmobile_SF` | `Batmobile` (3,905 B) | 5,490 | `Batmobile_Archetypes.Vehicle` |
| **MK2** | `Playable_BatmobileMK2_SF` | `Batmobile_MK2` (3,905 B) | 5,534 | `Batmobile_Mk2_Archetypes.Vehicle` |
| **Joker** | `Playable_BatmobileJoker_SF` | `JokersBatmobile` (2,239 B) | 3,388 | `Batmobile_Joker_Archetypes.Vehicle` (+ `Batwing_Archetypes.Vehicle`) |
| **Funhouse** | `Playable_BatmobileFunhouse_SF` | `BatmobileFunhouse` (3,905 B) | 5,584 | `Batmobile_Funhouse_Archetypes.Vehicle` |

Eleven `_Std_*` packages accompany them (4 records each: `ObjectReferencer`, two `Package`, and
`RAddContentBatmobileMesh`) except `Playable_Batmobile_Std_6_SF`, which carries 92 records including
a `Batmobile_Stage6` material — the upgrade-stage material, not a vehicle.

## 1. Mesh

| variant | mesh | verts | LOD0 / LOD1 / LOD2 faces | bones | materials | size (cm) | export (B) |
|---|---|---|---|---|---|---|---|
| V2 | `Batmobile_V2` | 201,338 | **299,837** / 144,857 / 21,720 | 180 | 19 | 702.560 × 349.530 × 234.185 | 20,151,210 |
| MK2 | `Batmobile_MK2_Skin` | 199,628 | **297,566** (−0.76%) / 115,056 / 21,242 | 175 | 19 | 702.539 × 349.487 × 234.185 | 20,034,142 |
| Joker | `Batmobile_Jokerfied_Skin` | 202,795 | **305,786** (+1.98%) / 117,897 / 21,407 | **220** | **20** | 713.804 × 349.156 × 233.900 | 20,385,512 |
| Funhouse | `Batmobile_Jokerfied_Skin` | 202,795 | **305,786** | 220 | 20 | 713.804 × 349.156 × 233.900 | 20,385,512 |

The Joker and Funhouse skin meshes are **the same export** (20,385,512 B each); what differs
between those two packages is what surrounds the mesh (materials, sockets, weapons — below).

Shared side-meshes:

| mesh | LOD0 / LOD1 | bones | materials | export (B) | in |
|---|---|---|---|---|---|
| `Batmobile_V3_Destroyed` | 36,513 / 16,225 | 32 | 1 | 3,637,836 | all four packages (identical size) |
| `Batmobile_V2_Fire` | 1,196 / 523 | 179 | 1 | 100,628 | V2, MK2, Funhouse — **not Joker** |
| `Batwing_Carrier` | 14,508 / 2,707 | 25 | 3 | 836,016 | **Joker only**, with `RBatwing Batwing_Rescue_Batmobile` |

## 2. Sockets

| variant | sockets | only in this variant | missing vs V2 |
|---|---|---|---|
| V2 | **65** | — | — |
| MK2 | **55** | — | `BrakeTrailL`, `BrakeTrailR`, `Dashboard_Light`, `Headlight_Centre`, `LWheelLight`, `LWheelLight_bottom`, `LWheelLight_top`, `RWheelLight`, `RWheelLight_bottom`, `RWheelLight_top` |
| Joker | **64** | `BatmobileAttach`, `HydraSocket` | `Dashboard_Light`, `Headlight_Centre`, `PassengerNoiseOrigin` |
| Funhouse | **63** | `HydraSocket` | `Dashboard_Light`, `Headlight_Centre`, `PassengerNoiseOrigin` |

The MK2 drops the whole wheel-light family and the centre headlight anchor (10 sockets); Joker and
Funhouse drop the interior/dashboard anchors and add the Joker-content ones.

## 3. Materials (`Material` + `MaterialInstanceConstant`)

| variant | count | extra vs V2 | missing vs V2 |
|---|---|---|---|
| V2 | **78** | — | — |
| MK2 | **80** | `Batmobile_MK2_Body_MIC`, `Batmobile_MK2_WheelArch_MAT`, `Batmobile_MK2_WheelArchs_MIC_INST`, `Batmobile_MK2_Wheel_INST` | `BatmobileV3_Wheel_V2_MIC`, `Batmobile_V3_Mainbody_NEW_MIC` |
| Joker | **69** | 26: the Jokerfied set (`Batmobile_Jokerfied_V2_MAT`, `_MainBody`, `_WheelArch_MIC`, `_Hair_MAT` + `_MIC`, `_Gloves`, `_Shoes`, `_Teeth`, `Batmobile_V3_Turret_Jokerfied_MIC`), `Batwing_Carrier_MAT` + `_INST`, `Hydra_Trails_M` + `_INST`, `Helicopter_Police_Rotor_S_MAT`, `Game_Cameo_Squirting_FLOWER_MAT`, `Dusty_hit_01_4x4`, `Falling_Dust_MAT` + `_INST`, `Smoke_02_SubUV_16_unlit`, `contrail_m`, `Simple_GlowFade`, `LensFlare_OWStreetLightReflection_SOFT_INST`, `Engine_Distortion`, `Batmobile_V3_Tyre_test_INST`, `wheel_V2_test_INST` | 38: the V2 FX/material set (both EMP burst stages, `Batmobile_Seismic_Sonar`, `SeismicScan_Distortion`, `SeismicSonar_Smoke`, `DroneHacker_Beam` + `_INST`, `Drone_Bomb_Radius`, `Batmobile_Fire_Main` + `_INST`, `Burnout_Mat_MUD_NV`, `Batmobile_V3_Wheel_EMP_MAT_INST`, `fx_Winch_M_lit` + `_INST`, `Nimbus_Power_Cell_Mat`, `Stagg_Battery_01/02`, `Batmobile_Worn_NoRain`, `Batmobile_V3_Mainbody_NEW_MIC`, `Batmobile_V3_Turret_NEW_MIC`, `Batmobile_V3_Tyre_V2_MIC`, `GPU_Spark_ConstantSize`, `MAT_BitsOfShockwave` + `_INST`, `MAT_Digital_Noise`, `INST_Digital_Noise_*`, `INST_New_Electric_Arc_BLUE_THIN`, `MAT_Flat_Shockwave_INST_BLUE`, `MAT_Mud_Splash_1x1_V02_INST`, `Vehicle_Smoke_01`, `Smoke_Dissolve`, `INST_Digital_Noise_V02`) |
| Funhouse | **84** | 13 (the Jokerfied set minus `Game_Cameo_Squirting_FLOWER_MAT`, plus nothing else new beyond it) | 7: `Batmobile_V3_Mainbody_NEW_MIC`, `Batmobile_V3_Turret_NEW_MIC`, `Batmobile_V3_Tyre_V2_MIC`, `Batmobile_Worn_NoRain`, `Nimbus_Power_Cell_Mat`, `Stagg_Battery_01_MAT`, `Stagg_Battery_Energy_01_MAT` |

## 4. Textures (`Texture2D`)

| variant | count | extra vs V2 | missing vs V2 |
|---|---|---|---|
| V2 | **92** | — | — |
| MK2 | **95** | `Batmobile_MK2_Body2_D`, `_Body2_R`, `_WheelArch2_D`, `_WheelArch2_R`, `_Wheel_MK2_D` | `Batmobile_V3_Power_Cell_D`, `Z_WIP` |
| Joker | **100** | 32: the Jokerfied body/wheel/tyre set (`Batmobile_Jokerfied_Body_D`, `_Body_Damage_ChapterMask`, `_WheelArch_D`, `_jokerfied_WheelArch_Damage_ChapterMask`, `_Wheel_V2_D`, `_Tyre_V2_D`, `_GlovesAndBoots_D/_N/_R`, `_Hair_D/_N/_R`), the Joker character maps (`Joker_BM3_Trousers_D/_N/_R`, `Joker_BM3_V2_Head_Hair_R`, `Joker_BM3_V2_Teeth2_D/_N/_R`), `Batmobile_V3_Weaponry_Turret_V2_D`, `Batwing_Carrier_D/_E/_N`, `Game_Cameo_Squirting_FLOWER_D/_N`, `Hydra`/`contrails`/`TXT_Helicopter_Police_Blades`, `Core_Mask2`, `gradientNoWrap`, `Batmobile_MK2_Body2_R`, `Batmobile_MK2_WheelArch2_R` | 24: the V2 power-cell/battery/noise set (`Batmobile_V3_Power_Cell_D/_INT_D`, `Nimbus_Power_Cell_N/_S`, `Stagg_Battery_01_D/_GLOW/_N`, `Batmobile_V3_TEXTURES_Body_Damage_ChapterMask`, `Batmobile_V3_Winch_EMP_D`, `Generator_Flakes`, `Generator_Storm_Cloud`, `Lightning_Timing`, `Glass_Dust`, `GridLines_split`, `HorizontalFade`, `Low_Noise`, `Loop3`, `V_Gradient`, `Square_Rounded_Mask`, `AceBridgeStatue_Detail`, `line1`, `linearMask_centre`, `Z_WIP`) |
| Funhouse | **102** | 26 (the Jokerfied set, same as Joker minus the Batwing/Hydra/cameo extras) | 14 |

## 5. Simulation — identical in all four

`RVehicleSimBatmobile` `SimulationModel` (2,328 B, 37 tags) is the **same object** in every package:
a tag-by-tag comparison of the four instances finds **0 differing tags**. Every variant therefore
carries the same physics: the same wheels, mass, torque curves and suspension (the values in
`MECHANICS.md` → SimulationModel). Nothing about handling distinguishes a skin.

## 6. Vehicle object (`RVehicleBatmobile`)

| variant | B | decoded properties | light rig entries |
|---|---|---|---|
| V2 | 3,905 | 13 | **28** (bones, Types and `MaterialType` bindings) |
| MK2 | 3,905 | 13 — **identical to V2** | **28** — identical rows to V2 |
| Funhouse | 3,905 | 13 — identical to V2 | **28** — identical rows to V2 |
| Joker | 2,239 | 11 — see below | **17** — and every `MaterialType` is `—` |

Joker's property diff vs V2:

| property | V2 | Joker |
|---|---|---|
| `InteriorLightsSwitchedOn` (ByteProperty, 0x86D) | `1` | **absent** |
| `WeaponGeneratorMeshPackage` (ArrayProperty, 0x1FF8) | 3 items | **absent** |
| `WeaponGeneratorMesh` (ArrayProperty, 0x2008) | 3 items `[0, 0, 0]` | **absent** |
| `UpgradedGeneratorBonus` (ArrayProperty, 0x21A0) | — | **2 items `[1.0, 1.0]`** |

Joker's light rig also lacks `BootLight`, `Dashboard_Light` (`VEHLT_Interior`), the second
`BrakeLightL/R` material bindings and the `VEHLTMAT_*` material types entirely (25 of V2's 28 rows
bind a `MaterialType`; 0 of Joker's 17 do).

Unnamed scalars: MK2 and Funhouse each differ from V2 at a handful of offsets that are **not** among
the 13 decoded properties — MK2: 0x384 276→275, 0x828 157→156, 0x12BC 147→146, 0x12DC 62→60,
0x12E4 47→45, 0x153C 115→104, 0x163C 278→277, 0x1644 277→276; Funhouse: the same fields
(276→272, 157→155, 147→145, 62→60, 47→45, 115→103, 278→274, 277→273) plus 0x2158 −105→−56.
They are small integers consistent with per-variant component/socket counts; no decoded property and
no sim value moves.

## 7. Weapons and projectiles

| variant | gadgets | projectiles |
|---|---|---|
| V2 | **10** — `Batmobile_Booster`, `Batmobile_Cannon_V2`, `Batmobile_EMP_Burst`, `Batmobile_EMP_Missile_Launcher`, `Batmobile_Heavy_Cannon_Primary`, `Batmobile_Missile_Launcher`, `Batmobile_Sonar`, `Batmobile_Winch`, `Drone_Hacker`, `Vehicle_Tracker` | 4 — EMP missile (×2 variants), missile, tracker |
| MK2 | **10** — identical names to V2 | 4 — identical |
| Funhouse | **10** — identical | 4 — identical |
| Joker | **6** — shared `Batmobile_Booster`, `Batmobile_Cannon_V2` + Joker-only `Batmobile_JokerCannon_V2`, `Batmobile_JokerHeavy_Cannon`, `Batmobile_JokerMissile_Launcher` (+ its `Default__`), and `RVehicleThreatComponent ThreatComp` | **1** — `Batmobile_JokerMissile_Projectile` |

`WEAPONS.md` (G1-08) already compared the shared objects: **0 of 332 fields differ** across the 18
multi-variant objects — the Joker package's distinct objects are its own, not retuned copies. So a
variant changes *which* weapons exist, never their values.

## 8. What this means for decision D-5

The data, without deciding anything:

1. **A skin is not a palette here.** Each variant is a complete mesh with its own materials,
   textures, sockets and (for Joker) its own weapon set and light rig. MK2 swaps 2 materials for 4
   and 5 textures; Jokerfied adds 32 textures, 26 materials and 40 bones. A tint of `Batmobile_V2`
   would carry none of that geometry, none of the `*_Damage_ChapterMask` decals and none of the
   Joker content.
2. **BmAK's own answer is a separate vehicle per skin**: four packages, four `RVehicleBatmobile`
   objects, four archetypes. The Joker/Funhouse pair shows the split is *vehicle-level*: identical
   mesh bytes, different surrounding package.
3. **Physics is shared**, so variants cost nothing in handling (§5) — a drop entry per skin needs
   no new sim tuning, only mesh, materials and the vehicle object's property set.
4. **The Joker variant is a different car in gameplay terms**: 6 gadgets instead of 10 (no EMP, no
   sonar, no tracker, no winch, no drone hacker), a 17-entry light rig with no material bindings,
   no interior-lights flag, and a threat component — not a cosmetic twin.
