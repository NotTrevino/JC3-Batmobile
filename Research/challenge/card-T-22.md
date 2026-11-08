# Assumption challenge — backlog card **T-22 · Collision translation** (done 2026-10-28)

Read-only pass over the finished card. What was read: `GRAB_BACKLOG.md` §0.5 (R1–R14, lines 59–76),
the T-22 card and its `Done` clause (§9, line 967), its §12 row (line 1331), the `MODLOG.md`
intended-change and done blocks (lines 13572–13800) incl. the appended *T-22 correction*, and every
artifact the card names: `Tools/scripts/t22_collision.py` (582 lines), `Working/Translation/t16_collision.json`,
the three row lines in `T1_TRANSLATION.md:217` / `T2_TRANSLATION.md:168-169,160`, `T_ROWS.jsonl`,
`REGISTER`-side `BUILD_BATCHES.md:149,168`, plus the inputs the script reads
(`PHYSICS.json/.md`, `BONES.json`, `MESHES.json`, `TYRES.md`, `stations.json`,
`parts_manifest.json`, `T8_PARTS.json`, `PARTS_TABLE.jsonl`, the donor `sportsmuscle.physicsc` and
`sportsmuscle_vehicle_parts.vmodc` in `Builds/test-091`) and the sibling G2-30 record
(`Research/JC3Grab/PHYSICS_WRITE.md`).

No game was launched (R6), nothing was written to `D:/Games`, nothing was committed, no secret was
read, and **no repository file was modified except this document**. The probes run against the data
were `python -c` one-liners or scratch scripts in the OS temp directory; the three read-only
entry points used were `t22_collision.py --check`, `t_rows.py check` and `status_audit.py --check`.
Tamper tests were **not** re-run (they write into the repo); §A16 says what that leaves unverified.

---

## VERDICT summary

**The card's arithmetic is reproducible; three of its load-bearing facts are not true of the files.**
`t22_collision.py --check` passes —

```
PASS: 32 BmAK bodies | 7 mapped / 21 unmapped | 54 donor hull slots, one per part | 38/42 parts collide | rows 3 (next 2, keep 1) | stations unchanged
```

— and every number in that line except one is what the data says. The one that is wrong is
"stations unchanged" (A2), and the "54 … one per part" half of another is wrong (A3). Beyond the
summary line, two translation *values* do not survive: the per-part `k_in`/`k_out` for the doors are
artifacts of an untested axis pairing (A8), and the placement rule ("translation = the part's pivot")
does not place anything (A9) — the body hull's implied position is 0.38 m too low and 0.55 m too far
back, the two door hulls stay at the donor's *front* doors, metres from the Batmobile's rear canopy.

| # | assumption (stated or silent) | verdict |
|---|---|---|
| A1 | BmAK numbers are centimetres and are **full** box extents | **WEAK** — the cm half holds to 0.6 mm; the "full extent" half is chosen silently and the repo's own sibling artifact reads the same floats as **half**-extents |
| A2 | "0 station quads in the physicsc, so there is nothing in the collision file to move" | **BROKEN** — the file carries all four wheel positions, already at the Batmobile's values; the reader returns 0 only because front and rear `y` differ by 2 mm |
| A3 | "54 hulls, one per part"; `max_hulls: 54`; `hulls_per_part: 1` | **WEAK** — 54 objects, 40 part-indexed shapes, 2 parts with none, 20 part indices with two instances; it is the donor's inventory, not a decomposition parameter |
| A4 | the 14 unindexed hulls are the donor's two bumpers, "not free slots" | **HOLDS** — and can now be *proven* from the body-entry table instead of asserted |
| A5 | 11 boxes are "the driveable car's", 21 are "wreck-only" | **WEAK** — drawn by bone-name string; 2 of the 21 (`Main_Turret_00`, `Jet_Fins001`) are the driveable car's own turret and jet |
| A6 | wheel `k` = tyre Ø / donor wheel-hull longest axis = 1.660052 | **HOLDS** for the diameter; two nits (printed arithmetic, and a second `k` = 1.659566 in G2-30 for the same hull) |
| A7 | one uniform `k` makes the wheel hull cover the tyre | **WEAK** — after scaling the hull is 0.491 m wide against a 0.7314 m tyre: 33 % of the width has no hull |
| A8 | box axis *i* pairs with hull axis *i* (`k_in` / `k_out` per part) | **BROKEN** — the pairing is never tested; a permutation search gives 0.564/0.672 where the card records 0.266/0.507, and `Rear_Door_MIDDLE` ends up with a hull 0.103 × 0.278 × 0.376 m |
| A9 | "translation = the part's pivot" (`bat_assemble T(p)`) places the hull | **BROKEN** — 40 hulls are authored in vehicle space at their donor part's centroid, 4 at the origin; neither reading of the line puts a hull on a Batmobile part |
| A10 | "the front and rear ~0.43 m of the body has no convex hull" | **BROKEN** — 0.975 m uncovered at the front, 0.117 m of hull *past* the tail, 0.257 m below the floor, 0.496 m below the roof |
| A11 | "whether the donor's `hknpExternMeshShape` still bounds it acceptably is a runtime question" | **BROKEN** — the body's extern mesh is 2.194 × 1.482 × 3.827 m, strictly inside the scaled hull: it covers 0 m of the gap, so this is a file question with a file answer |
| A12 | "the 11 T-8 parts have no slot" | **WEAK** — no slot is *free* for them, but 54 − 7 = 47 hull objects belong to parts other than the 7 mapped, and G2-30 §5 proved a slot can be replaced by a different hull block |
| A13 | T-CO3 `keep`: "38/42 = 1, the 4 wheels 0 → wheels are sim-only on both sides" | **WEAK** — true and now provable for the donor; "both sides" is UNKNOWN, and the flag does not mean "has a hull" (two parts at 1 have none) |
| A14 | tyre Ø 1.3654 m = 2 × the `stations.json` radius ("design identity") | **HOLDS** — the measured tread diameters are 1.3652–1.3657 m and their mean is 1.3654 |
| A15 | copying `stations.json` `tyre_width` per corner into the record | **WEAK** — `TYRES.md` §1 says those widths are mirrored L↔R; the record now carries an attribution its own source calls untraceable |
| A16 | the done block's own numbers (300 B hull minimum, 4/4 tamper tests, ledger summary) | **WEAK** — 300 is wrong (400, and the appended correction says so); the ledger summary has since drifted; the tamper tests were not re-run here |

Net: **3 hold (A4, A6, A14), 8 weak, 5 broken.** The card's *dispositions*
(`T-P3` next, `T-CO2` next, `T-CO3` keep) survive; what does not survive is the claim that
`t16_collision.json` is a hull set for the Batmobile. It is a hull set for **seven donor slots**, one
of which (the body) is mis-placed by up to 0.55 m and two of which (the doors) are mis-placed by
metres, and B-10's own gate — *"hull union bbox within 5 cm of the body bbox"*
(`BUILD_BATCHES.md:149`) — cannot pass on these values (§A9, A10).

---

## A1 · "BmAK extents are cm, and they are the full box extents"

**Claim.** `T-CO2`'s warrant cell is *"1 cm = 0.01 m; JC3 hull space is metres"* and the value cell
turns `316.155 × 63.418 × 109.881 cm` into `3.1615 × 0.6342 × 1.0988 m`. The script's helper says, in
one line, both things at once:

```python
def _box_m(extents_cm: list) -> dict:
    """A BmAK box in metres: `extents` is the full extent, so half is the radius."""
    return {"full": [_round(e / 100.0) for e in extents_cm]}
```

**Test 1 — the centimetre half.** Compare the grabbed mesh bounds of the intact car
(`MESHES.json`, `Playable_Batmobile_SF` / `Batmobile_V2`, Unreal axes) with the assembled body bbox
the card uses (`parts_manifest.json` → `body_bbox_m`, JC3 axes through `T(p)`):

```
Batmobile_V2 pskx bounds size  : 702.56 x 349.53 x 234.185  (cm, from MESHES.json)
body_bbox_m                    : 3.495 x 2.271 x 7.025      (m, from parts_manifest.json)
length 702.56 cm -> 7.025 m    : 0.6 mm apart
width  349.53 cm -> 3.495 m    : 0.3 mm apart
```

Two independent artifacts, 0.6 mm apart over 7 m. **The cm↔m bridge holds** — better than the card
claims, because the card only asserts it.

**Test 2 — the full/half half.** The same three floats are read a second way by the tool that wrote
them. `grab_physics.py:159` computes each body's volume as `8 * x * y * z / 1e6`, i.e. it treats the
triple as **half**-extents; `t22_collision.py` divides by 100 and prints the result in a column
headed *"extents X×Y×Z (cm)"*. Both readings are in the repo and PHYSICS.md prints the 8× one:

```
PHYSICS.md "Largest collision volumes": SUSP1_Wheel_Rear_Left_Mesh  17.6248 m3
8 * 3.16155 * 0.63418 * 1.09881                                   = 17.6248   <- PHYSICS.md's reading
1 * 3.16155 * 0.63418 * 1.09881                                   =  2.2031   <- T-22's reading
```

Nothing in the card, the script or `--check` tests which one is the file's convention; the
assumption is silent (`_box_m`'s docstring contradicts its own body). It is not cosmetic: under the
8× reading the largest box is **6.323 m**, and `T-CO2`'s "fits one donor hull (longest hull axis
3.679 m)" flips from true to false, and every `k` in `t16_collision.json` halves.

The wreck's own geometry cannot settle it either: the wheel box `97.605 × 55.342 × 101.533` cm
against the measured tyre (73.1 wide × 136.5 Ø) is too small at 1× and 2.7× too wide at 8×, so the
"destroyed" asset's envelopes are not the intact tyre's bounds under either reading (I say UNKNOWN
rather than pick one).

**Verdict: WEAK.** The unit bridge HOLDS with 0.6 mm evidence; "full extent" is an inference, and
the repo's other consumer of the same bytes disagrees by 2×.

---

## A2 · "0 station quads in the file, so there is nothing in the collision file to move"

**Claim.** MODLOG done block: *"The donor physicsc contains **0** station quads (`jc3hkx.stations`),
so there is nothing in the collision file to move"*. `t16_collision.json` records it twice:

```json
"donor":     { ..., "stations_in_file": 0 }
"stations":  { "in_physicsc": 0,
               "unchanged": "R3: no wheel/station row is touched; the quads live in the vmodc's
                             base_wheel_hardpoint_positions + land_global, not in the physicsc
                             (0 sets there)" }
```

and the §12 row repeats it: *"0 station quads in the file, stations untouched"*.

**Test.** Read the `hknpPhysicsSystemData` body-entry array directly, and pair it with the parts
module's body ids:

```
parts module (jc3adf.parts, sportsmuscle_vehicle_parts.vmodc):
  sportsmuscle_wheel_f_l   world_col=0 world_id=-1 raycast_id=22
  sportsmuscle_wheel_f_r   world_col=0 world_id=-1 raycast_id=23
  sportsmuscle_wheel_r_l   world_col=0 world_id=-1 raycast_id=36
  sportsmuscle_wheel_r_r   world_col=0 world_id=-1 raycast_id=37

body_entries[22] pos [-1.208, 0.705, -2.57, 1.0]   shape hknpConvexPolytopeShape
body_entries[23] pos [ 1.208, 0.705, -2.57, 1.0]   shape hknpConvexPolytopeShape
body_entries[36] pos [-1.285, 0.703,  2.459, 1.0]  shape hknpConvexPolytopeShape
body_entries[37] pos [ 1.285, 0.703,  2.459, 1.0]  shape hknpConvexPolytopeShape
```

Those four are **exactly** `Working/TrueScale/stations.json`'s `hub_true` values (and exactly the
`base_wheel_hardpoint_positions` in `..._land_global.vmodc`: `[-1.208, 0.7047, -2.57]` …). The
collision file carries the four wheel stations, as the raycast bodies of the four wheel parts.

Why the reader says 0 — `jc3hkx.stations` (lines 609–646) groups candidates by `round(y, 3)` and
then requires **one group of exactly four**:

```python
groups.setdefault(c[0], []).append(c)          # c[0] = round(y,3)
for y, g in groups.items():
    if len(g) != 4: continue                   # front y 0.7047, rear y 0.7027 -> 2 + 2
```

Front `y` = 0.7047, rear `y` = 0.7027 — 2 mm apart — so the group sizes are 2 and 2 and the
function returns `[]`. The 0 is a failed heuristic, not an absence, and G2-30's own record says so:

> `PHYSICS_WRITE.md` §6: "the wheel-station data | copied, not rebuilt: **it lives in
> `hknpPhysicsSystemData`**, outside every hull block"
> `PHYSICS_WRITE.md` §2: "one `f32` at `hknpPhysicsSystemData` +0x3598 = `body_entries[22]` +0x38:
> -2.569999933242798 -> -2.5699000358581543" — proof that an earlier card **did** move a station in
> this file.

And the stations have already been moved, by whatever build introduced TrueScale — compare an early
lineage with the live one (same size, different bytes):

```
test-003  bytes 340368 sha 62163ea4496f  4 non-zero entries: (-0.885, 0.4, -1.557) ... ( -0.885, 0.4, 1.446)
test-090  bytes 340368 sha 1b90daefdc96  4 non-zero entries: (-1.208, 0.7047, -2.57) ... (-1.2845, 0.7027, 2.4589)
test-091  bytes 340368 sha 1b90daefdc96  (same as test-090)
```

test-003's values are the donor sports car's own track (1.77 m) and wheelbase (3.003 m); test-090's
are the Batmobile's. So the file **was** edited, in exactly the place the card says has nothing.

**Verdict: BROKEN.** The conclusion "nothing to move" happens to be true *today* (the four positions
already are the Batmobile's), but the stated ground is false in three ways: the carrier exists, the
reader is the reason it read 0, and the member the json names (`base_wheel_hardpoint_positions`)
actually lives in `v0300_car_kensington_sportsmuscle_land_global.vmodc`, not in the parts module the
record lists as `inputs.jc3_parts_module`. A reader who trusts
`"in_physicsc": 0` will conclude the collision file can never hold stations — and then be surprised
when a scaled wheel body rides 0.68 m off the ground because the hull grew but the body entry did not.

---

## A3 · "54 hulls, one per part" / `max_hulls: 54` / `hulls_per_part: 1`

**Claim.** §12: *"54 hulls, one per part"*. `decomposition`: `{"max_hulls": 54, "hulls_per_part": 1}`;
MODLOG: *"22 compounds, **54** convex hulls - **40 bound to a part**, 14 unbound"* and *"One hull per
part"*.

**Test.** Count the objects and the bindings:

```
polytope objects in the file                     : 54      (so "54" is right as an object count)
distinct shapes reached through compound insts    : 54      (no shape only reachable outside a compound)
shapes with no part index                         : 14
part indices carrying two hull *instances*        : 20      (4,5,7,8,9,17,19,28..31,33..41)
part names carrying two hull *shapes*             : none    (so `hull_by_part` never silently overwrites)
parts module rows                                 : 42
parts with 0 part-indexed hulls                   : 2       (front_bumper idx 22, rear_bumper idx 6)
```

So of 42 parts, 40 have exactly one hull shape, 2 have none, and 14 of the 54 objects belong to
bodies with no part index. "54 hulls, one per part" is arithmetically impossible (54 > 42) and
describes three different counts at once. The json's `max_hulls: 54` reads like a decomposition
parameter of the Batmobile, but it is `len(hulls)` — the donor's inventory of shape objects. The
card's `Do` asked for *"convex decomposition parameters (convex decomposition parameters, max
hulls, convex radius)"* of the Batmobile body; what is delivered is the count of shapes that already
exist in another car. That is honestly explained in the script docstring and in `new_hull`
("UNKNOWN … the object count (54) is fixed"), but not in the row or in §12.

**Verdict: WEAK** (labels and counts, not values). The number 54 is right; "one per part" is false
for 2 parts and double for 20 instance slots; "max hulls" is a floor on objects, not a parameter.

---

## A4 · "the 14 unindexed hulls belong to the two bumpers, so they are not free slots"

**Claim.** `decomposition.unbound_note`: *"the 14 unbound hull instances belong to the donor's two
bumpers (no part index), so they are not free slots"*. MODLOG: *"14 unbound (the two bumpers'
panels, which carry no part index)"*.

**Test.** Group the unindexed shapes by the compound that owns them, and look up the two parts the
parts module says have no hull:

```
compound off 36640  instances 7  unbound 7   translations all [0,0,0,0.5]
compound off 50544  instances 7  unbound 7   translations near z 2.44-2.48 (rear of car)
parts module: sportsmuscle_front_bumper world_collision_body_id=16  hulls=0
              sportsmuscle_rear_bumper  world_collision_body_id=26  hulls=0
body_entries: [16] hknpStaticCompoundShape   [26] hknpStaticCompoundShape
```

Body ids 16 and 26 — the bumpers' own world-collision bodies — are the only two non-polytope,
non-extern-mesh bodies in the 62-entry table, and they are precisely the two compounds that carry the
14 unindexed shapes, 7 each. The claim is not just consistent, it is provable.

**Verdict: HOLDS.** (The only sharpening: they are 2 compound *bodies* × 7 shapes, so "hulls_unbound:
14" is a shape count and "not free slots" is right for the same reason.)

---

## A5 · "11 boxes are the driveable car's; 21 are wreck-only"

**Claim.** `T-P3` value cell: *"11 driveable boxes map onto 7 donor hull slots … 21 are not driveable
collision (18 destruction debris, 1 root placeholder, 1 turret, 1 jet fin)"*; §12: *"21 boxes are
wreck-only"*.

**Test 1 — where do the 32 bones come from?**

```
PHYSICS.json  physics_assets (all 4 packages) : Batmobile_V3_Destroyed_Physics
MESHES.json   Batmobile_V3_Destroyed          : 32 bones
MESHES.json   Batmobile_V2 (the intact car)   : 180 bones
BONES.json    intact car, 180 bones           : contains Rear_Door_BOTTOM, Rear_Door_MIDDLE,
                                                CockPit_Mesh, but none of the 18 `Object*` names
```

All 32 bodies belong to the **destroyed** asset's skeleton — including the 11 the card calls
"driveable". The criterion that splits the 32 into 11 + 21 is the bone-name string (`scripts
.load_bmak()` classifies by `"Wheel" in bone`, `bone.startswith("Rear_Door")`, `bone ==
"CockPit_Mesh"`, else "destruction debris"). Three of the 32 names (`CockPit_Mesh`,
`Rear_Door_MIDDLE`, `Rear_Door_BOTTOM`) exist verbatim in the intact skeleton; the eight wheel names
only match it after stripping `_Mesh`. That is an R5 reading: the member sounds like the driveable
part, so it is treated as the driveable part's collision.

**Test 2 — does the mapped set contain a box with no geometry?** Yes:

```
BONES.json  Rear_Door_BOTTOM  owned_faces {lod0: 0, lod1: 0, lod2: 0}  pivot [0.000121, 0.543079, 3.206766]
BONES.json  Rear_Door_MIDDLE  owned_faces {lod0: 872, lod1: 405, lod2: 80}  pivot [..., 1.647898, 2.915273]
BONES.json  CockPit_Mesh      owned_faces {lod0: 24120, ...}
```

One of the two "driveable door" boxes is the envelope of a bone that owns **zero** faces at every
LOD of the intact mesh, and the script hands it a hull (`sportsmuscle_door_f_l`, `k` 0.507).

**Test 3 — are the 21 really wreck-only?** 18 are (`Object*`, absent from the intact skeleton —
HOLDS). But the other 3 are not wreck debris: `Root` is a placeholder (fine), and `Main_Turret_00`
and `Jet_Fins001` are the **driveable car's own turret and jet fin** — `T8_PARTS.json` lists
`batmobile_turret` and `batmobile_jet` as two of its 11 moving parts, and the script's own
`WHY_NONE` says *"the turret is a T-8 part (`batmobile_turret`)"*. Calling those two "wreck-only"
in §12 is contradicted by the card's own output.

**Verdict: WEAK.** The 18-debris half HOLDS; the "11 driveable" half is name-based and includes a
bone with no faces; §12's "21 boxes are wreck-only" is wrong for 2 of the 21 (which are, instead,
parts T-22 leaves without collision).

---

## A6 · wheel `k` = tyre Ø / donor wheel-hull longest axis

**Claim.** §12: *"wheel k 1.660052 = tyre 1.3654 m / 0.8225 m"*; MODLOG: *"3 seconds of arithmetic
from G2-30's measured 1.659566"*.

**Test.**

```
donor wheel hull (sportsmuscle_wheel_f_l, 20 v / 12 p, 704 B) box : 0.2958 x 0.8225 x 0.7822 m
                                                       AABB centre: [0.0, 0.0001, 0.0009]
tyre_d  = 2 * mean(0.6829, 0.6826, 0.6826, 0.6827) = 1.3654
1.3654 / 0.8225 = 1.6600608          json scale_k = 1.660052   (uses box_precise max, 0.8225046)
G2-30 PHYSICS_WRITE.md §5: factor 1.659566 = 1.365 / 0.8225
```

The choice of *longest axis* as the radial one is supported by the shape: the hull's two large axes
are 0.8225 and 0.7822 (a near-circular disc), the small one 0.2958 is the width — the same reading
TYRES.md pins for the Batmobile tyre (x axle, y vertical, z longitudinal). Scaling about the hull's
own centre is what `jc3hkx.scale_hull` does and what G2-30 round-tripped; nothing moves.

**Verdict: HOLDS** for the diameter. Two nits: the printed equation is off in the 6th digit
(1.3654/0.8225 = 1.660061, not 1.660052 — the json's k comes from the unrounded hull axis), and the
repo now carries **two** k values for the same hull (1.660052 here, 1.659566 in G2-30). B-10 will
follow one of them; the 0.5 mm difference is harmless, the ambiguity is not.

---

## A7 · "one uniform `k`" makes the wheel hull *cover* the tyre

**Claim.** `decomposition.parameters.scale_k`: *"one uniform scale per hull - the only factor G2-30
proved"*; §12: *"wheel k 1.660052"*; T-CO3 keeps the wheels sim-only.

**Test.** The donor tyre's width/diameter ratio is not the Batmobile's:

```
donor wheel hull  : 0.2958 (x, width) / 0.8225 (diameter) = 0.360
Batmobile tyre    : 0.7314 .. 0.7325 / 1.3652 .. 1.3657    = 0.536
after scaling x 1.660052 : box 0.491 x 1.3654 x 1.2986
                            tyre  0.7314 wide, 1.3652-1.3657 Ø
```

The diameter is matched to 0.1 mm; the **width is 0.24 m short** (0.491 vs 0.7314) and one radial
axis is 0.067 m short (1.2986 vs 1.3654). So the wheel's contact hull is two-thirds the width of the
wheel it is supposed to be — a scrub/kerb contact the sim will not feel, and an R3-adjacent
visual/physics mismatch that no row mentions. This is inherent to a uniform k on a shape with a
different aspect ratio; the alternative (a non-uniform scale) is a different writer case T-22 never
considers.

**Verdict: WEAK.** The one factor that *can* be written is written; the claim that it produces a hull
that bounds the tyre is not tested, and it does not, in width.

---

## A8 · box axis *i* pairs with hull axis *i* (`k_in` / `k_out`)

**Claim.** For every non-wheel part: `k = min(box[j]/hull[j])`, `k_out = max(...)`, presented as *"k_in
fits inside the box, k_out covers it — one uniform factor cannot match both"*, so *"B-10 has to
choose"*.

**Test 1 — do the two boxes even share a frame?** The four wheel envelopes of one symmetric car must
have equal magnitudes in *any* car-global AABB (mirroring does not change an extent):

```
Wheel_Front_Left_Vis_Mesh   0.9761 x 0.5534 x 1.0153
Wheel_Front_Right_Vis_Mesh  0.9701 x 0.5254 x 1.0325
Wheel_Back_Left_Vis_Mesh    0.9899 x 0.6057 x 1.0890
Wheel_Rear_Right_Vis_Mesh   1.0661 x 0.6481 x 1.0603
```

They differ in every axis (up to 10 cm), so they are **bone-local** boxes in four differently
oriented bone frames. The donor hulls, by contrast, are authored in one vehicle frame (§A9). There is
therefore no reason for axis *j* of one to mean the same direction as axis *j* of the other — and the
card never states or tests the pairing.

**Test 2 — what a permutation search finds.** For each mapped part I recomputed the best uniform
scale over all six axis assignments:

```
Rear_Door_BOTTOM    script k 0.506995  best k_in 0.671919 (perm 0,2,1) | script k_out 1.461735  best 1.079576
Rear_Door_MIDDLE    script k 0.265582  best k_in 0.564093 (perm 2,0,1) | script k_out 1.881254  best 1.392862
BODY                script k 1.676259  best k_in 1.676259 (perm 0,1,2) | script k_out 1.909565  best 1.909590
```

For the body the identity pairing is already optimal (no finding). For the two doors it is not: the
recorded `k_in` is **2.1× smaller** than the best available and the recorded `k_out` **1.35× larger**,
purely because the axes were paired by index. What that does to the value B-10 must choose:

```
Rear_Door_MIDDLE  box 0.591 x 1.971 x 0.376 m
  script k 0.265582 -> hull 0.103 x 0.278 x 0.376 m   (a 28 cm tall collision hull for a 1.97 m door)
  script k_out 1.88 -> hull 0.729 x 1.971 x 2.662 m   (a 2.7 m long door)
  best pairing k_in 0.564 -> hull 0.219 x 0.591 x 0.798 m
```

Neither recorded number is defensible; the "choose between k_in and k_out" framing hides a third,
better option the script never computes.

**Verdict: BROKEN** as a measurement of the box↔hull relation. The body's identity pairing happens
to be optimal; for 2 of the 6 mapped parts the recorded k is a factor 2 off, and the reason is an
unstated coordinate assumption — exactly the class of error R5 exists to catch.

---

## A9 · "translation = the part's pivot (`bat_assemble T(p)`, R2)" places the hull

**Claim.** `decomposition.parameters.translation`: *"the part's pivot (bat_assemble T(p), R2)"*. This
is the only statement in the card about **where** each hull goes; everything else is a size.

**Test 1 — where are the donor's hulls authored?** Measured AABBs vs the parts module's centroids:

```
sportsmuscle_body    hull centre [ 0.0000, 0.8501, 0.6383]  part centroid [ 0.0, 0.815, 0.649]
sportsmuscle_door_f_l hull centre [-0.8374, 0.8677,-0.0539]  part centroid [-0.837, 0.882,-0.07]
sportsmuscle_fender_l hull centre [-0.7151, 0.6620,-1.6053]  part centroid [-0.711, 0.666,-1.609]
sportsmuscle_wheel_f_l hull centre [ 0.0000, 0.0001, 0.0009] part centroid [ 0.0, 0.0, 0.0]
```

40 of the 54 hulls are authored **in vehicle space, already at their part's position**; only the four
wheel hulls sit at the origin, because a wheel part is positioned by its raycast body (§A2). Two
consequences:

* Reading the json literally ("apply `T(p)` to the part") **double-transforms** the 40: they are
  already placed, and `bat_assemble`'s offset alone is `[0, 0.0222, 0.154]`.
* Reading it charitably ("put the hull at the target part's pivot") gives the body hull centre
  `(0, 0.0222, 0.154)` — 1.20 m below the body's own centre height (1.2265), so a 2.03 m tall hull
  would span −0.994 … 1.038 m: ~1.0 m of it underground.

The one rule cannot be right for both authoring conventions, and the card never says which hull is
which.

**Test 2 — what the body hull's implied position is.** `jc3hkx.scale_hull` scales about the hull's
own AABB centre, so the scaled body hull keeps the donor's centre `(0, 0.8501, 0.6383)`:

```
body hull after k=1.676259 : 3.4950 x 2.0316 x 6.1666 m, centre (0, 0.8501, 0.6383)
   spans y -0.1657 .. 1.8659      body spans y 0.091 .. 2.362   (T8 ground plane 0.02)
   spans z -2.4450 .. 3.7216      body spans z -3.420 .. 3.605
=> 0.257 m below the body floor, 0.496 m below the roof, 0.166 m below y=0 (0.186 m below the 0.02 ground plane)
```

A chassis hull hanging 0.19 m under the road, with the roof unbounded. And for the doors it is worse
than a scale: the Batmobile's `Rear_Door_BOTTOM` pivot is at **z 3.207** (the rear canopy), while the
donor hull it is bound to sits at **z -0.054** — a 3.26 m displacement that no k and no "part pivot"
statement resolves.

**Test 3 — can the writer even translate a hull?** G2-30's proven operation rewrites a hull object's
vertices/planes (`hull_bytes`), and `compound_aabb_edits` only recomputes ancestor AABBs. So a
translation would have to be **baked into the vertex block** (possible) or written into the 128-byte
shape-instance record (not demonstrated anywhere in G2-30). T-22 asks for neither: it names a
transform from the mesh pipeline, not an offset between two hull centres.

**Verdict: BROKEN.** The card records a size and calls the placement done by a sentence that is true
of the mesh pipeline and false of these hulls. This is the single most consequential item here,
because it decides whether B-10's gate can pass at all.

---

## A10 · "the front and rear ~0.43 m of the body has no convex hull"

**Claim.** MODLOG UNKNOWN 2: *"With one 3.679 m hull scaled to the 7.025 m body, the front and rear
~0.43 m of the body has no convex hull"*. (0.429 = (7.025 − 6.167)/2 — the symmetric assumption.)

**Test.** Arithmetic on the card's own numbers (§A9):

```
front gap  = -2.445 - (-3.420) = 0.975 m of body with no hull
rear  gap  =  3.605 -  3.7216  = -0.117 m  (the hull sticks 11.7 cm PAST the tail)
sum        = 0.975 - 0.117 = 0.858 = 7.025 - 6.167   (consistent)
vertical   = 0.257 m below the floor, 0.496 m below the roof
```

The gap is not symmetric: the donor's body hull is centred 0.546 m aft of the Batmobile body's
centre. So "~0.43 m front and rear" understates the front by 2.3× and invents a rear gap that does
not exist.

**Why it matters beyond the sentence.** `BUILD_BATCHES.md:149` gives B-10 its gate: *"`jc3hkx.py
check --all` on the built file; **hull union bbox within 5 cm of the body bbox**"*. Evaluating the
union over all seven hulls at the placements the json implies (body hull at the donor body's centre,
4 wheel hulls at the wheel stations, 2 door hulls at the donor door centres — wheels and doors are
scaled up, not moved):

```
union min [-1.7475, -0.1657, -3.2193]   union max [1.7475, 1.8659, 3.7216]
body  min [-1.7470,  0.0910, -3.4200]   body  max [ 1.7480, 2.3620, 3.6050]
  nose short 0.2007 m (the front wheel hulls reach z -3.219)   past the tail  0.1166 m
  below the floor 0.2567 m                                     below the roof 0.4961 m
  x: -0.0005 / -0.0005 m (the only axis that agrees)
```

So the union is not the body hull either — the scaled front wheels now overhang the front of the
chassis hull — and the union's bbox is 20 / 12 / 26 / 50 cm away from the body bbox. **B-10's gate
cannot pass on the values T-22 records**, and nothing in T-22 says what would move anything.

**Verdict: BROKEN** (a derived claim, wrong by construction because it assumes concentricity the
data does not have).

---

## A11 · "whether the donor's `hknpExternMeshShape` still bounds the uncovered body is a runtime question"

**Claim.** MODLOG UNKNOWN 2 (continued): *"whether the donor's `hknpExternMeshShape` (Serpente panels)
still bounds it acceptably is a runtime question, not a file question"*. `hull_set.body.note`: *"the
fine shell is the `hknpExternMeshShape`, whose quantization frame is UNKNOWN"*.

**Test.** There are 18 extern mesh shapes in the file, one per part (`CPfxPartIndexProperty` on each).
The body's is at `off 68480`, part index 0:

```
sportsmuscle_body hknpExternMeshShape  AABB
  min [-1.100, 0.074, -1.261]  max [1.094, 1.556, 2.566]   ->  2.194 x 1.482 x 3.827 m
scaled body hull (T-22's own numbers)                        ->  3.495 x 2.032 x 6.167 m
Batmobile body bbox (parts_manifest)                         ->  3.495 x 2.271 x 7.025 m
```

The extern mesh is the donor's body shell, 3.83 m long, unscaled (G2-30: it may **not** be written),
and it is **strictly inside** the scaled hull on all three axes (2.19 < 3.50, 1.48 < 2.03,
3.83 < 6.17). It cannot cover any of the 0.975 m front gap, the 0.496 m roof gap, or the width. So
this is not a runtime question: the file already says the answer is "no", and the note invites B-10 to
spend a phase-Q launch finding out.

**Verdict: BROKEN** — a "cannot be decided from the files" claim that the files decide.

---

## A12 · "the 11 T-8 parts have no slot"

**Claim.** `T-P3`: *"…11 T-8 parts have no slot"*. MODLOG: *"they are new parts, and giving them
collision needs a new hull, which is the UNKNOWN above"*; `decomposition.new_hull`: *"only an
existing slot can be written; the object count (54) is fixed"*.

**Test.** The count of new parts is right (`T8_PARTS.json`: 11 parts — turret, cannon, machine gun,
riot suppressor, 2 missile pods, 4 aero flaps, jet). "No slot" is only true in the narrow sense that
no *part index* of a T-8 part has a hull. What else is in the file:

```
54 hull objects;  7 are used by the Batmobile's mapped parts (body, 2 doors, 4 wheels)
54 - 7 = 47 hull objects belong to parts other than those 7
G2-30 §5, proven and round-tripped:
  "replace the sportsmuscle_wheel_f_l slot with the sportsmuscle_body hull block
   704 B, 20 v / 12 p  ->  1776 B, 36 v / 47 p, file 340,368 -> 341,440 B"
```

So a slot is not a fixed-size hole: a slot can hold **any existing hull block**, and 47 blocks the
Batmobile does not otherwise use are sitting in the same file. Whether one of them is a *good* shape
for a missile pod is a build decision — but "there is no slot" is not established, because the card
only enumerated the 7 slots it binds and the 14 bumper hulls it rejects. The stronger, correct claim
would be "no slot has a shape that fits a T-8 part, and no *new* shape can be authored".

**Verdict: WEAK.** The conclusion (T-8 parts get no collision in B-10) may still be the right one,
but it is derived from looked-at-only-the-7-slots, not from the file.

---

## A13 · T-CO3 `keep`: "38/42 = 1, the 4 wheels 0 → wheels are sim-only on both sides"

**Claim.** `T-CO3` value cell: *"donor's: 38/42 = 1, the 4 wheels = 0 (`world_collision_body_id` -1)"*,
take cell *"keep the donor's flags: wheels are sim-only on both sides"*.

**Test 1 — the flag counts.** HOLDS exactly: 42 parts, 38 with `has_world_collision_shape = 1`, and
the four 0s are `sportsmuscle_wheel_f_l/_f_r/_r_l/_r_r`, all with `world_collision_body_id = -1`
(and `raycast_body_id` 22 / 23 / 36 / 37). PARTS_TABLE's part order equals the module's part order
(0 mismatches of 42), so the flags are not mis-attributed.

**Test 2 — does the flag mean what the take says?** No. `has_world_collision_shape = 1` does not mean
"has a hull bound to it": `sportsmuscle_front_bumper` (idx 22) and `sportsmuscle_rear_bumper`
(idx 6) are both **1**, and both have zero part-indexed hulls (§A4). Conversely the four wheels are
**0** and each has a hull. Reading the flag as "collision on/off" is the R5 move; the behaviour it
actually names is "this part belongs to the world body", which for the wheels is false because they
hang off raycast bodies.

**Test 3 — "on both sides".** For the donor, "sim-only" is now *provable*: wheels have raycast bodies
22/23/36/37 at the four stations and world body −1. For the BmAK side there is nothing to test: the
only BmAK physics asset is `Batmobile_V3_Destroyed_Physics`, whose 8 wheel/suspension `RB_BodySetup`
boxes are the **wreck's** envelopes (§A5). Whether the driveable BmAK car's wheels are sim-only is
UNKNOWN from the files — the argument that the Batmobile side should match is a design choice (and a
reasonable one), not a measurement.

**Verdict: WEAK.** The disposition (`keep`) is defensible and the donor half is solid; the stated
grounds are a flag-name reading, and the "both sides" half is unfalsifiable from the data the card
cites.

---

## A14 · the tyre diameter

**Claim.** `tyre_basis`: *"2 x stations.json radius (TYRES.md §1: the tread diameter is 2 x the
contact radius by design)"*; `tyre_diameter_m: 1.3654`.

**Test.** TYRES.md §1 measures the tread Ø from wheel-bone vertices: 1.3652 / 1.3657 / 1.3654 /
1.3652 m, mean 1.3654. `stations.json` radii 0.6829 / 0.6826 / 0.6826 / 0.6827, mean 0.6827 →
1.3654. TYRES.md states the identity holds to ≤ 0.6 mm per corner. `land_global`'s own
`front_wheels.radius` 0.68275 / `rear_wheels.radius` 0.68265 bracket the same value.

**Verdict: HOLDS.** One nit: one `k` is applied to all four wheels though their radii differ by
0.3 mm — irrelevant physically, and it makes the §12 equation inexact (§A6).

---

## A15 · `stations.corners` copies `tyre_width` per corner

**Claim.** The json's `stations.corners.<c>` carries `{hub_true, radius, tyre_width}` per corner, and
`T-P3`'s evidence cell offers `t16_collision.json` as the hull-set record.

**Test.** TYRES.md §1, in the same table the card cites as its `tyre_basis`:

> **Station `tyre_width` is mirrored L↔R in `stations.json`**: the file's f_l 0.7325 is the mesh's
> f_r width 0.7325, and the file's f_r 0.7314 is the mesh's f_l 0.7314 … Nothing in `stations.json`
> records a `tyre_bone`, so the derivation cannot be traced; **whoever consumes `tyre_width` for
> physics must check the corner attribution (R3)**.

The json copies the four widths verbatim with no flag. The collision numbers are unaffected (T-22
uses `radius` only, and `radius` is not mirrored), so this is a trap for the next card, not a wrong
number in this one.

**Verdict: WEAK** (a known-untraceable value recorded without its caveat, in a record that B-10 reads
as authoritative).

---

## A16 · the done block's own numbers

**Claim.** MODLOG T-22 done: *"One hull per part, **300-1,776 B**, 8-36 vertices, 5-47 planes…
**4/4** tamper tests"*, and the ledger rebuild quoted as *"next 39 keep 61 … blocked 14 out 35"*.

**Test.**

```
t16_collision.json  hull_extent_range : [400, 1776]
smallest hull block : 400 B   (so "300" is wrong; the appended T-22 correction says exactly this)
```

The appended correction fixes 300 → 400, so the record now contains both — a reader who stops at the
done block keeps the wrong number. The ledger summary has also drifted, as a live ledger must:

```
today:  ledger 198 rows | edit 16 next 40 keep 60 epe 26 re-read 0 blocked 13 out 36 superseded 7
then :  ledger 198 rows | edit 16 next 39 keep 61 epe 26 re-read 0 blocked 14 out 35 superseded 7
both:   t_rows.py check -> check ok;  status_audit.py --check -> STATUS.md is current
```

The three T-22 dispositions are still in force (the `--check` above re-asserts them). The "4/4 tamper
tests" claim was **not** re-verified here: each tamper writes into `T1_TRANSLATION.md`,
`T2_TRANSLATION.md`, `t16_collision.json` or `T_ROWS.jsonl`, and this pass is read-only. By
inspection the check is real — it compares the json field-by-field, both row lines, the §7 prose
regex, and the three ledger dispositions — so the claim is plausible; it is simply not evidence I
produced.

**Verdict: WEAK** (record hygiene: a stale number kept alive beside its correction; one claim out of
reach of a read-only pass).

---

## What survives, and what the next card has to fix

**Survives.** The BmAK inventory (32 bodies × 4 byte-identical packages, 0 spheres, no chassis body,
asset `Batmobile_V3_Destroyed_Physics`); the donor inventory (430 objects, 22 compounds, 54 hull
objects, 40 part-indexed, 14 bumper hulls across two static compounds, `convex_radius` 0.01 m
median); the 42-part flag census (38/42, the four wheels at 0 with body −1, part order matched);
the tyre diameter; the wheel `k` for the diameter; the disposition set; the ability to write a
scaled hull and have the reader accept it (G2-30's round trip).

**Does not survive.** "0 station quads in the collision file" (A2); the axis pairing behind every
non-wheel `k` (A8); the placement sentence, hence the body hull's position and both door hulls
(A9); the "~0.43 m each end" figure (A10); "the extern mesh may cover it" (A11); "one hull per part /
max_hulls 54" as a parameter set (A3); "no slot for the T-8 parts" as a closed question (A12);
"both sides" in T-CO3's take (A13); and the full-extent reading of the BmAK boxes (A1), which is the
one that would invalidate `T-CO2` outright if the repo's other artifact is right.

**Smallest set of changes that would make the card honest** (no new work, no new files):
1. `stations_in_file` should be `4` (with the raycast body ids), and the sentence "the quads live in
   the vmodc … not in the physicsc" should be replaced by "both carriers hold the four stations and
   both already carry the Batmobile's values (`test-003` → `test-090`)".
2. `_box_m` should state one reading and cite the test that chose it — or say UNKNOWN and make
   `T-CO2` conditional on it.
3. The door rows should record `k` per axis assignment (or `k_in`/`k_out` per permutation), and
   `Rear_Door_MIDDLE` should not be handed a 28 cm hull without a note.
4. The translation parameter should be replaced by the two offsets that actually exist —
   `hull_centre → target part centre` for the 40 vehicle-space hulls, `body_entry position` for the
   4 wheel hulls — because B-10's 5 cm gate is decided by them.

No game was launched; no build, save, dropzone or git state was touched. `t22_collision.py --check`,
`t_rows.py check` and `status_audit.py --check` were run read-only and all exited 0.
