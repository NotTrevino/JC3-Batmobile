# Assumption challenge — feature **CAM-1 · chase camera at the decoded composition**

Read-only pass over a finished item. What was read:

- `GRAB_BACKLOG.md` §0.5 rules R1–R14 (lines 63–76), §1.10 *Lights, effects, camera, HUD* (line 234)
  and its CAM-1 row (line 244), the tracker row (line 1365), the Q-2 gate list (line 1198);
- the MODLOG blocks that are CAM-1's record — `## G3b` (line 6840), `## G3c` (6877), `## G3d`
  (6913), `## G3e` (6954) and `## Batch F` (7663);
- the artifacts: `Working/Camera/CAM_TUNE.json`, `Working/Camera/CAM_REF.md`,
  `Working/Camera/bat_base_dump.txt` (existence/headers), the shipped
  `Builds/test-091/…/bat_base.ctunec`, `Builds/test-091/…_civilian_01.epe`,
  `Builds/test-091/…_civilian_01.ee.toc`, `Builds/test-086/…/bat_base.ctunec`,
  `Working/Translation/T6_HUD_CAMERA.md` (T-CAM1…T-CAM13, §3, §4),
  `Research/BatmobileGrab/CAMERA.md` §2/§2b, `Working/Appearance/build_parts/parts_manifest.json`.

**CAM-1 has no card.** `grep -c "^#### " GRAB_BACKLOG.md` = **86**, and none of the 86 is a `CAM-1`
card; CAM-1 exists only as a §1.10 requirement row plus the tracker row. So there is no `In`/`Do`/
`Out`/`Done` block and no acceptance clause — "done" can only mean "the file is in the build". That is
finding **A15**.

Constraints honoured: no game launched (R6), nothing written to `D:/Games` (it was not read at all,
so the live dropzone is out of scope here), nothing committed, no secret read, **and no repository
file modified except this document** (all tests were `python -c`, `grep`, `sed`, `ls`).

---

## VERDICT summary

**The shipped artifact is the one the rows describe, and its two headline values are genuinely
decoded.** `Builds/test-091/…/bat_base.ctunec` carries `CameraPosition [0, 1.30, 7.00]`,
`LookAtPoint [0, 1.55, 0]`, `FOV 55 … 63`, `FOVVelocityRange [5, 108]`, roll `0.38`,
`CollisionStartPoint [0, 1.6, 0]` — read straight from the bytes — and 7.00/1.30 is the output of a
disassembled formula (`Loc = anchor − forward·400 + Rot·Sit` with sit −300,0,−25 cm and pivot 155 cm),
not a fit. **What does not survive is the evidence chain around it:** the only drive was a different,
withdrawn file; the one quantitative "the FOV is live" measurement is confounded and numerically
agrees with the *new* values rather than the ones that were installed; the optional "+10 → 68" figure
is refuted by its own formula; and the fleet/variant carriers CAM-1 is credited with were never built.

| # | assumption (stated or silent) | verdict |
|---|---|---|
| A1 | "7.00 m back, 1.30 m up" is the decoded composition, not a fit | **HOLDS** |
| A2 | the JC3 frame: `CameraPosition` y is metres above a ground-level origin | **WEAK** |
| A3 | "FOV 55 … 63" = BmAK 85/95 horizontal at 16:9 | **HOLDS** |
| A4 | "68 only if the +10 speed bonus is folded in" (and `CAMERA.md`'s "95+10 h → 68.4 v") | **BROKEN** |
| A5 | "the 2.27 m body at ~3.5 m reads 36 % of a 55° view, i.e. ~86° horizontal" | **WEAK** |
| A6 | "the tune is live" — the driven evidence transfers to the shipped values | **WEAK** |
| A7 | the 36 %→30 % frame count is a measurement of FOV | **WEAK** (quantitative: it matches 55→63, not the 55→85 that was installed) |
| A8 | G3b's `[0,2.4,7.0]` / `[0,1.7,0]` / `55…85` describe the current output | **WEAK** |
| A9 | the `.epe` ref is a 2-byte rename with exactly one occurrence | **HOLDS** |
| A10 | the tune is registered at `(16498168, 5968)`, internal, and the shared tune stays external | **HOLDS** |
| A11 | "every other car keeps `car_base.ctunec`" | **WEAK** (fleet claim; one `.epe` in the build) |
| A12 | "a second per-entity `.ctune` per variant is the carrier" | **WEAK** ("no carrier" searched in one place) |
| A13 | `CollisionStartPoint 1.6` from the body-height ratio | **WEAK** |
| A14 | BmAK's *boost state* maps onto JC3's FOV ramp at *108 km/h* | **WEAK** (admitted gap, then filled) |
| A15 | "done" | **WEAK** (no card, no clause; drive deferred to A15) |

Net: **4 hold (A1, A3, A9, A10), 10 weak, 1 broken (A4)**. The one broken item is a derived figure in
a note, not in the build. The weakness pattern is consistent: the *values* were decoded, the
*validation* was not — and the record sometimes presents the validation of a withdrawn file as if it
covered the shipped one.

---

## A1 · "7.00 m back / 1.30 m up" is decoded

**Claim.** §1.10: *"Chase camera at the decoded composition (7.00 m back, 1.30 m up, FOV 55…63)"*.
T-CAM5 "now" cell: *"**`CameraPosition [0,1.30,7.00]`**, `LookAtPoint [0,1.55,0]`"*, confidence
`decoded`. T6 §4: *"the new 7.00 m and 1.30 m come from the decoded composition instead (`Loc =
anchor − forward·400 + Rot·Sit`, sit −300,0,−25 cm, pivot 155 cm)"*.

**Test 1 — the two operands are decoded members, and the arithmetic closes.** `CAMERA.md` §2b prints
the struct map out of `SetFreeCameraConfig`:

```
cfg+0x00 -> StateFreeCameraSitOffsetMin   [-300, 0, -25]
cfg+0x34 -> CameraPivotOffset             [0, 0, 155]
cfg+0x54/0x58 -> Min/MaxFreeCameraDistance 400 / 400
```

and the composition from `UpdateCameraPosition`:

```
Loc = anchor - RotToVector(Rotator) * distance + RotateVector(Rotator, Sit)
| level (rest), t = 0.00 | sit −300, 0, −25 | boom 400 | camera vs pivot −700, 0, −25 |
```

```
back   = 400 cm boom + 300 cm sit-x  = 700 cm = 7.00 m
height = 155 cm pivot − 25 cm sit-z  = 130 cm = 1.30 m
```

**Test 2 — the built file carries exactly that.** Values read from the shipped bytes (`<f` at the
offsets `CAM_TUNE.json` records):

```
test-091  pos [1.3, 7.0]  look 1.55  fov 55.0 63.0  fovrng 108.0  roll 0.38  colstart 1.6
```

and the report's own re-read agrees (`readback: 1.2999999523162842`, `7.0`,
`1.5499999523162842`, `55.0`, `63.0`).

**Test 3 — the old 7.0 m coincidence is disclosed as a method change, not a lucky value.**
`CAMERA.md` §2a: *"The previous candidate's 7.0 m was a body-length ratio, not this data — although
the native answer turns out to give the same 7.0 m at rest, for a different reason (400 boom + 300
sit), so the withdrawal stands as a method correction, not a value one."* That is the honest form of
the claim and it is what the record says.

**Verdict: HOLDS** (with the frame caveat in A2). Nothing in this pass could move either number: it is
arithmetic on decoded members, and the artifact matches.

---

## A2 · the JC3 frame (metres, origin at the ground)

**Claim (silent).** Every built value is in metres *above the car's origin*, so a BmAK height of
1.55 m above the ground is written as JC3 `1.55`, and `1.30` is a height rather than an offset from
some pivot.

**Test 1 — the donor.** `car_base.ctune`: `CameraPosition [0,2,5]`, `LookAtPoint [0,1.25,0]` for a
small sports car. Those are only sensible as metres with y measured up from the ground (2 m camera,
1.25 m aim). So metres are established **for the donor**, by plausibility, not by a decode — the
`.ctunec` header carries no unit string and no scale field was found to prove it.

**Test 2 — the mod's own origin.** From `Working/Appearance/build_parts/parts_manifest.json`:

```
"body_bbox_m": [[-1.748, 0.091, -3.42], [1.747, 2.362, 3.605]]
```

so the body's underside sits **9.1 cm above y = 0**, i.e. the JC3 origin is at the ground plane (the
tyres, radius 0.6826 m, put the contact at 0.000). The height scale also cross-checks: 2.362 − 0.091
= **2.271 m**, which is the body height the collision row uses. So a 1.30 m camera height is 1.30 m
above the ground, and 1.55 m is at the pivot — consistent.

**Test 3 — what would break it.** If JC3 measured `CameraPosition.y` from the car's *pivot* (which
for the tank is `RotationPoint [0,0,0]` and for the car `[0,1.5,0]`), then 1.30 would be 1.30 m above
a 1.5 m pivot — 2.8 m off the ground, and the companion `CollisionStartPoint 1.6` would be *below* the
camera again. The donor's own pair (`LookAtPoint 1.25` under a `RotationPoint 1.5`) suggests the y's
are absolute-above-ground, since an aim 0.25 m *below* its own pivot would be odd. Suggestion, not
proof: one donor cannot separate the two conventions.

**Verdict: WEAK.** The numbers are right to within the evidence (≤ 9 cm of origin slack, 7 % of the
1.30 m height); the *convention* is inherited from a sample of one car and is not stated in the row
that claims `decoded`.

---

## A3 · "FOV 55 … 63" from 85/95 horizontal at 16:9

**Claim.** T-CAM2: *"`DrivingCamFOV` 85 **h**, `BoostingCamFOV` 95 **h** … UE3 horizontal → JC3
vertical (16:9)"*, proposed *"`FOV [55,63]` v"*, confidence `decoded`. Built: `FOV[0] 30 → 55`,
`FOV[1] 55 → 63`.

**Test 1 — the formula.** `v = 2·atan(tan(h/2)/(16/9))`:

```
85 h -> 54.54    95 h -> 63.09
```

55 and 63 are those values rounded outward by ≤ 0.5°. The claim closes.

**Test 2 — independent corroboration from the take (the only on-disk check of "85 is horizontal").**
If 85/95 had been *vertical*, the test-086 build would have shown a much stronger speed-shrink than
it did. With the body's 3.495 m width at the 7.0 m boom:

```
vFOV 55   (h 85.6)  -> car reads 32.8 % of frame width
vFOV 83.5 (h 115.6) -> 24.3 %
observed take       36 % at 0 km/h, 30 % at 103 km/h
```

The observed end point is nowhere near the "85 is vertical" prediction (24 %); it sits at the
55→63 family (29.7 % at 63 v). So the horizontal-FOV premise is consistent with the recording, not
just with convention.

**Test 3 — the aspect ratio is stamped on the build.** A vertical FOV means the *horizontal* view
varies with the player's screen (16:9 → 85.6°, 21:9 → 108°). That is the intended behaviour of a
vertical-FOV engine and is not a defect, but it does mean "85° horizontal" is only true at 16:9; the
row does say "16:9", so the claim is scoped correctly.

**Verdict: HOLDS.**

---

## A4 · "68 only if the +10 speed bonus is folded in"

**Claim.** T-CAM2: *"`FOV [55,63]` v; **68 only if the +10 speed bonus is folded in**; 95 boost is a
gap"*. `CAMERA.md` §2a: *"The conversion for 16:9 is `v = 2·atan(tan(h/2)/(16/9))`: **85 h → 54.5 v**,
**95 h → 63.1 v**, and **95+10 h → 68.4 v**."* T6 §4 and `CAMERA.md`'s table both repeat "(68 with
the +10)".

**Test — apply the paragraph's own formula to its own inputs.**

```
95 + 10 = 105 h at 16:9  ->  72.49 v        (not 68.4)
100 h                    ->  67.67 v
95 h at 16:10            ->  68.59 v        <- where 68.4/68 actually comes from
95 h at 16:9             ->  63.09 v        <- the shipped value
```

68.4 is not the 16:9 image of any BmAK FOV: it is 95° horizontal at **16:10** (68.59, 0.2° off) or
~100.5° at 16:9. So a reader who folds the +10 in on the strength of this note would target **68** and
land 4.5° narrow; the correct 16:9 number is **72.5**. The same figure is repeated in three places
(T-CAM2, `CAMERA.md` §2a, §2a's table), so the error propagates by quotation.

**Verdict: BROKEN.** A derived number that its own stated derivation refutes. It does not affect the
shipped 55/63 (which uses the un-bonused 85/95), so the build is not wrong — the *note* is, and it is
the note a future tuning pass would read.

---

## A5 · the FOV calibration sentence

**Claim.** `CAMERA.md` §2a: *"the test-086 recording calibrates it: the car's 2.27 m body at ~3.5 m
reads 36 % of a 55° view, which is ~86° horizontal"*.

**Test 1 — the sentence's own inputs.**

```
2.271 m at 3.5 m subtends            35.95°
as a fraction of a 55° vertical view 65.4 %
as a fraction of an 86° horizontal view 41.8 %
```

Neither 36 % nor "of a 55° view" is produced. If 36 % were the horizontal fraction at 3.5 m, the view
would be 35.95 / 0.36 = **99.9° horizontal ≈ 67° vertical**, i.e. the boosted end of the *withdrawn*
build, not 55°.

**Test 2 — the geometry that does produce 36 %.** The car is on a 7 m boom, not 3.5 m, and its body is
3.495 m wide (2.271 m is its *height*, used by the collision row):

```
3.495 m at 7.0 m in a 55 v (85.6 h) view -> 32.8 %
3.495 m at 6.4 m in the same view        -> 35.7 %   <- observed 36 %
```

So the observation is plausible; the *sentence describing it* mixes the body's height with its width
and halves the distance. The conclusion ("~86° horizontal") is right for a different reason than the
one given.

**Verdict: WEAK.** A supporting calibration whose stated inputs do not reproduce its output, in the
same paragraph as A4's wrong figure.

---

## A6 · "the tune is live" → does it transfer to the shipped values?

**Claim.** G3c's heading: *"G3c — CAM-1 packed, installed and driven: **the tune is live** (test-086,
2026-10-22)"*; body: *"The game ran: package loads, Batmobile drivable, no camera-related crash"*,
*"the `CCameraModifier`'s `bat_base.ctunec` is live"*. The tracker row: *"done as Batch F
(test-091)"*.

**Test 1 — the driven bytes are not the shipped bytes.**

```
Builds/test-086/.../bat_base.ctunec   5,968 B  6f5a9cce5a84bde7…   <- driven, withdrawn by G3d
Builds/test-091/.../bat_base.ctunec   5,968 B  c8a088e537a01c6d…   <- shipped
CAM_TUNE.json  output.sha256                 c8a088e537a01c6d…   <- the report describes the shipped file
```

Decoded per field:

```
test-086  pos [2.4, 7.0]  look 1.7   fov 55.0 85.0   roll 0.38  colstart 1.6
test-091  pos [1.3, 7.0]  look 1.55  fov 55.0 63.0   roll 0.38  colstart 1.6
```

**Test 2 — what the drive can and cannot support.** The take shows the black body's width falling
36 % → 33 % → 30 % with speed. A fixed-FOV camera would hold the fraction constant, so *something*
widened with speed: the per-entity tune is being read, and the routing question is closed. That
inference transfers (same path, same `.epe` field, same mechanism). The *values* do not: `1.30`,
`7.00`, `1.55`, `55…63`, `1.6` have never been in a running process.

**Test 3 — is the limitation disclosed?** Yes, twice: G3d (*"test-086 is withdrawn … the values were
wrong"*) and T6 §3 (*"**A15 drive pending**. The old test-086 drive proved the modifier's tune is live
(FOV widened with speed); its values were withdrawn and not reused"*). But the section that is CAM-1's
own evidence carries the words "the tune is live" in its headline, and the tracker says "done", so the
distinction survives only for a reader who reads two other places.

**Verdict: WEAK.** The mechanism claim is true and documented; the unstated step "and therefore the
shipped composition is verified" is false, and the strongest sentence in the record invites it.

---

## A7 · the 36 %→30 % frame count is a measurement of FOV

**Claim.** G3c: *"Counting the black body's width in six frames: **36 % of frame width at 0 km/h, 33 %
at 18–53, 30 % at 74–103**. A fixed 50° `SharedCarCamera` would hold the same fraction; this widens
with speed, so the `CCameraModifier`'s `bat_base.ctunec` is live and the epe's own `FOV` property does
not need raising. The routing question is closed."*

**Test 1 — the observed shrink is a product of two effects.** The tune also carries
`FollowCameraRange [-0.5, 2]`, filled from `DrivingCamMaxExtraTranslation = 50 cm` (T-CAM4:
*"pull-back at speed"*). So the camera moves back as well as widening. Predicted fraction of frame
width for a 3.495 m body, 16:9, at 7.0 m rest / 7.5 m at speed:

```
installed test-086 (55 -> 83.5 v):  32.8 % -> 22.7 %   ratio 1.44
shipped   test-091 (55 -> 62.6 v):  32.8 % -> 27.8 %   ratio 1.18
no FOV change, pull-back only:      32.8 % -> 30.7 %   ratio 1.07
observed:                           36 %   -> 30 %     ratio 1.20
```

The observed 1.20 matches the **55→63** prediction (1.18) and is far from the **55→85** prediction
(1.44) — yet test-086, the build that was installed for that take, carried `FOV[1] = 85`. It is also
well above the pull-back-only floor (1.07), which is what keeps the routing conclusion alive.

**Test 2 — what that means.** Two readings, both bad for the record as written:
(a) the take does not measure the FOV it thinks it measures, so it cannot calibrate a FOV (which is
exactly the use `CAMERA.md` §2a puts it to — A5); or (b) the interpolated endpoint is not
`FOV[1]` — i.e. the FOV the engine applied at 103 km/h was ~62 v even though the file said 85. Either
way the frames are consistent with the *new* values and inconsistent with the *installed* ones, which
is the opposite of what a validation should look like. Six hand-counted frames at 1280×720, with the
car pitching, cannot separate 12 % from 18 %; the numbers are too coarse to carry the conclusion they
are asked to carry.

**Verdict: WEAK.** Routing survives (the shrink exceeds the pull-back-only floor by 13 points); the
*magnitude* claim, and the calibration built on it, do not. No launch is permitted here, so this can
only be settled by A15 measuring FOV and distance separately.

---

## A8 · G3b's narrative numbers

**Claim.** G3b: *"`E:/Modding/_JC3cam_out/bat_base.ctunec` — 5,968 B, `6f5a9cce5a84…`: position
`[0,2.4,7.0]`, look-at `[0,1.7,0]`, FOV `[55,85]` over `[5,108]` km/h, roll 0.38, collision start
`[0,1.6,0]`"*, followed by *"Report: `Working/Camera/CAM_TUNE.json`"*.

**Test 1 — the numbers are right for the sha named.** `6f5a9cce…` is test-086's file, and the bytes
read:

```
pos [2.4, 7.0]  look 1.7  fov 55.0 85.0  fovrng 108.0  roll 0.38  colstart 1.6
```

So the sentence is internally consistent: it describes the first candidate, which later became
test-086 and was withdrawn.

**Test 2 — but the paragraph is not marked as history, and its report has moved on.**
`CAM_TUNE.json` now holds `1.3 / 7.0 / 1.55 / 55 / 63` and `output.sha256 = c8a088e5…` — i.e. the
shipped file — under a `build` string that still reads *"CAM-1 candidate: bat_base.ctunec + donor
.epe ref rename (**not packed, not installed**)"*, which is false of the file it now describes (it was
packed into test-086 and again into test-091). So both directions are stale: the narrative points at a
report whose numbers changed, and the report's own metadata describes an unpacked state.

**Verdict: WEAK.** No false statement, but a reader following the path gets a different file's values,
and the artifact's provenance string no longer matches its contents (R14's "journal everything" wants
the sha, not the path, to be the identity).

---

## A9 · the `.epe` reference

**Claim.** G3b: *"The path is a plain NUL-terminated ASCII string … `car_base.ctune` and
`bat_base.ctune` are both 14 bytes, so the edit is **2 bytes** (`c`→`b`, `r`→`t`) and nothing else
moves."* T6 §4: *"the 2-byte `.epe` ref rename"*.

**Test — count the strings in the shipped `.epe` and read the report's diff record.**

```
Builds/test-091/aaf/.../v0300_car_kensington_sportsmuscle_civilian_01.epe   105,430 B
  car_base.ctune     0
  bat_base.ctune     1
  SharedCarCamera    1

CAM_TUNE.json epe: {old_ref: car_base.ctune, new_ref: bat_base.ctune, offset: 53407,
                    occurrences: 1, bytes_changed: 2, size: 105430, size_same: true,
                    sha256_before: 7385eced…, sha256_after: cf49315a…}
```

One occurrence, renamed in place, size unchanged, and the camera *object* is still the shared
`SharedCarCamera` — i.e. only the modifier's path is per-entity, which is the mechanism claimed.

**Verdict: HOLDS.**

---

## A10 · the `.toc` routing

**Claim.** G3c: *"The new record lands **before** the `.epe` at `(16498168, 5968)`, internal;
`car_base.ctunec` stays external `(0, 5968)`, exactly as the base routes it."*

**Test — read the record bytes in the shipped `.toc`.**

```
Builds/test-091/..._civilian_01.ee.toc   50,643 B
  bat_base.ctunec  at 50489  -> after the name: f8bdfb00 50170000   = offset 16,498,168, size 5,968
  car_base.ctunec  at 36253  -> after the name: 00000000 50170000   = offset 0 (external), size 5,968
```

offset `0xFB BDF8` = 16,498,168 and size `0x1750` = 5,968 — both fields match the claim to the byte,
and the shared tune's external routing is untouched.

**Verdict: HOLDS.**

---

## A11 · "every other car keeps `car_base.ctunec`"

**Claim.** G3b: *"Every other car keeps `car_base.ctunec`; only the Batmobile entity points at
`bat_base.ctunec`."* `CAM_REF.md` §1 repeats it: *"every other car keeps `car_base.ctunec`"*, and §2
adds *"every car `.epe` repeats `car_base`"*.

**Test — census the build, then look for a census on disk.**

```
Builds/test-091/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/
  v0300_car_kensington_sportsmuscle_civilian_01.epe      (1 file, 1 .ee)
```

The build contains **one** vehicle entity. No other car's `.epe` is in the project, so "every other
car" is not testable here at all. The project has a fleet census (`jc3_feature_census.py --write` →
232 entities; `t3_fleet.py --check` → 41 members over 156 vehicles) and neither was run for camera
strings; `FEATURE_CENSUS.json` contains no camera row (`grep -c camera` = 0), and `G2X.md` records
CAM-1's needle as the string `car_base.ctune` with no count. The extracted-tune table (`CAM_REF.md` §2)
does support the *class* story — cars all resolve through `car_base`, the class is chosen by the path —
but that is a table of eight files, not a count over `.epe`s.

**Verdict: WEAK.** True as far as the one donor goes, and plausible for the fleet; the claim is
fleet-wide and the evidence is a sample of one `.epe` plus a note that asserts the rest.

---

## A12 · "a second per-entity `.ctune` per variant is the carrier"

**Claim.** T-CAM10: *"**superseded by T-15** (D-2): no battle-camera member, but a second per-entity
`.ctune` is the carrier (`bat_base.ctune`, Batch F, test-091)"*, confidence `decoded`.

**Test 1 — there is no second variant in the build.** One `.epe`, one `.ee` (A11), and
`bat_base.ctunec` is the *drive* tune: `FOV 55…63`. BmAK's battle FOV is 60 (h) ≈ 34.7 v, winch 60,
anti-personnel 40 — none of those is inside 55…63, and nothing in test-091 selects a mode.

**Test 2 — the "no carrier" half was searched in one place.** The claim that no battle-camera member
exists was tested against the 187-row `GenericVehicleCamera` layout (`CAM_REF.md` §3 lists the tank's
diffs member by member). That is a search of *the camera tune*, not of the entity graph — and the
proposal itself ("a second `.ctune` per variant") implies the real carrier lives in `.epe`/`.vmodc`,
which was not searched for a mode selector. So "no member, but a second file" is: no member *in the
file we decoded*, plus an untested mechanism elsewhere.

**Verdict: WEAK.** The row is labelled `decoded` and reads as a built carrier; it is a hypothesis
whose artefact does not exist. The tracker correctly leaves the battle camera to T-15, so no work is
miscredited — only the confidence label is wrong.

---

## A13 · `CollisionStartPoint 1.6` by body-height ratio

**Claim.** T-CAM13: *"body height 2.271 m vs donor 1.41 m → ×1.61 → 1.0 m → **1.6 m**"*, confidence
`derived`, verify *"no clipping through the taller body"*. Built: `CollisionStartPoint[1] 1.0 → 1.6`.

**Test 1 — the arithmetic.** 2.271 / 1.41 = 1.6106; × 1.0 m = 1.61 → 1.6. Closes.

**Test 2 — the pattern it produces, against the other seven classes.** The member is read by name, so
the question is whether "start height" behaves as a height. The class table (`CAM_REF.md` §2):

```
car        camera y 2.0   collision y 1.0   (below)
bike       camera y 1.5   collision y 2.0   (ABOVE)
medium tank camera y 2.0  collision y 3.4   (ABOVE)
```

So JC3's own tunes put the occlusion origin *above* the camera for the bike and the tank; the built
`1.6` over a `1.30` camera is in family, not an inversion. My first reading of this row ("the donor's
relation is inverted") is refuted by the fleet of tunes — good, that is the point of testing.

**Test 3 — the scaling rule itself.** One pair (donor 1.41 m → 1.0 m) cannot establish linearity. The
other classes do not sit on that line either: the tank's ray is 3.4 m for a 2.34 m hull
(`FLEET.md`), i.e. **3.4×** the car's 1.0 m for a hull only **1.66×** taller (2.34 / 1.41), and the
bike's 2.0 m is more than its own camera height. So the *value* 1.6 is a middle-of-the-road
interpolation and the *rule* ("scale linearly with body height") is an inference from one pair,
which the `derived` label does admit.

**Verdict: WEAK.** Honest class, in-family value, unestablished rule; the verify column ("no clipping")
is untested and would need A15.

---

## A14 · BmAK's boost *state* on JC3's *speed* ramp

**Claim (silent, in the built values).** `FOV [55, 63]` over `[5, 108]` km/h — the 63 is the
*boost* FOV (95 h), placed at the top of a ramp indexed by **speed**, not by the boost button.

**Test — how the two sides index FOV.**

```
BmAK: DrivingCamFOV 85 (normal) / BoostingCamFOV 95 (while boosting), MaxExtraFOV +10 by speed
      -> a STATE selector plus a small speed term
JC3 : FOV [min,max] over FOVVelocityRange [5,50] km/h in the donor, [5,108] in the build
      -> one ramp, purely speed-indexed
```

The row states the mismatch and calls it a gap: *"`BoostingCamFOV` 95 cannot be expressed by a single
JC3 `FOV` range; the table uses the normal 85 and records the boost +10 as a gap"*. But the build then
uses the **boost** value (63) as the ramp's top, so the artifact does express it — as "wide only at
108 km/h". Consequence: in the mod, pressing boost at 40 km/h widens nothing (the ramp is at ~58);
in BmAK it would jump to 95 h. Nobody has compared those two behaviours (A15 is the gate, and its list
is *"distance at rest, FOV stops changing at 108, roll follows the lean, no clipping"* — the boost
response is not in it).

**Verdict: WEAK.** Documented as a gap, then filled by the build without a test; the effect is
behavioural (boost feel), not numeric, so no measurement on disk can settle it.

---

## A15 · "done"

**Claim.** Tracker line 1365: *"CAM-1 | done as Batch F (test-091); A15 in Q-2; battle camera in
T-15"*.

**Test 1 — is there a card?** No. 86 `####` cards, none for CAM-1 (§ header). There is therefore no
`Done` clause to satisfy. The nearest acceptance language in the record is the T-CAM1 verify column
(*"one camera drive"*) and A15 in Q-2 (line 1198: *"A15 camera drive"*).

**Test 2 — has the drive happened?** T6 §3: *"in-game camera | **test-091 installed** (Batch F, 8
values; 13/13 pack + 14/14 verify) — **A15 drive pending**"*. So the build step is done and the
feature is not verified. What *is* verified statically: `bmak_camfile.py check` 8/8 (re-derived from
the written bytes), the `.epe`/`.toc` routing (A9, A10), and the pack/verify counts.

**Test 3 — is "installed" checkable here?** No. It would mean reading the live dropzone; that is
outside this pass (no `D:/Games` access). The build being installed *over test-090* is asserted in
Batch F, and the P0-1 baseline says the dropzone carries test-091, but neither is a measurement I can
repeat without touching `D:/Games`.

**Test 4 — the build and the drive both precede the phase that permits them.** R6: *"**No game launch
before phase V exits.** No install into `D:\\Games\\Just Cause 3\\dropzone` before phase Q, and only with
the user's explicit approval."* Yet G3c installed test-086 and drove it (*"The game ran: package loads,
Batmobile drivable"*), Batch F installed test-091 (*"test-091 installed over test-090 (game closed)"*),
and the tracker places the *remaining* drive in Q-2. So CAM-1's "installed" and its one piece of
behavioural evidence were obtained two phases early. That is not necessarily a violation — R6 allows
it *with the user's explicit approval*, and a user-requested camera look is plausible — but no line of
the record cites such an approval, and R6's own text makes the approval part of the evidence.

**Verdict: WEAK.** "Done" describes the build event on an item with no acceptance criterion; the row
does disclose the deferral, but the install/drive that back-fills the claim happened ahead of R6's
gate without a quoted approval. Defensible under a low bar ("the file exists and is packed"),
misleading under the one R14 sets ("evidence path required for `done`" — the evidence here is a build,
not a behaviour).

---

## What survives, what does not, and the smallest honest fixes

**Survives, well evidenced on disk.**
- 7.00 m / 1.30 m: two decoded operands and a disassembled composition; the artifact matches the
  report, and the report matches the bytes (A1).
- 55…63: the 16:9 conversion of 85/95 h, corroborated by the take's shrink being far from the
  "85 is vertical" prediction (A3).
- The carrier: one `.epe` string, 2 bytes, one occurrence, `SharedCarCamera` untouched (A9); one
  internal `.toc` record at `(16498168, 5968)` with the shared tune still external (A10).
- The routing conclusion ("the per-entity modifier is read, not the class camera") — the take's 20 %
  shrink exceeds the 7 % that the follow pull-back alone can produce (A7).

**Does not survive.**
- "95+10 h → 68.4 v" and its siblings (A4) — the 16:9 answer is **72.5**; 68.4 is 16:10.
- "2.27 m at ~3.5 m reads 36 % of a 55° view" (A5) — the stated inputs give 41.8 % (or 65 % of the
  vertical), not 36 %.
- "the tune is live" as evidence for the *shipped* values (A6, A7) — the file driven is
  `6f5a9cce…`, withdrawn; the frames' 1.20 shrink ratio matches 55→63 (1.18), not the installed
  55→85 (1.44).
- G3b's `2.4 / 1.7 / 55…85` as a description of the current output path (A8), and
  `CAM_TUNE.json`'s "not packed, not installed" (same section).
- The two fleet-shaped carriers (A11, A12) — one `.epe` in the build, no second variant, no census.

**Smallest set of changes that makes the record honest** (no new build, no launch):
1. `CAMERA.md` §2a and T-CAM2: "95+10 h → **72.5** v" and "**72** only if the +10 is folded in";
   a one-token fix in three places.
2. `CAMERA.md` §2a: restate the calibration with the real geometry ("3.495 m body at the 7 m boom
   reads ~33 % at 55 v", or drop the sentence — the value does not depend on it).
3. G3c: put "the tune is live" next to the sha it applies to, and add one line: *"nothing in the
   shipped file has been driven; the take's shrink ratio (1.20) matches 55→63, not the 55→85 that
   was installed — so the frames prove routing only."*
4. G3b: mark the paragraph "first candidate, withdrawn in G3d, sha `6f5a9cce…`", and fix
   `CAM_TUNE.json`'s `build` string to say packed into test-086/test-091.
5. A11/A12: either run `jc3_feature_census.py` for the `car_base.ctune` string and quote a count, or
   downgrade the wording to "the one donor plus eight class tunes".
6. T-CAM13: change `derived` → `assumed` until A15 shows the ray does not clip, and add bike/tank to
   the evidence that "above the camera" is normal.

Not closed by this pass, and not closeable without the game: whether the live dropzone still carries
test-091, the actual FOV at a given speed, the boost response (A14), and the collision ray behaviour
(A13).
