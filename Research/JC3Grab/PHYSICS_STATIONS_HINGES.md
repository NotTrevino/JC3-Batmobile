# Do the wheel-station quads coincide with G3-10e's hinge pivots?

**Answer: no** - the quads are not hinge pivots, and the rectangle heuristic is not confirmed by G3-10e's constraints.  Not one of the 24 station quads in the six distinct `.physicsc` files (4 per file, 68 across the 17 entities) is a hinge pivot: the closest quad-to-pivot distance in any file is **0.404 m**, the median **0.835 m**, the farthest **1.428 m**, over the 64 hinge pivots those six files carry.  What the quads *are* is decoded in §3: the position field of four entries of a 96-byte table inside `hknpPhysicsSystemData`.

Read `PHYSICS.md`'s 17/17 agreement as what it is: the four quads equal the four named `land_global.base_wheel_hardpoint_positions` (re-derived here, 17/17), i.e. a bytes-vs-name check.  What the quads are is settled by the surrounding bytes, not by the hinges.

## 1. Inputs

| input | what |
|---|---|
| `E:/Modding/_gamedata/JC3grab\phys` | the 232 per-entity `.physicsc` grabs, of which **17** have one station set |
| `Research/JC3Grab/PHYSICS_LIMITS.json` | G3-10e's hinge decode: 419 `hkpLimitedHingeConstraintData`, frames A/B |
| `Research/JC3Grab/PHYSICS_LIMITS.md` | the station method being checked |

The 17 entities are **6 distinct `.physicsc` files** - the variants of a car share one; the tables below are per file.

## 2. Stations against hinge pivots, per model

`nearest` = Euclidean distance from a station quad to the closest hinge pivot (frame A) in the same file.  Frame B carries the **same translation** as frame A in 64 of 64 hinges, so both frames were tested and only A is shown.

| `.physicsc` | entities | hinges | track | wheelbase | nearest pivot distances (4 quads) |
|---|---:|---:|---:|---:|---|
| `oldcampervan.physicsc` | 3 | 11 | 1.34 | 2.465 | 0.822, 0.930, 0.849, 0.835 |
| `modernsaloon.physicsc` | 3 | 10 | 1.772 | 3.197 | 0.752, 0.404, 0.410, 1.228 |
| `sportsmuscle.physicsc` | 3 | 9 | 1.77 | 3.003 | 0.827, 0.827, 1.107, 1.428 |
| `modernsedan.physicsc` | 3 | 8 | 1.636 | 2.418 | 0.663, 0.529, 0.408, 1.154 |
| `oldcompact.physicsc` | 2 | 10 | 1.47 | 2.804 | 0.791, 0.632, 0.830, 1.028 |
| `smalltank.physicsc` | 3 | 16 | 2.462 | 3.228 | 0.952, 0.938, 0.841, 0.846 |

Distance distribution over all 24 quads: **min 0.404**, median **0.835**, max **1.428**.  Quads within 1 mm of a pivot: **0**; within 1 cm: **0**; within 5 cm: **0**; within 20 cm: **0**.

Decoded: the pivots reach y = 2.663 m, far above every station's single hub height (y = 0.316 … 0.615 m across the six files).  `derived`: the hinges are body-panel joints (the decoded limit pairs are door-like: `0..80`, `-35..0`, `-15..0`, `0..30/70/90` deg, and 50 of the 64 pivots sit on the body sides at |x| 0.323-1.144 m and 14 on the centre line at |x| <= 0.1 m), while the quads sit at wheel-centre height.  Which panels they are is UNKNOWN.  The nearest pivot to a station is the outboard hinge of the same corner.

## 3. What the quads are

Every station quad is the **first field of a 96-byte entry** in one contiguous run of entries inside the `hknpPhysicsSystemData` object of the same file:

| entry offset | bytes | reading |
|---:|---|---|
| +0x00 | `float4` | **position**, `(x, y, z, 1.0)` - this is the station quad |
| +0x10 | `float4` | `(0, 0, 0, 0.99999994)` - unit quaternion, i.e. no rotation |
| +0x20 | 16 B | zero |
| +0x30 | `u32 u32 i32 u16` | `0`, `0`, `0x7fffffff`, **id** |
| +0x40 | `u16 u16` | a flag (`1` or `255`) and the same **id** |
| +0x50 | 16 B | zero |

Decoded facts about the run (each re-derived by `--check`):

| file | entries | ids | the four wheel ids | entries with a non-zero position | flags seen |
|---|---:|---|---|---:|---|
| `oldcampervan.physicsc` | 51 | 1..51 | [39, 40, 41, 42] | **4** | 255 |
| `modernsaloon.physicsc` | 41 | 1..41 | [34, 35, 36, 37] | **4** | 1, 255 |
| `sportsmuscle.physicsc` | 41 | 1..41 | [23, 24, 37, 38] | **4** | 1, 255 |
| `modernsedan.physicsc` | 49 | 1..49 | [40, 41, 42, 43] | **4** | 1, 255 |
| `oldcompact.physicsc` | 47 | 1..47 | [41, 42, 43, 44] | **4** | 1, 255 |
| `smalltank.physicsc` | 36 | 1..36 | [33, 34, 35, 36] | **4** | 255 |

So the four quads are four entries of **one contiguous table** in the same object, and they are the **only** entries of it that carry a non-zero position (4 of 51, 41, 41, 49, 47, 36).  Their ids are consecutive in **5 of the 6 files** and split 2+2 in `sportsmuscle.physicsc` (oldcampervan 39-42; modernsaloon 34-37; sportsmuscle 23/24/37/38; modernsedan 40-43; oldcompact 41-44; smalltank 33-36), so 'consecutive' is a property of five files, not a rule.  Every one of the four carries the identity rotation.  The entry type's Havok name is **UNKNOWN** (§6): the container class is decoded from the packfile's own class name, and the four entries are the wheel poses because their positions equal the four named wheel hardpoints (re-derived here, 17/17).

Container per file:

| `.physicsc` | class | object offset | extent | quad offsets inside it |
|---|---|---:|---:|---|
| `oldcampervan.physicsc` | `hknpPhysicsSystemData` | 0xA0 | 26912 B | [17968, 18064, 18160, 18256] |
| `modernsaloon.physicsc` | `hknpPhysicsSystemData` | 0xA0 | 22256 B | [14768, 14864, 14960, 15056] |
| `sportsmuscle.physicsc` | `hknpPhysicsSystemData` | 0xA0 | 20912 B | [13712, 13808, 15056, 15152] |
| `modernsedan.physicsc` | `hknpPhysicsSystemData` | 0xA0 | 25136 B | [17520, 17616, 17712, 17808] |
| `oldcompact.physicsc` | `hknpPhysicsSystemData` | 0xA0 | 24704 B | [17072, 17168, 17264, 17360] |
| `smalltank.physicsc` | `hknpPhysicsSystemData` | 0xA0 | 18272 B | [13312, 13408, 13504, 13600] |

## 4. Why the hinges are not the answer

- The hinge pivots live in separate `hkpLimitedHingeConstraintData` objects (304 B each), not in the `hknpPhysicsSystemData` table the quads sit in.
- A car with 16 hinges (the tank) has four station quads; a car with 8 hinges (the sedan) has four.  The count does not track.
- The pivots spread over these y ranges, one per file: oldcampervan 0.372-1.351, modernsaloon 0.583-1.112, sportsmuscle 0.209-1.440, modernsedan 0.363-1.448, oldcompact 0.534-1.034, smalltank 0.586-2.663; the quads of a car all sit at a single y (0.316 … 0.615 m).
- Both frames of every hinge carry the same translation, so a pivot is one point in vehicle space; the quads are 0.40-1.43 m away from the nearest of them.

## 5. Oracles

| oracle | result |
|---|---|
| `four_quads_per_entity` | **pass** |
| `variants_of_one_car_agree` | **pass** |
| `quads_inside_system_object` | **pass** |
| `quads_are_distinct_table_entries` | **pass** |
| `only_wheel_entries_have_a_position` | **pass** |
| `station_rotation_is_identity` | **pass** |
| `named_hardpoints_agree` | **pass** |
| `no_quad_is_a_hinge_pivot` | **pass** |
| `hinge_frames_share_the_pivot` | **pass** |

`four_quads_per_entity` and `variants_of_one_car_agree` cover the 17 entities / 6 files.  `only_wheel_entries_have_a_position` is the sharp one: 4 of N entries (N = 51, 41, 41, 49, 47, 36) are non-zero and they are exactly the station quads - an arbitrary float4 would not come with an id, a repeated id, the `0x7fffffff` sentinel and a unit quaternion in the next 16 bytes.  `no_quad_is_a_hinge_pivot` fails if any quad comes within 20 cm of any pivot; the closest is 0.404 m, so it clears its bar by 2x.

## 6. UNKNOWNs

- **The 96-byte entry's Havok type name.**  No Havok 2014.1 header or type library is in this project.  Fields are labelled by their decoded shape (float4 position with `w == 1.0`, unit quaternion, sentinel `0x7fffffff`, repeated id), never by a name.
- **The meaning of the `u16` flag at +0x40** (`1` in some files, `255` in others) and of the two zero `u32` at +0x30.
- **Why the run is as long as it is** (e.g. 51 entries in the campervan) and why the wheel ids differ per file ([39, 40, 41, 42], [34, 35, 36, 37], [23, 24, 37, 38], [40, 41, 42, 43], [41, 42, 43, 44], [33, 34, 35, 36] in the six files): the table's other entries are all `(0, 0, 0)`, so the file does not say what they stand for.
- **Whether the game uses a hinge or a raycast for these wheels**: no wheel constraint object appears in the six files (all hinges are `hkpLimitedHingeConstraintData`, 304 B), but a raycast wheel model would live in the vehicle's run-time data, which is not in `.physicsc`.

## 7. Tool

```
python Tools/scripts/jc3_stations_vs_hinges.py --write   # this page + the JSON
python Tools/scripts/jc3_stations_vs_hinges.py --check   # re-derive, diff, exit 1 on drift
```

G3-10e's own `jc3_physics_limits.scan` is imported and run on the same bytes (through a byte-identical temp copy, deleted after use), so the hinge side of this check is their decoder, not a re-implementation.
