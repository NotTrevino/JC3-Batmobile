# WPN-10 / T-WP10 + T-WP14 — the non-lethal riot mode: what JC3 can and cannot carry

Task: BmAK's cannon has a riot (non-lethal) mode (`RiotSuppressorLockOnAngle` 7.5 and the gel round
family). The ledger accepted JC3 lethality in T-WP14 (2026-10-28) because no non-lethal flag was
found. The decision is **not reopened here**; this report records the carrier facts so the choice can
be made on evidence. Search for rounds that incapacitate without killing (tasers, stun, knock-back
or ragdoll-only damage, Bavarium shock, water cannon, tranquiliser/bean-bag ammunition), list damage
type/member/values, and say what a private tune copy would need.

**Verdict.**

* **No non-lethal flag, stun state, ragdoll-only damage, taser, water cannon or tranquilliser
  member exists in any decoded JC3 weapon tune or module.** A word-boundary scan of
  `WEAPONS.md`, `WEAPON_WIRING.md` and `DAMAGE_MECHANISMS.md` returns **0** hits for
  `stun`, `taser`, `shock`, `tranq*`, `bean-bag`, `ragdoll`, `water cannon`, `non-lethal` and
  `incapacit*`; `VOCABULARY.md` returns only `electric`/`electricity` (the vehicle-armour channel).
  The 52 is the **module-type** count (`G2X.md:107`); the fleet uses **71 part damage types**
  (`PARTS.md:83`, `PARTS_TABLE.md:8`), and none is a "stun" type. The ledger's phrasing "52 damage
  types" therefore conflates the two counts; the absence conclusion is unchanged either way.
* **What a weapon tune does carry is `damage` and `impulse`, per side, with two scaling factors.**
  Every decoded bullet/missile tune has `base_tuning.damage`, `base_tuning.impulse`,
  `vehicle_damage_factor`, `object_damage_factor`, and an `ai_tuning` twin (`WEAPONS.md:84-112`,
  §10 table at 425-450). **Damage type is not in the tune at all** — JC3 types damage on the *part*
  (`PARTS_TABLE.jsonl` `dt`) and the health module, not on the weapon (`WEAPONS.md:431`). So a
  "non-lethal round" cannot be expressed as a damage type on the round; it can only be expressed as
  **damage numbers** (and knock-back).
* **The only decoded zero-damage impulse in the game is a pulse, not a bullet:**
  `gen_explosion_5m_nodamage.ftune` = **0 player damage / 0 AI damage / 5 m radius**, described as
  "push only", carried by 2 loose-cargo pulses (`FORCEPULSE.md` §3). Every bullet tune in the 22-weapon
  table has damage ≥ 1; the lowest (`w602`, `w605`, `w616` cannons) are **player damage 1 / AI 20**,
  i.e. low, not non-lethal.
* **The `electricity` channel exists, but only as vehicle armour, and no weapon maps to it.** The 8
  `VehicleDamage` channels are `bullet, bullet_heavy, explosion, impact, fire, melee, electricity,
  grapple_pull`; `electricity_armor` is an int32 at **0x34** and `electricity_armor_strength` a float
  at **0x38 = 100.0** (`0x42c80000`), with shipped rows `0@0` ×192 and `-1@100` ×41 (`ARMOR_STEP.md:180-181`,
  `DAMAGE_MODEL.md:20,46,246`). But "no file maps a weapon to a channel" (`DAMAGE_MODEL.md:20`), and
  what `-1 @ strength 100` does is `UNKNOWN` (three competing models, H0/H1/H2). An electric/taser
  round would therefore need a **code-side channel assignment**, not a tune member.
* **Closest carrier for the base riot mode:** a private bullet tune with `damage = 0` and a high
  `impulse` (+ `vehicle_impulse_factor` / `object_impulse_factor`), plus the BmAK gel VFX and the
  copied cadence/lock-angle values. The **mode toggle** (lethal ↔ riot) has no JC3 member: it would
  be a second weapon slot/entity, not a mode bit.
* **The decision stands unchanged:** because damage type is part-side and no non-lethal flag exists,
  a tune copy can produce a *low/zero-damage* round, but nothing in the data guarantees
  "incapacitates without killing". That guarantee is code/design, not a JC3 carrier — which is the
  fact T-WP14 was resolved on.

---

## 1. BmAK riot fields (the values to carry)

`Research/BatmobileGrab/WEAPONS.md` §8 (`RBatmobileCannon`, 5 objects / 4 packages, 280 field rows).
`Batmobile_Cannon_V2` has **67 fields, identical in all 4 instances (268 comparisons, 0
differences)**; `Batmobile_JokerCannon_V2` is a different 12-field object with its own numbers.

| field | offset | type | `Batmobile_Cannon_V2` (Batmobile, MK2, Funhouse, Joker) | `Batmobile_JokerCannon_V2` |
|---|---|---:|---|---|
| `RiotSuppressorImpactEffect` | 0x0988 | ref | `Riot_Suppressor.Anti_firearm_gel_Miss` | — |
| `RiotSuppressorTracerSystem` | 0x0998 | ref | `Particles.Batmobile_RiotSuppressor_Tracer` | — |
| `RiotSuppressorShell` | 0x09B0 | ref | `Particles.RiotSuppressor_BulletCasing` | — |
| `RiotSuppressorIndividualFireEvent` | 0x09B8 | ref | `Engine.Play_RiotSuppressor_Bolt` — **missing-object** | — |
| `RiotSuppressorHitSound` | 0x09C0 | ref | `Engine.Play_RiotSupressor_Impacts` — **missing-object** | — |
| `RiotSuppressorLockOnAngle` | 0x0AAC | float | **7.5** | **9.0** |
| `RiotSuppressorRange` | 0x0AB0 | float | not serialised on this object (class default) | **8000.0** |
| `RiotSuppressorFiringInterval` | 0x0AB4 | float | **0.75** | **0.3330000042915344** |
| `RiotSuppressorVillainImpulse` | 0x0AB8 | float | **6000.0** | **1500.0** |
| `RiotSuppressorFireScreenShake` | 0x0ABC | struct 112 B | 0.25; [-20,0,0]; [7,0,0]; [300,0,0]; [2,2,2]; AdvancedOptions true; 0x0090 true | — |
| `RiotSuppressorShellsSocket` | 0x0B8C | name | `"RiotSuppressorShells"` | — |
| `ChainGunDamage` | 0x0B64 | int | **40** (upgraded 50) | **999** |
| `ImpactMomentum` | 0x0A68 | float | **60000.0** | **2000.0** |
| `RecoilImpulse` | 0x0A6C | float | **400.0** | — |
| `RVehicleWeapon.LethalRange` / `LethalRadius` | 0x0900 / 0x08FC | float | **12000.0 / 175.0** (shared `RVehicleWeapon` defaults; not riot-specific) | — |

Two facts the fields themselves show:

* The riot round is a **gel projectile** (`Anti_firearm_gel_Miss`), i.e. a non-penetrating impact
  effect, not an electric or gas round. There is no `RiotSuppressorDamage` member: the riot mode has
  **cadence, cone, range, impulse and VFX**, but **no damage number of its own** — the cannon's
  `ChainGunDamage` 40 is the only damage value on the object.
* Both riot **sounds** are `missing-object` in the grab, so the audio half of the mode is not in the
  files (the VFX half is: all three ParticleSystems resolve).

T-WP10/T-WP14 record the decision: `T7_WEAPONS.md:64` ("no non-lethal flag, damage type or weapon
mode exists in the 52-type / 1,421-path vocabulary … resolved 2026-10-28 (user): accept JC3
lethality, no toggle"), `T7_WEAPONS.md:85,89`, `COMPROMISES_T.md:120-121`,
`LEDGER_AUDIT.md:209,213`.

---

## 2. What JC3 weapon tunes actually carry (damage, impulse, no type)

`Research/JC3Grab/WEAPONS.md` §3 (lines 84-112), §10 (425-450).

| member | where | range / values |
|---|---|---|
| `base_tuning.damage` | `<block>[i].tuning` and `ai_tuning` | 1 … 3000 (player), 0 … 1000 (AI) |
| `base_tuning.impulse` | same | bullet player **0 … 100**, AI **0 … 40**; missile **350** player, **10** AI |
| `vehicle_damage_factor` | same | bullet **0.1 … 5**, missile **1**; AI **0.15 … 10** |
| `object_damage_factor` | same | bullet **0 … 1**, missile **1**; AI **0 … 1** |
| `vehicle_impulse_factor` | same | **0.2 … 1** (player), **0.2 … 1** (AI) |
| `object_impulse_factor` | same | **0 … 1** |
| damage type | **not in the tune** | no member matches `damage.?type`; damage is typed on the part (`PARTS_TABLE.jsonl` `dt`) and the health module |
| stun / ragdoll / incapacity | **absent** | 0 word-boundary hits in `WEAPONS.md`, `WEAPON_WIRING.md`, `DAMAGE_MECHANISMS.md` |
| water cannon / tranq / bean-bag | **absent** | same scan, 0 hits |
| electricity (as a weapon property) | **absent** | the only `electricity` names are the armour channel hashes (`ARMOR_STEP.md:68-69`) and its bytes (`ARMOR_STEP.md:180-181`) |

Per-weapon values (excerpt, `WEAPONS.md:86-110`):

| weapon | block | player dmg | veh × | obj × | player impulse | AI dmg | AI impulse |
|---|---|---:|---:|---:|---:|---:|---:|
| `w602_mediumtank_canon` | bullet | 1 | 1 | 1 | 0 | 20 | 0 |
| `w603_mediumtank_mgun` | bullet | 190 | 0.3 | 1 | 60 | 20 | 20 |
| `w604_helicopter_mgun` | bullet | 250 | 0.1 | 0.75 | 100 | 15 | 40 |
| `w605_smalltank_canon` | bullet | 1 | 5 | 1 | 0 | 15 | 0 |
| `w610_fighterjet_mgun` | bullet | 150 | 1 | 1 | 100 | 15 | 40 |
| `w616_corvette_canon` | bullet | 1 | 1 | 1 | 0 | 20 | 0 |
| `w618_sportsmuscle_missile` | missile | 1500 | 1 | 1 | 350 | 30 | 10 |

So the closest thing to a "riot" bullet in the shipped table is a **damage = 1, impulse = 0** tank
cannon — low damage, no knock-back, still lethal by accumulation. There is no shipped round with
`damage = 0` and a high impulse.

---

## 3. The electrical / knock-back / zero-damage candidates, one by one

| candidate | what the data has | values | verdict |
|---|---|---|---|
| taser / stun gun | **nothing** — 0 tune paths (`WEAPONS.jsonl` path scan for stun/taser/shock/water/tranq/bean/riot = 0), 0 member names | — | no carrier |
| `electricity` damage | a vehicle armour channel only; no weapon→channel map | `electricity_armor` int32 @0x34, `electricity_armor_strength` float @0x38 = **100.0**; rows `0@0` ×192, `-1@100` ×41 | channel exists, **unreachable from a tune**; what the gate does is `UNKNOWN` (H0/H1/H2) |
| Bavarium shock | no weapon tune named bavarium; `bavarium` appears in FX/vehicle contexts, not ammunition | — | no carrier |
| water cannon | no `water` member in `WEAPONS.md` at all; water modules are vehicle buoyancy | — | no carrier |
| tranquiliser / bean-bag | no tune, no member; the nearest word in the corpus is BmAK's **gel** impact VFX | — | no JC3 carrier; BmAK side has only VFX |
| knock-back without damage | `WeaponTuning.base_tuning.impulse` + the two impulse factors; **and** a zero-damage pulse tune `gen_explosion_5m_nodamage.ftune` (**0/0 damage, 5 m**, "push only", 2 pulses on the loose-cargo oldtruck) | bullet impulse 0–100, missile 350; vehicle factor 0.2–1, object 0–1; pulse: 0 damage / 5 m | **closest decoded carrier**, but it is a pulse (explosion object), not a bullet round |
| ragdoll-only | no `ragdoll` member in any decoded module; `DAMAGE_MECHANISMS.md` covers vehicle health/armour, not NPC ragdoll state | — | `UNKNOWN` / absent |
| per-weapon mode toggle | none — the tune has no mode/enabled/lethal member | — | absent (the T-WP14 decision) |

**Measured absence, so it is not re-searched:** `for f in WEAPONS.md WEAPON_WIRING.md
DAMAGE_MECHANISMS.md; grep -E '\bstun\b|taser|shock|tranq|bean.?bag|ragdoll|water.?cannon|non.?lethal|incapacit'`
→ **0 hits each**. `VOCABULARY.md` → only `electric` ×2, `electricity` ×2.

---

## 4. What a private tune copy would need

**Can be copied from BmAK (assets and numbers):**

1. **Gel impact and casing VFX** — `Riot_Suppressor.Anti_firearm_gel_Miss`,
   `Batmobile_RiotSuppressor_Tracer`, `RiotSuppressor_BulletCasing` (all resolve in
   `Playable_Batmobile_SF`, `objects.jsonl`).
2. **Cadence and cone** — `FiringInterval 0.75` → JC3 `fire_rate` (seconds per shot);
   `LockOnAngle 7.5` → the autoaim members `AngleThresholdNewTarget` /
   `AngleThresholdCurrentTarget` / `StickyAimStartAngle` (`WEAPONS.md:441`);
   `Range 8000` → `MaxAimDistance` / `AlwaysTargetDistance` where the tune has them (Cannon_V2 does
   not serialise a riot range; the Joker cannon's 8000 is the only value).
3. **Knock-back** — `VillainImpulse 6000` and `ImpactMomentum 60000` can be expressed as
   `base_tuning.impulse` + `vehicle_impulse_factor` / `object_impulse_factor` (factors clamp to 1,
   so the absolute impulse value is the lever).
4. **No damage number of its own** — the riot mode inherits the cannon's `ChainGunDamage 40`
   (`UpgradedDamage 50`). To make it non-lethal in data, set the tune's `damage` to 0.

**Cannot be copied / must be built:**

5. **A "non-lethal" property.** Damage is typed on the *part* (71 damage types) and gated by the
   vehicle health module's 8 channels; a weapon has no damage type. Setting `damage = 0` removes
   damage but is not a lethality flag, and no shipped bullet tune proves the engine honours 0 (only
   the pulse tune carries 0). **UNKNOWN** whether a 0-damage bullet still applies impulse and still
   triggers hit reactions.
6. **The mode toggle.** No member switches a weapon between lethal and riot. It must be a second
   weapon slot/entity (or script), not a tune field — exactly the T-WP14 finding.
7. **A stun/incapacitate effect.** No stun state, ragdoll trigger or "downed" member exists in the
   decoded vocabulary; NPC health/incapacitation is outside the decoded vehicle damage model, so
   even the target-side response is `UNKNOWN`.
8. **The riot sounds.** `Play_RiotSuppressor_Bolt` and `Play_RiotSupressor_Impacts` are
   `missing-object` in the grab; they are not importable from the files we hold.

A minimal private-tune experiment (one variable, cheap): copy a bullet tune, set
`base_tuning.damage = 0`, keep `impulse` at the donor's value, fire at a pedestrian and a car, and
observe (a) whether HP drops, (b) whether the target is pushed. That single test settles whether
"zero damage + impulse" is a viable base for the mode — the only thing data can decide here.

---

## 5. Mapping table — BmAK riot field → JC3 member → gap

| BmAK field (value) | nearest JC3 member | can carry? | gap |
|---|---|---|---|
| `RiotSuppressorFiringInterval` **0.75** | `fire_rate` (seconds per shot) | yes | direct |
| `RiotSuppressorLockOnAngle` **7.5** | `AngleThresholdNewTarget` / `AngleThresholdCurrentTarget` / `StickyAimStartAngle` | yes (semantics per member unproven) | which threshold matches BmAK's cone is `UNKNOWN` |
| `RiotSuppressorRange` **8000.0** (Joker only) | `MaxAimDistance` / `AlwaysTargetDistance` | partly | Cannon_V2 does not serialise a riot range; no JC3 "riot range" concept |
| `RiotSuppressorVillainImpulse` **6000.0** | `base_tuning.impulse` (+ `vehicle/object_impulse_factor`) | yes as a number | impulse is per-hit, and factors clamp at 1; "villain only" has no JC3 member |
| `ImpactMomentum` **60000.0** | same impulse family | yes as a number | unit/meaning `UNKNOWN` |
| `ChainGunDamage` **40** / `UpgradedDamage` **50** | `base_tuning.damage` | yes | a 0 value is unproven for bullets (only pulses ship 0) |
| `RiotSuppressorImpactEffect` → gel `Anti_firearm_gel_Miss` | none (JC3 effect is an `.effc`/particle asset, no weapon member) | asset only | must be attached by the entity/effect side |
| `RiotSuppressorTracerSystem` / `RiotSuppressorShell` | JC3 tracer/casing are `.effc` assets, not tune members | asset only | same |
| `RiotSuppressorIndividualFireEvent` / `HitSound` (**missing**) | no JC3 weapon sound member for these | no | missing in the grab |
| `RiotSuppressorFireScreenShake` (0.25; [-20,0,0]; [7,0,0]; [300,0,0]; [2,2,2]) | `.ctunec` `CameraShakeModifierParams` (class exists, fields undecoded) | system-level | values cannot be converted |
| *mode switch* | **none** | no | second slot/entity or script |
| *non-lethal guarantee* | **none** — damage typed on part, 8 channels, no weapon→channel map | no | code/design, not data |

---

## 6. Gap for the build (STAGES.md BUILD)

1. **If the decision is ever revisited:** the deliverable is a **second weapon entity** (riot
   variant) with `damage = 0`, high `impulse`, the copied cadence/cone, and the gel VFX attached —
   plus a script-side check that zero damage does not kill. That is a build, not a tune edit, because
   the toggle has no member.
2. **The honest data boundary:** JC3 cannot express "non-lethal" as a property. It can express "0
   damage" and "large impulse" separately; whether the combination reads as non-lethal is a Q-1
   gameplay test.
3. **The electrical route is closed without code:** `electricity_armor`/`_strength` are real (0x34 /
   0x38, 100.0), but no weapon maps to the channel and the gate's effect is one of three models.
   A taser-like round would need engine-side channel assignment, so it is not a tune-copy path.

---

## 7. UNKNOWNs (named, not filled)

- Whether a 0-damage bullet tune still applies impulse / hit reactions (only the 0-damage **pulse**
  is shipped).
- What `electricity_armor = -1 @ strength 100` does (H0/H1/H2, unresolved).
- Which JC3 autoaim member corresponds to BmAK's 7.5° lock cone.
- Meaning/unit of `ImpactMomentum` 60000 and `VillainImpulse` 6000 beyond "impulse-like".
- NPC stun/ragdoll/incapacitation state — outside the decoded vehicle damage model.
- The two missing riot sounds (not in the grab).

## Evidence index

- `Research/BatmobileGrab/WEAPONS.md:553-574` (riot field groups), `§8` 655-770 (all riot values and
  the Joker variant), 736-742 (resolved/missing refs), 926/1041 (`LethalRange`/`LethalRadius`).
- `Working/Translation/T7_WEAPONS.md:64,85,89,318-334` — D-3 decision, T-WP10 and T-WP14 rows;
  `COMPROMISES_T.md:120-121`; `LEDGER_AUDIT.md:209,213`.
- `Research/JC3Grab/WEAPONS.md:84-112` (damage/impulse table), `425-450` (member table, "damage type
  not in the tune"), `431` (part-side damage typing), `441` (autoaim members).
- `Research/JC3Grab/PARTS.md:83`; `PARTS_TABLE.md:8` — **71** damage types fleet-wide.
- `Research/JC3Grab/G2X.md:107,167` — the 52-type / 1,421-path module vocabulary and WPN-10 absence.
- `Research/JC3Grab/ARMOR_STEP.md:68-69,180-181`; `DAMAGE_MODEL.md:20,21,46,246` — `electricity_armor`
  @0x34, `electricity_armor_strength` @0x38 = 100.0; 8 channels; no weapon→channel map.
- `Research/JC3Grab/FORCEPULSE.md` §3 — `gen_explosion_5m_nodamage.ftune` 0 damage / 5 m, "push only".
- `Research/JC3Grab/DAMAGE_MECHANISMS.md` — vehicle health/armour lives in the module + entity root
  (`health` 100.0, `invulnerable` 0), not in weapons.
- Word-boundary scans over `WEAPONS.md`, `WEAPON_WIRING.md`, `DAMAGE_MECHANISMS.md` — 0 hits for
  stun/taser/shock/tranq/bean-bag/ragdoll/water-cannon/non-lethal/incapacitate.
