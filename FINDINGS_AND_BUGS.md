# Findings and bugs — JC3 Batmobile

Written 2026-10-09. Companion to `MODLOG.md` (chronological journal) and
`Builds/test-020/README.md` (that one build in detail). This file is the *consolidated*
view: what is now known, what was wrong, and what is still open.

Everything here is either measured from a file in this project or observed in game by the
user. Nothing is recalled from memory. Where a thing is not established, it says so.

- [F1](#f1--the-shipped-batman-mod-contains-no-batmobile-geometry) … [F13](#f13--preview-render-cost-dominates-the-tuning-loop)
- [B1](#b1--pskx-read-as-a-flat-source-psk) … [B14](#b14--gitignore-covered-4-of-the-30-top-level-trees)
- [L1](#l1--latent-bugs-and-traps-in-existing-tooling) latent bugs in tools that still work
- [R1](#r1--open-risks--unresolved-questions) open risks

---

## Findings

### F1 — The shipped Batman mod contains no Batmobile geometry

**Measured.** `Research/Vehicle/batmobile_mod/` holds 634 files. Exactly one vehicle entity:
`editor/entities/jc_vehicles/01_land/v0401_car_mugello_racingsupercar/
v0401_car_mugello_racingsupercar_civilian_01.epe`. Zero assets match
`bat|bike|night|tumbler`. All 288 RBMs are Mugello or `00_shared` vehicle parts.

The "Batmobile mod" is the **Mugello racing supercar with Batman textures**. This is why
MODLOG §14 chose Mugello as a donor and why tests 002/005 pulled Mugello assets from it.

**Consequence:** `Batmobile_V2.pskx` is the only real Tumbler geometry in this project.
Reshaping the Serpente is not a stylistic preference, it is the only available route.

```
Get-ChildItem 'E:\Modding\JC3-Batmobile\Research\Vehicle\batmobile_mod' -Recurse -File |
  Where-Object { $_.Name -match 'bat|bike|night|tumbler' } | Measure-Object
```

### F2 — The Tumbler and the Serpente have almost the same width:height ratio

**Measured.**

| | length | width | height | W/L | H/L | **W/H** |
|---|---:|---:|---:|---:|---:|---:|
| Batmobile (PSK) | 702.56 | 349.53 | 234.18 | 0.4975 | 0.3333 | **1.4925** |
| Serpente (160 parts merged) | 5.134 | 2.123 | 1.405 | 0.4135 | 0.2737 | **1.5110** |

W/H differs by 1.2 %. **No uniform scale, rotation or shear can make one read as the other**,
because there is nothing to transform — the shapes already agree on that proportion.

This is the quantitative reason test-009 (uniform scaling) read as *"looks fine / subtle"*.
It was never going to work, and the geometry says so.

**What differs** is `W/L` and `H/L`: the Tumbler is proportionally much bigger for its
length (0.4975 vs 0.4135 wide, 0.3333 vs 0.2737 tall). Its character is *where the mass sits
along the length*, which only a non-uniform fit can move. That is what test-020 does.

### F3 — A faithful envelope fit makes the car *bigger*, not lower

**Measured.** Scaling the Tumbler to the Serpente's 5.134 m length gives **2.554 m wide,
1.711 m tall** against the Serpente's 2.123 × 1.405. The Tumbler is taller *and* wider at
equal length, because its bbox includes the rear fins and aerials.

test-020 therefore ends up wider than vanilla (2.416 m) and about vanilla height
(1.478 m). Lowering the roof past that is bounded by F10.

### F4 — `Batmobile_V2.pskx` is a chunked container, not a flat Source PSK

**Measured from the bytes.** It opens `ACTRHEAD\0`, not `char[20] flags`.

```
0x00  "ACTRHEAD"      id[8]
0x08  version[16]
0x18  u64                             = 0 in this file
0x20  "PNTS0000"      id[8]          (id "PNTS", version "0000")
0x28  version[16]                     "0000" + zero fill
0x38  u32 stride                      = 12
0x3c  u32 count                       = 201338
0x40  float3[201338]
```

Both chunk headers are 32 bytes. Reading it as a flat PSK yields
`numVertex = 20100482` — the low 4 bytes of the root chunk's 8-byte size field.

### F5 — ~~There are no triangles in the file~~ WRONG (MODLOG §38): 299,837 triangles in `FACE3200`

**Measured.** A scan of all 17,357,622 bytes for 4-character all-caps ids finds only
`ACTRHEAD` (0x00) and `PNTS` (0x20); the other 580 hits are float data that happens to look
like ASCII. It is a stripped vertex cloud.

**Consequence:** point splat rendering is the only option for this asset — not a preference.

### F6 — The PSK axis mapping, now proven rather than inferred

MODLOG §15 recorded this as *"reasoned inference, not proven"*: X must be length, because
the alternative makes the car twice as wide as it is long. Plausible, but not evidence, and
every millimetre of the fit depends on it.

`psk_geom.py grid` settles it by rendering all nine (horizontal, vertical) axis pairs with
the camera on the third axis:

- horizontal X / vertical Y / camera Z → **top view** (length × width, four wheel masses)
- horizontal X / vertical Z / camera Y → **side elevation** (prow at high X)
- horizontal Y / vertical Z / camera X → **head-on** (wide and low, aerials above)

**X = length 702.56, Y = width 349.53, Z = height 234.19.** The inference was correct.
JC3 puts a vehicle's front at −Z and the prow is at high PSK X, hence the sign flip in
`_tumbler_cloud`.

```
python Tools\scripts\psk_geom.py grid ^
    "E:\Modding\JC3-Batmobile\Playable_Batmobile_SF\SkeletalMesh3\Batmobile_V2.pskx" `
    -o Working\Tumbler\psk_axisgrid.png
```

### F7 — The Tumbler's tallest feature is a fin a frozen topology cannot build

**Measured** in the rear slices (zn 0.72–0.92): `T max` runs **~0.15 m above `T p99`**
(1.817 vs 1.641 at zn 0.88). Fitting a roofline to a per-slice maximum lifts the boot lid
into a wedge with nothing on it. Hence `h_clip`, which caps how far the roof may be
*raised*: the fit can lower the greenhouse but cannot invent a spoiler.

### F8 — Donor slice extents must be measured across all 160 parts at once

**Measured failure.** The first carve produced a **flat slab**. Cause: a JC3 car is ~20
separate RBMs, and a bumper and a roof occupy the same length slices at very different
heights. Measuring each part's own slice ceiling and fitting it to the target's whole-body
roofline stretches every low part — sills, valances, underbody — *upward* to roof height.

Fixed by `_donor_slice_stats`, which computes one shared set of per-slice extents over all
parts. Same reasoning as the existing `make_ref`.

### F9 — `top_pct` has a hard floor: 80 tears the shell

**Measured**, on the shell block:

| `top_pct` | body_lod1 height | shell |
|---:|---:|---|
| 99 | 1.497 m | intact |
| 90 | 1.484 m | intact, visually indistinguishable from 99 |
| 80 | — | **torn**: large gap opens in the flank |
| 70 | — | **torn** |

99 ships. Going lower needs a per-vertex criterion (fit the target's *body* silhouette
rather than a percentile of all its vertices), not a more aggressive percentile.

### F10 — The roof cannot be lowered much further by this route

The height lever is `top_pct`, and F09 bounds it. Combined with F3 (the target is taller
than the donor at equal length) and F7 (raising is clamped), the achievable roof range is
narrow. test-020 lands at 1.478 m merged, against test-010's 1.053 m — test-010 got lower
only by hand-tuned squashing, which is exactly what this work replaced.

### F11 — `guard` pins the car's width entirely

**Measured.** At test-010's `guard=0.52` the width stayed at *exactly* 2.099 m after the
carve. The guard freezes vertices inside a disc around each measured wheel hardpoint, and a
car's widest point is its arches — so the widest vertices were all frozen.

test-020 uses `guard=0.40`: still protects the wheel opening, but lets the flank move.
This is the single riskiest parameter in the build and the first to raise on rejection.

### F12 — An unclamped skirt puts the car under the road

**Measured.** `skirt=0.25` drove the sill to **Y −0.129**. The underbody sits at Y 0.106
and the road at Y 0.020, so that is 0.15 m under the tarmac. Hence the hard `ground` clamp
at Y 0.020.

### F13 — Preview render cost dominates the tuning loop

**Measured.** `_shade` walks triangles in a Python loop:

| | 160-part merged vehicle | one shell block |
|---|---:|---:|
| triangle rasteriser | **64 s** | <1 s |
| point splat (`--splat`) | **1.7 s** | 1.7 s |

38× is the difference between trying twenty variants and trying two. The splat is too noisy
to judge shape on a whole vehicle, but the shell block is both fast and legible, and it is
where the Tumbler silhouette actually has to change — and where the 1024/3168 constraint
lives. So tuning renders the shell.

### F14 — test-020 is verified offline only

160/160 ORACLE PASS · `roundtrip` 160 byte-identical, 0 mismatched · `selftest` on the donor
tree unchanged at 190/0/3 · `aafdiff` vs test-010: 0 added, 0 removed, 388 identical,
exactly 160 different · `@files.xml` byte-identical.

Its `aaf/` tree is a copy of test-010's, so the only delta from a known in-game-good build
is the 160 RBM byte streams.

```
Builds\test-020\v0300_car_kensington_sportsmuscle_civilian_01.ee
5,534,434 B
sha256 EBFFDE358F9CAD87D40070806E8D5DB826407E9C8E0F2EA2370D97881A25F7E2
```

---

## Bugs found and fixed

### B1 — PSKX read as a flat Source PSK

`psk_bounds.py` reads `char[20] flags` then int32 counts. Applied to this PSKX it produces
`numVertex = 20100482` and a nonsensical bbox. **It fails silently** — see L1.

Fixed in `psk_geom.py`: locate `PNTS` by signature, read stride and count at +24, validate
`stride == 12` and that the payload fits, raise `PskError` otherwise.

### B2 — Mis-transcribed view table produced two wrong cameras

I wrote `psk_geom.VIEWS` from memory of `rbm_geom.VIEWS` as `top=(2,0,2), front=(0,1,1)`.
The real values are `top=(2,0,1), front=(0,1,2)`. Two of three views had the camera on the
wrong axis, so the depth buffer resolved the wrong surface.

Caught by grepping `rbm_geom.py` instead of trusting my notes. **Lesson: never transcribe a
constant from memory when the source is one grep away.**

### B3 — `-inf` z-buffer produced NaN and a garbage depth term

`splat` initialised `zbuf` to `-inf` and computed `d = zbuf - where(isfinite, zbuf, 0)`,
which is `-inf - 0 = -inf` and then `-inf - (-inf) = NaN` on empty pixels. Three numpy
warnings per render and an all-black depth ramp.

Fixed: `zbuf` to `np.nan`, normalise over `zbuf[hit]` only, clip before the uint8 cast.

### B4 — PowerShell parameter binding ate the sweep flags

Two separate failures in `_sweep_tumbler.ps1`:

- `-p` is a **prefix match for `-Params`** in PowerShell, so `-p guard=0.40` bound to the
  script's own parameter and failed with *"Params is specified more than once"*.
- `powershell -File script.ps1` does **not** parse PowerShell syntax in its arguments, so
  `-Params 'guard=0.40','top_pct=90'` arrived as the single literal string
  `'guard=0.40','top_pct=90'`.

Fixed by taking one `-Kv "a=1;b=2"` string and splitting on `;`. The comment in the script
records why, so the next person does not "fix" it back.

### B5 — The sweep previewed its inputs, so every variant looked identical

`_sweep_tumbler.ps1` rendered `$files` (the donor) rather than the written output. The whole
point of the sweep is to compare variants; it would have compared 160 identical copies.

Fixed to render `$out/<name>.rbm`. The header comment states the failure mode explicitly.

### B6 — Broadcast error on the width-gain gate

```
ValueError: operands could not be broadcast together with shapes (48,) (1024,)
```

`sx` is per-slice (shape `(N,)`); `fy` is per-vertex (shape `(n,)`). Fixed with in-place
indexed assignment `sx[si] = 1.0 + (sx[si] - 1.0) * (1.0 - fy * x_pin)`.

### B7 — First carve was a flat slab

Root cause in F8. Fixed by `_donor_slice_stats` over all parts. *This was the bug that made
the method look wrong; the method was fine, the frame was per-file.*

### B8 — Profile diagnostic used the wrong frame, so every number was wrong

`_dump_profile.py` built the shared frame from `sportsmuscle_body_lod1.rbm` alone
(Z span 3.720 m) while the build used all 160 parts (Z span 5.134 m). The target cloud was
scaled to a different length, so its "Y gain" column was meaningless — it reported gains
that did not appear in the actual build output.

Fixed with `--parts`. The script now prints which frame it used and from how many vertices,
and errors if they disagree.

**Lesson: a diagnostic built on a different frame than the build is worse than none — it
produces confident wrong numbers.**

### B9 — `h_clip` reasoned about wrongly

I believed `h_clip` suppressed roof *lowering* too, so the roof barely moved and I went
looking for the cause in `top_pct`. `np.minimum(dy, h_clip)` only caps `dy > 0`; lowering
passes through untouched. No code bug — a reasoning error, caught by inspecting the numbers
rather than by running more variants.

### B10 — `skirt` had no ground clamp

F12. Added `ground` (default 0.020) with `np.maximum` after the smoothstep.

### B11 — `aafdiff` aborted the build after step 4

`aafdiff.py` writes its report to **stderr**. With `$ErrorActionPreference = 'Stop'` the
pipeline surfaced it as `NativeCommandError` and terminated, so the build died *after*
packing and *before* printing the provenance diff — the most important output.

Fixed by relaxing the preference around those two calls only, with a comment saying why.

### B12 — Sweep script ran displace twice

An early version of `_sweep_tumbler.ps1` ran `python rbm_geom.py displace` twice (once to
collect the oracle log, once to write) and previewed the inputs. Rewritten; the file is now
a straight 1 → 2 → preview sequence.

### B13 — `cmd_grid` had a dead code block

A leftover `if d is None: d = ImageDraw.Draw(...)` inside the render loop, before `im` was
even built. Removed.

### B14 — `.gitignore` covered 4 of the 30 top-level trees

**The most dangerous bug found.** `git add -A` would have staged **72,393 paths, ~15 GB**,
including the entire 11 GB / 70,967-file 3ds Max install and 3.8 GB of service packs — on a
repo whose own header reads *"never commit game files or extracted assets."*

The old file ignored donors by path but missed the modpack, the Max trees, `Research/`,
`Batman Vs Rico/`, `No-Intro/` and `jc3-console-thingy-steam/`, and its extension list
covered a handful of formats.

Fixed: engine formats by extension so a stray copy anywhere is caught (`*.btc`, `*.ban`,
`*.pfxc`, `*.fraglib`, `*.filelist`, `*.wem`, …), directories for software and third-party
mods, and `Research/Physics/` excluded as extracted game data.

Verified: `git add -A --dry-run` now stages **31 paths, 848 KB**, all `.py`/`.ps1`/`.md`/
`.json`/`.txt`/`.bat`, no game-shaped or binary file.

`*.max` / `*.maxcompound` were deliberately **not** added: the Max install is covered by its
directory rule, and the ApexMax/HavokMax round-trip track will want its scenes versioned.

---

## L1 — Latent bugs and traps in existing tooling

These still work and will still bite someone.

**`psk_bounds.py` fails silently on chunked PSKX.** It assumes a flat PSK header. Given
this file it returns `numVertex = 20100482` and a plausible-looking-but-wrong bbox, with no
error. It was trusted in MODLOG §15 for the width/height ratios. Those ratios turned out to
be right (F2), but they were derived from a tool that should have refused to run.
*Fix: detect a leading `ACTRHEAD` and raise, or delegate to `psk_geom.read_verts`.*

**`um publish check` does not respect `.gitignore`.** It scans the directory tree, so it
flags files git would never add. It currently reports 2 failures on this project, both from
ignored paths: `Builds/test-019/*.ee` (a verbatim game file, correctly gitignored) and
`Tools/Deca/.../ghidra_strings/jc3.txt` (its private-key heuristic on a third-party string
dump). **Do not read its FAIL count as a leak indicator**; validate with
`git add -A --dry-run`.

**`vb1` layout is still UNVERIFIED.** Per MODLOG §22/§33 H4, every vb1 probe also fires on
vanilla (`body blk0`: non-unit normals 1019/1024, winding 719 out / 337 in). Do not trust any
normal or winding reading from it. The packed-normal slot is `0x0C` in the stride-`0x20`
buffer — *not* `0x10`, not `0x18`; writing at `0x18` clobbers the deform normal.

**3 files still do not round-trip: `missile_base_signature_lod{1,2,3}`.** Block 1 is
`GeneralMkIII` (the missile upgrade part), whose layout is unsolved. `selftest` reports them
as not-parsed, 0 mismatched. They are deliberately left at vanilla and do not follow the
reshape.

---

## R1 — Open risks / unresolved questions

**1. `guard=0.40` has never been tested in game.** It is deliberately looser than test-010's
0.52 (F11). All 160 files pass the offline oracle and round-trip byte-identically, which is
the same class of edit as test-007…010 — but the oracle cannot see the engine's reaction to
a wider arch. *If test-020 is rejected, raise `guard` to 0.46 before changing anything else.*

**2. Does an `hknpExternMeshShape` tolerate a reshaped render mesh?** test-016 proved
`.physicsc` is load-bearing, and the Havok collision is an extern mesh shape pointing at the
render mesh. Nothing has established whether the engine accepts a *reshaped* target behind an
extern shape. **test-020 answers this, and it is independent of the count question — no
count changed.**

**3. The 1024/3168 count check is still unlocated.** test-018 (index 3168→3165) and test-019
(vertex 1024→1025) both crash. Six candidate locations were searched and cleared
(MODLOG §33): `.epe`, `.physicsc`, `.lod` tables, `.ctunec`/`.pfxc`/`.etunec`/`.ftunec`,
the RBM header, and the codec itself. No patched offset, no hidden size table, buffers are
packed not aligned (mod-16 residues 11, 15, 3). It is either compiled into the engine or
derived from an asset not yet inventoried.

**4. The dropzone currently holds test-019, which crashes.**

```
dropzone sha256 281E59FD88BDF16E18E2E9FADDB24A4E1FD40933E4B9D8865481B93F1C7402F1
```

Run `Builds\test-020\install.ps1 -Action Status` to confirm before launching.

**5. No fins, no turbine pods, no enclosed wheel arches.** There are no vertices to make
them with — every edit in test-020 is a displacement of the donor's own 1024. `skirt`
narrows the gap around the wheels but cannot close it. The result reads as a wide, low,
armoured coupe, not as the Arkham Knight Tumbler. Getting fins needs either the count check
patched or a Havok-authored `.physicsc` (the ApexMax/HavokMax route, still unexplored).

**6. Nothing has been committed.** `E:\Modding\JC3-Batmobile` has no commits; staging is
entirely the user's call.

---

## Reproduction

```powershell
cd E:\Modding\JC3-Batmobile\Tools\scripts
$w = 'E:\Modding\JC3-Batmobile\Working\Tumbler'
$psk = 'E:\Modding\JC3-Batmobile\Playable_Batmobile_SF\SkeletalMesh3\Batmobile_V2.pskx'

# F1  no Batmobile geometry in the shipped mod
# F4/F5/F6  container, no triangles, axis proof
python psk_geom.py stats  $psk
python psk_geom.py grid   $psk -o "$w\psk_axisgrid.png"
# F2/F8/F7/F9  the slice table the fit works from
python _dump_profile.py --cloud $psk --parts "$w\parts.txt" --slices 20
# F14  rebuild and re-verify
powershell -ExecutionPolicy Bypass -File .\_build_tumbler.ps1
# B14  confirm the commit set
cd E:\Modding\JC3-Batmobile; git add -A --dry-run
```

Sweep a variant (see B4 for why the parameters are one `;`-separated string):

```powershell
powershell -ExecutionPolicy Bypass -File .\_sweep_tumbler.ps1 g040 "guard=0.40;top_pct=99;h_clip=0;pinch=0.85;skirt=0.10"
```
