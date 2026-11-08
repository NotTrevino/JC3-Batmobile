# Review — G1-12 · Pursuit ↔ battle pose deltas

Reviewer: independent, read-only. Nothing outside this report was written; no game launched, no git.

Read: `GRAB_BACKLOG.md` §0.5 (R1–R14) and the G1-12 card (line 449), §12 row (line 1280);
`MODLOG.md` §"G1-12 · Pose deltas — done" (8117); `Research/BatmobileGrab/POSES.md` (268 lines),
`POSES.json`, `Tools/scripts/grab_poses.py` (739 lines); inputs `BONES.json`, the LOD0 PSKX and
`Playable_Batmobile_SF__Batmobile_V2_Pose_States.json`.

## VERDICT

**Minor issues.** The measurement work is sound: both poses are complete 180-bone reconstructions
skinned over the full 201,338-point LOD0 mesh, the bbox arithmetic, turret raise, wheel splay/strafe
yaw and loop closure all reproduce, and `--check` is green and byte-compares both outputs. The
defects are a handful of typed literals that should be derived (R11), one name-based claim stated as
fact in the journal (R4/R5), one loose label, and two minor scope/check-strength gaps. No number in
the doc is wrong.

## Check output (verbatim)

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
```

Exit status 0. The done section records the command (`MODLOG.md:8137`) but not its output — see
issue 7. Out paths
`Research/BatmobileGrab/POSES.json` (225,437 B) and `POSES.md` (28,430 B, 268 lines) both exist; the
§12 row cites `POSES.md` + the MODLOG section, and the card's Out names both files.

**Done criterion vs `--check`:** card Done = "two complete poses (pursuit, battle) with bbox each;
every moved bone listed". `pose_has_all_bones` asserts 180 bones in each pose, `all_deltas_accounted`
asserts 180 deltas, the bbox sits in each pose record and is byte-compared, and the md table is
generated from the same deltas, so every moved bone is listed. The Done is covered (see issue 6 for
a strengthened form).

## Issues

### 1. (R11) Three numbers in the outputs are typed, not derived — all three happen to be correct

- `Research/BatmobileGrab/POSES.md:48` — "`Batmobile_V2_Tank_Strafe` is the actual strafe stance.
  Its root translates **4.89 m**". The literal is at `Tools/scripts/grab_poses.py:636` (and in the
  docstring at `:16`); it is never computed from the key frames.
- `Research/BatmobileGrab/POSES.md:39` — "not the **90°** strafe stance". Typed in the renderer.
- `POSES.json` `convention.bbox` — "linear-blend skinning of all **201,338** LOD0 points"
  (`grab_poses.py:552`), a typed count that duplicates `BONES.json` `lods[0].points`.

Verified: the strafe chassis track moves 0 → −4.889105 m in `Batmobile_V2_Tank_Strafe` (82 frames);
the strafe wheel yaw is 89.952–90.004°; `BONES.json` `lods[0].points` is 201,338. So the values are
right, but by R11 they should be read from the data (the strafe track, `summary.strafe`, and
`BONES.json` respectively).

### 2. (R4/R5) The `_Game` / non-`_Game` role is a name-based guess stated as fact

`MODLOG.md:8124`–`8127`: "The `_Game` pair is the gameplay transition … The non-`_Game` pair is
recorded as the cinematic variant". Nothing in `ANIMATIONS.md`, `ANIMATIONS.json`, the key file or
the card says what the `_Game` suffix means; the only support is the suffix itself, and the check
`canonical_is_game_variant` (`grab_poses.py:515`) is `CANON_OPEN.endswith("_Game")` — it verifies the
name, not the behaviour, so it can never fail. `grab_poses.py:14`–`16` and `:428` repeat the claim.

Measured counterpoint: both pairs close to the same pursuit pose (the non-`_Game` open start and
close end are also 3.495 × 2.342 × 7.026, chassis 0.022, turret 1.315), so loop closure does **not**
distinguish them; their battle endpoints differ materially — chassis y 0.226 vs −0.028 m, turret y
2.198 vs 1.947 m, bbox 4.487 × 3.088 × 7.382 vs 4.691 × 2.865 × 7.443 m. Which one the game plays is
UNKNOWN from the files. Both are recorded, so nothing is lost; the wording and the check name should
say "the `_Game` variant was chosen as canonical; which suffix the gameplay transition uses is
UNKNOWN".

### 3. (R5 label) "All 13 aero-fin bones" is 12 flap bones (8 of them pistons) plus the jet fin

`POSES.md:59`. The 13 rows in `summary.fins` are `Batmobile_Rig_Aero_Flap_*` (12, including
`..._Piston_Top`/`..._Piston_Btm`) and `Batmobile_Rig_Jet_Fins` (1) — flap mechanism bones, not 13
fins. The measurement is right (max 0.000° vs the chassis, so the spread does not deploy them); the
noun overstates what was counted.

### 4. (R14, minor) "the four transformation-sequence endpoints" is eight endpoint records

`MODLOG.md:8121`. `POSES.json` `variants` has 8 rows: 4 sequences × 2 endpoints (open_start,
open_end, close_start, close_end). Wording only.

### 5. (scope note) Three other `transformation`-tagged clips of the same anim set are not reported

`ANIMATIONS.json` tags 7 clips of `Playable_Batmobile_SF`/`Batmobile_V2_Pose_States` as
`transformation`: the 4 Spread clips the doc covers, plus `Batmobile_V2_Bat_Tracker` (37 frames) and
`Batmobile_V2_Cannon_Reload_Left/Right` (15). The card's `Do` says "for the first and last frame of
each transformation sequence"; the doc reports the four Spread endpoints. The `Done` only asks for the
two poses, so this is a scope gap rather than a Done failure — the two other clips are mechanism
clips, not pose transitions, and their motion is already measured in T-12.

### 6. (check strength, minor) "every moved bone listed" is only implied

`all_deltas_accounted` is `len(deltas) == len(bones)`; it does not check that the moved subset (180)
matches `summary.bones_world_moved`, nor that the md table has one row per delta. The md is generated
from the same list and byte-compared, so the property holds today; asserting the moved count and the
row count would make the Done clause explicit.

### 7. (R14, minor) The done section gives no verbatim check output

`MODLOG.md:8137` records the command `python Tools/scripts/grab_poses.py --check` and says it
re-derives both files, but the section pastes no output, unlike other cards' done entries. R14 asks
for command output; adding the 9-line PASS block would close it.

### Read positively (not issues)

- The bbox is the skinned mesh, not a box around bone pivots, and the pursuit box reproduces
  `Working/TrueScale/stations.json` `body_bbox` to 0.3–1.4 mm on x/z; the lower bottom (0.020 vs
  0.091 m) is the tyre geometry — verified independently: the lowest bind-pose vertices (±0.002 m)
  are bound 1.0 to `Wheel_Rear_Left_Vis`/`Wheel_Rear_Right_Vis`. `MODLOG.md:8139`'s "tyre contact"
  claim holds.
- `--check` re-derives and compares both files byte for byte; the input hashes (BONES, key file,
  LOD0 mesh) are stored, and the mesh hash is re-verified in `build_doc()`.
- Missing animation channels fall back to the bind local, and the world chain uses the PSK
  left-handed convention already validated by G1-11.

## Spot-checks

| # | value in `POSES.md` | where verified |
|---|---|---|
| 1 | turret raise **+0.633 m**, 0.683 m relative to chassis (line 25) | `POSES.json` `poses.pursuit/battle` `Turret_Top.position_m`: 1.314716 → 1.947437 = +0.632721 m; +0.050 chassis drop = 0.682789 (matches `summary.turret`) |
| 2 | bbox **3.495 × 2.341 × 7.026 → 4.691 × 2.865 × 7.443 m** (lines 18–19) | `POSES.json` bbox min/max: (2.331 − −2.360)=4.691, (2.687 − −0.178)=2.865, (3.961 − −3.482)=7.443; deltas 1.196/0.524/0.418 match `summary.bbox_delta_m` |
| 3 | strafe "root translates **4.89 m**"; wheel yaw 90.0° (lines 48–57) | raw key file `Playable_Batmobile_SF__Batmobile_V2_Pose_States.json`, `Batmobile_V2_Tank_Strafe` chassis position (0.008333, −0.0, −0.050068) → (0.008333, −4.889105, −0.050315) = 4.8891 m; `summary.strafe` yaw 89.952–90.004° |
| 4 | "180/180 bones move, 64 articulate"; "all 201,338 LOD0 points" | `POSES.json`: 180 pose bones each, 180 deltas, `moved` 180, `articulated` 64; `BONES.json` `lods[0].points` = 201338 |
| 5 | loop "0.054 cm / 0.026°" (line 74) | `POSES.json` `loop`: 0.05389 cm / 0.026226°, 0.054236 cm / 0.024405° |
| 6 | "All 13 aero-fin bones … max 0.000°" (line 59) | `summary.fins` has 13 rows, all 0.0 — but the set is 12 `Aero_Flap*` bones (8 pistons) + `Jet_Fins` (issue 3) |

## Limits of this review

Read-only; no card file, script, research file or game file was changed. I rebuilt the poses through
`grab_poses.build_doc()` for the variant comparison and inspected the raw key-frame channels for the
strafe translation; I did not re-derive all 180 world transforms from scratch, so the pose chain rests
on G1-11's validated convention as the card says.
