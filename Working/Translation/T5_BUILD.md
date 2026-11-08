# T-5 — the one build carrying the translation table

**Status:** built and installed as **test-085**, 2026-10-22. The **35** numeric rows are in the live
`.ee` and were read back **through the `.toc`**, the way the engine reads them — 35/35. One driving
take has since measured the launch and top speed (`QA1_RESULTS.md`); the remaining `verify` cells
are behaviour and are named, not claimed.

```
base      Builds/test-083          (test-083: appearance/budget build, meshes untouched here)
edits     Working/Translation/t1_edits.json   (35: 34 number, 1 probe)
applied   Working/Translation/t5_applied.json (per-edit re-read + untouched-member proof)
build     Builds/test-085          .ee 10,736,895 B  sha256 D9C4AAD3…8BB7FC2
                                   .toc 50,573 B      sha256 4FD6DB3C…C88541A0
install   Builds/test-085/install.ps1 -Action Install   (Verify / Rollback083 / Status)
rollback  Builds/test-083/install.ps1 -Action Install
measured  Working/Translation/QA1_RESULTS.md          (QA-1 take 1)
```

## 1. What the build changes

Ten modules, 35 members. Nine kept their exact byte size; `rigid_body.vmodc` shrank 992 → 976
because Gibbed's writer normalises 16 bytes of trailing padding — proven unrelated to the edits by
decoding and re-encoding the **unedited** file, which also produces 976. Every other member in every
edited module was compared before and after: **0 moved** (the applier fails otherwise). Because one
module moved, the `.toc` was rebuilt from 083's and all **478** internal records were checked against
the new `.ee`.

| module | edits | rows |
|---|---|---|
| `rigid_body` | 4 | T-M1, T-M2 ×3 |
| `land_global` | 5 | T-M4 ×2, T-R1 ×2, T-G5 (probe) |
| `suspension` | 4 | T-S1 ×2, T-S2 ×2 |
| `land_steering` | 5 | T-ST1 ×5 |
| `land_engine` | 5 | T-E1 ×3, T-E3 ×2 |
| `transmission` | 6 | T-E4 ×6 (gears + 5 upshift points) |
| `land_aerodynamics` | 2 | T-A2, T-A4 |
| `brakes` | 2 | T-K1 ×2 |
| `land_audio` | 1 | T-AU4 (pitch ceiling follows T-E1) |
| `health` (`VehicleDamage`) | 1 | T-DM2 (armour 100 → 99, the fleet maximum) |

## 2. Offline verification (all re-runnable)

| check | tool | result |
|---|---|---|
| every `old` value equals the build's value, every row exists in the table, every member exists | `t1_apply.py` | **35 / 35 ok** |
| every edit applied, re-read, and every *other* member unchanged | `t5_apply.py` | **35 / 35**, 10 modules, 0 collateral |
| packed build differs from 083 only in those 10 modules | `t5_build.py` (aafdiff) | **10 changed, 0 added, 0 removed** |
| every internal `.toc` record (offset > 0) matches the `.ee` it names | `t5_build.py` | **478 / 478** (505 records) |
| installed pair matches the receipt; meshes/textures decode through the `.toc`; archives baseline unchanged | `verify_install.py` | **9 / 9 PASS** |
| each row's `new` value as the engine will read it: sliced by `.toc`, decoded, compared | `t5_measure.py` | **35 / 35 equal** (`t5_rows.json`, `problems: []`) |
| wheel stations still where the table says (T-G1: front ±1.208 @ z −2.570, rear ±1.2845 @ +2.4589, y 0.7047/0.7027) | station scan of the installed `.physicsc` | **4 / 4 quads** |

These are the rows whose `verify` cell is a **property of the files**, so they are measured:
T-G1, T-G5 (the enum is *carried*, its behaviour is not), T-MA1, T-P1, T-P2, T-P3's read side,
T-LG2's re-read, T-DM*'s thresholds, and every `decoded`/`derived`/`class` value in the edit list.

## 3. Behaviour: measured and open

QA-1 take 1 (`QA1_RESULTS.md`) is one run from a standstill to 138 km/h and off the road. It closes:

| row | measurement | result |
|---|---|---|
| T-M1 | 0-100 km/h | **16.4 s**, 257 m, at the built 6,000 kg |
| T-E1 | top speed in 800/2800/4500 rpm | **138 km/h**, drag-limited (the gearing would allow 240) |
| T-E4 | shift point at 4,200 rpm | **partial**: first knee at 67 km/h = the computed 66.8; no hunting |
| T-K1 | deceleration under braking | **partial**: 138→100 in 3.0 s, 3.5 m/s² on tarmac |

Still open, each needing a prescribed manoeuvre:

| rows | measurement | pass |
|---|---|---|
| T-E4 | shift points in gears 2-4 | needs engine pitch: a take recorded **with audio** |
| T-K1 | 100 → 0 km/h on tarmac | a full stop on the road, not through a corner exit |
| T-M2, T-M3 | yaw response, balance | a constant-radius corner at 60 and 100 km/h |
| T-S1, T-S2, T-M4 | kerb strike, pothole, landing | no bottoming-out, no wheel jitter |
| T-S1 (ride height) | static ride height on a known kerb | body clears, wheels grounded |
| T-G5 | the same corner at low speed | tells us what `wheels_friction_type = 2` *means* (probe) |
| T-LG*, T-AU*, T-FX*, T-DM* | dusk/night beams, engine pitch, window break, 5-star pursuit | as listed in T-1/T-2 |

## 4. Beyond this build: T-3 coverage

`T3_COVERAGE.md` closes the field set the first table did not name: every one of the **423** decoded
BmAK fields maps to a row (`bmak_coverage.py --check`), including the afterburner, drift block,
handbrake, suspension travel, tyre effects and the families JC3 cannot express (weapons, battle mode,
air control, ram assists, self-righting). The audit's three damage "defects" were withdrawn after
test-087 was driven: `impact_damage_factor` **0** is the switch that reproduces the Batmobile's
immunity to ramming, `deform_scale` **0** is a cosmetic switch, and `impact_armor` **5000** was a
misrecorded cap. The build's damage block is a declared saturation island
(`damage_switches.json`, checked by `damage_audit.py`), not a translation — see
`POSTMORTEM_DAMAGE.md`. The six class-median handling values remain staged, not built; each needs a
behaviour and a failing take first (`T3_COVERAGE.md` §4).
test-086 became the camera probe and is withdrawn, but its source was decoded afterwards; a corrected
camera batch is fully derivable (`CAMERA.md` §2b: FOV 55…63, 700 cm boom, 130 cm height), with
T-CAM9 (springs) and T-CAM11 (shake) still blocked.

## 5. Reproduce

```
python Tools/scripts/t1_apply.py                      # the list still matches the table + build
python Tools/scripts/t5_apply.py --aaf Builds/test-083/aaf --out Builds/test-085/aaf
python Tools/scripts/t5_build.py --aaf Builds/test-085/aaf --base Builds/test-083 --tag test-085
powershell -File Builds/test-085/install.ps1 -Action Install
python Tools/scripts/verify_install.py --build Builds/test-085
python Tools/scripts/t5_measure.py --build Builds/test-085
python Tools/scripts/t3_fleet.py --check      # class medians behind the T-3 rows
python Tools/scripts/bmak_coverage.py --check # every BmAK field has a row
```

QA-1, on any later take:

```
python Tools/scripts/qa1_hud.py crops --video <take>.mkv --out <work> --fps 5
python Tools/scripts/qa1_hud.py build --crops <work>/hud --known Working/Translation/QA1/known.json
python Tools/scripts/qa1_hud.py trace --crops <work>/hud --csv <work>/trace.csv --fps 5
python Tools/scripts/qa1_hud.py measure --csv <work>/trace.csv --json <work>/measure.json
```

## 6. test-088 — Batch B2, the behaviour-first build (2026-10-23)

```
base      Builds/test-085              (085's 35 values unchanged underneath)
edits     Working/Translation/t5c_edits.json    (4: T-B3, T-B2, T-K2 x2 — T-ST5 withdrawn)
applied   Working/Translation/t5c_applied.json  (per-edit re-read + size check)
build     Builds/test-088              .ee 10,736,878 B  sha256 5A79D885…79DF556F7860
                                      .toc 50,573 B      sha256 4FD6DB3C…C88541A0 (505 records)
install   Builds/test-088/install.ps1 -Action Install
rollback  Builds/test-085/install.ps1 -Action Install
```

The batch table — the BmAK behaviour behind each value, its source class and the take that can
fail — is `T_PLAN.md` §4 **Batch B2**. Two of test-087's six survivors were withdrawn there under
R2, so this build is four values, not six.

| gate | tool | result |
|---|---|---|
| every `old` equals the **batch base's own decode** (test-085 via `t5c_current.json`), every row and member real | `t1_apply.py --edits t5c_edits.json --current t5c_current.json` | **4 / 4** — and the control fails: the 35-edit list pointed at the same snapshot reports `T-K1 build holds 5000, list expects 10000 …`, exit 1 |
| every edit applied, re-read, size-checked | `t5_apply.py` | **4 / 4**, 2 modules |
| packed build differs from 085 only in the edited modules | `t5_build.py` (aafdiff) | **2 changed, 0 added, 0 removed** |
| every internal `.toc` record equals the `.ee` member it names | `t5_build.py` (guard) | **478 internal of 505**, 0 mismatch |
| installed pair matches the receipt; meshes/textures decode through the `.toc` | `verify_install.py` | **9 / 9** |
| each row's `new` as the engine will read it: sliced by `.toc`, decoded, compared | `t5_measure.py` | **4 / 4** |

Behaviour is open on purpose (R4 — the rows stay `next` until their take passes): **A2** boost
top speed, **A5** braking 100 → 0, **A9** 0–100 with and without boost, and **A7** for T-ST5,
which needs no build because its values did not move. One take each, into `QA1_RESULTS.md`.

**Why the deploy test came first.** `verify_install.py --build Builds/test-085` reported **8/9**
on 2026-10-23: the dropzone `.ee` was `10B14A60…` = **test-087**, so the postmortem's rollback
had never actually run. test-085 was reinstalled (9/9) and only then packed into test-088.

## 7. test-089 — Batch B3, re-sourced from the grab (2026-10-23)

```
base      Builds/test-088              (088's four Batch B2 values underneath)
edits     Working/Translation/t5d_edits.json    (4: T-ST5 x2, T-B2, T-B3 — re-sourced from CHAIN.json)
applied   Working/Translation/t5d_applied.json  (per-edit re-read + size check)
current   Working/Translation/t5d_current.json  (snapshot of test-088, the batch's own base)
build     Builds/test-089              .ee 10,736,878 B, 505 .toc records, 2 modules
install   Builds/test-089/install.ps1 -Action Install   (deployed; verify 9/9)
rollback  Builds/test-088/install.ps1 -Action Install
```

The batch table — the BmAK member behind each value, its source class and the take that can fail
— is `T_PLAN.md` §4 **Batch B3**. `bmak_chain.py` bound the SDK layout names to the cooked values
(`CHAIN.json`, cross-checked 336/0), which showed three of Batch B2's four "no member in BmAK"
claims were false: the countersteer/steer-in modifiers exist (both read **1.0**), the boost
extra-speed member exists (min(3500, 600 × 2.0) = **43.2 km/h**), and the grip absence is now
*proven* rather than asserted (so identity, **1.0**). T-K2's value did not move (donor 1.0); its
evidence cell now names `HandBrakeOffTime` 0.3 s and the exhaustive no-lock search.

| gate | tool | result |
|---|---|---|
| every `old` equals the **batch base's own decode** (test-088 via `t5d_current.json`) | `t1_apply.py --edits t5d_edits.json --current t5d_current.json` | **4 / 4** |
| every edit applied, re-read, size-checked | `t5_apply.py` | **4 / 4**, 2 modules |
| packed build differs from 088 only in the edited modules | `t5_build.py` (aafdiff) | **2 changed, all in the edit list** |
| `.toc` record list identical to base | `t5_build.py` (guard) | **505**, 0 mismatch |
| installed pair matches the receipt; meshes/textures decode through the `.toc` | `verify_install.py` | **9 / 9** |
| each row's `new` as the engine reads it, sliced by `.toc` | `t5_measure.py --applied t5d_applied.json` | **4 / 4** (43.2000008 / 1.0 / 1.0 / 1.0) |

Behaviour is open on purpose (R4): **A2** boost top speed, **A5** braking 100 → 0, **A9** 0–100
with/without boost, and **A7** drift release — A7 now needs this build, because T-ST5's values
moved 2.0 / 1.5 → 1.0 / 1.0 (both declared out-of-domain under R3).

## 8. test-090 — Batch B4, the sweep's one bridge (2026-10-23)

```
base      Builds/test-089              (089's four Batch B3 values underneath)
edits     Working/Translation/t5e_edits.json    (2: T-S3 front.length + rear.length)
applied   Working/Translation/t5e_applied.json  (per-edit re-read + size check)
current   Working/Translation/t5e_current.json  (snapshot of test-089, the batch's own base)
build     Builds/test-090              .ee 10,736,878 B, 505 .toc records, 1 module
install   Builds/test-090/install.ps1 -Action Install   (deployed; verify 9/9)
rollback  Builds/test-089/install.ps1 -Action Install
```

Batch B4 re-checked every remaining `class`/donor row against `CHAIN.json` (table in `T_PLAN.md`
§4). One row had a same-quantity, same-unit bridge: `SVehicleWheel.SuspensionTravelUp` 30 +
`SuspensionTravelDown` 40 cm = 0.70 m stroke, and `length/min_length` carry exactly one stroke
(T-S6), so T-S3 moves 0.25 → **0.70** — in-domain for the 6 t+ class (0.18 … 0.75), 3.9× its
median, declared BmAK-first. The sweep's negatives became chain results in their cells: T-K1's
`MaxBrakeTorque` 300 is **disproven** as a bridge by magnitude (0.29 m/s² at 6 t vs the measured
3.5–3.8), and T-M2/M3/M4, T-A2/A4, T-ST6, T-K3 record an absence the chain actually returned.

| gate | tool | result |
|---|---|---|
| every `old` equals the batch base's own decode (test-089 via `t5e_current.json`) | `t1_apply.py --edits t5e_edits.json --current t5e_current.json` | **2 / 2** |
| every edit applied, re-read, size-checked | `t5_apply.py` | **2 / 2**, 1 module |
| packed build differs from 089 only in the edited module | `t5_build.py` (aafdiff) | **1 changed, all in the edit list** |
| `.toc` record list identical to base | `t5_build.py` (guard) | **505**, 0 mismatch |
| installed pair matches the receipt | `verify_install.py` | **9 / 9** |
| each row's `new` as the engine reads it, sliced by `.toc` | `t5_measure.py --applied t5e_applied.json` | **2 / 2** (0.699999988 front and rear) |

Behaviour open on purpose (R4): **A6** (kerb strike, pothole, landing at 3 speeds) and the static
ride-height take are now the gate for T-S3 — the car rides on 0.70 m of travel it did not have.
