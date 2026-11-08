# T-CAM2 — corrected row, with the bytes behind it

**Verdict: the numbers are right, the clause is wrong.** The row ships `FOV [55,63]` v and
every byte that produces it agrees: 85 h → 54.54 v and 95 h → 63.09 v, rounded to
55/63, and those two floats sit in the built tune. The two clauses do not survive their own
arithmetic: folding the +10 in gives 95+10 = 105 h = **72.49 v**, not 68, and the
"95 boost is a gap" claim is refuted by the 63 the same cell ships, because 63 *is* 95 h.
The one unrepresented state is boost **at** speed (105 h = 72.49 v), not boost.

This file is a proposal. `T6_HUD_CAMERA.md:127` was **not** edited.

## 1. The numbers hold — 85 h and 95 h at 16:9 are exactly 55 and 63

The conversion the row names in its transform column, applied to its own inputs:

| horizontal (BmAK, `CAMERA.json`) | 16:9 vertical | shipped |
|---|---:|---:|
| 85 `DrivingCamFOV1` | 54.54 | 55 |
| 95 `BoostingCamFOV1` | 63.09 | 63 |
| 105 = 95 + 10 `DrivingCamMaxExtraFOV1` | 72.49 | — |
| 100 (for reference) | 67.67 | — |

Both shipped values are inside 0.5° of their source: 55 is 0.46° above
54.54, 63 is 0.09° below 63.09; the band is rounded inward by
under half a degree. Back-converted, 55 v = 85.57 h and 63 v = 94.90 h,
i.e. the pair is the 85/95 pair and nothing else.

The bytes are in three places and they agree:

* `Research/BatmobileGrab/CAMERA.json` — `"DrivingCamFOV1": 85.0` at byte
  241 (line 9),
  `"BoostingCamFOV1": 95.0` at byte 268 (line
  10), `"DrivingCamMaxExtraFOV1": 10.0` at byte
  296 (line 11). Those are the
  decoded `R3rdPersonCamera` values; `bmak_camera.py --check` re-reads all 33 from `BmGame.upk`.
* `Working/Audio/jc3cam/editor/entities/jc_cameras/vehicle_cameras/car_base.ctunec` (the donor tune the row replaces) — the `FOV` pair is the row's "now"
  column: offset 324 = `00 00 f0 41` = 30.0,
  offset 328 = `00 00 5c 42` = 55.0. That is
  "30…55° v", verbatim.
* `Builds/test-091/aaf/editor/entities/jc_cameras/vehicle_cameras/bat_base.ctunec` (test-091, the build the row records) — offset 324 =
  `00 00 5c 42` = 55.0, offset 328 =
  `00 00 7c 42` = 63.0. `00 00 d8 42` at
  320 = 108.0 km/h is the speed
  top T-CAM3 pairs with it. `Working/Camera/CAM_TUNE.json` records both edits (`FOV[0]` at
  line 51, `FOV[1]` at line 61, readback
  55.0 / 63.0).

## 2. The clause does not — 68 is not the 16:9 image of any of these values

The clause is inherited from `Research/BatmobileGrab/CAMERA.md`, line
111: "**85 h → 54.5 v**, **95 h → 63.1 v**, and **95+10 h → 68.4 v**".
Its first two terms are the row's numbers (correct); the third does not follow from its own
formula:

```
95 + 10 = 105 h at 16:9  ->  72.49 v     <- the formula's answer
100 h                    ->  67.67 v     <- 68 is this, at 16:9
 95 h at 16:9            ->  63.09 v      <- the shipped 63
 95 h at 16:10           ->  68.59 v     <- where 68.4 comes from
```

So "68" is either ~100 h at 16:9 (67.67) or 95 h on a 16:10 screen
(68.59) - a stray aspect ratio, not the +10 bonus. A reader who folds the +10 in
on the strength of that note targets 68 and lands **4.5° narrow**; the 16:9
number is 72.49.

The second half fails differently. "95 boost is a gap" says a state has no JC3 member, yet the
same cell ships its value: 63 is 95 h at 16:9, and 63 is what the built tune carries. The
boost FOV is expressed, so there is no boost gap. `CAMERA.md` line 249 gives
the reason a *second* value would be hard - "JC3's `FOV` is a min/max pair over speed, not a
per-state value" - and the ADF agrees: `FOV[0]`/`FOV[1]` at 324/328 are bounded by
`FOVVelocityRange` at 316/320. That argument rules out a *fourth* step
(boost at speed), which is the real gap; it cannot also rule out the boost value, because the
row already spends its top of band on it.

## 3. Why 63 is safe under either attribution

`DrivingCamMaxExtraFOV` is added to the driving FOV, and 85 + 10 = 95 = the boost FOV.
The two readings of the top of the band therefore coincide *numerically*:

| reading | value | 16:9 vertical |
|---|---:|---:|
| normal drive + the 10° speed bonus | 85 + 10 = 95 h | 63.09 |
| boost | 95 h | 63.09 |
| boost + the 10° speed bonus | 95 + 10 = 105 h | 72.49 |

The shipped 63 is right whichever of the first two the tune was aiming at; only the third is
missing. That is why the row can drop "95 boost is a gap" without moving a single byte - the
build is correct and stays untouched.

## 4. Corrected row (paste-ready, one line, 9 columns)

```
| T-CAM2 | `DrivingCamFOV` 85 **h**, `BoostingCamFOV` 95 **h**, `MaxExtraFOV` 10 **h** | `FOV [30,55]` over `FOVVelocityRange [5,50]` | UE3 horizontal → JC3 vertical (16:9): 85 h → 54.54 v, 95 h → 63.09 v | 30…55° v | `FOV [55,63]` v = rest 55 (85 h) → top 63 (95 h); 95 = 85 + 10, so 63 is the boost value **and** the +10 bonus at once — the only state one JC3 band cannot express is boost **at** speed, 95 + 10 = 105 h = **72.49** v (not 68) | derived | wide chase, no fisheye |
```

What changed, cell by cell:

| cell | before | after | why |
|---|---|---|---|
| BmAK source | `MaxExtraFOV` 10 | `MaxExtraFOV` 10 **h** | same unit as the two FOVs it is added to (`CAMERA.md`, line 107) |
| transform | "UE3 horizontal → JC3 vertical (16:9)" | same, plus both conversions | the two numbers are now checkable in the cell |
| proposed | "`FOV [55,63]` v; 68 only if the +10 speed bonus is folded in; **95 boost is a gap**" | "`FOV [55,63]` v = rest 55 (85 h) → top 63 (95 h); 95 = 85 + 10, so 63 is the boost value **and** the +10 bonus at once — the only state one JC3 band cannot express is boost **at** speed, 95 + 10 = 105 h = **72.49** v (not 68)" | drops the refuted 68 and the false boost gap; names the real gap |
| conf | `decoded` | `derived` | the value is a unit conversion plus a 0.5° inward rounding, not a decoded number (`review-CAM-1.md` §5, suggested fix 4). This is the one cell that is not a contradiction fix - drop it if the operator wants only the clause corrected |

Nothing else in the row changes: the JC3 target (`FOV`/`FOVVelocityRange`), the "now" column
(30…55 v, the donor bytes above), the verify cell and T-CAM3's 108 km/h are all untouched.

## 5. What this proposal does not touch

* `T6_HUD_CAMERA.md` — the row still reads exactly as quoted in §6; applying the change is the
  operator's edit.
* `Builds/test-091` and the tune — the FOV bytes are already right; no rebuild.
* `Research/BatmobileGrab/CAMERA.md` — the 68.4 sentence is still there (that file is another
  task's input). If this proposal is accepted, that line should carry the same correction, or
  the row will re-inherit it.
* The A15 camera drive — still pending, and this does not substitute for it: nothing here was
  observed in a game (test ban).

## 6. The row as it stands today

`T6_HUD_CAMERA.md`, line 127:

```
| T-CAM2 | `DrivingCamFOV` 85 **h**, `BoostingCamFOV` 95 **h**, `MaxExtraFOV` 10 | `FOV [30,55]` over `FOVVelocityRange [5,50]` | UE3 horizontal → JC3 vertical (16:9) | 30…55° v | `FOV [55,63]` v; 68 only if the +10 speed bonus is folded in; **95 boost is a gap** | decoded | wide chase, no fisheye |
```

`--check` asserts that line is unchanged, so a later edit of the row fails this tool instead of
silently rotating the proposal.

## 7. UNKNOWNs

* **Which of the two coincident readings the tune was aiming at.** 85 + 10 = 95 = the boost
  value, and the ADF carries one `FOV` pair with no per-state attribution; the number is the
  same either way, so nothing is guessed here - the row simply stops claiming a distinction
  the file does not make.
* **Whether JC3 recomputes the vertical FOV from the screen aspect at runtime.** The 55/63 are
  correct for 16:9 (`CAMERA.md` §2a's own scope). A 21:9 screen would widen the horizontal
  view; no file read here reports JC3's behaviour, and no game was run (test ban).
* **Whether 105 h should ever be built.** If the boost-at-speed state matters, it needs a
  second carrier (a per-state camera), which no byte here supplies - recorded as a gap, not
  filled.

## 8. Checks

`python Tools/scripts/t_cam2_proposal.py --check` re-reads every byte quoted above and
recomputes every number, including the 16:10 reconstruction of 68.4 and the equality
85 + 10 = 95. It also regenerates this file and requires it to match.
