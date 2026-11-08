# Review · G2-33 · Light system consolidated

Reviewer: independent (did not write the card). Date: 2026-10-28.
Read: `GRAB_BACKLOG.md` §0.5 (R1-R14), the G2-33 card (line 807), the G2-33 row in §12
(line 1316), `MODLOG.md` "G2-33 · … — done" (line 10717), `Research/JC3Grab/LIGHT_SYSTEM.md`
(332 lines) + `LIGHT_SYSTEM.json`, `Tools/scripts/jc3lights.py`, `Research/JC3Grab/README.md`
(lines 582, 937), `tmp/freebuff/probe_g2_33.py`, and for re-derivation the decoded caches
(`_JC3grab/entities`, `_JC3grab/detail`), `PARTS_TABLE.jsonl`, `GEOMETRY.jsonl`.
Nothing outside this report was edited; no game launched, no archive or game file opened,
nothing committed.

## VERDICT: **minor issues**

The card's core is sound and its central counts reproduce from the raw decodes: 3,217
light entries over 223 vehicles, 25 members, 9 behaviours, 3,972 `.epe` objects, 11,643
parts / 2,073 lit, 11,367 `CarLight` blocks, and the 25-member wheel-arch recipe with a
real source per value (the three recipe hashes recomputed independently; the donor
`lights[2]` template and part 26 verified field by field). `--check` is green, the doc is
generated and compared byte-for-byte, and the UNKNOWNs (renderer list, preset semantics,
`CarLight` parameter bytes, units) are declared rather than guessed.

What keeps it from "sound" is a pattern of **silent truncation and provenance slips in the
prose**: the "value census" prints 8 of the 15 `range` values, so the printed census sums
to 3,170 while the same document asserts 3,217; the `preset_id = 0` table shows 12 of the
17 rows it announces; the "exceptions" list shows 3 of 27 mismatches and 3 of 6 unlit
entries (with one line printed twice word-for-word). Added to that, the MODLOG's done
section carries a typed behaviour count (1,156) that contradicts the doc and the data
(1,177), and §7b classes a chosen `parent` as "decoded". No number is fabricated and the
card's Done criterion (a recipe with every member value sourced) is genuinely met, but
three lists are presented as complete when they are samples.

## Check output (verbatim)

Command: `python Tools/scripts/jc3lights.py --check`

```
PASS: 3,217 light entries / 223 vehicles, 25 members, 9 behaviours, 393 presets (17 use 0, 34 inconsistent), hashes 3217/3217/3217 recomputed; binding 2,073 lit parts, 27 name misses, 6 on unlit parts; CarLight 11,367 blocks stride ['12'] slots ['6']; recipe 25 members
```

Exit status 0. This matches the block in `MODLOG.md` (G2-33 done, "Done check") word for
word, and the `G2X.md` row's summary string.

`--check` is substantive: `cmd_check` (jc3lights.py:832-851) rebuilds the dataset, runs
`invariants()`, compares `LIGHT_SYSTEM.json` to the rebuild and regenerates the Markdown
and diffs it byte-for-byte, then prints the PASS. So every printed number is script-derived
(R11 holds for the doc), including the ones this review finds incomplete - the truncation is
in the renderer, not in the data.

## Card conformance

| item | result |
|---|---|
| Out path `Research/JC3Grab/LIGHT_SYSTEM.md` | exists, 332 lines, 21,500 B |
| `LIGHT_SYSTEM.json`, `jc3lights.py` (named in §12) | both exist (79,742 B / 46,559 B) |
| README registration | `### The light system (LIGHT_SYSTEM.md, G2-33)` line 582, Files row line 937 |
| §12 row | `\| G2-33 \| done \| …` line 1316 |
| MODLOG done + revert recipe | present; revert names script, both data files, probe, README section/row, §12 and the log truncation point |
| card In: `Working/Lights/LGT1_FINDINGS.md`, MODLOG §112-§113, `ENTITIES.md`, `GEOMETRY.md`, donor lights module | all four evidence streams used (§1 module, §2 `.epe`, §4 `has_lights`, §5 `CarLight`, §7 donor + BmAK); `probe_g2_33.py` exists as the independent re-derivation the log claims |
| Done: "a recipe for one custom light (wheel-arch light) with every member value sourced" | met: §7a has 25 rows, each with value + source + class (18 decoded, 1 decoded/mapped, 3 derived, 3 derived/verified by hash). Verified samples below; the only member whose *shape* is a judgement is `preset_id` 0, and that is argued from the 17 shipped zero-preset entries rather than left bare |

## Issues

1. **The `range` value census is silently cut to 8 of 15 values, so it does not add up to
   the entry count.**   `LIGHT_SYSTEM.md:75` prints `10` x1667, `2` x669, `30` x351,
   `1` x332, `50` x66, `3` x39, `0.5` x34, `2.5` x12 = **3,170**, against the 3,217
   entries the same table asserts at `:51` and the doc states at `:24` and `:310`. The JSON holds all 15 values (sum 3,217): the missing
   ones are `0.1` x4, `0.2` x11, `0.3` x6, `1.5` x6, `15` x2, `20` x12, `40` x6.
   Cause: `Tools/scripts/jc3lights.py:567` renders `list(v.items())[:8]`. The heading
   "Value census of the numeric members (value -> entries)" claims completeness, and no
   `… top 8 of 15` marker is printed, so a reader concludes a car lamp can only have 8
   ranges and would miss the 0.1-0.3 m and 15/20/40 m values entirely. This is the one
   defect here that can produce a wrong build number.

2. **The `preset_id = 0` table is a 12-row sample of 17, under a heading that says it is
   the list.** `LIGHT_SYSTEM.md:134` "The `preset_id = 0` rows:" followed by 12 rows
   (`:136-147`), while `:131` and the table above it say 17. `jc3lights.py:609` slices
   `[:12]`. Omitted: `v1401_boat_mugello_racingboat_signature_preorder` (None),
   `v2602_helicopter_urga_lightassault_{debug,military_01,rebel_01}` (HeadLight on
   `lightassault_body`), `v9999_car_mugello_dlctestcar_debug` (TailLight). Nothing is
   wrong with the 12 shown - they are exactly the first 12 records - but the count on the
   page cannot be reconciled with the list, which is the sort of contradiction R11 exists
   to prevent in a generated doc.

3. **The §4 "exceptions" list is 3-per-category and contains a duplicated line.**
   `LIGHT_SYSTEM.md:164` "The exceptions, so nobody re-derives them:" lists 9 bullets for
   categories measured at 3 / 27 / 6 (`:160-162`), i.e. 3 of 27 name mismatches and 3 of
   6 unlit entries. `jc3lights.py:224-244` appends only while `len(examples[…]) < 3`, and
   the unlit bullets are per *entry*, not per part, so the same Bavarium-turret line
   prints twice (`v0202_car_capstone_bavariumtank_debug` part 24). The result reads like a
   rendering bug and cannot identify the other 24 mismatched entries or the third unlit
   part. Either mark the lists "first 3 of N" or dedupe by (entity, part) and print all of
   the small categories (6 and 3 are tiny; 27 is one helicopter family repeated per build).

4. **MODLOG's done section states a behaviour census that contradicts its own total.**
   `MODLOG.md` G2-33 done, "Result" paragraph: "`None` 1,156". The doc (`:61`), the JSON
   (`module.behaviors`) and a raw recount of the entity decodes all give **1,177**, and the
   MODLOG's own list (1,156 + 1,027 + 301 + 253 + 253 + 191 + 9 + 3 + 3) sums to **3,196**,
   not the 3,217 the same paragraph states. This is a typed number in prose, i.e. exactly
   the failure mode the generated doc avoids; the doc is right and the log is wrong, but
   the log is what a later session reads first.

5. **§7b classes a chosen `parent` as "decoded" and does not note the consequence.**
   `LIGHT_SYSTEM.md:266`: `parent` = `26`, class **decoded**, source "PARTS_TABLE.jsonl
   donor: the wheel part". Verified in `PARTS_TABLE.jsonl`: part 26 is
   `sportsmuscle_wheel_f_l` (`Land_Wheel`, `parent` 3, `lights` 0, `deform` 0) - so 26 is
   the wheel's *index*, and no `parent` field anywhere holds 26 (the donor's lit parts sit
   under `parent` 0). Making the arch a child of the wheel is a design decision (it decides
   whether the arch follows the wheel's spin - the wheel parts are the ones the `wheels`
   array spins), not a decoded value, and the doc discusses neither the alternative
   (`parent` 0, like every donor light part) nor the spin consequence. Also worth stating
   in §7c: the donor wheel record has `deform` 0 as well as `lights` 0.

6. **§5's layout provenance says "blocks" where the cited source counts RBMs, and the
   numbers are hardcoded.**   `LIGHT_SYSTEM.md:195` quotes "round-trip 190/193 blocks
   byte-identical" as from MODLOG §17, but `MODLOG.md:925` says "Donor round-trip:
   **100/193 -> 166/193 -> 190/193** byte-identical, 0 mismatched" - that is 190 of the
   donor's 193 RBMs, not 193 `CarLight` blocks. The 1085 B / 16 B / `[12, 24, 2]` layout
   values are typed constants in `carlight()` (jc3lights.py:283-287) with a source string,
   so `--check` re-derives the stride/slot counts but not the layout. Minor, but a reader
   quoting §5 inherits the wrong noun.

7. **§9's "recipe values that are UNKNOWN | 0" overstates what the recipe leaves open.**`LIGHT_SYSTEM.md:332` sits next to §7b's `anchor node in the rig` row,
   which is classed **UNKNOWN (Q-1 probe)** (`:272`). The assertion counts only the 25 light-member rows, so
   the number is true of that table, but "recipe values … 0" next to a recipe field marked
   UNKNOWN invites the reading that nothing in §7 is unresolved.

8. **R5 nit: "point lamp" is a name-based reading presented as fact.** §7a's source text
   for all 15 shape members calls the donor's `lights[2]` "the shipped steady `HeadLight`
   **point** lamp" (`:243-261`). The donor entry has `light_type` 0 (verified), but no file
   labels 0 = point; the doc elsewhere applies exactly the right scepticism to units
   ("no file states the unit"). Same paragraph also says `has_lights` is "not a gate the
   loader enforces" (§4, `:178`) - a loader-behaviour claim inferred from 6 counter-
   examples. Both are probably right; neither is labelled a reading. Related observation,
   not a defect: the template is a `light_type` 0 lamp with `angle` 10, whereas the BmAK
   wheel component was a `SpotLightComponent` (cone 0, unusable). The doc never says why a
   non-spot lamp (723 entries ship `light_type` 1) is the right shape for an arch, so T-18's
   arch rows inherit "no cone" without that decision being recorded.

Checked and clean: the "223 vehicles / one vehicle carries two modules / both number from
`lights[0]`" statement is exact (the only two-module entity is
`v4603_plane_urga_cargotransport_military_cargo_tank.ee`); "every one of the 11,367 blocks
has stride 12 and 6 material slots" matches `GEOMETRY.jsonl`; the donor summary "42 parts,
12 with `has_lights = 1`, 10 `Land_Light`, rest `Land_Body` x1 / `Land_Generic` x1" matches
`PARTS_TABLE.jsonl`; "one part hosts several lamps - the donor's left tail-light part
carries TailLight + LeftSignal + Reverse" is true (`sportsmuscle_taillight_r_l`, indices
0/1/15); the `.epe`/module split is stated as a disagreement rather than papered over; and
`preset_id` 0 is explicitly "what 17 shipped lights carry", not a claim about what 0 means.

## Spot-checks (value, where verified)

| doc value | where verified |
|---|---|
| 3,217 entries over 223 vehicles, 1…45 per vehicle, 25 members | raw scan of all 232 `_JC3grab/entities/*.ee.json`: 224 `VehicleDynamicLights` modules on 223 entities, 3,217 `lights[i]` entries, 25 distinct member paths, per-entity 1..45 (`LIGHT_SYSTEM.json: module.per_entity` min/max); the 2-module vehicle is the cargo-tank plane |
| `None` 1,177 / 9 behaviours | raw behaviour counter over the same decodes: `None` 1,177, HeadLight 1,027, TailLight 301, LeftSignal 253, RightSignal 253, Reverse 191, SirenLightOn 9, SirenLightOnOffFast 3, SirenLightOffOnFast 3 (sum 3,217) - the doc is right, `MODLOG.md`'s 1,156 is the outlier |
| `range` "value census" of 8 values | raw counter: **15** distinct values summing 3,217; the doc's 8 sum to 3,170 (issue 1) |
| parts 11,643 / lit 2,073 / `Land_Light` 1,323; donor 42 parts / 12 lit / 10 `Land_Light` | recounted from `PARTS_TABLE.jsonl` (233 rows): 11,643, 2,073, 1,323; donor row 42 / 12 / 10 with `Land_Body` 1 + `Land_Generic` 1 |
| `CarLight` 11,367 blocks in 11,367 meshes / 220 vehicles, stride 12, 6 slots | recounted from `GEOMETRY.jsonl` (56,136 rows): 11,367 rows with a `CarLight` block across 220 entities; stride/slots from the same JSON as the doc |
| `.epe`: 3,972 `SVehicleLight`, 233 `SVehicleLights`, 412 `SVehicleLightList`, 404 preset names (`Dash_Light` x221) | recounted from all 232 `_JC3grab/detail/*.ee.json`: 3,972 / 233 / 412 objects, 404 distinct `preset_id` strings, `Dash_Light` 221 |
| recipe hashes `3460580079` (behavior), `1432199802` (part), `3050336140` (anchor) | recomputed here with `rbmhdr.hash_jenkins` on `HeadLight`, `sportsmuscle_wheel_f_l`, `\|sportsmuscle_LOD1\|wheel_f_l\|Wheel_Frnt_Left_Disc\|Wheel_Frnt_Left_Disc_LIG` - all three match |
| recipe shape members (range 2, angle 10, near_cap 1, multiplier 1, light_type 0, `falloff_start` 0, `projected_texture_index` -1, `volumetric_mode` 0, `volume_intensity` 1, uvscale 1/1, `preset_id` donor) | donor `lights[2]` in the entity decode: behaviour `HeadLight`, part `sportsmuscle_body`, part_index 0, range 2, angle 10, near_cap 1, multiplier 1, light_type 0, falloff_start 0, projected_texture_index -1, volumetric_mode 0, volume_intensity 1, uvscale 1/1, anchor `\|sportsmuscle_LOD1\|body\|dashboard_LIG`, preset 2763198432 |
| part `sportsmuscle_wheel_f_l` = index 26, `Land_Wheel`, ships `has_lights = 0`; parent field is 3, `deform` 0 | `PARTS_TABLE.jsonl`, donor row part 26 (issue 5) |
| 17 zero-preset rows; 12 printed | `LIGHT_SYSTEM.json: module.zero_preset_rows` length 17, the doc prints entries 0-11 (issue 2) |

No game was launched, no archive or game install was modified, no save/profile or dropzone
was touched, and nothing was committed.
