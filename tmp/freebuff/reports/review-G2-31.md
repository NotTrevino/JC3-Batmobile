# Review · G2-31 · Water behaviour

Reviewer: independent (did not write the card). Date: 2026-10-28.
Scope read: `GRAB_BACKLOG.md` §0.5 (R1-R14), the G2-31 card, the G2-31 row in §12
(line 1314), `MODLOG.md` §G2-31 done, `Research/JC3Grab/WATER.md` (288 lines),
`Research/JC3Grab/WATER.json`, `Tools/scripts/jc3water.py`, `Research/JC3Grab/README.md`
(§663, §945), `tmp/freebuff/probe_g2_31.py`.
Nothing was edited outside this report; no game launched, no archive or shared module
touched, nothing committed.

## VERDICT: **minor issues**

The card is substantively sound: the Out files exist, `--check` passes, the doc is
generated (never hand-edited) and its numbers reproduce from the raw entity decodes,
the card's Done criterion is answered for sinks/floats and answered as a *documented
absence* (`UNKNOWN`) for "drives underwater" - which is what R4 requires when the data
has no member. Three problems are wording/labelling rather than data: one sentence
calls 198 **module instances** "198 entities" (197 entities), one calls the three water
modules the carriers of "every water member" when §9 itself lists three more module
types carrying water-named members, and the summary overstates the float route by
requiring a `BoatBuoyancy` block that §5/§10 show is not needed merely to float.
None of them changes a value or a verdict; all are generated from
`Tools/scripts/jc3water.py:to_md`, so a `--write` after the prose fix would settle them.

## Check output (verbatim)

Command: `python Tools/scripts/jc3water.py --check`

```
PASS: 232 entities, sink 189 / floating 8 / boat 35, donor will_sink 1 buoyancy 2 drag 100 (1 hull element), 35 boats base_buoyancy 0.1..1.45, 21 fleet-wide water/engine rows in one shared VehicleCommon, build water modules identical to the donor: True, 38 member paths scan as water-related
```

Exit status 0. This matches the string in `MODLOG.md` (§G2-31 "Done check, verbatim")
word for word, including the line wrapping of the source.

`--check` does more than print that line: `jc3water.py:cmd_check` (lines 716-748)
rebuilds the whole dataset, runs `invariants()` (lines 652-699) **and** re-generates
the Markdown, comparing it byte-for-byte against `WATER.md` and the JSON against `d`.
So every number in the doc is covered, not just the ones the PASS string names.

## Card conformance

| item | result |
|---|---|
| Out path `Research/JC3Grab/WATER.md` | exists, 288 lines |
| extra Out files named in §12 (`WATER.json`, `jc3water.py`) | both exist (40 859 B / 37 575 B) |
| README registration | `### Water behaviour (WATER.md, G2-31)` at line 663, `Files` row at 945 |
| §12 row | `\| G2-31 \| done \| …` at line 1314 |
| MODLOG done section + revert recipe | present, revert names the script, both data files, the README section/row, §12 and the log truncation point |
| In-scope roster (donor, armoured transport, tanks, `v1717` duck, engine-kill/drown member) | all present: §4 roster covers all three donor builds, both transport builds, `v0201`/`v0202`/`v0603`, `v0200` APC, `v1717` duck, `v1200`/`v1401`/`v1500`/`v1717` boats, `v4500`, `v2603`; the engine-kill side is §7 |
| Done criterion | met for "sinks and stalls" (members+values, §1/§2/§7) and "floats" (§1/§2/§5/§6); "drives underwater" has **no member**, and the doc proves the absence (§9 + the `invariants()` guard that fails the check if any `drown`/`submerg`/`underwater` path appears) then records `UNKNOWN`. Read literally the card wanted values for that third row; the data cannot supply any, and inventing one would break R4. Acceptable - but the §12 "done" claim rests on an absence, and a reader comparing Done to the doc line by line should know that. |

## Issues

1. **"`Buoyancy` on 198 entities" is 198 module instances, not 198 entities.**
   `Research/JC3Grab/WATER.md:18`: "`Buoyancy` on 198 entities, `WaterInteraction` on
   233 module instances, `BoatBuoyancy` on 35 boats." Verified counts (via
   `jc3water.load()`, i.e. the same decodes the script reads):
   entities carrying `Buoyancy` = **197** (189 sinkers + 8 floaters), module instances =
   **198** - the extra is the cargo plane's tank copy the doc itself describes two lines
   later. Cause: `Tools/scripts/jc3water.py:476-478` prints
   `d['members']['Buoyancy']['buoyancy']['n']` (a row count = instances) with the word
   "entities", while the sibling clause correctly says "module instances". `--check`
   cannot catch it because it compares regenerated text against regenerated text; the
   number is script-derived (R11 is not broken) - the noun is wrong. Same paragraph,
   so the fix is a one-word change plus a `--write`.

2. **"Three module types carry every water member in the fleet" is contradicted by §9.**
   `WATER.md:18` and §2's heading, versus `WATER.md:254-262`, which lists water-named
   members in **six** module types: `WaterInteraction` 17, `BoatBuoyancy` 9,
   `HelicopterModel` 5, `VehicleCommon` 5, `Buoyancy` 3, `Fins` 1. §11 repeats the
   narrower reading as "module types with water members | 3" (generated from
   `len(MODULES)`). The three modules are the ones that carry the *buoyancy/drag*
   members; `VehicleCommon` carries the `*_water_entry_*` timers and
   `number_of_water_collision_sensors`, `Fins` carries `fins[].effective_in_water`, and
   `HelicopterModel` the `dive_*` flight terms. As written, §2 undercuts the doc's own
   scan and hands a reader a wrong count of "water modules" if they quote §2.

3. **The summary overstates what the float route needs.**
   `WATER.md:3`: "the float route would need `will_sink` 0 plus a `BoatBuoyancy` block
   that the donor does not have." But §5 and §10 show the opposite for floating itself:
   the eight floaters (`v0200` APC, `v2603`, `v4500`) float with `will_sink` 0 and the
   *ordinary car* `Buoyancy` module, no boat block - and 147 sinking entities carry the
   same `buoyancy` 2 they do. §10's table says it correctly ("only by `will_sink` 0, and
   for a boat-like ride a `BoatBuoyancy` block"), so the intro and §10 disagree about
   whether the block is a precondition for floating. The `MODLOG.md` resume repeats the
   intro version. Minor, but it is the sentence a plan would be written from.

4. **§9's table sums to 40 while the headline says 38 distinct paths.**
   `WATER.md:254` says "38 distinct member paths"; the table at 256-262 has
   17 + 9 + 5 + 5 + 3 + 1 = **40**. Both are right: `buoyancy_modules` and
   `buoyancy_modules[].position[]` live in both `Buoyancy` and `BoatBuoyancy`, so the
   distinct union is 38 (verified from `WATER.json['scan']`: 38 keys with `n > 0`,
   40 module-path pairs, duplicates exactly those two). The table has no note saying
   the column counts *module-path pairs*, so a reader adding the column gets a number
   that contradicts the sentence above it.

5. **R5/R4: the class-to-block mapping in §7 is name-based, and `_s` is read as seconds
   while `_ms` is declared `UNKNOWN`.**
   `WATER.md:239`: "the engine shut-down delay is 30 s for cars and 5 s for every other
   class", and §7's table labels each row "values (all entities) ... x232". All 232
   entities share one `vehicle_common.vmodc` that ships **all five** class blocks
   (`car_common` 30, `boat`/`helicopter`/`motorbike`/`plane` 5) on every vehicle, so
   which block a given vehicle's engine actually reads is not in the data - it is
   inferred from the block names. The doc applies exactly the right scepticism to the
   `_ms` unit ("10/20 ms is too short to be a drown timer, so the name is the only
   evidence") but not to the block-name mapping or to the `_s` suffix, which it states
   as fact. The §12 row inherits "30 (car) / 5 (others), 0 overrides". A one-clause
   hedge ("the block a class reads is by name, not observed") would bring §7 up to the
   standard §7 itself sets for `_ms`.

Not an issue, checked and clean: the claim that `will_sink` - not the hull mesh - is the
switch is supported by the 10 mesh-less sinkers (all `will_sink` 1, all in the sink
group, `WATER.json['no_hull']`); the "identical to the donor (1e-6)" claim is backed by
`WATER.json['build_check']` with both value pairs and `identical: true`; the "604 inner
files" and "734 rows"/"10 rows" figures come from `WATER.json['build']`, not by hand;
the 21 shared-constant rows are exactly the 21 rows listed in §7; and units, float
rounding and native behaviour are all declared `UNKNOWN` rather than filled in.

## Spot-checks (value, where verified)

| doc value | where verified |
|---|---|
| `WATER.md:3` / §3: sink **189**, floating **8**, boat **35** (232 total) | `jc3water.load()` + `group()` recount = 189/8/35; also `WATER.json['census']['groups']` and independently `tmp/freebuff/probe_g2_31.py` output: `"cache_groups": {"boat": 35, "floating": 8, "sink": 189}` (re-run by the reviewer, decoded straight from the archives) |
| `WATER.md:18` `Buoyancy` … 198 (labelled entities) | counted: entities with a `Buoyancy` module = 197, instances = 198 (the extra is `v4603_plane_urga_cargotransport_military_cargo_tank.ee`, listed as a duplicate in `WATER.json['duplicates']`) |
| §2 `buoyancy` "0 .. 2 (4 distinct)" on 198 modules | raw counter over the cache: `{2: 150, 0: 7, 0.25: 23, 1.5: 17, None: 35}` -> min 0, max 2, 4 distinct; the `None` 35 are the boats |
| §3 "both groups carry the same `pressure_drag` 5000 / 20000, `angular_drag_*` 0.05, `depth_full_drag` 0.1, `reference_drag_speed_ms` 20" | per-group counters: sink `{5000: 189}`, floating `{5000: 8}`, `angular_drag_pitch` `{0.05: 189}` / `{0.05: 8}`, `depth_full_drag` 0.1 on all 189 + 8, ref speed 20 on all 189; only the boats diffuse (`{5000: 14, 3000: 15, 2000: 3, 100: 3}`) |
| §7 constants `10 / 20 / 20 / 50` ms and `30 / 5 / 5 / 5 / 5` s, each x232 | `WATER.json['constants']['rows']` (all `{'10': 232}` … `{'30': 232}`); re-derived independently by `probe_g2_31.py`: `car_common.engine_shut_down_delay_s 30.0`, `vehicle_damage.fatal_water_entry_ms 20.0`, `min_water_entry_ms 10.0`, and one `vehicle_common_files` entry |
| §4/§5 roster: `v0201`/`v0202` tanks `buoyancy` 0, `v0603` 2; APC `will_sink` 0 `buoyancy` 2; duck `base_buoyancy` 1.45 with 9 pontoons; boats `base_buoyancy` 1 (24), 1.45 (9), 0.1 (2) | cache counters: `buoyancy` 0 = exactly the six `v0201`/`v0202` entities (+ the cargo plane); pontoon counts per boat 6..9 with `v1500` jetski = 6, `v1200` = 9; `base_buoyancy` distribution `{1: 24, 1.45: 9, 0.1: 2}`. Probe on the raw archives: APC `will_sink 0, buoyancy 2.0`; duck `will_sink 0, base_buoyancy 1.4500000476837158, pontoon_modules 9` |
| §8 build: 604 inner files, `WaterInteraction` 734 rows, `Buoyancy` 10 rows, `will_sink` 1, `buoyancy` 2, `drag` 100, 1 hull part `sportsmuscle_body` | `WATER.json['build']['container_files'] = 604`, `build.modules.{…}.rows = 734 / 10`, `build_check.identical = true`; donor `part_elements[0].from_part.string = "sportsmuscle_body"` from the cache; probe: `donor will_sink 1, drag 100.0, radius 0.55, hull_parts 1, from_part sportsmuscle_body` |
| §9 "38 distinct member paths" | `WATER.json['scan']`: 38 keys with `n > 0`; grouped 17/9/5/5/3/1 (40 pairs) with duplicates `buoyancy_modules`, `buoyancy_modules[].position[]` |

No game was launched, no save/profile or `D:\Games` path was opened, no archive or
shared module was modified, and nothing was committed.
