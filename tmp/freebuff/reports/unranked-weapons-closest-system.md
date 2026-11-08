# The four unranked Batmobile weapons — BmAK numbers, closest JC3 system, member mapping, build recipe

**Scope.** `OPERATOR_PRIORITIES.md` ranks the tracker+EMP missile (1), booster mesh (2), EMP burst (3),
hacker (4) and sonar (5), and says the **cannon, Vulcan, riot mode and missile pods are not ranked** — that
they are neither below sonar by default nor to be ranked without asking. This report does **not** rank
them. It does for those four what the ranking lane does for the five: every BmAK behaviour with its
numbers, the closest JC3 preset/entity by exact file, the member-by-member value mapping, what stays
unmatched, and the build recipe that closes each gap **with the closest JC3 system** (the 2026-11-06
rule: "JC3 has no system" is never an answer).

Read-only on the game install and the build trees. No archive, `.ee`, `.toc`, tune, module or tracker
row was written by this report.

**Labels** (`AGENTS.md`, R4 vocabulary): **decoded** = the shipped file's own number, read out;
**derived** = computed from a decoded value by one stated transform; **UNKNOWN** = no file evidence,
with the settling file named and a one-sentence pilot-card check that would settle it.

---

## 0. Naming: which BmAK object is which unranked weapon

Two names in BmAK collide with the operator's words, so the binding is stated before any number.

| operator's weapon | BmAK object (class / archetype) | BmAK's own `TempName` | evidence |
|---|---|---|---|
| **cannon** | `RBatmobileHeavyCannon` / `Batmobile_Heavy_Cannon_Primary` (4 packages, 165 fields, 41 per archetype) | `"Heavy Cannon"` (`RVehicleWeapon.TempName` @0x0814) | `Research/BatmobileGrab/WEAPONS.md` §11 |
| **Vulcan** | `RBatmobileCannon` / `Batmobile_Cannon_V2` (4 packages, 280 fields, 67 per archetype) | `"Chain Gun"` | `Research/BatmobileGrab/WEAPONS.md` §8 |
| **riot mode** | the *same* `RBatmobileCannon` object, riot field group @0x0AAC–0x0B8C — not a separate class | — (shares `"Chain Gun"`) | `WEAPONS.md` §8; `tmp/freebuff/reports/non-lethal-cannon-carrier.md` §1 |
| **missile pods** | `RBatmobileMissileLauncher` / `Batmobile_Missile_Launcher` (3 packages, 48 fields, 16 per archetype) | — (no `TempName` row) | `WEAPONS.md` §12 |

Two consequences that the rest of the report relies on:

1. **BmAK's "Chain Gun" is the Vulcan.** There is no separate "Vulcan" class. `RBatmobileCannon` carries
   the chain-gun fields *and* the riot-suppressor fields; the riot mode is a field group on the gun, not
   an object of its own. This is why riot mode needs a **second JC3 weapon entity** to exist at all
   (there is no class boundary in BmAK that a tune could mirror).
2. **The four packages carry identical values.** 0 of 1,065 field comparisons differ across
   Batmobile / MK2 / Funhouse (`WEAPONS.md` §3). The only retuned objects are the Joker-only ones
   (`Batmobile_JokerCannon_V2`, `Batmobile_JokerHeavy_Cannon`, `Batmobile_JokerMissile_Launcher`), which
   are recorded where they matter and are **not** the ship target.

### 0.1 What the build carries today

| weapon | private tune in the build | values written | where |
|---|---|---|---|
| cannon | `editor/entities/jc_weapons/06_vehicle/w602_batmobile_cannon/w602_batmobile_cannon.wtunec` | `fire_rate` 2.0 (`old` 1.75), `velocity` 400.0 (`old` 500.0) — read back equal | `Working/Weapons/manifest.json` (B-06), present in `Builds/bm-006`, `bm-RC2`, `bm-RC3-parts` |
| Vulcan | `…/w603_batmobile_vulcan/w603_batmobile_vulcan.wtunec` | `fire_rate` 0.138 (`old` 0.1) — read back equal | same |
| riot mode | **none** | — | `Research/specs/B-15.md` is the card; it is not built |
| missile pods | **none** (the donor's `w618_sportsmuscle_missile` binding survives, un-cloned) | — | `Working/Weapons/manifest.json` row `T-WP3` has `"private": null` |

So two of the four already have a carrier in the tree, and two have a written card but no build. This
report supplies the numbers and the remaining recipes; it does not install anything.

---

## 1. Cannon — `RBatmobileHeavyCannon` / `Batmobile_Heavy_Cannon_Primary`

### 1.1 BmAK behaviour, with numbers (all **decoded**)

| quantity | member | value | note |
|---|---|---:|---|
| fire rate | `RVehicleWeapon.FiringInterval` @0x0828 | **2.0 s** | one round per press cycle |
| charge | `RBatmobileHeavyCannon.ChargeUpTime` @0x0B00 | **2.5 s** | hold-to-charge before the shot |
| charge radius | `…ChargeMaxDamageRadius` @0x0B04 | **0.0** | charge adds no radius |
| damage | `Projectile.Damage` (primary projectile) | **50.0** | 24 hits to destroy the Batmobile at `Health` 1200 (T-7 §1) |
| turret-shot damage | `RBasicProjectile.TurretShotDamage` | **75** | upgraded variants `Damage` 75 / `TurretShotDamage` 110 |
| damage radius | `Projectile.DamageRadius` | **0.0** | direct hit only; the blast is a separate impulse component, not radial damage |
| projectile speed | `Projectile.Speed` | **40000 UU/s = 400 m/s** | `MaxSpeed` 48000 = **480 m/s** |
| projectile gravity | `RBasicProjectile.InitialAcceleration` | **[0, 0, −1000]** | constant, no lifetime serialized |
| momentum | `Projectile.MomentumTransfer` | **66666.671875** | plus `RecoilImpulse` **15000.0** on the gun |
| spread | — | **no member** | the heavy cannon has no `InaccuracyAngle`/`InaccuracyVsTime` row |
| ammo / magazine | — | **no member** (0 of 41 archetype fields, 0 of 165 class fields) | ammo is unlimited in data; the only limiter is the 2.0 s interval |
| reload | `RVehicleWeapon.ReloadSound` + `ReloadSoundDuration` | **0.4 s** | a reload step is audible; no clip size to reload |
| lock-on | `LockOnAngle` **15.0°**, `LockOnTimeMin` **0.5 s**, `LockOnTimeMax` **6.0 s** | — | acquire cone and the time window it may grow in |
| lethal envelope | `RVehicleWeapon.LethalRadius` | **175.0** | `LethalRange` is not serialized on this object |
| power | `RVehicleWeapon.PowerConsumption` | **0.0** | free to fire |
| muzzle | `SWeaponPoint` at BmAK socket `CannonMuzzle` on `Batmobile_Rig_Weapons_Heavy_Cannon_Barrrel_02` | built (0.000339, 1.702497, −0.455945) m, |d| **0.000 cm** | `tmp/freebuff/reports/weapon-points-vs-bmak.md` |

FX / audio, all decoded references: `Particles.Batmobile_canonMuzzleflash` (FireFX),
`Particles.Batmobile_HeavyCannon_Impact` (impact, 8 emitters), trail
`Particles.Rocket.Batmobile_CanonTrail`, sound `Engine.Play_BML_HeavyCannon_Fire` (**missing-object**),
`Play_BML_HeavyCannon_Reload` (**missing-object**), impact
`Ww_VFX_Tank_Explosion.Play_Batmobile_HeavyCannon_Explosion` (resolved).

### 1.2 Closest JC3 preset and entity

| item | value | evidence |
|---|---|---|
| **tune (preset)** | `editor/entities/jc_weapons/06_vehicle/w602_mediumtank_canon/w602_mediumtank_canon.wtunec` | `Research/JC3Grab/WEAPONS.md` §1, §2 |
| **private copy in the build** | `…/w602_batmobile_cannon/w602_batmobile_cannon.wtunec` | `Working/Weapons/manifest.json` |
| **carrier entity** | `editor/entities/jc_vehicles/01_land/v0201_car_capstone_mediumtank/v0201_car_capstone_mediumtank_debug.ee` (7 carriers: 3 medium/bavarium tank variants, cargo transport, and the APC pair) | `Research/JC3Grab/WEAPON_WIRING.md` |
| **slot** | `main_weapon` (`id:851CAABE`) | `WEAPON_WIRING.md:305` |
| **fire point** | `fire_position_0`, world (0.247, 0.485, −2.018), parent part `mediumtank_cannon` | `WEAPON_WIRING.md:314` |
| **part behaviour** | `Cannon` (index 38) parented to `Turret` (index 26) | `WEAPON_WIRING.md:52` |
| **blast** | `ForcePulseSettings` in the same bundle: player **1500** in **8 m**, AI **550** in **6 m** | `WEAPONS.md` §8 |
| **autoaim** | `autoaim_vehicle_mgun.wtune` | `WEAPONS.md` §1 |
| **alternative preset** | `w616_corvette_canon` (fire_rate 1.5, blast 1500/8 m, tracer 100) — closer on cadence than w602's 1.75? no: 1.75 is closer to 2.0 than 1.5 is to 2.0 **only if** the interval is the only criterion; 1.5 is equally far. w602 wins because it is the same role (tank main gun) and already carries the slot wiring | `WEAPONS.md` §2, §8 |

### 1.3 Member-by-member mapping

| BmAK quantity (decoded) | JC3 member (decoded) | transform | class |
|---|---|---|---|
| `FiringInterval` 2.0 s | `fire_rate` 1.75 → **2.0** | same unit, seconds between shots | **decoded→direct**; applied and read back 2.0 |
| `Projectile.Speed` 40000 UU/s | `velocity` 500 → **400** | ÷100 (1 UU = 1 cm, the project's one scale) | **derived**; applied and read back 400.0 |
| `Projectile.MaxSpeed` 48000 | — (no max-speed member) | — | **UNKNOWN** |
| `Projectile.Damage` 50.0 | `base_tuning.damage` 1 + blast `PlayerDamage` 1500 | no unit bridge; the kill ratio is carried by the health row (24 hits ⇒ `max_health` 36000, T-14), never by the weapon | **derived** (policy, T-7 §1) |
| `TurretShotDamage` 75 | `ai_tuning` side (`AIDamage` 550, `ai damage` 20) | closest: the AI side is the only "second shooter" damage the tune has | **UNKNOWN** (semantics differ) |
| `DamageRadius` 0.0 | `PlayerDamageRadius` 8 m (fleet min **1.5 m**) | BmAK has no radial damage; JC3 always resolves a blast | **derived**: set 1.5 m, the fleet minimum, to approximate a direct hit |
| `MomentumTransfer` 66666.67 + `RecoilImpulse` 15000 | `base_tuning.impulse` 0 (bullet band 0–100) + `recoil_pitch/yaw` [0,0] | no unit bridge; the shove crosses as the band top instead (C-7), not as 1/666 of the value | **UNKNOWN** |
| — (no spread member) | `scatter` 0.6/0.6/0, recover 0.4, reset 1.15 | keep the shipped scatter: BmAK has nothing to convert | **decoded (fleet)** |
| `ChargeUpTime` 2.5 s | — (no charge member in 175 decoded rows) | — | **UNKNOWN** |
| `LockOnAngle` 15.0° | `AngleThresholdNewTarget`/`AngleThresholdCurrentTarget` (AutoAim; observed 0–1.4) | angle unit unproven (the 7.5/15 vs 0–1.4 gap is 10×) | **UNKNOWN** |
| `LockOnTimeMin/Max` 0.5 / 6.0 s | — (`AutoAim` = 22 members, none a duration) | — | **UNKNOWN** (T-WP3b) |
| `LethalRadius` 175.0 | `PlayerDamageRadius` 8 m / `MaxAimDistance` 70 m | no radius member at 175 m scale | **UNKNOWN** |
| `ReloadSoundDuration` 0.4 s | `reload_time_scale` **0** (no reload step) | JC3 has no reload animation to time; only the sound can be 0.4 s | **derived** (sound-only) |
| no magazine | `magazine_size` **−1**, `unlimited_ammo` **1** | both sides unlimited ⇒ direct | **decoded** |
| `CannonMuzzle` socket | `SWeaponPoint` (0.000339, 1.702497, −0.455945) | already matched 0.000 cm | **decoded** |
| FX `Batmobile_canonMuzzleflash`, `Batmobile_HeavyCannon_Impact` | `tank_canon_muzzleflash.effc` on 11 vehicles; `tank_explosive_*` hit family | asset mapping, T-17 | **decoded** |

### 1.4 What is unmatched, and the build recipe that closes it

| # | unmatched | closest JC3 system | build recipe | closes when |
|---|---|---|---|---|
| C-1 | **charge gate** (2.5 s hold before the shot) | the tune has no charge member; the closest carrier is a **second weapon entity** on the same muzzle whose `fire_rate` is the charge time | author `w602_batmobile_cannon_charged.wtunec` = the clone with `fire_rate` **2.5**; bind it as a second component on the cannon node; both entities share the CannonMuzzle point | Q-3 #3 compares a tap (2.0 s cadence, direct shot) with a held shot (2.5 s cadence, charging FX): the two must differ in cadence, not in damage |
| C-2 | **radial blast vs direct hit** (`DamageRadius` 0, JC3 8 m) | `ForcePulseSettings.PlayerDamageRadius` (fleet min 1.5 m) | in the private bundle, write `PlayerDamageRadius` **1.5** and `AIDamageRadius` **1.5**; keep `PlayerDamage` 1500 | a shell on a wall damages only the wall panel it hits (1.5 m) instead of an 8 m disc |
| C-3 | **`MaxSpeed` 480 m/s** (a ballistic cap) | none in the tune; the closest is `velocity` + `gravity_on`/`gravity_strength` | keep `velocity` 400, `gravity_strength` 30 (w602's own); record the cap as not carried | Q-3 #3 flight time to 40 m is 0.10 s (400 m/s) and does not speed up at range |
| C-4 | **`TurretShotDamage` 75** (a different damage when a gunner fires) | the tune's separate `ai_tuning` side | set `ai_tuning.base_tuning.damage` and blast `AIDamage` from the BmAK turret number, 75 (the closest second-side member) | an NPC-paid gunner firing the cloned cannon does 75-scale damage, not 50 |
| C-5 | **lock-on time 0.5–6.0 s** | `AutoAim` has no duration; the HUD POI is the lock marker (`POI_TYPE_LOCK_ON_TARGET` 21) | write the angles 15 into `AngleThreshold*`/`StickyAimStartAngle`; the *time* is carried by the HUD marker rotation (1.5 s) only | Q-3 #3: the reticle's lock marker appears within 6 s of holding aim on a tank and never after, and the time is the HUD's, not the tune's |
| C-6 | **reload step 0.4 s** | `reload_time_scale` 0 + the weapon entity's own attached effects | attach a 0.4 s reload cue on the weapon entity; do not write a reload into the tune | a reload beat is audible after each shot and the gun does not fire during it |
| C-7 | **impulse 66666 / recoil 15000** | `base_tuning.impulse` (band 0–100) + `vehicle_impulse_factor` 1.0 | impulse **100**, `vehicle_impulse_factor` **1.0**, `object_impulse_factor` **1.0** — the band top, the closest value the member can hold | a shell shoves a car measurably (the Q-1 push check), not by 66,666 units |

C-1 is the only one that needs a **new entity**; C-2/C-7 are tune-byte edits inside the private copy;
C-3/C-5/C-6 are attach-side and HUD-side.

### 1.5 UNKNOWNs (settling file + pilot-card check)

| id | UNKNOWN | settling file | one-sentence pilot-card check |
|---|---|---|---|
| UC-1 | BmAK's `MaxSpeed` 480 m/s behaviour (is the shell capped, or is 480 only the initial ramp ceiling?) | `Research/BatmobileGrab/CLASS_DEFAULTS.md` (`Default__RBasicProjectile`) and `Working/vendor/BmAKgrab/scripts/` for the projectile tick | Q-3 #3: fire at a 200 m wall and at a 400 m wall; if the second impact is late by more than 400/480 s the cap is real, if both match 400 m/s it is not |
| UC-2 | whether `TurretShotDamage` is the AI-paid damage or a tank-turret-only override | `Research/BatmobileGrab/CLASS_DEFAULTS.md` (`Default__RBatmobileHeavyCannon`) | Q-3 #3: let an NPC gunner fire the cannon at an APC; if the APC loses more health than a player shot does, the 75 is a separate side and C-4 is right |
| UC-3 | the charge mechanic's gate (does holding the trigger change the round, or only its timing?) | `BmGame.upk` `Default__RBatmobileHeavyCannon` + the native function list in `Research/BatmobileGrab/REGISTRATION.md` | Q-3 #3: tap vs hold the trigger; if the held shot is identical in effect the 2.5 s is only a cadence, and C-1's second entity is unnecessary |
| UC-4 | the `AutoAim` angle unit (is 15° = 0.26 in the tune's unit, or 15?) | `Research/JC3Grab/WEAPONS.md` §9 (three presets, six contexts) and `E:/Modding/JustCause3/_grab/weapons/w602_mediumtank_canon/` | Q-3 #3: aim 10° off a tank at 50 m; if the reticle snaps, the written angle is larger than 10° and the unit is degrees, not fractions |
| UC-5 | what `LethalRadius` 175.0 gates (175 cm? 175 m? a HUD ring?) | `Research/BatmobileGrab/CLASS_DEFAULTS.md` and `HUD_SPEC.json` | Q-3 #3: fire at a target 170 m and 180 m away; if only the nearer one acquires, 175 is metres |

---

## 2. Vulcan — `RBatmobileCannon` / `Batmobile_Cannon_V2` (BmAK's "Chain Gun")

### 2.1 BmAK behaviour, with numbers (all **decoded**)

| quantity | member | value | note |
|---|---|---:|---|
| fire rate | `RVehicleWeapon.FiringInterval` @0x0828 | **0.138 s** | 7.25 rounds/s |
| combo rate | `RBatmobileCannon.ComboFiringInterval` @0x0B58 | **0.138 s** | identical to the base rate |
| damage | `RBatmobileCannon.ChainGunDamage` @0x0B64 | **40** | upgraded **50** (`UpgradedDamage` @0x0B68) |
| aim spread | `RBatmobileCannon.InaccuracyAngle` @0x0A70 | **0.1** | base cone |
| spread growth | `InaccuracyVsTime.Points` @0x0C4C | **(0 s, 0.0), (0.5, 0.0), (1.5, 1.5), (2.5, 3.0)**, linear | upgraded curve: (1.0, 3.0), (3.0, 1.5), (5.0, 3.0) |
| heat per second | `HeatUpPerSecond` @0x0A78 | **0.0** | nothing in the object adds heat with time |
| overheat release | `OverheatOffValue` @0x0A80 | **0.25** | the bar drops to 25% when it releases |
| heat bar | `HeatBarStart` [0.79, 0.68], `HeatBarSize` [0.125, 0.03] | — | HUD rectangle |
| barrel spin | `ChainGunMaxSpinSpeed` **1440 °/s**, `SpinAccel` **2500**, `SpinDecel` **2000** | — | 1440 °/s = **240 rpm** (derived) |
| impulse | `ImpactMomentum` **60000.0**, `RecoilImpulse` **400.0** | — | per-hit shove and per-shot recoil |
| ammo / magazine | — | **no member** (0 of 67 archetype fields) | unlimited in data; the heat bar is the only limiter, and it adds no heat per second |
| reload | — | **no member** | no reload step at all |
| projectile speed | — | **no `Projectile` archetype on this object** | the chain gun serializes *no* projectile speed |
| muzzle | socket `ChainGunMuzzle` on `Batmobile_Rig_Weapons_Machine_Gun_01` | built (−0.407368, 1.551869, −0.166883) m, |d| **0.000 cm** | `weapon-points-vs-bmak.md` |
| casings | socket `ChainGunShells`, `Particles.ChainGun_BulletCasing` | — | ejection point decoded |
| screenshake | `ChainGunScreenShake` 0.15 s, [−20,0,0], [7,0,0], [300,100,0], [2,2,2] | — | |
| FX / audio | tracer `Particles.Batmobile_Muzzleflash_Tracer`, no-tracer `Batmobile_Muzzleflash_NoTracer`, loop `Engine.Play_Minigun_Fire`, combo in/out, overheat/cooled | all four **missing-object** | `WEAPONS.md` §8 ref table |

Two decoded absences matter more than any value: **heat adds nothing per second** (`HeatUpPerSecond` 0.0,
confirmed by `FOOTAGE.md` §2), and **no projectile speed exists on the object**. The second is the reason
the Vulcan's JC3 `velocity` is the donor's number kept, not a translation (V-5 keeps it and the Q take measures it).

### 2.2 Closest JC3 preset and entity

| item | value | evidence |
|---|---|---|
| **tune (preset)** | `editor/entities/jc_weapons/06_vehicle/w603_mediumtank_mgun/w603_mediumtank_mgun.wtunec` | `Research/JC3Grab/WEAPONS.md` §1–§6 |
| **private copy in the build** | `…/w603_batmobile_vulcan/w603_batmobile_vulcan.wtunec` (`fire_rate` 0.138 written) | `Working/Weapons/manifest.json` |
| **carrier entity** | `v0201_car_capstone_mediumtank_debug.ee` (same 7 carriers as the cannon) | `WEAPON_WIRING.md` |
| **slot** | `secondary (id:00568A74)` — the tank's second driver slot | `WEAPON_WIRING.md:305` |
| **fire point** | `fire_position_0` world (−0.407, 1.552, −0.167) | `WEAPON_WIRING.md:314` |
| **spin donor** | `w619_buggy_mgun` on `v0604_car_urga_buggy` — the only **CCar** whose entity carries a `GatlingGun` part (`weapon_rpm`) | `Research/JC3Grab/MOVING_PARTS.md:127` |
| **tune values (decoded)** | fire_rate 0.1, burst 1, full-auto 1, magazine −1, unlimited 1, reload_scale 0, max_range 200, velocity **750**, damage 190 (veh ×0.3, impulse 60), AI 20 (veh ×1.3, impulse 20), scatter 0.6/0.6/0, recover 0.4, reset 1.15, tracer 750/20/ttl 0.25, ricochet 0.1×1, gravity off | `WEAPONS.md` §2–§6 |
| **autoaim** | `autoaim_vehicle_mgun.wtune` (also used by 37 components) | `WEAPONS.md` §13 |

### 2.3 Member-by-member mapping

| BmAK quantity (decoded) | JC3 member (decoded) | transform | class |
|---|---|---|---|
| `FiringInterval` 0.138 s | `fire_rate` 0.1 → **0.138** | same unit, same quantity | **decoded→direct**; applied and read back 0.138 |
| `ComboFiringInterval` 0.138 | `burst_count` 1 / `fully_automatic` 1 | BmAK's "combo" is a sustained-fire mode with its own entry/exit sounds; JC3's closest is full-auto with no mode | **UNKNOWN** |
| `ChainGunDamage` 40 (upgraded 50) | `base_tuning.damage` 190, `vehicle_damage_factor` **0.3** ⇒ 57 per vehicle hit | no unit bridge; keep the donor's number, ratio lives in the health row | **derived** (policy) |
| `InaccuracyAngle` 0.1 | `scatter_minimum`/`scatter_maximum` 0.6 | JC3's fleet minimum is 0.2; 0.1 is below it | **derived**, declared switch (below the observed band) |
| `InaccuracyVsTime` 4 points (0→0, 0.5→0, 1.5→1.5, 2.5→3.0) | `scatter_per_shot` + `scatter_recover_rate` 0.4 + `scatter_reset_time` 1.15 | JC3 has no time-keyed scatter curve; at 7.25 rps, 3.0° over 2.5 s is 18 rounds ⇒ **0.167°/shot** (derived) | **derived** |
| `ChainGunMaxSpinSpeed` 1440 °/s | `GatlingGun` part behaviour `weapon_rpm` (rotoscope 20.0; only CBoat/CHelicopter use it) | 1440 °/s ÷ 6 = **240 rpm**; the member's unit is not stated | **derived** (value), **UNKNOWN** (unit) |
| `SpinAccel` 2500 / `SpinDecel` 2000 | — (`weapon_rpm` is one number) | spin ramp has no member | **UNKNOWN** |
| `HeatUpPerSecond` 0.0, `OverheatOffValue` 0.25, heat bar | — (JC3 has **no heat member at all**; `WEAPONS.md` §10) | both sides add no heat; the HUD bar has no carrier (T-19) | **decoded (fleet)**: absent |
| no magazine | `magazine_size` −1, `unlimited_ammo` 1 | both unlimited | **decoded** |
| no reload | `reload_time_scale` 0 | both absent | **decoded** |
| — (no projectile speed) | `velocity` 750 kept | nothing to convert | **UNKNOWN** (BmAK side) |
| `ImpactMomentum` 60000 | `base_tuning.impulse` 60 (band 0–100) | no bridge; band top is 100 | **UNKNOWN** |
| `RecoilImpulse` 400 | `recoil_pitch/yaw` [0, 0] | not carried | **UNKNOWN** |
| `ChainGunMuzzle` / `ChainGunShells` sockets | `SWeaponPoint` (−0.407368, 1.551869, −0.166883) matched; casings socket | matched 0.000 cm | **decoded** |
| `Batmobile_Muzzleflash_Tracer`, `ChainGun_BulletCasing` | tracer `.effc` + casing particle on the entity | asset-side, T-17 | **decoded** |

### 2.4 What is unmatched, and the build recipe that closes it

| # | unmatched | closest JC3 system | build recipe | closes when |
|---|---|---|---|---|
| V-1 | **time-keyed spread curve** (2.5 s to 3.0°) | `scatter_per_shot` + `scatter_recover_rate` + `scatter_reset_time` | in `w603_batmobile_vulcan.wtunec` write `scatter_per_shot` **0.167**, `scatter_minimum`/`maximum` **0.1**, recover 0.4, reset 1.15 | a 2.5 s held burst ends with a ~3° reticle (Q-3 #3 bolt-group width), and a 0.5 s burst shows none |
| V-2 | **barrel spin while firing** (1440 °/s, ramp 2500/2000) | the `GatlingGun` part behaviour + `weapon_rpm` on a **Ccar** — unproven on cars (0 of 24 cars) | add a `GatlingGun` rotating part on the barrel bone with `weapon_rpm` **240**; ramp not carried | Q-3 #3: the barrels visibly spin only while the trigger is down, and stop within ~0.7 s (1440/2000) |
| V-3 | **heat model** (bar grows, releases at 0.25, two sounds) | none: `HeatUpPerSecond` is 0 on the BmAK side and JC3 has no heat member | no tune work; the HUD bar is a named omission in T-19, and the two overheat sounds are missing objects | Q-3 #3: a 10 s burst never stops firing (BmAK's own data predicts this), and the take is recorded as "no heat", not as a failure |
| V-4 | **combo mode** (entry/exit, 0.138 s) | `fully_automatic` 1 + the weapon entity's looping fire event | keep full-auto; attach `Play_Minigun_Combo_Fire` if a bank copy is found (it is a missing object today) | Q-3 #3: sustained fire has one loop and no mode-change beat; if the beat is required, the missing bank is the gap |
| V-5 | **projectile speed** | `velocity` 750 (donor) | keep 750; do not claim a translation | Q-3 #3: a 100 m wall is hit in 0.13 s (750 m/s); if the game's own Vulcan reads slower, the donor number is wrong |
| V-6 | **impulse 60000 / recoil 400** | `base_tuning.impulse` (band 0–100) + factors 1.0 | impulse **100**, factors **1.0** | a burst nudges a car (push check) rather than throwing it |
| V-7 | **spin ramp 2500/2000 °/s²** | `weapon_rpm` only (no accel member) | not carried; the spin reaches 240 rpm by the `GatlingGun` behaviour's own ramp | Q-3 #3: time from trigger to full spin; record it as the game's ramp, not BmAK's |

### 2.5 UNKNOWNs (settling file + pilot-card check)

| id | UNKNOWN | settling file | one-sentence pilot-card check |
|---|---|---|---|
| UV-1 | the chain gun's **projectile speed** (no `Projectile` archetype on the object) | `Research/BatmobileGrab/CLASS_DEFAULTS.md` (`Default__RBatmobileCannon`) | Q-3 #3: fire at a 100 m wall and time the impact — 0.13 s means 750 m/s, 0.25 s means 400 m/s |
| UV-2 | whether `ChainGunDamage` 40 is per round or per burst tick | `Working/vendor/BmAKgrab/scripts/` (the native `ChainGun` fire loop) + `Research/BatmobileGrab/REGISTRATION.md` | Q-3 #3: hold the trigger 2 s on a stock car and count hits from the tracer stream; 40 × hits must match the health loss |
| UV-3 | `weapon_rpm`'s unit (rpm, or a fraction of `rotoscope_rpm_per_cycle`) | `Research/JC3Grab/MOVING_PARTS.md:71` and `Research/BatmobileGrab/ANIMATIONS.md` for the barrel bone | Q-3 #3: count barrel revolutions in 1 s of video — 4 rev/s means rpm, 1 rev/s means the member is a fraction |
| UV-4 | whether the engine honours `scatter_per_shot` as a per-round bloom | `E:/Modding/JustCause3/_grab/weapons/w603_mediumtank_mgun/w603_mediumtank_mgun.wtunec` (decoded rows) | Q-3 #3: fire 18 rounds into a wall and measure the group; it must be ~3° wide, not 0.6° |

---

## 3. Riot mode — the `RBatmobileCannon` riot field group (no class of its own)

### 3.1 BmAK behaviour, with numbers (all **decoded**)

| quantity | member | value (`Batmobile_Cannon_V2`) | Joker variant |
|---|---|---:|---:|
| fire rate | `RiotSuppressorFiringInterval` @0x0AB4 | **0.75 s** | 0.333 s |
| lock cone | `RiotSuppressorLockOnAngle` @0x0AAC | **7.5°** | 9.0° |
| range | `RiotSuppressorRange` @0x0AB0 | **not serialized** (class default) | 8000 |
| villain impulse | `RiotSuppressorVillainImpulse` @0x0AB8 | **6000.0** | 1500.0 |
| impact momentum | `ImpactMomentum` @0x0A68 | **60000.0** | 2000.0 |
| damage | — | **no riot damage member**; the only damage on the object is `ChainGunDamage` **40** | 999 |
| ammo / magazine | — | **no member** | — |
| reload | — | **no member** | — |
| impact | `RiotSuppressorImpactEffect` | `Riot_Suppressor.Anti_firearm_gel_Miss` (gel, non-penetrating) | — |
| tracer / casing | `RiotSuppressorTracerSystem`, `RiotSuppressorShell` | `Batmobile_RiotSuppressor_Tracer`, `RiotSuppressor_BulletCasing` (both resolved) | — |
| audio | `RiotSuppressorIndividualFireEvent`, `RiotSuppressorHitSound` | `Play_RiotSuppressor_Bolt`, `Play_RiotSupressor_Impacts` — **both missing-object** | — |
| screenshake | `RiotSuppressorFireScreenShake` | 0.25 s, [−20,0,0], [7,0,0], [300,0,0], [2,2,2] | — |
| casing socket | `RiotSuppressorShellsSocket` | `"RiotSuppressorShells"` | — |

The decisive fact is a **decoded absence**: there is no `RiotSuppressorDamage`, no non-lethal flag, and no
mode bit. The mode is cadence + cone + impulse + gel VFX on the same gun (`non-lethal-cannon-carrier.md`
§1). `RiotSuppressorRange` 8000 is serialized only on the Joker object, so the ship target's range is a
class default = UNKNOWN value.

### 3.2 Closest JC3 preset and entity

| item | value | evidence |
|---|---|---|
| **closest system** | a private copy of the built bullet tune with `base_tuning.damage` **0**, `base_tuning.impulse` at the band top, and the autoaim angles | `Research/specs/B-15.md`; `WEAPONS.md` §3 (bullet damage band 1…3000, impulse 0…100) |
| **only shipped 0-damage tune** | `gen_explosion_5m_nodamage.ftune` — 0 player / 0 AI damage, 5 m, push only (a **pulse**, not a bullet) | `Research/JC3Grab/FORCEPULSE.md` §3 |
| **tune to copy** | `…/w603_batmobile_vulcan/w603_batmobile_vulcan.wtunec` (or the cannon clone for a shell-sized gel round) | `Working/Weapons/manifest.json` |
| **autoaim preset** | `autoaim_vehicle_mgun.wtune` — `AngleThresholdNewTarget`/`CurrentTarget`, `StickyAimStartAngle`, 6 contexts | `JC3Grab/WEAPONS.md` §9 |
| **toggle carrier** | none: a **second weapon entity** (the tune has no mode member) | `T-WP14`/`T-WP10`, `B-15.md` §2 |
| **slot** | the second driver slot `id:00568A74` — already occupied by the Vulcan; a third slot does not exist (T-WP13) | `WEAPON_WIRING.md` §2b |

### 3.3 Member-by-member mapping

| BmAK quantity (decoded) | JC3 member | value to write | class |
|---|---|---|---|
| `RiotSuppressorFiringInterval` 0.75 | `fire_rate` | **0.75** | **decoded→direct** |
| `RiotSuppressorLockOnAngle` 7.5 | `AngleThresholdNewTarget`, `AngleThresholdCurrentTarget`, `StickyAimStartAngle` | **7.5** ×3 (which member is the cone is UNKNOWN) | **derived** |
| `RiotSuppressorVillainImpulse` 6000, `ImpactMomentum` 60000 | `base_tuning.impulse` + `vehicle_impulse_factor`/`object_impulse_factor` | impulse **100** (player) / **40** (AI), factors **1.0** | **derived** |
| `ChainGunDamage` 40 (the riot mode has no damage of its own) | `base_tuning.damage` | **0** | **derived** |
| gel impact, tracer, casing | `.effc`/particle attachments on the weapon entity (not tune members) | the three assets | **decoded** |
| `RiotSuppressorIndividualFireEvent`, `HitSound` | — | missing objects | **decoded** (absent) |
| `RiotSuppressorRange` (class default) | `MaxAimDistance`/`AlwaysTargetDistance` | 80 (if the 8000 UU default is adopted) | **UNKNOWN** |
| `RiotSuppressorFireScreenShake` | `CameraShakeModifierParams` (fields undecoded) | not carried | **UNKNOWN** |
| *mode switch* | — | none | **UNKNOWN** (entity identity only) |

### 3.4 What is unmatched, and the build recipe that closes it

| # | unmatched | closest JC3 system | build recipe | closes when |
|---|---|---|---|---|
| R-1 | **non-lethality** (no flag exists in either game) | `base_tuning.damage` 0 + impulse | `B-15.md` steps 1–2: copy the built tune to `Working/Weapons/riot/<leaf>.wtunec`, write the 8 members, read every one back | Q-1: a pedestrian and a car are hit; HP unchanged, target pushed — if HP drops the card is BROKEN and returns to `blocked` |
| R-2 | **the lethal ↔ riot toggle** | a second weapon entity cloning the cannon node | `B-15.md` step 3: author the riot variant entity, lethal copy untouched | the player can hold two distinct variants; binding needs a third slot, which does not exist (T-WP13) |
| R-3 | **gel VFX on the round** | `.effc`/particle attachment (no weapon member) | attach `Anti_firearm_gel_Miss`, `Batmobile_RiotSuppressor_Tracer`, `RiotSuppressor_BulletCasing` on the riot entity | a hit shows the gel splat, the tracer is not the chain gun's, and the casing particle is the riot one |
| R-4 | **the two riot sounds** | the shipped `weapons.bank` | map by rule if a copy exists in another bank; the two named events are absent from the grab | a bolt and an impact sound exist whose names are not the missing ones; otherwise the audio half is a named gap |
| R-5 | **stun/incapacitation on the target** | outside the decoded damage model (no `stun`/`ragdoll` member anywhere) | not a tune job; record the target-side response from the Q-1 take | the Q-1 take notes whether the pedestrian stands up, staggers or dies |

### 3.5 UNKNOWNs (settling file + pilot-card check)

| id | UNKNOWN | settling file | one-sentence pilot-card check |
|---|---|---|---|
| UR-1 | whether a 0-damage bullet still applies impulse and hit reactions | `E:/Modding/JustCause3/_grab/weapons/w603_mediumtank_mgun/w603_mediumtank_mgun.wtunec` + `gen_explosion_5m_nodamage.ftune` (the only shipped 0) | Q-1: fire the 0-damage copy at a pedestrian and a car; note HP and displacement |
| UR-2 | which autoaim member is the 7.5° cone | `JC3Grab/WEAPONS.md` §9 (three presets, 22 members, six contexts) | Q-1: aim 10° off a target 20 m away; snapping = the member is the cone |
| UR-3 | `RiotSuppressorRange`'s ship value (only the Joker serializes 8000) | `Research/BatmobileGrab/CLASS_DEFAULTS.md` (`Default__RBatmobileCannon`) | Q-1: fire at 70 m and 90 m; the range that still acquires is the default |
| UR-4 | the impulse clamp above 100 once factors are 1.0 | `JC3Grab/WEAPONS.md` §3 (bullet impulse min/max per id) | Q-1: compare the push of the 100-impulse riot round with a stock 60-impulse MG round |

---

## 4. Missile pods — `RBatmobileMissileLauncher` / `Batmobile_Missile_Launcher`

### 4.1 BmAK behaviour, with numbers (all **decoded**)

| quantity | member | value | note |
|---|---|---:|---|
| salvo size | `RBatmobileMissileLauncher.MaxTargets` @0x095C | **8** | Joker variant 16 |
| salvo cadence | `RBatmobileMissileLauncher.FireInterval` @0x098C | **0.5 s** | one missile per 0.5 s ⇒ 8 over 3.5 s |
| gadget cooldown | `RVehicleWeapon.WeaponCoolDown` @0x0830 | **20.0 s** | reuse gate |
| lock cone | `RBatmobileMissileLauncher.LockOnAngle` @0x0980 | **40.0°** | wide, barrage-style |
| lock range | `…LockOnRange` @0x0984 and `RVehicleWeapon.LethalRange` @0x0900 | **12000 = 120 m** | both agree |
| damage | `Projectile.Damage` (missile projectile) | **250.0** | |
| damage radius | `Projectile.DamageRadius` | **0.0** | no radial damage serialized |
| momentum | `Projectile.MomentumTransfer` | **25000.0** | |
| damage type | `Projectile.MyDamageType` | `Core.RDmgType_BatmobileMissileBarrage` | the Barrage's own type |
| projectile speed | — | **absent** (`Projectile.Speed`, `MaxSpeed`, `AccelRate` all absent) | the Barrage missile's speed is UNKNOWN |
| homing | — | **absent** on this projectile (`HomingDelay`/`ForceExplodeProxDist` absent on `Batmobile_Missile_Projectile`) | the pods' missile carries no homing fields at all |
| ammo / magazine | — | **no member** | the salvo size 8 is the only count |
| reload | — | **no member** | the 20 s cooldown is the replacement |
| launch sockets | `MissileLaunchSockets` | array of **2**, payload not decoded | mesh sockets `MissileL`/`MissileR` matched 0.000 cm in the build |
| target UI | `TargetSwitchName` `Ww_Batmobile_Target.Batmobile_Target`, `LastTargetSwitchName` `…_Last`, `MissileNumberParameter` `Ww_Parameters.BML_NumberOfTargets` | — | target cycling + an RTPC for the count |
| FX / audio | `FireFX` `Rocket.Batmobile_Rocket_Muzzle`, explosion `Rocket.Batmobil_Rocket_Explosion` (14 emitters), sweetener `Play_Tank_Explosion_Barrage_Sweetener`, lock beep/locked sounds on `w618`'s siblings | partial | `Play_Batmobile_ApRocket_Fire` is a **missing-object** |
| muzzle placement | both pod sockets are on the body, not a turret; `CannonMuzzle`/`ChainGunMuzzle` are elsewhere | — | the pods fire forward from two points |

### 4.2 Closest JC3 preset and entity — two tiers

**Tier 1 (what the build already has):** `editor/entities/jc_weapons/06_vehicle/w618_sportsmuscle_missile/`
— the **donor chassis's own missile**, still bound to `main_weapon` on
`v0300_car_kensington_sportsmuscle`, 4 fire points, `autoaim_vehicle_no_lockon_missile`, fire_rate 0.5,
velocity 360, range 300, damage 1500, blast 1100 in 8 m, turning speed **0** (no homing), magazine −1.
It is the ship's single unguided missile, not the Barrage.

**Tier 2 (the salvo carrier):** `editor/entities/jc_weapons/06_vehicle/w614_monorailmissilecar_missile/`
on `v5603_train_urga_monorailmissilecar` — the only vehicle weapon that is **both guided and binds the
lock-on preset** (`missile_turning_speed` **200**), fire_rate **0.25**, `burst_count` **6**,
`burst_cooldown` **5**, velocity 600, range 300, damage 1500, impulse 350, `missile_per_shot` 1,
`detonate_on_impact` 1 (`JC3Grab/WEAPONS.md` §2, §5; `T-WP3b`).

**Salvo alternatives, with their numbers:** `w613_fighterbomber_missile_ground_lockon` — burst 6,
burst_cd 4, magazine 6, blast 1500 in 25 m, but `CanTargetCharacters/Vehicles/RigidObjects` all **0**
(it acquires nothing); `w609_fighterjet_missile_air_lockon` — magazine **8** (the only 8 in the fleet),
burst_cd 1, turning 150, no blast. The closest to "8 targets, one salvo, guided" is therefore a
**w614 clone with `magazine_size` 8**, because w614 is the only guided salvo with a working lock preset.

| item | value |
|---|---|
| tune | `…/w614_monorailmissilecar_missile/w614_monorailmissilecar_missile.wtunec` (copy) |
| carrier entity | `v5603_train_urga_monorailmissilecar` (a **CTrain**, not a `CCar` — a precedent, not a slot) |
| slot (ship) | `main_weapon` is taken by the cannon; the second driver slot by the Vulcan; the pods need a third (T-WP13) |
| blast | `car_explosion_medium` (500 in 5 m) — the shared pulse nearest BmAK's `DamageRadius` 0 |
| lock preset | `autoaim_vehicle_lockon_missile` (the only lock-on preset in the fleet) |

### 4.3 Member-by-member mapping

| BmAK quantity (decoded) | JC3 member (decoded) | transform | class |
|---|---|---|---|
| `FireInterval` 0.5 s | `fire_rate` 0.25 (w614) → **0.5** | same unit | **decoded→direct** |
| `MaxTargets` 8 | `burst_count` 6 (w614) → **8**, `magazine_size` −1 → **8** | salvo count and clip; 8 is outside the observed burst band (max 6) | **derived**, declared switch |
| `WeaponCoolDown` 20 s | `burst_cooldown` 5 → **20** | between-salvo gate; 20 is outside the observed band (max 5) | **derived**, declared switch |
| `LockOnAngle` 40.0° | `AngleThresholdNewTarget`/`CurrentTarget` (observed 0–1.4) | unit unproven; 40 is 28× the fleet max | **UNKNOWN** |
| `LockOnRange` 12000 = 120 m | `MaxAimDistance` 70 → **120** (fleet band 0–750) | metres → metres | **derived** |
| `Projectile.Damage` 250 | `base_tuning.damage` 1500 + blast 500/5 m | no unit bridge; health row carries the ratio | **derived** (policy) |
| `DamageRadius` 0.0 | `car_explosion_medium` `PlayerDamageRadius` 5 → **1.5** (fleet min) | BmAK has no radius; 1.5 m approximates a direct hit | **derived** |
| `MomentumTransfer` 25000 | `base_tuning.impulse` 350 (missile band, fixed) | band is a single value per missile in the fleet; 350 is what all missiles ship | **decoded (fleet)** |
| projectile speed (absent) | `velocity` 600 kept | nothing to convert | **UNKNOWN** |
| homing (absent on this projectile) | `missile_turning_speed` 200 (w614) | closest carrier gives homing because the launcher locks; BmAK's pod missile has no homing fields | **derived** (borrowed) |
| `MissileLaunchSockets` (2, undecoded) | 2 `SWeaponPoint`s at `MissileL`/`MissileR` | matched 0.000 cm | **decoded** (positions), **UNKNOWN** (array order) |
| `TargetSwitchName` / `LastTargetSwitchName` | no member; the HUD lock POI (`POI_TYPE_LOCK_ON_TARGET` 21) is the only target marker | — | **UNKNOWN** |
| `MissileNumberParameter` (RTPC `BML_NumberOfTargets`) | no RTPC member in a tune | audio-side only | **UNKNOWN** |
| `RDmgType_BatmobileMissileBarrage` | damage is typed on the **part**, not the weapon (71 part types) | no type member to write | **decoded (fleet)**: absent |
| explosion `Batmobil_Rocket_Explosion` (14 emitters) | `car_explosion_medium` pulse + the missile's own impact `.effc` | asset-side | **derived** |

### 4.4 What is unmatched, and the build recipe that closes it

| # | unmatched | closest JC3 system | build recipe | closes when |
|---|---|---|---|---|
| P-1 | **8-target salvo** (no per-target member in any tune) | `burst_count` + `magazine_size` on the w614 clone | copy w614 to `…/w614_batmobile_missilepods/`, write `burst_count` **8**, `magazine_size` **8**, `fire_rate` **0.5** | Q-3 #3: one trigger press fires 8 missiles, 0.5 s apart, then the launcher is empty |
| P-2 | **20 s reuse gate** | `burst_cooldown` | write `burst_cooldown` **20** | a second salvo is refused for 20 s (Q-3 #3 timing) |
| P-3 | **40° lock cone** | `AutoAim` angles (lock-on preset) | write 40 into the three angle members and bind `autoaim_vehicle_lockon_missile` | Q-3 #3: a target 30° off the nose acquires; 45° off does not |
| P-4 | **120 m lock range** | `MaxAimDistance` | write **120** | Q-3 #3: acquisition at 110 m works, at 130 m does not |
| P-5 | **target switching** (two AkSwitch names) | HUD lock marker only | no tune member; the HUD take records what the marker does | Q-3 #3: the marker moves to a second target when the reticle does; if it does not, the switch is a named gap with the HUD as its carrier |
| P-6 | **homing on a pod missile with no homing fields** | `missile_turning_speed` 200 from w614 | borrow 200; note it is not BmAK's number | Q-3 #3: a missile fired 20° off tracks onto a moving car; record the miss distance |
| P-7 | **two launch points** | two `SWeaponPoint`s at `MissileL`/`MissileR` (already 0.000 cm) | keep B-05's points; the w614 clone's fire point list is replaced by these two | Q-3 #3: alternating missiles leave from the left and right pod, not the car centre |
| P-8 | **blast radius 0 → 1.5 m** | `car_explosion_medium` pulse | private pulse copy with `PlayerDamageRadius` **1.5**, `PlayerDamage` **500** | a missile hit damages the targeted vehicle panel, not a 5 m disc |

### 4.5 UNKNOWNs (settling file + pilot-card check)

| id | UNKNOWN | settling file | one-sentence pilot-card check |
|---|---|---|---|
| UP-1 | the Barrage missile's **speed** (absent from the projectile) | `Research/BatmobileGrab/CLASS_DEFAULTS.md` (`Default__RBatmobileMissile`) | Q-3 #3: fire at a car 100 m away and time the flight; 0.17 s = 600 m/s, 0.28 s = 360 m/s |
| UP-2 | whether the pods' missile homes at all (no homing fields on `Batmobile_Missile_Projectile`) | `Research/BatmobileGrab/MECHANICS.md` (weapon→projectile links) and `CLASS_DEFAULTS.md` | Q-3 #3: fire 20° off a moving car; if the missile flies straight, there is no homing and P-6 is a borrowed behaviour, not a translation |
| UP-3 | `MissileLaunchSockets`' two entries → which mesh socket each maps to | `Research/BatmobileGrab/SOCKETS_JC3.json` (65 sockets) and `WEAPONS.md` §12 (array undecoded) | Q-3 #3: fire once and see which pod emits; left vs right settles the pairing |
| UP-4 | the `AutoAim` angle unit at 40° | `JC3Grab/WEAPONS.md` §9 | Q-3 #3: aim 30° off a tank at 40 m; acquisition means degrees, no acquisition means the unit is smaller |
| UP-5 | whether `MaxTargets` 8 is a simultaneous lock count or a salvo length | `Working/vendor/BmAKgrab/scripts/` (the launcher's lock loop) | Q-3 #3: with 8 cars in the cone, count distinct missiles and distinct targets |

---

## 5. Cross-weapon facts (they apply to all four)

| fact | value | evidence |
|---|---|---|
| driver slots in the fleet | **2** (`main_weapon` + `id:00568A74`), no active-slot index, no next/previous action | `WEAPON_WIRING.md` §2b; `T-WP13` |
| slots already claimed by this build | cannon → `main_weapon`, Vulcan → `id:00568A74` | `Working/Weapons/manifest.json` |
| ammo in BmAK | **absent** from all four objects (no magazine/clip member in 67 + 41 + 16 fields) | `WEAPONS.md` §8, §11, §12 |
| ammo in JC3 | `magazine_size` −1 and `unlimited_ammo` 1 on every fleet weapon; `reload_time_scale` 0 or 1 | `JC3Grab/WEAPONS.md` §2 |
| heat in JC3 | **no member at all** (0 heat params in the HUD data too) | `JC3Grab/WEAPONS.md` §10; `JC3_HUD_WEAPONS.json` |
| damage type | not in a JC3 tune; typed on the **part** (71 types) | `JC3Grab/WEAPONS.md` §10; `PARTS_TABLE.md` |
| muzzle points | 5 of 9 built points name a BmAK socket and all 5 match at **0.000 cm**; 4 are template `attach.vehicle` markers | `tmp/freebuff/reports/weapon-points-vs-bmak.md` |
| fire-point yaw | JC3 `fire_position_0` is a world transform, so the pod points must be re-authored, not cloned | `WEAPON_WIRING.md:314` |

The slot fact is the single blocker shared by riot mode and the missile pods: both are **complete as
recipes** and both need a slot that does not exist (riot: a third variant beside the Vulcan; pods: a
third arm beside the cannon and the Vulcan). That is `T-WP13`, not a tune gap.

---

## 6. Build order these four need

1. **Cannon (in the tree):** apply C-2 (`PlayerDamageRadius` 1.5), C-7 (impulse 100 / factors 1.0), then
   C-6 (0.4 s reload cue on the entity). C-1 (charge) is the only new-entity item; C-4 waits on UC-2.
2. **Vulcan (in the tree):** apply V-1 (scatter 0.1 + per-shot 0.167), V-6 (impulse 100), then V-2
   (`GatlingGun` + `weapon_rpm` 240 on the barrel bone). V-3/V-4 record absence, not work.
3. **Riot mode:** `B-15.md` steps 1–4 (8 members in a private tune + the second entity + the three gel
   assets). Binding waits on a slot.
4. **Missile pods:** copy w614, apply P-1/P-2/P-3/P-4/P-6 (burst 8, cd 20, angles 40, range 120,
   turning 200), a private `car_explosion_medium` copy with radius 1.5, and B-05's two pod points.
   Binding waits on a slot.

Every step lands in a private copy under
`editor/entities/jc_weapons/06_vehicle/w6xx_batmobile_<name>/` — never in a shipped `w6xx` file (R7:
other vehicles use them).

---

## 7. UNKNOWN register (all UNKNOWNs above, in one place)

| id | weapon | UNKNOWN | settling file | pilot-card check (one sentence) |
|---|---|---|---|---|
| UC-1 | cannon | `MaxSpeed` 480 m/s behaviour | `Research/BatmobileGrab/CLASS_DEFAULTS.md` | Q-3 #3: time a 200 m and a 400 m shot; a late 400 m impact proves the cap |
| UC-2 | cannon | `TurretShotDamage` 75 = AI-paid or turret-only | `CLASS_DEFAULTS.md` (`Default__RBatmobileHeavyCannon`) | Q-3 #3: let an NPC gunner fire; more health lost than a player shot ⇒ separate side |
| UC-3 | cannon | what the 2.5 s charge gates | `BmGame.upk` defaults + `REGISTRATION.md` | Q-3 #3: tap vs hold; identical effect ⇒ cadence only |
| UC-4 | cannon | AutoAim angle unit at 15° | `JC3Grab/WEAPONS.md` §9 | Q-3 #3: aim 10° off; snapping ⇒ degrees |
| UC-5 | cannon | what `LethalRadius` 175 gates | `CLASS_DEFAULTS.md` + `HUD_SPEC.json` | Q-3 #3: acquire at 170 m but not 180 m ⇒ metres |
| UV-1 | Vulcan | projectile speed (no archetype) | `CLASS_DEFAULTS.md` (`Default__RBatmobileCannon`) | Q-3 #3: 100 m impact at 0.13 s ⇒ 750 m/s |
| UV-2 | Vulcan | `ChainGunDamage` 40 per round or per tick | `Working/vendor/BmAKgrab/scripts/` + `REGISTRATION.md` | Q-3 #3: 2 s burst vs health loss, 40 × hits |
| UV-3 | Vulcan | `weapon_rpm` unit | `JC3Grab/MOVING_PARTS.md:71` + `ANIMATIONS.md` | Q-3 #3: count revolutions in 1 s of video |
| UV-4 | Vulcan | `scatter_per_shot` honoured as bloom | `E:/Modding/JustCause3/_grab/weapons/w603_mediumtank_mgun/` | Q-3 #3: 18 rounds ⇒ ~3° group |
| UR-1 | riot | 0-damage bullet impulse/reaction | `w603` tune + `gen_explosion_5m_nodamage.ftune` | Q-1: pedestrian and car, HP + displacement |
| UR-2 | riot | which autoaim member is the 7.5° cone | `JC3Grab/WEAPONS.md` §9 | Q-1: aim 10° off at 20 m |
| UR-3 | riot | `RiotSuppressorRange` ship value | `CLASS_DEFAULTS.md` (`Default__RBatmobileCannon`) | Q-1: acquire at 70 m vs 90 m |
| UR-4 | riot | impulse clamp above 100 | `JC3Grab/WEAPONS.md` §3 | Q-1: push vs a stock 60-impulse round |
| UP-1 | pods | Barrage missile speed | `CLASS_DEFAULTS.md` (`Default__RBatmobileMissile`) | Q-3 #3: 100 m flight time |
| UP-2 | pods | does the pod missile home at all | `MECHANICS.md` + `CLASS_DEFAULTS.md` | Q-3 #3: fire 20° off a moving car |
| UP-3 | pods | socket array → left/right mesh socket | `SOCKETS_JC3.json` | Q-3 #3: one shot, which pod emits |
| UP-4 | pods | AutoAim angle unit at 40° | `JC3Grab/WEAPONS.md` §9 | Q-3 #3: 30° off at 40 m |
| UP-5 | pods | `MaxTargets` = simultaneous locks or salvo length | `Working/vendor/BmAKgrab/scripts/` | Q-3 #3: 8 cars in cone, count targets |

18 UNKNOWNs; none is written as an accepted limit, and each carries the file that would settle it plus
one Q-card sentence.

---

## 8. Checks actually run for this report

```
$ ls Research/BatmobileGrab/WEAPONS.md Research/JC3Grab/WEAPONS.md   (both present, read)
$ ls Builds/bm-RC2/aaf/editor/entities/jc_weapons/06_vehicle
w602_batmobile_cannon  w603_batmobile_vulcan
$ python - <<'PY'  (Working/Weapons/manifest.json rows)
T-WP1 w602_mediumtank_canon …w602_batmobile_cannon.wtunec 2 edits
T-WP2 w603_mediumtank_mgun  …w603_batmobile_vulcan.wtunec 1 edit
T-WP3 w618_sportsmuscle_missile None 0
T-WP4 w618_sportsmuscle_missile None 0
```

Read-only: no build, tune, `.ee`, `.toc`, install, tracker row or game file was modified.

## 9. Evidence index

- `Research/BatmobileGrab/WEAPONS.md` §8 (`RBatmobileCannon`: 67 fields incl. riot group), §11
  (`RBatmobileHeavyCannon`: 41 fields + projectile 18), §12 (`RBatmobileMissileLauncher`: 16 fields),
  §4 (per-projectile speed/damage/radius/momentum), §5 (the card's quantity index).
- `Research/BatmobileGrab/FOOTAGE.md` §2–§4 (`HeatUpPerSecond` 0, the spread curve, what the files do
  answer), `Research/BatmobileGrab/CLASS_DEFAULTS.md` (the settling file for class defaults).
- `Research/JC3Grab/WEAPONS.md` §2 (fire rate/magazine/range/velocity), §3 (damage/impulse/factors),
  §4 (scatter/recoil), §5 (missile homing/accel), §6 (bullet tracer/ttl), §8 (`ForcePulseSettings`),
  §9 (`AutoAim`), §10 (what the card asked for, and the absences: damage type, heat, lock time).
- `Research/JC3Grab/WEAPON_WIRING.md` (slots 305, fire points 314, part behaviours 52, 2-slot limit)
  and `WEAPON_WIRING.jsonl` (the tank's two slot objects).
- `Working/Weapons/manifest.json` (B-06: the two private tunes and their read-back), `Research/specs/B-06.md`
  (BL-4: w602/w603 are tune-only copies), `Research/specs/B-15.md` (riot recipe).
- `Working/Translation/T7_WEAPONS.md` §3 (rows T-WP1…T-WP3) and `tmp/freebuff/reports/`
  `non-lethal-cannon-carrier.md`, `T-WP3b.md`, `T-WP4c.md`, `weapon-points-vs-bmak.md`.
