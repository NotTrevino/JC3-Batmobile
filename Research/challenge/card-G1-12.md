# Assumption challenge — G1-12 · Pursuit ↔ battle pose deltas

Challenger: Freebuff (did not write this card). Date: 2026-10-30. Read-only: nothing under
`GRAB_BACKLOG.md`, `MODLOG.md`, `Tools/`, `Working/`, the rest of `Research/` or the game install
was written; no game launched, nothing installed into `D:\Games`, nothing committed. This report
is the only file written.

Inputs read: `GRAB_BACKLOG.md` §0.5 (R1–R14, lines 71–91), the G1-12 card (lines 449–455), the
§12 row, `MODLOG.md` §"G1-12 · Pose deltas — done" (line 8117), the outputs
`Research/BatmobileGrab/POSES.{json,md}`, the script `Tools/scripts/grab_poses.py`, and the data
it reads (`BONES.json`, the LOD0 `.pskx`, `Playable_Batmobile_SF__Batmobile_V2_Pose_States.json`
and `Playable_Batmobile_SF__BM_Batmobile_Chassis.json` under `E:\Modding\_BmAKgrab\anims\keys\`).

## VERDICT

**The geometry pipeline is sound and independently reproducible; the pose it is pointed at is the
wrong one, and one headline number is therefore wrong by 0.25 m.** 16 assumptions tested:
**9 HOLD, 6 WEAK, 1 BROKEN.**

What holds: an independent re-implementation (own quaternion composition, own skinning, only the
one transform imported) reproduces both bounding boxes to 0.1 mm — `3.4954 × 2.3415 × 7.0257 m`
and `4.6910 × 2.8650 × 7.4434 m`; the JC3 frame is a proper rotation (`det = +1`, orthogonal) and
orients the car X width / Y up / Z length with the nose at -Z (front hubs z = -2.570,
rear z = +2.459); the pursuit frame 0 is the rest pose (chassis channel ≈ identity) and its
x/z box is `stations.json`'s independently measured `body_bbox` to 1.4 mm; the 0.020 m floor is a
tyre (the lowest LOD0 point is owned by `Wheel_Rear_Right_Vis`) and the 2.361 m top is the body
(`Batmobile_Chassis_Mesh`); local +X is the wheel axle (front-left tyre extent 0.731 m in X
against 1.365/1.367 m in Y/Z); `Tank_Strafe` really is the strafe stance (root translates
4.8891 m with 0.004° yaw, wheel axles turn +X → -Z by 90.0°); the four packages' PSAs are
byte-identical (`md5 c698bb81…` ×4), so one package's keys stand for all four; the keyframe input
hash in `POSES.json` still matches the file `--check` consumes.

What breaks: **the record calls `Batmobile_V2_Tank_Spread_Open_Game` "the gameplay transition" and
its last frame the battle pose, but the battle-mode idle (`Batmobile_V2_Tank_Idle`, 73 keyed
tracks) and the car's own `Drive_To_Combat` both settle on the *other* endpoint** — chassis
`+0.2263 m`, turret `2.1980 m` — while the `_Game` end sits at chassis `-0.0281 m`,
turret `1.9474 m`. The published "chassis settles 0.050 m" is therefore `-0.050` where the pose
state says `+0.204`, and the turret raise is `0.633 m` where it is `0.883 m`. The only support
for the choice in the record is the `_Game` suffix plus a check that is a tautology
(`CANON_OPEN.endswith("_Game")`).

```
$ python Tools/scripts/grab_poses.py --check
PASS: Pursuit -> battle (Batmobile_V2_Tank_Spread_Open_Game f0 -> f60): turret +0.633 m, chassis -0.050 m, wheel splay 17.27-19.32 deg; full bbox 3.495 x 2.341 x 7.026 -> 4.691 x 2.865 x 7.443 m; 180/180 bones move, 64 articulate. Tank_Strafe adds 90.0 deg wheel yaw.
  bones_total_180                      PASS
  pose_has_all_bones                   PASS
  all_deltas_accounted                 PASS
  fin_bones_present                    PASS
  game_open_close_loop                 PASS
  canonical_is_game_variant            PASS
  game_bbox_wider_than_pursuit         PASS
  game_bbox_taller_than_pursuit        PASS
EXIT=0
```

The card's Done line — "two complete poses (pursuit, battle) with bbox each; every moved bone
listed" — is met formally: two 180-bone poses with bboxes, 180 delta rows each with
`rotation_axis_jc3` and metres. `--check` is stronger than G1-10's: it re-derives, compares the
JSON and MD, and fails on any false entry in `checks`. The defect is not in the arithmetic, it is
in which frame of which sequence is called "battle".

---

## A1 — The `_Game` sequence is the gameplay transition and its last frame is the battle pose

**Test 1 — what does the rest of the data settle on?** Skinned LOD0 boxes for every candidate
battle pose, computed through the same pipeline:

```
Tank_Spread_Open_Game f0     size 3.495 x 2.341 x 7.026 m | min_y 0.020 max_y 2.361
Tank_Spread_Open_Game f60    size 4.691 x 2.865 x 7.443 m | min_y -0.178 max_y 2.687
Tank_Spread_Open f60         size 4.487 x 3.088 x 7.382 m | min_y -0.138 max_y 2.950
Tank_Idle f0                 size 4.487 x 3.087 x 7.382 m | min_y -0.137 max_y 2.950
Drive_To_Combat f0           size 3.496 x 2.342 x 7.026 m | min_y 0.020 max_y 2.362
Drive_To_Combat f60          size 4.487 x 3.088 x 7.381 m | min_y -0.138 max_y 2.950
```

Three sequences land on the 4.487 × 3.088 × 7.382 pose (the record's "cinematic" end), and only
the `_Game` end is alone at 4.691 × 2.865 × 7.443. The decisive one is `Batmobile_V2_Tank_Idle` —
a pose state with 73 keyed tracks, i.e. explicit animation data, not a fallback pose:

```
  Batmobile_V2_Tank_Spread_Open_Game  f-1  turret_y 1.9474 chassis_y -0.0281 rel 1.9755
  Batmobile_V2_Tank_Spread_Open       f-1  turret_y 2.1980 chassis_y  0.2263 rel 1.9717
  Batmobile_V2_Tank_Idle              f0   turret_y 2.1984 chassis_y  0.2267 rel 1.9717
  Drive_To_Combat                     f-1  turret_y 2.1980 chassis_y  0.2263
```

**Test 2 — what the recorded pair measures against what the idle measures.**

```
Batmobile_V2_Tank_Spread_Open_Game   chassis -0.0501 m  turret +0.6327 m  (turret rel +0.6828)
Batmobile_V2_Tank_Spread_Open        chassis +0.2041 m  turret +0.8831 m  (turret rel +0.6789)
```

The turret's height *relative to the chassis* agrees to 3.9 mm in both variants; the whole
0.254 m discrepancy is chassis ride height. So every quantity the card asks for except wheel yaw
is wrong in sign or magnitude: "body lift" is `-0.050 m` in the record and `+0.204 m` in the pose
state; the bbox height is 2.865 m against 3.088 m.

**Test 3 — the evidence the record does have.** The `_Game` open/close pair closes better in
rotation than the cinematic pair:

```
game open0 vs close_end          max bone pos 0.0539 cm  max rot 0.0262 deg
game open_end vs close0          max bone pos 0.0542 cm  max rot 0.0244 deg
cinematic open0 vs close_end     max bone pos 0.0602 cm  max rot 1.6829 deg
cinematic open_end vs close0     max bone pos 0.1195 cm  max rot 1.0237 deg
```

Position closure does not separate them (0.054 vs 0.060 cm); only rotation does, and the record
never computes the cinematic pair, so this comparison is not in the artefact either. The
"gameplay" label itself rests on the suffix alone:

```
"canonical_is_game_variant": CANON_OPEN.endswith("_Game")   # a tautology, not evidence
```

`POSES.md` never mentions `Batmobile_V2_Tank_Idle`, `Drive_To_Combat` or `Bat_Tracker`
(`grep -c` over the file: 0), so the pose states were not searched for the settled battle pose.

**Verdict: BROKEN.** The label and the canonical numbers are contradicted by three independent
sequences, one of which is the battle-mode idle itself. The record does publish both endpoint
sets in `variants`, so the correct numbers are recoverable from `POSES.json` — but the headline
in `POSES.md`, `MODLOG.md`, the `--check` line and `g1x_gate.py`'s APP-6 evidence, and every
`pose_delta` T-12 embeds per bone (`t12_parts.py` line 475), carry the wrong variant.

## A2 — Frame 0 of the open animation is the pursuit pose

**Test.** The chassis channel at frame 0, and the box against the independent measurement:

```
chassis track: pos0 [0.0, 0.0, -0.000248] quat0 [0.0, -4.8e-05, 0.0, 1.0]
chassis bind local: [1.5e-05, 0.0, 0.0]
pursuit bbox min [-1.748, 0.020, -3.420] max [1.747, 2.361, 3.605]
stations.json body_bbox [[-1.747, 0.091, -3.42], [1.748, 2.362, 3.605]]
```

x agrees to 1.4 mm, z to 0.3 mm, the top to 1 mm; the bottom differs by 71 mm because the box
includes tyres (`stations.json` `ground` is 0.02, and the lowest point is a tyre — A6). Frame 0
is the rest pose as *data*: the chassis's own keyed local transform is identity there.

**Verdict: HOLDS.** "Pursuit" is precisely "the car at rest", and that is what the animation's
first frame keys. (It is not evidence that the in-game pursuit idle is unposed, but no other
pursuit pose state exists in the set.)

## A3 — "180 / 180 bones move" is a measurement of the transformation

**Test.** Recount from the delta rows:

```
moved: 180 articulated: 64
deltas with moved but not articulated: 116
```

The `moved` predicate is `world translation ≥ 0.5 mm or world rotation ≥ 0.05°`, and the
chassis alone moves 50.1 mm, so every bone in a hierarchy rooted at the chassis necessarily
qualifies. 116 of the 180 have no parent-relative change at all.

**Verdict: WEAK.** The number is true and correctly defined in the MD ("A moved bone is one with
world translation ≥ 0.5 mm…"), but it is cited as a headline ("180/180 bones move") beside a real
one (64 articulate) and tells the reader nothing: it would be 180/180 for any 5 cm chassis motion.

## A4 — "64 articulate" is the car's articulation count

**Test.** The canonical sequence's keyframe record:

```
Batmobile_V2_Tank_Spread_Open_Game  frames=61 tracks=70 removed_tracks=152
Batmobile_V2_Tank_Spread_Open       frames=61 tracks=74 removed_tracks=152
Batmobile_V2_Tank_Idle              frames=2  tracks=73 removed_tracks=152
```

Only 70 of the 173 skeleton bones have any exported channel in the canonical sequence; 103 were
removed wholesale by the `RemoveTracks` config, and `local_track()` falls back to the bind local
for them. So 64 articulate is "64 of the 70 bones that were exported", and the other 110 are
counted as non-articulating by fallback, not by measurement.

**Verdict: WEAK.** Correct given the input filter, but it inherits G1-10's unaudited
`RemoveTracks` assumption (G1-10 challenge A7) and adds a second dependency on it: the number
cannot exceed what the exporter kept.

## A5 — The fins "stay rigid to the chassis (max 0.000°)"

**Test.** Fin tracks in the canonical sequence, and the fin rows in the record:

```
fin bones: 13
   Batmobile_Rig_Jet_Fins                     track=False removed=-
   Batmobile_Rig_Aero_Flap_L_F                track=False removed=-
   ... all 13: track=False
fin rows: 13, angle_vs_chassis_deg = 0.0 exactly
```

No fin bone has a channel in this sequence, so both poses take the bind local for them and the
relative angle is zero by construction — it would print 0.000 for *any* sequence that omits the
tracks. (The same bones do animate: `Batmobile_V2_Aero_Flap_*_Up/Down` are separate 26-frame
sequences in G1-10.) The list also mixes 12 `Aero_Flap` bones with `Batmobile_Rig_Jet_Fins`, so
"the 13 aero-fin bones" is 12 aero flaps + 1 jet fin.

**Verdict: WEAK.** "Rigid to the chassis in this pose" is true, but `max 0.000°` is a property of
the missing channel, not a measurement, and the record presents it as one. That the transition
does not deploy the fins is supported by G1-10 only through the same filter.

## A6 — The bbox is the car: all 201,338 LOD0 points, linear-blend skinned

**Test.** Independent recomputation with my own quaternion composition and skinning (importing
only `bat_assemble.to_jc3_rot` as the one transform):

```
independent bbox pursuit       3.4954 x 2.3415 x 7.0257 m (min_y 0.0199 max_y 2.3614)
independent bbox battle_game   4.6910 x 2.8650 x 7.4434 m (min_y -0.1784 max_y 2.6866)
recorded pursuit               3.495 x 2.341 x 7.026
recorded battle                4.691 x 2.865 x 7.443
```

Which part owns the extremes:

```
pursuit      min_y 0.0199 owner=Wheel_Rear_Right_Vis | max_y 2.3614 owner=Batmobile_Chassis_Mesh
battle       min_y -0.1784 owner=SUSP2_Wheel_Rear_Left | max_y 2.6866 owner=Batmobile_Rig_Weapons_Turret_Top
Tank_Idle    min_y -0.1367 owner=Wheel_Rear_Right_Vis | max_y 2.9503 owner=Batmobile_Rig_Weapons_Turret_Top
```

`skin_points()` also asserts the RAWWEIGHTS sum to 1 (it raises otherwise) and indexes inside
PNTS/REFSKELT.

**Verdict: HOLDS.** The box is the whole LOD0 mesh, the arithmetic reproduces independently, and
the pursuit box matches the separate `stations.json` measurement. (The height delta does switch
the top owner from body to turret, which the record reports separately as the turret raise.)

## A7 — The JC3 frame and units: metres, X width, Y up, Z length, nose at -Z

**Test.** The transform itself, then the axes:

```
to_jc3_rot basis matrix:
 [[-0.  0. -1.]
  [-1.  0. -0.]
  [-0.  1. -0.]]
determinant: 1.0 orthogonal: True
front hubs z = -2.570 / -2.5699   (stations.json)
rear  hubs z = +2.4589            (stations.json)
front wheel tyre extent: X=0.731 Y=1.365 Z=1.367 m
```

`to_jc3_rot` is a proper rotation (not a reflection), mapping PSK (X length, Y width, Z up) to
JC3 (X = -PSK Y, Y = PSK Z, Z = -PSK X). Front wheels at negative Z, tyre diameter 1.366 m in
the Y/Z plane and the 0.7325 m tyre width in X, so lengths are metres and the nose is -Z.

**Verdict: HOLDS.** Convention, handedness and units all check out numerically; the rotation
handler (`jc3_quat`, axis rotated, angle kept) is valid precisely because the transform is a
proper rotation.

## A8 — The one transform is imported, not re-implemented (R2)

**Test.** The script's imports and the pose path:

```
import bat_assemble as BA
import grab_bones as GB
...
def jc3_point(p_cm): return jc3_vec(p_cm) * SCALE
def skin_points(...): return BA.to_jc3_rot(acc) * SCALE + offset
```

`offset` comes from `BONES.json` (`transform.offset_used`, itself from
`Working/TrueScale/stations.json` and recomputed by `grab_bones.py`), `SCALE = 0.01`, and the
mesh is hashed against `BONES.json`'s LOD0 hash before use.

**Verdict: HOLDS.** R2 is respected for the transform. The PSK hierarchy composition is
re-implemented rather than imported from `grab_bones`, but my independent implementation of the
same convention reproduces the record's boxes (A6), so the duplication is currently harmless.

## A9 — The battle pose can be placed at the pursuit ride height

**Test.** Ground penetration of each pose (points below y = 0):

```
pursuit        min_y  0.0199  below0=0
battle (_Game) min_y -0.1784  below0=284
Tank_Idle      min_y -0.1367  below0=613
```

The record reports the numbers (`bbox_min_y_delta_m = -0.198`) but no statement that the pose is
0.178 m below the plane its own pursuit pose rests on, nor that the battle idle is 0.137 m below
it too — i.e. every battle pose in this set is authored at a lower ride height and something
else (physics/root) must lift it.

**Verdict: WEAK.** The bbox is honest; the consequence is not drawn. A consumer that drops the
battle pose in at the pursuit height (D-2's second variant, MOD-2) will clip the wheels unless
it applies a lift, and 0.178 m of turret "raise" would then partly be the car sitting lower.

## A10 — `Batmobile_V2_Tank_Strafe` is the real strafe stance, not the spread pose

**Test.** Root motion and wheel yaw over the sequence:

```
Tank_Strafe frames 82 | chassis root translation [4.8891, -0.0002, 0] = 4.8891 m | root rotation 0.004 deg
wheel axle start -> end (local 90 deg):
  Wheel_Parent_F_L  89.99 deg  1.000,-0.019,0.000 -> -0.000,-0.019,-1.000  yaw +90.00
  Wheel_Parent_B_R  90.01 deg  1.000,-0.018,-0.000 ->  0.000,-0.019,-1.000  yaw +89.95
```

Pure lateral translation (4.89 m, no yaw) with every wheel turned 90° about the vertical: a
sideways slide, which is what a strafe stance is. The spread sequence instead toes the wheels
17.27–19.32°.

**Verdict: HOLDS.** The two are different mechanisms, and the record's separation of them (using
only the wheel rotation from `Tank_Strafe`, since its root translates) is correct.

## A11 — The 17–19° "splay" is a toe about the vertical, not a spin

**Test.** From the record's wheel rows and the sequence's per-bone local rotation:

```
Wheel_Parent_F_L: axle 1.000,-0.000,0.000 -> 0.944,-0.045,0.328  (signed yaw -19.14)
Wheel_Parent_B_R: axle 1.000,-0.000,-0.000 -> 0.955,0.083,0.285  (signed yaw -16.60)
local rotation of Wheel_Parent_F_L in the sequence: 0.03 deg
SUSP1_Wheel_Front_Left local rotation: 19.32 deg
```

The axle stays almost horizontal (Y component ≤ 0.087) and gains a Z component — that is a yaw
in the ground plane. The wheel bone's own local rotation is 0.03°, so the toe is carried by the
`suspension arm` (`SUSP1`), which is what the record's "relative to the chassis" wording covers.

**Verdict: HOLDS.** The direction and magnitude are both in the data, and the record correctly
does not call this the strafe stance.

## A12 — Local +X is the wheel axle (the assumption behind every yaw number)

**Test.** Bind-pose tyre extent for the front-left wheel, by dominant weight:

```
Wheel_Front_Left_Vis  points=4352  extent X=0.731 Y=1.365 Z=1.367 m
stations.json f_l: tyre_width 0.7325, radius 0.6829 (Ø1.366)
```

The 0.731 m axis is the tyre's width, the other two are the diameter, so the axle is along X in
the JC3 frame, and `qrot(q, [1,0,0])` really is the axle vector for all four wheels.

**Verdict: HOLDS.** Without this the ±90° and ±19° numbers would be measuring the wrong axis; the
geometry confirms the axis used.

## A13 — Frame 60 is the last frame, and loop closure validates the pair

**Test.** `pose()` accepts `-1` and resolves it to `num_frames - 1` (61-frame sequences → frame
60); the closed pair is re-derived independently:

```
game open0 vs close_end          max bone pos 0.0539 cm  max rot 0.0262 deg
game open_end vs close0          max bone pos 0.0542 cm  max rot 0.0244 deg
```

**Verdict: HOLDS** for the frame indexing and the arithmetic (0.054 cm = 0.54 mm, matching
`loop`), and the check does what it says. But closure is **not** evidence that this is the
gameplay pair — the cinematic pair closes in position just as tightly (A1). The record's
`loop` block supports "these two animations are each other's inverse", not "this is the pair the
game plays".

## A14 — "Each transformation sequence" was processed

**Test.** The card's Do step says "for the first and last frame of *each* transformation
sequence". G1-10 classifies 8 distinct names as `transformation`; removing its 2 `Shell` false
positives leaves 6:

```
sequences in POSES variants: Tank_Spread_Close, Tank_Spread_Close_Game,
                             Tank_Spread_Open, Tank_Spread_Open_Game
genuine transformation sequences NOT covered: ['Batmobile_V2_Bat_Tracker', 'Drive_To_Combat']
```

`Drive_To_Combat` is the car's own 61-frame pursuit→combat sequence in `BM_Batmobile_Chassis`
(75 tracks) and is the sequence whose endpoint exposes A1.

**Verdict: WEAK.** The card's Done line only demands two poses, so the card passes; the Do step
is broader than the delivery, and the omission is not stated as a scope limit. It cost the record
the corroborating endpoint that would have caught A1.

## A15 — One package's keys represent the four variants

**Test.** The four `Batmobile_V2_Pose_States.psa` files:

```
c698bb811f493d3c6a2b18eaa6ba5a59  Playable_BatmobileFunhouse_SF/AnimSet/Batmobile_V2_Pose_States.psa
c698bb811f493d3c6a2b18eaa6ba5a59  Playable_BatmobileJoker_SF/AnimSet/Batmobile_V2_Pose_States.psa
c698bb811f493d3c6a2b18eaa6ba5a59  Playable_BatmobileMK2_SF/AnimSet/Batmobile_V2_Pose_States.psa
c698bb811f493d3c6a2b18eaa6ba5a59  Playable_Batmobile_SF/AnimSet/Batmobile_V2_Pose_States.psa
```

**Verdict: HOLDS** for the animation data: the pose deltas are identical for all four vehicle
variants. (The *mesh* differs per variant — `Batmobile_MK2_Skin`, `Batmobile_Jokerfied_Skin` — so
their bboxes are not covered by this record; `VARIANTS.md` is the place for that, and the card
does not ask for it.)

## A16 — `--check` passing proves the card's Done criteria

**Test.** `main()`:

```
fail = [k for k, v in doc["checks"].items() if not v]
if fail: print("FAIL: checks ..."); return 1
...
if json.dumps(old, sort_keys=True) != json.dumps(doc, sort_keys=True): return 1
if OUT_MD.read_text(...) != md: return 1
```

It does assert the `checks` dict and both files (stronger than G1-10's text compare), but six of
the eight checks are structural (`bones_total_180`, `pose_has_all_bones`,
`all_deltas_accounted`, `fin_bones_present`, and the two bbox-direction checks) and one is a
tautology (`canonical_is_game_variant` = the constant it tests ends with `_Game`). Nothing checks
that the "battle" frame is the battle pose.

**Verdict: WEAK.** The check proves reproducibility, not the Done criterion's meaning: a
reader-visible "two complete poses (pursuit, battle)" is not something the exit code can test,
and the one check that sounds like it does is vacuous.

---

## What this means for the project, smallest fix first

1. Re-point `CANON_OPEN`/`CANON_CLOSE` at the pose the battle idle holds. The data supports
   `Batmobile_V2_Tank_Spread_Open` (non-`_Game`) with `Batmobile_V2_Tank_Idle` and
   `Drive_To_Combat` as corroboration; if `_Game` really is the gameplay transition, the record
   must at least explain why its end differs from `Tank_Idle` by 0.254 m, and publish both as
   named poses rather than "canonical" and "cinematic". The headline numbers then become
   `chassis +0.204 m`, `turret +0.883 m`, bbox `3.495 × 2.342 × 7.026 → 4.487 × 3.088 × 7.382`.
2. Add `Tank_Idle` (and `Drive_To_Combat`) as a pose/endpoint row; the omission is what let the
   wrong variant pass, and T-12 embeds these deltas per bone.
3. Replace the `canonical_is_game_variant` check with something falsifiable (e.g. "the battle
   endpoint matches the battle idle within 5 mm"), and record the cinematic loop closure next to
   the gameplay one so the choice is visible.
4. State the ground-height caveat: the battle poses sit 0.137–0.178 m below the pursuit ground
   plane, so a variant dropped in at the pursuit height clips its wheels.
5. Reword the fin sentence to "no fin channel is exported in this sequence (so the bones follow
   the chassis); the model's fin sequences are separate", and note that `Batmobile_Rig_Jet_Fins`
   is a jet fin, not an aero flap.
6. Drop or qualify "180/180 bones move" (it is the chassis motion), and note that "64 articulate"
   counts the 70 exported tracks, not the 180-bone skeleton.

No game file, save, dropzone or build was touched; the only write was this report.
