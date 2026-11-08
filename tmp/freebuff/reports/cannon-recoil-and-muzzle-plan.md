# Cannon recoil, muzzle flash and shell ejection — BmAK numbers vs JC3 members

**Status: research note.** Read from the project's own records only (AGENTS.md); every value has a
file behind it. Two of the four requested BmAK numbers are **not in the files** — those rows say
**UNKNOWN** and name the probe that would settle them, instead of a plausible-looking number.

Sources: `Research/BatmobileGrab/WEAPONS.md` (§8 `RBatmobileCannon`, `RBatmobileHeavyCannon`),
`Research/BatmobileGrab/PARTICLES.md` + `PARTICLES_FEATURES.md` (muzzle-flash and casing systems),
`Research/BatmobileGrab/ANIMATIONS.md` (cannon sequences), `Research/BatmobileGrab/MECHANICS.md`
(casing sockets), `Research/JC3Grab/WEAPONS.md` (§2 fire rate, §4 recoil), `Research/JC3Grab/FX13_CASINGS.md`
(casing attachment, effc numbers), `Research/JC3Grab/TURRET.md` (pivot + fire point),
`Research/JC3Grab/LIGHTS_FORENSICS.md` (Fire-usage muzzle flash attachments).

---

## 1. What BmAK actually ships

BmAK has **two** cannon classes, and they are not the same weapon:

| | `RBatmobileCannon` (chain gun / riot suppressor) | `RBatmobileHeavyCannon` (the shell cannon) |
|---|---|---|
| fire FX | `GunFX` = `Particles.Batmobile_Muzzleflash_NoTracer` (`WEAPONS.md` off 0x0978) | `FireFX` = `Particles.Batmobile_canonMuzzleflash` (0x097C) |
| recoil | `RecoilImpulse` = **400.0** float (0x0A6C) | `RecoilImpulse` = **15000.0** (0x099C) on Batmobile/MK2/Funhouse; **150000.0** on Joker |
| impact | `ImpactMomentum` = **60000.0** (0x0A68) | — |
| spread | `InaccuracyAngle` = **0.1** (0x0A70) | `LockOnAngle` 15.0, `LockOnTimeMin/Max` 0.5 / 6.0 |
| casing | `ChainGunLoopingShells` = `Particles.ChainGun_BulletCasing`; `RiotSuppressorShell` = `Particles.RiotSuppressor_BulletCasing` | **none found** — no casing particle member on the class |

All 67 fields of `Batmobile_Cannon_V2` are identical in its 4 instances (268 comparisons, 0
differences, `WEAPONS.md` §8) — so 400.0 is the shipped chain-gun value everywhere, and the heavy
cannon's only per-car difference is the Joker's 10× impulse.

### 1.1 Recoil distance and recoil time

| asked | value | class | evidence |
|---|---|---|---|
| **recoil distance** | **UNKNOWN** | — | no distance/length/offset member exists on either cannon class; the only recoil member is `RecoilImpulse` (a float impulse, not a translation). The fire animation's per-bone translation deltas are not in the decoded animation tables, which carry frame count, length, rate and track *names* only. |
| **recoil impulse** | 400.0 (cannon) / 15000.0 / 150000.0 (heavy, Joker) | measured | `WEAPONS.md` §8 |
| **recoil time** | **0.700 s** as the authored fire-pose cycle | measured length, role inferred | `Batmobile_V2_Cannon_Fire`: 22 frames, 0.700 s, 30 fps, 74 tracks, notifies 0 (`ANIMATIONS.md`). Whether this is the recoil *recovery* time or just the pose length is **UNKNOWN**. |
| reload cycle | 0.467 s | measured | `Batmobile_V2_Cannon_Reload_Left` 15 frames / `_Right` 15 frames, 30 fps |

The honest reading: BmAK recoil is **an impulse handed to physics**, so its "distance" is whatever
`RecoilImpulse` does to the car's mass at runtime — not a number the files carry. To get the distance
we would have to watch the barrel bone across the 0.700 s sequence (one 5-minute session), not invent it.

### 1.2 Muzzle flash size

`Batmobile_canonMuzzleflash` (heavy cannon `FireFX`) — `PARTICLES.md` serialised vectors and
`PARTICLES_FEATURES.md` muzzle-flash table:

| property | value | evidence |
|---|---|---|
| emitters | 4 (light×1, sprite×3) | `PARTICLES_FEATURES.md` |
| lifetime | 0.05 … 1.0 s (`0.12-0.15`, `0.15`, `0.4-1`, `0.05-0.15`) | `PARTICLES.md` |
| spawn | requested 20 /s | ″ |
| **size range** | `[0.5, 0, 0]` … `[400, 5, 0]` (cm, unscaled) | `PARTICLES_FEATURES.md`, `PARTICLES.md` emitter 4635/4637/4638 |
| flash colour | start `[1.0, 0.425, 0.15]` and `[8.0, 5.0, 0.3]`; core `[0.5, 0.5, 0.5]` | ″ |
| materials | `Engine.Fire_01_4x4_m`, `Engine.GPU_spark_M` | ″ |
| brightest sprite | 400 cm (4 m) | emitter 4638 `start_size [400,400,400]` |

Night-vision variant `Batmobile_canonMuzzleflash_NV`: 5 emitters, size up to `[400, 25, 25]`.

The chain gun's flash is `Batmobile_Muzzleflash_NoTracer`: 9 emitters (light×1, mesh×3, sprite×3),
lifetime 0.05–1.1 s, rate req 20, **size not resolved** (`-` in `PARTICLES_FEATURES.md`) — so for a
*size* to copy, use the heavy cannon's 400 cm.

### 1.3 Shell ejection

BmAK splits this into two completely different things:

**(a) Spent casings — chain gun and riot suppressor only.**

| casing | system | particles | socket (measured) |
|---|---|---|---|
| 9 mm brass | `Particles.ChainGun_BulletCasing` | 1 mesh emitter, lifetime 1 s, rate **4 /s**, material `Engine.Bullet_9mm_Mat` | `ChainGunShells` on `Batmobile_Rig_Weapons_Machine_Gun_01` at **(0.00, 16.59, -0.00) cm** |
| riot-suppressor gel shell | `Particles.RiotSuppressor_BulletCasing` | 6 emitters (mesh×1, sprite×4), lifetime 0.05–1.1 s, rate 0–30 /s, sizes up to 80 | `RiotSuppressorShells` on `Batmobile_Rig_Weapons_Riot_Sup_Main` at **(0.00, 3.49, -9.29) cm** |

Sockets from `MECHANICS.md` (identical in all four packages). Casing mesh size itself is **UNKNOWN**
(mesh-particle size unresolved).

**(b) Cannon shells — geometry, not ejected.** `Batmobile_R_Shell_001…009`, `Batmobile_R_Shell_Chamber`,
`Batmobile_R_Shell_Tween_001…006` (and the `L_` set) exist as bones and are animated only by
`Cannon_Reload_Left/Right` (15 frames, 0.467 s). That is a **shell rack feeding the chamber**, not brass
leaving the car. No heavy-cannon casing particle and no eject socket were found, so "heavy cannon ejects
a spent shell" is **UNKNOWN / not shipped** as far as these files go.

---

## 2. The JC3 members these map onto

| BmAK thing | JC3 carrier | member / object | value on a stock vehicle gun |
|---|---|---|---|
| recoil impulse | `WeaponTuning` | `bullet_weapon[0].tuning.base_tuning.recoil.recoil_pitch[]` | `w602_mediumtank_canon`: **[0, 0]** (player), **[0.1, 0.1]** (AI) |
| ″ | ″ | `…recoil.recoil_yaw[]` | **[0, 0]** both sides |
| ″ | ″ | `…recoil.recoil_first_shot_multiplier` | 1 |
| ″ | ″ | `…recoil.recoil_recover_percentage` / `_recover_reset_time` / `_recover_speed` | 0.4 / 1.15 / — (player), 1 / 1 / — (AI) |
| ″ | ″ | `…recoil.recoil_precision_aim_multiplier` | 1 |
| recoil *time* | same block | `recoil_recover_reset_time` | **1.15** (player), 1 (AI) — seconds, the closest authored "recoil settles in" value |
| fire cadence | `WeaponTuning` | `fire_rate` | `w602` = **1.75 s**, `w605_smalltank_canon` = 0.75 s |
| muzzle flash | entity graph, **not** a tune member | `SAttachedEffect`, `Usage` = `Fire` (hash 4131019937) | e.g. `effects/jc_weapons/muzzle_flash/rico_50cal_muzzleflash.effc` — 21 vehicle carriers (`LIGHTS_FORENSICS.md`); the sportsmuscle missile pod ships 4 of them, one per tube |
| muzzle position | entity graph | type-2 `internal.fire_point.N` + `SWeaponPoint FirePosition` | `w602` on the medium tank: fire point local **(0, 0.3739, -5.8174)**, pitch hinge −5…+20°, yaw −179…+179°, pivot 0.25 m above the ring (`TURRET.md`) |
| shell ejection | entity graph | `SAttachedEffect` named `ShellEjection`, `Usage` = `Fire`, parented to the weapon entity, **no `world` offset** | `effects/jc_weapons/50_cal/bullet_eject_capstone.effc` (7,423 B, 329 rows, MaxParticles [15, 30], gravity **−9.82**, cone half-angles **10° / 5°**, casing model **0.0163 × 0.0163 × 0.074 m**, rate = the weapon's `fire_rate`) — `FX13_CASINGS.md` §4.3 |

Two facts that decide the implementation:

1. **A vehicle weapon in JC3 has no effect members at all.** `FX13_CASINGS.md` measured 444 decoded
   `WeaponTuning` member paths over 25 weapon ids: **0** contain effect/particle/spawn/prefab names, and
   **0** contain casing/shell/eject/brass. Muzzle flash and casings are `.effc` objects attached in the
   weapon entity's graph, triggered by the `Fire` usage — there is no tune field to hold BmAK's
   `GunFX`/`FireFX` pointers.
2. **JC3's tank cannon ships zero recoil.** `w602` player `recoil_pitch` and `recoil_yaw` are `[0, 0]`,
   so the recoil the player sees in JC3 is camera/vehicle physics, not this block. BmAK's `RecoilImpulse`
   has no JC3 field that applies force to the shooter — the closest existing quantities are the
   hit-side `impulse` in `bullet_base_tuning`, which pushes the *target*.

---

## 3. What we set

Target: our private cannon on the Batmobile clone, cloned from `w602_mediumtank_canon` (one bullet
block, one muzzle).

| # | setting | value | why this value | source of number |
|---|---|---|---:|---|
| 1 | `fire_rate` | **0.70 s** | matches BmAK's cannon fire-pose cycle (0.700 s) | BmAK measured |
| 2 | `recoil_pitch[]` | **[0, 0]** | keep JC3 behaviour: the tune block does no kick; BmAK's recoil is impulse, not camera | JC3 stock + BmAK has no camera recoil member |
| 3 | `recoil_yaw[]` | **[0, 0]** | same | ″ |
| 4 | `recoil_recover_reset_time` | **1.15** | stock tank value; **guess** for feel, not a BmAK number | JC3 stock |
| 5 | `recoil_first_shot_multiplier` | **1** | stock | JC3 stock |
| 6 | muzzle flash | `SAttachedEffect` + `Usage Fire`, one per muzzle | BmAK's flash is a `FireFX` pointer, so the JC3 equivalent is an attached effect | mechanism measured in JC3 |
| 7 | flash size to author in the `.effc` | sprite up to **400 cm**, lifetime **0.05–1.0 s**, colour `1.0 / 0.425 / 0.15` | copies `Batmobile_canonMuzzleflash` | BmAK measured |
| 8 | shell ejection | `SAttachedEffect ShellEjection` → `bullet_eject_capstone.effc` on the weapon entity | this is the shipped JC3 mechanism; BmAK's heavy cannon has no casing to copy | mechanism measured in JC3 |
| 9 | casing size | **0.0163 × 0.0163 × 0.074 m** (shipped model), gravity −9.82, cone 10°/5°, cap 15/30 | shipped `.effc` values; no BmAK heavy-cannon casing exists to match | JC3 measured |
| 10 | muzzle point | one `fire_point_0` at the barrel tip | BmAK barrel bones are `Batmobile_Rig_Weapons_Heavy_Cannon_Barrel_01` / `…Barrrel_02` (sic) | BmAK bone names measured |
| 11 | recoil travel (barrel punch) | **not set** | BmAK distance UNKNOWN, JC3 has no shooter-force member — this is a new mechanism, not a value | — |

**Deliberately not set:** a "recoil distance" and a "recoil time" for the vehicle. Both would be
invented. The 0.700 s above is the fire pose, used as the cadence, not as proof of a recoil spring.

### Values still missing (each a 5-minute experiment, not an implementation)

1. Barrel-bone travel across `Batmobile_V2_Cannon_Fire` → the muzzle's actual rearward distance.
2. Which JC3 field (if any) can apply a rearward force to the shooter vehicle — candidate probe: an
   impulse on the vehicle's Havok body at the muzzle, since no tuning member does it.
3. Whether the heavy cannon's shell rack is visual-only — read `Cannon_Reload_*` keys for
   `R_Shell_001…009` to confirm the shells only move chamber-ward.

## 4. Corrections and conflicts recorded

* `WEAPONS.md` lists `Batmobile_Muzzleflash_NoTracer` as the **chain gun** FX and
  `Batmobile_canonMuzzleflash` as the **heavy cannon** FX; the two are not interchangeable and their
  sizes differ (chain-gun size unresolved, heavy cannon 400 cm).
* `Batmobile_Heavy_Cannon_*` **projectile** archetypes carry their own `MuzzleFlashOverride`
  (`Muzzle_Body_UPGR`, `Muzzle_Full_UPGR`, `Muzzle_Head_UPGR`) — so the upgraded heavy cannon fires a
  *different* flash than `FireFX`. Pick `FireFX` for the stock cannon, the `Muzzle_*_UPGR` systems for the
  upgraded one.
* BmAK's Joker heavy cannon has `RecoilImpulse` 150000.0, exactly 10× the other three packages — a real
  per-package difference, not a decode slip (`WEAPONS.md` §8 table).

## 5. Checks run for this note

* Re-read the `RBatmobileCannon` field table (`WEAPONS.md` §8) and the `RBatmobileHeavyCannon` tables
  (0x099C rows) for the recoil values.
* Re-read `PARTICLES_FEATURES.md` muzzle-flash and casings tables plus `PARTICLES.md` serialised
  `start_size` blocks for the flash and casing numbers.
* Re-read JC3 `WEAPONS.md` §2/§4 for `w602` fire rate and recoil rows, and `FX13_CASINGS.md` §4 for the
  attachment and `.effc` values.
* No game process started; only `Research/` read and `tmp/freebuff/reports/` written.
