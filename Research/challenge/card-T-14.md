# Assumption challenge — card T-14 · Damage and armour translation

Written 2026-10-30. **Read-only review:** no source, generated artefact, build or game file was
modified; the only file written is this one. Nothing was installed into `D:\Games`, no game was
launched, nothing was committed. Running the card's own `--check` paths created only
`Tools/scripts/__pycache__/*.pyc` (git-ignored by `.gitignore:145-146`); `T10_DAMAGE.md`,
`t10_damage_edits.json` and `t10_damage.py` still carry their `10-29 02:46` mtimes.

**In scope:** `GRAB_BACKLOG.md` §0.5 (R1–R14), the T-14 card (§9, `GRAB_BACKLOG.md:902`), its §12
row (`GRAB_BACKLOG.md:1323`), `MODLOG.md` §"T-14 · Damage and armour translation — intended change"
/ "— done" / "T-14 rework — intended change" / "— done" (lines 12966–13090 and 14673–14970), and
the card's outputs: `Tools/scripts/t10_damage.py`, `Working/Translation/T10_DAMAGE.md`,
`Working/Translation/t10_damage_edits.json`, `Working/Translation/damage_switches.json`. Inputs read
where a claim needed testing: `DAMAGE_RULES.md/.json` (G1-14), `DAMAGE_MODEL.md/.json` (G2-28),
`DAMAGE_MECHANISMS.md`, `VOCABULARY.md`, `BMSDK_OFFSETS.json`, `CHAIN.json`, `objects.jsonl`,
`TETHER.json`, `current.json`, `T_ROWS.jsonl`, `Builds/test-091`.

**Card as written** (§9): *"1. T-DM9 (small-arms immunity): choose between root `invulnerable` = 1
… and root `health` scale + armour channels that make small-arms damage zero/negligible while heavy
weapons still kill … pick the one matching G1-14's ratio. 2. Wheels unbreakable (ARM-4) … 3. Regen
(ARM-5) if both sides have a member. 4. Death look (ARM-6) … Done: predicted table shows small arms
= no visible loss, heavy weapons = BmAK ratio ± 20 %; every switch recorded in `damage_switches.json`
with `damage_audit.py` green."*

---

## VERDICT

**The generator is honest, reproducible and unusually good at naming its own probes; the value it
translates against is not the number the card thinks it is.** T-14's `--check` is green today, but
it prints two failing criterion cells and a PARTIAL clause while exiting 0, so "done" rests on
"pending probe" being a pass. Of the 19 assumptions tested below, **3 HOLD, 10 are WEAK, and 6 are
BROKEN** — and one of the broken six is the card's central quantity: the "BmAK ratio" of 24 hits
is `1200 / 50`, where **50 is the damage of the Batmobile's own outgoing cannon**, from a section
G1-14 titles *"Outgoing weapon damage - archetypes, not rules"*. No enemy-tank projectile damage is
in the record, so "the car dies to 24 tank shells" is an unstated symmetry assumption, not a decode.

| # | assumption | verdict |
|---|---|---|
| 1 | the card's `--check` is green on disk | **HOLDS** — exit 0, md/json/switch all match |
| 2 | "done" means the card's Done line is met | **BROKEN** — exit 0 with ARM-1 H0 FAIL, ARM-2 H1 FAIL, clause 2 PARTIAL |
| 3 | the "BmAK ratio" 24 is the *incoming* heavy-cannon damage | **BROKEN** — 50 is the car's own outgoing shell; no enemy-tank damage in the record |
| 4 | 50 is *the* cannon damage | **WEAK** — Primary 50, but the same archetype has `TurretShotDamage` 75, BodyShot/FullyUpgraded 75, HeadShot 110 |
| 5 | the weapon-generator shield absorbs nothing | **WEAK** — `DrainWeaponGeneratorForDamage` is in the same `TakeDamage` body; 24 is a floor |
| 6 | `GetDamageMod` = 1 | **WEAK** — a native encounter multiplier sits on the path, value not decoded |
| 7 | `ArmourModeDamageReduction` = 0, so mode does not change the ratio | **HOLDS** — `DAMAGE_RULES.md` §3.1 step 2 + CHAIN 0 |
| 8 | "the build's values sit inside the shipped domain on every channel" | **BROKEN** — the card's own audit prints 5 outside, 3 of them armour channels |
| 9 | `explosion_threshold` is a per-hit damage, independent of the pool | **BROKEN** — G2-28 step 7 says UNKNOWN and both readings fit |
| 10 | `max_health` 36000 is the answer | **WEAK** — it is H0's answer, 9× the domain, and H1 needs 18000 |
| 11 | the root `health` 100.0 composes neutrally | **WEAK** — silent; G2-28 step 6 calls the composition UNKNOWN |
| 12 | "no visible loss" = 200 pistol rounds under 5 % | **WEAK** — both numbers are the card's own criterion, not decoded |
| 13 | ARM-4: "no off switch exists on either side" | **BROKEN** — the build's `Land_Wheel` part table already ships all three `instantly_*_by_bullets` = 0 |
| 14 | `skew_health` is the wheel's health | **WEAK** — name only; the part table's `Land_Wheel.initial_health` 1020 is the other candidate |
| 15 | ARM-5: "0 hits for recover/regen over the 52-type vocabulary" | **WEAK** — true of the file, but a sibling reader measures 53 module types |
| 16 | ARM-6: "no destroyed-state effect path exists" | **BROKEN** — `DAMAGE_RULES.md` itself lists `DeathExplosion` 5077 and `DeathExplosionSoundArray` |
| 17 | the 1500 shell is `PlayerDamage` at the blast centre | **WEAK** — field chosen by name; falloff and `AIDamage` exist |
| 18 | `HealthRecoverRate` @ +8220 is a `TArray<float>` with no archetype override | **HOLDS** — offset/type/absence all reproduce |
| 19 | the ledger's `T-14` document is this card's nine rows | **WEAK** — 28 rows are filed under doc `T-14`, 9 of them `T-DM` |

**Bottom line.** T-14 does the hard part right: every number in the doc is recomputed, the three
composition models are carried openly, the failing cells name the probes that would settle them, and
the `max_health` switch is refused until a build carries it. What does not survive is the claim that
the translation target is decoded: **the 24-hit ratio compares the Batmobile's own gun to its own
health** (§3), the "all channels in domain" sentence is refuted by the card's own audit (§8), the
threshold semantics are asserted against its dependency's UNKNOWN (§9), and the ARM-4 "no off
switch" sentence missed the one table the card's own chain documents (§13). None of that makes the
36000 wrong as a *design choice*; it makes it a choice, and the card should say so in those words.

---

## 1. The card's `--check` is green on disk today

**Why the card rests on it.** The §12 row says `done` because `t10_damage.py --check` exits 0.

**Test.**

```
$ python Tools/scripts/t10_damage.py --check
rows 9 | option B tank cannon H0 24 H1 48 H2 25 vs BmAK 24 | small arms H0 16.667 % H1 0.167 % H2 never
ARM-1 small arms (criterion < 5 % of the pool): H0 FAIL 16.667 % of the pool pending Q1-DM-B | H1 pass 0.167 % of the pool | H2 pass never (absorbed)
ARM-2 heavy weapons (criterion ±20 % of 24 hits): H0 pass 24 hits (+0.00 %) | H1 FAIL 48 hits (+100.00 %) pending Q1-DM-A | H2 pass 25 hits (+4.17 %)
switch file: 5 declared, 1 pending (max_health 36000) - Done clause 2 PARTIAL
md match True, json match True, switch file clean True
check ok
EXIT=0
```

The two standing gates the done section quotes also still pass: `t_rows.py check` →
`ledger 198 rows | … | check ok` (exit 0) and `status_audit.py --check` → `STATUS.md is current`.

**Verdict: HOLDS.** The artefacts are consistent with the generator, and the check re-derives the
doc rather than trusting it.

---

## 2. "Done" means the card's Done line is met

**Why the card rests on it.** §0.3: *"A task is `done` only when its **Done when** check passed."*
The card's Done has two clauses: the predicted table (small arms no visible loss, heavy weapons
within ±20 % of the BmAK ratio) and every switch recorded.

**Test.** The verbatim check output above, against the Done line.

```
ARM-1 … H0 FAIL 16.667 % of the pool pending Q1-DM-B
ARM-2 … H1 FAIL 48 hits (+100.00 %) pending Q1-DM-A
switch file: 5 declared, 1 pending (max_health 36000) - Done clause 2 PARTIAL
check ok   (exit 0)
```

Of the six criterion cells, **two fail** (ARM-1/H0, ARM-2/H1) and **clause 2 is PARTIAL**; the
script exits 0 because each failing cell has a named Q-1 probe. The doc is explicit (§0, §7), and
the §12 row says the failing cells are "printed … pending `Q1-DM-A/B`". So the state is honestly
reported — but the status word is `done`, which the project's own rules reserve for a passed check.

**Verdict: BROKEN as a completion claim.** The correct status under §0.3 is `blocked: Q1-DM-A/B`
(or the Done line should be rewritten to "model-conditional, two probes pending"). The card chose
the third option: pass the check, disclose in prose, mark done.

---

## 3. The "BmAK ratio" of 24 hits is the incoming heavy-cannon damage

**Why the card rests on it.** Every number in the card flows from `1200 / 50 = 24`: the
`max_health` 36000, the ±20 % band, both Done clauses, T-DM1's edit and the whole H0/H1/H2 table.

**Test.** Where the 1200 and the 50 come from, and what the source calls them.

```
$ sed -n '205,212p' Research/BatmobileGrab/DAMAGE_RULES.md
### 3.5 Outgoing weapon damage - archetypes, not rules
...
| package | archetype | `Damage` | `DamageRadius` | `MyDamageType` | `TurretShotDamage` |
| `Playable_Batmobile_SF` | `Batmobile_Heavy_Cannon_Primary_Projectile` | 50 | 0 | -121 | 75 |
```

```
$ python  # every Projectile.Damage row is a Batmobile archetype
rows: 251 | non-batmobile Projectile.Damage rows: none
Pawn.Health rows: 3, all 1200 (Funhouse, MK2, Batmobile)
```

```
$ sed -n '176,181p' Research/JC3Grab/DAMAGE_MODEL.md
The BmAK side is decoded (`DAMAGE_RULES.json`, G1-14): `Pawn.Health` **1200**, the heavy
cannon projectile `Damage` **50**, missile 250, and `ArmourModeDamageReduction`
**0** - so the BmAK ratio is
**1200 / 50 = 24 heavy-cannon hits** (or 1200 / 250 = 5 missile hits).
```

The 50 is decoded, and 1200 ÷ 50 is arithmetic. But the 50 belongs to **the Batmobile's own
projectile**, in the section the G1-14 record itself titles *"Outgoing weapon damage"*. Nothing in
`DAMAGE_RULES.json` carries an enemy tank's projectile damage — the 251 rows are the Batmobile
packages' archetypes, and `RVehicleHeavyTank` appears only as a *health* symbol and as a cast in
`TakeDamage`. So "the car survives 24 heavy-cannon hits" means "the car survives 24 of **its own**
shells"; whether an enemy heavy cannon deals the same 50 is nowhere decoded.

**Verdict: BROKEN.** The ratio is a decoded *outgoing* number used as an *incoming* one. It is a
defensible design anchor (symmetric weapon balance), but it is not "the BmAK ratio" of incoming
tank fire, and the card never says the symmetry is assumed. One line in `DAMAGE_MODEL.md` §5 and
one in `T10_DAMAGE.md` would fix it; the number itself need not change.

---

## 4. 50 is *the* cannon damage

**Why the card rests on it.** `damage_predict.py` picks it by archetype suffix and value:

```python
cannon = sorted({r["value"] for r in rules["damage_values"]
                 if r["archetype"].endswith("Batmobile_Heavy_Cannon_Primary_Projectile")
                 and r["name"] == "Projectile.Damage"})
...
"heavy_cannon_damage": cannon[0] if cannon else None,
```

**Test.** Every damage the same vehicle's heavy cannon carries.

```
| `Batmobile_Heavy_Cannon_Primary_Projectile`      | Damage 50 | TurretShotDamage 75 |
| `Batmobile_Heavy_Cannon_BodyShot_Projectile`     | Damage 75 | —                   |
| `Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile`| Damage 75 | TurretShotDamage 110|
| `Batmobile_Heavy_Cannon_HeadShot_Projectile`     | —         | TurretShotDamage 110|
| `Batmobile_JokerHeavy_Cannon_Projectile`         | Damage 250| —                   |
```

Four decoded values on the same gun (50 / 75 / 75 / 110) and one 250 for the Joker variant. The
suffix filter is what excludes the other three; `sorted(...)[0]` would silently take the *lowest*
if the three packages ever disagreed. 50 is the base-tier primary shot, which is a reasonable pick
(D-10 forbids the upgraded tiers), but the choice is not stated and 75 is the same gun's
body-shot/upgraded damage and its turret-shot damage.

**Verdict: WEAK.** A decoded value, selected by an unstated rule; the ratio would be 16, not 24,
with 75. The doc should name the chosen archetype and say why the others do not apply.

---

## 5. The weapon-generator shield absorbs nothing

**Why the card rests on it.** The hit count is `health / damage` — i.e. every point of the 50
reaches health.

**Test.** The damage path in the same script body.

```
$ sed -n '106,115p' Research/BatmobileGrab/DAMAGE_RULES.md
7. **The weapon generator is drained here** - the body references
   `DrainWeaponGeneratorForDamage`, then `bEmergencyWeaponGenerator` and
   `WeaponGeneratorPower` (that function is decoded in §4).
```

```
$ sed -n '284,291p' Research/BatmobileGrab/DAMAGE_RULES.md
- **The weapon generator is the shield**: `TakeDamage` calls
  `DrainWeaponGeneratorForDamage(DamageAmount, HitNumber)` (script, 322 B), which reads
  `WeaponGeneratorPower`, `bWeaponGeneratorShielding`, `WeaponUnavailableReason`, ...
```

`WeaponGeneratorPower` is a pool that absorbs damage before health (the doc's own words: "the
shield"), and `bWeaponGeneratorShielding` gates it. Its value and the drain formula are not fully
decoded, so the card cannot model it — but the card also never says it is excluded. If the pool
absorbs anything, the true hit count is **higher** than 24, so 36000 is a lower bound on the health
that reproduces the ratio.

**Verdict: WEAK.** A decoded, same-body mechanism that changes the count is absent from the model
and from the UNKNOWN list.

---

## 6. `GetDamageMod` is 1

**Why the card rests on it.** The per-hit damage is the raw 50.

**Test.**

```
$ sed -n '100,104p' Research/BatmobileGrab/DAMAGE_RULES.md
3. `GetDamageMod` - native, 3 parameters; the encounter layer scales the hit.
```

`RVehicleCombatManager.GetDamageMod` is native (58 B, 3 parms, per §2) and is applied to every
direct hit before the health loss. Its return value is not decoded anywhere in the record. T-14's
model does not mention it at all.

**Verdict: WEAK.** An undecoded multiplier on the measured path; the ratio implicitly assumes 1.
The doc's UNKNOWN list should carry it.

---

## 7. `ArmourModeDamageReduction` = 0 (positive control)

**Why the card rests on it.** If battle mode reduced incoming damage, the BmAK ratio would be
mode-dependent (pursuit 24, battle more), and D-2 would have to split the health scale.

**Test.**

```
$ sed -n '98,101p' Research/BatmobileGrab/DAMAGE_RULES.md
2. **`ArmouredMode` → `ArmourModeDamageReduction`** - **1** script function in the
   whole package reads that field, and this body is it. The shipped archetype value is
   **`0`** (`CHAIN.json`), so armoured/battle mode reduces incoming damage by *nothing* as
   shipped.
```

Also quoted by the generator's own record (`bmak.source`: "ArmourModeDamageReduction ships 0
(CHAIN.json)").

**Verdict: HOLDS.** One field, one reader, value 0 — the ratio genuinely does not vary by mode.

---

## 8. "The build's values sit inside the shipped domain on every channel"

**Why the card rests on it.** The sentence is how the doc dismisses the domains as a source of
uncertainty: *"The build's values sit inside the shipped domain on every channel, so the bracket is
the only uncertainty left"* (`T10_DAMAGE.md:94`).

**Test.** The audit the card runs in its own Done check.

```
$ python Tools/scripts/damage_audit.py
impact_armor                          5000      0..5             0  switch
impact_damage_factor                     0      1..12            1  switch
melee_armor                           5000      0..0             0  switch
melee_armor_strength                   100      0..0             0  switch
deform_scale                             0      1..2             1  switch
...
29 members, 5 outside the shipped range, 5 declared switches
check ok
```

Five values are outside, and three of them are armour-channel members: `impact_armor` 5000 vs
`0..5` (1,000×), `melee_armor` 5000 vs `0..0`, `melee_armor_strength` 100 vs `0..0`. The card's own
`damage_switches.json` declares all five as deliberate switches. So §1's sentence contradicts §6 of
the same document.

**Verdict: BROKEN.** A self-contradiction inside one generated file; the audit that proves it is the
one the card cites.

---

## 9. `explosion_threshold` is a per-hit damage, independent of the pool

**Why the card rests on it.** T-DM4 keeps the four thresholds unchanged and justifies it in one
sentence: *"per-hit damage thresholds, independent of the health pool: 36000 does not move them"*
(`T10_DAMAGE.md:159`). Scaling `max_health` 18× would otherwise interact with them.

**Test.** The dependency's own step.

```
$ sed -n '24p' Research/JC3Grab/DAMAGE_MODEL.md
| 7 | thresholds and death | smoke_threshold, burn_threshold, explosion_threshold, ... | the 233 modules |
  decoded (values); semantics UNKNOWN | whether explosion_threshold is a per-hit blast damage that
  destroys the vehicle outright or a health threshold; the fleet's 500..4000 range overlaps
  max_health 500..4000, so both readings fit the data |
```

The source says the semantics are **UNKNOWN** and that *both* readings fit the data. T-14 picks one
reading (per-hit damage) and states the independence as fact. Under the other reading
(`explosion_threshold` compared against health), a 36000 pool changes every threshold outcome, and
the 18× scale is not neutral.

**Verdict: BROKEN.** A value's semantics asserted against the explicit UNKNOWN of the file the card
names as its source; the consequence is exactly the interaction T-DM4 denies.

---

## 10. `max_health` 36000 is the answer

**Why the card rests on it.** T-DM9's option B and T-DM1's edit.

**Test.** The number against its own bracket and the domain.

```
$ python  # t10_damage_edits.json, "decision"
{"chosen": "B: armour channels + max_health scale, invulnerable stays 0",
 "max_health_chosen": 36000,
 "max_health_for_ratio": {"H0": 36000, "H1": 18000, "H2": 35750}, ...}
$ grep -n "max_health" Research/JC3Grab/VOCABULARY.md | head -1
1478:| `max_health` | int32 | 500 .. 4000 (med 700, n=233) | 700 |
```

36000 is 9× the fleet maximum and 18× the build's current 2000; it is a **switch**, not a
translation, and the doc says so. But note which model it is calibrated to: H0 is *"the reference,
not a claim"* (`DAMAGE_MODEL.md:30`), and the doc's own §1 says H0 fails ARM-1 outright. The number
is simultaneously H0's answer (exactly 24 hits) and within 1 % of H2's (35750 → 25 hits, +4.17 %);
it is wrong by 2× if H1 ships. So it is over-determined by two of the three models, which is the
strongest available defence — and it is still model-conditional.

**Verdict: WEAK.** Declared, probed and reversible, but presented as a decision when it is a bet on
H0/H2 over H1.

---

## 11. The root `health` 100.0 composes neutrally

**Why the card rests on it.** The health pool is `VehicleDamage.max_health` × the entity root's
`health` float. The model uses 36000 as the pool.

**Test.**

```
$ sed -n '23p' Research/JC3Grab/DAMAGE_MODEL.md
| 6 | the vehicle's health pool and scale | `VehicleDamage.max_health` (500..4000) x the entity
  root's `health` float32 (100.0 on all 233 roots) + the root's `invulnerable` int32 (0 on all 233) |
  ... | decoded (values) | how the root `health` float composes with `max_health` (percent?
  multiplier? a separate pool?). Every shipped root is 100.0, so no file shows a second value to
  compare against |
```

```
$ sed -n '15p' Research/JC3Grab/DAMAGE_MECHANISMS.md
| `health` | float32 | **100.0** on all 233 roots | the entity's base health scale (percent) |
```

Two of the card's own dependencies disagree in confidence: `DAMAGE_MECHANISMS` calls it a
"percent", `DAMAGE_MODEL` calls the composition UNKNOWN. T-14 silently uses the percent reading
(100 = ×1). `T10_DAMAGE.md` never mentions the root float.

**Verdict: WEAK.** Not stated anywhere in the card; if 100.0 is a multiplier instead of a percent,
the pool is 100× larger and every hit count in the card is off by two orders of magnitude.

---

## 12. "No visible loss" = 200 pistol rounds under 5 %

**Why the card rests on it.** ARM-1's pass/fail, and therefore the H0 FAIL row that makes the card's
Done conditional.

**Test.**

```
$ sed -n '56,58p' Tools/scripts/t10_damage.py
SMALL_ARMS_SETUP = 200          # Q1-DM-B: 200 pistol rounds on the body
VISIBLE_LOSS = 0.05             # "no visible loss": under 5 % of the pool
ARM2_TOLERANCE_PCT = 20.0       # the card's +-20 % of the BmAK hit count
```

The card says only *"small arms = no visible loss"*. 200 rounds and 5 % are the generator's
invention (the ±20 % is the card's). They are printed in the doc as if they were criteria from the
card: *"ARM-1 small arms do not move the bar | 200 pistol rounds < 5 % of the pool"*. Change either
number and the H0 cell flips: 200 × 30 = 6000 of 36000 = 16.7 %, while 25 % would pass.

**Verdict: WEAK.** A criterion is allowed to be a design choice, but it must be labelled as one;
here it decides a FAIL cell and is presented as the requirement's reading.

---

## 13. ARM-4: "No off switch exists on either side"

**Why the card rests on it.** It is how ARM-4 closes: *"No off switch exists on either side: JC3's
vocabulary has 6 `wheels_damage` rows and 0 hits for `bWheel`/`indestruct`, and the 92 distinct
wheel-named members in BmAK's SDK binding (122 entries) include 0 damage, health, broken or destruct
fields. So ARM-4 lands at the fleet ceiling, not proven unbreakable"* (`T10_DAMAGE.md:113`).

**Test.** The part-damage table the same document's dependency documents as step 5, and the build's
own values.

```
$ python  # current.json, part_damage_types
Land_Wheel  3  {'initial_health': 1020, 'damaged_health': 400, 'loosen_health': 100,
                'instantly_damaged_by_bullets': 0, 'instantly_broken_by_bullets': 0,
                'instantly_loosened_by_bullets': 0}
```

```
$ sed -n '22p' Research/JC3Grab/DAMAGE_MODEL.md
| 5 | the part's own damage table | `VehicleDamage.part_damage_types[]`: initial_health,
  damaged_health, loosen_health, instantly_{damaged,loosened,broken}_by_bullets, damages_owning_vehicle |
  24 rows ... the build's table is the donor's with exactly 1 change
  (Land_Wheel.instantly_damaged_by_bullets) |
```

The wheel's part type already carries **three** bullet switches, all 0 in the build, and a 1020-point
part health pool — the donor shipped `instantly_damaged_by_bullets = 1`, and the build's one part-table
change was to set it to 0. Those are exactly the kind of "off switch" the card says does not exist
(it treats `impact_damage_factor` 0 as one in T-DM8). Also: the `skew_health` 200 → 400 edit appears
**0 times** in the ledger:

```
$ grep -c "skew_health" Working/Translation/T_ROWS.jsonl
0
```

so the one ARM-4 edit the card does make lives only in `t10_damage_edits.json → arm4_wheels` and is
not a row any build card will read from `T_ROWS.jsonl`.

**Verdict: BROKEN.** The "no off switch" claim searched the `wheels_damage` module and the BmAK SDK
and missed the part-damage table — the one place the project already implements wheel switches, and
where the build already carries them. The ARM-4 edit is also unledgered.

---

## 14. `skew_health` is the wheel's health

**Why the card rests on it.** The ARM-4 edit is `front/rear_wheels_damage.skew_health` 200 → 400,
"the only wheel-damage health member with a shipped range".

**Test.**

```
$ grep -n "skew_health" Research/JC3Grab/VOCABULARY.md
490:| `front_wheels_damage.skew_health` | int32 | 200 .. 400 (med 200, n=145) | 200 |
497:| `rear_wheels_damage.skew_health` | int32 | 200 .. 400 (med 200, n=145) | 200 |
481-489: broken_wheel_friction_fraction 0.5..0.75, broken_wheel_radius_fraction 0.6..0.8
```

There are three members in each block: two broken-wheel *fractions* and `skew_health`. The name
"skew_health" suggests the health at which a wheel skews (a threshold), not a hit-point pool; the
part table's `Land_Wheel.initial_health` 1020 is the actual pool, with `damaged_health` 400 and
`loosen_health` 100. Raising a threshold from 200 to 400 may delay the skew; it does not make a
wheel absorb more damage if the pool is the part's 1020.

**Verdict: WEAK.** A name read as a quantity (R5), and the doc's own step-5 source calls the
part-health semantics UNKNOWN. The edit is at the fleet maximum and harmless; the *claim* that it
addresses "wheels cannot be shot off" is not established.

---

## 15. ARM-5: 0 hits for recover/regen over the 52-type vocabulary

**Why the card rests on it.** ARM-5 closes as a named omission on the JC3 side because there is
"nothing to write".

**Test.** Same count as the G2X gate uses, plus the sibling reader's count.

```
$ grep -n -i "recover\|regen" Research/JC3Grab/VOCABULARY.md
(no member; the only `heal` hits are the word `health`)
$ grep -c '^## `' Research/JC3Grab/VOCABULARY.md
52
$ python  # TETHER.json, written by jc3tether.py --write (green under G2X)
tether module_types 53
```

The claim is true of the file it names. But the same project has a second, gate-green reader that
counts **53** module types in the same 232 caches (`TETHER.md:174`: *"The fleet's 53 module types"*),
so one module's members are outside the vocabulary the omission rests on. (This is the same defect
challenged in `card-G2X.md` §10; it propagates here because T-14 quotes the 52-type count.)

**Verdict: WEAK.** True as scoped to `VOCABULARY.md`, not proven over the fleet.

---

## 16. ARM-6: "no destroyed-state effect path exists in the Batmobile packages' record"

**Why the card rests on it.** §4 closes ARM-6 as a named omission on this sentence: *"BmAK | none
decoded: G1-14 covers incoming-damage rules, not the death effect or sound; no destroyed-state effect
path exists in the Batmobile packages' record"* (`T10_DAMAGE.md` §4), with the rows handed to T-17
(effects) and T-16 (audio).

**Test.** The G1-14 record T-14 names as its source.

```
$ grep -n "Death" Research/BatmobileGrab/DAMAGE_RULES.md
571:| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `DeathExplosionSoundArray` | ArrayProperty | — | stream |
582:| `RVehicleBatmobile` | `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` | `RVehicleBatmobileBase.DeathExplosion` | ObjectNCRProperty | 5077 | sdk-layout |
```

The record contains **both members §1 ARM-6 names** — `DeathExplosionSoundArray` and the
`DeathExplosion` object reference (5077) — on the Funhouse archetype, i.e. exactly the death effect
and the death sound the card says G1-14 does not cover. So the reason given for the omission is
false: a destroyed-state path **is** in the record. What is missing is the *content* of object 5077
and the array (value `—`, `stream`), so "the death look is not decoded" may still be true; "there is
no path" is not.

**Verdict: BROKEN.** A "no carrier exists" claim that searched the incoming-damage half of the
record and missed the two death members in the same file. ARM-6's hand-off to T-17/T-16 may still be
the right division of labour, but it needs the correct reason, and T-17 should inherit object 5077
rather than a claim that nothing exists.

---

## 17. The 1500 shell is `PlayerDamage`, at the blast centre

**Why the card rests on it.** `tank_shell_damage` 1500 is the denominator of every hit count.

**Test.** Where the 1500 comes from and which field it is.

```
$ sed -n '78,90p' Research/JC3Grab/DAMAGE_MODEL.md
| key | arm | gun type | damage | veh. factor | pellets | per shot vs vehicle | blast (PlayerDamage) | channel used |
| `tank_cannon` | tank cannon w602_mediumtank_canon | `bullet_weapon` | 1 | 1 | 1 | 1 | 1500 in 8 m | explosion |
```

```
$ sed -n '159,166p' Research/JC3Grab/FORCEPULSE.md
| `AIDamage` | 0 | 1000 | 23 |
| `AIDamageRadius` | 0 | 50 | 23 |
| `PlayerDamage` | 0 | 3000 | 23 |
| `PlayerDamageRadius` | 1.5 | 50 | 23 |
```

The record chooses the pulse's `PlayerDamage` (by name: the vehicle is the player's) and takes the
blast centre (`Q1-DM-C`/`Q1-DM-A` setup: *"one tank shell into the Batmobile's body, at the centre
of the 8 m blast"*). `AIDamage` exists as the sibling field, and `*RadiusPercentageMax` 0.0/0.0 on
stock blasts means damage "falls off at once" — so any hit off the centre delivers less than 1500.
Also note the shell's *direct* bullet component is 1: the model uses only the blast, which is the
dominant term but not the whole hit.

**Verdict: WEAK.** A field chosen by its name and an idealised centre hit; both are defensible, both
are unstated. The 24-hit ratio is therefore the *best case* for the shell.

---

## 18. `HealthRecoverRate` @ +8220, `TArray<float>`, no archetype override (positive control)

**Why the card rests on it.** ARM-5's BmAK half: the mechanism exists, the value does not ship.

**Test.**

```
$ python  # BMSDK_OFFSETS.json, RVehicleBatmobileBase
{"kind": "ArrayProperty", "member": "HealthRecoverRate", "name": "HealthRecoverRate",
 "offset": 8220, "type": "float"}
$ grep -c "HealthRecoverRate" Research/BatmobileGrab/CHAIN.json Research/BatmobileGrab/objects.jsonl
CHAIN.json:0
objects.jsonl:0
```

```
$ python  # DAMAGE_RULES.json field_references
"RVehicleBatmobileBase.HealthRecoverRate": {"read_by": ["RVehicleBatmobileBase.ExperienceAwarded"], ...}
```

Offset, type, single reader and empty archetype tags all reproduce exactly as the doc states.

**Verdict: HOLDS.** This is the best-supported negative in the card: the layout is decoded, the
value is genuinely absent, and the doc refuses to invent it.

---

## 19. The ledger's `T-14` document is this card's nine rows

**Why the card rests on it.** §5's `ledger` column tells a build card where each value will be read
from; the done section quotes `ledger 198 rows`.

**Test.** Rows per `doc` in the ledger the card names.

```
$ python  # T_ROWS.jsonl
{'T-1': 49, 'T-2b': 39, 'T-3': 17, 'T-13': 17, 'T-14': 28, 'T-7': 14, 'T-20': 19, 'T-15': 15}
T-DM ids: 9
```

28 rows are filed under doc `T-14`; 9 are `T-DM`. The other 19 are T-18's light rows, which enter
the ledger as doc `T-14` (documented in the T-18 section at `MODLOG.md:12590`). `STATUS.md`'s T-14
line therefore counts 28, not 9. Nothing is lost — `t10_damage.py` filters by id — but anyone
auditing "T-14's rows" gets 28.

**Verdict: WEAK.** A document-id collision in the ledger; harmless to the generator, misleading in
`STATUS.md`.

---

## Method and limits

* Commands were read-only: `t10_damage.py --check`, `damage_audit.py` (a reporter), `t_rows.py check`,
  `status_audit.py --check`, plus `grep`/`python` reads. No `--write` was run; the three generated
  artefacts kept their `10-29 02:46` mtimes, and the only files created were git-ignored `.pyc`
  caches.
* No game file, archive, save, build or shared module was touched; nothing was installed into
  `D:\Games`; no game was launched; nothing was committed.
* The raw decoded corpus (`E:\Modding\JustCause3\_grab\`) and the BmAK packages were not re-decoded; every
  test uses the records the card itself names, which is also what its `--check` sees.
* Where a claim depends on the composition of `*_armor`/`str`ength (H0/H1/H2), the report follows the
  card's own framing: three named models with Q-1 probes, not a single decoded answer.
