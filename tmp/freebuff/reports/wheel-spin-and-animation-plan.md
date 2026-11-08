# Wheels in motion — BmAK's wheel rig vs the JC3 car rig, and the two numbers we need

**STATUS: done (plan, read-only).** BmAK steers at **`SUSP2_Wheel_*`**, spins at
**`Wheel_Parent_*`**, and puts the tyre (`Wheel_*_Vis`), the disc (`Wheel_Frnt_*_Disc`) and the
fan (`Wheel_Frnt_*_Fan`) under the spin joint. Its contact radius is **`WheelRadius` 64.0 cm**
(0.640 m), its visual tyre is **Ø 1.3711 m**, and the brake-disc glow is **an emissive map plus a
material switch — no numeric ramp exists**. JC3 exposes the same motion as **four separate wheel
parts** on a front-steered car with **`steer_angle_min_speed_deg` 35 / `steer_angle_max_speed_deg`
15** and **`Tire.radius` 0.38 m**, measured from our build.

**The two numbers our private rig needs:**

| | value | why |
|---|---|---|
| **steering joint range** | **±35° (low speed) → ±15° (high speed)**, so build the steer joint for **±35°** and let the module clamp | decoded from our build's `LandSteering` (donor values equal the fleet median) |
| **wheel-rotation scale** | **0.554 ×** the JC3 wheel angle (see §5.2 for the alternative 0.594 if we drive from BmAK's 0.640 m) | the Batmobile visual tyre (r 0.68555 m) is **1.804×** the JC3 physics radius (0.38 m) |

Both are measured/derived below with the arithmetic printed; BmAK's own steer lock is **UNKNOWN**
— no decoded field carries it (§9).

---

## 1. Evidence base

| fact | value | source |
|---|---|---|
| bone chain, front left | `SUSP2_Wheel_Front_Left` → `Wheel_Parent_F_L` → `Wheel_Front_Left_Vis` / `Wheel_Frnt_Left_Fan` / `Wheel_Frnt_Left_Disc` → `Damper_Left_Front_02` | `BONES.md:46-50` |
| spin joint | `Wheel_Parent_F_L` has **0 faces** (pure joint) and is a child of `SUSP2_Wheel_Front_Left` | `BONES.md:46`; `BONES.json:1410` |
| steer joint | `SUSP2_Wheel_Front_Left` carries the parent of the spin joint (the only bone between the chassis and the wheel) | `BONES.md:46` |
| tyre bone | `Wheel_Front_Left_Vis`, 6,700 faces | `BONES.md:47`; `TYRES.md:64` |
| disc bone | `Wheel_Frnt_Left_Disc`, 13,850 faces, parent `Wheel_Parent_F_L` | `BONES.md:49` |
| fan bone | `Wheel_Frnt_Left_Fan`, 32 faces | `BONES.md:48` |
| **contact radius** | **`WheelRadius` 64.0 cm** on all four wheels (offset 568, `0x238`) | `TYRES_PACKAGE.md:27,32`; `OFFSETS.md:526` |
| visual tyre | x 0.7314 wide, **Ø 1.3711 m** max radial | `TYRES.md:50` |
| visual disc | **Ø 1.5962 m** max radial, spans the tyre's width | `TYRES.md:51` |
| wheel animation class | `wheels/strafe` = 16 sequences, 532 active tracks, 200 moved | `ANIMATIONS.md:3,4` |
| strafe/drift clips | `BatMobile_Drift_In_01` 96 fr / 3.167 s; `Batmobile_V2_Spin` 138 fr / 4.567 s; `Batmobile_V2_Tank_Strafe` 82 fr / 2.700 s; `Batmobile_V2_Fans_Spin` 101 fr / 3.333 s | `ANIMATIONS.md:4` |
| measured rotation in a wheel clip | `BatMobile_Drift_In_01`: `max_rotation_deg` **179.993**, `max_translation_cm` 6583.8698 | `ANIMATIONS.json` (same sequence record) |
| disc material | `Batmobile_V3_Discbreak_MIC` → `Material_MASTERS.Batmobile_V3_Discbreak`, **3,712 faces**, textures `BRAKE_DISC_D/N/R` | `SLOTS.md:38` |
| disc emissive | `Batmobile_V3_Discbreak` EmissiveColor ← **StaticSwitchParameter**; MetalMask ← **ScalarParameter**; no numeric value recorded | `MATERIALS.md:21,70,109` |
| disc emissive texture | `Batmobile_V2_BRAKE_DISC_E` **1024×1024 PF_DXT1**, wired as `EmissiveTexture` in `Batmobile_Body_MASTER` | `TEXTURES.md:9,112,213,309`; `objects.jsonl:668` |
| wheel light on the disc | `LWheelLight`, `LWheelLight_top`, `LWheelLight_bottom` parented to `Wheel_Frnt_Left_Disc` | `SOCKETS_JC3.md:106-108`; `SKINS.md:884,908,909` |
| BmAK audio mirror of spin | `BML_WheelSpeed` parameter, 0→0 / 700→200 in the engine and burnout mixes | `AUDIO_FEATURES.md` §engine/burnout |
| **JC3 steer lock** | `steer_angle_min_speed_deg` **35**, `steer_angle_max_speed_deg` **15** | decoded from our build (§4) |
| JC3 steer response | `t_to_full_steer_s` **1.2**, `max_speed_t_to_full_steer_s` **0.85**, `steer_curve_falloff` **2**, `steer_in_speed_factor` **1.5**, `countersteer_speed_factor` **2** | decoded from our build (§4) |
| JC3 wheel radius | `Tire.radius` **0.38 m**, `rim_radius` **0.30 m** (front and rear) | decoded from our build (§4) |
| JC3 wheel count / steer layout | `number_of_wheels` **4**, `is_rear_steered` **0**, `is_all_wheel_steered` **0**, `wheels_friction_type` 0 | decoded from our build (§4) |
| JC3 steering model | `steering_type` = **FrontSteered** on every readable module; no rear/all-wheel mode is shipped | `DRIVE_CARRIERS.md` §C3 |
| JC3 wheel parts | `sportsmuscle_wheel_f_l/_f_r/_r_l/_r_r` are separate part models, each with its own `.lod`/`.rbm` | `DECODE_DEPTH.md:331-337`; `DECODE_DEPTH.json:2820-2850` |
| JC3 wheel-arch lights | `HeadLight` on `sportsmuscle_wheel_f_l_arch`, range 2.0 angle 10.0, plus a battle-mode red variant | `card-B-07.md:472,476`; `card-T-15.md:478` |
| JC3 wheel damage type | `Land_Wheel` (and `Land_Steering_Wheel`) exist in the 24-row part table | `DAMAGE_MODEL.md:64`; `DAMAGE_MODEL.json:1708,1818` |

## 2. How BmAK turns a wheel

**Hierarchy (front left, from the bind skeleton).**

```
Batmobile_Chassis
  └─ SUSP1_Wheel_Front_Left      (suspension upper, 14 faces)
      └─ SUSP2_Wheel_Front_Left  (suspension lower / the steer joint, 24 faces)
          └─ Wheel_Parent_F_L    (0 faces — the spin joint)
              ├─ Wheel_Front_Left_Vis     (tyre, 6,700)
              ├─ Wheel_Frnt_Left_Fan      (fan, 32)
              └─ Wheel_Frnt_Left_Disc     (hub/disc/strut, 13,850)
                  └─ Damper_Left_Front_02 (758)
```

This is the whole reason the Batmobile's wheels can do both jobs: **steer is `SUSP2_*`, spin is
`Wheel_Parent_*`**, and the tyre/disc/fan hang off the spin joint. The disc is **not** a child of
the tyre — it is a sibling, which is why the disc can sit still while the tyre spins (a locked
wheel) and why its material is separate.

**Radii, and the one that matters.**

| quantity | value | meaning |
|---|---:|---|
| `SVehicleWheel.WheelRadius` | **64.0 cm** = 0.640 m | the physics **contact** radius, all four wheels (`TYRES_PACKAGE.md:27`) |
| visual tyre Ø | **1.3711 m** → r 0.68555 m | the mesh (`TYRES.md:50`) |
| visual disc Ø | **1.5962 m** → r 0.79810 m | the mesh (`TYRES.md:51`) |
| contact circumference | 2π·0.640 = **4.0212 m** | one physics wheel turn per 4.0212 m |
| visual tyre circumference | 2π·0.68555 = **4.3074 m** | one visual turn per 4.3074 m |

**Spin speed.** BmAK does not keyframe wheel spin; the spin joint is driven by the sim from the
contact radius (`SVehicleWheel.WheelRadius`), which is exactly how Unreal's `SVehicle` works. The
only *measured* spin in the animation data is the chassis spin, not the wheel: `BatMobile_Drift_In_01`
moves bones by up to **179.993°** over 96 frames (`ANIMATIONS.json`), and `Batmobile_V2_Spin` is the
chassis rotating 4.567 s worth — neither is a wheel rate. The audio side confirms the quantity the
game feeds its mix: **`BML_WheelSpeed` 0→0, 700→200** (`AUDIO_FEATURES.md` §engine, §burnout), i.e.
a wheel-speed value with a 0–700 nominal span, but no unit is decoded for it.

**What is *not* decoded:** BmAK's steering lock and its steer input curve. A grep of
`CLASS_DEFAULTS.md` for `steer` returns only `ImpactRoadAssistSteeringFactor` 30.0,
`DriftAngularVelocityBySteer`, `DriftSpeedBySteer`, `DriftCorrectionSteerSpeed` 1.0 — all drift
shaping, **no angle limit**. `SVehicleWheel`'s 152 named offsets carry radius, suspension travel and
slip factors, **no steer-limit field**. So BmAK's lock is **UNKNOWN**, and the only honest number to
ship is the JC3 one (§4-5).

## 3. Brake-disc glow

**What exists, precisely:**

| layer | fact | source |
|---|---|---|
| geometry | `Wheel_Frnt_Left_Disc`, 13,850 faces, Ø 1.5962 m, a sibling of the tyre under the spin joint | `BONES.md:49`; `TYRES.md:51` |
| material | `Batmobile_V3_Discbreak_MIC` → `Material_MASTERS.Batmobile_V3_Discbreak`; 3,712 faces | `SLOTS.md:38` |
| emissive channel | `EmissiveColor` ← **`MaterialExpressionStaticSwitchParameter`** — a switch, not a scalar | `MATERIALS.md:21` |
| metal mask | `MetalMask` ← **`MaterialExpressionScalarParameter`** — a parameter exists, its value is not recorded | `MATERIALS.md:21` |
| emissive texture | `Batmobile_V2_BRAKE_DISC_E`, **1024² PF_DXT1**, sampled as `EmissiveTexture` in `Batmobile_Body_MASTER` | `TEXTURES.md:9`; `objects.jsonl:668` |
| lights on the disc | `LWheelLight`, `_top`, `_bottom` socketed to `Wheel_Frnt_Left_Disc` | `SOCKETS_JC3.md:106-108` |

**Conclusion:** the "glow" is **texture-driven** (`BRAKE_DISC_E` through a static switch in the body
master) plus **three small lights socketed to the disc**. There is **no** decodable
temperature/threshold/intensity ramp for it anywhere in the BmAK files read: no `BrakeGlow`,
`DiscHeat`, `DiscTemperature` or similar member appears in `CLASS_DEFAULTS.md`, `MATERIALS.md`,
`LIGHTS.md` or `PHYSICS.md`. Any JC3 implementation of "glowing brake discs" is therefore **a new
material/light effect**, not a translated value.

## 4. What the JC3 car rig actually exposes

Measured from our own build (`Builds/test-003/.../v0300_car_kensington_sportsmuscle/modules/default/*.vmodc`,
decoded with `Gibbed.JustCause3.ConvertAdf.exe --e`; 17 modules opened, values below printed by that run):

| module.member | value in our build |
|---|---:|
| `LandSteering.steer_angle_min_speed_deg` | **35** |
| `LandSteering.steer_angle_max_speed_deg` | **15** |
| `LandSteering.t_to_full_steer_s` | **1.2** |
| `LandSteering.max_speed_t_to_full_steer_s` | **0.85** |
| `LandSteering.steer_curve_falloff` | **2** |
| `LandSteering.steer_in_speed_factor` | **1.5** |
| `LandSteering.countersteer_speed_factor` | **2** |
| `LandSteering.wheel_drift_aligning_strength` | 0.30 |
| `LandSteering.wheel_load_responsiveness` | 0.20 |
| `LandGlobal.number_of_wheels` | **4** |
| `LandGlobal.number_of_front_wheels` | −1 (derived) |
| `LandGlobal.is_rear_steered` | **0** |
| `LandGlobal.is_all_wheel_steered` | **0** |
| `LandGlobal.wheels_friction_type` | 0 |
| `Tire.radius` (front, rear) | **0.38** |
| `Tire.rim_radius` (front, rear) | **0.30** |
| `Tire.broken_wheel_radius_fraction` (front, rear) | 0.80 |
| `Tire.broken_wheel_friction_fraction` (front, rear) | 0.50 |
| wheel-damage block `radius` | 0.55 (module not pinned in this run) |
| `LandSteering.base_wheel_hardpoint_positions` | present (4 hardpoints) |
| `Suspension.wheel_hardpoint_offsets` | present (`wheel_index` 0-3) |

Fleet context, so the donor is not an outlier: `steer_angle_min_speed_deg` 20..45 (median 35) and
`steer_angle_max_speed_deg` 10..35 (median 15) over n=252, `t_to_full_steer_s` 0.25..10 (median
1.2) (`VOCABULARY.md:885-892`; `DRIVE_CARRIERS.md:154-158`). Our build sits **exactly on the
median**, so the numbers above are the fleet's own supercar values, not a single car's quirk.

**Structural difference that decides the rig.** BmAK puts the wheels inside one skinned mesh with a
steer bone and a spin bone. JC3 puts each wheel in its **own part model**
(`sportsmuscle_wheel_f_l.lod` … `_r_r.lod`, plus `mshswap` twins, `DECODE_DEPTH.md:331-337`), and
the donor's wheel-arch part is parented to the wheel part, with `Damper_Left_Front_02` (594 faces)
and `Wheel_Frnt_Left_Disc` (18) inside it (`card-B-04.md:483-500`). JC3 steers by rotating those
four parts from `LandSteering`; it has **no per-wheel bone the modder can name** and only
`FrontSteered` ships (`DRIVE_CARRIERS.md` §C3).

## 5. The numbers our private rig needs

### 5.1 Steering joint range

**Ship ±35° as the joint's mechanical limit.** Justification, all decoded:

* `steer_angle_min_speed_deg` **35** is the lock **at low speed** — the largest angle the game will
  ever ask the wheels to reach, so a joint that cannot do 35° will clip at parking speed.
* `steer_angle_max_speed_deg` **15** is the lock **at high speed** — the module clamps down to it,
  so the joint never needs more than 35°, and 15° is the angle the car spends its time at.
* The clamp is shaped by `steer_curve_falloff` **2** and reaches full lock in
  `t_to_full_steer_s` **1.2 s** (0.85 s at max speed) — those are rates, not limits, and live in the
  module, not the rig.
* Rear wheels do not steer (`is_rear_steered` 0, `is_all_wheel_steered` 0), so only the two front
  joints need the ±35° range; rear joints can be strict spin-only.

Reference frame: the joint is the BmAK `SUSP2_Wheel_Front_*` analogue. If the rig is built on the
Batmobile bones, put the 35° range on `SUSP2_Wheel_Front_Left/Right` and keep `Wheel_Parent_F_L/R`
a pure spin joint (0 faces, `BONES.md:46`). If the rig is built on the JC3 wheel parts, the 35° is
the part's yaw limit around the donor hardpoint (`Suspension.wheel_hardpoint_offsets`, 4 entries,
`wheel_index` 0-3).

### 5.2 Wheel-rotation scale

The physics gives angular velocity from **its** radius; the visible tyre has **its own** radius.
Driving the rig from the physics angle unscaled makes the Batmobile's big wheel spin too fast by the
radius ratio:

```
JC3 physics radius           r_phys = 0.38 m        (Tire.radius, our build)
Batmobile visual tyre radius r_vis  = 0.68555 m     (Ø 1.3711 m / 2, TYRES.md:50)

ratio = r_phys / r_vis = 0.38 / 0.68555 = 0.5543

=> visual wheel angle = 0.554 x (physics wheel angle)
```

Cross-checks, so the number is not a one-off:

| check | arithmetic | result |
|---|---|---|
| circumferences | 2π·0.38 = 2.38761 m vs 2π·0.68555 = 4.30740 m | 2.38761 / 4.30740 = **0.5543** |
| at the 40 m/s ceiling | ω_phys = 40/0.38 = 105.26 rad/s (**1005.1 rpm**); ω_vis = 40/0.68555 = 58.35 rad/s (**557.3 rpm**) | 58.35/105.26 = **0.5543** |
| if driven from BmAK's contact radius instead | 0.38 / 0.640 | **0.5938** |

So: **0.554** when the rig's wheel geometry is the Batmobile tyre (the normal case), **0.594** only
if the wheel is modelled at BmAK's 64 cm contact radius. Both keep the tread speed equal to ground
speed; neither changes the physics radius, which must stay `Tire.radius` 0.38 m or the car's
handling and its `Land_Wheel` damage thresholds move with it.

**Spin direction:** JC3's four wheel parts are separate models, so the left and right sides spin
opposite in world space. Mirror the sign per side (`_f_l`/`_r_l` one sign, `_f_r`/`_r_r` the other,
or negate by the part's local X); nothing in the BmAK data names a sign, and get this wrong and the
wheels visibly counter-rotate.

**Why not just enlarge `Tire.radius` to 0.68555?** That is the tempting one-line "fix" and it is
wrong twice: it changes the contact patch and the ride height (the hardpoints are set for 0.38 m,
`Suspension.wheel_hardpoint_offsets`), and it changes the `broken_wheel_radius_fraction` 0.80
threshold that drives `Land_Wheel` damage. Scale the *visual* angle, leave the physics radius alone.

### 5.3 Brake-disc glow for the rig

No value exists to copy (§3), so the rig needs **an effect, not a number**:

1. **Emissive map** on the disc material: carry `Batmobile_V2_BRAKE_DISC_E` (1024² DXT1) or the
   `Batmobile_V3_BRAKE_DISC_D` set into the JC3 material's emissive slot. BmAK's own master feeds it
   through a **static switch**, so the cheapest faithful port is a two-state material (off / on) —
   exactly what JC3's `sportsmuscle_wheel_f_l_arch` battle-light variant already does
   (`card-B-07.md:476`, red arch light).
2. **Disc lights**: BmAK sockets `LWheelLight`, `_top`, `_bottom` to `Wheel_Frnt_Left_Disc`. JC3's
   nearest carrier is the **`HeadLight` behaviour on the wheel-arch part**, already shipped in our
   build (range 2.0, angle 10.0, plus a red battle variant) — reuse that row, retarget the socket,
   do not add a light system.
3. **Trigger**: with no decoded BmAK threshold, tie it to the only decoded braking signals — the
   `Brakes` module's handbrake and the `Land_Wheel` slip (`min_skid_velocity_for_skid_ms`,
   `skid_velocity_scale`, `DRIVE_CARRIERS.md`), i.e. glow while the wheel is slipping/braking.

## 6. Build recipe (what to change, when the operator approves)

| # | change | file / value |
|---|---|---|
| R-1 | steer limit on the two front joints | **±35°**, clamped by `LandSteering` 35→15 |
| R-2 | wheel spin | visual angle = **0.554 ×** physics angle; sign mirrored left/right |
| R-3 | physics radius | **unchanged** at `Tire.radius` 0.38 / `rim_radius` 0.30 |
| R-4 | disc glow | emissive map + two-state switch, on the existing disc material; reuse the wheel-arch `HeadLight` row rather than new lights |
| R-5 | steer response | leave `t_to_full_steer_s` 1.2, `max_speed_t_to_full_steer_s` 0.85, `steer_curve_falloff` 2, `steer_in_speed_factor` 1.5, `countersteer_speed_factor` 2 as decoded — they are the fleet median, not the donor's quirk |

None of R-1..R-5 was applied in this pass: no `.vmodc`, mesh, rig, material or build file was
written. This is the plan only.

## 7. Checks run

| check | result |
|---|---|
| bone chain re-read | `SUSP2 → Wheel_Parent_F_L → Vis/Fan/Disc → Damper` (`BONES.md:46-50`) |
| spin joint has no geometry | `Wheel_Parent_F_L` faces 0 (`BONES.md:46`) |
| radii | `WheelRadius` 64.0 cm (`TYRES_PACKAGE.md:27`); tyre Ø 1.3711 m, disc Ø 1.5962 m (`TYRES.md:50,51`) |
| disc material | `Batmobile_V3_Discbreak_MIC`, 3,712 faces; EmissiveColor ← StaticSwitch, MetalMask ← ScalarParameter (`SLOTS.md:38`; `MATERIALS.md:21`) |
| disc emissive texture | `Batmobile_V2_BRAKE_DISC_E` 1024×1024 PF_DXT1 as EmissiveTexture (`TEXTURES.md:9`; `objects.jsonl:668`) |
| **build modules decoded** | 17 `.vmodc` opened with Gibbed; `steer_angle_min/max` 35/15, `Tire.radius` 0.38, `rim_radius` 0.30, `number_of_wheels` 4, `is_rear_steered` 0 |
| fleet sanity | 35/15 and 1.2 s are the n=252 medians (`VOCABULARY.md:885-892`) |
| scale arithmetic | 0.38/0.68555 = 0.5543; 2.38761/4.30740 = 0.5543; 58.35/105.26 = 0.5543; alt 0.38/0.640 = 0.5938 |
| BmAK steer lock | **not found** — `CLASS_DEFAULTS.md` has only drift/impact steering factors; `SVehicleWheel` offsets have no steer-limit field |
| animation spin measurement | `BatMobile_Drift_In_01` max rotation 179.993° (chassis/pose motion, not a wheel rate) |

## 8. Change record (per `AGENTS.md`)

1. **Intended change:** add one report giving the rig's steering range and wheel-rotation scale from
   the decoded BmAK rig, BmAK's disc-glow mechanism, and the JC3 rig's exposed values.
2. **File:** `tmp/freebuff/reports/wheel-spin-and-animation-plan.md` (this file). Correct file
   because the brief names it and every comparable plan is in `tmp/freebuff/reports/`. No `Research/`
   page is regenerated and no build file is written.
3. **Revert:** delete this file. Nothing else changed; the only command with side effects was the
   Gibbed decode, which wrote a temp XML per module and deleted it in the same run.

## 9. UNKNOWNs

| # | UNKNOWN | what settles it |
|---|---|---|
| U-1 | BmAK's steering lock and steer curve | no field decoded: `CLASS_DEFAULTS.md` has only drift/impact steering factors, `SVehicleWheel`'s offsets carry radius/travel/slip only; needs the `RVehicle` steer function bodies or a frame-by-frame look |
| U-2 | the unit and full span of `BML_WheelSpeed` (0..700 with 200 in the mix) | the AkSwitch group definition; the parameter is decodable but its unit is not stated in the bank dump (`AUDIO_FEATURES.md`) |
| U-3 | the brake-disc glow's on/off condition and intensity | the `StaticSwitchParameter` and `ScalarParameter` inside `Batmobile_V3_Discbreak`; no value or driver is recorded in `MATERIALS.md` |
| U-4 | whether the rig builds on BmAK bones or on JC3 wheel parts | the operator's rig choice; both are described in §5.1 because the geometry exists on both sides |
| U-5 | whether JC3 exposes the wheel part's rotation to a mod at all, or only inside the native steering code | untested; the fleet has no per-wheel member (`DRIVE_CARRIERS.md` §C1), so this is the first thing a 5-minute in-game test should settle |
| U-6 | the 0.55 `radius` printed in the wheel-damage block | module not pinned in the decode run; needs the XML beside each value |

No game process was started; no build, module, mesh, material, rig or install was written.
