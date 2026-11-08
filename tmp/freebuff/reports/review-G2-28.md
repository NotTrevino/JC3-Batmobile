# Review — G2-28 · Damage model, complete, with a predicted hits-to-kill table

Reviewer: independent (did not write the card). Read-only pass: `GRAB_BACKLOG.md`, `MODLOG.md`,
`Research/` and `Tools/` were only read; nothing outside this file was written, no game launched,
no git.

Scope: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G2-28 card (§7, line 759) and its §12 row;
`MODLOG.md` §"G2-28 … — done" (line 11227); `Research/JC3Grab/DAMAGE_MODEL.md` (277 lines),
`Research/JC3Grab/DAMAGE_MODEL.json` (2,615 lines), `Tools/scripts/damage_predict.py` (984 lines).

## VERDICT

**Minor issues.**

The table is real and the arithmetic is right. I recomputed cells by hand and read them out of the
JSON: donor assault rifle 22, medium tank pistol 67 / 6,667 / never, build shotgun 14 / 1,389 / 49 —
all match, and `ceil(700/30)=24` etc. hold for every model. The measured diffs are exact
(`scalars_build_vs_tank` = 6 rows, `scalars_build_vs_donor` = 23, `part_table_build_vs_donor` = 1
row = `Land_Wheel.instantly_damaged_by_bullets` 1→0, `part_table_tank_vs_donor` = 24), the BmAK
ratio is 1200/50 = 24 with the missile at 250 → 5, and the fleet census (233 modules, bullet pairs
`0@0` ×183 … `5000@99` ×13) sums to 233 on every channel. R5 is handled the right way round: the
composition that the files do not state is carried as **three named models**, each with a formula and
a falsifiable probe, and the doc says so in its first paragraph.

What keeps it off "sound" is scope against the card's own Done sentence and one contradictory
column. The card says *any* UNKNOWN step becomes a Q-1 probe with expected values for both
hypotheses; the file has seven UNKNOWN steps and three probes, all three about step 4 (the gate /
pool composition), and §5 points the reader to "the Q-1 probe below" for the `bullet` vs
`bullet_heavy` question that no probe answers. §3's "channel used" column also disagrees with §4
and with the JSON for two of the nine arms.

## Check output (verbatim)

Command run from `E:/Modding/JustCause3/JC3-Batmobile`:

```
$ python Tools/scripts/damage_predict.py --check
PASS: 9 arms x 3 vehicles, models H0, H1, H2, finite H0 27 / H1 27 / H2 19, never H1 0 / H2 8
      chain 7 steps, 7 carry an UNKNOWN, 3 Q-1 probes
      donor 700 HP / tank 2000 HP / build 2000 HP, fleet 233 modules, json match True
```

Exit status `0`. Same three lines as the block at `MODLOG.md:11232`–`11234`.

Out paths — present:

| path | state |
|---|---|
| `Research/JC3Grab/DAMAGE_MODEL.md` (card Out) | present, 277 lines, §1–§9 |
| `Tools/scripts/damage_predict.py` (card Out, `--check`) | present, `--write`/`--check`/`dump` |
| `Research/JC3Grab/DAMAGE_MODEL.json` (row) | present: `chain` (7), `models`, `vehicles` (3), `arms` (9), `table` (3 × 9), `diffs` (6), `fleet`, `probes` (3), `arm_targets` |
| README section + Files row, §12 row, MODLOG done section | present |

## Issues

### 1. (card Done, partially unmet) "any `UNKNOWN` step becomes a Q-1 damage probe" — 7 UNKNOWN steps, 3 probes, all for step 4

Card text (`GRAB_BACKLOG.md:770`): "Done: a predicted table for all three vehicles; any `UNKNOWN`
step becomes a Q-1 damage probe with the exact expected values for both hypotheses."
`DAMAGE_MODEL.md` §1 gives every one of the seven steps its own UNKNOWN (and `--check` prints "7
carry an UNKNOWN"), but `probes` holds exactly three (`Q1-DM-A/B/C`), and each of the three is a
test of the step-4 composition (H1 vs H2 gate; H2 pool). Steps 1 (part → damage type), 2
(`vehicle_damage_factor` multiplication), 3 (weapon → armour channel), 6 (root `health` float) and 7
(`explosion_threshold`) have UNKNOWNs with no probe and no expected values. Step 6 and 7 are
explicitly "both readings fit the data" — exactly the shape the card asked to turn into a probe.
Either add the probes or state in §8 that these five are not probe-able and why; as written the Done
clause is met for 2 of 7 steps (three probes over one step).

### 2. (dangling reference) §5 promises "the Q-1 probe below" for the `bullet`/`bullet_heavy` split, and none exists — `Research/JC3Grab/DAMAGE_MODEL.md:195`–`197`

"Whether a given weapon lands in `bullet` or `bullet_heavy` is UNKNOWN (step 3), so T-14 cannot
write those rows from the files alone: it needs either a `bullet_heavy` carrier found in G2-11's
weapon components, or **the Q-1 probe below**." The probes below are A (H1 vs H2 on `explosion`), B
(H1 vs H2 on `bullet`) and C (the H2 pool) — none distinguishes which channel a weapon uses. This
is the one UNKNOWN that blocks a phase-T decision (ARM-1's per-channel split), so the missing probe
is the most consequential half of issue 1.

### 3. (R5/data) §3's "channel used" column contradicts §4 and the JSON for two arms — `DAMAGE_MODEL.md:85` and `:87` vs `:133`, `:150`, `:159`

§3 says `grenade` → `explosion` (line 85) and `heli_missile` → `bullet` (line 87). §4's rows for both
arms say `unknown`, with a note at line 159 ("Rows whose channel is `unknown` (a missile direct hit
and the grenade's thrown damage …)"). `DAMAGE_MODEL.json` agrees with §4:
`table.donor.heli_missile.primary.channel` = `unknown`, `table.donor.grenade.primary.channel` =
`unknown`. The cause is visible in the script: `to_md` prints the arm-level `channel`
(`vehicle_arm`/`hand_arm`: "explosion" if the arm has a blast, else "bullet"), while the numbers use
the component rule in `arm_damage()` (`bullet` only when `gun == "bullet_weapon"`, else `unknown`).
So §3 answers a different question from §4 and the two disagree on the same page — and §3 is the
table a later T-11/T-14 row will copy. One row of the column is simply wrong for the computation
that follows.

### 4. (R4, over-read of a known-unknown) `test-077` is cited as gate evidence four times, though its failure symptom is recorded as UNKNOWN — `DAMAGE_MODEL.md:31`, `:184`, `:197`, `:222`

`MODLOG.md:4917`–`4927` (§98) records the user verdict "Fail" with **no symptom** ("what actually
happens in game … is UNKNOWN and is not being assumed here"), and `DAMAGE_MODEL.md:21`/`:31` do carry
"(symptom unrecorded)". §5 then writes "test-077 shipped 100 and failed" (line 184) inside the
"inside the shipped domain?" column, where it reads as evidence that strength 100 does not work. The
claim does not need it — the fleet maximum of 99 is the domain argument — and using a failure with no
observed symptom to lean against H1 is the pattern R4 forbids. Line 222 is fine (explicitly
conditional: "If test-077's failure was small-arms damage"). Recommend dropping the test-077 clause
from §5 and keeping the caveated mention in §1.1.

### 5. (R11) Fleet constants are typed in the script, not re-derived — `Tools/scripts/damage_predict.py:460`, `Research/JC3Grab/DAMAGE_MODEL.md:186`–`188`

`fleet_max_health = 4000  # VOCABULARY.md max_health 500 .. 4000, n=233` is a literal; the fleet
range "500..4000, i.e. 3 hits under H0/H2 and 6 under H1 at the maximum" is the whole basis of the
ARM-2 "outside the domain" verdict, and `fleet_census()` collects only the armour pairs and the
module count — the `max_health` values are never read from the 233 modules here. It is correctly
sourced (`VOCABULARY.md:1478` says `500 .. 4000 (med 700, n=233)`), so the number is right; it is
just not re-derivable by `--check`. Same class: "the root `health` float is **100.0 on all 233
roots**" (line ~201) is inherited from `DAMAGE_MECHANISMS.md` §1/§3 — the step-6 cell says so, which
is honest, but `--check` does not test it. Also typed: "4 bytes at `epe+1167`" for `invulnerable`,
and the loadout spread "5 pistol / 4 AR / 2 MG / 4 shotgun / 7 RPG variants" (§8). None of these
changes a conclusion; they are the numbers a later card is most likely to quote without the source.

### Note (not a defect): what `--check` proves for this card

`--check` re-derives the JSON and md and compares them byte for byte, and prints model-dependent
tallies (finite/never per model, chain length, probes, vehicle HPs, fleet module count). It does not
evaluate the prose: neither the three models' worth nor the §5 recommendation is checkable, and the
two defects above (dangling probe promise, §3 channel column) pass green. That is the normal shape
for these readers — the point is only that PASS here means "the numbers are the numbers", not "the
card's Done clause is met".

## Spot-checks

| # | value in `DAMAGE_MODEL.md` | where verified |
|---|---|---|
| 1 | Table cells: donor `assault_rifle` 22/22/22, medium tank `pistol` 67 / 6,667 / never, build `shotgun` 14 / 1,389 / 49 (§4, lines 114–152) | Read from `DAMAGE_MODEL.json` `table.*.…primary` and recomputed by hand: 700/32 = 21.9→22; 2000/30 = 66.7→67; H1 30×0.01 = 0.3 → 2,000/0.3 = 6,667; H2 30 ≤ 99 → never; shotgun 144.000002 @99 → H0 13.9→14, H1 1.44 → 1,389, H2 (5,000+2,000)/144 = 48.6→49. Table matches the formulas in §1.1 exactly. |
| 2 | "the build's scalars differ from the medium tank's in 6 values … against the donor it differs in 23" and "the build's part table is the donor's with exactly 1 change: `Land_Wheel.instantly_damaged_by_bullets` 1 → 0"; "the tank's table differs from the donor's in 24 values" (§2, lines 52–72) | `DAMAGE_MODEL.json` `diffs`: `scalars_build_vs_tank` = 6 rows (`deform_scale`, `impact_armor`/`_strength`, `impact_damage_factor`, `melee_armor`/`_strength`), `scalars_build_vs_donor` = 23 rows, `part_table_build_vs_donor` = 1 row exactly as quoted, `part_table_tank_vs_donor` = 24 rows, `part_table_build_vs_tank` = 24 rows. The build's channel block itself (bullet 5000@99, impact/melee 5000@100) is in `vehicles.build_test-091.channels`. |
| 3 | "`Pawn.Health` 1200, the heavy cannon projectile `Damage` 50, missile 250 … the BmAK ratio is 1200 / 50 = 24 heavy-cannon hits (or 1200 / 250 = 5 missile hits)", `ArmourModeDamageReduction` 0 (§5, lines 177–180) | `DAMAGE_MODEL.json` `arm_targets.bmak_ratio`: `health` 1200, `heavy_cannon_damage` 50.0, `heavy_cannon_hits` 24, `missile_damages` [250.0], `armour_mode_damage_reduction` 0, source cited as `DAMAGE_RULES.json` (G1-14). Arithmetic re-checked: 1200/50 = 24, 1200/250 = 4.8 → 5. |
| 4 (bonus) | "233 `VehicleDamage` modules" and the bullet pair census `0@0` ×183, `100@50` ×18, `5000@99` ×13, `20@60` ×9, `2000@99` ×6, `100@75` ×4 (§7, lines 236–248) | `DAMAGE_MODEL.json` `fleet.modules` = 233; `fleet.pairs.bullet` is exactly that dict, and its counts sum to 233 (as do the other seven channels). `max_health` 500..4000 and `bullet_armor_strength` 0..99 are `VOCABULARY.md:1478` / `:1458`. |

## Tamper test

Not re-run (journaled at `MODLOG.md:11237`–`11240`: `table.build_test-091.tank_cannon.primary.H0`
2→3 in the JSON → `FAIL: DAMAGE_MODEL.json stale`, exit 1; `tank_cannon` H0 2→4 in the md →
`FAIL: DAMAGE_MODEL.md stale`; both restored → PASS). Re-running would mean writing `Research/`,
which this review may not do. The check path is consistent with the journal (JSON object equality +
rendered-md comparison).

## Limits of this review

The hits-to-kill numbers are only verified as *arithmetic from the JSON*, not as game behaviour: the
whole point of the card is that the composition rule is unknown, and no launch was made (R6). I did
not re-decode the nine weapon tunes or the build's `.vmodc`; the arm values and the build's channel
block are taken from `DAMAGE_MODEL.json`, which `--check` re-derives from those sources. I did not
verify the `w602` AI-tune claim (20 × 10 = 200) — it comes from G2-10's `WEAPONS.jsonl` and is not
used in any table cell.
