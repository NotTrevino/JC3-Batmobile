# Wheel orientation, radius and width — bm-RC2 vs BmAK (TYRES.md)

**Task.** Check how the four wheels are oriented in the build against BmAK:
`Research/BatmobileGrab/TYRES.md` (tyre diameters, width, wheel bones), the build's
`Working/Parts/bm_vehicle_parts.json` and its parts module (how the wheel parts rotate).
Verify the spin axis, radius and width per wheel against TYRES.md — cm vs m — and that
front/rear and left/right are not swapped after the coordinate conversion. Table of
wheel / BmAK value / built value / difference. Output
`Builds/bm-RC2/verify/wheels.md` + `Tools/scripts/v_wheels.py --check`. Read-only.

**Status: done. `v_wheels.py --check` exits 0 on the page it wrote.**

Files: `Tools/scripts/v_wheels.py` (new), `Builds/bm-RC2/verify/wheels.md` (new,
generated). Nothing under `Builds/` was modified except that page; no other tool,
manifest or build file was edited. Revert = delete the two files.

## The answer

| wheel | BmAK (TYRES.md) | built (bm-RC2) | difference |
|---|---|---|---|
| `f_l` (part 26, slot 0) | axle **x** (lateral, left = −x) | axle `x`; part rotation identity | 0° |
| `f_r` (part 27, slot 1) | axle **x** | axle `x`; rotation identity | 0° |
| `r_l` (part 11, slot 3) | axle **x** | axle `x`; rotation identity | 0° |
| `r_r` (part 12, slot 2) | axle **x** | axle `x`; rotation identity | 0° |
| `f_l` radius | station 0.6829 m · tread Ø 1.3652 m | 0.68275 m (front axle) | −0.15 mm vs station, +0.15 mm vs tread |
| `f_r` radius | station 0.6826 m · tread Ø 1.3657 m | 0.68275 m | +0.15 mm vs station, −0.10 mm vs tread |
| `r_l` radius | station 0.6826 m · tread Ø 1.3654 m | 0.68265 m (rear axle) | +0.05 mm vs station, −0.05 mm vs tread |
| `r_r` radius | station 0.6827 m · tread Ø 1.3652 m | 0.68265 m | −0.05 mm vs station, +0.05 mm vs tread |
| `f_l` width | mesh 0.7314 m (station 0.7325, mirrored L↔R) | 0.73195 m (front axle) | +0.55 mm |
| `f_r` width | mesh 0.7325 m (station 0.7314) | 0.73195 m | −0.55 mm |
| `r_l` width | mesh 0.7318 m (station 0.7315) | 0.73165 m (rear axle) | −0.15 mm |
| `r_r` width | mesh 0.7315 m (station 0.7318) | 0.73165 m | +0.15 mm |

* **Axis** — every wheel part's `parent_space_offset` 3×3 block in the built module is
  the identity, so each mesh's own axes are the car axes. Every built wheel LOD1 is thin
  along x (f_l: 1.053 × 1.388 × 1.340 m; x is the tyre + inboard `*_Disc`, y/z are the
  diameter), so the spin axis is **+x, lateral** — TYRES.md's axle. All four `spins = 1`.
* **Radius** — `land_global.front_wheels.radius` 0.6827499866 m and
  `rear_wheels.radius` 0.6826500297 m are **exactly** the axle means of TYRES.md's
  station radii ((0.6829+0.6826)/2, (0.6826+0.6827)/2). 0.000 mm.
* **Width** — `front_wheels.width` 0.7319499850 m and `rear_wheels.width`
  0.7316499949 m are **exactly** the axle means of the four measured tyre widths
  ((0.7314+0.7325)/2, (0.7318+0.7315)/2). 0.000 mm.
* **cm vs m** — JC3's members are metres; the built values are 0.68/0.73, not 68/73. The
  BmAK figure that invites the error is `SVehicleWheel.WheelRadius` **64.0 cm** = 0.640 m
  (`CHAIN.json` offset 568, TYRES.md §4): the built 0.68275 m is **+4.27 cm** over it,
  which T-G6 keeps on purpose (0.64 m is BmAK's contact-radius simplification inside the
  0.683 m visual tyre). Read as metres, 64.0 would be a 100× error; it is not what the
  build wrote.
* **Corners** — not swapped. Hardpoints decode as slot 0 FL (−1.208, 0.7047, −2.5700),
  1 FR (+1.208, 0.7047, −2.5699), 2 RR (+1.2845, 0.7027, +2.4589), 3 RL (−1.2845,
  0.7027, +2.4589) — left = −x, front = −z, and hardpoint 0 matches TYRES.md's f_l tyre
  box centre (x −1.208, z −2.570) to <1 mm. The `wheel_parts[]` order (26→0, 27→1,
  12→2, 11→3) is the fleet's own convention: over the 233 decoded vehicles slot 2 is
  always the `*_r_r` part and slot 3 the `*_r_l`, so rear-right-before-rear-left is
  correct, not a swap.

## One thing that does not match — reported, not asserted away

The wheel *parts* still carry the shipped **Serpente** `parent_space_offset`
translations — element for element the vanilla module's, and equal to the vanilla
land_global's hardpoints in `Builds/test-003` — while this build's hardpoints are the
Batmobile's:

| wheel | part origin (built) | hardpoint (built) | Δ (m) |
|---|---|---|---|
| `f_l` | (−0.8850, +0.4000, −1.5570) | (−1.2080, +0.7047, −2.5700) | (−0.3230, +0.3047, −1.0130) |
| `f_r` | (+0.8850, +0.4000, −1.5570) | (+1.2080, +0.7047, −2.5699) | (+0.3230, +0.3047, −1.0129) |
| `r_l` | (−0.8850, +0.4000, +1.4460) | (−1.2845, +0.7027, +2.4589) | (−0.3995, +0.3027, +1.0129) |
| `r_r` | (+0.8850, +0.4000, +1.4460) | (+1.2845, +0.7027, +2.4589) | (+0.3995, +0.3027, +1.0129) |

The wheel-arch parts *were* placed at the true hubs (part 42 world = (−1.208, 0.7047,
−2.5699)), so arch and wheel disagree by that delta **if** a wheel part is drawn at its
own transform — which is what vanilla does there (part translation == hardpoint). The
state is already recorded in `Working/Parts/bm_vehicle_parts.json`: "the existing
body/wheel parts keep the shipped Serpente transforms; ... the body/wheel re-emit is
still owed", and `Tools/scripts/bm_parts.py:911` repeats it. Whether the runtime places a
wheel by its transform or by `base_wheel_hardpoint_positions[]` is **UNKNOWN** in the
repo — no file decodes that path — so the page prints the delta as a WARN and does not
fail on it. It is not a regression introduced by this check and this task was read-only.

Also not matching, printed not asserted: `front/rear_wheels.rim_radius` (0.539013 /
0.538934) are untouched shipped values; TYRES.md has no rim radius to compare (its
1.0254 m is the `Fan` hubcap diameter).

## Evidence (bytes)

| source | what it contributed |
|---|---|
| `Builds/bm-RC2/…/batmobile/sportsmuscle_vehicle_parts.vmodc` (46300 B, `6e379e4c5716f15c…`) | parts 11/12/26/27 `parent_space_offset` (identity 3×3; translations above), `wheel_parts[]` slots, `spins` |
| `Builds/bm-RC2/…/batmobile/v0300_…_land_global.vmodc` (1600 B, `f9a1455ff23d16c4…`) | `front/rear_wheels.radius` / `.width` / `.rim_radius`, `base_wheel_hardpoint_positions[0..3]` |
| 4 × `sportsmuscle_wheel_{f_l,f_r,r_l,r_r}_lod1.rbm` (`9edc7f1a…`, `9729ada4…`, `aeebbb13…`, `1253fa71…`) | mesh bbox (thin axis), crown radius, tread band |
| `Research/BatmobileGrab/TYRES.md` (`dbcb9980…`) | per-corner tread Ø, width, station radius, station width, the axes line |
| `Research/JC3Grab/PARTS_TABLE.jsonl` (233 vehicles) | slot→corner convention (0 f_l, 1 f_r, 2 r_r, 3 r_l) |
| `Builds/test-003/…` (vanilla-geometry base) | vanilla Serpente wheel mesh 929 verts / 0.329 × 0.801 × 0.800 m; vanilla land_global radius 0.380 m and hardpoints (±0.885, 0.400, ±1.557) = the vanilla part translations |
| `Tools/scripts/bat_assemble.py:233` | `to_jc3_rot = (−y, z, −x)`, the proper rotation behind "left = −x, front = −z" |

One earlier draft of the page printed part origins as (0,0,0): the stored 4×4 is
row-vector form (translation in the last **row**, 12..14), so a chain composes as the
row-major product `P·M`. Fixed in `world()`; the delta table above is the corrected
read and `--check` re-derives it.

## Checks actually run

```
$ python Tools/scripts/v_wheels.py --write
wrote Builds\bm-RC2\verify\wheels.md (168 lines)
WARN: the four wheel parts still carry the shipped Serpente `parent_space_offset`
translations (max |hardpoint - part origin| = 1.0130 m); …
ok
WRITE_EXIT=0

$ python Tools/scripts/v_wheels.py --check
WARN: (same one warning)
check ok
CHECK_EXIT=0
```

Asserted by `--check` (all green): four identity rotation blocks (≤1e-6); each mesh's
thin axis is x; front/rear radius = TYRES station means (≤0.5 mm); front/rear width =
TYRES mesh means (≤0.5 mm); radius and width in 0.5…1.0 (metres, not centimetres); four
`wheel_parts` rows all `spins = 1`; part→slot = 26→0, 27→1, 12→2, 11→3 and the fleet
majority over 233 vehicles matches; hardpoint x reads left(−)/right(+) and z
front(−)/rear(+); hardpoint 0 = TYRES f_l hub to 1 mm; each wheel part's translation is
equal to the vanilla Serpente's. The page is also compared byte-for-byte against the
re-derived text, so it cannot go stale silently.

Limitations: read-only, so no in-game settlement of the §5 placement question; the
`rim_radius` and the transform delta are printed, not asserted. The tick "tyre Ø
1.3652–1.3657" is TYRES.md's mesh measure and is not re-measured here — the page
compares the *build* against the *page*, which is the comparison asked for; the PSKX
re-derivation lives in `bmak_tyres.py`.
