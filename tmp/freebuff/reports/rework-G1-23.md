# G1-23 rework — footage gap list

Date 2026-10-29. Input: `tmp/freebuff/reports/review-G1-23.md` (verdict `needs rework`, 9 issues).
Each issue was checked against the data and the generator first; commands and output are quoted.

## STATUS: **done — 9/9 issues CONFIRMED and fixed in the generator; 0 rejected**

`Tools/scripts/grab_footage_gaps.py` changed, `--write` regenerated `FOOTAGE.md` + `FOOTAGE.json`.
Those two were not hand-edited. The gate is green at **27/27** (was 23/23 with two tautologies), and
`--check` now byte-compares the note as well as the JSON.

**Process note, stated rather than hidden:** the script edits and the review's own demonstration were
run in the same pass, so the intended-change MODLOG entry was appended after the edits existed in the
working tree and before any regeneration, gate run or tamper test. The entry says so. No artifact was
written and no number recorded before it.

## State before the fix (verbatim)

```
$ python Tools/scripts/grab_footage_gaps.py --check
OK: 72 rows, 2 file-resolved, 1 measured (3 samples), reasons {'FILE-VALUE': 2, 'MEASURED': 1, 'NOT-IN-CLIP': 2, 'VALUE-NATIVE': 53, 'UNDOCUMENTED': 5, 'WRONG-SCOPE': 8, 'NATIVE': 1}; 23/23 checks
EXIT=0
```

Reproduction of the review's R11 demo (samples +0.6 s in memory, nothing written):

```
F-6 row: | F-6 | ... | **measured: 1.812 s mean** across three ramp jumps (1.251 / 1.183 / 1.200 s), 37-38 unique frames each ...
mean in summary: 1.8115
checks pass: 23 / 23
```

The mean moved, the sample list did not, every check still passed — confirmed.

## Per issue

### 1. F-6 carries typed sample numbers `--check` cannot see — CONFIRMED (R11, blocking)

Evidence: the demo above; the literals sit in `add(...)` in `build()`
(`"(1.251 / 1.183 / 1.200 s), 37-38 "`), while §3's table renders from `doc["rows"]`, so no check
could relate them. The same pattern existed for the §2 curve tuple, `InaccuracyAngle` 0.1,
`OverheatOffValue` 0.25 and the HeatBar pair.

Fix: the row's mean, sample list and frame range are formatted from the samples
(`" / ".join("%.3f" % t for t in air_times)`, `min/max(frames_airborne)`), and a check requires the
row text to contain that formatted list. The file-side numbers moved into `doc["file_values"]`
(`heat_up_per_second`, `overheat_off_value`, `inaccuracy_angle`, `inaccuracy_curve`,
`heatbar_start`, `heatbar_size`, `chain_gun_overheat_sound`) and the renderer prints them.

Same demo after the fix:

```
row text: **measured: 1.812 s mean** across three ramp jumps (1.851 / 1.783 / 1.800 s), 37-38 unique frames each ...
quote check passes: True
misquoted row passes: False        # row text edited to 9.999 / 9.999 / 9.999 in memory
```

### 2. `--check` never verifies `FOOTAGE.md` — CONFIRMED

Evidence: `main()` tested `os.path.isfile(md_path)` only and diffed the JSON. Fixed: it renders
`write_markdown(doc)` and compares, failing with `STALE: FOOTAGE.md does not match a fresh render
(run --write)`; the OK line ends `md byte-identical`.

### 3. Two checks cannot fail — CONFIRMED

Evidence: `bool(VULCAN_OUT_OF_FRAME)` where `VULCAN_OUT_OF_FRAME` is a non-empty constant;
`"UNREACHABLE" not in REASONS` where `REASONS` is a literal without that key; and the R4 check only
named two hardcoded gap labels.

Fix:
* "the Vulcan capture is recorded as out-of-frame" → **"no measured sample comes from the Vulcan
  capture (muzzle out of frame)"**, which walks every sample of every row against the Vulcan capture
  and can fail.
* the `UNREACHABLE` check → **"the air-control rows are MEASURED, not UNKNOWN (the corrected
  premise)"**, which inspects the rows.
* the R4 check → **every MEASURED row against every file-answered quantity**, plus **every RESOLVED
  row must cite a machine source, never footage**.
* added: row count ties to the sources (`72 = 5 card quantities + 61 mode fields + 1 measured + 5
  units`) and every native in `DAMAGE_RULES.md` is a row or explicitly out of scope (issue 9).

### 4. "The car is controllable in the air" — CONFIRMED (R4/R5)

Evidence: the samples time "first frame clear of the ramp" → "first contact" (`air_samples()`), which
is an airborne interval; nothing in the record observes attitude. The only steering evidence is the
clip names, and `bUsedAirControlDuringJump` is a member name.

Fix (row F-6 and §3): the measured claim is the airborne window; "steering rests on the clips'
names", `bUsedAirControlDuringJump` is called a member name not an observation, and "how much
authority they carry is UNKNOWN from the files".

### 5. The heat mechanism claim is stronger than the field — CONFIRMED (R4)

Evidence: the row said "firing adds no heat, so the bar cannot reach a stop and the weapon fires
indefinitely - the behaviour … is the field's own value". `HeatUpPerSecond` is the per-second term;
the same object carries `OverheatOffValue` **0.25** and `ChainGunOverheatSound` (import ref -148), so
the overheat path is wired.

Fix: "no per-second heat is configured" (what the field says) + "an overheat path is still wired" +
"a per-shot add in native code is not excluded by the grab, so the mechanism is **UNKNOWN** and the
observation stays yours". The correction box at the top of the note and the module docstring were
reworded the same way.

### 6. Five "answered" rows display no value — CONFIRMED (R11/evidence)

Evidence: 20 answered rows, 5 with `example_value is None` and no decoded array points, because
`q["fields"][0]` was taken regardless of whether it decodes (`ChargingScreenShake` for charge,
`MaxTargetsPerLevel` for salvo).

Fix: each quantity takes the first matched field that actually carries a value (`ChargeUpTime` 2.5,
`MaxTargets` 8), an `array_count` is recorded for the ones that do not decode, and the table says
"array present, contents not decoded (2 entries)"/"field present, contents not decoded". Summaries
now read `20 (17 with a decoded value)`. The intro no longer claims a value for all 20.

### 7. "each with >= 3 samples of itself" is not what was done — CONFIRMED

Evidence: 3 clips × 1 sample. Fix: the check is named "three ramp jumps are measured (one sample per
jump, three for the gap)" with detail `3 samples over 3 clips`, and it also asserts the three clips
are distinct.

### 8. The Health check verifies only the first package — CONFIRMED

Evidence: `health_val[0] == 1200`. Fix: asserts the list length equals `count` and every value is
1200 — detail prints `[1200, 1200, 1200]`.

### 9. Four G1-14 natives are not accounted for — CONFIRMED

Evidence: `DAMAGE_RULES.md` records 5 native entry points; FOOTAGE had one `NATIVE` row
(`ShouldRadialDamageHit`). Fix: a new §5 subsection "G1-14's other native entry points" lists
`CanBatmobileDoImpactDamage`, `GetDamageMod`, `SetArmouredMode`, `SetDamageLevel` with why each has no
footage observable (the `GetDamageMod` entry says ARM-2's hits-to-kill depends on a return value the
grab does not hold: UNKNOWN), and a check parses the native rows out of `DAMAGE_RULES.md` and fails if
any is neither a gap row nor listed. Currently: `5 native(s), unaccounted: none`.

## Files changed

| file | change |
|---|---|
| `Tools/scripts/grab_footage_gaps.py` | the nine fixes; `import re`, `first_value`/`field_array`/`fmt_num`/`fmt_val` helpers, `NATIVE_UNTRACED`, `doc["file_values"]`, `doc["natives_md"]`, md gate |
| `Research/BatmobileGrab/FOOTAGE.md` | regenerated (`--write`) — 27/27, reworded air/heat sections, answered table, natives subsection |
| `Research/BatmobileGrab/FOOTAGE.json` | regenerated — new `file_values`, `natives_md`, `natives_out_of_scope`, `answered[].decoded`/`array_count`, `summary.answered_decoded` |
| `Research/BatmobileGrab/README.md` | one row: the FOOTAGE.md description (no per-second heat, steering UNKNOWN, 20 (17 decoded), 27 checks) |
| `GRAB_BACKLOG.md` §12 `G1-23` row | one line: 27/27 + md byte-compared, heat/air wording corrected, natives recorded |
| `MODLOG.md` | intended-change entry, "G1-23 rework — done" |

Revert: restore `FOOTAGE.md`/`FOOTAGE.json` from
`tmp/freebuff/reports/FOOTAGE.before-g1-23-rework.{md,json}`, revert `grab_footage_gaps.py`, restore
the tracker line and README row, drop the two MODLOG entries.

## `--check` output (verbatim)

```
$ python -m py_compile Tools/scripts/grab_footage_gaps.py
(clean)

$ python Tools/scripts/grab_footage_gaps.py --check
OK: 72 rows, 2 file-resolved, 1 measured (3 samples), reasons {'FILE-VALUE': 2, 'MEASURED': 1, 'NOT-IN-CLIP': 2, 'VALUE-NATIVE': 53, 'UNDOCUMENTED': 5, 'WRONG-SCOPE': 8, 'NATIVE': 1}; 27/27 checks; md byte-identical
EXIT=0

$ python Tools/scripts/status_audit.py --check
STATUS.md is current
EXIT=0

$ python Tools/scripts/grab_model.py check
OK: grab output matches schema 6 and its own summary.
EXIT=0
```

`t_rows.py` was not run: no `Working/Translation/` row was touched.

## Tamper tests

```
# 1. hand edit the note
$ printf '\nhand edit\n' >> Research/BatmobileGrab/FOOTAGE.md
$ python Tools/scripts/grab_footage_gaps.py --check
STALE: FOOTAGE.md does not match a fresh render (run --write)
EXIT=1

# 2. change a summary number in the record
$ # summary.air_time_mean_s := 1.9 in FOOTAGE.json
$ python Tools/scripts/grab_footage_gaps.py --check
STALE: FOOTAGE.json does not match a fresh build (run --write)
EXIT=1

# restored
$ python Tools/scripts/grab_footage_gaps.py --check
OK: … ; 27/27 checks; md byte-identical
EXIT=0
```

Plus the in-memory F-6 quote test quoted under issue 1 (a row whose text misquotes its samples fails
the predicate).

## Values re-verified after regeneration

| value in `FOOTAGE.md` | where | verification |
|---|---|---|
| air times 1.251 / 1.183 / 1.200 s, frames 97→133 / 96→133 / 149→186 | `:44-46`, F-6 | the script's own PTS walk; unchanged from the pre-rework artifact (`diff` shows only text) |
| mean 1.212 s, spread 0.068 s | `:47` | `summary.air_time_mean_s` 1.2122, min 1.1832 max 1.2514 |
| `HeatUpPerSecond` 0, `OverheatOffValue` 0.25, curve 0/0.5/1.5/2.5 s → 0/0/1.5/3.0 | §2 | `WEAPONS.json`: 0.0 in all four cannon objects, point pairs unchanged |
| `ChargeUpTime` 2.5, `MaxTargets` 8 | §4 | `WEAPONS.json`: 2.5 ×4 heavy cannons; `Batmobile_JokerMissile_Launcher` 8 |
| `Health` [1200, 1200, 1200] | F-5 row | `OFFSETS.json` `RVehicleBatmobile` `Health`, count 3 |
| 72 rows, split 2/1/53/8/5/2/1 | summary | `FOOTAGE.json summary.by_reason`, sums to 72 |
