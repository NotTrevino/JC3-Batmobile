# COLOUR-palette · What the Serpente `.epe` palette words are — card report

**STATUS: done.** `0x6187A56B` is verified at `0x266` in the archived `.epe` (and in the loose
unpacked copy) and is **not** the palette: it is `hash_jenkins("palette")`, the module-slot
*name*. The word after it, `0xC023BA54`, is the asset reference — `hash_jenkins` of
`editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/
v0300_car_kensington_sportsmuscle_palette.vmodc`, the 1,897-byte ADF v4 palette that ships
**inside the vehicle's own `.ee`** (offset 12,294,464) and decodes to the 10 tint records, `Black`
= `(0.2, 0.2, 0.2)` at `0x184`. The review's finding is confirmed with one label correction, and
the palette is proven to be an asset reference of the entity. `COLOUR.md` was not edited; its
refuted claims are listed in §3 below and in the deliverable's §7.

## Files written

| file | what |
|---|---|
| `Tools/scripts/jc3_palette_hash.py` | new; `--write` generates `Research/JC3Grab/PALETTE_HASH.md`, `--check` re-derives every number and all 12 oracles from the source bytes and compares the document byte for byte, `--dump` prints the JSON payload |
| `Research/JC3Grab/PALETTE_HASH.md` | the deliverable (answer, offset verification, candidate-hash table, container resolution, the "not found" table, the decoded palette with the per-record byte check, refuted claims, oracles, UNKNOWNs) |
| `tmp/freebuff/scratch/pal1.py`, `pal2.py` | scratch probes (nothing depends on them) |
| `tmp/freebuff/reports/COLOUR-palette.md` | this report |

Not touched: `Research/JC3Grab/COLOUR.md`, `COLOUR.json`, any other task's files, `Builds/`,
`D:/Games`, `E:/Modding/_gamedata` (read only), git.

## Commands run, with output

### 1. The `.epe` bytes at the review's offset

```
$ python - <<'EOF'   (read b13b/unpacked/...civilian_01.epe, print 0x240..0x280, find 6b a5 87 61)
len 105430
0x240 92 01 c4 70 c9 5d 14 08 00 00 0e 8d 5d 12 5f 00 00 70 41 02 1c 72 55 5f 18 08 00 00 0e 2a d1 cc 60 1c 08 00 00 0e 6b a5 87 61 54 ba 23 c0 01 fc
0x250 00 70 41 02 1c 72 55 5f 18 08 00 00 0e 2a d1 cc 60 1c 08 00 00 0e 6b a5 87 61 54 ba 23 c0 01 fc d1 fb 61 20 08 00 00 0e 4e 2a d6 63 94 73 da 20
hit at 0x266
```

### 2. First hash attempt — wrong function, discarded

```
$ python tmp/freebuff/scratch/pal1.py     (naive Jenkins one-at-a-time)
--- direct values
0x66771820 palette
0x893f167c editor/entities/jc_vehicles/01_land/v0300_car_kensington_spo
0x758d9884 v0300_car_kensington_sportsmuscle_palette
```
No match. Discarded: JC3 uses `StringHelpers.HashJenkins` (lookup3), not the one-at-a-time
variant. This is why the candidate table is printed in full rather than one asserted value.

### 3. With the project's calibrated function (`rbmhdr.hash_jenkins`)

```
$ python tmp/freebuff/scratch/pal2.py
6187A56B  palette   want 6187A56B MATCH
8A7F58A7  Palette
B8452363  PALETTE
791797EE  palette.vmodc
28F7A2BF  v0300_car_kensington_sportsmuscle_palette

C023BA54  editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_palette.vmodc
C9CEFEAA  editor/entities/.../v0300_car_kensington_sportsmuscle_palette
28F7A2BF  v0300_car_kensington_sportsmuscle_palette
8FC55696  v0300_car_kensington_sportsmuscle_palette.vmodc
target value hash 0xC023BA54 = 3223566932
```

### 4. The `.epe` the game actually loads, and its format

```
$ python - <<'EOF'   (bm_rc.vfs + eetoc.unaaf + eetoc.sarc_dir on the .ee)
archive epe 109526 b'RTPC\x01\x00\x00\x00*R}\xaa\x14\x00\x00\x00'
0x266 bytes 18 08 00 00 0e 2a d1 cc 60 1c 08 00 00 0e 6b a5 87 61 54 ba 23 c0 01 fc d1 fb 61 20 08 00 00 0e 4e 2a d6 63 94 73 da 20
6187A56B ['0x266']
C023BA54 ['0x26a']
ADF fail not an ADF file: 0x43505452
```

### 5. Reverse tables that could have named the asset

```
$ python - <<'EOF'   (hash_jenkins over every unique INDEX.jsonl path, then dictionary.json)
tabs 88 ['D:/Games/Just Cause 3\\archives_win64\\game0.tab', ...]
unique paths 78907 in 4.1s
index hits []
dict type <class 'dict'> 181740
dict keys with sportsmuscle_palette []
BUNDLE editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.ee
```

### 6. The deliverable

```
$ uv run --with pefile python Tools/scripts/jc3_palette_hash.py --write
wrote E:\Modding\JC3-Batmobile\Research\JC3Grab\PALETTE_HASH.md
  name word 0x6187A56B at 0x266
  value word 0xC023BA54 -> editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_palette.vmodc
  palette 1897 B, 10 tints
  oracles 12/12
write_exit=0

$ uv run --with pefile python Tools/scripts/jc3_palette_hash.py --check
OK 12/12 oracles, 1897 B palette, 10 tints, md byte-identical
check_exit=0
```

### 7. The `rc_merge` variants (not interpreted)

```
v0300_car_kensington_sportsmuscle_civilian_01.epe 124344 0x296 value 0x4edb05ef 1322976751
v0300_car_kensington_sportsmuscle_debug.epe       124328 0x296 value 0x4edb05ef 1322976751
```

## The values, labelled

### decoded
- `0x6187A56B` at `0x266` and `0xC023BA54` at `0x26a`, both once each, in the archived `.epe`
  (109,526 B, sha256 `f67bc17ebb16b70f…`) and in the loose copy under `_gamedata/b13b` (105,430 B,
  same offsets). Bytes at `0x25e`: `d1 cc 60 1c 08 00 00 0e 6b a5 87 61 54 ba 23 c0 01 fc …`.
- `hash_jenkins("palette") == 0x6187A56B`; `hash_jenkins(<palette module path>) == 0xC023BA54`;
  the capitalised, upper, `.vmodc`-suffixed and leaf-only spellings do not hit either.
- The `.ee`'s 566-entry directory hashed by name resolves `0xC023BA54` to
  `…_palette.vmodc`, offset 12,294,464, size 1,897.
- `0x4F489F01 = hash_jenkins("damage")` and its value 670,155,287 resolves in the same directory
  to `editor/entities/jc_vehicles/00_shared/modules/health/lave_health_medium.vmodc` (3,741 B).
- The palette: ADF v4, header total 1,897 = length, 1 instance, types `A[Tint]`, `ColorRGBA`,
  `HashString`, `Palette`, `Tint`; 10 records; `Black` at `0x184` = `cd cc 4c 3e` =
  `0.20000000f`, with gloss 0, metallic 0, coat 1; every record re-read from `0x94 + 0x50*k`
  equals the ADF walk (10/10); `metallic = 1.0` in 8 of 10.
- 459 module references in the `.epe` (4-byte words equal to a hash of one of the container's own
  file names), across 53 distinct files.
- Not searched-and-missed: 0 hits in 78,907 VFS index paths, 0 in 181,740 dictionary keys,
  0 in 88 archive `.tab` name tables; 5 hits for the name word and 3 for the value word across the
  234 `.epe`/`.ee`/`.vmodc`/`.blo`/`.tab`/`.stringlookup` files under `_gamedata/JC3grab`
  (the `.epe` copies only).

### derived
- The record shape is *(module name hash, module path hash)*: the `damage` control slot has the
  same shape and resolves to a file the container ships, and 459 further words do the same. So
  the palette is an **asset reference of the entity**, and `0x6187A56B` names the slot rather
  than the asset.
- The palette module is packed inside the entity's `.ee`, which is why no `.tab`, index row or
  dictionary key can name it: the engine resolves it by hashing the path, exactly as the `.epe`
  stores it.

### UNKNOWN
- **Which tint a spawn selects, and whether that tint reaches the CarPaintMM dynamic float4s.**
  The `.epe` names the module, not an index; every palette record has `occurrence = 100`. Where
  it would be found: the vehicle/material code in the executable, or a runtime constant dump.
- **Any write-back between the palette's numbers and the paint blocks'** `(0.4, 1, 1)` override
  triple. No file maps one to the other.
- **Whether other vehicles reuse the same palette path hash.** One entity measured here.

## COLOUR.md claims refuted (file not edited)

1. §4 *"No `.rbm`, `.epe` or `.vmodc` of the entity names the palette, so the binding is
   engine-side … not an asset reference"* — false; the `.epe` carries the pair at `0x266`.
2. §6 UNKNOWN 2 *"the palette → block binding is not in any of the 566 files"* — it is in the
   `.epe`, one of those 566; the ASCII scan used to test it cannot see a hash.
3. §4 / check 9 *"no file in the bundle references the palette except the palette itself"* — the
   check asserts the false statement.
4. §4 *"the five 'metallic' tints"* — eight records have `metallic = 1.0`.
5. §4 / check 11 *"77 floats … for the 10 tints plus the palette root's own default record"* —
   the seven `palette.*` offsets are the seven `tints[9].*` offsets; no 11th record exists.
6. §5 *"no file in JC3's index is named for … a time of day"* — its own table counts 2.
7. §5 rows `sky` 3,364 / `sun` 31 — substring counts whose examples are false positives.

Correction to the review: its 109,526 B is the archive size; the loose unpacked `.epe` is
105,430 B. The pair is at `0x266` in both, so the finding stands.
