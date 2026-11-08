# Armour plates and deformation — BmAK stages vs JC3 per-part damage

**Status: research note, DONE for the files that exist.** Everything below is read from the project's
own decoded records; nothing is taken from memory of either game (AGENTS.md). Every number carries its
source file. Where a value exists but its *meaning* is not proven, it says **UNKNOWN** instead of
inventing a stage rule.

Sources used (all local, none edited):

| topic | file |
|---|---|
| BmAK damage entries, health, armour mode | `Research/BatmobileGrab/DAMAGE_RULES.md` (§2, §3.1, §3.6, §4) |
| BmAK class defaults (numbers) | `Research/BatmobileGrab/CLASS_DEFAULTS.md` (rows 64, 68–73, 143) |
| BmAK material slots / masks | `Research/BatmobileGrab/SLOTS.md` (19 slots, LOD0 faces) |
| BmAK material→texture bindings | `Research/BatmobileGrab/TEXTURES.md` (`*_Damage_ChapterMask` rows) |
| BmAK meshes | `Research/BatmobileGrab/MESHES.json` (4 packages × 3 meshes) |
| JC3 part table | `Research/JC3Grab/PARTS_TABLE.jsonl` (donor `sportsmuscle_civilian_01`, 42 parts) |
| JC3 part damage thresholds | `Research/JC3Grab/DAMAGE_MODEL.json` → `vehicles.donor.part_damage_types` (24 rows) |
| JC3 damage chain | `Research/JC3Grab/DAMAGE_MODEL.md` step 5, §2 |
| JC3 deform / mshswap | `Research/JC3Grab/PARTS.md` §3–5, `Research/JC3Grab/DECODE_DEPTH.md` |

---

## 1. What BmAK actually has: five armour levels, one mesh, four damage masks

### 1.1 The ladder (measured, one interpretation flagged)

`RVehicleBatmobileBase.ArmourLevels` is an `ArrayProperty`, **count = 5, int [0, 300, 600, 900, 1200]**
(`CLASS_DEFAULTS.md` row 143, off `BmGame\RVehicleBatmobileBase.g.cs:8755`). `Pawn.Health` is **1200**
on all three Batmobile archetypes (`DAMAGE_RULES.md` §4). The top rung equals max health, and the five
values are monotonic, which is why they are laid out below as stages S0…S4.

**Measured:** the array is 5 entries with those values; health is 1200.
**Inferred (not proven):** that the entries are *health thresholds* and that S0=0 … S4=1200 in that
order. Whether the array is a threshold ladder or an armour *pool* per level is **UNKNOWN** — no file
states it, and `SetDamageLevel` is **native** (48-byte export, empty body, 2 param descriptors,
`DAMAGE_RULES.md` §2), so the reader is in `BatmanAK.exe`, not in script.

| stage | ladder value | state named in this plan | evidence class |
|---|---:|---|---|
| S0 | 0 | pristine | array value measured; stage meaning inferred |
| S1 | 300 | first impact damage | ″ |
| S2 | 600 | heavy panel damage | ″ |
| S3 | 900 | critical | ″ |
| S4 | 1200 | wreck | ″ |

### 1.2 Armour mode is not a panel

`ArmouredMode` is a *BoolProperty* used as a collision-selector guard
(`COLLISION_SELECTOR3.md`), and it changes the collision box, not a plate mesh:

| mode | width | length | height | source |
|---|---:|---:|---:|---|
| `PursuitMode*` | 220.0 | 430.0 | 250.0 | `CLASS_DEFAULTS.md` rows 71–73 |
| `BattleMode*` | 265.0 | 430.0 | 250.0 | `CLASS_DEFAULTS.md` rows 68–70 |

So battle mode widens the car by **45 cm** (220→265) and nothing else. **No armour-plate mesh swap was
found for armoured mode**, and `ArmourModeDamageReduction` only scales incoming damage (§1.3).

### 1.3 The armour-damage number — two sources disagree, both are recorded

| source | `ArmourModeDamageReduction` |
|---|---:|
| class default (`CLASS_DEFAULTS.md` row 64, `IntProperty`, off 6424) | **20** |
| shipped archetype override (`DAMAGE_RULES.md` §3.1, from `CHAIN.json`) | **0** |

`TakeDamage` is the **only** reader in the package (1 script function). Which number the running game
uses is a CDO-vs-tag question, not resolved here — flagging it rather than picking one. It does not
affect panels: it multiplies incoming damage only.

### 1.4 What deforms: four mask-driven material groups on one mesh

The Batmobile is **one** mesh, `Batmobile_V2`, with **19 material slots** and **299,837 LOD0 faces**
(`SLOTS.md`). There is no per-panel mesh. Damage is painted through `Damage_Chapter_Mask` textures
bound into four slots, and each slot also carries its own damage normal map:

| BmAK panel group | slot | material | LOD0 faces | mask texture (`TEXTURES.md`) | normal |
|---|---:|---|---:|---|---|
| Main body | 2 | `Batmobile_V3_Mainbody_NEW_MIC` | 37,819 | `Batmobile_V3_TEXTURES_Body_Damage_ChapterMask` (4096², DXT1) | `Batmobile_V3_Body_N` |
| Wheel arches | 3 | `Batmobile_V3_WheelArchs_NEW_MIC` | 42,999 | `Batmobile_V3_TEXTURES_WheelArch_Damage_ChapterMask` (4096²) | `Batmobile_V3_WheelArch_N` |
| Undercarriage | 4 | `Batmobile_V3_Undercarriage_NEW_MIC` | 26,150 | `Batmobile_V3_Undercarriage_Damage_ChapterMask` (4096²) | `Batmobile_V3_Undercarriage_N` |
| Turret / weaponry | 7 | `Batmobile_V3_Turret_NEW_MIC` | 47,912 | `Batmobile_V3_TEXTURES_Weaponry_Damage_ChapterMask` (4096²) | `Batmobile_V3_Weaponry_Turret_V2_N` |

Plus the shared dent normal `Batmobile_Damagepattern_N` (2048×1024, `TEXTURES.md`).

Two overlay meshes exist per package (`MESHES.json`):

| mesh | vertices | faces | bones | role |
|---|---:|---:|---:|---|
| `Batmobile_V2_Fire` | — | — | — | fire/damage overlay on the car |
| `Batmobile_V3_Destroyed` | 57,101 | 36,513 | 32 | whole wreck, separate mesh |

**Which stage triggers the fire overlay or the wreck swap is UNKNOWN.** `MESHES.json` proves the meshes
ship; the traced scripts do not name them and `SetDamageLevel` is native.

**What deforms, precisely:** the *shading* deforms (mask + normal map grow dents/scratches across the
four groups). Whether vertices are displaced is **UNKNOWN** — no vertex-deform data or morph target was
found in the decoded BmAK assets. So for our rebuild: BmAK's "panel damage" is a texture-mask look, not
plate geometry.

### 1.5 BmAK stage → panel table (the honest version)

Only the four rows below are supported. No file maps S0…S4 to an individual mask amount, so the
"visible at" column is the **inferred** reading of a 5-rung ladder, marked as such.

| panel group | mask | S0 | S1 | S2 | S3 | S4 | evidence |
|---|---|---|---|---|---|---|---|
| Main body | Body chapter mask | clean | light | medium | heavy | wreck mesh candidate | mask exists (measured); per-stage amount inferred |
| Wheel arches | WheelArch chapter mask | clean | light | medium | heavy | wreck | ″ |
| Undercarriage | Undercarriage chapter mask | clean | light | medium | heavy | wreck | ″ |
| Turret / weaponry | Weaponry chapter mask | clean | light | medium | heavy | wreck | ″ |
| Glass, wheels, cockpit (slots 1, 0/9/13, 10/11) | none | unchanged | unchanged | unchanged | unchanged | unchanged | `SLOTS.md`: those slots bind no damage mask |

---

## 2. What JC3 offers: per-part health, vertex deform, and `mshswap` alternates

JC3 has no whole-car stage ladder. It has **42 parts**, each with its own damage type and health
thresholds, and it deforms by moving `DeformPoints`.

### 2.1 The per-part numbers we can use (donor, `DAMAGE_MODEL.json`)

| damage type | initial_health | damaged_health | loosen_health | instantly_damaged_by_bullets | damages_owning_vehicle |
|---|---:|---:|---:|---:|---:|
| `Land_Body` | 1000 | 0 | 0 | 0 | 1 |
| `Land_Fender` | 200 | 0 | 50 | 0 | 1 |
| `Land_Undercarriage` | 800 | 0 | 0 | 0 | 1 |
| `Land_Door` | 300 | 50 | 200 | 0 | 1 |
| `Land_Hood` | 350 | 0 | 100 | 0 | 1 |
| `Land_Trunk` | 350 | 0 | 100 | 0 | 1 |
| `Land_Bumper` | 200 | 30 | 50 | 0 | 1 |
| `Land_Grill` | 200 | 0 | 50 | 0 | 1 |
| `Land_Generic` | 200 | 0 | 50 | 0 | 1 |
| `Land_Engine` | 900 | 100 | 150 | 0 | 1 |
| `Land_Wheel` | 1020 | 400 | 100 | **1** | 1 |
| `Land_Light` | 50 | 30 | 20 | **1** | 0 |
| `Land_Window` | 50 | 30 | 20 | 0 | 0 |
| `Land_Stunt_Window` | 700 | 0 | 0 | 0 | 0 |

Semantics of `initial/damaged/loosen_health` are **UNKNOWN** (`DAMAGE_MODEL.md` step 5) — the numbers
are decoded, the rule that consumes them is not in any file. Use them as a 3-threshold per-part budget,
not as proven hit points.

### 2.2 Two deformation mechanisms, one mesh-swap mechanism

| mechanism | evidence | usable by health? |
|---|---|---|
| **Vertex deform** | donor parts carry `deform = 1`; 42/42 part names match `DeformPoints`, 12/12 light indices, 4/4 wheel indices (`PARTS.md` §3); `VehicleDamage.deform_scale` = 1 on the donor (`DAMAGE_MODEL.md` §2) | yes — deform points are per part and `deform_scale` is a vehicle tunable; exact health→deform curve is **UNKNOWN** |
| **Part states** (initial → damaged → loosen → broken) + detach | 24 `part_damage_types` rows with the three thresholds and the three `instantly_*` flags; `Land_Wheel` and `Land_Light` are `instantly_damaged_by_bullets = 1` | yes, this is the health hook |
| **Mesh swap** (`mshswap`) | alternate LOD sets ship per part: `sportsmuscle_headlight_f_l_01mshswap`, `..._02mshswap`, `..._headlight_f_r_01/02mshswap`, `..._signal_r_l/r_rmshswap`, `..._taillight_r_l/r_rmshswap`, `..._wheel_f_l/f_r/r_l/r_rmshswap` (`DECODE_DEPTH.md`) | **UNKNOWN** — the alternates exist, but nothing decoded states what selects them (health, light state, or variant). Do not assume "broken lens". |
| **Hide a mesh** | a `.lod` slot can be the literal `-`; 16 of 59 `.lod` files use it (the `mshswap` parts, seats, engine) — `DECODE_DEPTH.md` §`.lod` | **static**, not health-driven. There is no decoded health→hide rule. |

So the question "which JC3 parts can swap or hide meshes by health" has an exact answer: **none is
proven**. The candidates that *can carry an alternate mesh* are the 4 wheels, 4 headlight halves
(01/02 pairs), 2 rear signals, 2 taillights — and the route that *is* proven to respond to health is
part-state change + detach + deform.

---

## 3. Panel-by-panel mapping

Donor indices are from `PARTS_TABLE.jsonl` (`v0300_car_kensington_sportsmuscle_civilian_01`, entity
`.../v0300_car_kensington_sportsmuscle_civilian_01.ee`). Health values from §2.1.

| BmAK panel group | JC3 part(s) we bind | idx | damage type | deform | initial / damaged / loosen | swap route |
|---|---|---:|---|---|---:|---|
| Main body (slot 2) | `sportsmuscle_body` | 0 | `Land_Body` | 1 | 1000 / 0 / 0 | none; deform only |
| Main body — doors | `sportsmuscle_door_f_l`, `_f_r` | 1, 2 | `Land_Door` | 1 | 300 / 50 / 200 | detach via `doors[]` |
| Main body — hood | `sportsmuscle_hood`, `_hood_signature` | 24, 25 | `Land_Generic` / `Land_Hood` | 1 | 200/0/50 · 350/0/100 | none |
| Main body — trunk | `sportsmuscle_trunk` | 10 | `Land_Trunk` | 1 | 350 / 0 / 100 | none |
| Main body — bumpers | `sportsmuscle_front_bumper`, `_rear_bumper` | 22, 6 | `Land_Bumper` | 1 | 200 / 30 / 50 | none |
| Main body — glass | `sportsmuscle_window_f`, `_window_r_l`, `_window_r_r`, `_door_f_l_window`, `_door_f_r_window`, `_trunk_window` | 13–16, 18, 32 | `Land_Stunt_Window` / `Land_Window` | 1 | 700/0/0 · 50/30/20 | none |
| Wheel arches (slot 3) | `sportsmuscle_fender_l`, `_fender_r` | 20, 21 | `Land_Fender` | 1 | 200 / 0 / 50 | none; deform only |
| Undercarriage (slot 4) | **no donor part** | — | `Land_Undercarriage` exists in the table (800 / 0 / 0) but **no part in this car carries it** | — | — | must add a part or fall back to `Land_Body` |
| Turret / weaponry (slot 7) | **no turret on donor**; nearest `sportsmuscle_missile_base_signature` | 41 | `Land_Generic` | 0 | 200 / 0 / 50 | optional, non-deforming |
| Wheels (no BmAK mask) | `sportsmuscle_wheel_f_l/f_r/r_l/r_r` | 26, 27, 11, 12 | `Land_Wheel` | 0 | 1020 / 400 / 100, instantly damaged | `*_wheel_*mshswap` alternate exists; selection UNKNOWN |
| Lights (no BmAK mask) | `headlight_f_l_01/02`, `headlight_f_r_01/02`, `taillight_r_l/r_r`, `signal_f_l/f_r`, `signal_r_l/r_r` | 34, 35, 37, 38, 8, 9, 36, 39, 29, 30 | `Land_Light` | 0 | 50 / 30 / 20, instantly damaged | 01/02 pairs + `mshswap` alternates; selection UNKNOWN |

Facts that constrain the mapping:

* The donor has **no `Land_Undercarriage` part** and **no turret part** — BmAK's undercarriage and
  weaponry masks have no 1:1 JC3 receiver on this car. Any claim otherwise would be invented.
* `sportsmuscle_c_mirror` (idx 33) carries `Boat_Antenna`, a type absent from the vehicle's own table,
  so it falls back to `Default` (50 / 30 / 20) — a shipped-file inconsistency recorded in `PARTS.md` §3.
* The BmAK body mask covers the whole body shell; on JC3 that shell is split into body + doors + hood +
  trunk + bumpers + fenders. So BmAK's S1…S3 body dents map onto **several** JC3 parts, not one.

---

## 4. What we reuse, and the values we set

| BmAK behaviour | reuse | value to set |
|---|---|---|
| 5-stage ladder 0/300/600/900/1200, max health 1200 | **yes, as our damage budget** | `VehicleDamage.max_health` = 1200 on the Batmobile donor profile (donor ships 700; the tank 2000) — measured BmAK number |
| body shell dents | **yes** | part 0 `Land_Body` `deform = 1`, `deform_scale` = 1 (donor value) |
| wheel-arch / undercarriage / turret masks | **partly** — arches via `Land_Fender` (200/0/50); undercarriage needs a new part; turret not on this car | do not set a `Land_Undercarriage` threshold on a car that has no such part |
| armour mode = wider collision box only | **yes** | chase 220×430×250, battle 265×430×250 (`CLASS_DEFAULTS.md`) |
| incoming-damage reduction in armoured mode | **hold** — the two files disagree (20 vs 0) | leave at 0 until a probe settles which one ships |
| wreck mesh at the last stage | **later** | `Batmobile_V3_Destroyed` is a separate mesh; the trigger is UNKNOWN, so no value is set here |

**Values we need but do not have (do not guess):** the per-stage mask amounts, the health at which the
fire overlay appears, the health at which the wreck mesh appears, the `mshswap` selector, and the
health→deform curve. Each is one 5-minute experiment (set a value, observe) rather than a speculative
implementation (AGENTS.md).

## 5. Conflicts / corrections this note records

1. `ArmourModeDamageReduction`: class default **20** (`CLASS_DEFAULTS.md`) vs archetype **0**
   (`DAMAGE_RULES.md` / `CHAIN.json`). Both recorded; not resolved.
2. `DAMAGE_RULES.md` §3.1 says the shipped archetype value is 0 "so armoured mode reduces damage by
   nothing as shipped"; the class default row shows 20. The sentence about *script readers* is correct
   (1 reader); the *effective* value is the open question.
3. BmAK's "armour" is a texture-mask look plus a collision-box mode, **not** plate geometry. Nothing in
   the decoded assets shows armour plates being added or removed per stage.

## 6. Checks run for this note

* `Research/JC3Grab/PARTS_TABLE.jsonl` donor row re-read: 42 parts, indices 0–41, `deform` flags as
  tabulated above.
* `Research/JC3Grab/DAMAGE_MODEL.json` donor `part_damage_types`: 24 rows, values copied verbatim.
* `CLASS_DEFAULTS.md` rows 64, 68–73, 143 and `SLOTS.md` 19 slots re-read for the numbers quoted.
* `MESHES.json`: 4 packages × 3 meshes (`Batmobile_V2`, `Batmobile_V2_Fire`, `Batmobile_V3_Destroyed`),
  `Batmobile_V3_Destroyed` 57,101 verts / 36,513 faces / 32 bones.
* No game process started; no file outside `Research/` and `tmp/freebuff/reports/` written.
