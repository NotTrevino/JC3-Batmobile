# Damage rules, health, armour, regeneration (G1-14)

The Arkham Knight Batmobile's damage model, read out of `BmGame.upk` (214,757,637 B; 84,813 names /
3,268 imports / 177,031 exports, of which **29,620** are `Function`) with the class dump
(`Working/vendor/BmSDK`) and the archetype tag chain (`Research/BatmobileGrab/CHAIN.json`).

Two things had to be recovered before any of it was readable, and both are recorded in §1: the
`Function` export layout (UEViewer stops parsing this class early, so the script bodies past that
point have never been read from this package), and a native/script test that does not depend on
anybody's guess. Machine source: `DAMAGE_RULES.json`, re-derived by
`python Tools/scripts/bmak_damage.py --check` (6/6 anchors, PASS). The extracted bytecode itself
lives outside this folder, in `Working/vendor/BmAKgrab/scripts/` — this note carries offsets,
symbols, constants and sha1s only.

---

## 1. The `Function` export layout, recovered

`BmGame.upk` is UE3 (version 863 / licensee 800016) and a `Function` export carries **no Batman
property tags** — it is positional. Reading it from byte 0 of the export:

| bytes | field | note |
|---|---|---|
| `u16` | prefix | constant `0` on every `Function` export |
| `i32` @2 | `Next` | `UField` sibling link |
| `i32` @6 | `SuperField` | super function, `0` when the class declares it |
| `i32` @10 | `Children` | first child property (the first parameter) |
| `i32` @14 | `Line` | editor line of the source |
| `i32` @18 | `ScriptSize` | == `len(script) + 1` |
| `byte[]` @22 | `Script` | `len(export) - 38` bytes of executable bytecode |
| `i32` @size-16 | flags word | |
| `i32` @size-12 | pre-name word | always `0x0002xxxx` |
| `i32` @size-8 | name `FName` index | the function's own name |
| `i32` @size-4 | name number | always `0` |

UEViewer knows only the first four fields: `Unreal/UnTypeinfo.h` handles `GAME_Batman4` with
`Ar << Children; return;   //!! remaining data will be dropped anyway`, so the script bytes from
offset 22 onwards were unclaimed until this pass. That is why "does the Batmobile take damage from
X" has never been answerable from this package.

**Anchors** (all re-checked by `--check`, all pass):

| anchor | what it proves |
|---|---|
| A | `SuperField` of `RVehicleBatmobileBase.TakeDamage` resolves to the inherited `TakeDamage` import and `Children` to `TakeDamage.DamageAmount` |
| B | `ScriptSize == len(script) + 1` for every traced function (14/14) |
| C | the thinnest script in the package is **one byte** and it is `04` (`EX_Return`) — 1,724 functions |
| D | the trailing `FName` is the function's own short name (14/14) |
| E | every `0x29` descriptor reference names a property of the function it sits in |
| F | `0x1c` is followed by a `Function` export in 99%+ of corpus hits (`EX_FinalFunction`) |

Token numbering is the one UE3 and UE4 share (`EX_Return`=0x04, `EX_Let`=0x0F,
`EX_Context`=0x19, `EX_VirtualFunction`=0x1B, `EX_FinalFunction`=0x1C, `EX_IntConst`=0x1D,
`EX_FloatConst`=0x1E, `EX_DynamicCast`=0x2E).

## 2. Native or script: the entry points, decided

A cooked **native** function keeps its parameter list as `0x29 <own-property ref>` descriptors
(five bytes each) in place of bytecode; a **script** function has a statement body. Two independent
sources are recorded for each row: the body itself, and the executable's own `exec<Name>`
registration string in `BatmanAK.exe`.

| function | export B | body B | parm descs | `exec<>` in exe | verdict |
|---|---:|---:|---:|---:|---|
| `RVehicleBatmobileBase.TakeDamage` | 2066 | 2028 | 0 | 3 | **script** |
| `RVehicleBatmobileBase.TakeRadiusDamageFromWeapon` | 326 | 288 | 0 | 0 | **script** |
| `RVehicleBatmobileBase.TakesDamageFromRam` | 45 | 7 | 0 | 0 | **script** |
| `RVehicleBatmobileBase.ShouldRadialDamageHit` | 48 | 10 | 2 | 1 | **native** |
| `RVehicleBatmobileBase.CanBatmobileDoImpactDamage` | 43 | 5 | 1 | 1 | **native** |
| `RVehicleBatmobileBase.CalculateAndStoreImpactDamage` | 1570 | 1532 | 0 | 0 | **script** |
| `RVehicleBatmobileBase.SetDamageLevel` | 48 | 10 | 2 | 3 | **native** |
| `RVehicleBatmobileBase.SetArmouredMode` | 43 | 5 | 1 | 2 | **native** |
| `RVehicleBatmobileBase.DrainWeaponGeneratorForDamage` | 360 | 322 | 0 | 0 | **script** |
| `RVehicleBatmobileBase.ExperienceAwarded` | 218 | 180 | 0 | 0 | **script** |
| `RVehicleBatmobileBase.LoadHealth` | 357 | 319 | 0 | 0 | **script** |
| `RVehicleBatmobileBase.GiveMaxEnergy` | 62 | 24 | 0 | 0 | **script** |
| `RVehicleBatmobileBase.OnModifyHealth` | 154 | 116 | 0 | 0 | **script** |
| `RVehicleCombatManager.GetDamageMod` | 58 | 20 | 3 | 1 | **native** |

The `exec<>` count for `TakeDamage` is **3** and does not make *this* override native: those
strings belong to parent registrations. The body decides (2,028 bytes of statements), and the two
sources only ever disagree where the body is a stub — they do not.

## 3. The rule: damage type → entry → what scales it → mode

### 3.1 Direct incoming damage — `TakeDamage` (script, 2,028 B)

Decoded order of the body's own property/function references (byte offsets in
`DAMAGE_RULES.json → functions.*.refs`):

1. `RVehicle.SelfDriveMode` and `RPlayerControllerBase.InCinematicMode` gate the hit (cinematic
   mode returns early — no damage taken while the camera is scripted).
2. **`ArmouredMode` → `ArmourModeDamageReduction`** — the only read of that field anywhere in the
   package (one reference, in this function). The shipped archetype value is **`0`**
   (`CHAIN.json`), so armoured/battle mode reduces incoming damage by *nothing* as shipped.
3. `RGameInfo.VehicleCombatManager.GetDamageMod(DamagedActor, HitNumber, IncrementCurrentAttackHits)`
   — native, three parameters; the encounter layer scales the hit.
4. Cosmetic/state response: `RVehicle.UnStickTyres`, `RPlayerController.AddScreenShake` with
   `ExplosiveImpactScreenShake`, `ExplosiveImpactSound`.
5. Counters: `RPlayerController.NumBatmobileMissileHits` / `NumBatmobileCannonHits`, each followed
   by `RPersistentData.AutoActivateTutorial`.
6. Source-specific branches: cast `DamageCauser` to `RProjectile`, `RTankMissile`,
   `RVehicleHeavyTank` (`Cloudburst` → `RVehicleCombatManager.bDamagedByCloudburstTank`),
   `RCommandBeaconBase`; `RPlayerController.LastDamageType` is stored.
7. **`DrainWeaponGeneratorForDamage(DamageAmount, HitNumber)`** — the weapon generator is the
   shield (§4); afterwards `bEmergencyWeaponGenerator` and `WeaponGeneratorPower`.
8. Thresholds: `QuarterHealth`, `LowHealthWarningLevel` → `RHudModuleStoryMode.SetOneShotWarningMessage`,
   `RVehicleCombatManager.PlayCommanderBark`, `DisableUnderAttackWarning`, `bIsJokerfiedBatmobile`.
9. Body literals: `1000.0`, `0.5`, `1.0`.

### 3.2 Radial / explosion incoming — `TakeRadiusDamageFromWeapon` (script, 288 B)

Calls the **native** `ShouldRadialDamageHit(HurtOrigin, DamageRadius)` first (that gate's body is
two parameter descriptors, so *whether* a radial hit lands is decided in `BatmanAK.exe` and is not
readable from script), then computes a distance falloff from `Dist`, `ColRadius`, `ColHeight`,
`Dir` and `DamageFalloffExponent` with literals **1500.0, 0.5, 0.1, 1.0, 0.0**, clamps the result
into `Reduce`, and forwards `InstigatedBy, BaseDamage, DamageRadius, DamageType, Momentum,
HurtOrigin, DamageCauser` into `TakeDamage`.

### 3.3 Ram / collision — **outgoing** (matches T-DM7 → `out`)

`CalculateAndStoreImpactDamage` (script, 1,532 B) reads only the vehicle's own fields, and every
one of them is an *outgoing* multiplier:

| field | shipped (`Playable_Batmobile_SF.Batmobile`) | Joker |
|---|---:|---:|
| `ImpactMinDamageSpeed` / `ImpactMaxDamageSpeed` | 20 / 150 | 40 / 180 |
| `BattleModeImpactMinDamageSpeed` / `MaxDamageSpeed` | 120 / 540 | 120 / 540 |
| `BattleModeImpactMaxDamagePow` | 0.5 | 0.666 |
| `ImpactStrafeMod` | 2.25 | 0.8 |
| `ImpactBoostMod` | 2.0 | — |
| `ImpactCivilianVehicleMod` | read, `RVehicle.CivilianVehicle` branch | — |
| `ImpactMaxDamage` | read (cap) | — |

plus `RVehicleSimBatmobile.bBoosting`, `RVehicle.HeavyArmouredVehicle`, `CurrentStrafeCooldown` /
`StrafeCooldown` / `StafeImpactImpulse`, `RVehicle.bHasAPCStyleWeakSpot` →
`RVehicleCar.RemoveWeakSpot`, `RGameInfo.IsChallengeMode`, and the floating `DamageNumbers` UI.
The gate `CanBatmobileDoImpactDamage(OtherVehicle)` is native (1 descriptor, 1 `exec<>` string).

#### 3.3.1 Sideswipe - the targeting half (noted 2026-10-26)

The block above decides *how much* damage a hit deals. What decides *which* car is hit is a
second, runtime mechanism on the same class, and it is why no archetype value exists for it:

| member | type | role |
|---|---|---|
| `SideSwipeTargetsList` | `RInteractionClass` | the candidate set a sideswipe picks from |
| `SideSwipeInSweetSpot` | `bool` | true on the frames the hit lands in the sweet spot |
| `GetSideSwipeTarget(Targets, Direction, out Distance)` | function | picks a target for a direction |
| `GetCurrentSideSwipeTarget()` | function | the target currently held |
| `GetBatmobileDodgeDirection(Target)` | function | the dodge direction for that target |
| `CrushedThisFrame` / `BouncedThisFrame` | `bool` | per-frame contact state |

`OFFSETS.json` carries **0** rows for any of these: they are runtime state and script functions,
not serialised defaults (both functions are also listed in `NATIVE.md`). So the numbers for a ram
are the ones in the table above - `ImpactMinDamageSpeed`/`ImpactMaxDamageSpeed` 20/150 (Joker
40/180), `ImpactStrafeMod` 2.25 pursuit / 0.8 Joker, `ImpactBoostMod` 2.0, battle mode 120/540
with `BattleModeImpactMaxDamagePow` 0.5 / 0.666 - while *choosing* the victim and landing in the
sweet spot is native and not readable from the files.

In play the Batmobile does sideswipe traffic and ram it (user, 2026-10-26). The behaviour is
therefore real and the outgoing numbers are decoded; T-DM7 still routes the damage itself to
JC3's own collision response (`out`), and that translation decision is untouched by this note.

### 3.4 Ram — **incoming**, and unconditional

`TakesDamageFromRam(Target, RamSpeed)` is a **script** function whose whole body is seven bytes:

    return true;    // then a read of the function's own ReturnValue slot

**`return true`, with no condition and no field read.** So the postmortem's statement that
"there is no incoming-impact entry point on the class" is too strong: the entry point exists and
is open. Whatever makes ramming survivable, it is not this function, and no archetype value can
switch it off from here.

### 3.5 Outgoing weapon damage — archetypes, not rules

`CHAIN.json` (251 damage rows):

| carrier | field | value |
|---|---|---|
| `Batmobile_Heavy_Cannon_Primary_Projectile` | `Projectile.Damage` | 50 |
| `..._BodyShot_Projectile` | `Projectile.Damage` | 75 |
| `..._Fully_Upgraded_Projectile` | `Projectile.Damage` / `TurretShotDamage` | 75 / 110 |
| `..._HeadShot_Projectile` | `TurretShotDamage` | 110 |
| `Batmobile_JokerHeavy_Cannon_Projectile` | `Damage` / `DamageRadius` | 250 / 350 |
| `Batmobile_EMPMissile_Projectile` | `Damage` | 60 |
| `Batmobile_Missile_*` | `Projectile.Damage` | 60 |
| `Batmobile_Missile_*` (Joker) | `Projectile.Damage` | 250 |

Each projectile also carries `Projectile.MyDamageType` (an import reference, e.g. `-104`, `-113`,
`-121`), so the *damage class* is chosen per projectile — the per-type multiplier itself lives in
that class, not in the vehicle.

### 3.6 Summary table

| damage type | entry point | what scales it | mode |
|---|---|---|---|
| direct hit (bullet, shell, melee) | `TakeDamage` (script) | `GetDamageMod` (native, encounter) × `ArmourModeDamageReduction` (ships **0**) after the weapon-generator pool absorbs it | armoured/battle mode is the only mode gate |
| radial / explosive | `TakeRadiusDamageFromWeapon` (script) | native `ShouldRadialDamageHit` gate, then distance falloff (1500.0 / 0.5 / 0.1) | any |
| ram into the Batmobile | `TakesDamageFromRam` (script) | **none — `return true`** | none |
| ram by the Batmobile | `CanBatmobileDoImpactDamage` (native) + `CalculateAndStoreImpactDamage` (script) | speed band 20→150 (120→540 battle), `ImpactStrafeMod` ×2.25, `ImpactBoostMod` ×2.0, civilian mod, weak-spot removal | pursuit vs battle |
| weapons fired | projectile archetypes | `Projectile.Damage` 50/75/110/250, radius 350 | per weapon |
| cinematic | `TakeDamage` early-out | — | `InCinematicMode` |

## 4. Health, the weapon generator, and the numbers

- **`Pawn.Health` = 1200** on every Batmobile archetype (inside the shipped 500…4000 band; the
  postmortem's 6 t reading stands).
- **Persisted**: `RVehicleBatmobileBase.LoadHealth` (script, 319 B) reads
  `RPersistentData.BatmobileHealth` (int) and `RPersistentData.BatmobileEnergy` (float), plus
  `RGameRI.PersistentOptions.DDA_DeathsInRoom` — Batmobile health and energy are saved, and
  **dynamic difficulty reads the death count in the room** before deciding them. Literals
  `9999999` (challenge mode uses a sentinel health) and `0.0`.
- **The weapon generator is the shield**: `TakeDamage` calls
  `DrainWeaponGeneratorForDamage(DamageAmount, HitNumber)` (script, 322 B), which reads
  `WeaponGeneratorPower`, `bWeaponGeneratorShielding`, `WeaponUnavailableReason`,
  `bIsJokerfiedBatmobile`, `RGameInfo.GetDifficulty`, with literals **0.05, 0.5, 1.0**, and ends
  in `IncSteamEffect` + `RBatmobileCannon.OverHeat`. `WeaponGeneratorPower` is read by **25**
  script functions in total.
- **`GiveMaxEnergy`** (24 B): `WeaponGeneratorPower = MaxWeaponGeneratorPower[CurrentGeneratorLevel]`.
- **`QuarterHealth` / `LowHealthWarningLevel`** drive the low-health HUD warning
  (`RHudModuleStoryMode.SetOneShotWarningMessage`); `LowHealthWarningLevel` has exactly one
  reader in the whole package — `TakeDamage`.
- **`OnModifyHealth`** (116 B) takes an `Action`, casts the PC and calls
  `RPlayerController.InstantUpdateHealth` — that is the **Batsuit** bar (`HUD.md`), not the car's.

## 5. Regeneration — answered: a mechanism exists, its value does not ship

`ARM-5` asked whether BmAK has a regen value. It does, and it is **not** a passive timer:

- `RVehicleBatmobileBase.HealthRecoverRate` is a **`TArray<float>` at +8220** in the class dump.
- **No archetype overrides it** — it is absent from `CHAIN.json` and from the 423-field
  `OFFSETS.json` binding, so the tags carry no value; the shipped number is whatever the native
  CDO in `BmScript` (not shipped) holds.
- Exactly **one** script function in all 29,620 reads it:
  **`RVehicleBatmobileBase.ExperienceAwarded`** (180 B), which also reads `RGameInfo.GetDifficulty`
  and `RPawnCombat` state.

So recovery is **awarded per experience event, indexed by difficulty**, not a health-per-second
regen out of combat, and the rate table itself is not in the files. Verdict for the row:
**mechanism = yes (decoded), value = unknown from the files** (readable only from a running game's
CDO, same class of gap as `CAMERA.md` §2b).

Corroboration: the name table carries `HealthRecoverRate`, `HealthRecovery`, `ReplenishHealth`,
`RestoreHealth`, `RestoreArmour`, `RSeqAct_RestoreHealth`, `KOHealthRegainAmount`,
`BatmobileHealth`, `PDVer_BatmobileHealth`, `Play_BML_LowHealth` — health is a *state* with
restore triggers and a persisted version key, not a regenerating counter. No `*Regen*` field
exists on `RVehicle*`, `Pawn` or `AkVehicle` (the SDK scan in `DAMAGE_RULES.json → regeneration`
is the full list).

## 6. What this corrects in `POSTMORTEM_DAMAGE.md`

1. **T-DM7 → `out` is confirmed.** Every field `CalculateAndStoreImpactDamage` reads is an
   outgoing multiplier (`Impact*`, `BattleModeImpact*`, strafe/boost/civilian mods); the class
   still has no *scaling* expression for incoming impact damage.
2. **But the sentence "there is no incoming-impact entry point on the class" is wrong.**
   `TakesDamageFromRam` is exactly that entry point, it is script, and it returns `true`
   unconditionally. Incoming-impact immunity therefore cannot be a value row here.
3. **The armour-mode reduction is real but shipped at zero.** `ArmourModeDamageReduction` = `0`
   is *not* an undeclared switch: `0` is what the archetype sets, and it is read only by
   `TakeDamage`. The undeclared switches remain the ones the postmortem listed
   (`impact_damage_factor`, `impact_armor`, `deform_scale`, …) — those live in the **JC3** build,
   not in BmAK.
4. **`ShouldRadialDamageHit` is native, so "how a radial hit is decided" cannot be answered from
   script.** Any claim about it needs the exe, and it belongs in `G1-22` (native remainder).

## 7. Open, honestly

- `HealthRecoverRate[difficulty]` values → needs the running game's CDO (`G1-22` / a probe).
- `GetDamageMod` is native: the encounter scaling behind ARM-2's hits-to-kill is in `BatmanAK.exe`
  (`execGetDamageMod`), not in script. `G2-28`'s hits-to-kill table needs this number.
- The per-`DamageType` multipliers live in the damage classes (each projectile's
  `MyDamageType` import); those classes are engine-side and were not opened here.
- This note reads **structure and symbols**, not control flow: the reference trace is ordered and
  complete, but branches, jump offsets and operand nesting are not resolved into source. Where §3
  says "gates" or "afterwards" it is following the byte order, not a disassembled AST.

## 8. Tool and gates

```
python Tools/scripts/bmak_damage.py --write    # writes DAMAGE_RULES.json + raw scripts
python Tools/scripts/bmak_damage.py --check    # re-derives, diffs, prints the anchors
```

`--check` prints **6/6 anchors** and `PASS`. `DAMAGE_RULES.json` carries the layout, the anchors,
the `exec<>` counts, all 14 traced functions (offsets, symbols, constants, sha1s), 251 damage
values, the per-field reader lists and the full regen-symbol scan. Raw bytecode stays in
`Working/vendor/BmAKgrab/scripts/` (14 files), outside this folder, by the same rule that keeps
the animation keys and bone face lists outside the notes.
