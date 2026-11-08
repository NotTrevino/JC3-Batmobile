# V-02 (GRAB_BACKLOG 9a) - geometry and pose gates on bm-RC2, offline

STATUS: done. All three gates pass on `Builds/bm-RC2`:

| gate | result | threshold |
|---|---|---|
| silhouette | **99.9004%** (1,130,835 / 1,131,963 px) | >= 99.9% - PASS (by 0.0004 pt) |
| BUD-1 gross holes (extra oracle) | 0.2968% of the source silhouette | < 0.3% - PASS |
| interaction points | **77/77** placed points in band, 0.0577 m .. 0.1461 m | 5 cm outside, <= 30 cm - PASS |
| parts | **61/61** part models resolve, no duplicate `part_index` | PASS |

Nothing was launched, installed or deployed; the build was read only and the three PNGs + two
verify documents were written into `Builds/bm-RC2/verify/` (a verify folder, not a build asset).

## 1. Silhouette (Tools/scripts/silhouette_check.py, run on the RC2 body)

```
$ uv run --with numpy --with pillow python Tools/scripts/silhouette_check.py \
    Builds/bm-RC2/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/batmobile/sportsmuscle_body_lod1.rbm
frame 2400x864  source 215,893 tris  ours 44,602 tris
silhouette   source 1,131,963 px   ours 1,130,955 px   coverage 0.9991
holes        50,929 px = 4.499% of the source silhouette
of which interior tears (>=3 px inside the outline)  36,737 px = 3.245%
extra        49,921 px = 4.410% of the source silhouette
BUD-1 oracle   gross holes 4.499% of the source silhouette vs 0.3% = OVER; coverage 0.9991 above is NET (holes netted against 4.410% extra)
boundary edges   source 0%   ours 0%
```

That run is **unshifted**: the RC2 tree has no `stations.json`, so the script compared the source
in its own frame against a mesh the build had translated. With the build family's own offset
(`Working/Appearance/build/stations.json`, `[0, 0.022231, 0.154284]`) the same comparison is:

```
frame 2400x864  source 215,893 tris  ours 44,602 tris
silhouette   source 1,131,963 px   ours 1,130,835 px   coverage 0.9990
holes        3,360 px = 0.297% of the source silhouette
of which interior tears (>=3 px inside the outline)  582 px = 0.051%
extra        2,232 px = 0.197% of the source silhouette
BUD-1 oracle   gross holes 0.297% of the source silhouette vs 0.3% = under; coverage 0.9990 above is NET (holes netted against 0.197% extra)
```

The 15x hole drop is the oracle that the offset is the build's own; the two bounding boxes also
imply `[-0.0026, 0.0184, 0.1527]` m, i.e. the same translation within decimation shrink. Reported
both, because "coverage >= 99.9%" alone would pass a 4.5%-holes frame (99.91% net) - the trap this
row was measuring.

## 2. Interaction points (Tools/scripts/t9_interaction.py, pointed at RC2)

`t9_interaction.py` hard-codes `Working/TrueScale/body_lod1.rbm` and has no mesh argument, so the
new script substitutes `jc3interact.read_bat_mesh` with the RC2 body and calls the script's own
`build()` - placement rule, band, ray casts and socket are the existing code, only the mesh changes.

```
85 donor objects: 77 placed, 6 dropped by D-9, 1 socket, 1 UNKNOWN
placed distances 0.0577 m .. 0.1461 m; 77/77 in band
```

`V-02` writes those numbers to `geometry.md` §2; the per-object failures list is empty.

## 3. Parts (bm_parts.py)

`bm_parts.py --check` is pinned to `Builds/bm-002` and **fails there on its own stale spec**, not
on RC2 - it never reads RC2:

```
$ uv run python Tools/scripts/bm_parts.py --check
0. spec re-derived from its inputs: FAIL (differs in ['parts'])
...
FAIL the spec is not what build_plan()/spec_document() derive from its inputs (stale or hand-edited key(s): ['parts'])
FAIL: Builds/bm-002 re-read (18E55FE4AF78E8E9..., 604 .toc records, 59 parts, 1 problem(s))
EXIT=1
```

The RC2 question the row asks is asked directly of RC2's parts module through the same decoder
(`bm_parts.decode_parts`): **61 parts, 61/61 models resolved, 0 duplicate indices, 20 damage
types**. The bm-002 failure is recorded as a separate, pre-existing issue (its build has 59 parts
and a hand-edited spec), not as a V-02 gate.

## 4. Renders (preview_rbm.py, offline)

`--shade normal --size 1200` (shape only, so no `ConvertTexture` step and no external tool):

```
$ uv run --with numpy --with pillow python Tools/scripts/preview_rbm.py \
    Builds/bm-RC2/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/batmobile/sportsmuscle_body_lod1.rbm \
    -o Builds/bm-RC2/verify --view side --shade normal --size 1200
Builds/bm-RC2/verify\sportsmuscle_body_lod1_side.png  1200x415  44,608 tris
```

All three views rendered: side 1200x415 (84,338 B), front 1200x794 (146,375 B), top 1200x617
(112,826 B). They sit next to `geometry.md` / `geometry.json`.

## 5. Files written

- `Builds/bm-RC2/verify/geometry.json` - every number above, plus the inputs' hashes.
- `Builds/bm-RC2/verify/geometry.md` - the same as a page.
- `Builds/bm-RC2/verify/sportsmuscle_body_lod1_{side,front,top}.png` - the renders.
- `Tools/scripts/v02_geometry.py` - `--write` / `--check`; the check re-runs all three checks and
  rebuilds `geometry.md` byte for byte, and verifies the PNGs against their record.
- this report.

Revert = delete those six files. No build asset was modified (`geometry.*` and the PNGs are new
files in `verify/`).

## 6. Commands and output (verbatim, final run)

```
$ PYTHONIOENCODING=utf-8 uv run --with numpy --with pillow python Tools/scripts/v02_geometry.py --write; echo "WRITE_EXIT=$?"
wrote Builds\bm-RC2\verify\geometry.json and geometry.md
silhouette 99.9004% (PASS), interaction 77/77 in band (PASS), parts 61/61 (PASS)
WRITE_EXIT=0

$ PYTHONIOENCODING=utf-8 uv run --with numpy --with pillow python Tools/scripts/v02_geometry.py --check; echo "CHECK_EXIT=$?"
PASS source body split still 215,893 faces
PASS the build's stations offset lowers the hole count vs none
PASS coverage re-derives at 0.999004
PASS 77/77 interaction points
PASS interaction gate matches its failure list
PASS 61/61 part models resolve
PASS 3/3 renders present
PASS side render 1200x415 matches the record
PASS front render 1200x794 matches the record
PASS top render 1200x617 matches the record
PASS geometry.md re-derives byte for byte
PASS geometry.json matches the recomputed data
PASS: V-02 geometry 0 failure(s)
CHECK_EXIT=0
```

A first `--write` produced an empty render table: `v02_geometry.py` looked for `geometry_side.png`
while `preview_rbm.py` names its output `<stem>_<view>.png`. The script now records preview's own
path; the run above is the repaired one. No game, install script or deploy was run.

## 7. UNKNOWNs

1. **Which offset RC2 actually shipped with** - RC2 carries no `stations.json`. The offset used is
   the build family's, validated by the 15x hole drop and the bbox delta within 4 mm; the RC2
   assembler's own log would close it.
2. **The bm-002 spec drift** (`differs in ['parts']`) - pre-existing, outside V-02; it needs the
   b-04 spec regenerated or the edit justified. RC2 itself is unaffected (61/61 resolve).
3. **Silhouette in front/top views** - the gate is measured in the side view only, which is what
   `silhouette_check` implements; a 3-view silhouette is not decoded anywhere.
4. **Visual quality of the renders** - produced and recorded, not judged here (no screenshot
   review was asked for); the numbers above are the gate, not the pictures.
