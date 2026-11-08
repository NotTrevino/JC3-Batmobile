STATUS: done

# Entry, exit and in-car controls — BmAK vs JC3, member by member

Card: `tmp/freebuff/running/L3__8722-entry-exit-and-controls-plan.txt` (hand-written 2026-11-06).
Scope: the **driver entry sequence**, the **exit sequence**, the **Y-to-enter / LB-to-exit control
priority inside the Batmobile**, and the **BmAK pad scheme** (steer, drift, boost, weapons, gadget
wheel). Rule applied: `STAGES.md` closest-system rule — every gap gets a build action, no row is
written as "JC3 has no system" and no limit is accepted. No game launch, no install, no edit to
`GRAB_BACKLOG.md`, the pinned ledger (`Working/Translation/T_ROWS.jsonl`) or the tracker.

Labels used throughout: **decoded** = read from a file/bytes (path + offset or line given);
**derived** = computed here from decoded facts with the rule stated; **UNKNOWN** = not decodable
here, with the file/probe that settles it and one pilot-card check with a pass band.

---

## 0. The answer in eight lines

1. **BmAK has no enter binding.** Its ini chain carries no enter token at all; entry is a
   **scripted special move** chosen from **12** `GetIn*Move` members on `RVehicleBatmobile`
   (class offsets 8352–8520), and the canopy plays a **0.433 s / 14-frame / 23-track** animation
   (`BM_Batmobile_Chassis.Cockpit_Open`, bone `canopy`). So "enter with JC3's Y" costs BmAK nothing
   and is *the only* correct reading of the Y row — **decoded, not a compromise**.
2. **BmAK's exit is a command token with no key.** `ExitVehicle` is an alias at
   `DefaultInput.ini:178` that **no key line references**; the menu's `LB` row resolves to
   `DualPlay` (`:271`) → `DualPlayPressed` (17 bytes, no exit call). `ExitVehiclePressed` is not
   even in `BmGame.upk`'s name table. The ini cannot express LB-exit; a script route must
   (`CONTROLS_CONSUMERS.md` §4, already reported — cited, not re-derived).
3. **Inside the car, Y is the afterburner** (`bVehicleBoostButton`, `DefaultInput.ini:270`) and
   **LB is exit**. Those two facts plus JC3's shipped table (which puts `ENTER_VEHICLE` **and**
   `EXIT_VEHICLE` on **one** control, `RPADUP`, and binds **no face button at all**) give an exact
   priority resolution: **split JC3's shared enter/exit pair**, `Y → ENTER_VEHICLE` only,
   `LSHOULDER → EXIT_VEHICLE` only, and `Y → USE_VEHICLE_MOD` as the in-car boost. Context, not
   precedence, separates Y's two jobs.
4. The **closest JC3 carrier for entry/exit** is the donor's own interaction graph:
   `point.driver` (id `93F2612B=FFFF52D5`, translation **−0.440, 0.340, 0.200 m**),
   `entry.driver` → `S_ENTER_DRIVER_VEHICLE`, `exit.driver.default` → `S_EXIT_VEHICLE`,
   `exit.driver.moving.parachute` → `S_EXIT_VEHICLE_PARA` gated **(5.0, 999.0)**, and
   `set.node.npc.state = S_IDLE_DRIVER_VEHICLE` on that node — all **decoded** in the cooked `.epe`,
   already reviewed (`review-JC3-SEAT.md`, cited).
5. The **canopy** is the one genuinely new carrier this card adds: JC3 has no event-driven canopy
   timeline, so the gap is closed by **composing** (a) a hinged part on the canopy bone and
   (b) the occupant-count condition the donor graph already carries (`entry.driver` `min` 0,
   `max` 3, `check` 0) as the trigger source. Carrier files and members are named in §6.4/§7.
6. **Steering, drift and boost have exact JC3 tune members** (`LandSteering.steer_angle_*`,
   `CustomLandGlobal.drift.*` 20 members with the fleet defaults 10 km/h / 5000 / 4 / 45° / 30000,
   `arcade.nitro_boost` on 145/232 builds) — the gap in every case is **BmAK's numbers**, not the
   carrier (`DRIVE_CARRIERS.md` rows C1/C8/C9, cited).
7. **Weapons map onto BmAK's own slot model**, not onto a mode flag: `SelectVehicleWeapon(1..4)` on
   B/E/X/D-Pad-Up (decoded, 10-byte handler bodies) is the same shape as JC3's entity weapon slots
   (`main_weapon` `851CAABE`, `secondary` `00568A74`, two shipped-null slots) selected by
   `USE_VEHICLE_MOD`.
8. Six things stay **UNKNOWN**, each with its settling file/probe and a pilot band (§8). None of
   them is allowed to become a "JC3 can't" row.

---

## 1. Existing coverage — cited, not repeated

Read this table before writing anything on this topic. The "delta" column is what this card adds;
everything else is somebody else's card and must be quoted with its own label, not re-derived here.

### 1.1 `tmp/freebuff/reports/`

| report | covers | delta owned here |
|---|---|---|
| `pilot-controls-reference.md` | the 24-row master control table, conflicts A–H, each with its settling file | **sequence** (entry→cockpit→seat→exit as ordered steps with numbers) and the **priority order** as a rule, not as 24 independent rows |
| `CONTROLS-0xd8.md` | `[Pawn.Mesh+0xd8]` = `LocalToWorld.ZPlane.Z` = cos(tilt); the mode-change gate at ±0.707 | used only as the decode of the gate constant |
| `INPUT-d11.md` | battle-mode toggle / immobilizer / eject carry **0** action ids and **0** name hashes in 134 vehicle modules | the positive half: which JC3 action *does* carry them (`USE_VEHICLE_MOD`, `ENTER/EXIT_VEHICLE`) |
| `review-JC3-SEAT.md` | `point.driver` owns the transform; `CInteractionGraph.modifier` = `MOD_LOW` selects `car/low` | the canopy/sequence half of entry, which that review explicitly left out |
| `review-JC3-EJECT.md` | engine carries `ACT_EJECT_FROM_VEHICLE`/`S_EJECT_FROM_VEHICLE_*` but no graph authors it; 17 hash members per exit | the build action that authors one |
| `DRIVERLEFT-regions.md` | regions of `RVehicleBatmobile.DriverLeft` (binds swap, wheelspin) | not re-walked here |
| `keep-audit-steering-and-drift.md`, `steering-st7-apply.md`, `steering-wheel-p13.md` | JC3 steering/drift rows already applied and audited | — |
| `air-control-closest-system-plan.md` | the air-control composition (`Aerodynamics.aerodynamic_surfaces[]`) | — |
| `mode-switch-carriers.md`, `apply-riot-mode-rows.md`, `modes-hud-evidence.md` | battle↔pursuit carriers | mode split is **their** card; §6 quotes only the control consequence |
| `winch-and-tether.md`, `unranked-weapons-closest-system.md`, `GADGET-params.md`, `lock-hold-salvo-closest-system-plan.md` | gadget wheel, winch, salvo carriers | — |
| `G3-HUD-CLUSTER.md`, `hud-radar-bmak-values.md`, `review-hud-cluster-elements.md` | HUD elements and BmAK HUD values | — |
| `nitro-boost-values.md`, `boost-rows-proposal.md` | `nitro_boost` members and proposed rows | — |
| `physicsc-hinges.md`, `JC3-door-angles.md`, `JC3-stations-hinges.md`, `parts-manifest-joints-v2.md` | hinge/constraint rows on the fleet (the canopy's mechanism family) | the *trigger* for a hinge from the entry event |

### 1.2 `Working/`

| file | covers |
|---|---|
| `Working/Q/PILOT/CONTROLS.md` | canonical 24-row control table + §2 conflicts A–H + §3 small-model rules |
| `Working/Translation/build_batches.json` | `MOD-4` "Canopy opens on entry/exit" (rows `P-06` canopy hinge, `T-PA5` door_parts map, state `carried`, card `T-12`); `ANI-8` "Canopy opens on entry" (state `documented`) |
| `Working/Parts/` | part anchors used by `P-06` |
| `Working/Entity/bm_epe_edits.json` | the `.epe` edit receipt (interaction objects moved per `t9_interaction.json`) |

### 1.3 `Research/BatmobileGrab/` (BmAK side, all generated + `--check`ed)

`CONTROLS.md` (374 bindings, token→key→line), `CONTROLS_NATIVE.md` (native function presence,
`TryToChangeMode` gate, mode name constants), `CONTROLS_CONSUMERS.md` (§1 LT, §2 B, §4 LB, §5 A
verdicts), `CONTROLS_MENU_SCREENS.md` (the drawn labels, pursuit + battle), `BINDINGS_MERGED.md`
(the 366-entry oracle and the effective gamepad table), `BINDINGS_KEYBOARD.md`, `CLASS_DEFAULTS.md`
(the 21 move members), `ANIMATIONS.md` (canopy clips, frames, fps, tracks), `AUDIO.md`
(`Play_CockpitOpen`/`Play_CockpitClose`), `EJECT_MOVE.md` / `EJECT_VELOCITY.md` (the eject body),
`DRIVERLEFT_7400.md`, `SAMPLER_UNKNOWNS*.md` (`bCockpitOpen` bit), `SOCKETS_JC3.md`,
`BMSDK_OFFSETS.json` (offsets quoted in §2/§4), `FOOTAGE.md` (the boost capture 30–38 s).

### 1.4 `Research/JC3Grab/` (JC3 side)

`INPUT.md` (474 bindings / 154 actions), `INPUT_D11.md`, `EJECT_MAP.md` (§3–§5: the shipped table,
the face-button census, the per-button ownership table), `INTERACTION.md` (the driver objects),
`DRIVE_CARRIERS.md` (C1/C3/C6/C8/C9 carriers + fleet defaults), `MOVING_PARTS.md`,
`FEATURE_CENSUS.md` (part behaviours: `SteeringWheel` 9 chassis / 20 entities), `SEAT.md`,
`EJECT.md`/`EJECT_REVIEW.md`, `USAGES.md` (`arcade.nitro_boost` 145/232).

**Nothing in the two sections above is restated below except where a number is required to close a
row.**

---

## 2. BmAK entry — the sequence, with numbers

### 2.1 There is no enter button in BmAK (decoded absence)

| check | result | label |
|---|---|---|
| any token in the chain matching `Enter`/`GetIn`/`Board` | **none**; the 30-row vehicle action table in `CONTROLS.md` has no enter row | decoded |
| `ExitVehicle` alias | defined `DefaultInput.ini:178`, **referenced by 0 key lines** | decoded (`CONTROLS.md` alias table) |
| `ExitVehiclePressed` / `ExitVehicleReleased` | **not in** `BmGame.upk`'s name table (`False`, 0 exports) | decoded (`CONTROLS.md` token lookups) |
| `LB` (`XboxTypeS_LeftShoulder`, `:271`) | `DualPlay` → `DualPlayPressed`, 17 bytes, **0** virtual/final calls to an exit function | decoded (`CONTROLS_CONSUMERS.md` §4) |

Consequence (derived): the entry half of the control scheme **belongs to JC3 by construction**. The
operator statement "enter with JC3's Y" (`CONTROLS_MENU_SCREENS.md`, operator-stated) is therefore
not in conflict with BmAK — it is the only place an enter button *can* come from. The earlier
"conflict A" framing in `Working/Q/PILOT/CONTROLS.md` is resolved by this row: there is no BmAK
enter binding to displace.

### 2.2 What the entry actually is: one of twelve special moves (decoded)

`RVehicleBatmobile` (`BmScript\RVehicleBatmobile.g.cs`), class offsets from
`CLASS_DEFAULTS.md` rows 1–19 and `BMSDK_OFFSETS.json`:

| # | member | class off | move asset (`Batman_Batmobile_Moves.*`) | situation |
|---:|---|---:|---|---|
| 1 | `GetInMove` | 8352 | `Get_In_Batmobile_Standing` | standing beside a stopped car |
| 2 | `GlideInMove` | 8360 | `Get_In_Batmobile_Gliding` | gliding in |
| 3 | `GlideBoostInMove` | 0x20b0 (8368) | `Get_In_Batmobile_Glide_Boost` | glide + boost |
| 4 | `FallInMove` | 8376 | `Get_In_Batmobile_Falling` | falling in |
| 5 | `GetInRemoteMoveFront` | 8432 | `Get_In_Batmobile_Remote_Front` | remote recall, front |
| 6 | `GetInRemoteMoveBack` | 8440 | `Get_In_Batmobile_Remote_Back` | remote recall, back |
| 7 | `JumpInBatmobileSkidStopMove` | 8448 | `Jump_In_Batmobile_Skid_Stop` | skid-stop pickup |
| 8 | `GetInWithoutAnimMove` | 8456 | `Get_In_Batmobile_No_Anim` | teleport-in, no animation |
| 9 | `GetInWhenBatmbileVerticalMove` | 8480 | `Get_In_Batmobile_Abseiling` | car vertical (wall/abseil) |
| 10 | `SwingInBatmobileAbseilingMove` | 8488 | `Get_In_Batmobile_Swing` | swing-in |
| 11 | `GetInOnSideMove` | 8504 | `Get_In_Batmobile_On_Side` | car on its side |
| 12 | `HighSpeedPickupMove` | 0x2148 (8520) | `Get_In_Batmobile_Fast_Remote` | high-speed pickup |

All twelve names are **decoded** (`CLASS_DEFAULTS.md` rows 1–19 + `ASSETS.md`'s
`RSpecialMoveConfigConfigurable` list). What is **not** decoded: the *selection rule* (distance,
speed, tilt, `IsVehicleAsleep`) that chooses among them — §8 U1.

### 2.3 The cockpit canopy (decoded numbers)

`ANIMATIONS.md`, anim set `BM_Batmobile_Chassis`, 30 fps, bone `canopy`:

| clip | frames | seconds | tracks | loops | use |
|---|---:|---:|---:|---:|---|
| `Cockpit_Open` | 14 | **0.433** | 23 | 1 | open |
| `Cockpit_Open_Idle` | 2 | **0.033** | 23 | 0 | held open while seated/exit pending |
| `Cockpit_Close` | 16 | **0.500** | 23 | 1 | close |

Donor variant present in the same package: `Batmobile_V2_Pose_States.Batmobile_V2_Cockpit_Open`
**10 frames / 0.300 s** (3 tracks) and `..._Close` **10 frames / 0.300 s** (21 tracks) — decoded.

State/event side (**decoded**):
`bCockpitOpen` = mask `0x80000` of the bool word at **`RVehicleBatmobileBase +0x11d8` (4568)**
(`BmGame\RVehicleBatmobileBase.g.cs:4630`), observed set during the eject
(`SAMPLER_UNKNOWNS.md`: `0x400000 → 0x480000` gained `bCockpitOpen`, then reverted);
`ARVehicleBatmobileBase::PlayCockpitOpenFast` is called from
`DrivingMode.EjectFromVehicle` at script **+443** (`EJECT_MAP.md` step 6); audio events
`Play_CockpitOpen` / `Play_CockpitClose` exist in `Playable_Batmobile_SF` (`AUDIO.md`);
`SVehicle.EnterVehicleSound` **0x6fc**, `SVehicle.ExitVehicleSound` **0x704**.

`CockpitAnimNode` (`AnimNodeSequence`, `+0x149c`) plus `BoostBlendNode`/`ArmourBlendNode`
(`AnimNodeBlend`, `+0x14ac`/`+0x14b4`) are the anim-node members that hold these clips — decoded
offsets, values not serialised in the defaults.

---

## 3. BmAK exit — the sequence, with numbers

### 3.1 The five exit variants (decoded)

| member | class off | move asset | situation |
|---|---:|---|---|
| `GetOutMove` | 8384 | `Get_Out_Batmobile_Stand` | stopped car, normal exit |
| `GetOutToStandFastMove` | 8392 | `Get_Out_Batmobile_Moving_To_Stand` | moving exit → stand |
| `GetOutOnTopMove` | 0x20d0 | `Get_Out_Batmobile_Stand_On_Top` | exit onto the roof |
| `GetOutOnTopOnSteepInclineMove` | 0x20d8 | `Get_Out_Batmobile_Stand_On_Top_Steep_Incline` | roof, steep incline |
| `GetOutOnSideMove` | 0x2140 | `Get_Out_Batmobile_On_Side` | car on its side |

Roof-exit incline threshold: `GetOutOnTopOnSteepInclinePitch` = **5000** (`IntProperty`, off 8560) —
value decoded, **unit UNKNOWN** (§8 U2).

### 3.2 What gates an exit (decoded members, decoded natives)

| gate | member / function | offset or address | label |
|---|---|---|---|
| exit forbidden | `bPreventBatmbileExit` | `+0x11dc` (bool in the shared word) | decoded |
| side choice allowed | `bCanGetOutOnLeftSide` | `+0x11e0` (bool in the shared word) | decoded |
| space check | `ARVehicleBatmobileBase::execCheckSpaceToGetOutOfBatmobile` | `0x140548f10` | decoded |
| cockpit space | `...::execCheckSpaceAboveBatmobileCockpit` | `0x1404be190` | decoded |
| cockpit state | `...::execIsCockpitOpen` | `0x1404bde20` | decoded |
| exit placement | `...::execSetBatmobileExit` | `0x1404bdde0` | decoded |
| placement params | `SVehicle.ExitPositions[]` `+0x5dc`, `ExitRadius` `+0x5ec` (float), `ExitOffset` `+0x5f0` (`Vector3`) | — | decoded offsets, values UNKNOWN |
| anim-node driver | `Vehicle.Driver` `+0x5c8`, `AkVehicle.LastDriver` `+0x820` | — | decoded |
| tilt gate on mode change (not exit) | `LocalToWorld.ZPlane.Z` vs **−0.707 / +0.707** | `0x140063f04` / `0x140063f22` | decoded (`CONTROLS-0xd8.md`) |

Eject (the third way out) is fully reported in `EJECT_MOVE.md` / `EJECT_VELOCITY.md` /
`EJECT_MAP.md`: `EjectUpDist` `+0x1790`, `MaxEjectType` `+0x170e`, `OverrideNextEject` `+0x15e4`,
`BoostingOut` `+0x170d`, five eject move members (`EjectUpMove` 8416, `EjectForwardMove` 8424,
`EjectWhenBatmobileVerticalMove` 8464, `EjectUpWhenBatmobileVerticalMove` 8472, `EjectToSpotMove`
0x2130), car velocity `(0,0,0)` on `Car.Mesh` at +513, `LastEjectFromBatmobileTime` written at
+1273. **Not re-derived here.**

---

## 4. The BmAK pad scheme, as numbers

From `CONTROLS.md` (`DefaultInput.ini` line in brackets) + `CONTROLS_MENU_SCREENS.md` labels +
`BINDINGS_MERGED.md` (merge = append, 366/366 on the `BmInput.ini` oracle).

| function | BmAK token | pad | line | tuning members that make it BmAK's (decoded offsets) |
|---|---|---|---|---|
| accelerate | `aThrottleAxis`, `bFireVehicleWeapon` | RT axis / RT | 254 / 252 | `RVehicleSimBatmobile.BoostTorqueVSpeedCurve` 0x1dc, `StandardTorqueVSpeedCurve` 0x1f0, `ThrottleSpeed` 0x190c |
| brake / reverse | `BrakePressed`, `bHandbrakeOrBrake` | X | 269 | `Brakes.*`, `HandBrakePct` 0x3bc, `HandBrakeOffTime` 0x3c0, `HoldingBrakeTime` 0x290 |
| steer | `aTurn` (RS X), `aStrafe` (LS X), `aBaseY` (LS Y) | sticks | 265 / 263 / 264 | `StandardSteeringSpeedCurve` 0x240, `FrontWheelSteerPct` 0x3b8, `RearWheelSteerPct` 0x3b4, `DesiredTurnOnSpotSpeed` 0x1d8 |
| power slide (drift) | `bHandbrakeOrBrake` + throttle + steer (menu) | LS+RT+X | 269 + 254 | `DriftAngularVelocityBySteer` 0x1f48, `DriftSpeedBySteer` 0x1f5c, `DriftAngularVelocityFactor` 0x1f70/…Max 0x1f74, `DriftVelocityFactor` 0x1f78/…Max 0x1f7c, `DriftVelocityForcePosOffset` 0x1f80, `DriftCorrectionSteerSpeed` 0x1f8c, `DriftWobble*` 0x1f90/0x1f94/0x1f98, `DriftDrag` 0x2c8, `HandbrakeTurnType` 0x170a, `HandbrakeSteeringSpeedCurve` 0x254 |
| afterburner (pursuit) | `bVehicleBoostButton` | Y | 270 | `BoostDuration` 0x298, `BoostCooldown` 0x29c/0x2a0/0x2a4, `DriftingBoostCooldown` 0x2ac, `BoostSteeringSpeedCurve` 0x22c, `WheelspinBoost` 0x2b4, `AfterburnerSystem` 4636, `AfterburnerWarmupSystem` 4644, `SideExhaustBoostEffect` 0x125c, rumble `fAfterBurnerRumbleStartStrength` **5.0** / `…TimeMultiplier` **25.0** / `…CutoffTimeMultiplier` **100.0**, `AfterburnerFFWaveForm` 8528 |
| battle mode (hold LT) | `aLeftTrigger` | LT axis | 253 | threshold **0.05** in `IsBatmobileFireButtonHeld`; ini DeadZone **0.2**; `BattleModeSpeedDelta` 0x1eb4, `bBattleModeLocked`/`bLockInBattleMode` (word 0x11d8), `BattleModeYawOffset` 0x1910 |
| primary weapon | `BatmobileFireButton` | RT | 252 | `CurrentWeapon` 0x130c, `BattleModePrimaryWeapon` 0x147c, `PursuitModePrimaryWeapon` 0x1474 |
| secondary weapon | `SecondaryFireVehicleWeapon`, `bFireVehicleSecondaryWeapon` | RB | 272 | `SecondaryWeapon` 0x1314 |
| weapon slot 1 (tracker/immobiliser/EMP) | `QuickGadgetB` → `SelectVehicleWeapon(1)` | B | 268 | `VehicleWeapons[0..9]` 0x1334…, `ActualWeapons[10]` 0x13d4…, `WeaponWeaponFlags[10]` 0x17c0… |
| weapon slot 2 (barrage) | `QuickGadgetX` → `SelectVehicleWeapon(2)` | X | 269 | handler export **105040, 10 script bytes**, one virtual call; gate chain in `SelectVehicleWeapon` (export 104971, 448 bytes): `IsButtonInputIgnored` +8, `ReadyToFire` +92, `IsFiring` +209, `TryToFireWeapon` +278, `TryRightingFlip` +315, `ReadyToFire` +364, `TryToFireWeapon` +402, `TriggerEventClass` +432 |
| weapon slot 3 (drone virus) | `QuickGadgetY` → `SelectVehicleWeapon(3)` | Y | 270 | as above |
| weapon slot 4 (missile pods) | `SelectVehicleWeapon 4` / `ReleaseVehicleWeapon 4` | D-Pad Up | 259 | `PursuitModeWeapons[10]` 0x1384…, `PursuitModeWeaponFlags[10]` 0x1860… |
| sonar | `BatmobileSonar` → `…Pressed`/`…Released` | L3 | 256 | — |
| look behind | `bLookBehindVehicle` | RS | 255 | `DriverViewPitch/Yaw` `SVehicle` 0x788/0x78c |
| camera cycle | `ToggleDrivingCamera` | RB / C | 272 / 186 | `DriverView*`, `CockpitCameraOffset` `R3rdPersonCamera` 0x5580 |
| eject | `EjectFromVehicle` (+`BattleStrafe`) | A | 267 | §3.2 |
| exit | (menu only) | LB | 271 = `DualPlay` | §3.1 |
| pause / WayneTech | `UserPause` / `OpenLevelUpOrMap` | Start / Back | 262 / 261 | — |

Armour side of battle mode (for completeness of the mode row, not this card's build):
`ArmourModeDamageReduction` `+0x1918`, `CurrentArmourLevel` `+0x1fa8`, `ArmourLevels[]` `+0x1fac`,
`ArmourBlendNode` `+0x14b4`, `ArmourMode` bool in word `+0x11d8`.

---

## 5. JC3's side of the same facts (decoded)

| fact | value | source |
|---|---|---|
| shipped gamepad table | **131 base / 145 patch bindings**; `ENTER_VEHICLE` **and** `EXIT_VEHICLE` both on **`RPADUP`**; **0** face-button rows (no A/B/X/Y at all) | `EJECT_MAP.md` §3 + its 24/24 checks |
| player's export (`kepmap.txt`) | 249 rows; both actions on **`Y`**; `HANDBRAKE` X, `ACCELERATE` RT, `REVERSE` LT, secondary `LSHOULDER`, primary `RSHOULDER`, `USE_VEHICLE_MOD` B | same |
| multi-action keys are the shipped shape | `LSHOULDER` carries **8** tokens; `X` carries **8** (`TriggerFearTakedown 0`, `TriggerQuickStrike`, `QuickGadgetX`, `ReleaseQuickGadgetY`, …, `BrakeButton`, `QuickStrikeReleased`) | `BINDINGS_MERGED.md` §4 (BmAK) and `EJECT_MAP.md` §7 (JC3) |
| any vehicle module naming an action | **0 of 134**; **0 of 232** entity dumps contain `keymap` | `INPUT_D11.md`, `EJECT_MAP.md` |
| driver seat object | `point.driver` id `93F2612B=FFFF52D5`, world translation **−0.440, 0.340, 0.200 m**, 3×3 identity | `review-JC3-SEAT.md` §2 |
| enter state | `entry.driver` (`CInteractionGraphEntry`) → `S_ENTER_DRIVER_VEHICLE`; `check` 0, `min` 0, `max` 3 | `INTERACTION.md` line 40 |
| exit states | `exit.driver.default` → `S_EXIT_VEHICLE`; `exit.driver.moving.parachute` → `S_EXIT_VEHICLE_PARA` gate **(5.0, 999.0)**; `exit.driver.roll.out` → `S_ROLL_OUT_EXIT_VEHICLE`; `exit.ai.driver.to.hood` → `S_EXIT_DRIVER_TO_HOOD_VEHICLE` | donor `.epe`, `EJECT_MAP.md` §3.1 |
| seated pose selector | `set.node.npc.state = S_IDLE_DRIVER_VEHICLE` on `point.driver`; graph `modifier = MOD_LOW` → `car/low` (23 clips) | `review-JC3-SEAT.md` §§2–3 |
| entity | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.ee` (the mod's own file; `bm_entity.py:79`) | `bm_entity.py` |
| built tune tree | `Builds/bm-RC3-parts/.../v0300_car_kensington_sportsmuscle/modules/default/batmobile/`: `land_steering`, `brakes`, `custom_land_global`, `land_global`, `transmission`, `vehicle_misc`, `rigid_body`, `suspension`, `land_engine`, `land_aerodynamics`, `land_audio`, `palette` `.vmodc` | directory listing (decoded) |
| drift block fleet defaults | `min_speed_to_drift_kmph` **10**, `max_drift_torque` **5000**, `constant_drift_torque` 0, `steering_sensitivity` **4**, `max_drift_angle_deg` **45**, `counter_steer_torque_handbrake` **30000**, `keep_velocity_strength` 1, `velocity_rotation_amount` 80, `…start_angle` 15, `…end_angle` 40 (n=145) | `DRIVE_CARRIERS.md` §3.1 |
| boost block | `arcade.nitro_boost` on **145/232** builds (5 members) + `nitro_boost_upgraded` + `Transmission.nitrous_gears` + `VehicleMisc.full_nitro_*` | `DRIVE_CARRIERS.md` row C9, `USAGES.md` |
| camera tune | `editor/entities/jc_cameras/vehicle_cameras/bat_base.ctunec` (asserted present exactly once by `bm_entity.py`) | `bm_entity.py` |

---

## 6. Closest JC3 mechanism per BmAK step — member by member

Format: BmAK step → JC3 carrier (exact file + member) → verdict.

### 6.1 Entry trigger

| BmAK | JC3 carrier | verdict |
|---|---|---|
| enter is implicit (no token) | JC3 `ENTER_VEHICLE` action, keymap `settings/keymap_gamepad.bin` + `keymap_keyboard.bin` (patch layer) | **exact** — nothing to displace |
| 12 `GetIn*Move` variants chosen by situation | **one** JC3 state pair: `entry.driver` → `S_ENTER_DRIVER_VEHICLE` (+ `entry.ai.driver.left`, `entry.driver.no.door` → `S_ENTER_DRIVER_NO_DOOR_VEHICLE`) | **closest + gap**: JC3 ships 3 entry states where BmAK has 12 situations. Gap rows and build in §7.1 |
| the move itself (root-motion handoff, ~1 m step-in) | Rico's state machine `rico_base.afsmb`; entry clip family `car/low` (23 clips) selected by `graph.modifier = MOD_LOW` | **closest + gap**: BmAK's move assets are outside `BmGame.upk`; JC3's state is native. Build = §7.1(3) |
| canopy `Cockpit_Open` 0.433 s, 14 frames, 23 tracks, bone `canopy` | part hinge (`RB_ConstraintInstance`-family rows in the parts module, the same family as `JC3-door-angles.md`; part anchor `P-06` in `build_batches.json` MOD-4) + occupant condition `entry.driver min/max` | **closest + gap**: no event-driven canopy timeline in JC3 data. Build = §7.2 |
| `SVehicle.EnterVehicleSound` (0x6fc) + `Play_CockpitOpen` | `modules/default/batmobile/..._land_audio.vmodc` (event slots) | **closest**, event name UNKNOWN — §8 U4 |

### 6.2 Seat and pose

Covered by `review-JC3-SEAT.md` (`point.driver` transform, `MOD_LOW`, `S_IDLE_DRIVER_VEHICLE`).
This card adds only the transition: all three objects (`entry.driver`, `point.driver`,
`set.node.npc`) already exist in the mod's own `.epe`, so entry needs **no new interaction object** —
only the canopy and the exit-button split. Verdict: **exact**.

### 6.3 Exit trigger

| BmAK | JC3 carrier | verdict |
|---|---|---|
| LB exit (menu; token unbound in ini) | JC3 `EXIT_VEHICLE`, moved from `RPADUP` to `LSHOULDER` in the patch-layer keymap | **closest + gap**: JC3 shares enter/exit on one control, so it must be split (§7.3) |
| `bPreventBatmbileExit` gate | donor `exit.driver.default` `enabled` member + `CInteractionGraphNodeOccupiedCondition` | **closest**, condition semantics UNKNOWN — §8 U5 |
| `bCanGetOutOnLeftSide` | `exit.driver.left` **exists in the donor vocabulary** (`exit.ai.driver.left`, `INTERACTION.md` line 108) | **exact** (object exists) |
| `CheckSpaceToGetOutOfBatmobile` | JC3's own placement test on `point.driver` + `exit.driver` world | **closest + gap**: JC3's test is native; build = §7.3(3) |
| `SVehicle.ExitPositions[]` / `ExitRadius` / `ExitOffset`, 5 exit move variants | JC3: one `point.driver` (with the **−0.44, 0.34, 0.20** transform) + `exit.driver.roll.out` / `.to.hood` / `.moving.parachute` | **closest + gap**: 5 BmAK exits ↔ 4 JC3 exit states; roof/incline/side exits have no JC3 state — build = §7.3(4) |
| exit → cockpit close (0.500 s) | same hinge as entry | **closest + gap**: same build as §7.2 |
| exit at speed → parachute state | `exit.driver.moving.parachute` gate **(5.0, 999.0)** | **exact** for the "at speed Rico leaves through the air" half |

### 6.4 Controls → JC3 action + carrier

| BmAK control | JC3 action bound | carrier that makes it BmAK's behaviour | verdict |
|---|---|---|---|
| RT accelerate | `ACCELERATE` (unchanged) | `..._land_engine.vmodc` + `RigidBody` + `Transmission` | **exact binding**, numbers = §7.4 |
| LS steer | `TURN_LEFT`/`TURN_RIGHT` (+`aBaseY` on LS-Y) | `..._land_steering.vmodc`: `steer_angle_min_speed_deg`, `steer_angle_max_speed_deg`, `steering_type` (`FrontSteered`), `is_all_wheel_steered` 1 | **exact binding**, BmAK curve UNKNOWN — §8 U6 |
| X brake/reverse | `HANDBRAKE` (already X) **+ `REVERSE` added to X** | `..._brakes.vmodc` rear handbrake + `handbrake_friction_factor`; `CustomVelocityDamper` `handbrake_spin_damping` | **closest + gap**: JC3 splits brake (LT) from handbrake (X); BmAK has one X. Multi-action key is a shipped shape → §7.5 |
| LS+RT+X power slide | `HANDBRAKE` while `ACCELERATE` held + steer | `custom_land_global.vmodc`: `drift.min_speed_to_drift_kmph` 10, `max_drift_angle_deg` 45, `max_drift_torque` 5000, `steering_sensitivity` 4, `counter_steer_torque_handbrake` 30000, `keep_velocity_strength` 1, `velocity_rotation_amount` 80/15°/40° | **exact carrier** (`DRIVE_CARRIERS.md` C8 "carrier found") |
| Y afterburner | **`USE_VEHICLE_MOD` on Y** | `arcade.nitro_boost` (145/232) + `Transmission.nitrous_gears` + `VehicleMisc.full_nitro_*`; FX `effects/jc_vehicles/exhaust/car_cycle_base_nitrous.effc`, `EngineNitro → dynamic_nitrous` | **closest + gap**: JC3 has no boost action name; its *mod* action is the nearest trigger and the nitro block is a real carrier → §7.6 |
| RT primary (battle) | `FIRE_VEHICLE_WEAPON_PRIMARY` | entity `main_weapon` slot `851CAABE` (cannon `w602_mediumtank_canon`) | **closest + gap**: RT is accelerate in JC3 → §7.7 |
| RB secondary (battle) | `FIRE_VEHICLE_WEAPON_SECONDARY` → **moved to RB** (LSHOULDER freed for exit) | entity `secondary` slot `00568A74` (Vulcan `w603_mediumtank_mgun`) | **closest + gap** → §7.7 |
| B / X / Y slot selects | `USE_VEHICLE_MOD` selection + the entity's 4 slots (`main_weapon`, `secondary`, `id:AC0BC788`, `mounted_weapon` — the last two ship null) | `QuickGadgetB/X/Y` are `SelectVehicleWeapon(1/2/3)` — same slot model | **closest + gap**: JC3 has 4 slots, 2 null → §7.7 |
| D-Pad Up weapon 4 | `SelectVehicleWeapon 4` has no JC3 action | missile pod sockets `MissileL`/`MissileR` (`SOCKETS_JC3.md`) | **closest + gap** → §7.7 |
| L3 sonar | no action name | — | **UNKNOWN** — §8 U7 |
| RS look behind | `LOOK_BACK_CAM` (already RS) | `bat_base.ctunec` | **exact** |
| RB cycle view | `VEHICLE_CAM` on RS-button conflicts with `LOOK_BACK_CAM`; use LB? — **no**, LB is exit. Carrier-side this is `bat_base.ctunec` | **closest + gap** → §7.8 |
| A eject | no `EJECT` action name (0/4 tables) | `exit.driver.moving.parachute` + `S_EXIT_VEHICLE_PARA` | **closest + gap** (`EJECT_MAP.md` step rows; build row in §7.9) |
| LT battle hold | no action name | `mode-switch-carriers.md` | **deferred to that card** (cited), stated here only as a constraint: LT must be freed of `REVERSE` first |
| Start / Back | `GUI_PAUSE` / `GUI_PDA` | — | **exact, untouched** (priority 1) |

---

## 7. Build recipe — what closes each gap

Every action below is offline, into a new private tree under `Builds/`, and reversible by deleting
the tree. Paths are relative to the built car
`Builds/<tag>/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/`.

### 7.1 Entry sequence (gap: 12 BmAK entry situations → 3 JC3 entry states)

1. **`v0300_car_kensington_sportsmuscle_debug.epe`** — author the entry set:
   keep `entry.driver` → `S_ENTER_DRIVER_VEHICLE`; add `entry.driver.moving` →
   `S_ENTER_DRIVER_VEHICLE` gated by a `CInteractionGraphParentVelocityCondition`
   (`min` = first value of the measured pickup speed, `max` 999) so a car rolling past still admits
   the driver; add `entry.driver.side` → `S_ENTER_DRIVER_VEHICLE` on the side point, mirroring
   `exit.driver.left`'s vocabulary (`INTERACTION.md`).
2. **`point.driver`** — unchanged (−0.440, 0.340, 0.200 m). Any second entry point is a *clone* of
   it with its own world; do **not** move the seat.
3. **Recover the move length** so the "standing / gliding / falling / abseiling / swing / side /
   remote / skid-stop" split has numbers: read the seven
   `Batman_Batmobile_Moves.Get_In_Batmobile_*` `RSpecialMoveConfigConfigurable` instance bodies
   (root-motion curves). Output: `Working/Batmobile/entry_moves.json`, one row per move with
   duration (frames ÷ 30) and forward/vertical displacement. Those numbers become the JC3 **camera
   and state-timing** rows (`bat_base.ctunec` transition duration) and the **canopy lead time**
   (§7.2 step 2).
4. **Remote recall** (BmAK `GetInRemoteMoveFront/Back`, `HighSpeedPickupMove`) has no JC3
   interaction member: compose it as a second `point.driver` + `entry.driver` pair on the car's
   **left** and **right** side points, so the pickup is an ordinary entry from a different side.
   This is a data-only composition; no new class.

### 7.2 Canopy (gap: no event-driven canopy in JC3 data)

1. **Split the canopy into its own part** named on the `canopy` bone (part anchor `P-06`,
   `build_batches.json` MOD-4 row `P-06` state `documented`; `T-PA5` `door_parts` map). It must be
   a separate part, not a merge into `Batmobile_Chassis`, or it cannot be hinged
   (`FEATURE_CENSUS` part-behaviour model).
2. **Hinge rows**: author `RB_ConstraintInstance`-family rows on that part with the pivot on the
   canopy's rear edge, swing axis fore-aft, limits from the **decoded** anim swing (measure the
   canopy bone's rotation over `Cockpit_Open`'s 14 frames; that measurement — not a guess — sets
   `limit_angle`). Family and row shape: `physicsc-hinges.md`, `JC3-door-angles.md`,
   `JC3-stations-hinges.md`.
3. **Trigger**: drive the hinge from the only occupant signal the car owns —
   `entry.driver`'s occupancy condition (`check` 0, `min` 0, `max` 3). Compose: a second
   `CInteractionGraphNodeOccupiedCondition` on the *same* node with `min` 1 fires while Rico is
   seated; the hinge's target angle is authored **open** for `min` 0…1 transitions and **closed**
   once seated, i.e. the hinge's default pose is "open when empty" and the constraint drives it
   shut on occupancy. This inverts the usual door logic deliberately: it makes the *absence* of a
   driver the open state, which is exactly BmAK's `Cockpit_Open_Idle` (0.033 s hold-open) semantics.
   If the hinge cannot be driven by occupancy (U3), fallback: author the canopy as
   `Batmobile_V2_Pose_States.Batmobile_V2_Cockpit_Open`-style **pose blend** on the chassis
   part (10 frames / 0.300 s, decoded) and accept the animation channel — that is a *composition*,
   not a limit.
4. **Timing**: open lead ≥ 0.433 s before the driver's feed enter (from §7.1 step 3 numbers);
   close 0.500 s after `S_EXIT_VEHICLE` begins.
5. **Audio**: bind `Play_CockpitOpen` / `Play_CockpitClose` events into
   `modules/default/batmobile/..._land_audio.vmodc`'s vehicle event slots (the same mechanism
   `land_audio.vmodc` already carries for the fleet).

### 7.3 Exit sequence (gap: shared enter/exit control, 5→4 exit states)

1. **Split the pair** in the patch-layer keymap: `Y → ENTER_VEHICLE` only,
   `LSHOULDER → EXIT_VEHICLE` only, `LSHOULDER` loses `FIRE_VEHICLE_WEAPON_SECONDARY`. Byte-level
   target: gamepad patch entry (145 bindings) and keyboard patch entry (104 bindings); the same
   edit as `INPUT.md`'s patch layer, re-serialised with `jc3_input`. Reversible by shipping the
   vanilla bins.
2. **`exit.driver.default`** keeps `S_EXIT_VEHICLE`; **add** `exit.driver.side` on
   `point.driver.left` (mirrors `bCanGetOutOnLeftSide`) and keep the speed gate
   (5.0, 999.0) on `exit.driver.moving.parachute` so a moving exit still goes through
   `S_EXIT_VEHICLE_PARA`.
3. **Space test**: author the exit's world as a short ray off `point.driver` along the car's left
   normal; the JC3 side performs its own placement test, and `ExitRadius`'s BmAK value is the
   number to match once §8 U5 gives it. Until then, use the donor's shipped exit world.
4. **Roof / incline / side exits**: BmAK has three exit destinations JC3 does not name. Compose
   them from the *existing* vocabulary rather than inventing states: `exit.driver.roll.out`
   (`S_ROLL_OUT_EXIT_VEHICLE`) covers roof, `exit.ai.driver.to.hood`
   (`S_EXIT_DRIVER_TO_HOOD_VEHICLE`) covers incline, `exit.driver.left` covers side. Three JC3
   states, three BmAK destinations — a 1:1 assignment with no new state machine work. Assignment
   is **derived** from the state names' own wording; the check is §8 U2's pilot card.
5. **Cockpit close**: §7.2 step 4.
6. **Eject**: keep `exit.driver.moving.parachute`; `EJECT_MAP.md`'s 24 checks already pin the
   carrier. This card adds only that eject and LB-exit must not share a control
   (they do not: A vs LSHOULDER).

### 7.4 Steering numbers

Read `..._land_steering.vmodc`'s `steer_angle_min_speed_deg` / `steer_angle_max_speed_deg` and
`LandGlobal.steering_type`; write the BmAK pair once §8 U6 measures it. Until then the row stays
open with the donor value **not** re-labelled as BmAK's.

### 7.5 Brake and reverse on one key

Add `REVERSE` to `X`'s action list in the patch-layer keymap (X already carries `HANDBRAKE`).
Multi-action keys are the shipped shape (X: 8 tokens; LSHOULDER: 8 tokens — §5), so this is a
data edit, not a new mechanism. Consequence to record: `LT` is then free of `REVERSE`, which is the
precondition for the LT battle hold on the mode card.

### 7.6 Boost trigger (gap: no boost action name)

Bind `Y → USE_VEHICLE_MOD`, and put the boost in the mod slot:
`modules/default/batmobile/..._vehicle_misc.vmodc` + `..._transmission.vmodc` carry
`arcade.nitro_boost` / `nitrous_gears` / `full_nitro_*`; the effect side is
`effects/jc_vehicles/exhaust/car_cycle_base_nitrous.effc` (+ `EngineNitro → dynamic_nitrous`,
`G2X.md`). Numbers to write once measured: `BoostDuration`, `BoostCooldown` (three cooldown
members on `RVehicleSimBatmobile`: 0x29c/0x2a0/0x2a4) and the rumble triple (5.0 / 25.0 / 100.0).
`bBoostLocked` / `bDisableBoostOut` in the `+0x11d8`/`+0x11e0` words are the lock members should
the eject interaction need them.

### 7.7 Weapons and the gadget wheel (gap: 4 JC3 slots, 2 shipped null)

1. Slots: `main_weapon` `851CAABE` = cannon `w602_mediumtank_canon`; `secondary` `00568A74` =
   Vulcan `w603_mediumtank_mgun`; missile pods `w618_sportsmuscle_missile` into one of the two
   **null** slots (`id:AC0BC788`, `mounted_weapon`) — this is exactly what `bm_entity.py` already
   writes and records as `unbound[]`.
2. Fire actions: primary `RSHOULDER` (RB), secondary `LSHOULDER` → **moved to RB is wrong**
   (one button, two actions); instead the Vulcan stays `secondary` but its action moves to **RB**
   and the cannon to **RT**, keeping the two fire actions on BmAK's two fire buttons:
   `RT → ACCELERATE + FIRE_VEHICLE_WEAPON_PRIMARY` (multi-action), `RB → FIRE_VEHICLE_WEAPON_SECONDARY`.
   Consequence recorded: in pursuit, RT fires the slot-1 weapon as well as accelerating; the
   mitigation is that pursuit's slot-1 is the tracker/immobiliser, whose `ReadyToFire` gate
   (`SelectVehicleWeapon` +92 / +364) is what holds fire until a target is tagged — i.e. BmAK's own
   "B to tag, then fire" order.
3. Slot selection: `B/X/Y/D-Pad-Up` → `USE_VEHICLE_MOD`-driven slot index 1..4, matching
   `SelectVehicleWeapon(1/2/3/4)`; the release partner is BmAK's `ReleaseQuickGadgetB/Y`.
4. Gadget wheel: JC3 has no wheel — compose it from the four slot keys (B, X, Y, D-Pad Up) and the
   `DrawWeaponSelectHud` equivalent in `hud.gfx` (weapon widgets; `G3-HUD-CLUSTER.md`).

### 7.8 Camera

`bat_base.ctunec` is the carrier for both cycle-view and look-behind framing; the button conflict
(`R3` = `VEHICLE_CAM` and `LOOK_BACK_CAM`) is resolved on the keymap side by moving
`VEHICLE_CAM` to `RSTICKBUTTON`-long / leaving look-behind on the same stick **hold** — press vs
hold has no field in JC3's tables (`EJECT_MAP.md` §3.1), so this is the one row that needs
§8 U8's probe before a build edit.

### 7.9 Eject

No build action here: `EJECT_MAP.md` and `review-JC3-EJECT.md` own it. Only the control consequence
(A stays eject; it must not also carry enter) is registered in §7.3.

---

## 8. UNKNOWNs — each with its settling file/probe and a pilot card

Every row below is one sentence for the pilot: **what to do, and the band that passes**.

| # | UNKNOWN | settles with | pilot card check (one sentence) | pass band |
|---|---|---|---|---|
| U1 | which of the 12 `GetIn*Move` variants plays for a given distance/speed/tilt (the selection rule) | `DrivingMode`/`RPlayerController` bytecode walk for the `GetInMove`-family member reads (the same walker that produced `SAMPLER_UNKNOWNS2.md`); fallback probe = the `Get_In_Batmobile_*` root-motion curves (§7.1 step 3) | Stand 1 m, 5 m, 15 m and 30 m from the car and press enter four times each; note which body animation plays. | 1–5 m plays `Standing` 4/4; ≥ 15 m either does not offer the prompt or plays `Remote/Fast_Remote` 4/4; 0/12 plays `No_Anim` while standing still |
| U2 | unit of `GetOutOnTopOnSteepInclinePitch` = **5000** (int) and whether the roof/incline/side assignment in §7.3(4) is right | `BmScript\RVehicleBatmobile.g.cs` property block (comment/unit) + `BMSDK_OFFSETS.json` typed row; probe = park the car on a 30° and a 45° slope and exit | Park on a ~40° slope, exit twice, and record whether Rico ends on the roof (`Get_Out_..._Stand_On_Top`) or beside the car. | roof exit 2/2 on ≥ 40°; side exit 2/2 on ≤ 20°; 0 falls through the car |
| U3 | whether an occupancy condition can drive a hinge (the canopy trigger in §7.2 step 3) | `Research/JC3Grab/INTERACTION.md` member census (no graph object carries a pose/angle member today) + a 5-minute probe: set a hinge's target angle in a built part and watch it hold | Enter and exit three times; watch the canopy. | canopy reaches ≥ 80 % of its measured swing before Rico's feed enter 3/3, and returns to closed within 0.7 s of `S_EXIT_VEHICLE` 3/3 |
| U4 | BmAK's enter/exit audio event names as JC3 could receive them (`Play_CockpitOpen`/`Close`, `EnterVehicleSound` 0x6fc, `ExitVehicleSound` 0x704) | `Research/JC3Grab/JC3_AUDIO.md` event census + `..._land_audio.vmodc` slot list | Enter and exit twice with audio captured; listen for a cockpit servo on open and a close thunk on exit. | cockpit sound present on 4/4 transitions; no sound on a stationary re-entry within the same second (0 double-triggers) |
| U5 | whether `bPreventBatmbileExit` maps to the donor's `exit.driver.default` `enabled` member (exit denial while, e.g., the car is moving or mid-transform) | `RVehicleBatmobile.DriverLeft`-style walk of the exit body (`DRIVERLEFT_7400.md` is the template) + the `enabled` member semantics in `INTERACTION.md` | Drive at 60 km/h and press LB; then stop and press LB. | moving exit either refuses 3/3 or routes to `S_EXIT_VEHICLE_PARA` 3/3 (never a standing exit at speed); stopped exit 3/3 |
| U6 | BmAK's steering response (the `aTurn` axis has no decoded curve; `AirControl*` are `VALUE-NATIVE` per `FOOTAGE.md`) | `RVehicleSimBatmobile.StandardSteeringSpeedCurve` / `DesiredTurnOnSpotSpeed` are the *read* sites; the BmAK *values* need the capture set, or a `DriftSpeedBySteer`-style curve read from `Default__RVehicleBatmobile` serialisation | Hold full left stick at 30 km/h and at 120 km/h on the same flat road and measure the time to 90° heading change. | ratio (30 km/h time) / (120 km/h time) inside 1.6–2.4; no wheel-lock below 10 km/h |
| U7 | the sonar trigger (BmAK L3; JC3 has no `SONAR`/`SCAN` action) | `Research/JC3Grab/INPUT.md` action census (0 name matches) + a keymap probe: add a spare action id on `LSTICKBUTTON` and see whether any scan effect fires | Press L3 in the built car with a target 20 m away behind a wall. | a scan visual appears on 3/3 presses, or 0/3 with the row re-queued (no silent pass) |
| U8 | press vs hold on a shared control (`RSTICKBUTTON` = `VEHICLE_CAM` + `LOOK_BACK_CAM`) and whether a patched dropzone keymap is honoured at all | `INPUT.md` §UNKNOWN (no hold/duration field in any table) + the dropzone probe already named in `Working/Q/PILOT/CONTROLS.md` §2-G | Tap R3 (view should cycle) then hold R3 for 1 s (camera should swing back). | tap cycles view 5/5; hold swings back 5/5 and releases back 5/5 |

Two further rows are **not** UNKNOWN and are recorded as decoded absence so no future card
re-opens them: BmAK has **no enter binding** (§2.1) and JC3's shipped pad table has **no face
buttons** (§5) — the second is why binding Y costs nothing.

---

## 9. Priority rule, stated once

Inside the car, in this order:

1. **JC3 keeps** `GUI_PAUSE` (`Start`/`Esc`) and `GUI_PDA` (`Back`/`Tab`) — operator rule,
   `CONTROLS_MENU_SCREENS.md`; unchanged by this card.
2. **BmAK's exit** owns `LSHOULDER` (`EXIT_VEHICLE`).
3. **BmAK's other buttons** own the rest: RT accelerate / fire, RB secondary, X brake-reverse-slide,
   B/X/Y/D-Pad-Up slots, A eject, L3 sonar, RS look-behind, Y boost.
4. **JC3 fills only what BmAK does not claim** on those buttons (e.g. `aBaseY` on LS-Y), and
   `ENTER_VEHICLE` on `Y` is inert inside the car *by intent*, not by precedence.

Outside the car: `Y` = `ENTER_VEHICLE`, and nothing else changes.

The single structural change this rule needs is the **split of JC3's shared `RPADUP` enter/exit
pair** — in the shipped table both actions sit on one control, which would make Y exit the car and
destroy the boost row. That split is a keymap data edit (§7.3 step 1), not a new system.

---

## 10. What was checked here, and what was not

Checked (offline, read-only):

* the 12 entry + 5 exit + 5 eject move members and their class offsets — `CLASS_DEFAULTS.md`,
  `BMSDK_OFFSETS.json` (queried directly for `Exit|Enter|Eject|Cockpit|Driver` members);
* the canopy clip numbers (14/2/16 frames, 0.433/0.033/0.500 s, 30 fps, 23 tracks) —
  `ANIMATIONS.md`;
* the exit/eject gate members and native addresses — `BMSDK_OFFSETS.json`,
  `CONTROLS_NATIVE.md`, `EJECT_MAP.md`;
* the control tokens and their ini lines — `CONTROLS.md`, `BINDINGS_MERGED.md`;
* the JC3 keymap facts (shared `RPADUP`, 0 face buttons, multi-action keys) — `EJECT_MAP.md`'s
  24 checks (read, not re-run);
* the built car's module tree — directory listing of `Builds/bm-RC3-parts` (the handling set is
  under `modules/default/batmobile/`, which the earlier per-directory `find` did not show).

Not done, by scope: no game launch or install (`APPROVED_Q.txt` absent), no keymap re-serialise,
no `.epe` edit, no hinge authoring. The build recipe in §7 is a plan; its rows are not yet built,
and no number above is a measurement from a running game.
