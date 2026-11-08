# Moving-parts behaviour gaps - closest-system plan

Scope: every T-12 row that is **omitted, partial, blocked or UNKNOWN**, the closest JC3
animation/skeleton mechanism for each, the member or file that carries it, and the build step that
closes it with the row's own numbers.

Sources (read, not re-decoded here): `tmp/freebuff/reports/T-12.md`;
`Working/Translation/T8_PARTS.md` and `T8_PARTS.json`; `Working/Translation/PARTS_ANIM_COVERAGE.md`;
`Working/Translation/P02_CANNON.md`; `Working/Translation/P13_STEERING.md`;
`Working/Parts/JOINT_FIELDS.md`; `Research/JC3Grab/MOVING_PARTS.md`; `Research/JC3Grab/TURRET.md`;
`GRAB_BACKLOG.md` §8 (B-02, B-04, B-05) and ANI-2…9; `Tools/scripts/bm_parts.py` (the writer).

**Labels.** **decoded** = read at the file/export/offset quoted. **derived** = arithmetic over
decoded values. **UNKNOWN** = absent from every file read, with the file or probe that would settle
it. No value below is inferred from a plausible JC3 pattern.

---

## 1. Every marked row

T-12's own markers are `static_rows` P-02/P-05/P-13, the four `no part` rows P-06/P-07/P-08/P-13,
the `unproven-on-CCar` rows, P-04's `axis_agrees: false`, and the `omitted[]` array entries
`bm_parts.py` writes. They map to six mechanism groups.

| row | part | marker in T-12 / outputs | why the row is short | group |
|---|---|---|---|---|
| P-01 | `batmobile_turret` | not short - shown for contrast: -60…60° vs shipped hinge -179…179° | range differs from the donor carrier, axis agrees | A |
| **P-02** | `batmobile_cannon` | **static** (`joint: null`); `Cannon` channel `none` | no rotation animated; bones translate 53.376 / 36.129 cm; hinge -5…20° is the carrier's, not BmAK's | A |
| **P-04** | `batmobile_riot_suppressor` | **partial**: `axis_agrees: false` | BmAK joint turns about JC3 **-Z** (-89.999…0°), the shipped `Cannon` hinge about **+X** (-5…20°); the part bone itself only spans 6.677° | A |
| **P-03** | `batmobile_machine_gun` | **partial**: damage type `Boat_Generic`, `unproven-on-CCar` | no land vehicle in the fleet carries `GatlingGun`; the joint itself is covered | B |
| **P-05** | `batmobile_jet` | **static** (`joint: null`) + **omitted** `rotating_parts` row | no rotation animated; `JetSMove` translates 40.163 cm; spin is `engine_rpm`; no axis to write | C |
| **P-06** | `no part` (canopy) | **no part**; `Hood` door channel; translation 72.481 cm | geometry stays in the body shell; JC3 door parts only rotate | D |
| **P-07** | `no part` (left cover) | **no part** + **omitted** `door_parts` row; `unproven-on-CCar` | 14.988° lift is carried by pod bones; no hatch bone and no hatch part | E |
| **P-08** | `no part` (right cover) | **no part** + **omitted** `door_parts` row; `unproven-on-CCar` | same as P-07, mirror | E |
| **P-14** | `batmobile_missile_pod_l` | **static**: no behaviour of its own, `moves_with: P-07` | the shell is static; its cover is P-07 | E |
| **P-15** | `batmobile_missile_pod_r` | **static**: no behaviour of its own, `moves_with: P-08` | the shell is static; its cover is P-08 | E |
| **P-09…P-12** | four `batmobile_aero_flap_*` | **partial**: no hinge; `unproven-on-CCar` | `AirBrake` has 3 parts on 1 plane and 0 on land; carrier limits not in the 8-entity sample | F |
| **P-13** | `no part` (yoke) | **static** (`joint: null`) + **no part** | no bone and no geometry (`COCKPIT.md`); nothing to animate | G |
| - | `aim_part_constraints[]` | **omitted** (written empty) | 0 rows on all six turreted vehicles; aim is not a module array | H |
| - | hinge/rotating rate | **UNKNOWN** (T-12 §UNKNOWN 1) | `all_hinged_part_properties` has no rate member | A, D, E, F |

T-12's report also lists six UNKNOWNs; three are row facts (canopy translation, covers without a
bone, no rotation for cannon/turbine/yoke), two are member facts (hinge rate, unsampled carrier
hinges), one is the Vulcan damage type. They are placed in the groups below.

---

## 2. Group A - turret and gun rotators (P-01, P-02, P-04)

**Closest JC3 mechanism (decoded).** A part's only joint is `parts[i].constraint_index`, an int32
into the vehicle's ordered constraint objects in the `.physicsc`; the object is a 304-byte
`hkpLimitedHingeConstraintData` with axis at `+0x30`, pivot at `+0x60`, min/max angle in radians at
`+0xFC`/`+0x100` (`JOINT_FIELDS.md` §1-§2). `Turret` and `Cannon` have **no** `vehicle_common` row
(`MOVING_PARTS.md` §2); they are Havok-hinge parts. `hinged_parts[]` is not the joint - it stores a
part index only. `aim_part_constraints[]` is not the joint either - 85 rows in 17 of 78 modules, all
suspension, **0 on the six turreted vehicles** (`TURRET.md`, `bm_parts.py` `aim_note`).

**What closes it, with the row numbers.**

| row | build step | payload |
|---|---|---|
| P-01 | B-04 step 3 + the hinge append | `constraint_index` 11, axis `[-0.0, 1.0, -0.0]`, pivot `[1.3e-05, 0.876249, 0.333226]` m, `-1.047198 … 1.047198` rad (-60…60°), source: P-01 joint (decoded animation) |
| P-02 | same step | index 12, axis `[1.0, 0.0, 0.0]`, pivot `[0.000358, 1.702446, 0.017586]` m, `-0.087266 … 0.349066` rad (-5…20°), source: P-02 **carrier hinge** (`mediumtank_cannon`), not a BmAK pitch |
| P-04 | decision first, then the same step | if the BmAK line is chosen: axis `[-0.0, 0.0, -1.0]`, `-1.570778 … 0` rad (-89.999…0°), rate 315.39 °/s; if the carrier line is chosen: axis `[1.0, 0.0, 0.0]`, `-5…20°`, part bone span 6.677° at 47.21 °/s. The row must state which, because the two lines are not the same line |

Note P-02's row is *static for animation*, not *unhinged*: the -5…20° carrier hinge is already in the
row. B-10's writer path (`bm_physicsc_hinges.py`) writes `-0.087266 … 0.349066` rad into hinge 12;
the parts module currently ships `constraint_index = -1` on parts 50/51 (`JOINT_FIELDS.md` §5), so
the hinge exists in the physicsc but the part does not point at it.

**Evidence level.** Hinge offsets, class, indices and the -5…20° values: **decoded**
(`JOINT_FIELDS.md`, `Research/JC3Grab/TURRET.json`). P-04's axis disagreement: **decoded** (BmAK
joint `axis_jc3 [-0,0,-1]` vs donor hinge `[1,0,0]`). Which line P-04 should follow: **UNKNOWN** -
settled by a Q-1 turret/pod probe or an operator decision, not by any file.

**UNKNOWN.** Hinge **rate**: `all_hinged_part_properties` carries `target_position_variable`, `lod`,
`use_target_position_as_angle` and no rate (`MOVING_PARTS.md` §1); the 174.05 / 315.39 °/s are
BmAK animation rates. Settling file: none in JC3 data - it is code (`vehicle_common.vmodc` proves the
absence; the rate needs an in-game or engine-side probe).

**Pilot card.** "Aim at three targets around the car: the turret sweeps the measured -60…60° span and
the barrel stops at the carrier's -5…20° without entering the hull."

---

## 3. Group B - Gatling rotator (P-03)

**Closest JC3 mechanism (decoded).** `all_rotating_part_properties.GatlingGun` in
`vehicle_common.vmodc`: `rpm_variable = weapon_rpm`, `rotoscope_enabled 0`, `rotoscope_rpm_per_cycle
20.0`; the per-part row is `rotating_parts[]` in `sportsmuscle_vehicle_parts.vmodc`, which stores
`rotation_axis`, `position`, `number_of_blades`, rpm fields. 24 shipped rows use it on 12 parts across
3 chassis, all `CBoat`/`CHelicopter` (`MOVING_PARTS.md` §2).

**What closes it.** B-04 step 3 writes the `rotating_parts` row: part `batmobile_machine_gun`, axis
`[-0.0, 0.0, -1.0]`, `number_of_blades` 1, position = the part's `parent_space_offset`, `rpm_multiplier`
1.0, `rpm_variable` `weapon_rpm`. The row's motion is **2160.0° = 6.00 turns over 3.90 s at
1229.51 °/s**; the joint's 357.354° sampled extent is one ±180° wrap, not a limit.

**Evidence level.** Behaviour row and rpm fields: **decoded** (`MOVING_PARTS.md` §1); axis/travel:
**decoded** (`Batmobile_V2_ChainGun_Spin`, export 218). Damage type `Boat_Generic` is a fleet fact,
**decoded** (24 rows, training carrier `v1401_boat_mugello_racingboat`), not a car value - the row is
honest, not smoothed.

**UNKNOWN.** What JC3 does with `rotoscope_rpm_per_cycle` 20.0 (the value is decoded, the meaning is
inferred); and the deg/s JC3 actually produces, which is code. Settling file: no JC3 file defines it;
a Q-1 #4 / Q-3 #3 spin probe settles the observable.

**Pilot card.** "Fire a burst: the barrels start spinning on the first round, hold 6 turns per 3.9 s
of BmAK travel, and stop with the burst."

---

## 4. Group C - engine/turbine rotator (P-05)

**Closest JC3 mechanism (decoded).** `all_rotating_part_properties.EngineRotatingPart`:
`rpm_variable = engine_rpm`, `rotoscope_enabled 1`, `rotoscope_rpm_per_cycle 20.0`; 3 rows / 3 parts /
1 chassis, proven on a land vehicle (`v0506_car_solar_oldtractor`, a tractor fan) - unlike P-03.

**What closes it.** B-04 step 3, but the row is currently **omitted** by the writer: P-05 has
`joint: null` and no `axis_jc3`, so `bm_parts.py` leaves the `rotating_parts` row out rather than
guess an axis (`omitted[]`: "T-12 records `joint: null` ... no value without provenance"). The row
numbers are: `JetSMove` translates **40.163 cm** in `Batmobile_V2_Bat_Tracker`; the spin is
`engine_rpm`, not an animation; the carrier would be `EngineRotatingPart` with `rpm_per_cycle` 20.0.

**Evidence level.** Behaviour and rpm member: **decoded**; the 40.163 cm translation: **decoded**;
the spin axis: **UNKNOWN** - nothing in P-05's row or the animation supplies one.

**UNKNOWN.** The turbine's rotation axis. Settling file: a decoded `rotating_parts[]` row from the
proven carrier `v0506_car_solar_oldtractor` (or the turbine's own bone bind orientation in
`Research/BatmobileGrab/BONES.json` plus its geometry normal). Until one is cited, the omission is
the correct output (R4).

**Pilot card.** "Blip the throttle at idle: the turbine fan turns with engine rpm, speeds up on the
rev sweep, and never translates the 40 cm the BmAK clip moves."

---

## 5. Group D - canopy / hood hinge (P-06)

**Closest JC3 mechanism (decoded).** `Hood` is a name-only row in `all_door_part_properties`; a
door's travel comes from its Havok `hkpLimitedHingeConstraintData`, and the per-vehicle
`door_parts[]` lists only the part index (`MOVING_PARTS.md` §3). The shipped Batmobile carrier is
`sportsmuscle_hood_signature` on
`v0300_car_kensington_sportsmuscle_signature_preorder.ee`: axis `[1.0, 0.0, 0.0]`, **0.0…70.0°**,
pivot `[0.0, 1.0572, -0.8478]`, `Land_Hood` (`T8_PARTS.md` P-06).

**What closes it.** B-02 step 1 cuts the canopy faces into a part (the row currently has `part: null`
- geometry stays in the body shell), then B-04 step 3 writes the `door_parts` row and the hinge
points at the cut part. Row numbers: rotation **-12.492…0.002°** (12.494°, axis `[-1,0,0]`, 136.09
°/s) and translation **72.481 cm** in `Cockpit_Close`. A JC3 hinge reproduces the 12.494° rotation and
**cannot** reproduce the 0.72 m lift; use the donor's 0…70° as the travel envelope, or 12.494° if the
hinge is to match BmAK's angle. The row's verify already asks for "moves 0.71 m and 11 deg".

**Evidence level.** Hinge fields and animation span: **decoded**; the 72.481 cm lift: **decoded**
(`PARTS_ANIM_COVERAGE.md`, `Cockpit_Close`); the lift being unreproducible by a hinge: **derived**
from the hinge's one rotational DOF.

**UNKNOWN.** Whether a second translating part (a slider/link) exists anywhere in JC3 for a canopy -
no such behaviour is in the five `vehicle_common` tables. Settling file:
`Research/JC3Grab/MOVING_PARTS.md` (all 67 behaviours) already shows none; a fleet-wide part-module
scan for a translating door would settle it definitively.

**Pilot card.** "Enter and exit: the canopy rotates its 12.5° and closes flush, with the 0.72 m lift
either carried by a second part or visibly absent - never silently claimed."

---

## 6. Group E - missile hatches and pods (P-07, P-08, P-14, P-15)

**Closest JC3 mechanism (decoded).** `MissileHatch` is a name-only door row; 16 shipped rows, 1
part, 1 chassis (`v5603_train_urga_monorailmissilecar`, `CTrain`) - no car proof. The joint is a
limited hinge on the hatch part; `door_parts[]` only holds its index. The pods (P-14/P-15) have no
behaviour of their own and `moves_with` P-07/P-08.

**What closes it.** B-02 step 1 must re-cut the cover faces at face level out of the pod shell (the
14.988° is carried by `Missiles_L/R_T` bones whose faces are inside the pod parts), then B-04 step 3
writes the `door_parts` row for each cover. Row numbers: **0.019…15.007°** (14.988° span, axis
`[-1, 0, 0]`, top bone 32.14 °/s, bottom bone 75.10 °/s), pivot `[-0.616, 1.505, -0.465]` /
`[0.615, 1.505, -0.465]`, with a **10.866 / 10.863 cm** mid-bone translation that a hinge cannot
reproduce. The pods stay static and keep `moves_with`.

**Evidence level.** Angles, axes, pivots, translations: **decoded** (`Batmobile_V2_Missles_Up/Down`,
exports 237/239). Carrier existence: **decoded** (16 rows, one train). Car proof: **UNKNOWN** - the
behaviour is `unproven-on-CCar`.

**UNKNOWN.** The monorail `MissileHatch` carrier's hinge limits are not sampled: `TURRET.json`'s 8
entities do not include it, so only the animation span is known (T-12 §UNKNOWN 4). Settling file:
extend `Research/JC3Grab/TURRET.json` to `v5603_train_urga_monorailmissilecar` and decode its hinge.

**Pilot card.** "Fire one salvo: each cover lifts its 14.99°, the missiles leave, and the cover
closes; the pod shell itself never swings."

---

## 7. Group F - air-brake / fin hinge (P-09…P-12)

**Closest JC3 mechanism (decoded).** `all_hinged_part_properties.AirBrake`:
`target_position_variable = air_brakes_T`, `lod 1`, `use_target_position_as_angle 0`; the per-part
`hinged_parts[]` row stores the part index, and the angle/limit must come from a Havok limited hinge.
Only 3 shipped parts use it, all on one plane (`v4602_plane_urga_fighterbomber`, `CAirPlane`), so it
is `unproven-on-CCar`.

**What closes it.** B-04 step 3 for the four `hinged_parts` rows plus a hinge per flap. Row numbers:
part-bone spans **20.010°** (P-09/P-10, 37.20 °/s) and **29.986° / 30.005°** (P-11/P-12, 56.85 /
56.60 °/s); the piston-top bones carry 25.817° (front) and 54.787° / 54.799° (rear) at 48.70 / 106.14
°/s; all four pivot at ±1.155, 1.358, -0.798 (front) and ±1.200, 1.852, 1.641 (rear). The variable is
`air_brakes_T` (0..1 position, not an angle - `use_target_position_as_angle` is 0).

**Evidence level.** Spans, axes, rates, pivots: **decoded**; the 3-parts/1-plane fleet fact:
**decoded**; the hinge limits: **UNKNOWN** (same 8-entity sample problem as the hatch: the plane's
`AirBrake` carrier is not in `TURRET.json`).

**UNKNOWN.** Whether `AirBrake` works on a `CCar` at all, and the carrier's hinge limits. Settling
file: `Research/JC3Grab/TURRET.json` extended to `v4602_plane_urga_fighterbomber`, plus the Q-1 #4
air-brake probe (brake hard from 40 km/h); if the probe fails, ANI-5 becomes a static part with this
row as the reason.

**Pilot card.** "Brake hard from 40 km/h: all four flaps move together and return to zero when the
brake is released."

---

## 8. Group G - steering yoke (P-13)

**Closest JC3 mechanism (decoded).** `all_hinged_part_properties.SteeringWheel`:
`target_position_variable = steering_turn`, `lod 1`, `use_target_position_as_angle 0`; 20 rows over
20 parts on 9 chassis (8 cars + 1 sailboat) - proven on `CCar`. It is a variable-driven hinge, not an
animation, mirroring BmAK's sim-float steering.

**What closes it.** B-02 step 1 must create a yoke part and a pivot/bone (none exists), then B-04
step 3 writes the `SteeringWheel` row. There are **no row numbers to carry**: P-13 has `joint: null`,
no bone, no geometry (0 yoke faces in the hand box; 0 bone names matching steer/yoke across 180 bones
and 324 packages - `P13_STEERING.md`). The only number the mechanism supplies is the JC3 behaviour
row (20 parts / 9 chassis).

**Evidence level.** Absence of the BmAK asset: **decoded** (`COCKPIT.md`, `BONES.json`,
`ANIMATIONS.json`, 324-package name scan). The JC3 behaviour: **decoded** (`MOVING_PARTS.md`). The
steering-to-angle rate: **UNKNOWN** (code).

**UNKNOWN.** `SteerWheelBoneIndex`'s semantics (road-wheel chain, `Engine.upk`) - not a yoke. Settling
file: `Research/JC3Grab/BMSDK_OFFSETS.json` plus an `SVehicleWheel` archetype payload; but no file
makes a driver yoke exist. The asset gap is settled by `Research/BatmobileGrab/COCKPIT.md` §1/§4.

**Pilot card.** "Turn lock to lock in the cockpit: a yoke rotates with `steering_turn`, or the build
declares the yoke absent instead of shipping a static wheel."

---

## 9. Group H - module arrays and members the writer omits (not a part gap)

| item | writer behaviour | why | closing step |
|---|---|---|---|
| `aim_part_constraints[]` | written **empty** (`bm_parts.py`) | 85 rows in 17 of 78 modules, all suspension, **0 on six turreted vehicles**; turret/cannon aim is a Havok hinge, not this array | B-04 keeps it empty; no payload required |
| `door_parts[]` for P-06/P-07/P-08 | **omitted** entries | the rows carry a door channel but `part: null`, so no part index can reference them | B-02 face cut -> B-04 row |
| `hinged_parts[]` for P-13 | **omitted** | no part and no bone | B-02 new part -> B-04 row |
| `rotating_parts[]` for P-05 | **omitted** | `joint: null`, no axis | axis sourced (Group C) -> B-04 row |
| hinge rate | **no member** | `all_hinged_part_properties` has `lod`, `target_position_variable`, `use_target_position_as_angle` only | none; rate is code |

Evidence: **decoded** (`bm_parts.py` `omitted[]`, `aim_note`; `MOVING_PARTS.md` §1).

---

## 10. Build-step summary

| step | closes | evidence level |
|---|---|---|
| **B-02 step 1** (face cut per part) | P-06 canopy, P-07/P-08 covers, P-13 yoke | **decoded** face ownership (`parts_manifest.json`, `SPLIT_FACES.md`); no new numbers |
| **B-04 step 3** (behaviour arrays) | P-03 `rotating_parts` (axis `[0,0,-1]`, 6 turns/3.9 s); P-09…P-12 `hinged_parts` (`air_brakes_T`); P-06/P-07/P-08 `door_parts` after the cut; P-13 `SteeringWheel` after the part | **decoded** behaviour tables; row numbers above |
| **B-04 + hinge append** (`constraint_index`, `hkpLimitedHingeConstraintData`) | P-01 index 11 (-60…60°), P-02 index 12 (-5…20°), P-04 chosen line; P-06/P-07/P-08/P-09…P-12 hinges | **decoded** offsets/classes (`JOINT_FIELDS.md`); P-04 line **UNKNOWN** |
| **B-04 rotating row for P-05** | P-05 `EngineRotatingPart` | axis **UNKNOWN** until a carrier row is decoded |
| **B-05** (`CPartProp` per new part) | only after B-02/B-04 create the part (canopy, covers, yoke) | **decoded** (`GRAB_BACKLOG.md` B-05) |

---

## 11. UNKNOWN register

| # | UNKNOWN | settles it |
|---|---|---|
| 1 | hinge rate (all groups) | no JC3 member; code-side probe |
| 2 | P-04 which line the part turns about | Q-1 pod probe / operator decision |
| 3 | canopy lift mechanism (72.481 cm) | fleet scan of part modules for a translating door; `MOVING_PARTS.md` shows none |
| 4 | hatch and air-brake carrier hinge limits | `Research/JC3Grab/TURRET.json` extended to `v5603_train_urga_monorailmissilecar` and `v4602_plane_urga_fighterbomber` |
| 5 | jet spin axis | decoded `rotating_parts[]` row of `v0506_car_solar_oldtractor`, or `BONES.json` bind orientation + turbine geometry normal |
| 6 | `rotoscope_rpm_per_cycle` 20.0 meaning | no JC3 file defines it; in-game probe |
| 7 | yoke geometry / bone | `Research/BatmobileGrab/COCKPIT.md` (absent) and `BONES.json` (0 matches) |
| 8 | Vulcan land proof / damage type | fleet has `GatlingGun` only on `CBoat`/`CHelicopter`; a land probe or a decoded land carrier settles it |

## 12. Reproduce the row evidence

```bash
python Tools/scripts/t12_parts.py --check
python Tools/scripts/parts_anim_coverage.py --check
python -c "import json;d=json.load(open('Working/Translation/T8_PARTS.json'));print(d['summary']);print([r['id'] for r in d['rows'] if r.get('joint') is None])"
```

Read-only: this plan changes no row, no module and no build.
