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
python Tools/scripts/jc3weapons.py --write     # 25 ids -> WEAPONS.jsonl + WEAPONS.md      (G2-10)
python Tools/scripts/jc3weapons.py --check
python Tools/scripts/jc3weapons.py dump <id>   # one weapon's sources and members
python Tools/scripts/jc3wiring.py --write      # 53 armed entities -> WEAPON_WIRING.*      (G2-11)
python Tools/scripts/jc3wiring.py --check
python Tools/scripts/jc3wiring.py dump <substr>  # one entity's slots, weapons and seats
python Tools/scripts/jc3sigdiff.py --write     # civilian vs armed Serpente -> SIGNATURE_DIFF.* (G2-12)
python Tools/scripts/jc3sigdiff.py --check
python Tools/scripts/jc3sigdiff.py dump weapon # one section (members, graph, weapon, parts, meshes, tunes, toc)
python Tools/scripts/jc3turret.py --write     # 8 vehicles -> TURRET.md + TURRET.json        (G2-13)
python Tools/scripts/jc3turret.py --check
python Tools/scripts/jc3turret.py dump samples|census|tune
python Tools/scripts/jc3moving.py --write     # 67 behaviours -> MOVING_PARTS.md + .json    (G2-14)
python Tools/scripts/jc3moving.py --check
python Tools/scripts/jc3moving.py dump tables|behaviours|arrays
python Tools/scripts/jc3doors.py --write      # doors/hatches + entry paths -> DOORS.md       (G2-15)
python Tools/scripts/jc3doors.py --check
python Tools/scripts/jc3doors.py dump samples|census|interactions
python Tools/scripts/g2x_gate.py   --write      # G2 exit gate -> G2X.md + G2X.json         (G2X)
python Tools/scripts/g2x_gate.py   --check      # re-runs every G2 reader + every §1 feature row
```

## 1. The index (`INDEX.jsonl`)

| item | count |
|---|---|
| `.tab`/`.arc` pairs scanned | **88** (56 base, 7 patch, 25 DLC under `dlc_win64/*/`) |
| archive entries | **81,953** |
| entries named | **81,952 = 99.999%** |
| base / patch / DLC | 47,557 / 47,557 · 13,713 / 13,714 · 20,682 / 20,682 |
| DLC entries | **20,682 / 20,682** named |
| unnamed entries | **1**, a `.wavc` orphan, censused by magic byte in `INDEX.json` |

Two name sources, both hashed through the same Jenkins lookup3: Gibbed's filelists (**55,811** rows)
and JCMR's shipped `assets/jc3/dictionary.json` (**26,051** rows, which is what closes the DLC),
plus a generated list in `Tools/names/` (**90** rows, every one accepted because its hash is a real
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

One more came from the **FSB5 name table**. `.wavc` payloads are a 16-byte prefix plus an FMOD
**FSB5** bank; the name table holds one **language-invariant** token per take. The Japanese
(`BEA6350C`, `game64`) and English (`82088DE4`, `game56`) copies of
`mission_mm110_dial_defendtheplane_090.wavc` both carry token `a1630394639` — and so does the
unnamed `archives_win64/game67` `966DB7BC`. The basename is therefore known, and hashing
`sound/dialogue/<lang>/` + basename against `966DB7BC` hits exactly one directory: `pol`, a
1-entry Polish language shard (`game67` sits beside `game64`'s Japanese copy for the same reason).
This is how the token becomes a name: a sibling language already named the take.

The final `.wavc` (`patch_win64/game4` `016DE9D1`) resists the same trick: its token `1606523576`
maps to **no** named file in any language — a unique orphan, so there is no sibling to borrow a
basename from. Write order brackets it at `sound/dialogue/ara/mission_mm320_dial_gameplay_090.wavc`
< it < `…_gameplay_start05.wavc`, but no numeric take (0…9999, widths 1…4), known basename across
all 40 dialogue directories, or English `mm320` take hashes to it, and the token is FMOD's opaque
"original source file name" — not a hash of the basename — so it cannot be inverted without the
original FMOD project.

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

### Writing a `.physicsc` (`PHYSICS_WRITE.md`, G2-30)

The reader was half the job; `jc3hkx.py write` adds the other half. The donor's data section is
**fully partitioned by typed objects** - 430 objects contiguous from 0 to the local-fixup table, no
gap, every extent a multiple of 16 - so the section can be laid out again from per-object blobs with
every local / global / virtual fixup remapped and the `__data__` record regenerated. That is what
makes a size change possible; in-place patching would stop at "same vertex count".

Four cases, on the donor and on its assembly variant (the written blobs live outside the repo in
`_JC3grab/hkx/write/`, R10):

| case | result |
|---|---|
| round trip: all **54 hulls** re-emitted from their decoded vertices / planes / radius | **byte-identical**, 340,368 B, both files |
| remap stress: 16 filler bytes at data offset 0, so all 430 objects and the three tables move | re-reads with **0 violations**, decoded graph identical, 340,384 B |
| one hull scaled ×1.6596 (Batmobile tyre 1.365 m / hull 0.8225 m) | **0 violations**; 252 B over 69 runs; 2 parent compound AABBs moved |
| the `wheel_f_l` slot holding the `body` hull block (704 -> 1,776 B) | **0 violations**, 340,368 -> 341,440 B, object count still 430 |

Two rules the spike had to learn from the data, both in the tool: the **pointer slots stay zero**
(the loader writes the target from the fixup table - writing it there made a "correct" file differ
from the original in 2,702 bytes), and a **grown child leaves its parent's AABB stale**
(`a child AABB is outside the compound AABB`), so the writer moves the ancestors by exactly as much
as the children moved and keeps the margin the file authored.

What stays out of reach is in the report: the hull's **face table** has 0-32 bytes of an unnamed
block before it, so a **brand-new** hull cannot be authored yet, and an `hknpExternMeshShape`
cannot be re-authored at all (quantized vertices, frame unpinned).

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

### Weapon catalogue (`WEAPONS.md`, G2-10)

25 `06_vehicle` weapon ids (22 archive ids + 3 `+_impact` blast ids), decoded from their `.wtunec` /
`.ftunec` members: velocity, range, fire rate, magazine, damage, blast radius and impulse. Every id
has a row; `jc3weapons.py --check` re-reads and compares. The catalogue also found that blasts are
`.ftunec` members inside the weapon's `.ee` (there is no `jc_explosions/` tree), that no weapon has
an overheat member, and that damage type lives on the part/health side, not the weapon.

### Weapon wiring (`WEAPON_WIRING.md`, G2-11)

**53 armed entities over 21 chassis**, 88 weapon components (57 bullet, 25 missile, 6 RPG fire
leach), 62 driver slots and 19 gunner slots. The entity graph has no `weapon_slot` field: the root
class carries four object pointers - `main_weapon` (`id:851CAABE`, name recovered by Jenkins hash),
a second driver pointer (`id:00568A74`, name not in any shipped name table), `mounted_weapon` and
`mounted_weapon_2` (`id:AC0BC788`) - and a component no pointer names is inert (the fighter jet
ships one). Max driver weapons is 2 (medium/Bavarium tank, plus aircraft pairs); no entity binds a
third. All 19 gunner weapons name their mount parts through a type-4 `SWeaponPoint`, as does the
corvette's driver cannon; the other 59 driver weapons name none.
The mounted M2 `w206_mounted_capstone_m2hm` (19 components / 5 chassis) lives in `04_mounted`, so it
is outside G2-10's `06_vehicle` catalogue; its tune is in `WEAPONS_SHARED.json`. `--check` re-reads
all 53 `.epe`s, compares every row, and cross-checks weapon names and point counts against
`FEATURE_CENSUS.json`.

### The armed Serpente, civilian → signature (`SIGNATURE_DIFF.md`, G2-12)

The signature Serpente is the only armed entity in the fleet that carries a `w618` pod, and JC3
builds it from the same chassis as the civilian car. Diffing the two `.ee`s separates the *wiring* from the *art*: the
container grows by 35 members (566 → 601, +167/−132, 108 of them a `signature/` path replacing its
base twin), the graph by 14 objects (450 → 464; only 2 objects change, 4 subtrees are added and 1
removed), and the parts modules are **identical part-for-part** — 42 definitions at the same
indices, with 19 part models (and 4 wheel `model_swap` links) restyled to `signature/`. The `epe`
instantiates 40 of them in the civilian (no `hood_signature`/`missile_base`) and 41 in the
signature (no plain `hood`), so the "new parts" are selectable branches, not a new module.

All 84 paired `.rbm`s keep their block count and AABB (only byte sizes move, −141…+44), so the kit
is the same shell recompiled against the signature textures; the five genuinely new meshes are the
RPG fire-leach projectile's LODs, because **the missile is the stock RPG projectile**. The weapon
subtree is 11 objects: one `CMissileWeaponBase` on `main_weapon`, four type-2
`internal.fire_point.N` tubes at y 1.085 / z −1.566, four `SAttachedEffect` muzzles at those same
positions (all one `sportsmuscle_missile_muzzleflash.effc`), one `CAimPOIWeaponComponent`, one
`CForcePulse` and one `CMaterialEffectTable`. The tune is unguided (turning 0), unlimited
(`magazine_size` −1), 1500 damage at 300 m, blast 1100 player + 500 AI in 8 m.

`--check` re-reads both containers, converts both `.epe`s again, rebuilds every section and compares
the json field-for-field and the md byte-for-byte; it also asserts the four-point/muzzle pairing,
the 40/41 instantiation, the 84/84 mesh AABBs and that every restyled model is a `signature/` path.

## 8. Known gaps (all read-side, none blocking)

| item | why it matters |
|---|---|
| `.rbm` non-position streams | positions, indices and materials are decoded; the second/third vertex streams (normals, UVs) are framed with their stride but not dequantized |
| quantized mesh vertices | `hknpExternMeshShapeData` stores `3 × u16` per vertex; counts and AABBs are exact, positions are not dequantized |
| face table semantics | `hknpConvexPolytopeShape`'s 4-byte face records read plausibly as `u16 first, u8 count, u8 min`; only the index block is validated |
| body → shape wiring | the 80-byte body entries and 64-byte motion entries are counted and sized but their fields are not pinned; the compound instances carry the shape → part wiring, which is what the mod needed |
| writing | nothing here writes a `.physicsc` or a `.rbm` — reading only |

### Turrets and cannons (`TURRET.md`, G2-13)

A JC3 turret is not an object: it is a `Turret` part (yaw) and a `Cannon` part (pitch), each on one
`hkpLimitedHingeConstraintData` in the vehicle's `.physicsc`, selected by that part's
`constraint_index`. The medium tank is the reference - `mediumtank_turret` (index 26, parent 0) on
constraint 2 at (0, 2.2812, 1.1382) about +Y, **-179 .. +179 deg**, and `mediumtank_cannon`
(index 38, parent 26) on constraint 0 at (0, 2.5347, 0) about +X, **-5 .. +20 deg**;
`w602_mediumtank_canon.fire_position_0` names both parts in `id:80201E4D` (yaw) and
`id:5C19E7E0` (pitch). The Bavarium tank reuses both hinges unchanged. The wheeled mounts differ
only in numbers: APC turret ±179 at (-0.0037, 2.1367, 1.3048) with a -15..50 vertical, armoured
jeep ±179 / -25..50, technical ±179 / -10..45; the small tank pitches -5..25 and its deck rack
hangs on a ragdoll, not a hinge.

The parts module's `aim_part_constraints` is **not** turret aim: 85 rows live in 17 of 78 cached
modules and every one is suspension - a Y-bar, axle or spring source aiming at a brake drum, disc,
caliper or wheel - with **0** rows on all six turreted vehicles. `hinged_parts[]` and
`rotating_parts[]` are empty on the tanks as well (28 and 22 of 78 modules use them), so the hinge
exists only in `.physicsc`.

Aim is a tune, not a ray. Every entity's `STargetPoint` is at (0, 1, 0) with `min_aim_distance` -1,
and the tank cannon's `autoaim_vehicle_mgun` takes candidates at 5-70 m, 0.03 rad to acquire and
0.05 rad to hold, 6/16 deg sticky at strength 0.4, `CanTargetCharacters` 1 but
`CanTargetVehicles` 0. Fleet-wide, 92 fire points on 52 weapons name a yaw or pitch part: 47/47
pitch parts are `Cannon`, the 75 yaw parts are 18 `Turret`, 13 `Cannon` and 44 plain parts on
aircraft pods, and two entries on the cargo plane name the carried tank's parts.

`--check` re-reads the eight entities' parts modules and `.physicsc`s and rebuilds both files:
`PASS: 8 samples, 92 points on 52 weapons, 85 aim-constraint rows, 3 mediumtank constraints`.

### Moving parts (`MOVING_PARTS.md`, G2-14)

`vehicle_common.vmodc` - read from the Serpente civilian's container, the only copy in the fleet -
keys behaviour names to five tables. `all_hinged_part_properties` (25 rows) names a
`target_position_variable` (`steering_roll`, `flaps_T`, `landing_gears_T`...), a `lod` flag and
`use_target_position_as_angle`, which only `SteeringFork` sets; `all_rotating_part_properties` (12)
names an `rpm_variable` plus rotoscope flags and a 20-rpm/cycle disc rate. Doors (14), the fin
(`BoatRudder`) and the spring (`Spring`) are **name-only** rows, so a door's travel comes from its
Havok hinge, not from a speed here. 15 declared names have no user at all (the 12 spider-leg parts,
both elevons, `BoatRudder`); 29 behaviours in use have no row (turret/cannon, wheels, brakes,
windows); and 30 have no `CCar` user - `AirBrake` is 3 parts on one `CAirPlane`, the card's probe.

The per-part arrays are mostly indices: `door_parts[]` (224 rows in 56 modules) and `hinged_parts[]`
(148 in 28) store only `part_index`, which is why G2-13 found the tanks' hinges in `.physicsc`;
`rotating_parts[]` (47 in 22) is the only one with geometry - position, rotation axis, blade count,
rpm multiplier and visibility range.

`--check` rebuilds both files:
`PASS: 67 behaviours, 53 table rows (37 proven on CCar), 224 door rows`.

### Doors, canopies and missile hatches (`DOORS.md`, G2-15)

A door is three pieces: a behaviour name from `all_door_part_properties`, a bare `part_index` in
`door_parts[]`, and a limited hinge in `.physicsc`. No angle, speed or animation lives on the part.
Census of 224 door rows in 56 modules (220 hinged): 60 hinge about **X** (hoods, roof hatches,
canopies), 132 about **Y** (side doors), 28 about **Z** (the monorail bay covers); 4 rows have no
hinge at all. A forward-tilting canopy is therefore an ordinary `Hood`/`FrontLeftDoor` part on an
X-axis hinge - `mediumtank_hatch` 0..130 deg, `sportsmuscle_hood_signature` 0..70 deg.

The monorail car's 16 `MissileHatch` covers are 0..150 deg about ±Z; nothing outside `CPartProp`
names them, no interaction opens them, and its only weapon (`w614`, `CMissileWeaponBase`) fires from
`InternalFirePosition_0…5` *inside* the bay, so the trigger is code-side. Entry has two paths and
the states spell them out: `entry.driver` -> `S_ENTER_DRIVER_VEHICLE` against
`entry.driver.no.door` -> `S_ENTER_DRIVER_NO_DOOR_VEHICLE`; 21 of 55 cached graphs carry both, 4
only the no-door path and 30 neither. The donor is in the `both` group, but its container has 0
animation files, so the file proves the branch, not the swing.

`--check` → `PASS: 4 samples, 224 door rows / 220 hinged / X 60, both entry paths 21`.

### The EMP truck (`EMP.md`, G2-16)

The truck's EMP is **not a weapon**: a `CForcePulse` named `EMP` on the flatbed at (0, 2.0356,
0.6992), its own `truck_emp.ftunec` (100 damage in 25 m, held at full through the radius - against
500 in 5 m for the stock car blast), an `emp_flatbed_table` mapping every material to the embedded
`explosion_emp_flatbed.effc`, three device parts (the core is a `Rotor`: 6 blades, +Z,
`rpm_multiplier` 1.0), and `trigger.use_item` + `entry.use_item` -> `S_STUNT_USE_ITEM_VEHICLE` with
the prompt `ui_activate_emp`. No weapon component is on the vehicle and **no object references the
pulse** - the trigger and the pulse share the entity, and the wiring between them is code. Duration
and the disable effect are in no member: besides the radius, three unnamed boolean flags and the
effect table are all that separate it from a normal explosion pulse. The mm250 mission build drops
the pulse and its tune and adds the `epe_emp_powering_up` charging emitter (`emp_active.effc`).

The three device parts are compiled into **all 9 oldtruck variants**, but only the two EMP builds
carry the `CPartProp`s, the pulse and the trigger. The engine does have `CEMPWeapon` (`w702_emp`
handheld, `w503_turret_emp` static turret), whose tunes carry **no EMP field at all** - damage 500,
range 50 / 750 m, charging sounds on the handheld - so the effect is keyed off the class in code,
and none of the fleet's 88 vehicle weapon components is one. Card answer: the effect can be put on
another vehicle as entity objects (copy list in the doc), not as a weapon-slot copy.

`--check` → `PASS: 2 builds, 9 variants, 3 device parts, 2 EMP weapons, fleet CEMPWeapon 0`.

### Turn-on-the-spot (`TANKTURN.md`, G2-21)

The four tracked chassis (`v0200` APC, `v0201` medium tank, `v0202` Bavarium tank,
`v0603` small tank) are ordinary `CCar` wheel builds. The card's four modules (`LandGlobal`,
`LandSteering`, `Transmission`, `CustomLandGlobal`) carry **byte-identical member sets** in tanks
and cars (48/15/40/61 members, 0 tank-only, 0 non-tank-only) and no module type is tank-only.
None of the card's candidates separates them: `number_of_wheels` 6/8/8/4 is shared by 114
non-tank builds, `wheels_friction_type=2` by 36, `is_rear_steered` is 0 on all 145 player copies,
the only `is_all_wheel_steered=1` builds are three monster trucks, and the five-value tuple is
shared by 27 non-tank builds. 262 tank-unique values exist fleet-wide, **0 in a driving module**
(all deform/effect/fin/propeller/water art data), and a token scan of every member path and of
`VOCABULARY.md` finds only cosmetic skid markers and the `CTrain` track gauge. So turn-on-the-spot
has no data carrier: MOD-2's turn-on-the-spot becomes a **named omission**; whether the shipped
tanks actually pivot and which native key decides it is `UNKNOWN` from these files (Q-1 probe).

`--check` → `PASS: 12 tank builds / 145 player land_global, 4 card modules identical (0 tank-only
/ 0 non-tank-only members), 0 tank-only module types, 5 candidates refuted (27 non-tank builds
share a tank tuple), 262 tank-unique values with 0 in driving modules, 9 name matches (0 script
file types), vehicle class {'CCar': 12}`.

### Every pulse in the fleet (`FORCEPULSE.md`, G2-17)

`CForcePulse` is the fleet's blast component: **307 pulses in all 232 vehicle `.ee` files**
(79 chassis), one class carrying **31 members** - 5 named (`SettingsFile`, `name`, `name_hash`,
`world`, `_object_id`) plus 26 Jenkins-hashed `id:*` keys whose names are in no shipped name
table. Every pulse is an explosion: its `SettingsFile` names one of **23 tunes**, 22 under
`jc_explosions/` and one bossfight prototype (`prototype_missile_explosion_sam`), each tuned by
`ForcePulseSettings` with eight numbers (`PlayerDamage` 0 … 3000, radius 1.5 … 50 m, `AIDamage`
0 … 1000 in 0 … 50 m). The card's horn and collision candidates are refuted by the data: 178
entities carry an `SAttachedEffect horn` but **no tune path and no pulse name mentions a horn or
a collision**, and every tune is a blast tune.

The trigger is a pointer: `id:B5AE7986` on the owner holds the pulse's `_object_id` for **293 of
307** pulses - the vehicle root (`CCar` 126, `CBoat` 35, `CHelicopter` 23, `CAirPlane` 18,
`CTrain` 12, `CMotorBike` 19) carrying that type's own explosion tune, or a weapon component
(`CBulletWeaponBase` 29, `CMissileWeaponBase` 25, `CRPGFireLeachWeapon` 6) carrying its own
`jc_explosions/weapons/<id>.ftune`. The **14 unowned** pulses are declared UNKNOWN, not
explained: the ten oldtruck barrel blasts nest under their `CRigidObject` and point out at a
`CEntityObject` (`id:73D4D940`) instead of being pointed at, the two loose-cargo blasts use a
0-damage push tune, the mm340 `BOMB_JEEP` pulse is held by a `CGraphScriptGameObject`
(`id:65424AC6` - the only pulse reference in the fleet that is neither the owner pointer nor the
pulse itself), and the EMP pulse has no pointer at all (G2-16). So the WPN-5/WPN-8 push
is a copied entity object with a chosen tune; the firing moment lives in native code (Q-1).

`--check` → `PASS: 307 pulses / 232 entities / 79 chassis, 31 members, 23 tunes, owners
{'(none)': 14, 'CAirPlane': 18, 'CBoat': 35, 'CBulletWeaponBase': 29, 'CCar': 126,
'CHelicopter': 23, 'CMissileWeaponBase': 25, 'CMotorBike': 19, 'CRPGFireLeachWeapon': 6,
'CTrain': 12}, unowned 14, horn tunes 0, collision tunes 0`.

### The vehicle-weapon HUD (`JC3_HUD_WEAPONS.md`, G2-25)

The JC3 vehicle HUD (the HUD half of WPN-12) comes out of the decompiled `ui/hud.gfx` as
`InitVehicleWeapons(slot_index, weapon_id, weapon_name, infiniteAmmo, magazine_ammo,
magazine_size, inventory_ammo, weapon_cooldown, is_overcharged)` - **9 arguments** - and
`UpdateVehicleWeapons(slot_index, new_magazine_ammo_amount, total_ammo, is_low_ammo,
weapon_cooldown, is_overcharged)` - **6**; the slot array is
`MCI_vehicle_weapons0/1`, so **2 slots**, and `weapon_cooldown` is a `0..1` fraction where `-1`
means "no loader" (do not confuse either with `E_NUM_WEAPON_SLOTS = 7`, the on-foot wheel).
**Neither function has a heat argument and neither body mentions heat**: JC3's movie "heat" is
the 11-state police wanted level, and the Batmobile's Vulcan heat bar is a weapon-entity script
variable (`HeatBarStart`/`HeatBarSize`) with no `UC_*` setter - so WPN-12's heat bar is a **stated
absence on both sides**, not a missing member. The lock-on is **one POI**
(`POI_TYPE_LOCK_ON_TARGET = 21`, a reticle that turns once every 1.5 s in `hud_code/poi.as`) plus
a separate incoming-missile warning (`MCI_missile_locked`, flashing at 0.5 s), where the Batmobile
has a six-kind target box family; `w609`/`w612`/`w613`'s lock-on is an `AutoAim` tune, and the
link from that tune to POI 21 is in no file (UNKNOWN, native). Weapon id -> icon is
`textures/ui/weapon_icons/<weapon_id>.ddsc`; 22 of the fleet's 23 wired weapon ids have one -
`614` (the monorail's missile) does not. Caller census: the only in-movie call sites are the two
demo calls in `TestConstructor`, so the entity -> HUD bridge stays UNKNOWN.

`--check` → `PASS: 260 scripts, InitVehicleWeapons 9 args / UpdateVehicleWeapons 6 args, 2
vehicle slots (E_NUM_WEAPON_SLOTS 7 is on-foot), 14 reticle shapes, lock-on POI 21 at 1.5 s, 0
heat parameters, 0 heat in bodies, 0 BmAK heat setters, 69 weapon icons, 5 WPN-12 rows
(map/map/map/stated absence/partial)`.

### Rebel Drop (`REBELDROP.md`, G2-26)

A drop entry is one `Item` in `profile/item.onlinec`, and **its `Name` is the 32-bit
Jenkins hash of an entity leaf name** — that hash is the whole spawn binding (there is no
path field, and no price field: the only time value is `RebelDropTimer`). `Name` resolves to
an `.ee` for 185 of the 196 vanilla items (the 11 that do not carry `UIType` 0 and an
empty or `placeholder` image path; what they are is UNKNOWN) and for 229/240 items of the
mod's newest variant; the 80 vanilla vehicle drops all satisfy
`Name == hash(UIImagePath)`, `UIName == Name` and `Type` 1 / `UIType` 3.

The unlock lives in `profile/task.onlinec`: 87 `ItemReward` links (`Item` hash +
`Permanent`/`Quantity`/`Delivery`) hand items out from task rewards, e.g. the donor
drop from task `1361701860` (type 19, permanent, delivery 0).

Reader facts `--check` re-derives: the **base game's** `item.onlinec` declares its own
`Item` of **25** members (`Type` at 8, no `DlcId`, root `0x79DE48AE`), the patch layer
declares **26** (`DlcId` at 8, `Type` at 12, root `0x921AF417`), and the mod's tables have
no type table but carry the base root, so each file is read with the layout it declares.
Read that way the base and patch agree on all 25 shared members for 196/196 items and
`DlcId` is 0 on every record - the patch adds the member, not a value. The 128 B stride is
proved by the `UIImagePath` string pointers (196/196 base, 196/196 patch, 232/232 and
240/240 mod). Against the base layer the mod adds 39/45/45 items (`Type` 1, `UIType` 3,
timer 0, `BaseName` = `Name`, `placeholder` icon) and rewrites 160/162/162 items (timer,
order, icon, flags) — no task reward for any added item, and the task file is only
reordered. Which member list a type-table-less table is loaded with is UNKNOWN.

`--check` → `PASS: 196 vanilla items / 591 tasks / 80 vehicle-bound / 185 resolved to .ee, 0
hash mismatches, 39+45+45 items added by the 3 mod variants, recipe hash 443190071 for
v0300_car_kensington_sportsmuscle_batmobile`.

### Effect usage vocabulary (`USAGES.md`, G2-22)

The fleet's usage vocabulary is **12 names** - 346 `usage_effects[]` rows / 885 effect links
across 225 `EffectAttachments` modules on 224 vehicles. `ExtendedEffectUsages` is a shared
627-byte stub with **`usages[]` empty on all 232 vehicles**, so the vocabulary lives only in
`EffectAttachments` and in the `.epe` graphs. The twelve, by module count: `HeadLights` 145,
`EngineRunning` 69, `OnPartExplode` 33, `EngineSmoking` 23, `Explosion` 23, `EngineNitro` 18,
`EngineTurboJump` 11, `OnPartReachedDamageState` 3, `Siren` 3, `OnPartBrokeOn` 2, `OnExploded` 2,
and one **empty-string usage whose hash is `0xDEADBEEF`** (14 modules).

Nitro: usage `EngineNitro` (4197885156) binds to the effects `dynamic_nitrous` (14 vehicles) and
`EngineNitro` (4, the planes); the same `Usage` int sits on **307 objects in 202 of 232 `.epe`
graphs** - the `exhaust_upgrade_nitrous*` emitters, the `dynamic_exhaust_nitrous`
`SDynamicAttachedEffect` and the `engine_nitrous_sound` / `nitrous_active_sound` sounds. **No
usage is named afterburner, boost or flame**; the flame is carried by effect names and by the 9
`*nitrous*.effc` paths (275 containers). The donor attaches `exhaust_upgrade_nitrous` and
`exhaust_upgrade_nitrous2` under `Usage` = `EngineNitro` in its `.epe` although its module row
lists only `HeadLights` - reading only the module would have been a false negative.

Unknown: the `.epe` `Usage` int (155 distinct values / 12,576 objects) is named for only 70 of
them (6 from the usage vocabulary, 60 from an effect that shares the hash, 4 from
`SValueDrivenEffectUsage`); **85 have no name in any decoded file**, and **0 of 849,942 `.epe`
strings** name an `.effc`/`.ctunec`/`.trim`, so effect name -> effect file stays a native lookup.

`--check` → `PASS: 6045 modules in 232 caches, 225 EffectAttachments on 224 vehicles, 12 named
usages (346 rows, 885 effect links re-decoded), ExtendedEffectUsages 0 usages, EngineNitro ->
EngineNitro/dynamic_nitrous, 155 .epe Usage values / 12576 objects, 0 .effc refs in graphs, FX
rows 57187`.

**The nitro chain (G2-23, `USAGES.md` §6).** Input → effect → sound event → sample is complete on
the file side. Input: `CustomLandGlobal`'s `arcade.nitro_boost` block (torque x2, grip x2, 15,000 N
push, 0.2 s blend, +40 km/h; `_upgraded` 20,000 N / +80 km/h), present on **145 of 232** vehicles
together with `heat_boost`, `turbo_jump` and their `_upgraded` twins. Effect: the donor's
`exhaust_upgrade_nitrous` carries `Usage` `EngineNitro` (4197885156) and an object `Effect` hash
`3518298851` carried by **28 objects on 17 vehicles**, all `*nitrous*`; the module space instead
names `397752766` `dynamic_nitrous` for that usage, and the object's own hash is in no module
`all_effects[]` - so object hash → `.effc` is UNKNOWN. Sound: the object's `Sound` GUID
`f74ea43b-a8ac-4548-ad27-b92fd40a516d` is carried by **202 objects on 172 vehicles** (154 of them
`exhaust_upgrade_nitrous`), is 1 of the donor's 45 `fmod_guids`, and resolves to `vehicles.bank`
`EVTS` ordinal **249** (195 B). Samples are picked **by name** - `vehicles.bank` links no event to
a sample index (`JC3_AUDIO.md` §5): 56 `jc3_veh_land_premium_nitro_start`, 150 `..._nitro_loop`,
355 `..._nitro_stop`, exactly the three 0-based indices test-060's `_apply_audio.py` swapped
(`--check` compares the two sets). Which control fires nitro is in no decoded file (UNKNOWN).

### The light system (`LIGHT_SYSTEM.md`, G2-33)

A light is one entry in the vehicle's `VehicleDynamicLights` module: **3,217 entries over 223
vehicles**, **25 members** each, naming the part it hangs on (`part`, `part_index`) and the node
chain it anchors to (`deformable_transform`) and carrying all of its own numbers. The `.epe`
side is a *different* list - **3,972** named `SVehicleLight` objects (404 preset names, no part
binding, `preset_id` as a string) - and no file joins the two, so the module is the side to
build against. `has_lights` is a per-part flag in the parts module (2,073 of 11,643 parts), not
a gate: 6 entries sit on unlit parts and 13 lit parts carry no entry; entries outnumber lit
parts because one part hosts several lamps.

Presets do not decide the numbers: **393 preset ids** are in use, **17 shipped entries carry
`preset_id = 0`**, and **34 presets appear with different value tuples** on different vehicles,
so an entry is fully described by its own members. The `CarLight` block is uniform across the
fleet - **11,367 blocks, every one stride 12 B, uint16 indices, exactly 6 material slots** - and
its *parameter* bytes stay undecoded (MODLOG §102d): copy the block, never author it.

The wheel-arch recipe (`LWheelLight`, `Playable_Batmobile_SF`) has a source and a class for all
25 members; the hashes are `rbmhdr.hash_jenkins`, which the check proves against all 3,217
shipped `part_hash` / `behavior_hash` / `deformable_transform_hash` values. What it cannot fix:
the wheel part ships `has_lights = 0` with no `CarLight` block, and the anchor node is the §112
probe.

`--check` → `PASS: 3,217 light entries / 223 vehicles, 25 members, 9 behaviours, 393 presets (17
use 0, 34 inconsistent), hashes 3217/3217/3217 recomputed; binding 2,073 lit parts, 27 name
misses, 6 on unlit parts; CarLight 11,367 blocks stride ['12'] slots ['6']; recipe 25 members`.

### Traffic and spawning (`TRAFFIC.md`, G2-29)

`v0300_car_kensington_sportsmuscle_civilian_01` **is a civilian traffic vehicle**: it has a
record in the ground-vehicle spawn table `settings/spawn_vehicle_defs.bin` (86 records) whose
tag list `vehicle,ground,car,civilian,racing,modern,muscle,kensington,sports,unarmed,unarmored,
ambient,liberated` satisfies exactly **1 of the 41 tag selectors** in the traffic-rule block of
`global/global.blo` — `ambient,ground,car,liberated,-highend`, the civilian-car rule
`03_CivilianCarLiberatedProvince` — whose driver seats are bound to `ai/bts/...` behaviour trees
(10 of them in the file). So replacing `civilian_01` puts **NPC-driven Batmobiles** on the roads
in liberated provinces: a lore break (MOD-5, WLD-8) that points D-6 at the standalone route.

Only `civilian_01` is in that table; the `debug` build sits in `spawn_vehicle_proto_defs.bin`
and the `signature_preorder` build in the DLC's own table. The donor's spawn record carries **no
pool key** (only 8 of 86 records carry one, each a different key, so the key is not a group
label and the donor's pool is `UNKNOWN`). The other spawn sites are one Rebel Drop item
(`profile/item.onlinec`, key `…_civilian_01_desc`), one chop-shop task key
(`chopshop_v0300_…_civilian_01`) and two level `CVehicleRule` logic objects; no shipped region
level places it. The tag *matcher* is native — no file states that a selector takes tag
supersets — so the match is the strongest read the files allow, not a runtime proof.

`--check` → `PASS: 11751 files scanned (7719 MB, A+B), 17 name the donor (Rebel Drop/entity
registry/frontend/level rule/localisation/other/patch metadata/self/spawn table/task table), 86
spawn records (8 with a pool key), donor tag list of 13 tags, 31 traffic rules / 41 selectors, 1
match (`ambient,ground,car,liberated,-highend`), 10 AI behaviour trees`.

### Standalone entity (`STANDALONE.md`, G2-27)

**A new entity path needs no global registry edit for the routes that name it by path.** The
registration census is 17 file rows in 10 kinds (G2-29's scan, re-read by key type): spawn
tables (9 files, the entity as a **full path string**), the Rebel Drop item (32-bit leaf hash),
the chop-shop task key, two level `CVehicleRule`s, `frontend_global.blo`, `profile/online.stringlookup`
(hash only), `patchmetadata.bin`, the entity's own `.epe`/`.toc`, and
`global/entityregistry_gen.entityregc`.

The registry is a tagged stream (`03 <len16> <leaf>` + the leaf's 32-bit hash + that entity's
asset paths), 33.0 MB base + 39.2 MB patch, holding **251 of 922** index entity leaves — the
**base retail roster** and not much else: `settings/spawn_vehicle_defs.bin` has 86 records and
all 86 are registered, while **163 of the 169** debug records (`spawn_vehicle_proto_defs.bin`,
base + patch) and **13 of the 21** DLC production records are not — and one of those DLC
vehicles (the sport mech) is playable in retail. So a missing record does not stop an entity
loading; what a spawn needs is the path string, and that is available for a new leaf. The only
**hash** reference is the drop item, and no shipped hash points at an unregistered leaf, so
whether a new leaf resolves is `UNKNOWN` → one Q-1 probe (new-path `.ee` + one item).

The shipped Rebel-Drop mod shows the packaging: **20** `.ee` overrides, **20/20 at vanilla
paths**, **0** `.toc` files (so a `.toc` is optional), and one of them (a *boat* path) contains a
playground prop's `.epe` — inner names are independent of the outer leaf. A standalone entity is
therefore one `.ee` (donor: 604 inner files, 10,737,057 B, its own `.epe`/`.stringlookup`/
`.fmod_guids`) plus one reference (spawn record or drop item), with a name/icon optional.

`--check` → `PASS: 17 registration rows | registry records 251/922 index leaves (158/233
vehicles) | 101 spawned-by-path leaves unregistered | mod 20 .ee / 0 .toc, 20 vanilla paths |
donor .ee 604 inner files, json match True, md match True`.

### Water behaviour (`WATER.md`, G2-31)

One scalar plus one module decides it: **`WaterInteraction.will_sink`** is `1` on **189 of the
232** vehicle entities and `0` on the other 43, and the 43 split by module - **35 boats** carry a
`BoatBuoyancy` module (`base_buoyancy` 0.1…1.45, 6–9 pontoon modules with `radius` /
`forward_drag` / `lateral_drag` / `vertical_drag` / `air_drag`), and **8 land/air vehicles**
(`v0200` APC, `v2603` sea scout, `v4500` floatplane) keep the plain car `Buoyancy` module and
simply do not sink. The donor is a sinker (`will_sink` 1, `buoyancy` 2, `drag` 100, one hull
element), so the build - the donor's own `.ee` - **sinks and stalls by default**, which is D-8's
lore route with no water edit at all; both of its water modules were decoded out of
`Builds/test-091` and match the donor member for member.

The kill/stall side is **fleet-wide, not per vehicle**: all 232 entities point `VehicleCommon` at
one shared `vehicle_common.vmodc` whose `vehicle_damage.min/fatal_water_entry_(floating_)ms` read
10/20 and 20/50, and whose five `*_engine_shut_down_delay_s` rows read 30 s (car) and 5 s (boat,
bike, helicopter, plane). No vehicle overrides them, so changing them needs a private copy (R7),
and what the `_ms` numbers measure is `UNKNOWN`. **"Drives underwater" has no member anywhere** -
the scan of every member path in all 52 module types finds only those rows, the water modules,
`number_of_water_collision_sensors`, `fins[].effective_in_water` and the helicopter's flight
`dive_*` terms, so a submerged car's behaviour is native code.

`--check` → `PASS: 232 entities, sink 189 / floating 8 / boat 35, donor will_sink 1 buoyancy 2
drag 100 (1 hull element), 35 boats base_buoyancy 0.1..1.45, 21 fleet-wide water/engine rows in
one shared VehicleCommon, build water modules identical to the donor: True, 38 member paths scan
as water-related`.

### Tether, airlift and winch (`TETHER.md`, G2-34)

Of WLD-7's three halves, the files carry the **mass** only. `RigidBody.mass` is on **232
entities** with **no unit stated anywhere**, so every comparison is a ratio: the donor is
**975**, a 6,000 Batmobile is **6.154x** it, **15.0%** of the cargo plane's own body
(**40,000**) and **6.0%** of the transport boat's (**100,000**). `CVehicleCargoBay` exists on
**12 entities** (6 cargo planes, 4 transport boats, 2 monorail flatbeds) with **7 members and
no capacity field**, and `v4603 … military_cargo_tank` is the fleet's **only compound entity** -
two vehicle roots (`CAirPlane` + `CCar`) and two bodies (`40,000` plane + `25,000` tank) in one
`.ee`, which is the decoded proof that a vehicle can ride inside another. **No helicopter has a
cargo bay**, so "a helicopter airlifts the car" has no file carrier.

**Tether strength is UNKNOWN and provably absent**: all 335 `tether` names in the index are
dialogue, two upgrade icons, two upgrade videos, one decal and the two
`dualtether_test_to_vehicle` graph files - no tune, no force, no break threshold - and no module
type in the fleet's 53 is tether/cargo/rope/winch/tow. The only tether-ish vehicle data is
prop-side: **33 `CGrapplingHookPropData` objects on 3 entities** (a cargo truck's loose barrels
and a flatbed's container prop), where `tether_tear` / `tether_tear7` / `tether_yank` name which
prop may be torn off, with empty event fields and no number.

For WPN-6 the **mesh carrier exists and the mechanic does not**: the transport boat's parts
module has `transport_rope_winch` (part 26 of 56, `Boat_Generic`, `behavior = None`,
`parent = 0`) plus **9 more rope parts**, and the mesh ships in the entity as **6 files** (1
`.lod` + 5 `.rbm` LODs). Nothing in a vehicle part's 67 named behaviours is a winch, rope, tow or
reel - the nearest is `CargoBayDoor` - so a car can *wear* a winch and cannot *use* one.

`--check` → `PASS: 232 masses (donor 975, target 6000, 1 multi-body), bays 12 on 12 entities / 0
helicopters, hooks 33 on 3 entities, compound 1, rope/winch parts 40 (10 names) + 12 winch LODs,
tether-ish module types 0/53, winch classes 0, index tether 335 (7 non-dialogue) / winch 0`.

### Interaction points and stunt areas (`INTERACTION.md`, G2-18)

The donor `.epe` carries **85** prefixed objects - `entry.*` 29, `exit.*` 26, `transition.*` 12,
`point.*` 8, `trigger.*` 7, `interaction.*` 3 - and only **15** own a `world` matrix (the 8 points
and 7 triggers); the rest inherit their container's. Those container matrices are identity, so an
entry has **no position of its own** - it is marked as such rather than given a fake verdict at
the origin. Every object still carries the string the animation side needs (`S_ENTER_DRIVER_VEHICLE`,
`S_EXIT_VEHICLE`, 36 distinct states), which is what makes the graph portable.

`StuntAreas` **declares 3 areas in a 32-slot array** - `front_area` and `front_signature_area`
(coincident, 6 points / 4 triangles each, bound to `sportsmuscle_hood` vs
`sportsmuscle_hood_signature`) and `main_area` (10 points / 8 triangles on `sportsmuscle_body`) -
plus 64 `welding_info` rows of which only **8 are real welds**. The standable surfaces are real
triangle sets (`vertices3D_local` + `triangle_indices`), not AABBs.

Placed on the Batmobile by bbox normalisation (an analysis mapping, **not** the R2 build
transform) the objects land **30 inside the shell, 23 floating, 0 on-surface, 32 with no position
of their own**. The three stunt surfaces are *tilted*, not lifted: `front_area`'s own
`center_local` is 0.104 m out and its worst vertex 0.374 m, `main_area`'s 0.020 m (on-surface) and
0.596 m. A build has to re-fit these vertices against the Batmobile mesh; scaling them keeps the
centre right and the edges wrong.

`--check` → `PASS: 85 objects (entry 29, exit 26, interaction 3, point 8, transition 12, trigger
7), transforms own 15 / inherited 70 / none 0, verdicts {'floating': 23, 'inside': 30, 'n/a
(container origin)': 32}, stunt 3/32 active (64 welds), mesh 28940v/20000t, json match True`.

### Driver seat and pose (`SEAT.md`, G2-19)

**The car does not own the pose.** The vehicle half is the interaction graph only: **34**
driver-named objects (`entry.driver` with state `S_ENTER_DRIVER_VEHICLE`; prefix census
`entry` 10, `exit` 14, `transition` 4, `point` 3, `trigger` 2, `interaction` 1), all transform +
state string, no seat/occupant/animation module. The pose half is Rico's: `rico_base.afsmb` carries the driver-seat conditions
(`PPC_IS_CURRENT_VEHICLES_DRIVER_SEAT_OCCUPIED`, `PPC_IS_ENTRY_NODE_DRIVER_SEAT_OCCUPIED`), the
`PPikt.driving.{left,right}.{hand,foot}` IK targets and **36** `MOD_*` class selectors, and
`rico_base.asb` embeds **382** seated clip paths across **40** class folders (`car/low` 23,
`car/med` 35, `car/circuit` 9, `car/high` 4, `tank` 10, `boat` 33, `helicopter` 28, `plane` 17,
`bus`, `tractor`, `bike/…`, …). Two of the card's four In items do not exist: the index has **0**
`jc_statemachine/vehicles/` and **0** `jc_skeletons/vehicles/` files, and only 2 of Rico's vehicle
`.ban` files are separate entries (both the mech suit), so the clips live inside the `.asb`.

Seat height is measurable per vehicle because the seat is a part and its collision is a hull in
the `.physicsc`: the `Land_Seat` parts sit at **0.855 m** (`sportsmuscle_f_l/r_seat`),
**0.855 m** (same) and **0.894 m** (`racinghothatch_seats`) - a 39 mm span. The supercar's
`racingsupercar_seats` is a real `Land_Seat` part whose index no compound instance carries, and
the medium tank has no seat part at all (only `mediumtank_hatch`, class `Land_Door`), so those two
heights are UNKNOWN rather than 2.879 m. The candidate is `sportsmuscle_f_l_seat`, **10 mm**
below the Batmobile's `Driver` hip (0.8647 m), i.e. the `car/*` pose families; which of
`low`/`med`/`circuit` plays is chosen by native code and no index file maps an entity to one.

`--check` → `PASS: 34 driver points | 40 pose classes (382 clip names) | 36 MOD selectors | seat
boxes 4 | candidate v0300_car_kensington_sportsmuscle (10 mm from the hip), json match True, md
match True`.

### Exit, bail-out and eject (`EJECT.md`, G2-20)

**JC3 has no eject, and nothing in the data can push the driver upward.** The fleet's **4,832**
`CInteractionGraphExit` objects (232 graphs, 61 names, 26 in the donor) draw their members from a
fixed set of **9 keys** - `state`, `modifier`, `enabled`, `interaction`, the two event lists,
`name`/`name_hash`, `_object_id` - and **0** of them carries a velocity, impulse, launch or force
member; `enabled` is `1` and `interaction` is `00000000` on all 4,832. Of the 104 graph classes,
the only two with a moving-sounding name are the velocity *condition* (4,057 instances) and the
car's own `CForcePulse` (G2-17). The vehicle modules have exactly **1** launch-ish member name in
232 entities (`TrainGlobal.crashing_impulse` ×12) and one upward mechanism, `arcade.turbo_jump`
(145 land vehicles: `punch_speed_kph` 50/80, `top_speed_kph` 200, multipliers 15/12 and 30/25,
cooldowns 5 s/2 s) - which jumps the **car** and has no vertical-speed member at all.

What an exit *does* is select a state, gated by the parent's speed. The donor's driver side
splits at **5**: `exit.driver.default` (`S_EXIT_VEHICLE`) and `exit.driver.to.fall`
(`S_EXIT_VEHICLE_TO_FALL`) are gated 0..5, while `exit.driver.roll.out`
(`S_ROLL_OUT_EXIT_VEHICLE`) and `exit.driver.moving.parachute` (`S_EXIT_VEHICLE_PARA`) are gated
5..999. So the parachute exit is simply *the fast one* - the same on 221 of 232 vehicles,
including boats, helicopters and jets - and the two fast exits share a gate, so which one wins is
code. 7 of the 26 are speed-gated; 5 carry no condition at all (pushed out, pulled out, swim,
upside down ×2).

BmAK's eject is authored as `RVehicleBatmobile.EjectUpMove` / `EjectForwardMove` / `…VerticalMove`
/ `EjectToSpotMove` plus one float, `EjectUpDist`, and two natives (`ModifyEjectUpLoc`,
`SetBatmobileExit`). The mapping for MOD-3 is therefore **exit → `exit.driver.moving.parachute`,
launch → UNKNOWN**: the carrier exists for the exit and the parachute state, none exists for an
upward impulse, so the launch half is Q1-EJ-A (apex 0.0 ±0.2 m vs > 1.0 m), with Q1-EJ-B (which
fast exit wins) and Q1-EJ-C (is the chute automatic) beside it.

`--check` → `PASS: 4832 exits in 232 graphs (61 names) | donor 26 exits, 7 speed-gated, 5
unconditional | launch members: exits 0, graph classes 2, vehicle modules 1 | BmAK eject props 19,
json match True, md match True`.

### The damage model (`DAMAGE_MODEL.md`, G2-28)

The chain from a bullet to the health bar is **seven steps**; the files give numbers for four, the
mechanism for a fifth, and **nothing at all** for how `*_armor`, `*_armor_strength`, `max_health`
and the root `health` float compose. That last gap (POSTMORTEM_DAMAGE §5 item 1) is carried as
**three named models** with exact per-arm numbers rather than one formula pretending to be decoded:
H0 (armour ignored), H1 (percentage gate, the reading MODLOG 97 used) and H2 (per-hit threshold +
absorbing pool).

Measured for the three targets: the donor is **700 HP with every channel 0 @ 0 and 24
`part_damage_types`**; the medium tank is **2000 HP, bullet 5000 @ 99, explosion 250 @ 50, impact
0 @ 0**; the live build (`Builds/test-091`) is **the tank's profile in six values** (`impact_armor`
5000 @ 100, `melee` 5000 @ 100, `impact_damage_factor` 0, `deform_scale` 0) and keeps the
**donor's part table with exactly one change** - `Land_Wheel.instantly_damaged_by_bullets` 1 -> 0,
the only part-level ARM-4 edit in the build.

The nine arms are decoded, not typed: the three vehicle arms from `WEAPONS.jsonl` and the six hand
arms re-decoded from the archives (G2-10 only covered `06_vehicle/`). Two of them are not what
their name suggests - the **tank cannon's bullet damage is 1.0** and its work is the 1500 blast in
8 m, and the **shotgun is 144 per pull** (8 pellets x 90 x 0.2), the highest small-arm number by
4.5x, which is what an ARM-1 gate would have to exceed.

At the BmAK ratio (G1-14: `Pawn.Health` 1200 / heavy cannon 50 = **24 hits**) ARM-2's count is
**outside the shipped domain**: 24 x the 1500 shell would need `max_health` 36,000 against a fleet
range of 500..4000, i.e. 3 hits at the maximum. ARM-1 needs either `invulnerable` (whole-vehicle,
so it kills ARM-2) or a bullet gate the fleet does not ship.

`--check` -> `PASS: 9 arms x 3 vehicles, models H0, H1, H2, finite H0 27 / H1 27 / H2 19, never H1
0 / H2 8`, `chain 7 steps, 7 carry an UNKNOWN, 3 Q-1 probes`, `json match True`.

### Names, strings and icons (`NAMES.md`, G2-32)

The car the project replaces is called **KERNER SERPENTE R**, and that string is a pair in
**`profile/online.stringlookup`** keyed by the 32-bit Jenkins hash of the entity leaf name
(`v0300_car_kensington_sportsmuscle_civilian_01` -> `D2B46B49`). The store is 11 languages of
`{Hash, TextOffset}` into one 1.44 MB NUL-separated text blob; the `_desc` pair (`0x7B942DF2`) holds
the blurb. The Rebel Drop item (`profile/item.onlinec`) carries only the hashes - `UIName` is the
leaf hash, `UIDescription`/`UIFlagDescription`/`UITypeDescription` resolve to the blurb, **SPORTS
CARS** and **SPORTS CAR** - and the icon is the same leaf as a file:
`textures/ui/vehicle_icons/<leaf>.ddsc` (18,688 B). The bridge is exact across the drop list: **45 of
45** vanilla vehicle items resolve their `UIName` and **45 of 45** have their icon file.

Measured absences matter as much as the carriers: `ui/ui_localization.stringlookup` (923 KB, 11
languages) does **not** contain the name (its only "Serpente" strings are the two Weaponized-Serpente
DLC banners), the donor's own `.stringlookup` holds **one** entry - the prompt `Get in Vehicle` - and
no `.gfx` movie contains the leaf, the name hash or the string `vehicle_icons`, so the menu binding
is data-driven. No per-vehicle map icon exists at all, and the build's own copy of the entity
`.stringlookup` is byte-identical to the **base** archive copy (the patch copy differs only in
padding), so the mod ships the base string table and loses nothing.

For the Batmobile: keep the leaf and the vanilla name/icon come for free; rename by adding a pair for
the new leaf's hash (the `.ee` leaf, the item `Name`/`UIName` and the string pair must agree); a new
icon is one 18,688 B file named after the leaf.

`--check` -> `PASS: name 'KERNER SERPENTE R' in 11 languages (id D2B46B49), desc in 11 languages,
item 3535039305, icon 18688 B, fleet 45/45 named 45/45 iconed, ui_localization resolves 0 of 2 keys,
gfx references 0`.

### Vehicle audio (`JC3_AUDIO.md`, G2-24)

The sound banks are **FMOD Designer/Ex event banks**, not FMOD Studio: `RIFF` form `FEV ` with
`FMT ` version **56 build 50**, a `PROJ` section (`EVTS`, `TLNS`, `WAIS`, `WAVS`, `PRMS`, DSP
sections) and one **FSB5** sample bank in the `SND ` chunk. The donor pins **45 events** in 758 B
of `.ee.fmod_guids` across `vehicles` (24), `character` (2) and `effects` (19); all 45 are found as
an `EVTS` entry, **23** are named by an `SAttachedEffect`/`SDynamicAttachedEffect` in the `.epe`
(the other 22 are preloaded but unreferenced by the graph). `vehicles.bank` holds **257 events /
257 tunes / 1,674 sound instances / 649 waves / 649 FSB5 samples** (153,439,744 B of data, 21,196 B
of sample names).

**Event -> sample is UNKNOWN, and the report proves the gap**: the event entry's body starts with
the 16-byte event GUID and carries **no name string**, no event body contains a `TLNS` tune GUID
(0/257), no field permutes the tune indices, the 649 `WAVS` GUIDs are referenced **0** times
outside `WAVS`, and no field in the 1,674 sound instances enumerates 0..648. The chain stops at
the event GUID + its ordinal, so a build picks the sample it replaces by **name and audition** -
what test-060 did (MODLOG §70/§71).

The sample census is per-stream through `vgmstream-cli -s N -m`: **649 samples, all 16-bit PCM at
48 kHz** (1 or 2 channels, **22 looped**). `LandAudio` is the whole vehicle-side audio parameter
set - **2 members**, `min_rpm` 1,000 and `max_rpm` 10,000 - the JC3 counterpart of BmAK's
`REV_RPM`/`Speed` RTPCs; the bank's own 969 `PRMS` parameters and their event bindings stay
UNKNOWN.

Weapon sounds split two ways. `w602`/`w603` exist only as `.wtunec` (no `.ee`, no
`.fmod_guids`) and all **171** of their tune members are damage/recoil/scatter/shake with **0**
audio members - their firing audio lives on the vehicle that fires them (the medium tank's
`Fire`/`ReloadStart` roles) and in `weapons.bank`'s named samples. `w618`/`w619` carry their own
`.ee` + `.fmod_guids` (10 and 12 GUIDs, banks `weapons_preorder`/`effects`) and bind the fire
event on a `SAttachedEffect` whose `Sound` is the first GUID of that list.

Horn and radio: the donor's `horn` is `fd69c63c-…` in `vehicles`; **178** `horn` objects across
**178** vehicles (19 distinct GUIDs) make it a per-model attached effect, and the fleet has **0**
`radio` objects (JC3's radio is the music system, not a vehicle effect). Since BmAK's `horn` group
is **0 rows / 0 events** (`AUDIO_FEATURES.md`), removing the effect is the lore-correct move.

Routes: **(a)** same-size PCM payload swaps inside a copy of `vehicles.bank` (proven, test-060,
loose override with no `.toc`) works; **(b)** a new bank is **not** possible from the shipped data
- the FEV graph is the event authoring format and no `.fev` project ships; **(c)** the same swap
in `weapons.bank` (1,228 named samples) covers the guns. Recommendation **a + c**.

`--check` -> `PASS: 45 donor events in 3 banks, 257/257 vehicle events/tunes, 649 samples (22
looped, 1 rate), wave refs 0, LandAudio 2 members, weapons 4, horn 178 / radio 0, md match True`.

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
| `PHYSICS_WRITE.md` / `PHYSICS_WRITE.json` | **writing a `.physicsc`** (G2-30): the round trip over all 54 hulls, the offset-remap stress, a scaled hull and a size-changing replacement, the parent-AABB rule, the plan for a Batmobile hull set and its remaining UNKNOWNs, with `--check` re-deriving all four cases and re-reading the written blobs |
| `PARTS.md` | the parts module (`G2-7`): ADF v4 layout, why the converter failed, validation, limits |
| `PARTS_TABLE.jsonl` (2.6 MB) | **233 vehicles / 11,643 parts** — part index, name, damage type, behavior, model, collision body, light flag, children, wheel slots |
| `PARTS_TABLE.md` | generated summary: damage-type distribution, parts per vehicle, the donor's 42 rows |
| `GEOMETRY.md` / `GEOMETRY.jsonl` | **56,136 meshes** — decode status, counts, materials, payload offsets |
| `FX.md` / `FX_VOCAB.json` | **57,187 files / 62.5M rows** — per-extension roots, member vocabulary, ranges |
| `WEAPONS.md` / `WEAPONS.jsonl` | **25 weapon ids** (G2-10): every tune member, the shared autoaim presets and the per-id sources |
| `WEAPON_WIRING.md` / `WEAPON_WIRING.jsonl` (506 KB) | **53 armed entities** (G2-11): slot pointers, weapon props, fire points, aim components, seats, mount parts and chassis moving parts |
| `SIGNATURE_DIFF.md` / `SIGNATURE_DIFF.json` | **the armed Serpente vs its civilian build** (G2-12): every container member, graph change, part link, mesh header, tune row and `.toc` entry, with `--check` rebuilding both |
| `TURRET.md` / `TURRET.json` | **turrets and cannons** (G2-13): eight vehicles' hinged parts with pivots, axes and limits, the `id:80201E4D`/`id:5C19E7E0` point census (92 points / 52 weapons), the `aim_part_constraints` census and the two autoaim tunes, with `--check` rebuilding both |
| `MOVING_PARTS.md` / `MOVING_PARTS.json` | **the behaviour tables** (G2-14): 67 behaviours with channel, driving variable, parts/entities/chassis, root class and `CCar` proof, plus the per-part arrays, with `--check` rebuilding both |
| `DOORS.md` / `DOORS.json` | **doors, canopies and missile hatches** (G2-15): door parts with hinge axis/limits, a 224-row axis census, the monorail bay covers and their weapon, and the entry-path census (`entry.driver` vs `.no.door`), with `--check` rebuilding both |
| `EMP.md` / `EMP.json` | **the EMP truck** (G2-16): both builds' device parts and rotating core, every pulse member against the stock blast, the trigger/prompt, the effect files, a 9-variant census and the two `CEMPWeapon` files (points, components, tune values), with `--check` rebuilding both |
| `TANKTURN.md` / `TANKTURN.json` | **turn-on-the-spot** (G2-21): the four tracked chassis vs the fleet — identical card-module member sets, five refuted candidates with histograms and fleet ranges, the 262-value tank-unique census, the track/pivot/skid name scan, the container file types and the 12/12 `CCar` proof, with `--check` rebuilding both |
| `FORCEPULSE.md` / `FORCEPULSE.json` | **every pulse in the fleet** (G2-17): 307 pulses / 232 `.ee` / 79 chassis, all 31 members with presence and ranges, the 23 blast tunes decoded to their eight `ForcePulseSettings` numbers, the owner-pointer census (293 owned, 14 unowned), the horn/collision refutation and the one `GraphScript` reference, with `--check` rebuilding both |
| `JC3_HUD_WEAPONS.md` / `JC3_HUD_WEAPONS.json` | **the vehicle-weapon HUD API** (G2-25): both card functions' 9 and 6 arguments with defaults and drives, the 2-slot array and its six per-slot fields, the `0..1` cooldown loader and overcharge, 14 reticle shapes / 5 look states, the lock-on POI (21) vs the incoming-missile warning, the `w609`/`w612`/`w613` `AutoAim` envelopes, the weapon-id -> icon rule with its one missing icon, the caller census, and WPN-12 element by element, with `--check` rebuilding both |
| `REBELDROP.md` / `REBELDROP.json` | **Rebel Drop tables** (G2-26): the `Item`/`Task`/`Reward` schemas, the name-hash → `.ee` binding (80/80 vanilla vehicles, 45/45 mod additions), base-vs-patch and mod-vs-base diffs, the `task.onlinec` unlock links and the field-by-field recipe for a "Batmobile" entry, with `--check` rebuilding both |
| `USAGES.md` / `USAGES.json` | **the effect usage vocabulary** (G2-22): 12 usage names with hashes, module and vehicle counts, every row's vehicle list, the empty `ExtendedEffectUsages` stub, the 155-value `.epe` `Usage` space with its name provenance (6/60/4/85), the `EngineNitro` -> `dynamic_nitrous` flame candidate with its 307 objects and 9 nitrous `.effc` paths, the donor's 51-value usage map, and the unknown trigger names; **plus the nitro chain** (G2-23, §6): `arcade.nitro_boost` input values, the donor's two `EngineNitro` objects, the module effect `dynamic_nitrous` (397752766) vs the unnamed object hash 3518298851, the sound GUID `f74ea43b-…` (202 objects / 172 vehicles / `vehicles.bank` `EVTS` 249) and the three FSB5 samples chosen by name (56/150/355 = the test-060 swap), with `--check` rebuilding both |
| `LIGHT_SYSTEM.md` / `LIGHT_SYSTEM.json` | **the vehicle light system** (G2-33): the module's 25 members with value censuses, the `.epe` `SVehicleLight` side, the preset census (393 ids, 17 zeros, 34 inconsistent), the part-binding checks (`has_lights`), the `CarLight` block format, and the wheel-arch recipe with a source and a class per member, with `--check` rebuilding both |
| `INTERACTION.md` / `INTERACTION.json` | **interaction points and stunt areas** (G2-18): all 85 `entry`/`exit`/`point`/`transition`/`trigger`/`interaction` objects with their transform source and state string, the 7 trigger volumes, the 3 active stunt-area triangle sets with their welds, and every point's position in Serpente space plus its Batmobile verdict, with `--check` rebuilding both |
| `SEAT.md` / `SEAT.json` | **driver seat and pose** (G2-19): the 34 donor driver objects with their state strings, Rico's state machine (seat-occupancy conditions, driving IK targets, 36 `MOD_*` selectors), the 382 seated clip paths in 40 class folders, the seat part hulls per vehicle with their `Land_Seat`/`Land_Door` class, the candidate seat against the Batmobile hip, and the absent `jc_statemachine/vehicles`/`jc_skeletons/vehicles` inputs, with `--check` rebuilding both |
| `EJECT.md` / `EJECT.json` | **exit, bail-out and eject** (G2-20): the 4,832 exits' 9-key member set (no launch field anywhere), the velocity *condition* as the only motion class, the donor's 26 exits with state, gate and nested conditions from the `.epe` XML, the 5/3-unit speed split, the fleet's class coverage and `MOD_*` selectors, the `turbo_jump` numbers as the one vehicle-side impulse, the BmAK `Eject*Move`/`EjectUpDist`/`MaxEjectType` properties, the MOD-3 mapping and three Q-1 probes, with `--check` rebuilding both |
| `NAMES.md` | **names, strings and icons** (G2-32): the name and blurb per language with their hashes, the Rebel Drop item record and every `UI*` id it carries, what the donor's own `.stringlookup` holds (one prompt) and what `ui/ui_localization` does not (the name), the vehicle/store/variant icon files with their keying rule, the 45/45 fleet resolution, the `.gfx` and frontend reference scan, the rename/new-icon recipe, and the UNKNOWNs, with `--check` rebuilding it |
| `DAMAGE_MODEL.md` / `DAMAGE_MODEL.json` | **the damage model and the hits-to-kill table** (G2-28): the seven-step chain with its per-step UNKNOWNs, the three health profiles (donor / medium tank / build) field by field, the six-value diff that makes the build the tank's profile and the one-value diff that makes its part table the donor's, the nine arms with their guns/factors/pellets/blasts, the 27-cell hits-to-kill table under H0/H1/H2, the ARM-1/ARM-2 domain arithmetic at the BmAK 24-hit ratio, the fleet `armor @ strength` census, and three Q-1 probes with exact expected counts, with `--check` rebuilding both |
| `TETHER.md` / `TETHER.json` | **tether, airlift and winch carriers** (G2-34): the fleet mass census with its UNKNOWN unit, the 12 `CVehicleCargoBay` entities and their 7 member-only objects, the compound cargo-tank plane with two roots and two bodies, the 33 prop-side `CGrapplingHookPropData` objects (`tether_tear`/`tether_yank`), the `transport_rope_winch` geometry with its 10 rope parts and 6 mesh files, the behaviour census that rules out a pull, and the index `tether`/`winch` scan, with `--check` rebuilding both |
| `STANDALONE.md` / `STANDALONE.json` | **standalone entity** (G2-27): the 17 registration sites by key type, the two `entityregistry_gen.entityregc` blobs decoded to their record shape and coverage (251/922 index leaves, 158/233 vehicles, 0/86 base spawn records unregistered vs 163/169 debug and 13/21 DLC), the 9 spawn tables and their full-path records, the mod's 20 `.ee` at vanilla paths with 0 `.toc`, the donor `.ee`'s 604 inner files, and the yes/no for a new path with its one Q-1 probe, with `--check` rebuilding both |
| `WATER.md` / `WATER.json` | **water behaviour** (G2-31): every member of `Buoyancy` / `WaterInteraction` / `BoatBuoyancy` with fleet range and donor value, the 189/8/35 split by `will_sink`, the shared `vehicle_damage` + engine-shut-down constants, the card's roster (donor, armoured transport, three tanks, APC, duck, boats, floatplane, sea scout), the keyword scan that rules out an underwater member, and the `Builds/test-091` module comparison, with `--check` rebuilding both |
| `TRAFFIC.md` / `TRAFFIC.json` | **traffic, AI and spawning of `v0300`** (G2-29): the 11,751-file / 7.7 GB donor-name scan and its 17 hits, the 86-record ground spawn table and every other spawn table, the 31 traffic rules / 41 selector match, the Rebel Drop / chop-shop / level-rule spawn sites, the tag census and the traffic verdict for D-6, with `--check` rebuilding both |
| `JC3_AUDIO.md` / `JC3_AUDIO_EVENTS.json` | **the vehicle audio system** (G2-24): the FEV v56 container and its sections, the 45 donor events with bank, ordinal and `.epe` role, the three banks' event/tune/sound/wave/parameter census, the event -> tune -> sample chain (event -> tune stored on both sides, tune -> wave not stored), the 649-sample census (codec, rate, channels, loop points) through vgmstream, the four weapon ids' sound wiring, the fleet horn/radio census, `LandAudio`'s two members, and the three ship routes, with `--check` rebuilding both |
| `FX_TABLE.jsonl` (22 MB) | one row per effect/camera/trim file: container, source archive path, path, size, root class, row count, array census digest, row digest |
| `E:\Modding\JustCause3\_grab\entities\*.json` | raw module decodes, 233 files / 266 MB — **outside the repo** |
| `E:\Modding\JustCause3\_grab\detail\*.json` | raw `.epe` graphs + `.rbm` headers, 233 files / 48 MB |
| `E:\Modding\JustCause3\_grab\geom\*.json + .bin` | **440 MB** of decoded positions (float32 ×3) and indices (u16), one pair per entity |
| `E:\Modding\JustCause3\_grab\phys\*.json` | raw station extraction, 233 files |
| `E:\Modding\JustCause3\_grab\hkx\out\*.json` | decoded packfiles, 233 files / 141 MB: every hull vertex, plane and index, mesh AABBs, geometries — **outside the repo** |
| `G2X.md` / `G2X.json` | **the G2 exit gate** (G2X): all 75 feature codes of backlog §1 with the file that carries each one and a needle that must still be in it (67 carriers) or the census surface and must-not-exist words that prove the absence (8), the 24 G2 readers and the P0-2 census re-run as subprocesses with their verdict lines, and the §11 decisions each row's *value* waits on, with `--check` re-deriving every row and re-running every reader |

Game bytes never enter the repo; only derived tables and paths do.
