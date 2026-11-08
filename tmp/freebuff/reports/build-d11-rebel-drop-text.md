# D-11 · B-13 refresh — `Builds/bm-RC4-rebel`

**STATUS: built, `bm_rebel.py --check` green (0 failures).** The Rebel Drop item, task reward,
strings, icon, standalone leaf and traffic exclusion are all in one RC4 tree, and the item's
computed keys now resolve to Batmobile text in every language — not the Serpente's:

| item field | key | resolves in the built store | text |
|---|---:|---:|---|
| `UIName` / `Name` | **1621485476** = `HashJenkins("..._debug")` | **11/11** | `BATMOBILE` |
| `UIDescription` | **4081821928** = `HashJenkins("..._debug_desc")` | **11/11** | the Batman blurb |
| old plan key | 443190071 = `HashJenkins("..._batmobile")` | 0/11 (also 0/11 vanilla) | — never shipped |
| old plan desc | 1805638565 = `HashJenkins("..._batmobile_desc")` | 0/11 (also 0/11 vanilla) | — never shipped |
| Serpente name | 3535039305 | 11/11, unchanged | `KERNER SERPENTE R` |
| Serpente blurb | 2073308658 | 11/11, unchanged | Kerner's translated blurb |

The key pair comes from `apply-world-text-rows` (`tmp/freebuff/reports/apply-world-text-rows.md`
§1): name **1621485476**, description **4081821928**, and the never-shipping **443190071** is why
the old row premise was wrong. `bm_rebel.py` derives both keys from `LEAF = bm_leaf.NEW`; this run
re-proved them (`receipt.json`: `leaf_hash` 1621485476, `desc_hash` 4081821928) and the store diff
shows exactly those two hashes added, nothing else changed.

## 1. Commands run

```text
python Tools/scripts/bm_leaf.py --write --src Builds/bm-RC4-parts --tag bm-RC4-rebel
python Tools/scripts/bm_leaf.py --check --tag bm-RC4-rebel
python Tools/scripts/bm_rebel.py --write --tag bm-RC4-rebel
python Tools/scripts/bm_rebel.py --check --tag bm-RC4-rebel
```

Exit codes: `0`, `0`, `0`, `0`. `bm_rebel.py --check` ends
`PASS: B-13 0 failure(s)`; the write pass ends the same way and its output is reproduced in §5.

The leaf tree was taken from **`Builds/bm-RC4-parts`** (the RC4 line's 688-file entity tree:
RC4-base + the B-02/B-04 part split and 59-part module), because the item names the entity the
drop spawns and that is the current RC4 geometry tree. This is a **step tree**, not the merged RC;
B-14 merges it with the handling/audio steps and writes the RC `.toc`.

## 2. What is in `Builds/bm-RC4-rebel`

### 2.1 The drop files (`drop/`)

| path | bytes | sha256 |
|---|---:|---|
| `profile/item.onlinec` | 77,569 | `239d6b6d2425fb8c1f4883fcce7a70cf82bc9ed339182a179edb477d8b550a6c` |
| `profile/task.onlinec` | 168,174 | `9250e2712478d50c649a32fbf0a5ab90931a25b1fe9ebaf98c7e38ad89cae6c2` |
| `profile/online.stringlookup` | 1,746,322 | `6dcdf0ce1af304b6a77ebcb319e53a59fcaafed6bf329ca2e9821483d3c60bc4` |
| `textures/ui/vehicle_icons/v0300_car_kensington_sportsmuscle_debug.ddsc` | 18,688 | `5096fb74d8fcce49b26fad8dd269d48fea7be3859ca1c5dd692a0532fae5058f` |
| `settings/spawn_vehicle_defs.bin` | 27,785 | `797391dcef5fb5b6911c40a73d4b0691c876277681b2d51bd0a4eb6157043cf3` |

**Item.** 196 vanilla items -> 197; exactly one carries `Name` = `UIName` = 1621485476,
`UIDescription` = 4081821928, `UIDisplayOrder` 12, `UIImagePath` = the `_debug` leaf,
`UIFlag` 7 / `UIFlagDescription` 1492769243 (the vanilla "military" group, unchanged from bm-013).
All other 20 fields equal the donor's; `UIVideoPath` still names the donor's video string (no video
asset exists for the `_debug` leaf — unchanged decision).

**Task.** Task **1980624442** (type 100, vanilla's starter grant) gains exactly one repeatable
`ItemReward`: `(1621485476, 1, 0, 1, 0)`. All 1,765 reward groups decode and only that one changed,
so the unlock is the starter grant, not the Serpente's "bring to garage" task (Q-1a history).

**Icon (T-WLD5).** Byte copy of the donor icon under the leaf: input and output are both 18,688 B
and sha256 `5096fb74…`, so this is the carried Serpente icon (a real Batmobile icon remains open).

**Traffic exclusion.** The cloned spawn record for the `_debug` leaf carries
`entity = .../v0300_car_kensington_sportsmuscle_debug.ee`, `select = 1`,
`debug = vehicle|ground|rebel`, tags **`vehicle,batmobile`**, and the donor's two clearance vecs.
`--check` matches those tags against `Research/JC3Grab/TRAFFIC.json`: **0 of 41 selectors**, so no
traffic table picks the car (WLD-8 / T-WLD8). The spawn table diff is +1 record (9 XML lines) and
nothing else.

### 2.2 The standalone leaf (`aaf/` + packed `.ee`)

| item | value |
|---|---|
| source tree | `Builds/bm-RC4-parts/aaf` (688 files) |
| leaf | `v0300_car_kensington_sportsmuscle_debug`, `HashJenkins` **1621485476** |
| donor leaf removed | `v0300_car_kensington_sportsmuscle_civilian_01` (3535039305), **0 refs left** |
| renamed inner files | `.epe`, `.stringlookup`, `.ee.fmod_guids`; `@files.xml` 6 entries |
| `.epe` root | `name` = the new leaf, `name_hash` = 1621485476 (8,084 XML lines, only lines 32/33 changed) |
| packed `.ee` | 11,178,868 B, sha256 `4b23b11a07f72d4217a18923b7766e476e51136406a3f3a424fbfed740afbd2c` |
| vs source | 686 files byte-identical; only the renamed `.epe` differs |
| manifest | 702 listed / 687 on disk; **0 new dangling, 0 new unlisted** |
| budgets | inherited from `bm-RC4-parts`, delta **0 KB** (rename only) |

The inherited gaps are the source's, not this step's: 19 size-only shared-texture lines and the 4
wheel LOD4/5 `.rbm` that `@files.xml` does not list (already recorded in B-13b/B-14). No `.toc` is
written here: it is optional (STANDALONE.md §4.4) and B-14 writes the RC's.

## 3. The strings that resolve now — per language

`profile/online.stringlookup`: 11 languages, pairs **14,712 -> 14,734** (+22 = 2 keys × 11), every
pre-existing pair resolves to exactly its old text, every `SortedPairs` array stays ascending, the
dialogue lines are untouched, and the only added text is `BATMOBILE` and the Batman blurb.

| lang index | 1621485476 (name) | 4081821928 (desc, first 46 chars) | 3535039305 (Serpente, untouched) |
|---:|---|---|---|
| 0 | `BATMOBILE` | `Arkham Knight's armoured Batmobile: pursuit sp` | `KERNER SERPENTE R` |
| 1 | `BATMOBILE` | same | `KERNER SERPENTE R` |
| 2 | `BATMOBILE` | same | `KERNER SERPENTE R` |
| 3 | `BATMOBILE` | same | `KERNER SERPENTE R` |
| 4 | `BATMOBILE` | same | `KERNER SERPENTE R` |
| 5 | `BATMOBILE` | same | `KERNER SERPENTE R` |
| 6 | `BATMOBILE` | same | `KERNER SERPENTE R` |
| 7 | `BATMOBILE` | same | `KERNER SERPENTE R` |
| 8 | `BATMOBILE` | same | `KERNER SERPENTE R` |
| 9 | `BATMOBILE` | same | `KERNER SERPENTE R` |
| 10 | `BATMOBILE` | same | `KERNER SERPENTE R` |

Independent decode (`stringlookup_compare.load` on the vanilla store and the built store):

```text
languages vanilla/new: 11 11
pairs vanilla/new: 14712 14734
1621485476 | vanilla  0/11 | built 11/11 | built text ['BATMOBILE'] | name = HashJenkins(..._debug)
4081821928 | vanilla  0/11 | built 11/11 | built text ["Arkham Knight's armoured Batmobile: pursuit speed, a battle-mode turret, and armour that shrugs off small arms."] | desc = HashJenkins(..._debug_desc)
 443190071 | vanilla  0/11 | built  0/11 | built text [] | never-shipped ..._batmobile
1805638565 | vanilla  0/11 | built  0/11 | built text [] | never-shipped ..._batmobile_desc
3535039305 | vanilla 11/11 | built 11/11 | built text ['KERNER SERPENTE R'] | Serpente name (donor leaf)
2073308658 | vanilla 11/11 | built 11/11 | built text [10 translated strings] | Serpente desc (donor leaf)
```

So the Batmobile entry no longer depends on a fallback to the donor leaf: its own key resolves in
all 11 lanes, and the Serpente's name/blurb are still present and byte-identical. The old plan key
443190071 belongs to a leaf that never ships and resolves nowhere in either store — it was never
Serpente text, it was a miss.

Text source is `Working/World/bm_rebel_text.json` (`BATMOBILE` + the blurb), still English in all
11 languages: no translated text exists in the repo, so none was invented.

## 4. Item and task, re-read from the built files

```text
Batmobile: {"Name": 1621485476, "UIName": 1621485476, "UIDescription": 4081821928,
            "UIDisplayOrder": 12, "Type": 1, "UIType": 3, "UIFlag": 7,
            "RebelDropTimer": 1800, "Rewardable": 1,
            "UIImagePath_s": "v0300_car_kensington_sportsmuscle_debug",
            "UIVideoPath_s": "v0300_car_kensington_sportsmuscle_civilian_01"}
```

`task.onlinec`: 1,765 reward groups decode; the single diff is task 1980624442 `repeatable`,
`items == old + [(1621485476, 1, 0, 1, 0)]`.

## 5. `bm_rebel.py --check --tag bm-RC4-rebel` (verbatim, one line per gate)

```text
PASS sha256 profile/item.onlinec
PASS sha256 profile/task.onlinec
PASS sha256 profile/online.stringlookup
PASS sha256 textures/ui/vehicle_icons/v0300_car_kensington_sportsmuscle_debug.ddsc
PASS sha256 settings/spawn_vehicle_defs.bin
PASS item.onlinec decodes: 196 -> 197 items, 1 Batmobile
PASS all 196 vanilla items decode to the same values
PASS the other 20 fields equal the donor's
PASS icon path names textures/ui/vehicle_icons/v0300_car_kensington_sportsmuscle_debug.ddsc, present in the build
PASS task.onlinec decodes: 1765 reward groups
PASS only task 1980624442 repeatable changed: +1 ItemReward for the Batmobile
PASS settings/spawn_vehicle_defs.bin: +1 record for v0300_car_kensington_sportsmuscle_debug (9 XML lines), nothing else changed
PASS tags 'vehicle,batmobile' match 0 of 41 traffic selectors []
PASS online.stringlookup: 22 pairs added, nothing else changed
PASS the entity the item names exists in the build: Builds/bm-RC4-rebel/v0300_car_kensington_sportsmuscle_debug.ee
PASS bm_leaf.py --check: PASS: bm-RC4-rebel leaf v0300_car_kensington_sportsmuscle_debug (1621485476)
PASS: B-13 0 failure(s)
```

`bm_leaf.py --check --tag bm-RC4-rebel` itself: `(1)` `.epe` root ok, `(2)` 0 new dangling/0 new
unlisted, 0 donor-leaf refs, `(3)` 686 byte-identical, `(4)` budgets inherited delta 0 KB,
`PASS: bm-RC4-rebel leaf v0300_car_kensington_sportsmuscle_debug (1621485476)`.

## 6. Files changed, why, and how to revert

| file | change | why this file | revert |
|---|---|---|---|
| `Tools/scripts/bm_rebel.py` | `--tag` / `--entity-tag` (`set_tags`), receipt `entity` path derived from `ENTITY_TAG`, `bm_leaf --check` called with the entity tag | B-13's generator had `TAG="bm-013"` and `ENTITY_TAG=bm-013b` hard-coded; this is the only tool that writes the drop | `git checkout -- Tools/scripts/bm_rebel.py` |
| `Tools/scripts/bm_leaf.py` | `--tag`; `--check` now defaults `--src` to the receipt's `base`; a combined tag writes `receipt-leaf.json` instead of `receipt.json` | B-13b's generator had `TAG="bm-013b"` hard-coded; a single RC4 tree holds both bm_rebel's `receipt.json` and the leaf record | `git checkout -- Tools/scripts/bm_leaf.py` |
| `Builds/bm-RC4-rebel/` | new tree: `aaf/` (renamed), `drop/` (5 files), `v0300_..._debug.ee`, `receipt.json`, `receipt-leaf.json` | the requested step output | `rm -rf Builds/bm-RC4-rebel` |
| `tmp/freebuff/reports/build-d11-rebel-drop-text.md` | this report | the requested record | delete it |

Nothing was installed, no game process was started, and no game folder was read or written beyond
the read-only VFS inputs `bm_rebel.py` already opens (patch-layer `item.onlinec`, `task.onlinec`,
`online.stringlookup`, donor icon, spawn table).

## 7. Ledger state and what remains

- **T-WLD4** (name), **T-WLD6** (description) and **T-WLD11** stay `next` in the ledger: this run
  supplies the build carrier (the pair in the RC tree), and the remaining item is Q-1 runtime
  resolution. No ledger file was regenerated by this step.
- **T-WLD5** (icon) stays carried: the 18,688 B donor icon copy is in the tree; a real Batmobile
  icon is still open.
- **T-WLD8 / traffic**: 0 of 41 selectors match `vehicle,batmobile` in this build.
- Q-1 is untouched: whether the menu resolves a new record for this leaf, whether the starter grant
  re-fires on a save that already has it, and how the UI treats the donor video path are all
  runtime questions, not file questions. Nothing was launched (test ban in force).
- B-14 still has to merge this tree with the other RC4 steps and write the RC `.toc`; the `.ee` here
  has none, by design (STANDALONE.md §4.4).

## 8. UNKNOWNs

1. **Whether the Rebel Drop menu displays the pair for the `_debug` leaf** — the store is proven,
   the menu's lookup path is not decoded (Q-1).
2. **Whether the starter reward re-fires on an existing save** — repeatable reward, untested.
3. **How the UI treats `UIVideoPath` naming the donor's video** — no asset exists for the new leaf.
4. **Whether the 11 language indices map to the expected locales** — no language-name field is
   exposed by the decoder; the order is read off the text.
