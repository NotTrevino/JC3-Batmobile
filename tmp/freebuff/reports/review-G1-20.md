# Review — G1-20 · Skins and variants inventory

Reviewer: independent (did not write the card). Date 2026-10-29.
Scope: `GRAB_BACKLOG.md` §0.5 and the G1-20 card (lines 537–542), the §12 row (line 1288),
`MODLOG.md` §"G1-20 · Skins and variants — done" (lines 8660–8730),
`Research/BatmobileGrab/VARIANTS.md` (the only Out path), and the sources it names
(`MESHES.md`, `MATERIALS.md`, `MECHANICS.md`, `WEAPONS.md`) plus the machine source
`Research/BatmobileGrab/objects.jsonl`.
Read-only: nothing under `Research/`, `Tools/`, `Working/`, `GRAB_BACKLOG.md`, `MODLOG.md` or the game
install was written; no game was launched. This report is the only file written.

## VERDICT

**needs rework** — the inventory's skeleton is right (record counts, socket diffs, material/texture
totals, mesh LOD and export sizes, the identical sim, the Joker vehicle-object diff), but the
**set-difference counts that are the card's actual product are wrong in 5 places**, two of them
internally inconsistent with the totals printed in the same table, and the card has **no script and
no `--check`** — my step 3 could not be performed because the command does not exist. The MODLOG's
"independent assertion pass (30/30 … **ALL OK**)" is nowhere on disk, and the data contradicts at
least five of those 30 assertions, so it cannot stand as evidence. Every number in `VARIANTS.md` is
hand-typed (R11, §0.2 step 5). The fix is mechanical — ship `grab_variants.py --write/--check` and
correct the six items below; the raw facts are all recoverable from `objects.jsonl` in seconds (I
re-derived them).

## Check output (verbatim)

The card has **no `--check` command, no script and no JSON**. §12 names only
`Research/BatmobileGrab/VARIANTS.md` + the MODLOG entry; the card's Done is a statement ("each
variant has a diff table; D-5 can be answered from it"). Established by:

```
$ ls Tools/scripts/ | grep -i variant
```
(no output, exit status 1 — there is no `grab_variants.py`)

```
$ ls Research/BatmobileGrab/ | grep -i variant
-rw-r--r-- 1 User 197121 11003 Oct 25 10:06 VARIANTS.md
```
(no `VARIANTS.json`)

`MODLOG.md:8714–8720`: "every table in `VARIANTS.md` re-derived from `objects.jsonl` by an
independent assertion pass (30/30: socket, material, texture, record and gadget counts per package,
the 0-tag sim diff, the vehicle object name/size/tag counts, the mesh export sizes) — **ALL OK**".
No such pass exists on disk (nothing in `Tools/scripts/` reads `VARIANTS.md` or emits those 30
assertions), and it cannot have passed: the material/texture/gadget counts it claims to check are
wrong in the doc (Issues 2–5, 9–10).

Substitute verification I ran (read-only, in memory): one pass over `objects.jsonl`, grouping the
four vehicle packages by class and name, then set-differencing against `Playable_Batmobile_SF`.
Results are in the Spot-checks table; the mismatches are the Issues below.

## Issues

### 1. No script, no `--check`; every count typed (R11, §0.2 step 5)

`VARIANTS.md` is a hand-written page whose §1–§7 tables are all counts and set differences. R11:
"tables of counts in new docs come from a script with `--check`"; §0.2 step 5: "every value must be
re-derivable by a command". Nothing here is. G1-17/G1-18/G1-21 all ship a `--check`; this card does
not, and the "30/30 ALL OK" sentence in the MODLOG is the only claim of verification — an
unreproducible one. Five of the numbers below are wrong precisely because nothing recomputes them.

### 2. Joker materials: "missing 38" — actually 35, and 38 contradicts the table's own totals

`VARIANTS.md` §3, Joker row: count **69**, extra **26**, missing **38**. Data: V2 78, Joker 69,
Joker-only 26, V2-only **35**. The doc's own arithmetic fails: 78 − 38 + 26 = **66**, not 69. The
missing cell also compresses five EMP materials into "both EMP burst stages" (V2 ships
`EMP_BuildUp` + `EMP_Burst_V02_Stage_01…04`) and names "`Stagg_Battery_01/02`" where the two real
names are `Stagg_Battery_01_MAT` and `Stagg_Battery_Energy_01_MAT`. Correct count: 35 (the 35 are
listed in my set pass; e.g. the doc's list omits nothing, but the number is 3 too high).

### 3. Joker textures: "extra 32 / missing 24" — actual 31 / 23; one listed texture does not exist

`VARIANTS.md` §4, Joker row: **100**, extra **32**, missing **24**. Data: 100 total, **31** extra,
**23** missing (92 − 23 + 31 = 100 ✓). The extra cell counts a `Hydra` texture — there is no
`Hydra` Texture2D in any of the four packages (Hydra appears as the *material* `Hydra_Trails_M`);
the real extra list is 31 names ending `…contrails`, `TXT_Helicopter_Police_Blades`. The missing
cell says 24 but enumerates 23 real names.

### 4. Funhouse textures: "extra 26" — actual 24, and the totals do not add up

`VARIANTS.md` §4, Funhouse row: **102**, extra **26**, missing **14** = 92 − 14 + 26 = **104** ≠ 102.
Data: extra **24**, missing 14 → 102 ✓. The parenthetical ("the Jokerfied set, same as Joker minus
the Batwing/Hydra/cameo extras") is also wrong: Funhouse **does** ship the cameo textures
(`Game_Cameo_Squirting_FLOWER_D/_N`) and does not ship seven names the doc does not mention —
`Batwing_Carrier_D/_E/_N`, `Core_Mask2`, `TXT_Helicopter_Police_Blades`, `contrails`,
`gradientNoWrap`.

### 5. Funhouse materials: the parenthetical "minus `Game_Cameo_Squirting_FLOWER_MAT`" is false

`VARIANTS.md` §3 (count 13 is right, the explanation is not): the 13 extra Funhouse materials
**include** `Game_Cameo_Squirting_FLOWER_MAT`. What Funhouse actually lacks versus Joker's 26 is the
Batwing pair, `Hydra_Trails_M` + `_INST`, `Helicopter_Police_Rotor_S_MAT`, `Engine_Distortion`,
`Dusty_hit_01_4x4`, `Falling_Dust_MAT` + `_INST`, `Smoke_02_SubUV_16_unlit`, `contrail_m`,
`Simple_GlowFade`, `LensFlare_OWStreetLightReflection_SOFT_INST`.

### 6. "25 of V2's 28 rows bind a `MaterialType`" — actual 18 of 28

`VARIANTS.md` §6 and `MODLOG.md:8702`. `LIGHTS.json` / `MECHANICS.md`'s rig table: V2's 28 entries
carry a `MaterialType` on **18** rows; the 10 without are `ChainGunMuzzle`, both
`BattleModeSpotLight` rows, `HeadLight1a/2a/1b/1c/2b/2c` and `BootLight`. The qualitative point
(Joker binds none of its 17) is correct.

### 7. "a handful of offsets" understates the object diff by an order of magnitude, and "identical rows" is only semantic

`VARIANTS.md` §6: "MK2 and Funhouse each differ from V2 at a handful of offsets that are **not**
among the 13 decoded properties — MK2: [8 offsets] … Funhouse: [same 8] plus 0x2158". Measured tag
diffs against V2: **60 offsets differ for MK2, 59 for Funhouse** (MK2 has no 0x2158). The 8 (MK2) /
9 (Funhouse) small integers quoted are all correct — I re-derived every one — but the other ~50 are
component **export-index shifts** inside the `VehicleLights` structs (e.g. 0x121C 4993→5054,
0x1334 5112→5163), which the sentence does not mention. So "the same 28-entry light rig (**identical
rows**)" is true of socket/Type/MaterialType but not of the rows as serialised; say "identical apart
from per-package export indices".

### 8. "13 decoded properties" (and Joker's 11) is not the property count

`VARIANTS.md` §6 and the MODLOG. `MECHANICS.md`'s `RVehicleBatmobile` property table has **7** rows
for V2 (`ExplosiveImpactScreenShake`, `ImpactShake`, `DeathExplosionSoundArray`,
`WeaponGeneratorMeshPackage`, `WeaponGeneratorMesh`, `InteriorLightsSwitchedOn`, `Wheels`) and **5**
for Joker; V2's object carries 35 named tags (7 + 28 `VehicleLights`). 13 = 7 properties + **6 audio
references** (AkEvents / AkVehicleSound, which `MECHANICS.md` lists separately), and 11 = 5 + 6. The
diff table that follows is right (3 properties removed, `UpgradedGeneratorBonus` added), but calling
audio references "decoded properties" will mislead the next reader.

### 9. "0 of 332 fields differ" misquotes the source

`VARIANTS.md` §7: "`WEAPONS.md` … compared the shared objects: **0 of 332 fields differ** across the
18 multi-variant objects". `WEAPONS.md` (line 95) says "**0 of 1065 field comparisons differ**"; 332
is the *field count of one package* (its per-package table), not the number of comparisons. The
conclusion (no shared weapon is retuned) is correct.

### 10. "10 gadgets + 4 projectiles" and "6 gadgets" are both off, and the Joker count includes a non-gadget

`VARIANTS.md` §7. Each of V2/MK2/Funhouse carries **10 gadget objects + 8 projectile objects** in
`objects.jsonl` (the Heavy Cannon contributes four: `BodyShot`, `HeadShot`, `Primary`,
`Fully_Upgraded`); the doc's "4 projectiles" counts only the EMP missile pair, missile and tracker.
For Joker the objects are 5 gadgets (`Batmobile_Booster`, `Batmobile_Cannon_V2`,
`Batmobile_JokerCannon_V2`, `Batmobile_JokerHeavy_Cannon`,
`Batmobile_JokerMissile_Launcher` — plus its `Default__`) + 2 projectiles + `ThreatComp`. The doc's
"6 gadgets" reaches six only by counting `RVehicleThreatComponent ThreatComp`, which is a threat
component, not a gadget (R5: a component whose name sounds weapon-adjacent is not a weapon
behaviour). The substantive claim ("no EMP, no sonar, no tracker, no winch, no drone hacker") is
right; the counts and the label are not.

### 11. Not an issue — recorded so it is not re-opened

Verified correct against `objects.jsonl` / `MESHES.md` / `LIGHTS.json`:

- record counts 5,490 / 5,534 / 3,388 / 5,584; the 11 `_Std_*` note is consistent with the package
  list in the grab.
- sockets 65 / 55 / 64 / 63, and the three diff lists are exact name-for-name (MK2 drops the ten
  incl. the whole wheel-light family; Joker adds `BatmobileAttach` + `HydraSocket`; Funhouse adds
  `HydraSocket`; both drop `Dashboard_Light`, `Headlight_Centre`, `PassengerNoiseOrigin`).
- material totals 78 / 80 / 69 / 84 and texture totals 92 / 95 / 100 / 102; MK2's 4-for-2 material
  swap and 5-for-2 texture swap are exact.
- mesh rows: verts, LOD0/1/2 faces, bones (incl. 220 for the Jokerfied skin), 19/19/20/20 materials,
  sizes and export bytes (20,151,210 / 20,034,142 / 20,385,512, Destroyed 3,637,836, Fire 100,628,
  Batwing 836,016) all match `MESHES.md` and the record sizes; Joker and Funhouse really are the
  same 20,385,512 B export.
- §5: the sim object is 2,328 B / 37 tags in all four and **0 tags differ** — confirmed.
- §6: vehicle object sizes 3,905 / 3,905 / 2,239 / 3,905, 28/28/17 light-rig entries, Joker's 3
  removed + 1 added property, and all 8 MK2 / 9 Funhouse small-integer values (0x384 276→275/272,
  0x828 157→156/155, 0x12BC 147→146/145, 0x12DC 62→60, 0x12E4 47→45, 0x153C 115→104/103,
  0x163C 278→277/274, 0x1644 277→276/273, Funhouse 0x2158 −105→−56).

## Spot-checks

| # | value in the doc | where verified | result |
|---|---|---|---|
| 1 | Joker **missing 38** materials, extra 26, count 69 | set difference of `objects.jsonl` names (`Material` + `MaterialInstanceConstant`) against V2: V2 78, Joker 69 → **26 extra, 35 missing**; 78 − 38 + 26 = 66 ≠ 69 | **wrong** (35, not 38). |
| 2 | Joker **extra 32 / missing 24** textures | set difference of `Texture2D` names: 100 total, **31 extra, 23 missing**; no `Hydra` Texture2D exists in any package | **wrong** (31/23). |
| 3 | Funhouse **extra 26 / missing 14** textures | same pass: **24 extra**, 14 missing → 92 − 14 + 24 = 102 ✓ (doc's 26 gives 104 ≠ 102) | **wrong** (24). |
| 4 | socket counts **65 / 55 / 64 / 63** + the three diff lists | `SkeletalMeshSocket` NameProperty at offset 84, per package; set diffs | **exact** on all counts and lists. |
| 5 | materials **78 / 80 / 69 / 84**, textures **92 / 95 / 100 / 102** | class counts per package in `objects.jsonl` | **exact**. |
| 6 | sim **2,328 B / 37 tags, 0 tags differ** across the four | `RVehicleSimBatmobile` tag-by-tag comparison | **exact** (0 differing tags in MK2/Joker/Funhouse). |
| 7 | V2 `RVehicleBatmobile` **3,905 B, 28 rig rows**, 18 with `MaterialType` | record size + `LIGHTS.json` / `MECHANICS.md` rig table | size and 28 ✓; **"25 of 28" is wrong — 18**. |
| 8 | MK2/Funhouse small offsets (0x384 276→275 / 272, 0x828 157→156 / 155, 0x12BC 147→146 / 145, 0x12DC 62→60, 0x12E4 47→45, 0x153C 115→104 / 103, 0x163C 278→277 / 274, 0x1644 277→276 / 273, Funhouse 0x2158 −105→−56) | direct tag-offset diff of the two vehicle records against V2 | **all exact**; but 60 (MK2) / 59 (Funhouse) offsets differ in total, not "a handful". |
| 9 | V2 **10 gadgets + 4 projectiles**; Joker **6 + 1** | object inventory per package (`RBatmobile*`, `RBasicProjectile`, `RBatmobileMissile`, `RVehicleThreatComponent`) | gadgets 10 ✓; projectiles **8** not 4; Joker gadgets **5** (+`Default__`) + `ThreatComp`, projectiles 2 not 1. |
