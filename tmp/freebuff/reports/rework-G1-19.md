# G1-19 rework — cockpit and driver placement

Date 2026-10-29. Input: `tmp/freebuff/reports/review-G1-19.md` (verdict `needs rework`).
Every review issue was re-checked against the data before any change. No game was launched, nothing
was written under `D:/Games`, no shared game module was edited, nothing was committed.

## STATUS: **done — all 10 issues CONFIRMED and fixed; 0 rejected**

The card now has a generator (`Tools/scripts/grab_cockpit.py`) and a real gate: `--check` re-derives
every number from the PSKX, `SOCKETS_JC3.json`, `SLOTS.json`, `stations.json` and the material rows,
compares the result with `COCKPIT.json`, and fails if `COCKPIT.md` is not the current generator
output. `COCKPIT.md` is generated output from this point (R11, §0.2 step 5).

## Per-issue verdicts

### 1. "No script and no `--check` — every count typed" — **CONFIRMED**
Before: `ls Tools/scripts/ | grep -i cockpit` printed nothing; `Research/BatmobileGrab/` had only
`COCKPIT.md` (no `.json`); the MODLOG "Verified" block listed other cards' gates.
Fix: new `Tools/scripts/grab_cockpit.py` (`--write` / `--check`), new `COCKPIT.json`, and
`COCKPIT.md` re-generated from it. The page now carries no hand-typed count; `--check` verifies both
the JSON and the page.

### 2. "`DriverAnimOrigin` is not in the required-anchor list" — **CONFIRMED**
`SOCKETS_JC3.json` → `required_anchors.names` = 13 entries, `Driver` present, `DriverAnimOrigin`
absent (`present` also 13/13). Fixed in the generated text: "Of the 13 required anchors … `Driver`
is the only driver anchor in the list … `DriverAnimOrigin` is not one of the 13".

### 3. "A level ray from the eye passes at y 1.545 — that is the 13.5° sightline" — **CONFIRMED**
A level ray from (x, 1.6547, z) stays at y = 1.6547. The 1.545/1.543 figure is the screen
sightline's y where it crosses z −1.52. Measured now: crossing y **1.5434**, angle **13.8°** below
level to the *measured* screen centre (−0.000, 1.4857, −1.7552). (The review's 1.5458 uses the old
assumed centre (0, 1.489, −1.757); the arithmetic is right, the label was not.) Fixed: the sentence
names it the screen sightline and prints the generated value.

### 4. "1.065 m behind the car's midpoint toward the nose" — **CONFIRMED**
`stations.json` `body_bbox` z −3.42…3.605 → midpoint **+0.0925**; wheelbase midpoint
(−2.570 + 2.4589)/2 = **−0.0556**. Neither is 0; 1.065 is |z| from the assembly origin, and "behind
… toward the nose" contradicts itself (nose is −z). Fixed: the Driver's z is given as **assembly z
−1.0654** and **1.5046 m behind the front axle (z −2.57)**; no midpoint claim.

### 5. "Centre-screen box 0.314 × 0.145 m vs the panel's 0.318 × 0.151" — **CONFIRMED**
Measured on the 100 slot-12 faces: x −0.15943…0.15936 (**0.3188**), y 1.41013…1.56131 (**0.1512**),
z −1.85236…−1.65814; area 404.06 cm² (the review's area matched). Fixed: the generated box prints
**0.3188 × 0.1512** and the exact bounds.

### 6. "`rotation identity` hides that the socket basis is rolled 90°" — **CONFIRMED**
`SOCKETS_JC3.json` `Driver`: `up_jc3` **(−1, 0, 0)**, `right_jc3` **(0, 1, 0)**,
`rotation_missing: true`. Fixed: the socket table now prints `up_jc3` / `right_jc3` and says the
socket's own up is the car's lateral axis, so the seated pose must be built on world up.

### 7. "Three subset counts have no selection rule" — **CONFIRMED**
Re-ran the obvious rules: the slot-10 all-vertices box gives **5,114 faces / 4,951.8 cm²**, the
centroid rule 5,540 / 7,763 cm², the lip band 2,694 / 2,870, the bolsters 1,022 / 830 — none is
728 / 486, 3,310 + 3,862, 7,528 or 1,036. Fixed: those counts are gone; the page now prints only
selections whose rule is written next to them and computed by the script:
- driver-facing panel: **1,043 faces / 720.3 cm²**, bbox x ±0.3457, y 1.3148…1.6005, z −1.8981…−1.5097,
  rule "slot 10, face normal +z > 0.5, centroid |x| ≤ 0.36, y 1.30…1.60, z −1.90…−1.50";
- side windows: **611 faces**, z −1.5925…−0.8349, y 1.5165…1.8868 (rule: glass slot, |x| > 0.25,
  z −1.60…−0.40);
- seat/glass/roof slot totals and bone splits (12,470 + 544; 14,136 + 13,198; 1,716; 524) — all
  reproduce exactly.

### 8. "Anthropometry is an uncited assumption presented as `derived` (R4)" — **CONFIRMED**
No file in the project ships a seated eye or sitting height. Fixed: the values are class `assumed`,
the eye point is `derived (assumed input)`, and both the header and §4 say so.

### 9. "`MECHANICS.md` does not carry `RVehicleWeapon.OverrideCamera`" — **CONFIRMED**
`grep -c OverrideCamera Research/BatmobileGrab/MECHANICS.md` → **0**. The member exists as
`RVehicleWeapon.OverrideCamera` 0x0930 `NameProperty` = `"CustomCamera"` in `OFFSETS.md:234` and
`WEAPONS.md:993`; `BMSDK_OFFSETS.json` carries only the FOV variants. Fixed: the camera paragraph
cites `WEAPONS.md`/`OFFSETS.md` and names it a `NameProperty` with default `CustomCamera`.

### 10. "§12 row oversimplifies the bone attribution" — **CONFIRMED**
Slot 11 = 12,470 `Batmobile_Chassis` + 544 `CockPit_Mesh`; slot 10 = **14,136 `CockPit_Mesh` +
13,198 `Batmobile_Chassis`** — the dash is mostly `CockPit_Mesh`. Fixed: the tracker line gives both
splits.

### 11. Review's "not an issue" list — **CONFIRMED as written**
The card's substance was right: seat slot 11 / dash slot 10, `Driver` hip 0.8647 (0.8447 m above
ground with ground 0.02), 24 mm above the cushion, hip-to-liner 1.1014, "no yoke" proved by a
4-face hand box, the 12-mesh claim (12 rows in `MESHES.md`), and the material values
(`Glass_Opacity 1.2000`, `Glass_Reflectivity 0.8000`, `Glass_Roughness 1.1000`, `glass_smudges
0.2000`, seat `EmissiveMultiply 15.0000`, `Emissive → Batmobile_V3_Int_Cockpit_E`). All reproduce.

## Incidental finding while regenerating
The old roof sentence ("Ray straight up from the Driver") was not literally true for the whole
profile: a ray from the hip at z −1.35 / −0.25 / −0.80 hits the seat first (y 0.969 / 0.970 / 0.977).
The table's values were produced from y 1.40, so the table was right and the sentence was imprecise.
The generated page states the ray origin (y 1.40) and, for the centre strip, prints what the 63
sweep rays hit first (`Batmobile_Worn_NoRain` 48, `Batmobile_V3_Cockpit_MIC` 15, glass 0) instead of
claiming "never glass" without a count.

## Files changed
| file | change |
|---|---|
| `Tools/scripts/grab_cockpit.py` | **new** generator + `--check` (PSKX rays, slot/bone counts, sockets, materials, mesh list) |
| `Research/BatmobileGrab/COCKPIT.json` | **new**, 13,960 B — machine source for every value, with classes |
| `Research/BatmobileGrab/COCKPIT.md` | **regenerated** from the script (pre-rework copy: `tmp/freebuff/reports/COCKPIT.before-g1-19-rework.md`) |
| `Research/BatmobileGrab/README.md` | `COCKPIT.md` row updated (says generated + `derived (assumed input)`); `COCKPIT.json` row added |
| `GRAB_BACKLOG.md` §12 | the `G1-19` line only: adds the script/JSON, the bone splits, 0.3188 × 0.1512, 1.043-face panel, `assumed` eye |
| `MODLOG.md` | `G1-19 rework (intended)` + `G1-19 rework — done` |

No other file was touched. The pre-change MODLOG entry was appended before the script or the page
was written.

## Check output (verbatim)

`python Tools/scripts/grab_cockpit.py --check` → exit 0:

```
OK: 65 sockets, Driver (-0.0025, 0.8647, -1.0654) on Batmobile_Chassis; seat 13,014 faces (cushion y 0.8407) / tub 27,334 / screen 100 faces 0.3188 x 0.1512 m / glass 3,532; roof liner 1.9661 (hip-to-liner 1.1014); hand box 4 faces; panel 1043 faces; 12 mesh exports; MD regenerates identical
```

`python -m py_compile Tools/scripts/grab_cockpit.py` → clean (no output).

`python Tools/scripts/t_rows.py check` (translation rows untouched; run to show the ledger is
unaffected) → exit 0:

```
ledger 198 rows | edit 16 next 40 keep 60 epe 26 re-read 0 blocked 13 out 36 superseded 7 | edits 35 over 16 rows
check ok
```

`python Tools/scripts/status_audit.py --check` → exit 0: `STATUS.md is current`.

## Tamper test (caught and reverted)

1. `COCKPIT.json` → `eye.builds[0].eye[1] = 1.700` (the old typed eye y):

```
FAIL
  - stored JSON differs from a fresh build (keys: eye)
  - COCKPIT.md is not the current generator output
```
exit 1.

2. appending `| hand edit | 0.314 |` to `COCKPIT.md`:

```
FAIL
  - COCKPIT.md is not the current generator output
```
exit 1.

Both restored from `tmp/freebuff/reports/_cockpit.{json,md}.bak`; `--check` returned the OK line
above and `sha1sum` of the restored files equals the backups.
