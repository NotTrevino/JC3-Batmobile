# Moving fins: aero surfaces in BmAK and how to drive them in JC3

**Question.** Find whether BmAK raises or tilts any aero surface with speed or mode, with the angle
and timing. Then locate a JC3 vehicle part that animates a surface by speed (aircraft flaps, a
deploying spoiler) and say how we drive our fins from it.

**Verdict in one paragraph.** BmAK **tilts** four aero flaps — it never raises a fin by speed, and
no speed member is involved at all. Each flap is a skeletal part on its own pivot plus two piston
linkage bones, animated by the `Batmobile_V2_Pose_States` clips `Batmobile_V2_Aero_Flap_{L,R}_{Up,
Down}`: a **26-frame clip with a recorded length of 0.833 s** at RateScale 30.00, front flap travel **20.01°**, rear **29.99°**, peak rates
**37.2 °/s** and **56.9 °/s**, all about the part's local +Z. The project's own driving variable for
all four is **`air_brakes_T`** (`T8_PARTS.md` P-09…P-12) — the air-brake channel, fired by heavy
braking — with a second clip `Batmobile_V2_Jet_Boost` (19 frames, 0.600 s, 21 bones) for the boost
pose. On the JC3 side there is **no speed→surface member anywhere in the decoded data**: the two
candidate behaviours are `Flaps` (202 parts, 23 entities, 8 chassis, `flaps_T`, **proven on `CCar`**)
and `AirBrake` (3 parts, one chassis — `v4602_plane_urga_fighterbomber`, `CAirPlane` — **unproven on
a car**), and a search for `spoiler` in the JC3 research returns **zero** hits. Both are hinged parts
whose travel lives not in the module but in the `.physicsc` `hkpLimitedHingeConstraintData`, and
whose input is a 0..1 vehicle variable (`use_target_position_as_angle = 0` on every `Flaps`/
`AirBrake` row). So the drive is: keep the four parts the build already has (56–59), point each at a
real limited hinge with a ±20° / ±30° range, and let `air_brakes_T` index it — reproducing BmAK's
0.833 s by moving that variable 0→1 in 0.833 s.

---

## 0. Premise checks (per `AGENTS.md`, stated before the evidence)

| # | premise as asked | what the files show |
|---|---|---|
| P-1 | "raises **or tilts**" | **Tilts.** The Jourdain part bone's rotation range is 0→20.01° (front) and 0→29.99° (rear) about local +Z (`Working/Translation/T8_PARTS.md` P-09…P-12); there is no translation of the part bone in either clip. |
| P-2 | "**with speed or mode**" | **Neither, as a data member.** No speed- or mode-valued member appears in any fin row. The driving variable is `air_brakes_T` (`T8_PARTS.md` P-09/P-10/P-11/P-12, all four). The `BattleMode*` family in `Research/BatmobileGrab/MODES.md:83-95` contains no fin/flap/aero member. |
| P-3 | "a JC3 part that animates a surface **by speed**" | **No such binding is decoded.** `flaps_T` / `air_brakes_T` are vehicle-state variables; `Research/JC3Grab/MOVING_PARTS.md:44-46` says only *"the animation system writes it, the behaviour reads it"* — what writes `flaps_T` is code, and this project does not read the executable. The behaviour rows and their carrier proof are below; the speed input is a **named UNKNOWN**. |
| P-4 | "a deploying **spoiler**" | **Named absence.** No `spoiler` token in `Research/JC3Grab` (search for `air_brakes\|flaps_T\|spoiler\|downforce`: 14 matches, none a spoiler). JC3's closest names are `Flaps` and `AirBrake`. |

---

## 1. BmAK: the four flaps, measured

### 1.1 The parts and their bones

`Research/BatmobileGrab/BONES.md:210-221` (skeleton `Batmobile_V2`, 180 bones):

| bone | parent | bind pos (m) | note |
|---|---|---|---|
| `Batmobile_Rig_Aero_Flap_L_F` | `Batmobile_Chassis` | −1.208, 1.367, −0.918 | front-left flap pivot |
| `Batmobile_Rig_Aero_Flap_R_F` | `Batmobile_Chassis` | +1.208, 1.367, −0.918 | front-right flap pivot |
| `Batmobile_Rig_Aero_Flap_L_B` | `Batmobile_Chassis` | −1.209, 1.800, 1.251 | rear-left flap pivot |
| `Batmobile_Rig_Aero_Flap_R_B` | `Batmobile_Chassis` | +1.209, 1.800, 1.251 | rear-right flap pivot |
| `…_L_F_Piston_Top` | `…_L_F` | −1.155, 1.358, −0.798 | linkage, child of the flap |
| `…_L_F_Piston_Btm` | `Batmobile_Chassis` | −1.048, 1.407, −0.460 | linkage, child of the body |
| `…_R_F_Piston_Top` / `_Btm` | mirror | — | idem |
| `…_L_B_Piston_Top_001` | `…_L_B` | −1.200, 1.852, 1.641 | idem |
| `…_L_B_Piston_Btm_001` | `Batmobile_Chassis` | −1.208, 1.890, 2.001 | idem |
| `…_R_B_Piston_Top_001` / `_Btm_001` | mirror | — | idem |

There is also a separate **jet-fin** bone, not one of the four flaps:
`Batmobile_Rig_Jet_Fins` (#61, parent `Batmobile_Rig_Jet_Root`, at 0.000, 0.544, 2.354;
`BONES.md:103`). It is the fin that `FinTrail0` (`ASSETS.md:310`) rides on and it is not in the
`fins/air-brakes` clip set's moved-bone list for the flap clips.

### 1.2 The angles (per part, from the animation data)

`Working/Translation/T8_PARTS.md` P-09…P-12, cross-checked in
`Working/Translation/PARTS_ANIM_COVERAGE.md:39-42` (joint range per sequence = 25.763° front,
54.787° / 54.799° rear — that is the **piston-top child**, not the part pivot; T-8 records both):

| part (T-8 id) | part pivot rotation | max rate | piston-top child | piston-btm child |
|---|---|---|---|---|
| `batmobile_aero_flap_l_f` (P-09) | **−0.003 … +20.007°** about +Z | **37.20 °/s** | −18.352 … 7.465° at 48.70 °/s | −95.207 … −89.006° at 11.92 °/s |
| `batmobile_aero_flap_r_f` (P-10) | **−20.008 … +0.002°** about +Z | 37.20 °/s | −18.352 … 7.465° at 48.71 °/s | −90.994 … −84.793° at 11.92 °/s |
| `batmobile_aero_flap_l_b` (P-11) | **+0.003 … +29.989°** about +Z | **56.85 °/s** | −48.864 … 5.926° at 106.14 °/s | −18.877 … 5.925° at 51.67 °/s |
| `batmobile_aero_flap_r_b` (P-12) | **−29.999 … +0.006°** about +Z | 56.60 °/s | −48.826 … 5.973° at 105.82 °/s | −18.877 … 5.925° at 51.67 °/s |

The left/right signs are mirrored (L goes +, R goes −), i.e. the pair opens outward — the pose is a
**tilt of an air-brake panel**, not a lift of a wing. The `_Piston_Top`/`_Piston_Btm` figures are the
dog-leg linkage that drives it; a hinge cannot reproduce a linkage
(`JOINT_FIELDS.md` §5 and `T8_PARTS.md` "What the files do not give" #3), so the linear actuator is
expected to stay static on the port.

**Axis caveat, quoted rather than resolved.** T-8 prints e.g. *"turns about its local +Z
([-0.0, 1.0, -0.0] in JC3 space)"* — the stated local axis (+Z) and the bracketed JC3 vector (+Y)
disagree. That is T-8's own text, not a transcription of a decoded label; the hinge axis must be
confirmed against the `.rbm` pivot before it is written (`JOINT_FIELDS.md` §6 makes the same point
for the turret: *"the frame of the constraint pivot/axis … is not proven"*).

### 1.3 The timing

`Research/BatmobileGrab/ANIMATIONS.md:109-112` (and the MK2/Funhouse repeats at `:146-149`,
`:183-186`):

| clip | frames | length | RateScale | bones | mechanism | notifies |
|---|---|---|---|---|---|---|
| `Batmobile_V2_Aero_Flap_R_Down` | 26 | **0.833 s** (stored length; 26 frames at RateScale 30.00) | 30.00 | 26 | `fins/air-brakes` | 1 |
| `Batmobile_V2_Aero_Flap_R_Up` | 26 | 0.833 s | 30.00 | 7 | `fins/air-brakes` | 1 |
| `Batmobile_V2_Aero_Flap_L_Down` | 26 | 0.833 s | 30.00 | 7 | `fins/air-brakes` | 1 |
| `Batmobile_V2_Aero_Flap_L_Up` | 26 | 0.833 s | 30.00 | 9 | `fins/air-brakes` | 1 |
| `Batmobile_V2_Jet_Boost` | 19 | **0.600 s** | 30.00 | 21 | `fins/air-brakes` | 0 |

The mechanism class is defined by the bones it moves: *"`fins/air-brakes` - `Aero_Flap*` /
`Jet_Fins`"* (`ANIMATIONS.md:57`), and the group totals **20 sequences, 280 active tracks, 252
moved** (`:76`) — the second-largest moving mechanism after `transformation`.

Derived averages from the two numbers above (arithmetic, not a stored value):

- front flap: 20.007° in 0.833 s = **24.0 °/s average**, 37.2 °/s peak (the clip is eased);
- rear flap: 29.989° in 0.833 s = **36.0 °/s average**, 56.9 °/s peak.

### 1.4 Is it speed, mode, or brake?

| candidate trigger | evidence for | evidence against | verdict |
|---|---|---|---|
| **speed** (continuous) | nothing in the fin rows | no speed-valued member on the part, the bones or the clips; the speed-scaled member in `MODES.md` is `BattleModeVSpeedCurve` (a *steering* curve, `:83`), not a fin input | **no** |
| **mode** (pursuit↔battle) | the pose delta is non-zero: pursuit→battle moves each flap bone ~0.040–0.068 m / **0.54°** (`T8_PARTS.md` P-09…P-12, `pose delta (G1-12)`) | 0.54° is negligible; the `BattleMode*` family carries no fin member (`MODES.md:83-95`) | **no** — the mode only shifts the bind pose |
| **air brake / braking** | each of the four rows' driving variable is **`air_brakes_T`** (`T8_PARTS.md` P-09…P-12); the verify line is *"brake hard from 40 km/h. Pass = the flap moves"*; audio ships `Play_Flaps_Open` / `Play_Flaps_Close` in all four packages (`AUDIO.md:83-84`, `AUDIO_FEATURES.md:242-243`) | — | **yes** — this is the intended driver |
| **boost** | the `Batmobile_V2_Jet_Boost` clip is classified `fins/air-brakes` and moves 21 bones including `Aero_Flap*`/`Jet_Fins` | it is a separate clip, not a modifier on the flap clips | **yes, a second pose** (boost) |

The `RAnimNotify_RFlapsBlendWeight` class exists but is **not** a fin driver: its only user is the
Joker cinematic `2Face_Finale` in `Phase2_JK`, at t = 0.3396 s, with the notify's two floats 0.0 and
1.0 (`ANIMATIONS.md:1157`, `objects.jsonl:8618`). It is a cinema flap-weight blend, not a
speed/mode input.

---

## 2. JC3: the carrier

### 2.1 The two behaviours, side by side

`Research/JC3Grab/MOVING_PARTS.md:31-32` (the hinged-part table) and `:97`, `:157` (the proof
columns):

| behaviour | `target_position_variable` | `lod` | `use_target_position_as_angle` | parts | entities | chassis | classes | proof |
|---|---|---|---|---|---|---|---|---|
| **`Flaps`** | **`flaps_T`** | 1 | **0** | **202** | 23 | 8 | `CAirPlane`, **`CCar`** | **proven-on-CCar** |
| **`AirBrake`** | **`air_brakes_T`** | 1 | 0 | 3 | 3 | 1 | `CAirPlane` | **unproven-on-CCar** |

`AirBrake` is exactly three parts on one chassis — `v4602_plane_urga_fighterbomber`
(`MOVING_PARTS.md:173`: *"AirBrake is the only behaviour the card names as a Q-1 probe: 3 parts on 1
chassis … and nothing on land"*). `Flaps` is on 8 chassis including cars, which is the only decoded
evidence that a **ground vehicle** part can be animated from a flap variable.

`FEATURE_CENSUS.md:263-264` confirms the same two rows from `vehicle_common.vmodl` itself, and
`VOCABULARY.md:1357-1362` gives the full 25-row hinged table (only `SteeringFork` sets
`use_target_position_as_angle = 1`; every flap/air-brake row is `0`).

### 2.2 What "the behaviour reads it" means numerically

`MOVING_PARTS.md:44-46`: *"The variable is a float in the vehicle's own state: the animation system
writes it, the behaviour reads it. `SteeringFork` is the only row that sets
`use_target_position_as_angle`; every other row takes the variable as a 0..1 position."*

So on the JC3 side the flap's angle is **not** a module field:

| quantity | where it lives | evidence |
|---|---|---|
| **when** it moves | the vehicle variable `flaps_T` / `air_brakes_T` (0..1) | `MOVING_PARTS.md:44-46`; member `all_hinged_part_properties[].target_position_variable` (`VOCABULARY.md:1360-1361`) |
| **how far** it moves | the **Havok limited hinge** in the vehicle's `.physicsc` | `JOINT_FIELDS.md` §1: `+0x30` axis (float4), `+0x60` pivot (float4, m), `+0xFC` min rad, `+0x100` max rad, 304-byte `hkpLimitedHingeConstraintData` |
| **how fast** it moves | **nowhere in data** — no rate member | `T8_PARTS.md` UNKNOWN #2; `PARTS_ANIM_COVERAGE.md:74`; `JOINT_FIELDS.md` §6 |
| **which part** | `parts[i].constraint_index` (int32) → position in the `.physicsc` constraint list | `JOINT_FIELDS.md` §2 |

`hinged_parts[]` is **not** usable for limits: it stores only a part index
(`JOINT_FIELDS.md` §5, `MOVING_PARTS.md` §3).

### 2.3 Named absence: spoiler

No `spoiler` token anywhere in `Research/JC3Grab`. The nearest names are `Flaps`, `AirBrake`,
`LeftAileron`/`RightAileron` (`steering_roll`), `Elevator` (`steering_pitch`), `Rudder`
(`steering_yaw`) — all aircraft-only except `Flaps`. `all_fin_part_properties` holds exactly one
name, `BoatRudder` (`MOVING_PARTS.md:79-80`), with nothing but a name and hash, so "fin" in JC3 is
not a behaviour at all.

---

## 3. How we drive our fins from it

### 3.1 What the build already has

The four flaps are already real parts in the parts module, at indices **56–59**:

```
bm_vehicle_parts.json:132-135   "batmobile_aero_flap_l_f": 56, "..._r_f": 57,
                                "..._l_b": 58, "..._r_b": 59
bm_vehicle_parts.json:824-848   name batmobile_aero_flap_l_f, model
                                models/…/batmobile_aero_flap_l_f.lod, LOD1..5 .rbm
```

T-8 already assigns behaviour `AirBrake` and variable `air_brakes_T` to all four, with
`damage_type` `Plane_Control_Surface` and *"one RBM per LOD at the same pivot; the part is cut in
every LOD the build writes (LOD1..5)"* (`T8_PARTS.md` P-09…P-12).

### 3.2 The change list

| # | file / object | change | why this is the right place |
|---|---|---|---|
| 1 | `…/batmobile_vehicle_parts.vmodc`, parts 56–59 | set `constraint_index` to the four new hinge objects' ordered indices (not −1) | `bm_parts.py` writes −1 today (`JOINT_FIELDS.md` §5); a −1 part has no joint to animate |
| 2 | the vehicle's `.physicsc` | append **4** `hkpLimitedHingeConstraintData` (304 B): axis = the flap pivot axis, pivot = the part's `pivot_m`, min/max = the angles below | `JOINT_FIELDS.md` §1/§2 — the only class the fleet uses for a limited hinge |
| 3 | same four part rows | `target_position_variable` = **`air_brakes_T`** (keep T-8's choice), `use_target_position_as_angle` = **0** | `MOVING_PARTS.md:44-46` — 0 means "0..1 position", which is what the air-brake variable is; setting 1 would treat it as radians and fight the hinge |
| 4 | optional, if `air_brakes_T` proves dead on a `CCar` | switch the four rows' behaviour to **`Flaps`** / `flaps_T` | `Flaps` is the only surface behaviour **proven on `CCar`** (8 chassis); `AirBrake` is 1 plane (`MOVING_PARTS.md:97`, `:157`) |

### 3.3 The hinge numbers

| part | axis (to confirm) | min rad | max rad | span |
|---|---|---|---|---|
| `batmobile_aero_flap_l_f` | +Z (see §1.2 caveat) | −0.000052 (−0.003°) | **+0.349142 (+20.007°)** | 20.01° |
| `batmobile_aero_flap_r_f` | +Z | **−0.349211 (−20.008°)** | +0.000035 (+0.002°) | 20.01° |
| `batmobile_aero_flap_l_b` | +Z | +0.000052 (+0.003°) | **+0.523410 (+29.989°)** | 29.99° |
| `batmobile_aero_flap_r_b` | +Z | **−0.523584 (−29.999°)** | +0.000105 (+0.006°) | 30.00° |

Radians = degrees × π/180 (the only unit bridge `JOINT_FIELDS.md` §1 uses). The stored values are
float32; write the float32 rounding (`0.3491423…`, `0.5234104…`), not the printed decimal.

### 3.4 The timing → the variable

There is no rate member, so the 0.833 s is expressed as **how fast the variable travels 0→1**:

| BmAK fact | JC3 expression |
|---|---|
| **0.833 s** stored clip length (26 frames, RateScale 30.00) | `air_brakes_T` must go 0→1 in **0.833 s** (the state machine's ramp, code-side) |
| front peak 37.20 °/s, average 24.0 °/s | 20.007° / 0.833 s; a linear 0→1 ramp gives the average, an eased ramp gives the peak |
| rear peak 56.85 °/s, average 36.0 °/s | 29.989° / 0.833 s |
| boost pose `Jet_Boost`, 0.600 s | a second target value on the same variable (the boost state), not a second hinge |

If `air_brakes_T` turns out to be a boolean-ish 0/1 flip on a car, the 0.833 s cannot be reproduced
from data at all — that is the honest fallback, and it is testable in one drive (§5 #1).

### 3.5 The check the build must pass

| # | check | pass condition |
|---|---|---|
| 1 | parts 56–59 `constraint_index` | each is in `0…N-1` of the **final** `.physicsc` object order (recomputed after appending, never hardcoded — `JOINT_FIELDS.md` §2/§4) |
| 2 | hinge round-trip | re-read `+0x30/+0x60/+0xFC/+0x100` and equal the table in §3.3 within float32 |
| 3 | module walk | every other part row byte-identical (the B-04 rule: "every other ADF row unchanged (full walk)") |
| 4 | in-game | brake hard from 40 km/h: each flap tilts through its span and returns; boost: the `Jet_Boost` pose plays (T-8's own verify line for P-09…P-12) |

---

---

## 4. What is UNKNOWN, and the cheapest test

| # | UNKNOWN | why | 5-minute test |
|---|---|---|---|
| 1 | whether `air_brakes_T` is fed on a `CCar` at all | the writer is code; `AirBrake` is proven only on `CAirPlane` (`MOVING_PARTS.md:157`) | drive the current build, brake hard, watch parts 56–59 |
| 2 | the hinge axis frame (local +Z vs the bracketed JC3 +Y) | T-8's own text disagrees with itself (§1.2) | one hinge at +Z, one at +Y, same drive, keep the one that tilts correctly |
| 3 | the flap's rotation rate on the JC3 side | no rate member (`T8_PARTS.md` UNKNOWN #2) | time the flap from the in-game drive against 0.833 s |
| 4 | whether `flaps_T` or `air_brakes_T` is speed-derived | no decoded writer | not a data question; the variable's source is in the executable |
| 5 | what `RAnimNotify_RFlapsBlendWeight` blends | only one user, a cinematic (`ANIMATIONS.md:1157`) | irrelevant to the car; skip unless the cinema is ported |

## 5. Files this report touched

Only this file. No `.vmodc`, `.physicsc`, `.epe`, `Builds/` tree or game install was modified. The
three earlier reports (`health-damage-states-plan.md`, `cameras-per-mode-plan.md`,
`surface-skids-and-tracks-plan.md`) are unchanged.

**Revert.** Delete this file. If any §3 change is later written, revert it by restoring the
pre-build `.vmodc`/`.physicsc` from the build receipt's sha256 manifest and re-running
`bm_parts.py --check` (the same recipe B-09 uses for its private module).
