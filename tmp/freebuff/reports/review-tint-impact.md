STATUS: done - review complete. VERDICT: the report's check passes 14/14 and its conclusion ("no hit places a tint in the .epe") survives re-opening the cited files, but the phrase "wrong assumption" appears nowhere in it - the two hits it discounts as evidence carriers are `Working/Entity/bm_epe_edits.json` and `Tools/scripts/bm_entity.py`, both verified to contain no tint or palette string at all, and neither the report nor the two tint-bearing rows claims the tint is written into the `.epe`. The one missed search term is `CarPaintMM` (193 hits in `Working/`), which is the actual carrier of the "every paint block" half the report parks as out of scope.

# Review of `tmp/freebuff/reports/tint-palette-impact.md` (task 7224)

Task: run the report's check script, re-open the two repo hits it calls "wrong assumption" and
confirm whether each really says the tint is written into the `.epe`, then search `Working/` for a
term the report did not use and report extra hits.

## 1. The check script

The report names `Tools/scripts/t_tint_impact.py` (`--write` / `--check`, 14 gates). It exists and
`--check` passes: 14/14 gates, the generated `Working/Translation/TINT_IMPACT.md` matches its
128-line regeneration byte-for-byte, exit 0. No gate was skipped or loosened by this review (the
script was run, not edited).

## 2. The two "wrong assumption" hits - the premise does not hold

The report never uses that phrase. The only occurrence in the whole reports directory is an
unrelated chase report:

```
$ grep -rn -i "wrong assumption" tmp/freebuff/reports/
tmp/freebuff/reports/chase-G3-01b-boxes-u2.md:179:$ python tmp/freebuff/scratch/g301x_6.py        # first prefilter attempt - WRONG ASSUMPTION

$ grep -rn -i "wrong assumption" Working/Translation/
(no output)
```

`tint-palette-impact.md` and its generated `TINT_IMPACT.md` classify every hit with a `holds?`
column (`HOLDS` / `n/a` / `no assumption`). Exactly **two** hits carry "no assumption", and they are
the two repo hits whose job would be to write a tint into the `.epe`:

| hit | file | what the report says | what re-opening the file shows |
|---|---|---|---|
| #16 | `Working/Entity/bm_epe_edits.json` | 19 edits, 0 naming tint/palette | `grep -c -i "tint\|palette"` -> **0**; the file's 19 edit rows and 27 additions are named `.epe` members, so it cannot carry a tint claim - confirmed |
| #17 | `Tools/scripts/bm_entity.py` | 0 tint/palette strings, writes the `.epe` via `ConvertProperty` | `grep -c -i "tint\|palette"` -> **0** - confirmed; the writer applies named members only |

So **neither cited file says the tint is written into the `.epe`**, which agrees with the report
rather than contradicting it. The premise "it calls two repo hits a wrong assumption" is not
supported by the file; treating #16/#17 as those two hits is my reading of the report's own
`no assumption` label, and it is labelled as a reading, not as the report's words.

The two rows that actually make tint claims are `T-MA4` and `T-MA5`, and neither mentions the
`.epe` either:

```
T-MA4 keep | build carries the proposal; nothing to edit
   2 `CarPaintMM` gloss
   4 **0.45** in every paint block and in all 10 palette tints
T-MA5 keep | build carries the proposal; nothing to edit
   2 `Window` block
   4 tint = the authored paint colour (`VALUES.json` glass: `Material0_BaseColour` ...)
```

`T-MA4` is a `CarPaintMM` gloss (RBM material) plus the palette records; `T-MA5` is the `Window`
material's base colour. Neither is an `.epe` write, and `Research/JC3Grab/TINT_WRITE.md` §1 states the
decoded reason: `tint_r` is **not an `.epe` member** - the `.epe` carries only the 4-byte palette
path hash (`CCar.palette` at `0x29a`), the tint lives in the palette `.vmodc`. The report's summary
line, "no tint byte is written anywhere", is therefore consistent with every file re-opened here.

## 3. The term the report did not use

The report's scan terms were `tint|palette` (per `TINT_IMPACT.md` §2). It never searched the
material-block family. Extra hits in `Working/`:

| term | hits in `Working/` | files | relevance |
|---|---:|---|---|
| `CarPaintMM` | **193** | 8 material sets under `Working/Assembled/`, `Working/Appearance/{,grb6,build_parts,build_parts_dry,factors,diag}/`, `Working/verify_078.json`, `Working/verify_079.json` | the actual carrier of T-MA4's "every paint block" half, which the report parks as "a different carrier, not judged here" |
| `BaseColour` | 17 | `Working/Audio/umodel_batmobile_dump.txt` (`Main_BaseColour`, `Main_BaseColour2`, `Material0_BaseColour`, `Material2/3_BaseColour`), `Working/Audio/mk2_names.txt` | the material-parameter family T-MA5 quotes as `Material0_BaseColour`; the dump shows the whole family, including the `Main_*` pair |
| `diffuse_adjust` | 0 | - | the term does not occur in `Working/` |

The substantive miss is `CarPaintMM`: `Working/Assembled/factors.json` lists **8** parts whose block
is `CarPaintMM` (`Batmobile_V3_Mainbody_NEW_MIC`, `..._TEXTURES_Body_Decals`, `BatmobileV3_Wheel_V2_MIC`,
`BatmobileV3_Cockpit_Seat`, `BatmobileV3_Upgrades_MAT_INST`, `Batmobile_V3_Cockpit_MIC`,
`Batmobile_V3_Discbreak_MIC`, `Batmobile_V3_Emissive`), and `Working/verify_078.json` /
`verify_079.json` each carry `"CarPaintMM": 200`. That is where T-MA4's gloss 0.45 would have to be
verified, and the report excludes it - explicitly, as out of scope, not by mistake. Whether 200 is a
count, a byte size or a slot total is not stated in either file: **UNKNOWN** (not asserted here).

## 4. Files written

| file | what it is |
|---|---|
| `tmp/freebuff/reports/review-tint-impact.md` | this review |

No source, report, ledger or build file was modified. `t_tint_impact.py` was executed read-only; its
`--check` re-derives `TINT_IMPACT.md` and only compares.

## 5. Commands and verbatim output

```
$ PYTHONIOENCODING=utf-8 python Tools/scripts/t_tint_impact.py --check
PASS G1-rows                198 rows, 7 tint/palette cell hits in 3 rows, 5 palette-record hits
PASS G2-rows-dispo          every hit row is dispo=keep, edits=0 (no row edits were made)
PASS G3-plan-lines          appearance_plan.json 5 tint lines, APPEARANCE_PLAN.md 3
PASS G4-plan-no-palette     no plan line mentions a palette
PASS G5-epe-edits           19 edits, 0 naming tint/palette; 27 additions
PASS G6-bm_entity           0 tint/palette strings in bm_entity.py; writes the .epe via ConvertProperty
PASS G7-palette-sha         RC2 palette sha256 72d5d04f78c6 == bm-005 == 72d5d04f78c6
PASS G8-palette-records     10 tints: tint_r 0.05/0.05/0.05/1, gloss 0.45, metallic 1, clear_coat 1 in every record
PASS G9-rc2-pointer         RC2 palette int 1322976751 == Jenkins(batmobile palette path) == 1322976751 at 0x29a
PASS G10-bm005-pointer      bm-005 palette int -1071400364 == Jenkins(default palette path)
PASS G11-epe-has-no-tint    exports: RC2 tint_r x0, Palette class False; bm-005 tint_r x0
PASS G12-rc2-epe-set        RC2 ships 1 .epe: Builds/bm-RC2/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.epe
PASS G13-receipt-move       receipt moved the palette to batmobile/ and repointed it x1
PASS G14-receipt-sha        receipt cites palette sha256 72d5d04f78c6

PASS Working\Translation\TINT_IMPACT.md matches (128 lines)
check_exit=0
```

```
$ grep -rn -i "wrong assumption" tmp/freebuff/reports/
tmp/freebuff/reports/chase-G3-01b-boxes-u2.md:179:$ python tmp/freebuff/scratch/g301x_6.py        # first prefilter attempt - WRONG ASSUMPTION

$ grep -rn -i "wrong assumption" Working/Translation/
(no output)
```

```
$ grep -c -i "tint\|palette" Working/Entity/bm_epe_edits.json
0
$ grep -c -i "tint\|palette" Tools/scripts/bm_entity.py
0
```

```
$ PYTHONIOENCODING=utf-8 python -c "... print T-MA4/T-MA5/T-MA7 cells ..."
T-MA4 keep | build carries the proposal; nothing to edit
   0 T-MA4
   1 authored gloss 0.6, vanilla caps paint gloss at 0.4
   2 `CarPaintMM` gloss
   3 clamp to the vanilla cap, then raise
   4 **0.45** in every paint block and in all 10 palette tints
   5 keep 0.45
   6 derived
   7 dry-road screenshot: satin armour, not wet mirror (079 was the mirror)
T-MA5 keep | build carries the proposal; nothing to edit
   0 T-MA5
   1 `Batmobile_Glass` (8 slots empty), `...GLASS_D/N/MASK` textures present
   2 `Window` block
   3 empty slots → tint only
   4 tint = the authored paint colour (`VALUES.json` glass: `Material0_BaseColour` — the canopy has no colour parameters); opacity = ...
```

```
$ (code search, ripgrep-backed, cwd Working)
BaseColour     17 matches in 2 files: Audio\umodel_batmobile_dump.txt (Main_BaseColour, Main_BaseColour2,
               Material0_BaseColour, Material2_BaseColour, Material3_BaseColour),
               Audio\mk2_names.txt (5 names)
diffuse_adjust  0 matches
CarPaintMM     193 matches: Assembled\factors.json, Assembled\coverage.md, Assembled\assembly.json,
               verify_078.json ("CarPaintMM": 200), verify_079.json ("CarPaintMM": 200),
               Appearance\{progress.md,progress.json,grb6\*,factors\*,build_parts\*,build_parts_dry\*,diag\body_blocks.json}
```

Method note: `grep -rn` over all of `Working/` timed out at 120 s and `rg` is not on this bash's
PATH, so the three-term census was taken with the repo's code-search tool (`code_search`, cwd
`Working`); the single-file greps above are plain `grep`. The `BaseColour` run reported a search
timeout while still returning its 17 matches, so that count is what the tool returned, not a proof
of exhaustiveness - see UNKNOWNs.

## 6. UNKNOWNs

* **Whether the report's 17-hit census is exhaustive.** Its scan terms are `tint|palette`; a
  material-block term such as `CarPaintMM` was never in the scan. Whether any *other* unsearched term
  hides a tint claim is UNKNOWN - only the three terms above were tried.
* **What `Working/verify_078.json` / `verify_079.json`'s `"CarPaintMM": 200` means** (count, byte
  size, slot total). Neither file labels it and this review did not trace the writer.
* **Whether T-MA4's "0.45 in every paint block" is true in the built RBM.** That is an RBM material
  value, not an `.epe` or palette value; the report excludes it and this review did not decode it.
* **Whether the game honours the palette pointer** in play - test ban; unchanged by this review.

## 7. Labels

Decoded: the check output, the grep counts, the row cells, `TINT_WRITE.md` §1/§2.2 (the `tint_r`
offsets and the `CCar.palette` hash at `0x29a`). Derived: the mapping of "two hits called wrong
assumption" onto the report's two `no assumption` rows, which is a reading of its label, not its
wording. UNKNOWN: the four items above. Nothing was filled in from general knowledge of JC3, UE3 or
Arkham Knight, and no claim in the reviewed report was altered - it is another task's file.
