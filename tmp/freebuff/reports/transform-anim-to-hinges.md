# The battle-mode transform, bone by bone → what a JC3 hinge can carry

**STATUS: done (report only).** No build tree, parts module, `.physicsc`, ledger row or queue brief was
written or edited; nothing was launched.

**Provenance / reversibility.** New file, `tmp/freebuff/reports/transform-anim-to-hinges.md`
= `E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/transform-anim-to-hinges.md`. It is the output path the
brief names, and every comparable plan in this project lives in `tmp/freebuff/reports/`.
**Revert = delete this file.**

Labels: **decoded** = read at the cited file:line/field; **derived** = arithmetic over decoded values,
shown; **UNKNOWN** = searched and absent, with the settler named.

---

## 0. Verdict

| question | answer |
|---|---|
| which clip is the transform | `Drive_To_Combat` (75 tracks, **61 frames, 2.000 s, 30 fps**) and the pose pair `Batmobile_V2_Tank_Spread_Open_Game` / `_Close_Game` (70 tracks each, same length); all four packages identical |
| how much moves | **180/180 bones** change world transform, **64 articulate** (parent-relative change) |
| how many motions are pure rotation | **40** bones with a parent-relative **rotation** ≥ 0.05° → hinge-carriable |
| how many are translation | **24** bones articulate by translation only, led by the weapons mast **+0.633 m** and the chassis **−0.050 m** → **no hinge carrier** |
| wheel yaw in the transform | **splay/toe only**: front **19.31°/19.32°**, rear **18.01°/17.27°** (signed −19.14 / +19.15 / +17.31 / −16.60 about +Y). The 90° stance is `Batmobile_V2_Tank_Strafe`, a **different clip**, not this transform |
| the one motion no JC3 part behaviour can carry | the mast lift: `Weapons_Trans` **+0.634 m Y**, `Turret_Top` / `Turret_Top_Slide` **+0.633 m Y**, local rotation **0.00°** — there is no prismatic joint in the 25-row hinge table |
| the timing | **2.000 s** = (61 − 1) / 30; measured endpoint frame 0 → 60 = **1.967 s**; no hinge has a rate member, so the 2.000 s ramp must be authored (hook) or avoided (second entity in the end pose) |
| recommendation | carry the 40 rotations as hinged part rows + `.physicsc` limits; carry the mast/chassis translation with a **second entity variant in the battle pose** (already `9130`'s job) or a hook part-transform; never plan a skeletal transition (JC3 has no vehicle skeleton) |

---

## 1. The clip and its timing (decoded)

Source: `Research/BatmobileGrab/ANIMATIONS.md` §4 (per-sequence table) and §5 (bone lists);
`tmp/freebuff/reports/battle-mode-transform-plan.md` §1 for the cross-package check.

| sequence | set | frames | length | rate | tracks (bones) | notifies |
|---|---|---:|---:|---:|---:|---:|
| `Drive_To_Combat` | `BM_Batmobile_Chassis` | 61 | **2.000 s** | 30.00 | 75 | **0** |
| `Batmobile_V2_Tank_Spread_Open_Game` | `Batmobile_V2_Pose_States` | 61 | 2.000 s | 30.00 | 70 | **12** |
| `Batmobile_V2_Tank_Spread_Close_Game` | `Batmobile_V2_Pose_States` | 61 | 2.000 s | 30.00 | 70 | **15** |
| `Batmobile_V2_Tank_Spread_Open` / `_Close` | `Batmobile_V2_Pose_States` | 61 | 2.000 s | 30.00 | 74 | 3 |

(decoded: `ANIMATIONS.md` §4 rows, lines 84 / 99–105 and the three repeats at 121/136–142, 158/173–179, 195/311–317.)

* 61 frames at 30 fps means frame *n* sits at **n/30 s**; the last key is frame 60 = **2.000 s**, and the
  battle endpoint key. `POSES.md` labels frame 60 as **1.967 s**; `ANIMATIONS.md` gives the clip as
  **2.000 s**. Both are decoded from different columns; which label convention each uses is **UNKNOWN**
  (§6 U6). The build needs the duration, so it should ramp over 2.000 s and, if it must match the label,
  1.967 s — a 33 ms difference.
* Open/close are the same asset: loop check open-start vs close-end **0.054 cm / 0.026°**, open-end vs
  close-start **0.054 cm / 0.024°** (`POSES.md` §"Variant endpoints", `game_open_close_loop` PASS).
* **Notifies:** `Drive_To_Combat` has **0**; the gameplay pair carries **12 (open) / 15 (close)**; the
  non-game pair carries **3** — so the transition cueing lives in the `_Game` pair, not in
  `Drive_To_Combat`.
* **Top movers as `ANIMATIONS.md` prints them** (its own per-sequence table, lines 713–716):
  `Machine_Gun_01` **0.00 cm / 180.00°**, `Riot_Sup_Arm_01` **11.14 cm / 120.00°**,
  `Top_Sides_Root` **69.78 cm / 0.00°**, `Weapons_Trans` **68.51 cm / 0.00°**,
  `Heavy_Shells` **68.12 cm / 0.00°**. Those are **translation-only channels** (0.00° in the clip's own
  tracks), which is why no hinge reproduces them. Its values for the same bones differ from `POSES.md`'s
  pose-to-pose column (69.78 vs 64.77 cm for `Top_Sides_Root`); the two files measure different things
  and the reconciliation is **UNKNOWN** (§6 U6), so each figure below is cited to its own file.
* Identical in `Playable_Batmobile_SF`, `MK2`, `Funhouse`, `Joker` → one asset shipped four times.

**Timing schedule for the build (derived):** 0 s f0 → 0.500 s f15 → 1.000 s f30 → 1.500 s f45 →
2.000 s f60. A hinge or hook driven on a linear 0→1 ramp over 2.000 s hits the same five poses at
25 / 50 / 75 / 100 % of its travel. `POSES.md` and the key-frame export give frame 0 and frame 60 only,
so intermediate keys are **not** decoded here (`ANIMATIONS.md` §9 keeps the key-frame files outside the
repository).

---

## 2. The per-bone table

Start = pursuit pose (frame 0), end = battle pose (frame 60 of the `_Game` clip), both in JC3 metres
(X width, Y up, Z length, nose −Z). `world Δ` is the pose-to-pose movement; `local rot` is the
parent-relative rotation and is what actually articulates. Where `POSES.md` prints an absolute start
endpoint it is quoted; elsewhere the start is the bind pivot (`BONES.md` §3) and the end is
`start + world Δ` (**derived**, marked `+Δ`).

### 2a. The translations — no hinge carrier

| bone | parent | start (m) | end (m) | world Δ (m) | local rot | class |
|---|---|---|---|---:|---:|---|
| `Batmobile_Chassis` | itself (root) | −0.000, 0.022, 0.154 (bind) | −0.000, −0.028, 0.146 (+Δ) | 0.000, **−0.050**, −0.008 · 0.0508 | 0.54° | **translation** (whole body settles) |
| `Batmobile_Rig_Weapons_Trans` | `Weapons_Turret_Root` | +Δ | +Δ | 0.000, **+0.634**, +0.026 · 0.6350 | **0.00°** | **translation** — the mast lift |
| `Batmobile_Rig_Weapons_Turret_Top` | `Weapons_Trans` | 0.00009, **1.314716**, 0.335582 | 0.000317, **1.947437**, 0.366137 | 0.000, **+0.633**, +0.031 · 0.6335 | **0.00°** | **translation** (decoded start and end) |
| `Batmobile_Rig_Weapons_Turret_Top_Slide` | `Weapons_Trans` | +Δ | +Δ | 0.000, +0.633, +0.031 · 0.6335 | 0.00° | translation |
| `Batmobile_Rig_Weapons_Drone_Decoder_Arm` / `_Decoder` | `Turret_Top_Slide` / `_Arm` | +Δ | +Δ | 0.000, +0.743, +0.035 · 0.7441 / 0.7440 | 0.00° | translation (rides the slide) |
| `Batmobile_Rig_Weapons_Top_Sides_Root` | `Weapons_Turret_Root` | +Δ | +Δ | 0.000, +0.648, +0.006 · **0.6477** | 0.00° | translation (rides the mast) |
| `Batmobile_Rig_Weapons_Heavy_Shells` | `Weapons_Root` | +Δ | +Δ | 0.000, +0.631, +0.026 · 0.6311 | 0.00° | translation |
| 28 shell bones (`R_Shell_*`, `L_Shell_*`, `_Tween_*`, `_Chamber`) | `Turret_Top` | +Δ | +Δ | 0.000, **+0.634…+0.635**, +0.029…+0.035 · **0.6343–0.6355** | 0.00° | ride the raised turret (their own track is ≤ 3 mm of noise) |
| `Batmobile_Rig_Weapons_Heavy_Cannon_Barrel_01` / `_Barrrel_02` | `Turret_Top` / `_Barrel_01` | +Δ | +Δ | 0.000, +0.641 / +0.646, **−0.534 / −1.084** · 0.8343 / 1.2624 | 0.00° | translation (ride; pitch is code-side) |
| `CockPit_Mesh`, `Nose_Mesh`, `Winch_Door_Mesh`, `Rear_Door_*` (5), chair bones (10), `Sonar` (2) | chassis chain | +Δ | +Δ | 0.0226–0.0791 | 0.00° | translation (rigid ride — no battle motion) |
| 13 `Aero_Flap_*` bones (+5 pistons) | `Chassis` | +Δ | +Δ | 0.0402–0.0683 | **0.000°** | **no motion in this clip** (they move in `Aero_Flap_Up/Down`, 30.00°/20.01°, piston 54.80°) |
| 18 `Jet_Nozzle_0NN` + `Jet_Root` / `Jet_Thruster` / `Jet_Fins` | `Jet_Root` chain | +Δ | +Δ | 0.0794–0.0861 | **20.00°** | rotation, but **shared with the driving clips** (`Jet_Boost` 16.0–16.7°), so not a battle tell |

### 2b. The rotations — hinge-carriable

| bone | parent | world Δ (m) | world rot | **local rot** | what it is | signed axis |
|---|---|---:|---:|---:|---|---|
| `Batmobile_Rig_Weapons_Riot_Sup_Arm_01` | `Riot_Suppressor_Root` | 0.224, 0.682, 0.013 · 0.7183 | 120.01° | **120.00°** | riot arm swings out | hinge about the arm root |
| `Batmobile_Rig_Weapons_Riot_Sup_Main` (+ `_Ammo`) | `Riot_Sup_Arm_01` | 0.502, 0.957, 0.015 · **1.0813** | 179.99° | **59.98°** | furthest-travelling bone in the car | hinge (compounded with the arm) |
| `Batmobile_Rig_Weapons_Machine_Gun_01` | `Machine_Gun_Root` | −0.399, 0.838, 0.015 · 0.9279 | 179.99° | **179.99°** | gun flips over and rises | hinge (half-turn) |
| `Machine_Gun_02` / `_Root` | `_01` / `Top_Sides_Root` | −0.399, 0.841, −0.397 · 1.0122 / 0.9279 | 179.99° | 0.00° | ride the flip | — |
| `Projectile_Mine_Cover_01…04` | `Turret_Top` | 0.6283–0.6323 | 65.54° | **65.00°** | four bay lids open | hinge |
| `Projectile_Mine_01…04` | `Turret_Top` | 0.6817–0.6857 | 0.54° | 0.00° | rounds ride the lids | — |
| `Missiles_L_T` / `R_T` / `L_B` / `R_B` | `Chassis` | 0.0446 / 0.0367 | 15.54° | **15.00°** | missile-bay lids tilt | hinge |
| `Missiles_*_Mid` + 8 rounds | lids | 0.1205 / 0.1317–0.1471 | 15.54° | 0.00° | ride the lids | — |
| `Chassis_L_REAR_WHEEL_ARCH` / `_R_…` | `Chassis_Mesh` | 0.028, −0.089, 0.606 · 0.6132 / 0.6133 | 28.30° | **28.36° / 28.35°** | rear arch doors swing | hinge |
| arch arms `…_Arm_LB/RB`, `L/R_B_Wheel_Armour_001` | arches | 0.4534 / 0.6132 | 28.30° | 0.00° | ride | — |
| `L/R_B_Wheel_Armour_002` | `_001` | −0.798, +0.036, +0.124 · **0.8084 / 0.8082** | 28.29° | 0.00° | furthest body bone after the riot assembly | — |
| `Rig_Cockpit_Armor_R_01` / `_L_01` | `Chassis_Mesh` | 0.3603 | 1.09° | **1.41° / 1.42°** | cheek plates crack open | hinge (small) |
| `Rig_Cockpit_Armor_R_02` / `_L_02` | `_01` | 0.6672 | 6.06° | **5.10°** | plate tips | hinge |
| `SUSP1_Wheel_Front_Left` / `_Right` | `Chassis_Mesh` | 0.000, −0.038, −0.001 · 0.0376 | 19.40° | **19.32°** | front splay pivot | hinge about **+Y** |
| `SUSP1_Wheel_Rear_Left` / `_Right` | `Chassis_Mesh` | 0.000, −0.184, +0.322 · 0.3704 / 0.3709 | 17.86° / 17.10° | **18.01° / 17.25°** | rear splay pivot | hinge about +Y |
| `SUSP2_Wheel_Front_L/R` → `Wheel_Parent_F_*` → tyre/fan/disc | corner chain | 0.2518 → **0.5661 / 0.5660** | 19.40° | 0.01–0.03° | the whole corner swings out ~0.57 m | rides `SUSP1`'s rotation (arc radius) |
| `Damper_Left_Front_02`, `L/R_F_Wheel_Armour(001)` | corner | 0.7360 / 0.6479 / 0.4780 | 19.40° | 0.00° | ride the corner | — |
| `Wheel_Parent_B_L` / `_B_R` → tyre/fan/disc | corner chain | **0.5631 / 0.5466** | 17.86° / 17.12° | 0.01–0.02° | rear corners swing out | rides `SUSP1` |
| `Power_Cell_Root` / `_Core` / `_Glass` | rear-left corner | 0.3305 / 0.3054 | 17.86° | 0.00° | ride | — |

**Wheel yaw, precisely.** The axle directions in `POSES.md` §"Wheels" give the signed rotation about +Y:

| wheel | splay (this transform) | signed | strafe clip (`Tank_Strafe`) |
|---|---:|---:|---:|
| `Wheel_Parent_F_L` | 19.31° | **−19.14°** | +90.00° |
| `Wheel_Parent_F_R` | 19.32° | **+19.15°** | +90.00° |
| `Wheel_Parent_B_L` | 18.01° | **+17.31°** | +89.99° |
| `Wheel_Parent_B_R` | 17.27° | **−16.60°** | +89.95° |

Front pair toes out, rear pair toes in; the 90° stance belongs to `Batmobile_V2_Tank_Strafe`, whose root
also translates **4.89 m** (only its wheel rotation is usable — `POSES.md`).

### 2c. Counts, reconciled

| class | bones | evidence |
|---|---:|---|
| moved (world ≥ 0.5 mm or ≥ 0.05°) | **180 / 180** | `POSES.md` verdict, `all_deltas_accounted` PASS |
| articulate (parent-relative change) | **64** | `POSES.md` verdict |
| articulate by **rotation** ≥ 0.05° | **40** | re-derived this pass from the 180-row table (python, §7); the exact 40 are listed there |
| articulate by **translation** | **24** | 64 − 40 (derived). The table prints only world Δ and local rotation, so which 24 is **not** printed per bone — **UNKNOWN** (§6 U7); the four large ones are certain from the top-mover list: `Top_Sides_Root`, `Weapons_Trans`, `Heavy_Shells`, and the `Riot_Suppressor_Root` lift. |
| rigid riders (no local change) | 116 | 180 − 64. **Careful:** subtracting the parent's world Δ does **not** recover a local translation — a child riding a rotating parent moves on the arc (the `L/R_B_Wheel_Armour_002` 0.96 m and the cannon barrels' 0.57 m are arcs, not slides). Only the clip's own translation tracks prove a slide. |

---

## 3. Which motion each JC3 part behaviour can carry

Fleet facts, decoded: `Research/JC3Grab/MOVING_PARTS.md` §1-§3 tables (`vehicle_common.vmodc`, 25
`all_hinged_part_properties` rows) and the `PARTS_TABLE.jsonl` behaviour census (233 entities,
**11,643 parts**). A hinged part = `behavior` string + `parts[i]` row + `hinged_parts[]`/`door_parts[]`
index + a `hkpLimitedHingeConstraintData` whose **min is at +0x0FC and max at +0x100, radians**
(`DOOR_ANGLES.md` §1). There is **no rate/speed member** in `all_hinged_part_properties`.

| motion (bones) | travel | best-fit JC3 behaviour | fleet count | variable it reads | on a `CCar`? | verdict |
|---|---:|---|---:|---|---|---|
| riot arm 120°, riot main 60° (compounded to 179.99° world) | 120° / 60° | **`Turret`** (aim rig) or **`Flaps`** (variable) | **22** / **202** | `Turret` has **no `vehicle_common` row** (aim comes from the `.physicsc` hinge); `Flaps` reads **`flaps_T`** | both **proven-on-CCar** | **rotation: carriable**; `Flaps` is the only one that can be *driven by a variable* |
| machine gun flip | 179.99° | **`Cannon`** (or `Turret`) | **68** / 22 | **no `vehicle_common` row** either — the aim hinge is the driver | `Cannon` **proven-on-CCar** (11 chassis) | **rotation: carriable as a hinge angle**; not variable-driven |
| mine covers ×4 | 65° | **`MissileHatch`** (door, name only) or `Flaps` | door table (name only) / 202 | door: the `.physicsc` hinge range; `Flaps`: `flaps_T` | door rows: 338 rows, 334 on a limited hinge, 88 cars | **rotation: carriable** |
| missile-pod lids ×4 | 15° | **`MissileHatch`** / `Flaps` | as above | as above | yes | **rotation: carriable** |
| rear wheel arches ×2 | 28.3° | **`Flaps`** or `FrontLeftDoor`-style door | 202 / door table | `flaps_T` / hinge range | **proven-on-CCar** | **rotation: carriable** |
| cockpit cheek plates ×4 | 1.41° / 5.10° | **`Flaps`** (small angle) | 202 | `flaps_T` | yes | **rotation: carriable** |
| wheel splay ×4 | 19.32° / 17.25° (signed −19.14…+17.31) | **`SteeringFork`** is the only row with `use_target_position_as_angle = 1` (a literal angle); plain **`Wheel`** is the part type | **27** / **710** | `SteeringFork`: `steering_angle_inverted` | **proven-on-CCar** (11 chassis) | **wheel yaw: carriable as an angle**; note it is the steering variable, so a constant splay needs a separate variable or a static pose |
| jet nozzle ring ×18 | 20.00° | **`Flaps`** or a static pose | 202 | `flaps_T` | yes | rotation, but **not a battle tell** — `Jet_Boost` moves the same ring 16–16.7° |
| aero flaps ×13 | **0.000°** | none needed here | 202 (`Flaps`) | `flaps_T` | yes | **no motion in this transform**; the flap clips are `Aero_Flap_Up/Down` 30.00°/20.01° |
| **mast lift** | **+0.633 / +0.634 m Y** | **none** | — | — | — | **no carrier**: 25 hinge rows, **no prismatic behaviour**, and a hinge has an axis + two angle limits only |
| chassis settle | −0.050 m Y | **none** | — | — | — | no carrier (whole-body translation) |
| cannon barrels forward/up | −0.534 / −1.084 m Z, +0.641 Y | **none** (they ride the mast; pitch is code-side) | — | — | — | no carrier beyond the mast's |

**Two facts that decide the plan.** (1) `Turret` and `Cannon` — the two behaviours that match the two
biggest rotations — have **no `vehicle_common` row**, so they cannot be driven by a
`target_position_variable`; their angle comes from the Havok hinge (aim), which is exactly what a static
battle pose needs but not what a 2 s transition needs. (2) `Flaps` (`flaps_T`, 202 parts, 8 chassis,
proven on a car) is the only variable-driven behaviour with a decoded car precedent, and **who writes
`flaps_T` is not in any file read** (`MOVING_PARTS.md` §4).

---

## 4. The translation parts: minimal hook features

Everything the hinges cannot carry is in §2a. Three translations matter; the other 21 bones ride them.

| translation | value | what must move | can a variant carry it? | can a hook carry it? |
|---|---:|---|---|---|
| weapons mast | **+0.634 m Y** (`Weapons_Trans`), +0.633 m (`Turret_Top`, `_Slide`, 28 shells, 2 barrels, decoder arm, top-sides root, heavy shells) | one part (`batmobile_turret`) and its children | **yes** — the battle entity is authored in the end pose (`9130`, `NEW-MOD-21`) | yes, and it is the only way to *animate* the lift |
| chassis settle | **−0.050 m Y** | the whole body, or the entity's origin | **yes** (different `.ee` pose/origin) | yes (entity z-offset per frame) |
| suspension corner swing | 0.5661 / 0.5631 m **world**, but only 19.32° / 18.01° **local** | `SUSP1_*` (hinge) — the 0.57 m is the arc, not a translation | yes | not needed: the hinge produces it |

**Minimal hook surface for the animated route** (each item is the least that reproduces §2a at 61 keys):

1. **Part handle by name** — resolve `batmobile_turret` (and the chassis) from the live vehicle's parts
   list. The parts manager / `CPhysicalPart` addresses are **UNKNOWN**: `7982` decodes the vehicle
   pointer chain, not the parts list; `Working/RTTI/vehicle_rtti.json` has `CCar`/`CLandVehicle`/
   `CVehicle`/`hknpVehicleInstance`/`CDamageable` and **no parts class** (settler: the next RTTI pass,
   or `7982`'s live read once a session runs).
2. **Per-part local transform write** — set the part's local translation (mast: `(0, +0.634, +0.026)`)
   and rotation (`0.54°`) each tick. No decoded writer exists for a part transform; the closest decoded
   channel is the hinged variable (`flaps_T`), which is 0..1 or an angle and **cannot express a
   translation** (`MOVING_PARTS.md` §1).
3. **A 2.000 s ramp at 30 fps** — a frame counter 0…60 with the five poses of §1; no member supplies the
   duration (no hinge rate), so the hook owns the clock.
4. **Mode state + trigger** — the LT hold already specified for `7984`; the tracker HUD must persist
   across it (operator fact), and health/ammunition carry (not velocity) is `9130`'s rule.
5. **Off switch and log** — per `7986`'s pattern, so a bad part write can be disabled without a rebuild.

**The minimal non-hook route** (recommended, and what `9130` already builds): author the battle pose as
the second entity — mast at 1.947 m, chassis at −0.028 m, every rotation at its §2b angle — and swap
entities. That needs **no** part write, no ramp and no new member; it loses the animation (the 2.000 s
morph), which is `T-MD13`'s known gap.

---

## 5. What this does to the ledger and the queue

| record | today | this report's effect |
|---|---|---|
| `T-MD13` (transformation stance, `blocked`) | "the pose is a per-entity constant the battle variant can hold, the animation is not" | **confirmed and sharpened**: 40 of 64 articulations are hinge-reachable, 24 are translation-only, the mast is the blocker; the row can cite §2a + §3 |
| `NEW-MOD-21` (battle-stance static pose set) | "mast lift +0.633 m approximated by hinge arc (declare error)" | the approximation is **wrong in kind**: a hinge cannot lift, so the mast must be a pose (variant) or a hook; drop the "declare error" wording |
| `9172` (moving parts) | builds part classes and variable bindings | the rotation set and its angles/axes are the input; the mast is out of its scope |
| `9130` (mode pair) | builds the variant pair | the battle variant's part angles are §2b's limits; the mast/chassis offsets are §2a's |
| `V-RC2-turret` | FAIL "no joint" (yaw missing 120°, pitch 25°) | unchanged by this report — aim is the `.physicsc` hinge, not the transform |

**COMPROMISES: none needed.** The rotation half is carriable exactly; the translation half has two
routes that are both lore-faithful (a second entity in the end pose, or a hook part-transform). Neither
requires accepting a wrong number, so nothing here is a compromise the operator must approve.

---

## 6. UNKNOWNs

| # | unknown | what was tried | setter |
|---|---|---|---|
| U1 | the intermediate keys (frames 1-59) of the transform | `POSES.md` exports frame 0 and 60 only; `ANIMATIONS.md` §9 keeps the key-frame dumps outside the repo | the key-frame export for `Drive_To_Combat` (30 fps, 61 frames) |
| U2 | who writes `flaps_T` on a car (the only variable-driven car hinge) | `MOVING_PARTS.md` §4 states the writer is in no read file | the exe's variable writer, or the 8 `Flaps` chassis' data + one live read |
| U3 | whether a hinge can take a literal constant angle (a static pose) rather than a 0..1 variable | only `SteeringFork` sets `use_target_position_as_angle = 1`; the other 24 rows are 0..1 | one `.physicsc` + parts write on a copy, then a static check (no game) |
| U4 | the parts-list / part-transform addresses for the hook route | `vehicle_rtti.json` has no parts class; `7982` decodes only the vehicle chain | the next RTTI pass, or the first live `7982` read |
| U5 | whether `Turret`/`Cannon` angle limits in `.physicsc` can be authored to the transform's pose (120° arm, 180° MG) | `DOOR_ANGLES.md` proves min/max at +0x0FC/+0x100 for doors; the turret samples' hinges are `hkpLimitedHingeConstraintData` too but their ranges are aim ranges | `TURRET.md` §3 + a private `.physicsc` write on a copy |
| U6 | why `ANIMATIONS.md` and `POSES.md` disagree on the same bones (`Top_Sides_Root` 69.78 vs 64.77 cm) and on the clip's length (2.000 vs 1.967 s) | both values quoted from their own file; neither file states its measure (max-over-frames vs f0→f60; frame count vs label) | `Tools/scripts/grab_poses.py` and the animation reader's own definitions |
| U7 | which 24 bones articulate by parent-relative **translation** | the 180-row table prints world Δ + local rotation only; subtracting parent world Δ mixes in the arc of a rotating parent (verified: `L/R_B_Wheel_Armour_002` 0.96 m is an arc, cannons 0.57 m is an arc) | the raw local key matrices in the pose export, or `grab_poses.py --check` printing local translations |

---

## 7. Checks run this pass (verbatim)

```
# per-sequence numbers, all four packages
grep -n "Drive_To_Combat" Research/BatmobileGrab/ANIMATIONS.md
  -> 84,121,158,195 (61 frames | 2.000 s | 30.00 fps | 75 tracks | transformation | 0 notifies)
# pose endpoints, deltas, signed wheel yaw, loop check
Research/BatmobileGrab/POSES.md §Poses / §Turret / §Wheels / §"Every bone delta" / §Checks
  -> 180 rows, 8/8 checks PASS
# articulation split (re-derived here)
python (regex over the 180-row table, local rot >= 0.05 deg)  -> rows 180, articulated-by-rotation 40
  -> translation-only = 64 - 40 = 24 (derived; the mast/shell/cannon group, all local rot 0.00 deg)
# fleet part behaviour census (11,643 parts, 233 entities)
python (PARTS_TABLE.jsonl)  -> Wheel 710, Flaps 202, Turret 22, Cannon 68, GatlingGun 24,
   engine 187, doors 173/145/132/130/119/112/103/62/50/21..., LandingGear 114, MissileHatch: door table (name only)
# hinge mechanics
Research/JC3Grab/MOVING_PARTS.md §1 (25 all_hinged_part_properties rows, no rate member)
Research/JC3Grab/DOOR_ANGLES.md  -> 338 door rows, 334 on hkpLimitedHingeConstraintData,
   min +0x0FC / max +0x100 radians, 5/5 checks pass
# no vehicle skeleton / no animation module
tmp/freebuff/reports/battle-mode-transform-plan.md §3.1 (0 jc_skeletons/vehicles/*.bsk, 0 statemachine, no animation module in 52 types)
```

**Not done:** no `.vmodc`, `.physicsc`, `.ee`, parts manifest or build tree was written; no queue brief
was edited; nothing was launched or installed. **Revert = delete this file.**
