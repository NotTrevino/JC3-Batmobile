# review-G3-12d — the omitted-mip table, walked to the last byte

VERDICT: **holds**

The script's own check reproduces (`15/15`, `116 FULL / 0 PARTIAL`, `4 FULL / 0 PARTIAL`, md+summary
byte-identical), and a hand walk of six files — two tiny, two large, one format 83, one format 87 —
closes every one of them: 128-byte header + stored mips = file length, zero residue. The 84-byte tail
reads as **one record per omitted mip**: on the only one of the six with a non-empty table
(`k = 4`), the four record sizes are exactly the mip prices of levels 3, 2, 1, 0 and the offsets are
their prefix sums. All 116 files pass the same walk, so no file in the corpus has a table-row count
different from its omitted-mip count.

One correction to the premise this review was given: **G3-12b's card never said the tails track a
per-group chunk table**. `DECODE_DEPTH2.md:115-118` calls the tail an undecoded fixed-size table and
records that "no field mapping fits the mip sizes yet". The per-group hypothesis appears in
`tmp/freebuff/reports/review-G3-12b.md:108-110`, which reasons from siblings sharing a tail. Tested
here, that hypothesis fails: 9 of the 16 multi-file texture groups have **differing** tails.

## 1. `--check`

```
$ uv run python Tools/scripts/decode_depth6.py --check; echo "check_exit=$?"
OK: 116 .ddsc (116 FULL / 0 PARTIAL), 4 .pfxc (4 FULL / 0 PARTIAL), 15/15 checks, md+summary byte-identical=True
check_exit=0
```

## 2. Six files, walked by hand

Selected before parsing: the two smallest, the two largest, the one format-83 file and one format-87
file. Every number is read at its offset (0x08 format, 0x0C/0x0E w/h, 0x14/0x15 mip counts,
0x20 header size, 0x24 payload, 0x2C.. 12-byte records), then closed arithmetically.

| file | fmt | w x h | full / stored | k | header | payload | header+payload | file | closes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `t_velocity_streak_alpha_dif.ddsc` (tiny) | 77 | 16x32 | 1 / 1 | 0 | 128 | 512 | 640 | 640 | **yes** |
| `shared_car_007_windows_alpha_dif.ddsc` (tiny) | 77 | 32x32 | 6 / 6 | 0 | 128 | 1,392 | 1,520 | 1,520 | **yes** |
| `t_explosiongrid_fume_06_gold_alpha_dif.ddsc` (large) | 77 | 4096x4096 | 13 / 13 | 0 | 128 | 22,369,648 | 22,369,776 | 22,369,776 | **yes** |
| `t_smoke_rolling_top_04_alpha_dif.ddsc` (large) | 77 | 2048x2048 | 12 / 12 | 0 | 128 | 5,592,432 | 5,592,560 | 5,592,560 | **yes** |
| `v0300_car_kensington_sportsmuscle_body_nrm.ddsc` (fmt 83) | 83 | 2048x2048 | 12 / 8 | **4** | 128 | 21,872 | 22,000 | 22,000 | **yes** |
| `erosion_smallcurve_soft.ddsc` (fmt 87) | 87 | 256x16 | 1 / 1 | 0 | 128 | 16,384 | 16,512 | 16,512 | **yes** |

Stored mip prices (16 B per 4x4 block for formats 77/83, 64 B for 87):

- 16x32, 1 mip → `[512]`
- 32x32, 6 mips → `[1024, 256, 64, 16, 16, 16]` = 1,392
- 4096x4096, 13 mips → `[16777216, 4194304, …, 16, 16, 16]` = 22,369,648
- 2048x2048, 12 mips → `[4194304, 1048576, …, 16, 16, 16]` = 5,592,432
- 2048x2048, 8 of 12 stored (k = 4) → `[16384, 4096, 1024, 256, 64, 16, 16, 16]` = 21,872
- 256x16, 1 mip at 64 B/block → `[16384]` = 16,384

In every case the `0x24` word equals the stored sum, the `0x20` word is 128, and the sum with the
header equals the file length — the same result the card's §1.3 gives for the format-83 file, now
reproduced by an independent walk that does not call any `decode_depth6` function.

## 3. The 84-byte table against a file whose row count differs from its mip count

**No such file exists in this corpus.** `k = mip_count_full - mip_count_in_file`, and counting the
non-zero 12-byte slots in the tail shows the tagged-slot count is **k on all 116 files** (0 failures),
with every slot after the k-th zero. So the table length is not independent evidence — it is
`k` by construction; the independent part is what each record *says*.

That is tested on the one of the six with `k > 0` (`v0300..._body_nrm.ddsc`, format 83):

```
table rows(k)=4
record sizes  [65536, 262144, 1048576, 4194304]
mip prices    [65536, 262144, 1048576, 4194304]  (levels 3..0)  match=True  prefix-sums=True
tagged slots  (0,0,65536,0x1000010) (1,65536,262144,0x1000010) (2,327680,1048576,0x0100010) (3,1376256,4194304,0x1000010)
```

Each record's `size` is exactly one mip's block price and its `offset` the prefix sum of the sizes
before it, for the four levels the file does not store (3, 2, 1, 0). Adding them to the stored
payload gives the full 12-level chain. That is the "streamed-mip records" reading, at the level of a
single file.

Across all 116 files the same three checks pass — record count == k, record size == that level's
price, record offset == prefix sum, slots after k zero, `header + payload == len`, and
`full chain == payload + table total`:

```
files failing the walk: 0 []
```

## 4. The per-group alternative — tested, refuted

`review-G3-12b.md:108-110` proposed that shared tails mean a "per-group chunk descriptor". I grouped
the 116 by directory and basename stem and compared the raw 84 bytes:

```
texture groups with >1 file: 16   files in them: 46
groups with ONE shared tail: 7    groups with DIFFERING tails: 9
distinct tails: 8 of 116;  71 files share the all-zero tail
```

So the tail is not constant within a group: 9 of 16 groups with siblings disagree. Seven groups do
share one tail, but in every one of those all members have `k = 0` (the all-zero tail), so they carry
no information. The genuine multi-file coincidence is between *different* textures with the same
`(w, h, format, k)` — `v0300..._body_msk`, `v0300..._body_mpm` and `road_scorch_002_nrm` share one
`k = 3` tail — which is what a table derived from dimensions and format must do, and is not what a
per-group descriptor would predict.

Which statement the six files support: **G3-12d's**, the omitted-mip records. They do not support a
per-group chunk table, and they do not support G3-12b's "tracks the mip set, unmapped" either — that
was the honest UNKNOWN at the time, and this pass closes it.

## 5. The 4 `.pfxc`

They are not in `CookedPCConsole` (0 found there); they live in the donor tree at
`E:/Modding/_shared/gamedata/JC3grab/b13b/unpacked/.../vehicle_debris/`. Re-read there:

```
4 files, each 2500 B, 'PFX\0' at 0, packfile magic 0x57E0E057 at 0x44,
3 sections, contents index 3, 68 + (len - 0x44) == len on 4/4, 0 bytes after the packfile
```

**holds**: each file is wrapper (68 B) + packfile (2,432 B) to the last byte, no trailing blob — the
G3-12b "512-byte blob" was that section's own fixup tail, as the card says.

## 6. What I could not check

- **Texel content.** The walk proves the byte layout, not that a block decodes to the right pixels;
  no decoder or reference export exists in the project.
- **Why a file omits large mips.** The records price them exactly; nothing in the bytes says why the
  cooker streamed them out.
- **`.pfxc` object-level extents** (7 objects, 400-byte polytope, face/corner tables). I re-read the
  container arithmetic to EOF, not the body layout that the card's §2.3 closes; that is covered by
  its own checks, which I did not re-implement.
- **`0x06`, `0x12`, `0x28` header meanings.** Values decoded on every file; no oracle in the bytes
  assigns them a meaning, and the card marks them UNKNOWN.

## Commands run

```
$ uv run python Tools/scripts/decode_depth6.py --check
OK: 116 .ddsc (116 FULL / 0 PARTIAL), 4 .pfxc (4 FULL / 0 PARTIAL), 15/15 checks, md+summary byte-identical=True
(check_exit=0)

$ uv run python - <<'PY'   # six-file walk + all-116 table test
== six files: fmt77/640B, fmt77/1520B, fmt77/22369776B, fmt77/5592560B, fmt83/22000B, fmt87/16512B ==
... header+payload == len: True on all six ...
table rows(k)=4  record sizes [65536, 262144, 1048576, 4194304]  mip prices equal, prefix sums True
files failing the walk: 0 []
PY

$ uv run python - <<'PY'   # group test on the 84-byte tail
groups with ONE shared tail: 7   groups with DIFFERING tails: 9   distinct tails: 8 of 116
PY

$ uv run python - <<'PY'   # the 4 .pfxc from the donor tree
4 files, 2500 B each, packfile at 0x44, 68 + packfile == len, 0 trailing bytes
```

Read-only: `DECODE_DEPTH6.md`, `decode_depth6.py`, `DECODE_DEPTH2.md`, `review-G3-12b.md`, the donor
bundle and the four `.pfxc`. No file was edited; no new script was needed.
