# Independent review — B-03 · Emissive `CarLight` blocks and light parts

Reviewer: Freebuff (did not write this card). Date: 2026-10-29.

Scope: `GRAB_BACKLOG.md` §0.5 (R1–R14), the B-03 card (§8, lines 1017–1023), the §12 `B-03` row
(line 1335), `MODLOG.md` §"B-03 · Emissive `CarLight` blocks and light parts — done" (14178–14311)
and §"… — intended change" (13985–14041), and the outputs the row names:
`Working/Appearance/build_lights/` (24 RBMs + `lights_manifest.json`), `Tools/scripts/bm_lights.py`,
the `--lights` arm of `Tools/scripts/spec_check.py`, checked against `Research/BatmobileGrab/`
(`SLOTS.json`, `BONES.json`, `SOCKETS_JC3.json`, `LIGHTS.json`), `Working/Translation/t14_lights.json`,
`Working/Appearance/build_parts/parts_manifest.json` and the donor tree under `Builds/test-091/aaf/`.

Read-only: nothing under `GRAB_BACKLOG.md`, `MODLOG.md`, `Research/`, `Tools/`, `Working/`,
`Builds/` or the game install was written; no build, no install, no game launch. This report is the
only file written.

The card's §12 row names no separate `.md` deliverable (the doc is the MODLOG section), so the "doc"
in this review is that MODLOG section, read against the JSON and the script.

## VERDICT: **needs rework** (small and targeted)

Every number in the MODLOG reproduces from the files: the 4,576-face cut, 8 parts / 24 RBMs, the
288.6 KB / 4,899.6 KB budget, the 1,085 B header clone, the `[244, 108, 50]` ladder and all 24
read-back bboxes. The RBMs decode, the header is byte-identical to the clone, re-encode is
byte-identical, and the left/right naming is **correct** — I checked every lamp part's bbox against
the corresponding socket in `SOCKETS_JC3.json` and each one contains its socket (a check the card's
own tool does not perform). The Done command passes.

What is wrong is the part **contract**, not the numbers:

* the manifest has **no pivot and no frame**, so the four wheel-parented arch lamps are handed to
  B-04 in body-space coordinates while their parent's frame is the wheel pivot — the docstring even
  promises "part, parent, pivot, faces" (`bm_lights.py:26`) and the pivot is absent;
* two explicit Do steps (T-18 values in the block; the `CarLight` **+ `Window`** vanilla pattern)
  are not met, and §12 records the card as `done` without saying so;
* three MODLOG statements are contradicted by the data ("16 sockets … with their `LightColor`",
  "21 T-18 rows", "no light mesh has more [than 3 LODs]").

None of this requires rebuilding the RBMs; it requires the manifest to carry the part frame/pivot,
and three claims to be corrected (or the omissions flagged in the row).

## Check output (verbatim)

The command in the §12 row:

```
$ python Tools/scripts/spec_check.py --lights Working/Appearance/build_lights
CarLight: checked 24 blocks over 8 lamp parts; spec mismatches 0
exit=0
```

The card's script, full re-derivation (it prints one line per LOD from Blender before the verdict):

```
$ python Tools/scripts/bm_lights.py --check
  blender: DECIMATED 378 -> 378
  blender: DECIMATED 378 -> 324
  blender: DECIMATED 378 -> 150
  blender: DECIMATED 378 -> 378
  blender: DECIMATED 378 -> 324
  blender: DECIMATED 378 -> 150
  blender: DECIMATED 612 -> 612
  blender: DECIMATED 612 -> 323
  blender: DECIMATED 612 -> 150
  blender: DECIMATED 612 -> 612
  blender: DECIMATED 612 -> 323
  blender: DECIMATED 612 -> 150
  blender: DECIMATED 1146 -> 731
  blender: DECIMATED 1146 -> 324
  blender: DECIMATED 1146 -> 150
  blender: DECIMATED 1146 -> 732
  blender: DECIMATED 1146 -> 324
  blender: DECIMATED 1146 -> 150
  blender: DECIMATED 152 -> 152
  blender: DECIMATED 152 -> 106
  blender: DECIMATED 152 -> 50
  blender: DECIMATED 152 -> 152
  blender: DECIMATED 152 -> 106
  blender: DECIMATED 152 -> 50
PASS: 8 lamp parts / 24 RBMs, 4576 Emissive faces cut, 16 lamp sockets, 21 T-18 rows hosted, 3 rig lamps with no faces; model 288.6 KB lights, sum 5079.5 KB, net 4899.6 KB of 4915 KB
exit=0
```

The other two commands in the MODLOG's Done block (both re-run, both match the log):

```
$ python Tools/scripts/bm_lights.py --check --fast
PASS: 8 lamp parts / 24 RBMs, 4576 Emissive faces cut, 16 lamp sockets, 21 T-18 rows hosted, 3 rig lamps with no faces; model 288.6 KB lights, sum 5079.5 KB, net 4899.6 KB of 4915 KB (fast: files decoded, not re-decimated)
exit=0

$ python Tools/scripts/spec_check.py Working/Appearance/build_parts Builds/test-091/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_body_lod1.rbm
checked 295 blocks; spec mismatches 0; template values silently inherited 0
exit=0

$ python Tools/scripts/status_audit.py --check
STATUS.md is current
exit=0
```

Negative test (the `--lights` arm is not vacuous):

```
$ python Tools/scripts/spec_check.py --lights Working/Appearance/build_lights_nonexistent
FAIL: Working/Appearance/build_lights_nonexistent\lights_manifest.json missing
exit=1
```

## Issues

**1. [High] The manifest carries no pivot and no frame, so B-04 cannot place the four arch lamps —
and their geometry is in a different frame from every other part build.**
`lights_manifest.json` lamp keys are `part, kind, side, parent, bones, clusters, faces_lod0,
face_indices, lod_files, lod_budgets, faces_per_lod, vertices_per_lod, bytes_per_lod, bbox_m, block,
window_block, window_reason, sockets, t18_rows` — no pivot, no frame declaration. The module
docstring says the manifest holds "part, parent, **pivot**, faces, T-18 rows" (`bm_lights.py:26`).
B-02's manifest, the only other part build, carries `pivot_m` + `pivot_bone` for every entry, and
B-02's part RBMs are pivot-relative: `Working/Appearance/build_parts/wheel_f_l_lod1.rbm` spans
[-0.363,-0.678,-0.670]…[+0.690,+0.710,+0.670] while its pivot is [-1.208, 0.7047, -2.5699]; the body
RBM is absolute. B-03's light RBMs are **absolute body-space** (e.g. head lamp f_l
[-0.478, +0.503, -3.050]…[-0.356, +0.721, -2.965]), and four of the eight parts declare
`parent: 26/27/11/12` — the wheel parts (donor indices per `PARTS_TABLE.jsonl`), whose frame is the
wheel pivot. `bm_lights.py:129` applies `to_jc3_rot * scale + offset` and never subtracts a pivot, and
B-04's card says `parent_space_offset = pivot`. Adding the wheel pivot to the existing arch vertices
puts the f_l arch at roughly x −2.48, z −5.70 — off the car; using offset 0 instead puts it at the
right place but wrong in the parent frame (it would swing around the wheel pivot). The body-parented
head lamps and tail strips are fine only if B-04 happens to choose pivot 0 for them, which the
manifest also does not state. This is the one issue that blocks consumption: fix by recording
`pivot_m` (and the new parts' own `part_index`; T-18 gave the two front arch parts 42/43, the other
six have no index anywhere) and expressing each RBM's vertices relative to that pivot, as B-02 does.

**2. [Medium] "21 T-18 rows are hosted" is a count match, not a set match, and two of the 21 are
unmapped rows.** `MODLOG.md:14200` says "**21 T-18 rows** are hosted and **16 sockets** resolve
against `SOCKETS_JC3.json` with their `LightColor`." The manifest's 21 rows are
{T-L8, 9, 11, 12, 13, 14, 15, 16, 18, 19, 20, 22, 23, 25, 26, 27, 29, 31, 32, 33, 34}. T-18's own
part map (`t14_lights.json` `light_parts`) hosts exactly 21 rows too, but a different set:
body {T-L8, 9, 11, 12, 15, 16, 17, 18, 19, 24, 25, 26, 27, 29, 35} + arch {T-L13, 33, 34} +
{T-L14, 31, 32}. B-03 adds T-L20/22/23 and drops T-L17/24/35, so only 18 of the 21 coincide. Two of
the added rows are **unmapped**: T-L22 and T-L23 (`t14_lights.json`: `targets` empty; the manifest
records `"mapped": false` for both, and the MODLOG table at 14195 lists them as hosted anyway). The
same count on both sides hides three substitutions and two non-rows; a count that matches while the
set differs is exactly what R11's generated tables are meant to prevent.

**3. [Medium] No value from T-18 is in the block, although the card's Do says so.** Card
(`GRAB_BACKLOG.md:1019-1020`): "write the `CarLight` block with values from T-18." Every one of the
24 blocks is a byte-exact clone of `sportsmuscle_headlight_f_l_01_lod1.rbm`'s header, mid-static and
texture table (`bm_lights.py` `build_carlight`), so the emissive parameters are the donor head
lamp's, identical for the tail strips and wheel-arch lamps. The MODLOG discloses this as UNKNOWN #1
(14281-14284) — correctly, under R4 — but the Do step is not met and the §12 row (`done`) says
nothing about it. Either the row must carry the qualification, or the card's Do must be rewritten
after the block parameters are decoded.

**4. [Medium] No `Window` block, and the stated reason is not what the donor data shows.** Card Do:
"vanilla pattern: `CarLight` + `Window`, static". All 24 RBMs have a single `CarLight` block;
`window_block: None` and a per-lamp reason. The donor tree says the pattern is the opposite of the
blanket claim: of the 44 donor light meshes, **38 carry `CarLight` + `Window`**, and the only
`CarLight`-only family is `sportsmuscle_taillight_r_c` (all four LODs) plus the LOD4 of
`taillight_r_l/r`. So a `CarLight`-only **tail strip** has a vanilla precedent, but the two 3-lens
head-lamp parts mirror donor headlights that all ship the pair. The MODLOG's single reason ("the BmAK
lamp is one emissive surface with no separate lens shell", 14220) covers all eight parts and is
weaker for the head lamps. This needs to be decided per lamp kind, not asserted globally.

**5. [Medium] "16 sockets … with their `LightColor`" is false: six of the sixteen have a colour.**
`MODLOG.md:14200-14201`. Counting the manifest: `HeadLight1`, `HeadLight2`, `LWheelLight`,
`RWheelLight`, `BrakeLightL`, `BrakeLightR` carry `light_colour_rgba`; the ten flare-only sockets
(`HeadLight1a/1b`, `HeadLight2a/2b`, `LWheelLight_top/_bottom`, `RWheelLight_top/_bottom`,
`BrakeTrailL/R`) are `None` — which matches T-18, where those rows have `colour: null` because they
are `LensFlareComponent`-only. Worse, `socket_rows()` (`bm_lights.py:408-432`) keeps only the **first**
`LightColor` found per socket, so three different T-18 colours on the same socket collapse to one:
`HeadLight1` is [138,197,246,255] (T-L8), [223,91,75,0] (T-L11) and [255,0,0,0] (T-L18, battle mode);
the manifest records only the first. B-05/B-07 will need all three; the manifest's per-socket colour
is not enough and the log says it is.

**6. [Medium] "no light mesh has more" than three LODs is false.** `lights_manifest.json`
`lod_ladder.what` (generated at `bm_lights.py:484-486`) says "LOD1..LOD3 (no light mesh has more)".
The donor tree has `sportsmuscle_taillight_r_{c,l,lmshswap,r,rmshswap}` at **lod1..lod4** (five
families, verified on disk). The ladder really stops at 3 because `vanilla_ladder()` takes the
minimum LOD count across the 13 families (`bm_lights.py:290-318`), which is the right rule — the
sentence explaining it is wrong, and it is the sentence a reader will quote. The same wrong reason is
repeated in the MODLOG at 14218 ("the three LODs every donor lamp mesh reaches"), a sentence that is
true only because "reaches" means "all of them reach", immediately after a ceiling measured over all
13.

**7. [Low] Four of the twelve "PASS" checks are tautologies.** `checks` in the manifest:
`template_header_identical` is the literal `True`, `sum_reported_not_hidden` is the literal `True`,
`no_face_lamps_measured` is `len(NO_FACE) == 3` over a 3-row constant, and `lamps_with_faces_8` is
`len(entries) == len(LAMPS) == 8` after every empty lamp already raised `SystemExit`
(`bm_lights.py:392-397, 458-461`). "Its own 12 checks are all PASS" (14271-14274) therefore reports
eight real checks and four tautologies. `faces_total_4576` is a literal rather than
`emissive["lod0_faces"]` from `SLOTS.json`, so it does not test the material count, it retests the
constant. Harmless today, but it inflates the evidence line.

**8. [Low] The 8-lamp taxonomy is a typed table presented as derived, and one typed count sets the
LOD budgets.** `MODLOG.md:14192-14193`: "clustered by shared point (90 clusters) and named by the
dominant bone of each cluster". The clustering and face assignment are derived, but the parts are a
hand-authored `LAMPS` table (`bm_lights.py:66-93`): names, kinds, sides, parents, sockets and
`lenses` (3/3/3/3/3/3/1/1) are inputs. The nose bone yields **one** family that is split into two
parts by cluster-centroid X sign, so "named by the dominant bone" is not literally true; the rear
arches and tail strips are named by hand. `lenses` is the multiplier in every LOD budget
(`budgets = cap * lenses`, capped by the real face count), and for the two rear arches `lenses: 3`
has **no** supporting socket (`sockets: ()`) and is not derivable from the clusters (14 each) — it is
an unprovenance'd 3 that shapes LOD2/LOD3. The code comment two lines above says "No hand-typed
triangle count"; the count is not typed, but its multiplier is. Under R4 this should be labelled as a
parameter, or derived.

**9. [Low] "The material gives the dashboard and boot lamps no lens geometry" overstates the
measurement.** `MODLOG.md:14206-14209`. What is measured is "no Emissive-material face within
1.5565 m / 1.5827 m of the socket"; that supports "no emissive lens in this material", not "no lens
geometry" (geometry could exist under another slot) — the script's own evidence string is the honest
one. `Headlight_Centre` at 0.3909 m is the weakest of the three: 0.39 m is roughly the gap to the
left lens, so "no faces at all" rests on treating that distance as absence; no test distinguishes
"the centre lamp has its own lens" from "the centre lamp shares the two nose lenses".

**10. [Low] The Done check is manifest-driven and cannot see the thing it is trusted for.**
`spec_check.py:50-116` iterates `man["lamps"][*]["lod_files"]`, so only files the manifest lists are
checked (a stray RBM in the directory is never read) and every geometric expectation is the
manifest's own bbox, written by the same session. It cannot catch a left/right swap or a
socket→lamp mis-association, because the socket table is typed. I checked the associations
independently and they are right — `HeadLight1` (-0.452, 0.694, -2.977) lies inside the f_l head lamp
bbox, `HeadLight2` (+0.386, 0.527, -3.046) inside f_r, `LWheelLight` (-1.208, 0.963, -2.063) in the
f_l arch's x/z range, `RWheelLight` (+1.207) in f_r, `BrakeLightL/R` (±0.476) in the two tail strips
— but nothing in the card's Done proves it; only the log's prose does. `--fast` additionally trusts
the manifest's counts and bytes (`decode_only`, `bm_lights.py:566-600`), so it is a file-tamper
check, not a re-derivation.

**11. [Low] The "Done check (verbatim)" block is not verbatim.** `MODLOG.md:14245-14256` shows
`bm_lights.py --check` producing only its PASS line; the real run prints the 24 `blender: DECIMATED`
lines first (above). The final line and exit status match exactly, so no number is hidden — only the
word "verbatim" is wrong.

**12. [Note, already disclosed] The budget's operative number is accounting, not a build
measurement.** 288.6 KB lights + 4,790.9 KB B-02 = 5,079.5 KB, above the 4,915 KB cap; the green
figure (4,899.6 KB) subtracts 184,158 B of hypothetical CarPaintMM bytes for the moved faces. I
recomputed 184,158 from `vertices_per_lod * 24 + faces_per_lod * 6` and the net arithmetic both
match. UNKNOWN #7 states this; it is the only number in the row that cannot be confirmed until B-04
re-emits the body.

## Spot-checks (three numbers in the doc, against the JSON or the raw source)

| value in the doc | where checked | result |
|---|---|---|
| **4,576** Emissive LOD0 faces, slot 5 = PSKX material 5 (`MODLOG:14187-14188`, manifest `material`) | `Research/BatmobileGrab/SLOTS.json` slot 5 (`Batmobile_V3_Emissive`, `lod0_faces` 4576) **and** the raw PSKX: `Working/Appearance/grab/Playable_Batmobile_SF/SkeletalMesh3/Batmobile_V2.pskx`, `F['m']==5` → 4,576 faces (next largest 62,668 for material 0) | exact |
| head lamp f_l lod1 bbox **[-0.478,+0.503,-3.050]–[-0.356,+0.721,-2.965]**, 273 verts / 378 tris (`MODLOG:14231`) | decode `Working/Appearance/build_lights/sportsmuscle_headlight_f_l_lod1.rbm` with `rbm_geom` | exact (273 verts, 378 tris, bbox identical); the bbox also contains `SOCKETS_JC3.json` `HeadLight1` (-0.452, 0.694, -2.977) |
| **288.6 KB** lights, **4,899.6 KB** net, **184,158 B** paint-equivalent (`MODLOG:14289-14293`, manifest `budget`) | sum of the 24 RBM sizes = 295,518 B = 288.6 KiB; 4,790.9 + (295,518 − 184,158)/1024 = 4,899.6; 184,158 recomputed from `vertices_per_lod`/`faces_per_lod` | exact |
| 1,085 B header / 44 donor `CarLight` blocks / 6 texture names / strides (12,24,2) (`MODLOG:14211-14216`, `14259`) | decoded all 44 donor `*light*_lod*.rbm`: 44 `CarLight` blocks, `pre_static` 1,085 B, `mid_static` 16 B, 6 textures, strides (12,24,2) | exact |
| **21 T-18 rows** / **16 sockets** (`MODLOG:14200`) | manifest `t18_rows` = 21 (19 `mapped:true`), `sockets` = 16 (6 with `light_colour_rgba`) | counts exact, the "with their LightColor" qualifier is not (issue 5) |

## Done criterion vs what `--check` verifies

The card's Done has two halves and `spec_check --lights` covers both literally: it decodes each of
the 24 blocks, asserts one `CarLight` block, strides, header/mid-static/texture-table equality with
the clone, vertex/index counts and bbox against the manifest, file-header bbox against geometry, the
zeroed second-stream columns, and `m.write() == raw` — that is the "`GEOMETRY.md`-style decode …
round-trips" half. What it does not test is anything the card's Do asked for: T-18 values in the
block (issue 3), the `Window` pair (issue 4), the cut's completeness against the body/wheels (that is
`bm_lights --check`'s `every_face_once` + `faces_total_4576`, both self-checks), or the part frame
(issue 1). So the Done is met as written and the card is still not safe to consume.

## Verified green / not re-run

Verified: `spec_check --lights` (24/24, exit 0), `spec_check` assembly arm (295 blocks, exit 0),
`bm_lights --check` (full Blender re-derivation, exit 0), `bm_lights --check --fast` (exit 0),
`status_audit --check`, the manifest's face/vertex/byte/bbox/budget numbers, the left/right and
socket geometry, the donor header facts, and R2 (the transform is `bat_assemble.to_jc3_rot × scale +
offset` from `stations.json`, imported, not re-implemented — and it agrees with `BONES.json` pivots
and the socket positions).

Not re-run: the four tamper tests (they would require writing into `Working/Appearance/`, which this
review must not do; tamper 3's manifest-only change is the one I would most want to see replayed,
because `--fast` trusts the manifest). No game was launched, nothing was packed, installed or
committed.
