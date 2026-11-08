# Independent review — B-10 · Collision hull set

Reviewer: Buffy (did not write this card). Date: 2026-10-31. Read-only pass: nothing outside this
file was written. No game launched, nothing committed, no game/Research/Tools/Working file edited.

Card under review (`GRAB_BACKLOG.md` §8, lines 1070-1072):

```
#### B-10 · Collision (only if T-22 resolved)   M · deps: B-02, T-22 · serves: DIM-4
Do: write the Batmobile hull set with `jc3hkx.py`; stations unchanged (R3).
Done: `jc3hkx.py check --all` on the built file; hull union bbox within 5 cm of the body bbox.
```

Inputs read: `GRAB_BACKLOG.md` §0.5 (R1-R14), the B-10 card, the B-10 row in §12 (line 1336) and
the T-22 row; `MODLOG.md` §"B-10 start", §"B-10 · Collision hull set — independent verification"
and §"B-10 — done" (lines 16626-16856); `Working/Collision/{BM_COLLISION.md,bm_collision.json,
batmobile.physicsc}`; `Tools/scripts/bm_collision.py` (673 lines) and the writer half of
`Tools/scripts/jc3hkx.py`; the two dependencies `Working/Translation/t16_collision.json` (T-22) and
`Working/Appearance/build_parts/parts_manifest.json` (B-02), plus `Working/TrueScale/stations.json`
and both parts modules (`Builds/test-091/…`, `Builds/bm-002/…`).

---

## VERDICT: **minor issues**

The card's two Done clauses both reproduce on this tree, the delivered `.physicsc` is a valid,
same-size, 5-hull rewrite, and every number in the MD/JSON is generated and re-derived by
`--check`. Nothing in the delivered binary is falsified: the file is 340,368 B, 430 objects,
54 hulls, 8 objects differ from the donor (explained below), and the 5 written hulls decode to the
boxes the doc prints.

But the card's supporting evidence is weaker than its record says, and two reported numbers are
wrong:

* `BM_COLLISION.md:50` — the "placed" envelope is **not** the placement chain the same page
  describes; the generator drops the part-translation and prints the stored box twice.
* `MODLOG.md:16816` cites a parts-module sha256 (`3a5c…`) that matches no file.

plus a vacuous check presented as evidence (`bm_collision.py:388`), a `--against` diff that is
blind to the 3 compound edits it "proves" did not happen, a "5 objects changed" that is really 8,
an "22 AABB unions exact" that is 21 exact / 22 covered, a silent supersession of T-22's own `k`,
and two door hulls left wired to part indices that B-04 deleted (ownerless between the cards).
None of these changes the hull bytes; all of them change what the record is entitled to claim.
Fix the two wrong numbers and record the door/gap item, and the card stands.

---

## Check output (verbatim)

The card's `--check` command, re-run in `E:/Modding/JC3-Batmobile`:

```
$ python Tools/scripts/bm_collision.py --check
PASS: 5 hulls written, 3 ancestor compounds re-boxed, 430 objects, stations 0 -> 0 | body union vs body bbox max |dev| 0.0000 m <= 0.05 m: True | Working/Collision/batmobile.physicsc 340,368 B sha256 192c12479d81da6e... | json match True, md match True
EXIT=0
```

The card's Done command (first clause), re-run:

```
$ python Tools/scripts/jc3hkx.py check --all --file Working/Collision/batmobile.physicsc --against Builds/test-091/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc
file Working/Collision/batmobile.physicsc: 340,368 B, 430 objects, 54 hulls (convex 54), 18 mesh shapes, 22 compounds (112 instances, 22 AABB unions exact), station sets 0, sha256 192c12479d81da6e... | vs sportsmuscle.physicsc: 5 object(s) changed (hknpConvexPolytopeShape), hknpPhysicsSystemData identical True
entities 233 | files 234 | objects 130513 | hulls 18865 (convex 18865) | mesh shapes 4791 | geometries 9582 | compounds 6382 (35499 instances, 25769 with a part index, 6341 AABB unions exact) | station sets 17 (land_global agree 17, disagree 0)
check ok
EXIT=0
```

Both match the MODLOG block character for character. `--check` was **not** run as `--write` (this
pass is read-only); `--check` re-derives the whole document from its inputs and byte-compares the
three artefacts, so the reproduction above is the strongest available evidence that the delivered
files are the script's output.

### Output existence

The card has **no `Out:` line**, so "every Out path exists" is vacuous for the card itself; the
MODLOG says so and follows the B-02/B-03 staging convention. Every artefact named in the §12 row
exists and is non-empty:

| artefact | size | note |
|---|---|---|
| `Working/Collision/batmobile.physicsc` | 340,368 B | sha256 `192c12479d81da6e…`, same size as the donor |
| `Working/Collision/bm_collision.json` | 12,670 B | schema 1, 9 checks, all `ok: true` |
| `Working/Collision/BM_COLLISION.md` | 6,126 B | generated, `--check` says not stale |
| `Tools/scripts/bm_collision.py` | 673 lines | `--write` / `--check` |
| `jc3hkx.py check --all --file … --against …` | — | green, output above |

One reproducibility wrinkle: the §12 row states the command as
`jc3hkx.py check --all --file Working/Collision/batmobile.physicsc --against <donor>` with a
literal `<donor>` placeholder, so the row's own quote is not runnable as written (the MD §5 and the
MODLOG substitute the real path). Minor.

---

## Issues

### 1. `BM_COLLISION.md:50` + `:52` — the "placed" envelope is not the placement chain it claims (wrong number, false method statement)

`bm_collision.py:180` (`place()`) multiplies the point by the world matrix in the row-vector
direction (`Σ_r p[r]·m[r][c]`), while `part_world()` (`:159`) hands back the matrix in the
transposed, translation-last-column layout printed by this very script
(`world(f_l)` = `[[1,0,0,-0.885],[0,1,0,0.4],[0,0,1,-1.557],[0,0,0,1]]`). The result is that
**the part translation is dropped**; only rotations survive. Consequences, measured:

| | doc line 50 says | correctly placed (translation applied) |
|---|---|---|
| after | `3.495 x 3.045 x 7.025` | `3.495 x 2.6446 x 7.025`, min y `-0.2826` |
| before | `2.100 x 1.867 x 5.141` | `2.100 x 1.4673 x 5.141`, min y `-0.0112` |

After the write, `placed` equals `stored` exactly (`3.495 x 3.045 x 7.025`), which is the tell: the
wheel hulls are written at translation 0, so with translations ignored there is nothing left to
move. So the row adds no information and the sentence at `:52` ("`placed` = instance
basis/translation … then the part module's `parent_space_offset` chain") describes a computation
that does not happen. The number is printed, never asserted, so no gate is broken — but it is the
one place in the deliverable that would have shown *where the wheel hulls land*, and it is wrong.
Fix `place()` (or delete the row) before anyone uses it for the placement decision.

### 2. `bm_collision.py:361` / `:388` — the check "only the written hulls and their ancestor compounds changed" cannot fail

```python
compound_edits = changed_objs - len(changes)
...
"ok": changed_objs == len(changes) + compound_edits,
```

This is an identity (`x == y + (x − y)`), so it is `True` for any edit set, including one that
touches every object. It is nevertheless printed in `BM_COLLISION.md` §4 and quoted in the MODLOG
and §12 as evidence. The claim it advertises **is** true of this file (I measured it independently:
8 of 430 objects differ), but this check is not what establishes it — and a future regression that
edited unrelated objects would still print PASS here.

### 3. `BM_COLLISION.md` §4 / §12 / MODLOG — "5 object(s) changed" is really 8, and the `--against` diff cannot see the 3 compound edits

Independent object-by-object byte comparison of donor vs written file:

```
hknpConvexPolytopeShape  0x5250 1776 B      (body)
hknpConvexPolytopeShape  0xb5d0 / 0xb910 / 0xfb40 / 0xfe80  704 B each   (4 wheels)
hknpDynamicCompoundShape 0x474c0 2256 B
hknpDynamicCompoundShape 0x484f0 1360 B
hknpDynamicCompoundShape 0x4a920 2000 B
```

`jc3hkx.graph_signature()` records a compound's instance count, class, part index, translation and
`basis[0]`, but **not** its stored AABB — so `compound_aabb_edits()`'s writes are invisible to
`check_file()`'s diff, and the line reads "5 object(s) changed". `bm_collision.json` itself records
`write.edited_objects: 8`, so the record contradicts its own evidence line. Anyone reading §12's
"5 object(s) changed (hknpConvexPolytopeShape)" as "only the hulls moved" is being told the truth
by luck, not by measurement. (The compound boxes are covered by `shape_checks`' union test — see
issue 4 for how well.)

### 4. "22 AABB unions exact" is not what the counter measures, and one of the 22 is not exact

The phrase comes from `jc3hkx.py`'s print of `info["union_ok"]`, whose test is "the child union is
*covered* by the stored AABB within the children's convex radius"; `union_exact` is a separate,
stricter counter. Measured on the delivered file:

```
union_ok 22   union_exact 21   compounds 22   (0 violations)
```

So the delivered file has 22 covered unions and **21** exact ones. The word "exact" in
`BM_COLLISION.md` §4 ("22/22 AABB unions exact", via §12 and the MODLOG) is therefore wrong for
this file, even though nothing fails. `bm_collision`'s own detail string avoids the word
("22/22 unions") — the overstatement rides in on `jc3hkx`'s label.

### 5. The body hull silently supersedes T-22, and T-22's artefact was not updated (two done cards now disagree)

* B-10 delivers body hull `0x5250` = `3.495 x 2.271 x 7.025 m`, per-axis `k` `[1.676257, 1.873759, 1.909565]`.
* `Working/Translation/t16_collision.json` (T-22, `done`) still records `hull_set.body.scale_k`
  `1.676259` and `box_after_m` `[3.495, 2.0316, 6.1666]`, and the §12 T-22 row still quotes
  "body hull 3.495x2.032x6.167 m at k 1.676259" as T-22's done evidence.

Neither the T-22 JSON nor its row records that B-10 overrode it; the supersession exists only in
B-10's docstring, its MD §2 and the MODLOG. Per §0 "when they disagree about a measured fact, the
evidence file wins" — here two evidence files disagree about the delivered value, and a later
consumer (B-04's binding, V-01) has no rule for which wins. Worth noting in B-10's favour: T-22
already records `scale_k_out` `1.909565`, i.e. B-10's z factor is T-22-supported; the new part is
the **y** factor `1.873759` (2.271 / 1.212), which appears nowhere in T-22.

### 6. Done check 2 is true by construction, and §12 quotes it without the frame caveat

`body_map()` derives each `k` from the target bbox and then translates so the hull's AABB *is* that
bbox; `deviation()` then compares the AABB to the same bbox. `max |dev| 0.0000 m` can only fail if
the writer is broken, and says nothing about whether the hull is a good hull for the car. The
uniform-`k` negative control shows the check discriminates against a *different* factor, but no
per-axis fit can fail it — so "PASS" on Done 2 is a statement about the writer, not about the
collision volume. Also, §12's "hull union vs body bbox max abs dev 0.0000 m" is measured over the
body-bound hull **only**; the whole-file stored envelope is `3.495 x 3.045 x 7.025` (0.774 m of
wheel below the floor). The MODLOG discloses this, §12 does not, so the row alone reads as a
whole-file measurement.

### 7. Two door hulls stay wired to part indices that no longer exist — and nobody owns the consequence

The written file keeps hulls `0x59c0` / `0x6400` instanced against `part_index` **1 / 2**.
`Builds/bm-002/…sportsmuscle_vehicle_parts.vmodc` (B-04, 59 parts) has **no** parts 1/2 — they were
deleted and not reused (`[(0,'body'), (3,'engine'), (4,…)]`). So the delivered `.physicsc` still
contains two donor-scale door hulls (`0.387 x 1.045 x 1.415 m`, `0.388 x 1.048 x 1.415 m`) bound to
nothing. B-10's reasons for *not scaling* them are sound (R4: no part, no value), and it defers
"per-part hull placement and binding" to B-04 — but B-04 is `done` and only removed the parts. So
whether those two shapes still collide as invisible door-sized volumes is **UNKNOWN**, recorded
nowhere, and falls between two done cards. This should be a named open item (or B-04's follow-up),
not a silent "copied byte-identical".

### 8. R3 is proven at file level, not for the wheel hull's station — the claim "centred on the wheel's own pivot" is only a frame convention

The measured parts of R3 are real and I reproduced them: `stations(pf)` = 0 before and after, the
single `hknpPhysicsSystemData` object is byte-identical (it is not among the 8 changed objects),
and no parts module is written. But "the wheel hull is centred on the wheel's pivot, so the tyre
still spins about the right axis" is about the *frame*, not the world position: the hulls are
written at translation 0 and their placement is the parts module's. In the module B-10 names
(`bm-002`, which is byte-for-byte the same placements as `test-091` for these parts),
`sportsmuscle_wheel_f_l` sits at `(-0.885, 0.4, -1.557)` → track 1.77 m, wheelbase 3.00 m, while
`stations.json` puts the same hub at `(-1.208, 0.7047, -2.57)` → track 2.416 m and DIM-1's wheelbase
is 5.029 m. Nothing in B-10 compares the written wheel hull's placed centre with the station, so
"the station is kept" is **UNKNOWN** for the wheel hulls — it holds only if something else moves the
whole part frame (B-04's row, not measured here). Issue 1 is what hid this: a correctly computed
`placed` envelope would have shown the ~1.0 m z offset.

### 9. `MODLOG.md:16816` — a sha256 that matches no file (R4/R11 in the done record)

> "the parts module is only read (`sha256 3a5c…` in the manifest)"

`bm_collision.json:468` records `stations.parts_module_sha256 = "7335dfe71e95de1c"`, and the module
hashes to exactly that. I checked the other candidate files too: `Working/Parts/bm_vehicle_parts.json`
= `cdaaff765249f754`, `bm-002` module = `4fa283fc774f78b1`, `parts_manifest.json` = `ca7cbf7d764b78e1`.
`3a5c…` matches nothing — a typed citation in the section whose whole point is that nothing is
typed. Same class of defect the card exists to prevent.

### 10. `bm_collision.json:614` — `summary.objects_out: 54` is mislabelled

54 is the **hull** count (`counts["polytopes"]`); the file has 430 objects, which the same JSON
reports correctly in `donor.objects` and `write.objects`. Nothing in the MD prints this field, so it
is a wrong field in a delivered record rather than a wrong claim in the doc — but a consumer reading
`summary` gets 54 objects.

### 11. Typed prose constants in a generated document (R11 nit)

`bm_collision.py:432` hard-codes `"…(2.032 m in Y, 6.167 m in Z) - 0.239 m and 0.858 m short…"`,
which lands in `BM_COLLISION.md:28` and in `bm_collision.json`; `:545` hard-codes "differ by <= 0.3
mm"; §12 repeats `0.239 / 0.858 m`. All four are **currently correct** — I verified 2.271 − 2.0316 =
0.2394, 7.025 − 6.1666 = 0.8584, and the station radii `0.6829/0.6826/0.6826/0.6827` give a 0.3 mm
spread and 2 × mean = 1.3654 — but they are the only numbers in the doc that would survive an input
change, and R11 says generated, never typed. Low severity; worth a one-line compute.

### 12. Cosmetic — `BM_COLLISION.md:3`

The inputs sentence wraps strings that already contain backticks in more backticks, producing
`` `Working/Appearance/build_parts/parts_manifest.json (`body_bbox_m`, B-02 / DIM-1)` `` — the line
renders as broken code spans. Generated by `render_md`, so a one-line fix.

---

## Spot-checks (value, where verified)

| # | value in the doc | where verified | result |
|---|---|---|---|
| 1 | body per-axis `k` = `1.676257, 1.873759, 1.909565` (MD:11, :27) | recomputed from the donor hull `0x5250` bounds (`-1.04250097, 0.24412000, -1.20115054` .. `1.04250097, 1.45612204, 2.47769785`) against `parts_manifest.body_bbox_m` | `1.67625743 / 1.87375922 / 1.90956497` — matches to the printed digits |
| 2 | body radius `0.010000 -> 0.016763` (MD:11) | `0.01 × min(k)` = `0.01676257`; file `0x5250` `convex_radius` decoded = `0.016763` | ✓, and the doc states the rule it used |
| 3 | wheel hull after `0.491 x 1.3654 x 1.2986` (MD:12-15, JSON) | decoded from the written file at `0xb5d0`: min `(-0.2455, -0.6826, -0.6484)`, max `(0.2455, 0.6828, 0.6502)` | `0.4910 x 1.3654 x 1.2986` ✓; wheel `k` = 1.3654 / 0.8225042 = `1.6600523` ✓ |
| 4 | "483 ranges / 1,926 B differ, same file size" (§12, MD:78) | independent byte diff, `Working/Collision/batmobile.physicsc` vs donor | 483 ranges, 1,926 bytes, both 340,368 B ✓ (and 8 objects differ, see issue 3) |
| 5 | "54 hulls over the 54 the file carries, 430 objects / 22 compounds / 112 instances" (MD:7, §12) | decoded both files | 430 / 54 / 22 / 112 ✓ |
| 6 | "stations 0 -> 0", `hknpPhysicsSystemData` identical (MD:7, §12) | `jc3hkx.stations()` both files = 0; diff shows no `hknpPhysicsSystemData` among the 8 changed objects | ✓ |
| 7 | tyre `1.3654 m` and "radii differ by <= 0.3 mm" (MD:43) | `stations.json` corner radii `0.6829/0.6826/0.6826/0.6827` | 2 × mean = `1.3654`, spread `0.3 mm` ✓ (both typed, see issue 11) |

Cross-cutting checks:

* **R4 (provenance):** every row carries a class from the R4 vocabulary — body `derived` (DIM-1 bbox
  / donor AABB), wheels `decoded (T-22)`; the door rows are skipped with a card line as the reason
  rather than invented. Nothing is labelled `assumed`, and the parts with no decoded layout
  (`hknpExternMeshShape` frame, `hknpPhysicsSystemData` layout, G2-30 UNKNOWN 4/5) are named as not
  written in the MODLOG. Good.
* **R5 (behaviour before member):** not engaged — no JC3 member name is borrowed for a behaviour
  here; the card writes hull bytes and the MODLOG correctly reserves runtime acceptance for phase Q.
* **R11:** the MD and JSON are `render_md(public(build()))` output and `--check` re-derives and
  compares both, so every table value is script-derived; the exceptions are the prose constants in
  issue 11.
* **R3 / R7 / R8:** no shared module, no `land_global`, no station row touched; `test-091`'s donor
  files are read-only inputs (the delivered file is a separate `Working/` artefact, same size, so
  the `.toc` record cannot move). The `bm-002` and `test-091` part indices for the 5 written hulls
  agree (`0 / 11 / 12 / 26 / 27`), so the written hulls' part wiring is safe.
* **Tamper claims:** cannot be re-run (they were reverted); the artefacts' sha256 do match what the
  MODLOG states (`192c12479d81da6e…`) and `--check` is green, which is consistent with reversion.

---

## What the card gets right (so the next reader does not re-litigate it)

* The write is a real write: same file size, same object count and class list, 5 hulls and their 3
  ancestors changed, every other byte identical. I reproduced all of that from the bytes.
* The per-axis map is exact for a convex polytope: the written body hull's planes are supported to
  2.93e-07 m and it re-reads as convex; the 54/54 donor re-emission proves the writer round-trips.
* The `jc3hkx.py` extension is additive — `check --all` without `--file` prints the unchanged
  standing-gate totals (`233 / 234 / 130,513 / 18,865 …`) and `check ok`.
* The door decision is at least *reasoned* from a card line and R4 rather than from convenience,
  and the wheel `k` is derived from T-22 and cross-checked in-code against the tyre diameter.
* The MODLOG's own "independent verification" section already flags the whole-file envelope, which
  is the one place this record is honest about the frame it measured.

## What is needed before this card should be cited as evidence in V-01

1. Fix `place()` (or delete the `placed` row) and re-run `--write` + `--check` — one wrong number
   and one false method sentence in `BM_COLLISION.md` §3.
2. Fix `MODLOG.md:16816` (`3a5c…` → `7335dfe7…`), the wrong `summary.objects_out` (54 → 430, or
   rename the field), and the "22 AABB unions exact" wording (21 exact / 22 covered).
3. Record in `t16_collision.json` (or the §12 T-22 row) that B-10 supersedes T-22's uniform body
   `k`, so the two done cards stop asserting different body hulls.
4. Add a named open item for the two door hulls (`0x59c0`, `0x6400`) still instanced against deleted
   part indices 1/2, and state that the wheel hulls' station match is UNKNOWN until placement is
   measured (issue 8).
5. Replace the vacuous `changed_objs == len(changes) + compound_edits` check with a real per-object
   byte comparison (the measurement already exists in this review), and make `graph_signature()`
   include the compound AABB so `--against` can see the 3 edits it currently hides.
