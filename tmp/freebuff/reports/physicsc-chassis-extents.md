# physicsc-chassis-extents - the shipped Batmobile `.physicsc`: extents, hull oracle, BmAK chassis gap

## STATUS

**done - the G3-12c extents decoder runs unchanged on `Working/Collision/batmobile.physicsc`
(340,368 B, sha256 `192c12479d81da6e...`, 430 objects, 54 hulls, 22 compounds). Body hull at
`0x5250` is `349.500 x 227.100 x 702.500 cm` (x, y, z) and matches B-10's body bbox to 9.537e-08 m.
1,232 child-hull vertices tested: every one inside its compound's stored AABB (overshoot
0.0000 cm). Every stored compound AABB is the children's union plus at most 1.0000 cm - the child
convex radius - with nothing poking out. Against BmAK's drivable chassis box 690.305 x 374.536 x
207.5 cm the differences are **-25.036 cm in width, +19.600 cm in height, +12.195 cm in length**,
under the ASSUMED axis pairing that `COLLISION_GEOM.md` itself declines to prove. 9/9 checks pass,
`--check` exits 0.**

Files written:

- `Tools/scripts/bm_extents_check.py` (`--write` / `--check`; imports `jc3hkx`, never edits it)
- `Working/Collision/BM_EXTENTS_CHECK.md` (11,008 B - the extent table, the oracles, the comparison)
- `tmp/freebuff/reports/physicsc-chassis-extents.md` (this card)

Read-only on every input; `Working/Collision/batmobile.physicsc`, `bm_collision.json` and
`COLLISION_GEOM.md`/`.json` were not modified, and no game was launched or attached (§3).

---

## 1. Applying the decoder

`Tools/scripts/jc3_physicsc_extents.py` was written for five vanilla files. Its reader
(`jc3hkx.Packfile`, `decode_polytope`, `decode_compound`, `shape_aabb`, `transform_aabb`) takes any
Havok `hk_2014.1.0-r1` packfile, so this card imports those functions rather than copying them -
the shipped file goes through exactly the code that decoded the vanilla fleet.

What the file holds (**decoded** from the class table and fixup table):

| quantity | value |
|---|---|
| bytes | 340,368 |
| sha256 | `192c12479d81da6e9515b42d...` |
| objects | 430 |
| hulls (`hknpConvexPolytopeShape`) | 54 |
| compound shapes | 22 |

## 2. The body extents

- body hull object at data offset **`0x5250`** - the only hull whose decoded vertex bounds match
  B-10's `body_bbox_m`; found by search, not by trusting the card
- bounds `[-1.748, 0.091, -3.42] .. [1.747, 2.362, 3.605]` m (**decoded**: 16-byte `hkVector4`
  vertices at `+0x50 + 16i`)
- size **349.500 x 227.100 x 702.500 cm**
- agrees with B-10's 3.495 x 2.271 x 7.025 m to **9.537e-08 m** - the hull really is the box B-10
  says it wrote
- convex radius (field `+0x14`) **1.6763 cm**

Hosting compound `0x4a920` (`hknpDynamicCompoundShape`) stores
`[-1.748, 0.091, -3.42] .. [1.747, 2.372, 3.605]` = 349.500 x 228.100 x 702.500 cm: it contains
every child and exceeds their union by 1.0000 cm.

## 3. The oracles

**O1 - containment (the brief's second requirement).** For each compound, every child hull's
vertices are transformed by the instance basis/translation (`p' = M^T p + t`, the reading
`jc3hkx.transform_aabb` pins from the data) and tested against the stored AABB at `+0x80`/`+0x90`:

| | result |
|---|---|
| compounds | 22 (all with hull children) |
| child-hull vertices tested | **1,232** |
| worst overshoot | **0.0000 cm** |
| tolerance | that child's convex radius + 1e-3 m |

**O2 - is the stored box the union (the brief's first requirement)?** Two records compared: the
stored AABB and the union of the children's bounds in compound space. Hull children are bounded by
their decoded vertices (tight under rotation); a mesh child falls back to its stored AABB, because
its vertices are the undecoded frame. Result: no child pokes out of its compound's box
(worst **0.0000 cm**), and the box exceeds the union by at most **1.0000 cm** - exactly the child
convex radius, the same relation G3-12c measured on the five vanilla files (their worst "missing"
was also 0.0100). Per-compound detail is in the document's table.

**O3** every stored AABB is non-degenerate: 0 degenerate boxes.

Two of my own first-pass numbers were wrong and are worth naming, because the fix changed the
answer:

1. **The sign of the union comparison was inverted.** I first reported a "1.0 cm shortfall", i.e.
   children outside the box. They are not: the box is 1 cm *larger*, which is the Havok relation.
   The corrected direction is what the table above reports.
2. **A phantom 2.02 cm outlier came from unioning transformed child AABBs.** Transforming a box's
   8 corners through a rotation over-estimates the child's extent; unioning decoded vertices
   removes it (compound `0xc570` drops from 2.0233 cm to 1.0000 cm). The tool now uses the tight
   bound for hulls and says where it cannot.

A third, smaller one: `COLLISION_GEOM.json` stores the chassis spans **sorted**, so the md-vs-json
cross-check had to sort before comparing (it was 4,828 mm off before); it now agrees to 0.36 mm,
which is that card's rounding.

## 4. Batmobile body vs the BmAK drivable chassis box

BmAK side (**decoded**), `Research/BatmobileGrab/COLLISION_GEOM.md:29`, `RB_BodySetup` export
169750, AggGeom, bone `Batmobile_Chassis`, box 0: **690.305 x 374.536 x 207.5 cm**.

### 4.1 Axis-free (sorted spans) - what that card itself does

| span | Batmobile body (cm) | BmAK chassis (cm) | difference |
|---|---:|---:|---:|
| smallest | 227.100 | 207.500 | **+19.600 cm** |
| middle | 349.500 | 374.536 | **-25.036 cm** |
| largest | 702.500 | 690.305 | **+12.195 cm** |

### 4.2 Per axis, under an ASSUMED pairing

| axis | Batmobile body (cm) | BmAK chassis (cm) | difference |
|---|---:|---:|---:|
| x - width | 349.500 | 374.536 | **-25.036 cm** |
| y - height | 227.100 | 207.500 | **+19.600 cm** |
| z - length | 702.500 | 690.305 | **+12.195 cm** |

The pairing (JC3 x↔BmAK Y, y↔Z, z↔X) is **ASSUMED**, not decoded: `COLLISION_GEOM.md` says
"Frame axes are not proven" and that the chassis box's rotation "is not decoded". The two tables
agree as a multiset, so the assumption cannot be hiding an axis swap - if the mapping were
different, the same three numbers would be attached to different axes, and the sorted comparison
in 4.1 is the axis-free statement.

Reading: the Batmobile's hull is **25.0 cm narrower, 19.6 cm taller and 12.2 cm longer** than
BmAK's chassis box. That is not a drift: B-10 sized the hull to DIM-1's render-body bbox, and the
BmAK box additionally carries a centre offset `[9.0, 0.0, 106.75]` cm that a symmetric body bbox
does not reproduce.

## 5. Commands (verbatim)

```
$ cd E:/Modding/JustCause3/JC3-Batmobile && PYTHONIOENCODING=utf-8 python Tools/scripts/bm_extents_check.py --write; echo "write_exit=$?"; PYTHONIOENCODING=utf-8 python Tools/scripts/bm_extents_check.py --check; echo "check_exit=$?"
wrote Working/Collision/BM_EXTENTS_CHECK.md (11008 chars), 9/9 checks pass
write_exit=0
CHECK PASS
check_exit=0
```

The failing intermediate runs, kept so the final pass cannot hide them:

```
$ python Tools/scripts/bm_extents_check.py --write
wrote Working/Collision/BM_EXTENTS_CHECK.md (10372 chars), 7/9 checks pass
FAIL O2: each stored AABB is the children's union (+ convex radius): 22 compounds, worst shortfall 1.0000 cm, worst excess over the union 2.0233 cm
FAIL COLLISION_GEOM.md's chassis extents equal COLLISION_GEOM.json's sorted spans: max difference 4828.050000 mm
write_exit=1
```

and after the sign fix but before the tight-vertex union:

```
wrote Working/Collision/BM_EXTENTS_CHECK.md (10812 chars), 7/9 checks pass
FAIL O2: ... the union pokes out of its stored box by at most 1.0000 cm and the stored box exceeds the union by at most 2.0233 cm
FAIL the body hull's compound contains it, exceeding its bounds by no more than the radius: compound @0x4a920: stored box exceeds the hull bounds by 0.0000 cm (hull radius 1.6763 cm), union pokes out by 1.0000 cm
```

```
$ PYTHONIOENCODING=utf-8 python -c "... probe of 0x8f20 / 0x4a920 children ..."
compound 0x8f20 stored [-1.0423, 0.1745, -2.6015] [1.055, 0.5105, -1.9735]
  child 0x93f0    hknpConvexPolytopeShape  rad  1.000 cm  out -1.000 cm  min [-0.1235, 0.3403, -2.5915] max [0.1614, 0.5, -2.5438]
  child 0x9a30    hknpConvexPolytopeShape  rad  1.000 cm  out -1.000 cm  min [-1.0323, 0.1845, -2.435] max [-0.7177, 0.4952, -2.0312]
  ...
compound 0x4a920 stored [-1.748, 0.091, -3.42] [1.747, 2.372, 3.605]
  child 0x5250    hknpConvexPolytopeShape  rad  1.676 cm  out  0.000 cm  min [-1.748, 0.091, -3.42] max [1.747, 2.362, 3.605]
```
`out` negative = the child is inside its box; that probe is what showed the direction was inverted.

```
$ sha256sum Working/Collision/batmobile.physicsc | cut -c1-24
192c12479d81da6e9515b42d
```

## 6. UNKNOWN (with what was tried)

1. **The axis pairing** between the BmAK box and the JC3 body. `COLLISION_GEOM.md` states the axes
   are not proven and the chassis box's rotation is not decoded, so no source says which BmAK
   extent is width. Tried: the axis-free sorted comparison (4.1), which needs no pairing; the box
   centre `[9.0, 0.0, 106.75]` is consistent with Z-up and a ~207.5 cm tall box, but consistency is
   not proof; the constraint records in the same card carry no basis for the box.
2. **The unit.** The file stores game units; this project reads JC3 vehicle files as metres and the
   3.495 m body length is consistent with a car, but no byte states a scale. The cm figures are
   **derived** by x100 on that convention (G3-12c records the same UNKNOWN).
3. **Whether the hull *should* equal the BmAK chassis box.** BmAK's box is the drivable body in the
   Arkham engine; the JC3 hull is sized to the render body (B-10/DIM-1). Nothing in either package
   says the two must match, so section 4 measures a difference rather than finding a defect.
   Settling it would re-open B-10's sizing decision, which is not this card.
4. **The chassis box's rotation.** Undecoded; with a rotation the 690 x 375 x 208 cm box could
   project differently onto the car frame.
5. **Mesh-child bounds.** For a compound child that is a mesh rather than a hull, O2 uses the
   stored AABB because the mesh vertices' de-quantisation frame is unpinned (G3-12c UNKNOWN 2). No
   compound in this file needed it beyond one mesh child, and O1 does not use mesh vertices at all.
6. **Play behaviour** - untested, the test ban stands (§3).
