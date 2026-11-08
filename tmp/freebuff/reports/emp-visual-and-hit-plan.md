# EMP visuals: burst, missile, and what a hit vehicle shows

**Status: research note.** All numbers below are read from the project's decoded records
(`Research/BatmobileGrab/*`, `Research/JC3Grab/*`). Where a requested number has no carrier in the
files, the row says **UNKNOWN** and names the experiment that would produce it.

Sources: `Research/BatmobileGrab/WEAPONS.md` §9 `RBatmobileEMP`, §10 `RBatmobileEMPMissile`, §4
`Batmobile_EMPMissile_Projectile*`; `PARTICLES_FEATURES.md` (emp group, muzzle/explosion systems);
`PARTICLES.md` (per-emitter lifetime/size); `FX9_HAZE.md` (distortion carriers); `MATERIALS.md`
(EMP material instances and parameters); `ASSETS.md` (EMP package object list); `REMAINDER.md`
(`DisabledByEmpFx`); `CONTROLS_NATIVE2.md` (`DisabledByEMP` bit); `Research/JC3Grab/EMP.md` (the EMP
truck, its pulse, effects and copy list).

---

## 1. BmAK EMP burst — what the car fires

`RBatmobileEMP` on `Batmobile_EMP_Burst` (Batmobile, MK2, Funhouse; **all 12 fields identical**,
36 comparisons, 0 differences):

| field | value | meaning |
|---|---|---|
| `WeaponCoolDown` | **2.0 s** | burst recharge |
| `ChargeParticle` | `Batmobile_EMP_Burst.ChargeParticle0` → system `EMP_Burst_Charge` | the wind-up |
| `FireParticle` / `EMPFireSwitch` | ArrayProperty, **4 items each**, payload not decoded | the 4 fire stages below |
| `ImpulseComponent` | `Batmobile_EMP_Burst.ImpulseComponent0` (`RB_RadialImpulseComponent`) | the physical push |
| `MaterialToUpdateWhenPresent` | `Batmobile_V3_Wheel_EMP_MAT_INST` | own-car material swapped while EMP is present |
| `MaterialOriginalToUpdateWhenPresent` | `Batmobile_V3_Wheel_V2_MAT` | what it restores to |
| `MaterialIndexToUpdateWhenPresent` | **0** | wheel slot only |
| fire sounds | `Engine.Play_Batmobile_EMP` (`FireStartEvent` + `IndividualFireEvent`) | both `missing-object` in the grab |

### 1.1 Ring size, colour, duration

The burst is **four stages**, each its own particle system, and each stage is a flat shockwave plus
electric arcs under a distortion pass:

| stage | emitters | lifetime (s) | spawn (/s) | authored size (cm) | materials |
|---|---:|---|---:|---|---|
| `EMP_Burst_Charge` | 4 (light×4) | — | 0 | `[0,0,0]` | `Shaders.EMP_BuildUp`; colour start **`[0.0, 8.0, 1000.0]`** (deep blue, HDR) |
| `EMP_Burst_Stage_01` | 10 (light, mesh×2, sprite×2) | **0.2 – 1.0** | 0 | `[0.4,0,0]` … `[250,0,0]` | `Engine.AR_Distortion`, `Engine.EMP_Burst_Line_MAT` |
| `EMP_Burst_Stage_02` | 10 | 0.2 – 1.0 | 0 | `[0.4,0,0]` … `[250,0,0]` | same |
| `EMP_Burst_Stage_03` | 10 | 0.2 – 1.0 | 0 | `[0.4,0,0]` … `[250,0,0]`, scale-over-life to **`[20,10,20]`** | same |
| `EMP_Burst_Stage_04` | 13 (light, mesh×3, sprite×3) | **0.2 – 4.0** | **0 – 1500** | `[0.4,0,0]` … **`[250,30,30]`** | `Engine.AR_Distortion`, `Engine.EMP_Burst_Line_MAT`, `Engine.MAT_Distortion_MESH` |

So the authored numbers are:

* **Ring diameter 250 cm (2.5 m)** per stage mesh, with stage 03 carrying a scale-over-life curve that
  multiplies it up to **20×** — a *derived* reading (5,000 cm ≈ 50 m at full scale), not a stated radius.
* **Duration 0.2–1.0 s** for stages 01–03 and **0.2–4.0 s** for stage 04.
* **Colour:** charge is deep blue `[0, 8, 1000]`; the burst sprites start white `[1,1,1]` and are tinted
  by the blue material family that ships with the effect:
  `INST_New_Electric_Arc_BLUE_THIN` (radius A 1.0 / radius B 1.5), `MAT_Flat_Shockwave_INST_BLUE`
  (**brightness 10.0**), `INST_Digital_Noise_BLUE`, and `EMP_Burst_V02_Stage_01…04` (parent
  `Engine.EMP_Burst_V02_MAT`, no instance parameters).
* **Own-car glow:** the wheel material instance carries `EMP` (0.0 shipped) and
  `EMP_Emissive_Multiplier` **350.0** (Batmobile, MK2) / **650.0** (Joker test instance) — the tyre
  emissive that pulses while the EMP is charging.

**Burst radius is UNKNOWN.** `RBatmobileEMP` has no radius/damage field; the only spatial carrier is the
`RB_RadialImpulseComponent`, whose radius is not in the decoded table.

---

## 2. BmAK EMP missile

`RBatmobileEMPMissile` on `Batmobile_EMP_Missile_Launcher` (21 fields, identical across 3 packages):

| field | value |
|---|---|
| `ProjectileForCarsArchetype` | `Batmobile_EMPMissile_Projectile_ForCars` |
| `MissileLockOnDuration` | **2.0 s** (civilian **1.0 s**) |
| `MissileLaunchSockets` | ArrayProperty, **2 items**, payload not decoded |
| `LauncherAnimNodeName` | `"PursuitMissileAnim"` |
| `LoseLockXBonus` / `LoseLockYBonus` | **600.0 / 800.0** |
| launch socket / offset | `"BattleModeSpotLight"`, `[-3640, 0, 0]` rotator = **−20.0° pitch** |
| `bInstantFire` | true |

Projectile visuals — `Batmobile_EMPMissile_Projectile_ForCars` resolves only FX, no combat numbers:

| role | target | sizes / duration |
|---|---|---|
| explosion | `Rocket.Batmobil_Rocket_Explosion_Small` (9 emitters) | lifetime **0.2–3 s**, rate 0–600, size up to **`[450,10,25]` cm** |
| impact flame trail | `Damage_States.FireTrail_Car` (9 emitters) | lifetime 0.5–3 s, rate 0–50 |
| trail | `…RocketTrail` component | **no particle template** — the missile leaves no trail |
| damage / radius / speed / lifetime | **absent** on the `_ForCars` archetype | — |

The sibling archetype `Batmobile_EMPMissile_Projectile` (not the `_ForCars` one) carries
**Damage 60**, `DamageRadius 0`, damage type −104 (`DAMAGE_RULES.md` §3.5) — versus **250** on the Joker
missile. So the EMP missile is a low-damage, effect-driven round, and its "look" is the small rocket
explosion plus the EMP pulse the target runs.

---

## 3. What a hit vehicle shows — BmAK's hooks

| hook | evidence | what it gives us |
|---|---|---|
| `DisabledByEmpFx` | `REMAINDER.md` field 7319 (`ComponentProperty`, offset 7319, 34 refs, value **True**), also listed among the archetype tag names in `PACKAGES_G305.md` | the vehicle carries an **FX component** for the disabled state — the visual carrier exists |
| `DisabledByEMP` | `CONTROLS_NATIVE2.md`: control-mask bit **`0x40000000`** | the input lock while disabled |
| `RDeadVehicle` / `Dead_Batmobile` | `ASSETS.md` (4 `RDeadVehicle` objects per package, 1 named) | the wreck state asset, not the EMP state |
| `EMPRepairable` | `DAMAGE_RULES.md` §5 | Batmobile-specific EMP repairability flag |

**UNKNOWN:** what the disabled FX component actually draws (no particle/material binding for it was
decoded) and how long the disabled state lasts. Those are code-side.

---

## 4. JC3's closest carriers, and the pairing

### 4.1 The pulse and its look

| JC3 object | value | source |
|---|---|---|
| `CForcePulse` named `EMP` | `truck_emp.ftune`, position (0, **2.0356**, 0.6992) | `EMP.md` §2 |
| `truck_emp` tune | **100 damage in 25 m**, `*RadiusMin` 1, `*RadiusPercentageMax` 1 (full damage to the edge) | ″ |
| plain blast for scale | 500 damage in 5 m, `*RadiusMin` 0, `*RadiusPercentageMax` 0 | ″ |
| EMP-only data beyond radius | 3 flags (`id:4912FC04`, `id:AE6F7EFF`, `id:CF4F7880`) + the material-effect table | ″ |
| victim look | `CMaterialEffectTable` **`emp_flatbed_table`** — maps **every material slot** to one effect hash → embedded **`effects/destruction/explosion_emp_flatbed.effc`** (24,015 B) | ″ |
| charging prop | `effects/props/emp_active.effc` (8,783 B) + `CEffectPointEmitter epe_emp_powering_up` (enabled 0) | ″ |
| camera | embedded `full_screen_effect.ctunec` | ″ |
| EMP weapon class | `CEMPWeapon` on `w702_emp` (500 dmg / 50 m) and `w503_turret_emp` (500 / 750 m); **no EMP fields in either tune** | `EMP.md` §6 |
| duration / disable semantics | **not in any decoded member** | `EMP.md` §8 |

### 4.2 Pairing, BmAK ↔ JC3

| BmAK element | closest JC3 carrier | why this one | class |
|---|---|---|---|
| `EMP_Burst_Charge` (blue build-up, `EMP_BuildUp`, colour [0,8,1000]) | `emp_active.effc` + `epe_emp_powering_up` | the only charging EMP effect in JC3 | measured pairing |
| `EMP_Burst_Stage_01…04` (2.5 m flat shockwave, 0.2–4 s, distortion) | `explosion_emp_flatbed.effc` (24 KB) | the pulse's embedded effect file, the only EMP explosion asset | measured pairing |
| burst victim look (material/emissive flash) | `emp_flatbed_table` (`CMaterialEffectTable`) | the only victim-side visual carrier in JC3 data | measured pairing |
| EMP missile explosion (`Batmobil_Rocket_Explosion_Small`, 0.2–3 s, ≤450 cm) | `explosion_emp_flatbed.effc` | JC3 has no EMP missile; the EMP blast is the same effect | **our choice** |
| own-car wheel EMP emissive (`EMP_Emissive_Multiplier` 350/650) | no JC3 equivalent decoded | — | **add** |
| `DisabledByEmpFx` + `DisabledByEMP` bit | no JC3 equivalent found; `CEMPWeapon` is class-driven | disable semantics are code in both games | **UNKNOWN both sides** |

### 4.3 Values we use

| # | setting | value | source |
|---|---|---|---|
| 1 | pulse | `CForcePulse` `EMP` + `truck_emp.ftune` | JC3 stock, copied |
| 2 | radius / damage | **25 m / 100**, full damage at the edge | JC3 stock (`EMP.md`) |
| 3 | pulse height | **2.0356 m** above the vehicle origin | JC3 stock |
| 4 | burst visual | `explosion_emp_flatbed.effc` | JC3 stock |
| 5 | charge visual | `emp_active.effc` | JC3 stock |
| 6 | ring size to author | **250 cm** base mesh, growth curve to **20×** | BmAK measured; the 50 m result is derived |
| 7 | ring duration | **1.0 s** per stage, **4.0 s** final stage | BmAK measured |
| 8 | colour | deep blue charge `[0,8,1000]`; shockwave `MAT_Flat_Shockwave_INST_BLUE` brightness **10**; arc radius A 1.0 / B 1.5 | BmAK measured |
| 9 | cooldown | **2.0 s** burst / lock-on **2.0 s** (civilian 1.0) | BmAK measured |
| 10 | victim flash | `emp_flatbed_table` as a material effect table on the victim | JC3 stock mechanism |
| 11 | disable duration | **not set** | UNKNOWN in both games |

**Not set:** any disable duration, any "engine stops" visual, and any EMP-specific damage number beyond
the JC3 pulse's 100 — none of those exist as data in either title.

### Probes that would close the gaps

1. Fire the JC3 truck EMP at a car and watch what `emp_flatbed_table` does to the victim's materials
   (this also gives the visual duration, which no file states).
2. Read the `DisabledByEmpFx` component's particle binding from the BmAK package (the field exists with
   value True; its template is not in the tables we decoded).

## 5. Checks run for this note

* Re-read `RBatmobileEMP` (§9) and `RBatmobileEMPMissile` (§10) field tables; confirmed all-identical
  counts (36 and 63 comparisons).
* Re-read `PARTICLES_FEATURES.md` emp group and `PARTICLES.md` per-emitter lifetime/size blocks for
  `EMP_Burst_Stage_01…04` and `EMP_Burst_Charge`.
* Re-read `MATERIALS.md` EMP instances for `EMP_Emissive_Multiplier` 350/650, arc radii and shockwave
  brightness.
* Re-read `FX9_HAZE.md` for the EMP systems' distortion materials and lifetimes.
* Re-read `Research/JC3Grab/EMP.md` end to end for the pulse, effect files, material table and limits.
* No game process started; `Research/` was read only.
