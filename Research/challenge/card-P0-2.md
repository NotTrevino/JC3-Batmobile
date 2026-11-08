# Assumption challenge — P0-2 · Feature census script

Challenger: Freebuff (did not write this card). Date: 2026-10-29.
Card: `GRAB_BACKLOG.md` §3 `P0-2` (line 364), tracker row §12 line 1275, MODLOG
§"P0-2 · Feature census written, and the four §2 claims reconciled" (line 7752).
Outputs read: `Research/JC3Grab/FEATURE_CENSUS.md` + `.json`, `Tools/scripts/jc3_feature_census.py`,
and the three inputs it reads (`E:/Modding/_JC3grab/detail/*.ee.json`,
`E:/Modding/_JC3grab/entities/*.ee.json`, `Research/JC3Grab/PARTS_TABLE.jsonl`, `INDEX.jsonl`).
Read-only: nothing was written except this file; no game was launched; nothing was committed.

The card's own gate is green:

```
$ python Tools/scripts/jc3_feature_census.py --check
ok FEATURE_CENSUS.json
ok FEATURE_CENSUS.md
check ok: census matches the data (232 entities, 53 armed, 25 weapon ids)
EXIT=0
```

A green `--check` here means *the two files equal a fresh re-derivation*, not that any claim in them
is true. That distinction is assumption A11 below and it is the reason several of the numbers
survive while being wrong.

## VERDICT summary

| # | assumption (stated or silent) | verdict |
|---|---|---|
| A1 | "chassis" = the parent folder of the decoded `.ee` path | **HOLDS** |
| A2 | the 232 decoded graphs are the fleet (232 = every vehicle `.ee`) | **WEAK** — the fleet is 233; one armed-looking variant has no graph |
| A3 | "armed" (a weapon class in the graph) means a fitted, firing weapon | **HOLDS** on the mechanism, **WEAK** on the `.ee` counts (19 of 53 are `_debug`/`signature_*`) |
| A4 | "25 weapon ids (26 spellings)" counts weapons | **BROKEN** — 22 are weapon names, 3 are `.ftune` explosion tunes |
| A5 | "22 of the 25 have an archive directory" is a completeness stat | **WEAK** — the 22 directories *are* the weapons; the 3 without one are the non-weapons |
| A6 | the one-entry alias table `WEAPON_ID_ALIASES` decides "one weapon" | **WEAK** — `w613_bomb` is an explosion tune; the alias is right for a different reason than the one stated, and the same evidence would alias three more |
| A7 | "`vehicle_common` defines the behaviours and the variable that drives each one" | **BROKEN** as stated — 25 of the 67 behaviour names have no entry, incl. `Turret` (22 parts/7 chassis) and `Cannon` (68/11) |
| A8 | the donor's `vehicle_common` module speaks for the whole fleet | **HOLDS** — 232/232 entity files expose the same 7 tables |
| A9 | "`EngineRotatingPart` / `engine_rpm` on the `v0506` tractor" (census verdict "match") | **WEAK** — a name-join of two facts from two files; v0506's own rows never show the variable driving that part |
| A10 | "AirBrake: fighter-bomber only" ("still the only land-use probe") | **HOLDS** |
| A11 | the §2 reconciliation table is evidence a reader can trust | **BROKEN by design** — its verdicts are hand-written strings; `--check` cannot fail them, and one of them certifies A4 |
| A12 | "every vehicle carries one `CForcePulse`" | **HOLDS** (232/232 `.ee`, 79/79 chassis) |
| A13 | "parts" / "objects" are fleet quantities | **WEAK** — parts are counted per `.ee` row over a per-chassis module: 11,643 counted vs 3,661 distinct |
| A14 | any unit or coordinate convention | n/a — P0-2 has no physical value; its only convention is counting granularity, which A2/A3/A13 test |

Six assumptions hold, six are weak, three are broken (A4, A7, A11 — A11 is what lets A4 through).
Nothing here overturns §2's *purpose* (JC3 does give cars weapons, EMP exists, land vehicles have
moving-part behaviours); it overturns three of the numbers and one of the claim's wordings.

---

## A1. "chassis" = the parent folder of the `.ee` path — **HOLDS**

Test: print the entity ids and the derived `chassis`/`scheme`, and count distinct chassis over all
232 graphs.

```
$ python -c "import sys; sys.path.insert(0,'Tools/scripts'); import jc3_feature_census as c; …"
sample entity ids:
   editor/entities/jc_vehicles/01_land/v0200_car_capstone_apc/v0200_car_capstone_apc_debug.ee | chassis= v0200_car_capstone_apc | scheme= 01_land | root= CCar
   editor/entities/jc_vehicles/01_land/v0201_car_capstone_mediumtank/v0201_car_capstone_mediumtank_military_01.ee | chassis= v0201_car_capstone_mediumtank | scheme= 01_land | root= CCar
schemes: Counter({'02_air': 23, '01_land': 18, '03_sea': 12})
files: 232 distinct chassis over ALL detail graphs: 79
```

Every path is `editor/entities/jc_vehicles/<scheme>/<chassis>/<file>.ee`, so `split("/")[-2]` is
the chassis folder and `split("/")[3]` the scheme. 79 chassis for 232 `.ee` is the right order of
magnitude (≈3 variants per chassis) and matches the `CForcePulse` "every vehicle" count (79), which
is derived from the same field — a self-consistency check, not an independent one, but no path in
the corpus breaks the pattern.

## A2. 232 decoded graphs = the fleet — **WEAK**

Test: compare the three corpora by entity id.

```
INDEX vehicle .ee paths: 233
PARTS_TABLE entities: 233
INDEX not in PARTS_TABLE: 0
PARTS_TABLE not in INDEX: 0
files: 232 distinct chassis over ALL detail graphs: 79
in PARTS_TABLE not in detail: ['editor/entities/jc_vehicles/02_air/v2602_helicopter_urga_lightassault/v2602_helicopter_urga_lightassault_military_01_custom_mm230.ee']
```

The fleet is **233** `.ee` (`INDEX` and `PARTS_TABLE` agree exactly); only **232** have a decoded
`.epe` graph, and the census prints `entities: 232` and `parts_table_rows: 233` side by side without
reconciling them. The missing one is not inert:

```
module: lightassault_vehicle_parts.vmodc | parts: 44
  i=42 n=lightassault_minigun_l_barrel b=GatlingGun  m=lightassault_minigun_l_barrel.lod
  i=43 n=lightassault_minigun_r_barrel b=GatlingGun  m=lightassault_minigun_r_barrel.lod
  i=30 n=lightassault_minigun_mount_l_vertical b=Cannon …
  i=31 n=lightassault_minigun_mount_r_vertical b=Cannon …
```

A `mm230` (machine-gun calibre) variant with two minigun barrels and two cannon mounts, whose graph
was never decoded. `53 armed` is therefore a count over 232 of 233 files and is one armed `.ee`
short *at most*, one short *at least* of the possible population. The chassis count (21 of 79) is
unaffected because `v2602` is already armed through its sibling `.ee`. Verdict: **WEAK** — a
fleet-wide claim on an incomplete corpus, with the incompleteness invisible in the output (the two
totals sit in the same table).

## A3. "armed" = a weapon class in the graph = a fitted weapon — **HOLDS on mechanism, WEAK on counts**

The risk R5 describes is exactly this: a class *name* standing in for a behaviour. Four tests:

```
armed: 53
armed without bullet/missile: 0                     # every armed .ee has a real weapon base
armed with 0 SWeaponPoint: 0                        # every armed .ee has a firing point
armed only by CAimPOIWeaponComponent: 0             # an aim component never creates "armed"
unarmed .ee with a w6xx id string: 0                # the id scan and the class scan agree
CBulletWeaponBase objects per .ee: Counter({1: 33, 2: 12})   # tank = cannon + mgun, not double counting
bullet chassis: 17 | chassis with a non-debug armed .ee: 17
chassis armed ONLY via a _debug .ee: []
```

So no entity is "armed" by a name alone, and no chassis depends on a dev variant. What is weak is
the *file* granularity:

```
CBulletWeaponBase: 45 .ee, of which _debug: 12
CMissileWeaponBase: 19 .ee, of which _debug: 5
armed with debug/custom/sig in the name: 19
   v0300_car_kensington_sportsmuscle_signature_preorder.ee ['CAimPOIWeaponComponent', 'CForcePulse', 'CMissileWeaponBase']
   v0201_car_capstone_mediumtank_debug.ee ['CBulletWeaponBase', 'CForcePulse', 'CLightWeaponComponent']
```

§2.1's "**17 chassis / 45 `.ee` / 57 objects**" mixes a chassis count (survives every variant
question, 17/17 non-debug) with `.ee` and object counts in which 12 of 45 (27 %) are `_debug` dev
entities. The claim "the fleet carries these weapon components" is true; "45 `.ee`" is a file count
of the shipped data, not a count of armed production vehicles, and the census does not say so.

## A4. "25 weapon ids (26 spellings)" counts weapons — **BROKEN**

The id regex `w6\d\d_[a-z0-9_]+` is run over **every string value of every `.epe` object**, not over
weapon fields. The corpus therefore contributes `.ftune` explosion paths. Grouping every spelling by
where it appears:

```
w601_helicopter_missile                  {'field:name': 3}
w602_mediumtank_canon                    {'field:name': 14, 'ftune/explosion': 7}
…
w604_helicopter_mgun_impact              {'ftune/explosion': 11}
w610_fighterjet_mgun_impact              {'ftune/explosion': 3}
w613_bomb                                {'ftune/explosion': 3}
w617_vintagefighter_mgun_impact          {'ftune/explosion': 2}

example ftune hits:
   w610_fighterjet_mgun_impact -> editor/entities/jc_explosions/weapons/w610_fighterjet_mgun_impact.ftune
   w613_bomb                   -> editor/entities/jc_explosions/weapons/w613_bomb.ftune
   w604_helicopter_mgun_impact -> editor/entities/jc_explosions/weapons/w604_helicopter_mgun_impact.ftune
```

and where one of them sits:

```
v4202_plane_capstone_fighterjet_debug.ee | CForcePulse | ForcePulse
   field: SettingsFile = editor/entities/jc_explosions/weapons/w610_fighterjet_mgun_impact.ftune
```

**22 spellings are weapon object names; 4 are explosion-tune names and never a weapon name**
(`w604_…_impact`, `w610_…_impact`, `w617_…_impact`, `w613_bomb`). The census aliases exactly one of
the four (`w613_bomb`), so its `25` = 22 weapons + 3 explosion tunes. §2.1's "**25 weapon ids** (26
spellings: `w613_bomb` is the same weapon as `w613_…_ground_lockon`)" is therefore wrong twice: the
count includes three non-weapons, and its one alias is justified by a name coincidence when the
evidence is that `w613_bomb` is that weapon's explosion `.ftune`.

The right number is the one the census already computes and prints beside it: **22 archive weapon
ids** (`jc_weapons/06_vehicle/<id>/`), which match the 22 `field:name` spellings one-for-one.

## A5. "22 of the 25 have an archive directory" — **WEAK**

```
dirs not named in any .epe: []
epe spellings with no archive dir: ['w604_helicopter_mgun_impact', 'w610_fighterjet_mgun_impact',
                                    'w613_bomb', 'w617_vintagefighter_mgun_impact']
```

The sentence reads as "22 of 25 are shipped, 3 exotic", which is backwards: the 22 are the weapons
and the 3 (after the alias) are explosion tunes that have no business being in a weapon count. The
arithmetic is right; the framing invites the reader to trust the 25.

## A6. The typed alias table decides "one weapon" — **WEAK**

```python
WEAPON_ID_ALIASES = {"w613_bomb": "w613_fighterbomber_missile_ground_lockon"}
```

This is the only reason the count is 25 and not 26, and it is a hand-written single entry with a
comment ("both weapon 613 (the same tune, named for the payload)") rather than a derived rule. The
data supports the conclusion for a different reason (the `.ftune` path above), and it supports the
same treatment for the other three `_impact` tunes. So the census applies a "one weapon, several
names" rule exactly once, where a human happened to look, and counts the identical pattern three more
times as separate weapons. A rule like "a spelling that only ever appears under `jc_explosions/` is
an effect, not a weapon" would have produced 22 without a hand table.

## A7. "`vehicle_common` defines the behaviours and the variable that drives each one" — **BROKEN as stated**

Test: compare the 67 behaviour names in `PARTS_TABLE.b` with the 57 names in the donor's seven
`all_*_part_properties` tables.

```
part behaviours: 67 | names in the 7 tables: 57
behaviours with NO entry in any all_*_part_properties table: 25
   ['Antenna', 'Axle', 'BavariumShield', 'Body', 'Cannon', 'CenterLeftWindow', 'Engine',
    'FrontLeftWindow', 'FrontRightWindow', 'FrontWagonCoupling', 'LandingSkid', 'RearLeftWindow',
    'RearRightWindow', 'RearWagonCoupling', 'RearWindow', 'Stabilizer', 'Tail', 'TailWing',
    'TrainCargo', 'TrimTab', 'Turret', 'Windshield', 'WindshieldWiper',
    'FrontLeftDoor'-class names, …]
behaviour tables: [('all_door_part_properties', 14), ('all_fin_part_properties', 1),
 ('all_hinged_part_properties', 25), ('all_propeller_part_properties', 1),
 ('all_rotating_part_properties', 12), ('all_spring_part_properties', 1),
 ('all_wheel_part_properties', 4)]
```

Two of the missing 25 are the ones the project cares most about:

```
Turret  parts=  22 entities= 22 chassis=  7
Cannon  parts=  68 entities= 40 chassis= 11
```

and the behaviour is not in any entity module either:

```
$ python … (scan all 232 entity module sets for all_*_(turret|cannon|weapon)*_part_properties)
turret/cannon/weapon behaviour tables found: {}
```

So §2.3's "**`vehicle_common` defines the behaviours and the variable that drives each one**" is
true for the 7 tables (rotors, gatling, steering, flaps, air brakes, doors, wheels/springs) and false
for 25 of the 67 names the same paragraph's next clause ("the parts tables show who uses them")
counts — including `Turret` and `Cannon`, whose driving variable this module never provides and whose
definition lives in the turret/weapon component, not in `vehicle_common`. Even inside the 7 tables
the "variable" is not universal:

```
behaviours: 67 | with a table entry: 42 | with a non-empty variable: 23
entry but no variable: ['BrakeCalipers', 'BrakeDisc', 'BrakeDrum', 'CargoBayDoor', 'CenterLeftDoor',
 'CenterRightDoor', 'FrontLeftDoor', 'FrontRightDoor', 'Hood', 'LeftWing', 'MissileHatch', 'RearDoor',
 'RearLeftDoor', 'RearRightDoor', 'RightWing', 'Spring', 'Trunk', 'TurretDoor', 'Wheel']
```

So the census's own data says: 23 of 67 part behaviours have a driving variable here, 19 more have a
table entry with no variable (doors and wheels are animated by other systems), and 25 have nothing.
The census prints 57 names and 67 behaviours and never says that 25 (or 44) have no variable.

## A8. The donor's `vehicle_common` speaks for the fleet — **HOLDS**

```
donor tables: {'all_door_part_properties': 29, 'all_fin_part_properties': 3, …} sum 307
entity files: 232 | with no VehicleCommon tables: 0 | table-set differences: 0
```

Every one of the 232 entity module sets exposes exactly the donor's seven `all_*_part_properties`
table names. Reading one entity is legitimate here — the module is
`editor/entities/jc_vehicles/00_shared/modules/vehicle_common.vmodc`, shared by every vehicle, and
the decoded copies agree on the table set. (Values inside the tables are not compared across
entities; the census's `variable` column is a string from the shared table, so this holds at the
level the census uses it.)

## A9. "`EngineRotatingPart` / `engine_rpm` on the `v0506` tractor" — **WEAK**

The census's reconciliation row says:

```
claim: "§2.3 EngineRotatingPart on v0506"
derived: "1 chassis ['v0506_car_solar_oldtractor'], 3 parts"
verdict: "match (v0506_car_solar_oldtractor)"
```

`EngineRotatingPart` parts on v0506 is real (`PARTS_TABLE`: 3 parts / 3 entities / 1 chassis), and
`all_rotating_part_properties[10]` is `EngineRotatingPart → engine_rpm` in the shared table. But the
two facts are joined **by name only**: the census never shows v0506's own data driving that part with
`engine_rpm`. What v0506's own modules offer is suggestive, not proof:

```
  VehicleCommon 39 rpm rows; e.g. ('all_vehicles_common.radar_rpm_slow', 30), ('all_rotating_part_properties[0].rpm_variable.string', 'main_rotor_rpm')
  Transmission  19 rpm rows; e.g. ('upshift_rpm[0]', 2250) …
  LandEngine    12 rpm rows; e.g. ('rpm_power_band', 0), ('resistance_at_min_rpm', 0.2) …
```

The variable exists in the shared table and the part exists on the tractor; whether the tractor's
part is bound to that variable is an inference from a name match (and no `.epe` object in the whole
corpus mentions `AirBrake`/behaviour wiring — the behaviour binding is in the parts module, not the
graph). Defensible as a hypothesis; it is presented as "match".

## A10. "AirBrake: fighter-bomber only" — **HOLDS**

```
AirBrake  parts=3 entities=3 chassis=1 ['v4602_plane_urga_fighterbomber']
chassis whose .epe graph mentions AirBrake: {}
```

The only AirBrake parts in the 233-row fleet table are on the fighter-bomber, and no car has one.
The behaviour *slot* does exist for every vehicle (`all_hinged_part_properties` lists `AirBrake →
air_brakes_T`) — so the negative is about part usage, which is what §2.3 needs ("only `AirBrake` on a
car stays a probe"). Wording nit: the verdict says "still the only land-use probe" while the one
chassis is an aircraft; the intended meaning ("no land vehicle uses it") is correct.

## A11. The reconciliation table is evidence — **BROKEN by design**

The table is not derived. It is a literal list in `build()`:

```python
reconciliation = [
    {"claim": "§2.1 25 weapon ids",
     "derived": "%d ids (%d spellings incl. w613_bomb) …" % (…),
     "verdict": "match (25 ids after the w613_bomb alias; 26 spellings; 22 archive dirs)"},
    …
    {"claim": "§2.3 AirBrake: fighter-bomber only", "derived": …, "verdict": "match - still the only land-use probe"},
]
```

`derived` is computed (good, R11); `verdict` is prose. `--check` only compares the rendered files
with a fresh render, so:

* a data change that moves a count turns the page red (the derived cell differs) — good;
* but after `--write` the **verdict stays** whatever it was written as, and nothing can fail it;
* the failure mode is already present: the A4 row's verdict certifies "match (25 ids after the
  w613_bomb alias…)" for a number that is 22 weapons + 3 explosion tunes.

That is the R4/R5 shape again, one level up: the artefact asserts `match` because a human typed
`match`. A derived verdict ("every id has an archive dir", "every spelling appears as a weapon
`name`") would have failed on A4/A5.

## A12. "Every vehicle carries one `CForcePulse`" — **HOLDS**

```
CForcePulse | 307 | 232 | 79
CForcePulse entities: 232
```

232 of 232 `.ee` and 79 of 79 chassis carry exactly the class; an unarmed car shows only that class:

```
  v0000_car_autostraad_oldjeep_civilian_01.ee weapon-ish classes: {'CForcePulse': 1}
```

Excluding it from "armed" is therefore a judgement about what a weapon is (the pulse is a defensive
EMP, G2-17), not a data artefact — and it is applied consistently (53 armed without it, 0 armed by
it alone).

## A13. "parts" and "objects" are fleet quantities — **WEAK**

`PARTS_TABLE` has one row per `.ee`, but the module is shared per chassis:

```
rows: 233 | distinct parts modules: 79
most shared modules: [('oldtruck_vehicle_parts.vmodc', 9), ('monorailcargoengine_vehicle_parts.vmodc', 7),
                      ('oldjeep_vehicle_parts.vmodc', 6), ('buggy_vehicle_parts.vmodc', 6), ('cargotransport_vehicle_parts.vmodc', 6)]
parts counted over rows: 11643 | parts counted once per module: 3661
```

So `parts_table_parts: 11643` is 3.2× the distinct part definitions, and a per-behaviour "parts" cell
(e.g. `Flaps 202`) repeats each variant's copy for every `.ee` of a chassis. Chassis counts are
unaffected (the same chassis is counted once); `.ee`/part counts are inflated by variants — the same
pattern as A3. This is the "one value, three units" problem the backlog §2 fixed for *chassis* and
left in place for parts and objects.

## A14. Units and coordinate conventions — none to test

P0-2 carries no physical value, no axis, no unit conversion; its numbers are counts of strings,
files and graph nodes. The only convention it uses is granularity (chassis / `.ee` / object / part),
and that is what A2/A3/A13 test. The card's Do clause ("the `.md` reproduces every number in §2.1
and §2.3") is satisfied for the numbers it derived; the units of those numbers are where the
challenge lands.

---

## What remains true after the challenge

* JC3 ships vehicle weapons on cars: 22 weapon ids, each with a `jc_weapons/06_vehicle/<id>/`
  directory, over 21 of 79 chassis, every armed `.ee` with `SWeaponPoint` > 0. T-W1's `out` stays
  refuted.
* The decisive donor claim holds at both ends: `v0300_…_signature_preorder.ee` carries
  `CMissileWeaponBase` + `CAimPOIWeaponComponent` + 4 `SWeaponPoint`s and `w618_sportsmuscle_missile`,
  and the shared parts module of the same chassis (used by our `civilian_01` donor) contains
  `sportsmuscle_hood_signature` and `sportsmuscle_missile_base_signature`:

```
armed: v0300_car_kensington_sportsmuscle_signature_preorder.ee ['CAimPOIWeaponComponent', 'CForcePulse',
       'CMissileWeaponBase'] wpoints 4 ['w618_sportsmuscle_missile']
module: sportsmuscle_vehicle_parts.vmodc
names with signature/missile: ['sportsmuscle_hood_signature', 'sportsmuscle_missile_base_signature']
```

* The moving-part negatives hold: `AirBrake` only on the fighter-bomber, `EngineRotatingPart` only
  on v0506, `SteeringWheel` on 9 chassis including the sailboat, `GatlingGun` on the racing boat and
  both assault helicopters, `MissileHatch` 16 parts on the monorail car.
* The three numbers to change if this is acted on: §2.1's "25 weapon ids" → **22 weapons
  (+4 explosion-tune spellings, one aliased)**; §2.3's "the variable that drives each one" → **42 of
  the 67 names have a table entry and only 23 have a non-empty driving variable**
  (`67 behaviours, 42 with an entry, 23 with a variable`; the 19 without one include every door,
  `Wheel`, `BrakeDisc`, `Spring` and `MissileHatch`); and the `--check` line that certifies "match"
  → a derived predicate, or no verdict column at all.
