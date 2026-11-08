# T-17 FX pairs - DONE report

STATUS: done. Three chosen pairs were audited in full and all three hold: the `.effc` is
real, the row's size/arrays/rows/vehicles/family counts match the FX table, and the BmAK
group's systems/emitters/names/lifetime match the row's claim. Four of the five omissions
hold under the term each row cities; **T-FX16 does not name a search term, so its "0 of 955"
claim is UNKNOWN, not reproduced**. No chosen path is broken: 11 of the 12 are effects
**embedded in indexed `.ee` containers** (not index entries - that is why they "miss" the
index), and 1 (`spark_trail_02_med.effc`) is a standalone index entry whose index size
equals the row's byte count exactly. `--check` passes 11/11 gates and re-derives the `.md`
byte for byte. Read-only; no build tree touched.

## Files written

| file | what |
|---|---|
| `Working/Translation/FX_PAIR_AUDIT.md` | 96 lines: index explanation, 12-row existence/count table, the three audited pairs with BmAK and colour facts, the five-omission scan table, checks, UNKNOWNs |
| `Tools/scripts/t_fx_pair_audit.py` | `--write` / `--check`; rebuilds every number from `t17_fx.json`, `FX_TABLE.jsonl`, `INDEX.jsonl`, `PARTICLES_FEATURES.json` |
| `tmp/freebuff/reports/particles-to-effc.md` | this report |

## What the audit found

**Index reality.** `INDEX.jsonl` (`jc3index.py`) names 81,952 entries but only **35**
standalone `.effc` files. `FX_TABLE.jsonl` has 57,187 rows over **1,533** distinct effect
paths. The doc's **955** is exactly the subset whose `root` is `EffectRTSystem` (955 of
1,533), which is why the absence scans below use 955. An effect path embedded in an `.ee`
never appears as an index path, so "not in the index" needed the container check, not a
verdict on its own.

**The three audited pairs**

| row | chosen effect | existence | row counts | BmAK group | verdict |
|---|---|---|---|---|---|
| T-FX7 | `car_cycle_base_dual_nitrous.effc` (20,671 B / 337 arrays / 3,161 rows) | embedded, 17 rows in 17 containers, **17/17 containers indexed** | size/arrays/rows/vehicles 17/family 1 all match | `afterburner-exhaust`: 12 systems / 5 names / 114 emitters, life 0.05..5.0 - decoded 12 / 5 / 114, life 0.05..5.0 | holds |
| T-FX10 | `tank_canon_muzzleflash.effc` (27,519 B / 604 / 5,331) | embedded, 12 containers, **12/12 indexed** | matches incl. **11 vehicles** (11 distinct `/jc_vehicles/` containers of 12) | `muzzle-flash`: 21 systems / 6 names / 117 emitters, life 0.05..2.0 - decoded 21 / 6 / 117, same life | holds |
| T-FX19 | `spark_trail_02_med.effc` | **index entry**: `patch_win64/game1+453507072`, **8,495 B**, mount `patch` - equal to the row's 8,495 B | matches incl. 298 vehicles (298 of 301 containers) and the 3-variant family | `wall-scrape`: 0 systems / 0 emitters - decoded 0 / 0 (the row is the `derived` borrow) | holds |

**Colour.** None of the T-FX rows states a colour, so there is no colour claim to hold or
break. The document lists the decoded palettes for context (afterburner: 73 entries from
`StartColor` / `ColorScaleOverLife`; muzzle flash: 161 entries from `StartColor` /
`ColorOverLife` / `ColorScaleOverLife`; wall-scrape: none, 0 systems).

**The five omissions**

| row | terms scanned over the 955 | hits | verdict |
|---|---|---|---:|
| T-FX9 heat haze | `haze`, `steam`, `heat` | 0 haze, 0 steam, 1 heater path | holds (the hit is `car_speedrom_heater.effc`, a heater effect) |
| T-FX12 tracers | `tracer` | 0 | holds |
| T-FX13 shell casings | `casing`, `shell_eject` | 0 casings, 2 shell-eject | holds - both are the non-vehicle `w15x` weapon carriers the row itself names |
| T-FX16 cannon round trail | none named by the row | - | **UNKNOWN** - no term to reproduce; `trail` hits are too broad to settle it |
| T-FX20 brake-light trails | `brake` | 0 | holds |

**One derived convention, stated as such:** the rows' `vehicles` numbers reproduce as the
count of distinct containers under `/jc_vehicles/` (all 12 rows). The rows never say what
they count, and the container totals are higher (12 vs 11, 301 vs 298) because non-vehicle
containers carry the same effect - that part stays UNKNOWN.

## Commands, verbatim

```text
$ python Tools/scripts/t_fx_pair_audit.py --write
wrote Working/Translation/FX_PAIR_AUDIT.md: 12 chosen, 5 omissions; claims 12/12 hold
  T-FX9 holds
  T-FX12 holds
  T-FX13 holds
  T-FX16 UNKNOWN
  T-FX20 holds
```

```text
$ python Tools/scripts/t_fx_pair_audit.py --check
  rows_17                                  PASS
  chosen_12                                PASS
  omissions_5                              PASS
  fx_rows_57187                            PASS
  fx_paths_1533                            PASS
  effectrtsystem_paths_955                 PASS
  index_effc_35                            PASS
  all_chosen_in_fx_table                   PASS
  all_chosen_size_rows_arrays_hold         PASS
  audited_groups_hold                      PASS
  file_matches_rederivation                PASS (8501 bytes of text)
OK
```

Index / FX table probes that produced the figures (python one-liners by category, run in
the repo root):

```text
$ python -c "... INDEX.jsonl ..."
rows 81952  effc in index 35
MISS car_cycle_base_dual_nitrous.effc []
MISS tank_canon_muzzleflash.effc []
HIT  effects/trails/spark_trail_02_med.effc ('patch_win64/game1', 453507072, 8495, 'patch')
```

```text
$ python -c "... FX_TABLE.jsonl ..."
fx rows 57187 distinct paths 1533
{'all': 1533, 'mount_base': 1229, 'mount_dlc': 844, 'veh_container': 845, 'root_EffectRTSystem': 955}
effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc rows 17 containers 17 digests 1 sizes [20671]
effects/jc_weapons/muzzle_flash/tank_canon_muzzleflash.effc rows 12 containers 12 digests 1 sizes [27519]
effects/trails/spark_trail_02_med.effc rows 301 containers 301 digests 1 sizes [8495]
```

```text
$ python -c "... keyword scan over the 955 EffectRTSystem paths ..."
haze []  0
heat ['effects/jc_vehicles/exhaust/car_speedrom_heater.effc']  1
steam []  0
tracer []  0
casing []  0
shell_eject ['effects/jc_weapons/shotgun/impacts/shell_eject_12ga.effc',
             'effects/jc_weapons/shotgun/impacts/shell_eject_12ga_auto.effc']  2
brake []  0
```

## UNKNOWNs

* **T-FX16's absence proof.** The row claims "0 of 955 match" without naming the term it
  searched; the 955 set holds many `trail` effects, so a broad scan cannot settle it.
  Would be found in: `t17_fx.py`'s absence rule for the projectile-trail group, which this
  audit did not read.
* **What "vehicles" counts in `t17_fx.json`.** The `/jc_vehicles/` container count
  reproduces all 12 rows, but it is a derived convention, not a decoded field, and why the
  container totals are higher (12 vs 11, 301 vs 298) is not decoded.
* **Runtime behaviour of every pair.** Test ban: nothing here was launched or installed;
  the T-17 verify cells remain Q probes.
* **Colour of the BmAK groups in play.** The rows make no colour claim; the decoded palettes
  are reported but no row-to-colour judgement is made.

## COMPROMISES

None. Read-only audit of other tasks' outputs; `T_ROWS.jsonl`, `T13_FX.md` and the build
trees were not modified.
