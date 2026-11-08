# JC3 turrets: the yaw and pitch limits of the whole fleet

A turret in JC3 is a `Turret` part (yaw) and a `Cannon` part (pitch), each on one `hkpLimitedHingeConstraintData` (`Research/JC3Grab/TURRET.md`, G2-13). This page reads the two angle limits of every such pair in the fleet the decoded way, using G3-10e's atom layout: the angular limit atom starts at **+0x0F8** (u16 type code **14**), with the minimum at **+0x0FC** and the maximum at **+0x100**, radians.

Scope: **233 vehicle entities** in `PARTS_TABLE.jsonl`, all **233** re-read from the archives for this page: 233 with a parts module, 220 with a `.physicsc` (the other 13 ship no constraint at all). **40** entities carry a `Turret` or `Cannon` part; they fold into **11 distinct vehicle models**.

| | |
|---|---|
| turret-ish units | **14** (`pitch_only` 4; `turret` 7; `two_cannon` 3) |
| yaw hinged parts | 10 |
| pitch hinged parts | 14 |
| yaw spans present (deg) | 150, 300, 358 |
| pitch spans present (deg) | 25, 30, 55, 65, 75, 80, 100 |

`decoded` = the value sits at the stated offset in the stated object; `derived` = a rule over decoded values, stated where it is used; `UNKNOWN` = no byte pins it.

## 1. Every turret in the fleet

One row per unit. `Turret` = a `Turret`-behaviour yaw part; `two_cannon` = a pintle whose yaw and pitch are both `Cannon` parts (how the patrol boats are built); `pitch_only` = a gun frame with no yaw hinge in its parent chain (aircraft).

| model | class | units | yaw part | yaw min..max (deg) | yaw span | pitch part | pitch min..max (deg) | pitch span |
|---|---|---:|---|---:|---:|---|---:|---:|
| `advancedassault` | aircraft | pitch_only | `-` | - | - | `advancedassault_gatling_l_mount` | -45 .. 30 | 75 |
| `advancedassault` | aircraft | pitch_only | `-` | - | - | `advancedassault_gatling_r_mount` | -45 .. 30 | 75 |
| `lightassault` | aircraft | pitch_only | `-` | - | - | `lightassault_minigun_mount_l_vertical` | -45 .. 35 | 80 |
| `lightassault` | aircraft | pitch_only | `-` | - | - | `lightassault_minigun_mount_r_vertical` | -45 .. 35 | 80 |
| `apc` | apc | turret | `apc_turret_base` | -179 .. 179 | 358 | `apc_weapon_mount_vertical` | -15 .. 50 | 65 |
| `armoredjeep` | armed_land | turret | `armoredjeep_turret_base` | -179 .. 179 | 358 | `armoredjeep_weapon_mount_vertical` | -25 .. 50 | 75 |
| `technicaljeep` | armed_land | turret | `technicaljeep_rebel_turret` | -179 .. 179 | 358 | `technicaljeep_weapon_mount_vertical` | -10 .. 45 | 55 |
| `corvette` | boat | turret | `corvette_turret` | -150 .. 150 | 300 | `corvette_gun` | -5 .. 75 | 80 |
| `heavypatrol` | boat | two_cannon | `heavypatrol_weapon_mount_l_horizontal` | -75 .. 75 | 150 | `heavypatrol_weapon_mount_l_vertical` | -50 .. 50 | 100 |
| `heavypatrol` | boat | two_cannon | `heavypatrol_weapon_mount_r_horizontal` | -75 .. 75 | 150 | `heavypatrol_weapon_mount_r_vertical` | -50 .. 50 | 100 |
| `lightpatrol` | boat | two_cannon | `lightpatrol_weapon_mount_horizontal` | -75 .. 75 | 150 | `lightpatrol_weapon_mount_vertical` | -50 .. 25 | 75 |
| `bavariumtank` | tank | turret | `bavariumtank_turret` | -179 .. 179 | 358 | `bavariumtank_cannon` | -5 .. 20 | 25 |
| `mediumtank` | tank | turret | `mediumtank_turret` | -179 .. 179 | 358 | `mediumtank_cannon` | -5 .. 20 | 25 |
| `smalltank` | tank | turret | `smalltank_turret` | -179 .. 179 | 358 | `smalltank_cannon` | -5 .. 25 | 30 |

Each model row stands for every variant of it: `advancedassault` x5; `lightassault` x4; `apc` x3; `armoredjeep` x3; `technicaljeep` x4; `corvette` x3; `heavypatrol` x5; `lightpatrol` x4; `bavariumtank` x3; `mediumtank` x3; `smalltank` x3. The variants of a model share one parts module and one `.physicsc`, and the rebuild asserts every variant decodes the same numbers (`variants_of_a_model_agree`).

Hinge geometry (`decoded`: frame A row 0 is the axis, frame A translation the pivot; frame B row 0 agrees to 1e-3 on every unit):

| model | unit | side | constraint | .physicsc object | axis | pivot (x, y, z) |
|---|---|---|---:|---:|---|---|
| `advancedassault` | pitch_only | pitch | 11 | 0x2D820 | 1, 0, 0 | -0.989, 1.26, -0.094 |
| `advancedassault` | pitch_only | pitch | 12 | 0x2D950 | 1, 0, 0 | 0.983, 1.26, -0.094 |
| `lightassault` | pitch_only | pitch | 6 | 0x45B80 | 1, -0, 0 | -2.075, 1.134, 1.121 |
| `lightassault` | pitch_only | pitch | 7 | 0x45CB0 | 1, -0, 0 | 2.075, 1.134, 1.121 |
| `apc` | turret | yaw | 15 | 0x51E40 | -0, 1, 0 | -0.0037, 2.1367, 1.3048 |
| `apc` | turret | pitch | 14 | 0x51D10 | 1, 0, 0 | -0, 2.7313, 0.5942 |
| `armoredjeep` | turret | yaw | 18 | 0x64340 | -0, 1, 0 | 0.507, 2, 0.263 |
| `armoredjeep` | turret | pitch | 17 | 0x64210 | 1, 0, 0 | 0.5099, 2.2898, -0.3751 |
| `technicaljeep` | turret | yaw | 11 | 0x6CC30 | -0, 1, 0 | 0, 1.3878, 1.2902 |
| `technicaljeep` | turret | pitch | 12 | 0x6CD60 | 1, 0, 0 | 0, 2.0498, 0.6697 |
| `corvette` | turret | yaw | 6 | 0x45E70 | -0, 1, 0 | 0, 2.5787, -8.8316 |
| `corvette` | turret | pitch | 5 | 0x45D40 | 1, -0, 0 | 0.0212, 3.7889, -9.0548 |
| `heavypatrol` | two_cannon | yaw | 4 | 0x59AF0 | -0, 1, 0 | -2.7544, 2.7423, -0.2488 |
| `heavypatrol` | two_cannon | pitch | 3 | 0x599C0 | -0, 0, -1 | -2.7851, 2.9218, -0.2488 |
| `heavypatrol` | two_cannon | yaw | 6 | 0x59D50 | -0, 1, 0 | 2.7544, 2.7423, -0.2488 |
| `heavypatrol` | two_cannon | pitch | 5 | 0x59C20 | 0, 0, 1 | 2.7844, 2.9224, -0.2488 |
| `lightpatrol` | two_cannon | yaw | 3 | 0x3F1A0 | -0, 1, 0 | -0.0176, 1.4733, -3.0386 |
| `lightpatrol` | two_cannon | pitch | 2 | 0x3F070 | 1, 0, 0 | -0.0176, 1.6429, -3.0668 |
| `bavariumtank` | turret | yaw | 2 | 0x24F90 | -0, 1, 0 | 0, 2.2812, 1.1382 |
| `bavariumtank` | turret | pitch | 0 | 0x24D30 | 1, 0, 0 | 0, 2.5347, 0 |
| `mediumtank` | turret | yaw | 2 | 0x2E870 | -0, 1, 0 | 0, 2.2812, 1.1382 |
| `mediumtank` | turret | pitch | 0 | 0x2E610 | 1, 0, 0 | 0, 2.5347, 0 |
| `smalltank` | turret | yaw | 16 | 0x56B80 | -0, 1, 0 | 0, 1.8131, 0.5247 |
| `smalltank` | turret | pitch | 11 | 0x56520 | 1, 0, 0 | 0, 1.9143, -0.3611 |

Weapons whose fire points name these parts (`id:80201E4D` yaw / `id:5C19E7E0` pitch, `decoded` from the fire-point properties):

| model | unit | weapons |
|---|---|---|
| `advancedassault` | pitch_only | `w622_advancedhelicopter_mgun` (main_weapon, `weapon.point.left`) |
| `advancedassault` | pitch_only | `w622_advancedhelicopter_mgun` (main_weapon, `weapon.point.right`) |
| `lightassault` | pitch_only | `w604_helicopter_mgun` (main_weapon, `weapon.point.left`) |
| `lightassault` | pitch_only | `w604_helicopter_mgun` (main_weapon, `weapon.point.right`) |
| `apc` | turret | `w206_mounted_capstone_m2hm` (mounted_weapon, `attach.vehicle`) |
| `corvette` | turret | `w616_corvette_canon` (main_weapon, `fire_position_0`) |
| `heavypatrol` | two_cannon | `w206_mounted_capstone_m2hm` (mounted_weapon_2, `MountAttach`) |
| `heavypatrol` | two_cannon | `w206_mounted_capstone_m2hm` (mounted_weapon, `MountAttach`) |
| `bavariumtank` | turret | `w602_mediumtank_canon` (main_weapon, `fire_position_0`) |
| `mediumtank` | turret | `w602_mediumtank_canon` (main_weapon, `fire_position_0`) |
| `smalltank` | turret | `w605_smalltank_canon` (main_weapon, `fire_position_0`) |

## 2. Yaw: who turns all the way round, and who does not

- `Turret`-behaviour parts in the fleet: **22** over 233 entities; after folding the variants they are **10 distinct yaw hinges** (7 `Turret` yaws + 3 two-Cannon pintle yaws).
- Ship **-179 .. +179 deg** (span **358**): **6** of them - medium tank, Bavarium tank, small tank, APC, armoured jeep, technical. 358 deg of travel is one degree short of a full circle at each stop, so the aim is all-round with a **2 deg blind wedge pointing dead astern**.
- Ship a hinge with **no angular limit at all** (`hkpHingeConstraintData`): **0**.
- Ship a **full 360 deg** limited span: **0**.

Yaw narrower than the -179 .. +179 default (`decoded`):

| model | class | yaw part | min..max (deg) | span | unit |
|---|---|---|---:|---:|---|
| `corvette` | boat | `corvette_turret` | -150 .. 150 | 300 | turret |
| `heavypatrol` | boat | `heavypatrol_weapon_mount_l_horizontal` | -75 .. 75 | 150 | two_cannon |
| `heavypatrol` | boat | `heavypatrol_weapon_mount_r_horizontal` | -75 .. 75 | 150 | two_cannon |
| `lightpatrol` | boat | `lightpatrol_weapon_mount_horizontal` | -75 .. 75 | 150 | two_cannon |

**No turret in the fleet has an unlimited yaw hinge.** The full-rotation hinges that do exist are on other parts - the census in §3 lists all **15** of them with the parts that own them (no behaviour, `SteeringFork`), and every one fails the turret test. So "full rotation" for a shipped turret means the **358 deg** pair (-179 .. +179), not an unconstrained hinge.

Gun frames with **no yaw hinge at all** (`derived` from the parts' parent chains; the mount pitches, the aircraft aims):

| model | pitch part | parent part | parent behaviour | parent has a hinge |
|---|---|---|---|---|
| `advancedassault` | `advancedassault_gatling_l_mount` | `advancedassault_body` | None | no |
| `advancedassault` | `advancedassault_gatling_r_mount` | `advancedassault_body` | None | no |
| `lightassault` | `lightassault_minigun_mount_l_vertical` | `lightassault_minigun_mount_l_base` | None | no |
| `lightassault` | `lightassault_minigun_mount_r_vertical` | `lightassault_minigun_mount_r_base` | None | no |

## 3. The fleet's other full-rotation hinges (all non-turret)

`decoded`: every constraint object in all 233 entities whose class is `hkpHingeConstraintData` or whose limited span is a full 360 deg, with the part whose `constraint_index` selects it. **36 objects** on **32 entities** fold into **15 model hinges**: 4 unlimited (10 objects, `mediumoldfishing`, `transport`) and 11 at a full 360 deg span (26 objects, `atv`, `combatdirt`, `duck`, `jetski`, `modernmoped`, `modernroad`, `modernsport`, `oldmoped`, `oldroad`, `snowmobile`, `trials`).

| model | class | constraint | hinge class | span (deg) | owning part | behaviour | variants |
|---|---|---:|---|---:|---|---|---:|
| `atv` | armed_land | 5 | `hkpLimitedHingeConstraintData` | 360 | `atv_upper_steering` | SteeringFork | 4 |
| `combatdirt` | armed_land | 0 | `hkpLimitedHingeConstraintData` | 360 | `combatdirt_upper_steering` | SteeringFork | 3 |
| `duck` | boat | 0 | `hkpLimitedHingeConstraintData` | 360 | `duck_upper_steering` | SteeringFork | 2 |
| `jetski` | boat | 0 | `hkpLimitedHingeConstraintData` | 360 | `jetski_upper_steering` | SteeringFork | 3 |
| `mediumoldfishing` | boat | 34 | `hkpHingeConstraintData` | no limit atom | `mediumoldfishing_cast_net_c` | None | 2 |
| `mediumoldfishing` | boat | 35 | `hkpHingeConstraintData` | no limit atom | `mediumoldfishing_cast_net_l` | None | 2 |
| `mediumoldfishing` | boat | 36 | `hkpHingeConstraintData` | no limit atom | `mediumoldfishing_cast_net_r` | None | 2 |
| `modernmoped` | armed_land | 0 | `hkpLimitedHingeConstraintData` | 360 | `modernmoped_upper_steering` | SteeringFork | 2 |
| `modernroad` | armed_land | 0 | `hkpLimitedHingeConstraintData` | 360 | `modernroad_upper_steering` | SteeringFork | 2 |
| `modernsport` | armed_land | 0 | `hkpLimitedHingeConstraintData` | 360 | `modernsport_upper_steering` | SteeringFork | 2 |
| `oldmoped` | armed_land | 0 | `hkpLimitedHingeConstraintData` | 360 | `oldmoped_upper_steering` | SteeringFork | 2 |
| `oldroad` | armed_land | 0 | `hkpLimitedHingeConstraintData` | 360 | `oldroad_upper_steering` | SteeringFork | 2 |
| `snowmobile` | armed_land | 1 | `hkpLimitedHingeConstraintData` | 360 | `snowmobile_upper_steering` | None | 1 |
| `transport` | boat | 9 | `hkpHingeConstraintData` | no limit atom | `transport_spool` | None | 4 |
| `trials` | armed_land | 0 | `hkpLimitedHingeConstraintData` | 360 | `trials_upper_steering` | SteeringFork | 3 |

Two mechanisms therefore exist in shipped files for a part that turns freely: the **unlimited hinge class** (`hkpHingeConstraintData`, 10 objects on `mediumoldfishing`, `transport` - a cast-net pivot and a hose spool) and a **limited hinge whose pair is exactly -180 .. +180** (26 objects on `atv`, `combatdirt`, `duck`, `jetski`, `modernmoped`, `modernroad`, `modernsport`, `oldmoped`, `oldroad`, `snowmobile`, `trials` - the upper steering fork of a bike, or the snowmobile's equivalent). No turret part uses either, so a full-rotation turret would be a change of hinge class or of the pair - a build decision, not something the vanilla turrets already do.

## 4. Pitch: tanks, APCs, armed land vehicles, boats, aircraft

`decoded` per part; the class grouping is `derived` from the entity path (`01_land` / `02_air` / `03_sea`) and the model name - there is no decoded "vehicle class" field.

| class | models | pitch parts | depression (min) | elevation (max) | span min..max (deg) | yaw spans (deg) |
|---|---|---:|---:|---:|---|---|
| tank | `bavariumtank`, `mediumtank`, `smalltank` | 3 | -5 | 25 | 25 .. 30 | 358 |
| apc | `apc` | 1 | -15 | 50 | 65 .. 65 | 358 |
| armed_land | `armoredjeep`, `technicaljeep` | 2 | -25 | 50 | 55 .. 75 | 358 |
| boat | `corvette`, `heavypatrol`, `lightpatrol` | 4 | -50 | 75 | 75 .. 100 | 150, 300 |
| aircraft | `advancedassault`, `lightassault` | 4 | -45 | 35 | 75 .. 80 | - |

**tank**

| model | pitch part | unit | min..max (deg) | span |
|---|---|---|---:|---:|
| `bavariumtank` | `bavariumtank_cannon` | turret | -5 .. 20 | 25 |
| `mediumtank` | `mediumtank_cannon` | turret | -5 .. 20 | 25 |
| `smalltank` | `smalltank_cannon` | turret | -5 .. 25 | 30 |

**apc**

| model | pitch part | unit | min..max (deg) | span |
|---|---|---|---:|---:|
| `apc` | `apc_weapon_mount_vertical` | turret | -15 .. 50 | 65 |

**armed_land**

| model | pitch part | unit | min..max (deg) | span |
|---|---|---|---:|---:|
| `armoredjeep` | `armoredjeep_weapon_mount_vertical` | turret | -25 .. 50 | 75 |
| `technicaljeep` | `technicaljeep_weapon_mount_vertical` | turret | -10 .. 45 | 55 |

**boat**

| model | pitch part | unit | min..max (deg) | span |
|---|---|---|---:|---:|
| `lightpatrol` | `lightpatrol_weapon_mount_vertical` | two_cannon | -50 .. 25 | 75 |
| `heavypatrol` | `heavypatrol_weapon_mount_l_vertical` | two_cannon | -50 .. 50 | 100 |
| `heavypatrol` | `heavypatrol_weapon_mount_r_vertical` | two_cannon | -50 .. 50 | 100 |
| `corvette` | `corvette_gun` | turret | -5 .. 75 | 80 |

**aircraft**

| model | pitch part | unit | min..max (deg) | span |
|---|---|---|---:|---:|
| `advancedassault` | `advancedassault_gatling_l_mount` | pitch_only | -45 .. 30 | 75 |
| `advancedassault` | `advancedassault_gatling_r_mount` | pitch_only | -45 .. 30 | 75 |
| `lightassault` | `lightassault_minigun_mount_l_vertical` | pitch_only | -45 .. 35 | 80 |
| `lightassault` | `lightassault_minigun_mount_r_vertical` | pitch_only | -45 .. 35 | 80 |

What the numbers say:

- **Tanks are the flat shooters.** The medium tank and the Bavarium tank share exactly `-5 .. +20`; the small tank is `-5 .. +25`. 5 deg of depression is the whole tank family's limit, so a tank cannot shoot downward at a target below its hull, and its elevation stops at 20-25 deg.
- **The APC aims much higher and lower** than a tank: `-15 .. +50`. It is the same `w206` mounted M2 as the jeeps, on a taller turret, and its span (65 deg) is more than double the medium tank's 25.
- **Boats split into two builds.** The corvette's real turret is `-5 .. +75` - tank depression, three and a half times the tank's elevation - on a yaw restricted to `+-150`. The patrol boats use two-Cannon pintles instead: `+-50` (heavypatrol) and `-50 .. +25` (lightpatrol), with the yaw cut to `+-75` on both.
- **The trade is yaw for pitch.** Every `Turret`-behaviour yaw keeps 358 deg and gives up pitch (max elevation 20-25 deg on tanks); every two-Cannon pintle with a wide pitch gives up yaw (`+-75`). The corvette is the one vehicle that keeps both (300 deg yaw, 80 deg pitch).
- **Aircraft gun frames pitch but do not yaw on their own hinge**: `-45 .. +35` (lightassault door miniguns) and `-45 .. +30` (advancedassault gatlings), mounted on plain adapters, so the airframe does the aiming.

## 5. Oracles (`--check` re-runs every one of them)

| oracle | result |
|---|---|
| `every_Turret_part_on_a_limited_hinge_type_14` | **pass** |
| `every_yaw_axis_is_vertical` | **pass** |
| `every_pitch_axis_is_horizontal` | **pass** |
| `frame_A_and_frame_B_share_the_axis` | **pass** |
| `limits_ordered_and_within_pi` | **pass** |
| `turret_parts_identity_parent_offset` | **pass** |
| `TURRET_md_samples_reproduce` | **pass** |
| `variants_of_a_model_agree` | **pass** |
| `no_turret_part_on_a_full_rotation_hinge` | **pass** |
| `full_rotation_hinges_are_variant_stable` | **pass** |
| `boat_pitch_spans_exceed_tank_pitch_spans` | **pass** |
| `turret_yaw_all_round_two_cannon_yaw_not` | **pass** |
| `every_entity_scanned` | **pass** |

Why these are oracles and not decoration:

- `every_Turret_part_on_a_limited_hinge_type_14` - the pair of readings that must agree: behaviour `Turret` (from the parts module) and the atom type code (from `.physicsc`). If the limit offsets were wrong, the type code would not be 14.
- `every_yaw_axis_is_vertical` / `every_pitch_axis_is_horizontal` - a yaw hinge that reads a horizontal axis would mean the axis is not frame A row 0.
- `frame_A_and_frame_B_share_the_axis` - a limited hinge stores one axis in both frames; two independent 16-byte rows agreeing to 1e-3 on all 14 units is what pins the axis offset.
- `TURRET_md_samples_reproduce` - the six turreted vehicles G2-13 printed (`TURRET.md` §2) must come out at exactly its numbers: medium tank and Bavarium tank -179..179 / -5..20, small tank / -5..25, APC / -15..50, armoured jeep / -25..50, technical / -10..45.
- `variants_of_a_model_agree` - 40 entities grouped into 11 models; a variant disagreeing would mean the link part -> constraint was unstable.
- `no_turret_part_on_a_full_rotation_hinge` and `boat_pitch_spans_exceed_tank_pitch_spans` - the two claims this page makes about the fleet, turned into failing checks.

## 6. UNKNOWNs

- **the hinge axis frame (body-A local vs vehicle space)** - tried: compared the decoded pivots and axes with the art: the medium tank's turret pivot (0, 2.2812, 1.1382) and +Y axis agree with vehicle space, but the patrol boats' pitch hinge reads +-Z in a yawing parent's frame. Still unknown because no byte names the frame; only the parent part's rest orientation would settle it, and that matrix is in the .lod, not decoded here.
- **a rotation speed or acceleration for the turret** - tried: read every atom of the limited hinge (type 14 only carries the pair) and the parts module (no such field). Still unknown because the turn rate is code-side; the files carry an axis and two angles (G3-10e's finding, still true).
- **which of a two-Cannon boat mount is the 'turret' in game logic** - tried: the weapon fire point names the horizontal part as yaw and the vertical part as pitch, and the vertical part's parent is the horizontal one. Still unknown because both parts carry behaviour Cannon; there is no decoded ordinal.
- **whether a full-rotation turret is possible without a new hinge class** - tried: censused every hinge in the fleet: 4 hkpHingeConstraintData and 8 limited hinges with a full 360 deg span exist, none on a turret part. Still unknown because no shipped turret uses either; a port would have to change the class or the pair, and that is a build change, not a decode.

## 7. Files

| file | what |
|---|---|
| `Tools/scripts/jc3_turret_limits.py` | this pass, `--write` / `--check` |
| `Research/JC3Grab/TURRET_LIMITS.md` | this page |
| `Research/JC3Grab/TURRET_LIMITS.json` | the same, machine-readable, every offset and every angle |

