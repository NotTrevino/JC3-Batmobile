# Assumption challenge — card G2-10 · Vehicle weapon catalogue

Written 2026-10-30. Read-only review: nothing in `GRAB_BACKLOG.md`, `MODLOG.md`, `Research/`,
`Tools/` or any game file was modified; the only file written is this one. No game was launched,
nothing was written to `D:\Games`, nothing was committed. Commands that read the install are the
card's own readers, read-only (`--check`, `wtunesurvey`, `dump`).

**In scope:** `GRAB_BACKLOG.md` §0.5 (R1–R14), the G2-10 card (lines 584–596), the §12 row
(line 1293), `MODLOG.md` §"G2-10 · Vehicle weapon catalogue — intended change" (9143) and
§"— done" (9177–9280), and the card's outputs: `Research/JC3Grab/WEAPONS.md` (1,223 lines),
`WEAPONS.jsonl` (25 rows), `WEAPONS_SHARED.json` (24 tunes), `Tools/scripts/jc3weapons.py`.
Cross-checked against `Research/JC3Grab/INDEX.jsonl`, `WEAPON_WIRING.jsonl` (G2-11, which consumes
this card), `Tools/scripts/wtunesurvey.py` + `adfdump.py`, and the game archives via
`wtunesurvey --gamedir`.

**Card as written:** list every path under `jc_weapons/06_vehicle/` and every
`jc_explosions/weapons/w6*.ftune`; extract each weapon `.ee` and its tunes; decode fire rate,
burst, damage per hit, damage type, projectile speed/gravity/lifetime, spread/recoil,
ammo/clip/reload or overheat, lock-on time/angle/range, homing, explosion radius and damage,
impulse; one row per id. Done: 25/25 ids with every decoded member, `--check` re-reads and compares.

---

## VERDICT

**The data reproduces; three sentences in the record are wrong and two decision-relevant choices
are invisible.**

```
$ python Tools/scripts/jc3weapons.py --check
PASS: 25 ids, 197 extracted files, 24 shared tunes, md 1223 lines            EXIT=0
```

Every headline count re-derives from the outputs and the archive index: 25 ids, 22 weapon
directories, 14 of them with an `.ee`, 61 index rows under `06_vehicle`, 161 sources, **4,054**
rows across the authoritative copies, 24 shared tunes, 197 files. The member vocabulary is
complete and self-consistent, the blast numbers match the generated tables, and the one naming
inversion (`fire_rate` is a period, not a rate) is stated and self-evidently right.

What does not survive:

| # | assumption | verdict |
|---|---|---|
| 1 | `--check` green proves the decode | **WEAK** — same code re-derives the same answer; it is a regression guard, not an oracle |
| 2 | a second, independent reader agrees | **BROKEN** — it agrees on 4 fields; its fifth (`turn`) returns `100.0` for every missile, against the catalogue's 4 distinct homing values |
| 3 | the patch copy is the authoritative tune | **WEAK** — right call, but 22/25 ids ship a second, different copy and the difference is never printed; `w618`'s base copy says turning 100, the patch says 0 |
| 4 | "vehicle weapon catalogue" covers the fleet's vehicle weapons | **WEAK** — the most common vehicle weapon, `w206` (19 components / 5 chassis), is outside the 25 rows, and so is the model-only id `w503` |
| 5 | 25 ids = every `06_vehicle` id | **HOLDS** — 22 dirs + 3 `+_impact`, 26 spellings, 1 alias, all verified against the index and §2.1 |
| 6 | `fire_rate` is seconds per shot | **HOLDS** — stated, and the MG/tank values only make sense that way |
| 7 | velocity/range are in m/s and m | **WEAK** — no unit is stated anywhere; gravity −9.82 is the only anchor |
| 8 | `tuning` = player, `ai_tuning` = AI | **WEAK** — inferred from one member name, and the two sides differ 16× (250 vs 15) |
| 9 | overheat is absent from JC3 | **WEAK** — true for the decoded vehicle tunes, but only player/vehicle weapons were searched |
| 10 | damage type is not a weapon property | **WEAK/BROKEN as worded** — no `damage_type` in the tunes, but 88 weapon components carry `impact_usage` |
| 11 | there is no `jc_explosions` tree | **WEAK** — no *archive entries* (true), but the inner paths in its own data are `jc_explosions/weapons/w6*.ftunec`, and §2.1 still cites one as an archive fact |
| 12 | the 24 shared tunes' members are printed verbatim | **BROKEN** — section 13 prints 11 |
| 13 | "4 of the 14 missile ids home" | **BROKEN count** — 11 missile ids exist; the 4 values are right |
| 14 | the 3 `+_impact` ids are blasts, not weapons | **HOLDS** — `ForcePulseSettings` only, container counts 11/3/2 |
| 15 | 161 sources / 4,054 members / 197 files / 67 containers | **HOLDS** — all recomputed |

**Bottom line:** this is a solid decode with an over-confident record. Fix four sentences (2, 10,
12, 13) and print the losing copy's diff for the 22 patch/base conflicts (3); the numbers
themselves need no re-decode. The one item a translation will trip on is `w618`'s homing — the
donor missile the card recommends as "a straight rocket" is a straight rocket only under the patch
copy, and nothing in `WEAPONS.md` says so.

---

## 1. `--check` green proves the decode

**Why the card rests on it.** The card's Done line is *"`--check` re-reads the archives and
compares"*, and the MODLOG's "Verified" paragraph is that command's output.

**Test.**

```
$ python Tools/scripts/jc3weapons.py --check
PASS: 25 ids, 197 extracted files, 24 shared tunes, md 1223 lines            EXIT=0
$ grep -n "def check\|--check" Tools/scripts/jc3weapons.py | head -4
```

`--check` re-runs the same decoder over the same bytes and compares the result with the file it
produced last time. That catches drift (a regenerated doc, a changed archive, a missing
extraction) — it cannot catch a decode that was wrong the first time, because both sides of the
comparison come from the same code. The only thing in the record that is *not* the same code is
the `wtunesurvey` cross-check, and that is §2 below.

**Verdict: WEAK.** The claim "every decoded member" is true of the reader's output by
construction; "correct" rests on the cross-check, which covers four fields.

---

## 2. A second, independent reader agrees

**Why the card rests on it.** MODLOG: *"**A second, independent reader agrees.** `wtunesurvey.py`
(text decode via `adfdump.py`, a different code path) ran over 10 containers: velocity,
max_range, fire_rate and magazine_size agree on every weapon it printed …"* This is the only
external evidence that the decode is right, and the row is called "the part worth trusting".

**Test 1 — reproduce it.** `wtunesurvey.py` and `adfdump.py` both ship, so it is re-runnable:

```
$ python Tools/scripts/wtunesurvey.py --gamedir "D:/Games/Just Cause 3" \
    editor/entities/jc_weapons/06_vehicle/w618_sportsmuscle_missile/w618_sportsmuscle_missile.ee
w618_sportsm blk=M vel=     360.0 rng=   300.0 fr=    0.5 mag=  -1 aiDmg= 5.0 vehDmg= 1.0 objDmg= 4.0 turn=['100.0'] ...
   blast w618_sportsmuscle_missile.ftunec: player 1100/8.0m  ai 500/8.0m
```

vel 360, rng 300, fr 0.5, mag −1, blast 1100/8 vs 500/8 — all four agree with
`WEAPONS.md` §2 and §8. So the four fields the MODLOG names are genuinely reproduced.

**Test 2 — the fifth field it prints.** `wtunesurvey` also prints `turn`, its own docstring calling
it the "homing indicator":

```
$ python Tools/scripts/wtunesurvey.py --gamedir "D:/Games/Just Cause 3" <9 missile .ee paths>
w608_fighter rng=300.0 turn=['100.0']
w609_fighter rng=750.0 turn=['100.0']
w611_fighter rng=300.0 turn=['100.0']
w612_fighter rng=300.0 turn=['100.0']
w613_fighter rng=300.0 turn=['100.0']
w615_helicop rng=300.0 turn=['100.0']
w618_sportsm rng=300.0 turn=['100.0']
w621_advance rng=300.0 turn=['100.0']
w619_buggy_m rng=200.0 turn=[]
```

`100.0` for every missile — including the four the catalogue says home at **75 / 150 / 300 / 200**
and the seven it says do not home at all. That is not a reading of the per-weapon member; it is a
constant picked out of the text by

```python
turn = re.findall(r"missile_turning_speed=float=([^;]+)", ai)
```

The catalogue's own dump of the same file disagrees with it and is internally consistent:

```
$ python Tools/scripts/jc3weapons.py dump w618 --max 400 | grep -i "turning_speed  "
  missile_weapon[0].tuning.missile_base_tuning.missile_turning_speed        float    0.0
  missile_weapon[0].ai_tuning.missile_base_tuning.missile_turning_speed     float    0.0
```

**Verdict: BROKEN as stated.** The cross-check is real for four fields and worthless for the
fifth; the MODLOG lists only the four that pass and calls it agreement. "Only 4 of the 11 missile
ids home" (see §13) therefore rests on `jc3weapons.py` alone, with no independent confirmation —
and homing is the property the card uses to recommend `w618` as the donor weapon.

---

## 3. The patch copy is the authoritative tune

**Why the card rests on it.** §1's table column "authoritative sources" and the intended-change
note: *"ranks patch > bundle > bundle-base for the authoritative copy."* Every value in
`WEAPONS.md` comes from the copy that ranking picks.

**Test.** The ranking is not cosmetic — 22 of the 25 ids carry a **second `WeaponTuning` with a
different digest**:

```
$ python - <<'EOF'   # per id, distinct digests per class among sources
ids with >1 distinct digest for the same class: 22
('w601_helicopter_missile', ['WeaponTuning'], {'WeaponTuning':
   [('37eed16e…', 'patch'), ('eb64d2ea…', 'bundle-base')]})
('w602_mediumtank_canon', … ('patch') vs ('bundle-base') )
…
```

and at least one of the differences is behavioural:

```
$ python Tools/scripts/jc3weapons.py dump w618 --max 60 | head -4
  source patch patch  …/w618_sportsmuscle_missile.wtunec  (14244 B, 155 rows)
  source base  bundle-base …/w618_sportsmuscle_missile.ftunec  (649 B, 8 rows)
  source base  bundle-base …/w618_sportsmuscle_missile.wtunec  (12773 B, 148 rows)
```

The patch copy has 155 rows and `missile_turning_speed` 0; the base copy embedded in the weapon's
own bundle has 148 rows and, per `wtunesurvey` (§2), `missile_turning_speed` 100. The catalogue's
headline — *"`w618` is a straight rocket (`missile_turning_speed` 0 …): that is the donor weapon"*
— is therefore a statement about the patch, and the base copy of the *same VFS path* says the
opposite.

**Is the choice right?** Yes, on the evidence available:

```
$ grep "w618_sportsmuscle_missile.wtunec" Research/JC3Grab/INDEX.jsonl
{"path":"editor/entities/jc_weapons/06_vehicle/w618_sportsmuscle_missile/w618_sportsmuscle_missile.wtunec",
 "hash":"37036E16","archive":"patch_win64/game1","mount":"patch",…}
```

The path exists **only** in the patch mount: the patch ships a deliberate standalone override of
the copy the base bundles embed, so patch-over-base is what the engine does.

**Verdict: WEAK.** The decision is sound, but the losing copy is recorded only as a digest. A
reader cannot see that `w618`'s homing differs between copies, nor how many of the 22 conflicts
are behavioural rather than a re-save. One line ("base said 100, patch says 0") would close it.

---

## 4. "Vehicle weapon catalogue" covers the fleet's vehicle weapons

**Why the card rests on it.** The card is the JC3 half of WPN-1…5 and the carrier list for the
translation; its id set is §2.1's 25.

**Test — the fleet's own wiring, from the next card:**

```
$ python - <<'EOF'   # WEAPON_WIRING.jsonl, distinct weapons[].name
distinct bound weapon names: 23
 19  w206_mounted_capstone_m2hm
  7  w602_mediumtank_canon
  7  w603_mediumtank_mgun
  …
catalogue ids: 25
bound but not in catalogue: ['w206_mounted_capstone_m2hm']
catalogue ids never bound to a vehicle: ['w604_helicopter_mgun_impact',
  'w610_fighterjet_mgun_impact', 'w617_vintagefighter_mgun_impact']
```

`w206` is the **most common vehicle weapon in the fleet** — 19 components over the APC, technical
jeep and armoured jeep — and it has no catalogue row. The doc is honest about it (§13-adjacent
table lists it as `other`, `WeaponTuning`, 148 rows, embedded 14 times) and G2-11 flags it again,
but the two facts together mean the deliverable named "vehicle weapon catalogue" is really "the
`jc_weapons/06_vehicle` id list plus three blasts". For WPN-2 (the Vulcan), `w206` is a plausible
candidate the catalogue cannot answer for.

There is a second id outside the list, visible from the monorail car's missile object (G2-11's
`WEAPON_WIRING.jsonl`):

```
"id:61641926": "models/jc_weapons/06_vehicle/w503_missile_capstone_billfire/w503_missile_capstone_billfire_body.model_xml"
"id:C253D5FD": "models/jc_weapons/06_vehicle/w503_missile_capstone_billfire/w503_missile_capstone_billfire_body_col.pfx"
```

`w503_missile_capstone_billfire` is a vehicle-class weapon id that ships **no entity directory and
no tune** (the index has only three model/texture files for it), so it cannot appear in a list built
from `jc_weapons/06_vehicle` directories — but it is the model the monorail's catalogued `w614`
missile fires. "25/25" is therefore true of the directory list and false of "every vehicle weapon
id the fleet names".

**Verdict: WEAK.** Scope is stated in the data, not in the title or the §12 row; "25/25" is 25/25
of a list that excludes the fleet's most-used gun.

---

## 5. 25 ids = every `06_vehicle` id, 22 dirs, 26 spellings, 1 alias

**Test — all four numbers against the index and §2.1.**

```
$ grep -oE "editor/entities/jc_weapons/06_vehicle/[a-z0-9_]+/" Research/JC3Grab/INDEX.jsonl | sort -u | wc -l
22
$ grep -oE "editor/entities/jc_weapons/06_vehicle/[a-z0-9_]+/[a-z0-9_]+\.ee\"" Research/JC3Grab/INDEX.jsonl | sort -u | wc -l
14
$ grep -c "editor/entities/jc_weapons/06_vehicle/" Research/JC3Grab/INDEX.jsonl
64        # minus the 3 models/jc_weapons/06_vehicle/w503_…_dif|mpm|nrm textures = 61
$ python - <<'EOF'   # ids in §2.1 vs the catalogue
ids in 2.1 text: 23 | base ids: 23
in 2.1 but not catalogue: ['w613_bomb']            # the alias, recorded as a spelling
in catalogue but not 2.1 base: ['…_impact' ×3]     # the 3 blast ids, as §2.1 says
```

The doc's "22 of the 25 ids have their own directory, 14 of those carry an `.ee`" is exact, and
the 8 without a bundle of their own are `w601`–`w607` + `w614`, exactly as the MODLOG says:

```
$ ls dirs with .ee → w608 w609 w610 w611 w612 w613 w615 w616 w617 w618 w619 w620 w621 w622   (14)
```

**Verdict: HOLDS.** This is the card's strongest claim and it checks out to the row.

---

## 6. `fire_rate` is seconds per shot

**Why the card rests on it.** §2's column header, and the reading a translation will copy.

**Test.** The member is called `fire_rate`, which reads as a rate; the doc treats it as a period
and says so: *"`fire_rate` is the seconds between shots (0.1 on the buggy MG is 10 shots/s)"*.

```
$ grep -n "fire_rate (s)" Research/JC3Grab/WEAPONS.md | head -2
57:| weapon id | block | fire_rate (s) | …
$ sed -n '60,61p' Research/JC3Grab/WEAPONS.md
| `w602_mediumtank_canon` | bullet | 1.75 | 1 | 0 | 0 | -1 | 0 | 1000 | 500 | 1 | -1 |
| `w603_mediumtank_mgun` | bullet | 0.1 | 1 | 0 | 1 | -1 | 0 | 200 | 750 | 1 | -1 |
```

Read as a rate, the MG would fire once per ten seconds and the tank cannon 1.75 rounds/s — both
absurd. Read as a period, the MG is 10 rps and the cannon one shot every 1.75 s — both normal.
`fire_rate_level_2` 0.12 (slower) fits the same reading. The doc resolved the name/behaviour
tension explicitly rather than by the member's name, which is what R5 asks for.

**Verdict: HOLDS.** Worth recording because it is the one place where the doc got a
name-inversion right, and a future reader who trusts the member's name will get it wrong.

---

## 7. Velocity and range are in m/s and m

**Why the card rests on it.** §2 carries `max_range` and `velocity` with no unit; §5, §6 and §10
list `velocity`, `missile_acceleration`, `tracer_fire_velocity` and never name a unit.

**Test.**

```
$ grep -rn "m/s\|km/h" Research/JC3Grab/WEAPONS.md
(no output)
$ sed -n '186p' Research/JC3Grab/WEAPONS.md
| `w618_sportsmuscle_missile` | missile | 0 | [200, 0] | [5, 0] | 0 | -1 | 0 | 1 | 1 | -9.82 |
```

The only anchor is gravity `-9.82`, which is −9.81 m/s² to two figures, so the engine's projectile
space is metres and seconds and velocity 500 is m/s. Range 200–1,000 then reads as metres, which
fits a 7 m car and a 1,000 m tank engagement. Nothing in the doc says this; a reader who assumed
cm/s (as `CAMERA.md` warns for other sim fields) would be out by 100.

**Verdict: WEAK.** Inferable and almost certainly right, but it is an unstated convention in a
file whose whole purpose is to hand numbers to a translator, and the sibling G1 doc
(`CAMERA.md` line 33) shows the project's habit of stating units — this file does not.

---

## 8. `tuning` is the player's numbers and `ai_tuning` the AI's

**Why the card rests on it.** §3's column pairs "player dmg / AI dmg", the MODLOG table, and the
prose *"the AI side is what an NPC-fired copy of the same weapon does."*

**Test.** The only evidence is the member name and the block structure:

```
$ sed -n '91,92p' Research/JC3Grab/WEAPONS.md
| `w604_helicopter_mgun` | bullet | 250 | 0.1 | 0.75 | 100 | 15 | 0.15 | 0.2 | 40 |
| `w605_smalltank_canon` | bullet | 1 | 5 | 1 | 0 | 15 | 10 | 0 | 0 |
```

Two sibling blocks, one literally named `ai_tuning`; calling the other one "player" is the
reasonable complement, and no script body was traced to confirm which side the player's shot
reads. Unlike G1's damage rules — where `CalculateAndStoreImpactDamage` is decompiled and its
field reads are listed — there is no behavioural trace here. The stakes are large: the medium-tank
MG is 190 as "player" and 20 as "AI" (9.5×), the helicopter MG 250 vs 15 (16×).

**Verdict: WEAK.** Structurally likely, semantically unproven. A one-line note ("the split is the
`ai_tuning` member name; no script read was traced") would make the row honest at R4/R5, and the
translation should treat 190/250 as the number to copy without claiming it is the player's.

---

## 9. Overheat is absent from JC3

**Why the card rests on it.** The card's Do step asks for "overheat (heat per shot, cool rate)";
§10 answers *"**proven absent**"*, and the MODLOG escalates to *"**Overheat is absent from JC3.**"*

**Test 1 — inside the corpus.**

```
$ grep -oiE '"[a-z0-9_.]*heat[a-z0-9_.]*"|"[a-z0-9_.]*cool[a-z0-9_.]*"|"[a-z0-9_.]*temperature[a-z0-9_.]*"' Research/JC3Grab/WEAPONS.jsonl | sort | uniq -c
     66 "burst_cooldown"
$ grep -c -i heat Research/JC3Grab/WEAPONS.md
6        # all prose, no member
```

So within 22 `WeaponTuning` + 3 `AutoAim` + 9 `ForcePulseSettings` + 24 shared tunes there is no
heat, cooling or temperature member. `burst_cooldown` is a burst gap, and the doc says so.

**Test 2 — outside the corpus.** The search is scoped to the vehicle-weapon tune classes. Player
weapons (`w1xx`), `CBarrelSpinWeaponComponent`-style barrel heat and HUD heat bars were not
decoded by this card. The repo's own README records where heat actually lives:

```
$ grep -rn -i "overheat" Research/JC3Grab/README.md
295: … an overheat member, and that damage type lives on the part/health side, not the weapon.
495: … the Batmobile's Vulcan heat bar is a weapon-entity script variable (`HeatBarStart`/`HeatBarSize`)
```

— BmAK's heat bar is a BmAK script variable, and the JC3 side has none in the vehicle tunes.

**Verdict: WEAK.** True for everything decoded; the absolute sentence "absent from JC3" is a
game-wide claim from a 25-id sample of the game's weapon classes. The consequence the card draws
(the Vulcan's heat must be a BmAK-side behaviour) is unaffected.

---

## 10. Damage type is not a weapon property

**Why the card rests on it.** §10's row and the MODLOG's summary: *"damage type is a part/health
concept, not a weapon one."*

**Test.**

```
$ grep -c -i "damage_type" Research/JC3Grab/WEAPONS.jsonl
0
$ grep -o "impact_usage" Research/JC3Grab/WEAPON_WIRING.jsonl | wc -l
88
$ python -c "…first weapon row of WEAPON_WIRING.jsonl…"
{"name": "w206_mounted_capstone_m2hm", …, "impact_usage": "50CalBulletImpact", …}
```

No tune member names a damage type — that half holds. But every one of the **88** weapon
components in the next card carries `impact_usage`, a weapon-side property that selects the
impact/damage class (`50CalBulletImpact`), which is exactly the kind of "which damage is this"
value the claim says weapons do not have. G2-10's own doc is careful ("no member of any of the
decoded classes"), but the MODLOG sentence is not, and G2-28 will read the MODLOG.

**Verdict: WEAK for the doc, BROKEN for the MODLOG sentence.** The typing is not in the *tune*;
it is on the *weapon component*. Stating the second half as "not a weapon one" is wrong in the
direction that matters — a translator looking for the damage class should look at
`impact_usage`, not only at `PARTS_TABLE.jsonl dt`.

---

## 11. There is no `jc_explosions` tree

**Why the card rests on it.** Card step 1 asks to list "every `jc_explosions/weapons/w6*.ftune`";
§1 answers *"**No `editor/entities/jc_explosions/` tree.** … the whole game has exactly two
standalone `.ftunec` archive entries, neither a weapon."*

**Test 1 — as archive entries, the claim is exact.**

```
$ grep -oE '"[^"]*\.ftunec?"' Research/JC3Grab/INDEX.jsonl | sort | uniq -c
      1 "editor/entities/jc_explosions/gen_explosion_0.5m_nodamage.ftunec"
      1 "editor/entities/jc_explosions/structures/barrel_explosion.ftunec"
$ grep -iE "w6[0-9][0-9].*\.ftune" Research/JC3Grab/INDEX.jsonl
(no output)
```

**Test 2 — the same path exists inside the bundles, and that is where the card's own data points.**

```
$ python -c "…w618 sources…"
origin=bundle-base … path=editor/entities/jc_explosions/weapons/w618_sportsmuscle_missile.ftunec
origin=bundle      … path=editor/entities/jc_explosions/weapons/w618_sportsmuscle_missile.ftunec
```

So the "tree" exists as an **inner VFS path inside `.ee` bundles**, which is exactly what the doc
says elsewhere in the same paragraph. The finding is sound; the phrasing "No
`editor/entities/jc_explosions/` tree" invites the opposite reading from the file that lists
`editor/entities/jc_explosions/weapons/w618_….ftunec` six lines later.

**And it leaves the backlog wrong.** §2.1 still cites that path as archive evidence:

```
GRAB_BACKLOG.md:293: … and
`editor/entities/jc_explosions/weapons/w618_sportsmuscle_missile.ftune`. Our donor's own parts
```

G2-10 says "recorded, not litigated", but it is the card that discovered the path is not an
archive entry — §2.1's evidence line should have been corrected (`§0`: "when they disagree about a
measured fact, the evidence file wins and this file must be corrected").

**Verdict: WEAK.** The absence is real at archive level and mis-stated at path level; the
backlog's contradictory evidence path was left standing.

---

## 12. The 24 shared tunes' members are printed verbatim

**Why the card rests on it.** §7: *"**24 tunes in the fleet's bundles name no weapon id** … Their
members are printed verbatim in section 13."* The file's header claims the md holds "every decoded
member of every authoritative tune".

**Test.**

```
$ grep -n "^### \`" Research/JC3Grab/WEAPONS.md | sed -n '4,20p'
893:### `autoaim_aa_gun`
922:### `autoaim_assault_rifle`
950:### `autoaim_grenade`
979:### `autoaim_pistol`
1008:### `autoaim_rpg`
1037:### `autoaim_rpg_mm110`
1066:### `autoaim_smg`
1095:### `autoaim_sniper_rifle`
1124:### `autoaim_vehicle_lockon_missile`
1152:### `autoaim_vehicle_mgun`
1180:### `autoaim_vehicle_no_lockon_missile`
```

Eleven, all `autoaim_*`. The other 13 — `airplane_explosion_medium`, `boat_explosion_large/medium`,
`car_explosion_medium`, `helicopter_explosion_medium`, `rpg_assault_helicopter`,
`train_explosion_medium`, `prototype_*`, `w206_*` — appear only as one-line membership rows
(`| `car_explosion_medium` | other | `ForcePulseSettings` | - | 18 |`) and in the §12 vocabulary.
Their members are in `WEAPONS_SHARED.json`, not in the markdown.

**Verdict: BROKEN.** A factual sentence about the deliverable that is false for 13 of 24 items.
Either print them or say "the 11 AutoAim presets are printed; the 13 other tunes live in
`WEAPONS_SHARED.json`".

---

## 13. "Only 4 of the 14 missile ids home at all"

**Why the card rests on it.** MODLOG's reading paragraph, and it is the sentence that makes `w618`
the recommended donor ("straight rocket").

**Test.**

```
$ python - <<'EOF'
missiles: 11
turning_speed>0: [('w608_fighterjet_missile', 75.0), ('w609_fighterjet_missile_air_lockon', 150.0),
                  ('w612_fighterbomber_missile_air_lockon', 300.0), ('w614_monorailmissilecar_missile', 200.0)]
EOF
```

Eleven missiles, four of which turn; the four values (75 / 150 / 300 / 200) are exactly right and
match §5. There is no fourteenth missile id in the catalogue, in §2.1, or in the wiring — the
number is typed prose where the rest of the file is generated (R11).

**Verdict: BROKEN count, correct values.** "4 of the 11" is the true sentence. Small, but it is
the sort of number a later session will quote.

---

## 14. The 3 `+_impact` ids are blasts, not weapons

**Why the card rests on it.** The card says to "count the `+_impact` variants separately", and
"25/25" includes three ids that are not weapons.

**Test.**

```
$ python -c "…kinds…"
'w604_helicopter_mgun_impact': 'impact', 'w610_…_impact': 'impact', 'w617_…_impact': 'impact'
$ python -c "…sources for w604_impact…"
origin=bundle-base classes=['ForcePulseSettings'] rows=8 … w604_helicopter_mgun_impact.ftunec
$ grep -n "_impact\` | no | impact" Research/JC3Grab/WEAPONS.md   # containers per impact id
33:| `w604_helicopter_mgun_impact` | no | impact | - | 11 | bundle(ForcePulseSettings) | - |
40:| `w610_fighterjet_mgun_impact` | no | impact | - | 3 | bundle(ForcePulseSettings) | - |
48:| `w617_vintagefighter_mgun_impact` | no | impact | - | 2 | bundle(ForcePulseSettings) | - |
```

`ForcePulseSettings` only, no `WeaponTuning`, no archive directory of their own, found only inside
the vehicles that fire the matching gun, and the container counts (11 / 3 / 2) match the census
counts the MODLOG cites. `w206`'s grip points are likewise listed as `other` and not as weapons.

**Verdict: HOLDS.** The one place where the card distinguishes a name from a behaviour and gets
it right.

---

## 15. The headline counts

**Why the card rests on it.** The §12 row and the MODLOG lead with them.

**Test — recomputed from the outputs, not quoted:**

```
$ python - <<'EOF'
sources: 161 | sum rows of authoritative sources: 4054
class occurrences: {'WeaponTuning': 103, 'ForcePulseSettings': 43, 'AutoAim': 15}
WEAPONS_SHARED: list of 24
distinct containers named in sources: 53 (14 weapon .ee + 39 vehicle .ee)
EOF
$ python Tools/scripts/jc3weapons.py --check
PASS: 25 ids, 197 extracted files, 24 shared tunes, md 1223 lines
```

161 ✓, 4,054 ✓ (it is specifically the **authoritative** rows — 17,826 if every duplicate copy is
counted, which is why the definition matters), 24 ✓, 197 ✓, 14 weapon bundles ✓. The "67 `.ee`
containers opened" is 14 + 53 as stated; only 53 containers contribute a source after
duplicate-digest collapse, which is consistent and not a contradiction.

**Verdict: HOLDS.** All verified; the 4,054 figure in particular is the right quantity (authoritative
copies only), which is the kind of definitional care the rest of the record does not always show.

---

## What would make this card honest (no new decoding needed)

1. Delete "A second, independent reader agrees" or scope it to four fields, and say plainly that
   `wtunesurvey`'s `turn` is not a per-weapon read (fix its regex or drop the column from the claim).
2. Print, for the 22 patch/base conflicts, one line each: which member differs and by how much.
   `w618`'s `missile_turning_speed` 100 → 0 is the one that changes a recommendation.
3. Correct §7's "printed verbatim in section 13" to the 11 AutoAim presets.
4. Correct "4 of the 14 missile ids" to "4 of the 11".
5. Scope the two absence sentences: "no overheat member in the 25 decoded vehicle tunes"; "no
   damage type in the tune — the weapon component carries `impact_usage`".
6. State m/s and m next to velocity/range, and that the player/AI split is the `ai_tuning` member
   name with no traced read.
7. Fix `GRAB_BACKLOG.md` §2.1's `jc_explosions/weapons/w618_….ftune` evidence line to say it is an
   inner bundle path, not an archive entry — or note the correction in the G2-10 entry.
