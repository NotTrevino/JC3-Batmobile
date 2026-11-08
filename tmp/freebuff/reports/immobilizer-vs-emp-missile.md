# Is the Batmobile's Immobilizer the EMP missile? (operator question, 2026-11-05)

**Answer: yes — the data makes the Immobiliser the EMP missile, not an effective transplant.**
`RBatmobileEMPMissile` is the class that fires the immobilising round, and BmAK itself puts the
*Immobiliser* string on that round's impact sound. The qualification the data also forces: the
**tracker is a different launcher** (`RBatmobileVehicleTracker`), on the same button and socket, and
it is the half that tags the target. So "Immobiliser = EMP missile" and "the tracker is a second
launcher" are both true; "the Immobiliser is just a transplant of an EMP missile" is not.

This note is read-only: no ledger row, tune or build was changed.

## 1. The three readings, as claims

| reading | claim | what it would look like in the bytes |
|---|---|---|
| **A** | the Immobiliser **is** the EMP missile — one object, two names | the pursuit launcher class is `RBatmobileEMPMissile`; the menu's *Immobiliser* word appears on that object's payload; the button's native functions are `emp_*` |
| **B** | they are **two things** — an EMP missile and a separate immobiliser gadget | an independent immobiliser class/archetype, and an EMP device elsewhere (the burst) |
| **C** | **one launcher, two warheads** — the same tube fires a plain missile or an EMP round | one class with two `ProjectileArchetype`-style pointers resolving to two *different* payloads |

## 2. Evidence for A (the data's reading)

| # | evidence | file / offset | value | label |
|---:|---|---|---|---|
| A1 | the pursuit launcher's class is the EMP missile class | `Research/BatmobileGrab/WEAPONS.md:49,79`; `ASSETS.md:183,328`; class `BmGame.RBatmobileEMPMissile`, super `RPursuitModeMissileLauncher`, 3 instances, 21 tags | class + archetype `Batmobile_EMP_Missile_Launcher` | decoded |
| A2 | the gadget is mounted as the pursuit-mode weapon | `Research/BatmobileGrab/COLLISION_WHERE.md:73` — export 5036 `PursuitModeWeapons` → `Weapons.Batmobile_EMP_Missile_Launcher`, class `RBatmobileEMPMissile` | one mount, one class | decoded |
| A3 | **both** payload pointers on that launcher resolve to the same anti-car round | `T_WP4D` §1: `RPursuitModeMissileLauncher.ProjectileArchetype` **@2428 (0x97C)** and `RBatmobileEMPMissile.ProjectileForCarsArchetype` **@2492 (0x9BC)** → `Projectiles.Batmobile_EMPMissile_Projectile_ForCars` (export 5116) | 2 refs, 1 target, 0 refs to any other projectile | decoded |
| A4 | the only *Immobiliser* string in the weapon data is on that round family's impact | `RBatmobileMissile.ExlposionSound` **@968** = `Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact` — but **on the sibling archetype** `Batmobile_EMPMissile_Projectile` (export 16), which no export references; the fired `_ForCars` serializes no `AkEvent` | sound leg **demoted** (`T_WP4D` C2) | decoded (sibling) / UNKNOWN (fired) |
| A5 | the button's native functions are EMP-named and belong to this class | `Research/BatmobileGrab/CONTROLS_NATIVE.md:22-25` — `GetDumbFireTarget`, `SwitchLockOnTarget`, `GetAutoTargetOrigin`, `GetAutoTargetRotation` all on `RBatmobileEMPMissile`; 5 functions total (`:42`) | dumb + lock paths in one class | decoded |
| A6 | the controls menu has one button with both words | `Research/BatmobileGrab/CONTROLS_MENU_SCREENS.md:16` — `\| B \| Tracker / Immobilizer \|` | one label, one button | decoded |
| A7 | instant fire belongs to the EMP launcher, not the tracker | `RPursuitModeMissileLauncher.bInstantFire` **@2464** = true, carried by `Batmobile_EMP_Missile_Launcher` in 3 of 4 packages; **0** tracker archetypes carry it (`T_WP4D` §2.1) | true (EMP) / UNKNOWN (tracker) | decoded |

What A does *not* prove: that the round **disables**. The disable is not a member on the missile
class or its projectile (`T_WP4C` §2.4), and the state names that exist
(`DisabledByEMP` @4568, `VulnerableToEMP` @4568, `EMPRepairable` @4572, `SetDisabledByEMP`) are on
`RVehicleBatmobileBase` — the player's own car — not on an NPC vehicle.

## 3. Evidence for B (two things)

| # | evidence | file / offset | value | label |
|---:|---|---|---|---|
| B1 | two classes, not one | `T_WP4C` §0: `RBatmobileEMPMissile` (size 2672) and `RBatmobileVehicleTracker` (size 2468), both super `RPursuitModeMissileLauncher` (2468) | two launcher classes share one base | decoded |
| B2 | two payloads, one per launcher | `T_WP4D` §2/§1: tracker `ProjectileArchetype` **@2428** → `Batmobile_Tracker_Projectile`; EMP launcher **@2428** → `Batmobile_EMPMissile_Projectile_ForCars` | different projectile per class | decoded |
| B3 | the EMP *duration* lives on the burst gadget, not the missile | `RBatmobileEMP.DisableEnemyDuration` **@2400** = 2 / 4 / 8 / 12 s per level, `Range` 7500 uu = 75 m (`T_WP4C` §2.4, T-WP5b) | the missile class has 31 own members, none a duration/timer/target filter | decoded |
| B4 | two different buttons | battle-mode B = EMP burst; pursuit-mode B = tracker/Immobiliser (`T_WP4C` §2.4) | two gadgets, two modes | decoded (function) / derived (binding) |

B is true at the **class** level and false at the **control** level: the button labelled
"Tracker / Immobilizer" is one control, and the object behind the *Immobilizer* half is the EMP
missile class, not a third gadget.

## 4. Evidence for C (one launcher, two warheads)

| # | evidence | file / offset | value | label |
|---:|---|---|---|---|
| C1 | the EMP launcher carries **two** payload pointers | `ProjectileArchetype` @2428 and `ProjectileForCarsArchetype` @2492 (`T_WP4D` §1) | a general round and a cars-specific round were *designed* | decoded (member) |
| C2 | a second, complete round exists in the package | `Batmobile_EMPMissile_Projectile` (export 16): `Projectile.Damage` **@728** 60.0, `DamageRadius` **@732** 0.0, `MyDamageType` **@712** `Core.RDmgType_BatmobileCannon`, impact sound **@968**, `ExplosionTemplate` **@960** `Rocket.Batmobil_Rocket_Explosion` (`T_WP4D` §3) | a fully populated warhead | decoded |
| C3 | …but it is an **orphan** | 0 references to `Batmobile_EMPMissile_Projectile` across 5490 + 5534 + 5584 + 3388 exports; the only 2 refs in each package point at `_ForCars` (`T_WP4D` §1) | not fired by anything | decoded |
| C4 | two firing *paths* do exist in one class | `GetDumbFireTarget(AimDirection)` / `FireMissile(FireDir)` plus the locked path through `TagTarget` @2484 / `LockOnTarget` @2468 (`T_WP4C` §2.2) | aimed vs locked, not two warheads | decoded |

C is **structurally half-true and shipped-false**: the second pointer and a second archetype exist,
but both pointers resolve to `_ForCars`, and the alternate round is referenced by nothing. The
"two warheads" the data supports is *locked vs dumb fire of the same round*, not two round types.

## 5. Which reading the data supports

**A, with B as its qualifier.** The chain is not a name match:

1. the pursuit mount's class *is* `RBatmobileEMPMissile` (A1, A2);
2. that class's two payload pointers both resolve to the anti-car EMP round (A3);
3. the button it sits on is labelled "Tracker / Immobilizer" (A6) and its native functions are
   `emp_*` (A5);
4. instant fire is carried only by that launcher (A7);
5. the only *Immobiliser* event in the weapon data is on that round family (A4), though on the
   unfired sibling, so this leg is weaker than T-WP4c claimed.

So the correct statement is: **the Immobiliser is the EMP missile (`RBatmobileEMPMissile` firing
`Batmobile_EMPMissile_Projectile_ForCars`); the tracker (`RBatmobileVehicleTracker` firing
`Batmobile_Tracker_Projectile`) is a separate launcher on the same button that tags the target the
EMP missile locks onto.** It is not an "effective transplant": no JC3 object was substituted for a
BmAK immobiliser — BmAK has no other immobiliser object. What remains an inference is the
**effect** (the disable), which is code on both sides.

## 6. Effect on the translation (tracker + EMP missile, the operator's first-ranked weapon)

| row | current shape | what this verdict changes |
|---|---|---|
| `T-WP4` (EMP missile) | split as T-WP4a launcher / T-WP4b disable | the **launcher** is now unambiguous: `Batmobile_EMP_Missile_Launcher` (class `RBatmobileEMPMissile`), one mount, payload `_ForCars`; the row must not quote 60 damage or the Immobiliser impact sound as the fired round's (both are the orphan sibling's, `T_WP4D` C2/C3). The fired round's own numbers are: explosion `Rocket.Batmobil_Rocket_Explosion_Small` @960, launch socket `BattleModeSpotLight` @2436, launch rotator [-3640,0,0] @2452, `bInstantFire` @2464 true. Damage/impact sound: UNKNOWN |
| `T-WP9` (tracker) | partial: carrier yes, tag no | the tracker is **not** the Immobiliser and does not inherit its instant fire (`bInstantFire` absent on `Vehicle_Tracker`, `T_WP4D` C1). Its translation is one tagging projectile (`Batmobile_Tracker_Projectile`: homing, `HomingDelay` 0.2 s, `MaxSpeed` 20000, `AccelRate` 30000, no damage) plus the lock timer (`MissileLockOnDuration` **@2560** = 2.0 s, civilian **@2564** = 1.0 s); the tag itself has no JC3 member (`allegian` 0/295, `HACKABLES.md` §1) |
| `T-WP13` (11 weapons, 2 slots) | blocked: 11 into 2 | the two rows above are **one button and one socket** (`BattleModeSpotLight`, offsets 2436/2452 are identical on both launchers), and their effects compose (tag → lock → disable). Modelled as one missile weapon entity, the weapon count is **10, not 11** (derived: 11 classes − 1 shared mount). Still > 2 slots, so the row stays blocked - but its arithmetic must say 10, and the merged entity is what a script-side mode switch would flip |
| `T-MD2` (blocked) | launcher available in both modes | unchanged by this note: `BattleModeFireButtonPressed(RVehicleNPC)` exists beside the pursuit lock, so the launcher half is mode-agnostic; only the disable is missing |

**What the build should do with it (derived, not built):** one missile entity (w618 clone) whose
impact pulse is `truck_emp.ftune` (100 dmg / 25 m) is the Immobiliser; the tracker contributes the
locked-fire half only if a JC3 lock source is found (HUD `POI_TYPE_LOCK_ON_TARGET` = 21 is the marker
without a creation call). Do **not** ship "60 damage" as the Immobiliser's damage, and do not claim
the Immobiliser is a separate gadget from the EMP missile - both claims contradict the bytes.

## 7. UNKNOWN

- The **disable**: duration and look have no member on the missile, its projectile, or any NPC
  vehicle class (`T_WP4C` §2.4). Only the player car's own `DisabledByEMP` state names exist.
- The fired round's `Projectile.Damage`, `DamageRadius`, `MyDamageType` and impact `AkEvent` — all
  four are absent from `_ForCars` and from `Default__RBatmobileMissile` (`T_WP4D` §3, §5).
- The tracker's `bInstantFire` (no record carries it) and which way +pitch tilts its socket
  (5461 → 29.9982 deg, sign convention not in any file).
- Whether `FireBatTracker()` and the EMP launcher are the *same* actor at run time (the classes are
  separate; the samples never caught a launch, `T_WP4C` §1).
- Whether any native helicopter tow / EMP disable exists (engine code, not data).

## 8. Sources, in one block

`Research/BatmobileGrab/WEAPONS.md:48-49,78-79,89-90,105,111-112,124-209,567-574`;
`ASSETS.md:183,328,330`; `COVERAGE.md:91`; `COLLISION_WHERE.md:73`;
`CONTROLS_NATIVE.md:22-25,42`; `CONTROLS_MENU_SCREENS.md:16`;
`Working/Translation/T_WP4C_TRACKER_EMP.md` §0-§2, §5-§7;
`Working/Translation/T_WP4D_TRACKER_EMP.md` §0 (C1-C3), §1-§3;
offsets: 712, 728, 732, 960, 968, 2400, 2428, 2436, 2452, 2464, 2484, 2492, 2560, 2564.
