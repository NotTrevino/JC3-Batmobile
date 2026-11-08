# Independent review — G2-30 · `.physicsc` write spike

Reviewer note: I did not write this card. Read-only review; nothing under `GRAB_BACKLOG.md`,
`MODLOG.md`, `Research/`, `Tools/` or the game install was modified. No game was launched and
`D:\Games` was not touched.

## VERDICT

**minor issues.** The card's Done clause is met and I could re-derive every headline structure
byte for byte: the round trip is identical on both files, the scaled wheel and the size-changing
hull replacement re-read with 0 problems, and `check --all` reproduces the MODLOG's line exactly.
Two evidence statements are wrong and should be fixed before the doc is reused: the **remap-stress
case does not remap the root container** (it prepends 16 bytes *inside* `hkRootLevelContainer`,
so its three inbound fixups end up pointing into filler while the check reports PASS), and the
**AABB-margin rule is mis-stated** ("the root sits 0.011 m inside its union" — the file says
0.010 m, and 10 of 22 compounds carry no inset at all). Neither changes the card's answer (hull
writes are possible), but both are claimed as measured facts. The rest are typed numbers in a
generated doc (R11) and two mislabels.

## Check output (verbatim)

```
$ python Tools/scripts/jc3hkx.py write --check
PASS: round trip identical (2/2 files, 54 hulls re-emitted) | remap 0 problems | scale 0 | replace 0 | hulls 54 compounds 22, json match True, md match True
```

Exit status 0. Identical to the line recorded in `MODLOG.md` §"G2-30 · `.physicsc` write spike
(old Batch D route) — done".

Standing gate, also re-run (`python Tools/scripts/jc3hkx.py check --all`, exit 0), verbatim:

```
entities 233 | files 234 | objects 130513 | hulls 18865 (convex 18865) | mesh shapes 4791 | geometries 9582 | compounds 6382 (35499 instances, 25769 with a part index, 6341 AABB unions exact) | station sets 17 (land_global agree 17, disagree 0)
check ok
```

Matches the MODLOG block exactly. Out paths exist: `Research/JC3Grab/PHYSICS_WRITE.md` (194 lines;
the MODLOG says 195 — see issue 9), `PHYSICS_WRITE.json`, the writer in `Tools/scripts/jc3hkx.py`
(block from line 1384, `write` subcommand at line 2270), and the five test blobs under
`E:\Modding\_JC3grab\hkx\write\` (340,368 / 340,368 / 340,384 / 340,368 / 341,440 B).

What `--check` verifies versus the card's Done: it re-derives the four cases, requires the round
trip to be byte-identical on both files, requires the three problem lists to be empty, and
byte-compares each of the five written blobs with the bytes re-derived now, then compares the md
and json with their regeneration. That covers "round-trip identical and the modified file passes
every invariant" for the invariants the reader knows (the doc says so, §1/§9.5). The second half of
the Done ("rows T-P3/T-CO2/T-CO3 become buildable") is prose in §8 and is not machine-checked, as
intended — those rows belong to T-22.

## Issues

1. **The remap-stress case corrupts the root container and the checker cannot see it.**
   `Tools/scripts/jc3hkx.py:1755` (`_case_shift`) builds the edit as
   `filler + <object-0 blob>`, i.e. the 16 bytes are inserted **inside** `hkRootLevelContainer`
   (object 0, 96 B) rather than before the data section. Verified on the written blob:
   `shift16.physicsc` object 0 is `7f`×16 followed by the donor's original 96 bytes, extent 112.
   Its three inbound fixups are unchanged (`0→16`, `16→40`, `24→64`), so the container's fields
   now live at 32/48/72 while the pointers and the fixup `from` slots still address 16/40/64 —
   the container's own content is shifted out from under its fixups. The check passes because
   `verify_written` (`jc3hkx.py:1660`) records only `(class, extent)` for a non-hull/non-compound
   object in `graph_signature`, and object 0 is in `edits`, so any change to it is whitelisted;
   the pointer check only asserts that targets land inside *some* object's extent. So
   `PHYSICS_WRITE.md:66-68` — "**0 violations** and a decoded graph identical object-for-object" —
   is not established, and line 26 ("every pointer still resolves") is true only in that weak
   sense. The capability claim itself survives on the **replace** case, which shifts every object
   after the hull and is genuine (see spot-check 4), but the shift case is presented as "the case an
   in-place patcher cannot do" and should either be fixed (insert before the section and bump the
   section offset) or labelled as a structural-only test.

2. **The AABB-margin rule is numerically wrong and is not the file's rule.**
   `PHYSICS_WRITE.md:92-96` says "the stored box is the children's union inset by the convex
   radius (the root sits 0.011 m inside its union on every axis)". Measured on the same file: the
   root `hknpStaticCompoundShape` @`0x8f20` has margins `cur − union` = −0.00999999,
   −0.010000005, −0.00999999 on min **and** max (0.010 m, not 0.011); and 10 of the 22 compounds
   have **zero** margin, while `0xc570` has +0.002494 / +0.020233 on two axes. So "inset by the
   convex radius" is a property of some compounds, not a rule. The writer does not implement that
   sentence — `compound_aabb_edits` (`jc3hkx.py:1562`) preserves each compound's own margin — so
   the code is right and the prose is wrong, which matters because the doc calls this "the only
   value the writer *derives*". A reader implementing the sentence breaks exactly the 10
   zero-margin compounds the MODLOG says the first attempt broke.

3. **The `min`-byte census is a per-plane value reported as a per-hull one.**
   `PHYSICS_WRITE.md:130-131` and `:173-174`: "`min` takes 1 (31 hulls), 0 (17 hulls), 3 (16
   hulls), 2 (15 hulls) with no reading yet". `_face_census` (`jc3hkx.py:1806`) collects
   `mins` as a **set** per hull, so a hull is counted once for every distinct value it contains;
   the counts sum to **478**, not 54, and only **1 of 54** hulls has a single value (hull
   `0x5250` carries 16 distinct `min` bytes). The numbers are correct as "hulls containing at
   least one record with this value"; the wording implies one value per hull and the §7 step-1
   sentence inherits it.

4. **"the largest box (211x51x109 cm)" is not the largest.** `PHYSICS_WRITE.md:164` (T-CO2 row).
   `Research/BatmobileGrab/PHYSICS.md` rows 1 and 8 give 211.54×51.093×109.003 cm (front wheel)
   and 316.155×63.418×109.881 cm (rear wheel), and the ledger's own T-CO2 row says "largest box
   316.15x63.42x109.88 cm". The conclusion (it fits a donor hull, longest axis 3.679 m) still
   holds for 316 cm; the label and the number are wrong.

5. **"the donor" is the live build's copy, not the shipped donor file.**
   `Builds/test-091/aaf/.../sportsmuscle.physicsc` has sha256 `1b90daef…`; the shipped donor
   `.physicsc` inside the base `…_civilian_01.ee` is also 340,368 B but hashes `62163ea4…` and
   differs in **44 bytes over 8 ranges** (the four wheel-station quads). Every structure the doc
   measures is identical (54 hulls, 430 objects, wheel hull 0.822504 m, r 0.01, same class
   census), so no number changes — but "The donor can be read, re-emitted byte for byte" and the
   §3 sha256 row describe `Builds/test-091`, not the archive's file. Read the doc's "donor" as
   "the test-091 build copy".

6. **R11: many numbers in the generated doc are literals in `physics_md`, so `--check` cannot see
   them go stale.** `PHYSICS_WRITE.md` lines 9 ("every extent a multiple of 16"), 25 ("0
   violations"), 75 ("centroid at the part origin"), 95 ("0.011 m"), 103 ("`convex 54/54`"), 117
   ("56 objects"), 121 ("42 parts"), 124 ("32 bodies … 8 … 1 … 1 … 2 … 1"), 134 ("4 wheel hulls
   (704 B each, identical topology)"), 164 ("211x51x109"), 171 ("floats in one hull, `0xFF` words
   in another"), 177 ("80- and 64-byte body entries"). I checked the important ones and they are
   true today (all extents are multiples of 16; the four 704 B hulls are all 20 v / 12 p / 60
   indices / r 0.01; `hknpShapeMassProperties` is 56), but none comes from `doc`, so a change in
   the file would leave them untouched and green.

7. **The factor's shown arithmetic does not reproduce.** `PHYSICS_WRITE.md:75-77`: "**1.659566**
   = … Ø 1.365 m … / 0.8225 m". 1.365 / 0.8225 = **1.659574**; the exact hull height is 0.8225042
   m, which does give 1.659566. The display rounds the denominator to 4 dp, so the stated division
   is off by 8e-6. Related, "centroid at the part origin" is neither derived nor the datum used:
   the writer scales about the bounding-box centre, measured at (−1.06e-05, 7.56e-05, 0.0008767),
   ~0.9 mm from the origin; the vertex centroid is never computed.

8. **Two count/label slips in the prose.** `PHYSICS_WRITE.md:6` promises "two hard limits" while
   §6 lists four "may not" rows; `:15` is headed "The four cases" while the table has five rows
   (two round-trip files + three edits).

9. **Journal/tracker numbers that the outputs cannot back.**
   `MODLOG.md:11389-11390` says `PHYSICS_WRITE.md` is "(195 lines, generated)"; the file is **194**
   lines (the correction pass shortened it and the parenthetical was not updated).
   `GRAB_BACKLOG.md:1313` repeats "pointer slots must stay 0 (writing them cost 2,702 bytes while
   still passing the reader)" — the 2,702 figure exists only in a code comment
   (`jc3hkx.py:1507`) and MODLOG prose; no case in `PHYSICS_WRITE.json` produces it, so `--check`
   does not verify it.

## Spot-checks

| # | value in `PHYSICS_WRITE.md` / tracker | where I verified it |
|---|---|---|
| 1 | round trip `donor` **340,368 B**, sha256 `1b90daefdc9660b4…`, identical | Read the source file directly: 340,368 B, sha256 `1b90daefdc9660b4…`; the artifact `_JC3grab/hkx/write/roundtrip_donor.physicsc` is byte-identical to it, and `roundtrip_assembled.physicsc` to `Working/Assembled/sportsmuscle_true.physicsc` (`6a0e7e13efb329a3…`). |
| 2 | file census: **430 objects**, **0 gap**, every extent a multiple of 16, sections `__classnames__` @0x100 (528 B) / `__types__` @0x310 (0 B) / `__data__` @0x310 (339,584 B), **339 local / 765 global / 430 virtual** fixups, **54 hulls / 38,416 B / 22 compounds / 112 instances** | Independently parsed the donor with `jc3hkx.Packfile`: 430 objects, 0 non-multiple-of-16 extents, gaps 0 and last object ending at `lf` = 322,288, sections exactly as printed, 339/765 fixups and `len(pf.virtual)` = 430, 54 polytopes totalling 38,416 B, 22 compounds, 112 instances. Class census matches the JSON key for key. |
| 3 | scaled wheel: hull @`0xb5d0`, box **[0.4909, 1.365, 1.2982] m**, r **0.016596**, **252 B over 69 ranges**, **2** parent AABBs, stale case fails with `@0x484f0: a child AABB is outside the compound AABB` | Re-read `scale_wheel.physicsc` from disk: 20 v / 12 p, r 0.0165957, box 0.4909 × 1.365 × 1.2982 m; `diff_ranges(donor, scaled)` = 69 ranges / 252 B; all 56 non-degenerate vertex axes share exactly one ratio **1.659566** about the bbox centre; `K.decode_compound` shows 22 compounds and `compound_aabb_edits` touches `0x474c0` + `0x484f0` only. |
| 4 | size-changing replace: **704 → 1776 B**, **340,368 → 341,440 B**, still **430 objects**, 36 v / 47 p | Re-read `replace_hull.physicsc`: 341,440 B, 430 objects, slot `0xb5d0` extent 1,776 B decoding as 36 vertices / 47 planes. All 214 global fixups that target a hull target its offset 0 (verified), so a wholesale hull swap does not break an interior reference. |
| 5 | (negative) "donor" | The shipped donor `.physicsc`, extracted from the base `…_civilian_01.ee`, is 340,368 B with sha256 `62163ea4…`, i.e. **not** the file the card reads; 44 bytes differ over 8 ranges, and the wheel hull geometry is identical (0.822504 m, r 0.01). See issue 5. |
| 6 | standing gate numbers (233 entities / 18,865 hulls / 6,382 compounds / 35,499 instances) | `python Tools/scripts/jc3hkx.py check --all` run live; output quoted above and identical to MODLOG. |

## Not checked

- The MODLOG's three-way tamper test and the intended-change entry were not re-run (it would
  write into `Research/`, which this review may not do). The counter-example inside the JSON
  (`scale.stale_problems`) was confirmed by re-reading the stale case logic, not by rebuilding it.
- Runtime acceptance (Havok/the game loading a written file) is explicitly not claimed by the doc
  and was not tested — no game was launched.
- `Working/Assembled/sportsmuscle_true.physicsc` was checked only for the 2-byte station delta and
  the round trip, not for provenance (which card produced it).
