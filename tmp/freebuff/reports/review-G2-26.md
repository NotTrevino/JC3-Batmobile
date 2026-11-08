# Review — G2-26 · Rebel Drop data (RD-1 read half)

Reviewer: independent (did not write the card). Read-only pass: `GRAB_BACKLOG.md`, `MODLOG.md`,
`Research/` and `Tools/` were only read; nothing outside this file was written, no game launched,
no git. The game blobs under `E:/Modding/_JC3grab/rebeldrop/` and the mod's own `profile/*.onlinec`
under `Research/1456340180_Rebel-Drop-Mod-V5.3/` were read only.

Scope: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G2-26 card (§7, line 740) and its §12 row (line 1309);
`MODLOG.md` §"G2-26 · Rebel Drop data (RD-1 read half) — done" (line 10359);
`Research/JC3Grab/REBELDROP.md` (334 lines), `Research/JC3Grab/REBELDROP.json`,
`Tools/scripts/jc3rebeldrop.py` (1,026 lines).

## VERDICT

**Needs rework** — one structural error, everything else is minor.

The counts that the card leans on are right: I re-derived 196 items / 185 resolving to an `.ee` /
80 `Name == hash(UIImagePath)` / 963 entity paths, the recipe hash `443190071`, and the five
entities the Plus build ships (all five `.ee` files are present in the mod). The
`Item.Name = hash_jenkins(entity leaf)` binding is well evidenced (80/80 vanilla, 45/45 mod-added
resolving) and the doc is honest about the string hashes.

But the base-game and mod tables are decoded with the **patch's** 26-member `Item` schema, and those
files use the **base's** 25-member layout. The five int fields at offsets 8–24 are one member
earlier in the base layout, so the patch-schema read mislabels them by one slot. I proved it at
byte level: for all 196 matched items the base record's ints at 8..32 equal the patch record's ints
at 12..36, and the mod's 45 added records read `(1,0,0,1,0)`/`(2,0,0,1,0)`/`(0,0,0,1,0)` at
8..24 — ordinary vanilla `Type` 1/2/0 with `Rewardable` 1 — not the "all `Type` 0, `DlcId` 1,
`Consumable` 1, `Rewardable` 0" the doc reports. That artefact propagates into the card's own
deliverable: the §6 claim that the mod's new entries "rely on `Type` 0 / `UIType` 3 alone", the §7
"mirrored pair" note, and the §7 step-5 instruction to "use `Type` 0 (`UIType` 3)". The identity
fields (`Name`/`BaseName` at 0/4, `UIImagePath`/`UIVideoPath` at 88/96), `UIType` 60, `UIFlag` 64,
`UIDisplayOrder` 68 and `RebelDropTimer` 52 are unaffected, so the recipe's 22 donor-derived
values and the hash stand — the serialisation guidance around them does not.

## Check output (verbatim)

Command run from `E:/Modding/JC3-Batmobile`:

```
$ python Tools/scripts/jc3rebeldrop.py --check
PASS: 196 vanilla items / 591 tasks / 80 vehicle-bound / 185 resolved to .ee, 0 hash mismatches, 39+45+45 items added by the 3 mod variants, recipe hash 443190071 for v0300_car_kensington_sportsmuscle_batmobile
```

Exit status `0`. Identical to the block pasted at `MODLOG.md:10409`–`10411`.

Out paths — all present:

| path | state |
|---|---|
| `Research/JC3Grab/REBELDROP.md` (card's declared Out) | present, 334 lines, §1–§9 |
| `Research/JC3Grab/REBELDROP.json` | present: `totals`, `sources`, `variants`, `schema`, `vanilla`, `mod_added`, `recipe`, `digest` |
| `Tools/scripts/jc3rebeldrop.py` | present, `--write`/`--check`/`dump`; `invariants()` at line 868 |
| `Research/JC3Grab/README.md` section + Files row | present |
| `GRAB_BACKLOG.md` §12 row `G2-26 \| done \| …` | present, line 1309 |
| `MODLOG.md` §"G2-26 … — done" | present, line 10359 |

## Issues

### 1. (R4, structural) Base and mod tables decoded with the patch schema — the affected fields are misread by one slot, and the card's deliverable inherits it

Files/lines: `Research/JC3Grab/REBELDROP.md:32` (§1), `:155`–`:157` (§5), `:177`–`:179` and `:193`
(§6), `:287`–`:288` (§7 note), `:255`–`:283` (§7 mod-pattern table), `:248`–`:249` (§7 step 5);
`Tools/scripts/jc3rebeldrop.py:105`–`125` (`borrow`), `:127`–`160` (`item_rows`).

What the two type tables actually say (dumped from the extracted blobs):

| field | base `Item` (25 members) | patch `Item` (26 members) |
|---|---|---|
| `Name` / `BaseName` | 0 / 4 | 0 / 4 |
| `DlcId` | — | 8 |
| `Type` | 8 | 12 |
| `Purchasable` | 12 | 16 |
| `Consumable` | 16 | 20 |
| `Rewardable` | 20 | 24 |
| `Collectable` | 24 | 28 |
| `Feats` … `UIImagePath` … `UIPar4` | 32 … 88 … 120 | 32 … 88 … 120 |

So (a) there is **no swap of names** — the members are in the same order in both tables; (b) the
"4 bytes short" statement at `:32` is true only for the five-int run 8–24: `Feats` (32) onward sits
at identical offsets in both tables, including the `UIImagePath` pointer at 88 that the doc uses to
prove the 128 B stride. Reading the base file with the patch schema therefore labels base's `Type`
as `DlcId`, base's `Purchasable` as `Type`, base's `Consumable` as `Purchasable`, base's
`Rewardable` as `Consumable`, base's `Collectable` as `Rewardable`.

Raw evidence (independent of `jc3rebeldrop.py`, `jc3adf` used only to find the array):

* matched by `Name` across all 196 items, **196/196** base records satisfy `base[8:32] ==
  patch[12:36]` — the same values, one member earlier. 97 of them also differ later (real
  content differences), so the two files are not simply copies.
* that one fact predicts the doc's `--check` diff exactly: patch-read base gives
  `Consumable` 196, `Rewardable` 196, `DlcId` 106 (`=80 Type 1 + 26 Type 2`), `Type` 106 —
  i.e. `:155`–`:157` ("base and patch differ on every item in the `Consumable`/`Rewardable`
  pair") is measuring the layout shift, not a difference in content. The base and patch items
  agree on those five fields when each is read with its own table.
* the mod's files declare `own_types: 0` and root `2044610734` (`0x79DE48AE`, the base root —
  `REBELDROP.json` `variants[*].item_meta`), so the same base layout applies to them. Reading the
  mod's 45 added records raw at 8..24 gives **`(1,0,0,1,0)` ×27, `(2,0,0,1,0)` ×9,
  `(0,0,0,1,0)` ×9** = `Type` 1/2/0, `Purchasable` 0, `Consumable` 0, `Rewardable` 1,
  `Collectable` 0. The doc's "all with `Type` 0, `DlcId` 1, `Consumable` 1, `Rewardable` 0"
  (`:177`–`:179`, and the mod-pattern table at `:260`–`:283`) is the patch-schema view of those
  same bytes.

Consequences that need fixing, in order of weight:

1. `:193` — "the mod's new entries rely on `Type` 0 / `UIType` 3 alone … Whether `Type` 0 is what
   makes an item available without a task is an inference". The evidence for `Type` 0 does not
   exist under the base layout (the added items carry 0/1/2), so this inference is unsupported and
   should go, or be restated as UNKNOWN with the layout question.
2. `:248`–`:249` and `:287`–`:288` — the recipe's step 5 alternative ("leave it out and use `Type` 0
   (`UIType` 3)") and the "mirrored pair" note. The pair is not mirrored; the whole five-int run
   moves. A builder following the note writes the wrong slots.
3. `:32` and `:155`–`:157` — the §1 sentence and the base-vs-patch diff are stated as file facts
   and are reader artefacts.
4. `invariants()` (`jc3rebeldrop.py:868`–`940`) pins the mod pattern for `UIType`, `RebelDropTimer`,
   `UIImagePath` and `BaseName`, but **not** `Type` — which is exactly the field the doc
   generalises from, so `--check` cannot catch this. Pin the layout instead: assert that each
   file is decoded with the member list its own type table declares (base 25, patch 26, mod = the
   base layout via root `0x79DE48AE`).

What is **not** affected and should not be redone: `Name`/`BaseName`/`UIImagePath`/`UIVideoPath`,
`UIType`, `UIFlag`, `UIDisplayOrder`, `RebelDropTimer`, `MaxInventory`, `Region`, `Feats`, the
`UIPar*` floats, `DlcId`-independent counts (`196`/`591`/`80`/`185`/`229`), the task reward census,
and every donor value in the recipe's 22 non-identity rows (they come from the patch layer, which
*is* the 26-member layout). Which layout the engine applies to a type-table-less table is not
decidable from these files (the mod works, and it ships the base root) — that belongs in §8 as
UNKNOWN, not in a footnote that asserts the answer.

### 2. (data) The task `Type` histogram is truncated to 10 of 14 types — `Research/JC3Grab/REBELDROP.md:115`

The doc lists `2 x132, 3 x112, 4 x29, 5 x3, 6 x1, 11 x49, 12 x30, 14 x11, 16 x27, 19 x47` and calls
it "Task `Type` histogram". That is 441 of 591 tasks; `REBELDROP.json` `totals.vanilla_task_types`
has 14 entries, and the four omitted are the second-, third- and fourth-largest buckets:
`20 x71`, `22 x54`, `21 x23`, `100 x2`. Cause: `jc3rebeldrop.py:633`–`634` renders
`list(tot["vanilla_task_types"].items())[:10]` with no ellipsis. Reads as complete; is not.

### 3. (data) "18 of the mod's added items reuse one of a few existing `UIName` hashes" is not reproducible — `Research/JC3Grab/REBELDROP.md:251`

Typed literal in the renderer, and no invariant covers it. From `REBELDROP.json` `mod_added`
(V5.3 Plus, 45 entries): **27** added items have `UIName != Name`; among those, **25** share their
`UIName` with another added item (two hashes cover 15 and 10 items, plus two singletons) and **0**
reuse a `UIName` that appears in the vanilla table. So the sentence's "18" matches none of those
readings. Either derive it (and say which definition) or drop the number.

### 4. (recipe) The `UIDisplayOrder` row contradicts itself — `Research/JC3Grab/REBELDROP.md:228`

`| UIDisplayOrder | 3 | pick a free slot after the donor's |`. The value comes from the donor
record (`recipe.fields = dict(donor)`, `jc3rebeldrop.py:421`–`430`), and the donor's own
`UIDisplayOrder` is 3 — so "after the donor's" and "3" are mutually exclusive, and following the
table puts two menu entries at the same slot. This is the one row of the card's Done deliverable
that cannot be executed as written. Either the value should be a free slot (e.g. one past the
donor's) or the "why" should say the value is the donor's and a free slot is needed. Worth checking
the mod's own range too: its added items use 13..50 (`recipe.mod_added_orders`), i.e. the mod does
not reuse a donor slot.

### 5. (R11) Typed literals in generated prose, several of which I could verify only by hand

`"78 distinct sets over 80 vehicles"` (`:521`/doc §2 `UIPar0` row). Verified: over the 80 `Type` 1
items there are exactly 78 distinct `UIPar0..4` tuples — correct, but it comes from a literal in
the `FIELD_NOTE` dict, not from the build. The same holds for `"the five entities"` list, `"18"`
(issue 3), `"45/45"`, `"vanilla drop items never do this"` and the `UIDisplayOrder 13..50` range
(the last is derived). None is asserted, so none is protected by `--check`.

### 6. (presentation) The `Sources` table's counts column holds words — `Research/JC3Grab/REBELDROP.md:145`–`:153`

Header `items / tasks`, rows `item` / `task`. The counts exist in the JSON (`196`, `232`, `240`,
`591`). Cosmetic, but it is the table a later card will read for file provenance.

### Note (not a defect): the Done criterion and what `--check` proves

Card Done: "a field-by-field recipe for adding an entry named 'Batmobile' that spawns a given
`.ee`". §7 is that recipe: 26 fields, each with a value and a reason, plus the hash and the array
layout. `--check` re-derives the hash, the identity-field swap, the donor item's presence, the
counts and the mod-added pattern (minus `Type`), and compares both files byte for byte. It cannot
check the two prose instructions that are wrong (issues 1 and 4) — which is why a green check is
compatible with a recipe that does not work as written.

## Spot-checks

| # | value in `REBELDROP.md` | where verified |
|---|---|---|
| 1 | "196 vanilla items and 591 vanilla tasks", "80 of them are vehicle drops", "185 of the 196 name hashes resolve to an `.ee` path in `INDEX.jsonl` (963 entity paths)" (lines 9–14, 155) | Recomputed from `REBELDROP.json` + `INDEX.jsonl` with the project's `hash_jenkins`: 196 items, 185 resolve, 80 items satisfy `Name == hash(UIImagePath)`, 963 `.ee` paths. Matches `totals`. |
| 2 | Recipe: `hash_jenkins("v0300_car_kensington_sportsmuscle_batmobile")` = **443190071** = `0x1A6A8B37`; the `.ee` is not in the shipped index (lines 202–207) | Re-derived: `443190071`; `recipe.existing_ee_named_that = false`; the vanilla donor's `UIImagePath` is `…_civilian_01` and its `Name` 3535039305. |
| 3 | "the five entities the Plus builds ship" — `v1704_boat_na_lightpatrol_civic_police_01`, `w141_rpg_uvk_13_mm110`, `sponge`, `pinata`, `pinata_stick` (lines 131–134, 178) | All five ship as `.ee` in `Research/1456340180_Rebel-Drop-Mod-V5.3/V5.3 Plus/editor/entities/…` (found on disk); all 45 added items resolve to an `.ee` (`mod_added` `_ee`). |
| 4 (bonus) | `Item` is 26 fields / 128 B; the base file's own table has 25 members without `DlcId`; the mod tables carry no type table; the mod root is `0x79DE48AE` (lines 20–36, 155) | Dumped both type tables and all four files: base 25 members (no `DlcId`), patch 26, mod `own_types: 0`, roots `0x79DE48AE` (base, mod) / `0x921AF417` (patch). Also the source of issue 1. |
| 5 (bonus) | "Task Type histogram" (line 115) | `totals.vanilla_task_types` has 14 buckets summing to 591; the doc prints 10 summing to 441. |

## Tamper test

Not re-run (journaled at `MODLOG.md:10422`–`10426`: `recipe.name_hash` and
`string_pointer_failures` tampered in the JSON, one digit in the md → `--check` exit 1 in all three
cases, restored by `--write`). Re-running would mean writing `Research/`, which this review may not
do. The check path is consistent with the journal: it compares the JSON object and the rendered md
and exits 1 on either.

## Limits of this review

I used `jc3adf` (the project's ADF reader) only to find the record array; the field values in
issue 1 come from `struct.unpack_from` on the raw records. I did not re-implement `hash_jenkins`;
the spot-checks use the same function the script uses, so the 80/185/443190071 figures are
arithmetically independent but not hash-implementation-independent. I did not attempt to determine
which layout the engine uses for the mod's type-table-less files — that is the UNKNOWN issue 1 asks
the doc to record.
