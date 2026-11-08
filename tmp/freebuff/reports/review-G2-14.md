# Independent review - G2-14 (Moving-part behaviours: who drives each variable)

Reviewer: independent (did not author the card). Mode: read-only - nothing under
`GRAB_BACKLOG.md`, `MODLOG.md`, `Research/`, `Tools/` or any game path was modified; this file
is the only one written.

Card: `GRAB_BACKLOG.md` §2.3 "G2-14 · Moving-part behaviours ... S · deps: P0-2 · serves: ANI-3…8".
Row: `GRAB_BACKLOG.md:1297` (status `done`).
MODLOG: intended change `MODLOG.md:9703`, done block `MODLOG.md:9724`.

## VERDICT

**needs rework** - narrow and prose-only. Every table, every row count and every derived number
in `MOVING_PARTS.md` checked out against `MOVING_PARTS.json` and the raw data; the generator is
sound and `--check` passes. But one paragraph of the generated doc (`MOVING_PARTS.md:190-192`)
states something the card's own JSON refutes, the same sentence is repeated in the MODLOG done
block (`MODLOG.md:9758`), and the MODLOG additionally misstates a value that the doc prints
correctly (`MODLOG.md:9744`). The cause is typed literals in the doc template (R11), which is
also why `--check` cannot see the error.

## Check output (verbatim)

```
$ python Tools/scripts/jc3moving.py --check
PASS: 67 behaviours, 53 table rows (37 proven on CCar), 224 door rows
exit=0
```

Outputs named in the row all exist:

```
-rw-r--r-- 1 User 197121  89873 Oct 26 22:53 Research/JC3Grab/MOVING_PARTS.json
-rw-r--r-- 1 User 197121  14619 Oct 26 22:53 Research/JC3Grab/MOVING_PARTS.md
-rwxr-xr-x 1 User 197121  22864 Oct 26 22:52 Tools/scripts/jc3moving.py
```

`Research/JC3Grab/README.md` was also updated as the intended-change entry claims (lines 41, 375,
929).

## Issues

### 1. False claim about the six turreted vehicles (must fix)

`Research/JC3Grab/MOVING_PARTS.md:190-192`:

> The Serpente fills only `door_parts` (3 rows) and the APC only `door_parts` (5);
> the six turreted vehicles of G2-13 fill none of the three, because their motion is
> the `.physicsc` hinge or the deform/wheel system, not the arrays.

Repeated at `MODLOG.md:9758` ("the six turreted vehicles fill none of the three").

Why it is wrong: the six turreted vehicles of G2-13 are `v0200` APC, `v0201` medium tank,
`v0202` bavarium tank, `v0504` technical jeep, `v0600` armoured jeep, `v0603` small tank
(G2-13 card text; `TURRET.md` "the six turreted samples"). Their parts modules in
`MOVING_PARTS.json` -> `arrays.modules` carry these `door_parts` row counts:

| module | door_parts | hinged_parts | rotating_parts |
|---|---|---|---|
| `apc_vehicle_parts.vmodc` | 5 | 0 | 0 |
| `mediumtank_vehicle_parts.vmodc` | 1 | 0 | 0 |
| `bavariumtank_vehicle_parts.vmodc` | 1 | 0 | 0 |
| `technicaljeep_vehicle_parts.vmodc` | 4 | 0 | 0 |
| `armoredjeep_vehicle_parts.vmodc` | 5 | 0 | 0 |
| `smalltank_vehicle_parts.vmodc` | 1 | 0 | 0 |

So all six fill `door_parts`, and the APC is itself one of the six - the sentence contradicts
its own preceding clause ("the APC only `door_parts` (5)"). What is true is the weaker claim the
same MODLOG records for G2-13 (`MODLOG.md:9668`: `hinged_parts[]`/`rotating_parts[]`
"both are empty on every tank"): none of the six fills `hinged_parts[]` or `rotating_parts[]`.

Why it matters: a B-05 reader is told the armoured vehicles have no per-part door rows, which is
the opposite of what the JSON says; door hatches on those six are exactly the parts ANI-6/ANI-8
and WLD-3 care about.

Source: `Tools/scripts/jc3moving.py:343-345` - the sentence is a typed template literal, not
rendered from `d["arrays"]`, so `--check` reproduces it byte-for-byte and passes.

### 2. Typed numbers in the doc template (R11)

`Tools/scripts/jc3moving.py` writes these numbers as string literals instead of reading them from
the built dict (all currently correct, which is why `--check` passes):

| literal | line | derivable from |
|---|---|---|
| `29 behaviours` (intro) | 221 | `len(no_table)` |
| `3 rows` / `5 rows` (Serpente / APC) | 343 | module rows for `sportsmuscle` / `apc` |
| `148 hinged rows across 28 modules` | 339 | `arrays.counts` |
| `78 parts modules`, `233` | 358-364 | `len(d["arrays"]["modules"])`, census |
| `15 declared-but-unused`, `12 spider-leg parts` | 360-362 | `source.declared_not_used` |

Issue 1 is the demonstrated cost of this: the literal was simply wrong and nothing could catch
it. Every one of these numbers is currently right (see Spot-checks).

### 3. "split into three kinds" presents a partial taxonomy as complete

`MOVING_PARTS.md:163-170` (template `jc3moving.py:310-316`): "The **29** without one split into
three kinds: ... Havok constraint or physics body (`Turret`, `Cannon`, `Axle`) ... deform and
wheel system (`Wheel`, `Body`, `BrakeDrum`, `BrakeDisc`, `Engine`) ... windows and couplings
(`Windshield`, `FrontWagonCoupling`)".

The 29 no-row behaviours are:
`Wheel, BrakeCalipers, Windshield, BrakeDisc, Engine, FrontLeftWindow, FrontRightWindow,
RearRightWindow, RearWindow, RearLeftWindow, Body, BrakeDrum, Cannon, TrainCargo,
CenterLeftWindow, CenterRightWindow, BavariumShield, Turret, LandingSkid, Tail,
RearWagonCoupling, TailWing, Antenna, Axle, TrimTab, FrontWagonCoupling,
FrontWagonCouplingLinked, Stabilizer, WindshieldWiper`.

Ten of them fit none of the three named kinds: `TrainCargo`, `Tail`, `TailWing`, `Stabilizer`
(train/aero surfaces), `Antenna`, `TrimTab`, `WindshieldWiper`, `BavariumShield`, `LandingSkid`,
`BrakeCalipers`. The count 29 is derived; the taxonomy is not, and it is stated as if exhaustive.
A note like "the rest are surfaces/accessories whose motion is not in `vehicle_common`" wouldfix it. `MODLOG.md:9746-9747` repeats a version of the same list ("turret/cannon, wheel, body, brakes,
engine, windows, couplings"), which covers `BrakeCalipers` but still leaves the aero/accessory
names out.

### 4. MODLOG misstates `rotoscope_rpm_per_cycle`

`MODLOG.md:9740-9741`: "`rotoscope_rpm_per_cycle` (20.0 on every row)". The JSON has two values,
20.0 and 50.0 (`LeftRotor`, `RightRotor`, `Rotor`, `OuterLeftRotor`, `OuterRightRotor` = 50.0;
the doc's own table prints 50.0 for them). The generated doc is right; the hand-written MODLOG
sentence is wrong. (The doc's framing of the member as "the strobe rate for the blade disc, not
the rotor speed" is an interpretation not backed by a decoded definition in any file read here -
the json carries the number, not its meaning. Acceptable as labelled inference, but it should
not harden into fact.)

### 5. "over all 233 vehicles" - the census totals 232

`MOVING_PARTS.md:90` and `:363`: "`parts`/`entities`/`chassis` come from `FEATURE_CENSUS.json`
over all 233 vehicles" / "not all 233". `FEATURE_CENSUS.json` -> `totals.entities` is **232**;
233 is the fleet count from `PARTS_TABLE.jsonl` (used consistently in other G2 docs). The class
lookup reads 232 detail JSONs; one entity
(`.../v4603_plane_urga_cargotransport_military_cargo_tank.ee`) has two root classes (`CCar` and
`CAirPlane`) and is therefore dropped by `root_classes()`. I checked the consequence: all 79
chassis that carry any behaviour do resolve to exactly one class, and that entity's chassis
(`v4603`) resolves via its other entities, so **no proof verdict is affected**. It should still
be in the doc's Limits section, because it is the one place where a silent class-miss could have
turned a `proven-on-CCar` into `unproven-on-CCar`.

### 6. Done criterion vs what `--check` verifies

Done (card): "every behaviour in §2.3 has its member layout and proof column; `AirBrake` on a car
is listed as the only probe (for Q-1) unless a `CCar` user is found."

* Member layout + proof column: structurally guaranteed (the §2 table is rendered from
  `d["behaviours"]`, all 67 rows) and `--check` asserts the layout rules that matter (every
  hinged row has `target_position_variable`, every rotating row `rpm_variable`, door/fin/spring
  rows carry nothing but `name`, every proof follows from the chassis classes). Met.
* `AirBrake`: the doc says "`AirBrake` is the card's named probe - one chassis
  (`v4602_plane_urga_fighterbomber`, `CAirPlane`) and nothing on land" (`MOVING_PARTS.md:174-176`),
  which satisfies "listed as the only probe" only by implication - it never says it is the only
  candidate among the 30 unproven behaviours. `--check` has **no** invariant naming `AirBrake`
  (the `invariants()` "must" list is `Turret, Cannon, Wheel, Body`), so the sentence is protected   against edits only by the byte-comparison, never against the data changing. Weak but not
  untrue: the underlying number is right (`AirBrake` 3 parts / 3 entities / 1 chassis / `CAirPlane`).

## Spot-checks

| # | value in the doc | verified against | result |
|---|---|---|---|
| 1 | `door_parts[]` 224 rows / 56 modules, `part_index` only (`MOVING_PARTS.md:181`) | sum over `MOVING_PARTS.json` -> `arrays.modules`: 224 rows, 56 non-zero modules; member union = `['part_index']` for all 78 modules | match |
| 2 | `hinged_parts[]` 148 rows / 28 modules (`:181`) | same: 148 rows, 28 modules, member union = `['part_index']` only | match |
| 3 | `rotating_parts[]` 47 rows / 22 modules with position/axis/blades/rpm (`:183`) | same: 47 rows, 22 modules, members `position[0..2]`, `rotation_axis[0..2]`, `number_of_blades`, `rpm_multiplier`, `min/max_rpm_visible`, `rpm_opacity_transition` | match |
| 4 | Serpente 3 door rows, APC 5 (`:190`) | `sportsmuscle_vehicle_parts.vmodc` 3, `apc_vehicle_parts.vmodc` 5 | match |
| 5 | Table row counts 14 doors / 25 hinged / 12 rotating / 1 fin / 1 spring (`:7-13`) | `MOVING_PARTS.json` -> `tables[*].rows` lengths | match |
| 6 | `SteeringFork` is the only `use_target_position_as_angle`=1 row (`:55`) | hinged rows with that member = 1: `['SteeringFork']` | match |
| 7 | 38 behaviours have a `vehicle_common` row, 29 do not, 37 proven / 30 unproven (`:165`, `:172`) | computed over `behaviours[]`: 38 / 29 / 37 / 30 | match |
| 8 | `AirBrake` 3 parts, 1 chassis, `CAirPlane`, `v4602_plane_urga_fighterbomber` (`:174`) | `behaviours[AirBrake]`: parts 3, entities 3, chassis 1, classes `['CAirPlane']`, variable `air_brakes_T` | match |
| 9 | `MissileHatch` 16 parts / 1 entity / `CTrain` (`:172` table) | `behaviours[MissileHatch]`: 16 / 1 / `v5603_train_urga_monorailmissilecar` | match |
| 10 | `mediumtank_hatch` is a `FrontLeftDoor` on a 0..130 deg limited hinge (G2-13, `:83-84`) | `Research/JC3Grab/TURRET.md:13` and `:32` | match (citation to G2-13 is correct) |
| 11 | six turreted vehicles "fill none of the three" (`:191`) | `arrays.modules`, table in Issue 1 | **mismatch** - all six fill `door_parts` |
| 12 | `rotoscope_rpm_per_cycle` 20.0 everywhere (`MODLOG.md:9740-9741`) | JSON values {20.0, 50.0} | **mismatch** (MODLOG only; doc prints 50.0 correctly) |

## What holds up

* The card's own probes are answered and the answers are derived, not typed: which channel drives
  a behaviour (hinged variable / rotating variable / name-only / no row), the chassis classes and
  the `CCar` proof, and the per-part array members - the array members are read from the decoded
  module keys, so `part_index`-only for doors and hinged is a measured fact, not an assumption.
* The claim that G2-14's card assumptions might fail ("the per-part arrays carry members (axis,
  angle limits, rpm scale)") is honestly recorded in the intended-change entry and the doc's §3
  answers it with the measured answer (only `rotating_parts[]` has geometry).
* `R5` (name vs behaviour) is handled explicitly: the doc defines `proven-on-CCar` as "at least
  one `CCar` chassis ships a part with that behaviour", and the Limits section says the table
  proves the binding, not the writer. Worth a one-line caveat that for no-row behaviours such as
  `TrimTab` (6 parts, one `v0604_car_urga_buggy`) the string is present on a car while nothing in
  `vehicle_common` states how it moves - otherwise that row reads stronger than it is.
* UNKNOWNs are stated rather than guessed in the places checked (which code writes
  `steering_roll`; the one `vehicle_common` copy having nothing to diff against; array census
  limited to the 78 cached modules).

## Limits of this review

* Read-only, so I did not re-run a tamper test: `--check` compares the on-disk JSON and MD against
  a rebuild, which requires writing to `Research/JC3Grab/` to tamper with. `MODLOG.md:9766`
  records that tampering with `LeftAileron`'s variable produced
  `json section changed: tables` and exit 1, then a rebuild returned PASS - consistent with the
  code I read in `cmd_check()`.
* The doc's interpretation that `rpm_variable` is rpm and `rotoscope_rpm_per_cycle` is a strobe
  rate could not be confirmed against a decoded definition; it is labelled as inference.
* I did not re-derive `FEATURE_CENSUS.json` (P0-2/G2-11 territory); I used its `part_behaviours`
  as the doc does.
