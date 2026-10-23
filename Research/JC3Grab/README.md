# JC3 grab — archives, values, structure, geometry

Read-only grab of the installed Just Cause 3. Every script has a `check` that re-reads the game and
fails on drift:

```
python Tools/scripts/jc3index.py  build       # archives + filelists + DLC dictionary -> INDEX.jsonl (G2-1)
python Tools/scripts/jc3index.py  check
python Tools/scripts/jc3grab.py   build --all # 233 entities -> .vmodc values           (G2-2/3)
python Tools/scripts/jc3grab.py   report --donor v0300_car_kensington_sportsmuscle_civilian_01
python Tools/scripts/jc3detail.py build --all # 233 entities -> .epe graphs + .rbm bounds (G2-5/6)
python Tools/scripts/jc3detail.py report
python Tools/scripts/jc3geom.py   build --all # every .rbm payload: positions, indices, materials (G2-5)
python Tools/scripts/jc3geom.py   report
python Tools/scripts/jc3geom.py   check
python Tools/scripts/jc3hkx.py    check --all # .physicsc packfiles: shapes, compounds, stations (G2-8)
python Tools/scripts/jc3hkx.py    wiring --all # compound instance -> part index/name
python Tools/scripts/jc3hkx.py    report      # SHAPES.md
python Tools/scripts/jc3phys.py   build --all # .physicsc station quads                  (G2-8)
python Tools/scripts/jc3phys.py   report
python Tools/scripts/jc3fleet.py  report      # FLEET.md: geometry + donor ranking       (G2-5)
python Tools/scripts/jc3fx.py     build       # every .effc/.ctunec/.trim               (G2-9)
python Tools/scripts/jc3fx.py     report      # FX.md
python Tools/scripts/jc3fx.py     check
python Tools/scripts/jc3fx.py     dump <substr> [--max N] [--files N]
python Tools/scripts/jc3adf.py    verify      # reader vs Gibbed on the 4 parts files that convert
python Tools/scripts/jc3parts.py  build       # 233 parts modules -> PARTS_TABLE.jsonl (G2-7)
python Tools/scripts/jc3parts.py  wiring      # part indices/lights/wheels via DeformPoints
```

## 1. The index (`INDEX.jsonl`)

| item | count |
|---|---|
| `.tab`/`.arc` pairs scanned | **88** (56 base, 7 patch, 25 DLC under `dlc_win64/*/`) |
| archive entries | **81,953** |
| entries named | **81,951 = 99.998%** |
| base / patch / DLC | 47,556 / 47,557 · 13,713 / 13,714 · 20,682 / 20,682 |
| DLC entries | **20,682 / 20,682** named |
| unnamed entries | **2**, both `.wavc`, censused by magic byte in `INDEX.json` |

Two name sources, both hashed through the same Jenkins lookup3: Gibbed's filelists (**55,811** rows)
and JCMR's shipped `assets/jc3/dictionary.json` (**26,051** rows, which is what closes the DLC),
plus a generated list in `Tools/names/` (**89** rows, every one accepted because its hash is a real
`.tab` record). Resolving a path is one lookup; `MOUNT_RANK` says which copy loads
(patch > dlc > base).

The generated list is only for entries nothing else names. 88 were navmesh tiles, and their path
shape is regular: `ai/tiles/<x>_<y>.navmeshc` (`navmesh4x4.nmvhl` caps the grid at ±2048, and the
`.nmvhl` frame records are four `s16` tile coords each). Hashing the **52,937** points the tiles
share one coordinate with gives **88/88** hits and no collisions with known paths, so `x` and `y`
are s16 and the derived paths are what the game hashes.

One more came from **where the entry sits**. Within a `.arc` the payloads are written in ascending
path order, so an unnamed record is bracketed by its alphabetical neighbours. `patch_win64/game4`
record `9EBCE9A4` (655,360 B of float data, i.e. an `.hmddsc`) sits between
`…/dlc3_starfish_base_02/…_landmark_dif.hmddsc` and `…/dlc3_starfish_base_04/…_landmark_dif.hmddsc`,
so the missing sibling is `…/dlc3_starfish_base_03/dlc3_starfish_base_03_landmark_dif.hmddsc` — and
that string hashes to `9EBCE9A4`. The bracket is the evidence; the hash equality is the proof. The
same check reproduces a known neighbour (`dlc3_satellite_pontoon_14`, which has a doubled directory)
through the same ordering.

The two that remain are `.wavc` dialogue takes, and no filelist, dictionary, string in the install or
candidate search names them. Both are 16-byte-header + **FSB5** FMOD banks, like all 31,000 `.wavc`
entries. One is `patch_win64/game4` `016DE9D1`, which physical order brackets at
`sound/dialogue/ara/mission_mm320_dial_gameplay_090.wavc` < it < `…_gameplay_start05.wavc`; every
numeric take 0…9999 in widths 1…4, every known basename in all 40 dialogue directories, and every
English `mm320` take under the Arabic directory were hashed, none matching. The other,
`archives_win64/game67` `966DB7BC`, is the **only** entry in its archive (18,800 B, one-sample FSB5),
so it has no neighbours and no bracket.

Vehicle space: **5,435** indexed vehicle paths, **233 `.ee`** entities.

## 2. Modules and values (`VOCABULARY.md`)

`.ee` bundles are the unit of content: **modules do not exist as separate archive entries**. Vanilla
Serpente = 566 inner files / 13.6 MB un-AAFed (5.5 MB archived).

| item | count |
|---|---|
| inner files (all entities) | **135,283** |
| `.vmodc` modules | **6,045** |
| decoded to named values | **6,045 (100%)** |
| value rows | **3,111,689** |
| module types / member paths | **52 / 1,421** |

`VOCABULARY.md` gives one table per module type: member, type, fleet min/median/max, donor value.
Sample: `RigidBody.mass` **50 … 550,000, median 3,000**, donor **975**;
`LandSteering.t_to_full_steer_s` donor **1.2** vs its own `_ai` twin **2.0**.

Traps carried forward: module **instance** names truncate at 32 characters (group by `type-name`),
and every land vehicle ships an `*_ai` twin of several modules with *different* values.

## 3. Structure (`ENTITIES.md`)

`jc3detail.py` decodes each entity's `.epe` (RTPC graph, `ConvertProperty`) and the RBMDL header of
every `.rbm` in the bundle (`rbmhdr.parse_header`, which takes bytes — these meshes never exist as
files).

| item | value |
|---|---|
| `.epe` classes across the fleet | **103** |
| `CPartProp` (mesh parts) | **11,041** — 3 … 161 per entity, median **48** |
| `SVehicleLight` | **3,972** — 4 … 54 per entity, median **16** |
| `SAttachedEffect` / `SDynamicAttachedEffect` | **5,342 / 4,344** |
| `SWeaponPoint` / `CBulletWeaponBase` / `CMissileWeaponBase` | **300 / 57 / 25** |
| meshes per entity | 11 … **807**, median **229** |
| RBM version | 1.16.0 everywhere |

Settled by this: **LGT-1** (the donor's 22 `SVehicleLight`s with `preset_id`/`diffuse`/`radius`/
`spot_angle`/`volumetric_mode`, plus the fleet's preset vocabulary) and **PRT-1** (the donor's 40
`CPartProp`, `part_index` → mesh name, gap at 25). `PARTS.md` adds the vehicle's real part count:
**42** — the 40 graph parts plus `hood_signature` (25) and `missile_base_signature` (41), read from
`DeformPoints`, 40/40 agreeing.

## 4. Geometry payloads (`GEOMETRY.md`, G2-5)

`jc3geom.py` reads the blocks, not just the headers:

| item | value |
|---|---|
| entities | **233** |
| meshes | **56,136** |
| mesh blocks | **77,611** — **77,611 decoded, 0 framed, 0 failed** |
| vertices / triangles | **20,818,841 / 19,214,751** |
| material slots | **806,529** |

Nine decoders, each with its own oracle. `CarPaintMM` / `Window` / `CarLight` use the published
layouts and are checked by byte-exact re-encode. Beyond `GeneralMkIII` (pinned below):

* **`General`** — u8 version 6, a 68-byte `Attributes` carrying its own AABB, texture table, then
  `{s16 x, y, z, pad}` positions scaled by `Attributes.f0 / 32768`, a 20-byte second stream and the
  indices. Every vertex of every block must land inside that AABB (78/78).
* **`GeneralJC3`** — the GeneralMkIII buffer pattern (packed s16 normals, 20-byte stream, indices);
  the scale is the float 32 bytes before the texture table, and containment is checked against the
  mesh AABB (35/35).
* **`BavariumShield`** — 28-byte vertices, a float position first (49/49).
* **`WaterDisplacementOverride` / `0x90FE086C`** — no texture table; 12-byte float positions
  (211/211).
* **`Prop`** — u8 version 3, the GeneralJC3 pattern with the same scale slot. Its stored scale is
  bit-identical to the mesh AABB's Y extent, the s16 Y run the full 0..32767, and the X/Y/Z spans
  agree with the AABB to 6.5e-5 (1/1).

All nine check structural exactness too: the buffer counts and the terminal index buffer must end on
that block's `0x89ABCDEF`.

**`GeneralMkIII`** was the hard one and it is now pinned, not fitted:

* the header is `u8 version=5`, `Attributes` (0x68 — which ends in **the block's own AABB** at
  `+0x4C`/`+0x58` and `pristine_index_count` at `+0x64`), `MaterialConsts2` (70 floats), then the
  texture table;
* the position buffer is `u32 count` followed by `{s16 x, s16 y, s16 z, s16 32767}` records — but the
  record is **8 or 16 bytes**: on meshes whose vertex format interleaves a second 8-byte attribute the
  sentinel sits every 16. The sentinel is the test, so the stride is detected, not assumed;
* one scale per block: `span(AABB) / span(s16)` agrees across the non-degenerate axes to **0.29%**
  worst case (threshold 1%, reported per block as `scale_error`).

The mesh **header** AABB is the wrong oracle — it is the union over all blocks — and using it is what
produced the earlier 5% errors and 253 refusals.

## 5. Collision (`PHYSICS.md`, `SHAPES.md`, `WIRING.md`, G2-8)

**Wheel stations are a normal decode, not a heuristic.** `land_global.vmodc` carries
`base_wheel_hardpoint_positions[0..3]` for every wheeled vehicle; the Serpente's four quads are
`(±0.885, 0.4, −1.557 / +1.446)` → track **1.77 m**, wheelbase **3.003 m**.

`.physicsc` holds a *second copy* of the same quads in **17** bundles (five vehicle families), and
`jc3phys.py` reads them structurally: four `float4 (x, y, z, 1.0)` sharing one `y`, one `|x|` with
both signs, two `z` with both signs. Every one of those 17 agrees with its `land_global` to the last
digit, which is what proves the reading: `PHYSICS.md`.

`SHAPES.md` covers the packfiles: **233 entities, 234 files, 18,865 convex hulls, 4,791 collision
meshes, 9,582 `hkGeometry`**, every hull block summing to its extent and every plane the supporting
plane of its vertex set.

**Compound instance records (the last G2-8 gap) are decoded.** A compound's `hkArray` at `+0x60` holds
128-byte `hknpShapeInstance` records: a 3×3 basis (three `float4` rows, `w` carrying a per-row norm
marker), the translation at `+0x30`, a scale at `+0x40`, and the child shape at `+0x50`. Placement is
`p' = Mᵀp + t` — the reading under which rotated children land inside their compound's own AABB and
the transpose does not. The array is inline at `+0xD0` on the static class and a separate allocation
on the dynamic one.

`WIRING.md` is the result: **6,382 compounds / 35,499 instances**, **25,769 carrying a
`CPfxPartIndexProperty` part index**, **25,769 resolved to a part name** by joining
`PARTS_TABLE.jsonl`. That turns "18,865 hulls somewhere in the file" into a per-part collision layout.

## 6. Effects, cameras, trim (`FX.md`, G2-9)

The last untouched payload family is not a format of its own: every `.effc`, `.ctunec` and `.trim` is
ADF v4 (`' FDA'`), the same container the `.vmodc` modules use.

| item | value |
|---|---|
| files | **57,187** (`.effc` 25,025 · `.ctunec` 6,455 · `.trim` 25,707) |
| standalone archive entries | 104 (the rest are inside `.ee` bundles) |
| value rows | **62,504,473** |
| root classes | `EffectRTSystem`, `EffectTrimData`, 20+ camera tune classes |
| failures | **0** |

`jc3adf.py` grew the four type kinds the vehicle modules never exercise: pointer (code 2),
`String` (`0x8955583E`, a data-relative offset to a NUL-terminated string), StringHash (code 9) and
inline arrays of primitives (`IA[float]`, 29 `int32` in one member). `jc3fx.py check` re-reads every
file out of the archives and compares its **row digest and object census**, so a decode that stopped
early cannot pass.

## 7. Derived tables

`FLEET.md` is per land vehicle: body L×W×H, wheelbase, track, hub height, tyre radius, mass, top
speed, steering time — 145 vehicles with stations, 144 scored. Batmobile targets (length 7.026,
wheelbase 5.029, track 2.416, tyre radius 0.6826) rank them by RMS relative error.

**The headline:** the current donor, the Serpente, ranks **45th of 144** by shape. The nearest shapes
are the **Urga armored transport** (`v0602`, 6.17 × 2.53 × 2.67 m, wheelbase 4.211, track 2.116,
tyre Ø 1.20, 6,000 kg, score 0.134) and the **Capstone medium/bavarium tank** (`v0201`/`v0202`,
8.19 × 4.67 × 2.34, wheelbase 4.534, track 3.054, Ø 1.32, 25,000 kg, 0.164), then the articulated
truck (6.45 × 2.70 × 3.66, 0.182) and the old truck (6.94 × 2.24 × 2.61, 0.197). The Serpente scores
0.358.

Context for that ranking: our built Batmobile is **mass 4,000 kg, wheelbase 5.029, track 2.416,
tyre radius 0.6826, body 3.504 × 2.283 × 7.027** — a heavy, long, wide vehicle currently carried on a
975 kg supercar's chassis. The ranking says which shipped vehicle is the *least wrong* starting point;
it does not say a tank drives like the Batmobile.

## 8. Known gaps (all read-side, none blocking)

| item | why it matters |
|---|---|
| `.rbm` non-position streams | positions, indices and materials are decoded; the second/third vertex streams (normals, UVs) are framed with their stride but not dequantized |
| quantized mesh vertices | `hknpExternMeshShapeData` stores `3 × u16` per vertex; counts and AABBs are exact, positions are not dequantized |
| face table semantics | `hknpConvexPolytopeShape`'s 4-byte face records read plausibly as `u16 first, u8 count, u8 min`; only the index block is validated |
| body → shape wiring | the 80-byte body entries and 64-byte motion entries are counted and sized but their fields are not pinned; the compound instances carry the shape → part wiring, which is what the mod needed |
| writing | nothing here writes a `.physicsc` or a `.rbm` — reading only |

## 9. Files

| path | content |
|---|---|
| `INDEX.jsonl` (17 MB) | one row per named archive entry: path, hash, archive, mount, offset, size |
| `INDEX.json` | counts, per-archive coverage, unnamed-entry magic census, name sources |
| `VOCABULARY.md` (115 KB) | 52 module types × 1,421 member paths, fleet range + donor value |
| `ENTITIES.md` | class inventory, part counts, lights (incl. donor's 22), mesh stats |
| `PHYSICS.md` | station quads read out of the Havok files, and their agreement with `land_global` |
| `FLEET.md` | per-vehicle geometry/handling and the donor ranking |
| `SHAPES.md` | collision shapes (`G2-8`): packfile envelope, hull blob, plane convention, compound instances |
| `WIRING.md` / `WIRING.jsonl` (3 MB) | **6,382 compounds / 35,499 instances** — child shape, placement, part index and part name |
| `PARTS.md` | the parts module (`G2-7`): ADF v4 layout, why the converter failed, validation, limits |
| `PARTS_TABLE.jsonl` (2.6 MB) | **233 vehicles / 11,643 parts** — part index, name, damage type, behavior, model, collision body, light flag, children, wheel slots |
| `PARTS_TABLE.md` | generated summary: damage-type distribution, parts per vehicle, the donor's 42 rows |
| `GEOMETRY.md` / `GEOMETRY.jsonl` | **56,136 meshes** — decode status, counts, materials, payload offsets |
| `FX.md` / `FX_VOCAB.json` | **57,187 files / 62.5M rows** — per-extension roots, member vocabulary, ranges |
| `FX_TABLE.jsonl` (22 MB) | one row per effect/camera/trim file: container, source archive path, path, size, root class, row count, array census digest, row digest |
| `E:\Modding\_JC3grab\entities\*.json` | raw module decodes, 233 files / 266 MB — **outside the repo** |
| `E:\Modding\_JC3grab\detail\*.json` | raw `.epe` graphs + `.rbm` headers, 233 files / 48 MB |
| `E:\Modding\_JC3grab\geom\*.json + .bin` | **440 MB** of decoded positions (float32 ×3) and indices (u16), one pair per entity |
| `E:\Modding\_JC3grab\phys\*.json` | raw station extraction, 233 files |
| `E:\Modding\_JC3grab\hkx\out\*.json` | decoded packfiles, 233 files / 141 MB: every hull vertex, plane and index, mesh AABBs, geometries — **outside the repo** |

Game bytes never enter the repo; only derived tables and paths do.
