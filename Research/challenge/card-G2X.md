# Assumption challenge — card G2X · G2 exit gate

Written 2026-10-30. **Read-only review:** nothing in `GRAB_BACKLOG.md`, `MODLOG.md`, `Research/`,
`Tools/`, `Builds/` or any game file was modified; the only file written is this one. No game was
launched, nothing was installed into `D:\Games`, nothing was committed. Only `--check` paths that
write nothing were executed; the "Method and limits" section records the check that the gate's own
artefacts kept their `00:27` mtime through the runs.

**In scope.** `GRAB_BACKLOG.md` §0.5 (R1–R14), the G2X gate text (§6, last paragraph, line 823),
the §12 row (line 1318), `MODLOG.md` §"G2X · G2 exit gate — intended change" / "— passed" /
"G2X rework — done" (lines 11997–12119 and 16470–16576), and the card's three outputs
`Tools/scripts/g2x_gate.py`, `Research/JC3Grab/G2X.md`, `Research/JC3Grab/G2X.json`.

**Card as written** (§6): *"every new reader has `--check` green; P0-2 census re-run; every feature
code in §1 has a JC3 carrier with evidence or a proven absence. MODLOG section 'G2X'."*

**What the card claims** (§12 row): 75 codes **parsed from §1**, 67 carrier with labelled evidence
(7 numbers / 43 identifiers / 8 phrases / 9 short words), 8 proven absence, all negative scans with
a per-file anchor; the 24 G2 readers + P0-2 census re-run 25/25 green; 7 decision-gated, 0 open.

---

## VERDICT

**The mechanics reproduce exactly and the gate is genuinely green today; the step from "a needle is
in the file" to "this code has a JC3 carrier" is where it fails.** Of the 21 assumptions tested in
§1–§21, **9 HOLDS (one with a caveat), 9 are WEAK, and 3 are BROKEN.** Two of the broken rows (LGT-2, MOD-4/ANI-8) are named "carrier" while the
only evidence in the file is the *plan* or a *BmAK label*; one (the needle method itself) matches
sentences that say the opposite of the claim.

| # | assumption | verdict |
|---|---|---|
| 1 | the gate is green on disk today, with the 25 readers re-run | **HOLDS** |
| 2 | "every feature code in §1" = the 75 rows the gate parses | **HOLDS** |
| 3 | a needle hit means the code's carrier is in that file | **BROKEN** — 4 of 67 rows key on a negation, an omission phrase, a deferral or a row id |
| 4 | LGT-2's battle spotlight is a second JC3 *behaviour* value | **BROKEN** — `VEHLT_BattleModeLight` is the BmAK source label; both recipe entries use `HeadLight`, and no shipped entry has that behaviour value |
| 5 | MOD-4/ANI-8 "canopy opens" is a decoded door behaviour | **WEAK** — one forward-looking line, on a door census of 55/233 graphs |
| 6 | MOD-3 "ejection" is carried by `exit.driver.moving.parachute` | **WEAK** — that is a parachute *exit*; the launch half is UNKNOWN by the card's own doc |
| 7 | WLD-6 "30 s engine shut-down" is a behaviour | **WEAK** — `WATER.md` says the `_ms` unit is UNKNOWN and "the name is the only evidence" |
| 8 | WPN-6's winch absence is proven | **HOLDS** — `winch` = 0 of 81,952 index paths, 0 classes, 0 of 67 part behaviours |
| 9 | the 8 absences are scanned against a *complete* census | **WEAK** — 232 of 233 entities, 232 of 314 vehicle `.ee` paths |
| 10 | the module vocabulary is complete (52 types / 1,421 paths) | **BROKEN** — a second gate-green reader counts 53 module types; both artefacts cannot be right |
| 11 | "no sonar / tracker / allegiance carrier" is a statement about JC3 | **WEAK** — true of the vehicle classes; the index contains a sonar upgrade, a mission tracker, `factions.bin`, 288 hijack paths |
| 12 | a substring word scan is a proof of absence | **WEAK** — it over-matches (`stun`→`stunt`, `heal`→`health`, `rope`→`propeller`) and cannot see synonyms |
| 13 | DIM-2's evidence file carries the wheel radius | **WEAK** — `PHYSICS.md` has no "radius"; the member is in `VOCABULARY.md`, and the station cross-check is 17 of 145 |
| 14 | APP-1's 56,136 is the body mesh count (and the fleet is 233) | **HOLDS as stated** (the fact now calls it a fleet count); the fleet number is not stable — see §15 |
| 15 | one fleet denominator underlies the gate | **WEAK** — 233 / 232 / 223 / 224 / 232 appear in five evidence files |
| 16 | mass 975 / 6,000 / 6.154 is usable | **HOLDS** — 232 entities, ratio is unit-free and exact |
| 17 | the turret's ±179° is decoded, not a unit guess | **HOLDS** — 194 hinge rows, all within ±π, deg = rad × 57.29578 for 194/194 |
| 18 | ANI-9's seat is 10 mm under the hip | **WEAK** — 0.8647 − 0.855 = 0.0097, but a hull *centre* is not a sitting surface and the car does not own the pose |
| 19 | the reader set is complete and every reader is independent evidence | **HOLDS with caveat** — 25 subprocesses, all card `Out:` scripts covered; the list and labels are typed |
| 20 | 0 decisions open | **HOLDS** — 10 register rows, all "resolved 2026-10-28 (user)" |
| 21 | the build really carries the tank's 2000 HP (a fact cell) | **HOLDS** — int32 2000 present in `Builds/test-091`'s health module |

(The table numbers 1–21 because §3 and §4 split into four probes; the sections below are 1–17 and
the mapping is given per section.)

**Bottom line.** G2X answers "is this mechanism named somewhere in a generated file?" — and it
answers that cleanly and reproducibly. Three rows answer it in the wrong direction or on the wrong
side of the gate: **LGT-2** (a BmAK label, not a JC3 behaviour), **MOD-4/ANI-8** (a plan sentence),
and the **needle method** generally (WPN-5's needle is the sentence "no as a weapon-slot copy").
One numerical claim is internally contradictory: the vocabulary the absence rows scan has **52**
blocks while a gate-green reader measures **53** module types in the same 232 caches (§10). None of
this changes the *count* of 67 carriers — it changes what four of them are worth. The smallest fix
is mechanical: make every needle a value or an identifier on a line that asserts the fact, move
LGT-2/MOD-3's missing halves into the absence list (or into `UNKNOWN`), and take the 53-type count
from the same reader that produces the vocabulary.

---

## 1. The gate is green on disk today, and the reader half is really executed

**Why the card rests on it.** The §12 row and the MODLOG say `done` because `--check` exits 0. The
rework already found the gate red once (8 issues, 2026-10-29), so "green" is a live claim, not a
formality.

**Test.** Full re-run (all 25 subprocesses), then the fast mode, then a mtime check.

```
$ python Tools/scripts/g2x_gate.py --check
PASS: 75 codes (67 carrier, 8 absence, 7 decision-gated) in 29 files | readers 25/25 green (re-run) | census ok | json match True, md match True
EXIT=0

$ python Tools/scripts/g2x_gate.py --check --no-readers
PASS: 75 codes (67 carrier, 8 absence, 7 decision-gated) in 29 files | readers 25/25 green (recorded) | census ok | json match True, md match True
EXIT=0
```

`run_reader()` starts each script as a subprocess and requires exit 0 **and** a line beginning
`PASS`/`OK`/`check ok`; `jc3hkx.py write --check` writes nothing (its writes are gated on
`a.write`, lines 2192–2206), so the run is read-only. Two of the standing gates the G2X section
quoted were also re-run: `jc3index.py check` → `check ok: 81952 rows, 78907 paths, 1 unnamed
entries` (exit 0) and `jc3fx.py check` → `checked 57187 files | problems 0` (exit 0).

**Verdict: HOLDS.** The gate passes today with the readers re-run, not remembered.

---

## 2. "Every feature code in §1" = the 75 rows the gate parses

**Why the card rests on it.** `section1_codes()` is the only thing that stops the gate from grading
itself. If §1 contained a code the regex misses, the gate would silently cover 74 of 75.

**Test.** Parse §1 with the gate's own function, then look for code-shaped tokens the regex does
not take, and count §1's table rows independently.

```
gate parse: 75 codes; dupes 0
loose tokens in §1: 98 distinct; not parsed by the gate: 23
    DMG-2 1   G1-08 1   G1-09 1   G1-10 2   ...   POL-3 1   RD-1 1
§1 table lines: 95
§1 rows whose first cell is not a parsed code: 20
```

The 20 non-code lines are exactly 10 header+separator pairs (the ten family tables × 2, including
the `BmAK object (class)` table); the 23 loose tokens are legacy ids cited inside cells,
not rows — `GRAB_BACKLOG.md:147` (*"private health module (DMG-2)"*), `:225` (*"(`RD-1`)"*),
`:226` (*"(`POL-3`)"*), plus cross-references to G1/G2 cards. No table row starts with a code the
gate drops.

**Verdict: HOLDS.** 75 code rows, 75 parsed. The *row contents* (files, needle, fact) are still
hand-typed; only the code set is parsed — see §3 and §21.

---

## 3. A needle hit means the code's carrier is in that file

**Why the card rests on it.** This is the whole of clause 3: `ok = needle.lower() in
read_text(files[0]).lower()` (g2x_gate.py, `check_rows`). 67 of 75 codes are decided by one
case-insensitive substring in one file, anywhere in it.

**Test (a): a needle that is the negation.** `WPN-5`'s needle is `weapon-slot copy`.

```
$ grep -n -i "weapon-slot copy" Research/JC3Grab/EMP.md
3:G2-16. **Answer: yes for the effect, no as a weapon-slot copy.** Everything the truck's EMP
```

The string occurs **once**, inside the answer that says it is *not* one. The row's verdict is
`carrier`. The carrier sentence exists two lines later ("yes for the effect"), so the substance is
fine — but the gate would stay green if the doc said only "no".

**Test (b): a needle that is the omission phrase.** `MOD-2`'s needle is `named omission`, verdict
`carrier`.

```
$ grep -n -i "named omission" Research/JC3Grab/TANKTURN.md
10:data: **MOD-2's turn-on-the-spot is a named omission**, carried by native code keyed to
116:**Turn-on-the-spot has no JC3 data carrier** - it becomes a named omission for MOD-2:
```

Both hits state the *absence*. MOD-2's real carrier (turret/cannon parts) is proven by
`TURRET.md` and by row ANI-2, not by this needle.

**Test (c): a needle that is a deferral.** `AUD-4`'s needle is `deferred with D-2`.

```
$ grep -n "deferred with D-2" Research/JC3Grab/JC3_AUDIO.md
217:| AUD-4 | `battle-mode` group, 30 events / 75 WEMs | no mode-switch event in the donor; D-2 decides if a second variant ships | deferred with D-2 |
```

That is the `now` cell of the row, i.e. "not decided yet", counted as a carrier.

**Test (d): a needle that is a row id whose cell says there is no carrier.** `CAM-2`'s needle is
`T-CAM10`.

```
$ grep -n "T-CAM10" Working/Translation/T6_HUD_CAMERA.md
135:| T-CAM10 | `BattleModeCamFOV` 60, `BattleModeWinchCamFOV` 60, `AntiPersonel` 40 | none | — | — |
     **superseded by T-15** (D-2): no battle-camera member, but a second per-entity `.ctune` is the carrier ...
```

The needle is an id; the carrier claim (a second `.ctune`) lives in the explanation cell. A row id
is the weakest possible identifier.

**Verdict: BROKEN as an evidence test.** Not because any of these four codes lacks a carrier, but
because the test cannot distinguish a carrier from its negation, its omission, its deferral or its
own id. The md labels needle *strength* (7 numbers / 43 identifiers / 8 phrases / 9 words) but not
*polarity or scope*, which is what fails here.

---

## 4. LGT-2 — the "battle-mode spotlight" is a second JC3 behaviour value (R5)

**Why the card rests on it.** Row: `LGT-2 | carrier | ... | the battle spotlight is the same
socket's second behaviour value — needle VEHLT_BattleModeLight`. §1: *"Battle-mode spotlight, if
battle mode exists (D-2) | extra `SVehicleLight`"*.

**Test.** Where the string occurs, and what the shipped behaviour vocabulary is.

```
$ grep -n "VEHLT_BattleModeLight" Research/JC3Grab/LIGHT_SYSTEM.md
227:The same socket also carries 1 `VEHLT_BattleModeLight`
228:entry (VEHLT_BattleModeLight -> HeadLight) - that is LGT-2's battle-mode spotlight, a second entry ...
```

```
$ python  # count occurrences per file
Research/JC3Grab/LIGHT_SYSTEM.json BATTLEMODE occurrences: 1
   ... "material_type": "VEHLTMAT_Special3", "type": "VEHLT_BattleModeLight" } ], "battle_mode_count": 1, "behavior": "HeadLight", "bone": "Wheel_Frnt_Left_Disc",
```

The single JSON occurrence is under `recipe/bmak/battle_mode[0]/type` — the **BmAK** side of the
recipe. The JC3-side table in the same file gives `behavior = HeadLight`, with the arrow
`(VEHLT_BattleModeLight -> HeadLight, G1-17 mapping)`, i.e. the mapped JC3 behaviour is the
ordinary headlight. And the shipped entries' behaviour census is:

```
| behavior | entries |
| None | 1177 | HeadLight | 1027 | TailLight | 301 | LeftSignal | 253 | RightSignal | 253 |
| Reverse | 191 | SirenLightOn | 9 | SirenLightOffOnFast | 3 | SirenLightOnOffFast | 3 |
```

`VEHLT_BattleModeLight` is not among the 9 values used by any of the 3,217 shipped entries. So the
"second behaviour value" in the row's fact does not exist: there would be a second *entry* with the
**same** behaviour, and the "battle-mode spotlight" identity comes from a BmAK component name.

**Verdict: BROKEN.** LGT-2 is a name read as a behaviour (R5, exactly): the needle is a BmAK label
inside the recipe, and the fact ("second behaviour value") is contradicted by the same file's
behaviour census. The mechanism that might ship (an extra lamp entry) is real; the claim that it is
a distinct battle behaviour is not evidenced anywhere.

---

## 5. MOD-4 / ANI-8 — "the canopy opens" is a decoded door behaviour

**Why the card rests on it.** Two rows, one needle: `MOD-4 | ... | door behaviour + part index +
limited hinge ... : the canopy can open — needle canopy` and `ANI-8 | ... | the same door behaviour
covers the canopy on entry/exit — needle canopy`.

**Test.** Every `canopy` occurrence in `DOORS.md`, and the census size the door doc itself states.

```
$ grep -n -i "canopy" Research/JC3Grab/DOORS.md
134:For a B-05 canopy the actionable
135:form is: X-axis limited hinge on a `Hood`/`FrontLeftDoor` part, listed in
136:`door_parts[]`, plus the `entry.driver` path if the door is meant to be used.
```

One occurrence, and it is a forward-looking recipe sentence about the Batmobile — not a decoded
JC3 canopy. The decoded door evidence in that file is the donor's `door_f_l`/`door_f_r`/`hood` and
the monorail's 16 `MissileHatch`, none of which is a canopy. The file's own limits section:

```
The census covers the 78 cached parts modules (56 with doors) and the 55 cached
`.epe` graphs, not all 233 entities.
...
it is a hinge with no curve, driven by whatever runs after `S_ENTER_DRIVER_VEHICLE`.
```

So the door *mechanism* (a hinge + `door_parts[]` + an entry path) is real and decoded — for a
`Hood`/`FrontLeftDoor` part on 56 of 233 door modules — and the canopy is the author's plan to use
it. Both halves are true; the row's `carrier` verdict reads the plan as the evidence.

**Verdict: WEAK.** The mechanism holds (and is independently proven by the donor's own hood/doors),
but the needle proves nothing and the sample is 55/233 graphs — a "fleet-wide" word on a quarter of
the fleet.

---

## 6. MOD-3 — ejection is carried by `exit.driver.moving.parachute`

**Why the card rests on it.** §1 MOD-3: *"Ejection: hold-to-eject launches the driver into the air
(Batman glides)"*; the row's fact: *"exit.driver.moving.parachute is the fast exit on 221/232
vehicles; the upward launch has no member"*.

**Test.** The exit doc's own mapping, and the count in §1 versus the count in the evidence file.

```
$ grep -n "moving.parachute" Research/JC3Grab/EJECT.md
11:`exit.driver.moving.parachute` → `S_EXIT_VEHICLE_PARA` — that is the
131:| `exit.driver.moving.parachute` | 221 | 125 | 35 | 23 | 19 | 19 | `S_EXIT_VEHICLE_PARA` |
```

```
$ grep -n "MOD-3" GRAB_BACKLOG.md | head -2
191:| MOD-3 | Ejection: hold-to-eject launches the driver into the air (Batman glides) | ... (present on 220 entities) ...
1298:(...) `S_EXIT_VEHICLE_PARA` is *the fast exit*, present on 221/232 vehicles (125 cars, 35 boats, ...)
```

Two findings: the requirement's *launch* half has no member (the card says so), so the carrier is
the exit half only; and §1's typed "220" disagrees with `EJECT.md`'s 221 (R11: counts are generated,
never typed — the code set is parsed, the counts in §1 are not).

**Verdict: WEAK.** A parachute exit is not an ejection launch; the row is a carrier for the exit
path and the launch stays UNKNOWN. The 220/221 drift is cosmetic but shows the same typed-text
problem.

---

## 7. WLD-6 — the "30 s engine shut-down" is a behaviour

**Why the card rests on it.** `WLD-6 | ... will_sink + buoyancy + the fleet-wide water-entry damage
and 30 s engine shut-down — needle will_sink`. §1 WLD-6 asks for "sinks and stalls".

**Test.** The source paragraph behind the number.

```
$ sed -n '230p;239p' Research/JC3Grab/WATER.md
| `car_common.engine_shut_down_delay_s` | `30` x232 |
So the *kill* side is fleet-wide: ... the engine shut-down delay is 30 s for cars and 5 s for every
```

```
$ sed -n '239p' Research/JC3Grab/WATER.md   # the same paragraph, continuation
other class. **No vehicle overrides any of them** ... and the unit behind the `_ms` suffix is not
decoded here (`UNKNOWN`): 10/20 ms is too short to be a drown timer, so the name is the only
evidence of what the numbers mean.
```

The source is scrupulous: the member is fleet-wide and unoverridden (232/232 — that part holds), but
its *unit* and therefore its semantics are UNKNOWN and the name is the only argument. The gate's
fact drops that caveat and states "30 s engine shut-down" as a behaviour. The same `WaterInteraction`
row *is* behaviourally supported (`will_sink` 1 on 189, and 10 sinkers ship an empty hull, so the
mesh is not the switch).

**Verdict: WEAK.** A member name promoted to a behaviour in the summary, with the source's UNKNOWN
removed. The sink half is fine; the stall half is name-level.

---

## 8. WPN-6 — the winch absence is proven

**Why the card rests on it.** The row is one of the 8 `absence` verdicts; the backlog's §1 WPN-6 is
`Batmobile_Winch` (`RBatmobileWinch`) — a power winch.

**Test.** Word absence at three levels: the whole archive index, the vocabulary and class census,
and the behaviour census.

```
$ grep -c -i "winch" Research/JC3Grab/INDEX.jsonl
0
$ grep -c -i "winch" Research/JC3Grab/VOCABULARY.md Research/JC3Grab/ENTITIES.md
Research/JC3Grab/VOCABULARY.md:0
Research/JC3Grab/ENTITIES.md:0
```

```
$ python  # TETHER.json, winch block
behaviour: 67 distinct names; winch/tow/reel absent; nearest is CargoBayDoor x28
functional_winch_classes: 0
entities: 4        # the transport boat's parts module
names: {'transport_rope_winch': 4, 'transport_rope_01': 4, ...}
```

`TETHER.md` §4 also shows the winch **mesh** ships (`transport_rope_winch`, part 26, `Boat_Generic`,
`behavior = None`, parent 0, 5 LOD RBMs) and says so: *"a carrier exists for the geometry ... and
the mechanic is a proven absence"*. The word `winch` is absent from all 81,952 index paths, all 52
vocabulary blocks, all 103 classes and all 67 part behaviours.

**Verdict: HOLDS.** This is the best-supported absence in the set: three independent surfaces, and
the one positive hit (a mesh) is named and scoped by the same file. The only wrinkle is that
`G2X.md` calls WPN-6 an "absence" while `TETHER.md` calls it "a carrier exists for the geometry" —
same facts, opposite headline words.

---

## 9. The 8 absences are scanned against a *complete* census

**Why the card rests on it.** Every absence row's verdict means "no such mechanism in the decoded
fleet". That is only true if the two census files are the whole fleet.

**Test.** Count entities per artefact, and count vehicle entity paths in the index.

```
$ sed -n '3p;10p' Research/JC3Grab/GEOMETRY.md
Every mesh block in the 233 vehicle entities, decoded from the `.ee` bundles by
| entities | 233 |
$ sed -n '3p;46p' Research/JC3Grab/ENTITIES.md
Derived from **232** decoded `.epe` graphs and their `.rbm` headers by
| `CParts` | 233 |
$ sed -n '3p' Research/JC3Grab/VOCABULARY.md
Derived from **232** decoded `.ee` entities by `Tools/scripts/jc3grab.py`.
```

```
$ python  # INDEX.jsonl, paths under jc_vehicles
vehicle .ee paths : 314
vehicle .epe paths: 232
```

`ENTITIES.md`'s class inventory is 103 rows (verified by counting the inventory table; the rarest
classes have count 1, so it is a per-object census of the 232 graphs, not a sample of classes). But
it is a census of **232 of the 233 entities** the same project decodes, and of **232 of the 314
vehicle `.ee` paths** in the index. The 82 uncovered paths look like DLC/variant twins
(`..._blackhand_01`, `..._rebel_02`) of decoded models — but that is an inference, not a measurement,
and the one entity with `CParts` but no `.epe` graph is exactly where a class the absences forbid
could live.

**Verdict: WEAK.** "Complete" is true of the 232 decoded graphs and false of the index's 314
vehicle paths; the two missing denominators are never named in `G2X.md`.

---

## 10. The module vocabulary is complete: 52 types, 1,421 paths

**Why the card rests on it.** Four absence rows (ARM-5, WPN-10, HDL-6, and WPN-6's first file) scan
`VOCABULARY.md`; the gate's docstring and every one of those facts repeat "the 52-type / 1,421-path
vocabulary". If a type is missing, a member in it is invisible.

**Test.** Count the file's blocks and rows, then ask the other gate-green reader that measures the
same thing.

```
$ grep -c '^## `' Research/JC3Grab/VOCABULARY.md
52
$ grep -c '^| `' Research/JC3Grab/VOCABULARY.md
1421
$ python  # TETHER.json (written by jc3tether.py --write, run green by this gate)
module_types: 53
```

`TETHER.md:174` spells it out: *"The fleet's **53** module types contain 0 tether/cargo/rope/winch/tow
type"*. `SEAT.md:20` says *"the fleet's module vocabulary is 52 types"*. Two gate-green readers,
generated from the same 232 entity caches, disagree by one. Therefore at least one of them is wrong,
and the gate's absence rows are all scanned against the 52-type file.

**Verdict: BROKEN.** Not "the absences are wrong" — it is that the completeness claim is refuted by
the project's own artefacts. The 53rd type is not identified here (that needs
`E:\Modding\_JC3grab\entities\*.ee.json`, outside this review's read-only scope); its members are
unscanned by every absence row.

---

## 11. "No sonar / tracker / allegiance carrier" is a statement about JC3

**Why the card rests on it.** WPN-7/8/9 are `absence` verdicts over `ENTITIES.md`'s 103-class
census, and the §12 row summarises them as *"no allegiance-switch, sonar or tracker class in the
103-class fleet census"*. The md adds "no such mechanism in the decoded fleet".

**Test.** The same words against the full archive index, which no absence row reads.

```
winch          0      tow            1471   cable          1      hook           2
grapple        620    tether         335    allegian       0      faction        14
sonar          1      tracker        6      tranquil       0      lethal         0
regen          0      recover        2      upright        4      air_control    0
```

The non-zero hits are real paths:

```
"path":"textures/ui/upgrades/upgrade_detector_sonar_capability.ddsc"
"path":"graphs/mission/mm130/mm130_tracker.gdc" / ".gsc"
"path":"graphs/spawner_group_tracker.gdc" / ".gsc"
"path":"settings/factions.bin"
"path":"graphs/mission/modules/msub_faction_switcher.gdc" / ".gsc"
```

`hijack` matches **288** paths (bark animations, dialogue). So the *narrow* claims hold — there is
no vehicle class named sonar/tracker/allegiance in the 103-class census, and the words are indeed
absent from `ENTITIES.md` — while the *mechanism-level* reading is false: JC3 ships a sonar
capability upgrade texture, a mission tracker graph, a faction table and a faction switcher.

**Verdict: WEAK.** The row text is correctly scoped ("in the 103-class fleet census") and the
summary line is not ("no such mechanism in the decoded fleet"). A reader who takes the summary as
the claim is misled; a reader who takes the per-row sentence is not. The fix is to print the
scope in the summary column, as `§4` of the file already does for native code.

---

## 12. A substring word scan is a proof of absence

**Why the card rests on it.** All 8 absences are `vocab-scan` rows: every named file must contain
one anchor, and none of the `must_not` words may appear in any of them (case-insensitive substring).

**Test.** Probe the same two files with synonyms and with words that contain the must_not tokens.

```
$ for w in regen regenerat heal restore stun sedat tase paralyz air_control upright righting; do ...
regen    0   heal  6   stun  26   righting  1   air_control 0   upright 0 (VOCAB)
$ grep -o -i "stun[a-z_]*" VOCABULARY.md | sort | uniq -c
      1 StuntAreas   20 stunt_areas   1 Stunt_BarrelRoll   1 Stunt_Loop   1 Stunt_UTurn    1 stunt_area_a_index ...
$ grep -o -i "heal[a-z_]*" VOCABULARY.md | sort | uniq -c
      6 health
$ grep -c -i "rope" INDEX.jsonl        # 83
```

Every `stun` hit is `stunt`, every `heal` hit is `health`, and all 83 `rope` index hits are
`propeller`. So the two-sided failure is concrete: a `must_not` of `stun` would make WPN-10
permanently red on the word `stunt`, while a real non-lethal member named `sedate`/`tase`/`dart`
would pass. The 8 rows themselves survive this probe — none is refuted by a synonym in
`VOCABULARY.md` or `ENTITIES.md` (the only near-miss, `righting_torque` at line 566, is n=23
`DriverLean`, exactly as HDL-6 says).

**Verdict: WEAK as a proof form, HOLDS for these 8 rows.** "Proven absence" here means "no word
from a short hand-written list is in two summary files", which is neither necessary nor sufficient
for absence of the mechanism.

---

## 13. DIM-2 — the evidence file carries the wheel radius

**Why the card rests on it.** Row: `DIM-2 | carrier | ... station quads agree with land_global wheel
data, so the wheel radius is a readable member — needle land_global`. §1 DIM-2's carrier column is
`land_global.*_wheels.radius`, wheel RBMs.

**Test.** Does `PHYSICS.md`, the named file, contain a radius or the member?

```
$ grep -n -i "radius\|wheel_radius\|land_global" Research/JC3Grab/PHYSICS.md
9:Cross-check against the named `land_global.base_wheel_hardpoint_positions`: **17 agree**, 0 disagree (145 entities have named stations).
```

No "radius" anywhere in the file. The needle lands on a hardpoint *cross-check* sentence. The member
does exist where the vocabulary puts it:

```
$ grep -n "front_wheels.radius" Research/JC3Grab/VOCABULARY.md
86:| `front_wheels.radius` | float | 0.1 .. 0.88 (med 0.25, n=41) |  |
855:| `front_wheels.radius` | float | 0.2 .. 1.8 (med 0.36, n=271) | 0.379999995 |
```

So DIM-2's *carrier* is real (`land_global.front_wheels.radius`, donor 0.38), but the gate points at
the one file in the repo that does not contain it — and the cross-check it does contain is a sample:
17 entities with structural station quads out of 145 with named stations, out of 232.

**Verdict: WEAK.** Right mechanism, wrong file, and the "agree" number is 17/145. (The donor is one
of the 17 — `PHYSICS.md:30` gives `v0300 ... 1.77 | 3.003 | 0.4` — so the donor-specific decision
survives; the fleet-wide phrasing does not.)

---

## 14. APP-1 — "56,136" is what the requirement is about

**Why the card rests on it.** `APP-1 | carrier | number | GEOMETRY.md | 56,136 meshes over 233
entities decode ... needle 56136`. §1 APP-1 is the Batmobile's appearance (all LODs, material
slots).

**Test.** The needle's line and the doc's header.

```
$ grep -n "56136" Research/JC3Grab/GEOMETRY.md
11:| meshes | 56136 |
$ sed -n '3p' Research/JC3Grab/GEOMETRY.md
Every mesh block in the 233 vehicle entities, decoded from the `.ee` bundles by
```

The number is a fleet decoder total, not the Batmobile's mesh count. The rework corrected the fact
cell to say so ("a fleet count, not the Batmobile body"), and the requirement — can JC3 meshes be
decoded and re-encoded at all — is exactly what a 56,136/56,136 decode proves.

**Verdict: HOLDS as stated.** The row is now honest about what it measures. It remains the weakest
kind of carrier for APP-1 (a decoder capacity, not the asset), which is a property of APP-1 the
backlog cannot avoid without the built asset.

---

## 15. One fleet denominator underlies the gate

**Why the card rests on it.** Rows and facts compare counts across files ("189 of 232", "3,217 over
223", "145/232", "233 entities", "224 vehicles"). If the denominators differ, the ratios are not
comparable and "fleet-wide" means five different things.

**Test.** The first fleet number each evidence file states.

```
GEOMETRY.md     233 vehicle entities          ENTITIES.md     232 decoded .epe graphs
VOCABULARY.md   232 decoded .ee entities      TETHER.md       232 entity caches / 232 .epe graphs
LIGHT_SYSTEM.md 232 caches; 223 vehicles with VehicleDynamicLights; 3,217 entries
USAGES.md       232 caches; 224 vehicles with EffectAttachments; 232 ExtendedEffectUsages modules
INDEX.jsonl     314 vehicle .ee paths; 232 .epe paths
```

**Verdict: WEAK.** The gate never quotes a single "fleet" number, and each file is internally
consistent, so no row is arithmetically wrong. But "over 233 entities", "232 entities", "223
vehicles", "224 vehicles" and "232 graphs" are used as if interchangeable, and the 233↔232 gap is
the same gap as §9.

---

## 16. Mass 975 / 6,000 / 6.154 is usable

**Why the card rests on it.** DIM-3 and WLD-5 both rest on the donor's mass and a 6 t class target;
WLD-7's airlift/tether conclusion rests on the 6.154× ratio.

**Test.** The mass block of `TETHER.json` and the arithmetic.

```
$ python  # TETHER.json, mass
{'batmobile_target': 6000,
 'donor': {'entity': 'v0300_car_kensington_sportsmuscle_civilian_01', 'mass': 975},
 'entities_with_mass': 232, 'single_body_entities': 231,
 'multi_body_entities': {'v4603_plane_urga_cargotransport_military_cargo_tank': [40000, 25000]},
 'ratio_to_donor': 6.154, 'unit': 'UNKNOWN'}
```

6000 / 975 = 6.1538…, printed 6.154. All 232 entities carry a mass (231 single-body + 1 two-body),
so this is a true fleet census; the unit is declared UNKNOWN and the comparison is a ratio, which is
unit-free. The magnitudes (975 for a sports car, 40,000 for a cargo plane) are consistent with kg,
which makes the UNKNOWN *conservative*, not wrong.

**Verdict: HOLDS.** The one unit claim is correctly withheld, and the ratio does not depend on it.
(If a later row ever treats 975 as a mass in kg, the "unit UNKNOWN" label must move with it.)

---

## 17. The turret's ±179° is decoded, not a unit guess

**Why the card rests on it.** APP-6 and ANI-2 both carry `179` as a hinge limit, and the turret
carrier is "part angles".

**Test.** All hinge rows in the artefact, the conversion, and the physical ceiling.

```
$ python  # TURRET.json
hinge rows: 194
min rad -3.124139 max rad 3.124139
|rad| > 2*pi: 0
rows where deg != rad*57.29578: 0
rows with |deg| > 360: 0
  None -0.087266 0.349066 -5.0 20.0
  None 0.0 2.268928 0.0 130.0
  None -3.124139 3.124139 -179.0 179.0
```

`jc3turret.py:123-125` converts the two floats at `+0xFC`/`+0x100` with 57.29577951308232. All 194
rows are inside ±π and every `min_deg`/`max_deg` is exactly the converted value, 194/194. A degrees
encoding would put a door limit at ~130 and a turret at ±179, which after this conversion would read
7,449° and 10,257° — nothing in the file exceeds 360°.

**Verdict: HOLDS.** The radian convention is asserted at the byte level (not re-derived here), but
the artefact is internally exact across 194 hinges and the physical ceiling is consistent. No
off-by-180, no sign flip.

---

## 18. ANI-9 — the seat is 10 mm under the hip

**Why the card rests on it.** `ANI-9 | carrier | number | SEAT.md | seat part candidate 0.855 m, 10
mm under the BmAK Driver hip; pose via rico_base — needle 0.855`.

**Test.** Both numbers and what each one measures.

```
$ grep -n "0.855" Research/JC3Grab/SEAT.md
12:| how high each sits | `Land_Seat` part hull centres v0300 0.855 m, v0300 0.855 m, v0003 0.894 m ... | `.physicsc` hulls |
14:| candidate for the Batmobile | **... `sportsmuscle_f_l_seat`** at 0.855 m vs the `Driver` hip 0.865 m (10 mm) | ... |
$ grep -n "0.8647" Research/BatmobileGrab/COCKPIT.md
41:| `position_m` (JC3, through the one transform) | **(-0.0025, 0.8647, -1.0654)** ...
```

0.8647 − 0.855 = 0.0097, so "10 mm" is arithmetic on the two printed numbers. But 0.855 is a
**hull centre** of a `Land_Seat` part, not a sitting surface, and `SEAT.md`'s own headline is
*"the car does not own the pose"*: placement is `entry.driver` + `rico_base.afsmb`/`.asb` by vehicle
class. The row's fact says "candidate ... pose via rico_base", so it does not claim the part places
Rico — but the `carrier` verdict still rests on a name (`Land_Seat`) whose behaviour as a seat is not
established.

**Verdict: WEAK.** Correct arithmetic, inferred semantics: the 10 mm is centre-to-hip, and the
coordinate frame is consistent (both values are JC3 metres through the one transform, per
`SOCKETS_JC3.json`'s `convention`: cm → m, `bat_assemble.to_jc3_rot(p) * 0.01 + offset`).

---

## 19. The reader set is complete and every reader is independent evidence

**Why the card rests on it.** Clause 1 of the gate is "every new reader has `--check` green", and
the summary counts 25/25.

**Test.** Extract every G2 card's `Out:` scripts, compare with `READERS + CENSUS`, then inspect what
`--check` actually does in a sample.

```
$ python  # card Out: scripts vs gate list
G2-10 out=jc3weapons.py ... gate=OK      G2-22 out=jc3usage.py ... gate=OK
G2-28 out=damage_predict.py gate=OK      G2-30 out=jc3hkx.py ... gate=OK
(all 25 cards OK; 24 reader scripts + 1 census = 25 subprocesses; G2-22/23 share jc3usage.py)
```

```
$ grep -n "a.check\|json.load" Tools/scripts/jc3water.py
724:        if json.load(f) != d:
725:            bad.append(f"{JSON_NAME} stale")
761:def main() -> int:
772:    if a.check:
```

`jc3water.py --check` decodes the live build's water modules and compares them with the donor cache
before comparing its own JSON (`d` is the fresh derivation, not the file); `jc3traffic.py` and
`jc3strings.py` re-derive from `INDEX.jsonl` and the localisation blobs and then compare. So the
readers are not tautologies. Two caveats: the gate accepts *any* exit-0 run whose first verdict-like
line starts with PASS/OK, so a reader could print a caveat after its PASS; and the list itself is
typed — `G2X.md`'s reader table shows two rows labelled `G2-29` (`traffic`, `physics write`) and
none labelled `G2-30`, while the card that owns `jc3hkx.py` is G2-30.

**Verdict: HOLDS with caveat.** All card-named readers are run, and the sampled ones re-derive.
The label drift and the status-token rule are the soft spots, not the coverage.

---

## 20. Zero decisions open

**Why the card rests on it.** Seven rows carry a §11 decision and the md prints "decisions still
open | 0 (none)". If a decision were open, seven rows would be `blocked`.

**Test.** Parse the register the way the gate does, and read every row.

```
$ sed -n '/^## 11\./,/^---$/p' GRAB_BACKLOG.md | grep -c '^| D-'
10
$ ... every D- row contains "resolved 2026-10-28 (user)" / "resolved 2026-10-24:"
$ grep -c "not resolved\|unresolved" GRAB_BACKLOG.md
0
```

D-1 (tyres, 10-24), D-2 (one hybrid car), D-3 (accept lethality), D-4 (keep v0300), D-5 (skins),
D-6 (standalone), D-7 (all weapons), D-8 (lore water), D-9 (no enemy ejection), D-10 (no gear mods)
— all dated and attributed. The parser's rule (`"resolved" in cells[3].lower()`) would mis-read a
row that said "not resolved", but no such row exists.

**Verdict: HOLDS.** 0 open is true of the file, not just of the parser.

---

## 21. Fact cells that describe the build are true (ARM-2)

**Why the card rests on it.** `ARM-2`'s fact says *"the build already carries the tank's 2000 HP"*.
The gate never checks fact text — it is a string in the script — so any fact can drift while the
needle stays green.

**Test.** Search the build's own health module for the value, in both encodings.

```
$ python  # Builds/test-091/.../lave_health_medium.vmodc, 3,741 B
2000.0 float32 hits 0 int32 hits 1
700.0  float32 hits 0 int32 hits 1
1200.0 float32 hits 0 int32 hits 0
36000.0 float32 hits 0 int32 hits 0
```

The health module carries 2000 (and 700), and does **not** carry the BmAK `RVehicleBatmobile.Health`
1,200, so the claim is true as of test-091.

**Verdict: HOLDS** for this fact, and it shows the general risk: fact cells are prose in the
generator and are never re-derived, so they age silently — exactly what the 2026-10-29 rework
caught in `APP-1`.

---

## Method and limits

* Read-only: only `--check`/`--write`-free paths were run. `find Research/JC3Grab -newermt
  '-40 minutes'` returned nothing after the full gate run, and `G2X.md`/`G2X.json` still show their
  `00:27` mtime. `git status` already listed 187 modified paths before this review (the repo's
  pre-existing state); this review added only `Research/challenge/card-G2X.md`.
* The raw decoded corpus `E:\Modding\_JC3grab\` (and the game archives) were **not** read for this
  review; every test above uses in-repo artefacts, which is also the gate's own evidence base. That
  is why §10 cannot name the missing 53rd module type and §9 cannot name the 233rd entity.
* No game was launched, nothing was written into `D:\Games`, no save, build or shared module was
  touched, nothing was committed.
