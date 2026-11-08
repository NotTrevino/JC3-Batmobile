# chase-G3-01b-boxes-u3 — FMatrix storage order for this build, and the weapons box's tilt sign

**STATUS: partial** — the *layout* of the 64-byte `TM` is settled (decoded + oracle), the
*row/column* question is **not** settled by any known case in this build, and the tilt's sign
therefore stays conditional. What blocks it is stated exactly in `UNKNOWNs` below.

The brief: G3-01b (`tmp/freebuff/reports/G3-01b-boxes.md`, U-3) decoded the weapons box's 3x3 as a
proper 4.00° rotation about Y but could not tell whether the three planes are the transform's rows
or its columns, so the tilt's sign was open. Settle it with a known case — a skeletal mesh
reference pose compared both ways. Result: the case the brief names is **empty** (that bone's ref
pose is the identity), and no other transform in this build is stored both as a matrix and as a
quaternion.

## What the answer is

| question | answer | label |
|---|---|---|
| how the 16 floats are laid out | four planes, each stored `(W,X,Y,Z)`, in the order X, Y, Z, W; the W column is `(0,0,0,1)` | **decoded** (BmGame 169750/169751, 3/3 boxes) + oracle |
| reading A (rows = floats `4i+1..4i+3`) | orthonormal, det +1 | **decoded** (det 1.0000000 / 1.0000000 / 1.0000001; max row·row 3.49e−21) |
| reading B (rows = floats `4i..4i+2`) | singular on both identity boxes | **decoded** (det 0.0) → **rejected** |
| are the planes rows or columns | **UNSETTLED** — no known case exists in these packages | **UNKNOWN** (see U-1) |
| the tilt's magnitude / axis | 4.0000° about the Y line (`axis (0, −1.0000055, 0)` in the column-vector sense) | **decoded** (BmGame 169751, TM value at byte 89) |
| the tilt's **sign** | **conditional**: `+4.000001°` about **+Y** if the planes are the rows (row-vector, `P' = P·M + T`); `−4.000001°` about **+Y** if they are the columns (`P' = M·P + T`). The only relation in the build that points either way (capsule axes vs their bones' own reference-pose directions) points at the **column** reading, i.e. −4.00° about +Y — but that is *evidence* under an art-setup premise, not an oracle | **derived**, conditional |

Both readings are the *same three planes*: rows-are-images gives local X → `(0.9975641, 0,
−0.0697565)`, local Z → `(0.0697565, 0, 0.9975641)`; columns-are-images gives local X →
`(0.9975641, 0, +0.0697565)`, local Z → `(−0.0697565, 0, 0.9975641)`. One matrix cannot separate
`R` from `Rᵀ`, and no second transform of that bone exists to compare against.

## Files written

| file | what |
|---|---|
| `Tools/scripts/grab_matrix_order.py` | the new tool (`--write` / `--check`), 765 lines |
| `Research/BatmobileGrab/MATRIX_ORDER.md` | the record (generated, 153 lines) |
| `Research/BatmobileGrab/MATRIX_ORDER.json` | the same as data (16,335 B, 8 checks, 15 keys) |
| `tmp/freebuff/reports/chase-G3-01b-boxes-u3.md` | this report |

Nothing else was written. G3-01b's `grab_collision_boxes.py` / `COLLISION_BOXES.*` and every other
task's files are untouched; `grab_matrix_order.py` only *imports* `upk_read` and
`reverify_bones.find_ref_skeleton` read-only (the same way G3-01b imports G3-01c). Read-only on
`E:/Games`; no game process started; no git operation; scratch probes are in
`tmp/freebuff/scratch/`.

## Why the named known case is empty (decoded)

The mesh's reference pose for `Batmobile_Rig_Weapons_Trans` — record 101 of the 44-byte skeleton
array of `Playable_Batmobile_SF.upk` export 5284 (`Batmobile_V2_Mesh.Batmobile_V2`, 20,151,210 B),
array at byte 8395, stride 44, 180 records — is:

```
record 101  Batmobile_Rig_Weapons_Trans  parent Batmobile_Rig_Weapons_Turret_Root
            quat (x,y,z,w) = [-0.0, 0.0, -0.0, -1.0]        -> 0.0000 deg
            position_cm    = [17.65315, -0.00064, -1.51528]
record 0    Batmobile_Chassis            quat [-2e-06, -0.0, -2e-05, -1.0] -> 0.0023 deg
```

The reference pose rotation is the **identity**: the mesh carries no 4.00° tilt for that bone at
all. The box's tilt is a shape-local orientation authored inside the bone's frame, so comparing
the mesh pose against the box cannot yield a sign. Every *other* bone's rotation in the mesh is
also a quaternion and never a matrix, so there is nothing to compare the `TM` against.

## Why no other known case exists (decoded census)

Every 64-byte `TM` struct in the eight packages that carry them, by owning class:

| package | exports | `TM`(64) | by class |
|---|---:|---:|---|
| BmGame.upk | 177031 | 880 | `RB_BodySetup` 872, `RAggGeomCollisionComponent` 8 |
| Startup.upk | 174890 | 2186 | `RB_BodySetup` 2105, `ApexDestructibleAsset` 77, `RAggGeomCollisionComponent` 4 |
| StartupPatch.upk | 142232 | 237 | `RB_BodySetup` 236, `RAggGeomCollisionComponent` 1 |
| Orphan.upk | 27883 | 262 | `RB_BodySetup` 242, `ApexDestructibleAsset` 10, `RAggGeomCollisionComponent` 10 |
| Playable_Batmobile_SF / MK2 / Joker / Funhouse | 5490 / 5534 / 3388 / 5584 | 32 each | `RB_BodySetup` 32 each |

The SkeletalMesh export 5284 was scanned at every float offset (5,037,802 offsets) for an
orthonormal 3×3 in either lead layout: **10** prefilter candidates, **0** orthonormal. So the build
stores matrices only in aggregate geometry (shape frames inside a bone) and in Apex destructible
chunks (84 of 87 identity; the 3 that are not have no quaternion counterpart either), and
quaternions only in skeleton/anim records. **No transform is written both ways**, which is exactly
what a known case needs.

Also checked and rejected as a source of a known case: the 3 BmGame boxes' own bone poses (identity
for both chassis and weapons); the rig-assignment test showing 0 of 122 non-identity capsule TMs
reproduces its own bone's reference-pose rotation (so TMs are **not** bone transforms); and the
weapons bone's own skinned geometry — it owns **no** points (probe below), so its box cannot be
bracketed against its own vertices either.

## The evidence that does point somewhere (derived, premises stated)

A ragdoll capsule must span its bone. Its centre is `TM` floats 13..15, which no rotation reading
touches, so the premise is checkable before the axis is judged: 149 capsules, centre vs the bone's
own reference-pose direction (nearest child's `position_cm`) median **8.138°**, 58/149 within 5°;
capsule length / bone length median **0.8807**. On the strict subset (55 capsules with the centre
within 5°), reading the capsule's long axis both ways:

| reading | local axis | median | ≤2° | ≤5° | ≤10° |
|---|---|---|---|---|---|
| rows = axis images | Z | 26.278° | 7 | 23 | 26 |
| columns = axis images | Z | **4.385°** | 10 | 28 | 39 |

The column reading wins by a factor of six in the median. It is **not** an oracle: it rests on the
art-setup premise, the capsule is symmetric about its own long axis (so its bytes cannot name that
axis — U-2), and the two readings overlap at the tails. It is reported, not used, and the tool
labels it `evidence, not an oracle`.

## Commands and outputs (verbatim)

Skeleton decode probe (which reference pose the brief names):

```
$ uv run python tmp/freebuff/scratch/g301x_reorder.py
skeleton at 8395 count 180
{'index': 0, 'name': 'Batmobile_Chassis', 'name_index': 200, 'parent_index': 0, 'quat': [-2e-06, -0.0, -2e-05, -1.0], 'position_cm': [2e-05, -0.0, 0.0], 'trailer_word': 4294967295}
{'index': 101, 'name': 'Batmobile_Rig_Weapons_Trans', 'name_index': 381, 'parent_index': 100, 'quat': [-0.0, 0.0, -0.0, -1.0], 'position_cm': [17.65315, -0.00064, -1.51528], 'trailer_word': 4294967295}
```
exit status **0**

`TM`(64) census:

```
$ uv run python tmp/freebuff/scratch/g301x_tmsweep.py
BmGame.upk                       TM(64) struct tags: 880 in 2 classes: {'RB_BodySetup': 872, 'RAggGeomCollisionComponent': 8}
Startup.upk                      TM(64) struct tags: 2186 in 3 classes: {'RB_BodySetup': 2105, 'ApexDestructibleAsset': 77, 'RAggGeomCollisionComponent': 4}
StartupPatch.upk                 TM(64) struct tags: 237 in 2 classes: {'RB_BodySetup': 236, 'RAggGeomCollisionComponent': 1}
Orphan.upk                       TM(64) struct tags: 262 in 3 classes: {'RB_BodySetup': 242, 'RAggGeomCollisionComponent': 10, 'ApexDestructibleAsset': 10}
Playable_Batmobile_SF.upk        TM(64) struct tags: 32 in 1 classes: {'RB_BodySetup': 32}
Playable_BatmobileMK2_SF.upk     TM(64) struct tags: 32 in 1 classes: {'RB_BodySetup': 32}
Playable_BatmobileJoker_SF.upk   TM(64) struct tags: 32 in 1 classes: {'RB_BodySetup': 32}
Playable_BatmobileFunhouse_SF.upk TM(64) struct tags: 32 in 1 classes: {'RB_BodySetup': 32}
```
exit status **0**

Apex chunk TMs:

```
$ uv run --with numpy python tmp/freebuff/scratch/g301x_apex3.py
  non-identity: Startup.upk 82008 News_Stand.Gotham_Objects_news_money_base_APEX 112 1.0
  non-identity: Startup.upk 82008 News_Stand.Gotham_Objects_news_money_base_APEX 230 1.0
  non-identity: Startup.upk 82012 OBJ_Crate.OBJ_Crate_Ammox2_Apex 112 1.0
Apex chunk TMs: 87, non-identity: 3
```
exit status **0**

Weapons bone's own skinned geometry (from umodel's PSKX, so a probe only — it is not in the tool):

```
$ uv run --with numpy python tmp/freebuff/scratch/g301x_geo2.py
points 201338 wedges 253163 faces 299837 bones 180
  Batmobile_Chassis                        dominated points 14554
  Batmobile_Rig_Weapons_Trans              dominated points 0
  Batmobile_Rig_Weapons_Turret_Root        dominated points 0
  Batmobile_Rig_Weapons_Turret_Top         dominated points 3784
```
exit status **0** — the box's own bone has no vertices to bracket, which closes the last geometric
route (a `±4°` box has the same axis-aligned bounds either way, so containment cannot decide it
either).

Capsule evidence (exploration run; the tool reproduces it):

```
$ uv run python tmp/freebuff/scratch/g301x_caps5.py
capsule bodies with a bone name: 143
rig-assigned capsule bodies: 137 | centre residual median 8.20, p25 3.44 p75 22.18
capsules 149 (non-identity 122)

-- premise subset: centre within 5 deg of the bone direction: 55 capsules
   rows = axis images     X med  88.3 <=5deg    0/55 | Y med  87.4 <=5deg   14/55 | Z med  26.3 <=5deg   23/55
   columns = axis images  X med  88.8 <=5deg    0/55 | Y med  88.0 <=5deg    0/55 | Z med   4.4 <=5deg   28/55

-- premise subset: centre within 10 deg of the bone direction: 82 capsules
   rows = axis images     X med  88.5 <=5deg    0/82 | Y med  87.8 <=5deg   17/82 | Z med  10.4 <=5deg   37/82
   columns = axis images  X med  89.0 <=5deg    0/82 | Y med  87.5 <=5deg    0/82 | Z med   4.6 <=5deg   43/82
```
exit status **0**

The tool, write then check (both exit 0):

```
$ python -m py_compile Tools/scripts/grab_matrix_order.py
COMPILE_OK
```

```
$ uv run --with numpy python Tools/scripts/grab_matrix_order.py --write
wrote MATRIX_ORDER.json and MATRIX_ORDER.md
layout: SETTLED: four planes, each (W,X,Y,Z), in the order X, Y, Z, W
storage order: UNSETTLED | tilt: 4.00 deg about the Y axis (magnitude and axis decoded; R and R^T share both). Sign: conditional - +4.00 deg about +Y if the planes are the rows (row-vector), -4.00 deg about +Y if they are the columns.
mesh reference pose of the weapons bone: [-0.0, 0.0, -0.0, -1.0] -> 0.0000 deg
TM(64) census: BmGame.upk 880; Startup.upk 2186; StartupPatch.upk 237; Orphan.upk 262; Playable_Batmobile_SF.upk 32; Playable_BatmobileMK2_SF.upk 32; Playable_BatmobileJoker_SF.upk 32; Playable_BatmobileFunhouse_SF.upk 32
matrix scan of the SkeletalMesh export: 10/5037802 offsets, 0 orthonormal
capsule evidence (n=55): rows=Z median 26.278 deg, columns=Z median 4.385 deg
8/8 checks passed
```
exit status **0**

```
$ uv run --with numpy python Tools/scripts/grab_matrix_order.py --check
layout: SETTLED: four planes, each (W,X,Y,Z), in the order X, Y, Z, W
storage order: UNSETTLED | tilt: 4.00 deg about the Y axis (magnitude and axis decoded; R and R^T share both). Sign: conditional - +4.00 deg about +Y if the planes are the rows (row-vector), -4.00 deg about +Y if they are the columns.
mesh reference pose of the weapons bone: [-0.0, 0.0, -0.0, -1.0] -> 0.0000 deg
TM(64) census: BmGame.upk 880; Startup.upk 2186; StartupPatch.upk 237; Orphan.upk 262; Playable_Batmobile_SF.upk 32; Playable_BatmobileMK2_SF.upk 32; Playable_BatmobileJoker_SF.upk 32; Playable_BatmobileFunhouse_SF.upk 32
matrix scan of the SkeletalMesh export: 10/5037802 offsets, 0 orthonormal
capsule evidence (n=55): rows=Z median 26.278 deg, columns=Z median 4.385 deg
8/8 checks passed
```
exit status **0**. `--check` re-reads both packages, re-decodes every number, re-runs the eight
checks and fails if `MATRIX_ORDER.md` or `.json` differs by one byte.

Strict JSON validation (no NaN/Infinity tokens):

```
$ uv run python -c "import json; raw=open('Research/BatmobileGrab/MATRIX_ORDER.json',encoding='utf-8').read(); d=json.loads(raw, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x))); print('JSON strict-parse ok, bytes', len(raw), 'keys', len(d), '| checks', d['passed'], '/', d['checks_total'])"
JSON strict-parse ok, bytes 16335 keys 15 | checks 8 / 8
```
exit status **0**

The eight checks, all PASS: the W column is `(0,0,0,1)` on all three boxes; reading A is
orthonormal with det +1 on all three; reading B is singular on the identity boxes; the weapons 3×3
is 4.0000° about the Y axis; the mesh reference pose of that bone is the identity; the SkeletalMesh
export holds no stored 3×3 at any float offset; no `TM`(64) exists outside aggregate geometry /
destructible chunks; no capsule `TM` reproduces its own bone's reference-pose rotation.

## What this changes for the card

- **G3-01b U-3 stays open**, but its scope is now exact: the *bytes* are fully settled (plane
  layout `(W,X,Y,Z)` in X, Y, Z, W order, translation in the fourth plane, reading A the only
  orthonormal one), and what is missing is a *semantic* fact — whether this build's matrix code
  multiplies row or column vectors — which these packages do not record anywhere.
- The 4.00° Y tilt can be quoted as **4.00° about the Y line** without qualification. Its sign is
  `+4.00° about +Y` **iff** the planes are rows; `−4.00° about +Y` **iff** they are columns. The
  only build-internal pointer (ragdoll capsules vs their bones' own reference-pose directions)
  favours the column reading, so −4.00° about +Y is the better bet — but it is a bet, not a decode.
- Anything downstream that needs the tilt's sign (box corner positions, the weapons box's placement
  in JC3 space) must carry that condition until a native `FMatrix` layout exists.

## UNKNOWNs

| # | unknown | what was tried | why it is still unknown / where it would be found |
|---|---|---|---|
| U-1 | whether the three planes of `TM` are the transform's rows or its columns (hence the tilt's sign) | decoded all three BmGame box TMs; compared both readings of all 16 floats; enumerated every `TM`(64) in 8 packages by owning class (3,693 structs); scanned the 20,151,210-byte SkeletalMesh export at all 5,037,802 float offsets for an orthonormal 3×3 in either lead layout (0 hits); decoded the mesh reference pose of the box's own bone (identity); measured 122 non-identity ragdoll capsules against their bones' own reference-pose directions; checked the box's own bone for skinned vertices (0 points) | the build stores matrices only as aggregate-geometry shape frames (no quaternion counterpart) and rotations-as-quaternions only in skeleton/anim records (no matrix counterpart); the named known case is the identity. A native struct dump for this build that fixes `FMatrix`'s row/column semantics would decide it — i.e. the G3-06 native-layout work, which `BMSDK_OFFSETS.json` shows has no `FMatrix`/`FPlane`/`FKAggregateGeom` class at all (checked: `FMatrix in classes: False`, `FKAggregateGeom in classes: False`, `FKSphylElem in classes: False`). Not guessed |
| U-2 | which local axis a ragdoll capsule's long axis is | tested all three local axes against the bone direction under both readings | the capsule is rotationally symmetric about its long axis and no field names that axis; `BMSDK_OFFSETS.json` has no `FKSphylElem`/`FKAggregateGeom` layout to name it |
| U-3 | whether the capsule evidence can be strengthened into an oracle | measured the premise first (centre vs bone direction: median 8.1°, 58/149 within 5°), then read the axis both ways on the strict subset | the premise is an art-setup assumption, and the subset is 55 capsules; the medians separate 6× but the tails overlap (23/55 vs 28/55 within 5°). Turning it into an oracle needs a rig pairing that is exact rather than chosen by a rotation-free residual |

External documentation was consulted once and is **not** used for the verdict: Unreal's `FMatrix`
exposes `XPlane/YPlane/ZPlane/WPlane` and UE's transform math is row-vector (third-party summary:
<https://rodolphe-vaillant.fr/entry/145/unreal-engine-c-tmap-doc-sheet-1>; Epic's API reference for
`Matrix`: <http://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/Matrix>). This
build serialises those planes as `(W,X,Y,Z)` — not the documented `(X,Y,Z,W)` field order — so the
documented convention cannot be transferred to these bytes without a native dump of this build's
own struct.
