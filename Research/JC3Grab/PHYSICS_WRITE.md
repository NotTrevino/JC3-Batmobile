# Writing a `.physicsc` - the G2-30 spike

Decoded and written by `Tools/scripts/jc3hkx.py write`. **The donor can be read, re-emitted
byte for byte, and a hull inside it can be replaced - with the file still passing every
invariant the reader knows.** That is the whole question this card asked, and the answer is
yes, with two hard limits that are stated in §6-§7 rather than papered over.

The mechanism is not a guess: the data section of a JC3 `.physicsc` is **fully partitioned
by typed objects** (430 objects, 0 gap between them, every extent a multiple of 16,
the file ending exactly at the last object). So the section can be laid out again from
per-object blobs, every fixup can be remapped, and the three tables plus the `__data__`
section record can be regenerated. That is what makes a size change possible; an in-place
patch would only work while a hull keeps its vertex and plane counts.

## 1. The four cases

| case | what it proves | in -> out | verdict |
|---|---|---|---|
| round trip `donor` | `hull_bytes()` re-emits all 54 hulls from their decoded values and the file is unchanged | 340,368 -> 340,368 B | identical / PASS |
| round trip `assembled` | `hull_bytes()` re-emits all 54 hulls from their decoded values and the file is unchanged | 340,368 -> 340,368 B | identical / PASS |
| remap stress | every object, array and table shifted by +16 B, so all 430 objects and every fixup move | 340,368 -> 340,384 B | PASS |
| scaled hull | one hull scaled x1.659566 about its centre, the parent AABBs recomputed | 340,368 -> 340,368 B | PASS |
| size-changing replace | a 704 B hull slot holds a 1776 B hull, so everything after it shifts | 340,368 -> 341,440 B | PASS |

`shape_checks()` (the same pass `check --all` uses) reports **0 violations** on all four
outputs, every pointer still resolves, and the decoded object graph changes only in the
objects the case was given.

## 2. The file, byte for byte

| item | value |
|---|---|
| source | `Builds/test-091/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc` |
| size / version | 340,368 B, `hk_2014.1.0-r1` |
| sections | `__classnames__` @0x100 (528 B), `__types__` @0x310 (0 B), `__data__` @0x310 (339,584 B) |
| objects | 430, **0 gap** between consecutive extents |
| data section | objects 0..322,288, then local 322,288..325,008, global 325,008..334,416, virtual 334,416..339,584 |
| fixups | 339 local, 765 global, 430 virtual |
| collision | 54 convex hulls (38,416 B of hull blocks), 22 compounds, 112 instances |
| classes | `CPfxPartIndexProperty` 98, `hkGeometry` 36, `hkRefCountedProperties` 92, `hkRootLevelContainer` 1, `hknpConvexPolytopeShape` 54, `hknpDynamicCompoundShape` 20, `hknpDynamicCompoundShapeData` 20, `hknpExternMeshShape` 18, `hknpExternMeshShapeData` 18, `hknpPhysicsSceneData` 1, `hknpPhysicsSystemData` 1, `hknpShapeMassProperties` 56, `hknpStaticCompoundShape` 2, `hknpStaticCompoundShapeData` 2, `hkpLimitedHingeConstraintData` 9, `hkpRagdollConstraintData` 2 |

## 3. Round trip (Do step 1)

`hull_bytes(pf, off)` rebuilds a hull object from what `decode_polytope()` returns - the
vertex block, every plane slot (unused sentinel included) and `convex_radius` - and copies
only the parts the reader does not decode (the header's unnamed `u16`s, the block between
planes and faces, the face table, the index block, the `0x7F` padding). A round trip with no
arguments therefore tests the *decoder*, not a file copy.

| file | bytes | sha256 in | sha256 out | identical | hulls re-emitted |
|---|---|---|---|---|---|
| `sportsmuscle.physicsc` (`Builds`) | 340,368 | `1b90daefdc9660b4…` | `1b90daefdc9660b4…` | **yes** | 54 |
| `sportsmuscle_true.physicsc` (`Working`) | 340,368 | `6a0e7e13efb329a3…` | `6a0e7e13efb329a3…` | **yes** | 54 |

The second file is the assembly variant: same 340,368 B, and it differs from the donor in
**2 bytes over 1 range(s)** (@14,664+2), one `f32` at `hknpPhysicsSystemData` +0x3598 = `body_entries[22]` +0x38: -2.569999933242798 -> -2.5699000358581543.
So it is **not** a re-baked wheel-station table - and `stations()` reads **0** station set from either file.
The station quads of a true-scale build therefore do not come from this file's typed
field, which is what the plan in §7 means by "same station table": the writer copies the
bytes it was given and never rebuilds them.

## 4. The remap stress

Inserting 16 filler bytes at data offset 0 forces *every* offset to move: all
430 objects, the three fixup tables and the `__data__` section record.
Rebuilding exactly those - and leaving every pointer slot zero, as the file does - gives a
file that re-reads with
**0 violations** and a decoded graph identical object-for-object: 340,368 -> 340,384 B.
This is the case an in-place patcher cannot do, and it is why a hull with a different vertex
count is writable at all.

## 5. A scaled hull and a replaced hull (Do step 2)

The test hull is `sportsmuscle_wheel_f_l` @ `0xb5d0` - 20 vertices, 12 planes,
704 B, box height 0.8225 m, centroid at the part origin. The factor is **1.659566**
= Batmobile tyre Ø 1.365 m (`Research/BatmobileGrab/TYRES.md`) / 0.8225 m, i.e. two measured
file values, not a chosen number.

| case | before | after |
|---|---|---|
| scale x1.659566 | box [0.2958, 0.8225, 0.7822] m, r 0.01 | box [0.4909, 1.365, 1.2982] m, r 0.016596 |
| bytes touched | - | **252 B over 69 ranges** (@47,348+3, @47,408+3, @47,412+3, @47,416+4, @47,424+3, @47,428+7 …), 2 parent compound AABB(s) |
| replace the `sportsmuscle_wheel_f_l` slot with the `sportsmuscle_body` hull block | 704 B, 20 v / 12 p | 1776 B, 36 v / 47 p, file 340,368 -> 341,440 B |

Scaling the hull x1.659566 moves its box out of the parent compound's stored AABB. Without
recomputing the ancestors the file **fails** - the counter-example is kept in the numbers:

```
@0x484f0: a child AABB is outside the compound AABB
```

So `compound_aabb_edits()` moves every ancestor's `+0x80`/`+0x90` box by exactly as much as
its children moved (2 compound(s) here), keeping the margin the file
authored the box with - the stored box is the children's union inset by the convex radius
(the root sits 0.011 m inside its union on every axis), so `missing` and `overshoot` stay what
they already were. That is the only value the writer *derives* rather than copies.

## 6. What the writer may and may not change

| may | why |
|---|---|
| hull vertices, plane normals/distances, `convex_radius` | decoded, and the plane relation
  `max(n.v) + d == 0` re-checks after the write (`convex 54/54`) |
| the size of a hull object | objects are contiguous and 16-aligned, so the section is re-laid-out
  and every fixup remapped |
| a compound's AABB | derived from its children |
| the wheel-station data | copied, not rebuilt: it lives in `hknpPhysicsSystemData`, outside
  every hull block |

| may **not** | why |
|---|---|
| add or remove objects | the three fixup tables keep their counts, so the object count is fixed;
  a new hull must replace an existing slot (or the tables must be grown - see §7 step 4) |
| a *brand-new* hull | the face table reads as one 4-byte record per plane for **54/54** hulls, but only once a 16-byte-aligned prefix of 0 B on 17/16 B on 16/32 B on 9/48 B on 12 is skipped, and that block's content has no reading (nor the record's `min` byte) |
| an `hknpExternMeshShape` | its vertices are 3x u16 quantized and the de-quantization frame is
  still not pinned (`SHAPES.md`, *Still open*) |
| `hknpShapeMassProperties` | layout not decoded (56 objects in this file) |

## 7. The plan for a Batmobile hull set (Do step 3)

What the donor gives us to copy: **22 compounds / 112 instances** wiring shapes to the 42
parts of `PARTS_TABLE.jsonl`, with the body part carrying an `hknpExternMeshShape` and every
rigid part - the 4 wheels, seats, lights, grill, hood, trunk, windows, mirrors, signal and
plate parts - a convex hull. What BmAK gives us to build from: **32 bodies, each a single box**
(`Research/BatmobileGrab/PHYSICS.md`), of which 8 are wheels/suspension, 1 turret, 1 cockpit,
2 doors, 1 jet fin - **and no chassis body at all**, so the body hull has to come from a convex
decomposition of `Batmobile_V2` itself. Size and mass targets are DIM-1/DIM-3.

| step | input | method | check that proves it |
|---|---|---|---|
| 1 | the unnamed prefix block (0 B on 17 hulls, 16 B on 16 hulls, 32 B on 9 hulls, 48 B on 12 hulls) and the face record's `min` byte (1 on 31 hulls, 0 on 17 hulls, 3 on 16 hulls, 2 on 15 hulls) | byte analysis, `decode_polytope` |
  both decoded, i.e. a hull authored from a mesh becomes writable (the record layout itself
  already fits 54/54 hulls) |
| 2 | 4 wheel hulls (704 B each, identical topology) | scale + translate the existing block
  through `T(p)` (`bat_assemble.py`, R2), write with `hull_bytes()` | `check` 0 violations and
  station quads unchanged |
| 3 | 8 BmAK wheel/suspension boxes, 2 door boxes, turret, cockpit, fin | each box becomes a
  box hull in the donor *slot* of the part it replaces, so the count stays 54 | `convex`,
  `index_ok`, `aabb_ok`, `union_ok` all 100% |
| 4 | the body | either a convex decomposition of the body mesh as N new hulls (needs the
  fixup tables to grow) or one hull per donor body-part slot | the same invariants plus a
  volume/clearance comparison against the render mesh |
| 5 | `Working/TrueScale/stations.json` | left alone: the station quads stay
  `physics_stations.py`'s output, which the assembly already carries | the 17-entity
  `land_global` cross-check stays green |
| 6 | the whole file | repack with `eetoc` (+ `update_toc_offset.py` if the size changed) |
  the `.ee` toc hash matches and the build loads (phase Q, in-game) |

Steps 2 and 3 use only what this card proved: same-topology or donor-slot hull replacement with
a full remap. Step 4 is the one that needs more (either step 1 or a table-growing writer) and
is where the body, i.e. most of DIM-4, still waits.

## 8. What this changes for T-P3 / T-CO2 / T-CO3

All three rows were `blocked` with the same `why`: *no `.physicsc` writer*. That reason is
**gone**: a hull can be written and the result re-reads clean. What each row now needs is a
value, not a capability, so the rows stay for T-22 (`T-22 · Collision translation (only if
G2-30 succeeded)`) to resolve - this card does not edit `T_ROWS.jsonl`.

| row | was | now |
|---|---|---|
| T-P3 | blocked: *no `.physicsc` writer* | unblocked for hull-based collision; the 32 BmAK
  boxes can go into hull slots - the body chassis mesh (`hknpExternMeshShape`) still cannot |
| T-CO2 | blocked: same | unblocked the same way; the largest box (211x51x109 cm) is a hull
  and needs no new layout |
| T-CO3 | blocked: same | `has_world_collision_shape` can be honoured by reusing a donor hull
  slot; a *new* shape per part additionally needs step 4 |

## 9. UNKNOWNs

1. **The block between the plane block and the face table** - 0 B on 17 of 54 hulls, 16 B on 16 of 54 hulls, 32 B on 9 of 54 hulls, 48 B on 12 of 54 hulls. Its contents vary (floats in one
   hull, `0xFF` words in another) and it is copied, never built.
2. **The face record's `min` byte.** `first`/`count` are proven - one 4-byte record per plane
   partitions the index list on **54/54** hulls - but `min` takes 1 (31 hulls), 0 (17 hulls), 3 (16 hulls), 2 (15 hulls) with no reading yet.
3. **`hknpExternMeshShape` vertex quantization**: 3x u16 per vertex, frame unpinned, so the
   chassis panel mesh cannot be re-authored from a new body mesh.
4. **`hknpShapeMassProperties` / the 80- and 64-byte body entries**: counted and sized, not
   decoded, so inertia and the shape-to-body binding are untouched by a hull write.
5. **Runtime acceptance.** Every check here is the reader's; whether Havok and the game accept
   a written file is a phase-Q question and **not** claimed.

## 10. Commands, files, revert

```
python Tools/scripts/jc3hkx.py write --write    # this report + PHYSICS_WRITE.json + blobs
python Tools/scripts/jc3hkx.py write --check    # re-derive and compare
python Tools/scripts/jc3hkx.py check --all      # the standing gate, unchanged
```

Written `.physicsc` blobs (game data, outside the repo - R10): `_JC3grab/hkx/write/roundtrip_donor.physicsc`, `_JC3grab/hkx/write/roundtrip_assembled.physicsc`, `_JC3grab/hkx/write/shift16.physicsc`, `_JC3grab/hkx/write/scale_wheel.physicsc`, `_JC3grab/hkx/write/replace_hull.physicsc`)

Revert: delete the writer block + `write` command from `jc3hkx.py`, this file,
`PHYSICS_WRITE.json`, `_JC3grab/hkx/write/`, the README section and Files row; §12 back to
`| G2-30 | todo | |`; truncate `MODLOG.md` at the G2-30 intended-change heading.
