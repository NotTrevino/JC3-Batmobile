# Stuck / flipped recovery — merged build plan

Two records merged into one plan for the JC3 Batmobile build:

| source | path | what it contributes |
|---|---|---|
| scrape | `reports/stuck-flip-scrape.md` (`tmp/freebuff/reports/stuck-flip-scrape.md` is the same file) | package-level numbers: timers, torque fields, `FlipVehicle` body literals, Hydra reset family, the B/X/Y/D-Pad call site, the negative results on binding, animation, HUD |
| plan | `tmp/freebuff/reports/stuck-flip-recovery-plan.md` | the JC3 side: `CHALLENGE_RESET_VEHICLE`, `CForcePulse`, `DriverLean.righting_torque`, the `ParentIsUpRightCondition` predicate, the inertia arithmetic, the pilot card |

Where the two disagree the merge says so in §2 and takes the value the named file supports.
Nothing here was launched, attached to or written outside `tmp/freebuff/reports/`.

**Labels.** **decoded** = bytes read at the package/export/offset quoted. **derived** = a stated
rule or arithmetic over decoded values, with the arithmetic printed. **UNKNOWN** = absent from
every file read, with the file or probe that would settle it.

---

## 1. What BmAK does, step by step

The operator's lead ("B flips the car when it is stuck") resolves into **two recoveries that the
lead conflates**: a local torque flip, and a Hydra reset keyed on *why* the car was lost.

| # | step | BmAK mechanism | value | label | evidence |
|---|---|---|---|---|---|
| S1 | decide the car is over | up-axis test against world up: `|world_up · car_up|` | threshold **0.707** (45°) and **−0.707** (135°) | decoded gate, derived posture | `PAWNMESH_D8.md:10`, constants row `0.707@464` in `DRIVE_MODES.md:257`; the quantity is `Mesh.LocalToWorld.ZPlane.Z` = `[mesh+0xd8]` (`PAWNMESH_D8.md:1-8`) |
| S2 | decide the car is stuck | `BatmobileStuckTime` accumulator vs two class floats | `BatmobileStuckTimeMax` **2.0 s** (7452), `BatmobileStuckTimeFlip` **0.5 s** (7456) | decoded fields; **which one `TryRightingFlip` reads is UNKNOWN** | `CLASS_DEFAULTS.md:287-288`; scrape §1.3 |
| S3 | the press that offers the flip | `DrivingMode.SelectVehicleWeapon` calls `TryRightingFlip(false, 74)` at script offset **315**, between two `TryToFireWeapon` at 278 / 402 | — | decoded call site, **conditional-ness UNKNOWN** | `DRIVINGMODE.md:83`; scrape §1.1 |
| S4 | buttons that reach it | `QuickGadgetB/X/Y` → `SelectVehicleWeapon(1/2/3)`; D-Pad Up → `SelectVehicleWeapon(4)` | 4 presses, one function | decoded chain, derived reach | `DefaultInput.ini:259,268,269,270` via scrape §1.2 and plan §1.2 |
| S5 | the flip itself | `TryRightingFlip` (export 10572, 11 script bytes, no calls) → native; `FlipVehicle(bool bInstant)` (10596) uses `AddTorqueOverTime` + `AddKeepyUpForce` | literals **1000.0** and **2.0** | derived (body call/const layout), body native | scrape §2.6 |
| S6 | righting torque fields (the only serialised numbers near it) | `JumpRampRightingTorque` / `JumpNoRampRightingTorque` on all four playable archetypes | **2000 / 2000** | decoded | `MODES.md:159-160` |
| S7 | kill-flip pair (offensive, not recovery — the naming trap) | `KillFlipTorque`, `KillFlipTorqueDuration`, `KillKeepyUpFactor`, `KillKeepyUpFactorDuration` | **−200** (−400 Joker) / **0.5 s** (0.75 Joker) / **10** / **0.75 s** | decoded | `MODES.md:164-167` |
| S8 | self-righting mode flag | `SelfRightingMode` byte at 5900 | **0** shipped (CDO carries no tag) | decoded carrier, **meaning UNKNOWN** (no `ESelfRightingMode` names in the package) | scrape §1.1; `CONTROLS.md:169` |
| S9 | animation | none | no vehicle `*Flip*` clip; `FlipAnimName`/`bPlayingFlipAnimation` belong to `RBatarangCamera` | decoded negative (same-name trap) | scrape §1.5; `ANIMATIONS.md` |
| S10 | camera | no flip-specific camera value; the flip rides the normal chase camera | shake list has boost 35 and wheelspin 50×50×25 only | decoded negatives, **flip camera behaviour UNKNOWN** | `CAMERA.md:189`; scrape §1.5 |
| S11 | audio | `Play_Batmobile_Rotation` is the only rotation-tagged vehicle event: **0xD1A01DEE**, bank `BML_Batmobile`, 22 WEMs, 665,044 B, 4 event rows, switch `BML_Steering_Rotation` | — | decoded object; **is it the righting cue is UNKNOWN** | `AUDIO_MAP.md:67`; `AUDIO_FEATURES.md:214` |
| S12 | effect | none | nearest is `Exhaust.SideExhaust_Burst` on the *strafe* path, disjoint from the flip | decoded negative | scrape §1.5, §2.6 |
| S13 | HUD / prompt | none in BmAK | 0 hits in `HUD.md`; only GFx names `CI_FlipBatmobile` and `VGS_StrafeButton` exist, with **UNKNOWN** users | decoded names, UNKNOWN consumer | scrape §1.2 |
| S14 | give up and reset | `SendHydraEventBatmobileResetByGettingStuck` / `…ByFalling` / `…ByGettingCrushed` / `…ByBlowingUp`, native, 0-byte stubs | 4 reason codes | decoded names | `NATIVE.md:78-80`; scrape §1.5 |
| S15 | what the strafe press does (adjacent, *not* the flip) | A = `BattleStrafe` → `CheckBattleStrafe` → `BattleMode.BattleDodge` → `VehicleStrafe` → `KickStrafe(force, torque, duration)` (native) | pursuit: **PMDodgeTorque 6000 / PMDodgeForce 10000 / PMDodgeDuration 0.15 s**; battle: **BattleDodgeImpulse 150000**; cooldown **0.75 s**; `StrafeForce/Torque/Duration/Time` **not serialised anywhere** | decoded fields, derived argument order | scrape §2.2–2.5; `MODES.md:176-180` |

**Verdict the merge keeps.** The flip and the side boost are separate physics actions with
disjoint tuning, reached from different functions; what they share is only the press path. `B`
does not *carry* the flip — no binding token in `BINDINGS_MERGED.json` (176 rows) names
flip/upright/unstick/recover — the flip is a call *inside* the weapon-select function that B (and
X, Y, D-Pad Up) already runs.

---

## 2. Merge conflicts, and which file wins

| # | conflict | which file wins | disposition |
|---|---|---|---|
| M1 | `SelectVehicleWeapon` export number: **104971** (plan §1.2) vs **104978** (scrape §1.1) | `Research/BatmobileGrab/DRIVINGMODE.md:83` — "state body (export 104971, 486 bytes, 448 script bytes)" and the same 278/315/402/432 offsets the scrape quotes | same function, one number is a transcription slip. **The build keys on the script offsets (315), not on the export id** |
| M2 | `DriverLean.righting_torque` is "23 aircraft-class vehicles" (plan §2.1) | `Research/challenge/card-T-10.md` A4: **18 bikes + 5 boats, 0 aircraft** | corrected. It is a *land*-vehicle self-righting torque — bikes and jet-skis — and no car carries it. The plan's §2.1 sentence must not be reused |
| M3 | `Jump*RightingTorque` class default: **5000 / 2500** (plan §1.4, from `CLASS_DEFAULTS.md:147`) vs "CDO carries no tag at 6756/6760" (scrape §1.4) | both records | the 5000/2500 is the declared `.g.cs` default; the serialized CDO byte is absent. **Use the archetype 2000**, which is the value that runs |
| M4 | righting impulse: plan §3.2 says **115,000 N·m·s** at ω = 12.6 rad/s | arithmetic in the same section | 12.6 rad/s = **2π/0.5 s = a full 360°** in 0.5 s. For 180° in 0.5 s, ω = π/0.5 = **6.283 rad/s** → J = 9165.3 × 6.283 = **57,600 N·m·s**. The 115,000 figure is kept only as the 360° case |
| M5 | "B is bound to the flip" | scrape §1.2 (B command list, 0 flip tokens) | the plan already says B *reaches* it through `QuickGadgetB`; the merge states it as reach-through, not binding |

---

## 3. The closest JC3 system for each step

### 3.1 Reset / respawn — `CHALLENGE_RESET_VEHICLE` (S14, and the S2 give-up branch)

| item | value | label | evidence |
|---|---|---|---|
| action | `CHALLENGE_RESET_VEHICLE` | decoded | `INPUT.md:61` |
| gamepad / keyboard | **LPADDOWN** / **P** | decoded | `INPUT.md:61`, `DRIVE_CARRIERS.md:182` |
| node hash | `851F0D7A`, present in all four keymap layers | decoded | plan §2.1 |
| scope | the **only** land-vehicle reset action in either keymap | decoded | `DRIVE_CARRIERS.md` §4.1 (16 land actions, none other is a reset) |
| consumer | **UNKNOWN** — no entity names `keymap` (0/232) | — | `DRIVE_CARRIERS.md` §4.1 |

**Gap the build closes.** A reset that teleports is not a righting in place. The build's first
action is the 5-minute probe (plan §3.5): flip a car in vanilla free roam, tap `P` / `LPADDOWN`.
If it rights in place, S14 is a rebind and the rest of S1–S8 is unnecessary. If it respawns at a
challenge start, S14 stays the *fallback* after the 2.0 s budget, and S5–S7 carry the in-place
flip. Record the outcome in `MODLOG.md` either way; nothing else can settle it.

### 3.2 Flip torque — the righting member and where it exists (S5–S7)

| candidate | value | label | evidence | usable on a car? |
|---|---|---|---|---|
| `DriverLean.righting_torque` | **1500 .. 4000**, median **3000**, n=**23** | decoded | `VOCABULARY.md:566`; `card-T-10.md` A4 | the mechanism exists on **18 bikes + 5 boats, 0 aircraft, 0 cars** |
| `DriverLean.leaning_torque` | 2000 .. 8000, med 5000, n=23 | decoded | `card-T-10.md` A4 | same 23 |
| `DriverLean.max_lean_angle_deg` | 20 .. 40, med 30, n=23 | decoded | same | the *lean* limit, not a flip angle |
| `motorbike_common.roll_to_fall_with_driver_deg` / `_no_driver_deg` | **80 / 50**, n=232 | decoded | `card-T-10.md` A4 | the fall threshold on every vehicle module — a *test*, not a torque |
| whether a `CCar` module accepts a `DriverLean` block | — | **UNKNOWN** | `card-T-10.md` A4 ("untested") | this is the one experiment that would let a righting torque ship as **data** |

**Gap.** JC3 has no righting member on a car. Three routes, in cost order:

1. **Data probe (cheapest).** Add a `DriverLean` block (`righting_torque` 3000, `leaning_torque`
   5000, `max_lean_angle_deg` 30 — the medians of the 23) to the Batmobile's `CarHandling`/
   `CustomLandGlobal` module set and see whether the module loader accepts it and the sim reads
   it. Settles M-route 1 either way in one build.
2. **Vertical punch.** `turbo_jump.up_multiplier` **12 .. 25** (upgraded **25 .. 50**), n=35,
   `punch_delay_time` 0 .. 0.1 s, `punch_speed_kph` 50. A real member on land vehicles with an
   **UNDECODED consumer** (`VOCABULARY.md:361`). If it fires on `USE_VEHICLE_MOD`, a lift punch can
   start the roll; it cannot finish one, because it is along a fixed axis.
3. **Native hook (R17).** Apply torque/angular velocity to the car's rigid body when the flip
   condition holds — the route that mirrors BmAK exactly, and the only one that can guarantee the
   angle.

### 3.3 `CForcePulse` — the closest "shove the body" carrier (S5, if a pulse is used)

| item | value | label | evidence |
|---|---|---|---|
| tuning | `car_explosion_medium.ftune`: `PlayerDamage` **500** / `PlayerDamageRadius` **5 m**, AIDamage 500/5; `*RadiusPercentageMax` 0.0 (damage falls off at once) | decoded | `FORCEPULSE.md` fleet table |
| zero-damage variant | `gen_explosion_5m_nodamage.ftune`: **0 / 5 m** — "push only" | decoded | `FORCEPULSE.md` §3 |
| what fires one | **explosion only**: 22 of 23 tunes live under `jc_explosions/`, 0 of 23 tune paths name a collision, 0 name a horn | decoded | `FORCEPULSE.md` §4.1 |
| class instances | 307 `CForcePulse` objects; `CForcePulse` → `car_explosion_medium.ftune` is on every `CCar` donor | decoded | `FORCEPULSE.md` §2, §5 |

**Gap.** A pulse is radial and explosion-fired: wrong trigger, wrong axis. The build can only use
it as a **pop** (the `up_multiplier` role) on the zero-damage tune, and it must be fired from the
interaction graph, not from a collision. Anyone reading this plan should not expect a pulse to
right a car about its roll axis — it cannot, by construction.

### 3.4 Aircraft righting torque and drift — the two near-misses (S5)

| candidate | value | why it is not the flip | evidence |
|---|---|---|---|
| `righting_torque` on aircraft | none — the member is on bikes/boats (§3.2) | the name is right, the population is not | `card-T-10.md` A4 |
| `drift.max_drift_torque` / `constant_drift_torque` / `counter_steer_torque_handbrake` | 5000 (0..35000) / 0 (0..20000) / present | **yaw**, continuous, and it needs motion — it cannot rotate a stationary car | `DRIVE_CARRIERS.md:118-119`; `VOCABULARY.md:467` |
| `arcade.turbo_jump.*` | punch 50 kph, top 200 kph, `f_multiplier` 15, `r_multiplier` 12 | along the car's forward axis, on the jump action | `EJECT.md:198-203` |
| `arcade.nitro_boost.push_force` | 15000 | linear push, wrong axis | `DRIVE_CARRIERS.md:296` |

**Gap.** No JC3 land carrier supplies a roll-axis torque, so the drift/aircraft path is a
dead end for the flip and is recorded here only to stop the next reader re-opening it.

### 3.5 The upright test JC3 *does* have (S1)

| item | value | label | evidence |
|---|---|---|---|
| `CInteractionGraphParentIsUpRightCondition` | **6,761** instances | decoded | `ENTITIES.md:11` |
| where it is used | every exit in the donor's 26 exits, as check 1 — `exit.ai.driver.default` and its 0/90L/90R/180 variants | decoded | `EJECT.md:57-64` |
| what it gives the build | a **first-class "is the parent upright" predicate** in the `.epe` interaction graph — the trigger S1/S2 needs, already shipped | decoded | same |

**Gap.** The predicate is the *gate*; nothing behind it applies torque. The build pairs it with
§3.2 route 1 or 3: the graph fires the recovery, the module (or hook) supplies the rotation.

### 3.6 Camera (S10)

| item | value | label | evidence |
|---|---|---|---|
| JC3 vehicle camera | `GenericVehicleCamera`, 800-byte ADF struct, 321 instances; base tune `car_base.ctune` | decoded | `FX.md`; `CAMERA.md` §4 |
| roll handling | `RollWithVehicleAmount` **0.3**, `RollLimit` **[-20, 20]°**, `RollSpringStiffness` **1.0**, `PitchLimit` **[-70, 10]°** | decoded | `CAMERA.md` §4 |
| shake carriers | `CameraShakeModifierParams`, `RadialBlurParams`, `CameraTransitionParams` classes exist in `.ctunec` | decoded | `FX.md` class list |
| BmAK flip camera | no flip-specific value; shake list carries boost 35 and wheelspin 50×50×25 only | decoded negative | `CAMERA.md:189` |
| what BmAK's camera does during a flip | — | **UNKNOWN** | a live capture; `CAMERA.md` has no flip row |

**Gap.** JC3 clamps vehicle roll to ±20°, so a 180° flip happens under a horizon that stays level
— readable, but not BmAK's feel. The build's choice: keep ±20 (no edit) or widen `RollLimit` in
the Batmobile's own `car_base`-length copy of the tune (the `CCameraModifier` path is a renameable
NUL-terminated string, `CAMERA.md` §4). A flip shake would need a `CameraShakeModifierParams`
block that no vehicle tune in the corpus carries — name it as new content, not a port.

### 3.7 Audio (S11)

| item | value | label | evidence |
|---|---|---|---|
| JC3 carrier | an `SAttachedEffect` / `SDynamicAttachedEffect` in the `.epe` naming a **16-byte event GUID** in a FEV bank (`vehicles` / `character` / `effects`) | decoded | `JC3_AUDIO.md` §1-§3 |
| donor coverage | 45 events pinned in 758 B of `.ee.fmod_guids`; **45 of 45** found in a bank; 23 named by an attached effect | decoded | `JC3_AUDIO.md` §3 |
| BmAK cue candidate | `Play_Batmobile_Rotation` 0xD1A01DEE, `BML_Batmobile`, 22 WEMs, 665,044 B, 4 rows, switch `BML_Steering_Rotation` | decoded object, **cue role UNKNOWN** | `AUDIO_MAP.md:67`; `AUDIO_FEATURES.md:214` |
| is there a flip event in the donor's 45 | no rotation/roll/flip role among them | decoded negative | `JC3_AUDIO.md` §3 |

**Gap.** BmAK's event lives in a BmAK bank (Wwise, `BML_Batmobile`); JC3's banks are FMOD
Designer FEV with GUID-only identity and **no event name stored anywhere** (`JC3_AUDIO.md` §1).
Nothing in this repo imports a Wwise WEM into a FEV bank, so the round-trip cue cannot ship from
the data path. The build therefore either (a) reuses an existing JC3 vehicle event whose role is
already resolved (the honest placeholder), or (b) records the flip as silent, which is what BmAK
itself does not do but JC3 cannot source.

### 3.8 HUD / prompt (S13)

| item | value | label | evidence |
|---|---|---|---|
| BmAK prompt | none; `HUD.md` 0 hits for flip/stuck/recover/right | decoded negative | scrape §1.5 |
| BmAK icon names that do exist | `CI_FlipBatmobile`, `VGS_StrafeButton` — GFx names, **user UNKNOWN** | decoded names | scrape §1.2 |
| JC3 prompt carrier | the vehicle's own `.stringlookup` holds interaction prompts and no name; `A2B9F82C` = "Get in Vehicle" | decoded | `NAMES.md:76-83` |
| writer | `Tools/scripts/jc3strings_write.py` (add-only) | decoded tool | `Tools/scripts/jc3strings_write.py` |

**Gap.** BmAK's design is prompt-free, so the build adds **no** HUD row and no string. That is a
decision, and it is also why the operator found the flip by accident. If the build later wants a
prompt, the carrier is a `.stringlookup` entry plus the entity's use-item graph — not a HUD widget.

---

## 4. The build, per step: value to write and the gap it closes

Numbers come from the scrape unless marked; the JC3 carrier is the §3 row named.

| step | build edit | value | label | gap closed |
|---|---|---|---|---|
| S1 gate | `.epe` interaction graph: `CInteractionGraphParentIsUpRightCondition` on the recovery node | threshold **0.707** (45°) | decoded gate | no trigger exists on the JC3 side; the predicate is shipped but unused on the Batmobile |
| S2 timers | graph-owned timers: 0.5 s before a <45° righting is allowed, 2.0 s to the reset | **0.5 / 2.0 s** | decoded fields | JC3 has no stuck accumulator at all |
| S3 press | reuse the weapon-select press; no new binding | `USE_VEHICLE_MOD` / the gadget action already in the control plan | derived | BmAK gets both behaviours from one button; the build must not spend a second |
| S4 rotation | torque about the roll axis, 180° in 0.5 s | **T = 230,300 N·m** for 0.5 s (I_roll **9,165 kg·m²**, α = 2π/0.25 = 25.13 rad/s²) | derived (plan §3.2 arithmetic, re-checked: 500 × (3.745² + 2.075²) = 9,165.3) | no member carries a roll torque — this is the hook route (§3.2 route 3) |
| S4′ | or one angular impulse | **J = 57,600 N·m·s** (ω = π/0.5 = 6.283 rad/s) — *not* the plan's 115,000, which is a full 360° | derived (M4) | cheaper to cancel; needs an angular-velocity write |
| S4″ | side case (90°) | **115,200 N·m** for 0.5 s (α = 12.57 rad/s²) | derived | the car must not be treated as a roof case when it is on its side |
| S5 stop | damp the roll when the up axis passes the target | **0.985** (10° from vertical) | derived from the 0.707 line | without it the flip overshoots; BmAK's own stop rule is UNKNOWN |
| S6 lift | keepy-up during the flip, BmAK-shaped | **2.0** force, 0.75 s (BmAK `FlipVehicle` literal + `KillKeepyUpFactorDuration`) | derived literal + decoded duration | a roll about the contact patch digs in; the lift is what BmAK adds |
| S7 fallback | 2.0 s exceeded → reset | `CHALLENGE_RESET_VEHICLE` probe first | decoded action, undecoded consumer | the only JC3 reset action; consumer must be probed |
| S8 camera | keep ±20° roll clamp, or widen the Batmobile's own `car_base` copy | `RollWithVehicleAmount` 0.3, `RollLimit` ±20° | decoded | the flip reads under a level horizon otherwise |
| S9 audio | reuse a resolved vehicle event, or ship silent | `Play_Batmobile_Rotation` is **not** importable (Wwise → FEV) | decoded negative | no flip cue exists on the JC3 side |
| S10 HUD | nothing | — | decoded negative | prompt-free by BmAK's design |
| S11 strafe | leave the A path alone; the flip must not call it | PMDodge 6000/10000/0.15; BattleDodgeImpulse 150000; cooldown 0.75 s | decoded | proves the flip does not need the strafe path — one less thing to touch |

---

## 5. Pilot card — one sentence per step

Written to be read aloud by a tester with the car in hand. Each carries its pass band.

| step | pilot-card sentence |
|---|---|
| **S1/S2 gate** | "Drive onto a kerb until the car leans past 45° and hold still: the recovery must not begin before **0.5 s** of no progress and must have finished by **2.0 s**." |
| **S3 press** | "With the car upright, the same button must fire the equipped gadget and **not** roll the car; with the car over, the same press must roll it — one button, two behaviours." |
| **S4 roof case** | "Put the car on its roof and press once: it must be wheels-down in **≤ 0.5 s**, and the roll must not take longer than the 2.0 s budget." |
| **S4 side case** | "Put the car on its side and press once: it must come down onto its wheels in **≤ 0.5 s** and must not roll past vertical onto the other side." |
| **S4′ impulse** | "The roll must start and stop within one press: no residual spin after the car is level (roll rate must be **0 rad/s at the 0.985 target**)." |
| **S5 stop** | "The car must end with its up axis **≥ 0.985 of world up (within 10°)** — landing between 45° and 10° is a failed recovery, not a partial one." |
| **S6 lift** | "The car must not hop: the roof may rise by at most **0.5 m** during the roll, and the car must not leave the ground for more than **0.25 s**." |
| **S7 fallback** | "Wedged under a bridge where no roll can work, the car must reset within **2.0 s** of the flip failing, and must arrive on a drivable surface with **0 m/s** residual velocity." |
| **S8 camera** | "During the roll the horizon must stay readable: the camera may tilt with the car up to **20°** and must return to level within **1.0 s** of the car landing." |
| **S9 audio** | "The roll must produce exactly **one** discrete cue, not a loop, and it must stop when the car is level (no cue continues while driving away)." |
| **S10 HUD** | "No prompt may appear: the recovery is prompt-free, so a visible 'press X to recover' element is a **failure** of this card, not a bonus." |
| **S11 strafe** | "Hold the stick and tap the strafe button with the car upright: the car must dodge laterally exactly as before, and the flip must not fire (no roll on a strafe press)." |
| **whole feature** | "Take the car off a cliff, land on its roof, and press once: **≤ 0.5 s** to wheels-down, **≤ 2.0 s** to driveable, and the car must not be launched more than **0.5 m**." |

Pass-band sources: 0.5 / 2.0 s decoded (`CLASS_DEFAULTS.md:287-288`); 0.707 decoded
(`PAWNMESH_D8.md:10`); 0.985 derived (10° = the smallest angle at which the 45° line stops being a
false pass); 0.5 m derived (a roll about the contact patch lifts the roof by at most half the width,
3.745/2 = 1.87 m, so 0.5 m is the non-teleport allowance); 20° roll clamp decoded (`CAMERA.md` §4).

---

## 6. Order of work, and what stops it

1. **Probe** `CHALLENGE_RESET_VEHICLE` (P / LPADDOWN) on a flipped car in vanilla free roam. This
   decides whether the feature is a rebind or a hook. Nothing else should be written first.
2. **Data probe**: a `DriverLean` block on the Batmobile's land modules (§3.2 route 1). Two outcomes,
   both useful: the loader accepts it (righting as data, no hook) or it refuses (route 3 is the only
   path).
3. **Only then** the torque hook: 230,300 N·m for 0.5 s about the roll axis, damped at 0.985, with
   the 2.0 lift and the 2.0 s reset fallback.
4. Camera and audio are independent and can ship after the physics works; both have named
   placeholder decisions, so neither blocks step 3.

**What stops the plan from being "no member".** Every step above names a carrier that exists in
this repo's records — the upright predicate, the reset action, the righting member (on the wrong
population), the vertical punch, the pulse tune, the camera tune, the attached-effect GUID, the
prompt store — and where the carrier is missing, it names the experiment that closes it. The one
step with no JC3 carrier at all is the audio cue, and that is a real limitation, recorded as such
in S9 rather than filled with an invented event.

---

## 7. UNKNOWNs, each with the file or probe that settles it

| # | UNKNOWN | settling file or probe |
|---|---|---|
| U1 | which timer `TryRightingFlip` reads (0.5 or 2.0) and whether the offset-315 call is conditional | `Research/BatmobileGrab/DRIVINGMODE.md` bytecode walk with branches resolved; `BmGame.upk` export 10572 |
| U2 | `TryRightingFlip`'s body: torque magnitude, duration, whether it no-ops upright | disassembly at `REGISTRATION.json:163` VA, read-only (method of `PAWNMESH_D8.md`) |
| U3 | `SelfRightingMode` = 0: what the enum members mean | `BmGame.upk` bytecode at 5900, or a live read of `+0x170C` |
| U4 | writers of `BatmobileStuckTime` (0x1d18) / `BatmobileStuckTimeFlip` (0x1d20) | `.text` xref scan for displacements `18 1d 00 00` / `20 1d 00 00` |
| U5 | whether a `CCar` entity accepts a `DriverLean` block | one build + `Tools/scripts/*` module loader; the module type is decoded on 23 bikes/boats (`card-T-10.md` A4) |
| U6 | `CHALLENGE_RESET_VEHICLE`'s runtime effect (right in place vs challenge respawn) | in-game probe, §6 step 1; no entity names `keymap` (0/232) |
| U7 | `turbo_jump.up_multiplier` (12..25) — does a land car consume it, and on which action | `VOCABULARY.md:361` consumer is undecoded; a build with the member set and a take |
| U8 | BmAK's flip camera behaviour (snap vs animate; shake?) | live capture; `CAMERA.md` has no flip row and `ANIMATIONS.md` no clip |
| U9 | whether `Play_Batmobile_Rotation` is the righting cue | live BmAK capture with the flip pressed; `AUDIO_FEATURES.md:214` gives the switches, not the trigger |
| U10 | the N·m bridge behind BmAK's "engine torque" units | nothing in this tree — needs a BmAK take with a known inertia, itself UNKNOWN (`INERTIA.md` §6) |
| U11 | whether the flip shares an internal kick with the strafe (native-to-native) | hook 10572 and watch for a `KickStrafe` call or a `SideExhaust_*` spawn (scrape §2.6) |
| U12 | the roll angle / speed gate BmAK uses for "stuck" (no field implements it) | runtime watch of `Rotation.Roll` at a flip with a hook on 10572 |

---

## 8. Checks run for this merge

| # | check | result |
|---|---|---|
| 1 | both sources read in full | `reports/stuck-flip-scrape.md` (185 lines) and `tmp/freebuff/reports/stuck-flip-recovery-plan.md` (plan §1–§5); `reports/stuck-flip-recovery-plan.md` does **not** exist — the plan lives under `tmp/freebuff/reports/`, as the scrape itself records |
| 2 | every number re-derived where arithmetic exists | I_roll 500 × 18.3306 = 9,165.3 kg·m²; 180°/0.5 s → 25.13 rad/s² → 230,323 N·m; 90°/0.5 s → 115,190 N·m; impulse 9165.3 × 6.283 = 57,578 N·m·s (plan's 115,000 = 360°, M4) |
| 3 | JC3-side claims re-checked against local files, not memory | `INPUT.md:61`, `DRIVE_CARRIERS.md:182`, `card-T-10.md` A4, `VOCABULARY.md:361,566`, `FORCEPULSE.md` §3-§4, `EJECT.md:57-64`, `ENTITIES.md:11`, `NAMES.md:76-83`, `JC3_AUDIO.md` §1-§3, `FX.md`, `CAMERA.md` §4 |
| 4 | BmAK-side claims re-checked | `CLASS_DEFAULTS.md:287-288`, `MODES.md:159-167,176-180`, `PAWNMESH_D8.md:10`, `DRIVINGMODE.md:83`, `CAMERA.md:189`, `AUDIO_MAP.md:67`, `AUDIO_FEATURES.md:214`, `NATIVE.md:78-80`, `CONTROLS.md:169` |
| 5 | conflict scan between the two sources | 5 conflicts found (M1–M5), each resolved to a named file or an arithmetic correction |

**Limits.** This is a plan: no keymap, `.epe`, module, `.ctunec`, `.fev`, string or hook was
written, nothing was installed, no game was launched, and no ledger, backlog or `T_ROWS` row was
edited. Every BmAK "native" finding is an *absence of script*, not a read of native code. The
runtime questions — whether `P` rights a car, whether a `CCar` takes `DriverLean`, whether the
0.23 MN·m torque rolls a 6 t car, what BmAK's camera does — are named as probes in §6/U1–U12, not
asserted.
