# Recount: the shape and body numbers in `collision-missing-shapes-closest-system-plan.md`

**Provenance / reversibility.** New file, `tmp/freebuff/reports/collision-missing-shapes-recount.md`
= `E:/Modding/JC3-Batmobile/tmp/freebuff/reports/collision-missing-shapes-recount.md`. Intended
change: add one recount; no source, record, package or game file is modified. It is the correct file
because it is the requested output path and the only job artefact. Revert = delete this file.

Inputs, read-only: `tmp/freebuff/reports/collision-missing-shapes-closest-system-plan.md` (254 lines,
the subject), `tmp/freebuff/reports/g3-11-collision-sources.md` (209 lines) and
`tmp/freebuff/reports/g3-12-physicsc-extents.md` (the two censuses used as reference). Plan and census
line numbers are absolute in the file named.

---

## 0. Result

- **26 shape/body figures** are used by the plan. **17 agree** with a census line (or with a decoded
  value in the source file), **1 differs**, **8 cannot be pinned** to either census and are under
  `UNKNOWN` (§4) with the file that would decide them.
- The **one difference** is plan:69, "compounds exist **only** on bodies 16 and 26". The source file
  has **four** compound-shaped bodies: 16 and 26 (`hknpStaticCompoundShape` @ `0x8f20` / `0xc570`)
  and 60 and 61 (`hknpDynamicCompoundShape` @ `0x474c0` / `0x4a920`). The source supports **4**;
  the plan's own line 54 ("compounds 22") is consistent with 4, so line 69 is the outlier.
- Three further count differences are **scope**, not error, and are stated as such: the census counts
  **56 convex element boxes** beside the **3** physics-asset boxes the plan quotes (g3-11:11, :53);
  the plan's **1480 compounds** is a fleet population where the census's is **126** over five files
  (g3-12:9, :11); and g3-11's **32 bodies** belongs to the *wreck* asset, not the Batmobile's 62
  (g3-11:16, :39, :55).
- g3-12's census does not cover `batmobile.physicsc` at all — its five files are the oldjeep, the
  armoured transport, the racing boat, the medium tank and the moped (g3-12:34–40). So for the
  Batmobile's own object/shape counts the only references were g3-11's JSON-derived slot numbers and
  a direct read of the file (§1.2).

---

## 1. Method

### 1.1 What each reference actually counts

| reference | counts | lines |
|---|---|---|
| **g3-11** BmAK side | 3 drivable `RB_BodySetup` boxes (exports 169750 ×2, 169751 ×1); 56 drivable convex element boxes across 43 + 13 elements; 2 convex unions; wreck asset 4 × 32 = 128 bodies, largest wheel box 317.942 cm; **3 + 128 = 131** decoded boxes | 10–11, 16–17, 38–39, 52–57, 63, 174–177 |
| **g3-11** JC3 side | `t16_collision.json`: `hull_slots` **54**, `mapped_to_a_slot` 7, `mapped_bodies` 11, `unmapped` 21, `parts_colliding` **38**; "54 hulls total" | 126–131, 191, 205–206 |
| **g3-12** | five vanilla `.physicsc` files, per file object/hull/compound/mesh counts (car 794/90/45/40, truck 847/112/34/46, boat 382/58/22/9, tank 376/70/17/3, motorbike 241/37/8/10); **126 compounds**, **6,992 hull vertices**, **234 stored AABBs**; compounds are a body's shape *or* a child of one | 9, 11–12, 34–40, 65–67, 95, 111–115 |

### 1.2 The one extra reference, and why it was needed

The subject of the plan is `Working/Collision/batmobile.physicsc`, which **is not one of g3-12's five
files** and whose object counts g3-11 does not state. Rather than mark six figures UNKNOWN, the file
was read once, read-only, with the project's own reader (5-minute experiment, nothing written):

```
$ PYTHONIOENCODING=utf-8 python -        # sys.path += Tools/scripts; jc3hkx.Packfile(...)
objects 430
  CPfxPartIndexProperty                  98
  hknpConvexPolytopeShape                54
  hknpDynamicCompoundShape               20
  hknpExternMeshShape                    18
  hknpStaticCompoundShape                 2
  hknpShapeMassProperties                56
  hkpLimitedHingeConstraintData           9
  hkpRagdollConstraintData                2
  hknpPhysicsSystemData                   1
  simdata body_entries: size=62 cap=62
compound instances: 2 static × 7 + 20 dynamic = 112 total
body → shape (entry +0x00): hull 40, extern mesh 18, static compound 2, dynamic compound 2
body 16 -> hknpStaticCompoundShape @ 0x8f20 ; body 26 -> hknpStaticCompoundShape @ 0xc570
body 42..59 -> hknpExternMeshShape ; body 60, 61 -> hknpDynamicCompoundShape
```

This is labelled **source** in the table, and it is shown here so every "source" row is reproducible.
It never contradicts a census line; it supplies the counts the censuses do not carry. (Tool note,
outside the plan's figures: `jc3hkx.py:94` sets `BODY_ENTRY_SIZE = 96`, while its own report text at
`jc3hkx.py:1168` says "80-byte body entries". The recount used 96, the constant the reader actually
steps with. The plan quotes no body-entry size, so no row depends on it.)

---

## 2. Recount table

| # | figure as the plan states it | plan line(s) | reference line | verdict |
|---|---|---|---|---|
| 1 | drivable **2 bodies** | 4, 185 | g3-11:53 (169750 carries boxes 0 and 1; 169751 carries one) | **AGREE** |
| 2 | drivable **3 boxes** | 4, 22, 185 | g3-11:10, :53, :175 (3 physics-asset boxes) | **AGREE** (physics-asset boxes only — see §3.2) |
| 3 | drivable **1 constraint** | 4, 185 | — neither census counts BmAK constraints (g3-12:95 counts *JC3* constraints on the car: 10 hinge + 7 ragdoll) | **UNKNOWN** |
| 4 | extents `690.305×374.536×207.500`, `679.585×345.688×103.500`, `166.177×189.365×39.800` cm | 26–28 | g3-11:53 (all three triples, same order) | **AGREE** |
| 5 | centres `(9,0,106.75)`, `(0,0,79)`, `(−30.5,0,93.25)` | 26–28 | — g3-11:53 quotes extents only | **UNKNOWN** |
| 6 | box 2 TM **4.000°** about y | 28, 43 | — g3-11 quotes no rotation; g3-12 decodes *JC3* instance bases, not BmAK boxes | **UNKNOWN** |
| 7 | union **693.945×374.536×207.500** cm at (7.18, 0, 106.75) | 39, 125 | derived from #4 (both g3-11:53 values); not a census figure | **AGREE** (arithmetic on census values) |
| 8 | box 1 protrudes **3.64 cm** | 34, 45, 128, 202 | derived: (690.305/2 + 9) − 679.585/2 = 3.640 | **AGREE** |
| 9 | donor **54 hulls** | 5, 54, 58 | g3-11:130 (`hull_slots` 54), :206 ("54 hulls total"); source 54 | **AGREE** |
| 10 | donor **112 instances** | 5, 54 | census silent; source 112 (2×7 + 20 compounds) | **AGREE** |
| 11 | **14 instances unbound** | 5–6, 56, 72 | census silent (its `unmapped` 21 at g3-11:130 is the wreck census, a different quantity); source 14 | **AGREE** |
| 12 | **430 objects** | 54 | census's object column covers other files (g3-12:36–40); source 430 | **AGREE** |
| 13 | **18** extern meshes | 54 | source 18 (`hknpExternMeshShape`), all 18 are body shapes | **AGREE** |
| 14 | **22** compounds | 54 | source 20 dynamic + 2 static | **AGREE** |
| 15 | **40** hulls bound to a part (body shapes) | 55 | source 40 body entries point at a hull | **AGREE** |
| 16 | bumper bodies **16 / 26** → compounds `0x8f20` / `0xc570` | 56 | source: body 16 → 0x8f20, body 26 → 0xc570, 7 instances each | **AGREE** (exact) |
| 17 | **98 of 112** carry a `CPfxPartIndexProperty` | 57 | source 98 property objects; 112 − 14 = 98 | **AGREE** |
| 18 | free hull slots **0** — 40 + 14 = 54 | 58 | source 54 polytopes, 40 body shapes, 14 bumper children | **AGREE** |
| 19 | "compounds exist **only on bodies 16 and 26**" | 69 | source: **4** compound bodies — 16, 26 (static) and 60, 61 (dynamic) | **DIFFERS** — source supports 4 |
| 20 | **1480/1480** compounds are a body's shape or a child of one | 69 | g3-12:9, :11, :66 give **126** compounds (45+34+22+17+8) over five files | **UNKNOWN** (see §3.3) |
| 21 | **62 body entries**, each with a part index | 71, 164 | census silent; source `body_entries` size 62 | **AGREE** |
| 22 | front-bumper compound `size = 7` | 89 | source 7 instances on 0x8f20 | **AGREE** |
| 23 | hull budget **244** vertices, u8 cap **255** | 73, 124 | — neither census states a per-hull budget or cap (g3-12 counts 6,992 vertices *over* 126 compounds) | **UNKNOWN** |
| 24 | **54/54** hulls re-encode byte for byte | 119, 182 | — a tool result, not a census | **UNKNOWN** |
| 25 | **5 objects** rewritten (1 body hull + 4 wheels) | 150 | — not in either census | **UNKNOWN** |
| 26 | **5 cm** acceptance band, **1.0 cm** tolerance | 128, 202 | — not in either census | **UNKNOWN** |

Tally: 17 AGREE, 1 DIFFERS, 8 UNKNOWN (rows 3, 5, 6, 20, 23, 24, 25, 26).

---

## 3. Where the plan and the census differ

### 3.1 The one real difference: how many bodies carry a compound (plan:69 vs the file)

The plan writes, inside the compound-shape row:

> Body 0's shape is a hull, not a compound (**compounds exist only on bodies 16 and 26**)

A direct read of the 62 body entries' shape pointer resolves **four** entries to a compound:

| body | shape class | object |
|---:|---|---|
| 16 | `hknpStaticCompoundShape` | `0x8f20` (front bumper, 7 children) |
| 26 | `hknpStaticCompoundShape` | `0xc570` (rear bumper, 7 children) |
| 60 | `hknpDynamicCompoundShape` | `0x474c0` (16 children) |
| 61 | `hknpDynamicCompoundShape` | `0x4a920` (14 children) |

Neither census line contradicts the plan here — neither classifies bodies by shape (g3-11:53 counts
boxes, g3-12:66 counts compounds against their child union) — so this is a case where **the source
file is the tie-breaker**: it supports **4**, and it supports the plan's own line 54 ("compounds 22":
20 dynamic + 2 static). The arithmetic that shows line 69 is the outlier needs nothing but the plan's
own numbers: 62 bodies − 40 hulls (line 55) − 18 extern meshes (line 54) = **4**.

Scope of the correction, so it is not over-read:

- Route A's argument is **unaffected**: body 0 is still a hull (source: body 0 → polytope), so a
  compound on body 0 still has to be a new object.
- The plan's §5 U2 ("whether a JC3 body entry may point at a compound instead of a hull … no donor
  body does this for a **chassis**") stays literally true — but the file shows body→compound is
  already normal on four bodies, so the open half of U2 is narrower than the row reads.
- Only the parenthetical is wrong; the plan's "the two donor bumper compounds" (line 6) and "bodies
  16/26" (lines 56, 106, 216) all name the static pair correctly.

### 3.2 Scope, not error: 3 boxes vs 59 decoded drivable boxes

The plan's "3 boxes" (lines 4, 22, 185) is the `RB_BodySetup` census. The same census counts **56
convex element boxes across 43 + 13 elements** beside them (g3-11:11, :38, :53, and the oracle
list at :175) and two convex unions (`695.4/492.9/294.5` and `670.9/318.3/224.1` cm, g3-11:53). g3-11's own
131-box arithmetic counts only physics-asset boxes (g3-11:57), so the plan is using the census's own
convention. Verdict: **the census supports "3" for the physics-asset boxes and "56" for the convex
elements**; a reader who takes "3 boxes" as "every decoded drivable box" would be wrong by 56.

### 3.3 Scope, not error: 1480 compounds vs 126

Plan:69 counts the whole fleet (1480 compounds, every one a body's shape or a child — a `G3-10f.md`
statement). g3-12's census covers **five files and 126 compounds** (g3-12:9, :66). The two numbers
are not comparable, and neither census can confirm 1480; row 20 is therefore UNKNOWN rather than
"differs". The census's own structural finding is consistent with the plan's use: no compound in the
five files is orphaned — 126/126 are covered by their children's union (g3-12:11–12), which is the
same property the plan relies on ("a compound is the shape of exactly one body entry or a child").

### 3.4 The figure a reader is most likely to confuse: 32 vs 62 bodies

g3-11's whole finding is that the ledger quoted the **wreck** asset: **32 bodies per vehicle**, 128
records over 4 vehicles (g3-11:16, :39, :55, :63). The Batmobile's own `.physicsc` has **62 body
entries** (source, plan:71). The plan never mixes them — it cites 62 and does not use 32 — but any
future row that writes "32 bodies" for the Batmobile would be re-introducing exactly the error g3-11
documents. (g3-11's `unmapped` 21 at line 130 is likewise a wreck-side count, not spare hull space.)

---

## UNKNOWN

Each entry: what could not be pinned, and the file that would decide it. None of these is filled in
from assumption.

1. **"1 constraint" on the BmAK drivable asset** (plan:4, 185). Neither census counts BmAK
   constraints. Decided by `Working/Translation/T22_REOPEN.md` S4 / `RB_ConstraintSetup` 171462 —
   the plan's own §2 line 76 cites `T22_REOPEN.md` S4, and §8 U5 records that no `RB_ConstraintSetup`
   layout is in `Research/BatmobileGrab/BMSDK_OFFSETS.json`. Note the contrast the censuses do make:
   g3-12:95 counts **17 JC3 constraints** on the oldjeep (10 `hkpLimitedHingeConstraintData` + 7
   `hkpRagdollConstraintData`), and the Batmobile's own file has **9 hinge + 2 ragdoll = 11**
   (source read above) — that is the JC3 side, not BmAK's 1.
2. **The three box centres** `(9,0,106.75)`, `(0,0,79)`, `(−30.5,0,93.25)` (plan:26–28). g3-11:53
   quotes extents only. Decided by `Research/BatmobileGrab/COLLISION_GEOM.md`, which g3-11:38 names
   as the parser of the three `RB_BodySetup` boxes.
3. **Box 2's 4.000°/det 1.000000054 transform** (plan:28, 43, 205). Not in either census; the plan's
   own U7 (line 219) says `COLLISION_GEOM.md` does not decode the rotation either. Decided by a
   re-read of the export 169751 transform in `T22_REOPEN.md`, or `COLLISION_GEOM.md` if extended.
4. **1480 compounds, fleet-wide** (plan:69). g3-12's population is 126 over five files (g3-12:9, :66).
   Decided by `G3-10f.md`'s compound table, which the plan cites at line 69, or a fleet-wide re-run of
   `Tools/scripts/jc3_physicsc_extents.py` with a larger file list.
5. **244-vertex hull budget / 255 u8 cap** (plan:73, 124). Not a census figure; g3-12 counts 6,992
   vertices across 126 compounds, never a per-hull maximum. Decided by `Tools/scripts/bm_colhull.py`
   (`HULL_BUDGET`) and the per-hull maxima in `Research/JC3Grab/PHYSICSC_EXTENTS.md`.
6. **54/54 hulls re-encode byte for byte** (plan:119, 182). A writer self-test result, not a file
   count. Decided by `Tools/scripts/bm_colhull.py selftest` on this file.
7. **5 objects rewritten (1 body hull + 4 wheels)** (plan:150). Not in either census. Decided by
   `B-10.md:52` (the plan's citation) or `check_file(..., against=donor)`'s `changed_objects`.
8. **5 cm acceptance band / 1.0 cm `TOL_HULL_CM`** (plan:128, 202). Not in either census. Decided by
   `Tools/scripts/bm_vehicle_hull.py` (`TOL_HULL_CM`) and the T22 reopen's gate text.

---

## 4. Limits of this recount

1. **Two figures are 17-vs-1 because the census was built for a different question.** g3-11 audits
   *provenance* of five ledger rows and g3-12 decodes *extents* on five other vehicles; neither tries
   to profile `batmobile.physicsc`. So the AGREE verdicts on rows 10–18 rest on the source file read
   in §1.2, not on a census line, and are marked that way.
2. **The source read is structural, not a semantic decode.** It counts objects by class, the 62 body
   entries and the shape pointer at each entry's +0x00, and sums compound children. It does not
   verify that a body's part index is sensible, nor what bodies 60/61 are (the plan's §3 notes a
   `hknpDynamicCompoundShape` is not a hull); that remains `T22_REOPEN.md`'s territory.
3. **The one DIFFERS verdict is not a safety issue.** All of Route B (the recommended route) and the
   3.64 cm arithmetic rest on rows 4, 7, 8, 15–18, which agree; only the §2 compound-shape row's
   parenthetical is affected, and §3.1 states what the row should say.
4. No `.physicsc`, build tree or install was touched; the only file written is this report.
