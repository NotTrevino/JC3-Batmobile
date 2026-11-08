# Independent review — G3-12 (JC3 donor decode depth)

**VERDICT: minor issues.** Every decoded number I re-read reproduces exactly, and the grading is
conservative rather than flattering. Two prose quantities are wrong (one label, one arithmetic),
and the record is now stale against its own successor card G3-12b, which changes two of its grades
and answers two of its UNKNOWNs without the record pointing at it. No rework of the census is
needed.

Artifact under review: `Research/JC3Grab/DECODE_DEPTH.md` (661 lines),
`Research/JC3Grab/DECODE_DEPTH.json` (289,226 B), `Tools/scripts/decode_depth.py` (46,963 B).
I did not write this card and changed nothing outside this report.

## 1. `--check` output (verbatim)

```
$ cd /e/Modding/JustCause3/JC3-Batmobile && uv run --with numpy --with pillow --with pefile --with capstone python Tools/scripts/decode_depth.py --check; echo "CHECK_EXIT=$?"
ok   the bundle's own directory gives the 566 census exactly (566 files, .ctunec 17, .ddsc 116, .effc 74, .epe 1, .etunec 2, .fmod_guids 1, .ftunec 1, .lod 59, .pfxc 4, .physicsc 1, .rbm 198, .stringlookup 1, .trim 60, .vmodc 31)
ok   every file has a grade and a decoder, and each decoder/oracle pair is the one its extension gets
ok   the grades sum to the file count (441 + 121 + 4 = 566)
ok   the per-file grade agrees with the per-file evidence column (ADF files carry total==len and a non-zero row count; every ddsc carries a closing container)
ok   the .rbm oracle is a real round trip: 195 byte-identical, 3 without a codec, and those 3 are all GeneralMkIII signature missiles (sportsmuscle_missile_base_signature_lod1.rbm, sportsmuscle_missile_base_signature_lod2.rbm, sportsmuscle_missile_base_signature_lod3.rbm)
ok   the .ddsc container closes on every file (magic AVTX and 128 + size == len): 116/116
ok   every ADF file's header `total` equals its length (186 files) and the padding the accounting had to allow is all zero and <= 16 B
ok   the .physicsc class census is the live one (54 hulls, 18 extern meshes, typed from the virtual fixup table): CPfxPartIndexProperty 98, hkRefCountedProperties 92, hknpShapeMassProperties 56, hknpConvexPolytopeShape 54
ok   not one hull/mass-property claim is invented: the hull class is the only shape graded FULL and mass properties are NAMED-ONLY
ok   the constraint classes the card asks about are present and are graded NAMED-ONLY, with their counts: hkpLimitedHingeConstraintData 9, hkpRagdollConstraintData 2
ok   the 16 classes are all accounted for: every one has a grade, and the only FULL shape class is the convex polytope (16 classes)
ok   every partial/named-only file is in the open-item list, tied to a requirement (125 open items, 5 requirements)
ok   no FULL grade rests on a name alone: for every extension that has FULL files, the decoder and the oracle are both named (never `none`)
ok   the 19 reference entries (offset 0) are read from the archives and are not graded as embedded bytes
ok   E:\Modding\JustCause3\JC3-Batmobile\Research\JC3Grab\DECODE_DEPTH.md is byte-identical to a fresh census
ok   E:\Modding\JustCause3\JC3-Batmobile\Research\JC3Grab\DECODE_DEPTH.json is byte-identical to a fresh census

OK: 14/14 checks, md identical, json identical
CHECK_EXIT=0
```

## 2. Spot-checks — six values re-read from the raw source by me

Method: the entity bundle read myself (`bm_rc.vfs` → `eetoc.unaaf` → `eetoc.sarc_dir`, whose source
I printed: entries are `(name, offset, size)`, `offset == 0` = reference read through `bm_rc.vfs`),
then each payload decoded with the project reader the card names (`jc3adf.Adf`, `rbm_geom.decode`,
`jc3hkx.Packfile`, raw `struct` for `.ddsc`/`.lod`).

| # | value in the record | my source | match |
|---|---|---|---|
| 1 | 566 files, extension census `rbm 198, ddsc 116, effc 74, trim 60, lod 59, vmodc 31, ctunec 17, pfxc 4, etunec 2`, one each of `fmod_guids/physicsc/stringlookup/ftunec/epe`; 79.9 MB total | my own `sarc_dir` walk of the `.ee`: **566** entries, identical histogram, `sum(size) = 79,922,183` | **yes** |
| 2 | `.ddsc` closes `AVTX`, `u32[8] + u32[9] == len` (128 + payload) on 116/116 | `t_velocity_streak_alpha_dif.ddsc` 640 B: `AVTX`, 128 + 512 = 640; `t_explosiongrid_fume_06_gold_alpha_dif.ddsc` 22,369,776 B (a **reference** entry): 128 + 22,369,648 = 22,369,776 | **yes** |
| 3 | `.rbm` 195 byte-identical; the 3 failures are `sportsmuscle_missile_base_signature_lod1/2/3` because the codec has no `GeneralMkIII` serializer | `sportsmuscle_body_lod1.rbm` 403,514 B → `decode().write() == bytes` **True**; `sportsmuscle_missile_base_signature_lod1.rbm` 45,912 B → raises `RbmError: block 1 is GeneralMkIII, which this codec does not parse (need its serializer to …)` | **yes** |
| 4 | ADF family: header `total` == file length on 186 files | three files: `vehicle_motion.ctunec` 8,949 = 8,949; `action_noise.ctunec` 6,099 = 6,099; `car_base.ctunec` 5,968 = 5,968 | **yes** |
| 5 | `.physicsc` 340,368 B, **430 objects in 16 classes**, with the per-class counts (98/92/56/54/36/20/20/18/18/9/2/2/2/1/1/1) | my `jc3hkx.Packfile` read: len 340,368, **430 objects, 16 classes**, every count identical to §2 of the card (`CPfxPartIndexProperty 98`, `hkRefCountedProperties 92`, `hknpShapeMassProperties 56`, `hknpConvexPolytopeShape 54`, `hkGeometry 36`, `hknpDynamicCompoundShape 20`, `hknpDynamicCompoundShapeData 20`, `hknpExternMeshShape 18`, `hknpExternMeshShapeData 18`, `hkpLimitedHingeConstraintData 9`, `hknpStaticCompoundShape 2`, `hknpStaticCompoundShapeData 2`, `hkpRagdollConstraintData 2`, `hkRootLevelContainer 1`, `hknpPhysicsSceneData 1`, `hknpPhysicsSystemData 1`) | **yes** |
| 6 | `.lod` 59 files, all re-join; **16** carry a `-` slot line (mshswap parts, seats, engine) | my read: 59 `.lod`, `sep.join(split(sep)) == bytes` on **59/59**, and **16** contain a line that is exactly `-` | **yes** |

Not re-read by me, so not claimed as verified: the `.epe` ConvertProperty diff at `0x765` (needs the
Gibbed executable), the fleet-wide `18865/18865` hull blocks and supporting planes (`jc3hkx check
--all`), and the `41 of 6382` unexplained compound AABBs. Each is labelled with its own oracle in
the card, and each grade is the conservative side of what it proves, so none of them is an
over-claim — they are simply outside what I could re-derive cheaply.

## 3. Issues

### I-1 (must fix, arithmetic): "three quarters of the bundle" is 92 %

- **Where:** `DECODE_DEPTH.md:36` — *"`.ddsc` (116, 73640512 bytes - three quarters of the bundle)"*.
- **Why:** 73,640,512 / 79,922,183 = **92.1 %**, not ~75 %. Measured against the bytes actually
  stored inside the `.ee` (13,509,463 B — see I-2) the `.ddsc` total is larger still, so the
  sentence's denominator is ambiguous as well as wrong. **Fix:** say "92 % of the 79.9 MB of listed
  file sizes (most of it referenced from the archives)".

### I-2 (should fix, label): "79.9 MB of inner bytes" — 83 % of it is not inside the `.ee`

- **Where:** `DECODE_DEPTH.md:3` — *"Every one of the **566** inner files of the … `.ee` (79.9 MB of
  inner bytes)"*.
- **Why:** the 79,922,183 B is the sum of the 566 directory entries, and **19 of them have
  `offset == 0`** — references whose bytes live in the archives, totalling **66,412,720 B**. The
  bytes physically inside the entity bundle are **13,509,463 B**. The card's own check 14 says
  exactly this ("the 19 reference entries (offset 0) are read from the archives and are not graded
  as embedded bytes"), so the header line contradicts the check. **Fix:** "566 files listed by the
  entity (79.9 MB of file sizes; 13.5 MB stored inside the bundle, 66.4 MB referenced from the
  archives)".

### I-3 (must fix, staleness): the `.pfxc` grade and UNKNOWN are superseded by G3-12b

- **Where:** `DECODE_DEPTH.md:24` (`.pfxc … decoder none, oracle none`), `:38`
  (*"no script in `Tools/scripts` opens a `.pfxc`"*), `:342-345` and `:642` (per-file NAMED-ONLY
  reasons), `:651` (UNKNOWN "`.pfxc` payload … where it would be answered: a PFX container reader").
- **Why:** `Tools/scripts/decode_depth2.py` and `Research/JC3Grab/DECODE_DEPTH2.md` exist in the
  tree (written after this record) and **do open all 4 `.pfxc`**: `PFX\0` wrapper, Havok packfile
  located by its own `0x57E0E057` magic at **0x44**, parsed by `jc3hkx.Packfile`, 7 objects per file
  typed from the fixpoint table, with a 512-byte trailing blob left UNKNOWN — grade **PARTIAL**,
  not NAMED-ONLY. So "nothing in the project opens one" is now false, and the named "where it would
  be answered" already exists. The record contains **no reference to `decode_depth2`,
  `DECODE_DEPTH2` or `G3-12b`** (grep over the md: 0 hits), so a reader cannot tell the grade is
  stale. **Fix:** add a "superseded by G3-12b" line to the `.pfxc` row, the open-item row and the
  UNKNOWN, without changing the historical grade.

### I-4 (should fix, staleness): `.ddsc` 0 FULL / 116 PARTIAL, and the texel UNKNOWN, are superseded

- **Where:** `DECODE_DEPTH.md:24`, `:36`, `:643` (appearance open item), `:650` (UNKNOWN
  "`.ddsc` texel payload … no project decoder reads it").
- **Why:** `DECODE_DEPTH2.md` decodes the header by offset (magic, version, dimension, format id,
  width/height, mip counts, header 128, payload size), **derives** the format-id → 4×4-block-size
  map from the fleet (77→16, 71→8, 87→64, 83→16 B, each the only size whose chain sums to
  `size_body`), and tiles the 1013 mip ranges to EOF: **71 FULL / 45 PARTIAL**, the remainder being
  the header tail `0x2C..0x80` on the 45 files whose tail is non-zero. The card's claim that the
  payload is unread and the format id unmapped is therefore out of date. Same fix as I-3.
- Note: this is *not* a criticism of the original grading. At 02:11, when G3-12 ran, no project
  decoder read a `.ddsc`; the defect is that the record does not name the successor that changed it.

### I-5 (minor, presentation): the per-file `what is not read` column is a fixed template

- **Where:** `DECODE_DEPTH.md:88-121` and every other `.ddsc` row.
- **Why:** each of the 116 rows repeats the same sentence with only the byte arithmetic and the
  format id varying, so the column looks per-file-specific but is boilerplate. The underlying
  numbers are right (I checked two rows' arithmetic against the raw files). Not wrong — just easy
  to mistake for per-file analysis. Low priority.

## 4. UNKNOWNs that the bytes can resolve (or that already are resolved)

| unknown | status and how |
|---|---|
| **`.pfxc` payload** (`:651`) | **Resolved outside this card**: `DECODE_DEPTH2.md` §2 — wrapper + Havok packfile at 0x44, 7 typed objects, 512-byte trailing blob still UNKNOWN. |
| **`.ddsc` texel payload** (`:650`) | **Partly resolved**: `DECODE_DEPTH2.md` §1 — block sizes derived per format and mip chains tiled (71 files FULL); what remains is the meaning of the header tail `0x2C..0x80` (45 files) and the `u32` at 0x28. |
| **`.epe` round trip "first diff at 0x765"** | Verifiable without decoding anything: rerun `Gibbed.JustCause3.ConvertProperty.exe --e` then `--i` on the extracted `.epe` (the tool already does this; `Tools/Gibbed` is present). The diff offset is a derived fact I did not re-derive — cheap to confirm or refute. |
| **the 41 of 6382 compound AABBs not explained by the children** | Not resolvable here: it needs the compound's own header beyond the instance slot (`hknpStaticCompoundShape` is graded PARTIAL for that reason). Correctly left open; belongs to G3-01b/G3-10b territory. |
| **`hknpShapeMassProperties`** (56 objects, NAMED-ONLY) | Not resolvable from the bytes without a layout hypothesis; the card names the right oracle (symmetric positive-definite 4×4 inertia, mass summing to the body entry). Correctly open (G3-10b). |
| **constraint classes** (9 hinge + 2 ragdoll, NAMED-ONLY) | Correctly open: typed but no per-field layout, which is G3-10b's card. |

## 5. What holds up

- **The census is exact and reproducible**: 566 entries, the 14-extension histogram, and
  79,922,183 B total all match my independent walk of the `.ee`; `--check` regenerates the md and
  json byte-identically (14/14).
- **The `.physicsc` class table is the live one.** My `jc3hkx` read reproduces all 16 classes and
  all 16 counts, including the numbers the card leans on (54 hulls, 18+18 extern meshes, 9+2
  constraints, 56 mass properties).
- **The grading is conservative, which is the point of the card.** The `.rbm` PARTIAL 3 is real (I
  reproduced the exact `GeneralMkIII` refusal); `.ddsc` was graded PARTIAL although its container
  closes on all 116; `hknpExternMeshShape` is PARTIAL with the un-pinned de-quantization frame
  named rather than a position invented; mass properties and constraints are NAMED-ONLY. Nothing I
  checked was graded FULL on a name.
- **The oracles are named per extension and are falsifiable** (re-encode equality, `total == len`
  plus allocation tiling, mip-chain accounting, typed fixups) — not "looks right".
- **`.lod` is exactly as described**: 59 files, 16 with a `-` slot, all 59 re-joining to the bytes.

Scope of this review: read-only. I ran `--check`, read the bundle myself, decoded six payload
families, and cross-read `DECODE_DEPTH2.md` for staleness. I did not re-derive the fleet-wide hull
oracle, the `.epe` diff, or the compound-AABB count, and I touched no file except this report.
