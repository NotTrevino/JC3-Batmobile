# Stuck-flip and side-booster scrape (two operator leads, 2026-11-07)

Scraping only: no JC3 mapping, no build plan. Static reads of cooked packages; the game was never launched or attached to.

**Labels.** **decoded** = bytes read at the package, export and offset quoted. **derived** = a stated rule over decoded bytes. **UNKNOWN** = no field, body or asset found here, with the search that would settle it.

**Sources.** `BmGame.upk` (class default objects and script bodies, export numbers below), `Startup.upk` (shipped Batmobile simulation object), `Playable_Batmobile_SF.upk` (shipped playable archetypes and effects), `BmGame/Config/DefaultInput.ini` (bindings), plus the existing records under `Research/BatmobileGrab/` (`BMSDK_OFFSETS.json` for layout, `MODES.md` and `CLASS_DEFAULTS.md` for the serialised values, `BINDINGS_MERGED.json`/`CONTROLS.md` for the input table, `CHAIN.json` for field→object references).

**Two of the documents the task named do not exist.** `reports/stuck-flip-recovery-plan.md` is not on disk (`ls reports/ | grep -i "stuck\|flip\|recover"` returns nothing), and there is no `reports/` directory in the repository at the start of this pass. So the plan's two claims cannot be checked against the plan itself; they are checked against the data instead, in §2.6 and §1.1, and both happen to be confirmed independently. `Research/BatmobileGrab/ANIMATIONS.md` and `HUD.md` exist and were consulted (§1.5, §1.2).

---

## 1. Lead 1 — "the gamepad B button flips the Batmobile upright when it is stuck"

**Verdict in one line:** the righting action exists and is real, and it is even reachable from the weapon-select path, but **nothing binds it to B** — the B command list contains no flip, righting or unstick token, while A carries the strafe token that lead 2 is about. The flip is most likely *automatic* on the stuck timer, not a button.

### 1.1 The action exists — `TryRightingFlip` (decoded)

| item | evidence |
|---|---|
| `RVehicleBatmobileBase.TryRightingFlip(ForceFlip, AwayFromPoint)` | `BmGame.upk` export **10572**, 2 params + return, 11 script bytes = `0x29` param descriptors only, **no `EX_FinalFunction`** into any helper → the body is **native** |
| `RVehicleBatmobileBase.FlipVehicle(bool bInstant)` | export **10596**, 122 script bytes, also native-shaped (no calls out) |
| `RCheatManager.FlipBatmobile()` | export **64399**, 309 script bytes — the console/cheat twin, so a flip is reachable from `ce` without any binding |
| `RVehicleBatmobileBase.SelfRightingMode` | `ByteProperty` at layout offset **5900** (`BMSDK_OFFSETS.json`); the class default object `BmGame.Default__RVehicleBatmobileBase` (export **10923**) carries **no tag at 5900**, so the shipped value is the class-default 0 — the enum's member *names* are not in the package name table (no `ESelfRightingMode` export), so "0" is decoded but its meaning is UNKNOWN |
| `RVehicle.ApplyRightingTorque` / `ApplyRightingRoll` | exports **1711** / **1714**, 48 script bytes each, native |
| `RVehicle.IsUprightForSelfDrive` | export **10510**, 88 script bytes with one float const **0.5** → an upright test against a 0.5 threshold, i.e. an up-vector dot product. **derived** |
| `RB_StayUprightSetup` component | present on the vehicle as `MyStayUprightSetup`; `SVehicle` CDO has `bCanFlip=True` (`CLASS_DEFAULTS.md:344`) — the physics-side anti-roll, **decoded** as a shipped tag |

**Who calls it (decoded, and it is not an input handler).** `RPlayerController.DrivingMode.SelectVehicleWeapon` (export **104978**, 448 script bytes) calls `TryRightingFlip` at script offset **315**, sitting *between* two `RVehicleWeapon.TryToFireWeapon` calls at 278 and 402 (offset alignment `0x1C`). That is the weapon-select function, exactly as the missing plan reportedly found: the righting attempt is embedded in the same function that resolves "which weapon does this button fire", i.e. it is tried as a *fallback* when weapon selection runs and there is nothing to shoot. **This confirms the plan's first claim from the data**, and it also explains why the flip feels like a button: it fires on the same press path, but from the weapon function, not from a dedicated binding.

### 1.2 The binding — B does not carry it (decoded)

`BmGame/Config/DefaultInput.ini`:

- `:268` `XboxTypeS_B` → `ExitAgilityMode | QuickGadgetB | OnRelease ReleaseQuickGadgetB | Cover | BlockBreaker | SkipCutscene | CancelGadget | DebugMenuSelectB | CancelBatarangCamera | Button bCancelButton`
- `:267` `XboxTypeS_A` → `DebugCamSingleFrameStep | EjectFromVehicle | BattleStrafe | ContextSensitive | Run | CapeGlide | AcceptConversation | Evade | DebugMenuSelectA | CancelBatarangCamera | TriggerPhysImpact`

No token in **any** binding matches flip/upright/selfright/unstick/recover (`BINDINGS_MERGED.json`, all 176 alias rows walked; 0 hits). Also **decoded as absent**: `RVehicleBatmobileBase` is never a `DrivingMode` input receiver for a flip command — the DrivingMode handlers are `BattleStrafe`, `DelayedBattleStrafe`, `CheckBattleStrafe`, `PursuitStrafe*`, `SelectVehicleWeapon`, `TryToChangeMode`.

What B *does* do on the Batmobile: `ExitAgilityMode` (leave battle mode / agility stance) and `QuickGadgetB`. Both are mode transitions, and `ExitAgilityMode` in battle mode is the plausible origin of the "B puts the car right" impression — it drops the agility stance, which restores the car's attitude while it is in the low stance.

Two prompt-side names exist in the name table, which is the only trace of a player-facing flip affordance:

- `CI_FlipBatmobile` — a GFx/movie-clip icon name. **decoded as a name; its user is UNKNOWN.**
- `VGS_StrafeButton` — "vehicle gadget strafe button", the strafe prompt icon (see §2).

`Research/BatmobileGrab/HUD.md` carries no row for either icon name, so the prompt that shows them is UNKNOWN.

### 1.3 Trigger conditions

| condition | value | evidence | status |
|---|---|---|---|
| stuck timer that enables the flip | `BatmobileStuckTimeFlip = 0.5` s | `BmGame.Default__RVehicleBatmobileBase` (export 10923), offset **7456**, decoded float | **decoded** |
| stuck timer cap | `BatmobileStuckTimeMax = 2.0` s | same CDO, offset **7452** | **decoded** |
| running stuck accumulator | `BatmobileStuckTime` | layout offset 7448; **no tag** in the CDO or in any of the 4 shipped archetypes (`MODES.md:180` lists the 23 unshipped fields; `BatmobileStuckTime` is not among them, so it is initialised in native code) | **UNKNOWN** |
| flip attempt budget | `NumFlipTries` | layout offset 7460; **no tag** in CDO or archetypes | **UNKNOWN** (count only; no shipped number) |
| roll angle that counts as stuck | — | no field implements it. `ImpactRoadAssistMaxAngle` and `BattleModeStopAndTurnAngle*` are turn/assist angles, not a roll threshold | **UNKNOWN** |
| speed gate | — | none found at the Batmobile level | **UNKNOWN** |
| upright test threshold | 0.5 | `RVehicle.IsUprightForSelfDrive` const | **derived** |

`BatmobileStuckTimeMax` 2.0 / `BatmobileStuckTimeFlip` 0.5 read as a **derived** rule: the car is treated as stuck after 0.5 s of no progress and the flip is the last resort by 2.0 s. Nothing in the corpus states which of the two gates `TryRightingFlip` reads — both are floats on the same class, both are native consumers.

### 1.4 Torque and impulse values

| field | offset | CDO | V2 | MK2 | Joker | Funhouse | status |
|---|---:|---:|---:|---:|---:|---:|---|
| `KillFlipTorque` | 7192 | **-2000000** | -200 | -200 | -400 | -200 | **decoded** (`MODES.md:164`) |
| `KillFlipTorqueDuration` | 7196 | 1.5 s | 0.5 | 0.5 | 0.75 | 0.5 | **decoded** (`MODES.md:165`) |
| `JumpRampRightingTorque` | 6756 | no tag | 2000 | 2000 | 2000 | 2000 | **decoded** (`MODES.md:159`) |
| `JumpNoRampRightingTorque` | 6760 | no tag | 2000 | 2000 | 2000 | 2000 | **decoded** (`MODES.md:160`) |
| `SelfRightingMode` | 5900 | no tag (=0) | — | — | — | — | **decoded carrier, meaning UNKNOWN** |

The archetype values are what run; the CDO's -2,000,000 is a placeholder that no shipped playable Batmobile uses. `KillFlipTorque` is the *enemy-kill* flip (drive into a car and it rolls), torque **-200 / -400** for 0.5–0.75 s — not the self-right, and the naming is the trap here: `KillFlip*` is offensive, `Jump*RightingTorque` is the recovery pair.

**The self-right's own torque is UNKNOWN.** `TryRightingFlip` is native, its 11 script bytes hold no constants, and the two candidate carriers are `Jump*RightingTorque` (2000, the airborne righting) and `SelfRightingMode`. `reports/emp-effects-scrape-leads.md` shows the same pattern for the EMP: a 5-row tag set on the archetype and the numbers living in the native class default.

### 1.5 Animation and effect

- **Flip animation: UNKNOWN.** No `*Flip*` animation name exists in the vehicle animation sets. `FlipAnimName`, `bPlayingFlipAnimation` and `bAllowFlipAnimation` in the corpus belong to **`RBatarangCamera`** (the camera roll), not to the vehicle — a same-name trap. The vehicle side supplies only the pose sets (`Batmobile_V2_Pose_States`, with `Spin`/`Fans_Spin`) and the transformation nodes, and `TransformationAnimNode` is one of the 23 unshipped fields (`MODES.md:180`).
- **Flip sound:** `Play_Batmobile_Rotation` (AkEvent) exists and is the only rotation-tagged vehicle event; **derived** candidate, not proven to be the righting cue.
- **Flip effect:** none. Nothing in the Batmobile's effect field set (`SideExhaust*`, `ChargeParticle`, `FireParticle`, impact FX) names a righting or dust burst.
- **Hydra reset events (decoded names, 0-byte stubs):** `SendHydraEventBatmobileResetByGettingStuck`, `SendHydraEventBatmobileResetByFalling`, `SendHydraEventBatmobileResetByGettingCrushed`, `SendHydraEventBatmobileResetByBlowingUp`. This is the plan's "separate Hydra reset event", confirmed: the *destructive* recovery (teleport the car back to a road) is a distinct Hydra/AI-tracked path keyed on **why** the car was lost, and "ByGettingStuck" is its own reason code. So there are two recoveries — a local torque flip (§1.4) and a Hydra reset (§1.5) — and the lead conflates them.

---

## 2. Lead 2 — "left stick plus A fires side boosters; the flip uses the same booster"

**Verdict in one line:** the input combination is **decoded** and exact, the side-booster *effect objects* are **decoded**, but the thrust numbers the shipped car actually uses split into two separate paths (pursuit dodge vs battle dodge), four core `Strafe*` fields are **not serialised anywhere**, and there is **no evidence the flip calls the booster** — the flip and the dodge are different mechanisms that happen to share the A-press path.

### 2.1 The input combination (decoded, exact)

| key | binding line | command token | role |
|---|---|---|---|
| `XboxTypeS_LeftX` | `DefaultInput.ini:263` | `Axis aStrafe DeadZone=0.3` (+ `aRawLHJoyRight`) | lateral axis |
| `XboxTypeS_LeftY` | `DefaultInput.ini:264` | `Axis aBaseY DeadZone=0.3` (+ `aRawLHJoyUp`) | forward axis |
| `XboxTypeS_A` | `DefaultInput.ini:267` | **`BattleStrafe`** | fires the burst, direction taken from the stick |

So "left stick + A" is decoded as **`aStrafe`/`aBaseY` held plus the `BattleStrafe` command**, which is precisely the operator's description. The A list also holds `ContextSensitive | Run | CapeGlide | Evade | …`; on foot those win, in the Batmobile `BattleStrafe` is the live consumer (see 2.2 for the guard).

### 2.2 The handler chain and its literals (decoded bodies, derived argument mapping)

| body | export | script bytes | float/int constants found in the body |
|---|---:|---:|---|
| `RPlayerController.DrivingMode.BattleStrafe` | 104980 | 132 | 0.2, 0.3333 |
| `RPlayerController.DrivingMode.DelayedBattleStrafe` | 104981 | 134 | 0.3333 |
| `RPlayerController.DrivingMode.CheckBattleStrafe` | 104998 | 875 | 0.7, 0.5, -0.5, 0.9, int 16384 |
| `RVehicleBatmobileBase.BattleMode.BattleDodge` | 10544 | 896 | 2500.0, 0.25, 0.75, ±0.707, 0.2 |
| `RVehicleBatmobileBase.VehicleStrafe` | 10581 | 478 | 1200, 2500, 800, 0.7, 0.5, 0.25, -0.1 |
| `RVehicleBatmobileBase.KickStrafe(Force, Torque, Duration)` | 10143 | 53 | none — 3 param descriptors, **native** |
| `RVehicleBatmobileBase.PursuitMode.BattleDodge` | 10519 | 90 | 0.5 |

**derived:** the chain is `BattleStrafe` → (`DelayedBattleStrafe` | `CheckBattleStrafe`, the 0.7/0.9 pair reading as a dot-product gate on the stick direction with 16384 = 90° for the left/right sector test) → `BattleMode.BattleDodge` → `VehicleStrafe` → `KickStrafe(force, torque, duration)`. The literals in `VehicleStrafe` — **1200**, **2500**, **0.25** — are the strongest candidates for that triple, with 800 and 0.7/0.5 reading as a speed scale and blend factors, and -0.1 as a small brake. This is *derived*, not decoded: the constants sit in the same body as the `KickStrafe` call and three of them match its three parameters, but operand order is not proven without a decompile.

`KickStrafe` being native is the hard stop: even with perfect constants, the engine-side application of that force/torque is not in the package.

### 2.3 The side-booster object (decoded)

`RVehicleBatmobileBase` holds two effect fields, and both resolve to real particles in the shipped playable package:

| field | CHAIN reference | resolved object | class |
|---|---|---|---|
| `SideExhaustBurstEffect` | `Playable_Batmobile_SF` export **4971** | **`Exhaust.SideExhaust_Burst`** | `ParticleSystem`, 189 B |
| `SideExhaustBoostEffect` | `Playable_Batmobile_SF` export **4970** | **`Exhaust.SideExhaust_Boost`** | `ParticleSystem`, 197 B |

Both are `Exhaust.*` particles, sibling to `Exhaust.batmobileExhaust_burst` (4969) — i.e. the "side boosters" are **lateral exhaust plumes**, one burst (the dodge) and one boost (sustained). That is the object to hook. `Exhaust.SideExhaust_Boost` is the same-named trap as `RBatmobileBooster`, which is the **afterburner gadget** (T-B1), not this.

**Sound:** `Play_Batmobile_Dodge` AkEvent exists (name-table decoded) and is the natural pairing; which of the two FX it plays with is UNKNOWN.

### 2.4 Thrust values, duration and cooldown

| quantity | value | source | status |
|---|---|---|---|
| pursuit dodge torque | **6000** | `PMDodgeTorque`, 0x1fdc, V2/MK2/Funhouse (`MODES.md:176`) | **decoded** |
| pursuit dodge force | **10000** | `PMDodgeForce`, 0x1fe0, same 3 packages (`MODES.md:177`) | **decoded** |
| pursuit dodge duration | **0.15 s** | `PMDodgeDuration`, 0x1fe4 (`MODES.md:178`) | **decoded** |
| battle dodge impulse | **150000** | `BattleDodgeImpulse`, 0x1914, 3 of 4 packages (`MODES.md:152`); CDO 100000 | **decoded** |
| dodge cooldown | **0.75 s** | `StrafeCooldown`, 0x11e4, CDO only | **decoded carrier; no archetype tag → class default runs** |
| forward correction during strafe | **3000** | `StrafeFwdCorrectionForce`, 0x1208, CDO only | **decoded carrier** |
| `StrafeForce` / `StrafeTorque` / `StrafeDuration` / `StrafeTime` | **none** | 0x11f8 / 0x11fc / 0x1200 / 0x1204 — **not serialised in any shipped archetype and no CDO tag** (`MODES.md:180`) | **UNKNOWN** |
| second-dodge upgrade | `bDoubleDodgeUpgrade=True` (bit 2048 of the shared 4576 word) | CDO | **decoded** |

That last row is the important negative: the four fields that *look* like the strafe's force/torque/duration/time are empty in every shipped object, which is why the numbers in §2.2's `VehicleStrafe` body are the only place the battle strafe's magnitude appears at all. The class declares them, nothing cooks them, so the defaults live in native constructor code — same shape as `BatmobileStuckTime` in §1.3. `PMDodge*` and `BattleDodgeImpulse`, by contrast, **are** serialised, so the pursuit dodge's physics is fully known and the battle dodge's is not.

### 2.5 Which modes and which paths (decoded)

- **Pursuit:** `bAllowPMDodge=True` (CDO) gates an `RVehicleBatmobileBase.PursuitMode.BattleDodge` body (export 10519, 90 B, const 0.5) that uses the serialised `PMDodgeTorque/Force/Duration`. Also `PursuitStrafe`/`PursuitStrafeOn` handlers exist on `DrivingMode`. So pursuit has its **own** dodge, force-based, 0.15 s.
- **Battle:** `BattleMode.BattleDodge` (export 10544) with `BattleDodgeImpulse` 150000 — an impulse, not a sustained force, which is why battle mode "pops" sideways and pursuit mode "slides".
- **Mode gate:** the `SetDriveMode` pair recorded in `DRIVE_MODES.md` §2 (`BMDM_Drive` = 0 for `PursuitMode.BeginState`, `BMDM_BattleMode` = 2 for `BattleMode.BeginState`) means each mode owns its own `BattleDodge` override — the two paths are selected by drive mode, not by a bool.
- So the lead is **decoded as correct in both modes but not as one mechanism**: A + stick strafes in both, through two different tuning sets.

### 2.6 Does the flip call the same booster? — no evidence, and structurally unlikely

| check | result |
|---|---|
| `TryRightingFlip` (10572) calls `KickStrafe`, `VehicleStrafe`, `BattleDodge` or `SideExhaust*` | **No.** 11 script bytes, param descriptors only, no `EX_FinalFunction` |
| `FlipVehicle` (10596) calls the strafe path | **No.** 122 bytes, no recognisable call out (native-shaped) |
| `FlipVehicle`'s actual mechanism | `AddTorqueOverTime` + `AddKeepyUpForce`, literals **1000.0** and **2.0** — a torque-over-time and a lift force, **derived** from the body's call/const layout |
| shared field set | the flip reads `Jump*RightingTorque`/`SelfRightingMode`/`KillFlip*`; the strafe reads `Strafe*`/`PMDodge*`/`BattleDodgeImpulse` — **disjoint** |
| shared effect | the flip's effect is UNKNOWN (§1.5); the strafe's is `Exhaust.SideExhaust_Burst` |

**derived conclusion:** the flip and the side boost are **separate physics actions with disjoint tuning**, reached from different functions. What they share is the *press* — A runs `BattleStrafe` and B runs `ExitAgilityMode`, and `SelectVehicleWeapon` (the weapon function) tries `TryRightingFlip` as a fallback. So "the vehicle flip uses the same booster" is **UNKNOWN in the engine sense** (both are native, so a shared internal kick is not excluded) and **unsupported by every script-level symbol**: no cross-reference exists anywhere in the corpus from a flip body to a strafe body or to `SideExhaust*`. A shared visual (a puff of exhaust when the car rights itself) cannot be ruled out and would need the runtime.

---

## 3. Summary table

| lead | claim | evidence file, offset or object | status | search that settles it |
|---|---|---|---|---|
| 1 | A self-right/flip action exists | `BmGame.upk` export 10572 `RVehicleBatmobileBase.TryRightingFlip`; 10596 `FlipVehicle`; 64399 `RCheatManager.FlipBatmobile` | **decoded** | — |
| 1 | B is bound to it | `DefaultInput.ini:268` B command list (no flip token); `BINDINGS_MERGED.json` 176 rows, 0 flip hits | **decoded (negative)** | a UE `-dumpconsole`/`ce <binding>` sweep, or `PCOwner.PlayerInput` binding dump at runtime |
| 1 | What B actually does | `ExitAgilityMode`, `QuickGadgetB` on `DefaultInput.ini:268`; `ExitAgilityMode` is the battle-mode exit | **decoded token, derived effect** | runtime: press B in battle mode on a stuck car and log `DriveMode` |
| 1 | Flip is invoked from weapon select | export 104978 `DrivingMode.SelectVehicleWeapon`, `EX_FinalFunction` to 10572 at script byte 315, between two `TryToFireWeapon` at 278/402 | **decoded** | — |
| 1 | Trigger: stuck time | CDO export 10923, off **7456** `BatmobileStuckTimeFlip = 0.5`; off **7452** `BatmobileStuckTimeMax = 2.0` | **decoded** | which of the two `TryRightingFlip` reads: decompile 10572 in IDA with the BmGame PDB |
| 1 | Trigger: `BatmobileStuckTime` running value / `NumFlipTries` | layout 7448 / 7460; no tag in CDO or 4 archetypes (bit 0x… of shared words only) | **UNKNOWN** | engine default constructor in IDA, or a live property dump |
| 1 | Trigger: roll angle, speed gate | no such field; `ImpactRoadAssistMaxAngle` is an assist angle | **UNKNOWN** | a runtime watch of `Rotation.Roll` at the flip with a hook on 10572 |
| 1 | Torque values | `KillFlipTorque` 7192 (-200/-400, 0.5–0.75 s), `JumpRampRightingTorque` 6756 = 2000, `JumpNoRampRightingTorque` 6760 = 2000 (`MODES.md:159-165`) | **decoded** for the fields; **UNKNOWN** which one the self-right uses | native 10572/1711/1714 in IDA |
| 1 | Righting animation | no vehicle `*Flip*` anim; `FlipAnimName`/`bPlayingFlipAnimation` are `RBatarangCamera` | **decoded (negative)** | `ANIMATIONS.md` + `Batmobile_V2_Pose_States` per-clip inspection, in-engine anim tree dump |
| 1 | Righting effect | none; nearest is `Play_Batmobile_Rotation` AkEvent | **UNKNOWN** | runtime VFX log at the flip |
| 1 | Separate Hydra reset exists | `SendHydraEventBatmobileResetByGettingStuck/_ByFalling/_ByGettingCrushed/_ByBlowingUp` (0-byte stubs) | **decoded names** | `CHAIN.json` follow of the `SendHydraEvent` family |
| 2 | Left stick + A is the strafe input | `DefaultInput.ini:263` `XboxTypeS_LeftX→aStrafe`, `:264` `LeftY→aBaseY`, `:267` `XboxTypeS_A→BattleStrafe` | **decoded** | — |
| 2 | Handler chain | exports 104980/104981/104998 → 10544 → 10581 → 10143 `KickStrafe`, with literals 0.2/0.3333/0.7/0.5/-0.5/0.9/16384, 2500/0.25/0.75/±0.707/0.2, 1200/2500/800/0.7/0.5/0.25/-0.1 | **decoded bodies, derived argument order** | decompile 10581 to bind 1200/2500/0.25 to `KickStrafe`'s three params |
| 2 | Side-booster object | `SideExhaustBurstEffect` → **`Exhaust.SideExhaust_Burst`** (Playable_Batmobile_SF exp 4971); `SideExhaustBoostEffect` → **`Exhaust.SideExhaust_Boost`** (exp 4970) | **decoded** | — |
| 2 | Thrust/duration/cooldown | `PMDodgeTorque` 6000 / `PMDodgeForce` 10000 / `PMDodgeDuration` 0.15 (archetypes); `BattleDodgeImpulse` 150000; `StrafeCooldown` 0.75, `StrafeFwdCorrectionForce` 3000 (CDO only) | **decoded** | — |
| 2 | Battle-strafe force/torque/duration | `StrafeForce` 0x11f8, `StrafeTorque` 0x11fc, `StrafeDuration` 0x1200, `StrafeTime` 0x1204 — **not serialised anywhere** (`MODES.md:180`) | **UNKNOWN** | native `RVehicleBatmobileBase` constructor defaults in IDA, or a live property dump of a spawned car |
| 2 | Enabled in both modes | `bAllowPMDodge=True` (CDO) + `PursuitMode.BattleDodge` (10519) vs `BattleMode.BattleDodge` (10544); mode chosen by `DriveMode` (`DRIVE_MODES.md` §2) | **decoded** | — |
| 2 | Flip uses the same booster | no cross-reference from 10572/10596 to `KickStrafe`/`VehicleStrafe`/`BattleDodge`/`SideExhaust*`; `FlipVehicle` uses `AddTorqueOverTime`+`AddKeepyUpForce` (1000.0, 2.0); field sets disjoint | **derived: no; engine-internal share UNKNOWN** | runtime: hook 10572 and watch for a `KickStrafe` call / an `Exhaust.SideExhaust_*` emitter spawn |

---

## 4. Checks run and limitations

- `BmGame.upk` class default object 10923 (`Default__RVehicleBatmobileBase`) re-walked with `upk_read.walk_tags`: tags read at 7452/7456 (2.0, 0.5), 4580 (0.75), 4616 (3000), 6420 (100000), 8156/8160/8164 (5000/6000/0.25), 7192/7196 (-2000000, 1.5), 4576 (word 2048 = both `bAllowPMDodge` and `bDoubleDodgeUpgrade` True). Absent at 5900, 7448, 7460, 4600, 4604, 4608, 4612, 6756, 6760 — recorded as absence, not as zero.
- `Playable_Batmobile_SF.upk` exports 4969–4972 resolved by name, class and full path (the two side-exhaust particles above).
- Existing records reused rather than re-derived: `MODES.md` (archetype values for the flip/dodge fields), `CLASS_DEFAULTS.md` (CDO values), `BMSDK_OFFSETS.json` (layout offsets and kinds), `BINDINGS_MERGED.json`/`CONTROLS.md` (the input table), `CHAIN.json` (field→object refs), `DRIVE_MODES.md` (mode selection).
- **Not checked, and why:** no decompiler run (no IDA in the loop), so every "native" row above is an *absence of script* finding — a 53-byte or 11-byte script with no `EX_FinalFunction` — rather than a read of native code. That is what forces the UNKNOWNs at `KickStrafe`'s application, `TryRightingFlip`'s torque source, and the unshipped `Strafe*`/`BatmobileStuckTime`/`NumFlipTries` defaults.
- **Two named inputs missing:** `reports/stuck-flip-recovery-plan.md` does not exist in the repository, so its claims are re-derived here from the data (§1.1 confirms the weapon-select righting call; §1.5 confirms the Hydra reset family). `Research/BatmobileGrab/ANIMATIONS.md` and `HUD.md` were read for the flip animation and the prompt icon and contain no vehicle flip clip and no `CI_FlipBatmobile`/`VGS_StrafeButton` row — recorded as gaps in those records, not as proof of absence in the game.
