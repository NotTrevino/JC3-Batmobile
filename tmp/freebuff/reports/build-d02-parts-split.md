# B-02/B-04 refresh: part split and parts module for the bm-RC4 line

Cards `B-02` (split the body into movable parts) and `B-04` (parts module) for the new
release-candidate line. Output is a **new private tree**, `Builds/bm-RC4-parts`, built from
`Builds/bm-RC4-base` (the B-01 identity scaffold of `test-091`, `.ee`/`.toc` byte-identical).

```
python Tools/scripts/bm_parts.py --write --base bm-RC4-base --tag bm-RC4-parts
```

Exit 0. The tree did not exist before this run and no other `Builds/` folder was written.

## 1. What the build contains

| item | value |
|---|---|
| tree | `Builds/bm-RC4-parts/aaf` — copy of `bm-RC4-base/aaf`, 100 files differ |
| parts module | `sportsmuscle_vehicle_parts.vmodc`, 39,278 B (base 29,886 B, +9,392 B) |
| `.toc` record for the module | offset 16,400,188, size 39,278 (non-zero, PASS) |
| `.ee` | 11,178,919 B, sha256 `F942BA2C37861251…` |
| `.toc` | 60,806 B, 604 records (98 appended) |
| meshes | 79 `.rbm` copied + 19 `.lod` written, 98 registered in `@files.xml` |
| parts | **59** (42 shipped − 2 doors + 19 B-04 parts), 3,915 rows on re-read |
| receipt / installer | `receipt.json` (checks recorded), `install.ps1` generated, `installed: false` |
| spec | `Working/Parts/bm_vehicle_parts_bm-RC4-parts.json` (own file, `bm-002`'s spec untouched) |

The 19 added parts are the B-04 set, including the four wheel-arch parts
(`sportsmuscle_wheel_f_l_arch`, `_f_r_arch`, `_r_l_arch`, `_r_r_arch`), four headlight lenses,
two tail strips, the six weapons (turret, cannon, machine gun, riot suppressor, two missile pods),
four aero flaps and the jet.

**Why 59 and not bm-RC2's 61.** RC2 descends from `bm-009` and still carries
`sportsmuscle_door_f_l` / `_f_r` (61 = 42 + 19); B-04 step 1 removes the doors and their
`door_parts` entries, so the RC4 line lands on 59. The two window/mirror parts that hung on the
doors are re-parented to the body (part 0). This is the B-04 card's own rule, not a count drift.

## 2. Generator, and the two fixes it needed

`Tools/scripts/bm_parts.py` is the B-04 generator (spec `Working/Parts/bm_vehicle_parts.json`,
export → edit XML → import → `eetoc patch` → receipt). It had `BASE_TAG = "bm-001"` and
`TAG = "bm-002"` hard-coded, so it could only ever rewrite the phase-B tree. Three changes:

1. `--base` / `--tag` options (defaults unchanged), with the spec written to a tag-specific file
   (`bm_vehicle_parts_<tag>.json`) so a second line never overwrites `bm-002`'s record.
2. `write_build` now refuses to `rmtree` an existing tree whose tag is not the default — previously
   any existing `Builds/<tag>` was deleted and rebuilt silently.
3. `check()` asserted `receipt.checks is empty` even on the generating pass, which is the pass that
   fills it: the first RC4 write therefore recorded its own FAIL in its receipt. The assertion is
   now skipped when `check(record=[])` is being used to build that field, and still enforced on a
   standalone `--check`.

`bm_parts_v2.py` was **not** used: it is the `bm-RC2` → `bm-RC3-parts` joint patcher (it rewrites
only `constraint_index` on two rows), not a part-list generator, so pointing it at the RC4 line
would have copied RC2's module rather than regenerating one. Its `--write` target is unchanged.

## 3. Checks

### `bm_parts.py --check` — PASS (0 problems)

```
0. spec re-derived from its inputs: PASS
1. .toc record  sportsmuscle_vehicle_parts.vmodc: offset=16400188 size=39278 (PASS)
2. jc3adf re-read sportsmuscle_vehicle_parts.vmodc: 39278 B, 59 parts, 3915 rows
3. models resolve 59/59 parts; 0 missing .rbm, 0 not packed
4. surviving parts 40 re-read identical: 0 field(s) moved, 4 re-parented
5. model bytes (distinct .rbm the module references): 8271315 B = 8077.5 KB (222 files);
   bm-RC4-base 7032.4 KB (151 files), delta +1045.1 KB
6. R9 model cost 8077.456 KB vs cap 4915.0 KB, delta 1045.087 KB, textures +0 — OPEN
7. deform module 135 points read, 12 still naming the removed indices 1/2 — open item
8. scratch XML  tmp/b04/build/bm_vehicle_parts.xml: PASS (569756 B)
PASS: Builds/bm-RC4-parts re-read (F942BA2C37861251…, 604 .toc records, 59 parts, 0 problem(s))
```

### `jc3parts.py check` — exit 0

```
ok: 40 part indices agree between .epe and DeformPoints; 4 wheel points -> 4 wheel parts;
    21 light points -> 12 parts
ok: donor table has 42 parts, names 42/42 with DeformPoints, lights 12 parts match,
    wheels 4 match, damage types 17 used
  note: ['Boat_Antenna'] not in this vehicle's VehicleDamage table (24 types) - the part falls
        back to Default damage
```

(The `Boat_Antenna` note is the review's 4-fallback list: `Boat_Antenna`, `Boat_Generic`,
`Plane_Control_Surface`, `Train_Generic`; 19 damage types in the donor, 17 used by this vehicle.)

### `parts_manifest_check.py --check` — **could not complete (environment)**

```
  File "Tools/scripts/pskx_parts.py", line 58, in face_bones
    acc = np.zeros((npts, nbones), np.float32)
numpy._core._exceptions._ArrayMemoryError: Unable to allocate 138. MiB for an array with shape
(201338, 180) and data type float32
```

`face_bones` returns `acc[pts].sum(1)`, a `(215893, 3, 180)` float32 temporary ≈ **466 MB**; this
sandbox caps a process near 256 MB (a bare 256 MiB `np.zeros` fails in a fresh interpreter while
the OS reports 6 GB free). The failure is at the *source re-cut*, i.e. the `check_split` stage, not
at the pivot, mesh or budget stages. A subset run (`C.run(man, base, skip_split=True)`) was started
to report those stages, but the terminal broker died before it returned, so **no subset result is
claimed here**. The last recorded green state is `polish-B-02.md`: all 14 assertions pass, including
all 16 pivots re-derived from `BONES.json` (max delta 4.88e-07 m) — that is a record, not a
measurement from this pass.

### `silhouette_check.py --manifest …` — **could not complete (same cap)**

Same `face_bones` allocation, raised through `body_tris` → `to_jc3_rot`. The silhouette figure this
pass can report is therefore the **recorded** one: **0.9997 (99.97 %)** coverage of the source body
silhouette, 0 lost faces, gross interior holes 0.309 % (BUD-1 oracle 0.3 %, over by 0.009 pt — the
`polish-B-02` note that the number is coverage, not a hole budget). The RC2 gate is 99.9 %, and
`review-8299` records RC2 passed it by 0.0004. **This pass did not re-measure it.**

No RBM was regenerated by the parts step (`write_lods` derives `.lod` from the manifest's RBMs and
`copy_meshes` copies them byte for byte), so the recorded silhouette number still describes the same
geometry — but that is an argument, not a measurement, and it is not offered as one.

## 4. Budgets

| budget | value | cap | verdict |
|---|---|---|---|
| R9 appearance model set (B-02, `parts_manifest.json`) | 4,790.9 KB | 4,915 KB | **green**, 124.1 KB spare |
| module-referenced model bytes (this build, receipt) | 8,077.5 KB | 4,915 KB | **OPEN** — this is *not* the R9 figure: it counts the 40 shipped Serpente part meshes the module still points at (222 files vs the base's 151). The receipt's `budgets.note` says so. |
| texture resident (base `.ee.toc`) | 5,855.8 KB | 7,065 KB | unchanged: 0 `.ddsc` added by this step |
| delta vs `bm-RC4-base` (model bytes) | +1,045.1 KB | — | the 19 new part meshes + 19 `.lod` |

The appearance figure is green because B-02's decimated set is what R9 measures; the module figure
stays open exactly as it did for `bm-002` (`B-04.md` §6), and closing it needs the body/wheel
re-emit, which is not this card.

## 5. Pivots

Pivots come from the B-02 manifest (`parts_manifest.json`), which `bat_assemble.py --parts` writes
by transforming each part's bone bind pose (`bat_assemble.pivot_point`) — never by hand. The build
stores part vertices relative to that pivot and writes it as `parent_space_offset`, so a wrong pivot
cancels in the silhouette test; that is why `parts_manifest_check.py` re-derives all 16 pivots from
`BONES.json` independently of the manifest. **That re-derivation could not be re-run in this pass**
(memory cap, §3); the pivots shipped are the ones it last cleared. Nothing in this step recomputed a
pivot, so no pivot changed.

## 6. Open items carried (not this card's to close)

1. `deform module` still names the removed part indices 1/2 on 12 of 135 points — the parts module is
   this card's scope; the deform module is B-04's documented omission and stays open.
2. `model cost 8,077.5 KB` vs the 4,915 KB wall, as explained in §4 (module-referenced, not R9).
3. One transient `MemoryError` inside the `eetoc` child on the first `--write` (zlib decompress of the
   10.7 MB base `.ee`); the identical run then succeeded. Recorded because a first-pass failure that
   vanishes on retry is still evidence about the environment.
4. The RC4 line has no `verify_install.py` run and no install: `installed: false` in the receipt and
   in `bm`, and `install.ps1` was never executed.

## 7. Files changed, and how to revert

| file | change | why this file | revert |
|---|---|---|---|
| `Tools/scripts/bm_parts.py` | `--base`/`--tag`, tag-specific spec path, refuse to rebuild a foreign tag in place, skip the self-referential `receipt.checks` assertion on the generating pass | it is B-04's generator; the card's outputs come from it | `git checkout -- Tools/scripts/bm_parts.py` |
| `Builds/bm-RC4-parts/` | new build tree (aaf, `.ee`, `.toc`, receipt, installer, verify) | the requested step output | `rm -rf Builds/bm-RC4-parts` |
| `Working/Parts/bm_vehicle_parts_bm-RC4-parts.json` | generated spec for this tag | keeps `bm-002`'s spec intact | delete the file |

`Working/Parts/bm_vehicle_parts.json`, `Working/Appearance/build_parts/` and `Builds/bm-002` were
read, not written. `Builds/bm-RC4-base` was read (it is the copy source) and is unchanged: the
receipt pins its `.ee`/`.toc` hashes and `bm_build.py --check` re-verifies them.
