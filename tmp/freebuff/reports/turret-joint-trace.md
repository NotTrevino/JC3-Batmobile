# DONE — turret/cannon joint trace (task: `Builds/bm-RC2/verify/joint_trace.md`)

STATUS: done — the joints die at the **manifest**, and the generator hardcodes `-1`; no later step
removes them.

## Answer in one paragraph

T8's rows carry the joint (`Working/Translation/T8_PARTS.md` P-01 and P-04 each have a `shipped
hinge` bullet naming `hkpLimitedHingeConstraintData`, axis and limits). The B-04 manifest
(`Working/Parts/bm_vehicle_parts.json`) has **no joint member at all** — its 26 part-record keys
are `behaviour, behaviour_hash, behaviour_source, channel, collision_source, damage_type,
damage_type_source, has_lights, has_world_collision_shape, is_deformable, lod_files, model, name,
parent, parent_frame_origin_m, parent_index, parent_space_offset, part_index, pivot_m, provenance,
raycast_body_id, raycast_instance_id, source_dir, t12_row, world_collision_body_id,
world_collision_instance_id` — so the hinge data has nowhere to live. `Tools/scripts/bm_parts.py`
then writes `constraint_index = -1` for **every** new part inside an unconditional flag tuple
(L645) and never opens the `.physicsc` (`physicsc` appears 0 times in 1,412 lines). `bm_rc2.py`
step 3 (L232) only copies B-10's pinned `.physicsc` over the tree's; both files carry the same 11
donor constraints (9 limited hinges + 2 ragdolls, widest span 90.0°), so nothing was deleted later
— nothing was ever added.

## The chain

| # | step | carries the joint? |
|---|---|---|
| 1 | rows (T-12) | yes for P-01 / P-04; P-02 is an `internal row (no joint)` |
| 2 | manifest (B-04) | **no** — 26 keys, 0 joint-ish |
| 3 | generator `bm_parts.py` | **no** — writes `-1`, never opens the physics module |
| 4 | later steps `bm_rc2.py` | **no** — swaps in B-10's `.physicsc` (same 11 donor constraints) |
| 5 | build | **no** — parts 50/51/53 read `-1`; the 9 hinges are donor panels |

## The manifest entries (quoted)

```json
{"name": "batmobile_turret", "part_index": 50, "parent": "sportsmuscle_body", "parent_index": 0, "behaviour": "Turret", "t12_row": "P-01", "channel": "none", "damage_type": "Land_Generic"}
{"name": "batmobile_cannon", "part_index": 51, "parent": "batmobile_turret", "parent_index": 50, "behaviour": "Cannon", "t12_row": "P-02", "channel": "none", "damage_type": "Land_Generic"}
```

Both exist, both carry the behaviour, neither carries a joint. `channel` is `none` on both, so
neither reaches a behaviour array either. The manifest's `behaviour` block holds exactly four
arrays — `hinged_parts` `[56,57,58,59]`, `rotating_parts` `[52]`, `door_parts` `[25]`,
`aim_part_constraints` `[]` (empty because TURRET.md's 85 aim rows are all suspension, 0 on the
six turreted vehicles). None of them is a constraint table.

## The generator lines that handle joints

```python
# bm_parts.py L645 — inside the per-part flag loop, unconditional for all 19 new parts
                            ("constraint_index", -1)):
```

Docstring step list (no physics step exists):

```
  1. export `Builds/bm-001/aaf/.../sportsmuscle_vehicle_parts.vmodc` (the identity build) to XML;
  2. remove the two door parts, their `door_parts` entries, their entries in the body's
  3. append one `Part` record per new part (B-02 geometry + B-03 lamp parts);
  4. append the `hinged_parts` / `rotating_parts` rows T-12 justifies;
  5. import the XML, and re-read the result with `jc3adf` before it is allowed into a build.
```

The array writers it *does* have: `hinged_parts` (L674), `rotating_parts` (L690) and
`aim_part_constraints` (L501, empty by TURRET.md). `bm_parts.py` is the only script under
`Tools/scripts/` that assigns `constraint_index` — every other mention is
`p.get("constraint_index")`.

## Did any other part with a row lose its joint?

**Yes: P-04.** `batmobile_riot_suppressor` is a `Cannon` whose row animates -89.999…-0.000° about
[-0.000, -0.000, -1.000] with the same mediumtank shipped hinge, and it ships `constraint_index =
-1` like the turret. It was outside the 7261 brief because that check compared spans only.

| id | part | row asks for | fleet (`ci>=0`) | built | verdict |
|---|---|---|---|---|---|
| P-01 | `batmobile_turret` | hinge | Turret 7/7 | -1 | **LOST** |
| P-04 | `batmobile_riot_suppressor` | hinge | Cannon 17/17 | -1 | **LOST** |
| P-02 | `batmobile_cannon` | no hinge (internal row) | Cannon 17/17 | -1 | row declined one, its verify line needs it |
| P-09…P-12 | `batmobile_aero_flap_*` | no hinge | AirBrake 1/1 | -1 | row declined one; B4-03: 148/148 fleet `hinged_parts` rows sit on a part with `ci>=0` |
| P-03 | `batmobile_machine_gun` | no hinge | GatlingGun 0/6 | -1 | correct (rotation via `rotating_parts[0]`, part 52) |
| P-05 | `batmobile_jet` | no hinge | EngineRotatingPart 0/1 | -1 | correct |
| P-06, P-07, P-08, P-13 | — | — | Hood 27/27, MissileHatch 16/16 | no part | rows with no cut part; the donor hood keeps ci 8 |
| P-14, P-15 | missile pods | moves with P-07/P-08 | — | -1 | no joint asked for |

Fleet numbers are my own census of 78 shipped `*parts*.vmodc` under `JC3_RAW/tmp`, not the
232-entity census.

## Files written

* `Tools/scripts/v_joint_trace.py` — new, `--write` / `--check`; `--check` re-derives every row
  verdict, the manifest key list, the generator line numbers, the physics censuses, the fleet
  ratios and the build's `-1`s, then byte-compares the page (21 oracles).
* `Builds/bm-RC2/verify/joint_trace.md` — the generated trace (19,737 B). Only file written inside
  the build tree; the manifests and build are read-only here.
* `MODLOG.md` — one appended section (intended change, why this file, revert path).
* this report.

No manifest or build file was modified; nothing was built, installed, launched or attached to.

## Commands run (verbatim output)

```
$ python Tools/scripts/v_joint_trace.py --write
wrote Builds/bm-RC2/verify/joint_trace.md (19737 bytes)
WRITE=0

$ python Tools/scripts/v_joint_trace.py --check
PASS T8 still has P-01 with a shipped hinge
PASS T8 still has P-02 static and jointless
PASS T8 still has P-04 as a Cannon with a shipped hinge
PASS the manifest has no joint member
PASS the manifest still has 19 new parts
PASS the manifest still lists P-01's part with channel none
PASS bm_parts.py writes constraint_index -1 once
PASS bm_parts.py never names physicsc
PASS only bm_parts.py assigns constraint_index
PASS P-02 is an internal row, not a lost joint
PASS bm_rc2.py copies B-10's physicsc
PASS build and B-10 carry the same constraint count
PASS no limited hinge is wide enough to be the yaw joint
PASS the build still has 61 parts
PASS the turret unit still carries -1
PASS P-01 and P-04 are the lost joints
PASS fleet Turret parts all carry a hinge
PASS fleet Cannon parts all carry a hinge
PASS fleet GatlingGun parts carry none
PASS the donor hood keeps its hinge
PASS P-03 and P-05 are not loss rows
oracles: 21/21 pass
document identical: Builds/bm-RC2/verify/joint_trace.md
CHECK=0
```

Earlier runs caught three real defects in my own audit before the final one: a `pivot_m` key was
being mis-counted as a joint member, `p.get("constraint_index")` reads were being mis-counted as
writers, and P-02 was being classified as a lost joint against T8's own `internal rows` line. All
three are fixed in the script, which is why the `--check` above is the final state.

## UNKNOWNs

* **whether JC3 creates a joint for a `Turret`/`Cannon` with `constraint_index = -1`.** No decoded
  file says so and no fleet turret ships it; a test would answer it and the test ban stands.
* **whether appending hinges to B-10's `.physicsc` keeps `constraint_index` order stable across the
  packfile.** No card has written a constraint yet; the index→object-order convention is only
  observed on shipped files.
* **the fleet census is 78 `tmp/*parts*.vmodc` modules**, not the 232-entity walk; the per-behaviour
  ratios are stated against those 78.

## COMPROMISES

None. This task only read files and wrote one verify page plus this report.
