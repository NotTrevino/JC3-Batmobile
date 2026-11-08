# Independent review — G1-18 · Tyre diameter reconciliation

Reviewer: Freebuff (did not write this card). Date: 2026-10-29.
Scope: `GRAB_BACKLOG.md` §0.5 (R1–R14), card G1-18, tracker §12 row, DIM-2/D-1 rows; MODLOG §"G1-18 · Tyre
diameter — done"; `Research/BatmobileGrab/TYRES.md`; the inputs it measures (`Batmobile_V2.pskx`,
`Working/TrueScale/stations.json`, `T_ROWS.jsonl` T-G2/T-G6, the `bat_assemble.py` docstring).
Read-only: no project file was modified. This report is the only file written.

## VERDICT: **needs rework**

Every tyre number in the doc is **correct** — I re-measured all four wheels through `bat_assemble.to_jc3_rot`
× 0.01 + offset and reproduced the diameters, widths, face counts, shoulder radius, tread-to-ground gaps,
the `Disc`/`Fan` figures and the 1.3711/1.3714 shoulder spread to the last printed digit. The D-1 decision is
properly filled and its arithmetic checks out.

What fails is the **evidence and four sentences**: there is no script and **no `--check` at all** for this
card (R11; §0.2 step 5/6 were satisfied by prose instead of a command), one number in the 1.366 row has no
traceable source (`rear Ø1.369` attributed to T-G2, which does not contain it), one source cell cites a file
that does not carry the value (`WheelRadius` → `MECHANICS.md`), one count is computed by a different test than
the words say (338 vs 394), and the "4.8 cm above the ground" figure contradicts the doc's own ground plane
(5.0 cm). These are bounded fixes — a `bmak_tyres.py --write/--check` plus five corrections — not a re-measure.

Out path: `Research/BatmobileGrab/TYRES.md`, 7,234 B — exists, the only Out the card names (no `.json`, no
script).

## Check output (verbatim)

**There is no `--check` for this card.** `Tools/scripts/` contains no tyre/`TYRES` script; the card's Out is
the `.md` alone, and the MODLOG's "Verified" block lists only *other* cards' gates (`grab_*`, `bmak_chain`,
`status_audit`, …) plus `py_compile` — none of which reads a tyre number. The only executable recipe is §5 of
the doc; run verbatim (with `PSKX` pointing at
`Playable_Batmobile_SF/SkeletalMesh3/Batmobile_V2.pskx`) it prints exactly one number:

```
1.3652
```

That covers the tread diameter of one wheel. Widths, rim Ø, `Disc` extents, the 338 count, station radii and
the shoulder Ø have **no command** behind them, so the card's Done ("one table with the three numbers
explained; D-1 filled") was accepted without a machine check — contrary to §0.3 ("\"Looks right\" is never
done") and R11 ("tables of counts in new docs come from a script with `--check`").

## Issues

### 1. R11: no script, no `--check` — every table value is prose
`Research/BatmobileGrab/TYRES.md:14-19` (per-wheel table), `:27-31` (rim/aperture), `:33-44` (three bones),
`:52-58` (three numbers), `:82-86` (physics chain). None of these tables is generated; the card produced no
`.json` and no script, and the only re-measurable figure in §5 is the tread diameter (`:107-118`). Every other
number depends on a one-off snippet that no longer exists. The measurements themselves reproduce (see
spot-checks), so the fix is mechanical: port them to `Tools/scripts/bmak_tyres.py --write/--check` producing
the tables and a JSON, then regenerate the doc from it. Until then the doc breaks R11 by the letter of §0.5.

### 2. `rear Ø1.369` attributed to T-G2 does not exist anywhere (R4)
`TYRES.md:55`: "T-G2's own photo fit: front Ø1.366, rear 1.369". T-G2 is
`Working/Translation/T_ROWS.jsonl` (and `T1_TRANSLATION.md:78`); its cells are `tyre Ø 1.366 m (mesh)`,
`land_global.front/rear_wheels.radius`, `0.68275 / 0.68265`, check "`rbm` wheel mesh bounds vs `radius`" —
**no photo fit, no 1.369**. A repo-wide grep finds `1.369` only in this sentence. The rear measurement is
1.3652–1.3653 (spot-check 1), so the sentence also contradicts the card's own finding that all four tyres are
the same mould to 0.5 mm. Either cite where 1.369 came from or delete it.

### 3. The `WheelRadius` 0.640 row cites a file that does not contain it (R4)
`TYRES.md:85`: "| BmAK `SVehicleWheel.WheelRadius` | 0.640 | 1.280 | `MECHANICS.md` |". `MECHANICS.md` has no
`WheelRadius` text and no wheel-radius value (grep: 0 hits; its only `Wheel*` rows are `RWheelLight` sockets).
The value 64.0 exists in `Research/BatmobileGrab/CHAIN.json` (`{"offset":568,"name":"SVehicleWheel.WheelRadius",
"value":64.0,"named_by":"sdk-layout"}`) and in T-G6. The number is right, the source cell is wrong.

### 4. "338 outside the tyre radius" is a different test than the words say
`TYRES.md:45-47`: "**338 of its 11,543 front-left vertices lie beyond the tyre's radius**, all at x −1.370…−1.046
and z −2.798…−2.328". Reproduced on the same vertices:
- radial distance about the hub (what "beyond the tyre's radius" means): `sqrt(dy²+dz²) > 0.6855` → **394**
  verts, `x[−1.3702,−1.0457]`, `z[−2.7982,−2.2610]`;
- vertical offset only (`|y−hub_y| > 0.6829`): **338** verts, `x[−1.3702,−1.0457]`, `z[−2.7978,−2.3281]` —
  the doc's count *and* its z-max.
So the sentence's number and its quoted z-range come from the vertical test while the words name a radial
one; the radial answer is 394 with z-max −2.261. Both facts are true, but the label must say which is meant
("outside the tyre's radius vertically" / "beyond the tyre crown").

### 5. "4.8 cm above the ground" contradicts the doc's own ground plane
`TYRES.md:47` and `:75` ("stops 4.8 cm above the ground"). The doc defines ground as y = 0.02 (`:14`) and the
`Disc` row prints y 0.070…1.497 (`:42`); 0.0699 − 0.020 = **0.0499 → 5.0 cm**. The 4.8 cm comes from using the
transform's y offset 0.0222 instead of the stated ground; with that plane the tread-bottom column would read
−0.0001, not +0.0021. One of the two references is wrong; the table's own numbers imply 5.0 cm.

### 6. "2.0% short" and "1.025×" are two different gaps
`TYRES.md:68-69`: "Ø including the shoulder = 1.371, which is still **2.0% short** of 1.40 (reaching 1.40 needs
a **1.025×** scale-up …)". 1.40/1.371 = 1.021 (2.07%); 1.40/1.366 = 1.0249 (2.4%). The 1.025 factor belongs to
the 1.366 tread, not to the 1.371 shoulder in the same sentence. Pick one basis.

### 7. What 1.42 measured is an inference stated as fact (R4)
`TYRES.md:72-78`: "the only quantity in the wheel near 1.42 is the `*_Disc` bone's vertical extent, 1.427 …
**The docstring measured the assembly, not the tyre.**" The measured 1.427 is real (spot-check 4) and the
heading hedges ("probably"), but the closing sentence asserts the original author's method, which no file
records — `git log -S "1.42 m"` only proves the string enters in `7a0a07d`, not what it measured.
`GRAB_BACKLOG.md:138` (DIM-2) then repeats it as fact ("the docstring's 1.42 was an assembly envelope, not
rubber"). Under R4 the causal claim is `UNKNOWN`; the measurable facts (1.427 exists; nothing measures 1.42)
can stand without it.

### 8. Geometry prose contradicted by the row's own numbers, and an incomplete bone list
`TYRES.md:42`: the `Disc` is described as "the inner wheel structure (**inboard of the tyre**…)" while the same
row prints `x 1.026 (−1.551…−0.525)`; the tyre's own x range, not printed in the doc, is `−1.574…−0.842`
(measured, spot-check 1) — the Disc overlaps the tyre's entire width and only its inner end (−0.525) is 0.317 m
inboard. `:34` ("`*_Disc` owns everything inboard of
it") repeats the mis-description.
Also `:32-44` is headed "The three bones, one wheel", but five more bones per front corner own faces in the
wheel volume: `SUSP2_Wheel_Front_Left` (9,022 faces, y 0.091…1.650), `SUSP1_Wheel_Front_Left` (1,184), bare
`Wheel_Front_Left` (204, x −1.513…−1.343, y 0.851…1.194), plus `Wheel_Parent_F_L` and the two
`Batmobile_*_Wheel_Armour` bones (0 faces). None is the tyre, so the diameters are unaffected, but the
"everything inboard" / "three bones" framing is not what the mesh shows.
Smaller: the rim figure `1.0254` (`:29`) is the max distance from the hub; the `Fan`'s own y/z extent is
**1.0096** (`y 0.1999…1.2095`, `z −3.0746…−2.0652`), 15 mm smaller, because the cap is dished. The doc does not
say which measure "rim Ø" is.

### 9. Observation for D-1 consumers (not the doc's number): `stations.json` per-corner width is mirrored
`TYRES.md:16` measures f_l 0.7314 / f_r 0.7325 / r_l 0.7318 / r_r 0.7315 (reproduced). `stations.json` records
f_l 0.7325 / f_r 0.7314 / r_l 0.7315 / r_r 0.7318 — the same four numbers with L/R swapped, exactly. The
`station radius` column in the doc copies `stations.json` and matches its corner (0.6829/0.6826/0.6826/0.6827,
within 0.6 mm of the mesh), so the doc's ≤2 mm claim holds, but the width half of the same file is attributed to
the opposite corner and the doc does not notice. `stations.json` has no `tyre_bone` key in this revision, so the
derivation cannot be traced; whoever consumes `tyre_width` for physics should know.

### 10. MODLOG/record nits
- MODLOG:8567 "**Record:** … the `bat_assemble.py` docstring line corrected" — true: the docstring now reads
  "tyre Ø 1.366 m tread-to-tread, measured from the mesh … the 1.40 m reference is the wiki estimate, 2.4% out"
  (`bat_assemble.py:9-11`). No 1.42 remains. ✓
- The card's out-of-date In quote ("tyre Ø ≈ 1.42 m vs the 1.40 m reference") is now only in the card, which is
  fine (cards are history), but nothing in the MODLOG records the exact before/after text, so the revert step
  ("restore the docstring line") has nothing to restore from. Minor (R14).
- `GRAB_BACKLOG.md:1257` (D-1) writes "tread Ø1.365–1.3657"; the measured range is 1.3652–1.3657 — a typo that
  reads as 1.3650. Trivial.

## Spot-checks

Measured with `psk2rbm.read_pskx` + `pskx_parts.skeleton/face_bones` + `bat_assemble.to_jc3_rot`, × `stations.scale`
0.01 + `stations.offset`, ground = `stations.ground` 0.02, radial = √((y−hub_y)²+(z−hub_z)²).

| value in the doc | where verified |
|---|---|
| per-wheel face counts 6,700 / 6,700 / 7,564 / 7,564; tread Ø **1.3652 / 1.3657 / 1.3654 / 1.3652**; Ø(z) 1.3672 / 1.3674 / 1.3673 / 1.3673; width 0.7314 / 0.7325 / 0.7318 / 0.7315 (`TYRES.md:16-19`) | raw PSKX: `Wheel_Front_Left/Right_Vis`, `Wheel_Rear_Left/Right_Vis` vertex sets (6,485 / 6,490 / 7,432 / 7,440 verts) — every figure matches to the printed 4th decimal. |
| shoulder Ø **1.3711 / 1.3714 / 1.3712 / 1.3711**; "5.5 mm" bulge (`:17`, `:63-66`) | same runs, max radial about each corner's `hub_true`: 0.68555 / 0.6857 / 0.6856 / 0.68555 → Ø 1.3711 / 1.3714 / 1.3712 / 1.3711; 1.3711 − 1.3652 = 5.9 mm (doc: 5.5 mm from 1.3711 − 1.3656 average — the stated 5.5 is within 0.4 mm of the per-corner figure). |
| station radius 0.6829 / 0.6826 / 0.6826 / 0.6827 and tread bottom − ground +0.0021 / +0.0018 / 0.0000 / +0.0001 (`:16-19`) | `Working/TrueScale/stations.json` `corners.*.radius` and `ground` 0.02; mesh y-min 0.0221 / 0.0218 / 0.0200 / 0.0201 → the four gaps as printed. |
| `Disc` y **1.427** (0.070…1.497), x 1.026 (−1.551…−0.525), z 1.270, Ø1.596; 11,543 verts (`:42`, `:45`) | `Wheel_Frnt_Left_Disc`: 13,868 faces, 11,543 verts, y[0.0699,1.4967] = 1.4268, x[−1.5507,−0.5249] = 1.0257, z = 1.2704, max radial Ø 1.5962. |
| rim **Ø1.0254**, `Fan` 32 faces (`:29`) | `Wheel_Frnt_Left_Fan`: 32 faces, max radial about the hub 0.5127 → Ø1.0254 (its own y/z extent is 1.0096 — see issue 8). |
| `SVehicleWheel.WheelRadius` **0.640** (`:85`) | `CHAIN.json` `SVehicleWheel.WheelRadius` value 64.0 cm (×0.01 = 0.640) — value right, cited file wrong (issue 3). |
| tyre Ø = 2 × physics radius (`:55`) | `stations.json` radii ×2 = 1.3658 / 1.3652 / 1.3652 / 1.3654 vs tread 1.3652 / 1.3657 / 1.3654 / 1.3652 → agreement ≤0.6 mm; T-G2's `land_global` 0.68275 / 0.68265 confirmed in `T_ROWS.jsonl`. |

Not verified: the bead-aperture range (Ø1.135–1.360) and the sidewall-ring range (1.322–1.371) at `:27-28` —
the doc gives no selection rule for those vertices; and no game file or dropzone was touched.

## What is sound

- All four tyres really are one mould: 0.5 mm spread in the tread Ø, and the mesh supports "same mould" (the
  front/rear face counts differ only because of the brake/inner detail).
- The three-numbers table (`:52-59`) explains 1.366, 1.40 and 1.42 correctly; `git log -S "1.42 m"` really
  returns only `7a0a07d`, and no TrueScale or T doc measures 1.42.
- D-1 is filled with the measurement and the decision follows from it: the bulge is 5.5–5.9 mm, so the 34 mm
  gap to 1.40 is not in the mesh; nothing was rescaled (R1/R2 respected).
- The docstring was corrected and the README row exists (`Research/BatmobileGrab/README.md:31`).
