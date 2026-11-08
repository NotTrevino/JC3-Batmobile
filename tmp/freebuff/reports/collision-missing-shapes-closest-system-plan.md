# Collision missing shapes — closest-system plan

The reopen (`Working/Translation/T22_REOPEN.md`) found the drivable hull is
`Physics.Batmobile_V3_Physics` — **2 bodies, 3 boxes, 1 constraint** — while the build's
`Working/Collision/batmobile.physicsc` carries the donor's **54 hulls / 112 instances**, of which
**14 instances are unbound** (the two donor bumper compounds). This plan closes that gap on paper:
which JC3 mechanism can carry a second/third shape, the byte-level edits in the `.physicsc`, the
numbers from the decoded chassis and pod boxes, and the gates that would prove it.

Sources: `Working/Translation/T22_REOPEN.md`; `tmp/freebuff/reports/collision-where.md` (G3-16);
`tmp/freebuff/reports/collision-rows-corrected.md`; `tmp/freebuff/reports/review-collision-corrected.md`;
`tmp/freebuff/reports/G3-10f.md`, `G3-11d.md`, `G3-12.md`, `B-10.md`, `G3-30.md`; `Research/JC3Grab/SHAPES.md`;
`Tools/scripts/jc3hkx.py`, `bm_colhull.py`, `bm_vehicle_hull.py`.

**Labels.** **decoded** = bytes read at the file/export/offset quoted. **derived** = stated arithmetic
over decoded values. **UNKNOWN** = absent from every file read, with the file or probe that settles it.

---

## 1. The numbers, and the one that changes the whole plan

BmAK's three drivable boxes (**decoded**, `T22_REOPEN.md` §"The asset", export 169750 / 169751):

| box | bone | extents (cm) | centre (cm) | TM |
|---|---|---|---|---|
| 0 | `Batmobile_Chassis` | 690.305 × 374.536 × 207.500 | (9, 0, 106.75) | identity, 0.000° |
| 1 | `Batmobile_Chassis` | 679.585 × 345.688 × 103.500 | (0, 0, 79) | identity |
| 2 | `Batmobile_Rig_Weapons_Trans` | 166.177 × 189.365 × 39.800 | (−30.5, 0, 93.25) | 4.000° about y, det 1.000000054 |

**Box 1 is almost inside box 0** (**derived**, extents/2 about the centres):

```
box 0 x  =   9 ± 345.1525  ->  -336.1525 .. 354.1525
box 1 x  =   0 ± 339.7925  ->  -339.7925 .. 339.7925     <- 3.640 cm past box 0 at -x
box 0 y  =   0 ± 187.268   ->  -187.268  .. 187.268
box 1 y  =   0 ± 172.844   ->  -172.844  .. 172.844      inside
box 0 z  = 106.75 ± 103.75 ->     3.00   .. 210.50
box 1 z  =  79.00 ± 51.75  ->    27.25   .. 130.75       inside
union    = 693.945 × 374.536 × 207.500 cm at (7.18, 0, 106.75)   = box 0 + 3.640 cm at -x
```

**Box 2 is entirely inside box 0** (**derived**): x −113.59 .. 52.59, y ±94.68, z 73.35 .. 113.15 —
all inside box 0's ranges above. Its 4° tilt moves its own corners, not its containment.

So the *only* geometric reach box 1 adds over box 0 is **3.64 cm**, and box 2 adds **nothing**.
That is smaller than the plan's own 5 cm acceptance band, and it is the fact that lets S2 and S3
close without a second shape instance (§4, route B). It does **not** close them as *bodies*: BmAK
simulates the pod as its own body (S3/S4), and that is a different claim (§5).

The donor side the build inherits (**decoded**, `G3-10f.md`, `T-22.md:59`, `COLLISION_LEDGER_CHECK.md:103`):

| quantity | value |
|---|---|
| `batmobile.physicsc` objects | 430, `hknpConvexPolytopeShape` 54, extern meshes 18, compounds 22, instances 112 |
| hulls bound to a part | **40** (body shapes) |
| hulls not bound to a part | **14** = the 7 children each of the `front_bumper` (body 16, compound `0x8f20`) and `rear_bumper` (body 26, compound `0xc570`) |
| wrapped instances | 98 of 112 carry a `CPfxPartIndexProperty` |
| free hull slots | **0** — 40 + 14 = 54, every hull is a body shape or a bumper child |
| body table | `hknpPhysicsSystemData + 0x2D20`, stride `0x60`, shape pointer per entry |
| instance record | 128 B: basis 3 × float4 @ +0x00/+0x10/+0x20, translation @ +0x30, scale @ +0x40, child shape ptr @ +0x50 |
| compound AABB | @ +0x80 / +0x90 (`vec4` min/max), union of its children |

---

## 2. The closest JC3 mechanism, per mechanism

| mechanism | what JC3 actually has | can it carry the missing shape? | label / evidence |
|---|---|---|---|
| **compound shape** | `hknpStaticCompoundShape` / `hknpDynamicCompoundShape`: an `hkArray` of 128-byte instances at +0x60, each with its own basis/translation/scale and child pointer; the compound is the shape of **exactly one** body entry | **yes, but only by creating a new compound on body 0.** Body 0's shape is a hull, not a compound (compounds exist only on bodies 16 and 26), and a body entry's shape pointer can only be pointed at an object that exists | decoded `jc3hkx.py` LAYOUTS + `decode_compound`; `G3-10f.md` table (1480/1480 compounds are a body's shape or a child of one) |
| **instance lists** | the two bumper compounds' 14 children — all hulls, all unbound, all rigid children of bodies 16/26 | **no.** Re-pointing one moves collision to the *bumper* body, whose transform is the bumper part's, not the chassis bone's | decoded `G3-10f.md`; `T-22.md:59` |
| **a second body** | 62 body entries, each with a part index; the pod bone `Batmobile_Rig_Weapons_Trans` has **no part** in the Batmobile part table | **no owner.** A body with no part does not move with the car | decoded `T22_REOPEN.md` S3; parts census `PARTS_TABLE.jsonl` |
| **unbound hulls (14)** | the donor bumpers' children, 7 + 7 | **no free slot**; they are accounted for, not spare | decoded `COLLISION_LEDGER_CHECK.md:103` (O7) |
| **one hull, union vertex set** | a hull is a single convex polytope; `bm_colhull.encode_hull` builds one from vertices + face loops, budget **244 vertices**, u8 indices (hard cap 255) | **yes for the union** of boxes 0+1 (+ box 2, already inside); a convex hull cannot represent two *disjoint* boxes, but these three are not disjoint | decoded `bm_colhull.py` docstring + `HULL_BUDGET` 244 |
| **constraint** | BmAK has 1 (`RB_ConstraintSetup` 171462, names `[Weapons_Trans, Weapons_Trans, Chassis]`) | **no writer**: `bm_collision.json` carries 0 constraint data, no JC3 constraint writer decoded | decoded `T22_REOPEN.md` S4; parent/child FName **UNKNOWN** |

**Consequence the build must accept.** JC3's model is *one body per part, each with one shape*.
BmAK's model is *two bodies, one of them compound (2 boxes), joined by a constraint*. The build
cannot be BmAK's model without a new-object writer and a constraint writer; it can be **the same
collision volume** with one body and one hull, which is what the 5 cm gate asks for.

---

## 3. Route A — grow an instance list (the byte-level edit, for the record)

This is the route the reopen named as the open writer question. Byte-level, it is:

1. **Pick the array.** `hknpStaticCompoundShape + 0x60` is an `hkArray` of
   `{T* data (8); int size (4); u32 capacityAndFlags (4)}`. The front-bumper compound has
   `size = 7`, `instances_inline = True` (the array sits inside the object, right after the header).
2. **Grow it.** `size 7 → 9`, `capacity` ≥ 9. Because the array is inline, the object's extent grows
   by 2 × 128 B = 256 B, and the object's *own* array pointer target (if it is a fixup) must be
   declared in `packfile_bytes`'s `inner` map — an undeclared pointer into a resized object stops the
   write by design ("`pointer into resized object @… has no inner map`").
3. **Write two 128-byte records**: basis = identity (box 1) and the 4.000° y rotation (box 2);
   translation = the box centre **in the bumper body's frame**; scale = per-axis
   `box_half_extent / child_half_extent`. The child pointer at +0x50 must target a hull that already
   exists — there is no new hull to point at, so this reuses a chassis-sized hull on a bumper body.
4. **Fix the parent AABB.** `compound_aabb_edits()` re-stores +0x80/+0x90 as the children's union plus
   the margin the file authored; `shape_checks` fails with "a child AABB is outside the compound AABB"
   otherwise.
5. **Re-read.** `check_file(new, against=donor)` must report 0 problems, the same object class list,
   and `hknpPhysicsSystemData identical True`.

**Why this route is not the recommendation.** Steps 1–5 are mechanically available *today* (G2-30
proved the re-lay-out, B-10b proved the inner map, `compound_aabb_edits` exists for the AABB), but
the shape lands on **body 16/26** — the bumper body — so the chassis-sized hull would swing on the
bumper hinge and add 6.9 m of collision to a panel. To land it on body 0 you must first create a
**new compound object on body 0**, and `packfile_bytes` re-lays-out *existing* objects in order
(`edits` maps an existing offset to a new blob); it has no insertion path, no enlarged virtual-fixup
table, and no spare `__classnames__` row to add. Object insertion is therefore **new work**, not a
call to an existing writer.

---

## 4. Route B — one hull, the union (recommended, and it closes S1/S2/S3 at the gate)

The build already rewrites body 0's hull: B-10c's `bm_colhull.apply()` re-cuts body 0 to the
Batmobile body mesh (LOD2, welded) within the fleet's 244-vertex budget, and `selftest` re-encodes
**54/54** donor hulls byte for byte. The only change Route B needs is the **target set**: instead of
"the mesh hull", the hull must enclose the mesh **and** the union of boxes 0+1 (box 2 is inside it).

| # | step | value | label |
|---|---|---|---|
| B1 | hull vertex count | ≤ **244** (fleet max; `bm_colmesh` LOD2 welded is already inside it) | decoded |
| B2 | index width | u8 per index → ≤ **255** vertices reachable; 244 keeps 11 spare | decoded |
| B3 | union box to enclose | **693.945 × 374.536 × 207.500 cm** at (7.18, 0, 106.75) | derived (§1) |
| B4 | union in JC3 axes | `(x, y, z) = (y_b, z_b, x_b)` → **3.74536 × 2.075 × 6.93945 m**, centre `(0, 1.0675, −0.0718) m` | derived from `review-collision-corrected.md` §4 (JC3 width on X, height on Y, length on Z, front −Z) |
| B5 | extra reach vs the mesh hull | ≤ **3.64 cm** on one axis if the mesh hull already touches box 0's AABB; the build's own tolerance is **1.0 cm** (`bm_vehicle_hull.TOL_HULL_CM`) for a derived rotation, and the acceptance band is **5 cm** | derived |
| B6 | box 2 | inside the union → **no vertex, no loop, no instance** | derived (§1) |
| B7 | constraint | still absent (S4) | decoded |

**Byte-level edit, Route B** (all existing writer calls, no new object):

1. `pf = jc3hkx.Packfile(open("Working/Collision/batmobile.physicsc","rb").read())`.
2. Find body 0's entry: `hknpPhysicsSystemData` at `+0x2D20 + 0x60*n`, shape pointer slot 0; follow it
   to the `hknpConvexPolytopeShape` (B-10c already retargets this pointer to the rebuilt hull).
3. Build the hull bytes with `bm_colhull.encode_hull(head, V, P, loops, mha)`: `V` = the mesh hull's
   vertices **plus** the corners of the B4 union box that lie outside it (or, simplest, the 8 corners
   of the B4 box if the acceptance is box-shaped contact); `P` = outward unit planes with
   `n·v + d = 0` on the face; `loops` = CCW about each outward normal; `mha` from
   `min_half_angle` (exact on 69 % of donor faces, mean error 2.7/255).
4. `jc3hkx.packfile_bytes(pf, {hull_off: blob})` — the hull uses *relative* u16 array offsets
   (`+0x30/+0x40/+0x44/+0x48` count, offset-from-field), so nothing points *into* it and no `inner`
   map is needed; every fixup after it is remapped by the writer.
5. If the rebuilt hull is a compound child (it is not on body 0, but this matters if Route A is ever
   used), `compound_aabb_edits()` must also emit the ancestor's +0x80/+0x90.
6. `check_file(out, against=donor)`, then `jc3hkx.py check --all`.

**Why this is the correct file.** `Working/Collision/batmobile.physicsc` is the file the build ships
and the one B-10/B-10c already rewrite (5 objects: 1 body hull + 4 wheels, `B-10.md:52`). The BmAK
numbers are targets, not sources: nothing in BmAK is imported.

**Revert.** The file is regenerated, not hand-edited: re-run `Tools/scripts/bm_colhull.py` (or B-10's
builder) from its recorded inputs, or restore the pre-run copy the builder writes under
`Working/Collision/`; `check_file --against` pinpoints any object that is not one of the intended
hulls.

---

## 5. Route C — the second body (blocked, with the file that settles it)

| question | answer | label |
|---|---|---|
| does JC3 let two bodies share one part? | **UNKNOWN** — 62 body entries each carry a part index; no body in the donor shares a part with another | UNKNOWN; settling probe: a build with body 1 bound to body 0's part, then a take |
| is there a part for `Batmobile_Rig_Weapons_Trans`? | **no** — the Batmobile part table has no such part; BmAK's bone has no JC3 owner | decoded `T22_REOPEN.md` S3 |
| does the engine simulate the pod body at all? | bool at 0x224 = True but **unnamed** | UNKNOWN `collision-where.md` |
| could the pod ride as a compound child instead? | yes in principle, but on body 0 that needs a new compound object (§3) | decoded |
| would the pod's 4° tilt matter? | **no at the gate** — box 2 is inside box 0, so a tilted box inside a containing box changes no AABB | derived (§1) |

The honest sentence: JC3 can carry BmAK's **volume** but not BmAK's **two-body model**. The build
declares one body, one hull, and records the pod body and the constraint as omissions rather than
silently dropping them (the reopen already does this for S4).

---

## 6. The standing gates that would prove it

| # | gate | pass condition | proves |
|---|---|---|---|
| G1 | `python Tools/scripts/jc3hkx.py check --all` | **0 problems** on every vehicle, including the written Batmobile | the file is a valid Havok 2014 packfile: sections, empty `__types__`, table residue 0, every fixup bound, every hull block accounted, vertex ranks monotonic, planes unit, indices < vertex count, all hulls convex, compounds' children inside their AABB |
| G2 | `check_file(out, against=donor)` | 0 problems; same object class list; `hknpPhysicsSystemData identical True`; `changed_objects` ⊆ the hulls written | the edit touched **only** the intended hull — the body/station data is untouched, so wheels do not move |
| G3 | `bm_colhull.selftest` | **54/54** hulls re-encode byte for byte | the encoder is exact on this file, so a hull change is a design change, not a writer artefact |
| G4 | `bm_colmesh.selftest` | passes on this file | the mesh side (body 42's extern mesh) is unchanged |
| G5 | union check (new) | body-0 hull's AABB ⊇ the B4 union within **5 cm**; box 2's corners inside it | S1/S2/S3 are covered by one shape |
| G6 | T-22 oracles O1–O10 | still PASS (2 bodies / 3 boxes / 1 constraint / identity TM / 4° pod) | the target did not drift while the build changed |
| G7 | Q-2 take: kerb nose-first + reverse ram | body contact at the right height; no boxing through the bumper line; no floating 3–7 cm gap | the collision is where the render is (behaviour, not bytes) |

---

## 7. Pilot card

> **Drive the car nose-first into a kerb, then reverse into the same kerb, then scrape a wall along
> the driver's side:** the car must stop with its bodywork touching, not floating — no visible gap
> over **5 cm** at the nose, tail or sill, and no contact where the body is not (the front must not
> stop 3–7 cm short of the kerb). Then drive over a low ramp at speed: the car must not catch on its
> **underside** where the render shows clearance.

Pass band, and why each number:

| number | source | fails if |
|---|---|---|
| **5 cm** gap | the reopen's acceptance gate; box 1's 3.64 cm protrusion is inside it | the hull is short of the render by more than 5 cm at any of the three faces |
| nose / tail / sill | the three boxes: 690.305 long, 374.536 wide, 207.5 tall (`T22_REOPEN.md`) | one face matches and another floats — a scaled hull can be right in one axis and short in two |
| underside clearance | box 1 (the 103.5 cm-high underside box) is inside box 0, so the hull's **z-min = 3.0 cm** is the number that matters | the car grounds on a ramp the render clears, or sails over one it should catch |
| no extra contact | body 2 (pod) is inside box 0, so the hull must not bulge upward beyond **z-max 210.5 cm** | the pod's 4° box or the weapons pod reads as a bump the render does not have |

---

## 8. UNKNOWNs, each with the file or probe that settles it

| # | UNKNOWN | settles it |
|---|---|---|
| U1 | whether object insertion (a new compound) is possible at all | extend `jc3hkx.packfile_bytes` with a fixup-table append and re-run G1 — the writer currently re-lays-out existing objects only (`edits` keys are existing offsets) |
| U2 | whether a JC3 body entry may point at a compound instead of a hull | a written file with body 0's shape pointer at a compound + G1/G7; no donor body does this for a chassis |
| U3 | whether two body entries may share one part index | a build + a take; no donor example in `PARTS_TABLE.jsonl` |
| U4 | whether the bumper bodies (16/26) are bound to parts the *Batmobile's* module keeps | the built parts module's parent chain (`Working/Collision/bm_collision.json` + B-04's part table) |
| U5 | which FName in `RB_ConstraintSetup` 171462 is parent and which child | no `RB_ConstraintSetup` layout in `BMSDK_OFFSETS.json`; needs the class layout |
| U6 | whether the engine simulates the pod body (bool at 0x224, unnamed) | a live property read of `RVehicleBatmobileBase + SVehicleMesh.PhysicsAsset` on a spawned car |
| U7 | the box 0/1 rotation | `COLLISION_GEOM.md` decodes extents and centres; the rotation is not decoded, so the triple is the box's local frame |
| U8 | how many of the 3 boxes the current build uses | `t22_collision.py`'s slot binding — T-22's S1 says "the one hull B-10 rewrites", so **1 of 3**; re-derive after the union edit |
| U9 | whether `t16_collision.json`'s consumers (slot binding, 11 → 7 map, radius × k) still agree after the corrections | `t22_collision.py` re-read in the same pass (flagged by `collision-rows-corrected.md` UNKNOWN 5) |

---

## 9. What the build does, in order

1. **Nothing before a measurement.** Route B is chosen on the 3.64 cm arithmetic, so first run
   G5's union check against the **current** built hull: if body 0's hull already encloses the B4
   union within 5 cm, S2 is already closed and only S3's *body* claim (not its volume) is open.
2. **If it does not enclose it**, re-cut body 0's hull with the union target (B-10c, `encode_hull`)
   and run G1/G2/G3. That is one writer call and one gate, not a new writer.
3. **Only if a test insists on literal 3 shapes**, build the object-insertion path (U1) and point
   body 0's entry at a new compound; that is new work and the plan says so.
4. **S4 (the constraint) stays a named omission** until a constraint writer is decoded; a
   one-body build has nothing to constrain, which is the honest reason the row cannot pass.

---

## 10. Checks run for this plan

| # | check | result |
|---|---|---|
| 1 | both named inputs read | `Working/Translation/T22_REOPEN.md` (10 oracles, 2 bodies / 3 boxes / 1 constraint / 0 free slots) and the three `tmp/freebuff/reports/` files (`reports/*.md` do not exist — the documents live under `tmp/freebuff/reports/`) |
| 2 | containment arithmetic | box 1 protrudes **3.640 cm** past box 0 at −x only; box 2 lies inside box 0 on all three axes; union = 693.945 × 374.536 × 207.500 cm at (7.18, 0, 106.75) |
| 3 | hull census re-checked | 54 hulls = 40 body shapes + 14 bumper children (7 + 7, compounds `0x8f20` / `0xc570`, bodies 16 / 26); 112 instances, 98 part-wired |
| 4 | writer capabilities read from the tools, not assumed | `packfile_bytes` (re-lay-out, `inner` map), `hull_bytes` (vertex/plane blocks, fixed counts), `encode_hull` (244-vertex budget, u8 indices), `compound_aabb_edits` (+0x80/+0x90), `verify_written` (only given objects may change), `check_file --against` (`hknpPhysicsSystemData` identical) |
| 5 | byte offsets quoted from decoded layouts | `hknpPhysicsSystemData + 0x2D20` stride `0x60`; instance 128 B with basis/translation/scale at +0x00/+0x30/+0x40 and child at +0x50; `hkArray` 16 B `{ptr, size, cap|flags}`; compound AABB +0x80/+0x90 |
| 6 | axis order | JC3 = width X, height Y, length Z, front −Z (`review-collision-corrected.md` §4, from MODLOG §15/§16); BmAK = X/Y/Z Z-up |

**Limits.** This is a plan: no `.physicsc` was written, no build tree touched, no game launched.
Every byte offset is decoded from the reader/writer that already round-trips this file (54/54 hulls),
but the *edit* itself has not been executed, so G1–G7 are the gates that would prove it, not results.
The 3.64 cm containment is arithmetic on decoded box extents; it cannot see the *mesh* hull's true
shape, which is why G5 measures the built hull rather than trusting the number.
