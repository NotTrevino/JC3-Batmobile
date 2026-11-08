# Independent review — CAM-1 · Chase camera at the decoded composition

Reviewer: Freebuff (did not write this card). Date: 2026-10-29.
Scope: `GRAB_BACKLOG.md` §0.5 (R1–R14), §1 the CAM-1 row (line 244), §12 the CAM-1 row (line 1365);
`MODLOG.md` §"Batch F: the camera, re-derived from the executable — and a pack bug it exposed"
(line 7663); the outputs (`Working/Camera/CAM_REF.md`, `Working/Camera/CAM_TUNE.json`,
`Tools/scripts/bmak_camfile.py`, `Tools/scripts/bmak_camdecode.py`,
`Working/Translation/T6_HUD_CAMERA.md` §2/§4) and the two candidate files under
`E:/Modding/_JC3cam_out/`.
Read-only: nothing under `Research/`, `Tools/`, `Working/`, `GRAB_BACKLOG.md`, `MODLOG.md` or the
game install was written; no game was launched; nothing was committed. This report is the only file
written.

## VERDICT: **minor issues**

The work itself is sound and, unusually, independently reproducible: `bat_base.ctunec` in
`Builds/test-091` carries all eight delivered values, the donor `.epe` in that build references
`bat_base.ctune` once and `car_base.ctune` never, the source/donor hashes in `CAM_TUNE.json` match
the files on disk, and `bmak_camdecode.py --check` reproduces the composition 18/18. No value is a
guess, nothing is substituted for the two blocked rows (T-CAM9, T-CAM11), and the requirement (7.00 m
back / 1.30 m up / FOV 55…63) is met by the file that is named as its carrier.

What is not sound is the *paper trail around* it: `Working/Camera/CAM_REF.md` still calls the
candidate **withdrawn**, still says `build` fails closed, quotes a **sha256 that is the old
withdrawn candidate's**, and states two ADF row counts (187 / 179) that the project's own reader
contradicts (200 walk rows / 192 others). And `bmak_camfile.py check` — the command every record
cites — never looks at `test-091`, compares only the `.ctunec` candidate (never the `.epe`), and
silently skips even that when `E:/Modding/_JC3cam_out` is absent. The card is "done as Batch F
(test-091)"; no command in the card checks test-091.

## Check output (verbatim)

```
$ python Tools/scripts/bmak_camfile.py check
check: 8/8 edits, 0 collateral rows, epe 2 bytes / 1 ref
EXIT=0
```

Supporting commands named by the card's record:

```
$ python Tools/scripts/bmak_camdecode.py --check
PASS sit min (cfg+0x00)                           [-300.0, 0.0, -25.0]
… (17 more PASS lines)
PASS: boom composition
EXIT=0

$ python Tools/scripts/bmak_camera.py --check
… PASS: 33 camera values
EXIT=0
```

## Out paths

| path named by the card / record | exists | value |
|---|---|---|
| `E:/Modding/_JC3cam_out/bat_base.ctunec` | yes | 5,968 B, sha256 `c8a088e5…75cb` |
| `E:/Modding/_JC3cam_out/v0300_…_civilian_01.epe` | yes | 105,430 B, sha256 `cf49315a…f484` |
| `Working/Camera/CAM_TUNE.json` | yes | 3,010 B, the generated record |
| `Builds/test-091/aaf/editor/entities/jc_cameras/vehicle_cameras/bat_base.ctunec` | yes | 5,968 B, sha256 `c8a088e5…75cb` (identical to the candidate) |

`Builds/test-091/.../v0300_car_kensington_sportsmuscle_civilian_01.epe` references
`bat_base.ctune` 1× and `car_base.ctune` 0× — the `.epe` half of CAM-1 is in the delivered tree too.

## Does the Done criterion match what `--check` verifies? — **no, partially**

* The card's claim (§12 line 1365, and T6 §4 "What test-091 carries") is **done as Batch F
  (test-091)**.
* `bmak_camfile.py` never opens `Builds/test-091`. Its donor is hard-coded:
  `DONOR_EPE = Builds/test-085/.../v0300_car_kensington_sportsmuscle_civilian_01.epe`
  (`Tools/scripts/bmak_camfile.py:56`), and `grep -n 'test-091' Tools/scripts/bmak_camfile.py` has no
  hit. `check` re-emits a candidate into a temp dir and compares it to
  `E:/Modding/_JC3cam_out/bat_base.ctunec` — and only `if os.path.exists(fresh):` (line 260).
* Consequence: delete or corrupt the candidate outside the repo and the check still says
  `8/8 … EXIT=0`; the `.epe` candidate is never compared at all (`main()`'s `check` branch only
  byte-compares `OUT_CTUNEC`).
* The delivered values are nevertheless right — verified here independently, not by the card: the
  200-row decode of `Builds/test-091/.../bat_base.ctunec` returns `CameraPosition[1] 1.2999999`,
  `CameraPosition[2] 7.0`, `LookAtPoint[1] 1.5499999`, `FOV[0] 55.0`, `FOV[1] 63.0`,
  `FOVVelocityRange[1] 108.0`, `RollWithVehicleAmount 0.3800000`, `CollisionStartPoint[1] 1.6000000`.

So the requirement is met; the *evidence chain* the card relies on is a manual sha256 comparison that
no shipped command performs.

## Issues

### 1. `CAM_REF.md` is stale: it quotes the withdrawn candidate's hash and says "withdrawn"
File: `Working/Camera/CAM_REF.md:149` and `:144`, `:163`.
It prints
`E:/Modding/_JC3cam_out/bat_base.ctunec      5,968 B  sha256 6f5a9cce5a84…` and
"The candidate is withdrawn and `bmak_camfile.py build` fails closed." / "**Withdrawn.** … no build is
emitted until the sit-offset/400 cm composition is decoded."

Evidence:
```
$ sha256sum E:/Modding/_JC3cam_out/bat_base.ctunec
c8a088e537a01c6d684842a9094663225878d0919e6486dab6c13350dcbe75cb
$ grep -n '6f5a9cce' MODLOG.md Working/Camera/*.md
MODLOG.md:6862:- `E:/Modding/_JC3cam_out/bat_base.ctunec` — 5,968 B, `6f5a9cce5a84…`: position `[0,2.4,7.0]`,
Working/Camera/CAM_REF.md:149:E:/Modding/_JC3cam_out/bat_base.ctunec      5,968 B  sha256 6f5a9cce5a84…
```
`6f5a9cce…` is the first-pass candidate (`position [0,2.4,7.0]`, test-086, withdrawn 2026-10-22) —
not the file that exists. The composition was decoded and Batch F un-withdrew the tool on 2026-10-23
(`MODLOG.md:7663`); `guard()` now fails closed on *wrong inputs* only, so `build` no longer refuses,
which is why `check` (which calls the same `run()`) succeeds at all. §4's "withdrawn" heading is
correctly dated and labelled as history; §5's last paragraph and §6 were never updated. This is a
hand-maintained number in a research doc (R11) that is now false, and a status line that contradicts
§12 and T6 §4.

### 2. `--check` is fail-open and does not cover the artefact the card claims
Files: `Tools/scripts/bmak_camfile.py:56` (donor is test-085), `:260` (`if os.path.exists(fresh)`),
`:284-289` (the `check` branch prints a hardcoded summary); T6 §4's "`bmak_camfile.py check`
re-derives it (8/8 edits, 0 collateral ADF rows)".
Why it matters: `check` is the card's only command, and it cannot distinguish "the delivered build
carries these values" from "a candidate outside the repo happens to match a fresh rebuild from
test-085". With `E:/Modding/_JC3cam_out` removed, `check` verifies nothing beyond the rebuild and
still exits 0. The `.epe` candidate written by `build` is never compared by `check` either, so a
tampered `…civilian_01.epe` in `_JC3cam_out` goes unnoticed. A check that can pass while the only
delivered file is missing is not the Done gate for "done as Batch F (test-091)".

### 3. Two ADF row counts are typed and contradicted by the reader
Files: `Working/Camera/CAM_REF.md:73` ("Same 800-byte `GenericVehicleCamera` layout, **187 decoded
rows**"), `Working/Camera/CAM_REF.md:154` ("every one of the other **179** ADF rows unchanged");
the same 179 appears in `Research/BatmobileGrab/CAMERA.md:266`.

Evidence, with the project's own reader:
```
car_base.ctunec  5968 bytes  200 rows  GenericVehicleCamera
mediumtank.ctunec 5970 bytes 200 rows  GenericVehicleCamera
bike_base.ctunec  5969 bytes 200 rows  GenericVehicleCamera
members: 55 walk rows: 200
$ grep -rn '187\|179' Tools/scripts/bmak_cam*.py
(no output)
```
`jc3adf.walk()` yields **200** rows and the type has 55 members, so "187 decoded rows" is neither the
row count nor the member count, and "the other 179" should be **192** (200 − 8 edits). No script
emits either number (R11: counts come from a script). Note this does not weaken the delivered values —
`check`'s "0 collateral rows" is a real full-walk assertion over all 200 rows — it is the *documented
count* that is wrong.

### 4. The check prints a typed "8/8"
File: `Tools/scripts/bmak_camfile.py:288` — `print(f'check: 8/8 edits, …')`, and the `checks` array in
`run()` (`:227-232`) is typed prose ("8/8 old values asserted before write", …).
`len(EDITS)` is now 8, so the sentence is true today, but a ninth edit would still print "8/8" while
the JSON's `readback` said 9/9. Same class as issue 3, smaller blast radius: the number that the
record quotes should be formatted from `len(rows)` / `len(EDITS)`.

### 5. T-CAM2's target is a rounded conversion labelled `decoded`
File: `Working/Translation/T6_HUD_CAMERA.md:127` — `FOV [55,63]` with `conf = decoded`, and
`GRAB_BACKLOG.md:244` repeats "FOV 55…63".
The conversion is `v = 2·atan(tan(h/2)/(16/9))`: 85 h → **54.54** v, 95 h → **63.09** v (computed
here). The emitted 55 is 0.46° *above* the decoded lower bound and the 63 is 0.09° below the upper
one, i.e. the band is rounded inward; the row does not say so, and its `conf` cell — which the table
uses for the *derived* rows T-CAM6/T-CAM7/T-CAM13 — says `decoded` for a converted value. Neither the
0.5° nor the rounding is a build defect; the class label is (R4: a conversion is not a decoded value).
T-CAM3's `[5,108]` and T-CAM6's `0.38` and T-CAM13's `1.6` are the same rounding pattern and *are*
labelled `derived` (T-CAM3 is also `decoded`), so the table is internally inconsistent.

### 6. Not verified anywhere (stated as a limit, not a defect)
`CAM-1` is "done" at the build level. The behaviour take — A15, the camera drive (`GRAB_BACKLOG.md`
§Q-2, "camera drive") — is still in Q-2: no frame of the new composition has been driven. §12 says
so, T6 §3 says so, and R6 forbids launching before phase V, so this is the correct state, not an
omission. The only in-game evidence for the whole mechanism (the modifier's tune being live, car
36% → 30% of frame width from 0 to 103 km/h) comes from the withdrawn test-086 values and is used
only to settle *routing*, which is what T6 §3 claims for it.

## Spot-checks

| value in the doc | where verified | result |
|---|---|---|
| T-CAM5 `CameraPosition [0, 1.30, 7.00]`, `LookAtPoint [0, 1.55, 0]` | `CAM_TUNE.json` readback (`1.2999999 / 7.0 / 1.5499999`) and an independent `jc3adf.walk` of `Builds/test-091/.../bat_base.ctunec` | **agree** |
| T-CAM2 `FOV [55,63]` vertical from 85/95 h | `CAM_TUNE.json` `55.0 / 63.0`, test-091 decode `55.0 / 63.0`; conversion recomputed `54.54 / 63.09` | agree on the value; the 55 is a rounded-up 54.54 (issue 5) |
| T-CAM3 `[5,108]` km/h from 3000 cm/s | `CAM_TUNE.json` `108.0`; `3000 × 0.036 = 108.0` (computed); `bmak_camera.py --check` `PASS DrivingCamFOVInterpMaxSpeed1 3000.0` | **agree** |
| T-CAM6 `0.38` from lean 7.5° / roll limit 20° | `7.5/20 = 0.375` (computed), `CAM_TUNE.json` `0.37999999`, test-091 decode `0.3800000` | **agree** (0.375 rounded to 0.38) |
| T-CAM13 `1.6` m from body 2.271 m vs donor 1.41 m | `2.271/1.41 = 1.6106` (computed), `CAM_TUNE.json` `1.6`, test-091 decode `1.6000000` | **agree** |
| `CAM_TUNE.json` `source.sha256` / `epe.sha256_before` | `sha256sum` of `Working/Audio/jc3cam/.../car_base.ctunec` (`25e38c62…`) and `Builds/test-085/.../civilian_01.epe` (`7385eced…`) | **agree** |
| `CAM_REF.md:149` sha256 `6f5a9cce…` | `sha256sum E:/Modding/_JC3cam_out/bat_base.ctunec` → `c8a088e5…` | **disagree** (issue 1) |
| "187 decoded rows" / "other 179 ADF rows" | `jc3adf.walk` on three vehicle cameras → 200 rows, 55 members | **disagree** (issue 3) |

## What is solid

* The eight values are in the file the card names, in `Builds/test-091`, and re-read from it here.
* `bmak_camdecode.py --check` 18/18 reproduces the composition from the executable
  (`Loc = anchor − forward·400 + Rot·Sit`, sit −300,0,−25 cm, pivot 155): the 7.00 m / 1.30 m are
  arithmetic, not body-length scaling (the withdrawn pass's error), and the difference is stated.
* `bmak_camera.py --check` 33/33 covers the 33 authored values the rows cite.
* The `.epe` edit is the minimum possible: one 14-byte path, `car_base` → `bat_base`, 2 bytes, size
  unchanged, 1 occurrence asserted and the replacement asserted to land exactly
  (`patch_epe()`); test-091 confirms 1 × `bat_base.ctune`, 0 × `car_base.ctune`.
* No number was hand-substituted for T-CAM9 (spring bridge) or T-CAM11 (shake); both stay `blocked`,
  and T-CAM8 too. R4 is respected on the value side.
* The card did not ship a new shared module (R7): `bat_base.ctunec` is an added private file next to
  the six-byte-longer-family of vehicle tunes; `car_base.ctunec` is untouched.
* Candidate and build files live outside the repo / in `Builds/` (R10), and nothing was installed by
  this review.

## Minor / not an issue

* `CAM_TUNE.json`'s `output.ctunec` mixes separators (`E:/Modding/_JC3cam_out\bat_base.ctunec`).
  Cosmetic, same value on Windows.
* `MODLOG.md:7663` (Batch F) and T6 §4 agree with each other and with the file hashes; it is
  `CAM_REF.md` alone that was left behind.
* The `bmak_cambuild.py` path-escape bug recorded in Batch F (the patched `.epe` written into the
  test-085 tree) was fixed there and test-085's `.epe` was restored to `7385eced…` — re-verified
  here: `Builds/test-085/.../civilian_01.epe` is exactly that hash, i.e. the donor is clean and
  `bmak_camfile.py check` is reading an unmodified input.

## Suggested fixes, in the card's own terms

1. Regenerate or correct `CAM_REF.md` §5's last paragraph and §6: status `done (Batch F, test-091)`,
   the live sha256 `c8a088e5…`, no "withdrawn" on the candidate (keep §4's dated history).
2. Make `check` cover the claim: assert `Builds/test-091/.../bat_base.ctunec` byte-equals the fresh
   build (or decode the eight values out of it), compare the `.epe` candidate too, and make a missing
   `_JC3cam_out` a **failure** instead of a silent skip.
3. Replace the typed "8/8" and the row counts (187 / 179) with `len(rows)`-derived text, or drop the
   counts.
4. Give T-CAM2's target `conf = derived` (or state the inward rounding) so the row's class matches
   what the value is.
