# Traffic, AI and how JC3 should treat the Batmobile — plan

Sources: `tmp/freebuff/reports/G2-29.md`, `Research/JC3Grab/TRAFFIC.md` (the census, generated),
`Research/JC3Grab/STANDALONE.md` §4-§6, `Research/JC3Grab/DAMAGE_MODEL.md` (armour channels,
`impact_damage_factor`), `Research/BatmobileGrab/DAMAGE_RULES.md` §3.3/§3.3.1 (BmAK's ram numbers and
sideswipe targeting), `Research/BatmobileGrab/FOOTAGE.md` (`CivilianMissileLockOnDuration`),
`MODLOG.md` (D-6 resolution, the `_debug` leaf finding, the B-13c spawn record), and
`Research/JC3Grab/INDEX.jsonl` (which engine tables and behaviour trees ship at all).

Labels: **decoded** = read at the file/member named; **derived** = a stated rule or arithmetic over
decoded inputs; **UNKNOWN** = searched and absent, with the file that settles it.

**Answer in one line:** JC3 has **no traffic-reacts-to-a-vehicle system**, and the Batmobile is already
outside the only one that exists (the tag→traffic-rule picker), so the plan is not "make traffic react"
but "keep it out of traffic, let JC3's existing heat/faction response do the shooting, and put BmAK's
ram numbers on the car's own damage module". Three of the six behaviours are carried by shipped JC3
systems with **no build edit at all**; two are **UNKNOWN** on the BmAK side (there is no decoded BmAK
member for yielding or fleeing); one — ram damage — is a real, single-member edit.

---

## 0. Where the build actually stands (read this before planning anything around traffic)

| fact | evidence |
|---|---|
| `v0300_…_civilian_01` **is** a civilian traffic vehicle: record in `settings/spawn_vehicle_defs.bin`, 13 tags, 1 of 41 selectors | decoded, `TRAFFIC.md` §2-§3 |
| D-6 was resolved **standalone** (2026-10-28) | decoded, `GRAB_BACKLOG.md:1800` — "**resolved 2026-10-28 (user): standalone entity**" |
| a genuinely **new entity path does not spawn in game** — proven by two one-variable probes | decoded, `MODLOG.md` 2026-11-02 entries ("D-6's 'standalone new path' is disproven in game") |
| so the Batmobile rides the vanilla **`_debug`** leaf (`v0300_car_kensington_sportsmuscle_debug`): base archive, no registry record, **debug proto tables only → no traffic**, not in the vanilla drop menu | decoded, `MODLOG.md` same entry |
| its spawn record was cloned with tags **`vehicle,batmobile`**, which satisfy **0 of 41 traffic selectors** (checked by `bm_rebel --check`) | decoded, `MODLOG.md` B-13c entry |

Two consequences that shape every step below:

1. **The lore break (MOD-5, WLD-8) is already closed by selection, not by AI.** There is nothing to
   "fix" in traffic; there is something to *not break*.
2. **NPC-driven Batmobiles can only reappear if someone adds a tag that matches a selector or points a
   traffic record at the leaf.** Those two edits are the only failure modes, and both are one line.

---

## 1. What controls an NPC's reaction in JC3 data

| # | control | file | what is decoded | what a build can change | evidence |
|---|---|---|---|---|---|
| 1 | **traffic selection** | `settings/spawn_vehicle_defs.bin` (86 records, 8 with a pool key) | donor record = path + 13 tags + name, no pool key; `ambient` on 32 records, `ambient`+`liberated` on 14, faction `*_traffic` tags on 10 | a record's tags — the only lever that decides whether a vehicle is picked | decoded (`TRAFFIC.md` §2, §5) |
| 2 | **traffic rules → driver AI** | `global/global.blo` | 31 rule names, 41 tag selectors, `Driver` seats bound to **10** `ai/bts/*.bts` paths, `AITrafficImpostorSystem`, `PCAITrafficImpostorSystem` | nothing per-vehicle: the rule is chosen by selector, the tree by rule | decoded (`TRAFFIC.md` §3, §6) |
| 3 | **behaviour trees** | `ai/bts/**` | 11 paths in `civilian/` + `vehicle/`: `civilian_std.btc`, `civilian_car_driving.btc`, `civilian_car_passenger.btc`, `priest_heat_clearer.btc`, plus airplane/boat trees | tree contents | names decoded (INDEX); **bodies undecoded → UNKNOWN** |
| 4 | **faction table** | `settings/factions.bin` | the file ships; **layout not decoded** | faction relationships, if the layout were known | **UNKNOWN** — settles: `settings/factions.bin` decode |
| 5 | **threat / heat** | `global/heat.bl`, `global/heat.blo`, `settings/heat.gadfc` | the three files ship; **contents not decoded** | escalation thresholds and responder mix | **UNKNOWN** — settles: `global/heat.blo` decode |
| 6 | **combatant spawning** | `settings/spawn_combatant_defs.bin` (67 records), `spawn_encounter_defs.bin` (56) | counts decoded | who spawns near a fight | decoded counts; selectors **UNKNOWN** |
| 7 | **ram damage** | `<chassis>_vehicle_damage.vmodc` | `VehicleDamage` carries **8 channels** — bullet, bullet_heavy, explosion, **impact**, fire, melee, electricity, grapple_pull — and a per-vehicle `impact_damage_factor` (1 on the tank profile, 0 on the armoured one) | `impact_damage_factor` (dealer side), `deform_scale`, per-channel armour | decoded (`DAMAGE_MODEL.md` §3, §"6 values") |
| 8 | **weapon reaction to the car** | the car's own weapons + the game's heat system | the donor chassis carries 0 weapon slots; the build's weapons are its own | nothing traffic-specific | decoded (`MODLOG` G2-12: civilian 0 weapon slots) |

**Derived:** of the eight controls, **#1 is authored by this build** (and must stay "no match"),
**#7 is authored by this build** (a real member), **#3-#6 are engine-side** and only readable, and
**#2 is authored by the game** — a mod that edits `global.blo` changes traffic for the whole province,
not for one car. That asymmetry is why the plan has one edit and five verifications.

---

## 2. BmAK's requirement, behaviour by behaviour

BmAK evidence is deliberately thin where the files are thin. What the BmAK grab actually settles:

| BmAK fact | value | file |
|---|---|---|
| the Batmobile **sideswipes and rams traffic** | observed in play (user, 2026-10-26) + targeting state `SideSwipeTargetsList` (`RInteractionClass`), `SideSwipeInSweetSpot`, `CrushedThisFrame` / `BouncedThisFrame`, functions `GetSideSwipeTarget` / `GetCurrentSideSwipeTarget` / `GetBatmobileDodgeDirection` | `DAMAGE_RULES.md` §3.3.1 |
| ram damage band and multipliers | `ImpactMinDamageSpeed` **20** / `ImpactMaxDamageSpeed` **150** (Joker 40/180); battle **120 / 540**; `ImpactStrafeMod` **2.25** (Joker 0.8); `ImpactBoostMod` **2.0** | `DAMAGE_RULES.md` §3.3 |
| **hostiles shoot at the car**, and the car knows who | `FBatmobileWeaponWarningContainer` = `AttackingActor` + `StillRelevant` + per-weapon `WeaponWarning` + `AudioEvent`; `AddWeaponWarning(...)`, `TickWeaponWarnings(DeltaTime)` | `RVehicleBatmobileBase.g.cs` via `tmp/freebuff/reports/horn-and-siren-plan.md` §2.1 |
| civilians are a **target class** for the car's missile | `RBatmobileEMPMissile.CivilianMissileLockOnDuration` = **4** | `FOOTAGE.md:123` |
| civilians **yield / swerve / flee** from the Batmobile | **no member, no animation name, no event** found | **UNKNOWN** — settles: BmAK pawn/traffic AI package (`RPawn*`/`RTraffic*` bodies), not in the current grab |

So: ram/sideswipe, being-shot-at and civilian-targeting are **lore-evidenced**; yielding and fleeing
are **lore-plausible but unevidenced** and must not be written as requirements.

---

## 3. The six behaviours: carrier, edit, evidence, pilot card

### R1 — Civilian cars make way (yield / brake / lane-change)

**BmAK requirement:** UNKNOWN (no member). **JC3 carrier:** the vanilla traffic driver tree
(`ai/bts/civilian/civilian_car_driving.btc`, name decoded; body not). **Build edit: none.** Traffic
stays exactly as the game ships it — the Batmobile is not in traffic, so JC3's civilian cars keep
reacting to *each other* and to Rico on foot exactly as vanilla.

*Why no edit:* the only data lever for "civilians avoid X" is `global/global.blo`'s rule/selector set,
which is province-wide and would change every car in the game, not one; and no member tying avoidance
to a specific vehicle exists in any decoded file (`TRAFFIC.md` §6: the picker is native).

**Pilot card P1 — yield.**
*Drive at 50 km/h along a town's main road into 20 oncoming civilian cars: ≥ 14 of 20 slow down, change lane or stop before contact and ≤ 3 contact the Batmobile. Pass band: ≥ 14/20 avoid, ≤ 3 hits; below 10/20 the vanilla tree is not doing avoidance and R1 is recorded as UNKNOWN-not-carried.*

### R2 — Pedestrians and civilians flee (panic)

**BmAK requirement:** UNKNOWN. **JC3 carrier:** the civilian behaviour trees
(`civilian_std.btc`, `priest_heat_clearer.btc`) and JC3's own weapon-fire reactions. **Build edit:
none.** The Batmobile's weapons are ordinary entity weapons, so whatever panic JC3 runs on gunfire
or explosions applies unchanged.

**Pilot card P2 — flee.**
*Fire the cannon into the ground 8 m from a group of 10+ civilians in a settlement: ≥ 8 leave a 15 m radius within 4 s and none stand still. Pass band: ≥ 8/10 flee inside 4 s; a lower count means the panic path is not reached and R2 stays UNKNOWN.*

### R3 — No NPC-driven Batmobiles (MOD-5 / WLD-8)

**BmAK requirement:** decoded as a project requirement (`GRAB_BACKLOG.md` MOD-5 "nobody but the player
drives it", WLD-8 "no traffic/NPC Batmobiles"). **JC3 carrier:** the tag→selector match in control #1.
**Build edit (the guard, and the only traffic edit in this plan):**

| file | member / field | value | rule |
|---|---|---|---|
| `settings/spawn_vehicle_defs.bin` (dropzone override, RTPC) | the Batmobile leaf's record: `tags` | **`vehicle,batmobile`** — exactly as shipped today | must **never** gain `ambient`, `car`, `ground` or `liberated`: `ambient,ground,car,liberated,-highend` is the selector that pulls a record into `03_CivilianCarLiberatedProvince`, and it matches on **presence** of those four tags |
| same | `entity` | the `_debug` leaf path | stays the proven spawn target (`MODLOG` Q-1a) |
| same | `select` / `debug` | 1 / `vehicle|ground|rebel` | unchanged from B-13c |

Evidence: **decoded** (tags, selector, match count 0/41 re-checked by `bm_rebel --check`).
**UNKNOWN:** whether the engine's picker tests supersets (native; `TRAFFIC.md` §6) — so the guard is
"add no tag", which is safe under either reading.

**Pilot card P3 — no NPC copies.**
*Drive 10 minutes through two towns and one military base: count Batmobiles not driven by the player = **0**, and the Rebel Drop list shows exactly one Batmobile entry. Pass band: 0 NPC copies in 10 minutes and 20+ traffic records observed in the same run (so the zero is not "no traffic spawned").*

### R4 — Faction vehicles engage the Batmobile

**BmAK requirement:** decoded — the car expects **attackers** (`FBatmobileWeaponWarningContainer.AttackingActor`, `TickWeaponWarnings`). **JC3 carrier:** the game's existing heat/chaos response:
`global/heat.bl` / `global/heat.blo` (responder escalation) and `settings/heat.gadfc`, with responders
drawn from `settings/spawn_combatant_defs.bin` (67 records). **Build edit: none.** The Batmobile is
Rico's vehicle, so heat raised on Rico already sends military and, in occupied provinces, the army at
the car; nothing in the car's data suppresses it.

What would need an edit: the car's **faction identity**, and that is a decision, not a member —
`settings/factions.bin` ships (`INDEX`), but its layout is not decoded, so "make the car read as rebel
to the army" is **UNKNOWN** and settles in that file. Until then the car is faction-neutral, which is
what a player vehicle already is.

**Pilot card P4 — factions engage.**
*Raise heat to the level that spawns military responders (destroy three military vehicles), then drive for 60 s: ≥ 2 military vehicles pursue and ≥ 1 opens fire on the car within 30 s, and the car takes damage from gunfire (health drops). Pass band: ≥ 2 pursuers, ≥ 1 firing, health loss > 0 within 60 s; zero pursuers means the heat system does not see the car and R4 needs the `heat.blo` decode.*

### R5 — Ram and sideswipe damage traffic (BmAK's signature move)

**BmAK numbers (decoded):** band 20→150 km/h (battle 120→540), `ImpactStrafeMod` **2.25**,
`ImpactBoostMod` **2.0**. **JC3 carrier:** the car's own `VehicleDamage` module — the `impact` channel
plus `impact_damage_factor` (the dealer-side multiplier; the tank profiles carry 1 and 0) and
`deform_scale`. **Build edit (the one real member):**

| file | member | donor | build | derivation |
|---|---|---|---|---|
| `Builds/test-0NN/aaf/editor/entities/jc_vehicles/01_land/<chassis>/modules/default/<chassis>_vehicle_damage.vmodc` | `impact_damage_factor` | 1 | **2.25** | BmAK's `ImpactStrafeMod` — the only ratio BmAK gives for a sideswipe, applied as the dealer multiplier |
| same | `deform_scale` | 1 | **1** (keep) | BmAK deforms victims; changing this scales the *victim's* deform, and no BmAK number exists for it |
| same | `impact_armor` / `impact_armor_strength` | 0 @ 0 | **keep 0** | the car should be hurt by ramming less than it hurts |

Evidence: member and donor values **decoded** (`DAMAGE_MODEL.md`); the mapping from
`ImpactStrafeMod` to `impact_damage_factor` is **derived** (two multipliers, same role). **UNKNOWN:**
whether a JC3 *player* vehicle deals impact damage to AI vehicles at all — BmAK's `CanBatmobileDoImpactDamage`
is native and JC3's impact path was not exercised by this project; settles with pilot card P5.

**Pilot card P5 — ram.**
*Hit a civilian car head-on at 60 km/h, then sideswipe a parked one at 40 km/h: the struck car deforms visibly, is displaced ≥ 3 m (ram) / ≥ 2 m (sideswipe) and is disabled or destroyed within 2 hits, while the Batmobile loses ≤ 10 % health per hit. Pass band: 2/2 victims damaged on the first hit and ≤ 10 % self-damage; a victim that takes no damage means `impact_damage_factor` is not read for a player vehicle and R5 is UNKNOWN-not-carried.*

### R6 — Civilian traffic density around the Batmobile (the Arkham "empty streets" question)

**BmAK requirement:** UNKNOWN in data. What *is* decoded is that BmAK's Batmobile shares space with
traffic and can hit it (R5), so "streets empty of civilians" cannot be claimed as a BmAK requirement —
and no JC3 member sets traffic density per vehicle (`spawn_vehicle_defs.bin` selects *which*, not *how
many*; budget pools are named in `settings/spawn_budget_pools.bin`, `TRAFFIC.md` §2). **Build edit:
none.** Recorded as a named omission rather than a behaviour: JC3 keeps its own density.

**Pilot card P6 — density unchanged.**
*Count civilian vehicles passing a fixed junction for 60 s in a liberated province, three times: the count must match a vanilla-save baseline of the same junction within ±20 %. Pass band: 3/3 runs inside ±20 %; a larger swing means an `spawn_*` file leaked into the dropzone.*

---

## 4. The build edits, in one table

| # | file | member / field | from → to | evidence | settles if wrong |
|---|---|---|---|---|---|
| B1 | `settings/spawn_vehicle_defs.bin` (dropzone) | Batmobile record `tags` | `vehicle,batmobile` → **unchanged** | decoded; 0/41 selectors match | native picker (`TRAFFIC.md` §6) |
| B2 | `<chassis>_vehicle_damage.vmodc` | `impact_damage_factor` | **1 → 2.25** | decoded member, derived value (`ImpactStrafeMod`) | `VehicleDamage` impact consumer in `JustCause3.exe` |
| B3 | `<chassis>_vehicle_damage.vmodc` | `impact_armor`, `impact_armor_strength` | 0 @ 0 → **0 @ 0** (keep) | decoded | same |
| B4 | `modules/default/ai/<chassis>_land_global_ai.vmodc` | — | **keep the module** | decoded: the donor ships it (`TRAFFIC.md` §6); a player car is not selected into a Driver seat, so it is inert | whether a player-driven entity loads it |
| B5 | `settings/factions.bin` | — | **no edit** | file ships, layout **UNKNOWN** | that file's decode |
| B6 | `global/heat.bl(.blo)`, `settings/heat.gadfc` | — | **no edit** | files ship, contents **UNKNOWN** | `heat.blo` decode |

**Revert** for B2: restore `<chassis>_vehicle_damage.vmodc` from the donor copy in the build's AAF tree
(`Builds/test-091/aaf/.../modules/default/`, byte-identical round-trip proven via `ConvertAdf`,
`MODLOG.md` §0), rebuild, reinstall. B1 and B4 are "do not change", so their revert is "do not".

**Do not** touch `global/global.blo`: adding a rule would change traffic province-wide, and the
selector→rule pairing there is positional only, not a decoded schema (`TRAFFIC.md` §3).

---

## 5. UNKNOWNs, each with the file that settles it

| # | unknown | why it matters | settler |
|---|---|---|---|
| U1 | does the traffic tag matcher test supersets? | whether B1's tag list is safe by construction | native picker in `JustCause3.exe` (`TRAFFIC.md` §6) |
| U2 | what `settings/factions.bin` contains (relationship matrix? ids?) | whether the car can be given a faction identity | that file's decode; no tool in this project reads it yet |
| U3 | what `global/heat.blo` escalates on, and which responders it spawns | whether the car is targeted as Rico's vehicle or ignored | `global/heat.blo` decode |
| U4 | the bodies of `civilian_car_driving.btc` / `civilian_std.btc` | whether JC3 civilians yield at all (R1) | the `.btc` files in `ai/bts/` — names decoded, bodies not |
| U5 | whether the impact channel fires for a player-driven vehicle | R5's whole premise | the `VehicleDamage` consumer in `JustCause3.exe`; pilot card P5 |
| U6 | BmAK's own civilian-yield / flee behaviour | whether R1/R2 are lore requirements at all | BmAK pawn/traffic AI package — not in the current grab |
| U7 | whether `AITrafficImpostorSystem` reuses the same spawn records | whether a distant Batmobile could appear without a record match | `TRAFFIC.md` §6 (G2-29 leaves it open) |

## 6. Change record

1. **Intended change:** add one plan stating how JC3 traffic and AI should treat the Batmobile, which
   JC3 control carries each behaviour, the single member edit that carries BmAK's ram numbers, and a
   pass-banded pilot card per behaviour.
2. **File:** `tmp/freebuff/reports/traffic-and-ai-reaction-to-batmobile-plan.md` — the brief names it and
   every comparable plan lives in `tmp/freebuff/reports/`; no file in `Working/`, `Research/`,
   `Builds/`, the archive or the game install is modified.
3. **Revert:** delete this file. Nothing else changed; no game launched, no build packed, no install
   written, no git.

**Limits.** Static only. BmAK's civilian reaction is unevidenced and is not asserted anywhere above;
the JC3 side's faction and heat tables ship but were not decoded, so R4 is a verification, not a build
claim. The ram edit is the one change this plan proposes, and its premise (impact damage for a player
vehicle) is the one thing pilot card P5 must prove.
