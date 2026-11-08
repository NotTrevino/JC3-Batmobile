# G1-20 rework — skins and variants inventory

Date: 2026-10-29. Input: `tmp/freebuff/reports/review-G1-20.md` (verdict "needs rework").
Task: verify every review issue against the data, fix the confirmed ones per `GRAB_BACKLOG.md` §0.5
(R1–R14), reject any that are wrong, re-run the card's `--check`, tamper-test it.

## STATUS: **done — every issue verified; ten confirmed and fixed, one confirmed with two of the review's own numbers corrected; none rejected**

- `Research/BatmobileGrab/VARIANTS.md` is now **generated** by `Tools/scripts/grab_variants.py`.
  `--check` re-counts every table from `objects.jsonl`, joins `MESHES.md` (geometry rows) and
  `WEAPONS.md` (the gadget/projectile class list and its field-comparison sentence), asserts the
  set arithmetic on all six tables, and fails on any difference between the file and the render.
- Five set-difference counts in the old page were wrong (as the review said), the two Joker sets
  were internally inconsistent with their own totals, and the page carried claims the record does
  not support ("13 decoded properties", "a handful of offsets", "0 of 332 fields differ", a
  non-existent `Hydra` texture, a false Funhouse material parenthetical). All are gone.
- No game launched, nothing written into `D:/Games`, no shared game module touched, no commit.
- Review issue 7 is confirmed in substance but its own counts are partly wrong, and its
  "MK2 has no 0x2158" is wrong — both corrections are recorded below and in the page.

## Check output (verbatim)

```
$ python Tools/scripts/grab_variants.py --check
OK: 4 variants, 5,490 / 5,534 / 3,388 / 5,584 records; sockets 65/55/64/63; materials 78/80/69/84; textures 92/95/100/102; skin exports 20,151,210/20,034,142/20,385,512/20,385,512
OK: sim 0 differing tags in all four; rigs 28/28/17 rows, MaterialType 18/18; gadgets 10/10/5/10; tag diffs vs V2 86/77/87
OK: VARIANTS.md matches the re-derived render (340 lines)
EXIT=0
$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 40 keep 60 epe 26 re-read 0 blocked 13 out 36 superseded 7 | edits 35 over 16 rows
check ok
EXIT=0
$ python Tools/scripts/status_audit.py --check
STATUS.md is current
EXIT=0
```

`t_rows.py`/`status_audit.py` were run because the §12 row changed; the translation ledger and
`STATUS.md` are unaffected and still green.

**Tamper test** (one record count edited by hand in the stored page, then `--check`):

```
FAIL
  - VARIANTS.md differs from the render (2 changed lines; first: -| **V2** (reference) | `Playable_Batmobile_SF` | `Batmobile` (3,905 B) | 5,491 | `Batmobile_Archetypes.Vehicle` |)
TAMPER_EXIT=1
```

after `--write`, the three OK lines above again. (An earlier attempt that tried to tamper with a
phrase the page no longer contains was a no-op — the test above is the real one.)

## Per-issue

### 1. No script, no `--check`; every count typed (R11) — **CONFIRMED**, fixed
Evidence: `Tools/scripts/` had no `*variant*` script and `Research/BatmobileGrab/` no
`VARIANTS.json`; the page's Out was the `.md` alone. The MODLOG's "independent assertion pass
(30/30 … ALL OK)" appears nowhere on disk, and at least five of the counts it claims to check were
wrong, so it cannot have passed. That sentence is withdrawn in the new MODLOG entry, replaced by a
command and its output.
Fix: `Tools/scripts/grab_variants.py --write/--check` (records, sockets, materials, textures,
gadgets/projectiles, the `RVehicleBatmobile` tag diff, the `VehicleLights` rig rows, the 0-tag sim
diff, mesh export sizes from the `SkeletalMesh` record sizes). Every number in the page is rendered
by the script.

### 2. Joker materials "missing 38" — **CONFIRMED**, fixed
Evidence (independent probe, no import of the new script):

```
materials V2 78 Joker 69 extra 26 missing 35
```
so 38 contradicted the page's own table (78 − 38 + 26 = 66 ≠ 69). The page now prints **35**, and
the five EMP materials are listed one by one (`EMP_BuildUp`, `EMP_Burst_V02_Stage_01…04`) and the
battery names are the real `Stagg_Battery_01_MAT` / `Stagg_Battery_Energy_01_MAT`.

### 3. Joker textures "extra 32 / missing 24", `Hydra` — **CONFIRMED**, fixed
Evidence: 92 → 100 with **31 extra, 23 missing** (92 − 23 + 31 = 100). No `Hydra` `Texture2D`
exists in any of the four packages (the material is `Hydra_Trails_M`); the extra list now ends
`…contrails`, `TXT_Helicopter_Police_Blades`.

### 4. Funhouse textures "extra 26" — **CONFIRMED**, fixed
Evidence: `textures V2 92 Funhouse 102 extra 24 missing 14` → 92 − 14 + 24 = 102; the old 26 gave
104. The false parenthetical ("the Jokerfied set, same as Joker minus the Batwing/Hydra/cameo
extras") is replaced by the measured nesting: Funhouse's 24 extras are **all of** Joker's 31, and
the 7 it lacks are named (`Batwing_Carrier_D/_E/_N`, `Core_Mask2`,
`TXT_Helicopter_Police_Blades`, `contrails`, `gradientNoWrap`).

### 5. Funhouse materials "minus `Game_Cameo_Squirting_FLOWER_MAT`" — **CONFIRMED**, fixed
Evidence: that material **is** in Funhouse's 13 extras. The page now prints the 13 (a subset of
Joker's 26) and the 13 of Joker's 26 that Funhouse lacks (Batwing pair, Hydra pair, police rotor,
`Engine_Distortion`, `Dusty_hit_01_4x4`, `Falling_Dust_MAT` + `_INST`, `Smoke_02_SubUV_16_unlit`,
`contrail_m`, `Simple_GlowFade`, `LensFlare_OWStreetLightReflection_SOFT_INST`) — all generated.

### 6. "25 of V2's 28 rows bind a `MaterialType`" — **CONFIRMED**, fixed
Evidence: `V2 rig rows 28 with MaterialType 18`. The `MaterialType` row now reads **18 of 28** for
V2/MK2/Funhouse and **0 of 17** for Joker, and a row-by-row rig table shows which rows carry one
(`ChainGunMuzzle`, both `BattleModeSpotLight` rows, `HeadLight1a/2a/1b/1c/2b/2c` and `BootLight` do
not).

### 7. "a handful of offsets" / "identical rows" — **CONFIRMED** (substance); two of the review's own figures corrected
Evidence (re-derived): MK2 has **58** non-struct tags carrying a different value, Funhouse **59**;
add the 28 `VehicleLights` structs (each carries an inner export reference that resolves elsewhere)
and the totals are **86 / 87 of 135** tag offsets. Joker: 59 non-struct (50 references + 9 unnamed
floats) + 17 rig structs + `ExplosiveImpactScreenShake` = 77 of the 99 offsets it shares with V2.
So "a handful" was wrong by an order of magnitude and "identical rows" is only true of bone/`Type`/
`MaterialType`. The page now prints the full reference table and says the rows are identical in
those three fields, not as serialised.
**Review corrections:** (a) the review's "60 offsets differ for MK2" does not reproduce — the same
rule that gives the review's Funhouse figure (59) gives 58 for MK2; 86 is the count including the
rig structs. (b) "MK2 has no 0x2158" is wrong: `0x2158` is present in all four objects and MK2
carries V2's own value −105; Funhouse (−56) and Joker (−57) are the ones that differ. The page's
table shows this.
**Not claimed:** why the export indices differ — no repo file records the export table, so that is
UNKNOWN.

### 8. "13 decoded properties" — **CONFIRMED**, fixed
Evidence: the vehicle object's 35 named tags are 7 named properties + 28 `VehicleLights` rows;
MECHANICS.md lists the audio objects separately (`AkEvent` ×4, `AkPlayerVehicleSoundInfo`,
`AkVehicleSound`). The page's table now says named tags / named properties / rig rows separately,
and a sentence points out that the audio objects are listed separately in `MECHANICS.md` and that
the old "decoded properties" count mixed the two.

### 9. "0 of 332 fields differ" — **CONFIRMED**, fixed
Evidence: `WEAPONS.md:94` reads "**0 of 1065 field comparisons differ.** No shared object is retuned
between the base, MK2, Funhouse and Joker packages…"; the 332 appears in its verdict line ("0 of 332
fields compared across the 18 multi-variant objects"). The page now quotes the 1,065 sentence
verbatim (parsed from `WEAPONS.md`, not typed) and notes the 332 phrasing; which total counts fields
is UNKNOWN, but both say 0 differ, which is what the page relies on.

### 10. Gadget/projectile counts — **CONFIRMED**, fixed
Evidence (by WEAPONS.md's own class list): V2/MK2/Funhouse each carry **10 gadget objects and 8
projectile objects** (the Heavy Cannon alone contributes four projectiles); Joker carries **5**
gadgets and **2** projectiles. Joker's sixth "gadget" is `Default__RBatmobileMissileLauncherJoker`,
a class default, and `RVehicleThreatComponent ThreatComp` is a threat component, not a gadget (R5:
a weapon-adjacent class name is not a weapon). The page prints all names and the `Default__` /
`ThreatComp` caveats; the invariant list fails if a `Default__` is ever counted again.

### 11. "Not an issue — recorded so it is not re-opened" — **CONFIRMED as accurate**
Re-derived independently: records 5,490 / 5,534 / 3,388 / 5,584; sockets 65 / 55 / 64 / 63 with the
three exact name lists; material totals 78 / 80 / 69 / 84 and texture totals 92 / 95 / 100 / 102;
mesh rows (verts, LODs, bones incl. 220, 19/19/20/20 materials, sizes, export bytes) match
`MESHES.md` and the record sizes; the sim object is 2,328 B / 37 tags with 0 differing tags in all
four; vehicle-object sizes 3,905 / 3,905 / 2,239 / 3,905 and the 8 MK2 / 9 Funhouse small-integer
pairs. Also re-derived and true: the 11 `_Std_*` packages (4 records each, `Std_6` 92 with
`Batmobile_Stage6`).

## Spot-checks

| value in the page | where verified | result |
|---|---|---|
| Joker materials 69, extra 26, **missing 35** | `objects.jsonl` set difference of `Material` + `MaterialInstanceConstant` names | **35** (old 38 could not close 78 − 38 + 26 = 69) |
| Funhouse textures 102, **extra 24**, missing 14 | same pass, `Texture2D` | **24** (92 − 14 + 24 = 102 ✓) |
| V2 rig **28** rows, **18** with `MaterialType` | `RVehicleBatmobile` `VehicleLights` structs, `MaterialType` byte on each | 28 / **18** (old "25" wrong) |
| Joker gadgets **5**, projectiles **2** | gadget/projectile classes from WEAPONS.md's table, per package | 5 / 2 (plus one `Default__`, one `ThreatComp`) |
| MK2 LOD0 **297,566**, 175 bones, 19 materials | `MESHES.md:17` row for `Batmobile_MK2_Skin` | exact |
| `0x2158` = −105 (V2), −105 (MK2), −57 (Joker), −56 (Funhouse) | vehicle-object tags, all four packages | exact — and it refutes the review's "MK2 has no 0x2158" |

## Files changed

| file | change |
|---|---|
| `Tools/scripts/grab_variants.py` | **new** — generator + `--check`; counts every table from `objects.jsonl`, joins `MESHES.md` / `WEAPONS.md`, asserts the set arithmetic, the one-skin-per-package rule, the 28/28/17 rigs, 0 differing sim tags, no `Default__` gadget, and byte-diffs the page |
| `Research/BatmobileGrab/VARIANTS.md` | **regenerated** (340 lines) — corrected counts with every set closing, full extra/missing name lists, the row-by-row rig table, the full differing-reference table, Joker's 9 unnamed floats, and UNKNOWN where the record cannot settle a claim |
| `tmp/freebuff/reports/VARIANTS.before-g1-20-rework.md` | pre-rework snapshot (evidence, not a deliverable) |
| `GRAB_BACKLOG.md` | **§12 `G1-20` line only** — now cites the generator, the closing set arithmetic, the rig/`MaterialType` counts, 10/10/5/10 gadgets and 8/8/2/8 projectile objects |
| `MODLOG.md` | intended-change entry before the edit, then "G1-20 rework — done" with the check outputs, the tamper test, and the withdrawn "30/30" claim |

Revert: delete `Tools/scripts/grab_variants.py` and restore `VARIANTS.md` from the snapshot above;
the backlog and MODLOG edits are appends.
