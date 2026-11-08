VERDICT: minor issues — every number the card states about the three files reproduces exactly from the bytes (payload sums, 243 markers, the ULP statement, the UV-area claim), and all four §4 quotes are in `DECODE_DEPTH4.md`. The issues are in the *wording of the fleet cross-check* (its denominator silently excludes the two blocks that fail framing, and "126/126 uniform" cannot fail by construction), plus two small quoting imprecisions (the normals range drops two negative means; "2-component" has no row of its own in §4). Nothing found contradicts the card's conclusion, and the card's own restriction of its claim ("the field widths are the block type's but the semantics are not fleet-wide") is the right one except for the words "the block type's".

# Review of G3-19b

Sources re-read: `tmp/freebuff/reports/G3-19b.md`, `Research/JC3Grab/DECODE_DEPTH4.md` (§1–§6),
`Tools/scripts/decode_depth4.py`, and the three `.rbm` files themselves. No game process, no archive
writes; only the report you are reading was written.

Labels below: **decoded** = read from the file at the quoted offset; **derived** = arithmetic on decoded
values; **UNKNOWN** = not established here.

The bytes I used are the `b13b/unpacked` copy, and all four on-disk copies of each lod are byte-identical
(decoded, sha256 prefix):

```
lod1  copies=4  distinct_sha=1  ['2fdb273b4413cb99']
lod2  copies=4  distinct_sha=1  ['220c6a61f57aa4d8']
lod3  copies=4  distinct_sha=1  ['a009ee26e0299c49']
```

so checking one copy checks what the card's `.ee` extraction produced.

## 1. The three payload sums — reproduce exactly (decoded + derived)

Framing read straight from the files: `header_len` from the RBM header, then per block `u32 type_hash` +
payload + `u32 0x89ABCDEF`; each payload end is the next `0x89ABCDEF`, so the payload lengths are measured,
not asserted (decoded):

```
lod1 size=45912 header_len=53 nblocks=3
   block[0] type=0x483304D6 payload=13051 span=[57,13108) name=CarPaintMM
   block[1] type=0x2CEC5AD5 payload=7126 span=[13116,20242) name=GeneralMkIII
   block[2] type=0x483304D6 payload=25658 span=[20250,45908) name=CarPaintMM
   sum(header + 3*(4+payload+4)) = 45912  == file size? True
lod2 size=21842 header_len=53 nblocks=3
   block[0] type=0x483304D6 payload=8587 span=[57,8644) name=CarPaintMM
   block[1] type=0x2CEC5AD5 payload=2592 span=[8652,11244) name=GeneralMkIII
   block[2] type=0x483304D6 payload=10586 span=[11252,21838) name=CarPaintMM
   sum(header + 3*(4+payload+4)) = 21842  == file size? True
lod3 size=14590 header_len=53 nblocks=3
   block[0] type=0x483304D6 payload=5455 span=[57,5512) name=CarPaintMM
   block[1] type=0x2CEC5AD5 payload=1214 span=[5520,6734) name=GeneralMkIII
   block[2] type=0x483304D6 payload=7844 span=[6742,14586) name=CarPaintMM
   sum(header + 3*(4+payload+4)) = 14590  == file size? True
```

Then, inside each `GeneralMkIII` payload, every part measured from the bytes (decoded) and summed
(derived):

```
lod1 payload=7126 version=5
   head=842  vcount=176 stride=8  count2=176 stride2=20  icount=672  idx_at=18894
   842 + (4+176*8=1412) + (4+176*20=3524) + (4+672*2=1348) = 7126  exact? True
   triangle count icount/3 = 224 ; max index = 175 (vcount-1 = 175)
   position record s16@+6 == 32767 : 176/176
lod2 payload=2592 version=5
   head=842  vcount=55 stride=8  count2=55 stride2=20  icount=99  idx_at=11042
   842 + (4+55*8=444) + (4+55*20=1104) + (4+99*2=202) = 2592  exact? True
   triangle count icount/3 = 33 ; max index = 54 (vcount-1 = 54)
   position record s16@+6 == 32767 : 55/55
lod3 payload=1214 version=5
   head=842  vcount=12 stride=8  count2=12 stride2=20  icount=12  idx_at=6706
   842 + (4+12*8=100) + (4+12*20=244) + (4+12*2=28) = 1214  exact? True
   triangle count icount/3 = 4 ; max index = 11 (vcount-1 = 11)
   position record s16@+6 == 32767 : 12/12
```

So `7126 = 842 + 1412 + 3524 + 1348`, `2592 = 842 + 444 + 1104 + 202`, `1214 = 842 + 100 + 244 + 28`
hold **exactly**, the head is 842 on all three (measured as `pos_count_at − payload_start`), and every
stream boundary closes on the next `u32` count. The card's §1 table (block 2 = 25658 / 10586 / 7844) also
matches; note block 2 starts at 20250, not 20246, because 7126 bytes end with the trailer at 20242–20245.

The three block type words are `0x483304D6` (CarPaintMM) / `0x2CEC5AD5` (GeneralMkIII) read from the
files; that `0x2CEC5AD5` *is* the GeneralMkIII type comes from `rbm_geom.BLOCK_NAMES` and the on-disk
`renderblockgeneralmkiii.cc` name — **decoded** by name table, not re-derived here.

## 2. The 243 marker words — 176 + 55 + 12 (decoded + derived)

Per vertex, at `+4`, `+6`, `+16` of each 20-byte record (decoded):

```
lod1   markers  s16@+4==32767 176/176   s16@+6==0 176/176   u32@+16==0x487FFFFF 176/176
lod2   markers  s16@+4==32767 55/55     s16@+6==0 55/55     u32@+16==0x487FFFFF 55/55
lod3   markers  s16@+4==32767 12/12     s16@+6==0 12/12     u32@+16==0x487FFFFF 12/12
```

The record is exactly as the card states: `{s16 u, s16 v, s16 32767, s16 0}` + `{f32 a, f32 b, f32
0x487FFFFF}`; `s16@+4` takes the single value 32767 and `s16@+6` the single value 0 on every record of
all three files (`s16@+4 values: [32767]  s16@+6 values: [0]`). 176+55+12 = 243 is arithmetic on those
counts (**derived**).

## 3. `0x487FFFFF` is one ULP below 2^18 — true (decoded)

```
0x487FFFFF = 262143.984375
2**18 = 262144.0 = 0x48800000 ; 0x48800000-1 = 0x487FFFFF
same as bit pattern? True ; 2**18 - 2**-6 = 262143.984375
```

One caveat for anyone re-checking: the binade boundary is **0x48800000**, not 0x48000000 (0x48000000 is
2^17). Decrementing the wrong word makes the claim look false — I hit that on my first pass. The card's
parenthetical `(262143.9844)` is correct to the digits it prints.

## 4. The UV claim on lod1, recomputed per triangle (decoded + derived)

Signed UV area `(p1−p0) × (p2−p0)` per triangle of the 672-index list, computed here rather than read
from the card's script:

```
lod1   s16 uv area signs (pos,neg,zero) = (0, 224, 0) of 224 tris
       float pair area signs           = (136, 88, 0) of 224 tris
       float pair / 2^18 as UV signs   = (136, 88, 0) of 224 tris
lod2   s16 uv area signs               = (0, 33, 0) of 33 tris
       float pair area signs           = (21, 12, 0) of 33 tris
lod3   s16 uv area signs               = (0, 4, 0) of 4 tris
       float pair area signs           = (1, 2, 1) of 4 tris
```

On lod1 the unorm16 pair keeps one winding sign on **224/224** triangles (all negative — a consistent
orientation with a left-handed V, which is why the card's "same sign" wording, not "positive", is the
correct one), and the float pair is **136+/88−**, i.e. exactly the card's rejection number. §4 of
`DECODE_DEPTH4.md` lists lod2/lod3 float-pair signs as 21+/12− and 1+/2−; lod3 actually has **one
degenerate (zero-area) triangle**, which the card drops rather than mis-states — worth knowing, since
"1+/2−" reads as three triangles when the list has four.

The UV field values in §3 also reproduce (decoded): `u` distinct 44/23/8 with min 1906 and max 32767 on
all three, `v` distinct 21/9/3 with min 24171/24262/28269 — the identical `u` minimum 1906 on three
different meshes is a real property of the table, not a typo. Texture table: 20 slots, 4 filled
(`w503_missile_capstone_billfire_{dif,mpm,nrm}.ddsc`, `textures/dummies/dummy_black.ddsc`), matching §2.

## 5. `DECODE_DEPTH4.md` §4: the quoted numbers are present (re-read, not recomputed)

| G3-19b quote | §4 row(s) it comes from | verdict |
|---|---|---|
| normals "best mean dot with the face normals 0.006..0.136" | octahedral: 0.126 / 0.136 / 0.113; float triple: −0.284 / −0.261 / +0.006 | present, but the range is the min/max of **six** means whose other four are negative; "best mean" is doing real work there |
| tangents "\|dot with the surface normal\| 0.28..0.59" | float triple absmean 0.294 / 0.362 / 0.281; s16 pair absmean 0.593 / 0.495 / 0.526 | present; range is 0.281..0.593, rounded down at the top |
| float pair as UV "mixed winding 136+/88−" | 136+/88−, 21+/12−, 1+/2− | present, exact for lod1 |
| skin weights "no weight/index field pair; the block is unskinned" | max float 6.338e+04 / 5.285e+04 / 4.805e+04 + "the record holds no weight/index field pair, and the block is unskinned (single 20-byte stream; the skinned shader variant declares an extra uint4 input)" | present |

Two wording points, both minor:

* G3-19b writes "octahedral / **2-component** / float-triple normals". §4 has no separate 2-component
  row: the octahedral row *is* the 2-component decode of the `(u,v)` pair, so that phrase implies three
  measurements where the table has two.
* §4 also contains a rejected candidate the summary omits: "float triple as a **unit vector**" (worst
  relative error 0.033 / 0.027 / 0.023). Not a contradiction — the summary lists four families, not all
  eight rows — but a reader comparing the two texts will notice the gap.

## 6. The fleet cross-check — how it was counted, and where it is thin

**How `126 blocks / 56,319 vertices` was produced** (read from `decode_depth4.py`, `fleet_check` and
`_check_block`):

* Population A: every `.rbm` name in the Serpente bundle's archive directory, sorted, all blocks.
* Population B: `jc3strings.load_index()`, filter `editor/entities/jc_vehicles/*.ee` → **233** entries
  (I recomputed this: `vehicle .ee bundles in index: 233`), then `step = 233//12 = 19` and
  `ees[::19][:12]` — indices 0, 19, … 209. The twelve are (recomputed here, decoded from the index):
  `v0000_car_autostraad_oldjeep_civilian_01`, `v0008_car_autostraad_modernsportssaloon_debug`,
  `v0300_car_kensington_sportsmuscle_civilian_01`, `v0405_car_mugello_moderncircuitracer_civilian_01`,
  `v0505_car_solar_oldtruck_commercial_01`, `v0510_car_solar_modernroadster_civilian_01`,
  `v0604_car_urga_buggy_military_01`, `v3500_bike_solar_oldmoped_debug`,
  `v5602_train_urga_monorailflatbed_military_containers_rigidobject`,
  `v2602_helicopter_urga_lightassault_rebel_01`, `v4603_plane_urga_cargotransport_debug`,
  `v1302_boat_kensington_sailboat_debug`.
* The block cap is 200 and the census reached 126, so **the cap never truncated anything** — that part
  is clean.
* `seen["blocks"] += 1` happens only *after* `mkiii_layout` succeeds, and `_check_block` then does
  `if lay["stride2"] != 20: return` **before** touching `stride20`, `vertices` or any oracle. Consequences:
  * the two blocks that fail framing (`oldjeep_antenna_lod1/lod2`, stride 16) are *outside* the 126, so
    the real block population of the sample is **128**, not 126 — the doc says "2 block(s) … have no
    uniform 20-byte record", which is the disclosure, but the table row "126 / 126" is not the whole set;
  * "blocks with a uniform 20-byte record 126/126" **cannot fail**: a block with a uniform 24-byte stride
    would be counted in `blocks` and silently skipped by `stride20`. The only reason the row is true is
    that the sample happens to contain no uniform non-20 stride; the row is not evidence of it.
  * `stride2` is `(idx_at − s2_at) // count2` and only computed when the division is exact, so blocks
    whose attribute region does not divide by the vertex count are *excluded* rather than measured.
* `seen["vertices"] += lay["count2"]` — **56,319 is the sum of attribute-record counts, not of position
  counts**; `count2` is never compared with `vcount`. On the three target files they coincide (176/55/12,
  decoded above), but the fleet total also excludes the two interleaved blocks (289+ vertices each per
  the witness row).

**Could 12 of 233 hide a different layout?** Yes, and the sample already shows it does: 20 of 126 blocks
fail the `0x487FFFFF@+16` test, only **28/126** are single-sign UV charts (10 of the 32767 group, 18 of
the 0 group), 8 `buggy_vdova_89` blocks flip winding, and 2 blocks are a different stride. That is 5.2% of
bundles (one variant per family, alphabetical stride — land, air and sea are all represented), so the
sample is *spread*, not *dense*: it can miss a layout confined to a family whose selected variant differs
from the mesh that carries it. What the card does with this is the right thing — it states the fields'
**semantics** are not fleet-wide and keeps the float pair UNKNOWN. The one sentence that over-reaches is
"the *field widths* are the block type's": `oldjeep_antenna` shows a same-type block with stride-16
positions and a non-20 attribute region, so the 20-byte shape is a *variant* of the type, not an invariant
of it. Given the card lists that variant under UNKNOWN #3, this is a wording fix, not a lost result.

## 7. What I could not check

* **The census itself** (3,261 `.rbm`, 128 blocks, 56,319 records) was not re-run — it re-reads the whole
  archive. My statements about it come from the counting code and from the committed `--write` JSON, not
  from a second independent scan, so the *values* 126/56,319 are corroborated only by the card's own run
  plus my reading of the code path. **UNKNOWN** whether a re-scan today gives the same numbers (it should:
  the selection is deterministic, no time budget).
* **The §4 oracle measurements** (mean dots, density spreads, fit residuals, unit-vector errors) were
  checked for *presence and internal consistency*, not recomputed; the card's script is what measured
  them. My independent recomputation covers the sums, the markers, the ULP statement and the UV-area
  signs only.
* **The header sizes** (`Attributes 0x68`, 70-float `MaterialConsts2`, 457-byte table) came from
  `jc3geom`'s primitives; what I verified from the bytes is the resulting head length 842, `version = 5`
  and the 4-of-20 texture table, not the C++ `static_assert`.
* **The meaning of the float pair** stays **UNKNOWN** as the card says; nothing in this review changes
  that, and the shader body is still not on disk (only the 73-line reflection header).
* **`0x487FFFFF` as a scale** is **derived** (a marker that makes a/b unit-ranged), not decoded from a
  shader — same status the card gives it.

## 8. Commands run (verbatim)

```
$ python tmp/freebuff/scratch/g319b_review.py       # first run, wrong ROOT depth
Traceback (most recent call last):
  File "E:\Modding\JustCause3\JC3-Batmobile\tmp\freebuff\scratch\g319b_review.py", line 16, in <module>
    import jc3geom  # noqa: E402
ModuleNotFoundError: No module named 'jc3geom'
EXIT=1
```

(after changing `ROOT = HERE.parent.parent.parent` to `HERE.parents[3]`)

```
$ python tmp/freebuff/scratch/g319b_review.py
=== copies: content identity ===
lod1  copies=4  distinct_sha=1  ['2fdb273b4413cb99']
lod2  copies=4  distinct_sha=1  ['220c6a61f57aa4d8']
lod3  copies=4  distinct_sha=1  ['a009ee26e0299c49']

=== framing + payload sums recomputed ===
lod1 size=45912 header_len=53 nblocks=3
   block[0] type=0x483304D6 payload=13051 span=[57,13108) name=CarPaintMM
   block[1] type=0x2CEC5AD5 payload=7126 span=[13116,20242) name=GeneralMkIII
   block[2] type=0x483304D6 payload=25658 span=[20250,45908) name=CarPaintMM
   sum(header + 3*(4+payload+4)) = 45912  == file size? True
lod2 size=21842 header_len=53 nblocks=3
   block[0] type=0x483304D6 payload=8587 span=[57,8644) name=CarPaintMM
   block[1] type=0x2CEC5AD5 payload=2592 span=[8652,11244) name=GeneralMkIII
   block[2] type=0x483304D6 payload=10586 span=[11252,21838) name=CarPaintMM
   sum(header + 3*(4+payload+4)) = 21842  == file size? True
lod3 size=14590 header_len=53 nblocks=3
   block[0] type=0x483304D6 payload=5455 span=[57,5512) name=CarPaintMM
   block[1] type=0x2CEC5AD5 payload=1214 span=[5520,6734) name=GeneralMkIII
   block[2] type=0x483304D6 payload=7844 span=[6742,14586) name=CarPaintMM
   sum(header + 3*(4+payload+4)) = 14590  == file size? True

=== block 1 internals, recomputed from bytes ===
lod1 payload=7126 version=5 attrs_bbox=[-0.20952381193637848, 1.087841510772705, -1.5710318088531494]..[0.20929282903671265, 1.1404316425323486, -1.484980821609497]
   head=842  vcount=176 stride=8  count2=176 stride2=20  icount=672  idx_at=18894
   842 + (4+176*8=1412) + (4+176*20=3524) + (4+672*2=1348) = 7126  exact? True
   triangle count icount/3 = 224 ; max index = 175 (vcount-1 = 175)
   position record s16@+6 == 32767 : 176/176
   markers  s16@+4==32767 176/176   s16@+6==0 176/176   u32@+16==0x487FFFFF 176/176
   float a range 123.496094..31488.492188   b range 1679.628906..63383.628906   in [0,1) after /2^18: a 176/176 b 176/176
   s16 uv area signs (pos,neg,zero) = (0, 224, 0) of 224 tris
   float pair area signs           = (136, 88, 0) of 224 tris
   float pair / 2^18 as UV signs   = (136, 88, 0)
lod2 payload=2592 version=5 attrs_bbox=[-0.20952381193637848, 1.087841510772705, -1.5526179075241089]..[0.20233747363090515, 1.1367062330245972, -1.484980821609497]
   head=842  vcount=55 stride=8  count2=55 stride2=20  icount=99  idx_at=11042
   842 + (4+55*8=444) + (4+55*20=1104) + (4+99*2=202) = 2592  exact? True
   triangle count icount/3 = 33 ; max index = 54 (vcount-1 = 54)
   position record s16@+6 == 32767 : 55/55
   markers  s16@+4==32767 55/55   s16@+6==0 55/55   u32@+16==0x487FFFFF 55/55
   float a range 12484.773438..51934.347656   b range 2683.691406..52851.882812   in [0,1) after /2^18: a 55/55 b 55/55
   s16 uv area signs (pos,neg,zero) = (0, 33, 0) of 33 tris
   float pair area signs           = (21, 12, 0) of 33 tris
   float pair / 2^18 as UV signs   = (21, 12, 0)
lod3 payload=1214 version=5 attrs_bbox=[-0.08371978998184204, 1.0999222993850708, -1.5585724115371704]..[0.06946782767772675, 1.1371264457702637, -1.4862327575683594]
   head=842  vcount=12 stride=8  count2=12 stride2=20  icount=12  idx_at=6706
   842 + (4+12*8=100) + (4+12*20=244) + (4+12*2=28) = 1214  exact? True
   triangle count icount/3 = 4 ; max index = 11 (vcount-1 = 11)
   position record s16@+6 == 32767 : 12/12
   markers  s16@+4==32767 12/12   s16@+6==0 12/12   u32@+16==0x487FFFFF 12/12
   float a range 21895.027344..44923.957031   b range 25081.570312..48050.105469   in [0,1) after /2^18: a 12/12 b 12/12
   s16 uv area signs (pos,neg,zero) = (0, 4, 0) of 4 tris
   float pair area signs           = (1, 2, 1) of 4 tris
   float pair / 2^18 as UV signs   = (1, 2, 1)

=== float bits ===
0x487FFFFF = 262143.984375
2**18 = 262144.0 = 0x48800000 ; 0x48800000-1 = 0x487FFFFF
same as bit pattern? True ; 2**18 - 2**-6 = 262143.984375
EXIT=0
```

```
$ python tmp/freebuff/scratch/g319b_review2.py
lod1 u distinct=44 min=1906 max=32767 | v distinct=21 min=24171 max=32767 | texture slots=20
   textures: ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'models/jc_weapons/06_vehicle/w503_missile_capstone_billfire/textures/w503_missile_capstone_billfire_dif.ddsc', 'models/jc_weapons/06_vehicle/w503_missile_capstone_billfire/textures/w503_missile_capstone_billfire_mpm.ddsc', 'models/jc_weapons/06_vehicle/w503_missile_capstone_billfire/textures/w503_missile_capstone_billfire_nrm.ddsc', 'textures/dummies/dummy_black.ddsc']
   s16@+4 values: [32767]  s16@+6 values: [0]
lod2 u distinct=23 min=1906 max=32767 | v distinct=9 min=24262 max=32767 | texture slots=20
   s16@+4 values: [32767]  s16@+6 values: [0]
lod3 u distinct=8 min=1906 max=32767 | v distinct=3 min=28269 max=32767 | texture slots=20
   s16@+4 values: [32767]  s16@+6 values: [0]
EXIT=0
```

```
$ python -c "import sys; sys.path.insert(0,'Tools/scripts'); import jc3strings; ..."
vehicle .ee bundles in index: 233
max_entities=12 -> step = 19  -> selected indices [0, 19, 38, 57, 76, 95, 114, 133, 152, 171, 190, 209]
selected: 12
  [ 0] editor/entities/jc_vehicles/01_land/v0000_car_autostraad_oldjeep/v0000_car_autostraad_oldjeep_civilian_01.ee
  [ 1] editor/entities/jc_vehicles/01_land/v0008_car_autostraad_modernsportssaloon/v0008_car_autostraad_modernsportssaloon_debug.ee
  [ 2] editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.ee
  [ 3] editor/entities/jc_vehicles/01_land/v0405_car_mugello_moderncircuitracer/v0405_car_mugello_moderncircuitracer_civilian_01.ee
  [ 4] editor/entities/jc_vehicles/01_land/v0505_car_solar_oldtruck/v0505_car_solar_oldtruck_commercial_01.ee
  [ 5] editor/entities/jc_vehicles/01_land/v0510_car_solar_modernroadster/v0510_car_solar_modernroadster_civilian_01.ee
  [ 6] editor/entities/jc_vehicles/01_land/v0604_car_urga_buggy/v0604_car_urga_buggy_military_01.ee
  [ 7] editor/entities/jc_vehicles/01_land/v3500_bike_solar_oldmoped/v3500_bike_solar_oldmoped_debug.ee
  [ 8] editor/entities/jc_vehicles/01_land/v5602_train_urga_monorailflatbed/v5602_train_urga_monorailflatbed_military_containers_rigidobject.ee
  [ 9] editor/entities/jc_vehicles/02_air/v2602_helicopter_urga_lightassault/v2602_helicopter_urga_lightassault_rebel_01.ee
  [10] editor/entities/jc_vehicles/02_air/v4603_plane_urga_cargotransport/v4603_plane_urga_cargotransport_debug.ee
  [11] editor/entities/jc_vehicles/03_sea/v1302_boat_kensington_sailboat/v1302_boat_kensington_sailboat_debug.ee
EXIT=0
```

Also run, for the frame offsets: `python -c "... b[:32].hex(); find 0x2CEC5AD5 / 0x89ABCDEF"` →
`size 45912`, `first 32 bytes 0500000052424d444c010000001000000000000000cce497bea1c8803f9217c9`,
`hash 0x2CEC5AD5 LE [13112]`, `trailer 0x89ABCDEF LE [13108, 20242, 45908]` — the same framing the
section-1 table shows.

Scratch probes (not deliverables): `tmp/freebuff/scratch/g319b_review.py`, `g319b_review2.py`.

## 9. Files written

* `tmp/freebuff/reports/review-G3-19b.md` (this file)

Nothing else was created, edited or deleted; `decode_depth4.py`'s own `--check` was **not** re-run (the
card's report records it passing on the same bytes, and I did not want to re-run the 3,261-file census).
