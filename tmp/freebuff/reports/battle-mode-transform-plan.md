# Battle (tank) mode transformation — what moves, by how much, in how long, and what JC3 can carry

**Question:** which `BmAK` body parts move when the Batmobile switches driving → battle, over which
bones, how far and for how many seconds; which JC3 vehicle transform moves a skeleton the same way;
how our private entity would trigger it.

**Verdict, in one paragraph.** The BmAK transform is a **2.000 s skeletal clip of 61 frames** in
which **180/180 bones change world transform and 64 articulate**, the largest world travel being
**1.081 m** (`Riot_Sup_Main`), the largest rotation **179.995°** (`Machine_Gun_01` flip), the chassis
settling **−0.050 m** and the weapons mast rising **+0.633 m in pure translation**. **No JC3 vehicle
transform moves a skeleton, because no JC3 vehicle has an animation or skeleton module at all** (0
`jc_skeletons/vehicles/*.bsk`, 0 `jc_statemachine/vehicles/*`, no animation module among the 52
module types). The closest thing in kind is **landing-gear retraction** (`LandingGear` →
`landing_gears_T`, 114 parts / 25 entities / 7 chassis), a one-scalar, whole-subassembly pose change
built from **rigid hinged parts**. The decisive consequence for us: JC3 hinges rotate only — the
turret's 0.633 m **lift is translation**, so it cannot be a hinged part at all, and the pose must be
carried either by two entity variants or by hinged rotations that leave the mast at one height.

Labels: **decoded** = read in the cited file at the cited field; **derived** = arithmetic over
decoded inputs; **UNKNOWN** = searched and absent, with where it would be settled.

---

## 1. The clips that are the transformation (decoded)

From `Research/BatmobileGrab/ANIMATIONS.json` (`sequences[]`, fields `sequence_length`,
`num_frames`, `active_bone_count`, `moved_bone_count`, `max_translation_cm`,
`max_rotation_deg`) and `ANIMATIONS.md` §4. Every number below is identical in all four packages
(`Playable_Batmobile_SF`, `MK2`, `Funhouse`, `Joker`), so the transform is one asset shipped four
times.

| package label | set | sequence | frames | length | rate | active tracks | moved tracks | max translation | max rotation |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Batmobile / MK2 / Funhouse / Joker | `BM_Batmobile_Chassis` | `Drive_To_Combat` | 61 | **2.000 s** | 30.0 | 75 | 73 | 69.7866 cm | 179.995° |
| Batmobile / MK2 / Funhouse / Joker | `Batmobile_V2_Pose_States` | `Batmobile_V2_Tank_Spread_Open_Game` | 61 | **2.000 s** | 30.0 | 70 | 69 | 69.783 cm | 179.995° |
| Batmobile / MK2 / Funhouse / Joker | `Batmobile_V2_Pose_States` | `Batmobile_V2_Tank_Spread_Close_Game` | 61 | **2.000 s** | 30.0 | 70 | 69 | 69.783 cm | 179.995° |
| Batmobile / MK2 / Funhouse / Joker | `Batmobile_V2_Pose_States` | `Batmobile_V2_Tank_Spread_Open` | 61 | **2.000 s** | 30.0 | 74 | 73 | 69.783 cm | 179.995° |
| Batmobile / MK2 / Funhouse / Joker | `Batmobile_V2_Pose_States` | `Batmobile_V2_Tank_Spread_Close` | 61 | **2.000 s** | 30.0 | 74 | 73 | 69.783 cm | 179.995° |

* **Duration is 2.000 s** (`(61 − 1) / 30`); the measured endpoint pair in `POSES.md` is frame 0 →
  frame 60 = **1.967 s**. Open and Close are the same length; `Drive_To_Combat` (the chassis-set
  clip) is the same length again.
* `Drive_To_Combat`, `Spread_Open` and `Spread_Close` carry **3 notifies** each in the non-Game
  variants, **15 / 12** in the `_Game` variants (`ANIMATIONS.md` §4) — sound/script cues on the
  timeline, not motion.
* The two `_Game` clips are the gameplay pair: `POSES.md` loop check open-start vs close-end
  **0.054 cm / 0.026°**, open-end vs close-start **0.054 cm / 0.024°**, i.e. the same pose set.
* `max_translation_cm` (69.79 cm) is the largest **single-channel** displacement; the largest
  **world** travel in the pose is 1.081 m (§2), because a parent's rotation swings a child further
  than any one channel moves. Both are reported rather than reconciled into one number.

---

## 2. Which bones move, and how far (decoded)

Source for every figure in this section: `Research/BatmobileGrab/POSES.md`, "Every bone delta"
(180 rows, pursuit frame 0 → battle frame 60 of `Batmobile_V2_Tank_Spread_Open_Game`), plus
`ANIMATIONS.json` `moved_bones` for the `Drive_To_Combat` peak values. World travel is in JC3
metres (X width, Y up, Z length, nose −Z); "local" is parent-relative and is what actually
articulated.

### 2.1 The whole-body numbers

| quantity | value |
|---|---:|
| bones that move (world ≥ 0.5 mm or ≥ 0.05°) | **180 / 180** |
| bones that articulate (parent-relative change) | **64** |
| bbox 3.495 × 2.341 × 7.026 m → | **4.691 × 2.865 × 7.443 m** (+1.196 W, +0.524 H, +0.418 L) |
| chassis vertical settle | **−0.050 m** (local, 0.54°) |
| turret/mast rise | **+0.633 m in pure translation** (local rotation 0.00°) |
| largest world travel of any bone | **1.0813 m** (`Batmobile_Rig_Weapons_Riot_Sup_Main`) |
| largest local rotation | **179.99°** (`Batmobile_Rig_Weapons_Machine_Gun_01`) |
| wheels splay (toe, about vertical) | **19.31° / 19.32° front, 18.01° / 17.27° rear** |
| aero fins | **0.000°** — the spread transition does **not** deploy them |

The 116 bones with no local change ride a parent (121 of the 180 are rigid children of the mast or
the chassis). The table below groups the 64 that articulate and the children that travel furthest.

### 2.2 Grouped, with the exact travel

| group (bones) | world Δ (m) | local rotation | what it is |
|---|---:|---:|---|
| **Weapons mast** — `Weapons_Trans`, `Turret_Top`, `Turret_Top_Slide` | **0.6350 / 0.6335 / 0.6335** (+0.634, +0.633, +0.633 **Y**) | 0.00° | the lift — translation only |
| `Weapons_Top_Sides_Root` | 0.6477 | 0.00° | rides the mast |
| `Weapons_Drone_Decoder_Arm` / `_Decoder` | 0.7441 / 0.7440 | 0.00° | rides the slide |
| `Weapons_Heavy_Shells` | 0.6311 | 0.00° | rides the mast |
| `Weapons_Riot_Suppressor_Root` | 0.6917 | 0.00° | rides `Top_Sides_Root` |
| **`Weapons_Riot_Sup_Arm_01`** | 0.7183 | **120.00°** | riot arm swings out |
| **`Weapons_Riot_Sup_Main`** (+ `_Ammo`) | **1.0813** | **59.98°** | the furthest-travelling bone in the car |
| **`Machine_Gun_01`** / `_02` / `_Root` | 0.9279 / 1.0122 / 0.9279 | **179.99°** (01) | gun flips over and rises |
| `Weapons_Sides_Root` (+`_01`) | 0.2477 (0.5655) | 0.00° | side pods rise with the mast |
| `Weapons_Turret_Armour`, `R/L_Power_Cell` | 0.2477 / 0.2425 | 0.00° | ride |
| **Mine covers ×4** (`Projectile_Mine_Cover_01…04`) | 0.6283–0.6323 | **65.00°** | four bay lids open |
| `Projectile_Mine_01…04` | 0.6817–0.6857 | 0.00° | rounds ride the lids |
| **Missile pods** `Missiles_L_T/L_Mid/L_B` and R | 0.0446 / 0.1205 / 0.0367 | **15.00°** each | bay lids tilt |
| missile rounds (`_01`…`_04`, both sides) | 0.1317–0.1471 | 0.00° | ride |
| shells (`R_Shell_*`, `L_Shell_*`, tweens, chambers — 28 bones) | 0.6343–0.6355 | 0.00° | ride the raised turret |
| **Front wheels** `SUSP1_Wheel_Front_L/R` | 0.0376 | **19.32°** | splay pivot |
| `SUSP2_Wheel_Front_*` → `Wheel_Parent_F_*` → tyre/fan/disc | 0.2518 → **0.5661 / 0.5660** | 0.03° | whole corner swings out ~0.57 m |
| `Damper_Left_Front_02`, `L_F_Wheel_Armour(001)` | 0.7360, 0.6479, 0.4780 | 0.00° | ride the corner |
| **Rear wheels** `SUSP1_Wheel_Rear_L/R` | 0.3704 / 0.3709 | **18.01° / 17.25°** | splay pivot |
| `Wheel_Parent_B_L` / `_B_R` → tyre/fan/disc | **0.5631 / 0.5466** | 0.01–0.02° | rear corners swing out |
| `Power_Cell_Root` / `_Core` / `_Glass` | 0.3305 / 0.3054 | 0.00° | ride the rear-left corner |
| **Rear wheel arches** `Chassis_L/R_REAR_WHEEL_ARCH` | 0.6132 / 0.6133 | **28.36° / 28.35°** | arch doors swing |
| arch arms `…_Arm_LB/RB`, `L/R_B_Wheel_Armour_001` | 0.4534 / 0.4532, 0.6132 | 0.00° | ride |
| **`L/R_B_Wheel_Armour_002`** | **0.8084 / 0.8082** | 0.00° | furthest body bone after the riot assembly |
| **Cockpit armour** `R_01/L_01` → `R_02/L_02` | 0.3603 → **0.6672** | **1.41° → 5.10°** | cheek plates open |
| `JetSMove` / `Jet_Root` / 18 nozzles / `Thruster` / `Jet_Fins` | 0.1279 / 0.0794 / 0.0836–0.0861 / 0.0893 | **20.00°** nozzles | nozzle ring tilts 20° — this is shared with driving clips, not a battle tell |
| `CockPit_Mesh`, `Nose_Mesh`, `Winch_Door`, `Rear_Door_*`, chair bones, `Sonar` | 0.0226–0.0791 | 0.00° | rigid ride on the chassis |
| `Aero_Flap_*` (13 bones) | 0.0402–0.0683 | **0.00°** | **do not deploy in this clip** |

`Drive_To_Combat`'s own `moved_bones` list agrees in rank order — `Weapons_Top_Sides_Root`
**69.7866 cm**, `Weapons_Trans` **68.5117 cm**, `Heavy_Shells` **68.1255 cm**, then
`Riot_Sup_Main` **10.074 cm at 104.48°**, `Riot_Sup_Arm_01` **11.146 cm at 123.92°**,
`Wheel_Parent_*` **82–85°**, `Machine_Gun_01` **179.995°**, mine covers **65.0°**.

**Read this carefully, it decides the JC3 plan:** of the four big visible motions, three are
rotations (riot arm 120°, machine gun 180°, arches 28°) and **one is pure translation** (the mast's
+0.633 m). A JC3 hinged part has an axis, two angle limits and a scalar angle (`DOOR_ANGLES.md`
§1 hop 5) — it cannot slide.

---

## 3. The JC3 candidates, tested

### 3.1 There is no JC3 vehicle skeleton to move (decoded)

| claim | evidence |
|---|---|
| a vehicle entity has no animation module | `Research/JC3Grab/SEAT.md` §1: "A JC3 vehicle entity has **no seat, occupant, pose or animation module**" — 31 `.vmodc` modules in the donor, 52 module types in the vocabulary, none about animation |
| there are no vehicle skeletons | `SEAT.md` table: `jc_skeletons/vehicles/*.bsk` **0 files**, `jc_statemachine/vehicles/*` **0 files**; **3 skeleton files in total**, **7 vehicle `.ban` clips** (and those are Rico's seat clips) |
| no module named `*Mode*` / `*Transform*`; no animation-node member | `tmp/freebuff/reports/mode-switch-carriers.md` §2.7 and U5 |
| vehicle geometry is many rigid meshes, not a skinned body | `Research/JC3Grab/GEOMETRY.md`: **56,136 meshes / 77,611 blocks across 233 entities** (~240 mesh blocks per vehicle) |

**Therefore: no JC3 vehicle transform moves a skeleton the same way — no JC3 vehicle moves a
skeleton at all.** Everything that changes a vehicle's shape in JC3 is a rigid part on a Havok
hinge or a variable-driven part transform.

### 3.2 What actually moves, and how it is driven (decoded)

`Research/JC3Grab/MOVING_PARTS.md` §1 (`vehicle_common.vmodc`, the fleet's only copy):

| behaviour | driving variable | parts | entities | chassis | proven on a `CCar`? |
|---|---|---:|---:|---:|---|
| `LandingGear` | `landing_gears_T` | 114 | 25 | 7 | **no** (all `CAirPlane`/`CHelicopter`) |
| `LandingGearHatch` | `hatches_T` | 76 | 19 | 5 | **no** |
| `Flaps` | `flaps_T` | 202 | 23 | 8 | **yes** |
| `AirBrake` | `air_brakes_T` | 3 | 1 (`v4602_plane_urga_fighterbomber`) | 1 | **no** |
| `SteeringFork` | `steering_angle_inverted` | 27 | 27 | 11 | **yes** — the only row with `use_target_position_as_angle = 1` |
| `LeftWing` / `RightWing` | door table, **name only** | 9 each | 9 | 4 | **no** |

Door-type parts get their range from `.physicsc`: `hkpLimitedHingeConstraintData`, **min at
+0x0FC, max at +0x100 in radians** (`DOOR_ANGLES.md` §1). There is **no rate/speed member** in
`all_hinged_part_properties` (`anim-sequences-coverage.md` UNKNOWN 3), so **a JC3 hinge has no
authored duration** — its timing is whatever the sim ramps the variable at, and the code that
writes any of these variables is **not in any file read** (`MOVING_PARTS.md` §4 limits).

### 3.3 The four candidates the question names

| candidate | what the files say | matches the BmAK transform? |
|---|---|---|
| **"Chaos jet/tank swap"** | no such vehicle exists in the fleet: 233 entities, no entity swaps chassis; the same chassis in another state ships as **another `.ee`** (`_signature_shielded`, `_military_01`) — `mode-switch-carriers.md` §2.5, §2.7 | **absent from our files** — UNKNOWN as a JC3 asset, not merely unmodelled. Nothing to copy. |
| **Bavarium tank** `v0202_car_capstone_bavariumtank` | 1 door (`bavariumtank_hatch`, `FrontLeftDoor`, **0..130°**, `DOOR_ANGLES.md`); `BavariumShield` is a part behaviour (26 parts / 14 entities / 4 chassis) and is **damage, not motion** (`mode-switch-carriers.md` §2.2) | **no** — one door and a shield; its `LandGlobal` values do not change while the shield is up |
| **Landing gear** | `LandingGear` → `landing_gears_T`, 114 parts over 7 chassis: a whole subassembly rotates about a hinge, driven by **one scalar** | **closest in kind** — one variable, many parts, a bounded pose transition. Not a skeleton, and unproven on a car. |
| **Wing animations** | `LeftWing`/`RightWing` are **door** behaviours (name only, range in `.physicsc`); `Flaps` (202 parts) and `AirBrake` (3 parts) are variable-driven | **partial** — same hinge mechanism, but the BmAK fins measure **0.000°** in this clip, so there is nothing to copy from a wing here |

**Answer to "which JC3 vehicle transform moves a skeleton the same way": none does.** Closest
motion analogue: **landing-gear retraction on an aircraft** (`LandingGear` /
`landing_gears_T`); closest *carrying* mechanism our entity can legally use: **a hinged part row**
(`Flaps` on a `CCar`, proven on 8 chassis, or `SteeringFork` when a literal angle is wanted).

---

## 4. How our private entity would trigger it

### 4.1 What the private entity is today

* Built artefact: `Builds/test-091/v0300_car_kensington_sportsmuscle_civilian_01.ee` (latest; the
  Batmobile-named copy is `Builds/bm-013b/v0300_car_kensington_sportsmuscle_batmobile.ee`).
* Geometry split, from `Working/Appearance/build_parts/parts_manifest.json` — **16 entries**:
  `body`, `wheel_f_l/f_r/r_l/r_r`, `batmobile_turret`, `batmobile_cannon`,
  `batmobile_machine_gun`, `batmobile_riot_suppressor`, `batmobile_missile_pod_l/r`,
  `batmobile_aero_flap_l_f/r_f/l_b/r_b`, `batmobile_jet`.
* So the parts that rotate in the transform are **already cut** (riot suppressor, MG, missile pods,
  turret, flaps). Not cut: the mast itself, the mine covers, the rear arches, the cockpit armour,
  the suspension corners.

### 4.2 Three trigger routes, cheapest first

**Route A — hinged part + driving variable (the only decoded vehicle-shape switch).**
Give the rotating parts a `behavior` that has a `vehicle_common` row and a hinge: `Flaps`
(`flaps_T`, proven on a `CCar`) or `SteeringFork` (`steering_angle_inverted`, the one row that
takes the variable as an **angle** rather than a 0..1 position). Add `hinged_parts[]` index rows to
the private parts module, and author the axis + limits in the private `.physicsc` as
`hkpLimitedHingeConstraintData` (`+0x0FC` min, `+0x100` max, radians).
*Carries:* riot arm **0..120°**, MG **0..180°**, mine covers **0..65°**, missile pods **0..15°**,
wheel splay **0..19°**, arches **0..28°**, cockpit armour **0..5°**.
*Cannot carry:* the mast's **+0.633 m translation** (no prismatic behaviour exists in the 25-row
table), and the 2.000 s duration (no rate member; writer UNKNOWN).
*Blocker:* who writes `flaps_T` on a car is **UNKNOWN** — `MOVING_PARTS.md` §4 states plainly that
which code writes a given variable "is not in any file read here".

**Route B — `ExtendedExposedVariables` expression (the only in-data writer of a variable).**
`Research/JC3Grab/VOCABULARY.md` §`ExtendedExposedVariables`: `variables[].expression`, **2 strings
fleet-wide**, both a speed ramp
(`speed_rom_intensity = 1 - ( speed_rom_time_remaining / speed_rom_total_time )`,
`speed_rom_threshold = speed_ms / speed_rom_speed_threshold`). A private entity can therefore
define a variable from an expression over existing vehicle state. Whether a hinged part's
`target_position_variable` may resolve to such a variable is **UNKNOWN** (the consumer is in the
exe; `mode-switch-carriers.md` U2).

**Route C — two entity variants (the proven carrier of a whole different shape).**
Duplicate the private `.ee` into pursuit and battle copies, each with its own parts/pose values —
the pattern the fleet already uses for `_signature_shielded` and the three Bavarium-tank entities
(`mode-switch-carriers.md` §2.5, §5 Option A). This is the **only** route that carries the mast
lift and the full 4.691 × 2.865 × 7.443 m battle footprint, because it is a different static pose,
not a transition. Its switch (calling the variant swap at runtime) is **UNKNOWN** (U1).

### 4.3 Recommendation

1. **Pose first, transition second.** Build the battle pose as a **variant** (Route C): it is the
   only carrier that reproduces the measured bbox, the +0.633 m mast and the −0.050 m settle. No
   new mechanism, no unknown writer.
2. **Rotation-only in-place version** (Route A) for the parts that genuinely articulate: riot arm
   120°, MG 180°, mine covers 65°, missile pods 15°, wheels 19°/17°, arches 28°, cockpit armour 5°
   — the axes and pivots are already in `Working/Translation/T8_PARTS.md` (T-12), and four of them
   already have shipped hinge limits to copy.
3. **Do not plan a skeletal transition.** JC3 has no vehicle skeleton, no animation module and no
   animation-node member (`SEAT.md`, `mode-switch-carriers.md` U5). `TransformationAnimNode` is
   serialised in no BmAK package either (`T-15` row T-MD13), so there is not even a source clip to
   bind if a node existed.

### 4.4 The 5-minute experiment (before any of the above is built)

Offline, read-only, no game launch (the project has a test ban):
1. Take an existing `CCar` entity that ships `Flaps` (8 chassis do — `MOVING_PARTS.md` §2) and read
   its `hinged_parts[]` row, its `.physicsc` hinge limits and whether any of its 202 flap parts sits
   on the same module as a `ExtendedExposedVariables` variable. That answers "can a car's hinge be
   driven from data" without writing a line.
2. If yes, the build edit is three fields per part (behaviour string, `hinged_parts[]` index, hinge
   record). If no, Route A is dead for a `CCar` and Route C is the whole answer.

---

## 5. What this does to the ledger

Row **T-MD13** ("transformation stance") currently reads `out`: *"the static pose is T-12's part
angles (turret, cannon, fins, hatches); no JC3 anim node drives a transformation (0
`TransformationAnimNode` values in the files)"*, reason *"the animated transformation is a named
omission"* (`Working/Translation/T_ROWS.jsonl` line 196). This survey **confirms** that wording and
sharpens it:

* the **rotation pose is reachable** through hinged parts (Route A / C),
* the **0.633 m mast lift is not reachable through any decoded JC3 behaviour** (no prismatic joint),
* the **2.000 s timing is not authorable** (no rate member, writer UNKNOWN),
* so the row stays `out` and its reason can additionally cite the translation gap.

---

## 6. If any file is touched later — intended change, file, and revert

Nothing was modified for this report; it is read-only. When the build work starts:

| intended change | file | why it is the right file | revert |
|---|---|---|---|
| add `hinged_parts[]` rows + behaviour strings | the private `<car>_vehicle_parts.vmodc` **inside** the built `.ee` (`Builds/test-091/…civilian_01.ee`), never the shared `vehicle_common` | the parts module is where `parts[i].behavior`, `door_parts[]` and `hinged_parts[]` live (`MOVING_PARTS.md` §3); `R7` forbids in-place edits of shared modules | rebuild that build directory from `Working/Appearance/build_parts/parts_manifest.json`; or delete the build dir — no game file is touched |
| author hinge axis/limits | the private `.physicsc` bundled in the same `.ee` | hinge min/max are only in `hkpLimitedHingeConstraintData +0x0FC/+0x100` (`DOOR_ANGLES.md` §1) | same rebuild |
| pose values | `Working/Appearance/build_parts/parts_manifest.json` + the pose source `POSES.md` | the manifest is the single source the build reads | `git checkout --` the manifest |

---

## 7. UNKNOWNs, each with its settler

| # | unknown | settler |
|---|---|---|
| U1 | does a `CCar` ever drive a `target_position_variable` (no car carries `LandingGear`) | the 8 `Flaps` chassis' data (§4.4 step 1); the part consumer in the exe |
| U2 | can `ExtendedExposedVariables.variables[].expression` target a hinged part's variable | the 2 fleet expressions' consumers in the exe |
| U3 | what rate a JC3 hinge moves at | no rate member exists; a runtime read of a landing-gear aircraft, or the exe's variable writer |
| U4 | is a variant swap callable at runtime | `JustCause3.exe` entity/vehicle streaming consumer; live probe (test ban applies) |
| U5 | does a "Chaos jet/tank swap" exist as a JC3 asset | not in 233 entities / 52 modules / 0 vehicle skeletons; would need a source outside this grab |

## 8. Sources

`Research/BatmobileGrab/ANIMATIONS.json` + `ANIMATIONS.md` (clip lengths, track counts, maxima),
`POSES.md` (180-bone delta table, bbox, splay, loop check), `BONES.md` (skeleton),
`MESHES.md` (mesh/bone counts); `Research/JC3Grab/SEAT.md` (no vehicle animation/skeleton module),
`GEOMETRY.md` (56,136 rigid meshes), `MOVING_PARTS.md` (`vehicle_common` tables, variables, proofs),
`VOCABULARY.md` (`all_hinged_part_properties`, `ExtendedExposedVariables`), `DOOR_ANGLES.md`
(`hkpLimitedHingeConstraintData` offsets), `PARTS_TABLE.md` (behaviour census);
`tmp/freebuff/reports/mode-switch-carriers.md` (no runtime-switch vehicle, entity-variant pattern,
U1/U2/U5), `anim-sequences-coverage.md` (T-8 rows, no hinge rate);
`Working/Translation/T8_PARTS.md` (T-12 axes/pivots/limits), `Working/Translation/T_ROWS.jsonl`
(T-MD13), `Working/Appearance/build_parts/parts_manifest.json` (16 build entries).
