# Rework — T-12 · Moving-parts translation

**STATUS: DONE — 6/6 review issues CONFIRMED, 0 rejected, all fixed in the generator; `--check` PASS,
and the delivered JSON loads through `bat_assemble.load_part_spec` again.**

Review read: `tmp/freebuff/reports/review-T-12.md` (`needs rework (narrow)`, 6 issues + journal nits).
Every issue was re-verified against the key frames and the delivered JSON before any edit. All six
are confirmed; none rejected. The journal nits are confirmed too and corrected in the done entry
(`MODLOG.md` is append-only, so the old sentences are not rewritten).

Intended-change entry: `MODLOG.md` §"T-12 rework — intended change (2026-10-29)".
Done entry: `MODLOG.md` §"T-12 rework — done (2026-10-29)".

## Per-issue verdicts

### 1. The delivered JSON is no longer a `bat_assemble.py --parts` spec — **CONFIRMED**

Re-run of the review's compatibility check:

```
$ python -c "import sys; sys.path.insert(0,'Tools/scripts'); import bat_assemble; bat_assemble.load_part_spec('Working/Translation/T8_PARTS.json')"
part spec Working/Translation/T8_PARTS.json: schema 2, expected 1     (exit 1)
```

`T8_PARTS.json` had `schema: 2`; `load_part_spec()` accepts only 1. The doc's closing line and the
old done entry both claimed the file was still a valid spec.

**Fix:** the generator writes `schema: 1` (the `parts`/`left_in_body` arrays are byte-identical to the
B-02 cut) and versions the new content separately as `rows_schema: 2`. `cmd_write()` and
`cmd_check()` now call `bat_assemble.load_part_spec(SPEC)` on the delivered file and fail if it
refuses; an invariant also pins `schema == 1 and rows_schema == 2`. Verified:
`spec loads: True`, exit 0. `bat_assemble.py` itself was **not** edited (imported, not forked, R2).

### 2. P-02 and P-05 say no sequence moves their bones — **CONFIRMED**

Their rows have `joint: null` and a non-empty `translation`:

- P-02: `Barrrel_02` 53.376 cm, `Barrel_01` 36.129 cm in `Batmobile_V2_Cannon_Fire`
- P-05: `JetSMove` 40.163 cm in `Batmobile_V2_Bat_Tracker`

The renderer's no-joint branch printed "no sequence in the base package moves a bone of this part"
and the translation line was emitted only inside the joint branch.

**Fix:** every row now carries a derived `static_reason` (translation / no bone / variable-driven /
shell). P-02: *"no rotation is animated; the bones translate (`…Barrrel_02` 53.376 cm in
`Batmobile_V2_Cannon_Fire`) and a hinge cannot reproduce translation"*; P-05 adds that the spin is
`engine_rpm`-driven. The detail prints every translation line for static rows, and `--check` fails a
static row whose reason does not mention its translation (invariant added).

### 3. The Vulcan's limits are a wrap artifact — **CONFIRMED**

Recomputed from `Playable_Batmobile_SF__Batmobile_V2_Pose_States.json`
`Batmobile_V2_ChainGun_Spin`, bone `Batmobile_Rig_Weapons_Machine_Gun_02`, 119 frames, 3.900 s:

```
axis 0  min -179.493  max 177.861  span 357.354  travel 2160.0  turns 6.0  dur 3.9
```

So the row's "357.354°" is one ±180° wrap, and the real motion is six turns at 1229.51 °/s.

**Fix:** `euler_extents()` now also sums the short-way steps (`travel_deg`), records `turns`,
`monotonic` and `duration_s`; `collect()` keeps per-sequence spans and the longest single-sequence
travel. The joint gets `is_spin`, `per_sequence_spans`, `part_bone_extent`. A monotonic multi-turn
joint is rendered as **"6.00 turns / 2160.0° in 3.90 s"**, with the sampled extent explicitly labelled
"one ±180° wrap, not a limit"; the table's `BmAK motion` column prints the same. A spin invariant
fails if travel does not exceed one extent or the duration is missing.

### 4. The Done clause's axis and static-reason halves were not checked — **CONFIRMED**

`--check` only tested `span_deg > 0` / `max_rate_deg_s > 0`. **Fix:** invariants now require, for
every joint, `axis_index`, `axis_local`, `axis_jc3` and ordered min/max; for every static row a
non-empty `static_reason` that mentions any measured translation; for a spin, travel beyond one extent
and a clip duration. The reason is stored in the JSON, so it is checked rather than only printed.

### 5. "25 BmAK sequences" is 25 row-sequence pairs — **CONFIRMED**

Measured: 25 row-sequence pairs over **15 distinct clips** (`Batmobile_V2_Missles_Up` appears in
P-07, P-08, P-14, P-15). **Fix:** `summary.distinct_sequences` is derived and the summary, check
output and the doc say "25 BmAK row-sequence pairs (15 distinct clips)".

### 6. `axis` column is bone-local, the neighbouring limits column is JC3-space — **CONFIRMED**

**Fix:** the table has two columns, `axis (bone-local)` and `axis (JC3 space)` (the bone-local axis
through the bone's bind rotation), with a sentence saying what each is and that the JC3-space one is
what a hinge axis is compared with.

### 7. For six rows the headline joint is a child bone — **CONFIRMED**

P-03, P-04 and P-09…P-12 carry `is_pivot_bone: false` (barrel child / `Riot_Sup_Ammo` /
`Piston_Top`). P-09's part bone moves 20.010° at 37.20 °/s while the headline was the piston's
25.817° at 48.70 °/s. **Fix:** the table gained a `part bone (own span / rate)` column
("the joint bone" when they are the same, "part bone not animated" when it does not move), and each
detail adds a "part bone itself" line. The child-bone disclosure stays.

### 8. Journal nits (R14) — **CONFIRMED**

- old done entry: "262 lines" — `wc -l` was 268 before this pass, **295** now. Corrected in the new
  done entry (the old line is not rewritten).
- old done entry lists the yoke damage type as `Land_Selector`/`Land_Generic`; `grep -c
  Land_Selector Research/JC3Grab/PARTS_TABLE.jsonl` = **0**. The fleet values are
  `Boat_Steering_Wheel`, `Land_Generic`, `Land_Steering_Wheel`, as the doc prints. Corrected in the
  new entry.

### Note read positively (canopy statistics) — addressed

The 72.481 cm / 12.494° and the older "0.71 m / 11.2°" are the same five clips measured two ways.
§UNKNOWN 3 now derives both numbers from P-06's own row, names the sequence the max translation comes
from (`Cockpit_Close`), and lists the per-clip spans (12.49, 0.00, 12.45, 11.23, 11.23) so the
reader can reconcile them. The Q-1 verify cell keeps its pass criterion.

## Files changed

| file | change |
|---|---|
| `Tools/scripts/t12_parts.py` | `schema` 1 + `rows_schema` 2 and a `load_part_spec` check on the delivered file; travel/turns/monotonic/duration in `euler_extents`; per-sequence spans and longest-travel tracking in `collect`; joint `is_spin`/`per_sequence_spans`/`part_bone_extent`; derived `static_reason` per row; two-axis + part-bone table columns; spin wording; derived canopy/hatch numbers in §UNKNOWN; new axis/reason/spin invariants; `distinct_sequences` in the summary |
| `Working/Translation/T8_PARTS.md`, `T8_PARTS.json` | regenerated by `--write` only (295 lines; `schema` 1, `rows_schema` 2) |
| `GRAB_BACKLOG.md` | §12 T-12 line only |
| `MODLOG.md` | intended-change + done entries (append-only) |

No game file, `D:/Games`, shared game module, git or network was touched; no secret is involved.

## Check output (verbatim)

```
$ python Tools/scripts/t12_parts.py --check
PASS: 15 rows (11 cut parts, 12 with an animated joint, 4 with a shipped hinge, spins ['P-03']) | 25 BmAK row-sequence pairs (15 distinct clips) | fastest joint 1229.51 deg/s | pivots re-derived through bat_assemble (max delta 1.3918e-05 m) | damage types ['Boat_Generic', 'Land_Generic', 'Land_Hood', 'Plane_Control_Surface', 'Train_Generic'] | internal rows ['P-02', 'P-05', 'P-13'] | json match True, md match True
```

Exit status 0.

```
$ python Tools/scripts/t12_parts.py --write
T8_PARTS.md/json: 15 rows (11 parts), 12 joints, 4 shipped hinges, 25 sequences, fastest 1229.51 deg/s, pivot delta 1.3918e-05 m, 295 md lines

$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 40 keep 60 epe 26 re-read 0 blocked 13 out 36 superseded 7 | edits 35 over 16 rows
check ok

$ python Tools/scripts/status_audit.py --check
STATUS.md is current

$ python -c "import sys;sys.path.insert(0,'Tools/scripts');import bat_assemble;print(bool(bat_assemble.load_part_spec('Working/Translation/T8_PARTS.json')))"
True
```

Tamper test (then restored by `--write`, final `--check` exit 0):

```
# P-02 static_reason -> null in T8_PARTS.json
FAIL: T8_PARTS.json stale: rows                                   (exit 1)
# schema -> 2 in T8_PARTS.json
FAIL: T8_PARTS.json stale: schema; bat_assemble.load_part_spec refused ...: schema 2, expected 1   (exit 1)
# one digit in T8_PARTS.md (2160.0 -> 2161.0)
FAIL: md differs: @@ -47,3 +47,3 @@ ...                           (exit 1)
```

## Spot-checks of the corrected values

| value | where verified |
|---|---|
| Vulcan 2160.0° / 6.00 turns / 3.90 s / 1229.51 °/s | independent sum of short-way Euler steps over `Batmobile_V2_ChainGun_Spin` (119 frames) |
| P-02 translations 53.376 cm / 36.129 cm; P-05 40.163 cm | `T8_PARTS.json` `rows[*].translation`, re-read from the key frames by `t12_parts.build()` |
| 25 row-sequence pairs = 15 distinct clips | `sum(animation_sequence_count)` vs `len(set(animation_sequences))` over the 15 rows |
| part bone P-09 20.010° / 37.20 °/s vs piston 25.817° / 48.70 °/s | `T8_PARTS.json` P-09 `joint.part_bone_extent` and `joint.candidates` |
| JSON loads as a `--parts` spec | `bat_assemble.load_part_spec('Working/Translation/T8_PARTS.json')` returns parts (exit 0) |
| `Land_Selector` absent | `grep -c Land_Selector Research/JC3Grab/PARTS_TABLE.jsonl` = 0 |
