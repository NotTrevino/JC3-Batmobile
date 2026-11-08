STATUS: done. Every brought-forward feature is matched to a row, a T_ROWS id or an Appearance/T-21 entry, except **three features with no row at all** (summon/call, remote piloting, Batwing vertical drop) and **one row whose premise the grab contradicts** (MOD-5). Two features the operator asked about do not exist in the source at all (siren, horn) — that is a decoded negative, not a missing row. Nothing in `GRAB_BACKLOG.md` or `Working/Translation/T_ROWS.jsonl` was edited.

# BmAK feature completeness audit

Question: what does the Batmobile *do* in Arkham Knight, and does every behaviour have a row? Covered = a `GRAB_BACKLOG.md` feature code (APP/DIM/ARM/WPN/HDL/MOD/AUD/ANI/WLD/LGT/FX/CAM/HUD), a `T_ROWS.jsonl` id, or an Appearance/T-21 entry. Labels: **decoded** (read from the shipped files), **derived** (computed from decoded values), **UNKNOWN** (evidence absent; what would settle it is named).

Sources read for this audit: `Research/BatmobileGrab/{objects.jsonl (20,128 objects), MODES.md, DRIVE_MODES.md, GADGET_PARAMS.md, ANIMATIONS.md, AUDIO_FEATURES.md, AUDIO_BANKS.md, HUD.md, LIGHTS.md, COVERAGE.md, GAPS.md, MECHANICS.md}`, `Research/BatmobileGrab/BMSDK_OFFSETS.json` (present, not needed for these rows — the bindings `.g.cs` cited inside `GADGET_PARAMS.md` already name every member), `GRAB_BACKLOG.md` (§1 feature codes, §12 tracker), `Working/Translation/T_ROWS.jsonl` (198 rows).

## 1. The match table — features that have a row

| # | feature | BmAK evidence (file : key) | covering row | label |
|---:|---|---|---|---|
| 1 | Body, scale, 5 LODs, 19 slots | `MESHES.md`, `SLOTS.json` (`@`APP-1) | APP-1, T-G1, T-21 | decoded |
| 2 | Paint/armour look, noon + night | `MATERIALS.md`, `COLOUR_PARAMS.md` (BaseColour [0.0258,0.0258,0.03]) | APP-2, T-21 (`D`-classes in `APPEARANCE_PLAN.md`) | decoded |
| 3 | Canopy glass + visible cockpit | `SLOTS.json` Window block, `COCKPIT.md` | APP-3, T-21 | decoded |
| 4 | Emissive lenses, tail strip, arch lights, dashboard | `LIGHTS.md:19` (129 components, colour 129/129) | APP-4, T-L24/T-L35 | decoded |
| 5 | Movable parts split (turret, cannon, Vulcan, fins, hatches, fan, canopy, yoke) | `ANIMATIONS.md:65-78` (10 mechanism classes) | APP-5, T-12/T8_PARTS (12/15 parts covered), T-PA9 | decoded |
| 6 | Battle-mode silhouette reachable | `ANIMATIONS.md:333` transform set (32 `transformation` sequences) | APP-6, MOD-2, T-MD13 (named omission) | decoded |
| 7 | No deformation, scorch/smoke only | `PHYSICS.md` (no chassis body), damage rules G1-14 | APP-7, ARM-6, T-DM rows | decoded |
| 8 | Dimensions, wheelbase, track | `bat_assemble.py` / PSKX | DIM-1, T-G1 | decoded |
| 9 | Tyre Ø 1.365–1.366 m | `TYRES.md` | DIM-2, T-G2/T-G3 | decoded |
| 10 | Mass (6 t class) | no absolute mass tag (`INERTIA.md`, T-M1) | DIM-3, T-M1 (`out`, named) | UNKNOWN (no source value) |
| 11 | Collision hull = Batmobile body | `COLLISION.md`, `COLLISION_FRAME.md` (7/7) | DIM-4, T-CO1..3, B-10/B-10c | decoded |
| 12 | Small arms do not move the bar | play behaviour, `DAMAGE_RULES.md` | ARM-1, T-DM9, T-MD2 | derived |
| 13 | Heavy weapons damage; car destroyable | `RVehicleBatmobile.Health` 1,200 | ARM-2, T-DM1 | decoded |
| 14 | Ramming never damages the car | `impact_damage_factor` | ARM-3, T-DM8 | decoded |
| 15 | Wheels cannot be shot off | BmAK has no wheel damage | ARM-4, T-DM4 | decoded |
| 16 | Battle-mode armour reduction | `ArmourModeDamageReduction*` 1/1 serialised (`MODES.md:42`) | ARM-5, T-BM1 | decoded |
| 17 | 60 mm cannon, Vulcan, missiles, EMP missile, EMP burst, winch, drone hacker, sonar, tracker, riot suppressor, booster | `COVERAGE.md` "By class" (11 weapon classes, 261 `T-W1` fields) | WPN-1..12, T-WP1..14 | decoded |
| 18 | Riot-suppressor *target* binding | `CurrentRiotSuppressorTarget`, `RiotSuppressorBatmobile` (`GADGET_PARAMS.md:76,79`) | WPN-10 (decision D-3), T-WP13 | decoded |
| 19 | Top speed, torque curve, nitro tiers | `MECHANICS.md`, T-E1..E5, T-B1..B3 | HDL-1..4 | decoded |
| 20 | Suspension stroke 0.70 m, landing | `T-S3` (`SuspensionTravelUp` 30 / `Down` 4) | HDL-5, T-S3, T-S6 | decoded |
| 21 | Air control / self-righting | `AirControl*` 1/8, `StayUpright*` 2/6, `JumpRamp*` (`MODES.md:43,44,50`) | HDL-6, T-AC1, **T-SR1**, T-AC1 | decoded |
| 22 | Battle dodge, PM dodge, kill-flip, keepy-up, shove torque, road-assist | `BattleDodgeImpulse` 1/1, `PMDodge*` 3/3, `KillFlip*` 2/2, `KillKeepyUp*` 2/2, `VehicleShovingTorque` 1/1, `ImpactRoadAssist*` 5/10 | **T-RA1** (names all six families), T-3 doc | decoded |
| 23 | Pursuit mode (afterburner, Immobilizer, ram immunity, speed) | `DRIVE_MODES.md:148` `PursuitMode.BeginState` 10515, `:161` Tick, `EBatmobileDriveMode` `:9` | MOD-1, T-BM1 | decoded |
| 24 | Battle mode (turret, turn on spot, low top speed, battle FOV 60) | `DRIVE_MODES.md:192` `BattleMode.BeginState` 10529, `MODES.md:37` 42 `BattleMode*` declared | MOD-2, T-BM1, T-CAM2 proposal | decoded |
| 25 | Pursuit↔battle↔zoom HUD machine | `HUD.md` §4: `SetBattleAndZoomMode`, labels `DRIVETOBATTLE`… | HUD-1, MOD-2, T-19 | decoded |
| 26 | Eject (hold) + Batman glides | `EJECT_MOVE.md`, `EJECT_VELOCITY.md`, G3-02j (eject velocity (0,0,0) on the car mesh) | MOD-3, T-13, T-WLD rows | decoded |
| 27 | Canopy opens on entry/exit | `Batmobile_Skel_Ctrl_Door`; `ANIMATIONS.md:65-78` canopy 20 sequences | MOD-4, ANI-8, P-06 (20 rows) | decoded |
| 28 | Entry/exit interaction points | `COCKPIT.md` (seat), T-13 (85 objects, 77 placed) | WLD-3, T-13 | decoded |
| 29 | Rebel Drop entry, name, icon | `REBELDROP.md`, B-13 | WLD-1, WLD-2, B-13 | decoded |
| 30 | Stunt/roof standing | `point.stunt*` | WLD-4 | decoded |
| 31 | Heavy shove, no traffic copies | mass; `T-WLD18/T-WLD19` (traffic record) | WLD-5, WLD-8 | decoded |
| 32 | Water (not amphibious) | `WATER.md` (`will_sink` on 189/232) | WLD-6, T-MD? | decoded |
| 33 | Tether/airlift with 6 t | `TETHER.md` | WLD-7 | decoded |
| 34 | Headlights, high beams, tail/brake, arch, boot, dashboard | `LIGHTS.md:19` `VEHLT_HeadLight=46`, `VEHLT_TailLight=8`, `VEHLT_BootLight=3`, `VEHLT_Interior=4` | LGT-1, T-L8/T-L9, T-L11/T-L12, T-L15/T-L16, T-L24, T-L35 | decoded |
| 35 | Battle-mode spotlight | `LIGHTS.md:19` `VEHLT_BattleModeLight=16` | LGT-2, **T-MD12** ("battle lights", 4 entries T-L17–T-L20) | decoded |
| 36 | Forensics light rig | `LIGHTS.md:19` `VEHLT_ForensicsLight=12` | LGT-2 sibling, T-L21 (named omission) | decoded |
| 37 | Lens flares on every lamp | `LIGHTS.md` components = `LensFlareComponent` 55 | FX-2/lens-flare carrier report | decoded (JC3 has no flare — gap named) |
| 38 | Afterburner flame + heat haze | `PARTICLES_FEATURES.md`, `FX9_HAZE.md` | FX-1, T-FX3/T-FX9 | decoded |
| 39 | Muzzle flash, tracers, casings, missile trails, impacts | `AUDIO_FEATURES.md` groups, `FX13_CASINGS.md` | FX-2, T-FX12/T-FX13/T-FX16 | decoded |
| 40 | Tyre smoke, sparks, brake trails | `tire_effects` | FX-3, T-EF1, T-FX20 | decoded |
| 41 | Death explosion, burn without deform | `DeathExplosionSoundArray` | FX-4, ARM-6 | decoded |
| 42 | Chase camera 55…63° vertical, 400 cm boom | `CAMERA.md`, `DrivingCamConfig1/2` 400/400 | CAM-1, G3d | decoded |
| 43 | Battle camera FOV 60 | `BattleModeCamFOV` 60.0 (calibration F-11) | CAM-2, T-CAM2 proposal | decoded |
| 44 | HUD: health bar + armour tiers | `HUD.md` §4.1 contract (`MaxHealthChangePerFrame` 0.05, 2 s timer) | HUD-1, T-19 (`t19_hud.py` 10 rows) | decoded |
| 45 | HUD: boost gauge, cannon cooldown, weapon slots, lock-on, combo, winch meter, energy charges | `HUD.md` §4 setters table | HUD-1/HUD-2, T-19, WPN-12 | decoded |
| 46 | Lock-on and missile boxes (two independent paths) | `HUD.md` §5.1 (`HudModuleTargets` + local radar) | HUD-2, T-HUD5 | decoded |
| 47 | Engine start/idle/rev by RPM | `AUDIO_FEATURES.md:193` engine group | AUD-1, T-AU1/T-AU2 | decoded |
| 48 | Boost roar, burnout | `AUDIO_FEATURES.md:184,216` | AUD-2, T-AU1 | decoded |
| 49 | Interior layer | `AUDIO_FEATURES.md:231` | AUD-3, A-11 (named omission) | decoded |
| 50 | Battle transform in/out sound | `Play_BattleMode_In_Rev`/`_Out_Rev` | AUD-4, W-08 (120 rows) | decoded |
| 51 | Weapon fire/loop/tail/impact/lock beep | `AUDIO_FEATURES.md:176` | AUD-5, W-03/T-AU5 | decoded |
| 52 | Impact/death/voice/sonar/tracker audio | `AUDIO_FEATURES.md:38-58` (14 groups, 361 rows) | AUD-1..6, T-AU3/A-01 | decoded |
| 53 | Wheel spin/steer, turret yaw, cannon pitch, Vulcan spin, fan, fins, hatches, yoke, seat pose | `ANIMATIONS.md:65-78` (253 sequences, 9 rows) | ANI-1..9, T-PA4, P-01/P-02/P-03/P-07/P-09 | decoded |
| 54 | Occupant HUD, virus upload, forensic tracking, medallions | `HUD.md` §4 setters (`UC_SetOccupant`, `UC_SetVirusUploadState`) | HUD-1 (named omission) | decoded |
| 55 | Armour tiers / XP / combo display | `HUD.md` §4 (`UC_SetXpLevel`, `UC_SetBatmobileCombo`) | HUD-1 | decoded |

## 2. UNCOVERED — features with no row anywhere

Checked mechanically: `summon` = **0** hits in `GRAB_BACKLOG.md` and in the whole grab; `Remote`/`remote` = 0 hits in `T_ROWS.jsonl`; `rescue` = 0 hits in both. The only backlog mention of the remote gadget is `GRAB_BACKLOG.md:967` — "not read at all: `Gad_RBatmobileRemoteBm_SF` (remote-control gadget)" — i.e. the project *knows* the package is unread and has no row for what it does. `GAPS.md:160` lists it among the excluded packages.

### U-1 · Summon / call the Batmobile

- **Evidence (decoded)**: `GADGET_PARAMS.md:1` — the class `BmScript.RBatmobileRemoteBm` has **48 parameters**, 23 with values; `:59` `RemoteControlBatmobileMove` = `Batmobile_Remote.RemoteControlBatmobile` (`RSpecialMoveConfigConfigurable`); `:60` `CallSound` = `Engine.Play_Gauntlet_Batmobile_Call` (AkEvent); `:78` `CallingVehicle` (object ref, value UNKNOWN — no tag in the CDO); `:103` `NotifyRemoteDriveCancelled`; `:109` `NotifyReachedHardRemoteLimit`. CDO payloads read from both `Startup.upk` 536 @362 and `StartupPatch.upk` 520 @362 (`:17-18`), so the class ships in the shipped build.
- **Closest JC3 system (STAGES rule)**: the **Rebel Drop path already built** — `profile/item.onlinec` entry + `settings/spawn_vehicle_defs.bin` record (WLD-1, B-13, T-WLD18). JC3 does summon a vehicle to a *drop marker*; it has no call-to-player.
- **The gap the build must fill**: delivery at the player instead of at a designated drop zone, plus the call feedback (sound + HUD screen). JC3's spawn is anchored to a drop point, so the build needs either a payload that spawns the car at the player's coordinates or a drop-zone entry the player is always inside.
- **What the grab still needs**: the 25 behaviour-member bodies of `RBatmobileRemoteBm` (`GADGET_PARAMS.md:81` — no values exist, so the call distance, delay and spawn offset are inside script that has not been decoded); the `RemoteControlBatmobile` special-move config; the WEMs behind `Play_Gauntlet_Batmobile_Call`.
- **Proposed tracker row** (do not insert yet — operator approves): `T-WLD20 · summon/call — RBatmobileRemoteBm call path (CallSound Engine.Play_Gauntlet_Batmobile_Call, CallingVehicle, NotifyRemoteDriveCancelled); closest = B-13 drop + spawn_vehicle_defs; gap = at-player delivery; grab needed = the CallVehicle/RemoteDrive function bodies (25 members) + Batmobile_Remote.RemoteControlBatmobile; proof = a drop lands within 2 m of the player and the call event plays.`

### U-2 · Remote piloting (cursor-steered, jammed, hard-limited)

- **Evidence (decoded)**: `GADGET_PARAMS.md:48-64` — `CursorSpeed` 3.0, `CursorAccel` 5.0, `CursorDecel` 10.0, `CursorReturnDelay` 2.0, `CursorReturnFactor` 2.0, `MaxAimX` 0.9, `MaxAimY` 0.9, `RelativeAimingCurvePower` 1.0, `CurrentJam` −1.0, `JammerTime` 1.5 s, `JammingRange` 10000.0; `:59` the move config; `:103/:109` cancel and limit notifies; `:166` `RInventoryGadget.AssociatedGadgetFlagName` = `"Equip_BatmobileRemote"`; `:125` gadget `Mesh` = `Default__RBatmobileRemoteBm.GadgetMesh`. `GADGET_PARAMS.md:73-79` — `bRelativeAiming`, `ScreenOn`, `ReachedRemoteHardLimitThought`, `CurrentRiotSuppressorTarget`, `NpcBatmobileTarget`, `CallingVehicle`, `RiotSuppressorBatmobile` are **UNKNOWN values** (no tag in either CDO).
- **Closest JC3 system**: JC3's **AI-driven vehicles** (traffic and chase AI, `TRAFFIC.md`/G2-29, 11,751 data-table files) plus a camera override. Nothing in JC3 lets a player steer a vehicle from outside it.
- **The gap**: an input path that takes a reticle position and drives the car — the reverse of JC3's design, where input belongs to the driven vehicle. Requires either a native hook (route list in `tmp/freebuff/reports/new-behaviour-routes-survey.md`) or an AI-driver tune the reticle feeds.
- **What the grab still needs**: `bRelativeAiming`/`ScreenOn` (UNKNOWN in the CDO), the 25 behaviour bodies, and the `RSpecialMoveConfigConfigurable` config that `RemoteControlBatmobileMove` points at.
- **Proposed row**: `T-WLD21 · remote piloting — cursor steering (CursorSpeed 3.0 / Accel 5.0 / Decel 10.0, return 2.0 s ×2.0, MaxAim 0.9, JammingRange 10000, JammerTime 1.5, NotifyReachedHardRemoteLimit); closest = JC3 AI-driver + camera override; gap = player-steer from an external reticle; grab needed = RemoteControlBatmobile config + bRelativeAiming/ScreenOn; proof = the car reaches a reticle target without a driver and refuses past the hard limit.`

### U-3 · Batwing vertical drop / rescue delivery

- **Evidence (decoded)**: `ANIMATIONS.md:46` AnimSet `Batwing_Rescue` in `Playable_BatmobileJoker_SF` (484 tracks), `:49` AnimTree `Batwing_Vehicle_AnimTree`; `:333-336` four sequences — `Batwing_Rescue_01` (149 b, 4.933 s), `Batmobile_Vertical_Rescue_In` (218 b, 7.233 s), `_Idle` (113 b), `_Out` (133 b, 4.400 s); `:628` the set section; `:1260-1268` script notifies `ActivateHovering`, `ActivateExhaust`, `DeactivateHovering`, `ActivateBoosters`, `DestroyMe`, **`DropBatmobile`** at 0.488 s, **`CheckDropBatmobile`** at 1.868 s. `AUDIO_FEATURES.md:257` — the `other` audio group is literally "rows no rule matched: rain, world objects, **the Batwing line**", i.e. that audio has no owning feature row.
- **Closest JC3 system**: the **cargo-plane / helicopter airlift** path (WLD-7, `TETHER.md`/G2-34) and the Rebel Drop airdrop. JC3 drops *Rico and cargo*; it has no vehicle-carrier delivery.
- **The gap**: a carrier entity that holds the car, a drop event and the release. The carrier does not exist in JC3; the closest is a helicopter/plane with a tether payload that releases.
- **What the grab still needs**: the four sequences' **key frames** — `ANIMATIONS.md:1342` says they are outside the repository, so the exact drop height and timing are UNKNOWN; and the `DropBatmobile`/`CheckDropBatmobile` notify handler bodies.
- **Proposed row**: `T-WLD22 · Batwing vertical drop — AnimSet Batwing_Rescue (484 tracks) + BatMobile_Vertical_Rescue_In/Idle/Out, notifies DropBatmobile (0.488 s) / CheckDropBatmobile (1.868 s); closest = cargo-plane airlift (WLD-7) or Rebel Drop airdrop; gap = a carrier entity + drop event; grab needed = key frames (outside repo) + notify bodies; proof = the car is released at the decoded height and lands within the suspension's 0.70 m stroke.`

Also uncovered as **audio rows**: `T-AU8 · call/remote gadget audio — Engine.Play_Gauntlet_Batmobile_Call, Engine.Play_Remote_Gadget_Off, Ww_CHR_RemoteGadget.Play_Remote_Gadget (×2, Fire/Cancel), GADGET_PARAMS.md:60-63; closest = a donor AkEvent on a vehicle bank (G2-24); gap = no JC3 call event; grab needed = whether those three WEMs are in the grabbed banks.`
And **inventory**: `T-MD16 · remote-gadget equip entry — RInventoryGadget.AssociatedGadgetFlagName "Equip_BatmobileRemote" + GadgetMesh (GADGET_PARAMS.md:166,125); closest = JC3 profile flag (UNKNOWN); gap = no vehicle gadget wheel; grab needed = a JC3 equip-flag equivalent.`

## 3. A row that the grab contradicts — MOD-5

`GRAB_BACKLOG.md` MOD-5 reads "Nobody but the player drives it: no NPC hijack, no traffic copies" and cites lore. The grab says otherwise:

- `DRIVE_MODES.md:282` `RVehicleNPCBatmobile.PursuitMode.BeginState` (export 129841) and `:291` `BattleMode.BeginState` (export 129848) — an **NPC Batmobile with the full mode state machine** ships in the build.
- `RBatmobileRemoteBm` (`GADGET_PARAMS.md`) contains `NpcBatmobileTarget` and `CallingVehicle` — the remote gadget explicitly targets an NPC car.

So "no other driver" is a **design choice for the JC3 port**, not a BmAK fact. Under the project's own rule (a row is never kept at a donor/assumed value), MOD-5 needs rewording, not deletion. Proposed text: `MOD-5 · Only the player drives the ported car (design choice, 2026-11-06) — BmAK does ship RVehicleNPCBatmobile (pursuit + battle states, DRIVE_MODES.md:282/291) and a remote gadget that targets it (NpcBatmobileTarget); JC3 closest = entry/exit set + traffic exclusion (T-WLD18/19); gap = deliberate, recorded so nobody reads "BmAK has no NPC car" into the file.`

## 4. Features the source does **not** have (checked, decoded negative)

| asked-for feature | finding | evidence | consequence |
|---|---|---|---|
| **Siren / police lights** | BmAK's light rig has **7 types and no siren**: stripper 12, BattleModeLight 16, BootLight 3, ForensicsLight 12, HeadLight 46, Interior 4, TailLight 8 | `LIGHTS.md:19` (101 entries, 129 components; `by_type` line) | no row is needed; the closest *state* is the battle-mode spotlight (LGT-2/T-MD12). A siren would be lore-foreign — record it as a negative, do not build one |
| **Horn** | "no horn event ships in these packages — the only `Beep` events are tank lock-on UI" | `AUDIO_FEATURES.md:253-255` | AUD-7's parenthetical ("no horn unless lore has one") is **answered: none**; the row can be closed as a proven absence |
| **EMP sound** | "no AkEvent in the grab is an EMP sound" | `AUDIO_FEATURES.md:249-251` | WPN-4/WPN-5 keep a JC3 donor sound; the omission is proven, not assumed |

The relevant negative evidence is strong because the grab is complete on those records: `GAPS.md` reports 19,203/20,128 tag streams decoded (95.40%), and the light and audio records are fully enumerated (101 / 361 rows in `COVERAGE.md`), so a missing type is absence in the data, not a failed decode.

## 5. Rows that exist but are blocked or thin (not uncovered — recorded so they are not mistaken for gaps)

| row | state | evidence |
|---|---|---|
| `T-MD13` | transformation pose — **named omission**, "no JC3 carrier" (32 rows) | `COVERAGE.md` G1 feature table; `MODES.md:37-40` (`Transformation*` 4/9 serialised) |
| `WPN-8` sonar / vehicle scan | carrier `CForcePulse` or named omission; the **on-foot** scanner is `HudModuleScanner`, not the car's | `HUD.md` §5; `COVERAGE.md` (`RBatmobileSonar` 18 fields → T-W1) |
| `T-B1..B3` boost | torque cap / accel / decel covered; **duration and recharge are the open gap** | tracker row `BOOST-cov`: `BOOST_COVERAGE.md` + `t_boost_coverage.py --check` |
| `AU(G1-15)` 90 audio rows | the bank is **absent from the install** (`T-AU3`) | `AUDIO_FEATURES.md:723-765` (missing-bank sections) |
| `HUD-1` speedometer | **not a movie**; the only speedometer is the native debug readout, off in both configs | `HUD.md` §8, `SPEEDOMETER.md`, `bmak_speedometer.py --check` |
| `LGT-1` flares | JC3 light module has **no flare** (55 `LensFlareComponent`s) | `LIGHTS.md` component column; lens-flare carrier report |
| `T-L21` forensics rig | named omission (12 rows) | `COVERAGE.md` |
| `WLD-6` water | `will_sink` on 189/232; 43 differ | `WATER.md` |

## 6. Coverage arithmetic (so the audit can be re-checked)

- 423 decoded fields → 19 T rows, **0 unassigned** (`COVERAGE.md`, `bmak_coverage.py --check`).
- 777 feature rows (ANIMATIONS 253, AUDIO_FEATURES 361, LIGHTS 101, WEAPONS 62) → **777 assigned, 0 unassigned** (`COVERAGE.md`, T-23).
- 198 ledger rows in `T_ROWS.jsonl`; the four families this audit looked for are present: `T-RA1` (dodge/kill/shove/road-assist), `T-SR1` (jump-ramp/self-right), `T-MD12` (battle lights), `T-BM1` (battle mode).
- The three uncovered features are **outside** those counts because `Gad_RBatmobileRemoteBm_SF` was not read at all (`GRAB_BACKLOG.md:967`) and the Batwing sequences sit in `ANIMATIONS.md`'s `other` bucket, which is assigned to `T-PA9` as "no cut part moves" — a row that describes *which parts move*, not *what the sequence delivers*.

## 7. UNKNOWNs

1. **What the call/remote behaviour actually does** — 25 behaviour members have no values and their bodies are not decoded (`GADGET_PARAMS.md:81`). Settled by decompiling those exports (`.g.cs` line numbers are already listed in the file).
2. **Whether the three call/gadget WEMs are on disk** — the events are named but the grab's bank list (`AUDIO_BANKS.md`, 29 banks) has not been cross-referenced against them here.
3. **The Batwing drop height/timing** — key frames are outside the repository (`ANIMATIONS.md:1342`).
4. **Whether JC3 can spawn a vehicle at the player at all** — not tested; the closest documented path is the drop marker (`REBELDROP.md`), and the at-player variant is UNKNOWN.
5. **Whether `bRelativeAiming`/`ScreenOn` are false by default** — no tag in either CDO; a CDO with an unset bool means false *by construction*, which is a derived guess, not a decode.
6. **Whether the operator wants the NCB Batmobile / remote gadget at all** — a scope decision, not an evidence question; listed so it is not silently dropped.

## 8. What to do with this (no files edited)

1. Operator: approve or reject the five proposed rows (T-WLD20, T-WLD21, T-WLD22, T-AU8, T-MD16) and the MOD-5 reword.
2. Add one grab card: **read `Gad_RBatmobileRemoteBm_SF`** — it is named in `GRAB_BACKLOG.md:967` as unread and is the whole evidence base for U-1/U-2.
3. Add one grab card: **decode the 25 `RBatmobileRemoteBm` behaviour exports** and the three call WEMs.
4. Then TRANSLATE the three rows; U-2 will need the route survey (`new-behaviour-routes-survey.md`) because no JC3 carrier exists, and U-3 needs a carrier entity that JC3 does not ship.
