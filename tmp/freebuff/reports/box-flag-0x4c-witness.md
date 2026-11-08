# Witness - `FKBoxElem+0x4C` box flag census

**Task:** chase `BOX_FLAG_0X4C` to a finish: walk the cooked PhysicsAsset exports of the
other vehicles and characters, list every box whose `0x4C` byte is nonzero, and name the
flag only if one property is shared by all hits and absent from every zero box.

**Status: complete. Verdict: UNKNOWN.**

| item | where |
|---|---|
| tool (`--write` / `--check`) | `Tools/scripts/box_flag_0x4c.py` (new) |
| record | `Research/BatmobileGrab/BOX_FLAG_0X4C.md` (new, 131,224 B) |
| this witness | `tmp/freebuff/reports/box-flag-0x4c-witness.md` |

Read-only on `E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole`; no game process
started, no game file written, no git commit/push.

## What was asked, and the answer

The starting points named by the card were used, not re-invented:

- box table: `tmp/freebuff/reports/G3-01b-boxes.md` - box = `TM` struct + three FULL
  extents (0x40/0x44/0x48) + a `BoolProperty` word at 0x4C, 118 bytes; the three published
  boxes are `169750` box 0 `0x40`, box 1 `0x00`, `169751` box 0 `0x00`.
- layout: `tmp/freebuff/reports/chase-G3-01b-boxes-u2.md` -
  `[nSphere][spheres][nBox][boxes][nSphyl][sphyls][nConvex][convex][9-byte zero footer]`.
  The tool calls that card's own parser, `grab_collision_shapes.parse_aggregate()`, so the
  walk cannot drift from the settled layout.
- the open item: `tmp/freebuff/reports/chase-G3-01b-boxes-u5.md`, U-3 (line ~136) left the
  0x4C bool's meaning out of scope.

**Answer.** Across the fleet, the `0x4C` word takes nine values (`0x00` to `0x40`), and
**no property is shared by all 1,068 nonzero boxes and absent from every zero box**. The
card's rule therefore forbids a name: `0x4C` stays **UNKNOWN**.

## Census (all numbers reproduced by `--check`)

| quantity | value |
|---|---:|
| `.upk` packages in the folder | 3,266 |
| packages whose name table carries `RB_BodySetup` | 861 |
| of those, fleet-named (batmobile / vehicle / playable / character / ragdoll) | 117 |
| **packages decoded** (117 fleet + 4 core) | **121** |
| `RB_BodySetup` exports with an `AggGeom` payload | 5,768 |
| exports with no `AggGeom` at all | 2,778 |
| bodies carrying at least one box | 3,079 |
| **boxes checked** | **3,563** |
| **boxes whose `0x4C` byte is nonzero** | **1,068** |
| hit bodies | 722 |
| hit packages | 8 |

Hit packages: `BmGame.upk` (14), `Startup.upk` (885), `StartupPatch.upk` (10),
`Orphan.upk` (153), `Playable_Nightwing0_SF.upk` (1),
`Showcase_Batmobiles_Jokerfied.upk` (1), `Showcase_Characters_Joker.upk` (3),
`Showcase_Vehicles_DumpsterTruck.upk` (1).

Word histogram over all 3,563 boxes:

| word | bits | boxes |
|---|---|---:|
| `0x00000000` | - | 2495 |
| `0x00000003` | 0, 1 | 939 |
| `0x00000004` | 2 | 3 |
| `0x0000000B` | 0, 1, 3 | 3 |
| `0x0000000F` | 0, 1, 2, 3 | 3 |
| `0x00000010` | 4 | 79 |
| `0x00000013` | 0, 1, 4 | 2 |
| `0x00000020` | 5 | 16 |
| `0x00000040` | 6 | 23 |

By body class: driving **42** hit boxes (`0x04` x3, `0x20` x16, `0x40` x23), visual
**1,026** (`0x03` x939, `0x0B` x3, `0x0F` x3, `0x10` x79, `0x13` x2).

Vehicles are where the nonzero values concentrate: `Batmobile_V3_Physics` chassis `0x40`,
`Red_Hood_Persuit_Vehicle_V2_Physics` `0x40`, `Coupe_Car_Physics` wheels `0x20` and
chassis `0x40`, the traffic `Generic_*` / `Vehicle_*` chassis `0x40`,
`Batmobile_Jokerfied_V3_Physics` `0x40`. Every character `Playable_*` / `Showcase_Characters_*`
package decoded here carries **zero** nonzero box words.

## The rule, applied

Word level, over 1,068 hits against 2,495 zero boxes: no property holds for all hits
(the closest, `bone_unnamed`, covers 947 of 1,068), so nothing is adopted.

Per declared bit:

| bit | mask | hit boxes | property that passes | verdict |
|---|---|---:|---|---|
| 0 | `0x01` | 947 | `bone_unnamed` (947/947 hits, 0/2,616 zeros) | correlation, not a decode |
| 1 | `0x02` | 947 | `bone_unnamed` (same 947 boxes) | correlation, not a decode |
| 2 | `0x04` | 6 | none | UNKNOWN |
| 3 | `0x08` | 6 | none | UNKNOWN |
| 4 | `0x10` | 81 | none | UNKNOWN |
| 5 | `0x20` | 16 | none | UNKNOWN |
| 6 | `0x40` | 23 | none | UNKNOWN |

Bit 6 is the case the earlier card named `bInterVehicleCollision`: all 23 boxes are on a
`*Chassis*` bone, but 54 zero boxes also sit on a chassis bone, so the rule rejects it.
Bits 0 and 1 pass only because every box that sets either is a body with no `BoneName` at
all (cooked tags omit defaults); that is a property of the body, not a meaning for the bit,
and the bits never appear apart in this corpus (`0x01` or `0x02` alone never occurs).

## Oracles actually run (8/8 PASS)

1. every decoded box comes from an `AggGeom` payload that closes on the 9-byte footer -
   3,563/3,563; 5,768 bodies close; 2,778 exports carry no `AggGeom`.
2. every box record carries three extents and a word at 0x4C - 3,563 boxes, 0 null.
3. no word sets a bit above bit 6 - none.
4. **G3-01b's three published boxes decode to the same words and extents** - `169750`
   box 0 `0x40`, box 1 `0x00`, `169751` box 0 `0x00`, extents within 0.05 cm.
5. the Batmobile's own chassis box is classed driving.
6. hits exist in more than one package - 8 packages.
7. the zero side is populated - 2,495 boxes with word `0x00`.
8. every hit box carries a driving/visual label.

Bit 0 against the decoded rotation: 2,201 identity boxes clear it and 41 rotated boxes set
it, so the earlier card's `bIsAxisAligned` ordering fails in bytes as well.

## Commands and exit codes

```
python -m py_compile Tools/scripts/box_flag_0x4c.py
-> exit 0
python Tools/scripts/box_flag_0x4c.py --write
-> scanned 3266 packages, 861 carry RB_BodySetup, decoded 121
-> wrote Research\BatmobileGrab\BOX_FLAG_0X4C.md (131224 B): 121 packages, 3563 boxes,
   1068 hits, verdict UNKNOWN
-> exit 0
python Tools/scripts/box_flag_0x4c.py --check
-> scanned 3266 packages, 861 carry RB_BodySetup, decoded 121
-> OK: 121 packages, 3563 boxes, 1068 hits, verdict UNKNOWN, 8/8 checks
-> exit 0
```

`--check` re-walks the packages, re-decodes every box, re-runs every oracle and requires
the record to come back byte-identical. It passed on the record as written.

## Evidence discipline (per AGENTS.md)

- The layout, the element size and the three published box values are cited to the two
  named reports; the tool imports u2's parser rather than re-deriving it.
- The bit names printed in the record come from `BOX_FLAGS.md`, which cites
  `_tools/BmSDK-AK/src/BmSDK/Generated/Engine/KMeshProps.g.cs`. That path **does not exist**
  in this repository (checked: `_tools` is absent), so the names are never adopted as
  evidence - they appear only beside the measured bits.
- The meaning of the word, the bit order, and runtime effect are all left **UNKNOWN**;
  §9 of the record says what would settle each.

## Limitations

- `driving` / `visual` is a derived, documented split, not an engine flag: a PhysicsAsset
  with a `*Chassis*` or `*Wheel*` bone that is not a wreck variant is a drivable vehicle rig
  (driving); wreck rigs, character ragdolls, static props and scenery are visual. The binary
  is the card's; the derivation is `classify_asset()` in the tool.
- A body with no `BoneName` tag is recorded as `None` - that is the cooked stream omitting a
  default, not a missing parse.
- Scope is the fleet: the 117 fleet-named packages that carry `RB_BodySetup` plus the four
  core packages. The other 740 hit packages are level scenery and are not decoded; the
  record states this so the exclusion is auditable.
- `muscle` / traversal collision beyond `RB_BodySetup` was not searched - the question is
  about `FKBoxElem` records, which live only in `AggGeom`.
- One package name table (`JokerBoss_B1_Cine_Ch9r_PreEnd.upk`, scenery) could not be read;
  it is listed in the record and is not a fleet package.
- `grab_collision_shapes.candidates()` under-reports on this folder (4 packages against the
  real 861), so this tool uses `grab_box_flags.candidates()` for coverage. That is a
  pre-existing bug in the u2 tool's prefilter, not in its parser.
