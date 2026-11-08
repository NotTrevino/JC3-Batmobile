# G1-18 · Tyre diameter reconciliation — assumption challenge

Scope: `GRAB_BACKLOG.md` §0.5 (R1–R14), card **G1-18** (line 517), its §12 row (line 1286), the
D-1 row (line 1257), `MODLOG.md` §"G1-18 · Tyre diameter — done" (8529), §"G1-18 rework —
done" (15549), and the card's own outputs `Research/BatmobileGrab/TYRES.md` +
`Tools/scripts/bmak_tyres.py`, against `Working/TrueScale/stations.json`,
`Working/Translation/T_ROWS.jsonl` (T-G2/T-G6), `Research/BatmobileGrab/CHAIN.json`,
`Working/Movement/lore_batmobile.json`, `Tools/scripts/bat_assemble.py` and the PSKX exports.

Read-only apart from this file. No game launched, nothing written to `D:/Games` or any install,
no commit. Quoted output is verbatim from commands run in this session.

---

## VERDICT

The tyre *numbers* are right and reproducible — `--check` passes today, and the 1.366 figure has a
genuine external anchor in the decoded `land_global.*_wheels.radius`. But two of the page's three
"verification" claims are circular, and one is a file defect the page reports as a property of the
data:

* **The "≤ 0.6 mm" agreement between tread Ø and `stations.json` `radius` is a comparison of a
  quantity with itself.** `bat_assemble.py` computes `radius = (tyre bbox y extent)/2` from the
  same `Wheel_*_Vis` bone that `bmak_tyres.py` measures, and `ground = min(hub_y − radius)`, then
  offsets the car so that minimum is 0.02. Both invariants are therefore tautologies.
* **`stations.json`'s per-corner `radius` and `tyre_width` are transposed L↔R.** Every corner's
  station value matches the *opposite* corner's mesh measurement to ≤ 0.04 mm, while differing
  from its own corner by up to 0.30 mm. The file also lacks the `mapping` and `tyre_bone` keys
  that the current `bat_assemble.py` writes, so it is a stale snapshot. `TYRES.md` reports the
  symptom ("station `tyre_width` is mirrored L↔R") as a caveat about the data; it is a defect in
  the record the card calls the physics source.
* **"Front/rear are not different parts" is contradicted by the page's own table**: the rear tyre
  carries 7,564 faces against the front's 6,700 (13 % more geometry). They are the same *size*
  (within 0.5 mm), not the same part.

Everything else holds, including what the rework fixed: 1.42 has no carrier, T-G2 carries no rear
figure, 1.369 appears nowhere except the generator's own tamper guard, and the fleet check I ran
on the other two skins shows the same tyre mould everywhere.

| # | assumption | verdict |
|---|---|---|
| A1 | 1.42 has no source; what it measured is UNKNOWN | HOLDS |
| A2 | tread Ø = 2 × `stations.json` `radius` within 0.6 mm, as verification | **BROKEN** (circular + transposed corners) |
| A3 | "the tread sits on the ground plane" | **BROKEN as evidence** (ground is defined from the tyre) |
| A4 | 1.366 is 2 × the decoded physics radius | HOLDS (anchored on `land_global` 0.68275/0.68265) |
| A5 | "all four tyres are the same mould … front/rear are not different parts" | WEAK (same size, different parts) |
| A6 | the shoulder bulge is 5.7–5.9 mm | HOLDS (0.1–0.2 mm robust to hub choice) |
| A7 | "rim Ø 1.0254" | WEAK (that is the hubcap's max radial, not a rim) |
| A8 | 1.40 is "the lore reference" from `lore_batmobile.json` | WEAK (that file has no tyre value at all) |
| A9 | T-G2 has no rear figure; no file contains 1.369 | HOLDS |
| A10 | `SVehicleWheel.WheelRadius` = 0.640 at `CHAIN.json` offset 568 | HOLDS (16 rows, all 64.0) |
| A11 | the frame and units used (x axle, y up, z length, scale 0.01, offset) | HOLDS |
| A12 | "Disc sits 5.0 cm above the ground, 10.9 cm above the crown" | HOLDS (given the datum, which is the right physical datum) |
| A13 | `--check` proves the measurement | WEAK (it re-derives, but two of its three invariants are A2/A3) |
| A14 | only V2 was measured — "one table" for the car | HOLDS once extended: MK2 and Joker tyres are the same to 0.5 mm |

---

## A1 — 1.42 has no source — HOLDS

**Claim.** "`git log -S "1.42 m"` finds only the initial commit (`7a0a07d`), and no file in the
repo measures it (no 0.71 radius anywhere, nothing in the TrueScale or T docs)."

**Test.**

```
$ git log --oneline | head -3
be407e4 Fix translation completion denominator and start first translation batch
7a0a07d Initial commit: JC3 Batmobile research and BmAK grab ledger
count: 2
$ git log -S "1.42 m" --oneline
7a0a07d Initial commit: JC3 Batmobile research and BmAK grab ledger
```

and the current docstring no longer carries it:

```
$ grep -c "1.42" Tools/scripts/bat_assemble.py
0
$ grep -n "tyre Ø" Tools/scripts/bat_assemble.py
9:   (tyre Ø 1.366 m tread-to-tread, measured from the …
```

The `git log -S` half of the evidence is near-vacuous in a two-commit repository — it could not
have found anything else — but the working-tree grep is the real proof, and the page's replacement
explanation (the `Disc` bone's vertical extent, 1.4268 m) is measured on disk.

**Result: HOLDS**, with the cited git evidence weaker than its presentation suggests.

## A2 — "Tread Ø = 2 × `stations.json` radius within 0.6 mm" — BROKEN

**Claim** (`TYRES.md` §1, and invariant `|dy − 2·station_r| ≤ 0.0015` in `bmak_tyres.py`):
"Each tread Ø is 2 × the corner's `stations.json` `radius` to ≤ 0.6 mm … the mesh agrees with
stations to ≤ 2 mm", used to support "1.366 is tread-to-tread *and* physics radius ×2 — the same
figure by design".

**Test 1 — where `radius` comes from.** `bat_assemble.py` (lines 641–684):

```python
for c in CORNERS:
    bs = [b for b, cc in wheel_of.items() if cc == c and size(b) >= 0.8 * max(...)]
    tb = min(bs, key=lambda b: cl[b][2][2])
    pts = Vw[np.unique(tris[fb == tb])]          # the tyre bone's vertices
    lo, hi = pts.min(0), pts.max(0)
    hubs[c] = ((lo+hi)/2, (hi[1]-lo[1])/2, hi[0]-lo[0], bones[tb][0])
    ...
    "radius": round(float(hubs[c][1]), 4)
```

`radius` **is** the tyre bone's vertical bbox half-extent — the identical quantity `bmak_tyres.py`
prints as `dy/2`. The two cannot disagree; the ≤0.6 mm "agreement" is a comparison of one
measurement with itself (rounded to 4 dp).

**Test 2 — the per-corner residuals, and which corner they belong to.**

```
  f_l  mesh dy=1.3652 r=0.68260 width=0.7314 | station r=0.6829 w=0.7325 | d_r=-0.00030 d_w=-0.00109
  f_r  mesh dy=1.3657 r=0.68286 width=0.7325 | station r=0.6826 w=0.7314 | d_r=+0.00026 d_w=+0.00108
  r_l  mesh dy=1.3654 r=0.68268 width=0.7318 | station r=0.6826 w=0.7315 | d_r=+0.00008 d_w=+0.00029
  r_r  mesh dy=1.3652 r=0.68260 width=0.7315 | station r=0.6827 w=0.7318 | d_r=-0.00010 d_w=-0.00028

  opposite-corner match:
    station f_l: r 0.6829 w 0.7325  vs mesh f_r: r 0.68286 w 0.7325   d_r=-0.00004 d_w=-0.00002
    station f_r: r 0.6826 w 0.7314  vs mesh f_l: r 0.68260 w 0.7314   d_r=+0.00000 d_w=+0.00001
    station r_l: r 0.6826 w 0.7315  vs mesh r_r: r 0.68260 w 0.7315   d_r=+0.00000 d_w=+0.00002
    station r_r: r 0.6827 w 0.7318  vs mesh r_l: r 0.68268 w 0.7318   d_r=-0.00002 d_w=-0.00001
```

All four corners of `stations.json` carry the **opposite side's** `radius` *and* `tyre_width`, to
0.04 mm, while their own corner is off by up to 0.30 mm. That is not a tolerance effect; it is a
transposition. The 1.5 mm invariant is four times wider than the transposition, so it passes.

**Test 3 — the file is stale.** The current writer emits `mapping` and a per-corner `tyre_bone`;
the file on disk has neither:

```
keys: ['scale', 'offset', 'ground', 'hardpoint_x', 'corners', 'body_bbox']
corner keys: ['hub_true', 'hardpoint', 'axle_shift_x', 'radius', 'tyre_width']
has mapping: False | tyre_bone anywhere: False
```

So `stations.json` predates the current `bat_assemble.py` output and was produced by a run whose
side attribution differed. `TYRES.md`'s sentence — "Nothing in `stations.json` records a
`tyre_bone`, so the derivation cannot be traced" — is the symptom of that staleness, not a
property of the design; the generator the card credits *does* write the key.

**Result: BROKEN** as a verification. The number it is meant to check (the tyre Ø) is right; the
check that is supposed to prove it compares the measurement with a 4-dp-rounded copy of itself
taken from a stale file whose sides are swapped, and the card presents the result as independent
agreement.

## A3 — "The tread sits on the ground plane" — BROKEN as evidence

**Claim.** "the tread sits on the ground plane (rear +0.0000, front +0.0021)"; invariant
`-0.001 ≤ gap ≤ 0.004`.

**Test.** The ground plane is *derived from the tyre* in `bat_assemble.py`:

```python
ground = min(h[0][1] - h[1] for h in hubs.values())   # lowest tyre point
offset = np.array([-xc, a.ground - ground, a.center_z - zc])   # a.ground = 0.02
```

so after the offset the lowest tyre vertex is 0.0200 by construction:

```
  ground plane test: ground=0.020, min(y of tyre verts)=0.0200,
  per-corner gaps=[0.0021, 0.0018, 0.0, 0.0001]
```

"Stations radius and the mesh agree to ≤2 mm" is the same statement as A2's, and "the tyre touches
the ground" is definitionally true of the lowest point of a wheel.

**Result: BROKEN as evidence** — but benign as geometry: the lowest point of a tyre *is* the road
contact, so using it as the datum is correct. What is wrong is presenting the identity as a check
that could have failed. (Contrast with A12, where measuring the Disc against that datum *is* a real
measurement, because the Disc could have been anywhere.)

## A4 — 1.366 = 2 × physics radius — HOLDS

**Claim.** "1.366 is tread-to-tread *and* physics radius ×2 — the same figure by design … =
T-G2's `land_global.*_wheels.radius` 0.68275 / 0.68265."

**Test.** The two decoded game values are per-axle, not per-corner, and they bracket the measured
halves:

```
front  2 × 0.68275 = 1.36550   measured vertical span 1.3652 / 1.3657  (Δ 0.3 / 0.2 mm)
rear   2 × 0.68265 = 1.36530   measured vertical span 1.3654 / 1.3652  (Δ 0.1 / 0.1 mm)
```

and the page's own diagnostic of the third number is right: `SVehicleWheel.WheelRadius` 0.640
(→ Ø 1.280) is BmAK's contact simplification inside the 1.365 m visual tyre.

One caveat the page does not draw: the tyre is not circular in the y–z plane. The **vertical** span
is 1.3652–1.3657 and the **longitudinal** span 1.3672–1.3674 — 2 mm larger — which is exactly what
a loaded tyre looks like (flattened at the contact patch). The "tread Ø" headline is the deflected
vertical span; the free diameter reads 1.3672–1.3674. The game radius 0.68275 sits between the two
halves (0.6826 vertical, 0.6836 longitudinal), so the conclusion is unchanged, but the headline
number is a loaded-tyre measurement, not the mould's diameter.

**Result: HOLDS**, with the loaded-vs-free distinction worth stating.

## A5 — "All four tyres are the same mould … front/rear are not different parts" — WEAK

**Claim** (`TYRES.md` §1): "All four tyres are the same mould to **0.5 mm** (tread Ø
1.3652–1.3657, shoulder Ø 1.3711–1.3714, width 0.7314–0.7325 m)"; MODLOG: "front/rear are not
different parts".

**Test 1 — same page's own table.** The rear tyre carries more geometry than the front:

```
| f_l | 6,700 faces | 6,485 verts |      | r_l | 7,564 faces | 7,432 verts |
| f_r | 6,700 faces | 6,490 verts |      | r_r | 7,564 faces | 7,440 verts |
```

+864 faces (+12.9 %) and +947 verts. The dimensions match to 0.5 mm; the parts do not.

**Test 2 — the other two skins (a fleet check the card does not do).** Measured the same way from
their own PSKX, raw PSK axes (x length / y width / z up), × 0.01:

```
Batmobile_MK2_Skin
  Wheel_Front_Left_Vis   verts=6484  width 0.7315  vertical 1.3652  longitudinal 1.3673
  Wheel_Front_Right_Vis  verts=6495  width 0.7319  vertical 1.3654  longitudinal 1.3674
  Wheel_Rear_Left_Vis    verts=7432  width 0.7318  vertical 1.3654  longitudinal 1.3673
  Wheel_Rear_Right_Vis   verts=7440  width 0.7315  vertical 1.3652  longitudinal 1.3673

Batmobile_Jokerfied_Skin
  Wheel_Front_Left_Vis   verts=6485  width 0.7315  vertical 1.3652  longitudinal 1.3672
  Wheel_Front_Right_Vis  verts=6490  width 0.7324  vertical 1.3657  longitudinal 1.3674
  Wheel_Rear_Left_Vis    verts=6484  width 0.7318  vertical 1.3654  longitudinal 1.3672
  Wheel_Rear_Right_Vis   verts=6489  width 0.7315  vertical 1.3652  longitudinal 1.3672
```

Every skin's tyre is within 0.5 mm of `Batmobile_V2`'s — so the *size* claim survives across the
fleet (and note the Jokerfied rear tyre has the front's 6,489 verts, i.e. the rear/front geometry
split is not even consistent between skins).

**Result: WEAK.** The size claim holds for all four corners and all three skins; "not different
parts" is false as written, since the rear tyre is a different mesh with 13 % more faces.

## A6 — The shoulder bulge is 5.7–5.9 mm — HOLDS

**Claim.** "Ø max radial (shoulder)" exceeds the tread Ø by 5.7–5.9 mm; the page's D-1 argument
turns on this being ~6 mm rather than the 34 mm needed for 1.40.

**Test — is the max-radial measure an artefact of the hub choice?** It is computed about the
station hub. Recomputing about each tyre's own bbox centre:

```
    f_l  hub-based Ø 1.3711  tyre-centre Ø 1.3709  hub offset (y,z) +0.0000 -0.0001
    f_r  hub-based Ø 1.3714  tyre-centre Ø 1.3714  hub offset (y,z) +0.0000 +0.0000
    r_l  hub-based Ø 1.3712  tyre-centre Ø 1.3711  hub offset (y,z) +0.0000 -0.0000
    r_r  hub-based Ø 1.3711  tyre-centre Ø 1.3710  hub offset (y,z) +0.0000 -0.0000
```

The hub sits within 0.1 mm of the tyre's own centre and the two measures differ by ≤0.2 mm, so the
5.7–5.9 mm is a real shoulder, not a centring error. It is also self-consistent with the loaded
tyre picture (A4): the shoulder at ~45° is further out than either principal span.

**Result: HOLDS.** This is the one measurement in the page whose robustness I could improve rather
than break.

## A7 — "Rim Ø 1.0254" — WEAK

**Claim.** "Rim (the `Wheel_*_Fan` hubcap, 32 faces) Ø1.0254; … 1.0254 is the measurable rim
figure."

**Test.** The page defines the measure honestly ("the figure quoted as rim Ø is the **max radial
distance from the hub**, 0.5127 → **Ø 1.0254**; the cap is dished, so its own y/z extent is
1.0096 / 1.0095 m"), and the bead aperture / sidewall ring were downgraded to UNKNOWN in the
rework (good R4 discipline). So the number is what it says: a 32-face hubcap's radial extent.

But a rim diameter is the bead seat on the *tyre*, and the page itself says that is UNKNOWN. A
1.0254 m "rim" inside a 1.365 m tyre is a 75 % aspect ratio, and the real AK wheel is a low-profile
sport tyre; whether 1.0254 is the rim or just the visible cap is unresolved. The column is labelled
"rim" in the table and `Rim` in prose while the only measurable object is a hubcap.

**Result: WEAK.** Correctly hedged in the paragraph, misleading in the table label. Under R5 the
member is `Wheel_Frnt_Left_Fan`, not "rim".

## A8 — 1.40 is "the lore reference" — WEAK

**Claim** (card In, and `TYRES.md` §2): 1.40 comes from "4 ft 7 in = 1.397 m wiki estimate,
user-verified against footage with Batman at 188 cm (MODLOG §70)", and the card lists
`Working/Movement/lore_batmobile.json` as an input.

**Test.**

```
$ python (json.dumps of Working/Movement/lore_batmobile.json).lower().count(...)
4 ft 7   occurrences: 0
4'7      occurrences: 0
1397     occurrences: 0
1.397    occurrences: 0
tyre     occurrences: 0
wheel    occurrences: 0
diameter occurrences: 0
```

The file holds `top_speed_kmh`, `power_bhp`, `afterburner_pct`, `zero_to_60_mph_s`, `mass_kg` and
nothing about wheels. The 1.40 value exists only as prose:

```
MODLOG.md:3828: diameter 4 ft 7 in = 1.40 m (wiki estimate, user-verified against footage: Batman 188 cm);
```

The arithmetic is right (4 ft 7 in = 55 in = 1.397 m), and a user-verified wiki estimate is a
legitimate `read`-class source — but it has no data carrier, and the card's In list names a file
that does not contain it. Under R4 this value should be labelled `read (wiki, user-verified)`,
not "the lore reference" as if a dataset backed it.

**Result: WEAK** (value fine, provenance line wrong).

## A9 — T-G2 has no rear figure; 1.369 is nowhere — HOLDS

**Test.** The ledger rows themselves (`Working/Translation/T_ROWS.jsonl`):

```
T-G2 cells: ["T-G2", "tyre Ø 1.366 m (mesh)", "`land_global.front/rear_wheels.radius`",
             "decoded", "0.68275 / 0.68265", "unchanged", "decoded",
             "`rbm` wheel mesh bounds vs `radius`"]
T-G6 cells: ["T-G6", "`SVehicleWheel.WheelRadius` = 64.0", "`land_global.front/rear_wheels.radius`",
             "decoded", "0.68275 / 0.68265 m (mesh)", "**keep** the mesh radius: 0.64 m is BmAK's
             contact-radius simplification inside a 0.683 m visual tyre, …"]
```

No 1.369 and no separate rear diameter, exactly as the rework states. `grep -rl "1\.369"` over
`Research`, `Tools/scripts`, `Working/Translation` hits one file only — `bmak_tyres.py` line 517,
where it is the tamper guard `for bad in ("1.369", "4.8 cm"):` that keeps the removed claims from
reappearing.

Note T-G2's own evidence cell — "`rbm` wheel mesh bounds vs `radius`" — says the decoded radius was
itself checked against mesh bounds, so the "decoded" claim rests on a mesh-derived cross-check.
That does not weaken A4 (the value is a game field), but it means the mesh-vs-radius agreement is
circular in T-1 as well as in this card.

**Result: HOLDS.**

## A10 — `SVehicleWheel.WheelRadius` = 0.640 at offset 568 — HOLDS

```
SVehicleWheel.WheelRadius rows: 16 rows, every value 64.0, offset 568, e.g.
  /fields/SVehicleWheel/Playable_Batmobile_SFunhouse….WheelFL[1] → 568, 64.0
```

All four wheels × four packages, all 64.0 cm. The page's 0.640 → Ø 1.280 is the right reading, and
the "not imported" decision is consistent with T-G6.

**Result: HOLDS.**

## A11 — Frame and units — HOLDS

The page states x = axle (left = −x), y = vertical, z = longitudinal, ground y = 0.02, and the ONE
transform `to_jc3_rot(p) × 0.01 + offset` with `offset [-4.77e-07, 0.0222314, 0.1542974]` from
`stations.json`, matching `bat_assemble.py` (the same array, byte for byte) and the G1-11 finding
(recomputed offset differs by 1.3e-05 m). The measured spans are consistent with the car's
`body_bbox` and with `MESHES.md` (`Batmobile_V2` 702.560 × 349.530 × 234.185 cm → 0.01 scale).

One thing the page does not say: `ground = 0.02` is not a JC3 or BmAK constant, it is the datum
chosen in `bat_assemble.py` (`a.ground`) and enforced by the offset. That is fine as long as it is
called a datum, which §1 does ("ground is y = 0.02").

**Result: HOLDS.**

## A12 — Disc clearance — HOLDS

**Claim.** "The front-left Disc's lowest vertex is y 0.0699 — **5.0 cm above the ground plane y =
0.02** — and its top is 10.9 cm above the tyre crown (y 1.3873); its radial envelope reaches
Ø 1.5962."

**Test.** These are measurements of a *different* bone against a datum that the tyre defines, which
is the legitimate use of that datum — the Disc could have been anywhere (including below the tyre),
and in fact 394 of its 11,543 vertices are outside the tyre's max radial and 338 outside it
vertically. The two counts are printed with their tests named, and the earlier conflation (338
printed under "beyond the tyre's radius") is gone.

**Result: HOLDS.**

## A13 — `--check` proves the measurement — WEAK

**Test.** It runs and passes:

```
$ python Tools/scripts/bmak_tyres.py --check
OK: 4 tyres; tread Ø 1.3652-1.3657, shoulder Ø 1.3711-1.3714, width 0.7314-0.7325;
    station radius vs mesh <= 0.6 mm
OK: TYRES.md matches the re-derived render (169 lines)
EXIT=0
```

The render comparison is a real anti-drift gate (and the rework's tamper test demonstrates it
fails on a one-digit edit). But of the four invariants, one (`tread spread ≤ 0.6 mm`) is a
self-consistency check over four copies of one mould, two (station radius, ground) are A2/A3
tautologies, and only `faces > 0` is independent. So `--check` proves the page matches its own
derivation; it does not prove the derivation is anchored, and a change to `stations.json` (rather
than to the mesh) would move the reference with it.

**Result: WEAK** — the gate is right for what it claims (`TYRES.md` is generated, never hand
edited); it should not be read as independent validation of the diameters.

## A14 — "One table" from one mesh — HOLDS once extended

**Claim.** The card measures `Batmobile_V2` only, in a mod that ships `Batmobile_MK2_Skin` and
`Batmobile_Jokerfied_Skin` (MESHES.md: 12 mesh/variant rows over 4 packages).

**Test.** A5's fleet measurement: every `Wheel_*_Vis` in all three car skins has vertical Ø
1.3652–1.3657 and width 0.7315–0.7325. Same mould, same size, three packages.

**Result: HOLDS** — the card did not test the other skins, but the claim survives the test. Worth
adding one line to `TYRES.md` so the next reader does not have to re-run it.

---

## Cross-cutting notes

* **R11 is now satisfied** — `TYRES.md` is generated and `--check` compares the page with a fresh
  render (169 lines). That was the main review finding, and it is genuinely fixed.
* **Smallest fixes**, in value order:
  1. Regenerate `stations.json` with the current `bat_assemble.py` (it would gain `mapping` and
     `tyre_bone`) and see whether the L↔R transposition persists — if it does, the bug is in the
     corner→bone selection, not in file age. Until then the "≤0.6 mm" line should be labelled as
     an internal consistency check, not an agreement with an independent source.
  2. Relabel `radius`/`ground` invariants in `--check` as "re-derivation" rather than
     "station vs mesh", and add one truly independent invariant: `|dy/2 − 0.68275| ≤ 1.5 mm` for
     the front pair and `|dy/2 − 0.68265| ≤ 1.5 mm` for the rear pair, against the decoded
     `land_global` values that are *not* derived from the mesh.
  3. Change "front/rear are not different parts" to "same size, different mesh (6,700 vs 7,564
     faces)".
  4. Move the 1.40 provenance from `lore_batmobile.json` (which has no wheel value) to the MODLOG
     §70 prose, and label it `read (wiki, user-verified)`.
* **Not decidable here:** whether the transposed `radius`/`tyre_width` came from a stale run or a
  live bug in `bat_assemble.py`'s corner selection (needs a full assembly run), and what the
  initial docstring's 1.42 measured — the page's UNKNOWN is the correct answer, and the Disc's
  1.4268 m vertical extent is the nearest quantity that could have produced it.
