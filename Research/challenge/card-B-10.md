# Assumption challenge — backlog card B-10 (collision hull set)

**VERDICT: 3 HOLDS · 4 WEAK · 1 BROKEN.** The mechanics of the card hold: the write is
deterministic, re-derivable, tamper-detected, and the hulls it builds are valid convex polytopes.
What does **not** hold at full strength is the card's *proof* and two of its *values*:

* **BROKEN — A8, the convex radius rule.** B-10 writes `radius = 0.01 × min(k)`. The shipped file
  contradicts the premise: **45 hulls of extremely different sizes all carry exactly `0.01`**
  (max extents 0.139 m … 3.679 m). The radius is not proportional to hull size in JC3's own data, so
  scaling it is an invented value (R4) — small in effect (0.0168 m), but not "decoded".
* **WEAK — A1/A2, Done check 2 is tautological in the frame it is evaluated in.** The body hull is
  built by a map *derived from* the bbox, so `max|dev| 0.0000 m` cannot come out any other way; and
  read in the file's own frame ("hull union bbox" of every hull the file holds) the same hull set is
  `3.495 × 3.045 × 7.025 m`, i.e. **0.774 m over the 5 cm band**, 15× the tolerance.
* **WEAK — A4, the skipped door hulls are not actually inert.** The built file still wires **8
  compound instances to part indices 1 and 2**, exactly the `door_f_l`/`door_f_r` indices B-04 frees.
  The card's own reasoning ("scaling it would bind collision to a part that will not exist") applies
  to keeping the instances as much as to rescaling the hulls.

Everything below is read-only: no game launch, no write to `D:/Games`/`E:/Games`, no commit. The
only output of this pass is this file.

Sources challenged: `GRAB_BACKLOG.md` §8 `#### B-10`, §12 `| B-10 | done | … |`,
`MODLOG.md` §"B-10 start", §"B-10 · Collision hull set — independent verification",
§"B-10 — done"; artefacts `Working/Collision/{batmobile.physicsc,bm_collision.json,BM_COLLISION.md}`;
generators `Tools/scripts/bm_collision.py`, `Tools/scripts/jc3hkx.py`.

---

## A1 — "the body hull is re-scaled to DIM-1's bbox, so the Done check measures the body's size"

**Silent assumption.** That the hull's own AABB → DIM-1 map is a *measurement of the car*, and that
the resulting `max|dev| 0.0000 m` is evidence the collision fits the body.

**Test.** Read the map (`Tools/scripts/bm_collision.py`, `body_map`):

```
    if k is None:
        k = [(hi[j] - lo[j]) / (src_hi[j] - src_lo[j]) for j in range(3)]
    s = [lo[j] - k[j] * src_lo[j] for j in range(3)]
```

`k` is *defined* by the target box and `s` shifts the hull so its minimum lands exactly on `lo`.
`bm_collision.py` then evaluates `deviation(body_union, bbox_lo, bbox_hi)` on `after_body["bounds"]`
— the AABB of the vertices it just wrote. The number is an arithmetic identity: with `float32`
rounding it is 0.0000 by construction, for any donor hull and any bbox.

**Verdict: WEAK.** The check as written cannot fail; it proves "the writer put the hull where the
writer was told", not "the collision matches the car". A discriminating test would compare the hull
against something the writer does not consume — e.g. the assembled mesh's own body bbox read
independently, or the hull's volume/support against the mesh (the `V-02` silhouette-style gate).

## A2 — "hull union bbox within 5 cm of the body bbox" (the card's own Done wording)

**Silent assumption.** That "hull union bbox" means *the hulls bound to the body part*, not the hulls
the file holds.

**Test.** `Working/Collision/BM_COLLISION.md` §3, verbatim:

```
| frame | before (m) | after (m) |
|---|---|---|
| `stored` | 2.100 x 1.979 x 5.115 | 3.495 x 3.045 x 7.025 |
| `placed` | 2.100 x 1.867 x 5.141 | 3.495 x 3.045 x 7.025 |
```

The file's stored envelope after the write is **3.495 × 3.045 × 7.025 m** against a body bbox of
**3.495 × 2.271 × 7.025 m** → **+0.774 m in Y**, i.e. 3,870 % of the 5 cm band. The MODLOG
verification section says so itself ("the extra 0.774 m in Y is the four wheel hulls … reported,
never asserted").

**Verdict: WEAK.** The card's words do not name a frame, and the frame that makes the check pass is
the one where a single hull was built to be that box (A1). Read literally — "the hulls' union" — the
card's own Done criterion **fails**. The honest statement is: "the body hull's AABB equals the body
bbox by construction; the whole-file envelope exceeds it by 0.774 m and its frame is B-04's".

## A3 — T-22's `k = 1.660052` rests on "the donor wheel hull's Ø 0.8225 m *is* its tyre"

**Silent assumption.** The donor's wheel hull diameter equals the donor's tyre diameter, so
`k = our_tyre / donor_hull` is a tyre-preserving scale.

**Test 1 — the hull's shape.** Donor wheel hull `box_before_m` = `0.2958 × 0.8225 × 0.7822`
(`bm_collision.json`). Rolling-plane ratio `0.7822 / 0.8225 = 0.9509`. An inscribed regular prism's
flat-to-vertex ratio is `cos(π/n)`; for `n = 10`, `cos(18°) = 0.9511`. The hull is therefore a
**10-sided inscribed prism of a Ø 0.8225 m circle**, i.e. the vertex circle — exactly what a tyre OD
would be. (A 12-gon would give 0.9659; the hull carries 12 planes because two are the side faces.)

**Test 2 — the delivered size against the measured station.**

```
| `sportsmuscle_wheel_f_l` | `f_l` | [-1.208, 0.7047, -2.57] | 1.3658 | 1.660052 |
```
`2 × 0.6827 = 1.3654` (T-22's tyre) and the written hull's Y extent is **1.365** m — the hull matches
the measured station radius, not a typed number.

**Verdict: HOLDS** (with the premise stated as a premise): both tests support "donor hull = donor
tyre OD" from geometry and from the station cross-check. The residual is that the donor's own tyre was
never measured directly, so "the donor hull is its tyre" stays an inference — strong, not decoded.

## A4 — "the two door slots are copied byte-identical because B-04 removes the door parts"

**Silent assumption.** That an unscaled, unmodified door hull bound to a removed part is inert.

**Test.** Enumerate the part indices the built file's compound instances reference
(`jc3hkx.decode_compound` over `Working/Collision/batmobile.physicsc`):

```
part indices referenced by compound instances: [(0, 2), (1, 4), (2, 4), (3, 4), (4, 2), (5, 2), …
(41, 2)]
```

Part indices **1 and 2** — the `door_f_l`/`door_f_r` slots B-04 frees (`Working/Parts/bm_vehicle_parts.json`
`index_map`, `removals`) — are each referenced **4 times**. Indices 42…60, B-04's 19 new parts, are
referenced **0 times** (expected: T-22 gives the new parts no hull), but 1/2 are not vacated at all.

**Verdict: WEAK, and the card's own argument cuts against it.** B-10's stated reason for not
rescaling is "scaling it would bind collision to a part that will not exist (R4)". That reasoning is
about the **binding**, which is untouched: the file still declares 8 instances bound to indices that
B-04 no longer defines. Either the binding does nothing (in which case the hull could have been
scaled at no cost, and the R4 argument is rhetorical) or it binds (in which case the card ships two
unscaled donor hulls on two nonexistent parts). Neither branch was tested, and **no B-10 check lists
compound instances whose `part_index` is missing from the built parts module** — a one-line check that
would settle it. This is the most concrete gap found.

## A5 — "stations unchanged (R3)" is satisfied by the `.physicsc` alone

**Silent assumption.** That asserting `hknpPhysicsSystemData` byte-identical and "0 → 0 station sets"
covers R3 *for this file's change*.

**Test.** `bm_collision.json` `stations`:

```
{"in_file_before": 0, "in_file_after": 0, "physics_system_data_identical": true,
 "parts_module_sha256": "7335dfe71e95de1c", "note": "R3: no station row, no
 `base_wheel_hardpoint_positions`, no parts module and no `land_global` value is written or moved; …"}
```

So the file has **no station data at all**; the wheel stations live elsewhere (`Working/TrueScale/
stations.json`, `land_global`). The one in-file object that could carry placement or per-hull body
data — `hknpPhysicsSystemData`, 20,912 B — is asserted identical, but G2-30 recorded its layout as
**UNKNOWN 4**. "Identical" is therefore asserted, "still consistent with hulls that grew 1.87×/1.91×
in Y/Z" is not proven.

**Verdict: WEAK.** The wheel half is consistent (hull radius = station radius, hubs untouched, box
centre = pivot). The body half rests on an undecoded object. The honest form is: "no station datum is
in this file; the body hull changed and R3 is satisfied only if nothing in that 20,912 B block is
position-dependent — UNKNOWN pending a decode (Q-1 cannot see it either)".

## A6 — the fleet-wide claim "`jc3hkx.py check --all` green (233/234 entities)"

**Silent assumption.** That the gate covers the fleet rather than a sample.

**Test.** `grep -n "233\|234" Tools/scripts/jc3hkx.py`:

```
1036:        "from the archives instead: 33 of the 233 bundles keep their 400-680 KB physics",
```

233 **entities**, 234 **files** — the extra file is a second `.physicsc` on one entity (the cargo
plane carries two caches), not an excluded entity. The census reads all indexed bundles; for 33 of
them the physics is taken from an archive copy rather than the loose override.

**Verdict: HOLDS.** Not a sample; the 233/234 is files-vs-entities, and the 33 archive-read bundles
are still counted. (The caveat worth keeping: the gate re-reads shipped data, so it cannot vouch for
the *modded* entity — that is what `--file/--against` adds, and B-10 does use it.)

## A7 — the donor `.physicsc` is the shipped file

**Silent assumption.** `Builds/test-091/aaf/models/…/sportsmuscle.physicsc` is the game's own file,
so every "before" box is the shipped box.

**Test.** The provenance is a **build tree**, and no artefact compares it to the archive:

```
$ sha256sum Builds/test-091/aaf/…/sportsmuscle.physicsc
1b90daefdc9660b44649c32aca758f6beb1395b424d1269d50415bbc6a8f321d
$ grep -o "sportsmuscle[^\"]*physicsc" Research/JC3Grab/INDEX.jsonl   # (no output)
```

`Research/JC3Grab/PHYSICS_WRITE.json` `sources.donor` is the same build path (340,368 B / 430
objects), and `Research/JC3Grab/INDEX.jsonl` (81,952 rows) contains no row that names this member, so
the repo holds **no archive-side hash** for it. test-091 is the live CAM-1 build; its aaf tree was
assembled from earlier builds, and nothing in the B-10 record proves this member was never touched by
them.

**Verdict: WEAK / provenance UNKNOWN.** Low risk (the file's decoded class census matches G2-30's
shipped-file census exactly: 430 objects, 54 `hknpConvexPolytopeShape`, 22 compounds), but the card
calls its "before" box a decoded value; the decode is real, the *identity to the shipped bytes* is not
recorded anywhere. A one-command fix: extract the member from the archive via `jc3detail` and compare
`sha256`.

## A8 — the convex radius rule `0.01 × min(k)`

**Silent assumption.** That the donor's `0.01` radius is a *base* value that scales with the hull.

**Test.** Radii of every hull in the donor file, grouped, with each group's largest extent:

```
radius 0.002436: 1 hull(s), max extent range 0.482..0.482
radius 0.003382: 1 hull(s), max extent range 0.101..0.101
radius 0.003863: 1 hull(s), max extent range 0.074..0.074
radius 0.004475: 1 hull(s), max extent range 0.457..0.457
radius 0.004629: 1 hull(s), max extent range 0.41..0.41
radius 0.01:     45 hull(s), max extent range 0.139..3.679
```

A single radius `0.01` covers hulls from **0.139 m to 3.679 m** — a 26× size range with no
proportionality whatsoever. Nine other hulls carry small radii (0.0024…0.0046) that do not track their
extents either (0.074 m → 0.0039; 0.482 m → 0.0024). So the shipped convention is *not*
`radius ∝ hull size`.

B-10 writes `radius = d["convex_radius"] * min(k)` (`bm_collision.py`, `body_map`) → `0.016763` for
the body and `0.016601` for the wheels, and labels it `derived`.

**Verdict: BROKEN (as a provenance claim).** The value is a plausible safety margin, but it is not
derived from anything measured: the data it points at (45 hulls at 0.01) says the radius is
*independent* of size. `min(k)` is also unmotivated — with per-axis k of `1.676257 / 1.873759 /
1.909565`, choosing the smallest rather than any other statistic is a decision, not a measurement.
R4 calls this `assumed`, which is not buildable; the honest label is `class: assumed` with the reason
"hull inflation margin, no shipped proportionality measured", or keep the donor's `0.01` unchanged
(the value 45 shipped hulls carry, which is at least a decoded value).

---

## What would make the card fully "done" (all one command each)

1. Replace Done check 2 with a comparison against data the writer does not consume (mesh bbox or
   support function), or state it as "by construction" and drop the 5 cm framing.
2. Report the whole-file envelope against the same 5 cm band and accept/annotate the 0.774 m.
3. Add the missing-part-index check for compound instances (A4); decide the 8 door instances.
4. Keep the donor radius or label it `assumed` (A8).
5. Record the archive sha256 of the donor member (A7).
6. State A5's residual: the body half of R3 is UNKNOWN until `hknpPhysicsSystemData` is decoded.
