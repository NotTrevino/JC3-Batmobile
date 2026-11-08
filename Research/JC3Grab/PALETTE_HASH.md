# The palette reference in the Serpente entity (G3-09 review follow-up)

The review of G3-09 rejected that card's claim *"no `.rbm`, `.epe` or `.vmodc` of the entity names the palette, so the binding is engine-side"* and pointed at two 32-bit words in the donor's own `.epe`. This card checks those words in the bytes, names them with the project's own hash function, resolves the one that is a path hash, and decodes the asset. Nothing was launched, built, or written outside this card's files.

## 1. Answer

**`0x6187A56B` is not the palette.** It is `hash_jenkins("palette")`, the *name* of the module slot; the word immediately after it, **`0xC023BA54`, is the asset reference**: `hash_jenkins` of the palette module's full VFS path. The asset is

```
editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_palette.vmodc
```

a **1897-byte ADF v4** file holding the vehicle's 10 tint records.

`Black` is entry 3: RGB (0.200000, 0.200000, 0.200000) with gloss 0.000000, metallic 0.000000, coat 1.000000 - `0.2` per channel, stored as a float in the file.

So the pairing the review found is real, but its label needs one correction: the palette *hash* is `0xC023BA54` (the value); `0x6187A56B` is the hash of the word `palette`, i.e. the key the entity files its palette module under. Both statements are decoded below.

## 2. Verifying the offset in the actual `.epe` bytes

The `.epe` is the one **inside the archived `.ee`** (`editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.epe`, 109526 B, sha256 `f67bc17ebb16b70f…`), read through `bm_rc.vfs` + `eetoc.unaaf` + `eetoc.sarc_dir`; a loose unpacked copy is checked as a second witness.

| copy | bytes | `0x6187A56B` at | `0xC023BA54` at | adjacent pair |
|---|---:|---|---|---|
| archive (.ee inner SARC) | 109526 | 0x266 | 0x26a | 0x266 |
| loose unpack (b13b) | 105430 | 0x266 | 0x26a | 0x266 |

Bytes around the pair (from `0x25e`):

```
d1 cc 60 1c 08 00 00 0e 6b a5 87 61 54 ba 23 c0 01 fc d1 fb 61 20 08 00
```

Each word occurs exactly once in that file and the two are adjacent, in that order, so the pair is one record rather than two coincidences: a `u32` pair at `0x266`.

## 3. Naming the words with `hash_jenkins`

`rbmhdr.hash_jenkins` is Gibbed's `StringHelpers.HashJenkins` ported byte for byte; `jc3index.py` uses it to name archive `.tab` entries and it is the same function `MODLOG` records as matching 78,907 VFS paths. Candidates are the module word and the file names beside the colour data - no name was taken from memory.

| label | string | `hash_jenkins` | is the name word | is the value word |
|---|---|---|---|---|
| module word | `palette` | `6187A56B` | **yes** |  |
| module word, capitalised | `Palette` | `8A7F58A7` |  |  |
| module word, upper | `PALETTE` | `B8452363` |  |  |
| module word + extension | `palette.vmodc` | `791797EE` |  |  |
| palette module leaf | `v0300_car_kensington_sportsmuscle_palette` | `28F7A2BF` |  |  |
| palette module leaf + extension | `v0300_car_kensington_sportsmuscle_palette.vmodc` | `8FC55696` |  |  |
| palette module path | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sp…` | `C023BA54` |  | **yes** |
| damage module word | `damage` | `4F489F01` |  |  |

Exactly one candidate hits each word, and the nearest variants (capitalised, upper, with `.vmodc`, leaf only) miss - the recipe is not being fitted to the target.

## 4. Resolved by the `.ee`'s own directory, not by a table

The vehicle's `.ee` contains 566 inner files. Hashing each of their names and looking the two words up resolves the *value* word to a file the container actually ships:

| lookup | hash | inner file | offset | size |
|---|---|---|---:|---:|
| value word | `0xC023BA54` | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_palette.vmodc` | 12294464 | 1897 |
| damage slot | `670155287` | `editor/entities/jc_vehicles/00_shared/modules/health/lave_health_medium.vmodc` | 12280672 | 3741 |

The second slot is the control: `0x4F489F01` is `hash_jenkins("damage")` (match) and its value resolves the same way, so the record shape is *(module name hash, module path hash)*, exactly as `MODLOG`/B-09 describe the root `damage` hash. The file the `damage` slot names is the shared health module `lave_health_medium.vmodc`, i.e. the entity's damage model.

Scanning every 4-byte word of the `.epe` against the container's name hashes resolves **459** module references across **53** distinct files - the mechanism is not a one-off. Counted per file, first offset shown:

| module file | refs | first offset |
|---|---:|---|
| `notire_asphalt.effc` | 92 | `0x6b34` |
| `rear_asphalt.effc` | 88 | `0x6194` |
| `chassis_impact_default.effc` | 74 | `0x6568` |
| `chassis_slide_default.effc` | 28 | `0x74c4` |
| `dust_trail_asphalt.effc` | 24 | `0xd444` |
| `rear_dirt.effc` | 20 | `0x61d0` |
| `notire_dirt.effc` | 16 | `0x6b84` |
| `def_default.effc` | 14 | `0x6ed8` |
| `chassis_impact_dirt.effc` | 12 | `0x65b8` |
| `def_dirt.effc` | 4 | `0x6f00` |
| `def_metal.effc` | 4 | `0x6fb4` |
| `notire_grass.effc` | 4 | `0x6bac` |
| `notire_gravel.effc` | 4 | `0x6b5c` |
| `notire_sand.effc` | 4 | `0x6b48` |
| `notire_snow.effc` | 4 | `0x6bd4` |
| `notire_water.effc` | 4 | `0x6bc0` |
| `rear_grass.effc` | 4 | `0x620c` |
| `rear_gravel.effc` | 4 | `0x61bc` |
| `rear_sand.effc` | 4 | `0x61a8` |
| `rear_snow.effc` | 4 | `0x6234` |
| `rear_water.effc` | 4 | `0x6220` |
| `chassis_impact_sand.effc` | 3 | `0x657c` |
| `chassis_impact_snow.effc` | 3 | `0x6608` |
| `def_concrete.effc` | 3 | `0x6eb0` |
| `dust_trail_dirt.effc` | 3 | `0xd494` |
| `chassis_impact_vegetation.effc` | 2 | `0xc2e0` |
| `chassis_impact_water.effc` | 2 | `0x6658` |
| `dust_trail_grass.effc` | 2 | `0xd480` |
| `chassis_slide_dirt.effc` | 1 | `0x7528` |
| `chassis_slide_sand.effc` | 1 | `0x74d8` |
| `chassis_slide_snow.effc` | 1 | `0x7564` |
| `chassis_slide_vegetation.effc` | 1 | `0x7500` |
| `def_blood.effc` | 1 | `0x70a4` |
| `def_grass.effc` | 1 | `0x6f28` |
| `def_sand.effc` | 1 | `0x6ec4` |
| `def_snow.effc` | 1 | `0x6f50` |
| `def_stone.effc` | 1 | `0x6f78` |
| `def_vegetation.effc` | 1 | `0x6eec` |
| `def_water.effc` | 1 | `0x6f3c` |
| `dmg_engine_drips.effc` | 1 | `0xa134` |
| `dmg_engine_ground_flames.effc` | 1 | `0x79f0` |
| `dust_trail_sand.effc` | 1 | `0xd458` |
| `dust_trail_snow.effc` | 1 | `0xd4e4` |
| `dust_trail_water.effc` | 1 | `0xd4d0` |
| `headlight_break_on_01.effc` | 1 | `0x1c8` |
| `sportsmuscle.physicsc` | 1 | `0xf0` |
| `v0300_car_kensington_sportsmuscle_custom_velocity_damper.vmodc` | 1 | `0x27c` |
| `v0300_car_kensington_sportsmuscle_effect_attachments.vmodc` | 1 | `0x5dc` |
| `v0300_car_kensington_sportsmuscle_land_engine.vmodc` | 1 | `0x2a0` |
| `v0300_car_kensington_sportsmuscle_land_steering.vmodc` | 1 | `0x1ec` |
| `v0300_car_kensington_sportsmuscle_rear_tire.vmodc` | 1 | `0x2c4` |
| `v0300_car_kensington_sportsmuscle_vehicle_misc.vmodc` | 1 | `0x330` |
| `v0300_car_kensington_sportsmuscle_water_interaction.vmodc` | 1 | `0x498` |

## 5. Where the two words are **not** (every name space searched)

| space | size | `0x6187A56B` | `0xC023BA54` |
|---|---:|---:|---:|
| VFS index (`INDEX.jsonl`, unique paths) | 78907 | 0 | 0 |
| JCMR dictionary (`dictionary.json`, keys) | 181740 | 0 | 0 |
| archive `.tab` name tables | 88 files | 0 | 0 |
| `_gamedata/JC3grab` raw `.epe`/`.ee`/`.vmodc`/`.blo`/`.tab`/`.stringlookup` | 234 files | 5 | 3 |

The zeroes are the finding, not a gap: the palette module is **packed inside the vehicle's own `.ee`**, so no archive `.tab` and no index row can name it. The value resolves only by recipe (hashing the path) and by the container's own directory - which is exactly how the engine finds it, since JC3 addresses by hash.

Raw `u32` hits under `_gamedata/JC3grab` (offsets are in the hit file):

| file | bytes | hits |
|---|---:|---|
| `b13b/unpacked/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.epe` | 105430 | `0x6187A56B`@0x266, `0xC023BA54`@0x26a |
| `rc_merge/stage/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.epe` | 124344 | `0x6187A56B`@0x296 |
| `rc_merge/verify/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.epe` | 124328 | `0x6187A56B`@0x296 |
| `sigdiff/civilian.ee.epe` | 109526 | `0x6187A56B`@0x266, `0xC023BA54`@0x26a |
| `sigdiff/civilian.epe` | 109526 | `0x6187A56B`@0x266, `0xC023BA54`@0x26a |

Two further copies under `_gamedata/JC3grab/rc_merge` (this project's build staging) carry the name word at `0x296` followed by `0x4EDB05EF`, not the palette path hash. They are merged-graph variants and this card does not interpret them.

Base rate: 400 random 4-40 character names produce 0 hits in the 109526-byte `.epe` and 0 in the palette, so the matches above are not what random 32-bit words do in these files.

## 6. The asset, decoded

`editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_palette.vmodc` - **1897 B**, sha256 `6e2c4615535de834…`, ADF v4, header total 1897 (equals its length), 1 instance, types `A[Tint]`, `ColorRGBA`, `HashString`, `Palette`, `Tint`.

| # | name | occurrence | R = G = B | A | gloss | metallic | coat |
|---:|---|---:|---|---:|---:|---:|---:|
| 0 | White | 100 | (0.880000, 0.880000, 0.880000) | 1.000000 | 0.000000 | 0.000000 | 1.000000 |
| 1 | Evergreen Pearl | 100 | (0.094118, 0.229412, 0.164706) | 1.000000 | 0.450000 | 1.000000 | 1.000000 |
| 2 | Garnet Red Metallic | 100 | (0.426471, 0.050000, 0.050000) | 1.000000 | 0.450000 | 1.000000 | 1.000000 |
| 3 | Black | 100 | (0.200000, 0.200000, 0.200000) | 1.000000 | 0.000000 | 0.000000 | 1.000000 |
| 4 | Grey | 100 | (0.410667, 0.410667, 0.410667) | 1.000000 | 0.450000 | 1.000000 | 1.000000 |
| 5 | Silver | 100 | (0.424000, 0.424000, 0.424000) | 1.000000 | 0.450000 | 1.000000 | 1.000000 |
| 6 | Blue | 100 | (0.218667, 0.322667, 0.458667) | 1.000000 | 0.450000 | 1.000000 | 1.000000 |
| 7 | Brown | 100 | (0.432000, 0.389333, 0.384000) | 1.000000 | 0.450000 | 1.000000 | 1.000000 |
| 8 | Red | 100 | (0.538667, 0.200000, 0.200000) | 1.000000 | 0.450000 | 1.000000 | 1.000000 |
| 9 | Green | 100 | (0.200000, 0.424000, 0.200000) | 1.000000 | 0.450000 | 1.000000 | 1.000000 |

**JC3 `Black` is entry 3**: `tint_r/g/b` (0.200000, 0.200000, 0.200000), and the four bytes at `0x184` are `cd cc 4c 3e` = `0.20000000f`, i.e. **0.2** stored as a float - the value is in the file, not inferred.

Byte check - each record re-read from its own `0x94 + 0x50*k` (7 floats: R, G, B, A, gloss, metallic, coat) and compared with the ADF walk:

| # | offset | floats from bytes | equals ADF |
|---:|---|---|---|
| 0 | `0x94` | 0.880000, 0.880000, 0.880000, 1.000000, 0.000000, 0.000000, 1.000000 | yes |
| 1 | `0xe4` | 0.094118, 0.229412, 0.164706, 1.000000, 0.450000, 1.000000, 1.000000 | yes |
| 2 | `0x134` | 0.426471, 0.050000, 0.050000, 1.000000, 0.450000, 1.000000, 1.000000 | yes |
| 3 | `0x184` | 0.200000, 0.200000, 0.200000, 1.000000, 0.000000, 0.000000, 1.000000 | yes |
| 4 | `0x1d4` | 0.410667, 0.410667, 0.410667, 1.000000, 0.450000, 1.000000, 1.000000 | yes |
| 5 | `0x224` | 0.424000, 0.424000, 0.424000, 1.000000, 0.450000, 1.000000, 1.000000 | yes |
| 6 | `0x274` | 0.218667, 0.322667, 0.458667, 1.000000, 0.450000, 1.000000, 1.000000 | yes |
| 7 | `0x2c4` | 0.432000, 0.389333, 0.384000, 1.000000, 0.450000, 1.000000, 1.000000 | yes |
| 8 | `0x314` | 0.538667, 0.200000, 0.200000, 1.000000, 0.450000, 1.000000, 1.000000 | yes |
| 9 | `0x364` | 0.200000, 0.424000, 0.200000, 1.000000, 0.450000, 1.000000, 1.000000 | yes |

`metallic = 1.0` in records 1, 2, 4, 5, 6, 7, 8, 9 (8 of 10) - the number the review counted, re-read here from the bytes.


## 7. Claims in `COLOUR.md` that this refutes

`COLOUR.md` was not edited. These are the statements the bytes above contradict, with the part of that file they live in:

| # | `COLOUR.md` says | measured |
|---|---|---|
| 1 | §4: *"No `.rbm`, `.epe` or `.vmodc` of the entity names the palette, so the binding is engine-side (spawn/vehicle-system), not an asset reference."* | the entity's own `.epe` carries `hash_jenkins("palette")` followed by the palette module's path hash at `0x266`; the palette **is** an asset reference of the entity |
| 2 | §6 UNKNOWN 2: *"The palette -> block binding is not in any of the 566 files."* | it is in the `.epe`, one of those 566 files; the ASCII scan used to test it cannot see a hash by construction |
| 3 | §4/check 9: *"no file in the bundle references the palette except the palette itself"* | the check asserts the false statement, so `--check` passing does not cover it |
| 4 | §4: *"the five 'metallic' tints"* | eight records carry `metallic = 1.0` (8 of 10); that card's own table is right and its prose is not |
| 5 | §4/check 11: *"77 floats … for the 10 tints plus the palette root's own default record"* | the seven `palette.*` offsets are the seven `tints[9].*` offsets; there is no 11th record (the file declares one instance) |
| 6 | §5 prose: *"no file in JC3's index is named for … a time of day"* | that card's own table counts `time_of_day` = 2 (`msub_time_of_day.gdc`/`.gsc`) |
| 7 | §5 table rows `sky` 3,364 / `sun` 31 as lighting evidence | substring counts whose own examples are false positives (`…_skyshield_…`, `…_boatsunk_…`) |

One correction to the review itself, for the record: it gives the `.epe` as 109,526 B, which is the **archive** size; the loose unpacked copy under `_gamedata/b13b` is 105430 B. The pair is at `0x266` in both, so the finding stands, but the two files are not the same bytes.

## 8. Oracles

Each line is recomputed from the source bytes by `--check`; the document is only written when all pass.

- **PASS** the pair sits at 0x266/0x26a in the archived .epe
- **PASS** both words also occur in the loose unpacked copy at the same relative pair
- **PASS** hash_jenkins('palette') == 0x6187A56B
- **PASS** hash_jenkins(<palette module path>) == 0xC023BA54
- **PASS** exactly one name in the candidate table hits the name word
- **PASS** the .ee's own directory resolves 0xC023BA54 to the palette module
- **PASS** the same shape resolves the damage slot (0x4F489F01 -> 670155287)
- **PASS** no VFS index path hashes to either word
- **PASS** no archive .tab carries either word as a name hash
- **PASS** every scanned tint equals its own bytes at 0x94 + 0x50*k
- **PASS** the palette's ADF header total equals its length
- **PASS** 400 random names hit neither the .epe nor the palette

## 9. What is still UNKNOWN

1. **Which tint the engine selects for a given spawn, and whether it copies that tint into the CarPaintMM dynamic float4s.** The `.epe` says *which palette module* the entity uses; it carries no selected index, and the palette's `occurrence` field is 100 for every record. The coupling to the block lives in the render/material code, not in these files. Tried: the `.epe` property table (one int per module slot, no index), the palette bytes (no selector), and the dynamic payload of the paint blocks (`COLOUR.md` §1, identical on blocks 6/7/8).
2. **The 0.2/0.45 relationship.** `Black` is `(0.2, 0.2, 0.2)` with gloss 0 / metallic 0 / coat 1; the paint blocks' own override triple is `(0.4, 1, 1)`. No file maps one to the other, so no write-back is claimed.
3. **Whether other vehicles use the same palette path hash.** This card checks one entity. A fleet-wide census of `(palette name hash, value hash)` pairs across all vehicle `.epe` files is a separate measurement and is not claimed here.

## 10. Reproduce

```
python Tools/scripts/jc3_palette_hash.py --write
python Tools/scripts/jc3_palette_hash.py --check
```

