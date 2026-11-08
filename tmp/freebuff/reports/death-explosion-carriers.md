# Death explosion — the closest JC3 carriers for "0 HP = instant explosion, passengers die"

Card: `death-explosion-carriers`. 2026-11-08. **Report only.** No `.epe`, `.vmodc`, `.effc`, tune, bank, build
tree or ledger row is written; the four files this card quotes are byte-identical to `HEAD`.

Operator fact: **at health 0 the Batmobile explodes instantly — no warning smoke, no sparks — and the
occupants die.** `ROADMAP.md` §7 records the same ruling and adds the consequence: *"9171; drop the donor
smoke/burn stages (T-FX22/23 conflict)"*.

Labels: **decoded** = read at the named file:line/offset; **derived** = arithmetic shown; **operator** = the
2026-11-08 statement; **UNKNOWN** = absent from the named files, with what settles it.

## 0. The plan in five lines

1. **What fires at zero health:** `VehicleDamage.explosion_threshold` — a health gate, not a damage gate. The
   donor ships it equal to `max_health` (700/700), i.e. it fires at 0 % ; the build ships 4000 against
   `max_health` 2000, so today it **cannot** fire (`health-damage-states-plan.md` §3.2, §4).
2. **Instant, not delayed:** `VehicleDamage.explosion_delay_s` ships 5–10 s. Set **0**; that single member is
   the whole "no warning window" behaviour.
3. **No smoke, no burn:** the intermediate stages are three more members (`smoke_threshold` 1050,
   `burn_threshold` 250, `vulnerable_explosion_threshold` 100) **plus** five effect objects in the donor `.epe`
   (`damage_smoke`, `dynamic_burn_roof`, `damage_fire_left/right`, `engine_fire_drips`, `engine_fire_ground`).
   Zeroing the thresholds is not enough — the objects must be unbound, because the `.epe` usage map, not the
   module, decides what draws.
4. **BmAK particle:** `Batmobile_Explosion` (14 emitters, 0.1–5 s) → the donor's `exp_car_01.effc` container
   (126 vehicles), already the T-FX21 choice. **Sound:** `DeathExplosionSoundArray` (2 items, payload
   undecoded) + AkEvent `Play_Batmobile_Destroyed`, which is **missing-bank** in the install, so the build
   falls back to JC3's own blast tune and keeps the BmAK sounds as a bank-swap card (B-26).
5. **Passenger kill:** **no JC3 member exists** (0 hits for `occupant`/`passenger`/`eject` in
   `Research/JC3Grab/VOCABULARY.md`). It is native engine behaviour (UNKNOWN by file) or the native hook; no
   data route.

---

## 1. The BmAK death chain, member by member (decoded)

| # | member | offset | value / reference | what it does at 0 HP | source |
|---|---|---|---|---|---|
| 1 | `Pawn.Health` | — | **1200** on all three Batmobile archetypes | the pool that reaches 0 | `DAMAGE_RULES.md` §4; `health-damage-states-plan.md` §1.1 |
| 2 | `RVehicleBatmobileBase.DeathExplosion` | 5564 (`0x15BC`) | **`Impacts.Batmobile_Explosion`** (`ParticleSystem`) | the death particle | `COLLISION_WHERE.md:84`; `health-damage-states-plan.md` §2 stage 6 |
| 3 | `RVehicleBatmobile.DeathExplosionSoundArray` | 0x1D08 | **`ArrayProperty`, 2 items**, payload stream-only | the two death sounds | `MECHANICS.md:13`; `DAMAGE_RULES.md:571,598,624,651` |
| 4 | (AkEvent) `Play_Batmobile_Destroyed` | — | 4 references, **`missing-bank`** in the install | the destroy sting | `AUDIO_FEATURES.md:152`, `:731` |
| 5 | `RVehicleBatmobileBase.DeadBatmobileArchetype` | 5556 (`0x15B4`) | **`DeadVehicle.Dead_Batmobile`** (`RDeadVehicle`) | the wreck the car becomes | `COLLISION_WHERE.md:83` |
| 6 | `RVehicleBatmobileBase.BatmobileOnFireMeshComp` | 5684 (`0x1634`) | `Batmobile.BatmobileOnFireMeshComp0` (`SkeletalMeshComponent`) | the burning mesh — **post-death wreck state, not a warning state** | `COLLISION_WHERE.md:85` |
| 7 | `BatmobileOnFireDamageRadiusScale` | 8128 | **0.005** | the radius scale of that burning wreck | `CLASS_DEFAULTS.md` row 145 |
| 8 | `ArmourLevels` | 8108 | `[0, 300, 600, 900, 1200]` | 5 bands; **cosmetic/HUD only** — no smoke, no sparks | `CLASS_DEFAULTS.md` row 143 |
| 9 | `LowHealthWarningLevel` | 8124 | **300** | the low-health *warning message*, not a flame | `CLASS_DEFAULTS.md` row 144 |
| 10 | `DamageLevel` (`SetDamageLevel`) | — | param only, **threshold table UNKNOWN** | cosmetic material stages | `FOOTAGE.md:158` |

**The particle itself** (`PARTICLES_FEATURES.md`, `explosion` group) — `Batmobile_Explosion`:
**4 rows, 14 emitters** (light ×1, mesh ×3, sprite ×10), lifetime **0.1…5 s**, spawn **0…2000/s**,
sizes 0.1 → 25000, materials `Engine.DefaultParticle` + `Engine.GPU_spark_M`. Referenced by
`objects.jsonl (RVehicleBatmobile)` — i.e. exactly the object behind member #2. Two siblings exist for the
missile family (`Batmobil_Rocket_Explosion`, `…_Small`) and are **not** the vehicle death effect.

**Why the operator sees no warning stages.** The BmAK damage staging that the files prove is five 25 % bands
(`ArmourLevels`), a *generator steam/overheat* state (`DrainWeaponGeneratorForDamage` → `IncSteamEffect`,
`OverHeat`), an on-fire mesh, and the death/wreck state (`health-damage-states-plan.md` §2). **None of the
file-provable stages is a smoke plume or a spark shower on the car body before death** — the steam comes from
the weapon generator, and the fire state is the burning *wreck*. So the operator's "no warning smoke or
sparks" agrees with the record; the disagreement is entirely on the JC3 side, whose donor has a
smoke→burn→explode ladder.

---

## 2. JC3: which slot actually fires at zero health

There are **two** death paths in JC3 and only one of them is available to a `CCar`:

### 2.1 The one that works: the `VehicleDamage` health gate

| member | donor value | build value (test-091) | meaning | source |
|---|---:|---:|---|---|
| `VehicleDamage.max_health` | 700 | 2000 | the pool | `DAMAGE_MODEL.md` §2 |
| `VehicleDamage.explosion_threshold` | **700** | **4000** | fires when remaining health ≤ this; donor = 100 % of max | `health-damage-states-plan.md` §3.2, §4 |
| `VehicleDamage.explosion_delay_s` | 5–10 | (per build) | **seconds between the gate and the bang** | same §3.2 |
| `VehicleDamage.vulnerable_explosion_threshold` | 35 | 100 | the "vulnerable" sub-state | same |
| `VehicleDamage.burn_threshold` | 80 | 250 | fire stage | same |
| `VehicleDamage.smoke_threshold` | 200 | 1050 | smoke stage | same |
| `VehicleDamage.burn_duration_s` | 20 | 20 | how long the fire lasts | same |

So at 0 HP the **trigger** is `explosion_threshold`, and the visible explosion is whatever the module's effect
list binds to the death usage. Two readings of the threshold are still open (`health-damage-states-plan.md`
§4: *health remaining* vs *per-hit damage*); only the first is coherent with `smoke > burn`, and the plan says
so. Under either reading, `explosion_threshold` **is** the zero-health slot — it is the only member whose name
says "explode".

### 2.2 The one that is not available: the `OnExploded` usage

`Research/JC3Grab/USAGES.md` §2 lists the whole named vocabulary (12 names, 346 rows). `OnExploded`
(hash **3587098424**) exists — on **two vehicles only**, both
`v4800_plane_brothers_vintagefighter`, binding effect `engine_break`. The Batmobile donor
(`v0300_car_kensington_sportsmuscle_civilian_01.ee`) is **not** one of them.

The nearest car-side usages in the donor's own `.epe` (USAGES.md, "The donor's own attachments"):

| usage uint32 | name | objects carrying it |
|---:|---|---|
| 1666327646 | **UNKNOWN** | **`fire_post_explosion`** |
| 1752342301 | `burn_roof` (module effect name) | `dynamic_burn_roof` |
| 1181737112 | UNKNOWN | `damage_fire_left`, `damage_fire_right`, `engine_fire_drips`, `engine_fire_ground` |
| 102641159 | `EngineSmoking` (module usage name) | `damage_smoke` |
| 456657646 | UNKNOWN | `flame` |

`fire_post_explosion` is the donor's **post-explosion** object and its usage hash has **no name in any decoded
file** (86 of the 155 `.epe` usage values are unnamed, G2-22 §UNKNOWNs). That is the honest state of the death
binding on the car: the object exists, the hash is not named, so no file proves "this is the death trigger".

### 2.3 What is decoded about the car's death effect

- `effects/jc_vehicles/damage/exp_car_01.effc` — **126 vehicles**, 34,895 B, 759 arrays, 6,891 rows; the donor
  `.ee` embeds it (T-FX21, `FX_TABLE.jsonl`; 18 donor rows across its three containers). This is the car
  explosion container the fleet uses.
- `T-FX21.why` (the ledger's own words): *"death explosion = the donor's `exp_car_01` (126 vehicles) under
  `OnExploded` (G2-22) plus the blast tune (G2-10)"*. **That attribution is wrong for the car** and is
  corrected here: `OnExploded` is the vintage-fighter usage; `exp_car_01` reaches the car through the
  `VehicleDamage` effect list, not through `OnExploded`. Kept as a contradiction, not silently edited
  (the ledger row is owned by T-13/B-24).
- The `.epe` `SAttachedEffect` shape (from the shell-casing work, `T13_FX.md` §5 T-FX13): `Effect` = Jenkins
  hash of the `.effc` **name**, `Usage` = uint32, `name_hash`, optional `world` flag. That is the object type
  to author or re-point, and the reason an effect can exist in the graph without a named trigger.

---

## 3. Removing the intermediate smoke/burn stages

Two layers, and both are needed: **the module thresholds** decide *when*, **the `.epe` usage objects** decide
*what*. Unbinding the objects is what actually removes the visuals, because the smoke/fire the donor draws is
attached at usage level, not by the thresholds alone.

### 3.1 Module layer (`lave_health_medium.vmodc`, the private copy)

| member | donor | to | why |
|---|---:|---:|---|
| `explosion_threshold` | 700 | **= `max_health`** (e.g. 2000) | fires at 0 % , i.e. exactly at death |
| `explosion_delay_s` | 5–10 | **0** | removes the delay window (the "warning" the operator says does not exist) |
| `smoke_threshold` | 200 | **0** | 0 is the only value that cannot fire before death (`uint16`, no negatives) |
| `burn_threshold` | 80 | **0** | same |
| `burn_duration_s` | 20 | **0** | no burn window even if a threshold raced the explosion |
| `vulnerable_explosion_threshold` | 35 | **0** | no "vulnerable" sub-state |
| `vulnerable_duration_s` | 5 | **0** | same |
| `deform_scale` | 1 | **0** (already 0 in the build) | no crumple — BmAK has no panel deformation (`RVisualDamageComponent` decodes nothing) |
| `impact_damage_factor` | 1–12 | **0** (already 0, T-DM8) | ramming never damages the car |
| `fire_spreading_speed_ms` | 1.5 | keep | inert once `burn_threshold` is 0 |

Caveat that must be stated before the build: `smoke_threshold`/`burn_threshold` are `uint16`
(`health-damage-states-plan.md` §3.2). If the engine reads them as *per-hit damage* rather than *health
remaining*, 0 means "a hit of 0 damage triggers smoke" — harmless in practice, but it is a probe, not a proof.

### 3.2 Entity layer (the private `.epe`)

Unbind (null the `Effect` ref, or delete the object) the five donor objects that paint the stages:

| object in the donor `.epe` | usage | what it draws | action |
|---:|---|---|---|
| `damage_smoke` | 102641159 `EngineSmoking` | the engine smoke plume | **remove** |
| `dynamic_burn_roof` | 1752342301 `burn_roof` | roof fire | **remove** |
| `damage_fire_left`, `damage_fire_right` | 1181737112 (unnamed) | body fire | **remove** |
| `engine_fire_drips`, `engine_fire_ground` | 1181737112 (unnamed) | fire drips / ground fire | **remove** |
| `flame` | 456657646 (unnamed) | residual flame | **remove** |
| `fire_post_explosion` | 1666327646 (unnamed) | **post-explosion burn** | **keep** — this is the wreck, not a warning stage |
| `dynamic_break_*`, `dynamic_trail_*`, `dynamic_headlight` | part usages | part break / lights | optional: keep (part events, not health stages) |

Because deleting objects changes the `.epe` object table, the safe order is **null the `Effect` field first**
(4 B / 8 B ref → 0 or a null object id), verify the graph still loads, then delete. `jc3_damage_search.py
--epe <file>` prints `health` / `invulnerable` / `damage` triples for the file, so it doubles as the
"graph still parses" check; `bm_entity.py --check` is the fuller gate.

### 3.3 The ledger conflict this creates (kept, not edited)

`T13_FX.md` §2 keeps both rows and their `why` lines unchanged:

- **T-FX22** (`dmg_fire_engine` / `_spread_base` / `_spread_roof`, 192 vehicles) — "burn states = the donor's
  … family under the damage-state usage", disposition `epe`.
- **T-FX23** (`dmg_smoke_engine`, 23 vehicles → `dmg_post_burn`, 139 vehicles) — "engine smoke … then
  `dmg_post_burn`", disposition `epe`.

Both are correct as *descriptions of the donor* and both are **wrong as build instructions for the Batmobile**:
the operator's death has no intermediate stages, so on this vehicle those rows must end as **explosion-only**,
with T-FX22 and T-FX23 recorded as "carried by the donor, deliberately unbound on the mod" — i.e. the rows move
from `keep` to a named build deviation, not to `out` (JC3 *can* express them; the lore does not want them).
`ROADMAP.md` §8/§7 already flags this as the "T-FX22/23 conflict". **This report does not change either row** —
that is a TRANSLATE decision on T-13.

---

## 4. Which BmAK particle and sound go in

| slot | BmAK | JC3 carrier | action | status |
|---|---|---|---|---|
| death particle | `Batmobile_Explosion` — 4 rows, 14 emitters, 0.1–5 s, 0–2000/s, `Engine.DefaultParticle` + `Engine.GPU_spark_M` | `effects/jc_vehicles/damage/exp_car_01.effc` (126 vehicles, 34,895 B, 759 arrays) | keep the shipped container (T-FX21) and, only if the look needs it, author a private copy: `EmitterTemplates[i].MaxParticles` and `Instantiators[i].RenderBlockData[]` are the writable fields (`effc_writer.py` proven for in-place patches) | particle **decoded**, carrier **decoded**, growth **not** proven (B-17) |
| death sound ×2 | `DeathExplosionSoundArray` @0x1D08, **2 items** | — | payload is **stream-only**: `DAMAGE_RULES.md` records the array as `—`/stream at all four archetypes, `MECHANICS.md:13` gives only `2 items`. The two AkEvent names are **UNKNOWN** | **UNKNOWN** |
| destroy sting | AkEvent `Play_Batmobile_Destroyed` (4 refs) | — | **`missing-bank`** in the install (`AUDIO_FEATURES.md:152`) — the event is named but its bank is absent, so it cannot be copied | **blocked (bank)** |
| fallback while those are open | — | JC3's own vehicle blast: `Engine.Play_Explosion_3D` (4 refs, on `Batmobile_JokerMissile_Projectile`, `Batmobile_Missile_Projectile`) and the blast tune `car_explosion_medium` (G2-10 §8) | use these as the placeholder; they are the fleet's own explosion audio and need no bank work | **decoded** |

The bank route for the two BmAK sounds is **B-26** (private banks, `AUDIO_BANKS.md` / `AUDIO_BANKS2.md`): the
array payload has to be decoded first (one `.uasset` read of `RVehicleBatmobile.DeathExplosionSoundArray`), and
`Play_Batmobile_Destroyed` has to be located in a shipped `.bnk` before it can be swapped — today it is
`missing-bank`, i.e. the name resolves but no bank in the install carries it.

---

## 5. The passenger-kill path

| side | member | exists? | evidence |
|---|---|---|---|
| JC3 | `occupant` / `passenger` / `eject_occupants` / `kill_occupants` | **no** | `grep -n "occupant" Research/JC3Grab/VOCABULARY.md` → 0 hits; the only related name is `DriverLean` (an animation) at `VOCABULARY.md:550` |
| JC3 | vehicle-destruction → occupant death | **native**, UNKNOWN by file | no data member names it; the `.epe` object set (`RVehicleBatmobile`-equivalent `CCar` root) has no occupant reference in the 233 decoded roots (`DAMAGE_MECHANISMS.md` §1 lists `health`, `invulnerable`, `damage` only) |
| BmAK | explicit "kill passengers" member | **no** | the death path is the wreck archetype (`DeadVehicle.Dead_Batmobile`) plus `DeathExplosion`; no occupant member is in the 423 named fields (`OFFSETS.json`) |

So the honest answer is: **the passengers die because the vehicle is destroyed, and that is engine behaviour on
both sides** — no member to translate. Two routes, in order of preference:

1. **Native (moot, likely already true).** If JC3's own vehicle destruction kills the driver, nothing is
   needed; the probe below confirms it. This is the expected case: JC3 cars at 0 HP eject/kill the occupant
   without a data member naming it.
2. **Native hook** (permitted 2026-11-08, `ROADMAP.md` §5b). The hook can call the vehicle's destroy/occupant
   routine at the moment `health` hits 0 if route 1 fails. This is the only fallback, because no graph or
   module member exists to author.

**Probe `Q-DEATH-1`** (needs `APPROVED_Q.txt`): drive the mod car to 0 HP with Rico inside, at a standstill
and at speed. Pass = the car is gone in one frame (no smoke/fire frame between full health and the explosion)
and Rico is dead or displaced; fail = any intermediate frame, or Rico still driving the burning wreck.

**Probe `Q-DEATH-2`**: same, with the wreck visible for 5 s after the bang. Pass = the wreck is the
`DeadVehicle`-equivalent (a burnt shell), no flames licking the body, no smoke plume from the engine bay.

---

## 6. Build order, offline checks, revert

| step | file | change | check |
|---|---|---|---|
| 1 | private `lave_health_medium.vmodc` | §3.1 table: `explosion_threshold` = `max_health`, `explosion_delay_s` 0, `smoke_threshold` 0, `burn_threshold` 0, `burn_duration_s` 0, `vulnerable_*` 0, `deform_scale` 0 | `t_damage`/`jc3damage` decode of the copy shows the new values; tamper 1 value and confirm the checker fails |
| 2 | private `.epe` | null the `Effect` ref of `damage_smoke`, `dynamic_burn_roof`, `damage_fire_left/right`, `engine_fire_drips`, `engine_fire_ground`, `flame`; keep `fire_post_explosion` | `jc3_damage_search.py --epe` still prints the `health`/`invulnerable`/`damage` triple; `bm_entity.py --check` shows no dangling object ids |
| 3 | private `.epe` | keep the death particle binding (`exp_car_01` via the module effect list); no growth | `FX_TABLE`-style re-read lists `exp_car_01` once, and the removed objects are gone |
| 4 | audio | use JC3's `Play_Explosion_3D` + `car_explosion_medium` as the placeholder | the two BmAK events stay UNKNOWN/missing-bank; B-26 owns them |
| 5 | probe | `Q-DEATH-1`, `Q-DEATH-2` | operator-gated |

**Revert:** every step is a copy in a private `Builds/` tree; restoring the previous tree restores the donor
behaviour (smoke → burn → delayed explosion). Nothing here edits a game install.

---

## 7. Contradictions kept on the record

| # | item | record says | operator says | kept as |
|---|---|---|---|---|
| C1 | intermediate stages | T-FX22/T-FX23 `keep` (donor's smoke/burn families on 192 / 139 vehicles) | none exist before death | **both kept**; §3.3 says which wins for this build and that the rows belong to T-13 |
| C2 | the death usage | `T-FX21.why` says `exp_car_01` is under `OnExploded` | — | **corrected here**: `OnExploded` is on 2 vintage fighters only; the car's death effect comes from the module list. The ledger row is not edited |
| C3 | BmAK on-fire mesh | `BatmobileOnFireMeshComp0` exists as a component + `BatmobileOnFireDamageRadiusScale` 0.005 | no fire before death, explosion at 0 | **agree**, provided the mesh is read as the *wreck* state — the boundary (`SetBatmobileOnFire`) is UNKNOWN, which is why C1 needs the probe |
| C4 | death sound | `DeathExplosionSoundArray` 2 items, `Play_Batmobile_Destroyed` named | a single instant bang | **UNKNOWN**: 2 items could be a bang + a tail; the payload is undecoded |
| C5 | the trigger value | build `explosion_threshold` 4000 vs `max_health` 2000 (200 %) | explodes at 0 | **build is wrong today**: under the "health remaining" reading 4000 can never be reached, so the car would die *silently* — this is the single highest-value fix in this card |

## 8. UNKNOWNs, each with what settles it

| # | unknown | settles it |
|---|---|---|
| U1 | the two `DeathExplosionSoundArray` AkEvents | one `.uasset` read of `RVehicleBatmobile` (0x1D08, 2 items × 8 B) |
| U2 | whether `smoke_threshold`/`burn_threshold` are health-remaining or per-hit damage | `Q-DEATH-2` (a 0-threshold build shows whether anything ignites), or the `TakeDamage` consumer in the exe |
| U3 | the usage hash 1666327646 behind `fire_post_explosion` | no decoded string carries it (G2-22 UNKNOWNs); a hash-dictionary extension or the exe |
| U4 | whether a `CCar` destruction kills the occupant natively | `Q-DEATH-1` |
| U5 | `SetBatmobileOnFire`'s health boundary | bytecode trace of `TakeDamage`'s caller (the audit lists it as an unresolved name) |
| U6 | whether `.effc` growth (adding an emitter) is safe | B-17's last step (`effc-format-writable.md` §4/§6) |

## 9. Reproduce

```bash
cd /e/Modding/JC3-Batmobile
sed -n '10,16p' Research/BatmobileGrab/MECHANICS.md            # DeathExplosionSoundArray 2 items @0x1D08
sed -n '570,575p' Research/BatmobileGrab/DAMAGE_RULES.md        # the array is stream-only, per archetype
sed -n '150,154p;728,733p' Research/BatmobileGrab/AUDIO_FEATURES.md   # Play_Batmobile_Destroyed: missing-bank
grep -n "Batmobile_Explosion" Research/BatmobileGrab/PARTICLES_FEATURES.md
grep -n "OnExploded\|EngineSmoking" Research/JC3Grab/USAGES.md  # 3587098424 (2 vehicles), 102641159 (23)
grep -n "fire_post_explosion\|damage_smoke\|dynamic_burn_roof" Research/JC3Grab/USAGES.md
python -c "import json;[print(r['id'],r['dispo']) for r in map(json.loads,open('Working/Translation/T_ROWS.jsonl')) if r['id'] in ('T-FX21','T-FX22','T-FX23')]"
```
