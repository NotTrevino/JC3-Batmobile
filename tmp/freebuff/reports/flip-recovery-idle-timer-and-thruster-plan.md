# Rested on roof or side → thrusters fire and right it: the idle timer, the effect, and the JC3 carrier

**Scope.** The operator's 2026-11-08 fact — *when the Batmobile rests on its roof or side for a while,
its thrusters fire and right it* — worked back to a timer, to the effects that fire, and forward to the
closest JC3 systems. Written on top of `reports/stuck-flip-scrape.md` and
`reports/stuck-flip-build-plan-merge.md`, which both record **no roll-angle field and no speed gate** and
that **the flip does not share the strafe kick**. Those two negatives are re-tested here, not assumed.

Nothing was launched, attached to or written outside `tmp/freebuff/reports/`.

**Labels.** **decoded** = bytes/tags read at the package, export or offset cited. **derived** = a stated
rule or arithmetic over decoded values. **UNKNOWN** = absent from every file read, with the settler named.

**Headline.**

1. **The timer exists and is decoded, twice: `BatmobileStuckTimeFlip` = 0.5 and `BatmobileStuckTimeMax`
   = 2.0**, both floats on `RVehicleBatmobileBase` (`CLASS_DEFAULTS.md:287-288`). The unit is **seconds**
   by derivation only — no file annotates it.
2. **The running "rested" quantity is `BatmobileStuckTime`, and its value is UNKNOWN** — declared at
   0x1d18, never serialised, initialised in native code. So "for a while" is a **0.5 s / 2.0 s pair of
   gates around an accumulator whose runtime value no file holds**.
3. **The one place the executable is seen reading that pair is a mode-change gate**:
   `PAWNMESH_D8.md:10` decodes `0x140063e90` refusing a mode change when the car is more than 135° from
   upright, and refusing at more than 45° **unless `BatmobileStuckTimeFlip < BatmobileStuckTime`**. That is
   the "rested long enough" condition, in code, at an address — not an inference from the field names.
4. **`SideExhaust*` is confirmed as an object and rejected as the righting effect.** Both fields resolve
   to real `Exhaust.*` particles, but no flip body references them, and the flip's own effect is UNKNOWN.
5. **JC3 has no righting torque on a car** — but it does have a **thruster effect carrier**
   (`EngineTurboJump` usage, 349 objects / 164 entities, fired by `turbo_jump.*`) and an **upright
   predicate** (`CInteractionGraphParentIsUpRightCondition`, 6,761 instances). Those two are the build;
   the torque is the gap.

---

## 1. The timer hunt — every candidate, and what each is

Searched: every `Research/BatmobileGrab/*.md` and `chase/*.md` for `Righting(Delay|Time|Duration)`,
`AutoRight`, `FlipTime`, `SelfRighting(Delay|Time)`, `TimeToRight`, `StuckTime`, `idle*time`,
`stationary`, `upside`, `onroof`, `rollover`. **Result: 0 hits for any righting/flip *timer* other than the
three `BatmobileStuck*` fields below.** The "for a while" condition therefore has exactly one candidate
family, and it is the stuck accumulator.

| # | member | offset | value | kind | label |
|---|---|---:|---|---|---|
| T1 | `BatmobileStuckTime` | **0x1d18** (7448) | **no tag anywhere** — CDO and all four playable archetypes carry none | running float accumulator (the *duration*) | **decoded carrier, UNKNOWN value** |
| T2 | `BatmobileStuckTimeFlip` | **7456** | **0.5** | float on the class default object | **decoded** (`CLASS_DEFAULTS.md:288`) |
| T3 | `BatmobileStuckTimeMax` | **7452** | **2.0** | float on the class default object | **decoded** (`CLASS_DEFAULTS.md:287`) |
| T4 | `NumFlipTries` | 7460 | no tag | attempt budget | **decoded carrier, UNKNOWN value** |
| T5 | `SelfRightingMode` | 5900 | **0** shipped (no tag → class default) | byte enum | **decoded carrier, meaning UNKNOWN** (no `ESelfRightingMode` name table) |

### 1.1 The unit

No file annotates the unit. **Seconds is derived**, on three independent supports:

- both fields are `FloatProperty` in a class whose every other `*Time*`/`*Duration*` member is a duration
  (`KillFlipTorqueDuration` 1.5, `KillKeepyUpFactorDuration` 0.75, `PMDodgeDuration` 0.15);
- the pair reads as a threshold ladder only in seconds (0.5 s to treat the car as stuck, 2.0 s to give
  up) — as cm/s or as frames the two numbers are meaningless against a 500–4000 HP, 6 t car;
- the one decoded *consumer* compares them against each other (`PAWNMESH_D8.md:61-62`:
  `movss [rbx+0x1d20]` then `comiss [rbx+0x1d18]`), so T2 and T3 are in the same unit as T1 and the
  comparison is unit-free — the seconds reading is for the *rate*, not for the comparison.

**Marked derived, not decoded.** The settler is §6 U1 below.

### 1.2 The consumer that is actually decoded

`PAWNMESH_D8.md:10` and `:61-62`, at `0x140063e90` (the mode-change test, `±0.707` constants
`0x141bf1cdc` / `0x141bce8f8`):

> a mode change is refused when the car is more than **135°** from upright, and refused when it is more
> than **45°** from upright **unless the flip timer has run out** (`BatmobileStuckTimeFlip <
> BatmobileStuckTime`).

Read against the operator's description, this is the *shape*: a **>45° out-of-upright posture** plus **a
timer that has run out**. It is not proof that `TryRightingFlip` reads the same pair — that function is
native (11 script bytes, no call out, `stuck-flip-scrape.md` §1.1) — but it is the only decoded code that
uses an out-of-upright angle and a "rested long enough" timer together.

### 1.3 The two negatives, re-tested

| claim | re-test | result |
|---|---|---|
| no **roll-angle** field gates the flip | 0 hits for any `*Roll*Angle*`/`RightingAngle`/`MaxTilt` on the vehicle; `ImpactRoadAssistMaxAngle` is a road-assist angle, `BattleModeStopAndTurnAngle*` is a turn angle | **confirmed absent** |
| no **speed** gate | 0 hits for a speed member near the flip; `SpeedLinesSystem` is an effect, `PMDodgeForce` is strafe | **confirmed absent** |
| the flip does **not** share the strafe kick | `TryRightingFlip` (10572) and `FlipVehicle` (10596) reference no `KickStrafe` / `VehicleStrafe` / `SideExhaust*`; field sets disjoint | **confirmed** — the flip is `AddTorqueOverTime` + `AddKeepyUpForce` (literals 1000.0 / 2.0, derived from the body) |

So the gate the operator experiences is **posture (≥45°) × time (0.5 s), not angle × speed**.

### 1.4 The upright-torque members — a record conflict to report, not resolve

| member | offset | MODES.md | chase-07 / chase2-07 |
|---|---:|---|---|
| `BattleModeUprightTorqueFactor` | 0x370 | **not serialised** in any of the four archetypes or their defaults (`MODES.md:105`, `:121`; `FOOTAGE.md` F-50 = UNKNOWN, `VALUE-NATIVE`) | **SERIALISED 2000.0** (`chase-07.md:74`, `chase2-07.md:13`) |
| `BattleModeUprightMaxTorque` | 0x374 | not serialised (`MODES.md:106`) | **SERIALISED 2000.0** (`chase-07.md:75`) |

Two records in the same repository disagree, so **the value is reported as disputed**: 2000.0 appears in
the chase records, absence appears in the archetype walk. The build must not quote 2000 as a fact. Both
members exist and are the closest named carriers of "upright torque" on the class
(`BMSDK_OFFSETS.json:24541, 24548`), alongside `UprightCarWhenOn2Wheels` (`:25111`) and
`InAirUprightTorqueFactor` (`:25255`), whose values are **UNKNOWN** (no serialised tag found).

The stay-upright path is a **constraint**, not a number: `SVehicle.StayUprightConstraintSetup` →
`Batmobile.RB_StayUprightSetup` (export 5106) and `…ConstraintInstance` → `RB_ConstraintInstance`
(archetype offsets 1764 / 1772, `COLLISION_WHERE.md:49-50`). The setup object is **2 bytes with 0 tags**
(`COLLISION_WHERE.md:130`), so **no per-vehicle upright tuning is serialised there** — the stiffness and
the resist angles are native (`chase2-08.md` §4, `chase2-09.md` F-65/F-66).

---

## 2. The effect hunt — `SideExhaust*` and `KickStrafe`, confirmed or rejected

### 2.1 `SideExhaustBurstEffect` / `SideExhaustBoostEffect` — **confirmed as objects, rejected as the righting effect**

| field | archetype offset | CDO row | archetype resolution |
|---|---:|---|---|
| `SideExhaustBurstEffect` | 0x006c (4692) | `Exhaust.Batmobile_Side_Exhaust` (`CLASS_DEFAULTS.md:192`) | **`Exhaust.SideExhaust_Burst`** (`COLLISION_WHERE.md:62`) |
| `SideExhaustBoostEffect` | 0x0074 (4700) | `Exhaust.Batmobile_Side_Exhaust` (`CLASS_DEFAULTS.md:193`) | **`Exhaust.SideExhaust_Boost`** (`COLLISION_WHERE.md:63`) |

Three findings, in order of confidence:

1. **The fields are real and point at real `ParticleSystem` objects** — decoded twice, at the CDO and at
   the archetype. *Confirmed.*
2. **The two records name different objects** — one shared `Batmobile_Side_Exhaust` at the CDO, two
   distinct `SideExhaust_Burst` / `_Boost` at the archetype. Which one the shipped car plays is
   **UNKNOWN**; the archetype is the layer that runs, so `_Burst` / `_Boost` is the working assumption and
   the CDO row is a template reference (`stuck-flip-scrape.md` §2.3 reached the same pair).
3. **No decoded link from a flip body to either field.** `TryRightingFlip` (10572, 11 bytes) and
   `FlipVehicle` (10596) contain no reference to them; the flip's effect is UNKNOWN. *Rejected as the
   righting effect.*

What that leaves: the side exhaust is the **strafe/dodge** plume (`stuck-flip-scrape.md` §2.3-§2.6). The
operator sees **thrusters** when the car rights itself, and these are the only lateral-thruster particles
on the class — so they stay on the candidate list for *appearance*, with the link unproven (§6 U3).

### 2.2 `KickStrafe(Force, Torque, Duration)` — **rejected as the flip mechanism**

`RVehicleBatmobileBase.KickStrafe` export **10143**, 53 script bytes, **3 param descriptors and no
constant** → native (`stuck-flip-scrape.md` §2.2). It is the only member on the class that takes a
**force + torque + duration** triple, which makes it the natural suspect for "thrusters fire and the car
turns over". It is rejected for three reasons:

- no call site from `TryRightingFlip` / `FlipVehicle` to it;
- its callers are the strafe chain (`BattleStrafe` → `CheckBattleStrafe` → `BattleMode.BattleDodge` →
  `VehicleStrafe` → `KickStrafe`), and that chain is reachable from **A**, not from the rest state;
- the field sets are disjoint: the flip reads `Jump*RightingTorque` / `SelfRightingMode` / `KillFlip*`;
  the strafe reads `Strafe*` / `PMDodge*` / `BattleDodgeImpulse`.

**A shared native kick is not excluded** — both are native — but nothing in the corpus links them, and the
merge plan already reached the same conclusion. Marked *rejected at the script level, UNKNOWN at the
native level* (§6 U4).

### 2.3 What actually pushes the car over

`FlipVehicle(bool bInstant)` (export 10596, 122 script bytes) contains **`AddTorqueOverTime` +
`AddKeepyUpForce`** with literals **1000.0** and **2.0** (`stuck-flip-scrape.md` §2.6, derived from the
body's call/const layout). So the righting is **a torque over a duration plus a lift**, not a discrete
kick and not a radial blast. That single sentence is what the JC3 mapping below has to reproduce.

---

## 3. JC3 — the closest systems, member by member

### 3.1 An idle-triggered righting force: **no member; the gate and the reset exist**

| candidate the task names | what JC3 actually has | verdict |
|---|---|---|
| **`FlipVehicle`** | no such member or class in 232 vehicle graphs; the only flip-ish thing is BmAK's own export 10596 | **no carrier** |
| **`AddTorqueOverTime`** | no torque-over-time member on a `CCar`. The torque-shaped members are `DriverLean.righting_torque` **1500 … 4000 (med 3000, n=23)** and `leaning_torque` 2000…8000 (med 5000) — on **18 bikes + 5 boats, 0 cars** (`card-T-10.md` A4; `VOCABULARY.md:566`) | **carrier on the wrong population** |
| **`CForcePulse`** | radial impulse, **explosion-fired only** (0 of 23 tune paths name a collision or a horn); `gen_explosion_5m_nodamage.ftune` = **0 damage / 5 m**, "push only" | **pop, not roll** — it cannot turn a car about its roll axis |

What does exist, and is the real build surface:

| JC3 carrier | value | what it gives |
|---|---|---|
| **`CInteractionGraphParentIsUpRightCondition`** | **6,761** instances (`ENTITIES.md:11`); used as check 1 on every exit of the donor's 26 exits (`EJECT.md:57-64`) | a first-class **"is the parent upside-down"** predicate, shipped, already in the `.epe` interaction graph — the trigger |
| **`motorbike_common.roll_to_fall_with_driver_deg` / `_no_driver_deg`** | **80 / 50** (n=232, `card-T-10.md` A4) | the fall angle on *every* vehicle module — a threshold to borrow, not a torque |
| **`arcade.turbo_jump.*`** | `punch_speed_kph` **50…60 (med 50)**, `punch_delay_time` **0…0.1**, `up_multiplier` **12…25** (upgraded 25…50), n=35 (`VOCABULARY.md:357-358`; merge §3.2) | a **real member on land vehicles** that punches along a fixed axis — a lift, not a roll |
| **`CHALLENGE_RESET_VEHICLE`** | LPADDOWN / **P** (`INPUT.md:61`) | the reset fallback; its runtime effect is UNKNOWN (probe) |

**The gap, stated plainly:** JC3 has the *trigger* and the *lift*, and no *roll torque*. The build's own
arithmetic from the merge plan still stands and is what a hook must supply — **T = 230,300 N·m for 0.5 s**
(180° in 0.5 s, I_roll 9,165 kg·m², α = 25.13 rad/s²), or one impulse **J = 57,600 N·m·s** (ω = 6.283
rad/s), damped at **0.985** of world up (10°) — *derived, not ported*.

### 3.2 The thruster effect: **this one has a carrier**

JC3 attaches effects by **usage name** on `SAttachedEffect` / `SDynamicAttachedEffect`. The thruster family
is fully populated (`USAGES.md`):

| usage | hash | objects | entities | example effect names |
|---|---:|---:|---:|---|
| **`EngineTurboJump`** | 3877802965 | **349** | **164** | `exhaust_upgrade_tjump` (154), `exhaust_upgrade_tjump_trail` (113), `turbo_jump_sound` (35), `exhaust_upgrade_tjump2` (17) |
| `dynamic_tjump` | 3850682818 | 14 | 14 | `dynamic_exhaust_upgrade_tjump` |
| `EngineNitro` | 4197885156 | 18 | 18 | `dynamic_nitrous` (14), `EngineNitro` (4) |
| `dynamic_exhaust` | 94496804 | 49 | 49 | `dynamic_exhaust` |
| `EngineRunning` | 2819629913 | 69 | 69 | `dynamic_exhaust` (46), `EngineNitro` (20) |
| `flame` (unnamed) | 456657646 | 121 | 121 | `flame` |

`EngineTurboJump` is the closest thing in JC3 to "thrusters fire": a shipped, **164-entity** usage whose
purposes are a jump plume, a trail and a sound. The build reuses it on the rear/thruster part and fires it
from the same graph node that runs the recovery — **no new asset**. `turbo_jump.up_multiplier` 12…25 is the
member that makes the plume *do* something, and it is on land vehicles (n=35) with an **UNDECODED
consumer** (`VOCABULARY.md:361`), so the lift is a probe, not a promise.

### 3.3 Values to write

| # | file | member | write | label |
|---|---|---|---:|---|
| FR-1 | `.epe` interaction graph | `CInteractionGraphParentIsUpRightCondition` on the recovery node | gate at **0.707** (45° off upright, BmAK's decoded constant) | decoded gate |
| FR-2 | graph timers | rest delay before the recovery fires | **0.5 s** (T2) then give up at **2.0 s** (T3) | decoded values, derived use |
| FR-3 | `turbo_jump` tune | `punch_speed_kph` / `punch_delay_time` / `up_multiplier` | **50 / 0.0 / 12** (fleet medians) | decoded |
| FR-4 | thruster part | effect usage **`EngineTurboJump`** | reuse | decoded usage, 164 entities |
| FR-5 | char module (probe) | `DriverLean.righting_torque` | **3000** | decoded on bikes/boats, 0 cars — **probe only** |
| FR-6 | fallback | `CHALLENGE_RESET_VEHICLE` after 2.0 s | **P / LPADDOWN** | decoded action, UNKNOWN consumer |
| FR-7 | hook (only if FR-5 fails) | roll torque about the long axis | **230,300 N·m for 0.5 s**, damp at **0.985** | derived |

---

## 4. Pilot card

**One sentence, read aloud by a tester:**

> "Put the car on its roof, let go of everything and wait: **nothing may fire before 0.5 s of rest**, the
> thrusters must fire and the car must be **wheels-down by 2.0 s**, and it must settle with its up axis
> **within 10° of vertical** (≥ 0.985 of world up) and **0 rad/s residual roll** — landing between 45° and
> 10° is a failed recovery, not a partial one."

Pass bands: **0.5 s / 2.0 s decoded** (T2, T3), **0.985 / 10° derived** (the smallest angle at which the
45° line stops being a false pass). The same card on the **side** case must end wheels-down without
rolling past vertical onto the other flank.

---

## 5. Order of work

1. **Probe `CHALLENGE_RESET_VEHICLE`** on a flipped car (one press, free roam): rights in place, or
   respawns? Decides whether the feature is a rebind or a hook.
2. **Probe the `DriverLean` block** on the Batmobile's land module set (`righting_torque` 3000): loader
   accepts → righting as data; refuses → FR-7 is the only route.
3. **Then** the graph node (FR-1/FR-2) + the `EngineTurboJump` plume (FR-3/FR-4). The effect ships
   independently of the physics and cannot be wrong in the same way.
4. Audio and camera stay out of this plan: BmAK's flip cue (`Play_Batmobile_Rotation`) is not importable
   into a FEV bank, and JC3's camera clamps vehicle roll to ±20° (`CAMERA.md` §4).

---

## 6. UNKNOWN register

| # | unknown | settling file or probe |
|---|---|---|
| U1 | the unit of `BatmobileStuckTimeFlip` / `Max` (seconds is **derived**) | the `.g.cs` doc for 7452/7456 carries no unit; a live read of the accumulator's rate |
| U2 | the runtime value/growth of `BatmobileStuckTime` (0x1d18) and `NumFlipTries` (7460) | native constructor in IDA, or a live property dump of a spawned car |
| U3 | which `Exhaust.*` object the shipped car plays for `SideExhaustBurst/BoostEffect` (CDO vs archetype conflict) | `Playable_Batmobile_SF.upk` 4969-4971 re-read against the archetype's own property block |
| U4 | whether the righting shares a native kick with the strafe (`KickStrafe`) | hook 10572 / 10596 and watch for a `KickStrafe` call or a `SideExhaust_*` spawn |
| U5 | what fires the thrusters in BmAK (which effect, which bone) | runtime VFX log at a flip; the class's effect set names none for a flip |
| U6 | `BattleModeUprightTorqueFactor` / `MaxTorque` = 2000 or unset (record conflict, §1.4) | re-walk the four archetypes' `RVehicleSimBatmobile` serialisation at 0x370/0x374 |
| U7 | whether a `CCar` accepts `DriverLean` (FR-5) | one build + the module loader |
| U8 | `turbo_jump.up_multiplier`'s consumer on a land car | `VOCABULARY.md:361` consumer undecoded; a build with the member set and a take |
| U9 | `SelfRightingMode` = 0 meaning | `BmGame.upk` bytecode at 5900, or a live read of `+0x170C` |

---

## 7. Change record

- **Intended change:** none to game data. This document names the timer, the effect verdicts and the JC3
  carriers only.
- **File written:** `tmp/freebuff/reports/flip-recovery-idle-timer-and-thruster-plan.md`.
- **Why this file:** the request names it as the deliverable.
- **Revert:** delete the file. No other file was touched.

## 8. Checks run

| # | check | result |
|---|---|---|
| 1 | `stuck-flip-scrape.md` §1.3-§1.5, §2.2-§2.6 and `stuck-flip-build-plan-merge.md` §1-§4 re-read | the two negatives (no roll gate, no speed gate) and the "no shared strafe kick" finding re-used, not re-derived |
| 2 | `CLASS_DEFAULTS.md:287-288` | `BatmobileStuckTimeMax` **2.0**, `BatmobileStuckTimeFlip` **0.5**, both floats |
| 3 | `PAWNMESH_D8.md:10`, `:61-62` | the ±0.707 gate at `0x140063e90` and its `0x1d20` vs `0x1d18` comparison |
| 4 | `MODES.md:105-106, 121` vs `chase-07.md:74-75` / `chase2-07.md:13-14` | **conflict recorded** (unset vs 2000.0), not silently resolved |
| 5 | `CLASS_DEFAULTS.md:192-193` vs `COLLISION_WHERE.md:62-63` | **conflict recorded** on the `SideExhaust` object name (CDO vs archetype) |
| 6 | negative greps for `Righting(Delay|Time|Duration)`, `AutoRight`, `FlipTime`, `SelfRighting*`, `*Roll*Angle*` | **0 hits** — the timer family is `BatmobileStuck*` only, and there is no roll-angle field |
| 7 | `USAGES.md` exhaust/thruster rows | `EngineTurboJump` 349/164; `dynamic_tjump` 14; `EngineNitro` 18; `dynamic_exhaust` 49 |
| 8 | `VOCABULARY.md:357-358`, `card-T-10.md` A4 | `turbo_jump` 50 kph / 0..0.1 s; `DriverLean.righting_torque` 1500..4000 on 23 bikes/boats, 0 cars |
| 9 | `COLLISION_WHERE.md:49-50, 130` | `RB_StayUprightSetup` 2 bytes, 0 tags — no serialised upright tuning |

No game process was started, attached to or injected into; static read only.
