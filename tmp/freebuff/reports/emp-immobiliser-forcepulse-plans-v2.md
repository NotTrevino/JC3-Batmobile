# EMP, Immobiliser and the force pulse — plans v2

Card: emp-immobiliser-forcepulse-plans-v2. 2026-11-08. Reconciles six reports that were never
reconciled with each other, and keeps the operator's answer as the frame.

| input | what it settles here |
|---|---|
| `tmp/freebuff/reports/emp-effects-closest-system-plan.md` (326 L) | the build shape (class leg + pulse leg) and every BmAK number's first citation |
| `tmp/freebuff/reports/audit-emp-effects-numbers.md` | 65 figures checked against the JC3 grab: **31 agree, 0 disagree, 34 silent** — every BmAK-side figure is silent because the grab holds no BmAK values |
| `tmp/freebuff/reports/immobiliser-launch-payload-build-plan.md` | the launched round's four missing tags, the splice proof, and the one blocker (no package writer) |
| `tmp/freebuff/reports/four-slot-immobiliser-audit.md` | two defects in that plan (property type, splice provenance) and the package-scope wording |
| `tmp/freebuff/reports/force-pulse-carrier-recount.md` | 23 of 28 pulse numbers match; five differ (owner table, matrix claim, bike falloff, origin exceptions, line count) |
| `tmp/freebuff/reports/emp-burst-route-result-check.md` | E1–E5: **0 confirmed, 0 contradicted, 5 UNKNOWN** — the experiments were specified, never run |
| `tmp/freebuff/reports/immobilizer-vs-emp-missile.md` | **the Immobiliser is the EMP missile** (`RBatmobileEMPMissile` firing `Batmobile_EMPMissile_Projectile_ForCars`); the **tracker is a separate launcher on the same button and socket** |

Labels: **decoded** = value read at the cited file:line; **derived** = arithmetic over decoded values,
shown; **UNKNOWN** = no cited file states it, and the file that settles it is named in §5.

---

## 1. Every EMP number, and its status after the audits

"Status after audit" is the tightest honest label the four audits leave. The JC3 grab holds no BmAK
values (`EMP_DISABLE.json` keeps offsets, not values), so a BmAK figure can only be **decoded in
`Research/BatmobileGrab`** or **UNKNOWN** — never "agreed" by a JC3 file.

| # | number | value | where it is stated | status after audit |
|---:|---|---|---|---|
| N1 | burst cooldown | **2.0 s** | `Research/BatmobileGrab/WEAPONS.md:800` — `RVehicleWeapon.WeaponCoolDown` @`0x0830` = 2.0 | **decoded** (defaults row). The plan's *archetype 2.0 / CDO 10.0* split is **UNKNOWN**: the grab records the offset only (`BMSDK_OFFSETS.json:25436`), and the audit's D7 found no value (audit §2, D7) |
| N2 | burst stages | **4** (`Stage_01`…`Stage_04`) | `Research/BatmobileGrab/PARTICLES.md:349–353` — four stage rows, 10/10/10/**13** emitters (Funhouse block) | **decoded** (count + emitter split). The old "10/10/10/13" is right; the *per-stage lifetime/rate* table at `PARTICLES.md:139–142` truncates its columns |
| N3 | stage lifetimes | **0.2 – 4.0 s** (01–03 to 1.0 s, 04 to 4.0 s) | claimed from `PARTICLES.md`, but the rows read `| 1, 1, 0.2, 0.8 ... |` (`PARTICLES.md:139–142`) — the 4.0 s endpoint is **not printed** | **UNKNOWN** — audit D2/D3 silent; settle with the stage module blocks named in `PARTICLES.md:350–353` (`EMP_Burst_Stage_0N.ParticleModuleRequired`) or the raw package |
| N4 | stage-04 spawn rate | **1500 /s** | `PARTICLES.md:142` — spawn column `1.5e+03`; lower stages `-` | **decoded** for the 1500 ceiling. The **0** floor ("0–1500") is **derived** (a rate's minimum in a column that prints a single value); no file prints 0 |
| N5 | ring mesh / cross-section | **250 cm** mesh, **250 × 30 × 30 cm** on stage 04 | claimed from `PARTICLES.md`; **no 250 appears on any `EMP_Burst_*` row** in that file | **UNKNOWN** — audit R7/R13 silent; settle with the mesh/size parameters in the stage module blocks (`PARTICLES.md:350–353`) |
| N6 | scale-over-life | **20×** (→ 50 m ring inside a 75 m range = 0.667) | claimed from `PARTICLES.md` | **UNKNOWN** — audit R8/R9 silent; the growth curve lives in the module block, not the summary table |
| N7 | pulse, player half | `PlayerDamage` **100**, `PlayerDamageRadius` **25 m**, `…RadiusPercentageMax` **1**, `…RadiusMin` **1** | `Research/JC3Grab/EMP.md:39–42` (truck `EMP` column) | **decoded / AGREE** (audit R3, R4, V3) |
| N8 | pulse, AI half | `AIDamage` **100**, `AIDamageRadius` **25 m**, `…PercentageMax` **1**, `…RadiusMin` **1** | `EMP.md:43–46` | **decoded / AGREE** (audit V4) |
| N9 | pulse flags | `id:4912FC04`=**0**, `id:AE6F7EFF`=**1**, `id:CF4F7880`=**1** | `EMP.md:60–62` | **decoded / AGREE** (audit C9). Fleet census: 307 pulses split `0,0,0`×16 / `0,1,1`×1 / `1,0,0`×278 / `1,0,1`×12 (`EMP_DISABLE.json` `pulse.flag_triples`) |
| N10 | disable duration | **[2, 4, 8, 12] s**, index = power level | `RBatmobileEMP.DisableEnemyDuration` @2400 — **member named only** at `BMSDK_OFFSETS.json:14197–14198`; no value in any file | **UNKNOWN** — audit D1 silent; settles with the class-default export (CDO 46694) or the in-game probe Q-EMP-4 |
| N11 | power-level charge times | **[0, 0.5, 1.0, 1.5] s** | `PowerLevelChargeTime` @2424 — name only, `BMSDK_OFFSETS.json:14211–14212` | **UNKNOWN** — audit D4 silent |
| N12 | burst range | **7500 UU = 75 m** | `Range` @2396 — not in the grab's offset set at all (audit §8) | **UNKNOWN** — audit R5/R6 silent; the 75 m build value is **derived** from 7500 UU ÷ 100 |
| N13 | `w702_emp` payload | damage **500**, range **50 m**, id **702**, type **6**, class `CEMPWeapon` | `EMP.md:164–170`; `EMP.json:670`, `:673` | **decoded / AGREE** (audit R1, V1, C14) |
| N14 | `w503_turret_emp` payload | damage **500**, range **750 m**, id **503**, type **2** | `EMP.md:164–170`; `EMP.json:734`, `:737` | **decoded / AGREE** (audit R2, V2) |
| N15 | shipped `fire_rate` on those weapons | **0.0** (`w702`), **0.5** (`w503`) | `EMP.json:671`, `:735` (audit D6) | **decoded** — so writing **2.0** (N1) is a deliberate change, and the grab never states whether `fire_rate` is seconds or shots/s (audit §7) |
| N16 | `CEMPWeapon` in a vehicle | **0 of 88** vehicle weapon components | `EMP.md:223`; `EMP.json:4–5` (`cemp: 0`, `components: 88`) | **decoded / AGREE** (audit C14) — the class is a handheld + a static prop today, so it has to be **added**, not found |
| N17 | the disable state in data | `is_disabled_by_emp`: **0** literal and **0** Jenkins-hash bindings across **1,941** entries / **3,978,089,026 B**; control hits `invulnerable` 289, `is_in_water` 160 | `EMP_DISABLE.json:170`, `:168`, `:193`, `:199`, `:192`, `:194` | **decoded / AGREE** (audit C10, C11, C13). The **1,307 entries / 3.96 GB** second pass is **UNKNOWN** (audit C12 — no grab file records that pass) |
| N18 | the only engine-off timer | `car_common.engine_shut_down_delay_s` **30**, boat/heli/motorbike/plane **5** | `WATER.md:229–233`; `VOCABULARY.md:1390` | **decoded / AGREE** (audit D10) — but the trigger is water, not any weapon |
| N19 | engine-kill floor | `engine_max_damage_torque` **0.25–0.75** (n=145) | `VOCABULARY.md:831` | **decoded / AGREE** (audit V10) — floors torque, never 0 |
| N20 | electrical armour of the medium tank | `electricity_armor` **−1** @ strength **100**; bullet 5000@99; explosion 250@50 | `DAMAGE_MODEL.md:40`, `:42`, `:46`; `VOCABULARY.md:1464–1465` | **decoded / AGREE** (audit V8, V9) |
| N21 | missile payload (fired round) | damage **60**, radius **0**, type `RDmgType_BatmobileCannon` — **on the orphan sibling**, not the fired archetype | `immobiliser-launch-payload-build-plan.md` §0 run log (fired `_ForCars`: 10 tags, 83 B, `@728`/`@732` absent) | **UNKNOWN** for the fired round: the values exist one export over (export 16, 0 incoming refs) and are **copied in**, not read off it |
| N22 | missile launch shape | `bInstantFire` **True**, launch rotator **−3640** = **−19.995°** pitch, socket `BattleModeSpotLight` | `immobiliser-launch-payload-build-plan.md` §4 (`@2464`, `@2452`, `@2436`) | **decoded** in that plan's package run; **derived** here (the pitch conversion). The tracker's `bInstantFire` is **UNKNOWN** |
| N23 | Immobiliser impact sound | `Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact` on export 968 of the **orphan** | build plan §2; `immobilizer-vs-emp-missile.md` A4 | **UNKNOWN as played** — the fired archetype's only audio member (`@124`) serialises no event |
| N24 | pulse fleet shape | **307** pulses, **25** owned by `CMissileWeaponBase`, **29** `CBulletWeaponBase`, **126** `CCar`, **1** non-owner reference | `FORCEPULSE.md:194–197`, `:280`; recount §0 | **decoded / MATCHED.** Recount corrections: `CMotorBike` **19** was omitted from one owner table (so 288 of 307 accounted, not 307); the "six non-identity matrices" claim is really **six distinct, five non-identity, two with rotation**; `bike_explosion_medium` falloff is **0.1/0.15**, not 0.1/0.25 |
| N25 | `truck_emp.ftune` place in the fleet | **1** pulse, `100 / 25` player and AI, radius factors 1/1 | `FORCEPULSE.md:141`; `EMP.md:39–46` | **decoded** — this is the pulse the build copies |
| N26 | burst media sizes | `explosion_emp_flatbed.effc` **24,015 B**; `emp_active.effc` **8,783 B** | `EMP.md:100`, `:104`; `EMP.json:45`, `:348` | **decoded / AGREE** (audit C15, C16) |

**Net on the audit:** 31 agree / 0 disagree / 34 unknown is not a verdict on the plan — it is the
shape of the corpus. What the audits *do* change is narrower and is all applied above: the BmAK
values are decoded in `Research/BatmobileGrab` rather than "agreed" by JC3; three numbers the plan
presented as decoded (N3, N5, N6) are not printed anywhere I can cite; and two payload figures (N21,
N23) belong to an export nothing references.

---

## 2. The burst and the missile, as two rows

| row | BmAK object (decoded) | JC3 carrier | number written | build step | label |
|---|---|---|---|---|---|
| **EMP burst** | `RBatmobileEMP`, `Weapons.Batmobile_EMP_Burst`, 2,552 B; 4 stages; prompt `ui_activate_emp`; trigger `trigger.use_item` @`(0, 1.3507, 2.396)` → `S_STUNT_USE_ITEM_VEHICLE` (`EMP.md:80–82`) | **`CForcePulse` with `truck_emp.ftune`** — the only shipped pulse with the EMP flag triple (`1,0,1` = 12 pulses; `0,1,1` = 1, `EMP_DISABLE.json` `pulse.flag_triples`), damage `100 / 25 m`, factors `1 / 1` | 100 dmg, 25 m, factors 1/1, flags as shipped; radius widened to **75 m** only if the derive in N12 is accepted | copy the `rebel_emp_01`…`rebel_emp_custom_mm250` pulse object onto the car at chassis centre, copy the truck's `trigger.use_item` box + prompt, point it at `bm_emp_burst.effc` | burst: decoded; the 75 m: derived; the disable: **UNKNOWN** (Q-EMP-2) |
| **EMP missile (the Immobiliser)** | `RBatmobileEMPMissile` firing `Projectiles.Batmobile_EMPMissile_Projectile_ForCars` (both pointers `@2428`, `@2492` already name it, 6/6 PASS); the **tracker** is `RBatmobileVehicleTracker` firing `Batmobile_Tracker_Projectile`, same button `B`, same socket `BattleModeSpotLight` | two carriers, both real: **(a) `w702_emp`** — the only `CEMPWeapon` in the data, cloned into the second driver slot `id:00568A74`; **(b) a `w618_sportsmuscle_missile` clone** carrying its own `CForcePulse`, the shipped pattern (`CMissileWeaponBase` owns 25 of 307 pulses, `FORCEPULSE.md:197`) | (a) damage 500, range 50 → 75 m if the derive is accepted, `fire_rate` 2.0, `weapon_type` **6**, `weapon_id` moved into **601–622** because **702 has no icon** (`JC3_HUD_WEAPONS.md:161–162`); (b) the w618 tune's own velocity + `truck_emp.ftune` pulse | (a) clone the component block into the `.epe`'s second driver slot; (b) clone the pod and add the pulse; both legs removable alone | launcher pointers decoded 6/6; payload values (N21) copied from the orphan; the disable **UNKNOWN** |

**Package scope, corrected** (`four-slot-immobiliser-audit.md` C8): say **"the three packages that
carry `Batmobile_EMP_Missile_Launcher` (Batmobile, MK2, Funhouse)"** — `Playable_BatmobileJoker_SF`
has no launcher and 0 references to either projectile.

**Two payload corrections** (same audit, B7/B8): `@712` is an **`ObjectNCRProperty`** (type 16)
holding a Class reference, not a `ClassProperty`; and the **83 → 115 B / 10 → 14 tags** splice result
is the build plan's own in-memory measurement, **not** a `T-WP4d.md` figure — label it "measured in
this plan's scratch run".

**Four-slot / tracker note that survives:** the Immobiliser and the tracker are **one button and one
socket** (offsets 2436/2452 identical on both launchers), so as one missile entity the weapon count
is **10, not 11** (`immobilizer-vs-emp-missile.md` §6). That does not unblock the 11-into-2 slot
problem, it only fixes its arithmetic.

---

## 3. The disable half — a composed route, not an omission

The premise: **`is_disabled_by_emp` has 0 bindings in the 1,941-entry / 3.98 GB scan**
(`EMP_DISABLE.json:170`, `:193`, `:199`), the literal is written nowhere, the hash is read nowhere,
and no `CEMPWeapon` exists among the fleet's 88 vehicle weapon components (`EMP.md:223`). So the
disable cannot be *found* in data, and the build must *compose* it. The composition:

| leg | what it is | what it can actually deliver | why it is in the route |
|---|---|---|---|
| **L1 — class leg** | clone `w702_emp`'s `CEMPWeapon` component into the Batmobile's second driver slot `id:00568A74`, `weapon_type` 6, damage 500, `fire_rate` 2.0, `weapon_id` in 601–622 | the engine's own EMP hit path, i.e. whatever sets `is_disabled_by_emp` if anything does | the **only** data-side writer of the state: the class is what carries it (N16/N17). This is the primary disable |
| **L2 — pulse leg** | `CForcePulse` + `truck_emp.ftune` (100 / 25 m, factors 1/1, EMP flag triple) on the car, plus `bm_emp_burst.effc` | damage and the visual; whether the flag triple disables is undecided in every file | the shipped EMP *look* and the only 3-flag pulse in 307 (`FORCEPULSE.md:141`; `EMP_DISABLE.json` `pulse.flag_triples`) |
| **L3 — fallback stall** | `LandEngine.engine_max_damage_torque` driven to **0.0** against a fleet domain of **0.25–0.75** (n=145) | a torque floor, i.e. "stops driving" without a state | only used **if L1 is rejected on a car**; and only in a **private** module, because the value lives in shared `vehicle_common` (0.0 is a declared switch outside the fleet domain, not a translation) |

**Precedence, stated so the build cannot drift:** L1 is the disable; L2 is damage + visual; L3 is a
documented fallback that must never be enabled silently. Each leg is removable alone, and the pilot
separates them: if the victim stalls with L1 and not with L2, L2 is visual-only and L1 carries the
state (§4, Q-EMP-2 vs Q-EMP-1).

**The composition is not an omission of a member.** There is no member to omit — the state is
class-keyed and native (`EMP_DISABLE.json`; `EMP.md:215`). What the route adds is the one thing data
can add: the class that owns the state, mounted where a vehicle can fire it.

---

## 4. The four runtime probes — pilot cards only, nothing launched

These are the four Q-EMP probes from `tmp/freebuff/reports/immobiliser-and-emp-trigger.md:251–264`,
restated as pilot cards. **Status: specified, never run.** `emp-burst-route-result-check.md` finds
**0 confirmed / 0 contradicted / 5 UNKNOWN** across E1–E5, `Builds/test-09*` does not exist, and the
experiment report itself records "experiments are specified, not run (test ban)". Nothing below is a
result.

| # | probe | one sentence | pass band |
|---:|---|---|---|
| Q-EMP-1 | does the engine's own `CEMPWeapon` disable a car | Spawn a stock civilian car, fire `w702_emp` at it from 10 m, and time the restart from the hit. | engine stops within **1 frame** 4/4; restarts once, not repeatedly |
| Q-EMP-2 | does the pulse alone disable, or only damage | Park a stock car inside 25 m of the rebel EMP truck, press its use-item, and watch the car. | car stalls **3/3**, or takes exactly **100** damage and drives on **3/3** — either answer passes; a mix fails |
| Q-EMP-3 | is a `CEMPWeapon` accepted on a car | Install the L1 build and fire the second slot at a stock car at 10 m, then at 70 m. | same stall signature as Q-EMP-1 at both ranges **3/3**; no stall means the class is not vehicle-mountable and L1 is out |
| Q-EMP-4 | the disable duration on the Batmobile's target | Repeat Q-EMP-1 and read the restart time at power level 0, 1, 2, 3. | restart at **2 / 4 / 8 / 12 s ± 1 s** for the four levels 4/4 (the values are N10, which no file states) |

---

## 5. UNKNOWNs — the file that settles each

| # | UNKNOWN | settles with |
|---:|---|---|
| U1 | disable duration (N10) and charge times (N11) | the `RBatmobileEMP` class-default export (CDO 46694) — names and offsets are already in `BMSDK_OFFSETS.json:14197–14212`, values are not; then Q-EMP-4 |
| U2 | whether a `CEMPWeapon` is accepted in a car's weapon slot | the engine's weapon-class factory (`JustCause3.exe`), or Q-EMP-3 |
| U3 | whether code reads `is_disabled_by_emp` by name or hash | pointer/instruction scan of the vehicle-variable block (0 bindings today, `EMP_DISABLE.json:193`) |
| U4 | the pulse flag triple's meaning | Q-EMP-2 only — the flags are named in no file |
| U5 | stage lifetimes, 250 cm mesh, 20× growth (N3, N5, N6) | the `EMP_Burst_Stage_0N.ParticleModuleRequired` blocks named at `PARTICLES.md:350–353`, or the raw `Playable_Batmobile*_SF` particle packages |
| U6 | the fired missile's damage/sound before the payload edit (N21, N23) | `wp4_emp_payload_check.py --reverse` today (all four FAIL), then the same check after the splice |
| U7 | the package writer that can grow an export by 32 B and keep a 17.9 MB chunked package loadable | the writer named in `immobiliser-launch-payload-build-plan.md` §5 step 2 — **this is the plan's single blocker** |
| U8 | whether the pulse disables at all (the whole L2 question) | Q-EMP-2; the alternative is that L1 alone carries the disable |

---

## 6. Checks run for this page

| check | result |
|---|---|
| audit tallies applied | 65 figures: 31 agree / 0 disagree / 34 UNKNOWN, with the silent ones marked UNKNOWN and their settler named |
| burst stage figures re-read | `PARTICLES.md:139–142` (truncated lifetime/rate columns) and `:349–353` (4 stages, 10/10/10/13) — **three plan numbers are not printed there** and are marked UNKNOWN |
| pulse numbers re-read | `EMP.md:39–46`, `:60–62`, `:100–104`, `:164–170`, `:215`, `:223`; `FORCEPULSE.md:141`, `:194–197`, `:280`; `EMP_DISABLE.json:22–23`, `:168–170`, `:192–194`, `:199` |
| disable-state scan figures | 1,941 entries / 3,978,089,026 B / literal 0 / hash 0 / 289 / 160 — all as the JSON states |
| carrier corrections folded | `CMotorBike` 19; six-distinct/five-non-identity matrices; bike falloff 0.1/0.15; 15 origin exceptions not 14; `ObjectNCRProperty` at 712; splice labelled self-measured; Joker has no launcher |
| runtime probes | 4, listed as pilot cards; **0 run**, 0 results claimed (`emp-burst-route-result-check.md`: 5 UNKNOWN, `Builds/test-09*` absent) |
| files written | this page only |
| game launched / package or tune written | **no** |

Revert: delete this file. No plan, tune, `.effc`, `.epe` or package was modified.
