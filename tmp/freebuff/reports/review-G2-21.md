# Independent review - G2-21 (Turn-on-the-spot / tank pivot)

Reviewer: independent (did not author the card). Mode: read-only - `GRAB_BACKLOG.md`, `MODLOG.md`,
`Research/`, `Tools/` and every game path untouched; this file is the only one written. No game
launched, nothing committed.

Card: `GRAB_BACKLOG.md` §2.3 "G2-21 · Turn-on-the-spot (tank pivot) · S · deps: P0-2".
Row: `GRAB_BACKLOG.md:1304` (`done`). MODLOG: intended change `:9956`, done `:10050`.

## VERDICT

**minor issues.** Every table, histogram and count in the doc is reproduced by the script and by
my own independent scan, `--check` has real invariants (not just a text diff), and the card reaches
the right practical outcome for MOD-2 (named omission + a Q-1 probe). Three things are wrong or
overstated:

1. The headline argument is a **non sequitur**: "the four modules carry byte-identical member sets
   … so no tuned value in them can switch a neutral turn on". Identical *member sets* say nothing
   about *values* - and the doc's own table shows the tank values differ from the fleet's. The
   valid argument ("no candidate value, and no five-tuple, separates tanks from the fleet") is made
   in §2 and is correct; §1's reason is not.
2. The Done clause's second branch - "the pivot is **proven** to be code tied to a vehicle type" -
   is not proven. What is proven is that no data value distinguishes the tanks. Whether the shipped
   tanks pivot at all is untested (the doc itself says so), so "carried by native code keyed to the
   vehicle's identity" is an inference, not the proof the tracker row implies.
3. The fleet class table (§5) sums to **214 of 232** builds: **19 bike builds have no `.epe`
   vehicle class** and the doc does not say so, although `TANKTURN.json` records the list
   (`vehicle_class.no_vehicle_class`).

None of these changes a number in the candidate tables, and the MOD-2 conclusion stands.

## Check output (verbatim)

```
$ python Tools/scripts/jc3tankturn.py --check
PASS: 12 tank builds / 145 player land_global, 4 card modules identical (0 tank-only / 0 non-tank-only members), 0 tank-only module types, 5 candidates refuted (27 non-tank builds share a tank tuple), 262 tank-unique values with 0 in driving modules, 9 name matches (0 script file types), vehicle class {'CCar': 12}
exit=0
```

Out paths named in the row all exist:

```
-rw-r--r-- 1 User 197121 46655 Oct 27 21:59 Research/JC3Grab/TANKTURN.json
-rw-r--r-- 1 User 197121  9123 Oct 27 21:59 Research/JC3Grab/TANKTURN.md
-rwxr-xr-x 1 User 197121 31957 Oct 27 21:55 Tools/scripts/jc3tankturn.py
```

## Issues

### 1. The §1 reason does not support the sentence it carries

`TANKTURN.md:5-8` (template `jc3tankturn.py:427`): the four card modules "carry **byte-identical
member sets** in tanks and cars, so no tuned value in them can switch a neutral turn on."

* "Byte-identical" is wrong twice: a set of member names has no bytes, and the *values* in those
  modules are not identical - the doc's own §2 lists `number_of_wheels` 6/8/8/4 on the tanks
  against a fleet histogram, and `wheels_friction_type` 2. A reader who takes "byte-identical"
  literally would conclude the tanks are copies of the cars, which the same page contradicts.
* The inference is invalid: identical *vocabulary* means a pivot would have to be expressed with
  the same members but different values, which is exactly what §2 then tests. The conclusion is
  right; the reason attached to it is not. Say "member sets identical, so a pivot could only be a
  value on those members - and no value separates the tanks (§2)".

### 2. "Proven to be code" is stronger than the evidence (Done clause)

The card's Done: "the member set that produces a pivot is named with values, **or the pivot is
proven to be code tied to a vehicle type** (then MOD-2's turn-on-the-spot becomes a named
omission)."

The doc concludes: "a pivot, if the game has one, is decided in native code keyed to the vehicle's
identity - data leaves no other discriminator" (§6). That is one hypothesis among two: the other
is that JC3's tanks cannot pivot at all (no such mechanic exists), in which case MOD-2 is a new
mechanic rather than an omitted translation. The evidence rules out a *data* carrier; it does not
distinguish "native pivot" from "no pivot". The doc's own UNKNOWN sentence concedes this ("whether
the shipped tanks pivot at all … is UNKNOWN"), so the finding is honestly hedged in §6 - but the
tracker row's "the pivot itself UNKNOWN (native code, Q-1 probe)" and the headline read as if code
involvement were established. The record should say: *no data carrier; runtime behaviour unknown;
the omission is declared on the absence, not on a proof of native support.*

### 3. The fleet class table is incomplete and does not say so

`TANKTURN.md:110-114`: "`.epe` vehicle class | CCar x12 | CAirPlane x18, CBoat x35, CCar x126,
CHelicopter x23, CTrain x12". Sum = **214**. `TANKTURN.json` →
`vehicle_class.no_vehicle_class` lists **19 builds with no class at all** - every `v3xxx` bike
build (`v3000`, `v3001`, `v3401`, `v3402`, `v3500`–`v3503`, `v3600`). So the class census is 214/232
and the missing 19 are a whole vehicle family, not noise. The tank conclusion is unaffected (all
12 tank builds resolve to `CCar`), but a fleet census that silently drops 8 % of the fleet in a
column headed "fleet" is the kind of thing R4 exists to prevent. The json already carries the
list; the doc should carry a footnote.

### 4. "40 of 47 users" does not match the artifact

`TANKTURN.md:129` (Limits, typed in `jc3tankturn.py:586`): "`wheels_friction_type`'s enum meaning
(0/1/2) is `UNKNOWN` - it tracks the off-road tyre modules only loosely (**40 of 47 users**)".
`TANKTURN.json`'s histogram for that member is `{0: 92, 1: 5, 2: 48}` over 145 player builds
(4 tanks + 44 others at type 2). Neither 47 nor 40 appears anywhere in the build. The claim is
correct in substance (type 2 is shared by far more cars than tanks; 36 non-tank builds share a
tank value per §2), but the parenthetical is unsourced and the numbers are not the ones the card
generated. Drop the parenthetical or derive it.

### 5. Two literal numbers in an otherwise fully derived doc (R11)

* "4/6/8 discrete wheels" (`TANKTURN.md:4`, `jc3tankturn.py:429`) - correct, but typed; the tank
  values are in `candidates`.
* "40 of 47" as above.
Everything else in the doc is interpolated from `TANKTURN.json` (I checked the render function for
the candidate table, the module table, the unique table, the container table and the class table:
all `d[...]` values).

### 6. "Value = player `LandGlobal`" is a real strength - and worth stating once in §7

The doc says the `_ai` twin "differs on a candidate member, so it is never read" (§1). That single
rule is what makes the histograms right: my first independent scan read the first `LandGlobal`
instance per entity and got `is_all_wheel_steered` 0 on all 144 builds, while the correct
player-copy read gives 0 x142 / 1 x3 (the three monster-truck builds). The card's numbers are the
correct ones; the pitfall is worth naming in §7 as a method note, because any later census that
forgets it will disagree with this card.

## Spot-checks

| # | value in the doc | verified against | result |
|---|---|---|---|
| 1 | 12 tank builds, 145 player `LandGlobal`, 232 entities / 232 detail graphs | `TANKTURN.json` inputs (232/232), `fleet_land_global` 145, `vehicle_class.tank` `{CCar: 12}` | match |
| 2 | `number_of_wheels` tank values 6 / 8 / 8 / 4; fleet 2 x18, 3 x1, 4 x113, 6 x6, 8 x7 | `TANKTURN.json` `candidates[0]`; independent count over the decoded land builds gives the same histogram shape (4 x113, 6 x6) | match |
| 3 | `wheels_friction_type` tank values all 2; fleet 0 x92, 1 x5, 2 x48; 36 non-tank builds share a tank value | `TANKTURN.json` `candidates[4]` histogram and `non_tank_sharing_tank_value` 36 | match (but see Issue 4 for the 47/40 sentence) |
| 4 | five-tuple: 3 tank tuples, **27** non-tank builds share one ((4,-1,0,0,2) x23, (6,-1,0,0,2) x3, (8,4,0,0,2) x1) | `TANKTURN.json` `tuple_test`: `tank_tuples` 3, `non_tank_sharing` {23,3,1}, `non_tank_sharing_total` **27** | match |
| 5 | 262 tank-unique values, by module 1 + 37 + 14 + 16 + 194; 0 in driving modules | `TANKTURN.json` `unique`: `by_module` sums to **262**, `driving_module_hits` `{}` | match |
| 6 | 52 fleet module types, 25 on tanks, 0 tank-only | `TANKTURN.json` `module_types` {fleet 52, tank 25, tank_only 0}; my own census over 232 entities also gives 52 | match |
| 7 | 9 name matches, none in a driving module | `TANKTURN.json` `names.data_matches` 9 / `vocabulary_matches` 9; §4 lists them and all are `tire_effects.*` or `train_track_width_scale` | match |
| 8 | "the only `is_all_wheel_steered=1` builds are three monster trucks" | direct scan of the decoded entities: 3 hits, all `v0803_car_na_monstertruck_*` | match |
| 9 | wheel stations = `number_of_wheels` on all 12 tank builds | `invariants()` asserts `hardpoints.tank_mismatch` empty and `--check` passes | match (script-side) |
| 10 | fleet class census | json `vehicle_class.fleet` sums to **214**, `no_vehicle_class` 19 | **incomplete in doc** (Issue 3) |

## What holds up

* The card answers its own question the right way round: it does not hunt for a member whose name
  sounds like a pivot, it tests whether any *value* separates the tanks from the fleet, and when
  none does it says so instead of inventing a bridge. That is R5 done properly.
* The five candidates are each refuted with the sharing count against them, and the five-tuple
  test is the strongest form of the argument - 27 non-tank builds share a tank tuple, including an
  aircraft.
* The tank-unique census is a good negative control: 262 tank-unique values exist, but the
  breakdown shows they are art data (water-mesh geometry, effect slots, fins, propellers) and
  **zero** are in a driving module. That closes the "maybe you missed a driving member" objection.
* Container and class checks are the right second angle: the tanks are `CCar` wheel vehicles with
  data-only bundles and wheel stations equal to `number_of_wheels`, so there is no track object to
  find.
* `invariants()` genuinely asserts the findings (0 tank-only members, no candidate separates, 0
  tank-unique driving values, no script types, `CCar` x12, hardpoint match, AI-twin difference
  exists) rather than only diffing text - unlike some sibling cards.

## Limits of this review

* Read-only: I did not tamper with `TANKTURN.json` to re-test the failure mode. `MODLOG.md:10044`
  records a one-value json edit making `--check` exit 1, and a rebuild returning PASS, consistent
  with `main()` as written.
* I did not re-decode the 232 `.epe` graphs; the class figures are checked against
  `TANKTURN.json` and my own preamble-level scan of the decoded cache, not against raw `.epe` bytes.
* The claim "wheel stations = `number_of_wheels` on all 12" and the container extension census are
  script-side assertions I did not recompute from the containers.
* Whether JC3 tanks pivot remains untestable here (no game launch allowed) - the review does not
  contradict the card on that point, it only disputes calling it proven.
