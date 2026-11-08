# Review — G1-19 · Cockpit and driver placement

Reviewer: independent (did not write the card). Date 2026-10-29.
Scope: `GRAB_BACKLOG.md` §0.5 and the G1-19 card (lines 530–537), the §12 row (line 1287),
`MODLOG.md` §"G1-19 · Cockpit and driver placement — done" (lines 8594–8650),
`Research/BatmobileGrab/COCKPIT.md` (the only Out path), and the inputs it names
(`SLOTS.json`, `BONES.json`, `SOCKETS_JC3.json`, `MATERIALS.md`, `Working/TrueScale/stations.json`)
plus the raw mesh `Working/Appearance/grab/Playable_Batmobile_SF/SkeletalMesh3/Batmobile_V2.pskx`.
Read-only: nothing under `Research/`, `Tools/`, `Working/`, `GRAB_BACKLOG.md`, `MODLOG.md` or the
game install was written; no game was launched. This report is the only file written.

## VERDICT

**needs rework** — and the rework is mechanical, not a re-measurement. The card's *content* is
largely right: I independently re-derived the load-bearing numbers from the PSKX through the one
transform and they reproduce (seat 0.8407, liner 1.966, profile 1.884…2.001, windscreen 0.849,
1.88 m eye line 0.750, empty hand-box 4 faces, every face/bone split). What fails is the
**verification discipline the backlog requires**: the card has **no script, no `--check`, no JSON**
— my step 3 could not be performed because the command does not exist — so every count in
`COCKPIT.md` is hand-typed (R11, §0.2 step 5), and several of those typed numbers are wrong or
unreproducible: the centre-screen box (0.314 × 0.145 vs the panel's own 0.318 × 0.151), the
"required-anchor" claim (`DriverAnimOrigin` is not in that list), a "level ray" that is not level,
a "midpoint" that no midpoint reproduces, and three face/area counts (728 faces / 486 cm²,
3,310 + 3,862, 7,528) that no stated selection rule reproduces. Add `grab_cockpit.py --write/--check`
so the tables are generated, correct the items below, and the card is done.

## Check output (verbatim)

The card has **no `--check` command and no script**. What the card's Done names is a statement
(seat, yoke, dashboard identified by slot and bone; `Driver` position + headroom in metres), and
§12 names only `Research/BatmobileGrab/COCKPIT.md` + the MODLOG entry. Established by:

```
$ ls Tools/scripts/ | grep -i cockpit
```
(no output, exit status 1 — there is no `grab_cockpit.py`, `jc3cockpit.py` or similar)

```
$ ls Research/BatmobileGrab/ | grep -i cockpit
-rw-r--r-- 1 User 197121 9400 Oct 25 09:42 COCKPIT.md
```
(no `COCKPIT.json`)

The MODLOG's "**Verified:** the whole battery is green" lists other cards' gates (`grab_anims`,
`grab_bones`, `grab_slots`, `grab_sockets`, `status_audit`, `grab_model.py check`, `py_compile`) —
none of them reads `COCKPIT.md` or re-derives a single number in it, so it is not evidence for
this card. `COCKPIT.md` §7 "How to re-measure" is a pseudocode recipe, not a program; it cannot be
run.

Substitute verification I ran (read-only, in memory, no files written): `psk2rbm.read_pskx` +
`PSKX` skeleton → vertices through `to_jc3 × 0.01 + offset`, Möller–Trumbore rays, per-face
material = `FACE3200.m`, dominant bone = `pskx_parts.face_bones`. The card's headline values
reproduce:

```
vertical up at Driver (x=-0.002546,z=-1.06536) from y=1.0
   y=1.9661  Batmobile_Worn_NoRain (slot 18)
   y=1.9914  Batmobile_V3_Mainbody_NEW_MIC (slot 2)
vertical down at Driver from y=1.40
   y=0.8407  BatmobileV3_Cockpit_Seat (slot 11)
   y=0.7289  Batmobile_V3_Cockpit_MIC (slot 10)
z=-1.35 1.8838 (liner)   z=-1.25 1.9010 (Cockpit_MIC)   z=-1.20 1.9277 (liner)
z=-1.00 1.9857 (liner)   z=-0.95 2.0007 (liner)         z=-0.80 1.8078 (seat)
forward -z from mean eye (-0.003,1.655,-1.065): 0.8487 m, Batmobile_V3_Glass_INST
forward -z from 1.88 m eye (-0.003,1.705,-1.065): 0.7503 m, Batmobile_V3_Cockpit_MIC
faces fully inside |x|<0.17, y1.00..1.30, z-1.60..-1.10: 4
   y 0.90..1.00: 24   y 1.00..1.10: 0   y 1.10..1.20: 0   y 1.20..1.30: 4
```

## Issues

### 1. No script and no `--check` — every count in the doc is typed (R11, §0.2 step 5)

`Research/BatmobileGrab/COCKPIT.md` is a hand-written page. It carries tables of counts — 13,014 /
27,334 / 3,532 / 524 / 100 faces; 12,470 + 544, 14,136 + 13,198, 1,716, 524 bone splits; 728 faces
/ 486 cm²; 3,310 + 3,862; 7,528; 4 faces; 404 cm² — and none of them is produced or checked by a
command. R11 says "tables of counts in new docs come from a script with `--check`", and §0.2 step 5
says "Write scripts, not hand edits: every value must be re-derivable by a command". §0.5 says
breaking a rule fails the task. The card's Done is a statement, not a check, so nothing in the
project would notice if the mesh changed and this page went stale (the very failure mode the rules
exist to prevent — compare G1-17/G1-18/G1-21, which all ship a `--check`).

This is not pedantry here: two of the typed numbers are already wrong (§5, §6) and three more are
not reproducible (§7), which a `--check` would have caught.

### 2. "Both are in the required-anchor list" — `DriverAnimOrigin` is not (wrong claim)

`COCKPIT.md` §2, last line: "Both are in the required-anchor list of `SOCKETS_JC3.json`
(`required_anchors` 13/13 present)." `SOCKETS_JC3.json` `required_anchors.names` is
`["Driver", "CannonMuzzle", "ChainGunMuzzle", "RiotSuppressorMuzzle", "MissileL", "MissileR",
"Afterburner", "Afterburner_Front", "WinchOrigin", "BattleModeSpotLight", "BootLight",
"Dashboard_Light", "Headlight_Centre"]` — 13 names, `Driver` yes, **`DriverAnimOrigin` no**. Only
one of the two is required. (The 13/13 figure itself is correct.)

### 3. "a level ray from the eye passes at y 1.545" — that is the 13.5° sightline, not a level ray

`COCKPIT.md` §4: "the dash lip at z −1.52 (y 1.31…1.40) does not occlude it (a level ray from the
eye passes at y 1.545)". A level ray from (−0.003, 1.655, −1.065) stays at y = 1.655 by definition;
1.545 is where the **13.5° sightline to the screen centre** crosses z −1.52
(1.655 − 0.166 × 0.455/0.692 = 1.5458). The conclusion (no occlusion) is right; the sentence
misnames the ray it quotes.

### 4. "1.065 m behind the car's midpoint toward the nose" — contradictory, and no midpoint gives 1.065

`COCKPIT.md` §2. The nose is at −z, so from a midpoint at z 0 the Driver is 1.065 m **ahead of**
the midpoint, not behind it. And no natural midpoint is at z 0: `stations.json` `body_bbox` is
z −3.42…3.605 → midpoint **+0.0925** (driver 1.158 m ahead of it), and the wheelbase midpoint
(−2.570 + 2.4589)/2 = **−0.0556** (driver 1.010 m ahead). 1.065 is simply |z| from the assembly
origin. Say "z = −1.065 (assembly origin), 1.505 m behind the front axle (z −2.570)" — the front
axle figure checks out (−1.0654 − (−2.570) = 1.5046).

### 5. The centre-screen box is 4–6 mm off the panel it says it describes

`COCKPIT.md` §1 and §6: "centre panel of slot **12** … (100 faces, 404 cm²) … Centre screen:
x ±0.157 (0.314 m wide), y 1.416…1.561 (0.145 m tall), z −1.851…−1.662". Measured on the 100
slot-12 faces (area reproduces exactly at 404 cm²): **x ±0.159, y 1.410…1.561, z −1.852…−1.658**
→ **0.318 × 0.151 m**. The width/height are quoted to the millimetre, so a 4–6 mm error is not
rounding, and 0.314 × 0.145 is repeated in the §12 row. Either measure the panel you name or state
the subset rule that gives 0.314 × 0.145 (see §7 for the same problem elsewhere).

### 6. `rotation identity` hides that the socket basis is rolled 90° (orientation, i.e. ANI-9's seated pose)

`COCKPIT.md` §2 gives the socket's rotation as "identity (`rotation_missing: true`)" and quotes only
`forward_jc3` = (0, 0, −1). The same record has **`up_jc3` = (−1, 0, 0)** and
**`right_jc3` = (0, 1, 0)`** — the socket's up axis is the car's lateral axis. That is true of the
*relative* socket rotation (null, so it inherits the bone bind rotation) and the doc is not lying,
but a modder who builds the seated pose from the full `Driver` basis will lay the driver on their
side; the doc never says so. The eye point itself is computed in world axes and is fine — this is
an omission, not an arithmetic error. It belongs in §2 with a sentence ("use world up; the socket's
own up is lateral"), because ANI-9 is exactly the requirement that depends on it (R5: behaviour,
not member name).

### 7. Three subset counts are not reproducible because no selection rule is given

`COCKPIT.md` §1: "driver-facing panel of slot **10** (**728** faces, **486 cm²**)", "dash front face
z −1.50…−1.60 at y 1.30…1.50 (**3,310 + 3,862** centre-strip faces)", "its top lip band
(z −1.56…−1.45, y 1.25…1.45) is **7,528** faces all on `Batmobile_Chassis`"; §1 seat "bolsters/tub
walls … (**1,036** faces)". The slot totals and bone splits reproduce exactly (§ Spot-checks), but
these sub-selections do not, under either obvious rule:

| claimed | all-3-vertices-inside | face-centroid-inside |
|---|---|---|
| slot-10 panel 728 faces / 486 cm² (x ±0.328, y 1.317…1.560, z −1.865…−1.521) | 5,114 faces / 4,952 cm² | 5,540 / 7,763 cm² |
| dash front 3,310 + 3,862 (z −1.60…−1.50, y 1.30…1.50) | 3,850 (slot 10 only) | — |
| lip band 7,528 (z −1.56…−1.45, y 1.25…1.45) | 2,694 / 822 cm² | 2,870 |
| seat bolsters 1,036 (x 0.20…0.30, y 1.00…1.27, z −1.45…−1.20) | 1,022 | 830 (±0.20…0.30) |

They may well be "faces of a connected flat island" or "faces in a screen-shaped quad" — but the
doc does not say, so they are unverifiable as written and a reader cannot tell a typo from a rule.
Either define the selection or drop the counts; the `--check` from §1 should compute them.

### 8. The eye point's anthropometry is an uncited assumption presented as `derived` (R4)

`COCKPIT.md` §4: seated eye height 0.79 m (1.76 m adult) / 0.84 m (1.88 m reference), sitting
height 0.91 / 0.97 m — "standard adult anthropometry". R4's value classes are decoded / derived /
class / epe / read, and "assumed is not buildable". These are assumptions with no source named
(no standard, table or document), so the eye point should be marked `assumed` (or the source
cited) rather than `derived`, however clearly the arithmetic is shown. The doc does state the
assumption "so it travels with the number", which is the right instinct — just not the class R4
asks for, and ANI-9 is going to lean on it.

### 9. `MECHANICS.md` does not carry `RVehicleWeapon.OverrideCamera` (the citation is wrong)

`COCKPIT.md` §4: "`MECHANICS.md` carries no camera/eye property (only `RVehicleWeapon.OverrideCamera`
and an AnimSet named `Camera`, neither of which is an eye point)." The negative is true —
`grep -i camera Research/BatmobileGrab/MECHANICS.md` returns exactly one line, the AnimSet
`Camera` row (line 1235) — but there is **no `OverrideCamera`** anywhere in
`Research/BatmobileGrab/` (`grep -rn OverrideCamera` finds only `bOverrideCameraFOV`,
`OverrideCameraFOVAngle`, `OverrideCameraFOVTime` in `BMSDK_OFFSETS.json`). The member is
`OverrideCameraFOVAngle`, and it lives in the BmSDK dump, not in `MECHANICS.md`.

### 10. §12 row oversimplifies the bone attribution

`GRAB_BACKLOG.md:1287`: "seat = slot 11 / dash = slot 10 on `Batmobile_Chassis`". The doc's own
table says the seat is 12,470 `Batmobile_Chassis` + 544 `CockPit_Mesh`, and the dash slot 10 is
**14,136 `CockPit_Mesh` + 13,198 `Batmobile_Chassis`** — the dash is mostly `CockPit_Mesh`, so the
row's single bone is wrong for it. (Both splits re-derived; see Spot-checks.)

### 11. Not an issue, recorded so it is not re-opened

- The card's Done is met in substance: seat slot 11 + bones, dash slot 10 + bones, yoke answered as
  "absent" with a measured hand-box (4 faces) rather than guessed, `Driver` position in metres and
  headroom 1.101 m hip-to-liner plus two eye-point variants. "No yoke" is the correct R5 answer
  (the card said "identify the faces/slots of … yoke"; proving absence is stronger than naming a
  keyboard-like mesh that does not exist).
- `0.845 m above the ground` checks out (0.864732 − 0.020 ground = 0.8447).
- The 12-mesh claim in §6 is right: `MESHES.md` lists 12 SkeletalMeshes, 11 of them
  Destroyed/Fire/Jokerfied/MK2/Batwing, none an interior.
- Material values quoted (`Glass_Opacity 1.2000`, `Glass_Reflectivity 0.8000`,
  `Glass_Roughness 1.1000`, `glass_smudges 0.2000`, seat `EmissiveMultiply=15.0000` with
  `Emissive → Batmobile_V3_Int_Cockpit_E`) are exactly `MATERIALS.md:972–973`.

## Spot-checks

| # | value in the doc | where verified | result |
|---|---|---|---|
| 1 | `Driver` `position_m` **(−0.0025, 0.8647, −1.0654)**, bone `Batmobile_Chassis`, relative (121.9658, 0.25, 84.2500) cm, rotation null | `SOCKETS_JC3.json` → `sockets[Driver]`: `position_m` **(−0.002546, 0.864732, −1.06536)**, `relative_location_cm` (121.965767, 0.25, 84.249992), `relative_rotation_raw: null`, `rotation_missing: true` | **match**; and 0.864732 − 0.8407 = **0.0240 m**, the doc's "24 mm above the cushion". |
| 2 | cushion top **y 0.8407** under the Driver; roof liner **1.9662**, skin **1.9914**; hip-to-roof **1.101 m** | my ray-cast on `Batmobile_V2.pskx` through `to_jc3 × 0.01 + offset`: down → **0.8407** (slot 11), up → **1.9661** (slot 18) then **1.9914** (slot 2); 1.9661 − 0.8647 = **1.1014** | **match** to 0.1 mm (1.9661 vs 1.9662). |
| 3 | roof profile −1.35 **1.884**, −1.25 **1.901**, −1.20 **1.928**, −1.065 **1.966**, −1.00 **1.986**, −0.95 **2.001**, −0.80 **1.808** | same ray-cast at each z: 1.8838 / 1.9010 / 1.9277 / 1.9661 / 1.9857 / 2.0007 / 1.8078, first hits on the materials the table names | **match** at every column. |
| 4 | windscreen **0.849 m** ahead of the mean eye (z −1.914); 1.88 m eye line meets the cowl at **0.750 m**; side windows **x ±0.30, y ≈ 1.71** | ray −z from (−0.003, 1.655, −1.0654) → **0.8487 m** at z −1.9141 on `Batmobile_V3_Glass_INST`; from y 1.7047 → **0.7503 m** on `Batmobile_V3_Cockpit_MIC`; lateral ray at y 1.71, z −1.10 → glass at x **0.294 / 0.303** | **match** (0.849 / 0.750 / ≈0.30). |
| 5 | slot face counts **13,014 / 27,334 / 3,532 / 524 / 100** and bone splits **12,470 + 544**, **14,136 + 13,198**, **1,716** on `CockPit_Mesh` | `FACE3200.m` counts per material and `pskx_parts.face_bones` on the same file | **match** exactly on all six. |
| 6 | slot-12 centre screen **100 faces, 404 cm²**, x ±0.157, y 1.416…1.561, z −1.851…−1.662 | same file: 100 faces, area **0.0404 m² = 404 cm²** but bbox **x −0.159…0.159, y 1.410…1.561, z −1.852…−1.658** | **area matches; bbox does not** (see Issue 5). |
| 7 | hand-box empty: **4 faces** of any material; **24** at y 0.90…1.00, none at 1.00…1.20, **4** at 1.20…1.30 | all-vertices-inside test on every face of every material | **match** exactly (4 / 24 / 0 / 4). |
| 8 | glass `Glass_Opacity 1.2000`, `Reflectivity 0.8000`, `Roughness 1.1000`, `smudges 0.2000`; seat `EmissiveMultiply=15` | `MATERIALS.md:972` and `:973` (instance parameter cells) | **match**. |
