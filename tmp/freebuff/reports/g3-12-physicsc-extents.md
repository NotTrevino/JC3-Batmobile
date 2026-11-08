# g3-12 - JC3 `.physicsc` shape extents: decoded on five vehicle files, hull oracle passes

STATUS: **done.** The extents / AABB fields that DECODE_DEPTH6 and DECODE_DEPTH left open
("meshes FULL except the vertex frame; compounds PARTIAL because 41 parent AABBs were not explained")
are now decoded and certified on five vanilla files, one per family - car, truck, boat, tank,
motorbike. `Tools/scripts/jc3_physicsc_extents.py --check` exits 0 with 9/9 oracles and a
byte-identical rebuild of `Research/JC3Grab/PHYSICSC_EXTENTS.md`.

The oracle the brief asks for passes exactly: **6,992 decoded hull vertices over 126 compounds, every
one inside its compound's stored AABB, worst overshoot 0.0000** (tolerance = the child's own convex
radius + 1e-3). The stored box is also the children's box, not a lucky larger one: 126 of 126
compounds are covered by the children's union. So the "41 unexplained parent AABBs" in the earlier
census are explained by the child union inflated by the convex radius, on these five files.

Per file, the bytes no decoder reads are **6.55% to 13.48%** of the file: `hknpExternMeshShapeData`
(the mesh vertex frame plus its section table), `hknpShapeMassProperties` (the mass/inertia objects
G3-10c also left NAMED-ONLY on the BmAK side), `hknpStatic/DynamicCompoundShapeData`, the constraints,
and the unnamed halves of the mesh / compound headers. No AABB is in the residue.

## Files written

| file | size | what |
|---|---:|---|
| `Tools/scripts/jc3_physicsc_extents.py` | 32,135 B | decodes the five files through `jc3hkx`, runs the containment oracles, writes/checks the md |
| `Research/JC3Grab/PHYSICSC_EXTENTS.md` | 29,891 B, 337 lines | per-file extents, the oracle, the residue ranges per class, the named fields, the UNKNOWNs |
| `tmp/freebuff/reports/g3-12-physicsc-extents.md` | this report | |

Read-only inputs: `Tools/scripts/jc3hkx.py` (imported, not edited), `Tools/scripts/_lzo1x.py`,
`Tools/scripts/eetoc.py`, and the five `.physicsc` files named in section 1 of the output. No game was
run or attached to; nothing was written under a game install (test ban respected).

## The five files (all discovered on disk, no extraction needed)

| family | file | bytes | objects | hulls | compounds | meshes |
|---|---|---:|---:|---:|---:|---:|
| car | `Research/VanillaOldJeep/physics/models/jc_vehicles/01_land/v0000_car_autostraad_oldjeep/oldjeep.physicsc` | 678,576 | 794 | 90 | 45 | 40 |
| truck | `Research/UrgaRef/aaf/models/jc_vehicles/01_land/v0602_car_urga_armoredtransport/armoredtransport.physicsc` | 492,736 | 847 | 112 | 34 | 46 |
| boat | `E:/Modding/_gamedata/JC3grab/hkx/all/racingboat.physicsc` | 173,920 | 382 | 58 | 22 | 9 |
| tank | `Research/TankRef/aaf/models/jc_vehicles/01_land/v0201_car_capstone_mediumtank/mediumtank.physicsc` | 206,976 | 376 | 70 | 17 | 3 |
| motorbike | `Research/VanillaMoped/aaf/models/jc_vehicles/01_land/v3501_bike_solar_modernmoped/modernmoped.physicsc` | 207,328 | 241 | 37 | 8 | 10 |

## The decode, stated with its offsets

| field | offset | label | evidence |
|---|---|---|---|
| `hknpExternMeshShapeData.aabb_min` | +0x20 (vec4) | **decoded** | `jc3hkx.shape_aabb` reads it; five files agree that it is <= every hull vertex's axis values where the hull belongs to the chassis mesh |
| `hknpExternMeshShapeData.aabb_max` | +0x30 (vec4) | **decoded** | same |
| mesh extent | — | **derived** | `aabb_max.xyz - aabb_min.xyz` |
| `hknpStaticCompoundShape.aabb_min` | +0x80 (vec4) | **decoded** | O1: contains every child hull vertex |
| `hknpStaticCompoundShape.aabb_max` | +0x90 (vec4) | **decoded** | same |
| `hknpDynamicCompoundShape.aabb_min/max` | +0x80 / +0x90 | **decoded** | same two fields on the dynamic class (the largest compound in all five files is dynamic) |
| compound extent | — | **derived** | `max - min` per axis |
| hull extent | — | **derived** | bounds of the decoded vertex block at `+0x50 + 16i` (vertices are `hkVector4`, `w` = 0.5 + rank) |
| instance placement | +0x00/+0x10/+0x20 basis, +0x30 translation | **decoded** | `p' = M^T p + t`; the transposed reading puts rotated children outside the parent, this one does not |

The file extent (union of every stored AABB and every hull's decoded bounds) comes out as, in game
units: car `[2.1946, 2.8833, 5.0743]`, truck `[2.9585, 3.6598, 6.8335]`, boat `[2.7519, 1.9732,
11.0773]`, tank `[4.671, 4.0084, 9.1167]`, motorbike `[0.9947, 1.7575, 2.2755]`. The unit is **not**
claimed to be metres (see UNKNOWN 1).

## Oracles (9/9, `--check` recomputes each)

| oracle | result | detail |
|---|---|---|
| `o1_compounds_contain_child_hull_vertices` | PASS | car 1392 v / 0.0000; truck 1364 / 0.0000; boat 1488 / 0.0000; tank 1968 / 0.0000; motorbike 780 / 0.0000 |
| `o2_compound_aabb_is_the_child_union` | PASS | 45/45, 34/34, 22/22, 17/17, 8/8 compounds covered |
| `o3_stored_aabbs_non_degenerate` | PASS | 0 degenerate boxes over 234 stored AABBs |
| `o4_hull_blocks_tile_extent` | PASS | 0 violations (every hull's header+vertices+planes+faces+indices+pad == its extent) |
| `five_families_present` | PASS | car, truck, boat, tank, motorbike |
| `hull_vertex_oracle_is_not_vacuous` | PASS | 1392 / 1364 / 1488 / 1968 / 780 vertices actually tested |
| `every_file_has_a_stored_aabb` | PASS | 85 / 80 / 31 / 20 / 18 stored boxes per file |
| `byte_accounting_closes` | PASS | residue + tail <= file length on all five |
| `md_rebuilds` | PASS | `--check` compares the document byte for byte |

Two things I deliberately did **not** make into oracles, and why:

* **Hulls inside the render-geometry (`hkGeometry`) union** - measured, not asserted: car 0.0932,
  truck 0.0000, boat 0.2547, tank 0.9788, motorbike 0.1740 units outside. A collision hull may
  legitimately approximate a bumper and stick out of the detailed mesh; asserting it would be a guess.
* **A "file AABB" field** - there is none; the file extent is derived by union, and that derivation is
  labelled as such rather than passed off as a decoded field.

## Commands and output (verbatim)

The probe that chose the oracle (scratch, `tmp/freebuff/scratch/extents_probe.py`), excerpt - the car
section, the other four have the same shape:

```
$ cd "E:/Modding/JC3-Batmobile" && PYTHONIOENCODING=utf-8 uv run python tmp/freebuff/scratch/extents_probe.py
```

```
car Research/VanillaOldJeep/physics/models/jc_vehicles/01_land/v0000_car_autostraad_oldjeep/oldjeep.physicsc
  678576 bytes, 794 objects, lf=646368 gf=651504 vf=668256 ex=677792
  classes: {'hkRootLevelContainer': 1, 'hknpPhysicsSceneData': 1, 'hknpPhysicsSystemData': 1, 'hknpConvexPolytopeShape': 90, 'hkRefCountedProperties': 173, 'hknpShapeMassProperties': 105, 'CPfxPartIndexProperty': 156, 'hknpStaticCompoundShape': 21, 'hknpStaticCompoundShapeData': 21, 'hknpExternMeshShape': 40, 'hkGeometry': 80, 'hknpExternMeshShapeData': 40, 'hknpDynamicCompoundShape': 24, 'hknpDynamicCompoundShapeData': 24, 'hkpLimitedHingeConstraintData': 10, 'hkpRagdollConstraintData': 7}
  polytopes=90 compounds=45 meshes=40
   containment comp @36624: 20 child vertices, worst overshoot 0.0000
   containment comp @63696: 20 child vertices, worst overshoot 0.0000
   ...
   hull-vs-mesh-union: 1216 vertices, worst overshoot 0.0432  mesh union [-1.04, -0.5, -1.97]..[1.06, 2.39, 3.1]
```

Final run of the tool:

```
$ cd "E:/Modding/JC3-Batmobile" && PYTHONIOENCODING=utf-8 uv run python Tools/scripts/jc3_physicsc_extents.py --write; echo "WRITE_EXIT=$?"; echo "=== CHECK ==="; PYTHONIOENCODING=utf-8 uv run python Tools/scripts/jc3_physicsc_extents.py --check; echo "CHECK_EXIT=$?"
```

```
wrote Research\JC3Grab\PHYSICSC_EXTENTS.md
car        678576 B  objects= 794 hulls= 90 compounds= 45 meshes= 40  O1 verts= 1392 worst=0.0000 candidates=0  residue=50420 B
truck      492736 B  objects= 847 hulls=112 compounds= 34 meshes= 46  O1 verts= 1364 worst=0.0000 candidates=0  residue=49176 B
boat       173920 B  objects= 382 hulls= 58 compounds= 22 meshes=  9  O1 verts= 1488 worst=0.0000 candidates=0  residue=23444 B
tank       206976 B  objects= 376 hulls= 70 compounds= 17 meshes=  3  O1 verts= 1968 worst=0.0000 candidates=0  residue=23216 B
motorbike  207328 B  objects= 241 hulls= 37 compounds=  8 meshes= 10  O1 verts=  780 worst=0.0000 candidates=0  residue=13576 B
oracles: {"byte_accounting_closes": true, "every_file_has_a_stored_aabb": true, "five_families_present": true, "hull_vertex_oracle_is_not_vacuous": true, "md_rebuilds": true, "o1_compounds_contain_child_hull_vertices": true, "o2_compound_aabb_is_the_child_union": true, "o3_stored_aabbs_non_degenerate": true, "o4_hull_blocks_tile_extent": true}
  byte_accounting_closes: OK - {"car": [50420, 784, 678576], "truck": [49176, 752, 492736], "boat": [23444, 800, 173920], "tank": [23216, 752, 206976], "motorbike": [13576, 752, 207328]}
  every_file_has_a_stored_aabb: OK - {"car": 85, "truck": 80, "boat": 31, "tank": 20, "motorbike": 18}
  five_families_present: OK - ["car", "truck", "boat", "tank", "motorbike"]
  hull_vertex_oracle_is_not_vacuous: OK - {"car": 1392, "truck": 1364, "boat": 1488, "tank": 1968, "motorbike": 780}
  md_rebuilds: OK - "checked by --check, not here"
  o1_compounds_contain_child_hull_vertices: OK - {"car": [0.0, 0], "truck": [0.0, 0], "boat": [0.0, 0], "tank": [0.0, 0], "motorbike": [0.0, 0]}
  o2_compound_aabb_is_the_child_union: OK - {"car": [45, 45], "truck": [34, 34], "boat": [22, 22], "tank": [17, 17], "motorbike": [8, 8]}
  o3_stored_aabbs_non_degenerate: OK - {"car": 0, "truck": 0, "boat": 0, "tank": 0, "motorbike": 0}
  o4_hull_blocks_tile_extent: OK - {"car": 0, "truck": 0, "boat": 0, "tank": 0, "motorbike": 0}
WRITE_EXIT=0
=== CHECK ===
OK PHYSICSC_EXTENTS.md byte-identical to a fresh rebuild
car        678576 B  objects= 794 hulls= 90 compounds= 45 meshes= 40  O1 verts= 1392 worst=0.0000 candidates=0  residue=50420 B
truck      492736 B  objects= 847 hulls=112 compounds= 34 meshes= 46  O1 verts= 1364 worst=0.0000 candidates=0  residue=49176 B
boat       173920 B  objects= 382 hulls= 58 compounds= 22 meshes=  9  O1 verts= 1488 worst=0.0000 candidates=0  residue=23444 B
tank       206976 B  objects= 376 hulls= 70 compounds= 17 meshes=  3  O1 verts= 1968 worst=0.0000 candidates=0  residue=23216 B
motorbike  207328 B  objects= 241 hulls= 37 compounds=  8 meshes= 10  O1 verts=  780 worst=0.0000 candidates=0  residue=13576 B
oracles: {"byte_accounting_closes": true, "every_file_has_a_stored_aabb": true, "five_families_present": true, "hull_vertex_oracle_is_not_vacuous": true, "md_rebuilds": true, "o1_compounds_contain_child_hull_vertices": true, "o2_compound_aabb_is_the_child_union": true, "o3_stored_aabbs_non_degenerate": true, "o4_hull_blocks_tile_extent": true}
  ... (same nine lines) ...
CHECK_EXIT=0
```

Residue, per file (from the generated document - the "still undecoded" answer):

```
$ grep -n "are residue\|of which" Research/JC3Grab/PHYSICSC_EXTENTS.md
167:678,576 bytes: 50,420 are residue
168:(7.43%), of which 784 lie
195:492,736 bytes: 49,176 are residue
196:(9.98%), of which 752 lie
222:173,920 bytes: 23,444 are residue
223:(13.48%), of which 800 lie
251:206,976 bytes: 23,216 are residue
252:(11.22%), of which 752 lie
278:207,328 bytes: 13,576 are residue
279:(6.55%), of which 752 lie
```

The largest residue class in every file is the mesh data tail (`hknpExternMeshShapeData`: 10,528 B of
the car's 50,420), then `hknpShapeMassProperties`, the compound data blocks and the constraints; the
ranges are listed per class with data-relative offsets in section 4 of the output.

## UNKNOWNs, with what was tried

1. **The unit of an extent.** Values are game units; a car spans ~3.0 along z and a truck ~6.8, which
   is consistent with metres, but no byte states a unit. Tried: the packfile header (version, tag,
   layout rules), the section names, the shape headers - none carries a scale. So the document says
   "game units" and nothing more.
2. **The mesh vertex frame (`hknpExternMeshShapeData.packed_vertices`).** The array is located exactly
   (count, 6-byte stride proven by the gap to the next allocation), but the 3 x u16 triples are
   quantized against a frame that reproduces the minimum corner and not the extent. Tried here: the
   AABB at +0x20/+0x30 against the raw u16 triples; no affine frame maps count*6 bytes onto the box
   exactly, so the frame stays UNKNOWN and the oracle uses hull vertices, which are full floats.
3. **`hknpShapeMassProperties` mass / inertia / centre of mass.** Still NAMED-ONLY: 105 objects of 48
   bytes each on the car are in the residue. Tried: no layout in `jc3hkx.LAYOUTS` (empty list), and
   the byte pattern gives no invariant to pin a mass or tensor. This is the same gap G3-10c recorded
   from the BmAK side.
4. **The unnamed halves of the mesh / compound headers.** Named spans are +0x10..0x1C, +0x20..0x28,
   +0x60..0x70, +0x80..0xA0, +0xC0..0xC8; the rest (80-ish bytes per mesh shape, 100-ish per
   compound) did not pin to an invariant when read as flags or pointers, so nothing is claimed. The
   AABBs live inside the named part.
5. **`hknpPhysicsSystemData`'s 5th array (offset 0x50, element size unknown).** Its pointer and count
   are read, but with no element size its allocation is not credited in the byte table, so its bytes
   show up in that class's residue (2,784 B on the car). Tried: element sizes 64/80/96/112 against the
   allocation gap - none tiles it, so UNKNOWN rather than assumed.
6. **Why a hull may sit outside the render-geometry AABB** (up to 0.9788 units on the tank).
   Measured, reported, not explained by any byte read here.

Nothing in the output is filled in from general knowledge of Havok or JC3; every row is decoded with
its offset, derived with its rule, or UNKNOWN with the route above.
