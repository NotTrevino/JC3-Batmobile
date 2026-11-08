# Independent review — G2-18 · Interaction points and stunt areas

Reviewer: independent read-only pass (did not write the card). Date 2026-10-28.
Card: `GRAB_BACKLOG.md:670` (`G2-18 · Interaction points and stunt areas`, M, deps P0-1,
serves WLD-3/4, MOD-3/4, ANI-9). Tracker row: `GRAB_BACKLOG.md:1301`
(`G2-18 | done | Research/JC3Grab/INTERACTION.md (jc3interact.py --check green)`).
Journal: `MODLOG.md:10971` (intended change), `MODLOG.md:11015` (done).
Outputs reviewed: `Research/JC3Grab/INTERACTION.md` (312 lines), `Research/JC3Grab/INTERACTION.json`
(66,257 B), `Tools/scripts/jc3interact.py` (41,389 B), README registration `README.md:719`.

## VERDICT: minor issues

The card is substantially done: both Out paths exist, the check re-derives and byte-compares both
artefacts, the stunt module is decoded with counts I could reproduce exactly, the 85-object census
matches the XML and the JSON, and the doc is unusually honest about what it does not know (the
bbox-normalisation is *not* the R2 transform; the `.asb` state machine is not decoded). Three things
deserve correction before the next card leans on it: one row of the card's Done ("every interaction
object … with a Batmobile-surface verdict") is not met for 32 of the 85 objects, the "0 on-surface"
headline rests on an unjustified 0.03 m threshold, and §4 asserts animation wiring stays valid while
§5 says the state machine is undecoded.

## Check output (verbatim)

Command: `python Tools/scripts/jc3interact.py --check`

```
PASS: 85 objects (entry 29, exit 26, interaction 3, point 8, transition 12, trigger 7), transforms own 15 / inherited 70 / none 0, verdicts {'floating': 23, 'inside': 30, 'n/a (container origin)': 32}, stunt 3/32 active (64 welds), mesh 28940v/20000t, json match True
```

Exit code 0. `cmd_check` (`jc3interact.py:782-801`) rebuilds `build()`, compares
`INTERACTION.json` for equality and `render_md()` against the file byte-for-byte; writes happen only
in `--write` (lines 772/776), and no archive, `INDEX.jsonl` or `D:/Games` path is touched.

Done-criterion match: the card asks for (1) every interaction object with transform and state,
(2) the stunt module decoded, (3) each point expressed relative to the Serpente bbox/wheel stations
and a Batmobile-surface verdict. The check asserts (1) and (2) fully and the verdict census for (3)
— but see issue 1 for the 32 objects.

## Issues

1. **32 of 85 objects get no surface verdict, while the card's Done asks for one for every object.**
   `INTERACTION.md:30-124` (the object table, rows marked `n/a (container origin)`) and
   `INTERACTION.md:125` (the verdict rule); `INTERACTION.json` `points[]`: 32 entries carry
   `"verdict": "n/a (container origin)"` because their nearest transform is the identity
   `graph`/`context` container. They are listed with a position (0,0,0) and a `world_from`, which is
   defensible — inventing a verdict at the origin would be worse — but the row is not literally met,
   and the validation table's `objects with a position | 85 | 85` (`INTERACTION.md:300`) counts a
   container origin as a position. Recommend marking the row `done (32 n/a by construction)` in
   `GRAB_BACKLOG.md` §12, or listing which 32 and why in one line of the doc.

2. **The "0 on-surface" headline depends on an unstated constant.** `INTERACTION.md:125` defines
   on-surface as "nearest Batmobile triangle ≤ **0.03 m**"; the number is repeated in
   `INTERACTION.json` `mesh.on_surface_threshold_m = 0.03`. Nothing on disk justifies 0.03 m — not
   the mesh resolution, not a hull tolerance. It matters: `main_area`'s `center_local` is
   **0.0197 m** (inside the band, and the doc does call that single point on-surface), so a 0.05 m
   band would move several area centres from "floating" to "on-surface". Class: **assumed**. Fix:
   state the rule as a chosen tolerance and report the counts at two or three thresholds.

3. **§4 claims the animation wiring stays valid; §5 says the consumer was not decoded.**
   `INTERACTION.md:249-250`: "a rebuilt graph keeps the vanilla state names and the animation wiring
   stays valid"; `INTERACTION.md:281` (§5): "the `.asb` state machine that consumes them was not
   decoded here, so 'which animation plays' stays UNKNOWN". R5: the presence of a `state` string is
   a name, not a behaviour — nothing read here shows the state machine accepts the same names in a
   new graph. Fix: "the state names are portable and unchanged; that the machine still resolves them
   is untested (UNKNOWN)".

4. **Minor: two different Batmobile bboxes are in play without a note.** The mapping uses
   `stations.json` `body_bbox` = [-1.747, 0.091, -3.42] … [1.748, 2.362, 3.605]
   (`INTERACTION.json` `frames.batmobile_body`), while the measured mesh AABB is
   [-1.7531, 0.0783, -3.4218] … [1.7508, 2.3667, 3.6093] (`mesh.bbox`). The doc's frame table gives
   only the first. That is correct for the mapping (it is the build's own box) but a reader comparing
   the two surfaces will find a ~6 mm x / 13 mm y difference with no explanation.

5. **Provenance of `number_of_triangles` (R4, mild).** The doc reports "4 / 4 / 8 triangles"
   (`INTERACTION.md:213-224`, the `points | triangles` columns; `MODLOG.md:11051`) — those are the
   module's **declared**
   `number_of_triangles`, and the script slices `triangle_indices[:3 * number_of_triangles]` with
   them (`jc3interact.py:397`). The declaration checks out where I tested it (area 0: 12 indices,
   all < 6 points, covering all six), but the doc should say "declared" rather than implying the
   array length was measured — the slot array is a fixed 42 entries for all 32 slots, active or not.

## Spot-checks

| value in the doc | where verified |
|---|---|
| 85 objects / entry 29, exit 26, interaction 3, point 8, transition 12, trigger 7 (`INTERACTION.md:30`, validation table) | `INTERACTION.json` `points` length 85 and `counts.by_prefix` identical; class census `CInteractionGraphEntry` 29, `CInteractionGraphExit` 26, `CInteractionGraphTransition` 12, `CInteractionGraphPointNode` 8, `CInteractionTrigger` 7, `CInteraction` 3 |
| 32 stunt slots, 3 active (6 / 6 / 10 deform points, 4 / 4 / 8 triangles), **64 weld rows**, **8 real welds (0↔1 ×6, 0↔2 ×1, 1↔2 ×1)** (`INTERACTION.md:204-224`, `MODLOG.md:11051`) | re-counted independently from `E:/Modding/_JC3grab/entities/v0300_…_civilian_01.ee.json` `StuntAreas` rows: `stunt_areas[0..31]`, `number_of_deform_points` 6/6/10 then 0×29, `number_of_triangles` 4/4/8 then 0, `name` front_area / front_signature_area / main_area / NoName, `welding_info[0..63]` = 64 entries, pairs `{0-1: 6, 0-2: 1, 1-2: 1}` = 8 — **exact match**, including the pair breakdown |
| mesh 28,940 verts / 20,000 triangles, and the bbox / transform chain (`INTERACTION.md:8-29`, `MODLOG.md` check line) | decoded `Working/TrueScale/body_lod1.rbm` with the project's own reader (`rbm_geom.decode` + `collect_mesh`): **28,940 / 20,000**, AABB [-1.7531, 0.0783, -3.4218] … [1.7508, 2.3667, 3.6093], i.e. the json's `mesh` block exactly; the bbox mapping re-computed for `point.driver` (Serpente -0.440/0.340/0.200 → Batmobile -0.578/0.598/0.392) reproduces the doc's row from `frames` alone |
| 135 deform points, envelope x ±1.33, y 0…1.524, z −2.560…2.527 | `DeformPoints` module: 135 `points[i]`, `start_transform[12..14]` ranges -1.33000004…1.33000004 / 0…1.52420545 / -2.5601728…2.526968 |
| 36 distinct states, 15 own / 70 inherited, verdicts 23/30/32 | `INTERACTION.json` `counts.states` (36 keys), `verdicts` (23 + 30 + 32 = 85), and 15 + 70 = 85 |

## Rules

R4: the two derived steps (bbox mapping, trigger scale as half-extent) are declared as mapping and
UNKNOWN respectively — good. The 0.03 m tolerance (issue 2) and the "declared" triangle counts
(issue 5) are the gaps. R5: the animation-wiring sentence (issue 3) is the one place a name stands in
for a behaviour. R11: every number in the doc is printed by `render_md` from `build()`, and the
validation table's "expected" column is a constant list compared against the measured value inside
`invariants()` — so a change in the data fails the check rather than silently updating the table.

## Limits of this review

Read-only: I ran `--check`, `t2_lg2`-style independent reads of the entity cache and the RBM, and
static reading of the script; I did not edit `GRAB_BACKLOG.md`, `MODLOG.md`, `Research/` or `Tools/`,
did not re-run the tamper tests recorded at `MODLOG.md:11023-11030`, and did not re-derive the
point-triangle distances (I verified the transform chain that feeds them, not the ray-parity
verdicts). No archive was opened, no game launched, nothing committed.
