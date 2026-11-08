STATUS: done — bm-RC2's `debug.epe` matches the vanilla debug graph on every matched object's property list but one, yet it **drops 34 of the original's 40 `CPartProp` objects**, and two more structural differences (the root `CCar` rename and the added `palette` member) have no entry in `Working/Entity/bm_epe_edits.json`: 87 differences, 51 tagged, 36 UNEXPLAINED.

# Fleet sanity: entity graph, bm-RC2 vs the unmodified original

## What was asked

Compare the structure of the edited `.epe` bm-RC2 ships with the unmodified original: object count,
property list per object, every property present on one side only. Tag each difference with the
`Working/Entity/bm_epe_edits.json` entry that explains it, or UNEXPLAINED. Output
`Builds/bm-RC2/verify/entity_diff.md` + `Tools/scripts/v_entity_diff.py --check`, report here.

## The two graphs

| side | file | identity |
|---|---|---|
| original | `editor/entities/.../v0300_car_kensington_sportsmuscle_debug.ee` inside `archives_win64/game35` at offset 214134784 (5,539,360 B bundle; `.epe` member 109,510 B) | extracted every run |
| built | `Builds/bm-RC2/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.epe` | sha256 `2db78866360b960dfb30183740bf14b80fafa048828610a06ab2dd0d91432b8b` |

Both go through `Gibbed.JustCause3.ConvertProperty.exe --e` (the round trip `bm_entity.py` uses), then
every `<object>`, its `_class`, its `name` value and every `<value>` member is read. Objects are
matched by `(class, name)` and, inside a name group, by document order — the exporter re-orders
siblings and renames array elements positionally, so a path match reports churn. The root `CCar` is
paired by node because the build replaced its name. Both build and original are exported to a temp
directory; the build is opened read-only and nothing is written under `_gamedata`.

## Counts

| | original | build | delta |
|---|---|---|---|
| `<object>` elements | 450 | 467 | +17 |
| with a `_class` | 449 | 466 | +17 |
| distinct classes | 43 | 46 | +3 |

`450 - 34 (dropped) + 47 (added) + 4 (extra `SEffects` copies) + 1 (the renamed root, on both sides) = 467`.

| class | original | build | delta |
|---|---|---|---|
| `CPartProp` | 40 | 6 | **-34** |
| `SVehicleLight` | 22 | 28 | +6 |
| `SEffects` | 1 | 5 | +4 |
| `SAttachedEffect` | 27 | 47 | +20 |
| `SDynamicAttachedEffectTable` | 6 | 10 | +4 |
| `SWeaponPoint` | 0 | 9 | +9 |
| `CBulletWeaponBase` | 0 | 4 | +4 |
| `CAIEntityProxy` | 0 | 4 | +4 |

## Differences, by kind

* **Added: 47 objects + 4 extra copies = 51**, all tagged to `additions[]`: `T-WP1..T-WP4` (4
  `CBulletWeaponBase`, 9 `SWeaponPoint`, 4 `CAIEntityProxy`, 5×4 effect nodes, 4 `SEffects` clones)
  and `T-L13/L14/L18/L19/L20/L35` (6 `SVehicleLight`). 47/47 resolve to a row id the spec carries.
* **Dropped: 34 objects, all `CPartProp`** — `sportsmuscle_door_f_l`, `…_door_f_r`, `…_engine`,
  `…_hood`, `…_trunk`, `…_front_bumper`, `…_rear_bumper`, `…_grill`, both seats, both mirrors,
  `…_steeringwheel`, both fenders, `…_window_f/_r_l/_r_r`, `…_trunk_window`,
  both x2 headlight props, 4 signal props, 2 plate props, `…_taillight_r_c/_r_r`,
  `…_door_f_l_window`, `…_door_f_r_window`. **UNEXPLAINED**: no entry claims them. The build's spec
  itself says `cpartprop_existing: 6` and its base is `bm-009` (the civilian variant's graph), while
  the original *debug* graph ships one `CPartProp` per part — the build renamed the civilian graph to
  the debug leaf (B-13b) and the 34 props did not come with it.
* **Replaced: the root `CCar`**, `v0300_car_kensington_sportsmuscle_generated` ->
  `…_debug` (same node, `_object_id 8F2162A5=FFFF2382`). **UNEXPLAINED** by the spec; B-13b's
  receipt step is the record that renames it.
* **Property on one side only: 1.** The root `CCar` gains `palette = 1322976751`
  (`0x4EDB05EF`). **UNEXPLAINED** by the spec; `Research/JC3Grab/PALETTE_HASH.md` records exactly this
  value on exactly this `.epe`. Every other matched object carries the identical member list on both
  sides (415/416 pairs).
* **Member values (appendix, outside the structural brief):** 440 values differ, **414 of them
  `_object_id`** — the id pair also changes on objects no edit touches (`CCameraRef/CarCameraRef`), so
  that is importer churn — and **26 are real value changes** (interaction `world` matrices, light
  members, weapon slot pointers, palette).

## Result in one line

The graph the build ships is the civilian graph renamed, plus 51 documented additions: its property
lists are intact, but it is **not** the debug graph it replaces — 34 per-part `CPartProp` entries are
missing and two structural changes (root name, `palette`) are outside the edit spec that is supposed
to account for every difference.

## Files written

| file | what |
|---|---|
| `Tools/scripts/v_entity_diff.py` | new generator; `--write` renders, `--check` re-extracts the original from the game archive, re-runs every comparison and byte-compares the page |
| `Builds/bm-RC2/verify/entity_diff.md` | the full tabulation: 47 added + 4 copies + 34 dropped + 1 renamed + 1 property, with node, `_object_id` and tag per row, the UNEXPLAINED list, oracles and labels |
| `MODLOG.md` | one appended section (intended change, why, revert) |
| this report | `tmp/freebuff/reports/fleet-sanity-entity.md` |

## Commands and output (verbatim)

```
cd "E:/Modding/JustCause3/JC3-Batmobile" && export PYTHONIOENCODING=utf-8 && set -o pipefail && python Tools/scripts/v_entity_diff.py --write; echo "EXIT write=$?"; python Tools/scripts/v_entity_diff.py --check; echo "EXIT check=$?"
wrote Builds/bm-RC2/verify/entity_diff.md (25030 bytes)
EXIT write=0
PASS original parses as 450 objects
PASS build parses as 467 objects
PASS class counts are 43 / 46
PASS 34 CPartProp objects are dropped
PASS the removed set is 34 CPartProp objects
PASS 47 objects are added
PASS 4 extra SEffects copies are added
PASS the root CCar is renamed
PASS every added/copied object is tagged
PASS every tag is a row id the spec carries
PASS the only property-list difference is on the root
PASS the added member is `palette`
PASS every matched pair was compared
PASS the census arithmetic closes
PASS UNEXPLAINED is 34 dropped + root rename + palette
oracles: 15/15 pass
document identical: Builds/bm-RC2/verify/entity_diff.md
EXIT check=0
```

## UNKNOWNs

* **Whether the 34 missing `CPartProp` objects matter in game.** They carry `name`, `name_hash`,
  `part_index`, `_object_id` and `_GUID` only — no physics or damage member (B-05's own note: no
  `CPartProp` carries a behaviour). What the engine does with a part that has no prop is not decoded
  in any repo file; the test ban stands. Recorded as a structural loss, not as a proven fault.
* **Where the `palette` member comes from.** The value is documented (`PALETTE_HASH.md`) and the member
  exists only in the build; which build step adds it (the palette patch or the importer) is not in
  `bm_epe_edits.json`, and I did not infer it.
* **Whether the root rename is safe.** `B-13b` renames the graph root deliberately and the `.ee`/`.toc`
  point at the debug leaf (build receipt), but no repo file proves the root `CCar` name is free to
  differ from `<leaf>_generated`. Stated, not resolved.

## COMPROMISES

* The shipped entity graph is **not** the vanilla debug graph: **34 of 40 `CPartProp` objects are
  absent**, which is a fleet-sanity deviation the operator must approve or schedule (either restore
  them from the vanilla debug graph or declare the civilian graph canonical). Nothing was changed in
  the build here.
* Two structural differences — the root `CCar` name and the `palette` member — are **not covered by
  `bm_epe_edits.json`**, so the edit spec no longer accounts for every difference between the built
  graph and its original; the spec needs a row each, or the receipt needs to be the documented home.
* No install, launch, attach or payload edit; the only new file inside `Builds/bm-RC2/` is the
  requested `verify/entity_diff.md`.
