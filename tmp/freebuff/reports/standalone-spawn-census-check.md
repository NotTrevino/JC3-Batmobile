# Standalone spawn plan - its entity names and counts against the two census files

Card: 8823-standalone-spawn-census-check. 2026-11-08.

Citation legend (paths relative to `tmp/freebuff/reports/`, where all three files live):

- **SEL** = `standalone-entity-spawn-check-plan.md`
- **FSE** = `fleet-sanity-entity.md`
- **EU36** = `entity-unexplained-36.md`

## Count

**22 items cited by SEL: 2 MATCHING, 0 DIFFERING, 20 ABSENT.**

Only **two** of the items are entity *names*, and both match the census exactly. The other twenty are
**file, byte or byte-string counts** — `.ee` sizes, `.toc` records, AAF file counts, stringlookup
hits, traffic selectors — and the census files do not record any of those quantities, so they are
**absent**, not differing. **Zero differences** were found, and the reason is structural rather than
lucky: SEL measures **`Builds/bm-RC4`** (`SEL:36`) while both census files measure **`Builds/bm-RC2`**
(`FSE:1`, `EU36:1`), so no count in the plan and no count in the census measures the same object at
the same revision. The plan therefore **cannot be sanity-checked against the census for counts**, only
for names — which is what this page records rather than inventing agreements or conflicts.

One trap worth naming up front: SEL says "**9** named by the `.epe` — 2 private, 7 shipped, 0
dangling" (`SEL:64`) and FSE reports `SWeaponPoint` going **0 → 9** (`FSE:43`, `FSE:50`). The number
9 appears on both sides but is **not the same quantity** (graph function pointers vs weapon-point
objects, and different builds). It is marked ABSENT below, not MATCHING.

## 1. Entity names cited by SEL

| # | item | SEL says (line) | FSE (line) | EU36 (line) | status |
|---|---|---|---|---|---|
| 1 | entity leaf `v0300_car_kensington_sportsmuscle_debug` | `SEL:36` "leaf `v0300_car_kensington_sportsmuscle_debug`"; also `SEL:42` (the `.ee` path), `SEL:46` (spawn-record bytes), `SEL:50` (icon `.ddsc`), `SEL:68` (hash input) | `FSE:17` `..._debug.epe` as the built graph | `EU36:12` "take the unused vanilla `_debug` leaf" | **MATCHING** |
| 2 | the inner `.epe` keeps the **civilian** name `v0300_car_kensington_sportsmuscle_civilian_01.epe` while the entity leaf is `_debug` | `SEL:44` "the file keeps the **civilian** leaf name while the entity leaf is `_debug`" | `FSE:57-59` "its base is `bm-009` (the civilian variant's graph) … the build renamed the civilian graph to the debug leaf (B-13b)" | `EU36:11` "`:77` (civilian leaf)" | **MATCHING** |

Both names are confirmed, including the subtle one (the plan's inner/outer name split is exactly what
both census files describe). This is the plan's strongest support: the graph really is the civilian
graph carrying the `_debug` leaf, as `SEL:44` says.

## 2. Counts cited by SEL, against the census

Every row: SEL's number, then what the census records for that quantity. "Absent" = the census does
not record that quantity at all (not that it disagrees).

| # | quantity | SEL says (line) | FSE / EU36 record it? | status |
|---|---|---|---|---|
| 3 | donor `.ee` inner file count | **604** (`SEL:23`) | no — FSE records the original's `.epe` *size* `109,510 B` (`FSE:16`), never an inner-file count | **ABSENT** |
| 4 | index leaves carrying a registry record | **251 / 922** (`SEL:28`) | no | **ABSENT** |
| 5 | spawn leaves referenced by path with no registry record | **101 of 196** (`SEL:28`) | no | **ABSENT** |
| 6 | shipped mod's `.ee` / `.toc` counts | **20 `.ee`, 0 `.toc`** (`SEL:29`) | no | **ABSENT** |
| 7 | donor `.toc` records vs SARC entries | **506 vs 604** (`SEL:29`, restated `SEL:70`) | no | **ABSENT** |
| 8 | AAF file count in bm-RC4 | **696** (`SEL:37`) | no — FSE counts `<object>` elements, not AAF files (`FSE:30`) | **ABSENT** |
| 9 | `.toc` records in bm-RC4 | **714**, 225 changed vs vanilla (`SEL:37`, `SEL:43`) | no | **ABSENT** |
| 10 | built `.ee` size | **11,225,533 B** (`SEL:42`, `SEL:62`) | no — FSE:16's `5,539,360 B` is the *bundle* the original came from, not this file | **ABSENT** |
| 11 | built `.epe` size | **9,025 XML lines** (`SEL:44`) | partial — FSE records the same graph as **467 `<object>` elements** (`FSE:30`, `FSE:95`), a different unit; neither confirms 9,025 | **ABSENT** |
| 12 | private tune/module copies | **7** (`SEL:45`), "2 private, 7 shipped" (`SEL:64`) | no | **ABSENT** |
| 13 | `batmobile`-path AAF files / `@files.xml` rows | **111 / 111** (`SEL:45`, `SEL:66`) | no | **ABSENT** |
| 14 | `spawn_vehicle_defs.bin` size | **27,785 B** (`SEL:46`) | no | **ABSENT** |
| 15 | `item.onlinec` size; leaf hash hits | **77,569 B**; `0x60A5E7A4` **3 LE**, 0 BE (`SEL:47`, `SEL:68`) | no | **ABSENT** |
| 16 | `task.onlinec` size; `batmobile` hits | **168,174 B**; **0** (`SEL:48`) | no | **ABSENT** |
| 17 | `online.stringlookup` size; `BATMOBILE` strings | **1,746,322 B**; **22** (`SEL:49`) | no | **ABSENT** |
| 18 | graph pointer census | **9 named, 2 private, 7 shipped, 0 dangling** (`SEL:64`) | numerically 9 appears (`FSE:43` `SWeaponPoint` 0 → 9, `FSE:50` "9 `SWeaponPoint`") but a **different quantity** and build | **ABSENT** (not a match — see the trap above) |
| 19 | traffic selectors matched by the spawn record's tags | **0 of 41** (`SEL:67`, `SEL:79`) | no | **ABSENT** |
| 20 | AAF diff result | **120 differ, 120 planned, 0 unplanned** (`SEL:71`) | no — FSE reports **87 differences, 51 tagged, 36 UNEXPLAINED** (`FSE:1`) for bm-RC2, a different build **and** a different measurement (whole-tree file diff vs one `.epe` object diff) | **ABSENT** |
| 21 | weapon/tune re-read check | **3/3 edits, 2/2 tunes** (`SEL:65`) | no | **ABSENT** |
| 22 | bm-RC4 receipt state | **`complete: false`, `installed: false`, `not_deployed: true`** (`SEL:36-37`) | no | **ABSENT** |

## 3. The reverse direction: census counts SEL never cites

For completeness, because "check the counts" runs both ways. These are the entity counts the census
files actually own, and **none appears anywhere in SEL** — the plan never cites an entity-object
census at all, which is the real finding of this audit.

| census count | FSE line | EU36 line | in SEL? |
|---|---|---|---|
| `<object>` elements **450 → 467** (+17) | `FSE:30`, `FSE:34`, `FSE:94-95` | `EU36:20`, `EU36:68` | **absent** |
| distinct classes **43 → 46** (+3) | `FSE:32` | — | **absent** |
| `CPartProp` **40 → 6** (**-34**) | `FSE:38`, `FSE:52` | `EU36:11`, `EU36:36` | **absent** |
| **51** additions (47 objects + 4 `SEffects` copies) | `FSE:49` | `EU36:68` | **absent** |
| **36 UNEXPLAINED** (34 + rename + palette) | `FSE:1`, `FSE:108` | `EU36:1`, `EU36:68` | **absent** |
| **6 kept props** (body 0, wheels 11/12/26/27, `taillight_r_l` 8) | `FSE:57` ("`cpartprop_existing: 6`") | `EU36:45` | **absent** |
| **61-part** module index space 0..60 | — | `EU36:46-48` | **absent** |

Census-internal coherence, noted because it is the one thing that *can* be verified here: `40 - 34 =
6` (`FSE:38`) and `450 - 34 + 47 + 4 + 1 = 467` (`FSE:34`), and EU36's six kept props (`EU36:45`)
are exactly the six FSE counts (`FSE:38`). The two census files agree with each other; neither
overlaps SEL's numbers.

## 4. What this means

1. **Names: verified.** The leaf and the inner civilian `.epe` name are exactly as the census records
   them, including the inner/outer split (`SEL:44` vs `FSE:57-59`).
2. **Counts: not verifiable from these two files.** The plan's numbers are all file-, byte- or
   byte-string-scale, and the census is object-scale on a different build (`bm-RC4` vs `bm-RC2`). The
   audit cannot promote any of them to "matching", and none needs demoting to "differing".
3. **The gap that matters.** SEL plans the standalone spawn off a receipt and a spawn record, and
   never checks the **entity graph contents** — the very thing the census says is wrong in bm-RC2
   (`34 of 40 CPartProp` dropped, `FSE:1`). If bm-RC4 inherits that base, the plan's "**which it
   lacks: nothing**" (`SEL:54`) is scoped to *on-disk items*, not to graph parity, and the census
   deviation is outside its claim. That is not a contradiction of SEL; it is a blind spot SEL does not
   claim to cover, and it is the one census finding a spawn check should probably read.

## 5. Checks run

| check | result |
|---|---|
| SEL items extracted | 22 (2 names, 20 counts), each with a line citation |
| names found in both census files | 2 of 2, `SEL:36`/`SEL:44` against `FSE:17`/`FSE:57-59` and `EU36:11-12` |
| counts found in either census file | 0 of 20 |
| differing counts | **0** — no SEL count shares a unit and build with a census count |
| census counts absent from SEL | 7 of 7 checked |
| census-internal arithmetic | closes: `450-34+47+4+1=467` (`FSE:34`), `40-34=6` (`FSE:38`), 6 kept props (`EU36:45`) |
| game launched / anything built | **no** — files read only; nothing written outside this page |

## 6. UNKNOWNs

1. **bm-RC4's graph object count.** Neither census file covers bm-RC4, so whether the 34 `CPartProp`
   are still missing there is UNKNOWN. Settle with `v_entity_diff.py` pointed at
   `Builds/bm-RC4/aaf` (the tool already exists, `FSE:83`).
2. **The plan's `604` inner files** cannot be cross-checked because no census records SARC entry
   counts for the donor. Settle by `ConvertProperty`/AAF listing of the donor `.ee` (`SEL:23` names it).
3. **Whether the 9 graph pointers (`SEL:64`) relate to the 9 `SWeaponPoint` objects (`FSE:43`).** They
   are different quantities as far as either file says; no file joins them.
