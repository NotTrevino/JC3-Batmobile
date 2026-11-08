# chase-G3-01b-boxes-u2 — which element type's count is the zero before the convex count

**STATUS: resolved**

The `u32 0` at **byte 244 of export 169750** (`Batmobile_Chassis`) and at**byte 126 of export 169751** (`Batmobile_Rig_Weapons_Trans`) is the **sphyl (capsule) count** — the third of four
interleaved `[u32 count][elements...]` arrays:

```
[ nSphere ][ sphere elems ][ nBox ][ box elems ][ nSphyl ][ sphyl elems ][ nConvex ][ convex elems ][ 9-byte zero footer ]
```

So the aggregate is **not** a 16-byte header of four counts (`grab_collision_geom.py`'s
docstring guess); each count sits immediately before its own array. The convex count is the
`u32` *after* the zero: byte **248** in 169750, byte **130** in 169751.

Decided by bodies that actually carry spheres and capsules, found in the cooked packages:

| | count 1 (sphere) | count 2 (box) | count 3 (sphyl) | count 4 (convex) |
|---|---|---|---|---|
| where | `payload+0` | after the sphere array | `payload + boxes_end` | after the sphyl array |
| element | TM + **1** float (0x40) + bool 0x44 + end = **102 B** | TM + **3** floats (0x40/44/48) + bool 0x4C + end = **118 B** (G3-01b) | TM + **2** floats (0x40/0x44) + bool 0x48 + end = **110 B** | G3-01c's layout, starts with a raw `u32` vertex count |
| bodies in the fleet scan | 25 | 3119 elements | 271 | 165+ |

Example, `BmGame.upk` export 169746, bone `Baseball_bat_anim_01`: counts `[0, 0, 1, 0]`, one
110-byte element, TM identity, radius **6.779 cm**, length **113.5 cm** — a bat. Export 169758,
bone `Bip01_L_Thigh`: `[0, 0, 3, 0]`, three capsules. Export 169853, bone `Bip01_Head`:
`[1, 0, 1, 0]`, one sphere of radius **9.72 cm** (a head) plus one capsule.

## Files written

| file | what |
|---|---|
| `Tools/scripts/grab_collision_shapes.py` | the tool (`--write` / `--check`), new |
| `Research/BatmobileGrab/COLLISION_SHAPES.md` | the record (11,199 B, generated) |
| `Research/BatmobileGrab/COLLISION_SHAPES.json` | the same as data (393,498 B) |
| `tmp/freebuff/reports/chase-G3-01b-boxes-u2.md` | this report |

Nothing else was written. G3-01b's `grab_collision_boxes.py` / `COLLISION_BOXES.*`, G3-01c's
`grab_collision_convex.py`, `grab_collision_geom.py`, `grab_physics.py` and `upk_read.py` are
untouched (`git status` lists only the three new files above as untracked from this task);
`grab_collision_shapes.py` *imports* `upk_read` and `grab_collision_convex.parse_element`
read-only, the same way G3-01b imports G3-01c. Read-only on the game install; no game process
started; no git commit/push.

## What the bytes say

1. **The parse.** `parse_aggregate()` reads three shaped arrays and the convex array in the
   order above and then requires exactly the 9-byte zero footer. Over **3,276 bodies in 4
   packages (BmGame 1081, Startup 2099, StartupPatch 260, Orphan 269)**: **3,276 exact, 0
   non-exact, 0 parse errors**. 433 further `RB_BodySetup` exports carry no `AggGeom` tag at
   all and are excluded.
2. **The two G3-01b bodies.** 169750: counts `[0, 2, 0, 1]`, payload 1759 B, boxes end at
   **244** = the sphyl count (0), convex count at **248** (1), exact, footer 9 B. 169751:
   `[0, 1, 0, 0]`, 143 B, boxes end at **126** = sphyl count (0), convex count at **130** (0),
   exact, footer 9 B.
3. **Oracles actually run** (all numbers in the generated `.md`):
   - payload closes to the 9-byte footer on 3276/3276 bodies (decoded);
   - every element of an array carries that shape's exact field set — sphere 36/36 with only
     float 0x40 and bool 0x44, box 3119/3119 with 0x40/0x44/0x48 + bool 0x4C, sphyl 300/300 with
     0x40/0x44 + bool 0x48 (0 exceptions of any kind);
   - TM orthonormal with det +1 on 36/36 spheres and 300/300 sphyls; 230/300 capsules carry a
     non-identity rotation, i.e. the TM is the shape's own frame;
   - radii/lengths all positive: 36/36 sphere radii in 6.13–160.0 cm, 300/300 capsule radius
     2.15–29.15 cm and length 2.59–944.5 cm;
   - bone-name oracle: array-1 (sphere) elements sit on `Head`, `Pelvis`, `Spine` bones,
     array-3 (sphyl) elements on `Thigh`, `Calf`, `Foot`, `Clavicle`, `UpperArm`, `Forearm`,
     `Hand`, `Neck` bones — round joints vs limbs;
   - 16 bodies carry spheres **and** capsules in one payload (`Assault_Rifle_Physics`, counts
     `[2, 1, 1, 0]`), so the two arrays are not one-or-the-other;
   - the 3rd slot in a body with capsules starts with `u32 10` (StructProperty) + name index
     78655 = `TM`; the 4th slot in 169748/169749/169750 starts with `u32 10 / 8 / 12` = its own
     `nV` and no TM tag.
4. **One hypothesis refuted on the way** (kept in the output as refuted): *"a wrong array order
   cannot close, so byte accounting alone fixes the order"* — **false**. Re-running the same
   parser with `sphyl` first over the 280 bodies that carry a shaped array closes **280/280**
   exactly, because a shaped element's field tags are self-terminating. What actually decides
   the order is the per-array field set (1 float vs 2 floats vs 3) plus the bone-name oracle,
   which is what the report claims.

## Commands and outputs (verbatim)

Exploration (scratch, kept under `tmp/freebuff/scratch/`):

```
$ python tmp/freebuff/scratch/g301x_1.py BmGame.upk Ace_B2_Ch2z_Physics.upk
== BmGame.upk: 1081 bodies, 3.4s
   header (0, 1, 10, 78655) x 678
   header no-agg x 250
   header (0, 0, 1, 10) x 121
   header (0, 0, 2, 10) x 10
   header (1, 10, 78655, 0) x 7
   header (2, 10, 78655, 0) x 5
   header (0, 2, 10, 78655) x 3
   header (0, 3, 10, 78655) x 2
   header (0, 0, 0, 43) x 1
   header (0, 0, 0, 13) x 1
   header (0, 0, 3, 10) x 1
   header (0, 7, 10, 78655) x 1
   bodies with nonzero 1st/3rd/4th word: 831
      (169740, 'RB_BodySetup', (0, 1, 10, 78655), 143)
      ...
      (169744, 'RB_BodySetup', (2, 10, 78655, 0), 457)
      (169746, 'RB_BodySetup', (0, 0, 1, 10), 135)
      (169750, 'RB_BodySetup', (0, 2, 10, 78655), 1759)
== Ace_B2_Ch2z_Physics.upk: 0 bodies
   bodies with nonzero 1st/3rd/4th word: 0
```
(the words `10, 78655` are the StructProperty tag / `TM` name index, i.e. a shaped element
starts there — so counts 1 and 3 are non-zero on real bodies)

```
$ python tmp/freebuff/scratch/g301x_4.py        # first full parse with the derived order
bodies 1081
count hist:
    (0, 1, 0, 0) x 673
    no-agg x 250
    (0, 0, 1, 0) x 121
    (0, 0, 2, 0) x 10
    (1, 0, 1, 0) x 6
    (0, 2, 0, 1) x 3
    (2, 0, 0, 0) x 3
    (0, 1, 0, 1) x 2
    (0, 1, 2, 0) x 2
    (2, 1, 1, 0) x 1
    (0, 0, 0, 43) x 1
    (0, 0, 0, 13) x 1
    (1, 0, 0, 0) x 1
    (0, 0, 3, 0) x 1
    (0, 1, 1, 0) x 1
    (2, 0, 1, 0) x 1
    (0, 3, 0, 0) x 1
    (0, 7, 0, 0) x 1
    (0, 3, 0, 2) x 1
    (0, 0, 0, 1) x 1
accounting failures: 0
bodies with spheres: 12
     (169744, 'Assault_Rifle_Physics.RB_BodySetup', [8.0, 8.768])
     (169754, 'Sphere.RB_BodySetup', [160.0])
     (169853, 'Joker_BM3_Ragdoll.RB_BodySetup', [9.72])
     ...
bodies with sphyls: 143
     (169744, 'Assault_Rifle_Physics.RB_BodySetup', [[7.711, 15.0]])
     (169746, 'Weapons_Baseball_Bat_btm_broken_Physics.RB_BodySetup', [[6.779, 113.5]])
     (169747, 'Weapons_Baseball_Bat_top_broken_Physics.RB_BodySetup', [[4.674, 68.0]])
     (169756, 'GCPD_Cop_Ragdoll_NewJacket.RB_BodySetup', [[15.494, 10.984]])
     ...
```

```
$ python tmp/freebuff/scratch/g301x_2.py        # tags of the decisive bodies (abridged)
== 169754 Sphere.RB_BodySetup
    {'type': 'ByteProperty', 'name': 'PreCachedPhysDataVersion', 'size': 1, 'at': 20, 'value': 5}
    {'type': 'StructProperty', 'name': 'AggGeom', 'size': 127, 'at': 41}
== 169750 Batmobile_V3_Physics.RB_BodySetup
    {'type': 'NameProperty', 'value': 'Batmobile_Chassis', 'at': 25}
    {'type': 'StructProperty', 'name': 'AggGeom', 'size': 1759, 'at': 61}
== 169758 GCPD_Cop_Ragdoll_NewJacket.RB_BodySetup
    {'type': 'NameProperty', 'value': 'Bip01_L_Thigh', 'at': 25}
    {'type': 'StructProperty', 'name': 'AggGeom', 'size': 355, 'at': 69}
== 169746 Weapons_Baseball_Bat_btm_broken_Physics.RB_BodySetup
    {'type': 'NameProperty', 'value': 'Baseball_bat_anim_01', 'at': 25}
    {'type': 'StructProperty', 'name': 'AggGeom', 'size': 135, 'at': 53}
```

```
$ python tmp/freebuff/scratch/g301x_3.py        # hex dump with offsets (abridged to the tails)
export 169754 Sphere.RB_BodySetup payload 127
0050  cc 37 bb b6 ac 7b 52 b7 04 00 40 00 00 00 20 43
0060  03 00 44 00 00 00 00 00 00 00 ...
export 169746 Weapons_Baseball_Bat_btm_broken_Physics.RB_BodySetup payload 135
0050  00 00 80 3f 00 00 00 c0 00 00 00 00 00 00 f0 40
0060  04 00 40 00 66 f0 d8 40 04 00 44 00 00 00 e3 42
0070  03 00 48 00 00 00 00 00 ...
```
(169754: 1 float tag at 0x58 then a bool tag; 169746: two float tags 0x60/0x68 then the bool —
the 8-byte difference that makes the two arrays different shapes)

```
$ python tmp/freebuff/scratch/g301x_6.py        # first prefilter attempt - WRONG ASSUMPTION
files 3266 candidates 0 header errors 0 name bytes total 104.1 MB candidate bytes 0.0 MB t=11.9s
```
That zero was the tool's bug, not an absence: BmGame.upk is a **chunked** package, so its name
table lives in the decompressed image, not at `name_offset` in the raw file:

```
$ python -c "... print(pkg.image is pkg.raw, len(pkg.image), len(pkg.raw)) ..."
image is raw: False 356085334 214757637
in image: 1 in raw: 0
```

Fixed by decompressing only as much of each package as the name table needs
(`image_prefix()`); the prefilter then ran:

```
$ python -c "import sys;sys.path.insert(0,'Tools/scripts');import grab_collision_shapes as S;..." 
files 3266 hits 4 errs 0 truncated 0 t=26.5s
first hits ['BmGame.upk', 'Orphan.upk', 'Startup.upk', 'StartupPatch.upk']
errs []
```

Bone-name pairing over BmGame (which array a body's non-zero count belongs to, vs its bone):

```
$ python -c "... walks every RB_BodySetup of BmGame.upk ..."
SPHERE bodies:
   (169744, 'Assault_Rifle', 'Assault_Rifle_Physics', 2)
   (169754, None, 'Sphere', 1)
   (169853, 'Bip01_Head', 'Joker_BM3_Ragdoll', 1)
   (169917, 'Bip01_Head', 'Joker_BM3_Thug_Ragdoll', 1)
   (169982, 'Bip01_Pelvis', 'Thug_Ragdoll', 2)
   (169992, 'Bip01_L_UpperArm', 'Thug_Ragdoll', 1)
   (170001, 'Bip01_R_UpperArm', 'Thug_Ragdoll', 1)
   (170036, 'Bip01_Spine', 'Penguin_Thug_Ragdoll', 2)
   (170047, 'Bip01_Spine1', 'Penguin_Thug_Ragdoll', 2)
   (170133, 'Bip01_Spine2', 'Thug_Rioters_Ragdoll', 2)
   (170154, 'Bip01_L_UpperArm', 'Thug_TwoFace_Ragdoll', 1)
   (170163, 'Bip01_R_UpperArm', 'Thug_TwoFace_Ragdoll', 1)
```
(the capsule side of that listing printed the raw header words, not counts — the proper parse in
the final tool replaced it)

Final tool:

```
$ time timeout 580 python Tools/scripts/grab_collision_shapes.py --write
wrote COLLISION_SHAPES.json and COLLISION_SHAPES.md (3276 bodies scanned, 25 sphere bodies, 271 capsule bodies, 11/11 checks)

real    0m30.594s

$ time timeout 580 python Tools/scripts/grab_collision_shapes.py --check; echo "CHECK_EXIT=$?"
OK: sphyl (capsule) - array 3 of the four [u32 count][elements] arrays; 11/11 checks; bodies 3276, sphere bodies 25, capsule bodies 271
CHECK_EXIT=0

real    0m29.931s
```

The 11 checks, as printed into `COLLISION_SHAPES.md` §4, all PASS: the two G3-01b bytes are
array counts (244→sphyl, 126→sphyl); both bodies agree on the same array; 3276/3276 payloads
close to the 9-byte footer; 25 sphere bodies / 36 elements with radius > 0; 271 sphyl bodies /
300 elements with both floats > 0; TM orthonormal 36/36 and 300/300; 16 bodies carry both
arrays; shaped elements are TM StructProperty records while convex elements are raw vertex
counts; element sizes are single-valued per kind (sphere 102, box 118, sphyl 110); every element
carries its shape's exact field set (36/3119/300 ok, 0 other).

## UNKNOWNs

| item | status | what was tried / what would decide it |
|---|---|---|
| the FName of the sphyl's two floats (`radius`, `length`) | UNKNOWN (assignment **derived** from magnitudes: 0x44 = 113.5 cm on a bat, 0x40 = 6.78 cm) | the payload stores simple types by offset only; `BMSDK_OFFSETS.json` has no `FKSphylElem`/`FKSphereElem`/`FKAggregateGeom` layout. Would need an engine struct dump (G3-06-style native layout). |
| the BoolProperty inside a sphere (0x44) / sphyl (0x48) element | UNKNOWN | decoded the tag and every element's word; same status as G3-01b's box bool 0x4C. No local layout names the bit; a struct dump would. |
| whether a 1-float element could be a degenerate capsule (length 0) | recorded, not distinguished | a capsule with zero length *is* a sphere, so the label does not change any decoded byte; the report names the 1-float array "sphere" because it has exactly one dimension and sits on head/pelvis/spine bones. |
| further `AggGeom` payload variants outside these 4 packages | none found | the prefilter examined all 3,266 `.upk` name tables (0 truncated) and found `RB_BodySetup` in only 4 packages; `.tfc` files hold no packages. |
