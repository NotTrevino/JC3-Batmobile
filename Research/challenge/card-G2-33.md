# Assumption challenge — G2-33 · light system consolidated

**Card:** `GRAB_BACKLOG.md` §G2-33 (line 807), §12 row (line 1316).
**Outputs challenged:** `Research/JC3Grab/LIGHT_SYSTEM.md`, `LIGHT_SYSTEM.json`,
`Tools/scripts/jc3lights.py`, MODLOG §"G2-33 · Light system consolidated — done" (line 10720).
**Rules applied:** `GRAB_BACKLOG.md` §0.5 (R1–R14), especially R5 (a member is what it does, not what
it is called), R4, R11.

**Method.** Every number below was re-derived from the inputs the card names: the 232 entity caches
(`E:/Modding/JustCause3/_grab/entities/`), the 232 `.epe` graphs (`E:/Modding/JustCause3/_grab/detail/`),
`Research/JC3Grab/PARTS_TABLE.jsonl` (233 rows), `GEOMETRY.jsonl` (56,136 rows),
`INDEX.jsonl`, `Research/BatmobileGrab/LIGHTS.json`, and `rbmhdr.hash_jenkins`. No game was
launched, nothing was written under `D:/Games`, no archive was opened, nothing committed. This
report is the only file written.

---

## VERDICT summary

| # | assumption | verdict |
|---|---|---|
| 1 | 3,217 entries / 223 vehicles / 224 modules / 25 members each | **HOLDS** — exact |
| 2 | 9 behaviour values with the counts in §1 | **HOLDS**; the MODLOG's `None 1,156` is wrong (it is 1,177) |
| 3 | "no file joins the two light lists"; preset ids unknowable | **BROKEN** — 381 of the 404 `.epe` preset names are `hash_jenkins` of a module `preset_id` |
| 4 | `.epe` side: 3,972 / 233 / 412 objects, 404 names, 13 members, no part binding | **HOLDS** |
| 5 | 393 presets, 17 with `preset_id = 0`, 34 inconsistent | **HOLDS** — 34 is robust across all shape members |
| 6 | binding census 3 / 27 / 6 / 13 | **WEAK** — the buckets overlap; 32 entries land on `has_lights = 0` parts, not 6 |
| 7 | "`has_lights` is a flag, not a gate; every vanilla light part has it set" | **WEAK** — 32 entries target unlit parts (26 of them also name-mismatched) |
| 8 | donor facts: 42 parts, 12 lit, 10 `Land_Light`, part 26 unlit | **HOLDS** |
| 9 | `CarLight` 11,367 blocks / 220 vehicles / stride 12 / uint16 / 6 slots | **HOLDS** |
| 10 | `CarLight` layout 1085 B header, 16 B gap, buffers 12/24/2, 190/193 round-trip | **HOLDS** as cited (MODLOG §17, solver on disk) |
| 11 | the recipe's 13 shape members are the donor's `lights[2]`, values exact | **HOLDS** |
| 12 | the recipe is a **spot**light / LGT-2's "battle-mode spotlight" | **WEAK/BROKEN** — `light_type 0` is a point lamp; only `light_type 1` ever carries a cone |
| 13 | `deformable_transform` is "decoded (mapped)" | **BROKEN** as classed — a constructed node path; the cited file says `needs-lig-bone`, and the bone occurs nowhere in the JC3 data |
| 14 | colour 160,180,255 ÷ 255 = 0.627 / 0.706 / 1.0 | **HOLDS** the arithmetic; the sRGB/255 convention is unstated (WEAK) |
| 15 | the wheel part cannot host the light as-is (`has_lights` 0, `CarPaintMM` only) | **HOLDS** — 99 donor wheel meshes, 0 `CarLight` blocks |
| 16 | 588 "light" paths outside `jc_vehicles`, 0 preset table | **HOLDS** (count reproduced; the 588 include `flight_*` names) |
| 17 | `--check` proves the document | **WEAK** — self-consistency only; §3 and §7a pass while being wrong |

Headline: **the census is exact and the recipe's numbers are real, but the card's biggest open
question is answered by the project's own hash function.** The module's `uint32 preset_id` is the
Jenkins hash of the `.epe` preset *name*: 381 of 393 ids decode to a name (`Dash_Light` =
`2763198432`, 170 entries, the donor's dashboard lamp). So the two "lists" are one preset vocabulary
in two encodings — not two disconnected lists — and "no file joins them" is false. Two smaller
things also need rewriting: `light_type 0` is a point light, so the "spotlight" language is a name,
and the recipe's anchor is a *fabricated* node path classed as decoded.

---

## 1. 3,217 entries over 223 vehicles, 224 modules, 25 members each

**Claim.** Scope table and §1: 223 vehicles with a `VehicleDynamicLights` module, 3,217 entries,
25 members each, 1…45 per vehicle, "a vehicle may carry two modules (the cargo-tank plane does) and
each numbers its entries from `lights[0]` again".

**Test.** Independent parse of `lights[i].<member>` in every cache:

```
caches 232 | vehicles with module 223 | modules 224 | entries 3217
multi-module vehicles: [('v4603_plane_urga_cargotransport__…_military_cargo_tank.ee.json', 2)]
members-per-entry histogram: {25: 3217}
entries per vehicle min/max: 1 45
vehicles without module: 9
cargo plane light modules: v4603_…_lights.vmodc 24 entries + v0201_…_mediumtank_lights.vmodc 21
```

24 + 21 = 45, which is the fleet maximum — the doubled module is the same cargo-tank variant that
carries two `VehicleDamage`, two `Buoyancy` and two `WaterInteraction` modules.

**Verdict: HOLDS.**

## 2. The behaviour census

**Claim.** §1: `None` 1177, `HeadLight` 1027, `TailLight` 301, `LeftSignal` 253, `RightSignal` 253,
`Reverse` 191, `SirenLightOn` 9, `SirenLightOnOffFast` 3, `SirenLightOffOnFast` 3. MODLOG: "`None`
1,156".

**Test.**

```
behaviours: [('None', 1177), ('HeadLight', 1027), ('TailLight', 301), ('LeftSignal', 253),
             ('RightSignal', 253), ('Reverse', 191), ('SirenLightOn', 9),
             ('SirenLightOnOffFast', 3), ('SirenLightOffOnFast', 3)]
```

**Result.** The generated document is right; the MODLOG prose is 21 entries short (1,156 vs 1,177).
The file that the next card will read is the document, so this is a log-only defect — worth fixing
because the log is the card's "done" evidence.

**Verdict: HOLDS (doc), the MODLOG figure is wrong.**

## 3. "No file joins the two light lists"

**Claim.** §2: "They are **not the same list** … its `preset_id` is a **string** … while the
module's `preset_id` is a **uint32** hash … **No file joins the two lists**, so the module is the only
side that binds a light to a part; which one the renderer reads is UNKNOWN". MODLOG repeats it.

**Test.** Hash every `.epe` preset name with the function the card already trusts, and intersect with
the module ids (the same check the card runs on `part`, `behavior` and `deformable_transform`):

```
module ids 393   ids matched to an epe name 381   ids with no name 12
epe names with no module id 23
Dash_Light hash 2763198432   is a module id? True
top ids: 2763198432 x170, 1358616627 x128, 1271816577 x128, 4272096469 x126, 1814273923 x122
mapping samples: (3358775008,'Rear_Brake'), (3815211005,'Rear_Left_Reverse'),
                 (1358616627,'Rear_Left_Turn'), (2763198432,'Dash_Light'),
                 (1814273923,'Front_Left_Volumetric')
```

381 of 404 names (94 %) hash exactly onto an id in use; 12 ids have no name in the 404; 23 names are
unused by any entry. And the join is meaningful: the 16 preset names containing "wheel" are all
aircraft gear/landing lamps or a moped steering lamp when resolved this way —

```
Cargo_Headlight_Wheel_Left   → cargotransport_light_landing_l   x6
Capstone_Fighter_Headlight_Wheel(+_Point,_Volume) → fighterjet_gear_base_f  x3 each
Vintage_Headlight_Wheel_*    → vintagefighter_gear_l / _gear_f_r  x2 each
Modern_Moped_Front_Wheel_*_Turn → modernmoped_lower_steering  x2 each
```

which is exactly what the recipe needed to know ("none is a wheel-arch lamp") and could not look up
without the join.

**Result.** No decoded *table* joins the two sides, but the card's own hash function does, on 94 % of
the names. "No file joins the two lists" is therefore false in the sense that matters for the recipe,
and the module `preset_id` is not an opaque uint32 — it is a preset *name* for 381 of 393 ids. What
remains genuinely UNKNOWN is narrower: which of the two representations the renderer reads, and
whether a preset overrides the entry (still not decodable). Everything the card says about preset
*values* survives — see §5.

**Verdict: BROKEN.**

## 4. The `.epe` side: counts and members

**Claim.** §2: 3,972 `SVehicleLight` objects, 233 `SVehicleLights`, 412 `SVehicleLightList`, 404
preset names, 13 members, "no part, no part index and no transform".

**Test.** Walk all 232 graphs:

```
graphs 232 | SVehicleLight 3972 | SVehicleLights 233 | SVehicleLightList 412
members on SVehicleLight: 16 keys = _object_id, name, name_hash + the 13 data members
  (diffuse, enabled, falloff_start, is_shadow_caster, min_luminosity, multiplier, near_cap,
   preset_id, radius, spot_angle, spot_inner_angle, volume_intensity, volumetric_mode)
distinct preset names: 404   top: Dash_Light 221, Front_Left_Turn 145, Front_Primary_Head 145 …
has_lights hits on .epe SVehicleLight: 0
```

**Result.** Exact, including the "13 members" (16 keys minus the three bookkeeping ones) and the
absence of any part binding or `has_lights` on this side.

**Verdict: HOLDS.**

## 5. 393 presets, 17 zeros, 34 inconsistent

**Claim.** §3: 393 distinct `preset_id` hashes, 17 shipped entries with `preset_id = 0`, 34 presets
with more than one value tuple (top `1271816577` x17, `1358616627` x16 …).

**Test A — counts.**

```
distinct preset ids 393 | entries with preset 0: 17
presets with >1 tuple: 34   (signature = the generator's 9 shape members)
presets with >1 tuple over ALL shape members (excluding part/part_index/anchor/hashes): 34
```

**Test B — does 0 mean "no preset"?** `hash_jenkins("")` = **834184464**, not 0, and no `.epe` name
hashes to 0. So 0 is not a valid name hash: the "no preset" reading is supported by the data, not
merely by the 17 precedents.

**Result.** All three numbers hold, and the 34 is not an artefact of a narrow signature (it is 34
with the whole shape tuple too). My first pass counted 57, but that included `part`/`part_index`,
i.e. the *binding*, which is not a preset value — the card's 34 is the right definition. The one
upgrade: `preset_id = 0` can be moved from UNKNOWN to "not a name hash" (§8 still right that the
engine's use of it is UNKNOWN).

**Verdict: HOLDS.**

## 6. The binding census: 3 / 27 / 6 / 13

**Claim.** §4 table: 3 `part_index` misses, 27 entries resolving to a different part name, 6 entries
on a `has_lights = 0` part, 13 lit parts with no entry.

**Test.** Resolve every entry against `PARTS_TABLE.jsonl` (key = the bare entity name):

```
entities matched 232   entries processed 3217
misses 3   name mismatches 27   on unlit parts 32
unlit AND name matches: 6   name-mismatch AND unlit: 26   index miss: 3
lit parts with no entry: 9   (+4 on a parts row with no light module = 13)
```

`jc3lights.bind()` counts `unlit` only **after** the name check and `continue`s on a name mismatch,
so "6" is "entries that resolve by name to an unlit part". There are **32** entries whose resolved
part is unlit — the 26 name-mismatched ones (heavyassault wing/tail lights sitting on missile parts)
are also unlit but are filed only under "name mismatch". The buckets are presented as disjoint and
are not.

The 13 is correct by its definition but hides a fact: `PARTS_TABLE.jsonl` has **233** rows, one more
than the 232 caches — `v2602_helicopter_urga_lightassault_military_01_custom_mm230.ee`, 44 parts,
4 lit — an entity with **no light module at all**. 9 + 4 = 13.

**Result.** Two of the four numbers reproduce; the "6" understates the phenomenon by 5x, and the
overlap between the "27" and the "6" is not stated. The conclusion ("flag, not gate") is unaffected
and in fact strengthened.

**Verdict: WEAK.**

## 7. "Every vanilla light part has `has_lights` set"

**Claim.** §4: "`has_lights` is a **flag the artist sets, not a gate the loader enforces** … The flag
is still the right one for a new light part: every vanilla light part has it set."

**Test.** The same resolution as §6, counted per entity: 32 entries bind to a part whose flag is 0 (6 bavarium turret, 6 heavyassault wing/tail, 20 on the
cargo plane's medium-tank parts). Those parts are not "light parts" by name, but they *are* light
targets the game ships.

**Result.** The recommendation stands for parts *named* as lights; the universal form does not: the
fleet ships 32 lamps on parts whose flag is clear, and the cargo plane's tank-part lamps are the
largest single block. "Every vanilla light part" needs to be "every part named `*_light*`".

**Verdict: WEAK.**

## 8. The donor facts

**Claim.** §4: donor 42 parts, 12 with `has_lights = 1`, 10 of them `Land_Light`, the rest
`Land_Body` x1 and `Land_Generic` x1; "the donor's left tail-light part alone carries a `TailLight`,
a `LeftSignal` and a `Reverse` entry"; §7c: `sportsmuscle_wheel_f_l` ships `has_lights = 0`.

**Test.**

```
donor parts 42  lit 12  lit damage types: Land_Light 10, Land_Body 1, Land_Generic 1
donor part 26: {'n': 'sportsmuscle_wheel_f_l', 'dt': 'Land_Wheel', 'parent': 3, 'lights': 0,
                'm': '…/sportsmuscle_wheel_f_l.lod'}
donor module: lights[0] TailLight idx 8, lights[1] LeftSignal idx 8, lights[15] Reverse idx 8
```

**Result.** Exact, including the triple-lamp part at index 8 and the wheel part's flag.

**Verdict: HOLDS.**

## 9. `CarLight`: 11,367 blocks, 220 vehicles, stride 12, 6 slots

**Claim.** §5 table: 11,367 blocks in 11,367 meshes / 220 vehicles, vertex stride 12 B x11,367,
index width 2 B x11,367, 6 material slots x11,367.

**Test.** Count every geometry block of `type == "CarLight"`:

```
CarLight blocks 11367   meshes 11367   entities 220
vertex_stride {'12': 11367}   material_slots {'6': 11367}   index_width {'2': 11367}
errors {'None': 11367}
payload keys: positions_at, positions_bytes, indices_at, indices_bytes, index_width  (all 11367)
```

**Result.** Every number and every invariant holds. The payload carries offsets and counts only —
no material bytes — which is consistent with the card's "parameters UNKNOWN": the decoder does not
emit them, so nothing here contradicts it.

**Verdict: HOLDS.**

## 10. The `CarLight` layout

**Claim.** §5: static header 1085 B, 16 B gap, buffers `[12, 24, 2]`, "MODLOG.md §17 … round-trip
190/193 blocks byte-identical, 0 mismatched", solver `Tools/scripts/_probe_layout.py`.

**Test.** Read MODLOG §17 and check the solver is on disk:

```
| CarLight 0xDB948BF1 | 1085 B | 16 B | (12, 24, 2) |
Donor round-trip: 100/193 -> 166/193 -> 190/193 byte-identical, 0 mismatched
-rw-r--r-- Tools/scripts/_probe_layout.py  (7,244 B)
```

**Result.** The card quotes its source correctly. This is inherited evidence (G2-33 did not re-run
the solver), which is fine and is what the citation is for.

**Verdict: HOLDS** (as cited).

## 11. The recipe's shape members are the donor's `lights[2]`

**Claim.** §7a: 13 shape members (range 2, falloff 0, near_cap 1, multiplier 1, min_luminosity 0,
light_type 0, blinking 0, angle 10, cast_shadows 0, projected_texture_index -1, volumetric_mode 0,
volume_intensity 1, uvscale 1/1) copied from "the donor module `lights[2]` (the shipped steady
HeadLight point lamp, anchor `|sportsmuscle_LOD1|body|dashboard_LIG`)".

**Test.** Dump the donor's 21 entries:

```
lights[2] HeadLight part=sportsmuscle_body idx=0 range=2 angle=10 type=0 blink=0 mult=1
          anchor=|sportsmuscle_LOD1|body|dashboard_LIG
          diffuse .803/.908/1.0  preset_id=2763198432
```

**Result.** Every shape value matches, and the entry is exactly what the card calls it: a steady
(`blinking` 0) `HeadLight` whose `light_type` is **0**. The recipe then changes two things it says
it changes: the colour (BmAK) and `preset_id` (to 0). The reference light's own preset is
`2763198432` = `Dash_Light` (§3), which is now decodable — worth stating, because "preset 0" versus
"the donor's own preset" is a real choice rather than an unknowable one.

**Verdict: HOLDS.**

## 12. "The recipe is a spotlight" / LGT-2's "battle-mode spotlight"

**Claim.** §6/§7: LGT-2's battle-mode spotlight is "a second row with the same 25 members";
§7a: the BmAK `SpotLightComponent` ships radius/cone/brightness 0.

**Test A — does `light_type` mean point/spot?** Cross-tab of the two members over all 3,217 entries:

```
(light_type, angle) -> entries
(0, 10) 2494 | (1, 40) 628 | (1, 50) 74 | (1, 45) 12 | (1, 30) 4 | (1, 25) 3 | (1, 35) 2
light_type: {0: 2494, 1: 723}   angle: {10: 2494, 40: 628, 50: 74, 45: 12, 30: 4, 25: 3, 35: 2}
```

The correlation is perfect: `light_type 0` always carries `angle 10`, and every cone (25–50°) is
`light_type 1`. `angle 10` on a type-0 lamp is the unused default, not a 10° cone.

**Test B — what the BmAK actually has.** From `LIGHTS.json`:

```
LWheelLight  (VEHLT_HeadLight)  SpotLightComponent: OuterConeAngle 0.0, Radius 0.0,
            Brightness 0.0, LightColor [160,180,255,0], FalloffExponent 1.0
LWheelLight  (VEHLT_BattleModeLight) same socket, same component shape
LWheelLight_top / _bottom: LensFlareComponent only (no light component)
```

**Result.** The recipe copies `light_type 0`, i.e. it ships a **point** light with the angle field at
its default. That is a defensible choice for an arch glow, but (a) calling it a "spotlight" is the
UDK class name (`SpotLightComponent`) doing the work while its cone, radius and brightness are all
0, and (b) LGT-2's "battle-mode spotlight … the same 25 members" would ship a second point light
with no cone — a spotlight in name only. If a cone is wanted, `light_type` must be 1 and `angle`
taken from the 723 cone entries (25–50°), not from `lights[2]`.

**Verdict: WEAK for LGT-1, BROKEN for the LGT-2 "spotlight" wording.**

## 13. `deformable_transform` is "decoded (mapped)"

**Claim.** §7a row: `deformable_transform` = `|sportsmuscle_LOD1|wheel_f_l|Wheel_Frnt_Left_Disc|
Wheel_Frnt_Left_Disc_LIG`, class **"decoded (mapped)"**, source "LIGHTS.json `jc3_anchor` …
G1-17's translation of the BmAK socket chain". §6 and §7b call the same thing UNKNOWN.

**Test.** Read the cited field and search the JC3 data for the node:

```
LIGHTS.json vehicles[0].entries[5].anchor_state = "needs-lig-bone: the assembled part has no bone
                                                  hierarchy yet"
grep -rl "Wheel_Frnt_Left_Disc" E:/Modding/JustCause3/_grab   -> no hits
grep -rl "Wheel_Frnt_Left_Disc" E:/Modding/JustCause3/JC3-Batmobile/Research/BatmobileGrab -> LIGHTS.json
```

The bone name exists only on the BmAK side; the `_LIG` suffix follows the donor's anchor convention
(`|sportsmuscle_LOD1|body|dashboard_LIG`), but the node itself is not in any JC3 file the project
decodes, and the card's own §6 says so ("not in the RBM, not in the parts `bones` array and not in
the deform table").

**Result.** The value is a *constructed* string — BmAK bone + donor path grammar + `_LIG` — and its
own source labels it "needs-lig-bone". Classing it "decoded (mapped)" in the one table that is meant
to be audited ("a source for every value") is the exact failure mode R5/R4 warn about. The §7b row
gets it right; §7a must match.

**Verdict: BROKEN** (classification; the value may still be the right guess).

## 14. Colour ÷ 255

**Claim.** §7a: `diffuse.R/G/B` = 0.627451 / 0.705882 / 1.0 from BmAK `LightColor [160, 180, 255]`
"sRGB -> 0..1".

**Test.**

```
160/255 = 0.627451   180/255 = 0.705882   255/255 = 1.0        (arithmetic exact)
donor lights[2].diffuse = 0.803 / 0.908 / 1.0                    (0..1 floats in the module)
BmAK LightColor = [160,180,255,0]                                (0..255, alpha 0, Brightness 0)
```

**Result.** The division is the only sane bridge and the target range is right. What is *not* shown
is the transfer function: whether the module's floats are sRGB/255 or linear/255 (the donor's own
0.803/0.908 look like sRGB), and the alpha 0 with brightness 0 means the BmAK lamp itself emits
nothing, so there is no rendered colour to check against. The doc converts one side (colour) and
refuses to convert the others (range, angle) for lack of a unit — consistent, but the colour
conversion is an unstated convention, not a decode.

**Verdict: HOLDS arithmetic, WEAK convention.**

## 15. The wheel part cannot host the light as-is

**Claim.** §7c: `sportsmuscle_wheel_f_l` ships `has_lights = 0` and "its meshes are `CarPaintMM`
only (all four wheel parts, every LOD): there is no `CarLight` block to carry the glow and no anchor
node".

**Test.**

```
donor part 26: lights 0, model …/sportsmuscle_wheel_f_l.lod
GEOMETRY rows for donor + 'wheel': 99 meshes, 63 distinct paths, block types {'CarPaintMM': 99}
```

**Result.** Exactly right: no `CarLight` block anywhere in the donor's wheel meshes, so a new part
(or a new block) is required. This is the cleanest justification in the card.

**Verdict: HOLDS.**

## 16. "588 light paths outside `jc_vehicles`, 0 preset table"

**Claim.** §8: "588 archive paths mention 'light' outside `jc_vehicles` and **0** is a vehicle
light-preset table - they are environment models and localisation. So the preset name space is
per-vehicle data, not a global table (at least in the decoded index)."

**Test.**

```
paths mentioning light 1517 | outside jc_vehicles 588
extensions: hmddsc 107, nl 92, wavc 90, toc 84, ban 54, fl 38, ddsc 26, rbm 14
grep INDEX for preset files: environment_presets_config.bin, map-export.environc,
                             global/environment_presets.bl, settings/road_presets.bin
grep INDEX for 'Dash_Light': 0 hits
```

**Result.** The count reproduces, and no vehicle light-preset table exists in the index. Caveat the
card should carry: the 588 includes `flight_*` dialogue and sound names (the search is a substring),
so the number is an upper bound on "light" assets.

**Verdict: HOLDS.**

## 17. What `--check` proves

**Claim.** §9/§11 and MODLOG: "`--check` re-reads every input, rebuilds both files in memory,
compares them byte-for-byte and runs the assertion table"; the tamper test shows it failing on an
edited number.

**Test.** `python Tools/scripts/jc3lights.py --check` → exit 0, the PASS line. The 25 assertions
include `recipe values that are UNKNOWN 0` — which is the problem: the table asserts that no recipe
value is *labelled* UNKNOWN, not that every value is *verified*. §7a's "decoded (mapped)" anchor
satisfies it; the "no file joins the two lists" sentence is prose the check does not test.

**Result.** `--check` proves the document equals its generator and that the generator's own
assertions hold. It cannot catch a wrong class label or a wrong prose claim — both of which this
report finds.

**Verdict: WEAK** (necessary, not sufficient — the same defect as G2-28 §20).

## 18. "A recipe with every member value sourced"

**Claim.** The card's Done criterion and MODLOG: "25 members, each with a source and a value class";
the doc's §9 asserts "recipe values that are UNKNOWN: 0".

**Test.** Tally the recipe's classes against this session's checks:

| class in §7a | members | independent verdict |
|---|---|---|
| decoded (donor `lights[2]`) | 13 shape members + `part`/`part_index` | all reproduce exactly |
| derived (hash) | `behavior_hash`, `part_hash`, `deformable_transform_hash` | all three recompute; 3,217/3,217 x3 shipped values also recompute |
| derived (colour) | `diffuse.R/G/B` | arithmetic exact, convention unstated (§14) |
| decoded | `preset_id 0` | 17 precedents; and 0 is no name hash (§5) |
| **decoded (mapped)** | `deformable_transform` | **fabricated** — its own source says `needs-lig-bone` (§13) |
| decoded | `part`, `part_index 26` | correct (`sportsmuscle_wheel_f_l`, `Land_Wheel`) |

**Result.** Every *number* is sourced; one *class* is wrong, and it is the one member the whole
recipe's feasibility hinges on (without a `_LIG` node the light has no anchor). The Done criterion
("a recipe for one custom light with every member value sourced") is met on paper; the recipe is not
yet buildable, and the card says so in §6/§7b — the §7a table should agree.

**Verdict: WEAK** (meets the letter; the one mislabel is load-bearing).

---

## What survives, and what should change

**Survives, reproduced to the value:** 223 vehicles / 224 modules / 3,217 entries / 25 members;
the nine behaviour counts (modulo the MODLOG's 1,156); 393 presets, 17 zeros, 34 inconsistent
(robust to the signature); 3,972 / 233 / 412 `.epe` objects, 404 names, 13 members, no part binding;
2,073 lit parts, 1,323 `Land_Light`, 11,643 parts; 3 index misses and 27 name mismatches; donor 42
parts / 12 lit / 10 `Land_Light`; the triple-lamp tail part; part 26 unlit with `CarPaintMM` only
(99 meshes, 0 `CarLight`); 11,367 `CarLight` blocks, 11,367 meshes, 220 vehicles, stride 12, uint16,
6 slots; the 1085/16/(12,24,2) layout as cited; the donor `lights[2]` shape copy; all three recipe
hashes; 588 light paths and no preset table in the index.

**Does not survive:**
1. **"no file joins the two light lists"** — 381 of 404 `.epe` preset names are the Jenkins hash of a
   module `preset_id` (`Dash_Light` = 2763198432, 170 entries). The join is in the project's own
   hash function, and it already answers the recipe's "is there a wheel-arch preset" question (§3);
2. **the binding census's "6 on unlit parts"** — 32 entries resolve to `has_lights = 0` parts; 26 of
   them are hidden behind the name-mismatch `continue`; the "13" is 9 in-cache + 4 on an entity with
   no light module, which the doc does not say (§6);
3. **"every vanilla light part has `has_lights` set"** — 32 shipped lamps sit on clear-flagged parts
   (§7);
4. **"spotlight"** — `light_type 0` is a point lamp (2,494/2,494 entries pair type 0 with the default
   angle 10; only type 1 has cones); the BmAK component's cone, radius and brightness are 0, so the
   word comes from the UDK class name (§12);
5. **the anchor's "decoded (mapped)"** — its own source records `needs-lig-bone`, and the bone name
   exists only in the BmAK data (§13).

**What the next card (T-18) should do with this.** Use the hash join: name every preset in the
translation, and take `Dash_Light` (2763198432) rather than 0 if a preset is wanted, or keep 0 and
say it is "no name" rather than "unknown". Decide LGT-2's cone explicitly — `light_type 1` with an
angle from the 723 cone entries — or drop the word "spotlight". Re-label the anchor as derived /
UNKNOWN, which is what makes the §112 probe the gate it is described as. None of this changes the
card's design conclusion (a new light part is needed; the wheel part cannot host it); it changes
three sentences and one class label.

**Reproduce.**

```
python Tools/scripts/jc3lights.py --check
# census: lights[i].* over E:/Modding/JustCause3/_grab/entities/*.ee.json
# .epe side: epe.objects where class == SVehicleLight in E:/Modding/JustCause3/_grab/detail/*.ee.json
# join: rbmhdr.hash_jenkins(name) vs lights[i].preset_id
# binding: PARTS_TABLE.jsonl rows keyed by entity basename
# CarLight: GEOMETRY.jsonl blocks where type == "CarLight"
# recipe: Research/BatmobileGrab/LIGHTS.json vehicles[0].entries (socket LWheelLight)
```
