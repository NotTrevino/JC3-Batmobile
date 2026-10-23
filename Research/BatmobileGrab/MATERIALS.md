# Batmobile — materials

Slot values come from the decoded `Material` tag stream; instance rows from `MaterialInstanceConstant` parameter arrays.

## Master materials

| package | material | expression slots |
|---|---|---|
| Playable_BatmobileFunhouse_SF | Batmobile_Body_MASTER | DiffuseColor→`Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` [`NEW_Batmobile_V2_BODY_D`]; SpecularColor→`Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter`; SpecularPower→`Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` [`NEW_Batmobile_V2_BODY_S`]; Normal→`Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` [`NEW_Batmobile_V2_BODY_N`]; EmissiveColor→`Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` |
| Playable_BatmobileFunhouse_SF | Batmobile_Glass | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→—; Opacity→—; OpacityMask→—; MetalMask→— |
| Playable_BatmobileFunhouse_SF | Batmobile_Jokerfied_Gloves | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→— |
| Playable_BatmobileFunhouse_SF | Batmobile_Jokerfied_Hair | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→— |
| Playable_BatmobileFunhouse_SF | Batmobile_Jokerfied_Shoes | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→— |
| Playable_BatmobileFunhouse_SF | Batmobile_Jokerfied_Teeth | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→— |
| Playable_BatmobileFunhouse_SF | Batmobile_Jokerfied_Hair_MAT | DiffuseColor→`Batmobile_Jokerfied_Hair_MAT.MaterialExpressionStaticSwitchParameter`; SpecularColor→—; SpecularPower→—; Normal→`Batmobile_Jokerfied_Hair_MAT.MaterialExpressionTextureSampleParameter2D` [`neutral_normal`, `fx_waterCaustic1`]; EmissiveColor→—; Opacity→—; OpacityMask→—; Distortion→—; AnisotropicDirection→`Batmobile_Jokerfied_Hair_MAT.MaterialExpressionVectorParameter`; SSSColor→—; MetalMask→`Batmobile_Jokerfied_Hair_MAT.MaterialExpressionScalarParameter`; TwoSidedLightingMask→—; WorldPositionOffset→— |
| Playable_BatmobileFunhouse_SF | Batmobile_Jokerfied_V2_MAT | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→—; MetalMask→—; WorldPositionOffset→`Batmobile_Jokerfied_V2_MAT.MaterialExpressionStaticSwitchParameter` |
| Playable_BatmobileFunhouse_SF | Batmobile_V3_TEXTURES_Body_Decals | DiffuseColor→—; OpacityMask→— |
| Playable_BatmobileFunhouse_SF | Batmobile_V3_Undercarriage | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; OpacityMask→—; MetalMask→— |
| Playable_BatmobileFunhouse_SF | Cockpit_Master_Flip_Data | DiffuseColor→—; SpecularColor→—; SpecularPower→—; EmissiveColor→— |
| Playable_BatmobileFunhouse_SF | Batmobile_V3_Body_NoRain_MAT | DiffuseColor→—; SpecularColor→`Batmobile_V3_Body_NoRain_MAT.MaterialExpressionStaticSwitchParameter`; SpecularPower→—; Normal→—; EmissiveColor→`Batmobile_V3_Body_NoRain_MAT.MaterialExpressionStaticSwitchParameter`; MetalMask→`Batmobile_V3_Body_NoRain_MAT.MaterialExpressionScalarParameter` |
| Playable_BatmobileFunhouse_SF | Batmobile_V3_Discbreak | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→`Batmobile_V3_Discbreak.MaterialExpressionStaticSwitchParameter`; OpacityMask→—; MetalMask→`Batmobile_V3_Discbreak.MaterialExpressionScalarParameter` |
| Playable_BatmobileFunhouse_SF | Batmobile_V3_Tyre_V2_MAT | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→—; MetalMask→— |
| Playable_BatmobileFunhouse_SF | Batmobile_V3_Wheel_V2_MAT | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; MetalMask→— |
| Playable_BatmobileFunhouse_SF | Batmobile_Worn | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→`Batmobile_Worn.MaterialExpressionStaticSwitchParameter`; MetalMask→—; WorldPositionOffset→`Batmobile_Worn.MaterialExpressionStaticSwitchParameter` |
| Playable_BatmobileFunhouse_SF | BatmobileV3_Rubber_Bullet | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; MetalMask→— |
| Playable_BatmobileFunhouse_SF | Back_Explosion_PP | EmissiveColor→—; Opacity→— |
| Playable_BatmobileFunhouse_SF | Game_Cameo_Squirting_FLOWER_MAT | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→— |
| Playable_BatmobileFunhouse_SF | Batmobile_Takedown_Beam_M | DiffuseColor→—; Normal→—; EmissiveColor→—; Opacity→—; WorldPositionOffset→— |
| Playable_BatmobileFunhouse_SF | Burnout_Mat_MUD_NV | DiffuseColor→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileFunhouse_SF | Drone_Bomb_Radius | EmissiveColor→—; Opacity→— |
| Playable_BatmobileFunhouse_SF | Batmobile_Fire_Main | EmissiveColor→—; Opacity→—; Distortion→—; WorldPositionOffset→— |
| Playable_BatmobileFunhouse_SF | Batmobile_Seismic_Sonar | EmissiveColor→—; Opacity→—; Distortion→— |
| Playable_BatmobileFunhouse_SF | DroneHacker_Beam | EmissiveColor→—; Opacity→— |
| Playable_BatmobileFunhouse_SF | Missile_Line_2_Mat | EmissiveColor→—; Opacity→— |
| Playable_BatmobileFunhouse_SF | Missile_Line_Mat | EmissiveColor→—; Opacity→— |
| Playable_BatmobileFunhouse_SF | SeismicScan_Distortion | EmissiveColor→—; Opacity→—; Distortion→— |
| Playable_BatmobileFunhouse_SF | Target_Sphere_COMBO_OPT | DiffuseColor→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileFunhouse_SF | Tyre_Smoke | DiffuseColor→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileFunhouse_SF | EMP_BuildUp | EmissiveColor→—; Opacity→—; Distortion→— |
| Playable_BatmobileFunhouse_SF | SeismicSonar_Smoke | DiffuseColor→—; EmissiveColor→—; Opacity→—; WorldPositionOffset→— |
| Playable_BatmobileFunhouse_SF | ThickGas_Tyre | DiffuseColor→—; Normal→—; EmissiveColor→—; OpacityMask→— |
| Playable_BatmobileFunhouse_SF | FearGas_Burnout | DiffuseColor→—; Opacity→— |
| Playable_BatmobileFunhouse_SF | Gas_FollowDissolve | DiffuseColor→—; SpecularColor→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileFunhouse_SF | xrayBatmobile_MASTER | Normal→`xrayBatmobile_MASTER.MaterialExpressionStaticSwitchParameter` [`WhiteSquareTexture`]; EmissiveColor→—; Opacity→—; OpacityMask→— |
| Playable_BatmobileFunhouse_SF | Vehicle_Smoke_01 | DiffuseColor→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileFunhouse_SF | fx_Winch_M_lit | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→—; MetalMask→— |
| Playable_BatmobileFunhouse_SF | Exp_Smoke_M | DiffuseColor→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileFunhouse_SF | Mat_tracerBeam_Dup | EmissiveColor→—; Opacity→— |
| Playable_BatmobileFunhouse_SF | Fire_Proc_MAT | EmissiveColor→—; OpacityMask→— |
| Playable_BatmobileFunhouse_SF | Beam_Mesh_M | EmissiveColor→—; Opacity→—; WorldPositionOffset→— |
| Playable_BatmobileFunhouse_SF | GPU_Spark_ConstantSize | EmissiveColor→—; Opacity→—; WorldPositionOffset→— |
| Playable_BatmobileFunhouse_SF | Smoke_Dissolve | DiffuseColor→—; SpecularColor→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileFunhouse_SF | MAT_BitsOfShockwave | EmissiveColor→—; Opacity→— |
| Playable_BatmobileFunhouse_SF | MAT_Digital_Noise | EmissiveColor→—; Opacity→— |
| Playable_BatmobileFunhouse_SF | MAT_Mud_Tyre_Decal_V05 | DiffuseColor→—; SpecularColor→—; SpecularColor2→—; SpecularPower→—; Normal→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileFunhouse_SF | MAT_Smoke_4x4_LIT | DiffuseColor→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileFunhouse_SF | muzzleflash_straight_02 | EmissiveColor→—; Opacity→—; OpacityMask→— |
| Playable_BatmobileJoker_SF | Batmobile_Body_MASTER | DiffuseColor→`Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` [`NEW_Batmobile_V2_BODY_D`]; SpecularColor→`Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter`; SpecularPower→`Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` [`NEW_Batmobile_V2_BODY_S`]; Normal→`Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` [`NEW_Batmobile_V2_BODY_N`]; EmissiveColor→`Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` |
| Playable_BatmobileJoker_SF | Batmobile_Glass | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→—; Opacity→—; OpacityMask→—; MetalMask→— |
| Playable_BatmobileJoker_SF | Batmobile_Jokerfied_Gloves | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→— |
| Playable_BatmobileJoker_SF | Batmobile_Jokerfied_Hair | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→— |
| Playable_BatmobileJoker_SF | Batmobile_Jokerfied_Shoes | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→— |
| Playable_BatmobileJoker_SF | Batmobile_Jokerfied_Teeth | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→— |
| Playable_BatmobileJoker_SF | Batmobile_Jokerfied_Hair_MAT | DiffuseColor→`Batmobile_Jokerfied_Hair_MAT.MaterialExpressionStaticSwitchParameter`; SpecularColor→—; SpecularPower→—; Normal→`Batmobile_Jokerfied_Hair_MAT.MaterialExpressionTextureSampleParameter2D` [`neutral_normal`]; EmissiveColor→—; Opacity→—; OpacityMask→—; Distortion→—; AnisotropicDirection→`Batmobile_Jokerfied_Hair_MAT.MaterialExpressionVectorParameter`; SSSColor→—; MetalMask→`Batmobile_Jokerfied_Hair_MAT.MaterialExpressionScalarParameter`; TwoSidedLightingMask→—; WorldPositionOffset→— |
| Playable_BatmobileJoker_SF | Batmobile_Jokerfied_V2_MAT | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→—; MetalMask→—; WorldPositionOffset→`Batmobile_Jokerfied_V2_MAT.MaterialExpressionStaticSwitchParameter` |
| Playable_BatmobileJoker_SF | Batmobile_V3_TEXTURES_Body_Decals | DiffuseColor→—; OpacityMask→— |
| Playable_BatmobileJoker_SF | Batmobile_V3_Undercarriage | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; OpacityMask→—; MetalMask→— |
| Playable_BatmobileJoker_SF | Cockpit_Master_Flip_Data | DiffuseColor→—; SpecularColor→—; SpecularPower→—; EmissiveColor→— |
| Playable_BatmobileJoker_SF | Batmobile_V3_Body_NoRain_MAT | DiffuseColor→—; SpecularColor→`Batmobile_V3_Body_NoRain_MAT.MaterialExpressionStaticSwitchParameter`; SpecularPower→—; Normal→—; EmissiveColor→`Batmobile_V3_Body_NoRain_MAT.MaterialExpressionStaticSwitchParameter`; MetalMask→`Batmobile_V3_Body_NoRain_MAT.MaterialExpressionScalarParameter` |
| Playable_BatmobileJoker_SF | Batmobile_V3_Discbreak | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→`Batmobile_V3_Discbreak.MaterialExpressionStaticSwitchParameter`; OpacityMask→—; MetalMask→`Batmobile_V3_Discbreak.MaterialExpressionScalarParameter` |
| Playable_BatmobileJoker_SF | Batmobile_V3_Tyre_V2_MAT | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→—; MetalMask→— |
| Playable_BatmobileJoker_SF | Batmobile_V3_Wheel_V2_MAT | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; MetalMask→— |
| Playable_BatmobileJoker_SF | Batmobile_Worn | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→`Batmobile_Worn.MaterialExpressionStaticSwitchParameter`; MetalMask→—; WorldPositionOffset→`Batmobile_Worn.MaterialExpressionStaticSwitchParameter` |
| Playable_BatmobileJoker_SF | BatmobileV3_Rubber_Bullet | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; MetalMask→— |
| Playable_BatmobileJoker_SF | Batwing_Carrier_MAT | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→— |
| Playable_BatmobileJoker_SF | Hydra_Trails_M | DiffuseColor→—; Normal→—; EmissiveColor→—; Opacity→—; OpacityMask→—; WorldPositionOffset→— |
| Playable_BatmobileJoker_SF | Back_Explosion_PP | EmissiveColor→—; Opacity→— |
| Playable_BatmobileJoker_SF | Game_Cameo_Squirting_FLOWER_MAT | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→— |
| Playable_BatmobileJoker_SF | Helicopter_Police_Rotor_S_MAT | DiffuseColor→—; EmissiveColor→—; Opacity→—; OpacityMask→—; Distortion→— |
| Playable_BatmobileJoker_SF | Batmobile_Takedown_Beam_M | DiffuseColor→—; Normal→—; EmissiveColor→—; Opacity→—; WorldPositionOffset→— |
| Playable_BatmobileJoker_SF | contrail_m | EmissiveColor→—; Opacity→— |
| Playable_BatmobileJoker_SF | Simple_GlowFade | EmissiveColor→—; Opacity→— |
| Playable_BatmobileJoker_SF | Missile_Line_2_Mat | EmissiveColor→—; Opacity→— |
| Playable_BatmobileJoker_SF | Missile_Line_Mat | EmissiveColor→—; Opacity→— |
| Playable_BatmobileJoker_SF | Target_Sphere_COMBO_OPT | DiffuseColor→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileJoker_SF | Tyre_Smoke | DiffuseColor→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileJoker_SF | ThickGas_Tyre | DiffuseColor→—; Normal→—; EmissiveColor→—; OpacityMask→— |
| Playable_BatmobileJoker_SF | FearGas_Burnout | DiffuseColor→—; Opacity→— |
| Playable_BatmobileJoker_SF | Gas_FollowDissolve | DiffuseColor→—; SpecularColor→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileJoker_SF | xrayBatmobile_MASTER | Normal→`xrayBatmobile_MASTER.MaterialExpressionStaticSwitchParameter` [`WhiteSquareTexture`, `Batmobile_MK2_Body2_R`]; EmissiveColor→—; Opacity→—; OpacityMask→— |
| Playable_BatmobileJoker_SF | Falling_Dust_MAT | DiffuseColor→—; Opacity→`Falling_Dust_MAT.MaterialExpressionStaticSwitchParameter` |
| Playable_BatmobileJoker_SF | Engine_Distortion | EmissiveColor→—; Opacity→—; OpacityMask→—; Distortion→— |
| Playable_BatmobileJoker_SF | Exp_Smoke_M | DiffuseColor→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileJoker_SF | Mat_tracerBeam_Dup | EmissiveColor→—; Opacity→— |
| Playable_BatmobileJoker_SF | Fire_Proc_MAT | EmissiveColor→—; OpacityMask→— |
| Playable_BatmobileJoker_SF | Beam_Mesh_M | EmissiveColor→—; Opacity→—; WorldPositionOffset→— |
| Playable_BatmobileJoker_SF | MAT_Mud_Tyre_Decal_V05 | DiffuseColor→—; SpecularColor→—; SpecularColor2→—; SpecularPower→—; Normal→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileJoker_SF | MAT_Smoke_4x4_LIT | DiffuseColor→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileJoker_SF | Dusty_hit_01_4x4 | EmissiveColor→—; Opacity→—; OpacityMask→— |
| Playable_BatmobileJoker_SF | muzzleflash_straight_02 | EmissiveColor→—; Opacity→—; OpacityMask→— |
| Playable_BatmobileJoker_SF | Smoke_02_SubUV_16_unlit | DiffuseColor→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileMK2_SF | Batmobile_Body_MASTER | DiffuseColor→`Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` [`NEW_Batmobile_V2_BODY_D`]; SpecularColor→`Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter`; SpecularPower→`Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` [`NEW_Batmobile_V2_BODY_S`]; Normal→`Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` [`NEW_Batmobile_V2_BODY_N`]; EmissiveColor→`Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` |
| Playable_BatmobileMK2_SF | Batmobile_Glass | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→—; Opacity→—; OpacityMask→—; MetalMask→— |
| Playable_BatmobileMK2_SF | Batmobile_MK2_WheelArch_MAT | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→—; MetalMask→—; WorldPositionOffset→`Batmobile_MK2_WheelArch_MAT.MaterialExpressionStaticSwitchParameter` |
| Playable_BatmobileMK2_SF | Batmobile_V3_TEXTURES_Body_Decals | DiffuseColor→—; OpacityMask→— |
| Playable_BatmobileMK2_SF | Batmobile_V3_Undercarriage | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; OpacityMask→—; MetalMask→— |
| Playable_BatmobileMK2_SF | Cockpit_Master_Flip_Data | DiffuseColor→—; SpecularColor→—; SpecularPower→—; EmissiveColor→— |
| Playable_BatmobileMK2_SF | Batmobile_V3_Body_NoRain_MAT | DiffuseColor→—; SpecularColor→`Batmobile_V3_Body_NoRain_MAT.MaterialExpressionStaticSwitchParameter`; SpecularPower→—; Normal→—; EmissiveColor→`Batmobile_V3_Body_NoRain_MAT.MaterialExpressionStaticSwitchParameter`; MetalMask→`Batmobile_V3_Body_NoRain_MAT.MaterialExpressionScalarParameter` |
| Playable_BatmobileMK2_SF | Batmobile_V3_Discbreak | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→`Batmobile_V3_Discbreak.MaterialExpressionStaticSwitchParameter`; OpacityMask→—; MetalMask→`Batmobile_V3_Discbreak.MaterialExpressionScalarParameter` |
| Playable_BatmobileMK2_SF | Batmobile_V3_Tyre_V2_MAT | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→—; MetalMask→— |
| Playable_BatmobileMK2_SF | Batmobile_V3_Wheel_V2_MAT | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; MetalMask→— |
| Playable_BatmobileMK2_SF | Batmobile_Worn | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→`Batmobile_Worn.MaterialExpressionStaticSwitchParameter`; MetalMask→—; WorldPositionOffset→`Batmobile_Worn.MaterialExpressionStaticSwitchParameter` |
| Playable_BatmobileMK2_SF | Batmobile_Worn_NoRain | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→—; MetalMask→—; WorldPositionOffset→— |
| Playable_BatmobileMK2_SF | BatmobileV3_Rubber_Bullet | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; MetalMask→— |
| Playable_BatmobileMK2_SF | Back_Explosion_PP | EmissiveColor→—; Opacity→— |
| Playable_BatmobileMK2_SF | Batmobile_Takedown_Beam_M | DiffuseColor→—; Normal→—; EmissiveColor→—; Opacity→—; WorldPositionOffset→— |
| Playable_BatmobileMK2_SF | Stagg_Battery_Energy_01_MAT | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→—; Opacity→—; WorldPositionOffset→— |
| Playable_BatmobileMK2_SF | Stagg_Battery_01_MAT | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→—; OpacityMask→— |
| Playable_BatmobileMK2_SF | Burnout_Mat_MUD_NV | DiffuseColor→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileMK2_SF | Drone_Bomb_Radius | EmissiveColor→—; Opacity→— |
| Playable_BatmobileMK2_SF | Batmobile_Fire_Main | EmissiveColor→—; Opacity→—; Distortion→—; WorldPositionOffset→— |
| Playable_BatmobileMK2_SF | Batmobile_Seismic_Sonar | EmissiveColor→—; Opacity→—; Distortion→— |
| Playable_BatmobileMK2_SF | DroneHacker_Beam | EmissiveColor→—; Opacity→— |
| Playable_BatmobileMK2_SF | Missile_Line_2_Mat | EmissiveColor→—; Opacity→— |
| Playable_BatmobileMK2_SF | Missile_Line_Mat | EmissiveColor→—; Opacity→— |
| Playable_BatmobileMK2_SF | SeismicScan_Distortion | EmissiveColor→—; Opacity→—; Distortion→— |
| Playable_BatmobileMK2_SF | Target_Sphere_COMBO_OPT | DiffuseColor→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileMK2_SF | Tyre_Smoke | DiffuseColor→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileMK2_SF | EMP_BuildUp | EmissiveColor→—; Opacity→—; Distortion→— |
| Playable_BatmobileMK2_SF | SeismicSonar_Smoke | DiffuseColor→—; EmissiveColor→—; Opacity→—; WorldPositionOffset→— |
| Playable_BatmobileMK2_SF | ThickGas_Tyre | DiffuseColor→—; Normal→—; EmissiveColor→—; OpacityMask→— |
| Playable_BatmobileMK2_SF | FearGas_Burnout | DiffuseColor→—; Opacity→— |
| Playable_BatmobileMK2_SF | Gas_FollowDissolve | DiffuseColor→—; SpecularColor→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileMK2_SF | xrayBatmobile_MASTER | Normal→`xrayBatmobile_MASTER.MaterialExpressionStaticSwitchParameter` [`WhiteSquareTexture`]; EmissiveColor→—; Opacity→—; OpacityMask→— |
| Playable_BatmobileMK2_SF | Vehicle_Smoke_01 | DiffuseColor→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileMK2_SF | fx_Winch_M_lit | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→—; MetalMask→— |
| Playable_BatmobileMK2_SF | Exp_Smoke_M | DiffuseColor→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileMK2_SF | Mat_tracerBeam_Dup | EmissiveColor→—; Opacity→— |
| Playable_BatmobileMK2_SF | Fire_Proc_MAT | EmissiveColor→—; OpacityMask→— |
| Playable_BatmobileMK2_SF | Beam_Mesh_M | EmissiveColor→—; Opacity→—; WorldPositionOffset→— |
| Playable_BatmobileMK2_SF | GPU_Spark_ConstantSize | EmissiveColor→—; Opacity→—; WorldPositionOffset→— |
| Playable_BatmobileMK2_SF | Smoke_Dissolve | DiffuseColor→—; SpecularColor→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileMK2_SF | MAT_BitsOfShockwave | EmissiveColor→—; Opacity→— |
| Playable_BatmobileMK2_SF | MAT_Digital_Noise | EmissiveColor→—; Opacity→— |
| Playable_BatmobileMK2_SF | MAT_Mud_Tyre_Decal_V05 | DiffuseColor→—; SpecularColor→—; SpecularColor2→—; SpecularPower→—; Normal→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileMK2_SF | MAT_Smoke_4x4_LIT | DiffuseColor→—; EmissiveColor→—; Opacity→— |
| Playable_BatmobileMK2_SF | muzzleflash_straight_02 | EmissiveColor→—; Opacity→—; OpacityMask→— |
| Playable_Batmobile_SF | Batmobile_Body_MASTER | DiffuseColor→`Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` [`NEW_Batmobile_V2_BODY_D`]; SpecularColor→`Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter`; SpecularPower→`Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` [`NEW_Batmobile_V2_BODY_S`]; Normal→`Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` [`NEW_Batmobile_V2_BODY_N`]; EmissiveColor→`Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` |
| Playable_Batmobile_SF | Batmobile_Glass | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→—; Opacity→—; OpacityMask→—; MetalMask→— |
| Playable_Batmobile_SF | Stagg_Battery_01_MAT | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→—; OpacityMask→— |
| Playable_Batmobile_SF | Stagg_Battery_Energy_01_MAT | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→—; Opacity→—; WorldPositionOffset→— |
| Playable_Batmobile_SF | Batmobile_V3_TEXTURES_Body_Decals | DiffuseColor→—; OpacityMask→— |
| Playable_Batmobile_SF | Batmobile_V3_Undercarriage | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; OpacityMask→—; MetalMask→— |
| Playable_Batmobile_SF | Cockpit_Master_Flip_Data | DiffuseColor→—; SpecularColor→—; SpecularPower→—; EmissiveColor→— |
| Playable_Batmobile_SF | Batmobile_V3_Body_NoRain_MAT | DiffuseColor→—; SpecularColor→`Batmobile_V3_Body_NoRain_MAT.MaterialExpressionStaticSwitchParameter`; SpecularPower→—; Normal→—; EmissiveColor→`Batmobile_V3_Body_NoRain_MAT.MaterialExpressionStaticSwitchParameter`; MetalMask→`Batmobile_V3_Body_NoRain_MAT.MaterialExpressionScalarParameter` |
| Playable_Batmobile_SF | Batmobile_V3_Discbreak | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→`Batmobile_V3_Discbreak.MaterialExpressionStaticSwitchParameter`; OpacityMask→—; MetalMask→`Batmobile_V3_Discbreak.MaterialExpressionScalarParameter` |
| Playable_Batmobile_SF | Batmobile_V3_Tyre_V2_MAT | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→—; MetalMask→— |
| Playable_Batmobile_SF | Batmobile_V3_Wheel_V2_MAT | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; MetalMask→— |
| Playable_Batmobile_SF | Batmobile_Worn | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→`Batmobile_Worn.MaterialExpressionStaticSwitchParameter`; MetalMask→—; WorldPositionOffset→`Batmobile_Worn.MaterialExpressionStaticSwitchParameter` |
| Playable_Batmobile_SF | Batmobile_Worn_NoRain | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→—; MetalMask→—; WorldPositionOffset→— |
| Playable_Batmobile_SF | BatmobileV3_Rubber_Bullet | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; MetalMask→— |
| Playable_Batmobile_SF | Back_Explosion_PP | EmissiveColor→—; Opacity→— |
| Playable_Batmobile_SF | Batmobile_Takedown_Beam_M | DiffuseColor→—; Normal→—; EmissiveColor→—; Opacity→—; WorldPositionOffset→— |
| Playable_Batmobile_SF | Burnout_Mat_MUD_NV | DiffuseColor→—; EmissiveColor→—; Opacity→— |
| Playable_Batmobile_SF | Drone_Bomb_Radius | EmissiveColor→—; Opacity→— |
| Playable_Batmobile_SF | Batmobile_Fire_Main | EmissiveColor→—; Opacity→—; Distortion→—; WorldPositionOffset→— |
| Playable_Batmobile_SF | Batmobile_Seismic_Sonar | EmissiveColor→—; Opacity→—; Distortion→— |
| Playable_Batmobile_SF | DroneHacker_Beam | EmissiveColor→—; Opacity→— |
| Playable_Batmobile_SF | Missile_Line_2_Mat | EmissiveColor→—; Opacity→— |
| Playable_Batmobile_SF | Missile_Line_Mat | EmissiveColor→—; Opacity→— |
| Playable_Batmobile_SF | SeismicScan_Distortion | EmissiveColor→—; Opacity→—; Distortion→— |
| Playable_Batmobile_SF | Target_Sphere_COMBO_OPT | DiffuseColor→—; EmissiveColor→—; Opacity→— |
| Playable_Batmobile_SF | Tyre_Smoke | DiffuseColor→—; EmissiveColor→—; Opacity→— |
| Playable_Batmobile_SF | EMP_BuildUp | EmissiveColor→—; Opacity→—; Distortion→— |
| Playable_Batmobile_SF | SeismicSonar_Smoke | DiffuseColor→—; EmissiveColor→—; Opacity→—; WorldPositionOffset→— |
| Playable_Batmobile_SF | ThickGas_Tyre | DiffuseColor→—; Normal→—; EmissiveColor→—; OpacityMask→— |
| Playable_Batmobile_SF | FearGas_Burnout | DiffuseColor→—; Opacity→— |
| Playable_Batmobile_SF | Gas_FollowDissolve | DiffuseColor→—; SpecularColor→—; EmissiveColor→—; Opacity→— |
| Playable_Batmobile_SF | xrayBatmobile_MASTER | Normal→`xrayBatmobile_MASTER.MaterialExpressionStaticSwitchParameter` [`WhiteSquareTexture`]; EmissiveColor→—; Opacity→—; OpacityMask→— |
| Playable_Batmobile_SF | Vehicle_Smoke_01 | DiffuseColor→—; EmissiveColor→—; Opacity→— |
| Playable_Batmobile_SF | fx_Winch_M_lit | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→—; MetalMask→— |
| Playable_Batmobile_SF | Exp_Smoke_M | DiffuseColor→—; EmissiveColor→—; Opacity→— |
| Playable_Batmobile_SF | Mat_tracerBeam_Dup | EmissiveColor→—; Opacity→— |
| Playable_Batmobile_SF | Fire_Proc_MAT | EmissiveColor→—; OpacityMask→— |
| Playable_Batmobile_SF | Beam_Mesh_M | EmissiveColor→—; Opacity→—; WorldPositionOffset→— |
| Playable_Batmobile_SF | GPU_Spark_ConstantSize | EmissiveColor→—; Opacity→—; WorldPositionOffset→— |
| Playable_Batmobile_SF | Smoke_Dissolve | DiffuseColor→—; SpecularColor→—; EmissiveColor→—; Opacity→— |
| Playable_Batmobile_SF | MAT_BitsOfShockwave | EmissiveColor→—; Opacity→— |
| Playable_Batmobile_SF | MAT_Digital_Noise | EmissiveColor→—; Opacity→— |
| Playable_Batmobile_SF | MAT_Mud_Tyre_Decal_V05 | DiffuseColor→—; SpecularColor→—; SpecularColor2→—; SpecularPower→—; Normal→—; EmissiveColor→—; Opacity→— |
| Playable_Batmobile_SF | MAT_Smoke_4x4_LIT | DiffuseColor→—; EmissiveColor→—; Opacity→— |
| Playable_Batmobile_SF | muzzleflash_straight_02 | EmissiveColor→—; Opacity→—; OpacityMask→— |
| Playable_Batmobile_Std_6_SF | Batmobile_Stage6 | DiffuseColor→—; SpecularColor→—; SpecularPower→—; Normal→—; EmissiveColor→`Batmobile_Stage6.MaterialExpressionStaticSwitchParameter` [`Batmobile_Micropattern_A`, `Batmobile_TEXTURES_FearSand_N`]; MetalMask→—; WorldPositionOffset→`Batmobile_Stage6.MaterialExpressionStaticSwitchParameter` |

## Slot → texture (masters)

| package | material | slot | expression | texture |
|---|---|---|---|---|
| Playable_BatmobileFunhouse_SF | `Batmobile_Body_MASTER` | DiffuseColor | `Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` | `Batmobile_V2_Textures_NEW.NEW_Batmobile_V2_BODY_D` |
| Playable_BatmobileFunhouse_SF | `Batmobile_Body_MASTER` | SpecularColor | `Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Body_MASTER` | SpecularPower | `Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` | `Batmobile_V2_Textures_NEW.NEW_Batmobile_V2_BODY_S` |
| Playable_BatmobileFunhouse_SF | `Batmobile_Body_MASTER` | Normal | `Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` | `Batmobile_V2_Textures_NEW.NEW_Batmobile_V2_BODY_N` |
| Playable_BatmobileFunhouse_SF | `Batmobile_Body_MASTER` | EmissiveColor | `Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Glass` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Glass` | SpecularColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Glass` | SpecularPower | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Glass` | Normal | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Glass` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Glass` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Glass` | OpacityMask | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Glass` | MetalMask | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Gloves` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Gloves` | SpecularColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Gloves` | SpecularPower | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Gloves` | Normal | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Hair` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Hair` | SpecularColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Hair` | SpecularPower | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Hair` | Normal | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Shoes` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Shoes` | SpecularColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Shoes` | SpecularPower | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Shoes` | Normal | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Teeth` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Teeth` | SpecularColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Teeth` | SpecularPower | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Teeth` | Normal | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Hair_MAT` | DiffuseColor | `Batmobile_Jokerfied_Hair_MAT.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Hair_MAT` | SpecularColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Hair_MAT` | SpecularPower | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Hair_MAT` | Normal | `Batmobile_Jokerfied_Hair_MAT.MaterialExpressionTextureSampleParameter2D` | `Engine.neutral_normal`; `Engine.fx_waterCaustic1` |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Hair_MAT` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Hair_MAT` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Hair_MAT` | OpacityMask | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Hair_MAT` | Distortion | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Hair_MAT` | AnisotropicDirection | `Batmobile_Jokerfied_Hair_MAT.MaterialExpressionVectorParameter` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Hair_MAT` | SSSColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Hair_MAT` | MetalMask | `Batmobile_Jokerfied_Hair_MAT.MaterialExpressionScalarParameter` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Hair_MAT` | TwoSidedLightingMask | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_Hair_MAT` | WorldPositionOffset | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_V2_MAT` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_V2_MAT` | SpecularColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_V2_MAT` | SpecularPower | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_V2_MAT` | Normal | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_V2_MAT` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_V2_MAT` | MetalMask | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Jokerfied_V2_MAT` | WorldPositionOffset | `Batmobile_Jokerfied_V2_MAT.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_TEXTURES_Body_Decals` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_TEXTURES_Body_Decals` | OpacityMask | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Undercarriage` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Undercarriage` | SpecularColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Undercarriage` | SpecularPower | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Undercarriage` | Normal | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Undercarriage` | OpacityMask | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Undercarriage` | MetalMask | `—` | — |
| Playable_BatmobileFunhouse_SF | `Cockpit_Master_Flip_Data` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Cockpit_Master_Flip_Data` | SpecularColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Cockpit_Master_Flip_Data` | SpecularPower | `—` | — |
| Playable_BatmobileFunhouse_SF | `Cockpit_Master_Flip_Data` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Body_NoRain_MAT` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Body_NoRain_MAT` | SpecularColor | `Batmobile_V3_Body_NoRain_MAT.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Body_NoRain_MAT` | SpecularPower | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Body_NoRain_MAT` | Normal | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Body_NoRain_MAT` | EmissiveColor | `Batmobile_V3_Body_NoRain_MAT.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Body_NoRain_MAT` | MetalMask | `Batmobile_V3_Body_NoRain_MAT.MaterialExpressionScalarParameter` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Discbreak` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Discbreak` | SpecularColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Discbreak` | SpecularPower | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Discbreak` | Normal | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Discbreak` | EmissiveColor | `Batmobile_V3_Discbreak.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Discbreak` | OpacityMask | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Discbreak` | MetalMask | `Batmobile_V3_Discbreak.MaterialExpressionScalarParameter` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Tyre_V2_MAT` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Tyre_V2_MAT` | SpecularColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Tyre_V2_MAT` | SpecularPower | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Tyre_V2_MAT` | Normal | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Tyre_V2_MAT` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Tyre_V2_MAT` | MetalMask | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Wheel_V2_MAT` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Wheel_V2_MAT` | SpecularColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Wheel_V2_MAT` | SpecularPower | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Wheel_V2_MAT` | Normal | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_V3_Wheel_V2_MAT` | MetalMask | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Worn` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Worn` | SpecularColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Worn` | SpecularPower | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Worn` | Normal | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Worn` | EmissiveColor | `Batmobile_Worn.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Worn` | MetalMask | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Worn` | WorldPositionOffset | `Batmobile_Worn.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileFunhouse_SF | `BatmobileV3_Rubber_Bullet` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `BatmobileV3_Rubber_Bullet` | SpecularColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `BatmobileV3_Rubber_Bullet` | SpecularPower | `—` | — |
| Playable_BatmobileFunhouse_SF | `BatmobileV3_Rubber_Bullet` | Normal | `—` | — |
| Playable_BatmobileFunhouse_SF | `BatmobileV3_Rubber_Bullet` | MetalMask | `—` | — |
| Playable_BatmobileFunhouse_SF | `Back_Explosion_PP` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Back_Explosion_PP` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `Game_Cameo_Squirting_FLOWER_MAT` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Game_Cameo_Squirting_FLOWER_MAT` | SpecularColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Game_Cameo_Squirting_FLOWER_MAT` | SpecularPower | `—` | — |
| Playable_BatmobileFunhouse_SF | `Game_Cameo_Squirting_FLOWER_MAT` | Normal | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Takedown_Beam_M` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Takedown_Beam_M` | Normal | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Takedown_Beam_M` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Takedown_Beam_M` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Takedown_Beam_M` | WorldPositionOffset | `—` | — |
| Playable_BatmobileFunhouse_SF | `Burnout_Mat_MUD_NV` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Burnout_Mat_MUD_NV` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Burnout_Mat_MUD_NV` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `Drone_Bomb_Radius` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Drone_Bomb_Radius` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Fire_Main` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Fire_Main` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Fire_Main` | Distortion | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Fire_Main` | WorldPositionOffset | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Seismic_Sonar` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Seismic_Sonar` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `Batmobile_Seismic_Sonar` | Distortion | `—` | — |
| Playable_BatmobileFunhouse_SF | `DroneHacker_Beam` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `DroneHacker_Beam` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `Missile_Line_2_Mat` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Missile_Line_2_Mat` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `Missile_Line_Mat` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Missile_Line_Mat` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `SeismicScan_Distortion` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `SeismicScan_Distortion` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `SeismicScan_Distortion` | Distortion | `—` | — |
| Playable_BatmobileFunhouse_SF | `Target_Sphere_COMBO_OPT` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Target_Sphere_COMBO_OPT` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Target_Sphere_COMBO_OPT` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `Tyre_Smoke` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Tyre_Smoke` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Tyre_Smoke` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `EMP_BuildUp` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `EMP_BuildUp` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `EMP_BuildUp` | Distortion | `—` | — |
| Playable_BatmobileFunhouse_SF | `SeismicSonar_Smoke` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `SeismicSonar_Smoke` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `SeismicSonar_Smoke` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `SeismicSonar_Smoke` | WorldPositionOffset | `—` | — |
| Playable_BatmobileFunhouse_SF | `ThickGas_Tyre` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `ThickGas_Tyre` | Normal | `—` | — |
| Playable_BatmobileFunhouse_SF | `ThickGas_Tyre` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `ThickGas_Tyre` | OpacityMask | `—` | — |
| Playable_BatmobileFunhouse_SF | `FearGas_Burnout` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `FearGas_Burnout` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `Gas_FollowDissolve` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Gas_FollowDissolve` | SpecularColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Gas_FollowDissolve` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Gas_FollowDissolve` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `xrayBatmobile_MASTER` | Normal | `xrayBatmobile_MASTER.MaterialExpressionStaticSwitchParameter` | `Engine.WhiteSquareTexture` |
| Playable_BatmobileFunhouse_SF | `xrayBatmobile_MASTER` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `xrayBatmobile_MASTER` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `xrayBatmobile_MASTER` | OpacityMask | `—` | — |
| Playable_BatmobileFunhouse_SF | `Vehicle_Smoke_01` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Vehicle_Smoke_01` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Vehicle_Smoke_01` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `fx_Winch_M_lit` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `fx_Winch_M_lit` | SpecularColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `fx_Winch_M_lit` | SpecularPower | `—` | — |
| Playable_BatmobileFunhouse_SF | `fx_Winch_M_lit` | Normal | `—` | — |
| Playable_BatmobileFunhouse_SF | `fx_Winch_M_lit` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `fx_Winch_M_lit` | MetalMask | `—` | — |
| Playable_BatmobileFunhouse_SF | `Exp_Smoke_M` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Exp_Smoke_M` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Exp_Smoke_M` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `Mat_tracerBeam_Dup` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Mat_tracerBeam_Dup` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `Fire_Proc_MAT` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Fire_Proc_MAT` | OpacityMask | `—` | — |
| Playable_BatmobileFunhouse_SF | `Beam_Mesh_M` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Beam_Mesh_M` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `Beam_Mesh_M` | WorldPositionOffset | `—` | — |
| Playable_BatmobileFunhouse_SF | `GPU_Spark_ConstantSize` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `GPU_Spark_ConstantSize` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `GPU_Spark_ConstantSize` | WorldPositionOffset | `—` | — |
| Playable_BatmobileFunhouse_SF | `Smoke_Dissolve` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Smoke_Dissolve` | SpecularColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Smoke_Dissolve` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `Smoke_Dissolve` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `MAT_BitsOfShockwave` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `MAT_BitsOfShockwave` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `MAT_Digital_Noise` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `MAT_Digital_Noise` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `MAT_Mud_Tyre_Decal_V05` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `MAT_Mud_Tyre_Decal_V05` | SpecularColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `MAT_Mud_Tyre_Decal_V05` | SpecularColor2 | `—` | — |
| Playable_BatmobileFunhouse_SF | `MAT_Mud_Tyre_Decal_V05` | SpecularPower | `—` | — |
| Playable_BatmobileFunhouse_SF | `MAT_Mud_Tyre_Decal_V05` | Normal | `—` | — |
| Playable_BatmobileFunhouse_SF | `MAT_Mud_Tyre_Decal_V05` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `MAT_Mud_Tyre_Decal_V05` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `MAT_Smoke_4x4_LIT` | DiffuseColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `MAT_Smoke_4x4_LIT` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `MAT_Smoke_4x4_LIT` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `muzzleflash_straight_02` | EmissiveColor | `—` | — |
| Playable_BatmobileFunhouse_SF | `muzzleflash_straight_02` | Opacity | `—` | — |
| Playable_BatmobileFunhouse_SF | `muzzleflash_straight_02` | OpacityMask | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Body_MASTER` | DiffuseColor | `Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` | `Batmobile_V2_Textures_NEW.NEW_Batmobile_V2_BODY_D` |
| Playable_BatmobileJoker_SF | `Batmobile_Body_MASTER` | SpecularColor | `Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Body_MASTER` | SpecularPower | `Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` | `Batmobile_V2_Textures_NEW.NEW_Batmobile_V2_BODY_S` |
| Playable_BatmobileJoker_SF | `Batmobile_Body_MASTER` | Normal | `Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` | `Batmobile_V2_Textures_NEW.NEW_Batmobile_V2_BODY_N` |
| Playable_BatmobileJoker_SF | `Batmobile_Body_MASTER` | EmissiveColor | `Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Glass` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Glass` | SpecularColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Glass` | SpecularPower | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Glass` | Normal | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Glass` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Glass` | Opacity | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Glass` | OpacityMask | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Glass` | MetalMask | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Gloves` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Gloves` | SpecularColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Gloves` | SpecularPower | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Gloves` | Normal | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Hair` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Hair` | SpecularColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Hair` | SpecularPower | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Hair` | Normal | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Shoes` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Shoes` | SpecularColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Shoes` | SpecularPower | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Shoes` | Normal | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Teeth` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Teeth` | SpecularColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Teeth` | SpecularPower | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Teeth` | Normal | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Hair_MAT` | DiffuseColor | `Batmobile_Jokerfied_Hair_MAT.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Hair_MAT` | SpecularColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Hair_MAT` | SpecularPower | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Hair_MAT` | Normal | `Batmobile_Jokerfied_Hair_MAT.MaterialExpressionTextureSampleParameter2D` | `Engine.neutral_normal` |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Hair_MAT` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Hair_MAT` | Opacity | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Hair_MAT` | OpacityMask | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Hair_MAT` | Distortion | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Hair_MAT` | AnisotropicDirection | `Batmobile_Jokerfied_Hair_MAT.MaterialExpressionVectorParameter` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Hair_MAT` | SSSColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Hair_MAT` | MetalMask | `Batmobile_Jokerfied_Hair_MAT.MaterialExpressionScalarParameter` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Hair_MAT` | TwoSidedLightingMask | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_Hair_MAT` | WorldPositionOffset | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_V2_MAT` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_V2_MAT` | SpecularColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_V2_MAT` | SpecularPower | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_V2_MAT` | Normal | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_V2_MAT` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_V2_MAT` | MetalMask | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Jokerfied_V2_MAT` | WorldPositionOffset | `Batmobile_Jokerfied_V2_MAT.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_TEXTURES_Body_Decals` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_TEXTURES_Body_Decals` | OpacityMask | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Undercarriage` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Undercarriage` | SpecularColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Undercarriage` | SpecularPower | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Undercarriage` | Normal | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Undercarriage` | OpacityMask | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Undercarriage` | MetalMask | `—` | — |
| Playable_BatmobileJoker_SF | `Cockpit_Master_Flip_Data` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Cockpit_Master_Flip_Data` | SpecularColor | `—` | — |
| Playable_BatmobileJoker_SF | `Cockpit_Master_Flip_Data` | SpecularPower | `—` | — |
| Playable_BatmobileJoker_SF | `Cockpit_Master_Flip_Data` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Body_NoRain_MAT` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Body_NoRain_MAT` | SpecularColor | `Batmobile_V3_Body_NoRain_MAT.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Body_NoRain_MAT` | SpecularPower | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Body_NoRain_MAT` | Normal | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Body_NoRain_MAT` | EmissiveColor | `Batmobile_V3_Body_NoRain_MAT.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Body_NoRain_MAT` | MetalMask | `Batmobile_V3_Body_NoRain_MAT.MaterialExpressionScalarParameter` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Discbreak` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Discbreak` | SpecularColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Discbreak` | SpecularPower | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Discbreak` | Normal | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Discbreak` | EmissiveColor | `Batmobile_V3_Discbreak.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Discbreak` | OpacityMask | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Discbreak` | MetalMask | `Batmobile_V3_Discbreak.MaterialExpressionScalarParameter` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Tyre_V2_MAT` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Tyre_V2_MAT` | SpecularColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Tyre_V2_MAT` | SpecularPower | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Tyre_V2_MAT` | Normal | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Tyre_V2_MAT` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Tyre_V2_MAT` | MetalMask | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Wheel_V2_MAT` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Wheel_V2_MAT` | SpecularColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Wheel_V2_MAT` | SpecularPower | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Wheel_V2_MAT` | Normal | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_V3_Wheel_V2_MAT` | MetalMask | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Worn` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Worn` | SpecularColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Worn` | SpecularPower | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Worn` | Normal | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Worn` | EmissiveColor | `Batmobile_Worn.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Worn` | MetalMask | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Worn` | WorldPositionOffset | `Batmobile_Worn.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileJoker_SF | `BatmobileV3_Rubber_Bullet` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `BatmobileV3_Rubber_Bullet` | SpecularColor | `—` | — |
| Playable_BatmobileJoker_SF | `BatmobileV3_Rubber_Bullet` | SpecularPower | `—` | — |
| Playable_BatmobileJoker_SF | `BatmobileV3_Rubber_Bullet` | Normal | `—` | — |
| Playable_BatmobileJoker_SF | `BatmobileV3_Rubber_Bullet` | MetalMask | `—` | — |
| Playable_BatmobileJoker_SF | `Batwing_Carrier_MAT` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batwing_Carrier_MAT` | SpecularColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batwing_Carrier_MAT` | SpecularPower | `—` | — |
| Playable_BatmobileJoker_SF | `Batwing_Carrier_MAT` | Normal | `—` | — |
| Playable_BatmobileJoker_SF | `Batwing_Carrier_MAT` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `Hydra_Trails_M` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Hydra_Trails_M` | Normal | `—` | — |
| Playable_BatmobileJoker_SF | `Hydra_Trails_M` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `Hydra_Trails_M` | Opacity | `—` | — |
| Playable_BatmobileJoker_SF | `Hydra_Trails_M` | OpacityMask | `—` | — |
| Playable_BatmobileJoker_SF | `Hydra_Trails_M` | WorldPositionOffset | `—` | — |
| Playable_BatmobileJoker_SF | `Back_Explosion_PP` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `Back_Explosion_PP` | Opacity | `—` | — |
| Playable_BatmobileJoker_SF | `Game_Cameo_Squirting_FLOWER_MAT` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Game_Cameo_Squirting_FLOWER_MAT` | SpecularColor | `—` | — |
| Playable_BatmobileJoker_SF | `Game_Cameo_Squirting_FLOWER_MAT` | SpecularPower | `—` | — |
| Playable_BatmobileJoker_SF | `Game_Cameo_Squirting_FLOWER_MAT` | Normal | `—` | — |
| Playable_BatmobileJoker_SF | `Helicopter_Police_Rotor_S_MAT` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Helicopter_Police_Rotor_S_MAT` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `Helicopter_Police_Rotor_S_MAT` | Opacity | `—` | — |
| Playable_BatmobileJoker_SF | `Helicopter_Police_Rotor_S_MAT` | OpacityMask | `—` | — |
| Playable_BatmobileJoker_SF | `Helicopter_Police_Rotor_S_MAT` | Distortion | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Takedown_Beam_M` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Takedown_Beam_M` | Normal | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Takedown_Beam_M` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Takedown_Beam_M` | Opacity | `—` | — |
| Playable_BatmobileJoker_SF | `Batmobile_Takedown_Beam_M` | WorldPositionOffset | `—` | — |
| Playable_BatmobileJoker_SF | `contrail_m` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `contrail_m` | Opacity | `—` | — |
| Playable_BatmobileJoker_SF | `Simple_GlowFade` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `Simple_GlowFade` | Opacity | `—` | — |
| Playable_BatmobileJoker_SF | `Missile_Line_2_Mat` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `Missile_Line_2_Mat` | Opacity | `—` | — |
| Playable_BatmobileJoker_SF | `Missile_Line_Mat` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `Missile_Line_Mat` | Opacity | `—` | — |
| Playable_BatmobileJoker_SF | `Target_Sphere_COMBO_OPT` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Target_Sphere_COMBO_OPT` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `Target_Sphere_COMBO_OPT` | Opacity | `—` | — |
| Playable_BatmobileJoker_SF | `Tyre_Smoke` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Tyre_Smoke` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `Tyre_Smoke` | Opacity | `—` | — |
| Playable_BatmobileJoker_SF | `ThickGas_Tyre` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `ThickGas_Tyre` | Normal | `—` | — |
| Playable_BatmobileJoker_SF | `ThickGas_Tyre` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `ThickGas_Tyre` | OpacityMask | `—` | — |
| Playable_BatmobileJoker_SF | `FearGas_Burnout` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `FearGas_Burnout` | Opacity | `—` | — |
| Playable_BatmobileJoker_SF | `Gas_FollowDissolve` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Gas_FollowDissolve` | SpecularColor | `—` | — |
| Playable_BatmobileJoker_SF | `Gas_FollowDissolve` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `Gas_FollowDissolve` | Opacity | `—` | — |
| Playable_BatmobileJoker_SF | `xrayBatmobile_MASTER` | Normal | `xrayBatmobile_MASTER.MaterialExpressionStaticSwitchParameter` | `Engine.WhiteSquareTexture`; `Textures.Batmobile_MK2_Body2_R` |
| Playable_BatmobileJoker_SF | `xrayBatmobile_MASTER` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `xrayBatmobile_MASTER` | Opacity | `—` | — |
| Playable_BatmobileJoker_SF | `xrayBatmobile_MASTER` | OpacityMask | `—` | — |
| Playable_BatmobileJoker_SF | `Falling_Dust_MAT` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Falling_Dust_MAT` | Opacity | `Falling_Dust_MAT.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileJoker_SF | `Engine_Distortion` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `Engine_Distortion` | Opacity | `—` | — |
| Playable_BatmobileJoker_SF | `Engine_Distortion` | OpacityMask | `—` | — |
| Playable_BatmobileJoker_SF | `Engine_Distortion` | Distortion | `—` | — |
| Playable_BatmobileJoker_SF | `Exp_Smoke_M` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Exp_Smoke_M` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `Exp_Smoke_M` | Opacity | `—` | — |
| Playable_BatmobileJoker_SF | `Mat_tracerBeam_Dup` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `Mat_tracerBeam_Dup` | Opacity | `—` | — |
| Playable_BatmobileJoker_SF | `Fire_Proc_MAT` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `Fire_Proc_MAT` | OpacityMask | `—` | — |
| Playable_BatmobileJoker_SF | `Beam_Mesh_M` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `Beam_Mesh_M` | Opacity | `—` | — |
| Playable_BatmobileJoker_SF | `Beam_Mesh_M` | WorldPositionOffset | `—` | — |
| Playable_BatmobileJoker_SF | `MAT_Mud_Tyre_Decal_V05` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `MAT_Mud_Tyre_Decal_V05` | SpecularColor | `—` | — |
| Playable_BatmobileJoker_SF | `MAT_Mud_Tyre_Decal_V05` | SpecularColor2 | `—` | — |
| Playable_BatmobileJoker_SF | `MAT_Mud_Tyre_Decal_V05` | SpecularPower | `—` | — |
| Playable_BatmobileJoker_SF | `MAT_Mud_Tyre_Decal_V05` | Normal | `—` | — |
| Playable_BatmobileJoker_SF | `MAT_Mud_Tyre_Decal_V05` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `MAT_Mud_Tyre_Decal_V05` | Opacity | `—` | — |
| Playable_BatmobileJoker_SF | `MAT_Smoke_4x4_LIT` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `MAT_Smoke_4x4_LIT` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `MAT_Smoke_4x4_LIT` | Opacity | `—` | — |
| Playable_BatmobileJoker_SF | `Dusty_hit_01_4x4` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `Dusty_hit_01_4x4` | Opacity | `—` | — |
| Playable_BatmobileJoker_SF | `Dusty_hit_01_4x4` | OpacityMask | `—` | — |
| Playable_BatmobileJoker_SF | `muzzleflash_straight_02` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `muzzleflash_straight_02` | Opacity | `—` | — |
| Playable_BatmobileJoker_SF | `muzzleflash_straight_02` | OpacityMask | `—` | — |
| Playable_BatmobileJoker_SF | `Smoke_02_SubUV_16_unlit` | DiffuseColor | `—` | — |
| Playable_BatmobileJoker_SF | `Smoke_02_SubUV_16_unlit` | EmissiveColor | `—` | — |
| Playable_BatmobileJoker_SF | `Smoke_02_SubUV_16_unlit` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Body_MASTER` | DiffuseColor | `Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` | `Batmobile_V2_Textures_NEW.NEW_Batmobile_V2_BODY_D` |
| Playable_BatmobileMK2_SF | `Batmobile_Body_MASTER` | SpecularColor | `Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Body_MASTER` | SpecularPower | `Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` | `Batmobile_V2_Textures_NEW.NEW_Batmobile_V2_BODY_S` |
| Playable_BatmobileMK2_SF | `Batmobile_Body_MASTER` | Normal | `Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` | `Batmobile_V2_Textures_NEW.NEW_Batmobile_V2_BODY_N` |
| Playable_BatmobileMK2_SF | `Batmobile_Body_MASTER` | EmissiveColor | `Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Glass` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Glass` | SpecularColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Glass` | SpecularPower | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Glass` | Normal | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Glass` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Glass` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Glass` | OpacityMask | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Glass` | MetalMask | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_MK2_WheelArch_MAT` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_MK2_WheelArch_MAT` | SpecularColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_MK2_WheelArch_MAT` | SpecularPower | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_MK2_WheelArch_MAT` | Normal | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_MK2_WheelArch_MAT` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_MK2_WheelArch_MAT` | MetalMask | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_MK2_WheelArch_MAT` | WorldPositionOffset | `Batmobile_MK2_WheelArch_MAT.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_TEXTURES_Body_Decals` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_TEXTURES_Body_Decals` | OpacityMask | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Undercarriage` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Undercarriage` | SpecularColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Undercarriage` | SpecularPower | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Undercarriage` | Normal | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Undercarriage` | OpacityMask | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Undercarriage` | MetalMask | `—` | — |
| Playable_BatmobileMK2_SF | `Cockpit_Master_Flip_Data` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `Cockpit_Master_Flip_Data` | SpecularColor | `—` | — |
| Playable_BatmobileMK2_SF | `Cockpit_Master_Flip_Data` | SpecularPower | `—` | — |
| Playable_BatmobileMK2_SF | `Cockpit_Master_Flip_Data` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Body_NoRain_MAT` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Body_NoRain_MAT` | SpecularColor | `Batmobile_V3_Body_NoRain_MAT.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Body_NoRain_MAT` | SpecularPower | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Body_NoRain_MAT` | Normal | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Body_NoRain_MAT` | EmissiveColor | `Batmobile_V3_Body_NoRain_MAT.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Body_NoRain_MAT` | MetalMask | `Batmobile_V3_Body_NoRain_MAT.MaterialExpressionScalarParameter` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Discbreak` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Discbreak` | SpecularColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Discbreak` | SpecularPower | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Discbreak` | Normal | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Discbreak` | EmissiveColor | `Batmobile_V3_Discbreak.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Discbreak` | OpacityMask | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Discbreak` | MetalMask | `Batmobile_V3_Discbreak.MaterialExpressionScalarParameter` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Tyre_V2_MAT` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Tyre_V2_MAT` | SpecularColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Tyre_V2_MAT` | SpecularPower | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Tyre_V2_MAT` | Normal | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Tyre_V2_MAT` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Tyre_V2_MAT` | MetalMask | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Wheel_V2_MAT` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Wheel_V2_MAT` | SpecularColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Wheel_V2_MAT` | SpecularPower | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Wheel_V2_MAT` | Normal | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_V3_Wheel_V2_MAT` | MetalMask | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Worn` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Worn` | SpecularColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Worn` | SpecularPower | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Worn` | Normal | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Worn` | EmissiveColor | `Batmobile_Worn.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Worn` | MetalMask | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Worn` | WorldPositionOffset | `Batmobile_Worn.MaterialExpressionStaticSwitchParameter` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Worn_NoRain` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Worn_NoRain` | SpecularColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Worn_NoRain` | SpecularPower | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Worn_NoRain` | Normal | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Worn_NoRain` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Worn_NoRain` | MetalMask | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Worn_NoRain` | WorldPositionOffset | `—` | — |
| Playable_BatmobileMK2_SF | `BatmobileV3_Rubber_Bullet` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `BatmobileV3_Rubber_Bullet` | SpecularColor | `—` | — |
| Playable_BatmobileMK2_SF | `BatmobileV3_Rubber_Bullet` | SpecularPower | `—` | — |
| Playable_BatmobileMK2_SF | `BatmobileV3_Rubber_Bullet` | Normal | `—` | — |
| Playable_BatmobileMK2_SF | `BatmobileV3_Rubber_Bullet` | MetalMask | `—` | — |
| Playable_BatmobileMK2_SF | `Back_Explosion_PP` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Back_Explosion_PP` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Takedown_Beam_M` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Takedown_Beam_M` | Normal | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Takedown_Beam_M` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Takedown_Beam_M` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Takedown_Beam_M` | WorldPositionOffset | `—` | — |
| Playable_BatmobileMK2_SF | `Stagg_Battery_Energy_01_MAT` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `Stagg_Battery_Energy_01_MAT` | SpecularColor | `—` | — |
| Playable_BatmobileMK2_SF | `Stagg_Battery_Energy_01_MAT` | SpecularPower | `—` | — |
| Playable_BatmobileMK2_SF | `Stagg_Battery_Energy_01_MAT` | Normal | `—` | — |
| Playable_BatmobileMK2_SF | `Stagg_Battery_Energy_01_MAT` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Stagg_Battery_Energy_01_MAT` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `Stagg_Battery_Energy_01_MAT` | WorldPositionOffset | `—` | — |
| Playable_BatmobileMK2_SF | `Stagg_Battery_01_MAT` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `Stagg_Battery_01_MAT` | SpecularColor | `—` | — |
| Playable_BatmobileMK2_SF | `Stagg_Battery_01_MAT` | SpecularPower | `—` | — |
| Playable_BatmobileMK2_SF | `Stagg_Battery_01_MAT` | Normal | `—` | — |
| Playable_BatmobileMK2_SF | `Stagg_Battery_01_MAT` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Stagg_Battery_01_MAT` | OpacityMask | `—` | — |
| Playable_BatmobileMK2_SF | `Burnout_Mat_MUD_NV` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `Burnout_Mat_MUD_NV` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Burnout_Mat_MUD_NV` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `Drone_Bomb_Radius` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Drone_Bomb_Radius` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Fire_Main` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Fire_Main` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Fire_Main` | Distortion | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Fire_Main` | WorldPositionOffset | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Seismic_Sonar` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Seismic_Sonar` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `Batmobile_Seismic_Sonar` | Distortion | `—` | — |
| Playable_BatmobileMK2_SF | `DroneHacker_Beam` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `DroneHacker_Beam` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `Missile_Line_2_Mat` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Missile_Line_2_Mat` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `Missile_Line_Mat` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Missile_Line_Mat` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `SeismicScan_Distortion` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `SeismicScan_Distortion` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `SeismicScan_Distortion` | Distortion | `—` | — |
| Playable_BatmobileMK2_SF | `Target_Sphere_COMBO_OPT` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `Target_Sphere_COMBO_OPT` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Target_Sphere_COMBO_OPT` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `Tyre_Smoke` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `Tyre_Smoke` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Tyre_Smoke` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `EMP_BuildUp` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `EMP_BuildUp` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `EMP_BuildUp` | Distortion | `—` | — |
| Playable_BatmobileMK2_SF | `SeismicSonar_Smoke` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `SeismicSonar_Smoke` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `SeismicSonar_Smoke` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `SeismicSonar_Smoke` | WorldPositionOffset | `—` | — |
| Playable_BatmobileMK2_SF | `ThickGas_Tyre` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `ThickGas_Tyre` | Normal | `—` | — |
| Playable_BatmobileMK2_SF | `ThickGas_Tyre` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `ThickGas_Tyre` | OpacityMask | `—` | — |
| Playable_BatmobileMK2_SF | `FearGas_Burnout` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `FearGas_Burnout` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `Gas_FollowDissolve` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `Gas_FollowDissolve` | SpecularColor | `—` | — |
| Playable_BatmobileMK2_SF | `Gas_FollowDissolve` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Gas_FollowDissolve` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `xrayBatmobile_MASTER` | Normal | `xrayBatmobile_MASTER.MaterialExpressionStaticSwitchParameter` | `Engine.WhiteSquareTexture` |
| Playable_BatmobileMK2_SF | `xrayBatmobile_MASTER` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `xrayBatmobile_MASTER` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `xrayBatmobile_MASTER` | OpacityMask | `—` | — |
| Playable_BatmobileMK2_SF | `Vehicle_Smoke_01` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `Vehicle_Smoke_01` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Vehicle_Smoke_01` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `fx_Winch_M_lit` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `fx_Winch_M_lit` | SpecularColor | `—` | — |
| Playable_BatmobileMK2_SF | `fx_Winch_M_lit` | SpecularPower | `—` | — |
| Playable_BatmobileMK2_SF | `fx_Winch_M_lit` | Normal | `—` | — |
| Playable_BatmobileMK2_SF | `fx_Winch_M_lit` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `fx_Winch_M_lit` | MetalMask | `—` | — |
| Playable_BatmobileMK2_SF | `Exp_Smoke_M` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `Exp_Smoke_M` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Exp_Smoke_M` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `Mat_tracerBeam_Dup` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Mat_tracerBeam_Dup` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `Fire_Proc_MAT` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Fire_Proc_MAT` | OpacityMask | `—` | — |
| Playable_BatmobileMK2_SF | `Beam_Mesh_M` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Beam_Mesh_M` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `Beam_Mesh_M` | WorldPositionOffset | `—` | — |
| Playable_BatmobileMK2_SF | `GPU_Spark_ConstantSize` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `GPU_Spark_ConstantSize` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `GPU_Spark_ConstantSize` | WorldPositionOffset | `—` | — |
| Playable_BatmobileMK2_SF | `Smoke_Dissolve` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `Smoke_Dissolve` | SpecularColor | `—` | — |
| Playable_BatmobileMK2_SF | `Smoke_Dissolve` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `Smoke_Dissolve` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `MAT_BitsOfShockwave` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `MAT_BitsOfShockwave` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `MAT_Digital_Noise` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `MAT_Digital_Noise` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `MAT_Mud_Tyre_Decal_V05` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `MAT_Mud_Tyre_Decal_V05` | SpecularColor | `—` | — |
| Playable_BatmobileMK2_SF | `MAT_Mud_Tyre_Decal_V05` | SpecularColor2 | `—` | — |
| Playable_BatmobileMK2_SF | `MAT_Mud_Tyre_Decal_V05` | SpecularPower | `—` | — |
| Playable_BatmobileMK2_SF | `MAT_Mud_Tyre_Decal_V05` | Normal | `—` | — |
| Playable_BatmobileMK2_SF | `MAT_Mud_Tyre_Decal_V05` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `MAT_Mud_Tyre_Decal_V05` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `MAT_Smoke_4x4_LIT` | DiffuseColor | `—` | — |
| Playable_BatmobileMK2_SF | `MAT_Smoke_4x4_LIT` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `MAT_Smoke_4x4_LIT` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `muzzleflash_straight_02` | EmissiveColor | `—` | — |
| Playable_BatmobileMK2_SF | `muzzleflash_straight_02` | Opacity | `—` | — |
| Playable_BatmobileMK2_SF | `muzzleflash_straight_02` | OpacityMask | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Body_MASTER` | DiffuseColor | `Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` | `Batmobile_V2_Textures_NEW.NEW_Batmobile_V2_BODY_D` |
| Playable_Batmobile_SF | `Batmobile_Body_MASTER` | SpecularColor | `Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` | — |
| Playable_Batmobile_SF | `Batmobile_Body_MASTER` | SpecularPower | `Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` | `Batmobile_V2_Textures_NEW.NEW_Batmobile_V2_BODY_S` |
| Playable_Batmobile_SF | `Batmobile_Body_MASTER` | Normal | `Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` | `Batmobile_V2_Textures_NEW.NEW_Batmobile_V2_BODY_N` |
| Playable_Batmobile_SF | `Batmobile_Body_MASTER` | EmissiveColor | `Batmobile_Body_MASTER.MaterialExpressionStaticSwitchParameter` | — |
| Playable_Batmobile_SF | `Batmobile_Glass` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Glass` | SpecularColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Glass` | SpecularPower | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Glass` | Normal | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Glass` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Glass` | Opacity | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Glass` | OpacityMask | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Glass` | MetalMask | `—` | — |
| Playable_Batmobile_SF | `Stagg_Battery_01_MAT` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `Stagg_Battery_01_MAT` | SpecularColor | `—` | — |
| Playable_Batmobile_SF | `Stagg_Battery_01_MAT` | SpecularPower | `—` | — |
| Playable_Batmobile_SF | `Stagg_Battery_01_MAT` | Normal | `—` | — |
| Playable_Batmobile_SF | `Stagg_Battery_01_MAT` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `Stagg_Battery_01_MAT` | OpacityMask | `—` | — |
| Playable_Batmobile_SF | `Stagg_Battery_Energy_01_MAT` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `Stagg_Battery_Energy_01_MAT` | SpecularColor | `—` | — |
| Playable_Batmobile_SF | `Stagg_Battery_Energy_01_MAT` | SpecularPower | `—` | — |
| Playable_Batmobile_SF | `Stagg_Battery_Energy_01_MAT` | Normal | `—` | — |
| Playable_Batmobile_SF | `Stagg_Battery_Energy_01_MAT` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `Stagg_Battery_Energy_01_MAT` | Opacity | `—` | — |
| Playable_Batmobile_SF | `Stagg_Battery_Energy_01_MAT` | WorldPositionOffset | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_TEXTURES_Body_Decals` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_TEXTURES_Body_Decals` | OpacityMask | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Undercarriage` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Undercarriage` | SpecularColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Undercarriage` | SpecularPower | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Undercarriage` | Normal | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Undercarriage` | OpacityMask | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Undercarriage` | MetalMask | `—` | — |
| Playable_Batmobile_SF | `Cockpit_Master_Flip_Data` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `Cockpit_Master_Flip_Data` | SpecularColor | `—` | — |
| Playable_Batmobile_SF | `Cockpit_Master_Flip_Data` | SpecularPower | `—` | — |
| Playable_Batmobile_SF | `Cockpit_Master_Flip_Data` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Body_NoRain_MAT` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Body_NoRain_MAT` | SpecularColor | `Batmobile_V3_Body_NoRain_MAT.MaterialExpressionStaticSwitchParameter` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Body_NoRain_MAT` | SpecularPower | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Body_NoRain_MAT` | Normal | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Body_NoRain_MAT` | EmissiveColor | `Batmobile_V3_Body_NoRain_MAT.MaterialExpressionStaticSwitchParameter` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Body_NoRain_MAT` | MetalMask | `Batmobile_V3_Body_NoRain_MAT.MaterialExpressionScalarParameter` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Discbreak` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Discbreak` | SpecularColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Discbreak` | SpecularPower | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Discbreak` | Normal | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Discbreak` | EmissiveColor | `Batmobile_V3_Discbreak.MaterialExpressionStaticSwitchParameter` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Discbreak` | OpacityMask | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Discbreak` | MetalMask | `Batmobile_V3_Discbreak.MaterialExpressionScalarParameter` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Tyre_V2_MAT` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Tyre_V2_MAT` | SpecularColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Tyre_V2_MAT` | SpecularPower | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Tyre_V2_MAT` | Normal | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Tyre_V2_MAT` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Tyre_V2_MAT` | MetalMask | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Wheel_V2_MAT` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Wheel_V2_MAT` | SpecularColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Wheel_V2_MAT` | SpecularPower | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Wheel_V2_MAT` | Normal | `—` | — |
| Playable_Batmobile_SF | `Batmobile_V3_Wheel_V2_MAT` | MetalMask | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Worn` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Worn` | SpecularColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Worn` | SpecularPower | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Worn` | Normal | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Worn` | EmissiveColor | `Batmobile_Worn.MaterialExpressionStaticSwitchParameter` | — |
| Playable_Batmobile_SF | `Batmobile_Worn` | MetalMask | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Worn` | WorldPositionOffset | `Batmobile_Worn.MaterialExpressionStaticSwitchParameter` | — |
| Playable_Batmobile_SF | `Batmobile_Worn_NoRain` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Worn_NoRain` | SpecularColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Worn_NoRain` | SpecularPower | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Worn_NoRain` | Normal | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Worn_NoRain` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Worn_NoRain` | MetalMask | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Worn_NoRain` | WorldPositionOffset | `—` | — |
| Playable_Batmobile_SF | `BatmobileV3_Rubber_Bullet` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `BatmobileV3_Rubber_Bullet` | SpecularColor | `—` | — |
| Playable_Batmobile_SF | `BatmobileV3_Rubber_Bullet` | SpecularPower | `—` | — |
| Playable_Batmobile_SF | `BatmobileV3_Rubber_Bullet` | Normal | `—` | — |
| Playable_Batmobile_SF | `BatmobileV3_Rubber_Bullet` | MetalMask | `—` | — |
| Playable_Batmobile_SF | `Back_Explosion_PP` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `Back_Explosion_PP` | Opacity | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Takedown_Beam_M` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Takedown_Beam_M` | Normal | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Takedown_Beam_M` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Takedown_Beam_M` | Opacity | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Takedown_Beam_M` | WorldPositionOffset | `—` | — |
| Playable_Batmobile_SF | `Burnout_Mat_MUD_NV` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `Burnout_Mat_MUD_NV` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `Burnout_Mat_MUD_NV` | Opacity | `—` | — |
| Playable_Batmobile_SF | `Drone_Bomb_Radius` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `Drone_Bomb_Radius` | Opacity | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Fire_Main` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Fire_Main` | Opacity | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Fire_Main` | Distortion | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Fire_Main` | WorldPositionOffset | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Seismic_Sonar` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Seismic_Sonar` | Opacity | `—` | — |
| Playable_Batmobile_SF | `Batmobile_Seismic_Sonar` | Distortion | `—` | — |
| Playable_Batmobile_SF | `DroneHacker_Beam` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `DroneHacker_Beam` | Opacity | `—` | — |
| Playable_Batmobile_SF | `Missile_Line_2_Mat` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `Missile_Line_2_Mat` | Opacity | `—` | — |
| Playable_Batmobile_SF | `Missile_Line_Mat` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `Missile_Line_Mat` | Opacity | `—` | — |
| Playable_Batmobile_SF | `SeismicScan_Distortion` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `SeismicScan_Distortion` | Opacity | `—` | — |
| Playable_Batmobile_SF | `SeismicScan_Distortion` | Distortion | `—` | — |
| Playable_Batmobile_SF | `Target_Sphere_COMBO_OPT` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `Target_Sphere_COMBO_OPT` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `Target_Sphere_COMBO_OPT` | Opacity | `—` | — |
| Playable_Batmobile_SF | `Tyre_Smoke` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `Tyre_Smoke` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `Tyre_Smoke` | Opacity | `—` | — |
| Playable_Batmobile_SF | `EMP_BuildUp` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `EMP_BuildUp` | Opacity | `—` | — |
| Playable_Batmobile_SF | `EMP_BuildUp` | Distortion | `—` | — |
| Playable_Batmobile_SF | `SeismicSonar_Smoke` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `SeismicSonar_Smoke` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `SeismicSonar_Smoke` | Opacity | `—` | — |
| Playable_Batmobile_SF | `SeismicSonar_Smoke` | WorldPositionOffset | `—` | — |
| Playable_Batmobile_SF | `ThickGas_Tyre` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `ThickGas_Tyre` | Normal | `—` | — |
| Playable_Batmobile_SF | `ThickGas_Tyre` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `ThickGas_Tyre` | OpacityMask | `—` | — |
| Playable_Batmobile_SF | `FearGas_Burnout` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `FearGas_Burnout` | Opacity | `—` | — |
| Playable_Batmobile_SF | `Gas_FollowDissolve` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `Gas_FollowDissolve` | SpecularColor | `—` | — |
| Playable_Batmobile_SF | `Gas_FollowDissolve` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `Gas_FollowDissolve` | Opacity | `—` | — |
| Playable_Batmobile_SF | `xrayBatmobile_MASTER` | Normal | `xrayBatmobile_MASTER.MaterialExpressionStaticSwitchParameter` | `Engine.WhiteSquareTexture` |
| Playable_Batmobile_SF | `xrayBatmobile_MASTER` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `xrayBatmobile_MASTER` | Opacity | `—` | — |
| Playable_Batmobile_SF | `xrayBatmobile_MASTER` | OpacityMask | `—` | — |
| Playable_Batmobile_SF | `Vehicle_Smoke_01` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `Vehicle_Smoke_01` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `Vehicle_Smoke_01` | Opacity | `—` | — |
| Playable_Batmobile_SF | `fx_Winch_M_lit` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `fx_Winch_M_lit` | SpecularColor | `—` | — |
| Playable_Batmobile_SF | `fx_Winch_M_lit` | SpecularPower | `—` | — |
| Playable_Batmobile_SF | `fx_Winch_M_lit` | Normal | `—` | — |
| Playable_Batmobile_SF | `fx_Winch_M_lit` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `fx_Winch_M_lit` | MetalMask | `—` | — |
| Playable_Batmobile_SF | `Exp_Smoke_M` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `Exp_Smoke_M` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `Exp_Smoke_M` | Opacity | `—` | — |
| Playable_Batmobile_SF | `Mat_tracerBeam_Dup` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `Mat_tracerBeam_Dup` | Opacity | `—` | — |
| Playable_Batmobile_SF | `Fire_Proc_MAT` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `Fire_Proc_MAT` | OpacityMask | `—` | — |
| Playable_Batmobile_SF | `Beam_Mesh_M` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `Beam_Mesh_M` | Opacity | `—` | — |
| Playable_Batmobile_SF | `Beam_Mesh_M` | WorldPositionOffset | `—` | — |
| Playable_Batmobile_SF | `GPU_Spark_ConstantSize` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `GPU_Spark_ConstantSize` | Opacity | `—` | — |
| Playable_Batmobile_SF | `GPU_Spark_ConstantSize` | WorldPositionOffset | `—` | — |
| Playable_Batmobile_SF | `Smoke_Dissolve` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `Smoke_Dissolve` | SpecularColor | `—` | — |
| Playable_Batmobile_SF | `Smoke_Dissolve` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `Smoke_Dissolve` | Opacity | `—` | — |
| Playable_Batmobile_SF | `MAT_BitsOfShockwave` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `MAT_BitsOfShockwave` | Opacity | `—` | — |
| Playable_Batmobile_SF | `MAT_Digital_Noise` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `MAT_Digital_Noise` | Opacity | `—` | — |
| Playable_Batmobile_SF | `MAT_Mud_Tyre_Decal_V05` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `MAT_Mud_Tyre_Decal_V05` | SpecularColor | `—` | — |
| Playable_Batmobile_SF | `MAT_Mud_Tyre_Decal_V05` | SpecularColor2 | `—` | — |
| Playable_Batmobile_SF | `MAT_Mud_Tyre_Decal_V05` | SpecularPower | `—` | — |
| Playable_Batmobile_SF | `MAT_Mud_Tyre_Decal_V05` | Normal | `—` | — |
| Playable_Batmobile_SF | `MAT_Mud_Tyre_Decal_V05` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `MAT_Mud_Tyre_Decal_V05` | Opacity | `—` | — |
| Playable_Batmobile_SF | `MAT_Smoke_4x4_LIT` | DiffuseColor | `—` | — |
| Playable_Batmobile_SF | `MAT_Smoke_4x4_LIT` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `MAT_Smoke_4x4_LIT` | Opacity | `—` | — |
| Playable_Batmobile_SF | `muzzleflash_straight_02` | EmissiveColor | `—` | — |
| Playable_Batmobile_SF | `muzzleflash_straight_02` | Opacity | `—` | — |
| Playable_Batmobile_SF | `muzzleflash_straight_02` | OpacityMask | `—` | — |
| Playable_Batmobile_Std_6_SF | `Batmobile_Stage6` | DiffuseColor | `—` | — |
| Playable_Batmobile_Std_6_SF | `Batmobile_Stage6` | SpecularColor | `—` | — |
| Playable_Batmobile_Std_6_SF | `Batmobile_Stage6` | SpecularPower | `—` | — |
| Playable_Batmobile_Std_6_SF | `Batmobile_Stage6` | Normal | `—` | — |
| Playable_Batmobile_Std_6_SF | `Batmobile_Stage6` | EmissiveColor | `Batmobile_Stage6.MaterialExpressionStaticSwitchParameter` | `Engine.Batmobile_Micropattern_A`; `Textures.Batmobile_TEXTURES_FearSand_N` |
| Playable_Batmobile_Std_6_SF | `Batmobile_Stage6` | MetalMask | `—` | — |
| Playable_Batmobile_Std_6_SF | `Batmobile_Stage6` | WorldPositionOffset | `Batmobile_Stage6.MaterialExpressionStaticSwitchParameter` | — |

## Material instances

| package | instance | parent | scalars | vectors | textures |
|---|---|---|---|---|---|
| Playable_BatmobileFunhouse_SF | Batmobile_Interior_INST | `Engine.Metal` | — | — | Diffuse→`Batmobile_V2_Textures_NEW.Batmobile_V2_INTERIOR_D`, Normal→`Batmobile_V2_Textures_NEW.Batmobile_V2_INTERIOR_N`, Reflectivity\|Roughness→`Batmobile_V2_Textures_NEW.Batmobile_V2_INTERIOR_S` |
| Playable_BatmobileFunhouse_SF | MIC1 | `—` | — | — | — |
| Playable_BatmobileFunhouse_SF | Batmobile_Jokerfied_Hair_MAT_MIC | `Material_MASTERS.Batmobile_Jokerfied_Hair_MAT` | Emissive=0.5000, Fake Aniso Brightness=3.0000, Metalisity_Multiplier=0.9000, Opacity_Multiplier=1.2000, Reflectivity=0.2000, Reflectivity_Multiplier=4.0000, Roughness_Multiplier=1.5000 | — | Color/Reflectivity_Roughness_Transp→`Maps_v2.Joker_BM3_V2_Head_Hair_R`, Colour Texture→`Engine.Joker_BM3_V2_Head_Hair_D`, Normal_Map→`Engine.Joker_BM3_V2_Head_Hair_N` |
| Playable_BatmobileFunhouse_SF | Batmobile_Jokerfied_MainBody | `Material_MASTERS.Batmobile_Jokerfied_V2_MAT` | Damage_dirt=1.0000, Joker_Damage_Scratches_All_Over=0.4000, Paint_Strength=3.0000 | — | Damage_Chapter_Mask→`Texture.Batmobile_Jokerfied_Body_Damage_ChapterMask`, Diffuse→`Texture.Batmobile_Jokerfied_Body_D`, Normal→`Textures.Batmobile_V3_Body_N` |
| Playable_BatmobileFunhouse_SF | Batmobile_Jokerfied_WheelArch_MIC | `Material_MASTERS.Batmobile_Jokerfied_V2_MAT` | Damage_dirt=1.0000, Joker_Damage_Scratches_All_Over=0.4000, Paint_Strength=3.0000 | — | Damage_Chapter_Mask→`Texture.Batmobile_jokerfied_WheelArch_Damage_ChapterMask`, Diffuse→`Texture.Batmobile_Jokerfied_WheelArch_D`, Metalicity_Roughness_Reflectivity→`Textures.Batmobile_MK2_WheelArch2_R`, Normal→`Textures.Batmobile_V3_WheelArch_N` |
| Playable_BatmobileFunhouse_SF | Batmobile_V3_Tyre_test_INST | `Material_MASTERS.Batmobile_V3_Tyre_V2_MAT` | colour_ramp_intensity=0.1000, Diffuse_Adjust=1.0000, EMP=0.0000, EMP_Emissive_Multiplier=650.0000, Mud_Density=0.5000, Reflectivity_Multiplier=0.2000, Roughness_Multiplier=0.8000 | — | Diffuse_Map→`Texture.Batmobile_Jokerfied_Tyre_V2_D`, Normal_Map→`jongee_test.Batmobile_V3_TEXTURES_Tyre_V2_N`, Ref_n_Rough_Map→`jongee_test.Batmobile_V3_TEXTURES_Tyre_V2_R` |
| Playable_BatmobileFunhouse_SF | wheel_V2_test_INST | `Material_Worn.BatmobileV3_Wheel_V2_MIC` | Damage_dirt=0.2000, Metalicity_Multiplier=0.8000, Reflectivity_Multiplier=1.0000, Roughness_Multiplier=0.3500 | — | Diffuse→`Texture.Batmobile_Jokerfied_Wheel_V2_D` |
| Playable_BatmobileFunhouse_SF | Batmobile_V3_Cockpit_MIC | `Material_MASTERS.Batmobile_V3_Body_NoRain_MAT` | BaseMaterial_Microdetail_Size=45.0000, Fake Aniso Brightness 1=2.0000, Fake Aniso Brightness 2=0.1000, fake aniso orientation=1.0000, fake aniso uv magnitude=1.0000, fake aniso uv shift=0.0000, Material1_Microdetail_Size=120.0000, Material2_Microdetail_Size=30.0000, Material3_Microdetail_Size=30.0000, Metalicity=0.9000, Reflectivity_BaseMaterial2_Multiplier=5.0000, Reflectivity_Material3=1.0000 | — | Anisotropic Ramp→`Engine.Aniso_ramp_Lacquered`, Colour_Ramp_Map→`Engine.Batman_BM3_V2_Lacquered_Underlayer_Ramp`, Material1_Microdetail_N→`Engine.neutral_normal`, Material2_Microdetail→`Engine.Batmobile_Micropattern_C`, Material2_Microdetail_N→`Engine.neutral_normal`, Material3_Microdetail→`Engine.Batmobile_Micropattern_C`, Material3_Microdetail_N→`Engine.neutral_normal`, Material_Separation_Mask→`Textures.Batmobile_V3_Int_Cockpit_M`, Normal_Map→`Textures.Batmobile_V3_Int_Cockpit_N` |
| Playable_BatmobileFunhouse_SF | Batmobile_V3_Discbreak_MIC | `Material_MASTERS.Batmobile_V3_Discbreak` | Emissive_Intensity=1.5000, Fake Aniso Brightness 1=0.0000, Fake Aniso Brightness 2=0.0000, fake aniso orientation=0.0000, fake aniso uv magnitude=1.0000, Metalicity_Multiplier=0.8000, Mud2_Opacity=1.0000, Mud_Edges_Opacity=0.2000, Mud_Opacity=0.0000, Mud_WetStreaks=1.2000, Reflectivity_Multiplier=1.0000 | — | Anisotropic Ramp→`Engine.Aniso_ramp_Lacquered`, Colour_Map→`Textures.Batmobile_V3_BRAKE_DISC_D`, Colour_Ramp_Map→`Engine.Batman_BM3_V2_Lacquered_Underlayer_Ramp`, Normal_Map→`Textures.Batmobile_V3_BRAKE_DISC_N`, Ref_n_Rough_Map→`Textures.Batmobile_V3_BRAKE_DISC_R` |
| Playable_BatmobileFunhouse_SF | Batmobile_V3_Emissive | `Engine.Batmobile_V3_Body_MAT` | Fake Aniso Brightness 1=0.5000, Fake Aniso Brightness 2=0.1000, fake aniso orientation=1.0000, fake aniso uv magnitude=1.0000, fake aniso uv shift=0.0000, Material1_Microdetail_Size=250.0000, Material2_Microdetail_Size=30.0000, Material3_Microdetail_Size=30.0000, Metalicity=0.9200, Rain_Constant=1.0000, Reflectivity_Multiplier=1.0000 | — | Anisotropic Ramp→`Engine.Aniso_ramp_Lacquered`, BaseMaterial_Microdetail→`Engine.Batmobile_Micropattern_B`, Colour_Ramp_Map→`Engine.Batmobile_V3_Body_ColourRamp`, Emissive_Map→`Engine.Batmobile_V3_Wheel_E`, Material1_Microdetail→`Engine.Batmobile_Micropattern_A`, Material1_Microdetail_N→`Engine.Batmobile_Micropattern_A_Normal`, Material2_Microdetail→`Engine.Batmobile_Micropattern_C`, Material2_Microdetail_N→`Engine.neutral_normal`, Material3_Microdetail→`Engine.Batmobile_Micropattern_C`, Material3_Microdetail_N→`Engine.neutral_normal`, Material_Separation_Mask→`Textures.Batmobile_V3_Wheel_Lights_M`, Normal_Map→`Textures.Batmobile_V3_Wheel_Lights_N` |
| Playable_BatmobileFunhouse_SF | Batmobile_V3_Glass_INST | `Batmobile_V2_Textures_NEW.Batmobile_Glass` | Glass_Opacity=1.2000, Glass_Reflectivity=0.8000, Glass_Roughness=1.1000, glass_smudges=0.2000 | — | Mask (R=Reflect / G=Rough / B=Normal map compression artifacts fix)→`Textures.Batmobile_V3_Glass_S`, Normal→`Textures.Batmobile_V3_Glass_N`, OpacityMap→`Textures.Batmobile_V3_Glass_A` |
| Playable_BatmobileFunhouse_SF | BatmobileV3_Cockpit_Seat | `Engine.Batmobile_Hardleather_Master_MAT` | EmissiveMultiply=15.0000, Fake Aniso Brightness 1=0.0100, Fake Aniso Brightness 2=1.0000, fake aniso orientation=1.0000, fake aniso uv magnitude=1.0000, fake aniso uv shift=0.0000, Reflectivity_Multiplier=1.2000 | — | Colour_Map→`Textures.Batmobile_V3_Int_Cockpit_D`, Colour_Ramp_Map→`Maps.Batman_BM3_V2_Leather_Ramp`, Emissive→`Textures.Batmobile_V3_Int_Cockpit_E`, Normal_Map_Lacquer→`Textures.Batmobile_V3_Int_Cockpit_N`, Ref_n_Rough_Map→`Textures.Batmobile_V3_Int_Cockpit_S` |
| Playable_BatmobileFunhouse_SF | Batmobile_V3_Turret_Jokerfied_MIC | `Material_MASTERS.Batmobile_Jokerfied_V2_MAT` | Damage_dirt=0.3000, Damage_Dirt2_Opacity=0.6500, Damage_Dirt_Edges=2.0000, Grubby_Multiplier=1.2300, Joker_Damage_Scratches_All_Over=0.4000, Material2_Reflectivity=1.0000, MicroDetail_size=20.0000 | — | Damage_Chapter_Mask→`Textures.Batmobile_V3_TEXTURES_Weaponry_Damage_ChapterMask`, Diffuse→`jongee_test.Batmobile_V3_Weaponry_Turret_V2_D`, Material_Microdetail→`Textures.Batmobile_Microdetail`, Normal→`Textures.Batmobile_V3_Weaponry_Turret_V2_N` |
| Playable_BatmobileFunhouse_SF | Batmobile_V3_Undercarriage_NEW_MIC | `Material_Worn.Batmobile_V3_WheelArchs_NEW_MIC` | Damage_dirt=0.5000, Damage_Dirt_Edges=3.0000, Material1_Reflectivity=0.4000, Material1_Roughness=0.1000 | — | Damage_Chapter_Mask→`Textures.Batmobile_V3_Undercarriage_Damage_ChapterMask`, Normal_Map→`Textures.Batmobile_V3_Undercarriage_N` |
| Playable_BatmobileFunhouse_SF | Batmobile_V3_WheelArchs_NEW_MIC | `Material_MASTERS.Batmobile_Worn` | Damage_dirt=0.5000, Damage_Dirt2_Opacity=2.0000, Damage_Dirt_Edges=1.5000, EdgeMask_Metalicity=2.0000, Material0_Reflectivity=0.1500, Material0_Roughness=0.4000, Material1_Reflectivity=0.2000, Material1_Roughness=0.2500, Material2_Metalicity=1.0000, Material2_Reflectivity=0.9000, Material2_Roughness=0.1500, Material3_Reflectivity=0.5000 | — | Anisotropic Ramp→`Engine.Aniso_ramp_Lacquered`, Colour_Ramp_Map→`Engine.Batman_BM3_V2_Lacquered_Underlayer_Ramp`, Damage_Chapter_Mask→`Textures.Batmobile_V3_TEXTURES_WheelArch_Damage_ChapterMask`, Material3_Microdetail_N→`Engine.Batmobile_Micropattern_A_Normal`, Material_Microdetail→`Textures.Batmobile_Microdetail`, Normal_Map→`Textures.Batmobile_V3_WheelArch_N` |
| Playable_BatmobileFunhouse_SF | BatmobileV3_Wheel_V2_MIC | `Material_MASTERS.Batmobile_V3_Wheel_V2_MAT` | Metalicity_Multiplier=0.8000, Mud2_Opacity=2.0000, Mud_Edges_Opacity=0.5000, Mud_Opacity=1.0000, Mud_WetStreaks=1.0000, Reflectivity_Multiplier=1.0000, Roughness_Multiplier=0.2500 | — | — |
| Playable_BatmobileFunhouse_SF | BatmobileV3_Upgrades_MAT_INST | `Engine.Gadgets_Master_MAT` | Reflectivity_Multiplier=1.2000 | — | Colour_Map→`BatmobileV3_Upgrades.Batmobile_V3_Missile_Upgrade_D`, Normal_Map_Lacquer→`BatmobileV3_Upgrades.Batmobile_V3_Missile_Upgrade_N`, Ref_n_Rough_Map→`BatmobileV3_Upgrades.Batmobile_V3_Missile_Upgrade_S` |
| Playable_BatmobileFunhouse_SF | Batmobile_V3_Wheel_EMP_MAT_INST | `Material_MASTERS.Batmobile_V3_Wheel_V2_MAT` | — | — | Diffuse→`Material_MASTERS.Batmobile_V3_Winch_EMP_D` |
| Playable_BatmobileFunhouse_SF | Outro_Explosion_INST | `Shaders.Back_Explosion_PP` | — | — | — |
| Playable_BatmobileFunhouse_SF | Batmobile_Fire_Main_INST | `Materials.Batmobile_Fire_Main` | Blackbody_Desat=0.0000, Brightness=15.0000, Distortion=2.0000, Ember_Amount=0.7000, Hardness=0.9500, Mask_Power=2.5000, Radius=1.0000, RandomP=0.5000, Smoke_Strength=2.0000, Speed=2.0000, Spread=0.3000, Tile_Speed=1.8000 | — | — |
| Playable_BatmobileFunhouse_SF | DroneHacker_Beam_INST | `Materials.DroneHacker_Beam` | Green=1.0025 | — | — |
| Playable_BatmobileFunhouse_SF | EMP_Burst_V02_Stage_01 | `Engine.EMP_Burst_V02_MAT` | — | — | — |
| Playable_BatmobileFunhouse_SF | EMP_Burst_V02_Stage_02 | `Engine.EMP_Burst_V02_MAT` | — | — | — |
| Playable_BatmobileFunhouse_SF | EMP_Burst_V02_Stage_03 | `Engine.EMP_Burst_V02_MAT` | — | — | — |
| Playable_BatmobileFunhouse_SF | EMP_Burst_V02_Stage_04 | `Engine.EMP_Burst_V02_MAT` | — | — | — |
| Playable_BatmobileFunhouse_SF | ThickGas_Tyre_1_INST | `Materials.ThickGas_Tyre` | — | — | — |
| Playable_BatmobileFunhouse_SF | xrayMetal_Batmobile_INST | `Xray.xrayBatmobile_MASTER` | — | — | — |
| Playable_BatmobileFunhouse_SF | fx_Winch_M_lit_INST | `VFX_Generic.fx_Winch_M_lit` | Electricity=0.0000 | — | — |
| Playable_BatmobileFunhouse_SF | INST_Digital_Noise_BLUE | `Other.MAT_Digital_Noise` | Electricity_Brightness=20.0000, DBA_Alpha=50.0000, Distortion_Strength=2.0000, Distortion_Tiling=1.0000, Falloff=1.0000 | — | — |
| Playable_BatmobileFunhouse_SF | INST_Digital_Noise_V02 | `Other.MAT_Digital_Noise` | Electricity_Brightness=20.0000, DBA_Alpha=50.0000, Distortion_Strength=2.0000, Distortion_Tiling=1.0000, Falloff=1.0000 | — | — |
| Playable_BatmobileFunhouse_SF | INST_New_Electric_Arc_BLUE_THIN | `Engine.MAT_New_Electric_Arc` | Radius A=1.0000, Radius B=1.5000 | — | — |
| Playable_BatmobileFunhouse_SF | MAT_BitsOfShockwave_INST | `Other.MAT_BitsOfShockwave` | Brightness=15.0000 | — | — |
| Playable_BatmobileFunhouse_SF | MAT_Flat_Shockwave_INST | `Engine.MAT_Flat_Shockwave` | Brightness=10.0000 | — | — |
| Playable_BatmobileFunhouse_SF | MAT_Flat_Shockwave_INST_BLUE | `Engine.MAT_Flat_Shockwave` | Brightness=10.0000 | — | — |
| Playable_BatmobileFunhouse_SF | MAT_Mud_Splash_1x1_V02_INST | `Engine.MAT_Mud_Splash_1x1_V02` | — | — | — |
| Playable_BatmobileJoker_SF | Batmobile_Interior_INST | `Engine.Metal` | — | — | Diffuse→`Batmobile_V2_Textures_NEW.Batmobile_V2_INTERIOR_D`, Normal→`Batmobile_V2_Textures_NEW.Batmobile_V2_INTERIOR_N`, Reflectivity\|Roughness→`Batmobile_V2_Textures_NEW.Batmobile_V2_INTERIOR_S` |
| Playable_BatmobileJoker_SF | MIC1 | `—` | — | — | — |
| Playable_BatmobileJoker_SF | Batmobile_Jokerfied_Hair_MAT_MIC | `Material_MASTERS.Batmobile_Jokerfied_Hair_MAT` | Emissive=0.5000, Fake Aniso Brightness=3.0000, Metalisity_Multiplier=0.9000, Opacity_Multiplier=1.2000, Reflectivity=0.2000, Reflectivity_Multiplier=4.0000, Roughness_Multiplier=1.5000 | — | Color/Reflectivity_Roughness_Transp→`Maps_v2.Joker_BM3_V2_Head_Hair_R`, Colour Texture→`Engine.Joker_BM3_V2_Head_Hair_D`, Normal_Map→`Engine.Joker_BM3_V2_Head_Hair_N` |
| Playable_BatmobileJoker_SF | Batmobile_Jokerfied_MainBody | `Material_MASTERS.Batmobile_Jokerfied_V2_MAT` | Damage_dirt=1.0000, Joker_Damage_Scratches_All_Over=0.4000, Paint_Strength=3.0000 | — | Damage_Chapter_Mask→`Texture.Batmobile_Jokerfied_Body_Damage_ChapterMask`, Diffuse→`Texture.Batmobile_Jokerfied_Body_D`, Normal→`Textures.Batmobile_V3_Body_N` |
| Playable_BatmobileJoker_SF | Batmobile_Jokerfied_WheelArch_MIC | `Material_MASTERS.Batmobile_Jokerfied_V2_MAT` | Damage_dirt=1.0000, Joker_Damage_Scratches_All_Over=0.4000, Paint_Strength=3.0000 | — | Damage_Chapter_Mask→`Texture.Batmobile_jokerfied_WheelArch_Damage_ChapterMask`, Diffuse→`Texture.Batmobile_Jokerfied_WheelArch_D`, Metalicity_Roughness_Reflectivity→`Textures.Batmobile_MK2_WheelArch2_R`, Normal→`Textures.Batmobile_V3_WheelArch_N` |
| Playable_BatmobileJoker_SF | Batmobile_V3_Tyre_test_INST | `Material_MASTERS.Batmobile_V3_Tyre_V2_MAT` | colour_ramp_intensity=0.1000, Diffuse_Adjust=1.0000, EMP=0.0000, EMP_Emissive_Multiplier=650.0000, Mud_Density=0.5000, Reflectivity_Multiplier=0.2000, Roughness_Multiplier=0.8000 | — | Diffuse_Map→`Texture.Batmobile_Jokerfied_Tyre_V2_D`, Normal_Map→`jongee_test.Batmobile_V3_TEXTURES_Tyre_V2_N`, Ref_n_Rough_Map→`jongee_test.Batmobile_V3_TEXTURES_Tyre_V2_R` |
| Playable_BatmobileJoker_SF | wheel_V2_test_INST | `Material_Worn.BatmobileV3_Wheel_V2_MIC` | Damage_dirt=0.2000, Metalicity_Multiplier=0.8000, Reflectivity_Multiplier=1.0000, Roughness_Multiplier=0.3500 | — | Diffuse→`Texture.Batmobile_Jokerfied_Wheel_V2_D` |
| Playable_BatmobileJoker_SF | Batmobile_V3_Cockpit_MIC | `Material_MASTERS.Batmobile_V3_Body_NoRain_MAT` | BaseMaterial_Microdetail_Size=45.0000, Fake Aniso Brightness 1=2.0000, Fake Aniso Brightness 2=0.1000, fake aniso orientation=1.0000, fake aniso uv magnitude=1.0000, fake aniso uv shift=0.0000, Material1_Microdetail_Size=120.0000, Material2_Microdetail_Size=30.0000, Material3_Microdetail_Size=30.0000, Metalicity=0.9000, Reflectivity_BaseMaterial2_Multiplier=5.0000, Reflectivity_Material3=1.0000 | — | Anisotropic Ramp→`Engine.Aniso_ramp_Lacquered`, Colour_Ramp_Map→`Engine.Batman_BM3_V2_Lacquered_Underlayer_Ramp`, Material1_Microdetail_N→`Engine.neutral_normal`, Material2_Microdetail→`Engine.Batmobile_Micropattern_C`, Material2_Microdetail_N→`Engine.neutral_normal`, Material3_Microdetail→`Engine.Batmobile_Micropattern_C`, Material3_Microdetail_N→`Engine.neutral_normal`, Material_Separation_Mask→`Textures.Batmobile_V3_Int_Cockpit_M`, Normal_Map→`Textures.Batmobile_V3_Int_Cockpit_N` |
| Playable_BatmobileJoker_SF | Batmobile_V3_Discbreak_MIC | `Material_MASTERS.Batmobile_V3_Discbreak` | Emissive_Intensity=1.5000, Fake Aniso Brightness 1=0.0000, Fake Aniso Brightness 2=0.0000, fake aniso orientation=0.0000, fake aniso uv magnitude=1.0000, Metalicity_Multiplier=0.8000, Mud2_Opacity=1.0000, Mud_Edges_Opacity=0.2000, Mud_Opacity=0.0000, Mud_WetStreaks=1.2000, Reflectivity_Multiplier=1.0000 | — | Anisotropic Ramp→`Engine.Aniso_ramp_Lacquered`, Colour_Map→`Textures.Batmobile_V3_BRAKE_DISC_D`, Colour_Ramp_Map→`Engine.Batman_BM3_V2_Lacquered_Underlayer_Ramp`, Normal_Map→`Textures.Batmobile_V3_BRAKE_DISC_N`, Ref_n_Rough_Map→`Textures.Batmobile_V3_BRAKE_DISC_R` |
| Playable_BatmobileJoker_SF | Batmobile_V3_Emissive | `Engine.Batmobile_V3_Body_MAT` | Fake Aniso Brightness 1=0.5000, Fake Aniso Brightness 2=0.1000, fake aniso orientation=1.0000, fake aniso uv magnitude=1.0000, fake aniso uv shift=0.0000, Material1_Microdetail_Size=250.0000, Material2_Microdetail_Size=30.0000, Material3_Microdetail_Size=30.0000, Metalicity=0.9200, Rain_Constant=1.0000, Reflectivity_Multiplier=1.0000 | — | Anisotropic Ramp→`Engine.Aniso_ramp_Lacquered`, BaseMaterial_Microdetail→`Engine.Batmobile_Micropattern_B`, Colour_Ramp_Map→`Engine.Batmobile_V3_Body_ColourRamp`, Emissive_Map→`Engine.Batmobile_V3_Wheel_E`, Material1_Microdetail→`Engine.Batmobile_Micropattern_A`, Material1_Microdetail_N→`Engine.Batmobile_Micropattern_A_Normal`, Material2_Microdetail→`Engine.Batmobile_Micropattern_C`, Material2_Microdetail_N→`Engine.neutral_normal`, Material3_Microdetail→`Engine.Batmobile_Micropattern_C`, Material3_Microdetail_N→`Engine.neutral_normal`, Material_Separation_Mask→`Textures.Batmobile_V3_Wheel_Lights_M`, Normal_Map→`Textures.Batmobile_V3_Wheel_Lights_N` |
| Playable_BatmobileJoker_SF | Batmobile_V3_Glass_INST | `Batmobile_V2_Textures_NEW.Batmobile_Glass` | Glass_Opacity=1.2000, Glass_Reflectivity=0.8000, Glass_Roughness=1.1000, glass_smudges=0.2000 | — | Mask (R=Reflect / G=Rough / B=Normal map compression artifacts fix)→`Textures.Batmobile_V3_Glass_S`, Normal→`Textures.Batmobile_V3_Glass_N`, OpacityMap→`Textures.Batmobile_V3_Glass_A` |
| Playable_BatmobileJoker_SF | BatmobileV3_Cockpit_Seat | `Engine.Batmobile_Hardleather_Master_MAT` | EmissiveMultiply=15.0000, Fake Aniso Brightness 1=0.0100, Fake Aniso Brightness 2=1.0000, fake aniso orientation=1.0000, fake aniso uv magnitude=1.0000, fake aniso uv shift=0.0000, Reflectivity_Multiplier=1.2000 | — | Colour_Map→`Textures.Batmobile_V3_Int_Cockpit_D`, Colour_Ramp_Map→`Maps.Batman_BM3_V2_Leather_Ramp`, Emissive→`Textures.Batmobile_V3_Int_Cockpit_E`, Normal_Map_Lacquer→`Textures.Batmobile_V3_Int_Cockpit_N`, Ref_n_Rough_Map→`Textures.Batmobile_V3_Int_Cockpit_S` |
| Playable_BatmobileJoker_SF | Batmobile_V3_Turret_Jokerfied_MIC | `Material_MASTERS.Batmobile_Jokerfied_V2_MAT` | Damage_dirt=0.3000, Damage_Dirt2_Opacity=0.6500, Damage_Dirt_Edges=2.0000, Grubby_Multiplier=1.2300, Joker_Damage_Scratches_All_Over=0.4000, Material2_Reflectivity=1.0000, MicroDetail_size=20.0000 | — | Damage_Chapter_Mask→`Textures.Batmobile_V3_TEXTURES_Weaponry_Damage_ChapterMask`, Diffuse→`jongee_test.Batmobile_V3_Weaponry_Turret_V2_D`, Material_Microdetail→`Textures.Batmobile_Microdetail`, Normal→`Textures.Batmobile_V3_Weaponry_Turret_V2_N` |
| Playable_BatmobileJoker_SF | Batmobile_V3_Undercarriage_NEW_MIC | `Material_Worn.Batmobile_V3_WheelArchs_NEW_MIC` | Damage_dirt=0.5000, Damage_Dirt_Edges=3.0000, Material1_Reflectivity=0.4000, Material1_Roughness=0.1000 | — | Damage_Chapter_Mask→`Textures.Batmobile_V3_Undercarriage_Damage_ChapterMask`, Normal_Map→`Textures.Batmobile_V3_Undercarriage_N` |
| Playable_BatmobileJoker_SF | Batmobile_V3_WheelArchs_NEW_MIC | `Material_MASTERS.Batmobile_Worn` | Damage_dirt=0.5000, Damage_Dirt2_Opacity=2.0000, Damage_Dirt_Edges=1.5000, EdgeMask_Metalicity=2.0000, Material0_Reflectivity=0.1500, Material0_Roughness=0.4000, Material1_Reflectivity=0.2000, Material1_Roughness=0.2500, Material2_Metalicity=1.0000, Material2_Reflectivity=0.9000, Material2_Roughness=0.1500, Material3_Reflectivity=0.5000 | — | Anisotropic Ramp→`Engine.Aniso_ramp_Lacquered`, Colour_Ramp_Map→`Engine.Batman_BM3_V2_Lacquered_Underlayer_Ramp`, Damage_Chapter_Mask→`Textures.Batmobile_V3_TEXTURES_WheelArch_Damage_ChapterMask`, Material3_Microdetail_N→`Engine.Batmobile_Micropattern_A_Normal`, Material_Microdetail→`Textures.Batmobile_Microdetail`, Normal_Map→`Textures.Batmobile_V3_WheelArch_N` |
| Playable_BatmobileJoker_SF | BatmobileV3_Wheel_V2_MIC | `Material_MASTERS.Batmobile_V3_Wheel_V2_MAT` | Metalicity_Multiplier=0.8000, Mud2_Opacity=2.0000, Mud_Edges_Opacity=0.5000, Mud_Opacity=1.0000, Mud_WetStreaks=1.0000, Reflectivity_Multiplier=1.0000, Roughness_Multiplier=0.2500 | — | — |
| Playable_BatmobileJoker_SF | BatmobileV3_Upgrades_MAT_INST | `Engine.Gadgets_Master_MAT` | Reflectivity_Multiplier=1.2000 | — | Colour_Map→`BatmobileV3_Upgrades.Batmobile_V3_Missile_Upgrade_D`, Normal_Map_Lacquer→`BatmobileV3_Upgrades.Batmobile_V3_Missile_Upgrade_N`, Ref_n_Rough_Map→`BatmobileV3_Upgrades.Batmobile_V3_Missile_Upgrade_S` |
| Playable_BatmobileJoker_SF | Batwing_Carrier_MAT_INST | `Engine.Metal` | — | — | — |
| Playable_BatmobileJoker_SF | Hydra_Trails_M_INST | `Shaders.Hydra_Trails_M` | HotPoint=1.0000, main_noise_scale=0.4000, noise_turb=0.0000, None=1.0000, turbscale=0.0000 | — | — |
| Playable_BatmobileJoker_SF | Outro_Explosion_INST | `Shaders.Back_Explosion_PP` | — | — | — |
| Playable_BatmobileJoker_SF | ThickGas_Tyre_1_INST | `Materials.ThickGas_Tyre` | — | — | — |
| Playable_BatmobileJoker_SF | xrayMetal_Batmobile_INST | `Xray.xrayBatmobile_MASTER` | — | — | — |
| Playable_BatmobileJoker_SF | LensFlare_OWStreetLightReflection_SOFT_INST | `Engine.LensFlare_ReflectionAdditive_MASTER` | — | — | Texture1→`Engine.LensFlare_RadialDiffractionWarm`, Texture2→`Engine.LensFlares_RadialStar` |
| Playable_BatmobileJoker_SF | Falling_Dust_MAT_INST | `Materials.Falling_Dust_MAT` | — | — | — |
| Playable_BatmobileJoker_SF | MAT_Flat_Shockwave_INST | `Engine.MAT_Flat_Shockwave` | Brightness=10.0000 | — | — |
| Playable_BatmobileMK2_SF | Batmobile_Interior_INST | `Engine.Metal` | — | — | Diffuse→`Batmobile_V2_Textures_NEW.Batmobile_V2_INTERIOR_D`, Normal→`Batmobile_V2_Textures_NEW.Batmobile_V2_INTERIOR_N`, Reflectivity\|Roughness→`Batmobile_V2_Textures_NEW.Batmobile_V2_INTERIOR_S` |
| Playable_BatmobileMK2_SF | Batmobile_MK2_Body_MIC | `Material.Batmobile_MK2_WheelArchs_MIC_INST` | Damage_Scratches_All_Over=0.4000, EdgeMask_Colour=0.4500 | — | Damage_Chapter_Mask→`Textures.Batmobile_V3_TEXTURES_Body_Damage_ChapterMask`, Diffuse→`Textures.Batmobile_MK2_Body2_D`, Metalicity_Roughness_Reflectivity→`Textures.Batmobile_MK2_Body2_R`, Normal→`Textures.Batmobile_V3_Body_N` |
| Playable_BatmobileMK2_SF | Batmobile_MK2_Wheel_INST | `Material_MASTERS.Batmobile_MK2_WheelArch_MAT` | Damage_Scratches_All_Over=0.4400, Paint_Strength=0.0000 | — | Diffuse→`Textures.Batmobile_MK2_Wheel_MK2_D`, Metalicity_Roughness_Reflectivity→`jongee_test.Batmobile_V3_TEXTURES_Wheel_V2_R`, Normal→`Textures.Batmobile_V3_TEXTURES_Wheel_V2_N` |
| Playable_BatmobileMK2_SF | Batmobile_MK2_WheelArchs_MIC_INST | `Material_MASTERS.Batmobile_MK2_WheelArch_MAT` | Damage_dirt=0.3000, Damage_Dirt_Edges=2.0000, Damage_Scratches_All_Over=0.4500, EdgeMask_Colour=0.6500, Grubby_Multiplier=1.0000, Metalicity_Multiplier=1.0000, Mud2_Opacity=0.4000, Mud_Density=0.0000, Mud_Edges_Opacity=1.0000, Mud_Opacity=300.0000, Paint_Metalicity=0.2000, Paint_Reflectivity=0.5000 | — | Diffuse→`Textures.Batmobile_MK2_WheelArch2_D`, Metalicity_Roughness_Reflectivity→`Textures.Batmobile_MK2_WheelArch2_R`, Normal→`Textures.Batmobile_V3_WheelArch_N` |
| Playable_BatmobileMK2_SF | MIC1 | `—` | — | — | — |
| Playable_BatmobileMK2_SF | Nimbus_Power_Cell_Mat | `Engine.Stagg_Quarantine_Panel_Window_MAT` | — | — | Texture_Diffuse→`Textures.Batmobile_V3_Power_Cell_INT_D`, Texture_Normal→`Stagg_Obj.Nimbus_Power_Cell_N`, Texture_Ref_Rough→`Stagg_Obj.Nimbus_Power_Cell_S` |
| Playable_BatmobileMK2_SF | Batmobile_V3_Cockpit_MIC | `Material_MASTERS.Batmobile_V3_Body_NoRain_MAT` | BaseMaterial_Microdetail_Size=45.0000, Fake Aniso Brightness 1=2.0000, Fake Aniso Brightness 2=0.1000, fake aniso orientation=1.0000, fake aniso uv magnitude=1.0000, fake aniso uv shift=0.0000, Material1_Microdetail_Size=120.0000, Material2_Microdetail_Size=30.0000, Material3_Microdetail_Size=30.0000, Metalicity=0.9000, Reflectivity_BaseMaterial2_Multiplier=5.0000, Reflectivity_Material3=1.0000 | — | Anisotropic Ramp→`Engine.Aniso_ramp_Lacquered`, Colour_Ramp_Map→`Engine.Batman_BM3_V2_Lacquered_Underlayer_Ramp`, Material1_Microdetail_N→`Engine.neutral_normal`, Material2_Microdetail→`Engine.Batmobile_Micropattern_C`, Material2_Microdetail_N→`Engine.neutral_normal`, Material3_Microdetail→`Engine.Batmobile_Micropattern_C`, Material3_Microdetail_N→`Engine.neutral_normal`, Material_Separation_Mask→`Textures.Batmobile_V3_Int_Cockpit_M`, Normal_Map→`Textures.Batmobile_V3_Int_Cockpit_N` |
| Playable_BatmobileMK2_SF | Batmobile_V3_Discbreak_MIC | `Material_MASTERS.Batmobile_V3_Discbreak` | Emissive_Intensity=1.5000, Fake Aniso Brightness 1=0.0000, Fake Aniso Brightness 2=0.0000, fake aniso orientation=0.0000, fake aniso uv magnitude=1.0000, Metalicity_Multiplier=0.8000, Mud2_Opacity=1.0000, Mud_Edges_Opacity=0.2000, Mud_Opacity=0.0000, Mud_WetStreaks=1.2000, Reflectivity_Multiplier=1.0000 | — | Anisotropic Ramp→`Engine.Aniso_ramp_Lacquered`, Colour_Map→`Textures.Batmobile_V3_BRAKE_DISC_D`, Colour_Ramp_Map→`Engine.Batman_BM3_V2_Lacquered_Underlayer_Ramp`, Normal_Map→`Textures.Batmobile_V3_BRAKE_DISC_N`, Ref_n_Rough_Map→`Textures.Batmobile_V3_BRAKE_DISC_R` |
| Playable_BatmobileMK2_SF | Batmobile_V3_Emissive | `Engine.Batmobile_V3_Body_MAT` | Fake Aniso Brightness 1=0.5000, Fake Aniso Brightness 2=0.1000, fake aniso orientation=1.0000, fake aniso uv magnitude=1.0000, fake aniso uv shift=0.0000, Material1_Microdetail_Size=250.0000, Material2_Microdetail_Size=30.0000, Material3_Microdetail_Size=30.0000, Metalicity=0.9200, Rain_Constant=1.0000, Reflectivity_Multiplier=1.0000 | — | Anisotropic Ramp→`Engine.Aniso_ramp_Lacquered`, BaseMaterial_Microdetail→`Engine.Batmobile_Micropattern_B`, Colour_Ramp_Map→`Engine.Batmobile_V3_Body_ColourRamp`, Emissive_Map→`Engine.Batmobile_V3_Wheel_E`, Material1_Microdetail→`Engine.Batmobile_Micropattern_A`, Material1_Microdetail_N→`Engine.Batmobile_Micropattern_A_Normal`, Material2_Microdetail→`Engine.Batmobile_Micropattern_C`, Material2_Microdetail_N→`Engine.neutral_normal`, Material3_Microdetail→`Engine.Batmobile_Micropattern_C`, Material3_Microdetail_N→`Engine.neutral_normal`, Material_Separation_Mask→`Textures.Batmobile_V3_Wheel_Lights_M`, Normal_Map→`Textures.Batmobile_V3_Wheel_Lights_N` |
| Playable_BatmobileMK2_SF | Batmobile_V3_Glass_INST | `Batmobile_V2_Textures_NEW.Batmobile_Glass` | Glass_Opacity=1.2000, Glass_Reflectivity=0.8000, Glass_Roughness=1.1000, glass_smudges=0.2000 | — | Mask (R=Reflect / G=Rough / B=Normal map compression artifacts fix)→`Textures.Batmobile_V3_Glass_S`, Normal→`Textures.Batmobile_V3_Glass_N`, OpacityMap→`Textures.Batmobile_V3_Glass_A` |
| Playable_BatmobileMK2_SF | BatmobileV3_Cockpit_Seat | `Engine.Batmobile_Hardleather_Master_MAT` | EmissiveMultiply=15.0000, Fake Aniso Brightness 1=0.0100, Fake Aniso Brightness 2=1.0000, fake aniso orientation=1.0000, fake aniso uv magnitude=1.0000, fake aniso uv shift=0.0000, Reflectivity_Multiplier=1.2000 | — | Colour_Map→`Textures.Batmobile_V3_Int_Cockpit_D`, Colour_Ramp_Map→`Maps.Batman_BM3_V2_Leather_Ramp`, Emissive→`Textures.Batmobile_V3_Int_Cockpit_E`, Normal_Map_Lacquer→`Textures.Batmobile_V3_Int_Cockpit_N`, Ref_n_Rough_Map→`Textures.Batmobile_V3_Int_Cockpit_S` |
| Playable_BatmobileMK2_SF | Batmobile_V3_Turret_NEW_MIC | `Material_Worn.Batmobile_V3_WheelArchs_NEW_MIC` | Damage_dirt=0.6500, Damage_Dirt_Edges=3.0000, Mud_Density=0.0000, Vector_Displacement_Multiplier=0.0000 | — | Damage_Chapter_Mask→`Textures.Batmobile_V3_TEXTURES_Weaponry_Damage_ChapterMask`, Normal_Map→`Textures.Batmobile_V3_Weaponry_Turret_V2_N` |
| Playable_BatmobileMK2_SF | Batmobile_V3_Tyre_V2_MIC | `Material_MASTERS.Batmobile_V3_Tyre_V2_MAT` | Diffuse_Adjust=1.3000, EMP=0.0000, EMP_Emissive_Multiplier=350.0000, Mud2_Opacity=1.5000, Mud_Edges_Opacity=1.2000, Mud_Opacity=30.0000, Mud_Roughness=0.2000, Mud_WetStreaks=1.0000, Rain_Constant=1.0000, RainReflectivityMul=2.0000, RainRoughnessMul=0.5000, Reflectivity_Multiplier=0.2000 | — | — |
| Playable_BatmobileMK2_SF | Batmobile_V3_Undercarriage_NEW_MIC | `Material_Worn.Batmobile_V3_WheelArchs_NEW_MIC` | Damage_dirt=0.5000, Damage_Dirt_Edges=3.0000, Material1_Reflectivity=0.4000, Material1_Roughness=0.1000 | — | Damage_Chapter_Mask→`Textures.Batmobile_V3_Undercarriage_Damage_ChapterMask`, Normal_Map→`Textures.Batmobile_V3_Undercarriage_N` |
| Playable_BatmobileMK2_SF | Batmobile_V3_WheelArchs_NEW_MIC | `Material_MASTERS.Batmobile_Worn` | Damage_dirt=0.5000, Damage_Dirt2_Opacity=2.0000, Damage_Dirt_Edges=1.5000, EdgeMask_Metalicity=2.0000, Material0_Reflectivity=0.1500, Material0_Roughness=0.4000, Material1_Reflectivity=0.2000, Material1_Roughness=0.2500, Material2_Metalicity=1.0000, Material2_Reflectivity=0.9000, Material2_Roughness=0.1500, Material3_Reflectivity=0.5000 | — | Anisotropic Ramp→`Engine.Aniso_ramp_Lacquered`, Colour_Ramp_Map→`Engine.Batman_BM3_V2_Lacquered_Underlayer_Ramp`, Damage_Chapter_Mask→`Textures.Batmobile_V3_TEXTURES_WheelArch_Damage_ChapterMask`, Material3_Microdetail_N→`Engine.Batmobile_Micropattern_A_Normal`, Material_Microdetail→`Textures.Batmobile_Microdetail`, Normal_Map→`Textures.Batmobile_V3_WheelArch_N` |
| Playable_BatmobileMK2_SF | BatmobileV3_Upgrades_MAT_INST | `Engine.Gadgets_Master_MAT` | Reflectivity_Multiplier=1.2000 | — | Colour_Map→`BatmobileV3_Upgrades.Batmobile_V3_Missile_Upgrade_D`, Normal_Map_Lacquer→`BatmobileV3_Upgrades.Batmobile_V3_Missile_Upgrade_N`, Ref_n_Rough_Map→`BatmobileV3_Upgrades.Batmobile_V3_Missile_Upgrade_S` |
| Playable_BatmobileMK2_SF | Batmobile_V3_Wheel_EMP_MAT_INST | `Material_MASTERS.Batmobile_V3_Wheel_V2_MAT` | — | — | Diffuse→`Material_MASTERS.Batmobile_V3_Winch_EMP_D` |
| Playable_BatmobileMK2_SF | Outro_Explosion_INST | `Shaders.Back_Explosion_PP` | — | — | — |
| Playable_BatmobileMK2_SF | Batmobile_Fire_Main_INST | `Materials.Batmobile_Fire_Main` | Blackbody_Desat=0.0000, Brightness=15.0000, Distortion=2.0000, Ember_Amount=0.7000, Hardness=0.9500, Mask_Power=2.5000, Radius=1.0000, RandomP=0.5000, Smoke_Strength=2.0000, Speed=2.0000, Spread=0.3000, Tile_Speed=1.8000 | — | — |
| Playable_BatmobileMK2_SF | DroneHacker_Beam_INST | `Materials.DroneHacker_Beam` | Green=1.0025 | — | — |
| Playable_BatmobileMK2_SF | EMP_Burst_V02_Stage_01 | `Engine.EMP_Burst_V02_MAT` | — | — | — |
| Playable_BatmobileMK2_SF | EMP_Burst_V02_Stage_02 | `Engine.EMP_Burst_V02_MAT` | — | — | — |
| Playable_BatmobileMK2_SF | EMP_Burst_V02_Stage_03 | `Engine.EMP_Burst_V02_MAT` | — | — | — |
| Playable_BatmobileMK2_SF | EMP_Burst_V02_Stage_04 | `Engine.EMP_Burst_V02_MAT` | — | — | — |
| Playable_BatmobileMK2_SF | ThickGas_Tyre_1_INST | `Materials.ThickGas_Tyre` | — | — | — |
| Playable_BatmobileMK2_SF | xrayMetal_Batmobile_INST | `Xray.xrayBatmobile_MASTER` | — | — | — |
| Playable_BatmobileMK2_SF | fx_Winch_M_lit_INST | `VFX_Generic.fx_Winch_M_lit` | Electricity=0.0000 | — | — |
| Playable_BatmobileMK2_SF | INST_Digital_Noise_BLUE | `Other.MAT_Digital_Noise` | Electricity_Brightness=20.0000, DBA_Alpha=50.0000, Distortion_Strength=2.0000, Distortion_Tiling=1.0000, Falloff=1.0000 | — | — |
| Playable_BatmobileMK2_SF | INST_Digital_Noise_V02 | `Other.MAT_Digital_Noise` | Electricity_Brightness=20.0000, DBA_Alpha=50.0000, Distortion_Strength=2.0000, Distortion_Tiling=1.0000, Falloff=1.0000 | — | — |
| Playable_BatmobileMK2_SF | INST_New_Electric_Arc_BLUE_THIN | `Engine.MAT_New_Electric_Arc` | Radius A=1.0000, Radius B=1.5000 | — | — |
| Playable_BatmobileMK2_SF | MAT_BitsOfShockwave_INST | `Other.MAT_BitsOfShockwave` | Brightness=15.0000 | — | — |
| Playable_BatmobileMK2_SF | MAT_Flat_Shockwave_INST | `Engine.MAT_Flat_Shockwave` | Brightness=10.0000 | — | — |
| Playable_BatmobileMK2_SF | MAT_Flat_Shockwave_INST_BLUE | `Engine.MAT_Flat_Shockwave` | Brightness=10.0000 | — | — |
| Playable_BatmobileMK2_SF | MAT_Mud_Splash_1x1_V02_INST | `Engine.MAT_Mud_Splash_1x1_V02` | — | — | — |
| Playable_Batmobile_SF | Batmobile_Interior_INST | `Engine.Metal` | — | — | Diffuse→`Batmobile_V2_Textures_NEW.Batmobile_V2_INTERIOR_D`, Normal→`Batmobile_V2_Textures_NEW.Batmobile_V2_INTERIOR_N`, Reflectivity\|Roughness→`Batmobile_V2_Textures_NEW.Batmobile_V2_INTERIOR_S` |
| Playable_Batmobile_SF | MIC1 | `—` | — | — | — |
| Playable_Batmobile_SF | Nimbus_Power_Cell_Mat | `Engine.Stagg_Quarantine_Panel_Window_MAT` | — | — | Texture_Diffuse→`Textures.Batmobile_V3_Power_Cell_INT_D`, Texture_Normal→`Stagg_Obj.Nimbus_Power_Cell_N`, Texture_Ref_Rough→`Stagg_Obj.Nimbus_Power_Cell_S` |
| Playable_Batmobile_SF | Batmobile_V3_Cockpit_MIC | `Material_MASTERS.Batmobile_V3_Body_NoRain_MAT` | BaseMaterial_Microdetail_Size=45.0000, Fake Aniso Brightness 1=2.0000, Fake Aniso Brightness 2=0.1000, fake aniso orientation=1.0000, fake aniso uv magnitude=1.0000, fake aniso uv shift=0.0000, Material1_Microdetail_Size=120.0000, Material2_Microdetail_Size=30.0000, Material3_Microdetail_Size=30.0000, Metalicity=0.9000, Reflectivity_BaseMaterial2_Multiplier=5.0000, Reflectivity_Material3=1.0000 | — | Anisotropic Ramp→`Engine.Aniso_ramp_Lacquered`, Colour_Ramp_Map→`Engine.Batman_BM3_V2_Lacquered_Underlayer_Ramp`, Material1_Microdetail_N→`Engine.neutral_normal`, Material2_Microdetail→`Engine.Batmobile_Micropattern_C`, Material2_Microdetail_N→`Engine.neutral_normal`, Material3_Microdetail→`Engine.Batmobile_Micropattern_C`, Material3_Microdetail_N→`Engine.neutral_normal`, Material_Separation_Mask→`Textures.Batmobile_V3_Int_Cockpit_M`, Normal_Map→`Textures.Batmobile_V3_Int_Cockpit_N` |
| Playable_Batmobile_SF | Batmobile_V3_Discbreak_MIC | `Material_MASTERS.Batmobile_V3_Discbreak` | Emissive_Intensity=1.5000, Fake Aniso Brightness 1=0.0000, Fake Aniso Brightness 2=0.0000, fake aniso orientation=0.0000, fake aniso uv magnitude=1.0000, Metalicity_Multiplier=0.8000, Mud2_Opacity=1.0000, Mud_Edges_Opacity=0.2000, Mud_Opacity=0.0000, Mud_WetStreaks=1.2000, Reflectivity_Multiplier=1.0000 | — | Anisotropic Ramp→`Engine.Aniso_ramp_Lacquered`, Colour_Map→`Textures.Batmobile_V3_BRAKE_DISC_D`, Colour_Ramp_Map→`Engine.Batman_BM3_V2_Lacquered_Underlayer_Ramp`, Normal_Map→`Textures.Batmobile_V3_BRAKE_DISC_N`, Ref_n_Rough_Map→`Textures.Batmobile_V3_BRAKE_DISC_R` |
| Playable_Batmobile_SF | Batmobile_V3_Emissive | `Engine.Batmobile_V3_Body_MAT` | Fake Aniso Brightness 1=0.5000, Fake Aniso Brightness 2=0.1000, fake aniso orientation=1.0000, fake aniso uv magnitude=1.0000, fake aniso uv shift=0.0000, Material1_Microdetail_Size=250.0000, Material2_Microdetail_Size=30.0000, Material3_Microdetail_Size=30.0000, Metalicity=0.9200, Rain_Constant=1.0000, Reflectivity_Multiplier=1.0000 | — | Anisotropic Ramp→`Engine.Aniso_ramp_Lacquered`, BaseMaterial_Microdetail→`Engine.Batmobile_Micropattern_B`, Colour_Ramp_Map→`Engine.Batmobile_V3_Body_ColourRamp`, Emissive_Map→`Engine.Batmobile_V3_Wheel_E`, Material1_Microdetail→`Engine.Batmobile_Micropattern_A`, Material1_Microdetail_N→`Engine.Batmobile_Micropattern_A_Normal`, Material2_Microdetail→`Engine.Batmobile_Micropattern_C`, Material2_Microdetail_N→`Engine.neutral_normal`, Material3_Microdetail→`Engine.Batmobile_Micropattern_C`, Material3_Microdetail_N→`Engine.neutral_normal`, Material_Separation_Mask→`Textures.Batmobile_V3_Wheel_Lights_M`, Normal_Map→`Textures.Batmobile_V3_Wheel_Lights_N` |
| Playable_Batmobile_SF | Batmobile_V3_Glass_INST | `Batmobile_V2_Textures_NEW.Batmobile_Glass` | Glass_Opacity=1.2000, Glass_Reflectivity=0.8000, Glass_Roughness=1.1000, glass_smudges=0.2000 | — | Mask (R=Reflect / G=Rough / B=Normal map compression artifacts fix)→`Textures.Batmobile_V3_Glass_S`, Normal→`Textures.Batmobile_V3_Glass_N`, OpacityMap→`Textures.Batmobile_V3_Glass_A` |
| Playable_Batmobile_SF | BatmobileV3_Cockpit_Seat | `Engine.Batmobile_Hardleather_Master_MAT` | EmissiveMultiply=15.0000, Fake Aniso Brightness 1=0.0100, Fake Aniso Brightness 2=1.0000, fake aniso orientation=1.0000, fake aniso uv magnitude=1.0000, fake aniso uv shift=0.0000, Reflectivity_Multiplier=1.2000 | — | Colour_Map→`Textures.Batmobile_V3_Int_Cockpit_D`, Colour_Ramp_Map→`Maps.Batman_BM3_V2_Leather_Ramp`, Emissive→`Textures.Batmobile_V3_Int_Cockpit_E`, Normal_Map_Lacquer→`Textures.Batmobile_V3_Int_Cockpit_N`, Ref_n_Rough_Map→`Textures.Batmobile_V3_Int_Cockpit_S` |
| Playable_Batmobile_SF | Batmobile_V3_Mainbody_NEW_MIC | `Material_Worn.Batmobile_V3_WheelArchs_NEW_MIC` | Material0_Reflectivity=0.2000, Material0_Roughness=0.4000, Material1_Reflectivity=0.2000, Material1_Roughness=0.2500, Material2_Reflectivity=0.9000, Material3_Reflectivity=0.1500, Mud2_Opacity=2.0000, Mud_Edges_Opacity=100.0000, Mud_Opacity=50.0000, Vector_Displacement_Multiplier=1.0000 | — | Damage_Chapter_Mask→`Textures.Batmobile_V3_TEXTURES_Body_Damage_ChapterMask`, Normal_Map→`Textures.Batmobile_V3_Body_N` |
| Playable_Batmobile_SF | Batmobile_V3_Turret_NEW_MIC | `Material_Worn.Batmobile_V3_WheelArchs_NEW_MIC` | Damage_dirt=0.6500, Damage_Dirt_Edges=3.0000, Mud_Density=0.0000, Vector_Displacement_Multiplier=0.0000 | — | Damage_Chapter_Mask→`Textures.Batmobile_V3_TEXTURES_Weaponry_Damage_ChapterMask`, Normal_Map→`Textures.Batmobile_V3_Weaponry_Turret_V2_N` |
| Playable_Batmobile_SF | Batmobile_V3_Tyre_V2_MIC | `Material_MASTERS.Batmobile_V3_Tyre_V2_MAT` | Diffuse_Adjust=1.3000, EMP=0.0000, EMP_Emissive_Multiplier=350.0000, Mud2_Opacity=1.5000, Mud_Edges_Opacity=1.2000, Mud_Opacity=30.0000, Mud_Roughness=0.2000, Mud_WetStreaks=1.0000, Rain_Constant=1.0000, RainReflectivityMul=2.0000, RainRoughnessMul=0.5000, Reflectivity_Multiplier=0.2000 | — | — |
| Playable_Batmobile_SF | Batmobile_V3_Undercarriage_NEW_MIC | `Material_Worn.Batmobile_V3_WheelArchs_NEW_MIC` | Damage_dirt=0.5000, Damage_Dirt_Edges=3.0000, Material1_Reflectivity=0.4000, Material1_Roughness=0.1000 | — | Damage_Chapter_Mask→`Textures.Batmobile_V3_Undercarriage_Damage_ChapterMask`, Normal_Map→`Textures.Batmobile_V3_Undercarriage_N` |
| Playable_Batmobile_SF | Batmobile_V3_WheelArchs_NEW_MIC | `Material_MASTERS.Batmobile_Worn` | Damage_dirt=0.5000, Damage_Dirt2_Opacity=2.0000, Damage_Dirt_Edges=1.5000, EdgeMask_Metalicity=2.0000, Material0_Reflectivity=0.1500, Material0_Roughness=0.4000, Material1_Reflectivity=0.2000, Material1_Roughness=0.2500, Material2_Metalicity=1.0000, Material2_Reflectivity=0.9000, Material2_Roughness=0.1500, Material3_Reflectivity=0.5000 | — | Anisotropic Ramp→`Engine.Aniso_ramp_Lacquered`, Colour_Ramp_Map→`Engine.Batman_BM3_V2_Lacquered_Underlayer_Ramp`, Damage_Chapter_Mask→`Textures.Batmobile_V3_TEXTURES_WheelArch_Damage_ChapterMask`, Material3_Microdetail_N→`Engine.Batmobile_Micropattern_A_Normal`, Material_Microdetail→`Textures.Batmobile_Microdetail`, Normal_Map→`Textures.Batmobile_V3_WheelArch_N` |
| Playable_Batmobile_SF | BatmobileV3_Wheel_V2_MIC | `Material_MASTERS.Batmobile_V3_Wheel_V2_MAT` | Metalicity_Multiplier=0.8000, Mud2_Opacity=2.0000, Mud_Edges_Opacity=0.5000, Mud_Opacity=1.0000, Mud_WetStreaks=1.0000, Reflectivity_Multiplier=1.0000, Roughness_Multiplier=0.2500 | — | — |
| Playable_Batmobile_SF | BatmobileV3_Upgrades_MAT_INST | `Engine.Gadgets_Master_MAT` | Reflectivity_Multiplier=1.2000 | — | Colour_Map→`BatmobileV3_Upgrades.Batmobile_V3_Missile_Upgrade_D`, Normal_Map_Lacquer→`BatmobileV3_Upgrades.Batmobile_V3_Missile_Upgrade_N`, Ref_n_Rough_Map→`BatmobileV3_Upgrades.Batmobile_V3_Missile_Upgrade_S` |
| Playable_Batmobile_SF | Batmobile_V3_Wheel_EMP_MAT_INST | `Material_MASTERS.Batmobile_V3_Wheel_V2_MAT` | — | — | Diffuse→`Material_MASTERS.Batmobile_V3_Winch_EMP_D` |
| Playable_Batmobile_SF | Outro_Explosion_INST | `Shaders.Back_Explosion_PP` | — | — | — |
| Playable_Batmobile_SF | Batmobile_Fire_Main_INST | `Materials.Batmobile_Fire_Main` | Blackbody_Desat=0.0000, Brightness=15.0000, Distortion=2.0000, Ember_Amount=0.7000, Hardness=0.9500, Mask_Power=2.5000, Radius=1.0000, RandomP=0.5000, Smoke_Strength=2.0000, Speed=2.0000, Spread=0.3000, Tile_Speed=1.8000 | — | — |
| Playable_Batmobile_SF | DroneHacker_Beam_INST | `Materials.DroneHacker_Beam` | Green=1.0025 | — | — |
| Playable_Batmobile_SF | EMP_Burst_V02_Stage_01 | `Engine.EMP_Burst_V02_MAT` | — | — | — |
| Playable_Batmobile_SF | EMP_Burst_V02_Stage_02 | `Engine.EMP_Burst_V02_MAT` | — | — | — |
| Playable_Batmobile_SF | EMP_Burst_V02_Stage_03 | `Engine.EMP_Burst_V02_MAT` | — | — | — |
| Playable_Batmobile_SF | EMP_Burst_V02_Stage_04 | `Engine.EMP_Burst_V02_MAT` | — | — | — |
| Playable_Batmobile_SF | ThickGas_Tyre_1_INST | `Materials.ThickGas_Tyre` | — | — | — |
| Playable_Batmobile_SF | xrayMetal_Batmobile_INST | `Xray.xrayBatmobile_MASTER` | — | — | — |
| Playable_Batmobile_SF | fx_Winch_M_lit_INST | `VFX_Generic.fx_Winch_M_lit` | Electricity=0.0000 | — | — |
| Playable_Batmobile_SF | INST_Digital_Noise_BLUE | `Other.MAT_Digital_Noise` | Electricity_Brightness=20.0000, DBA_Alpha=50.0000, Distortion_Strength=2.0000, Distortion_Tiling=1.0000, Falloff=1.0000 | — | — |
| Playable_Batmobile_SF | INST_Digital_Noise_V02 | `Other.MAT_Digital_Noise` | Electricity_Brightness=20.0000, DBA_Alpha=50.0000, Distortion_Strength=2.0000, Distortion_Tiling=1.0000, Falloff=1.0000 | — | — |
| Playable_Batmobile_SF | INST_New_Electric_Arc_BLUE_THIN | `Engine.MAT_New_Electric_Arc` | Radius A=1.0000, Radius B=1.5000 | — | — |
| Playable_Batmobile_SF | MAT_BitsOfShockwave_INST | `Other.MAT_BitsOfShockwave` | Brightness=15.0000 | — | — |
| Playable_Batmobile_SF | MAT_Flat_Shockwave_INST | `Engine.MAT_Flat_Shockwave` | Brightness=10.0000 | — | — |
| Playable_Batmobile_SF | MAT_Flat_Shockwave_INST_BLUE | `Engine.MAT_Flat_Shockwave` | Brightness=10.0000 | — | — |
| Playable_Batmobile_SF | MAT_Mud_Splash_1x1_V02_INST | `Engine.MAT_Mud_Splash_1x1_V02` | — | — | — |
| Playable_Batmobile_Std_6_SF | Batmobile_V3_Mainbody_Stage6_MIC | `Material_Stage6.Batmobile_V3_WheelArchs_Stage6_MIC` | Fear_Opacity=1.5000 | — | Damage_Chapter_Mask→`Textures.Batmobile_V3_TEXTURES_Body_Damage_ChapterMask`, Normal_Map→`Textures.Batmobile_V3_Body_N` |
| Playable_Batmobile_Std_6_SF | Batmobile_V3_Weaponry_Stage6_MIC | `Material_Stage6.Batmobile_V3_Mainbody_Stage6_MIC` | — | — | Damage_Chapter_Mask→`Textures.Batmobile_V3_TEXTURES_Weaponry_Damage_ChapterMask`, Normal_Map→`Textures.Batmobile_V3_Weaponry_Turret_V2_N` |
| Playable_Batmobile_Std_6_SF | Batmobile_V3_WheelArchs_Stage6_MIC | `Material_MASTERS.Batmobile_Stage6` | Damage_Scratches_All_Over=0.5000, EdgeMask_Metalicity=2.0000, fake aniso orientation=1.0000, fake aniso uv magnitude=1.0000, fake aniso uv shift=0.0000, Fear2_Opacity=2.0000, Fear_Density=1.0000, Fear_Edges_Opacity=1.0000, Fear_Opacity=1.0000, Fear_Reflectivity=0.2000, Fear_Roughness=0.6500, Fear_Streaks=1.0000 | — | Anisotropic Ramp→`Engine.Aniso_ramp_Lacquered`, Colour_Ramp_Map→`Engine.Batman_BM3_V2_Lacquered_Underlayer_Ramp`, Damage_Chapter_Mask→`Textures.Batmobile_V3_TEXTURES_WheelArch_Damage_ChapterMask`, Material3_Microdetail_N→`Engine.Batmobile_Micropattern_A_Normal`, Material_Microdetail→`Textures.Batmobile_Microdetail`, Normal_Map→`Textures.Batmobile_V3_WheelArch_N` |