# Landmark map: WEAPONS & GADGETS (as of 2026-11-08)

Read-only survey of `E:\Modding\JustCause3\JC3-Batmobile`. Nothing was edited, installed or launched. Rule applied: no pretrained JC3 knowledge; every claim cites a repo path; absent = UNKNOWN.

## 0. Where the landmark stands in one paragraph

GRAB and TRANSLATE are desk-complete for weapons (G1-08/G1-09/G1-23, G2-10..13/16/17/25/34, T-10, T-11, T-19 all `done` in `GRAB_BACKLOG.md` §12; ledger rows T-WP1..T-WP15 exist in `Working/Translation/T_ROWS.jsonl`, 13 `next`, 1 `keep` (T-WP11), 1 `blocked` (T-WP6 winch)). BUILD produced a partial RC4 (`Builds/bm-RC4/receipt.json`: `complete:false`, pursuit set only, installed:false). `Builds/bm-RC4-weapons/receipt.json` carries 4 bound weapon components (cannon w602 clone, Vulcan w603 clone, missile w618 clone, EMP missile w618 clone + lock-on AutoAim) plus 1 authored-but-UNBOUND riot tune; `carrier_class_mismatch: 2`; limits L-1..L-5 declared. B-17 (effect payloads), B-18 (EMP disable), B-19 (hacker), B-20 (sonar), B-21 (tracker) ship NO payload in RC4 (`GRAB_BACKLOG.md` tracker lines 1964-1969; `Builds/bm-RC4/receipt.json` `not_done`). Booster is the nitro block (T-WP11 `keep`, live in test-091) but the 18-nozzle gadget mesh is not authored. HUD has no entity-to-`hud.gfx` caller (`STATUS.md` T section). The RC5 weapon wave 9100-9110 + 9119 is written but NOT run (no `rc5-*` weapon reports; `Builds/` has only `bm-RC5-audio`, `bm-RC5-entity`); it waits on 9033, whose own inputs 9031/9032 also have no report yet (`tmp/freebuff/reports/` has `apply-v2-weapon-lock-hud-rows.md` only). Nothing is behaviour-verified: `STATUS.md` "0 rows fully verified in game". `tmp/freebuff/APPROVED_Q.txt` does not exist; the test ban stands.

Note on stale/colliding labels (see Risks): `Research/specs/B-24.md` / `B-25.md` (lock-hold/salvo, reticle) are NOT the `GRAB_BACKLOG.md` B-24 (handling) / B-25 (flare) cards; B-15 has three meanings (`tmp/freebuff/reports/pilot-card-combat-and-gadgets.md` §1).

## 1. Weapon inventory (the 11 BmAK classes plus adjuncts)

Source: `Working/Translation/T7_WEAPONS.md` §1 table and `Research/BatmobileGrab/WEAPONS.md`.

| WPN | BmAK class | JC3 carrier chosen (ledger) | rank (OPERATOR_PRIORITIES.md) | ledger row / dispo |
|---|---|---|---|---|
| WPN-1 | `RBatmobileHeavyCannon` 60 mm cannon | `w602_mediumtank_canon` on `main_weapon` | unranked | T-WP1 next |
| WPN-2 | `RBatmobileCannon` Vulcan | `w603_mediumtank_mgun` on `secondary id:00568A74` | unranked | T-WP2 next |
| WPN-3 | `RBatmobileMissileLauncher` missile barrage | donor's own `w618_sportsmuscle_missile` (4 fire points) | unranked (lock UI relates to rank 1) | T-WP3 next |
| WPN-4 | `RBatmobileEMPMissile` = Immobiliser (`tmp/freebuff/reports/immobilizer-vs-emp-missile.md`) | `w618` clone + Fire Leech guidance + new lock-on AutoAim; disable = T-WP15 | 1 | T-WP4 next, T-WP15 next |
| WPN-5 | `RBatmobileEMP` burst | entity `CForcePulse` + `truck_emp.ftune` + `CEMPWeapon` (w702 clone) | 3 | T-WP5 next |
| WPN-6 | `RBatmobileWinch` | closest: `CVehicleCargoBay`-style anchor at `WinchOrigin`; operator lead = Rico's grapple/tether | unranked, required | T-WP6 **blocked** |
| WPN-7 | `RBatmobileAllegianceSwitcher` Drone_Hacker (SAM hack) | SAM context-act + 2 `SAttachedEffect`, `faction` on mount | 4 | T-WP7 next |
| WPN-8 | `RBatmobileSonar` | damage-free `CForcePulse` (`gen_explosion_5m_nodamage`) + authored ring + `BML_Sonar` bank | 5 | T-WP8 next |
| WPN-9 | `RBatmobileVehicleTracker` | mounted weapon entity + HUD `CreatePoi` | 1 (with WPN-4) | T-WP9 next |
| WPN-10 | riot suppressor mode of `RBatmobileCannon` | private zero-damage + impulse tune, second weapon entity | unranked | T-WP10/T-WP14 next |
| WPN-11 | `RBatmobileBooster` | nitro block (live) + authored 18-nozzle gadget mesh | 2 | T-WP11 keep |
| WPN-12 | HUD slots/reticle/cooldown/heat/lock | `hud.gfx` 2 clips, 1 lock POI; heat = absent both sides | - | T-WP12 next, T-19 done |
| (adj) | `RBatmobileMissileLauncherJoker` (11th class in G1-08, 25 fields, 2 instances) | no WPN code, no ledger row | unranked | only `G3-06g` todo |
| (adj) | missile pods = missile-bay open/close mechanism (6 bay bones, 0.833 s) | `tmp/freebuff/reports/missile-pod-salvo-plan.md` | unranked | 9110 |
| (slots) | D-7 all weapons both modes; T-WP13 | 2 driver slots + 2 spare pointers (UNKNOWN if they fire) | - | T-WP13 next |

## 2. Task table

Stage legend: GRAB/TRANSLATE/BUILD/VERIFY/PILOT/TEST/RELEASE. Status legend: done, partial, queued (a brief exists in `tmp/freebuff/queue/` but has not run), todo (no brief), blocked. Size: S, M, L as specified. "blocks" lists main dependents only.

### 2.1 Cross-cutting foundation

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| G1-08 | Every value of every weapon/gadget archetype | GRAB | done | - | T-11 | M | `Research/BatmobileGrab/WEAPONS.md` |
| G1-09 | Projectiles and explosions | GRAB | done | - | T-11 | S | `Research/BatmobileGrab/WEAPONS.md` §4 |
| G1-13 | Sockets in JC3 space (MissileL/R, CannonMuzzle, ChainGunMuzzle, WinchOrigin, BattleModeSpotLight) | GRAB | done | - | B-05 | S | `Research/BatmobileGrab/SOCKETS_JC3.md` |
| G1-23 | Footage-based gap closure (Vulcan heat, LockOnTime 233 samples max 1 s) | GRAB | done | - | T-WP2/3 | M | `Research/BatmobileGrab/FOOTAGE.md` |
| G2-10 | Vehicle weapon catalogue (25 ids, 4,054 members) | GRAB | done | - | T-11 | M | `Research/JC3Grab/WEAPONS.md` |
| G2-11 | Weapon wiring per armed vehicle (62 driver slots, spare pointers) | GRAB | done | - | T-WP13 | M | `Research/JC3Grab/WEAPON_WIRING.md` |
| G2-13 | Turret and cannon mechanics | GRAB | done | - | T-WP1 | S | `Research/JC3Grab/TURRET.md` |
| G2-16/17 | EMP truck / `CForcePulse` census | GRAB | done | - | T-WP5/8 | S | `Research/JC3Grab/EMP.md`, `FORCEPULSE.md` |
| G2-25 | HUD vehicle-weapons API | GRAB | done | - | T-19 | S | `Research/JC3Grab/JC3_HUD_WEAPONS.md` |
| G2-34 | Tether/airlift/winch carriers | GRAB | done | - | T-WP6 | S | `Research/JC3Grab/TETHER.md` |
| G3-02..02j | BmAK control bindings and runtime sampling (B immobilizer on auto-tagged enemy CONFIRMED; X barrage, Y boost user+config) | GRAB | done (12 UNKNOWN open earlier, some closed) | - | NEW-WPN-4 | M | `Research/BatmobileGrab/CONTROLS.md`, `SAMPLER_FIELDS2.md`, `GRAB_BACKLOG.md` tracker G3-02* rows |
| G3-14 | Weapon/gadget audio banks located (BML_Sonar etc.) | GRAB | done | - | NEW-WPN-14 | S | `Research/BatmobileGrab/AUDIO_BANKS.md`, `AUDIO_BANKS2.md:154-169` |
| G3-06g | Weapon-adjacent native remainder (`RJokerMissileTarget`, launcher PFX/mesh components) | GRAB | todo | T-11 (done, so only unstarted) | NEW-WPN-10 | S | `GRAB_BACKLOG.md` tracker G3-06g |
| 9050 | exe entity-swap consumer / native remainder (feeds slot-firing unknowns) | GRAB | queued | - | NEW-WPN-2 | M | `tmp/freebuff/queue/9050*`, `QUEUE_MAP.md:91-101` |
| T-10 | Re-open `out` rows with G2 evidence | TRANSLATE | done | - | T-11 | S | `Working/Translation/T10_OPEN_ROWS.md` |
| T-11 | Weapons translation (15 rows T-WP1..15) | TRANSLATE | done (rows resolved, 0 verified) | - | B-05/06 | L | `Working/Translation/T7_WEAPONS.md`, `t7_weapons_edits.json` |
| T-19 | HUD translation incl. T-HUD5 (2 slots, reticle, cooldown; heat absent) | TRANSLATE | done | - | 9160 | S | `Working/Translation/T6_HUD_CAMERA.md` §1a |
| T-WP13 | Slot ruling: 11 weapons into 2 driver slots (D-7); forced build of 4 `CCar` roots x 2 slots; third/fourth via spare pointers | TRANSLATE | partial (row `next`; mechanism for fire path UNKNOWN) | NEW-WPN-2, NEW-WPN-3 | all weapon fire | M | `Working/Translation/T_WP13_PROPOSAL.md`, `T_WP13B.md`, `tmp/freebuff/reports/four-weapon-slot-build-plan.md` |
| T-WP12 | HUD translation row (slots, reticle, cooldown, no heat) | TRANSLATE | done (as row) / BUILD not done | 9160 | - | S | `T_ROWS.jsonl` T-WP12 |
| D-3 | Weapon lethality: accept JC3 lethality, no toggle (2026-10-28). Superseded for riot only by the 2026-11-06 rule: zero-damage impulse tune as second weapon entity | TRANSLATE | done (but partly superseded; see NEW-WPN-24) | - | T-WP10 | S | `GRAB_BACKLOG.md:1797`, `T_ROWS.jsonl` T-WP10/14 |
| D-7 | All BmAK weapons in both modes | decision | done | - | T-WP13 | S | `GRAB_BACKLOG.md:1801` |
| D-11 | BmAK controls win inside car; only ENTER uses JC3 | decision | done | - | NEW-WPN-4 | S | `GRAB_BACKLOG.md:1805` |
| D-2 | Pursuit/battle pair (hybrid withdrawn, awaiting operator) | decision | blocked (reopened) | operator | B-12, NEW-WPN-9 | S | `GRAB_BACKLOG.md:1796` |
| B-05 | Entity graph (slots, weapon points) | BUILD | done for RC4 (4 roots, weapon components cloned from APC bullet weapon) | - | B-06 | L | `Working/Entity/bm_epe_edits.json`, `Builds/bm-RC4-entity/` |
| B-06 | Weapon entities (private copies): cannon, Vulcan, missile, EMP missile tunes | BUILD | partial (4 bound; 5 private tunes; L-1 class mismatch, L-5 angle unit UNKNOWN) | NEW-WPN-26, NEW-WPN-27 | RC5 | M | `Builds/bm-RC4-weapons/receipt.json` |
| B-16 | Weapon-clone cleanup in RC merge | BUILD | done | - | - | S | tracker B-16 |
| B-17 | Effect-writer payloads (muzzle, tracer, trail, flame, beam, ring) | BUILD | todo (writer proven 95/95; no payload in RC4) | 9100 | all weapon FX | L | `tmp/freebuff/reports/effc-format-writable.md`, `Tools/scripts/effc_writer.py check` |
| R wave 9001-9004 | Dangling fire refs, asset paths, size pins, loop 279 | BUILD | done | - | 9100 | M | `tmp/freebuff/reports/rc5-dangling-fire-refs.md` etc. |
| P wave 9010-9019 | Plans v2 (summon/unranked, lock/salvo/reticle, EMP/immobiliser, boost, controls, hud) | TRANSLATE | done | - | 9100.. | M | `tmp/freebuff/reports/*-v2.md`, `apply-v2-weapon-lock-hud-rows.md` |
| 9031/9032/9033 | Ledger apply (driving/world, body) and 9033 review that rewrites 91xx briefs | TRANSLATE | queued | 9030 chain output | 9100 | M | `tmp/freebuff/queue/9031*`, `9032*`, `9033*` |
| 9100 | RC5 scaffold + merge script (`bm_rc5.py`, branch records) | BUILD | queued | 9033 + R wave | 9101..9110 | M | `tmp/freebuff/queue/9100-rc5-scaffold-and-merge-script.txt` |
| 9101 | Entity roots and slots (2 driver slots, 4 CCar roots, 69 interaction objects, fire refs) | BUILD | queued | 9100 | 9102..9110, 9160, 9170 | M | `tmp/freebuff/queue/9101-*` |
| 9102 | Effect-writer payloads: missile trail/launch flash, booster plume/flame, sonar ring plan | BUILD | queued | 9101 | 9103, 9106, 9109 | M | `tmp/freebuff/queue/9102-*` |
| 9119 | Adversarial review of the ten weapon builds | VERIFY | queued | 9101..9110 | 9190 | M | `tmp/freebuff/queue/9119-*` |
| 9190 | Merge RC5 | BUILD | queued | all builds + reviews | 9191, 9192 | M | `tmp/freebuff/queue/9190-*` |
| 9191 | Verify group A (V-01 files, V-03 wiring, V-04 audio) | VERIFY | queued | 9190 | 9193 | M | `tmp/freebuff/queue/9191-*` |
| 9192 | Verify group B (V-02 geometry, V-05 predictions, V-06 install dry runs) | VERIFY | queued | 9190 | 9193 | M | `tmp/freebuff/queue/9192-*` |
| 9193 | VX gate + `APPROVAL_REQUEST_RC5.md` (operator creates `APPROVED_Q.txt` himself) | VERIFY | queued | 9191, 9192 | TEST | S | `tmp/freebuff/queue/9193-*` |
| 9194 | Pilot-card refresh for RC5 | PILOT | queued | 9193 | TEST | S | `QUEUE_MAP.md:101` |
| 9199 | Final review | VERIFY | queued | 9194 | RELEASE | S | `QUEUE_MAP.md:101` |

### 2.2 Per weapon

#### Rank 1: Tracker (WPN-9) + EMP missile / Immobiliser (WPN-4) + lock-on (WPN-3 reticle)

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| T-WP9 | Tracker row: mounted weapon + `missile_base_tuning.*` + BattleModeSpotLight 30 deg fire pos; `bInstantFire` UNKNOWN | TRANSLATE | done (row) | - | B-21 | S | `T_ROWS.jsonl`, `Working/Translation/T_WP4D_TRACKER_EMP.md` |
| T-WP4 | EMP missile launcher row (w618 clone, Fire Leech guidance: turning speed 300 random 60, accel 30->65 over 0.2->10 s, accel random 2->5; new AutoAim, cone 0.12/0.15, MaxAimDistance 120 m) | TRANSLATE | done (row) | - | B-06 | S | `T_ROWS.jsonl` T-WP4, `tmp/freebuff/reports/wp4-fire-leech.md` |
| T-WP15 | EMP disable half (composed: pulse + cloned `CEMPWeapon w702_emp`; `is_disabled_by_emp` has 0 bindings in 1,941 entries) | TRANSLATE | done (row, mechanism unproven) | NEW-WPN-19 | B-18 | S | `T_ROWS.jsonl`, `tmp/freebuff/reports/immobiliser-and-emp-trigger.md` |
| T-WP3 | Missile barrage row (w618; lock time/range = UNKNOWN) | TRANSLATE | done (row) | - | 9104 | S | `T_ROWS.jsonl` |
| T-WP3b | Lock-on carriers: `missile_turning_speed` + `autoaim_vehicle_lockon_missile`; no hold timer member | TRANSLATE | done | - | 9105 | S | `Working/Translation/T_WP3B_LOCKON.md` |
| B-21 / 9103 | Tracker launcher on same button+socket as missile, private tune, 30 deg fire pos; yellow/grey POI (type 19 / 24), distance via `MCI_distance.TXT_distance`, state change by remove+create | BUILD | queued | 9102, 9101, HUD caller (9160) | 9104 | M | `tmp/freebuff/queue/9103-*`, `tmp/freebuff/reports/tracker-lock-hud-plan.md`, tracker `GRAB_BACKLOG.md` B-21 |
| NEW-WPN-17 | Tracker world behaviour: signal strength weakens with distance, visible through walls when close (operator fact), metre/km string rule, mission-style `mm130_tracker` graph | BUILD | todo (plan exists) | 9103, 9160 | TEST | M | `tmp/freebuff/reports/tracker-signal-range-and-wall-visibility.md`, memory `bmak-gameplay-facts.md` |
| B-06 / 9104 | EMP missile weapon entity (w618 clone + guidance + AutoAim; trail at MissileL/R); every fire-block value kept from w618 | BUILD | partial (RC4 clone exists) / queued (RC5 rework) | 9103, NEW-WPN-27 | 9105, 9107 | M | `Builds/bm-RC4-weapons/receipt.json`, `tmp/freebuff/queue/9104-*` |
| NEW-WPN-27 | Fix L-1: a missile tune sits on a `CBulletWeaponBase` component (B-05 cloned the APC bullet weapon for all four). Re-clone on a `CMissileWeaponBase` carrier or prove the engine accepts it | BUILD | todo | 9101 | 9104, NEW-WPN-30 | M | `Builds/bm-RC4-weapons/receipt.json` limits L-1, `carrier_class_mismatch: 2` |
| NEW-WPN-26 | Settle AutoAim angle unit (0.15 = 54 deg as turns vs 8.6 deg as radians) so BmAK's 40 deg cone can be written | GRAB | todo | probe or exe read (9050) | 9104, 9105 | S | `Builds/bm-RC4-weapons/receipt.json` L-5, `apply-weapon-slot-rows.md` §10 |
| B-24* / 9105 | Lock hold + salvo + reticle: pursuit circle shrinking over 2.0 s lock, battle instant orange diamond, crosshair-nearest-first target pick, 8-round composed salvo; reticle entity-to-HUD link (POI type 21, 1.5 s rotation, 0.5 s `MCI_missile_locked`) | BUILD | queued | 9104, 9160 | TEST | L | `tmp/freebuff/queue/9105-*`, `Research/specs/B-24.md`, `B-25.md`, `tmp/freebuff/reports/lock-hold-salvo-reticle-plan-v2.md`, `lock-on-reticle-hud-link.md` |
| NEW-WPN-8 | Confirm what `MissileLockOnDuration` 2.0 s governs (pursuit circle vs other), `MaxTargets` 8 provenance (flagged as found-by-rebuild in plan v2), and target sort key (operator unsure: crosshair-nearest first, proximity second) | GRAB | todo | operator / footage (G1-23 style) | 9105 | S | `tmp/freebuff/reports/bm-lock-duration-and-cone.md`, `bm-lock-target-sort-key.md`, memory facts |
| B-18 / 9107 (EMP half) | Mount the Immobiliser disable: clone `w702_emp.wtunec`, `CEMPWeapon` entity, entity `CForcePulse` + `truck_emp.ftune` with the 3 flags as shipped; probes Q-EMP-1..4 | BUILD | queued (no RC4 payload) | 9104, 9101 | NEW-WPN-19 | M | `GRAB_BACKLOG.md` B-18, `tmp/freebuff/reports/emp-immobiliser-forcepulse-plans-v2.md` |
| NEW-WPN-19 | In-game EMP probes: does stock `w702_emp` stall a car (Q-EMP-1), does the pulse alone (2), is `CEMPWeapon` accepted in a car slot (3), duration bracket (4); write measured `DisableEnemyDuration` | TEST | todo (gated) | `APPROVED_Q.txt`, operator, B-18 | B-18 done, T-WP15 verified | M | `GRAB_BACKLOG.md` B-18 Do-4 |
| NEW-WPN-20 | Immobiliser target rules: operator scrape lead (unverified) says battle-mode EMP permanently disables cars with no explosion/smoke/flame + lightning; tank and chopper drones are stunned; brief 7997 settles it. Pull fired archetype's own damage 60.0/impact sound (UNKNOWN on `_ForCars` archetype) | TRANSLATE | partial | operator confirmation | 9104 | S | `GRAB_BACKLOG.md:169-170`, `Working/Translation/T_WP4D_TRACKER_EMP.md` |
| NEW-WPN-18 | Radar/minimap: tracked vehicle green icon, hacked red to green, cops/military/tank/helicopter icons, direction arrows | BUILD | queued (inside 9160) | 9160 | TEST | M | `OPERATOR_PRIORITIES.md`, `tmp/freebuff/queue/9160-*`, `hud-radar-dash-plans-v2.md` |
| NEW-WPN-1 | Rank-1 verify + TEST: tag a moving car, marker yellow/grey + live distance, missile homes and the car stalls permanently (see operator lead), tank/drone stunned | TEST | todo | 9190, `APPROVED_Q`, NEW-WPN-19 | RELEASE | M | `tmp/freebuff/reports/pilot-card-combat-and-gadgets.md` |

#### Rank 2: Booster mesh (WPN-11)

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| T-WP11 | Afterburner = JC3 nitro (live in test-091); gadget mesh is a cockpit part row | TRANSLATE | done (`keep`) | - | 9106 | S | `T_ROWS.jsonl` T-WP11 |
| 9106 | Author 18-nozzle ring mesh (z 2.989 m, ~34 cm), deploy 0.600 s/19 keys, close 0.833 s/26 keys, bind as movable part, drive from nitro state, plume from effects branch | BUILD | queued | 9102, `boost-selector-and-moving-parts-plans-v2.md` | 9119 | L | `tmp/freebuff/queue/9106-*`, `tmp/freebuff/reports/booster-mesh-and-flame-plan.md`, `weapon-bay-animation-plan.md` |
| NEW-WPN-11 | In-cockpit gadget meshes (`Drone_Hacker.GadgetMesh`, `Batmobile_Sonar.GadgetMesh`, `Vehicle_Tracker.GadgetMesh`, Booster mesh) as parts: no brief owns them | BUILD | todo | 9172 (parts) | - | M | `T_ROWS.jsonl` T-WP7/8/9/11 |
| NEW-WPN-12 | Missile-bay open/close animation (6 bay bones, 14.99 deg rotate, 10.87 cm translate, 0.833 s) tied to missile fire | BUILD | todo (in 9110 as "pods", unclear) | 9101, 9172 | NEW-WPN-30 | M | `tmp/freebuff/reports/missile-pod-salvo-plan.md`, `Research/BatmobileGrab/ANIMATIONS.md` |
| NEW-WPN-35 | Afterburner HUD: gauge left in pursuit, quick-recharge cooldown gauge to its left; nitro gauge reuse | BUILD | queued (inside 9160) | 9160 | TEST | S | `OPERATOR_PRIORITIES.md` |
| NEW-WPN-36 | Booster TEST: deploy/close timing, plume, 0-100 with/without boost (T-B1/T-B3 take already owns this) | TEST | todo | 9190, `APPROVED_Q` | RELEASE | S | `Working/Q/PREDICTIONS.md` |

#### Rank 3: EMP burst (WPN-5)

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| T-WP5 / T-WP5b | Burst row; decoded: range 75 m, disable 2/4/8/12 s per power level, charge 0/0.5/1/1.5 s, impulse 15000, cooldown 2.0 s | TRANSLATE | done | - | 9107 | S | `Working/Translation/T_WP5B_EMP_BURST.md` |
| 9107 (burst half) | Burst effect (4 stages to 250/30/30 cm, lifetime 0.2-4.0 s, spawn 0-1500, wheel EMP material at index 0), entity pulse, composed disable | BUILD | queued | 9104, 9102 | 9119 | M | `tmp/freebuff/queue/9107-*`, `emp-visual-and-hit-plan.md` |
| NEW-WPN-37 | Charged-power-level input (hold = higher level, 4 levels), HUD power level (`DrawWeaponPowerLevel`) | BUILD | todo | 9107, 9160 | TEST | M | `T_WP5B_EMP_BURST.md` §2 |
| NEW-WPN-38 | Burst TEST: stalls/pushes car, damages nothing, cooldown 2.0 s, wheel glow | TEST | todo | 9190, `APPROVED_Q`, NEW-WPN-19 | RELEASE | S | `pilot-card-combat-and-gadgets.md` |

#### Rank 4: Hacker (WPN-7)

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| T-WP7 | Row: 2 `SAttachedEffect` + SAM context-act + `faction`; no allegiance member in 295 wiring dumps | TRANSLATE | done (row) | - | 9108 | S | `T_ROWS.jsonl`, `tmp/freebuff/reports/hacker-and-tracker-gadgets.md` |
| 9108 / B-19 | Hacker build: magenta beam 35 cm (colour 2.0,0.0,1.0; 6 sockets; 4 s drone/10 s heavy tank; cooldown 1.0 s), success feedback, interaction on SAM site + drone, side flip | BUILD | queued | 9101, 9110 plan | 9119 | M | `tmp/freebuff/queue/9108-*`, `hacker-gadget-visual-plan.md`, `sam-hack-allegiance-state.md` |
| NEW-WPN-21 | Allegiance-flip reader: SAM hack leaves only the event `5D26E95A`; no faction write; find a runtime consumer or compose (swap to a friendly turret entity / Rebel-Drop friendly drone route). Operator facts: hacked SAM fires at enemies, aircraft only; drones cannot be hacked in JC3 | GRAB/BUILD | todo | probe (needs game) | 9108 done-line | M | `tmp/freebuff/reports/sam-hack-allegiance-state.md`, `OPERATOR_PRIORITIES.md` |
| NEW-WPN-39 | Hacker TEST: SAM stops firing at player, fires at aircraft; marker red to green; beam visual; cooldown | TEST | todo | 9190, `APPROVED_Q` | RELEASE | S | `pilot-card-combat-and-gadgets.md` |

#### Rank 5: Sonar (WPN-8)

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| T-WP8 | Row: damage-free `CForcePulse`, authored ring effect, `BML_Sonar` bank (6 events) | TRANSLATE | done (row) | - | 9109 | S | `T_ROWS.jsonl` |
| 9109 / B-20 | Pulse (copied from `gen_explosion_5m_nodamage`), ring `.effc` (7 emitters, 2500 cm/s axial, lifetimes -> 25/37.5/75 m; fade undecoded), import 6 BML_Sonar events, optional reveal markers | BUILD | queued | 9102 | 9119 | M | `tmp/freebuff/queue/9109-*`, `sonar-pulse-visual-plan.md`, `AUDIO_BANKS2.md:154-169` |
| NEW-WPN-22 | Treadmark-following half: both BmAK assets are `missing-object`; locate them (G3 package reads) or record permanent UNKNOWN; mission-only in BmAK (operator) | GRAB | todo | - | NEW-WPN-40 | S | `tmp/freebuff/reports/sonar-and-scan-pulse.md` §4 |
| NEW-WPN-40 | Sonar TEST: pulse range/timing, pushes a parked car without damage, sounds, markers expire | TEST | todo | 9190, `APPROVED_Q` | RELEASE | S | `pilot-card-combat-and-gadgets.md` |

#### Unranked: 60 mm cannon, Vulcan, riot, missile pods, winch, Joker launcher

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| T-WP1 | Cannon row: w602, 1.75->2.0 s, velocity 500->400 (built in RC4 tune) | TRANSLATE/BUILD | done (RC4 values written, readback only) | - | 9110 | S | `Builds/bm-RC4-weapons/receipt.json` |
| T-WP2 | Vulcan row: w603 on second slot, fire_rate 0.1->0.138; barrel-spin part is T-12 | TRANSLATE/BUILD | done (RC4 values written) | - | 9110 | S | same |
| 9110 | Cannon fire_position (0, 0.3739, -5.8174) + 60 mm reload circle + recoil/muzzle; Vulcan bloom spreading then turning red with no lockout; riot second entity; pods | BUILD | queued | 9105 and 9101 chain | 9119 | L | `tmp/freebuff/queue/9110-*`, `summon-and-unranked-weapon-plans-v2.md`, `cannon-60mm-reload-circle-plan.md`, `vulcan-capture-fire-and-overheat-timing.md` |
| NEW-WPN-5 | 60 mm cannon HUD: reload circle (operator fact) via `InitVehicleWeapons` `weapon_cooldown` 0..1 / `UC_SetCannonCoolDown`; BmAK has no magazine, `ReloadSoundDuration` 0.4 s is a sound length (plan) | BUILD | todo (plan exists) | 9160 | TEST | S | `tmp/freebuff/reports/ammo-types-and-reload-plan.md`, `cannon-60mm-reload-circle-plan.md` |
| NEW-WPN-6 | Vulcan bloom HUD: crosshair spread, turn red, cool-down shrinks bloom, never interrupts fire; `UC_SetMachineGunAccuracyFrame` frame scale UNKNOWN | BUILD | todo | 9160, NEW-WPN-7 | TEST | M | `T_WP12` row, memory `bmak-gameplay-facts.md`, `vulcan-spinup-and-heat-plan.md` |
| NEW-WPN-7 | Extract bloom curve (spread vs time, red threshold) from capture `C:\Users\User\Videos\Captures\Batman... VulcanFire_10s-15s.mp4` | GRAB | todo | operator-supplied file read | NEW-WPN-6 | S | memory `bmak-gameplay-facts.md`, `vulcan-capture-fire-and-overheat-timing.md` |
| NEW-WPN-41 | Vulcan barrel spin-up + casings + tracer FX payloads (T-FX10..16) via B-17 | BUILD | todo | B-17 / 9102 | TEST | M | `T_ROWS.jsonl` T-FX10..16, `Builds/bm-RC4-weapons/receipt.json` tracer_unchanged |
| T-WP10/T-WP14 + B-15(riot) | Riot suppressor: zero-damage + impulse + 0.75 s cadence, gel VFX; toggle = second weapon entity (no per-weapon mode member) | TRANSLATE | done (row) | - | 9110 | S | `tmp/freebuff/reports/non-lethal-cannon-carrier.md`, `Research/specs/B-15.md` |
| NEW-WPN-23 | Bind riot entity (RC4 authored it but UNBOUND, L-4); riot mode switch input; riot lock-on angle 7.5 | BUILD | todo (inside 9110) | T-WP13 slot decision | TEST | M | `Builds/bm-RC4-weapons/receipt.json` L-4 |
| T-WP6 | Winch row | TRANSLATE | blocked | closest-system build plan (NEW-WPN-15) | B-?? winch | M | `T_ROWS.jsonl` T-WP6, `tmp/freebuff/reports/winch-and-tether.md` |
| NEW-WPN-15 | Winch closest-system plan: operator lead = Rico's grapple/tether (`FIRE_GRAPPLE`, `dualtether_test_to_vehicle.gdc`, `grapple_pull` damage channel, `CVehicleCargoBay`); decide: character grapple fired from car vs authored rope part. No queue brief builds it | TRANSLATE | todo | operator lead processing | NEW-WPN-16 | M | `OPERATOR_PRIORITIES.md`, `winch-and-tether.md`, `Research/JC3Grab/TETHER.md` |
| NEW-WPN-16 | Winch BUILD: D-pad right input (replaces mission select, per operator), rope part (`transport_rope_winch`, BmAK two `RSimpleRopeComponent`s, muzzle/latch FX, `Play_BML_WinchFire`/`_Attatch`), pull behaviour | BUILD | todo (9170 binds input only) | NEW-WPN-15, 9170 | NEW-WPN-42 | L | `Working/Q/PILOT/CONTROLS.md` row 20, `T_ROWS.jsonl` T-WP6 |
| NEW-WPN-42 | Winch TEST | TEST | todo | NEW-WPN-16 | RELEASE | S | `pilot-card-combat-and-gadgets.md` |
| NEW-WPN-10 | Joker launcher (`RBatmobileMissileLauncherJoker`, 25 fields, 2 instances; `Batmobile_JokersRocket_Trail`): decide in/out, give a WPN code and ledger row; Joker variants in scope? (D-5 skins as drop entries) | TRANSLATE | todo | G3-06g | - | S | `T7_WEAPONS.md:43`, `GRAB_BACKLOG.md` G3-06g, D-5 |
| NEW-WPN-43 | Cannon / Vulcan / riot / missile TEST cards: shots-to-kill bands K-1..K-11 (K-7 tank cannon 24-48 hits; K-11 lock UNKNOWN), cannon 2.0 s +-0.15, shell 400 m/s | TEST | todo | 9190, `APPROVED_Q` | RELEASE | M | `Working/Q/PREDICTIONS_COMBAT.md`, `Builds/bm-RC4-weapons/receipt.json` |

### 2.3 Slots, input binding, HUD, audio, effects (shared by all weapons)

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| NEW-WPN-2 | Engine probe: does a weapon behind spare pointers `id:8580BA42` / `id:CA86AA17` (non-null on 0 of 54 roots) fire? Is a 3rd/4th driver fire path possible at all? | TEST | todo | `APPROVED_Q`, 9050 (static first) | T-WP13 final shape | M | `Working/Translation/T_WP13B.md`, `repeated-slot-pointer-evidence.md` |
| NEW-WPN-3 | Probe: is a dropzone `settings/keymap_gamepad.bin` honoured so B/X/Y/D-pad up can be rebound to BmAK weapon select 1..4? Else weapons collapse to RB/LB fire + `USE_VEHICLE_MOD` + `USE_ITEM` | TEST | todo | `APPROVED_Q` | NEW-WPN-4 | S | `tmp/freebuff/reports/gadget-wheel-input-plan.md` |
| NEW-WPN-4 | Input binding build: weapon select 1..4 (B tracker/EMP-in-battle, X barrage, Y hacker, D-pad up 4), L3 sonar, D-pad right winch, RB/RT fire; per-mode weapon table | BUILD | queued (9170 partial; 9170 covers entry/exit/eject) | 9101, NEW-WPN-3, NEW-WPN-34 | all weapon TEST | L | `Working/Q/PILOT/CONTROLS.md`, `tmp/freebuff/queue/9170-*`, `gadget-wheel-input-plan.md` |
| NEW-WPN-34 | Weapon-per-mode loadout table (battle: cannon RT, Vulcan RB, barrage X, hacker Y, EMP B; pursuit: tracker/Immobiliser B, ...) with D-7; sonar/winch/booster mode availability | TRANSLATE | todo | operator (c) | NEW-WPN-4, B-12 | S | `Working/Q/PILOT/CONTROLS.md` rows 10-18 |
| NEW-WPN-9 | Battle-mode weapon set cannot ride a pursuit-only RC: B-12 mode pair merge must carry weapon sets; D-2 reopened | BUILD | blocked | D-2, B-12/9130 | NEW-WPN-4 | L | `Builds/bm-RC4/receipt.json` not_done, `GRAB_BACKLOG.md:1796`, 9130 |
| 9160 | HUD build: `hud.gfx` caller, weapon slots, lock reticle, tracker POIs, power level, speedometer disabled, health top-left battle, afterburner gauge | BUILD | queued | 9100, 9103, `hud-radar-dash-plans-v2.md` | NEW-WPN-5,6,17,18,35,37 | L | `tmp/freebuff/queue/9160-*` |
| NEW-WPN-44 | Weapon-name / gadget strings (menu text "60mm Cannon", "Tracker / Immobilizer" etc.) as stringlookup rows | BUILD | todo | 9173 string route | - | S | `Working/Q/PILOT/CONTROLS.md` |
| NEW-WPN-14 | Weapon audio: cannon fire/impact, Vulcan loop (`weapons#408` loop click RED earlier), missile flight/up (`Play_Batmobile_ApRocket_Flight/_Up` are `missing-object`), Immobiliser impact, EMP fire, hacker, riot bolt/impacts, winch; private effects-class bank + per-entity bindings (B-26 route) | BUILD | queued (9150 covers vehicle audio; weapon events not enumerated) | 9150, T-AU3/T-AU5 | TEST | L | `GRAB_BACKLOG.md` B-26, `AUDIO_BANKS2.md:164-170`, `T_ROWS.jsonl` T-AU3/T-AU5 |
| NEW-WPN-13 | Recoil / muzzle flash / impact FX / casings per weapon via B-17 writer (sequence after 9102) | BUILD | todo | 9102 | TEST | L | `cannon-recoil-and-muzzle-plan.md`, `T_ROWS.jsonl` T-FX10..16 |
| NEW-WPN-25 | Weapon damage numbers vs target classes (BmAK missile 250 vs EMP 60 against 1,200 HP; build 36,000 HP): per-weapon damage rows (Vulcan, riot, barrage per round, EMP 60) are UNKNOWN or deferred to T-14 | TRANSLATE | partial | - | NEW-WPN-43 | M | `Working/Q/PREDICTIONS_COMBAT.md` UNKNOWNs, `Research/BatmobileGrab/DAMAGE_RULES.md` |
| NEW-WPN-45 | Ammo/cooldown build: BmAK = unlimited, cadence + `WeaponCoolDown` only; write `unlimited_ammo`/`magazine_size`/`reload_time_scale` in the 4 private tunes; cooldown values for EMP burst 2.0 s, hacker 1.0 s, EMP/tracker | BUILD | todo (plan done) | 9101 | TEST | S | `tmp/freebuff/reports/ammo-types-and-reload-plan.md`, `weapon-slot-inputs-prep-list.md` |
| NEW-WPN-28 | Static per-weapon VERIFY scripts (`rc5_*.py --check`), wiring gate (V-03: every weapon point/asset path/object id resolves), tune read-back via `jc3weapons.py --check --root` | VERIFY | queued (9119, 9191) | builds | 9193 | M | `tmp/freebuff/queue/9119-*`, `9191-*` |
| NEW-WPN-29 | Refresh pilot card `pilot-card-combat-and-gadgets.md` to the RC5 slot/binding reality (eleven cards) | PILOT | queued (9194) | 9193 | TEST | S | `tmp/freebuff/reports/pilot-card-combat-and-gadgets.md` |
| NEW-WPN-24 | Reconcile D-3 record ("accept JC3 lethality, no toggle" 2026-10-28) with the 2026-11-06 rule (riot = zero-damage second entity); the user's brief calls D-3 "accept lethality" | TRANSLATE | todo | - | NEW-WPN-23 | S | `GRAB_BACKLOG.md:1797`, `T_ROWS.jsonl` T-WP10 why |
| NEW-WPN-46 | Resolve numbering collision: `Research/specs/B-24.md`/`B-25.md` (lock-hold, reticle) vs backlog B-24 (handling)/B-25 (flare); B-15 triple meaning | TRANSLATE | todo | - | 9105 review | S | `pilot-card-combat-and-gadgets.md` §1, `QUEUE_MAP.md` |
| NEW-WPN-47 | Q-3 combat session execution (7 items, ~45 min nominal) plus repair loops; Q-1 "weapons at a wall" item | TEST | todo | `APPROVED_Q`, 9193, 9194 | RELEASE | L | `Working/Q/APPROVAL_REQUEST.md` §2 |
| NEW-WPN-31 | Fix-card loop: every failed weapon take returns to BUILD with a measured value (EMP duration, lock time, bloom, reload) | BUILD | todo | NEW-WPN-47 | RELEASE | L | `STAGES.md:14` |
| NEW-WPN-32 | Weapon keyboard/mouse vs gamepad parity (RB/LB vs LMB/RMB; operator's input device UNKNOWN) | BUILD | todo | operator (c) | NEW-WPN-4 | S | `Working/Q/PILOT/CONTROLS.md` |
| NEW-WPN-33 | Installer: use `install_v2.ps1` rollback-safe flow for RC5 (V-06-RC2 found Rollback091 deletes files; fix exists for copies only); weapon tunes must load, install/verify/uninstall | RELEASE | partial | 9192 | RELEASE | M | `Working/Installer/install_v2.ps1`, `GRAB_BACKLOG.md` V-06-RC2/V-06-fix |
| NEW-WPN-48 | Release package: known-limitation notes per weapon (no heat model; sonar treadmarks missing; winch approximation; hacker flip composed; lock-time source) and operator sign-off | RELEASE | todo | all TEST | - | S | this file §d |

## 3. (a) Done, with evidence

- GRAB complete: weapons record `Research/BatmobileGrab/WEAPONS.md` (1,771 lines; 11 classes); JC3 catalogue/wiring/HUD `Research/JC3Grab/WEAPONS.md`, `WEAPON_WIRING.md`, `JC3_HUD_WEAPONS.md`, `EMP.md`, `FORCEPULSE.md`, `TETHER.md`; tracker rows G1-08, G1-09, G1-13, G1-23, G2-10, G2-11, G2-13, G2-16, G2-17, G2-25, G2-34 all `done` in `GRAB_BACKLOG.md` §12.
- Operator facts captured: ranking and HUD leads `OPERATOR_PRIORITIES.md`; gameplay facts `memory/bmak-gameplay-facts.md` (lock diamond/circle, tracker weakening signal, SAM hack, sonar, Vulcan bloom no lockout, cannon reload circle).
- Immobiliser identity settled: `tmp/freebuff/reports/immobilizer-vs-emp-missile.md`; BmAK input B confirmed live (G3-02d).
- TRANSLATE complete: T-10, T-11 (`Working/Translation/T7_WEAPONS.md`, 15 rows, 136-164 classified aspects, 46-53 UNKNOWN), T-19, corrective cards T_WP3B, T_WP4C/D, T_WP5B, T_WP13/T_WP13B.
- Decisions: D-3, D-4 (keep v0300 donor), D-7, D-11 resolved.
- BUILD (partial): B-05 entity graph, B-06 four private weapon tunes plus unbound riot (`Builds/bm-RC4-weapons/receipt.json`, 13 tune edits, 37 AutoAim edits, 7 files registered, 0 dangling), B-16 cleanup, nitro block live since test-091.
- Prediction table written: `Working/Q/PREDICTIONS_COMBAT.md` (10 predicted, 1 UNKNOWN K-11 lock time), eleven pilot cards written: `tmp/freebuff/reports/pilot-card-combat-and-gadgets.md`.
- Plans v2 done (R wave and P wave): lock/salvo/reticle, EMP/immobiliser, hud/radar, summon/unranked, controls.
- Zero behaviour-verified weapon rows; zero weapon in-game observation.

## 4. (b) BLOCKERS, root first

Root blockers (everything else sits behind these):

1. **R1: Test ban / `tmp/freebuff/APPROVED_Q.txt` absent.** Only the operator creates it. No weapon can be tested; every Q-EMP probe, slot probe and keymap probe is gated. Blocks: NEW-WPN-2, -3, -19, -21 (runtime part), NEW-WPN-47 and all TEST rows.
2. **R2: No in-game proof that JC3 fires more than two driver weapons or honours a rebound keymap.** (T-WP13B: two fire paths only; spare pointers' effect UNKNOWN; `keymap_gamepad.bin` override UNKNOWN.) Blocks: NEW-WPN-4 final shape, 11-weapon D-7 promise.
3. **R3: Queue head not run: 9031/9032/9033 -> 9100.** 9100 (merge scaffold) waits for 9033; everything weapon-build sits behind 9100 -> 9101 -> 9102 -> 9103 -> 9104 -> 9105 (serial rank-1 chain), then 9106-9109 in parallel, then 9110, 9119.
4. **R4: D-2 reopened (pursuit/battle pair).** RC4 is pursuit only; battle weapon set (cannon, Vulcan, barrage, hacker, EMP burst per `CONTROLS.md`) rides the unbuilt mode switch (B-12 / 9130). Blocks NEW-WPN-9, NEW-WPN-34, D-7 "both modes". Needs the operator.
5. **R5: No `hud.gfx` entity-to-HUD caller** (`STATUS.md`). 9160 must land first. Blocks tracker marker (rank 1), lock reticle, reload circle, Vulcan bloom, power level, radar icons.
6. **R6: Effect writer has no payload (B-17).** Missile trail, booster plume, sonar ring, beam, muzzle all need it; 9102 first.
7. **R7: Audio route (B-26).** Weapon sounds need the private effects-class bank; 2 missile loop events are `missing-object`.

Dependency spine for rank 1 (tracker + EMP missile): 9033 -> 9100 -> 9101 -> 9102 -> 9103 (needs 9160 HUD) -> 9104 (needs NEW-WPN-27, NEW-WPN-26) -> 9105 -> 9107 disable half -> NEW-WPN-19 (game).

Other direct blockers: T-WP6 winch (no queue brief; needs NEW-WPN-15 plan); T-WP15 disable mechanism unproven until NEW-WPN-19; hacker allegiance reader UNKNOWN (NEW-WPN-21); B-17/B-26 card numbers colliding in the queue map.

## 5. (c) Open questions for the operator (player knowledge only)

1. Which weapons are available in pursuit mode versus battle mode, and on which buttons (tracker B pursuit, EMP B battle per `CONTROLS_MENU_SCREENS.md`; is cannon/Vulcan/barrage really battle only; is the Vulcan on RB and the cannon on RT in your game)? D-7 says all in both modes, but BmAK data suggests per-mode sets.
2. Target-priority for the missile barrage: confirm crosshair-nearest first then proximity (you were unsure); how many missiles in a full salvo and does an 8th target ever show; does the salvo fire when you release the button or auto at full lock?
3. Pursuit lock circle: how long does it take to close (the file says 2.0 s; footage max was 1 s), and do you hold the button during it?
4. Battle-mode orange diamond: is there any delay at all, and can you lock a Cobra/tank/drone/soldier?
5. EMP burst: how long are cars/tanks/drones disabled and does the duration scale with how long you charge; what does the player see on the car (lightning only)? Can you charge-hold for levels 2/3/4?
6. Immobiliser (EMP missile): can it be fired without the tracker having tagged the target first; what happens to tanks and helicopter drones versus cars (your 11-07 lead: car disabled permanently with no explosion, drones stunned)?
7. Tracker: how does the signal visually weaken (icon colour, size, fade); what is the maximum range; yellow versus grey meaning exactly?
8. Hacker: which targets can it hack besides SAM (drones in your game, tanks)? What does the beam look like on a SAM, and does the hack time-out?
9. Winch: when is it used in play (puzzles, pulling objects, towing cars, zip-line to rooftops), and how far does it reach?
10. Sonar: does the pulse reveal enemies through walls with outlines or only radar dots; how far; does Batman scan things on the pulse?
11. Booster: does the nozzle ring deploy visibly each boost; does it close after; is there a sound per deploy?
12. Riot suppressor: how does it switch from the Vulcan (button/timing) and what does the crosshair look like?
13. 60 mm cannon: reload circle length (visual), splash radius feel, camera shake? Vulcan bloom: how many seconds to full red?
14. Do you play with a gamepad or mouse and keyboard? (decides NEW-WPN-32 and which JC3 fire actions we map)
15. Rank request: where do cannon, Vulcan, riot, pods and winch sit in the build order? (`OPERATOR_PRIORITIES.md` says ask.)
16. Is the Joker missile launcher (a Joker-variant weapon) required for the release?

## 6. (d) Risks

- JC3 has two driver fire paths and no vehicle weapon-select action; D-7 "all 11 weapons" may need engine behaviour (spare pointers, rebound keymap) that data cannot prove. Fallback must remain lore-first (user rule: amend, never accept), but acceptance is only knowable in game.
- Lock-on hold (2.0 s) and 8-target salvo have no JC3 member (0 of 4,054 tune rows); composed build may not behave like BmAK (K-11 UNKNOWN).
- Disable mechanism `is_disabled_by_emp` has 0 bindings in 1,941 entries; EMP burst and Immobiliser might not stall a car at all (NEW-WPN-19 only oracle).
- Hacker allegiance flip has no data member; may fall back to compose/visual only. Winch has 0 functional winch classes in JC3; blocked row, no build brief.
- Missile tune sits on a bullet-weapon carrier (L-1); weapon may spawn but not seek.
- Documentation drift: `STATUS.md` lists winch under `out`, the ledger lists T-WP6 `blocked`; `GRAB_BACKLOG.md:1799` text and tracker disagree with specs numbering (B-24/B-25); D-3 text partly superseded; `tmp/freebuff/QUEUE_MAP.md` says 59 briefs, wave 9100-9110 still queued, RC4 stale pins. A small model could misread any of these.
- Test ban means weapons are 0% observed; any mistaken static decode (e.g. wrong unit for AutoAim angle, projectile velocity /100, `Projectile.Speed`) only shows in game.
- 36,000 HP health gate makes JC3 weapon balance (K-1..K-9: pistol 1,200 hits) untested vs real enemy damage; damage rows (NEW-WPN-25) UNKNOWN.
- Weapon audio: missile loop events `missing-object`; `weapons#408` loop click RED earlier; bank route is private-copy only.
- Install risk: `Rollback091` deleted payload files in RC2 (`install_v2` fix exists for copies only).
- Pursuit-only RC means battle weapons have no mode to live in.
- Parallel small models editing `T_ROWS.jsonl` serially (9030-9033) is a single-file bottleneck.

## 7. (e) Remaining effort (estimates, not measurements)

Assumptions: ~100 small-model briefs/day; each build brief EST 55 min and 1-3 attempts; chain steps with `AFTER:` run serially; in-game tests need the operator and one fix loop per weapon.

| phase | work | agent sessions (briefs) | calendar days |
|---|---|---:|---:|
| Queue head to scaffold | 9031-9033, 9100 | 5-8 | 0.5-1 |
| Entity + slots + effects + HUD base | 9101, 9102, 9160 (HUD shared), NEW-WPN-26/27 | 15-25 | 1-2 |
| Rank 1 chain | 9103, 9104, 9105, NEW-WPN-8/17/20 | 20-35 | 2-3 (serial) |
| Ranks 2-5 + unranked builds | 9106-9110, NEW-WPN-5/6/7/10-16/21-23/34/35/37, NEW-WPN-41/44/45 | 40-60 | 3-5 |
| Audio + input + FX per weapon | NEW-WPN-4, -13, -14, B-26 route (9150, shared), winch | 20-35 | 2-3 |
| Merge + review + verify | 9119, 9190-9199, NEW-WPN-24/28/29/46 | 12-20 | 1-2 |
| **Agent total (desk)** | | **~110-185 briefs** | **~8-14 working days** (about 1.5-2.5 weeks including reruns) |
| Operator in-game tests | Q-1 (weapons at a wall), Q-3 combat (7 items ~45 min nominal), plus probes NEW-WPN-2/3/19/21 and a fix loop per weapon: ~5-8 sessions of 1-2 h | operator time ~8-14 h | spread over 1.5-3 weeks (each failed take returns to BUILD + reinstall, ~1 day turnaround) |
| Release | NEW-WPN-33, -48 | 3-6 | 1 |

Expected whole-landmark finish to in-game-verified release: 3-5 calendar weeks if the engine accepts the composed slot/disable designs; open-ended if the spare-pointer probe or EMP disable probe fails (then redesign briefs per weapon). The earliest operator-dependent milestone is the first rank-1 test (tracker + Immobiliser), reachable only after approximately 6-9 working days of agent work plus `APPROVED_Q.txt`.
