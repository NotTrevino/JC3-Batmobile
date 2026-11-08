# G3-11 collision-source audit - is the number drivable or wreck?

**STATUS: done.** Of the five collision artefacts G3-11d did not already correct, **three carry the same
error class** (T-CO1, T-P3, `t16_collision.json`) and **two are clean** (T-CO3, T-PA3, whose numbers are
JC3 donor part-table values with no BmAK geometry in them).

The finding is systematic, not a single bad row: the ledger's collision section never quotes the
**drivable** car's geometry. Every box figure and every box/bodies count traces to
`Batmobile_V3_Destroyed_Physics` - the asset `PHYSICS.md` says in its own words is "what the game hands
to the **destroyed** wreck" and which has **no chassis body**. The drivable car's decoded geometry (3
physics-asset boxes + 56 convex element boxes across 43 + 13 elements) appears in none of the five rows
and in no field of `t16_collision.json`.

| artefact | verdict | what it quotes from BmAK | where that box actually lives |
|---|---|---|---|
| `T-CO1` | **MISMATCH** | `32 boxes` | 32 = one wreck vehicle's body count (32 boxes of 1 each); decoded box total is 131 = 3 drivable + 128 wreck |
| `T-P3` | **MISMATCH** | `32 collision bodies`, `11 driveable boxes` (with 21 not) | the 11/21 split is the wreck census's own categories: wheels 8 + doors 2 + cockpit 1 = 11, debris 18 + root 1 + turret 1 + fin 1 = 21 |
| `t16_collision.json` | **MISMATCH** | `bmak.bodies` 32, `bmak.box_count` 32, `bmak.largest` 316.155×63.418×109.881, categories | the whole `bmak` block is the wreck census; the drivable chassis triple (690.305/374.536/207.5) is absent from the file |
| `T-CO3` | **CLEAN** | - (38/42 parts, 4 wheels `-1`) | JC3 donor part table, not BmAK geometry |
| `T-PA3` | **CLEAN** | - (`body`→0, `door_f_l`→1, `engine`→7) | JC3 donor part table |
| `T-CO2` | **MISMATCH** *(reference)* | `316.15x63.42x109.88`, `3.1615x0.6342x1.0988 m` | the wreck wheel box; G3-11d's finding, re-confirmed here |

## Files written (all new; nothing existing was edited)

| file | what |
|---|---|
| `Tools/scripts/t_collision_sources.py` | the audit tool, `--write` / `--check`, 15 oracles |
| `Working/Translation/COLLISION_SOURCES_AUDIT.md` | 17,978 chars - one verdict per artefact, both censuses in full |
| `tmp/freebuff/reports/g3-11-collision-sources.md` | this report |

Not modified: `Working/Translation/T_ROWS.jsonl`, `Working/Translation/t16_collision.json`,
`Research/BatmobileGrab/COLLISION_GEOM.md`, `COLLISION_CONVEX.md`, `PHYSICS.md`, every `Tools/scripts`
file written by another card, and the game installs. Revert = delete the three files above.

## How a verdict is reached (so it is not hand-typed)

1. Parse the three censuses on every run: `COLLISION_GEOM.md` (3 drivable `RB_BodySetup` boxes),
   `COLLISION_CONVEX.md` (56 drivable convex element boxes, extents = max − min, plus the 2 unions),
   `PHYSICS.md` (32 wreck bodies per vehicle, 128 records total).
2. Pull every triple (`a x b x c`) and every `N boxes` / `N bodies` out of each artefact; triples are
   matched in **both** cm and m, since T-CO2 quotes its box once in each.
3. Match each figure against the censuses (sorted-axis, 0.01 cm tolerance). A figure that only matches
   wreck records is labelled **wreck**; a count is labelled by which census count it equals.
4. The artefact's verdict follows: all figures wreck → MISMATCH, no figures → CLEAN, mixed → MIXED.

`--check` recomputes all of this and byte-compares the document; 15/15 oracles pass, none of the
figures is unsourced.

## The three censuses, as the tool recomputes them

- **Drivable**: `COLLISION_GEOM.md` → 169750 `Batmobile_Chassis` boxes 0 and 1
  (`690.305/374.536/207.500` and `679.585/345.688/103.500` cm) and 169751
  `Batmobile_Rig_Weapons_Trans` (`166.177/189.365/39.800` cm); `COLLISION_CONVEX.md` → 43 + 13 = 56
  element boxes, unions `695.4/492.9/294.5` and `670.9/318.3/224.1` cm.
- **Wreck-only**: `PHYSICS.md` → asset `Batmobile_V3_Destroyed_Physics`, 4 vehicles × 32 bodies =
  128 records, largest `SUSP1_Wheel_Rear_Right_Mesh` `317.942×64.552×97.966` cm.
- **Arithmetic**: 3 + 128 = **131 decoded boxes**, and the largest single box of all of them is the
  **drivable chassis** at 690.305 cm. That is G3-11d's finding, re-derived from the docs rather than
  restated.

The classification witness is `PHYSICS.md`'s own sentence (quoted verbatim in the document):

> **There is no chassis body.** The 32 bones cover wheels/suspension, cockpit, doors, jet fins, the
> turret and the `Object*_frag_*` debris pieces — the main hull has no `RB_BodySetup`. Hull collision
> for the *driveable* car therefore does not come from this asset …

So a row that calls a wreck box "the car's collision" is not merely imprecise about which file it read;
it is quoting an asset the game attaches to the destroyed car.

## Commands and verbatim output

### 1. Scope and the location of the known bad number

```
$ cd E:/Modding/JC3-Batmobile && ls -l Working/Translation/T_ROWS.jsonl Working/Translation/t16_collision.json Research/BatmobileGrab/COLLISION_GEOM.md Research/BatmobileGrab/COLLISION_CONVEX.md
-rw-r--r-- 1 User 197121  13994 Nov  3 01:59 Research/BatmobileGrab/COLLISION_CONVEX.md
-rw-r--r-- 1 User 197121   4937 Nov  3 01:16 Research/BatmobileGrab/COLLISION_GEOM.md
-rw-r--r-- 1 User 197121 133520 Oct 31 08:35 Working/Translation/T_ROWS.jsonl
-rw-r--r-- 1 User 197121  23533 Oct 28 07:06 Working/Translation/t16_collision.json

$ grep -n '"id":"T-CO' Working/Translation/T_ROWS.jsonl
86:{"id":"T-CO1","doc":"T-2b","section":"7. Collision — 128 BmAK boxes, and a JC3 chassis we already moved","cells":["T-CO1","32 boxes (bone, centre, extents)","`.physicsc` collision shapes","—","donor's shapes, stations moved","JC3 shapes now decode (G2-8): ...","read","hull bbox of the built vehicle vs its mesh"],"dispo":"keep","why":"donor chassis by decision","edits":0}
87:{"id":"T-CO2",... "largest box 316.15x63.42x109.88 cm" ...}
88:{"id":"T-CO3",... "donor's: 38/42 = 1, the 4 wheels = 0 (`world_collision_body_id` -1)" ...}

$ grep -rn "316\.1\|63\.42\|109\.88" Research/BatmobileGrab/*.md Working/Translation/*.json Working/Translation/*.jsonl
Research/BatmobileGrab/BOX_UNION_FRAME.md:74:| 8 | `SUSP1_Wheel_Rear_Left_Mesh` | 0 | -67.15 / -104.00 / 122.35 | -117.41 / -17.57 / -12.15 | 316.15 / 63.42 / 109.88 | inside |
Research/BatmobileGrab/COLLISION_LEDGER_CHECK.md:11:- largest wreck box: bone `SUSP1_Wheel_Rear_Right_Mesh` export `5162`, extents `[317.9422, 64.5518, 97.9657]` cm; T-22's recorded largest (the triple the ledger quotes) is a different box: bone `SUSP1_Wheel_Rear_Left_Mesh`, extents `[316.155, 63.418, 109.881]` cm
Research/BatmobileGrab/PHYSICS.md:33:| 8 | `SUSP1_Wheel_Rear_Left_Mesh` | 1 box | 316.155×63.418×109.881 | (-117.414, -17.569, -12.155) | wheel/suspension |
Research/BatmobileGrab/PHYSICS_REVERIFY.md:34:| 8 | 5074 | `SUSP1_Wheel_Rear_Left_Mesh` | 1 | 316.155x63.418x109.881 | (-117.414, -17.569, -12.155) | wheel/suspension |
Working/Translation/t16_collision.json:30:    316.155,
Working/Translation/t16_collision.json:32:    109.881
```

The triple is **absent from `COLLISION_GEOM.md` and `COLLISION_CONVEX.md`** and present only in the
wreck data (`PHYSICS.md` row 8, re-verified in `PHYSICS_REVERIFY.md`) - the first hard confirmation
that T-CO2 quotes a wreck box.

### 2. The JSON's own BmAK block - the same numbers as data, not prose

```
$ PYTHONIOENCODING=utf-8 uv run python -   # dump t16_collision.json
=== bmak ===
{
 "packages": 4,
 "bodies": 32,
 "layouts_identical": true,
 "categories": {
  "root placeholder": 1,
  "wheel/suspension": 8,
  "destruction debris": 18,
  "turret": 1,
  "cockpit": 1,
  "door": 2,
  "jet fin": 1
 },
 "largest": {
  "bone": "SUSP1_Wheel_Rear_Left_Mesh",
  "extents_cm": [316.155, 63.418, 109.881],
  "box_m": [3.1615, 0.6342, 1.0988]
 },
 "spheres": 0,
 "box_count": 32
}
=== rows ===
{"T-P3": "| T-P3 | 32 collision bodies (boxes) | ... 11 driveable boxes map onto 7 donor hull slots; 21 are not driveable ... |",
 "T-CO2": "| T-CO2 | largest box 316.15x63.42x109.88 cm | ... |",
 "T-CO3": "| T-CO3 | — | ... |"}
=== summary ===
{"bodies": 32, "mapped_to_a_slot": 7, "mapped_bodies": 11, "unmapped": 21, "hull_slots": 54,
 "parts_colliding": 38, "rows": 3, "dispositions": {"T-P3": "next", "T-CO2": "next", "T-CO3": "keep"}}
```

The JSON reproduces the wreck census exactly (categories, 32 bodies, the same wheel box), and contains
no drivable figure at all. `bmak.largest` is the same triple T-CO2 quotes.

### 3. Defects in my own first extraction, caught before the result

The first `derive()` run mis-parsed two figures. I read the debug output rather than trusting the
document, and both are fixed:

```
$ PYTHONIOENCODING=utf-8 uv run python -   # import the tool and print its verdicts
counts {'drivable_boxes': 3, 'drivable_convex_elements': 56, ... 'wreck_boxes_total': 128, 'all_boxes': 35}
T-P3                   MIXED     32 collision bodies->wreck; 11 driveable boxes->unsourced
T-PA3                  CLEAN
T-CO1                  MIXED     1 32 boxes->unsourced
T-CO2                  MIXED     316.15x63.42x109.88->wreck; 3.1615x0.6342x1.0988->unsourced
T-CO3                  CLEAN
t16_collision.json     MISMATCH  bmak.largest.extents_cm->wreck; bmak.bodies->wreck; bmak.box_count->wreck
FAIL scope rule reproduces G3-11d's 5 collision rows :: T-P3, T-PA3, T-CO1, T-CO2, T-CO3
FAIL every figure quoted by a row reached a verdict (none unsourced) :: ...
```

Three bugs, all fixed: (a) the count regex swallowed the `1` of the id (`T-CO1` + `32 boxes` →
`1 32 boxes`), fixed with a lookbehind and an explicit `driveable boxes` alternative; (b) T-CO2's
metre-denominated triple matched no centimetre census, so figures are now tested in both units;
(c) the scope oracle compared a file-ordered list to a sorted one. The final document's `--check`
fails if any of the three regresses, because the verdicts are recomputed from the figures.

### 4. Final write and check

```
$ cd E:/Modding/JC3-Batmobile && PYTHONIOENCODING=utf-8 uv run python Tools/scripts/t_collision_sources.py --write && PYTHONIOENCODING=utf-8 uv run python Tools/scripts/t_collision_sources.py --check; echo "EXIT=$?"; ls -l Working/Translation/COLLISION_SOURCES_AUDIT.md Tools/scripts/t_collision_sources.py
wrote Working/Translation/COLLISION_SOURCES_AUDIT.md (17978 chars)
OK Working/Translation/COLLISION_SOURCES_AUDIT.md (17978 chars)
CHECK PASS
EXIT=0
-rwxr-xr-x 1 User 197121 33938 Nov  5 15:25 Tools/scripts/t_collision_sources.py
-rw-r--r-- 1 User 197121 18093 Nov  5 15:25 Working/Translation/COLLISION_SOURCES_AUDIT.md
```

The 15 oracles, all PASS: scope rule reproduces G3-11d's 5 rows; T-P3's 11/21 split is the wreck
census's categories; T-P3 names exactly the wreck's debris/root/turret/fin counts (18/1/1/1); the
drivable asset holds 3 boxes; the convex census holds 43 + 13; the wreck header is 32 bodies/vehicle
and 128 records and parses to 32 rows; the wreck says it has no chassis body; no wreck bone is the
chassis; 3 + 128 = 131; the largest single box is the drivable chassis at 690.305; no row figure is
unsourced; the JSON's `bmak` block is the wreck census; its categories match exactly; it holds no
drivable figure; its row texts match `T_ROWS.jsonl`.

## UNKNOWNs, each with what was tried

1. **Whether the wreck boxes coincide with the drivable car's volume in game.** The wreck asset has no
   chassis body, so its boxes are per-bone debris envelopes in the wreck rig's frame. Tried: the frame
   verdicts in `COLLISION_GEOM.md` and `COLLISION_FRAME.md` (they cover the physics-asset boxes, not
   these). Would need a decode of the wreck rig's transform.
2. **Which convex element is the hull silhouette per mode.** All 56 elements are decoded and bounded,
   but no field names them body/skirt/fin; the seventh array and the 14-byte trailer stay UNKNOWN in
   `COLLISION_CONVEX.md`. Tried: that file's oracles and `COLLISION_GEOM.md`'s mode selector. Would need
   `FKConvexElem` names or a per-element effect of `SetBatmanVsBatmobileCollisionMode`.
3. **Whether the donor's 54 hulls were authored from the drivable boxes.** The hull set is decoded
   (`t16_collision.json` `hull_set`, longest axis 3.679 m) but its authoring inputs are not in the
   file. Tried: `hull_set` and `decomposition.parameters` (prose, no BmAK figure).
4. **The intended repair.** This card classifies and quantifies; it does not rewrite another card's
   rows or the JSON's fields. The evidence-backed fix is to replace the wreck superlative with the
   drivable chassis triple and to rename the `bmak` block as the wreck census - a G3-11/G3-11d
   decision, named in the document but not applied here.

## COMPROMISES

None. No lore or accuracy compromise is proposed; the audit only re-labels sources.

## One consequence for the build

`t16_collision.json`'s `hull_set` still maps JC3 donor hulls onto **wreck** bodies (11 bodies onto 7
slots, 54 hulls total), and its `scale_k` for the body uses the JC3 body bbox (3.495 / 2.271 / 7.025 m),
not the BmAK wreck boxes, so the build itself is not obviously wrong - but the *provenance* sentence in
the ledger ("11 driveable boxes") is. That distinction is worth keeping when the rows are repaired: the
build's inputs are the JC3 side plus the drivable 690 cm box if anything, never the 316 cm wreck wheel.
