# Independent review — G1X · G1 exit gate

Reviewer: Freebuff (did not write this card). Date: 2026-10-29.
Scope: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G1X gate paragraph (§5, "G1 exit gate (G1X)"),
the §12 `G1X` row (line 1292), `MODLOG.md` §"G1X · G1 exit gate — passed" (lines 9019–9140), the
gate itself (`Tools/scripts/g1x_gate.py`), its evidence (`Research/BatmobileGrab/*`), and the four
checks the card's Done names.
Read-only: nothing under `Research/`, `Tools/`, `GRAB_BACKLOG.md`, `MODLOG.md` or the game install
was written; no game launched. This report is the only file written.

## VERDICT: **minor issues**

The gate is green, the code coverage is complete, and the MODLOG's code table is byte-identical to
what the tool prints. What is weaker than it reads is the *classification*: the 56/19 split is a
hand choice (ten codes with no lore/source column in §1 are counted as "satisfied by G1 files"
while eight identically column-less WLD codes are counted as "proven absences"), the 19 absences
pass without any check at all, and **18 of the 56 needles are vacuous** — substrings like `fin`
(952 hits in `ANIMATIONS.md`, matching "find"/"final"), `60`, `cone` (one hit, a table header) — so
the gate cannot notice a doc losing the fact it is supposed to carry. Separately, the MODLOG quotes
`grab_lights --check`'s "36 … carry colour and intensity" as LGT-1/APP-4 evidence, and that line is
not what the script tests: 17 of the 36 are lens flares with no intensity value.

Out path: the card's Out is the MODLOG section `G1X` — it exists (line 9019), as does
`Tools/scripts/g1x_gate.py`. There is no `.json`/`.md` artefact for this card, which matches the
card text ("Write a MODLOG section \"G1X\" listing the files").

## Check output (verbatim)

```
$ python Tools/scripts/g1x_gate.py --check
codes 75: 56 from G1 files, 19 proven absences (no BmAK source); PASS
EXIT=0
```

The four checks the card's Done names, re-run:

```
$ python Tools/scripts/grab_model.py check
OK: grab output matches schema 6 and its own summary.
EXIT=0
$ python Tools/scripts/grab_weapons.py --check
ok E:\Modding\JC3-Batmobile\Research\BatmobileGrab\WEAPONS.md
PASS: 62 objects, 13 classes, 594 references (128 missing-object), 0 variant differences, 10 projectiles (9 launcher targets, 1 unfired), 30 FX rows, 12 AkEvent rows
EXIT=0
$ python Tools/scripts/grab_anims.py --check
ok E:\Modding\JC3-Batmobile\Research\BatmobileGrab\ANIMATIONS.md
PASS: 253 sequences, 13 sets, 3 trees, 253 PSA sequences, 3147888 keys, 309 notifies (204 sound, 35 script); 253/253 named, 253 bone lists, 253 mechanisms; 13/13 keyframe files present
EXIT=0
$ python Tools/scripts/grab_lights.py --check
OK: 101 entries / 4 rigs, 6 orphan sockets, 0 missing bones
OK: 36 Batmobile-rig components carry colour and intensity (schema 2)
EXIT=0
```

All four are green, so the gate's prerequisite half holds today. Note `--check` does **not** run
them: `g1x_gate.py` verifies only its own code table, and its docstring says so ("This tool is the
second half"). The Done criterion is therefore satisfied but not machine-verified by any one
command.

## Issues

### 1. The 56/19 split is a hand classification, and it is applied two ways to the same absence
`g1x_gate.py` `G1_ROWS` is a literal table: each code's kind, files and needle are typed. Ten codes
in §1 have **no lore/source column at all** — `LGT-1`, `LGT-2`, `FX-1…4`, `CAM-1`, `CAM-2`,
`HUD-1`, `HUD-2` (§1.10 is `| code | requirement | carrier |`) — and all ten are counted in the
"56 from G1 files" half, while the eight `WLD` codes in the same 3-column table are counted in the
"19 proven absences" half through one blanket reason. For `LGT-1` and `LGT-2` the requirement text
does name BmAK light components, so `g1` is defensible; for `HUD-1`, `HUD-2`, `FX-2`, `FX-3` and
`CAM-2` nothing in the §1 row names a BmAK source, yet they still count as satisfied by G1 files.
The headline "56 from G1 files, 19 proven absences" (also in the §12 row) is therefore a judgement,
not a count derived from §1. Under R11 the *total* (75) is script-derived, but the split is not.

### 2. 18 of the 56 needles are vacuous
Measured occurrences of each needle in the file the row points at:

| code | needle | occurrences | why it proves nothing |
|---|---|---|---|
| `ANI-5` | `fin` | **952** | matches "find", "final", "definition" in the same file |
| `APP-4` | `emissive` | 334 | a word the whole doc uses; nothing about a colour |
| `FX-2` | `muzzle` | 222 | any particle table matches |
| `MOD-4`, `ANI-8` | `Door` | 194 each | bone-name lists are full of it |
| `APP-5` | `bone` | 81 | every section |
| `APP-8` | `MK2` | 48 | package names |
| `DIM-2` | `1.36` | 37 | matches `1.3652`, `1.369`-style text; not the measured value |
| `CAM-1` | `FOV` | 33 | column header |
| `ANI-4` | `fan` | 16 | "fan", "fantastic"? 16 hits |
| `AUD-1` | `RPM` | 12 | |
| `CAM-2` | `60` | 12 | matches "1,60x", "60 mm", "FOV 60" |
| `APP-6` | `Pose` | 8 | |
| `ARM-2` | `1200` | 4 | does not require the value to be Health |
| `AUD-7` | `horn` | 3 | |
| `ANI-7` | `yoke` | 3 | |
| `LGT-1` | `cone` | **2** | the only hits are the table header `inner cone | outer cone`; no cone value is decoded for point lights (`LIGHTS.md` prints `-`) |

The gate checks "the file still contains this string", not "the doc still states this fact", so a
regeneration that dropped e.g. the headlight cone numbers, the FOV range, the fin animation or the
`Pawn.Health` 1200 row would still pass as long as the word survives somewhere. R5's "behaviour
with a take that can fail" is not met by a substring.

### 3. The 19 "proven absences" are never checked
`check()` returns `pass: True` for every `not-g1` row without reading a file — the "proof" is the
`absence_reason` string in the Python literal. Some of those reasons do have repo backing
(`APP-7`: `DAMAGE_RULES.md:370` says `impact_damage_factor`, `impact_armor`, `deform_scale` "live in
the **JC3** build, not in BmAK"), but the gate does not verify it, so the word "proven" rests on
the author's word. R4 is about values, so this is not a value error — it is an evidence gap in a
gate whose job is evidence.

### 4. `HDL-6` is counted as an absence although a G1 file now carries its measurement
`HDL-6`'s row is `not-g1` with reason "…air time now measured in FOOTAGE.md". `FOOTAGE.md` (G1-23)
is a G1 file and does carry the value: "air time (three ramp jumps) **1.212 s mean** (1.183 – 1.251)"
(line 26, and F-6 at line 142). Whatever the right classification is, the gate's own reason names a
G1 file it neither lists nor checks, and the headline count does not reflect it.

### 5. The MODLOG quotes a `grab_lights` line that the script does not test
The gate table quotes `OK: 36 Batmobile-rig components carry colour and intensity`. In
`grab_lights.py:670-695` every component of every rig entry increments `checked`, and the flare
branch explicitly skips the intensity **value** check ("A lens flare has no brightness…"), so the
printed 36 includes components that carry no intensity at all. From `LIGHTS.json`
(`Playable_Batmobile_SF`, 28 entries):

```
rig entries 28 components 36
Counter({'LensFlareComponent': 17, 'SpotLightComponent': 16, 'PointLightComponent': 2, 'RHelicopterSpotLightComponent': 1})
components with an intensity value: 19
flares with intensity value: 0
```

So 19 of 36 carry an intensity value, not 36. The MODLOG uses the line as gate evidence for LGT-1
and APP-4; the colour half is real, the intensity half is not. (The same line was flagged in
`tmp/freebuff/reports/review-G1-17.md`; G1X propagates it.)

### 6. The MODLOG's quoted gate output is not verbatim any more
`grab_weapons` is quoted as "…10 projectiles, 30 FX rows, 12 AkEvent rows"; today it prints
"10 projectiles (9 launcher targets, 1 unfired), 30 FX rows, 12 AkEvent rows". `grab_anims` is
quoted "253 PSA, 3,147,888 keys, 309 notifies; 253/253 named; 13/13 keyframe files present"; today
it prints "253 PSA sequences, 3147888 keys, 309 notifies (204 sound, 35 script); 253/253 named,
253 bone lists, 253 mechanisms; 13/13 keyframe files present". The numbers agree — the sentences do
not. R14 asks for command output; these are paraphrases of a slightly older message.

### 7. Not an issue — verified sound
- **Coverage is complete.** Parsing §1 gives 75 code rows (APP 8, DIM 4, ARM 6, WPN 12, HDL 6,
  MOD 5, AUD 7, ANI 9, WLD 8, LGT 2, FX 4, CAM 2, HUD 2) and the gate has exactly the same 75 codes
  — none missing, none invented.
- **The MODLOG table is generated, not typed**: `g1x_gate.py --markdown` and the 75 rows of the
  MODLOG section `**Every feature code, and the file that satisfies it**` are identical line for
  line (checked programmatically).
- **Every named file exists**: all 56 `g1` rows' first file exists and contains the needle (that is
  what `--check` just proved), and the second files exist too.
- **§12's sideswipe claim holds**: `DAMAGE_RULES.md:167` §3.3.1 exists with the six members
  (`SideSwipeTargetsList`, `SideSwipeInSweetSpot`, the three functions, `CrushedThisFrame` /
  `BouncedThisFrame`) and says the record has no archetype value for them; `OFFSETS.json` has
  `0` lines matching any of them, as the entry claims.
- **The four Done-checks are green** (verbatim above); nothing in the gate's table contradicts the
  §1 text for the 19 `not-g1` codes whose §1 row does name a non-BmAK source (play rules, T-ledger
  rows, wiki rows, a build value).

### Consequence for the DoD
The card's Done is met as written. The risk it leaves is that "every feature code has rows in a G1
file" is really "a file exists and contains a common word", and "19 proven absences" is really "19
hand-written reasons, unchecked". Neither is wrong today; both would hide a real loss tomorrow.

## Spot-checks

| value in the doc | where verified | result |
|---|---|---|
| **75** codes, 56 from G1 files / 19 absences | `GRAB_BACKLOG.md` §1 rows vs `g1x_gate.py --markdown`; the script's own `--check` line | 75 = 75; 56 + 19 = 75; §12 row repeats the same three numbers |
| `grab_anims`: **253** sequences, **3,147,888** keys | `grab_anims.py --check` output vs `ANIMATIONS.md:16` ("PSA keys read 3,147,888") and line 5 verdict | agree |
| `Pawn.Health` **1200** (ARM-2) | `DAMAGE_RULES.md:280` ("= 1200 on all 3 Batmobile archetypes") and the three per-archetype rows at 574/627/654 | agree |
| body length **7.026 m** (DIM-1 needle) | `POSES.md:18` (`3.495 × 2.341 × 7.026`), 7 occurrences | agree |
| 36 rig components / **19** with intensity | `LIGHTS.json` `Playable_Batmobile_SF`: 17 flare + 16 spot + 2 point + 1 helicopter spot | 36 and 19 ✓ — but the check's wording claims all 36 (issue 5) |

Not verified: the MODLOG's "the first run failed 13 needles" (history, unprovable from the repo),
and whether the quoted gate lines were verbatim on 2026-10-26 (they are not today — issue 6).
