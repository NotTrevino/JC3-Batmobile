# Damage rules, health, armour, regeneration (G1-14)

The Arkham Knight Batmobile's damage model, read out of `BmGame.upk` (214,757,637 B; 84,813 names /
3,268 imports / 177,031 exports, of which **29,620** are `Function`) with the class dump
(`Working/vendor/BmSDK`) and the archetype tag chain (`Research/BatmobileGrab/CHAIN.json`).

Two things had to be recovered before any of it was readable, and both are recorded in
§1: the `Function` export layout (UEViewer stops parsing this class early, so the
script bodies past that point have never been read from this package), and a
native/script test that does not depend on anybody's guess.

**This note is generated.** `Tools/scripts/bmak_damage.py --write` renders it from
`DAMAGE_RULES.json`; `--check` re-derives that JSON, re-renders this file and diffs both,
so a hand edit to either fails the check (R11: no typed number). Every count, table row
and literal list below is read from the record. The extracted bytecode itself lives
outside this folder, in `Working/vendor/BmAKgrab/scripts/` - this note carries offsets,
symbols, constants and sha1s only.

---

## 1. The `Function` export layout, recovered

`BmGame.upk` is UE3 (version 863 / licensee 32995) and a `Function` export carries **no
Batman property tags** - it is positional. Reading it from byte 0 of the export:

| bytes | field | note |
|---|---|---|
| `u16` | prefix | constant `0` on every `Function` export |
| `i32` @2 | `Next` | `UField` sibling link |
| `i32` @6 | `SuperField` | super function, `0` when the class declares it |
| `i32` @10 | `Children` | first child property (the first parameter) |
| `i32` @14 | `Line` | editor line of the source |
| `i32` @18 | `ScriptSize` | == `len(script) + 1` |
| `byte[]` @22 | `Script` | `len(export) - 38` bytes of executable bytecode |
| `i32` @size-16 | flags word |  |
| `i32` @size-12 | pre-name word | always `0x0002xxxx` |
| `i32` @size-8 | name `FName` index | the function's own name |
| `i32` @size-4 | name number | always `0` |

UEViewer knows only the first four fields: `Unreal/UnTypeinfo.h` handles `GAME_Batman4`
with `Ar << Children; return;   //!! remaining data will be dropped anyway`, so the
script bytes from offset 22 onwards were unclaimed until this pass.

**Anchors** (re-derived by `--check` on every run; 7 of 7 hold):

| anchor | holds | what it proves |
|---|---|---|
| `A_super_is_parent_take_damage` | `true` | `SuperField` of `RVehicleBatmobileBase.TakeDamage` resolves to an inherited `TakeDamage` |
| `A_children_is_first_param` | `true` | `Children` of the same export is `TakeDamage.DamageAmount`, the first parameter |
| `B_script_size_is_len_plus_one` | `true` | `ScriptSize == len(script) + 1` for every traced function |
| `C_thinnest_script_is_return` | `true` | the thinnest script in the package is one byte and it is `0x04` (`EX_Return`) |
| `D_name_word_is_own_name` | `true` | the trailing `FName` is the function's own short name, on every traced function |
| `E_native_parm_refs_own_properties` | `true` | every `0x29` descriptor reference names a property of the function it sits in |
| `F_final_function_token_is_call` | `true` | `0x1c` is followed by a `Function` export in 99%+ of corpus hits (`EX_FinalFunction`) |

Token numbering is the one UE3 and UE4 share (`EX_Return`=0x04, `EX_Let`=0x0F,
`EX_Context`=0x19, `EX_VirtualFunction`=0x1B, `EX_FinalFunction`=0x1C,
`EX_IntConst`=0x1D, `EX_FloatConst`=0x1E, `EX_DynamicCast`=0x2E).

## 2. Native or script: the entry points, decided

A cooked **native** function keeps its parameter list as `0x29 <own-property ref>`
descriptors (five bytes each) in place of bytecode; a **script** function has a statement
body. Two independent sources are recorded per row: the body itself, and the executable's
own `exec<Name>` registration string in `BatmanAK.exe`.

| function | export B | body B | parm descs | `exec<>` in exe | verdict |
|---|---:|---:|---:|---:|---|
| `RVehicleBatmobileBase.TakeDamage` | 2,066 | 2,028 | 0 | 3 | **script** |
| `RVehicleBatmobileBase.TakeRadiusDamageFromWeapon` | 326 | 288 | 0 | 0 | **script** |
| `RVehicleBatmobileBase.TakesDamageFromRam` | 45 | 7 | 0 | 0 | **script** |
| `RVehicleBatmobileBase.ShouldRadialDamageHit` | 48 | 10 | 2 | 1 | **native** |
| `RVehicleBatmobileBase.CanBatmobileDoImpactDamage` | 43 | 5 | 1 | 1 | **native** |
| `RVehicleBatmobileBase.CalculateAndStoreImpactDamage` | 1,570 | 1,532 | 0 | 0 | **script** |
| `RVehicleBatmobileBase.SetDamageLevel` | 48 | 10 | 2 | 3 | **native** |
| `RVehicleBatmobileBase.SetArmouredMode` | 43 | 5 | 1 | 2 | **native** |
| `RVehicleBatmobileBase.DrainWeaponGeneratorForDamage` | 360 | 322 | 0 | 0 | **script** |
| `RVehicleBatmobileBase.ExperienceAwarded` | 218 | 180 | 0 | 0 | **script** |
| `RVehicleBatmobileBase.LoadHealth` | 357 | 319 | 0 | 0 | **script** |
| `RVehicleBatmobileBase.GiveMaxEnergy` | 62 | 24 | 0 | 0 | **script** |
| `RVehicleBatmobileBase.OnModifyHealth` | 154 | 116 | 0 | 0 | **script** |
| `RVehicleCombatManager.GetDamageMod` | 58 | 20 | 3 | 1 | **native** |

Verdict counts, read from the record: **5 native / 9 script** of 14 traced entry
points. The `exec<>` count for `TakeDamage` is 3 and does not make *this* override native:
those strings belong to parent registrations. The body decides, and the two sources only
ever disagree where the body is a stub - they do not.

## 3. The rule: damage type → entry → what scales it → mode

### 3.1 Direct incoming damage - `TakeDamage` (script, 2,028 B)

Aligned reference trace in byte order: 245 references, 90 distinct, listed with their
offsets in `DAMAGE_RULES.json → functions.*.refs`. Reading the byte order:

1. `InCinematicMode` and `SelfDriveMode` gate the hit (cinematic mode returns early - no damage taken while the
   camera is scripted).
2. **`ArmouredMode` → `ArmourModeDamageReduction`** - **1** script function in the
   whole package reads that field, and this body is it. The shipped archetype value is
   **`0`** (`CHAIN.json`), so armoured/battle mode reduces incoming damage by *nothing* as
   shipped.
3. `GetDamageMod` - native, 3 parameters; the encounter layer scales the hit.
4. Cosmetic/state response: `UnStickTyres`, `AddScreenShake`
   with `ExplosiveImpactScreenShake`, `ExplosiveImpactSound`.
5. Counters: `NumBatmobileMissileHits`, `NumBatmobileCannonHits`, each followed by
   `AutoActivateTutorial`.
6. Source-specific branches: casts of `DamageCauser` to `RProjectile`, `RTankMissile` and `RVehicleHeavyTank`,
   the `Cloudburst` flag `bDamagedByCloudburstTank`, the beacon type `RCommandBeaconBase`;
   `LastDamageType` is stored.
7. **The weapon generator is drained here** - the body references
   `DrainWeaponGeneratorForDamage`, then `bEmergencyWeaponGenerator` and
   `WeaponGeneratorPower` (that function is decoded in §4).
8. Thresholds: `QuarterHealth`, `LowHealthWarningLevel` →
   `SetOneShotWarningMessage`, `PlayCommanderBark`, `DisableUnderAttackWarning`,
   `bIsJokerfiedBatmobile`.

Body literals, from the same walk: **9** found, distinct `0.5`, `1.0`, `2.0`, `2.5`, `5.0`, `1000.0`.

### 3.2 Radial / explosion incoming - `TakeRadiusDamageFromWeapon` (script, 288 B)

Calls the **native** `ShouldRadialDamageHit` first (that gate's body is 2 parameter descriptors, so
*whether* a radial hit lands is decided in `BatmanAK.exe` and is not readable from script),
then computes a distance falloff from
`Dist`, `ColRadius`, `ColHeight`, `Dir` and `DamageFalloffExponent` with the
body literals **`0.0`, `0.1`, `0.5`, `1.0`, `1500.0`**, clamps the result into
`Reduce`, and pushes the parameter set
(`InstigatedBy`, `BaseDamage`, `DamageRadius`, `DamageType`, `Momentum`, `HurtOrigin`, `DamageCauser`) into the imported
`Core.TakeRadiusDamageFromWeapon` (import ref -1635). **No token in this body references
the script `TakeDamage`**: the hand-off to the override above is engine-side, so that
step is UNKNOWN. The engine call is recorded as an import reference, which the old trace
dropped.
The body carries **3** aligned function references (`ShouldRadialDamageHit`@13, `AssignCasualty`@33, `TakeRadiusDamageFromWeapon`@236); this section explains the two
engine-side ones above and builds no claim on the rest (§7: aligned is a candidate,
not a call).

### 3.3 Ram / collision - **outgoing** (matches T-DM7 → `out`)

`CalculateAndStoreImpactDamage` (script, 1,532 B) reads only the vehicle's own fields, and
every one of them is an *outgoing* multiplier. Values from `CHAIN.json`, presence from
this body's aligned trace:

| field | shipped (`Batmobile`) | Joker (`JokersBatmobile`) |
|---|---:|---:|
| `BattleModeImpactMaxDamagePow` | 0.5 | 0.666 |
| `BattleModeImpactMaxDamageSpeed` | 540 | 540 |
| `BattleModeImpactMinDamageSpeed` | 120 | 120 |
| `ImpactBoostMod` | 2 | — |
| `ImpactCivilianVehicleMod` | — | — |
| `ImpactMaxDamage` | — | — |
| `ImpactMaxDamagePow` | — | — |
| `ImpactMaxDamageSpeed` | 150 | 180 |
| `ImpactMinDamageSpeed` | 20 | 40 |
| `ImpactStrafeMod` | 2.25 | 0.8 |
| `StafeImpactImpulse` | — | — |

Every field in that table is in this body's trace (11 distinct class fields match
`*Impact*`). A `—` in a value column means no archetype tag carries the field: its
shipped number is whatever the native CDO holds - UNKNOWN from the files.

The body also reads `bBoosting`, `HeavyArmouredVehicle`,
`CurrentStrafeCooldown`, `StrafeCooldown` and the floating `DamageNumbers` UI.
It branches on `bHasAPCStyleWeakSpot` and, on a car, calls `RemoveWeakSpot`; it also gates on `IsChallengeMode`.
The gate `CanBatmobileDoImpactDamage(OtherVehicle)` is native (1 descriptor, 1 `exec<>` string).
This body does **not** reference that gate, so whether the impact is allowed at all is decided
elsewhere - UNKNOWN from here.

#### 3.3.1 Sideswipe - the targeting half (noted 2026-10-26)

The block above decides *how much* damage a hit deals. What decides *which* car is hit is
a second, runtime mechanism on the same class, and it is why no archetype value exists
for it:

| member | type | role |
|---|---|---|
| `SideSwipeTargetsList` | `RInteractionClass` | the candidate set a sideswipe picks from |
| `SideSwipeInSweetSpot` | `bool` | true on the frames the hit lands in the sweet spot |
| `GetSideSwipeTarget(Targets, Direction, out Distance)` | function | picks a target for a direction |
| `GetCurrentSideSwipeTarget()` | function | the target currently held |
| `GetBatmobileDodgeDirection(Target)` | function | the dodge direction for that target |
| `CrushedThisFrame` / `BouncedThisFrame` | `bool` | per-frame contact state |

`OFFSETS.json` carries **0** rows for any of these: they are runtime state and script
functions, not serialised defaults. So the numbers for a ram are the ones in the table
above, while *choosing* the victim and landing in the sweet spot is native and not
readable from the files.

In play the Batmobile does sideswipe traffic and ram it (user, 2026-10-26). The behaviour
is therefore real and the outgoing numbers are decoded; T-DM7 still routes the damage
itself to JC3's own collision response (`out`), and that translation decision is untouched
by this note.

### 3.4 Ram - **incoming**, and unconditional

`TakesDamageFromRam(Target, RamSpeed)` is a **script** function whose whole body is 7
bytes (sha1 `1aa78f331a90f55e8fb9f173dcc80128458f4030`). The walk finds EX_Return@0, EX_True@1, EX_Return@2 and then **4 trailing bytes that do not form a
complete descriptor**. The first two tokens read as `return true`; what the tail does is
**UNKNOWN** - it is not a property reference (the body's aligned refs are 0) and not a
literal (constants: 0), so the earlier reading of it as "a read of the function's own
ReturnValue slot" was not supported by the trace and is withdrawn.

**`return true`, with no condition and no field read.** So the postmortem's statement that
"there is no incoming-impact entry point on the class" is too strong: the entry point
exists and is open. Whatever makes ramming survivable, it is not this function, and no
archetype value can switch it off from here. How the tail is executed is UNKNOWN.

### 3.5 Outgoing weapon damage - archetypes, not rules

Every projectile archetype that carries a damage-related tag, rendered from the **251**
damage rows in `DAMAGE_RULES.json`:

| package | archetype | `Damage` | `DamageRadius` | `MyDamageType` | `TurretShotDamage` |
|---|---|---:|---:|---:|---:|
| `Playable_BatmobileFunhouse_SF` | `Batmobile_EMPMissile_Projectile` | 60 | 0 | -104 | — |
| `Playable_BatmobileFunhouse_SF` | `Batmobile_EMPMissile_Projectile_ForCars` | — | — | — | — |
| `Playable_BatmobileFunhouse_SF` | `Batmobile_Heavy_Cannon_BodyShot_Projectile` | 75 | — | — | — |
| `Playable_BatmobileFunhouse_SF` | `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` | 75 | — | — | 110 |
| `Playable_BatmobileFunhouse_SF` | `Batmobile_Heavy_Cannon_HeadShot_Projectile` | — | — | — | 110 |
| `Playable_BatmobileFunhouse_SF` | `Batmobile_Heavy_Cannon_Primary_Projectile` | 50 | 0 | -104 | 75 |
| `Playable_BatmobileFunhouse_SF` | `Batmobile_Missile_Projectile` | 250 | 0 | -105 | — |
| `Playable_BatmobileFunhouse_SF` | `Batmobile_Tracker_Projectile` | — | 0 | 0 | — |
| `Playable_BatmobileJoker_SF` | `Batmobile_JokerHeavy_Cannon_Projectile` | 250 | 350 | -113 | — |
| `Playable_BatmobileJoker_SF` | `Batmobile_JokerMissile_Projectile` | 250 | 300 | -115 | — |
| `Playable_BatmobileMK2_SF` | `Batmobile_EMPMissile_Projectile` | 60 | 0 | -121 | — |
| `Playable_BatmobileMK2_SF` | `Batmobile_EMPMissile_Projectile_ForCars` | — | — | — | — |
| `Playable_BatmobileMK2_SF` | `Batmobile_Heavy_Cannon_BodyShot_Projectile` | 75 | — | — | — |
| `Playable_BatmobileMK2_SF` | `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` | 75 | — | — | 110 |
| `Playable_BatmobileMK2_SF` | `Batmobile_Heavy_Cannon_HeadShot_Projectile` | — | — | — | 110 |
| `Playable_BatmobileMK2_SF` | `Batmobile_Heavy_Cannon_Primary_Projectile` | 50 | 0 | -121 | 75 |
| `Playable_BatmobileMK2_SF` | `Batmobile_Missile_Projectile` | 250 | 0 | -122 | — |
| `Playable_BatmobileMK2_SF` | `Batmobile_Tracker_Projectile` | — | 0 | 0 | — |
| `Playable_Batmobile_SF` | `Batmobile_EMPMissile_Projectile` | 60 | 0 | -121 | — |
| `Playable_Batmobile_SF` | `Batmobile_EMPMissile_Projectile_ForCars` | — | — | — | — |
| `Playable_Batmobile_SF` | `Batmobile_Heavy_Cannon_BodyShot_Projectile` | 75 | — | — | — |
| `Playable_Batmobile_SF` | `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` | 75 | — | — | 110 |
| `Playable_Batmobile_SF` | `Batmobile_Heavy_Cannon_HeadShot_Projectile` | — | — | — | 110 |
| `Playable_Batmobile_SF` | `Batmobile_Heavy_Cannon_Primary_Projectile` | 50 | 0 | -121 | 75 |
| `Playable_Batmobile_SF` | `Batmobile_Missile_Projectile` | 250 | 0 | -122 | — |
| `Playable_Batmobile_SF` | `Batmobile_Tracker_Projectile` | — | 0 | 0 | — |

An all-`—` row is an archetype that carries none of these four tags; 3 do
not (`Batmobile_EMPMissile_Projectile_ForCars`, `Batmobile_EMPMissile_Projectile_ForCars`, `Batmobile_EMPMissile_Projectile_ForCars`). They are in the record for their
`RProjectile.Impact*` object references only.
**`Projectile.MyDamageType` is not on every projectile:** 14 of the 26 archetypes carry
it (an import reference, e.g. `-104`, `-113`, `-121`), and 12 do not:

- `Batmobile_EMPMissile_Projectile_ForCars` (`Playable_BatmobileFunhouse_SF` package)
- `Batmobile_Heavy_Cannon_BodyShot_Projectile` (`Playable_BatmobileFunhouse_SF` package)
- `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` (`Playable_BatmobileFunhouse_SF` package)
- `Batmobile_Heavy_Cannon_HeadShot_Projectile` (`Playable_BatmobileFunhouse_SF` package)
- `Batmobile_EMPMissile_Projectile_ForCars` (`Playable_BatmobileMK2_SF` package)
- `Batmobile_Heavy_Cannon_BodyShot_Projectile` (`Playable_BatmobileMK2_SF` package)
- `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` (`Playable_BatmobileMK2_SF` package)
- `Batmobile_Heavy_Cannon_HeadShot_Projectile` (`Playable_BatmobileMK2_SF` package)
- `Batmobile_EMPMissile_Projectile_ForCars` (`Playable_Batmobile_SF` package)
- `Batmobile_Heavy_Cannon_BodyShot_Projectile` (`Playable_Batmobile_SF` package)
- `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` (`Playable_Batmobile_SF` package)
- `Batmobile_Heavy_Cannon_HeadShot_Projectile` (`Playable_Batmobile_SF` package)

For those 12 the per-type multiplier is absent from the archetype as well. The damage
class of every projectile that does carry `MyDamageType` lives in that class, not in the
vehicle.

Read the missiles by name, not by family: `Batmobile_Missile_Projectile` is **250** and
`Batmobile_EMPMissile_Projectile` is **60**; the Joker missile is **250**.
The EMP missile is the outlier on the low side, not a second missile class.

### 3.6 Summary table

| damage type | entry point | what scales it | mode |
|---|---|---|---|
| direct hit (bullet, shell, melee) | `TakeDamage` (script) | `GetDamageMod` (native, encounter) × `ArmourModeDamageReduction` (ships **0**), after the weapon-generator pool absorbs it | armoured/battle mode is the only mode gate |
| radial / explosive | `TakeRadiusDamageFromWeapon` (script) | native `ShouldRadialDamageHit` gate, then distance falloff (0.0 / 0.1 / 0.5 / 1.0 / 1500.0) | any |
| ram into the Batmobile | `TakesDamageFromRam` (script) | **none - `return true`**; the body's tail is UNKNOWN | none |
| ram by the Batmobile | `CanBatmobileDoImpactDamage` (native) + `CalculateAndStoreImpactDamage` (script) | speed band 20→150 (120→540 battle), `ImpactStrafeMod` ×2.25, `ImpactBoostMod` ×2, civilian mod, weak-spot removal | pursuit vs battle |
| weapons fired | projectile archetypes (§3.5) | per-archetype `Projectile.Damage` / `TurretShotDamage` / `DamageRadius`; no rule in this class | per weapon |
| cinematic | `TakeDamage` early-out | — | `InCinematicMode` |

## 4. Health, the weapon generator, and the numbers

- **`Pawn.Health` = 1200** on all **3** Batmobile archetypes (`BatmobileFunhouse`, `Batmobile_MK2`, `Batmobile`).
- **Persisted**: `LoadHealth` (script, 319 B) reads
  `BatmobileHealth`, `BatmobileEnergy` and
  `PersistentOptions`, `DDA_DeathsInRoom` - Batmobile health and energy are
  saved, and **dynamic difficulty reads the death count in the room** before deciding
  them. Body literals: `9999999`, `0.0`.
- **The weapon generator is the shield**: `TakeDamage` calls
  `DrainWeaponGeneratorForDamage(DamageAmount, HitNumber)` (script, 322 B), which reads
  `WeaponGeneratorPower`, `bWeaponGeneratorShielding`, `WeaponUnavailableReason`, `bIsJokerfiedBatmobile`, `GetDifficulty`, with body literals
  **8** found, distinct `0.0`, `0.05`, `0.5`, `1.0`, and ends in `IncSteamEffect` + `OverHeat`.
  `WeaponGeneratorPower` is read by **25** script functions in total (the same count the old four-byte test gave).
- **`GiveMaxEnergy`** (24 B) reads `WeaponGeneratorPower` and `MaxWeaponGeneratorPower`
  - the three members of the assignment are in the body: `WeaponGeneratorPower`, `MaxWeaponGeneratorPower`, `CurrentGeneratorLevel`.
- **`QuarterHealth` / `LowHealthWarningLevel`** drive the low-health HUD warning
  (`SetOneShotWarningMessage`); `LowHealthWarningLevel` has exactly **1** reader in the whole package -
  `TakeDamage`.
- **`OnModifyHealth`** (116 B) takes an `Action`, casts the PC and calls
  `InstantUpdateHealth` - that is the **Batsuit** bar (`HUD.md`), not the car's.

## 5. Regeneration - answered: a mechanism exists, its value does not ship

`ARM-5` asked whether BmAK has a regen value. It does, and it is **not** a passive timer:

- `RVehicleBatmobileBase.HealthRecoverRate` is a **`TArray<float>` at +8220** in the class dump
  (`Working\vendor\BmSDK\RVehicleBatmobileBase.g.cs:8874`, `ArrayProperty`).
- **No archetype overrides it** - it is absent from `CHAIN.json` (0 mentions) and from
  the 423-field `OFFSETS.json` binding (0 rows), so the tags carry no value; the shipped
  number is whatever the native CDO in `BmScript` (not shipped) holds.
- Exactly **1** script function in all 29,620 reads it:
  **`ExperienceAwarded`** (180 B), which also reads `GetDifficulty`.

So recovery is **awarded per experience event, indexed by difficulty**, not a
health-per-second regen out of combat, and the rate table itself is not in the files.
Verdict for the row: **mechanism = yes (decoded), value = unknown from the files**
(readable only from a running game's CDO, same class of gap as `CAMERA.md` §2b).

**The `*Regen*` negation, now per class.** The old sentence checked a global name list,
which cannot answer an owner question. The export scan can:

- **70** classes match `^(?:RVehicle|Pawn|AkVehicle)`. Their members matching
  `Regen|Heal|Recover|Restore|Repair|Replenish` number **25**, and **0** of them match
  `Regen`: none.
- The `Regen`-named symbols in the name table, with owners from the BmGame export
  scan: `bRegenerateChildren` owned by `RCrowdSpawnPointMaster` (BoolProperty).
- The 25 vehicle-family members the scan does find are state and restore triggers:
  `RVehicle.GetMaxHealth`, `RVehicle.MaxHealth`, `RVehicleBatmobileBase.EMPRepairable`, `RVehicleBatmobileBase.GetMaxHealth`, `RVehicleBatmobileBase.GiveMaxHealth`, `RVehicleBatmobileBase.HealthRecoverRate`, `RVehicleBatmobileBase.HealthUpdated`, `RVehicleBatmobileBase.LoadHealth`, `RVehicleBatmobileBase.LowHealthWarningLevel`, `RVehicleBatmobileBase.OnModifyHealth`, `RVehicleBehaviour_CommandTankSearch.InitHealthBar`, `RVehicleCar.HealthBarBossName`, `RVehicleCar.HealthBarFlashThreshold`, `RVehicleCar.HealthBarHealth`, `RVehicleCar.HealthBarVisible`, `RVehicleCar.InitialHealth`, `RVehicleCar.OnlyShowHealthBarWhenNoFollowers`, `RVehicleCar.ShowHealthBarWhenTracked`, `RVehicleCar.UpdateHealthBarVisibility`, `RVehicleHeavyTank.StartingHealth`, `RVehicleNPC.UpdateHealthBarVisibility`, `RVehicleNPC.VehicleAsBombHealth`, `RVehicleSimBatmobile.RestoreStopThreshold`, `RVehicleTank.MissileVolleyMaxHealth`, `RVehicleThreatComponent.ShowHealth`.
- Name-table match count for the whole package (superset, `Heal` matches `Health`): **266**.

Corroboration, from the same name table (14 names): `BatmobileHealth`, `CMod_Pos_ReplenishingHealth`, `CanReplenishHealth`, `HealthRecoverRate`, `HealthRecovery`, `KOHealthRegainAmount`, `PDVer_BatmobileHealth`, `Play_BML_LowHealth`, `RestoreArmour`, `RestoreArmourProportional`, `RestoreHealth`, `RestoreHealthAndArmour`, `UpdateReplenishingHealth`, `bReplenishHealth` -
health is a *state* with restore triggers and a persisted version key, not a regenerating
counter. No `*Regen*` member exists on any `RVehicle*`, `Pawn` or `AkVehicle` class (0
of 25 members), and the one `bRegenerateChildren` belongs to a crowd spawner.

The SDK dump, with the class that declares each symbol (19 symbols):

| symbol | classes |
|---|---|
| `DebugRestoreAmmo` | `RInventoryGadget` |
| `EMPRepairable` | `RVehicleBatmobileBase` |
| `GetMaxHealth` | `RVehicle`, `RVehicleBatmobileBase` |
| `GiveMaxHealth` | `RVehicleBatmobileBase` |
| `HealDamage` | `Actor`, `Pawn` |
| `Healer` | `Actor`, `Pawn` |
| `Health` | `Pawn` |
| `HealthMax` | `Pawn` |
| `HealthRecoverRate` | `RVehicleBatmobileBase` |
| `HealthUpdated` | `RVehicleBatmobileBase` |
| `LoadHealth` | `RVehicleBatmobileBase` |
| `LowHealthWarningLevel` | `RVehicleBatmobileBase` |
| `MaxHealth` | `RVehicle` |
| `OnModifyHealth` | `Actor`, `RVehicleBatmobileBase` |
| `RestoreAnimSetsToDefault` | `Pawn` |
| `RestoreOldRopeLengthIfShorter` | `RBatmobileWinch` |
| `RestoreStopThreshold` | `RVehicleSimBatmobile` |
| `SeqAct_ModifyHealth` | `Actor`, `RVehicleBatmobileBase` |
| `bReplicateHealthToAll` | `Pawn` |

## 6. What this corrects in `POSTMORTEM_DAMAGE.md`

1. **T-DM7 → `out` is confirmed.** Every field `CalculateAndStoreImpactDamage` reads is
   an outgoing multiplier (`Impact*`, `BattleModeImpact*`, strafe/boost/civilian mods);
   the class still has no *scaling* expression for incoming impact damage.
2. **But the sentence "there is no incoming-impact entry point on the class" is wrong.**
   `TakesDamageFromRam` is exactly that entry point, it is script, and its body begins
   with `return true`. Incoming-impact immunity therefore cannot be a value row here.
   What its trailing 4 bytes do is UNKNOWN.
3. **The armour-mode reduction is real but shipped at zero.** `ArmourModeDamageReduction`
   = `0` is *not* an undeclared switch: that is the value the archetype authors set,
   and `TakeDamage` is its only reader. The undeclared switches remain the ones the
   postmortem listed
   (`impact_damage_factor`, `impact_armor`, `deform_scale`, …) - those live in the
   **JC3** build, not in BmAK.
4. **`ShouldRadialDamageHit` is native, so "how a radial hit is decided" cannot be
   answered from script.** Any claim about it needs the exe, and it belongs in `G1-22`.

## 7. Open, honestly

- `HealthRecoverRate[difficulty]` values → needs the running game's CDO (`G1-22` / a probe).
- `GetDamageMod` is native: the encounter scaling behind ARM-2's hits-to-kill is in
  `BatmanAK.exe` (`execGetDamageMod`), not in script. `G2-28` needs this number.
- The per-`DamageType` multipliers live in the damage classes (each projectile's
  `MyDamageType` import); those classes are engine-side and were not opened here.
- **The trace is token-aligned, not decoded.** `walk()` accepts a reference/literal only
  at a byte where no earlier accepted token covers it, and leaves every other byte
  unnamed: **71** reference candidates are unaligned across the 14 traced functions
  (sampled under `functions.*.walk.unaligned_sample`) and 1235 body bytes belong to no
  recognised token. That is the difference between "a token references X" and "these
  four bytes occur somewhere": the old trace listed `PawnDied` and `SetupResolution` as
  calls of a distance-falloff function, and the walk shows both were unaligned.
  No reader count or call claim in this note comes from an unaligned candidate.
- **Literals are candidates, not an expression tree.** The walk finds each `EX_IntConst`
  / `EX_FloatConst` at an aligned offset; it does not prove which operand the compiler
  built it for. Branches, jump offsets and nesting are not resolved into source, so where
  §3 says "gates" or "afterwards" it is following byte order, not a disassembled AST.
- `read_by` is now token-aligned; the old containment count is kept beside it per field
  (`field_references.*.containment_only`), so no reader claim rests on four bytes.
- **Aligned is still a candidate, not a call.** A recognised token can sit after a byte
  the size table does not cover, so an aligned name can be a mis-parse. The walk must not
  be read as a decompiler; every count in this note is a token count, and each name it
  uses is also present in the record with its offset so a reader can re-check it.

## 8. Tool and gates

```
python Tools/scripts/bmak_damage.py --write    # JSON + this note + the raw bodies
python Tools/scripts/bmak_damage.py --check    # re-derive, diff both, assert the anchors
```

`--check` prints the anchor dict, `anchors true: 7/7`, `json: PASS|FAIL`,
`md: PASS|FAIL` and `check: PASS|FAIL`, and exits 1 if any anchor is `False`, if the
JSON differs, or if this file differs by a byte.

`DAMAGE_RULES.json` carries the layout, the anchors, the `exec<>` counts, all 14 traced
functions (offsets, symbols, constants, walk summary, sha1s), the package stats, 251
damage values, the per-field reader lists and the per-class regen scan. Raw bytecode stays
in `Working/vendor/BmAKgrab/scripts/` (14 files), outside this folder, by the same rule
that keeps the animation keys and bone face lists outside the notes.

## Appendix A. Every damage-related field (251 rows)

The selection is the tool's own field regex (`health|damage|armou?r|regen|heal|recover|
death|die|dying|destroy|explos|bullet|melee|smoke|burn|impact|invuln|fragil|deform|kill`,
case-insensitive) over every archetype tag in `CHAIN.json`. `named_by` is the binding that
gave the row its name (`sdk-layout` = class-dump layout, `stream` = the tag stream itself).

| class | archetype | field | type | value | named_by |
|---|---|---|---|---:|---|
| `RBasicProjectile` | `Playable_BatmobileFunhouse_SF.Batmobile_Heavy_Cannon_BodyShot_Projectile` | `Projectile.Damage` | FloatProperty | 75 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileFunhouse_SF.Batmobile_Heavy_Cannon_BodyShot_Projectile` | `RBasicProjectile.ImpactExplosion` | ObjectNCRProperty | 5041 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileFunhouse_SF.Batmobile_Heavy_Cannon_BodyShot_Projectile` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 5190 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileFunhouse_SF.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` | `Projectile.Damage` | FloatProperty | 75 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileFunhouse_SF.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` | `RBasicProjectile.ImpactExplosion` | ObjectNCRProperty | 5042 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileFunhouse_SF.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` | `RBasicProjectile.TurretShotDamage` | IntProperty | 110 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileFunhouse_SF.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 5191 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileFunhouse_SF.Batmobile_Heavy_Cannon_HeadShot_Projectile` | `RBasicProjectile.ImpactExplosion` | ObjectNCRProperty | 5043 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileFunhouse_SF.Batmobile_Heavy_Cannon_HeadShot_Projectile` | `RBasicProjectile.TurretShotDamage` | IntProperty | 110 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileFunhouse_SF.Batmobile_Heavy_Cannon_HeadShot_Projectile` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 5192 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileFunhouse_SF.Batmobile_Heavy_Cannon_Primary_Projectile` | `Projectile.Damage` | FloatProperty | 50 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileFunhouse_SF.Batmobile_Heavy_Cannon_Primary_Projectile` | `Projectile.DamageRadius` | FloatProperty | 0 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileFunhouse_SF.Batmobile_Heavy_Cannon_Primary_Projectile` | `Projectile.MyDamageType` | ObjectNCRProperty | -104 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileFunhouse_SF.Batmobile_Heavy_Cannon_Primary_Projectile` | `RBasicProjectile.ImpactExplosion` | ObjectNCRProperty | 5033 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileFunhouse_SF.Batmobile_Heavy_Cannon_Primary_Projectile` | `RBasicProjectile.ImpactExplosionSound` | ObjectNCRProperty | 120 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileFunhouse_SF.Batmobile_Heavy_Cannon_Primary_Projectile` | `RBasicProjectile.TurretShotDamage` | IntProperty | 75 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileFunhouse_SF.Batmobile_Heavy_Cannon_Primary_Projectile` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 14 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileJoker_SF.Batmobile_JokerHeavy_Cannon_Projectile` | `Projectile.Damage` | FloatProperty | 250 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileJoker_SF.Batmobile_JokerHeavy_Cannon_Projectile` | `Projectile.DamageRadius` | FloatProperty | 350 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileJoker_SF.Batmobile_JokerHeavy_Cannon_Projectile` | `Projectile.MyDamageType` | ObjectNCRProperty | -113 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileJoker_SF.Batmobile_JokerHeavy_Cannon_Projectile` | `RBasicProjectile.ImpactExplosion` | ObjectNCRProperty | -543 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileJoker_SF.Batmobile_JokerHeavy_Cannon_Projectile` | `RBasicProjectile.ImpactExplosionSound` | ObjectNCRProperty | 252 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileJoker_SF.Batmobile_JokerHeavy_Cannon_Projectile` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 3121 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileMK2_SF.Batmobile_Heavy_Cannon_BodyShot_Projectile` | `Projectile.Damage` | FloatProperty | 75 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileMK2_SF.Batmobile_Heavy_Cannon_BodyShot_Projectile` | `RBasicProjectile.ImpactExplosion` | ObjectNCRProperty | 5001 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileMK2_SF.Batmobile_Heavy_Cannon_BodyShot_Projectile` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 5151 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileMK2_SF.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` | `Projectile.Damage` | FloatProperty | 75 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileMK2_SF.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` | `RBasicProjectile.ImpactExplosion` | ObjectNCRProperty | 5002 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileMK2_SF.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` | `RBasicProjectile.TurretShotDamage` | IntProperty | 110 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileMK2_SF.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 5152 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileMK2_SF.Batmobile_Heavy_Cannon_HeadShot_Projectile` | `RBasicProjectile.ImpactExplosion` | ObjectNCRProperty | 5003 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileMK2_SF.Batmobile_Heavy_Cannon_HeadShot_Projectile` | `RBasicProjectile.TurretShotDamage` | IntProperty | 110 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileMK2_SF.Batmobile_Heavy_Cannon_HeadShot_Projectile` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 5153 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileMK2_SF.Batmobile_Heavy_Cannon_Primary_Projectile` | `Projectile.Damage` | FloatProperty | 50 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileMK2_SF.Batmobile_Heavy_Cannon_Primary_Projectile` | `Projectile.DamageRadius` | FloatProperty | 0 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileMK2_SF.Batmobile_Heavy_Cannon_Primary_Projectile` | `Projectile.MyDamageType` | ObjectNCRProperty | -121 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileMK2_SF.Batmobile_Heavy_Cannon_Primary_Projectile` | `RBasicProjectile.ImpactExplosion` | ObjectNCRProperty | 4993 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileMK2_SF.Batmobile_Heavy_Cannon_Primary_Projectile` | `RBasicProjectile.ImpactExplosionSound` | ObjectNCRProperty | 121 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileMK2_SF.Batmobile_Heavy_Cannon_Primary_Projectile` | `RBasicProjectile.TurretShotDamage` | IntProperty | 75 | sdk-layout |
| `RBasicProjectile` | `Playable_BatmobileMK2_SF.Batmobile_Heavy_Cannon_Primary_Projectile` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 14 | sdk-layout |
| `RBasicProjectile` | `Playable_Batmobile_SF.Batmobile_Heavy_Cannon_BodyShot_Projectile` | `Projectile.Damage` | FloatProperty | 75 | sdk-layout |
| `RBasicProjectile` | `Playable_Batmobile_SF.Batmobile_Heavy_Cannon_BodyShot_Projectile` | `RBasicProjectile.ImpactExplosion` | ObjectNCRProperty | 4950 | sdk-layout |
| `RBasicProjectile` | `Playable_Batmobile_SF.Batmobile_Heavy_Cannon_BodyShot_Projectile` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 5100 | sdk-layout |
| `RBasicProjectile` | `Playable_Batmobile_SF.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` | `Projectile.Damage` | FloatProperty | 75 | sdk-layout |
| `RBasicProjectile` | `Playable_Batmobile_SF.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` | `RBasicProjectile.ImpactExplosion` | ObjectNCRProperty | 4951 | sdk-layout |
| `RBasicProjectile` | `Playable_Batmobile_SF.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` | `RBasicProjectile.TurretShotDamage` | IntProperty | 110 | sdk-layout |
| `RBasicProjectile` | `Playable_Batmobile_SF.Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 5101 | sdk-layout |
| `RBasicProjectile` | `Playable_Batmobile_SF.Batmobile_Heavy_Cannon_HeadShot_Projectile` | `RBasicProjectile.ImpactExplosion` | ObjectNCRProperty | 4952 | sdk-layout |
| `RBasicProjectile` | `Playable_Batmobile_SF.Batmobile_Heavy_Cannon_HeadShot_Projectile` | `RBasicProjectile.TurretShotDamage` | IntProperty | 110 | sdk-layout |
| `RBasicProjectile` | `Playable_Batmobile_SF.Batmobile_Heavy_Cannon_HeadShot_Projectile` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 5102 | sdk-layout |
| `RBasicProjectile` | `Playable_Batmobile_SF.Batmobile_Heavy_Cannon_Primary_Projectile` | `Projectile.Damage` | FloatProperty | 50 | sdk-layout |
| `RBasicProjectile` | `Playable_Batmobile_SF.Batmobile_Heavy_Cannon_Primary_Projectile` | `Projectile.DamageRadius` | FloatProperty | 0 | sdk-layout |
| `RBasicProjectile` | `Playable_Batmobile_SF.Batmobile_Heavy_Cannon_Primary_Projectile` | `Projectile.MyDamageType` | ObjectNCRProperty | -121 | sdk-layout |
| `RBasicProjectile` | `Playable_Batmobile_SF.Batmobile_Heavy_Cannon_Primary_Projectile` | `RBasicProjectile.ImpactExplosion` | ObjectNCRProperty | 4942 | sdk-layout |
| `RBasicProjectile` | `Playable_Batmobile_SF.Batmobile_Heavy_Cannon_Primary_Projectile` | `RBasicProjectile.ImpactExplosionSound` | ObjectNCRProperty | 122 | sdk-layout |
| `RBasicProjectile` | `Playable_Batmobile_SF.Batmobile_Heavy_Cannon_Primary_Projectile` | `RBasicProjectile.TurretShotDamage` | IntProperty | 75 | sdk-layout |
| `RBasicProjectile` | `Playable_Batmobile_SF.Batmobile_Heavy_Cannon_Primary_Projectile` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 14 | sdk-layout |
| `RBatmobileCannon` | `Playable_BatmobileFunhouse_SF.Batmobile_Cannon_V2` | `RBatmobileCannon.ChainGunDamage` | IntProperty | 40 | sdk-layout |
| `RBatmobileCannon` | `Playable_BatmobileFunhouse_SF.Batmobile_Cannon_V2` | `RBatmobileCannon.ImpactMomentum` | FloatProperty | 60000 | sdk-layout |
| `RBatmobileCannon` | `Playable_BatmobileFunhouse_SF.Batmobile_Cannon_V2` | `RBatmobileCannon.RiotSuppressorImpactEffect` | ObjectNCRProperty | 5065 | sdk-layout |
| `RBatmobileCannon` | `Playable_BatmobileFunhouse_SF.Batmobile_Cannon_V2` | `RBatmobileCannon.UpgradedDamage` | IntProperty | 50 | sdk-layout |
| `RBatmobileCannon` | `Playable_BatmobileJoker_SF.Batmobile_Cannon_V2` | `RBatmobileCannon.ChainGunDamage` | IntProperty | 40 | sdk-layout |
| `RBatmobileCannon` | `Playable_BatmobileJoker_SF.Batmobile_Cannon_V2` | `RBatmobileCannon.ImpactMomentum` | FloatProperty | 60000 | sdk-layout |
| `RBatmobileCannon` | `Playable_BatmobileJoker_SF.Batmobile_Cannon_V2` | `RBatmobileCannon.RiotSuppressorImpactEffect` | ObjectNCRProperty | 2930 | sdk-layout |
| `RBatmobileCannon` | `Playable_BatmobileJoker_SF.Batmobile_Cannon_V2` | `RBatmobileCannon.UpgradedDamage` | IntProperty | 50 | sdk-layout |
| `RBatmobileCannon` | `Playable_BatmobileJoker_SF.Batmobile_JokerCannon_V2` | `RBatmobileCannon.ChainGunDamage` | IntProperty | 999 | sdk-layout |
| `RBatmobileCannon` | `Playable_BatmobileJoker_SF.Batmobile_JokerCannon_V2` | `RBatmobileCannon.ImpactMomentum` | FloatProperty | 2000 | sdk-layout |
| `RBatmobileCannon` | `Playable_BatmobileMK2_SF.Batmobile_Cannon_V2` | `RBatmobileCannon.ChainGunDamage` | IntProperty | 40 | sdk-layout |
| `RBatmobileCannon` | `Playable_BatmobileMK2_SF.Batmobile_Cannon_V2` | `RBatmobileCannon.ImpactMomentum` | FloatProperty | 60000 | sdk-layout |
| `RBatmobileCannon` | `Playable_BatmobileMK2_SF.Batmobile_Cannon_V2` | `RBatmobileCannon.RiotSuppressorImpactEffect` | ObjectNCRProperty | 5025 | sdk-layout |
| `RBatmobileCannon` | `Playable_BatmobileMK2_SF.Batmobile_Cannon_V2` | `RBatmobileCannon.UpgradedDamage` | IntProperty | 50 | sdk-layout |
| `RBatmobileCannon` | `Playable_Batmobile_SF.Batmobile_Cannon_V2` | `RBatmobileCannon.ChainGunDamage` | IntProperty | 40 | sdk-layout |
| `RBatmobileCannon` | `Playable_Batmobile_SF.Batmobile_Cannon_V2` | `RBatmobileCannon.ImpactMomentum` | FloatProperty | 60000 | sdk-layout |
| `RBatmobileCannon` | `Playable_Batmobile_SF.Batmobile_Cannon_V2` | `RBatmobileCannon.RiotSuppressorImpactEffect` | ObjectNCRProperty | 4974 | sdk-layout |
| `RBatmobileCannon` | `Playable_Batmobile_SF.Batmobile_Cannon_V2` | `RBatmobileCannon.UpgradedDamage` | IntProperty | 50 | sdk-layout |
| `RBatmobileHeavyCannon` | `Playable_BatmobileFunhouse_SF.Batmobile_Heavy_Cannon_Primary` | `RBatmobileHeavyCannon.ChargeMaxDamageRadius` | FloatProperty | 0 | sdk-layout |
| `RBatmobileHeavyCannon` | `Playable_BatmobileJoker_SF.Batmobile_JokerHeavy_Cannon` | `RBatmobileHeavyCannon.ChargeMaxDamageRadius` | FloatProperty | 0 | sdk-layout |
| `RBatmobileHeavyCannon` | `Playable_BatmobileMK2_SF.Batmobile_Heavy_Cannon_Primary` | `RBatmobileHeavyCannon.ChargeMaxDamageRadius` | FloatProperty | 0 | sdk-layout |
| `RBatmobileHeavyCannon` | `Playable_Batmobile_SF.Batmobile_Heavy_Cannon_Primary` | `RBatmobileHeavyCannon.ChargeMaxDamageRadius` | FloatProperty | 0 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileFunhouse_SF.Batmobile_EMPMissile_Projectile` | `Projectile.Damage` | FloatProperty | 60 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileFunhouse_SF.Batmobile_EMPMissile_Projectile` | `Projectile.DamageRadius` | FloatProperty | 0 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileFunhouse_SF.Batmobile_EMPMissile_Projectile` | `Projectile.MyDamageType` | ObjectNCRProperty | -104 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileFunhouse_SF.Batmobile_EMPMissile_Projectile` | `RBatmobileMissile.ExplosionTemplate` | ObjectNCRProperty | 5067 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileFunhouse_SF.Batmobile_EMPMissile_Projectile` | `RProjectile.ImpactExplosionFlameTrail` | ObjectNCRProperty | 5075 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileFunhouse_SF.Batmobile_EMPMissile_Projectile` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 13 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileFunhouse_SF.Batmobile_EMPMissile_Projectile_ForCars` | `RBatmobileMissile.ExplosionTemplate` | ObjectNCRProperty | 5068 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileFunhouse_SF.Batmobile_EMPMissile_Projectile_ForCars` | `RProjectile.ImpactExplosionFlameTrail` | ObjectNCRProperty | 5076 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileFunhouse_SF.Batmobile_EMPMissile_Projectile_ForCars` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 5189 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileFunhouse_SF.Batmobile_Missile_Projectile` | `Projectile.Damage` | FloatProperty | 250 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileFunhouse_SF.Batmobile_Missile_Projectile` | `Projectile.DamageRadius` | FloatProperty | 0 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileFunhouse_SF.Batmobile_Missile_Projectile` | `Projectile.MyDamageType` | ObjectNCRProperty | -105 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileFunhouse_SF.Batmobile_Missile_Projectile` | `RBatmobileMissile.ExplosionTemplate` | ObjectNCRProperty | 5067 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileFunhouse_SF.Batmobile_Missile_Projectile` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 5193 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileFunhouse_SF.Batmobile_Tracker_Projectile` | `Projectile.DamageRadius` | FloatProperty | 0 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileFunhouse_SF.Batmobile_Tracker_Projectile` | `Projectile.MyDamageType` | ObjectNCRProperty | 0 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileFunhouse_SF.Batmobile_Tracker_Projectile` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 5194 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileJoker_SF.Batmobile_JokerMissile_Projectile` | `Projectile.Damage` | FloatProperty | 250 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileJoker_SF.Batmobile_JokerMissile_Projectile` | `Projectile.DamageRadius` | FloatProperty | 300 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileJoker_SF.Batmobile_JokerMissile_Projectile` | `Projectile.MyDamageType` | ObjectNCRProperty | -115 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileJoker_SF.Batmobile_JokerMissile_Projectile` | `RBatmobileMissile.ExplosionTemplate` | ObjectNCRProperty | 2932 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileJoker_SF.Batmobile_JokerMissile_Projectile` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 3122 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileMK2_SF.Batmobile_EMPMissile_Projectile` | `Projectile.Damage` | FloatProperty | 60 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileMK2_SF.Batmobile_EMPMissile_Projectile` | `Projectile.DamageRadius` | FloatProperty | 0 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileMK2_SF.Batmobile_EMPMissile_Projectile` | `Projectile.MyDamageType` | ObjectNCRProperty | -121 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileMK2_SF.Batmobile_EMPMissile_Projectile` | `RBatmobileMissile.ExplosionTemplate` | ObjectNCRProperty | 5027 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileMK2_SF.Batmobile_EMPMissile_Projectile` | `RProjectile.ImpactExplosionFlameTrail` | ObjectNCRProperty | 5035 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileMK2_SF.Batmobile_EMPMissile_Projectile` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 13 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileMK2_SF.Batmobile_EMPMissile_Projectile_ForCars` | `RBatmobileMissile.ExplosionTemplate` | ObjectNCRProperty | 5028 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileMK2_SF.Batmobile_EMPMissile_Projectile_ForCars` | `RProjectile.ImpactExplosionFlameTrail` | ObjectNCRProperty | 5036 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileMK2_SF.Batmobile_EMPMissile_Projectile_ForCars` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 5150 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileMK2_SF.Batmobile_Missile_Projectile` | `Projectile.Damage` | FloatProperty | 250 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileMK2_SF.Batmobile_Missile_Projectile` | `Projectile.DamageRadius` | FloatProperty | 0 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileMK2_SF.Batmobile_Missile_Projectile` | `Projectile.MyDamageType` | ObjectNCRProperty | -122 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileMK2_SF.Batmobile_Missile_Projectile` | `RBatmobileMissile.ExplosionTemplate` | ObjectNCRProperty | 5027 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileMK2_SF.Batmobile_Missile_Projectile` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 5154 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileMK2_SF.Batmobile_Tracker_Projectile` | `Projectile.DamageRadius` | FloatProperty | 0 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileMK2_SF.Batmobile_Tracker_Projectile` | `Projectile.MyDamageType` | ObjectNCRProperty | 0 | sdk-layout |
| `RBatmobileMissile` | `Playable_BatmobileMK2_SF.Batmobile_Tracker_Projectile` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 5155 | sdk-layout |
| `RBatmobileMissile` | `Playable_Batmobile_SF.Batmobile_EMPMissile_Projectile` | `Projectile.Damage` | FloatProperty | 60 | sdk-layout |
| `RBatmobileMissile` | `Playable_Batmobile_SF.Batmobile_EMPMissile_Projectile` | `Projectile.DamageRadius` | FloatProperty | 0 | sdk-layout |
| `RBatmobileMissile` | `Playable_Batmobile_SF.Batmobile_EMPMissile_Projectile` | `Projectile.MyDamageType` | ObjectNCRProperty | -121 | sdk-layout |
| `RBatmobileMissile` | `Playable_Batmobile_SF.Batmobile_EMPMissile_Projectile` | `RBatmobileMissile.ExplosionTemplate` | ObjectNCRProperty | 4976 | sdk-layout |
| `RBatmobileMissile` | `Playable_Batmobile_SF.Batmobile_EMPMissile_Projectile` | `RProjectile.ImpactExplosionFlameTrail` | ObjectNCRProperty | 4984 | sdk-layout |
| `RBatmobileMissile` | `Playable_Batmobile_SF.Batmobile_EMPMissile_Projectile` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 13 | sdk-layout |
| `RBatmobileMissile` | `Playable_Batmobile_SF.Batmobile_EMPMissile_Projectile_ForCars` | `RBatmobileMissile.ExplosionTemplate` | ObjectNCRProperty | 4977 | sdk-layout |
| `RBatmobileMissile` | `Playable_Batmobile_SF.Batmobile_EMPMissile_Projectile_ForCars` | `RProjectile.ImpactExplosionFlameTrail` | ObjectNCRProperty | 4985 | sdk-layout |
| `RBatmobileMissile` | `Playable_Batmobile_SF.Batmobile_EMPMissile_Projectile_ForCars` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 5099 | sdk-layout |
| `RBatmobileMissile` | `Playable_Batmobile_SF.Batmobile_Missile_Projectile` | `Projectile.Damage` | FloatProperty | 250 | sdk-layout |
| `RBatmobileMissile` | `Playable_Batmobile_SF.Batmobile_Missile_Projectile` | `Projectile.DamageRadius` | FloatProperty | 0 | sdk-layout |
| `RBatmobileMissile` | `Playable_Batmobile_SF.Batmobile_Missile_Projectile` | `Projectile.MyDamageType` | ObjectNCRProperty | -122 | sdk-layout |
| `RBatmobileMissile` | `Playable_Batmobile_SF.Batmobile_Missile_Projectile` | `RBatmobileMissile.ExplosionTemplate` | ObjectNCRProperty | 4976 | sdk-layout |
| `RBatmobileMissile` | `Playable_Batmobile_SF.Batmobile_Missile_Projectile` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 5103 | sdk-layout |
| `RBatmobileMissile` | `Playable_Batmobile_SF.Batmobile_Tracker_Projectile` | `Projectile.DamageRadius` | FloatProperty | 0 | sdk-layout |
| `RBatmobileMissile` | `Playable_Batmobile_SF.Batmobile_Tracker_Projectile` | `Projectile.MyDamageType` | ObjectNCRProperty | 0 | sdk-layout |
| `RBatmobileMissile` | `Playable_Batmobile_SF.Batmobile_Tracker_Projectile` | `RProjectile.ImpactRadialImpulseComponent` | ObjectNCRProperty | 5104 | sdk-layout |
| `RBatmobileMissileLauncher` | `Playable_BatmobileFunhouse_SF.Batmobile_Missile_Launcher` | `RBatmobileMissileLauncher.FinalExplosionSweetener` | ObjectNCRProperty | 123 | sdk-layout |
| `RBatmobileMissileLauncher` | `Playable_BatmobileMK2_SF.Batmobile_Missile_Launcher` | `RBatmobileMissileLauncher.FinalExplosionSweetener` | ObjectNCRProperty | 124 | sdk-layout |
| `RBatmobileMissileLauncher` | `Playable_Batmobile_SF.Batmobile_Missile_Launcher` | `RBatmobileMissileLauncher.FinalExplosionSweetener` | ObjectNCRProperty | 125 | sdk-layout |
| `RBatmobileWinch` | `Playable_BatmobileFunhouse_SF.Batmobile_Winch` | `RBatmobileWinch.ImpactEffect` | ObjectNCRProperty | 5072 | sdk-layout |
| `RBatmobileWinch` | `Playable_BatmobileFunhouse_SF.Batmobile_Winch` | `RBatmobileWinch.ImpactSound` | ObjectNCRProperty | -65 | sdk-layout |
| `RBatmobileWinch` | `Playable_BatmobileMK2_SF.Batmobile_Winch` | `RBatmobileWinch.ImpactEffect` | ObjectNCRProperty | 5032 | sdk-layout |
| `RBatmobileWinch` | `Playable_BatmobileMK2_SF.Batmobile_Winch` | `RBatmobileWinch.ImpactSound` | ObjectNCRProperty | -56 | sdk-layout |
| `RBatmobileWinch` | `Playable_Batmobile_SF.Batmobile_Winch` | `RBatmobileWinch.ImpactEffect` | ObjectNCRProperty | 4981 | sdk-layout |
| `RBatmobileWinch` | `Playable_Batmobile_SF.Batmobile_Winch` | `RBatmobileWinch.ImpactSound` | ObjectNCRProperty | -56 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `DeathExplosionSoundArray` | ArrayProperty | — | stream |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `ExplosiveImpactScreenShake` | StructProperty | — | stream |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `ImpactShake` | StructProperty | — | stream |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `Pawn.Health` | IntProperty | 1200 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicle.VisualDamageComp` | ObjectNCRProperty | 5369 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicleBatmobileBase.AfterburnerSystem` | ObjectNCRProperty | 5094 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicleBatmobileBase.AfterburnerWarmupSystem` | ObjectNCRProperty | 5095 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicleBatmobileBase.ArmourModeDamageReduction` | IntProperty | 0 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicleBatmobileBase.BattleModeImpactMaxDamagePow` | FloatProperty | 0.5 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicleBatmobileBase.BattleModeImpactMaxDamageSpeed` | FloatProperty | 540 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicleBatmobileBase.BattleModeImpactMinDamageSpeed` | FloatProperty | 120 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicleBatmobileBase.DeathExplosion` | ObjectNCRProperty | 5077 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicleBatmobileBase.ImpactBoostMod` | FloatProperty | 2 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicleBatmobileBase.ImpactMaxDamageSpeed` | FloatProperty | 150 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicleBatmobileBase.ImpactMinDamageSpeed` | FloatProperty | 20 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicleBatmobileBase.ImpactRoadAssistAngleStrength` | FloatProperty | 2000 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicleBatmobileBase.ImpactRoadAssistEnemyDuration` | FloatProperty | 0.333 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicleBatmobileBase.ImpactRoadAssistFactor` | FloatProperty | 90000 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicleBatmobileBase.ImpactRoadAssistMaxTorque` | FloatProperty | 30000 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicleBatmobileBase.ImpactRoadAssistSceneryDuration` | FloatProperty | 0 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicleBatmobileBase.ImpactShakeForceFactor` | FloatProperty | 0.01333 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicleBatmobileBase.ImpactShakeVehicleFactor` | FloatProperty | 1.5 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicleBatmobileBase.ImpactStrafeMod` | FloatProperty | 2.25 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicleBatmobileBase.KillFlipTorque` | FloatProperty | -200 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicleBatmobileBase.KillFlipTorqueDuration` | FloatProperty | 0.5 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicleBatmobileBase.KillKeepyUpFactor` | FloatProperty | 10 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicleBatmobileBase.KillKeepyUpFactorDuration` | FloatProperty | 0.75 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `DeathExplosionSoundArray` | ArrayProperty | — | stream |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `ExplosiveImpactScreenShake` | StructProperty | — | stream |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `ImpactShake` | StructProperty | — | stream |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `RVehicle.VisualDamageComp` | ObjectNCRProperty | 3183 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `RVehicleBatmobileBase.AfterburnerSystem` | ObjectNCRProperty | 2944 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `RVehicleBatmobileBase.AfterburnerWarmupSystem` | ObjectNCRProperty | 2945 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `RVehicleBatmobileBase.BattleModeImpactMaxDamagePow` | FloatProperty | 0.666 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `RVehicleBatmobileBase.BattleModeImpactMaxDamageSpeed` | FloatProperty | 540 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `RVehicleBatmobileBase.BattleModeImpactMinDamageSpeed` | FloatProperty | 120 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `RVehicleBatmobileBase.DeathExplosion` | ObjectNCRProperty | 2941 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `RVehicleBatmobileBase.ImpactMaxDamageSpeed` | FloatProperty | 180 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `RVehicleBatmobileBase.ImpactMinDamageSpeed` | FloatProperty | 40 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `RVehicleBatmobileBase.ImpactRoadAssistAngleStrength` | FloatProperty | 2000 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `RVehicleBatmobileBase.ImpactRoadAssistEnemyDuration` | FloatProperty | 0.75 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `RVehicleBatmobileBase.ImpactRoadAssistFactor` | FloatProperty | 90000 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `RVehicleBatmobileBase.ImpactRoadAssistMaxTorque` | FloatProperty | 30000 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `RVehicleBatmobileBase.ImpactRoadAssistSceneryDuration` | FloatProperty | 0.33 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `RVehicleBatmobileBase.ImpactShakeForceFactor` | FloatProperty | 0.01333 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `RVehicleBatmobileBase.ImpactShakeVehicleFactor` | FloatProperty | 1.5 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `RVehicleBatmobileBase.ImpactStrafeMod` | FloatProperty | 0.8 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `RVehicleBatmobileBase.KillFlipTorque` | FloatProperty | -400 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `RVehicleBatmobileBase.KillFlipTorqueDuration` | FloatProperty | 0.75 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `RVehicleBatmobileBase.KillKeepyUpFactor` | FloatProperty | 10 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `RVehicleBatmobileBase.KillKeepyUpFactorDuration` | FloatProperty | 0.75 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `RVehicleBatmobileBase.WeaponGeneratorKillBonus` | FloatProperty | 0 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileJoker_SF.JokersBatmobile` | `RVehicleBatmobileBase.WeaponGeneratorThugKillBonus` | FloatProperty | 0.03 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `DeathExplosionSoundArray` | ArrayProperty | — | stream |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `ExplosiveImpactScreenShake` | StructProperty | — | stream |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `ImpactShake` | StructProperty | — | stream |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `Pawn.Health` | IntProperty | 1200 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `RVehicle.VisualDamageComp` | ObjectNCRProperty | 5334 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `RVehicleBatmobileBase.AfterburnerSystem` | ObjectNCRProperty | 5054 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `RVehicleBatmobileBase.AfterburnerWarmupSystem` | ObjectNCRProperty | 5055 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `RVehicleBatmobileBase.ArmourModeDamageReduction` | IntProperty | 0 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `RVehicleBatmobileBase.BattleModeImpactMaxDamagePow` | FloatProperty | 0.5 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `RVehicleBatmobileBase.BattleModeImpactMaxDamageSpeed` | FloatProperty | 540 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `RVehicleBatmobileBase.BattleModeImpactMinDamageSpeed` | FloatProperty | 120 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `RVehicleBatmobileBase.DeathExplosion` | ObjectNCRProperty | 5037 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `RVehicleBatmobileBase.ImpactBoostMod` | FloatProperty | 2 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `RVehicleBatmobileBase.ImpactMaxDamageSpeed` | FloatProperty | 150 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `RVehicleBatmobileBase.ImpactMinDamageSpeed` | FloatProperty | 20 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `RVehicleBatmobileBase.ImpactRoadAssistAngleStrength` | FloatProperty | 2000 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `RVehicleBatmobileBase.ImpactRoadAssistEnemyDuration` | FloatProperty | 0.333 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `RVehicleBatmobileBase.ImpactRoadAssistFactor` | FloatProperty | 90000 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `RVehicleBatmobileBase.ImpactRoadAssistMaxTorque` | FloatProperty | 30000 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `RVehicleBatmobileBase.ImpactRoadAssistSceneryDuration` | FloatProperty | 0 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `RVehicleBatmobileBase.ImpactShakeForceFactor` | FloatProperty | 0.01333 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `RVehicleBatmobileBase.ImpactShakeVehicleFactor` | FloatProperty | 1.5 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `RVehicleBatmobileBase.ImpactStrafeMod` | FloatProperty | 2.25 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `RVehicleBatmobileBase.KillFlipTorque` | FloatProperty | -200 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `RVehicleBatmobileBase.KillFlipTorqueDuration` | FloatProperty | 0.5 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `RVehicleBatmobileBase.KillKeepyUpFactor` | FloatProperty | 10 | sdk-layout |
| `RVehicleBatmobile` | `Playable_BatmobileMK2_SF.Batmobile_MK2` | `RVehicleBatmobileBase.KillKeepyUpFactorDuration` | FloatProperty | 0.75 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `DeathExplosionSoundArray` | ArrayProperty | — | stream |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `ExplosiveImpactScreenShake` | StructProperty | — | stream |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `ImpactShake` | StructProperty | — | stream |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `Pawn.Health` | IntProperty | 1200 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `RVehicle.VisualDamageComp` | ObjectNCRProperty | 5283 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `RVehicleBatmobileBase.AfterburnerSystem` | ObjectNCRProperty | 4993 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `RVehicleBatmobileBase.AfterburnerWarmupSystem` | ObjectNCRProperty | 4994 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `RVehicleBatmobileBase.ArmourModeDamageReduction` | IntProperty | 0 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `RVehicleBatmobileBase.BattleModeImpactMaxDamagePow` | FloatProperty | 0.5 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `RVehicleBatmobileBase.BattleModeImpactMaxDamageSpeed` | FloatProperty | 540 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `RVehicleBatmobileBase.BattleModeImpactMinDamageSpeed` | FloatProperty | 120 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `RVehicleBatmobileBase.DeathExplosion` | ObjectNCRProperty | 4986 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `RVehicleBatmobileBase.ImpactBoostMod` | FloatProperty | 2 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `RVehicleBatmobileBase.ImpactMaxDamageSpeed` | FloatProperty | 150 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `RVehicleBatmobileBase.ImpactMinDamageSpeed` | FloatProperty | 20 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `RVehicleBatmobileBase.ImpactRoadAssistAngleStrength` | FloatProperty | 2000 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `RVehicleBatmobileBase.ImpactRoadAssistEnemyDuration` | FloatProperty | 0.333 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `RVehicleBatmobileBase.ImpactRoadAssistFactor` | FloatProperty | 90000 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `RVehicleBatmobileBase.ImpactRoadAssistMaxTorque` | FloatProperty | 30000 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `RVehicleBatmobileBase.ImpactRoadAssistSceneryDuration` | FloatProperty | 0 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `RVehicleBatmobileBase.ImpactShakeForceFactor` | FloatProperty | 0.01333 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `RVehicleBatmobileBase.ImpactShakeVehicleFactor` | FloatProperty | 1.5 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `RVehicleBatmobileBase.ImpactStrafeMod` | FloatProperty | 2.25 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `RVehicleBatmobileBase.KillFlipTorque` | FloatProperty | -200 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `RVehicleBatmobileBase.KillFlipTorqueDuration` | FloatProperty | 0.5 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `RVehicleBatmobileBase.KillKeepyUpFactor` | FloatProperty | 10 | sdk-layout |
| `RVehicleBatmobile` | `Playable_Batmobile_SF.Batmobile` | `RVehicleBatmobileBase.KillKeepyUpFactorDuration` | FloatProperty | 0.75 | sdk-layout |

