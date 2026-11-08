# Canopy, doors and trunk — BmAK mechanism vs JC3 door joints

Status: research + build values. Every BmAK number below is re-read from
`Research/BatmobileGrab/ANIMATIONS.json` / `BONES.json` (dump commands in §9), every JC3
number from `Research/JC3Grab/DOORS.md`, `Research/JC3Grab/DOOR_ANGLES.md` (via
`tmp/freebuff/reports/JC3-door-angles.md`), `Research/JC3Grab/SEAT.md` and the build's own
`Working/Translation/T8_PARTS.*`, `Working/Translation/T9_INTERACTION.*`,
`Working/Parts/bm_vehicle_parts.json`. Nothing here is hand-typed.

Frame: JC3 metres, x = axle (left = −x), y = up (ground 0.02), z = longitudinal, nose at −z.

## 0. Verdict in one table

| channel | BmAK | JC3 carrier | value we set | confidence |
|---|---|---|---|---|
| **canopy** | `CockPit_Mesh` slides **72.48 cm** and turns **12.493°** about a transverse axis; 5 clips, 0.300–0.500 s | `Hood` on a limited hinge about **+X** (26/26 hood rows are X) | part `batmobile_canopy`, `Hood`, axis +X, **0…12.5°**, pivot **(−0.0001, 1.4808, −1.3544)**, 0.433 s open / 0.500 s close | angle + pivot + timing decoded; the **slide cannot be reproduced** (a hinge only rotates) |
| **side doors** | **none exist** — no door bone in 180 bones, no door clip in 253 sequences | donor `sportsmuscle_door_f_l/_f_r` (already deleted by B-04) | keep deleted, no `door_parts` entry | decoded |
| **trunk / rear door** | `Rear_Door_BOTTOM` **120.0° / 44.3151 cm**, `MIDDLE` 24.994° / 29.4731 cm, `TOP` 29.995° / 0.572 cm, 1.000 s open, 0.9333 s close | `Trunk` (20 rows, 19 on X, limits −90…110°) | part `batmobile_rear_door`, `Trunk`, axis +X, **0…110°** (10° short of the clip), 1.000 s / 0.933 s | angles + timing decoded; 120° has no verified X carrier above 110° |
| **winch door** | `Winch_DOOR_Mesh` **40.0°**, 0.6667 s, no notify | no verified carrier (wing parts carry `LeftWing/RightWing` and have **no hinge at all**) | leave static until a carrier is picked | rotation decoded; carrier UNKNOWN |
| **entry / exit hook** | no enter/exit clip in the vehicle package; the canopy+chair clips carry a **sound notify only** | `entry.driver` → `S_ENTER_DRIVER_VEHICLE`, `entry.driver.no.door` → `S_ENTER_DRIVER_NO_DOOR_VEHICLE` | keep `entry.driver` + `entry.driver.no.door` (both shipped on the donor) | hook decoded; **what opens the hinge is code-side, no rate anywhere** |

## 1. BmAK — what the canopy actually does

**Bone.** `CockPit_Mesh` (bone #62, parent `Batmobile_Chassis_Mesh` #1, no children) is the
only canopy bone: the glass is not a separate part and has "no independent pivot to cut on"
(`Working/Translation/T8_PARTS.json`, omission item `canopy`). `Batmobile_Nose_Mesh` (#63)
moves with it. Bind pivot in JC3 metres: **(−0.0001, 1.4808, −1.3544)** (`BONES.json`
`pivot_jc3_m`), i.e. low and behind the driver, not at the roof.

**The five clips** (`ANIMATIONS.json`, package label `Batmobile`; the same five repeat
unchanged in MK2, Funhouse and Joker — `ANIMATIONS.md` seq table lines 85–91, 122–128,
159–165, 196–203):

| clip | AnimSet | frames | length s | tracks | `CockPit_Mesh` | `Batmobile_Nose_Mesh` | notifies |
|---|---|---:|---:|---:|---|---|---|
| `Cockpit_Open` | `BM_Batmobile_Chassis` | 14 | **0.4333** | 23 | 72.3771 cm / **12.445°** | 39.6914 cm / 0.000° | 1 × `AnimNotify_Sound` |
| `Cockpit_Open_Idle` | `BM_Batmobile_Chassis` | 2 | 0.0333 | 23 | 0 / 0 (hold) | 0 / 0 | — |
| `Cockpit_Close` | `BM_Batmobile_Chassis` | 16 | **0.5000** | 23 | 72.4813 cm / **12.493°** | 41.0135 cm / 0.000° | 1 × `AnimNotify_Sound` |
| `Batmobile_V2_Cockpit_Open` | `Batmobile_V2_Pose_States` | 10 | **0.3000** | 3 | 71.0094 cm / **11.227°** | 45.3528 cm / 0.000° | 1 × `AnimNotify_Sound` |
| `Batmobile_V2_Cockpit_Close` | `Batmobile_V2_Pose_States` | 10 | **0.3000** | 21 | 71.0094 cm / **11.227°** | 45.3528 cm / 0.000° | 1 × `AnimNotify_Sound` |

Read strictly:

* **Two motions at once** — a ≈0.71–0.72 m translation *and* an 11.2–12.5° rotation. The
  nose moves 39.7–45.4 cm with **zero** rotation, so the canopy group slides as a unit and
  only the cockpit shell tips. A JC3 hinge reproduces the rotation, **not** the slide
  (T8 UNKNOWN #3, unchanged).
* **Angles**: two families — base clips 12.445/12.493°, V2 clips 11.227/11.227°. The
  difference is the open/close end pose (base opens 0.068° further), not noise.
* **Rates**: mean `Cockpit_Open` 12.445 / 0.4333 = **28.72 °/s**, `Cockpit_Close`
  12.493 / 0.5 = **24.99 °/s**, V2 pair 11.227 / 0.3 = **37.42 °/s**; peak across the clips
  **136.09 °/s** (T8 P-06, `[−1.0, 0.0, −0.0]` axis, i.e. transverse = hinge X in JC3).
* **`Cockpit_Open_Idle` is a 2-frame hold** (0.0333 s, nothing moves) — it is the open
  end-pose to park on while Rico is outside, not an animation.
* **Notify content**: the class is `AnimNotify_Sound` for all five (`RAnimNotify_Script`
  never appears on a canopy clip; the package total is 204 sound vs 35 script — 
  `ANIMATIONS.md` line 21). **No script notify means no game-logic hook inside the clip**:
  the canopy does not tell the game "open" or "closed" — whatever plays it owns the timing.
* **Duplication**: all four Batmobile skins ship the identical pair, so a sound/anim choice
  made for one is valid for all four.

## 2. BmAK — how the canopy links to the entry pose

There is **no enter or exit sequence in the vehicle packages**. What the vehicle owns is the
**chair**, in two clips of its own:

| clip | frames | length s | `Batmobile_Bone_Chair_Rot_001` | `Batmobile_Bone_Chair_Root` | notifies |
|---|---:|---:|---|---|---|
| `Batmobile_V2_Chair_Open` | 68 | **2.2333** | 23.672° / 56.6396 cm | 150.7468 cm | 1 × `AnimNotify_Sound` |
| `Batmobile_V2_Chair_Close` | 69 | **2.2667** | 44.612° / 49.2808 cm | 150.7468 cm | 1 × `AnimNotify_Sound` |

* The seat assembly lifts **1.507 m** and rotates — that is the physical act of standing
  the driver up out of a low cockpit, i.e. the vehicle-side half of the entry pose.
* **The link is track ownership, not a notify.** `Batmobile_V2_Cockpit_Open` carries
  `Batmobile_Bone_Chair_Rot_001` as one of its **3** active tracks (and V2 close among its
  21) — the canopy clip holds the chair pose while the shell moves. The base
  `Cockpit_Open` / `Cockpit_Close` (23 tracks) do **not** carry the chair at all.
* **Ordering by length**: canopy **0.300–0.500 s** vs chair **2.233–2.267 s** — the canopy
  finishes while the chair is still moving. So the shipped ordering is: shell opens first,
  seat follows over ~4.5× longer.
* **No file links the canopy clip to an entry state.** The pairing "canopy opens on entry"
  is the project decision MOD-4, carried in `Working/Translation/T15_WORLD.md` T-WLD8 ("the
  canopy opens instead of a door") and `T8_PARTS.md` P-06 verify line, and echoed by the
  audio ledger (`t12_audio_map.json` A-06: driver-door-open ↔ `Play_CockpitOpen`). The clip
  set (open / idle / close) is consistent with it; the trigger itself is not in the files.
* The driver-category clips in the grab are the Joker package's `BatMobile_Stand_Out`
  family (`ANIMATIONS.md` `driver/Batman`, e.g. export 361/411) — takedown / stand-out
  clips on a Batman skeleton, not a seated-in-car pose. **The seated pose is not in the
  vehicle package** (same conclusion as the JC3 side, §5).

## 3. BmAK — doors and trunk

* **No side doors.** `BONES.json` (180 bones) has no door bone and `ANIMATIONS.json`
  (253 sequences) has no side-door clip; the only door-shaped bones are `Rear_Door_TOP`,
  `Rear_Door_MIDDLE`, `Rear_Door_BOTTOM` and `Winch_DOOR_Mesh`. That is the evidence behind
  B-04's "the Batmobile has no doors" removal (`Working/Parts/bm_vehicle_parts.json`,
  `removals[]`).
* **Rear door (the trunk)** — `Batmobile_V2_Back_Door_Open`, `Batmobile_V2_Pose_States`,
  **31 frames, 1.000 s**, 27 tracks, 1 × `AnimNotify_Sound`:

  | bone | translation | rotation |
  |---|---:|---:|
  | `Rear_Door_BOTTOM` | 44.3151 cm | **120.0°** |
  | `Rear_Door_MIDDLE` | 29.4731 cm | 24.994° |
  | `Rear_Door_TOP` | 0.572 cm | 29.995° |

  `Batmobile_V2_Back_Door_Close` is the mirror: **29 frames, 0.9333 s**, same per-bone
  maxima. **A three-way segmented door** whose bottom panel swings 120° while the middle and
  top panels only tilt ~25–30° and the whole group translates up to 0.51 m.
* **Winch door** — `Batmobile_V2_Winch_Door_Open`, 21 frames, **0.6667 s**, 2 tracks,
  **no notify**; `Winch_DOOR_Mesh` rotates **40.0°**, 0 cm.

## 4. JC3 — the door joint model

A JC3 door is three things and **no animation**: a behaviour name in
`vehicle_common.all_door_part_properties`, a bare `part_index` in the parts module's
`door_parts[]`, and an `hkpLimitedHingeConstraintData` in `.physicsc`
(`Research/JC3Grab/DOORS.md` §intro). Nothing stores an open angle, a speed, a curve or an
interaction; the travel is the hinge's two limits (+0x0FC/+0x100 rad) and the drive is
code-side.

**Donor (v0300 Serpente)** — the vehicle the Batmobile is built on:

| part | behaviour | axis | limits | pivot | parent | damage |
|---|---|---|---|---|---:|---|
| `sportsmuscle_door_f_l` | `FrontLeftDoor` | (0, −1, 0) | 0…80° | (−1.018, 0.622, −0.771) | 0 | UNKNOWN (not in the cached door rows) |
| `sportsmuscle_door_f_r` | `FrontRightDoor` | (0, 1, 0) | 0…80° | (1.018, 0.622, −0.771) | 0 | UNKNOWN (not in the cached door rows) |
| `sportsmuscle_hood_signature` | `Hood` | (1, 0, 0) | **0…70°** | (0, 1.0572, −0.8478) | 3 | **`Land_Hood`** |

Fleet facts that decide our carriers (`DOORS.md` §2, `DOOR_ANGLES`):

* **233 entities scanned, 173 with door parts, 338 door rows, 334 on a limited hinge**
  (`tmp/freebuff/reports/JC3-door-angles.md`); the 4 hinge-less rows are propeller wings
  (`LeftWing`/`RightWing`, `constraint_index` −1).
* **Axis census** of the 220 hinged rows: **X (transverse) 60**, Y (vertical) 132, Z
  (longitudinal) 28. A canopy that tips up is an ordinary X-axis row.
* By behaviour: `Hood` **26 rows, all X, 0…90°**; `Trunk` **20 rows, 19 X / 1 Y, −90…110°**;
  `FrontLeftDoor` 55 (X 5, Y 44, Z 6); `FrontRightDoor` 41 (Y 39, Z 2) up to 120°.
* Axes are general (e.g. `bavariumtank_hatch` (0.999, −0.04, 0)) — an X carrier does not
  have to be exactly (1, 0, 0).
* Only the hood has a stated damage type in the T-8 record (`Land_Hood`); the two door
  rows' damage class is not in the cached door data and is left UNKNOWN above.

**Frequency of the angle pairs** (`DOOR_ANGLES` fleet table): 0…80° 203 rows, 0…90° 31,
0…30° 25, 0…150° 16, 0…130° 8, 0…100° 6, 0…120° 4. So 0…12.5° (the canopy's real swing)
and 0…110° (trunk) are both inside the authored vocabulary, but a **12.5° canopy is far
under the shipping norm** — the hinge limit is ours to author, not a fleet step.

## 5. JC3 — the enter/exit hook, and the pose

| question | answer | evidence |
|---|---|---|
| What places Rico | `entry.driver` (`CInteractionGraphEntry`, state **`S_ENTER_DRIVER_VEHICLE`**) and its siblings; the donor carries **both** paths — with a door and `entry.driver.no.door` → **`S_ENTER_DRIVER_NO_DOOR_VEHICLE`** | `DOORS.md` §4, `t9_interaction.json` |
| How common the branch is | 21 of 55 cached graphs carry both, 4 only no-door, 30 neither; the donor is in the *both* group | `DOORS.md` §4 |
| Does anything in the entity open the part | **No.** The donor container is 566 members and holds **0 animation files**; the swing is not authored in the entity | `DOORS.md` §4 |
| Door speed | **UNKNOWN everywhere** — no rate field, no animation curve | `DOORS.md` §5 |
| What the state actually triggers | code. `S_ENTER_DRIVER_VEHICLE` → `ACT_ENTER_VEHICLE` and the character state machine; the vehicle side is a transform + a state string | `SEAT.md` §1–2 |
| The close-side hook that exists | `entry.pull.up.to.stunt.hood.close` → **`S_PULL_UP_TO_STUNT_CLOSE_VEHICLE`** (placed); `exit.ai.driver.to.hood` → `S_EXIT_DRIVER_TO_HOOD_VEHICLE` | `t9_interaction.json` |
| The pose itself | not on the car: `rico_base.afsmb` / `.asb`, **40 vehicle classes, 382 clip names** (`car` 2, `car/low` 23, `car/med` 35, `car/circuit` 9, …) | `SEAT.md` §2 |
| Seat height the pose assumes | `Land_Seat` hull centres 0.855 / 0.855 / 0.894 m; nearest to the Batmobile `Driver` hip 0.8647 m is `sportsmuscle_f_l_seat` at 0.855 m (**10 mm**) | `SEAT.md` §3 |

The donor's **`hood.close` entry is the only shipped "close" hook** — a stunt pull-up that
closes the vehicle over the driver. It is the natural state to hang the canopy/turret-shell
close on if a close needs an entry rather than an exit.

## 6. Where the build stands today

| item | state | source |
|---|---|---|
| side doors | **removed** — `sportsmuscle_door_f_l` (1) and `_f_r` (2), windows/mirror reparented to `sportsmuscle_body` (0) | `Working/Parts/bm_vehicle_parts.json` `removals[]`, `reparent[]` |
| `door_parts[]` | **`[25]`** only — `sportsmuscle_hood_signature`; note: "the shipped list minus 1 and 2" | same file, `door_parts` block |
| canopy part | **none** — T8 P-06 has `part: null` (`Hood`, geometry stays in the shell), so no `door_parts` row can reference it | `T8_PARTS.md` P-06, `bm_vehicle_parts.json` `omissions[]` |
| canopy channel | `door`, behaviour `Hood`, donor hinge axis **agrees** with the BmAK joint, donor limits 0…70° | `T8_PARTS.md` P-06 |
| entry objects | left **x −1.571**, right **x 1.5744**, y **1.15**, z **−0.95** (both sides, 0.10 m clearance) | `T9_INTERACTION.md` §4 |
| roof / stunt anchors | roof **y 2.0811** at z −0.5; stunt point **y 2.2467** at z −0.5 | `T9_INTERACTION.md` §4 |
| hood anchor | `entry.pull.up.to.stunt.hood.close` at **(0.0005, 1.5265, −2.14)** | `T9_INTERACTION.md` §4 |
| seat socket | **(−0.0025, 0.8647, −1.0654)**, 24 mm above the cushion (y 0.8407) | `Research/BatmobileGrab/COCKPIT.md` §2 |
| roof above the driver | liner **y 1.9661**, skin 1.9914, **opaque** (0 of 63 rays hit glass) | `COCKPIT.md` §3 |

Two consequences a builder must not skip:

1. **Nothing in the build moves the canopy today.** The `door_parts` row points at part 25,
   which is the Serpente hood's shell geometry — not the canopy. To animate the canopy the
   glass + roof have to be **cut out as their own part** (a B-02 face-level cut, exactly as
   the missile covers need, T8 UNKNOWN #4) and that part's index written into `door_parts[]`.
2. **The entry line is the side, the canopy is overhead.** Both entry anchors sit at
   y 1.15 — chest height at the side of a car with no door — while the canopy pivots at
   y 1.4808. So the shipped decision is: the side is open (no door part), the canopy opens
   above for the stand-out, and the side anchors stay as they are. Do not raise the entry
   points to the canopy; that would place Rico on the roof.

## 7. The values we set

### 7.1 Canopy — `batmobile_canopy`

| field | value | from |
|---|---|---|
| part | new part, canopy glass + roof liner cut from `CockPit_Mesh` geometry, per LOD 1…5 | T8 P-06 + B-02 cut rule |
| behaviour | **`Hood`** | donor + 26/26 hood rows on X |
| hinge axis | **+X** (1, 0, 0) | BmAK `[−1, 0, −0]` local +Y ⇒ transverse; donor hood X; "axis agrees" (T8) |
| pivot | **(−0.0001, 1.4808, −1.3544)** m | `BONES.json` `CockPit_Mesh.pivot_jc3_m` |
| limits | **0…12.5°** | max of the two families (12.493° close / 12.445° open); V2 pair 11.227° |
| open timing | **0.433 s**, 12.445°, mean 28.72 °/s | `Cockpit_Open` |
| close timing | **0.500 s**, 12.493°, mean 24.99 °/s | `Cockpit_Close` |
| alternate (V2) | 0.300 s / 0.300 s, 11.227°, 37.42 °/s | the `Batmobile_V2_Cockpit_*` pair |
| peak rate | **136.09 °/s** | T8 P-06 |
| end pose to hold | 0.033 s hold, nothing moving | `Cockpit_Open_Idle` |
| damage type | **`Land_Hood`** | donor row |
| lost motion | the **71.0–72.5 cm slide** and the 39.7–45.4 cm nose travel | hinges only rotate (`DOORS.md` §intro) |

Which of the two families to take: the **base pair (0.433 / 0.500 s, 12.5°)** is the one to
author. It is the longer, more readable motion, its 12.493° is the largest angle BmAK ever
uses, and 0.433/0.500 s bracket the 2.23 s chair lift the way the shipped ordering does.

**The 0…70° donor limit must not be inherited.** At 70° the canopy would pass through the
roof line and end up over the windscreen; the file's own number is 12.5°. Write
`0…12.5°` (or 0…12.493° rounded on the 0.5° grid the fleet uses — 12.5 fits).

### 7.2 Trunk / rear door — `batmobile_rear_door`

The BmAK rear door is **three stacked panels**, not one:

| bone | rotation | translation | as a JC3 part |
|---|---:|---:|---|
| `Rear_Door_BOTTOM` | 120.0° | 44.3151 cm | behaviour `Trunk`, axis +X, **0…110°** (fleet `Trunk` X max; 10° short of the clip) |
| `Rear_Door_MIDDLE` | 24.994° | 29.4731 cm | second `Trunk` part, 0…25° |
| `Rear_Door_TOP` | 29.995° | 0.572 cm | third `Trunk` part, 0…30° |

| field | value |
|---|---|
| open timing | **1.000 s** (`Batmobile_V2_Back_Door_Open`, 31 frames) |
| close timing | **0.9333 s** (`Batmobile_V2_Back_Door_Close`, 29 frames) |
| notify | 1 × `AnimNotify_Sound` on both — no script hook |
| sums | whole group translates up to **51.0594 cm**; 120° is the largest single rotation in the whole car |

If the 120° is wanted exactly, a carrier with an X-axis 0…120° pair is needed — the fleet
table shows 0…120° exists on 4 rows but `DOOR_ANGLES` does not pin their axes; **UNKNOWN**
until one is looked up. Until then author 0…110° and accept the 10° shortfall, or split the
bottom panel's 120° across `Trunk` (110°).

### 7.3 Doors

**None.** BmAK has no side-door bone or clip, the build removed parts 1 and 2, and the JC3
entry graph keeps both driver paths. Keep `entry.driver` + `entry.driver.no.door` and leave
`door_parts[]` without the removed indices; do not add a `FrontLeftDoor`/`FrontRightDoor`
carrier, because there is no geometry for it to move (the door meshes are gone and the
windows/mirror now hang on `sportsmuscle_body`).

### 7.4 Winch door

`Winch_DOOR_Mesh` 40.0°, 0 cm, 0.6667 s, no notify, 2 tracks. Carrier: **UNKNOWN** —
`CargoBayDoor` (0…90°, X) is the nearest behaviour by shape, but no cached module has been
checked for a 40° X hinge on a small panel. Leave static until one is.

## 8. Timings: what can and cannot be authored

| quantity | can we write it into JC3? |
|---|---|
| hinge angle / travel | **yes** — `hkpLimitedHingeConstraintData` +0x0FC/+0x100 rad, 0.5° grid |
| hinge axis / pivot | **yes** — same constraint, frame A |
| which part | **yes** — `door_parts[].part_index` + behaviour in `all_door_part_properties` |
| **speed / duration** | **no** — `all_door_part_properties` carries `target_position_variable`, `lod`, `use_target_position_as_angle` and **no rate** (T8 UNKNOWN #2). The 0.433/0.500/1.000/0.933 s numbers are therefore **acceptance criteria for Q-1 #3**, not file values |
| trigger (entry → open) | **no** — the entity holds no animation and no door linkage; the state name is the contract, the code does the rest |

So the deliverable for B-05 is: the angles and pivots above go into the physics hinges and
the parts module; the durations go into the verification card (open completes inside
0.5 s of the entry state firing, close ends within 0.3 s of the shell seating —
`t12_audio_map.json` A-06/A-07 already phrase the audio pass this way).

## 9. Reproduce

```
python -c "import json;d=json.load(open('Research/BatmobileGrab/ANIMATIONS.json'));
[print(s['name'],s['num_frames'],s['sequence_length'],[(b['bone'],b['dpos_cm'],b['drot_deg']) for b in s['moved_bones']])
 for s in d['sequences'] if s['package_label']=='Batmobile' and s['name'] in
 ('Cockpit_Open','Cockpit_Close','Cockpit_Open_Idle','Batmobile_V2_Cockpit_Open',
  'Batmobile_V2_Cockpit_Close','Batmobile_V2_Chair_Open','Batmobile_V2_Chair_Close',
  'Batmobile_V2_Back_Door_Open','Batmobile_V2_Back_Door_Close','Batmobile_V2_Winch_Door_Open')]"
python -c "import json;b=json.load(open('Research/BatmobileGrab/BONES.json'));
[print(i,x['name'],x['pivot_jc3_m']) for i,x in enumerate(b['bones']) if x['name'] in ('CockPit_Mesh','Batmobile_Nose_Mesh')]"
python Tools/scripts/jc3_door_angles.py --check     # 338 door rows, 21/21 oracles
python Tools/scripts/jc3doors.py --check            # the four sampled vehicles
python Tools/scripts/t12_parts.py --check           # T8_PARTS rows
```

## 10. UNKNOWNs (stated, not filled)

1. **The canopy trigger.** No file links `Cockpit_Open` to `S_ENTER_DRIVER_VEHICLE`; the
   pairing is MOD-4, a project decision. The clips carry `AnimNotify_Sound` only.
2. **Canopy drive speed in JC3.** No rate member; how fast the engine swings a `Hood` part
   is code, and the 0.433/0.500 s pair cannot be enforced from the module.
3. **The 120° X carrier.** `Rear_Door_BOTTOM` needs 0…120° about X; `DOOR_ANGLES` reports
   four 0…120° rows without pinning their axes, and no cached `Trunk` row exceeds 110°.
4. **Whether part 25 still owns canopy geometry.** `bm_vehicle_parts.json` keeps
   `door_parts = [25]` (`sportsmuscle_hood_signature`), but the build's
   `parts_manifest.json` names no hood part, so what geometry that row moves in the built
   module is unverified.
5. **The winch door's carrier.** 40° rotation, no behaviour with a verified 40° X hinge.
6. **Which seated pose plays.** `SEAT.md` §4/§7: the vehicle→class mapping is native.
7. **The chair clips' role.** `Batmobile_V2_Chair_Open/Close` (150.7468 cm, 2.233 s) are the
   only 1.5 m motion on the vehicle and read as the stand-out lift, but no file names them
   as an entry/exit animation.
