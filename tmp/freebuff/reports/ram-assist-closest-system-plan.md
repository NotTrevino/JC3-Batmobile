# Ram damage and road assist — the closest system, and the build that closes it

**Rows:** T-DM7 (`ImpactMinDamageSpeed` 20 / `ImpactMaxDamageSpeed` 150 / `ImpactStrafeMod` 2.25 /
`ImpactBoostMod` 2.0, all **outgoing**) and T-RA1 (`ImpactRoadAssist*`, `PMDodge*`,
`BattleDodgeImpulse`, `VehicleShovingTorque`, `KillFlip*`). Both are `out`
(`Working/Translation/T_ROWS.jsonl:95,103`). `tmp/freebuff/reports/carrier-ram-and-dodge.md` found
the one outgoing channel and named the missing capability; this note composes the build, per the
project rule that a gap is closed by the build.

**New in this note — three things the carrier report left open:**

1. **The rotor block's offset is no longer UNKNOWN.** It is a standalone file,
   `Builds/bm-RC2/aaf/editor/entities/jc_vehicles/00_shared/modules/vehicle_common.vmodc` (12,271 B,
   type `VehicleCommon`, instance at **0x50**, size 5,012): `rotor_collision` at **0x130**,
   `damage_to_other_per_second` a float at **0x138**, `min_rpm` 0x130, `mass_ratio_when_no_mass`
   0x134, `light_object_mass_ratio` 0x13C. Verified by reading the floats back (§2).
2. **The block loads on a car; the gate's input is the open question, and it has a decisive
   experiment.** Static evidence says the module is in every vehicle's set (n=232, donor car =
   100000); the gate is named against rotor RPM and a car has no rotating part. §3 turns that into a
   two-build probe instead of a maybe.
3. **T-RA1's road-assist torque and angle are already carried, exactly.** `counter_steer_torque_brake`
   15000 = the class-default `ImpactRoadAssistMaxTorque` 15000, `counter_steer_torque_handbrake` 30000
   = the archetype 30000, and `max_drift_angle_deg` 45 = `ImpactRoadAssistMaxAngle` 45. The gap is the
   trigger and the duration, not the numbers. §5.

Nothing was written to a build. Revert = delete this file.

Labels: **decoded** = a member/value/offset read from the named file; **derived** = arithmetic over
decoded inputs; **switch** = a declared out-of-domain value; **speculative** = a probe, not a carry;
**UNKNOWN** = searched and absent, with the file that would settle it.

---

## 0. Answer

**T-DM7** cannot be carried as a speed band by JC3's channel, because the channel is a *rate per
second of contact* and BmAK's rule is a *per-impact curve*. What the build can do is put a value in
the rate so that one mid-band contact does the damage BmAK's mid-band impact does, and use `min_rpm`
as the speed gate: `min_rpm` = **1260** is the engine RPM at **20 km/h** in first gear, derived from
the car's own gearing (§2.3). Because the gate's input may instead be rotor RPM (0 on a car), the
build ships in **two stages**: A with `min_rpm` 0 proves the channel fires at all; B with 1260 tests
the threshold. The speed *ramp* and the strafe/boost multipliers have no member and stay named gaps.

**T-RA1** composes into the three mechanisms the report lists, one per function, each with the
compromise stated: road assist → the drift counter-steer torque (values already exact); dodge → the
boost push force plus the turbo-jump impulse; shove and kill-flip → a `CForcePulse` impulse (no
collision trigger, unit UNKNOWN, **speculative**). `KillFlipTorque` −2,000,000 cannot go into any
torque member (the drift torque ceiling is 35000, 57× short) and goes into a pulse impulse with its
unit declared unknown.

---

## 1. BmAK side, both value sets (the conflict that stays open)

| member | CLASS_DEFAULTS (CDO) | archetype (`DAMAGE_RULES.md`) | used by this plan |
|---|---:|---:|---|
| `ImpactMinDamageSpeed` | 60.0 | **20** | 20 (archetype; the ledger's cell) |
| `ImpactMaxDamageSpeed` | 200.0 | **150** | 150 |
| `ImpactStrafeMod` | 1.5 | **2.25** | 2.25 (no member — §2.4) |
| `ImpactBoostMod` | 1.5 | **2.0** | 2.0 (no member) |
| `ImpactRoadAssistFactor` | 40000 | 90000 | not carried (unit UNKNOWN) |
| `ImpactRoadAssistMaxTorque` | **15000** | **30000** | **already present**, §5.1 |
| `ImpactRoadAssistAngleStrength` | 1500 | 2000 | no bridge |
| `ImpactRoadAssistMaxAngle` | 45.0 | — | **already present** (45) |
| `ImpactRoadAssistSceneryDuration` / `EnemyDuration` | 0.75 s / 1.5 s | — | no member |
| `ImpactRoadAssistAngVelocityTime` / `LookAheadTime` | 0.25 s / 1.0 s | — | no member |
| `ImpactRoadAssistSteeringFactor` | 30.0 | — | no member (sensitivity is 4; 30 is out of domain) |
| `PMDodgeTorque` / `PMDodgeForce` / `PMDodgeDuration` | 5000 / 6000 / 0.25 s | — | force only, §5.2 |
| `bAllowPMDodge` | True | — | no switch |
| `BattleDodgeImpulse` | 100000 | — | no member (pulse is an explosion) |
| `VehicleShovingTorque` | 20000 | **10000** | pulse probe only |
| `KillFlipTorque` / `KillFlipTorqueDuration` | **−2000000** / 1.5 s | — | pulse probe only |
| `ImpactMaxDamage` / `ImpactMinDamage` / `ImpactMaxDamagePow` | **no value** | — | **the missing absolute** |

The last row is the reason the rate below is a *reference-case* choice and not a 1:1 carry: BmAK's
damage magnitude has no shipped number, so there is nothing to match it to.

---

## 2. T-DM7 — the channel, measured

### 2.1 The file and the offsets (new)

`Builds/bm-RC2/aaf/editor/entities/jc_vehicles/00_shared/modules/vehicle_common.vmodc` —
12,271 B, one instance `vehicle_common.vmod` of type `VehicleCommon` at 0x50, size 5,012. Type
`RotorCollision` (hash `0xed54d0d9`, size 16, 4 float members), instance-relative 224:

| member | offset | value read back | role |
|---|---:|---:|---|
| `min_rpm` | **0x130** | 30.0 | gate: below this RPM the block deals nothing |
| `mass_ratio_when_no_mass` | **0x134** | 0.1 | scale when the other object has no mass |
| `damage_to_other_per_second` | **0x138** | **100000.0** | the outgoing rate |
| `light_object_mass_ratio` | **0x13C** | 0.02 | scale against a light object |

Read with `jc3adf.py dump` and verified by `struct.unpack_from("<f")` at each absolute offset
(§8). This is the shared module every vehicle uses, so the write needs a **private copy (R7)**:
copy the file to the Batmobile's own modules directory, repoint the entity's module entry and add
the file to `@files.xml`. The shared original at `00_shared/modules/` is never edited.

### 2.2 Is the block evaluated on a car? — what is proven, and the experiment

**Proven (decoded):** the module is in the module set of **all 232** vehicles including the donor car,
with the same 100000. So on a car the block is *loaded*; there is no per-vehicle override and no
car-specific gate in the asset.

**Not proven:** whether the engine's consumer reads `damage_to_other_per_second` for a `CCar` that has
no rotor, and what `min_rpm` is compared against. The name says rotor, and the sibling evidence is the
rotating-part table in the same file (`all_rotating_part_properties[].rpm_variable` =
`main_rotor_rpm` / `tail_rotor_rpm` / `rotor_rpm`); a car ships **no `vehicle_parts` module at all**
(its private set is brakes, custom_land_global, land_aerodynamics, land_audio, land_engine,
land_global, land_steering, palette, rigid_body, suspension, transmission, vehicle_misc), so it has no
rotating part and any rotor-RPM read is 0.

That gives two mutually exclusive hypotheses with opposite settings:

| | gate input | `min_rpm` 0 | `min_rpm` 1260 |
|---|---|---|---|
| **H1** | engine RPM | fires always | fires above ~20 km/h |
| **H2** | rotor RPM (0 on a car) | **fires always** (0 ≥ 0) | **never fires** |

Both hypotheses agree that `min_rpm` **0** makes the block fire on any contact *if* the consumer runs.
So stage A ships `min_rpm` 0: a positive result proves the channel; a negative result (no damage at
any speed) proves the consumer does not run for a car, and that is the one fact no static file can
supply. Stage B then writes 1260 and distinguishes H1 from H2 by speed: H1 damages at 80 km/h, H2 does
not.

### 2.3 The gate value: 20 km/h in engine RPM (derived)

Inputs, all decoded from the car's own modules:

| input | value | file |
|---|---:|---|
| rear wheel radius | 0.68265 m (front 0.68275) | `land_global` |
| `final_drive` | 5.1401253 | `transmission` |
| `gear_ratios[0]` (1st) | 3.15 | `transmission` |
| `min_rpm` / `optimal_rpm` / `max_rpm` (engine) | 800 / 2800 / 4500 | `land_engine` |

```
circumference      = 2π × 0.68265            = 4.28922 m
20 km/h            = 5.55556 m/s
wheel rev/s        = 5.55556 / 4.28922       = 1.295222
wheel rpm          = 77.7133
engine rpm (1st)   = 77.7133 × 5.1401253 × 3.15 = 1257.84  →  1260 (rounded up, gate just above)
```

The same arithmetic in 2nd (1.94) is **774.7 rpm**, below the engine's 800 rpm floor, so at 20 km/h the
car is necessarily in 1st and 1258 rpm is the only rpm it can be turning. That is why the gate value is
defensible rather than a guess. At the band's top, 150 km/h in 6th (0.94) is **2815.6 rpm** (5th: 3445),
i.e. just above the engine's 2800 optimal — the band's top and the engine's optimal speed coincide,
which is a second, independent check that 20…150 is a real driving band for this gearing.

**No upper gate exists**: there is no `max_rpm` member in the block, so BmAK's 150 km/h cut-off cannot
be expressed. **Gap.**

### 2.4 The rate value (derived) and why the band inverts

BmAK's `ImpactMaxDamage` / `ImpactMinDamage` carry **no shipped value**, so the rate is set to a stated
reference case instead of a carry:

```
target health          = 100        (CCar root `health`, all 233 roots, DAMAGE_MECHANISMS.md §1)
contact time at 80 km/h = 1.1 m / 22.222 m/s = 0.0495 s ≈ 0.05 s
rate = 100 / 0.05      = 2000 / s   (a mid-band ram removes a normal vehicle's whole bar)
```

Predicted victim health loss = `2000 × t_contact`, with `t_contact = 1.1 m / (v / 3.6)`:

| ram speed | contact | predicted loss | BmAK's rule at that speed |
|---:|---:|---:|---|
| 20 km/h | 0.198 s | 396 → capped at 100 | ≈ 0 (band starts at 20) |
| 80 km/h | 0.050 s | 100 | ≈ 46 % of max |
| 150 km/h | 0.026 s | **52.8** | 100 % (band ends at 150) |

**The channel is speed-inverse**: a constant rate times a *shorter* contact at higher speed gives
*less* damage, exactly opposite to BmAK. This is the honest core of T-DM7: the rate can carry a
magnitude, and `min_rpm` can carry one threshold, but nothing in JC3 turns speed into damage. The
build therefore buys the 20 km/h floor (the gate) and accepts the inverted ramp as a declared
compromise; the pass band in §4 is written from the model, not from the wish.

Strafe and boost mods: `2000 × 2.25 = 4500/s` and `2000 × 2.0 = 4000/s` would be the values **if** a
per-state multiplier existed. It does not (one rate, no state input) — **UNKNOWN**, named in §7.

### 2.5 T-DM7 build composition

| stage | file | member | from | to | evidence |
|---|---|---|---:|---:|---|
| A | `batmobile_vehicle_common.vmodc` (private copy of the 12,271 B file) | `rotor_collision.damage_to_other_per_second` @0x138 | 100000 | **2000** | derived (§2.4) |
| A | same | `rotor_collision.min_rpm` @0x130 | 30 | **0** | derived: removes the rotor gate so the consumer is tested unconditionally |
| A | same | `light_object_mass_ratio` @0x13C | 0.02 | 0.02 | keep (2000 × 0.02 = 40/s → a 100-health prop survives 2.5 s: a shove, not a kill) |
| A | same | `mass_ratio_when_no_mass` @0x134 | 0.1 | 0.1 | keep (200/s on a massless object) |
| B | same | `min_rpm` @0x130 | 0 | **1260** | derived (§2.3): the 20 km/h gate |
| both | entity | module entry + `@files.xml` | shared path | private path | R7: private copy, build-time path hash |
| both | `vehicledamage` | `impact_damage_factor` | 0 | **0** | keep: T-DM8, own damage off, or the ram kills the player |

Write path: 4-byte float at a fixed offset in a file whose size does not change; `.toc` record
re-pointed with `eetoc.py patch`; values read back through `jc3adf.py dump` before packing.

---

## 3. What each layer can and cannot do for the ram (summary)

| need | layer | answer |
|---|---|---|
| damage to another object on contact | module `rotor_collision` | **yes** — one rate, two mass ratios, one RPM gate |
| speed → damage curve | none | **no** member; the rate is constant (§2.4) |
| strafe ×2.25 / boost ×2.0 | none | **no** per-state multiplier on the channel |
| 20 km/h floor | `min_rpm` | **yes, if** H1 (engine RPM) — 1260 |
| 150 km/h ceiling | none | **no** max-rpm member |
| collision trigger for a pulse | entity graph | **no** — `CForcePulse` fires on explosion only (0/23) |
| victim-side health | `CCar.health` 100 / `CDamageController` | **yes**, already there |
| character damage | not decoded | **UNKNOWN** — no character class in the 104-class graph vocabulary |

---

## 4. T-DM7 — the in-game check

**Card sentence (stage A, channel probe):**

> **Q-RAM-1A** — Ram a parked NPC car head-on at 80 km/h, then a second one at 150 km/h, then one at
> 20 km/h; each contact must remove **40–100 %** of the victim's health bar at 80 km/h, **40–65 %** at
> 150 km/h and **100 %** at 20 km/h (the inverted ramp is expected, §2.4), and the Batmobile's own bar
> must not move at any of the three speeds.

**Card sentence (stage B, gate probe):**

> **Q-RAM-1B** — With `min_rpm` 1260, the same three rams: **0–5 %** victim health loss at 20 km/h,
> **40–100 %** at 80 km/h, **40–65 %** at 150 km/h. A zero at 80 km/h means H2 (the gate reads rotor
> RPM) and the gate is reverted to 0.

Bands are the model in §2.4 with a ±20 % ratio tolerance (the project's ARM-2 convention) and the
health bar's 100-point scale. Stage A's 20 km/h expectation is 100 % precisely because the gate is
off — that row is the control that proves the gate, not a bug.

---

## 5. T-RA1 — the four functions, composed

### 5.1 Road assist — already carried, exact (no write)

| BmAK | value | JC3 member | now | verdict |
|---|---:|---|---:|---|
| `ImpactRoadAssistMaxTorque` (class default) | 15000 | `drift.counter_steer_torque_brake` | **15000** | **exact match, decoded** |
| `ImpactRoadAssistMaxTorque` (archetype) | 30000 | `drift.counter_steer_torque_handbrake` | **30000** | **exact match, decoded** |
| `ImpactRoadAssistMaxAngle` | 45 | `drift.max_drift_angle_deg` | **45** | **exact match, decoded** |
| `ImpactRoadAssistAngleStrength` | 1500 / 2000 | `drift.counter_steer_rot_factor` 0.0 | 0.0 | no unit bridge (1500/40000 = 0.0375; 2000/90000 = 0.0222) — **UNKNOWN** |
| `ImpactRoadAssistScenery/EnemyDuration` | 0.75 / 1.5 s | none (`exit_drift_yaw_vel_damp` 0.5 is a rate) | — | **gap** |
| `ImpactRoadAssistSteeringFactor` | 30 | `drift.steering_sensitivity` | 4.0 | 30 is out of the fleet domain and would wreck normal steering — **no write** |
| `ImpactRoadAssistFactor` | 40000 / 90000 | none | — | **gap** |

**Trigger (compromise):** the counter-steer torque fires when the player counter-steers **in the drift
state**, not on the frame after a wall hit. That is the same physical action BmAK's assist amplifies
(steering out of a deflection) with a different trigger source. **Evidence: values decoded; trigger
declared.**

**Check Q-RA-1** — hit a wall at 60 km/h with the car yawed 30°, then counter-steer: heading returns
to within **5°** of wall-parallel in **≤ 1.5 s** (the `EnemyDuration` value) while the car keeps ≥ 40 %
of its speed. Pass on 3 of 3.

### 5.2 Dodge — the boost force plus the jump impulse

| BmAK | value | JC3 member | from | to | evidence |
|---|---:|---|---:|---:|---|
| `PMDodgeForce` | 6000 | `arcade.nitro_boost.push_force` | 15000 | **6000** | decoded value, force→force |
| `PMDodgeDuration` | 0.25 s | `arcade.nitro_boost.boost_blend_time` | 0.2 | **0.25** | decoded, closest time member |
| `PMDodgeTorque` | 5000 | `arcade.turbo_jump.r_multiplier` 12 / `f_multiplier` 15 | — | **no write** | unit mismatch (a multiplier is not a torque) — **UNKNOWN** |
| `bAllowPMDodge` | True | none | — | — | **no switch** |
| `BattleDodgeImpulse` | 100000 | `arcade.turbo_jump.*` (fixed-axis impulse) | 15 / 12 / 50 / 200 / 2.0 | keep | shape fits (impulse + speed + multiplier), trigger is the jump action |

**The mass problem, stated:** 6000 N on a 6000 kg car is **1.0 m/s²**; over the 0.25 s duration that is
0.25 m/s and **0.031 m** of displacement — not a dodge. Either the BmAK force is not in newtons or the
Batmobile is far lighter than the 6 t this build carries (`rigid_body.mass` 6000). Scaling by a 4×
mass ratio would give **24000**, and `nitro_boost_upgraded.push_force` is 20000 — suggestive, not
proof. The unit is **UNKNOWN** (§7) and the check is therefore relative.

**Trigger:** the boost input while steering. **Compromise:** the dodge is a forward push, not a lateral
one; the lateral component comes only from `turbo_jump`'s fixed-axis punch.

**Check Q-DG-1** — at 80 km/h, boost+sidestep for 0.25 s must move the car laterally **≥ 2×** the same
input without boost, and must not spin it past 20° yaw. Pass on 3 of 3; if displacement is under 0.05 m
the force unit is wrong and the leg is reverted.

### 5.3 Shove — a pulse, speculative

| BmAK | value | nearest member | plan |
|---|---:|---|---|
| `VehicleShovingTorque` (archetype / class) | 10000 / 20000 | `CForcePulse` hashed impulse `id:24872388` (fleet 25..1000) | **speculative**: write 10000 into one pulse's impulse slot, trigger on the pulse's own button |
| — | — | `drift.max_drift_torque` | no: taken by T-AC1's 8000, and a torque on the attacker is not a shove on the victim |

**No collision trigger exists** (`FORCEPULSE.md`: collision 0 of 23 tune paths), so the shove becomes a
**player-triggered** pulse that must be aimed; the contact that BmAK reacts to is replaced by a button.
**Evidence: value decoded; mechanism speculative; trigger wrong by construction.**

**Check Q-SV-1** — fire the pulse with a car 1 m off the nose: the car is displaced **≥ 1 m** laterally
in ≤ 0.5 s and takes no damage (the pulse's damage slot stays 0). If the car is unmoved, the impulse
slot is not the one written — revert.

### 5.4 Kill-flip — −2,000,000 over 1.5 s, the hardest gap

| BmAK | value | member that could hold it | verdict |
|---|---:|---|---|
| `KillFlipTorque` | **−2000000** | `drift.max_drift_torque` ceiling 35000 | **57× short — impossible** |
| | | `CForcePulse` impulse slot | reachable as a raw float; **2000× the fleet max** (1000) — **speculative, out of domain** |
| `KillFlipTorqueDuration` | 1.5 s | none (a pulse is instantaneous) | **gap** |

Plan: one pulse, impulse **2000000**, applied at the victim's side above its centre so the impulse
becomes a roll; trigger the same button as the shove. The 1.5 s hold cannot be expressed — a pulse is
one impulse, so the flip must be won in the first frames or not at all. **Evidence: value decoded;
carrier speculative and 2000× out of domain; unit UNKNOWN; duration absent.**

**Check Q-KF-1** — pulse beside a moving NPC car at 40 km/h: the car's roll must exceed **90°** within
1.5 s (it lands on its roof or side) in **2 of 3** attempts, and the Batmobile must not be flipped by
its own pulse (it is outside the radius or takes no impulse). If nothing moves, the impulse is being
clamped — the slot's range (25..1000 in the fleet) is then a hard limit and the leg is dropped, not
retuned.

### 5.5 The T-RA1 build, in one table

| leg | file | member | from | to | trigger | evidence |
|---|---|---|---:|---:|---|---|
| road assist | `custom_land_global.vmodc` | *(nothing)* | — | — | counter-steer in drift | decoded exact match |
| dodge force | `custom_land_global.vmodc` | `arcade.nitro_boost.push_force` | 15000 | **6000** | boost + steer | decoded value |
| dodge time | same | `arcade.nitro_boost.boost_blend_time` | 0.2 | **0.25** | same | decoded, closest |
| shove | entity graph, one `CForcePulse` | hashed impulse `id:24872388` | 25..1000 | **10000** | pulse button | speculative |
| kill-flip | entity graph, one `CForcePulse` | hashed impulse `id:24872388` | 25..1000 | **2000000** | pulse button | speculative, 2000× out of domain |

Shove and kill-flip cannot share one pulse (one slot, two magnitudes); they are two pulses on two
buttons, or one pulse rebuilt per test. The build ships **road assist + dodge** as the real legs and
the two pulses as separate probe builds, so a speculative failure never drags a decoded carry down
with it.

---

## 6. Order of work and what each stage proves

| stage | build | writes | proves |
|---|---|---|---|
| 0 | `bm-RC4-ramA` | private `vehicle_common` copy, rate 2000, `min_rpm` 0 | the channel runs on a car (Q-RAM-1A) |
| 1 | `bm-RC4-ramB` | `min_rpm` 1260 | H1 vs H2, the 20 km/h gate (Q-RAM-1B) |
| 2 | `bm-RC4-assist` | road-assist (none) + dodge force/blend | Q-RA-1, Q-DG-1 |
| 3 | `bm-RC4-pulse1` | shove pulse 10000 | Q-SV-1 |
| 4 | `bm-RC4-pulse2` | kill-flip pulse 2000000 | Q-KF-1 |

Each stage is a separate tree and receipt; stage 0's private copy is the base for 1, and stages 2–4 do
not depend on it. A failed stage is reverted by deleting that tree, never by retuning in place
(STAGES: a failure becomes a fix card).

---

## 7. UNKNOWNs, each with the file that would settle it

| # | unknown | why it matters | settler |
|---|---|---|---|
| U1 | does the consumer run `rotor_collision` on a `CCar` with no rotor? | decides whether the whole T-DM7 leg exists | **Q-RAM-1A**; static route = the RotorCollision consumer in `JustCause3.exe` (not decoded) |
| U2 | is `min_rpm` compared to engine RPM or rotor RPM? | H1 → gate 1260; H2 → gate must be 0 | **Q-RAM-1B** (the two stages distinguish it) |
| U3 | `ImpactMaxDamage` / `ImpactMinDamage` / `ImpactMaxDamagePow` | the absolute damage the rate should match | `BmGame.upk` CDO / archetype tags — `Research/BatmobileGrab/CHAIN.json` has none; a CDO dump (`chase08_cdo.py`) or a live read |
| U4 | contact time and the mass-ratio law (victim mass / attacker mass) | the rate 2000 assumes 1.1 m of engagement and ratio ≈ 1 | Q-RAM-1A's frame count; the consumer in the exe |
| U5 | is `PMDodgeForce` 6000 newtons? | 1 m/s² on 6 t is not a dodge; 4× scaling would be 24000 | the exe's dodge consumer (not decoded); Q-DG-1's displacement |
| U6 | what are `CForcePulse`'s hashed impulse members (`id:24872388`, `id:9865E7F2`)? | no name → no unit; the 2e6 write is blind | `FORCEPULSE.md` §1: names are in no shipped table; a live probe, or the exe's pulse consumer |
| U7 | is a pulse impulse clamped to ~1000? | if yes, kill-flip is impossible | Q-KF-1; the exe consumer |
| U8 | does `counter_steer_torque` fire after a *wall hit* or only in the drift state? | road assist's trigger | Q-RA-1 with and without drift entry; the Drift consumer (not decoded) |
| U9 | character damage from contact | "ram a pedestrian" has no decoded path at all | the NPC/character damage system in the exe; no asset file |

---

## 8. Commands run for this note (re-runnable)

```
# the rotor block, decoded and offset-checked
python Tools/scripts/jc3adf.py dump \
  Builds/bm-RC2/aaf/editor/entities/jc_vehicles/00_shared/modules/vehicle_common.vmodc \
  | grep rotor_collision
#   rotor_collision.min_rpm                        float  30.0
#   rotor_collision.mass_ratio_when_no_mass        float  0.1
#   rotor_collision.damage_to_other_per_second     float  100000.0
#   rotor_collision.light_object_mass_ratio        float  0.02

python - <<'EOF'   # offsets: instance 0x50 + rotor 0xE0, members 0/4/8/12
import struct
b=open("Builds/bm-RC2/aaf/editor/entities/jc_vehicles/00_shared/modules/vehicle_common.vmodc","rb").read()
for n,o in [("min_rpm",0x130),("mass_ratio_when_no_mass",0x134),
            ("damage_to_other_per_second",0x138),("light_object_mass_ratio",0x13c)]:
    print(n, hex(o), struct.unpack_from("<f",b,o)[0])
EOF
# 0x130 30.0 | 0x134 0.10000000149011612 | 0x138 100000.0 | 0x13c 0.019999999552965164

# the gearing inputs behind min_rpm 1260
python Tools/scripts/jc3adf.py dump .../v0300_..._transmission.vmodc | grep -E "gear_ratios|final_drive"
python Tools/scripts/jc3adf.py dump .../v0300_..._land_global.vmodc    | grep radius
python Tools/scripts/jc3adf.py dump .../v0300_..._land_engine.vmodc    | grep rpm
```

**Sources:** `tmp/freebuff/reports/carrier-ram-and-dodge.md` (candidate table, layer search);
`Research/BatmobileGrab/CLASS_DEFAULTS.md` and `DAMAGE_RULES.md:153,274` (the two value sets);
`Research/BatmobileGrab/DAMAGE_RULES.md` §3.3 (`CalculateAndStoreImpactDamage`, all outgoing);
`Research/JC3Grab/DAMAGE_MECHANISMS.md` (root health 100, `CDamageController`);
`Research/JC3Grab/FORCEPULSE.md` §4.1 (explosion-only trigger, hashed impulse slots);
`Research/JC3Grab/VOCABULARY.md:1415-1418` (rotor block ranges);
`Research/JC3Grab/README.md:681` and `WATER.md:239` (R7: shared module needs a private copy);
`Working/Translation/T_ROWS.jsonl:95,103` (the two rows and their `out` disposition);
`Builds/bm-RC2` modules (gearing, wheel radius, drift block, boost and turbo-jump values, mass 6000).
