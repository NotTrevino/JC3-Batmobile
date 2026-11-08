VERDICT: holds

The report's four checkable claims are correct. The **690×375×208 cm** figure is the
drivable chassis box **0** of export 169750 in `COLLISION_BOXES.md`, read as **extents
X/Y/Z in centimetres**, not the hull union in `COLLISION_CONVEX.md` (whose union is a
different triple, `[695.4123, 492.9222, 294.5026]` cm). The **316 cm** box is
`SUSP1_Wheel_Rear_Left_Mesh` in the **`PHYSICS.md` wreck data**, and `COLLISION.md` contains
no such box (its `316` hits are table row indices). All **five rows** in
`T_ROWS.jsonl` say exactly what the report says they say. There is **no unit or axis-order
slip**: every cm→m conversion is exact and order-preserving, and T-CO2's fit argument
survives any permutation of the box's axes.

Two nits, neither affecting a verdict: the summary rounds a margin to `0.518` where the
JSON holds `0.5173`, and "131 records over 2 BmGame bodies" reads as if all 131 were
BmGame (3 are; 128 are wreck). I also re-ran the card's own oracle: `8/8`, exit 0.

## C1. The 690 × 375 × 208 cm figure - from `COLLISION_BOXES.md`, axes X/Y/Z

The brief asked which of the two documents it comes from. It is **`COLLISION_BOXES.md`**,
and its table header names the axes:

```
## Export 169750 - `Batmobile_V3_Physics.RB_BodySetup`, bone `Batmobile_Chassis`
AggGeom payload **1759 B**, header `sphere_count=0`, `box_count=2`; boxes decoded: **2**.

| box | element bytes | TM tag | extents X/Y/Z (cm) | 0x4C word | bits set |
|---:|---|---|---|---:|---|
| 0 | 8..125 (118 B) | type 10, offset 0, name `TM` (index 78655), size 64 | 690.305 / 374.536 / 207.500 | `0x40` | [6] |
| 1 | 126..243 (118 B) | type 10, offset 0, name `TM` (index 78655), size 64 | 679.585 / 345.688 / 103.500 | `0x00` | [] |
```

So **X = 690.305, Y = 374.536, Z = 207.500 cm**. The same file's byte map confirms the
values field by field, at the logical offsets of one 80-byte element:

```
| 92 | 8 | extent_float | decoded FloatProperty at logical offset 0x40 - offset 0x40, value 690.305 |
| 100 | 8 | extent_float | decoded FloatProperty at logical offset 0x44 - offset 0x44, value 374.5361 |
| 108 | 8 | extent_float | decoded FloatProperty at logical offset 0x48 - offset 0x48, value 207.5 |
```

and the convention is stated with its oracle:

```
- chassis box 0 extents (decoded): 690.305, 374.536, 207.500 cm -> spans as full lengths 6.903, 3.745, 2.075 m,
  as half lengths 13.806, 7.491, 4.150 m.
- **verdict: FULL lengths.**
```

**It is not the pursuit hull union.** `COLLISION_CONVEX.md:87` gives, for the convex
element set it decodes:

```
- union of the element boxes (derived): min [-338.4417, -245.9405, -0.75], max [356.9706, 246.9817, 293.7526],
  extent [695.4123, 492.9222, 294.5026] cm.
```

Three different numbers (695.4 × 492.9 × 294.5). Anyone asked to "re-derive 690×375×208
from the hull union" would fail, because that triple is not there - it is a single
`FKBoxElem`'s extents, and `COLLISION_BOXES.md` itself compares it against both hulls
(`169748` battle, `169749` pursuit) rather than deriving it from them:

```
| 169749 | full | 224.1, 318.3, 671.0 | 207.5, 374.5, 690.3 | 1.080, 0.850, 0.972 | 0.150 | 28.1 |
```

G3-11d states it exactly this way ("largest **drivable** box: export 169750, extents
`[690.305, 374.5361, 207.5]` cm"), so the report's provenance is right.

## C2. The 316 cm wheel box - `PHYSICS.md` wreck data, not `COLLISION.md`

`Research/BatmobileGrab/PHYSICS.md:33`:

```
| 8 | `SUSP1_Wheel_Rear_Left_Mesh` | 1 box | 316.155×63.418×109.881 | (-117.414, -17.569, -12.155) | wheel/suspension |
```

and the wreck set it belongs to (`PHYSICS.md:5`): "**4 vehicles, 32 bodies each, 128 records
total.** All four vehicles carry byte-identical collision layouts." The report's claim that
T-22's "largest" is not even the decoded wreck maximum also checks out - `PHYSICS.md:31`:

```
| 6 | `SUSP1_Wheel_Rear_Right_Mesh` | 1 box | 317.942×64.552×97.966 | (-121.915, 25.708, -17.364) | wheel/suspension |
```

`COLLISION.md` has **no** 316 cm box; every `316` in it is a column of the per-instance
table (`| 316 | instance | ObjectReference | ReplacementPrimitive (decoded) | null |`), i.e.
a row index. So the brief's "`COLLISION.md` or the `PHYSICS.md` wreck data" resolves to
**`PHYSICS.md`** only.

## C3. The five rows - all say what the report says

Read from `Working/Translation/T_ROWS.jsonl` (schema `cells`/`dispo`/`doc`/`section`/`why`,
not the `LEDGER_G3B.json` schema). All five exist.

`T-CO1` (dispo `keep`):

```
[1] 32 boxes (bone, centre, extents)
[4] donor's shapes, stations moved
```

`T-CO2` (dispo `next`) - the row the report calls MISMATCH:

```
[1] largest box 316.15x63.42x109.88 cm
[3] 1 cm = 0.01 m; JC3 hull space is metres
[4] 3.1615x0.6342x1.0988 m fits one donor hull (longest hull axis 3.679 m)
why: the largest box 3.1615x0.6342x1.0988 m fits one donor hull (longest axis 3.679 m) at 1 cm = 0.01 m,
     so no layout change; `t16_collision.json`
```

`T-CO3` (dispo `keep`):

```
[4] donor's: 38/42 = 1, the 4 wheels = 0 (`world_collision_body_id` -1)
```

`T-P3` (dispo `next`):

```
[1] 32 collision bodies (boxes)
[4] written (G2-30): 11 driveable boxes map onto 7 donor hull slots; 21 are not driveable collision
    (18 destruction debris, 1 root placeholder, 1 turret, 1 jet fin); 11 T-8 parts have no slot
```

`T-PA3` (dispo `epe`):

```
[4] decoded - e.g. `body` -> 0, `door_f_l` -> 1, `engine` -> 7, wheels -> -1 (`PARTS_TABLE.jsonl`)
why: part -> collision body ids in the built graph
```

The report's quotations match all five, including the two it marks PARTIAL because the row
claims more than the `.physicsc` can show: `T-P3`'s "11 T-8 parts have no slot" and
`T-PA3`'s "built graph" (`why` says exactly that, and no `.epe` was read). The brief's
phrasing "the JC3 targets of five collision rows match" is also right, and the report keeps
the distinction sharp: the targets are not where `T-CO2` fails - its **source** cell is
("largest box 316.15…"), which is what the MISMATCH verdict addresses.

## C4. Unit and axis-order check - no slip

* cm→m, row `T-CO2`: `316.15 → 3.1615`, `63.42 → 0.6342`, `109.88 → 1.0988`. Exact at
  1 cm = 0.01 m, and the **axis order is preserved** (X, Y, Z stay X, Y, Z).
* chassis box: `690.305 / 374.536 / 207.500 cm` → the report's `690.305×374.5361×207.5 cm`
  and `6.90 m`. Exact (374.5361 is the stored float; the table rounds it to 374.536).
* the `12.57 cm` the report quotes for the box sitting outside the render bounds is
  `COLLISION_FRAME.md:68`: "margin inside the render bounds **-12.57 cm**, inside =
  **False**". Quoted correctly.
* **The fit conclusion is axis-order-independent, which is worth saying because the two
  frames label their axes differently.** BmAK's X is the car's length (690.305 cm); in the
  JC3/body frame the car's length is Z (body bbox span 7.031 m). G3-11d compares 6.903 m
  against the donor's longest hull axis 3.679 m - longest against longest - so the
  conclusion holds without matching labels. It also holds if the box's extents are read in
  any other order: the **second** largest extent, Y = 374.536 cm = **3.745 m**, still
  exceeds 3.679 m. So "the largest decoded box fits no donor hull" survives a swapped
  axis, a sorted reading, or a full/half-length misreading (half lengths would be larger
  still). That is the strongest form of the claim and the report's version is safe.

## C5. The report's own oracle - reproduces

```
$ uv run python Tools/scripts/g3_11d_collision_recheck.py --check
OK 8/8 oracles, 5 rows, 87 build trees, md+json identical
real    0m7.811s
```

## Nits (not defects of substance)

1. **`0.518` should be `0.517`.** The summary table says the 3.1615 m box fits "one donor
   hull (margins 0.518…0.986 m)"; §4 and the stored JSON both say
   `[0.5778, 0.9862, 0.5173]`, so the rounded range is `0.517…0.986`. A 1 mm rounding
   typo in the summary only.
2. **"131 records over 2 BmGame bodies"** reads as though all 131 are BmGame. The file
   says 131 = **3** boxes in `BmGame.upk` (2 + 1) **+ 128** wreck boxes over 4 wreck
   vehicles (`COLLISION_BOXES.md`:6, `PHYSICS.md`:5). §2 of the report does spell this out
   correctly; only the summary line compresses it badly.

## What I could not check

* **The containment arithmetic itself.** I did not re-run the hull-triangle/AABB containment
  for the 3.1615 m box against hull `@21072`, nor the "fits no hull" test across all 54
  hulls; I verified the *inputs* (the 690.305 triple and the 3.679 m longest hull axis) and
  the necessary-condition argument above, and the card's own `--check` passes 8/8.
* **The 87 build trees / 4 sha groups.** I did not re-hash every `.physicsc`; I ran the
  report's checker, which does (7.8 s) and agrees.
* **The `.physicsc` invariants** (54 hulls, 18 meshes, 62 body entries, 5 changed hull
  objects, `hknpPhysicsSystemData` identical) - not independently re-derived here.
* **"38/42 parts with a world shape"** - I did not recount it from `PARTS_TABLE.jsonl`.
* **`jc3hkx.stations` = 0 quads in every file** - quoted from the report, not re-run.
* **The wreck-union oracle's own caveat** (`COLLISION_BOXES.md`:223 says the half reading
  is the one that matches the intact car, the opposite of the chassis-box test) - the
  report does not mention this, but it also does not rely on the wreck union for any
  verdict, so it does not affect the five rows.
