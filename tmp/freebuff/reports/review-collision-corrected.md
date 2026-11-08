# Review — `collision-rows-corrected.md` (task 7227)

**VERDICT: PASS with two corrections to the wording.** All 9 proposed corrections recompute independently (`3` drivable boxes, 43+13=56 convex elements, largest `Batmobile_Chassis` box 0 at 690.305 × 374.536 × 207.5 cm, `box_m` = cm/100, and the old values are still what the untouched artefacts say). Two statements in the corrected text overstate the evidence and should be reworded: the "3 + 56 = 59 shapes" total adds the two **mutually exclusive per-mode** convex sets (per mode it is 46 or 16, not 59), and the replacement text calls the root body an "identity box" where every source calls it `root placeholder`. Neither changes a number; both change what a reader believes the car has.

STATUS: done — the card's own `--check` passes and was run first; the 9 numbers were then recomputed from `COLLISION_GEOM.md`, `COLLISION_CONVEX.md`, `PHYSICS.md`, `t16_collision.json` and `T_ROWS.jsonl` without importing the card's script. No file of the card was modified; `Working/Translation/T_ROWS.jsonl` and `t16_collision.json` are still unedited (their old values are re-read below and agree with the report's "old" column).

## 1. The card's check, run first

```
$ python Tools/scripts/t_collision_corrected.py --check
CHECK PASS
check_exit=0
```

Then `Working/Translation/T_ROWS.jsonl` (sha256 prefix `8996b60a5370d932`) and `t16_collision.json` (`ebc0f4b7ef806875`) carry their old values, which the table above treats as the true "old" column.

## 2. One recomputed number per correction

| # | artefact / field | old (re-read) | new (card) | my recomputation | unit check | axis check | verdict |
|---:|---|---|---|---|---|---|---|
| 1 | T_ROWS:86 (T-CO1) cells[1] | 32 boxes (bone, centre, extents) | 3 drivable boxes + 56 convex element boxes | 3 drivable boxes | count (unitless) | n/a | agree |
| 2 | T_ROWS:49 (T-P3) cells[1] | 32 collision bodies (boxes) | 3 drivable collision bodies (boxes) + 56 convex element boxes | 3 drivable boxes | count (unitless) | n/a | agree |
| 3 | T_ROWS:49 (T-P3) cells[4] | 11 driveable boxes ... 21 not driveable | 11 wreck bodies ... 21 wreck bodies | 11 / 21 | count (unitless) | n/a | agree, wording drift |
| 4 | t16_collision.json bmak.bodies | 32 | 3 | 3 | count (unitless) | n/a | agree |
| 5 | t16_collision.json bmak.box_count | 32 | 3 | 3 | count (unitless) | n/a | agree |
| 6 | t16_collision.json bmak.categories | 7 semantic keys summing 32 | Chassis 2, Rig_Weapons_Trans 1 | {'Batmobile_Chassis': 2, 'Batmobile_Rig_Weapons_Trans': 1} | count (unitless) | bone-keyed, not semantic | agree, scheme change |
| 7 | t16_collision.json bmak.largest.bone | SUSP1_Wheel_Rear_Left_Mesh | Batmobile_Chassis | Batmobile_Chassis | n/a | n/a | agree |
| 8 | t16_collision.json bmak.largest.extents_cm | [316.155, 63.418, 109.881] | [690.305, 374.536, 207.5] | [690.305, 374.536, 207.5] | cm (Z-up check: Z is the smallest, centre Z - extent/2 = 3.0 cm) | BmAK X/Y/Z, not remapped to JC3 | agree, units ok |
| 9 | t16_collision.json bmak.largest.box_m | [3.1615, 0.6342, 1.0988] | [6.9030499999999995, 3.74536, 2.075] | [6.90305, 3.74536, 2.075] | m = cm / 100 | BmAK X/Y/Z, not remapped to JC3 | agree, units ok |

## 3. Units — each numeric row

- **Rows 4–7** are counts; no unit can be wrong, and each recomputes to `3` or the same bone.
- **Row 8 (`extents_cm`)** is centimetres, straight from `COLLISION_GEOM.md`'s decoded floats (`0x40/0x44/0x48`). The unit is corroborated rather than assumed: the doc's own oracle compares 690.305 cm against the body box span 7.025 m, and 6.903 m vs 7.025 m only agrees if these are full lengths in cm. If they were half-lengths the car would be 13.8 m long.
- **Row 9 (`box_m`)** divides by 100 exactly: 690.305/100 = 6.9030499999999995, 374.536/100 = 3.74536, 207.5/100 = 2.075. Agrees with the card's new triple.
- **No row mixes units.** The one place a unit could leak is the card's own prose ("316.155 cm", "3.1615"), and both keep their unit attached.

## 4. Axis order — the part a reader must not skim

**BmAK is Z-up and the triple is X/Y/Z.** Evidence (derived from the decoded box, not assumed): Z is the **smallest** extent (207.5 cm = the car's height) and the centre's Z is half the extent within 3.0 cm (106.75 cm against 103.75 cm), i.e. the box sits on the ground — which only holds if Z is vertical. X = 6.903 m is the length, Y = 3.745 m the width.

**JC3 is not Z-up for a vehicle.** MODLOG §16 (decoded): the merged painted car spans `X -1.061..+1.061`, `Z -2.570..+2.564` and measures 5.134 × 2.123 × 1.388 m — length on **Z**, width on **X**, height on **Y** (front = -Z, §15). So the BmAK triple must be permuted for a JC3 consumer: `(X_bmak, Y_bmak, Z_bmak) → (x=3.74536, y=2.075, z=6.90305)`.

| row | order used by the card | JC3 requirement | risk |
|---|---|---|---|
| 8 `extents_cm` | BmAK X/Y/Z | permute before use | a consumer that reads it as JC3 (x,y,z) gets a 6.9 m **width** |
| 9 `box_m` | BmAK X/Y/Z | same permutation | same |

**Assessment:** the card keeps the pre-existing convention (the old `box_m` was also BmAK order) and its UNKNOWN 3 says axes are unproven and un-remapped, so this is a disclosed limitation, **not a new defect**. It stays a real trap for whoever applies the number: the corrected 6.90305 must not be pasted into a JC3 x slot.

## 5. The two things to reword

1. **"3 + 56 = 59 shapes" mixes two mutually exclusive modes.** The 43 and 13 convex elements belong to `RB_BodySetup` 169748 (battle) and 169749 (pursuit) — one setup is live per mode. Per mode the car therefore has 46 (3 boxes + 43) or 16 (3 boxes + 13) shapes, not 59. The card's UNKNOWN 1 records that the live mode is unknown, but the correction text (rows 1, 2) states the sum as if all 56 were present at once. Fix: "3 drivable boxes + 43 battle / 13 pursuit convex elements (one mode live, which is UNKNOWN)".
2. **"identity box" is a rename of `root placeholder`.** Every source key — `t16_collision.json` and PHYSICS.md's category table — calls that body `root placeholder`. The replacement text in row 3 says "18 debris, identity box, turret and fin", introducing a name no artefact uses. Fix: keep `root placeholder`.

Mechanically the card is sound: the counts are right, the largest box is right by both longest edge and volume (`Batmobile_Chassis` box 0), the 11/21 partition is right (11 + 21 = 32), and the old values are untouched. The old triple was also not even the wreck's superlative: the wreck's largest is SUSP1_Wheel_Rear_Right_Mesh at 317.942 cm, and the quoted 316.155 cm is the second (`SUSP1_Wheel_Rear_Left_Mesh`).

## 6. UNKNOWNs

1. **Which convex mode is live** — UNKNOWN in the card and here; `active_mesh_per_mode` is not serialised in the archetype/CDO that was walked, so the 43/13 split cannot be resolved from files.
2. **The box rotation** — the chassis box's TM is not decoded, so the triple is the box's local frame, not a world AABB. Both the card and `COLLISION_GEOM.md` say so.
3. **Whether a consumer already assumes the axis order** — I did not re-read `t22_collision.py` or any other reader (the card flags the same gap in its UNKNOWN 5). Whether applying rows 4–9 needs a code change in those consumers is therefore UNKNOWN here.
4. **Whether `Physics.Batmobile_V3_Physics` is the drivable asset by more than its name** — the 3-box census is decoded, and the doc's title says "drivable", but no runtime observation ties that PhysicsAsset to the spawned car (G3-07 would). Labelled derived-by-name, not proven.

## 7. Commands run (verbatim)

```
$ python Tools/scripts/t_collision_corrected.py --check
CHECK PASS
check_exit=0

$ python Tools/scripts/t_collision_review.py --write
boxes 3 convex 43+13=56 per-mode totals (46, 16)
largest Batmobile_Chassis box 0 [690.305, 374.536, 207.5] cm
wreck bodies 32 largest SUSP1_Wheel_Rear_Right_Mesh 317.942 cm
partition 11 / 21
wrote E:\Modding\JustCause3\JC3-Batmobile\tmp\freebuff\reports\review-collision-corrected.md
```
