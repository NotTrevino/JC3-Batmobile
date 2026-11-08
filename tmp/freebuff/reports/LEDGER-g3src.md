# LEDGER-g3src — 15 OPEN ledger rows re-derived from the decoded G3 files

STATUS: done

Fifteen rows still OPEN after `LEDGER_G3B.md` (96) and `LEDGER_G3C.md` (68) were re-derived
from the decoded G3 source files themselves, each with a file + line and an explicit rule.
Result: **10 holds, 4 wrong value, 1 not derivable**. No ledger, card or other task's file was
edited; the only writes are the new script, its generated `.md`/`.json`, and this report.

## The 15 rows

| row | ledger says | re-derived | source | verdict |
|---|---|---|---|---|
| T-FX5 | 74 `.effc` in the donor `.ee` | **74** rows (container == donor `.ee`, ext == `.effc`) | `FX_TABLE.jsonl:27222` | **holds** |
| T-FX10 | 11 vehicles | **12** distinct `.ee` carriers | `FX_TABLE.jsonl:5199` | **wrong value** |
| T-FX14 | 2 vehicles | **3** | `FX_TABLE.jsonl:2892` | **wrong value** |
| T-FX17 | 161 vehicles | **161** | `FX_TABLE.jsonl:379` | **holds** |
| T-FX18 | 289 vehicles | **290** | `FX_TABLE.jsonl:340` | **wrong value** |
| T-FX19 | 298 vehicles | **301** | `FX_TABLE.jsonl:461` | **wrong value** |
| T-FX21 | 126 vehicles | **126** | `FX_TABLE.jsonl:358` | **holds** |
| T-FX22 | 192 vehicles | **192** | `FX_TABLE.jsonl:349` | **holds** |
| T-FX23 | 139 vehicles | **139** | `FX_TABLE.jsonl:352` | **holds** |
| T-P2 | 17 damage types across 42 parts | **17 types, 42 parts** | `PARTS_TABLE.jsonl:39` | **holds** |
| T-PA4 | parts 11,12,26,27 → slots 3,2,0,1 | **exactly that**, spokes 1, spins 1 | `PARTS_TABLE.jsonl:39` | **holds** |
| T-PA7 | 20 parts skipped by the deform solver | **24** parts with `deform == 0` | `PARTS_TABLE.jsonl:39` | **not derivable** |
| T-S5 | 0.2 = fleet median, n=125, IQR 0.1…0.3 | **median 0.2, n=125, 0.1…0.3** | `T3_FLEET.md:25` (all-land) | **holds** |
| T-K3 | 1 = the 6 t median, band 1…2.25 | **median 1, n=26, 1…2.25** | `T3_FLEET.md:29` (6 t+) | **holds** |
| T-E2 | 1,121 at 6 t, ratio ×1.24 | **1,120.8** (`2.153 × 6000^0.719`), ratio **1.243** | `FITS.md:24` | **holds** |

The four mismatches are one and three too high on a rule that counts distinct `.ee` containers;
the same rows also count the same under `source` and under distinct `.ee` leaf names, so the
ledger's numbers are low under every rule tried - not a rule artefact. The report's §UNKNOWN 1
says what is still unread about the producer's rule.

T-PA7 is **not derivable** and is *not* marked wrong: `PARTS_TABLE` carries `parts[].deform`
(24 parts at 0), while the row's quantity is `DeformPoints.non_deformable_parts_indices`, which
lives in the built `.epe`. 20 is reproducible only by adding the unstated rule "wheels excluded"
(24 − 4). Marking that "holds" would have been fitting a rule to the answer.

## Files written

- `Tools/scripts/ledger_g3_rederive.py` — new script, `--write` / `--check`.
- `Working/Translation/LEDGER_G3_REDERIVE.md` — generated note (207 lines).
- `Working/Translation/LEDGER_G3_REDERIVE.json` — generated data (all 15 rows, oracles,
  UNKNOWNs).
- `tmp/freebuff/reports/LEDGER-g3src.md` — this report.

`--check` re-reads FX_TABLE (57,187 rows), PARTS_TABLE (233 rows), T3_FLEET.md, FITS.md,
T_ROWS.jsonl and LEDGER_G3B/C, recomputes every number, compares the stored JSON, re-renders
the `.md` and re-runs seven structural oracles; exit 0.

## Values, labelled

| value | label |
|---|---|
| FX carrier counts (74 / 12 / 3 / 161 / 290 / 301 / 126 / 192 / 139) | **derived** from `FX_TABLE.jsonl` (`container`, `path`, `ext`), rule stated per row |
| first line of each path in `FX_TABLE.jsonl` (5199, 2892, 340, 461, 379, 358, 349, 352, 27222) | **decoded** (line numbers in the file) |
| donor part census: 42 parts, 17 damage types, wheels 11/12/26/27 → 3/2/0/1, doors 1/2/25, 24 parts with `deform == 0`, 12 with `lights == 1` | **decoded** (`PARTS_TABLE.jsonl:39`, `sportsmuscle_vehicle_parts.vmodc`) |
| T3_FLEET medians/bands/n (0.2 @ n=125 0.1…0.3; 1 @ n=26 1…2.25) | **decoded** (`T3_FLEET.md:25`, `:29`) |
| FITS fit a=2.153, b=+0.719, R²=0.808, n=142 (`FITS.md:24`) | **decoded** |
| 1,120.8 at 6,000 kg; ratio 1.243 | **derived** (a × 6000^b; 1393.5 / 1120.8) |
| 955 distinct `.effc` paths, 512 donor FX rows, 57,187 FX rows | **derived** by counting the table |
| the producer's exact "vehicles" rule; T-FX5's "23 unreferenced by the 51 rows"; T-PA7's 20 | **UNKNOWN** (see below) |

## Commands run (verbatim, abridged only where a command printed 96 rows)

1. First load of the ledgers — failed on the Windows console code page, not on the data:

```
$ uv run python - <<'PY'  ... print row ids and cells ...
UnicodeEncodeError: 'charmap' codec can't encode character '\u2212' in position 51
exit=1
```

   fixed with `PYTHONIOENCODING=utf-8` for every later run.

2. Row inventory (96 OPEN ids from `LEDGER_G3B.json`, cells from `T_ROWS.jsonl`):

```
$ PYTHONIOENCODING=utf-8 uv run python ...   (prints id | member | now per OPEN row)
T-G1     `land_global.base_wheel_hardpo | now=front z −2.570, rear z +2.459; x ±1.208 front / ±1.285 rear; y 0.7047
T-M2     `rigid_body.unit_inertia_yaw / | now=1.8 / 1.5 / 0.5
T-S1     `suspension.front/rear.strengt | now=**80 / 80**
...
T-FX5    74 `.effc` in the donor `.ee`   | now=23 unreferenced by the 51 rows
T-FX10   `effects/jc_weapons/muzzle_fla | now=absent: the Batmobile carries no weapon until the T-11 clone
```

   (one earlier variant of this dump died on `T-P1`: `IndexError: list index out of range`,
   because some rows have fewer than 8 cells; the script now reads cells defensively.)

3. `CHAIN.json` schema — needed to see whether the physics rows could be re-read there:

```
$ PYTHONIOENCODING=utf-8 uv run python ...
top keys: ['verdict', 'sdk_classes', 'objects_bound', 'named_bindings', 'offsets_cross_checked', 'cross_check_conflicts', 'ambiguous_bitfields', 'still_unnamed', 'fields', 'unnamed']
RBasicProjectile  rows=13 ... SVehicleWheel rows=16 ...
sample row: {"offset": 568, "name": "SVehicleWheel.WheelRadius", "type": "FloatProperty", "value": 64.0, "named_by": "sdk-layout"}
```

4. `PARTS_TABLE.jsonl` + `FX_TABLE.jsonl` census:

```
$ ... print donor row and FX schema ...
PARTS_TABLE rows: 233
donor rows: [(39, 'sportsmuscle_vehicle_parts.vmodc'), (40, ...), (41, ...)]
 entity: editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.ee
 parts: 42 distinct dt: 17
 wheels: [{'part': 11, 'slot': 3, 'spokes': 1, 'spins': 1}, {'part': 12, 'slot': 2, ...},
          {'part': 26, 'slot': 0, ...}, {'part': 27, 'slot': 1, ...}]
 doors: [1, 2, 25]
 lights==1: 12   deform==0: 24
FX rows: 57187  ext census: {'.effc': 25025, '.trim': 25707, '.ctunec': 6455}
distinct .effc paths: 955   donor .effc rows: 74
```

5. Carrier counts per path before choosing the rule:

```
effects/jc_vehicles/collision/chassis_slide_default.effc    290 vehicles
effects/jc_vehicles/damage/dmg_fire_engine.effc             192 vehicles
effects/jc_vehicles/damage/dmg_post_burn.effc               139 vehicles
effects/jc_vehicles/damage/exp_car_01.effc                  126 vehicles
effects/jc_vehicles/wheels/trail/dust_trail_asphalt.effc    161 vehicles
effects/jc_weapons/missile/missile_trail_car.effc             3 vehicles
effects/jc_weapons/muzzle_flash/tank_canon_muzzleflash.effc  12 vehicles
effects/trails/spark_trail_02_med.effc                      301 vehicles
```

6. Rule test for the four mismatches (`container` vs `source` vs `.ee` leaf):

```
tank_canon_muzzleflash.effc  ledger=11 container=12 source=12 src_ee=12 mounts=['base', 'dlc']
missile_trail_car.effc       ledger=2  container=3  source=3  src_ee=3  mounts=['base', 'dlc']
chassis_slide_default.effc   ledger=289 container=290 source=290 src_ee=290 mounts=['base','dlc','patch']
spark_trail_02_med.effc      ledger=298 container=301 source=301 src_ee=301 mounts=['base','dlc','patch']
```

7. First `--write` — crash on the comma in `1,121`:

```
ValueError: could not convert string to float: '1,121'
```

   fixed (`num_from` strips thousands separators). A second pass reported T-PA7 as `holds`
   through a variant rule; that was rejected as rule-fitting and changed to `not derivable`.

8. Final write and check:

```
$ PYTHONIOENCODING=utf-8 uv run python Tools/scripts/ledger_g3_rederive.py --write; echo "write_exit=$?"; PYTHONIOENCODING=utf-8 uv run python Tools/scripts/ledger_g3_rederive.py --check; echo "check_exit=$?"
wrote LEDGER_G3_REDERIVE.md / .json
counts: {'holds': 10, 'wrong value': 4, 'not derivable': 1}
  T-FX5   holds         derived=74                     ledger_n=74  FX_TABLE.jsonl:27222 (container == donor .ee, ext == .effc)
  T-FX10  wrong value   derived=12                     ledger_n=11  FX_TABLE.jsonl:5199
  T-FX14  wrong value   derived=3                      ledger_n=2   FX_TABLE.jsonl:2892
  T-FX17  holds         derived=161                    ledger_n=161 FX_TABLE.jsonl:379
  T-FX18  wrong value   derived=290                    ledger_n=289 FX_TABLE.jsonl:340
  T-FX19  wrong value   derived=301                    ledger_n=298 FX_TABLE.jsonl:461
  T-FX21  holds         derived=126                    ledger_n=126 FX_TABLE.jsonl:358
  T-FX22  holds         derived=192                    ledger_n=192 FX_TABLE.jsonl:349
  T-FX23  holds         derived=139                    ledger_n=139 FX_TABLE.jsonl:352
  T-P2    holds         derived=17                     ledger_n=-   PARTS_TABLE.jsonl:39 (sportsmuscle_vehicle_parts.vmodc)
  T-PA4   holds         derived=parts=[11, 12, 26, 27] ledger_n=-  PARTS_TABLE.jsonl:39 (sportsmuscle_vehicle_parts.vmodc)
  T-PA7   not derivable derived=24                     ledger_n=20  PARTS_TABLE.jsonl:39 (sportsmuscle_vehicle_parts.vmodc)
  T-S5    holds         derived=0.2                    ledger_n=0.2 T3_FLEET.md:25 column all land
  T-K3    holds         derived=1                      ledger_n=1   T3_FLEET.md:29 column 6 t+
  T-E2    holds         derived=1120.8                 ledger_n=1121 FITS.md:24
oracles: {'fifteen_rows_selected': True, 'every_row_is_open_in_the_ledgers': True, 'every_source_file_exists': True, 'fx_scan_covers_the_whole_table': True, 'every_row_has_a_verdict_and_a_source': True, 'no_row_reads_a_paint_or_collision_source': True, 'ledgers_and_existing_cards_untouched': True}
write_exit=0
OK: 15 rows (10 holds, 4 wrong value, 1 not derivable); all structural oracles true
check_exit=0
```

## Why these 15 and not others

- 27 of the 96 G3B OPEN rows cite none of the seven sources (`LEDGER_SOURCES.md` §2): their
  supplier is `stations.json`, the §70 mesh measurement or a card from another family.
- The 68 G3C OPEN rows are card-keyed (world/light/warpaint): their supplier is a decode that
  does not exist yet, so there is nothing to re-read. That is why no G3C row appears here.
- Paint rows (T-MA1/3/4/5/7) were excluded: `COLOUR_PARAMS.md` states the combine operator is
  UNKNOWN, so any effective colour is an assumption, not a re-derivation.
- Collision rows (T-CO1/2/3) were excluded: no decoded collision source is in this set.
- CHAIN.json turned out not to carry any of the candidate values: its 20 classes are the
  weapons, lights, booster and wheel archetypes, and the physics rows that cite it rest on
  fleet statistics rather than on a chain member (that is why the three fleet-sourced rows
  above come from `T3_FLEET.md` / `FITS.md`).

## UNKNOWNs

1. **The producer's exact "vehicles" rule.** My counts (distinct `.ee` containers, distinct
   `source`, distinct `.ee` leaf names) all give 12 / 3 / 290 / 301 for the four mismatching
   paths, against the ledger's 11 / 2 / 289 / 298. The ledger's numbers come from the T-13 card,
   whose producer is not among the five files read here, so the rule is inferred from the rows
   that *do* agree (5 of 9), not read from code. Where it would be found: `Tools/scripts/`
   FX producer for T13, or `Working/Translation/T13_FX.md`.
2. **T-FX5's second half** — "23 unreferenced by the 51 rows". The 51 T-13 effect rows are
   outside these five sources; the 74 (the row's first number) re-derives exactly.
3. **T-PA7's quantity.** `DeformPoints.non_deformable_parts_indices` is an array in the built
   `.epe`, not in `PARTS_TABLE`. The decoded neighbour is 24 (and 22 with a body, 20 excluding
   wheels); which one the array encodes is UNKNOWN from these files.
4. **Whether the four FX counts are stale or differently counted.** Both readings are possible
   and this pass cannot separate them: a card written before a table refresh, or a stricter
   vehicle identity (e.g. one entry per vehicle model rather than per bundle).
