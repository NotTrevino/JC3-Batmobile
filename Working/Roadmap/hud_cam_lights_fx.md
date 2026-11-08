# Landmark map: HUD, CAMERA, LIGHTS & EFFECTS (as of 2026-11-08, read-only survey)

Rules applied (AGENTS.md): no pretrained JC3 knowledge used as evidence. Every claim cites a local file; absent = UNKNOWN. Nothing in the project was edited. No game launched.

Path shorthand (root `E:\Modding\JustCause3\JC3-Batmobile\`):
- GB = `GRAB_BACKLOG.md` (cards sections 5-9, tracker section 12 from line 1809)
- RPT = `tmp\freebuff\reports\`   Q = `tmp\freebuff\queue\`   WT = `Working\Translation\`
- RB = `Research\BatmobileGrab\`   RJ = `Research\JC3Grab\`   T6 = `WT\T6_HUD_CAMERA.md`
- OP = `OPERATOR_PRIORITIES.md`   GF = memory `bmak-gameplay-facts.md`

Where this landmark stands (`STATUS.md`, `tmp\freebuff\QUEUE_MAP.md` RC5 section, `Builds\bm-RC4\receipt.json` not_done): GRAB and TRANSLATE are desk-complete for HUD/camera/lights/FX. RC4 carries the camera tune (`bat_base.ctunec`), a 24-row lamp module and the nitro-flame placement, but NO payload for B-17 and B-25 and no HUD at all. RC5 branch briefs 9102 / 9142 / 9160 / 9174 exist but have no report yet (only 4 R-wave rc5 reports exist in `RPT`). Nothing here is behaviour-verified in game (`STATUS.md`: 0 rows fully verified). Test ban stands (`Working\Q\APPROVAL_REQUEST.md` line 5).

---

## 1. TASK TABLES

Legend. stage: GRAB / TRANSLATE / BUILD / VERIFY / PILOT / TEST / RELEASE. status: done / partial / queued / todo / blocked. size: S<=1 session, M 1-3, L 1-2 wk. "Gate-T" = needs an in-game take = human operator + `APPROVED_Q.txt` (absent by design). NEW-HUD-4 is the Scaleform gate (see (b)). IDs prefixed NEW- are inferred missing tasks.

### 1A. HUD (25 BmAK modules; Batmobile cluster; radar; lock/reticle)

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| G1-HUD-INV | Inventory BmAK HUD: 25 `RHudModule*` classes, 19 carved movies, 252 `UC_*` setters; Batmobile module = 99 scripts / 37 setters | GRAB | done | - | all HUD | M | `RB\HUD.md`, `RB\HUD_INVENTORY.json`, `RB\HUD_INTERFACES.json`, `STATUS.md` |
| G1-HUD-SPEC | HUD behaviour contract (31 setters, 112 frame labels, 7 constants, health contract) | GRAB | done | - | T-HUD* | S | `RB\HUD_SPEC.json`, `Tools\scripts\hud_spec.py --check` |
| G3-HUD-CLUSTER | Placed clips of the dash cluster (Health, BoostMovie L/R, Combo, RemoteInterface, ClockTimer), 6/6 confirmed vs AS3 | GRAB | done | - | NEW-HUD-6/7 | S | `RPT\G3-HUD-CLUSTER.md`, `WT\HUD_CLUSTER_ELEMENTS.md` (13/13), `Working\HUD\CLUSTER.json` |
| G3-HUD-RADAR | Radar module decode: 15 `UC_*`, 80 px/unit, stage 1024x720; world radius, icon px sizes, pulse period UNKNOWN | GRAB | done | - | NEW-HUD-10/11 | S | `RPT\G3-HUD-RADAR.md`, `WT\HUD_RADAR_RECHECK.md` (5 same, 3 no source), `Working\HUD\RADAR.md` |
| G1-HUD-SPEEDO | Speedometer is native debug readout (`bDebugSpeedometer`, off), not a HUD movie | GRAB | done | - | T-HUD1 | S | `RB\SPEEDOMETER.md`, `bmak_speedometer.py --check` |
| G1-HUD-ICON | Radar icon classes in BmAK data: module has NO class switch; colour is symbol content; 0 tokens for helicopter/police/military/hack | GRAB | partial | - | NEW-HUD-10 | S | `RPT\hud-radar-dash-plans-v2.md` s2.2, `RPT\radar-minimap-icon-plan.md` |
| NEW-HUD-23 | Disposition table for ALL 25 BmAK modules (only Batmobile/Targets/Radar/Health/Scanner/Alerts look relevant; the rest have no stated in/out call) | GRAB | todo | - | NEW-HUD-24 | S | `RB\HUD.md` s6 ("14 of 15 have no JC3 host"), `RB\HUD_INVENTORY.json` native_modules |
| NEW-HUD-GRAB-1 | Decode remaining HUD UNKNOWNs: `Cap` Decrease frame length (F3), damage-number text arg (U3), `ch1040` (U8), icon sizes, radar world radius (native), `BoostCooldown` tiers 1/2 (U1) | GRAB | todo | - | NEW-HUD-6/7/18 | M | `RPT\hud-radar-dash-plans-v2.md` s3, `RPT\hud-cluster-closest-system-plan.md` s8 U1-U8 |
| NEW-HUD-GRAB-2 | JC3 side: decode `hud_code\poi.as` icon `Update` (label placement U7, sub-frame animation for rotor), `m_CurrentType` delivery (U4) | GRAB | todo | - | NEW-HUD-10/13 | S | `RPT\hud-radar-dash-plans-v2.md` s2.2 end, `hud-cluster-closest-system-plan.md` U4/U7 |
| G2-25 | JC3 HUD vehicle-weapons API: 2 slots, Init/UpdateVehicleWeapons, 14 reticle shapes, lock-on POI 21, 0 heat args | GRAB | done | - | T-19 | S | GB tracker line 1847, `RJ\JC3_HUD_WEAPONS.md` |
| T-HUD1 | Speedometer: ledger says "reuse MCI_speedo"; operator lead = DISABLE it in the Batmobile; plan v2 H12 = suppress. Ledger row stale | TRANSLATE | partial | NEW-HUD-1 | NEW-HUD-9 | S | `T6` line 20, OP "HUD leads", `RPT\hud-radar-dash-plans-v2.md` H12 |
| T-HUD2 | Boost gauge: `UC_SetBoostLevel(0..100,upgrade)` -> `InitVehicleNitrous(recharge=level/100)`; badges: id 614 free per plan | TRANSLATE | queued | NEW-HUD-1 | NEW-HUD-7 | S | `T6` line 21, plan v2 H6/H7 |
| T-HUD3 | Health: `UC_SetHealth(h,max)` -> vehicle health bar, identity 0..1 | TRANSLATE | queued | - | NEW-HUD-6 | S | `T6` line 22 |
| T-HUD4 | Armour overlay (health>1): ledger `out`, plan v2 proposes `map`; operator fact is a single health bar | TRANSLATE | partial | operator Q (c)1 | - | S | `T6` line 23, `RPT\hud-cluster-closest-system-plan.md` s10 |
| T-HUD5, T-HUD11..20 | Weapon slots/name/icon/reticle/cooldown/heat/lock/ammo (T-19 completion): 6 map, 2 partial, 2 out | TRANSLATE | done | - | weapon branches | S | GB tracker line 1868, `Tools\scripts\t19_hud.py --check`, `T6` lines 48-57 |
| T-HUD6..10 | Battle/zoom overlay, winch meter, energy system, combo/medals, occupants: `out` (T-10) | TRANSLATE | done (out) | - | NEW-HUD-22 | S | `T6` lines 25-29 |
| T-HUD15 | Vulcan accuracy frame -> `reticle_size`: scale UNKNOWN | TRANSLATE | partial | Gate-T | NEW-HUD-15 | S | `T6` line 52 |
| T-HUD17/19 | Vulcan heat; missile target-kind family: stated absence both sides | TRANSLATE | done (out) | - | - | S | `T6` lines 54, 56 |
| T-HUD18 | Missile lock: one rotating POI 21 (1.5 s); no AutoAim->POI link in files | TRANSLATE | partial | NEW-HUD-5 | NEW-HUD-14 | S | `T6` line 55, `RPT\lock-on-reticle-hud-link.md` |
| T-HUD21 | Pursuit lock = shrinking circle in edge-gapped diamond (GF) | TRANSLATE | partial | NEW-HUD-GRAB-1 | NEW-HUD-14 | S | `T6` line 215 (s1b), GF |
| T-HUD22 | Battle lock = instant orange diamond; no diamond element decoded in JC3 | TRANSLATE | blocked | NEW-HUD-4 (art) | NEW-HUD-14 | S | `T6` line 216 (UNKNOWN) |
| T-HUD23 | Vulcan bloom grows, crosshair reddens, no lockout | TRANSLATE | partial | - | NEW-HUD-15 | S | `T6` line 217, `RPT\vulcan-capture-fire-and-overheat-timing.md` |
| T-HUD24 | 60 mm cannon reload circle = 0..1 cooldown arc swept 360 | TRANSLATE | partial | - | NEW-HUD-16 | S | `T6` line 218, `RPT\cannon-60mm-reload-circle-plan.md` |
| NEW-HUD-1 | Apply plan-v2 ledger changes: T-HUD1 -> suppress; badge -> map; armour decision; ADD ROWS for operator leads that have no T-HUD row (health top-left in battle, afterburner left in pursuit, cooldown gauge left of it, radar class icons) | TRANSLATE | todo | 9033 review | T-HUD1/2 | S | `RPT\hud-cluster-closest-system-plan.md` s10 ("proposal only"), OP |
| NEW-HUD-2 | Health bar top-left, visible in battle mode: `UC_SetHealthBarVisible(true,"Delayed")` forced in battle; target screen (32.8,55.7) | TRANSLATE | partial (plan only) | NEW-HUD-4 | NEW-HUD-6 | S | `RPT\hud-radar-dash-plans-v2.md` s4 |
| NEW-HUD-3 | Mode signal for HUD: boost gauge in pursuit, health in battle - what tells the HUD the mode? needs B-12 mode pair + native `m_CurrentType` | TRANSLATE | blocked | B-12 (modes unbuilt), NEW-HUD-5 | NEW-HUD-6/7 | M | `Builds\bm-RC4\receipt.json` not_done, `RPT\hud-cluster-closest-system-plan.md` U4 |
| **NEW-HUD-4** | **Scaleform gate: establish by bytes whether a modified/private `ui/hud.gfx` can be (a) authored (no GFx/SWF writer exists in repo; ffdec only used as exporter), (b) packed at the path JC3 loads, (c) loaded (AVM2 GFx v0f tag compat, U6), (d) selected per vehicle or only globally (R7)** | GRAB | todo | - | NEW-HUD-6..21, T-HUD22 | M | `Q\9160-rc5-hud-build.txt`, `RPT\hud-cluster-closest-system-plan.md` U5/U6 + s9 steps 1-2, `RB\HUD.md` s8 |
| NEW-HUD-5 | Caller census/probe: do native pushes (`UpdateVehicleNitrous`, `UpdateVehicleWeapons`, health paint, `m_CurrentType=4`) reach our entity if it carries donor nitro/weapon components? | GRAB/TEST | blocked | Gate-T (live slot read Q-3 #3) | NEW-HUD-3, T-HUD18, 6, 7, 14 | M | `STATUS.md` ("no entity->hud.gfx caller"), `RJ\JC3_HUD_WEAPONS.md` s7, plan v2 s5 |
| NEW-HUD-6 | BUILD health bar top-left in battle mode | BUILD | todo | NEW-HUD-4/2/3 | NEW-HUD-24 | M | `Q\9160`, plan v2 H1-H3 |
| NEW-HUD-7 | BUILD afterburner gauge left in pursuit (`MCI_nitro_meter` to (59.1,449.6)) + quick-recharge cooldown gauge to its left (`MCI_radial_loader_cooldown`, 1-t/12, 12.0/6.0/2.0 s tier 0) | BUILD | todo | NEW-HUD-4/3/5/8, GRAB-1 (U1) | NEW-HUD-24 | M | plan v2 H6/H8, `Working\HUD\CLUSTER.json` |
| NEW-HUD-8 | Reconcile what the player sees as the "second cooldown gauge": BmAK has no cooldown element (native only) | GRAB | todo | operator Q (c)2 | NEW-HUD-7 | S | plan v2 s4 row 4, OP |
| NEW-HUD-9 | BUILD speedometer suppression for Batmobile only; first the 5-min probe (`MCI_speedo.visible=false`, Batmobile vs vanilla car) | BUILD | todo | NEW-HUD-4/5 | NEW-HUD-24 | S | plan v2 s4, s6 step 1, `RPT\dash-hud-unknown-closing.md` N23 |
| NEW-HUD-10 | Radar icon art: cops, military, tracked (green), hacked red->green pair, tank (bigger via `m_IconScale`), helicopter (arrow + spinning blades): 6 authored icons + atlas entry | BUILD | todo | NEW-HUD-4, G1-HUD-ICON, operator Q (c)4 | NEW-HUD-11 | L | OP, `RPT\radar-minimap-icon-plan.md`, plan v2 s2.2 |
| NEW-HUD-11 | Radar driver: per-frame vehicle->POI creator (0 vehicle `CreatePoi` calls in movie; script hook UNKNOWN); facing arrow is 8-way `m_ArrowState` (accuracy cost vs BmAK continuous bearing) | BUILD | blocked | NEW-HUD-4/5, script-hook capability UNKNOWN | NEW-HUD-12/13 | L | `RPT\radar-minimap-icon-plan.md` s8 ("both unproven"), `WT\HUD_RADAR_RECHECK.md` |
| NEW-HUD-12 | Hacked-vehicle state source (red->green) | BUILD | blocked | NEW-HUD-11, B-19/9108 | - | M | plan v2 s2.2 ("UNKNOWN state source"), OP |
| NEW-HUD-13 | Helicopter spinning-blade icon (POI icon is one static clip) | BUILD | blocked | GRAB-2, NEW-HUD-4 | - | M | plan v2 s2.2 last row |
| NEW-HUD-14 | Lock markers: pursuit circle+gapped diamond, battle orange diamond (new art), POI 21 creation by missile branch 9105 | BUILD | blocked | NEW-HUD-4/5, 9105, T-HUD22 | NEW-HUD-24 | L | `T6` s1b, `Q\9105`, `RPT\lock-hold-salvo-reticle-plan-v2.md`, GF |
| NEW-HUD-15 | Vulcan crosshair bloom + red via `UpdateWeaponReticle(reticle_size, weapons_look)`; recorded capture is the oracle | BUILD | todo | T-HUD15, NEW-HUD-5 | NEW-HUD-24 | M | `RPT\vulcan-capture-fire-and-overheat-timing.md`, GF |
| NEW-HUD-16 | Cannon reload circle (cooldown arc 0..1 over 2 s) | BUILD | todo | NEW-HUD-5 | NEW-HUD-24 | S | `RPT\cannon-60mm-reload-circle-plan.md` |
| NEW-HUD-17 | Tracker POI: yellow (`POI_TYPE_MISSION` 19) / grey (`POI_TYPE_LOCKED` 24) with distance string; signal weakens with range, visible through walls (GF); B-21 | BUILD | todo | B-21/9103, NEW-HUD-5 | NEW-HUD-24 | M | `RPT\tracker-lock-hud-plan.md`, GF, OP |
| NEW-HUD-18 | Damage number / hit marker: signature (part, amount, duration, frames); screen position UNKNOWN | BUILD | todo | GRAB-1 (U3,U7) | - | M | plan v2 F1/F2, H4/H5 |
| NEW-HUD-19 | Weapon-slot HUD content: names/icons (602,603,618,619; 614 boost badges), `infiniteAmmo=true` hides counters | BUILD | todo | 9101 slots | NEW-HUD-24 | S | `T6` lines 48-57, `RPT\four-weapon-slot-build-plan.md` |
| NEW-HUD-20 | Four visible weapon slots (`MCI_vehicle_weapons2/3`, hard-sized to 2) via movie extension | BUILD | blocked | NEW-HUD-4 | - | M | `RPT\four-weapon-slot-build-plan.md` B8 line 194 |
| NEW-HUD-21 | Gadget/radial select HUD for Batmobile gadgets (`RadialGadgetSelect` pairing unconfirmed) | TRANSLATE | todo | NEW-HUD-4 | - | M | `RPT\gadget-wheel-input-plan.md`, `RB\HUD.md` s8 |
| NEW-HUD-22 | Re-open `out` HUD rows under the closest-system rule (winch meter -> grapple lead, energy system, remote interface + static overlay); memory forbids "JC3 has no system" | TRANSLATE | todo | - | - | M | `T6` lines 25-29, `RPT\remote-control-range-static-overlay-plan.md` (HALTED), OP leads |
| NEW-HUD-25 | Layout re-fit: BmAK stage 1024x720 (cluster math 1024x768) vs JC3 1280x720; derive pixel coords once | BUILD | todo | NEW-HUD-4 | NEW-HUD-6/7 | S | `WT\HUD_RADAR_RECHECK.md` row 7, `hud-cluster-closest-system-plan.md` s6 |
| NEW-HUD-26 | Build script `Tools\scripts\rc5_hud.py` (--write/--check) + branch record; parse check of each edited file | BUILD | queued (9160) | 9100, 9103, plans v2 | NEW-HUD-24 | M | `Q\9160-rc5-hud-build.txt` |
| NEW-HUD-24 | VERIFY offline: `bmak_hud_cluster`, `hud_spec`, `bmak_speedometer`, `t19_hud`, `hud_radar_recheck`, `bm_rc4`, `v03_wiring` stay green; gfx parse check | VERIFY | todo | NEW-HUD-26 | PILOT | S | `RPT\hud-cluster-closest-system-plan.md` s9 |
| NEW-HUD-27 | PILOT HUD card (rest/cannon/fire frames; speedo hidden vs vanilla; boost ring 12.0 s +/-0.3; 8 arrow headings; tank larger; heli distinct) | PILOT | partial | NEW-HUD-26 | TEST | S | `RPT\pilot-card-looks-and-audio.md` s3, plan v2 s6 step 6 |
| NEW-HUD-28 | TEST HUD in game (private copy loads, `UpdateVehicleWeapons` runs, type=4, pass bands) | TEST | blocked | `APPROVED_Q.txt`, NEW-HUD-26 | RELEASE | M | `Working\Q\APPROVAL_REQUEST.md`, Q-3 #3 |
| NEW-HUD-29 | RELEASE concerns: global `hud.gfx` replacement affects every vehicle and on-foot; compat, rollback guard, install size | RELEASE | todo | NEW-HUD-4(d) | release | M | plan v2 s6 (R7), `Working\Installer\install_v3.ps1` |

### 1B. CAMERA

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| G1-CAM | Decode `R3rdPersonCamera`: 33 values, 13 configs, boom composition `Loc=anchor-fwd*dist+Rot*Sit` (18/18) | GRAB | done | - | T-CAM* | M | `RB\CAMERA.md` s2b, `bmak_camdecode.py --check`, `STATUS.md` |
| G1-CAM-HELP | Native tracking helper = `Vehicle.ExitOffset` (static disasm; source exe digest of CAMERA.md UNKNOWN) | GRAB | done | - | - | S | `RB\CAMERA_HELPER.md` |
| G2-CAM | JC3 `GenericVehicleCamera` 800 B struct, one `CCameraRef` per entity, 8 shipped vehicle tunes | GRAB | done | - | T-CAM* | S | `Working\Camera\CAM_REF.md`, `Working\Audio\car_base.xml` |
| NEW-CAM-GRAB-1 | Read the unread configs: `BatmobileConversationCamConfig`, `RidingCarCamFOV` geometry | GRAB | todo | - | NEW-CAM-12 | S | `RPT\cameras-per-mode-plan.md` s2 ("values not read this pass") |
| T-CAM1 | Camera1 = preset; Camera2/Bonnet other | TRANSLATE | done | - | NEW-CAM-2 | S | `T6` line 126 |
| T-CAM2 | FOV 85h/95h -> vertical 55/63 over [5,108] km/h; corrected clause: 105h = 72.49v (not 68), "95 is a gap" refuted; corrected row proposed not applied | TRANSLATE | partial | NEW-CAM-1 | - | S | `T6` line 127, `WT\T_CAM2_PROPOSAL.md`, `RPT\t-cam2-contradiction.md` |
| T-CAM3 / T-CAM4 / T-CAM7 | FOV speed range [5,108]; extra translation keep; pitch limits keep | TRANSLATE | done | - | - | S | `T6` lines 128, 129, 132 |
| T-CAM5 / T-CAM12 | Chase composition `CameraPosition [0,1.30,7.00]`, `LookAtPoint [0,1.55,0]`; boom 400 cm additive to sit | TRANSLATE | done | - | NEW-CAM-15 | S | `T6` lines 130, 137, `STATUS.md` |
| T-CAM6 / T-CAM13 | Roll 0.3 -> 0.38; collision start x1.61 -> 1.6 m | TRANSLATE | done | - | NEW-CAM-15 | S | `T6` lines 131, 138 |
| T-CAM8 | Head impulse 0.5 / drift orientation 0.15: no JC3 member; no closest-system plan written | TRANSLATE | blocked | NEW-CAM-10 | - | S | `T6` line 133 |
| T-CAM9 | Smoothing 30/12/10000/airborne 12 vs JC3 spring 0.08/0.12/1.0: NO unit bridge | TRANSLATE | blocked | NEW-CAM-9 (Gate-T) | - | M | `T6` line 134, `STATUS.md` |
| T-CAM10 | Battle FOV 60h / winch 60h / AP 40h: superseded by T-15 (second per-entity `.ctune`) | TRANSLATE | done (superseded) | - | NEW-CAM-4 | S | `T6` line 135, GB tracker T-15 |
| T-CAM11 | Boost shake 35, wheelspin 50x50x25, 0.1 s: no member in `GenericVehicleCamera` | TRANSLATE | blocked | NEW-CAM-8 | - | M | `T6` line 136, `RPT\cameras-per-mode-plan.md` s6 |
| B-CAM (Batch F) | `bat_base.ctunec` (8 values) + 2-byte `.epe` ref rename; test-091, carried in RC4 | BUILD | done (file-level) | - | NEW-CAM-15 | S | `Working\Camera\CAM_TUNE.json`, `T6` s4, `Builds\bm-RC4\receipt.json`, `bmak_camfile.py check` |
| NEW-CAM-1 | Apply `T_CAM2_PROPOSAL` corrected row; resolve cameras-per-mode boost `[63,67.7]` vs 72.49 | TRANSLATE | todo | 9033 | NEW-CAM-3 | S | `WT\T_CAM2_PROPOSAL.md`, `RPT\cameras-per-mode-plan.md` s4 |
| NEW-CAM-2 | Chase-2 preset (`[0,1.55,9.00]`): needs second camera object on entity (UNKNOWN in JC3) or variant | TRANSLATE | blocked | camera-object-count probe | - | M | `RPT\cameras-per-mode-plan.md` s4 note |
| NEW-CAM-3 | Boost camera state (BmAK 600 back/80 up, 95h, smoothing 10000): JC3 FOV is a min/max pair over speed, no state | TRANSLATE | blocked | state selector UNKNOWN | - | M | plan s4, T-CAM2 proposal |
| NEW-CAM-4 | Battle camera tune: `[0,2.05,13.50]`, look `[0,0.05,0]`, FOV [36,36] (60h), rigid pivot; second tune + selection with the mode variant | BUILD | blocked | B-12/9130, tune selection | NEW-CAM-5 | M | plan s4 Battle, `Q\9130` |
| NEW-CAM-5 | Battle+winch camera (`[0,4.05,12.50]`), anti-personnel 40h `[23.2]` | BUILD | todo | NEW-CAM-4, winch decision | - | S | plan s4 |
| NEW-CAM-6 | Battle-mode nose-to-camera yaw coupling (operator fact: nose swings toward where camera points) | TRANSLATE | todo | 9122 | - | M | GF, `Q\9122-rc5-drive-modes-and-yaw.txt` |
| NEW-CAM-7 | "Chasing" takedown camera (`[0,-2,25]`, 80h, default pitch -65.9deg not a JC3 member) | TRANSLATE | blocked | closest-system plan | - | M | plan s4 Chasing, s6 |
| NEW-CAM-8 | Camera shake: author `CameraShakeModifierParams` instance in `.ctunec` (needs ADF writer that appends type + instance; `bmak_camfile.py` only rewrites existing rows) | BUILD | todo | ADF append writer (absent) | T-CAM11 | L | `RPT\cameras-per-mode-plan.md` s6 steps 1-3 |
| NEW-CAM-9 | Spring "felt test": one-variable A/B takes (candidate yaw 0.12/0.6) | TEST | blocked | Gate-T | T-CAM9 | M | plan s5 last paragraph |
| NEW-CAM-10 | Closest-system plan for head impulse / drift orientation / airborne smoothing | TRANSLATE | todo | - | T-CAM8 | S | `T6` line 133, memory closest-system-rule |
| NEW-CAM-11 | Remote-control view / homing (static overlay halted by plan) | TRANSLATE | blocked | NEW-HUD-22 | - | M | `RPT\remote-control-range-static-overlay-plan.md` |
| NEW-CAM-12 | Bonnet/cockpit camera and conversation/riding-car cameras: no JC3 cockpit camera found | TRANSLATE | todo | NEW-CAM-GRAB-1 | - | S | `T6` T-CAM1, plan s2 |
| NEW-CAM-13 | Aspect-ratio dependence: conversion assumes 16:9 | TRANSLATE | todo | operator Q (c)9 | - | S | plan s1, `WT\T_CAM2_PROPOSAL.md` |
| NEW-CAM-14 | Camera ref survives standalone entity rebuild (9101): re-verify `CarCameraRef -> bat_base` | BUILD | queued | 9101 | NEW-CAM-15 | S | `Q\9101`, `Working\Camera\CAM_REF.md` |
| NEW-CAM-15 | TEST A15 camera drive: distance at rest, FOV stops at 108 km/h, roll follows lean, no clipping through taller body | TEST | blocked | `APPROVED_Q.txt` | RELEASE | S | `T6` s4 ("A15 drive pending"), `APPROVAL_REQUEST.md` Q-2 |
| NEW-CAM-16 | PILOT camera cards per mode (no camera card exists; only `VEHICLE_CAM`=B rows) | PILOT | todo | NEW-CAM-4 | TEST | S | `RPT\pilot-card-looks-and-audio.md` line 27 |
| NEW-CAM-17 | Fix stale `CAM_REF.md` s5/s6 status text | VERIFY | todo | - | - | S | `RPT\review-CAM-1.md` |

### 1C. LIGHTS

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| G1-17 | BmAK light colours/intensities/cones: 36 rig components | GRAB | done | - | T-18 | S | GB line 1824, `RB\LIGHTS.md` |
| G1-LGT-SOCK | Light sockets in JC3 space | GRAB | done | - | B-03 | S | `RB\LIGHT_SOCKETS.md`, `RPT\LIGHTS-sockets.md` |
| G2-33 | JC3 light system: 3,217 `VehicleDynamicLights` entries, 25 members; `.epe` list is a different list; which renders UNKNOWN; `CarLight` params UNKNOWN | GRAB | done (UNKNOWNs open) | - | NEW-LGT-2 | S | GB line 1855, `RJ\LIGHT_SYSTEM.md` |
| NEW-LGT-2 | Settle which list renders (module vs `.epe` `SVehicleLight`) | GRAB/TEST | blocked | Gate-T | all lamps | S | GB line 1855, `RPT\correction-8394-light-units-domain.md` |
| NEW-LGT-1 | Units bridge for `range/angle/multiplier/falloff_start` (RC4 writes 60 m / 70 deg outside shipped max 50/50; multiplier 1.0 and falloff 0.8 are stand-ins) | TRANSLATE | blocked | Gate-T stock-vs-mod take (B-25 step 3) | NEW-LGT-7, T-LG6 | M | `RPT\correction-8394-light-units-domain.md`, GB line 1587, `Q\9142` |
| T-18 | Lights translation: 28 rows = 22 mapped + 6 named omissions | TRANSLATE | done | - | B-07 | S | GB line 1867, `WT\T14_LIGHTS.md` |
| T-L1..L7 | Lights T-1 rows: L1/2/3/5/6 `epe`; L4, L7 superseded by T-18 | TRANSLATE | done | - | - | S | `WT\T_ROWS.jsonl` |
| T-L8..L16, L24, L35 | Head/brake/dash/boot lamps: donor rows repointed with BmAK colour, boot custom | TRANSLATE | queued (`next`) | - | NEW-LGT-12 | S | `WT\T_ROWS.jsonl`, `Working\Lights\bm_lightrig.json` |
| T-L13/L14/L20 | Wheel-arch lamps as custom `preset_id 0` entries on new arch parts 42/43 | TRANSLATE | queued | - | - | S | `WT\T_ROWS.jsonl`, GB line 1867 |
| T-L17 | Battle spotlight (`Front_Secondary_Head`) "row wrong": colour graph 0.604/0.604/0.953 vs BmAK white 1/1/1; cone 60 deg / volume 0.25 outside shipped set; fix proposed not applied | TRANSLATE | partial | NEW-LGT-3 | NEW-LGT-9 | S | `WT\TL17_PROPOSAL.md`, `RPT\light-entry-11.md`, `RPT\correction-8394-light-units-domain.md` |
| NEW-LGT-3 | Apply T-L17 proposal to ledger and row 11 colour (1,1,1); intensity stays multiplier 1.0 | TRANSLATE | todo | 9033 | NEW-LGT-9, 9142 | S | `WT\TL17_PROPOSAL.md` s1 |
| T-L18..L20 | Battle head lamps (custom entries) | TRANSLATE | queued | - | NEW-LGT-9 | S | `WT\T_ROWS.jsonl` |
| T-L21..L23, T-L10 | Forensics spot/heads and muzzle light (enable-state is T-25) | TRANSLATE | queued | T-25 | - | S | `WT\T_ROWS.jsonl`, `RPT\muzzle-and-forensics-lights.md` |
| T-L28 / T-L30 | Flare entries with null socket AND null bone: need `_LIG` node + `CarLight` block on the body part | TRANSLATE | blocked | NEW-LGT-4 | B-25 | M | `WT\T_ROWS.jsonl`, `correction-8394` s1 end |
| NEW-LGT-4 | Unblock T-L28/T-L30 (body-hosted HeadLight pattern, author `_LIG` + CarLight block) | BUILD | todo | NEW-LGT-5 | B-25 | M | `Q\9142`, `WT\T_ROWS.jsonl` |
| NEW-LGT-5 | Prove orphan sockets `HeadLight1c`/`HeadLight2c` absent from shipped mesh | GRAB | todo | - | NEW-LGT-4 | S | GB B-25 card step 2 |
| T-L25..27, L29, L31..34 | Lens-flare rows: emissive lens block + volumetric halo (glow-only); sprite binding is T-24 | TRANSLATE | queued (`next`) | T-24 | B-25 | S | GB line 1872, `RPT\lens-flare-carriers.md` |
| T-LG1/LG3/LG6 | Module recount 18 entries; 4 rows at 30/40; replacement values range=Radius/100 etc. | TRANSLATE | queued | NEW-LGT-1 | - | S | `WT\T_ROWS.jsonl`, `RPT\keep-audit-lights.md` s5 |
| T-LG2/LG4/LG5 | LG2 keep (donor join only), LG4 superseded by T-18, LG5 battle lamps ride HeadLight | TRANSLATE | done | - | NEW-LGT-9 | S | `WT\T_ROWS.jsonl` |
| T-24 | Lamp-bound flare sprite: attach `effects\flare\headlight_flare_01.effc` (8,079 B, in 160 `.ee`) via `SAttachedEffect` at 6 sockets | TRANSLATE | todo | NEW-FX-1 | B-25 | S | GB lines 1244, 1872, `RPT\apply-light-rows.md` |
| T-25 | Lamp state/pulse carrier (muzzle fire, `bForensicsLightActive`); `blinking` flag with no period decoded | TRANSLATE | todo | - | T-L10/L21..23 | S | GB lines 1257, 1873, `RPT\t25-lamp-state-carrier.md` |
| B-03 | Emissive `CarLight` blocks + 8 lamp parts / 24 RBMs / 4,576 emissive faces | BUILD | done | - | B-07 | M | GB line 1946, `Working\Appearance\build_lights\lights_manifest.json` |
| B-07 | Lights module rewrite: 21->18 entries, T-L17 new row, 6 custom rows | BUILD | done | - | 9142 | S | GB line 1956, `Working\Lights\bm_lightrig.json` |
| B-25 | Lens flares + light units (17 flare entries, 4 members): NO payload in RC4 | BUILD | todo | T-24, NEW-LGT-1/4/5 | VX | M | GB line 1587, tracker 1967, `Research\specs\B-25.md`, RC4 receipt not_done |
| 9142 | RC5 lights branch: bridged units with error shown, 17/17 flares named, brake/reverse state, underglow as emissive wheel material; `rc5_lights.py` | BUILD | queued | 9100 | 9190 | L | `Q\9142-rc5-lights-flares-beams.txt` |
| NEW-LGT-6 | Brake/tail/reverse: BmAK has 2 TailLight entries (FF2600, r150, falloff 6), tail vs brake differ only in LensFlare objects + brake-trail particles; NO reverse lamp in BmAK | BUILD | todo | NEW-LGT-1, T-25 | 9142 | M | `RPT\taillight-brake-reverse-plan.md` |
| NEW-LGT-7 | Headlight beam: two spot components per socket (70/20 deg, 60 m, [138,197,246], Brightness 0.15; narrow 18 m falloff 2); JC3 one cone + `.epe` `spot_inner_angle`; BmAK "high beam" state not identified | TRANSLATE | partial | NEW-LGT-1, operator Q (c)8 | 9142 | M | `RPT\headlight-beam-plan.md` |
| NEW-LGT-8 | Day/night: BmAK has no day/night member; confirm lamps switch with JC3 night | TRANSLATE | partial | Gate-T | pilot L6 | S | `RPT\weather-and-night-plan.md` s0 |
| NEW-LGT-9 | Battle-mode spotlight/battle headlights switch with the mode pair (fleet has no battle-light behaviour) | BUILD | blocked | B-12/9130, NEW-LGT-3 | - | M | GB T-15 line 1864, T-LG5 |
| NEW-LGT-10 | Underglow: BmAK has none; low accent = emissive wheel material (texture lane) | BUILD | queued (in 9142) | 9140 | - | S | `RPT\underglow-and-accent-lights-plan.md` |
| NEW-LGT-11 | Light budget: lamp meshes vs model budget (4,791.3/4,915 KB) and lights per vehicle | VERIFY | todo | 9142 | 9190 | S | GB B-15 line 1961, `Builds\bm-RC4\verify\files.md` |
| NEW-LGT-12 | VERIFY offline RC5 lights vs BmAK (successor to `v_lights_rc2.py`), 17/17 flares named, module read-back | VERIFY | todo | 9142 | 9193 | S | GB V-RC2-lights line 2004, `Q\9142` Done line |
| NEW-LGT-13 | PILOT cards: night look L6 (expected 18 entries, 12 HeadLight + 6 TailLight, flares=0/17 until built), lamp close C5, wheel C2 | PILOT | done (cards written) | - | TEST | S | `RPT\pilot-card-looks-and-audio.md`, `Working\Q\PREDICTIONS_LOOKS.md` |
| NEW-LGT-14 | TEST night take Q-1 #7 and Q-3 lamp/engine FX: lit-lamp count, flare per socket, beam reach | TEST | blocked | `APPROVED_Q.txt` | RELEASE | M | `Working\Q\APPROVAL_REQUEST.md` |

### 1D. EFFECTS

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| G1-16 | BmAK particles by feature: 206 systems, 17 groups, 1,433 emitters | GRAB | done | - | T-17 | S | GB line 1823, `RB\PARTICLES_FEATURES.md` |
| G2-22 / G2-23 | JC3 effect usage vocabulary (12 usages, flame candidate `EngineNitro`); nitro FX + audio carriers | GRAB | done | - | B-08 | S | GB lines 1844-1845, `RJ\USAGES.md` |
| T-FX3B | Proof that a JC3 exhaust/boost flame carrier exists (`SAttachedEffect`, 5,342 objects) | GRAB | done | - | B-08 | S | `WT\T_FX3B.md` |
| T-17 | Effects translation: 17 rows, all with a chosen carrier | TRANSLATE | done | - | B-08, B-17 | M | GB line 1866, `WT\T13_FX.md` |
| T-FX3 / T-FX7 | Afterburner flame = donor `car_cycle_base_dual_nitrous.effc` under `EngineNitro`, placed at `Afterburner` socket (B-08) | BUILD | done (file-level) | - | NEW-FX-5 | S | GB line 1955, `Working\Effects\bm_fx_edits.json`, `Builds\bm-008\receipt.json` |
| T-FX8 | Always-on exhaust (EngineRunning) | TRANSLATE | queued (`epe`) | - | - | S | `WT\T_ROWS.jsonl` |
| T-FX9 | Heat haze: closest `car_speedrom_heater.effc` (12 vehicles, 24 `z80_exhaust_heat` attachments); per-emitter blend/texture bindings UNKNOWN | TRANSLATE | queued (`next`) | NEW-FX-1 | NEW-FX-5 | M | `RPT\fx9-heat-haze-source.md`, `RPT\exhaust-and-heat-plan.md` |
| T-FX10/11 | Cannon muzzle `tank_canon_muzzleflash`; Vulcan `helicopter_minigun_muzzleflash` | TRANSLATE | queued | weapon clones 9101-9110 | - | S | `WT\T_ROWS.jsonl` |
| T-FX12/16 | Tracers (tune half + art half) and round trail | TRANSLATE | queued | NEW-FX-1, 9102 | NEW-FX-8 | M | `RPT\fx12-16-tracer-and-trail.md`, `RPT\tracer-width-and-ribbon-units.md` |
| T-FX13 | Shell casings `SAttachedEffect ShellEjection` | TRANSLATE | queued | weapon entity | NEW-FX-8 | S | `RPT\fx13-shell-casings.md` |
| T-FX14 | Missile trail `missile_trail_car` at MissileL/R | TRANSLATE | queued | 9104 | 9102 | S | `WT\T_ROWS.jsonl` |
| T-FX15 | Cannon impact 7-variant `tank_explosive_*` | TRANSLATE | queued | 9110 | - | S | `WT\T_ROWS.jsonl` |
| T-FX17/18/19 | Tyre kick-up (`dust_trail_*`), slide dust (`chassis_slide_*`), wall-scrape sparks (donor `ScrapeSparks`; BmAK ships 0 wall-scrape systems) | TRANSLATE | queued (`epe`, donor-carried) | - | NEW-FX-12 | S | `WT\T_ROWS.jsonl` |
| T-FX20 | Brake-light trail: private restyled copy of `car_cycle_base_dual_nitrous.effc` | TRANSLATE | queued | NEW-FX-1 | - | M | `RPT\fx20-brake-trail.md`, `WT\T13_FX.md` s5 |
| T-FX21 | Death explosion `exp_car_01` under `OnExploded` + blast tune | TRANSLATE | queued (`epe`) | - | NEW-FX-9 | S | `WT\T_ROWS.jsonl` |
| T-FX22/23 | Burn states (`dmg_fire_*`) and engine smoke (`EngineSmoking`): CONFLICT with operator fact "no visible damage stages" | TRANSLATE | partial (conflict) | operator Q (c)10, NEW-FX-9 | 9171 | S | GF, `RPT\health-to-explosion-no-crash-damage-plan.md` lines 86, 234-242 |
| T-FX1/FX2/FX5/EF1 | Window-break/fire (keep), fx container (keep), tyre effects fleet-invariant (keep) | TRANSLATE | done (keep) | - | - | S | `WT\T_ROWS.jsonl`, `RPT\keep-audit-audio-fx.md` |
| T-FX4 | EMP effect: superseded to T-11 (CForcePulse) | TRANSLATE | done (superseded) | - | NEW-FX-2 | S | `WT\T_ROWS.jsonl` |
| B-08 | Effect attachments: 48 objects / 32 hashes resolve; flame placement | BUILD | done | - | B-17 | S | GB line 1955, `Tools\scripts\bm_fx.py --check` |
| B-17 / 9102 | Effect writer (private `.effc` copies): NO payload in RC4; writer proof 95/95 byte-identical; growth unproven | BUILD | todo / queued | 9101 | all new FX | L | GB lines 1436, 1963, `RPT\effc-format-writable.md`, `Tools\scripts\effc_writer.py`, `Q\9102-rc5-effect-writer-payloads.txt` |
| NEW-FX-1 | Prove `.effc` writer can GROW (A[] pair layout, total_size) and that a new private `.effc` is reachable from `.ee` | GRAB | todo | - | B-17, 9174, T-24 | M | `WT\T13_FX.md` s6 last bullet, `Q\9174` |
| NEW-FX-2 | EMP burst + EMP missile visuals + disabled-vehicle lightning (15 systems / 141 emitters); CForcePulse effects; no material writer (U-6) | BUILD | todo | 9104/9107, NEW-FX-1 | - | L | `RPT\emp-visual-and-hit-plan.md`, `RPT\emp-effects-closest-system-plan.md` |
| NEW-FX-3 | Sonar pulse ring (7 emitters, axial 25 m/s, 1-3 s): no JC3 ring effect named; new effect needed; outside missions only visual+audio | BUILD | todo | NEW-FX-1, 9109 | - | M | `RPT\sonar-pulse-visual-plan.md`, `RPT\sonar-marker-reveal.md`, GF, GB B-20 line 1496 |
| NEW-FX-4 | Booster plume/mesh: `MESH_Batmobile_Jet_V01` 114,160 B + `Firefly_JetMesh`; carriers `car_cycle_base_nitrous.effc` (8 emitters) / `jet_exhaust_base.effc` (11) | BUILD | queued (9102/9106) | NEW-FX-1 | - | M | `RPT\booster-mesh-and-flame-plan.md`, `Q\9106` |
| NEW-FX-5 | Afterburner confirmation: heat haze, flame audio binding (`EngineNitro` sound GUID), trigger = boost input is a Q probe | VERIFY | todo | T-FX9 | NEW-FX-16 | S | `RPT\afterburner-effects-audio-plan.md`, `WT\T13_FX.md` s6 |
| NEW-FX-6 | First 9102 payloads: MissileL/R trail + launch flash, booster plume | BUILD | queued | 9101 | 9174 | M | `Q\9102` |
| NEW-FX-7 | Remaining families in 9174: skids/tracks, weather/night, collision impacts, exhaust+heat, glass, tracer/casing/trail | BUILD | queued | 9102 | 9190 | L | `Q\9174-rc5-surface-weather-impact-fx.txt` |
| NEW-FX-8 | Full coverage of tracer (16 systems/112 emitters), casings (8/40), trails (18/53) beyond one-per-kind | BUILD | todo | NEW-FX-1 | - | M | `WT\T13_FX.md` s1 |
| NEW-FX-9 | Death explosion "violent", kills passengers, no wreck, no crash damage; `explosion_threshold` semantics UNKNOWN | BUILD | queued (9171) | threshold semantics | - | M | `RPT\health-to-explosion-no-crash-damage-plan.md`, `Q\9171` |
| NEW-FX-10 | Collision impact effects consistent with "no crash damage" | BUILD | queued | NEW-FX-9 | - | S | `RPT\collision-impact-effects-plan.md` |
| NEW-FX-11 | Hack FX (12 systems): SAM/drone chain visuals | BUILD | todo | B-19/9108 | - | M | `RPT\hacker-gadget-visual-plan.md` |
| NEW-FX-12 | Tyre-surface (16 systems/90 emitters) BmAK fidelity vs donor dust/slide; skid marks/tracks | VERIFY | todo | T-FX17/18 | - | M | `RPT\surface-skids-and-tracks-plan.md` |
| NEW-FX-13 | Flip/stuck thruster FX and side-booster (LStick+A) FX | BUILD | todo | 9124 | - | S | `RPT\stuck-flip-build-plan-merge.md`, QUEUE_MAP 7998 note, GF |
| NEW-FX-14 | Winch/grapple FX (6), gel rounds (8), fear gas (12), target-marker FX (20): T13 labels some "named omission"; reconcile with OP "All BmAK weapons are required" | BUILD | todo | weapon lanes | - | M | `WT\T13_FX.md` s1, OP |
| NEW-FX-15 | VERIFY offline: every built effect read back; fx budget unchanged (`bm_fx.py`, `effc_writer.py check`, `t17_fx.py`) | VERIFY | todo | 9102, 9174 | 9193 | S | `Q\9102`, `Q\9174` Done lines |
| NEW-FX-16 | PILOT/TEST effects: flame on boost, muzzle, trail, tyre smoke, explosion take | PILOT/TEST | blocked | `APPROVED_Q.txt` | RELEASE | M | `Working\Q\PREDICTIONS_COMBAT.md`, `APPROVAL_REQUEST.md` Q-3 |

### 1E. Cross-cutting chain

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| 9030-9033 | Serial ledger apply wave (all edit `T_ROWS.jsonl`) + review rewriting 91xx briefs | TRANSLATE | queued | R wave | all B | M | `tmp\freebuff\QUEUE_MAP.md` RC5 table |
| 9100 / 9101 | Scaffold + merge script; entity roots and slots | BUILD | queued | 9033 | 9102, 9142, 9160, 9174 | M | `Q\9100`, `Q\9101` |
| 9190-9194 | Merge RC5; verify files/wiring/audio; geometry/predictions/install; gate VX + approval request; pilot refresh | BUILD/VERIFY | queued | all branches | TEST | M | QUEUE_MAP RC5 table |
| Q-0..Q-5 | Prove pilot cards on a simple car; Q-1 static+lights, Q-2 driving+camera, Q-3 world+FX; Q-4 fix-loop triage; Q-5 recording | PILOT/TEST | blocked | `APPROVED_Q.txt`, V-07 | RELEASE | L | `Q\8600-8605`, `Working\Q\APPROVAL_REQUEST.md` |
| NEW-REL-1 | RELEASE: installer v3, rollback proven, Verify, user README for HUD/lamp/FX, changelog | RELEASE | partial | Q results | - | M | `Working\Installer\install_v3.ps1`, GB V-06-fix line 2007 |

---

## (a) DONE, with evidence

- BmAK HUD decoded (25 modules, 19 movies byte-identical, 252 setters; speedometer proven native/debug-only): `RB\HUD.md`, `HUD_INVENTORY.json`, `SPEEDOMETER.md`, `bmak_speedometer.py --check`.
- Dash cluster placement 6/6 vs AS3: `WT\HUD_CLUSTER_ELEMENTS.md`. Radar numbers recheck (5 same, 3 no source): `WT\HUD_RADAR_RECHECK.md`.
- G2-25, T-10, T-19 (T-HUD5 completed to 10 rows): GB tracker lines 1847, 1859, 1868.
- Camera: composition decoded (700 cm back, 130 cm up), FOV 85->54.5 / 95->63.1, 8 values built as `bat_base.ctunec` (test-091, carried in RC4): `STATUS.md`, `T6` s4, `Builds\bm-RC4\receipt.json`.
- Lights: G1-17 (129/129 colours), G2-33, T-18 (28 rows), B-03, B-07, V-RC2-lights (colour 17/18): GB lines 1824, 1855, 1867, 1946, 1956, 2004.
- Effects: G1-16, G2-22/23, T-17 (17 rows all with carrier), B-08 (flame placement, 32/32 hashes resolve): GB lines 1823, 1844-1845, 1866, 1955.
- Offline gates exist and pass for each lane (`bmak_camfile.py check` 8/8, `bm_fx.py --check`, `t17_fx.py --check`, `t19_hud.py --check`, `t18_lights.py`).
- Nothing is behaviour-verified in game (`STATUS.md`: 0 rows fully verified).

## (b) BLOCKERS, root-first

1. **Scaleform / `hud.gfx` editing capability: NOT evidenced.** Evidenced: ffdec EXPORTS (decompiles) the 19 BmAK movies and JC3 `ui/hud.gfx` (260 AS3 scripts) - `RB\HUD.md` s7; BmAK movies can be carved from UPKs. NOT evidenced anywhere in the repo:
   - No tool in `Tools\scripts\` writes or recompiles a SWF/GFx; all HUD scripts are read/analyse (`bmak_hud*`, `hud_spec`, `jc3hudwpn`, `hud_cluster_elements`, `hud_radar_recheck`, `t19_hud`, `qa1_hud`). `RB\HUD.md` line 313: "`ui/hud.gfx` was read, not replaced; the Batmobile movies were never mounted"; line 336: "needs a script hook or a `ui/hud.gfx` patch, neither attempted".
   - Whether ffdec AS3 recompile/import can be driven for writing = UNKNOWN (never run).
   - U6 AVM2 GFx v0f -> JC3 loader compatibility = UNKNOWN (the 5-min `ffdec -dumpSWF` tag compare is unrun: `RPT\hud-cluster-closest-system-plan.md` U6).
   - U5 "does a private `ui/hud.gfx` copy load at all" = UNKNOWN; R7 says never replace the shared one; no per-entity HUD-movie member found (`RJ\NAMES.md` line 149: "hud.gfx has no reference").
   - No B-xx card owns the `hud.gfx` write (`WT\BUILD_BATCHES.md` line 234 asks for a "B-15" step; B-15 was later used for the budget card, GB line 1961). 9160 is the first owner (`Q\9160`).
   - U5 cannot be settled while the test ban stands.
   Dependents of NEW-HUD-4: health top-left, afterburner-left, cooldown gauge, speedo suppression, 4-slot HUD, lock-diamond art, radar icons, release.
2. **Entity -> hud caller bridge: UNKNOWN / native.** 0 movie call sites for `InitVehicleNitrous`/`UpdateVehicleNitrous`/`UpdateVehicleWeapons`/`UpdateWeaponReticle`; no vehicle `CreatePoi` (`RPT\hud-radar-dash-plans-v2.md` s5; `STATUS.md`). Modified AS3 can react only to native pushes; whether stock native code pushes them for a custom entity (U2, U4) is settled only by a live slot read. A script-hook route has no evidence (UNKNOWN). There may be a free bridge if the donor nitro/weapon components drive the pushes - unproven.
3. **Test ban / `APPROVED_Q.txt` absent by design** (`Working\Q\APPROVAL_REQUEST.md`): every camera, light-unit, flare, flame and HUD probe is Gate-T.
4. **Light-unit domain + render path** (NEW-LGT-1/2): units undocumented; RC4 values out of domain; which list renders UNKNOWN. Blocks beam values, T-LG6, B-25.
5. **No lamp->effect member** (T-24): flare sprite must ride `SAttachedEffect`; needs NEW-FX-1.
6. **`.effc` growth unproven + no material writer** (NEW-FX-1, U-6): blocks sonar ring, EMP lightning, brake trail, booster restyle.
7. **ADF append writer missing**: blocks camera shake (T-CAM11).
8. **Mode pair unmerged (B-12/9130)**: blocks battle camera, battle lamps, mode-dependent HUD swap.
9. **No unit bridge for camera springs (T-CAM9); no member for head impulse/drift (T-CAM8)**: felt test only.
10. Weapon branches 9103-9110 (tracker, EMP missile, lock/reticle, booster, EMP burst, hacker, sonar) must land before HUD lock/tracker POIs and weapon FX (`Q\9160` AFTER gates).

## (c) OPEN QUESTIONS FOR THE OPERATOR (player-only)

1. Health bar: battle mode only, or in pursuit too? Any armour/second bar, or one bar only? (OP: top-left in battle.)
2. The "second cooldown gauge" left of the afterburner: look (ring/bar), when it fills, what it means? BmAK files have no such element.
3. Afterburner gauge: pursuit only? hidden in battle? any number/percent label?
4. Radar: colours for cops / military / tanks / helicopters / tracked / hacked-before / hacked-after? tank vs car arrow size ratio? does the helicopter blade spin continuously? Does the radar ping/pulse, and how often? Radar range in metres?
5. Lock markers: exact look/size/colour of pursuit circle+gapped diamond and battle orange diamond; do they clamp to screen edge; any lock beep or text?
6. Vulcan crosshair: shape, spread range, how quickly it blooms and recovers (capture `C:\Users\User\Videos\Captures\Batman Arkham Knight VulcanFire_10s-15s.mp4` is the only oracle).
7. Lights: does the Batmobile have player-toggled HIGH BEAMS? Lights on in daytime? Do brake lights visibly brighten when braking? Reverse light? Lens flares in daylight? Does battle spotlight light the whole front or one wide beam?
8. Camera: feel at boost (pull-back, FOV pop, shake strength); shake on landing/impacts; battle camera transition time/smoothness; is there a bonnet/cockpit camera the player uses? Your monitor aspect ratio (FOV conversion assumes 16:9)?
9. Burn/smoke: confirm no smoke/fire stages before the explosion (conflicts with donor T-FX22/23); is there a warning flash/delay before the blast?
10. Afterburner flame colour/length; does heat haze visibly distort the road; tyre smoke on drift; skid marks on road?
11. EMP: what do disabled vehicles look like? Sonar pulse ring colour and duration?
12. Confirm no speed readout appears anywhere (incl. cockpit dash) - OP says none.

## (d) RISKS

- The whole HUD plan rests on an untested assumption that a modified `hud.gfx` loads in JC3. If U5/U6 fail, every position target (health top-left, gauges left, speedo hidden) is dead and only JC3 anchors remain (`RPT\hud-radar-dash-plans-v2.md` s4: "one experiment kills the route").
- A global `hud.gfx` replacement changes HUD for every vehicle, on-foot and other mods; the AS3 type guard depends on `m_CurrentType = 4` being delivered natively (U4 UNKNOWN).
- Radar fidelity: 8-way arrows vs BmAK continuous bearing; no class/colour member; helicopter rotor needs animation a POI cannot do; lore-accuracy rule then needs authored clips (L-size art) or an operator-approved compromise.
- Lights: RC4 values measured out-of-domain; T-L17 wrong colour; flares 0/17; one stock-vs-mod take decides whether range/angle/multiplier change anything (B-25 stop condition: "display-only").
- Camera spring feel cannot be derived (T-CAM9); one `CCameraRef` per entity makes battle/boost cameras need a second entity/variant or an unknown switch.
- Donor burn/smoke effects (T-FX22/23) may contradict the player-confirmed "no damage stages".
- `.effc` writer proven only for in-place patches; growth may lose emitters (9174 requires a lost-emitter list).
- Model budget 4,791.3/4,915 KB leaves ~124 KB for new lamp/FX geometry (GB B-15).
- Queue hygiene: briefs with templated text are stripped by the similarity guard (QUEUE_MAP 2026-11-06/08 notes); ~40+ more briefs needed.
- Stale/contradictory ledger text (T-HUD1 "reuse" vs operator "disable"; T-CAM2 "95 is a gap"; cameras-per-mode boost 67.7 vs 72.49): wrong values could be built if the apply wave 9030-9033 misses them.
- 0 rows behaviour-verified: surprises will cluster in the first in-game session.

## (e) REMAINING EFFORT (estimates, not measurements)

Counting this landmark: ~165 rows above, ~60 done/closed, ~105 open. Assumptions: ~100 small-model briefs/day (QUEUE_MAP: 7-15 min each, serial `AFTER:` chains, similarity guard); each open row = 1-3 briefs (avg ~1.7) with x1.5 for retries/reviews.

| bucket | open rows | agent sessions (briefs) | note |
|---|---:|---:|---|
| GRAB/TRANSLATE leftovers + ledger apply 9030-9033 | ~28 | ~55 | desk only, ~1 day |
| HUD tooling gate (NEW-HUD-4: GFx write path, AVM compat, archive path) | 1 (+3 sub) | ~25-40 | may need a new Python/ffdec writer; success UNKNOWN |
| BUILD HUD (6,7,9-21,25,26) | ~18 | ~70-90 | radar art and POI driver are the cost |
| BUILD lights (9142, LGT-4/6/7/9/10) | ~9 | ~25 | |
| BUILD effects (B-17/9102, 9174, FX-1..14) | ~16 | ~60 | |
| BUILD camera (CAM-4/5/8/14) | ~5 | ~20 | shake writer is L |
| VERIFY offline + PILOT cards | ~12 | ~30 | |
| **Total** | | **~290-340** | |

At 100 briefs/day throughput this is ~3-4 days of raw volume, but the chain is serial (9100 -> 9101 -> branches -> 9190 merge -> verify) so desk+build calendar is ~7-10 days.

In-game (human operator): the approval plan is 3 sessions of ~45 + 40 + 45 min (`APPROVAL_REQUEST.md`, derived estimates). For this landmark expect ~8-12 operator sessions overall: HUD gate probe (1), first Q-1/Q-2/Q-3 (3), fix loops (4-8) because each defect (hud.gfx not loading, light units wrong, flares missing) forces a build -> install -> play -> report cycle. Operator time ~10-20 h over ~2-4 weeks calendar; release packaging +1-2 days.

Overall: landmark finished roughly 3-5 weeks calendar if the hud.gfx gate (NEW-HUD-4) passes on first probe. If it fails, HUD scope collapses to JC3 anchors plus a documented compromise (needs operator approval), and radar icon set, battle-mode HUD layout and four-slot HUD cannot ship.
