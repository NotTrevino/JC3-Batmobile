# Review — G3-01c · BmAK convex elements (`COLLISION_CONVEX.md` / `.json`)

Independent review. I did not write this card. Read-only: `BmGame.upk` through
`Tools/scripts/upk_read.py` (my own tag walk and element parser, not `grab_collision_convex.py`),
`BMSDK_OFFSETS.json`, `COLLISION_GEOM.md`, the card and its script. Only this report and the earlier
`review-G3-02c.md` were written. No game was launched or read; no git operations.

## VERDICT: **minor issues**

The geometry is right. I re-decoded both AggGeom payloads from the package with my own parser and every
published number reproduced: element starts, byte sizes, counts, boxes, trailer, the exact byte
accounting, both union boxes, and the three near-miss triangles to the digits given. The card's core
result — 43 + 13 convex hulls, six counted arrays + a seventh + box + 14-byte trailer, box == vertex
bounds on 56/56 — stands on my independent read.

What is wrong is evidence prose around it, and one item is material because it is the *only* justification
for the card's main remaining UNKNOWN:

1. **U-1's stated test is false on both clauses.** The seventh array's counts are 5–13 (not 6–13, and the
   card's own table shows the 5), and they *do* equal the triangle count in 6 of 43 battle and 9 of 13
   pursuit elements. The conclusion (semantics UNKNOWN) survives, but not for the reason written.
2. A passing check's detail calls **1416 indices "1416 triangles"**; the triangle count is 472.
3. "**accounts for every byte**" is unlabelled in scope: 17,390 B of export 169748 and 5,738 B of 169749
   are outside the AggGeom payload and are never described.
4. The explanation of **why G3-01b stopped** misstates that record (its cited stop byte is the box's
   first float, not a misread array).
5. Hypothesis-derived **field names** ("edge records", "permuted data") are presented as if read, while
   the same rows say the semantics are UNKNOWN.

No decoded geometric value needs rework.

## Check output

Command:

```
cd /e/Modding/JustCause3/JC3-Batmobile && uv run --with numpy python Tools/scripts/grab_collision_convex.py --check 2>&1 | tee /tmp/g301c_check.txt; echo "EXIT=${PIPESTATUS[0]}"
```

Output (verbatim):

```
OK: 56 elements ({'169748': 43, '169749': 13}), 34182 B accounted, plane-clean 53/56, box-exact 56/56; 11/11 checks; md byte-identical
EXIT=0
```

The check compares a fresh build to both files and re-runs every oracle, so it is stronger than a
byte-compare — but it is still the card's own code judging the card's own parse. The re-reads below are
the independent part.

## Spot-checks

| # | card value | card label | my source | match |
|---|---|---|---|---|
| 1 | AggGeom 25907 B / 8275 B, header `[0,0,0,43]` / `[0,0,0,13]` | decoded | export tag walk → `AggGeom` payload at export byte 49 | **yes** |
| 2 | el0 169748: start 16, 926 B, 10 v, 16 tris, 7 planes, 13 recs, box `[-305.27,-161.43,-0.00]..[92.46,-86.84,226.60]` | decoded | my element parse | **yes** |
| 3 | el3 near-miss: normal 1.5e-04, W 0.056 cm | decoded | recomputed plane distances | **yes** (0.000152 / 0.055503) |
| 4 | accounting 25898 of 25907 (footer 9 B, zero); 8266 of 8275 | decoded | sequential element walk | **yes** |
| 5 | union: battle min `[-338.4417,-245.9405,-0.75]` max `[356.9706,246.9817,293.7526]`; pursuit `[-331.3439,-159.1562,-0.0]..[339.6018,159.1562,224.0855]` | derived | component min/max of my decoded boxes | **yes** |

Also reproduced (not counted in the five): box == vertex bounds max difference **0.0** on all 56; trailer
`01000000`+10 zero bytes constant on all 56; the near misses on el24 (0.000278 / 0.094133) and el32
(0.000205 / 0.067002); the `nZ` ranges; the StaticMesh rows (175973: 25,324 B, 4 tags; 175974: 20,660 B,
4 tags); and `169748` total export size 43,346 B / `169749` 14,062 B.

Detail worth recording, because it is the strongest thing in the card: the box oracle is exact — the
stored 6 floats equal min/max of the element's own vertices to the last bit on 56 of 56 elements, at
24 bytes, immediately after the seventh array. That single invariant pins the seventh array as *counted*
(not padding) and pins the box boundary, which is what G3-01b lacked.

## Issues

**I-1 · `COLLISION_CONVEX.md`, UNKNOWN U-1 — the stated test is false, on both clauses.**
Value: "they vary per element (**6-13**) and do not equal the triangle or vertex count".
- Range: battle `nZ` is **5..13** (the card's own table lists `edge recs 5` for elements 7 and 12 and the
  derived line says "edge records [5, 6, 7, 8, 9, 10, 12, 13]").
- Equality: `nZ` **equals the triangle count in 6 of 43 battle elements and 9 of 13 pursuit elements**
  (e.g. pursuit element 0: 12 records, 12 triangles). `nZ == nV` never happens (0/56).
Why it matters: those two equalities were the card's argument that the array is "extra". They do not hold.
The conclusion is still right, but it needs a different argument — see U-1 under resolvable UNKNOWNs,
where the values themselves rule out an index reading.

**I-2 · `COLLISION_CONVEX.md`, Checks row "every triangle index is inside the element's own vertex array" — detail mislabels the unit.**
Value: "**1416 triangles checked**". 1,416 is the number of *indices*: 332 battle triangles + 140 pursuit
triangles = 472 triangles = 1,416 indices. The check itself is correct and passes; the count in its detail
is three times the triangle count.

**I-3 · `COLLISION_CONVEX.md`, opening line — "accounts for every byte" is unlabelled in scope.**
Value: "This record decodes **56 elements** (169748: 43, 169749: 13) and **accounts for every byte**."
The accounting is exact for the AggGeom payloads (25,907 and 8,275 B). The exports are larger: 43,346 B and
14,062 B. The tag walk ends at 25,956 / 8,324 B (a type-0 terminator), so **17,390 B and 5,738 B of the
exports are outside anything this record describes**, and the reader is not told. It should read "every
byte of the two AggGeom payloads", with the remainder named as out of scope.

**I-4 · `COLLISION_CONVEX.md`, "G3-01b's chain stopped because it read a seventh array (`Z`) where the box begins" — misattributes the earlier record.**
`COLLISION_GEOM.md:13` says the chain was "the seven-array chain (V,A,I,E,X,Y,Z)" and that it stopped at
"byte 644" for 169749. In this decode, 169749 element 0 starts at 16 and ends at 682, so its box occupies
**644 … 668**. G3-01b therefore read Z at its correct offset and then expected *another count* at the first
box float; it did not read Z "where the box begins". The new decode explains the stop — but the sentence as
written contradicts the record it cites, and it is exactly the kind of second-hand claim this project's rule
targets. (Also unlabelled: it is presented as fact with no reference.)

**I-5 · `COLLISION_CONVEX.md` layout table + `COLLISION_CONVEX.json` keys — hypothesis names presented as field names.**
Rows 2, 4, 5, 7 read "(permuted data)", "(edge vectors)", "(face vectors)", "(edge **records**)" and the JSON
keys are `n_permuted`, `n_edge_vectors`, `n_face_vectors`, `n_edge_records`, while the same rows say
"semantics UNKNOWN". Those names are exactly the parts of the `FKConvexElem` hypothesis the card says it did
*not* prove. A reader of the JSON alone sees `n_edge_records` and will treat it as decoded. Neutral keys
(`n_array7`, `n_array2`, …) or an explicit `_hypothesis` suffix would keep the UNKNOWN honest.
Related, smaller: "the 14 bytes … start with **int32 1**" is one reading of bytes that a 1-byte validity
flag + 13 zeros fits equally well. The rejection of "ElemBox incl. a valid byte" is *proven* — but by the
box oracle (box == vertex bounds at exactly 24 B), not by the trailer's width, and the record says it the
other way round.

**I-6 · `COLLISION_CONVEX.md`, StaticMesh evidence table — decoded content is hidden.**
The table shows only "tags 4 / names —". The four tags are decodable now and are:
`BoolProperty @412 = True`, `ObjectNCRProperty @284 → export 169748`, `IntProperty @236 = 1`,
`IntProperty @232 = 32`. The object reference is the **collision StaticMesh → its `RB_BodySetup`** link —
precisely the chain U-4 and G3-01d need, already in hand, rendered as a dash. (It does not give the Bounds;
it does show which hulls that mesh owns.)

**I-7 · `COLLISION_CONVEX.md`, Checks table — a tolerance is presented as a pass.**
The plane oracle passes when an element has **at most one** triangle off its planes *and* the miss is
parallel. That is a deliberate softening (a wrong layout would fail wholesale), but the research record's
Checks row states only "PASS"; the softening is disclosed in `tmp/freebuff/reports/G3-01c.md`
("Limitations"), which is not the record a later reader quotes. Similarly, the row "the StaticMesh bounds
are not claimed (they stay UNKNOWN)" tests a string in the verdict dict — it cannot fail — so counting it as
one of "11/11 checks" inflates the check count.

## Resolvable UNKNOWNs

**U-1 · "semantics of the seventh array" — the card's argument is refuted, and the bytes already narrow it a lot.**
I read the 4-byte records: 348 values over the battle body, 136 over the pursuit body, ranging
**256 … 591,107**, against triangle counts of 4–16 and vertex counts of 4–10. So the "one index per
triangle" reading is **refuted by value range**, not by count — a much stronger statement than the card's
count mismatch. The first element's values begin `772, 1537, 514, 1289, 256, 66054, 66816, 66563, 132102,
131845, 197895, 197637, 263427`; several are near multiples of 256 (256, 514, 772, 1289, 1537), which
*suggests* a fixed-point scale — **a hypothesis, not a decoded fact, and it must not be written as one**.
How to settle it: test the record as two u16 halves and against an independently known per-element
quantity; a third `RB_BodySetup` with different counts would discriminate. That work is G3-01c's own scope
and is not done here.

**U-2 · "semantics of the 14-byte trailer" — not resolvable from these two bodies.**
All 56 elements carry byte-identical trailers, so no field inside them varies and nothing in these files
separates "int32 valid flag" from "1 byte + 13 bytes". It needs an element whose validity differs (another
body in the install) or the serialiser's own definition.

**U-3 · "the 9 zero bytes at the payload end" — same limit.** Both payloads end in nine zeros; padding and
a zero-valued field are indistinguishable here. The card's "where it would be found" cell says
"array/aggregate padding, or a field; not proven", which is a restatement of the unknown, not a location —
the honest entry is "another AggGeom whose tail is non-zero, or the aggregate serialiser".

**U-4 · "the collision StaticMesh's bounds" — still UNKNOWN, and the card's reason is accurate; there is a partial route.**
I verified the blocker: `BMSDK_OFFSETS.json` has **no** `StaticMesh` / `UStaticMesh` / `SkeletalMesh` class;
its only `FBoxSphereBounds` `Bounds` is `PrimitiveComponent` offset 128, and the four tags on these exports
carry no Bounds. So the collision mesh's own box needs a cooked-mesh body decoder. However, a *render* mesh
extent already exists in the project (MODLOG line 20250: render mesh 7.03 × 3.50 × 2.27 m; G3-01d compares
against a decoded mesh AABB), so the union-versus-mesh comparison could be run today against the render
mesh — as a different oracle than the one U-4 names, and it should be labelled that way.

**U-5 · "why 3 of 56 elements have one triangle 0.6–0.9 mm off its stored plane" — not resolvable from the file.**
I reproduced all three exactly (0.055503 / 0.094133 / 0.067002 cm). The offsets are consistent with the
authoring tool quantising the plane constant after computing it from the vertices; that is a hypothesis
about a generator, not a file fact, and the card is right to leave it UNKNOWN.

## Bottom line

Keep every number in the element tables and both union boxes — they reproduce byte for byte. Fix the prose:
re-argue U-1 from the record values (the counts do not carry the argument, the values do), correct "1416
triangles" to "1416 indices / 472 triangles", scope "every byte" to the payloads and name the 17,390 /
5,738 B remainder, drop or correct the G3-01b attribution, rename the hypothesis-derived fields, and publish
the plane oracle's tolerance in the record rather than only in the task report.
