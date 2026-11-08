# Assumption challenge — backlog card G2-21 (turn-on-the-spot / tank pivot)

Read-only pass over the finished card: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G2-21 card (§6, line 698),
its §12 row (line 1304), the MODLOG `G2-21 · Turn-on-the-spot (tank pivot) — intended change` and
`— done` sections, and the outputs `Research/JC3Grab/TANKTURN.md` + `TANKTURN.json` + the generator
`Tools/scripts/jc3tankturn.py`, plus what it reads: `E:/Modding/_JC3grab/entities/*.ee.json` (232),
`VOCABULARY.md`, `WEAPON_WIRING.jsonl`, and — for the physics check below — the already-decoded Havok
census in `E:/Modding/_JC3grab/hkx/out/`.

Constraints honoured: no game launched, nothing written into `D:/Games`, no archive opened, nothing
committed, no secrets, no `--write`. The card's gate:

```
$ python Tools/scripts/jc3tankturn.py --check
PASS: 12 tank builds / 145 player land_global, 4 card modules identical (0 tank-only /
0 non-tank-only members), 0 tank-only module types, 5 candidates refuted (27 non-tank builds
share a tank tuple), 262 tank-unique values with 0 in driving modules, 9 name matches
(0 script file types), vehicle class {'CCar': 12}                                    EXIT=0
```

## VERDICT

**One BROKEN, five WEAK, seven HOLDS.** The **negative result stands, and it stands better than the
document argues it**: I re-ran the "does anything distinguish a tank" question as a full separability
test over all 731 driving-module member paths rather than the card's five candidates — 524 of them are
constant across all 12 tank builds, and **not one** has a value that is absent from the 133 non-tank
land builds or shared by as few as five of them. That is a stronger statement than the md makes, and
it supports MOD-2's omission.

What is broken is the *argument* the md leads with. `TANKTURN.md` §1 says the four card modules "carry
**byte-identical member sets** in tanks and cars, so no tuned value in them can switch a neutral turn
on". Two errors in one clause: the comparison is of member **paths** (the MODLOG says so correctly),
not bytes; and the inference does not follow — a shared member *name* is exactly how a per-vehicle
*value* would switch a behaviour on. The same document then prints tank values that differ from the
cars' by a factor of 26 (`RigidBody.mass` 975 vs 25 000, `Transmission.top_speed` 320 vs 105), which
is the proof that the members are not "identical" in the sense the sentence needs.

The frame is also narrower than the card implies (12 of 13 tank builds in the index, 232 of 314
vehicle `.ee`), and the token scan that backs "nothing names a pivot" uses a word list that omits the
closest vocabulary in the game — `counter_steer_*`, `*_yaw_vel_damp`, `steering_sensitivity` — so its
9 hits are a sample of a different question. Neither changes the answer; both should be fixed before
someone quotes the md as a proof.

| # | assumption | verdict |
|---|---|---|
| A1 | the tank set is 12 builds of 4 chassis, against the 232 cached builds | **WEAK** — the index has 13 tank builds (DLC `mediumtank_blackhand_01` is not decoded) and 314 vehicle `.ee` |
| A2 | "byte-identical member sets, so no tuned value can switch a pivot on" | **BROKEN** — sets of member *paths* are equal, values are not (mass 975 vs 25 000), and the inference is invalid |
| A3 | no driving-module value distinguishes the tanks | **HOLDS** — 524 tank-constant members, 0 unique, 0 shared by ≤5 non-tanks |
| A4 | the five-tuple does not separate tanks | **HOLDS** — 12 tanks collapse to 3 tuples that 27 non-tank builds also carry |
| A5 | `is_all_wheel_steered=1` is a monster-truck crab steer, not a pivot flag | **HOLDS** — the only three builds are 4-wheel, `number_of_front_wheels=-1` |
| A6 | wheel stations = `number_of_wheels` ⇒ "the physics is a wheel set, not a track belt" | **WEAK** — station count fits both; the Havok census is the real evidence and it too is only consistent |
| A7 | no tank-only module type; tanks use the fleet vocabulary | **HOLDS** — 52 types fleet / 25 tank / 0 tank-only |
| A8 | 262 tank-unique values, none in a driving module | **HOLDS** — recomputed; all in DeformPoints/EffectAttachments/Fins/Propellers/WaterInteraction |
| A9 | the name scan's 9 hits are the whole story | **WEAK** — the token list misses `counter_steer_*`/`yaw`/`steer`; a wider scan finds 30 driving members, none tank-unique |
| A10 | the tanks' containers are data-only (0 script-like) | **HOLDS** — 18 extensions, no script type; `.afsmb`/`.asb` are compiled binaries |
| A11 | all 12 tank builds declare `CCar` | **HOLDS** — no track vehicle class exists in the graphs |
| A12 | therefore the pivot is native code keyed to the vehicle's identity | **WEAK** — the absence is solid; the attribution is one hypothesis among several |
| A13 | the card's "pivot is proven to be code tied to a vehicle type" | **WEAK** — what is proven is that no data value separates tanks, not that a pivot exists or where it lives |

Counts: 7 HOLDS, 5 WEAK, 1 BROKEN.

---

## A1 — 12 tank builds against the 232-build cache. **WEAK**

The tank set is name-prefix based (`v0200_`, `v0201_`, `v0202_`, `v0603_`) — that is the card's four
chassis, so the *definition* is faithful. The frame is not the fleet:

```
index tank-tagged .ee: 13
    dlc/mech_land_assault/…/v0201_car_capstone_mediumtank/v0201_car_capstone_mediumtank_blackhand_01.ee
    … the 12 base builds (apc/mediumtank/bavariumtank/smalltank × debug/military_01/rebel_01)
cache entity builds: 232         tank builds in cache: 12
index vehicle .ee: 314           vehicle .ee NOT decoded: 82
```

The one missing tank build is a DLC re-skin of the medium tank (`blackhand_01`), so the 12/13 gap is
unlikely to change any value claim — but the 232/314 gap matters in principle: the same DLC set that
broke G2-17's fleet claim is absent here too, and the tanks' values are compared against a
three-quarters sample of land vehicles. `TANKTURN.md` §7 states the limit ("the 232 cached entity
builds, not live archives"); §1's "every other land vehicle in the decoded cache" is accurate. The
headline "the fleet" is the only overreach. **WEAK**, mild.

## A2 — identical member sets, therefore no tuned value can pivot. **BROKEN**

`TANKTURN.md`, §0:

> … and the four modules the card names carry **byte-identical member sets** in tanks and cars, **so
> no tuned value in them can switch a neutral turn on**.

The comparison in the generator is `set(rows_of(player, t))` — a set of member *paths*. Bytes are not
compared, and the modules' contents are plainly different:

```
chassis      nw aws   smin smax  topspeed      mass  drift
apc           6   0     35   15       110      6400     25
medium        8   0     45   30       105     25000     45
bavarium      8   0     45   30       105     25000     45
small         4   0     35   25        90     13100     45
donor car     4   0     35   15       320       975     45
```

Same member names, different values (`mass` ×26, `top_speed` ×3). That is not a cosmetic wording
problem: the conclusion the sentence draws is the opposite of what the data shows. If a pivot were a
tuned value, it would live in exactly such a shared member — and the document's own §2 admits a
shared member (`is_all_wheel_steered`) that could be one. The correct sentence is: *the four modules
expose the same members in tanks and cars, so a pivot switch would have to be a value on a shared
member — and §2/§3 show that no such value separates the tanks.* That version is true and still
supports the omission.

## A3 — no driving-module value distinguishes a tank. **HOLDS (stronger than the md)**

I re-ran the question as a separability test instead of five named candidates. For every one of the
731 member paths in the ten driving modules, across 145 player `LandGlobal` builds (12 tank):

```
tank-constant members (same value on all 12 tanks): 524
  of which value absent from all 133 non-tank builds: 0
  of which value shared by <=5 non-tank builds:       0
```

So no single driving value marks a tank, and the margin is not marginal — every tank-constant value is
shared widely. Allow the tanks to differ among themselves and ask for value *sets* that never overlap
the rest:

```
driving members whose tank value-set is disjoint from all non-tanks: 3
  RigidBody.mass               ['13100', '25000', '6400']
  RigidBody.unit_inertia_pitch ['2.95', '4.1', '6.19']
  RigidBody.unit_inertia_yaw   ['3.15', '4.6', '7']    (non-tanks: 0.31 .. 0.86)
```

Three set-level exceptions, all rigid-body inertia — a heavy vehicle's mass properties, not a steering
or drive switch. They are worth naming because they are the only members whose tank values are
unreachable by any other land vehicle, and because a port that copies the donor's `RigidBody` gets none
of that mass. **HOLDS**, with the caveat that "no member distinguishes" is true per value and false per
set for these three.

## A4 — the five-tuple. **HOLDS**

```
tank tuples:      (4,-1,0,0,2) ×3    (6,-1,0,0,2) ×3    (8,4,0,0,2) ×6     = 12
non-tank sharing: (4,-1,0,0,2) ×23   (6,-1,0,0,2) ×3    (8,4,0,0,2) ×1     = 27
```

Reproduced from `TANKTURN.json` (`tuple_test.non_tank_sharing_total = 27`). The small tank's tuple is
carried by 23 ordinary off-road builds; the medium/Bavarium 8-wheel tuple by one cargo plane. The
claim "the candidate set does not identify a tracked vehicle" is exact.

## A5 — `is_all_wheel_steered` is not a pivot flag. **HOLDS**

The md uses this to close the one candidate that could plausibly *enable* a neutral turn. Verified:

```
v0803_car_na_monstertruck__…_civilian_01  nw=4 front=-1 rear=0 aws=1
v0803_car_na_monstertruck__…_civilian_…  nw=4 front=-1 rear=0 aws=1
v0803_car_na_monstertruck__…_debug       nw=4 front=-1 rear=0 aws=1
```

Three monster-truck builds, four wheels, `number_of_front_wheels=-1` (auto), rear steer 0. "All wheels
steered" on a 4-wheel vehicle is a crab/all-wheel-steer setup, not skid steering; the tanks have it 0.
So the flag is neither a track marker nor present on the tanks. **HOLDS.**

## A6 — wheel stations ⇒ "a wheel set, not a track belt". **WEAK**

```
hardpoints.tank_mismatch: []      # station count == number_of_wheels on all 12
```

That equality is evidence that the *entity* declares one hardpoint per wheel; it cannot distinguish a
tracked vehicle that is simulated as N wheels (which is how many games do it) from a car. The sentence
"i.e. the physics is a wheel set, not a track belt" is an inference, and the container/havok census is
where the real support is:

```
class                                        tank-medium tank-small tank-apc tank-bavarium car-donor car-hothatch
hknpConvexPolytopeShape                       70          37         76       62           54        79
hknpDynamicCompoundShape                       6          12          7        6           20        16
hknpStaticCompoundShape                       11           0         13       11            2        12
hknpExternMeshShape                            3          14         35        2           18        31
hkpLimitedHingeConstraintData                  3          16         16       15            9         7
```

The tanks and cars share the same Havok class vocabulary — no track, tread or belt class exists in any
of them, and the tanks have *fewer* dynamic compound shapes than the donor car, not a different kind.
That is good evidence that the physics is built from hull polytopes + hinges, like every other vehicle.
It is still not proof that no track constraint exists inside a polytope or a property list, so the
claim should be "the physics contains no track-specific shape class", which the census supports.
**WEAK** (conclusion likely right, stated as decoded fact).

## A7 — no tank-only module type. **HOLDS**

```
module_types: fleet 52, tank 25, tank_only []
tank_list: Brakes, Buoyancy, CarAI, CustomLandGlobal, CustomVelocityDamper, DeformPoints,
           EffectAttachments, ExtendedEffectUsages, Fins, LandAerodynamics, LandAudio, LandEngine,
           LandGlobal, LandSteering, Propellers, RigidBody, StuntAreas, Suspension, Tire,
           Transmission, VehicleCommon, VehicleDamage, VehicleDynamicLights, VehicleMisc,
           WaterInteraction
```

No track module, no second steering module. Reproduced.

## A8 — 262 tank-unique values, all art. **HOLDS**

```
unique.by_module: DeformPoints 1, EffectAttachments 37, Fins 14, Propellers 16, WaterInteraction 194
unique.driving_module_hits: {}
```

Definition used: value identical on all 12 tank builds and absent from every other vehicle. The 194
`WaterInteraction` hits are water-mesh/float data (a tank is not amphibious, so its water config is
unique), the rest are deform points, effect slots and fin/propeller placements. None is in a driving
module. Caveat: a tank-vs-car difference that varies *between* the four tank chassis is invisible to
this census — I checked that case separately in A3 (3 rigid-body members).

## A9 — the name scan. **WEAK (the scan, not the conclusion)**

The token list is `track|pivot|skid|neutral|turn_on|turnin|in_place|counter_rot|opposite`. Re-scanning
the same 32 219 member paths with the words a neutral-turn feature would plausibly use
(`+ counter|yaw|spin|rotat|steer|differ|left|right`):

```
wider-token hits: 390, of which 30 are in driving modules
  CustomLandGlobal.drift.counter_steer_rot_factor
  CustomLandGlobal.drift.counter_steer_torque
  CustomLandGlobal.drift.counter_steer_torque_brake
  CustomLandGlobal.drift.counter_steer_torque_handbrake
  CustomLandGlobal.drift.drift_yaw_vel_damp / exit_… / overdrift_…
  CustomLandGlobal.drift.steering_sensitivity
  LandGlobal.is_all_wheel_steered / is_rear_steered
  LandSteering.countersteer_speed_factor, steer_angle_*, steer_curve_falloff,
             steer_in_speed_factor, t_to_full_steer_s, wheel_drift_aligning_strength
  RigidBody.unit_inertia_yaw
```

`counter_steer_torque` and `counter_steer_torque_handbrake` are the closest thing in the game's
vocabulary to a counter-rotating (neutral-turn) control, and the md's token list would not have found
them — its `counter_rot` matches neither. They turn out to be drift parameters inside
`CustomLandGlobal.drift.*`, present on every vehicle with the module, and their tank values are not
tank-unique. So the conclusion is unaffected, but the claim "9 name matches, 0 in a driving module" is
an artefact of the word list, and the md should say "no member whose *name* denotes a track or a
neutral turn separates tanks from cars" rather than "the vocabulary has no such name".

## A10 — containers are data-only. **HOLDS**

```
extensions: rbm 2496, ddsc 1350, effc 1152, trim 876, lod 705, vmodc 354, ctunec 204, pfxc 54,
            etunec 36, wtunec 33, ftunec 21, epe 12, fmod_guids 12, physicsc 12, stringlookup 12,
            afsmb 9, asb 9, bsk 9          script_like: []
```

No script extension. Minor wording: `.afsmb`/`.asb` are compiled animation/state binaries, so "data
only" is true only in the sense "no script file type" — the md already words it that way in §5. The
stronger claim it feeds (pivot logic is native code) does not follow from an extension census, see A12.

## A11 — all 12 tanks declare `CCar`. **HOLDS**

```
vehicle_class.tank: {'CCar': 12}     fleet: CAirPlane 18, CBoat 35, CCar 126, CHelicopter 23, CTrain 12
```

There is no `CTrackVehicle`-style class in any graph, so a port cannot select "tank behaviour" by class
name. Reproduced. (Side note the artefact surfaces: 19 bikes have no vehicle class at all, which is why
the fleet classes sum to 214, not 232.)

## A12 — therefore the pivot is native code keyed to identity. **WEAK**

The absence result (A3/A7/A8/A9) is solid. The attribution is a leap: "no data value distinguishes" is
compatible with several carriers other than "native code keyed to the vehicle's identity", e.g.

* a native *behaviour* of the wheel configuration (high yaw inertia, 8 wheels, handbrake torque) that
  no single member selects — the 3 rigid-body members in A3 are exactly that shape of difference;
* an input mapping or game-mode flag outside the entity (the card itself notes `MOD-2` needs a mode);
* a physics property inside a polytope/hull that this project does not decode.

The md states the conclusion as fact ("The deciding logic therefore cannot be data") and then, in the
same paragraph, correctly says whether the tanks pivot at all is UNKNOWN. Both halves cannot be strong:
if we do not know whether the behaviour exists, we cannot attribute its implementation. The honest
claim is the one the card's Done column allows: *no data value in the decoded entities selects a
pivot, so MOD-2's requirement has no data carrier to copy.* **WEAK.**

## A13 — "the pivot is proven to be code tied to a vehicle type". **WEAK**

The card's Done condition is an either/or: "the member set that produces a pivot is named with values,
**or** the pivot is proven to be code tied to a vehicle type". The work establishes the first branch
fails; it does not establish the second (that would need the executable or a probe). What it does
establish is enough for MOD-2: there is no JC3 data member to port. The §12 row and the md should
therefore read "named omission: no data carrier" rather than "proven code", and the Q-1 probe remains
the only way to know whether JC3 tanks pivot at all — which `TANKTURN.md` §6 does say.

---

## What would close the gap cheaply

1. **Fix A2's sentence** — "the four modules expose the same member paths in tanks and cars (48/15/40/61,
   0 either way); their values differ (mass 975 → 25 000), so a pivot would have to be a value on a
   shared member, and the separability test below shows none exists."
2. **Add the separability test to the generator** — 524 tank-constant driving members, 0 unique, 0
   shared by ≤5, 3 disjoint value-sets (mass, unit_inertia_pitch/yaw). It is 20 lines over JSON already
   in memory, and it replaces five hand-picked candidates with a census.
3. **Widen the token list** and report the 30 driving-module hits it currently hides, then say they are
   drift/steer parameters, none tank-unique.
4. **Soften A12/A13** to "no data carrier" and put the identity claim in the Q-1 probe, and decode the
   one missing tank build (`…_mediumtank_blackhand_01.ee`) so the count is 13/13.
