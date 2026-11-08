# Review of G3-20b — its own 6 HOLDS and 3 WRONG_VALUE rows, and three WRONG_CARD rows

**VERDICT: partially supported.**

Of the 10 rows I checked (the 6 HOLDS of the 105-row set, the first pass's 7th HOLDS row
`T-MD1`, and the 3 WRONG_VALUE rows), **3 keep exactly the label G3-20b gave them** (2 strict
HOLDS, 1 WRONG_VALUE), **3 more are HOLDS only loosely** (the cited line proves the row's
*source* cell but never states the row's *value*), and **4 change class** — always in the same
direction: a line was cited for a quantity it does not carry. 1 of the 10 citations is a section
heading, not a value.

Every stored quote is a genuine substring of the line it names (**12/12**, recomputed), so
G3-20b's mechanical guarantee holds. The defect its `--check` cannot see is the one that matters:
a quote can match a line that carries no value at all (T-MA4), or a value for a *different*
quantity (T-B2, T-PA3), and the checker still passes.

| row | G3-20b | this review | why |
|---|---|---|---|
| T-M1 | HOLDS | HOLDS (loose) | line 48 states 56 blocks / total 1627.097155 — the census, not the row's 4,000 / 6,000 kg |
| T-M4 | HOLDS | HOLDS (loose) | line 49 does carry `'25.0': 10`; the card never says those blocks are wheels |
| T-ST5 | HOLDS | **HOLDS** | line 317 decodes `DriftCorrectionSteerSpeed` (RVehicleBatmobileBase) = **1.0**, the row's source word for word |
| T-B2 | HOLDS | **WRONG_CARD** | line 93 documents the boost *state bit* (`bBoosting` @2396 mask 1); the row's 3500 / 600 / 2.0 members are in `CLASS_DEFAULTS.md:265-266`, not in this card |
| T-PA3 | HOLDS | **WRONG_CARD** | line 41 names the *body entry's* +0x0C; the row is a `parts[]` field |
| T-PA6 | HOLDS | HOLDS (loose) | line 25 states the 24-byte record and §1 lists 11 records; the row's `DeformPoints.constraint_indices` is not read by the card |
| T-MD1 | HOLDS | **HOLDS** | line 93 `bBoosting` @2396 and line 37 `RPlayerInput.bVehicleBoostButton` @781 — both offsets the row names |
| T-MA1 | WRONG_VALUE | **WRONG_CARD** | the row's own value is a block count ("17 blocks per LOD; 200 CarPaintMM + 35 Window across 35 meshes"), not a colour — a colour line cannot be its wrong *value* |
| T-MA3 | WRONG_VALUE | **WRONG_VALUE** | line 69 = authored [0.025787, 0.025787, 0.03, 1]; row states the effective [0.056738, 0.05158, 0.06], and §5/:228-230 + §6/:240 say the combine rule is UNKNOWN (944/944 expression slots zero) |
| T-MA4 | WRONG_VALUE | **WRONG_CARD** | the card has no gloss parameter at all (roughness / reflectivity are different quantities), and the cited line 25 is the heading "## 2. Overrides carried by the chain's MICs (52)" |

What this means for G3-20b's headline ("only 6 hold, 9 cite the wrong card, 3 have the wrong
value"): the arithmetic is right (6 + 9 + 3 = 18; 6 + 3 + 96 = 105, recomputed), but on the rows I
re-opened the split does not survive as labelled — 2 of its 6 HOLDS are wrong-card, and 2 of its 3
WRONG_VALUE are wrong-card, so the "6 hold / 3 wrong value" side is really **2 hold strictly, 3
hold only at the source cell, 1 wrong value, 4 wrong card** among these 10.

## The three WRONG_CARD rows chased

| row | does a card answer it? | answer |
|---|---|---|
| T-MA2 `CarPaintMM` diffuse texture | **partly** | `Research/BatmobileGrab/TEXTURES.md:15` names the row's own source texture (`NEW_Batmobile_V2_BODY_D`, 4096×2048, bound as DiffuseColor of `Batmobile_Body_MASTER`) and `SLOTS.md:27` maps the CarPaintMM slot (2, `Batmobile_V3_Mainbody_NEW_MIC`) into that chain. The row's "28 Batmobile textures shipped" is in neither: TEXTURES.md lists **405** texture rows across 5 packages. |
| T-P3 `.physicsc` shapes | **yes** | `Working/Translation/t16_collision.json` exists and carries `hull_set`, `bindings`, `donor_parts`, `decomposition`, `stations`, `rows` — the hull set and slot binding the row asks for. G3-20b's own routing names this file; it simply did not open it. |
| T-CO1 `.physicsc` collision shapes | **partly** | `Research/JC3Grab/SHAPES.md` is the G2-8 card (line 4: 233 entities, 18,865 convex hulls, 6,382 compounds, 35,499 instance records) and it has the hull→part wiring section. But its vehicle table prints only the 80 largest hull bboxes (Serpente not among them) and the per-entity JSON it points at, `Research/JC3Grab/_JC3grab/hkx/out/`, **is not in the repository** — so the donor's own hull list is not in the card. |

## Files written

| file | what |
|---|---|
| `Tools/scripts/review_g3b_claims.py` | new tool, `--write` / `--check`; re-opens every cited line and every token |
| `Working/Translation/REVIEW_G3B.md` | generated record (the full per-row blocks, quotes and findings) |
| `Working/Translation/REVIEW_G3B.json` | the same as data |
| `tmp/freebuff/reports/review-G3-20b.md` | this report |

Nothing else was written. `Working/Translation/LEDGER_G3B.*`, `Tools/scripts/ledger_g3b.py`,
`T_ROWS.jsonl` and every card are read-only here; no game process; no git action.

## Defects found in G3-20b (each is evidence-backed above)

1. **T-B2 is mislabelled HOLDS.** The row's quantity is `arcade.nitro_boost.extra_top_speed`
   (50.46 → 43.2 km/h from `FakeExtraSpeedMax` 3500, `FakeExtaSpeedAccel` 600, `BoostDuration`
   2.0). `SAMPLER_FIELDS2.md` contains **none** of those three members (`grep` finds no
   `FakeExtraSpeedMax`/`FakeExtaSpeedAccel`/`BoostDuration` there); its line 93 documents the
   boost state bit. The members are in `CLASS_DEFAULTS.md:265-266` (3500.0 / 600.0);
   `BoostDuration` appears in **no** `.md` under `Research/BatmobileGrab`.
2. **T-PA3 is mislabelled HOLDS.** `PHYSICS_ROLES3.md:41` documents the body entry's `+0x0C`;
   the row is `parts[].world_collision_body_id` / `raycast_body_id`. Both field names appear
   nowhere on the cited line.
3. **T-MA4's citation is empty.** `COLOUR_PARAMS.md:25` is a section heading. Its note's numbers
   are real but on other lines: `Material0_Roughness` 0.4 (line 33) / 0.25 (line 111),
   `Material0_Reflectivity` 0.2 (line 32) / 0.25 (line 120); the word "gloss" does not occur in
   the card. Because the card has a *different parameter*, G3-20b's own definitions make this a
   WRONG_CARD, not a WRONG_VALUE.
4. **T-MA1 is mislabelled WRONG_VALUE.** Its value cell is a block count (17 per LOD, 200 + 35
   across 35 meshes); the colour comparison does not touch that claim, and the row's 17 / 200 / 35
   were never checked.
5. **T-M1, T-M4, T-PA6 pass on the source cell, not on the row's value** — the definition at the
   top of `LEDGER_G3B.md` ("HOLDS = the quoted line states what the row claims") is applied
   loosely in these three.
6. **T-PA6's note repeats an uncited G3-10d claim** ("the constant 0 word is body 0 in 494/494
   records, so the partner is no longer UNKNOWN") that contradicts the very card it cites,
   `PHYSICS_ROLES3.md:25-28` ("the partner is **not stored in the cinfo**"), and it carries no
   line.
7. **T-M1's two cited lines cannot rebuild its own total**: `:48` states 1627.097155, the
   histogram on `:49` lists 52 of the 56 masses and sums to 1317.076000, leaving 310.021155 on 4
   values that line does not enumerate (the 275.0 of the `:47` first-eight list is one of them).
   Not an error in the card — a limit of citing two lines as proof.
8. **`PARTS_TABLE.jsonl` is routed without its directory** in §4/open_with; the file is
   `Research/JC3Grab/PARTS_TABLE.jsonl`, not under `Research/BatmobileGrab`.

## Commands and outputs (verbatim, abridged only where a table is long)

```
$ awk 'NR>=40&&NR<=60{printf "%d: %s\n",NR,$0}' Research/JC3Grab/PHYSICS_ROLES2.md
40: - `hkpLimitedHingeConstraintData` @0x4E610: +0x094 = 1.0, +0x0A0 = -0.50784, ...
43: ## 2. The 56 `hknpShapeMassProperties`
45: 56 objects. Each is 48 bytes: no IEEE float except the one at **0x28**, and that one is the mass.
47: - mass float @0x28 (IEEE-754 little-endian). Donor values, first eight: [800.0, 40.0, 5.0, 1.0, 40.0, 5.0, 1.0, 275.0]
48: - strictly positive in the donor: **True**; finite: **True**; total over all 56 blocks: **1627.097155**
49: - the values are authored discrete numbers, not computed from geometry: {'1.0': 17, '25.0': 10, '5.0': 6, '40.0': 4, '30.0': 2, '0.002': 2, '0.006': 2, '0.009': 2, '0.005': 2, '0.012': 2, '0.004': 2, '800.0': 1}
54: | 0x5970 | 800.0 | 0x5940 | 94 | `8fff9759d8560030d93c8546cd188035d77d0580e87f2af5` |
```
=> T-M1 / T-M4: both quotes are substrings (line 48 carries "total over all 56 blocks:
**1627.097155**", line 49 carries `'25.0': 10`, line 54 `| 0x5970 | 800.0 |`).

```
$ awk 'NR>=18&&NR<=28{printf "%d: %s\n",NR,$0}' Research/JC3Grab/PHYSICS_ROLES3.md
18: | 5 | 0x48F8 | 00000000 00000000 00000010 7fffffff 00000000 00000000 | hkpLimitedHingeConstraintData | 16 | 0x7FFFFFFF | **none** |
...
24: |
25: **Decoded negative:** the record is 24 bytes - pointer (a fixup, so 0 in the raw), body id,
26: 0x7FFFFFFF, 0, 0. No word other than the one body id is a body index, in the donor or in any
27: fleet file; +0x0C is the same sentinel the body table uses for bodies without a part id.
28: So the partner is **not stored in the cinfo**; G3-10b's "chassis hypothesis" is neither

$ awk 'NR>=34&&NR<=46{printf "%d: %s\n",NR,$0}' Research/JC3Grab/PHYSICS_ROLES3.md
41: | +0x0C | body id | equals the entry index for the 38 part bodies (0..41 minus 22/23/36/37); 0x7FFFFFFF for the other 24 |
```
=> T-PA6 quote present (11 records 0..10 at 0x4880..0x4970 in §1); T-PA3 quote present, but it is
the body-entry word, not a `parts[]` field.

```
$ awk 'NR>=30&&NR<=40{printf "%d: %s\n",NR,$0}' Research/BatmobileGrab/SAMPLER_FIELDS2.md
37: | Y held (boost) - the digital button byte | `RPlayerInput.bVehicleBoostButton` | 781 (0x30d) | `u8` | - | 1 | ...
$ awk 'NR>=86&&NR<=100{printf "%d: %s\n",NR,$0}' Research/BatmobileGrab/SAMPLER_FIELDS2.md
93: | boost active | `RBatmobileBooster.bBoosting` | 2396 (0x95c) | `bit` | 1 | 4 | `BmSDK/Generated/BmGame/RBatmobileBooster.g.cs:82` | decoded ...
```
=> T-MD1 holds (both quotes, both offsets). T-B2's quote also matches 93, but that line is the
state bit; the row's speed members are not in this card:

```
$ grep -n "FakeExtraSpeedMax\|FakeExtaSpeedAccel\|BoostDuration" Research/BatmobileGrab/SAMPLER_FIELDS2.md
(no output)

$ grep -n "FakeExtraSpeedMax\|FakeExtaSpeedAccel\|BoostDuration" Research/BatmobileGrab/CLASS_DEFAULTS.md
265:| 87 | `0x0560` | 7156 | `FakeExtraSpeedMax` (RVehicleBatmobileBase) | FloatProperty | 3500.0 | decoded | ...
266:| 88 | `0x0568` | 7160 | `FakeExtaSpeedAccel` (RVehicleBatmobileBase) | FloatProperty | 600.0 | decoded | ...
572: | 7156 | `FakeExtraSpeedMax` | 3500.0 |
573: | 7160 | `FakeExtaSpeedAccel` | 600.0 |

$ grep -rn "BoostDuration" Research/BatmobileGrab/*.md
(no output)
```

```
$ awk 'NR>=310&&NR<=322{printf "%d: %s\n",NR,$0}' Research/BatmobileGrab/CLASS_DEFAULTS.md
317: | 139 | `0x0a38` | 8076 | `DriftCorrectionSteerSpeed` (RVehicleBatmobileBase) | FloatProperty | 1.0 | decoded | BmGame\RVehicleBatmobileBase.g.cs:8683 (off 8076) |
```
=> T-ST5 holds exactly.

```
$ awk 'NR>=18&&NR<=32{printf "%d: %s\n",NR,$0}' Research/BatmobileGrab/COLOUR_PARAMS.md
25: ## 2. Overrides carried by the chain's MICs (52)
32: | 1 | `Batmobile_V3_Mainbody_NEW_MIC` (#763) | `Material0_Reflectivity` | scalar | 0.2 | ...
$ awk 'NR>=60&&NR<=80{printf "%d: %s\n",NR,$0}' Research/BatmobileGrab/COLOUR_PARAMS.md
69: | 38 | `Batmobile_V3_WheelArchs_NEW_MIC` (#767) | `Material0_BaseColour` | vector | [0.025787, 0.025787, 0.03, 1] | `f36abc2b` | ...
$ grep -n -i "roughness\|reflectivity\|gloss" Research/BatmobileGrab/COLOUR_PARAMS.md
33:| 2 | `Batmobile_V3_Mainbody_NEW_MIC` (#763) | `Material0_Roughness` | scalar | 0.4 | ...
111:| 19 | 506 | `Material0_Roughness` | float | 0.25 | FloatProperty @0xcc |
120:| 28 | 515 | `Material0_Reflectivity` | float | 0.25 | FloatProperty @0xcc |
(no line contains "gloss")

$ grep -n "^#\{1,3\} " Research/BatmobileGrab/COLOUR_PARAMS.md
...
225:## 5. What this document does not claim
238:## 6. UNKNOWNs
240:1. **the rule that combines the parameters ... every `FunctionExpressions` slot ... is zero (944 slots, 0 non-zero in this read)**
```
=> T-MA3's WRONG_VALUE stands (authored 0.025787 / 0.025787 / 0.03 on line 69 vs the row's
effective 0.056738 / 0.05158 / 0.06, combine rule UNKNOWN). T-MA1's row value is a block count,
so the colour comparison does not apply to it. T-MA4's cited line 25 is a heading; its numbers are
on 33/111/32/120; the card has no gloss.

```
$ awk 'NR<=11{printf "%d: %s\n",NR,$0}' Research/BatmobileGrab/TEXTURES.md
3: `format` is the BmAK pixel-format id as stored in the object ...
5: | package | texture | size | format | bytes | bound by |
15: | Playable_BatmobileFunhouse_SF | `NEW_Batmobile_V2_BODY_D` | 4096×2048 | PF_DXT1 | 6042 | ...Batmobile_Body_MASTER (DiffuseColor); ... |

$ awk -F'|' '/^\| /{gsub(/ /,"",$2); print $2}' Research/BatmobileGrab/TEXTURES.md | sort | uniq -c
    103 Playable_BatmobileFunhouse_SF
    101 Playable_BatmobileJoker_SF
     96 Playable_BatmobileMK2_SF
     93 Playable_Batmobile_SF
     12 Playable_Batmobile_Std_6_SF
```
=> T-MA2 partly answered (texture identity/size yes; "28 shipped" no — the card lists 405 rows).

```
$ awk 'NR<=45{printf "%d: %s\n",NR,$0}' Research/BatmobileGrab/SLOTS.md
5: ## Summary            ... 15: | textures | **38** | ...
23: | # | material | kind | parent | LOD0 faces | textures | block | parts |
27: | 2 | `Batmobile_V3_Mainbody_NEW_MIC` | MaterialInstanceConstant | `Material_Worn.Batmobile_V3_WheelArchs_NEW_MIC` | 37819 | ... | CarPaintMM | body |
```
=> the CarPaintMM slot exists in SLOTS.md; it does not name the diffuse texture itself.

```
$ PYTHONIOENCODING=utf-8 python -c "import json;d=json.load(open('Working/Translation/t16_collision.json',encoding='utf-8'));print(list(d))"
['schema', 'generator', 'card', 'inputs', 'bmak', 'donor', 'donor_parts', 'decomposition', 'hull_set', 'bindings', 'stations', 'rows', 'prose_fix', 'summary']

$ ls -d Research/JC3Grab/_JC3grab
ls: cannot access 'Research/JC3Grab/_JC3grab': No such file or directory

$ ls Working/Translation | grep -i -E "T3|FLEET|FITS|VALUES|VOCAB"
FITS.md  T3_COVERAGE.md  T3_FLEET.md
```
=> T-P3 is answerable from a file G3-20b itself names; SHAPES.md's per-entity JSON pointer is
dangling; T3_FLEET.md does exist.

```
$ grep -n -i "sportsmuscle\|serpente" Research/JC3Grab/SHAPES.md
219:**Placement is `p' = M^T p + t`.** That is not a guess either: the Serpente's doors
$ sed -n '176,184p' Research/JC3Grab/SHAPES.md
| `v0006_car_autostraad_modernbus/...` | 140 | 1716 | 1255 | 1089 | 2.96 × 3.87 × 10.62 |  |
...
First 80 of 233 entities, largest hull bbox first.
```
=> the Serpente is not in SHAPES.md's printed table (T-CO1 partly answered).

Final tool runs:

```
$ python Tools/scripts/review_g3b_claims.py --write; echo WRITE_EXIT=$?
wrote REVIEW_G3B.md and REVIEW_G3B.json (10 rows checked, 2 with the row's value on the cited line, 1 heading citations, 4/4 cross-checks)
WRITE_EXIT=0

$ python Tools/scripts/review_g3b_claims.py --check; echo CHECK_EXIT=$?
OK: On the 10 rows checked, 3 keep exactly the label G3-20b gave; rows 10, value-on-line 2, heading citations 1, cross-checks 4/4
CHECK_EXIT=0
```

Its four cross-checks (all PASS, recomputed from `LEDGER_G3B.json` and the cards): the 105-row
status tally `{HOLDS 6, OPEN 96, WRONG_VALUE 3}`; the 18 first-pass rows `{HOLDS 6, WRONG_CARD 9,
WRONG_VALUE 3}`; **12/12 quotes are substrings of the lines they name**; the T-M1 total on
`PHYSICS_ROLES2.md:48` is 1627.097155.

## UNKNOWNs

| item | status | what would settle it |
|---|---|---|
| whether the rows I relabelled are still *right about the game* | not judged (out of scope) | a card/row pair can be wrong-card and still correct; the T-MA2 "28 textures" and T-MA1's 17/200/35 counts would need their own source (built RBM texture table / material-block census), which no card read here carries |
| where `BoostDuration` = 2.0 s is decoded | UNKNOWN in `.md` cards | the member appears in `CLASS_DEFAULTS.json`/BMSDK offsets but no `.md` card states its value; a class-default line would close T-B2's fourth input |
| the donor's own `.physicsc` hull list for the Serpente | UNKNOWN in a card | `Research/JC3Grab/SHAPES.md` prints only the 80 largest hull bboxes and its per-entity JSON directory is absent; re-running `Tools/scripts/jc3hkx.py` for `v0300_car_kensington_sportsmuscle` would produce it |
| whether G3-20b's 9 WRONG_CARD verdicts are all sound | 3 of 9 checked | the other six are T-B3, T-B4, T-MA5, T-MA7, T-CO2, T-WP11; each needs the same chase (answering card found or not) |
