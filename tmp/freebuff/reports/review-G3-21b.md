# Review — G3-21b `RESET_STATUS2.md` refresh (R-1..R-6)

Reviewed: `tmp/freebuff/reports/G3-21b.md`, `Research/RESET_STATUS2.md`, `Tools/scripts/reset_status2.py`
(read only), against the reports it cites and against `tmp/freebuff/reports/` itself. Nothing was
edited except this file.

## VERDICT: **needs rework** (narrow — the ratings survive, the premise does not)

Every number I checked in the R-1/R-4/R-6 prose reproduces **except three**, and the 0/6/0 rating is
what the stated rule forces. But the document's defining claim — "every `G3-*.md` in
`tmp/freebuff/reports` is scanned" — is false on three files, and one of them refutes R-3's whole
"what changed" paragraph. On top of that, two cards in the census are listed without the review
verdict they actually carry, one of them (R-1's `G3-01b`, R-5's core `G3-20`) in a way that changes
what the item can claim.

Concretely:

1. **Three G3 reports on disk are not in the census.** The document was generated at
   `2026-11-04T15:09` (its own mtime). Cards written afterwards: `G3-07b2.md` (21:04),
   `G3-07b1.md` (21:36), `G3-04e1.md` (22:38). `Research/RESET_STATUS2.md` mentions none of them
   (`grep -c "G3-07b1\|G3-07b2\|G3-04e1"` = **0**). The inventory line "reports scanned: 53" is
   consistent with its own scan, but there are now 58 `G3-*.md`, i.e. 56 evidence reports excluding
   `G3-21.md` and `G3-21b.md` itself — 53 + 3.
2. **R-3's newest-card sentence is refuted by two of them.** The document says R-3's newest card is
   `G3-07a` (11-03T06:31) and "no new runtime card landed in this window", and U-1 says "no new
   runtime card since `G3-07a`". `G3-07b1` opens by accepting `review-G3-07a` as its starting point
   and resolving the six `.pdata` chunks; `G3-07b2` decodes body-slot float4 groups from
   `JustCause3.exe`. Both are newer than `G3-07a` and both are in the `G3-07b` runtime family.
3. **R-4's newest card is stale for the same reason.** `G3-04e1` (22:38, the on-disk format of the
   material uniform records) landed after generation and is on R-4's subject.
4. **Three review verdicts are missing from the census, one of them on a core card.**
   `review-G3-04d.md` (22:50) = **needs rework**; `review-G3-20.md` (22:43) = **needs rework**;
   `review-G3-11c.md` (22:41) = **needs rework**; and `review-G3-21.md` (22:42) = **needs rework**
   on the very document this one supersedes. `RESET_STATUS2.md` shows `G3-04d` as "partial",
   `G3-20` as **core / done**, `G3-11c` as "done", all with an empty review column, and never says
   its own base `G3-21` was sent back.
5. **A review that predates the generation is also missing.** `review-G3-01e-fix.md` (13:59) — i.e.
   before 15:09 — verdict: "**The settlement's conclusion is right and its corrections are wrong**".
   `RESET_STATUS2.md` lists `G3-01e-fix` (supporting) as "done" with no review note, so R-1's
   supporting set is presented cleaner than the record.
6. **Three unsupported numbers in R-1's prose** (details in §1): "3556 bodies", "five candidate
   partner rules" and "439/439 cases" do not occur in `G3-10d.md`, and `439` occurs in none of
   `G3-10d.md`, `G3-10h.md`, `G3-10i.md` or `Research/JC3Grab/PHYSICS_ROLES4.md`.
7. **The document repeats the exact error `G3-21` was sent back for.** R-1's *What remains* says
   "`G3-01` and `G3-01b` themselves have no report file", while its own census row for `G3-01b`
   lists `G3-01b-boxes.md`, `G3-01b-cyl.md`, `G3-01b-mode.md`. All three exist (02:48 / 03:44 /
   02:19 on 11-03). `review-G3-21.md` row S2 flags this same sentence in `RESET_STATUS.md`.

None of this moves the 0/6/0 result: the rule needs every core card `done` and unreviewed, and
`G3-20`'s new `needs rework` only entrenches R-5 as PARTIAL. The problem is the claim that the
census is complete and current, which is the reason to run this synthesis at all.

## 1. R-1 — every changed sentence checked

Document's line: "`G3-10d` scores five candidate partner rules over 50 fleet files / 494 constraint
records / 3556 bodies and none fits every record; `G3-10h` shows `hknpConstraintCinfo.bodyB` is
`0x7fffffff` in 494/494 …; `G3-10i` shows the loader validates both ids against that sentinel and
**drops** the record, never substituting a fixed/world body."

| claim | source | verdict |
|---|---|---|
| five candidate partner rules | `G3-10d.md` line 77 describes one oracle ("both bodies must touch its pivot"); line 13 scores **bodies 0/1/2/3** (48.4 % vs 7.2/6.4/9.7 %), line 25 scores int16 triples for inertia. No "five rules" list. | **not in the source** |
| 50 fleet files | `G3-10d.md` line 48: `fleet files: 50` | **verified** |
| 494 constraint records | `G3-10d.md` line 48: `cinfos: 494` | **verified** |
| 3556 bodies | `G3-10d.md` line 48 gives `hulls with mass: 2011`; `3556` / `3,556` occurs nowhere in it | **not in the source** |
| none fits every record | `G3-10d.md` §2 is a scoreboard of candidate readings, each with a failure rate | **verified in substance** |
| `bodyB` = `0x7fffffff` in 494/494 | `G3-10h.md` lines 27–30, 102 | **verified** |
| loader validates both ids and drops the record | `G3-10i.md` line 39 (re-swept 50 files / 494 records / 494 sentinel) and line 41 — but line 41 is labelled "**Derived (not decoded)**" | **verified, but mislabelled**: `RESET_STATUS2.md` files the `CONSTRAINT_CODE2.md` line under "What the G3 outputs establish (**decoded**)" |
| "the one positive structural result … 439/439 cases" | `grep 439` over `G3-10d/10h/10i` and `PHYSICS_ROLES4.md` → **no matches** | **unsupported** |
| `G3-01e` is under `needs rework` | `review-G3-01e.md` (11-03T06:17): "VERDICT: needs rework" | **verified** |
| `G3-01` and `G3-01b` have no report file | `G3-01b-boxes.md`, `G3-01b-cyl.md`, `G3-01b-mode.md` all on disk; census row for `G3-01b` lists them | **false in the prose, contradicted by its own census** |
| census: `G3-01b` "done (review: minor issues, needs rework)" | `review-G3-01b.md` (05:56, minor issues) and `review-G3-01b-mode.md` (needs rework) — both real, but two different reports are merged into one cell | **misleading, not false** |
| census: `G3-10d` partial, no review | `review-G3-10d.md` (11-03T08:03) exists; its verdict table says the script is **not** clean of two-version leftovers | **review omitted** |

## 2. R-4 — every changed sentence checked

Document's line: "`G3-09c` re-reads them as `u32` small integers 0..10 (denormal as floats) and shows
the consuming code reads integers; `G3-04d` decodes both cooked shader caches (38,201 + 2,098 DXBC
containers) and finds **0 `RDEF` chunks** … That is a decoded negative".

| claim | source | verdict |
|---|---|---|
| 15 constants are u32 integers 0..10 | `G3-09c.md` line 1 and line 21: "`u32`: 14 of 15 tuples have a non-zero word (values 0…10); only `0x142331360` is all zero" | **verified** |
| denormal as floats | `G3-09c.md` line 22: `float4_at()` did `round(x, 6)`, a denormal rounds to `0.0` | **verified** |
| consumer reads integers | `G3-09c.md` line 43 plus `review-G3-09c.md` (14:14), which adds that the consumer builds 32-byte `D3D11_INPUT_ELEMENT_DESC` records | **verified** (the review adds a step the card omits) |
| 38,201 + 2,098 DXBC containers | `G3-04d.md` lines 11–12, 63–67 | **verified** |
| 0 `RDEF` anywhere | `G3-04d.md` lines 18–19: "0 of 38,201 and 0 of 2,098" | **verified** |
| "strongest statement R-4 can now make" | `review-G3-04d.md` (22:50) = **needs rework**: the two headline counts survive, a third headline does not | **the two named facts hold; the card is under `needs rework`, which the document does not show** |
| "Four colour cards are under a `needs rework` review (`G3-04b`, `G3-09`, `G3-03`, `G3-09b`)" | all four verified in their reviews (11-03); `G3-04d` now makes **five** | **incomplete** |

## 3. R-6 — every changed sentence checked

| claim | source | verdict |
|---|---|---|
| `Default__RVehicleBatmobile` tag by tag, 274 tag rows | `G3-06b.md` line 6 and line 23 ("274 tag rows + the comparison", 768 lines) | **verified**; `review-G3-06b.md` (21:38) = minor issues, consistent |
| `.ddsc` 116/116 FULL; the 84-byte tail is one record per absent mip | `G3-12d.md` lines 9, 14, 105, 118 (78 records, tag `0x01000010`) | **verified** |
| `.pfxc` 4/4 FULL; no trailing blob, a length field was read as an offset | `G3-12d.md` line 15 | **verified** |
| `G3-19`/`G3-19b` finish the donor depth | `G3-19b.md` lines 15–17: 7126 / 2592 / 1214 **exact**; `G3-19.md` STATUS "done — 1 of 4 FULL, 3 of 4 FULL except one named block payload" | **verified, but `review-G3-19.md` (14:08) "ACCEPT WITH CORRECTIONS" is not shown, and it says the check's headline oracle is an identity, not a proof** |
| `G3-12e` attributes all 2,293 round-trip bytes | `G3-12e.md` line 16: "2,293 bytes differ (2.09%)"; `review-G3-12e.md` (21:51) = holds | **verified** |
| `G3-14` indexes `AkBank` carriers and names the 29 banks | `G3-14.md` lines 20, 40, 55 (29 referenced banks) | **verified** |
| "…with the absent banks **named**" | `G3-14.md` line 5: "**0 of the 29 referenced banks are absent**, and 10/10 of the banks called missing are **present**" | **contradicted by its own source** |
| `G3-06` under `needs rework` is why R-6 is not RESOLVED | `review-G3-06.md` (11-03T06:18) = needs rework | **verified** |

## 4. Cards after the generated timestamp, missing from the census

Generation time = `G3-21b.md` mtime `2026-11-04T15:09`.

| card | mtime | in census? | consequence |
|---|---|---|---|
| `G3-07b2.md` | 2026-11-04T21:04 | **no** | R-3 "no new runtime card" false |
| `G3-07b1.md` | 2026-11-04T21:36 | **no** | R-3 "no new runtime card", U-1 false |
| `G3-04e1.md` | 2026-11-04T22:38 | **no** | R-4 newest cited card stale; R-6 cites "materials" too |

Reviews that landed after 15:09 and change the census columns: `review-G3-11c.md` (22:41),
`review-G3-21.md` (22:42), `review-G3-20.md` (22:43), `review-G3-04d.md` (22:50). Reviews before
15:09 that the census also omits: `review-G3-19.md` (14:08), `review-G3-09c.md` (14:14),
`review-G3-01e-fix.md` (13:59). None of `G3-10i`, `G3-19b` has a review file at all, so the
"no review" cells there are correct.

## 5. What I could not check

- **`RESET_STATUS2.md`'s internal consistency as generated** — I read it and `reset_status2.py`
  was not executed; a `--check` run now would exercise the script's own scan set (53), but whether
  the script *can* see the three new files is a script question the card already answers (it
  excludes only `G3-21.md`/`G3-21b.md`), so the gap is a generation-time one, not a filter bug.
- **Relevance of `G3-04e1` to R-4/R-6** — I read only its STATUS and opening lines; whether its
  6,934 material uniform records bear on "an exact colour conversion exists" is a judgement.
- **`G3-07b1`/`G3-07b2`'s own correctness** — no reviews exist for them; I did not re-derive their
  `.pdata`/float4 claims, only their dates, topics and STATUS lines.
- **The `3556`/`439` provenance** — they may come from a JSON or a doc the card does not name;
  they are not in the four files the sentence cites, which is the test the card sets for itself.

## 6. Commands that carry the evidence

```
$ ls -t G3-*.md | head -5
G3-04e1.md       2026-11-04T22:38
G3-07b1.md       2026-11-04T21:36
G3-07b2.md       2026-11-04T21:04
G3-21b.md        2026-11-04T15:09
G3-19b.md        2026-11-04T12:24
$ ls G3-*.md | wc -l
58

$ grep -c "G3-07b1\|G3-07b2\|G3-04e1" Research/RESET_STATUS2.md
0

$ for c in 04d 20 11c 21; do grep -m1 -i VERDICT review-G3-$c.md; done
VERDICT: **needs rework**          (review-G3-04d.md, 22:50)
VERDICT: **needs rework**          (review-G3-20.md, 22:43)
VERDICT: needs rework              (review-G3-11c.md, 22:41)
VERDICT: **needs rework**          (review-G3-21.md, 22:42)

$ grep -m1 -i -A3 VERDICT review-G3-01e-fix.md   (13:59)
## VERDICT
**The settlement's conclusion is right and its corrections are wrong.**

$ grep -n "3556\|439" G3-10d.md G3-10h.md G3-10i.md
(no matches)
$ grep -n "cinfos:\|fleet files" G3-10d.md
48: cinfos: 494; hulls with mass: 2011; fleet files: 50

$ grep -n "116/116\|4/4\|78 records\|0x01000010" G3-12d.md
9:  - `.ddsc` 116/116 **FULL**. The 84-byte tail region is exactly 7 slots of 12 bytes …
15: - `.pfxc` 4/4 **FULL**. There is no trailing blob …
118:  5  tail record size = absent level's mip size, offset = prefix sum, tag, zero remainder   116 of 116 files; 78 records

$ grep -n "RDEF" G3-04d.md
19: anywhere — 0 of 38,201 and 0 of 2,098.
67: .upk RDEF 0 of 38201, .bin RDEF 0 of 2098; chunk tags ISGN,OSGN,SHEX

$ grep -n "0 of the 29 referenced banks" G3-14.md
5: 0 of the 29 referenced banks are absent, and 10/10 of the banks called missing are present as
```
