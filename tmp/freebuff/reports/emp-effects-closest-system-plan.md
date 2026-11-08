# EMP / immobiliser effects on enemy vehicles — closest JC3 system per lead, and what the build sets

Card: `reports/emp-effects-scrape-leads.md` (the lead table A1–B5 and §6 UNKNOWNs). Rule applied:
**a gap is closed by the build, not reported** (`STAGES.md`) — no row below ends at "no member".

Labels: **decoded** = bytes read at the path/offset named; **derived** = rule + arithmetic shown;
**UNKNOWN** = searched, not found, and the file that settles it named.

Plan only: no `.effc`, `.ftune`, `.wtune`, `.epe`, module, bank or receipt was written; no game ran.
Revert = delete this file.

**Provenance / reversibility.** New file, `tmp/freebuff/reports/emp-effects-closest-system-plan.md`.
It changes no source, record or package; reverting it is deleting it. It is the correct file because
it is the requested output path, and every number in it is copied from the lead report or derived
from a number in it (arithmetic shown inline).

---

## 0. Answer in seven lines

1. **Disable mechanism:** the only data-side writer of a vehicle disable is the engine's
   `CEMPWeapon` class, shipped as `w702_emp` (id 702, type 6, 500 dmg / 50 m) and `w503_turret_emp`
   (503 / 2 / 500 / 750 m). The class carries no EMP field in either tune, so the *state* is
   class-keyed and its duration is native (`is_disabled_by_emp` has **0** asset bindings).
2. The build mounts a cloned `CEMPWeapon` in the Batmobile's second driver slot
   (`id:00568A74`), with `weapon_id` moved into the icon-bearing range (601–622) so the slot renders,
   and a pulse copy as the visual/radial leg. Both legs are data; the *duration* is the one number no
   file carries, and it is bracketed by `[2, 4, 8, 12]` s.
3. **Visual carrier:** `explosion_emp_flatbed.effc` (24,015 B) reached through
   `CMaterialEffectTable emp_flatbed_table`, plus `effects/props/emp_active.effc` (8,783 B) for the
   charge. `.effc` is writable (`effc_writer.py`: carry round-trip + a verified
   `EmitterTemplates[0].MaxParticles` edit).
4. **Numbers to set** come from the BmAK burst: 4 stages, ring **250 cm** mesh with a **20×**
   scale-over-life (= **50 m**), lifetimes **1.0 s** (stages 01–03) and **4.0 s** (stage 04),
   `Range` **7500 UU = 75 m**, `PowerLevelChargeTime` **[0, 0.5, 1.0, 1.5] s**, charge colour
   **[0, 8, 1000]**, shockwave brightness **10**, arc radii **1.0 / 1.5**, cooldown **2.0 s**
   (archetype) vs **10.0 s** (CDO).
5. The derived spatial relation is the useful one: the ring grows to **50 m** inside a **75 m**
   `Range` — **0.667×**; the build keeps 20× and records 30× (= 75 m) as the alternate if the ring
   must match the disable radius.
6. **Audio carrier:** `w702`'s own charging/charged/fire effects and sounds (the only weapon-side
   EMP sounds decoded), bound onto the Batmobile weapon's effect rows. BmAK's
   `Engine.Play_Batmobile_EMP` is `missing-object` — there is no host sample to import, so the JC3
   event is reused, not authored.
7. Every remaining silence is a probe, not a wish: duration (Q-EMP-1/4), whether a `CEMPWeapon` is
   accepted on a car (Q-EMP-3), whether the pulse alone disables (Q-EMP-2), and stage↔power-level
   binding (§8 U-5).

---

## 1. What BmAK actually ships (the numbers to reproduce)

From `reports/emp-effects-scrape-leads.md` §1/§3 and `Research/BatmobileGrab/WEAPONS.md` §9/§10:

| element | value | label |
|---|---|---|
| battle-mode object | `RBatmobileEMP` `Weapons.Batmobile_EMP_Burst`, super `RVehicleWeapon`, 2,552 B | decoded |
| `Range` @2396 | **7500.0** = **75 m** (UU→cm→m) | decoded / derived |
| `DisableEnemyDuration` @2400 | **[2.0, 4.0, 8.0, 12.0]** s, index = power level | decoded (CDO export 46694) |
| `PowerLevelChargeTime` @2424 | **[0.0, 0.5, 1.0, 1.5]** s | decoded |
| `EMPImpulse` @2512 / `EMPVehicleImpulse` @2528 | **[5000.0] / [20000.0]** (unit not stated) | decoded |
| `WeaponCoolDown` @2096 | **2.0 s** in the archetype, **10.0 s** in the CDO | decoded |
| `ChargeParticle` @2416 | `Batmobile_EMP_Burst.ChargeParticle0` → `EMP_Burst_Charge` | decoded |
| `FireParticle` @2440 / `EMPFireSwitch` @2472 | 4 items each (one per power level) | decoded counts / payload UNKNOWN |
| `ImpulseComponent` @2496 | `RB_RadialImpulseComponent` | decoded |
| `EMPFireSound`; `FireStartEvent`/`IndividualFireEvent` @2176/@2200 | `Engine.Play_Batmobile_EMP` — **missing-object** in the grab | decoded (missing) |
| stages 01–04 | 10 / 10 / 10 / 13 emitters; lifetime **0.2–1.0 s** (01–03), **0.2–4.0 s** (04); sizes **0.4 … 250 cm**; stage 03 scale-over-life **20×**; stage 04 rate **0–1500/s**, size **250×30×30 cm** | decoded (`PARTICLES.md`) |
| charge system | 4 light emitters, `Shaders.EMP_BuildUp`, colour **`[0.0, 8.0, 1000.0]`** | decoded |
| materials | `MAT_Flat_Shockwave_INST_BLUE` brightness **10.0**; `INST_New_Electric_Arc_BLUE_THIN` radius A **1.0** / B **1.5** | decoded |
| own-car emissive | `EMP_Emissive_Multiplier` **350** (Batmobile) / **650** (Joker) on the wheel instance | decoded |
| target-side hook | `RVehicleNPC.ParticlesEMP` (11281, ComponentProperty); `DisabledByEmpFx` (offset 7319, True) | decoded (member) / template UNKNOWN |
| missile | `RBatmobileEMPMissile`: lock **2.0 s** (civilian **1.0**), `MaxSpeed` **7500**, `AccelRate` **40000**, `Damage` **60**, `DamageRadius` **0**, `MyDamageType` `RDmgType_BatmobileCannon`, explosion `Batmobil_Rocket_Explosion` (14 emitters) / `_Small` (9); `_ForCars` serialises **no** scalars | decoded |
| impact sound | `Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact` — on the **orphan** sibling projectile only | decoded (sibling) / UNKNOWN (fired) |

**Derived facts this plan uses**

| # | value | arithmetic | use |
|---|---:|---|---|
| D1 | **75 m** | `Range` 7500 UU ÷ 100 = 75 m | pulse `PlayerDamageRadius` / `AIDamageRadius` (JC3 25 m stock → ×3) |
| D2 | **50 m** | 250 cm mesh × 20 (scale-over-life) = 5,000 cm = 50 m | ring's grown diameter |
| D3 | **0.667** | 50 / 75 = 0.667 | ring / disable radius; the visual covers two-thirds of the effect |
| D4 | **30×** | 75 m / 2.5 m = 30 | alternate scale so the ring reaches `Range` |
| D5 | **6000** | 1500/s × 4.0 s = 6,000 | stage-04 `MaxParticles` cap |
| D6 | **0.333 / 0.667 / 1.0** | 0.5/1.5, 1.0/1.5, 1.5/1.5 | charge timeline `EndX` breakpoints for the 1.5 s top level |
| D7 | **2.0 s** | archetype `WeaponCoolDown` (the CDO's 10.0 is not the shipped value) | tune `fire_rate` |
| D8 | **75 m/s / 400 m/s²** | 7500 UU/s ÷ 100; 40000 UU/s² ÷ 100 | missile `velocity` / `acceleration` |
| D9 | **4.5 m** | explosion size `[450,10,25]` cm → 4.50 m | missile explosion start size |
| D10 | **0.1 s** | BmAK charge level 0 is instant (`PowerLevelChargeTime[0]` = 0.0) | minimum visible charge before a tap-fire |

---

## 2. JC3 mechanisms that disable or stall a vehicle

Searched in this order: engine-kill on damage, the stalled-engine state, the electrical channel, the
EMP weapon class, the state setter. All citations are from `tmp/freebuff/reports/immobiliser-and-emp-trigger.md`
(itself citing `VOCABULARY.md`, `WATER.md`, `DAMAGE_MODEL.md`, `EMP.md`, `t_md2_emp_state.py`).

| # | mechanism | member / value | what it can actually do | verdict for this build |
|---|---|---|---|---|
| M1 | **`CEMPWeapon` (the class)** | exe RTTI `.?AVCEMPWeapon@@` @0x2D6E058; shipped `w702_emp` (id 702 / type 6 / 500 dmg / 50 m) and `w503_turret_emp` (503 / 2 / 500 / 750 m); **no EMP field in either tune** | the state is class-keyed; the hit path is native and sets `is_disabled_by_emp` if it sets anything | **selected — primary disable leg.** Mountable-in-a-car is the one open question (probe Q-EMP-3) |
| M2 | **`CForcePulse` `EMP`** | `truck_emp.ftune`: `PlayerDamage`/`PlayerDamageRadius` **100 / 25**, `…RadiusMin` **1**, `…RadiusPercentageMax` **1**; flags `4912FC04`=0 / `AE6F7EFF`=1 / `CF4F7880`=1 (unique among 307 pulses); `CMaterialEffectTable emp_flatbed_table`; position (0, **2.0356**, 0.6992) | damages and draws; whether it disables is the unique flag triple, not a member | **selected — visual + damage leg**; disable claim is probe Q-EMP-2 |
| M3 | engine-kill on damage | `LandEngine.engine_max_damage_torque` **0.25–0.75** (fleet, n=145); `damage_from_parts[].damage_ratio_from_broken_off` **1** | floors torque at 25–75 %; never 0 | **carried as a *fallback stall***: a **private** copy of the victim-side module is not permitted (R7, shared `vehicle_common`), so this is only usable if the class leg fails — value 0.0 is outside the fleet domain and is a declared switch (D-F1) |
| M4 | stalled-engine state | `vehicle_common.car_common.engine_shut_down_delay_s` **30** (boats/helis/planes/bikes **5**) | the only engine-off timer in data; trigger is water, not any weapon/pulse; shared file | **not a carrier** (trigger absent, file shared). Recorded so no later card re-opens it |
| M5 | electrical damage channel | `VehicleDamage.electricity_armor` **−1..0**, `electricity_armor_strength` **0..100**; build already **−1 @ 100** | armour domain only; no weapon tune names a damage channel (0/1,515 members) | **not a stall**; used only as the channel the EMP hit is assumed to arrive on (U-4) |
| M6 | state variable | `is_disabled_by_emp` @0x24EA080 in the vehicle-variable block; literal **0** in 1,941 entries (3.98 GB), Jenkins hash `0x0A6B5E46` **0** in 1,307 entity entries (3.96 GB); controls `invulnerable` 289 / `is_in_water` 160 hit on the same pass | a name the engine tracks; **nothing in data writes or reads it** | **the target of both legs**; a value-driven effect/HUD may read it (U-3) |

**Derived:** there is no data path from "a pulse fires" to "the engine stops"; the only data path that
ends in the state is the class. The build therefore ships **both** a class leg (disable) and a pulse
leg (damage + visual), and the pilot separates them: if the car stalls with the class leg and not with
the pulse, the pulse is visual-only and the class carries the state.

---

## 3. Visual carriers and the `.effc` members to set

### 3.1 The two shipped carriers

| carrier | value | label |
|---|---|---|
| `effects/destruction/explosion_emp_flatbed.effc` | **24,015 B**, reached by `emp_flatbed_table` mapping **every material slot** to one effect hash | decoded (`EMP.md` §4) |
| `effects/props/emp_active.effc` | **8,783 B**; the mm250 mission's charging prop is `CEffectPointEmitter epe_emp_powering_up` (hash −1458959942, `enabled` 0) at (−0.011, 2.448, 0.07) | decoded (`EMP.md` §5) |
| `.effc` vocabulary | 94 member paths: `EmitterTemplates[]`, `Emitters[]`, `Instantiators[].RenderInfos[].RenderBlockTypeHash`, `Timelines[]` (`EndX` 0..1, `StartX` 0..0.997, `XScaleRecip` 0..337), `Modifiers[]`, `Params[]` (−10000..100000) | decoded (`FX.md`, `FX_VOCAB.json`) |
| writer | `effc_writer.py` — 95/95 carry round-trip; an `EmitterTemplates[0].MaxParticles` edit re-reads and reverts byte-identically; editable leaves `MaxParticles`, `EmitterTemplateIndex`, `Lifetime`, `StartTime`, `Flags` | decoded (`Working/Effects/EFFC_WRITER.md`) |

### 3.2 `bm_emp_burst.effc` — the burst, member by member

Built as a **carry-mode edit of `explosion_emp_flatbed.effc`** (`effc_writer.py`), never a new format.
Emitter order maps BmAK's four stages; the values below are D-numbers from §1.

| BmAK stage | `.effc` row to write | value | why |
|---|---|---|---|
| 01 (10 emitters, light/mesh/sprite) | `EmitterTemplates[i].Lifetime` | **1.0** s | stage 01 max lifetime |
| 02 (10) | `EmitterTemplates[i].Lifetime` | **1.0** s | stage 02 max lifetime |
| 03 (10, scale-over-life 20×) | `EmitterTemplates[i].Lifetime` + `Timelines[].EndX` = 1.0 | **1.0** s | the growth curve's full span |
| 04 (13, rate 0–1500) | `EmitterTemplates[i].Lifetime` | **4.0** s | stage 04 max lifetime |
| 04 particle cap | `EmitterTemplates[i].MaxParticles` | **6000** | D5 (1500/s × 4.0 s) |
| 04 start time | `EmitterTemplates[i].StartTime` | **0.0** s | all four stages fire on the burst frame (U-5 is the intra-frame order) |
| ring size | `Params[]` size block on the ring emitter | **2.5 m** (=250 cm) base, growth **20×** (50 m, D2) — alternate **30×** (75 m, D4) | BmAK authored mesh + scale curve |
| charge colour | `Params[]` colour on the charge emitter | **(0.0, 8.0, 1000.0)** | `EMP_BuildUp` start colour, inside `Params[]`'s −10000..100000 |
| shockwave brightness | material instance param `MAT_Flat_Shockwave_INST_BLUE` = **10.0** | **10.0** | decoded BmAK value; the carrier is a material instance, not the `.effc` (U-6) |
| arc radii | `INST_New_Electric_Arc_BLUE_THIN` radius A **1.0** / B **1.5** | **1.0 / 1.5** | decoded; same material carrier |
| flags | `EmitterTemplates[i].Flags` | keep the donor's | no BmAK analogue decoded (U-5) |

**Charge leg:** `emp_active.effc` is reused as-is, with `Lifetime` **1.5 s** on the charge emitter so
it spans `PowerLevelChargeTime[3]`; the `CEffectPointEmitter` is enabled (the mm250 donor ships
`enabled` **0**) and its timeline `EndX` uses D6's breakpoints (0.333 / 0.667 / 1.0) so the four power
levels read as four charge stops.

**Victim leg:** `emp_flatbed_table` is reused unchanged (every material slot → the burst effect). Its
payload is a **30-byte opaque blob per entry, 72 objects** (no member list decoded), so the only
number the build sets is *which* table an entity points at, not a member inside it (U-7).

---

## 4. Audio carriers and the events to bind

| element | BmAK | JC3 carrier | what the build does |
|---|---|---|---|
| charge whine | `ChargeParticle0` plays while `PowerLevelChargeTime` runs 0→1.5 s; no separate loop event decoded | `w702_emp`'s **charging/charged** effects and sounds (the only weapon-side EMP sounds decoded, `EMP.md` §6) | bind the charging GUID on the weapon's effect rows, start at 0.0 s, stop on the burst frame |
| burst zap | `FireStartEvent` + `IndividualFireEvent` both `Engine.Play_Batmobile_EMP` — **missing-object**, so there is no sample to import | `w702_emp`'s **fire** sound (same block) | bind the fire GUID on the pulse/burst, one event, switched by `EMPFireSwitch`'s **4** states (one per power level) |
| missile impact | `Play_Batmobile_Immobiliser_Impact` — resolved on the **orphan** sibling projectile, never fired | the pulse's own `SAttachedEffect` sound row | bind the fire event at the impact, not a second authored event |
| switch granularity | `EMPFireSwitch` = **4** items | JC3 Sound switch states (mechanism decoded in `JC3_AUDIO.md`; names not decoded for this event) | 4 states, index = power level 0–3 |
| loop/stop shape | Play + `Stop_` pair not present for EMP | `w702` charging has a charged state, so the stop is the state change | stop on burst, no `Stop_` event authored |

**Why no new bank:** JC3's event → bank → sample chain is `Sound` object GUID → bank EVTS →
samples (the nitro chain is the worked example: GUID `f74ea43b…` → `vehicles` EVTS 249 → 3 samples).
There is **no FEV writer** in `Tools/scripts/`, so authoring a new event is not available to the
build; binding an existing GUID is.

---

## 5. The build composition

New private tree `Builds/bm-RC4-emp/`, based on `Builds/bm-RC4`. Four legs, each removable alone.

### Leg A — the disable: a cloned `CEMPWeapon` in a driver slot

1. **Weapon tune:** private copy of `w702_emp.wtunec` → `bm_emp_weapon.wtunec`; set `damage`
   **500** (shipped), `max_range` **75** (D1), `fire_rate` **2.0** (D7). No EMP field exists, so none
   is invented.
2. **Weapon entity:** clone the `w702_emp` weapon entity's component block into the Batmobile `.epe`
   as the **second driver slot** `id:00568A74` (`WEAPON_WIRING.md` §1 — the unnamed second pointer),
   keeping class `CEMPWeapon` and `weapon_type` **6** (as shipped on `w702`).
3. **Icon:** `weapon_id` is the icon key (`textures/ui/weapon_icons/<id>.ddsc`) and **702 has no
   icon** (shipped icons: 206, 601–622; **614** is missing too). Set `weapon_id` to a shipped id in
   **601–622** so slot 1 renders — the class, not the id, carries the behaviour.
4. **Cooldown display:** `weapon_cooldown` in `InitVehicleWeapons` is a **0..1 fraction** or −1; feed
   it `t / 2.0` (D7) during the recharge.

### Leg B — the pulse: damage + the only disable candidate besides the class

1. Copy the `rebel_emp_01` `CForcePulse` object (`EMP`, `truck_emp.ftune`) onto the car, at the
   chassis centre (**0, 1.2, 0.0** m — derived: the truck's 2.0356 m is its flatbed deck height, the
   car's roof line is ~1.2 m).
2. Private `bm_emp_pulse.ftune`: `PlayerDamage` **100**, `PlayerDamageRadius` **75** (D1),
   `PlayerDamageRadiusMin` **1**, `PlayerDamageRadiusPercentageMax` **1**; the `AIDamage*` four the
   same. The three flags stay as shipped (`4912FC04`=0 / `AE6F7EFF`=1 / `CF4F7880`=1) — they are the
   only data-side switch and cost nothing.
3. Trigger: copy `trigger.use_item` + `entry.use_item` → `S_STUNT_USE_ITEM_VEHICLE` with prompt
   `ui_activate_emp` from the truck (decoded), so the pulse has the same door into the game the only
   shipped EMP has.

### Leg C — the visual: `bm_emp_burst.effc` + `emp_active.effc`

1. Carry-mode edit of `explosion_emp_flatbed.effc` with §3.2's members.
2. `emp_active.effc` copied private, `Lifetime` 1.5 s, `enabled` **1** on the charge emitter row.
3. `SAttachedEffect` rows on the car for both, usage `EMP` (the pulse's own usage name).
4. Own-car wheel emissive (`EMP_Emissive_Multiplier` 350/650) is **out of scope**: it is a Batmobile
   material instance for the *charging car*, not an enemy-vehicle effect.

### Leg D — audio

Bind the three `w702` GUIDs (charging / charged / fire) on the Leg A weapon's `SAttachedEffect` sound
rows; 4 switch states; stop on burst.

### Offline checks

| check | command | pass |
|---|---|---|
| burst decodes and reverts | `python Tools/scripts/effc_writer.py check` | carry round-trip identical; the edited `MaxParticles` re-reads |
| edited burst values read back | `python Tools/scripts/jc3fx.py check` | `Lifetime` 1.0/4.0, `MaxParticles` 6000, `StartTime` 0.0 at the named rows |
| pulse tune values | `python Tools/scripts/jc3forcepulse.py --check` | radius 75, min 1, percentage 1, damage 100 (both player and AI) |
| weapon mount | `python Tools/scripts/bm_entity.py --check` | 8 non-null slot ids; `id:00568A74` → the `CEMPWeapon` component |
| icon resolves | `jc3index` path lookup | `textures/ui/weapon_icons/<id>.ddsc` exists for the chosen id (≠ 614) |
| `.toc` internal | `eetoc.py verify` / `aafdiff` | record offset ≠ 0, size matches, file count +3 |
| tamper | flip `Lifetime`, `MaxParticles`, one radius, force `.toc` offset 0 | each caught and reverted |

---

## 6. The numbers, once, with their source

| # | what | value | source / derivation |
|---|---:|---|---|
| N1 | disable window | **2 / 4 / 8 / 12 s** (power level 0–3) | `DisableEnemyDuration` decoded; **no JC3 member** — probe P-D1 |
| N2 | charge time | **0 / 0.5 / 1.0 / 1.5 s** | decoded; `emp_active.effc` `Lifetime` 1.5 |
| N3 | burst radius | **75 m** | D1: `Range` 7500 UU |
| N4 | ring diameter | **2.5 m** → **50 m** (20×) → alt **75 m** (30×) | D2/D3/D4 |
| N5 | stage lifetimes | **1.0 s** (01–03), **4.0 s** (04) | §1 decoded; written to `Lifetime` |
| N6 | stage-04 particle cap | **6000** | D5 |
| N7 | charge colour | **(0, 8, 1000)** | decoded `EMP_BuildUp` |
| N8 | shockwave brightness / arc radii | **10.0** / **1.0, 1.5** | decoded materials |
| N9 | pulse damage | **100** | JC3 `truck_emp.ftune` (unchanged) |
| N10 | weapon damage / range | **500 / 75 m** | `w702_emp` 500; range D1 |
| N11 | cooldown | **2.0 s** | D7 (archetype, not the CDO) |
| N12 | impulse | **5000 / 20000** (unit UNKNOWN) | decoded; no JC3 pulse member — U-8 |
| N13 | missile speed / accel | **75 m/s / 400 m/s²** | D8 |
| N14 | missile damage / radius | **60 / 0** | decoded (`_ForCars` serialises none — U-9) |
| N15 | missile lock | **2.0 s** (civilian 1.0) | decoded; no AutoAim duration member — U-10 |
| N16 | missile explosion size | **4.5 m** | D9 |
| N17 | EMP sound switch states | **4** | `EMPFireSwitch` 4 items |

Nothing is rescaled silently: every JC3 write above is either the shipped JC3 value, a BmAK value
copied 1:1, or a D-number whose arithmetic is printed.

---

## 7. Pilot cards — one sentence, one band, per effect

| effect | pilot-card sentence | pass band |
|---|---|---|
| **P-D1 disable (class leg)** | Fire the EMP slot at a stationary civilian car inside 75 m at power level 0, 1, 2, 3 and time the restart from the burst frame. | engine stops within **1 frame** 4/4; restart at **2 / 4 / 8 / 12 s ± 1 s** for the four levels 4/4 |
| **P-D2 pulse alone** | Park a stock car within 25 m of the EMP truck and press the flatbed's use-item, then repeat with the Batmobile's pulse copy. | with the truck: car stalls **3/3** or takes exactly **100** damage and drives on **3/3** (either answer is a pass; a mix is a fail) |
| **P-D3 class-on-a-car** | Install the Leg A build and fire slot 2 at a stock car at 10 m, then at 70 m. | same stall signature as P-D1 at both ranges **3/3**; no stall means the class is not vehicle-mountable and Leg B becomes the only disable |
| **P-V1 charge** | Hold the EMP button without firing; watch the wheels and the pulse origin from t = 0 to 1.5 s. | blue build-up visible from **≤0.1 s** (D10) and reaching full brightness by **1.5 s** **3/3** |
| **P-V2 burst ring** | Fire at an empty road and measure the ring against the car's own 4.5 m length. | ring starts at **2.5 m** and grows to **50 m ± 5 m** by **1.0 s**, gone by **4.0 s** **3/3** |
| **P-V3 no explosion** | Fire at a car and watch for smoke, flame or debris. | **0** smoke emitters, **0** flame emitters, **0** debris parts on **3/3** bursts |
| **P-V4 victim flash** | Fire at a car with a visible paint panel, from 8 m, camera fixed. | the target's materials flash within **0.1 s** of the burst and return by **4.0 s** **3/3** |
| **P-A1 charge + burst audio** | Record the charge and the burst with the HUD off, then listen for a whine before the zap and nothing after 0.3 s. | charge audible for the full hold **3/3**; burst event on the fire frame **3/3**; no tail beyond **0.3 s** **3/3** |
| **P-A2 switch granularity** | Fire at levels 0 and 3 back to back and compare the zap. | the two levels are audibly different **3/3**, or identical **3/3** with the switch row recorded as unused |
| **P-M1 missile disable** | Fire the pursuit EMP missile at a car at 30 m and time the restart. | impact within **0.4 s** at 75 m/s; stall **3/3**; restart inside the P-D1 band for the same level |
| **P-T1 tank response** | Fire the EMP at a heavy tank and at a chopper drone. | drone stalls **3/3**; tank shows no stall and plays one bark **3/3** (BmAK's own `EMPIneffectiveLine` shape) |

---

## 8. UNKNOWNs — each with the file that settles it

| # | unknown | settles with |
|---|---|---|
| U-1 | the disable's **duration** on the Batmobile's target | `RBatmobileEMP` CDO is decoded ([2,4,8,12]); the JC3 side has no member — `JustCause3.exe` `CEMPWeapon` hit path (not decoded) + probe P-D1 |
| U-2 | whether a **`CEMPWeapon` is accepted in a car's weapon slot** (0 of 88 vehicle components is one) | `JustCause3.exe` weapon-class factory; probe P-D3 |
| U-3 | whether code **reads `is_disabled_by_emp`** by name/hash (0 asset bindings) | `ARMOR_STEP.md` §2's instruction + pointer scan applied to the vehicle-variable block 0x24E9F40..0x24EA210 |
| U-4 | which **damage channel** a `CEMPWeapon` hit uses (`electricity` −1..0 vs `explosion` 0..250) | one hit on the medium tank (`bullet` 5000@99 / `explosion` 250@50 / `electricity` −1@100) — the channel that reacts is the answer |
| U-5 | **which `EMP_Burst_Stage_0N` plays at which power level**, and the intra-frame order | re-walk the 4-item `FireParticle`/`EMPFireSwitch` arrays @2440/@2472 in `Playable_Batmobile_SF.upk` |
| U-6 | whether a **material instance** (`MAT_Flat_Shockwave_INST_BLUE` brightness 10) is writable in this build | material-instance writer status — no `.mat` writer in `Tools/scripts/` today; the `.effc` colour covers the visible half |
| U-7 | what `emp_flatbed_table`'s **30-byte entries** contain (72 objects) | `jc3adf.py` dump of the table object + `FX.md` member paths; until then only the pointer is set |
| U-8 | the **impulse** unit and whether a `CForcePulse` carries one | `FORCEPULSE.json` member table (the 8 tune fields have no impulse) |
| U-9 | the **fired** missile's scalars (`_ForCars` serialises none) | `T_WP4D` §1/§3 + `jc3weapons.py` on the fired projectile; probe P-M1 |
| U-10 | whether `MissileLockOnDuration` **2.0 s** has any JC3 carrier | `AutoAim` is 22 members, **0 durations** (`lock-hold-and-salvo-carrier.md`); probe P-M1's impact time only |
| U-11 | the target-side particle (`RVehicleNPC.ParticlesEMP`, export 11281) | decode that export's tag payload → object path → `PARTICLES.json`; probe P-V4 |
| U-12 | whether the heavy tank is disabled at all | `RVehicleHeavyTank.EMPIneffectiveLine` (129218) payload + a verified trace of 129436; probe P-T1 |
| U-13 | whether the pulse alone disables (the flag triple's meaning) | probe P-D2 (the only instrument — the flags are named nowhere) |

---

## 9. Sources

- `reports/emp-effects-scrape-leads.md` (and its `tmp/freebuff/reports/` copy) — A1–B5, the CDO values,
  §3 object graph, §6 UNKNOWNs.
- `tmp/freebuff/reports/immobiliser-and-emp-trigger.md` — the five mechanisms, `truck_emp.ftune`,
  `is_disabled_by_emp` scan, `vehicle_common` stall constants, probes Q-EMP-1…4.
- `tmp/freebuff/reports/emp-visual-and-hit-plan.md` — stage emitter counts, sizes, lifetimes, colours,
  materials, the `explosion_emp_flatbed.effc` / `emp_active.effc` pairing.
- `tmp/freebuff/reports/immobilizer-vs-emp-missile.md` — the missile/lock/impact-sound facts.
- `tmp/freebuff/reports/apply-gadget-rows.md` — B-18/B-20 cards, the `CEMPWeapon` mounting gap.
- `tmp/freebuff/reports/afterburner-effects-audio-plan.md` §3–§4 — the `.effc` write path and the
  `Sound` GUID → bank EVTS → samples chain used for the audio leg.
- `Research/JC3Grab/EMP.md` §2/§3/§5/§6 — pulse members, tune values, flags, trigger/prompt, `w702`.
- `Research/JC3Grab/FORCEPULSE.md` §1/§4 — the 8 tune fields, their domains, the flag census.
- `Research/JC3Grab/FX.md`, `Working/Effects/EFFC_WRITER.md` — `.effc` vocabulary and writer proof.
- `Research/JC3Grab/JC3_HUD_WEAPONS.md` §6 — `weapon_id` → icon path; the 69-id set and the 614 gap.
- `Research/JC3Grab/WEAPON_WIRING.md` §1 — the four slot pointers and `id:00568A74`.
- `Research/BatmobileGrab/WEAPONS.md` §9/§10, `BMSDK_OFFSETS.json`, `PARTICLES.md`, `MATERIALS.md`.
- `Tools/scripts/effc_writer.py`, `jc3fx.py`, `jc3forcepulse.py`, `bm_entity.py`, `eetoc.py`.

## 10. What was checked, and the limits

Checked (offline, read-only): every BmAK number in §1 against the lead report's offsets and exports;
the five JC3 mechanisms against the immobiliser report's own measurements (1,941 entries / 3.98 GB,
0 literal, 0 hash; 289/160 control hits); the `.effc` writer's carry round-trip and its edit proof; the
pulse's 8 tune fields and their fleet domains; the icon set (206, 601–622; 614 absent) and the
`id:00568A74` slot; the `emp_flatbed_table` object count (72) and its opaque 30-byte entries.

Not done: no `.effc` written, no tune copied, no `.epe` edited, no bank read, no install, no launch.
Every "derived" number is arithmetic on a decoded BmAK value (D1–D10) and every JC3 value written is
either shipped (100 damage, 1/1 radius factors, 500 weapon damage, the flag triple) or a D-number.
No claim above is filled in from outside these files.
