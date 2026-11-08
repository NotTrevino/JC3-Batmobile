STATUS: DONE

# 7211 - G3-09d: the `Palette.tints[i].tint_r` write path

## Answer (decoded + round-trip proven)

`tint_r` is **not stored in the `.epe`**. The `.epe` is an RTPC v1 container and its only
palette surface is `CCar.palette`, one int32 at file offset `0x29a`: the Jenkins hash of the
palette module **path**. The tint float itself lives in the palette `.vmodc` (ADF v4) as
`Palette.tints[i].tint_r`, a `ColorRGBA` of four float32 at `Tint+20` (R/G/B/A at +0/+4/+8/+12,
record stride 80 B).

So the edit is: one float in the palette module via `ConvertAdf --e/-i`, plus (only if the
module is renamed) one int in the `.epe` via `ConvertProperty --e/-i`.

**The current build writes no tint.** bm-005 (and bm-009) name the vanilla palette path
(hash `-1071400364`) and ship a palette byte-identical to bm-001. bm-RC1/bm-RC2 repoint the
hash to the `batmobile/` copy (`1322976751`) but ship the **same bytes** (`72d5d04f78c6...`):
the pointer moved, no value did. `Working/Entity/bm_epe_edits.json` has 19 rows, none
palette/tint.

Round trip (staged in a temp dir, build files untouched): changing `tints[0].tint_r.R` from
`0.0500000007` to `0.239` changed **exactly 4 bytes at `0x74..0x77`**, one XML value line, same
file size (1897 B), and re-importing the re-export was byte-identical. The `.epe` pointer edit
changed exactly 4 bytes at `0x29a..0x29d` (124488 B, idempotent).

## Files written

| file | sha256 |
|---|---|
| `Tools/scripts/jc3_tint_write.py` | `c4b908b1c9b9ea5f1ec2e12212bbffbdf3fd22964ea020afb510af7f513c0121` |
| `Research/JC3Grab/TINT_WRITE.md` | `f9574fcb1ee4b8cd4cb743ba5c95771396318c0283014a9728dc99f48d60f259` |
| `tmp/freebuff/reports/7211-g3-09d-tint-write-path.md` | this report |
| `Backups/tint-write-colour-20261105/jc3_tint_write.py` | `a9baa1dd21ec613740d0b664a63faf34eb1c404012a4c94a08083614e70b79ca` (displaced predecessor) |
| `Backups/tint-write-colour-20261105/TINT_WRITE.md` | `d5d9bcb4a7e94ea10d2cd8d29905f9f8e83017b9ca7c760a2856b6327ed3fc19` (displaced predecessor) |

The two requested paths were already occupied by an unrelated **COLOUR-tint** card (engine
uploader, exe-based). That card's artifacts are preserved byte-for-byte in `Backups/` before
the new G3-09d script/doc took the requested paths.

## Change statement (AGENTS.md)

* **Intended change:** replace the exe-based COLOUR-tint script/doc at the requested paths with
  the G3-09d on-disk write-path gate, preserving the old ones.
* **Files:** `Tools/scripts/jc3_tint_write.py`, `Research/JC3Grab/TINT_WRITE.md` (both explicitly
  requested), plus backups.
* **Why correct:** the requested outputs are exactly these paths; the predecessors were a
  different card's artifacts and are not referenced by this one.
* **Revert:** `cp Backups/tint-write-colour-20261105/jc3_tint_write.py Tools/scripts/jc3_tint_write.py`
  and `cp Backups/tint-write-colour-20261105/TINT_WRITE.md Research/JC3Grab/TINT_WRITE.md`.
  No build file, `.epe` or palette module was modified; every edit ran on temp copies.

## Commands and verbatim output

```
$ python Tools/scripts/jc3_tint_write.py --write
PASS G1-adf-layout: Tint size 80, tint_r +20, ColorRGBA 16 B (R/G/B/A +0/+4/+8/+12)
PASS G1b-array-element: A[Tint] element type = Tint (80 B stride)
PASS G2-epe-has-no-tint: bm-005 .epe export: 8271 lines, 'Palette' 0, 'tint_r' 0, palette int -1071400364
PASS G3-pointer-hash: Jenkins('editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_palette.vmodc') = -1071400364 == .epe palette -1071400364
PASS G1c-tint-count: 10 Tint records by ConvertAdf export == 10 by jc3adf.walk
PASS G4-adf-roundtrip-bytes: 1897 -> 1897 B; 4 byte(s) differ at 0x74, 0x75, 0x76, 0x77
PASS G4b-float-value: float@0x74 0.0500000007 -> 0.238999993 (target float32 0.238999993)
PASS G4c-adf-idempotent: 2 XML value line(s) changed; re-import of the re-export is byte-identical: True
PASS G5-epe-roundtrip-bytes: 124488 -> 124488 B; 4 byte(s) differ at 0x29a, 0x29b, 0x29c, 0x29d
PASS G5b-epe-idempotent: 2 XML value line(s) changed; re-import byte-identical: True
PASS G6-build-pointers: 5 builds: every .epe palette int equals the Jenkins hash of the module path
PASS G6b-no-tint-written: every build's palette module is byte-identical to bm-001: True
PASS G7-no-tint-row: 19 bm_epe_edits rows, 0 name palette/tint
PASS G8-ee-is-archive: v0300_car_kensington_sportsmuscle_debug.ee magic b'AAF' (an AAF archive, not ADF/RTPC)
wrote Research\JC3Grab\TINT_WRITE.md
OK (14 gates)
write_exit=0
```

```
$ python Tools/scripts/jc3_tint_write.py --check
PASS G1-adf-layout: Tint size 80, tint_r +20, ColorRGBA 16 B (R/G/B/A +0/+4/+8/+12)
PASS G1b-array-element: A[Tint] element type = Tint (80 B stride)
PASS G2-epe-has-no-tint: bm-005 .epe export: 8271 lines, 'Palette' 0, 'tint_r' 0, palette int -1071400364
PASS G3-pointer-hash: Jenkins('editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_palette.vmodc') = -1071400364 == .epe palette -1071400364
PASS G1c-tint-count: 10 Tint records by ConvertAdf export == 10 by jc3adf.walk
PASS G4-adf-roundtrip-bytes: 1897 -> 1897 B; 4 byte(s) differ at 0x74, 0x75, 0x76, 0x77
PASS G4b-float-value: float@0x74 0.0500000007 -> 0.238999993 (target float32 0.238999993)
PASS G4c-adf-idempotent: 2 XML value line(s) changed; re-import of the re-export is byte-identical: True
PASS G5-epe-roundtrip-bytes: 124488 -> 124488 B; 4 byte(s) differ at 0x29a, 0x29b, 0x29c, 0x29d
PASS G5b-epe-idempotent: 2 XML value line(s) changed; re-import byte-identical: True
PASS G6-build-pointers: 5 builds: every .epe palette int equals the Jenkins hash of the module path
PASS G6b-no-tint-written: every build's palette module is byte-identical to bm-001: True
PASS G7-no-tint-row: 19 bm_epe_edits rows, 0 name palette/tint
PASS G8-ee-is-archive: v0300_car_kensington_sportsmuscle_debug.ee magic b'AAF' (an AAF archive, not ADF/RTPC)
PASS document: TINT_WRITE.md matches the regenerated text
OK (14 gates)
check_exit=0
```

Tamper test (append one comment line to the doc, then restore):

```
=== TAMPER
@@ -165,3 +165 @@
 
-
-<!-- tamper -->
FAIL document: on-disk TINT_WRITE.md does not match the regenerated one
1 FAILURE(S)
tamper_exit=1
=== RESTORE
restore_check_exit=0
```

Build inputs re-hashed after the run (unchanged):

```
72d5d04f78c64120409362646db273ef6f83d9d99606f257794ef5df9c49073b *.../modules/default/v0300_car_kensington_sportsmuscle_palette.vmodc
f4abe91da0bc3ce371edb1da135e0eb34357555741a409cb377b0785cb4e9fdf *.../v0300_car_kensington_sportsmuscle_civilian_01.epe
0811fea3c3278c1ed10b952020d716a05b1c1ab75eb890b553c22e7b28eba817 *Working/Entity/bm_epe_edits.json
```

## What the evidence came from

* `.epe`: `ConvertProperty --e` of `Builds/bm-005/.../v0300_car_kensington_sportsmuscle_civilian_01.epe`
  - `8271` XML lines, no `Palette` object, no `tint_r`, one `<value name="palette" type="int">-1071400364</value>`.
* palette: `Builds/bm-005/.../modules/default/v0300_car_kensington_sportsmuscle_palette.vmodc`,
  decoded both by `jc3adf.py` (`Adf`, `walk`) and by `ConvertAdf --e`; both give `Tint` 80 B,
  `tint_r` +20, `ColorRGBA` 16 B, 10 records.
* pointer hash: `rbmhdr.name_hash` (Jenkins, pinned against `HashName.exe`) over the
  `.epe`-relative module path; both signed values reproduced exactly.
* build state: palette sha and `.epe` palette int for bm-001, bm-005, bm-009, bm-RC1, bm-RC2.
* `Working/Entity/bm_epe_edits.json`: 19 edits, none palette/tint.

## UNKNOWN (with what was tried)

1. **Which engine code turns the palette tint into `cb6` (`m_TintColorR/G/B`).** TINT.md
   (G3-09) already measured no asset names the binding; this card covers the write side only.
   Tried: `.epe` export (no binding), palette ADF (values only).
2. **Whether the packaged `.ee` carries/overrides an inlined palette.** `..._debug.ee` is an
   AAF archive (`magic AAF`); `ConvertAdf` raises FormatException and `ConvertProperty`
   NotSupported, so it was not decoded.
3. **Whether the game honours an edited tint in play.** Test ban - not measured; no install,
   no game launched.
4. **Which record a player's paint selection picks.** TINT.md decodes `occurrence` weights but
   no selector.

Labels: everything above is **decoded** from the named files or **derived** by the stated
round trip; the four items are UNKNOWN, not filled in.
