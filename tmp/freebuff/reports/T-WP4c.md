# T-WP4c — tracker, Immobilizer (EMP missile), booster mesh: DONE

Scope: files only. Read-only on the game install, no launch. Translation analysis only; nothing was
built, nothing was approved.

Deliverables (all new; no existing file edited):

- `Tools/scripts/t_wp4c.py` — `--write` / `--check` / `--tamper-test`
- `Working/Translation/T_WP4C_TRACKER_EMP.md` (21,373 chars) and `.json` (36,266 chars)

## What the bytes say, in one paragraph each

**Names vs roles (operator lead (a)).** The Immobilizer **is** `RBatmobileEMPMissile` — proven, not
inferred. Three decoded facts: the class/archetype pair (`RBatmobileEMPMissile` /
`Batmobile_EMP_Missile_Launcher`), its payload pointers
(`ProjectileForCarsArchetype` and superclass `ProjectileArchetype`, both
`Projectiles.Batmobile_EMPMissile_Projectile_ForCars`), and the only *Immobiliser* string in the
weapon data — `RBatmobileMissile.ExlposionSound` =
`Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact` — sitting on this missile's impact. The
*effect* (the disable) remains inferred/native, and that is stated separately.

**Tracker.** `RBatmobileVehicleTracker` (super `RPursuitModeMissileLauncher`, size 2468 = the base's,
so **0 own fields**) is three overrides — `ReadyToFire`, `CheckAutoTarget`, `ProjectileHitActor` — plus
the inherited launcher: `FireWeapon`, `FireBatTracker`, `LaunchSocketName` `BattleModeSpotLight`,
`LaunchRotationOffset` [5461,0,0] = **+30°** pitch, `bInstantFire` true (class default), payload
`Batmobile_Tracker_Projectile` (homing true, `HomingDelay` 0.2 s, `MaxSpeed` 20000, `AccelRate` 30000,
MomentumTransfer 500, **no** `Projectile.Damage`). The acquire envelope (`AutoTargetAngle`@2444,
`Range`@2448) is **not serialized** → values UNKNOWN. The tag is held **on the launcher**, not on the
target: `RBatmobileEMPMissile.TagTarget` (type `RVehicle`), `LockOnTarget`/`LastLockTarget`
(`RVehicleNPC`); no `Tagged`-named member exists on any `RVehicle*` class.

**Gating (lead (b)).** Partly proven, partly refuted. Proven: the lock is fed by the tag, and
`LockOnTime` climbs to `MissileLockOnDuration` **2.0 s** (civilian **1.0 s**). Refuted as a hard gate:
the class carries a dumb-fire path — `GetDumbFireTarget(AimDirection)`, `FireMissile(FireDir)`,
`bTryingToAcquireNewTarget`, `SwitchLockOnTarget(WorldDirection)` — so it can leave the tube without a
lock; whether a dumb-fired missile still **disables** is UNKNOWN (native). The refusal path is decoded
but its rule is not: `CantFireOnPenguinVanDialogue`. Losing a tag is warned, not silent:
`UntagWarningEvent` = `Play_HUD_fail`, `LoseLockTime`, `PromoteUntagPromptTime`, `LoseLockX/YBonus`
600/800.

**Observed activity** (reading the 7 earlier sample files, 1,122 lines): `TagTarget` 50 changes
(26 set / 24 cleared, 17 distinct cars), `LockOnTime` 233 changes, max **1.0**, `LockOnTarget` on 7
distinct cars, `MissileAnimState` ∈ {0,1,2,3}, and **`bFiring = true` never observed** for either
gadget. So tag → lock → (no catch of the launch) is the observed order; nothing about the impact
effect is observed.

**Disable duration (operator's open question).** Not in the files — and not invented. The missile has
no duration/timer/target-class member anywhere in its 36 parsed members or in its ref-only
`_ForCars` projectile. The state names *are* decoded: `RVehicleBatmobileBase.DisabledByEMP`,
`VulnerableToEMP`, `EMPMaterial`, `EMPMaterialIndex`, `SetDisabledByEMP(bool)` (native). The only EMP
durations in BmAK belong to the **burst** gadget (`RBatmobileEMP.DisableEnemyDuration` = 2/4/8/12 s,
Range 7500 uu = 75 m), which is a different button.

**EMP missile numbers.** `Projectile.Damage` 60.0 with `RDmgType_BatmobileCannon`, `DamageRadius` 0,
explosion `Rocket.Batmobil_Rocket_Explosion_Small`, launch at `BattleModeSpotLight` with −20° pitch,
`bInstantFire` true, `BattleModeFireButtonPressed` beside the pursuit lock → written for **both modes**.
The anti-car payload serializes **no scalar at all** (10 reference tags).

**Booster mesh.** `RBatmobileBooster` (size 2400, super `RVehicleWeapon`) holds only
`bBoosting`/`bWarming`; the mesh is on the archetype (`RInventoryGadget.Mesh` →
`Batmobile_Booster.GadgetMesh`). Attach points decoded from `SOCKETS_JC3.md`: `Afterburner` on bone
`JetSMove` (−0.010, 0.538, 3.393, `part_hint` = jet) and `Afterburner_Front` on
`Batmobile_Chassis_Mesh` (0, 0.690, −2.930). Missing in the build: a jet part under `JetSMove` and the
gadget mesh object; the boost force itself is live (`arcade.nitro_boost`).

## JC3 house (five routes, each with its one-shot experiment)

| # | route | key decoded fact | status |
|---|---|---|---|
| R1 | missile weapon that owns the EMP pulse | **25** pulses owned by a `CMissileWeaponBase`, **29** by a `CBulletWeaponBase`, 307 total | decoded pattern; pairing derived |
| R2 | `CEMPWeapon` in a driver slot | `w702_emp` / `w503_turret_emp`, **0** of 88 vehicle weapon components | decoded absence, acceptance UNKNOWN |
| R3 | tag-then-lock | **0** `allegian` hits in 295 entity dumps; lock marker = `POI_TYPE_LOCK_ON_TARGET` 21 | tag half absent; marker half exists |
| R4 | use-item graph | `ui_activate_emp` / `S_STUNT_USE_ITEM_VEHICLE`, no pointer to the pulse | decoded objects, UNKNOWN link |
| R5 | booster mesh | afterburner socket exists and tracks the chassis | decoded socket; part missing |

Reopened: **T-WP9** out → **partial** (carrier yes via w618 clone, tag gate no); **T-WP4** and
**T-MD2** blocked → reopened on routes R1/R2 (the disable is still UNKNOWN, so nothing is claimed met);
**T-WP5** left with T-WP5b, **T-WP8** untouched (sonar is priority 5). Three compromises (C1 tag, C2
disable, C3 mesh) each carry a **RECOMMENDED COMPROMISE** line; none is approved.

## Checks run

- `python Tools/scripts/t_wp4c.py --write` → wrote both outputs (exit 0)
- `python Tools/scripts/t_wp4c.py --check` → `OK` both files, `CHECK PASS` (exit 0)
- `python Tools/scripts/t_wp4c.py --tamper-test` → 3/3 noticed (exit 0):
  header offset `2560 → 2599`; a sample `LockOnTime` forced to `9.25` and the derived max followed
  (`1.0 → 9.25`, same line count); mutated output text fails the byte compare.

## Limitations

- Bytecode bodies of `RBatmobileEMPMissile` / `RBatmobileVehicleTracker` are native (no script bytes),
  so rules inside `CheckAutoTarget`, `ProjectileHitActor`, `FireMissile` are UNKNOWN by construction.
- `AutoTargetAngle`, `Range`, `bInstantFire` are class defaults; only `bInstantFire` is carried by a
  decoded row (true). The other two are UNKNOWN, not zero.
- The disable's duration/look has no member on either side; the earlier runtime samples never caught a
  launch, so the operator's question stays open by evidence, not by omission.
- JC3 numbers in §4.1 come from the generated, independently `--check`ed notes (EMP.md, FORCEPULSE.md,
  HACKABLES.md); the script asserts the values it quotes.
