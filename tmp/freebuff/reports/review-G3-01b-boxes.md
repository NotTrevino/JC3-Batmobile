# Review — G3-01b-boxes (box rotations, the 0x4C tag, every byte of the box record)

Reviewer: independent (did not write the card). Reviewed: `tmp/freebuff/reports/G3-01b-boxes.md`,
`Research/BatmobileGrab/COLLISION_BOXES.md` (266 lines), `COLLISION_BOXES.json` (10 keys,
138,630 B), `Tools/scripts/grab_collision_boxes.py` (1,278 lines). Sources re-read directly:
`BmGame.upk` (exports 169750, 169751), `Playable_Batmobile_SF.upk`, `COLLISION_CONVEX.json`,
`Research/BatmobileGrab/BMSDK_OFFSETS.json`, and the BmSDK-AK layout tree named in the task
brief (`E:/Modding/_shared/tools/BmSDK-AK`, MIT). Nothing was written except this file; no game was
launched or attached; no git operations.

## VERDICT: **minor issues**

The decoded record, the byte accounting, the extents verdict and every label I could test
reproduce from the raw bytes. `--check` passes and the `.md`/`.json` on disk are the tool's
output, not a hand edit. The verdict itself is correct — and it is *under-proven*, not wrong.

The issues are of three kinds, none of which overturns a value:

1. **Three UNKNOWNs are resolvable from evidence the task brief already names** (U-1, U-2, U-3),
   because the card searched only `BMSDK_OFFSETS.json`'s 41 classes, not the BmSDK-AK tree.
2. **The strongest oracle in the record was not used**: export 169750 carries its own convex
   element, whose decoded vertices bound the *same bone in the same frame*. It settles
   full-vs-half lengths to 0.04 % on X instead of the 30 %-tolerance cross-body comparison used.
3. Wording/labelling: a phrase that points at the wrong offset, "two independent tests" that are
   one comparison, containment that ignores the rotation the card itself decoded, and an implied
   upgrade of a derived convention.

No decoded value is wrong. No UNKNOWN is a false negative introduced by the bytes.

## 1. Check output (verbatim)

```
$ uv run --with numpy --with pillow --with pefile --with capstone python Tools/scripts/grab_collision_boxes.py --check
OK: 131 boxes (3 BmGame + 128 wreck), 2 byte-mapped payloads, rotations 3/131, extents FULL lengths, 14/14 checks, md byte-identical
EXIT=0
```

Matches the report's quoted line character for character, and `md byte-identical` means the
`COLLISION_BOXES.md`/`.json` on disk are a fresh rebuild, so the doc was not edited by hand after
generation. I did not run `--write` (it would rewrite the card's outputs for no gain).

## 2. Spot-checks (value, source, match)

All five were re-read with my own `struct.unpack_from` calls on `p.data(export)` after locating
the AggGeom payload by the TM-tag byte pattern — no import of the card's decoder.

| # | value the card labels decoded | my raw read | source | match |
|---|---|---|---|---|
| 1 | TM struct tag: `type 10`, `offset 0`, name index **78655 → `TM`**, `size 64`, `array_index 0` | `10, 0, 78655, 0, 64, 0`; `names[78655] == 'TM'` | `BmGame.upk` export 169750, payload byte 8 | **yes** |
| 2 | Extents `690.305 / 374.536 / 207.500` at logical `0x40 / 0x44 / 0x48` | `690.304993 / 374.536072 / 207.500000`, tags `(type 4, off 0x40/0x44/0x48)` | same payload, bytes 92/100/108 and their 4-byte values | **yes** |
| 3 | `0x4C` word `0x40`, bit 6 only (chassis box 0); word `0` on chassis box 1 and the weapons box | tag `(type 3, off 0x4C)`, payload `0x00000040`; the other two `0x00000000` | same payload, byte 116 (box 0) / 234 (box 1); 169751 byte 116 | **yes** |
| 4 | Chassis box 0 TM = identity 3x3, translation `(9.0, 0.0, 106.75)`; quads lead `0,0,0,1` | rows `(1,0,0),(0,1,0),(0,0,1)`, translation `9.0 / 0.0 / 106.75`, quad leads `[0.0,0.0,0.0,1.0]` | same payload, bytes 28–92 | **yes** |
| 5 | 169751 extents `166.177 / 189.365 / 39.800`, 3x3 rows `(0.998,0,−0.070),(0,1,0),(0.070,0,0.998)`, translation `(−30.5, 0.0, 93.25)` | `166.176926 / 189.364883 / 39.800056`; rows `(0.997564, 0, −0.069756),(0,1,0),(0.069756,0,0.997564)`; translation `−30.499996 / 0.0 / 93.25` | `BmGame.upk` export 169751, payload bytes 8–126 | **yes** |

Two extra checks, because the report's headline claim ("every byte mapped") is the risky one:

| # | claim | my raw read | match |
|---|---|---|---|
| 6 | 169750: `u32 0` at 244, `convex_count 1` at 248, convex element 1,498 B, footer 9 B, **1759/1759** mapped; `ElemBox == vertex bounds` | 244 → `0`; 248 → `1`; 252 → `nV 12`; bytes 252…1750 = the element; footer `000000000000000000` at 1750; AggGeom tag declares `size 1759`. At each of the card's own offsets the counts read `nP 9, nI 60, nE 25, nX 19, nY 20, nZ 14`, and the blocks close exactly: `252+4+144=400`, `+4+144=548`, `+4+240=792`, `+4+300=1096`, `+4+228=1328`, `+4+320=1652`, `+4+56=1712`, `+24=1736`, `+14=1750`, `+9=1759`. `ElemBox` at 1712 = `−339.25, −169.5, 40.5, 350.75, 175.5, 227.75` = vertex bounds, max diff 0.0 | **yes** |
| 7 | 169751: boxes to 126, `u32 0`, `u32 0`, 9-byte footer, **143/143**; wreck boxes are single-box, identity, word `0`, TM named `TM` | 126 → `0`, 130 → `0`, footer `000000000000000000` at 134, declared `size 143`. `Playable_Batmobile_SF`: TM name index 2846, exports 5066/5067/5068 = `spheres 0, boxes 1`, identity, word `0x0`, extents `30.3³`, `211.54/51.09/109.00`, `157.80/60.06/110.26` | **yes** |

Spot-check 2 is worth one note: the card's byte map gives block *sizes* (e.g. `796 | 300 |
convex_edge_vectors`) but not the per-record stride; the implied strides are `nP` 16 B, `nI` 4 B,
`nE` 12 B, `nX` 12 B, `nY` 16 B, `nZ` 4 B. A reader cannot re-derive the block boundaries from
the `.md` alone (the `.json` presumably carries them). Minor documentation gap.

## 3. Issues

### I-1 · U-1 is a scope gap, not an absent layout — the bit has a name

The card: *"Searched `BMSDK_OFFSETS.json`: only 41 classes … no `FKBoxElem`/aggregate struct, so
no local layout names the member or the bit."*

That is true of that file — I verified `BMSDK_OFFSETS.json` has **zero** occurrences of
`FKBoxElem`, `FKSphylElem`, `FKAggregateGeom`, `AggGeom`, `BoxElem` or `Sphyl`, and exactly 41
classes. But the task brief names BmSDK-AK itself as an evidence source, and that tree ships
generated native layouts. `E:/Modding/_shared/tools/BmSDK-AK/src/BmSDK/Generated/Engine/KMeshProps.g.cs`,
struct `FKBoxElem` (line 413):

| offset | member | SDK evidence |
|---:|---|---|
| 0 | `TM` (FMatrix) | `ToManaged<FMatrix>(Ptr + 0)` |
| **64 = 0x40** | `X` | `Ptr + 64` |
| **68 = 0x44** | `Y` | `Ptr + 68` |
| **72 = 0x48** | `Z` | `Ptr + 72` |
| **76 = 0x4C** | 7 BoolProperties, masks 1,2,4,8,16,32,64 | see below |

The seven bools at `Ptr + 76` and their masks (same file):

| mask | member |
|---:|---|
| 1 | `bIsAxisAligned` |
| 2 | `bHasCookedAlignmentData` |
| 4 | `bNoRBCollision` |
| 8 | `bPerPolyShape` |
| 16 | `bNoClipNavMesh` |
| 32 | `bOptionalRBCollision` |
| **64** | **`bInterVehicleCollision`** |

The offsets are the decoded ones *exactly* (0x40/0x44/0x48/0x4C, struct size 80 = 0x50), so the
element the card calls "the box record" is `FKBoxElem`, and the word at 0x4C with **bit 6 set on
`Batmobile_Chassis` box 0 only** is `bInterVehicleCollision`. That is a *named* member from an
SDK layout, not a guess — but it is SDK-derived, not game-byte-derived, so it belongs in the
record as "decoded from BmSDK-AK layout; offsets corroborated by the decoded tags", and the
0x4C row should lose its UNKNOWN, keeping only "no behaviour observed for the flag".

### I-2 · U-2 is resolvable — the third count is the sphyl count

The card keeps "which element type the zero count before the convex count belongs to" UNKNOWN
because no decoded body contains a sphere or sphyl element. The SDK answers it structurally:
`FKAggregateGeom` (same file, line 97) declares `SphereElems` @ 0, `BoxElems` @ 16,
**`SphylElems` @ 32**, `ConvexElems` @ 48. Counts precede their arrays in the decoded payload
(`sphere_count`, `box_count`, boxes…, third count, convex count), so the third count is the
**SphylElems** count and the fourth the **ConvexElems** count. The bytes agree (`0` then `1` in
169750; `0` then `0` in 169751). The card's working name `sphyl_or_third_count` can be settled.

### I-3 · U-3 is resolvable — the planes are rows, so the 4° sign is fixed

The card reports the weapons box as `axis (0,−1,0), angle ±4.00 deg (sign conditional: R vs Rᵀ is
not decidable from one matrix)`. `FMatrix`
(`src/BmSDK/Generated/Core/GameObject.g.cs:4708`) is `XPlane`@0, `YPlane`@16, `ZPlane`@32,
`WPlane`@48, and `FPlane` is 16 B. The decoded 64 bytes are four quads
`(0, r0), (0, r1), (0, r2), (1, tx, ty, tz)` — the fourth quad is the homogeneous **translation
plane with W = 1**, so the three 3-float groups are the matrix's rows and reading A is the
rotation block itself, not its transpose.

With rows fixed, the stored matrix is

```
R = [ 0.997564  0  -0.069756 ]
    [ 0         1   0        ]
    [ 0.069756  0   0.997564 ]
```

which is `Ry(−4.00°)`, i.e. **+4.00° about (0, −1, 0)** — the sign the card left conditional. The
`±` can be dropped.

Caveat to record with it: the cooked serialisation puts each plane's **W first**
(leading floats `0, 0, 0, 1`), which is *not* the SDK's `FPlane` field order (`W` at +12, i.e.
`X,Y,Z,W`). Under the SDK's order the same bytes would make the rows singular — which is
precisely the card's reading B, already rejected 0/131 by orthonormality. So the row conclusion
is safe, but the W-first quirk is a real serialisation detail that a later tool must not assume
away.

### I-4 · The decisive oracle was in the same export and was not used

The verdict rests on `COLLISION_CONVEX.json`'s hull for a *different* export (169749), compared
as **sorted** spans with a 30 % tolerance and a 30 cm containment budget. Export 169750 contains
a better one: its single convex element (the one the card already decodes and checks
`ElemBox == vertex bounds` on) has 12 vertices in the same bone, same frame:

| quantity | value (cm) |
|---|---|
| convex element vertex bounds | min `−339.25, −169.5, 40.5` / max `350.75, 175.5, 227.75` |
| convex span | **690.0 / 345.0 / 187.25** |
| chassis box 0 stored | 690.305 / 374.536 / 207.500 |
| 0-0 deviation as **full** lengths | **0.04 % / 8.6 % / 10.8 %** |
| the same as **half** lengths | 100.1 % / 117.1 % / 121.6 % |

So full lengths are established inside one export, one bone, one frame, with no sorted matching,
no cross-body assumption and no tolerance to tune — a 2× reading is off by more than 100 % where
the full reading is off by 10.8 % at worst. The card's conclusion is right; the evidence it quotes
is the weaker of the two available. It should adopt this as the primary oracle (and keep the
cross-body hull as a consistency finding). Side finding the same test exposes: box 0 is genuinely
8.6 % wider in Y than the same body's convex hull (374.5 vs 345.0 cm), consistent with the
28.1 cm overhang the card reports against 169749.

### I-5 · "Two independent mechanical tests" is one comparison measured twice

The span-match and the containment test use the same hull, the same extents and the same
full/half premise; they are two statistics of one comparison, not independent oracles. The card's
own U-5 correctly declines to count the wreck union, which leaves exactly one line of evidence —
strong, but single. I-4 is what would make it two.

### I-6 · Containment ignores the rotation the card decoded

`max_overhang` is computed from `t ± e/2`, i.e. axis-aligned intervals, while the weapons box
carries a 4° Y rotation and the report says *"the largest distance by which a box's interval
leaves the hull's interval"* — true of intervals, but the table is read as box containment. It
changes nothing here (the rotated weapons box's worst axis grows by ≈2.3 cm on X and it sits
≥66 cm inside on every axis), but the label should say "axis-aligned interval containment" or the
corners should be rotated.

### I-7 · Wording that points at the wrong offset

*"The translation is byte-identical to the 12 bytes before the tag stream that `grab_physics.py`
read as the centre"* — the TM tag stream starts at payload byte 8, so 12 bytes before it is
outside the payload. The earlier tools meant 12 bytes before the **extent tags** (box 0: bytes
80–92; box 1: 198–210), which is exactly where floats 13–15 of each TM sit and my spot-check
confirms the values. The claim is true; the sentence is not, and it appears in both the report and
the `.md`.

### I-8 · Unlabelled provenance for the two hulls

*"the battle-mode hull (169748)"* and *"the pursuit mesh (169749)"* are not decoded by this card;
they come from G3-01c's export object names (`Batmobile_V2 battle mode`,
`Batmobile_V2_Collision_Pursuite`, `COLLISION_CONVEX.md` lines 35 and 90). The report should cite
that rather than assert the names.

### I-9 · "Decoded-structure + oracle result" overstates the convention's status

The report: *"the old 'derived/conditional' label on that value can now be upgraded to a
decoded-structure + oracle result"*. The *structure* is decoded; the *convention* (a stored float
is a full length) is inferred by an oracle and must stay labelled **derived + oracle-confirmed** —
the bytes do not name it. The `.md` labels the rule `derived:` correctly (`COLLISION_BOXES.md`,
"Oracle: are the extents full or half lengths?"), so this is a report-wording issue only.

### I-10 · Cosmetic

- `--check` prints `rotations 3/131`; 131/131 boxes have a decoded rotation record and exactly 1
  is non-identity. The token cannot be read either way.
- The card calls the fields "Extent X/Y/Z"; the SDK member names are `X`, `Y`, `Z` (offset names
  are the decoder's, not the format's).
- The `.md` block sizes (I-2/spot-check note) omit the per-record strides.

## 4. Resolvable UNKNOWNs (how)

| card | status after this review | how, and what it rests on |
|---|---|---|
| **U-1** — name/meaning of the 0x4C bool | **resolvable** | BmSDK-AK `Engine/KMeshProps.g.cs` `FKBoxElem`: 7 bools at `Ptr + 76`; mask 64 = `bInterVehicleCollision`, which is the bit set (`0x40`) on `Batmobile_Chassis` box 0. SDK layout, offsets corroborated by the decoded tags (0x40/0x44/0x48/0x4C, size 0x50). Behaviour of the flag still unobserved → keep that half UNKNOWN. |
| **U-2** — which element type the zero count counts | **resolvable** | `FKAggregateGeom`: `SphereElems`@0, `BoxElems`@16, `SphylElems`@32, `ConvexElems`@48 → third count = sphyls, fourth = convex. Payload agrees (0, then 1 / 0 / 0). |
| **U-3** — rows vs columns / the tilt's sign | **resolvable** | `FMatrix` = four planes, `WPlane` carries the translation; the decoded fourth quad is `(1, tx, ty, tz)` ⇒ planes are rows ⇒ `R = Ry(−4.00°)` i.e. +4.00° about `(0,−1,0)`. Note the W-first cooked order (differs from `FPlane`'s `X,Y,Z,W`). |
| **U-4** — StaticMesh `Bounds` as a second extents oracle | **stays UNKNOWN** (confirmed, not just "not tried") | The BmSDK-AK tree ships no `Engine/StaticMesh.g.cs` (only `*StaticMesh*Component/Actor*` files), so even the layout source does not give the member or a cooked offset. The card's negative is stronger than it claims and should say so. |
| **U-5** — the wreck-union size test | **moot** | The convention is fixed inside 169750 (I-4), so the wreck union no longer has to decide anything. The card's numbers can stay as a recorded inconsistency; the reason it "does not decide" is no longer load-bearing. |

Nothing in the bytes contradicts anything in the card. The three resolvable items are additions,
not corrections, and none of them moves a value: `bInterVehicleCollision`, `SphylElems`,
`Ry(−4°)` are names/signs the card left open, and the extents verdict is unchanged.

## 5. Reproduction

```
uv run --with numpy --with pillow --with pefile --with capstone python Tools/scripts/grab_collision_boxes.py --check
# OK: 131 boxes (3 BmGame + 128 wreck), 2 byte-mapped payloads, rotations 3/131, extents FULL lengths, 14/14 checks, md byte-identical   (exit 0)
```

My own reads used `upk_read.Package.data(export)` plus `struct.unpack_from`, locating the AggGeom
payload by the `(10, 0, 78655, 0, 64, 0)` tag pattern and stepping back 8 bytes to the header —
independent of `grab_collision_boxes.py`, `agg_of` and `parse_element`.

State left behind: only this review file. `COLLISION_BOXES.md`/`.json`, `GRAB_BACKLOG.md`,
`MODLOG.md`, `STATUS.md` and all tools are untouched.
