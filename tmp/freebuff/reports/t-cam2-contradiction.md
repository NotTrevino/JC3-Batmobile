STATUS: done — T-CAM2's numbers are right and its clause is wrong; the corrected row is proposed in `Working/Translation/T_CAM2_PROPOSAL.md` with the bytes behind it, and `T6_HUD_CAMERA.md` was not edited.

## What was decided

The row (`T6_HUD_CAMERA.md:127`) carries two things: the numbers `FOV [55,63]` v and a clause
"68 only if the +10 speed bonus is folded in; **95 boost is a gap**". The finding in
`Working/Translation/MODES_HUD_EVIDENCE.md` is correct in its verdict but it stops at "the cell
cannot have both". The evidence settles it: **the numbers survive, the clause does not.**

Numbers (decoded + derived, every byte re-read):

| value | source | result |
|---|---|---|
| `DrivingCamFOV1` = 85 h | `Research/BatmobileGrab/CAMERA.json` byte 241 (line 9), `bmak_camera.py --check` 33/33 from `BmGame.upk` | 85 h → **54.54** v, shipped as 55 |
| `BoostingCamFOV1` = 95 h | `CAMERA.json` byte 268 (line 10) | 95 h → **63.09** v, shipped as 63 |
| `DrivingCamMaxExtraFOV1` = 10 h | `CAMERA.json` byte 296 (line 11) | 95+10 = 105 h → **72.49** v |
| shipped `FOV` pair | `Builds/test-091/.../bat_base.ctunec` offsets 324/328 = `00 00 5c 42` / `00 00 7c 42` = 55.0 / 63.0 | matches 85 h / 95 h |
| the row's "now" 30…55 v | donor `Working/Audio/jc3cam/.../car_base.ctunec` offsets 324/328 = `00 00 f0 41` / `00 00 5c 42` = 30.0 / 55.0 | verbatim |

Clause, both halves refuted:

1. **"68 only if the +10 is folded in"** — its own formula gives 105 h → 72.49 v, not 68. 68 is
   100 h at 16:9 (67.67) or 95 h at **16:10** (68.59). It comes from `CAMERA.md:111`
   ("95+10 h → 68.4 v"), a stray aspect ratio; a reader following it lands 4.5° narrow.
2. **"95 boost is a gap"** — 63 *is* 95 h at 16:9 and 63 is what the built tune carries, so the
   boost FOV is expressed. The genuine unrepresentable state is boost **at** speed
   (95+10 = 105 h = 72.49 v), because JC3's `FOV` is one min/max pair over speed
   (`CAMERA.md:249`; ADF `FOV` 324/328 bounded by `FOVVelocityRange` 316/320).

The reason the cell reads as a contradiction is arithmetic, not a value error: `85 + 10 = 95`,
so the top of the band is *both* the boost FOV and the +10 bonus. 63 is right under either
attribution; only 105 h is missing. No byte of the build needs to move.

## Files written

| file | what |
|---|---|
| `Tools/scripts/t_cam2_proposal.py` | new tool, `--write` / `--check`; re-reads every cited byte, recomputes all conversions, renders the proposal, and fails if T6's row was edited |
| `Working/Translation/T_CAM2_PROPOSAL.md` | 8,353 bytes: verdict, byte table, the 16:10 reconstruction of 68.4, cell-by-cell change table, paste-ready corrected row, UNKNOWNs |
| `tmp/freebuff/reports/t-cam2-contradiction.md` | this report |

Not edited: `T6_HUD_CAMERA.md`, `Research/BatmobileGrab/CAMERA.md`, `CAM_TUNE.json`, any
`Builds/` tree, `CAMERA.json`. No rebuild, no install, no game launched.

## Commands run (verbatim)

```
cd /e/Modding/JustCause3/JC3-Batmobile && set -o pipefail && echo "=== write ===" && python Tools/scripts/t_cam2_proposal.py --write; echo "write exit=$?"; echo "=== check ===" && python Tools/scripts/t_cam2_proposal.py --check; echo "check exit=$?"
```
```
=== write ===
wrote Working\Translation\T_CAM2_PROPOSAL.md (8353 bytes)
85 h -> 54.54 v | 95 h -> 63.09 v | 105 h -> 72.49 v
write exit=0
=== check ===
PASS CAMERA.json DrivingCamFOV1 is 85 h at its byte offset
PASS CAMERA.json BoostingCamFOV1 is 95 h at its byte offset
PASS CAMERA.json DrivingCamMaxExtraFOV1 is 10 h at its byte offset
PASS 85 + 10 = 95: the bonus lands exactly on the boost FOV
PASS 85 h -> 54.54 v, rounds to 55
PASS 95 h -> 63.09 v, rounds to 63
PASS 95 + 10 = 105 h -> 72.49 v, which is not 68
PASS 68 v is the 16:9 vertical of ~100 h (67.67), not of any cited value
PASS 95 h at 16:10 -> 68.59 v: where the 68.4 in CAMERA.md came from
PASS the band is rounded inward (54.54 < 55, 63 < 63.09)
PASS 63 v back-converts to 94.90 h, i.e. the boost FOV
PASS donor FOV[0] at 324 is float32 30.0 (the row's 'now')
PASS donor FOV[1] at 328 is float32 55.0 (the row's 'now')
PASS test-091 FOV[0] at 324 is float32 55.0
PASS test-091 FOV[1] at 328 is float32 63.0
PASS test-091 FOVVelocityRange[1] at 320 is 108 km/h (T-CAM3's pair)
PASS CAMERA.md line 111 still carries 95+10 -> 68.4
PASS CAMERA.md still states JC3's FOV is one min/max pair over speed
PASS T6_HUD_CAMERA.md:127 still holds the original row (not edited)
PASS the original row appears exactly once in T6
PASS Working\Translation\T_CAM2_PROPOSAL.md matches a fresh render (bytes re-checked)
PASS the proposal carries the corrected row verbatim
PASS the corrected row drops the false gap
PASS the row mentions 68 only to refute it
PASS the row's three conversions are the recomputed ones

check: all assertions passed
check exit=0
```

Upstream oracles re-run (unchanged tools, read-only):

```
cd /e/Modding/JustCause3/JC3-Batmobile && set -o pipefail && echo "=== bmak_camera --check ===" && python Tools/scripts/bmak_camera.py --check 2>&1 | tail -6; echo "camera exit=${PIPESTATUS[0]}"; echo "=== bmak_camfile check ===" && python Tools/scripts/bmak_camfile.py check 2>&1 | tail -8; echo "camfile exit=${PIPESTATUS[0]}"
```
```
=== bmak_camera --check ===
PASS HelicopterCameraFOVAngle               70.0
PASS MinFreeCameraDistance                  164.0
PASS MaxFreeCameraDistance                  200.0
PASS DrivingCamConfig1 distance             400.0 / 400.0
PASS DrivingCamConfig2 distance             400.0 / 400.0
PASS: 33 camera values
camera exit=0
=== bmak_camfile check ===
check: 8/8 edits, 0 collateral rows, epe 2 bytes / 1 ref
camfile exit=0
```

And the raw byte probe that fixed the ADF offsets (before the tool existed):

```
cd /e/Modding/JustCause3/JC3-Batmobile && ls Builds/test-091/aaf/editor/entities/jc_cameras/vehicle_cameras/ 2>&1 | head; echo "---adf bytes"; python - <<'PY'
import struct
for p in ["Working/Audio/jc3cam/editor/entities/jc_cameras/vehicle_cameras/car_base.ctunec",
          "Builds/test-091/aaf/editor/entities/jc_cameras/vehicle_cameras/bat_base.ctunec"]:
    try:
        b=open(p,'rb').read()
        print(p, len(b))
        for off in (324,328,320):
            print("  off",off, b[off:off+4].hex(), struct.unpack_from('<f',b,off)[0])
    except Exception as e:
        print(p,"ERR",e)
PY
```
```
Builds/test-091/aaf/editor/entities/jc_cameras/vehicle_cameras/
auxilarymotion
bat_base.ctunec
car_base.ctunec
framing
shake
to_vehicle_trans.ctunec
transitions
---adf bytes
Working/Audio/jc3cam/editor/entities/jc_cameras/vehicle_cameras/car_base.ctunec 5968
  off 324 0000f041 30.0
  off 328 00005c42 55.0
  off 320 00004842 50.0
Builds/test-091/aaf/editor/entities/jc_cameras/vehicle_cameras/bat_base.ctunec 5968
  off 324 00005c42 55.0
  off 328 00007c42 63.0
  off 320 0000d842 108.0
```

## Labels

- **Decoded:** the three `CAMERA.json` values and their byte offsets/lines; the eight float32
  bytes in the donor and test-091 tunes (offsets 316/320/324/328); `CAM_TUNE.json`'s edit offsets
  and read-backs (55.0 / 63.0); the `CAMERA.md` lines and the T6 row text.
- **Derived:** 85 h → 54.54 v, 95 h → 63.09 v, 105 h → 72.49 v, 100 h → 67.67 v, 95 h at 16:10 →
  68.59 v, 85 + 10 = 95, and the inward-rounding note (55 is +0.46°, 63 is −0.09°).
- **UNKNOWN:** the three items in the proposal's §7 (which coincident reading the tune targeted;
  JC3's runtime aspect handling; whether 105 h should ever be built).

## UNKNOWNs

1. **Which reading of 63 the tune targeted** (85+10 or the boost 95). Both are numerically 95 h, so
   no value is at stake; the ADF carries one `FOV` pair with no per-state attribution. Resolving it
   would need JC3 camera code or an in-game take — the test ban excludes the latter.
2. **JC3's runtime aspect behaviour.** 55/63 are correct at 16:9, the row's stated scope. No file
   read reports what JC3 does on a 21:9 screen; not guessed.
3. **Whether the boost-at-speed state (105 h → 72.49 v) should be built at all.** No byte here
   supplies a per-state carrier, so it stays a named gap rather than a number.

## COMPROMISES

None. No value was hand-substituted, no row was edited, no build touched, no install, no game.

## Note for the operator

Accepting the proposal leaves the wrong sentence in `Research/BatmobileGrab/CAMERA.md:111`
("95+10 h → 68.4 v"), which is where the clause came from; that file belongs to another task, so
it was left alone. If T6 is fixed without fixing that line, the error can be re-inherited by the
next reader.
