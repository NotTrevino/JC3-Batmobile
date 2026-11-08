# Assumption challenge — G2-14 · Moving-part behaviours: who drives each variable

**Scope.** Finished card `GRAB_BACKLOG.md:632-643` (S, deps P0-2), its §12 row (`:1297`),
MODLOG §"G2-14 · Moving-part behaviours: who drives each variable — done" (`:9727`, plus the
2026-10-29 rework at `:14639`/`:14722`) and the outputs it names: `Research/JC3Grab/MOVING_PARTS.md`
(209 lines), `MOVING_PARTS.json`, `Tools/scripts/jc3moving.py`. Rules read first:
`GRAB_BACKLOG.md` §0.5 R1–R14.

**Method.** Re-ran the card's check, then attacked each claim with the data on disk: the cached
`vehicle_common.vmodc` (`E:\Modding\_JC3grab\tmp\vehicle_common.vmodc`), `FEATURE_CENSUS.json`,
`PARTS_TABLE.jsonl`, the 78 cached parts modules, `DOORS.md`, and — read-only — all 314 vehicle
`.ee` containers at `D:\Games\Just Cause 3` (the generator itself reads them; nothing was written
there, no game launched, nothing committed). Every number below is copied from a command output.

**Change record (AGENTS.md).** One file written: this one, `Research/challenge/card-G2-14.md` —
the path the task names, beside the existing `Research/challenge/card-G1-*.md` and
`card-G2-*.md`. Revert: delete it.

**The card's own check, re-run:**

```
$ python Tools/scripts/jc3moving.py --check
PASS: 67 behaviours, 53 table rows (37 proven on CCar), 224 door rows
EXIT=0
```

The generator is intact and reproducible. Everything below is about what its numbers are taken to
mean, and what it never looked at.

---

## VERDICT

| # | assumption | verdict |
|---|---|---|
| A1 | `vehicle_common` holds **five** behaviour tables; 38 behaviours have a row, 29 do not | **BROKEN** |
| A2 | the module is "the only copy in the fleet"; nothing to diff it against | **BROKEN** |
| A3 | 67 behaviours "in use across 233 vehicles" | **BROKEN** (fleet is 314 containers / 70 behaviours) |
| A4 | 37 proven on `CCar`, 30 not | **BROKEN** — a DLC `CCar` ships `RadarFast` |
| A5 | "`AirBrake` is 3 parts" — the `parts` column counts parts | **WEAK** (it counts entity variants: 3 → 1 distinct part) |
| A6 | arrays: `door_parts` 224/56, `hinged_parts` 148/28, `rotating_parts` 47/22 "of 78" | **WEAK** (fleet: 229/60, 162/30, 74/28 of 86) |
| A7 | "the animation system writes it", variable read as "a 0..1 position" | **WEAK** — inference stated as decoded |
| A8 | "232 entities have a detail JSON"; class map resolves 231 of 233 | **WEAK** (the 233rd record is never named) |
| A9 | `proven-on-CCar` means a car can copy the behaviour | **WEAK** — it means "a part with that string exists" |
| A10 | every unproven user is "an aircraft, boat, helicopter, bike or train" | **WEAK** — no bike |
| A11 | doors/fin/spring rows are name-only; a door's travel is its Havok hinge | **HOLDS** |
| A12 | hinged = `target_position_variable` + `lod` + flag; rotating = `rpm_variable` + flags | **HOLDS** |
| A13 | `SteeringFork` is the only row with `use_target_position_as_angle` = 1 | **HOLDS** |
| A14 | 11 of 25 hinged used, 15 declared-unused (12 spider legs + 2 elevons + `BoatRudder`) | **HOLDS** in the doc, **BROKEN** in §12 |
| A15 | `AirBrake` 3 parts on 1 `CAirPlane` chassis, nothing on land — Q-1 probe stands | **HOLDS** (across all 314) |
| A16 | the six turreted samples fill `door_parts[]` (5/1/1/4/5/1) and not `hinged`/`rotating` | **HOLDS** |
| A17 | `rotoscope_rpm_per_cycle` "20 rpm/cycle" on every row | **BROKEN** in §12 / old MODLOG; doc correct (7×20, 5×50) |
| A18 | `--check` validates the tables against the game | **WEAK** — it re-reads a cache, and one invariant asserts the claim A1 breaks |

**One-line summary.** The decode of `vehicle_common` is precise — every row, member, flag and
table size reproduces exactly, and the two "name-only" families really are empty. But the census
around it is bounded by what the card happened to read: it decoded 5 of the **7**
`all_*_part_properties` tables in the same file (so `Wheel`, `BrakeCalipers`, `BrakeDisc`,
`BrakeDrum` *do* have rows, and the "29 without a row" is 25), it counted 67 behaviours over the
232 base-game entities while the index holds **314** vehicle containers (3 more behaviours exist on
the DLC drones), it marked `RadarFast` unproven on a car although the DLC mech — a `CCar` — ships
it, and it calls the module "the only copy in the fleet" when **233** containers carry a
byte-identical copy.

---

## A1 · "five behaviour tables … 38 have a row, 29 do not" — **BROKEN**

**Claim.**

```
MOVING_PARTS.md:4-6   "…which holds five behaviour tables: all_hinged_,
                       all_rotating_, all_door_, all_fin_ and all_spring_part_properties."
MOVING_PARTS.md:162   "**67 behaviours** in use, **38** of them with a `vehicle_common` row.
                       The **29** without one group like this…"
MODLOG:9750           "38 of them have a `vehicle_common` row, 29 do not (turret/cannon,
                       wheel, body, brakes, engine, windows, couplings)."
```

**Assumption.** The behaviour-carrying tables are exactly the five named in the generator's
`TABLES` tuple; any behaviour not in them has no row.

**Test.** Walk the whole module and list every top-level member, then every
`all_*_part_properties` table with its rows and members:

```
$ python - <<'EOF'   # walk E:/Modding/_JC3grab/tmp/vehicle_common.vmodc
top-level members: ['all_door_part_properties', 'all_fin_part_properties',
 'all_hinged_part_properties', 'all_propeller_part_properties',
 'all_rotating_part_properties', 'all_spring_part_properties',
 'all_vehicles_common', 'all_wheel_part_properties', 'boat_common', 'car_common',
 'helicopter_common', 'motorbike_common', 'plane_common', 'rotor_collision',
 'tire_effects', 'train_common', 'vehicle_damage']
rows: 473  bytes: 12271

all_fin_part_properties           1 rows  members=['name.hash','name.string']
all_spring_part_properties        1 rows  members=['name.hash','name.string']
all_door_part_properties         14 rows  members=['name.hash','name.string']
all_hinged_part_properties       25 rows  members=['lod','name.hash','name.string',
                                                 'target_position_variable.hash',
                                                 'target_position_variable.string',
                                                 'use_target_position_as_angle']
all_rotating_part_properties     12 rows  members=['inverted','name.hash','name.string',
                                                 'number_of_water_collision_sensors',
                                                 'rotoscope_enabled','rotoscope_rpm_per_cycle',
                                                 'rpm_variable.hash','rpm_variable.string',
                                                 'special_collision_enabled']
all_propeller_part_properties     1 rows  members=['name.hash','name.string']
all_wheel_part_properties         4 rows  members=['name.hash','name.string']

all_wheel_part_properties rows: Wheel, BrakeCalipers, BrakeDisc, BrakeDrum
all_propeller_part_properties rows: Propeller
```

There are **seven** `all_*_part_properties` tables, not five. Intersecting those names with the
card's own 67:

```
behaviours covered by any of the 7 tables: 42
not covered: 25
card says 'no row': 29
of those, actually in a table: ['Wheel', 'BrakeCalipers', 'BrakeDisc', 'BrakeDrum']
   table: {'Wheel': 'all_wheel_part_properties', 'BrakeCalipers': 'all_wheel_part_properties',
           'BrakeDisc': 'all_wheel_part_properties', 'BrakeDrum': 'all_wheel_part_properties'}
```

**Result.** Four of the 29 "no row" behaviours have a row — in `all_wheel_part_properties`, a table
in the same 12,271-byte file. The corrected split is **42 with a row, 25 without**. The doc's
grouping sentence ("the deform and wheel system: `Wheel`, `Body`, `BrakeDrum`, `BrakeDisc`,
`Engine`") is 4-of-5 wrong, and the §2 table prints "no vehicle_common row" in the channel column
for `Wheel` (710 parts), `BrakeCalipers` (330), `BrakeDisc` (192) and `BrakeDrum` (78) — the four
largest behaviours it says have no home other than `Wheel=`… which it also lists as no-row.

The card's own census input already said 7. `FEATURE_CENSUS.json -> totals` carries
`"behaviour_tables": 7` and `behaviour_variables` lists all seven tables (including
`all_wheel_part_properties rows=4 names=['Wheel','BrakeCalipers','BrakeDisc','BrakeDrum']`), so the
information was in the file the generator reads.

> **Verdict: BROKEN.** The count "29 without a row" is a search of five table names, not of the
> carrier.

---

## A2 · "the only copy in the fleet … nothing to diff it against" — **BROKEN**

**Claim.**

```
MOVING_PARTS.md:18   "Source: `vehicle_common.vmodc`, the only copy in the fleet, carried as an
                      inner file of the Serpente civilian `.ee`."
jc3moving.py:16-17   "the `vehicle_common.vmodc` module inside the Serpente civilian `.ee`
                      (the only copy in the fleet)"
MOVING_PARTS.md:198  "The `vehicle_common` copy is read from one entity's container…; no second
                      copy exists in the index to diff against."
```

**Assumption.** Because the VFS index has no row for the inner file, only one copy exists, so the
table cannot be cross-checked.

**Test 1 — provenance of the copy that was read.** Re-read the sportsmuscle (Serpente) container
and compare bytes with the cache the generator uses:

```
container: editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/
           v0300_car_kensington_sportsmuscle_civilian_01.ee
inner: editor/entities/jc_vehicles/00_shared/modules/vehicle_common.vmodc offset 12214868 size 12271
serpente/sportsmuscle copy bytes: 12271  cached: 12271  identical: True
```

So the card's byte-for-byte provenance claim ("12,271 B, member at 12,214,868 in that container",
MODLOG:9730) is exact — for that one copy.

**Test 2 — count the copies.** Walk every vehicle container's inner files and hash each
`vehicle_common.vmodc`:

```
$ python - <<'EOF'   # all editor/entities/jc_vehicles/**/*.ee in INDEX.jsonl
vehicle .ee rows in index: 233
containers read: 233 | errors: 0
distinct vehicle_common.vmodc hashes: 1
  b402542d7641d6b7  x233  e.g. .../v0000_car_autostraad_oldjeep_civilian_01.ee
containers WITHOUT vehicle_common: 0
```

**Result.** Every one of the 233 base+patch vehicle containers embeds the module, and all 233
copies hash to one value — including the copy the generator read. The "only copy" sentence is
false, and the "nothing to diff against" limit is false in the direction that matters: the diff is
possible, and it *confirms* the table fleet-wide instead of leaving it as one entity's word. (The
81 DLC vehicle containers were not in this 233-row set; the ship is already contradicted by the
base game alone.)

> **Verdict: BROKEN.** A 233-way diff exists and agrees; the doc's weakest bullet is the one claim
> that could have been strengthened.

---

## A3 · "67 behaviours in use across 233 vehicles" — **BROKEN** for the fleet

**Claim.**

```
MOVING_PARTS.md:162   "**67 behaviours** in use"
MODLOG:9749           "67 behaviours in use across 233 vehicles"
GRAB_BACKLOG.md:1297  "67 behaviours over 233 vehicles"
```

**Assumption.** The 232 detail JSONs / 233 `PARTS_TABLE` records are the fleet.

**Test 1 — what the index holds.**

```
jc_vehicles .ee: 314  mounts: Counter({'base': 232, 'dlc': 81, 'patch': 1})
```

`PARTS_TABLE.jsonl` has 233 records (232 distinct entities + one duplicate line) and covers
base+patch; the **81 DLC vehicle containers are not in it**. Every fleet-worded number in the doc
therefore stops at 74 % of the containers.

**Test 2 — decode the DLC parts modules and compare the behaviour vocabulary.** For all 314
containers, extract each `*_parts.vmodc`, walk its ADF, collect `parts[i].behavior.string`:

```
containers: 314 | distinct modules: 86
distinct behaviours in parts modules: 70
behaviours NOT in the card's 67: 3
    MoodAttack -> ['elitedrone_vehicle_parts.vmodc', 'gruntdrone_vehicle_parts.vmodc']
    MoodIdle   -> ['elitedrone_vehicle_parts.vmodc', 'gruntdrone_vehicle_parts.vmodc']
    MoodSearch -> ['elitedrone_vehicle_parts.vmodc', 'gruntdrone_vehicle_parts.vmodc']
```

**Result.** The fleet vocabulary is **70** behaviours over **314** containers. Three behaviours
(`MoodAttack`, `MoodIdle`, `MoodSearch`, on the Eden drone parts modules) appear nowhere in the doc.
They have no `vehicle_common` row either, so they belong in the "no row" group — which is a second
reason the 29 is a base-game figure.

> **Verdict: BROKEN** as a fleet claim; the 67 is right for the 232 censused entities.

---

## A4 · "37 proven on `CCar`, 30 not" — **BROKEN**

**Claim.**

```
MOVING_PARTS.md:88    "`proven-on-CCar` means at least one `CCar` chassis ships a part with that
                       behaviour."
MOVING_PARTS.md:142   "| `RadarFast` | rotating, `radar_fast_rpm` | 3 | 3 | 1 | `CBoat` | unproven-on-CCar |"
MOVING_PARTS.md:168   "Those are the behaviours a B-05 port cannot copy from another `CCar`: every
                       user is an aircraft, boat, helicopter, bike or train."
```

**Assumption.** The classes come from `each entity's .epe class histogram` over the 232 base
entities, and no `CCar` outside that set carries an "unproven" behaviour.

**Test.** For all 82 non-base vehicle containers: locate the `.epe` inner file, count the raw
`CCar`/`CBoat`/… class strings (on the base containers this raw count reproduces the decoded
histogram exactly — APC `CCar`×1, plane `CAirPlane`×1), decode each parts module's behaviours, and
intersect with the doc's unproven 30:

```
non-base containers: 82
unproven behaviours carried by a non-base container:
  RadarFast          chassis=['v0805_car_na_mech', 'v1202_boat_capstone_corvette',
                              'v1706_boat_na_rocketboat']  classes=['CBoat','CCar']
  … (23 more, all aircraft/boat/helicopter)
```

and the mech itself:

```
v0805_car_na_mech .epe: CCar occurrences = 1 | CBoat = 0 | CAirPlane = 0
mech_vehicle_parts.vmodc -> behaviours: ['BavariumShield','Body','FrontLeftDoor',
                                        'RadarFast','Turret','Wheel']
RadarFast part: parts[36] 'mech_light_beacon'
```

15 DLC containers declare `CCar` (`dlc/…/v0800 series`, the mech `v0805_car_na_mech`, blackhand
jeeps/tanks, …). The class census seen from the raw `.epe` strings:

```
base  ('CCar',): 125   base ('CBoat',): 35   base ('CHelicopter',): 23   base ('CMotorBike',): 19
base  ('CAirPlane',): 17  base ('CTrain',): 12  base ('CCar','CAirPlane'): 1
dlc   ('CCar',): 15    dlc ('CBoat',): 16   dlc ('CHelicopter',): 6   dlc ('CAirPlane',): 4
dlc   ('CMotorBike',): 1   dlc (): 39   patch ('CHelicopter',): 1
```

**Result.** `RadarFast` is shipped by a **`CCar`** (the DLC mech, on a part named
`mech_light_beacon`). By the doc's own definition it is `proven-on-CCar`; the fleet split is
**38 proven / 29 not** among the 67 (and the 3 DLC drone behaviours carry no class among the six at
all, because 39 DLC containers — the drones — declare none of `CCar`/`CAirPlane`/…).

`AirBrake`'s class is unaffected: no non-plane module anywhere carries it (A15). But the
sentence "every user is an aircraft, boat, helicopter, bike or train" is now wrong twice: a car
uses `RadarFast`, and the unproven classes contain no `CMotorBike` at all —

```
unproven classes: Counter({'CAirPlane': 18, 'CHelicopter': 7, 'CBoat': 7, 'CTrain': 5})
```

> **Verdict: BROKEN.** One of the 30 flips when the 81 DLC containers are read.

---

## A5 · the `parts` column counts parts — **WEAK**

**Claim.**

```
MOVING_PARTS.md:142   "| `AirBrake` | hinged, `air_brakes_T` | 3 | 3 | 1 | `CAirPlane` | …"
MOVING_PARTS.md:169   "`AirBrake` … 3 parts on 1 chassis (v4602_plane_urga_fighterbomber; CAirPlane)"
```

**Assumption.** "3 parts" is three air-brake parts.

**Test.** Distinct `(module, part name)` per behaviour, from `PARTS_TABLE.jsonl`:

```
behaviour                  parts  distinct-part-names
AirBrake                       3     1
Flaps                        202    48
FrontLeftDoor                173    56
Hood                          78    27
SteeringFork                  27    11
Wheel                        710   234
MainRotor                     24     7
```

and the AirBrake rows:

```
v4602_plane_urga_fighterbomber_debug.ee        fighterbomber_vehicle_parts.vmodc  [(12,'fighterbomber_airbrake')]
v4602_plane_urga_fighterbomber_military_01.ee  fighterbomber_vehicle_parts.vmodc  [(12,'fighterbomber_airbrake')]
v4602_plane_urga_fighterbomber_rebel_01.ee     fighterbomber_vehicle_parts.vmodc  [(12,'fighterbomber_airbrake')]
```

**Result.** `parts` is a sum over entity variants: three `.ee` files of one aircraft, one part
index each. The Q-1 probe is therefore **one** `fighterbomber_airbrake` part, not three; and every
"parts" figure in the table is inflated by the variant multiplier (Flaps ×4.2, Wheel ×3.0). The
column is honest as a workload figure and misleading as a fleet width — "3 parts on 1 chassis"
reads as three independent samples when it is one sample copied to three files.

> **Verdict: WEAK** — a silent unit (entity-variant occurrences), not an error in the decode.

---

## A6 · the per-part arrays, "of 78" — **WEAK**

**Claim.**

```
MOVING_PARTS.md:177-181
| array | modules with rows (of 78) | rows |
| door_parts[]     | 56 | 224 |
| hinged_parts[]   | 28 | 148 |
| rotating_parts[] | 22 |  47 |
MODLOG:9774  "The array census covers the 78 cached modules, not all 233."
```

**Test.** Decode those three arrays in every `*_parts.vmodc` of all 314 containers, dedupe by module
name, and compare with the cache:

```
modules: 86
per-module totals over all 86 fleet modules: {'door_parts': 229, 'hinged_parts': 162, 'rotating_parts': 74}
modules with rows: {'door_parts': 60, 'hinged_parts': 30, 'rotating_parts': 28}
cached modules: 78
fleet modules not cached: ['elitedrone_vehicle_parts.vmodc', 'gruntdrone_vehicle_parts.vmodc',
 'mech_vehicle_parts.vmodc', 'monorailflatbed_vehicle_parts.vmodc',
 'rocketboat_vehicle_parts.vmodc', 'shielddrone_vehicle_parts.vmodc',
 'sportmech_vehicle_parts.vmodc', 'transportdrone_vehicle_parts.vmodc']
   elitedrone   door 0 hinged 0 rotating 5
   gruntdrone   door 0 hinged 0 rotating 5
   mech         door 2 hinged 0 rotating 1
   monorailflatbed door 0 hinged 0 rotating 0
   rocketboat   door 1 hinged 2 rotating 4
   shielddrone  door 0 hinged 0 rotating 8
   sportmech    door 1 hinged 0 rotating 0
   transportdrone door 1 hinged 12 rotating 4
```

(The four extra rows are `mech` 2, `rocketboat` 1, `sportmech` 1, `transportdrone` 1 = 5; the 14
hinged are `rocketboat` 2 + `transportdrone` 12; the 27 rotating are 5+5+1+4+8+4.)

**Result.** The doc does flag the 78-module limit, so this is disclosed — but the table header says
"of 78" as if the denominator were the fleet, and the §12 row quotes 224/56 as *the* array census.
The fleet numbers are **229/60, 162/30, 74/28** over 86 modules. One module the card *does* name
(`monorailflatbed`, referenced by `v5602_train_urga_monorailflatbed` ×4 in `PARTS_TABLE.jsonl`) is
missing from the cache — and it turns out to have **0** rows in all three arrays, so the totals are
short only by the DLC modules.

> **Verdict: WEAK** — right for the cache, wrong as a fleet figure, and the cache is one module
> short of the base game too.

---

## A7 · "the animation system writes it", "a 0..1 position" — **WEAK**

**Claim.**

```
MOVING_PARTS.md:51-52  "The variable is a float in the vehicle's own state: the animation system
                        writes it, the behaviour reads it. `SteeringFork` is the only row that sets
                        `use_target_position_as_angle`; every other row takes the variable as a
                        0..1 position."
MOVING_PARTS.md:208    "Which *code* writes a given variable (`steering_roll`, `hood_angle`) is not
                        in any file read here - the table proves the binding, not the writer."
```

**Assumption.** The variable is a float state channel, the writer is the animation system, and
flag-0 variables are normalised positions.

**Test.** The decode gives names, not types — the table stores `target_position_variable.string`
and `.hash`, nothing else:

```
all_hinged_part_properties members: ['lod','name.hash','name.string',
  'target_position_variable.hash','target_position_variable.string','use_target_position_as_angle']
```

Search the animation state-machine and skeleton files shipped beside the vehicle for those names:

```
$ python - <<'EOF'   # v0201 medium tank: .bsk / vehicle_null.asb / vehicle_null.afsmb
animations/jc_skeletons/vehicles/v0201_car_capstone_mediumtank.bsk 1200 {}
animations/jc_statemachine/vehicles/vehicle_null.asb 420 {}
animations/jc_statemachine/vehicles/vehicle_null.afsmb 227 {}
```

No occurrence of `steering_roll`, `steering_pitch`, `steering_yaw`, `air_brakes_T`, `hood_angle`,
`main_rotor_rpm`, `flaps_T`, `landing_gears_T` or `steering_turn` in any of them. Grepping the
research tree for a definition of the flag or the range returns only the doc's own sentence:

```
$ grep -rn "0\.\.1\b|0 to 1|0-1 position" Research/JC3Grab/*.md
MOVING_PARTS.md:52: … every other row takes the variable as a 0..1 position.
```

**Result.** Both halves are inference. The flags are decoded (`use_target_position_as_angle`
24×0 / 1×1; `lod` 22×1 / 3×0), the *meaning* of the flag and the *range* of the variable are not.
The doc marks its other inferences (rotoscope: "the name suggests … UNKNOWN") but presents this
one as fact — and then §4 contradicts it ("the table proves the binding, not the writer"). A port
that assumes 0..1 has no decoded basis.

> **Verdict: WEAK.** The decode is right; the two sentences around it should read UNKNOWN.

---

## A8 · "232 entities have a detail JSON"; 231 of 233 — **WEAK**

**Claim.**

```
MOVING_PARTS.md:204  "The class map resolves 231 of the 233 records: 232 entities have a detail
                      JSON and one of them (v4603_plane_urga_cargotransport_military_cargo_tank.ee)
                      declares both CCar and CAirPlane, so it is dropped"
```

**Test.**

```
PARTS_TABLE records: 233  distinct entities: 233  detail JSONs: 232
records without a detail JSON: ['editor/entities/jc_vehicles/02_air/v2602_helicopter_urga_lightassault/
                                 v2602_helicopter_urga_lightassault_military_01_custom_mm230.ee']
detail JSONs without a record: []
```

and the method that picks the class:

```
jc3moving.py:127-136  "entity -> root class, from the decoded .epe class histogram
                       (exactly one root per file)"  ->  found = [c for c in ROOT_CLASSES
                       if classes.get(c) == 1]
```

**Result.** The arithmetic is right: 233 records, 232 with a graph, of which one is dropped for a
dual root → 231. But the sentence accounts for only one of the two exclusions: the record with **no
detail JSON** is never named, so a reader recomputing 233 − 1 gets 232. The class *method* is also
a count rather than a root read (`classes.get(c) == 1`), which is a name/count shortcut — but it
was checked here against the decoded object tree and agrees 231/231:

```
count of depth-1 objects with a ROOT class, per file: {1: 231, 2: 1}
```

so the result is sound even though the rule is not the one the docstring describes ("the chassis'
root class").

> **Verdict: WEAK** — right numbers, one unexplained exclusion, a class rule that coincides with
> the decoded root everywhere but is not derived from it.

---

## A9 · "proven-on-CCar" as evidence for a port — **WEAK**

**Claim.**

```
MOVING_PARTS.md:87-89  "`proven-on-CCar` means at least one `CCar` chassis ships a part with that
                        behaviour."
MODLOG:9749-9750       "37 are proven on a CCar; 30 are not - aircraft, boat, helicopter, bike and
                        train parts"
```

**Assumption.** "A part carries this behaviour string on a car chassis" can be read as "this
behaviour is known to work on a car".

**Test.** The proof is computed from the same census row that defines it:

```
jc3moving.py:220-226  ch_classes = sorted({c for ch in b["chassis_list"] for c in chassis_class.get(ch, [])})
                      "proof": "proven-on-CCar" if "CCar" in ch_classes else "unproven-on-CCar"
jc3moving.py:512-513  if (b["proof"] == "proven-on-CCar") != ("CCar" in b["classes"]): bad.append(...)
```

and the members that would say *how* it moves are absent for 42 of the 67 behaviours (A1): the
only rows that name anything are hinged/rotating, and those name a variable, not a rate, limit or
direction (A12).

**Result.** The invariant is a tautology — it compares the proof column with the expression that
produced it, so it can never fail. The column is a *presence* fact ("a car chassis ships a part
whose behaviour string is `Flaps`"), not a behaviour fact: nothing decoded says the car animates
it. That distinction matters where the doc uses it, e.g. `Flaps` (202 parts / 8 chassis, incl.
`CCar`) is offered as a car-copyable behaviour on the strength of a string match. The doc defines
the term, so this is a rigour problem, not a falsehood.

> **Verdict: WEAK** — the definition is stated, the inference drawn from it is not.

---

## A10 · "every user is an aircraft, boat, helicopter, bike or train" — **WEAK**

Covered with A4's evidence:

```
unproven classes: Counter({'CAirPlane': 18, 'CHelicopter': 7, 'CBoat': 7, 'CTrain': 5})
```

No unproven behaviour has a `CMotorBike` user. Bike parts that *are* in the census
(`SteeringFork` 27, `Hood` 78, `Spring` 61, `BrakeDrum` 78) are all proven, so "bike" in that
sentence is a list item with no instance behind it.

> **Verdict: WEAK** — a fleet-wide enumeration with one unsupported member.

---

## A11 · doors/fin/spring are name-only; door travel is the hinge — **HOLDS**

**Claim.**

```
MOVING_PARTS.md:105-110  "These rows carry nothing but the name and its hash. A door's angle is
                          the part's Havok hinge (G2-13: mediumtank_hatch is a FrontLeftDoor on a
                          0..130 deg limited hinge)…"
```

**Test.** Member lists of the three tables (A1 output) are exactly `['name.hash','name.string']` —
no angle, no speed, no variable. And the G2-13/G2-15 sample to which the claim defers:

```
$ grep -n "mediumtank|deg" Research/JC3Grab/DOORS.md
37:| v0201 medium tank | `mediumtank_hatch` | FrontLeftDoor | (1, 0, 0) | 0 .. 130 deg | …
13:| v0300 Serpente (civilian) | `sportsmuscle_door_f_l` | FrontLeftDoor | (0,-1,0) | 0 .. 80 deg | …
16:| v0200 APC (military)    | `apc_door_c_l`        | CenterLeftDoor  | (0,-1,0) | 0 .. 100 deg | …
21:| v5603 monorail missile car | `…hatch_l_01`      | MissileHatch    | (0,0,-1) | 0 .. 150 deg | …
```

**Result.** The rows are empty, and the hinge really does carry the travel — with limits that vary
per door (70/80/95/100/130/150°), all `0 .. N`. The one sample named in the sentence
(`mediumtank_hatch`, 0..130) is verified in `DOORS.md:37`.

> **Verdict: HOLDS.**

---

## A12 · hinged/rotating member layouts — **HOLDS**

**Claim.** `MOVING_PARTS.md` §1 tables: hinged = `target_position_variable` + `lod` +
`use_target_position_as_angle`; rotating = `rpm_variable` + `rotoscope_enabled` + `inverted` +
`special_collision_enabled` + `number_of_water_collision_sensors` + `rotoscope_rpm_per_cycle`.

**Test.** From `MOVING_PARTS.json`:

```
all_hinged_part_properties    rows=25 members=['lod','target_position_variable','use_target_position_as_angle']
all_rotating_part_properties  rows=12 members=['inverted','number_of_water_collision_sensors',
 'rotoscope_enabled','rotoscope_rpm_per_cycle','rpm_variable','special_collision_enabled']

hinged rows with empty variable: []
rotating rows with empty rpm: []
use_target_position_as_angle: Counter({0: 24, 1: 1})
lod: Counter({1: 22, 0: 3})
```

**Result.** Every member, every row, every flag value matches the doc's table cell for cell (the
rotating table's 12 rows also match the printed values: water sensors 5/3/0/3/3/3/0/3/3/0/3/3).

> **Verdict: HOLDS.**

---

## A13 · `SteeringFork` is the only angle-flag row — **HOLDS**

```
use_target_position_as_angle: Counter({0: 24, 1: 1})
```

The single 1 is `SteeringFork` (variable `steering_angle_inverted`, `lod` 0) in the printed table.
The *flag* claim is exact; what the flag means is A7.

> **Verdict: HOLDS** (flag decoded; semantics UNKNOWN).

---

## A14 · "11 of 25 hinged used, 15 declared-unused" — **HOLDS** in the doc, **BROKEN** in §12

**Claim.**

```
MOVING_PARTS.md:10    "all_hinged_part_properties | 25 | 11 | …"
MOVING_PARTS.md:199   "The 15 declared-but-unused names (12 spider-leg parts, 2 elevons, BoatRudder)
                       have no user in the fleet"
GRAB_BACKLOG.md:1297  "11 of 25 hinged names used, 15 declared-unused incl. 12 spider legs"
```

**Test.** Names in the seven tables with no part in `PARTS_TABLE.jsonl`:

```
15 ['BoatRudder','FrontLeftCoxa','FrontLeftFemur','FrontLeftTibia','FrontRightCoxa',
    'FrontRightFemur','FrontRightTibia','LeftElevon','RearLeftCoxa','RearLeftFemur',
    'RearLeftTibia','RearRightCoxa','RearRightFemur','RearRightTibia','RightElevon']
```

**Result.** The doc's decomposition is right: 12 spider-leg names + 2 elevons = 14 unused *hinged*
rows, plus `BoatRudder` in the *fin* table = 15 unused names overall. The §12 row conflates the
two sets ("11 of 25 … 15 declared-unused") and does not add up: 25 − 11 = 14.

> **Verdict: HOLDS** in `MOVING_PARTS.md`; **BROKEN** as written in the §12 summary.

---

## A15 · `AirBrake` — 3 parts, 1 `CAirPlane`, nothing on land — **HOLDS**

**Claim.** The card's Done criterion: "`AirBrake` on a car is listed as the only probe (for Q-1)
unless a `CCar` user is found."

**Test.** AirBrake rows in `PARTS_TABLE.jsonl` (A5) are the three `v4602` variants — one chassis,
`CAirPlane`. Now search *every* parts module in *all* 314 containers for the string:

```
$ … for every container, every *_parts.vmodc, behaviour set
AirBrake users: none outside fighterbomber_vehicle_parts.vmodc (3 variants of v4602)
```

and the pre-existing module-level scan (all 87 cached modules + all fleet modules) shows
`AirBrake` only in `fighterbomber_vehicle_parts.vmodc`, while the control behaviour
`FrontLeftDoor` appears in 174 base + 38 DLC module copies.

**Result.** No `CCar` user exists anywhere in the fleet, DLC included. The probe stands — and the
honest reading is stronger than the doc's: it is **one** part on **one** aircraft, so porting it to
a car is entirely unproven.

> **Verdict: HOLDS** (the "nothing on land" claim survives the wider search; only "3 parts" is
> inflated, A5).

---

## A16 · the six turreted samples — **HOLDS**

**Claim.**

```
MOVING_PARTS.md:181-186  "The six G2-13 turreted samples … fill door_parts[] - v0200 APC 5,
                          v0201 medium tank 1, v0202 Bavarium tank 1, v0504 technical 4,
                          v0600 armoured jeep 5, v0603 small tank 1 - and none fills hinged_parts[]
                          or rotating_parts[] (max 0 / 0)"
```

**Test.**

```
apc_vehicle_parts.vmodc            {'door_parts': 5, 'hinged_parts': 0, 'rotating_parts': 0}
mediumtank_vehicle_parts.vmodc     {'door_parts': 1, 'hinged_parts': 0, 'rotating_parts': 0}
bavariumtank_vehicle_parts.vmodc   {'door_parts': 1, 'hinged_parts': 0, 'rotating_parts': 0}
technicaljeep_vehicle_parts.vmodc  {'door_parts': 4, 'hinged_parts': 0, 'rotating_parts': 0}
armoredjeep_vehicle_parts.vmodc    {'door_parts': 5, 'hinged_parts': 0, 'rotating_parts': 0}
smalltank_vehicle_parts.vmodc      {'door_parts': 1, 'hinged_parts': 0, 'rotating_parts': 0}
sportsmuscle_vehicle_parts.vmodc   {'door_parts': 3, 'hinged_parts': 0, 'rotating_parts': 0}
```

Member names in those arrays:

```
door_parts   in the APC: ['part_index']
hinged_parts in a module with rows: ['part_index']
rotating_parts: ['max_rpm_visible','min_rpm_visible','number_of_blades','part_index',
                 'position[0]','position[1]','position[2]','rotation_axis[0]',
                 'rotation_axis[1]','rotation_axis[2]','rpm_multiplier','rpm_opacity_transition']
```

**Result.** All six counts and the "0 hinged / 0 rotating" claim are exact; `rotating_parts[]` is
indeed the only array with geometry, and `door_parts`/`hinged_parts` store nothing but an index.
(The card's §3 sentence about the six was already corrected by the 2026-10-29 rework from an older
"fill none of the three".)

> **Verdict: HOLDS.**

---

## A17 · `rotoscope_rpm_per_cycle` — **BROKEN** in §12, correct in the doc

**Claim.**

```
GRAB_BACKLOG.md:1297  "rotating carrying `rpm_variable` + rotoscope flags + 20 rpm/cycle"
MODLOG:9739           "`rotoscope_rpm_per_cycle` (20.0 on every row)"
MOVING_PARTS.md:86-88 "`rotoscope_rpm_per_cycle` holds 20.0 on 7 …; 50.0 on 5 (LeftRotor,
                       RightRotor, Rotor, OuterLeftRotor, OuterRightRotor). What the field drives
                       is not defined in any file read here"
```

**Test.**

```
rotoscope_rpm_per_cycle values: Counter({20.0: 7, 50.0: 5})
rows=20.0: 7
rows=50.0: 5
```

**Result.** The doc is right (7/5, meaning marked UNKNOWN) and the old MODLOG sentence was
corrected in the 2026-10-29 rework (`MODLOG:14740`). The §12 row was **not** corrected: it still
says "20 rpm/cycle" as a fleet-wide value, and its own rework entry claims that row now reads
"20/50 rpm per cycle" (`MODLOG:14661`). Reading the file today:

```
| G2-14 | done | … rotating carrying `rpm_variable` + rotoscope flags + 20 rpm/cycle, …
         38 behaviours have a row, 29 do not … 37 proven on `CCar` and 30 not …
         `door_parts` 224/56 … `hinged_parts` 148/28 … `rotating_parts` 47/22 …
```

Every one of those five summaries is superseded by evidence above (A1, A3/A4, A6).

> **Verdict: BROKEN** at the §12 row; the generated doc is correct.

---

## A18 · "`--check` validates the tables" — **WEAK**

**Claim.**

```
MOVING_PARTS.md:190-196  "`jc3moving.py --check` re-reads the module and the census, rebuilds both
                          files and compares them: table row counts are 14/25/12/1/1; … every
                          behaviour's proof follows from its chassis classes …"
```

**Test 1 — does it re-read the module?** No: `common_module()` short-circuits on the cache:

```
jc3moving.py:81-86
cached = os.path.join(RAW, "tmp", COMMON)
if os.path.exists(cached):
    return open(cached, "rb").read()
rows = jc3index.load_index(OUT); r = jc3detail.pick(rows, CONTAINER)
```

So `--check` compares the renderer against a **local copy**. The copy happens to be correct today
(A2: identical to the container), but a stale or edited cache would still pass — the tamper tests
cited in MODLOG changed the JSON and the cache, not the game file.

**Test 2 — do the invariants test the claims?** One of them asserts A1's false claim:

```
jc3moving.py:506-510
for must in ("Turret", "Cannon", "Wheel", "Body"):
    ...
    if must in {r["name"] for t in d["tables"] for r in t["rows"]}:
        bad.append(f"behaviour {must} unexpectedly has a vehicle_common row")
```

`d["tables"]` holds only the five decoded tables, so `Wheel` (a row in
`all_wheel_part_properties`) passes. Likewise the proof invariant is the generating expression
(A9), and the fleet-scope invariants (AirBrake on one chassis, turreted 0 hinged/rotating) are true
— they were re-verified here independently.

**Result.** `--check` is a good regression test for the renderer and a weak test of the game: it
cannot see a table it does not decode, cannot see a container it does not re-read, and one
invariant actively holds a false statement green.

> **Verdict: WEAK.** The PASS is real for what it covers, and the claim "re-reads the module" is
> not what the code does when the cache exists.

---

## What this does and does not change

* **Unchanged and confirmed:** the whole `vehicle_common` decode — 53 rows in the
  five originally-modelled families, every member, `lod`, the angle flag, the rpm variables, the
  7/5 rpm-per-cycle split, the name-only door/fin/spring rows, the 15 declared-unused names, the
  per-array row *shapes*, the six turreted samples, the `AirBrake` probe, the 79 chassis / 0 empty
  class lists, and the 231/233 class resolution.
* **Changed by wider data:** 7 part-property tables (not 5) → 42 behaviours with a row, 25 without;
  314 vehicle containers → 70 behaviours, DLC `CCar` uses `RadarFast` (38/29), arrays
  229/162/74 over 86 modules; 233 byte-identical `vehicle_common` copies.
* **Presentational:** "3 parts" is 1 part × 3 variants; "0..1" and "the animation system writes it"
  are inferences where the rest of the doc says UNKNOWN; §12 still repeats four superseded
  numbers.
* **Not done here:** the `.epe` of the 81 DLC containers was read as raw class strings in the
  `.epe` (validated against the base game's decoded histograms), not through `jc3detail`'s
  converter, which writes temp files; the 39 DLC drone containers declare none of the six root
  classes, so their `Mood*` behaviours have no class in this record's vocabulary. Nothing was
  written into `D:\Games`, no game was launched, nothing was committed.
