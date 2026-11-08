# Rebel Drop - `profile/item.onlinec` and `profile/task.onlinec`

G2-26. **A drop entry is an `Item` whose `Name` is the 32-bit Jenkins hash of an
entity leaf name**, and the game spawns the `.ee` that hash names. Every field the card
asks about is in the `Item` struct except the unlock, which lives in `task.onlinec` as a
task reward. There is no entity-path field and no price field anywhere in either table.

- 196 vanilla items and 591 vanilla tasks from
 2 archive layers (archives_win64/game2, patch_win64/game4; the
 patch layer is the effective one);
- 80 of them are vehicle drops, and
 185 of the 196 name hashes resolve to an
 `.ee` path in `INDEX.jsonl` (963 entity paths) - the
 11 that do not name a shipped `.ee` (§4);
- the mod's newest variant adds 45 items and changes
 162 of the vanilla ones; 229 of
 its 240 items resolve to an `.ee` path (the same
 11 stay unresolved).

## 1. What the two files are, and two reader facts

Both are bare ADF v4 files (`20 46 44 41 04 00 00 00`): one root instance, an
`A[Item]` / `A[Task]` array, and string data after it. Two facts had to be
established before any value could be trusted, and `--check` re-derives both:

1. **Base and patch are two layouts of the same 25 fields; the mods use the base
   one.** The base game's own `profile/item.onlinec` declares five types and its
   `Item` has **25** members (`Type` at 8, no `DlcId`); the patch layer
   (`patch_win64/game4`, root `0x921af417`) has **26** (`DlcId` at 8, `Type` at
   12). Both arrays are 128 B per item and the content is the same: the 25 common
   fields agree on 196/196 matched
   items and `DlcId` is 0 on 196/196 records, so the patch adds the member and changes
   no value. The mod tables carry no type table and declare the **base** root
   `0x79de48ae`, so they are read with the base 25-member layout, not the
   patch's - the patch list names every int at 8..24 one slot late. Each file is read
   with the layout it declares (its own type table, or the vanilla layer whose root
   hash it carries), and §9 asserts that assignment. The 128 B stride is proved
   without the type table: the `UIImagePath` pointer at offset 88 resolves to a
   printable or empty NUL-terminated string for **every** record -
   196/196 base, 196/196 patch, 232/232 mod Regular v5.2, 240/240 mod V5.2 Plus, 240/240 mod V5.3 Plus (§9).
2. **`jc3adf.walk` reads a 4-byte `StringHash` as 8 bytes.** The type
   `StringHash_48C5294D_4` declares element `0x48C5294D`, which is not a known
   primitive, so the reader falls through to `<Q`. The low 32 bits are the true hash
   (the high half is whatever the next member holds - e.g. `Region` reads
   `2576980377600` = `600 << 32` because `RebelDropTimer` 600 follows it). Every hash
   in this doc is masked to 32 bits and checked against
   `struct.unpack_from("<I", ...)` at the declared member offset.

## 2. `Item` - the drop entry (26 members in the effective patch layout, 128 B)

The table is the patch layer's 26-member `Item`. The base layer and the three mod
tables carry the same list **without `DlcId`** (25 members); every other member keeps
the offset printed here (§1).

| field | type | size | offset | what the files prove |
|---|---|---:|---:|---|
| `Name` | StringHash_48c5294d_4 | 4 | 0 | hash of the entity leaf name - this is the spawn binding (§4) |
| `BaseName` | StringHash_48c5294d_4 | 4 | 4 | a different hash; it takes 138 distinct values over the 196 vanilla items, so it is a grouping key (what it names: UNKNOWN) |
| `DlcId` | int32 | 4 | 8 | 196/196 records carry 0; this member exists only in the patch layout (the base/mod 25-member layout has no `DlcId`) |
| `Type` | int32 | 4 | 12 | `1` on all 80 vanilla vehicle items and on the mod's 45 added entries; enum labels UNKNOWN |
| `Purchasable` | int32 | 4 | 16 | `0` on all 80 vanilla vehicle items; not a price (no price field exists) |
| `Consumable` | int32 | 4 | 20 | `0` on all 80 vanilla vehicle items and on the mod's added entries |
| `Rewardable` | int32 | 4 | 24 | `1` on all 80 vanilla vehicle items |
| `Collectable` | int32 | 4 | 28 | `0` on all 80 vanilla vehicle items |
| `Feats` | A[StringHash_48c5294d_4] | 8 | 32 | array of hashes, empty on the vehicle items |
| `Region` | StringHash_48c5294d_4 | 4 | 48 | `0` on all 80 vanilla vehicle items |
| `RebelDropTimer` | int32 | 4 | 52 | the only time-like number: 60/600/900/1200/1500/1800/2400/2700 on vanilla vehicles, 0 on the mod's added entries; unit UNKNOWN (consistent with seconds) |
| `MaxInventory` | int32 | 4 | 56 | `0` on all 80 vanilla vehicle items |
| `UIType` | int32 | 4 | 60 | `3` on all 80 vanilla vehicle items; enum labels UNKNOWN |
| `UIFlag` | int32 | 4 | 64 | 1..11 on vanilla vehicles; enum labels UNKNOWN |
| `UIDisplayOrder` | int32 | 4 | 68 | menu order; 1..11 on vanilla vehicles (0/1/2/3/4/5/6/7/8/9/10/11 over all items) |
| `UIName` | StringHash_48c5294d_4 | 4 | 72 | equal to `Name` on 80/80 vanilla vehicle items |
| `UIDescription` | StringHash_48c5294d_4 | 4 | 76 | localization key hash (string not in these files) |
| `UITypeDescription` | StringHash_48c5294d_4 | 4 | 80 | localization key hash, shared by items of one category |
| `UIFlagDescription` | StringHash_48c5294d_4 | 4 | 84 | localization key hash, one per `UIFlag` value |
| `UIImagePath` | string | 8 | 88 | string: the entity leaf name on vanilla vehicles, `placeholder` on the mod's new entries - cosmetic, not the binding |
| `UIVideoPath` | string | 8 | 96 | string: equal to `UIImagePath` on vanilla vehicles |
| `UIPar0` | float | 4 | 104 | float; one of five per-item numbers (the distinct-set count is in the text below); icon framing is the likely meaning and is UNKNOWN from the files |
| `UIPar1` | float | 4 | 108 | float; part of the same five-number set as `UIPar0` |
| `UIPar2` | float | 4 | 112 | float; part of the same five-number set as `UIPar0` |
| `UIPar3` | float | 4 | 116 | float; part of the same five-number set as `UIPar0` |
| `UIPar4` | float | 4 | 120 | float; part of the same five-number set as `UIPar0` |

Every value list in that table is measured over the 80
 vanilla vehicle drops (`--check` re-derives the counts). Their `UIImagePath` is a
 distinct leaf on 80/80,
 and the five `UIPar` numbers take 78 distinct values over the
 80. `BaseName` is not per-item: its
 138 distinct values group the
 196 items by size (1 x99, 2 x29, 3 x5, 4 x3, 5 x1, 7 x1), and `Name != BaseName` on
 80/80 vehicles.

**Cost: there is no cost field.** The only economic fields are the flags above; the
only time is `RebelDropTimer`. If the game charges anything for a drop it is not in
these files.

## 3. `Task` - where the unlock is

| field | type | size | offset | what the files prove |
|---|---|---:|---:|---|
| `Name` | StringHash_48c5294d_4 | 4 | 0 | task hash (string not in these files) |
| `TaskGroup` | StringHash_48c5294d_4 | 4 | 4 | task-group hash |
| `Type` | int32 | 4 | 8 | task type; the type histogram is in the text below, the enum labels are UNKNOWN |
| `ProvinceWeight` | int32 | 4 | 12 | weighting for province selection |
| `LiberationPercent` | int32 | 4 | 16 | liberation gate |
| `RepeatableRewardSemantics` | int32 | 4 | 20 | enum, UNKNOWN |
| `RepeatableReward` | Reward | 8 | 24 | a `Reward` handed out each repeat |
| `RewardThresholds` | A[RewardThreshold] | 8 | 56 | `RewardThreshold[]`: threshold -> `Reward` |
| `Prerequisites` | A[Prerequisite] | 8 | 72 | `Prerequisite[]`: name + reward index + tag |
| `HasChurch` | int32 | 4 | 88 | flag |
| `ShownOnMap` | int32 | 4 | 92 | flag |
| `UIName` | StringHash_48c5294d_4 | 4 | 96 | localization key hash |
| `UIDescription` | StringHash_48c5294d_4 | 4 | 100 | localization key hash |
| `UITip` | StringHash_48c5294d_4 | 4 | 104 | localization key hash |
| `UIOrderHint` | int32 | 4 | 108 | sort key |

`Reward` (`Skillpoints` int32, `Chaos` int32, `ItemRewardSemantics` int32,
`Items` `A[ItemReward]`) and `ItemReward` (`Item` hash, `Permanent`, `Duration`,
`Quantity`, `Delivery`) are the only place an item is granted; `Prerequisite` is
`Name` + `RewardIndex` + `Tag`. The vanilla tables carry
87 reward links, all with `Delivery` = 0
 (`0` x87), and 87 distinct items are handed out by
some task. Task `Type` histogram (14 buckets,
 591 tasks): 2 x132, 3 x112, 4 x29, 5 x3, 6 x1, 11 x49, 12 x30, 14 x11, 16 x27, 19 x47, 20 x71, 21 x23, 22 x54, 100 x2.

## 4. What the name hash names

`Item.Name` is the Jenkins hash (the archive-path function, `rbmhdr.hash_jenkins`)
of an **entity leaf name**, and that is the whole spawn binding:

- independent check on the vanilla vehicles: `Name == hash(UIImagePath)` for
 80/80 items whose
 `UIImagePath` is a vehicle leaf;
- `Name` resolves to an `.ee` path for 185/
196 vanilla items and 229/
240 items of the mod's newest variant, against the
 963 entity paths in `INDEX.jsonl`. The 11
 vanilla items that do not resolve carry `UIType` 0 and an empty (7) or `placeholder` (4) `UIImagePath`; what they are is UNKNOWN,
 and the mod keeps exactly those unresolved (`--check` asserts it);
- the mod proves the direction the other way: it ships 15 `.ee` files of
  its own, and 11 of its added entries hash to one of those
  leaves (`armored_transport_wreck`, `bus_wreck`, `oldcompact_wreck`, `pinata`, `pinata_stick`, `sponge`, `tank2_transport_wreck`, `tank_bus_wreck`, `tank_oldcompact_wreck`, `tank_wreck`, `technicaljeep_wreck`); the
 4 shipped `.ee` leaves that no added entry names are `tank_techinal_wreck`, `techinal2_oldcompact_wreck`, `v1704_boat_na_lightpatrol_civic_police_01`, `w141_rpg_uvk_13_mm110`.

So the `.ee` path is **not** stored: the game looks the entity up by the hash of its
leaf. Two entries cannot share a name hash, and the `.ee` must exist (or be shipped by
the mod) under the **leaf** the hash was computed from.

## 5. Sources

| source | file | bytes | sha1 | items / tasks | note |
|---|---|---:|---|---|---|
| vanilla `archives_win64/game2` | `profile/item.onlinec` | 52165 | `23348af9561c4aa6` | 196 items | own type table, 25 members; extracted to `_JC3grab\rebeldrop\` |
| vanilla `patch_win64/game4` | `profile/item.onlinec` | 52204 | `bcb146b55fbd07ce` | 196 items | own type table, 26 members; extracted to `_JC3grab\rebeldrop\` |
| vanilla `archives_win64/game2` | `profile/task.onlinec` | 167286 | `6d60288e1534b725` | 591 tasks | own type table; extracted to `_JC3grab\rebeldrop\` |
| vanilla `patch_win64/game4` | `profile/task.onlinec` | 167470 | `72a907016cbfd97f` | 591 tasks | own type table; extracted to `_JC3grab\rebeldrop\` |
| mod `Regular v5.2` | `profile/item.onlinec` | 60554 | `90034a11a7fd2816` | 232 items | base layout (archives_win64/game2 root 0x79de48ae) |
| mod `Regular v5.2` | `profile/task.onlinec` | 166233 | `261114afa4066ab6` | 591 tasks | base layout (archives_win64/game2 root 0xba99d54c) |
| mod `V5.2 Plus` | `profile/item.onlinec` | 62041 | `b9507408611dcf88` | 240 items | base layout (archives_win64/game2 root 0x79de48ae) |
| mod `V5.2 Plus` | `profile/task.onlinec` | 166480 | `a83b6af314987c81` | 591 tasks | base layout (archives_win64/game2 root 0xba99d54c) |
| mod `V5.3 Plus` | `profile/item.onlinec` | 62041 | `73a21a9f196a749d` | 240 items | base layout (archives_win64/game2 root 0x79de48ae) |
| mod `V5.3 Plus` | `profile/task.onlinec` | 166518 | `ca07af05f44de020` | 591 tasks | base layout (archives_win64/game2 root 0xba99d54c) |

Base game vs patch layer: 196 -> 196 items,
+0 / -0 items, and 0 items whose value
 changes in any of the 25 members the two layouts share
 (the five ints at 8..24 agree on 196/196 matched
 items). The patch adds one member, `DlcId` (0 on 196/196), and no other
 value differs. `--check` re-derives this diff.

## 6. How a new entry is added (mod vs vanilla)

**Two baselines, because the mod tables use the base layout.** Base and patch carry
the same content: the patch only adds `DlcId` (0 on 196/196), and every one of the
 25 shared members is equal on 196
 of 196 matched items. The mod tables declare the base root and are
read with the base 25-member layout, so their own edits are the diff against the base
layer; the patch column is shown for completeness.

| variant | items | added | removed | changed vs patch | changed vs base | fields it changes vs base (top) | tasks vs base |
|---|---:|---:|---:|---:|---:|---|---|
| `Regular v5.2` | 232 | 39 | 3 | 160 | 160 | `RebelDropTimer` 109, `UIDisplayOrder` 55, `UIImagePath` 50, `UIVideoPath` 50 | 0 / 0 |
| `V5.2 Plus` | 240 | 45 | 1 | 162 | 162 | `RebelDropTimer` 109, `UIDisplayOrder` 57, `UIImagePath` 52, `UIVideoPath` 52 | 0 / 0 |
| `V5.3 Plus` | 240 | 45 | 1 | 162 | 162 | `RebelDropTimer` 109, `UIDisplayOrder` 57, `UIImagePath` 52, `UIVideoPath` 52 | 0 / 0 |

What the newest variant actually does:

- **adds 45 items** at the end of the array, all with
  `Type` 1, `UIType` 3, `RebelDropTimer` 0,
  `UIImagePath` = `placeholder`, `BaseName` = `Name`
  (45/45; vanilla vehicle items:
 0/80)
  and an explicit `UIDisplayOrder` that continues the menu; their `Name` hashes name
  the `.ee` they spawn, and
  11 of the 45 hash to an `.ee`
  the mod ships itself (§4);
- **rewrites 162 existing items**
  (against the base layer); the fields it changes most are `RebelDropTimer` 109, `UIDisplayOrder` 57, `UIImagePath` 52, `UIVideoPath` 52, `UIDescription` 51. That is consistent with exposing entries that were already in the table but
 hidden from the menu - an inference: the files do not label the fields;
- **0 tasks added** and 0
  tasks changed by name, but the task file is **reordered**:
  566 of 591 positions hold a
  different task than vanilla (that is the whole byte difference). None of its added
  items appears in a task reward
  (0 of 45 have an unlock). The
  added entries carry `Type` 1, `UIType` 3 and no reward; the
  mod also rewrites `Type` on
  50 existing items,
  and all its additions carry the same `Type 1` / `UIType 3` pair.
  Whether the absence of a task reward is what makes an entry available is UNKNOWN:
  the mod is evidence of a working pattern, not of the rule.

## 7. The recipe - an entry named "Batmobile" that spawns a given `.ee`

1. **Pick the leaf name** of the entity to spawn. The entry binds by hash, so the
   leaf must match the `.ee` exactly. For the Batmobile in the donor's chassis folder
   this doc uses `v0300_car_kensington_sportsmuscle_batmobile`.
2. **Compute the 32-bit Jenkins hash** of that leaf - the same function as the
   archive paths (`rbmhdr.hash_jenkins`; §9 re-runs the checks):

   `hash_jenkins("v0300_car_kensington_sportsmuscle_batmobile")` = **443190071** =
   `0x1A6A8B37`. That `.ee` is
   **not** in the shipped index yet - the entity must be shipped as an archive override (`G2-27`).

3. **Add one `Item`** with these values (the row is the donor vehicle drop
   `v0300_car_kensington_sportsmuscle_civilian_01` with the identity fields swapped):

| field | value | why |
|---|---|---|
| `Name` | `443190071` | hash of the leaf (step 2) - the spawn binding |
| `BaseName` | `276735921` | kept from the donor; its meaning is UNKNOWN |
| `DlcId` | `0` | 196/196 vanilla records carry 0; only the patch layout has this member - a base-root table omits it and every other offset is unchanged |
| `Type` | `1` | kept from the donor: 1 is what all 80 vanilla vehicle drops use |
| `Purchasable` | `0` | 0 (all 80 vanilla vehicle drops) |
| `Consumable` | `0` | 0 (all 80 vanilla vehicle drops and the mod's added entries) |
| `Rewardable` | `1` | 1 (all 80 vanilla vehicle drops) |
| `Collectable` | `0` | 0 (all 80 vanilla vehicle drops) |
| `Feats` | (empty) | empty array (all 80 vanilla vehicle drops) |
| `Region` | `0` | 0 (all 80 vanilla vehicle drops) |
| `RebelDropTimer` | `1800` | donor cooldown 1800; 0 if no cooldown is wanted (the mod uses 0) |
| `MaxInventory` | `0` | 0 (all 80 vanilla vehicle drops) |
| `UIType` | `3` | 3 on all 80 vanilla vehicle drops |
| `UIFlag` | `5` | the donor's flag; 1..11 occur on vanilla vehicles, enum labels UNKNOWN |
| `UIDisplayOrder` | `12` | one past the highest slot in the vanilla table (11), so a free slot; the donor's own value is 3 and the mod's added entries use 13..50 |
| `UIName` | `443190071` | same hash as `Name` (80/80 vanilla vehicles) |
| `UIDescription` | `2073308658` | the donor's localization key hash (string not in these files) |
| `UITypeDescription` | `2432797658` | the donor's localization key hash (string not in these files) |
| `UIFlagDescription` | `1383769868` | the donor's localization key hash (string not in these files) |
| `UIImagePath` | `v0300_car_kensington_sportsmuscle_batmobile` | the leaf name (vanilla convention; `placeholder` also occurs in the mod) |
| `UIVideoPath` | `v0300_car_kensington_sportsmuscle_batmobile` | the leaf name |
| `UIPar0` | 0.83 | donor icon parameter; the five are per-item |
| `UIPar1` | 0.4 | donor icon parameter; the five are per-item |
| `UIPar2` | 0.45 | donor icon parameter; the five are per-item |
| `UIPar3` | 0.09 | donor icon parameter; the five are per-item |
| `UIPar4` | 0 | donor icon parameter; the five are per-item |

4. **Keep the array valid**: append the item to `Items[]`, bump the array count, and
   write the strings (`UIImagePath`, `UIVideoPath`) into the string area. In the two
   mod tables the items sit back to back at 128 B each and the strings follow the
   block - that is the layout `--check` verifies (`stride` 128, `strings_start` =
   block end).
5. **Optional unlock**: vanilla hands the donor drop out from a task reward. The
   donor item's unlock rows are task `1361701860` (type 19, permanent 1, delivery 0, quantity 1). To gate the new entry the same way, add an `ItemReward` with `Item` = the hash,
   `Permanent` 1, `Quantity` 1, `Delivery` 0 to a `Reward.Items[]` of a task; to make
   it available like the mod does, leave it out: its added entries carry `Type` 1,
   `UIType` 3, `RebelDropTimer` 0 and no reward (measured).
   Whether the missing reward is what makes them available is UNKNOWN (Q-1 probe).

`UIName` may also be shared: 27 of the mod's 45 added
 items set it to a hash other than `Name`, and 27 of those share it
 with another added item (one hash covers 16, one hash covers 11), while 0 reuse a `UIName` that a vanilla item also uses. So the
 field is a display-name key, not an identity. `Name` (and the `BaseName` the mod also
 sets to it) is the identity.

The mod's own added entries look like this (most common value per field over its
 45 additions, `UIDisplayOrder` 13..50):

| field | mod value |
|---|---|
| `BaseName` | `3378979396` |
| `Type` | `1` |
| `Purchasable` | `0` |
| `Consumable` | `0` |
| `Rewardable` | `1` |
| `Collectable` | `0` |
| `Feats` | (empty) |
| `Region` | `0` |
| `RebelDropTimer` | `0` |
| `MaxInventory` | `0` |
| `UIType` | `3` |
| `UIFlag` | `3` |
| `UIDisplayOrder` | `27` |
| `UIName` | `3371861532` |
| `UIDescription` | `3371861532` |
| `UITypeDescription` | `4071394088` |
| `UIFlagDescription` | `1206262488` |
| `UIImagePath` | `placeholder` |
| `UIVideoPath` | `placeholder` |
| `UIPar0` | `0.44` |
| `UIPar1` | `0.29` |
| `UIPar2` | `0.98` |
| `UIPar3` | `0.21` |
| `UIPar4` | `0.11` |

The mod tables carry the base 25-member layout, so there is no `DlcId` row here;
their records hold `Type`..`Collectable` at 8..24, i.e. the ordinary vanilla ints
 (`Type` 1 on all 45 added entries). The patch layout inserts
`DlcId` at 8 and moves those five by 4 B; the values are not 'mirrored' - the whole
run shifts by one member.


## 8. UNKNOWN

- The **strings behind every hash** (`Name`, `BaseName`, `UIName`, `UIDescription`,
  `UITypeDescription`, `UIFlagDescription`, task names/tips): only hashes are in these
  files. Resolving them needs the string tables (G2-32). What `BaseName`, `Type`,
  `UIType`, `UIFlag`, `DlcId` and `ItemReward.Delivery` *mean* is likewise UNKNOWN -
  only their distributions are measured.
- The **`RebelDropTimer` unit**: the field name and the 60/600/900/1200/1500/1800/2400/2700 values
  read as seconds, but nothing in the file states the unit.
- **Which layout a type-table-less table is loaded with.** The mod ships the base root
  and its records read as ordinary base-layout entries (`Type` 1), so this doc uses the
  base layout; nothing in the files says which member list the loader picks, and the
  question matters to a writer even though base and patch values are identical.
- Whether the absence of a task reward is what makes an entry available: the mod's
  added entries carry `Type` 1, `UIType` 3 and no reward, a working pattern, not a
  decoded rule (Q-1 probe: one variable).
- What `UIPar0..4` frame and whether `UIImagePath` must be a real icon for the menu
  (the mod ships `placeholder`).
- The exact array serialisation a *new* item must follow beyond stride 128 + string
  area: both mod files were written by an external tool and this doc reproduces their
  layout, not the game's writer.

## 9. Validation and limits

`jc3rebeldrop.py --check` re-extracts both vanilla layers, re-decodes the three mod
variants with the layout each file declares, rebuilds `REBELDROP.json` and this file byte for
byte and asserts:

- 196 vanilla items / 591 vanilla tasks;
 80 vehicle-bound items; 185 of
 196 items resolving to an `.ee` (the other 11 name no shipped `.ee`)
 and the same 11 staying unresolved in every mod variant;
- **the stride proof is the string pointer, not the hash read**: every `UIImagePath`
  pointer resolves to a printable or empty NUL-terminated string for every record
  (196/196 base, 196/196 patch, 232/232 mod Regular v5.2, 240/240 mod V5.2 Plus, 240/240 mod V5.3 Plus; 0 failures). The hash-field
  check (0 mismatches) only proves the 32-bit masking, because it reads the same
  offset it decodes;
- **the layout assignment**: the base and patch files carry their own type tables (25
  and 26 members), the mods carry none and their root hash selects the base layout; the
  base/patch diff over the 25 common members is re-derived and the five ints at 8..24
  must agree on every matched item;
- the base table's type count (5) and root hash (`0x79DE48AE`), the mods' empty type
  tables and their root, and the variant item/task counts, diffs, added-entry pattern
  (`BaseName` = `Name`, `Type` 1, `UIType` 3, timer 0, `placeholder`) and the task reorder;
- the recipe hash (`hash_jenkins(leaf)`) and the documented Jenkins checks.

**Limits.** Only the two `profile` tables are read; how the game consumes an item
(menu, pricing, delivery animation) is code. The `.ee` resolved from a name hash is a
path in `INDEX.jsonl`, not proof the entity loads. Task strings and enums stay
UNKNOWN. Nothing here is written into the game; the recipe produces a table edit for
phases T/B, and shipping the entity itself is `G2-27`.
