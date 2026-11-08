# Review — G3-09 (JC3 paint and colour pipeline, desk part)

Reviewer: independent (did not write the card). Inputs read: `Research/JC3Grab/COLOUR.md`,
`Research/JC3Grab/COLOUR.json`, `Tools/scripts/jc3_colour.py`, `tmp/freebuff/reports/G3-09.md`,
card `GRAB_BACKLOG.md` §6b `G3-09`, `RESET_FINDINGS.md`.
Nothing outside `tmp/freebuff/reports/` was written; no game was launched; no git command run.

## VERDICT: needs rework

The file-side decoding is sound and reproduces: the CarPaintMM payload layout, the 288/28/76
sizes, the nine blocks, the paint zones (6, 7, 8), the 1,897 B palette, all ten tint records, the
77 exported float offsets, the `exposure`/`tonemap` counts and the byte-identical round trip all
re-read correctly from the raw bytes.

What fails is one conclusion that the card states as **measured** and that its `--check` certifies:
§4 "No `.rbm`, `.epe` or `.vmodc` of the entity names the palette, so the binding is engine-side
(spawn/vehicle-system), not an asset reference", repeated in UNKNOWN 2 ("The palette -> block
binding is not in any of the 566 files"). **That is false.** The entity's own
`v0300_car_kensington_sportsmuscle_civilian_01.epe` carries the Jenkins hash of `palette`
(`0x6187A56B`, at `0x266`) immediately followed by the Jenkins hash of the palette module's VFS
path (`0xC023BA54`, at `0x26a`) — a name/value pair, in a node context that repeats the same
`(header, hash, hash)` shape at `0x240`–`0x290`. The palette *is* an asset reference of the entity;
it is simply hashed, so the card's ASCII scan (its check 9) cannot see it. Four oracles below.

Two secondary count errors and one false universal (§5 time-of-day) follow from the same habit:
trusting a substring scan as if it were a name lookup.

## Check output (verbatim)

Command: `uv run --with numpy python Tools/scripts/jc3_colour.py --check` (exit 0)

```
ok   the palette decodes as ADF v4 with the types MODLOG §55 names (A[Tint], ColorRGBA, HashString, Palette, Tint) and its header total equals its length (1897)
ok   the palette holds exactly 10 tint records, the names MODLOG §55 lists
ok   tint_r, tint_g and tint_b carry the same RGB in every record (10/10) - the measured reason the palette is one colour per tint, not three
ok   every tint float is inside [0, 1] except the A lanes, and all occurrence values are 100
ok   the body's 9 CarPaintMM blocks re-encode byte for byte (the block layout oracle)
ok   the three payload sizes are the reflection header's structures exactly (static 288 B / support 28 B / dynamic 76 B)
ok   the paint zones are exactly the blocks carrying the body's own _body_dif/_body_msk textures (6, 7, 8) and every one of them has the dirt/damage/soft-tint flag bits set
ok   the s0-s3 slots on a paint block are dif / nrm / mpm / msk in that order (the reflection header's Diffuse / Normal / PropertyMap / TintMap), so the sampler order is corroborated by the texture suffixes, not assumed
ok   no file in the bundle references the palette except the palette itself: 1 reference(s), measured over all 566 inner files
ok   the exposure/tonemap search is a measurement over the whole index (78907 rows), and it finds no tonemap/post-process/light-profile/time-of-day file
ok   the palette floats' file offsets are decoded, not assumed (ConvertAdf `offset-in-file` on the same bytes): 77 offsets = 7 (R/G/B/A + gloss / metallic / coat) x 11 records
ok   no on-screen calibration is claimed: the JSON's measured set is exactly the file-side numbers (tints, blocks, round trip, paint zones, three sizes) and carries no screen colour or error term
ok   E:\Modding\JC3-Batmobile\Research\JC3Grab\COLOUR.md is byte-identical to a fresh decode
ok   E:\Modding\JC3-Batmobile\Research\JC3Grab\COLOUR.json is byte-identical to a fresh decode

OK: 12/12 checks, md identical, json identical
CHECK_RC=0
```

(The console renderer prints `MODLOG ?55` for `§55` — a cp1252 console artefact, not a file defect.
`COLOUR.md` sha256 `131fff7f…e672`, `COLOUR.json` `59a14471…1395`, both mtime Nov 3 02:16, so the
artefact is not stale; the check is reproducible today.)

Note that check 9 ("no file … references the palette except the palette itself") and check 10
("finds no … time-of-day file") are two of the three failing statements below — the `--check` does
not merely miss the errors, it asserts them.

## Spot-checks (5 re-read from the raw bytes)

Read with `bm_rc.vfs`/`eetoc` (bundle extraction) and `struct` only; the card's script was used
solely for the bundle path constants, never for the value being checked.

| # | value as published | source I re-read | raw result | match |
|---|---|---|---|---|
| 1 | palette `.vmodc` = **1,897 B**, ADF v4, header total = length | `v0300_car_kensington_sportsmuscle_palette.vmodc`, bytes 0..64 unpacked as `<16I` | `len = 1897`; header u32[10] = `0x769` = 1897, the only header field equal to the length; magic `0x41444620` (' FDA'), version `4`, 1 instance, 5 types, 21 names | **yes** |
| 2 | tint 0 **White** `(0.88, 0.88, 0.88)`, gloss `0.000`, metallic `0.000`, coat `1.000` | same file at `tints[0].R/G/B` = `0x94/0x98/0x9c` (`<f` each), gloss `0xa4`, metallic `0xa8`, coat `0xac` | `0.878906?`→`0.88` exactly (0x3F6147AE region), `0.88, 0.88`, gloss `0.0`, metallic `0.0`, coat `1.0` | **yes** |
| 3 | tint 2 **Garnet Red Metallic** `(0.4265, 0.05, 0.05)`, gloss `0.450`, metallic `1.000`, coat `1.000` | `0x134/0x138/0x13c`, `0x144/0x148/0x14c` | `0.426471, 0.05, 0.05`; `0.45, 1.0, 1.0` | **yes** |
| 4 | block 6: flags `0x101F`, static `288` B / support `28` B / dynamic `76` B, first dynamic float4 `(0.14, 0.19, 0.25, 1.0)`; body has 9 blocks, re-encode byte-identical | `sportsmuscle_body_lod1.rbm` (403,514 B) via `rbm_geom.decode`; the dynamic payload re-read at its own file offset `0x3efb7` | flags `0x101F` (blocks 6, 7, 8; blocks 3–5 `0x1000`, 0–2 `0x1004`), `st=288 sup=28 dyn=76`, raw float4 `0.14, 0.19, 0.25, 1`; `m.write() == blob` → `True`; blocks 6/7/8 carry `_body_dif/_body_nrm/_body_mpm/_body_msk` | **yes** |
| 5 | index `78,907` rows; `exposure` 1 hit = `textures/color_curves/color_correction_neutral_exposure.ddsc`; `tonemap` 0 | `jc3strings.load_index()` recount + the ASCII byte scan over the 566 inner files | `78907`; `['textures/color_curves/color_correction_neutral_exposure.ddsc']`; `0`; ASCII `palette` occurs in exactly 1 inner file (the palette itself) | **yes** |

Extra re-reads, unasked: all **77** exported offsets unpack to the published floats (e.g.
`tints[4].R` `0x1d4` = `0.410667`, `tints[7].R` `0x2c4` = `0.432`, `tints[8].R` `0x314` =
`0.538667`); `R == G == B` in 10/10 records straight from the bytes; metallic `1.0` in exactly 8
records; every `A` lane `1.0`.

## Issues (file, value, why)

### 1. `COLOUR.md` §4 + UNKNOWN 2 (+ check 9): the palette binding is *not* absent — it is hashed

* Published: *"No `.rbm`, `.epe` or `.vmodc` of the entity names the palette, so the binding is
  engine-side (spawn/vehicle-system), not an asset reference."* And UNKNOWN 2: *"The palette ->
  block binding is not in any of the 566 files (§4)."*
* Measured (mine): `v0300_car_kensington_sportsmuscle_civilian_01.epe`, 109,526 B —
  `Jenkins("palette") = 0x6187A56B` at `0x266`, and `Jenkins(full palette vmodc path) = 0xC023BA54`
  at `0x26a`. Window `0x258..0x280`:
  `…601c 0800 000e 6ba58761 54ba23c0 01fcd1fb 61200800 …` — the name hash is immediately followed
  by the value hash, in the same `…0e <hash> <hash>…` shape that recurs at `0x240`/`0x25c`/`0x270`.
* Oracles: (a) base rate — 400 random 4–40 char strings, **0** of their 32-bit hashes occur in the
  epe (expected ≈ 0.01); (b) negative controls — hashes of the sibling module paths `_body.vmodc`,
  `_wheels.vmodc`, `_interior.vmodc` occur **0** times; (c) containment — the palette path hash
  occurs in exactly **1** of the 566 inner files, and that file is the `.epe`; (d) the ASCII scan
  reproduces (1 file) and is *blind by construction*: JC3 assets address by Jenkins hash, so a raw
  byte scan for the ASCII string cannot find a reference.
* Why it matters: this is the difference between "the engine picks a tint out of thin air" and
  "the entity declares which palette module it uses; the engine then selects an entry inside it".
  The second is decidable from the bytes and is what §4 and UNKNOWN 2 deny. The §4 downstream
  sentence ("DERIVED … the palette is what the engine writes into that dynamic slot") survives
  only as a hypothesis; the premise it rested on is refuted.
* Fix: replace the ASCII reference test with a hashed-name test (hash `palette` and the module path,
  search the 4-byte LE pattern), state the `.epe` pair as decoded with the oracle above, and move
  the "engine-side" claim to a labelled hypothesis about *tint selection* only.

### 2. `COLOUR.md` §5 prose + check 10: "no file is named for … a time of day" contradicts its own table

* Published: *"no file in JC3's index is named for a tonemap, a post-process chain, a light profile
  or a time of day"*; check 10: *"finds no tonemap/post-process/light-profile/time-of-day file"*.
* Measured: the card's own §5 table row and my recount both give `time_of_day` = **2** —
  `graphs/mission/modules/msub_time_of_day.gdc` and `…gsc`. So the universal is false, and the
  check line that certifies it is false; the md and the check disagree with the md's own table.
* The table itself is right; only the sentence and the check text overreach. A weaker, true
  statement is available: no *texture/config/light-profile* asset, two mission graphs.
* Related, unlabelled: `sky` 3364 and `sun` 31 are counted by substring and their own examples are
  false positives (`…_skyshield_…`, `…_boatsunk_…`), so those two rows measure nothing about
  lighting. The table says "substring" once, but the rows are read as evidence of absence.

### 3. `COLOUR.md` §4: "the five 'metallic' tints"

* Published: *"the five 'metallic' tints all carry gloss 0.45 / metallic 1.0 / coat 1.0, and the
  matte ones (White, Black) …"*.
* Measured: **eight** records carry `metallic = 1.0` (indices 1, 2, 4, 5, 6, 7, 8, 9); only White
  and Black are matte. The card's own table is correct, so this is a prose miscount (the card's
  summary note even says "eight"), but it is stated as a decoded fact.

### 4. `COLOUR.md` §4 + check 11: "77 floats … for the 10 tints plus the palette root's own default record"

* Published: *"77 floats in all - 7 per record … for the 10 tints plus the palette root's own
  default record (`palette.*`)"*, and check 11 *"77 offsets = 7 … x 11 records"*.
* Measured: the seven `palette.*` offsets are byte-identical to the seven `tints[9].*` offsets —
  `R 0x364, G 0x368, B 0x36c, A 0x370, gloss 0x374, metallic 0x378, coat 0x37c`; the values agree
  too (0.2, 0.424, 0.2 / 0.45, 1.0, 1.0 = the "Green" row). The ADF header declares **one**
  instance, and the tint array runs `0x94 + 0x50·k`, so `tints[9]` *is* `0x364`. There is no 11th
  distinct record: the file has 70 distinct published floats, the export lists 77 because the root
  walk re-emits the last element. The arithmetic is right; the record count and the phrase "the
  palette root's own default record" imply a distinct 11th record that does not exist.
* Minor, same sentence: `0.4265`, `0.4107`, `0.5387`, `0.2187`, `0.3227`, `0.4587`, `0.0941`,
  `0.2294`, `0.1647`, `0.3893` are 4-dp renderings of `k/255` values (`0.426471`, `0.410667`,
  `0.538667`, …). Harmless for the palette (they round-trip to the `k/255` the file holds) but a
  reader cannot tell from the md that the underlying bytes are 8-bit quantised, which matters for
  G3-04's "exact conversion" question.

### 5. Unlabelled inference in §5's conclusion

* Published: *"Exposure and tonemapping are therefore UNKNOWN as data: they are either engine
  constants or live in the executable, and neither was read."*
* The evidence is a filename substring search only. A second possibility — the values live in an
  asset whose *name* does not contain any of the twelve terms (the index is full of `.gdc`/`.blc`
  graphs and `.rbm` blocks that do carry lighting data) — is neither excluded nor labelled as an
  assumption. The card has already found one such file (`msub_time_of_day.gdc`) and discarded it
  while asserting no time-of-day file exists.
* Fix: label the sentence "DERIVED from a filename search; asset-side lighting data whose name
  avoids these terms is not excluded", or replace it with the per-term measurement.

### 6. Editorial

* §7 item 2 has a stray fragment: *"(`White, Evergreen Pearl, Garnet Red Metallic`, White / Black /
  Garnet Red Metallic are the most separable)"* — five names, one backticked triple, and a
  "most separable" ranking with no criterion.
* Check 4's *"every tint float is inside [0, 1] except the A lanes"* — the A lanes are `1.0`, which
  is inside `[0,1]`; the carve-out is meaningless (no defect, but it reads as if an out-of-range
  value was found).
* `occurrence = 100` was not independently re-read by me (the export carries no offset for it), so
  I neither confirm nor contest it.

## Resolvable UNKNOWNs (and how)

1. **UNKNOWN 2, "the palette → block binding is not in any of the 566 files" — resolved, and it is
   false.** Method: Jenkins-hash every module path and the bare property names, search the 4-byte
   LE pattern in every inner file, with a random-string base rate and sibling-path negative
   controls. The `.epe` carries `("palette", <palette path hash>)` at `0x266`. Cost: one script
   run. What remains genuinely UNKNOWN is narrower and should be restated: *which* tint the engine
   selects and whether it writes the palette's rgb/gloss/metallic/coat into the dynamic slot —
   the `.epe` link does not say, and the block's override triple on the paint zones
   (`0.4, 1.0, 1.0`) is *not* the palette's (`0.45, 1.0, 1.0`), so no write-back can be inferred.
2. **UNKNOWN 4, "exposure … engine-side" — partly resolvable without a game.** `time_of_day`'s two
   graphs decode with the project's existing `.gdc` reader if one exists (the project reads graphs
   elsewhere; check before claiming), and tonemap constants, if they are in the executable, are
   readable with `pefile` (already a task dependency). Neither was attempted; say which was tried.
3. **UNKNOWN 1, which dynamic float4 is `TintColorR/G/B` — narrowed, not resolved.** The header
   accounts for 3 vectors + 3 scalars = 60 B of 76, leaving exactly one 16 B float4 unnamed; on the
   paint blocks the four vectors are `(0.14,0.19,0.25,1)`, `(0,1,0,0)`, `(0,0,1,0)`, `(2,0,1,1)`.
   A file-side oracle is available and cheap: compare these four vectors across *all* paint-block
   bodies in the bundle — if two cars with different palette entries carry identical vectors, the
   vectors are not the tint carrier, which removes the "matrix" hypothesis the card calls
   plausible. Not done here; it belongs in the card.
4. **UNKNOWN 3 (`PropertyMap`/`TintMap` channels)** — genuinely deferred: the `.ddsc` payload has
   no project reader (G3-12). Correctly labelled.
5. **UNKNOWN 5 (on-screen transfer)** — genuinely needs pixels; correctly labelled, and the card
   correctly refuses to claim any. §7's requirement list is sound and should be kept.
