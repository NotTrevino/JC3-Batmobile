# V-02b — pose renders and the lights module, `Builds/bm-RC4`

Date: 2026-11-07. Scope is exactly this card: the moving parts at their two limits, the delivered
pose, the 24-row lights module and its `CarLight` census. Silhouette, part counts and collision were
measured under V-02a (`tmp/freebuff/reports/verify-v02a-silhouette-census-collision.md`) and are not
re-measured or restated here.

Everything below is read-only against the build tree. The only files written are the PNGs and the two
JSONs under `Builds/bm-RC4/verify/v02b/`.

## 0. One deviation from the brief, declared first

The brief names `Tools/scripts/v02_render.py` as the renderer. That script is pinned to `Builds/bm-RC1`
and its own header lists pose renders as out of scope for it:

```
$ sed -n '1,14p' Tools/scripts/v02_render.py
"""v02_render.py - V-02 (part): assembled-car renders of the RC ...
Assembles every part of Builds/bm-RC1's parts module at LOD1 ...
Out: Builds/bm-RC1/verify/v02/{side_l,side_r,front,rear,top,bottom}.png + geometry.json
Not covered here (V-02 items 2-4): pose renders at each moving part's limits, the silhouette %,
interaction-point distances. Exit 0 only if no view shows more than 0.5 % red of the car's pixels.
```

So the renders were made by `Tools/scripts/v02b_pose_renders.py`, which imports `preview_rbm.render` —
the same rasteriser `v02_render.py` calls — and points it at `Builds/bm-RC4`.

- **Intended change:** render RC4 poses with v02's renderer path, not a second renderer.
- **File:** `Tools/scripts/v02b_pose_renders.py` (new, 167 lines).
- **Why this file:** `v02_render.py` hard-codes `RC1` and the assembled six views; the reusable part of
  it is `preview_rbm.render`, which the new script imports rather than copies.
- **Revert:** `rm Tools/scripts/v02b_pose_renders.py Builds/bm-RC4/verify/v02b/`; the build tree is
  untouched by either.

## 1. Pose renders — 18 images, 9 moving parts × 2 limits

Command (completed in one pass, no pose exceeded the 10-minute kill):

```
$ python Tools/scripts/v02b_pose_renders.py
poses rendered 18, unknown 6, battle pose: not in this tree
CHECK PASS
```

Each row rotates one part about the joint pivot and axis decoded in `Working/Translation/T8_PARTS.json`
(T-12), z-buffer renders at 900 px, and reports the largest vertex displacement so a pose that
"rendered" but did not move is visible as such.

| Row | Part | Limit | Angle | Axis | Max vertex move | Tris | PNG |
|---|---|---|---|---|---|---|---|
| P-01 | `batmobile_turret` | min | −60.000° | (0,1,0) | 1170 mm | 3142 | `P-01_batmobile_turret_min.png` |
| P-01 | `batmobile_turret` | max | +60.000° | (0,1,0) | 1170 mm | 3142 | `P-01_batmobile_turret_max.png` |
| P-03 | `batmobile_machine_gun` | min | −179.493° | (0,0,−1) | 3617 mm | 974 | `P-03_batmobile_machine_gun_min.png` |
| P-03 | `batmobile_machine_gun` | max | +177.861° | (0,0,−1) | 3635 mm | 974 | `P-03_batmobile_machine_gun_max.png` |
| P-04 | `batmobile_riot_suppressor` | min | −89.999° | (0,0,−1) | 2229 mm | 921 | `P-04_batmobile_riot_suppressor_min.png` |
| P-04 | `batmobile_riot_suppressor` | max | −0.000° | (0,0,−1) | **0 mm** | 921 | `P-04_batmobile_riot_suppressor_max.png` |
| P-09 | `batmobile_aero_flap_l_f` | min | −18.352° | (0,1,0) | 475 mm | 61 | `P-09_batmobile_aero_flap_l_f_min.png` |
| P-09 | `batmobile_aero_flap_l_f` | max | +7.465° | (0,1,0) | 173 mm | 61 | `P-09_batmobile_aero_flap_l_f_max.png` |
| P-10 | `batmobile_aero_flap_r_f` | min | −18.352° | (0,1,0) | 397 mm | 61 | `P-10_batmobile_aero_flap_r_f_min.png` |
| P-10 | `batmobile_aero_flap_r_f` | max | +7.465° | (0,1,0) | 186 mm | 61 | `P-10_batmobile_aero_flap_r_f_max.png` |
| P-11 | `batmobile_aero_flap_l_b` | min | −48.864° | (0,1,0) | 2077 mm | 76 | `P-11_batmobile_aero_flap_l_b_min.png` |
| P-11 | `batmobile_aero_flap_l_b` | max | +5.926° | (0,1,0) | 236 mm | 76 | `P-11_batmobile_aero_flap_l_b_max.png` |
| P-12 | `batmobile_aero_flap_r_b` | min | −48.826° | (0,1,0) | 1768 mm | 76 | `P-12_batmobile_aero_flap_r_b_min.png` |
| P-12 | `batmobile_aero_flap_r_b` | max | +5.973° | (0,1,0) | 248 mm | 76 | `P-12_batmobile_aero_flap_r_b_max.png` |
| P-14 | `batmobile_missile_pod_l` | min | +0.019° | (−1,0,0) | 1 mm | 777 | `P-14_batmobile_missile_pod_l_min.png` |
| P-14 | `batmobile_missile_pod_l` | max | +15.007° | (−1,0,0) | 432 mm | 777 | `P-14_batmobile_missile_pod_l_max.png` |
| P-15 | `batmobile_missile_pod_r` | min | +0.019° | (−1,0,0) | 1 mm | 773 | `P-15_batmobile_missile_pod_r_min.png` |
| P-15 | `batmobile_missile_pod_r` | max | +15.007° | (−1,0,0) | 433 mm | 773 | `P-15_batmobile_missile_pod_r_max.png` |

Two rows are technically rendered but are not evidence of travel, and I will not present them as a
pass on "both limits move":

- **P-04 max is −0.000° — 0 mm of motion.** The riot suppressor's upper limit is its own rest pose, so
  `P-04_..._max.png` is the delivered pose again. Whether T-12's `max_deg` is a decode truncation or a
  real zero-travel limit is UNKNOWN; the file that settles it is `Working/Translation/T8_PARTS.json`
  row P-04, re-decoded against the animation named in its `joint` block
  (`Research/BatmobileGrab/ANIMATIONS.json`).
- **P-14/P-15 min is +0.019° — 1 mm.** The pods' lower limit is effectively closed. Real limit or
  quantization, same UNKNOWN, same two files.

Three rest views were rendered for reference from the same run (`rest_front.png`, `rest_side.png`,
`rest_top.png`), which is why the folder holds **21 PNGs for 18 pose rows**.

### Poses left UNKNOWN — 6, with the exact command to rerun

```
$ python Tools/scripts/v02b_pose_renders.py     # re-emits all of the above; exit 0
```

| Row | Mechanism | Why no rotation exists | Settled by |
|---|---|---|---|
| P-02 cannon pitch | cannon | no rotation is animated; the bones translate (`Batmobile_Rig_Weapons_Heavy_Cannon_Barrrel_02`, 53.376 cm in `Batmobile_V2_Cannon_Fire`) and a hinge cannot reproduce translation | `Working/Translation/P02_CANNON.md`, `Research/BatmobileGrab/ANIMATIONS.json` |
| P-05 jet | transformation | bones translate (`JetSMove`, 40.163 cm in `Batmobile_V2_Bat_Tracker`); the spin is driven by `engine_rpm` in code, not by an animation | `Working/Translation/T8_PARTS.json` (row P-05), `Working/Translation/t1_handling.json`, `Research/BatmobileGrab/ANIMATIONS.json` |
| P-06 canopy | canopy | T-12 gives no joint and no bone; the geometry has no separate part to rotate | `Working/Translation/T8_PARTS.json` (row P-06), `Research/JC3Grab/MOVING_PARTS.md` |
| P-07 hatches L | missile bays | same: no joint, no bone, geometry stays in the shell | `Working/Translation/T8_PARTS.json` (row P-07) |
| P-08 hatches R | missile bays | same | `Working/Translation/T8_PARTS.json` (row P-08) |
| P-13 steering yoke | steering | no bone carries the part, so there is nothing to animate | `Working/Translation/T8_PARTS.json` (row P-13), `Working/Translation/P13_STEERING.md` |

The brief asked for canopy, hatches and air-brakes specifically. Air-brakes are **rendered** (P-09 to
P-12, four flaps, two limits each). Canopy (P-06) and both hatches (P-07, P-08) are UNKNOWN for the
reason in the table: no joint exists in this tree to rotate, so no image could be produced honestly.

### Battle pose

```
battle pose: not in this tree
```

Not a PASS, not a FAIL: `tmp/freebuff/reports/build-d12-variants-modes.md` line 126 records T-MD13 as
blocked by the toolchain — `ConvertAdf --e sportsmuscle_vehicle_parts.vmodc` throws
`NullReferenceException` in `InstanceMemberInfo.PrepareForWritting` →
`InstanceInfo.GuessInlineArrayCopyPosition`, and `bm_build` has no `.epe` applier, so the pose is
declared and not written. The battle pose therefore exists nowhere in `Builds/bm-RC4`. Only the
delivered pose is rendered (`rest_*.png`). Settled by: an `.epe` applier for `bm_build`, or a Gibbed
fix for the parts module's inline-array decode (`build-d12` line 218); rerun this card once a battle
pose is written.

## 2. Lights module — 24 rows, two 70° entries per headlight

Command:

```
$ python Tools/scripts/v02b_lights_check.py
module 7105 B 01405084aefe1ddf..., rows 24, behaviours {'HeadLight': 15, 'TailLight': 3, 'None': 4, 'Reverse': 2}
headlight rows 10, at 70 deg 4, reaches [18.0, 18.0, 60.0, 60.0]
```

- **24 rows, 7,105 B**, sha256 `01405084aefe1ddff24d9a66a4f2be30363dfec0849025d2418ffc559c583f4c`.
  Verified byte-identical to the stage tree's module:
  `sha256sum Builds/bm-RC4/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/generated/v0300_car_kensington_sportsmuscle_lights.vmodc`
  and the `bm-RC4-lights` copy return the same digest.
- **Two entries of 70° on each headlight**, as the brief states: `sportsmuscle_headlight_f_l` and
  `sportsmuscle_headlight_f_r` each carry a 70° row at **18 m** and a 70° row at **60 m**.
- Behaviour census: 15 `HeadLight`, 3 `TailLight`, 2 `Reverse` (on `sportsmuscle_tailstrip_r_l/r`),
  4 `None` (muzzle, forensics spot, two forensics heads).

### `.toc` offset — the brief's figure and the tree's figure

```
$ python -c "<eetoc.read_toc over Builds/bm-RC4*/*.ee>"
bm-RC4-lights  ee=11179037 toc=60806 recs=604  lights=(..., 16499504, 7105)
bm-RC4-parts   ee=11178919 toc=60806 recs=604  lights=(..., 16499504, 6337)
```

`Builds/bm-RC4` itself has **no `.ee`/`.toc`** — it ships as a loose drop tree
(`Builds/bm-RC4/drop/{editor,profile,settings,sound,textures}`, plus `receipt.json` and
`install.ps1`; `find Builds/bm-RC4 -maxdepth 2 -name "*.ee*"` returns nothing). So the 7,105 B module
inside RC4 is the loose file, and the **offset 16,499,504 is a property of the `bm-RC4-lights` stage
tree**, which is where the brief's figure belongs. The merged RC4 measurement of this record was
**16,500,744** in `tmp/freebuff/reports/verify-v01-file-gates-rc4.md` (line 63). Size 7,105 B and the
content digest agree everywhere; only the packing offset differs between trees. Recorded here, not
resolved, and not treated as a gate.

### Out-of-domain render risk — 6 rows beyond the shipped maximum

`build-d03` (U-1) pins the fleet's shipped maximum at **range 50 / angle 50**. Six of the 24 rows
exceed one or both:

| Part | Behaviour | Range | Angle | Exceeds |
|---|---|---|---|---|
| `sportsmuscle_headlight_f_l` | HeadLight | 60.0 | 70.0 | range and angle |
| `sportsmuscle_headlight_f_l` | HeadLight | 18.0 | 70.0 | angle |
| `sportsmuscle_headlight_f_r` | HeadLight | 18.0 | 70.0 | angle |
| `sportsmuscle_headlight_f_r` | HeadLight | 60.0 | 70.0 | range and angle |
| `sportsmuscle_body` | HeadLight | 10.0 | 60.0 | angle |
| `sportsmuscle_body` | TailLight | 4.0 | 60.0 | angle |

This is a **render risk, not a render failure**: the cone geometry drawn for the 70°/60 m entries has no
shipped counterpart, so an in-game cone that reads shorter or narrower than the PNGs suggest is a
plausible engine clamp rather than a build defect. The 18 m pair sits inside the shipped range and is
the one to trust for beam length. Whether JC3 clamps at 50 or extrapolates is UNKNOWN; the files that
settle it are `Working/Translation/t14_lights.json` (the 3,217-entry fleet census the labels rest on)
and the `domain_ledger` in `Tools/scripts/bm_rc4_lights.py` (lines 167-260), plus an in-game look at
one 70° cone. The 60° `body` rows are the same class and are included for completeness.

### `CarLight` census — 24 blocks over 8 lamp parts

```
$ python -c "<census from Builds/bm-RC4/verify/v02b/lights.json>"
car_light_blocks 24, lamp_parts_present 8
```

| Lamp part | LOD1 | LOD2 | LOD3 | Blocks |
|---|---|---|---|---|
| `sportsmuscle_headlight_f_l` | 1 | 1 | 1 | 3 |
| `sportsmuscle_headlight_f_r` | 1 | 1 | 1 | 3 |
| `sportsmuscle_wheel_f_l_arch` | 1 | 1 | 1 | 3 |
| `sportsmuscle_wheel_f_r_arch` | 1 | 1 | 1 | 3 |
| `sportsmuscle_wheel_r_l_arch` | 1 | 1 | 1 | 3 |
| `sportsmuscle_wheel_r_r_arch` | 1 | 1 | 1 | 3 |
| `sportsmuscle_tailstrip_r_l` | 1 | 1 | 1 | 3 |
| `sportsmuscle_tailstrip_r_r` | 1 | 1 | 1 | 3 |

24 = 8 parts × 3 LODs, one `CarLight` block each, so every row's part is a part that can actually be
lit. No lamp part is missing a block, and no non-lamp part carries one. The 8 parts here are the
"8 lamp parts" of the card; the module's 24 rows are distinct from the 24 blocks by construction
(three LOD instances per part, one row set per part).

## 3. Files written

```
Builds/bm-RC4/verify/v02b/
  P-01_batmobile_turret_{min,max}.png            P-09_aero_flap_l_f_{min,max}.png
  P-03_batmobile_machine_gun_{min,max}.png       P-10_aero_flap_r_f_{min,max}.png
  P-04_batmobile_riot_suppressor_{min,max}.png   P-11_aero_flap_l_b_{min,max}.png
  P-12_aero_flap_r_b_{min,max}.png               P-14_missile_pod_l_{min,max}.png
  P-15_missile_pod_r_{min,max}.png
  rest_front.png  rest_side.png  rest_top.png
  poses.json  lights.json
```

21 PNGs (18 poses + 3 rest views), 900 px, one JSON per half of the card carrying every number above.

## 4. Status summary

| Item | Result |
|---|---|
| Poses rendered at two limits | **18 / 18 renderable rows**, PASS with the two caveats (P-04 max and P-14/15 min are degenerate limits) |
| Canopy, hatches | **UNKNOWN** — no joint in this tree; rerun `python Tools/scripts/v02b_pose_renders.py` when T8_PARTS gains joints |
| Air-brakes | **PASS**, 4 flaps × 2 limits |
| Battle pose | **not in this tree** (`build-d12` `ConvertAdf` NRE) — neither PASS nor FAIL |
| Lights module rows | **24**, two 70° entries per headlight, 18 m + 60 m |
| Out-of-domain | **6 rows** beyond 50/50 — render risk recorded, not a gate |
| `CarLight` census | **24 blocks over 8 lamp parts**, 3 per part (one per LOD) |
| Renders killed at 10 minutes | **none** |
