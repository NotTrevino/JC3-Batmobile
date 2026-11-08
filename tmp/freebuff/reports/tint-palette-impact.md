# Task 7211 - every tint/palette assumption vs TINT_WRITE.md

STATUS: DONE - 17 tint/palette hits across the named sources (7 T_ROWS cells, 8 appearance-plan
lines, 2 RC2-receipt entries); two named sources contain none. No hit places `tint_r` in the
`.epe`. The build writes the palette pointer only; no tint byte is written anywhere.

Files written:

* `Working/Translation/TINT_IMPACT.md` (128 lines, generated)
* `Tools/scripts/t_tint_impact.py` (`--write` / `--check`, 14 gates)
* this report

No row was edited. `Working/Translation/T_ROWS.jsonl` was read only; its mtime is untouched by
the script (it opens the file read-only). No build tree was modified; the two `.epe` exports go
to a temp directory that is deleted on exit.

## What was checked, and the answer

| source | hits | what the hit is about | does the build write the tint? |
|---|---|---:|---|
| `T_ROWS.jsonl` | 7 cells in 3 rows | 5 palette-record claims (T-MA4 x1, T-MA7 x4), 2 material-tint cells (T-MA5) | no |
| `Working/Appearance/appearance_plan.json` | 5 | Window/material tint, no palette | no |
| `Working/Appearance/APPEARANCE_PLAN.md` | 3 | shader tint components, no palette | no |
| `Working/Entity/bm_epe_edits.json` | 0 of 19 edits, 27 additions | `.epe` members only | no |
| `Tools/scripts/bm_entity.py` | 0 strings | writes the `.epe` via `ConvertProperty` | no |
| `Builds/bm-RC2/receipt.json` | 2 entries | palette module copy + pointer repoint | pointer only |

(Note: the brief named `Working/Translation/appearance_plan.json` and
`Working/Translation/APPEARANCE_PLAN.md`; those paths do not exist. The plan lives at
`Working/Appearance/appearance_plan.json` and `Working/Appearance/APPEARANCE_PLAN.md`, which is
what was scanned.)

Per-hit verdicts:

* **T-MA4** ("0.45 in every paint block and in all 10 palette tints", `dispo: keep`,
  `why: build carries the proposal`): the palette half **holds as a vanilla value**. All ten
  records decode at gloss `0.45`, `metallic 1`, `clear_coat 1` in the RC2 palette, whose sha256
  equals bm-005's (`72d5d04f78c6...`). No palette byte is written; nothing needs to be. The
  "every paint block" half is an RBM material edit, a different carrier, not judged here.
* **T-MA5** (two cells: "empty slots -> tint only", "tint = the authored paint colour"): Window
  material tint, **not a palette claim**; no relation to `tint_r`.
* **T-MA7**, four cells: "`Palette` does not exist in UE3 vehicles" **holds** (the RC2 `.epe`
  export has no `Palette` object and no `tint_r`, only the hash); "`Palette.tints[]`" **holds**
  (the palette `.vmodc` is the carrier); "10 tints, all gloss 0.45, clear_coat 1, metallic 1"
  **holds** (decoded 10/10 exactly); "leave the donor's palette untouched" **holds** (the module
  is byte-identical to bm-005).
* **plan json / md**: all eight lines are the Window/glass tint or shader tint map. Not a palette
  claim.
* **`bm_epe_edits.json`**: 19 edit rows, 0 name tint or palette; 27 additions likewise. No
  assumption to contradict.
* **`bm_entity.py`**: 0 occurrences of tint/palette; it applies named `.epe` members via
  `ConvertProperty`. No tint write path exists in the graph writer.
* **RC2 receipt**: `b18.moved` maps the vanilla palette to `.../batmobile/...` with sha256
  `72d5d04f...` (vanilla bytes); `b18.repointed[.../civilian_01.epe]` counts the palette x1.
  The pointer is written (`CCar.palette` = `1322976751` at `0x29a`), the tint is not.

## The one discrepancy worth flagging

RC2 ships exactly **one** `.epe`: `..._debug.epe` (8259 exported lines). bm-005 shipped only
`..._civilian_01.epe` (8271 lines). The receipt's repointed key still names the merge-stage
`civilian_01.epe`; the built tree carries `debug.epe` with the `batmobile/` palette hash. So the
receipt's filename and the shipped filename differ - the pointer content is present, the key is
the pre-rename name. Whether the game honours the pointer depends on which entity file it loads;
that is UNKNOWN and unchanged by this card.

## Commands and verbatim output

1. Locating the appearance plan (the brief's paths were wrong):

```
$ cd "E:/Modding/JC3-Batmobile"; find . -iname "*appearance*plan*" -not -path "./.git/*" 2>/dev/null | head -20
./Tools/scripts/appearance_plan.py
./Tools/scripts/__pycache__/appearance_plan.cpython-313.pyc
./Working/Appearance/appearance_plan.json
./Working/Appearance/APPEARANCE_PLAN.md
```

2. Scanning the sources:

```
$ grep -n -i "tint\|palette" Tools/scripts/bm_entity.py | head
(no output)

$ grep -n -i "tint\|palette" Working/Entity/bm_epe_edits.json | head
(no output)

$ grep -n -i "palette" Builds/bm-RC2/receipt.json | head -20
56:   "editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_palette.vmodc": "editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/batmobile/v0300_car_kensington_sportsmuscle_palette.vmodc",
122:    "editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_palette.vmodc": 1,
442:    "path": "editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/batmobile/v0300_car_kensington_sportsmuscle_palette.vmodc",
```

3. Decoding the RC2 palette records (the numbers T-MA4/T-MA7 quote):

```
$ python - <<'EOF'
import sys; sys.path.insert(0,'Tools/scripts')
import jc3adf
p='Builds/bm-RC2/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/batmobile/v0300_car_kensington_sportsmuscle_palette.vmodc'
a=jc3adf.Adf(open(p,'rb').read())
vals=dict((k,v) for k,_t,v in jc3adf.walk(a))
ks=[k for k in vals if k.endswith('.name.string')]
print('tints',len(ks))
...
EOF
tints 10
0 White occ 100 rgba [0.05000000074505806, 0.05000000074505806, 0.05000000074505806, 1.0] gloss 0.44999998807907104 metal 1.0 coat 1.0
1 Evergreen Pearl occ 100 rgba [0.05..., 0.05..., 0.05..., 1.0] gloss 0.45 metal 1.0 coat 1.0
... (all ten records identical except the name)
9 Green occ 100 rgba [0.05..., 0.05..., 0.05..., 1.0] gloss 0.45 metal 1.0 coat 1.0
```

4. The palette bytes and both `.epe` pointers:

```
$ sha256sum Builds/bm-RC2/aaf/.../modules/default/batmobile/..._palette.vmodc Builds/bm-005/aaf/.../modules/default/..._palette.vmodc
72d5d04f78c64120409362646db273ef6f83d9d99606f257794ef5df9c49073b *Builds/bm-RC2/.../batmobile/..._palette.vmodc
72d5d04f78c64120409362646db273ef6f83d9d99606f257794ef5df9c49073b *Builds/bm-005/.../default/..._palette.vmodc

$ ConvertProperty --e Builds/bm-RC2/..._debug.epe tmp/.../bm-RC2.xml; grep 'name="palette"' ...
37:			<value name="palette" type="int">1322976751</value>
(grep -c "tint_r" -> 0)

$ ConvertProperty --e Builds/bm-005/..._civilian_01.epe tmp/.../bm005.xml; grep 'name="palette"' ...
37:			<value name="palette" type="int">-1071400364</value>
(grep -c "tint_r" -> 0)

$ python - (struct.search for the int in the RC2 epe)
hits ['0x29a']
```

5. The generator and its final check:

```
$ python -m py_compile Tools/scripts/t_tint_impact.py && python Tools/scripts/t_tint_impact.py --write && python Tools/scripts/t_tint_impact.py --check

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

wrote Working\Translation\TINT_IMPACT.md (128 lines)
... same 14 PASS lines ...
PASS Working\Translation\TINT_IMPACT.md matches (128 lines)
rc=0
```

Two rendering defects were caught and fixed before this run: the §2.1 line printed literal
`%.2f` placeholders (missing `%` operands) and the STATUS/totals counts were wrong (4/3 instead
of 7/5 hits). Both were corrected in the generator, and the final `--check` above is on the
corrected output.

## UNKNOWNs

* **Whether the shipped `debug.epe` or the base archive's `civilian_01.epe` is the entity the
  game loads for the civilian variant.** Tried: the RC2 receipt (`b18.repointed` names
  `civilian_01.epe`), the built tree (only `debug.epe`), and the `.ee` archive (AAF; no repo
  reader). Static check only, test ban. Does not affect the tint finding - neither file has a
  tint value.
* **Which material field the paint menu varies to produce the ten named colours** (`tint_r`
  is identical `0.05` in all ten records, so the record name alone selects something else).
  Tried: `TINT.md` (occurrence weights, no selector), the palette record decode. No selector in
  any file read; still UNKNOWN, and unchanged by this card.

## COMPROMISES

None. No build, row, or source file was modified; no test was run.
