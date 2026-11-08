# Cabin motion — what moves inside the BmAK cockpit, and which JC3 joint can carry it

**Question:** list the cabin parts that move while driving in BmAK (steering wheel, dials, screens),
give the angle per unit steering input, then the JC3 interior joints that can carry each and how we
feed them.

**Verdict, in one line: nothing in the BmAK cabin moves while driving.** There is **no steering
yoke, no dial and no needle geometry** in the shipped mesh or rig, and the only cabin joints that
animate at all are the **seat** and the **canopy**, both on enter/exit and neither while driving.
So the requested ratio "degrees of wheel per unit steering input" has **no BmAK numerator** — it is
**UNKNOWN, not zero**: the yoke that would hold the angle does not exist. On the JC3 side a donor
`SteeringWheel` part does exist and is driven by `steering_turn`, but its angular sweep is also
**UNKNOWN** in our decode, so the ratio has **no denominator either**. What this report can pin down
is the wiring: which bone/part would carry each cabin element, and what value it would be fed.

Labels: **decoded** = read at the cited field; **derived** = arithmetic over decoded inputs;
**UNKNOWN** = searched and absent, with the settler named.

---

## 1. The cabin inventory (decoded)

Every cabin bone in the 180-bone rig, from `Research/BatmobileGrab/BONES.md` (the only bones whose
names are `Chair*` or `CockPit*`; nothing else in the list is interior):

| # | bone | parent | bind offset in parent frame (cm) |
|---:|---|---|---|
| 81 | `Batmobile_Bone_Chair_Root` | `Batmobile_Chassis_Mesh` | −0.000, 0.022, 0.154 |
| 82 | `Batmobile_Bone_Chair_Rot_001` | `Batmobile_Bone_Chair_Root` | 0.000, 1.143, 1.729 |
| 83 | `Batmobile_Bone_Chair_Foot_Rest_L_001` | `Chair_Rot_001` | −0.326, 1.074, 2.370 |
| 84 | `Batmobile_Bone_Chair_Foot_Rest_L_002` | `Foot_Rest_L_001` | −0.326, 0.982, 2.791 |
| 85 | `Batmobile_Bone_Chair_Restraint_L_001` | `Chair_Rot_001` | −0.326, 1.705, 1.537 |
| 86 | `Batmobile_Bone_Chair_Piston_001` | `Chair_Rot_001` | 0.000, 1.638, 1.275 |
| 87 | `Batmobile_Bone_Chair_Piston_002` | `Chair_Rot_001` | 0.000, 1.410, 1.188 |
| 88 | `Batmobile_Bone_Chair_Piston_Root_001` | `Chair_Root` | 0.000, 1.169, 1.254 |
| 89 | `Batmobile_Bone_Chair_Piston_Top_001` | `Piston_Root_001` | 0.000, 1.257, 1.406 |
| 90 | `Batmobile_Bone_Chair_Piston_Btm_001` | `Piston_Root_001` | 0.000, 1.257, 1.406 |

`Chair_Root` sits at **0.022 / 0.154 cm** in x/z-of-parent — the same 0.0222 / 0.1543 m offset as the
`DriverAnimOrigin` socket (`COCKPIT.md` §2), i.e. the rig's seat pivot is the entry/exit origin.

There is **no** `Steer*`, `Dial*`, `Needle*`, `Gauge*`, `Screen*` or `Monitor*` bone anywhere in the
180. The 10 chair bones are the whole cabin skeleton.

### Part-by-part verdict

| cabin element | geometry that ships | bone | moves while driving? | evidence |
|---|---|---|---|---|
| **steering wheel / yoke** | **none** | **none** | **no part exists** | `COCKPIT.md` §1 last row: "*yoke / steering control — **- none -** — absent*"; §6.1: the hand box `|x| < 0.17, y 1.00..1.30, z −1.60..−1.10` holds **4 faces of any material** (y 1.20–1.30), and the nearest driver-facing surface is the panel at z −1.5097 |
| **dials / needles / gauges** | **none** — the panel is one body-material surface | **none** | **no part exists** | instrument panel = slot 10 `Batmobile_V3_Cockpit_MIC`, **1,043 faces / 720.3 cm²**, x −0.3456..0.3457, y 1.3148..1.6005, z −1.8981..−1.5097 (`COCKPIT.md` §1); no needle mesh among the 12 mesh exports (`COCKPIT.md` §6.4) |
| **centre screen** | one quad, **0.3188 × 0.1512 m** | `Batmobile_Chassis` (slot 12) | **no** — static quad | slot 12 `Cockpit_Master_Flip_Data`, **100 faces**, 404.1 cm², centre **(0, 1.4857, −1.7552)**, mean normal 35.2° from vertical; the master material has **no connected Diffuse/Specular/Power/Emissive and no texture** (`COCKPIT.md` §1, §6.3) |
| **driver-facing panel** | 1,043 faces, slot 10 | `Batmobile_Chassis` | **no** | same row as the panel above |
| **dashboard lamp** | a light socket, not a moving part | `Dashboard_Light` / `Dashboard` socket | lamp only | `LIGHT_SOCKETS.md` §"Packages with no decoded socket table": `Dashboard_Light` on `Playable_BatmobileMK2_SF` and `Playable_BatmobileFunhouse_SF`, `Dashboard` on `Playable_BatmobileJoker_SF` |
| **seat** | 9 animated bones + 150.7 cm of travel, **entry/exit only** | `Chair_Rot_001` chain | **no** — see §2 | `Batmobile_V2_Chair_Open` 2.2333 s / 68 frames / 9 moved bones / max 150.7468 cm; `..._Chair_Close` 2.2667 s / 69 frames / same (`ANIMATIONS.json`) |
| **canopy** | cockpit shell, 0.3 s travel **entry/exit only** | `CockPit_Mesh`, `Batmobile_Nose_Mesh`, `Chair_Rot_001` | **no** | `Batmobile_V2_Cockpit_Open/_Close` 0.3 s / 10 frames / **2 moved bones / 71.0094 cm**; the older `Cockpit_Open` 0.4333 s / 72.3771 cm and `Cockpit_Close` 0.5 s / 72.4813 cm / 12.493° |

**Why "no steering yoke" is not a modelling gap on our side:** the shipped rig itself has no pivot for
one. The build's own parts schema records it as a deliberate exclusion —
`tmp/freebuff/b02polish/spec-schema3.json` → `left_in_body`: *"steering yoke — BONES.json has no
steering-wheel/yoke bone; no pivot exists for a separate part."*

**Conflict to note:** `GRAB_BACKLOG.md:222` carries `ANI-7 "Steering yoke turns with steering |
cockpit bone"`. That row is a **needle** (a target to be filled by JC3, `Research/JC3Grab/G2X.md:134`),
not a BmAK observation — the decoded mesh contradicts the "cockpit bone" premise. The backlog row
should be read as "there is no donor part, so this is a build item", not as evidence a yoke moves.

---

## 2. What the animation data says about cabin motion (decoded)

Every Batmobile sequence in `ANIMATIONS.json`, filtered to bones whose name contains `Chair` or
`CockPit`: **only the four entry/exit clips touch them.** All driving clips move wheels, chassis,
turret, nozzles, flaps — and **zero** cabin bones.

| sequence | length | frames | moved bones | max rot | max translation | cabin bones moved |
|---|---:|---:|---:|---:|---:|---|
| `Batmobile_V2_Idle` | 0.0333 s | 2 | **0** | **0.0°** | **0.0 cm** | 1 *active* (`Chair_Rot_001`), 0 moved |
| `Batmobile_V2_Tank_Idle` | 0.0333 s | 2 | 0 | 0.0° | 0.0 cm | none |
| `Drive_To_Combat` | 2.0 s | — | 12 | 179.995° | 69.7866 cm | **none** |
| `Batmobile_V2_Tank_Strafe` | 2.7 s | 82 | 12 | 178.237° | 491.7997 cm | **none** |
| `Batmobile_V2_Cannon_Fire` | 0.7 s | — | 12 | 2.99° | 53.376 cm | **none** |
| `Batmobile_V2_Jet_Boost` | 0.6 s | — | 12 | 16.725° | 12.4983 cm | **none** |
| `Batmobile_V2_Boost_Noise` | 0.6 s | — | 12 | 14.355° | 0.6347 cm | **none** |
| `Batmobile_V2_ChainGun_Spin` | 3.9333 s | — | 1 | 179.496° | 0.0 cm | **none** |
| `Batmobile_V2_Turret_Spin` | 2.6 s | — | 12 | 60.001° | 10.8964 cm | **none** |
| `Batmobile_V2_Chair_Open` | 2.2333 s | 68 | 9 | 179.999° | **150.7468 cm** | chair chain |
| `Batmobile_V2_Chair_Close` | 2.2667 s | 69 | 9 | 180.0° | **150.7468 cm** | chair chain |
| `Batmobile_V2_Cockpit_Open` | 0.3 s | 10 | 2 | 11.227° | **71.0094 cm** | `CockPit_Mesh`, `Chair_Rot_001` |
| `Batmobile_V2_Cockpit_Close` | 0.3 s | 10 | 2 | 11.227° | **71.0094 cm** | same |
| `Cockpit_Open` | 0.4333 s | — | 2 | 12.445° | 72.3771 cm | same |
| `Cockpit_Close` | 0.5 s | — | 2 | 12.493° | 72.4813 cm | same |

The one "cabin track" in the driving idle, `Batmobile_V2_Idle` → `Batmobile_Bone_Chair_Rot_001`, is a
**static** single-bone track: 2 frames, `moved_bones = []`, `max_rotation_deg = 0.0`,
`max_translation_cm = 0.0`. It is the rig's bind pose being re-stated, not a motion.

Read together with `SPEEDOMETER.md` (the install's only speedometer is `bDebugSpeedometer`, a
`BoolProperty` **off** in `BmGame.ini:6303` and `DefaultGame.ini:989`, drawn by a native
bean-counted HUD thunk with no movie asset), the conclusion is: **BmAK's cockpit is a modelled
interior, not an instrumented one.** There is no instrument to animate.

---

## 3. "Angle per unit steering input" — what exists on each side

### 3.1 BmAK: no wheel to measure (UNKNOWN)

| candidate source for a yoke angle | result |
|---|---|
| yoke geometry | **absent** (4 faces in the hand box, `COCKPIT.md` §6.1) |
| yoke bone | **absent** (no `Steer*` in the 180, §1) |
| yoke animation | **absent** (0 cabin bones in 9 driving clips, §2) |
| `SVehicleWheel` steer-limit field | **absent** — 152 named offsets carry radius/travel/slip only (`wheel-spin-and-animation-plan.md` §2, U-1) |
| `CLASS_DEFAULTS.md` steering members | only drift/impact shaping (`ImpactRoadAssistSteeringFactor` 30.0, `DriftCorrectionSteerSpeed` 1.0, `DriftAngularVelocityBySteer`, `DriftSpeedBySteer`) — no angle limit |

The only steering numbers BmAK ships are **rate curves**, not angles
(`Research/BatmobileGrab/MECHANICS.md`, `RVehicleSimBatmobile`, 2,328 B; the four playable packages):

| curve | Playable / MK2 / Funhouse | Joker |
|---|---|---|
| `StandardSteeringSpeedCurve` | 0 → **60.0**, 600 → 55.0, 1100 → 55.0, 1300 → 30.0, 2000 → **20.0** | 0 → 60.0, 600 → 55.0, 1100 → 50.0, 1300 → 35.0, 2000 → **15.0** |
| `SteerSpeedVsSpeedCurve` | 0 → **720.0**, 3500 → **720.0** | 0 → **220.0**, 3500 → **20.0** |
| `BattleModeVSpeedCurve` | 0 → 60.0, 600 → 40.0, 1200 → 30.0 | same |

The **units of these curve outputs are not decoded** in `MECHANICS.md` (x is a speed value in the
same space as the torque curves, y is unnamed). They cannot be turned into "degrees of wheel per unit
stick" without a unit, so they are quoted here as context, not as the ratio.

**Therefore: BmAK's angle-per-unit-steering-input is UNKNOWN because the part it would describe does
not exist.** A rig that adds a yoke is adding new geometry, so the ratio becomes a design constant,
not a translation.

### 3.2 JC3: the part and the variable exist, the sweep does not (UNKNOWN)

| item | value | source |
|---|---|---|
| behaviour | **`SteeringWheel`** | `MOVING_PARTS.md` §1 hinged table |
| channel | hinged, `target_position_variable` = **`steering_turn`** | same |
| flags | `lod = 1`, **`use_target_position_as_angle = 0`** → the variable is a **0…1 position**, not an angle | same |
| fleet proof | **20 parts, 20 entities, 9 chassis** (8 cars + `v1302` sailboat), **proven on `CCar`** | `MOVING_PARTS.md` §2 |
| donor part | `sportsmuscle_steeringwheel`, **part index 7**, `dt = Land_Steering_Wheel`, `body = 27`, `ray = 27`, model `sportsmuscle_steeringwheel.lod`, `deform = 1` | `PARTS_TABLE.jsonl` (`v0300_car_kensington_sportsmuscle`) |
| second donor | `oldjeep_steeringwheel`, **part index 19**, `Land_Steering_Wheel`, `body = 50` | `PARTS_TABLE.jsonl` (6 `v0000` variants) |
| what stores the travel | **nothing decoded** — `hinged_parts[]` rows carry only `part_index` (§3 of `MOVING_PARTS.md`); the axis/limit live in `.physicsc` | `MOVING_PARTS.md` §3 |
| what writes `steering_turn` | **UNKNOWN** — "the animation system writes it, the behaviour reads it"; which code writes it is not in any file read | `MOVING_PARTS.md` intro, §4 |
| sibling behaviour | `SteeringFork` → `steering_angle_inverted`, **`use_target_position_as_angle = 1`** (27 parts, 11 chassis) — the *only* hinged row that takes its variable as an angle | `MOVING_PARTS.md` §1 |

**The sweep is genuinely missing, not overlooked.** `PHYSICS_LIMITS.json` decodes all **9**
`hkpLimitedHingeConstraintData` in `sportsmuscle.physicsc`; their limit pairs are

```
0..80, -35..0, 0..80, -35..0, -15..0, 0..30, 0..70, -15..0, 0..90  (degrees)
```

— door / hood / boot ranges, **no wheel-like symmetric pair** — and `PHYSICS_ROLES.md` §4/§7 records
that *which bodies each constraint joins is UNKNOWN*. So the steering-wheel part's own hinge (if it
has one at all) is not among the decoded limit pairs we can attribute, and the part may instead be
rotated kinematically like the wheels (`sportsmuscle_wheel_*` have `world body = -1`).
`Research/JC3Grab/DOOR_ANGLES.md` covers only `door_parts[]` rows, so it does not help here.

**Shape of the relation that *is* settled:** with `use_target_position_as_angle = 0`, the part's
rotation is a blend across the hinge range driven by a 0…1 scalar:

```
part_angle = hinge_min + steering_turn * (hinge_max - hinge_min)
=> degrees per 1.0 of steering_turn = hinge_max - hinge_min      (sweep UNKNOWN)
```

Our input is a signed axis, so the feed is `steering_turn = (axis + 1) / 2`, done on the entity/HUD
side before it reaches the variable. **Do not invert**: `steering_turn` is a position, and there is no
`steering_turn_inverted` string in the 24 variables (`VOCABULARY.md:1361` lists the whole set; the
only inverted-steering channel is `steering_roll_inverted` for aircraft ailerons).

---

## 4. Dials and screens — the honest answer on both sides

### 4.1 Dials: no carrier on either side

JC3 has **12 rotating behaviours**, and all 12 are continuous-spin rpm channels
(`MOVING_PARTS.md` §1 rotating table): `MainRotor`, `TailRotor`, `Propeller`, `GatlingGun`,
`RadarSlow`, `RadarFast`, `LeftRotor`, `RightRotor`, `Rotor`, `EngineRotatingPart`,
`OuterLeftRotor`, `OuterRightRotor`. Not one is angle-limited or position-driven, so none can hold a
needle that sweeps once across a dial.

The nearest *shape* is `EngineRotatingPart` → `engine_rpm` (**3 parts, 1 chassis:
`v0506_car_solar_oldtractor`**, `rotoscope_enabled = 1`, `rotoscope_rpm_per_cycle = 20`) — but an
`engine_rpm` fan spins as long as the engine turns; a speedometer needle must stop at full scale. Using
it would make the needle spin, which is visibly wrong.

Conclusion: **no JC3 joint can carry a dial needle.** Since BmAK ships no dial either (§1), the
correct port is to **not build one**. If a needle is ever wanted it is new native behaviour, not
authoring — say so rather than bending `EngineRotatingPart` into it.

### 4.2 Screens: static geometry on both sides

BmAK's screen is a **0.3188 × 0.1512 m / 100-face quad** whose master material has no texture at all
(`COCKPIT.md` §6.3) — the picture is not in the asset, so there is nothing to animate or swap.

JC3's runtime-changeable surface evidence is thin and points at **whole-part swap**, not texture
animation:

| route | what it actually is |
|---|---|
| `mshswap` twin `.lod` models | a second model per light part (`sportsmuscle_headlight_f_l_01mshswap.lod`, `…_signal_r_lmshswap.lod`, `…_taillight_r_lmshswap.lod` — `DECODE_DEPTH.md:302-326`): a whole-part variant, chosen by state |
| battle-mode light variant | the wheel-arch `HeadLight` row ships a **red battle variant** in our build (`wheel-spin-and-animation-plan.md` §3.3, citing `card-B-07.md:476`) |
| palette tint | an **entity-graph `Palette` module** (`tints[i].tint_r/g/b`) written to shader `cb6` by **engine code whose binding is UNKNOWN** (`TINT.md` §1) — per-entity, not a per-frame runtime input |
| material tint/emissive setter | **no decoded vehicle-side setter** in the fleet |

So the faithful build is: **one emissive screen quad on the body part, lit at a fixed level**, matching
BmAK's own "geometry ships, picture does not". A second material variant selected on the mode switch
(same mechanism as the battle-mode light rows) is the only evidence-backed way to change it later.

---

## 5. The carrier table — what to attach, and what to feed

| cabin element | BmAK reality | JC3 joint / carrier | value to feed | confidence |
|---|---|---|---|---|
| **steering wheel** | absent — no geometry, no bone | cut a new **`batmobile_yoke`** part (pivot at the panel centre, z −1.5097) and give it behaviour **`SteeringWheel`** (`steering_turn`, `use_target_position_as_angle = 0`, `lod = 1`) — the same row 9 chassis already use | `steering_turn = (steer_axis + 1) / 2`; the part's sweep is set by **our** hinge, because BmAK supplies no sweep | behaviour decoded; sweep is ours to choose |
| **dials / needles** | absent | **none** — no position-driven rotating behaviour exists | nothing | absence on both sides |
| **centre screen** | quad ships, texture does not | keep the quad on the body part with an **emissive material**; no joint | constant emissive; a second material variant only if a state change is wanted | static on both sides |
| **driver panel** | 1,043 static faces | body part geometry, no joint | — | decoded |
| **dashboard lamp** | `Dashboard_Light` / `Dashboard` socket (MK2, Funhouse, Joker tables) | existing JC3 light row on the dash part (same binding a light uses: `LIGHT_SYSTEM.md` §6) | on while driving | decoded socket |
| **seat** | 9 bones / 150.7468 cm, 2.2333 s open / 2.2667 s close | **no `Land_Seat` behaviour exists** — `Land_Seat` is a *damage type* (196 parts), not a moving part; the door/hatch behaviours carry no seat row | — | no carrier (UNKNOWN route) |
| **canopy** | 2 bones / 71.0094 cm / 0.3 s | a **door part** (`FrontLeftDoor` family) or `LandingGearHatch` on a `.physicsc` hinge — already planned | hinge sweep + 0.3 s timing | covered by `entry-exit-and-controls-plan.md` |

Two things this table deliberately does **not** do: it does not put a `SteeringWheel` behaviour on a
part whose sweep we have not measured, and it does not repurpose a rotating behaviour for a needle.

---

## 6. Build order (when the operator approves)

1. **Yoke part** — cut `batmobile_yoke` from the panel region, pivot on the column axis (perpendicular
   to the 35.2°-from-vertical screen normal, i.e. the driver's line of sight), add it to
   `parts_manifest.json` (currently `left_in_body`), give it `SteeringWheel` + `steering_turn`.
   Pick the sweep **from the JC3 donor by measurement** (step 4), not from a guess.
2. **Screen** — emissive quad on the body part; no joint. Leave the `Dashboard_Light` socket wired.
3. **Seat/canopy** — no new work; the entry/exit plan owns the canopy and the seat has no carrier.
4. **Measure before shipping the ratio** — the 5-minute experiment in §7.

---

## 7. The 5-minute experiment that settles the sweep

Cheapest, read-only until the last step:

1. In `Builds/test-091/.../v0300_car_kensington_sportsmuscle/`, the entity's `.ee` names part 7 as
   `sportsmuscle_steeringwheel` with `body = 27`. Decode `sportsmuscle.physicsc`'s 9
   `hkpLimitedHingeConstraintData` **frames** (already in `PHYSICS_LIMITS.json → transforms`) and keep
   the one whose pivot sits in the cabin (|x| ≈ 0.3–0.5 m, y ≈ 0.9–1.2 m, z between the front axle and
   the centre). That identifies the hinge *if* the wheel has one — which the limit pairs in §3.2 suggest
   it does not.
2. If step 1 finds nothing (most likely), the wheel is **kinematic**: watch it in-game at full lock and
   read the angle off the donor wheel's spokes, or dump `steering_turn` at full left / full right. One
   of the two gives the sweep, and the sweep is the only number this report is missing.
3. Pass the measured sweep into our part's hinge, keep `steering_turn = (axis + 1) / 2`, and the yoke
   then matches the donor's feel by construction.

No game process was started for this report; no mesh, part, module, rig or build file was written.

---

## 8. Checks run

| check | result |
|---|---|
| cabin bones enumerated from the rig | 10 `Chair*` bones, 0 steering/dial/screen bones (`BONES.md:123-132`) |
| yoke absence | `COCKPIT.md` §1 ("- none -") + §6.1 (4 faces in the hand box) |
| build schema agrees | `spec-schema3.json` → `left_in_body` "steering yoke … no pivot exists" |
| idle clip | `Batmobile_V2_Idle`: 2 frames, 0.0333 s, 1 active bone, **0 moved**, 0.0° / 0.0 cm |
| driving clips | 9 clips scanned; **0** moved cabin bones |
| seat/canopy numbers | Chair open 2.2333 s / close 2.2667 s / 9 bones / 150.7468 cm; Cockpit open+close 0.3 s / 2 bones / 71.0094 cm |
| screen geometry | 0.3188 × 0.1512 m, 100 faces, 404.1 cm², centre (0, 1.4857, −1.7552) |
| panel geometry | slot 10, 1,043 faces / 720.3 cm², z −1.8981..−1.5097 |
| JC3 behaviour counts | `SteeringWheel` 20 parts / 20 entities / 9 chassis; `SteeringFork` 27 parts / 11 chassis; 12 rotating behaviours, 0 position-driven |
| donor hinge pairs | 9 hinges in `sportsmuscle.physicsc`: 0..80, −35..0, 0..80, −35..0, −15..0, 0..30, 0..70, −15..0, 0..90 — none wheel-like |
| steering speed curves | 60→20 (Playable/MK2/Funhouse), 60→15 (Joker); `SteerSpeedVsSpeedCurve` 720/720 vs 220/20; units UNKNOWN |

## 9. Change record (per `AGENTS.md`)

1. **Intended change:** add one report that lists the BmAK cabin parts and their motion, states why
   the angle-per-unit ratio is UNKNOWN on both sides, and names the JC3 carrier for each element.
2. **File:** `tmp/freebuff/reports/steering-wheel-and-dash-animation-plan.md` — the brief names this
   path and every comparable plan lives in `tmp/freebuff/reports/`. No `Research/` card is regenerated
   and no build file is written.
3. **Revert:** delete this file. Nothing else changed (read-only JSON/Python queries and
   `write_file`).

## 10. UNKNOWNs

| # | UNKNOWN | settler |
|---|---|---|
| U-1 | degrees of yoke per unit steering input | no BmAK yoke exists (§1, §3.1); if a yoke is built, the ratio is a design constant |
| U-2 | the JC3 `SteeringWheel` part's hinge sweep | decode the donor's hinge frames, or read the donor wheel at full lock in-game (§7) |
| U-3 | who writes `steering_turn` | `MOVING_PARTS.md` §4: no file read here names the writer; the animation system is inferred from the binding |
| U-4 | whether the donor steering wheel is hinged at all | `sportsmuscle.physicsc` has 9 hinges, none wheel-like; joints' body links UNKNOWN (`PHYSICS_ROLES.md` §4) |
| U-5 | units of `StandardSteeringSpeedCurve` / `SteerSpeedVsSpeedCurve` | `MECHANICS.md` names the properties and the points, not the units |
| U-6 | any runtime material/texture swap for the screen | `TINT.md` (palette), `DECODE_DEPTH.md` (`mshswap`) and the battle-light variant are whole-part routes; no per-frame material setter decoded |
| U-7 | a carrier for the seat recline | no seat behaviour in the 12+25+14+1+1 tables; `Land_Seat` is a damage type only |
