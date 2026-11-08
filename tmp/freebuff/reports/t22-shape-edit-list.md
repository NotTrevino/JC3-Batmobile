# T-22 — the exact shape edits for the two missing BmAK boxes (plan only)

Read for this note: `Working/Translation/T22_REOPEN.md` (the S1-S5 table, `:26-32`), the box table in
`Research/BatmobileGrab/COLLISION_WHERE.md` (§Bodies, `:20-21`), and the built file's own bytes,
`Working/Collision/batmobile.physicsc`. **Nothing was applied.** The built file's sha256 is
`192c12479d81da6e…` before and after this task, and `t22_shape_edits.json` records `applied: false`
on every edit.

Machine-readable list: `Working/Prep/t22_shape_edits.json` — **8 edits**, 4 per missing shape.

## 0. The two shapes and the two slots

`T22_REOPEN.md:26-32` gives the plan: **S1** (chassis box 0) is already written by B-10 into the body
hull `0x5250`; **S2** (chassis box 1, the underside box) and **S3** (the weapons pod) are the two
shapes the built set is short. The slots this plan uses are two donor bumper hulls, each already
**8 vertices / 6 planes** — a box topology, so the per-axis map produces a box, not a deformed donor
hull:

| step | BmAK box | slot hull | instance record | compound | old AABB (m) |
|---|---|---|---|---:|---|
| S2 | box 1, 679.585 x 345.688 x 103.500 cm at (0, 0, 79) — `COLLISION_WHERE.md:20` | `0x93f0` (8 v, 6 p, 400 B) | `0x8ff0` | `0x8f20` | 0.2850 x 0.1598 x 0.0477 |
| S3 | pod, 166.177 x 189.365 x 39.800 cm at (-30.5, 0, 93.25), 4.000 deg about y — `COLLISION_WHERE.md:21`, `T22_REOPEN.md:29` | `0x95d0` (8 v, 6 p, 400 B) | `0x9070` | `0x8f20` | 0.1976 x 0.1611 x 0.0566 |

Both instances carry an **identity basis and zero translation** in compound `0x8f20`, so the box lands
axis-aligned in that compound's frame; the instance translation field is what places it.

## 1. The eight edits

Offsets are data-section-relative, the convention `jc3hkx` writes with (`+ pf.base`, here `0x310`);
the absolute file offset is in the `file_offset` field of the JSON. Every object keeps its extent
(400 B), so no offset in the packfile moves.

| # | step | member | byte offset | len | old value (built file) | new value | source that states it |
|---|---|---|---|---:|---|---|---|
| 1 | S2 | `vertices` | `0x9440` | 128 | 8 float4 at hull+0x50; AABB `[0.2850, 0.1598, 0.0477]` m | 8 float4, hull centred on origin, k = 12.129613 / 6.477849 / 142.553517 | `COLLISION_WHERE.md:20` |
| 2 | S2 | `planes` | `0x94c0` | 96 | 6 float4 `(n, d)`; first `[-0.023451, -0.066441, 0.997515, 2.574357]` | 6 float4 re-derived as supporting planes of the new vertices | `COLLISION_WHERE.md:20` |
| 3 | S2 | `convex_radius` | `0x9404` | 4 | `0.01` | `0.06477849` = 0.01 x min(k) 6.477849 | `COLLISION_WHERE.md:20` |
| 4 | S2 | instance `translation` | `0x9020` | 16 | `[0, 0, 0, 1]` (w lane 1) | `[0.0, 0.79, 0.09, 1]` = box centre (0, 79, 0) cm in jc3 (x, y, z) | `COLLISION_WHERE.md:20` |
| 5 | S3 | `vertices` | `0x9620` | 128 | 8 float4 at hull+0x50; AABB `[0.1976, 0.1611, 0.0566]` m | 8 float4, k = 9.582436 / 2.470703 / 29.381876, then rotated 4 deg about jc3 x | `COLLISION_WHERE.md:21`, `T22_REOPEN.md:29` |
| 6 | S3 | `planes` | `0x96a0` | 96 | 6 float4 `(n, d)`; first `[-0.079793, 0.066059, -0.99462, -2.610928]` | 6 float4, normal `R(s^-1 n)` normalised, distance re-supported | `COLLISION_WHERE.md:21` |
| 7 | S3 | `convex_radius` | `0x95e4` | 4 | `0.01` | `0.02470703` = 0.01 x min(k) 2.470703 | `COLLISION_WHERE.md:21` |
| 8 | S3 | instance `translation` | `0x90a0` | 16 | `[0, 0, 0, 1]` (w lane 0.5) | `[0.0, 0.9325, -0.305, 0]` = box centre (0, 93.25, -30.5) cm under the ASSUMED pairing | `COLLISION_WHERE.md:21` |

The full float4 blocks (every old and new vertex and plane, not just the first) are in the JSON, one
object per edit with `name`-equivalent fields `member`, `byte_offset`, `old_value`, `new_value`,
`source`, `method`, `frame`.

Method, identical to S1's: map the donor hull's AABB onto the box AABB per axis, about the hull's own
centre, then place the instance at the box centre; re-derive each plane as the supporting plane of the
new vertex set (`n' = -max(n·v)`), which is exact rather than a scaled `d`; `convex_radius` follows the
same rule B-10 used on the body hull (0.01 x min(k) = 0.016763 there, 0.064778 and 0.024707 here).

**Frame, stated because it is not decoded:** the box triples are in BmAK bone axes (x length, y width,
z height) and `new_value` is in the built file's (x, y, z) metres under the pairing
(x, y, z) = (bone y, bone z, bone x). That pairing is **ASSUMED** — `BM_EXTENTS_CHECK.md` §4.2 calls it
ASSUMED and `COLLISION_GEOM.md` says the axes are not proven. The pod's 4 deg is about bone y, which is
jc3 x under that pairing; the sign is unresolved and does not change the extents.

## 2. Dry run — every old value matches the built file (before anything is changed)

The check re-opens `batmobile.physicsc`, reads each byte range at `0x310 + byte_offset`, hashes it and
re-reads the float values, then compares both against what the edit object recorded:

| edit | offset | len | sha256 match | value match | result |
|---|---|---:|---|---|---|
| S2-vertices | `0x9440` | 128 | yes | yes | PASS |
| S2-planes | `0x94c0` | 96 | yes | yes | PASS |
| S2-convex_radius | `0x9404` | 4 | yes | yes | PASS |
| S2-instance_translation | `0x9020` | 16 | yes | yes | PASS |
| S3-vertices | `0x9620` | 128 | yes | yes | PASS |
| S3-planes | `0x96a0` | 96 | yes | yes | PASS |
| S3-convex_radius | `0x95e4` | 4 | yes | yes | PASS |
| S3-instance_translation | `0x90a0` | 16 | yes | yes | PASS |

**8 of 8 PASS** (`dry_run.all_ok: true`; `file_sha_before` == `file_sha_after` == `192c12479d81da6e`).
The first value of each block reads back as `[0.160471, 0.498016, -2.543827, 0.5]` (S2 vertex 0),
`[-0.023451, -0.066441, 0.997515, 2.574357]` (S2 plane 0), `0.01` (S2 radius),
`[-0.14356, 0.497926, -2.550005, 0.5]` (S3 vertex 0), `[-0.079793, 0.066059, -0.99462, -2.610928]`
(S3 plane 0) and `0.01` (S3 radius) — i.e. the edits are anchored to the file the build will read.

Two further in-memory checks, on the computed blocks only (no file write):

| step | new AABB (m) | box as decoded (m) | decoded `Bounds` AABB (m) | residual vs Bounds (cm) | 5 cm gate | plane support gap |
|---|---|---|---|---|---|---|
| S2 | 3.45688 x 1.035 x 6.79585 | same | 3.45688 x 1.035 x 6.79585 | 0.0 / -0.0 / -0.0 | PASS | 5.1e-08 m |
| S3 | 1.89365 x 0.46994 x 1.68432 | 1.89365 x 0.398 x 1.66177 | 1.89365 x 0.51296 x 1.68548 | 0.0 / **-4.302** / -0.116 | PASS | 1.1e-08 m |

S2 lands exactly on the box. S3 lands 4.30 cm under the rotated `Bounds` AABB on one axis, because the
donor's 8-vertex hull is not a perfect right box and the rotation mixes the two axes; that is inside the
plan's own 5 cm acceptance band (`T22_REOPEN.md:32`, "pod within 5 cm at 4 deg").

## 3. What this list deliberately does not contain

| item | why not | where it is recorded |
|---|---|---|
| moving the two shapes from compound `0x8f20` into body 0's compound `0x4a920` | `0x4a920` holds **14 of 14** instances; re-binding or growing the array is the slot question `T22_REOPEN.md:28-29` marks UNKNOWN | `not_writable` in the JSON |
| the BmAK constraint (export 171462) | `bm_collision.json` carries 0 constraint data and no JC3 constraint writer is decoded — `T22_REOPEN.md:30` (S4) | `not_writable` in the JSON |
| the body hull `0x5250` (S1) | already written by B-10; this plan only adds the two missing boxes | — |

UNKNOWN, with what would settle each: the bone-to-jc3 axis pairing (a decoded box TM frame, or the
in-game extents probe); the pod's rotation sign (neither sign changes the AABB, so only a shape-accurate
comparison would separate them); whether the engine simulates a shape carried in compound `0x8f20` as
body-0 contact rather than bumper contact (a drive, which the test ban forbids).

## 4. Cost, order, revert

244 B per shape, **488 B total**, all inside two existing 400-byte objects — no object is created or
resized, so no fixup or `.toc` record moves. The order a later build step would use: edits 1-4 (S2),
then 5-8 (S3), then `jc3hkx.py check --all --file`, then the 5 cm shape-union gate.

**Revert:** delete `Working/Prep/t22_shape_edits.json` and this report. `batmobile.physicsc` and the
T-22 row are unchanged, so there is nothing to undo in the build.
