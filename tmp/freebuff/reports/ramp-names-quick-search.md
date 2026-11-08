# Ramp names: grep of the generated name tables

Search only, no extraction. Written 2026-11-06. Every line number below is a decoded
file offset (a printed line in a generated table), not a game address.

**Scope, both roots named by the brief:**

| root | files | what it is |
|---|---|---|
| `Research/BatmobileGrab` | 230 files | the generated material / texture / skin / slot dumps (`*.md`, `*.json`, `*.jsonl`, `list_*.txt`) |
| `E:/Modding/_gamedata/BmAKgrab` | 2,363 files, 862 of them text-ish | a mesh / animation / audio working area: top-level `chase2_09_packages.json`, `motion.txt`, and `anims/ audio/ bones/ chase/ gltf/ gltf_test/ lodtest/ lodtest2/ meshes/ umodelcfg/` |

Method: fixed-string (`grep -F`, so `_` and case are literal), case-sensitive,
recursive over both roots, `--binary-files=without-match`. Command form:

```
grep -rnoF "<name>" Research/BatmobileGrab E:/Modding/_gamedata/BmAKgrab
```

## 0. Headline

All three names were found. **138 hits total — 87 / 33 / 18 — and every one of them is
in `Research/BatmobileGrab`. `E:/Modding/_gamedata/BmAKgrab` returned 0 hits for all
three**, which is expected: that tree holds no material, texture or name index (see §4).

| name | hits | files | in BmAKgrab |
|---|---|---|---|
| `Batman_BM3_V2_Lacquered_Underlayer_Ramp` | 87 | 13 | 0 |
| `Batman_BM3_V2_Leather_Ramp` | 33 | 11 | 0 |
| `Batmobile_V3_Body_ColourRamp` | 18 | 6 | 0 |

## 1. `Batman_BM3_V2_Lacquered_Underlayer_Ramp` — 87 hits, 13 files

| file | lines | what the line is |
|---|---|---|
| `Research/BatmobileGrab/COCKPIT.json` | 665 | `Colour_Ramp_Map` slot value on `Batmobile_V3_Cockpit_MIC` |
| `Research/BatmobileGrab/COCKPIT.md` | 31 | same slot, rendered row |
| `Research/BatmobileGrab/COLOUR.json` | 342, 750 | emitted texture-parameter record, twice |
| `Research/BatmobileGrab/COLOUR.md` | 70 | `Colour_Ramp_Map` / `Batmobile_V3_WheelArchs_NEW_MIC` / #767 / guid `e9632f4f` |
| `Research/BatmobileGrab/COLOUR_FUNCTIONS.json` | 4491, 4576 | two material-graph function dumps that carry the value |
| `Research/BatmobileGrab/COLOUR_PARAMS.json` | 3077 | `"object"` field of the texture parameter |
| `Research/BatmobileGrab/COLOUR_PARAMS.md` | 79 | the parameter row (texture, #-588, guid `e9632f4f`, field `0x158`) |
| `Research/BatmobileGrab/MATERIALS.md` | 969, 970, 976, 1004, 1005, 1011, 1028, 1029, 1036, 1059, 1060, 1068, 1091 | skin material tables (13 rows across the 5 playable skin packages) |
| `Research/BatmobileGrab/SKINS.json` | 935, 2098, 2628, 7627, 8503, 9018, 9548, 13272, 13646, 14093, 14969, 15484, 16014, 20682, 21056, 21503, 22379, 22894, 23424 | per-skin texture-parameter records |
| `Research/BatmobileGrab/SKINS.md` | 210, 219, 232, 258, 279, 299, 378, 387, 400, 426, 447, 467, 571, 597, 618, 638, 742, 786, 806 | the same, rendered |
| `Research/BatmobileGrab/SLOTS.json` | 78, 209, 268 | material-slot tables |
| `Research/BatmobileGrab/SLOTS.md` | 28, 35, 38 | material-slot tables, rendered |
| `Research/BatmobileGrab/objects.jsonl` | 707, 712, 850, 851, 857, 6481, 6486, 6615, 6616, 6622, 9638, 9643, 9784, 9785, 9792, 15148, 15153, 15280, 15281, 15289, 20098 | object-index lines (a line repeats because the name occurs more than once on that one JSONL line; it is one line, several occurrences) |

## 2. `Batman_BM3_V2_Leather_Ramp` — 33 hits, 11 files

| file | lines | what the line is |
|---|---|---|
| `Research/BatmobileGrab/ASSETS.md` | 360, 530, 689, 854 | `Texture2D` name list, one per skin package |
| `Research/BatmobileGrab/COCKPIT.json` | 692 | `Colour_Ramp_Map` slot value on `BatmobileV3_Cockpit_Seat` (`Maps.` prefix) |
| `Research/BatmobileGrab/COCKPIT.md` | 33 | same slot, rendered row |
| `Research/BatmobileGrab/MATERIALS.md` | 973, 1008, 1032, 1063 | seat material row, one per skin |
| `Research/BatmobileGrab/SKINS.json` | 2414, 9334, 15800, 23210 | per-skin texture-parameter records |
| `Research/BatmobileGrab/SKINS.md` | 287, 455, 626, 794 | the same, rendered (`#5399` at 287, `#422` at 455) |
| `Research/BatmobileGrab/SLOTS.json` | 233 | material-slot table |
| `Research/BatmobileGrab/SLOTS.md` | 36 | material-slot table, rendered |
| `Research/BatmobileGrab/TEXTURES.md` | 8, 111, 212, 308 | texture rows, one per skin package |
| `Research/BatmobileGrab/list_Playable_Batmobile_SF.txt` | 5402 | package name table: `5398  1FED779  766 Texture2D Batman_BM3_V2_Leather_Ramp` |
| `Research/BatmobileGrab/objects.jsonl` | 854, 5483, 6619, 8877, 9788, 14420, 15284, 19921 | object index: `Texture2D` records #5483 / #3289 / #5440 / #5399 (one per package) plus the `BatmobileV3_Cockpit_Seat` MICs |

## 3. `Batmobile_V3_Body_ColourRamp` — 18 hits, 6 files

| file | lines | what the line is |
|---|---|---|
| `Research/BatmobileGrab/MATERIALS.md` | 971, 1006, 1030, 1061 | `Batmobile_V3_Emissive` row, one per skin |
| `Research/BatmobileGrab/SKINS.json` | 1263, 7955, 14421, 21831 | per-skin texture-parameter records |
| `Research/BatmobileGrab/SKINS.md` | 241, 409, 580, 751 | the same, rendered (`Colour_Ramp_Map`=`Batmobile_V3_Body_ColourRamp`) |
| `Research/BatmobileGrab/SLOTS.json` | 117 | slot table: `"Colour_Ramp_Map": "Engine.Batmobile_V3_Body_ColourRamp"` |
| `Research/BatmobileGrab/SLOTS.md` | 30 | slot 5, `Batmobile_V3_Emissive`, base `Engine.Batmobile_V3_Body_MAT` |
| `Research/BatmobileGrab/objects.jsonl` | 852, 6617, 9786, 15282 | `Batmobile_V3_Emissive` MIC records, one per package |

## 4. Names with no hit — `E:/Modding/_gamedata/BmAKgrab`

Zero hits for all three names. Files searched there: all 2,363 files under the root
(non-binary content read), including the two top-level files
`chase2_09_packages.json` and `motion.txt` and every file under `anims/`, `audio/`,
`bones/`, `chase/`, `gltf/`, `gltf_test/`, `lodtest/`, `lodtest2/`, `meshes/`,
`umodelcfg/`.

**This absence is not evidence about the game.** That tree contains no material,
texture or name index at all (its 862 text files are mesh, animation and audio
sidecars), so a ramp name has nothing there to be written into. The only place these
names are indexed is `Research/BatmobileGrab`.

## 5. What the hits already settle, in one line each

- **Lacquered Underlayer** is the `Colour_Ramp_Map` of `Batmobile_V3_Cockpit_MIC` and,
  via MIC #767 (`Batmobile_V3_WheelArchs_NEW_MIC`), it overrides the same
  `e9632f4f` slot that the tyre ramp holds in the master — `COLOUR_PARAMS.md:79`,
  `COLOUR.md:70`.
- **Leather** is the `Colour_Ramp_Map` of `BatmobileV3_Cockpit_Seat`, and its texture
  object genuinely exists in the packages: `#5399` in `Playable_Batmobile_SF`
  (`SKINS.md:287`, `objects.jsonl:19921`), `#422` in another skin (`SKINS.md:455`).
- **Body_ColourRamp** is slot 5, `Batmobile_V3_Emissive`, base
  `Engine.Batmobile_V3_Body_MAT` — `SLOTS.md:30`.

Nothing here changes a ledger row; this page is a locator index only.

## 6. Limits of this search

- Case-sensitive exact string, as spelled in the brief. Lower-case or shortened forms
  (`Batman_BM3_V2_*Ramp`, `Body_ColourRamp`) were not searched, and neither were the
  unprefixed tails of the names.
- Binaries (`.upk`, `.tfc`, mesh and audio payloads) were not grepped, so a name that
  appears only inside a package is not listed here; the generated tables are the
  authority for what the packages contain.
- Line numbers are line numbers in the generated files at the time of the run; a
  regeneration of those tables (`Tools/scripts` writers) will move them.
