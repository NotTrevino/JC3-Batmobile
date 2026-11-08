# Summon and the four unranked weapons — plans v2

Supersedes the contested rows of `tmp/freebuff/reports/unranked-weapons-closest-system.md` (W) and
`tmp/freebuff/reports/summon-drive-in-closest-system.md` (S). Audit:
`tmp/freebuff/reports/audit-summon-and-unranked-weapon-plans.md` (A). Folded in:
`vulcan-capture-fire-and-overheat-timing.md`, `cannon-60mm-reload-circle-plan.md`,
`cannon-recoil-and-muzzle-plan.md`, `vulcan-spinup-and-heat-plan.md`, `missile-pod-salvo-plan.md`,
`summon-and-arrival-plan.md`.

**No ranking.** `OPERATOR_PRIORITIES.md` ranks five weapons (tracker+EMP missile, booster mesh, EMP burst,
hacker, sonar) and says the cannon, Vulcan, riot mode and missile pods "are not ranked here: they are not
below sonar by default; ask the operator before ranking them". §7 records **build-order dependencies
only**.

**File facts checked at their source this pass, not taken from the audit:**

| # | item | value | line |
|---|---|---|---:|
| 1 | cannon `fire_position_0` | **(0, 0.3739, −5.8174)** | `Research/JC3Grab/WEAPON_WIRING.md:315` |
| 2 | Vulcan/mgun `fire_position_0` | (0.247, 0.485, −2.018) — **this is `w603_mediumtank_mgun`'s point** | `:314` |
| 3 | part behaviours | `mediumtank_turret` (Turret, 26 ← body), `mediumtank_cannon` (Cannon, 38 ← turret) | **`:329`** (also `:359`, `:389`) |
| 4 | tank slots | `main_weapon` w602 · `secondary (id:00568A74)` w603 · mounted `-` | `:305` |
| 5 | `.bts` in the index | **0** | `grep -c '\.bts"' Research/JC3Grab/INDEX.jsonl` |

**Two places the audit itself is wrong, and v2 corrects it:**

1. **W4 is not UNSUPPORTED.** A cited "no such statement appears in the file (grep for `index 38` = 0)" —
   but the statement is there verbatim at **`WEAPON_WIRING.md:329`**: "`mediumtank_turret` (Turret, 26 ←
   `mediumtank_body`), `mediumtank_cannon` (Cannon, 38 ← `mediumtank_turret`)". The v1 citation (`:52`) was
   wrong; the claim is **decoded**.
2. **The brief's and audit's line for the cannon point is off by one.** `grep -n "0.3739"` returns **`:315`**
   (six copies across the tank/APC sections: 315, 345, 375, 405, 435, 465, plus `:1908`). The mgun row is
   `:314`. The number the brief gives is right; the line number to cite is **315**.

**The muzzle correction the brief asks for, stated once:** the cannon's own point is
**(0, 0.3739, −5.8174)** — 5.82 m behind and 0.37 m above the hull origin, on the barrel axis — not
(0.247, 0.485, −2.018), which belongs to the coaxial machine gun. Anything in W §1.2 that derives the
"0.000 cm match" from the mgun row has to be re-derived against :315; the built Batmobile muzzle
(0.000339, 1.702497, −0.455945) is a **BmAK socket** match (`weapon-points-vs-bmak.md`), not a JC3
`fire_position_0` match, so the cannon's JC3 point must be **authored**, not cloned.

---

## 0. Audit rows, restated with the corrected source

| # | v1 claim | audit | **v2 corrected** | source |
|---|---|---|---|---|
| A1 | missile pods had `"private": null`, no carrier | MISMATCH | **four recipes registered, two on disk**: manifest rows exist for cannon (`w602_batmobile_cannon.wtunec`), Vulcan (`w603_batmobile_vulcan.wtunec`), missile (component `w618_sportsmuscle_missile`) and riot (points at `apply-riot-mode-rows.md` §4); `Builds/bm-RC2/.../06_vehicle` holds **only** the cannon and Vulcan directories | `Working/Weapons/manifest.json:25-30,111-116,157-159`; W §8 `ls` |
| A2 | riot had no private tune / no card | MISMATCH | same as A1: a recipe row and `Research/specs/B-15.md` exist; **no `riot_batmobile_suppressor` directory on disk** | `manifest.json:19`; W §8 |
| A3 | cannon muzzle (0.247, 0.485, −2.018) | OVERSTATED | **(0, 0.3739, −5.8174)** at `:315`; the mgun owns the other point (`:314`) | `WEAPON_WIRING.md:314-315` |
| A4 | `GatlingGun` on `v0604_car_urga_buggy` is "the only CCar with a GatlingGun part" | OVERSTATED | **unproven on a car**: the cited row marks it `unproven-on-CCar` and lists it under "Unproven on a car (30)"; W's own V-2 says 0 of 24 cars. Donor candidate only | `MOVING_PARTS.md:127,170` (audit) |
| A5 | `civilian_std.bts` pairing is a `TRAFFIC.md` fact | OVERSTATED | the mechanism and the rule name are `TRAFFIC.md:105,111`; the **tree string itself is from the probe** `tmp/freebuff/probe/global.blo` | `TRAFFIC.md:105,111` |
| A6 | `Limit_Speed` fleet table 22/30/2/8 | UNSUPPORTED in repo | decoded band is **`y_max` 30..40 (med 35, n=19)** and `y_min` 5..7; 22/30/2/8 are **probe readings outside every in-repo observation**. Donor 35 is inside | `VOCABULARY.md:251-260` |
| A7 | six bare BmAK citations (`CONTROLS.md`, `COLLISION_SELECTOR.md`, …) | UNSUPPORTED as written | all six exist under **`Research/BatmobileGrab/`**; the prefix was missing | path check |
| A8 | five `_ai.vmodc` modules at `DECODE_DEPTH.md:539-543` | VERIFIED, wrong lines | rows 539–543 are at file lines **609-613** (the numbers were table row ids) | `DECODE_DEPTH.md:609-613` |
| A9 | Vulcan point (−0.407, 1.552, −0.167) cited to `WEAPON_WIRING.md` | UNSUPPORTED as cited | it is the **built** point (`weapon-points-vs-bmak.md`), not a JC3 row; no such value in the wiring file | `weapon-points-vs-bmak.md` |
| A10 | `weapon_rpm` unit cited to `MOVING_PARTS.md:71` | UNSUPPORTED line | `:71` is `rotoscope_rpm_per_cycle`; `weapon_rpm` is at **`:61`** and **`:127`**. The unit conclusion (UNKNOWN) stands | `MOVING_PARTS.md:61,127` |

Also corrected here without an audit row: W §0.1's "two of four have a carrier" — see A1/A2.

---

## 1. Cannon — 60 mm heavy cannon (`RBatmobileHeavyCannon`)

### 1.1 Numbers, corrected

| quantity | value | source | label |
|---|---:|---|---|
| cadence | **2.0 s** | `RVehicleWeapon.FiringInterval`; manifest quote `WEAPONS.md:553` (`manifest.json:51`) | decoded |
| charge before shot | **2.5 s**, charge radius **0.0** | `RBatmobileHeavyCannon.ChargeUpTime` @0x0B00 (W §1.1) | decoded |
| damage / turret damage | **50** / **75** | `Projectile.Damage`, `TurretShotDamage` (W §1.1) | decoded |
| damage radius | **0.0** — direct hit only | `Projectile.DamageRadius` | decoded |
| projectile speed | **40000 UU/s = 400 m/s** (cap 480) | `Projectile.Speed` / `MaxSpeed` | decoded |
| momentum / recoil | **66666.67** / **15000.0** (Joker 150000) | `MomentumTransfer` / `RecoilImpulse` @0x099C (`cannon-recoil-and-muzzle-plan.md` §1) | decoded |
| fire pose | **0.700 s** (22 frames @30 fps) | `ANIMATIONS.md:95` | decoded |
| reload clip, one rack | **0.467 s** (15 frames) | `ANIMATIONS.md:119-120` | decoded |
| reload, both racks | **0.933 s** | arithmetic, nothing states they are sequential | **derived** |
| reload sound | **0.4 s**, `Engine.Play_BML_HeavyCannon_Reload` (**missing-object**) | `WEAPONS.md:925` | decoded |
| magazine / ammo | **no member** on any of the 62 weapon objects | field scan, `cannon-60mm-reload-circle-plan.md` §1 R5 | decoded absence |
| spread | **no member** | W §1.1 | decoded absence |
| HUD reload state | **5 labels** `PreReady / Ready / PreReadyLevel1 / PreReadyLevel2 / Blank`, setter **`UC_SetCannonCoolDown(0…4)`** — an **integer state**, no 0…1 fill in any of the 37 setters | `HUD.md:138`, `:167` | decoded |

### 1.2 Closest JC3 mechanism, with members

`w602_mediumtank_canon` (`Research/JC3Grab/WEAPONS.md:30`, fire_rate **1.75** at `:60`, damage 1 + blast
1500 at `:89`), carried by `v0201_car_capstone_mediumtank_debug.ee` on `main_weapon` (`:305`), point
**(0, 0.3739, −5.8174)** (`:315`), parts `Turret 26 → Cannon 38` (`:329`).

| BmAK | JC3 member | write |
|---|---|---:|
| cadence 2.0 s | `WeaponTuning.fire_rate` | **2.0** |
| two-rack reload | `magazine_size` **2** + `reload_time_scale` **1.0** + `unlimited_ammo` **1** | as listed |
| direct hit, radius 0 | `ForcePulseSettings.PlayerDamageRadius` (fleet min 1.5 m) | **1.5** |
| impulse 66666 (band 0–100) | `base_tuning.impulse` + `vehicle_impulse_factor` | **100**, **1.0** |
| reload circle | `SetCooldownRotation(0…1)` → **360°** over `MCI_mask_0_50` + `MCI_mask_50_100`; `weapon_cooldown` **−1 = no loader** | no edit (movie-side) |
| 0.4 s reload cue | an attached effect on the weapon entity (tunes hold no effects) | 0.4 s |

### 1.3 Gap

Three, and only one needs a new entity: (a) the **charge gate** has no JC3 member — closest is a second
weapon entity with `fire_rate` 2.5 sharing the muzzle; (b) the reload **duration** cannot be written
because `reload_time_scale` is a **scale 0…1**, not seconds (`WEAPONS.md:880`) — it must be calibrated;
(c) BmAK's circle is a **5-state integer**, JC3's loader takes a **fraction**, so the 0…1 is synthesised
from the reload clock (`Blank` 0.0 → `PreReady` 1.0) rather than translated.

### 1.4 Single-session build step

One sitting, one private tune, one take: clone `w602_mediumtank_canon` to
`…/w602_batmobile_cannon/`, write `fire_rate` **2.0**, `magazine_size` **2**, `reload_time_scale` **1.0**,
`unlimited_ammo` **1**, `PlayerDamageRadius` **1.5**, `impulse` **100**, read every one back; then fire
once on a 60 fps capture and solve `reload_time_scale = 0.467 / T_base`, clamped 0…1. That closes the
circle in the same session as the tune write; the charge gate (C-1) is a separate entity and stays out.

### 1.5 Pilot sentence, with a band

> Fire the 60 mm once and start the clock: the reload circle must be **full again in 0.47 s ± 0.10 s**
> (**0.93 s ± 0.15 s** if the two racks reload in sequence), and the cannon must not fire a second round
> before the circle closes.

Bands are the decoded 0.467 s and the derived 0.933 s, with ±0.10/±0.15 s = three frames of the 30 fps HUD
movie (`ModularHudBm3.TickDeltaTime` 0.033 s).

---

## 2. Vulcan — BmAK's "Chain Gun" (`RBatmobileCannon`)

### 2.1 Numbers, corrected

| quantity | value | source | label |
|---|---:|---|---|
| cadence | **0.138 s** (7.25 rps); `ComboFiringInterval` is the **same float** — no rate ramp | `FiringInterval` `0.1379999965429306` @0x0828, `vulcan-spinup-and-heat-plan.md` §2 | decoded |
| damage | **40** (upgraded 50) | `ChainGunDamage` @0x0B64 | decoded |
| spin | 1440 ÷ 2500 = **0.576 s up**, ÷ 2000 = **0.720 s down** | `ChainGunMaxSpinSpeed`/`SpinAccel`/`SpinDecel` | **derived** |
| base spread | **0.1** | `InaccuracyAngle` @0x0A70 | decoded |
| bloom curve | 0→0, **0.5→0**, **1.5→1.5**, **2.5→3.0** (linear) | `InaccuracyVsTime.Points` @0x0C4C | decoded |
| heat per second | **0.0** — the shipped gun cannot heat | `HeatUpPerSecond` @0x0A78 | decoded |
| heat release | **0.25** (`OverheatOffValue`) — **unreachable at 0 heat/s**; no cap, no cool rate | @0x0A80 | decoded |
| projectile speed | **no `Projectile` archetype** on the object | W §2.1 | decoded absence |
| heat bar / sounds | `HeatBarStart [0.79,0.68]`, `HeatBarSize [0.125,0.03]`, overheat + cooled events (**missing-object**) | @0x0A88/@0x0A90 | decoded |

### 2.2 The operator fact, now measured

`vulcan-capture-fire-and-overheat-timing.md` (capture read in place, derived data only in `tmp/`):

| event | time | relative | label |
|---|---:|---:|---|
| trigger down (audio step, +24 dB) | 11.120 s | 0.00 | measured |
| spread first visible | 12.682 s | **+1.56 s** | measured |
| **turns red** | 13.457 s | **+2.34 s** | measured |
| spread plateaus (40.6 px vs ring 25.0 px = **1.62×**) | 13.633 s | **+2.51 s** | measured |
| trigger released | **not in the clip** (fire runs to 49.14 s) | — | measured absence |

So "spreads, then turns red, **no lockout**" matches the file: red arrives in **one frame** at ≈**92 %** of
full bloom, and `HeatUpPerSecond` 0.0 means nothing can ever interrupt fire. Red is a **threshold**, not a
ramp. Whether that threshold is the spread or an unreachable heat state is **UNKNOWN** — the clip never
releases the trigger, and both readings predict the same pixels (report §7).

### 2.3 Closest JC3 mechanism, with members

`w603_mediumtank_mgun` (`WEAPONS.md:31`; fire_rate **0.1**, velocity **750** at `:61`), built as
`w603_batmobile_vulcan.wtunec`. Spread model — `base_tuning.scatter.*`: no time-keyed bloom, growth is
**per shot**. Best donor for a growing spread: **`w620_racingboat_mgun`** (0.2 / 1.85 / 0.1, recover 0.35,
reset 1.0), the only gatling in the fleet that blooms.

| BmAK | JC3 member | write |
|---|---|---:|
| 0.138 s | `fire_rate` | **0.138** |
| 0.1 base | `scatter_minimum` | **0.1** |
| 3.0 full bloom | `scatter_maximum` | **3.0** |
| (3.0 − 0.1) / 18.2 rounds | `scatter_per_shot` | **0.159** |
| recover / reset | `scatter_recover_rate` / `scatter_reset_time` | **0.35 / 1.0** (donor) |
| tracer 0.35–0.5 s | `tracer_time_to_live` | **0.4** |
| spin | `GatlingGun` → `weapon_rpm` (unit UNKNOWN) | 240 (derived 1440°/s ÷ 6) |
| red crosshair | **no member**: the reticle colour input is one of five `ECrosshairLook_*` relationship states; `E_RETICLE_CANNON` 8 is in the fall-through group with **no size rig** | — |

### 2.4 Gap

(a) time-keyed bloom vs per-shot scatter — **re-expressed** as 18.2 rounds at 0.138 s, which reproduces
the endpoints but not the curve between 0.5 s and 1.5 s; (b) **red has no carrier** in JC3 — either a new
UI element or it is accepted as absent; (c) spin-up has no decoded JC3 member
(`CBarrelSpinWeaponComponent` is present on 12 entities, members undecoded).

### 2.5 Single-session build step

In one sitting: write `fire_rate` 0.138, `scatter_minimum` 0.1, `scatter_maximum` 3.0,
`scatter_per_shot` 0.159, recover 0.35, reset 1.0, `tracer_time_to_live` 0.4 into
`w603_batmobile_vulcan.wtunec`, read back; then one 3 s held-fire take to confirm the bloom reaches its
maximum at ~2.5 s and that fire is never interrupted. Do **not** add heat (neither game has a heat member
to write) and do not claim the red.

### 2.6 Pilot sentence, with a band

> Hold the trigger for 3 s: the group must open from rest to its maximum over **2.5 s ± 0.1 s** and fire
> must never stop; on release the group must recover within **1.0 s** (the donor's `scatter_reset_time`).

Band: the measured plateau at +2.51 s against the file's 2.5 s end point; ±0.1 s is the one-frame
resolution of the 27.5 fps capture.

---

## 3. Riot mode — the riot field group on `RBatmobileCannon`

### 3.1 Numbers, corrected

| quantity | value | source | label |
|---|---:|---|---|
| cadence | **0.75 s** (Joker 0.333) | `RiotSuppressorFiringInterval` @0x0AB4 | decoded |
| lock cone | **7.5°** (Joker 9.0) | `RiotSuppressorLockOnAngle` @0x0AAC | decoded |
| range | **not serialised** on the ship object (Joker 8000) → ship value is the class default, **UNKNOWN** | `RiotSuppressorRange` @0x0AB0 | UNKNOWN |
| villain impulse | **6000.0** (Joker 1500) | @0x0AB8 | decoded |
| impact momentum | **60000.0** | `ImpactMomentum` @0x0A68 | decoded |
| damage | **no riot damage member at all** — the object's only damage is `ChainGunDamage` 40 | W §3.1 | decoded absence |
| impact VFX | `Riot_Suppressor.Anti_firearm_gel_Miss` (gel) | resolved | decoded |
| audio | `Play_RiotSuppressor_Bolt`, `Play_RiotSupressor_Impacts` — **both missing-object** | W §3.1 | decoded absence |
| build state | recipe + card, **no private tune on disk** | `manifest.json:19`; `Research/specs/B-15.md` | decoded |

### 3.2 Closest JC3 mechanism, with members

A **bullet tune with `damage` 0** — JC3 has no non-lethal flag either, and the only shipped 0-damage
object in the fleet is a **pulse**, `gen_explosion_5m_nodamage.ftune` (0 player / 0 AI, 5 m, push only,
`FORCEPULSE.md:108,131,168`). So: clone `w603_batmobile_vulcan.wtunec`, write `base_tuning.damage` **0**,
`base_tuning.impulse` **100** (band top), `vehicle_impulse_factor`/`object_impulse_factor` **1.0**,
`fire_rate` **0.75**; put the 7.5° on `AngleThresholdNewTarget` / `AngleThresholdCurrentTarget` /
`StickyAimStartAngle`; attach the three gel/tracer/casing assets on the entity.

### 3.3 Gap

No mode bit anywhere → riot must be a **second weapon entity**, and a third arm does not exist: the fleet
gives a car **2 driver slots** (`main_weapon`, `id:00568A74` — `:305`), both already used by the cannon and
the Vulcan. That is `T-WP13`, a **binding** gap, not a tune gap. Also: `RiotSuppressorRange`'s ship value
and whether a 0-damage bullet still applies impulse are UNKNOWN.

### 3.4 Single-session build step

Author the private riot tune from the Vulcan clone with the 8 members in §3.2, read back, and run the
one take: fire one round at a pedestrian and at a car at 10 m and record HP and displacement. That settles
non-lethality and the impulse in the same session. The **entity + slot** (R-2) is deliberately not in this
step — it cannot be done without the operator's slot decision.

### 3.5 Pilot sentence, with a band

> One round at a pedestrian at 10 m must leave health **unchanged (0 HP lost)** and must move the target by
> at least as much as a stock 60-impulse MG round (**displacement ≥ the control, ±10 %**).

---

## 4. Missile pods (`RBatmobileMissileLauncher`)

### 4.1 Numbers, corrected

| quantity | value | source | label |
|---|---:|---|---|
| salvo cadence | **0.5 s** | `FireInterval` @0x098C | decoded |
| targets per salvo | **8** (Joker 16) | `MaxTargets` @0x095C | decoded |
| reuse gate | **20.0 s** | `RVehicleWeapon.WeaponCoolDown` @0x0830 | decoded |
| lock cone | **40.0°** | `LockOnAngle` @0x0980 | decoded |
| lock range | **12000 cm = 120 m** (both fields agree) | `LockOnRange` @0x0984, `LethalRange` @0x0900 | decoded |
| damage / radius | **250** / **0.0** | `Projectile.Damage` / `DamageRadius` | decoded |
| momentum | **25000.0** | `MomentumTransfer` | decoded |
| projectile speed / homing | **absent on every instance** | `missile-pod-salvo-plan.md` §1.2 | decoded absence |
| bay pose | **0.833 s** open/close, 26 frames; 4 bones rotate **14.99°**, one translates **10.87 cm** | `ANIMATIONS.md` mechanism table | decoded |
| launch angle | **−20.0° pitch** (`LaunchRotationOffset` −3640 rotator units); **no per-missile cone exists** | `RPursuitModeMissileLauncher` | decoded |
| trail | names `Engine.Batmobile_Rocket_Trail` — **missing-object** → trail **length UNKNOWN** | `missile-pod-salvo-plan.md` §1.3 | decoded absence |

The count conflict must be stated, not smoothed: **8 targets, 6 bay bones, 4 tubes** on the JC3 donor.

### 4.2 Closest JC3 mechanism, with members

Two tiers. **Tier 1** `w618_sportsmuscle_missile` — the donor chassis's own pod, 4 type-2 fire points, one
`SAttachedEffect` flash per tube, `fire_rate` 0.5, turning speed **0**. **Tier 2** the salvo carrier
`w614_monorailmissilecar_missile` — the only vehicle missile that is **guided and binds the lock preset**:
`missile_turning_speed` **200**, `fire_rate` **0.25**, `burst_count` **6**, `burst_cooldown` **5**.

| BmAK | JC3 member | write |
|---|---|---:|
| 0.5 s | `fire_rate` | **0.5** |
| 8 targets | `burst_count` + `magazine_size` | **8 / 8** (outside the fleet burst max of 6 — declared) |
| 20 s gate | `burst_cooldown` | **20** (outside the fleet band 0–5 — declared) |
| 40° cone | `AngleThreshold*`, `StickyAimStartAngle` | **40** (unit UNKNOWN) |
| 120 m | `MaxAimDistance` | **120** |
| radius 0 | pulse `PlayerDamageRadius` | **1.5** |
| 2 pod points | two `SWeaponPoint`s (`MissileL`/`MissileR`, matched 0.000 cm) | keep |

Every missile in the fleet ships `scatter_minimum = scatter_maximum = scatter_per_shot = 0` — the fan comes
from **multiple muzzles**, so no scatter value is written.

### 4.3 Gap

(a) no per-target member, so an 8-salvo is `burst_count`; (b) the **20 s gate is outside every shipped
value**; (c) the pods need a **third arm** — same slot limit as riot; (d) the pod missile has **no speed and
no homing fields**, so homing would be borrowed from w614, declared as borrowed.

### 4.4 Single-session build step

Copy `w614_monorailmissilecar_missile` to `…/w614_batmobile_missilepods/`, write `burst_count` 8,
`magazine_size` 8, `fire_rate` 0.5, `burst_cooldown` 20, `MaxAimDistance` 120, `missile_turning_speed` 200,
read back, and replace the fire-point list with the two pod points. One take: one press, count eight
missiles 0.5 s apart, then confirm the 20 s refusal. Binding to a slot is out of scope (T-WP13).

### 4.5 Pilot sentence, with a band

> One trigger press must launch **8 missiles at 0.5 s intervals (last at 3.5 s ± 0.3 s)** and the launcher
> must refuse a second salvo for **20 s ± 0.5 s**.

---

## 5. Summon — calling the car

### 5.1 Numbers, corrected

| quantity | value | source | label |
|---|---:|---|---|
| trigger | pad **LB**, keyboard **E** (`pCallBatmobile`, `kCallBatmobile`) | `CONFIG2.md:291,319` | decoded |
| call sound | `Engine.Play_Gauntlet_Batmobile_Call` | `GADGET_PARAMS.md:60` | decoded |
| speed ceiling | **4000 cm/s = 40 m/s = 144 km/h** | `CLASS_DEFAULTS.md:163` | decoded |
| boost / jump-down / U-turn | `SelfDriveAllowBoost` **True**, `SelfDriveCanJumpDown` **True**, `SelfDriveUturn` **0x800000** | `CLASS_DEFAULTS.md:179`, `:152`; `CONTROLS_NATIVE2.md:34` | decoded |
| stop | **skid stop**: `bSkidToStop`, `DestReachedSkidToStop`, `SkidToStopJumpIn` | `NATIVE.md:119,134`; `PACKAGES_G305.md:565` | decoded |
| after arrival | `GetInRemoteMoveFront`/`_Back`, `JumpInBatmobileSkidStopMove` | `CLASS_DEFAULTS.md:89-91` | decoded |
| call delay / spawn offset / stop radius / self-drive cap | **UNKNOWN** — the 25 `RBatmobileRemoteBm` behaviour bodies ship with no bytecode | `GADGET_PARAMS.md` | UNKNOWN |
| fleet `Limit_Speed` band | **`y_max` 30..40 (med 35, n=19)**, `y_min` 5..7 | `VOCABULARY.md:255-258` | decoded (22/30/2/8 are probe readings — A6) |
| `.bts` trees in the index | **0** | `INDEX.jsonl` | decoded absence |

### 5.2 Closest JC3 mechanism, with members

**Carrier A — the AI tune set.** Five `_ai.vmodc` modules on the donor (`DECODE_DEPTH.md:609-613`):
`_ai` **61 rows** (`Limit_Speed`, `Input_Speed`), `_brakes_ai` 7, `_land_steering_ai` 15,
`_land_global_ai` 36, `_land_aerodynamics_ai` 5. Set `Limit_Speed.y_max` **35 → 40** (BmAK's 40 m/s);
keep `brakes_ai` `rear.handbrake` 1, `handbrake_friction_factor` **2**, `max_brake_torque` **14000**,
`min_time_to_block` **1** — that pair *is* the skid stop.

**Carrier B — the traffic driver.** `ai/bts/civilian/civilian_std.bts` bound to a `Driver` seat by rule
`03_CivilianCarLiberatedProvince` (`TRAFFIC.md:105,111`); the tree string itself is a probe finding
(`tmp/freebuff/probe/global.blo`) — A5.

**Carrier D — the anchor.** Rebel Drop has **no position field**; the car appears at the drop marker's
transform and "(menu, pricing, delivery animation) is code" (`REBELDROP.md:359`).

### 5.3 Gap

One datum: **which parameter of the behaviour tree is the goal**, and whether it accepts a player
coordinate. The `.bts` container is not in the index (0 entries), so the goal is unread, not absent.

### 5.4 Single-session build step

Clone the donor `.ee`, set `Limit_Speed.y_max` to **40**, bind a `Driver` seat to `civilian_std.bts`, place
the drop marker **80 m** down the road the player faces, and keep the `brakes_ai` set as shipped. Travel is
`t = d / 40 m/s`, so 80 m = **2.0 s** with no acceleration term (the ramp is unquantified). The
teleport-and-brake fallback is the same session's fallback: marker 6–8 m ahead, velocity 0, brakes locked.

### 5.5 Pilot sentence, with a band

> Call the car from a marker **80 m ± 10 m** away on the road ahead: it must arrive, stopped and locked,
> **2.0 s ± 0.5 s** after the call (1.75–2.25 s of travel at the 40 m/s ceiling), without the player
> moving and without either car taking damage.

---

## 6. What the four unranked weapons still share

| fact | value | source |
|---|---|---|
| driver slots on a car | **2** (`main_weapon`, `id:00568A74`); mounted slots `-` | `WEAPON_WIRING.md:305` |
| slots this build uses | cannon → `main_weapon`, Vulcan → `id:00568A74` | `manifest.json:25-30,111-116` |
| on disk under `06_vehicle` | **only** `w602_batmobile_cannon`, `w603_batmobile_vulcan` | W §8 `ls` |
| ammo in BmAK | absent from all four objects | W §5 |
| heat in JC3 | **no member anywhere** | `WEAPONS.md:880` region / W §5 |
| damage type | typed on the **part**, not the tune | W §5 |
| muzzle points | 5 of 9 built points name a BmAK socket, all match at 0.000 cm | `weapon-points-vs-bmak.md` |

The slot fact is the one blocker shared by riot mode and the pods: both are complete recipes and both need
a third arm that does not exist (`T-WP13`). That is a **binding** decision for the operator, not a gap the
build can close on its own.

---

## 7. Build-order dependencies only (no ranking)

| item | depends on | why |
|---|---|---|
| cannon | cannon private tune (exists); HUD cooldown loader | the reload circle is the shared vehicle-weapon loader, so the HUD lane must be live before the circle can be judged |
| cannon charge (C-1) | a second weapon entity on the cannon muzzle | it needs a component, not a value |
| Vulcan | Vulcan private tune (exists) | the bloom edit is inside the same file already written |
| Vulcan spin (V-2) | `GatlingGun` proven on a `CCar` (unproven today) | the part behaviour is the only spin channel |
| riot mode | **Vulcan tune as its base** + a **third arm** | it is the same `RBatmobileCannon` field group; the tune is a clone of the Vulcan's |
| missile pods | **the ranked missile lane's lock-on preset** (`autoaim_vehicle_lockon_missile`) + a **third arm** | the pods borrow guided behaviour from the same preset the ranked tracker/EMP lane binds |
| summon | **B-13 Rebel Drop entry** (built) + a `Driver`/`.bts` binding | the drop is the only spawn anchor; the drive leg needs the tree |
| summon drive leg | the `.bts` goal parameter (UNKNOWN) | without it the leg is authored, not translated |

None of this orders the four among themselves. The only hard edges are: riot and pods wait on the slot
decision; pods also wait on the lock preset; nothing waits on a ranked weapon's *values*.

---

## 8. Change record and checks

- **Intended change:** no game data modified. This document restates the audited rows with corrected
  sources and adds one section per weapon plus the summon.
- **File:** `tmp/freebuff/reports/summon-and-unranked-weapon-plans-v2.md` — the brief names it; every
  comparable plan lives in `tmp/freebuff/reports/`.
- **Revert:** delete this file. Nothing else was written.

Checks actually run this pass:

```
grep -n "moving parts on the chassis: \`mediumtank_turret\`" Research/JC3Grab/WEAPON_WIRING.md → 329, 359, 389
grep -n "0.3739" Research/JC3Grab/WEAPON_WIRING.md → 315, 345, 375, 405, 435, 465, 1908  (cannon row = 315)
grep -nE "^\| \`w60[23]" Research/JC3Grab/WEAPONS.md → 30 w602, 31 w603; fire_rate 1.75 (:60), 0.1 (:61)
grep -c '\.bts"' Research/JC3Grab/INDEX.jsonl → 0
grep -n Limit_Speed Research/JC3Grab/VOCABULARY.md → 251-254 (control points), **255-258** (x_max/x_min/y_max 30..40/y_min 5..7, n=19)
grep -nE "missile|riot|cannon|vulcan" Working/Weapons/manifest.json → cannon :25-30, vulcan :111-116,
    riot recipe ref :19, missile component :157-159
```

Not re-derived here, and carried from the reports named in the header: the capture timings (§2.2), the
reload clip lengths (§1.1), the missile bay animation, and every BmAK weapon field that lives only in
`Research/BatmobileGrab/WEAPONS.md` §8/§11/§12. No game process was started; no tune, `.ee`, `.toc` or
install file was touched.
