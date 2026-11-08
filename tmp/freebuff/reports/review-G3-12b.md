# Independent review — G3-12b (4 `.pfxc` + 116 `.ddsc` containers)

Reviewer: independent (did not write the card). Date: 2026-11-03.
Read: `tmp/freebuff/reports/G3-12b.md`, `Research/JC3Grab/DECODE_DEPTH2.md`,
`Research/JC3Grab/DECODE_DEPTH2.json`, `Tools/scripts/decode_depth2.py`, and the prior grades in
`Research/JC3Grab/DECODE_DEPTH.md`.

Read-only: I ran `--check` only; I did **not** run `--write`. No game launched or read; nothing written
under `E:/Games` or `D:/Games`; no git command.

Method: I re-read the bundle myself through the project's own readers (`bm_rc.vfs` + `eetoc.unaaf` /
`eetoc.sarc_dir`, the same entry points the tool uses) and re-implemented the header parse, the 4x4-block
mip tiling, the block-size solve and the `.pfxc` packfile walk. Shared-dependency caveat: the bundle
reader is the card's, so a bundle-level error would be common-mode; the per-file numbers are not.

---

## VERDICT: **minor issues**

The core result holds exactly. I reproduce, from the raw bytes: **116 `.ddsc` = 71 FULL / 45 PARTIAL**,
**1,013 mips** tiled to EOF, **format → block bytes 77→16, 71→8, 87→64, 83→16** with exactly one
surviving candidate per file, `128 + size_body == file length` on 116/116, the `0x28` word = 16 on all
116, and all **4 `.pfxc`**: `PFX\0`, wrapper `[1,1,3,0]`, packfile at `0x44`, `hk_2014.1.0-r1`, 7 objects
in exactly the 7 claimed classes, packfile end 1988, 512 trailing bytes with the four claimed md5s.
Per-file comparison against `DECODE_DEPTH2.json`: **0 mismatches on 116 files**.

The defects are in three places: one decoded detail in the report is false for 3 of the 4 files, one
check is named for an invariant it does not test (and that invariant is asserted nowhere), and the
characterisation of the `.ddsc` tail as mip-derived is contradicted by the bytes. None of them moves the
71/45 grade, which my independent recomputation confirms.

---

## 1. Check output (verbatim)

```
cd "E:/Modding/JC3-Batmobile" && uv run --with numpy --with pillow --with pefile --with capstone python Tools/scripts/decode_depth2.py --check; echo "CHECK_EXIT=$?"
```

```
OK: 116 .ddsc (71 FULL / 45 PARTIAL), 4 .pfxc (4 PARTIAL), 8/8 checks, md+summary byte-identical=True
CHECK_EXIT=0
```

Matches the report exactly.

---

## 2. Spot-checks — 5 decoded values re-read from the raw source

| # | decoded value claimed | where I read it | match |
|---|---|---|---|
| 1 | `car_tire_sport02_nrm.ddsc`: fmt **77**, **1024x512**, mip counts **8 stored / 10 full**, `size_header 128`, `size_body 43712`, file 43840, `0x28` word **16** | bundle entry → `raw[off:off+size]`, `<I` at 8, `<2H` at 12, bytes 20/21, `<I` at 32/36/40 | **yes** (128 + 43712 = 43840, const@0x28 = 16) |
| 2 | fleet: **116** `.ddsc`, **71 FULL / 45 PARTIAL**, **1,013 mips**, formats 77 ×66, 71 ×46, 87 ×3, 83 ×1; block map 77→16, 71→8, 87→64, 83→16, one candidate per file | my own tiling solve over all 116 blobs | **yes** (exact on every count; 0 files with ambiguous candidates) |
| 3 | `v0300_car_kensington_sportsmuscle_body_nrm.ddsc` (fmt **83**): 2048x2048, mips **8/12**, `size_body 21872`, block 16, ranges tile exactly, non-zero tail → PARTIAL | same, recomputed mip sizes 16384+4096+1024+256+64+16+16+16 = 21872, end == len | **yes** |
| 4 | every `.pfxc`: 2500 B, `PFX\0`, wrapper `[1,1,3,0]`, packfile at **0x44**, `hk_2014.1.0-r1`, sections `__classnames__/__types__/__data__`, **7 objects** = `hkRootLevelContainer, hkxScene, hknpPhysicsSceneData, hknpPhysicsSystemData, hknpConvexPolytopeShape, hkRefCountedProperties, hknpShapeMassProperties`, end **1988**, trailing **512**, md5s `43f5234e / 3957a03d / dbd6c225 / 41b16092` | `jc3hkx.Packfile` on each blob at the located offset | **yes** (all four, byte for byte) |
| 5 | "the 45 non-zero tails … whose values **track the mip set**" | counted the distinct 84-byte tails across the 45 PARTIAL files | **no** — 45 files carry only **7 distinct tails**, and the same tail covers different mip sets (see I3) |

---

## 3. Issues

### I1 — a decoded detail is false: the `.pfxc` trailing blob does not "begin with `0x3f800000`"

Report (§ Criterion 1) and doc (§ 4): "*it begins with `0x3f800000` (1.0f) and ends with a table of 16-bit
pairs*". The four trailing blobs start:

| file | trailing blob bytes 1988..1991 |
|---|---|
| `debris_vehicle_debri01_col.pfxc` | `00 00 80 3f` (= 1.0f) |
| `debris_vehicle_debri02_col.pfxc` | `fe ff 7f bf` (≈ −0.99999) |
| `debris_vehicle_debri03_col.pfxc` | `00 00 00 00` |
| `debris_vehicle_debri04_col.pfxc` | `00 00 00 00` |

So the statement describes 1 of 4 files and is false for the other three. All four do end with
`ff ff ff ff ff ff ff ff`, so "ends with a table of 16-bit pairs" is consistent as an observation but is
an interpretation, not a decoded field. Fix: give the four first words, or say "one file starts with 1.0f".

### I2 — check 4 is named for the `+40` constant but asserts the header size, and the `+40` invariant is asserted nowhere

Script check 4: name "*the constant at +40 is the same on every `.ddsc`*", body
`assert size_header == 128` — that is the field at **0x20**, not the word at **0x28**. The doc's table
repeats the mismatched name with the revealing detail ("`size_header = [128]`"), while the report renames
the row to "header size is the same on every `.ddsc`". Consequences:

- the `0x28 == 16` invariant that the doc's header table presents as "116/116" has **no check**;
  `CONST_40 = 16` is defined in the script and never used;
- `HDR_SIZE = 40` is likewise dead code.

I verified independently that `0x28 == 16` does hold on all 116, so the *claim* is true — the problem is
that the evidence table and the checks disagree about what was tested.

### I3 — "the tail values track the mip set" is contradicted by the files

Doc § 4: "*a fixed-size table whose u32 pattern repeats … and whose values track the mip set*". Censused
by me over the 45 non-zero tails: **7 distinct 84-byte patterns**. The same pattern covers different mip
sets and different texture sizes:

- pattern `0x20000` (8 files): `car_tire_sport02_nrm` (1024×512, 8 mips, fmt 77), `car_undercarriage_sport01_dif`
  (1024×1024, 9 mips, fmt 71), `shared_car_009_licenseplate_decal_nrm` (1024×256, 7 mips, fmt 77) — one tail,
  three different chains, two formats;
- pattern `0x10000` (14 files): all 256×256;
- the tails do differ by *something*, but not by the per-file mip list.

What the bytes do show: each tail is a sequence of **u32 triples** `(start, size, 0x1000010)` whose `start`
accumulates exactly (`0`, `0x20000`, `0xa0000`, …) and whose `size` takes the values `0x10000, 0x20000,
0x40000, 0x80000, 0x50000, 0x100000, 0x200000`. That is the shape of a **chunk/tile table**, and the
files that share a tail are the `_dif`/`_nrm`/`_mpm`/`_msk` siblings of the same texture group — so the
table is probably per *group*, not per file. The card's "tracks the mip set" sends the next reader down the
wrong road; "7 shared patterns, triples (start, size, 0x1000010), grouped by texture" is what the bytes say.

### I4 — check 2 does not test the oracle it names

Name: "*every `.ddsc` mip chain is accounted for by exactly one block size, and the ranges tile the payload
to EOF*". Body: `all(x["closes"] and (x["mips"] or not x["closes"]))` — i.e. the container closes and the
mip list is non-empty. It does **not** test `end == len(blob)` (the tiling) and does not check the number
of candidates. `ddsc_decode` does compute tiling (`ok = off == len(blob)`), but the check never reads that
result, so a file whose ranges overran by a byte would still pass check 2 (it would drop to PARTIAL only
through the grade field, which no check inspects for accounting). The tiling is in fact correct — I
recomputed it on all 116 — but the check that advertises it is weaker than advertised.

### I5 — check 5 is near-tautological

`tail_zero == (grade == "FULL")` holds by construction for every file whose accounting closes (`grade` is
`FULL` only if `tail_zero`). All 116 files close, so the check can only ever exercise the branch that does
not occur. Combined with I2, the "8/8" contains one tautology and one mislabelled assertion; the genuinely
independent checks are 1 (closure), 3 (block map), 6–8 (packfile). The report's phrasing
"the grade follows the bytes, not the file name" is fine as prose but is not what the check proves.

### I6 — minor number/label slips

- Module docstring: "*the 88 bytes of header tail after the constant at +40*" — 128 − 40 = 88, but the
  constant occupies 40..43, so the tail after it is **84** bytes. The doc's own table says
  `0x2C..0x80 | 84`, which is right; the docstring is the odd one out.
- Report: "*the wrapper … three u32 = 1, 1, 3*" — the wrapper is four u32, `[1, 1, 3, 0]`, as the doc
  prints; the trailing 0 is part of the same struct.
- Report: "*one convex hull + its part index + mass properties*" — the part index is attributed to
  `hkRefCountedProperties`, which is decoded as a class name only. The classes are right; that one phrase
  is an interpretation and should be labelled.

---

## 4. Resolvable UNKNOWNs

1. **The `.ddsc` tail table (45 files) — narrowed, not closed.** My census shows 7 shared patterns, not 45
   per-file tables, and a triple structure `(start, size, 0x1000010)` with cumulative `start`. The next
   test is cheap and decisive: group the 45 by texture basename (`_dif/_nrm/_mpm/_msk` siblings) and check
   that the tail is constant within a group and equal across groups of the same chain — if so, the table is
   a per-group chunk descriptor, and its `size` column can be compared with the group's `.ddsc` sizes.
2. **The `.pfxc` trailing blob — the card's own first-word claim is refuted** (I1), which is a starting
   point: the four blobs share the last 8 bytes (`ff×8`) and differ in the first words, so a fixed
   header/tail with a per-file middle is the shape to test. 512 bytes = 32 × 16 (planes) or 128 floats;
   the invariant that would discriminate is that a convex-plane set has |n| ≈ 1 across the first three
   floats of each 16-byte record — a mechanical test over 32 records per file, no new reader needed.
3. **The `0x28` word (= 16).** Not resolvable from these files alone (constant on all 116, so it carries no
   variation to correlate); the card's two exclusions (block size, mip-size floor) are correct, and my
   independent read confirms the value. It stays UNKNOWN unless a `.ddsc` with a different value is found
   elsewhere.
4. **Whether `.pfxc` is honoured for debris collision** — out of scope by the reset, correctly stated.

---

## 5. What the card gets right

- The container decode is exact on 116/116, including the part that matters most: **one** block-size
  candidate survives per file, and the tiling ends at EOF (I recomputed both independently).
- The block-size map is derived, not tabled, and the fleet-function invariant is real (77→16, 71→8,
  87→64, 83→16), matching the card's own caution that no DDS/BC name is claimed.
- The `.pfxc` decode is the strongest part: the packfile is located by its own magic, parsed by the
  project's reader, its objects typed from the packfile's own fixups, and the trailing range is *named*
  rather than glossed — which is exactly why no `.pfxc` reaches FULL.
- The correction of the prior census (0 FULL/116 PARTIAL → 71/45; 4 NAMED-ONLY → 4 PARTIAL) is accurate,
  and the `DECODE_DEPTH.md` figures I re-read agree with it.
- `--check` re-derives both the markdown and the summary and fails on any check; the JSON matches my
  independent per-file read with 0 mismatches, so the record is not stale.

---

## 6. Required changes

1. Correct the trailing-blob sentence with the four actual first words (I1).
2. Rename check 4 to what it asserts, and add the `0x28 == 16` assertion it currently lacks (or drop
   `CONST_40`/`HDR_SIZE` and say the invariant is unverified) (I2).
3. Replace "the values track the mip set" with the 7-pattern census and the triple structure (I3).
4. Make check 2 assert tiling and single-candidate, or rename it (I4).
5. Replace check 5 with an assertion that is not implied by the grade rule (I5).
6. Fix the 88/84 slip and label the `hkRefCountedProperties` "part index" as an interpretation (I6).
