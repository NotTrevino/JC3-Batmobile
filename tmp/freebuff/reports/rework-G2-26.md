# Rework — G2-26 · Rebel Drop data (RD-1 read half)

**STATUS: DONE — 6/6 review issues CONFIRMED, 0 rejected, all fixed in the generator; `--check` PASS.**

Review read: `tmp/freebuff/reports/review-G2-26.md` (verdict `needs rework`, 6 issues + 1 note).
Each issue was re-verified against the raw bytes and the re-run script before any edit. One of the
review's own figures (the 27/9/9 split of the mod's added records) is wrong and is corrected below;
the finding it belongs to is still confirmed.

Intended-change entry: `MODLOG.md` §"G2-26 rework — intended change (2026-10-29)" (line ~14781).
Done entry: `MODLOG.md` §"G2-26 rework — done (2026-10-29)".

## Per-issue verdicts

### 1. Base and mod tables decoded with the patch schema — **CONFIRMED** (review's 27/9/9 sub-figure corrected)

Evidence, re-derived by dumping the two type tables and reading records with `struct.unpack_from`
(the project's `jc3adf` only to locate the arrays):

| field | base `Item` (25) | patch `Item` (26) |
|---|---|---|
| `Name` / `BaseName` | 0 / 4 | 0 / 4 |
| `DlcId` | — | 8 |
| `Type` / `Purchasable` / `Consumable` / `Rewardable` / `Collectable` | 8 / 12 / 16 / 20 / 24 | 12 / 16 / 20 / 24 / 28 |
| `Feats` … `UIImagePath` … `UIPar4` | 32 … 88 … 120 | 32 … 88 … 120 |

- base file: `own_types 5`, root `0x79DE48AE`; patch: root `0x921AF417`; mod `V5.3 Plus`:
  `own_types 0`, root `0x79DE48AE` (= base root) → the base layout is the one the mod declares.
- base read with base layout vs patch with patch layout: **196/196 matched, 0 changed** on the 25
  shared members; `DlcId` = 0 on all 196. The old "base and patch differ on every item" was the
  one-member shift.
- mod's 45 added records at 8..24: `(1,0,0,1,0)` — **45/45**. The review's `27/9/9` does not
  reproduce under either layout (all 240 records under the patch layout read `(0,0,1,0,0)` at
  12..28, i.e. one uniform value); its `196/196 base[8:32] == patch[12:36]` check is right, so the
  finding stands, the split is an artefact of that pass. Corrected value is what the fix uses.
- `--check` also shows the old field pin `items_changed != 195` was stale: the mod rewrites **162**
  existing items, both against the patch and against the base layer (identical now).

Fix (generator): `lend()` assigns each type-table-less file the layout of the vanilla layer whose
root hash it declares; `items_of`/`items_of`-path call `item_rows` with that file's own member list;
the base/patch diff compares only the shared members and records `only_patch = ["DlcId"]`;
`schema.ItemBase` is written to the JSON; `invariants()` now asserts base `own`/25 members/patch 26,
each mod `lent` with 25 members and root `0x79DE48AE`, `common_fields 25`, `only_patch ["DlcId"]`,
`five_int_equal == matched`, and added records are base-layout `Type` 1 with no `DlcId`. Which
layout the *engine* applies to a type-table-less table stays **UNKNOWN** in §8.

### 2. Task `Type` histogram truncated — **CONFIRMED**

`REBELDROP.json` `totals.vanilla_task_types` has 14 buckets (2×132, 3×112, 4×29, 5×3, 6×1, 11×49,
12×30, 14×11, 16×27, 19×47, 20×71, 21×23, 22×54, 100×2) summing to 591; the renderer printed
`list(...)[:10]` = 441 with no ellipsis. Fix: render every bucket; invariant asserts 14 buckets and
that they sum to `vanilla_tasks`.

### 3. "18 of the mod's added items reuse a `UIName`" — **CONFIRMED**

Measured over V5.3 Plus's 45 additions: **27** have `UIName != Name`; **27** share their `UIName`
with another added item (two groups: 16 and 11); **0** reuse a vanilla `UIName`. "18" matches no
reading. Fix: the sentence is now derived (`recipe.mod_added_uiname`) and states its definition and
the group sizes; invariant unchanged (no literal remains).

### 4. `UIDisplayOrder` row contradicts itself — **CONFIRMED**

Donor record carries `UIDisplayOrder` 3 (it is `dict(donor)`), vanilla uses 0..11, the mod's
additions use 13..50. Fix: `recipe.fields.UIDisplayOrder` is now a derived **free slot, 12**
(`max(vanilla_orders) + 1`), with `recipe.donor_order = 3` named in the why column; invariants
assert the value is not already in `vanilla_orders` and that `fields.UIDisplayOrder == free_order`.

### 5. Typed literals in generated prose — **CONFIRMED**

Every literal the review named is now derived: "78 distinct sets" → `totals.vehicle_ui_tuples`
(78); "the five entities" → `recipe.mod_named_items` (11 of 45 added entries hash to a mod-shipped
`.ee`); "18" → `mod_added_uiname`; "45/45" → `mod_added_base_eq_name` (45/45); "`UIDisplayOrder`
13..50" → `recipe.mod_added_orders`; `FIELD_NOTE` is a template filled from
`totals.vanilla_vehicle_values`.

The same pass exposed three values that were not just underived but **wrong**, and they are fixed
from the data: `UIFlag` is **1..11** over the 80 vehicles (not 1/5/6/7/9/10); `RebelDropTimer` is
**60/600/900/1200/1500/1800/2400/2700** (not five values); "every `BaseName` is shared by two items"
is false — group sizes are 1×99, 2×29, 3×5, 4×3, 5×1, 7×1 (138 distinct values over 196 items).

Additional defect found while verifying (not in the review), fixed: "the 11 that do not resolve are
the non-vehicle items (no `UIImagePath`)" is unsupported — **87** items have an empty image path, and
only **11** fail to resolve; all 11 carry `UIType` 0, with an empty (7) or `placeholder` (4) image.
The doc now states that and leaves what they are UNKNOWN.

### 6. Sources table counts column holds words — **CONFIRMED**

Rows read `items` / `tasks`. Fix: the column now prints `s["objects"]` + noun (`196 items`,
`591 tasks`, `232 items`, …) and the layout each file was read with (own table 25/26 members, or
the lent base layout with its root).

### Note (Done criterion vs `--check`) — accepted, no change

The review's note is not a defect: the card's Done is the field-by-field recipe, and `--check`
cannot validate prose. The two prose instructions it named (issues 1 and 4) are now derived values,
so the gap is narrowed.

## Files changed

| file | change |
|---|---|
| `Tools/scripts/jc3rebeldrop.py` | per-file layout (`lend`, base 25 / patch 26 / mod = declared root); own-layout `item_rows`; shared-member base/patch diff + `only_patch`; `schema.ItemBase`; derived totals (`vanilla_orders`, `vanilla_vehicle_values`, `base_name_group_sizes`, `patch_dlc_zero`, unresolved census, `vehicle_ui_tuples`); recipe `free_order`/`donor_order`/`mod_added_base_eq_name`/`mod_named_items`/`mod_added_uiname`; `FIELD_NOTE` templates; §1/§4/§6/§7/§8/§9 rewritten; new layout/free-slot/census invariants; stale 195 → 162 |
| `Research/JC3Grab/REBELDROP.md`, `REBELDROP.json` | regenerated by `--write` only (362 md lines) |
| `Research/JC3Grab/README.md` | G2-26 section: removed "all four decoded with the patch schema", "`Type` 0", the "mirrored pair" and "the other 11 are non-vehicle unlocks" |
| `GRAB_BACKLOG.md` | §12 `G2-26` line only (25/26-member layouts, base = patch, `Type` 1, the 11 unresolved, layout UNKNOWN) |
| `MODLOG.md` | intended-change + done entries (append-only) |

No translation rows changed → `t_rows.py check` / `status_audit.py --check` not re-run.

## Check output (verbatim)

```
$ python Tools/scripts/jc3rebeldrop.py --check
PASS: 196 vanilla items / 591 tasks / 80 vehicle-bound / 185 resolved to .ee, 0 hash mismatches, 39+45+45 items added by the 3 mod variants, recipe hash 443190071 for v0300_car_kensington_sportsmuscle_batmobile
```

Exit status 0.

```
$ python Tools/scripts/jc3rebeldrop.py --write
REBELDROP.json/REBELDROP.md: 196 vanilla items, 591 tasks, 80 vehicle-bound, 3 mod variants, 362 md lines
```

Tamper test (then restored by `--write`):

```
# recipe.name_hash += 1 in REBELDROP.json
FAIL: REBELDROP.json stale                       (exit 1)
# one digit in REBELDROP.md (`Type` 1 -> 2)
FAIL: md differs: @@ -188,3 +188,3 @@ ...        (exit 1)
# restored
PASS: 196 vanilla items / 591 tasks / ...        (exit 0)
```

## Spot-checks of the corrected values

| value | where verified |
|---|---|
| base `Item` 25 members / `Type` at 8 / no `DlcId`; patch 26 / `DlcId` 8 | `jc3adf` type tables of `archives_win64/game2` and `patch_win64/game4` `profile/item.onlinec`, dumped as (name, offset, type) |
| base vs patch: 196 matched, 0 changed, `DlcId` 0 on 196 | raw `<I` reads at the declared offsets of both files |
| mod added records `(1,0,0,1,0)` 45/45 | `struct.unpack_from("<5I", mod_blob, start + i*128 + 8)` over the 45 names not in the base table (`start` from the array offset, stride proved by the string pointers) |
| task histogram 14 buckets = 591 | `REBELDROP.json` `totals.vanilla_task_types`, sum checked |
| recipe slot 12 free; donor 3; mod 13..50 | `totals.vanilla_orders` 0..11; `recipe.donor_order` 3; `recipe.mod_added_orders` |
| `UIName`: 27 differ / 27 shared (16+11) / 0 vanilla reuse | `recipe.mod_added_uiname` recomputed from the 45 added records |
