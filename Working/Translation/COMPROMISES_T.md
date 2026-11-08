# COMPROMISES_T - where the translation chose less than BmAK lore

**Answer: 72 of the project's 199 translation rows compromise the lore goal, and only 1 carry a recorded operator approval.** The other 71 are unapproved: they were decided inside the translation (a fleet median, a donor value, a proven absence, a "JC3 cannot") and no file quotes the operator agreeing to the loss. The most visible are the weapon slots (2 of 11 weapons fire; a third index has no member), the steering rate (2.4-3.2x slower than BmAK) and the silent BmAK banks.

Approval is quoted, never inferred: `APPROVED` means a file states a user/operator decision for that loss, and the check re-opens the file at the cited line. A loss that merely follows from an approved decision (D-2's hybrid car) is still UNAPPROVED.

| disposition | rows audited |
|---|---:|
| `next` | 48 |
| `blocked` | 11 |
| `edit` | 10 |
| `superseded` | 2 |
| `keep` | 1 |

| visibility | rows audited | unapproved |
|---|---:|---:|
| controls | 3 | 3 |
| weapons | 9 | 8 |
| sounds | 4 | 4 |
| look | 20 | 20 |
| handling | 26 | 26 |
| collision | 10 | 10 |

## 1. UNAPPROVED, ranked by visibility in play


### controls

- **T-WP13** (`next`, T-7) - BmAK: 11 weapon classes + 1 HUD code; D-7 says **every weapon in both modes**. **Build instead:** 2 driver slots bind; a 3rd SelectVehicleWeapon index has no member; 8 weapons have no slot. **Loss:** only 2 of 11 weapons can actually fire; the first T-WP13 pass recorded the other 8 as lost outright. *UNAPPROVED*
- **T-MD8** (`blocked`, T-15) - BmAK: battle mode turns the car on the spot (MOD-2's pivot; G2-21 found no JC3 carrier). **Build instead:** no pivot; the car turns only by driving. **Loss:** battle-mode turn-on-the-spot is missing from the car's control set. *UNAPPROVED*
- **T-BM1** (`superseded`, T-3) - BmAK: `BattleMode*` (9), `TurnOnSpot*` (3), `TransformationTurn*` (2), `TurningModeMaxSpeed`, `ArmourModeDamageReduction`. **Build instead:** `TurnOnSpot*` dropped to TANKTURN's named omission. **Loss:** the same pivot, recorded as a superseded row. *UNAPPROVED*

### weapons

- **T-WP4** (`next`, T-7) - BmAK: `RBatmobileEMPMissile` `Batmobile_EMP_Missile_Launcher` (3 instances, 63 fields) + `Batmobile_EMPMissile_Projectile_ForCars`. **Build instead:** `w618` clone + the entity `CForcePulse`; no disable. **Loss:** the EMP missile cannot disable a vehicle - the whole point of the gadget. *UNAPPROVED*
- **T-WP5** (`next`, T-7) - BmAK: `RBatmobileEMP` `Batmobile_EMP_Burst` (3 instances, 36 fields). **Build instead:** entity `CForcePulse` + `truck_emp.ftune` + the flag triple; the disable rides a cloned `CEMPWeapon` (B-18). **Loss:** the disable's duration is UNKNOWN on both sides; until B-18's probes run only the pulse ships. *UNAPPROVED*
- **T-WP3** (`next`, T-7) - BmAK: `RBatmobileMissileLauncher` `Batmobile_Missile_Launcher` (3 instances, 48 fields) + `RBatmobileMissile` `Batmobile_Missile_Projectile`. **Build instead:** `w618` clone, unguided; lock-on half UNKNOWN. **Loss:** the Missile Barrage locks nothing: no cone, no range, no hold - reopened by T-WP3b. *UNAPPROVED*
- **T-WP7** (`next`, T-7) - BmAK: `RBatmobileAllegianceSwitcher` `Drone_Hacker` (3 packages, 13 fields, 39 field rows, identical in every package): `BatmobileHackerEffect` -> `Particles.DroneHacker_Beam`, `SuccessfulHackEffect` ->.... **Build instead:** two `SAttachedEffect` rows + the SAM context-act hack + an authored side flip (B-19). **Loss:** the allegiance switch has no member on either side; the drone changes side only once B-19's authored flip holds. *UNAPPROVED*
- **T-WP8** (`next`, T-7) - BmAK: `RBatmobileSonar` `Batmobile_Sonar` (3 objects, 22 fields, 66 field rows, 0 differences across the three packages): `ScanParticle` -> `Particles.Batmobile_Seismic_Sonar` (205 B), `BlastParticle` ->.... **Build instead:** 0-damage `CForcePulse` + a private ring `.effc` + the `BML_Sonar` bank (B-20). **Loss:** the reveal/marker and the treadmark tracking are absent until B-20 authors them. *UNAPPROVED*
- **T-WP9** (`next`, T-7) - BmAK: `RPursuitModeMissileLauncher` `Vehicle_Tracker` (3 packages, 7 fields) + the tracker projectile (16 fields): `ProjectileArchetype` -> `Projectiles.Batmobile_Tracker_Projectile`, `LaunchSocketName` =.... **Build instead:** weapon entity + tracker tune + a HUD tracker graph (B-21). **Loss:** no homing flag and no distance member: the round homes and the readout appears only once B-21 authors them. *UNAPPROVED*
- **T-WP10** (`next`, T-7) - BmAK: `RBatmobileCannon (riot fields)` `Batmobile_Cannon_V2`: `RBatmobileCannon.RiotSuppressorImpactEffect` ref:Riot_Suppressor.Anti_firearm_gel_Miss, `RBatmobileCannon.RiotSuppressorTracerSystem`.... **Build instead:** `base_tuning.damage` 0 + impulse (closest system); the toggle is a second entity (B-15). **Loss:** 0 damage is not a non-lethal flag, and the riot/lethal toggle has no member until B-15 builds the second entity. *UNAPPROVED*
- **T-WP14** (`next`, T-7) - BmAK: `RBatmobileCannon` riot mode: `RiotSuppressorLockOnAngle` 7.5, `RiotSuppressorFiringInterval` 0.75, gel impact `ref:Riot_Suppressor.Anti_firearm_gel_Miss`. **Build instead:** the closest system (0-damage impulse tune); no per-weapon mode member. **Loss:** the riot-suppressor's 7.5 deg cone / 0.75 s cadence ride a second entity, not a toggle. *UNAPPROVED*

### sounds

- **T-AU3** (`next`, T-2b) - BmAK: 90 audio events across 10 banks drive the car, weapons and gadgets. **Build instead:** donor banks for 26 ids. **Loss:** 90 BmAK events in 10 banks are silent; 10 banks are not in the install. *UNAPPROVED*
- **T-AU5** (`next`, T-3) - BmAK: `TransformationReverseDirection*` sounds, `TaserSound`, `VehicleSound`. **Build instead:** engine bank only (T-AU2). **Loss:** transformation, taser and vehicle-voice events have no bank. *UNAPPROVED*
- **T-MD14** (`blocked`, T-15) - BmAK: switching pursuit/battle plays a transformation sting (3 variants). **Build instead:** no transformation sting. **Loss:** the mode-change sound (V2 62 / MK2 60 / Joker 191) never plays - a hybrid has no change. *UNAPPROVED*
- **T-AU4** (`edit`, T-2b) - BmAK: —. **Build instead:** `LandAudio.max_rpm` 4500 (follows the engine). **Loss:** BmAK's 10,000 rpm audio band is replaced by the translated engine's. *UNAPPROVED*

### look

- **T-MA4** (`next`, T-2b) - BmAK: authored gloss **0.600** (`VALUES.json` `paint.authored_gloss`), palette `clear_coat` 1.0. **Build instead:** gloss 0.45 (vanilla cap raised from 0.4 to reach it). **Loss:** BmAK's authored 0.6 gloss is not reproduced; the paint reads flatter. *UNAPPROVED*
- **T-MA7** (`next`, T-2b) - BmAK: no `Palette` in UE3 vehicles. **Build instead:** 10 palette tints kept. **Loss:** BmAK has no palette; the tint set is JC3's, not lore. *UNAPPROVED*
- **T-L10** (`next`, T-14) - BmAK: `ChainGunMuzzle` (stripped) → (none). **Build instead:** muzzle spot dropped (no weapon-light behaviour). **Loss:** the ChainGunMuzzle light (white spot, cone 50, R 4096) is gone. *UNAPPROVED*
- **T-L21** (`next`, T-14) - BmAK: `BattleModeSpotLight` VEHLT_ForensicsLight → (none). **Build instead:** forensics rig dropped. **Loss:** the scanner rig (12 entries) is absent. *UNAPPROVED*
- **T-L22** (`next`, T-14) - BmAK: `HeadLight1` VEHLT_ForensicsLight → (none). **Build instead:** forensics rig dropped. **Loss:** the red winch-door lamp is absent. *UNAPPROVED*
- **T-L23** (`next`, T-14) - BmAK: `HeadLight2` VEHLT_ForensicsLight → (none). **Build instead:** forensics rig dropped. **Loss:** the second red winch-door lamp is absent. *UNAPPROVED*
- **T-L25** (`next`, T-14) - BmAK: `HeadLight1a` VEHLT_HeadLight → HeadLight. **Build instead:** flare rides the lamp row; `SourceColor` not adopted. **Loss:** the headlight lens flare loses its own colour. *UNAPPROVED*
- **T-L26** (`next`, T-14) - BmAK: `HeadLight2a` VEHLT_HeadLight → HeadLight. **Build instead:** flare rides the lamp row. **Loss:** right headlight flare colour lost. *UNAPPROVED*
- **T-L27** (`next`, T-14) - BmAK: `HeadLight1b` VEHLT_HeadLight → HeadLight. **Build instead:** flare rides the lamp row. **Loss:** left headlight flare b lost. *UNAPPROVED*
- **T-L28** (`blocked`, T-14) - BmAK: `HeadLight1c` VEHLT_HeadLight → HeadLight. **Build instead:** omitted (socket absent). **Loss:** left headlight flare c has no anchor. *UNAPPROVED*
- **T-L29** (`next`, T-14) - BmAK: `HeadLight2b` VEHLT_HeadLight → HeadLight. **Build instead:** flare rides the lamp row. **Loss:** right headlight flare b lost. *UNAPPROVED*
- **T-L30** (`blocked`, T-14) - BmAK: `HeadLight2c` VEHLT_HeadLight → HeadLight. **Build instead:** omitted (socket absent). **Loss:** right headlight flare c has no anchor. *UNAPPROVED*
- **T-L31** (`next`, T-14) - BmAK: `RWheelLight_top` VEHLT_HeadLight → HeadLight. **Build instead:** flare rides the wheel lamp row. **Loss:** right wheel flare top colour lost. *UNAPPROVED*
- **T-L32** (`next`, T-14) - BmAK: `RWheelLight_bottom` VEHLT_HeadLight → HeadLight. **Build instead:** flare rides the wheel lamp row. **Loss:** right wheel flare bottom colour lost. *UNAPPROVED*
- **T-L33** (`next`, T-14) - BmAK: `LWheelLight_top` VEHLT_HeadLight → HeadLight. **Build instead:** flare rides the wheel lamp row. **Loss:** left wheel flare top colour lost. *UNAPPROVED*
- **T-L34** (`next`, T-14) - BmAK: `LWheelLight_bottom` VEHLT_HeadLight → HeadLight. **Build instead:** flare rides the wheel lamp row. **Loss:** left wheel flare bottom colour lost. *UNAPPROVED*
- **T-LG5** (`superseded`, T-2b) - BmAK: battle-mode/forensics rigs (16 + 12 entries). **Build instead:** battle spotlight mapped to HeadLight; forensics stays out. **Loss:** the forensics rig and its 12 entries are absent. *UNAPPROVED*
- **T-FX12** (`next`, T-13) - BmAK: G1-16 tracer: 16 systems / 4 names (Batmobile_Muzzleflash_NoTracer, Batmobile_Muzzleflash_NoTracer_Nv, Batmobile_Muzzleflash_Tracer...), 112 emitters, life 0.05..1.1 s. **Build instead:** tracer is a WeaponTuning texture, not an .effc. **Loss:** BmAK's tracer system (16 systems, 112 emitters) is not reproduced as authored. *UNAPPROVED*
- **T-FX13** (`next`, T-13) - BmAK: G1-16 casings: 8 systems / 2 names (ChainGun_BulletCasing, RiotSuppressor_BulletCasing), 40 emitters, life 0.05..1.1 s. **Build instead:** `ChainGunShells` socket stays empty. **Loss:** no gun ejects casings: 8 BmAK systems lost. *UNAPPROVED*
- **T-FX16** (`next`, T-13) - BmAK: G1-16 projectile-trail: 18 systems / 6 names (Batmobile_CanonTrail, Batmobile_JokersRocket_Trail, Batmobile_Mud_Trail...), 53 emitters, life 0.035..500.0 s. **Build instead:** no round trail; the round shows as a tracer. **Loss:** 6 BmAK projectile trails (18 systems) lost. *UNAPPROVED*

### handling

- **T-ST7** (`next`, T-3) - BmAK: `SteerSpeed` 220 °/s, `SpinSteeringFactor` 100000, steer-curve knots `InVal/OutVal/ArriveTangent/LeaveTangent`. **Build instead:** `t_to_full_steer_s` 0.8 low / 0.6 high. **Loss:** BmAK locks 55 deg in 0.25 s at 220 deg/s; the car steers 2.4-3.2x slower - reopened 2026-11-05. *UNAPPROVED*
- **T-MD7** (`blocked`, T-15) - BmAK: MOD-2. **Build instead:** one handling set (T-M1/T-S1/T-E3/T-ST1). **Loss:** the six battle drive/slip factors (drive force 500, lat slip 0.75, long slip 1.25, steer 1, trailing -0.25, Z offset 20 cm) are gone. *UNAPPROVED*
- **T-MD5** (`blocked`, T-15) - BmAK: MOD-2. **Build instead:** one top speed. **Loss:** the battle top-speed curve (60/40/30) has no carrier. *UNAPPROVED*
- **T-MD6** (`blocked`, T-15) - BmAK: MOD-2. **Build instead:** no 21.6 km/h cap. **Loss:** the turning-mode speed cap is absent. *UNAPPROVED*
- **T-MD13** (`blocked`, T-15) - BmAK: MOD-2. **Build instead:** static pose only. **Loss:** the animated transformation (3000/24000 torque factors) does not play. *UNAPPROVED*
- **T-S6** (`next`, T-3) - BmAK: `SuspensionTravelUp` 30, `SuspensionTravelDown` 40, `BMRearWheelMaxDroop` 100 (cm); `BM/PMWheelSuspensionStiffness` 3000/750, `SuspensionDamping` 300, `SuspensionBias` 50, `FrontWheelSuspensionBias` 10,.... **Build instead:** one stroke + one rate per axle. **Loss:** per-axle bias, droop (BMRearWheelMaxDroop 100) and undamped rate absent; stiffness 3000/750 has no unit bridge (strength 45). *UNAPPROVED*
- **T-S1** (`edit`, T-1) - BmAK: BmAK's rate pair exists and is named — `BMWheelSuspensionStiffness` **3000**, `BMWheelSuspensionDamping` **300** (archetype over all four cars, `CHAIN.json`) — but has **no unit bridge** to `strength`; that is T-S6's.... **Build instead:** `strength` 45/45 (fleet 6 t class). **Loss:** BmAK BMWheelSuspensionStiffness 3000 / damping 300 are not carried - no unit bridge. *UNAPPROVED*
- **T-S2** (`edit`, T-1) - BmAK: —. **Build instead:** `compression` 3.0. **Loss:** BmAK's damping has no member. *UNAPPROVED*
- **T-K1** (`edit`, T-1) - BmAK: `SVehicleSimCar.MaxBrakeTorque` **300** (archetype, all four sims) exists — but the bridge is disproven by magnitude, not assumed: 4 × 300 N·m over 6,000 kg × 0.683 m = **0.29 m/s²**, against the 3.5–3.8 m/s² we.... **Build instead:** max_brake_torque 5000 (class). **Loss:** BmAK MaxBrakeTorque 300 exists but the bridge is disproven by magnitude (0.29 vs 3.5 m/s2). *UNAPPROVED*
- **T-K2** (`next`, T-1) - BmAK: **no brake-lock member — now proven exhaustively**: `bmak_chain.py` over the full chain (`RVehicle → RVehicleBatmobileBase → RVehicleSimCar → RVehicleSimBatmobile → SVehicleSimCar → SVehicle`) finds `MaxBrakeTorque`.... **Build instead:** `min_time_to_block` 1 (donor value). **Loss:** BmAK's brake-lock time is unknown and the donor's is used; EbrakeTime 0.75 not carried. *UNAPPROVED*
- **T-K3** (`next`, T-1) - BmAK: none of `HandbrakeOnSpeed` 10000, `HandbrakeOffSpeed` 1.0, `HandbrakeLatSlipFactor` 1.5/1.1, `HandBrakeOffTime` 0.3 is a friction factor — but `EBrakeBrakeForce` **640,000** is a force whose **class default 160,000**.... **Build instead:** `handbrake_friction_factor` 1 (6 t median). **Loss:** BmAK HandbrakeOn/OffSpeed and lat-slip pair have no member. *UNAPPROVED*
- **T-K4** (`next`, T-3) - BmAK: `EbrakeTime` 0.75, `EBrakeBrakeForce` 640000, `HandbrakeOnSpeed` 10000, `HandbrakeOffSpeed` 1, `HandbrakeLatSlipFactor` 1.5 front / 1.1 rear (all four wheels), `HandBrakeOffTime` 0.3. **Build instead:** rear-only handbrake, factor 1. **Loss:** EBrakeBrakeForce 640000 has no member. *UNAPPROVED*
- **T-ST3** (`next`, T-1) - BmAK: `SteerSpeedVsSpeedCurve` **flat 720 °/s**; the high-speed lock is T-ST1's 20°. **Build instead:** 0.6 s high-speed steer time. **Loss:** BmAK's 0.25 s is not reachable (same limit as T-ST7). *UNAPPROVED*
- **T-ST5** (`next`, T-1) - BmAK: **the members exist** — every steering-rate modifier in the chain reads neutral: `DriftCorrectionSteerSpeed` **1.0** (`RVehicleBatmobileBase`), `SteeringSpeedReCentreMod` **1.0** (`RVehicleSimCar`),.... **Build instead:** countersteer / steer_in 1.0 / 1.0 (BmAK's own neutral values). **Loss:** no countersteer gain exists on either side; the row keeps neutrality. *UNAPPROVED*
- **T-ST6** (`next`, T-1) - BmAK: rear `LatSlipFactor` **1.6** (front inherited; no `*Align*` member anywhere — the quantity, not the name, is what translates, `CHAIN.json` 12366/12424). **Build instead:** drift aligning 0.3 (fleet band). **Loss:** BmAK's aligning rate has no member. *UNAPPROVED*
- **T-B2** (`next`, T-1) - BmAK: **the additive member exists**: `FakeExtraSpeedMax` **3500** cu, `FakeExtaSpeedAccel` **600** cu/s², `FakeExtaSpeedDecel` 2000, `BoostDuration` **2.0 s** (class default, no archetype override), `InfiniteBoost` false.... **Build instead:** nitro extra_top_speed 43.2 km/h (derived from BmAK). **Loss:** BmAK's FakeExtraSpeedMax 3500 is capped by accel x duration (1200 cu) - a lower bound, not the authored max. *UNAPPROVED*
- **T-B3** (`next`, T-1) - BmAK: **absence now proven, and absence means identity**: `OFFSETS.json` (G1-1: 423/423 fields named) carries no `*grip*`/`*traction*` field anywhere, and `bmak_chain.py --grep 'Grip. **Build instead:** nitro grip 1.0 (identity). **Loss:** BmAK boost touches no grip member, so grip under boost is JC3's, below the shipped 1.2..2 band. *UNAPPROVED*
- **T-DR1** (`next`, T-3) - BmAK: `LatSlipFactor` 1.6, `HandbrakeLatSlipFactor` 1.5/1.1, `HandbrakeOnSpeed` 10000 cm/s, `DriftCorrectionSteerSpeed` 1.0, `DriftSteeringAssist` absent, `DriftingBoostCooldown` 1.5 s. **Build instead:** JC3-native drift block (sens 4, entry 20). **Loss:** the drift feel is JC3's, deliberately not the 6 t class. *UNAPPROVED*
- **T-E2** (`next`, T-1) - BmAK: lore power **1200 bhp**; BmAK has **no absolute torque** (curve only, `CHAIN.json`). **Build instead:** absolute torque 1393.5. **Loss:** BmAK's torque curve scale is a class fit (+30%), not the authored number. *UNAPPROVED*
- **T-E5** (`next`, T-1) - BmAK: wiki 209 mph (336 km/h) with afterburner; BmAK has **no speed member**. **Build instead:** top speed 336 km/h (wiki 209 mph). **Loss:** the only source is a wiki figure, inside the fleet band but not decoded. *UNAPPROVED*
- **T-M2** (`edit`, T-1) - BmAK: — (**no absolute inertia tag**: `InertiaTensorMultiplier` [1, 1, 1] is neutral, so the sim scales an inertia the streams never store, `CHAIN.json`). **Build instead:** inertia 4.0/2.6/1.2 (class). **Loss:** BmAK's inertia tensor is a neutral multiplier - no authored value exists. *UNAPPROVED*
- **T-M4** (`edit`, T-1) - BmAK: — (**no wheel-mass member**: the chain over `SVehicleWheel` finds only `MassScale` 1.0, neutral, `CHAIN.json`). **Build instead:** wheel mass 75/150 (class). **Loss:** BmAK has no wheel-mass member (MassScale 1.0 neutral). *UNAPPROVED*
- **T-R1** (`edit`, T-1) - BmAK: — (**no friction tag anywhere**: `bmak_chain.py --grep 'Friction. **Build instead:** arcade friction 3.0. **Loss:** BmAK has no friction tag; the grip is a fleet value. *UNAPPROVED*
- **T-A2** (`edit`, T-1) - BmAK: — (**no aero member anywhere**: chain grep `Drag. **Build instead:** drag 0.55. **Loss:** BmAK has no aero member; drag is JC3's. *UNAPPROVED*
- **T-A4** (`edit`, T-1) - BmAK: — (no lift/downforce member either; the chain proof is T-A2's). **Build instead:** lift -0.3. **Loss:** BmAK has no downforce member; lift is JC3's. *UNAPPROVED*
- **T-G6** (`keep`, T-3) - BmAK: `SVehicleWheel.WheelRadius` = 64.0. **Build instead:** contact radius 0.683 (mesh). **Loss:** BmAK's sim radius 0.64 is not carried. *UNAPPROVED*

### collision

- **T-DM7** (`next`, T-3) - BmAK: `ImpactMinDamageSpeed` 20 (class 60), `ImpactMaxDamageSpeed` 150 (class 200), `ImpactStrafeMod` 2.25 (class 1.5), `ImpactBoostMod` 2.0 (class 1.5), `ImpactCivilianVehicleMod` 1.0 (class only, not serialised),.... **Build instead:** `rotor_collision.damage_to_other_per_second` 100000/s + mass ratios. **Loss:** BmAK's outgoing ram damage is a 20->150 speed band with strafe 2.25 and boost 2.0; JC3's member is a per-second rate, so the band is a named omission and a `CCar` evaluating the block is UNKNOWN. *UNAPPROVED*
- **T-DM2** (`edit`, T-2b) - BmAK: —. **Build instead:** bullet armour 99 (fleet max). **Loss:** BmAK's authored bullet armour is above the fleet gate. *UNAPPROVED*
- **T-DM6** (`next`, T-2b) - BmAK: **UNKNOWN** whether AK deforms panels: the record proves a destroyed mesh, damage masks and a `Damage_States` package, not panel deformation (`card-G1X.md` §6c). **Build instead:** `deform_scale` 0 (no crumple). **Loss:** BmAK panels deform in play; the switch is off. *UNAPPROVED*
- **T-DM1** (`next`, T-2b) - BmAK: `RVehicleBatmobile.Health` = **1,200** (3 archetypes). **Build instead:** max_health 36000 (out of shipped domain). **Loss:** BmAK Health 1200 becomes a declared switch 30x the authored value. *UNAPPROVED*
- **T-AC1** (`next`, T-3) - BmAK: `AirControlYawTorqueFactorMax` 8000 (mid-air yaw authority; the 1.212 s airborne window is F-6). **Build instead:** closest system: `drift.max_drift_torque` 8000 + aero `turn/pitch_steering_factor` 0.2286. **Loss:** JC3 has no airborne gate, so the yaw acts only while the drift state survives take-off. *UNAPPROVED*
- **T-RA1** (`blocked`, T-3) - BmAK: `ImpactRoadAssist*` (90000 / 30000 / 2000), `PMDodge*` (5000 / 6000 / 0.25 s), `BattleDodgeImpulse` 100000, `VehicleShovingTorque` 10000, `KillFlip*` (−2000000 over 1.5 s), `KillKeepyUp*`, `ImpactShake*`. **Build instead:** blocked: none at any layer; G2-35 names the capability to add. **Loss:** ImpactRoadAssist 90000/30000/2000, PMDodge 5000/6000/0.25 s, BattleDodgeImpulse 100000, VehicleShovingTorque 10000 and KillFlip -2000000 over 1.5 s have no triggered member with a target or a duration. *UNAPPROVED*
- **T-SR1** (`next`, T-3) - BmAK: `JumpRampRightingTorque` 2000, `JumpNoRampRightingTorque` 2000, `StayUprightConstraintSetup/Instance`. **Build instead:** closest system: `DriverLean.righting_torque` 2000 + the Havok stabilizer atom. **Loss:** no car ships `DriverLean`, and the StayUpright stiffness/damping/resist angles have no JC3 member. *UNAPPROVED*
- **T-WLD11** (`next`, T-20) - BmAK: WLD-4. **Build instead:** the 2-column spine fit is narrow (0.28-0.60 m) versus the donor's 1.65 m blanket; 1/40 and 16/80 interior samples still dip into the roof vents. **Loss:** Rico stands on the derived spine, but the donor's full-width hood/roof blanket needs a third column and deform indices above 134. *UNAPPROVED*
- **T-WLD15** (`next`, T-20) - BmAK: WLD-7. **Build instead:** translated to `CVehicleCargoBay`/`CGrapplingHookPropData` + mass 6,000; the pull is native. **Loss:** whether the tether holds a 6 t car is unverified (Q-3 #5). *UNAPPROVED*
- **T-WLD17** (`blocked`, T-20) - BmAK: WLD-7. **Build instead:** 0 of 23 helicopters has a cargo bay; closest is the plane's bay + compound entity (B-16). **Loss:** helicopter airlift cannot happen until a bay is cloned and its native attach rule probed. *UNAPPROVED*

## 2. APPROVED (a file quotes the operator)

| row | what is lost | approval | cited |
|---|---|---|---|
| T-WP6 | the Power Winch does not pull until B-16's loop exists; the 2026-11-05 d-pad RIGHT decision stands | WINCH | `Research/BatmobileGrab/CONTROLS_MENU_SCREENS.md:50` - "DECIDED (operator, 2026-11-05): the winch takes d-pad RIGHT and REPLACES Mission Select" |

## 3. "JC3 cannot" closures the 2026-11-05 leads reopen

| feature | row | closed as | what the lead says | evidence |
|---|---|---|---|---|
| 11 weapons / 8 lost | T-WP13 | 2 driver slots, no active-slot index | T-WP13's own proposal kept 3 addressable and 8 lost; D-7 asks for all 11 | T_WP13_PROPOSAL.md:18 (3 addressable / 8 lost) |
| 0.25 s steering | T-ST7 | 0.6-0.8 s, fleet rack floor 0.5 s | BmAK 220 deg/s = 0.25 s; the row called it a JC3 model limit | DRIVE_CARRIERS.md section 4/7 (no pivot/steer-through-torque carrier) + the 2026-11-05 lead |
| Real BmAK sounds | T-AU3 | donor banks for 26 ids | 10 BmAK banks are absent from the install, so the row stops | T-AU3/T-AU5 `why` (banks absent), no re-decode attempted since |
| Heat-seeking / lock-on | T-WP3 | unguided `w618`; lock-on UNKNOWN | T-WP3b found `missile_turning_speed` and the lock-on AutoAim preset | T_WP3B_LOCKON.md sections 1-3; JC3_HUD_WEAPONS.md section 5 |
| Hackable drones | T-WP7 | no allegiance class | 0 hits in the 103-class census; the lead says JC3 has hackable drones | ENTITIES.md census (0 classes), T-WP7 `why` |
| Stunt areas | T-WLD11 | areas float 0.10-0.60 m; deform list missing | the 0.10-0.60 m figure is the bbox map; the stored points sink 0.19-0.31 m and the derived spine fit places 22/22 vertices, so the carrier exists | tmp/freebuff/reports/stunt-areas-deform-points.md; T_WLD11B_SURFACES.md |

Each of these is an **UNAPPROVED** compromise until a file records the operator accepting the loss; a lead that narrows where to look is not an acceptance, and reopening a closure does not by itself approve the omission it left behind.

### 3.1 The 8 weapons the first T-WP13 pass declared lost

`T_WP13_PROPOSAL.md:18` records **3 addressable** (2 decoded binds + 1 index with no member) and **8 lost**: WPN-4 EMP missile, WPN-5 EMP burst, WPN-6 winch, WPN-7 hacker, WPN-8 sonar, WPN-9 tracker, WPN-10 riot suppressor, WPN-11 booster mesh. Of those, one is approved (WPN-6 winch -> tether, 2026-11-05); WPN-10's 2026-10-28 approval is **superseded** by the 2026-11-06 operator rule and its row is now `next` (closest system: a 0-damage impulse tune; the toggle is BUILD card `Research/specs/B-15.md`), and seven are UNAPPROVED. The ninth and tenth weapons (cannon, Vulcan) have slots; the missiles are the third addressable row but carry no lock-on (T-WP3).

## 4. Approval citations that do not exist, and rows kept out of the ranked list

The 2026-11-05 instruction says the exact-colour decision is recorded in `Research/BatmobileGrab/CONTROLS_MENU_SCREENS.md`. **That file contains no colour statement** - it records the controls, the winch and the AR/Mission Select drops only. Note that the colour itself is not compromised: T-MA3 keeps the authored base colour `[0.02579, 0.02579, 0.03]` linear through the linear->sRGB gain, so no decision is needed for it. The one colour row that loses something is T-MA4 (authored gloss 0.6 -> 0.45), and it is listed as UNAPPROVED above, not approved; the citation gap is reported rather than filled:

- searched: all 52 lines of `CONTROLS_MENU_SCREENS.md` for `colour`, `color`, `lighting` and `exact`; 0 hits for the first three, and `exact` matches only line 4's "labels are exactly as drawn". No colour or lighting decision is recorded there.

| row | why it is not in the ranked list |
|---|---|
| T-FX9 | carried since 2026-11-06: `car_speedrom_heater.effc` at the `Afterburner` socket (12 vehicles, 24 `z80_exhaust_heat_l/r` attachments); the gap is the blend/texture name, not a value |
| T-FX20 | carried as an authoring plan since 2026-11-06: no light or ribbon member and no `Brake` behaviour exist to convert, so nothing is lost; the trigger is build work |
| T-L4 | superseded by T-L13/T-L14 - the wheel lamp is carried by a custom entry |
| T-L7 | superseded by T-L35 - the boot lamp is carried by a custom entry |
| T-LG4 | superseded by T-L13/T-L14 - the under-glow is carried |
| T-FX4 | superseded by T-11/T-17; the seismic half is counted under T-WP8 |
| T-W1 | superseded by T-11 - the 11 weapons are counted row by row |
| T-WLD4 | carried: the shipped `_debug` leaf's name key 1621485476 is present 11/11 in bm-013's drop (BATMOBILE); 443190071 belonged to a leaf that never ships |
| T-WLD6 | carried: the `_debug_desc` key 4081821928 is present 11/11 in bm-013's drop with the Batmobile blurb |

## 5. Method, counts and limits

- Universe: all 199 rows of `T_ROWS.jsonl`. Inclusion rule: the row drops a BmAK feature, keeps a JC3/donor/fleet value where BmAK has one, shrinks or merges a feature, or records a permanent omission. 72 rows qualify; 9 were examined and excluded with the reason in section 4.
- Counts are computed by the script from `dispo`, never typed: `blocked` 11, `edit` 10, `keep` 1, `next` 48, `superseded` 2.
- `what BmAK does` is read from each row's own `cells[1]`; this file never re-types a BmAK value, so a corrected row cannot leave a stale quote behind.
- `--check` asserts every audited id exists in `T_ROWS.jsonl`, every APPROVED row's quote is still at the cited line of the cited file, and the rendered markdown/JSON match a fresh re-derivation.

**Limits.** This is a reading of the ledger, not a re-decode: it does not re-prove any absence. Rows that are `blocked` but not permanent (T-WP4/T-WP5/T-WP13) are counted as compromises because a blocked row ships the omission today. The audit does not touch `T_ROWS.jsonl`, the backlog or any build.

Checkable: `python Tools/scripts/audit_compromises_t.py --check`.
