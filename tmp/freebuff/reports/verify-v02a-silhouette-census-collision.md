# V-02 part A - silhouette, parts census, interaction, collision on bm-RC4

Build: `Builds/bm-RC4` (shipped `.ee` + its `aaf` staging copy). Offline; no game, no install, no
archive. Part A only: **no renders were started** (no `preview_rbm`, no pose pass, no light pass).

Every number below is produced by the command named in its table. The JSON for each gate is written
to `tmp/freebuff/verify-v02a/<gate>.json`; the four gate commands all exited 0 and none ran past the
10-minute limit.

| gate | result | command |
|---|---|---|
| 1 silhouette (limit 99.9 %/view) | **PASS**, worst side **+0.0004 pp** | `python Tools/scripts/v02a_rc4.py --gate silhouette` |
| 2 parts census (59 / 19) | **PASS**, 59 parts / 19 types, 59/59 models | `python Tools/scripts/v02a_rc4.py --gate census` |
| 3 interaction (5-30 cm, +2 cm envelope) | **PASS**, 77/77 in band, worst outside 0.0000 m | `python Tools/scripts/v02a_rc4.py --gate interaction` |
| 4 collision (not a render-bbox gate) | **shape 0.0000 m; 5 hulls / 62 bodies; 0/54 free; 2 of 3 boxes missing; constraint omission - but shipped placement is 0.25 cm, not the brief's 6.1 cm** | `python Tools/scripts/v02a_rc4.py --gate collision` |

The one place the brief's expected figure did not reproduce is §5: the shipped artifact's body-0
hull sits at **y 0.030..2.105 m**, so the placement deviation is **[0.0005, 0.0000, 0.0025] m
(0.25 cm)**, not `[0.0005, 0.061, 0.0025]` (6.1 cm). The 6.1 cm vector is real for the superseded
payload `0164936b…`, which is **not in the RC4 tree**. It is recorded as **NOT MET** for that
payload and is **not** counted as a pass anywhere in this report.

## 1. Silhouette vs the BmAK body - per view (limit 99.9 %)

Command: `python Tools/scripts/v02a_rc4.py --gate silhouette`

- our mesh `Builds/bm-RC4/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_body_lod1.rbm`
  (sha256 `10cbbf400d5d6182…`, 2,311,365 B, 44,602 non-degenerate triangles)
- source: the non-wheel body of `Working/Appearance/grab/Playable_Batmobile_SF/SkeletalMesh3/Batmobile_V2.pskx`,
  215,893 body faces (split re-measured at 215,893 - asserted against the build's own number)
- offset applied to the source: `[0.0, 0.022231, 0.154284]` m from
  `Working/Appearance/build/stations.json`; one fixed frame per view, 2 % margin.

| view | frame px | source px | ours px | coverage | margin vs 99.9 % | holes % | tears % | extra % | gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| side | 2400 x 864 | 1,131,963 | 1,130,835 | **99.9004 %** | **+0.0004 pp** | 0.2968 | 0.0514 | 0.1972 | PASS |
| front | 2400 x 1605 | 2,631,531 | 2,633,349 | **100.0691 %** | **+0.1691 pp** | 0.1448 | 0.0110 | 0.2139 | PASS |
| top | 1259 x 2400 | 2,047,733 | 2,046,192 | **99.9247 %** | **+0.0247 pp** | 0.1932 | 0.0047 | 0.1179 | PASS |

**What moved it: nothing.** The margin is carried over unchanged from RC2, not improved or eroded by
RC4. RC2's own `Builds/bm-RC2/verify/geometry.json` (read by the same command, `rc2` block) records
the side view at 1,130,835 / 1,131,963 = 0.999004 (+0.0004 pp); RC4's side view is the same two
pixel counts, `side_px_delta = 0`. The body mesh is **byte-identical** (`10cbbf400d5d6182…` in both),
the offset is identical (`[0.0, 0.022231, 0.154284]`), and the source split is identical at 215,893
faces. RC2 measured only the side view; front and top are new measurements in this pass, and both
pass with more room than the side.

The source BUD-1 gross-hole oracle is printed beside coverage because coverage is **net** (our extra
pixels count towards it): side holes 0.2968 % is **0.0032 pp under** the 0.3 % line; front 0.1448 %
and top 0.1932 % are also under it.

## 2. Parts-module census

Command: `python Tools/scripts/v02a_rc4.py --gate census`

- module `Builds/bm-RC4/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_vehicle_parts.vmodc`,
  39,278 B, sha256 `1fcd4215ff490248…`
- the packed `.ee` member `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_vehicle_parts.vmodc`
  is the same bytes (`1fcd4215ff490248…`, 39,278 B), so the census is of what ships, not only of staging.

| measure | value | expected (build-d08 §2) |
|---|---:|---:|
| parts | **59** | 59 |
| distinct damage types | **19** | 19 |
| part models that resolve in the build | **59 / 59** | all |
| missing models | none | none |
| part indices absent from the table | **1, 2** | 1, 2 (B-04's removed doors) |
| parts beyond the first 59 | none | none |
| lamp parts (`has_lights`) | 20 | (not part of this gate) |

**It returned 59, not 61, so there were no two extra parts to find.** The 59-part module is the
post-B-04 table: indices 1 and 2 (the two doors) are absent, which is exactly the -2 that separates
RC2's census (61 parts / 20 types) from this one. If this census had read 61, the two to find would
be `sportsmuscle_door_f_l` (index 1) and `sportsmuscle_door_f_r` (index 2) - the same pair
`bm_parts.py` removes. The 19 types are the 20 RC2 carried minus `Land_Door`.

## 3. Interaction points (5 cm outside the hull, within 30 cm; envelope +2 cm)

Command: `python Tools/scripts/v02a_rc4.py --gate interaction`

- mesh: the RC4 body, sha256 `10cbbf400d5d6182…`, 55,554 vertices / 44,608 triangles,
  bbox `[-1.7508, 0.0867, -3.4218] .. [1.7464, 2.3627, 3.6055]` m
- `t9_interaction.build()` run with `jc3interact.read_bat_mesh` pointed at the RC4 body (the same
  substitution the template used for RC2).

| measure | value |
|---|---:|
| donor objects | 85 |
| placed | 77 |
| dropped by D-9 | 6 |
| socket | 1 |
| UNKNOWN | 1 |
| in band (5 cm <= d <= 30 cm, not inside) | **77 / 77** |
| distance range | 0.0577 m .. 0.1461 m |
| placed inside the hull | 0 |
| worst excursion outside the envelope | **0.0000 m** (limit 0.02 m) |

**Gate: PASS.** The whole placed set is inside the 5-30 cm band; the 2 cm outer tolerance is unused,
and no placed point is inside the hull. The socket is the documented driver seat; the UNKNOWN is the
passenger seat (one-seat cockpit).

## 4. Collision - re-measured from the packed physicsc, not a render bbox

Command: `python Tools/scripts/v02a_rc4.py --gate collision`
(the body count is independently printed by `python Tools/scripts/bm_vehicle_hull.py --check`)

### 4.1 Which bytes were measured

| quantity | value |
|---|---|
| shipped member | `Builds/bm-RC4/drop/.../v0300_car_kensington_sportsmuscle_debug.ee::models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc` |
| size / sha256 | 340,368 B / **`fda78f4d8056a4ee47bd8316b6c738fac6f16d227e3bd4769853a43613b41095`** |
| aaf staging copy | same sha256 (`aaf_matches_ee = true`) |
| objects / polytopes | 430 / **54** (54 convex) |
| shape instances / hull instances | 112 / **74** |
| donor bodies | **62** (`bm_vehicle_hull.py --check`: "bodies 62") |

### 4.2 Five hulls written (body 0 + 4 wheels)

Comparing **decoded vertex/plane sets** against the recorded donor
`Builds/test-091/.../sportsmuscle.physicsc` (sha256 `1b90daefdc9660b4…`), 5 hulls differ:

| hull shape | part bound | change |
|---|---|---|
| `0x5250` | part **0** `sportsmuscle_body` | size 2.085 x 1.212 x 3.679 m -> **3.745 x 2.075 x 6.903 m** |
| `0xfb40` | part **11** `sportsmuscle_wheel_r_l` | 0.2958 x 0.8225 x 0.7822 -> **0.491 x 1.365 x 1.299 m** |
| `0xfe80` | part **12** `sportsmuscle_wheel_r_r` | same wheel change |
| `0xb5d0` | part **26** `sportsmuscle_wheel_f_l` | same wheel change |
| `0xb910` | part **27** `sportsmuscle_wheel_f_r` | same wheel change |

So the five named parts each bind one hull, and those five are the five geometrically changed hulls:
**5 written over the donor's 62 bodies - confirmed.** (A raw byte comparison of each polytope
*object* reads 6, but that is not a hull diff: a hull's vertex/plane arrays sit outside the object
extent. The three extra byte diffs - the hull bound to absent part index 1, the seat hull (part 4)
and the mirror hull (part 33) - decode to identical vertices and planes, i.e. re-serialisation, not a
write.)

### 4.3 Shape and placement vs BmAK chassis box 0

Box 0 in JC3 axes, from `Working/Collision2/bm_vehicle_hull.json` `chassis_box_0`
(centre `[9.0, 0.0, 106.75]` cm, extents `[690.305, 374.536, 207.5]` cm; PSK x=length, y=width,
z=height -> JC3 x=width, y=height, z=length):

| | min (m) | max (m) | size (m) |
|---|---|---|---|
| body-0 hull (shipped) | `[-1.87318, 0.030, -3.359025]` | `[1.87218, 2.105, 3.544025]` | `[3.74536, 2.075, 6.90305]` |
| BmAK chassis box 0 | `[-1.87268, 0.030, -3.361525]` | `[1.87268, 2.105, 3.541525]` | `[3.74536, 2.075, 6.90305]` |

| measure | value | limit | verdict |
|---|---:|---:|---|
| shape deviation | **0.000000 m** | 0.05 m | exact |
| placement deviation | **[0.0005, 0.0000, 0.0025] m = 0.25 cm** | 0.05 m | **MET on the shipped bytes** |

### 4.4 BmAK's three boxes: 1 carried, 2 have no shape instance

Matching each decoded box's JC3 extents against every hull in the file (nearest hull by max extent
difference; a match within 1 cm counts as having a shape):

| box | bone | size m | nearest hull part | best extent dev | shape instance |
|---|---|---|---:|---:|---|
| chassis box 0 (export 169750) | Batmobile_Chassis | 3.745 x 2.075 x 6.903 | 0 | **0.000 m** | **yes** |
| chassis box 1 (export 169750) | Batmobile_Chassis | 3.457 x 1.035 x 6.796 | 0 | **1.040 m** | **no** |
| weapons pod (export 169751) | Batmobile_Rig_Weapons_Trans | 1.894 x 0.398 x 1.662 | 24 | **0.3218 m** | **no** |

**2 of 3 boxes have no shape instance - confirmed** (1 of 3 carried).

### 4.5 Hull slots

| measure | value |
|---|---:|
| polytope (hull) objects | 54 |
| distinct hull shapes referenced by a compound instance | 54 |
| **free hull slots** | **0** |

**0 of 54 hull slots are free - confirmed.** All 54 hull objects are already referenced; 62 bodies
share them, so landing another shape needs insertion, not a free slot.

### 4.6 The constraint

The shipped `physicsc` carries **11 constraint objects of its own** - 9 `hkpLimitedHingeConstraintData`
and 2 `hkpRagdollConstraintData` - none of which is the BmAK chassis constraint. The BmAK asset
declares **1 constraint**, and there is no JC3 constraint writer for it, so it is recorded as a
**named omission**. That is the correct reading of "the 1 constraint is a named omission": 1 is
BmAK's count, **not** a count of objects in the file; the file contains none of BmAK's constraint.

## 5. The 6.1 cm - what the shipped bytes actually say

The brief's placement `[0.0005, 0.061, 0.0025] m` (6.1 cm, gate **NOT MET**) is the body-0 hull at
**y 0.091..2.166 m**, i.e. on the render mesh's ground line. It is the payload with sha256
`0164936b928f821c058c5a154a93b7cadcdbb9baca7d44fb67cb8f18a9399323`, quoted by
`build-d08-health-collision.md` §4 and `build-d13-release-candidate-4.md` §2. **That file is not in
the RC4 tree**, so its bytes were not re-measured here; its 6.1 cm is recorded as NOT MET and is
carried nowhere else in this report.

The RC4 tree ships `fda78f4d…`, in **both** the packed `.ee` member and the aaf staging copy, and its
body-0 hull is at **y 0.030..2.105 m** - 6.1 cm lower, on chassis box 0's own floor. Re-measured
against box 0, that is **0.25 cm**, not 6.1 cm. So:

- the 6.1 cm is **not** reinterpreted as a pass - on the payload it belongs to, the gate is NOT MET;
- the shipped artifact does not reproduce 6.1 cm, so it cannot "confirm" that figure;
- if the operator's acceptance basis is the brief's numbers, the shipped bytes show the box-floor
  correction has already been applied, and the remaining placement deviation is 2.5 mm.

Direct evidence for the shipped y floor, from the collision gate: `body0_hull.min = [-1.87318, 0.03,
-3.359025]`, `body0_hull.max = [1.87218, 2.105, 3.544025]`; and from the 8390 correction, the
`0164936b…` payload's min y is 0.091 and its max y is 2.166.

## 6. UNKNOWN / limits of this pass

| item | status |
|---|---|
| `0164936b…` payload's bytes | **UNKNOWN by direct measurement** - file absent from `Builds/bm-RC4/**`; its 6.1 cm is quoted from `build-d08` §4, `build-d13` §2 and `correction-8390` §2. To re-measure it, restore that sha256 and run `python Tools/scripts/v02a_rc4.py --gate collision` against it. |
| renders / visual silhouette | **not run** (part A instruction). The silhouette gate is geometric, not a screenshot. |
| pose and light gates | **not run** (part B). |
| box "has a shape" test | extent match within 1 cm (nearest hull); a cube could in principle coincide in size without being the box. Box 0 matches its hull at 0.000 m, and the other two are 1.040 m / 0.3218 m away, so the conclusion (2 of 3 missing) is not sensitive to that tolerance. |

## 7. Reproduce

```bash
cd /e/Modding/JustCause3/JC3-Batmobile
python Tools/scripts/v02a_rc4.py --gate silhouette    # §1 (also reads RC2's geometry.json)
python Tools/scripts/v02a_rc4.py --gate census        # §2
python Tools/scripts/v02a_rc4.py --gate interaction   # §3
python Tools/scripts/v02a_rc4.py --gate collision     # §4, §5 (reads the .ee member, not the aaf copy)
python Tools/scripts/bm_vehicle_hull.py --check       # §4.1 donor bodies 62
```

JSON: `tmp/freebuff/verify-v02a/{silhouette,census,interaction,collision}.json`.
The script is read-only: it opens the build, decodes, and writes only under `tmp/freebuff/`.
