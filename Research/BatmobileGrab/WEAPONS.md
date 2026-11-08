# The Batmobile's weapons: every value in the four vehicle packages

**Verdict.** The four Batmobile packages carry 62 weapon and projectile objects over 13 classes (11 gadget, 2 projectile); 1028 tags flatten to 1185 fields, 1002 of the tags are named and 26 bit-packed bools stay offset-only; 0 of 332 fields compared across the 18 multi-variant objects differ - the Joker package's distinct objects are its 5 Joker-only ones, not a retuned shared object; the 10 projectile names over 26 instances resolve 9 launcher target(s), and 1 projectile name(s) is included without one.

Checkable: `python Tools/scripts/grab_weapons.py --check` (record `WEAPONS.json`).

## 0. How to read this record

- **field** is the SDK name when one exists (`RBatmobileCannon.ImpactMomentum`), the
  stream name when the struct carried one (`HeatBarStart`, `InaccuracyVsTime`), and
  `offset 0x...` only when neither names the offset. A bool whose bits are packed with
  another bool cannot be named from an offset; the record keeps its raw bool word.
- **offset** is the byte offset in the export (hex). Nested struct children show their
  offset inside the struct; array items show the item index in the path.
- **value** is the cooked package's own number. Unreal units are centimetres for
  positions, cm/s for speeds and 16-bit angle units for rotators (65,536 = 360 degrees);
  nothing is converted here. An array item lists its decoded children in source order;
  for a curve point only `InterpMode` carries a name in the stream.
- **named_by**: `stream` = the tag carried its own name; `sdk-layout` = joined from
  `CHAIN.json`; `-` = no name exists at that offset (bit-packed bool).
- **instance** is one package's copy of an object. `Batmobile`, `MK2`, `Funhouse` and
  `Joker` are the four packages. A field marked with a per-package value differs between
  them; `-` means the field is absent from that instance.

## 1. Sources and selection

| input | rows used |
|---|---:|
| `objects.jsonl` (grab, schema 6) | 62 object records selected |
| `CHAIN.json` (`bmak_chain.py`) | the `sdk-layout` names below |
| `PARTICLES.json` (`grab_particles.py`) | particle-system emitter counts for the projectile FX |

Selection is literal: in the four vehicle packages, every object whose class starts
with `RBatmobile`, plus every `RBasicProjectile`. The `_Std_*` packages hold
materials and textures, not a vehicle, and are excluded.

## 2. Census

62 objects over 13 classes: 36 gadget objects in 11 gadget classes and 26 projectile
objects in 2 projectile classes. 1028 tags flatten to 1185 fields; 1002 tags are named, 26
bit-packed bools stay offset-only.

| class | kind | objects | names | fields | refs | resolved | missing |
|---|---|---|---|---|---|---|---|
| RBatmobileAllegianceSwitcher | gadget | 3 | 1 | 39 | 30 | 21 | 9 |
| RBatmobileBooster | gadget | 4 | 1 | 8 | 4 | 4 | 0 |
| RBatmobileCannon | gadget | 5 | 2 | 280 | 70 | 34 | 36 |
| RBatmobileEMP | gadget | 3 | 1 | 36 | 21 | 15 | 6 |
| RBatmobileEMPMissile | gadget | 3 | 1 | 63 | 33 | 18 | 15 |
| RBatmobileHeavyCannon | gadget | 4 | 2 | 165 | 48 | 41 | 7 |
| RBatmobileMissileLauncher | gadget | 3 | 1 | 48 | 33 | 27 | 6 |
| RBatmobileMissileLauncherJoker | gadget | 2 | 2 | 25 | 9 | 8 | 1 |
| RBatmobileSonar | gadget | 3 | 1 | 66 | 33 | 27 | 6 |
| RBatmobileVehicleTracker | gadget | 3 | 1 | 21 | 12 | 12 | 0 |
| RBatmobileWinch | gadget | 3 | 1 | 63 | 39 | 24 | 15 |
| RBasicProjectile | projectile | 13 | 5 | 155 | 111 | 106 | 5 |
| RBatmobileMissile | projectile | 13 | 5 | 216 | 151 | 129 | 22 |

| variant | package | objects | fields | refs |
|---|---|---|---|---|
| Batmobile | `Playable_Batmobile_SF` | 18 | 332 | 178 |
| MK2 | `Playable_BatmobileMK2_SF` | 18 | 332 | 178 |
| Funhouse | `Playable_BatmobileFunhouse_SF` | 18 | 332 | 178 |
| Joker | `Playable_BatmobileJoker_SF` | 8 | 189 | 60 |

## 3. Variant map

The same-named objects are compared field by field. A field is a *difference* when its
value (or its reference target) differs, or when it is present in one instance and not
another. References are compared by target path, not by export index, because the index
is per-package.

| class | object | instances | fields | comparisons | differing |
|---|---|---|---|---|---|
| RBatmobileAllegianceSwitcher | `Drone_Hacker` | 3 | 13 | 39 | 0 |
| RBatmobileBooster | `Batmobile_Booster` | 4 | 2 | 8 | 0 |
| RBatmobileCannon | `Batmobile_Cannon_V2` | 4 | 67 | 268 | 0 |
| RBatmobileEMP | `Batmobile_EMP_Burst` | 3 | 12 | 36 | 0 |
| RBatmobileEMPMissile | `Batmobile_EMP_Missile_Launcher` | 3 | 21 | 63 | 0 |
| RBatmobileHeavyCannon | `Batmobile_Heavy_Cannon_Primary` | 3 | 41 | 123 | 0 |
| RBatmobileMissileLauncher | `Batmobile_Missile_Launcher` | 3 | 16 | 48 | 0 |
| RBatmobileSonar | `Batmobile_Sonar` | 3 | 22 | 66 | 0 |
| RBatmobileVehicleTracker | `Vehicle_Tracker` | 3 | 7 | 21 | 0 |
| RBatmobileWinch | `Batmobile_Winch` | 3 | 21 | 63 | 0 |
| RBasicProjectile | `Batmobile_Heavy_Cannon_BodyShot_Projectile` | 3 | 9 | 27 | 0 |
| RBasicProjectile | `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` | 3 | 10 | 30 | 0 |
| RBasicProjectile | `Batmobile_Heavy_Cannon_HeadShot_Projectile` | 3 | 9 | 27 | 0 |
| RBasicProjectile | `Batmobile_Heavy_Cannon_Primary_Projectile` | 3 | 18 | 54 | 0 |
| RBatmobileMissile | `Batmobile_EMPMissile_Projectile` | 3 | 20 | 60 | 0 |
| RBatmobileMissile | `Batmobile_EMPMissile_Projectile_ForCars` | 3 | 10 | 30 | 0 |
| RBatmobileMissile | `Batmobile_Missile_Projectile` | 3 | 18 | 54 | 0 |
| RBatmobileMissile | `Batmobile_Tracker_Projectile` | 3 | 16 | 48 | 0 |

**0 of 1065 field comparisons differ.** No shared object is retuned between the base,
MK2, Funhouse and Joker packages: the four packages carry the same weapon values.
The Joker package's distinct objects are its 5 Joker-only ones, which have no
same-named counterpart and are dumped in their own sections below: `Batmobile_JokerCannon_V2`, `Batmobile_JokerHeavy_Cannon_Projectile`, `Batmobile_JokerHeavy_Cannon`, `Batmobile_JokerMissile_Launcher`, `Batmobile_JokerMissile_Projectile`.

## 4. Projectiles

The four vehicle packages carry **10** projectile archetypes over **26** instances. **9** are named by a launcher in the same 62-object selection; **1** is included without one.

The projectile's own values, its impulse component, and the particle/audio objects it references. Each row is one object name; the instances are listed because the base, MK2, Funhouse and Joker packages each carry their own copy. The G1-08 variant map found no value difference among the shared objects, so a per-package column appears only where a value actually differs.

Three absences are findings, not omissions. `Batmobile_EMPMissile_Projectile` and `Batmobile_Tracker_Projectile` serialize no `Projectile.Damage`; `Batmobile_EMPMissile_Projectile_ForCars` serializes no scalar value at all (it is a reference-only archetype); and no projectile carries `LifeSpan`/`Lifetime`. Class defaults are not claimed. The missile trail components resolve locally, but their particle template is `Engine.Batmobile_Rocket_Trail`, outside these packages, so it stays `missing-object`.

**Launcher coverage.** Every launcher reference in the 62 selected gadgets:

| projectile | class | instances | fired by |
|---|---|---|---|
| `Batmobile_EMPMissile_Projectile` | RBatmobileMissile | 3 | - (no launcher in these packages) |
| `Batmobile_EMPMissile_Projectile_ForCars` | RBatmobileMissile | 3 | `Batmobile_EMP_Missile_Launcher` via `RBatmobileEMPMissile.ProjectileForCarsArchetype`, `RPursuitModeMissileLauncher.ProjectileArchetype` (Batmobile, MK2, Funhouse) |
| `Batmobile_Heavy_Cannon_BodyShot_Projectile` | RBasicProjectile | 3 | `Batmobile_Heavy_Cannon_Primary` via `RBatmobileHeavyCannon.UpgradedBodyShotProjectileArchetype` (Batmobile, MK2, Funhouse) |
| `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` | RBasicProjectile | 3 | `Batmobile_Heavy_Cannon_Primary` via `RBatmobileHeavyCannon.BothUpgradesProjectileArchetype` (Batmobile, MK2, Funhouse) |
| `Batmobile_Heavy_Cannon_HeadShot_Projectile` | RBasicProjectile | 3 | `Batmobile_Heavy_Cannon_Primary` via `RBatmobileHeavyCannon.UpgradedHeadShotProjectileArchetype` (Batmobile, MK2, Funhouse) |
| `Batmobile_Heavy_Cannon_Primary_Projectile` | RBasicProjectile | 3 | `Batmobile_Heavy_Cannon_Primary` via `RBatmobileHeavyCannon.ProjectileArchetype` (Batmobile, MK2, Funhouse) |
| `Batmobile_JokerHeavy_Cannon_Projectile` | RBasicProjectile | 1 | `Batmobile_JokerHeavy_Cannon` via `RBatmobileHeavyCannon.ProjectileArchetype` (Joker) |
| `Batmobile_JokerMissile_Projectile` | RBatmobileMissile | 1 | `Batmobile_JokerMissile_Launcher` via `RBatmobileMissileLauncher.MissileClass` (Joker) |
| `Batmobile_Missile_Projectile` | RBatmobileMissile | 3 | `Batmobile_Missile_Launcher` via `RBatmobileMissileLauncher.MissileClass` (Batmobile, MK2, Funhouse) |
| `Batmobile_Tracker_Projectile` | RBatmobileMissile | 3 | `Vehicle_Tracker` via `RPursuitModeMissileLauncher.ProjectileArchetype` (Batmobile, MK2, Funhouse) |

`Batmobile_EMPMissile_Projectile` is included from the card's list but no `ProjectileArchetype`/`MissileClass` field in these four packages points at it; its `_ForCars` sibling is the EMP launcher's target. It is kept, marked, rather than dropped.

### `Batmobile_EMPMissile_Projectile`

3 instance(s): **Batmobile**, **MK2**, **Funhouse**. Class `RBatmobileMissile`.

| quantity | field | value |
|---|---|---|
| speed | - | absent |
| max speed | `Projectile.MaxSpeed` | 7500.0 |
| acceleration | `RBatmobileMissile.AccelRate` | 40000.0 |
| homing flag (unnamed bool) | - | absent |
| homing delay | - | absent |
| force-explode proximity distance | - | absent |
| damage | `Projectile.Damage` | 60.0 |
| turret-shot damage | - | absent |
| damage radius | `Projectile.DamageRadius` | 0.0 |
| momentum transfer | - | absent |
| damage type | `Projectile.MyDamageType` | `Core.RDmgType_BatmobileCannon` |
| lifetime | - | absent |

Absent from every instance: speed (`Projectile.Speed`); homing flag (unnamed bool) (`offset 0x0420`); homing delay (`RBatmobileMissile.HomingDelay`); force-explode proximity distance (`RBatmobileMissile.ForceExplodeProxDist`); turret-shot damage (`RBasicProjectile.TurretShotDamage`); momentum transfer (`Projectile.MomentumTransfer`); lifetime (`Projectile.LifeSpan`, `Projectile.Lifetime`, `Actor.LifeSpan`). Whether a class default supplies it is not claimed; the row records the absence.

**Impulse component** `Projectiles.Batmobile_EMPMissile_Projectile.RB_RadialImpulseComponent` (`RB_RadialImpulseComponent`), resolved from `RProjectile.ImpactRadialImpulseComponent`.

| field | offset | type | value |
|---|---|---|---|
| `offset 0x0220` | 0x0220 | FloatProperty | 1000.0 |
| `offset 0x0228` | 0x0228 | BoolProperty | true |
| `ReplacementPrimitive` | 0x013C | ObjectProperty | 0 |
| `offset 0x016C` | 0x016C | FloatProperty | 0.9753715395927429 |
| `LightingChannels` | 0x0200 | StructProperty | struct, 1 props, 31 B |

**Flight and impact FX**

| role | field | target | class | status | resolved | packages |
|---|---|---|---|---|---|---|
| explosion | `RBatmobileMissile.ExplosionTemplate` | `Rocket.Batmobil_Rocket_Explosion` | ParticleSystem | resolved | `Particles.Rocket.Batmobil_Rocket_Explosion`; 14 emitters | Batmobile, MK2, Funhouse |
| impact flame trail | `RProjectile.ImpactExplosionFlameTrail` | `Damage_States.FireTrail_APC` | ParticleSystem | resolved | `Particles.Damage_States.FireTrail_APC`; 10 emitters | Batmobile, MK2, Funhouse |
| trail | `RBasicProjectile.ProjectileTrail` | `Batmobile_EMPMissile_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_EMPMissile_Projectile.RocketTrail`; system `Engine.Batmobile_Rocket_Trail` missing-object | Batmobile, MK2, Funhouse |
| trail | `RBatmobileMissile.Trail` | `Batmobile_EMPMissile_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_EMPMissile_Projectile.RocketTrail`; system `Engine.Batmobile_Rocket_Trail` missing-object | Batmobile, MK2, Funhouse |

**AkEvents**

| field | target | class | status | resolved | packages |
|---|---|---|---|---|---|
| `RBatmobileMissile.ExlposionSound` | `Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact` | AkEvent | resolved | `Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact` | Batmobile, MK2, Funhouse |
| `RBatmobileMissile.HomingLoop` | `Engine.Play_Batmobile_ApRocket_Flight` | AkEvent | missing-object | - | Batmobile, MK2, Funhouse |
| `RBatmobileMissile.InitialLoop` | `Engine.Play_Batmobile_ApRocket_Up` | AkEvent | missing-object | - | Batmobile, MK2, Funhouse |

### `Batmobile_EMPMissile_Projectile_ForCars`

3 instance(s): **Batmobile**, **MK2**, **Funhouse**. Class `RBatmobileMissile`.

Fired by `RBatmobileEMPMissile.Batmobile_EMP_Missile_Launcher` via `RBatmobileEMPMissile.ProjectileForCarsArchetype`, `RPursuitModeMissileLauncher.ProjectileArchetype`.

| quantity | field | value |
|---|---|---|
| speed | - | absent |
| max speed | - | absent |
| acceleration | - | absent |
| homing flag (unnamed bool) | - | absent |
| homing delay | - | absent |
| force-explode proximity distance | - | absent |
| damage | - | absent |
| turret-shot damage | - | absent |
| damage radius | - | absent |
| momentum transfer | - | absent |
| damage type | - | absent |
| lifetime | - | absent |

Absent from every instance: speed (`Projectile.Speed`); max speed (`Projectile.MaxSpeed`); acceleration (`RBatmobileMissile.AccelRate`, `RBasicProjectile.InitialAcceleration`); homing flag (unnamed bool) (`offset 0x0420`); homing delay (`RBatmobileMissile.HomingDelay`); force-explode proximity distance (`RBatmobileMissile.ForceExplodeProxDist`); damage (`Projectile.Damage`); turret-shot damage (`RBasicProjectile.TurretShotDamage`); damage radius (`Projectile.DamageRadius`); momentum transfer (`Projectile.MomentumTransfer`); damage type (`Projectile.MyDamageType`); lifetime (`Projectile.LifeSpan`, `Projectile.Lifetime`, `Actor.LifeSpan`). Whether a class default supplies it is not claimed; the row records the absence.

**Impulse component** `Projectiles.Batmobile_EMPMissile_Projectile_ForCars.RB_RadialImpulseComponent` (`RB_RadialImpulseComponent`), resolved from `RProjectile.ImpactRadialImpulseComponent`.

| field | offset | type | value |
|---|---|---|---|
| `ReplacementPrimitive` | 0x013C | ObjectProperty | 0 |
| `offset 0x016C` | 0x016C | FloatProperty | 0.9298989772796631 |

**Flight and impact FX**

| role | field | target | class | status | resolved | packages |
|---|---|---|---|---|---|---|
| explosion | `RBatmobileMissile.ExplosionTemplate` | `Rocket.Batmobil_Rocket_Explosion_Small` | ParticleSystem | resolved | `Particles.Rocket.Batmobil_Rocket_Explosion_Small`; 9 emitters | Batmobile, MK2, Funhouse |
| impact flame trail | `RProjectile.ImpactExplosionFlameTrail` | `Damage_States.FireTrail_Car` | ParticleSystem | resolved | `Particles.Damage_States.FireTrail_Car`; 9 emitters | Batmobile, MK2, Funhouse |
| trail | `RBasicProjectile.ProjectileTrail` | `Batmobile_EMPMissile_Projectile_ForCars.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_EMPMissile_Projectile_ForCars.RocketTrail`; no particle template | Batmobile, MK2, Funhouse |
| trail | `RBatmobileMissile.Trail` | `Batmobile_EMPMissile_Projectile_ForCars.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_EMPMissile_Projectile_ForCars.RocketTrail`; no particle template | Batmobile, MK2, Funhouse |

### `Batmobile_Heavy_Cannon_BodyShot_Projectile`

3 instance(s): **Batmobile**, **MK2**, **Funhouse**. Class `RBasicProjectile`.

Fired by `RBatmobileHeavyCannon.Batmobile_Heavy_Cannon_Primary` via `RBatmobileHeavyCannon.UpgradedBodyShotProjectileArchetype`.

| quantity | field | value |
|---|---|---|
| speed | - | absent |
| max speed | - | absent |
| acceleration | - | absent |
| homing flag (unnamed bool) | - | absent |
| homing delay | - | absent |
| force-explode proximity distance | - | absent |
| damage | `Projectile.Damage` | 75.0 |
| turret-shot damage | - | absent |
| damage radius | - | absent |
| momentum transfer | - | absent |
| damage type | - | absent |
| lifetime | - | absent |

Absent from every instance: speed (`Projectile.Speed`); max speed (`Projectile.MaxSpeed`); acceleration (`RBatmobileMissile.AccelRate`, `RBasicProjectile.InitialAcceleration`); homing flag (unnamed bool) (`offset 0x0420`); homing delay (`RBatmobileMissile.HomingDelay`); force-explode proximity distance (`RBatmobileMissile.ForceExplodeProxDist`); turret-shot damage (`RBasicProjectile.TurretShotDamage`); damage radius (`Projectile.DamageRadius`); momentum transfer (`Projectile.MomentumTransfer`); damage type (`Projectile.MyDamageType`); lifetime (`Projectile.LifeSpan`, `Projectile.Lifetime`, `Actor.LifeSpan`). Whether a class default supplies it is not claimed; the row records the absence.

**Impulse component** `Projectiles.Batmobile_Heavy_Cannon_BodyShot_Projectile.ImpulseComponent0` (`RB_RadialImpulseComponent`), resolved from `RProjectile.ImpactRadialImpulseComponent`.

| field | offset | type | value |
|---|---|---|---|
| `ReplacementPrimitive` | 0x013C | ObjectProperty | 0 |
| `offset 0x016C` | 0x016C | FloatProperty | 0.8149052262306213 |

**Flight and impact FX**

| role | field | target | class | status | resolved | packages |
|---|---|---|---|---|---|---|
| impact | `RBasicProjectile.ImpactExplosion` | `Cannon_Upgrades.Impact_Body_UPGR` | ParticleSystem | resolved | `Particles.Cannon_Upgrades.Impact_Body_UPGR`; 14 emitters | Batmobile, MK2, Funhouse |
| muzzle flash | `RBasicProjectile.MuzzleFlashOverride` | `Cannon_Upgrades.Muzzle_Body_UPGR` | ParticleSystem | resolved | `Particles.Cannon_Upgrades.Muzzle_Body_UPGR`; 7 emitters | Batmobile, MK2, Funhouse |
| trail | `RBasicProjectile.ProjectileTrail` | `Batmobile_Heavy_Cannon_BodyShot_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_BodyShot_Projectile.RocketTrail`; system `Particles.Cannon_Upgrades.Trail_Body_UPGR` (4 emitters) | Batmobile, MK2, Funhouse |

### `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile`

3 instance(s): **Batmobile**, **MK2**, **Funhouse**. Class `RBasicProjectile`.

Fired by `RBatmobileHeavyCannon.Batmobile_Heavy_Cannon_Primary` via `RBatmobileHeavyCannon.BothUpgradesProjectileArchetype`.

| quantity | field | value |
|---|---|---|
| speed | - | absent |
| max speed | - | absent |
| acceleration | - | absent |
| homing flag (unnamed bool) | - | absent |
| homing delay | - | absent |
| force-explode proximity distance | - | absent |
| damage | `Projectile.Damage` | 75.0 |
| turret-shot damage | `RBasicProjectile.TurretShotDamage` | 110 |
| damage radius | - | absent |
| momentum transfer | - | absent |
| damage type | - | absent |
| lifetime | - | absent |

Absent from every instance: speed (`Projectile.Speed`); max speed (`Projectile.MaxSpeed`); acceleration (`RBatmobileMissile.AccelRate`, `RBasicProjectile.InitialAcceleration`); homing flag (unnamed bool) (`offset 0x0420`); homing delay (`RBatmobileMissile.HomingDelay`); force-explode proximity distance (`RBatmobileMissile.ForceExplodeProxDist`); damage radius (`Projectile.DamageRadius`); momentum transfer (`Projectile.MomentumTransfer`); damage type (`Projectile.MyDamageType`); lifetime (`Projectile.LifeSpan`, `Projectile.Lifetime`, `Actor.LifeSpan`). Whether a class default supplies it is not claimed; the row records the absence.

**Impulse component** `Projectiles.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.ImpulseComponent0` (`RB_RadialImpulseComponent`), resolved from `RProjectile.ImpactRadialImpulseComponent`.

| field | offset | type | value |
|---|---|---|---|
| `ReplacementPrimitive` | 0x013C | ObjectProperty | 0 |
| `offset 0x016C` | 0x016C | FloatProperty | 0.5829950571060181 |

**Flight and impact FX**

| role | field | target | class | status | resolved | packages |
|---|---|---|---|---|---|---|
| impact | `RBasicProjectile.ImpactExplosion` | `Cannon_Upgrades.Impact_Full_UPGR` | ParticleSystem | resolved | `Particles.Cannon_Upgrades.Impact_Full_UPGR`; 16 emitters | Batmobile, MK2, Funhouse |
| muzzle flash | `RBasicProjectile.MuzzleFlashOverride` | `Cannon_Upgrades.Muzzle_Full_UPGR` | ParticleSystem | resolved | `Particles.Cannon_Upgrades.Muzzle_Full_UPGR`; 9 emitters | Batmobile, MK2, Funhouse |
| trail | `RBasicProjectile.ProjectileTrail` | `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.RocketTrail`; system `Particles.Cannon_Upgrades.Trail_Full_UPGR` (4 emitters) | Batmobile, MK2, Funhouse |

### `Batmobile_Heavy_Cannon_HeadShot_Projectile`

3 instance(s): **Batmobile**, **MK2**, **Funhouse**. Class `RBasicProjectile`.

Fired by `RBatmobileHeavyCannon.Batmobile_Heavy_Cannon_Primary` via `RBatmobileHeavyCannon.UpgradedHeadShotProjectileArchetype`.

| quantity | field | value |
|---|---|---|
| speed | - | absent |
| max speed | - | absent |
| acceleration | - | absent |
| homing flag (unnamed bool) | - | absent |
| homing delay | - | absent |
| force-explode proximity distance | - | absent |
| damage | - | absent |
| turret-shot damage | `RBasicProjectile.TurretShotDamage` | 110 |
| damage radius | - | absent |
| momentum transfer | - | absent |
| damage type | - | absent |
| lifetime | - | absent |

Absent from every instance: speed (`Projectile.Speed`); max speed (`Projectile.MaxSpeed`); acceleration (`RBatmobileMissile.AccelRate`, `RBasicProjectile.InitialAcceleration`); homing flag (unnamed bool) (`offset 0x0420`); homing delay (`RBatmobileMissile.HomingDelay`); force-explode proximity distance (`RBatmobileMissile.ForceExplodeProxDist`); damage (`Projectile.Damage`); damage radius (`Projectile.DamageRadius`); momentum transfer (`Projectile.MomentumTransfer`); damage type (`Projectile.MyDamageType`); lifetime (`Projectile.LifeSpan`, `Projectile.Lifetime`, `Actor.LifeSpan`). Whether a class default supplies it is not claimed; the row records the absence.

**Impulse component** `Projectiles.Batmobile_Heavy_Cannon_HeadShot_Projectile.ImpulseComponent0` (`RB_RadialImpulseComponent`), resolved from `RProjectile.ImpactRadialImpulseComponent`.

| field | offset | type | value |
|---|---|---|---|
| `ReplacementPrimitive` | 0x013C | ObjectProperty | 0 |
| `offset 0x016C` | 0x016C | FloatProperty | 0.3268532454967499 |

**Flight and impact FX**

| role | field | target | class | status | resolved | packages |
|---|---|---|---|---|---|---|
| impact | `RBasicProjectile.ImpactExplosion` | `Cannon_Upgrades.Impact_Head_UPGR` | ParticleSystem | resolved | `Particles.Cannon_Upgrades.Impact_Head_UPGR`; 14 emitters | Batmobile, MK2, Funhouse |
| muzzle flash | `RBasicProjectile.MuzzleFlashOverride` | `Cannon_Upgrades.Muzzle_Head_UPGR` | ParticleSystem | resolved | `Particles.Cannon_Upgrades.Muzzle_Head_UPGR`; 7 emitters | Batmobile, MK2, Funhouse |
| trail | `RBasicProjectile.ProjectileTrail` | `Batmobile_Heavy_Cannon_HeadShot_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_HeadShot_Projectile.RocketTrail`; system `Particles.Cannon_Upgrades.Trail_Head_UPGR` (3 emitters) | Batmobile, MK2, Funhouse |

### `Batmobile_Heavy_Cannon_Primary_Projectile`

3 instance(s): **Batmobile**, **MK2**, **Funhouse**. Class `RBasicProjectile`.

Fired by `RBatmobileHeavyCannon.Batmobile_Heavy_Cannon_Primary` via `RBatmobileHeavyCannon.ProjectileArchetype`.

| quantity | field | value |
|---|---|---|
| speed | `Projectile.Speed` | 40000.0 |
| max speed | `Projectile.MaxSpeed` | 48000.0 |
| acceleration | `RBasicProjectile.InitialAcceleration` | [0.0, 0.0, -1000.0] |
| homing flag (unnamed bool) | - | absent |
| homing delay | - | absent |
| force-explode proximity distance | - | absent |
| damage | `Projectile.Damage` | 50.0 |
| turret-shot damage | `RBasicProjectile.TurretShotDamage` | 75 |
| damage radius | `Projectile.DamageRadius` | 0.0 |
| momentum transfer | `Projectile.MomentumTransfer` | 66666.671875 |
| damage type | `Projectile.MyDamageType` | `Core.RDmgType_BatmobileCannon` |
| lifetime | - | absent |

Absent from every instance: homing flag (unnamed bool) (`offset 0x0420`); homing delay (`RBatmobileMissile.HomingDelay`); force-explode proximity distance (`RBatmobileMissile.ForceExplodeProxDist`); lifetime (`Projectile.LifeSpan`, `Projectile.Lifetime`, `Actor.LifeSpan`). Whether a class default supplies it is not claimed; the row records the absence.

**Impulse component** `Projectiles.Batmobile_Heavy_Cannon_Primary_Projectile.ImpulseComponent0` (`RB_RadialImpulseComponent`), resolved from `RProjectile.ImpactRadialImpulseComponent`.

| field | offset | type | value |
|---|---|---|---|
| `ImpulseFalloff` | 0x021C | ByteProperty | "RIF_Constant" |
| `offset 0x0220` | 0x0220 | FloatProperty | 15000.0 |
| `offset 0x0234` | 0x0234 | ObjectNCRProperty | `Core.RDmgType_Explosion` |
| `ReplacementPrimitive` | 0x013C | ObjectProperty | 0 |
| `offset 0x016C` | 0x016C | FloatProperty | 0.2468947470188141 |

**Flight and impact FX**

| role | field | target | class | status | resolved | packages |
|---|---|---|---|---|---|---|
| impact | `RBasicProjectile.ImpactExplosion` | `Particles.Batmobile_HeavyCannon_Impact` | ParticleSystem | resolved | `VFX_Batmobile.Particles.Batmobile_HeavyCannon_Impact`; 8 emitters | Batmobile, MK2, Funhouse |
| pass-through effect | `RBasicProjectile.PassThroughDestructibleEffect` | `Particles.Batmobile_HeavyCannon_Impact` | ParticleSystem | resolved | `VFX_Batmobile.Particles.Batmobile_HeavyCannon_Impact`; 5 emitters | Batmobile, MK2, Funhouse |
| trail | `RBasicProjectile.ProjectileTrail` | `Batmobile_Heavy_Cannon_Primary_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_Primary_Projectile.RocketTrail`; system `Particles.Rocket.Batmobile_CanonTrail` (2 emitters) | Batmobile, MK2, Funhouse |

**AkEvents**

| field | target | class | status | resolved | packages |
|---|---|---|---|---|---|
| `RBasicProjectile.ImpactExplosionSound` | `Ww_VFX_Tank_Explosion.Play_Batmobile_HeavyCannon_Explosion` | AkEvent | resolved | `Ww_VFX_Tank_Explosion.Play_Batmobile_HeavyCannon_Explosion` | Batmobile, MK2, Funhouse |

### `Batmobile_JokerHeavy_Cannon_Projectile`

1 instance(s): **Joker**. Class `RBasicProjectile`.

Fired by `RBatmobileHeavyCannon.Batmobile_JokerHeavy_Cannon` via `RBatmobileHeavyCannon.ProjectileArchetype`.

| quantity | field | value |
|---|---|---|
| speed | `Projectile.Speed` | 10000.0 |
| max speed | `Projectile.MaxSpeed` | 12000.0 |
| acceleration | `RBasicProjectile.InitialAcceleration` | [0.0, 0.0, -1000.0] |
| homing flag (unnamed bool) | - | absent |
| homing delay | - | absent |
| force-explode proximity distance | - | absent |
| damage | `Projectile.Damage` | 250.0 |
| turret-shot damage | - | absent |
| damage radius | `Projectile.DamageRadius` | 350.0 |
| momentum transfer | `Projectile.MomentumTransfer` | 70000.0 |
| damage type | `Projectile.MyDamageType` | `Core.RDmgType_BatmobileCannon` |
| lifetime | - | absent |

Absent from every instance: homing flag (unnamed bool) (`offset 0x0420`); homing delay (`RBatmobileMissile.HomingDelay`); force-explode proximity distance (`RBatmobileMissile.ForceExplodeProxDist`); turret-shot damage (`RBasicProjectile.TurretShotDamage`); lifetime (`Projectile.LifeSpan`, `Projectile.Lifetime`, `Actor.LifeSpan`). Whether a class default supplies it is not claimed; the row records the absence.

**Impulse component** `Projectiles.Batmobile_JokerHeavy_Cannon_Projectile.ImpulseComponent0` (`RB_RadialImpulseComponent`), resolved from `RProjectile.ImpactRadialImpulseComponent`.

| field | offset | type | value |
|---|---|---|---|
| `ImpulseFalloff` | 0x021C | ByteProperty | "RIF_Constant" |
| `offset 0x0220` | 0x0220 | FloatProperty | 500.0 |
| `ReplacementPrimitive` | 0x013C | ObjectProperty | 0 |
| `offset 0x016C` | 0x016C | FloatProperty | 0.09024323523044586 |
| `offset 0x0190` | 0x0190 | VectorProperty | [0.0, 0.0, -100.0] |

**Flight and impact FX**

| role | field | target | class | status | resolved | packages |
|---|---|---|---|---|---|---|
| impact | `RBasicProjectile.ImpactExplosion` | `Engine.Batmobile_rocketExplosion_TEMP` | ParticleSystem | missing-object | - | Joker |
| trail | `RBasicProjectile.ProjectileTrail` | `Batmobile_JokerHeavy_Cannon_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_JokerHeavy_Cannon_Projectile.RocketTrail`; system `Particles.Rocket.Batmobile_CanonTrail` (2 emitters) | Joker |

**AkEvents**

| field | target | class | status | resolved | packages |
|---|---|---|---|---|---|
| `RBasicProjectile.ImpactExplosionSound` | `Ww_VFX_Tank_Explosion.Play_Batmobile_HeavyCannon_Explosion` | AkEvent | resolved | `Ww_VFX_Tank_Explosion.Play_Batmobile_HeavyCannon_Explosion` | Joker |

### `Batmobile_JokerMissile_Projectile`

1 instance(s): **Joker**. Class `RBatmobileMissile`.

Fired by `RBatmobileMissileLauncherJoker.Batmobile_JokerMissile_Launcher` via `RBatmobileMissileLauncher.MissileClass`.

| quantity | field | value |
|---|---|---|
| speed | `Projectile.Speed` | 500.0 |
| max speed | `Projectile.MaxSpeed` | 1000.0 |
| acceleration | `RBatmobileMissile.AccelRate` | 8000.0 |
| homing flag (unnamed bool) | `offset 0x0420` | true |
| homing delay | - | absent |
| force-explode proximity distance | `RBatmobileMissile.ForceExplodeProxDist` | 100.0 |
| damage | `Projectile.Damage` | 250.0 |
| turret-shot damage | - | absent |
| damage radius | `Projectile.DamageRadius` | 300.0 |
| momentum transfer | `Projectile.MomentumTransfer` | 25000.0 |
| damage type | `Projectile.MyDamageType` | `Core.RDmgType_BatmobileMissileBarrage` |
| lifetime | - | absent |

Absent from every instance: homing delay (`RBatmobileMissile.HomingDelay`); turret-shot damage (`RBasicProjectile.TurretShotDamage`); lifetime (`Projectile.LifeSpan`, `Projectile.Lifetime`, `Actor.LifeSpan`). Whether a class default supplies it is not claimed; the row records the absence.

**Impulse component** `Projectiles.Batmobile_JokerMissile_Projectile.ImpulseComponent0` (`RB_RadialImpulseComponent`), resolved from `RProjectile.ImpactRadialImpulseComponent`.

| field | offset | type | value |
|---|---|---|---|
| `ReplacementPrimitive` | 0x013C | ObjectProperty | 0 |
| `offset 0x016C` | 0x016C | FloatProperty | 0.5089572072029114 |

**Flight and impact FX**

| role | field | target | class | status | resolved | packages |
|---|---|---|---|---|---|---|
| explosion | `RBatmobileMissile.ExplosionTemplate` | `Rocket.Batmobil_Rocket_Explosion` | ParticleSystem | resolved | `Particles.Rocket.Batmobil_Rocket_Explosion`; 14 emitters | Joker |
| trail | `RBasicProjectile.ProjectileTrail` | `Batmobile_JokerMissile_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_JokerMissile_Projectile.RocketTrail`; system `Particles.Rocket.Batmobile_JokersRocket_Trail` (4 emitters) | Joker |
| trail | `RBatmobileMissile.Trail` | `Batmobile_JokerMissile_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_JokerMissile_Projectile.RocketTrail`; system `Particles.Rocket.Batmobile_JokersRocket_Trail` (4 emitters) | Joker |

**AkEvents**

| field | target | class | status | resolved | packages |
|---|---|---|---|---|---|
| `RBatmobileMissile.ExlposionSound` | `Engine.Play_Explosion_3D` | AkEvent | missing-object | - | Joker |
| `RBatmobileMissile.HomingLoop` | `Engine.Play_Batmobile_ApRocket_Flight` | AkEvent | missing-object | - | Joker |
| `RBatmobileMissile.InitialLoop` | `Engine.Play_Batmobile_ApRocket_Up` | AkEvent | missing-object | - | Joker |

### `Batmobile_Missile_Projectile`

3 instance(s): **Batmobile**, **MK2**, **Funhouse**. Class `RBatmobileMissile`.

Fired by `RBatmobileMissileLauncher.Batmobile_Missile_Launcher` via `RBatmobileMissileLauncher.MissileClass`.

| quantity | field | value |
|---|---|---|
| speed | - | absent |
| max speed | - | absent |
| acceleration | - | absent |
| homing flag (unnamed bool) | - | absent |
| homing delay | - | absent |
| force-explode proximity distance | - | absent |
| damage | `Projectile.Damage` | 250.0 |
| turret-shot damage | - | absent |
| damage radius | `Projectile.DamageRadius` | 0.0 |
| momentum transfer | `Projectile.MomentumTransfer` | 25000.0 |
| damage type | `Projectile.MyDamageType` | `Core.RDmgType_BatmobileMissileBarrage` |
| lifetime | - | absent |

Absent from every instance: speed (`Projectile.Speed`); max speed (`Projectile.MaxSpeed`); acceleration (`RBatmobileMissile.AccelRate`, `RBasicProjectile.InitialAcceleration`); homing flag (unnamed bool) (`offset 0x0420`); homing delay (`RBatmobileMissile.HomingDelay`); force-explode proximity distance (`RBatmobileMissile.ForceExplodeProxDist`); turret-shot damage (`RBasicProjectile.TurretShotDamage`); lifetime (`Projectile.LifeSpan`, `Projectile.Lifetime`, `Actor.LifeSpan`). Whether a class default supplies it is not claimed; the row records the absence.

**Impulse component** `Projectiles.Batmobile_Missile_Projectile.ImpulseComponent0` (`RB_RadialImpulseComponent`), resolved from `RProjectile.ImpactRadialImpulseComponent`.

| field | offset | type | value |
|---|---|---|---|
| `ReplacementPrimitive` | 0x013C | ObjectProperty | 0 |
| `offset 0x016C` | 0x016C | FloatProperty | 0.6685994863510132 |

**Flight and impact FX**

| role | field | target | class | status | resolved | packages |
|---|---|---|---|---|---|---|
| explosion | `RBatmobileMissile.ExplosionTemplate` | `Rocket.Batmobil_Rocket_Explosion` | ParticleSystem | resolved | `Particles.Rocket.Batmobil_Rocket_Explosion`; 14 emitters | Batmobile, MK2, Funhouse |
| trail | `RBasicProjectile.ProjectileTrail` | `Batmobile_Missile_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_Missile_Projectile.RocketTrail`; system `Engine.Batmobile_Rocket_Trail` missing-object | Batmobile, MK2, Funhouse |
| trail | `RBatmobileMissile.Trail` | `Batmobile_Missile_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_Missile_Projectile.RocketTrail`; system `Engine.Batmobile_Rocket_Trail` missing-object | Batmobile, MK2, Funhouse |

**AkEvents**

| field | target | class | status | resolved | packages |
|---|---|---|---|---|---|
| `RBatmobileMissile.ExlposionSound` | `Engine.Play_Explosion_3D` | AkEvent | missing-object | - | Batmobile, MK2, Funhouse |
| `RBatmobileMissile.HomingLoopOff` | `Ww_VEH_Tank_Missiles.Stop_Batmobile_RocketTails` | AkEvent | resolved | `Ww_VEH_Tank_Missiles.Stop_Batmobile_RocketTails` | Batmobile, MK2, Funhouse |
| `RBatmobileMissile.HomingLoopOn` | `Engine.Play_Batmobile_ApRocket_Flight` | AkEvent | missing-object | - | Batmobile, MK2, Funhouse |
| `RBatmobileMissile.InitialLoopOn` | `Ww_VEH_Tank_Missiles.Play_Batmobile_RocketTails` | AkEvent | resolved | `Ww_VEH_Tank_Missiles.Play_Batmobile_RocketTails` | Batmobile, MK2, Funhouse |

### `Batmobile_Tracker_Projectile`

3 instance(s): **Batmobile**, **MK2**, **Funhouse**. Class `RBatmobileMissile`.

Fired by `RBatmobileVehicleTracker.Vehicle_Tracker` via `RPursuitModeMissileLauncher.ProjectileArchetype`.

| quantity | field | value |
|---|---|---|
| speed | - | absent |
| max speed | `Projectile.MaxSpeed` | 20000.0 |
| acceleration | `RBatmobileMissile.AccelRate` | 30000.0 |
| homing flag (unnamed bool) | `offset 0x0420` | true |
| homing delay | `RBatmobileMissile.HomingDelay` | 0.20000000298023224 |
| force-explode proximity distance | - | absent |
| damage | - | absent |
| turret-shot damage | - | absent |
| damage radius | `Projectile.DamageRadius` | 0.0 |
| momentum transfer | `Projectile.MomentumTransfer` | 500.0 |
| damage type | `Projectile.MyDamageType` | null (value 0) |
| lifetime | - | absent |

Absent from every instance: speed (`Projectile.Speed`); force-explode proximity distance (`RBatmobileMissile.ForceExplodeProxDist`); damage (`Projectile.Damage`); turret-shot damage (`RBasicProjectile.TurretShotDamage`); lifetime (`Projectile.LifeSpan`, `Projectile.Lifetime`, `Actor.LifeSpan`). Whether a class default supplies it is not claimed; the row records the absence.

**Impulse component** `Projectiles.Batmobile_Tracker_Projectile.ImpulseComponent0` (`RB_RadialImpulseComponent`), resolved from `RProjectile.ImpactRadialImpulseComponent`.

| field | offset | type | value |
|---|---|---|---|
| `ReplacementPrimitive` | 0x013C | ObjectProperty | 0 |
| `offset 0x016C` | 0x016C | FloatProperty | 0.40815454721450806 |

**Flight and impact FX**

| role | field | target | class | status | resolved | packages |
|---|---|---|---|---|---|---|
| trail | `RBasicProjectile.ProjectileTrail` | `Batmobile_Tracker_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_Tracker_Projectile.RocketTrail`; system `Engine.Batmobile_Rocket_Trail` missing-object | Batmobile, MK2, Funhouse |
| trail | `RBatmobileMissile.Trail` | `Batmobile_Tracker_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_Tracker_Projectile.RocketTrail`; system `Engine.Batmobile_Rocket_Trail` missing-object | Batmobile, MK2, Funhouse |

## 5. The card's quantities

Every field path that matches a quantity the G1-08 card names. A path can appear under
more than one quantity; the list is the index, not a second set of values.

- **fire rate / cooldown** (5): `RBatmobileCannon.ComboFiringInterval`, `RBatmobileCannon.RiotSuppressorFiringInterval`, `RBatmobileMissileLauncher.FireInterval`, `RVehicleWeapon.FiringInterval`, `RVehicleWeapon.WeaponCoolDown`
- **damage** (6): `Projectile.Damage`, `Projectile.DamageRadius`, `RBasicProjectile.TurretShotDamage`, `RBatmobileCannon.ChainGunDamage`, `RBatmobileCannon.UpgradedDamage`, `RBatmobileHeavyCannon.ChargeMaxDamageRadius`
- **damage / lethal radius** (3): `Projectile.DamageRadius`, `RBatmobileHeavyCannon.ChargeMaxDamageRadius`, `RVehicleWeapon.LethalRadius`
- **range** (3): `RBatmobileCannon.RiotSuppressorRange`, `RBatmobileMissileLauncher.LockOnRange`, `RVehicleWeapon.LethalRange`
- **projectile archetype** (6): `RBatmobileHeavyCannon.BothUpgradesProjectileArchetype`, `RBatmobileHeavyCannon.ProjectileArchetype`, `RBatmobileHeavyCannon.UpgradedBodyShotProjectileArchetype`, `RBatmobileHeavyCannon.UpgradedHeadShotProjectileArchetype`, `RBatmobileMissileLauncher.MissileClass`, `RPursuitModeMissileLauncher.ProjectileArchetype`
- **speed / acceleration** (5): `Projectile.MaxSpeed`, `Projectile.Speed`, `RBasicProjectile.InitialAcceleration`, `RBatmobileCannon.ChainGunMaxSpinSpeed`, `RBatmobileMissile.AccelRate`
- **projectile lifetime** (0): no field in these objects carries this name.
- **homing / flight** (5): `RBatmobileMissile.ForceExplodeProxDist`, `RBatmobileMissile.HomingDelay`, `RBatmobileMissile.HomingLoop`, `RBatmobileMissile.HomingLoopOff`, `RBatmobileMissile.HomingLoopOn`
- **heat bar** (4): `HeatBarSize`, `HeatBarStart`, `RBatmobileCannon.HeatUpPerSecond`, `RBatmobileCannon.OverheatOffValue`
- **inaccuracy-vs-time** (4): `InaccuracyVsTime`, `InaccuracyVsTime.Points`, `InaccuracyVsTimeUpgrade`, `InaccuracyVsTimeUpgrade.Points`
- **inaccuracy-vs-heat** (0): no field in these objects carries this name.
- **charge** (2): `ChargingScreenShake`, `RBatmobileHeavyCannon.ChargeUpTime`
- **salvo / targets** (4): `MaxTargetsPerLevel`, `RBatmobileMissileLauncher.MaxTargets`, `RBatmobileMissileLauncher.MissileNumberParameter`, `RBatmobileMissileLauncherJoker.NumFakeTargetReps`
- **launch sockets** (2): `MissileLaunchSockets`, `MissileSockets`
- **lock time** (4): `RBatmobileEMPMissile.CivilianMissileLockOnDuration`, `RBatmobileEMPMissile.MissileLockOnDuration`, `RBatmobileHeavyCannon.LockOnTimeMax`, `RBatmobileHeavyCannon.LockOnTimeMin`
- **lock angle** (3): `RBatmobileCannon.RiotSuppressorLockOnAngle`, `RBatmobileHeavyCannon.LockOnAngle`, `RBatmobileMissileLauncher.LockOnAngle`
- **impulse / momentum** (6): `Projectile.MomentumTransfer`, `RBatmobileCannon.ImpactMomentum`, `RBatmobileCannon.RecoilImpulse`, `RBatmobileEMP.ImpulseComponent`, `RBatmobileHeavyCannon.RecoilImpulse`, `RProjectile.ImpactRadialImpulseComponent`
- **screen shakes** (5): `BlastScreenShake`, `ChainGunScreenShake`, `ChargingScreenShake`, `FireScreenShake`, `RiotSuppressorFireScreenShake`
- **bones to hide** (1): `BonesToHideWhenNotPresent`
- **mesh / trail** (5): `RBasicProjectile.ProjectileMesh`, `RBasicProjectile.ProjectileTrail`, `RBatmobileMissile.Mesh`, `RBatmobileMissile.Trail`, `RInventoryGadget.Mesh`
- **fire / impact FX** (7): `RBasicProjectile.ImpactExplosion`, `RBasicProjectile.ImpactExplosionSound`, `RBasicProjectile.MuzzleFlashOverride`, `RBatmobileHeavyCannon.FireFX`, `RBatmobileMissile.ExplosionTemplate`, `RBatmobileMissileLauncher.FireFX`, `RProjectile.ImpactExplosionFlameTrail`
- **audio** (34): `RBasicProjectile.ImpactExplosionSound`, `RBatmobileAllegianceSwitcher.BeamPositionalSound`, `RBatmobileAllegianceSwitcher.HackingSound`, `RBatmobileAllegianceSwitcher.SucessfullHackSound`, `RBatmobileCannon.ChainGunCooledSound`, `RBatmobileCannon.ChainGunOverheatSound`, `RBatmobileCannon.ComboFireLoopingEvent`, `RBatmobileCannon.EnterComboSound`, `RBatmobileCannon.ExitComboSound`, `RBatmobileCannon.RiotSuppressorHitSound`, `RBatmobileCannon.RiotSuppressorIndividualFireEvent`, `RBatmobileEMPMissile.UntagWarningEvent`, `RBatmobileHeavyCannon.FireSound`, `RBatmobileMissile.ExlposionSound`, `RBatmobileMissileLauncher.LockOnSound`, `RBatmobileSonar.BasicScanSound`, `RBatmobileSonar.BlastSound`, `RBatmobileSonar.ChargeStartSound`, `RBatmobileSonar.ChargeStopSound`, `RBatmobileSonar.ScanSound`, `RBatmobileSonar.ScannerOffSound`, `RBatmobileSonar.ScannerOnSound`, `RBatmobileWinch.FireSound`, `RBatmobileWinch.ImpactSound`, `RBatmobileWinch.ReleaseSound`, `RBatmobileWinch.TensionStartSound`, `RBatmobileWinch.WinchLoopingSound`, `RVehicleWeapon.FireLoopingEvent`, `RVehicleWeapon.FireStartEvent`, `RVehicleWeapon.IndividualFireEvent`, `RVehicleWeapon.LockOnBeepSound`, `RVehicleWeapon.LockedOnSound`, `RVehicleWeapon.ReloadSound`, `RVehicleWeapon.WeaponHitEvent`

The 2 zero row(s) are findings, not omissions: projectile lifetime, inaccuracy-vs-heat are not serialized in these 62
objects. Whether the engine holds a class default for them is not claimed here.

## 6. `RBatmobileAllegianceSwitcher` - gadget

3 objects over 3 packages, 1 object name(s): 39 field rows (all instances), 30
references (21 resolved, 9 `missing-object`).

| object | instances | variants | field rows | refs | missing |
|---|---|---|---|---|---|
| `Drone_Hacker` | 3 | Batmobile, MK2, Funhouse | 39 | 30 | 9 |

### `Drone_Hacker`

3 instances: **Batmobile**, **MK2**, **Funhouse**.

All 13 fields are identical in every instance (39 comparisons, 0 differences).

| field | offset | type | value |
|---|---|---|---|
| `RBatmobileAllegianceSwitcher.BatmobileHackerEffect` | 0x0968 | ObjectNCRProperty | `Particles.DroneHacker_Beam` |
| `RBatmobileAllegianceSwitcher.SuccessfulHackEffect` | 0x0970 | ObjectNCRProperty | `Particles.DroneHacker_Success` |
| `RBatmobileAllegianceSwitcher.BatmobileHackerEffectHvyTank` | 0x0978 | ObjectNCRProperty | `Particles.CobraHacker_Beam` |
| `RBatmobileAllegianceSwitcher.SuccessfulHackEffectHvyTank` | 0x0980 | ObjectNCRProperty | `Particles.CobraHacker_Success` |
| `RBatmobileAllegianceSwitcher.DroneHackerMaterial` | 0x0988 | ObjectNCRProperty | `Materials.DroneHacker_Beam_INST` |
| `RBatmobileAllegianceSwitcher.SucessfullHackSound` | 0x0990 | ObjectNCRProperty | `Engine.Play_Batmobile_DroneHacker_Hacked` |
| `RBatmobileAllegianceSwitcher.HackingSound` | 0x0998 | ObjectNCRProperty | `Engine.Play_Batmobile_DroneHacker_Fire` |
| `RBatmobileAllegianceSwitcher.BeamPositionalSound` | 0x09A0 | ObjectNCRProperty | `Engine.Play_Batmobile_DroneHacker_Loop` |
| `RBatmobileAllegianceSwitcher.NotEnoughEnergyThought` | 0x09A8 | ObjectNCRProperty | `Lines.Char_Batman_Misc_Cobra_Barrage_Energy_B_01` |
| `HackerEffect` | 0x09B0 | ArrayProperty | array, 6 items, 4 B each - payload not decoded |
| `RVehicleWeapon.WeaponCoolDown` | 0x0830 | FloatProperty | 1.0 |
| `RInventoryGadget.Mesh` | 0x0318 | ObjectNCRProperty | `Drone_Hacker.GadgetMesh` |
| `Actor.Tag` | 0x0168 | NameProperty | "RBatmobileAllegianceSwitcher" |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RBatmobileAllegianceSwitcher.BatmobileHackerEffect` | `Particles.DroneHacker_Beam` | ParticleSystem | resolved | `VFX_Batmobile.Particles.DroneHacker_Beam` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileAllegianceSwitcher.SuccessfulHackEffect` | `Particles.DroneHacker_Success` | ParticleSystem | resolved | `VFX_Batmobile.Particles.DroneHacker_Success` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileAllegianceSwitcher.BatmobileHackerEffectHvyTank` | `Particles.CobraHacker_Beam` | ParticleSystem | resolved | `VFX_Batmobile.Particles.CobraHacker_Beam` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileAllegianceSwitcher.SuccessfulHackEffectHvyTank` | `Particles.CobraHacker_Success` | ParticleSystem | resolved | `VFX_Batmobile.Particles.CobraHacker_Success` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileAllegianceSwitcher.DroneHackerMaterial` | `Materials.DroneHacker_Beam_INST` | MaterialInstanceConstant | resolved | `VFX_Batmobile.Materials.DroneHacker_Beam_INST` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileAllegianceSwitcher.SucessfullHackSound` | `Engine.Play_Batmobile_DroneHacker_Hacked` | AkEvent | missing-object | - |
| `RBatmobileAllegianceSwitcher.HackingSound` | `Engine.Play_Batmobile_DroneHacker_Fire` | AkEvent | missing-object | - |
| `RBatmobileAllegianceSwitcher.BeamPositionalSound` | `Engine.Play_Batmobile_DroneHacker_Loop` | AkEvent | missing-object | - |
| `RBatmobileAllegianceSwitcher.NotEnoughEnergyThought` | `Lines.Char_Batman_Misc_Cobra_Barrage_Energy_B_01` | AkDialogueLineSingle | resolved | `Char_Batman_Misc_Cobra_Barrage_Energy_B.Lines.Char_Batman_Misc_Cobra_Barrage_Energy_B_01` in Playable_Batmobile_SF (objects.jsonl) |
| `RInventoryGadget.Mesh` | `Drone_Hacker.GadgetMesh` | SkeletalMeshComponent | resolved | `Weapons.Drone_Hacker.GadgetMesh` in Playable_Batmobile_SF (objects.jsonl) |

## 7. `RBatmobileBooster` - gadget

4 objects over 4 packages, 1 object name(s): 8 field rows (all instances), 4
references (4 resolved, 0 `missing-object`).

| object | instances | variants | field rows | refs | missing |
|---|---|---|---|---|---|
| `Batmobile_Booster` | 4 | Batmobile, MK2, Funhouse, Joker | 8 | 4 | 0 |

### `Batmobile_Booster`

4 instances: **Batmobile**, **MK2**, **Funhouse**, **Joker**.

All 2 fields are identical in every instance (8 comparisons, 0 differences).

| field | offset | type | value |
|---|---|---|---|
| `RInventoryGadget.Mesh` | 0x0318 | ObjectNCRProperty | `Batmobile_Booster.GadgetMesh` |
| `Actor.Tag` | 0x0168 | NameProperty | "RBatmobileBooster" |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RInventoryGadget.Mesh` | `Batmobile_Booster.GadgetMesh` | SkeletalMeshComponent | resolved | `Weapons.Batmobile_Booster.GadgetMesh` in Playable_Batmobile_SF (objects.jsonl) |

## 8. `RBatmobileCannon` - gadget

5 objects over 4 packages, 2 object name(s): 280 field rows (all instances), 70
references (34 resolved, 36 `missing-object`).

| object | instances | variants | field rows | refs | missing |
|---|---|---|---|---|---|
| `Batmobile_Cannon_V2` | 4 | Batmobile, MK2, Funhouse, Joker | 268 | 68 | 36 |
| `Batmobile_JokerCannon_V2` | 1 | Joker | 12 | 2 | 0 |

### `Batmobile_Cannon_V2`

4 instances: **Batmobile**, **MK2**, **Funhouse**, **Joker**.

All 67 fields are identical in every instance (268 comparisons, 0 differences).

| field | offset | type | value |
|---|---|---|---|
| `offset 0x095C` | 0x095C | BoolProperty | true |
| `RBatmobileCannon.GunFX` | 0x0978 | ObjectNCRProperty | `Particles.Batmobile_Muzzleflash_NoTracer` |
| `RBatmobileCannon.RiotSuppressorImpactEffect` | 0x0988 | ObjectNCRProperty | `Riot_Suppressor.Anti_firearm_gel_Miss` |
| `RBatmobileCannon.RiotSuppressorTracerSystem` | 0x0998 | ObjectNCRProperty | `Particles.Batmobile_RiotSuppressor_Tracer` |
| `RBatmobileCannon.ChainGunTracerSystem` | 0x09A0 | ObjectNCRProperty | `Particles.Batmobile_Muzzleflash_Tracer` |
| `RBatmobileCannon.ChainGunLoopingShells` | 0x09A8 | ObjectNCRProperty | `Particles.ChainGun_BulletCasing` |
| `RBatmobileCannon.RiotSuppressorShell` | 0x09B0 | ObjectNCRProperty | `Particles.RiotSuppressor_BulletCasing` |
| `RBatmobileCannon.RiotSuppressorIndividualFireEvent` | 0x09B8 | ObjectNCRProperty | `Engine.Play_RiotSuppressor_Bolt` |
| `RBatmobileCannon.RiotSuppressorHitSound` | 0x09C0 | ObjectNCRProperty | `Engine.Play_RiotSupressor_Impacts` |
| `RBatmobileCannon.ChainGunOverheatSound` | 0x09C8 | ObjectNCRProperty | `Engine.Play_Minigun_Overheat` |
| `RBatmobileCannon.ChainGunCooledSound` | 0x09D0 | ObjectNCRProperty | `Engine.Play_Minigun_Cooled` |
| `RBatmobileCannon.ComboFireLoopingEvent` | 0x0A08 | ObjectNCRProperty | `Engine.Play_Minigun_Combo_Fire` |
| `RBatmobileCannon.EnterComboSound` | 0x0A10 | ObjectNCRProperty | `Engine.Play_Minigun_Combo_Trans_In` |
| `RBatmobileCannon.ExitComboSound` | 0x0A18 | ObjectNCRProperty | `Engine.Play_Minigun_Combo_Trans_Out` |
| `RBatmobileCannon.ChainGunShells` | 0x0A30 | ObjectNCRProperty | `Batmobile_Cannon_V2.ChainGunShells0` |
| `RBatmobileCannon.ImpactMomentum` | 0x0A68 | FloatProperty | 60000.0 |
| `RBatmobileCannon.RecoilImpulse` | 0x0A6C | FloatProperty | 400.0 |
| `RBatmobileCannon.InaccuracyAngle` | 0x0A70 | FloatProperty | 0.10000000149011612 |
| `RBatmobileCannon.HeatUpPerSecond` | 0x0A78 | FloatProperty | 0.0 |
| `RBatmobileCannon.OverheatOffValue` | 0x0A80 | FloatProperty | 0.25 |
| `HeatBarStart` | 0x0A88 | StructProperty | [0.79, 0.68] |
| `HeatBarSize` | 0x0A90 | StructProperty | [0.125, 0.03] |
| `RBatmobileCannon.ChainGunMaxSpinSpeed` | 0x0A98 | FloatProperty | 1440.0 |
| `RBatmobileCannon.ChainGunSpinAccel` | 0x0A9C | FloatProperty | 2500.0 |
| `RBatmobileCannon.ChainGunSpinDecel` | 0x0AA0 | FloatProperty | 2000.0 |
| `RBatmobileCannon.RiotSuppressorLockOnAngle` | 0x0AAC | FloatProperty | 7.5 |
| `RBatmobileCannon.RiotSuppressorFiringInterval` | 0x0AB4 | FloatProperty | 0.75 |
| `RBatmobileCannon.RiotSuppressorVillainImpulse` | 0x0AB8 | FloatProperty | 6000.0 |
| `RiotSuppressorFireScreenShake` | 0x0ABC | StructProperty | struct, 7 props, 112 B |
| `RiotSuppressorFireScreenShake.offset 0x0004` | 0x0004 | FloatProperty | 0.25 |
| `RiotSuppressorFireScreenShake.offset 0x0008` | 0x0008 | VectorProperty | [-20.0, 0.0, 0.0] |
| `RiotSuppressorFireScreenShake.offset 0x0014` | 0x0014 | VectorProperty | [7.0, 0.0, 0.0] |
| `RiotSuppressorFireScreenShake.offset 0x0038` | 0x0038 | VectorProperty | [300.0, 0.0, 0.0] |
| `RiotSuppressorFireScreenShake.offset 0x0044` | 0x0044 | VectorProperty | [2.0, 2.0, 2.0] |
| `RiotSuppressorFireScreenShake.AdvancedOptions` | 0x0078 | StructProperty | struct, 1 props, 10 B |
| `RiotSuppressorFireScreenShake.AdvancedOptions.offset 0x0000` | 0x0000 | BoolProperty | true |
| `RiotSuppressorFireScreenShake.offset 0x0090` | 0x0090 | BoolProperty | true |
| `RBatmobileCannon.ComboFiringInterval` | 0x0B58 | FloatProperty | 0.1379999965429306 |
| `RBatmobileCannon.ChainGunDamage` | 0x0B64 | IntProperty | 40 |
| `RBatmobileCannon.UpgradedDamage` | 0x0B68 | IntProperty | 50 |
| `RBatmobileCannon.ChainGunShellsSocket` | 0x0B84 | NameProperty | "ChainGunShells" |
| `RBatmobileCannon.RiotSuppressorShellsSocket` | 0x0B8C | NameProperty | "RiotSuppressorShells" |
| `ChainGunScreenShake` | 0x0BA4 | StructProperty | struct, 7 props, 112 B |
| `ChainGunScreenShake.offset 0x0004` | 0x0004 | FloatProperty | 0.15000000596046448 |
| `ChainGunScreenShake.offset 0x0008` | 0x0008 | VectorProperty | [-20.0, 0.0, 0.0] |
| `ChainGunScreenShake.offset 0x0014` | 0x0014 | VectorProperty | [7.0, 0.0, 0.0] |
| `ChainGunScreenShake.offset 0x0038` | 0x0038 | VectorProperty | [300.0, 100.0, 0.0] |
| `ChainGunScreenShake.offset 0x0044` | 0x0044 | VectorProperty | [2.0, 2.0, 2.0] |
| `ChainGunScreenShake.AdvancedOptions` | 0x0078 | StructProperty | struct, 1 props, 10 B |
| `ChainGunScreenShake.AdvancedOptions.offset 0x0000` | 0x0000 | BoolProperty | true |
| `ChainGunScreenShake.offset 0x0090` | 0x0090 | BoolProperty | true |
| `InaccuracyVsTime` | 0x0C4C | StructProperty | struct, 1 props, 274 B |
| `InaccuracyVsTime.Points` | 0x0000 | ArrayProperty | array, 4 items: [0.0, 0.0, 0.0, 0.0, "CIM_Linear"]; [0.5, 0.0, 0.0, 0.0, "CIM_Linear"]; [1.5, 1.5, 0.0, 0.0, "CIM_Linear"]; [2.5, 3.0, 0.0, 0.0, "CIM_Linear"] |
| `InaccuracyVsTimeUpgrade` | 0x0C68 | StructProperty | struct, 1 props, 274 B |
| `InaccuracyVsTimeUpgrade.Points` | 0x0000 | ArrayProperty | array, 4 items: [0.0, 0.0, 0.0, 0.0, "CIM_Linear"]; [1.0, 0.0, 0.0, 0.0, "CIM_Linear"]; [3.0, 1.5, 0.0, 0.0, "CIM_Linear"]; [5.0, 3.0, 0.0, 0.0, "CIM_Linear"] |
| `RVehicleWeapon.TempName` | 0x0814 | StrProperty | "Chain Gun" |
| `offset 0x0824` | 0x0824 | BoolProperty | true |
| `RVehicleWeapon.FiringInterval` | 0x0828 | FloatProperty | 0.1379999965429306 |
| `RVehicleWeapon.CursorSpeed` | 0x0858 | FloatProperty | 10.0 |
| `RVehicleWeapon.CursorAccel` | 0x085C | FloatProperty | 18.0 |
| `RVehicleWeapon.CursorDecel` | 0x0860 | FloatProperty | 24.0 |
| `RVehicleWeapon.CursorReturnFactor` | 0x0864 | FloatProperty | 10.0 |
| `RVehicleWeapon.CursorReturnDelay` | 0x0868 | FloatProperty | 0.15000000596046448 |
| `RVehicleWeapon.FireLoopingEvent` | 0x0890 | ObjectNCRProperty | `Engine.Play_Minigun_Fire` |
| `RVehicleWeapon.WeaponHitEvent` | 0x08A8 | ObjectNCRProperty | `Engine.Play_BulletImpact_HitBeep` |
| `RInventoryGadget.Mesh` | 0x0318 | ObjectNCRProperty | `Batmobile_Cannon_V2.GadgetMesh` |
| `Actor.Tag` | 0x0168 | NameProperty | "RBatmobileCannon" |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RBatmobileCannon.GunFX` | `Particles.Batmobile_Muzzleflash_NoTracer` | ParticleSystem | resolved | `VFX_Batmobile.Particles.Batmobile_Muzzleflash_NoTracer` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileCannon.RiotSuppressorImpactEffect` | `Riot_Suppressor.Anti_firearm_gel_Miss` | ParticleSystem | resolved | `Particles.Riot_Suppressor.Anti_firearm_gel_Miss` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileCannon.RiotSuppressorTracerSystem` | `Particles.Batmobile_RiotSuppressor_Tracer` | ParticleSystem | resolved | `VFX_Batmobile.Particles.Batmobile_RiotSuppressor_Tracer` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileCannon.ChainGunTracerSystem` | `Particles.Batmobile_Muzzleflash_Tracer` | ParticleSystem | resolved | `VFX_Batmobile.Particles.Batmobile_Muzzleflash_Tracer` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileCannon.ChainGunLoopingShells` | `Particles.ChainGun_BulletCasing` | ParticleSystem | resolved | `VFX_Batmobile.Particles.ChainGun_BulletCasing` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileCannon.RiotSuppressorShell` | `Particles.RiotSuppressor_BulletCasing` | ParticleSystem | resolved | `VFX_Batmobile.Particles.RiotSuppressor_BulletCasing` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileCannon.RiotSuppressorIndividualFireEvent` | `Engine.Play_RiotSuppressor_Bolt` | AkEvent | missing-object | - |
| `RBatmobileCannon.RiotSuppressorHitSound` | `Engine.Play_RiotSupressor_Impacts` | AkEvent | missing-object | - |
| `RBatmobileCannon.ChainGunOverheatSound` | `Engine.Play_Minigun_Overheat` | AkEvent | missing-object | - |
| `RBatmobileCannon.ChainGunCooledSound` | `Engine.Play_Minigun_Cooled` | AkEvent | missing-object | - |
| `RBatmobileCannon.ComboFireLoopingEvent` | `Engine.Play_Minigun_Combo_Fire` | AkEvent | missing-object | - |
| `RBatmobileCannon.EnterComboSound` | `Engine.Play_Minigun_Combo_Trans_In` | AkEvent | missing-object | - |
| `RBatmobileCannon.ExitComboSound` | `Engine.Play_Minigun_Combo_Trans_Out` | AkEvent | missing-object | - |
| `RBatmobileCannon.ChainGunShells` | `Batmobile_Cannon_V2.ChainGunShells0` | ParticleSystemComponent | resolved | `Weapons.Batmobile_Cannon_V2.ChainGunShells0` in Playable_Batmobile_SF (objects.jsonl) |
| `RVehicleWeapon.FireLoopingEvent` | `Engine.Play_Minigun_Fire` | AkEvent | missing-object | - |
| `RVehicleWeapon.WeaponHitEvent` | `Engine.Play_BulletImpact_HitBeep` | AkEvent | missing-object | - |
| `RInventoryGadget.Mesh` | `Batmobile_Cannon_V2.GadgetMesh` | SkeletalMeshComponent | resolved | `Weapons.Batmobile_Cannon_V2.GadgetMesh` in Playable_Batmobile_SF (objects.jsonl) |

### `Batmobile_JokerCannon_V2`

One instance: **Joker**.

No same-named counterpart in another package, so there is nothing to compare.

| field | offset | type | value |
|---|---|---|---|
| `offset 0x095C` | 0x095C | BoolProperty | true |
| `RBatmobileCannon.ChainGunShells` | 0x0A30 | ObjectNCRProperty | `Batmobile_JokerCannon_V2.ChainGunShells0` |
| `RBatmobileCannon.ImpactMomentum` | 0x0A68 | FloatProperty | 2000.0 |
| `RBatmobileCannon.RiotSuppressorLockOnAngle` | 0x0AAC | FloatProperty | 9.0 |
| `RBatmobileCannon.RiotSuppressorRange` | 0x0AB0 | FloatProperty | 8000.0 |
| `RBatmobileCannon.RiotSuppressorFiringInterval` | 0x0AB4 | FloatProperty | 0.3330000042915344 |
| `RBatmobileCannon.RiotSuppressorVillainImpulse` | 0x0AB8 | FloatProperty | 1500.0 |
| `RBatmobileCannon.MinTurretPitch` | 0x0B5C | FloatProperty | 0.0 |
| `RBatmobileCannon.MaxTurretPitch` | 0x0B60 | FloatProperty | 18.0 |
| `RBatmobileCannon.ChainGunDamage` | 0x0B64 | IntProperty | 999 |
| `RVehicleWeapon.FiringInterval` | 0x0828 | FloatProperty | 0.10000000149011612 |
| `RInventoryGadget.Mesh` | 0x0318 | ObjectNCRProperty | `Batmobile_JokerCannon_V2.GadgetMesh` |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RBatmobileCannon.ChainGunShells` | `Batmobile_JokerCannon_V2.ChainGunShells0` | ParticleSystemComponent | resolved | `Weapons.Batmobile_JokerCannon_V2.ChainGunShells0` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `RInventoryGadget.Mesh` | `Batmobile_JokerCannon_V2.GadgetMesh` | SkeletalMeshComponent | resolved | `Weapons.Batmobile_JokerCannon_V2.GadgetMesh` in Playable_BatmobileJoker_SF (objects.jsonl) |

## 9. `RBatmobileEMP` - gadget

3 objects over 3 packages, 1 object name(s): 36 field rows (all instances), 21
references (15 resolved, 6 `missing-object`).

| object | instances | variants | field rows | refs | missing |
|---|---|---|---|---|---|
| `Batmobile_EMP_Burst` | 3 | Batmobile, MK2, Funhouse | 36 | 21 | 6 |

### `Batmobile_EMP_Burst`

3 instances: **Batmobile**, **MK2**, **Funhouse**.

All 12 fields are identical in every instance (36 comparisons, 0 differences).

| field | offset | type | value |
|---|---|---|---|
| `RBatmobileEMP.ChargeParticle` | 0x0970 | ObjectNCRProperty | `Batmobile_EMP_Burst.ChargeParticle0` |
| `FireParticle` | 0x0988 | ArrayProperty | array, 4 items, 4 B each - payload not decoded |
| `EMPFireSwitch` | 0x09A8 | ArrayProperty | array, 4 items, 4 B each - payload not decoded |
| `RBatmobileEMP.ImpulseComponent` | 0x09C0 | ObjectNCRProperty | `Batmobile_EMP_Burst.ImpulseComponent0` |
| `RVehicleWeapon.WeaponCoolDown` | 0x0830 | FloatProperty | 2.0 |
| `RVehicleWeapon.FireStartEvent` | 0x0880 | ObjectNCRProperty | `Engine.Play_Batmobile_EMP` |
| `RVehicleWeapon.IndividualFireEvent` | 0x0898 | ObjectNCRProperty | `Engine.Play_Batmobile_EMP` |
| `RVehicleWeapon.MaterialToUpdateWhenPresent` | 0x08B8 | ObjectNCRProperty | `Material_MASTERS.Batmobile_V3_Wheel_EMP_MAT_INST` |
| `RVehicleWeapon.MaterialOriginalToUpdateWhenPresent` | 0x08C0 | ObjectNCRProperty | `Material_MASTERS.Batmobile_V3_Wheel_V2_MAT` |
| `RVehicleWeapon.MaterialIndexToUpdateWhenPresent` | 0x092C | IntProperty | 0 |
| `RInventoryGadget.Mesh` | 0x0318 | ObjectNCRProperty | `Batmobile_EMP_Burst.GadgetMesh` |
| `Actor.Tag` | 0x0168 | NameProperty | "RBatmobileEMP" |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RBatmobileEMP.ChargeParticle` | `Batmobile_EMP_Burst.ChargeParticle0` | ParticleSystemComponent | resolved | `Weapons.Batmobile_EMP_Burst.ChargeParticle0` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileEMP.ImpulseComponent` | `Batmobile_EMP_Burst.ImpulseComponent0` | RB_RadialImpulseComponent | resolved | `Weapons.Batmobile_EMP_Burst.ImpulseComponent0` in Playable_Batmobile_SF (objects.jsonl) |
| `RVehicleWeapon.FireStartEvent` | `Engine.Play_Batmobile_EMP` | AkEvent | missing-object | - |
| `RVehicleWeapon.IndividualFireEvent` | `Engine.Play_Batmobile_EMP` | AkEvent | missing-object | - |
| `RVehicleWeapon.MaterialToUpdateWhenPresent` | `Material_MASTERS.Batmobile_V3_Wheel_EMP_MAT_INST` | MaterialInstanceConstant | resolved | `BatmobileV3_Upgrades.Material_MASTERS.Batmobile_V3_Wheel_EMP_MAT_INST` in Playable_Batmobile_SF (objects.jsonl) |
| `RVehicleWeapon.MaterialOriginalToUpdateWhenPresent` | `Material_MASTERS.Batmobile_V3_Wheel_V2_MAT` | Material | resolved | `BatmobileV3_Materials.Material_MASTERS.Batmobile_V3_Wheel_V2_MAT` in Playable_Batmobile_SF (objects.jsonl) |
| `RInventoryGadget.Mesh` | `Batmobile_EMP_Burst.GadgetMesh` | SkeletalMeshComponent | resolved | `Weapons.Batmobile_EMP_Burst.GadgetMesh` in Playable_Batmobile_SF (objects.jsonl) |

## 10. `RBatmobileEMPMissile` - gadget

3 objects over 3 packages, 1 object name(s): 63 field rows (all instances), 33
references (18 resolved, 15 `missing-object`).

| object | instances | variants | field rows | refs | missing |
|---|---|---|---|---|---|
| `Batmobile_EMP_Missile_Launcher` | 3 | Batmobile, MK2, Funhouse | 63 | 33 | 15 |

### `Batmobile_EMP_Missile_Launcher`

3 instances: **Batmobile**, **MK2**, **Funhouse**.

All 21 fields are identical in every instance (63 comparisons, 0 differences).

| field | offset | type | value |
|---|---|---|---|
| `RBatmobileEMPMissile.ProjectileForCarsArchetype` | 0x09BC | ObjectNCRProperty | `Projectiles.Batmobile_EMPMissile_Projectile_ForCars` |
| `RBatmobileEMPMissile.UntagWarningEvent` | 0x09CC | ObjectNCRProperty | `Ww_CHR_BatmanAlerts.Play_HUD_fail` |
| `RBatmobileEMPMissile.CantFireOnPenguinVanDialogue` | 0x09E4 | ObjectNCRProperty | `Conversation.Main_Ch03_S24_Cityx_Pt3_Callcar` |
| `RBatmobileEMPMissile.MissileLockOnDuration` | 0x0A00 | FloatProperty | 2.0 |
| `RBatmobileEMPMissile.CivilianMissileLockOnDuration` | 0x0A04 | FloatProperty | 1.0 |
| `MissileLaunchSockets` | 0x0A0C | ArrayProperty | array, 2 items, 8 B each - payload not decoded |
| `RBatmobileEMPMissile.LauncherAnimNodeName` | 0x0A1C | NameProperty | "PursuitMissileAnim" |
| `RBatmobileEMPMissile.LoseLockXBonus` | 0x0A50 | FloatProperty | 600.0 |
| `RBatmobileEMPMissile.LoseLockYBonus` | 0x0A54 | FloatProperty | 800.0 |
| `RPursuitModeMissileLauncher.ProjectileArchetype` | 0x097C | ObjectNCRProperty | `Projectiles.Batmobile_EMPMissile_Projectile_ForCars` |
| `RPursuitModeMissileLauncher.LaunchSocketName` | 0x0984 | NameProperty | "BattleModeSpotLight" |
| `RPursuitModeMissileLauncher.LaunchRotationOffset` | 0x0994 | RotatorProperty | [-3640, 0, 0] |
| `RPursuitModeMissileLauncher.bInstantFire` | 0x09A0 | BoolProperty | true |
| `RVehicleWeapon.IndividualFireEvent` | 0x0898 | ObjectNCRProperty | `Engine.Play_Batmobile_ApRocket_Fire` |
| `RVehicleWeapon.LockOnBeepSound` | 0x08C8 | ObjectNCRProperty | `Engine.Play_Batmobile_ApRocket_Lock_Beep` |
| `RVehicleWeapon.LockOnBeepProportionParam` | 0x08D0 | ObjectNCRProperty | `Ww_Parameters.BML_AP_Rocket_Lock` |
| `RVehicleWeapon.LockedOnSound` | 0x08D8 | ObjectNCRProperty | `Engine.Play_Batmobile_ApRocket_Locked` |
| `RVehicleWeapon.LockedOnSoundOff` | 0x08E0 | ObjectNCRProperty | `Engine.Stop_Batmobile_ApRocket_Locked` |
| `RVehicleWeapon.LockOnBeepSoundOff` | 0x08E8 | ObjectNCRProperty | `Engine.Stop_Batmobile_ApRocket_Lock_Beep` |
| `RInventoryGadget.Mesh` | 0x0318 | ObjectNCRProperty | `Batmobile_EMP_Missile_Launcher.GadgetMesh` |
| `Actor.Tag` | 0x0168 | NameProperty | "RBatmobileEMPMissile" |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RBatmobileEMPMissile.ProjectileForCarsArchetype` | `Projectiles.Batmobile_EMPMissile_Projectile_ForCars` | RBatmobileMissile | resolved | `Batmobile_Archetypes.Projectiles.Batmobile_EMPMissile_Projectile_ForCars` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileEMPMissile.UntagWarningEvent` | `Ww_CHR_BatmanAlerts.Play_HUD_fail` | AkEvent | resolved | `Ww_CHR_BatmanAlerts.Play_HUD_fail` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileEMPMissile.CantFireOnPenguinVanDialogue` | `Conversation.Main_Ch03_S24_Cityx_Pt3_Callcar` | AkDialogueConversation | resolved | `Main_Ch03_S24_Cityx_Pt3_Callcar.Conversation.Main_Ch03_S24_Cityx_Pt3_Callcar` in Playable_Batmobile_SF (objects.jsonl) |
| `RPursuitModeMissileLauncher.ProjectileArchetype` | `Projectiles.Batmobile_EMPMissile_Projectile_ForCars` | RBatmobileMissile | resolved | `Batmobile_Archetypes.Projectiles.Batmobile_EMPMissile_Projectile_ForCars` in Playable_Batmobile_SF (objects.jsonl) |
| `RVehicleWeapon.IndividualFireEvent` | `Engine.Play_Batmobile_ApRocket_Fire` | AkEvent | missing-object | - |
| `RVehicleWeapon.LockOnBeepSound` | `Engine.Play_Batmobile_ApRocket_Lock_Beep` | AkEvent | missing-object | - |
| `RVehicleWeapon.LockOnBeepProportionParam` | `Ww_Parameters.BML_AP_Rocket_Lock` | AkParameterName | resolved | `Ww_Parameters.BML_AP_Rocket_Lock` in Playable_Batmobile_SF (objects.jsonl) |
| `RVehicleWeapon.LockedOnSound` | `Engine.Play_Batmobile_ApRocket_Locked` | AkEvent | missing-object | - |
| `RVehicleWeapon.LockedOnSoundOff` | `Engine.Stop_Batmobile_ApRocket_Locked` | AkEvent | missing-object | - |
| `RVehicleWeapon.LockOnBeepSoundOff` | `Engine.Stop_Batmobile_ApRocket_Lock_Beep` | AkEvent | missing-object | - |
| `RInventoryGadget.Mesh` | `Batmobile_EMP_Missile_Launcher.GadgetMesh` | SkeletalMeshComponent | resolved | `Weapons.Batmobile_EMP_Missile_Launcher.GadgetMesh` in Playable_Batmobile_SF (objects.jsonl) |

## 11. `RBatmobileHeavyCannon` - gadget

4 objects over 4 packages, 2 object name(s): 165 field rows (all instances), 48
references (41 resolved, 7 `missing-object`).

| object | instances | variants | field rows | refs | missing |
|---|---|---|---|---|---|
| `Batmobile_Heavy_Cannon_Primary` | 3 | Batmobile, MK2, Funhouse | 123 | 39 | 6 |
| `Batmobile_JokerHeavy_Cannon` | 1 | Joker | 42 | 9 | 1 |

### `Batmobile_Heavy_Cannon_Primary`

3 instances: **Batmobile**, **MK2**, **Funhouse**.

All 41 fields are identical in every instance (123 comparisons, 0 differences).

| field | offset | type | value |
|---|---|---|---|
| `RBatmobileHeavyCannon.ProjectileArchetype` | 0x095C | ObjectNCRProperty | `Projectiles.Batmobile_Heavy_Cannon_Primary_Projectile` |
| `RBatmobileHeavyCannon.UpgradedBodyShotProjectileArchetype` | 0x0964 | ObjectNCRProperty | `Projectiles.Batmobile_Heavy_Cannon_BodyShot_Projectile` |
| `RBatmobileHeavyCannon.UpgradedHeadShotProjectileArchetype` | 0x096C | ObjectNCRProperty | `Projectiles.Batmobile_Heavy_Cannon_HeadShot_Projectile` |
| `RBatmobileHeavyCannon.BothUpgradesProjectileArchetype` | 0x0974 | ObjectNCRProperty | `Projectiles.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` |
| `RBatmobileHeavyCannon.FireFX` | 0x097C | ObjectNCRProperty | `Particles.Batmobile_canonMuzzleflash` |
| `RBatmobileHeavyCannon.FireSound` | 0x0984 | ObjectNCRProperty | `Engine.Play_BML_HeavyCannon_Fire` |
| `RBatmobileHeavyCannon.RecoilImpulse` | 0x099C | FloatProperty | 15000.0 |
| `RBatmobileHeavyCannon.LockOnAngle` | 0x09B0 | FloatProperty | 15.0 |
| `RBatmobileHeavyCannon.LockOnTimeMin` | 0x09B8 | FloatProperty | 0.5 |
| `RBatmobileHeavyCannon.LockOnTimeMax` | 0x09BC | FloatProperty | 6.0 |
| `FireScreenShake` | 0x09C4 | StructProperty | struct, 7 props, 112 B |
| `FireScreenShake.offset 0x0004` | 0x0004 | FloatProperty | 0.25 |
| `FireScreenShake.offset 0x0008` | 0x0008 | VectorProperty | [-100.0, 0.0, 0.0] |
| `FireScreenShake.offset 0x0014` | 0x0014 | VectorProperty | [7.0, 35.0, 35.0] |
| `FireScreenShake.offset 0x0038` | 0x0038 | VectorProperty | [1500.0, 0.0, 0.0] |
| `FireScreenShake.offset 0x0044` | 0x0044 | VectorProperty | [2.0, 2.0, 2.0] |
| `FireScreenShake.AdvancedOptions` | 0x0078 | StructProperty | struct, 1 props, 10 B |
| `FireScreenShake.AdvancedOptions.offset 0x0000` | 0x0000 | BoolProperty | true |
| `FireScreenShake.offset 0x0090` | 0x0090 | BoolProperty | true |
| `ChargingScreenShake` | 0x0A60 | StructProperty | struct, 5 props, 66 B |
| `ChargingScreenShake.offset 0x0004` | 0x0004 | FloatProperty | 1000000.0 |
| `ChargingScreenShake.offset 0x0008` | 0x0008 | VectorProperty | [0.0, 0.0, 0.0] |
| `ChargingScreenShake.offset 0x0038` | 0x0038 | VectorProperty | [50.0, 50.0, 0.0] |
| `ChargingScreenShake.offset 0x0044` | 0x0044 | VectorProperty | [15.0, 15.0, 15.0] |
| `ChargingScreenShake.offset 0x0070` | 0x0070 | FloatProperty | 0.0 |
| `RBatmobileHeavyCannon.ChargeUpTime` | 0x0B00 | FloatProperty | 2.5 |
| `RBatmobileHeavyCannon.ChargeMaxDamageRadius` | 0x0B04 | FloatProperty | 0.0 |
| `RVehicleWeapon.TempName` | 0x0814 | StrProperty | "Heavy Cannon" |
| `RVehicleWeapon.FiringInterval` | 0x0828 | FloatProperty | 2.0 |
| `RVehicleWeapon.ReloadSound` | 0x08A0 | ObjectNCRProperty | `Engine.Play_BML_HeavyCannon_Reload` |
| `RVehicleWeapon.LockOnBeepSound` | 0x08C8 | ObjectNCRProperty | `ww_veh_tank_heavy.Play_Tank_Heavy_LockBeep` |
| `RVehicleWeapon.LockOnBeepProportionParam` | 0x08D0 | ObjectNCRProperty | `Ww_Parameters.VEH_Tank_Heavy_LockOn` |
| `RVehicleWeapon.LockedOnSound` | 0x08D8 | ObjectNCRProperty | `ww_veh_tank_heavy.Play_Tank_Heavy_Locked` |
| `RVehicleWeapon.LockedOnSoundOff` | 0x08E0 | ObjectNCRProperty | `ww_veh_tank_heavy.Stop_VEH_Tank_Heavy_Locked` |
| `RVehicleWeapon.LockOnBeepSoundOff` | 0x08E8 | ObjectNCRProperty | `ww_veh_tank_heavy.Stop_VEH_Tank_Heavy_LockBeep` |
| `RVehicleWeapon.ReloadSoundDuration` | 0x08F0 | FloatProperty | 0.4000000059604645 |
| `RVehicleWeapon.LethalRadius` | 0x08FC | FloatProperty | 175.0 |
| `BonesToHideWhenNotPresent` | 0x0914 | ArrayProperty | array, 2 items, 8 B each - payload not decoded |
| `RVehicleWeapon.PowerConsumption` | 0x0938 | FloatProperty | 0.0 |
| `RInventoryGadget.Mesh` | 0x0318 | ObjectNCRProperty | `Batmobile_Heavy_Cannon_Primary.GadgetMesh` |
| `Actor.Tag` | 0x0168 | NameProperty | "RBatmobileHeavyCannon" |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RBatmobileHeavyCannon.ProjectileArchetype` | `Projectiles.Batmobile_Heavy_Cannon_Primary_Projectile` | RBasicProjectile | resolved | `Batmobile_Archetypes.Projectiles.Batmobile_Heavy_Cannon_Primary_Projectile` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileHeavyCannon.UpgradedBodyShotProjectileArchetype` | `Projectiles.Batmobile_Heavy_Cannon_BodyShot_Projectile` | RBasicProjectile | resolved | `Batmobile_Archetypes.Projectiles.Batmobile_Heavy_Cannon_BodyShot_Projectile` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileHeavyCannon.UpgradedHeadShotProjectileArchetype` | `Projectiles.Batmobile_Heavy_Cannon_HeadShot_Projectile` | RBasicProjectile | resolved | `Batmobile_Archetypes.Projectiles.Batmobile_Heavy_Cannon_HeadShot_Projectile` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileHeavyCannon.BothUpgradesProjectileArchetype` | `Projectiles.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` | RBasicProjectile | resolved | `Batmobile_Archetypes.Projectiles.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileHeavyCannon.FireFX` | `Particles.Batmobile_canonMuzzleflash` | ParticleSystem | resolved | `VFX_Batmobile.Particles.Batmobile_canonMuzzleflash` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileHeavyCannon.FireSound` | `Engine.Play_BML_HeavyCannon_Fire` | AkEvent | missing-object | - |
| `RVehicleWeapon.ReloadSound` | `Engine.Play_BML_HeavyCannon_Reload` | AkEvent | missing-object | - |
| `RVehicleWeapon.LockOnBeepSound` | `ww_veh_tank_heavy.Play_Tank_Heavy_LockBeep` | AkEvent | resolved | `ww_veh_tank_heavy.Play_Tank_Heavy_LockBeep` in Playable_Batmobile_SF (objects.jsonl) |
| `RVehicleWeapon.LockOnBeepProportionParam` | `Ww_Parameters.VEH_Tank_Heavy_LockOn` | AkParameterName | resolved | `Ww_Parameters.VEH_Tank_Heavy_LockOn` in Playable_Batmobile_SF (objects.jsonl) |
| `RVehicleWeapon.LockedOnSound` | `ww_veh_tank_heavy.Play_Tank_Heavy_Locked` | AkEvent | resolved | `ww_veh_tank_heavy.Play_Tank_Heavy_Locked` in Playable_Batmobile_SF (objects.jsonl) |
| `RVehicleWeapon.LockedOnSoundOff` | `ww_veh_tank_heavy.Stop_VEH_Tank_Heavy_Locked` | AkEvent | resolved | `ww_veh_tank_heavy.Stop_VEH_Tank_Heavy_Locked` in Playable_Batmobile_SF (objects.jsonl) |
| `RVehicleWeapon.LockOnBeepSoundOff` | `ww_veh_tank_heavy.Stop_VEH_Tank_Heavy_LockBeep` | AkEvent | resolved | `ww_veh_tank_heavy.Stop_VEH_Tank_Heavy_LockBeep` in Playable_Batmobile_SF (objects.jsonl) |
| `RInventoryGadget.Mesh` | `Batmobile_Heavy_Cannon_Primary.GadgetMesh` | SkeletalMeshComponent | resolved | `Weapons.Batmobile_Heavy_Cannon_Primary.GadgetMesh` in Playable_Batmobile_SF (objects.jsonl) |

### `Batmobile_JokerHeavy_Cannon`

One instance: **Joker**.

No same-named counterpart in another package, so there is nothing to compare.

| field | offset | type | value |
|---|---|---|---|
| `RBatmobileHeavyCannon.ProjectileArchetype` | 0x095C | ObjectNCRProperty | `Projectiles.Batmobile_JokerHeavy_Cannon_Projectile` |
| `RBatmobileHeavyCannon.FireFX` | 0x097C | ObjectNCRProperty | `Particles.Batmobile_canonMuzzleflash` |
| `RBatmobileHeavyCannon.FireSound` | 0x0984 | ObjectNCRProperty | `Engine.Play_BML_HeavyCannon_Fire` |
| `RBatmobileHeavyCannon.RecoilImpulse` | 0x099C | FloatProperty | 150000.0 |
| `RBatmobileHeavyCannon.FirePitchOffset` | 0x09A4 | IntProperty | 350 |
| `RBatmobileHeavyCannon.LockOnAngle` | 0x09B0 | FloatProperty | 0.10000000149011612 |
| `offset 0x09B4` | 0x09B4 | BoolProperty | true |
| `RBatmobileHeavyCannon.LockOnTimeMin` | 0x09B8 | FloatProperty | 0.5 |
| `RBatmobileHeavyCannon.LockOnTimeMax` | 0x09BC | FloatProperty | 6.0 |
| `FireScreenShake` | 0x09C4 | StructProperty | struct, 7 props, 112 B |
| `FireScreenShake.offset 0x0004` | 0x0004 | FloatProperty | 0.25 |
| `FireScreenShake.offset 0x0008` | 0x0008 | VectorProperty | [-100.0, 0.0, 0.0] |
| `FireScreenShake.offset 0x0014` | 0x0014 | VectorProperty | [7.0, 35.0, 35.0] |
| `FireScreenShake.offset 0x0038` | 0x0038 | VectorProperty | [1500.0, 0.0, 0.0] |
| `FireScreenShake.offset 0x0044` | 0x0044 | VectorProperty | [2.0, 2.0, 2.0] |
| `FireScreenShake.AdvancedOptions` | 0x0078 | StructProperty | struct, 1 props, 10 B |
| `FireScreenShake.AdvancedOptions.offset 0x0000` | 0x0000 | BoolProperty | true |
| `FireScreenShake.offset 0x0090` | 0x0090 | BoolProperty | true |
| `ChargingScreenShake` | 0x0A60 | StructProperty | struct, 5 props, 66 B |
| `ChargingScreenShake.offset 0x0004` | 0x0004 | FloatProperty | 1000000.0 |
| `ChargingScreenShake.offset 0x0008` | 0x0008 | VectorProperty | [0.0, 0.0, 0.0] |
| `ChargingScreenShake.offset 0x0038` | 0x0038 | VectorProperty | [50.0, 50.0, 0.0] |
| `ChargingScreenShake.offset 0x0044` | 0x0044 | VectorProperty | [15.0, 15.0, 15.0] |
| `ChargingScreenShake.offset 0x0070` | 0x0070 | FloatProperty | 0.0 |
| `RBatmobileHeavyCannon.ChargeUpTime` | 0x0B00 | FloatProperty | 2.5 |
| `RBatmobileHeavyCannon.ChargeMaxDamageRadius` | 0x0B04 | FloatProperty | 0.0 |
| `RBatmobileHeavyCannon.ChaingunAimOffset` | 0x0B0C | VectorProperty | [0.0, 0.0, -50.0] |
| `RVehicleWeapon.TempName` | 0x0814 | StrProperty | "Heavy Cannon" |
| `offset 0x0824` | 0x0824 | BoolProperty | true |
| `RVehicleWeapon.FiringInterval` | 0x0828 | FloatProperty | 2.5 |
| `RVehicleWeapon.LockOnBeepSound` | 0x08C8 | ObjectNCRProperty | `ww_veh_tank_heavy.Play_Tank_Heavy_LockBeep` |
| `RVehicleWeapon.LockOnBeepProportionParam` | 0x08D0 | ObjectNCRProperty | `Ww_Parameters.VEH_Tank_Heavy_LockOn` |
| `RVehicleWeapon.LockedOnSound` | 0x08D8 | ObjectNCRProperty | `ww_veh_tank_heavy.Play_Tank_Heavy_Locked` |
| `RVehicleWeapon.LockedOnSoundOff` | 0x08E0 | ObjectNCRProperty | `ww_veh_tank_heavy.Stop_VEH_Tank_Heavy_Locked` |
| `RVehicleWeapon.LockOnBeepSoundOff` | 0x08E8 | ObjectNCRProperty | `ww_veh_tank_heavy.Stop_VEH_Tank_Heavy_LockBeep` |
| `RVehicleWeapon.ReloadSoundDuration` | 0x08F0 | FloatProperty | 0.5 |
| `BonesToHideWhenNotPresent` | 0x0914 | ArrayProperty | array, 2 items, 8 B each - payload not decoded |
| `RVehicleWeapon.OverrideCamera` | 0x0930 | NameProperty | "CustomCamera" |
| `RVehicleWeapon.PowerConsumption` | 0x0938 | FloatProperty | 0.0 |
| `RInventoryGadget.Mesh` | 0x0318 | ObjectNCRProperty | `Batmobile_JokerHeavy_Cannon.GadgetMesh` |
| `offset 0x010C` | 0x010C | BoolProperty | true |
| `Actor.Tag` | 0x0168 | NameProperty | "RBatmobileHeavyCannon" |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RBatmobileHeavyCannon.ProjectileArchetype` | `Projectiles.Batmobile_JokerHeavy_Cannon_Projectile` | RBasicProjectile | resolved | `Batmobile_Joker_Archetypes.Projectiles.Batmobile_JokerHeavy_Cannon_Projectile` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `RBatmobileHeavyCannon.FireFX` | `Particles.Batmobile_canonMuzzleflash` | ParticleSystem | resolved | `VFX_Batmobile.Particles.Batmobile_canonMuzzleflash` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `RBatmobileHeavyCannon.FireSound` | `Engine.Play_BML_HeavyCannon_Fire` | AkEvent | missing-object | - |
| `RVehicleWeapon.LockOnBeepSound` | `ww_veh_tank_heavy.Play_Tank_Heavy_LockBeep` | AkEvent | resolved | `ww_veh_tank_heavy.Play_Tank_Heavy_LockBeep` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `RVehicleWeapon.LockOnBeepProportionParam` | `Ww_Parameters.VEH_Tank_Heavy_LockOn` | AkParameterName | resolved | `Ww_Parameters.VEH_Tank_Heavy_LockOn` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `RVehicleWeapon.LockedOnSound` | `ww_veh_tank_heavy.Play_Tank_Heavy_Locked` | AkEvent | resolved | `ww_veh_tank_heavy.Play_Tank_Heavy_Locked` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `RVehicleWeapon.LockedOnSoundOff` | `ww_veh_tank_heavy.Stop_VEH_Tank_Heavy_Locked` | AkEvent | resolved | `ww_veh_tank_heavy.Stop_VEH_Tank_Heavy_Locked` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `RVehicleWeapon.LockOnBeepSoundOff` | `ww_veh_tank_heavy.Stop_VEH_Tank_Heavy_LockBeep` | AkEvent | resolved | `ww_veh_tank_heavy.Stop_VEH_Tank_Heavy_LockBeep` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `RInventoryGadget.Mesh` | `Batmobile_JokerHeavy_Cannon.GadgetMesh` | SkeletalMeshComponent | resolved | `Weapons.Batmobile_JokerHeavy_Cannon.GadgetMesh` in Playable_BatmobileJoker_SF (objects.jsonl) |

## 12. `RBatmobileMissileLauncher` - gadget

3 objects over 3 packages, 1 object name(s): 48 field rows (all instances), 33
references (27 resolved, 6 `missing-object`).

| object | instances | variants | field rows | refs | missing |
|---|---|---|---|---|---|
| `Batmobile_Missile_Launcher` | 3 | Batmobile, MK2, Funhouse | 48 | 33 | 6 |

### `Batmobile_Missile_Launcher`

3 instances: **Batmobile**, **MK2**, **Funhouse**.

All 16 fields are identical in every instance (48 comparisons, 0 differences).

| field | offset | type | value |
|---|---|---|---|
| `RBatmobileMissileLauncher.LockOnAngle` | 0x0980 | FloatProperty | 40.0 |
| `RBatmobileMissileLauncher.LockOnRange` | 0x0984 | FloatProperty | 12000.0 |
| `RBatmobileMissileLauncher.MissileClass` | 0x0994 | ObjectNCRProperty | `Projectiles.Batmobile_Missile_Projectile` |
| `RBatmobileMissileLauncher.FireFX` | 0x099C | ObjectNCRProperty | `Rocket.Batmobile_Rocket_Muzzle` |
| `RBatmobileMissileLauncher.LockOnSound` | 0x09A4 | ObjectNCRProperty | `Engine.Play_RiotSuppressor_Select` |
| `RBatmobileMissileLauncher.TargetSwitchName` | 0x09BC | ObjectNCRProperty | `Ww_Batmobile_Target.Batmobile_Target` |
| `RBatmobileMissileLauncher.LastTargetSwitchName` | 0x09C4 | ObjectNCRProperty | `Ww_Batmobile_Target.Batmobile_Target_Last` |
| `RBatmobileMissileLauncher.MissileNumberParameter` | 0x09CC | ObjectNCRProperty | `Ww_Parameters.BML_NumberOfTargets` |
| `RBatmobileMissileLauncher.FinalExplosionSweetener` | 0x09D4 | ObjectNCRProperty | `Ww_VFX_Tank_Explosion.Play_Tank_Explosion_Barrage_Sweetener` |
| `RBatmobileMissileLauncher.NotEnoughEnergyThought` | 0x09E4 | ObjectNCRProperty | `Lines.Char_Batman_Misc_Cobra_Barrage_Energy_01` |
| `RBatmobileMissileLauncher.InvalidHeavyTankAngleThought` | 0x09EC | ObjectNCRProperty | `Lines.Char_Batman_Misc_Cobra_Barrage_01` |
| `RVehicleWeapon.WeaponCoolDown` | 0x0830 | FloatProperty | 20.0 |
| `RVehicleWeapon.IndividualFireEvent` | 0x0898 | ObjectNCRProperty | `Engine.Play_Batmobile_ApRocket_Fire` |
| `RVehicleWeapon.LethalRange` | 0x0900 | FloatProperty | 12000.0 |
| `RInventoryGadget.Mesh` | 0x0318 | ObjectNCRProperty | `Batmobile_Missile_Launcher.GadgetMesh` |
| `Actor.Tag` | 0x0168 | NameProperty | "RBatmobileMissileLauncher" |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RBatmobileMissileLauncher.MissileClass` | `Projectiles.Batmobile_Missile_Projectile` | RBatmobileMissile | resolved | `Batmobile_Archetypes.Projectiles.Batmobile_Missile_Projectile` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileMissileLauncher.FireFX` | `Rocket.Batmobile_Rocket_Muzzle` | ParticleSystem | resolved | `Particles.Rocket.Batmobile_Rocket_Muzzle` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileMissileLauncher.LockOnSound` | `Engine.Play_RiotSuppressor_Select` | AkEvent | missing-object | - |
| `RBatmobileMissileLauncher.TargetSwitchName` | `Ww_Batmobile_Target.Batmobile_Target` | AkSwitchName | resolved | `Ww_Batmobile_Target.Batmobile_Target` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileMissileLauncher.LastTargetSwitchName` | `Ww_Batmobile_Target.Batmobile_Target_Last` | AkSwitchName | resolved | `Ww_Batmobile_Target.Batmobile_Target_Last` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileMissileLauncher.MissileNumberParameter` | `Ww_Parameters.BML_NumberOfTargets` | AkParameterName | resolved | `Ww_Parameters.BML_NumberOfTargets` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileMissileLauncher.FinalExplosionSweetener` | `Ww_VFX_Tank_Explosion.Play_Tank_Explosion_Barrage_Sweetener` | AkEvent | resolved | `Ww_VFX_Tank_Explosion.Play_Tank_Explosion_Barrage_Sweetener` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileMissileLauncher.NotEnoughEnergyThought` | `Lines.Char_Batman_Misc_Cobra_Barrage_Energy_01` | AkDialogueLineSingle | resolved | `Char_Batman_Misc_Cobra_Barrage_Energy.Lines.Char_Batman_Misc_Cobra_Barrage_Energy_01` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileMissileLauncher.InvalidHeavyTankAngleThought` | `Lines.Char_Batman_Misc_Cobra_Barrage_01` | AkDialogueLineSingle | resolved | `Char_Batman_Misc_Cobra_Barrage.Lines.Char_Batman_Misc_Cobra_Barrage_01` in Playable_Batmobile_SF (objects.jsonl) |
| `RVehicleWeapon.IndividualFireEvent` | `Engine.Play_Batmobile_ApRocket_Fire` | AkEvent | missing-object | - |
| `RInventoryGadget.Mesh` | `Batmobile_Missile_Launcher.GadgetMesh` | SkeletalMeshComponent | resolved | `Weapons.Batmobile_Missile_Launcher.GadgetMesh` in Playable_Batmobile_SF (objects.jsonl) |

## 13. `RBatmobileMissileLauncherJoker` - gadget

2 objects over 1 packages, 2 object name(s): 25 field rows (all instances), 9
references (8 resolved, 1 `missing-object`).

| object | instances | variants | field rows | refs | missing |
|---|---|---|---|---|---|
| `Batmobile_JokerMissile_Launcher` | 1 | Joker | 16 | 6 | 1 |
| `Default__RBatmobileMissileLauncherJoker` | 1 | Joker | 9 | 3 | 0 |

### `Batmobile_JokerMissile_Launcher`

One instance: **Joker**.

No same-named counterpart in another package, so there is nothing to compare.

| field | offset | type | value |
|---|---|---|---|
| `RBatmobileMissileLauncherJoker.NumFakeTargetReps` | 0x0A68 | IntProperty | 1 |
| `RBatmobileMissileLauncherJoker.MaxPostTapTargets` | 0x0A6C | IntProperty | 12 |
| `RBatmobileMissileLauncherJoker.NewHydraFX` | 0x0A74 | ObjectNCRProperty | `JokerA2.HydraMissile_P` |
| `RBatmobileMissileLauncherJoker.NewHydraPFX` | 0x0A7C | ObjectNCRProperty | `Batmobile_JokerMissile_Launcher.NewHydraPFX1` |
| `RBatmobileMissileLauncher.MaxTargets` | 0x095C | IntProperty | 8 |
| `RBatmobileMissileLauncher.LockOnAngle` | 0x0980 | FloatProperty | 40.0 |
| `RBatmobileMissileLauncher.FireInterval` | 0x098C | FloatProperty | 0.5 |
| `RBatmobileMissileLauncher.MissileClass` | 0x0994 | ObjectNCRProperty | `Projectiles.Batmobile_JokerMissile_Projectile` |
| `RBatmobileMissileLauncher.FireFX` | 0x099C | ObjectNCRProperty | `Rocket.Batmobile_Rocket_Muzzle` |
| `RBatmobileMissileLauncher.LockOnSound` | 0x09A4 | ObjectNCRProperty | `Engine.Play_RiotSuppressor_Select` |
| `MaxTargetsPerLevel` | 0x0A20 | ArrayProperty | array, 1 items, 4 B each - payload not decoded |
| `MissileSockets` | 0x0A30 | ArrayProperty | array, 10 items, 8 B each - payload not decoded |
| `RVehicleWeapon.WeaponCoolDown` | 0x0830 | FloatProperty | 20.0 |
| `RInventoryGadget.Mesh` | 0x0318 | ObjectNCRProperty | `Batmobile_JokerMissile_Launcher.GadgetMesh` |
| `offset 0x010C` | 0x010C | BoolProperty | true |
| `Actor.Tag` | 0x0168 | NameProperty | "RBatmobileMissileLauncherJoker" |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RBatmobileMissileLauncherJoker.NewHydraFX` | `JokerA2.HydraMissile_P` | ParticleSystem | resolved | `Particles.JokerA2.HydraMissile_P` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `RBatmobileMissileLauncherJoker.NewHydraPFX` | `Batmobile_JokerMissile_Launcher.NewHydraPFX1` | ParticleSystemComponent | resolved | `Weapons.Batmobile_JokerMissile_Launcher.NewHydraPFX1` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `RBatmobileMissileLauncher.MissileClass` | `Projectiles.Batmobile_JokerMissile_Projectile` | RBatmobileMissile | resolved | `Batmobile_Joker_Archetypes.Projectiles.Batmobile_JokerMissile_Projectile` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `RBatmobileMissileLauncher.FireFX` | `Rocket.Batmobile_Rocket_Muzzle` | ParticleSystem | resolved | `Particles.Rocket.Batmobile_Rocket_Muzzle` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `RBatmobileMissileLauncher.LockOnSound` | `Engine.Play_RiotSuppressor_Select` | AkEvent | missing-object | - |
| `RInventoryGadget.Mesh` | `Batmobile_JokerMissile_Launcher.GadgetMesh` | SkeletalMeshComponent | resolved | `Weapons.Batmobile_JokerMissile_Launcher.GadgetMesh` in Playable_BatmobileJoker_SF (objects.jsonl) |

### `Default__RBatmobileMissileLauncherJoker`

One instance: **Joker**.
This is the class-default export (`Default__...`), not a placed gadget; it
is kept in the dump because the card selects by class, and excluded from the
variant comparison.

No same-named counterpart in another package, so there is nothing to compare.

| field | offset | type | value |
|---|---|---|---|
| `RBatmobileMissileLauncherJoker.MaxPostTapTargets` | 0x0A6C | IntProperty | 32 |
| `RBatmobileMissileLauncherJoker.NewHydraPFX` | 0x0A7C | ObjectNCRProperty | `Default__RBatmobileMissileLauncherJoker.NewHydraPFX1` |
| `RBatmobileMissileLauncher.MaxTargets` | 0x095C | IntProperty | 16 |
| `RBatmobileMissileLauncher.MissileFFWaveForm` | 0x09DC | ObjectNCRProperty | `Default__RBatmobileMissileLauncherJoker.MissileForceFeedbackWaveform` |
| `MaxTargetsPerLevel` | 0x0A20 | ArrayProperty | array, 4 items, 4 B each - payload not decoded |
| `RVehicleWeapon.TempName` | 0x0814 | StrProperty | "Missile LauncherJoker" |
| `RVehicleWeapon.PowerConsumption` | 0x0938 | FloatProperty | 4.0 |
| `RInventoryGadget.Mesh` | 0x0318 | ObjectNCRProperty | `Default__RBatmobileMissileLauncherJoker.GadgetMesh` |
| `RInventoryGadget.TargetClass` | 0x04B4 | NameProperty | "BatmobileMissileLauncherJoker" |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RBatmobileMissileLauncherJoker.NewHydraPFX` | `Default__RBatmobileMissileLauncherJoker.NewHydraPFX1` | ParticleSystemComponent | resolved | `BmScript.Default__RBatmobileMissileLauncherJoker.NewHydraPFX1` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `RBatmobileMissileLauncher.MissileFFWaveForm` | `Default__RBatmobileMissileLauncherJoker.MissileForceFeedbackWaveform` | ForceFeedbackWaveform | resolved | `BmScript.Default__RBatmobileMissileLauncherJoker.MissileForceFeedbackWaveform` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `RInventoryGadget.Mesh` | `Default__RBatmobileMissileLauncherJoker.GadgetMesh` | SkeletalMeshComponent | resolved | `BmScript.Default__RBatmobileMissileLauncherJoker.GadgetMesh` in Playable_BatmobileJoker_SF (objects.jsonl) |

## 14. `RBatmobileSonar` - gadget

3 objects over 3 packages, 1 object name(s): 66 field rows (all instances), 33
references (27 resolved, 6 `missing-object`).

| object | instances | variants | field rows | refs | missing |
|---|---|---|---|---|---|
| `Batmobile_Sonar` | 3 | Batmobile, MK2, Funhouse | 66 | 33 | 6 |

### `Batmobile_Sonar`

3 instances: **Batmobile**, **MK2**, **Funhouse**.

All 22 fields are identical in every instance (66 comparisons, 0 differences).

| field | offset | type | value |
|---|---|---|---|
| `ChargingScreenShake` | 0x0968 | StructProperty | struct, 4 props, 50 B |
| `ChargingScreenShake.offset 0x0004` | 0x0004 | FloatProperty | 10000.0 |
| `ChargingScreenShake.offset 0x0008` | 0x0008 | VectorProperty | [4.0, 4.0, 4.0] |
| `ChargingScreenShake.offset 0x0038` | 0x0038 | VectorProperty | [40.0, 40.0, 40.0] |
| `ChargingScreenShake.offset 0x0090` | 0x0090 | BoolProperty | true |
| `RBatmobileSonar.ScanParticle` | 0x0A10 | ObjectNCRProperty | `Particles.Batmobile_Seismic_Sonar` |
| `RBatmobileSonar.ScanSound` | 0x0A18 | ObjectNCRProperty | `Ww_BML_Sonar.Play_BML_Sonar_Pulse_Search` |
| `RBatmobileSonar.ChargeStartSound` | 0x0A28 | ObjectNCRProperty | `Ww_BML_Sonar.Play_BML_Sonar_Rumble_Lp` |
| `RBatmobileSonar.ChargeStopSound` | 0x0A30 | ObjectNCRProperty | `Ww_BML_Sonar.Stop_BML_Sonar_Rumble_Lp` |
| `RBatmobileSonar.BlastParticle` | 0x0A38 | ObjectNCRProperty | `Particles.Batmobile_Seismic_Sonar_Charged` |
| `RBatmobileSonar.BlastSound` | 0x0A40 | ObjectNCRProperty | `Ww_BML_Sonar.Play_BML_Sonar_Pulse_Full` |
| `RBatmobileSonar.BasicScanEffect` | 0x0A48 | ObjectNCRProperty | `Engine.Tire_Track_Pulse_P` |
| `RBatmobileSonar.BasicScanSound` | 0x0A50 | ObjectNCRProperty | `Engine.Play_BML_Sonar_Forensics_Pulse` |
| `RBatmobileSonar.ScannerOnSound` | 0x0A70 | ObjectNCRProperty | `Ww_BML_Sonar.Play_BML_Sonar_Turn_On` |
| `RBatmobileSonar.ScannerOffSound` | 0x0A78 | ObjectNCRProperty | `Ww_BML_Sonar.Play_BML_Sonar_Turn_Off` |
| `BlastScreenShake` | 0x0B1C | StructProperty | struct, 4 props, 66 B |
| `BlastScreenShake.offset 0x0008` | 0x0008 | VectorProperty | [0.0, 70.0, 70.0] |
| `BlastScreenShake.offset 0x0014` | 0x0014 | VectorProperty | [10.0, 10.0, 10.0] |
| `BlastScreenShake.offset 0x0038` | 0x0038 | VectorProperty | [160.0, 160.0, 160.0] |
| `BlastScreenShake.offset 0x0044` | 0x0044 | VectorProperty | [15.0, 15.0, 15.0] |
| `RInventoryGadget.Mesh` | 0x0318 | ObjectNCRProperty | `Batmobile_Sonar.GadgetMesh` |
| `Actor.Tag` | 0x0168 | NameProperty | "RBatmobileSonar" |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RBatmobileSonar.ScanParticle` | `Particles.Batmobile_Seismic_Sonar` | ParticleSystem | resolved | `VFX_Batmobile.Particles.Batmobile_Seismic_Sonar` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileSonar.ScanSound` | `Ww_BML_Sonar.Play_BML_Sonar_Pulse_Search` | AkEvent | resolved | `Ww_BML_Sonar.Play_BML_Sonar_Pulse_Search` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileSonar.ChargeStartSound` | `Ww_BML_Sonar.Play_BML_Sonar_Rumble_Lp` | AkEvent | resolved | `Ww_BML_Sonar.Play_BML_Sonar_Rumble_Lp` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileSonar.ChargeStopSound` | `Ww_BML_Sonar.Stop_BML_Sonar_Rumble_Lp` | AkEvent | resolved | `Ww_BML_Sonar.Stop_BML_Sonar_Rumble_Lp` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileSonar.BlastParticle` | `Particles.Batmobile_Seismic_Sonar_Charged` | ParticleSystem | resolved | `VFX_Batmobile.Particles.Batmobile_Seismic_Sonar_Charged` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileSonar.BlastSound` | `Ww_BML_Sonar.Play_BML_Sonar_Pulse_Full` | AkEvent | resolved | `Ww_BML_Sonar.Play_BML_Sonar_Pulse_Full` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileSonar.BasicScanEffect` | `Engine.Tire_Track_Pulse_P` | ParticleSystem | missing-object | - |
| `RBatmobileSonar.BasicScanSound` | `Engine.Play_BML_Sonar_Forensics_Pulse` | AkEvent | missing-object | - |
| `RBatmobileSonar.ScannerOnSound` | `Ww_BML_Sonar.Play_BML_Sonar_Turn_On` | AkEvent | resolved | `Ww_BML_Sonar.Play_BML_Sonar_Turn_On` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileSonar.ScannerOffSound` | `Ww_BML_Sonar.Play_BML_Sonar_Turn_Off` | AkEvent | resolved | `Ww_BML_Sonar.Play_BML_Sonar_Turn_Off` in Playable_Batmobile_SF (objects.jsonl) |
| `RInventoryGadget.Mesh` | `Batmobile_Sonar.GadgetMesh` | SkeletalMeshComponent | resolved | `Weapons.Batmobile_Sonar.GadgetMesh` in Playable_Batmobile_SF (objects.jsonl) |

## 15. `RBatmobileVehicleTracker` - gadget

3 objects over 3 packages, 1 object name(s): 21 field rows (all instances), 12
references (12 resolved, 0 `missing-object`).

| object | instances | variants | field rows | refs | missing |
|---|---|---|---|---|---|
| `Vehicle_Tracker` | 3 | Batmobile, MK2, Funhouse | 21 | 12 | 0 |

### `Vehicle_Tracker`

3 instances: **Batmobile**, **MK2**, **Funhouse**.

All 7 fields are identical in every instance (21 comparisons, 0 differences).

| field | offset | type | value |
|---|---|---|---|
| `RPursuitModeMissileLauncher.ProjectileArchetype` | 0x097C | ObjectNCRProperty | `Projectiles.Batmobile_Tracker_Projectile` |
| `RPursuitModeMissileLauncher.LaunchSocketName` | 0x0984 | NameProperty | "BattleModeSpotLight" |
| `RPursuitModeMissileLauncher.LaunchRotationOffset` | 0x0994 | RotatorProperty | [5461, 0, 0] |
| `RVehicleWeapon.FireStartEvent` | 0x0880 | ObjectNCRProperty | `ww_chr_batmandisruptor.Play_BatSniperRifle_Vehicle_Tracking_Fire` |
| `RVehicleWeapon.IndividualFireEvent` | 0x0898 | ObjectNCRProperty | `ww_chr_batmandisruptor.Play_BatSniperRifle_Vehicle_Tracking_Fire` |
| `RInventoryGadget.Mesh` | 0x0318 | ObjectNCRProperty | `Vehicle_Tracker.GadgetMesh` |
| `Actor.Tag` | 0x0168 | NameProperty | "RBatmobileVehicleTracker" |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RPursuitModeMissileLauncher.ProjectileArchetype` | `Projectiles.Batmobile_Tracker_Projectile` | RBatmobileMissile | resolved | `Batmobile_Archetypes.Projectiles.Batmobile_Tracker_Projectile` in Playable_Batmobile_SF (objects.jsonl) |
| `RVehicleWeapon.FireStartEvent` | `ww_chr_batmandisruptor.Play_BatSniperRifle_Vehicle_Tracking_Fire` | AkEvent | resolved | `ww_chr_batmandisruptor.Play_BatSniperRifle_Vehicle_Tracking_Fire` in Playable_Batmobile_SF (objects.jsonl) |
| `RVehicleWeapon.IndividualFireEvent` | `ww_chr_batmandisruptor.Play_BatSniperRifle_Vehicle_Tracking_Fire` | AkEvent | resolved | `ww_chr_batmandisruptor.Play_BatSniperRifle_Vehicle_Tracking_Fire` in Playable_Batmobile_SF (objects.jsonl) |
| `RInventoryGadget.Mesh` | `Vehicle_Tracker.GadgetMesh` | SkeletalMeshComponent | resolved | `Weapons.Vehicle_Tracker.GadgetMesh` in Playable_Batmobile_SF (objects.jsonl) |

## 16. `RBatmobileWinch` - gadget

3 objects over 3 packages, 1 object name(s): 63 field rows (all instances), 39
references (24 resolved, 15 `missing-object`).

| object | instances | variants | field rows | refs | missing |
|---|---|---|---|---|---|
| `Batmobile_Winch` | 3 | Batmobile, MK2, Funhouse | 63 | 39 | 15 |

### `Batmobile_Winch`

3 instances: **Batmobile**, **MK2**, **Funhouse**.

All 21 fields are identical in every instance (63 comparisons, 0 differences).

| field | offset | type | value |
|---|---|---|---|
| `offset 0x0970` | 0x0970 | BoolProperty | true |
| `RBatmobileWinch.FireEffect` | 0x0990 | ObjectNCRProperty | `Winch.Winch_Muzzle` |
| `RBatmobileWinch.ImpactEffect` | 0x0998 | ObjectNCRProperty | `VFX_Batmobile.winch_latched` |
| `RBatmobileWinch.FireSound` | 0x09A0 | ObjectNCRProperty | `Engine.Play_BML_WinchFire` |
| `RBatmobileWinch.ImpactSound` | 0x09A8 | ObjectNCRProperty | `Engine.Play_BML_Winch_Attatch` |
| `RBatmobileWinch.ReleaseSound` | 0x09B0 | ObjectNCRProperty | `Engine.Play_BML_WinchDetach` |
| `RBatmobileWinch.TensionStartSound` | 0x09B8 | ObjectNCRProperty | `Engine.Play_BML_Winch_Cable_Tension` |
| `RBatmobileWinch.WinchLoopingSound` | 0x09D0 | ObjectNCRProperty | `Engine.Play_BML_Winch_Cable` |
| `RBatmobileWinch.BatmobileHidePointClass` | 0x0A08 | ObjectNCRProperty | `BmScript.RHidePoint_Batmobile` |
| `RBatmobileWinch.StubRope` | 0x0A10 | ObjectNCRProperty | `Batmobile_Winch.RopeComponent1` |
| `RBatmobileWinch.ProjectileRope` | 0x0A18 | ObjectNCRProperty | `Batmobile_Winch.RopeComponent0` |
| `RBatmobileWinch.BeamElectricityComp` | 0x0A20 | ObjectNCRProperty | `Batmobile_Winch.BeamElectricityComp0` |
| `RBatmobileWinch.FireElectricityComp` | 0x0A28 | ObjectNCRProperty | `Batmobile_Winch.FireElectricityComp0` |
| `FireScreenShake` | 0x0A7C | StructProperty | struct, 3 props, 42 B |
| `FireScreenShake.offset 0x0004` | 0x0004 | FloatProperty | 0.20000000298023224 |
| `FireScreenShake.offset 0x0014` | 0x0014 | VectorProperty | [10.0, 10.0, 10.0] |
| `FireScreenShake.offset 0x0044` | 0x0044 | VectorProperty | [5.0, 5.0, 5.0] |
| `BonesToHideWhenNotPresent` | 0x0914 | ArrayProperty | array, 1 items, 8 B each - payload not decoded |
| `RInventoryGadget.Mesh` | 0x0318 | ObjectNCRProperty | `Batmobile_Winch.GadgetMesh` |
| `CollisionFilter` | 0x011F | ByteProperty | "COF_Projectile" |
| `Actor.Tag` | 0x0168 | NameProperty | "RBatmobileWinch" |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RBatmobileWinch.FireEffect` | `Winch.Winch_Muzzle` | ParticleSystem | resolved | `Particles.Winch.Winch_Muzzle` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileWinch.ImpactEffect` | `VFX_Batmobile.winch_latched` | ParticleSystem | resolved | `VFX_Batmobile.winch_latched` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileWinch.FireSound` | `Engine.Play_BML_WinchFire` | AkEvent | missing-object | - |
| `RBatmobileWinch.ImpactSound` | `Engine.Play_BML_Winch_Attatch` | AkEvent | missing-object | - |
| `RBatmobileWinch.ReleaseSound` | `Engine.Play_BML_WinchDetach` | AkEvent | missing-object | - |
| `RBatmobileWinch.TensionStartSound` | `Engine.Play_BML_Winch_Cable_Tension` | AkEvent | missing-object | - |
| `RBatmobileWinch.WinchLoopingSound` | `Engine.Play_BML_Winch_Cable` | AkEvent | missing-object | - |
| `RBatmobileWinch.BatmobileHidePointClass` | `BmScript.RHidePoint_Batmobile` | - | resolved | `BmScript.RHidePoint_Batmobile` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileWinch.StubRope` | `Batmobile_Winch.RopeComponent1` | RSimpleRopeComponent | resolved | `Weapons.Batmobile_Winch.RopeComponent1` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileWinch.ProjectileRope` | `Batmobile_Winch.RopeComponent0` | RSimpleRopeComponent | resolved | `Weapons.Batmobile_Winch.RopeComponent0` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileWinch.BeamElectricityComp` | `Batmobile_Winch.BeamElectricityComp0` | ParticleSystemComponent | resolved | `Weapons.Batmobile_Winch.BeamElectricityComp0` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileWinch.FireElectricityComp` | `Batmobile_Winch.FireElectricityComp0` | ParticleSystemComponent | resolved | `Weapons.Batmobile_Winch.FireElectricityComp0` in Playable_Batmobile_SF (objects.jsonl) |
| `RInventoryGadget.Mesh` | `Batmobile_Winch.GadgetMesh` | SkeletalMeshComponent | resolved | `Weapons.Batmobile_Winch.GadgetMesh` in Playable_Batmobile_SF (objects.jsonl) |

## 17. `RBasicProjectile` - projectile

13 objects over 4 packages, 5 object name(s): 155 field rows (all instances), 111
references (106 resolved, 5 `missing-object`).

| object | instances | variants | field rows | refs | missing |
|---|---|---|---|---|---|
| `Batmobile_Heavy_Cannon_BodyShot_Projectile` | 3 | Batmobile, MK2, Funhouse | 27 | 24 | 0 |
| `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` | 3 | Batmobile, MK2, Funhouse | 30 | 24 | 0 |
| `Batmobile_Heavy_Cannon_HeadShot_Projectile` | 3 | Batmobile, MK2, Funhouse | 27 | 24 | 0 |
| `Batmobile_Heavy_Cannon_Primary_Projectile` | 3 | Batmobile, MK2, Funhouse | 54 | 30 | 3 |
| `Batmobile_JokerHeavy_Cannon_Projectile` | 1 | Joker | 17 | 9 | 2 |

### `Batmobile_Heavy_Cannon_BodyShot_Projectile`

3 instances: **Batmobile**, **MK2**, **Funhouse**.

All 9 fields are identical in every instance (27 comparisons, 0 differences).

| field | offset | type | value |
|---|---|---|---|
| `RBasicProjectile.ProjectileMesh` | 0x0348 | ObjectNCRProperty | `Batmobile_Heavy_Cannon_BodyShot_Projectile.Mesh0` |
| `RBasicProjectile.ProjectileTrail` | 0x0350 | ObjectNCRProperty | `Batmobile_Heavy_Cannon_BodyShot_Projectile.RocketTrail` |
| `RBasicProjectile.ImpactExplosion` | 0x0364 | ObjectNCRProperty | `Cannon_Upgrades.Impact_Body_UPGR` |
| `RBasicProjectile.MuzzleFlashOverride` | 0x0374 | ObjectNCRProperty | `Cannon_Upgrades.Muzzle_Body_UPGR` |
| `RProjectile.ImpactRadialImpulseComponent` | 0x0330 | ObjectNCRProperty | `Batmobile_Heavy_Cannon_BodyShot_Projectile.ImpulseComponent0` |
| `Projectile.CylinderComponent` | 0x02C0 | ObjectNCRProperty | `Batmobile_Heavy_Cannon_BodyShot_Projectile.CollisionCylinder` |
| `Projectile.Damage` | 0x02D8 | FloatProperty | 75.0 |
| `Actor.DefaultAkAudible` | 0x007C | ObjectNCRProperty | `Batmobile_Heavy_Cannon_BodyShot_Projectile.DefaultAkAudible_` |
| `Actor.CollisionComponent` | 0x00B4 | ObjectNCRProperty | `Batmobile_Heavy_Cannon_BodyShot_Projectile.CollisionCylinder` |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RBasicProjectile.ProjectileMesh` | `Batmobile_Heavy_Cannon_BodyShot_Projectile.Mesh0` | StaticMeshComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_BodyShot_Projectile.Mesh0` in Playable_Batmobile_SF (objects.jsonl) |
| `RBasicProjectile.ProjectileTrail` | `Batmobile_Heavy_Cannon_BodyShot_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_BodyShot_Projectile.RocketTrail` in Playable_Batmobile_SF (objects.jsonl) |
| `RBasicProjectile.ImpactExplosion` | `Cannon_Upgrades.Impact_Body_UPGR` | ParticleSystem | resolved | `Particles.Cannon_Upgrades.Impact_Body_UPGR` in Playable_Batmobile_SF (objects.jsonl) |
| `RBasicProjectile.MuzzleFlashOverride` | `Cannon_Upgrades.Muzzle_Body_UPGR` | ParticleSystem | resolved | `Particles.Cannon_Upgrades.Muzzle_Body_UPGR` in Playable_Batmobile_SF (objects.jsonl) |
| `RProjectile.ImpactRadialImpulseComponent` | `Batmobile_Heavy_Cannon_BodyShot_Projectile.ImpulseComponent0` | RB_RadialImpulseComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_BodyShot_Projectile.ImpulseComponent0` in Playable_Batmobile_SF (objects.jsonl) |
| `Projectile.CylinderComponent` | `Batmobile_Heavy_Cannon_BodyShot_Projectile.CollisionCylinder` | CylinderComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_BodyShot_Projectile.CollisionCylinder` in Playable_Batmobile_SF (objects.jsonl) |
| `Actor.DefaultAkAudible` | `Batmobile_Heavy_Cannon_BodyShot_Projectile.DefaultAkAudible_` | RAkAudible | resolved | `Projectiles.Batmobile_Heavy_Cannon_BodyShot_Projectile.DefaultAkAudible_` in Playable_Batmobile_SF (objects.jsonl) |
| `Actor.CollisionComponent` | `Batmobile_Heavy_Cannon_BodyShot_Projectile.CollisionCylinder` | CylinderComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_BodyShot_Projectile.CollisionCylinder` in Playable_Batmobile_SF (objects.jsonl) |

### `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile`

3 instances: **Batmobile**, **MK2**, **Funhouse**.

All 10 fields are identical in every instance (30 comparisons, 0 differences).

| field | offset | type | value |
|---|---|---|---|
| `RBasicProjectile.ProjectileMesh` | 0x0348 | ObjectNCRProperty | `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.Mesh0` |
| `RBasicProjectile.ProjectileTrail` | 0x0350 | ObjectNCRProperty | `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.RocketTrail` |
| `RBasicProjectile.ImpactExplosion` | 0x0364 | ObjectNCRProperty | `Cannon_Upgrades.Impact_Full_UPGR` |
| `RBasicProjectile.MuzzleFlashOverride` | 0x0374 | ObjectNCRProperty | `Cannon_Upgrades.Muzzle_Full_UPGR` |
| `RBasicProjectile.TurretShotDamage` | 0x03B0 | IntProperty | 110 |
| `RProjectile.ImpactRadialImpulseComponent` | 0x0330 | ObjectNCRProperty | `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.ImpulseComponent0` |
| `Projectile.CylinderComponent` | 0x02C0 | ObjectNCRProperty | `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.CollisionCylinder` |
| `Projectile.Damage` | 0x02D8 | FloatProperty | 75.0 |
| `Actor.DefaultAkAudible` | 0x007C | ObjectNCRProperty | `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.DefaultAkAudible_` |
| `Actor.CollisionComponent` | 0x00B4 | ObjectNCRProperty | `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.CollisionCylinder` |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RBasicProjectile.ProjectileMesh` | `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.Mesh0` | StaticMeshComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.Mesh0` in Playable_Batmobile_SF (objects.jsonl) |
| `RBasicProjectile.ProjectileTrail` | `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.RocketTrail` in Playable_Batmobile_SF (objects.jsonl) |
| `RBasicProjectile.ImpactExplosion` | `Cannon_Upgrades.Impact_Full_UPGR` | ParticleSystem | resolved | `Particles.Cannon_Upgrades.Impact_Full_UPGR` in Playable_Batmobile_SF (objects.jsonl) |
| `RBasicProjectile.MuzzleFlashOverride` | `Cannon_Upgrades.Muzzle_Full_UPGR` | ParticleSystem | resolved | `Particles.Cannon_Upgrades.Muzzle_Full_UPGR` in Playable_Batmobile_SF (objects.jsonl) |
| `RProjectile.ImpactRadialImpulseComponent` | `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.ImpulseComponent0` | RB_RadialImpulseComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.ImpulseComponent0` in Playable_Batmobile_SF (objects.jsonl) |
| `Projectile.CylinderComponent` | `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.CollisionCylinder` | CylinderComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.CollisionCylinder` in Playable_Batmobile_SF (objects.jsonl) |
| `Actor.DefaultAkAudible` | `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.DefaultAkAudible_` | RAkAudible | resolved | `Projectiles.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.DefaultAkAudible_` in Playable_Batmobile_SF (objects.jsonl) |
| `Actor.CollisionComponent` | `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.CollisionCylinder` | CylinderComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile.CollisionCylinder` in Playable_Batmobile_SF (objects.jsonl) |

### `Batmobile_Heavy_Cannon_HeadShot_Projectile`

3 instances: **Batmobile**, **MK2**, **Funhouse**.

All 9 fields are identical in every instance (27 comparisons, 0 differences).

| field | offset | type | value |
|---|---|---|---|
| `RBasicProjectile.ProjectileMesh` | 0x0348 | ObjectNCRProperty | `Batmobile_Heavy_Cannon_HeadShot_Projectile.Mesh0` |
| `RBasicProjectile.ProjectileTrail` | 0x0350 | ObjectNCRProperty | `Batmobile_Heavy_Cannon_HeadShot_Projectile.RocketTrail` |
| `RBasicProjectile.ImpactExplosion` | 0x0364 | ObjectNCRProperty | `Cannon_Upgrades.Impact_Head_UPGR` |
| `RBasicProjectile.MuzzleFlashOverride` | 0x0374 | ObjectNCRProperty | `Cannon_Upgrades.Muzzle_Head_UPGR` |
| `RBasicProjectile.TurretShotDamage` | 0x03B0 | IntProperty | 110 |
| `RProjectile.ImpactRadialImpulseComponent` | 0x0330 | ObjectNCRProperty | `Batmobile_Heavy_Cannon_HeadShot_Projectile.ImpulseComponent0` |
| `Projectile.CylinderComponent` | 0x02C0 | ObjectNCRProperty | `Batmobile_Heavy_Cannon_HeadShot_Projectile.CollisionCylinder` |
| `Actor.DefaultAkAudible` | 0x007C | ObjectNCRProperty | `Batmobile_Heavy_Cannon_HeadShot_Projectile.DefaultAkAudible_` |
| `Actor.CollisionComponent` | 0x00B4 | ObjectNCRProperty | `Batmobile_Heavy_Cannon_HeadShot_Projectile.CollisionCylinder` |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RBasicProjectile.ProjectileMesh` | `Batmobile_Heavy_Cannon_HeadShot_Projectile.Mesh0` | StaticMeshComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_HeadShot_Projectile.Mesh0` in Playable_Batmobile_SF (objects.jsonl) |
| `RBasicProjectile.ProjectileTrail` | `Batmobile_Heavy_Cannon_HeadShot_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_HeadShot_Projectile.RocketTrail` in Playable_Batmobile_SF (objects.jsonl) |
| `RBasicProjectile.ImpactExplosion` | `Cannon_Upgrades.Impact_Head_UPGR` | ParticleSystem | resolved | `Particles.Cannon_Upgrades.Impact_Head_UPGR` in Playable_Batmobile_SF (objects.jsonl) |
| `RBasicProjectile.MuzzleFlashOverride` | `Cannon_Upgrades.Muzzle_Head_UPGR` | ParticleSystem | resolved | `Particles.Cannon_Upgrades.Muzzle_Head_UPGR` in Playable_Batmobile_SF (objects.jsonl) |
| `RProjectile.ImpactRadialImpulseComponent` | `Batmobile_Heavy_Cannon_HeadShot_Projectile.ImpulseComponent0` | RB_RadialImpulseComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_HeadShot_Projectile.ImpulseComponent0` in Playable_Batmobile_SF (objects.jsonl) |
| `Projectile.CylinderComponent` | `Batmobile_Heavy_Cannon_HeadShot_Projectile.CollisionCylinder` | CylinderComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_HeadShot_Projectile.CollisionCylinder` in Playable_Batmobile_SF (objects.jsonl) |
| `Actor.DefaultAkAudible` | `Batmobile_Heavy_Cannon_HeadShot_Projectile.DefaultAkAudible_` | RAkAudible | resolved | `Projectiles.Batmobile_Heavy_Cannon_HeadShot_Projectile.DefaultAkAudible_` in Playable_Batmobile_SF (objects.jsonl) |
| `Actor.CollisionComponent` | `Batmobile_Heavy_Cannon_HeadShot_Projectile.CollisionCylinder` | CylinderComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_HeadShot_Projectile.CollisionCylinder` in Playable_Batmobile_SF (objects.jsonl) |

### `Batmobile_Heavy_Cannon_Primary_Projectile`

3 instances: **Batmobile**, **MK2**, **Funhouse**.

All 18 fields are identical in every instance (54 comparisons, 0 differences).

| field | offset | type | value |
|---|---|---|---|
| `RBasicProjectile.ProjectileMesh` | 0x0348 | ObjectNCRProperty | `Batmobile_Heavy_Cannon_Primary_Projectile.Mesh0` |
| `RBasicProjectile.ProjectileTrail` | 0x0350 | ObjectNCRProperty | `Batmobile_Heavy_Cannon_Primary_Projectile.RocketTrail` |
| `RBasicProjectile.InitialAcceleration` | 0x0358 | VectorProperty | [0.0, 0.0, -1000.0] |
| `RBasicProjectile.ImpactExplosion` | 0x0364 | ObjectNCRProperty | `Particles.Batmobile_HeavyCannon_Impact` |
| `RBasicProjectile.PassThroughDestructibleEffect` | 0x036C | ObjectNCRProperty | `Particles.Batmobile_HeavyCannon_Impact` |
| `RBasicProjectile.ImpactExplosionSound` | 0x037C | ObjectNCRProperty | `Ww_VFX_Tank_Explosion.Play_Batmobile_HeavyCannon_Explosion` |
| `RBasicProjectile.TurretShotDamage` | 0x03B0 | IntProperty | 75 |
| `RProjectile.ImpactRadialImpulseComponent` | 0x0330 | ObjectNCRProperty | `Batmobile_Heavy_Cannon_Primary_Projectile.ImpulseComponent0` |
| `Projectile.Speed` | 0x029C | FloatProperty | 40000.0 |
| `Projectile.MaxSpeed` | 0x02A0 | FloatProperty | 48000.0 |
| `Projectile.CylinderComponent` | 0x02C0 | ObjectNCRProperty | `Batmobile_Heavy_Cannon_Primary_Projectile.CollisionCylinder` |
| `Projectile.MyDamageType` | 0x02C8 | ObjectNCRProperty | `Core.RDmgType_BatmobileCannon` |
| `Projectile.Damage` | 0x02D8 | FloatProperty | 50.0 |
| `Projectile.DamageRadius` | 0x02DC | FloatProperty | 0.0 |
| `Projectile.MomentumTransfer` | 0x02E0 | FloatProperty | 66666.671875 |
| `Actor.DefaultAkAudible` | 0x007C | ObjectNCRProperty | `Batmobile_Heavy_Cannon_Primary_Projectile.DefaultAkAudible_` |
| `Actor.CollisionComponent` | 0x00B4 | ObjectNCRProperty | `Batmobile_Heavy_Cannon_Primary_Projectile.CollisionCylinder` |
| `Actor.Tag` | 0x0168 | NameProperty | "RBasicProjectile" |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RBasicProjectile.ProjectileMesh` | `Batmobile_Heavy_Cannon_Primary_Projectile.Mesh0` | StaticMeshComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_Primary_Projectile.Mesh0` in Playable_Batmobile_SF (objects.jsonl) |
| `RBasicProjectile.ProjectileTrail` | `Batmobile_Heavy_Cannon_Primary_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_Primary_Projectile.RocketTrail` in Playable_Batmobile_SF (objects.jsonl) |
| `RBasicProjectile.ImpactExplosion` | `Particles.Batmobile_HeavyCannon_Impact` | ParticleSystem | resolved | `VFX_Batmobile.Particles.Batmobile_HeavyCannon_Impact` in Playable_Batmobile_SF (objects.jsonl) |
| `RBasicProjectile.PassThroughDestructibleEffect` | `Particles.Batmobile_HeavyCannon_Impact` | ParticleSystem | resolved | `VFX_Batmobile.Particles.Batmobile_HeavyCannon_Impact` in Playable_Batmobile_SF (objects.jsonl) |
| `RBasicProjectile.ImpactExplosionSound` | `Ww_VFX_Tank_Explosion.Play_Batmobile_HeavyCannon_Explosion` | AkEvent | resolved | `Ww_VFX_Tank_Explosion.Play_Batmobile_HeavyCannon_Explosion` in Playable_Batmobile_SF (objects.jsonl) |
| `RProjectile.ImpactRadialImpulseComponent` | `Batmobile_Heavy_Cannon_Primary_Projectile.ImpulseComponent0` | RB_RadialImpulseComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_Primary_Projectile.ImpulseComponent0` in Playable_Batmobile_SF (objects.jsonl) |
| `Projectile.CylinderComponent` | `Batmobile_Heavy_Cannon_Primary_Projectile.CollisionCylinder` | CylinderComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_Primary_Projectile.CollisionCylinder` in Playable_Batmobile_SF (objects.jsonl) |
| `Projectile.MyDamageType` | `Core.RDmgType_BatmobileCannon` | Class | missing-object | - |
| `Actor.DefaultAkAudible` | `Batmobile_Heavy_Cannon_Primary_Projectile.DefaultAkAudible_` | RAkAudible | resolved | `Projectiles.Batmobile_Heavy_Cannon_Primary_Projectile.DefaultAkAudible_` in Playable_Batmobile_SF (objects.jsonl) |
| `Actor.CollisionComponent` | `Batmobile_Heavy_Cannon_Primary_Projectile.CollisionCylinder` | CylinderComponent | resolved | `Projectiles.Batmobile_Heavy_Cannon_Primary_Projectile.CollisionCylinder` in Playable_Batmobile_SF (objects.jsonl) |

### `Batmobile_JokerHeavy_Cannon_Projectile`

One instance: **Joker**.

No same-named counterpart in another package, so there is nothing to compare.

| field | offset | type | value |
|---|---|---|---|
| `RBasicProjectile.ProjectileMesh` | 0x0348 | ObjectNCRProperty | `Batmobile_JokerHeavy_Cannon_Projectile.Mesh0` |
| `RBasicProjectile.ProjectileTrail` | 0x0350 | ObjectNCRProperty | `Batmobile_JokerHeavy_Cannon_Projectile.RocketTrail` |
| `RBasicProjectile.InitialAcceleration` | 0x0358 | VectorProperty | [0.0, 0.0, -1000.0] |
| `RBasicProjectile.ImpactExplosion` | 0x0364 | ObjectNCRProperty | `Engine.Batmobile_rocketExplosion_TEMP` |
| `RBasicProjectile.ImpactExplosionSound` | 0x037C | ObjectNCRProperty | `Ww_VFX_Tank_Explosion.Play_Batmobile_HeavyCannon_Explosion` |
| `RProjectile.ImpactRadialImpulseComponent` | 0x0330 | ObjectNCRProperty | `Batmobile_JokerHeavy_Cannon_Projectile.ImpulseComponent0` |
| `Projectile.Speed` | 0x029C | FloatProperty | 10000.0 |
| `Projectile.MaxSpeed` | 0x02A0 | FloatProperty | 12000.0 |
| `Projectile.CylinderComponent` | 0x02C0 | ObjectNCRProperty | `Batmobile_JokerHeavy_Cannon_Projectile.CollisionCylinder` |
| `Projectile.MyDamageType` | 0x02C8 | ObjectNCRProperty | `Core.RDmgType_BatmobileCannon` |
| `Projectile.Damage` | 0x02D8 | FloatProperty | 250.0 |
| `Projectile.DamageRadius` | 0x02DC | FloatProperty | 350.0 |
| `Projectile.MomentumTransfer` | 0x02E0 | FloatProperty | 70000.0 |
| `Actor.DefaultAkAudible` | 0x007C | ObjectNCRProperty | `Batmobile_JokerHeavy_Cannon_Projectile.DefaultAkAudible_` |
| `Actor.CollisionComponent` | 0x00B4 | ObjectNCRProperty | `Batmobile_JokerHeavy_Cannon_Projectile.CollisionCylinder` |
| `offset 0x010C` | 0x010C | BoolProperty | true |
| `Actor.Tag` | 0x0168 | NameProperty | "RBasicProjectile" |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RBasicProjectile.ProjectileMesh` | `Batmobile_JokerHeavy_Cannon_Projectile.Mesh0` | StaticMeshComponent | resolved | `Projectiles.Batmobile_JokerHeavy_Cannon_Projectile.Mesh0` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `RBasicProjectile.ProjectileTrail` | `Batmobile_JokerHeavy_Cannon_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_JokerHeavy_Cannon_Projectile.RocketTrail` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `RBasicProjectile.ImpactExplosion` | `Engine.Batmobile_rocketExplosion_TEMP` | ParticleSystem | missing-object | - |
| `RBasicProjectile.ImpactExplosionSound` | `Ww_VFX_Tank_Explosion.Play_Batmobile_HeavyCannon_Explosion` | AkEvent | resolved | `Ww_VFX_Tank_Explosion.Play_Batmobile_HeavyCannon_Explosion` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `RProjectile.ImpactRadialImpulseComponent` | `Batmobile_JokerHeavy_Cannon_Projectile.ImpulseComponent0` | RB_RadialImpulseComponent | resolved | `Projectiles.Batmobile_JokerHeavy_Cannon_Projectile.ImpulseComponent0` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `Projectile.CylinderComponent` | `Batmobile_JokerHeavy_Cannon_Projectile.CollisionCylinder` | CylinderComponent | resolved | `Projectiles.Batmobile_JokerHeavy_Cannon_Projectile.CollisionCylinder` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `Projectile.MyDamageType` | `Core.RDmgType_BatmobileCannon` | Class | missing-object | - |
| `Actor.DefaultAkAudible` | `Batmobile_JokerHeavy_Cannon_Projectile.DefaultAkAudible_` | RAkAudible | resolved | `Projectiles.Batmobile_JokerHeavy_Cannon_Projectile.DefaultAkAudible_` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `Actor.CollisionComponent` | `Batmobile_JokerHeavy_Cannon_Projectile.CollisionCylinder` | CylinderComponent | resolved | `Projectiles.Batmobile_JokerHeavy_Cannon_Projectile.CollisionCylinder` in Playable_BatmobileJoker_SF (objects.jsonl) |

## 18. `RBatmobileMissile` - projectile

13 objects over 4 packages, 5 object name(s): 216 field rows (all instances), 151
references (129 resolved, 22 `missing-object`).

| object | instances | variants | field rows | refs | missing |
|---|---|---|---|---|---|
| `Batmobile_EMPMissile_Projectile` | 3 | Batmobile, MK2, Funhouse | 60 | 42 | 9 |
| `Batmobile_EMPMissile_Projectile_ForCars` | 3 | Batmobile, MK2, Funhouse | 30 | 30 | 0 |
| `Batmobile_JokerMissile_Projectile` | 1 | Joker | 24 | 13 | 4 |
| `Batmobile_Missile_Projectile` | 3 | Batmobile, MK2, Funhouse | 54 | 42 | 9 |
| `Batmobile_Tracker_Projectile` | 3 | Batmobile, MK2, Funhouse | 48 | 24 | 0 |

### `Batmobile_EMPMissile_Projectile`

3 instances: **Batmobile**, **MK2**, **Funhouse**.

All 20 fields are identical in every instance (60 comparisons, 0 differences).

| field | offset | type | value |
|---|---|---|---|
| `RBatmobileMissile.ExplosionTemplate` | 0x03C0 | ObjectNCRProperty | `Rocket.Batmobil_Rocket_Explosion` |
| `RBatmobileMissile.ExlposionSound` | 0x03C8 | ObjectNCRProperty | `Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact` |
| `RBatmobileMissile.InitialLoop` | 0x03E0 | ObjectNCRProperty | `Engine.Play_Batmobile_ApRocket_Up` |
| `RBatmobileMissile.HomingLoop` | 0x03F8 | ObjectNCRProperty | `Engine.Play_Batmobile_ApRocket_Flight` |
| `RBatmobileMissile.Trail` | 0x0410 | ObjectNCRProperty | `Batmobile_EMPMissile_Projectile.RocketTrail` |
| `RBatmobileMissile.Mesh` | 0x0418 | ObjectNCRProperty | `Batmobile_EMPMissile_Projectile.Mesh0` |
| `RBatmobileMissile.AccelRate` | 0x0428 | FloatProperty | 40000.0 |
| `RBasicProjectile.ProjectileMesh` | 0x0348 | ObjectNCRProperty | `Batmobile_EMPMissile_Projectile.Mesh0` |
| `RBasicProjectile.ProjectileTrail` | 0x0350 | ObjectNCRProperty | `Batmobile_EMPMissile_Projectile.RocketTrail` |
| `RProjectile.ImpactExplosionFlameTrail` | 0x0328 | ObjectNCRProperty | `Damage_States.FireTrail_APC` |
| `RProjectile.ImpactRadialImpulseComponent` | 0x0330 | ObjectNCRProperty | `Batmobile_EMPMissile_Projectile.RB_RadialImpulseComponent` |
| `offset 0x0338` | 0x0338 | BoolProperty | true |
| `Projectile.MaxSpeed` | 0x02A0 | FloatProperty | 7500.0 |
| `Projectile.CylinderComponent` | 0x02C0 | ObjectNCRProperty | `Batmobile_EMPMissile_Projectile.CollisionCylinder` |
| `Projectile.MyDamageType` | 0x02C8 | ObjectNCRProperty | `Core.RDmgType_BatmobileCannon` |
| `Projectile.Damage` | 0x02D8 | FloatProperty | 60.0 |
| `Projectile.DamageRadius` | 0x02DC | FloatProperty | 0.0 |
| `Actor.DefaultAkAudible` | 0x007C | ObjectNCRProperty | `Batmobile_EMPMissile_Projectile.DefaultAkAudible_` |
| `Actor.CollisionComponent` | 0x00B4 | ObjectNCRProperty | `Batmobile_EMPMissile_Projectile.CollisionCylinder` |
| `Actor.Tag` | 0x0168 | NameProperty | "RBatmobileMissile" |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RBatmobileMissile.ExplosionTemplate` | `Rocket.Batmobil_Rocket_Explosion` | ParticleSystem | resolved | `Particles.Rocket.Batmobil_Rocket_Explosion` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileMissile.ExlposionSound` | `Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact` | AkEvent | resolved | `Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileMissile.InitialLoop` | `Engine.Play_Batmobile_ApRocket_Up` | AkEvent | missing-object | - |
| `RBatmobileMissile.HomingLoop` | `Engine.Play_Batmobile_ApRocket_Flight` | AkEvent | missing-object | - |
| `RBatmobileMissile.Trail` | `Batmobile_EMPMissile_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_EMPMissile_Projectile.RocketTrail` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileMissile.Mesh` | `Batmobile_EMPMissile_Projectile.Mesh0` | StaticMeshComponent | resolved | `Projectiles.Batmobile_EMPMissile_Projectile.Mesh0` in Playable_Batmobile_SF (objects.jsonl) |
| `RBasicProjectile.ProjectileMesh` | `Batmobile_EMPMissile_Projectile.Mesh0` | StaticMeshComponent | resolved | `Projectiles.Batmobile_EMPMissile_Projectile.Mesh0` in Playable_Batmobile_SF (objects.jsonl) |
| `RBasicProjectile.ProjectileTrail` | `Batmobile_EMPMissile_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_EMPMissile_Projectile.RocketTrail` in Playable_Batmobile_SF (objects.jsonl) |
| `RProjectile.ImpactExplosionFlameTrail` | `Damage_States.FireTrail_APC` | ParticleSystem | resolved | `Particles.Damage_States.FireTrail_APC` in Playable_Batmobile_SF (objects.jsonl) |
| `RProjectile.ImpactRadialImpulseComponent` | `Batmobile_EMPMissile_Projectile.RB_RadialImpulseComponent` | RB_RadialImpulseComponent | resolved | `Projectiles.Batmobile_EMPMissile_Projectile.RB_RadialImpulseComponent` in Playable_Batmobile_SF (objects.jsonl) |
| `Projectile.CylinderComponent` | `Batmobile_EMPMissile_Projectile.CollisionCylinder` | CylinderComponent | resolved | `Projectiles.Batmobile_EMPMissile_Projectile.CollisionCylinder` in Playable_Batmobile_SF (objects.jsonl) |
| `Projectile.MyDamageType` | `Core.RDmgType_BatmobileCannon` | Class | missing-object | - |
| `Actor.DefaultAkAudible` | `Batmobile_EMPMissile_Projectile.DefaultAkAudible_` | RAkAudible | resolved | `Projectiles.Batmobile_EMPMissile_Projectile.DefaultAkAudible_` in Playable_Batmobile_SF (objects.jsonl) |
| `Actor.CollisionComponent` | `Batmobile_EMPMissile_Projectile.CollisionCylinder` | CylinderComponent | resolved | `Projectiles.Batmobile_EMPMissile_Projectile.CollisionCylinder` in Playable_Batmobile_SF (objects.jsonl) |

### `Batmobile_EMPMissile_Projectile_ForCars`

3 instances: **Batmobile**, **MK2**, **Funhouse**.

All 10 fields are identical in every instance (30 comparisons, 0 differences).

| field | offset | type | value |
|---|---|---|---|
| `RBatmobileMissile.ExplosionTemplate` | 0x03C0 | ObjectNCRProperty | `Rocket.Batmobil_Rocket_Explosion_Small` |
| `RBatmobileMissile.Trail` | 0x0410 | ObjectNCRProperty | `Batmobile_EMPMissile_Projectile_ForCars.RocketTrail` |
| `RBatmobileMissile.Mesh` | 0x0418 | ObjectNCRProperty | `Batmobile_EMPMissile_Projectile_ForCars.Mesh0` |
| `RBasicProjectile.ProjectileMesh` | 0x0348 | ObjectNCRProperty | `Batmobile_EMPMissile_Projectile_ForCars.Mesh0` |
| `RBasicProjectile.ProjectileTrail` | 0x0350 | ObjectNCRProperty | `Batmobile_EMPMissile_Projectile_ForCars.RocketTrail` |
| `RProjectile.ImpactExplosionFlameTrail` | 0x0328 | ObjectNCRProperty | `Damage_States.FireTrail_Car` |
| `RProjectile.ImpactRadialImpulseComponent` | 0x0330 | ObjectNCRProperty | `Batmobile_EMPMissile_Projectile_ForCars.RB_RadialImpulseComponent` |
| `Projectile.CylinderComponent` | 0x02C0 | ObjectNCRProperty | `Batmobile_EMPMissile_Projectile_ForCars.CollisionCylinder` |
| `Actor.DefaultAkAudible` | 0x007C | ObjectNCRProperty | `Batmobile_EMPMissile_Projectile_ForCars.DefaultAkAudible_` |
| `Actor.CollisionComponent` | 0x00B4 | ObjectNCRProperty | `Batmobile_EMPMissile_Projectile_ForCars.CollisionCylinder` |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RBatmobileMissile.ExplosionTemplate` | `Rocket.Batmobil_Rocket_Explosion_Small` | ParticleSystem | resolved | `Particles.Rocket.Batmobil_Rocket_Explosion_Small` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileMissile.Trail` | `Batmobile_EMPMissile_Projectile_ForCars.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_EMPMissile_Projectile_ForCars.RocketTrail` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileMissile.Mesh` | `Batmobile_EMPMissile_Projectile_ForCars.Mesh0` | StaticMeshComponent | resolved | `Projectiles.Batmobile_EMPMissile_Projectile_ForCars.Mesh0` in Playable_Batmobile_SF (objects.jsonl) |
| `RBasicProjectile.ProjectileMesh` | `Batmobile_EMPMissile_Projectile_ForCars.Mesh0` | StaticMeshComponent | resolved | `Projectiles.Batmobile_EMPMissile_Projectile_ForCars.Mesh0` in Playable_Batmobile_SF (objects.jsonl) |
| `RBasicProjectile.ProjectileTrail` | `Batmobile_EMPMissile_Projectile_ForCars.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_EMPMissile_Projectile_ForCars.RocketTrail` in Playable_Batmobile_SF (objects.jsonl) |
| `RProjectile.ImpactExplosionFlameTrail` | `Damage_States.FireTrail_Car` | ParticleSystem | resolved | `Particles.Damage_States.FireTrail_Car` in Playable_Batmobile_SF (objects.jsonl) |
| `RProjectile.ImpactRadialImpulseComponent` | `Batmobile_EMPMissile_Projectile_ForCars.RB_RadialImpulseComponent` | RB_RadialImpulseComponent | resolved | `Projectiles.Batmobile_EMPMissile_Projectile_ForCars.RB_RadialImpulseComponent` in Playable_Batmobile_SF (objects.jsonl) |
| `Projectile.CylinderComponent` | `Batmobile_EMPMissile_Projectile_ForCars.CollisionCylinder` | CylinderComponent | resolved | `Projectiles.Batmobile_EMPMissile_Projectile_ForCars.CollisionCylinder` in Playable_Batmobile_SF (objects.jsonl) |
| `Actor.DefaultAkAudible` | `Batmobile_EMPMissile_Projectile_ForCars.DefaultAkAudible_` | RAkAudible | resolved | `Projectiles.Batmobile_EMPMissile_Projectile_ForCars.DefaultAkAudible_` in Playable_Batmobile_SF (objects.jsonl) |
| `Actor.CollisionComponent` | `Batmobile_EMPMissile_Projectile_ForCars.CollisionCylinder` | CylinderComponent | resolved | `Projectiles.Batmobile_EMPMissile_Projectile_ForCars.CollisionCylinder` in Playable_Batmobile_SF (objects.jsonl) |

### `Batmobile_JokerMissile_Projectile`

One instance: **Joker**.

No same-named counterpart in another package, so there is nothing to compare.

| field | offset | type | value |
|---|---|---|---|
| `RBatmobileMissile.ExplosionTemplate` | 0x03C0 | ObjectNCRProperty | `Rocket.Batmobil_Rocket_Explosion` |
| `RBatmobileMissile.ExlposionSound` | 0x03C8 | ObjectNCRProperty | `Engine.Play_Explosion_3D` |
| `RBatmobileMissile.InitialLoop` | 0x03E0 | ObjectNCRProperty | `Engine.Play_Batmobile_ApRocket_Up` |
| `RBatmobileMissile.HomingLoop` | 0x03F8 | ObjectNCRProperty | `Engine.Play_Batmobile_ApRocket_Flight` |
| `RBatmobileMissile.Trail` | 0x0410 | ObjectNCRProperty | `Batmobile_JokerMissile_Projectile.RocketTrail` |
| `RBatmobileMissile.Mesh` | 0x0418 | ObjectNCRProperty | `Batmobile_JokerMissile_Projectile.Mesh0` |
| `offset 0x0420` | 0x0420 | BoolProperty | true |
| `RBatmobileMissile.AccelRate` | 0x0428 | FloatProperty | 8000.0 |
| `RBatmobileMissile.ForceExplodeProxDist` | 0x043C | FloatProperty | 100.0 |
| `RBasicProjectile.ProjectileMesh` | 0x0348 | ObjectNCRProperty | `Batmobile_JokerMissile_Projectile.Mesh0` |
| `RBasicProjectile.ProjectileTrail` | 0x0350 | ObjectNCRProperty | `Batmobile_JokerMissile_Projectile.RocketTrail` |
| `RProjectile.ImpactRadialImpulseComponent` | 0x0330 | ObjectNCRProperty | `Batmobile_JokerMissile_Projectile.ImpulseComponent0` |
| `Projectile.Speed` | 0x029C | FloatProperty | 500.0 |
| `Projectile.MaxSpeed` | 0x02A0 | FloatProperty | 1000.0 |
| `Projectile.CylinderComponent` | 0x02C0 | ObjectNCRProperty | `Batmobile_JokerMissile_Projectile.CollisionCylinder` |
| `Projectile.MyDamageType` | 0x02C8 | ObjectNCRProperty | `Core.RDmgType_BatmobileMissileBarrage` |
| `Projectile.Damage` | 0x02D8 | FloatProperty | 250.0 |
| `Projectile.DamageRadius` | 0x02DC | FloatProperty | 300.0 |
| `Projectile.MomentumTransfer` | 0x02E0 | FloatProperty | 25000.0 |
| `Actor.DefaultAkAudible` | 0x007C | ObjectNCRProperty | `Batmobile_JokerMissile_Projectile.DefaultAkAudible_` |
| `Actor.CollisionComponent` | 0x00B4 | ObjectNCRProperty | `Batmobile_JokerMissile_Projectile.CollisionCylinder` |
| `offset 0x0108` | 0x0108 | BoolProperty | true |
| `offset 0x010C` | 0x010C | BoolProperty | true |
| `Actor.Tag` | 0x0168 | NameProperty | "RBatmobileMissile" |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RBatmobileMissile.ExplosionTemplate` | `Rocket.Batmobil_Rocket_Explosion` | ParticleSystem | resolved | `Particles.Rocket.Batmobil_Rocket_Explosion` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `RBatmobileMissile.ExlposionSound` | `Engine.Play_Explosion_3D` | AkEvent | missing-object | - |
| `RBatmobileMissile.InitialLoop` | `Engine.Play_Batmobile_ApRocket_Up` | AkEvent | missing-object | - |
| `RBatmobileMissile.HomingLoop` | `Engine.Play_Batmobile_ApRocket_Flight` | AkEvent | missing-object | - |
| `RBatmobileMissile.Trail` | `Batmobile_JokerMissile_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_JokerMissile_Projectile.RocketTrail` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `RBatmobileMissile.Mesh` | `Batmobile_JokerMissile_Projectile.Mesh0` | StaticMeshComponent | resolved | `Projectiles.Batmobile_JokerMissile_Projectile.Mesh0` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `RBasicProjectile.ProjectileMesh` | `Batmobile_JokerMissile_Projectile.Mesh0` | StaticMeshComponent | resolved | `Projectiles.Batmobile_JokerMissile_Projectile.Mesh0` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `RBasicProjectile.ProjectileTrail` | `Batmobile_JokerMissile_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_JokerMissile_Projectile.RocketTrail` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `RProjectile.ImpactRadialImpulseComponent` | `Batmobile_JokerMissile_Projectile.ImpulseComponent0` | RB_RadialImpulseComponent | resolved | `Projectiles.Batmobile_JokerMissile_Projectile.ImpulseComponent0` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `Projectile.CylinderComponent` | `Batmobile_JokerMissile_Projectile.CollisionCylinder` | CylinderComponent | resolved | `Projectiles.Batmobile_JokerMissile_Projectile.CollisionCylinder` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `Projectile.MyDamageType` | `Core.RDmgType_BatmobileMissileBarrage` | Class | missing-object | - |
| `Actor.DefaultAkAudible` | `Batmobile_JokerMissile_Projectile.DefaultAkAudible_` | RAkAudible | resolved | `Projectiles.Batmobile_JokerMissile_Projectile.DefaultAkAudible_` in Playable_BatmobileJoker_SF (objects.jsonl) |
| `Actor.CollisionComponent` | `Batmobile_JokerMissile_Projectile.CollisionCylinder` | CylinderComponent | resolved | `Projectiles.Batmobile_JokerMissile_Projectile.CollisionCylinder` in Playable_BatmobileJoker_SF (objects.jsonl) |

### `Batmobile_Missile_Projectile`

3 instances: **Batmobile**, **MK2**, **Funhouse**.

All 18 fields are identical in every instance (54 comparisons, 0 differences).

| field | offset | type | value |
|---|---|---|---|
| `RBatmobileMissile.ExplosionTemplate` | 0x03C0 | ObjectNCRProperty | `Rocket.Batmobil_Rocket_Explosion` |
| `RBatmobileMissile.ExlposionSound` | 0x03C8 | ObjectNCRProperty | `Engine.Play_Explosion_3D` |
| `RBatmobileMissile.InitialLoopOn` | 0x03D0 | ObjectNCRProperty | `Ww_VEH_Tank_Missiles.Play_Batmobile_RocketTails` |
| `RBatmobileMissile.HomingLoopOn` | 0x03E8 | ObjectNCRProperty | `Engine.Play_Batmobile_ApRocket_Flight` |
| `RBatmobileMissile.HomingLoopOff` | 0x03F0 | ObjectNCRProperty | `Ww_VEH_Tank_Missiles.Stop_Batmobile_RocketTails` |
| `RBatmobileMissile.Trail` | 0x0410 | ObjectNCRProperty | `Batmobile_Missile_Projectile.RocketTrail` |
| `RBatmobileMissile.Mesh` | 0x0418 | ObjectNCRProperty | `Batmobile_Missile_Projectile.Mesh0` |
| `RBasicProjectile.ProjectileMesh` | 0x0348 | ObjectNCRProperty | `Batmobile_Missile_Projectile.Mesh0` |
| `RBasicProjectile.ProjectileTrail` | 0x0350 | ObjectNCRProperty | `Batmobile_Missile_Projectile.RocketTrail` |
| `RProjectile.ImpactRadialImpulseComponent` | 0x0330 | ObjectNCRProperty | `Batmobile_Missile_Projectile.ImpulseComponent0` |
| `Projectile.CylinderComponent` | 0x02C0 | ObjectNCRProperty | `Batmobile_Missile_Projectile.CollisionCylinder` |
| `Projectile.MyDamageType` | 0x02C8 | ObjectNCRProperty | `Core.RDmgType_BatmobileMissileBarrage` |
| `Projectile.Damage` | 0x02D8 | FloatProperty | 250.0 |
| `Projectile.DamageRadius` | 0x02DC | FloatProperty | 0.0 |
| `Projectile.MomentumTransfer` | 0x02E0 | FloatProperty | 25000.0 |
| `Actor.DefaultAkAudible` | 0x007C | ObjectNCRProperty | `Batmobile_Missile_Projectile.DefaultAkAudible_` |
| `Actor.CollisionComponent` | 0x00B4 | ObjectNCRProperty | `Batmobile_Missile_Projectile.CollisionCylinder` |
| `Actor.Tag` | 0x0168 | NameProperty | "RBatmobileMissile" |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RBatmobileMissile.ExplosionTemplate` | `Rocket.Batmobil_Rocket_Explosion` | ParticleSystem | resolved | `Particles.Rocket.Batmobil_Rocket_Explosion` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileMissile.ExlposionSound` | `Engine.Play_Explosion_3D` | AkEvent | missing-object | - |
| `RBatmobileMissile.InitialLoopOn` | `Ww_VEH_Tank_Missiles.Play_Batmobile_RocketTails` | AkEvent | resolved | `Ww_VEH_Tank_Missiles.Play_Batmobile_RocketTails` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileMissile.HomingLoopOn` | `Engine.Play_Batmobile_ApRocket_Flight` | AkEvent | missing-object | - |
| `RBatmobileMissile.HomingLoopOff` | `Ww_VEH_Tank_Missiles.Stop_Batmobile_RocketTails` | AkEvent | resolved | `Ww_VEH_Tank_Missiles.Stop_Batmobile_RocketTails` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileMissile.Trail` | `Batmobile_Missile_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_Missile_Projectile.RocketTrail` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileMissile.Mesh` | `Batmobile_Missile_Projectile.Mesh0` | StaticMeshComponent | resolved | `Projectiles.Batmobile_Missile_Projectile.Mesh0` in Playable_Batmobile_SF (objects.jsonl) |
| `RBasicProjectile.ProjectileMesh` | `Batmobile_Missile_Projectile.Mesh0` | StaticMeshComponent | resolved | `Projectiles.Batmobile_Missile_Projectile.Mesh0` in Playable_Batmobile_SF (objects.jsonl) |
| `RBasicProjectile.ProjectileTrail` | `Batmobile_Missile_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_Missile_Projectile.RocketTrail` in Playable_Batmobile_SF (objects.jsonl) |
| `RProjectile.ImpactRadialImpulseComponent` | `Batmobile_Missile_Projectile.ImpulseComponent0` | RB_RadialImpulseComponent | resolved | `Projectiles.Batmobile_Missile_Projectile.ImpulseComponent0` in Playable_Batmobile_SF (objects.jsonl) |
| `Projectile.CylinderComponent` | `Batmobile_Missile_Projectile.CollisionCylinder` | CylinderComponent | resolved | `Projectiles.Batmobile_Missile_Projectile.CollisionCylinder` in Playable_Batmobile_SF (objects.jsonl) |
| `Projectile.MyDamageType` | `Core.RDmgType_BatmobileMissileBarrage` | Class | missing-object | - |
| `Actor.DefaultAkAudible` | `Batmobile_Missile_Projectile.DefaultAkAudible_` | RAkAudible | resolved | `Projectiles.Batmobile_Missile_Projectile.DefaultAkAudible_` in Playable_Batmobile_SF (objects.jsonl) |
| `Actor.CollisionComponent` | `Batmobile_Missile_Projectile.CollisionCylinder` | CylinderComponent | resolved | `Projectiles.Batmobile_Missile_Projectile.CollisionCylinder` in Playable_Batmobile_SF (objects.jsonl) |

### `Batmobile_Tracker_Projectile`

3 instances: **Batmobile**, **MK2**, **Funhouse**.

All 16 fields are identical in every instance (48 comparisons, 0 differences).

| field | offset | type | value |
|---|---|---|---|
| `RBatmobileMissile.Trail` | 0x0410 | ObjectNCRProperty | `Batmobile_Tracker_Projectile.RocketTrail` |
| `RBatmobileMissile.Mesh` | 0x0418 | ObjectNCRProperty | `Batmobile_Tracker_Projectile.Mesh0` |
| `offset 0x0420` | 0x0420 | BoolProperty | true |
| `RBatmobileMissile.HomingDelay` | 0x0424 | FloatProperty | 0.20000000298023224 |
| `RBatmobileMissile.AccelRate` | 0x0428 | FloatProperty | 30000.0 |
| `RBasicProjectile.ProjectileMesh` | 0x0348 | ObjectNCRProperty | `Batmobile_Tracker_Projectile.Mesh0` |
| `RBasicProjectile.ProjectileTrail` | 0x0350 | ObjectNCRProperty | `Batmobile_Tracker_Projectile.RocketTrail` |
| `RProjectile.ImpactRadialImpulseComponent` | 0x0330 | ObjectNCRProperty | `Batmobile_Tracker_Projectile.ImpulseComponent0` |
| `Projectile.MaxSpeed` | 0x02A0 | FloatProperty | 20000.0 |
| `Projectile.CylinderComponent` | 0x02C0 | ObjectNCRProperty | `Batmobile_Tracker_Projectile.CollisionCylinder` |
| `Projectile.MyDamageType` | 0x02C8 | ObjectNCRProperty | 0 |
| `Projectile.DamageRadius` | 0x02DC | FloatProperty | 0.0 |
| `Projectile.MomentumTransfer` | 0x02E0 | FloatProperty | 500.0 |
| `Actor.DefaultAkAudible` | 0x007C | ObjectNCRProperty | `Batmobile_Tracker_Projectile.DefaultAkAudible_` |
| `Actor.CollisionComponent` | 0x00B4 | ObjectNCRProperty | `Batmobile_Tracker_Projectile.CollisionCylinder` |
| `Actor.Tag` | 0x0168 | NameProperty | "RBatmobileMissile" |

| field | target | class | status | resolved to |
|---|---|---|---|---|
| `RBatmobileMissile.Trail` | `Batmobile_Tracker_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_Tracker_Projectile.RocketTrail` in Playable_Batmobile_SF (objects.jsonl) |
| `RBatmobileMissile.Mesh` | `Batmobile_Tracker_Projectile.Mesh0` | StaticMeshComponent | resolved | `Projectiles.Batmobile_Tracker_Projectile.Mesh0` in Playable_Batmobile_SF (objects.jsonl) |
| `RBasicProjectile.ProjectileMesh` | `Batmobile_Tracker_Projectile.Mesh0` | StaticMeshComponent | resolved | `Projectiles.Batmobile_Tracker_Projectile.Mesh0` in Playable_Batmobile_SF (objects.jsonl) |
| `RBasicProjectile.ProjectileTrail` | `Batmobile_Tracker_Projectile.RocketTrail` | ParticleSystemComponent | resolved | `Projectiles.Batmobile_Tracker_Projectile.RocketTrail` in Playable_Batmobile_SF (objects.jsonl) |
| `RProjectile.ImpactRadialImpulseComponent` | `Batmobile_Tracker_Projectile.ImpulseComponent0` | RB_RadialImpulseComponent | resolved | `Projectiles.Batmobile_Tracker_Projectile.ImpulseComponent0` in Playable_Batmobile_SF (objects.jsonl) |
| `Projectile.CylinderComponent` | `Batmobile_Tracker_Projectile.CollisionCylinder` | CylinderComponent | resolved | `Projectiles.Batmobile_Tracker_Projectile.CollisionCylinder` in Playable_Batmobile_SF (objects.jsonl) |
| `Actor.DefaultAkAudible` | `Batmobile_Tracker_Projectile.DefaultAkAudible_` | RAkAudible | resolved | `Projectiles.Batmobile_Tracker_Projectile.DefaultAkAudible_` in Playable_Batmobile_SF (objects.jsonl) |
| `Actor.CollisionComponent` | `Batmobile_Tracker_Projectile.CollisionCylinder` | CylinderComponent | resolved | `Projectiles.Batmobile_Tracker_Projectile.CollisionCylinder` in Playable_Batmobile_SF (objects.jsonl) |

## 19. References that leave the four packages

466 references resolve inside their own package; 128 are
`missing-object` over 34 distinct targets. They are not missing from the game - they
point at `Engine.*`, `Core.*` or another package outside the four vehicle packages,
which this desk grab does not carry. Nothing about their values is claimed.

| target | class | occurrences | used by |
|---|---|---|---|
| `Core.RDmgType_BatmobileCannon` | Class | 7 | Batmobile_EMPMissile_Projectile, Batmobile_Heavy_Cannon_Primary_Projectile, Batmobile_JokerHeavy_Cannon_Projectile |
| `Core.RDmgType_BatmobileMissileBarrage` | Class | 4 | Batmobile_JokerMissile_Projectile, Batmobile_Missile_Projectile |
| `Engine.Batmobile_rocketExplosion_TEMP` | ParticleSystem | 1 | Batmobile_JokerHeavy_Cannon_Projectile |
| `Engine.Play_BML_HeavyCannon_Fire` | AkEvent | 4 | Batmobile_Heavy_Cannon_Primary, Batmobile_JokerHeavy_Cannon |
| `Engine.Play_BML_HeavyCannon_Reload` | AkEvent | 3 | Batmobile_Heavy_Cannon_Primary |
| `Engine.Play_BML_Sonar_Forensics_Pulse` | AkEvent | 3 | Batmobile_Sonar |
| `Engine.Play_BML_WinchDetach` | AkEvent | 3 | Batmobile_Winch |
| `Engine.Play_BML_WinchFire` | AkEvent | 3 | Batmobile_Winch |
| `Engine.Play_BML_Winch_Attatch` | AkEvent | 3 | Batmobile_Winch |
| `Engine.Play_BML_Winch_Cable` | AkEvent | 3 | Batmobile_Winch |
| `Engine.Play_BML_Winch_Cable_Tension` | AkEvent | 3 | Batmobile_Winch |
| `Engine.Play_Batmobile_ApRocket_Fire` | AkEvent | 6 | Batmobile_EMP_Missile_Launcher, Batmobile_Missile_Launcher |
| `Engine.Play_Batmobile_ApRocket_Flight` | AkEvent | 7 | Batmobile_EMPMissile_Projectile, Batmobile_JokerMissile_Projectile, Batmobile_Missile_Projectile |
| `Engine.Play_Batmobile_ApRocket_Lock_Beep` | AkEvent | 3 | Batmobile_EMP_Missile_Launcher |
| `Engine.Play_Batmobile_ApRocket_Locked` | AkEvent | 3 | Batmobile_EMP_Missile_Launcher |
| `Engine.Play_Batmobile_ApRocket_Up` | AkEvent | 4 | Batmobile_EMPMissile_Projectile, Batmobile_JokerMissile_Projectile |
| `Engine.Play_Batmobile_DroneHacker_Fire` | AkEvent | 3 | Drone_Hacker |
| `Engine.Play_Batmobile_DroneHacker_Hacked` | AkEvent | 3 | Drone_Hacker |
| `Engine.Play_Batmobile_DroneHacker_Loop` | AkEvent | 3 | Drone_Hacker |
| `Engine.Play_Batmobile_EMP` | AkEvent | 6 | Batmobile_EMP_Burst |
| `Engine.Play_BulletImpact_HitBeep` | AkEvent | 4 | Batmobile_Cannon_V2 |
| `Engine.Play_Explosion_3D` | AkEvent | 4 | Batmobile_JokerMissile_Projectile, Batmobile_Missile_Projectile |
| `Engine.Play_Minigun_Combo_Fire` | AkEvent | 4 | Batmobile_Cannon_V2 |
| `Engine.Play_Minigun_Combo_Trans_In` | AkEvent | 4 | Batmobile_Cannon_V2 |
| `Engine.Play_Minigun_Combo_Trans_Out` | AkEvent | 4 | Batmobile_Cannon_V2 |
| `Engine.Play_Minigun_Cooled` | AkEvent | 4 | Batmobile_Cannon_V2 |
| `Engine.Play_Minigun_Fire` | AkEvent | 4 | Batmobile_Cannon_V2 |
| `Engine.Play_Minigun_Overheat` | AkEvent | 4 | Batmobile_Cannon_V2 |
| `Engine.Play_RiotSuppressor_Bolt` | AkEvent | 4 | Batmobile_Cannon_V2 |
| `Engine.Play_RiotSuppressor_Select` | AkEvent | 4 | Batmobile_JokerMissile_Launcher, Batmobile_Missile_Launcher |
| `Engine.Play_RiotSupressor_Impacts` | AkEvent | 4 | Batmobile_Cannon_V2 |
| `Engine.Stop_Batmobile_ApRocket_Lock_Beep` | AkEvent | 3 | Batmobile_EMP_Missile_Launcher |
| `Engine.Stop_Batmobile_ApRocket_Locked` | AkEvent | 3 | Batmobile_EMP_Missile_Launcher |
| `Engine.Tire_Track_Pulse_P` | ParticleSystem | 3 | Batmobile_Sonar |

## 20. Arrays whose elements the grab did not decode

`objects.jsonl` keeps the array header (`count`, `stride`, `size`) but not the element
bytes, so these arrays are recorded by shape only. They are listed here rather than
silently rendered as empty.

| field | count | stride | size | used by |
|---|---|---|---|---|
| `BonesToHideWhenNotPresent` | 2 | 8 | 20 | Batmobile_Heavy_Cannon_Primary, Batmobile_JokerHeavy_Cannon, Batmobile_Winch |
| `EMPFireSwitch` | 4 | 4 | 20 | Batmobile_EMP_Burst |
| `FireParticle` | 4 | 4 | 20 | Batmobile_EMP_Burst |
| `HackerEffect` | 6 | 4 | 28 | Drone_Hacker |
| `MaxTargetsPerLevel` | 1 | 4 | 8 | Batmobile_JokerMissile_Launcher, Default__RBatmobileMissileLauncherJoker |
| `MissileLaunchSockets` | 2 | 8 | 20 | Batmobile_EMP_Missile_Launcher |
| `MissileSockets` | 10 | 8 | 84 | Batmobile_JokerMissile_Launcher |

## 21. Offset-only fields

These top-level bools have no name: the cooker packs consecutive bools into one 32-bit
word, so a single offset cannot say which flag it belongs to and `bmak_chain.py` refuses
to guess. `objects.jsonl` preserves the word (`bits`); the tag's own value is exact.

| object | field | offset | bool word | value |
|---|---|---|---|---|
| `Playable_BatmobileJoker_SF.Batmobile_JokerHeavy_Cannon_Projectile` | `offset 0x010C` | 0x010C | 0x9C000414 | true |
| `Playable_BatmobileFunhouse_SF.Batmobile_Cannon_V2` | `offset 0x095C` | 0x095C | 0x00000362 | true |
| `Playable_BatmobileFunhouse_SF.Batmobile_Cannon_V2` | `offset 0x0824` | 0x0824 | 0x00000295 | true |
| `Playable_BatmobileJoker_SF.Batmobile_Cannon_V2` | `offset 0x095C` | 0x095C | 0x00000362 | true |
| `Playable_BatmobileJoker_SF.Batmobile_Cannon_V2` | `offset 0x0824` | 0x0824 | 0x00000295 | true |
| `Playable_BatmobileMK2_SF.Batmobile_Cannon_V2` | `offset 0x095C` | 0x095C | 0x00000362 | true |
| `Playable_BatmobileMK2_SF.Batmobile_Cannon_V2` | `offset 0x0824` | 0x0824 | 0x00000295 | true |
| `Playable_Batmobile_SF.Batmobile_Cannon_V2` | `offset 0x095C` | 0x095C | 0x00000362 | true |
| `Playable_Batmobile_SF.Batmobile_Cannon_V2` | `offset 0x0824` | 0x0824 | 0x00000295 | true |
| `Playable_BatmobileJoker_SF.Batmobile_JokerCannon_V2` | `offset 0x095C` | 0x095C | 0x0000136C | true |
| `Playable_BatmobileJoker_SF.Batmobile_JokerHeavy_Cannon` | `offset 0x09B4` | 0x09B4 | 0x00000002 | true |
| `Playable_BatmobileJoker_SF.Batmobile_JokerHeavy_Cannon` | `offset 0x0824` | 0x0824 | 0x00000081 | true |
| `Playable_BatmobileJoker_SF.Batmobile_JokerHeavy_Cannon` | `offset 0x010C` | 0x010C | 0x9C000514 | true |
| `Playable_BatmobileFunhouse_SF.Batmobile_EMPMissile_Projectile` | `offset 0x0338` | 0x0338 | 0x00000200 | true |
| `Playable_BatmobileMK2_SF.Batmobile_EMPMissile_Projectile` | `offset 0x0338` | 0x0338 | 0x00000200 | true |
| `Playable_Batmobile_SF.Batmobile_EMPMissile_Projectile` | `offset 0x0338` | 0x0338 | 0x00000200 | true |
| `Playable_BatmobileJoker_SF.Batmobile_JokerMissile_Projectile` | `offset 0x0420` | 0x0420 | 0x00000018 | true |
| `Playable_BatmobileJoker_SF.Batmobile_JokerMissile_Projectile` | `offset 0x0108` | 0x0108 | 0x00808058 | true |
| `Playable_BatmobileJoker_SF.Batmobile_JokerMissile_Projectile` | `offset 0x010C` | 0x010C | 0x9C000414 | true |
| `Playable_BatmobileFunhouse_SF.Batmobile_Tracker_Projectile` | `offset 0x0420` | 0x0420 | 0x00000002 | true |
| `Playable_BatmobileMK2_SF.Batmobile_Tracker_Projectile` | `offset 0x0420` | 0x0420 | 0x00000002 | true |
| `Playable_Batmobile_SF.Batmobile_Tracker_Projectile` | `offset 0x0420` | 0x0420 | 0x00000002 | true |
| `Playable_BatmobileJoker_SF.Batmobile_JokerMissile_Launcher` | `offset 0x010C` | 0x010C | 0x9C000514 | true |
| `Playable_BatmobileFunhouse_SF.Batmobile_Winch` | `offset 0x0970` | 0x0970 | 0x00000008 | true |
| `Playable_BatmobileMK2_SF.Batmobile_Winch` | `offset 0x0970` | 0x0970 | 0x00000008 | true |
| `Playable_Batmobile_SF.Batmobile_Winch` | `offset 0x0970` | 0x0970 | 0x00000008 | true |

## 22. Reproduce

```bash
python Tools/scripts/grab_weapons.py --write   # -> WEAPONS.json + WEAPONS.md
python Tools/scripts/grab_weapons.py --check   # re-derive and compare
```

