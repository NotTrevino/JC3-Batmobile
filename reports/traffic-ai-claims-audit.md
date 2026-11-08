# Traffic/AI claims audit: 56 numbered claims, 18 supported, 3 contradicted, 15 partial, 20 UNKNOWN

**Task.** Split `tmp/freebuff/reports/traffic-and-ai-reaction-to-batmobile-plan.md` into a numbered list of
claims — one per sentence that states a rule or a number — and for each, find the `Research/JC3Grab/` AI or
traffic file it implies, recording the file and line that supports or contradicts it. Claims with no file
are **UNKNOWN** and name the file that would settle them. The plan was not edited.

**Result.** 56 claims: **43 analytic claims** (18 supported, 3 contradicted, 15 partial, 7 UNKNOWN), **6
pilot-card bands** (UNKNOWN as data by design — they are the test, not a source) and **7 self-declared
UNKNOWNs**, each already naming a settler.

**Three claims are contradicted by the grab, and all three are in the build-edit table** — the part a
builder would act on:

1. **B2's `1 → 2.25`** says `impact_damage_factor` is 1 in the build. `DAMAGE_MODEL.md:50` gives the build
   column (`Builds/test-091`) as **0**. The edit is `0 → 2.25`.
2. **B3's `0 @ 0 → keep 0`** for `impact_armor` / `impact_armor_strength` quotes the **donor's** row.
   `DAMAGE_MODEL.md:43` gives the build as **5000 @ 100**. "Keep 0" would be a regression, not a no-op.
3. **§1's "11 behaviour-tree paths in `civilian/` + `vehicle/`"** — `INDEX.jsonl:58-61` has **4** in
   `civilian/`, and there is no `ai/bts/vehicle/` directory; the vehicle trees sit under
   `ai/bts/01_micro_behaviors/vehicle/` (`INDEX.jsonl:30-55`).

Everything else in the plan that the JC3 side can referee holds: the traffic census, the 41 selectors, the
shared timers, the BmAK ram numbers, and the "no per-vehicle avoidance member" absence.

**Labels.** **SUPPORTED** = a JC3Grab file states it at the line given. **CONTRADICTED** = a JC3Grab file
states something different. **PARTIAL** = the cited file supports the mechanism but not the number, or the
number is a derivation the file does not state. **UNKNOWN** = no JC3Grab file states it; the settler is named.

---

## 1. Method

* **One claim per sentence that states a rule or a number.** Sentences that only name the plan's own
  structure ("this plan states…", "Revert: delete this file") are not claims.
* **Search scope.** `Research/JC3Grab/` — chiefly `TRAFFIC.md`, `DAMAGE_MODEL.md`, `STANDALONE.md`,
  `SIGNATURE_DIFF.md`, `INDEX.jsonl`. BmAK-side claims imply files under `Research/BatmobileGrab/`; those are
  outside the instructed scope but in-project, so they were read and cited rather than guessed (C21, C22,
  C24). Where even that fails (C23), the claim is UNKNOWN with the settler named.
* **Searching is not proving.** `INDEX.jsonl` proves a file **ships**, never what it contains; a row scored
  SUPPORTED on an INDEX line is supported *as a file-existence claim* only.
* Line numbers are the files' own, as returned by search.

---

## 2. Claims — summary and §0

| # | claim | file:line | verdict |
|---:|---|---|---|
| C1 | "JC3 has **no traffic-reacts-to-a-vehicle system**" | `TRAFFIC.md:139` — "no script (`graphs/*.gsc`, `ai/bts/*.btc`) mentions these tags - the picker is native"; §3's 41 selectors are all vehicle-class/faction rules, none keyed on another vehicle | **SUPPORTED** (absence, evidenced) |
| C2 | "the Batmobile is already outside the only one that exists (the tag→traffic-rule picker)" | `TRAFFIC.md:3` and `:117` — "satisfies 1 of the 41 tag selectors … **1 of 41 selectors match**"; the matching selector needs `ambient,ground,car,liberated`, which `vehicle,batmobile` lacks | **SUPPORTED** (derived from the selector list) |
| C3 | "three of the six behaviours are carried by shipped JC3 systems with **no build edit**; two are UNKNOWN on the BmAK side; one — ram damage — is a real, single-member edit" | derived from §3 R1-R6; BmAK half has no JC3Grab file | **PARTIAL** |
| C4 | `civilian_01` is a civilian traffic vehicle: record in `spawn_vehicle_defs.bin`, **13 tags**, **1 of 41** selectors | `TRAFFIC.md:3` (13 tags + 1 of 41), `:41` ("The donor's record, read out of the table (offset 23240)"), `:50` (tag census) | **SUPPORTED** |
| C5 | D-6 was resolved standalone on 2026-10-28 | `GRAB_BACKLOG.md:1800` — outside `Research/JC3Grab/`; the plan's own citation | **UNKNOWN** (settler: that line) |
| C6 | "a genuinely **new entity path does not spawn in game** — proven by two one-variable probes" | no JC3Grab line; it is a runtime result (`MODLOG.md` 2026-11-02). Note `STANDALONE.md:128` cuts the other way on the data: "**101 of 196 distinct spawn leaves are referenced by path with no registry record**" | **UNKNOWN** (settler: `MODLOG.md` 2026-11-02 probes) |
| C7 | the Batmobile rides the vanilla `_debug` leaf; base archive, no registry record, **debug proto tables only → no traffic**, not in the vanilla drop menu | `TRAFFIC.md:52` ("the debug build in `settings/spawn_vehicle_proto_defs.bin`"), `:98`; `STANDALONE.md:103-107` — "The debug builds are the unregistered mass … 169 records, **163** of them unregistered" | **SUPPORTED** |
| C8 | "its spawn record was cloned with tags **`vehicle,batmobile`**, which satisfy **0 of 41** traffic selectors" | derivation holds from `TRAFFIC.md:3` + `:117` (no selector is satisfied without `ambient`/`ground`/`car`/`character`); the **0/41 count itself** is a tool result, not a grab line | **PARTIAL** |
| C9 | "the lore break … is already closed by selection, not by AI" | derived from C4 + C8; no file states the conclusion | **PARTIAL** |
| C10 | "NPC-driven Batmobiles can **only** reappear if someone adds a tag that matches a selector **or** points a traffic record at the leaf. Those two edits are the only failure modes" | `TRAFFIC.md:52` + §7's three routes; the "only two" is not proven — `TRAFFIC.md:139` leaves `AITrafficImpostorSystem` reuse open | **PARTIAL** |

---

## 3. Claims — §1, the eight controls

| # | claim | file:line | verdict |
|---:|---|---|---|
| C11 | `spawn_vehicle_defs.bin`: **86 records**, **8** with a pool key; donor record = path + 13 tags + name, **no pool key** | `TRAFFIC.md:37` ("**86 records**, each `entity path` + `tag list` + `name`"), `:39` ("Only **8** of the 86 records carry a `a|b|c` key"), `:41` | **SUPPORTED** |
| C12 | `ambient` on **32** records, `ambient`+`liberated` on **14**, faction `*_traffic` on **10** | `TRAFFIC.md:134` — "**32 carry `ambient`** and **14 carry both `ambient` and `liberated`** … 10 carry a faction `*_traffic` tag" | **SUPPORTED** |
| C13 | `global/global.blo`: **31** rule names, **41** tag selectors, `Driver` seats bound to **10** `ai/bts/*.bts`, `AITrafficImpostorSystem`, `PCAITrafficImpostorSystem` | `TRAFFIC.md:105` ("**31 traffic-rule names**, **41 tag selectors** … and **10 AI behaviour-tree paths**"), `:138` (both impostor systems) | **SUPPORTED** |
| C14 | behaviour trees: **"11 paths in `civilian/` + `vehicle/`"**, incl. `civilian_std.btc`, `civilian_car_driving.btc`, `civilian_car_passenger.btc`, `priest_heat_clearer.btc` | `INDEX.jsonl:58-61` — exactly **4** `ai/bts/civilian/*.btc`, those four names. No `ai/bts/vehicle/` path exists; the vehicle trees are `ai/bts/01_micro_behaviors/vehicle/*.btc` (`INDEX.jsonl:30-55`, ~26 files) | **CONTRADICTED** |
| C15 | `settings/factions.bin` ships; **layout not decoded** | `INDEX.jsonl:61518-61519` — `settings/factions.bin`, **908 B**, base + patch. Contents: no JC3Grab decode | **PARTIAL** (ships ✓, layout claim unverifiable) |
| C16 | `global/heat.bl`, `global/heat.blo`, `settings/heat.gadfc` ship; contents not decoded | `INDEX.jsonl:38930` (heat.bl 390,432 B), `:38932` (heat.blo 109,528 B), `:61524-61525` (heat.gadfc 10,632 B) | **PARTIAL** |
| C17 | `spawn_combatant_defs.bin` **67 records**, `spawn_encounter_defs.bin` **56** | `TRAFFIC.md:89` (`settings/spawn_combatant_defs.bin \| base \| 67`), `:92` (`settings/spawn_encounter_defs.bin \| base \| 56`) | **SUPPORTED** |
| C18 | `VehicleDamage` carries **8 channels** incl. `impact`; `impact_damage_factor` **1 on the tank profile, 0 on the armoured one** | `DAMAGE_MODEL.md:20` ("8 channels: bullet, bullet_heavy, explosion, impact, fire, melee, electricity, grapple_pull"), `:50` (`impact_damage_factor / deform_scale \| 1 / 1 \| 1 / 1 \| 0 / 0`, columns donor / medium tank / build) | **SUPPORTED** (tank 1, build 0) |
| C19 | "the donor chassis carries **0 weapon slots**" | `SIGNATURE_DIFF.md:544` — "the civilian has **0 weapon slots** and the variant 1" | **SUPPORTED** |
| C20 | of the eight controls, #1 and #7 are authored by this build, #3-#6 engine-side and only readable, #2 authored by the game | derived; `TRAFFIC.md:105` (rules live in `global.blo`) supports the #2 half only | **PARTIAL** |

---

## 4. Claims — §2, BmAK's requirement

| # | claim | file:line | verdict |
|---:|---|---|---|
| C21 | the Batmobile sideswipes and rams traffic; targeting state `SideSwipeTargetsList`, `SideSwipeInSweetSpot`, `CrushedThisFrame`/`BouncedThisFrame`, `GetSideSwipeTarget`/`GetCurrentSideSwipeTarget`/`GetBatmobileDodgeDirection` | `Research/BatmobileGrab/DAMAGE_RULES.md:175` (`SideSwipeTargetsList \| RInteractionClass \| the candidate set a sideswipe picks from`), `:274` (`CanBatmobileDoImpactDamage` native + `CalculateAndStoreImpactDamage`) | **SUPPORTED** (outside JC3Grab; read in-project) |
| C22 | ram band **20 → 150** (Joker 40/180); battle **120 / 540**; `ImpactStrafeMod` **2.25** (Joker 0.8); `ImpactBoostMod` **2.0** | `DAMAGE_RULES.md:151-153` (`ImpactMaxDamageSpeed 150 \| 180`, `ImpactMinDamageSpeed 20 \| 40`, `ImpactStrafeMod 2.25 \| 0.8`), `:145-147` (`BattleModeImpactMaxDamageSpeed 540`, `…Min… 120`, `ImpactBoostMod 2`) | **SUPPORTED** |
| C23 | hostiles shoot at the car and the car knows who: `FBatmobileWeaponWarningContainer` = `AttackingActor` + `StillRelevant` + per-weapon `WeaponWarning` + `AudioEvent`; `AddWeaponWarning`, `TickWeaponWarnings` | cited as `RVehicleBatmobileBase.g.cs` via `tmp/freebuff/reports/horn-and-siren-plan.md` §2.1 — not in `Research/JC3Grab/`, not in `Research/BatmobileGrab/` | **UNKNOWN** (settler: `Working/vendor/BmSDK/RVehicleBatmobileBase.g.cs`) |
| C24 | `RBatmobileEMPMissile.CivilianMissileLockOnDuration` = **4** | `Research/BatmobileGrab/FOOTAGE.md:123` — `\| lock time \| 4 \| \`RBatmobileEMPMissile.CivilianMissileLockOnDuration\` \| 1 \|` | **SUPPORTED** |
| C25 | civilians yield / swerve / flee from the Batmobile: **no member, no animation name, no event** found | no JC3Grab or BmAK line; the plan's own absence result | **UNKNOWN** (settler: BmAK pawn/traffic AI package, `RPawn*`/`RTraffic*` bodies) |

---

## 5. Claims — §3, the six behaviours and their pilot bands

| # | claim | file:line | verdict |
|---:|---|---|---|
| C26 | R1 carrier is `ai/bts/civilian/civilian_car_driving.btc`; build edit none | `INDEX.jsonl:58` (path + hash `6796389B`, 92,278 B); body undecoded — `TRAFFIC.md:139` | **SUPPORTED** (file ships; contents UNKNOWN) |
| C27 | "the **only** data lever for 'civilians avoid X' is `global.blo`'s rule/selector set, which is **province-wide**" | `TRAFFIC.md:105` (the 31 rules / 41 selectors live in that one file) + `:139`; "only" and "province-wide" are the plan's inference, not stated | **PARTIAL** |
| C28 | R2 carriers are `civilian_std.btc` and `priest_heat_clearer.btc`; no edit | `INDEX.jsonl:60` (`civilian_std.btc`, 294,850 B), `:61` (`priest_heat_clearer.btc`, 35,677 B) | **SUPPORTED** (files ship) |
| C29 | R3 guard: the record must **never** gain `ambient`, `car`, `ground` or `liberated`, because `ambient,ground,car,liberated,-highend` pulls a record into `03_CivilianCarLiberatedProvince` and matches on **presence** | `TRAFFIC.md:3` (that exact selector + rule), `:134` ("the matching selector asks for exactly `ambient,ground,car,liberated`") | **SUPPORTED** |
| C30 | R3: the entity stays the `_debug` leaf; `select`/`debug` = 1 / `vehicle\|ground\|rebel`, unchanged from B-13c | `MODLOG.md` B-13c — outside JC3Grab; the field values are not in any grab file | **UNKNOWN** (settler: `MODLOG.md` B-13c entry) |
| C31 | UNKNOWN: whether the engine's picker tests **supersets** | `TRAFFIC.md:139` — "no file in the archive states that a rule selecting `ambient,ground,car,liberated,-highend` takes records whose tags are a superset" | **SUPPORTED** (as an accurate UNKNOWN) |
| C32 | R4 carrier is the heat/chaos response: `global/heat.bl`/`.blo`, `settings/heat.gadfc`, responders from `spawn_combatant_defs.bin` (**67**) | `TRAFFIC.md:89` (67 records ✓); escalation behaviour itself: no decode (`INDEX.jsonl:38930/38932/61524`) | **PARTIAL** |
| C33 | "the car is faction-neutral, which is what a player vehicle already is" | `INDEX.jsonl:61518` shows `factions.bin` ships (908 B); no JC3Grab decode of its matrix | **PARTIAL** |
| C34 | R5 carrier is the car's own `VehicleDamage`: `impact` channel + `impact_damage_factor` + `deform_scale`; "the tank profiles carry 1 and 0" | `DAMAGE_MODEL.md:20`, `:50`, `:243` (`\| \`impact\` \| \`0@0\` x220, \`5@100\` x13 \|`) | **SUPPORTED** |
| C35 | R6: "no JC3 member sets traffic density per vehicle"; `spawn_vehicle_defs.bin` selects *which*, not *how many*; budget pools named in `settings/spawn_budget_pools.bin` | `TRAFFIC.md:37` ("`settings/spawn_budget_pools.bin` names it as *Ground Vehicles*"); "which, not how many" is the plan's inference from an undecoded numeric block (`TRAFFIC.md:139`) | **PARTIAL** |
| C36 | P6: density must match a vanilla baseline within **±20 %**, **3/3** runs | none — a test band | **UNKNOWN** (settler: the run itself) |

**Pilot-card bands** (numbers the plan states that no file can source — each is a pass band, not a data
claim, and each names its own failure mode):

| # | band | verdict |
|---:|---|---|
| P1 | 50 km/h, 20 oncoming cars, **≥ 14/20** avoid, **≤ 3** contact; below **10/20** → UNKNOWN-not-carried | **UNKNOWN** (settler: the P1 run) |
| P2 | 10+ civilians, **≥ 8/10** leave a **15 m** radius within **4 s** | **UNKNOWN** (settler: the P2 run) |
| P3 | 10 minutes, 2 towns + 1 base, **0** NPC Batmobiles, **20+** traffic records observed | **UNKNOWN** (settler: the P3 run) |
| P4 | **≥ 2** pursuers, **≥ 1** firing within **30 s**, health loss **> 0** within **60 s** | **UNKNOWN** (settler: the P4 run) |
| P5 | 60 km/h ram / 40 km/h sideswipe, displace **≥ 3 m** / **≥ 2 m**, disabled within **2 hits**, self-loss **≤ 10 %**/hit | **UNKNOWN** (settler: the P5 run — the plan itself says this is R5's whole premise) |
| P6 | junction count within **±20 %** of baseline, **3/3** runs | **UNKNOWN** (settler: the P6 run) |

---

## 6. Claims — §4, the build-edit table (where the contradictions are)

| # | claim | file:line | verdict |
|---:|---|---|---|
| C37 | B1: the Batmobile record's `tags` stay `vehicle,batmobile` | `MODLOG.md` B-13c (outside JC3Grab); the selector semantics that make it safe: `TRAFFIC.md:3`, `:134` | **PARTIAL** |
| C38 | B2: `impact_damage_factor` **1 → 2.25** | `DAMAGE_MODEL.md:50` — `\| \`impact_damage_factor\` / \`deform_scale\` \| 1 / 1 \| 1 / 1 \| **0 / 0** \|`, columns donor / medium tank / **build**. The build's value is **0**, so the edit is `0 → 2.25`, and the "from" is the donor's number, not the build's | **CONTRADICTED** |
| C39 | B3: `impact_armor`, `impact_armor_strength` **0 @ 0 → 0 @ 0 (keep)** | `DAMAGE_MODEL.md:43` — `\| \`impact_armor\` @ strength \| 0 @ 0 \| 0 @ 0 \| **5000 @ 100** \|`; `:53` repeats it in the six-value diff list ("`impact_armor` 0 -> 5000, `impact_armor_strength` 0 -> 100"). The build already carries the raised pair; "keep 0" would undo it | **CONTRADICTED** |
| C40 | B4: the donor ships `…_land_global_ai.vmodc`; keep it, inert because a player car is never selected into a Driver seat | `TRAFFIC.md:138` (the module path, "3 module files in the entity's `modules/` tree"); "inert" is unproven | **PARTIAL** |
| C41 | B5: **no edit** to `settings/factions.bin` | `INDEX.jsonl:61518` (ships, 908 B); layout undecoded | **PARTIAL** |
| C42 | B6: **no edit** to `global/heat.bl(.blo)` / `settings/heat.gadfc` | `INDEX.jsonl:38930`, `:38932`, `:61524` (all ship); contents undecoded | **PARTIAL** |
| C43 | revert B2 by restoring `<chassis>_vehicle_damage.vmodc` from the donor AAF copy; byte-identical round trip via ConvertAdf | `MODLOG.md` §0 — outside JC3Grab | **UNKNOWN** (settler: `MODLOG.md` §0) |

---

## 7. Claims — §5, the self-declared UNKNOWNs (each already names its settler)

| # | unknown | verdict | settler the plan names |
|---:|---|---|---|
| U1 | does the traffic tag matcher test supersets? | **UNKNOWN** (documented at `TRAFFIC.md:139`) | native picker in `JustCause3.exe` |
| U2 | what `settings/factions.bin` contains (relationship matrix? ids?) | **UNKNOWN** (file ships: `INDEX.jsonl:61518`; no decoder in this project) | that file's decode |
| U3 | what `global/heat.blo` escalates on, and which responders it spawns | **UNKNOWN** (`INDEX.jsonl:38932` shows it ships at 109,528 B; no decode) | `global/heat.blo` decode |
| U4 | the bodies of `civilian_car_driving.btc` / `civilian_std.btc` | **UNKNOWN** (files at `INDEX.jsonl:58`/`:60`; bodies not decoded) | those `.btc` files in `ai/bts/` |
| U5 | whether the `impact` channel fires for a player-driven vehicle | **UNKNOWN** (`DAMAGE_MODEL.md:43/50` give the values, not the consumer) | the `VehicleDamage` consumer in `JustCause3.exe`; P5 |
| U6 | BmAK's own civilian-yield / flee behaviour | **UNKNOWN** (C25) | BmAK pawn/traffic AI package (not grabbed) |
| U7 | whether `AITrafficImpostorSystem` reuses the same spawn records | **UNKNOWN** (`TRAFFIC.md:139` — "Whether the impostor system reuses the same records … UNKNOWN") | `TRAFFIC.md` §6 / G2-29 |

---

## 8. Tally

| verdict | count |
|---|---:|
| SUPPORTED | **18** |
| CONTRADICTED | **3** |
| PARTIAL | **15** |
| UNKNOWN (7 analytic + 6 pilot + 7 self-declared) | **20** |
| **rows** | **56** |

Reconciliation: 43 analytic claims = 18 + 3 + 15 + 7; plus 6 pilot bands and 7 declared UNKNOWNs = 56.

The plan is **substantively sound where it describes JC3** — the census (86 records / 8 pool keys / 13
tags), the selector count (1 of 41 for the donor), the 32/14/10 tag split, the 31 rules and 10 behaviour
trees, the 67/56 spawn-record counts, the 8 damage channels and the 0 weapon slots all reproduce exactly at
the lines above. Its weaknesses are concentrated in two places: **the build-edit table**, where the donor
column is presented as the build's (C38, C39), and **the behaviour-tree count**, where 4 files became 11 and
a non-existent `ai/bts/vehicle/` directory was invented (C14).

## 9. Limits

* Static reads only: `TRAFFIC.md`, `DAMAGE_MODEL.md`, `STANDALONE.md`, `SIGNATURE_DIFF.md`,
  `INDEX.jsonl`, plus `DAMAGE_RULES.md` / `FOOTAGE.md` for the BmAK-side claims. No archive was re-read, no
  `.bin` decoded, no game run.
* `INDEX.jsonl` proves existence and size only; every "ships ✓" verdict is that narrow claim, and the
  companion "contents undecoded" is stated wherever it applies.
* C5, C6, C30, C43 cite root-level documents (`GRAB_BACKLOG.md`, `MODLOG.md`) that are outside
  `Research/JC3Grab/`; they are marked UNKNOWN **for this scope**, not necessarily unknown to the project.
* Pilot bands are scored UNKNOWN because no file can source a pass band; that is not a defect in the plan,
  which labels them as tests.

## 10. Revert

Delete this file. Nothing else was created or changed.
