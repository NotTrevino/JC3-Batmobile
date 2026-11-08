# Health and damage states — BmAK ⇄ JC3, and the numeric mapping

Scope: the Batmobile's hit-point model in Batman: Arkham Knight (BmSDK members, armour, per-weapon
damage), the visible damage stages the files prove, the JC3 side it has to land on, and an exact
mapping that makes a rocket and a bullet take the same fraction of health in both games.

Every value below is read from a file in this repository. Values the files do not carry are marked
**UNKNOWN**, with what would settle them. No number here is a plausible-sounding JC3 or BmAK
implementation.

**Headline results**

1. **BmAK's durability is one 1,200-point `Pawn.Health` pool plus a five-band armour ladder**
   (`ArmourLevels` `[0, 300, 600, 900, 1200]`, i.e. 25 % steps) **plus a weapon-generator shield** that
   absorbs damage and ends in steam/overheat. There is **no per-damage-type multiplier table** on the
   class — the eight-channel armour model is JC3's, not BmAK's.
2. **BmAK has no small-arms damage path at all**, so its bullet fraction is **0**. JC3's is ~1.5% and
   cannot be driven to 0 from inside `VehicleDamage` (the required strength is out of the shipped
   domain). That asymmetry is the real content of the bullet half of the question.
3. **Rocket parity and cannon parity need different health values** (7,200 vs 36,000 at shipped JC3
   weapon damage), so no single health pool matches both. An in-domain solution exists only on the
   damage side.
4. BmAK's visible damage is **five armour tiers + an on-fire mesh + a death explosion and wreck**;
   JC3's is **three numeric thresholds (smoke, burn, explode), a three-state part table and an
   optional crumple scale** — different carriers, so the stages have to be mapped by *fraction*, not
   by member name.

---

## 1. The BmAK hit-point model

### 1.1 Health members (BmSDK class `RVehicleBatmobileBase`, superclass `Pawn`)

| member | type | offset | shipped value | evidence |
|---|---|---:|---|---|
| `Pawn.Health` | int | — | **1200** on all 3 Batmobile archetypes (`BatmobileFunhouse`, `Batmobile_MK2`, `Batmobile`) | `Research/BatmobileGrab/DAMAGE_RULES.md` §4 |
| `ArmourLevels` | `TArray<int>` | 8108 (`0x0a68`) | **`[0, 300, 600, 900, 1200]`** (count 5) | `Research/BatmobileGrab/CLASS_DEFAULTS.md` row 143 |
| `LowHealthWarningLevel` | int | 8124 (`0x0a84`) | **300** | `CLASS_DEFAULTS.md` row 144 |
| `ArmourModeDamageReduction` | int | — | **0** on all three archetypes | `DAMAGE_RULES.md` §3.1 |
| `HealthRecoverRate` | `TArray<float>` | 8220 | not carried by any archetype tag — value is in the unshipped native CDO | `DAMAGE_RULES.md` §5 |
| `HealthUpdated`, `LoadHealth`, `OnModifyHealth`, `GiveMaxHealth`, `GetMaxHealth`, `EMPRepairable` | — | — | restore/persist triggers, no numbers | `DAMAGE_RULES.md` §5 |
| `MaxWeaponGeneratorPower` | `TArray<float>` | 7920 | **`[2.0, 3.0, 4.0]`** (per generator level) | `CLASS_DEFAULTS.md` row 121 |
| `WeaponGeneratorPowerTickUp` | float | 7916 | **0.666** | `CLASS_DEFAULTS.md` row 120 |
| `WeaponGeneratorKillBonus` | float | 7936 | **0.3334** | `CLASS_DEFAULTS.md` row 122 |
| `BatmobileOnFireDamageRadiusScale` | float | 8128 | **0.005** | `CLASS_DEFAULTS.md` row 145 |
| `DeathExplosion` | object ref | 5564 | `Impacts.Batmobile_Explosion` (`ParticleSystem`) | `Research/BatmobileGrab/COLLISION_WHERE.md` line 84 |
| `DeadBatmobileArchetype` | object ref | 5556 | `DeadVehicle.Dead_Batmobile` (`RDeadVehicle`) | `COLLISION_WHERE.md` line 83 |
| `BatmobileOnFireMeshComp` | object ref | 5684 | `Batmobile.BatmobileOnFireMeshComp0` (`SkeletalMeshComponent`) | `COLLISION_WHERE.md` line 85 |
| `VisualDamageComp` | object ref | `0x0874` | `VisDmgComp` (`RVisualDamageComponent`) | `Research/BatmobileGrab/OFFSETS.md` line 381 |
| `HealthMax` / `MaxHealth` | int | — | present on `Pawn` / `RVehicle`; **UNKNOWN** which one the car reads for its 1200 | `DAMAGE_RULES.md` §5 |

`QuarterHealth` is **not** a class default: it is an `IntProperty` local of `TakeDamage` itself
(`DAMAGE_RULES.json` ref 10422), i.e. the code computes a quarter of health rather than reading a
threshold.

### 1.2 Armour — and what BmAK does *not* have

- `ArmourLevels` is a five-entry ladder spanning **0…1200, the whole health pool**, in **300 steps**.
  The HUD reads exactly this shape: the health-bar clip draws `ArmourForeground` from `max(0, h-1)`
  and selects `Armour<n>` of **5** tiers (`Tools/scripts/bmak_hud_cluster.py` §"armour tiers", lines
  603–607). Reading the ladder as quarter-health bands is therefore strongly indicated; the native
  consumer is not readable (that file records it as "decoded / out — no JC3 member").
- `ArmourModeDamageReduction` is the *only* mode gate, read by exactly **one** script function
  (`TakeDamage`), and it ships **0**, i.e. battle/armoured mode cuts nothing
  (`DAMAGE_RULES.md` §3.1; bytecode traced in `DAMAGE_LAYOUT_AUDIT.md` §5 R1).
- **There is no `damage type → multiplier` table in BmAK.** `Research/challenge/card-G1-14.md` A13
  records this as a delivered-card failure: `MyDamageType` appears only as an import index
  (`-104`, `-105`, `-121`…), with no multiplier and no class. So the "armour" BmAK has is a **band
  ladder**, not JC3's eight per-type channels.

### 1.3 The shield that sits in front of health

`TakeDamage` calls `DrainWeaponGeneratorForDamage(DamageAmount, HitNumber)` (script, 322 B) before
health is affected. That function reads `WeaponGeneratorPower`, `bWeaponGeneratorShielding`,
`bIsJokerfiedBatmobile` and `GetDifficulty`, has body literals `0.0 / 0.05 / 0.5 / 1.0`, and **ends
in `IncSteamEffect` + `OverHeat`** (`DAMAGE_RULES.md` §4). So the first visible damage response in
BmAK is *steam from an overheated generator*, driven by a 2/3/4-unit pool at generator levels 1–3.
How much of a hit the pool absorbs per unit is **UNKNOWN** (native).

### 1.4 Per-weapon damage that is actually decoded

Incoming damage is `TakeDamage(DamageAmount)` scaled by `GetDamageMod` (native, **UNKNOWN** return)
and the armour-mode factor (1.0 as shipped). The per-hit `DamageAmount` numbers the files carry are
the projectile archetypes (`DAMAGE_RULES.md` §3.5, Appendix A):

| BmAK archetype family | `Projectile.Damage` | `DamageRadius` | `TurretShotDamage` |
|---|---:|---:|---:|
| `Batmobile_Missile_Projectile` | **250** | 0 | — |
| `Batmobile_EMPMissile_Projectile` | **60** | 0 | — |
| `Batmobile_Heavy_Cannon_Primary_Projectile` | **50** | 0 | 75 |
| `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile` | **75** | — | 110 |
| `Batmobile_Heavy_Cannon_BodyShot_Projectile` | **75** | — | — |
| `Batmobile_Heavy_Cannon_HeadShot_Projectile` | — | — | 110 |
| `Batmobile_JokerHeavy_Cannon_Projectile` | **250** | 350 | — |
| `Batmobile_JokerMissile_Projectile` | **250** | 300 | — |
| *any bullet / small arm* | **no path** | — | — |

Two honest caveats that the mapping must inherit:

- These are the Batmobile's **own** projectile classes. That the same `RBasicProjectile` /
  `RBatmobileMissile` numbers are what NPC tanks and RPGs deliver to it is an **idealisation**
  (`DAMAGE_MODEL.md` §8 states the same limit from the JC3 side). Enemy projectile archetypes were
  not opened.
- `GetDamageMod` (encounter scaling) is native and in `BatmanAK.exe`, so the *health loss a player
  sees* is `DamageAmount × GetDamageMod × 1.0` minus whatever the generator pool ate. The mapping
  below therefore uses **archetype damage vs pawn health**, exactly as `DAMAGE_MODEL.md` §5 already
  does for the 24-hit figure.

### 1.5 What BmAK does not evidence

- **A bullet path.** `DAMAGE_RULES.md` §6 and `MODLOG.md` §4294–4296: "Health + ArmourModeDamageReduction
  + TakeRadiusDamageFromWeapon (+falloff) + ram/crush/impact speeds + DeathExplosion + ricochet bank +
  ShootBatmobile AI; **NO bullet-damage path anywhere**."
- **A per-part health table.** No such member appears in the 423 named fields (`OFFSETS.json`), and the
  one visual-damage object (`RVisualDamageComponent`, 4 instances, ≤6 B, no property tags) decodes to
  nothing (`Research/BatmobileGrab/REMAINDER.md` lines 1168, 1896).
- **Regeneration as a rate.** `HealthRecoverRate[difficulty]` exists and is read by exactly one
  function, `ExperienceAwarded` — recovery is **awarded per XP event**, not a passive timer, and the
  per-difficulty values are not in the shipped files (`DAMAGE_RULES.md` §5).
- **A ram-damage scaling curve for incoming hits.** `TakesDamageFromRam` is `return true`
  unconditionally (8-byte body, `DAMAGE_LAYOUT_AUDIT.md` §5 R2).

---

## 2. The visible damage stages that BmAK proves

| # | stage | carrier (decoded) | value / boundary | strength |
|---|---|---|---|---|
| 0 | intact | — | health 1200 = `ArmourLevels[4]` | decoded |
| 1 | armour tier III | `ArmourLevels[3]` = **900** | 75 % health | decoded ladder; HUD reads 5 tiers |
| 2 | armour tier II | `ArmourLevels[2]` = **600** | 50 % | decoded ladder |
| 3 | armour tier I **+ low-health warning** | `ArmourLevels[1]` = **300** = `LowHealthWarningLevel` | 25 %; `SetOneShotWarningMessage`, `PlayCommanderBark` fire from `TakeDamage` | decoded (value 300, single reader) |
| 4 | generator overheat / steam | `IncSteamEffect` + `OverHeat` at the end of `DrainWeaponGeneratorForDamage` | pool 2 / 3 / 4 at generator levels 1–3 | decoded mechanism, absorption rate UNKNOWN |
| 5 | on fire | `BatmobileOnFireMeshComp0` (`SkeletalMeshComponent`), `BatmobileOnFireDamageRadiusScale` 0.005 | threshold UNKNOWN; the name-table occurrence `SetBatmobileOnFire` sits near `TakeDamage`'s body but the audit records it as an unresolved name (`card-G1-14.md`, mis-resolution list) | mechanism present, boundary UNKNOWN |
| 6 | death explosion + wreck | `DeathExplosion` = `Impacts.Batmobile_Explosion`, `DeathExplosionSoundArray`, `DeadBatmobileArchetype` = `DeadVehicle.Dead_Batmobile`, AkEvent `Play_Batmobile_Destroyed` | at health 0 | decoded references |
| — | `DamageLevel` | native `SetDamageLevel(PlayerBatmobileName, NewDamageLevel)` — `NewDamageLevel` is an `IntProperty` param | threshold table **UNKNOWN** (setter carries nothing; caller not traced) | `FOOTAGE.md` line 158 |
| — | material damage | `Batmobile_Damage_FCT`, `Batmobile_Damage_Dirt_FCT`, `Batmobile_Worn` material | visual-only | `GRAB_BACKLOG.md` line 958 |

So the file-provable BmAK damage staging is **five 25 % health bands, a steam/overheat shield state,
a fire state and a death/wreck state** — with the *numeric* boundaries known only for the band ladder.

---

## 3. The JC3 hit-point model it has to land on

### 3.1 Health and the entity-level switch

| carrier | value | evidence |
|---|---|---|
| `VehicleDamage.max_health` (int32) | fleet **500…4000** (med 700); donor **700**; build (test-091, `lave_health_medium`) **2000** | `Research/JC3Grab/VOCABULARY.md` `VehicleDamage`; `Research/JC3Grab/DAMAGE_MODEL.md` §2 |
| entity root `health` (float32, `.epe`) | **100.0** on all 233 roots | `Research/JC3Grab/DAMAGE_MECHANISMS.md` §1 |
| entity root `invulnerable` (int32) | **0** on all 233; live flag, 4 bytes at `.epe+1167` | `DAMAGE_MECHANISMS.md` §2–§3 |
| composition of root `health` with `max_health` | **UNKNOWN** (no shipped root differs from 100.0) | `DAMAGE_MODEL.md` step 6 |

### 3.2 The 30 `VehicleDamage` members that matter here

Eight armour channels, each `<channel>_armor` (int32) + `<channel>_armor_strength` (float32; the
strength is a float — `ARMOR_STEP.md` §5 corrects the earlier integer print):
bullet, bullet_heavy, explosion, impact, fire, melee, electricity, grapple_pull. Build vs medium
tank vs donor: `DAMAGE_MODEL.md` §2. Composition rule still **UNKNOWN** — three models carried
(H0 ignore / H1 percentage / H2 threshold+pool), judged by the three Q-1 probes.

Staging members: `smoke_threshold` (uint16), `burn_threshold` (uint16), `burn_duration_s` 20,
`explosion_threshold` (int32), `explosion_delay_s` (5–10), `vulnerable_explosion_threshold`,
`vulnerable_duration_s` 5, `fire_spreading_speed_ms` 1.5, `impact_damage_factor` (1–12),
`impact_deform_threshold`, `weapon_deform_threshold`, `deform_scale` (1–2).

### 3.3 Per-part damage table

`part_damage_types[]` — 24 rows of `Land_*` in the donor, the medium tank and the build, each row
`initial_health` / `damaged_health` / `loosen_health` + `instantly_{damaged,loosened,broken}_by_bullets`
+ `damages_owning_vehicle` (`VOCABULARY.md`; `DAMAGE_MODEL.md` §2). Donor `Land_Wheel` 1020/400/100;
the build's table is the donor's with exactly one change, `Land_Wheel.instantly_damaged_by_bullets`
1 → 0. Semantics of the three health fields is **UNKNOWN** (thresholds? damage taken?).

---

## 4. The visible damage stages JC3 actually has

| stage | carrier | build value | as fraction of `max_health` 2000 | donor value | donor fraction (700) |
|---|---|---:|---:|---:|---:|
| smoke | `smoke_threshold` | **1050** | 52.50 % | 200 | 28.57 % |
| burn (fire) | `burn_threshold` | **250** | 12.50 % | 80 | 11.43 % |
| vulnerable | `vulnerable_explosion_threshold` | 100 | 5.00 % | 35 | 5.00 % |
| explode | `explosion_threshold` | **4000** | 200 % (never, if a health threshold) | 700 | 100 % |
| part: intact | `initial_health` | per row | — | e.g. `Land_Wheel` 1020 | — |
| part: damaged | `damaged_health` | per row | — | 400 | — |
| part: loosened/broken | `loosen_health` + `instantly_*_by_bullets` | per row | — | 100 | — |
| crumple | `deform_scale` | **0** (off) | — | 1 | — |
| part events | effect usages `OnPartReachedDamageState`, `OnPartBrokeOn`, `OnExploded`, `OnPartExplode` | — | — | — | — |

Two readings of the thresholds remain open (`DAMAGE_MODEL.md` step 7): *health remaining* or
*per-hit damage*. Only the first is coherent with `smoke > burn`; under it the build's
`explosion_threshold` 4000 **can never be reached** by damage, and the donor explodes at 100 %.
`vehicle_deform` is a decoded-but-memberless module in the vocabulary tables; the deformation
switch that has a name is `deform_scale`.

---

## 5. Side-by-side comparison

| question | BmAK | JC3 | substitutable? |
|---|---|---|---|
| health pool | `Pawn.Health` **1200** | `VehicleDamage.max_health` **2000** (build) / fleet 500–4000 | yes, by ratio |
| scale on top of the pool | none (health is absolute) | entity root `health` **100.0** (semantics UNKNOWN) | leave at 100 |
| immunity switch | none; small arms simply have no path | root `invulnerable` **0** (whole-vehicle) | yes, but whole-vehicle only |
| armour | `ArmourLevels` **5 bands, 25 % steps** | 8 per-type `*_armor` + `*_armor_strength` channels | **no** — different model |
| mode reduction | `ArmourModeDamageReduction` **0** | none | n/a |
| shield in front of health | weapon-generator pool **2/3/4**, steam+overheat | none | **no carrier** |
| damage types | per-archetype `Damage` only | 8 channels + part types (24 `Land_*`) | partly |
| bullets | **no path → 0** | `bullet` channel, ~1.4–7.2 % per hit | only via root flag |
| rocket | missile **250** = 20.83 % | heli missile / RPG / shell blast **1500** = 75 % (build), 214 % (donor) | yes, by ratio |
| heavy cannon | **50** = 4.17 % (75/110 variants) | shell bullet damage 1 + **1500** blast | yes, by ratio |
| visible tiers | 5 × 25 % + fire + wreck | **3** thresholds (smoke 52.5 %, burn 12.5 %, explode never) + 3-state parts | by fraction only |
| regen | XP-awarded, value UNKNOWN | none in the vocabulary | n/a |
| crumple | none (no deform in BmAK) | `deform_scale` **0** = off | already matches |

**The one-line answer to "what is the BmAK model":** 1,200 HP, five 25 % armour bands, a 2–4 unit
generator shield that steams when it empties, a 25 % warning at 300, a fire state with an unfindable
boundary, and a death explosion that swaps in a wreck — with per-hit damage coming from projectile
`Damage` values and no per-type multipliers anywhere.

---

## 6. The numeric mapping: equal health fraction per hit

### 6.1 Definition

For a hit of raw damage `D` against a pool `H`, the fraction is

```
f = D / H            (armour-mode factor 1.0 in BmAK; JC3 armour composition UNKNOWN, see 6.6)
```

Equal-fraction mapping requires **`f_J = f_B`**, i.e.

```
D_J / H_J = D_B / H_B          →          H_J = H_B · (D_J / D_B)      or      D_J = D_B · (H_J / H_B)
```

with `H_B = 1200`. Two knobs exist: the JC3 pool `H_J` (in-domain 500…4000) and the JC3 per-hit
damage `D_J`. `k := H_J / H_B` is the single scale factor when the health side is chosen.

### 6.2 BmAK fractions (`H_B = 1200`)

| BmAK arm | `D_B` | `f_B = D_B/1200` | hits to kill (exact) |
|---|---:|---:|---:|
| missile (`Batmobile_Missile_Projectile`) | 250 | **20.833 %** | 4.80 |
| Joker missile / Joker heavy cannon | 250 | 20.833 % | 4.80 |
| EMP missile | 60 | 5.000 % | 20.00 |
| heavy cannon, fully upgraded / body shot | 75 | 6.250 % | 16.00 |
| heavy cannon, primary | 50 | **4.167 %** | 24.00 |
| turret shot (upgraded) | 110 | 9.167 % | 10.91 |
| any bullet / small arm | **0** | **0.000 %** | ∞ |

### 6.3 JC3 fractions as shipped (`H_J = 2000` build; donor 700 in brackets)

| JC3 arm | `D_J` | `f_J` | hits (build) |
|---|---:|---:|---:|
| heli missile `w601` | 1500 | **75.000 %** | 1.33 |
| RPG `w141` (blast 1500 in 10 m) | 1500 | 75.000 % | 1.33 |
| tank cannon `w602` (blast 1500 in 8 m; bullet damage 1) | 1500 | 75.000 % | 1.33 |
| grenade `w301` | 1012.5 | 50.625 % | 1.98 |
| shotgun `w151` (8 × 90 × 0.2) | 144 | 7.200 % | 13.9 |
| assault rifle `w111` | 32 | 1.600 % | 62.5 |
| pistol `w011` | 30 | 1.500 % | 66.7 |
| machine gun `w131` | 28 | 1.400 % | 71.4 |
| heli MG `w604` | 25 | 1.250 % | 80.0 |
| *donor (700)*: heli missile | 1500 | 214.286 % | one-shot |

### 6.4 The equal-fraction table (exact)

`r := D_J / D_B`; health-side solution `H_J* = 1200 · r`; damage-side solution at the two in-domain
pool values.

| arm pair | `r = D_J/D_B` | `H_J*` (health side) | in 500–4000? | `D_J*` at `H_J=2000` (k=1.6667) | `D_J*` at `H_J=4000` (k=3.3333) |
|---|---:|---:|---|---:|---:|
| **rocket**: BmAK 250 ↔ JC3 1500 | **6.0** | **7200** | **no** (1.8× the fleet max) | 416.67 | **833.33** |
| **cannon**: BmAK 50 ↔ JC3 shell blast 1500 | **30.0** | **36 000** | **no** (9× the fleet max) | 83.33 | **166.67** |
| upgraded cannon: 75 ↔ 1500 | 20.0 | 24 000 | no | 125.00 | 250.00 |
| EMP: 60 ↔ 1500 | 25.0 | 30 000 | no | 100.00 | 200.00 |
| turret shot: 110 ↔ 1500 | 13.636 | 16 364 | no | 183.33 | 366.67 |
| **bullet**: BmAK 0 ↔ JC3 30/32/28 | ∞ | **no finite pool** | **no** | **0** | **0** |

Read as hits-to-kill, the rocket row is `1200/250 = 4.8` vs `7200/1500 = 4.8` — **5 hits in both
games** — and the cannon row is **24 hits in both** at 36,000. Those two numbers reproduce the
existing `DAMAGE_MODEL.md` §5 result and extend it to the exact health values.

**The unavoidable conclusion:** `r` is 6 for the rocket but 30 for the cannon, so **one health pool
cannot equalise both** at shipped JC3 weapon damage. The mapping is therefore per-arm on the damage
side, with the health side fixed. Two consistent choices:

- **Anchor = rocket, pool at fleet max.** `H_J = 4000`, `k = 3.33333`; the JC3 rocket must deliver
  **833.33** (not 1500) and the shell blast **166.67** (not 1500). Both are vanilla `.ftunec` /
  `WEAPONS.jsonl` values, i.e. a data edit, not a module edit. Rocket = 20.833 %, shell = 4.167 %,
  identical to BmAK.
- **Anchor = rocket, pool at the build's 2000.** `k = 1.66667`; rocket **416.67**, shell **83.33**,
  EMP 100, upgraded cannon 125. Fractions identical to BmAK, hit counts identical too.

Everything else in the JC3 armour model is either unknown (composition) or can only reduce damage,
so it must be set to a known-neutral value before the fractions above hold: on the H2 reading that
means every channel `*_armor` 0 (as the donor ships, `DAMAGE_MODEL.md` §2) and `*_armor_strength` 0;
on the H1 reading it means the same. The build currently carries `bullet 5000 @ 99` — a **reduction
of unknown size** on exactly the channel the bullet row is about.

### 6.5 The bullet row, stated exactly

BmAK's bullet fraction is **0.000 %** — not "small", zero: there is no bullet path in the class
(`DAMAGE_RULES.md` §6, `MODLOG.md` §4294–4296). To make the JC3 bullet fraction equal, `D_J` on the
`bullet` channel must be **0**. What each knob would need:

| route | required value | in the shipped domain? | consequence |
|---|---|---|---|
| H2 (threshold + pool): `bullet_armor_strength` | ≥ **144** (the shotgun's per-pull damage; the AR needs 32) | **no** — fleet max is **99** | — |
| H1 (percentage gate): `bullet_armor_strength` | **100** (a full stop) | **no** — max 99, and test-077 shipped exactly 100 and failed (`DAMAGE_MODEL.md` §5) | — |
| entity root `invulnerable` | **1** (4 bytes at `.epe+1167`) | **yes**, and the game itself ships 1 on 10 `CDamageController` objects | whole-vehicle: also zeroes the rocket, so the rocket row would go to 0 % and the pair would no longer be equal |
| accept the shipped JC3 bullet fraction | 1.4–7.2 % | yes | bullet fraction differs from BmAK by 1.4–7.2 points |

So the exact pair *"rocket 20.833 %, bullet 0 %"* is **not expressible** inside `VehicleDamage`, and
the exact single-knob answer *"both zero"* contradicts BmAK's rocket. The mapping is therefore
two-part, and the operator decision between them is explicit:

- **M1 (recommended, in domain):** rocket and cannon matched on the damage side at `H_J = 4000`
  (`k = 3.33333`); bullet left at JC3's shipped fraction and **ARM-1 restated as "small arms are
  ineffective, not free"** (≈ 14 shotgun pulls or ≈ 63 rifle rounds per Batmobile at 4000 HP, versus
  ∞ in BmAK).
- **M2 (exact, out of domain):** `H_J = 7200` and `invulnerable` left 0, with the rocket at 1500 →
  20.833 % and 5 hits, bullets at 1.5 %/0.7 % — still not zero, so M2 does not close the bullet gap
  either. It only removes the weapon-data edit.
- **M3 (exact both, whole-vehicle):** `invulnerable = 1` → bullet 0 % and rocket 0 %; equal to each
  other in both games only if BmAK's rocket is also treated as 0 %, which it is not.

### 6.6 Threshold / stage mapping (fractions, not members)

| BmAK stage | BmAK fraction of 1200 | nearest JC3 carrier | value to write at `H_J = 4000` |
|---|---:|---|---:|
| `ArmourLevels[3]` | 75 % | `smoke_threshold` (single value only) | 3000 |
| `ArmourLevels[2]` | 50 % | — no second smoke tier — | — |
| `ArmourLevels[1]` = `LowHealthWarningLevel` | **25 %** | `burn_threshold` (fire onset) | **1000** |
| on-fire mesh | UNKNOWN | `burn_threshold` + `burn_duration_s` 20 | shares the 1000 row |
| death | 0 % | `explosion_threshold` (and `explosion_delay_s`) | 0/1, or leave 4000 = never |
| generator steam/overheat | not health-based | **no carrier** (no shield in `VehicleDamage`) | — |

JC3 gives **one** smoke boundary, **one** burn boundary and one explosion boundary, so BmAK's five
bands collapse to three stages. Writing `smoke_threshold` 3000 and `burn_threshold` 1000 reproduces
the 75 % and 25 % BmAK boundaries in the build's own units. Both are **outside** the fleet's shipped
ranges (`smoke_threshold` 200…1050, `burn_threshold` 50…250 — `VOCABULARY.md`), so they are only
reachable by treating those fields as a health-threshold scale rather than as fleet-domain values.
By the project's own rule (`GRAB_BACKLOG.md` R4) that is an **undeclared switch** and must be labelled,
not shipped as a value.
In-domain equivalents at `H_J = 4000` are `smoke_threshold` 1050 (26.25 %) and `burn_threshold` 250
(6.25 %), which is what the build already ships.

### 6.7 Sensitivity and what would break the mapping

1. **`GetDamageMod`** (BmAK, native) scales every incoming hit by an unknown factor. If it is not
   1.0, every BmAK fraction above scales by it, and `k` scales by `1/GetDamageMod`.
2. **The generator pool** absorbs some damage before health in BmAK; the mapping treats the pool as
   already empty. With a full 2/3/4 pool the first hits cost health nothing.
3. **JC3 armour composition** is UNKNOWN (H0/H1/H2). The table assumes H0-or-neutral; the build's
   `bullet 5000 @ 99` is *not* neutral.
4. **Weapon → channel** is UNKNOWN (`DAMAGE_MODEL.md` step 3): whether an RPG lands in `explosion`
   or `bullet` changes which armour row applies, not the fraction.
5. **`max_health` unit** — absolute pool vs scale — is UNKNOWN (`ARMOR_STEP.md` §8). The mapping
   assumes absolute, as the 500…4000 census and the fleet's hit counts imply.
6. BmAK's archetype `Damage` numbers belong to the Batmobile's *own* projectiles (1.4 note).

---

## 7. What a build would change (if this is taken forward)

| row | file | change | oracle |
|---|---|---|---|
| HP-1 | `lave_health_medium.vmodc` copy, `.epe` `damage` hash repointed | `max_health` 2000 → **4000** (`k = 3.33333`) | ammo count: rocket survives with 20.8 % lost |
| HP-2 | same module | all eight `*_armor` 0 / `*_armor_strength` 0 (neutral) | shotgun round moves the bar by 3.6 % |
| HP-3 | same module | `smoke_threshold` 1050, `burn_threshold` 250 (in-domain) — **not** 3000/1000 | smoke at 26.25 %, fire at 6.25 % |
| HP-4 | `jc_weapons/06_vehicle/*` tunes (data, not module) | rocket blast 1500 → **833.33**; shell blast 1500 → **166.67** | 5 rocket hits, 24 shell hits |
| HP-5 | entity `.epe` | leave `invulnerable` **0** (M1) or set **1** (M3, whole-vehicle) | 200 rifle rounds: bar moves (M1) / no change (M3) |

None of these may be built until each has a take that can fail; HP-1…HP-5 are the takes above, and
the Q-1 damage probes (`DAMAGE_MODEL.md` §6) decide the armour composition that HP-2 depends on.

---

## 8. Reproduce / provenance

```
python Tools/scripts/bmak_damage.py --write|--check                 # DAMAGE_RULES.md/.json (BmAK)
python Tools/scripts/bmak_damage_layout_audit.py --write|--check    # DAMAGE_LAYOUT_AUDIT.md
python Tools/scripts/grab_model.py check                            # 423 named fields, offsets
python Tools/scripts/damage_predict.py --write|--check              # DAMAGE_MODEL.md/.json (JC3)
python Tools/scripts/jc3_armor_step.py --write|--check              # ARMOR_STEP.md/.json (armour bytes)
python Tools/scripts/jc3_damage_search.py --check                   # DAMAGE_MECHANISMS.json (root flags)
python Tools/scripts/bmak_hud_cluster.py                            # HUD health/armour tiers
```

Sources used, by claim: `Research/BatmobileGrab/DAMAGE_RULES.md` §3–§5 (health, members, per-weapon
damage), `DAMAGE_LAYOUT_AUDIT.md` §5 (bytecode for armour mode and ram), `CLASS_DEFAULTS.md` rows
120–145 (`ArmourLevels`, `LowHealthWarningLevel`, generator pool, on-fire/explosion refs),
`COLLISION_WHERE.md` lines 83–85, `OFFSETS.md` line 381, `FOOTAGE.md` line 158, `REMAINDER.md`
(`RVisualDamageComponent`), `Research/challenge/card-G1-14.md` A13/A17 (no damage-type table; native
signatures), `Research/JC3Grab/VOCABULARY.md` (`VehicleDamage`, `vehicle_damage.*`),
`Research/JC3Grab/DAMAGE_MODEL.md` §2–§7, `Research/JC3Grab/ARMOR_STEP.md` §5–§8,
`Research/JC3Grab/DAMAGE_MECHANISMS.md` §1–§3, `Research/JC3Grab/README.md` (effect usages),
`Tools/scripts/bmak_hud_cluster.py` lines 603–607.

## 9. UNKNOWN register (nothing below is assumed anywhere above)

1. `GetDamageMod`'s return value (native, `BatmanAK.exe`).
2. How much damage one weapon-generator unit absorbs, and the pool's regeneration rule.
3. `DamageLevel`'s threshold table and whether the fire state uses it.
4. The `RVisualDamageComponent` contents (untagged, ≤6 B, unparseable).
5. `HealthMax` vs `MaxHealth` — which one the car's 1200 is read against.
6. `HealthRecoverRate[difficulty]` values (unshipped CDO).
7. JC3's armour composition rule (H0/H1/H2) and the `max_health` unit.
8. JC3 weapon → armour channel mapping.
9. `smoke_threshold` / `burn_threshold` / `explosion_threshold`: health-remaining vs per-hit damage.
10. Whether BmAK's `Damage` archetype values are what NPC weapons deliver to the car.
11. The `vehicle_deform` module's named members (decoded file, no vocabulary rows).
