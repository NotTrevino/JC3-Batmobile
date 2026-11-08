# Decisions needed from the operator

**What this is.** `Working/Translation/BLOCKED_PROPOSALS.md` lists 17 translation rows that are not
in the build. Most are waiting for a *missing piece of evidence* - a decoded member, a writer, a
bank. Four are waiting for **you to choose**: the evidence is in, or the block's stated reason is
false, and no further reading will settle it.

This sheet states each one in plain terms: what the row is, what it said it was waiting for, the
evidence that changes that, the options, what each option costs in BmAK lore accuracy, and a
**recommendation** (labelled as one - it is not a decision). **No row has been edited.** Every
quote below is from a file in this repository, with its path and line number.

Rows in this sheet are read-only by design: `T_ROWS.jsonl` is sha256-pinned by
`Tools/scripts/t_blocked.py --check`, so applying any of these options means editing the ledger and
the proposals file together, not before you have chosen. **Exception, 2026-11-06:** `T-WLD4`,
`T-WLD6` and `T-WLD11` were closed in the ledger (new pin
`e2b7e3b14f53bd9c517e9af73f0aa6e4f2669eddbd45f7ea4fd9143f5e85e309`) on decoded evidence - the
name/description pairs are `HashJenkins(leaf)` / `HashJenkins(leaf + "_desc")` = 1621485476 /
4081821928, present 11/11 in bm-013's drop, and the 22 stunt-area vertices have a derived spine
fit. See `tmp/freebuff/reports/apply-world-text-rows.md`.

| # | row | doc | what it needs from you |
|---:|---|---|---|
| 1 | `T-ST7` | T-3 steering | choose 0.25 s (BmAK's value) or keep 0.8 / 0.6 s |
| 2 | `T-FX3` | T-2b effects | approve the decoded afterburner-flame edit, or keep the omission |
| 3 | `T-WP13` | T-7 weapons | accept JC3's 2 driver slots, or leave the row blocked |
| 4 | `T-WP4` | T-7 weapons | approve splitting it so the missile launcher can ship |

---

## 1. `T-ST7` - the Batmobile's steering lock time

**The row.** `Working/Translation/T_ROWS.jsonl:91` (doc T-3). BmAK's Batmobile turns at
**220 °/s** with a **55°** lock, so it reaches full lock in **0.25 s** (55 / 220; *derived*). The
translation row currently says **0.8 s at low speed / 0.6 s at high speed** and is marked

> `**blocked**: 55° lock at 220 °/s is 0.25 s, and the fleet's fastest rack is 0.5 s; JC3's
> steering model cannot be that quick, so the table keeps 0.8 s inside the family`

**What it was waiting for.** A JC3 limit: the claim that *no* JC3 vehicle can be quicker than
0.5 s to full lock, so 0.25 s would be inventing a capability the engine does not have.

**The evidence that refutes it.**

- `Working/Translation/T_ST7B_FLOOR.md:16` - `| \`MotorbikeSteering\` player (bikes) | 0.3 | 2 | 9 |`
  i.e. **player** bike modules ship **0.3 s** today, on 2 modules, with 9 modules below 0.5 s. The
  player steering path is therefore not floored at 0.5 s.
- `Working/Translation/T_ST7B_FLOOR.md:17` - `| \`LandSteering\` AI twin | 0.25 | 4 | 4 |`: **0.25 s
  ships in 4 `LandSteering` AI twins**, on the same member, same parser, same type as the player car.
- `Working/Translation/T_ST7B_FLOOR.md:19-20` - "**A player module does ship below 0.5 s**: the bikes
  (`MotorbikeSteering`) carry **0.3 s** on 2 player modules, so the player steering path is not
  floored at 0.5 in the data".
- `Working/Translation/T_ST7B_FLOOR.md:10` - the census is **6,045** decoded modules over **232**
  entities, **271** of them steering modules - not a sample.
- `Research/JC3Grab/DRIVE_CARRIERS.json:600` - `"path": "t_to_full_steer_s"`: the member is decoded
  per module, so every value above is data, not inference.

**What is still true, and must not be overstated.** No *player car* ships below **0.5 s**
(`T_ST7B_FLOOR.md:26-29`: the car minimum is 0.5 s on 6 modules; the best player car rate is
80 °/s against BmAK's 220 °/s). So 0.8 s is *in family* - but it is in family **by convention, not
by a limit**, and the row's stated reason is false. The honest label is "compromise", not "model
limit".

### The options

| option | what it means | BmAK lore accuracy | cost / risk |
|---|---|---|---|
| **A. 0.25 s** (route R1) | write `0.25` into the player car's `t_to_full_steer_s` (`T_ST7B_FLOOR.md:43-44`: member at **+8**, file byte **88**, float bytes `0000803e` = 0.25) | **exact** - matches BmAK's 55° / 220 °/s = 0.25 s | the car would reach full lock **3.2x** quicker than today and **2x** quicker than the fleet's fastest player car; nobody has watched it in play (test ban). If the player path clamps or ignores the value, the build ships a number that does nothing and needs a revert |
| **B. keep 0.8 / 0.6 s** | leave the row as it is | **0.55 s slower** to full lock at low speed (0.8 vs 0.25); the Batmobile would steer like a heavy road car | none mechanically, but the row must stop calling it a JC3 limit - and a false limit in the ledger is itself a lore-accuracy defect |
| **C. 0.5 s** | the fleet's fastest *player car* value | **2x slower** than BmAK (0.5 vs 0.25) | in family by the observable player-car evidence; still unmeasured |
| **D. other** | e.g. 0.3 s via the `MotorbikeSteering` class (route R2), or 0.25 s only on the high-speed member (R3), or reassess the 55° lock (R4 is impossible: it needs 110°, the fleet max is 45°) | varies | each is a different trade; R2 is a module-class amendment, R3 only affects the fast end |

**Recommendation (a recommendation, not a decision): A, 0.25 s - conditional.** It is the only
option that reproduces BmAK's actual lock time with one decoded member and no invention. The
condition is that you accept a **data-only change nobody can measure until a play probe is allowed**;
if that is not acceptable, take **C (0.5 s)** rather than leaving B as-is, because B keeps a false
engine claim in the ledger. Whichever way you choose, T-ST7 stays UNAPPROVED until a probe.

---

## 2. `T-FX3` - the afterburner exhaust flame

**The row.** `Working/Translation/T_ROWS.jsonl` (doc T-2b): it ships no exhaust/boost flame, on the
stated ground that JC3 has no carrier for one.

**Evidence that changes that** - all from `Working/Translation/T_FX3B.md`:

- **line 8**: "Answer: **YES** ... T-FX3's wording ('no usage slot for an exhaust flame') is **wrong
  as an engine claim**".
- **line 62**: "The donor's two emitters carry `usage` = EngineNitro (**4197885156**) ... (decoded,
  `Working/Effects/bm_fx_edits.json`)" - so the donor entity **already** fires under that usage.
- **line 98**: `| 4197885156 | \`EngineNitro\` | 18 | ...` - the usage exists in the decoded 155-value
  vocabulary (`Research/JC3Grab/USAGES.json` contains it 9 times).
- the carrier is the entity `usage_effects` array, not a stat slot, and the fleet ships the dual
  nitro flame `car_cycle_base_dual_nitrous.effc`.

**The decision.** `BLOCKED_PROPOSALS.md:12` records it as "nothing structural ... what is missing is a
decision on which usage raises the flame". `BLOCKED_PROPOSALS.md:38-46` carries the proposed edit
(unapplied) and the one remaining UNKNOWN: whether the game raises `EngineNitro` outside the arcade
nitro stat fields.

### The options

| option | BmAK lore accuracy | cost / risk |
|---|---|---|
| **A. apply the proposed edit** - usage `4197885156` on the donor's two emitters at the `Afterburner` socket | the afterburner gets its flame, on a lawyer-clean decoded usage | the flame's trigger may not fire outside arcade nitro; that would ship a visible effect that never shows, or shows at the wrong time |
| **B. keep the omission** | the afterburner stays flame-less - a visible BmAK feature absent | none; but the ledger must say "no flame" is a choice, not an engine limit |
| **C. other** | a different usage, or attach at a different point | each needs its own decode |

**Recommendation (a recommendation): A.** The row's stated blocker is false and the donor already
carries the usage; shipping it is reversible (one module write) and turns an admitted gap into a
decoded best-effort.

---

## 3. `T-WP13` - eleven weapons in two driver slots

**The row.** `Working/Translation/T_ROWS.jsonl:163` (doc T-7). D-7 asks for **every weapon in both
modes**. JC3 has **at most 2 driver weapon slots** and no way to switch between more.

**Evidence** (`Working/Translation/T7_WEAPONS.md:63`; the row repeats it at `:88`;
`BLOCKED_PROPOSALS.md:18`): "the fleet has **2 driver slots** at most (medium and Bavarium tank:
`main_weapon` + `id:00568A74`); there is no active-slot index, no next/previous weapon action and no
weapon group anywhere in the 232 `.epe` graphs (G2-11 section 2b)". BmAK itself has primary +
secondary + **3 special-weapon states** and a radial wheel.

**This is not a missing decode.** 232 `.epe` graphs were read; nothing carries a third slot. The
choice is between a named omission and an indefinite block.

### The options

| option | BmAK lore accuracy | cost / risk |
|---|---|---|
| **A. accept 2 slots** - cannon + missile (or EMP) on the tank's pair, the other 9 weapons recorded as an approved omission | **9 of 11 weapons unreachable from the driver's seat**; D-7 unmet and must be re-worded as an approved compromise | the build ships a working, honest 2-slot car; nothing waits on an impossible member |
| **B. keep the row blocked** | the same 9 weapons absent - a block does not add them | the row stays red forever, and 3 T-7 deliverables stay undelivered with no decision recorded |
| **C. other** - e.g. Q-3 #3's 3-weapon experiment (fire 3 from one seat), or a HUD-driven wheel | at most a partial recovery | an experiment out of the decoded member set; may not survive play |

**Recommendation (a recommendation): A**, and record the 9-weapon omission as approved. If D-7's
"every weapon" is non-negotiable lore, then the honest statement is that this project cannot meet it,
and the ledger should say so rather than stay blocked.

---

## 4. `T-WP4` - the EMP missile: split it so the launcher can ship

**The row.** `BLOCKED_PROPOSALS.md:74-84` (doc T-7). One row covers two things: the EMP **missile
launcher** and the EMP **disable** effect.

**Evidence.** The launcher half is fully decoded (`Batmobile_EMP_Missile_Launcher`, 3 instances, 63
fields, and the `_ForCars` projectile); the disable half has no member on either side - "no EMP-named
member exists on any NPC `RVehicle*` class" (`T_WP4C_TRACKER_EMP.md`), and JC3's EMP is the truck's
entity-level blast (`Research/JC3Grab/EMP.json`, `truck_emp`). `BLOCKED_PROPOSALS.md:80` proposes an
unapplied `split`: T-WP4a launcher (decoded, buildable), T-WP4b disable (named omission).

### The options

| option | BmAK lore accuracy | cost / risk |
|---|---|---|
| **A. approve the split** | the EMP launcher ships (a real BmAK weapon); the disable stays a named omission | one ledger restructure; the launcher is a normal w618 clone (no invention) |
| **B. leave it as one blocked row** | the launcher stays out too, though it is buildable today | a decoded weapon is withheld because of an unrelated half |
| **C. other** | - | - |

**Recommendation (a recommendation): A.** Splitting costs nothing and unblocks a decoded weapon; the
disable half still waits on evidence (a JC3 member that disables an NPC vehicle, 0 of 88 vehicle
weapon components are a `CEMPWeapon`).

---

## 5. Rows that need evidence, not a decision

Listed so the distinction is explicit: **there is nothing for you to choose here** - each needs a
file that does not exist yet, or a decode that has not been done. They are not on this sheet's
decision list.

| row | doc | still needs |
|---|---|---|
| `T-AU3` | T-2b | a JC3-format bank carrying BmAK's 10 absent banks - all 27 BmAK banks absent 27/27, and no FEV authoring route |
| `T-AU5` | T-3 | the same absence, for the transformation/taser/vehicle-voice events |
| `T-S6` | T-3 | BmAK's numeric stiffness/damping in a known unit (the SDK gives offsets only) and a droop member JC3 does not have |
| `T-WP5` | T-7 | a decoded firing trigger for the entity-level `CForcePulse` (14 unowned pulses, moment UNKNOWN) |
| `T-MD2` | T-15 | the disable half of T-WP4 (same missing member as T-WP4b) |
| `T-MD14` | T-15 | a mode-switch event or a second variant for the 30 battle-mode events |
| `T-HUD5` | T6 | a weapon component on the entity for the HUD's 2 slots |
| `T-CAM8` | T6 | a head-impulse / drift-orientation camera member - none in any decoded camera module |
| `T-CAM9` | T6 | a unit bridge from BmAK camera smoothing strength to JC3 spring stiffness |
| `T-CAM11` | T6 | a numeric bridge to `AddCameraShake` (game code, no values decoded) |

---

## 6. If you say yes - what changes, and what it costs to undo

Nothing here is applied. Each decision would be applied by editing `T_ROWS.jsonl` (the row's cells
and `dispo`) **and** `Working/Translation/BLOCKED_PROPOSALS.md` (its proposal becomes `applied`), and
`Tools/scripts/t_blocked.py --check` would have to be re-run because it pins the ledger's sha256 and
re-derives the blocked set - a row that leaves the blocked set makes that check fail until the
proposals file is regenerated. Undo is the reverse edit; no build artefact is touched by any of the
four decisions except option A of T-ST7 and T-FX3, which are one module value each.

**UNKNOWN on this sheet:** whether any of these choices behaves as predicted in play - the test ban
(INSTRUCTIONS.md section 3) forbids launching the game, so all four recommendations are static
arguments from decoded bytes. T-ST7's option A in particular needs a probe to be called proven.

---
## OPERATOR RULINGS 2026-11-06 (rule: lore accuracy is the only option; a compromise is never taken)
1. **T-ST7: A, 0.25 s** (BmAK 55 deg / 220 deg/s). Also check the steering-rate / max-speed members so the full BmAK rate is carried, not only the lock time. "No player car ships below 0.5 s" is not a reason: AI cars ship 0.25 s and bikes 0.3 s.
2. **T-FX3: approve** the decoded afterburner-flame edit.
3. **T-WP13: force extra weapon slots.** The Imperator Bavarium Tank and Urga Mstitel carry 2 weapons + a shield, so JC3's "2 driver slots" is a convention, not a limit. All BmAK weapons are required.
4. **T-WP4: approve the split** so the missile launcher ships; lead: JC3 Fire Leech (lock-on HUD, heat-seeks after firing) as the lock-on carrier.
5. Colour: reference screenshot = dark charcoal/gunmetal, satin, wet; no daylight shot exists - derive how BmAK produces it from its own materials.
Ledger edits (T_ROWS.jsonl + BLOCKED_PROPOSALS together, re-pin `t_blocked.py`) are carried out by lane briefs 8010-8016; no row was edited by hand.

## OPERATOR LEADS 2026-11-06 (answers to "no JC3 system" questions)
- Winch: model = Rico's grappling hook / tether; no vehicle-cable known.
- Sonar: no JC3 scanner; mission-dependent in BmAK (tracking treadmarks on the road); outside missions a pulse only; lowest weapon priority.
- Two modes: no lead (research the data).
- Hacker/allegiance: SAMs can be hacked and then target enemy aircraft; drones cannot be hacked but can be Rebel Dropped as your own; Vehicle Tracker: some missions and random encounters track a vehicle with distance and a yellow/grey circle.
