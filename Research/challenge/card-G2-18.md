# Assumption challenge — G2-18 · Interaction points and stunt areas

**Scope.** Finished card `GRAB_BACKLOG.md:670-681` (M, deps P0-1), its §12 row (`:1301`),
MODLOG §"G2-18 · Interaction points and stunt areas — done" (`:11018`, intended change `:10974`)
and the outputs it names: `Research/JC3Grab/INTERACTION.md` (312 lines), `INTERACTION.json`,
`Tools/scripts/jc3interact.py` (846 lines). Rules read first: `GRAB_BACKLOG.md` §0.5 R1–R14.

**Method.** Re-ran the card's check, then attacked each claim with the data on disk: the donor
entity cache (`E:\Modding\JustCause3\_grab\entities\…sportsmuscle_civilian_01.ee.json`), the decoded
`.epe` JSON, `Research/Epe/serpente_civilian.xml`, `Working/TrueScale/stations.json` and
`Working/TrueScale/body_lod1.rbm` (via `rbm_geom`). No archive was opened, nothing was written
outside this file, no game launched, nothing committed.

**Change record (AGENTS.md).** One file written: this one, `Research/challenge/card-G2-18.md` —
the path the task names, beside the existing `card-G1-*.md` / `card-G2-*.md`. Revert: delete it.

**The card's own check, re-run:**

```
$ python Tools/scripts/jc3interact.py --check
PASS: 85 objects (entry 29, exit 26, interaction 3, point 8, transition 12, trigger 7),
transforms own 15 / inherited 70 / none 0, verdicts {'floating': 23, 'inside': 30,
'n/a (container origin)': 32}, stunt 3/32 active (64 welds), mesh 28940v/20000t, json match True
EXIT=0
```

The machine reproduces. Everything below is about what the census, the frames and the verdict
counts are taken to mean.

---

## VERDICT

| # | assumption | verdict |
|---|---|---|
| A1 | "every interaction object" = the 85 six-prefix objects | **WEAK** — 85 of 255 `CInteraction*` objects; 6 `set.node.*` and 162 condition nodes are outside |
| A2 | 15 own / 70 inherited / 0 without a transform | **HOLDS** |
| A3 | the 32 "n/a" objects have no position because *their placement is the point they transition from* | **BROKEN** — entries carry no link at all; placement is UNKNOWN, not inherited from a point |
| A4 | Serpente frame = the 135-point deform envelope; all points in one space | **HOLDS** |
| A5 | the deform envelope and the mesh union "agree in z" | **WEAK** — 2.527 vs 2.5643 (3.7 cm), and they disagree by 0.43 m in y |
| A6 | the envelope is wider in x "because bumper corners deform" | **WEAK** — unmarked causal reading |
| A7 | the bbox-normalised verdicts (30 inside / 23 floating / 0 on-surface) mean the positions are not portable | **BROKEN** — a uniform wheelbase map puts **30** of the same 53 **on-surface** |
| A8 | "0 on-surface" | **WEAK** — true only below a 4 cm threshold; at 5 cm it is 32 |
| A9 | 30 objects are "inside the shell" (three-ray parity) | **WEAK** — all 30 are 2-of-3 votes, none unanimous |
| A10 | `surface_m` is an exact point-triangle distance | **WEAK** — it is an upper bound (≤ 18.8 mm high) |
| A11 | a trigger's scale is a *half*-extent | **WEAK** — UNKNOWN, disclosed in §5 but printed as fact in the table |
| A12 | `trigger.*` is the only class with a scaled transform | **HOLDS** |
| A13 | stunt areas: 3 of 32 active, 64 weld rows / 8 real welds, front pair coincident, triangle sets | **HOLDS** |
| A14 | `main_area` is "the roof/trunk deck" | **WEAK** — name + part binding, no decoded semantic |
| A15 | 79 distinct JSON names; 85 objects collapse to 79 because 3 transitions repeat | **HOLDS** |
| A16 | `wheelbase_fraction` 0 at the front axle (front = −z) | **HOLDS** — but the doc never shows the evidence |
| A17 | `--check` re-derives every number; no typed literals | **WEAK** — prose has typed "135", "198", "seven", "three"; one assertion row is literal-vs-literal |
| A18 | driver/passenger/seat roles | **WEAK** — by object *name*; `interaction` is `00000000` on every row |
| A19 | §4's "the graph is portable: entry → point → exit" | **BROKEN** — the edges and the 162 conditions are not decoded |

**One-line summary.** The decode is careful and the stunt-area work is solid — every count,
weld, triangle and coincident pair reproduces exactly, and the XML transform reading is correct.
But the document's headline negative ("the positions do not land on the shell", "30 inside") is a
property of one chosen mapping: scale the donor by its wheelbase instead of its bbox and 30 of the
same points sit **on** the shell within 3 cm. The "inside" count is a 2-of-3 ray vote in which no
point is ever unanimous, and the 32 "no position" objects are justified by a graph edge
(entry→point) that exists nowhere in the file.

---

## A1 · "every interaction object" = 85 — **WEAK**

**Claim.**

```
INTERACTION.md:3-4    "Every interaction object in the Serpente donor `.epe`, its animation/state
                       strings, and the `StuntAreas` module decoded from the entity cache"
INTERACTION.md:41     "**85 objects** in the donor `.epe` match the six prefixes: `entry.*` 29, …"
INTERACTION.md:242-4  "The **graph** is portable: `entry.*` → `point.*` → `exit.*` with a `state`
                       string each, so a rebuilt graph keeps the vanilla state names and the
                       animation wiring stays valid."
```

**Assumption.** "Interaction object" = an object whose name begins with one of the six prefixes the
card lists, so the 85 are the whole interaction layer.

**Test.** Walk `Research/Epe/serpente_civilian.xml` and classify every object:

```
objects in xml: 450
classes with Interaction/Trigger:
  CInteraction 3, CInteractionTrigger 7, CInteractionGraph 1, CInteractionContext 1,
  CInteractionGraphEntry 29, CInteractionGraphPointNode 8, CInteractionGraphExit 26,
  CInteractionGraphTransition 12, CInteractionComponentSetNode 6,
  CInteractionGraphParentIsUpRightCondition 41, CInteractionGraphNodeAboveWaterCondition 27,
  CInteractionGraphParentVelocityCondition 24, CInteractionGraphVehicleSeatPlayerUsableCondition 24,
  CInteractionGraphParentPlayerLockedCondition 17, CInteractionGraphNodeOccupiedCondition 15,
  CInteractionGraphExitObstructedCondition 5, CInteractionGraphUserIsPlayerCondition 4,
  CInteractionGraphEntryIsFacingParentCondition 2, CInteractionGraphStuntExitValidCondition 2
prefixes: {'interaction': 3, 'set': 6, 'entry': 29, 'point': 8, 'exit': 26,
           'transition': 12, 'trigger': 7}
objects of class CInteraction*: 255
   with a prefixed name: 85
```

**Result.** The interaction *layer* is 255 objects: the 85 named nodes, 1 `context`, 1 `graph`,
**6 `set.node.*`** (`CInteractionComponentSetNode`, the seat's component-set roots, nested under
`interaction.seat.driver` / `seat.stunt` / `seat.passenger1`) and **162 condition nodes**
(`ParentIsUpRightCondition` 41, `NodeAboveWaterCondition` 27, …) that gate every entry, transition
and exit. The card's Do step names the six prefixes, so the extraction is what was asked; the md's
prose ("Every interaction object") and §4's portability claim are not: the edges and their
conditions are exactly what a rebuilt graph would have to reproduce, and none of them is in the 85.
The conditions do carry data (`check` 107, `max` 24, `min` 24 values) that this card never reads.

> **Verdict: WEAK.** The 85 are a complete set *for the six prefixes*, not for the interaction
> layer; "the wiring stays valid" is asserted without the wiring being decoded.

---

## A2 · 15 own / 70 inherited / 0 none — **HOLDS**

**Claim.** `INTERACTION.md:43-46`, validation rows (`:266-271`).

**Test.** Recount from the XML with the same rule (own `world` = own; else nearest ancestor with a
`world`):

```
world count in xml (all objects): 66
prefixed with own world: 15
prefixed inheriting an ancestor's world: 70
prefixed with none: 0
```

and the JSON side:

```
prefixed object rows: 85  distinct: 79
objects without a world among prefixed (json): 72  → 54 carry a world value
duplicate node paths: 26   '?' placeholders: 409
```

**Result.** 15 + 70 = 85 exactly, and the two triggers the XML has and the JSON lacks
(`trigger.driver.fast`, `trigger.stationary.stunt`) are exactly the documented gap. The count and
its provenance hold.

> **Verdict: HOLDS.**

---

## A3 · the 32 "n/a" objects — **BROKEN**

**Claim.**

```
INTERACTION.md:118-121  "An object that only inherits the identity matrix of the `graph` or
                         `context` container has **no position of its own** - its placement is
                         defined by the point it transitions from - so it is marked
                         `n/a (container origin)` rather than given a fake verdict at 0,0,0."
```

**Assumption.** An entry's placement is recoverable from the point it transitions from, so the
n/a is a bookkeeping choice, not missing data.

**Test.** Print the members of every prefixed object and the parent each hangs under:

```
== CInteractionGraphEntry 29
   entry.driver          parent graph  members {_class, disable_event, enable_event, enabled,
                                             interaction:'00000000', name, state:'S_ENTER_DRIVER_VEHICLE'}
   entry.ai.passenger1   parent graph  members {… same seven …}
parents of entry.*: Counter({'graph': 29})
parents of point.*: Counter({'graph': 8})
parents of exit.*: Counter({'point.driver': 14, 'point.passenger1': 10, 'point.stunt': 1,
                            'point.stunt.hood': 1})
parents of transition.*: Counter({'point.driver': 3, 'point.passenger1.onground': 2,
                                  'point.passenger1.side': 2, 'point.driver.onground': 2,
                                  'point.driver.side': 2, 'point.passenger1': 1})
parents of interaction.*: Counter({'context': 3})
parents of trigger.*: Counter({'context': 7})
parents of set.*: Counter({'interaction.seat.driver': 2, 'interaction.seat.stunt': 2,
                           'interaction.seat.passenger1': 2})
```

No prefixed object carries a pointer member (`world`, `state`, `interaction`, `modifier`,
`enabled`, `enable_event`, `disable_event`, `node` are the only names present); `interaction` is
`00000000` on all 55 rows that have it.

**Result.** Exits and transitions sit **inside** their point node in the tree, so inheriting the
point's transform is structural and correct. Entries do not: all 29 hang directly under `graph`,
side by side with the 8 points, and carry no reference to any point. There is no decoded
entry→point edge anywhere in the file. So the entries' placement is **UNKNOWN**, and the sentence
"its placement is defined by the point it transitions from" attributes data that does not exist.
The `n/a` label is the honest part; the justification is not. 29 of 85 objects — the ones WLD-3
("entry/exit points sit on the Batmobile's sides") is about — have no position in the donor.

> **Verdict: BROKEN** for the causal claim; the n/a count itself is right.

---

## A4 · the Serpente frame is the 135-point deform envelope — **HOLDS**

**Claim.**

```
INTERACTION.md:9-14   "Serpente deform envelope | -1.330 … 1.330 | 0.000 … 1.524 |
                       -2.560 … 2.527 | `DeformPoints.points[i].start_transform[12..14]`, 135 points"
INTERACTION.md:17-19  "the envelope is used as the Serpente frame because all 135 points are
                       provably in one space (they carry part bindings)."
```

**Test.**

```
deform points: 135
min: [-1.33, 0.0, -2.5602]  max: [1.33, 1.5242, 2.527]
deform member names: deform_point_type.hash/.string, end_transform[0..15], from_part, from_part_hash, …
```

**Result.** The count, the three ranges and the "one space" argument (each point has a `from_part`
binding, and the same translation slot is used for all of them) reproduce exactly.

> **Verdict: HOLDS.**

---

## A5 · "the deform envelope and the mesh union agree in z" — **WEAK**

**Claim.** `INTERACTION.md:15-17` (two table rows and the sentence "…agree in **z** (the
longitudinal axis) and the envelope is the wider in x").

**Test.**

```
mesh count: 198
union z: -2.57 2.5643      union y: -0.4288 1.511
envelope z: -2.5602 2.527  envelope y: 0.0 1.5242
```

**Result.** In z the two frames differ by 1.0 cm at the front and 3.7 cm at the rear — "agree" is
fair for a 5.1 m car, and the doc prints both rows so a reader can see it. In y they do **not**
agree at all: the mesh reaches 0.429 m *below* the envelope's floor (wheels/underbody are not
deform points), which is not stated and matters for the mapping's y axis (A7). The envelope is
also 0.27 m wider per side than the mesh, which the doc explains (A6).

> **Verdict: WEAK** — one axis agrees, the other is left implied.

---

## A6 · "wider in x because bumper corners deform" — **WEAK**

**Claim.** `INTERACTION.md:17-18`.

**Assumption.** The 0.27 m of extra half-width is deform points on bumper corners.

**Test.** Which parts do the extreme-x points bind to?

```
$ python - <<'EOF'   # deform points with |x| > 1.06 (the mesh half-width)
points |x|>1.06: 2
  point 62: x=-1.330 from_part=sportsmuscle_body
  point 66: x=1.330 from_part=sportsmuscle_body
```

**Result.** The two outermost points bind `sportsmuscle_body`, not a bumper part — so the doc's
"bumper corners deform" attribution is not carried by the binding data; the envelope simply has
two body points wider than any mesh. The explanation is a plausible causal reading of a decoded
fact (the mesh *is* narrower than the envelope), unmarked as inference, and nothing rests on it.

> **Verdict: WEAK** (an unlabelled inference, and its stated cause is not in the binding).

---

## A7 · the verdict census: "30 inside / 23 floating / 0 on-surface" ⇒ "not portable" — **BROKEN**

**Claim.**

```
INTERACTION.md:34-38   "Mapping (analysis only …): u = (p - serpente_min) / (serpente_size);
                         p' = bat_min + u * bat_size"
INTERACTION.md:270-3   "The **positions** are not: every one of the 8 points is a Serpente-space
                         translation, and bbox-scaled onto the Batmobile they do **not** land on
                         its shell - the counts are 30 inside the shell, 23 floating, 0 on-surface"
INTERACTION.md:286-8   "they too scale *away* from the shell … Geometry has to be re-fitted to the
                         Batmobile, not scaled"
```

**Assumption.** The per-axis bbox normalisation is a neutral way to place the donor on the
Batmobile, so the resulting verdicts describe the data.

**Test.** Recompute the verdicts with the same mesh and the same 30 mm rule, under two mappings:
the card's bbox map, and a uniform scale matched on wheelbase (the one physical correspondence the
doc itself reports: 5.0289 / 3.003 = 1.6746), front axle to front axle, y from the mesh floor:

```
card bbox map                    -> {'on-surface': 0,  'inside': 30, 'floating': 23}  min dist 0.0405 m
uniform wheelbase map (s=1.6746) -> {'on-surface': 30, 'inside': 0,  'floating': 23}  min dist 0.0093 m
```

**Result.** The same 53 positioned objects are "30 inside, 0 on-surface" under the bbox map and
"0 inside, 30 on-surface" under a uniform wheelbase map — and 9.3 mm is on the shell by any
reading. The count is a property of the mapping, not of the positions: a car-to-car transfer scaled
by its wheelbase lands on the shell; one scaled independently per axis (x 1.3139, y 1.49,
z 1.3809) does not, because the donor and the Batmobile have different proportions. The doc's
conclusion ("re-fit, don't scale") may still be the right engineering call, but the evidence
offered for it is circular, and §4's flat "The positions are not [portable]" is refuted by the
counter-map.

> **Verdict: BROKEN** as stated. The measurement is real; the inference is map-dependent.

---

## A8 · "0 on-surface" — **WEAK**

**Claim.** The three verdict counts, and `INTERACTION.md:114` ("**on-surface** = nearest Batmobile
triangle ≤ 0.03 m").

**Test.** Same distances, different thresholds:

```
threshold 0.01 m -> {'on-surface': 0,  'inside': 30, 'floating': 23}
threshold 0.03 m -> {'on-surface': 0,  'inside': 30, 'floating': 23}
threshold 0.05 m -> {'on-surface': 32, 'inside': 0,  'floating': 21}
threshold 0.08 m -> {'on-surface': 33, 'inside': 0,  'floating': 20}
threshold 0.10 m -> {'on-surface': 33, 'inside': 0,  'floating': 20}
```

and the two closest points:

```
point.stunt.hood   0.0405 m   floating
point.driver       0.0428 m   inside
```

**Result.** "0 on-surface" is true only because the threshold sits 7 mm under the nearest point.
A 5 cm rule — reasonable for a 20000-triangle shell ~0.5 m across — turns 32 of 53 into
on-surface. The number is disclosed and the threshold is printed, so this is a fragility, not a
falsehood.

> **Verdict: WEAK.**

---

## A9 · 30 objects "inside the shell" — **WEAK**

**Claim.** `INTERACTION.md:114-117` ("otherwise **inside** if three-ray parity says the point is
within the shell"), §5 ("the three-ray parity test can disagree with itself … an `inside` verdict
near an opening is weak").

**Test.** Recompute the three ray votes per object:

```
ray votes for the 53 positioned objects: 3 = 0   2 = 30   1 = 7   0 = 16
of the 30 'inside': unanimous 0 | 2-of-3 30
```

**Result.** Not one of the 30 is a unanimous inside vote; every one is a 2–1 split, and 7 more
objects are 1-of-3 (classified floating). For a closed shell an interior point would vote 3–0 on
all three rays, so the test is not resolving interior/exterior here — the body mesh is an open
shell (wheel arches, windows, panel gaps) and parity is near-arbitrary. The doc flags the method as
weak "near an opening"; the data says the split is the *rule*, not the exception, for every positive
verdict. The count 30 is therefore not a measurement of "inside".

> **Verdict: WEAK** (disclosed method, undiscussed ubiquity of the disagreement).

---

## A10 · `surface_m` is exact — **WEAK**

**Claim.** `jc3interact.py:255` "Exact point-triangle distance (Ericson), vectorised over triangles
per point"; the md prints those distances to 0.1 mm.

**Test.** Compare `nearest_distance()` with a region-based closest-point-on-triangle over all 20000
triangles:

```
finite: True
max |approx-exact| (m): 0.018801
approx overstates by >1 mm at 7 points; understates at 0
   trigger.passenger1      approx 0.7839 exact 0.7651 diff 18.80 mm
   trigger.driver          approx 0.7831 exact 0.7647 diff 18.49 mm
   point.stunt             approx 0.3495 exact 0.3439 diff  5.56 mm
```

and for the stunt surfaces:

```
main_area vertex centroid: approx 0.0746 / exact 0.0635
main_area worst vertex:    approx 0.5955 / exact 0.5957
```

**Result.** The function clamps barycentrics to the triangle instead of selecting the closest
feature, so it returns a point *on* the triangle that is not always the nearest one: a guaranteed
upper bound, never below the true distance. No verdict flips at 30 mm (the nearest non-on-surface
point is 40.5 mm), but the printed millimetres are not exact — up to 1.9 cm high, and the
`main_area` centroid figure in the doc is 0.0746 instead of 0.0635.

> **Verdict: WEAK** — the label "exact" is wrong; the classification survives.

---

## A11 · a trigger's scale is a half-extent — **WEAK**

**Claim.**

```
INTERACTION.md:126-128  "`trigger.*` is the only class with a **scaled** transform, i.e. a volume
                         rather than a point:"  … "| trigger | scale (half-extent x,y,z) | …"
§5                      "read as a half-extent because the translation is in the last row; no file
                         states it, so the box size is *derived*."
```

**Test.** The raw transforms confirm the layout the script assumes (translation in the last row,
scale on the diagonal):

```
trigger.driver raw: [2.65,0,0,0, 0,1.91,0,0, 0,0,2.83,0, -1.48,-0.117,0.287,1.0]
   row3 [-1.48 -0.117 0.287 1.0]   col3 [0 0 0 1]   row norms [2.65 1.91 2.83]
point.driver  raw: [1,0,0,0, 0,1,0,0, 0,0,1,0, -0.44,0.34,0.2,1]
```

**Result.** The translation reading is *proved* by the trailing 1.0 and the unit 3×3 of the point
objects. The half-extent reading is not: an engine scale of (2.65, 1.91, 2.83) is a multiplier on
whatever the trigger's base shape is, and no file says that base is a unit half-cube. The doc does
say this in §5, but the table header states it as fact and the md prints "a volume" first. For
`trigger.driver` the two readings are 5.3 × 3.8 × 5.7 m versus 2.65 × 1.91 × 2.83 m — both
plausible for a door-entry volume, so the data cannot settle it.

> **Verdict: WEAK** — correctly flagged as derived, incorrectly presented as a decoded unit.

---

## A12 · `trigger.*` is the only class with a scaled transform — **HOLDS**

**Test.** Every own-`world` named object in the XML, split by whether its 3×3 row norms are 1:

```
own-world named objects with unit scale: 59
scaled own-world objects: 7
    trigger.driver                      [2.65, 1.91, 2.83]
    trigger.step.to.stunt               [10.0, 10.0, 10.0]
    trigger.driver.fast                 [3.69, 1.776, 6.749]
    trigger.passenger1                  [2.65, 1.91, 2.83]
    trigger.stunt.vehicle.to.vehicle    [19.12, 14.11, 23.41]
    trigger.stationary.stunt            [1.948, 1.596, 5.116]
    trigger.stunt                       [14.32, 9.31, 18.61]
```

**Result.** Exactly the seven triggers, nothing else. (The md prints `trigger.driver.fast`'s z as
6.748 against the file's 6.7485…; rounding, not a wrong value.)

> **Verdict: HOLDS.**

---

## A13 · the stunt areas — **HOLDS**

**Claim.** `INTERACTION.md:214-235`: 3 areas in 32 slots, 29 `NoName`, 64 `welding_info` rows of
which 8 are real (0↔1 ×6, 0↔2 ×1, 1↔2 ×1), `front_area` / `front_signature_area` coincident, each
a triangle set (`vertices3D_local` + `triangle_indices`) bound to a part.

**Test.** Re-read the module rows:

```
slot 0: name='front_area'  part='sportsmuscle_hood'  tris=4  active=1  npoints=6
slot 1: name='front_signature_area' part='sportsmuscle_hood_signature' tris=4 active=1 npoints=6
slot 2: name='main_area'   part='sportsmuscle_body'  tris=8  active=1  npoints=10
distinct names: [('NoName', 29), ('front_area', 1), ('front_signature_area', 1), ('main_area', 1)]
weld rows: 64  real: 8
pairs: Counter({(1, 0): 6, (2, 0): 1, (2, 1): 1})
area 0 vs 1 identical vertices: True  | nonzero: 18
area 0 vs 2 identical vertices: False | nonzero: 18
```

and the surface distances, recomputed independently:

```
front_area            center 0.1035 (exact 0.1035)  centroid 0.1512  max vertex 0.3740  0/6 on-surface
front_signature_area  identical
main_area             center 0.0197 (exact 0.0197)  centroid 0.0746  max vertex 0.5955  0/10 on-surface
center vs vertex centroid gap (local): main 0.1474, front 0.0480
```

**Result.** Every number in §3 reproduces: 3/32 active, 64 rows, 8 welds with the stated pair
multiplicities, coincident front pair (identical 18 floats), real triangle sets, part indices
24 / 25 / 0, and the "tilted, not lifted" reading (centre 0.0197 m on-surface but every vertex
≥ 0.12 m). The double-centre presentation is exactly the right way to show it.

> **Verdict: HOLDS.**

---

## A14 · `main_area` is "the roof/trunk deck" — **WEAK**

**Claim.** `INTERACTION.md:236-238` ("The `main_area` is the roof/trunk deck").

**Test.** What the module says about it: `name='main_area'`, `part_name='sportsmuscle_body'`,
`bbox` y 1.104…1.524, z −0.923…2.414, 10 points. Where it maps: centre at Batmobile
(0.001, 2.049, 1.145) — top rear of the body.

**Result.** The geometry is consistent with a rear-deck surface, and the part binding is real.
But "roof/trunk deck" is a reading of the name and the shape; no file labels the surface. Nothing
load-bearing rests on the noun (the numbers are the deliverable), so this is a minor unmarked
inference.

> **Verdict: WEAK** (inference, clearly benign).

---

## A15 · 79 distinct JSON names — **HOLDS**

**Claim.** `INTERACTION.md:196-204`.

**Test.**

```
objects (json): 450
prefixed object rows: 85  distinct: 79
duplicates: {'transition.passenger1': 3, 'transition.stunt': 3, 'transition.driver': 3}
duplicate node paths: 26   '?' placeholders: 409
```

**Result.** 85 − 6 = 79, and the duplicates are exactly the three transition names that appear
under more than one point (the md lists all three). The "26 duplicate paths" and the `?`
placeholders also reproduce, which justifies the choice of the XML tree as authoritative.

> **Verdict: HOLDS.**

---

## A16 · `wheelbase_fraction` 0 at the front axle — **HOLDS** (evidence unstated)

**Claim.** `INTERACTION.md:122-124` ("`wheelbase_fraction` is 0 at the front axle and 1 at the rear
axle (negative = ahead of the front axle)").

**Test.** Serpente hardpoints from `LandGlobal`:

```
base_wheel_hardpoint_positions[0..3]: (±0.885, 0.400, -1.557) and (±0.885, 0.400, +1.446)
wheelbase 3.003  track 1.77
```

Which end is the front? The hood mesh:

```
sportsmuscle_hood_lod1.rbm  z -2.4315 … -0.8703     (z negative)
sportsmuscle_hood_signature_lod1.rbm z -2.4315 … -0.8703
```

and the Batmobile's own corners (`stations.json`): front z −2.570 / −2.5699, rear +2.4589.

**Result.** `−z` is the front on both vehicles, so fraction 0 at z=−1.557 is correct and the
computed values (`point.stunt.hood` z=−1.505 → 0.017; `point.stunt` z=+0.422 → 0.659) are right.
The doc never shows the hood/`front` evidence, so the convention is an unproven premise a reader
cannot check from the document alone.

> **Verdict: HOLDS** (convention correct; the evidence is not printed).

---

## A17 · `--check` re-derives every number — **WEAK**

**Claim.** `INTERACTION.md:5-6` ("Rebuilt by `python Tools/scripts/jc3interact.py --check`"), and
MODLOG's "every number must be re-derivable".

**Test 1 — prose literals.** The generator's template contains bare counts:

```
jc3interact.py:521  "`DeformPoints.points[i].start_transform[12..14]`, 135 points"
jc3interact.py:523  "union of the 198 part-mesh AABBs"
jc3interact.py:530  "all 135 points are provably in one space"
INTERACTION.md:255  "and the three `point.stunt*` nodes are the ones ANI-9 needs first."
```

`--check` compares `render_md(d)` with the file, so a typed literal renders the same on both sides
and can never fail. Two of them are right today (135 deform points, 198 meshes, both verified in
A4/A5); one is wrong:

```
point.*: ['point.driver', 'point.driver.onground', 'point.driver.side', 'point.passenger1',
          'point.passenger1.onground', 'point.passenger1.side', 'point.stunt', 'point.stunt.hood']
point.stunt*: ['point.stunt', 'point.stunt.hood']     → two, not three
```

**Test 2 — a tautological assertion row.**

```
jc3interact.py:736  ("deform points", 135, 135),
```

measured and expected are the same literal; the deform count is never read. (The other rows do
read the built dict against a literal, which is a legitimate drift guard.)

**Result.** The build is genuinely re-derived from the XML, the entity cache, `stations.json` and
the `.rbm` — `--check` is not self-referential. But the validation table's "deform points 135 |
135" row cannot fail, and the prose's typed numbers (including the wrong "three `point.stunt*`
nodes") are invisible to it. That is the same class of defect the G2-14 rework fixed: numbers that
are correct today and cannot be regressed.

> **Verdict: WEAK.**

---

## A18 · driver / passenger / seat roles — **WEAK**

**Claim.** The role column of the census (`point.driver`, `entry.ai.passenger1`,
`interaction.seat.driver`), on which WLD-3 rests.

**Test.** The only role-bearing members in the file:

```
member names on prefixed objects: {'enabled': 102, 'world': 54, 'node': 6, 'state': 61,
                                   'modifier': 10, 'interaction': 55}
interaction values: '00000000' on all 55 rows that carry it
interaction.seat.driver members: {_class: CInteraction, name: 'interaction.seat.driver'}
```

**Result.** There is no seat id, no seat index, no role enum and no target slot. `interaction` is a
zero hash everywhere. "Driver", "passenger1", "seat.stunt" are read from the object **name** — the
same R5 pattern the rules warn about (a member read by its name rather than its behaviour). Here
the name is the only signal that exists, and the mapping name→role is self-evident for driver and
passenger1, so the practical risk is low; but "AI vs player" and "side" are name-only too, and the
seat interaction object carries *nothing* — the actual seat anchor is not in these 85 objects at
all.

> **Verdict: WEAK** — a name-based classification, stated as if decoded.

---

## A19 · "the graph is portable: entry → point → exit" — **BROKEN**

**Claim.** `INTERACTION.md:242-246`.

**Assumption.** The 85 named objects contain the graph's edges, so a rebuilt graph can reproduce
the behaviour with the same state strings.

**Test.** Same tree dump as A3 plus the condition inventory:

```
parents of entry.*: {'graph': 29}
parents of exit.*: 'point.driver' 14, 'point.passenger1' 10, 'point.stunt' 1, 'point.stunt.hood' 1
parents of transition.*: 'point.driver' 3, 'point.passenger1.onground' 2, …
CInteractionGraph*Condition classes: 162 objects (check 107 / min 24 / max 24 values)
CInteractionComponentSetNode: 6 (nested under the three interaction.seat.*)
```

**Result.** The *downward* side of the graph is present (exits and transitions hang under points),
but the *upward* side is not: nothing links an entry to a point, and the 162 condition objects that
decide which entry can fire and which exit is valid are outside the census entirely. A rebuilt
graph from these 85 rows would keep the state strings (real value for ANI-9) but could not
reproduce the wiring. The word "portable" overstates what was decoded.

> **Verdict: BROKEN** for the portability claim; the state-string inventory itself is sound.

---

## What this does and does not change

* **Confirmed:** 85 prefixed objects with the exact six-prefix split, 15/70/0 transform census,
  135-point envelope with its exact ranges, 198-mesh union, 3/32 stunt areas with 6/6/10 points,
  4/4/8 triangles, 64 weld rows / 8 real welds and the coincident front pair, the 7 triggers as the
  only scaled objects, the XML over JSON choice (79 names, 26 duplicate paths), the Serpente and
  Batmobile wheelbases (3.003 / 5.0289) and tracks (1.77 / 2.416, 2.569), the front = −z convention,
  and the "tilted, not lifted" stunt-area finding with its measured gaps.
* **Changed by a wider test:** the verdict census is mapping-dependent (30 on-surface under a
  wheelbase map), "0 on-surface" survives only a < 4 cm threshold, the "inside" count is a
  2-of-3 vote with no unanimous positive, `surface_m` is an upper bound not an exact distance
  (≤ 18.8 mm), and 29 entries have no position and no decoded link to one.
* **Presentational:** §4 says "three `point.stunt*` nodes" (there are two); the half-extent
  reading is printed as a unit; the validation table has one literal-vs-literal row.
* **Not done here:** no game was launched, no archive opened beyond the caches the generator uses,
  nothing was written into `D:\Games`, nothing committed. The 162 condition objects and the 6
  `set.node.*` nodes were counted and listed, not decoded — that is the next card's work, not this
  challenge's.
