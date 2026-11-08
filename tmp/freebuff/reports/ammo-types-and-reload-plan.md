# Ammunition: BmAK magazines, reloads and heat against the JC3 tune members

What the donor carries per weapon, what a JC3 `WeaponTuning` can actually hold, and the value mapping
weapon by weapon. Read from `Research/BatmobileGrab/WEAPONS.md` + `WEAPONS.json` (G1-08/G1-09),
`WEAPONS_BOOLS.md`, `FOOTAGE.md`, `Research/JC3Grab/WEAPONS.md` + `WEAPONS.jsonl` (G2-10) and
`Working/Translation/T7_WEAPONS.md` (T-11). Nothing was launched or built.

## 1. Verdict

* **BmAK has no magazine at all.** A field scan of all 1,214 field rows in `WEAPONS.json` returns **no**
  `Ammo`, `Magazine`, `Clip`, `MaxAmmo` or `Round` member in any of the 62 weapon objects. The donor's
  weapons are **unlimited rounds gated by a cadence** (`RVehicleWeapon.FiringInterval`) and, on some
  gadgets, a **cooldown** (`RVehicleWeapon.WeaponCoolDown`).
* **BmAK's only reload-named fields time a sound, not a reload.** `RVehicleWeapon.ReloadSound`
  (a reference) and `RVehicleWeapon.ReloadSoundDuration` **0.4 s** (heavy cannon primary) / **0.5 s**
  (Joker heavy cannon) — the sound event's length. The bool `bReloading` exists and ships **false**;
  no object carries a reload duration.
* **BmAK's heat exists on one weapon and ships zero.** `RBatmobileCannon.HeatUpPerSecond` **0.0**,
  `OverheatOffValue` **0.25**, the overheat/cooled sound refs, and the HUD bar geometry
  `HeatBarStart` [0.79, 0.68] / `HeatBarSize` [0.125, 0.03]. `bOverheating` ships **false**. No other
  weapon object has a heat field.
* **JC3 has the ammo members and no heat model.** `magazine_size`, `reload_time_scale`,
  `unlimited_ammo`, `burst_count`, `burst_cooldown` are real tune members (`WEAPONS.md` §2, §10);
  overheat is a **proven absence** — no member of any decoded class names heat, cooling or
  temperature, and the only cooldown-shaped member is `burst_cooldown` (`WEAPONS.md:438,446-451`).
* **The mapping is therefore mostly a no-op, and that is the finding.** Unlimited + cadence on the
  BmAK side maps onto `magazine_size -1` + `unlimited_ammo 1` + `reload_time_scale 0`, which is what
  every relevant JC3 tune already ships. Nothing to write for ammo; nothing exists to write for heat.
* **The only real ammunition decision is the non-lethal round**: the riot suppressor's gel is the
  donor's one non-lethal ammunition type, and JC3 expresses it only as `damage = 0` + `impulse`
  (card **B-15**, `T-WP10`/`T-WP14`). EMP is the second non-damaging payload; it is a pulse/disable,
  not a round (card **B-18**).

## 2. Per-weapon BmAK values

`mag` = magazine size member, `reload` = reload time member, `heat` = overheat member. "none" means
**no such member exists on that object**, not zero. All values are from `WEAPONS.md` §8–§16 with the
offset the grab records.

| BmAK weapon (class · object) | mag | reload | heat / overheat | cadence & cooldown (the ammo model it actually uses) |
|---|---|---|---|---|
| **Vulcan / chain gun** — `RBatmobileCannon` · `Batmobile_Cannon_V2` (4 pkgs, 67 fields identical) | none | none on this object (only `ChainGun*` fields; `bReloading` false) | **`HeatUpPerSecond` 0.0** @0x0A78; `OverheatOffValue` **0.25** @0x0A80; `HeatBarStart` [0.79, 0.68] @0x0A88; `HeatBarSize` [0.125, 0.03] @0x0A90; `ChainGunOverheatSound` → `Engine.Play_Minigun_Overheat` (missing object); `ChainGunCooledSound` → `Play_Minigun_Cooled` (missing); `bOverheating` false | `FiringInterval` **0.138 s** @0x0828; `ComboFiringInterval` **0.138 s** @0x0B58; `ChainGunMaxSpinSpeed` 1440, accel 2500, decel 2000 |
| **Riot suppressor** — same object, riot fields | none | none | none | `RiotSuppressorFiringInterval` **0.75 s** @0x0AB4 (Joker cannon **0.333 s**); `RiotSuppressorLockOnAngle` **7.5°** (Joker **9.0**); `RiotSuppressorVillainImpulse` **6000** (Joker 1500); `ChainGunDamage` 40 / `UpgradedDamage` 50 is the only damage number on the object — the riot mode has **no damage member of its own** |
| **Heavy cannon** — `RBatmobileHeavyCannon` · `Batmobile_Heavy_Cannon_Primary` (3 pkgs, 41 fields identical) | none | **`ReloadSound`** → `Engine.Play_BML_HeavyCannon_Reload` (missing object) + **`ReloadSoundDuration` 0.4 s** @0x08F0 (Joker 0.5 s) — the sound's length | none | `FiringInterval` **2.0 s** (Joker 2.5); `ChargeUpTime` 2.5 s; `ChargeMaxDamageRadius` 0 |
| **Missile launcher** — `RBatmobileMissileLauncher` · `Batmobile_Missile_Launcher` (3 pkgs, 16 fields identical) | none | none | none | `RVehicleWeapon.WeaponCoolDown` **20.0 s** @0x0830 (the barrage cooldown); `FireInterval` is **absent on this object** and **0.5 s** on the Joker launcher @0x098C; `MaxTargets` 8 (Joker 12/16), `LockOnAngle` 40, `LockOnRange` 12000 |
| **EMP missile** — `RBatmobileEMPMissile` · `Batmobile_EMP_Missile_Launcher` (3 pkgs, 63 fields) | none | none | none | `WeaponCoolDown` **2.0 s**; `MissileLockOnDuration` 2 s / civilian 1 s; `Projectile.Damage` **absent** on `Batmobile_EMPMissile_Projectile_ForCars` — it disables, it does not damage (`T7_WEAPONS.md`, T-WP4) |
| **EMP burst** — `RBatmobileEMP` · `Batmobile_EMP_Burst` (3 pkgs, 36 fields) | none | none | none | `WeaponCoolDown` **2.0 s**; `DisableEnemyDuration`, `EMPImpulse`, `EMPVehicleImpulse` are declared and **serialise no value** in the three packages (`T7_WEAPONS.md`, T-WP5) |
| **Sonar** — `RBatmobileSonar` · `Batmobile_Sonar` (3 pkgs, 22 fields identical) | none | none | none | no cadence field; `ScanParticle`/`BlastParticle` + charge/scan sounds; the pulse is an entity object, no round |
| **Vehicle tracker** — `RPursuitModeMissileLauncher` · `Vehicle_Tracker` (3 pkgs, 7 fields identical) | none | none | none | `LaunchSocketName` `BattleModeSpotLight`, `LaunchRotationOffset` [5461, 0, 0]; projectile `Batmobile_Tracker_Projectile` |
| **Drone hacker** — `RBatmobileAllegianceSwitcher` · `Drone_Hacker` (3 pkgs, 13 fields identical) | none | none | none | `WeaponCoolDown` **1.0 s**; beam/success particles |
| **Winch** — `RBatmobileWinch` · `Batmobile_Winch` (3 pkgs, 21 fields identical) | none | none | none | no cadence, no cooldown: a rope, `ProjectileRope`/`StubRope` |
| **Booster** — `RBatmobileBooster` · `Batmobile_Booster` (4 pkgs, 2 fields) | — | — | — | not a weapon: `RInventoryGadget.Mesh` only (`T-WP11`) |

Cross-check: `WEAPONS_BOOLS.md:90,93` — `bOverheating` (0x10) and `bReloading` (0x80) are serialised
**false** on the cannon; `FOOTAGE.md:11-15,56-63,141-142` records the same 0.0 heat reading and states
plainly that a per-shot heat add in native code is **UNKNOWN** (the overheat path is wired but the
field adds nothing per second).

## 3. The JC3 tune members

`WeaponTuning`, one instance per `.wtune` (`Research/JC3Grab/WEAPONS.md` §2 lines 55-82, §10 425-454):

| member | type | shipped range (22 tunes) | meaning as the doc states it |
|---|---|---|---|
| `magazine_size` | int32 | **-1 … 8** (`WEAPONS.md:764`) | **-1 = no magazine** |
| `unlimited_ammo` | uint8 | **1 … 1** (all 22) | 1 = the weapon never runs dry |
| `reload_time_scale` | float | **0 … 1** (`WEAPONS.md:880`) | **0 = no reload step is scaled in**; it is a *scale*, not a duration |
| `burst_count` | uint8 | **1 … 6** | shots per burst |
| `burst_cooldown` | float | **0 … 5** s | seconds between bursts — the only cooldown-shaped member in the tune |
| `fully_automatic` | bool | 0/1 | hold to fire |
| overheat / heat per shot / cool rate | — | **proven absent** | "No member of any decoded class names heat, cooling or temperature…JC3 weapons therefore have no heat model at all" (`WEAPONS.md:438,446-451`) |

Per-weapon ammo rows for the four carriers T-11 uses (plus the three tunes that do carry a magazine):

| tune | block | fire_rate s | burst | burst_cd | magazine | reload_scale | unlimited_ammo |
|---|---|---|---|---|---|---|---|
| `w602_mediumtank_canon` | bullet | 1.75 | 1 | 0 | **-1** | **0** | 1 |
| `w603_mediumtank_mgun` | bullet | 0.1 | 1 | 0 | **-1** | **0** | 1 |
| `w618_sportsmuscle_missile` | missile | 0.5 | 1 | 0 | **-1** | **1** | 1 |
| `w619_buggy_mgun` | bullet | 0.1 | 1 | 0 | **-1** | **0** | 1 |
| `w609_fighterjet_missile_air_lockon` | missile | 0.2 | 1 | 1 | **8** | 1 | 1 |
| `w612_fighterbomber_missile_air_lockon` | missile | 0.5 | 1 | 0 | **2** | 1 | 1 |
| `w613_fighterbomber_missile_ground_lockon` | missile | 0.2 | 6 | 4 | **6** | 1 | 1 |
| `w614_monorailmissilecar_missile` | missile | 0.25 | 6 | 5 | -1 | 1 | 1 |

A direct read of all 25 records (`WEAPONS.jsonl`, every `tunes[].instances[].rows` path matching
`clip|ammo|reload|heat|overheat|burst|cool`) returns **only** `magazine_size`, `reload_time_scale`,
`unlimited_ammo`, `burst_count`, `burst_cooldown` and the AI-only `dropped_magazines[0..1]` — **no
heat member in any tune**, which is the same absence the doc states in prose.

## 4. The value mapping, weapon by weapon

`decoded` = read from the file; `derived` = computed here; `absent` = the member does not exist (a
file answer, not a zero); `UNKNOWN` = nothing decoded settles it. "Write:" is what a build would put
in the cloned tune; `—` means no edit, because the shipped value already equals the donor's model.

| BmAK weapon | magazine size | reload time | heat | JC3 member(s) and the value to write |
|---|---|---|---|---|
| **Vulcan** (`RBatmobileCannon`) | **absent on BmAK** → JC3 `magazine_size` **-1** (`w603`/`w619` already ship it) | **absent on BmAK** (no reload member; sound only) → `reload_time_scale` **0** (already) | BmAK `HeatUpPerSecond` **0.0**, `OverheatOffValue` 0.25 → **JC3 has no heat member**: write nothing; a heat bar is code + HUD (T-WP12's named omission) | `w603` clone: `fire_rate` 0.1 → **0.138** (T-11 edit), `burst_count` 1, `burst_cooldown` 0, `magazine_size` -1, `unlimited_ammo` 1, `reload_time_scale` 0 → **decoded**, all `—` except `fire_rate` |
| **Riot suppressor** (same object) | absent | absent | none | private bullet-tune copy: `fire_rate` **0.75**, `base_tuning.damage` **0**, `base_tuning.impulse` high (BmAK `ImpactMomentum` 60000 / `VillainImpulse` 6000), the two impulse factors 1, the three autoaim angle members **7.5** → **derived**; the mode itself has no member (B-15) |
| **Heavy cannon** (`RBatmobileHeavyCannon`) | absent | `ReloadSoundDuration` **0.4 s** (sound, not a reload) → no JC3 duration member; `reload_time_scale` **0** | none | `w602` clone: `fire_rate` 1.75 → **2.0** (T-11 edit), `magazine_size` -1, `unlimited_ammo` 1, `reload_time_scale` 0, `burst_count` 1, `burst_cooldown` 0 → **decoded** |
| **Missiles** (`RBatmobileMissileLauncher`) | absent | absent; `WeaponCoolDown` **20 s** is a barrage cooldown, not a reload | none | `w618` clone: `magazine_size` -1, `unlimited_ammo` 1, `reload_time_scale` 1, `burst_count` 1, `burst_cooldown` 0. A 20 s barrage beat has **no member**; nearest shipped shape is a 6-round burst with `burst_cooldown` 4–5 s (`w613`/`w614`), which changes the weapon's feel → **UNKNOWN/no write** |
| **EMP missile** (`RBatmobileEMPMissile`) | absent | absent; `WeaponCoolDown` 2.0 | none | `w618` clone for the flight + a `CForcePulse` copy; no ammo member changes. The disable has no tune member → **absent**, card B-18 |
| **EMP burst** (`RBatmobileEMP`) | absent | absent; `WeaponCoolDown` 2.0 | none | **no tune at all**: an entity `CForcePulse` on `truck_emp.ftune` (100 damage / 25 m, its own numbers) → **decoded**, but not an ammo row |
| **Sonar** (`RBatmobileSonar`) | absent | absent | none | no tune: `CForcePulse` + `gen_explosion_5m_nodamage.ftune` (**0 damage / 5 m**, push only, 2 pulses) → **decoded**; no round, so no ammo member |
| **Tracker** (`RPursuitModeMissileLauncher`) | absent | absent | none | `w618` clone + homing members (`missile_base_tuning.*`); ammo members stay -1 / 1 → **decoded** |
| **Drone hacker** (`RBatmobileAllegianceSwitcher`) | absent | absent; `WeaponCoolDown` **1.0 s** | none | a cooldown-shaped beat maps to **`burst_cooldown` 1.0** in the cloned tune (22 tunes ship the member, none at 1.0 except `w609`); the hack itself has no member → **derived** + B-19 |
| **Winch / booster** | — | — | — | no weapon tune: **absent**; the winch is an entity anchor + mesh (B-16), the booster is `arcade.nitro_boost` (T-WP11) |

What this table says in one line: **every value the donor would put into a magazine, a reload timer or
a heat gauge has no counterpart to receive it, and the JC3 side's "no magazine" default is exactly the
donor's model** — so the ammunition translation is a confirmation, not an edit, apart from the
non-lethal tune (B-15) and the `fire_rate` edits T-11 already owns.

## 5. Non-lethal ammunition types

| type | BmAK evidence | JC3 carrier | value mapping |
|---|---|---|---|
| **Riot gel round** (the one explicit non-lethal ammo) | `RiotSuppressorImpactEffect` → `Riot_Suppressor.Anti_firearm_gel_Miss`, `RiotSuppressorTracerSystem` → `Particles.Batmobile_RiotSuppressor_Tracer`, `RiotSuppressorShell` → `Particles.RiotSuppressor_BulletCasing`, `RiotSuppressorIndividualFireEvent` → `Engine.Play_RiotSuppressor_Bolt` (**missing object**), `RiotSuppressorHitSound` → `Play_RiotSupressor_Impacts` (**missing**); `ChainGunDamage` 40 is the only damage number, so the riot round has **no damage value of its own** | **no non-lethal member anywhere** (0 hits for stun/taser/shock/tranq/bean-bag/ragdoll/non-lethal across `WEAPONS.md`, `WEAPON_WIRING.md`, `DAMAGE_MECHANISMS.md`); damage is typed on the **part**, not the tune | `base_tuning.damage` **0**, `base_tuning.impulse` = the tune top, `vehicle_impulse_factor` / `object_impulse_factor` 1.0, `fire_rate` 0.75, gel VFX attached entity-side. Label **derived**; whether a 0-damage bullet still pushes is **UNKNOWN** (only the 0-damage *pulse* is shipped) — B-15's probe decides |
| **EMP round** (disables, does not damage) | `Projectile.Damage` **absent** on `Batmobile_EMPMissile_Projectile_ForCars`; `DisableEnemyDuration`/`EMPImpulse`/`EMPVehicleImpulse` serialise no value | `CEMPWeapon` (`w702_emp`: 500 damage / 50 m) and the entity `CForcePulse`; **no disable member in the tune** | fly a `w618`-class missile clone, then reach the disable through B-18's `CEMPWeapon`/pulse probe. Ammo member: none |
| **Sonar pulse** (non-damaging, not a round) | `RBatmobileSonar` scan/blast particles + charge; no damage number | `gen_explosion_5m_nodamage.ftune` (0 damage / 5 m) | pulse only; **no ammo member** |
| **Fear gas** | particle assets exist (`Batmobile_FearGas_Burnout`, `_KickUp`, `_NV` in `ASSETS.md`) but **no weapon field references them** | none found | **UNKNOWN** — asset names only, no weapon or ammo field binds them; not counted as an ammo type here |
| **Tracker round** | tracking projectile, lethal | `w618` clone | lethal, not non-lethal |

## 6. What the build must (and must not) do

1. **Do not add magazine logic.** No BmAK member sizes a magazine and no JC3 carrier needs one: the
   cloned tunes keep `magazine_size -1` + `unlimited_ammo 1` + `reload_time_scale 0`. If a build ever
   wants a magazine, the JC3 side can express it (`magazine_size` 2/6/8 ship in `w612`/`w613`/`w609`),
   but nothing on the donor side asks for it.
2. **Do not build a reload timer.** The only reload-shaped donor value is a 0.4–0.5 s **sound**
   (`ReloadSoundDuration`), and JC3's `reload_time_scale` is a scale whose 0 means "no reload step".
   A visible reload would be invented behaviour.
3. **Heat is BmAK-side only and zero.** `HeatUpPerSecond` 0.0 with `OverheatOffValue` 0.25 and a wired
   overheat sound means the donor itself never overheats in data; JC3 has no heat member at all. A
   heat gauge is therefore a code + HUD feature (T-WP12 already records it as a named omission), not
   a value to copy.
4. **`burst_cooldown` is the only cooldown member** and it is the right carrier for the hacker's 1.0 s
   and possibly the missile barrage's 20 s beat — but the barrage needs a design decision, because the
   shipped 20 s is a different beat from `burst_cooldown`'s 4–5 s examples.
5. **The non-lethal round is the one ammunition build**: B-15's private tune (`damage` 0, impulse kept,
   `fire_rate` 0.75, gel VFX) with its probe; no toggle exists.

## 7. UNKNOWNs (named, not filled)

- whether a **0-damage bullet** still applies impulse and hit reactions (only a 0-damage *pulse* is shipped);
- whether BmAK's native code adds **heat per shot** (the field is 0.0; the overheat path is wired, so a
  code-side add is not excluded — `FOOTAGE.md:14-15,142`);
- the unit/meaning of `OverheatOffValue` 0.25 and of `ImpactMomentum` 60000 beyond "impulse-like";
- the barrage's 20 s `WeaponCoolDown` beat as a tune value — no member expresses a 20 s beat without
  also changing burst shape;
- fear-gas ammunition: particle assets exist, but no weapon or ammo field binds them;
- the two riot sounds (`Play_RiotSuppressor_Bolt`, `Play_RiotSupressor_Impacts`) are `missing-object`
  in the grab, so the audio half of the non-lethal round cannot be carried from these files.

## 8. Evidence index

- `Research/BatmobileGrab/WEAPONS.md` §5 (field index: fire rate/cooldown, heat bar, damage, 574 audio),
  §8 (cannon: `HeatUpPerSecond` 0.0 @0x0A78, `OverheatOffValue` 0.25 @0x0A80, `HeatBarStart` [0.79,0.68],
  `HeatBarSize` [0.125,0.03], `ChainGunOverheatSound`/`CooledSound`, `FiringInterval` 0.138,
  `ChainGunDamage` 40/50, riot fields 0x0988–0x0AB8), §11 (heavy cannon: `ReloadSound`,
  `ReloadSoundDuration` 0.4/0.5 @0x08F0, `FiringInterval` 2.0/2.5), §12 (missile launcher:
  `WeaponCoolDown` 20.0 @0x0830), §13 (Joker launcher `FireInterval` 0.5), §14 (sonar), §15 (tracker),
  §16 (winch).
- `Research/BatmobileGrab/WEAPONS.json` — the machine-readable form of the same rows; a scan of its
  1,214 field rows for ammo/magazine/clip/reload/heat names returns 19 distinct matches, all
  `ReloadSound*`, `HeatUpPerSecond`, `OverheatOffValue`, `HeatBar*`, `ChainGunOverheatSound`,
  `TurretShotDamage` (enemy turret) and the `Upgraded*ShotProjectileArchetype` refs — no magazine.
- `Research/BatmobileGrab/WEAPONS_BOOLS.md:90,93` — `bOverheating` false, `bReloading` false.
- `Research/BatmobileGrab/FOOTAGE.md:11-15,56-63,118,141-142` — the 0.0 heat reading, the wired
  overheat path, and the statement that a per-shot heat add is not excluded.
- `Research/JC3Grab/WEAPONS.md` §2 55-82 (the per-tune magazine/reload/burst table), §10 425-454
  (member table + "overheat proven absent"), 757-769 and 880-882 (shipped ranges: magazine -1…8,
  reload 0…1, unlimited 1…1, burst 1…6, burst_cooldown 0…5).
- `Research/JC3Grab/WEAPONS.jsonl` — 25 records; a path scan for clip/ammo/reload/heat/burst/cool
  returns only the five members plus AI `dropped_magazines`, and no heat row at all.
- `Working/Translation/T7_WEAPONS.md` — T-WP1/T-WP2/T-WP3 (carriers and fire_rate edits),
  T-WP4/T-WP5 (EMP has no damage member), T-WP10/T-WP14 (riot: no non-lethal member, decision
  2026-10-28), T-WP12 (heat = named omission), §1 ("heat: `HeatUpPerSecond` 0.0 … both absent").
- `Research/specs/B-15.md` — the riot tune's 6 written values and the 0-damage probe.
- `tmp/freebuff/reports/non-lethal-cannon-carrier.md` — the absence scans and the pulse-vs-bullet gap.
