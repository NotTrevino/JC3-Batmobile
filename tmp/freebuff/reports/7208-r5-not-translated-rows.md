# R-5 / G3-11 part 1 - first 35 "NOT TRANSLATED" rows re-read in the build

STATUS: done. Of the first 35 rows that `Working/Translation/LEDGER_AUDIT.md` calls NOT TRANSLATED,
**20 are built and equal to the row, 5 are built with a different value, 6 are absent, 4 cannot be
read** by the decoders used. "NOT TRANSLATED" therefore does not mean "missing": 25 of the 35 are
in `Builds/bm-RC2`, 20 of them with exactly the value the row states.

## What was measured

- Selection: the first 35 NOT TRANSLATED rows **in ledger order**, reselected by calling
  `ledger_audit.build()` (the script that wrote the audit), not by copying ids. It re-derives
  106/198 NOT TRANSLATED and yields the ids below.
- Evidence: `Builds/bm-RC2`. ADF members via `jc3adf`, parts via `bm_parts.decode_parts`, paint
  blocks and texture lists via `rbm_geom`, the palette / deform / audio / lights modules via
  `jc3adf`, the fmod bank by size. One probe per row names a file and a member; no row was judged
  from its own prose.
- Match rule: a number matches when it rounds to the value the row prints (the row's own
  precision). Counts compare exactly.
- Read-only: ledger, audit and build opened for reading; only the page was written.

| class | rows | ids |
|---|---|---|
| built-and-equal | 20 | T-G3, T-M2, T-S2, T-S3, T-S4, T-S5, T-R2, T-R3, T-E1, T-E3, T-A1, T-K2, T-P1, T-MA1, T-MA2, T-MA4, T-MA6, T-PA6, T-PA7, T-AU2 |
| built-and-different | 5 | T-B4, T-P2, T-LG1, T-LG3, T-AU1 |
| absent | 6 | T-L4, T-L7, T-PA8, T-LG4, T-LG5, T-AU3 |
| cannot-read | 4 | T-L2, T-P3, T-MA3, T-MA5 |

## The five differences (all decoded, with the member)

| row | row states | built |
|---|---|---|
| T-B4 | arcade heat_boost extra 80 / grip 1.5 | `custom_land_global.vmodc` `arcade.heat_boost.extra_top_speed` = 100.92, `grip_multiplier` = 4.26 (blend 0 and torque 2 match) |
| T-P2 | 42 damage parts, 17 damage types | `sportsmuscle_vehicle_parts.vmodc`: 61 parts, 20 damage types |
| T-LG1 | 21 `VehicleDynamicLights.lights[]` entries | `..._lights.vmodc`: 18 entries |
| T-LG3 | 5 spot rows at `range` 30 | 5 spot entries (light_type 1), only 4 at range 30 (one is range 10) |
| T-AU1 | `LandAudio` `max_rpm` 10000 | `land_audio.vmodc`: `max_rpm` 4500 (`min_rpm` 1000 matches) |

These are the rows where the build's number is not the row's number; each is a candidate ledger
edit, not a missing file. T-B4's disagreement is with the *donor column* the row quotes, so it may
be the row's citation that is stale rather than the build.

## The four cannot-read rows (and why)

- **T-L2** - the 18 `lights[]` entries have no `radius` member (the largest is `range`) and
  `volumetric_mode` is 0 on all 18; the light presets live in `..._debug.epe`, an RTCP container
  (`jc3adf` rejects it: magic `0x43505452`).
- **T-P3** - `sportsmuscle.physicsc` (902,384 B) is RTCP, not ADF; no ADF member carries a
  collision-shape count and this script has no physicsc decoder.
- **T-MA3** - `rbm_geom` exposes CarPaintMM `static_params` as opaque bytes with no named colour
  member; the only 0.0567 float in `sportsmuscle_body_lod1.rbm` is at byte 553192 and is not a
  colour triple.
- **T-MA5** - the `Window` block is present (1 per LOD) but its opacity is baked into a texture
  plus a scalar; no named member to compare.

## The 20 equal rows are the important finding

The audit missed them because it matches member hints by content and the rows name members with an
ellipsis (`…wheels.width`) or state the value only in the `proposed` column. Examples with the
decoded member: `front_wheels.width` 0.73195 / `rear_wheels.width` 0.73165 (T-G3),
`unit_inertia` 4.0/2.6/1.2 (T-M2), `compression`/`relaxation` 3.0/5.0 (T-S2), `suspension.length`
0.70 (T-S3, a row marked `dispo=next` that **is** built), `frontal_area` 6.6347 (T-A1),
`min_time_to_block` 1/1 (T-K2), 17 paint blocks on body lod1 (T-MA1), `specular_gloss` 0.45 across
10 palette tints (T-MA4), `constraint_indices` 11 (T-PA6), `non_deformable_parts_indices` 20
(T-PA7), and the 210,781,376 B `vehicles.bank` (T-AU2).

## Files written

- `Tools/scripts/r5_part1.py` - `--write` / `--check`; the check re-runs `ledger_audit.build()` for
  the selection, re-reads every probe from `Builds/bm-RC2`, and rebuilds the page byte for byte.
- `Working/Translation/R5_PART1.md` - the class table with the built evidence per row.
- this report.

Nothing else was touched; both builds are read-only. Revert = delete the three files above.

## Commands and output (verbatim, final run)

```
$ PYTHONIOENCODING=utf-8 uv run python Tools/scripts/r5_part1.py --write; echo "WRITE_EXIT=$?"
wrote Working\Translation\R5_PART1.md
35 rows; built-and-equal 20, built-and-different 5, absent 6, cannot-read 4
WRITE_EXIT=0

$ PYTHONIOENCODING=utf-8 uv run python Tools/scripts/r5_part1.py --check; echo "CHECK_EXIT=$?"
PASS the audit's NOT TRANSLATED count re-derives (106)
PASS took 35 rows in ledger order
PASS every row has exactly one class
PASS no row was classified from its own text
PASS every row has a built-evidence string
PASS every built-and-equal row names a built file and its value
PASS T-MA4 palette gloss 0.45 x 10 tints re-derives
PASS T-PA7 non_deformable_parts_indices has 20 entries
PASS T-LG1 lights[] has 18 entries, not 21
PASS T-AU2 vehicles.bank is 210,781,376 B
PASS Working\Translation\R5_PART1.md re-derives byte for byte
PASS: R5 part 1 0 failure(s)
CHECK_EXIT=0
```

Two runs before this one failed their own assertions and were repaired, not skipped: the first
`--check` demanded a `=` in every built-and-equal evidence string (T-P1's name list has none - the
assertion now requires a built file path plus a number), and T-B4 was first probed in
`land_global.vmodc` where the `arcade.heat_boost` block does not live (it is in
`custom_land_global.vmodc`), which had wrongly classified it `absent`. Both fixes are in the script
and the run above is the repaired one. No build, game or install script was run.

## UNKNOWNs

1. **The four cannot-read rows** - the data is in RTCP containers (`.epe`, `.physicsc`) that
   `jc3adf` cannot open. Route: a physicsc/epe reader (the `bm_collision` packfile path is the
   nearest existing decoder) or the converter's XML export.
2. **Whether the 5 differences are ledger errors or build intent** - this page only reports that
   the values differ; which side should change is a translation decision, not a decode.
3. **Rows 36-106** - out of scope here (the brief says first 35). The same probe method applies.
4. **`Research/JC3Grab` fleet context for T-P2's 42/17** - the row quotes the donor's 42 parts; the
   build has 61 because parts were added (T-12/B-04). Whether the two numbers are meant to be the
   same quantity is UNKNOWN from the ledger alone.
