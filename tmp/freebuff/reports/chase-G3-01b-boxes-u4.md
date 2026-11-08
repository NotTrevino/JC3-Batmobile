# chase-G3-01b-boxes-u4 — the StaticMesh Bounds of the two Batmobile collision meshes

**STATUS: resolved**

G3-01b's U-4 asked for the `StaticMesh` bounds of `BmGame.upk` exports **175973** (`Batmobile_V2`,
battle-mode collision mesh) and **175974** (`Batmobile_V2_Collision_Pursuite`) as a second check
on its box extents, and stopped because the tagged properties carry no `Bounds` struct.

Both are `StaticMesh` exports and G3-01b was right about the tag stream: **four** tags, ending the
property list at byte **32**, then a 2-byte `type 0` terminator. The bounds are **not** a tagged
property — they are the first 28 bytes of the untagged native data, which starts at byte **34** in
both exports, as an `FBoxSphereBounds`:

```
native+0   28 B   Origin (3f), BoxExtent (3f), SphereRadius (1f)
native+28   4 B   int32 = the export's own ObjectNCR tag value (its RB_BodySetup)
native+32  24 B   FBox: Min (3f), Max (3f)
native+56   8 B   2 x int32, `6, 128` in both exports — semantics UNKNOWN
native+64         cooked compressed mesh data (not decoded)
```

## The seven floats, located in both exports

| export | where | Origin (cm) | BoxExtent (cm) | SphereRadius (cm) |
|---|---|---|---:|---:|
| 175973 `Batmobile_V2` | export byte **34** = tag_end(32)+2 | 5.8023 / 0.0000 / 146.4544 | 356.3003 / 245.6297 / 146.4651 | **434.8802** |
| 175974 `Batmobile_V2_Collision_Pursuite` | export byte **34** = tag_end(32)+2 | 8.5922 / 0.0000 / 117.3755 | 352.8289 / 175.9482 / 116.6620 | **382.2412** |

Hex, verbatim from the record (`native+0 .. +55`):

```
175973  40acb940 00008037 55741243 6f26b243 34a17543 13771243 aa70d943 14970200
        be3fafc3 33a175c3 00682fbc 200db543 34a17543 b4759243
175974  a0790941 00000000 46c0ea42 186ab043 bdf22f43 f752e942 e01ebf43 15970200
        4b1eacc3 bdf22fc3 4fa7363f e4b5b443 bdf22f43 9e096a43
```

So the two meshes' own extents (full spans = 2 x BoxExtent) are
**712.600 x 491.259 x 292.930 cm** (battle) and **705.658 x 351.896 x 233.324 cm** (pursuit) —
6.9–7.1 m long, 3.5–4.9 m wide, 2.3–2.9 m tall — against the car's chassis box 0
(690.305 / 374.536 / 207.500 cm).

## Oracles actually run (each would fail if the reading were wrong)

| # | oracle | result |
|---:|---|---|
| 1 | position: the block is at `tag_end+2`, and is the **only** self-consistent FBoxSphereBounds + FBox pair in the whole native body (every 4-byte offset scanned, extents > 1 cm) | 175973: 1 candidate at delta 0; 175974: 1 candidate at delta 0 |
| 2 | internal arithmetic: `Origin == (Min+Max)/2`, `BoxExtent == (Max-Min)/2` | 175973: 7.63e−06 cm / 7.63e−06 cm; 175974: 1.53e−05 / 1.53e−05 |
| 3 | identity: the int32 between them is the export's own `ObjectNCR` value | 175973 → 169748 `Batmobile_V2.RB_BodySetup`; 175974 → 169749 (both exactly the tags' values) |
| 4 | package-wide shape: same block at `tag_end+2` on BmGame.upk's StaticMesh exports | **37 / 52 conform** (15 recorded as non-conforming, heads kept in the JSON) — so the position is the package's `StaticMesh` serialisation, not a coincidence at two exports |
| 5 | geometry: FBox vs the hull's own decoded vertices (43 / 13 `FKConvexElem` arrays of 169748 / 169749, re-read from BmGame.upk) | worst 12.06 cm (1.69 % of span) / 21.82 cm (3.09 %) |
| 6 | SphereRadius vs hull `max |v − Origin|` | 434.8802 vs 435.8772 cm (0.23 %); 382.2412 vs 382.0314 cm (0.05 %) |
| 7 | SphereRadius vs the box corner distance (i.e. is it `|BoxExtent|`?) | 434.8802 / 456.8762 = 0.9519 and 382.2412 / 411.1642 = 0.9297 → **no**, it is a vertex-measured radius |
| 8 | G3-01b's box extents vs these mesh spans, FULL vs HALF reading | **FULL lengths** (see below) |

## The comparison G3-01b asked for

Sorted per axis (frame-agnostic, the rule G3-01b used), box extent ÷ mesh full span:

| box | mesh | ratio, FULL reading | ratio, HALF reading |
|---|---|---|---|
| 169750 `Batmobile_Chassis` box 0 (690.305 / 374.536 / 207.500) | 175973 battle | 0.9687 / 0.7624 / 0.7084 | 1.9374 / 1.5248 / 1.4167 |
| 169750 `Batmobile_Chassis` box 0 | 175974 pursuit | 0.9782 / 1.0643 / 0.8893 | 1.9565 / 2.1287 / 1.7786 |
| 169750 `Batmobile_Chassis` box 1 (679.585 / 345.688 / 103.500) | 175973 battle | 0.9537 / 0.7037 / 0.3533 | 1.9073 / 1.4074 / 0.7067 |
| 169750 `Batmobile_Chassis` box 1 | 175974 pursuit | 0.9631 / 0.9824 / 0.4436 | 1.9261 / 1.9647 / 0.8872 |
| 169751 `Batmobile_Rig_Weapons_Trans` box 0 | battle / pursuit | 0.14–0.47 (a part, not the car) | 0.27–0.94 |

**Second verdict: FULL lengths — G3-01b's result reproduced from the render-mesh bounds instead of
from the convex hull.** Under FULL lengths every chassis-box dimension is at most **1.0643** of the
mesh span; under HALF lengths every chassis box's **long axis** would be **1.9073** of the span of
the mesh that is supposed to contain it. The test is taken on each box's longest axis, not its
smallest: chassis box 1 is a floor pan (103.5 cm on one axis), so that axis alone would read 0.7067
under the half reading and decide nothing — its long axis is where the two readings differ by 2×.
The weapons box is a bone envelope for the weapon rig, so it is listed without a verdict.

## Files written

| file | what |
|---|---|
| `Tools/scripts/grab_sm_bounds.py` | the tool (`--write` / `--check`), new, 780 lines |
| `Research/BatmobileGrab/SM_BOUNDS.md` | the record, generated |
| `Research/BatmobileGrab/SM_BOUNDS.json` | the same as data (both exports, all 52 fleet rows, all 6 comparison rows, every oracle number) |
| `tmp/freebuff/reports/chase-G3-01b-boxes-u4.md` | this report |

Nothing else was written: `git status` adds exactly those three files (`??`) and no edits.
G3-01b's `grab_collision_boxes.py` / `COLLISION_BOXES.*`, G3-01c's `grab_collision_convex.py`,
`upk_read.py`, `GRAB_BACKLOG.md`, `MODLOG.md`, `STATUS.md` are untouched (the pre-existing `M`
entries in `git status` are other tasks' work, not mine). The tool *imports* `upk_read` and
`grab_collision_convex.parse_element` read-only, the same way G3-01b imports G3-01c. Read-only on
the game install; no game launched, attached to or read from memory; no builds, no installs, no git
operations.

## Commands and outputs (verbatim)

```
uv run python Tools/scripts/grab_sm_bounds.py --write
```
```
wrote SM_BOUNDS.json and SM_BOUNDS.md (2 StaticMesh exports, 13 checks, 0 failed)
```
exit status **0**

```
uv run python Tools/scripts/grab_sm_bounds.py --check
```
```
OK: 2 StaticMesh exports, bounds at native+0 in both, fleet 37/52, extents FULL lengths, 13/13 checks, md+json byte-identical
```
exit status **0**. `--check` re-opens `BmGame.upk`, re-walks both exports' tags, re-decodes the
bounds block, re-scans the whole native body for candidates, re-runs the 52-export fleet scan,
re-decodes the 56 convex elements' vertices for oracles 5–7, re-reads G3-01b's box extents from
`COLLISION_BOXES.json`, re-runs every check, and fails if `SM_BOUNDS.md` or `.json` differs by one
byte.

```
python -m py_compile Tools/scripts/grab_sm_bounds.py
```
```
COMPILE_OK
```
exit status **0**

The 13 checks, as printed into `SM_BOUNDS.md` §4, all PASS: no Bounds tag (4 tags, 0..32 in both);
2-byte `0000` terminator; the block is the only one of its shape in each body; Origin/BoxExtent
equal the FBox centre/half-span; the int32 is each export's ObjectNCR value; 37/52 StaticMesh
exports carry it at the same offset; the hull vertices re-read with a zero footer; the FBox agrees
with the hull union within 5 % of span; the radius within 0.5 % of the hull's max vertex distance;
the radius is below the box corner distance; every chassis box fits the mesh's span (1.0643) and
would not under the half reading (1.9073); and the verdict is FULL lengths.

## UNKNOWNs and why

| # | unknown | what was tried | why it stays UNKNOWN / where it would be found |
|---|---|---|---|
| U-1 | the member names of the int32 at native+28 and of the two int32 at native+56 | decoded every value: +28 equals the export's own `ObjectNCR` (169748 / 169749), +56 is `6, 128` in both exports | `BMSDK_OFFSETS.json` has no `StaticMesh` layout, so an offset cannot be named without the engine's struct dump (the G3-06 native-layout question). The values are recorded, not named |
| U-2 | the exact vertex set `SphereRadius` was measured on | compared it with the hull's `max |v − Origin|` (0.997 cm / 0.210 cm apart, 0.23 % / 0.05 %) and with the box corner distance (4.8 % / 7.0 % farther) | the render mesh's own vertex buffer is cooked/compressed (native+64 onward is not decoded here), so equality can be tested only against the collision decomposition, which is a different vertex set |
| U-3 | why 15 of 52 StaticMesh exports do not carry the block at `tag_end+2` | scanned every 4-byte offset up to 16 bytes past each terminator; kept each one's head hex in `SM_BOUNDS.json` (`fleet.non_conforming`) | those native heads start with zero bytes (e.g. 176006 `HelicopterSearchLight`: 12 zero bytes then floats), i.e. another or absent native prologue; deciding it needs its own decode and does not affect 175973/175974 |
| U-4 | whether the FBox was authored from the render mesh's vertices or the collision proxy's | the FBox reaches up to +21.82 cm beyond the hull vertex union on one side and falls up to 16.79 cm inside it on another; both numbers are in the record | both candidate vertex sets are only partly available here; which one the engine measured is not provable without the render vertex buffer |
| U-5 | the frame of the mesh bounds (mesh-local vs any actor/bone frame) | the bounds axios are the mesh's own; no transform to JC3 space is claimed | this record does not link the mesh frame to the actor frame; that is `COLLISION_FRAME.md`'s question (G3-01b limitation, unchanged) |

## Limitations

- The comparison divides sorted box extents by sorted mesh spans, the frame-agnostic rule G3-01b
  used. It is a span test, not a containment test: it does not prove the chassis box lies inside
  the mesh bounds axis by axis.
- Oracles 5–7 use the collision hull's vertices (G3-01c's `parse_element`), not the render mesh's,
  because the render vertex buffer is compressed. The agreement is therefore "within 3.09 % of
  span", not "exact"; the exact figure is reported as a number rather than rounded to a pass.
- Oracle 4 is a position/invariant test over `BmGame.upk` only; other packages' StaticMesh exports
  were not scanned (they hold no Batmobile mesh, per G3-01b's fleet scan).
