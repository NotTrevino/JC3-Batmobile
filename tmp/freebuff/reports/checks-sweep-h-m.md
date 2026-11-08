**STATUS: DONE — h..m sweep ran, 83 `--check` scripts, 61 ok, 22 red. Nothing fixed.** Page: `Working/Translation/CHECKS_SWEEP_HM.md`; raw rows: `tmp/freebuff/scratch/sweep_h-m.jsonl`; per-script full stdout: `tmp/freebuff/scratch/sweep_logs/<script>.log`.

# Repo health sweep, letters h..m

Command (after reading `--help`):

```
python Tools/scripts/checks_sweep.py h m --jobs 6 \
  --jsonl tmp/freebuff/scratch/sweep_h-m.jsonl \
  --md Working/Translation/CHECKS_SWEEP_HM.md
```

Exit status **1**, which is the sweep's normal signal for "some row is red", not a crash. Selection is every `Tools/scripts/*.py` whose first letter is h..m and whose text contains `--check` (85 names start h..m, 2 have no `--check`, 83 ran). Each ran under the generated `tmp/freebuff/scratch/checks_guard.py` audit hook (300 s wall limit, cwd = repo root, `stdin` closed) as it does for the a..g half.

| candidates | ok | red | real failure | missing dependency | missing input file | usage error | skipped (write guard) | timeout |
|---|---|---|---|---|---|---|---|---|
| 83 | 61 | 22 | 9 | **0** | **0** | 1 | 11 | 1 |

**No `missing dependency` and no `missing input file` rows**: every h..m script that failed had its dependencies and its inputs available. The reds are stored-record drift, one timeout, one interface mismatch, and the write guard.

## Every failing script, with its reason class

### real failure (9)

| script | exit | evidence from its own output | reason class |
|---|---|---|---|
| `jc3eject.py` | 1 | `FAIL EJECT.md stale` … `-232 vehicle .epe graphs in E:/Modding/_JC3grab\detail` / `+… in E:/Modding/_gamedata/JC3grab\detail` (also line 323) | stale document: the record still cites the old game-data root `_JC3grab`, the re-derivation cites `_gamedata/JC3grab` |
| `jc3_feature_census.py` | 1 | `STALE …FEATURE_CENSUS.md` line 16: `detail_root` disk `E:/Modding/_JC3grab/detail` vs derived `E:/Modding/_gamedata/JC3grab/detail`; `FAIL: 1 file(s) differ` | stale document, same root rename |
| `jc3weapons.py` | 1 | `FAIL: 25 ids, 197 extracted files, 24 shared tunes, md 1223 lines`; diff at §11: `_JC3grab/weapons` → `_gamedata/JC3grab/weapons` | stale document, same root rename |
| `jc3_last_entry.py` | 1 | `FAIL: Research/JC3Grab/LAST_ENTRY.json differs from the re-derived record` (single line, no path in it) | stored JSON differs from its re-derivation; **which field differs is UNKNOWN** from this run |
| `jc3hudwpn.py` | 1 | `FAIL: JC3_HUD_WEAPONS.json stale` (single line) | stored JSON stale vs re-derivation; field-level cause UNKNOWN from this run |
| `jc3lights.py` | 1 | `FAIL: LIGHT_SYSTEM.json stale` (single line) | stored JSON stale vs re-derivation; field-level cause UNKNOWN from this run |
| `jc3_runtime_layout4.py` | 1 | `json identical False  md identical True` / `verdict UNKNOWN  hits 15  readers 33  callers 54` / `CHECK FAIL` | the JSON half of the record is out of step with the re-derivation while the MD still matches, and the script's own verdict line is UNKNOWN — it treats a non-proven claim as a failure |
| `hud_spec.py` | 1 | last line `give --bmak and/or --jc3` (this run produced only that line; the a..g-era run showed it then dying in `int()` on that string) | no-argument invocation path: it asks for `--bmak`/`--jc3` and exits nonzero; no spec was re-derived |
| `jc3wiring.py` | 1 | `FAIL: census 53 entities != rows 0` / `FAIL: 0 entities, 0 weapons, 0 bound, 0 unbound, 0 seats, md 148 lines`; its log also ends `GUARD blocked write: E:/Modding/_gamedata/JC3grab\wiring\epe\v5603_train_urga_monorailmissilecar_military_01.ee.epe` | **guard-truncated, not proven drift**: the tool classified exit 1 as a real failure, but the run's only written state is 0 rows because its intermediate `.epe` write was blocked. Classification is the tool's; the cause is the guard |

### timeout (1)

| script | exit | evidence | reason class |
|---|---|---|---|
| `jc3_runtime_layout3.py` | TIMEOUT | log is **empty** — `(no output before 300s)` | exceeded the 300 s wall limit. It printed nothing at all under `PYTHONUNBUFFERED=1`, so where it spends the time is UNKNOWN; in the earlier h..z sweep it did emit partial output (`invariants not universal: none`) before being killed |

### usage error — `--check` not accepted (1)

| script | exit | evidence | reason class |
|---|---|---|---|
| `jc3hkx.py` | 2 | `usage: jc3hkx.py [-h] {build,report,wiring,check,write} ...` / `error: the following arguments are required: cmd` | interface mismatch: `check` is a **subcommand** (`jc3hkx.py check …`), not a `--check` flag; the file only mentions `--check` in prose, so no check ran |

### skipped — writes outside `tmp/` (11, all exit 77)

The guard refused the write; nothing on disk changed. The path is the script's own target.

| script | blocked path |
|---|---|
| `install_v2.py` | `E:\Modding\_dropzone_sim_rc2_case_a` |
| `install_v3.py` | `E:\Modding\_dropzone_sim_rc2_v3_prefix_14496` |
| `jc3_tint_write.py` | `Builds\bm-005\aaf\…\modules\default\v0300_car_kensington_sportsmuscle_palette.vmodc` |
| `jc3audio.py` | `E:/Modding/_gamedata/JC3grab\wiring\epe\v0300_car_kensington_sportsmuscle_civilian_01.ee.epe` |
| `jc3doors.py` | `E:/Modding/_gamedata/JC3grab\wiring\epe\v5603_train_urga_monorailmissilecar_military_01.ee.epe` |
| `jc3emp.py` | `E:/Modding/_gamedata/JC3grab\wiring\epe\v0505_car_solar_oldtruck_rebel_emp_01.ee.epe` |
| `jc3forcepulse.py` | `E:/Modding/_gamedata/JC3grab\wiring\epe\v0000_car_autostraad_oldjeep_civilian_01.ee.epe` |
| `jc3moving.py` | `E:/Modding/_gamedata/JC3grab\tmp\vehicle_common.vmodc` |
| `jc3rebeldrop.py` | `E:/Modding/_gamedata/JC3grab\rebeldrop\archives_win64_game2__profile_item.onlinec` |
| `jc3sigdiff.py` | `E:/Modding/_gamedata/JC3grab\sigdiff\civilian.epe` |
| `jc3turret.py` | `E:/Modding/_gamedata/JC3grab\wiring\epe\v0201_car_capstone_mediumtank_military_01.ee.epe` |

These are **not** stale-record failures: their `--check` writes a scratch copy outside `tmp/` before comparing, so under this harness they cannot be judged either way.

## Where this differs from the older `Working/Translation/CHECKS_SWEEP_H.md`

That page was produced by a different driver (`tmp/freebuff/scratch/checks_sweep_h.py`) and is **not comparable row-for-row**. Named differences visible here:

- **Installers.** `checks_sweep.py` has no installer ban, so `install_v2.py` / `install_v3.py` ran; both were stopped by the guard at `_dropzone_sim_rc2_*` paths. The old page excluded them outright ("skipped - installer (test ban)").
- `jc3moving.py`: `ok` on the old page, **skipped** here (blocked write `_gamedata/JC3grab\tmp\vehicle_common.vmodc`).
- `jc3hkx.py`: `real failure` on the old page, **usage error** here (the classifier now recognises the argparse rejection).
- `jc3wiring.py`: labelled `skipped` on the old page while its text was a `real failure`; here the exit-1 class wins and the guard line is inside its log.
- `jc3_runtime_layout3.py`: had partial output on the old page, **empty** here before the 300 s kill.
- `-` vs `?` character mangling: the old page was written through a non-UTF-8 path; this page keeps the tool's UTF-8 (`clean()` maps undecodable bytes to `?`).

## Cosmetic script quirk (not fixed, per instruction)

The generated page's byline reads "Generated by `python Tools/scripts/checks_sweep.py h m --md Working/Translation/CHECKS_SWEEP_A.md`" — `page()` interpolates the literal `CHECKS_SWEEP_A.md` instead of the path it was given. The page's own title and content are correct for h..m; only that sentence names the a..g file. Not edited, and the page was not hand-patched (it must stay reproducible by `--render`).

## What was and was not touched

- Written by the sweep: `Working/Translation/CHECKS_SWEEP_HM.md` (150 lines, 83 rows) and, under `tmp/`, the JSONL, the guard, and one log per script in `tmp/freebuff/scratch/sweep_logs/` (that directory also holds logs from earlier a..g / h..z sweeps).
- No script, build, research record or game-data file was edited; no fix was attempted; no game was launched. The guard's 11 blocked writes are the evidence that no `--check` reached `Builds/`, `Research/` or the game data.
- Page integrity checked by re-rendering the JSONL to a scratch page and diffing it against the delivered page: identical.
