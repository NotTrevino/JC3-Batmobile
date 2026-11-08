# JC3 door angles -- DONE report

STATUS: done

Every vehicle entity in `Research/JC3Grab/INDEX.json` (233 `.ee` bundles) was opened, its
`*_vehicle_parts.vmodc` decoded for `door_parts[]` / `part_index` /
`world_collision_body_id` / `constraint_index`, and each door part linked through the
`.physicsc` constraint array to its `hkpLimitedHingeConstraintData`, whose +0x0FC/+0x100
radian limits are given in degrees.

Result: **233 entities scanned, 173 with door parts, 88 cars (parts-module payloads) with
door parts, 338 door rows, 334 of them on a limited hinge, over 1086 constraint records.**
The 4 rows without a hinge are reported as such; no door row resolves to a constraint of a
non-limited class. The vanilla Serpente (sportsmuscle) doors are 0..80 deg, 0..80 deg and
0..70 deg (hood). `--check` re-decodes everything from the game bytes, rebuilds both
outputs, compares them byte-for-byte and passes 21/21 oracles.

## Files written

| file | what |
|---|---|
| `Tools/scripts/jc3_door_angles.py` | new script, `--write` / `--check` |
| `Research/JC3Grab/DOOR_ANGLES.md` | 88 cars, 338 door rows, summary, exceptions, oracles, UNKNOWNs |
| `Research/JC3Grab/DOOR_ANGLES.json` | the same, machine-readable, every row with its record slot, constraint offset and byte offsets of the two limits |
| `tmp/freebuff/reports/JC3-door-angles.md` | this report |

Nothing else was edited. Scratch probes live under `tmp/freebuff/scratch/` (`probe_doorangles1..16.py`).

## The chain, decoded

| hop | file | field / offset | evidence |
|---|---|---|---|
| 1 | `<car>_vehicle_parts.vmodc` | `door_parts[i].part_index` | 338/338 rows resolve to a part in the same module; no duplicate array entries |
| 2 | same module | `parts[i].world_collision_body_id` | recorded per row as `body_id`; equals hop 4's body u32 in 330/334 hinged rows |
| 3 | same module | `parts[i].constraint_index` | in range of the physics system's constraint array in 334/334 hinged rows |
| 4 | `.physicsc`, `hknpPhysicsSystemData +0x50` | 24 B record: `+0x00` `hkpConstraintData*` (fixup), `+0x08` u32 body, `+0x0C` 0x7fffffff, `+0x10`/`+0x14` zero | record count = constraint-object count in 88/88 files; every record pointer resolves to a `*ConstraintData` object; record set = object set; offsets ascend; 24 B stride fits each array (0..15 B pad to the next target) |
| 5 | `.physicsc`, that constraint | `+0x0FC` min, `+0x100` max (rad), `+0x104` factor | min <= max 334/334, within +/-pi 334/334, on a 0.5-deg grid 334/334, factor 1.0, frame A orthonormal 334/334 |

`travel_deg` is `derived` as `max - min`; `min_deg`/`max_deg` are the raw radians times
180/pi rounded to 3 decimals. The report gives the authored limit pair, which by DOORS.md
§1/§5 is the whole open range: the module stores no rate, curve or interaction.

### Vanilla Serpente (sportsmuscle)

| part | behaviour | part idx | body | con | hinge @ | axis | min | max | travel | pivot |
|---|---|---:|---:|---:|---|---|---:|---:|---:|---|
| `sportsmuscle_door_f_l` | FrontLeftDoor | 1 | 1 | 0 | 0x4DA80 | (0, -1, 0) | 0 | 80 | 80 | (-1.018, 0.622, -0.771) |
| `sportsmuscle_door_f_r` | FrontRightDoor | 2 | 4 | 2 | 0x4DCE0 | (0, 1, 0) | 0 | 80 | 80 | (1.018, 0.622, -0.771) |
| `sportsmuscle_hood_signature` | Hood | 25 | 20 | 8 | 0x4E4E0 | (1, 0, 0) | 0 | 70 | 70 | (0, 1.057, -0.848) |

These match G2-15's published values. The vanilla bundle `vanilla_v0300.ee`'s
`sportsmuscle_vehicle_parts.vmodc` (sha1 `23f0bcc8ff57a985`) and `sportsmuscle.physicsc`
(sha1 `e206a2be779cb14d`) are byte-identical to the archive members this pass decoded, so
the table above is the vanilla Serpente, not a modded copy.

### Exceptions, all listed in the outputs

- **4 door rows with `constraint_index` -1** (no hinge, no range in the files):
  `smallfloatprop_wing_l/_r`, `privatepropeller_wing_cl1/_cr1` (LeftWing/RightWing).
- **4 door rows whose part body id differs from their constraint record's body u32**:
  `vintagesports_door_f_l` 21 vs 16, `vintagesports_door_f_r` 24 vs 19,
  `vintagesports_hood` 32 vs 29, `oldbus_trunk` 49 vs 50. The hinge is still the one the
  module's own `constraint_index` names (its pivot mirrors the opposite door and the limits
  are the same), so the link is kept and both numbers are shown. The set is pinned by name
  in the checker so it cannot drift silently.

### Fleet-wide ranges

| limit pair (deg) | rows | | limit pair (deg) | rows |
|---|---:|---|---|---:|
| 0..80 | 203 | | -1..1 | 4 |
| 0..90 | 31 | | 0..120 | 4 |
| 0..30 | 25 | | 0..15 | 4 |
| 0..150 | 16 | | 0..43 | 4 |
| 0..130 | 8 | | 0..95 | 4 |
| -0.5..0.5 | 6 | | 0..60 | 3 |
| 0..100 | 6 | | 0..75 | 3 |
| -90..0 | 5 | | 0..110 / 0..70 / 0..85 | 2 each |
| | | | 0..160 / 0..35 | 1 each |

By behaviour (rows include the 4 hinge-less wing rows): FrontLeftDoor 87, FrontRightDoor 64,
Hood 36, RearRightDoor 34, RearLeftDoor 26, Trunk 25, MissileHatch 16, CargoBayDoor 10,
CenterRightDoor 10, CenterLeftDoor 8, RearDoor 8, LeftWing 5, RightWing 5, TurretDoor 4.

## Commands and output

### 1. Read the governing files (no stdout)

```
E:/Modding/JC3-Batmobile/tmp/freebuff/INSTRUCTIONS.md
Research/JC3Grab/DOORS.md
Research/JC3Grab/PHYSICS_LIMITS.md
Tools/scripts/jc3_physics_limits.py
Tools/scripts/jc3doors.py
Tools/scripts/jc3hkx.py
```

### 2. Environment check

```
$ cd E:/Modding/JC3-Batmobile && ls Research/JC3Grab | head -80; echo ---; ls Tools/scripts | head -60; echo ---; ls tmp/freebuff
```
Output: the `Research/JC3Grab` listing (COLOUR*, CONSTRAINT_CODE*, DAMAGE_*, DECODE_DEPTH*,
DOORS.json/DOORS.md, ... PHYSICS_LIMITS.*, PHYSICS_ROLES*, PARTS_TABLE.*, ...), the
`Tools/scripts` listing (`jc3doors.py`, `jc3_physics_limits.py`, ...) and the
`tmp/freebuff` listing (`INSTRUCTIONS.md`, `manual`, `reports`, `scratch`, ...).
Verdict: `Tools/scripts/jc3doors.py` and `jc3_physics_limits.py` exist as the two prior
passes this one builds on.

```
$ python --version
Python 3.13.12
```

### 3. Probe 1 -- donor parts, door array, constraints and system-data arrays

```
$ cd E:/Modding/JC3-Batmobile && python tmp/freebuff/scratch/probe_doorangles1.py 2>&1 | head -80
table entries 233 distinct modules 79
module sportsmuscle_vehicle_parts.vmodc parts 42
0 sportsmuscle_body beh= None body= 0 parent= -1
1 sportsmuscle_door_f_l beh= FrontLeftDoor body= 1 parent= 0
2 sportsmuscle_door_f_r beh= FrontRightDoor body= 4 parent= 0
... (42 parts) ...
--- raw part keys with constraint
door_parts raw: {'door_parts': '', 'door_parts[0].part_index': 1, 'door_parts[1].part_index': 2, 'door_parts[2].part_index': 25}
constraint-ish: {'parts[0].constraint_index': -1, 'parts[1].constraint_index': 0, 'parts[2].constraint_index': 2, 'parts[3].constraint_index': 4, ... 'parts[25].constraint_index': 8, ...}
body-ish: {}
physics files [('models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc', 340368)]
models/.../sportsmuscle.physicsc objs 430 Counter({'CPfxPartIndexProperty': 98, 'hkRefCountedProperties': 92, 'hknpShapeMassProperties': 56, 'hknpConvexPolytopeShape': 54, 'hkGeometry': 36, 'hknpDynamicCompoundShape': 20, 'hknpDynamicCompoundShapeData': 20, 'hknpExternMeshShape': 18, 'hknpExternMeshShapeData': 18, 'hkpLimitedHingeConstraintData': 9, 'hknpStaticCompoundShape': 2, 'hknpStaticCompoundShapeData': 2, 'hkpRagdollConstraintData': 2, 'hkRootLevelContainer': 1, 'hknpPhysicsSceneData': 1, 'hknpPhysicsSystemData': 1})
  cons 0x4DA80 hkpLimitedHingeConstraintData        ext=304 lo=0.0000 hi=1.3963
  cons 0x4DBB0 hkpLimitedHingeConstraintData        ext=304 lo=-0.6109 hi=0.0000
  cons 0x4DCE0 hkpLimitedHingeConstraintData        ext=304 lo=0.0000 hi=1.3963
  cons 0x4DE10 hkpLimitedHingeConstraintData        ext=304 lo=-0.6109 hi=0.0000
  cons 0x4DF40 hkpRagdollConstraintData             ext=416 lo=0.0000 hi=0.0000
  cons 0x4E0E0 hkpLimitedHingeConstraintData        ext=304 lo=-0.2618 hi=0.0000
  cons 0x4E210 hkpRagdollConstraintData             ext=416 lo=0.0000 hi=0.0000
  cons 0x4E3B0 hkpLimitedHingeConstraintData        ext=304 lo=0.0000 hi=0.5236
  cons 0x4E4E0 hkpLimitedHingeConstraintData        ext=304 lo=0.0000 hi=1.2217
  cons 0x4E610 hkpLimitedHingeConstraintData        ext=304 lo=-0.2618 hi=0.0000
  cons 0x4E740 hkpLimitedHingeConstraintData        ext=304 lo=0.0000 hi=1.5708
  system data 0x000A0 ext=20912
    +0x10 ptr=0x00120 size=42 cap=42 elem=80
    +0x20 ptr=0x010E0 size=42 cap=42 elem=64
    +0x30 ptr=0x01B60 size=42 cap=42 elem=112
    +0x40 ptr=0x02DC0 size=62 cap=62 elem=96
    +0x50 ptr=0x04880 size=11 cap=11 elem=None
    +0x60 ptr=0x04990 size=276 cap=276 elem=8
```

The system data's +0x50 array has **11 entries and the file has 11 constraint objects**;
the donor's constraint indices run 0..10. That is the hop-3 -> hop-4 link.

### 4. Probe 2/3 -- the +0x50 array is 24-byte records

```
$ python tmp/freebuff/scratch/probe_doorangles3.py 2>&1 | head -30
array50 ptr=0x04880 size=11 cap=11
next object after array start: 0x4990
0 rec@0x04880 data=0x4DA80 cls='hkpLimitedHingeConstraintData'    u32_8=1 u32_12=0x7fffffff u32_16=0 u32_20=0x0
1 rec@0x04898 data=0x4DBB0 cls='hkpLimitedHingeConstraintData'    u32_8=3 u32_12=0x7fffffff u32_16=0 u32_20=0x0
2 rec@0x048B0 data=0x4DCE0 cls='hkpLimitedHingeConstraintData'    u32_8=4 u32_12=0x7fffffff u32_16=0 u32_20=0x0
3 rec@0x048C8 data=0x4DE10 cls='hkpLimitedHingeConstraintData'    u32_8=6 u32_12=0x7fffffff u32_16=0 u32_20=0x0
4 rec@0x048E0 data=0x4DF40 cls='hkpRagdollConstraintData'         u32_8=7 u32_12=0x7fffffff u32_16=0 u32_20=0x0
5 rec@0x048F8 data=0x4E0E0 cls='hkpLimitedHingeConstraintData'    u32_8=16 u32_12=0x7fffffff u32_16=0 u32_20=0x0
6 rec@0x04910 data=0x4E210 cls='hkpRagdollConstraintData'         u32_8=18 u32_12=0x7fffffff u32_16=0 u32_20=0x0
7 rec@0x04928 data=0x4E3B0 cls='hkpLimitedHingeConstraintData'    u32_8=19 u32_12=0x7fffffff u32_16=0 u32_20=0x0
8 rec@0x04940 data=0x4E4E0 cls='hkpLimitedHingeConstraintData'    u32_8=20 u32_12=0x7fffffff u32_16=0 u32_20=0x0
9 rec@0x04958 data=0x4E610 cls='hkpLimitedHingeConstraintData'    u32_8=26 u32_12=0x7fffffff u32_16=0 u32_20=0x0
10 rec@0x04970 data=0x4E740 cls='hkpLimitedHingeConstraintData'   u32_8=35 u32_12=0x7fffffff u32_16=0 u32_20=0x0
bytes between 0x04988 and 0x04990:
7f7f7f7f7f7f7f7f
```

11 records x 24 B = 264 B (`0x4880..0x4988`), then 8 pad bytes of 0x7F to the next object.
`+0x08` equals the part's `world_collision_body_id` for every constrained part of the donor
(11/11), e.g. record 0 body 1 = part 1 `sportsmuscle_door_f_l`.

### 5. Probe 5 -- cached-module census (the DOORS.md universe)

```
$ python tmp/freebuff/scratch/probe_doorangles5.py 2>&1 | head -12
{
 "modules": 56,
 "constraint_objects": 666,
 "instance_records": 666,
 "hinges": 606,
 "door_rows": 224,
 "door_with_hinge": 220,
 "body_match": 216,
 "other_class_hkpRagdollConstraintData": 56,
 "other_class_hkpHingeConstraintData": 4,
 "body_mismatch": 4,
 "door_no_hinge": 4
```

The 78 cached parts modules (56 with doors) reproduce G2-15's 220 hinged rows; record count
equals constraint-object count there too (666/666).

### 6. Probe 11 -- fleet sweep over all 233 entity bundles

```
$ python tmp/freebuff/scratch/probe_doorangles11.py 2>&1 | tail -14
non-ascending: []
door rows with con 335 no con 4 limited 335 other Counter()
min<=max 335 / 335
grid 335 / 335
body mismatches 5
   ('vintagesports_vehicle_parts.vmodc', 'vintagesports_door_f_l', 21, 16)
   ('vintagesports_vehicle_parts.vmodc', 'vintagesports_door_f_r', 24, 19)
   ('vintagesports_vehicle_parts.vmodc', 'vintagesports_hood', 32, 29)
   ('oldbus_vehicle_parts.vmodc', 'oldbus_trunk', 49, 50)
   ('mediumtank_vehicle_parts.vmodc', 'mediumtank_hatch', 25, 3)
modules with >1 group: {'oldjeep_vehicle_parts.vmodc': 3, 'apc_vehicle_parts.vmodc': 2, 'mediumtank_vehicle_parts.vmodc': 3, ...}
keys collisions across physics: 87 distinct module paths
behaviours {'FrontLeftDoor': 88, 'FrontRightDoor': 64, 'RearLeftDoor': 26, 'RearRightDoor': 34, 'Trunk': 25, 'Hood': 36, 'RearDoor': 8, 'CenterRightDoor': 10, 'CenterLeftDoor': 8, 'TurretDoor': 4, 'MissileHatch': 16, 'LeftWing': 5, 'RightWing': 5, 'CargoBayDoor': 10}
pairs by behaviour/limits sample: [(('FrontLeftDoor', 0, 80.0), 67), (('FrontRightDoor', 0, 80.0), 59), (('RearRightDoor', 0, 80.0), 28), (('Hood', 0, 30.0), 24), (('RearLeftDoor', 0, 80.0), 19), (('MissileHatch', 0, 150.0), 16), (('Trunk', 0, 80.0), 15), (('FrontLeftDoor', 0, 90.0), 9)]
```

Two probe artefacts were fixed in the real script, not in the data:

1. the sweep keyed cars by module *basename*, so `rebel/`, `signature/` and `dlc` copies of
   a module collapsed; the script keys by `(module path, sha1)` and reports 88 cars;
2. `mediumtank_hatch`'s apparent 25-vs-3 body mismatch came from reading `phys[0]`; the
   cargo-tank plane bundle carries **both** `cargotransport.physicsc` and
   `mediumtank.physicsc`, so `phys[0]` is the plane's. The script picks the physics member
   named `<module stem>.physicsc` (88/88 cars), which gives `mediumtank.physicsc` and a
   body match (25 = 25). Confirmed below.

```
$ timeout 300 python -c "..." # list physics members of the two bundles
['models/jc_vehicles/01_land/v0201_car_capstone_mediumtank/mediumtank.physicsc']
['models/jc_vehicles/02_air/v4603_plane_urga_cargotransport/cargotransport.physicsc', 'models/jc_vehicles/01_land/v0201_car_capstone_mediumtank/mediumtank.physicsc']
```

The eighth line of the same probe (as captured) also printed the plane entry, which is why
the probe count was 335/5 and the final pass is 334/4: the plane's duplicate of the tank's
hatch door row was counted against the wrong physics file.

### 7. Probe 14 -- G2-15 cross-check

```
$ python tmp/freebuff/scratch/probe_doorangles14.py 2>&1 | tail -40
... (mirror-pair statistics; not used as an oracle: some left/right pairs differ by 10 deg
     and some pivots differ by 0.04 m, so mirror symmetry is not fleet-wide) ...
--- cross-check DOORS.json
donor v0300 Serpente (civilian) 3
    sportsmuscle_door_f_l 0 hkpLimitedHingeConstraintData 0.0 80.0 [0.0, -1.0, 0.0]
    sportsmuscle_door_f_r 2 hkpLimitedHingeConstraintData 0.0 80.0 [0.0, 1.0, 0.0]
    sportsmuscle_hood_signature 8 hkpLimitedHingeConstraintData 0.0 70.0 [1.0, 0.0, 0.0]
apc v0200 APC (military) 5
    apc_door_c_l 6 hkpLimitedHingeConstraintData 0.0 100.0 [0.0, -1.0, 0.0]
    apc_door_c_r 7 hkpLimitedHingeConstraintData 0.0 100.0 [0.0, 1.0, 0.0]
    apc_door_r 8 hkpLimitedHingeConstraintData 0.0 95.0 [0.001, -1.0, 0.002]
    apc_hatch_l 9 hkpLimitedHingeConstraintData 0.0 130.0 [1.0, 0.0, 0.0]
    apc_turret_hatch 13 hkpLimitedHingeConstraintData 0.0 130.0 [1.0, 0.0, 0.0]
monorail v5603 monorail missile car 16
    monorailmissilecar_missile_hatch_l_01 0 hkpLimitedHingeConstraintData 0.0 150.0 [0.0, -0.0, -1.0]
    ... (15 more hatches, all 0..150 on +-Z) ...
mediumtank v0201 medium tank 1
    mediumtank_hatch 1 hkpLimitedHingeConstraintData 0.0 130.0 [1.0, 0.0, 0.0]
```

The shipped script replays all 25 of those rows and agrees on constraint index, class and
both limits (oracle `agrees_with_g2_15_samples`, 25/25).

### 8. Probe 15 -- grouping preconditions

```
$ python tmp/freebuff/scratch/probe_doorangles15.py 2>&1 | tail -10
modules seen 116
part_index != array pos 0 []
duplicate door indices []
stride bad 0 []
```

`part_index` equals the array position in every module, no `door_parts[]` duplicates, and
the 24 B record stride fits every array (0..15 B pad).

### 9. Probe 16 -- raw per-payload door counts vs the published JSON

```
$ python tmp/freebuff/scratch/probe_doorangles16.py 2>&1 | head -6
entities by module count {1: 232, 2: 1}
raw door rows (unique module payloads) 671 payloads 88
json rows 338 cars 88
DIFF ('models/jc_vehicles/01_land/v0000_car_autostraad_oldjeep/civilian/oldjeep_vehicle_parts.vmodc', 'a0d5a72d') raw 12 json 6
DIFF ('models/jc_vehicles/01_land/v0000_car_autostraad_oldjeep/oldjeep_vehicle_parts.vmodc', '25dfa021') raw 18 json 6
DIFF ('models/jc_vehicles/01_land/v0001_car_autostraad_armoredtruck/armoredtruck_vehicle_parts.vmodc', 'a1d0ae0f') raw 10 json 5
```

`raw` is incremented once per entity that bundles a payload, so 671 is the variant
multiplicity (e.g. 12 = 6 rows x 2 entities); 232 entities bundle one parts module and one
bundles two (the cargo-tank plane), which is why 88 unique `(module, sha1)` payloads carry
338 rows. The `DIFF` lines are that multiplicity, not a mismatch.

### 10. Independent byte re-read (manual section parse, not `jc3hkx`)

```
$ cd E:/Modding/JC3-Batmobile && timeout 300 python -c "..."   # manual packfile section table + struct.unpack of +0xFC/+0x100
0 __classnames__ ['0x100', '0x210', '0x210', '0x210', '0x210', '0x210', '0x210']
1 __types__ ['0x310', '0x0', '0x0', '0x0', '0x0', '0x0', '0x0']
2 __data__ ['0x310', '0x9dce0', '0x9f0f0', '0xa3260', '0xa57a0', '0xa57a0', '0xa57a0']
file models/jc_vehicles/01_land/v0000_car_autostraad_oldjeep/oldjeep.physicsc size 678576 data base 0x310
0x9c2a0 min 0.000 deg, max 80.000 deg
0x9c570 min 0.000 deg, max 80.000 deg
0x9c840 min 0.000 deg, max 80.000 deg
0x9c970 min 0.000 deg, max 80.000 deg
0x9d8b0 min 0.000 deg, max 75.000 deg
0x9d120 min 0.000 deg, max 30.000 deg
```

Those six are the oldjeep civilian's four doors (0..80), trunk (0..75) and hood (0..30) -
identical to the JSON rows for `oldjeep_door_f_l/_f_r/_r_l/_r_r`, `oldjeep_trunk`,
`oldjeep_hood`, read through a separate code path.

### 11. Final runs

```
$ cd E:/Modding/JC3-Batmobile && timeout 580 python Tools/scripts/jc3_door_angles.py --write
wrote Research/JC3Grab/DOOR_ANGLES.md and Research/JC3Grab/DOOR_ANGLES.json
cars 88 / door rows 338 (hinged 334) / entities 233 / records 1086
oracles 21/21
```

```
$ cd E:/Modding/JC3-Batmobile && timeout 580 python Tools/scripts/jc3_door_angles.py --check
OK cars 88 / door rows 338 (hinged 334) / entities 233 / records 1086; md+json byte-identical to a fresh decode
oracles: {"agrees_with_g2_15_samples": true, "body_id_mismatch_set_unchanged": true, "body_ids_match_mostly": true, "cars_have_physics": true, "constraint_index_in_range": true, "door_rows_resolve_to_a_part": true, "every_door_hinge_is_limited": true, "hinge_factor_is_one": true, "hinge_frame_orthonormal": true, "hinge_limits_on_half_degree_grid": true, "hinge_limits_within_pi": true, "hinge_min_le_max": true, "no_anomalies": true, "record_count_equals_constraint_objects": true, "record_pointers_are_constraint_objects": true, "record_sentinel_constant": true, "record_set_equals_constraint_objects": true, "record_stride_fits_array": true, "records_ascending_by_offset": true, "serpente_vanilla_limits": true, "vanilla_bundle_members_match": true}
```

## UNKNOWNs

- **What drives a door.** The parts module stores no open rate, no animation curve and no
  interaction for the part; the entity containers hold no animation member (G2-15 §4). The
  open range is the authored hinge limit, not a measured swing. Where a code-side driver
  would be is not in these files.
- **Meaning of the constraint record's +0x0C u32.** It is 0x7fffffff in all 1086 records,
  decoded as a constant, but no Havok 2014 header in this project names the field (it may be
  a second-body index / world anchor, but that is not proven here).
- **Field names inside the 24 B record.** The stride, the typed `+0x00` pointer and the
  constant tail are decoded by pattern (stride fits the array, pointer resolves to a
  `*ConstraintData`, `+0x08` tracks part body ids), not from a header. Only the pointer and
  `+0x08` are used.
- **Why four parts' body ids differ from their record's body u32** (vintagesports
  door_f_l/door_f_r/hood, oldbus_trunk). The hinge is still the one the module's
  `constraint_index` names (pivot mirrors the opposite door, limits equal), but the two
  numberings are not one space and the body enumeration is not decoded. Record `+0x08` was
  therefore used as a cross-check (330/334) and not as the lookup key.
- **Frame space of the hinge axis/pivot** (body-local vs parent). Comparing pivots to part
  centroids is not consistent fleet-wide, so no such comparison is claimed or used as an
  oracle.
- **Which frame column is the joint's free axis.** G3-10e §2 leaves that UNKNOWN; the axis
  column in the outputs is frame A row 0, the convention G2-15 used.
- **Open range of the four hinge-less rows** (`constraint_index` -1): no hinge exists, so no
  range is authored in the files.
- **Vehicles outside `INDEX.json`'s 233 `jc_vehicles` bundles.** Nothing else was scanned;
  a vehicle absent from the index is absent from the outputs.

## Notes / scope

- Inputs were read-only: `D:/Games/Just Cause 3` archives through `Research/JC3Grab/INDEX.json`,
  `E:/Modding/_gamedata/JC3grab/vanilla_v0300.ee`, and existing `Research/Tools` files
  (`DOORS.json` as a cross-check only). No game process was started, nothing was installed,
  no `Builds/` file was touched, nothing was committed.
- Readings are data-section relative offsets, the convention G3-10e used
  (`hknpPhysicsSystemData +0x50`, hinge `+0x0FC`); the absolute file offset of a hinge is
  `data base + data_offset`, and the two limit addresses are given per row as `min_at` /
  `max_at` in the JSON.
- The fleet is 233 entity bundles (156 land / 42 air / 35 sea entities from
  `editor/entities/jc_vehicles/<class>/...`); 88 cars carry `door_parts[]` (55 land, 25 air,
  8 sea), 338 rows, 334 hinged. G2-15's 220 hinged rows are the subset visible through the
  78 cached module files; this pass reads every entity bundle, hence the larger set.
- The script is rerunnable: `--write` regenerates both outputs, `--check` rebuilds in memory,
  compares both files byte-for-byte and re-runs the 21 oracles.
