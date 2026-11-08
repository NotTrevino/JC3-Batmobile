# Assumption challenge — card G2-30 (`.physicsc` write spike)

**Card:** G2-30, `GRAB_BACKLOG.md` §6 (line 782) and §12 (line 1313).
**Result under challenge:** `Research/JC3Grab/PHYSICS_WRITE.md` + `PHYSICS_WRITE.json` +
`Tools/scripts/jc3hkx.py write` (MODLOG "G2-30 · `.physicsc` write spike — done", line 11316,
and the same-session correction, line 11403).
**Rules read:** `GRAB_BACKLOG.md` §0.5 R1–R14.
**Mode:** read-only. No game, no `D:/Games` write, no commit, no secret. The only file written is
this one. Test blobs are the ones the card already left in
`E:/Modding/_JC3grab/hkx/write/` (5 files) and were only read.
**Method:** every claim was re-derived with inline Python against `Tools/scripts/jc3hkx.py`
(the reader/writer itself) plus direct byte reads of
`Builds/test-091/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc`
(340,368 B, the card's donor), `Working/Assembled/sportsmuscle_true.physicsc` and the five
written blobs. Nothing was written to the project except this report.

---

## VERDICT

**The capability the card claims is real and reproducible. Three load-bearing statements are
broken, and the invariant gate the card uses as its "done" proof is far weaker than the card
treats it.**

The four mechanical claims survive: the donor's data section is partitioned by typed objects on
all 234 shipped files (not just the donor), all 54 hulls re-emit byte-identically, the face table
reads as one 4-byte record per plane on 54/54 hulls with no ambiguous alternative, and the scaled
wheel writes exactly 252 B over 69 runs, changing 3 objects. But:

| # | assumption | verdict |
|---|---|---|
| A1 | "round trip identical" proves the decoder is exact | **WEAK** — proves the three decoded blocks' offsets/sizes, not their semantics |
| A2 | data section fully partitioned, "the file ends exactly at the last object" | **HOLDS** for the partition (234/234 files); **BROKEN** as worded (17,296 B of fixup tables follow the last object) |
| A3 | the 16 B remap stress "re-reads with a decoded graph identical object-for-object" | **BROKEN** — it prepends 16 B inside `hkRootLevelContainer`; object 0 changes 96→112 B and its fields shift |
| A4 | a grown child moves its ancestors' AABBs (2 compounds) | **BROKEN** — each dynamic compound's box is stored **twice**; the copy in `hknpDynamicCompoundShapeData` +0x60/+0x70 is left stale in both shipped artefacts (0.271 m and 2.086 m) |
| A5 | "passes every invariant → rows become buildable" (the invariants certify a correct hull) | **BROKEN** — a hull with planes 0.258 m off (with radius 1.0), radius 0, a 4 cm displacement, a ×1.05 scale, or the 3.68 m body hull in a wheel slot all pass with 0 violations |
| A6 | the AABB/union tolerance is a measured value | **WEAK** — 1 % of span + 1 mm and the convex radius are chosen thresholds; measured effects below |
| A7 | pointer slots must stay 0 because the loader fills them | **HOLDS** for the convention (316,471/316,471 slots are 0 across 234 files); **WEAK** for the mechanism (inferred; the reader never reads a slot) |
| A8 | the face table is one 4-byte record per plane (54/54) | **HOLDS** — unique candidate prefix on 54/54, prefixes 0/16/32/48 B, index block 16-aligned 54/54 |
| A9 | the record's `min` byte takes 0/1/2/3 | **BROKEN** — 101 distinct values (0–128); the four named values sum to 79 hulls of 54; the test wheel has 127 and 51 |
| A10 | the 0–48 B prefix before the face table is opaque | **HOLDS** (content), **refined**: its size is a deterministic function of plane-count mod 4, and `pad = prefix/4` on 54/54 |
| A11 | §7 step 3 (8 BmAK boxes → "box hulls in donor slots") uses only what the card proved | **BROKEN** — `hull_bytes()` rejects 8 vertices / 6 planes; a box is only writable as a degenerate 20-vertex/12-plane hull whose copied face table no longer describes faces, and that still scores 100 % |
| A12 | hull height (0.8225 m) is the tyre diameter; ×1.6596 makes a 1.365 m wheel | **HOLDS** with a caveat — the hull is a 10-gon prism: circumdiameter 1.365, **flat-to-flat 1.298**; the sim radius 0.68275 sits between them |
| A13 | 1.659566 comes from two measured files | **HOLDS** — 1.365/0.822514 = 1.659566; TYRES gives 1.3652–1.3657 |
| A14 | the stored compound box is the child union inset by the convex radius | **HOLDS** as "preserve each axis's own margin" (0.0100 m, the radius; the report's 0.011 is the check's allowance); 6,341/6,382 unions exact fleet-wide |
| A15 | the scale case is minimal (252 B / 69 runs, only ancestors touched) | **HOLDS** — 3 objects differ: hull 236 B, 0x474c0 6 B, 0x484f0 10 B |
| A16 | BmAK: 32 bodies, one box each, no chassis, identical across the four vehicles | **HOLDS** — 4/4 vehicle packages, identical layouts ignoring the package-local `index` |
| A17 | the assembled file is not a re-baked station table; `stations()` reads none | **HOLDS** — 2 B / 1 range @14,664; `stations()` returns [] for both files |
| A18 | the standing gate is unchanged/green, reader untouched | **HOLDS** — `check --all` reproduces the card exactly; `git diff` shows +870/−1 and `decode_polytope` changed only by `plane_slots` |
| A19 | test blobs stay outside the repo (R10), nothing written to `D:/Games` | **HOLDS** for the five blobs; **UNKNOWN** for `D:/Games` (not decidable from disk) |

**Bottom line for the card's consumer (T-22).** The writer can write a hull and the reader will
re-read it. It cannot yet be shown that the written file is *right*: the only gate is a set of
internal-consistency invariants, and the one field that is authored in two places (a dynamic
compound's AABB) is updated in one. Both shipped artefacts are internally inconsistent in that
field. Build steps that rely on "0 violations" as their check (PHYSICS_WRITE.md §7 step 3) do not
have a check.

---

## A1 · "The round trip proves the decoder is exact"

**Claim.** PHYSICS_WRITE.md §3: "A round trip with no arguments therefore tests the *decoder*,
not a file copy." MODLOG: "A file-level copy would have proved nothing; this proves the decoder is
exact."

**Why it matters.** It is the card's evidence that the reader's field semantics (vertex block,
plane equation, radius) — the things the writer scales — are right, not merely that their byte
offsets are right.

**Test.** Re-emit every hull with `hull_bytes(pf, off)` and compare to the source slice:

```
hulls re-emitted byte-identically: 54 of 54
donor sha256 1b90daefdc9660b4 size 340368
assembled sha256 6a0e7e13efb329a3 size 340368
```

**Result.** The claim is true for what it tests: the vertex block, the plane block (including the
unused sentinel slots) and `convex_radius` are located at the right offsets and copied back
exactly. It is *not* a test of semantics: `hull_bytes` copies the face table, the 0–48 B prefix,
the header u16s, the index block and the padding without decoding them, so a wrong reading of any
of those cannot show up. The plane *orientation* is pinned separately (see A5), and the mass
properties are explicitly undecoded (56 objects, 48 B each).

**Verdict.** **WEAK** as worded ("the decoder is exact"): the arithmetic subset is proven, the
semantic subset is not. HOLDS if read as "the three decoded blocks are re-emitted exactly".

---

## A2 · "The data section is fully partitioned … the file ending exactly at the last object"

**Claim.** Intended-change entry and writer comment: "430 objects, contiguous 0..`lf`, **0 gaps**,
every extent a multiple of 16, the file ending exactly at the last object." PHYSICS_WRITE.md §1:
"the data section … is fully partitioned by typed objects".

**Why it matters.** The whole size-changing write rests on it, and the card generalises from one
file to the fleet (§7 step 6 repacks any vehicle).

**Test.** Walk every `.physicsc` the standing gate walks (233 entities, 234 files) and check
consecutive extents, 16-alignment, and where the last object ends:

```
files 234 hulls 18865
gap files 0 []
align bad 0 []
last-object != lf 0 []
```

**Result.** HOLDS, and stronger than the card: 234/234 files, no gaps, every extent a multiple of
16, and the last object ends exactly at `lf` in every file. BROKEN only as *wording*: the last
object ends at `lf` = 322,288, but the data section continues to `ex` = 339,584 (local 2,720 B,
global 9,408 B, virtual 5,168 B = **17,296 B of fixup tables**). The file does not end at the last
object; the object partition does. PHYSICS_WRITE.md §2 states the correct layout in its table, so
the prose and the table disagree with each other. A writer that took the sentence literally would
truncate the tables.

**Verdict.** **HOLDS** (partition, fleet-wide); **BROKEN** (the sentence "the file ending exactly
at the last object").

---

## A3 · The 16 B remap stress "re-reads with a decoded graph identical object-for-object"

**Claim.** PHYSICS_WRITE.md §4: "Inserting 16 filler bytes at data offset 0 forces *every* offset
to move … gives a file that re-reads with **0 violations** and a decoded graph identical
object-for-object: 340,368 -> 340,384 B." §12: "re-reads with 0 violations."

**Why it matters.** This is the only case that exercises a size change of *every* offset, i.e. the
path a real hull replacement uses.

**Test.** Run `_case_shift(pf, 16)` and inspect object 0 and the graph signature:

```
first object 0x0 hkRootLevelContainer extent 96
graph sig len 430 430 changed indices [0]
sig0 in  ('hkRootLevelContainer', 96)
sig0 out ('hkRootLevelContainer', 112)
shift problems []
before 0000000000000000010000000100008000000000000000000000000000000000
after  7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f0000000000000000010000000100008000...
```

**Result.** `_case_shift` prepends `0x7f`×16 to the *contents* of object 0, so the root-level
container's struct fields move 16 bytes: `name` is now `0x7f7f7f7f`, `numVariants` is no longer at
+8, and the variants array is read from the old name bytes. Its decoded record changes
(`96 → 112`), so the graph is **not** identical object-for-object; `verify_written` only reports
no problems because the edited object is excluded from the "objects it was not given" test
(`set(changed) <= touched`). The other 429 signatures are identical, and the remap of all fixups
does work — the *mechanism* claim holds; the *artefact* claim does not. `shift16.physicsc` is not a
loadable `.physicsc`, and the card cites it as a passing case.

**Verdict.** **BROKEN** as claimed (identical graph / valid file). HOLDS for "the fixups of the
other 429 objects are remapped correctly".

---

## A4 · A grown child moves its ancestors' AABBs — the box is stored twice

**Claim.** MODLOG correction (b): "The writer instead moves an ancestor by exactly as much as its
children moved, preserving the file's own margin, and touches only ancestors (**2** of 22
compounds for the scaled wheel)." PHYSICS_WRITE.md §6: "a compound's AABB | derived from its
children".

**Why it matters.** It is the only value the writer *derives* rather than copies (§5), and the
card presents it as the complete fix for a grown or replaced child.

**Test 1 — is the box unique?** For every dynamic compound, compare the shape's `+0x80/+0x90`
box with the box at `+0x60/+0x70` of the object its `shape_data` pointer (`+0xc0`) points at:

```
('hknpStaticCompoundShape',  'hknpStaticCompoundShapeData')   compounds 2692  box mismatch 2692
('hknpDynamicCompoundShape', 'hknpDynamicCompoundShapeData')  compounds 3690  box mismatch 0
donor: data-box == shape-box 20 of 22; the 2 mismatches are the static compounds
```

So for every dynamic compound in the fleet (3,690/3,690, and 20/20 in the donor) the AABB is
stored **twice**, identically: once in the shape, once in its `…CompoundShapeData` at +0x60/+0x70.
The static compounds use a different data layout (all 2,692 differ), which is why the two classes
must be separated.

**Test 2 — is the written copy consistent?** Read the shipped `scale_wheel.physicsc`:

```
written compound @0x474c0 shape lo [-1.12486, -0.69242, -2.61336] hi [1.11822, 1.55644, 2.59619]
written Data     @0x4a4c0 +0x60 [-1.12486, -0.42118, -2.61336] +0x70 [1.11822, 1.55644, 2.59619]
written compound @0x484f0 shape lo [-1.10463, -0.69242, -2.61336] hi [1.10463, 1.32886, 0.65997]
written Data     @0x49940 +0x60 [-1.10463, -0.42118, -2.61336] +0x70 [1.10463, 1.32886, 0.402]
stale pairs in scale_wheel.physicsc: [('0x474c0','0x4a4c0',0.2712), ('0x484f0','0x49940',0.2712)]
stale pairs in the donor: []
```

The shape y-min moved to −0.69242; the Data copy is still −0.42118: **0.2712 m apart**. In
`replace_hull.physicsc` the one ancestor that grows leaves its Data copy **2.0857 m** stale:

```
stale shape-vs-data boxes in replace output: [('0x48920', '0x49d70', 2.0857)]
stale in donor: []
```

`shape_checks()` reads only `off+0x80`/`off+0x90` (jc3hkx.py lines 906–908), so it reports
`aabb_ok 22/22`, `union_ok 22/22`, **0 violations** on files whose two copies of the same box
disagree by up to 2 m.

**Result.** The ancestor fix is incomplete. Whether Havok reads the Data copy at runtime is not
testable here (phase Q, and the card itself does not claim runtime acceptance), but the file now
contains two different values for one box, and the check cannot see it. This is the same class of
error as correction (a) — the pointer slots — which was only caught because the round trip
compared bytes; here nothing compares bytes, so it ships.

**Verdict.** **BROKEN.**

---

## A5 · "Passes every invariant" certifies the hull

**Claim.** Card Done: "round-trip identical and the modified file passes every invariant → rows
T-P3/T-CO2/T-CO3 become buildable." PHYSICS_WRITE.md §1: "`shape_checks()` … reports **0
violations** on all four outputs". §7 step 3 uses "`convex`, `index_ok`, `aabb_ok`, `union_ok` all
100 %" as the proof that a box hull is right.

**Why it matters.** It is the card's exit criterion and the plan's per-step check. If the
invariants cannot distinguish a right hull from a wrong one, "buildable" is not supported.

**Test — construct wrong hulls and run the same checks.** All cases below were written through
`hull_bytes`/`packfile_bytes`, re-read with `shape_checks` and `verify_written`:

| constructed edit | 0-violation? | what the file now says |
|---|---|---|
| scale vertices ×1.659566, leave planes untouched, set `convex_radius = 1.0`, update ancestors | **yes** (convex 54/54, aabb 22/22) | planes are **0.258 m** off the vertices (gap 0.25798 with r = 0.01000 when the radius is left alone → 1 violation) |
| set `convex_radius = 0`, no other change | **yes** | the rounding radius that the writer scales is unconstrained |
| translate vertices *and* planes +4 cm, do **not** touch the ancestors | **yes** | a collider displaced 4 cm passes (the parent box has that much slack + the 1 % tolerance) |
| uniform scale ×1.05 (vertices, planes, radius, ancestors) | **yes** | a 5 %-wrong hull size passes |
| replace the 704 B wheel hull with the 1,776 B **body** hull (2.085 × 1.212 × 3.679 m) in part 26 | **yes** (convex 54/54, aabb 22/22, union 22/22) | the front-left wheel now carries a whole-car collider; the compound AABB grows to the car |
| scale vertices ×0.98, planes untouched | **yes** (gap 0.008) | a 2 % shape error is inside the radius tolerance; ×0.97 fails (gap 0.01173) |

The written `replace_hull.physicsc` on disk:

```
instance in compound 0x48920 part 26 translation [0.0, 0.0, 0.0, 0.5]
replaced hull: v36 p47 box [2.085, 1.212, 3.6788] convex_ok True
replace_hull size 341440 viol 0 convex 54 aabb 22 union 22 polytopes 54 compounds 22
```

**Result.** The invariants are internal-consistency tests: planes must support the vertex set
(within the shape's own radius), indices must be in range, a child box must sit inside its parent
(within 1 % of the parent span + 1 mm), the parent must cover the child union (within the child's
radius). None of them compares the hull to a mesh, a station table, a mass, a part, or a
neighbour. They are necessary, not sufficient. The card's own truth is the literal sentence
"0 violations" — what fails is the inference from it to "buildable".

**Verdict.** **BROKEN** (as a sufficiency claim); the literal "0 violations" statements in
PHYSICS_WRITE.md are true.

---

## A6 · The tolerance constants are measured

**Claim.** Implicit: `shape_checks`'s `1e-2 * max span + 1e-3` (AABB) and `convex_radius + 1e-3`
(convex/union) are the reader's rules, so passing them means the value is right.

**Why it matters.** R4: no value without provenance. These are the thresholds that decide pass or
fail for every hull in the fleet, and they were chosen, not decoded.

**Test.** Bisect the effects: a 2 % vertex-only shrink passes (gap 0.008), 3 % fails
(0.01173 > r + 1e-3 = 0.011); a 4 cm rigid displacement passes with the ancestors untouched; a
5 % uniform scale passes with ancestors moved. The AABB tolerance for this hull's parent is
1 % × 3.0154 + 0.001 ≈ 0.031 m, plus the box's own slack (stored box is 0.011 m outside the union
per axis), which is why 4 cm still fits.

**Verdict.** **WEAK** — the constants are plausible but unprovenanced (R4), and they are wide
enough to hide centimetre-scale placement errors and percent-scale size errors.

---

## A7 · "Pointer slots must stay 0 because the loader fills them"

**Claim.** MODLOG correction (a): "all 339 local and 765 global slots read **0** in the donor and
the loader fills them from the fixup table. Writing them produced a file that passed every reader
check while differing from the original in **2,702 bytes**".

**Test.** Count the value at every fixup `from` slot in all 234 files:

```
fixup from-slots: nonzero files 0 nonzero slots 0 of 316471
```

**Result.** The convention is measured and much stronger than the card's one-file sample:
316,471/316,471 slots are zero across the fleet. The explanation ("the loader fills them") is an
inference — the reader builds `pf.pointers` from the fixup tables and never reads a slot, so the
2,702-byte test only proves the reader ignores slots. Keeping them zero is safe because it copies
the donor's convention; it is not proof of how the loader works.

**Verdict.** **HOLDS** (convention), **WEAK** (mechanism).

---

## A8 · The face table is one 4-byte record per plane, found (not assumed)

**Claim.** PHYSICS_WRITE.md §6/§9: the table is found by scanning a 16-byte-aligned prefix; the
record is `u16 first | u8 count | u8 min`; `first`/`count` partition the index list on **54/54**
hulls; the table is padded with `0x7F` to a 16-byte boundary before the index block.

**Test.** Enumerate every prefix 0..48 that satisfies the chain for each of the 54 hulls, and check
uniqueness and alignment:

```
hulls 54 multi-candidate 0 no candidate 0
prefix histogram {0: 17, 16: 16, 32: 9, 48: 12} prefix not multiple of 16: 0
hulls whose index block starts 16-aligned: 54 of 54
face-table pad histogram {0: 17, 4: 16, 8: 9, 12: 12}
explained 54 of 54
```

On the test wheel: `firsts [0,10,20,24,…,56]`, `counts [10,10,4,4,…,4]`, sum 60 = index_count;
i.e. two 10-gons (the prism caps) and ten quads (the sides), exactly the 10-gon prism of A12.

**Verdict.** **HOLDS** — unique on 54/54, the prefix is always a multiple of 16, and the index
block is 16-aligned in every hull.

---

## A9 · "The record's `min` byte takes 0/1/2/3"

**Claim.** PHYSICS_WRITE.md §9.2: "`min` takes 1 (31 hulls), 0 (17 hulls), 3 (16 hulls), 2 (15
hulls) with no reading yet." §7 step 1 repeats it.

**Test.** Read the census the card itself generates (`PHYSICS_WRITE.json` → `face_table.min_bytes`)
and the wheel's 12 records:

```
distinct min-byte values in JSON: 101
values: [0, 1, 2, …, 126, 127, 128]
counts for the four named values: {'0': 17, '1': 31, '2': 15, '3': 16}  sum 79
wheel records: firsts [0,10,20,24,…] counts [10,10,4,…] mins [127,127,51,51,…,51]
```

**Result.** The byte takes **101 distinct values from 0 to 128**, not four. The four values the
report names are the four most common *per-hull membership* entries (`_face_census` counts each
distinct value once per hull, so the counts do not partition 54 and sum to 79). On the test wheel
the two cap faces carry 127 and the ten side faces carry 51 — probably face-size-dependent, but
that is a new hypothesis, not a reading. The operational conclusion ("no reading → preserve") is
still right; the number quoted to the next agent is wrong.

**Verdict.** **BROKEN** (the value set / counts as stated). The unknown itself is real.

---

## A10 · The unnamed prefix before the face table

**Claim.** "0–32 bytes of an unnamed block … 17 of 54 hulls have a zero-length prefix"; correction:
"0 B on 17, 16 B on 16, 32 B on 9, 48 B on 12"; "that prefix stays **UNKNOWN** and the writer
therefore preserves it byte-for-byte."

**Test.** Read the 37 non-empty prefixes and correlate their length with hull geometry:

```
prefix 16 @0x5250: 80dddf50 00000000 081e0dec fe070000
prefix 16 @0x6010: ffffffff ffffffff 12000000 00000000
prefix 16 @0x6400: 705eef50 00000000 eaea843b 00000000
prefix 48 @0x72d0: b00f0d51 00000000 d0babc3a 6210803f e04bef50 00000000 68d0af3a 00000000 …
prefix content classes: {'mixed': 37}   (none all-zero, none all-0xFF)
prefix/16 -> plane_count mod 4: {0: {0: 17}, 1: {3: 16}, 2: {2: 9}, 3: {1: 12}}
all pad == prefix/4: True
```

**Result.** The content is structured 16-byte records (not slack: no all-zero/all-0xFF block), so
"no reading" is honest. What the card misses is that the *size* is fully determined: prefix =
16·k with p ≡ 3k (mod 4), and the padding after the table is exactly prefix/4 — together the
0x20·k + 4p bytes that keep the index block 16-aligned. A new hull's prefix **size** is therefore
computable today; only its content is unknown. That shrinks §7 step 1 a little.

**Verdict.** **HOLDS** (content UNKNOWN, preserved); **refined** (size rule now measured).

---

## A11 · §7 step 3: "8 BmAK boxes → box hulls in donor slots" uses only what the card proved

**Claim.** PHYSICS_WRITE.md §7: "Steps 2 and 3 use only what this card proved"; step 3: "each box
becomes a box hull in the donor *slot* of the part it replaces, so the count stays 54 | `convex`,
`index_ok`, `aabb_ok`, `union_ok` all 100 %". §6: "a *brand-new* hull" may **not** be written
(face table prefix/min unknown).

**Test 1.** Try to author a box in the wheel slot:

```
hull_bytes with 8 verts: ValueError @0xb5d0: 8 vertices for a 20-vertex hull
hull_bytes with 6 planes: ValueError @0xb5d0: 6 planes for a 12-slot hull
```

`hull_bytes` copies the source object and only overwrites the vertex/plane blocks and radius; the
header's `vcount` (+0x30), plane/index counts (+0x44/+0x48), face table, index block and prefix are
not writable. There is no box builder anywhere in the writer.

**Test 2.** The only way to get a box through the current writer is to keep the 20/12 topology and
put the 20 vertices on the 8 corners with the 6 planes duplicated:

```
20-vertex box: viol 0 convex 54/54 index_ok 54 aabb 22 union 22 gap 0.0
box [0.2558, 0.7825, 0.7422] distinct positions 8 of 20
face table of the box slot: {'prefix': 0, 'records': 12, 'pad': 0, 'mins': [51, 127]}
firsts [0,10,20,24,…] counts [10,10,4,…] minbytes [127,127,51,…]
```

The solid is a box; the copied face table still claims 12 faces of 10 and 4 indices over 8 distinct
positions (12 duplicated vertices, 6 duplicated planes) and no check notices, because the face
table is never validated. So "all four invariants 100 %" cannot distinguish this from a correctly
authored box.

**Verdict.** **BROKEN** for the sentence "steps 2 and 3 use only what this card proved". A box
hull is not writable as a box; it is writable as a degenerate polytope whose non-plane blocks are
wrong, and the proposed check cannot tell.

---

## A12 · Hull height = tyre diameter (the 1.365 m target)

**Claim.** "Batmobile tyre Ø 1.365 m (`TYRES.md`) / 0.8225 m = **1.6596**"; after scaling the box
is "0.4909 × 1.365 × 1.2982 m".

**Why it matters.** It fixes what the collider's "diameter" means. A convex hull that approximates
a cylinder is not a circle; choosing the wrong dimension is a systematic 5 % error.

**Test.** Decode the wheel hull's geometry:

```
2 rings of 10 vertices, x = ±0.147901/0.147880, radii 0.41125–0.41126
R 0.411257  2R 0.822514  width 0.295781
box 0.8225 × 0.7822, ratio 0.7822/0.8225 = 0.951003 = cos 18°
after ×1.659566: box 1.365 × 1.2982
```

So the hull is a 10-sided prism: circumdiameter 0.8225, **flat-to-flat 0.7822**. Scaling by the
circumdiameter ratio makes the circumdiameter 1.365 (matching TYRES' tread Ø 1.3652–1.3657,
0.02–0.05 % low) and the flat-to-flat 1.298.

**Result.** The convention is coherent with the target: the mesh tyre is 1.365 and the hull's
vertices would lie on it. The caveat the card does not state: the *collider* is 5 % smaller
flat-to-flat, so its effective contact radius is 0.649–0.6825 while the sim's `land_global` radius
is 0.68275 (TYRES §"1.366 … 2 × the physics radius"). The donor's own declared radius (0.38)
against its hull (R 0.4113, flat 0.3911) shows the donor does **not** use "hull height = 2 ×
declared radius"; the card's rule is a *hull-to-mesh* rule, not the donor's sim rule. Whether the
3.4 cm flat gap matters is a runtime question (phase Q).

**Verdict.** **HOLDS** as "hull circumdiameter = tyre diameter"; **WEAK** if read as "the collider
is a 1.365 m circle" (it is a 10-gon with 1.298 m flats).

---

## A13 · The factor 1.659566

**Test.** `1.365 / 0.8225141434664279 = 1.6595459…`; the code computes
`round(1.365 / wheel_d, 6)` with the decoded height, giving 1.659566. TYRES.md gives tread
1.3652–1.3657 (four tyres, 0.5 mm spread); using 1.3652 gives 1.65982 (+0.015 %), using 1.366
gives 1.66076 (+0.07 %). Scaled radii in the written blob: 1.659566 ± 9.1e-8 over the 56
components that can be ratioed (4 components sit within 0.05 m of the centre and cannot be).

**Verdict.** **HOLDS** (rounding only). Minor: the md's "exactly one ratio across all **60** vertex
axes" is 56 testable axes, not 60.

---

## A14 · The stored box is the child union inset by the convex radius

**Claim.** PHYSICS_WRITE.md §5: "the stored box is the children's union inset by the convex radius
(the root sits 0.011 m inside its union on every axis)"; the writer preserves that margin.

**Test.** Compare stored vs computed union for the two ancestors:

```
@0x474c0 leaf union [-1.1249, -0.4112, -2.6134] [1.1182, 1.5564, 2.5962]
         stored    [-1.1249, -0.4212, -2.6134] [1.1182, 1.5564, 2.5962]
         inset (stored - union): [0.0, -0.0100, -0.0] on min, [0.0, 0.0, 0.0] on max
@0x484f0 leaf union [-1.1046, -0.4112, -2.6134] [1.1046, 1.3289, 0.3920]
         stored    [-1.1046, -0.4212, -2.6134] [1.1046, 1.3289, 0.4020]
         inset (stored - union): [0.0, -0.0100, -0.0] on min, [0.0, 0.0, -0.0100] on max
```

Fleet (`check --all`): **6,341 of 6,382** compounds have "AABB unions exact", i.e. 41 do not.

**Result.** The per-axis delta the writer applies preserves whatever margin each axis already had,
so the *mechanism* is right even where the margin is not exactly the radius. Correction to the
card's sentence: the inset measured here is **0.0100 m**, the convex radius itself, on the axes
where a wheel hull defines the extreme (0 on the others); the **0.011** the report quotes is the
check's *allowance*, `max(radius) + 1e-3`, not the authored inset. The root and the child both
show 0.0100, so "inset by the convex radius" is accurate for this file (just not to the third
decimal the report gives).

**Verdict.** **HOLDS** (the writer preserves the file's own margin, and the inset is the radius on
the axes measured); **BROKEN** for the claim's "0.011 m on every axis" — it is 0.0100 m, only on
the axes where a wheel hull sets the extreme, and 0.011 is the check's allowance.

---

## A15 · The scale case is minimal: 252 B / 69 runs, only ancestors touched

**Test.** Diff the shipped blob against the donor:

```
ranges 69 bytes 252 size 340368 340368
objects whose bytes differ: 3
  ('0xb5d0', 'hknpConvexPolytopeShape', 236)
  ('0x474c0', 'hknpDynamicCompoundShape', 6)
  ('0x484f0', 'hknpDynamicCompoundShape', 10)
indices identical True face_bytes 48 48
```

**Result.** Exactly 3 of 430 objects change (hull, parent, root); the other 20 compounds and all
other shapes are byte-identical; vertices, plane distances and radius all scale by one factor
(1.659566). Matches the card's "252 B over 69 runs" and "2 compounds".

**Verdict.** **HOLDS.**

---

## A16 · BmAK: 32 bodies, one box each, no chassis, all four vehicles identical

**Claim.** PHYSICS_WRITE.md §7: "32 bodies, each a single box … 8 wheels/suspension, 1 turret, 1
cockpit, 2 doors, 1 jet fin — and no chassis body at all".

**Test.** `Research/BatmobileGrab/PHYSICS.md` line 5: "4 vehicles, 32 bodies each, 128 records
total"; line 73: "Every body is a **single axis-aligned-ish box** … box count 1, sphere count 0";
line 75: "**There is no chassis body.**" `PHYSICS.json`: four packages, 32 bodies each; the bodies
differ only in the package-local `index` (e.g. 5,156 vs 3,088) — with `index` removed, all four
lists are identical (`True`). The four are the four `RVehicleBatmobile` packages (`README.md`:
15 packages total, 4 vehicles, 4 sims, 16 wheels), so this is 4/4 of the vehicle set, not a
sample.

**Verdict.** **HOLDS**; the phrase "byte-identical collision layouts" is true of the layout
(bones/extents/centres) but not of the record (`index` differs). The box rows also match the
plan's counts: rows 1–8 wheels/suspension, 10 turret, 11 cockpit, 12–13 doors, 24 fin, 18 debris
+ root.

---

## A17 · The assembled file and the station table

**Claim.** MODLOG correction (c): `sportsmuscle_true.physicsc` is not a re-baked station table; it
differs in one `f32`; `stations()` reads **no** station set from either file.

**Test.** Byte diff and `stations()`:

```
assembled: 340,368 B, 2 bytes over 1 range (@14,664+2)
f32: -2.569999933242798 -> -2.5699000358581543  (hknpPhysicsSystemData +0x3598)
stations donor []   stations shifted []
```

**Verdict.** **HOLDS.** (The consequence the card draws — "same station table" means "copy the
bytes" — is correct for this writer.)

---

## A18 · The standing gate is green and the reader was not changed

**Claim.** §12: "standing gate `check --all` green 233/234 entities 18,865 hulls"; MODLOG:
"unchanged by the writer".

**Test.** Re-run, and diff the tracked reader against `HEAD`:

```
entities 233 | files 234 | objects 130513 | hulls 18865 (convex 18865) | mesh shapes 4791 |
geometries 9582 | compounds 6382 (35499 instances, 25769 with a part index, 6341 AABB unions exact) |
station sets 17 (land_global agree 17, disagree 0)
check ok
```

`git diff --stat Tools/scripts/jc3hkx.py` → `870 insertions(+), 1 deletion(-)`; the only change
inside `decode_polytope` is the new `plane_slots` list plus its key. No existing key or check was
changed, so the census is comparable to the pre-writer state.

**Verdict.** **HOLDS.** Note what it does *not* prove: it is the reader checking the shipped game
files, not the writer checking its output.

---

## A19 · Artefacts outside the repo (R10) and "nothing written to D:/Games"

**Test.** The five blobs named in `PHYSICS_WRITE.json` exist where the card says, with the listed
sizes and hashes:

```
roundtrip_donor      340368  1b90daefdc9660b4
roundtrip_assembled  340368  6a0e7e13efb329a3
shift16              340384  8a3631986246a49d
scale_wheel          340368  d26910da6992b0f7
replace_hull         341440  dec81b8e8f467425
```

No `*.physicsc` was added to the repo by this card (the 156 present are pre-existing `Builds/`,
`Research/`, `Working/` files; `Builds/` is not tracked). The donor itself is
`Builds/test-091/…`, i.e. inside the repo — that is the project's sanctioned build staging area
(R6), not a new R10 breach.

`D:/Games` writes cannot be decided from the filesystem snapshot; the card says none, and the
donor path's mtime (Oct 28) is the only evidence visible. Treated as **UNKNOWN**, not as a pass.

**Verdict.** **HOLDS** for the five artefacts; **UNKNOWN** for the game directory.

---

## Cross-cutting: what the card still does not know, and one process lesson

* **Mass properties are untouched and undecoded** (56 × 48 B). A wheel hull scaled ×1.66 keeps the
  donor's `hknpShapeMassProperties`; the card lists this as UNKNOWN (§9.4), which is honest, but
  it means "the hull can be replaced" is only true of the geometry.
* **The extern mesh** (body panel) and the 80/64-byte body entries are untouched; the card says so.
* **The process lesson from correction (a) repeats in A4:** the checks passed a file that differed
  from the donor in 2,702 B, and only the byte-level round trip caught it. The stale
  `…CompoundShapeData` box is invisible to every check and exists in both shipped artefacts. A
  writer that derives a value stored in two places needs a *byte-level* invariant ("the two copies
  must be equal"), not only a geometric one.

## How to reproduce

```
python Tools/scripts/jc3hkx.py write --check     # PASS (exit 0), as quoted in the card
python Tools/scripts/jc3hkx.py check --all       # the standing gate, as quoted above
```

The remaining measurements are one-liners against the same module (`K.Packfile`,
`decode_polytope`, `shape_checks`, `packfile_bytes`, `compound_aabb_edits`, `face_table`) plus
direct `struct` reads of the five blobs in `E:/Modding/_JC3grab/hkx/write/`; the exact calls and
outputs are quoted in each section. Nothing was written outside this report.

**Revert this report:** delete `Research/challenge/card-G2-30.md`. Nothing else was changed.
