# Correction 3/9 - the 12 unfaithful texture rows, recorded from bytes

Date: 2026-11-07. Tree: `Builds/bm-RC4-appearance` (private, `not_deployed: true`).
Record changed: `texture_ledger.json` -> `refusals` (and its rendered table in `texture_ledger.md`).
Generator changed: `Tools/scripts/appearance_bake.py` (`refusal_evidence()` + `--refusals-only`).
**No texture, mesh, material or packed file was touched by this record.**

## 1. What the record now holds

`refusals` is no longer a list of prose strings built at bake time. Every entry is produced by
`refusal_evidence()`, which reads three things and nothing else:

| input | what it supplies |
|---|---|
| `Working/Appearance/grab/**/Texture2D/*.tga` | present/absent, path, bytes, sha256, size, mode, every hit |
| the 25 RBMs in the tree (`rbm_geom` blocks) | `CarPaintMM` count and each block's `SupportDmgBlend` bytes |
| `Tools/JCMR-src/assets/jc3/shaders/*.fb.txt` (961 headers) | whether a chapter field or a ramp sampler is declared anywhere, with the matching lines kept |

Each entry carries `present_in_grab`, `present_in_playable_batch`, `source_file`, `bytes`,
`sha256`, `size`, `mode`, `reason`, `measurement`, `byte_evidence[]`, `status: "refused"` and
`counted_in_the_12`. Regeneration is record-only:

```
OPENBLAS_NUM_THREADS=1 python Tools/scripts/appearance_bake.py --refusals-only
```

The gate run that follows it is `appearance_progress.py` (section 4). A rebuild of the tree runs the
same function, so a stale reason cannot survive a rebuild.

## 2. The 12 rows, with the file and the byte-level reason

Order and grouping are the correction's. "12" is the count of rows with **no carrier at all**; the
Leather ramp is measured too and is the 13th texture refusal (its pixels exist - only the sampler
does not), so it is marked `counted_in_the_12: false` and named in section 3.

### 2.1 The four chapter masks (D9) - pixels present, no chapter state to read

| texture | file | bytes | sha256 (first 16) | size |
|---|---|---:|---|---|
| `..._Body_Damage_ChapterMask` | `Working/Appearance/grab/Playable_Batmobile_SF/Texture2D/Batmobile_V3_TEXTURES_Body_Damage_ChapterMask.tga` | 1,791,138 | `e78f02365cbd6303` | 1024x1024 RGB |
| `..._Weaponry_Damage_ChapterMask` | same directory, `..._Weaponry_Damage_ChapterMask.tga` | 1,327,221 | recorded in the ledger | 1024x1024 RGB |
| `..._WheelArch_Damage_ChapterMask` | same directory, `..._WheelArch_Damage_ChapterMask.tga` | 1,612,406 | recorded in the ledger | 1024x1024 RGB |
| `..._Undercarriage_Damage_ChapterMask` | same directory, `..._Undercarriage_Damage_ChapterMask.tga` | 1,257,047 | recorded in the ledger | 1024x1024 RGB |

Measured refusal, recomputed by `--refusals-only`:

* **0 of 961** shader reflection headers contain the word `chapter` (case-insensitive, whole
  population in `Tools/JCMR-src/assets/jc3/shaders/*.fb.txt`). There is no selector uniform to bind.
* **160** `CarPaintMM` blocks across the 25 RBMs; **every** one reads `SupportDmgBlend = 0.0`
  (`static_support` float[1], payload **+0x12d**, per `Research/JC3Grab/CB0_SLOTS.md` §3). Distinct
  value set: `[0.0]`.
* `SupportDmgBlend` is a global blend scalar. It is not an index, so it cannot select one of four
  chapters, and no per-chapter field exists in the decoded block.

**Decision: kept declared, no carrier written.** The correction allows closing a row only with a
carrier that changes in-game state, proven before writing. The only writable state here (mask into a
texture slot + `SupportDmgBlend = 1`) is one permanent pre-damaged look for all chapters: it would
*remove* the vanilla chapter behaviour rather than carry it, and its in-game read is UNKNOWN under the
test ban. That is a compromise, not a faithful route, so it was not written. `SupportDmgBlend` stays
0.0 in all 160 blocks.

### 2.2 The eight rows whose pixel set the bake could not supply

| rule | texture | present? | file / census | byte-level reason |
|---|---|---|---|---|
| P1 | `Batmobile_Micropattern_A` | no | 0 hits in 61 `.tga` under `Working/Appearance/grab/**/Texture2D` | no pixels to bake; nothing was substituted |
| P1 | `Batmobile_Micropattern_A_Normal` | no | 0 of 61 | same; the MIC points at `Engine.Batmobile_Micropattern_A_Normal` (package `-590`, `Research/BatmobileGrab/SLOTS.md`), which this export batch does not contain |
| P1 | `Batmobile_Micropattern_B` | no | 0 of 61 | no pixels |
| P1 | `Batmobile_Micropattern_C` | no | 0 of 61 | no pixels |
| R2 | `Batmobile_V3_Wheel_E` | no | 0 of 61 | no emissive pixels for the four arch strips; and 0 `CarLight` blocks exist in the tree, so no `s5 EmissiveMap` to bind even with pixels |
| D10 | `Batman_BM3_V2_Lacquered_Underlayer_Ramp` | **yes** | `Working/Appearance/grab/Startup/Texture2D/...tga`, **4,050 B**, 64x512 RGB | pixels exist but **not in the `Playable_Batmobile_SF` batch the bake reads**; independently, 0 of 961 headers declare a ramp texture parameter, so there is no sampler |
| D10 | `Batmobile_V3_Body_ColourRamp` | no | 0 of 61 | no pixels, and 0 of 961 headers declare a ramp sampler |
| D5 | `Aniso_ramp_Lacquered` | no | 0 of 61 | no pixels; the anisotropy lobes are a UV-space fake with no sampler (0 of 961 headers name one) |

The `present=False` note on the Underlayer ramp is the one **measurement that corrected the
report's prose**: `build-d04` §3 says "`present=False`; and no ramp sampler on any block". The file
is in the grab, in the `Startup` package, at 4,050 B and 64x512. The refusal stands, but for the
sampler and the batch, not because the pixels are missing.

## 3. The row that is refused for the sampler alone (13th texture refusal)

| rule | texture | file | bytes | size | reason |
|---|---|---|---:|---|---|
| D10 | `Batman_BM3_V2_Leather_Ramp` | `Working/Appearance/grab/Playable_Batmobile_SF/Texture2D/Batman_BM3_V2_Leather_Ramp.tga` | 5,786 | 64x512 RGB | pixels present; 0 of 961 headers name a ramp sampler |

The `ramp` token census is recorded in the entry so the claim cannot be read as "the word does not
occur": it occurs **4** times, always as `float DamageRampWeight;` in `window.fb.txt`,
`windowdamage.fb.txt`, `windowsimple.fb.txt`, `windowsimpledamage.fb.txt` - a float, in window
shaders, never a texture parameter. A sampler would have to appear as a texture binding in one of
the 12 `CarPaintStaticMaterialParams` headers; none does.

## 4. The appearance gate, re-run

```
OPENBLAS_NUM_THREADS=1 python Tools/scripts/appearance_progress.py \
    --build Builds/bm-RC4-appearance \
    --json  Builds/bm-RC4-appearance/progress.json \
    --md    Builds/bm-RC4-appearance/progress.md
```

```
class       total     ok   part   miss   excl       %
geometry       25     25      0      0      0   100.0
materials      19     19      0      0      0   100.0
textures       38     17      7      0     14    53.9
factors       257    106     29      0    122    46.9
OVERALL       339    167     36      0    136    54.6
strict 49.3%  |  of transferable 91.1%
plan: bake 23 route 61 drop 88 | unclassified 0
```

**The percentages did not move: 54.6 / 49.3 / 91.1 / 53.9**, exactly the review's forecast. That is
the correct outcome, not a failure to register: `appearance_progress.textures()` counts the 38 unique
BmAK texture objects the used materials bind, and takes each one's status from its disposition. A
refusal record adds no member to that set and changes no disposition. The four `s2` selectors built
by D3 stay `partial` (21-44 % of texels take their block's band; channel order R/G/B =
rough/reflect/metal is UNKNOWN), the six P1/micropattern rows stay `excluded`, the atlas is not one
of the 38, and the bake rewrites existing `s1` files in place. Only a row whose *disposition* changes
- a row that gains a carrier the engine reads - could move these numbers, and section 2.1 explains
why the chapter masks did not.

## 5. `complete` was not raised

`Builds/bm-RC4/receipt.json` still reads `"complete": false`; the appearance tree's own
`receipt.json` carries `not_deployed: true` and has no completion flag to raise. Nothing in this
record sets a completion flag true, and the RC state remains incomplete by design: 12 rows have no
faithful carrier, and the other 11 texture rows include the four `s2` partials.

## 6. Limits

* **No game run** (test ban). Whether `SupportDmgBlend = 1` would even be read as a permanent damage
  state is UNKNOWN; it is recorded as unproven, not as a working carrier.
* **Texture-slot semantics** beyond `s0` dif / `s1` normal / `s2` property map are not established
  for `CarPaintMM`; the chapter-mask refusal therefore does not claim which slot would hold it.
* The 8 "pixel" rows are counted from the **grab**, not from the game: a texture absent from
  `Working/Appearance/grab` could still exist in an unexported package (`Aniso_ramp_Lacquered` and
  the micropatterns are referenced at negative `Engine.*` package indices, which this export batch
  does not include).
* `factors` remains 46.9 % - outside this correction's scope and unchanged.

## 7. Revert

```
git checkout Tools/scripts/appearance_bake.py
```

and restore the previous `refusals` array in `Builds/bm-RC4-appearance/texture_ledger.json` (the
record-only write, no texture tree change). Deleting the two ledger files and re-running the bake
regenerates them from the code in the same shape.
