## B-03 · Emissive `CarLight` blocks and light parts — done (2026-10-29)

**Delivered.** `Tools/scripts/bm_lights.py` (`--write` / `--check`, plus `--check --fast`),
`Working/Appearance/build_lights/` (24 RBMs = 8 lamp parts × 3 LODs + `lights_manifest.json`), and a
`--lights` arm on `Tools/scripts/spec_check.py`. Nothing packed, installed or committed; no game file
touched; B-01 is deferred above, so this is a desk build exactly like B-02.

**The cut.** All **4,576** `Batmobile_V3_Emissive` LOD0 faces (SLOTS.json slot 5 = PSKX material 5)
leave the body/wheels for **8 lamp parts**, clustered by shared point (90 clusters) and named by the
dominant bone of each cluster (`pskx_parts.face_bones`):

| part | kind | parent | clusters | LOD0 faces | bones (faces) | lamp sockets (T-18 rows) |
|---|---|---|---|---|---|---|
| `sportsmuscle_headlight_f_l` | head-lamp lens | 0 | 6 | 378 | `Batmobile_Nose_Mesh` 378 | HeadLight1/1a/1b (T-L8, 11, 18, 22, 25, 27) |
| `sportsmuscle_headlight_f_r` | head-lamp lens | 0 | 6 | 378 | `Batmobile_Nose_Mesh` 378 | HeadLight2/2a/2b (T-L9, 12, 19, 23, 26, 29) |
| `sportsmuscle_wheel_f_l_arch` | wheel-arch light | 26 | 11 | 612 | `Damper_Left_Front_02` 594, `Wheel_Frnt_Left_Disc` 18 | LWheelLight/_top/_bottom (T-L13, 20, 33, 34) |
| `sportsmuscle_wheel_f_r_arch` | wheel-arch light | 27 | 11 | 612 | `Wheel_Frnt_Right_Disc` 612 | RWheelLight/_top/_bottom (T-L14, 31, 32) |
| `sportsmuscle_wheel_r_l_arch` | wheel-arch light | 11 | 14 | 1,146 | `Wheel_Rear_Left_Disc` 1,146 | none in the rig |
| `sportsmuscle_wheel_r_r_arch` | wheel-arch light | 12 | 14 | 1,146 | `Wheel_Rear_Right_Disc` 1,146 | none in the rig |
| `sportsmuscle_tailstrip_r_l` | tail strip | 0 | 14 | 152 | `SUSP2_Wheel_Rear_Left` 152 | BrakeLightL, BrakeTrailL (T-L15) |
| `sportsmuscle_tailstrip_r_r` | tail strip | 0 | 14 | 152 | `SUSP2_Wheel_Rear_Right` 152 | BrakeLightR, BrakeTrailR (T-L16) |

4,576 / 4,576 faces accounted, none twice. **21 T-18 rows** are hosted and **16 sockets** resolve
against `SOCKETS_JC3.json` with their `LightColor`. Part names follow T-18's own new-part naming
(`sportsmuscle_wheel_f_*_arch`, parts 42/43); the rear arches and the tail strips are new names because
the rig has no socket for them and donor part 8 already owns `sportsmuscle_taillight_r_l`. The cut is
recorded as the source face-index list + sha256 (`9ac665d8…`) so B-04/B-05 re-emit the body/wheels
without those faces.

**Three rig lamps have no Emissive faces at all** (measured, not assumed): `Dashboard_Light` 1.5565 m
from the nearest lamp face, `BootLight` 1.5827 m, `Headlight_Centre` 0.3909 m. The material gives the
dashboard and boot lamps no lens geometry — that is what the files say, and this card does not invent
one.

**The block.** Every lamp LOD is ONE `CarLight` block cloned from
`sportsmuscle_headlight_f_l_01_lod1.rbm`: the 1,085 B pre-static header, the 16 B mid-static and the
6-name texture table are **byte-identical to the template** (that is what `spec_check --lights`
proves); only the buffers are ours — positions 12 B/vertex, the 24 B second stream `(u, v, 0, 0,
packed, packed)` with our BmAK UVs in `u,v` (Blender-decimated per LOD) and the packed pair copied from
the nearest template vertex (§102d: nobody has decoded it). The LOD ladder is the donor's own: the
three LODs every donor lamp mesh reaches (head lamps ship lod1..lod3), ceiling = the largest `CarLight`
triangle count at that level over the 13 donor light meshes × the lamp elements the part hosts (3 for a
3-lens lamp, 1 for a tail strip) → `[244, 108, 50]` tris per lens. **No `Window` block is written**:
the BmAK lamp is one emissive surface with no separate lens shell, so only the emitter exists.

**Read-back (the `GEOMETRY.md`-style decode round-trips).**

```
file                                    block     strides      verts  tris  bbox m
sportsmuscle_headlight_f_l_lod1.rbm     CarLight (12, 24, 2)    273   378  [-0.478,+0.503,-3.050]-[-0.356,+0.721,-2.965]
sportsmuscle_headlight_f_r_lod1.rbm     CarLight (12, 24, 2)    273   378  [+0.356,+0.503,-3.050]-[+0.479,+0.721,-2.964]
sportsmuscle_wheel_f_l_arch_lod1.rbm    CarLight (12, 24, 2)    465   612  [-1.271,+0.744,-3.137]-[-1.145,+1.262,-2.811]
sportsmuscle_wheel_f_r_arch_lod1.rbm    CarLight (12, 24, 2)    465   612  [+1.145,+0.744,-3.137]-[+1.271,+1.262,-2.811]
sportsmuscle_wheel_r_l_arch_lod1.rbm    CarLight (12, 24, 2)    607   731  [-1.356,+0.594,+2.619]-[-1.211,+1.246,+3.049]
sportsmuscle_wheel_r_r_arch_lod1.rbm    CarLight (12, 24, 2)    608   732  [+1.211,+0.594,+2.619]-[+1.356,+1.246,+3.049]
sportsmuscle_tailstrip_r_l_lod1.rbm     CarLight (12, 24, 2)    134   152  [-1.487,+0.670,+3.255]-[-1.103,+0.783,+3.340]
sportsmuscle_tailstrip_r_r_lod1.rbm     CarLight (12, 24, 2)    134   152  [+1.102,+0.670,+3.255]-[+1.486,+0.783,+3.340]
```

(lod2/lod3 units are in `lights_manifest.json` `bytes_per_lod`/`faces_per_lod`; every file's header
bbox equals its geometry.) Each side sits at its own bone's X (left = −X: `BONES.json` pivots −1.211 /
+1.21 for the front discs), which is the cross-check that the ONE transform is used — R2's
`bat_assemble.to_jc3_rot * scale + offset` (`psk2rbm.to_jc3` is the older reflection and mirrors X).

**Done check (verbatim).**

```
$ python Tools/scripts/spec_check.py --lights Working/Appearance/build_lights
CarLight: checked 24 blocks over 8 lamp parts; spec mismatches 0
exit=0

$ python Tools/scripts/spec_check.py Working/Appearance/build_parts Builds/test-091/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_body_lod1.rbm
checked 295 blocks; spec mismatches 0; template values silently inherited 0
exit=0

$ python Tools/scripts/bm_lights.py --check
PASS: 8 lamp parts / 24 RBMs, 4576 Emissive faces cut, 16 lamp sockets, 21 T-18 rows hosted, 3 rig lamps with no faces; model 288.6 KB lights, sum 5079.5 KB, net 4899.6 KB of 4915 KB
exit=0

$ python Tools/scripts/status_audit.py --check
STATUS.md is current
exit=0
```

`bm_lights.py --check` re-derives every byte from the PSKX — including re-running Blender for all 24
LODs — and compares the files and the manifest; it passed after a full `rm -rf` + `--write`, so the
build is reproducible. Its own 12 checks are all PASS (`faces_total_4576`, `every_face_once`,
`lod_budget_within_vanilla_ladder`, `lamps_with_faces_8`, `lods_each_3`, `lod_files_unique`,
`carllight_header_from_template`, `roundtrip_byte_identical`, `template_header_identical`,
`net_model_budget_green`, `sum_reported_not_hidden`, `no_face_lamps_measured`).

**Budget (R9, both numbers).** lights **288.6 KB**, B-02 **4,790.9 KB**, sum **5,079.5 KB**; the faces
move out of the body/wheels, so the operative figure is the net: 4,790.9 + (288.6 − the marginal
CarPaintMM bytes of the same faces, 184,158 B) = **4,899.6 KB of 4,915 KB** (green, 15 KB spare). The
sum is reported rather than hidden: nothing is added without a cut.

**Tamper tests (4/4 caught, each reverted and re-checked to PASS).**

| tamper | result |
|---|---|
| `sportsmuscle_headlight_f_l_lod1.rbm`: one byte of the cloned 1,085 B header flipped (0x3F→0x3E) | `spec_check --lights` exit 1, `FAIL … 1085 B header differs from …sportsmuscle_headlight_f_l_01_lod1.rbm`; `bm_lights --check --fast` exit 1, `cloned header differs` |
| `sportsmuscle_wheel_f_l_arch_lod2.rbm`: file header `bbox_min.x` −1.2725 → −1.2625 | `spec_check --lights` exit 1, `FAIL … file header bbox != geometry` |
| `lights_manifest.json`: `lamps[0].faces_per_lod[0]` 378 → 377 | `spec_check --lights` exit 1, `FAIL … 1134 indices vs manifest 377 tris`; full `bm_lights --check` exit 1, `lights_manifest.json: differs in ['lamps']` |
| `sportsmuscle_tailstrip_r_r_lod3.rbm` deleted | `spec_check --lights` exit 1, `FAIL … missing` |

`--fast` deliberately checks the files only (decode, header equality, counts, re-encode); the full
`--check` is the one that also re-derives the manifest — tamper 3 shows both.

**UNKNOWNs and limits.**

1. **The `CarLight` material parameters are still undecoded** (§102d): the block is a byte-exact clone
   of a vanilla header, so its emissive colour/intensity is whatever the template's is. Only the
   *light* colours are decoded (T-18 / `LIGHTS.json` `LightColor`, recorded per socket in the
   manifest), not the block's own numbers.
2. **The 24 B second stream's packed pair** (columns 4,5) is copied from the nearest template vertex —
   no decoded field says what it is, so it is copied, never authored.
3. **The texture table is the template's** (shared `car_lights_kensington_modern_*`). Our UVs are BmAK
   UVs, so the mapping from UV to that atlas is not proven — a night look in phase Q decides it.
4. **No `Window` lens block** (reason above). Whether the game needs the pair for a lamp to read
   correctly is a runtime question, not a file one.
5. **Which light list the renderer reads** (module entries vs `.epe` `SVehicleLight`) is still G2-33's
   UNKNOWN; this card only makes the emitter meshes exist. Wiring them to parts is B-04
   (`has_lights`, `part_index`) and B-07.
6. **Rear-arch lamps have no BmAK light socket** (the rig carries `LWheelLight`/`RWheelLight` at the
   front only): their geometry is cut, but their module row would be a new entry — a T-18/B-07 gap,
   listed rather than filled.
7. **The budget's "net" is an accounting figure, not a build measurement**: it credits the marginal
   CarPaintMM bytes of the moved faces at the same LOD budgets (24 B/vertex, 2 B/index). The exact
   number arrives when B-04/B-05 re-emit the body and wheels without the cut faces.
8. Nothing here proves anything renders; that is phase Q.

**Revert:** delete `Tools/scripts/bm_lights.py`, `Working/Appearance/build_lights/`, this section and the
intended-change section; restore `Tools/scripts/spec_check.py` from git (drop the `--lights` arm);
remove the B-03 row from §12. No game file, build, save or dropzone was modified, and nothing was
committed.
