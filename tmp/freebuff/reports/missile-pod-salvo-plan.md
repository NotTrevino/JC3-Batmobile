# Missile pod salvo — BmAK timing, launch spread, trail; JC3 interval and spread members

**Status: research note.** Read from local records only (AGENTS.md). Two of the three requested
BmAK numbers are in the files; the third (smoke-trail **length**) is **UNKNOWN**, because the trail
system the stock missile names does not resolve and no file carries the missile's speed.

Sources: `Research/BatmobileGrab/WEAPONS.md` (§12 `RBatmobileMissileLauncher`, §13 Joker launcher,
§4 `Batmobile_Missile_Projectile`, §10 `RBatmobileEMPMissile`, §15 tracker),
`Research/BatmobileGrab/ANIMATIONS.md` (missile-bay sequences), `Research/BatmobileGrab/PARTICLES_FEATURES.md`
(missile/trail systems), `Research/JC3Grab/WEAPONS.md` (§2 cadence, §4 recoil/scatter, §missile tuning
vocabulary), `Research/JC3Grab/SIGNATURE_DIFF.md` (four-tube pod wiring).

---

## 1. BmAK: is there even a "pod"?

The pod is the **missile bay mechanism**, not a separate weapon. The car has six missile-bay bones —
`Batmobile_Rig_Weapons_Missiles_L_T / L_Mid / L_B / R_T / R_Mid / R_B` — and two sequences open and
close them:

| sequence | frames | length | tracks | mechanism | what moves |
|---|---:|---:|---:|---|---|
| `Batmobile_V2_Missles_Up` | 26 | **0.833 s** | 7 | `missile bays` | L_B/L_T/R_B/R_T rotate **14.99°**; `L_Mid` translates **10.87 cm** |
| `Batmobile_V2_Missles_Down` | 26 | 0.833 s | 27 | `missile bays` | same values, opposite travel |

(Identical in all four packages, `ANIMATIONS.md` §mechanism table.) So a salvo has a **0.833 s bay-open
pose** before/around firing — that is the closest authored "pod opens" timing, and it is *not* the
missile-to-missile delay.

The real cadence numbers, `RBatmobileMissileLauncher` (`WEAPONS.md` §12, all 16 fields identical in
Batmobile/MK2/Funhouse):

| field | value | meaning |
|---|---:|---|
| `RBatmobileMissileLauncher.FireInterval` | **0.5 s** | delay between missiles in a salvo |
| `RBatmobileMissileLauncher.MaxTargets` | **8** | targets per barrage (Joker launcher: **16**) |
| `RVehicleWeapon.WeaponCoolDown` | **20.0 s** | salvo reload |
| `RBatmobileMissileLauncher.LockOnAngle` | 40.0 (deg) | lock cone |
| `RBatmobileMissileLauncher.LockOnRange` / `LethalRange` | 12000.0 / 12000.0 | range (cm) |
| `MissileNumberParameter` | `Ww_Parameters.BML_NumberOfTargets` | the count the audio receives |
| `FireFX` | `Rocket.Batmobile_Rocket_Muzzle` | launch flash |

### 1.1 Launch angle spread — measured, but as a **rotator**, not a per-missile cone

`RPursuitModeMissileLauncher` (the pursuit-mode launcher) is the only class in the grab that authors a
launch angle at all:

| field | raw value | decoded |
|---|---|---|
| `LaunchRotationOffset` | `[-3640, 0, 0]` (Rotator) | **−20.0° pitch** (65536 units = 360°) |
| `LaunchSocketName` | `"BattleModeSpotLight"` | the launch socket is the battle-mode light socket |
| `bInstantFire` | `true` | fires immediately on trigger |
| `ProjectileArchetype` | `Batmobile_EMPMissile_Projectile_ForCars` | the pursuit-mode missile |

**What is NOT there:** a per-missile cone, a jitter angle, or a "spread" field on either launcher class.
`RBatmobileMissileLauncher` has no angle member besides `LockOnAngle` 40.0. So BmAK's salvo spread is
**one fixed −20° pitch offset applied to the launch**, not a fan. Any fan we want is our addition, and
this note says so rather than inventing a "BmAK 4° cone".

### 1.2 Missile-to-missile timing, cross-checked against the projectile

| quantity | value | source |
|---|---:|---|
| `Projectile.Damage` | 250.0 | `WEAPONS.md` §4 |
| `Projectile.MomentumTransfer` | 25000.0 | ″ |
| `Projectile.DamageRadius` | 0.0 | ″ (no splash) |
| damage type | `Core.RDmgType_BatmobileMissileBarrage` | ″ |
| speed / max speed / acceleration / homing delay / lifetime | **absent from every instance** | ″ |
| one undecoded float at `0x016C` | 0.6685995 | ″ |

Speed and lifetime absent means flight time and **trail length cannot be computed** even if the trail
lifetime is known.

### 1.3 Smoke trail length

The stock missile names its trail twice (`RBasicProjectile.ProjectileTrail` and `RBatmobileMissile.Trail`)
and both resolve to `Projectiles.Batmobile_Missile_Projectile.RocketTrail`, whose system
**`Engine.Batmobile_Rocket_Trail` is `missing-object`** in the grab. So:

| asked | value | class |
|---|---|---|
| trail system | `Engine.Batmobile_Rocket_Trail` (unresolved) | measured name, missing asset |
| **trail length** | **UNKNOWN** | needs the particle system *and* the missile speed |
| nearest measured trail | `Batmobile_JokersRocket_Trail` — 4 emitters, ribbon lifetime **0.06–3 s**, size `[5,0,0]`–`[80,25,15]`, rate 1–8/s | measured (Joker only) |
| cannon trail for comparison | `Batmobile_CanonTrail` — 2 emitters (ribbon×1, sprite×1), lifetime **0.035–1.25 s** | measured |

A 3 s ribbon at a few hundred m/s is a kilometre-long trail; without the speed number, quoting a
length would be fabrication. The honest plan is: copy the Joker trail's lifetime/size, then measure the
visible length once in game.

---

## 2. JC3: which members set interval and spread

JC3 splits a salvo across **two layers**:

**(a) Cadence — top-level `WeaponTuning` (one value per weapon id, not per missile block):**

| member | type | fleet range | role |
|---|---|---:|---|
| `fire_rate` | float | 0.1 – 1.75 (s) | delay between shots |
| `burst_count` | uint8 | 1 – 6 | shots in one burst before `burst_cooldown` |
| `burst_cooldown` | float | 0 – 5 (s) | pause after the burst |
| `fully_automatic` | uint8 | 0 – 1 | hold to keep firing |

**(b) Misile behaviour + spread — `missile_weapon[0].tuning.*`:**

| member | type | fleet range | role |
|---|---|---:|---|
| `missile_base_tuning.missile_per_shot` | uint8 | 1 – 1 | missiles launched per trigger pull |
| `missile_base_tuning.missile_acceleration[]` | float | 0 – 300 | accel ramp |
| `missile_base_tuning.missile_turning_speed` | float | 0 – 300 | homing turn rate |
| `missile_base_tuning.missile_no_turning_time` | float | 0 – 0 | delay before homing |
| `base_tuning.scatter.scatter_minimum` / `scatter_maximum` | float | **0 – 0** | spread floor / ceiling |
| `base_tuning.scatter.scatter_per_shot` | float | **0 – 0** | spread added per missile |
| `base_tuning.scatter.scatter_recover_rate` / `scatter_reset_time` | float | 0 – 0 / 2 | recovery |
| `base_tuning.scatter.scatter_clamp_horizontal[]` / `_vertical[]` | float | −1 – 1 | clamps |
| `base_tuning.recoil.*` | float | pitch/yaw [0,0], recover 0.75 / 2 s | camera kick |

**Shipped reality:** every missile in the fleet has `scatter_minimum = scatter_maximum =
scatter_per_shot = 0` — JC3's missiles do **not** fan out from the tuning block. The fan comes from
**multiple muzzles**: the sportsmuscle missile pod is one `CMissileWeaponBase` (`w618_sportsmuscle_missile`)
with **four** type-2 `internal.fire_point.N` points and **four** `SAttachedEffect` muzzle flashes, one
per tube (`SIGNATURE_DIFF.md` §534). Units of `scatter.*` are **UNKNOWN** (nothing in the decoded rows
states degrees or mils).

---

## 3. What we use

Target: the Batmobile's missile pod clone, built from `w618_sportsmuscle_missile` (missile block, four
fire points already wired) — the closest stock multi-tube vehicle launcher.

| # | JC3 member / object | value | source of number | class |
|---|---|---|---:|---|
| 1 | `fire_rate` | **0.5 s** | BmAK `RBatmobileMissileLauncher.FireInterval` | measured |
| 2 | `burst_count` | **6** | matches BmAK's six bay bones; stays inside the fleet max of 6 | BmAK bones measured, count chosen |
| 3 | `burst_cooldown` | **20.0 s** | BmAK `RVehicleWeapon.WeaponCoolDown` — **outside** the fleet's 0–5 s range, so flag it as a deliberate outlier | BmAK measured |
| 4 | `missile_base_tuning.missile_per_shot` | **1** per fire point | fleet ships 1 | JC3 stock |
| 5 | `scatter_minimum` / `scatter_maximum` / `scatter_per_shot` | **0 / 0 / 0** | JC3 stock; BmAK has no cone to copy | both measured |
| 6 | `scatter_reset_time` | **2.0** | JC3 stock | JC3 stock |
| 7 | launch pitch offset | **−20.0°** on the fire-point matrix | BmAK `LaunchRotationOffset` = −3640 rotator units | BmAK measured; **the angle is measured, applying it per fire point is our choice** |
| 8 | fire points | **4** to start (w618 ships 4); 6 to match the bays | w618 wiring | JC3 measured / BmAK bones |
| 9 | `missile_acceleration[]` | **300** (fleet max) | closest to a fast launch; BmAK has no accel value | JC3 stock value, choice |
| 10 | `missile_turning_speed` | **300** (fleet max) | ditto | JC3 stock value, choice |
| 11 | `missile_no_turning_time` | **0** | fleet ships 0 | JC3 stock |
| 12 | trail | copy `Batmobile_JokersRocket_Trail` lifetime **0.06–3 s**, size `[5,0,0]`–`[80,25,15]` | measured | BmAK measured (Joker) |
| 13 | salvo targets | **8** (Joker: 16) | BmAK `MaxTargets` | BmAK measured |
| 14 | reload | **20 s** | BmAK `WeaponCoolDown` | BmAK measured |

**Not set:** a missile smoke-trail *length* in metres, and any numeric spread cone. Both would be
invented; JC3's own missiles ship zero scatter and BmAK's trail asset is missing.

### Values still missing (each a short experiment, not an implementation)

1. Missile speed — absent on both sides (BmAK `Projectile.Speed` absent; JC3 has no speed member in the
   missile tuning, only acceleration/turning). Needed before any trail length is quoted.
2. `Engine.Batmobile_Rocket_Trail` — pull the system from the package (the object is `missing-object` in
   the current grab) and read ribbon lifetime × speed.
3. Whether `burst_count` > 4 with only 4 fire points cycles the muzzles or refuses to fire — one test.

## 4. Conflicts and quirks recorded

* **Eight targets, six bays, four tubes.** BmAK `MaxTargets` = 8, missile-bay bones = 6, and the JC3
  donor pod has 4 fire points. Any "8-missile salvo" claim has to pick which of those it means.
* **The pursuit launcher's socket is a light socket** (`LaunchSocketName = "BattleModeSpotLight"`), and
  `LIGHTS.md` resolves that name to `Batmobile_Rig_Weapons_Drone_Decoder`. Missiles firing from a
  spotlight socket is shipped behaviour, not a decode error.
* **Joker launcher doubles the salvo** (`MaxTargets` 16) and has `NumFakeTargetReps`; its `MaxTargetsPerLevel`
  array is 4 items vs 1 on the other launcher (`WEAPONS.md` §13).
* **Fleet-wide `burst_cooldown` never exceeds 5 s**, so our 20 s value is an intentional departure —
  worth stating in the build log, not silently shipping.

## 5. Checks run for this note

* Re-read `RBatmobileMissileLauncher` field table (§12) and the Joker launcher (§13) for FireInterval,
  MaxTargets, WeaponCoolDown.
* Re-read `Batmobile_Missile_Projectile` (§4) for damage/momentum and the absent speed/trail fields.
* Re-read JC3 `WEAPONS.md` missile-tuning vocabulary rows and the top-level `fire_rate` / `burst_*` rows.
* Re-read `SIGNATURE_DIFF.md` §534 for the four-tube pod wiring, and `PARTICLES_FEATURES.md` for the
  Joker rocket trail numbers.
* No game process started; `Research/` was read only.
