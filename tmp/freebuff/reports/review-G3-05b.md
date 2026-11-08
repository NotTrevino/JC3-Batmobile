# Independent review — G3-05b (BmAK skins: MK2, Jokerfied, Standard)

Reviewed 2026-11-03. I did not write this card. Everything below is my own read of the packages,
using `Tools/scripts/upk_read.py` for the container/table/tag format and raw `struct` reads at
payload offsets — **not** `grab_skins.py`'s helpers, so a bug in the card's decode could not
reproduce itself in the check.

Files reviewed: `tmp/freebuff/reports/G3-05b.md`;
`Tools/scripts/grab_skins.py` (1,296 lines); `Research/BatmobileGrab/SKINS.md` (1,507 lines,
140,824 B); `Research/BatmobileGrab/SKINS.json` (701,523 B). Card text read from
`GRAB_BACKLOG.md` §6b line 1044. Nothing was written except this file; `--write` was not run, so
no output was regenerated.

## VERDICT: **minor issues**

The card's numbers reproduce. Every value I re-read from the bytes matches, the `--check` gate is
real (it re-derives both outputs and compares them byte for byte), and the doc is unusually
disciplined about refusing to call the two `Batmobile_V2` meshes identical. No invented value, no
gap filled from Arkham Knight/UE3 knowledge that I could find.

What keeps it from `sound` is labelling, not decoding:

- one **false UNKNOWN** (U-5): the 662 residual bytes are decodable now, and I decode most of them
  in §5 below — they are package-local *name-table* indices, which the card's resolver never tried
  (it only resolves *export/object* indices);
- one **self-contradiction**: §3 of the report states the Standard skin differs by "nothing beyond
  package-local index numbering", while §4.5 says those same bytes are UNKNOWN and must not be
  summarised as identical;
- one **category bug** that mislabels what 130 of the differing bytes are (they are the 65 socket
  object references, not socket payload values);
- one over-strong heading (§8 "what carries the mesh in the level") and a few nits.

All of these are fixable by editing the decoder's labelling and the U-5 entry; no part of the
decode needs to be redone.

## 1. Check output (my run, verbatim)

```
$ uv run --with numpy --with pillow --with pefile --with capstone python Tools/scripts/grab_skins.py --check
OK 4 packages, 248 sockets, 84 slots, 79 material chains, 7 unknowns; md+json byte-identical to a fresh rebuild
  oracle playable: umodel Materials[19] == decoded order -> True
EXIT=0
```

Exit status 0. I did not re-run the report's tamper tests (Command 3): they were run before this
review and the outputs are since restored, so I can only confirm that the failure messages they
quote are the strings `main()` actually produces (`SKINS.md is stale (inputs changed since
--write)` / `SKINS.json is stale (inputs changed since --write)`) — both exist in the code at
`grab_skins.py:1246-1250`, so the quoted behaviour is plausible but was not re-observed.

## 2. Spot-checks — five values labelled decoded, re-read from the raw source

| # | value in the record | my independent read | source | match |
|---|---|---|---|---|
| 1 | `mk2` mesh `Batmobile_MK2_Skin`, export 98, payload **20,034,142 B**, sha1 `c249bd59c7125fc6` (SKINS.md §2, report §2 D1) | class `SkeletalMesh`, name `Batmobile_MK2_Skin`, export 98, `pkg.data(98)` length 20,034,142, sha1 `c249bd59c7125fc6…` (the only `SkeletalMesh` export with that name in the package) | `Showcase_Batmobiles_MK2.upk`, export 98 | **yes** |
| 2 | socket `Afterburner`: bone `JetSMove`, relative location **[-205.1, 0.9707, -0.4999]**, relative rotation **[32768, -32768, 0]** (SKINS.md §5) | `SkeletalMeshSocket` export 5300, 58 B: `name@0x54`→`Afterburner`, `name@0x5c`→`JetSMove`, `vector@0x64`→(-205.05699, 0.970673, -0.49994075), `rotator@0x70`→(32768, -32768, 0) | `Playable_Batmobile_SF.upk`, export 5300 | **yes** |
| 3 | `mk2` slot array: **count 19 at payload byte 8341**, refs from 8345, slot 2 = `Batmobile_MK2_Body_MIC` (SKINS.md §3) | `int32@8341` = 19; 19 refs from 8345; ref[2] = 240 → `Batmobile_MK2_Body_MIC`, class `MaterialInstanceConstant`; my own uniqueness scan over all byte positions 0..0x8000 finds exactly **one** candidate, `(8341, 19, 0 empty)` | `Showcase_Batmobiles_MK2.upk`, mesh export 98 | **yes** |
| 4 | Jokerfied `Batmobile_Jokerfied_V3_Physics`: **10 `BodySetup`**, body 617 bone `Batmobile_Chassis`, AggGeom **1,771 B**, header words **[0, 2, 10, 1397]** (SKINS.md §7, report §2 D4) | export 550 (`PhysicsAsset`, 510 B): `BodySetup` count 10, 10 refs; export 617 = 2,710 B, `AggGeom` 1,771 B, first four u32 = [0, 2, 10, 1397]; its only `NameProperty` = `Batmobile_Chassis` | `Showcase_Batmobiles_Jokerfied.upk` | **yes** |
| 5 | Standard vs Playable `Batmobile_V2`: **1,345 differing bytes** of 20,151,210, categories outside_decoded_spans 662 / slot_ref 32 / tag_header 10 / ClothingTeleportRefBones 2 / LODInfo 508 / SkelControls 1 / Sockets 130; 19 ref fields all same name | my own byte diff: 1,345 differing bytes; with the card's slot spans added to the tag spans I get the identical category counts and 662 outside bytes in 363 clusters (my raw span set alone gives 694 outside = those 662 + the 32 slot_ref bytes); size equal, tag layouts identical | `Playable_Batmobile_SF` export 5284 vs `Showcase_Batmobiles_Standard` export 98 | **yes** |

Extra reads done while checking (not counted above), all matching:

- package sizes / export counts: 17,916,421 / 5,490 · 9,730,550 / 1,055 · 9,799,400 / 945 ·
  8,967,713 / 1,136 (SKINS.md §1).
- socket census 65 / 65 / 55 / 63, shapes 39×58 B + 25×42 B + 1×26 B (playable, standard),
  no-rotation 26 / 26 / 25 / 26, no-location 1 each.
- slot-array uniqueness in all four packages: playable 8287 (19), standard 8287 (19), mk2 8341
  (19), jokerfied 9917 (27, five null refs) — one candidate each.
- Jokerfied slot list identical to SKINS.md §3, including `Batmobile_Jokerfied_Teeth` at slots 19
  and 20 (both export 542) and slots 22–26 empty.
- Jokerfied flower bodies 618/619 are 51 B with exactly three tags
  (`PreCachedPhysDataVersion`, bone name, one `ObjectNCRProperty`), as report §2 D4 states.
- `PhysicsAsset` census: playable 1 (32 bodies), standard 0, mk2 0, jokerfied 1 (10 bodies).
- Standard sockets vs Playable: same 65 names, **0** bone diffs, **0** location diffs, **0**
  rotation diffs (this confirms report §2 D5's claim, which its own quoted output does not show —
  see I-4).
- `Working/Appearance/grab/Playable_Batmobile_SF/SkeletalMesh3/Batmobile_V2.props.txt` has
  `Materials[19]` in the same order the decoder produces, so the card's independent oracle is a
  real second read, not a restatement.

## 3. Issues

### I-1 · significant — U-5 is a false UNKNOWN, and it is resolvable from the bytes (see §5)

The card reports "662 bytes that differ after the tag stream … the rest are in the bulk data,
where no field is decoded". `classify_diff` resolves leftover words only with
`pkg.object_name(...)` — the **export/object** table — so a name-table index can never match, and
every cluster stays UNKNOWN. Resolving the same 4-byte words against `pkg.names` instead gives
**360 of 363** clusters resolving to the *same string* in both packages: `Batmobile_Chassis`,
`Batmobile_Chassis_Mesh`, `SUSP1_Wheel_Front_Left`, `SUSP2_Wheel_Front_Left`, `Wheel_Parent_F_L`,
`Wheel_Front_Left_Vis`, … The first 180 clusters sit at a constant 44-byte stride
(payload bytes 8423…16299), each record's first u32 is a name index, and the 180 names are unique
— i.e. a 180-record table keyed by bone name, which matches `MESHES.md`'s independent umodel bone
count of **180** for `Batmobile_V2`. The remaining bulk-data clusters follow the same pattern.

Consequence: the "662 bytes are unknown" statement, and the refusal in U-5 to conclude anything,
are both wrong in kind — the difference is package-local **name** numbering, not undecoded
geometry. This also means the report's §3 table claim is *correct*, but the card never proved it
(and contradicted it — I-2). Fix: try `pkg.names` as well as `pkg.object_name`, and keep only what
still fails as UNKNOWN. Three clusters still fail (see §5).

### I-2 · moderate — the report states two opposite conclusions about the same bytes

Report §3, Standard row: "distinguishable from the drivable `Batmobile_V2` by … **nothing beyond
package-local index numbering in the 1,345 differing bytes**". Report §4.5: those bytes are
UNKNOWN and "Deliberately **not** summarised as 'geometry is identical'." Both cannot stand. As
shipped, §3 is an unlabelled conclusion the implementation explicitly refuses to make; after I-1
it *can* be made, but then it must carry the evidence (name-index oracle, 180-record bone table,
the 3 residual clusters) and §4.5 must shrink to that residual.

### I-3 · moderate — span shadowing: 130 bytes are mislabelled, and reference bytes are never counted as references

`_field_spans` emits both `tag_payload:<name>` (covering `at … at+size`) and `ref:<name>`
(covering `at+4+4k …`) for the same tag, then sorts by start. `_category` returns the **first**
span containing the offset, so the enclosing payload span always wins and the `ref:` categories
are unreachable code. Two consequences in the published record:

- SKINS.md §9 lists `tag_payload:Sockets 130`, which reads as socket *values* differing. Measured:
  the `Sockets` tag payload is 264 B and all 130 differing bytes fall in the 65 reference fields
  (`(offset − at) mod 4` = 0 for 65 bytes and 1 for 65 bytes) — they are the low two bytes of each
  socket's object index, i.e. package-local index numbering, exactly as expected from 5,490 vs
  1,055 exports. The number is right; the stated kind is wrong.
- "object-reference fields touched: 19" therefore counts only the slot array. The 65 socket
  references — which *do* differ — are never counted as references anywhere, which makes §3's
  "nothing beyond package-local index numbering" look less supported than it is.

Fix: make `_category` prefer the narrowest span (or subtract ref spans from the payload span),
then report socket refs as refs with a same-name/different-index count.

### I-4 · minor — a true claim whose evidence is not printed

Report §2 D5 states "all 65 sockets have the same names, bones, locations and rotations". I
verified it independently (0/0/0 diffs), and the JSON does hold
`location_differences: []` and `rotation_differences: []`. But the quoted Command 4 output prints
only `same-set` and `bone-diffs` for Standard, so the claim cannot be checked from the report. The
mk2/jokerfied blocks do print those lists, which makes the omission look intentional. Print the
two lists for every skin.

### I-5 · minor — "the 10 `RB_BodyInstance` objects … are counted" is not true of the outputs

Report §4 (last paragraph): "what `PhysicsAssetInstance`'s 10 `RB_BodyInstance` objects (2–10
bytes each) hold — they are counted, not decoded". Measured: the *package* has exactly 10 exports
of class `RB_BodyInstance` (one 2-byte, nine 10-byte), but `SKINS.md` §7 records the
`PhysicsAssetInstance` (export 551, 70 B) as having "no body-instance array", and
`SKINS.json` → `physics_instances[0].body_instance_arrays` is `[]`. So the 10 objects appear
nowhere in the outputs; they are counted only in the report's prose, and the "2–10 bytes each"
range should be the exact sizes. Also unmentioned: the playable package has 32 such exports.

### I-6 · minor — §8's heading is a claim about the game world that the bytes do not support

"What carries the mesh in the level" lists package-local components (`SkeletalMeshComponent0`,
`BatmobileOnFireMeshComp0`, `SVehicleMesh`, 10× `GadgetMesh`, plus one `RSkeletalMeshActor` per
showcase package). These are exports inside the package, not level actors, and nothing in the
bytes says which one a level instantiates. Rename to "components in the package" (the decoded
content is fine — e.g. `SVehicleMesh` → `Batmobile_V2_Mesh.Batmobile_V2` #5284).

### I-7 · minor — AggGeom word 2 is labelled `sphyl`, but the project's decoder calls it UNKNOWN

`grab_skins.py`'s box label says "COLLISION_GEOM.md labels word 0 spheres, word 1 boxes, word 2
sphyl, word 3 convex count when it is small". The decoder it imports says the opposite about
word 2: `grab_collision_geom.py:199-200` sets
`"sphyl_label": "UNKNOWN: word 2 = 10 on all box bodies (meaning not decoded)"`, and
`COLLISION_GEOM.md` commits only to word 0 = sphere count and word 3 = convex count when small.
So the Jokerfied chassis `[0, 2, 10, 1397]` is quoted with a stronger label than the project's own
decode supports (and word 2 = 10 happening to equal the body count is unproven coincidence).
Related: "word 3 = 1397 is larger than any convex count this project's decoder accepts" is true
only in the sense that `grab_skins.py` gates convex decoding on `< 256`; nothing shows 1397 is not
a count. Keep the refusal to decode it, but describe the gate, not a fact about 1397.

### I-8 · nit — "LODInfo decodes identically" vs 508 differing bytes inside the LODInfo payload

SKINS.md §6 does show the decoded LOD fields are equal for standard/playable (same
DisplayFactor/LODHysteresis/counts), so the *counts* are identical; the 508 differing bytes are
inside the `LODMaterialMap` / `bEnableShadowCasting` / `TriangleSortSettings` arrays, whose
contents are never printed. Say "the decoded LOD counts are equal; 508 bytes inside those arrays
differ (values not decoded)" so the sentence and §9's category table agree.

### I-9 · nit — mesh payload sizes exceed the package file size with no explanation

SKINS.md §2 gives `Batmobile_V2` a 20,151,210-byte payload while §1 gives its package as
17,916,421 bytes. Correct, but only because `upk_read.Package.data()` returns *decompressed*
payload from the chunked container (that package's logical image is 34,582,268 B). The doc never
says so, so every size in §2 looks like an arithmetic error on first read. One sentence in §1/§2.

### I-10 · nit — "Output, verbatim" is elided

Report §1 Command 4 shows a `python - <<'PY'` block containing `...   # prints D1..D6` and then
quotes "verbatim" output. The code shown cannot produce that output. The numbers themselves
reproduce (I re-derived D1/D2/D5/D6 independently), but the block should not be labelled verbatim.

### Unlabelled claims (item 3 of the brief), in one list

- §3 table's "nothing beyond package-local index numbering" — conclusion without the evidence,
  and contradicted by U-5 (I-2).
- §8 heading (I-6).
- "the showcase packages reuse the same MICs and masters — the skin difference is carried by
  *which* material each slot points at": supported by the 0-difference shared-step comparison, but
  the counts 29 / 26 / 21 are shared *chain objects* (MICs and Materials), described as "steps" in
  §3 and "materials compared" in the output — pick one word.
- `sphyl` label for AggGeom word 2 (I-7).
- "1397 is larger than any convex count this project's decoder accepts" (I-7).
- "the 10 `RB_BodyInstance` objects … are counted" (I-5).
- Report §2 D2's "decoded: … the same shape as `MATERIALS.md`" is a comparison, not a label; the
  underlying slot/parameter values I sampled (COLOUR.md's `Material0_BaseColour`
  [0.02579, 0.02579, 0.03, 1] and `Diffuse_Adjust` [2.2, 2, 2, 1] via
  `Batmobile_V3_WheelArchs_NEW_MIC`) are consistent with the existing `COLOUR.md` record.

## 4. Decoded labels I could not fault

For balance, the labels that held up under re-read: mesh export identity and sha1 (§2); the socket
tag layout and its three shapes, including the `0x54 / 0x5c / 0x64 / 0x70` class offsets (§5);
the slot array's count+refs form and the uniqueness oracle (§3); the `LODInfo` frame (§6); the
PhysicsAsset body census and the 206-byte/51-byte body shapes (§7); the object-reference chains
(§4, spot-sampled); and the "not comparable (different sizes)" refusal for mk2/jokerfied mesh
diffs, which is the right answer rather than a fabricated count.

## 5. UNKNOWNs I could resolve from the bytes

**U-5 — resolved, mostly.** Method: take the 662 differing bytes outside the decoded spans, group
them into 363 clusters (gap ≤ 8), and for each cluster try the 4-byte word at the cluster start
(and 1–3 bytes back) as an index into **both** packages' *name* tables, accepting only an exact
string match. Result:

- **360 / 363 clusters resolve to the same string** in `Playable_Batmobile_SF` (3,151 names) and
  `Showcase_Batmobiles_Standard` (1,528 names). Examples: 8423 → 200/98 = `Batmobile_Chassis`;
  8467 → 202/100 = `Batmobile_Chassis_Mesh`; 8511 → 2734/1373 = `SUSP1_Wheel_Front_Left`.
- The first **180** clusters form a strict 44-byte-stride table (payload bytes 8423, 8467, …,
  16299); the first u32 of every record is a valid name index and all 180 names are distinct —
  a bone-name table. Independent corroboration: `MESHES.md` (umodel, a different reader) counts
  **180 bones** for `Batmobile_V2`.
- **3 clusters remain UNKNOWN** — payload bytes 3,616,647–3,616,649; 14,470,952–14,470,955;
  19,100,809–19,100,811 — where the differing word is not a name index in either package
  (values e.g. 13,153,998 vs 4,984,387). These are the honest residue of U-5 and are what the
  doc should keep as UNKNOWN, together with the fact that the 508 LODInfo-payload bytes and 130
  socket-index bytes are "position decoded, value not decoded".
- Caveat I am not glossing over: resolving a word to the *same name string* proves the two
  readings are the same name, not that the field is a name index. The 44-byte record structure
  and the 180-name/180-bone correspondence make that near-certain here, but the record's field
  layout is still not decoded — so the honest label is "decoded as name-table indices (same string
  both sides), record layout UNKNOWN", not "FMeshBone" or any other struct name.

**U-1 / U-2 (Standard and MK2 collision asset) — narrowed, not closed.** The card's evidence is an
export census by class. I re-tested harder: walking every export in both packages and looking for
any tag whose `ref_class` is `PhysicsAsset` or whose name is `PhysicsAsset` returns **nothing**. The
`SkeletalMeshComponent` (export 97 in both) parses to `end` with no such reference. What remains
open, and should be said: the packages' `RSkeletalMeshActor` exports (293 B / 289 B) do **not**
parse (`stop = unknown_type_-7679 / -6655`), so a reference in their unparsed tail is not excluded
— that needs the native `RSkeletalMeshActor` layout (G3-06), not more censusing. So U-1/U-2 are
"not in these bytes" for the mesh and component, and "UNKNOWN: unparsed actor tail" for the rest.

**U-3 (slot names)** — confirmed correctly closed: the element is 4 bytes; the only name-like
thing in the mesh payload near a slot is the object reference itself. No resolution possible, and
none needed.

**U-4 (mesh geometry behind the 20 MB)** — partly resolvable now that U-5 is understood: the
Standard/Playable meshes are byte-identical except for name/index numbering, so their geometry
*is* the same as far as any byte goes. It stays UNKNOWN for the mk2/jokerfied meshes (different
sizes), and for actual vertex/bounds numbers, which need the bulk-data layout or the umodel read.

**U-6 / U-7** — remain out of scope of these bytes, as stated.

## 6. What a corrected card needs (no rebuild required)

1. `classify_diff`: resolve leftover words against `pkg.names` as well as `pkg.object_name`;
   report the three residual clusters, the 508 LODInfo-payload bytes and the 130 socket-index
   bytes as the real UNKNOWN.
2. `_field_spans` / `_category`: innermost-span lookup, so socket references are counted as
   references (they differ by index only) instead of as socket payload bytes.
3. Print the location/rotation difference lists for every skin.
4. Rewrite §3's Standard row with the name-index evidence (or drop the conclusion), and make U-5
   agree with it.
5. Fix the `sphyl` label (inherit the decoder's UNKNOWN), the `RB_BodyInstance` sentence, the §8
   heading, the "LODInfo decodes identically" sentence, and add the decompressed-size note.

None of this changes a decoded number; it changes what the card claims those numbers mean. The
card's status (`done`) is defensible on the decode, but U-5's "the rest are in the bulk data"
should not be carried into G3-06 or the ledger as a real gap.
