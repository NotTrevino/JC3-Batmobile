# collision-rows-corrected - the drivable BmAK numbers behind T-CO1, T-P3 and t16_collision.json

## STATUS

**done - 9 proposed corrections written to new files only; `T_ROWS.jsonl` (sha256 `8996b60a5370d932…`)
and `t16_collision.json` (sha256 `ebc0f4b7ef806875…`) are unedited. The drivable asset carries
3 boxes + 56 convex element boxes, and its largest box is `Batmobile_Chassis` box 0 at
690.305 x 374.536 x 207.5 cm - not the wreck's 316.155 cm wheel box. 9/9 checks pass, `--check` PASS.**

Files written:

- `Tools/scripts/t_collision_corrected.py` (`--write` / `--check`; reads the censuses, never edits a row)
- `Working/Translation/COLLISION_ROWS_CORRECTED.json` (8,100 B - old, new, rule, source, label per correction, `applies: false`)
- `Working/Translation/COLLISION_ROWS_CORRECTED.md` (11,702 B - the note)
- `tmp/freebuff/reports/collision-rows-corrected.md` (this card)

Untouched: `Working/Translation/T_ROWS.jsonl`, `Working/Translation/t16_collision.json`,
`COLLISION_SOURCES_AUDIT.md`, all research censuses. No game launched or attached (§3).

---

## 1. The derivation rule (one rule for all three artefacts)

```
drivable boxes        = every decoded `- box N: extents [...]` line in COLLISION_GEOM.md   = 3
drivable convex boxes = header convex counts 43 + 13 in COLLISION_CONVEX.md                = 56
drivable shapes       = boxes + convex element boxes                                       = 59
largest drivable box  = max by longest axis over the decoded boxes = Batmobile_Chassis box 0
box_m                 = extents_cm / 100
```

Inputs, all **decoded**:

| box | export | bone | extents X/Y/Z (cm) | centre (cm) |
|---:|---:|---|---|---|
| 0 | 169750 | `Batmobile_Chassis` | 690.305 / 374.536 / 207.500 | 9.000, 0.000, 106.750 |
| 1 | 169750 | `Batmobile_Chassis` | 679.585 / 345.688 / 103.500 | 0.000, 0.000, 79.000 |
| 0 | 169751 | `Batmobile_Rig_Weapons_Trans` | 166.177 / 189.365 / 39.800 | -30.500, -0.000, 93.250 |

Convex element unions (**decoded**): 169748 = 695.4123 / 492.9222 / 294.5026 cm over 43 elements;
169749 = 670.9457 / 318.3124 / 224.0855 cm over 13.

The wreck asset (`PHYSICS.md`, `Batmobile_V3_Destroyed_Physics`) is 32 bodies per vehicle with
largest **317.942 cm** (`SUSP1_Wheel_Rear_Right_Mesh`); its own doc says "There is no chassis
body". So every figure below that quotes 32 / 316.155 / 3.1615 is a wreck figure.

## 2. The nine corrections

| # | artefact | field | old | new | label |
|---:|---|---|---|---|---|
| 1 | `T_ROWS.jsonl:86` (T-CO1) | `cells[1]` | `32 boxes (bone, centre, extents)` | `3 drivable boxes (bone, centre, extents) + 56 convex element boxes; the 32-box set is the destroyed wreck` | decoded counts + derived sum |
| 2 | `T_ROWS.jsonl:49` (T-P3) | `cells[1]` | `32 collision bodies (boxes)` | `3 drivable collision bodies (boxes) + 56 convex element boxes` | decoded counts + derived sum |
| 3 | `T_ROWS.jsonl:49` (T-P3) | `cells[4]` | `... 11 driveable boxes map onto 7 donor hull slots; 21 are not driveable collision ...` | `... 11 wreck bodies (8 wheel/suspension + 2 doors + 1 cockpit) map onto 7 donor hull slots; they are not the drivable car's collision (the drivable asset has 3 boxes + 56 convex element boxes); 21 wreck bodies are 18 debris, identity box, turret and fin ...` | derived partition of decoded counts |
| 4 | `t16_collision.json` | `bmak.bodies` | 32 | **3** | decoded |
| 5 | `t16_collision.json` | `bmak.box_count` | 32 | **3** | decoded |
| 6 | `t16_collision.json` | `bmak.categories` | `{cockpit 1, destruction debris 18, door 2, jet fin 1, root 1, turret 1, wheel/suspension 8}` | `{Batmobile_Chassis: 2, Batmobile_Rig_Weapons_Trans: 1}` | decoded |
| 7 | `t16_collision.json` | `bmak.largest.bone` | `SUSP1_Wheel_Rear_Left_Mesh` | **`Batmobile_Chassis`** | decoded |
| 8 | `t16_collision.json` | `bmak.largest.extents_cm` | `[316.155, 63.418, 109.881]` | **`[690.305, 374.536, 207.5]`** | decoded |
| 9 | `t16_collision.json` | `bmak.largest.box_m` | `[3.1615, 0.6342, 1.0988]` | **`[6.90305, 3.74536, 2.075]`** | derived (x 0.01) |

Two details worth naming:

- the quoted 316.155 cm is `SUSP1_Wheel_Rear_**Left**_Mesh`, which is the wreck's **second** largest
  box - the wreck's own largest is 317.942 cm (`..._Right_Mesh`), so the old triple was not even the
  wreck's superlative;
- T-P3's `11 / 21` arithmetic is *correct as a partition of the wreck* (8 wheels + 2 doors + 1
  cockpit = 11; 18 debris + root + turret + fin = 21). The error is calling those 11 "driveable
  boxes" - they are wreck bodies of the asset that has no chassis.

## 3. Commands (verbatim)

```
$ cd E:/Modding/JustCause3/JC3-Batmobile && python Tools/scripts/t_collision_corrected.py --write; echo "write_exit=$?"; python Tools/scripts/t_collision_corrected.py --check; echo "check_exit=$?"
wrote Working/Translation/COLLISION_ROWS_CORRECTED.json (8100 chars)
wrote Working/Translation/COLLISION_ROWS_CORRECTED.md (11694 chars)
9/9 checks pass, 9 corrections
write_exit=0
CHECK PASS
check_exit=0
```

The first run, before the parser was fixed - kept so the final pass is not the only evidence:

```
$ python Tools/scripts/t_collision_corrected.py --write
Research/BatmobileGrab/COLLISION_GEOM.md: no box lines decoded
write_exit=1
```

(cause: the doc indents its bullet lines by two spaces and the regex was anchored on `- box`; the
anchors now allow leading whitespace.)

```
$ python -c "... dump COLLISION_ROWS_CORRECTED.json ..."
applies False verdict PASS
- line 86 (T-CO1) cells[1] | "32 boxes (bone, centre, extents)" -> "3 drivable boxes (bone, centre, extents) + 56 convex element boxes; the 32-box set is the destroyed wreck"
- line 49 (T-P3) cells[1] | "32 collision bodies (boxes)" -> "3 drivable collision bodies (boxes) + 56 convex element boxes"
- line 49 (T-P3) cells[4] | "written (G2-30): 11 driveable boxes map onto 7 donor hull slots; 21 a -> "written (G2-30): 11 wreck bodies (8 wheel/suspension + 2 doors + 1 cockpit) map onto 7 donor hull slots; they
- bmak.bodies bodies | 32 -> 3
- bmak.box_count box_count | 32 -> 3
- bmak.categories categories | {"cockpit": 1, "destruction debris": 18, "door": 2, "jet fin": 1, "roo -> {"Batmobile_Chassis": 2, "Batmobile_Rig_Weapons_Trans": 1}
- bmak.largest.bone bone | "SUSP1_Wheel_Rear_Left_Mesh" -> "Batmobile_Chassis"
- bmak.largest.extents_cm extents_cm | [316.155, 63.418, 109.881] -> [690.305, 374.536, 207.5]
- bmak.largest.box_m box_m | [3.1615, 0.6342, 1.0988] -> [6.90305, 3.74536, 2.075]
census {"drivable_boxes": 3, "drivable_convex_elements": 56, "drivable_shapes_total": 59, "largest_drivable_bone": "Batmobile_Chassis", "largest_drivable_cm": [690.305, 374.536, 207.5], "wreck_bodies_per_vehicle": 32, ...}
```

```
$ sha256sum Working/Translation/T_ROWS.jsonl Working/Translation/t16_collision.json | cut -c1-20
8996b60a5370d932f437
ebc0f4b7ef806875d36a
```

The ledger hash matches the one `BLOCKED_PROPOSALS.md` pins, and both files keep their old values on
disk - the script's check 6 asserts exactly that, so a future edit to either file fails this card
rather than silently making the "old" column a lie.

## 4. The nine checks

1. `COLLISION_GEOM.md` yields exactly 3 boxes, listed by bone and extents.
2. The largest is `Batmobile_Chassis` box 0 of export 169750 at 690.305 / 374.536 / 207.5 cm.
3. `COLLISION_CONVEX.md`'s header counts (43, 13) equal its decoded counts and sum to 56.
4. `PHYSICS.md` is 32 wreck bodies per vehicle and carries the no-chassis verdict.
5. The quoted 316.155 is a wreck box and is the wreck's **second** largest.
6. The old values are still what the artefacts say (nothing edited).
7. The wreck partition recomputes to 11 / 21.
8. The new largest equals the max of the decoded boxes; `box_m` equals `cm / 100`.
9. Every correction changes the value and carries a source and a label.

## 5. UNKNOWN (with what was tried)

1. **Which mode's convex set is live.** `COLLISION_GEOM.md` records `active_mesh_per_mode: UNKNOWN`
   (the mode enum is not serialised in the archetype or the CDO it walked). The corrected count
   therefore states both setups (43 + 13), not one.
2. **The chassis boxes' rotation.** The doc decodes extents and centres and says the rotation is not
   decoded, so 690.305 x 374.536 x 207.5 cm is the box's local frame, not a world AABB.
3. **The axes.** The doc's own oracle says "Frame axes are not proven"; the triple is quoted in the
   doc's X/Y/Z order with no re-mapping.
4. **How many of the 3 boxes the build uses.** T-22's slot binding is built on the wreck census;
   re-deriving it from the drivable boxes is not in this card.
5. **Whether editing `t16_collision.json` breaks its consumers.** `t22_collision.py` reads
   `bmak.bodies` / `largest` for the slot binding, the 11 -> 7 map and radius x k; that consumer was
   not re-read here. Applying corrections 4-9 needs it checked in the same pass - flagged in the note,
   not guessed.
