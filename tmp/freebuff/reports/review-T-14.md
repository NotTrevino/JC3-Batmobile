# Review — T-14 · Damage and armour translation

Reviewer: independent pass (did not write the card). Read-only: nothing outside this report was
modified; no game launched, nothing committed.

## VERDICT

**needs rework**

The numeric core is careful and reproducible: the BmAK 24-hit target, the 36000 / 18000 / 35750
per-model health figures, the wheel edit and the ARM-5/ARM-6 omissions all check out against
`DAMAGE_MODEL.json`, `VOCABULARY.md`, `current.json`, `BMSDK_OFFSETS.json` and the H0/H1/H2 formulas
in `damage_predict.py`. What fails review is the claim that the card's Done criterion is met, and
three statements the delivered files contradict.

1. The card's Done line is **not** met on the face of the delivered table: ARM-1 fails under H0
   (16.667 % ≥ 5 %) and ARM-2 fails under H1 (48 hits vs 24, +100 %). `--check` passes because it
   **skips exactly those two cells by name** — `and m != "H0"`, `and m != "H1"`
   (`Tools/scripts/t10_damage.py:497,499`). A check that verifies a weakened version of the Done
   criterion, while its PASS line says nothing about the exclusion, is the defect this review was
   told to look for.
2. The doc says `damage_switches.json` "currently declares six switches" — it declares five
   (`doc:130` vs the file).
3. The doc says `skew_health` "is the only wheel-damage member with a range" — four other
   wheel-damage members have ranges (`doc:82` vs `VOCABULARY.md:488-489,495-496`).
4. `T_ROWS.jsonl` still says T-DM1 `keep`, T-DM2 `edit`, T-DM9 `blocked`, i.e. the ledger of record
   contradicts the card's three changed decisions, and the generator captures the mismatch without
   the doc mentioning it.
5. Option A is rejected on an inference ("never", the `invulnerable` engine gate) presented as
   arithmetic fact, although the research file the card cites says the gate is **unproven for a
   vehicle root** (`DAMAGE_MECHANISMS.md:85-87`).

The remedy is not a rewrite of the analysis: it is (a) make `--check` report the model-conditional
status instead of dropping H0/H1, (b) correct the three false statements, (c) carry the
`invulnerable` caveat next to option A, (d) either update the three ledger dispositions or state in
the doc that the ledger rows belong to T-2b/T-3 and are unchanged, and (e) mark T-DM1/T-DM9 as
pending `Q1-DM-A` rather than settled, since 36000 vs 18000 is by the author's own statement
undecided.

## Check output (verbatim)

```
$ python Tools/scripts/t10_damage.py --check
rows 9 | option B tank cannon H0 24 H1 48 H2 25 vs BmAK 24 | small arms H1 0.167 % of pool
md match True, json match True, switch file clean True
check ok
EXIT=0
```

Matches the MODLOG `## T-14 · Damage and armour translation — done (2026-10-28)` block verbatim.
The card's second Done clause also runs green:

```
$ python Tools/scripts/damage_audit.py
... 29 members, 5 outside the shipped range, 5 declared switches
check ok
EXIT=0
```

## Out paths

| card `Out:` path | exists | notes |
|---|---|---|
| `Working/Translation/T10_DAMAGE.md` | yes (9,072 B) | generated, 152 lines |
| `Working/Translation/t10_damage_edits.json` | yes (10,588 B) | generated |
| `Tools/scripts/t10_damage.py` | yes (26,131 B) | `--write` / `--check` / dump |
| `Working/Translation/damage_switches.json` | yes (1,707 B) | `bullet_armor_strength` declaration removed; `_t14` note added |
| rows in `T-2b` | via the ledger only | the card allows the new doc instead; all nine ids are in `T_ROWS.jsonl` — but see issue 3 |

`GRAB_BACKLOG.md:1323` marks T-14 `done` with the same claims (option B, 36000, 24/48/25, wheels
400, ARM-5/6 omissions, stale switch removed, audit green). The row repeats "tank cannon 24/48/25
hits H0/H1/H2 vs the BmAK 24", so the +100 % H1 figure is at least visible in the ledger text.

## Done criterion vs what `--check` verifies

Card (`GRAB_BACKLOG.md:888`): *"predicted table shows small arms = no visible loss, heavy weapons =
BmAK ratio ± 20 %; every switch recorded in `damage_switches.json` with `damage_audit.py` green."*

| card clause | what the payload says | what `--check` enforces |
|---|---|---|
| small arms = no visible loss | `checks.small_arms_no_visible_loss` = {H0: **false**, H1: true, H2: true}; H0 loss 16.6667 %, criterion `< 5 %` | skips `not ... and m != "H0"` → H0 failure never fails the run |
| heavy weapons = ±20 % of 24 | `checks.arm2_within_20pct` = {H0: true, H1: **false**, H2: true}; H1 deviation 100.0 % | skips `... and m != "H1"` → H1 failure never fails the run |
| every switch recorded in `damage_switches.json` | `max_health` 36000 is the card's own switch and is **not** in the file (`switch_file.pending`) | only asserts the *stale* declaration is gone; the pending one is not checked |
| `damage_audit.py` green | yes | run separately (exit 0) |

So `--check` verifies md/json equality, stale-switch removal, row-id existence, and the Done rule
under the two models the author expects — not the rule the card states. The exclusion is a
deliberate design choice (visible in the code as a comparison against a literal model name) and it
is not mentioned in the doc or the MODLOG.

`--check` does not test the wheel edit: `front/rear_wheels_damage.skew_health` live in
`CustomLandGlobal`, not `VehicleDamage`, so `damage_audit.py`'s 29-member table never sees them; the
only check is that the generated md matches the payload that was generated from the same values.

## Issues

1. **`Tools/scripts/t10_damage.py:497,499` — `--check` silently drops the two failing Done cells.**
   ```python
   if not ck["small_arms_no_visible_loss"][m] and m != "H0": fails.append("ARM-1 fails under %s" % m)
   if not ck["arm2_within_20pct"][m]      and m != "H1": fails.append("ARM-2 outside 20 %% under %s" % m)
   ```
   The payload (`t10_damage_edits.json → checks`) records H0 ARM-1 = false and H1 ARM-2 = false; the
   doc prints both as failures (`doc:74` "16.667 %", `doc:75` "48 (outside)"). A reader of
   "check ok" would conclude the card's Done line is satisfied. It is satisfied under two of three
   candidate models and no line of output says so.

2. **`Working/Translation/T10_DAMAGE.md:73-75` — the Done claim is contradicted by the doc's own
   table.** The section "What the two requirements become" prints ARM-1 H0 `16.667 %` against a
   `< 5 %` criterion and ARM-2 H1 `48 (outside)`. The card asks the predicted table to *show* those
   properties; the table shows the opposite for one model each. The honest disposition is that
   T-DM1's 36000 and T-DM9's decision are **pending `Q1-DM-A`/`Q1-DM-B`**, exactly as §1 says
   ("if `Q1-DM-A` shows the gate is the H1 percentage model the same ratio needs 18000"), not that
   both ARM codes are carried today.

3. **`Working/Translation/T_ROWS.jsonl` — three ledger dispositions contradict the card.**
   T-DM1 ledger `keep` vs doc `edit`; T-DM2 ledger `edit` vs doc `keep`; T-DM9 ledger `blocked` vs
   doc `decide`. The generator already knows: `t10_damage_edits.json → rows[].ledger_dispo` stores
   `keep / edit / blocked` next to `action` `edit / keep / decide`. The doc's §5 table does not show
   the ledger value, the MODLOG says "no `T_ROWS.jsonl` change (the nine `T-DM` ids already exist)",
   and `--check` only asserts membership (`if r["id"] not in ledger`). Consequence: the project's
   ledger of record still says T-DM9 is **blocked** while the card is marked done.

4. **`Working/Translation/T10_DAMAGE.md:130` — "currently declares six switches" is false.**
   `Working/Translation/damage_switches.json` declares five (`impact_damage_factor`,
   `impact_armor`, `deform_scale`, `melee_armor`, `melee_armor_strength`); `bullet_armor_strength`
   is gone and `max_health` is not there. The sentence is a typed literal in `md()` describing the
   pre-write state and was never updated, so the doc misreports the file it is about. Also
   self-contradictory: "one of them no longer applies" — the file no longer contains it.

5. **`Working/Translation/T10_DAMAGE.md:82` — "`skew_health` is the only wheel-damage member with a
   range (200..400)" is false.** `Research/JC3Grab/VOCABULARY.md:488-489` and `:495-496` give four
   more wheel-damage members with shipped ranges: `broken_wheel_friction_fraction` 0.5 .. 0.75 and
   `broken_wheel_radius_fraction` 0.6 .. 0.8, front and rear. `skew_health` is the only wheel-damage
   **health/threshold** member, which is the claim the sentence needs. The same wording is baked into
   `t10_damage_edits.json → arm4_wheels.note`.

6. **`Working/Translation/T10_DAMAGE.md:82` — "89 wheel-named members" does not reproduce.**
   `Research/BatmobileGrab/BMSDK_OFFSETS.json` holds **92 distinct** wheel-named property names
   (122 entries over 41 classes); 0 of them match `damage|health|broken|destruct`. The substantive
   half of the sentence ("none is a damage field") is correct and was verified; the count is a typed
   literal that is off by three and cannot be derived from anything the script reads.

7. **`Working/Translation/T10_DAMAGE.md:29-39, 126` — option A's "never (engine gate)" is an
   inference stated as fact (R5/R4).** The table asserts that `invulnerable` = 1 makes all nine arms,
   including the tank cannon, read "never", and the rejection argument is "a `never` cannot be within
   ±20 % of 24". The cited evidence (`Research/JC3Grab/DAMAGE_MECHANISMS.md` §4) says the opposite
   about certainty: the flag's *whole-vehicle* scope is an inference from the member and its prop
   usage, and "nothing in the shipped vehicle fleet uses it, so the engine path is **unproven for a
   vehicle root**; the evidence that `1` is honoured comes from `CDamageController` (props)". A
   member's name and a prop-use analogy are not a decoded behaviour. The card's conclusion (prefer
   B) is still right — B is the only option whose numbers come from decoded fields — but option A
   must be labelled "would, if the gate is whole-vehicle as the name implies; unproven for a vehicle
   root" rather than "never".

8. **`Working/Translation/T10_DAMAGE.md:21, 126` — two internally contradictory sentences.**
   `:21` calls 0.17 % the small-arms loss "at worst (H1)" while the same doc's table gives H0
   16.667 %, i.e. 100× worse. `:126` says option B "hits the BmAK ratio **24 %**" — 24 is a hit count,
   not a percentage, and the same sentence then quotes a 100.00 % deviation at H1. The generator
   formats `bmak_hits` with a `%%` (`t10_damage.py:243-246`), which is where "24 %" comes from.

9. **Typed numbers in `md()` (R11), several of them checkable from the payload.**
   `t10_damage.py` prose literals include "six switches" (`:400`), "9x the fleet maximum of 4 000"
   and "4 000 gives 3 hits under H0/H2, 6 under H1" (`:415-417` — both values are already in
   `DAMAGE_MODEL.json → arm_targets.hits_at_fleet_max_health_H0/H1`), "0.3 damage per pistol round"
   (`:420` — derivable from the H1 row: 30 × (1 − 99/100)), "52-type" (twice), "6 `wheels_damage`
   rows" and "89 wheel-named" (`:181-183`), and "±20 %"/"5 %" instead of `VISIBLE_LOSS` /
   a deviation constant. Additionally, the H1 "per-hit" column is computed as
   `tank_shell_damage / 2.0` (`:325`) — the `2.0` assumes explosion strength 50, while the
   `health_needed` next to it uses the real strength; if strength changed, the two columns would
   disagree.

10. **`max_health` 36000 is the card's own switch and is not recorded (Done clause 2).** The doc is
    explicit (`:130-133`) and the MODLOG explains why (the audit would fail against a build that
    still ships 2000 — verified in `damage_audit.py:99-107`). Disclosed, but the Done line says
    "every switch recorded"; T-14's ship value is therefore undeclared by construction until the
    build card writes it. It should be reported as a deviation, not counted as met.

Checked and found sound: the 29-member audit table and its five declarations; the stale
`bullet_armor_strength` removal (audit fails while it stays — the tamper test in the MODLOG matches
`damage_audit.py:104-106`); BmAK 1200 / 50 → 24; `max_health_needed` 36000 in `DAMAGE_MODEL.json`;
H0/H1/H2 formulas as described and the three hits-per-model values; the wheel edit 200 → 400 at the
shipped maximum; ARM-5's `HealthRecoverRate` being a `TArray<float>` at +8220 read only by
`ExperienceAwarded` (so "awarded per experience event" is sourced, not guessed) with the value
UNKNOWN; ARM-6 as a named omission with owners T-16/T-17; option A's rejection as a *direction*
(B is the only option with decoded numbers); and the generator's `--write`/`--check` symmetry (md and
json are byte-compared against a rebuild, and the four tamper tests in the MODLOG map onto real
failure paths).

## Spot-checks

| value in the doc | where verified |
|---|---|
| tank cannon **24 / 48 / 25** hits at `max_health` 36000 (doc:20-21, 45-49) | recomputed from the model formulas: H0 ceil(36000/1500)=**24**; H1 ceil(36000/(1500·0.5))=**48**; H2 ceil((250+36000)/1500)=**25**, using `Tools/scripts/damage_predict.py:94-96`; json `options.B_channels.table.tank_cannon` = 24/48/25, armour 250 @ strength 50, damage 1500.0 |
| BmAK **1200 / 50.0 → 24 heavy-cannon hits**, JC3 shell **1500.0**, `max_health` needed **36000** (doc:9-12) | `Research/JC3Grab/DAMAGE_MODEL.json → arm_targets.bmak_ratio` = {health 1200, heavy_cannon_damage 50.0, heavy_cannon_hits 24}, `arm_targets.tank_shell_damage` = 1500.0, `arm_targets.max_health_needed` = 36000.0; 1200/50 = 24 |
| `front/rear_wheels_damage.skew_health` **200 → 400**, range 200..400 (doc:80-82) | `Working/Translation/current.json → modules.CustomLandGlobal.values` front 200 / rear 200; `Research/JC3Grab/VOCABULARY.md:490` and `:497` = `int32 200 .. 400`, donor 200 |
| small arms H1 **0.167 %** of the pool per 200 rounds (doc:21, 74) | 200 × 30 (pistol, bullet, armour 5000 @ 99) × (1 − 99/100) = 60; 60 / 36000 = **0.1667 %**; json `small_arms_pool_loss_pct_200_rounds.H1` = 0.1667; doc prints 0.167 % at 3 dp |
| switch file: **5** declarations, `bullet_armor_strength` absent (contradicting doc:130) | `cat Working/Translation/damage_switches.json` → `impact_damage_factor`, `impact_armor`, `deform_scale`, `melee_armor`, `melee_armor_strength`, plus `_t14` note |
| ledger says **T-DM1 keep / T-DM2 edit / T-DM9 blocked** | parsed `Working/Translation/T_ROWS.jsonl`; same values mirrored in `t10_damage_edits.json → rows[].ledger_dispo` |
