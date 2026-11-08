# G1-18 rework — tyre diameter reconciliation

Date: 2026-10-29. Input: `tmp/freebuff/reports/review-G1-18.md` (verdict "needs rework").
Task: verify every review issue against the data, fix the confirmed ones in the way
`GRAB_BACKLOG.md` §0.5 (R1–R14) requires, reject any that are wrong, re-run `--check`.

## STATUS: **done — all ten issues confirmed; nine fixed in the generator/doc, one blocked by the edit scope**

- Every tyre **number** in the old page was correct; the review reproduced them and so did the new
  script. What was wrong was the evidence (no script, no `--check`), two source cells, one
  mislabelled count, one arithmetic slip, one inference stated as fact, and three bits of geometry
  prose that the page's own rows contradict.
- `Research/BatmobileGrab/TYRES.md` is now **generated**, not hand-written:
  `python Tools/scripts/bmak_tyres.py --check` re-derives the tables from
  `Playable_Batmobile_SF/SkeletalMesh3/Batmobile_V2.pskx`, `Working/TrueScale/stations.json`,
  `Working/Translation/T_ROWS.jsonl` (T-G2/T-G6) and `Research/BatmobileGrab/CHAIN.json`, asserts
  four invariants, and diffs the rendered page against the stored one (exit 1 on any difference).
- No game launched, nothing written into `D:/Games`, no shared game module touched, no git commit.
- **Not edited:** `GRAB_BACKLOG.md` lines 138 (DIM-2) and 1257 (D-1) — the task permits only the
  §12 `G1-18` line. Both carry confirmed defects; the exact replacement text is given under
  "Blocked by scope" below.

## Check output (verbatim)

```
$ python Tools/scripts/bmak_tyres.py --check
OK: 4 tyres; tread Ø 1.3652-1.3657, shoulder Ø 1.3711-1.3714, width 0.7314-0.7325; station radius vs mesh <= 0.6 mm
OK: TYRES.md matches the re-derived render (169 lines)
EXIT=0
$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 40 keep 60 epe 26 re-read 0 blocked 13 out 36 superseded 7 | edits 35 over 16 rows
check ok
EXIT=0
$ python Tools/scripts/status_audit.py --check
STATUS.md is current
EXIT=0
```

`t_rows.py check` was run because the page quotes T-G2/T-G6 cells; it is unchanged and still green.

**Tamper test** (one digit changed by hand in the stored page, then `--check`):

```
FAIL
  - TYRES.md differs from the render (2 changed lines; first: -| f_l | 6,700 | 6,485 | **1.3653** | 1.3672 | 1.3711 | 0.7314 |)
EXIT=1
```

after `--write`, the two OK lines above again and `grep -c 1.3653 TYRES.md` = 0. The gate is real:
it fails on a hand edit, and the file on disk is the render.

## Per-issue

### 1. R11 — no script, no `--check` — **CONFIRMED**, fixed
Evidence: `ls Tools/scripts/*tyre*` → nothing; the old page's Out was the `.md` alone and the
MODLOG's "Verified" block listed only other cards' gates. The old §5 recipe printed one number
(`1.3652`).

Fix: new `Tools/scripts/bmak_tyres.py` (25,953 B) with `--write` / `--check`. It rebuilds every
table — per-wheel faces/verts/Ø(y)/Ø(z)/Ø max-radial/width/station radius/tread-to-ground, the
shoulder-bulge table, the bone inventory, the Disc-outside-envelope table, §3's quantities, the
three numbers, the physics chain and the D-1 record — and `--check` compares `write_md()` with the
file byte for byte. Nothing in `TYRES.md` is typed any more; the only prose the script carries is
prose about script-derived numbers.

### 2. `rear Ø1.369` attributed to T-G2 — **CONFIRMED**, fixed
Evidence: `grep -rn "1\.369" --include=*.md --include=*.json --include=*.jsonl --include=*.py .`
(excluding `tmp/`) returns only unrelated substrings — `adsk_physical.json` `"editorpos"
[-51.369865…]`, an `AnimSequence` float array, `Research/JC3Grab/FLEET.md` `1.3696` column, plus my
own new MODLOG text. `T_ROWS.jsonl` T-G2 holds `tyre Ø 1.366 m (mesh)`, `land_global.front/
rear_wheels.radius`, `rbm` wheel mesh bounds vs `radius`, `0.68275 / 0.68265` — no photo fit, no
1.369. The rear measures 1.3652–1.3654.
Fix: the sentence is gone; §2 now records explicitly that T-G2 carries **no** rear-tyre figure and
that no repo file records a rear diameter different from the front (`TYRES.md:96-98`).

### 3. `WheelRadius` 0.640 row cites `MECHANICS.md` — **CONFIRMED**, fixed
Evidence: `grep -c "WheelRadius" Research/BatmobileGrab/MECHANICS.md` → `0`.
Fix: the cell now reads `CHAIN.json` (offset 568, 64.0 cm) (`TYRES.md:139`).

### 4. "338 outside the tyre radius" is the vertical test — **CONFIRMED**, fixed
Evidence (re-run on the same vertices): radial about the hub, `√((y−hub)²+(z−hub)²) > 0.6855` →
**394**, z −2.798…−2.261; vertical only, `|y−hub| > 0.6829` → **338**, z −2.798…−2.328. The old
sentence printed 338 next to the radial z-range.
Fix: `TYRES.md:73-83` prints both, each with its own test named in the column header and the
selected vertex set ("faces/verts of the `Disc` **bone**", not the box), and says which one the
earlier pass mislabelled.

### 5. "4.8 cm above the ground" — **CONFIRMED**, fixed
Evidence: ground in the page's own frame is `stations.ground` = 0.02; Disc y-min 0.0699 →
0.0699 − 0.020 = **0.0499 → 5.0 cm**. 4.8 cm is 0.0699 − 0.0222, i.e. the transform's y offset.
Fix: `TYRES.md:85` reads "5.0 cm above the ground plane y = 0.02"; the §3 row that repeated 4.8 cm
is generated from the same values.

### 6. "2.0% short" and "1.025×" are different gaps — **CONFIRMED**, fixed
Evidence: 1.40/1.371 = 1.021 (+2.1%); 1.40/1.366 = 1.025 (+2.5%); the gap is 0.0346 m.
Fix: `TYRES.md:112-115` splits the two bases explicitly ("×1.021 (+2.1%) from the shoulder, ×1.025
(+2.5%) from the tread"), so no sentence mixes them.

### 7. What 1.42 measured stated as fact — **CONFIRMED**, fixed in the page
Evidence: `git log -S "1.42 m"` → only `7a0a07d`; no file records the method.
Fix: §3 is headed "What 1.42 might have measured — **UNKNOWN**", prints the four nearest measured
quantities (Disc vertical 1.4268; tyre+Disc+Fan box 1.4746 vertical / Ø1.5962 radial; tread 1.3654)
and states "Which of these — if either — the 1.42 … measured is **UNKNOWN**" (`TYRES.md:118-132`).
The §2 table row for 1.42 says "no source in the repo … What the docstring measured is UNKNOWN".
The **DIM-2** cell still asserts the old causal claim — see "Blocked by scope".

### 8. Geometry prose contradicted by its own rows; incomplete bone list — **CONFIRMED**, fixed
- 8a "inboard of the tyre" vs x −1.551…−0.525 while the tyre spans −1.574…−0.842: fixed;
  `TYRES.md:51` now says the Disc "spans the tyre's width" and the paragraph below states only its
  inner end (−0.525) lies 0.317 m inboard.
- 8b "The three bones": fixed — the section is now a measured inventory, "Faces whose three
  vertices lie inside the tyre's bounding box", listing all seven bones that own faces there:
  `Wheel_Frnt_Left_Disc` 8,198; `Wheel_Front_Left_Vis` 6,700; `SUSP2_Wheel_Front_Left` 4,938;
  `Damper_Left_Front_02` 776; `Wheel_Front_Left` 204; `Wheel_Frnt_Left_Fan` 32;
  `Batmobile_Chassis_Mesh` 2. **Note on the review's own numbers:** its `SUSP2 … 9,022 faces` is
  that bone's *total* face count, not its in-box count (4,938) — no contradiction, different
  measure; `SUSP1_Wheel_Front_Left`, `Wheel_Parent_F_L` and the two `*_Wheel_Armour` bones own **0**
  faces inside the box, so they do not belong in an in-box table.
- 8c rim Ø undefined: fixed — "The figure quoted as rim Ø is the **max radial distance from the
  hub**, 0.5127 → **Ø 1.0254**; the cap is dished, so its own y/z extent is 1.0096 / 1.0095 m, not
  the same measure."

### 9. `stations.json` `tyre_width` mirrored L↔R — **CONFIRMED**, fixed
Evidence: file f_l 0.7325 / f_r 0.7314 / r_l 0.7315 / r_r 0.7318 vs mesh f_l 0.7314 / f_r 0.7325 /
r_l 0.7318 / r_r 0.7315 — the same four numbers, L/R swapped; `stations.json` has no `tyre_bone`
key, so the attribution cannot be traced.
Fix: `TYRES.md:33-40` records the mirror explicitly, per corner, and warns that a consumer of
`tyre_width` must check the corner attribution (R3). The generator prints both columns, so a future
`stations.json` change that fixes or worsens the mirror will show up in the `--check` diff.

### 10. Record nits — **CONFIRMED (10b, 10c) / already true (10a)**
- 10a docstring corrected: verified —
  `sed -n 1,14p Tools/scripts/bat_assemble.py` shows "tyre Ø 1.366 m tread-to-tread, measured from
  the mesh … the 1.40 m reference is the wiki estimate, 2.4% out"; no 1.42 remains. No action.
- 10b no before/after text for the revert step: fixed — the MODLOG entry now quotes the exact line
  from `git show 7a0a07d:Tools/scripts/bat_assemble.py`
  (`(tyre Ø ≈ 1.42 m vs the 1.40 m reference)`) and the three lines that replaced it.
- 10c `GRAB_BACKLOG.md:1257` "tread Ø1.365–1.3657": confirmed (measured 1.3652–1.3657). **Blocked by
  scope** — see below.

Nothing was REJECTED: every issue in the review held up when re-measured.

## Blocked by scope (confirmed, not edited)

The task allows changing only the §12 `G1-18` line in `GRAB_BACKLOG.md`. Two confirmed defects sit
outside that line and are left for the decision owner:

1. `GRAB_BACKLOG.md:138` (DIM-2) — "the docstring's 1.42 was an assembly envelope, not rubber"
   repeats the UNKNOWN inference as fact (review issue 7). Suggested replacement of that clause:
   "the docstring's 1.42 has no source and what it measured is UNKNOWN (`TYRES.md` §3)".
2. `GRAB_BACKLOG.md:1257` (D-1) — "tread Ø1.365–1.3657" is a typo for **1.3652–1.3657** (review
   issue 10c).

## Files changed

| file | change |
|---|---|
| `Tools/scripts/bmak_tyres.py` | **new** — generator + `--check`; reads the PSKX, `stations.json`, T-G2/T-G6, `CHAIN.json`; asserts 4 corners, tread spread ≤ 0.6 mm, tread Ø = 2 × station radius ≤ 1.5 mm, tread on the ground ≤ 0.4 cm, and byte-diffs the page |
| `Research/BatmobileGrab/TYRES.md` | **regenerated** (169 lines, 9,965 B) — R11-clean, every number from the script; UNKNOWN where the data cannot support a claim; 394/338 split; 5.0 cm; mirrored `tyre_width`; measured bone inventory; reworded Disc/rim |
| `tmp/freebuff/reports/TYRES.before-g1-18-rework.md` | pre-rework copy of the old page (evidence, not a deliverable) |
| `GRAB_BACKLOG.md` | **§12 `G1-18` line only** (now cites the generator, `--check`, the 394/338 split, the 5.0 cm and the mirror) |
| `MODLOG.md` | intended-change entry before the edit, then "G1-18 rework — done" with the check outputs and the R14 revert text |

Revert: `git checkout -- Research/BatmobileGrab/TYRES.md` (or copy the `.before-g1-18-rework.md`
snapshot back) and delete `Tools/scripts/bmak_tyres.py`; the backlog and MODLOG entries are
append-only history and need no revert.

## Spot-checks (re-derived in the new script, printed by `--check`)

| value | where verified |
|---|---|
| tread Ø **1.3652 / 1.3657 / 1.3654 / 1.3652**, shoulder **1.3711 / 1.3714 / 1.3712 / 1.3711**, width **0.7314 / 0.7325 / 0.7318 / 0.7315**, faces 6,700/6,700/7,564/7,564 | `Wheel_Front_Left/Right_Vis`, `Wheel_Rear_Left/Right_Vis` vertex sets through `bat_assemble.to_jc3_rot` × 0.01 + `stations.json` offset |
| Disc **394** radial / **338** vertical outside the envelope; y 0.0699 → **5.0 cm** above y 0.02 | `Wheel_Frnt_Left_Disc`, 11,543 verts, both tests in the generator |
| tread Ø = 2 × station radius ≤ 0.6 mm; `land_global` 0.68275 / 0.68265 | `stations.json` radii ×2 vs mesh; T-G2 cells in `T_ROWS.jsonl` |
