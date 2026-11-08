# T-DM7 / T-RA1 — what a JC3 car can do to what it hits: every layer searched

STATUS: done — one decoded **outgoing contact-damage member** found on every vehicle
(`rotor_collision.damage_to_other_per_second` 100000, n=232), so T-DM7's "no outgoing damage
member" premise is **too strong**; the dodge/shove/kill-flip half (T-RA1) has **no** decoded member
and the exact missing capability is named in §9. Nothing tuned, nothing tested (test ban).

Lane: ram and dodge carriers, 2026-11-06. Brief: G2-28 searched only the vehicle modules; check
character damage on impact, `CDamageController`, collision-event hooks in the entity graph, rigid-body
contact data in `.physicsc`, and how the tank/APC/Bavarium vehicles injure what they touch.

Labels: **decoded** = a member, value or byte read at the file/offset named; **derived** = arithmetic
or stated rule over decoded inputs; **UNKNOWN** = searched and absent, with where it would be found.

---

## 0. Answer

**Outgoing ram damage exists in JC3 as data, but not in BmAK's shape.** Every one of the fleet's
232 vehicle module sets carries `rotor_collision.damage_to_other_per_second` = **100000 / s**, with
`light_object_mass_ratio` 0.02, `mass_ratio_when_no_mass` 0.1 and `min_rpm` 30 — a member whose
entire purpose is *damage dealt to another object on contact*. That is an outgoing contact-damage
channel and it is on the donor too, so T-DM7 cannot stay `out` on the sentence "no outgoing member
exists". What it cannot carry is BmAK's **speed-band** rule (`ImpactMinDamageSpeed` 20,
`ImpactMaxDamageSpeed` 150, `ImpactStrafeMod` 2.25, `ImpactBoostMod` 2.0) — JC3's channel is a
per-second rate gated on rotor RPM, not a ram-speed curve. **T-RA1 has no member at any layer**: no
road assist, dodge, shove or kill-flip name exists in the modules, the entity graphs, the
`CDamageController` objects or the `.physicsc` packfiles; the nearest decoded mechanisms
(`drift.*` torque, `nitro_boost.push_force`, `CForcePulse`) each lack a trigger or a target.

---

## 1. The BmAK numbers (both sets, and the conflict between them)

`decoded` — `Research/BatmobileGrab/CLASS_DEFAULTS.md` (class-default table, offset in the
`RVehicleBatmobileBase` CDO) versus `Research/BatmobileGrab/DAMAGE_RULES.md` (archetype tags,
`sdk-layout`) and the ledger cells in `Working/Translation/T_ROWS.jsonl:95,103`:

| BmAK member | CLASS_DEFAULTS | archetype / ledger | conflict |
|---|---|---|---|
| `ImpactMinDamageSpeed` | **60.0** (0x04E8, export off 6864) | **20** | **yes** |
| `ImpactMaxDamageSpeed` | **200.0** (0x04E0, off 6860) | **150** | **yes** |
| `ImpactStrafeMod` | **1.5** (0x04F0, off 6868) | **2.25** | **yes** |
| `ImpactBoostMod` | 1.5 (`CLASS_DEFAULTS.md:260`) | 2.0 | **yes** (`BOOST_COVERAGE.md:120` notes it) |
| `ImpactRoadAssistFactor` | **40000** (0x02CE, off 5988) | **90000** | **yes** |
| `ImpactRoadAssistMaxTorque` | **15000** (0x02D6, off 5992) | **30000** | **yes** |
| `ImpactRoadAssistAngleStrength` | **1500** (0x02FE, off 6012) | **2000** | **yes** |
| `ImpactRoadAssistSceneryDuration` | 0.75 | — | — |
| `ImpactRoadAssistEnemyDuration` | 1.5 | — | — |
| `ImpactRoadAssistMaxAngle` | 45.0 | — | — |
| `ImpactRoadAssistAngVelocityTime` | 0.25 | — | — |
| `ImpactRoadAssistSteeringFactor` | 30.0 | — | — |
| `ImpactRoadAssistLookAheadTime` | 1.0 | — | — |
| `PMDodgeTorque` | 5000.0 (0x0AA4, off 8156) | `PMDodge*` (no values in the cell) | — |
| `PMDodgeForce` | 6000.0 (0x0AAC, off 8160) | — | — |
| `PMDodgeDuration` | 0.25 (0x0AB4, off 8164) | — | — |
| `bAllowPMDodge` | **True** (`CLASS_DEFAULTS.md:108`, boolword at 0x010C/4576, mask 0x20) | — | — |
| `BattleDodgeImpulse` | 100000.0 (0x032E, off 6420) | `BattleDodgeImpulse` | — |
| `VehicleShovingTorque` | **20000.0** (0x0724, off 7416) | **10000** | **yes** |
| `KillFlipTorque` | **-2000000.0** (0x0588, off 7192) | `KillFlip*` | — |
| `KillFlipTorqueDuration` | 1.5 (0x0590, off 7196) | — | — |
| `BattleModeImpactMin/MaxDamageSpeed` | 120 / 540 | same | — |
| `BattleModeImpactMaxDamagePow` | 0.5 (Joker 0.666) | — | — |

`derived` — the two columns cannot both be the shipped value. Both are "decoded" by their own doc,
from different files: CLASS_DEFAULTS reads the class-default object, DAMAGE_RULES reads the archetype
tag stream. The archetype is the instance that ships, so the archetype column should win — but this
brief does not settle it and does not edit a row. **Every carrier table below therefore quotes both
and marks which is which.** Where the ledger's cell and CLASS_DEFAULTS disagree, an operator-level
value correction is a separate edit (T-DM7's value cell, T-RA1's parenthetical).

---

## 2. Layer 1 — the vehicle module (the only layer with an outgoing member)

`decoded` — `Research/JC3Grab/VOCABULARY.md` line 1415, re-counted over 232 builds; the block is
present on **every** vehicle, donor included:

| member | type | fleet | donor | module owner |
|---|---|---|---|---|
| `rotor_collision.damage_to_other_per_second` | float | **100000 .. 100000** (n=232) | 100000 | `VehicleCommon` / `all_vehicles_common` (inner `.ee` module) |
| `rotor_collision.light_object_mass_ratio` | float | 0.02 (n=232) | 0.02 | same |
| `rotor_collision.mass_ratio_when_no_mass` | float | 0.1 (n=232) | 0.1 | same |
| `rotor_collision.min_rpm` | float | 30 (n=232) | 30 | same |

**Offset: UNKNOWN.** A type-dictionary scan of all **408** standalone `*_vmodc` files under
`jc_vehicles` (this session, `jc3adf`, 0 decode failures) finds no type declaring
`damage_to_other_per_second`; the block lives in an `.ee`-embedded shared module, which this brief
did not open. The path, type and value are decoded by the project's vocabulary pass; the byte offset
is not.

`derived` — this member is the closest thing to T-DM7 in the whole corpus: it names a *rate of damage
to another object*, has a mass-ratio rule (so hitting a light object — a pedestrian or a bike —
scales), and a threshold (`min_rpm` 30) that gates it. Its name says rotor: it is the helicopter
blade's damage to what it clips, and every vehicle carries the block because the block is shared, not
because every vehicle spins a rotor. Whether the engine evaluates it on a `CCar` with no rotor is
**UNKNOWN** and is the one probe that decides T-DM7's carrier.

Other module members in the same layer, and why they are not outgoing damage:

| member | fleet | what it is |
|---|---|---|
| `VehicleDamage.impact_damage_factor` | **1 .. 12** (n=233) | **incoming**: scales damage the vehicle takes on impact |
| `VehicleDamage.impact_armor` / `impact_armor_strength` | 0..5 / 0..100 | incoming mitigation |
| `VehicleDamage.part_damage_types[].damages_owning_vehicle` | 0..1 (n=4820) | whether a broken part hurts *its own* car |
| `CustomVelocityDamper.velocity_damper.collision_spin_damping` | 0..5 (n=145) | collision response (spin), no damage |
| `arcade.nitro_boost.push_force` | 15000 (n=145) | a forward force while boosting, no contact needed |

---

## 3. Layer 2 — the entity root and `CDamageController`

`decoded` — `Research/JC3Grab/DAMAGE_MECHANISMS.md` §1-2 (232 decoded `.epe` graphs, 91,157 objects):

| object | members | values | what it can express |
|---|---|---|---|
| vehicle root (`CCar` 126, …) | `health` float32 (0x09), `invulnerable` int32 (0x0e), `damage` int32 object id | 100.0 / 0 / module ref, all 233 roots | the *victim's* health and immunity switch |
| `CDamageController` (104 objects) | `health`, `invulnerable` | 10 of 104 ship `invulnerable = 1` (props: barrels, cargo, monorail flatbeds) | a destructible prop's health, i.e. the target side |

**Neither object has an outgoing field.** A `CDamageController` is the thing that *receives* damage;
its byte address is decoded (`epe + 1167`, int32), and `jc3_damage_search.py --epe` prints the triple.
So the "character damage on impact" layer is not here: this layer is prop/vehicle health, and the
amount dealt to it comes from whatever fires the damage event, which no decoded member of this layer
names.

`derived` — the useful half for T-DM7 is the **victim** side: if a `CDamageController` prop or a
vehicle root can be damaged at all, the only thing missing on the attacker side is a member that says
how much. `rotor_collision.damage_to_other_per_second` is exactly that member (§2), which is why the
two layers are complementary rather than contradictory.

---

## 4. Layer 3 — collision-event hooks in the entity graph

`decoded` — `Research/JC3Grab/ENTITIES.md` class census (232 entity graphs) and `INTERACTION.md`:

| class | objects | collision/damage member? |
|---|---:|---|
| `CInteractionGraphExitObstructedCondition` | 865 | no — an exit-obstruction *condition* |
| `CInteraction` | 675 | no |
| `CInteractionGraphStuntTransitionValidCondition` | 310 | no |
| `CForcePulse` | 307 | no collision trigger: `FORCEPULSE.md:181` "collision 0 of 23 tune paths; no pulse owner is a collision object" |
| `CShapeTrigger` / `CShapeTriggerComponent` | 32 / 38 | a trigger volume, no damage field |
| `CEventTrigger` / `SEventTriggerComponent` | 18 / 36 | event dispatch, no damage field |
| `CGraphScriptGameObject` | 13 | script hook, no velocity/impulse/force member (`EJECT.md` §1: 0 of 4,832 exit nodes carry one) |
| `CMaterialEffectTable` | 72 | material → effect, not damage |
| `CDamageController` | 104 | victim health only (§3) |

`grep -i "collision\|impact\|damage"` over `INTERACTION.md` returns **0 lines**; the graph's condition
classes are interaction/stunt gates, not contact events. `CForcePulse`'s only decoded trigger is an
explosion (`FORCEPULSE.md` §4.1), and the 14 unowned pulses have `UNKNOWN` owners.

**Verdict:** the entity graph can *notice* an obstruction and can *fire* a pulse, but it has no
"on contact, damage the other actor" node. No BmAK number can be carried here.

---

## 5. Layer 4 — rigid-body contact data in `.physicsc`

`decoded` — `Research/JC3Grab/PHYSICS_ROLES.md`, `PHYSICS_LIMITS*.md`, `SHAPES.md`, `DECODE_DEPTH.md`:

| what the packfile holds | count | decoded |
|---|---:|---|
| `hknpConvexPolytopeShape` | 54 (18,865 in fleet) | **FULL**, 0 violations (supporting-plane oracle) |
| `hknpDynamicCompoundShape` | 20 | partial (child AABBs) |
| `hknpExternMeshShape` | 18 | partial |
| `hknpShapeMassProperties` | 56 | **named only** — no mass, inertia or centre of mass read |
| `hkpLimitedHingeConstraintData` | 419 | atoms decoded, incl. `TYPE_SETUP_STABILIZATION` at +0x0B0 |
| `hkpRagdollConstraintData` | 71 | atoms decoded |
| **contact material / friction / restitution table** | **0** | **not present in any decoded file** |
| **contact-point damage / impulse record** | **0** | **not present** |

The one contact fact decoded is geometric: `SHAPES.md:69` proves the support plane with
`max(n·v) + d == 0` at the contact vertex — that is hull construction, not a collision response.

**Verdict:** JC3's `.physicsc` layer describes shapes, bodies and joints; it carries **no contact
material and no damage-on-contact record**. It cannot express T-DM7 or T-RA1, and it is the layer that
would have to be extended if a contact-damage member had to be added below the module layer.

---

## 6. Layer 5 — how the tank, APC and Bavarium vehicles injure what they touch

`decoded` — `Research/BatmobileGrab/DAMAGE_RULES.md:107-108,162,274,325` (the BmAK side) and the JC3
vehicle classes:

| BmAK class/member | what it says |
|---|---|
| `RVehicleHeavyTank`, `RTankMissile`, `RVehicleHeavyTank.StartingHealth` | the tank's damage comes from **weapon archetypes** (`Damage`, `MyDamageType`), not from contact |
| `bDamagedByCloudburstTank` | a *victim* flag for a specific tank type |
| `bHasAPCStyleWeakSpot` + `RemoveWeakSpot` | the APC's damage multiplier is a **weak spot**, removed by the Batmobile's sideswipe |
| `RVehicleTank.MissileVolleyMaxHealth` | health of a missile volley sub-object |

JC3 side: there is **no tank-contact damage class** in the decoded graphs. The tank/APC/Bavarium
vehicles are `CCar`/`CForcePulse` owners like every other car: 126 of the 307 pulses are owned by a
`CCar`, 23 by `CHelicopter`, and every pulse fires an explosion tune. So "how the tank injures what
it touches" in JC3 is: its **weapons** (projectile `Damage`) and its **explosion pulse** — not a
contact channel.

`derived` — the Bavarium shield is a `CPartProp`/`BavariumShield` object (T-WP13 report), not a damage
source; nothing in the decoded shield carries an outgoing damage value.

**Verdict:** the tank/APC precedent does **not** supply a contact-damage member. It reinforces §4:
in JC3, damage is dealt by weapons and pulses, and contact damage is the `rotor_collision` block's
job.

---

## 7. Character damage on impact — the layer that is not decoded at all

Searches run, all negative:

```
grep -rn -i "CCharacter" Research/JC3Grab/*.md          → 0
grep -rn -i "pedestrian" Research/JC3Grab/*.md          → 0
grep -rn -i "ragdoll" Research/JC3Grab/*.md             → only hkpRagdollConstraintData (vehicle joints, 71)
```

The entity-graph census (`ENTITIES.md`, 104 classes) contains **no character class**; the graphs are
vehicle/prop graphs. Character health is an engine/NPC-system fact, not a vehicle-entity member, and no
decoded file names how a vehicle's contact reaches it.

**UNKNOWN:** the character damage path. *Tried:* the 232 vehicle graphs, the 104-class graph
vocabulary, the `.physicsc` contact search, `CDamageController` (props only), the pulse owners.
*Where it would be found:* the NPC/character damage system's classes in the executable, or a live
contact test. That is exactly the capability `rotor_collision.damage_to_other_per_second` would need
to reach — and it is the reason the rotor block is the right candidate even though its name says
rotor.

---

## 8. T-RA1 — road assist, dodge, shove, kill-flip: what each layer can express

| BmAK member | value (CLASS_DEFAULTS / archetype) | JC3 member that could carry it | verdict |
|---|---|---|---|
| `ImpactRoadAssistFactor` | 40000 / 90000 | none — no road-assist member at any layer | **not carried** |
| `ImpactRoadAssistMaxTorque` | 15000 / 30000 | `CustomLandGlobal.drift.max_drift_torque` float **0x48** (0..35000, n=145) — a yaw torque, wrong trigger | **wrong mechanism**: drift torque, not a post-impact assist |
| `ImpactRoadAssistAngleStrength` | 1500 / 2000 | `drift.counter_steer_torque` **0x4C** (0..60000) | wrong trigger |
| `ImpactRoadAssist*Duration/Angle/Steering/LookAhead` | 0.75 s / 1.5 s / 45° / 0.25 s / 30 / 1.0 s | none | **not carried** |
| `PMDodgeTorque` | 5000 | `drift.max_drift_torque` **0x48** (5000 is in range) | value fits, trigger does not |
| `PMDodgeForce` | 6000 | `arcade.nitro_boost.push_force` float (15000 fleet, n=145) | a boost force, not a dodge |
| `PMDodgeDuration` | 0.25 s | none | **not carried** |
| `bAllowPMDodge` | True | none (no per-car dodge switch) | **not carried** |
| `BattleDodgeImpulse` | 100000 | `CForcePulse` (307; hashed impulse members `id:24872388` 25..1000, `id:9865E7F2` 25..250) | **wrong trigger** (explosion only) and the impulse unit/name is UNKNOWN |
| `VehicleShovingTorque` | 20000 / 10000 | `drift.max_drift_torque` **0x48** (0..35000) | value fits; no shove event |
| `KillFlipTorque` / `KillFlipTorqueDuration` | -2000000 / 1.5 s | none — no member reaches 2e6, none is a timed torque | **not carried** |
| `ImpactShake*` | — | camera shake lives in the camera rig; T-CAM11 already records the missing numeric bridge | not this row |

`decoded` — the only per-event impulse block on a land vehicle is `arcade.turbo_jump.*`
(`CustomLandGlobal`, floats at **0xC4, 0xC8, 0xCC, 0xD0, 0xD4, 0xD8**; fleet 12..15 / 50 km/h / 200
km/h / ×2) — a fixed-axis punch on a jump (`DRIVE_CARRIERS.md` C7). It is the closest thing to
`BattleDodgeImpulse` **in shape** (impulse with a multiplier and a top speed), but it fires on the
jump action, not on a dodge, and it has no target selection.

**Verdict for T-RA1:** no candidate carries it. The mechanism that would have to be added is a
**triggered, non-damaging impulse/torque with target selection and a duration** — see §9.

---

## 9. Negative answer — every place searched, and the capability that must be added

### Places searched (all layers, this brief + the project files it read)

| layer | file / tool | result |
|---|---|---|
| vehicle modules (145 land, 232 all) | `VOCABULARY.md` 1,421 paths / 155-value scan; this session's re-decode of 408 `*_vmodc` type dictionaries | `rotor_collision.damage_to_other_per_second` (outgoing, §2); **no** road-assist / dodge / shove / kill-flip / contact-damage member |
| entity roots | `DAMAGE_MECHANISMS.md` (232 graphs, 91,157 objects) | `health`/`invulnerable`/`damage`; victim side only |
| `CDamageController` | same, 104 objects | victim health; 10 ship `invulnerable = 1` |
| entity graph hooks | `ENTITIES.md` 104-class census; `INTERACTION.md`; `FORCEPULSE.md`; `EJECT.md` | no contact-damage node; pulse trigger is explosion only |
| `.physicsc` | `PHYSICS_ROLES.md`, `PHYSICS_LIMITS.md`, `SHAPES.md`, `DECODE_DEPTH.md` (51 files, 419 hinges, 71 ragdolls) | shapes/bodies/joints only; **0 contact material, 0 contact-damage record** |
| characters | `ENTITIES.md`, `grep CCharacter|pedestrian|ragdoll` | **0 character classes decoded**; character health is native |
| tank / APC / Bavarium | `DAMAGE_RULES.md:107-108,162,274,325`; pulse owners; T-WP13 shield note | damage via weapons + explosion pulses, not contact |
| script layer | `CGraphScriptGameObject` 13; `EJECT.md` 0/4,832 force members; `REBELDROP.md` | no rotation/impulse/force writers decoded |

### The capability that would have to be added

> **T-DM7:** a land-vehicle member that converts **contact speed** into damage to the other actor —
> BmAK's band is `ImpactMinDamageSpeed` 20 → `ImpactMaxDamageSpeed` 150 with `ImpactStrafeMod` 2.25
> and `ImpactBoostMod` 2.0 — plus a per-target mass rule. JC3 has the *rate* (`rotor_collision`,
> 100000/s on 232 builds) and the mass ratios, but **no speed band and no strafe/boost modifier**.
> If the rotor block is not evaluated on a `CCar`, the missing capability is exactly that block
> evaluated for a car body: one float rate + two mass ratios, already present in every module set.

> **T-RA1:** a **triggered** (event-driven, not continuous) impulse/torque with **target selection**
> and a **duration** — road assist (40000/90000 factor, 15000/30000 max torque, 45°, 0.25 s), dodge
> (5000 torque / 6000 force / 0.25 s / allow flag), shove (20000/10000 torque) and kill-flip
> (−2000000 over 1.5 s). The nearest JC3 members are a drift yaw torque and a boost push force; both
> are continuous, neither selects a target, neither has a duration.

`COMPROMISES`: none proposed. No value was tuned and no ledger row was edited by this brief.

---

## 10. Files, commands, UNKNOWNs

**Written:** `tmp/freebuff/reports/carrier-ram-and-dodge.md` (this file). Nothing else created/edited.

**Commands run (verbatim, key lines):**

```
$ grep -n "T-DM7\|T-RA1" Working/Translation/T_ROWS.jsonl
95:{"id":"T-DM7", … "why":"stays `out`: G2-28 found no outgoing ram damage - its chain is hit -> own health and the only impact member is `impact_damage_factor` (incoming) …","edits":0}
103:{"id":"T-RA1", … "why":"stays `out`: no ram-assist, dodge, shove or kill-flip member anywhere in the 52-type / 1,421-path vocabulary …","edits":0}

$ grep -rn "ImpactMinDamageSpeed\|ImpactRoadAssist\|PMDodge\|BattleDodgeImpulse\|VehicleShovingTorque\|KillFlip" Research/BatmobileGrab/*.md
CLASS_DEFAULTS.md:256:| 78 | `0x04E0` | 6860 | `ImpactMaxDamageSpeed` | FloatProperty | 200.0 | decoded |
CLASS_DEFAULTS.md:257:| 79 | `0x04E8` | 6864 | `ImpactMinDamageSpeed` | FloatProperty | 60.0 | decoded |
CLASS_DEFAULTS.md:258:| 80 | `0x04F0` | 6868 | `ImpactStrafeMod` | FloatProperty | 1.5 | decoded |
CLASS_DEFAULTS.md:229:| 51 | `0x02CE` | 5988 | `ImpactRoadAssistFactor` | FloatProperty | 40000.0 | decoded |
CLASS_DEFAULTS.md:326-328:| `PMDodgeTorque` 5000.0 | `PMDodgeForce` 6000.0 | `PMDodgeDuration` 0.25 |
CLASS_DEFAULTS.md:241:| 63 | `0x032E` | 6420 | `BattleDodgeImpulse` | FloatProperty | 100000.0 |
CLASS_DEFAULTS.md:286:| 108 | `0x0724` | 7416 | `VehicleShovingTorque` | FloatProperty | 20000.0 |
CLASS_DEFAULTS.md:270-271:| `KillFlipTorque` -2000000.0 | `KillFlipTorqueDuration` 1.5 |
DAMAGE_RULES.md:153:| `ImpactStrafeMod` | 2.25 | 0.8 |      ← archetype; conflicts with CLASS_DEFAULTS 1.5
DAMAGE_RULES.md:274:| ram by the Batmobile | `CanBatmobileDoImpactDamage` (native) + `CalculateAndStoreImpactDamage` (script) | speed band 20→150 …

$ grep -n -i "impact\|contact\|collision\|damage\|ragdoll" Research/JC3Grab/VOCABULARY.md
1415:| `rotor_collision.damage_to_other_per_second` | float | 100000 .. 100000 (med 100000, n=232) | 100000 |
1416:| `rotor_collision.light_object_mass_ratio` | float | 0.02 .. 0.02 (n=232) | 0.0199999996 |
1417:| `rotor_collision.mass_ratio_when_no_mass` | float | 0.1 .. 0.1 (n=232) | 0.100000001 |
1418:| `rotor_collision.min_rpm` | float | 30 .. 30 (n=232) | 30 |
1474:| `impact_armor` | int32 | 0 .. 5 (med 0, n=233) | 0 |
1476:| `impact_damage_factor` | float | 1 .. 12 (med 1, n=233) | 1 |
1484:| `part_damage_types[].damages_owning_vehicle` | int8 | 0 .. 1 (med 1, n=4820) | 1 |

$ grep -rn "CDamageController" Research --include=*.md
Research/JC3Grab/DAMAGE_MECHANISMS.md:39:`CDamageController` — the destructible-prop controller used for cargo, barrels and the monorail
Research/JC3Grab/ENTITIES.md:61:| `CDamageController` | 104 |

$ grep -rn -i "contact\|hknpMaterial\|collision_filter\|material" Research/JC3Grab/PHYSICS_ROLES*.md Research/JC3Grab/SHAPES.md Research/JC3Grab/PHYSICS.md
Research/JC3Grab/SHAPES.md:69:`max(n·v) + d == 0` at the contact vertex and `<= 0` for all the others.
   (no contact material, no collision filter, no contact-damage record)

$ grep -rn -i "CCharacter\|ragdoll\|pedestrian" Research/JC3Grab/*.md
   only hkpRagdollConstraintData (vehicle joints, 71 objects)

$ sed -n '170,195p' Research/JC3Grab/FORCEPULSE.md
| collision | 0 of 23 tune paths mention collision; no pulse owner is a collision object |

$ cd Tools/scripts && python - # jc3adf type-dictionary scan, 408 *_vmodc under jc_vehicles
   # looking for any type declaring 'damage_to_other'; result: 0 types (block is in an .ee module)
```

**UNKNOWNs**

1. **`rotor_collision`'s offset in file** — the block is in an `.ee`-embedded shared module, not in
   any of the 408 standalone `*_vmodc` files. Would settle: decode the shared `vehicle_common`
   bundle with `eetoc` + `jc3adf`.
2. **Whether the engine evaluates `rotor_collision` on a `CCar` with no rotor** — the decisive probe
   for T-DM7; test ban.
3. **The character damage path** — no character class in the 104-class graph vocabulary; would be
   found in the NPC/character damage code, not in a vehicle asset.
4. **Whether BmAK's archetype values (20/150/2.25) or CLASS_DEFAULTS' (60/200/1.5) are the shipped
   ones** — two files disagree; the archetype is the instance, but no third oracle was read here.
5. **The `CForcePulse` hashed impulse members** (`id:24872388`, `id:9865E7F2`, …) — names are in no
   shipped table (`FORCEPULSE.md` §1), so no BmAK impulse can be mapped to a slot.
6. **Whether a `CDamageController` prop can be damaged by vehicle contact at all** — the prop has
   health; the attacker-side member is `rotor_collision` (UNKNOWN gate).

**Revert:** delete `tmp/freebuff/reports/carrier-ram-and-dodge.md`. Nothing else changed.
