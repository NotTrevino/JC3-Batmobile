# Review of G3-20b's ledger verdicts

**VERDICT: partially supported.** On the 10 rows checked, 3 keep exactly the label G3-20b gave them (2 strict HOLDS, 1 WRONG_VALUE); 3 more are HOLDS only loosely - the cited line proves the row's source cell but never states the row's value; 4 rows change class, all in the same direction, a line being cited for a quantity it does not carry (2 HOLDS cite a different quantity, 2 WRONG_VALUE cite a different quantity rather than a different value), and 1 of the 10 citations is a section heading; every stored quote (12/12) is a genuine line substring, so its --check works but cannot detect a citation that carries no value.

Checked: the 6 HOLDS rows of the 105-row set, the first pass's 7th HOLDS row (`T-MD1`,
outside the three groups) and the 3 WRONG_VALUE rows — 10 rows, every cited line re-opened.
Three WRONG_CARD rows were then chased for an answering card.

| | count |
|---|---:|
| rows checked | 10 |
| rows whose *whole* stated value is on a cited line | 2 |
| rows with at least one stated value on a cited line | 4 |
| citations that are section headings, not values | 1 |

## 1. The 10 rows, line by line

| row | G3-20b | this review | quoted line | quote is a substring | the row's own value on that line |
|---|---|---|---|---|---|
| T-M1 | HOLDS | HOLDS (loose) | `PHYSICS_ROLES2.md:48` | yes | no |
| T-M4 | HOLDS | HOLDS (loose) | `PHYSICS_ROLES2.md:49` | yes | partly (25 yes, 75 no) |
| T-ST5 | HOLDS | HOLDS | `CLASS_DEFAULTS.md:317` | yes | yes |
| T-B2 | HOLDS | WRONG_CARD | `SAMPLER_FIELDS2.md:93` | yes | no |
| T-PA3 | HOLDS | WRONG_CARD | `PHYSICS_ROLES3.md:41` | yes | no |
| T-PA6 | HOLDS | HOLDS (loose) | `PHYSICS_ROLES3.md:25` | yes | no |
| T-MD1 | HOLDS | HOLDS | `SAMPLER_FIELDS2.md:93` | yes | yes |
| T-MA1 | WRONG_VALUE | WRONG_CARD | `COLOUR_PARAMS.md:69` | yes | no |
| T-MA3 | WRONG_VALUE | WRONG_VALUE | `COLOUR_PARAMS.md:69` | yes | partly (0.056738 no, 0.025787 yes) |
| T-MA4 | WRONG_VALUE | WRONG_CARD | `COLOUR_PARAMS.md:25` | yes | no |

### T-M1 — ``rigid_body.mass`` (HOLDS)

row says (now): **4,000 kg**
row proposes : **6,000 kg** (armored transport; 3–8 t p75 = 6,000 kg, `T3_FLEET.md`)

cited `Research/JC3Grab/PHYSICS_ROLES2.md:48`:

```
- strictly positive in the donor: **True**; finite: **True**; total over all 56 blocks: **1627.097155**
```

quote present: **True**
cited `Research/JC3Grab/PHYSICS_ROLES2.md:54`:

```
| 0x5970 | 800.0 | 0x5940 | 94 | `8fff9759d8560030d93c8546cd188035d77d0580e87f2af5` |
```

quote present: **True**

the row's own tokens:

| token | what it is | on the cited line | found at |
|---|---|---|---|
| `4,000` | the row's 'now' mass | no | `Research/BatmobileGrab/CLASS_DEFAULTS.md:163` |
| `6,000` | the row's proposed mass | no | `Working/Translation/T3_FLEET.md:11` |

this review's label: **HOLDS (loose)** — the line proves the census, not the row's 4,000 / 6,000 kg

finding: holds for the card's census, not for the row's value: the line states 56 blocks and the total 1627.097155 (and line 54 the 800.0 block), which is exactly the 'no single rigid-body mass' argument; the row's own 4,000 / 6,000 kg never appear on either cited line, and the 6,000 is a T3_FLEET.md class choice.

### T-M4 — ``land_global.front/rear_wheels.mass`` (HOLDS)

row says (now): 25 / 75
row proposes : **75 / 150** (armored transport 75; old truck 200; 25 kg is a supercar wheel on a 6 t car)

cited `Research/JC3Grab/PHYSICS_ROLES2.md:49`:

```
- the values are authored discrete numbers, not computed from geometry: {'1.0': 17, '25.0': 10, '5.0': 6, '40.0': 4, '30.0': 2, '0.002': 2, '0.006': 2, '0.009': 2, '0.005': 2, '0.012': 2, '0.004': 2, '800.0': 1}
```

quote present: **True**

the row's own tokens:

| token | what it is | on the cited line | found at |
|---|---|---|---|
| `25` | the wheel mass the row quotes as its 'now' | yes | — |
| `75` | the rear mass the row proposes | no | `Working/Translation/T3_FLEET.md:4` |

this review's label: **HOLDS (loose)** — 25.0 appears; the card never says those blocks are wheels

finding: holds for the value's existence, not for the attribution: line 49 does carry `'25.0': 10`. The card never says those ten 25.0 blocks are wheels - it lists 56 anonymous shape-mass blocks by offset - so 'wheel mass = 25' is an inference the cited line does not make.

### T-ST5 — ``land_steering.countersteer_speed_factor`, `steer_in_speed_factor`` (HOLDS)

row says (now): 2.0 / 1.5
row proposes : **next**: 2.0 / 1.5 → **1.0 / 1.0** — BmAK corrects drift at the **base steering rate** (×1.0, no assist gain), so both JC3 rate factors translate to identity. Out of domain on both (countersteer 1.5 … 20, steer_in 1.2 …

cited `Research/BatmobileGrab/CLASS_DEFAULTS.md:317`:

```
| 139 | `0x0a38` | 8076 | `DriftCorrectionSteerSpeed` (RVehicleBatmobileBase) | FloatProperty | 1.0 | decoded | BmGame\RVehicleBatmobileBase.g.cs:8683 (off 8076) |
```

quote present: **True**

the row's own tokens:

| token | what it is | on the cited line | found at |
|---|---|---|---|
| `1.0` | the BmAK steering factor the row's source cites | yes | — |

this review's label: **HOLDS** — the line states the row's 1.0

finding: holds exactly: line 317 decodes `DriftCorrectionSteerSpeed` (RVehicleBatmobileBase) = 1.0, which is the row's source cell word for word. The row's 2.0 / 1.5 proposal is donor data and is not claimed from this card.

### T-B2 — ``arcade.nitro_boost.extra_top_speed`` (HOLDS)

row says (now): 50.46
row proposes : **next**: 50.46 → **43.2** — min(`FakeExtraSpeedMax`, `FakeExtaSpeedAccel` × `BoostDuration`) = 1200 cu = **43.2 km/h**, inside the shipped domain 30 … 60 (n=145, med 40) and above the curve's +32.4 km/h bound: a comput…

cited `Research/BatmobileGrab/SAMPLER_FIELDS2.md:93`:

```
| boost active | `RBatmobileBooster.bBoosting` | 2396 (0x95c) | `bit` | 1 | 4 | `BmSDK/Generated/BmGame/RBatmobileBooster.g.cs:82` | decoded (BmSDK/Generated/BmGame/RBatmobileBooster.g.cs:82, bit @2396, mask 0x1) |
```

quote present: **True**

the row's own tokens:

| token | what it is | on the cited line | found at |
|---|---|---|---|
| `3500` | FakeExtraSpeedMax | no | `Working/Translation/T3_FLEET.md:11` |
| `600` | FakeExtaSpeedAccel | no | `Working/Translation/T3_FLEET.md:11` |
| `43.2` | the row's proposed km/h | no | — |

this review's label: **WRONG_CARD** — the line documents the boost state bit, not the speed members

finding: does NOT hold as cited: line 93 documents the boost *state bit* (`RBatmobileBooster.bBoosting` @2396, mask 1), while the row's quantity is an extra top speed computed from `FakeExtraSpeedMax` 3500 / `FakeExtaSpeedAccel` 600 / `BoostDuration` 2.0 - members that are not in SAMPLER_FIELDS2.md at all. They are in CLASS_DEFAULTS.md:265-266 (3500.0, 600.0); `BoostDuration` is in no .md card under Research/BatmobileGrab. By G3-20b's own definition this is the wrong card for the row's quantity.

### T-PA3 — ``parts[].world_collision_body_id` / `raycast_body_id`` (HOLDS)

row says (now): decoded — e.g. `body` → 0, `door_f_l` → 1, `engine` → 7, wheels → −1 (`PARTS_TABLE.jsonl`)
row proposes : keep

cited `Research/JC3Grab/PHYSICS_ROLES3.md:41`:

```
| +0x0C | body id | equals the entry index for the 38 part bodies (0..41 minus 22/23/36/37); 0x7FFFFFFF for the other 24 |
```

quote present: **True**

the row's own tokens:

| token | what it is | on the cited line | found at |
|---|---|---|---|
| `world_collision_body_id` | the field the row targets | no | — |
| `raycast_body_id` | the field the row targets | no | — |

this review's label: **WRONG_CARD** — the line documents the body entry's word, not the parts field

finding: does NOT hold as cited: line 41 names the *body entry's* +0x0C word. The row is `parts[].world_collision_body_id` / `raycast_body_id` - a parts-table field, which G3-20b's own note points at PHYSICS_ROLES.md §2 / PARTS_TABLE.jsonl. The card supplies one end of the mapping, not the row.

### T-PA6 — ``DeformPoints.constraint_indices`` (HOLDS)

row says (now): 11 points → **11 parts**
row proposes : keep

cited `Research/JC3Grab/PHYSICS_ROLES3.md:25`:

```
**Decoded negative:** the record is 24 bytes - pointer (a fixup, so 0 in the raw), body id,
```

quote present: **True**

the row's own tokens:

| token | what it is | on the cited line | found at |
|---|---|---|---|
| `11` | the constraint-index count the row states | no | `Research/BatmobileGrab/CLASS_DEFAULTS.md:91` |

this review's label: **HOLDS (loose)** — the record shape is stated; the row's 11 indices are not

finding: holds for the record shape, not for the row's count: line 25 states the 24-byte record and that no second body id is stored, and §1 lists 11 records (0..10, offsets 0x4880..0x4970). The row's claim is that `DeformPoints.constraint_indices` has 11 entries; the cited card does not read DeformPoints. The note's uncited G3-10d claim (constant 0 word = body 0 in 494/494) also contradicts the same card's 'partner is not stored'.

### T-MD1 — `` (HOLDS)

row says (now): 

cited `Research/BatmobileGrab/SAMPLER_FIELDS2.md:93`:

```
| boost active | `RBatmobileBooster.bBoosting` | 2396 (0x95c) | `bit` | 1 | 4 | `BmSDK/Generated/BmGame/RBatmobileBooster.g.cs:82` | decoded (BmSDK/Generated/BmGame/RBatmobileBooster.g.cs:82, bit @2396, mask 0x1) |
```

quote present: **True**
cited `Research/BatmobileGrab/SAMPLER_FIELDS2.md:37`:

```
| Y held (boost) - the digital button byte | `RPlayerInput.bVehicleBoostButton` | 781 (0x30d) | `u8` | - | 1 | `BmSDK/Generated/BmGame/RPlayerInput.g.cs:944` | decoded (BmSDK/Generated/BmGame/RPlayerInput.g.cs:944, u8 @781) |
```

quote present: **True**

the row's own tokens:

| token | what it is | on the cited line | found at |
|---|---|---|---|
| `2396` | the booster bit offset | yes | — |
| `781` | the input byte offset | yes | — |

this review's label: **HOLDS** — both offsets the row names are on the cited lines

finding: holds: line 93 gives `bBoosting` @2396 mask 0x1 and line 37 gives `RPlayerInput.bVehicleBoostButton` @781, which are the row's two states.

### T-MA1 — `material blocks per `.rbm`, one set per LOD` (WRONG_VALUE)

row says (now): **17 blocks per LOD** (16 `CarPaintMM` + 1 `Window`); 200 `CarPaintMM` + 35 `Window` across 35 meshes
row proposes : keep

cited `Research/BatmobileGrab/COLOUR_PARAMS.md:69`:

```
| 38 | `Batmobile_V3_WheelArchs_NEW_MIC` (#767) | `Material0_BaseColour` | vector | [0.025787, 0.025787, 0.03, 1] | `f36abc2b` | VectorParameterValues field 0x168, item byte 262, tag @0x8 |
```

quote present: **True**

the row's own tokens:

| token | what it is | on the cited line | found at |
|---|---|---|---|
| `17` | the block count per LOD the row states | no | `Working/Translation/T3_FLEET.md:26` |

this review's label: **WRONG_CARD** — the row's value is a block count, not a colour

finding: the WRONG_VALUE label is wrong for this row: its own value cell is a block count ('17 blocks per LOD (16 CarPaintMM + 1 Window); 200 CarPaintMM + 35 Window across 35 meshes'), not a colour, so a colour line cannot be its wrong *value* - by G3-20b's definitions this is a WRONG_CARD. The underlying fact stands (line 69 does not answer the row), but the row's 17 / 200 / 35 counts were never checked.

### T-MA3 — ``CarPaintMM` diffuse colour` (WRONG_VALUE)

row says (now): effective `[0.056738, 0.05158, 0.06]` (albedo byte 0x83/0x7d/0x86)
row proposes : keep

cited `Research/BatmobileGrab/COLOUR_PARAMS.md:69`:

```
| 38 | `Batmobile_V3_WheelArchs_NEW_MIC` (#767) | `Material0_BaseColour` | vector | [0.025787, 0.025787, 0.03, 1] | `f36abc2b` | VectorParameterValues field 0x168, item byte 262, tag @0x8 |
```

quote present: **True**

the row's own tokens:

| token | what it is | on the cited line | found at |
|---|---|---|---|
| `0.056738` | the effective colour the row states | no | — |
| `0.025787` | the authored override the card carries | yes | — |

this review's label: **WRONG_VALUE** — the card carries the authored colour, not the effective one

finding: holds: line 69 is the authored override [0.025787, 0.025787, 0.03, 1] and the row states the effective [0.056738, 0.05158, 0.06]; the card's §5 (line 228-230) and §6 item 1 (line 240) do say the combine rule is UNKNOWN (944 of 944 expression slots zero), so the card cannot supply the effective colour.

### T-MA4 — ``CarPaintMM` gloss` (WRONG_VALUE)

row says (now): **0.45** in every paint block and in all 10 palette tints
row proposes : keep 0.45

cited `Research/BatmobileGrab/COLOUR_PARAMS.md:25` (HEADING):

```
## 2. Overrides carried by the chain's MICs (52)
```

quote present: **True**

the row's own tokens:

| token | what it is | on the cited line | found at |
|---|---|---|---|
| `0.45` | the gloss the row states | no | `Working/Translation/T3_FLEET.md:15` |

this review's label: **WRONG_CARD** — the card has no gloss parameter at all (and the line is a heading)

finding: the verdict is defensible but the citation is empty: line 25 is the section heading '## 2. Overrides carried by the chain's MICs (52)' - it carries no value. The numbers in the note are real but on other lines: Material0_Roughness 0.4 (MIC, line 33) and 0.25 (chain, line 111); Material0_Reflectivity 0.2 (line 32) and 0.25 (line 120). 'gloss' appears nowhere in COLOUR_PARAMS.md. Under G3-20b's definition (a different quantity) this is again a WRONG_CARD, not a WRONG_VALUE.

## 2. The three WRONG_CARD rows: is there a card that does answer them?

### T-MA2 — ``CarPaintMM` diffuse texture`

row says (now): 28 Batmobile textures shipped
G3-20b routed it to: `Research/BatmobileGrab/CHAIN.json (mass/inertia members) + Working/Translation/T3_FLEET.md`

answering card `Research/BatmobileGrab/TEXTURES.md:15`:

```
| Playable_BatmobileFunhouse_SF | `NEW_Batmobile_V2_BODY_D` | 4096×2048 | PF_DXT1 | 6042 | Playable_BatmobileFunhouse_SF.Batmobile_Body_MASTER (DiffuseColor); Playable_BatmobileJoker_SF.Batmobile_Body_MASTER (DiffuseColor); Playable_BatmobileMK2_SF.Ba |
```

answering card `Research/BatmobileGrab/SLOTS.md:27`:

```
| 2 | `Batmobile_V3_Mainbody_NEW_MIC` | MaterialInstanceConstant | `Material_Worn.Batmobile_V3_WheelArchs_NEW_MIC` | 37819 | Damage_Chapter_Mask=Textures.Batmobile_V3_TEXTURES_Body_Damage_ChapterMask, Normal_Map=Textures.Batmobile_V3_Body_N | CarPaintMM | body |
```

checked: {"textures_md_packages": 5, "textures_md_rows": 405}

finding: partly answerable. `Research/BatmobileGrab/TEXTURES.md:15` names the texture the row's source cell names (`NEW_Batmobile_V2_BODY_D`, 4096x2048, bound as DiffuseColor of `Batmobile_Body_MASTER`), and `SLOTS.md:27` maps the CarPaintMM slot (2, `Batmobile_V3_Mainbody_NEW_MIC`) into that chain. The row's '28 Batmobile textures shipped' is in neither card: TEXTURES.md lists 405 texture rows across 5 packages.

### T-P3 — ``.physicsc` shapes`

row says (now): written (G2-30): 11 driveable boxes map onto 7 donor hull slots; 21 are not driveable collision (18 destruction debris, 1 root placeholder, 1 turret, 1 jet fin); 11 T-8 parts have no slot
G3-20b routed it to: `Research/BatmobileGrab/PARTS_TABLE.jsonl (+ t16_collision.json for T-P3)`

checked: {"t16_collision_exists": true, "t16_collision_keys": ["schema", "generator", "card", "inputs", "bmak", "donor", "donor_parts", "decomposition", "hull_set", "bindings", "stations", "rows", "prose_fix", "summary"]}

finding: answerable, and G3-20b's own routing names it: `Working/Translation/t16_collision.json` exists and carries `hull_set`, `bindings`, `decomposition`, `stations`, `donor_parts` - the hull set and slot binding the row asks for. So for this row a card does exist; G3-20b simply did not open it.

### T-CO1 — ``.physicsc` collision shapes`

row says (now): donor's shapes, stations moved
G3-20b routed it to: `Research/BatmobileGrab/COLLISION_BOXES.md / COLLISION_CONVEX.md / SHAPES.md`

answering card `Research/JC3Grab/SHAPES.md:4`:

```
**233 vehicle entities / 234 `.physicsc` files**, 130513 objects, 18865 convex hulls (18865 verified convex), 302576 hull vertices, 238476 planes, 972642 hull indices, 1806301 collision-mesh vertices, and **6,382 compounds / 35,499 instance records** (25,769 with a part index).
```

checked: {"per_entity_json_dir_exists": false}

finding: partly answerable. `Research/JC3Grab/SHAPES.md` is the G2-8 card for the donor's `.physicsc` hulls (line 4: 233 entities, 18,865 convex hulls, 6,382 compounds, 35,499 instance records) and it has a hull->part wiring section. But its vehicle table prints only the 80 largest hull bboxes, the Serpente is not one of them, and the per-entity JSON it points at (`Research/JC3Grab/_JC3grab/hkx/out/`) is not in the repository - so the donor's own hull list is not in the card.

## 3. Cross-checks of G3-20b's own arithmetic

| check | result | detail |
|---|---|---|
| row statuses sum to the 105-row set | **PASS** | 105 rows; {'HOLDS': 6, 'OPEN': 96, 'WRONG_VALUE': 3} |
| the 18 first-pass rows tally as 6 HOLDS / 9 WRONG_CARD / 3 WRONG_VALUE | **PASS** | {'HOLDS': 6, 'WRONG_CARD': 9, 'WRONG_VALUE': 3} over 16 verdicts + 2 outside-group rows |
| every stored quote is a substring of the line it names | **PASS** | 12/12 quotes present |
| the T-M1 total quoted by G3-20b is the number on the cited line | **PASS** | PHYSICS_ROLES2.md:48 total 1627.097155, quote present: True |

## 3b. Notes

- **T-M1's cited total cannot be rebuilt from the histogram quoted next to it** — PHYSICS_ROLES2.md:48 states the total 1627.097155; the histogram on :49 lists 52 of the 56 masses and sums to 1317.076000, leaving 310.021155 on 4 values that line does not enumerate (the 275.0 of the first-eight list on :47 is one of them). The cited lines are correct; they are just not sufficient on their own.
- **G3-20b's §4 routing names `PARTS_TABLE.jsonl` without its directory** — the file is Research/JC3Grab/PARTS_TABLE.jsonl; Research/BatmobileGrab has no PARTS_TABLE.jsonl, so a reader following §4 from the BatmobileGrab listing finds nothing

## 4. Definitions this review uses

- **HOLDS** — the quoted line states what the row claims (LEDGER_G3B.md §1)
- **WRONG_VALUE** — the card's number is not the row's number (§1)
- **WRONG_CARD** — the card answers a different question than the row asks (§1)

Limit: this review judges the card/row pair only; a row can be right about the game and still be answered by the wrong card.

## 5. Reproduce

```
python Tools/scripts/review_g3b_claims.py --write
python Tools/scripts/review_g3b_claims.py --check
```
