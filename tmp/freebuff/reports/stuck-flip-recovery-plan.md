# Stuck-flip recovery — the B-button lead, tested against the files

Operator lead (2026-11-06, unverified): **B flips the Batmobile back over when it is stuck.**
Verdict: **the lead is right in structure and wrong in one detail.** B does reach the engine's
righting call — but so do X, Y and D-Pad Up, because the call sits inside the weapon-select
function all four buttons run. And it is not the recovery: the *reset* is a separate Hydra event.
Nothing was launched, attached to or written outside `Research/` and `tmp/freebuff/reports/`.

Labels: **decoded** = read from a file/package/exe at the named place; **derived** = arithmetic on
decoded values with the rule shown; **UNKNOWN** = not in any file read, with the file that would
settle it.

---

## 1. Step 1 — is there a self-right action in BmAK, and what fires it?

### 1.1 The action exists, by name (decoded)

| thing | where | label |
|---|---|---|
| `RVehicleBatmobileBase.SelfRightingMode` | `ByteProperty`, export 9772, offset **5900** (`CONTROLS.md:169`, `BMSDK_OFFSETS.json:21813`); runtime slot at `0x170C` in the BmSDK layout | decoded name; **value UNKNOWN** (no serialized value in `CLASS_DEFAULTS.md`, no enum members named anywhere in the grab) |
| `RVehicleBatmobileBase.TryRightingFlip` | export **10572**, 11 script bytes, **no calls** (`DRIVINGMODE.md:95`) | decoded — a native function (registered in `REGISTRATION.json:163`), body not in the package |
| `ApplyRightingTorque` | registered native name — `NATIVE.json:38` (the list); `NATIVE.md:92` prints only `TryRightingFlip` | decoded name; signature and units UNKNOWN |
| `ApplyRightingRoll` | registered native name — `NATIVE.json:37` | decoded name; same |
| `SendHydraEventBatmobileResetByGettingStuck` | native function, export 10479 (`CONTROLS.json:23503`, `NATIVE.md:80`) | decoded name — a **reset**, not a righting |
| `RSeqEvent_BatmobileStuck` | event object in the packages (`PACKAGES_G305.json:19105`) | decoded — the stuck state raises an event the level can see |

So BmAK has **two** layers and they are not the same thing: a torque-based `TryRightingFlip`
(a 180° roll) and a `...ResetByGettingStuck` teleport/respawn sent to Hydra. Which one the player
sees when upside down is UNKNOWN from these files; the event name says the *reset* is the
"getting stuck" path.

### 1.2 The input — and this is where the lead gets sharpened (decoded)

`DrivingMode.SelectVehicleWeapon` (export 104971) contains, at script offset **315**:

```
final(0x1C)  RVehicleBatmobileBase.TryRightingFlip   TryRightingFlip(false, <0x4a>)
```

(`DRIVINGMODE.md:83`; `0x4a` = **74**, the same integer the same function passes to
`TriggerEventClass(RSeqEvent_BatmobileRiddlerButton, self, 0, 74)` at offset 432.)

`SelectVehicleWeapon` is what the B button runs:

```
DefaultInput.ini:268  XboxTypeS_B -> ... QuickGadgetB | OnRelease ReleaseQuickGadgetB ...
QuickGadgetB (export 105042, 9 script bytes) -> SelectVehicleWeapon(1)      [CONTROLS_CONSUMERS.md §2]
```

**But the same function is behind three more buttons** (`CONTROLS_CONSUMERS.md` §"Virtual-call
sites by name"):

| button | binding line | function | argument |
|---|---|---|---|
| B | `DefaultInput.ini:268` | `QuickGadgetB` → `SelectVehicleWeapon` | 1 (immobilizer slot) |
| X | `DefaultInput.ini:269` | `QuickGadgetX` → `SelectVehicleWeapon` | 2 (barrage) |
| Y | `DefaultInput.ini:270` | `QuickGadgetY` → `SelectVehicleWeapon` | 3 (drone virus) |
| D-Pad Up | `DefaultInput.ini:259` | `SelectVehicleWeapon 4` (direct) | 4 (missile pods) |

So the truth the operator felt: **any weapon-select tap also offers the car a righting flip.** B is
the one they happened to press while stuck. `TryRightingFlip(false, 74)` is a call *site* — whether
it is inside an `if` in that function is **UNKNOWN** (bytecode branches are not decoded;
`CONTROLS_CONSUMERS.md` UNKNOWN list).

There is **no keyboard binding** for any of it: the only keyboard `B` in the BmAK chain is
`SpawnPlayerCar` (cheat, `DefaultInput.ini:242`), and `QuickGadgetB`/`ReleaseQuickGadgetB` have no
key line (`CONTROLS.md` action table: keyboard = "none in chain").

### 1.3 The trigger conditions (decoded)

| quantity | value | source |
|---|---|---|
| tilted past this, a mode change is refused outright | up-axis `cos(theta) < **−0.707**` (>135° from upright) | `PAWNMESH_D8.md` §2, `comiss` at `0x140063f04` vs `0x141bf1cdc` |
| tilted past this, refused **unless** the flip timer has expired | `cos(theta) < **+0.707**` (>45°) while `BatmobileStuckTimeFlip < BatmobileStuckTime` | same, `0x140063f22` vs `0x141bce8f8` |
| the quantity measured | `Mesh.LocalToWorld.ZPlane.Z` = cos of the car's up axis against world up (`[mesh + 0xd8]`) | `PAWNMESH_D8.md` §1 |
| stuck timer | `BatmobileStuckTime` runtime at `0x1d18`; writers **UNKNOWN** | `CONTROLS_NATIVE2.md:109` |
| flip timer | `BatmobileStuckTimeFlip` runtime at `0x1d20`; class default **0.5 s** (offset 7456) | `CLASS_DEFAULTS.md:288` |
| stuck max | `BatmobileStuckTimeMax` class default **2.0 s** (offset 7452) | `CLASS_DEFAULTS.md:287` |
| speed condition | **none found** — the decoded gate reads tilt, the two timers, `TransformationAnimNode` (0x1494), `MatineeControlRefCount` (0x112c), two flag bytes (0x11d8/0x11dc) and `PreventModeSwitchDuration` (0x1990) | `PAWNMESH_D8.md` §2 |

Read the gate carefully: it is the **mode-change** gate, not the flip's own gate. It tells us what
the engine considers "too far over to transform" — 45° normally, 135° once the flip timer has run
out. It is the best decoded statement of BmAK's stuck posture, and it is why 0.707 / 135° are the
numbers this plan reuses.

### 1.4 Torque / impulse values

| member | archetypes | class default | label |
|---|---|---|---|
| `JumpRampRightingTorque` | **2000** x4 | 5000.0 | decoded (`MODES.md:159`, `CLASS_DEFAULTS.md:147`); units "engine torque" |
| `JumpNoRampRightingTorque` | **2000** x4 | 2500.0 | decoded (`MODES.md:160`) |
| `KillFlipTorque` | **−200** x3, **−400** (Joker) | −2,000,000.0 | decoded (`MODES.md:164`, `CLASS_DEFAULTS.md:270`) |
| `VehicleShovingTorque` | 10000 | 20000.0 | decoded |
| `PMDodgeTorque` | 6000 | 5000.0 | decoded |
| stuck-flip specific torque | — | — | **UNKNOWN**: no member names it. `SelfRightingMode` + `TryRightingFlip` + `ApplyRightingTorque` are the mechanism; their magnitudes are inside the native function |

Useful ratio (derived): the class defaults put a *kill*-flip at 2,000,000 against a *righting*
torque of 2,500–5,000, i.e. **400x–800x**; the shipped archetypes put −200 against 2000, i.e.
**0.1x**. The two columns disagree by three orders of magnitude, so **the archetype and class
columns are in different units or on different objects** — an honest gap, not a translation. No
conversion from "engine torque" to N·m exists in any file here (UNKNOWN).

### 1.5 HUD, animation and menu: the flip is not advertised (decoded absences)

| file | search | result |
|---|---|---|
| `HUD.md` | `flip\|stuck\|recover\|right`, case-insensitive | **0 hits** — no prompt, no "press B to recover" element |
| `ANIMATIONS.md` | same | **0 relevant hits** — the pose-state animation set is missiles, cannon reload, cockpit, jet boost, drift, strafe, aerofoils; **no flip or righting clip** |
| `CONTROLS_MENU_SCREENS.md` | same | **0 hits** — B is labelled `EMP` (battle) and `Tracker / Immobilizer` (pursuit); no flip row |

Two consequences. First, the righting is invisible by design: no clip means the flip is either
native IK/pose work or a snap (`ApplyRightingRoll` name fits a per-frame roll application). Second,
**BmAK's own controls screen does not document it**, which is why the operator found it by accident
and why no config line describes it.

---

## 2. Step 2 — the closest JC3 system, and the B conflict

### 2.1 What JC3 has (decoded)

| candidate | what it is | why it is not the righting | source |
|---|---|---|---|
| **`CHALLENGE_RESET_VEHICLE`** | a land-vehicle action, gamepad **`LPADDOWN`**, keyboard **`P`**; node hash `851F0D7A` in all four keymap layers | the **only** land-vehicle reset action JC3 has, and the closest single thing to the lead. Its consumer is not decoded, and its name scopes it to AR challenges (respawn at the challenge start), which is not "roll the car back over" | `INPUT.md:61`, `INPUT.json:6371`, `DRIVE_CARRIERS.md:182` |
| `CForcePulse` | radial impulse, **explosion-fired only** (0 of 23 tune paths name a collision) | a linear push from a blast, not a torque about the roll axis; wrong trigger | `G2-35.md` §2, `G2-17` |
| `arcade.turbo_jump.*` | fixed-axis punch: `punch_speed_kph` 50, `top_speed_kph` 200, `f_multiplier` 15, `r_multiplier` 12, `punch_delay_time` 0.1 s | along the car's own forward axis, on the jump action; a speed punch, not a rotation. A `turbo_jump.up_multiplier` (12..25, n=35) exists in the vocabulary with **UNKNOWN** consumer | `EJECT.md:198-203`, `VOCABULARY.md:361` |
| `drift.max_drift_torque` 5000 (0..35000), `constant_drift_torque` 0 (0..20000), `counter_steer_torque_handbrake` | continuous **yaw** torques | yaw, not roll; continuous, not a one-shot righting | `DRIVE_CARRIERS.md:118-119`, `VOCABULARY.md:467` |
| `arcade.nitro_boost.push_force` 15000 | linear push | wrong axis | `DRIVE_CARRIERS.md:296` |
| `rigid_body.unit_inertia_*` | inertia **distribution** only (4.0 / 2.6 / 1.2 built) | stores no torque, applies none | `keep-audit-suspension-and-mass.md` |

Two more JC3 names matter, and they are the only ones close enough to be worth quoting (decoded):

| member / class | value | what it actually is |
|---|---|---|
| `DriverLean.righting_torque` | **1500 .. 4000** (median **3000**, n = **23**) | a righting torque for the **driver's lean**, on the 23 aircraft-class vehicles (`VOCABULARY.md:566`, `DRIVE_CARRIERS.json:3882`); it has no consumer on a land vehicle and `G2X.md:115` records self-righting as a **named omission** for land vehicles (`HDL-6`) |
| `CInteractionGraphParentIsUpRightCondition` | **6,761** instances (`EJECT.json:1957`) | an **exit-graph condition** — JC3 already has a first-class "is the parent upright" predicate, used to gate exits (`EJECT.md:57-58`, `exit.ai.driver.default`). This is the one decoded JC3 **test** for uprightness |

So JC3 can *ask* whether a car is upright (`CInteractionGraphParentIsUpRightCondition`) and has one
member literally named `righting_torque` (for the rider, on aircraft). What it does **not** have is a
righting torque on a land vehicle: a case-insensitive scan of **every file in `Research/JC3Grab`** for
`righting|upright|overturn` matches **12 files**, and every match is either the `DriverLean` member
above, the up-right exit condition, or prose; for `antiroll|\bflip\b` the matches are the
`antirollbar_strength` vocabulary rows (0 on all 167 vehicles) and two prose sentences. No vehicle
module carries a righting or un-flip member — the same result three earlier cards reached from other
angles (`G2-35.md` §2: 0 members across five layers for the impulse family; `G2X.md` HDL-6).

### 2.2 Who owns B on the JC3 side (decoded)

| device | B | source |
|---|---|---|
| gamepad | `BTN_B` = `RPADRIGHT`, scope **UNKNOWN** — and `RPADRIGHT` is also `CANCEL`, `BYPASS_FALL_PREVENTION`, `GUI_CANCEL`, `PUSH_GRAPPLE`, `RELEASE_GRAPPLE`, `SKIP_CUTSCENE`, `MECH_JUMP`, `USE_VEHICLE_MOD`, `PLANE_TURN_RIGHT`, ... | `INPUT.md` action table |
| keyboard | `B` is bound **twice**: `VEHICLE_CAM` and `LOOK_BACK_CAM` | `INPUT.md` |
| inside the Batmobile in the build | **BmAK wins** (D-11): B = `QuickGadgetB` → `SelectVehicleWeapon(1)` = tracker/immobilizer (pursuit) / EMP (battle) | `GRAB_BACKLOG.md` D-11, `Working/Q/PILOT/CONTROLS.md` rows 12 and 15 |

There is **no free B**. That is exactly why BmAK's design is elegant and why this plan copies it:
because `TryRightingFlip` is called *from inside* the weapon-select function, the game needs no
extra binding — pressing B with the car upright fires the weapon, and the same call offers the flip
when the car is over. BmAK gets both behaviours from one button; the build should too.

**Conflict with the control-priority rule (D-11).** The rule says only ENTER is JC3's; everything
else inside the Batmobile is BmAK's. Under that rule B must stay `SelectVehicleWeapon(1)`, so:

- **do not** rebind B to a recovery action — that would delete the tracker/immobilizer (priority 1
  in `OPERATOR_PRIORITIES.md`).
- **do not** use JC3's `P` (`CHALLENGE_RESET_VEHICLE`) as the primary key: it is JC3's control, its
  consumer is undecoded, and it is a challenge respawn, not a righting.
- `P` is, however, the **free keyboard probe** for the Q test in §3.5 — no BmAK keyboard action
  claims it, and it costs nothing to try.

---

## 3. Step 3 — the build composition

### 3.1 Trigger (from decoded BmAK, no invention)

```
on SelectVehicleWeapon(n)                       # the B/X/Y/D-Pad-Up call already in the build
    up := |world_up · car_up|                   # 1 = upright, 0 = on its side
    if up <= 0.707:                             # >45 deg from vertical
        if up <= 0.707 and car_is_over_threshold_or_timer_elapsed:
            begin righting(roll_axis, target = up axis +world)
    else: nothing                               # upright -> the weapon fires, no flip
timers: stuck >= 0.5 s (BatmobileStuckTimeFlip) before a <45 deg recovery is allowed
        stuck >= 2.0 s (BatmobileStuckTimeMax) -> give up, send the reset event
```

`up <= 0.707` is BmAK's own 45°/135° pair: below 0.707 the car is "over", and below **−0.707**
(>135°, i.e. on its roof) the recovery is unconditional.

### 3.2 Torque, derived from the mass and inertia already decoded

Built values (`keep-audit-suspension-and-mass.md`, decoded from `bm-RC2`): mass **6000 kg**,
`unit_inertia_yaw/pitch/roll` **4.0 / 2.6 / 1.2**, `center_of_mass_bias` −0.3. Chassis box from
BmAK's own `Batmobile_Chassis`: extents **6.903 x 3.745 x 2.075 m** (`INERTIA.md` §2).

```
I_roll  (about x, length)  = 6000/12 * (3.745^2 + 2.075^2) = 500 * 18.331 =  9,165 kg m2
I_pitch (about y, width)   = 6000/12 * (6.903^2 + 2.075^2) = 500 * 51.958 = 25,979 kg m2
I_yaw   (about z)          = 6000/12 * (6.903^2 + 3.745^2) = 500 * 61.678 = 30,839 kg m2
```

Consistency check on the build's own multipliers (derived): `I_roll / 1.2 = 7,638`, and that scale
gives pitch 19,858 and yaw 30,551 — yaw matches the box tensor to **0.9 %** and pitch is 24 % low.
So the built distribution and the box tensor describe the same car, and **`I_roll = 9,165 kg·m²`**
is the number to use.

Righting torque for a constant-torque roll, starting and ending at rest, `theta = ½ alpha t²`:

| case | angle | T | alpha | torque = I_roll * alpha |
|---|---:|---:|---:|---:|
| on its roof | 180° (pi rad) | 0.5 s | 25.13 rad/s² | **230,300 N·m** |
| on its side | 90° (pi/2 rad) | 0.5 s | 12.57 rad/s² | **115,200 N·m** |
| roof, in the 2.0 s budget | 180° | 2.0 s | 1.57 rad/s² | 14,400 N·m |

**Recommendation: 0.23 MN·m about the roll axis for 0.5 s** (the `BatmobileStuckTimeFlip` timer),
applied as a continuous torque with the sign of the shortest rotation to world-up, and with the
roll rate zeroed when the up axis passes 0.985 (10° from vertical) so it does not overshoot.

Sanity against BmAK's own scale (derived, and the units are the weak link): BmAK's archetype
`KillFlipTorque` −200 against `JumpRampRightingTorque` 2000 means a *killing* flip is only a tenth
of a *righting* torque in those units, i.e. the fields do not share one scale — so **no numeric
bridge from "engine torque" to N·m is claimed here**. The 0.23 MN·m figure stands on the JC3
inertia and the BmAK 0.5 s timer alone.

Alternative worth trying before writing any hook (5-minute experiment, §3.5): if `rigid_body` /
the physics setters expose an angular-velocity write, a **single impulse** `J = I_roll * omega` with
`omega = 2*pi/0.5 = 12.6 rad/s` (= **115,000 N·m·s**) produces the same 180° in the same 0.5 s with
no per-frame torque, which is cheaper to implement and easier to cancel.

### 3.3 Which route carries it

| route | carrier | verdict |
|---|---|---|
| data (module member) | none — 0 righting members in 232 vehicles | **blocked**, decoded |
| action + data | `CHALLENGE_RESET_VEHICLE` (LPADDOWN / P) | **probe first**: if tapping P in vanilla JC3 rights a flipped car in free roam, the whole feature is a rebind. If it respawns at a challenge point, it is not |
| native hook (R17) | apply torque / angular velocity to the `rigid_body` on the existing `SelectVehicleWeapon` call | **the route that works**, and it mirrors BmAK exactly |

The R17 route has one large advantage: BmAK's own call site is inside `SelectVehicleWeapon`, so the
hook needs no new input, no new binding and no keymap change — it rides the button that already
exists, which is also what the "BmAK controls win inside the Batmobile" rule wants.

### 3.4 The pilot-card sentence

> **Press B (or X, Y, D-Pad Up) with the car on its roof, side or wedged:** the car rolls itself
> wheels-down in **≤ 0.5 s** and is driveable again in **≤ 2.0 s**; it must end with its up axis
> **≥ 0.985 of vertical (within 10°)** and must not be launched more than **0.5 m** into the air.
> With the car upright the same press must fire the equipped weapon and **not** right the car.

Pass band, and why each number is there:

| number | source | fails if |
|---|---|---|
| righting in ≤0.5 s | `BatmobileStuckTimeFlip` 0.5 s (decoded) | the car is still over at 0.5 s |
| fully recovered ≤2.0 s | `BatmobileStuckTimeMax` 2.0 s (decoded) | a second press is needed, or the reset event fired instead |
| end ≥0.985 (10°) | derived: 0.707 (45°) is BmAK's *"too far to transform"* line, so landing anywhere between 0.707 and 0.985 is a failed recovery | the car ends between 45° and 10° of level, or on the other side |
| no hop >0.5 m | derived: a roll about the contact patch lifts the roof by at most half the width (3.745/2 = 1.87 m); 0.5 m is the allowance for a non-teleporting roll | the car pops into the air like a `CForcePulse` |
| B with the car upright still fires | D-11 + `CONTROLS_CONSUMERS.md` §2 | the immobilizer stops working, i.e. the flip stole the button |

### 3.5 The two 5-minute experiments that come before any code

1. **`CHALLENGE_RESET_VEHICLE` probe.** In vanilla JC3 free roam, flip a car and tap `P`
   (keyboard) / `LPADDOWN`. If the car rights itself in place, the feature is a rebind of that
   action and nothing else is needed. If it teleports to a challenge start or does nothing, record
   it and go to R17.
2. **B-tap probe in BmAK** (read-only observation): stop the car upright and tap B — does the
   immobilizer fire and the car stay put? Then put it on its side and tap B — does it roll back?
   If yes, §1.2's call site is confirmed live and the build's trigger is exactly BmAK's.

---

## 4. Every open number, and the file that would settle it

| # | UNKNOWN | what would settle it |
|---|---|---|
| 1 | `SelfRightingMode`'s value and enum members | `BmGame.upk` bytecode reading/writing offset 5900, or a live read of `RVehicleBatmobileBase + 0x170C` (`BMSDK_OFFSETS.json`); the `.g.cs` declares the type, not the enum |
| 2 | `TryRightingFlip`'s body — does it no-op when upright? how much torque, over what time? | disassembly of the native function at its registered VA (`REGISTRATION.json:163`), read-only, same method as `PAWNMESH_D8.md` |
| 3 | the writers of `BatmobileStuckTime` (0x1d18) / `BatmobileStuckTimeFlip` (0x1d20) | an xref scan of `.text` for displacements `18 1d 00 00` / `20 1d 00 00`, the way `PAWNMESH_D8.md` §3 scanned `8c 03 00 00` |
| 4 | whether the `TryRightingFlip` call at offset 315 is conditional | the `SelectVehicleWeapon` bytecode walk with branches resolved (`DRIVINGMODE.md` records it as an unconditional row at 315) |
| 5 | whether the flip has a speed gate | the same bytecode walk, plus the `BatmobileStuckTime` writer |
| 6 | `CHALLENGE_RESET_VEHICLE`'s runtime effect on a flipped car | the in-game probe in §3.5, plus whichever module consumes the action (no entity names `keymap`; 0/232) |
| 7 | the N·m value behind "engine torque" | nothing in this tree — no unit conversion exists; it would need a BmAK take with a known inertia, which is itself UNKNOWN (`INERTIA.md` §6) |
| 8 | whether BmAK snaps or animates the flip | `ANIMATIONS.md` has no clip, so: a live capture of the B flip, counting frames |
| 9 | `turbo_jump.up_multiplier` (12..25, n=35) — does it lift the car? | its consumer is not decoded (`USAGES.md:566`: "which control fires any of them is in no file here") |

---

## 5. Checks run for this report

| # | check | result |
|---|---|---|
| 1 | case-insensitive scan of `Research/BatmobileGrab` for `self.?right\|self.?upright\|unflip\|flip.?recover\|righting\|unstick\|stuck` | 163 matches, all read at the places cited above |
| 2 | case-insensitive shell scan of every file in `Research/JC3Grab` for `righting\|upright\|overturn` | **12 files**, every match the `DriverLean.righting_torque` member, the `…ParentIsUpRightCondition` exit condition, or prose; no land-vehicle righting member. (A first-pass tool search reported 0 — it under-reported, so the shell scan is the authority here) |
| 3 | `HUD.md`, `ANIMATIONS.md`, `CONTROLS_MENU_SCREENS.md` for `flip\|stuck\|recover\|right` | 0 / 0 relevant / 0 |
| 4 | the B/X/Y/D-Pad-Up call chain | `DefaultInput.ini:268-270`, `:259` → `QuickGadget*` → `SelectVehicleWeapon` (decoded in `CONTROLS_CONSUMERS.md`) |
| 5 | the `TryRightingFlip` call site | `DRIVINGMODE.md:83`, offset 315, args `(false, 74)` |
| 6 | inertia arithmetic | 6,000 kg chassis box: 9,165 / 25,979 / 30,839 kg·m²; build multipliers imply 7,638 (yaw within 0.9 %) |
| 7 | torque arithmetic | 180° in 0.5 s → 25.13 rad/s² → **230,300 N·m**; 90° → 115,200 N·m; 180° in 2.0 s → 14,400 N·m |
| 8 | JC3 B ownership | `INPUT.md` (BTN_B = RPADRIGHT; keyboard B twice), D-11 (BmAK B = immobilizer) |

No game launched, no file outside `Research/` and `tmp/freebuff/reports/` written.
