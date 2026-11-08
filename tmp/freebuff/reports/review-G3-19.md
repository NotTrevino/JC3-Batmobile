# review-G3-19 - is the G3-19 byte accounting real, or does it read itself?

STATUS: done

## VERDICT

**ACCEPT WITH CORRECTIONS.**

The extents are real and independently reproducible - I re-derived all three `.rbm` framings from
the bytes with my own parser, decoded two `FULL` blocks myself, and every number matches. The
`.epe` classes recompute exactly. **But the check's headline oracle is an identity, not a proof**,
and two of the card's supporting claims do not survive: a stride solver that is not in the script,
and a "0 hits" negative result produced by scanning on the one alignment the card elsewhere shows
is wrong.

* **Sizes are read from the archive, not from its own output.** `size` comes from
  `eetoc.sarc_dir(raw)` (the `.ee` TOC); `--check` diffs a fresh recomputation against the
  committed JSON/MD. So it is not circular in *that* sense: the file size is an input. My run
  prints TOC size == `len(blob)` == the card's size for all three files (45,912 / 21,842 / 14,590).
* **But `sum == size` is algebraically vacuous.** With `blocks = [4 + b0 + 4, 4 + b1 + 4, 4 + b2 + 4]`,
  `b0 = end0-(hl+4)`, `s1 = end0+8`, `b1 = e1-s1`, `s2 = e1+8`, `b2 = end2-s2`, the script's
  `total = hl + sum(4+b+4)` collapses to **`end2 + 4`**, independent of `hl`, `end0` and `e1`.
  Verified numerically on all three files: 45908+4 = 45,912; 21,838+4 = 21,842; 14,586+4 = 14,590.
  So "oracle 1" is a restatement of "block 2 ends at `len-4` and there is a checksum there". It
  cannot detect a wrong header length, a wrong block-0 end or a wrong block-1 end - errors in any
  of those cancel out of the sum by construction.
* **What actually closes the framing is the checksum inventory**, which the script never states:
  each file contains **exactly three** `0x89ABCDEF` words, at exactly the three block ends, and
  block 2's end is `len-4`. I found no fourth occurrence anywhere, and none *inside* block 1 before
  its end, so the block-1 end chosen by the "first checksum after the payload start" scan is
  unambiguous in these files.
* **Two FULL blocks decoded independently and the numbers match.** My own `CarPaintMM` walk (counts
  and strides from the format, not from `rbm_geom`) reproduces both block extents and their
  contents: lod1 block 0 = **13,051 B** ending exactly on the checksum at 13,108 (v14, flags
  `0x4`, 12 textures, 262 vertices at stride 12, 696 indices); lod1 block 2 = **25,658 B** ending
  at 45,908 = `len-4` (v14, flags `0x1f`, 12 textures, 548 vertices, 1,764 indices). lod2/lod3
  likewise (8,587 / 10,586 and 5,455 / 7,844). The GeneralMkIII trailer also matches exactly:
  `u32 672` at 18,894, first eight `[0,1,2,2,1,3,1,4]`, max index 175, ending on the checksum at
  20,242 - and it is the **only** fit in that payload (brute-forced at every 2-byte position).
* **The `.epe` classes recompute exactly**: 2,293 differing bytes = 2,189 `0x50`->`0x00` in 750
  runs + 104 float bytes in 75 fields (75 runs), **0 unexplained**; relative change
  6.338022e-08..4.306916e-07, largest absolute change 3.81469726562e-06, and 97 of the 104 print
  identically at seven significant digits. `a.epe` is byte-identical to the vanilla member
  (full sha256 `f67bc17ebb16b70f35a6a131ffc8a1c5ca772ee5dac2b5524ae0603c93c22c32`).
* **Undecoded is not counted as decoded anywhere** - with one imprecise label. The JSON's block 1
  is `"decoded": null`, the MD table marks it `**undecoded payload**`, §1b names the range, and §3
  files `GeneralMkIII` as `UNKNOWN`. The imprecision: the table's block-1 column calls all
  **7,126 B** undecoded while §1a decodes the last **1,348 B** of that same block (lod2: 202 B of
  2,592; lod3: 28 B of 1,214). §1b's own range (5,778 B) is right; the table row is not.
* **Defect 1 - a claimed experiment that is not in the script.** §1b's first bullet describes "a
  stride solver over `prefix + n*(u32 count, count*stride)` for `prefix` in 0..96 step 4 and
  strides 2..64 ... one accidental closure (lod2, prefix 36, one stride-8 buffer of 319 entries)".
  No such solver exists in `decode_depth3.py`: grep finds those words only inside the MD string at
  lines 372-375. `--check` cannot re-derive it, and it is the card's stated reason for rejecting a
  candidate layout. As written it is an **unreproducible claim** and should be labelled UNKNOWN.
* **Defect 2 - the "0 hits" negative result is an alignment artifact.** The float3-vs-AABB scan
  iterates `range(s1, e1-11, 4)`, i.e. only offsets `s1 mod 4`. At **every byte offset** there are
  **2 hits per file** (6 total) that land inside the header AABB, and they are 12 bytes apart - one
  stride:
  * lod1: 13,193 `(-0.209524, 1.087842, -1.571032)`, 13,205 `(0.209293, 1.140432, -1.484981)`
  * lod2: 8,729 `(-0.209524, 1.087842, -1.552618)`, 8,741 `(0.202337, 1.136706, -1.484981)`
  * lod3: 5,597 `(-0.083720, 1.099922, -1.558572)`, 5,609 `(0.069468, 1.137126, -1.486233)`
  This matters because the card's own §1a proves the block's numeric run starts at **+0x11**, one
  byte off the word grid. A buffer starting on that shifted grid has its float3s at
  `s1+1 mod 4`, which the scan cannot see. So the card's strongest refutation - "the naive reading
  ... is ruled out on the bytes: no 12-byte run anywhere" - is **not established**; only
  "no *4-byte-aligned* 12-byte run" is, which is precisely the alignment the card shows is wrong.
  Whether those two hits are the vertex buffer is **UNKNOWN** (no oracle), but they are enough to
  void the negative.
* **Cosmetic:** §2 prints `sha256 f67bc17ebb16b70f35a6a131ffc8a1c5` - that is the first 32 hex
  characters of the digest, labelled `sha256`. The full value is in my check below.

Nothing here is a claim about JC3, `.rbm` semantics or the `.epe` format beyond the bytes I read.
`decode_depth3.py` and `rbm_geom.py` were **not** edited; my verifier is a scratch file.

## 1. Independent framing (my own header + CarPaintMM parser, no `rbm_geom`)

`archive`: `bm_rc`/`eetoc` used only to reach the container TOC.

| file | TOC size | len(blob) | nblocks | header | `0x89ABCDEF` at | block 0 (mine) | block 1 | block 2 (mine) |
|---|---:|---:|---:|---:|---|---|---|---|
| lod1 | 45,912 | 45,912 | 3 | 53 | 13108, **20242**, 45908 | 13,051 B, ends on CS | 7,126 B | 25,658 B, ends 45908 = len-4 |
| lod2 | 21,842 | 21,842 | 3 | 53 | 8644, 11244, 21838 | 8,587 B, ends on CS | 2,592 B | 10,586 B, ends 21838 = len-4 |
| lod3 | 14,590 | 14,590 | 3 | 53 | 5512, **6734**, 14586 | 5,455 B, ends on CS | 1,214 B | 7,844 B, ends 14586 = len-4 |

Note the middle checksum is **not 4-byte aligned** in lod1 (20,242) and lod3 (6,734), so the
script's byte-wise scan (`range(s1, len-4)`, step 1) is necessary and correct; an aligned-only
scan would miss the block-1 end.

Two FULL blocks, decoded with my own walk (version, flags, textures, vertex count/stride, index
count), all landing on the checksum:

| file | block | v | flags | textures | verts | stride | indices | max idx | bytes | land |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| lod1 | 0 | 14 | `0x4` | 12 | 262 | 12 | 696 | 261 | 13,051 | CS @13108 |
| lod1 | 2 | 14 | `0x1f` | 12 | 548 | 12 | 1,764 | 547 | 25,658 | CS @45908 |
| lod2 | 0 | 14 | `0x4` | 12 | 156 | 12 | 372 | 155 | 8,587 | CS @8644 |
| lod2 | 2 | 14 | `0x1f` | 12 | 203 | 12 | 438 | 202 | 10,586 | CS @21838 |
| lod3 | 0 | 14 | `0x4` | 12 | 79 | 12 | 192 | 78 | 5,455 | CS @5512 |
| lod3 | 2 | 14 | `0x1f` | 12 | 136 | 12 | 273 | 135 | 7,844 | CS @14586 |

Every byte count equals the card's. The GeneralMkIII head is byte-identical across the three lods
(one distinct 144-hex-character string), as claimed.

GeneralMkIII trailer, re-read by me at the card's `count_at` and brute-forced for uniqueness:

| file | count_at | count | first eight | max | ends at | fits found |
|---|---:|---:|---|---:|---:|---:|
| lod1 | 18,894 | 672 | `[0,1,2,2,1,3,1,4]` | 175 | 20,242 (CS) | **1** |
| lod2 | 11,042 | 99 | `[0,1,2,3,4,5,6,7]` | 54 | 11,244 (CS) | **1** |
| lod3 | 6,706 | 12 | `[0,1,2,3,4,5,6,7]` | 11 | 6,734 (CS) | **1** |

So the trailer is unique in each payload - the card's index table is sound, and "oracle 3" is
weaker than claimed only in that its end bound is the checksum that defined the block's end.

## 2. The `.epe`, recomputed from the artefacts

```
a 109526 f67bc17ebb16b70f35a6a131ffc8a1c5ca772ee5dac2b5524ae0603c93c22c32
b 109526 f5a11052b5fc8f3a6492926e5fa2f3c3552f7392937e7e67d4e7c6806370e413
len equal: True differing bytes: 2293
fill 0x50->0x00: bytes=2189 runs=750
float-text class: bytes=104 fields=75 runs=75
unexplained bytes: 0
rel_min=6.338022e-08 rel_max=4.306916e-07
max_abs=3.81469726562e-06
same at 7 sig digits: 97
vanilla editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.epe 109526 f67bc17ebb16b70f35a6a131ffc8a1c5ca772ee5dac2b5524ae0603c93c22c32
a identical to vanilla: True
```

Identical to the card, digit for digit (including `2293 = 2189 + 104`, which the card implies but
never prints). The `.epe` is "FULL" only in the sense of "no unexplained differing byte on this
round trip" - the card does say that, and its own §4.2 correctly keeps the engine-load question
OPEN.

## 3. Commands and output

`python Tools/scripts/decode_depth3.py --check` (exit 0):

```
PASS json matches recomputation
PASS md matches recomputation
PASS rbm sums ok
PASS epe 0 unexplained
OK   sportsmuscle_missile_base_signature_lod1.rbm   size  45912  sum==size True  mkiii  7126 B  idx  672  verts 176
OK   sportsmuscle_missile_base_signature_lod2.rbm   size  21842  sum==size True  mkiii  2592 B  idx   99  verts  55
OK   sportsmuscle_missile_base_signature_lod3.rbm   size  14590  sum==size True  mkiii  1214 B  idx   12  verts  12
RESULT: PASS
```

My framing verifier (`tmp/freebuff/scratch/g319_verify.py`, output verbatim, one lod shown; the
other two differ only in the numbers tabulated above):

```
archive members matched: 3

=== sportsmuscle_missile_base_signature_lod1.rbm
  TOC size=45912  blob len=45912  nblocks=3  header_len=53  tag=0x9
  bbox_min=(-0.2966674566268921, 1.0061227083206177, -1.5710318088531494) bbox_max=(0.29746440052986145, 1.1840211153030396, -1.1791528463363647)
  0x89ABCDEF occurrences: 3 total [13108, 20242, 45908] ; 4-aligned: [13108, 45908]
  block0 type=0x483304d6  payload [57,13108)  bytes=13051  ends_on_cs=True
     v14 flags=0x4 tex=12 vb0=262 idx=696 max_idx=261 bytes=13051
  block1 type=0x2cec5ad5  payload [13116,20242)  bytes=7126  (end = first CS >= start)
     CS-pattern inside block1 before its end: []
  block2 type=0x483304d6  payload [20250,45908)  bytes=25658  ends_at=45908  file-4=45908  ends_on_cs=True
     v14 flags=0x1f tex=12 vb0=548 idx=1764 max_idx=547 bytes=25658
  my sum=45912  size=45912  equal=True   end2+4=45912
  idx first8: [0, 1, 2, 3, 4, 5, 5, 4]

=== GeneralMkIII head identical across lods? ===
  distinct head hex strings: 1  len: [144, 144, 144]
```

(The `sum with header_len=45/61 -> False` lines from that same run are **not** evidence for the
identity either way: they hold the parsed block lengths fixed while changing `hl`, which is not
what the script does. The valid statement of the identity is the symbolic one in the verdict plus
`my sum == end2+4` above, which is exact.)

Trailer uniqueness and the alignment test (`python - <<'PY' ...`, output verbatim):

```
=== sportsmuscle_missile_base_signature_lod1.rbm   block1 [13116,20242) = 7126 B
  undecoded per card 1b: [13116,18894) = 5778 B ; tail decoded = 1348 B
  trailer fits with end==20242 (every 2 B): 1 [(18894, 672, 175)] ; card picked 18894
  float3-in-bbox over block1: step1=2 [13193, 13205] | step4=0
     at 13193: (-0.20952381193637848, 1.087841510772705, -1.5710318088531494)
     at 13205: (0.20929282903671265, 1.1404316425323486, -1.484980821609497)

=== sportsmuscle_missile_base_signature_lod2.rbm   block1 [8652,11244) = 2592 B
  undecoded per card 1b: [8652,11042) = 2390 B ; tail decoded = 202 B
  trailer fits with end==11244 (every 2 B): 1 [(11042, 99, 54)] ; card picked 11042
  float3-in-bbox over block1: step1=2 [8729, 8741] | step4=0
     at 8729: (-0.20952381193637848, 1.087841510772705, -1.5526179075241089)
     at 8741: (0.20233747363090515, 1.1367062330245972, -1.484980821609497)

=== sportsmuscle_missile_base_signature_lod3.rbm   block1 [5520,6734) = 1214 B
  undecoded per card 1b: [5520,6706) = 1186 B ; tail decoded = 28 B
  trailer fits with end==6734 (every 2 B): 1 [(6706, 12, 11)] ; card picked 6706
  float3-in-bbox over block1: step1=2 [5597, 5609] | step4=0
     at 5597: (-0.08371978998184204, 1.0999222993850708, -1.5585724115371704)
     at 5609: (0.06946782767772675, 1.1371264457702637, -1.4862327575683594)
```

Grep for the claimed stride solver:

```
$ grep -n "prefix\|range(0, 96\|stride in range(2\|319" Tools/scripts/decode_depth3.py
372:    A("* A stride solver over `prefix + n*(u32 count, count*stride)` for `prefix` in")
374:    A("  block checksum. It found **one** accidental closure (lod2, prefix 36, one")
375:    A("  stride-8 buffer of 319 entries) that does not exist for lod1 or lod3, so it is")
```

Only the render strings - no solver code.

## 4. Files

* `tmp/freebuff/reports/review-G3-19.md` (this report)
* `tmp/freebuff/scratch/g319_verify.py` (my independent framing/CarPaintMM parser)
* No project file edited; `decode_depth3.py`, `rbm_geom.py`, `DECODE_DEPTH3.md`/`.json` untouched.

## UNKNOWNs

1. **Whether the two unaligned float3 hits per file are the GeneralMkIII position buffer.** Tried:
   read them (listed above), counted them at every byte offset, checked they are 12 bytes apart.
   No oracle names a GeneralMkIII field, so they are candidates only. Where it would be answered:
   a serializer for block type `0x2cec5ad5`, or a stride-12 walk from `s1+1` that lands on the
   index count - which is the experiment the card's rejected solver was supposed to be.
2. **What the "lod2, prefix 36, stride-8, 319 entries" closure is.** Tried: grep of the whole
   script (render text only), search of the JSON for any prefix/stride-solver record (none). The
   result cannot be recomputed from anything committed. Where it would be answered: the solver
   itself, in a new version of the script (`...2.py`), recorded in the JSON.
3. **Whether `ConvertProperty`'s float-text round trip loads in the engine.** As the card says, a
   runtime question; 75 fields' low bits move and no byte-level check can settle it.
