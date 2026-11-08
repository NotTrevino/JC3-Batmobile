# DONE — wheel stations vs G3-10e's hinge pivots

STATUS: done

**They do not coincide. The four station quads are not hinge pivots** — and the earlier
rectangle heuristic is therefore *not* confirmed by a decoded structure; it is confirmed only
by the named `land_global.base_wheel_hardpoint_positions` (17/17, re-derived here). What the
quads *are* is now decoded: the position field of four entries of a 96-byte table inside the
`hknpPhysicsSystemData` object — entries that are the only non-zero positions in that table.

Numbers (all re-derived by `--check` from the shipped bytes):

| measurement | value |
|---|---|
| station entities / distinct `.physicsc` files | 17 / **6** (variants of a car share one file) |
| station quads vs hinge pivots | 24 quads (68 entity-quads) against 64 pivots (419 fleet-wide) |
| nearest quad→pivot distance | **min 0.404 m**, median **0.835 m**, max **1.428 m** |
| quads within 1 mm / 1 cm / 5 cm / 20 cm of a pivot | **0 / 0 / 0 / 0** |
| hinge frames A vs B translation | identical in **64 / 64** hinges, so each hinge is one pivot point |
| the quads' container | the `hknpPhysicsSystemData` object (offset 0xA0 in all six files) |
| non-zero positions in that table | **4 of N** (N = 51, 41, 41, 49, 47, 36) and they are exactly the 4 quads |

Per file (nearest pivot distance for the four quads, and the decoded y range of that file's pivots):

| `.physicsc` | entities | hinges | quad→pivot distances | pivot y range |
|---|---:|---:|---|---|
| `oldcampervan` | 3 | 11 | 0.822, 0.930, 0.849, 0.835 | 0.372–1.351 |
| `modernsaloon` | 3 | 10 | 0.752, 0.404, 0.410, 1.228 | 0.583–1.112 |
| `sportsmuscle` | 3 | 9 | 0.827, 0.827, 1.107, 1.428 | 0.209–1.440 |
| `modernsedan` | 3 | 8 | 0.663, 0.529, 0.408, 1.154 | 0.363–1.448 |
| `oldcompact` | 2 | 10 | 0.791, 0.632, 0.830, 1.028 | 0.534–1.034 |
| `smalltank` | 3 | 16 | 0.952, 0.938, 0.841, 0.846 | 0.586–2.663 |

The stations sit at one hub height per car (y = 0.316 … 0.615 m); the pivots do not.

## What the quads are (decoded)

Every station quad is at **+0x00 of a 96-byte entry** in one contiguous table inside the
`hknpPhysicsSystemData` object. The entry, read field by field:

| offset | bytes | reading |
|---:|---|---|
| +0x00 | `float4` | **position** `(x, y, z, 1.0)` — this is the station quad |
| +0x10 | `float4` | `(0, 0, 0, 0.99999994)` — unit quaternion, no rotation |
| +0x20 | 16 B | zero |
| +0x30 | `u32 u32 i32 u16` | `0`, `0`, `0x7fffffff`, **id** |
| +0x40 | `u16 u16` | a flag (`1` or `255`) and the same **id** |
| +0x50 | 16 B | zero |

Facts, each checked across all six files: the four entries are the only ones with a non-zero
position; their ids are consecutive in 5 of 6 files (`oldcampervan 39-42`, `modernsaloon 34-37`,
`modernsedan 40-43`, `oldcompact 41-44`, `smalltank 33-36`) and split 2+2 in `sportsmuscle`
(`23`, `24`, `37`, `38`); all four carry the identity rotation. The entry's Havok type **name**
is UNKNOWN (no 2014.1 header in this project) — the container class name is decoded from the
packfile itself.

Why the four are the wheels: their positions equal the four named
`base_wheel_hardpoint_positions` (17/17), and they are 4 of N table entries, the other N−4
being `(0, 0, 0)`.

## Why no hinge can be the station

- The pivots live in separate `hkpLimitedHingeConstraintData` objects (304 B, extent uniform),
  a different object from the `hknpPhysicsSystemData` table the quads sit in.
- Hinge count does not track: 8 hinges (`modernsedan`) and 16 (`smalltank`) both have exactly
  four station quads.
- The decoded limit pairs are door-like (`0..80`, `-35..0`, `-15..0`, `0..30/70/90` deg), the
  pivots sit at |x| 0.32–1.14 m on the body sides (50 of 64) or on the centre line (14 of 64),
  and reach y = 2.663 m — none of that is a wheel.
- No wheel/vehicle constraint class exists in these six files at all (class census: no name
  containing `Wheel` or `Vehicle`).

## Files written

| file | what |
|---|---|
| `Tools/scripts/jc3_stations_vs_hinges.py` | new; `--write` regenerates both artifacts, `--check` re-derives every number and diffs them (exit 1 on drift) |
| `Research/JC3Grab/PHYSICS_STATIONS_HINGES.md` | the rendered answer: per-file distances, the 96-byte entry decode, oracles, UNKNOWNs |
| `Research/JC3Grab/PHYSICS_STATIONS_HINGES.json` | the same, machine-readable (per-entity quads, every pivot, table ids, checks) |

Nothing else was modified: `PHYSICS.md`, `PHYSICS_LIMITS.*` and the `phys` grabs are read-only
inputs here. The hinge side is G3-10e's own decoder (`jc3_physics_limits.scan` imported and run
on the same bytes through a byte-identical temp copy), not a re-implementation.

## Commands and output

`uv run python Tools/scripts/jc3_stations_vs_hinges.py --write`:

```
wrote Research\JC3Grab\PHYSICS_STATIONS_HINGES.json
wrote Research\JC3Grab\PHYSICS_STATIONS_HINGES.md
answer: no
  four_quads_per_entity              pass
  variants_of_one_car_agree          pass
  quads_inside_system_object         pass
  quads_are_distinct_table_entries   pass
  only_wheel_entries_have_a_position pass
  station_rotation_is_identity       pass
  named_hardpoints_agree             pass
  no_quad_is_a_hinge_pivot           pass
  hinge_frames_share_the_pivot       pass
```

`uv run python Tools/scripts/jc3_stations_vs_hinges.py --check` (final run):

```
json: PASS
md:   PASS
  four_quads_per_entity              pass
  variants_of_one_car_agree          pass
  quads_inside_system_object         pass
  quads_are_distinct_table_entries   pass
  only_wheel_entries_have_a_position pass
  station_rotation_is_identity       pass
  named_hardpoints_agree             pass
  no_quad_is_a_hinge_pivot           pass
  hinge_frames_share_the_pivot       pass
check: PASS
exit=0
```

Exploration that produced the answer — `uv run python tmp/freebuff/scratch/h4.py` (stations vs
hinge pivots, all 17 entities; abridged to the columns that matter):

```
cars with one station set: 17
v0002_car_autostraad_oldcampervan_civilian_01. hinges 11 A==B 11  quads [(-0.67, 0.333, -1.265), (0.67, 0.333, -1.265), (-0.67, 0.333, 1.2), (0.67, 0.333, 1.2)]  min-dist [0.8218, 0.9296, 0.8493, 0.8354]
v0009_car_autostraad_modernsaloon_civilian_01. hinges 10 A==B 10  quads [(-0.886, 0.342, -1.469), (0.886, 0.342, -1.469), (-0.886, 0.342, 1.728), (0.886, 0.342, 1.728)]  min-dist [0.7517, 0.4035, 0.4101, 1.2285]
v0300_car_kensington_sportsmuscle_civilian_01. hinges  9 A==B  9  quads [(-0.885, 0.4, -1.557), (0.885, 0.4, -1.557), (-0.885, 0.4, 1.446), (0.885, 0.4, 1.446)]  min-dist [0.8273, 0.8273, 1.1069, 1.428]
v0502_car_solar_modernsedan_civic_police_01.ee hinges  8 A==B  8  quads [(-0.818, 0.316, -1.114), (0.818, 0.316, -1.114), (-0.818, 0.316, 1.304), (0.818, 0.316, 1.304)]  min-dist [0.6632, 0.529, 0.408, 1.1544]
v0508_car_solar_oldcompact_civilian_01.ee hinges 10 A==B 10  quads [(-0.735, 0.321, -1.374), (0.735, 0.321, -1.374), (-0.735, 0.321, 1.43), (0.735, 0.321, 1.43)]  min-dist [0.791, 0.6322, 0.8298, 1.0285]
v0603_car_urga_smalltank_debug.ee              hinges 16 A==B 16  quads [(-1.231, 0.615, -1.598), (1.231, 0.615, -1.598), (-1.231, 0.615, 1.63), (1.231, 0.615, 1.63)]  min-dist [0.9518, 0.9378, 0.8412, 0.8458]

all 68 quads: min 0.4035 median 0.8354 max 1.428
within 1e-3: 0 1e-2: 0 0.05: 0 0.2: 0
```

`uv run python tmp/freebuff/scratch/h7.py` (top-level context of the first station quad — the
96-byte entry, `+0` is the quad; abridged):

```
quad at +14768
     -96  00 00 00 00 00 00 00 00 00 00 00 00 00 00 80 3f
     -48  00 00 00 00 00 00 00 00 ff ff ff 7f 21 00 00 00
     -32  01 00 21 00 00 00 00 00 00 00 00 00 00 00 00 00
      +0  e5 d0 62 bf a0 1a af 3e 30 08 bc bf 00 00 80 3f
     +16  00 00 00 00 00 00 00 00 00 00 00 00 ff ff 7f 3f
     +32  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
     +48  00 00 00 00 00 00 00 00 ff ff ff 7f 22 00 00 00
     +64  01 00 22 00 00 00 00 00 00 00 00 00 00 00 00 00
     +80  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  fields at quad: pos (-0.886, 0.342, -1.469, 1.0)  next16 as float4 (0.0, 0.0, 0.0, 1.0)
  +0x30 (0, 0, 2147483647, 34)
  +0x40 (1, 34)
```

`uv run python tmp/freebuff/scratch/h8.py` (every entry of the campervan table, abridged):

```
v0002_car_autostraad_oldcampervan_civilian_01.ee  extent 26912  records 51  hinges 11
  +14320 id  1 flag 255 pos    0.000    0.000    0.000  nearest pivot 1.448
  ...
  +17968 id 39 flag 255 pos   -0.670    0.333   -1.265  nearest pivot 0.822 <- STATION
  +18064 id 40 flag 255 pos    0.670    0.333   -1.265  nearest pivot 0.930 <- STATION
  +18160 id 41 flag 255 pos   -0.670    0.333    1.200  nearest pivot 0.849 <- STATION
  +18256 id 42 flag 255 pos    0.670    0.333    1.200  nearest pivot 0.835 <- STATION
  ...
  +19120 id 51 flag 255 pos    0.000    0.000    0.000  nearest pivot 1.448
```

Class census over the six files (`uv run python - <<'PY'` with `jc3hkx.Packfile`):

```
oldcampervan.physicsc wheel/vehicle classes: none | hinge extents: [304]
modernsaloon.physicsc wheel/vehicle classes: none | hinge extents: [304]
sportsmuscle.physicsc wheel/vehicle classes: none | hinge extents: [304]
modernsedan.physicsc wheel/vehicle classes: none | hinge extents: [304]
oldcompact.physicsc wheel/vehicle classes: none | hinge extents: [304]
smalltank.physicsc wheel/vehicle classes: none | hinge extents: [304]
```

## UNKNOWNs

- **The 96-byte entry's Havok type name.** No Havok 2014.1 header or type library exists in this
  project, so the entry is reported by its decoded shape only. Where it would be found: a Havok
  2014.1 type library or the packfile's own type section, which `jc3hkx` does not parse.
- **The meaning of the `u16` at +0x40** (`1` in some files, `255` in others) and of the two zero
  `u32` at +0x30, beyond the repeated id and the `0x7fffffff` sentinel.
- **What the other N−4 entries of the table stand for** (all `(0, 0, 0)`) and why the wheel ids
  differ per file (39-42, 34-37, 23/24/37/38, 40-43, 41-44, 33-36).
- **Which body panels the hinges are.** Decoded: pivots, limits (door-like pairs), object class.
  Not decoded: a name per hinge. A rendered pose or a per-hinge name in a module would settle it.
- **Whether the wheels are simulated as hinges or raycasts.** No wheel constraint object exists
  in the six files; a raycast model would live in run-time vehicle data, which is not in
  `.physicsc`.
