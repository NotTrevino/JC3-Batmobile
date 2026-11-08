# VEC_DEFAULTS - the parent material's vector parameter defaults, read from the package

**Card:** COLOUR-vecdefaults (follow-on to the review of **G3-04b**, issue I-1). **Status: the review is right.**
`Playable_Batmobile_SF.upk` holds **87** `MaterialExpressionVectorParameter` exports; **82**
serialise a default and **5** do not. The default is a `StructProperty` whose tag name is
**`DefaultValue`**, at field **0xCC**, payload **16 B** = four little-endian floats. G3-04b's
"0/87, no value tag at all" is therefore a decoder miss (it looked only for `FloatProperty`/
`VectorProperty` at 0xCC), not a property of the bytes.

**Inputs (read-only):** the package, `COLOUR_FUNCTIONS.md` (the 87 and the material names),
`COLOUR_PARAMS.md` (the two values the brief names), `Tools/scripts/upk_read.py`, and BmSDK-AK's
`MaterialExpressionVectorParameter.g.cs` (MIT) for the field's name and offset. No game ran.

## 1. Package and reader facts (decoded)

| quantity | value | source |
|---|---:|---|
| package | `Playable_Batmobile_SF.upk` | header |
| bytes | 17,916,421 | file size |
| sha1 | `c6e87dd0c06fbce9` | hashlib over the file |
| exports | 5490 | export table |
| names | 3151 | name table |
| `MaterialExpressionVectorParameter` exports | 87 | export table, class name per export |
| of those with a serialised default | 82 | tag walk, §2 |
| of those without | 5 | tag walk, §5 |

## 2. Where the default sits (decoded)

| fact | value | evidence |
|---|---|---|
| tag type | `StructProperty` | tag stream of every export with a default |
| tag's own name | `DefaultValue` | same |
| field offset | 0xCC = 204 | same |
| payload | 16 B, 4 x f32 | 82/82 tags have size 16 |
| class size | 0xDC = 220 | 0xCC + 16 = 0xDC; BmSDK `MaterialExpressionVectorParameter.g.cs:8` (`size = 220`) |
| BmSDK field | `DefaultValue`, `FLinearColor` | same file lines 82 / 85 (`StructProperty: DefaultValue`, `Ptr + 204`) |

The offset is not inferred from UE3: the serialised tag offset, the tag name and BmSDK's own
declared field agree, and `0xCC + 16` lands exactly on the class size.

## 3. All 87 vector parameters, by tag shape (decoded)

`fingerprint` is every tag in the export as `Type@field`, so a missing default is visible as a
missing `StructProperty@0xcc` rather than as a decoder failure. Every walk reaches `eof`.

| exports | count | fingerprint |
|---:|---:|---|
| 63 | 63 | `BoolProperty@0x64 GuidProperty@0xb4 NameProperty@0xac ObjectNCRProperty@0x68 StructProperty@0xcc` |
| 14 | 14 | `GuidProperty@0xb4 NameProperty@0xac ObjectNCRProperty@0x68 StructProperty@0xcc` |
| 4 | 4 | `BoolProperty@0x64 GuidProperty@0xb4 NameProperty@0xac ObjectNCRProperty@0x68` |
| 3 | 3 | `BoolProperty@0x64 GuidProperty@0xb4 NameProperty@0xac NameProperty@0xc4 ObjectNCRProperty@0x68 StructProperty@0xcc` |
| 2 | 2 | `BoolProperty@0x64 GuidProperty@0xb4 ObjectNCRProperty@0x68 StructProperty@0xcc` |
| 1 | 1 | `GuidProperty@0xb4 NameProperty@0xac ObjectNCRProperty@0x68` |

## 4. The 82 defaults (decoded: package export, tag @0xCC, 16 B)

| # | export | material (outer) | parameter | default [R, G, B, A] | guid | source |
|---:|---:|---|---|---|---|---|
| 1 | 657 | `Batmobile_Body_MASTER` | `DetailMapTile` | [128, 64, 0, 1] | `068ba253` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 2 | 658 | `Batmobile_Body_MASTER` | `Batman_Rain_Direction` | [0, 0, 0, 0] | `9a4638f6` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 3 | 659 | `Batmobile_Body_MASTER` | `Rain_Mask_Vector` | [1, 1, 1, 1] | `d68ca176` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 4 | 660 | `Batmobile_Glass` | `Batman_Rain_Direction` | [0, 0, 1, 0] | `8658ddc6` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 5 | 661 | `Batmobile_Glass` | `Rain_Size_Multiplier` | [3, 3, 0, 1] | `8550db52` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 6 | 662 | `Stagg_Battery_01_MAT` | `CellColour` | [0.121, 0.588, 0.608, 1] | `703e0b5c` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 7 | 663 | `Stagg_Battery_01_MAT` | `None` | [0.81, 0.79, 0.26, 1] | `57d30361` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 8 | 664 | `Stagg_Battery_Energy_01_MAT` | `Lightning Color` | [10, 10, 10, 1] | `04039342` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 9 | 665 | `Stagg_Battery_Energy_01_MAT` | `MainColour` | [0.35, 0.72, 0.989, 1] | `9a1f8396` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 10 | 666 | `Batmobile_V3_Body_NoRain_MAT` | `Material1_Basecolour` | [0.623595, 0.39245, 0.329779, 1] | `f3e33f73` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 11 | 667 | `Batmobile_V3_Body_NoRain_MAT` | `Fake_Aniso_2_Colour` | [0.131219, 0.153623, 0.674157, 1] | `562fe1bc` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 12 | 668 | `Batmobile_V3_Body_NoRain_MAT` | `Rain_Size_Multiplier` | [2, 2, 0, 1] | `db12ecf7` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 13 | 670 | `Batmobile_V3_Body_NoRain_MAT` | `LightGroup1234` | [1, 1, 1, 1] | `8dd366c3` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 14 | 671 | `Batmobile_V3_Body_NoRain_MAT` | `LightGroup5678` | [1, 1, 1, 1] | `88e40055` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 15 | 672 | `Batmobile_V3_Body_NoRain_MAT` | `Art Light Mul 1234` | [1, 1, 1, 1] | `6b3d2ec6` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 16 | 673 | `Batmobile_V3_Body_NoRain_MAT` | `Art Light Mul 5678` | [1, 1, 1, 1] | `e6333ff1` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 17 | 674 | `Batmobile_V3_Body_NoRain_MAT` | `Batman_Rain_Direction` | [0, 0, 0, 0] | `df26f9cf` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 18 | 675 | `Batmobile_V3_Body_NoRain_MAT` | `CodeHeadlightColor` | [1, 0, 0, 1] | `815f76f9` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 19 | 676 | `Batmobile_V3_Body_NoRain_MAT` | `Fake_Aniso_1_Colour` | [0.674157, 0.647211, 0.375439, 1] | `c69ef213` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 20 | 677 | `Batmobile_V3_Body_NoRain_MAT` | `underlayer_Detail_to_Roughness` | [0, 0, 1, 1] | `ee1b6faf` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 21 | 678 | `Batmobile_V3_Body_NoRain_MAT` | `Roughness_per_material` | [0.25, 0.25, 0.25, 0.1] | `203454a5` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 22 | 679 | `Batmobile_V3_Body_NoRain_MAT` | `Material2_BaseColour` | [0.423977, 0.609159, 0.752809, 1] | `36c2320f` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 23 | 680 | `Batmobile_V3_Body_NoRain_MAT` | `Roughness_Base_Level` | [0.05, 0.2, 0, 1] | `fc8cef7b` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 24 | 681 | `Batmobile_V3_Body_NoRain_MAT` | `Material3_BaseColour` | [0.423977, 0.609159, 0.752809, 1] | `cbdefd37` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 25 | 682 | `Batmobile_V3_Body_NoRain_MAT` | `Main_BaseColour2` | [0.5, 0.5, 0.5, 1] | `ce2c5dcd` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 26 | 684 | `Batmobile_V3_Discbreak` | `Mud2_Colour` | [0.147998, 0.054592, 0.015175, 1] | `67dddc83` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 27 | 685 | `Batmobile_V3_Discbreak` | `Mud_Colour` | [0.263175, 0.14198, 0.067725, 1] | `70c846f7` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 28 | 686 | `Batmobile_V3_Discbreak` | `EmissiveCol` | [0.769663, 0.075344, 0.018439, 1] | `e6a52edb` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 29 | 687 | `Batmobile_V3_Tyre_V2_MAT` | `EMP_Emissive_Colour1` | [1, 0.955941, 0.972869, 1] | `7ef40e36` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 30 | 688 | `Batmobile_V3_Tyre_V2_MAT` | `Mud_Colour` | [0.263175, 0.14198, 0.067725, 1] | `0b9508bc` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 31 | 689 | `Batmobile_V3_Tyre_V2_MAT` | `Mud2_Colour` | [0.147998, 0.054592, 0.015175, 1] | `aa8b2377` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 32 | 690 | `Batmobile_V3_Tyre_V2_MAT` | `Rain_Size_Multiplier` | [1, 2, 0, 1] | `61627ccb` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 33 | 691 | `Batmobile_V3_Tyre_V2_MAT` | `Batman_Rain_Direction` | [0, 0, 0, 0] | `23c1aec9` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 34 | 692 | `Batmobile_V3_Tyre_V2_MAT` | `EMP_Emissive_Colour2` | [0, 0.094067, 1, 1] | `cd2736d3` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 35 | 693 | `Batmobile_V3_Wheel_V2_MAT` | `Rain_Size_Multiplier` | [1, 2, 0, 1] | `fa281deb` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 36 | 694 | `Batmobile_V3_Wheel_V2_MAT` | `Damage_Dirt_Colour` | [0.41573, 0.389493, 0.33165, 1] | `ecb2e1cc` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 37 | 695 | `Batmobile_V3_Wheel_V2_MAT` | `Mud2_Colour` | [0.147998, 0.054592, 0.015175, 1] | `02700a82` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 38 | 696 | `Batmobile_V3_Wheel_V2_MAT` | `Mud_Colour` | [0.263175, 0.14198, 0.067725, 1] | `5fb96ac6` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 39 | 697 | `Batmobile_V3_Wheel_V2_MAT` | `Batman_Rain_Direction` | [0, 0, -1, 0] | `fd8e1a8f` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 40 | 698 | `Batmobile_Worn` | `Material1_Basecolour` | [0.623595, 0.39245, 0.329779, 1] | `f3e33f73` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 41 | 699 | `Batmobile_Worn` | `Material3_Anisotropic_broad_Colour` | [0.131219, 0.153623, 0.674157, 1] | `562fe1bc` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 42 | 700 | `Batmobile_Worn` | `Rain_Size_Multiplier` | [1, 2, 0, 1] | `db12ecf7` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 43 | 701 | `Batmobile_Worn` | `Damage_Colour` | [0.302125, 0.230998, 0.163641, 0.098039] | `7099ce87` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 44 | 702 | `Batmobile_Worn` | `LightGroup1234` | [1, 1, 1, 1] | `8dd366c3` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 45 | 703 | `Batmobile_Worn` | `LightGroup5678` | [1, 1, 1, 1] | `88e40055` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 46 | 704 | `Batmobile_Worn` | `Art Light Mul 1234` | [1, 1, 1, 1] | `6b3d2ec6` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 47 | 705 | `Batmobile_Worn` | `Art Light Mul 5678` | [1, 1, 1, 1] | `e6333ff1` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 48 | 706 | `Batmobile_Worn` | `Batman_Rain_Direction` | [0, 0, -1, 0] | `df26f9cf` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 49 | 707 | `Batmobile_Worn` | `Damage_Dirt_Colour` | [0.41573, 0.389493, 0.33165, 1] | `b3ca3f4a` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 50 | 708 | `Batmobile_Worn` | `Damage_Chapter` | [0, 0, 0, 0] | `4614e464` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 51 | 709 | `Batmobile_Worn` | `Material3_Anisotropic_thin_Colour` | [0.674157, 0.647211, 0.375439, 1] | `c69ef213` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 52 | 710 | `Batmobile_Worn` | `EdgeMask_Colour` | [0.1, 0.1, 0.1, 1] | `535170e3` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 53 | 711 | `Batmobile_Worn` | `Diffuse_Adjust` | [1, 1, 1, 1] | `5fda350d` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 54 | 712 | `Batmobile_Worn` | `Material2_BaseColour` | [0.423977, 0.609159, 0.752809, 1] | `36c2320f` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 55 | 713 | `Batmobile_Worn` | `Mud_Colour` | [0.263175, 0.14198, 0.067725, 1] | `93b46dc1` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 56 | 714 | `Batmobile_Worn` | `Material3_BaseColour` | [0.423977, 0.609159, 0.752809, 1] | `cbdefd37` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 57 | 715 | `Batmobile_Worn` | `Mud2_Colour` | [0.147998, 0.054592, 0.015175, 1] | `6d5c89d4` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 58 | 717 | `Batmobile_Worn_NoRain` | `Material1_Basecolour` | [0.623595, 0.39245, 0.329779, 1] | `f3e33f73` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 59 | 718 | `Batmobile_Worn_NoRain` | `Material2_BaseColour` | [0.423977, 0.609159, 0.752809, 1] | `36c2320f` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 60 | 719 | `Batmobile_Worn_NoRain` | `Material3_BaseColour` | [0.423977, 0.609159, 0.752809, 1] | `cbdefd37` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 61 | 721 | `Back_Explosion_PP` | `OverExpose_Color` | [1, 1, 1, 1] | `48214c75` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 62 | 722 | `Back_Explosion_PP` | `Source` | [0.5, 1, 0, 1] | `c710dff2` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 63 | 723 | `Batmobile_Fire_Main` | `Colour_Add` | [8, 2, 1, 1] | `2e758f2e` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 64 | 725 | `Batmobile_Fire_Main` | `Impact` | [0.5, 0.5, 0, 0.5] | `42b58605` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 65 | 726 | `Batmobile_Fire_Main` | `Tiling_Fire` | [0.9, 0.7, 0, 1] | `1409fc4c` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 66 | 727 | `Batmobile_Fire_Main` | `Impact` | [0.5, 0.5, 0, 0.5] | `cd74b668` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 67 | 728 | `Batmobile_Fire_Main` | `Tiling_Fire` | [1.2, 0.9, 0, 1] | `ae5aca42` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 68 | 729 | `Batmobile_Fire_Main` | `Flow_Strength` | [-0.2, 0.01, 0, 1] | `82e32713` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 69 | 730 | `SeismicScan_Distortion` | `Colour` | [0.243137, 0.996078, 0.760784, 1] | `24a53378` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 70 | 731 | `SeismicScan_Distortion` | `Colour` | [0.243137, 0.996078, 0.760784, 1] | `940e8a53` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 71 | 732 | `EMP_BuildUp` | `None` | [1, 1, 5, 1] | `ec133610` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 72 | 733 | `EMP_BuildUp` | `Strenght` | [1, 1, 1, 1] | `c6b6e9e0` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 73 | 734 | `EMP_BuildUp` | `Tiling` | [1, 1, 1, 1] | `4b40a268` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 74 | 735 | `SeismicSonar_Smoke` | `LightingDirection` | [0, -0.5, 1, 1] | `b7ae6835` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 75 | 736 | `ThickGas_Tyre` | `Colour` | [3, 2, 1, 1] | `192b6849` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 76 | 737 | `xrayBatmobile_MASTER` | `metalColour` | [0.033333, 0.3, 1, 1] | `9c8ef98b` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 77 | 738 | `Beam_Mesh_M` | `Colour` | [0.243137, 0.996078, 0.760784, 5] | `a1ae0dfc` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 78 | 739 | `Beam_Mesh_M` | `Colour` | [0.243137, 0.996078, 0.760784, 5] | `891c9987` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 79 | 740 | `MAT_BitsOfShockwave` | `Colour` | [0.477364, 0.643423, 0.9, 1] | `677b9f3f` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 80 | 741 | `MAT_Digital_Noise` | `Electricity_Colour` | [1, 1, 1, 1] | `ec133610` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 81 | 742 | `MAT_Digital_Noise` | `Squares_Colour` | [1, 1, 1, 1] | `9f89167d` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |
| 82 | 743 | `MAT_Digital_Noise` | `Electricity_Tiling` | [1.5, 1.5, 1.5, 1] | `4b40a268` | `StructProperty:DefaultValue` @0xcc, value at object byte 20 |

## 5. The 5 that carry no default (decoded)

Each walks to `eof` with no `StructProperty` anywhere in its stream, so the absence is a byte
fact: these exports are 58/66 B against 90 B for the smallest export that has a default.

| export | material (outer) | parameter | object bytes | tags present |
|---:|---|---|---:|---|
| 669 | `Batmobile_V3_Body_NoRain_MAT` | `Anisotropic_Channel_Choice` | 66 | `BoolProperty@0x64 GuidProperty@0xb4 NameProperty@0xac ObjectNCRProperty@0x68` |
| 683 | `Batmobile_V3_Body_NoRain_MAT` | `Main_BaseColour` | 66 | `BoolProperty@0x64 GuidProperty@0xb4 NameProperty@0xac ObjectNCRProperty@0x68` |
| 716 | `Batmobile_Worn` | `Material0_BaseColour` | 66 | `BoolProperty@0x64 GuidProperty@0xb4 NameProperty@0xac ObjectNCRProperty@0x68` |
| 720 | `Batmobile_Worn_NoRain` | `Material0_BaseColour` | 66 | `BoolProperty@0x64 GuidProperty@0xb4 NameProperty@0xac ObjectNCRProperty@0x68` |
| 724 | `Batmobile_Fire_Main` | `Direction` | 58 | `GuidProperty@0xb4 NameProperty@0xac ObjectNCRProperty@0x68` |

## 6. The two values the brief names, checked against the whole default set

Both are compared **by value** over all 82 defaults (max component difference <= 0.0005), not by
name, so a differently named expression carrying the same colour would still be found.

| target | value (COLOUR_PARAMS.md) | same-named expressions and their defaults | defaults matching the value | nearest default | distance |
|---|---|---|---|---|---|
| BaseColour | [0.0258, 0.0258, 0.03, 1] | 683 `Main_BaseColour` **no default**; 716 `Material0_BaseColour` **no default**; 720 `Material0_BaseColour` **no default** | 0 | 710 `EdgeMask_Colour` [0.1, 0.1, 0.1, 1] | 0.074200 |
| Diffuse_Adjust | [2.2, 2, 2, 1] | 711 `Diffuse_Adjust` [1, 1, 1, 1] | 0 | 743 `Electricity_Tiling` [1.5, 1.5, 1.5, 1] | 0.700000 |

**BaseColour.** The value the brief names is stored at COLOUR_PARAMS.md §2 row 38 (owner `Batmobile_V3_WheelArchs_NEW_MIC` #767, VectorParameterValues field 0x168, item byte 262, tag @0x8), i.e. it is an
`FVectorParameterValue` item in a **material instance**, not a default on an expression.
Of the 3 expressions with that name, 3 carry **no default at all** (683, 716, 720).
Zero of the 82 defaults match it (nearest is 0.074200 away), so the
value is **not** among the 82 with the same numbers.

**Diffuse_Adjust.** The value the brief names is stored at COLOUR_PARAMS.md §2 row 37 (owner `Batmobile_V3_WheelArchs_NEW_MIC` #767, VectorParameterValues field 0x168, item byte 176, tag @0x8), i.e. it is an
`FVectorParameterValue` item in a **material instance**, not a default on an expression.
The single expression with that name (`Diffuse_Adjust`) carries a default: 711 [1, 1, 1, 1].
Zero of the 82 defaults match it (nearest is 0.700000 away), so the
value is **not** among the 82 with the same numbers.

**Answer to the brief's check:** neither value is a material default with those numbers.
`BaseColour` is the sharper case: the expressions of that name (`Material0_BaseColour` 716/720,
`Main_BaseColour` 683) have no serialised default at all, so the only base colour in the package is
the MIC override. `Diffuse_Adjust` has a default, and it is [1, 1, 1, 1] (export 711) - the
[2.2, 2, 2, 1] is the override in MIC 767.

## 7. Per-material census (derived: counts from §4-§5)

| master material | vector parameters | with default | without |
|---|---:|---:|---:|
| `Batmobile_Worn` | 19 | 18 | 1 |
| `Batmobile_V3_Body_NoRain_MAT` | 18 | 16 | 2 |
| `Batmobile_Fire_Main` | 7 | 6 | 1 |
| `Batmobile_V3_Tyre_V2_MAT` | 6 | 6 | 0 |
| `Batmobile_V3_Wheel_V2_MAT` | 5 | 5 | 0 |
| `Batmobile_Worn_NoRain` | 4 | 3 | 1 |
| `Batmobile_Body_MASTER` | 3 | 3 | 0 |
| `Batmobile_V3_Discbreak` | 3 | 3 | 0 |
| `EMP_BuildUp` | 3 | 3 | 0 |
| `MAT_Digital_Noise` | 3 | 3 | 0 |
| `Back_Explosion_PP` | 2 | 2 | 0 |
| `Batmobile_Glass` | 2 | 2 | 0 |
| `Beam_Mesh_M` | 2 | 2 | 0 |
| `SeismicScan_Distortion` | 2 | 2 | 0 |
| `Stagg_Battery_01_MAT` | 2 | 2 | 0 |
| `Stagg_Battery_Energy_01_MAT` | 2 | 2 | 0 |
| `MAT_BitsOfShockwave` | 1 | 1 | 0 |
| `SeismicSonar_Smoke` | 1 | 1 | 0 |
| `ThickGas_Tyre` | 1 | 1 | 0 |
| `xrayBatmobile_MASTER` | 1 | 1 | 0 |

## 8. What is not claimed

- **No combine rule.** Re-counted only as a guard: 11 MaterialFunctions, 944 `FunctionExpressions` slots, 0 non-zero. The operator graph is UNKNOWN (G3-04b), and this card does not
  re-open it.
- **No claim that a default is what the shader receives.** An expression default is the authored
  value a MIC may override; which one is live is a runtime question with no oracle in the project.
- **No socket mapping** (which parameter feeds base colour / roughness / dirt): the links are
  stripped, so that stays UNKNOWN.
- **GUIDs are not unique per export.** 13 of the 82 default GUIDs occur in more
  than one export (the body/worn copies share them), so a GUID names a parameter slot and cannot
  on its own tie one expression to one override [derived: §4 guid column].

## 9. Oracles (`--check` re-runs each)

| oracle | ok | detail |
|---|---|---|
| `class_size_is_0xcc_plus_16` | True | `{"0xcc+16": "0xdc", "bmsdk_size": "0xdc", "gcs_lines": {"ptr": 85, "size": 8, "struct": 82}}` |
| `defaults_are_named_16_byte_structs_at_0xcc` | True | `{"tag_names": ["DefaultValue"], "tag_offsets": [204], "tag_sizes": [16], "with_default": 82}` |
| `diffuse_adjust_default_is_white` | True | `{"711": [1.0, 1.0, 1.0, 1.0]}` |
| `every_walk_reaches_eof` | True | `{"eof": 87, "of": 87}` |
| `five_without_have_no_struct_tag_at_all` | True | `{"without": [[669, "Anisotropic_Channel_Choice", "Batmobile_V3_Body_NoRain_MAT", 66], [683, "Main_BaseColour", "Batmobile_V3_Body_NoRain_MAT", 66], [716, "Material0_BaseColour", "Batmobile_Worn", 66], [720, "Material0_BaseColour", "Batmobil` |
| `operator_graph_still_stripped` | True | `{"functions": 11, "nonzero": 0, "slots": 944}` |
| `package_header` | True | `{"exports": 5490, "names": 3151}` |
| `package_sha1_matches_colour_params` | True | `{"sha1": "c6e87dd0c06fbce956c0fd0adaebacef54e093a0"}` |
| `targets_are_not_defaults` | True | `{"BaseColour": {"distance": 0.0742, "matches": 0, "nearest": [710, "EdgeMask_Colour", [0.1, 0.1, 0.1, 1.0]]}, "Diffuse_Adjust": {"distance": 0.7000000000000002, "matches": 0, "nearest": [743, "Electricity_Tiling", [1.5, 1.5, 1.5, 1.0]]}}` |
| `vector_parameter_count_matches_colour_functions_md` | True | `{"colour_functions_md": 87, "measured": 87}` |

## 10. Result

- `MaterialExpressionVectorParameter` exports: **87** [decoded: export table]
- with a `DefaultValue` `StructProperty` @0xCC, 16 B: **82** [decoded: tag walk]
- without any default: **5** - 669 `Anisotropic_Channel_Choice`, 683 `Main_BaseColour`, 716 `Material0_BaseColour`, 720 `Material0_BaseColour`, 724 `Direction` [decoded]
- the two named values: **not defaults**; both sit in MIC 767's `VectorParameterValues` [decoded: COLOUR_PARAMS.md §2 rows 37-38]
- how the parameters combine: **UNKNOWN**, unchanged (944/944 slots zero, §8)
