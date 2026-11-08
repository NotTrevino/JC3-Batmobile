# Keep-row audit: damage and collision

**Rows audited:** T-DM3, T-DM4, T-DM5, T-DM6, T-DM8 (T-2b / T-3), T-CO1, T-CO3 (T-2b), T-P2 (T-1).
**Question:** for each row marked `keep`, what does BmAK actually do, what does the build actually
carry, and is the result **LORE-EXACT** or a **COMPROMISE**?
**Answer in one line:** one row is lore-exact in behaviour (T-DM8, ramming); the other seven are
compromises — donor values, fleet maxima, or declared switches — and three of the eight rows
(T-DM5, T-CO1, T-P2) also carry a **stale or wrong BmAK number** in their own text.

This is a read-only audit. No ledger row, module, `.physicsc`, receipt or build was changed.
Revert = delete this file. Evidence is cited per claim; where the record has no evidence the cell
says **UNKNOWN** rather than a plausible value (AGENTS.md).

---

## 0. Verdict map

| row | member / feature | BmAK behaviour (evidence) | carried behaviour (measured) | verdict |
|---|---|---|---|---|
| **T-DM3** | `bullet_heavy_armor` 5 @ 20 | no per-channel armour at all; one `TakeDamage` path, weapon-generator shield, `ArmourModeDamageReduction` 0 | 5 @ 20, a channel **no decoded JC3 weapon writes to** | **COMPROMISE** |
| **T-DM4** | `explosion_threshold` / `npc_explosion_threshold` / `smoke_threshold` / `burn_threshold` | no threshold fields decoded; destruction is health + generator + radial falloff | 4000 / 4000 / 1050 / 250 — all at the fleet maximum | **COMPROMISE** |
| **T-DM5** | 24 `part_damage_types` + part join | no per-part health table; 32 **collision** bodies on the wreck, `RVisualDamageComponent` values undecoded | donor's 24 `Land_*` rows, 17 types over 42 parts (19 over 59 in RC2) | **COMPROMISE** |
| **T-DM6** | `deform_scale` 0 | no deform value decoded; damage-state assets exist, panel deformation not established | 0 (outside shipped 1..2), declared switch | **COMPROMISE** |
| **T-DM8** | `impact_damage_factor` 0 | `TakesDamageFromRam` returns **true** — the class does not encode immunity; the bar not moving is a play observation | 0 (outside shipped 1..12) + `impact_armor` 5000, declared switch | **LORE-EXACT (behaviour)** |
| **T-CO1** | collision shapes | drivable asset = **3 boxes + 56 convex elements**; the 32-box set is the **destroyed wreck** | donor hulls: bm-009 untouched donor (54 hulls); bm-RC2 donor hulls re-cut to the body mesh | **COMPROMISE** |
| **T-CO3** | `has_world_collision_shape` | no per-part flag exists; drivable collision is two whole-car meshes + 3 boxes | donor flags 38/42 = 1, 4 wheels 0 with body −1 | **COMPROMISE** |
| **T-P2** | 42 damage parts (health, type) | no per-part damage values decoded; 32 wreck bodies are geometry only | 24 types joined to 42 parts (bm-009) / 61 parts (bm-RC2) | **COMPROMISE** |

"LORE-EXACT" is used only where the **carried behaviour** reproduces what the record says a player
sees. It is not a claim that the carrier is the same mechanism, and it is not in-game verified:
`STATUS.md` reports **0 / 185 rows behaviour-verified**.

---

## 1. What BmAK actually carries

The prompt's shorthand ("RVisualDamageComponent, the destroyed physics asset with 32 boxes, health
model") maps onto **three separate objects**, and only one of them has decoded numbers.

### 1.1 `RVisualDamageComponent` — present, values UNKNOWN

| fact | value | source |
|---|---|---|
| instances in the four Batmobile packages | 4 | `Research/BatmobileGrab/REMAINDER.md:60` |
| drivable car's instance | `Playable_Batmobile_SF.VisDmgComp`, export 5283, **6 B** | `REMAINDER.md:990,1102` |
| reachability | reached from `Vehicle.Batmobile` at depth 0 | `REMAINDER.md:1102` |
| decodable values | **none** — the tag list terminates at byte 2; no start offset 0..19 yields a 2+ tag stream that reaches the payload end | `REMAINDER.md:1102`; `REMAINDER_SAMPLE_AUDIT.md:72` (`native_record x4`, no `tag_count == 0`) |

So BmAK has a visual-damage component on the drivable car, but **no parameter of it is decoded**.
Any row that claims a BmAK visual-damage value is claiming something the record does not contain.

### 1.2 The destroyed physics asset — 32 bodies, geometry only, wreck-only

`Research/BatmobileGrab/PHYSICS.md` decodes `Batmobile_V3_Destroyed_Physics`: **32 bodies per
vehicle, 128 records, all four vehicles byte-identical**. Every body is **one box** (box count 1,
sphere count 0), extents and local centre in cm.

| category | bodies |
|---|---:|
| wheel/suspension | 8 |
| destruction debris (`Object*_frag_*`) | 18 |
| door | 2 |
| cockpit | 1 |
| turret | 1 |
| jet fin | 1 |
| root placeholder | 1 |

The doc's own verdict: **"There is no chassis body."** The main hull has no `RB_BodySetup`; this
asset is what the game hands to the **destroyed** car. Largest box: `SUSP1_Wheel_Rear_Right_Mesh`
317.942 × 64.552 × 97.966 cm.

**These are collision bodies, not damage bodies.** No health, damage type, threshold or break
value is decoded on any of the 32. Calling them "32 per-bone damage bodies" (as the row text and
the brief do) is not supported by the record; the only per-bone damage carrier is the undecoded
`RVisualDamageComponent`.

### 1.3 The drivable collision asset — 3 boxes + 56 convex elements

`Research/BatmobileGrab/COLLISION_GEOM.md` decodes `Physics.Batmobile_V3_Physics` (export 158266),
body setups 169750 / 169751:

| body | box | extents (cm) | centre (cm) |
|---|---|---|---:|
| `Batmobile_Chassis` | 0 | 690.305 × 374.536 × 207.5 | (9.0, 0.0, 106.75) |
| `Batmobile_Chassis` | 1 | 679.585 × 345.688 × 103.5 | (0.0, 0.0, 79.0) |
| `Batmobile_Rig_Weapons_Trans` | 0 | 166.177 × 189.365 × 39.8 | (−30.5, −0.0, 93.25) |

Plus two `RB_BodySetup` collision meshes: `Batmobile_V2 battle` (43 convex elements) and
`Batmobile_V2_Collision_Pursuite` (13) = **56 convex element boxes** (`COLLISION_CONVEX.md`).
**Which mesh is live per mode is UNKNOWN** — `BatmanVsBatmobileCollisionMode` is not serialised
(`COLLISION_GEOM.md`, Verdicts). Box rotations are also not decoded.

### 1.4 The health model — 1200 HP, a generator shield, no channels

`Research/BatmobileGrab/DAMAGE_RULES.md` (G1-14):

| fact | value | source |
|---|---|---|
| `Pawn.Health` | **1200** on all 3 Batmobile archetypes | §4 |
| direct hit path | `TakeDamage` (script, 2,028 B) | §3.1 |
| armour-mode reduction | `ArmourModeDamageReduction` = **0** as shipped | §3.1, §6.3 |
| the shield | `DrainWeaponGeneratorForDamage` — the weapon generator absorbs hits | §4 |
| incoming ram | `TakesDamageFromRam` (script, 7 B) begins **`return true`**; the 4-byte tail is UNKNOWN | §3.4 |
| outgoing ram | `CalculateAndStoreImpactDamage` reads only outgoing multipliers (`Impact*`, `BattleModeImpact*`, strafe/boost/civilian mods) | §3.3 |
| encounter scaling | `GetDamageMod` is **native** | §7 |
| heavy cannon | primary projectile `Damage` **50** → 1200 / 50 = **24 hits** | §3.5; `T10_DAMAGE.md` |

There is **no per-channel armour** (bullet/explosion/impact/…), **no per-part health table**, and
**no threshold field** in this model. Those are JC3 concepts; BmAK's equivalents are the generator
shield, the single 1200 pool, and the native encounter modifier.

---

## 2. What the builds actually carry (measured, not quoted)

### 2.1 bm-009 — the damage build

`Builds/bm-009/receipt.json` + `Working/Damage/bm_health.json`:

| item | value |
|---|---|
| private module | `…/v0300_car_kensington_sportsmuscle/batmobile_health_medium.vmodc`, 3,741 B, sha256 `D325308B…` |
| shared module | `lave_health_medium.vmodc` left byte-identical (R7) |
| `.epe` `damage` hash | 670,155,287 → 1,928,726,201 (private path) |
| `max_health` | 2000 → **36000** (declared switch, scoped `"build": "bm-009"`) |
| `bullet_armor` @ strength | 5000 @ 99 |
| `bullet_heavy_armor` @ strength | **5 @ 20** |
| `explosion_armor` @ strength | 250 @ 50 |
| `impact_armor` @ strength | 5000 @ 100 |
| `melee_armor` @ strength | 5000 @ 100 |
| `fire_armor` @ strength | 0 @ 0 |
| `electricity` / `grapple_pull` | −1 @ 100 |
| `impact_damage_factor` | **0** |
| `deform_scale` | **0** |
| thresholds | explosion 4000, npc_explosion 4000, smoke 1050, burn 250 |
| part table | donor's 24 `Land_*` rows, **no edit** |
| collision | donor `sportsmuscle.physicsc`, **340,368 B**, sha256 `1b90daef…` — the untouched 54-hull donor set |

`damage_audit.py --build Builds/bm-009/aaf` → **exit 0**, `29 members, 6 outside the shipped range,
6 declared switches`, `check ok` (re-run for this audit).

### 2.2 bm-RC2 — the release candidate

`Builds/bm-RC2/receipt.json` + files on disk:

| item | value |
|---|---|
| health module | same private `batmobile_health_medium.vmodc`, sha256 `d325308b…` (identical to bm-009) |
| shared health module | reverted to vanilla, sha256 `6f9c8fab…` |
| collision | `…/batmobile/sportsmuscle.physicsc`, **902,384 B**, sha256 `eda17906…` |
| collision provenance | B-10 copied `Working/Collision/batmobile.physicsc` (`192c1247…`); B-10b re-boxed 1 compound + refit 3 dynamic trees to `sportsmuscle_body_lod2.rbm`; B-10c re-encoded **54 donor hulls** (95 vertices, 186 faces, `max_cut_m` 0.0, `convex_radius` 0.016763), bounds `[-1.745, 0.075, -3.428] … [1.754, 2.358, 3.609]` |
| parts | **61** after B-04R (2 doors deleted, 4 orphans re-parented, 19 new parts from B-04) |
| damage audit | **exit 1** — see §4.1 |

So RC2 carries the **same damage values as bm-009** and a **donor-topology hull set re-cut to the
Batmobile body mesh**. It does not carry BmAK's 3 drivable boxes, its 56 convex elements, or its
32 wreck bodies.

---

## 3. Row by row

### T-DM3 — `bullet_heavy_armor` 5 @ 20 — **COMPROMISE**

**BmAK.** There is no heavy/light armour split. A hit enters `TakeDamage`, is reduced by
`ArmourModeDamageReduction` (0), scaled by native `GetDamageMod`, and drained from the weapon
generator (`DAMAGE_RULES.md` §3.1, §4). The only "heavy" distinction in the data is projectile
damage: heavy cannon body shot 75, primary 50, missile 250 (`DAMAGE_RULES.md` §3.5).

**Carried.** 5 @ 20, inherited from the medium tank's profile (`DAMAGE_MODEL.md` §2). The channel
is **unused**: no decoded JC3 weapon component maps to `bullet_heavy` (`DAMAGE_MODEL.md` step 3,
§7; `T10_DAMAGE.md` §7). The row is therefore a value in a channel nothing writes to.

**Player-visible match.** Not established. Whether a given AK weapon would land in JC3's `bullet`
or `bullet_heavy` is UNKNOWN, so the row cannot be said to reproduce AK's small-arms behaviour.

**Closest JC3 system + gap (STAGES.md).** Closest = `VehicleDamage`'s eight channels. Gap = the
weapon→channel map. Build action: keep the value, but do not count it as translation until a
`bullet_heavy` carrier is decoded; if none exists, the row is a donor carry and should say so.

### T-DM4 — thresholds — **COMPROMISE**

**BmAK.** No `explosion_threshold` / `smoke_threshold` / `burn_threshold` equivalent is decoded.
Destruction is the 1200 pool plus the generator shield; radial damage has a distance falloff
(0.0 / 0.1 / 0.5 / 1.0 / 1500.0) and a native `ShouldRadialDamageHit` gate (`DAMAGE_RULES.md`
§3.2). What makes the car burn or explode, and when, is **UNKNOWN** from the files.

**Carried.** explosion 4000, npc_explosion 4000, smoke 1050, burn 250 — every one at the top of its
shipped domain (`damage_audit.py` output; `T10_DAMAGE.md` §5). This is "fleet maximum", not a BmAK
number.

**Bookkeeping defect.** `T_ROWS.jsonl` names the triple `explosion_threshold / smoke_threshold /
burn_threshold` = 4000 / 1050 / 250, while `T10_DAMAGE.md` names `explosion_threshold /
npc_explosion_threshold / smoke_threshold` = 4000 / 4000 / 1050. The module carries **all four** at
maximum. The row and the card describe different triples; neither is wrong about the values, but
the row is not a complete statement of what is carried.

**Player-visible match.** Unproven. The thresholds are per-hit damage gates whose semantics are
UNKNOWN even on the JC3 side (`DAMAGE_MODEL.md` step 7).

**Closest JC3 system + gap.** Closest = `VehicleDamage` thresholds. Gap = BmAK's burn/explosion
timing. Build action: leave the values; the gap closes only with a BmAK timer/effect decode or a
Q-1 observation, not with a different number.

### T-DM5 — 24 part damage types + join — **COMPROMISE**

**BmAK.** No per-part health table exists in the record. The 32 bodies are collision geometry on
the **destroyed** asset (§1.2); `RVisualDamageComponent` is 6 bytes with no decodable values
(§1.1). BmAK does ship damage-state assets — `Batmobile_V3_Destroyed` (57,101 verts),
`Damage_Chapter_Mask` textures, a `Damage_States` package (`Research/challenge/card-G1X.md` §6(c),
citing `MESHES.md`, `SLOTS.md`, `ASSETS.md`) — but those are **states and masks**, not a
part→health table.

**Carried.** The donor's 24 `Land_*` rows (`Land_Body` 1000, `Land_Wheel` 1020, `Land_Engine` 900,
`Land_Window` 50, `Land_Light` 50, `Land_Grill` 200, …), joined to the parts module. 17 distinct
types over the donor's 42 parts; `c_mirror` uses `Boat_Antenna`, which has no row in this vehicle's
land table and falls back to `Default` (`T_ROWS.jsonl`; `MODLOG.md:5143-5144,6291-6292`).

**Wording defect.** The row says `Boat_Antenna` "is not in the table". The challenge review
(`Research/challenge/T2_TRANSLATION.md` C23) shows `Boat_Antenna` **is** a real type, declared by
all 35 boat entities; it is simply not in this vehicle's 24-row land table. The fallback is real;
the reason as written is wrong.

**Player-visible match.** Unproven. Per-part break order is the row's own UNKNOWN, and no BmAK
per-part HP exists to compare against.

**Closest JC3 system + gap.** Closest = `VehicleDamage.part_damage_types[]` + the part join. Gap =
BmAK per-part values and break order. Build action: keep the donor rows; the gap is a Q-1 crash
test, not a value edit.

### T-DM6 — `deform_scale` 0 — **COMPROMISE**

**Provenance (fact, as requested).** The choice is a **project rule**, not a BmAK value:
`GRAB_BACKLOG.md:135` — APP-7 "The car never deforms; damage shows as scorch/smoke only | **user
rule R1; BmAK has no deform** | `deform_scale` 0 (switch)". `MODLOG.md:7382` records `T-DM6` →
`keep` as a "declared cosmetic switch". `damage_switches.json` declares it: "cosmetic switch: no
panel crumple on the Batmobile. Shipped range is 1..2".

**Does it match what a player sees in Arkham Knight?** **Not established.** The stated BmAK
justification ("BmAK has no deform") is contested by the project's own challenge review:
`Research/challenge/card-G1X.md` §6(c) calls it "an unsupported claim sitting next to shipped
destroyed-mesh evidence", and notes that "deform" and "damage states" are not the same thing. The
record proves AK ships a destroyed mesh, damage masks and a `Damage_States` package; it does **not**
prove whether panels visibly deform under fire. So the honest answer is **UNKNOWN**, and the
choice stands on R1 (do not conform to JC3 mechanics), not on a decoded AK behaviour.

**Carried.** 0, outside the shipped 1..2, declared. `damage_audit.py` reports it as a switch in
both builds.

**Closest JC3 system + gap.** Closest = `deform_scale` itself (a real module switch). Gap = none in
the carrier; the gap is **evidence**: a BmAK damage-state/deform decode or a frame-by-frame
observation. Build action: keep 0 under R1; if the operator wants AK's damage-state look, the
carrier is the damage-state material/mask path, not `deform_scale`.

### T-DM8 — `impact_damage_factor` 0 — **LORE-EXACT (behaviour)**

**Provenance (fact).** The row was created after test-087: `MODLOG.md:7382` — "new `T-DM8`
(behaviour: ramming does not move the health bar; JC3 mechanism = `impact_damage_factor` 0, a
declared switch, keep)". `GRAB_BACKLOG.md:153` — ARM-3 "Ramming anything never damages the
Batmobile". The value 0 is hand-set and declared, not translated.

**BmAK.** `TakesDamageFromRam(Target, RamSpeed)` is a script function whose body begins
**`return true`** — the incoming-ram entry point exists and is **open**, not switched off
(`DAMAGE_RULES.md` §3.4). What keeps the bar still is therefore not this function; the candidates
are the weapon-generator shield and/or a native gate, and the 4-byte tail is UNKNOWN. BmAK does
**not** encode ram immunity as a value.

**Carried.** `impact_damage_factor` 0 (incoming collision damage multiplied off) plus
`impact_armor` 5000 @ 100 as a belt-and-braces cap that is inert while the factor is 0
(`damage_switches.json`). Both are outside the shipped ranges (1..12 and 0..5) and declared.

**Does it match what a player sees?** **Yes, at the level the record states.** The project's play
observation is that ramming does not move the health bar (ARM-3), and the build reproduces exactly
that observable: no collision damage, no crumple, no fire. This is why the row is the one
LORE-EXACT verdict here. The qualification: the mechanism is a JC3 off-switch, not BmAK's
generator shield, and the behaviour has not been re-verified in game (`STATUS.md`: 0 rows
behaviour-verified). The take is Q-3/A11 (ram a wall and cars at 40/80 km/h, bar delta 0).

**Closest JC3 system + gap.** Closest = `impact_damage_factor` (the only incoming-collision
multiplier). Gap = none behaviourally; mechanically the gap is that JC3 has no generator shield, so
the build cannot reproduce *how* AK survives a ram, only *that* it does.

### T-CO1 — collision shapes — **COMPROMISE**

**BmAK.** The row's BmAK cell says "32 boxes (bone, centre, extents)". That is the **destroyed
wreck** asset (§1.2), not the car the player drives. The drivable asset is **3 boxes + 56 convex
element boxes** (§1.3), and the active mesh per mode is UNKNOWN. The wreck's own doc says it has
**no chassis body**, so the drivable hull cannot be copied from it.

**Carried.** bm-009: the untouched donor `sportsmuscle.physicsc` (340,368 B, 54 hulls, 22
compounds, 112 instances, body as `hknpExternMeshShape`). bm-RC2: the same donor **topology**
re-encoded and cut to the Batmobile body mesh (902,384 B, 54 hulls, 95 vertices, 186 faces,
`max_cut_m` 0.0, bounds 3.499 × 2.283 × 7.037 m). That is a donor chassis fitted to the BmAK body,
not BmAK's collision.

**Player-visible match.** Approximate. The silhouette and world collision come from the body mesh,
so the car should not clip or float; but the hull set is the Serpente's, and the BmAK drivable
boxes are not represented.

**Closest JC3 system + gap.** Closest = `.physicsc` hulls (writer proven, G2-30). Gap = the hull
set itself: BmAK's 3 drivable boxes + 56 convex elements, and a chassis hull that BmAK does not
ship. Build action per `PHYSICS_WRITE.md` §7 / `STAGES.md`: author hulls from the body mesh (or map
the 3 drivable boxes into donor slots), then re-read through the `.toc`. The row's "32 boxes" text
must be corrected first — see §4.2.

### T-CO3 — `has_world_collision_shape` — **COMPROMISE**

**BmAK.** There is no per-part world-collision flag. The drivable car's collision is two whole-car
collision meshes (`BatmanCollisionMeshBattleMode0` / `PursuitMode0`, `objects.jsonl`) plus the 3
physics-asset boxes; the wreck has 8 wheel/suspension bodies. So "wheels are sim-only on both
sides" is **not** what the files say: the wreck has wheel boxes, and the drivable asset has no
per-wheel bodies at all — only whole-car shapes.

**Carried.** The donor's flags: 38/42 parts = 1, the 4 wheels = 0 with `world_collision_body_id`
−1 (`T_ROWS.jsonl`; `t16_collision.json`; `T-22`). In bm-RC2 the part count is 61, so the 42-part
denominator is stale; B-04 gave the 19 new parts collision ids −1/−1 by the same hull-less pattern.

**Player-visible match.** Plausible but unproven: JC3 wheels have no separate world shape, and the
chassis hull covers their volume, so a player should not notice. The record does not establish that
AK's wheels are sim-only, only that the drivable asset has no per-wheel bodies.

**Closest JC3 system + gap.** Closest = `parts[].has_world_collision_shape` +
`world_collision_body_id`. Gap = BmAK has no per-part equivalent, so the row is a donor carry. Build
action: keep the flags, but restate the reason as "donor flags; BmAK exposes no per-part flag",
not "wheels are sim-only on both sides".

### T-P2 — 42 damage parts — **COMPROMISE**

**BmAK.** No per-part damage values. The 32 wreck bodies are geometry (§1.2); the visual-damage
component is undecoded (§1.1); the damage-state assets are states/masks, not a part table.

**Carried.** The donor's 24 `Land_*` rows joined to the parts module: 42 parts in bm-009, **61
parts in bm-RC2** (B-04R), 17 distinct types at 42 parts and 19 at 59 parts (`MODLOG.md:17326`).
Four types used by the build have no `PartDamageType` row — `Boat_Antenna`, `Boat_Generic`,
`Plane_Control_Surface`, `Train_Generic` — and fall back to `Default` (`Builds/bm-009/receipt.json`
open item; `GRAB_BACKLOG.md:1663`).

**Player-visible match.** Unproven. The row's own UNKNOWN is "per-part break order in a crash
test"; no BmAK per-part HP exists to compare.

**Closest JC3 system + gap.** Closest = `VehicleDamage.part_damage_types[]` + the part join. Gap =
BmAK per-part values and break order, plus the four fallback types. Build action: update the row to
the RC part count (61), and close the break-order gap with a Q-1 crash test rather than a value.

---

## 4. Cross-row findings (defects found by this audit)

### 4.1 bm-RC2 fails its own damage audit

Measured now:

```
python Tools/scripts/damage_audit.py --build Builds/bm-009/aaf   -> exit 0, "check ok"
python Tools/scripts/damage_audit.py --build Builds/bm-RC2/aaf   -> exit 1
  29 members, 6 outside the shipped range, 5 declared switches
  FAIL max_health = 36000 is outside the shipped 500..4000 and is not declared in damage_switches.json
```

Cause: `damage_switches.json` scopes the `max_health` declaration with `"build": "bm-009"`, and
`damage_audit.py`'s `applies()` only honours a declaration whose build tag equals the audited tag
(`Tools/scripts/damage_audit.py:79-92`). RC2 carries the same 36000 (same module sha), so the
declaration is ignored and the value is unlicensed. This is a **gate failure on the release
candidate**, not a value error: either the declaration must be re-scoped to `bm-RC2` (or made
unscoped once RC2 is the live tree), or RC2 must not carry 36000. It also means the "6 declared
switches" claim in the bm-009 receipt does not hold for RC2.

### 4.2 T-CO1 / T-P3 still quote the wreck as the drivable car

`Working/Translation/COLLISION_ROWS_CORRECTED.md` (9/9 checks) establishes that the "32 boxes" and
the "11 driveable boxes" are **wreck** numbers, and that the drivable asset is 3 boxes + 56 convex
elements. The correction sheet explicitly says **nothing was edited**; `T_ROWS.jsonl` still carries
the old text for T-CO1 and T-P3, and `t16_collision.json` still has `bmak.bodies = 32`. T-P3 is
`next`, so the wrong number is queued to be built from. This audit did not apply the correction
(out of scope, and it has downstream consumers — `t22_collision.py`'s slot binding).

### 4.3 T-P2's part count is stale for the release candidate

The row says 42 parts. bm-009 has 42; bm-RC2 has **61** after B-04R. The damage-type join and the
`has_world_collision_shape` denominator (T-CO3) both still use 42. Any read-back of T-P2/T-CO3
against RC2 will be measuring the wrong population.

### 4.4 The 32 bodies are not "damage bodies"

The brief and the row text call them "32 per-bone damage bodies". `PHYSICS.md` decodes them as
`RB_BodySetup` **collision** boxes on the destroyed asset, with no health or damage field. The only
per-bone damage carrier is `RVisualDamageComponent`, whose values are undecoded. This matters
because it removes the apparent BmAK source for T-DM5/T-P2: there is no BmAK per-part damage table
to translate, only a JC3 donor table to carry.

---

## 5. Gaps and build actions (STAGES.md)

`STAGES.md` says a row is never kept at a donor value "for character", and that where JC3 has no
exact carrier the build stage closes the gap. Applied to these eight rows:

| row | closest JC3 system | gap | build action that closes it |
|---|---|---|---|
| T-DM3 | `VehicleDamage` channels | weapon→channel map (UNKNOWN) | decode a `bullet_heavy` weapon carrier, or record the row as a donor carry |
| T-DM4 | `VehicleDamage` thresholds | BmAK burn/explosion timing (UNKNOWN) | BmAK effect/timer decode or Q-1 observation; no value edit |
| T-DM5 | `part_damage_types[]` + join | BmAK per-part HP and break order | Q-1 crash test; keep donor rows until then |
| T-DM6 | `deform_scale` | evidence that AK deforms (contested) | damage-state/deform decode or frame observation; keep 0 under R1 |
| T-DM8 | `impact_damage_factor` | none behaviourally; no generator shield in JC3 | Q-3/A11 ram take; keep 0 |
| T-CO1 | `.physicsc` hulls | BmAK's 3 drivable boxes + 56 convex elements; no chassis body in BmAK | author hulls from the body mesh / map the 3 boxes; correct the row text first |
| T-CO3 | `has_world_collision_shape` | BmAK has no per-part flag | restate as donor carry; no value edit |
| T-P2 | `part_damage_types[]` + join | BmAK per-part values; 4 fallback types | update to 61 parts; Q-1 crash test |

The two rows that can be closed **offline** are T-CO1 (hull authoring, writer already proven) and
the bookkeeping defects in §4.2/§4.3. The rest need either a BmAK decode that does not exist yet
(T-DM3/4/5/6, T-P2) or an in-game take (T-DM8, T-P2 break order), which the test ban currently
blocks (`STAGES.md`: the ban lifts only when `tmp/freebuff/APPROVED_Q.txt` exists).

---

## 6. Evidence index

| claim | file |
|---|---|
| 32 wreck bodies, no chassis, categories, extents | `Research/BatmobileGrab/PHYSICS.md` |
| drivable 3 boxes, rotations/mode UNKNOWN | `Research/BatmobileGrab/COLLISION_GEOM.md` |
| 43 + 13 convex elements | `Research/BatmobileGrab/COLLISION_CONVEX.md` |
| 1200 HP, generator shield, `TakesDamageFromRam` true, outgoing impact fields | `Research/BatmobileGrab/DAMAGE_RULES.md` §3.1-3.5, §4 |
| `RVisualDamageComponent` 6 B, undecoded | `Research/BatmobileGrab/REMAINDER.md:990,1102`; `REMAINDER_SAMPLE_AUDIT.md:72` |
| damage-state assets / APP-7 challenge | `Research/challenge/card-G1X.md` §6(c) |
| APP-7 and ARM-3 provenance | `GRAB_BACKLOG.md:135,153`; `MODLOG.md:7382` |
| row cells and dispositions | `Working/Translation/T_ROWS.jsonl` |
| damage translation, switches, domains | `Working/Translation/T10_DAMAGE.md`; `damage_switches.json` |
| collision correction (unapplied) | `Working/Translation/COLLISION_ROWS_CORRECTED.md` |
| bm-009 values and receipt | `Working/Damage/bm_health.json`; `Builds/bm-009/receipt.json` |
| bm-RC2 collision, parts, health module | `Builds/bm-RC2/receipt.json`; files on disk |
| JC3 damage chain and UNKNOWNs | `Research/JC3Grab/DAMAGE_MODEL.md`; `ARMOR_STEP.md` |
| 0 rows behaviour-verified | `STATUS.md` |

## 7. Checks run for this audit

| check | result |
|---|---|
| `damage_audit.py --build Builds/bm-009/aaf` | **exit 0**, `check ok`, 6 declared switches |
| `damage_audit.py --build Builds/bm-RC2/aaf` | **exit 1**, `max_health` 36000 unlicensed for `bm-RC2` |
| sha256 bm-009 `sportsmuscle.physicsc` | `1b90daef…`, 340,368 B (donor, untouched) |
| sha256 bm-RC2 `sportsmuscle.physicsc` | `eda17906…`, 902,384 B (B-10c re-encode) |
| sha256 bm-RC2 health module | `d325308b…` = bm-009's private module |
| row text vs corrected collision audit | 2 rows still carry wreck numbers (T-CO1, T-P3) |

## 8. Limits

- **No in-game verification.** Every "player sees" statement is the project's recorded observation
  or an explicit UNKNOWN; `STATUS.md` reports 0/185 rows behaviour-verified.
- **`RVisualDamageComponent` values are not decoded**, so no BmAK visual-damage parameter can be
  compared with the build.
- **The 32 wreck bodies are geometry only**; no per-part health exists on the BmAK side to audit
  T-DM5/T-P2 against.
- **The drivable collision mode is UNKNOWN** (`COLLISION_GEOM.md`), so the 3-box + 56-element set is
  both setups, not one live set.
- **The collision correction was not applied**; this audit reports it, it does not edit
  `T_ROWS.jsonl` or `t16_collision.json`.
- **The bm-RC2 audit failure is reported, not fixed**; re-scoping the switch declaration is a
  ledger/build decision, not a read-only audit action.
