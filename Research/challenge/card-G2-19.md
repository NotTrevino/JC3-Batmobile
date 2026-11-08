# Assumption challenge — card G2-19 · Driver seat and pose

Written 2026-10-30. Read-only review: nothing in `GRAB_BACKLOG.md`, `MODLOG.md`, `Research/`,
`Tools/` or any game file was modified; the only file written is this one. No game was launched,
nothing was written to `D:\Games`, nothing was committed, no secrets read or echoed. The reader's
own cache under `E:\Modding\_JC3grab\wiring\epe\` gained decoded `.xml` files as a side effect of
`jc3wiring.decode_epe` / `jc3hkx` — that is the documented cache location (R10), not a project file.

**In scope:** `GRAB_BACKLOG.md` §0.5 (R1–R14), the G2-19 card (line 682), the §12 row (line 1302),
`MODLOG.md` §"G2-19 · Driver seat and pose — intended change" (11453) and §"— done" (11547), and
the outputs: `Research/JC3Grab/SEAT.md` (205 lines), `SEAT.json`, `Tools/scripts/jc3seat.py`
(557 lines).

**Card as written:** "find where the driver attach transform and the driver pose/animation set are
chosen; list the pose sets that exist for cars (sports, truck, tank hatch, bike…) and their seat
heights. Done: the member(s) that place Rico and choose his pose are named, with a candidate pose
that fits the Batmobile's `Driver` socket height (G1-19)."

**Method.** The card's reader was re-run (`--check`, PASS), then its claims were attacked with
probes it did not run: a scan of **all 32,224 member paths in all 232 decoded vehicle entities** (not
the donor's 31 modules), a census of every `.epe`'s `CInteractionComponentSetNode` (the class the
card never names), a per-shape hull dump for the candidate seat, and seat-hull measurements on seven
chassis instead of the card's two cars. The two `rico_base` files were re-read from the archives to
check which file the counts actually come from.

---

## VERDICT

**The attach/pose split is wrong in the direction the card did not look.** The vehicle entity
*does* name the seated character state — `CInteractionComponentSetNode.state = S_IDLE_DRIVER_VEHICLE`,
pointing at `point.driver`, in 224 of 284 vehicle graphs — and the card's name-filtered census
("34 driver-named objects") drops exactly those objects. The sentence "the car does not own the
pose" and §5's "nothing the mod can edit on the car chooses the seated clip" are false as written.

**The candidate pose's number is an artefact.** The "0.855 m vs the 0.865 m hip, 10 mm" comparison
puts a *whole-seat* collision hull's midpoint (a single 0.98 m-tall polytope spanning y 0.363–1.347,
floor to headrest) against a hip joint. The same construction on the hothatch gives a top within
4 mm of the sports car's, and a bike seat that is measured cushion-sized (0.303 m tall) shows the
boxes are not built to a convention at all. Across seven chassis the hull centres run 0.679 → 1.536 m,
so "JC3's car seats ship at one height whatever the class" is a two-car sample presented as a rule.

**What survives:** the index counting (0 vehicle state machines, 0 vehicle skeletons, 142
state-machine files, 7 vehicle `.ban`), the "no character module" sweep, the v0201 hatch reading, the
v0401 no-hull finding, and the 34-name census as a count. The gate passes and the md/json agree.

```
$ python Tools/scripts/jc3seat.py --check
PASS: 34 driver points | 40 pose classes (382 clip names) | 36 MOD selectors | seat boxes 4 |
candidate v0300_car_kensington_sportsmuscle (10 mm from the hip), json match True, md match True
EXIT=0
```

| # | Assumption the result rests on | Verdict |
|---|---|---|
| A1 | "**the car does not own the pose**"; "the pose half is not a vehicle member" | **BROKEN** — `CInteractionComponentSetNode.state = S_IDLE_DRIVER_VEHICLE`, 224 entities |
| A2 | "`entry.driver` … places Rico" | **BROKEN** — its transform is 0,0,0 inherited; 29 of 34 rows place nothing |
| A3 | seat height = hull **centre** (0.855 m, 10 mm from the hip) | **BROKEN** — centre of a 0.98 m whole-seat box is mid-back, not the cushion |
| A4 | "car seats ship at one height whatever the class" (39 mm span) | **BROKEN** — 3 parts in 2 cars; 7-chassis span is 0.86 m |
| A5 | "40 vehicle classes, 382 seated clips" | **WEAK/BROKEN** — 9 top-level types, 40 folders, 383 clips, and a third are not seated |
| A6 | "36 `MOD_*` class selectors … out of `afsmb`'s string table" | **BROKEN** — the strings are in the `.asb`; 34 real suffixes, 2 contaminated, ~14 not classes |
| A7 | "34 driver-named objects, prefix census" | **HOLDS as a count**; **WEAK** as "what places Rico" |
| A8 | 0 vehicle state machines, 0 vehicle skeletons, 142 / 3 / 7 / 2 file counts | **HOLDS** |
| A9 | "no seat/occupant/pose/animation module"; 52 module types | **HOLDS** (53 types incl. the empty one; `DriverLean` is physics, not pose) |
| A10 | "no file maps an entity to `car/low|med|circuit`; the class is native" | **WEAK** — holds for 32,224 member paths, unproven for the other 81,952 index entries |
| A11 | `v0401`'s seat has no hull; indices 19/22 not carried | **HOLDS** (42 vs 43 counting caveat) |
| A12 | `v0201` has no seat part; `mediumtank_hatch` is part 39 `Land_Door` | **HOLDS** |
| A13 | the Done clause: "a candidate pose that fits the `Driver` socket height" | **BROKEN** — rests on A3 + A4 |
| A14 | the gate: `--check` PASS, md/json match | **HOLDS** (re-run, exit 0) |

---

## A1 · "The car does not own the pose" / "the pose half is not a vehicle member" → BROKEN

This is the report's thesis (§ opening line, §5). The vehicle graph has a class the card never
names, and it carries a character *state*:

```
$ python -c '... parse v0300_car_kensington_sportsmuscle_civilian_01.ee.xml ...'
set nodes: [('set.node.npc', 'CInteractionComponentSetNode', '29F9EE52=FFFFF1B6'),
            ('set.node.player', 'CInteractionComponentSetNode', '3BBFCDD6=FFFFF7DB'), ... x3 pairs]
== set.node.player CInteractionComponentSetNode
    node  = 93F2612B=FFFF52D5 -> CInteractionGraphPointNode point.driver
    state = S_IDLE_DRIVER_VEHICLE
== set.node.npc CInteractionComponentSetNode
    node  = 93F2612B=FFFF52D5 -> CInteractionGraphPointNode point.driver
    state = S_IDLE_DRIVER_VEHICLE
```

Every vehicle carries these pairs (one player, one npc, per seat node) and the state name is a
character state that exists in Rico's machine:

```
$ python -c 'S_IDLE_DRIVER_VEHICLE in rico_base.afsmb strings'
S_IDLE_DRIVER_VEHICLE True     S_IDLE_PASSENGER_VEHICLE True     S_IDLE True
```

Fleet census over every cached vehicle graph:

```
vehicle epe files now: 284
vehicles naming S_IDLE_DRIVER_VEHICLE: 224
distinct set-node states: 10
   S_IDLE 488 | S_IDLE_DRIVER_VEHICLE 450 | S_IDLE_PASSENGER_VEHICLE 399
   S_SLOW_RIDING_MOTORBIKE 58 | S_VEHICLE_FIXED_MOUNTED_WEAPON 32 | S_DRIVER_SIDE_TO_HANG_VEHICLE 28 …
```

So the vehicle *does* choose a pose state: it names the seated idle state on the node that the
entry/exit objects hang from. What the vehicle does **not** name is which clip variant inside that
state plays (`MOD_LOW` / `MOD_MED` / `MOD_CIRCUIT`) — that part of the card's UNKNOWN stands. But
"the pose half is not a vehicle member" is refuted by a member in 224 entities, and the card's own
census filter is why it was missed: `points_of()` keeps rows whose **name** contains "driver"
(`set.node.player` / `set.node.npc` do not), so the six objects that carry the state were silently
dropped from the "34".

**Why it matters for the mod.** §5 tells the builder that nothing on the car matters for the pose and
only a phase-Q look can settle it. In fact the Batmobile can carry the same `set.node` pair with
`S_IDLE_DRIVER_VEHICLE` — i.e. the state (not the clip) is a copyable vehicle member, exactly the
kind of thing T-13 needs.

## A2 · "`entry.driver` … places Rico" → BROKEN (placed by the point nodes, not the entry)

The md's answer table says `entry.driver` "places Rico". Its own row shows `0.000, 0.000, 0.000`
"n/a (container origin)". The census of transform provenance:

```
world_source: Counter({'inherited': 29, 'own': 5})
verdict:      Counter({'inside': 16, 'n/a (container origin)': 11, 'floating': 7})
entry.driver         serpente [0.0, 0.0, 0.0]      batmobile [0.0005, 0.091, 0.1154]  inherited
point.driver         serpente [-0.44, 0.34, 0.2]   batmobile [-0.5776, 0.5976, 0.3916]  own
point.driver.side    serpente [-0.26, 1.47, 0.37]  batmobile …                          own
```

`entry.driver` has no transform of its own and sits at the container origin; 29 of the 34 rows
inherit theirs. The only placement data is the five `own` transforms, all of them `point.*` nodes.
"The interaction graph places Rico" is right; "`entry.driver` places Rico" is wrong, and the md's
table already shows it — the prose contradicts the table.

## A3 · "seat height = hull centre, 0.855 m, 10 mm from the hip" → BROKEN

The candidate's number is the midpoint of a single convex polytope that spans the whole seat. Per-shape
dump (not the merged box the script prints):

```
part 4 shape hknpConvexPolytopeShape min [-0.7207, 0.3632, -0.2089] max [-0.1602, 1.3469, 0.5955]
                     size [0.5605, 0.9837, 0.8044]      (v0300, sportsmuscle_f_l_seat)
```

0.98 m tall from 0.363 to 1.347 — that is floor-to-headrest, not a cushion. Its midpoint 0.855 is
mid-back. The card's rule ("A hull is a part's whole envelope (cushion to headrest for a seat), so
its **centre** is the comparison quantity, not its top") is asserted, not argued, and the geometry
says the opposite: a hip sits just above the cushion, near the *bottom* of such an envelope. The
Batmobile's own cockpit numbers make the gap explicit — hip 0.8647, **cushion top 0.8407** (COCKPIT.md,
parsed by the script as `cushion_top_m` and then never used): the hip is 24 mm above the cushion. A
car whose hull centre is 0.855 therefore has its cushion roughly 0.4 m below the Batmobile's hip.

The convention is not even consistent between parts, which is the giveaway:

```
v3503 oldroad_seat   Land_Seat  min_y 0.637 max_y 0.940  size 0.303  (cushion-sized)
v0003 hothatch_seats Land_Seat  min_y 0.445 max_y 1.343  size 0.898  (whole seat)
v0300 f_l_seat       Land_Seat  min_y 0.363 max_y 1.347  size 0.984  (whole seat)
```

The two cars' box *tops* are 1.3469 and 1.3433 — within 4 mm across two unrelated cars — while their
bottoms differ by 82 mm. So the top is a fixed line (headrest/roof), and the midpoint mostly encodes
that line. The 10 mm agreement with the Batmobile hip is an artefact of that constant, not a fit.

## A4 · "the 3 `Land_Seat` parts sit at 0.855/0.855/0.894 … JC3's car seats ship at one height whatever the class" → BROKEN

The claim is measured on 2 cars. The fleet carries far more seat parts, and seven chassis measured
the same way spread over 0.86 m:

```
part                           class        min_y   max_y   centre    size_y
v0300 sportsmuscle_f_l_seat    Land_Seat    0.363   1.347   0.855     0.984
v0300 sportsmuscle_f_r_seat    Land_Seat    0.363   1.347   0.855     0.984
v0003 racinghothatch_seats     Land_Seat    0.445   1.343   0.894     0.898
v0505 oldtruck_seats           Land_Seat    1.121   1.950   1.536     0.829
v0006 modernbus_seats          Land_Seat    0.669   2.157   1.413     1.488
v3503 oldroad_seat             Land_Seat    0.637   0.940   0.788     0.303
v1401 racingboat_seat_f_l      Boat_Seat    0.106   1.253   0.679     1.147
v4600 privatepropeller_seat_cl1 Plane_Seat 0.762   1.886   1.324     1.124
```

Fleet census of the parts: `{'Land_Seat': 128, 'Plane_Seat': 4, 'Boat_Seat': 26}` across 31 + 1 + 5
chassis. The card measured 3 of the 128 `Land_Seat` parts. "One height whatever the class" is false:
the truck is 0.68 m above the muscle car; the bus and the private plane are 0.42–0.47 m above it.

## A5 · "40 vehicle classes, 382 seated clip paths" → WEAK/BROKEN

Three separate problems, all reproducible from the same `.asb` string table:

```
unique vehicle clip paths: 383      (SEAT.json says 382)
top-level dirs: {'bike': 201, 'car': 73, 'boat': 33, 'helicopter': 28, 'plane': 17,
                 'tractor': 10, 'tank': 10, 'bus': 8, 'stunt': 2, + rico_vehi_crawl_out.ban}
clip leaf keywords over the 383: drive 105 | geton/getoff/enter/exit/rollout/reel/hijack 113 |
                                 idle 22 | aim 33 | additive (add_larm/add_head/…) rest
```

- **40 is a folder count, not a class count.** `clip_families()` keys on the path under
  `rico/vehicle/`, so `bike/fast/larm`, `bike/add/head` and `car/med` are peers. There are **9**
  top-level vehicle types; `car` has 73 clips in 5 folders (2 + 9 + 4 + 23 + 35).
- **382 vs 383.** A clip that sits directly under `vehicle/` — `rico_vehi_crawl_out.ban` — has
  `len(parts) == 1` and is dropped by the `if len(parts) < 2: continue` branch. The missing clip is
  a vehicle *exit* clip, the one family the card's pose question cares about.
- **"Seated"** is not what the 382 are: at least 113 are get-on/get-off/enter/exit/rollout/reel/hijack
  clips and 105 drive clips. Calling them "382 seated clip paths" in the answer table overstates what
  the list is (all Rico vehicle clips).

## A6 · "36 `MOD_*` class selectors … straight out of its [afsmb's] string table" → BROKEN

The two `rico_base` files were re-read and the strings attributed per file:

```
rico_base.afsmb   strings 1665   containing MOD_: 5   (PMOD_SAMPLER_0, MOD_SAMPLER_1..3, PMOD_PARACHUTING)
                  ANIM_ strings: 0    VEHICLE_MOD strings: 0    S_*VEHICLE strings: 183
rico_base.asb     strings 9723   VEHICLE_MOD strings: 295   ANIM_ strings 2482
                  e.g. ANIM_DRIVER_SIDE_ENTER_VEHICLE_MOD_TANK, ANIM_IDLE_DRIVER_VEHICLE_MOD_JETSKI
```

So the "class selectors" are **`.asb` animation-name suffixes**, not `afsmb` state-machine members.
The §2 table ("The names that matter, straight out of its string table", listing `MOD_*` under
`rico_base.afsmb`) attributes them to the wrong file — the script itself concatenates
`afsmb + asb` before counting, which is why the numbers are right and the file is wrong.

The count is also contaminated:

```
distinct VEHICLE_MOD_ suffixes: 34
['ATV','BIKE','BOAT','BOAT_CABIN','BOAT_FORWARD','BOAT_PATROL','BOAT_SPY','BUS','BUTTON','CARGO',
 'CAR_ENTER_MOUNTED_WEAPON_FROM_STATIONARY_STUNT','CAR_EXIT_MOUNTED_WEAPON','CIRCUIT','CIRCUIT_RIGHT',
 'HELI','HELI_ASSAULT','HELI_ASSAULT_RIGHT','HELI_EXIT_FALL','HIGH','JET','JETSKI','JET_BEHIND','LOW',
 'LOW_RIGHT','MED','MINE','REAR_MOUNTED','RIGHT','SPORTBIKE','TANK','TANK_EXIT_FALL','TRACTOR',
 'TRACTOR_RIGHT','VAN']
script's set: 36  (adds BACK, CAR_MOUNTED_WEAPON_PARA via a second regex)
```

`BACK` and `CAR_MOUNTED_WEAPON_PARA` are not `VEHICLE_MOD_` suffixes at all; and `RIGHT`, `LOW_RIGHT`,
`CIRCUIT_RIGHT`, `HELI_ASSAULT_RIGHT`, `TRACTOR_RIGHT`, `JET_BEHIND`, `TANK_EXIT_FALL`,
`HELI_EXIT_FALL`, `CAR_EXIT_MOUNTED_WEAPON`, `BUTTON`, `MINE`, `REAR_MOUNTED` are direction/exit/mount
variants. The number of *vehicle classes* in that list is about 20, not 36; the md's "36 class
selectors" with `ATV, BACK, BIKE, BOAT, BOAT_CABIN` as examples shows the mixture.

## A7 · "34 driver-named objects" → HOLDS as a count, WEAK as "the member(s) that place Rico"

The count is exactly what `points_of()` computes (`"driver" in name.lower()`), and it reproduces:
`{'entry': 10, 'exit': 14, 'interaction': 1, 'point': 3, 'transition': 4, 'trigger': 2} = 34`. But as
the answer to "what places Rico" it is both too wide and too narrow:

- too wide: 29 of the 34 have `world_source: inherited` and contribute no transform (A2);
- too narrow: the same `.epe` has 37 objects whose name **or state** names the driver, including the
  six `CInteractionComponentSetNode` objects that carry `S_IDLE_DRIVER_VEHICLE` (A1).

A name-substring filter is the R5 failure mode this rule exists to catch: the member that matters
is found by what it *does* (`node → point.driver`, `state → S_IDLE_DRIVER_VEHICLE`), not by having
"driver" in its name.

## A8 · The index counts → HOLDS

Re-derived from `INDEX.jsonl` (81,952 entries):

```
jc_statemachine/vehicles/   0       jc_skeletons/vehicles/  0
jc_statemachine/            142     jc_skeletons/           3   (.bsk: 1, gen_male.bsk)
vehicle .ban                7       rico/vehicle .ban       2   (both mech/)
state-machine dirs: npc 124, main_characters 9, animals 7, aero 2
```

Every number in the card's "what the card's In list promises" row and in the MODLOG is exact. The
only wording slip: `SEAT.md` says "3 skeleton files in total" (files under `jc_skeletons/`) while the
MODLOG's intended-change says "exactly one `.bsk`" — both true, different units.

## A9 · "A JC3 vehicle entity has no seat, occupant, pose or animation module"; "52 module types" → HOLDS

Scan of all 232 decoded entity JSONs, by module type and by member path (32,224 distinct paths):

```
distinct module types: 53 (52 non-empty + one '')
module types matching seat|occupant|driver|anim|pose|character|skeleton|attach:
   EffectAttachments, ExtendedExposedVariables, DriverLean
member paths matching: add_drivers_mass, driver_center_of_mass[0..2],
   motorbike_common.animation_max_roll_error_deg, motorbike_common.animation_roll_pid_{p,i,d},
   motorbike_common.roll_to_fall_{with,no}_driver_deg
```

No module or member chooses a character pose or a seated clip. Two caveats worth one line each in
the md: `DriverLean` **is** a driver module (23 boat/jetski entities: `max_lean_angle_deg` 30,
`leaning_torque` 5000 — vehicle physics, not the character), and every vehicle carries
`driver_center_of_mass` (0, 0.5, 0) in `RigidBody`. So "none about a character" is correct; "the
vehicle says nothing about the driver" would not be.

## A10 · "no file maps `v0300` (or any entity) to `car/low`, `car/med` or `car/circuit`" → WEAK (bounded search)

What was actually searched: the 232 decoded vehicle entities (all module types and every member
path) plus the two `rico_base` files. Results:

```
paths containing 'class'               0 of 32,224
rows whose value is a pose-class name  0   (LOW / MED / HIGH / CIRCUIT / SPORTBIKE / ATV / JETSKI / TANK …)
sportsmuscle | kensington | v0300 | v0401 | hothatch | mediumtank  in afsmb: 0 each; in asb: 0 each
```

That is good evidence for the negative where it was looked. It is not the whole archive: the index
has 81,952 entries and the claim is "no file in the index". A vehicle-class table could live in a
`profile/`, `ai/`, `physics/` or DLC file that no G2 card has decoded. The md should say "no member
of a vehicle entity or of Rico's two animation files maps an entity to a pose class", which is what
was proven, and keep "the class is native" as the inference it is.

## A11 · "`v0401`'s `racingsupercar_seats` … no compound instance carries its index (19 or 22)" → HOLDS

Full compound sweep of `racingsupercar.physicsc`:

```
compound objects: 20   instances: 114   distinct part indices carried: 43 (42 ints + None)
19 in carried: False    22 in carried: False
parts: 19 = racingsupercar_seats (Land_Seat), 22 = racingsupercar_steeringwheel (Land_Steering_Wheel)
```

The seat and the steering wheel are the two decorative parts with no collision hull. The card's
"42 carried indices" is 43 counting a `None`; harmless, but the number in the md is one short.

## A12 · "`v0201` has no seat part at all; `mediumtank_hatch` is part 39 `Land_Door`" → HOLDS

```
v0201 parts 42; parts whose name has 'hatch' or whose class ends 'Seat':
  [(39, 'mediumtank_hatch', 'Land_Door')]
```

One driver-ish part, a door. The tank's seat height stays UNKNOWN, as the md says. (The table's
"+2014 mm" line is deliberately labelled a door roof, so it is not a false number — just noise.)

## A13 · The Done clause — "a candidate pose that fits the `Driver` socket height" → BROKEN

The clause rests entirely on A3 and A4: `SEAT.json.candidate.nearest` is
`{"vehicle": "v0300_car_kensington_sportsmuscle", "part": "sportsmuscle_f_l_seat",
"seat_y_m": 0.8551, "delta_m": 0.0096}` against `hip_y_m 0.864732`. Given that (a) 0.8551 is the
midpoint of a 0.98 m whole-seat envelope and (b) the "one height" premise fails across the fleet,
the 10 mm is not evidence of fit and the candidate is a name that happened to land near the hip.
The honest output is: the fleet's seat envelopes differ by class and body style (0.679–1.536 m hull
centres; cushion-sized parts exist only on some vehicles), the only vehicle-independent quantity the
data supports is the *state* (`S_IDLE_DRIVER_VEHICLE`, A1), and the Batmobile's hip needs a cushion,
not a hull centre.

## A14 · The gate → HOLDS

`python Tools/scripts/jc3seat.py --check` re-derived both files from the archives and printed
`PASS … json match True, md match True`, exit 0. Note what the gate can and cannot catch: every
number in the md is generated, so a *wrong method* (A3's hull centre, A6's file attribution, A1's
name filter) passes forever. The five sentences that carry the answer — "the car does not own the
pose", "`entry.driver` places Rico", "hull centre is the comparison quantity", "40 vehicle classes",
"382 seated clips" — are template prose that no assertion tests.

---

## What should change

1. **Add the state carrier.** `CInteractionComponentSetNode` (`set.node.player` / `set.node.npc`):
   `node → point.driver`, `state = S_IDLE_DRIVER_VEHICLE`; 224/284 vehicle graphs. It belongs in the
   answer table and in `SEAT.json`, and it changes §5 ("nothing the mod can edit chooses the pose")
   and the T-13 hand-off. The fleet's 10 set-node states are worth a table.
2. **Fix "places Rico".** `entry.driver` carries no transform; the point nodes do
   (`point.driver` −0.440, 0.340, 0.200; `point.driver.side` −0.260, 1.470, 0.370). Say so, and use
   the Batmobile-space conversion (0.598 m for `point.driver`) next to the hip 0.865 m.
3. **Drop the hull-centre convention or justify it with the cushion.** The v0300 seat is one 0.98 m
   polytope; the bike's is 0.30 m. If a height is quoted, quote the minimum (cushion base) and mark
   the cushion top as UNKNOWN, or restrict the claim to "no shipped seat part measures a cushion".
4. **Withdraw "one height whatever the class".** Replace with the 7-chassis span (0.679–1.536 m) and
   the note that 128 `Land_Seat` parts exist in 31 chassis; the card read 3.
5. **Correct the clip census.** 383 paths (the crawl-out clip is dropped), 9 top-level types, 40
   folder keys, and describe them as "vehicle clips", not "seated clips".
6. **Move the `MOD_*` numbers to the `.asb` and to 34 suffixes**, separating classes from
   `RIGHT`/`_EXIT_FALL`/`_MOUNTED_WEAPON` variants.
7. **Bound A10's negative** to what was searched (vehicle entities + the two Rico files).
8. **Make the prose assertions data.** Every sentence in 1–6 should be in `SEAT.json`, so `--check`
   fails when the data moves (R4/R11).

**Reproduce.** Probes read `Research/JC3Grab/{INDEX.jsonl,SEAT.json,INTERACTION.json,PARTS_TABLE.jsonl}`,
`Research/BatmobileGrab/SOCKETS_JC3.json` + `COCKPIT.md`, the cached graphs in
`E:\Modding\_JC3grab\wiring\epe\*.xml`, the 232 JSONs in `E:\Modding\_JC3grab\entities\`, and — through
`jc3grab.read_entry` only — `rico_base.afsmb`, `rico_base.asb` and seven `.physicsc` bundles from
`D:\Games`. Nothing was written outside this file.
