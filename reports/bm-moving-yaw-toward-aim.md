# Battle mode, moving: what turns the nose toward the aim — member set, offsets, input, and the pivot question

Requirement being reproduced (operator, who has played BmAK, 2026-11-08):

> in battle mode, driving forward with no steering input still swings the nose toward where the
> camera points.

This report does not test whether that happens. It asks which BmAK member or event produces it, what
the input to that member is (stick, camera yaw, or a fixed rate), what each carries as a unit and at
what offset, and which prior report already settled what.

Labels used throughout:

* **decoded** — read at the file, export, member and offset named, and quoted.
* **derived** — arithmetic or a stated rule over decoded inputs, said in the same sentence.
* **UNKNOWN** — searched and absent, with the search run and the file that would settle it.

Nothing below is filled from memory or from another engine's convention.

---

## 0. Answer in one line

The turn is not driven by a steering command from script and not by a constant rate: the sim carries
a **world-space aim direction** (`RVehicleSimBatmobile.AbsoluteMoveDirection`, `Vector3` at
`0x378` / 888) that is separate from the body's rotation, and the body yaw is servoed onto it with
`BattleModeSteerAngleFactor` 1 (factor, `0x300`), clamped by `BattleModeMaxSteering` 80 (deg,
`0x2cc`), with the rear axle counter-steering at `BattleModeTrailingSteerFactorMoving` −0.25 (factor,
`0x320`) and a stop-and-turn gate at `BattleModeStopAndTurnAngleMoving` 90 (deg, `0x2fc`). The
shipped cars run `BattleModeYawOffset` **0** (int rotator units, `0x1910`), i.e. the nose is aligned
with that aim direction — the 90° that two earlier reports quote is the **class default**, which every
shipped archetype overrides to zero. With the stick centred the aim direction resolves to where the
camera looks, which is the behaviour the operator describes.

What is **not** in any file: the camera→direction resolution itself, and the arithmetic inside
`RVehicleSimBatmobile.SetDriveMode` (a native stub). Those are UNKNOWN, with the settling file named
in §6. `BattleModeSteerBiasRate` 3.0 exists and is rate-named, but no decoded consumer of it exists —
so "fixed rate" is **not** supported as the mechanism.

---

## 1. What the three named reports already settle, and what they leave open

### 1.1 `tmp/freebuff/reports/four-wheel-drive-and-spin-in-place-build-plan.md`

**Settles.**

| # | what | where |
|---|---|---|
| 1 | The battle value set, member by member, with offsets and per-archetype numbers: `BattleModeLatSlipScale` 0.75, `LongSlipScale` 1.25, `TrailingSteerFactorMoving` −0.25, `DriveForceFactor` 500, `DrivingForceZOffset` 20 cm, `SteerAngleFactor` 1, `ThrottleSpeed` 10, `StopAndTurnAngleStationary` 30°, `YawOffset` 0. | §3 table, lines 140–151 |
| 2 | JC3 has **0** camera-relative members in any driving module and **0** keymap actions carrying a 2-D stick into a vehicle; the only whole-stick binding is `LSTICKGENERIC → MOVE_ALL`, on-foot scope. | line 130, and the M2a row at line 39 |
| 3 | The input gap is a **stick→vehicle vector**, i.e. an input problem, so an extra entity cannot close it ("an extra entity carries values, not inputs"). | line 375 |
| 4 | Three ranked routes for that input: `MOVE_ALL` reuse, an `.epe` graph thrust along the **camera yaw**, or an operator amendment that drops "move where the stick points" and keeps "the car turns to face the camera". | lines 183–188 |
| 5 | The battle number set forces the second-entity route (M2b); the move itself does not. | §8, lines 373–383 |

**Leaves open.**

* It treats "the car turns to face the camera" as the *stance* half of a second-entity value set
  (line 188) rather than as a **per-tick servo** with its own members. It never names the member that
  turns the heading while the car is moving, and never mentions
  `BattleModeStopAndTurnAngleMoving` (90°) or `BattleModeSteerBiasRate` (3.0).
* Its M2a row reads "camera-relative move" as "move where the stick points" and concludes "not
  closable in data" (line 39). That conclusion is about *translation*; the *rotation* half is not
  assessed at all.
* The `AbsoluteMoveDirection` field is not cited anywhere in it.

### 1.2 `tmp/freebuff/reports/G3-02l.md`

**Settles.**

| # | what | where |
|---|---|---|
| 1 | `EBatmobileDriveMode` = `BMDM_Drive` 0, `BMDM_TurnOnSpot` 1, `BMDM_BattleMode` 2; `PursuitMode.BeginState` calls `SetDriveMode(0)`, `BattleMode.BeginState` calls `SetDriveMode(2)`, and **no script body passes 1**. | §"What was decoded" 1–2 |
| 2 | `BattleMode.Tick` has no steering call at all; the battle movement "is implemented inside the native simulation", with `AbsoluteMoveDirection`, `BattleModeSteerAngleFactor`, `BattleModeMaxSteering`, `BattleModeTrailingSteerFactorMoving` and `BattleModeYawOffset` as its fields. | §4, quoted in §1.2 note below |
| 3 | The 40-field driving-mode member set with class-default values: `StopAndTurnAngleStationary` 60, `…AngleMoving` 90, `SteerAngleFactor` 2.5, `MaxSteering` 80, `TrailingSteerFactorTurnOnSpot` 1.0, `…Moving` −0.5, `ThrottleSpeed` 5. It lists the family but **not** `SteerBiasRate`. | §4 |
| 4 | Script's only stick reads are `PlayerInput.aBaseY` / `aStrafe` in `CheckBattleStrafe` / `PursuitStrafe`, which also read `BatmobilePawn.Rotation` and `BattleModeYawOffset`; `PursuitMode.Tick` reads `Core.OutputSteering` and passes it to `SetWantAirBrakes`. | §5, line 46 |
| 5 | `AbsoluteMoveDirection` (`StructProperty`, `0x0378`) is read/written by `PursuitMode.Tick` and by `DrivingMode.StartRun`/`EndRun`. | line 46 |

Quote, `G3-02l.md` line 46:

> `BattleMode.Tick` has no steering call at all: it only handles audio state, the winch, stuck-flip
> recovery and the `TryToChangeMode(PursuitMode)` exits.

**Leaves open.**

* The arithmetic inside `SetDriveMode` — "5 bytes `29 <param ref>` and nothing else", native
  ("UNKNOWN 1"). So the per-mode torque/steer arithmetic is not in the package.
* It reports `BattleModeYawOffset` as "vehicle CDO value **16384 = 90 deg**" (line 46) and then, in
  the operator-lead section, repeats "turns to face the camera" with a 90° offset. **That is the
  class default, not the shipped value** — `MODES.md:151` records `0` in V2, MK2, Joker and Funhouse
  (§2.3 below). The report therefore leaves the shipped stance ambiguous by 90°.
* It never connects `SVehicleWheel.BattleModeSteerBias` (0x320, per-wheel) to
  `RVehicleSimBatmobile.BattleModeTrailingSteerFactorMoving` (0x320, per-car); `MODES.md:7` warns the
  offset is ambiguous and only the class scoping disambiguates it.

### 1.3 `tmp/freebuff/reports/G3-08c.md`

**Settles.**

| # | what | where |
|---|---|---|
| 1 | Camera-relative control has **no JC3 data carrier**: 6 regex hits, all in `Propellers` (docking strafe), 0 in a driving module — printed as `camera-relative / face-camera control      distinct=  6 drive=0`. | line 46 |
| 2 | The patch gamepad keymap has 16 land-vehicle actions, all discrete; the only 2-D stick binding in either keymap is `LSTICKGENERIC → MOVE_ALL`, on-foot scope. | §3, line 77 |
| 3 | `.epe` graphs do carry `CCameraModifier` (5,796 objects), but "a camera modifier frames the camera; it is not a control path". | line 88 |
| 4 | Verdict on the battle move: code bridge or amendment; recorded as a compromise for the operator. | lines 235, 268 |

**Leaves open.**

* It is a JC3-side carrier hunt only. It says nothing about how BmAK's own sim produces the turn, so
  it cannot say which member the effect needs — only that no JC3 member matches it.
* "Move in the stick direction while the car turns to face the camera" is treated as one requirement
  (line 4) and answered as one negative; the two halves are not separated, and the rotation half is
  assumed to fail because the translation half has no member.

### 1.4 What the three together still did not answer — this report's scope

1. Which **member or event** applies the heading change while the car is moving (none of the three
   names one; two imply "native").
2. Whether the input is the stick, the camera yaw, or a fixed rate, with **unit and offset**.
3. Whether the shipped car runs a 90° yaw offset or a 0° one — the reports disagree in effect.

---

## 2. The BmAK side: script tick, member set, shipped values

### 2.1 The lookup through `objects.jsonl`

`Research/BatmobileGrab/objects.jsonl` (20,128 export records) was scanned for the archetype objects
and for the mode functions (`python` line-scan; 20,128 records, filters `SimulationModel`,
`BattleMode`/`PursuitMode`, class `Function`).

* Four `SimulationModel` archetype objects, one per shipped car, each `RVehicleSimBatmobile`,
  2,328 bytes, 37 tags:

  | line | object | class | size | tags |
  |---:|---|---|---:|---:|
  | 5368 | `Vehicle.BatmobileFunhouse` | `RVehicleSimBatmobile` | 2328 | 37 |
  | 8769 | `Vehicle.JokersBatmobile` | `RVehicleSimBatmobile` | 2328 | 37 |
  | 14313 | `Vehicle.Batmobile_MK2` | `RVehicleSimBatmobile` | 2328 | 37 |
  | 19804 | `Vehicle.Batmobile` | `RVehicleSimBatmobile` | 2328 | 37 |

* Their named tags are the six curves only — `BattleModeVSpeedCurve`, `BoostTorqueVSpeedCurve`,
  `StandardSteeringSpeedCurve`, `StandardTorqueVSpeedCurve`, `SteerSpeedVsSpeedCurve`,
  `TorqueVSpeedCurve`. The scalar tags in these objects are unnamed struct sub-tags in this dump, so
  `objects.jsonl` **cannot** be the source for the scalar values; those are quoted from `MODES.md`
  (which reads the same objects with tag names) in §2.3. This is a limit of the dump, not an absence
  of values.
* **0** `Function` exports under `BattleMode` / `PursuitMode` exist in `objects.jsonl`. The battle
  tick body therefore cannot be read from it; the tick is cited from `DRIVE_MODES.md` §4 (decoded
  from the package's script bytes by `Tools/scripts/grab_drive_modes.py`).

### 2.2 The battle-mode tick

Decoded, `Research/BatmobileGrab/DRIVE_MODES.md` line 109:

> `BattleMode.Tick` has no steering call at all: it only handles audio state, the winch, stuck-flip
> recovery and the `TryToChangeMode(PursuitMode)` exits. So the battle-mode movement (left stick in
> the stick's direction, car turning to face the camera) is implemented inside the native
> simulation, with `AbsoluteMoveDirection`, `BattleModeSteerAngleFactor`, `BattleModeMaxSteering`,
> `BattleModeTrailingSteerFactorMoving` and `BattleModeYawOffset` as its fields.

**Derived:** there is no script event, timer or tick handler that rotates the body toward the aim.
The only battle-mode script that touches orientation is `BattleMode.BeginState`/`EndState`, which
read `BattleModeYawOffset` at three compare sites (`DRIVE_MODES.md` §2 rows 36–37; O8 oracle). The
turn is therefore a native consequence of the field set in §2.3 — not an event a mod can rebind.

### 2.3 The member set that produces the moving turn

Class = declaring class; "class CDO" = `Default__RVehicleSimBatmobile` (export 129779) /
`Default__RVehicleBatmobileBase`; "shipped" = V2 / MK2 / Joker / Funhouse.

| member | class | offset | type | unit | class CDO | shipped | role in the turn | label | source line |
|---|---|---:|---|---|---:|---|---|---|---|
| `AbsoluteMoveDirection` | `RVehicleSimBatmobile` | `0x378` (888) | `Vector3` | UE3 FVector direction (components uu) | — | — | the **aim / movement direction**, held apart from body rotation | decoded type+offset | `BMSDK_OFFSETS.json:24554-24558` |
| `BattleModeSteerAngleFactor` | `RVehicleSimBatmobile` | `0x300` (768) | float | factor | 2.5 | **1** | scales front steer angle toward the direction | decoded | `MODES.md:100` |
| `BattleModeMaxSteering` | `RVehicleSimBatmobile` | `0x2cc` (716) | float | deg | 80 | — (no tag) | steer clamp; the shipped car runs the class default | decoded value / derived unit | `MODES.md:87`, `chase-06:33` |
| `BattleModeTrailingSteerFactorMoving` | `RVehicleSimBatmobile` | `0x320` (800) | float | factor | −0.5 | **−0.25** | rear-axle steer while moving, **opposite** sign to the front → extra yaw about the front axle | decoded | `MODES.md:102` |
| `BattleModeStopAndTurnAngleMoving` | `RVehicleSimBatmobile` | `0x2fc` (764) | float | deg | **90** | — (no tag) | the aim error at which a moving car is allowed to stop and turn | decoded value / derived unit | `MODES.md:99`, `chase-06:39` |
| `BattleModeStopAndTurnAngleStationary` | `RVehicleSimBatmobile` | `0x2f8` (760) | float | deg | 60 | **30** | same gate at rest (settled elsewhere, listed for contrast) | decoded | `MODES.md:98` |
| `BattleModeMoving` | `RVehicleSimBatmobile` | `0x294` (660) | bool | bool | — | — (no tag) | the state bit that selects the moving rule set | decoded | `MODES.md:85` |
| `BattleModeYawOffset` | `RVehicleBatmobileBase` | `0x1910` (6416) | int | UE3 rotator int (65536 = 360°) | **16384 = 90°** | **0** | constant offset between body facing and the aim direction; **0 shipped** | decoded | `MODES.md:151`, `DRIVE_MODES.md:83` |
| `BattleModeSteerBiasRate` | `RVehicleSimBatmobile` | `0x3c4` (964) | float | **undocumented** (rate-sized) | **3.0** | — (no tag) | the only rate-named member; consumer unproven | decoded value / UNKNOWN unit | `MODES.md:112`, `chase2-07:18` |
| `BattleModeThrottleSpeed` | `RVehicleSimBatmobile` | `0x2ec` (748) | float | undocumented (rate-sized) | 5 | **10** | second rate-sized candidate | decoded value / UNKNOWN unit | `MODES.md:95`, `chase2-09:20` |
| `SVehicleWheel.BattleModeSteerBias` | `SVehicleWheel` | `0x320` (800) | float | undocumented | — | — (runtime) | **per-wheel** steer bias; the wheel-level half of the same 0x320 | decoded declaration / no value | `BMSDK_OFFSETS.json:27648-27652` |

Two decoded facts that decide the reading:

1. **`YawOffset` ships 0, not 90°.** `MODES.md:151` records `0 | 0 | 0 | 0` for V2/MK2/Joker/Funhouse;
   `16384` is the class default on `RVehicleBatmobileBase` (`DRIVE_MODES.md:83`), which is why
   `G3-02l.md:46` and `DRIVE_MODES.md:119` describe a 90° offset. **Derived:** with the shipped value
   at 0 the body faces the aim direction exactly; with 16384 the nose would sit 90° off it (a crab
   stance). The shipped game therefore does *not* run the crab stance, and the operator's "nose
   swings toward where the camera points" matches the shipped 0, not the class default.
2. **The rear axle's moving factor is non-zero and negative** (`−0.25`), while the turn-on-spot
   factor is `+1.0` (`MODES.md:101`, class only). **Derived:** sign-flipped rear steer adds yaw
   rather than cancelling it, which is what brings the nose round while the car keeps moving. The
   *sign convention itself* is stated in no file — UNKNOWN (U4).

Quote, `MODES.md` lines 99–102 (verbatim rows):

> | `BattleModeStopAndTurnAngleMoving` | 0x2fc | `float` | deg | — | — | — | — | no |
> | `BattleModeSteerAngleFactor` | 0x300 | `float` | factor | 1 | 1 | 1 | 1 | yes |
> | `BattleModeTrailingSteerFactorMoving` | 0x320 | `float` | factor | -0.25 | -0.25 | -0.25 | -0.25 | yes |

---

## 3. The input: stick, camera yaw, or fixed rate

Each candidate with its unit and its offset or script site.

| candidate | carrier | unit | offset / site | what the data shows | verdict |
|---|---|---|---:|---|---|
| **stick** | `PlayerInput.aBaseY`, `PlayerInput.aStrafe` | axis, magnitude undocumented | no class offset — controller fields, read in `CheckBattleStrafe` / `PursuitStrafe` only (`DRIVE_MODES.md:104`, ref lists at `:402`/`:375`) | The battle tick contains **no** stick read (`DRIVE_MODES.md:109`). The only script bodies that read `aBaseY`/`aStrafe` are the strafe/dodge bodies, and they build a strafe vector, not a drive heading. | **not the heading input.** With the stick at rest the behaviour still occurs (operator), which the tick's own silence explains: no script reads it. |
| **camera yaw** | `AbsoluteMoveDirection` (the aim direction) + `BattleModeYawOffset` | `Vector3` (direction) / rotator int (65536 = 360°) | `0x378` (888) / `0x1910` (6416) | The sim holds a world-space direction **separately from body rotation** and yaws the body onto it; the shipped offset between body and that direction is 0. A camera-referenced stick resolution upstream means "stick centred" = "camera forward", so the body chases the camera. | **supported as the reference** — but the camera itself is not a decoded member anywhere (U1). |
| **fixed rate** | `BattleModeSteerBiasRate` 3.0; second candidate `BattleModeThrottleSpeed` 10 | undocumented / undocumented | `0x3c4` (964) / `0x2ec` (748) | `SteerBiasRate` has **0 read sites** in the executable and only constructor stores (`chase2-09:21`, `:90`); `ThrottleSpeed`'s single read is a cross-object comparison with no scale (`chase2-09:20`, F-71). Neither is shown to drive anything. | **not supported.** A constant-rate turn would also be speed-independent, which contradicts the 90° angle gate and the factor-based steer fields. |

### 3.1 The contradiction to record, not smooth over

The two chase passes disagree on whether `BattleModeSteerBiasRate` is consumed:

* `chase2-07.md:18` — "F-55 … `BattleModeSteerBiasRate` | FOUND (confirmed) | **3.0**, unit **UNKNOWN** (U-2, F-72)"; and its U-2 section says "134 instructions reference 0x3c4, all unattributable".
* `chase2-09.md:21` — "value 3.0 unchanged; **0 read sites** of `[reg+0x3c4]` and only constructor stores; nothing consumes it statically".
* `chase2-09.md:90` — "**F-72 (0x3c4) — 0 read sites.**"

Both passes agree on the only thing this report uses: **nothing attributable consumes it**. The
disagreement is in the counting method (displacement substrings vs decoded read operands), and it is
recorded here rather than resolved, because neither pass found an attributable consumer. Consequence:
"fixed rate" cannot be claimed as the mechanism on the strength of this member's name.

### 3.2 Why the answer is a direction and not a rate — the arithmetic that is and is not there

* **Decoded:** a direction field (`Vector3`), a steer-angle multiplier (1), a steer clamp (80°), a
  non-zero rear counter-steer while moving (−0.25), a 90° stop-and-turn gate, a 0° body-to-aim offset.
* **Derived:** a proportional steer toward a direction with a clamp and a threshold is a *servo*, not
  a constant rate; its rate emerges from steer geometry and speed, so no single number describes it.
* **UNKNOWN:** the expression that combines them — the body of `RVehicleSimBatmobile.SetDriveMode`
  is the native call site, 5 script bytes (`G3-02l.md` UNKNOWN 1). This is the one place the missing
  facts live; §6 names the file that would carry it.

---

## 4. Moving mode: does it keep or drop the stationary pivot

The stationary pivot is settled elsewhere (`tmp/freebuff/reports/tank-pivot-values-for-battle-mode-turn-plan.md`,
answer line 11: the tanks do not carry it, the split "can only be approximated by per-axle grip
asymmetry plus the drift yaw-torque block"). It is **not** re-derived here.

**Moving mode keeps the pivot, at reduced authority, and re-enters the full pivot when the aim error
reaches 90°.** Evidence, all decoded:

| fact | value | source |
|---|---|---|
| the pivot state and the moving state are separate rule sets, switched by a bool | `BattleModeMoving` `0x294` | `MODES.md:85` |
| rear steer while moving | `BattleModeTrailingSteerFactorMoving` **−0.25** (never zero) | `MODES.md:102` |
| rear steer in the pivot state | `BattleModeTrailingSteerFactorTurnOnSpot` **1.0** (class only, no tag) | `MODES.md:101` |
| the pivot torque still runs in battle mode | `BattleModeTurnOnSpotTorqueFactor` **0.333333** | `MODES.md` family table |
| the moving car is allowed to stop and turn | `BattleModeStopAndTurnAngleMoving` **90°** (class only) | `MODES.md:99` |
| the stationary car's gate, for contrast | `BattleModeStopAndTurnAngleStationary` **30°** shipped | `MODES.md:98` |

**Derived:** nothing in the moving set zeroes the pivot's torque factor or its trailing steer; the
differences are magnitude (1.0 → −0.25) and threshold (30° → 90°). Moving mode therefore *keeps* a
quarter-strength counter-steering rear axle and escalates to the stationary pivot at ≥ 90° of aim
error. **UNKNOWN (U4):** what the sign difference means physically — no file states whether +1.0
turns the rear wheels with or against the front.

---

## 5. The closest JC3 mechanism for the operator fact

The operator fact needs two things: a camera-referenced aim direction, and a yaw servo that chases it
while the car drives. JC3's data has neither as such (`G3-08c.md:46`: 6 camera-relative members, all
`Propellers`, **0** in a driving module). The closest decoded pieces, in order:

| piece | member(s) | file | distance from the requirement |
|---|---|---|---|
| steering geometry that already reduces lock with speed | `LandSteering.steer_angle_min_speed_deg` / `steer_angle_max_speed_deg` / `min_speed_kmph` / `max_speed_kmph`, `countersteer_speed_factor` | `TANKTURN.md` §2 (tank chassis, 252 builds) | a steer-vs-speed map exists, but its reference is the steering input, not an aim direction — no camera term |
| yaw torque that is not slip-gated by name | `CustomLandGlobal.drift.constant_drift_torque`, `max_drift_torque`, `steering_sensitivity` | `DRIVE_CARRIERS.md` §3.1 | can rotate the body, but is driven by stick/slip, not by an aim vector |
| per-axle steer asymmetry (the counter-steer analogue) | `LandSteering.front_wheels` / `rear_wheels`; per-axle `arcade_friction_multiplier` | `G3-08c.md` §1–2 | only grip asymmetry ships; `steering_type` is `FrontSteered` on 51/51 readable modules, so no rear-steer value exists |
| camera-yaw graph force | `.epe` sequence applying a force in camera yaw when the stick is off-centre | `four-wheel-drive-…build-plan.md:183-185` | the only *data* shape that expresses "camera yaw"; needs a trigger and a graph per entity |

**Verdict (derived from the four):** the reproduction is a **camera-referenced yaw target plus a
steer servo**, and JC3 exposes no member for either half. The honest build is: `steer_angle_*` +
`countersteer_speed_factor` for the servo shape, `drift.constant_drift_torque` /
`steering_sensitivity` for yaw authority, and the camera-yaw graph route for the reference — with the
`bForceBattleModeMovement`/`AbsoluteMoveDirection` pair having no JC3 counterpart at all
(`DRIVE_MODES.md` §5: no script writer for `bForceBattleModeMovement` in BmAK either). Anything
closer is a code bridge, which is what `G3-08c.md:235` and the four-wheel plan already conclude.

---

## 6. UNKNOWNs — with the searches run and the settling file

| # | unknown | searches run | settling file that would carry it |
|---|---|---|---|
| U1 | **the camera→aim resolution**: no member anywhere holds a camera yaw or a camera-relative transform for the vehicle | `objects.jsonl` scan for `SimulationModel` / `BattleMode*` / `PursuitMode*` (4 archetypes, 0 functions); `Research/BatmobileGrab/*` grep for `BattleModeSteerBias`, `TrailingSteerFactorMoving`, `SteerBiasRate`, `YawOffset`, `ThrottleSpeed`; `DRIVE_MODES.json` field block | the `RPlayerController` / `PlayerInput` producer of `Core.OutputSteering` in `BmGame.upk` (the body that turns stick+camera into the steering scalar) — not decoded by `grab_drive_modes.py` |
| U2 | **the arithmetic inside `SetDriveMode`** — how direction, factor, clamp and gate combine | package scan of all four bodies; `DRIVE_MODES.md` §7 UNKNOWN 1; `G3-02l.md` UNKNOWN 1 | the native `RVehicleSimBatmobile.SetDriveMode` in `BatmanAK.exe` (script is the 5-byte stub `29 <param ref>`) |
| U3 | **whether `BattleModeSteerBiasRate` is consumed at all** | `chase2-07.md` U-2 (134 displacement hits, none attributable); `chase2-09.md:90` (0 read sites) | a runtime read of a live `RVehicleSimBatmobile` at 0x3c4, or a decompiled sim tick in `BatmanAK.exe` |
| U4 | **the sign convention** of `TrailingSteerFactorMoving` / `…TurnOnSpot` (rear with or against the front) | `MODES.md` unit column (says "factor", not direction); `BMSDK_OFFSETS.json` (no comment); chase-06 numeric rows | the native trailing-steer term in `BatmanAK.exe`; no package carries it |
| U5 | **`SVehicleWheel.BattleModeSteerBias`'s value and unit** — declared at 0x320 on the wheel class, no tag in any package | `BMSDK_OFFSETS.json:27648-27652`; `MODES.md:7` (offset collision warning); `MODES.json` field entry with no value | a live wheel object at run time, or the `SVehicleWheel` CDO tag stream in `BmGame.upk` |
| U6 | **whether the shipped 0 yaw offset is authored or inherited** | `MODES.md:151` (0 in all four); `DRIVE_MODES.md:83` (class 16384); `chase-09.md` F-69 (unit UNKNOWN, 0 is unit-free) | the four `SimulationModel` objects' tag streams re-read with tag names (`objects.jsonl` names only the six curves) |

No value in this report is inferred from another engine's convention. The two unit calls that are
*not* stated by a file are marked as such in §2.3 (`deg` for the two angle gates, `rotator int` for
`YawOffset`); both follow the project's own unit column (`MODES.md` "Units" table: `conv` = the
field's name under UE3 conventions), not a guess.

---

## 7. Sources, limits, revert

**Sources** (all read-only): `Research/BatmobileGrab/objects.jsonl` (lines 5368, 8769, 14313, 19804),
`Research/BatmobileGrab/MODES.md` (lines 7, 30–31, 85–112, 121, 151), `DRIVE_MODES.md` (lines 83,
104, 109, 119), `DRIVE_MODES.json` (`AbsoluteMoveDirection` refs, field block),
`BMSDK_OFFSETS.json` (24554–24558, 27648–27652), `chase/chase-06.md` (33, 39),
`chase/chase2-07.md` (18, U-2), `chase/chase2-09.md` (20, 21, 90), and the three named reports.

**Limits.**

* Desk decode only: no game launched, nothing attached, no package re-read this session. The battle
  tick, the 40-field set and the archetype values are quoted from `DRIVE_MODES.md` / `MODES.md`,
  which re-derive them with their own `--check`; `objects.jsonl` was re-scanned here and cannot
  supply scalar tag names for these archetypes (§2.1).
* The behaviour itself is the operator's statement of 2026-11-08, not a measurement. The pilot
  evidence that would confirm the servo is one drive test: forward at 30 km/h with the stick
  centred, rotate the camera 90° — the nose should follow within ~1 s while the ground path stays on
  the camera axis.

**Revert:** delete this file and its copy under `tmp/freebuff/reports/`. No other file was created,
edited or moved; `MODES.md`, both chase files and the three prior reports were not modified.
