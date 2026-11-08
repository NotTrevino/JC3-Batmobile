# EMP: the effect object, the state it sets, and the effects it skips

Scrape of the two operator leads of 2026-11-07, read out of the already-decoded BmAK records and
then out of the cooked packages with the project's own readers. Read-only: nothing was launched,
patched or installed.

**Provenance / reversibility.** New file, `reports/emp-effects-scrape-leads.md` (copied to
`tmp/freebuff/reports/emp-effects-scrape-leads.md`). It changes no source, no record and no
package; reverting it is deleting the two copies (`git rm` or `rm`). It is the correct file
because it is the requested output path for this task, and it holds only claims that cite a
record already in the repo or a byte range re-read below.

**The three reports the task pointed at do not exist**: `reports/emp-visual-and-hit-plan.md`,
`reports/immobiliser-and-emp-trigger.md` and `reports/immobilizer-vs-emp-missile.md` are absent
(`reports/` was created by this task; a glob for `reports/*emp*` returns nothing). Their content
is therefore not evidence here. What does exist and is used: `Research/BatmobileGrab/WEAPONS.md`
(§9 EMP gadget, §10 EMP missile launcher, §4 projectiles), `DAMAGE_RULES.md`, `PARTICLES.md`,
`PARTICLES_FEATURES.md`, `ASSETS.md`, `COVERAGE.json`, `BMSDK_OFFSETS.json`, `CHAIN.json`,
`CLASS_DEFAULTS.json`, `objects.jsonl`, `COLLISION_WHERE.md`.

## 0. Verdict in one paragraph

In battle mode the EMP is **not a projectile**: it is the weapon gadget `RBatmobileEMP`
(`Weapons.Batmobile_EMP_Burst`), and it has no explosion, fire or smoke field anywhere in its
class layout or its archetype - which is exactly why the operator sees none. What it carries is a
charge component (`ChargeParticle0`), a radial impulse component, per-power-level fire particles
and sounds, and **`DisableEnemyDuration = [2, 4, 8, 12]` seconds** - so the enemy state it sets is
a *timed disable*, not a permanent kill. The disable itself is implemented on the enemy vehicle
classes (`RVehicleNPC.TakeDamageFromEMP`, `DisabledByEMP`, `bCompletelyDisabledByEMP`), and the
flying and car subclasses both forward to it, while the heavy tank has its own branch with an
`EMPIneffectiveLine` dialogue. Whether the target's health is zeroed ("killed") is **UNKNOWN**;
the 12 s maximum timer argues against permanent.

## 1. The table

Status vocabulary as the project uses it: **decoded** = bytes read at a named payload offset of a
named export; **derived** = produced by a stated rule from decoded bytes; **UNKNOWN** = no layout
evidence.

| # | lead | evidence: file + offset / object path | status | file or search that would settle it |
|---|---|---|---|---|
| A1 | Which object is "the EMP" in battle mode | `COLLISION_WHERE.md:69` - `RVehicleBatmobile.VehicleWeapons` @4956 → `Weapons.Batmobile_EMP_Burst` class `RBatmobileEMP`; pursuit mode @5036 → `Batmobile_EMP_Missile_Launcher` (`COLLISION_WHERE.md:73`) | **decoded** | - |
| A2 | EMP burst class layout and fields | `BMSDK_OFFSETS.json` → `classes.RBatmobileEMP` (super `RVehicleWeapon`, size 2552): `Range`@2396, `DisableEnemyDuration`@2400, `ChargeParticle`@2416, `PowerLevelChargeTime`@2424, `FireParticle`@2440, `EMPFireSound`@2456, `EMPFireSwitch`@2472, `ImpulseComponent`@2496, `ChargingEMP`@2508, `EMPImpulse`@2512, `EMPVehicleImpulse`@2528, `PowerLevel`@2544, `MaxPowerLevel`@2548 | **decoded** | - |
| A3 | Shipped values of that object (class default object) | `BmGame.upk` export **46694** `BmGame.Default__RBatmobileEMP` (class `RBatmobileEMP`, 276 B, 15 tags, stop `eof`): `Range`=7500.0; `DisableEnemyDuration`=**[2.0, 4.0, 8.0, 12.0]**; `PowerLevelChargeTime`=[0.0, 0.5, 1.0, 1.5]; `EMPImpulse`=[5000.0]; `EMPVehicleImpulse`=[20000.0]; `WeaponCoolDown`@2096=10.0; `PowerConsumption`@2360=1.0; `TempName`="EMP Burst"; `GadgetType`="GA_BatmobileWeapon_EMPBurst" | **decoded** | - |
| A4 | Recovery timer for the disabled enemy | same export, `DisableEnemyDuration` @2400, 4 floats = 2/4/8/12 s, index = power level (4 entries; `PowerLevelChargeTime` also 4) | **decoded** | how the value is handed to the target: `RBatmobileEMP.FireEMP` body (export 46666) shows no `TakeDamageFromEMP` call, so the pass is native/UNKNOWN |
| A5 | The archetype overrides the cooldown, not the timer | `Research/BatmobileGrab/CHAIN.json` → `RBatmobileEMP.Playable_Batmobile_SF.Batmobile_EMP_Burst` `WeaponCoolDown`@2096 = 2.0 (CDO 10.0); the archetype serialises **none** of `Range`/`DisableEnemyDuration`/`PowerLevelChargeTime`/`EMPImpulse`/`EMPVehicleImpulse` (12 tags, `objects.jsonl`) | **decoded** | - |
| A6 | Damage type of the EMP burst | none: `RBatmobileEMP` declares no `MyDamageType`/`Projectile` member, and no `ProjectileArchetype` points at anything; the dedicated class **`RDmgType_BatmobileEMP`** exists in `BmGame.upk` (export 76647, default object 76648) | **decoded** (class exists) / **UNKNOWN** (which script call applies it) | `RBatmobileEMP.FireEMP` export 46666 - a full bytecode trace (`Tools/scripts/bmak_damage.py` idiom) would show the `TakeRadiusDamage`/damage-type literal |
| A7 | No explosion / no fire / no smoke | by absence: `BMSDK_OFFSETS.json` `RBatmobileEMP` has no `ExplosionTemplate`, `ImpactExplosion`, `ImpactExplosionFlameTrail`, `DeathExplosion` member; `objects.jsonl` archetype carries only `ChargeParticle0`, `ImpulseComponent0`, two wheel materials, `Engine.Play_Batmobile_EMP` | **derived** | contrast is decoded: the *pursuit* EMP missile does carry `ExplosionTemplate` + `ImpactExplosionFlameTrail` (A10) |
| A8 | The lightning effect that does play | `ChargeParticle` @2416 → `Weapons.Batmobile_EMP_Burst.ChargeParticle0` (`WEAPONS.md` §9); CDO points at `Default__RBatmobileEMP.ChargeParticle0`; the EMP particle systems in the same packages: `Particles.EMP_Burst_Charge` (4 emitters, all light, material `Shaders.EMP_BuildUp`), `EMP_Burst_Stage_01..04` (10/10/10/13 emitters; light+mesh+sprite; `Engine.EMP_Sphere` mesh; `Engine.AR_Distortion`, `Engine.EMP_Burst_Line_MAT`) | **decoded** (objects and their emitter counts) | which stage binds to which power level: the archetype's `FireParticle`/`EMPFireSwitch` arrays are 4-item but their payload is not decoded (`WEAPONS.md` §9) - re-walk those two arrays in Playable_Batmobile_SF.upk |
| A9 | Per-level fire particles and the EMP sound | archetype `FireParticle`@2440 = 4 items, `EMPFireSwitch`@2472 = 4 items (one per power level); `FireStartEvent`/`IndividualFireEvent` @2176/@2200 = `Engine.Play_Batmobile_EMP`; CDO `EMPFireSound`/`EMPFireSwitch` arrays absent | **decoded** (counts, sound event) / **derived** (stage↔level mapping) | decode the 4 `FireParticle` refs (same array re-walk as A8) |
| A10 | Pursuit-mode EMP missile (the other EMP) | `WEAPONS.md` §4: `Batmobile_EMPMissile_Projectile` - `MaxSpeed` 7500, `AccelRate` 40000, `Damage` 60, `DamageRadius` 0, `MyDamageType` = `Core.RDmgType_BatmobileCannon`, `ExplosionTemplate` = `Rocket.Batmobil_Rocket_Explosion` (14 emitters), `ImpactExplosionFlameTrail` = `Damage_States.FireTrail_APC` (10), explosion sound `Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact`; `..._ForCars` variant has no scalars at all, `Rocket_Explosion_Small` (9) + `FireTrail_Car` (9) | **decoded** | - |
| A11 | "the car is killed" | `RVehicleNPC.TakeDamageFromEMP` (export 11526, 173 B, 135 B script) exists and `RVehicleCar.TakeDamageFromEMP` (128660) calls it; state members `bCompletelyDisabledByEMP` (11257), `VehicleAsBombEMP` (11255), `DamageTimeEMP` (11142) | **derived** (a disable state exists) / **UNKNOWN** (health zeroed?) | no `Health` reference resolves in 11526's aligned trace; a verified bytecode trace of 11526 + `SetVehicleAsBomb` would settle it |
| A12 | Which enemy classes respond - cars | `RVehicleCar.TakeDamageFromEMP` (export 128660, 180 B) `final` → `RVehicleNPC.TakeDamageFromEMP`; `RVehicleSimNPC.DisabledByEMP` (128580) + `SetDisabledByEMP` (128582, 52 B) | **decoded** | - |
| B1 | Chopper drones respond | `RVehicleFlying.TakeDamageFromEMP` (export 128806, 111 B) `final` → `RVehicleNPC.TakeDamageFromEMP`; `RVehicleSimFlyingNPC.SetDisabledByEMP` (128723, 64 B) | **decoded** | - |
| B2 | Tank drones: own branch, likely "ineffective" | `RVehicleHeavyTank.TakeDamageFromEMP` (export 129436, 289 B, **does not** call `RVehicleNPC.TakeDamageFromEMP`); refs `RGameInfo.GetPC` + `RPawnPlayer.PlayThought` + `RVehicleCombatManager.PlayCommanderBark`; `EMPIneffectiveLine` (129218, ObjectProperty) is the dialogue it plays | **decoded** (branch exists) / **derived** (tank answers with a line instead of a disable) | the object `EMPIneffectiveLine` points at (decode its tag payload) + a verified trace of 129436 |
| B3 | Stun temporary or permanent, per drone | `RVehicleNPC.DamageTimeEMP` (export 11142, FloatProperty) is a per-class timer; `UpdateDamageFromEMP` (11528, 43 B, 5 B script) is effectively empty, so the countdown is native | **decoded** (a timer field exists) / **UNKNOWN** (its shipped default per class) | a BmSDK layout for `RVehicleNPC`/`RVehicleFlying`/`RVehicleHeavyTank` added to `BMSDK_OFFSETS.json` (`bmsdk_offsets.py`), then read their `Default__*` objects in BmGame.upk |
| B4 | The Batmobile's own EMP flags (mirror mechanism) | `RVehicleBatmobileBase.DisabledByEMP`@4568 mask 1073741824, `VulnerableToEMP`@4568, `EMPRepairable`@4572 mask 1, `EMPMaterial`@5508, `EMPMaterialIndex`@5936 (=9 in the CDO); `SetDisabledByEMP` (10439), `FiredEMP` (10838), `StopEMP` (10839) | **decoded** (members, index 9) / **derived** (`DisabledByEMP` and `EMPRepairable` are 0 in the CDO: word@4568 = 0x400000, word@4572 = 0x800) | `VulnerableToEMP`'s bit is the one the layout records without a mask - only the BmSDK getter gives it |
| B5 | Other EMP consumers | `RBatmobileCannon.EMPTarget`@2520, `EMPLockOnTime`@2924, `EMPLockOn`@2928 (the cannon can hold an EMP lock); `RDisruptableLaserGridBase.bImmuneToBatmobileEMP` (76207); `RSeqAct_StopPlayerUsingGadgets.bBatmobileEMP`/`bBatmobileEMPMissile` (97285/97283) | **decoded** | - |

## 2. What the operator leads get right, and where the data disagrees

**Lead (a) - battle-mode EMP: no explosion, no smoke, no flame, lightning, car killed.**

- *No explosion / smoke / flame*: **supported**. The battle-mode object is a `RVehicleWeapon`
  gadget, and neither its class layout nor its archetype has an explosion, impact or flame-trail
  field. The only FX it can raise are the charge component and the per-level fire particles.
  This is a property of the object, not of a flag that could be wrong.
- *Lightning*: **supported**. `ChargeParticle0` is a `ParticleSystemComponent`; the EMP particle
  family in these packages is electric (`EMP_Burst_Charge` is 4 light emitters on
  `Shaders.EMP_BuildUp`; the four stages add `Engine.EMP_Sphere` meshes, `Engine.AR_Distortion`
  and `Engine.EMP_Burst_Line_MAT`), and the wheel material swap uses
  `Batmobile_V3_Wheel_EMP_MAT_INST`.
- *Car is killed / permanently disabled*: **contradicted in the "permanent" part, UNKNOWN in the
  "killed" part.** The disable is a timer: `DisableEnemyDuration = [2, 4, 8, 12]` s, four entries
  for four power levels, with `PowerLevelChargeTime = [0, 0.5, 1, 1.5]` charging. A 12 s maximum
  is long enough to read as "permanent" in a fight, but nothing in the object says never-recovers.
  Whether `TakeDamageFromEMP` also zeroes health is not readable from the aligned trace.

**Lead (b) - tank drones and chopper drones are stunned.**

- *Chopper drones*: **supported at class level.** `RVehicleFlying.TakeDamageFromEMP` forwards to
  `RVehicleNPC.TakeDamageFromEMP`, and `RVehicleSimFlyingNPC.SetDisabledByEMP` exists. The flying
  family has both halves of the mechanism.
- *Tank drones*: **the data says "not the same".** `RVehicleHeavyTank.TakeDamageFromEMP` is a
  289-byte script that does **not** call the NPC version; it reaches for the player and plays a
  thought (`EMPIneffectiveLine`, `PlayCommanderBark`) - the shape of an "EMP does nothing to this"
  answer, not of a stun. Temporarily-vs-permanently is UNKNOWN for both families because the
  per-class `DamageTimeEMP` default is not in any layout the repo holds.

## 3. The object graph, assembled

```
RVehicleBatmobile.VehicleWeapons @4956
  └─ Weapons.Batmobile_EMP_Burst                class RBatmobileEMP (2552 B, super RVehicleWeapon)
       ├─ ChargeParticle      @2416 → Batmobile_EMP_Burst.ChargeParticle0  [ParticleSystemComponent]
       ├─ ImpulseComponent    @2496 → Batmobile_EMP_Burst.ImpulseComponent0 [RB_RadialImpulseComponent]
       ├─ Range               @2396 = 7500.0
       ├─ DisableEnemyDuration@2400 = [2, 4, 8, 12]        ← the recovery timer
       ├─ PowerLevelChargeTime@2424 = [0.0, 0.5, 1.0, 1.5]
       ├─ EMPImpulse          @2512 = [5000.0]
       ├─ EMPVehicleImpulse   @2528 = [20000.0]
       ├─ FireParticle        @2440 = 4 items (payload not decoded)
       ├─ EMPFireSwitch       @2472 = 4 items (payload not decoded)
       ├─ FireStartEvent      @2176 → Engine.Play_Batmobile_EMP  [AkEvent, missing-object]
       └─ WeaponCoolDown      @2096 = 2.0 in the archetype (10.0 in the CDO)

target classes
  RVehicleNPC        TakeDamageFromEMP / UpdateDamageFromEMP / DamageTimeEMP /
                     bCompletelyDisabledByEMP / bSusceptibleToEMP / VehicleAsBombEMP / ParticlesEMP
  RVehicleCar        TakeDamageFromEMP → RVehicleNPC.TakeDamageFromEMP
  RVehicleFlying     TakeDamageFromEMP → RVehicleNPC.TakeDamageFromEMP
  RVehicleHeavyTank  TakeDamageFromEMP (own 289 B branch) + EMPIneffectiveLine
  RVehicleSimNPC     DisabledByEMP / SetDisabledByEMP      (cars)
  RVehicleSimFlyingNPC SetDisabledByEMP                    (flying)
```

`RVehicleNPC.ParticlesEMP` (11281, ComponentProperty) is the target-side particle hook: the
lightning that plays *on the victim* is a component on the victim, not the weapon's charge effect.
Its template is not read here and is the single most useful next decode for the visual.

## 4. The pursuit-mode EMP, for contrast

The missile (`RBatmobileEMPMissile`, `Batmobile_EMP_Missile_Launcher`) is the *other* EMP and it is
built the opposite way: a real projectile with `Projectile.Damage` 60, `MyDamageType`
`Core.RDmgType_BatmobileCannon` (not the EMP damage type), a 14-emitter rocket explosion and a
`Damage_States.FireTrail_APC` flame trail. Its `_ForCars` sibling serialises no scalar at all
(reference-only archetype) and pairs `Rocket_Explosion_Small` (9 emitters) with `FireTrail_Car`
(9). Its explosion sound is literally
`Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact` - the audio name for the same device
("immobiliser"), which is the one place the shipped data spells out the intent.

So: **battle mode = burst, no explosion, timed disable; pursuit mode = missile, explosion + flame
trail, cannon damage type.** The operator's "no explosion, no smoke, no flame" describes the burst
correctly and would be wrong for the missile.

## 5. Method (re-runnable)

Records read as-is: `Research/BatmobileGrab/{WEAPONS.md,CHAIN.json,objects.jsonl,BMSDK_OFFSETS.json,
CLASS_DEFAULTS.json,COLLISION_WHERE.md,PARTICLES.md,PARTICLES_FEATURES.md,ASSETS.md,COVERAGE.json}`.

Cooked packages were re-read with the existing readers, no new tool committed:

```bash
# class-default object, its arrays, its flags
python - <<'EOF'
import sys,os,struct,json
sys.path.insert(0,'Tools/scripts')
import upk_read as U
from grab_packages_g305 import PartialPackage
pkg=PartialPackage(r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\BmGame.upk")
d=pkg.data(46694)                      # BmGame.Default__RBatmobileEMP
tags,end,why=U.walk_tags(pkg,d,0,max_tags=8000)
for t in tags: print(t['offset'],t['type'],t.get('name'),t.get('value'),t.get('count'),t.get('floats'))
EOF
```

The class layout used to name each offset is `BMSDK_OFFSETS.json` (BmSDK-AK, MIT) restricted to the
super chain `RBatmobileEMP → RVehicleWeapon → RInventoryGadget → Inventory → Actor`; an offset with
no member was printed as `UNKNOWN@<offset>` and none of the 15 tags in 46694 was one.

Function bodies were read as `data[22:len-16]` (the layout recorded in `DAMAGE_RULES.md` §1) and
referenced exports scanned at `0x1B`/`0x1C`/`0x29`/`0x2E` token positions. Those traces are
**aligned candidates, not verified calls** (`DAMAGE_RULES.md` §3.2 makes the same distinction); the
two that carry this note's weight are the `0x1C` (`EX_FinalFunction`) hits
`RVehicleCar → RVehicleNPC.TakeDamageFromEMP` and `RVehicleFlying → RVehicleNPC.TakeDamageFromEMP`.

Reading export 158039 (the CDO's `ChargeParticle0`) raised `MemoryError` in the chunk pump, so the
component's own particle template was **not** read from BmGame.upk; the effect identity in A8 rests
on the archetype reference (`WEAPONS.md` §9) plus `PARTICLES.md`/`PARTICLES_FEATURES.md`.

## 6. UNKNOWNs, and the one file or search that closes each

| UNKNOWN | closes with |
|---|---|
| Are the target's hit points zeroed on an EMP hit ("killed")? | verified trace of `BmGame.upk` export 11526 (`RVehicleNPC.TakeDamageFromEMP`) and of `SetVehicleAsBomb`; search for `Health`/`SetHealth` refs in that body |
| Which `EMP_Burst_Stage_0N` plays at which power level? | re-walk the 4-item `FireParticle` and 4-item `EMPFireSwitch` arrays at @2440/@2472 of `Weapons.Batmobile_EMP_Burst` in `Playable_Batmobile_SF.upk` |
| What particle plays on the victim (`RVehicleNPC.ParticlesEMP`)? | decode export 11281's tag payload → object path, then `PARTICLES.json` |
| `DamageTimeEMP` shipped value per class (drone stun duration) | a BmSDK layout for `RVehicleNPC` / `RVehicleFlying` / `RVehicleHeavyTank` / `RVehicleSimFlyingNPC` added to `BMSDK_OFFSETS.json` (run `Tools/scripts/bmsdk_offsets.py` with those classes in scope), then read their `Default__*` exports |
| Is a heavy tank disabled at all, or only told "EMP ineffective"? | the object `RVehicleHeavyTank.EMPIneffectiveLine` (export 129218) tag payload, and a verified trace of export 129436 |
| Does the EMP burst apply `RDmgType_BatmobileEMP`, and with what radius? | verified trace of `RBatmobileEMP.FireEMP` (export 46666, 577 B script) for the `TakeRadiusDamage` argument list; `Range` 7500 is the only radius the object carries |
| `VulnerableToEMP`'s shipped bit | BmSDK getter for `RVehicleBatmobileBase.VulnerableToEMP` (the offsets record has no mask for it) |

No claim above is filled in from outside these sources. Where the data is silent the row says
UNKNOWN.
