# Review — G2-13 · Turret and cannon mechanics

Reviewer: independent (did not write the card). Read-only: no file under `GRAB_BACKLOG.md`,
`MODLOG.md`, `Research/`, `Tools/` or the game data was modified; all experiments ran on copies in
`tmp/freebuff/g213/` (deleted afterwards) or in memory.

## VERDICT: minor issues

The card is substantially sound: every Out path exists, `--check` passes, the Done criterion is met
and generated, the turret/cannon numbers I re-derived from `TURRET.json` all match the doc, and the
doc distinguishes behaviour from member name better than most cards (it uses the negative proof that
`aim_part_constraints` holds no turret row rather than trusting the array's name). What keeps it off
"sound" is one R11 violation (the headline table in §1 is typed text, not data-derived) and three
sentences that state interpretations as facts — one of which contradicts the doc's own Limits
section.

## Check output (verbatim)

Command:

```
cd /e/Modding/JC3-Batmobile && python Tools/scripts/jc3turret.py --check
```

Output:

```
PASS: 8 samples, 92 points on 52 weapons, 85 aim-constraint rows, 3 mediumtank constraints
```

Exit status: `0`.

Tamper re-run (on a copy, `os.path.join` redirected for `TURRET.json`/`TURRET.md` only):

| tamper | result |
|---|---|
| clean copy of the two files | `PASS: 8 samples, 92 points on 52 weapons, 85 aim-constraint rows, 3 mediumtank constraints`, rc 0 |
| `TURRET.json` mediumtank turret `max_deg` 179 → 90 | `FAIL: json section changed: samples`, rc 1 |
| `TURRET.md` with one extra trailing line | `FAIL: ... md differs: @@ -384,3 +384 @@ ...`, rc 1 |

The MODLOG claim ("setting the turret's `max_deg` to 90 in the json made `--check` exit 1 with
`json section changed: samples`") reproduces exactly.

## Out paths and Done criterion

| item | status |
|---|---|
| `Research/JC3Grab/TURRET.md` (the card's Out) | exists, 384 lines, 29 769 B |
| `Research/JC3Grab/TURRET.json` (named in the §12 row) | exists, 113 822 B |
| `Tools/scripts/jc3turret.py` (named in the §12 row) | exists, 35 439 B, `--write` / `--check` / `dump samples\|census\|tune` |
| README registration | `Research/JC3Grab/README.md:38` (command), `:346` (section), `:928` (Files row) |
| §12 row | `GRAB_BACKLOG.md:1296`, `G2-13 \| done` + evidence |

Done criterion in the card: *"the medium tank's turret+cannon chain is fully described with numbers;
same for one wheeled vehicle (APC or armoured jeep)"*. It is met: §1 gives the medium tank chain
(parts, indices, constraints, pivots, axes, limits, fire point, weapon binding), §2 adds the APC and
the armoured jeep with the same fields, plus the technical, small tank, Bavarium tank, Serpente
(`sportsmuscle`) and buggy. `--check` verifies it indirectly but adequately: all eight samples are
rebuilt from source and the md/json are compared, so a missing or changed turret row fails; the
medium tank's three limits are additionally asserted by name.

## Issues

1. **R11 — the §1 headline table is typed, not derived.** `Research/JC3Grab/TURRET.md:7-16` (the
   yaw/pitch/hatch row of indices, pivots, axes, limits and "42 parts, 3 constraints") and its
   paragraph at `:18` are string literals in `Tools/scripts/jc3turret.py:427-438`; nothing in
   `render_md` interpolates `d["samples"]` there. Proven: I doctored the built data in memory
   (`mediumtank_turret` index 26→99, pivot →9,9,9, `max_deg` 179→90) and re-rendered — only §2's
   row changed (`TURRET.md:33` became `| ... | 99 | ... | 9, 9, 9 | ... | -179 .. 90 |`); §1 kept
   `index 26`, `0, 2.2812, 1.1382`, `-179 .. 179`. The values are correct **today** (I checked all
   of §1 against the json, below), but the safety net is only indirect: if the game data changed,
   `--check` would fail on the json, and a following `--write` would regenerate the json and md and
   leave §1 stale while `--check` passes again. Same class of typed prose: "0.25 m" / "5.82 m" at
   `:18`, the rad→deg conversions and the "5..70 m / 6 / 16 deg" sentence at `:374`, and "not all
   233" at `:382` (233 = the row count of `PARTS_TABLE.jsonl`, verifiable but not interpolated).
   Everything else that carries counts is generated: §2 tables (from `constrained_parts`), §3
   (`pc`), §4 (`ac`), §5 tune tables (`d["autoaim"]`).

2. **Unsupported geometry claim, contradicting the doc's own Limits.** `TURRET.md:18`: "the pivots
   are printed as the packfile stores them: on this vehicle they land exactly where the art puts the
   ring and the trunnion." No code reads a mesh, and `TURRET.md:382` says the opposite: "The hinge
   transform's frame (body-A local vs vehicle space) is not proven". The data does offer a weaker,
   verifiable statement the doc could have made (`constrained_parts[].centroid`, e.g. the cannon's
   centroid `(0.0012, 2.5471, -2.2961)` against its pivot `(0, 2.5347, 0)`), but it is not made.

3. **Interpretation presented as fact: what `aim_part_constraints` does.** `TURRET.md:330` — "used
   by suspension and steering links". The proven half is the negative one (85 rows in 17 of 78
   modules, no `Turret`/`Cannon` row, 0 rows on all six turreted vehicles) and the behaviour census
   (source 13 `Spring` / 2 `Axle` / 70 `None`; target 34 `BrakeDrum` / 19 `Wheel` / 12 `BrakeDisc` /
   6 `BrakeCalipers` / 2 `Engine` / 12 `None`). "Suspension and steering" is read off part names
   (`atv_y_bar_*`, `atv_axle_arm_*`, brake drums) — the same name→behaviour step R5 warns about,
   applied in the opposite direction. It should read as an inference, or be left UNKNOWN, because
   no file decodes what the array is consumed by.

4. **Small count error in §5.** `TURRET.md:336`: "plus two unnamed values (a float 2 and an int 1)".
   `TURRET.json` → `samples[].aim_objects[0].unnamed` has **three** entries:
   `id:076F6110` = `"2"`, `id:3E5487F2` = `"1"`, `id:D04059E6` = `"970552602"`. The third is
   dropped without a note, and the "float"/"int" types are asserted from raw strings rather than
   shown.

5. **Control-loop claim beyond the data.** `TURRET.md:376`: "So no file holds an aim ray or a turret
   target. The aim system picks a point ... and the two hinges are driven to put the cannon on it."
   The first sentence is supported (no such object in the decoded entities); the second is engine
   behaviour that no decoded file shows — the same paragraph's Limits (`:382`) concede the turn rate
   is code-side UNKNOWN. Related, `:374` "`Stunting` is the in-vehicle set" is a namespace-name
   inference, and `:336` "`min_aim_distance` -1, so no minimum" reads a documented-by-value meaning
   from a property whose name is otherwise unrecovered.

None of these change a port decision: the parts, pivots, axes, limits and point properties a B-05
port must copy are all in the json and all correct.

## Spot-checks

| value in the doc | where verified | verdict |
|---|---|---|
| `TURRET.md:7-15` — medium tank: turret `mediumtank_turret` i26, parent 0, constraint 2, pivot `(0, 2.2812, 1.1382)`, axis +Y, −179..179; cannon `mediumtank_cannon` i38, parent 26, constraint 0, pivot `(0, 2.5347, 0)`, axis +X, −5..20; hatch i39, constraint 1, pivot `(-0.4848, 2.921, 1.4785)`, 0..130; "42 parts, 3 constraints, no ragdoll" | `TURRET.json` `samples[mediumtank]`: `parts` 42, 3 constraints, `constraint_classes` `{hkpLimitedHingeConstraintData: 3}`, `constrained_parts` rows exactly as quoted, `identity_offset` true on all three | match |
| `TURRET.md:295-298` — census "Across 41 armed entities, 92 fire points on 52 weapons"; yaw 13 `Cannon` / 44 `None` / 18 `Turret`; pitch 47 `Cannon`; 0 unresolved | `TURRET.json` `point_census`: `vehicles` 41, `points` 92, `weapons` 52, `yaw` {Cannon 13, None 44, Turret 18}, `pitch` {Cannon 47}, `unresolved` [], `bad_behaviour` [] | match |
| `TURRET.md:132` and §12 row — APC pitch `apc_weapon_mount_vertical` i44, constraint 14, pivot `(-0, 2.7313, 0.5942)`, −15..50; yaw `apc_turret_base` i30, constraint 15, `(-0.0037, 2.1367, 1.3048)`, ±179 | `TURRET.json` `samples[apc]` — identical; armoured jeep (−25..50 at `0.5099, 2.2898, -0.3751`) and technical (−10..45 at `0, 2.0498, 0.6697`) also match the §12 row | match |
| `TURRET.md:327-330` — "85 rows in 17 of 78 modules"; `hinged_parts` 28/78, `rotating_parts` 22/78; 0 rows on all eight samples | `TURRET.json` `aim_constraint_census`: `rows` 85, `with_constraints` 17, `modules` 78, `hinged_modules` 28, `rotating_modules` 22; `samples[].aim_rows`/`hinged_rows`/`rotating_rows` all 0 except the buggy's 12 aim rows. Behaviour counts sum to 85 per side | match |
| `TURRET.md:299` — "44 plain parts on aircraft pods" | independent re-derivation from `WEAPON_WIRING.jsonl` + `PARTS_TABLE.jsonl`: the 44 yaw parts with behaviour `None` sit on 11 `v2200`/`v2601`/`v2604` helicopter entities (4 each); the remaining plain yaw entry is the cross-entity one on `v4603_plane_..._cargo_tank` (the doc's 2 cross-entity entries) | match (helicopters = aircraft) |
| `TURRET.md:360-371` — autoaim: tanks' `w602`/`w603` and small tank's `w605` use `autoaim_vehicle_mgun`, the M2 `w206` on APC/armoured jeep/technical uses `autoaim_assault_rifle`; both 5..70 m, sticky 6/16 deg, `CanTargetVehicles` 0 | `TURRET.json`: `samples[].weapons[].autoaim` = `autoaim_vehicle_mgun.wtune` for mediumtank/Bavarium/smalltank, `autoaim_assault_rifle.wtune` for all three M2 mounts; both tunes decode `MinAimDistance` 5.0, `MaxAimDistance` 70.0, `StickyAimAngleNewTarget` 6.0, `StickyAimAngleCurrentTarget` 16.0, `StickyAimStrength` 0.4, `CanTargetVehicles` 0, `CanTargetCharacters` 1; thresholds 0.03/0.05 vs 0.04/0.06 rad | match |
| §12 row "8 entities / 106 constraints" | `TURRET.json` per-sample constraint counts 3+15+17+16+19+13+11+12 = 106, 8 samples | match |

## Notes / limits of this review

- I did not re-decode any `.physicsc` or `.vmodc` from `E:/Modding/_JC3grab`; the raw-data checks
  above re-read the card's own machine half (`TURRET.json`) and, for the point census, the upstream
  `WEAPON_WIRING.jsonl`/`PARTS_TABLE.jsonl` the script consumes. If `TURRET.json` itself were wrong
  relative to the packfiles, this review would not see it — but `--check` rebuilds that json from
  the packfiles on every run, so a wrong json cannot pass.
- No game was launched, nothing was committed, no secrets read.
- The R11 issue (#1) is the only one I would expect a fix to touch: generate §1 from the medium
  sample (it is already in `d["samples"]`) and assert its indices/pivots, then the typed values
  cannot drift.
