# Health to explosion — no crash damage, no wreck, occupants die

**Scope.** The operator's 2026-11-08 player facts, turned into the smallest JC3 change set:

> The Batmobile has **no visible damage stages**. Crashes never damage, scratch or dent it. Its
> health bar falls to zero from **weapon** damage, and then it **explodes violently and kills the
> passengers**. It does **not** remain as a wreck you keep driving.

Written against `reports/health-damage-states-plan.md` (the HP model and the fraction mapping) and
`reports/collision-impact-effects-plan.md` (the contact/impact side). Every number is read from a
file in this repository; anything the files do not carry is marked **UNKNOWN** with the file that
would settle it. No game file was modified — this is a plan.

**Evidence levels used below:** *decoded* (a value or member read out of a shipped file),
*derived* (arithmetic or geometry over decoded values), *UNKNOWN* (no evidence; settling file named).

**The one-paragraph answer.** Collision damage is already off in the build (`impact_damage_factor` 0
and `deform_scale` 0, `Builds/test-091`), and the constructor that matters — `impact_damage_factor`
— is a direct multiplier on collision damage, not an armour-channel gate, which is exactly why it is
the right switch: the armour channels are **not** a working exemption in this game
(`DAMAGE_MECHANISMS.md` line 3-5: the build already sits at the shipped maximum in every armour
channel and bullets still destroy the car). Weapon damage and the bar are therefore kept by *not*
touching `invulnerable`, `max_health` or the eight channels. The explosion at zero health is the
vehicle root's own `CForcePulse` (`car_explosion_medium.ftune`, 500 player damage in a 5 m radius) —
the blast that carries occupant damage — and "no wreck" is satisfied by JC3's own destruction
behaviour, because JC3 wrecks are **separate scenery entities**, not a drivable state of the car.

---

## 1. Evidence base

| source | what it gave |
|---|---|
| `Builds/test-091` via `Research/JC3Grab/DAMAGE_MODEL.md` §2 | the build's actual `VehicleDamage` values (the tank profile with impact/melee raised) |
| `Research/JC3Grab/DAMAGE_MODEL.md` §2, §7, §8 | fleet domains per channel; the three armour composition models (H0/H1/H2) |
| `Research/JC3Grab/DAMAGE_MECHANISMS.md` §1-§4 | root `health` 100.0 / `invulnerable` 0 on all 233 roots; **armour is not an exemption** |
| `Research/JC3Grab/ARMOR_STEP.md` §7 | `CVehicleDamageState` (12 vtable slots) — the health state object |
| `Research/JC3Grab/VOCABULARY.md` | the staging members and their fleet ranges (`smoke_threshold`, `burn_threshold`, `explosion_threshold`, `explosion_delay_s`, …) |
| `Research/JC3Grab/FORCEPULSE.md` §§2-3 | the vehicle root's blast, its tune, and the eight `ForcePulseSettings` numbers per tune |
| `Research/JC3Grab/USAGES.md` line 64 | `OnExploded` (effect usage, 2 vehicles, `engine_break`) |
| `Research/JC3Grab/STANDALONE.json`, `REBELDROP.md` line 142 | the `*_wreck.ee` entities — wrecks exist as scenery |
| `tmp/freebuff/reports/app-skins-and-variants.md` §6 item 6, §3 row 5 | BmAK's destroyed/fire meshes and what is known about their role |
| `tmp/freebuff/reports/collision-impact-effects-plan.md` §3 | BmAK has **no dent member and no deform asset** — "no scratch or dent" is fidelity, not an omission |

---

## 2. Step 1 — switch collision damage off on the Batmobile entity

### 2.1 The four carriers, and which one is the switch

| carrier | type | fleet domain | build (test-091) | role |
|---|---|---|---|---|
| `impact_damage_factor` | int | **1 … 12** | **0** | multiplier applied to impact (collision) damage |
| `deform_scale` | int | **1 … 2** | **0** | the crumple/deform scale; 0 = no deformation |
| `impact_armor` / `impact_armor_strength` | int32 / float32 | `impact_armor` **0 … 5**; strength **0 … 100** | **5000 @ 100** | per-type reduction channel |
| `melee_armor` / `melee_armor_strength` | int32 / float32 | both **0 … 0** (no vehicle in the fleet uses them) | **5000 @ 100** | the melee/shove channel |

Evidence: `VOCABULARY.md` rows for `VehicleDamage`; `DAMAGE_MODEL.md` §2 build-vs-donor-vs-tank
table; `DAMAGE_MODEL.md` §7 fleet pair census (`impact`: `0@0` x220, `5@100` x13).

**Why `impact_damage_factor` 0 is the switch and `impact_armor` 5000 is not.** `DAMAGE_MECHANISMS.md`
opens with the finding that killed T-DM9: *"the build already sits at the shipped maximum in every
armour channel and bullets still destroy the car."* Whatever the armour composition turns out to be
(H0 ignore / H1 percentage / H2 threshold+pool — `DAMAGE_MODEL.md` §6, still UNKNOWN), the observed
behaviour says the armour numbers **reduce** damage and do not exempt from it. `impact_damage_factor`
is not an armour channel: it is the module's own collision multiplier, the same member
`collision-impact-effects-plan.md` §4.1-§4.3 places on the ram path. Turning a multiplier to 0 is a
different kind of edit from raising a resistance, which is why it is the value to trust.

### 2.2 Values to write

| # | member | write | in the shipped domain? | evidence level |
|---|---|---:|---|---|
| CX-1 | `impact_damage_factor` | **0** | **no** (fleet 1…12) — an undeclared switch, label it | decoded member, **derived** effect |
| CX-2 | `deform_scale` | **0** | **no** (fleet 1…2) | decoded member, **derived** effect |
| CX-3 | `impact_armor` @ `impact_armor_strength` | **5000 @ 100** (already in the build) | `impact_armor` no (max 5), strength yes | decoded value, effect **UNKNOWN** (composition) |
| CX-4 | `melee_armor` @ `melee_armor_strength` | **5000 @ 100** (already in the build) | no (fleet is 0@0 everywhere) | decoded value, effect **UNKNOWN** |

CX-1 and CX-2 are already what the build ships, so **step 1 needs no new edit** — it needs the probe
that proves it. CX-3/CX-4 stay because they do no harm and removing them would be a second variable
in the same probe.

**The probe (one variable, no other edit).** Full-boost ram into a wall, then into traffic, three
times each, on `build_test-091`, health read before and after each hit (`jc3_damage_search.py --epe`
prints the triple; the HUD bar is the second read). **Take:** the bar does not move on any of the six
hits, the car does not dent, smoke or catch fire, and it is still drivable afterwards. A single point
of movement falsifies CX-1 and sends the plan to CX-3 (`impact_armor_strength` raised, or the
`CDamageControllerArmor` binder of `ARMOR_STEP.md` §3 if collision lands on a part).

### 2.3 What "no scratch and no dent" costs

Nothing. BmAK has **no dent**, no deformation and no debris member on `RVehicleBatmobileBase`
(`collision-impact-effects-plan.md` §3, U6 "no dent member, no dent asset"). The Batmobile's real
contact response is sparks, two scrape components, landing sparks, a pad rumble and a screen shake —
and **none of those are gated by speed in the decoded members**, so they can stay on. The operator's
"no scratch or dent" is therefore a *default*, not a subtraction: keep `chassis_impact_vfx` /
`chassis_sliding` / `chassis_impact_default_sfx` as the collision-only carriers and touch no number.

---

## 3. Step 2 — keep weapon damage and the health bar

### 3.1 What must not change

| # | member / member set | keep | why |
|---|---|---|---|
| WD-1 | entity root `invulnerable` | **0** | 1 is whole-vehicle (`DAMAGE_MECHANISMS.md` §4 caveat) and would zero weapon damage too — it is the one value that would break this request |
| WD-2 | `max_health` | **2000** | the pool the bar is drawn from; changing it re-scales every hits-to-kill number in `health-damage-states-plan.md` §6 |
| WD-3 | `bullet` 5000 @ 99, `bullet_heavy` 5 @ 20, `explosion` 250 @ 50 | **unchanged** | the tank profile the build already uses; measured to still let weapon damage through (`DAMAGE_MECHANISMS.md` line 4) |
| WD-4 | `part_damage_types[]` 24 `Land_*` rows | **unchanged** | the build already differs from the donor by exactly one row (`Land_Wheel.instantly_damaged_by_bullets` 1 → 0) |

### 3.2 The bar itself

**UNKNOWN, and it must be said plainly.** `Research/JC3Grab/JC3_HUD_WEAPONS.md` is the only vehicle
HUD decode in the repository and it carries **no health-bar element** — its vehicle HUD table covers
the reticle, lock-on, ammo and weapon-failure events, nothing that reads health. What *is* evidenced
is that a bar exists in play: `DAMAGE_MECHANISMS.md` §4 writes the probe take as *"health bar
untouched, no fire, no explosion"*, i.e. the project's own authors already treat a vehicle health bar
as an observable. So "keep the health bar" is satisfied by keeping WD-1…WD-3; it is **not** a HUD
edit, and no HUD value is proposed here.

- **Settling file for the HUD half:** the vehicle HUD movie / `hud_code` module list for the vehicle
  layer (the same class of file `JC3_HUD_WEAPONS.md` decoded for the reticle), searched for a health
  read. Until it is read, the bar's carrier is UNKNOWN.

---

## 4. Step 3 — the explosion at zero health

### 4.1 Two different mechanisms, and only one of them is the death blast

| mechanism | carrier | what it is |
|---|---|---|
| the vehicle's own destruction blast | `CForcePulse` on the `CCar` root, `SettingsFile` = `car_explosion_medium.ftune` | the explosion a destroyed vehicle sets off (`FORCEPULSE.md` §4.2: 214 of 307 pulses are owned by the vehicle root and each uses that vehicle type's own blast) |
| the pre-death blast trigger | `explosion_threshold` (int32, fleet **500 … 4000**, build **4000**) + `explosion_delay_s` (uint16, fleet **5 … 10**, build **8**) | a threshold instant, separate from destruction |

`explosion_threshold`'s **semantics are UNKNOWN** (`DAMAGE_MODEL.md` step 7: health remaining vs
per-hit blast damage; the fleet range 500…4000 overlaps `max_health` 500…4000 so both readings fit).
The build's 4000 on a 2000 pool is "never" under the health reading.

**So: do not write `explosion_threshold` to get the death blast.** The death blast is already the
root pulse. What must be *verified* is that the pulse survived into the Batmobile's `.ee` — the
donor's armed build carries `CForcePulse` → `car_explosion_medium.ftune` (`FORCEPULSE.md` §5,
"donor, armed"), but whether the Batmobile entity kept that object is **UNKNOWN** in this repository.

- **Settling file:** the Batmobile's own `.ee` graph dump, read with `jc3forcepulse.py`'s decoder
  (the same pass that produced `FORCEPULSE.json` over 232 entities). `grep CForcePulse` on the dump
  is enough: present → leave every threshold alone; absent → add the pulse with the donor's tune.

### 4.2 If the probe shows health 0 does *not* explode

Then, and only then, the fallback is a threshold edit:

| # | member | write | domain | note |
|---|---|---:|---|---|
| EX-1 | `explosion_threshold` | **1** | **no** (fleet 500…4000) | undeclared switch; under the health reading = "explode with 1 HP left" |
| EX-2 | `explosion_delay_s` | **1** | **no** (fleet 5…10) | collapses the 5-10 s fuse to one second, so the blast lands with the bar emptying |

EX-2 is the value that matters for the operator's phrasing ("then it explodes"): the fleet's 5-10 s
delay is a burning-car fuse, not a death throe.

---

## 5. Step 4 — the blast that kills the occupants

The blast is `car_explosion_medium.ftune`; its eight `ForcePulseSettings` numbers are decoded in
`FORCEPULSE.md` §3 and are identical in all 115 entities that carry it:

| member | value | meaning |
|---|---:|---|
| `PlayerDamage` | **500** | damage dealt to the player inside the radius |
| `PlayerDamageRadius` | **5** | metres |
| `PlayerDamageRadiusMin` / `PlayerDamageRadiusPercentageMax` | **0 / 0** | full damage at the centre, falling off at once |
| `AIDamage` | **500** | damage to AI |
| `AIDamageRadius` | **5** | metres |
| `AIDamageRadiusMin` / `AIDamageRadiusPercentageMax` | **0 / 0** | same falloff |

**The occupant-kill route, stated at its real evidence level:**

1. The pulse is owned by the vehicle root and sits **at the entity origin** — `FORCEPULSE.md` §2:
   position `(0.0, 0.0, 0.0)` for **292 of 307** pulses and world transform identity for the
   commonest of the six. *(decoded)*
2. The seated driver is at `point.driver`, which `EJECT.md` §3 places inside the hull —
   `(-0.44, 0.34, 0.20)` to `(-0.58, 0.60, 0.39)` in vehicle space. *(decoded)*
3. Therefore the occupant is inside `PlayerDamageRadius` 5. *(derived: geometry + radius)*
4. The occupant receives `PlayerDamage` 500. *(derived; the delivery path is code, so this is an
   inference from the member's name, not a decoded call edge — `FORCEPULSE.md` §6 records exactly
   this limit: "the owner pointer proves who carries the blast, not the code path that fires it")*
5. 500 ≥ the player's health, so the occupant dies. **UNKNOWN** — no player-health value exists in
   `Research/JC3Grab/`. Settling file: the player character's health/`CPawn` module, not yet decoded;
   the operator's own report ("kills the passengers") is the behavioural confirmation that the
   stock number is enough.

**Values to write: none.** The stock 500/5 is the blast the operator described. The lever, if
"violently" ever needs to be stronger, is the fleet's own spread from `FORCEPULSE.md` §3: `w613_bomb`
1500/25, `w704_m488` 3000/50. Both are additions, not ports — a 50 m player-damage radius kills
every pedestrian on the block, which `car_explosion_medium`'s 5 m does not.

---

## 6. Step 5 — no wreck, no fire, nothing drivable afterwards

### 6.1 The destroyed meshes are scenery — and open item 6 says so

`app-skins-and-variants.md` §6 **open item 6**: *"Whether the destroyed/fire meshes ever appear as a
player-held car — they ship in the player packages, but `MECHANICS.md`/`VARIANTS.md` do not say
whether the player's car becomes them or they are only scene props."* — **UNKNOWN**.

The same report's §3 row 5 offers the swap as *one candidate*: `Batmobile_V3_Destroyed` (57,101
verts, 1 material) could ride the `mshswap` slot the wheels already use. **This plan does not take
that route**, for two reasons:

- JC3's own wrecks are **standalone scenery entities**, not vehicle states: `STANDALONE.json` lists
  `bus_wreck.ee`, `tank_wreck.ee`, `oldcompact_wreck.ee`, `technicaljeep_wreck.ee` and six more under
  `editor/entities/jc_design_tools/world_at_war/encounters/ambient/`, and `REBELDROP.md` line 142
  counts them as scenery leaves. A wreck in JC3 is a *different entity placed in the world*.
- the operator's fact is that the car "does not remain as a wreck you keep driving". A mesh swap is
  precisely the mechanism that would keep it drivable while looking destroyed.

So the destroyed/fire **meshes are scenery**: they belong to a wreck entity, if one is ever wanted as
a set piece, and never to the player's car. *(derived from `STANDALONE.json` + `REBELDROP.md`; the
BmAK side stays UNKNOWN per item 6.)*

### 6.2 The visible stages, and the fire

| stage | carrier | build | action |
|---|---|---:|---|
| smoke | `smoke_threshold` uint16 | **1050** (52.5 % of 2000) | see below |
| burn (fire) | `burn_threshold` uint16 | **250** (12.5 %) | see below |
| burn duration | `burn_duration_s` | **20** | leave |
| vulnerable window | `vulnerable_explosion_threshold` | 100 | leave |
| destruction | root `CForcePulse` | (see §4.1) | leave |

"No visible damage stages" argues for switching the smoke and fire stages off, **but the field
semantics do not allow it to be asserted**: `smoke_threshold`/`burn_threshold` are UNKNOWN between
*health remaining* and *per-hit damage* (`DAMAGE_MODEL.md` step 7), and 0 is out of the fleet domain
for both (`smoke_threshold` 200…1050, `burn_threshold` 50…250). Under one reading 0 = "never"; under
another it could read as "always".

| # | member | write | domain | note |
|---|---|---:|---|---|
| NF-1 | `smoke_threshold` | **0**, *probe only* | no (min 200) | if 0 shows a car smoking at spawn, fall back to **200** (in-domain min) |
| NF-2 | `burn_threshold` | **0**, *probe only* | no (min 50) | fall back to **50** (in-domain min, = 2.5 % of health) |
| NF-3 | destroyed-mesh `mshswap` | **not wired** | n/a | no wreck state on the player car (§6.1) |

**Take for NF-1/NF-2:** spawn the car untouched → no smoke, no fire (0 is "never"); damage it to 100 HP
→ still no smoke, no fire, bar only; destroy it → explosion, no burning wreck left behind. Any smoke
appearing at full health falsifies the 0 reading and selects the in-domain fallback.

---

## 7. All values in one place

| # | file | member | build | write | evidence |
|---|---|---|---:|---:|---|
| CX-1 | `lave_health_medium.vmodc` (build copy) | `impact_damage_factor` | 0 | **0** | decoded; effect derived, probe pending |
| CX-2 | same | `deform_scale` | 0 | **0** | decoded; effect derived |
| CX-3 | same | `impact_armor` @ strength | 5000 @ 100 | **keep** | decoded; effect UNKNOWN |
| CX-4 | same | `melee_armor` @ strength | 5000 @ 100 | **keep** | decoded; effect UNKNOWN |
| WD-1 | entity `.epe` | `invulnerable` | 0 | **0** | decoded (233/233 roots) |
| WD-2 | `lave_health_medium.vmodc` | `max_health` | 2000 | **keep** | decoded |
| WD-3 | same | `bullet` / `bullet_heavy` / `explosion` channels | 5000@99 / 5@20 / 250@50 | **keep** | decoded |
| EX-0 | build `.ee` | `CForcePulse` + `car_explosion_medium.ftune` | unknown | **verify, then leave** | decoded in donor; build UNKNOWN |
| EX-1 | `lave_health_medium.vmodc` | `explosion_threshold` | 4000 | **4000**, or 1 on failure | decoded value, semantics UNKNOWN |
| EX-2 | same | `explosion_delay_s` | 8 | **8**, or 1 on failure | decoded value |
| OC-1 | `car_explosion_medium.ftunec` | `PlayerDamage` / `AIDamage` | 500 / 500 | **keep** | decoded |
| OC-2 | same | `PlayerDamageRadius` / `AIDamageRadius` | 5 / 5 | **keep** | decoded |
| NF-1 | `lave_health_medium.vmodc` | `smoke_threshold` | 1050 | **0** (probe) → 200 | decoded value, semantics UNKNOWN |
| NF-2 | same | `burn_threshold` | 250 | **0** (probe) → 50 | decoded value, semantics UNKNOWN |
| NF-3 | wheel/destroyed `mshswap` | — | wheels only | **do not add destroyed** | decoded (`app-skins-and-variants.md` §2) |

---

## 8. Pilot cards

### HX-1 — a crash does not damage the Batmobile

**Setup:** `build_test-091` (CX-1…CX-4 only), no weather, dry road.

**Do:** three full-boost rams into a concrete wall, then three full-boost rams into a stock civilian
car, then one boost-ram into the flatbed at battle-mode speed.

**Pass band:** health read is **identical before and after all seven hits (Δ = 0)**; the HUD bar does
not move; **no** smoke, fire, dent, mesh or material change at any point; the car is still drivable
and steers normally afterwards. **Fail:** any bar movement, any smoke/fire, or the car becoming
undrivable.

### HX-2 — weapon damage empties the bar and the blast kills the seated occupant

**Setup:** same build, player seated, one arm per run.

**Do:** destroy the car three ways — a tank shell (explosion channel), an RPG (explosion), and 200
rifle rounds (bullet, the `Q1-DM-B` arm).

**Pass band:** the bar moves on every weapon hit (weapon damage is live), reaches 0, and the car
**explodes within 0–1 s of the bar reaching 0**; the seated player is **dead within 1 s of the blast**
(defeat/respawn, not a survivable knock); **no wreck is drivable afterwards** — the vehicle entity is
gone and no fire or destroyed mesh remains on the road where the car was; a pedestrian standing
**≤ 5 m** away is also killed, and one at **≥ 8 m** is not (the radius test). **Fail:** the car
survives at 0 HP, the player survives the blast, or anything looking like a wreck can still be driven.

---

## 9. UNKNOWN register

| # | question | settling file |
|---|---|---|
| 1 | does `impact_damage_factor` 0 actually zero collision damage, or is collision damage applied through a part? | probe HX-1; else `CDamageControllerArmor` binder, `ARMOR_STEP.md` §3 |
| 2 | the armour composition rule (H0/H1/H2) and the `max_health` unit | `DAMAGE_MODEL.md` §6 Q-1 probes (A/B/C) |
| 3 | does the Batmobile's own `.ee` still carry the `CForcePulse` / `car_explosion_medium` pair? | its graph dump via `jc3forcepulse.py` |
| 4 | which instant fires the vehicle blast on destruction | code; `FORCEPULSE.md` §6 ("not in any file") |
| 5 | does the seated player actually take `PlayerDamage` from the vehicle's own pulse? | probe HX-2; the member name is the only bridge |
| 6 | the player's health value (is 500 enough?) | the player `CPawn` / health module — **not decoded in this repository** |
| 7 | `explosion_threshold` / `smoke_threshold` / `burn_threshold`: health-remaining vs per-hit damage | `DAMAGE_MODEL.md` step 7; probes EX-1/NF-1/NF-2 |
| 8 | the vehicle health bar's HUD carrier | the vehicle HUD movie / `hud_code` module list (the file class behind `JC3_HUD_WEAPONS.md`) |
| 9 | do BmAK's destroyed/fire meshes ever appear as the player's car? (`app-skins-and-variants.md` §6 item 6) | BmAK gameplay trace / `MECHANICS.md`; not answerable from the grab |
| 10 | `OnExploded` (`USAGES.md` line 64, 2 vehicles, `engine_break`) — is it the destruction hook? | the two carrier entities' `.ee` dumps |

---

## 10. Change record

- **Intended change:** none to game data. This document plans the health/explosion behaviour only.
- **File written:** `tmp/freebuff/reports/health-to-explosion-no-crash-damage-plan.md`.
- **Why this file:** the request names it as the deliverable.
- **Revert:** delete the file. No other file was touched.

## 11. Checks run

| # | check | result |
|---|---|---|
| 1 | `health-damage-states-plan.md` §1-§6, `collision-impact-effects-plan.md` §2-§9 | read; BmAK 1200 HP / no dent / no bullet path; JC3 eight channels + three thresholds |
| 2 | `DAMAGE_MODEL.md` §2 | build values quoted exactly: `impact_armor` 5000 @ 100, `impact_damage_factor` 0, `deform_scale` 0, `melee` 5000 @ 100, `max_health` 2000 |
| 3 | `DAMAGE_MODEL.md` §7 | fleet domains: `impact_armor` 0…5, `impact_armor_strength` 0…100, `impact_damage_factor` 1…12, `deform_scale` 1…2 |
| 4 | `DAMAGE_MECHANISMS.md` lines 3-5, §4 | armour channels are **not** an exemption — the build hits their maximum and still takes bullet damage |
| 5 | `VOCABULARY.md` | `smoke_threshold` 200…1050, `burn_threshold` 50…250, `burn_duration_s` 20…20, `explosion_threshold` 500…4000, `explosion_delay_s` 5…10 |
| 6 | `FORCEPULSE.md` §2-§5 | `car_explosion_medium` = 500/5 player and 500/5 AI, radius % 0; 292/307 pulses at the entity origin; donor armed car owns the pulse |
| 7 | `app-skins-and-variants.md` §6 item 6 | quoted verbatim as UNKNOWN; §3 row 5 (the swap candidate) explicitly declined |
| 8 | `STANDALONE.json` / `REBELDROP.md` line 142 | eleven `*_wreck.ee` scenery entities — wrecks are scenery, not vehicle states |
| 9 | negative search `health` in `JC3_HUD_WEAPONS.md` | **0 hits for a vehicle health-bar element** — reported as UNKNOWN, not as "there is no bar" |

No game process was started, attached to or injected into; static read only.
