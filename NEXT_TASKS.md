# NEXT_TASKS — 32 tasks no queued brief covers (menu for hand-written briefs)

**How to use this file.** Take the first task whose dependencies are done, write a brief from its four lines
(`tmp/freebuff/queue/92NN-<slug>.txt`), add `BRIEF: hand-written <date>` and the `DONE:` path, start one lane.
Two minutes per brief.

**What this file is not.** It is not a template and must not be pasted wholesale. Freebuff's policy (and
`SKILL.md:51–74`) allows **one hand-written brief per task, written for that task**, and forbids templated or looped
briefs. Two tasks here may look alike; their briefs must still say different things about different files.

Coverage: all 53 files in `tmp/freebuff/queue/` were read (the 91xx RC5 chain, 7981–7987, 8600/8606/8607/8608, 8906,
7940/7942/7943). None of the tasks below has a queued brief. Card ids are the ones in `Working/Roadmap/*.md`.

---

## Stage 0 — record hygiene first (a wrong record makes every later brief build the wrong thing)

**1. `NEW-WPN-46` — resolve the B-24 / B-25 / B-15 numbering collision**
Task: one table that says which document owns which id, and fix the references that point at the wrong one.
Inputs: `Research/specs/B-24.md`, `Research/specs/B-25.md`, `GRAB_BACKLOG.md` §8 and §12,
`tmp/freebuff/reports/review-build-wave.md` §3, `Working/Roadmap/weapons.md` lines 96–99 and 182.
Done-check: `grep -rn "B-24\|B-25\|B-15" tmp/freebuff/queue/` returns only unambiguous uses, and the table is in the
report.

**2. `NEW-AUD-26` — STATUS/ledger audio hygiene**
Task: reconcile the three audio claims that disagree (`0x6BB2C66E` UNKNOWN vs resolved; media-0 rows; winch `out` vs
`blocked`).
Inputs: `STATUS.md`, `Research/BatmobileGrab/AUDIO_BANKS2.md`, `Research/BatmobileGrab/AUDIO_FEATURES.md`,
`Working/Roadmap/sound.md` line 74.
Done-check: every disagreement listed with both sides and the file that settles it; `status_audit.py --check` stays
current.

**3. `NEW-APP-4` — reconcile `STAGES.md` ("0 rows out") with T-21's 88 drop classes**
Task: give each dropped appearance class a row or a card id, so "out" is not silently equal to "not built".
Inputs: `STAGES.md`, `Working/Appearance/`, `Tools/scripts/appearance_plan.py`, `Working/Roadmap/appearance.md` §65.
Done-check: the D1/D6/D7/D9…D14 classes each map to an id; the count printed matches the plan's 88.

**4. `NEW-ARM-03` — settle the health-scale ruling (36,000 vs 1,200) in writing**
Task: decide which ships, show the arithmetic both ways, and state the consequence for hits-to-kill.
Inputs: `T-DM1` row, `tmp/freebuff/reports/health-to-explosion-no-crash-damage-plan.md`,
`Tools/scripts/bm_health.py`, `Research/BatmobileGrab/DAMAGE_RULES.md`.
Done-check: one decision paragraph plus the per-weapon hits table; no round number without its inputs.

## Stage 1 — decodes that gate the RC5 builds

**5. `NEW-WLD-01` — decode the `.btc` goal member in `car_drive_to_point.btc`**
Task: find the goal/target member in the behaviour-tree body, or prove it absent.
Inputs: `Research/JC3Grab/INDEX.jsonl`, the `ai/bts/*.btc` entries it lists, `Tools/scripts/` readers that already
walk `.btc`, `tmp/freebuff/reports/water-flip-damage-remote-plans-v2.md` (U13).
Done-check: the member offset and type, or UNKNOWN with the byte ranges tried.

**6. `NEW-WLD-03` — can a dropzone `.gsc/.gdc` run at all (desk evidence)**
Task: decide from archives and shipped examples whether a mod-authored graph can execute, because water teleport,
flip thrusters and homing all depend on it.
Inputs: `INDEX.jsonl` (`scripts/` families), `Research/JC3Grab/` script notes, the RC4 receipt's drop list.
Done-check: a yes/no with the loader rule cited, or UNKNOWN with the file that would settle it — never a build on a
guess.

**7. `NEW-WPN-26` — settle the AutoAim angle unit (0.15 = turns or radians)**
Task: decide from the fleet whether `0.15` is 54° or 8.6°, so BmAK's 40° cone can be written.
Inputs: the AutoAim tunes the weapon plans name, `Research/JC3Grab/` weapon notes,
`Working/Roadmap/weapons.md` line 97.
Done-check: the unit proven by at least three fleet instances plus one doc quote, or UNKNOWN.

**8. `NEW-WPN-27` — fix L-1: the missile tune sits on a bullet weapon component**
Task: re-plan the two clone that puts the missile tune on a `CMissileWeaponBase`, not the APC bullet weapon.
Inputs: `Builds/bm-RC4` receipt conflicts, `T-WP4` row, `Working/Roadmap/weapons.md` line 96.
Done-check: the class mismatch reproduced from the bytes and the corrected clone named file by file.

**9. `NEW-WPN-8` — provenance of `MissileLockOnDuration` 2.0 s and `MaxTargets` 8**
Task: state where the two numbers were found and what they govern, given the operator's 1/4/7/10 by level.
Inputs: `Research/specs/B-24.md`, `Working/Roadmap/weapons.md` line 99, `ROADMAP.md` §7.
Done-check: each number traced to a package/export/offset or marked found-by-rebuild; the conflict with 10 recorded.

**10. `NEW-HDL-5` — ledger rows for handling facts that exist only in plans**
Task: add rows for the flip idle timer, 4WD, the 21.6 km/h spin gate and battle yaw-toward-aim — each with its
carrier and its UNKNOWNs.
Inputs: `Working/Translation/T_ROWS.jsonl` (244 rows), `Working/Roadmap/handling.md` line 88,
`tmp/freebuff/reports/air-control-and-ram-assist-plans-v2.md`.
Done-check: four new row ids, `t_rows.py check` green, no row left without a provenance class.

**11. `NEW-HDL-6` — the 4WD decision**
Task: name the closest JC3 composition (per-axle slip / driveline split) and its limits; JC3 has one driveline.
Inputs: `Working/Roadmap/handling.md` line 89, `T3_FLEET.md`, `Tools/scripts/t3_fleet.py`.
Done-check: a composition with member paths and a stated gap, not a refusal.

**12. `NEW-HDL-7` — re-derive T-E5 honestly**
Task: show the 267 km/h terminal from Cd 0.55 and what Cd 0.276 would need, then state what the label means.
Inputs: `T-E5` row, `T-E2` row, `Working/Roadmap/handling.md` line 90.
Done-check: the arithmetic reproduced by a script, the 336.4 label kept `assumed`.

**13. `NEW-HDL-8` — pursuit-vs-battle value-set table**
Task: one table of every per-mode member (stiffness 3000/750, damping 300/20, bias, speed cap, battle factors).
Inputs: `Working/Roadmap/handling.md` line 91, `T-MD5` row, `tmp/freebuff/reports/collision-impact-and-mode-switch-plans-v2.md`.
Done-check: every row has a value, a mode, and a source file; no cell says "same".

**14. `NEW-AUD-1` — extract/decode media for the 10 found banks**
Task: get the samples/events out of the ten banks that are on disk, so lock beeps, sonar, tracker and impacts stop
being ids only.
Inputs: `Research/BatmobileGrab/AUDIO_BANKS.md`, `AUDIO_BANKS2.md`, `Tools/scripts/` FMOD readers,
`Working/Roadmap/sound.md` line 39.
Done-check: per bank, the event list with sample counts; unreadable ones named.

**15. `NEW-AUD-2` — per-event JC3 binding for the 26 ids**
Task: for each BmAK id, the closest JC3 event plus the gap — an auditionable candidate, not a name.
Inputs: `T-AU3` row, `Working/Roadmap/sound.md` lines 25, 40.
Done-check: 26 rows with a JC3 event path + a gap sentence each; no "identical".

**16. `NEW-AUD-3` — locate the bank for `TransformationReverseDirection*`, `TaserSound`, `VehicleSound`**
Task: widen the scan past the four `Playable_Batmobile*` packages.
Inputs: `INDEX.jsonl`, `T-AU5` row, `Working/Roadmap/sound.md` line 41.
Done-check: bank + slot, or UNKNOWN with the packages scanned listed.

**17. `NEW-ARM-05` — suppress the visible damage stages (audit, not build)**
Task: list every JC3 member that can produce smoke, burn, part detach or a mesh swap on the car, and the value that
turns each off.
Inputs: `T-DM4`, `T-DM5`, `T-FX22`, `T-FX23` rows, `Working/Roadmap/damage_world.md` line 49,
`Research/BatmobileGrab/DAMAGE_RULES.md`.
Done-check: a table member → off-value → file; any member with no off-value gets a card.

**18. `NEW-ARM-06` — do falls, trains, water and script kills damage the car**
Task: map `vehicle_damage.*` and the kill paths so "crashes never damage" is not read as "nothing damages".
Inputs: `Working/Roadmap/damage_world.md` line 50, `Research/JC3Grab/DAMAGE_MECHANISMS.md`, `vehicle_common.vmodc` rows.
Done-check: each kill path classified as crash / water / script, with the member.

**19. `NEW-ARM-07` — define the "heavy weapon" attacker set**
Task: per-attacker hits-to-kill for rifles/MG/helicopter MG vs missiles/tank/RPG/mines, against the chosen health.
Inputs: `Working/Roadmap/damage_world.md` line 51, `Research/JC3Grab/DAMAGE_MECHANISMS.md`, `T-DM1`.
Done-check: the table, with each enemy weapon's JC3 damage cited.

**20. `NEW-ARM-12` — re-run `damage_audit.py` and the hits table on the RC5 merge**
Task: catch the T-DM7 / T10_DAMAGE / STATUS contradictions after the RC5 branches land.
Inputs: `Tools/scripts/damage_audit.py`, `Builds/bm-RC5` (when it exists), `Working/Translation/T10_DAMAGE.md`.
Done-check: the audit runs clean or every diff is listed with the file that owns it.

## Stage 2 — appearance desk work (these block the 9190 merge, not a build)

**21. `NEW-APP-7` — budget ledger across all RC5 branches**
Task: model 4,791.3 of 4,915 KB today plus booster mesh, tracker launcher, arch lamps and skin variants; name what
gets trimmed.
Inputs: `Tools/scripts/bm_budget.py`, `Builds/bm-RC4/receipt.json`, `Working/Roadmap/appearance.md` line 68.
Done-check: a per-branch KB table that sums, with the trim list.

**22. `NEW-APP-8` — reconcile the texture budget figures**
Task: explain `budget.json` 5,380.9 KB vs the allocator cap 4,648 KB and the build-d04 numbers.
Inputs: `Tools/scripts/bm_budget.py`, `Working/Appearance/budget.json`, `Working/Roadmap/appearance.md` line 69.
Done-check: one number with its denominator, and the contradicting files corrected or named.

**23. `NEW-APP-5` — palette write plan (10 tints, gloss 0.6)**
Task: plan the private palette `.vmodc` write and the `CCar.palette` hash check, so 9143 does not improvise it.
Inputs: `T-MA7` row, `tmp/freebuff/reports/paint-plans-v2.md`, `Working/Appearance/` palette notes.
Done-check: every one of the 10 tints has a slot and a source; the hash path is stated.

**24. `NEW-APP-10` — the four D9 chapter masks: pick one static state**
Task: decide which chapter state BmAK shows by default and route it through `SupportDmgBlend` + `m_Damage`.
Inputs: `Research/BatmobileGrab/COLOUR_PARAMS.md`, `tmp/freebuff/reports/paint-plans-v2.md`, `Working/Roadmap/appearance.md` line 91.
Done-check: one state chosen with evidence, the other three named as a documented limit, not an omission.

**25. `NEW-APP-11` — colour ramps and the Leather ramp bake route**
Task: the ramps' pixels exist but the sampler is absent in all 961 shader headers — bake or card it.
Inputs: `Working/Appearance/PIXEL_LOCATE.md`, `Research/BatmobileGrab/` ramp notes, `Working/Roadmap/appearance.md` line 92.
Done-check: a bake route with the texture format, or a card naming the missing sampler.

**26. `NEW-APP-13` — per-pixel reflectivity for brake disc, cockpit, missile, Nimbus**
Task: settle the packing ("R channel dead") so the channels can be written.
Inputs: `Research/BatmobileGrab/COLOUR_PARAMS.md`, `Working/Roadmap/appearance.md` line 94.
Done-check: the packing proven on one asset, then applied to the other three or named UNKNOWN.

**27. `NEW-APP-17` — residual Serpente geometry audit**
Task: confirm no donor panel (bumper/fender/hood/window) is still on the car.
Inputs: `Builds/bm-RC4` parts, `Working/Translation/T8_PARTS.md`, `Working/Roadmap/appearance.md` line 98.
Done-check: a list of every donor-named part and its BmAK counterpart or its absence.

**28. `NEW-APP-29` — silhouette margin budget for the RC5 adds**
Task: RC4 passes the 99.9 % gate by 0.0004 pp; model the new geometry before it is built.
Inputs: `Tools/scripts/v02a_*` / the silhouette census, `Builds/bm-RC4/receipt.json`, `Working/Roadmap/appearance.md` line 110.
Done-check: a predicted margin per add, and the rollback point named.

**29. `NEW-APP-30` — LOD behaviour and the resident-texture limit**
Task: 5 LOD distances, shadow LOD, and the vehicle-vanish mode seen in MODLOG §76.
Inputs: `MODLOG.md` §76, the `.lod` files the appearance tree ships, `Working/Roadmap/appearance.md` line 111.
Done-check: the distance table and the resident limit with a number.

**30. `NEW-APP-31` — hole/seam repair**
Task: BUD-1 gross holes 0.309 % / 0.2968 % at part seams plus 31 three-bone-tie faces.
Inputs: the BUD-1 outputs, `Tools/scripts/appearance_bake.py`, `Working/Roadmap/appearance.md` line 112.
Done-check: holes re-measured after the repair, with the face count.

## Stage 3 — parts and controls

**31. `NEW-MOD-13` — controls are not in the ledger at all**
Task: add one row per button (18 in the plan) with its closest JC3 action and its gap; `T-ROWS` has no `T-IN*` rows.
Inputs: `tmp/freebuff/reports/controls-entry-exit-eject-plans-v2.md`, `Working/Q/PILOT/CONTROLS.md`, `T_ROWS.jsonl`.
Done-check: 18 rows, `t_rows.py check` green, each with a carrier or a card.

**32. `NEW-MOD-19` — the keymap writer**
Task: serialise the 12-byte binding record plus 18 B of `stringZ` property records into the 7,207 B patch keymap and
re-parse to 145 bindings.
Inputs: `T-CT1` row, `Research/JC3Grab/INPUT.md`, the patch gamepad keymap entry in `INDEX.jsonl`, `Tools/scripts/`.
Done-check: the written file re-parses to 145/104 with the same tail-0 tiling (C9).

---

## The batch after these (no entry written yet — queue only when the 32 above are placed)

`NEW-MOD-15` (fan/yoke reconcile), `NEW-WLD-07` (real icon), `NEW-WLD-08` (HUD name / radar icon strings),
`NEW-WLD-20` (`install_v3` into the RC generators), `NEW-MOD-23` (second Rebel Drop leaf), `NEW-WPN-15`/`16` (winch
plan, then build), `NEW-APP-40` (pipeline rebuildable from the user's own files), `NEW-WPN-24` (D-3 record
reconciliation).

## Tasks that are not on this menu on purpose

Q-1…Q-4 takes, 9x9x verify briefs and every pilot card: queued or gated on `tmp/freebuff/APPROVED_Q.txt`. Nothing
here asks for a game launch, an install into a real game folder or an attach to a process.
