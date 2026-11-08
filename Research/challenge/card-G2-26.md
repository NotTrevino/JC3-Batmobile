# Assumption challenge — backlog card G2-26 (Rebel Drop data, RD-1 read half)

Read-only pass over the finished card: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G2-26 card (§6, line 740),
its §12 row (line 1309), the MODLOG `G2-26 · Rebel Drop data (RD-1 read half) — intended change`
(line 10230) and `— done` (line 10362), and the outputs `Research/JC3Grab/REBELDROP.md` +
`REBELDROP.json` + the generator `Tools/scripts/jc3rebeldrop.py`, plus what it reads:
`Research/1456340180_Rebel-Drop-Mod-V5.3/{Regular v5.2,V5.2 Plus,V5.3 Plus}/profile/{item,task}.onlinec`,
the two vanilla layers from `INDEX.jsonl` (`profile/item.onlinec` 52,165 / 52,204 B;
`profile/task.onlinec` 167,286 / 167,470 B), the extracted copies in
`E:/Modding/_JC3grab/rebeldrop/`, `INDEX.jsonl` (81,952 entries, 963 `.ee`), and — for the
"only searched some places" tests — the other `profile/*.onlinec` tables the card's **In** list never
mentions (`offer`, `taskgroup`, `upgrade`).

Constraints honoured: no game launched, nothing written into `D:/Games`, nothing committed, no secrets,
no writes at all — **I did not run `--check`**, because `build()` calls `extract()`, which rewrites the
`E:/Modding/_JC3grab/rebeldrop/` cache (`os.makedirs` + `open(..., "wb")`). Instead I imported the module
and re-derived every number in-process from those cached bytes and the mod files. The cache is the same
data the report describes — its sha1s match REBELDROP.md §5 exactly:

```
base_item     52165 B sha1 23348af9561c4aa6     (md: 23348af9561c4aa6)
patch_item    52204 B sha1 bcb146b55fbd07ce     (md: bcb146b55fbd07ce)
base_task    167286 B sha1 6d60288e1534b725     (md: 6d60288e1534b725)
patch_task   167470 B sha1 72a907016cbfd97f     (md: 72a907016cbfd97f)
```

Baseline re-derivation (`R.item_rows` on both vanilla layers + the three mod tables):

```
base  types 5 root 0x79de48ae  Item 25 members  Type at 8      196 items  hashmis 0  strfail 0
patch types 5 root 0x921af417  Item 26 members  DlcId at 8     196 items  hashmis 0  strfail 0
```

## VERDICT

**Five BROKEN, five WEAK, ten HOLDS.** The card's *measurements* survive: 196 items / 591 tasks, 80
vehicle drops, 185/196 names resolving, the 128 B stride, 87 reward links, the mod's 39/45/45 additions,
the recipe hash, and every per-field value the md prints. What does not survive is the **scope of its
negatives** and a **definitional circularity at the centre of the "binding" argument**, plus three
places where the MODLOG's own summary contradicts the output it summarises (A7, A8).

The headline claim — `Item.Name` is a Jenkins hash of the entity leaf and "that is the whole spawn
binding" — is *consistent with every byte I can read* and has real corroboration, but it is not proved:
the only test that produces 185/196 is "find an `.ee` whose leaf hashes to `Name`", which assumes the
rule it is meant to test. The one check the md calls independent (`Name == hash(UIImagePath)`, 80/80)
is not independent, because on vehicles `UIImagePath` *is* the entity leaf: it is the same string on
both sides. Nothing in the game files shows the lookup; it is code (the md admits as much for the menu,
not for the spawn).

The negatives are the weak part. **"There is no cost field"** and **"`Reward`/`ItemReward` are the only
place an item is granted"** are statements about `item.onlinec`/`task.onlinec` only — the profile folder
also carries `offer.onlinec`, whose schema has `Offer.Cost`, `Offer.StartTime`, `Offer.EndTime` and
`OfferItem { Item, Permanent, Duration, Quantity }` (a priced, item-granting offer). Both tables are
*empty/zero* in vanilla (0 offers; 59 upgrades all `Cost` 0), so no value is contradicted — but the
wording is wider than the search. And **"the unlock is in `task.onlinec`"** is true for 74 of 80 vehicle
drops: six drop items have no reward anywhere, all of them ordinary vehicles
(`v0000…_rebel_01`, `v0504…_rebel_01`, `v0505…_rebel_01`, `v1701…_boat`, `v2102…_helicopter`,
`v4600…_plane`). That is a better precedent for the recipe's "leave the reward out" branch than the
external mod is.

| # | assumption | verdict |
|---|---|---|
| A1 | `Item.Name` is the 32-bit Jenkins hash of the entity **leaf**, and the game resolves it to the `.ee` (the spawn binding) | **WEAK** — the hash convention is pinned (0/196 for leaf+`.ee`, full path, uppercase; 185/196 for bare leaf), but "resolve" is definitional and no file shows the lookup |
| A2 | "independent check on the vanilla vehicles: `Name == hash(UIImagePath)` 80/80" | **BROKEN (as independence)** — on vehicles `UIImagePath` is the entity leaf itself (80/80 leaf equality); for the 116 non-vehicle items the same equality holds 0/116 (images `''` 87, `placeholder` 4, `'123'`, `'21'`) |
| A3 | "80 vanilla vehicle drops … all satisfy `Name == hash(UIImagePath)`" | **WEAK** — the 80 *are* the items for which that equality holds; the sentence restates the filter. (The 80 is nevertheless sound: `Type == 1` is also exactly 80 and the two sets are identical, 80 overlap / 0 either way) |
| A4 | "185/196 resolve to an `.ee`" says something about drops | **WEAK** — 130 resolve to a `jc_vehicles` path, 105 resolve to non-`Type 1` items (80 `Type` 0, 25 `Type` 2) incl. `jc_weapons/…` and `…_propaganda_chaoslist`; resolution ≠ vehicle drop |
| A5 | the unlock is a task reward (87 `ItemReward` links) | **WEAK** — true for 74/80 vehicle drops; **6 have no reward at all**, so a reward-less drop is vanilla-precedented, not only mod-precedented |
| A6 | "no cost field", "`RebelDropTimer` the only time", "`Reward`/`ItemReward` are the only place an item is granted" | **BROKEN as a corpus claim** — `profile/offer.onlinec` declares `Offer.Cost`/`StartTime`/`EndTime` + `OfferItem.Item`; `profile/upgrade.onlinec` declares `Upgrade.Cost`. Vanilla data is empty/zero (0 offers; 59 upgrades `Cost` 0), so only the wording fails |
| A7 | "All four files are decoded with the patch's `ItemRoot` (0x921AF417) schema" (MODLOG done) vs "the mods are read with the base 25-member layout" (md/§12) | **BROKEN (the MODLOG sentence)** — the md is right: grafting the patch `Item` members onto a mod table yields `Type` 0 on every record and `DlcId` 0 on exactly 39 |
| A8 | the mod adds "39/45/45 items, all `Type` **0**" (MODLOG done) vs "`Type` **1**" (md §6, §12) | **BROKEN (the MODLOG value)** — measured `Type` 1 on 39/39, 45/45, 45/45 added entries |
| A9 | `RebelDropTimer` takes "600/900/1200/1800/2400" (§12, MODLOG) | **WEAK** — actual set is 60×1, 600×17, 900×15, 1200×11, 1500×8, 1800×16, 2400×9, 2700×3 (md §2 prints all eight; the summary rows drop three) |
| A10 | `UITypeDescription` is "shared by items of one category" | **BROKEN** — 32 distinct values over the 80 items that all carry `UIType` 3. (The parallel claim for `UIFlagDescription` holds: 11 distinct, 1:1 with `UIFlag` 1…11) |
| A11 | `BaseName` is a grouping key, "what it names: UNKNOWN" | **HOLDS** — 138 distinct over 196, group sizes 1×99 / 2×29 / 3×5 / 4×3 / 5×1 / 7×1; and 0 of the 138 is also an item `Name`, so it is not a parent reference |
| A12 | "`Name` resolves to exactly one `.ee` path" | **HOLDS for the 196 item names** (0 with >1 candidate) but **not generally**: 39 of the 963 leaves are shared by 2–3 paths, so a new leaf's uniqueness must be checked — the recipe's `443190071` is in no item name and no leaf hash |
| A13 | the 128 B stride, proved by the string pointer (124 B gives garbage) | **HOLDS** — string-pointer failures: stride 128 → **0**, 124 → **175**, 132 → **173** |
| A14 | every hash field is a 4-byte `StringHash` masked to 32 bits | **HOLDS** — 0 raw-vs-walked mismatches on 196/196; `Region` 0 / `RebelDropTimer` 600 is the `600 << 32` artefact the md describes |
| A15 | "it ships 15 `.ee` files of its own … 11 named / 4 unnamed" | **HOLDS in substance** (15 distinct leaves, 11 named, the 4 unnamed are exactly the md's list) **WEAK in wording** — 20 files, because the 5 leaves the Plus builds ship appear in both Plus variants |
| A16 | the recipe (leaf, hash 443190071, donor's 22 fields, `UIDisplayOrder` 12) | **HOLDS on every number re-derived**, **WEAK on completeness** — it copies a `BaseName` whose meaning is UNKNOWN and sets `UIImagePath` to the leaf while §8 says a real icon may be needed |
| A17 | the 11 unresolved names are `UIType` 0; "what they are is UNKNOWN" | **HOLDS** — 11/11 `UIType` 0, images 7 empty + 4 `placeholder`, and none of the 11 appears in `task`/`upgrade`/`taskgroup` (1,535 / 236 / 40 hashes searched) |
| A18 | the `RebelDropTimer` unit is UNKNOWN | **HOLDS** — correctly hedged, and the recipe's 1800 is a donor copy, so unit-independent |
| A19 | "196 items / 591 tasks from the base + patch layers; the patch is the effective one" | **HOLDS (and moot)** — both layers carry the same 196/591 records and agree on all 25 shared members; "effective" changes nothing but `DlcId` (0 on 196/196) |
| A20 | the per-field value lists over the 80 (flags, timers, orders, `UIName`) | **HOLDS** — every list re-derives exactly (see §A20) |

Counts: 10 HOLDS, 5 WEAK, 5 BROKEN (A15 and A16 are counted HOLDS with a wording/completeness caveat in
side them; the two MODLOG contradictions A7/A8 are counted BROKEN because the journal text is false even
though the md's result is right).

---

## A1 — `Item.Name` = `hash_jenkins(leaf)` is the spawn binding. **WEAK**

The convention test is clean and decisive *about the hash*, and I could not find a competing one:

```
leaf (no .ee) : 185/196 item names match a hashed .ee leaf
leaf + .ee    :   0/196
full path     :   0/196
LEAF upper    :   0/196
```

That pins the input string (`<leaf without .ee>`, exact case) for 185 items, and the script's
`entity_index()` builds the map by hashing `p.rsplit('/',1)[-1][:-3]`. But the same table shows what the
test actually is: it *defines* the map as `hash(leaf) → path`, then counts how many item names are keys.
Any item whose `Name` happened to be a hash of something else would simply be "unresolved". So 185/196
proves "185 of the names are hashes of leaves", not "the game looks the entity up by that hash". The
md's strongest sentence — "the mod proves the direction the other way: it ships 15 `.ee` files and 11 of
its added entries hash to one of those leaves" — is genuinely independent and is the reason this is WEAK
rather than BROKEN: an external mod author, working from behaviour, chose leaves that then hashed to the
`Name` values in his own table. Nothing in either `.onlinec` references a path; `Item` has no path member
at all (its 26 members are hashes, ints, two strings and five floats), so the binding is code.

Two things would settle it and neither is in the card: a `Name` whose leaf exists in *no* archive (the
11 unresolved are the closest thing, and the md correctly says what they are is UNKNOWN), or the
relocation the mod does *not* do (an item whose `UIImagePath` leaf differs from the ship path).

## A2 — the "independent check" is not independent. **BROKEN as an independence claim**

`REBELDROP.md` §4:

> independent check on the vanilla vehicles: `Name == hash(UIImagePath)` for 80/80 items whose
> `UIImagePath` is a vehicle leaf

Measured, the check is the leaf test wearing a different field name:

```
vehicle item UIImagePath == resolved .ee leaf : 80 / 80
distinct UIImagePath over the 80             : 80
UIImagePath == UIVideoPath over the 80       : 80
hash(UIImagePath) == Name over non-vehicles  : 0 / 116   (images: '' 87, 'placeholder' 4, '123', '21')
```

So on vehicles the image string *is* the entity leaf, and the equality is `hash(leaf) == Name` a second
time — reported as if two fields agreeing were a second witness. It is not wrong, but it cannot be
called independent, and the same pattern (image = entity leaf) is what makes the recipe's
`UIImagePath = leaf` step safe; the card should say that instead.

## A3 — the "80" is a filter, not a finding. **WEAK**

`--check` computes `vanilla_vehicle_items = van_image_bound`, i.e. the count of items where
`hash(UIImagePath) == Name`, and the md then reports "all 80 vanilla vehicle drops satisfy
`Name == hash(UIImagePath)`". Definitionally true. The 80 is nonetheless a real population — the
independent discriminator lands on exactly the same set:

```
patch Type dist: {0: 90, 1: 80, 2: 26}
image_bound 80   Type==1 80
overlap Type1 & image_bound 80 · Type1 & not image_bound 0 · image_bound & not Type1 0
```

so the sentences that say "on all 80 vanilla vehicle drops, `X = y`" are sound as statements about
`Type == 1`, and every value below re-derives (A20). The fix is to say "the 80 items with `Type` 1
(which are exactly the items whose `Name` is the hash of their `UIImagePath` leaf)" and then stop
calling the equality a check.

## A4 — "resolved to an `.ee`" is not "is a drop". **WEAK**

```
resolved to a jc_vehicles path : 130
resolved but Type != 1         : 105  (Type 0 ×80, Type 2 ×25)
   e.g. editor/entities/jc_vehicles/02_air/v2201_helicopter_capstone_heavytroop/…_military_01.ee
        editor/entities/jc_weapons/06_vehicle/w610_fighterjet_mgun/w610_fighterjet_mgun.ee
        editor/entities/jc_vehicles/01_land/v0505_car_solar_oldtruck/…_commercial_cargo_barrel.ee
        editor/entities/jc_vehicles/01_land/v0501_car_solar_smallvan/…_propaganda_chaoslist.ee
entity .ee paths in index : 963
```

The `.ee` namespace includes weapons, parts and props, so "185/196 resolve" mixes drops with upgrade
unlocks and carcass entities. The md mostly keeps the distinction (it prints "80 vehicle drops" and
"185 resolved" separately) but the §12 row leads with the 185 and the MODLOG says "`Name` resolves to
exactly one `.ee` path for 185 of the 196 vanilla items — the 11 that do not resolve are the non-vehicle
unlocks", which reverses the causality: 105 of the 185 are the non-vehicle unlocks.

## A5 — the unlock story covers 74 of 80 drops. **WEAK**

```
tasks 591 · reward links 87 · distinct rewarded items 87 · Delivery all 0
vehicle drops WITH a reward      : 74 / 80
vehicle drops with NO reward     :  6
   3910701466  v0505_car_solar_oldtruck_rebel_01          timer 1500
   3145488079  v0504_car_solar_technicaljeep_rebel_01      timer 1500
    274180142  v0000_car_autostraad_oldjeep_rebel_01       timer 1500
   2580011165  v1701_boat_na_smalloldfishing_civilian_01   timer   60
   1493705456  v2102_helicopter_eubus_utility_civilian_01  timer 2400
    596249749  v4600_plane_urga_privatepropeller_civilian_01 timer 1800
```

Six ordinary `Type 1` / `UIType 3` drops are in the menu with no `ItemReward` anywhere, and they are
not the mod's invented pattern — they are vanilla, shipped, working entries. `REBELDROP.md` §3 says
"`Reward` … and `ItemReward` … are the only place an item is granted" and §7 offers "Optional unlock";
the six show that *not* granting is a shipped state, which is exactly the evidence the recipe's
"leave it out" branch needs. Worth promoting from "the mod does it" to "six vanilla drops do it".

## A6 — "no cost field" / "the only place an item is granted". **BROKEN as a corpus claim**

The profile folder the card's **In** list names contains **two** files. The archive has five:

```
profile/        11 index entries:
   profile/item.onlinec (base, patch)
   profile/task.onlinec (base, patch)
   profile/taskgroup.onlinec (base, patch)
   profile/offer.onlinec            (1 layer, 1246 B)
   profile/upgrade.onlinec          (2 layers, 14525 B)
   profile/online.stringlookup (base, patch)
```

Decoded read-only through `jc3adf` (their own type tables):

```
OfferRoot      -> A[Offer]
  Offer       { GroupId, Type, Cost, Items: A[OfferItem], StartTime, EndTime,
                UIType, UIFlag, UIDisplayOrder, UIName, …, UIImagePath, UIVideoPath }
  OfferItem   { Item, Permanent, Duration, Quantity }
UpgradeRoot   -> A[Upgrade]
  Upgrade     { Name, TaskGroup, StarThreshold, Prerequisites, Cost, Ability, …, DlcId }
```

Measured contents: `offer.onlinec` has **0 offers** (`array_off 0 count 0` at `data_off 80`), and all
**59** upgrades have `Cost 0`. So:

* **nothing in the vanilla *data* contradicts "no cost"** — the only economic values are the
  `Purchasable`/`Consumable` flags on `Item`, all 0 on the 80, and the offer table is empty;
* **the *schemas* contradict the wording**. `Offer.Cost`, `Offer.StartTime`/`EndTime` (two more time
  fields) and `OfferItem.Item` (a second grant path) all exist in the same profile folder, and
  `Upgrade.Cost` too. "There is no entity-path field and no price field anywhere in either table" is
  true; "the only place an item is granted" and "the only time is `RebelDropTimer`" are not statements
  about the same files, and the §12 row and MODLOG state them at file scope with bold.

The card is a *read half*, and it was entitled to stay in two files — but then the negatives need the
scope in the sentence, or `offer.onlinec` needs one line in the md saying the price machinery exists and
is empty. (It also matters for G2-27/T-20: if a priced or timed entry is ever wanted, the table exists
and the item table cannot express it.)

## A7 — the layout story: two schemas, and the MODLOG names the wrong one. **BROKEN (MODLOG)**

`REBELDROP.md` §1 and §12 say each file is read with the layout it declares: base 25 members
(`Type` at 8, no `DlcId`), patch 26 (`DlcId` at 8). The MODLOG done entry says the opposite:

> All four files are decoded with the patch's `ItemRoot` (0x921AF417) schema.

Tested by grafting the patch's `Item` member list onto the base root (the only way a base-rooted file
can carry it — the patch type table has no `0x79DE48AE` at all, so "read with the patch schema"
cannot even be attempted without a remap):

```
V5.3 Plus: own_types 0 root 0x79de48ae items 240
   base 25-member : hashmis 0 strfail 0  Type=1 172  Type=0 39
   patch 26-member: hashmis 0 strfail 0  DlcId=0  39  Type=1   0
```

The patch layout reads every record's `Type` as 0 (it is reading base `Type` as `DlcId`), including the
45 added entries. So the md's assignment is the correct one and the MODLOG's sentence is wrong — and
`jc3rebeldrop.lend()` is written the md's way (`layout_from = f"{layer} root {root:#010x}"`). This
matters because "just use the patch schema everywhere" is the tempting simplification, and the MODLOG
currently recommends it.

## A8 — the mod's added entries are `Type` 1, not 0. **BROKEN (MODLOG)**

```
Regular v5.2 : added 39  added Type Counter({1: 39})  UIType {3: 39}  BaseName==Name 39/39  timer [0]
V5.2 Plus    : added 45  added Type Counter({1: 45})  UIType {3: 45}  BaseName==Name 45/45  timer [0]
V5.3 Plus    : added 45  added Type Counter({1: 45})  UIType {3: 45}  BaseName==Name 45/45  timer [0]
```

md §6 and §12 say `Type` 1 (correct); the MODLOG done entry says "adds 39 / 45 / 45 items (**all `Type`
0**, `UIType` 3, …)". The added set is exactly what the md describes, and the recipe's "a working new
entry looks like this" table is right. No output is affected — but the one-line summary a future session
reads first is wrong, and `Type 0` is the *vanilla non-vehicle* value (90 items), so copying it from the
MODLOG would produce a non-drop entry.

## A9 — the timer list. **WEAK**

```
RebelDropTimer over the 80: 60×1, 600×17, 900×15, 1200×11, 1500×8, 1800×16, 2400×9, 2700×3
```

md §2 prints all eight; §12 and the MODLOG print five ("600/900/1200/1800/2400"), dropping 60, 1500 and
2700. The unit stays UNKNOWN as the md says. Small, but it is the kind of list someone copies into a row.

## A10 — `UITypeDescription` is not per-category. **BROKEN**

`REBELDROP.md` §2: "`UITypeDescription` | localization key hash, **shared by items of one category**".
The 80 vehicle items all carry `UIType` 3, so "one category" is a single value:

```
distinct UIType over 80            : 1
distinct UITypeDescription over 80 : 32
distinct UIFlag over 80            : 11
distinct UIFlagDescription         : 11    UIFlag -> UIFlagDescription 1:1: True
distinct UIDescription over 80     : 80
```

32 descriptions for one type value falsifies the parenthetical. (The same sentence shape for
`UIFlagDescription` *is* right — 11 values, one per `UIFlag` — which is why this reads as an inference
from the member's name, R5 exactly: `UITypeDescription` sounds like it describes `UIType`; it evidently
describes something finer (vehicle class? icon family?) that the file does not name.)

## A11 — `BaseName` is a grouping key, not a reference. **HOLDS**

```
distinct BaseName over 196 : 138
group sizes: 1×99, 2×29, 3×5, 4×3, 5×1, 7×1
BaseName values that are also an item Name : 0 / 138
donor BaseName : 276735921 (Name 3535039305)
```

The md's "grouping key, what it names UNKNOWN" survives, and my extra test closes the obvious candidate
(it is not a parent/variant pointer to another item). 80/80 vehicle items have `BaseName != Name` as
printed.

## A12 — "exactly one `.ee` path per name". **HOLDS for items, WEAK in general**

```
resolved item names with >1 candidate .ee : 0
leaf hashes with >1 path over 963 .ee     : 39   (max 3)
recipe hash 443190071 : in item names False · in leaf hashes False
```

So the claim is true of the 196 and of the recipe, but the leaf→path map is **not injective in the
archive** — 39 leaves live in two or three folders (`…_mm230`-style variants). That does not touch this
card's numbers, but it is a live risk for G2-27: a new Batmobile leaf must be checked against the shared
namespace (443190071 is free, measured), and if two paths ever share a leaf the game's choice is UNKNOWN.

## A13 / A14 — the two reader facts. **HOLDS**

The stride proof is real and discriminating (the md's "124 B gives garbage" re-derives as 21 of 196
passing):

```
string-pointer failures at stride 128 : 0
string-pointer failures at stride 124 : 175
string-pointer failures at stride 132 : 173
```

The masking fact also holds, and the doc is honest that the hash check is self-referential
("it reads the offset it decodes"):

```
patch 196 items: hash_field_mismatches 0
first record: Region 0, RebelDropTimer 600      (i.e. the 8-byte read is 600 << 32)
```

## A15 — "15 `.ee` files". **HOLDS in substance, WEAK in wording**

```
mod .ee files: 20      distinct leaves: 15
duplicated leaves (in both Plus variants): pinata, pinata_stick, sponge,
    v1704_boat_na_lightpatrol_civic_police_01, w141_rpg_uvk_13_mm110
11 named by an added entry · 4 unnamed: tank_techinal_wreck, techinal2_oldcompact_wreck,
    v1704_boat_na_lightpatrol_civic_police_01, w141_rpg_uvk_13_mm110
```

The 11/4 split is right and the md's named/unnamed lists re-derive exactly; only "15 `.ee` files" should
be "15 distinct leaves (20 files, 5 shipped in both Plus variants)".

## A16 — the recipe. **HOLDS on every number, WEAK on completeness**

Re-derived from the donor row (`UIImagePath == "v0300_car_kensington_sportsmuscle_civilian_01"`):

```
Name 3535039305  BaseName 276735921  DlcId 0  Type 1  Purchasable 0  Consumable 0  Rewardable 1
Collectable 0  Region 0  RebelDropTimer 1800  MaxInventory 0  UIType 3  UIFlag 5  UIDisplayOrder 3
UIName 3535039305  UIDescription 2073308658  UITypeDescription 2432797658  UIFlagDescription 1383769868
UIPar0..4 0.83 / 0.4 / 0.45 / 0.09 / 0
max UIDisplayOrder over 196 = 11  ->  free slot 12
hash_jenkins("v0300_car_kensington_sportsmuscle_batmobile") = 443190071 = 0x1A6A8B37  (free)
```

Every value matches the recipe table, the "12 is free" claim is right, and the donor's unlock row is
`task 1361701860, type 19, permanent 1, quantity 1, delivery 0, threshold 1` as printed. Two gaps:

1. `BaseName` is copied from the donor although the md itself says its meaning is UNKNOWN; since it is
   a grouping key (A11) and every vehicle has its own value, copying is a guess that happens to look
   like the fleet (138 groups over 196 items, so 2.1 avg — not unique per item).
2. `UIImagePath` is set to the leaf, and §8 lists "whether `UIImagePath` must be a real icon" as
   UNKNOWN. Since on vehicles it *is* the leaf (A2), the recipe is consistent with vanilla; but the
   card never tests what draws the icon, and the mod proves `placeholder` is accepted by the menu.

## A17 — the 11 unresolved names. **HOLDS**

```
11 unresolved · UIType {0} · images: '' ×7, 'placeholder' ×4
names: 761188693 2798585508 4229490449 154566667 502440914 1835714130 2580345571 682355505
       1057967201 613299528 2995941402
search of task/upgrade/taskgroup hashes (1535 / 236 / 40): none of the 11 found
```

The md's description is exact and the mod keeps the same 11 (`unresolved 11/232, 11/240, 11/240`). My
extra search narrows "UNKNOWN" a little (not a task, upgrade or taskgroup key), so the remaining
candidates are the string tables (G2-32) or entities outside `INDEX.jsonl`.

## A18 / A19 / A20 — the remaining measured claims. **HOLDS**

* **A18** the timer unit is UNKNOWN and the recipe copies 1800, so nothing depends on the unit.
* **A19** both layers carry 196 items / 591 tasks; the 25 shared members agree on 196/196 matched items;
  `DlcId` 0 on 196/196; so "the patch is the effective one" is true and harmless.
* **A20** every per-field list in the md re-derives:

```
Purchasable 0×80 · Consumable 0×80 · Rewardable 1×80 · Collectable 0×80 · Region 0×80
MaxInventory 0×80 · UIType 3×80 · UIFlag 1..11 (7,5,6,5,10,10,8,3,11,9,6)
UIDisplayOrder 1..11 (11,11,11,10,10,8,6,5,4,3,1) · BaseName != Name 80/80 · UIName == Name 80/80
UIImagePath distinct 80/80 · UIPar tuples distinct 78/80 · UIDescription distinct 80/80
mod added with a vanilla-task reward 0/39, 0/45, 0/45 · added UIDisplayOrder 13..50
UIName: 27 of 45 differ from Name, all 27 shared (groups 16 and 11), vanilla reuse 0
diff vs base: added 39/45/45, removed 3/1/1, changed 160/162/162
   top fields 109 RebelDropTimer, 57 UIDisplayOrder, 52 UIImagePath/UIVideoPath (Plus)
task file: 591 tasks, 0 added, 0 removed, 566/591 positions moved — identical False
```

The `Type` histogram of tasks (`2×132, 3×112, 4×29, 5×3, 6×1, 11×49, 12×30, 14×11, 16×27, 19×47,
20×71, 21×23, 22×54, 100×2`) and the 87/87 reward census reproduce as printed.

---

## What would close the gap cheaply

1. **Say what the binding test is.** "185/196 item names are the Jenkins hash of a shipped `.ee` leaf;
   the game's lookup is code (no path is stored). An external mod's 11 added entries hash to the `.ee`
   files it ships, which is the only non-circular evidence." Then drop "independent check" from A2 or
   replace it with the fact that `UIImagePath` *is* the leaf on vehicles.
2. **Scope the negatives in one sentence**: "Item has no price member; the profile folder's price
   machinery lives in `offer.onlinec` (`Offer.Cost`, `OfferItem.Item`, `StartTime`/`EndTime`), which
   ships **empty** (0 offers), and `upgrade.onlinec` (59 upgrades, all `Cost` 0)."
3. **Promote the six reward-less drops** (A5) next to the mod's pattern — vanilla precedent for the
   recipe's "no reward" branch, and a real limit on "the unlock is a task reward".
4. **Fix the three MODLOG lines** (patch-schema sentence, `Type` 0, five-value timer list) and the
   `UITypeDescription` note (A10).
5. **Add the leaf-uniqueness check** to the recipe (39 of 963 leaves are shared; 443190071 is free) so
   G2-27 knows the new leaf must be globally unique, not just absent from `INDEX.jsonl`.
