# Assumption challenge — G2-29 (`Traffic, AI and spawning of v0300`)

Scope: the card (`GRAB_BACKLOG.md`, "G2-29 · Traffic, AI and spawning of `v0300`"), the §12 row for
it, the MODLOG block `G2-29 … intended change` / `… done` (lines 10456–10549) and the card's
outputs `Research/JC3Grab/TRAFFIC.md` (+ `TRAFFIC.json`, built by `Tools/scripts/jc3traffic.py`).

Everything below was run against the index and the archives read-only. Nothing was launched, no
archive was written, nothing under `D:\Games` was opened, nothing committed. All offsets are byte
offsets into the archive entry (unpacked), not file offsets.

---

## VERDICT

**The card's answer survives, and its central number survives a parser rewrite. Two of the
supporting claims do not.**

| # | Assumption | Verdict |
|---|---|---|
| A1 | `settings/spawn_vehicle_defs.bin` is the pool ambient traffic is drawn from | **WEAK** — the "Ground Vehicles" label is real, but the same 86-name catalogue is also the Rebel Drop catalogue (85/86), so the label does not prove a traffic consumer |
| A2 | The donor's record is path + 13 tags + name at 23240 | **HOLDS** |
| A3 | The donor satisfies exactly one traffic selector, a civilian *car* rule | **HOLDS** — 41 → 47 selectors under a wider tag vocabulary, still exactly 1 match, same selector |
| A4 | That rule spawns an NPC driver, so the record means NPC-driven Batmobiles | **WEAK** — the `Driver` seat and the bts trees exist in the file, but neither sits next to this rule |
| A5 | "The entity ships its own AI module" supports the AI claim | **BROKEN** — the `/ai/`-named file is a 3-byte-different copy of the *wheel* module and the `.ee` never references it; 76 of 86 chassis have one (all 10 that do not are bikes) |
| A6 | Only `civilian_01` is in the ground-vehicle table; each `v0300` build sits in exactly one table | **HOLDS** |
| A7 | A pool key is "in the same record"; 8 of 86 carry one; donor's pool is UNKNOWN | **HOLDS** in conclusion, **WEAK** in wording (the key precedes the record it labels) |
| A8 | "86 records, each `entity path` + `tag list` + `name`" | **WEAK** — 22 of 86 records have no tag string at all; the tag census covers 64 records |
| A9 | Tag census: 32 `ambient`, 14 `liberated`, 14 both, 0 `liberated`-without-`ambient`, 10 `*_traffic` | **HOLDS** |
| A10 | No shipped region level places the donor; "the spawner is what puts it in the world" | **HOLDS**, with a control the card never ran (and three hash-only carriers it never looked for) |
| A11 | Nothing outside the 11,751 scanned files can carry a spawn site ("none is a data table") | **WEAK** reasoning, **HOLDS** empirically — the unread set contains data-shaped types, all of which I scanned: 0 name hits |
| A12 | The Rebel Drop listing is a spawn site | **WEAK** — 85 of 86 ground vehicles are in that list; it is the catalogue, not this car's entry |
| A13 | One chop-shop task key on the donor | **HOLDS** and is specific (54 of 86 names appear) |
| A14 | Registry / `.epe` / `.stringlookup` / `patchmetadata.bin` are not spawn sites | **HOLDS** (and the `.stringlookup` hash is the *name* hash, so "may be a coincidence" is the wrong hedge) |
| A15 | Two level `CVehicleRule`s name the donor, with `point.stunt` | **HOLDS** (full string dump) |
| A16 | "Mario's house" (card wording) is covered | **HOLDS** implicitly — the mission/region files where that content lives hold no donor string |
| A17 | MODLOG: "the six numeric fields of a spawn record (weights? offsets?)" | **BROKEN** — `TRAFFIC.md` says the layout is *not* decoded, and no test covers six numeric fields |
| A18 | Replacing `civilian_01` therefore yields NPC-driven Batmobiles (D-6) | **WEAK** — record validity survives a same-path override, but drivability of the replacement and load of a dropzone `.ee` are unproven |
| A19 | 17 files name the donor out of 11,751 scanned | **HOLDS** — the project's own `--check` reproduces it verbatim |

**Headline.** The load-bearing claim — *the donor has a record in the ground-vehicle spawn table
whose tags satisfy a civilian-car traffic rule* — is solid and parser-independent (A2, A3, A6, A9).
What the report over-sells is the *AI* half: the `Driver`/bts pattern it quotes belongs to the
tank rule, the `/ai/` module it names contains wheel data, and the donor's absence from every
level is only as strong as the control the card never ran (which I ran, and it passes). One
number in the MODLOG ("six numeric fields") has no support in the md at all.

---

## A1 — the ground-vehicle spawn table is what ambient traffic draws from

**Assumption (stated, §2):** "`settings/spawn_budget_pools.bin` names it as *Ground Vehicles* …
so this is the file the spawner draws ground vehicles from."

**Test.** Dump every meaningful string of `settings/spawn_budget_pools.bin`, and count how many of
the table's 86 entity names appear in the Rebel Drop catalogue.

```
all meaningful strings in spawn_budget_pools.bin:
     555 'settings/spawn_boat_defs.bin'         621 'Water Vehicles'
     815 'settings/spawn_aircraft_defs.bin'     889 'Air Vehicles'
    1221 'Miscellaneous Props'                 1415 'Ambient Effects'
    1572 'settings/spawn_road_decoration_defs.bin' 1612 'Road Decorations'
    1924 'settings/spawn_device_defs.bin'      1955 'Rico Device Components'
    2174 'settings/spawn_vehicle_defs.bin'     2206 'settings/spawn_vehicle_premium_defs.bin'
    2246 'Ground Vehicles'
    2648 'settings/spawn_encounter_defs.bin'   2682 'Random Encounters'

profile/item.onlinec [base] 52165 B: 85 of the 86 ground-vehicle names appear
profile/item.onlinec [patch] 52204 B: 85 of the 86 ground-vehicle names appear
```

**Result.** The label is exactly as quoted, so "this is the ground-vehicle pool" is a fact about
the data. What it does not establish is *who* reads the pool: the identical 86-name catalogue is
the Rebel Drop list (85/86), and `spawn_budget_pools.bin` is itself a menu-shaped table
("Miscellaneous Props", "Random Encounters", "Road Decorations") — a spawn/streaming budget list,
not demonstrably the ambient-traffic picker. The md's own §6 concedes the picker is native and
`UNKNOWN`, so §2's "so this is the file the spawner draws ground vehicles from" is one step
stronger than its evidence. Supporting it: the tag vocabulary in these tables is the *same*
vocabulary the `global/global.blo` selectors use (`ambient`, `ground`, `car`, `liberated`,
`highend`, faction `*_traffic` tags), which is why A3's match is meaningful at all.

**Verdict: WEAK.** Keep the claim "the donor has a record in the ground-vehicle pool"; do not read
the pool label as proof that ambient traffic consumes it.

---

## A2 — the donor's record: path + 13 tags + name at byte 23240

**Test.** Raw string dump of `settings/spawn_vehicle_defs.bin` around the record.

```
    23189        '~iT?['
    23215        'Pff'
    23226        ' @ff'
    23240 PATH>> 'editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_civilian_01.ee'
    23359        'vehicle,ground,car,civilian,racing,modern,muscle,kensington,sports,unarmed,unarmored,ambient,liberated'
    23462        'v0300_car_kensington_sportsmuscle_civilian_01'
    23529        '& \'
```

**Result.** Path, tag block and name are three consecutive strings in that order, the tag list is
13 tokens and matches the md character for character, and the offset 23240 in the md is the path's
offset. The file holds 86 `.ee` strings and the parser yields 86 records — no record is invented
and none is skipped (no record needed the basename fallback).

**Verdict: HOLDS.**

---

## A3 — "1 of 41 selectors match", and it is a civilian *car* rule

**Assumption (stated, §3):** the donor's tag set satisfies exactly one of the tag selectors in
`global/global.blo`, `ambient,ground,car,liberated,-highend`.

**Test.** The selector list is filtered by "shares a token with the spawn-table tag vocabulary",
and that vocabulary is itself built by the record parser (see A8), so the count of 41 is
parser-dependent. I rebuilt the vocabulary with a wider rule — everything between one `.ee` path
and the next that looks like a tag list, instead of only the strings between the path and a name
equal to the basename — and re-ran the selector filter and the match test against the same donor
tags.

```
  old   vocab 363 -> selectors 41, donor matches 1: ['ambient,ground,car,liberated,-highend']
  new   vocab 560 -> selectors 46, donor matches 1: ['ambient,ground,car,liberated,-highend']
  union vocab 598 -> selectors 47, donor matches 1: ['ambient,ground,car,liberated,-highend']
```

**Result.** The *denominator* is fragile (41 → 47 with a wider parser, because six more selector
strings then share a token with the vocabulary), but the *numerator* is not: whatever vocabulary
you use, the donor satisfies exactly one selector, and it is always the same string. Only two
`ambient,ground,car*` selectors exist in the file:

```
'ambient,ground,car' selectors present: ['ambient,ground,car,liberated,-highend', 'ambient,ground,car, highend']
```

The donor has `liberated` and no `highend` (tag `highend` occurs on 5 of the 86 records), so the
second selector — the high-end variant — genuinely cannot match. The match is not an artefact of
the vocabulary.

**Verdict: HOLDS.** (The md's "1 of 41" is parser-dependent in its *denominator* — read it as
"1 of 41–47"; the match itself is not parser-dependent.)

---

## A4 — that rule spawns an NPC driver, so traffic = NPC-driven Batmobiles

**Assumption (stated §3 and §6, "Proven"):** "those rules spawn a driver seat with an AI behaviour
tree" and the pairing `selector → rule` is positional.

**Test 1 — the string stream around the matched selector.**

```
     34656 SEL>> 'ambient,ground,car,liberated,-highend'
     34801       'wnK'
     34848       '03_CivilianCarLiberatedProvince'
     34944       '~iT'
     35155       'kjI'
     35232       'character,civilian, -farmer, -servant'
     35404       '/5`'
     37152       'character, highend'
```

**Test 2 — every `Driver` and every `ai/bts/` string in the file, with offsets.**

```
           3348 'Driver'
           3372 'ai/bts/enemies/01_shared/soldier_tank_driver.bts'
           4568 'character,civilian,truck_driver'
           4676 'ai/bts/civilian/civilian_std.bts'
           9200 'ai/bts/vehicle/airplane/airplane_roam.bts'
          17432 'ai/bts/vehicle/boat/military_boat_driver_2.bts'
          30404 'character,civilian'
          30476 'ai/bts/vehicle/boat/civilian_roam_in_boat.bts'
          34848 '03_CivilianCarLiberatedProvince'
          35232 'character,civilian, -farmer, -servant'
  exact 'Driver' strings: 1 ; strings containing 'Driver': ['Driver', 'Passenger_BehindDriver']
  occurrences of b'Driver' in the file: 2
```

**Result.** The pattern the md describes does exist — a `Driver` seat string with a
`ai/bts/...driver.bts` right after it — but it is at 3348/3372, which is the *tank* rule's
neighbourhood (`soldier_tank_driver.bts`), not the civilian car rule's. The one civilian bts,
`civilian_std.bts`, sits at 4676 next to `character,civilian,truck_driver` at 4568. Rule
`03_CivilianCarLiberatedProvince` (34848) is followed by a *character* selector
(`character,civilian, -farmer, -servant`) and nothing else within 8 kB; **no `ai/bts/` path occurs
between 34656 and 43000**. So for this specific rule the file shows a driver *character* list, not a
behaviour tree.

Also: the MODLOG's "2 `Driver` seats" is one seat counted twice — `Driver` plus the substring in
`Passenger_BehindDriver` (`rd.count(b"Driver") == 2`, one of them a different seat name).

**Verdict: WEAK.** "The donor's tags satisfy a civilian-car traffic rule, and this rule block
contains Driver seats bound to bts trees" is supportable as two separate facts. "Those rules spawn
a driver seat with an AI behaviour tree" applied to *this* rule is a positional inference that the
string stream does not carry — and the one seat that *is* paired with a bts belongs to the tank
rule. The lore-break conclusion (D-6) still stands on A1+A3 alone, but the AI half of §6 should be
labelled inference, not "Proven".

---

## A5 — "the entity ships its own AI module" (R5: read by name, not behaviour)

**Assumption (stated §6, "Proven"; and MODLOG "The donor also ships its own `land_global_ai`
module").** `jc3traffic.donor_ai()` selects modules by path: any `.vmodc` under the entity's
`modules/` tree whose path contains `/ai/`.

**Test 1 — the three modules' bytes and strings.**

```
 default/ai/v0300_car_kensington_sportsmuscle_land_global_ai.vmodc   ddd94a31e6fbc514 1600 B
 default/v0300_car_kensington_sportsmuscle_land_engine.vmodc        ecd6fc8bd39b19d5 1207 B
 default/v0300_car_kensington_sportsmuscle_land_global.vmodc        9b7cac5291354692 1600 B
 len 1600 1600 differing bytes: 3
 identical strings? True
 ai module strings containing 'ai'/AI: []
```

The `_ai` file's 31 strings are `LandGlobal`, `number_of_wheels`, `number_of_front_wheels`,
`steering_type`, `wheels_friction_type`, `ground_clearance`, `front_wheels`, `rear_wheels`,
`base_wheel_hardpoint_positions`, `LandWheel`, `radius`, `rim_radius`, `width`, `use_shape_cast`,
`mass`, `arcade_friction_multiplier`, … — the wheel/steering module, byte-for-byte the same string
table as the sibling `_land_global.vmodc` with 3 bytes different.

**Test 2 — does the entity declare its modules?**

```
.ee (5539952 B, 158276 strings) module-ish strings:
   (none)      # 0 occurrences of "modules/" or ".vmodc"
```

**Test 3 — is having an `/ai/` vmodc distinctive?**

```
ground-vehicle table records: 86; chassis with an /ai/ vmodc: 76
  without one (first 8): v3600_bike_urga_combatdirt_military_01, v3502_bike_solar_modernroad_civilian_01,
  v3500_bike_solar_oldmoped_civilian_01, v3000_bike_autostraad_trials_civilian_01, … (all 10 are bikes)
vehicle dirs with a .ee: 79 ; of them with an /ai/ vmodc: 42
```

**Result.** The file exists, so "the entity ships a module whose path says ai" is true. It is not
evidence of AI behaviour: its content is the LandGlobal wheel module, the `.ee` names no module at
all, and *every* car chassis in the table (76 of 76) carries one while no bike does — so presence
tracks "is a car", not "is in traffic". The md's sentence "the entity ships its own AI module(s)"
is exactly the failure mode R5 names: a member read by its name rather than its behaviour.

**Verdict: BROKEN** as support for "AI drives it". Either cite it as "a module named `_ai` exists
and its bytes are the LandGlobal wheel module", or drop it.

---

## A6 — "only `civilian_01` is in that table; each build sits in exactly one table"

**Test.** Every `v0300` record in every `spawn_*_defs.bin`, across base/patch/DLC mounts.

```
v0300_car_kensington_sportsmuscle_signature_preorder  tags=12 group='vehicle|preorder'
     dlc/v0300_preorder/settings/spawn_vehicle_defs.bin [dlc]
v0300_car_kensington_sportsmuscle_civilian_01         tags=13 group=''
     settings/spawn_vehicle_defs.bin [base]
v0300_car_kensington_sportsmuscle_debug               tags= 0 group=''
     settings/spawn_vehicle_proto_defs.bin [patch]
```

Plus: there is no patch- or DLC-mount copy of the ground table that could override the base one —

```
[('dlc/bavarium_sea_heist/settings/spawn_vehicle_defs.bin', 'dlc', 781),
 ('dlc/mech_land_assault/settings/spawn_vehicle_defs.bin', 'dlc', 4894),
 ('dlc/v0300_preorder/settings/spawn_vehicle_defs.bin', 'dlc', 437),
 ('dlc/v0604_preorder/settings/spawn_vehicle_defs.bin', 'dlc', 387),
 ('dlc/v0805_sportmech/settings/spawn_vehicle_defs.bin', 'dlc', 314),
 ('settings/spawn_vehicle_defs.bin', 'base', 27513)]
```

**Result.** Three builds, three different tables, one record each; the donor's table has exactly
one mount and no override. The claim that the Batmobile would inherit a traffic slot *because it
replaces `civilian_01`* is correctly grounded.

**Verdict: HOLDS.**

---

## A7 — "a pool key is a sparse field in the same record; the donor's pool is UNKNOWN"

**Assumption (stated §2):** "Only 8 of the 86 records carry a `a|b|c` key string in the **same
record** … So the key cannot be read as a group label … the donor's pool is `UNKNOWN`."

**Test.** For each of the 8 keys, the record that follows it and the record that precedes it.

```
key vehicle|ground|z80        -> v0402_car_mugello_vintagesuper_civilian_z80_01     | prev v0000…military_z80
key vehicle|ground|civilian   -> v0510_car_solar_modernroadster_civilian_01          | prev v0000…military_z80
key vehicle|ground|rebel      -> v0000_car_autostraad_oldjeep_rebel_01               | prev v0510…civilian_01
key vehicle|ground|military   -> v3600_bike_urga_combatdirt_military_01              | prev v0000…rebel_01
key vehicle|ground|commercial -> v0001_car_autostraad_armoredtruck_commercial_01     | prev v0514…civilian_z80
key vehicle|bavarium          -> v0202_car_capstone_bavariumtank_rebel_01            | prev v0401…racingsupercar
key vehicle|ground|militia    -> v0504_car_solar_technicaljeep_militia_01            | prev v0200…apc_rebel_01
key vehicle|ground|reward     -> v3000_bike_autostraad_trials_signature_01           | prev v0604…buggy_military_01
```

**Result.** All 8 keys match the record *after* them (z80 → a `_z80` build, rebel → a `_rebel`
build, bavarium → the bavarium tank, reward → the `signature` bike), 8 of 8. The key is therefore
not "in the same record" — it is a header for the record that follows, and it is spent on that one
record. The donor's own neighbourhood (`23189 '~iT?['`, `23215 'Pff'`, `23226 ' @ff'`) contains no
key, so "the donor has no pool key" and "its pool is `UNKNOWN`" both survive; what does not survive
is the phrase "in the same record" and, with it, the argument that a key cannot label a following
record.

**Verdict: HOLDS (conclusion), WEAK (wording).** Worth fixing because the same off-by-one could
bite the "8 of 86" number if the parser is ever changed.

---

## A8 — "86 records, each `entity path` + `tag list` + `name`"

**Assumption (stated §2).** The universal quantifier is what the tag vocabulary and the tag census
rest on.

**Test.** Re-parse every record as "everything between this `.ee` path and the next", and compare
with the shipped parser.

```
old records 86, new 86
old: ambient 32 liberated 14 both 14 lw/o-a 0 zero-tag 22 vehicle 63 ground 59
new: ambient 32 liberated 14 both 14 lw/o-a 0 zero-tag 24 vehicle 62 ground 59
records whose tags changed: 2
  ('v0505_car_solar_oldtruck_commercial_cargo_random.ee', ['random_cargo'], [])
  ('v0000_car_autostraad_oldjeep_civilian_01.ee', ['vehicle'], [])
```

and the raw window of a tagless record, showing there is no tag string to find:

```
== settings/spawn_vehicle_defs.bin: 27513 B, 553 strings, 86 '.ee' strings, 86 parsed records ==
  first untagged record v0604_car_urga_buggy_military_z80; raw window:
       1448 PATH>> 'editor\entities\jc_vehicles\01_land\v0604_car_urga_buggy\v0604_car_urga_buggy_military_z80.ee'
       1542       'v0604_car_urga_buggy_military_z80'
       1664       'editor\entities\…\v0000_car_autostraad_oldjeep_military_z80.ee'
  name at i+1: 21, at i+2: 64, no name found (fallback to basename): 1
```

**Result.** For 22 of 86 records the path is immediately followed by the name with no tag block in
between (all of them `_z80` builds), and one of them is parsed by fallback. So "each record" is
false: **64 of 86** records carry a tag list, and the tag census and the 363-token vocabulary are
computed over those 64. This does not touch the donor (path + 13 tags + name, A2), and my wider
parse produces the *same* ambient/liberated counts, but a reader who takes "each" literally will
believe 22 tagless cars participate in tag matching when the data shows no tags for them.

Also, in a sibling table the same heuristic silently drops tags on most records — the name field
there is not the basename, so the parser's `name == basename` test never fires:

```
== settings/spawn_civilian_defs.bin: 24246 B, 616 strings, 135 '.ee' strings, 135 parsed records ==
  raw window: 1940 PATH>> '…civ_male_business_005_avg.ee'  2021 'character,business,male,highend,motor_bike_rider'  2070 'business_male_005'
  name at i+1: 22, at i+2: 20, no name found (fallback to basename): 93
```

93 of 135 civilian records lose their tags that way. That is why A3's selector denominator moves
between vocabularies, and it is a caveat on `jc3traffic.py`'s record model generally.

**Verdict: WEAK.** Fix the sentence to "64 of the 86 records carry a tag list; 22 `_z80` builds
carry none", and note that the tag vocabulary is a lower bound.

---

## A9 — the counted tag census in §5

**Test.** Recompute from the table.

```
records 86, ambient 32, liberated 14, both 14, liberated-without-ambient 0, *_traffic 10
highend records: 5  records with 'vehicle': 63  'ground': 59  zero-tag: 22
```

**Result.** Every §5 number reproduces exactly (32 / 14 / 14 / 0 / 10), and the `highend` exclusion
in the matched selector is a real distinction (5 records carry it, the donor is not among them).

**Verdict: HOLDS.**

---

## A10 — "no shipped region level places the donor" / "the world does not park this car"

**Assumption (stated §4, §7):** absence from the scanned census means absence from the world, so
the spawner is the only thing that puts the donor in a province.

**Test 1 — the card never ran a positive control, so I did.** Scan all 951 `locations/region_*`
`.bl` / `.blo` (2,602,426,933 B) for the donor name, the `v0300_car_kensington` prefix, the name
hash and the path hash — and, as controls, for every one of the 86 table names.

```
read 951 region files / 2602426933 B in 55.5s (errors 0); files containing '.ee': 33

donor patterns:
  prefix v0300_car_kensington     0 files
  name                            0 files
  namehash                        0 files
  namehash_be                     0 files
  pathhash                        1 files  [('locations/region_01/missions/mm180/mm180_csa.bl', 'base', 15884768)]
  pathhash_be                     0 files

control - table names found in region levels: 29 of 86
  v0600_car_urga_armoredjeep_rebel_01                          229 files
  v0000_car_autostraad_oldjeep_rebel_01                         21 files
  v0504_car_solar_technicaljeep_rebel_01                        15 files
  v0600_car_urga_armoredjeep_military_01                        14 files
  v0201_car_capstone_mediumtank_military_01                      9 files
```

**Test 2 — what a level reference actually looks like** (so the control is not measuring a
channel that does not exist):

```
control context in locations/region_01/military/checkpoints/province_a_roadway_1x2_lanes_tunnel_01.blo (341876 B):
  printable: ['CContextActionRule', 'v0600_car_urga_armoredjeep_rebel_01', 'PPPPPPPPPPPP']
  occurrences: 1
```

**Test 3 — the path-hash channel the census never searched.** `D2B46B49 = jenkins(name)` but the
*path* hash is `FC21B7E3`, which the census does not look for. Scanned it across every non-media
type outside the tier list (1,643 files / 1,845 MB), incl. all 1,326 `.fl` scatter files:

```
scanned 1643 files in 12s (errors 0)  hits: 2
   ('pathhash_le', 'dlc/bavarium_sea_heist/locations/sea/dlc3_starfish_base_02.fl', 'dlc', 2142144)
   ('pathhash_le', 'locations/region_01/military/prison_01/prison_01_piers.fl', 'base', 2578160)

.fl hash-noise control: 1326 files, 1730 MB
expected hits for ONE value if bytes were uniform: 0.40
table path-hashes found: 25 of 86 (expected 34.6 by chance)
   3289B439 files=8  v0003_car_autostraad_racinghothatch_civilian_01
   DD7CEDE7 files=3  v0006_car_autostraad_modernbus_commercial_01
   FC21B7E3 files=2  v0300_car_kensington_sportsmuscle_civilian_01
   A5BE707F files=2  v0604_car_urga_buggy_military_z80
control jenkins('x') FAAC85A7 files 1
```

**Result.** The name channel is live (29 of 86 names appear in region levels, up to 229 files
each), and the donor is absent from it — not just as `civilian_01`, but under every `v0300`
build name. The hash hits are noise: 25 of 86 table path hashes occur in `.fl` files at
essentially the rate random bytes predict, a value that belongs to nothing (`jenkins('x')`) also
hits one file, and the one region-level hit sits in 96 bytes of dense binary with no readable
neighbours in a 15.9 MB file that contains no `.ee` or `entities/` string at all. So the region
claim holds — but only because the control I ran exists; the md's §4 says "No shipped *region*
level places the donor" without one, and never mentions `FC21B7E3` or `.fl`.

**Verdict: HOLDS**, with the caveat that three hash-only carriers exist and the report should
record the control (29/86) and the coincidence measurement rather than leaving the claim as a
bare absence.

---

## A11 — the census boundary: "none of the 70,201 unread files is a data table"

**Assumption (stated §1, and MODLOG "UNKNOWN / limits"):** what was not read is media and
navmesh, so nothing that could hold a spawn site was skipped.

**Test 1 — what is actually in the unread set.** Extension census over all 81,952 index rows:

```
outside scan, by count:
  .wavc 31001   .ban 12554   .hmddsc 8296   .streampatch 5600   .rbm 3105
  .nl 2771      .navmeshc 2631   .ddsc 1687   .fl 1326   .bikc 228   .lod 196 …
also outside the tier list: .missionsc 4, .collectionc 5, .restartpointsc 4, .environc 9,
  .roadgraphc 7, .routec 1, .world 2, .pfic 61, .obc 11, .gfx 59, .fmod_guids 54, .terrainsystemc 2
the five extensions the md names (.hmddsc, .nl, .bank, .streampatch, .bikc) total 16,949 rows, not 70,201
```

**Test 2 — scan them.** Every unread type that is not obviously media (1,643 files / 1,845.7 MB),
plus all 702 `graphs/` entries, plus `.missionsc` / `.collectionc` / `.restartpointsc` / `.environc`
/ `.routec` / `.world` / `.pfic` / `.obc` separately:

```
uncovered non-media: 1643 files 1845.7 MB
scanned 1643 files in 12s (errors 0); hits: 2   (both the .fl path hash — noise, see A10)
graphs/ scan: 702 files -> graph hits: 0
.missionsc 4 files, donor hits 0    .collectionc 5 files, 0    .restartpointsc 4 files, 0
.environc 9 files, 0                .routec 1 file, 0          .world 2 files, 0
.pfic 61 files, 0                   .obc 11 files, 0
graphs/mission/mm320/train_test.gsc (36583 B): name False, prefix False, 'v0300' False, 'VehicleRule' False
```

**Result.** The conclusion survives — no unread type names the donor — but the justification as
written is wrong twice: the unread set is not "media and navmesh types" (it contains
`.missionsc`, `.collectionc`, `.restartpointsc`, `.environc`, `.roadgraphc`, `.routec`, `.world`,
`.pfic`, `.obc`, `.fl`, `.fmod_guids`), and the five extensions the md enumerates do not add up to
the 70,201 files it quotes. The md's reasoning was correct only by luck; the empirical check now
backs it.

**Verdict: WEAK (reasoning), HOLDS (conclusion).**

---

## A12 — "one Rebel Drop item … so it is droppable by the player"

**Test.** How many of the 86 ground-vehicle names appear in `profile/item.onlinec`.

```
profile/item.onlinec [base] 52165 B: 85 of the 86 ground-vehicle names appear
     donor name occurrences: 4 ; '_desc' variant: True
profile/item.onlinec [patch] 52204 B: 85 of the 86 …
```

**Result.** The donor's entry (with `v0300_car_kensington_sportsmuscle_civilian_01_desc`) is real,
but so is an entry for 85 of the 86 ground vehicles, including every `_z80` build — `item.onlinec`
is the vehicle catalogue, not a site specific to this car. Listing it as a *spawn site* is
defensible (it is where the drop menu finds the vehicle); reading it as evidence that this
particular car is droppable "so" (implying something special) is not, and it does not distinguish
the donor from any other ground vehicle.

**Verdict: WEAK** as a distinguishing spawn site; the row itself is accurate.

---

## A13 — "one chop-shop task key"

**Test.** Count table names in `profile/task.onlinec` and list the donor's keys.

```
profile/task.onlinec [patch]: 54 of 86 vehicle names appear
  donor keys: ['chopshop_v0300_car_kensington_sportsmuscle_civilian_01',
               'v0300_car_kensington_sportsmuscle_civilian_01']
```

**Result.** Only 54 of 86 vehicles have task entries, and the donor's is the named `chopshop_…`
key — specific, correctly quoted, and it is a real second spawn site (a chop-shop spawns the car
for the player).

**Verdict: HOLDS.**

---

## A14 — "the registry / `.epe` / `.stringlookup` / `patchmetadata.bin` are not spawn sites"

**Test.** Verify the hash the census searches and how it relates to the localisation files.

```
jenkins(name) = D2B46B49          <- the value the census searches for
jenkins(path) = FC21B7E3
jenkins(dir)  = 41CE33AE
md says name hash D2B46B49
```

**Result.** The census's hash is the **name** hash, which is exactly what a `.stringlookup` keys
localised names on — so its appearance there is expected, not "may be a coincidence" as §1 hedges.
`patchmetadata.bin` listing the file, the entity registry listing every entity, and the `.epe`
being the entity's own effect/prefab payload are all correctly excluded.

**Verdict: HOLDS.** Minor: replace "hash only (may be a coincidence)" in the `.stringlookup` rows
with "the name hash — this is a localisation key, expected"; the hedge is the only place the md
under-claims.

---

## A15 — "two level `CVehicleRule` objects … `CVehicleRule` + `point.stunt` + the donor name"

**Test.** Full string dump of the small one (44 strings).

```
      125 'PPPCGraphScriptGameObject'
      194 'graphs/mission/mm320/train_test.gsr'
     1336 'point.stunt point.stunt.hood'
     1396 'CVehicleRule'
     1448 'v0300_car_kensington_sportsmuscle_civilian_01'
     2264 'Point-of-Interest'
  contains 'point': True   'stunt': True   'VehicleRule': True
  contains 'Driver': False 'ai/bts': False 'character': False
```

**Result.** All three evidence strings are present, in that order, and the object is a
`CVehicleRule` inside a level logic object — not a spawn table, and the file carries no driver or
bts string, so nothing in it says the rule drives the car. The md already calls the runtime effect
`UNKNOWN` for these two; that is the right call.

**Verdict: HOLDS** (as a reference, not as a driving carrier).

---

## A16 — the card's "Mario's house"

**Assumption (silent):** the coverage claim satisfies the card's wording even though the md never
mentions Mario.

**Test.** The Mario mission content lives in the region mission `.blo`s (`mm150`), all inside my
region scan; and every mission graph is inside the `graphs/` scan.

```
locations/region_*/missions/mm150/*.blo     (inside the 951-file region scan: donor 0 hits)
graphs/ 702 files                            donor hits: 0
.missionsc 4 files                           donor hits: 0
```

**Result.** Nothing under a mission names the donor, Mario's or otherwise. The card's fourth
example is answered by the census; the md should say so explicitly rather than leaving the word
"missions" to be inferred from a table row.

**Verdict: HOLDS.**

---

## A17 — MODLOG: "the six numeric fields of a spawn record (weights? offsets?)"

**Test.** Compare the two records of the claim.

```
TRAFFIC.md §2: "The record layout beyond its three strings is not decoded here."
TRAFFIC.md §2: "the file's numeric block is not decoded, only its strings"
MODLOG (UNKNOWN / limits): "The six numeric fields of a spawn record (weights? offsets?) are not decoded"
--check output:  no field of this kind is tested
TRAFFIC.json:    no numeric-field structure recorded
```

**Result.** "Six numeric fields" appears nowhere in the generated md or json and no probe measures
a field count; the donor's neighbourhood shows three unprintable runs (`'~iT?['`, `'Pff'`,
`' @ff'`) of unknown width. The number is an unsupported assertion introduced only in the log.

**Verdict: BROKEN.** Either delete it or record the actual byte layout a probe shows.

---

## A18 — "replacing `civilian_01` puts NPC-driven Batmobiles in traffic" (the D-6 conclusion)

**Assumptions (silent):**
(a) a dropzone override of the entity file at the same path is loaded, keeping the record valid;
(b) the replacement is still drivable by whatever AI the engine attaches;
(c) the record's *chassis* directory (and therefore its `modules/`) is the vanilla one.

**Test.** The record references the entity by **path string**, and the modules live in the chassis
directory beside the `.ee`:

```
record path : editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_civilian_01.ee
modules     : …/v0300_car_kensington_sportsmuscle/modules/default/{ai/…_land_global_ai, …_land_engine, …_land_global}.vmodc
.ee strings referencing "modules/" or ".vmodc": 0
```

**Result.** (c) holds — a same-path `.ee` override leaves the chassis directory and its modules
alone, so the spawn table needs no edit and (a) is not even needed for the table to stay valid.
But (a) is exactly the unproven step: nothing in the archives shows that a dropzone `.ee` at a
vanilla path is honoured without a registry/hash change — the md itself defers that to G2-27. And
(b) is untested: the wheel module that would drive the AI Batmobile belongs to the *sports muscle*
chassis (A5), and a Batmobile replacement whose wheels/steering differ has no evidence of matching
it. So the chain "replace → record still selects it → AI drives the replacement" has one proven
link, one inherited unknown and one untested link.

**Verdict: WEAK.** The recommendation (standalone route, D-6) is still the safe read — it is the
option that needs neither (a) nor (b) — but the sentence "replacing it puts NPC-driven Batmobiles
on the roads" should be "would put them there if the dropzone `.ee` override loads, which G2-27
has not shown".

---

## A19 — the census headline (17 of 11,751) reproduces

**Test.** The project's own verifier, with no edits on disk:

```
$ python Tools/scripts/jc3traffic.py --check
PASS: 11751 files scanned (7719 MB, A+B), 17 name the donor (Rebel Drop/entity registry/frontend/level
rule/localisation/other/patch metadata/self/spawn table/task table), 86 spawn records (8 with a pool
key), donor tag list of 13 tags, 31 traffic rules / 41 selectors, 1 match
(`ambient,ground,car,liberated,-highend`), 10 AI behaviour trees
```

**Result.** The census, the record count, the tag list, the selector count, the match and the bts
count all reproduce from the archives, and `--check` compares the regenerated md and json
byte-for-byte rather than trusting a cached number. Independent re-derivation in this review
agrees on every one of those figures (A2, A3, A9, A6, A15).

**Verdict: HOLDS.**

---

## What this changes

* **Keep:** the record (A2), the tag list (A2), the single civilian-car selector match (A3), the
  "only `civilian_01` in the ground table" split (A6), the tag census (A9), the chop-shop key
  (A13), and the absence of any level placement (A10 — now with the 29-of-86 control that makes it
  an argument rather than an absence).
* **Rewrite:** the AI paragraph of §6 and the matching MODLOG sentence. The `Driver`/bts evidence
  belongs to the tank rule (A4), and the `/ai/` module is the wheel module under another name (A5).
  The honest form is: "the file defines civilian-car rules with character drivers; whether a
  selected record is driven by an NPC, and by which tree, is native and `UNKNOWN`". The lore-break
  conclusion does not need the AI paragraph — a record in the ground-vehicle pool with `ambient`
  and `liberated` is enough to make D-6's standalone route the safe choice.
* **Fix the small falsities:** "in the same record" for pool keys (A7), "each record" for the
  tag list (A8), "none is a data table" for the unread set (A11), "so it is droppable" for the
  drop catalogue (A12), "may be a coincidence" for the localisation hash (A14), and "six numeric
  fields" in the MODLOG (A17).
* **Add one control to `jc3traffic.py`:** count how many of the table's own names appear in
  `locations/region_*` (29 of 86, up to 229 files) so the "no level places the donor" claim is
  published with its positive control, and search `FC21B7E3` (path hash) alongside `D2B46B49`
  (name hash) so the hash-only rows are a census and not a spot check.
