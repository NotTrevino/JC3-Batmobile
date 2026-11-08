# BACKLOG — the complete Arkham Knight Batmobile in Just Cause 3

**This is the single backlog for the project (written 2026-10-24).** It replaces the old
`GRAB_BACKLOG.md` text (saved as `Backups/backlog-20261024/GRAB_BACKLOG.pre-unified.md`) and
absorbs the open work from `MODDING_PLAN.md` §3–§6 and `Working/Translation/T_PLAN.md` §4–§10.
Those two files stay as **history and evidence**; when they disagree with this file about *what to
do next*, this file wins. When they disagree about *a measured fact*, the evidence file wins and
this file must be corrected.

**Phase order is fixed by the user (2026-10-24):** finish **G1** (BmAK grab) → finish **G2**
(JC3 grab) → finish **T** (translation) → **B** (build offline) → **V** (verify offline) →
**Q** (in-game testing, last, batched) → **R** (release). In-game testing is the most expensive
step, so nothing launches the game until phase V has exited.

---

> **2026-11-02 RESEARCH RESET (user): no builds. See `RESET_FINDINGS.md` for what was never grabbed, never translated, or translated wrongly, and the research list R-1..R-6.**

> **Operator weapon ranking, HUD leads and open-row leads are in `OPERATOR_PRIORITIES.md`.**
> **Stages and the closest-system rule are defined in `STAGES.md` (operator 2026-11-06). "JC3 has no system" is never an answer: name the closest system and the gap; build closes it.**

## 0. How to use this file (read this first, every session)

### 0.1 Who this is written for

Any agent, including small models. Every task card says exactly which files to read, what to
produce, and the command that proves it is done. **If a card does not tell you a number, you do
not have that number.** Do not fill it from memory, from the internet, or from "what JC3 usually
does". Write `UNKNOWN`, stop, and record why in `MODLOG.md`.

### 0.2 The session loop (do these in order, every time)

1. Read the **tail** of `MODLOG.md` (last ~150 lines). Other agents work here too.
2. Read §12 (the tracker) of this file. Pick the **first** task whose status is `todo` and whose
   `deps` are all `done`. Do not skip ahead to a more interesting task.
3. Read the task card fully, then every file in its **In** list.
4. Before changing any file, write in `MODLOG.md`: the intended change, the file, why it is the
   right file, and how to revert it (rule from `AGENTS.md`).
5. Do the **Do** steps. Write scripts, not hand edits: every value must be re-derivable by a
   command (`--check` mode re-derives and compares).
6. Run the **Done when** check. Paste its output summary into `MODLOG.md`.
7. Flip the task's status in §12 to `done` (or `blocked: <reason>`), add the evidence path.
8. Run `python Tools/scripts/status_audit.py --check` if the task touched translation rows.

### 0.3 Status words (use only these)

`todo` · `doing` · `done` · `blocked: <reason>` · `skipped: <decision id>` (only when a
decision in §11 removed the task). A task is `done` only when its **Done when** check passed and
its output is on disk. "Looks right" is never done.

### 0.4 Card format

```
#### <ID> · <title>   size S/M/L/XL · deps: <ids> · serves: <feature codes from §1>
In:    files/tools to read
Do:    numbered steps
Out:   files produced (exact paths)
Done:  the check that must pass (a command, a count, a comparison)
Stop:  conditions where you must stop and ask or record UNKNOWN instead of continuing
```

Sizes: **S** ≤ 1 session · **M** 1–3 sessions · **L** 1–2 weeks · **XL** multi-week.

### 0.5 Non-negotiable rules (break one = the task is failed, revert it)

| # | rule | source |
|---|---|---|
| R1 | **Lore over the donor car.** True scale, no deformation, BmAK behaviour first. Do not conform to non-essential JC3 mechanics. | user, memory `jc3-batmobile-design-rules` |
| R2 | **One transform for every asset.** Body, wheels, every new part, every socket, every light, every interaction point goes through `T(p) = to_jc3(p) × 0.01 + offset` from `Tools/scripts/bat_assemble.py`. Import it; never re-implement it; never fit a part separately. | user, `bat_assemble.py` docstring |
| R3 | **Physics follows the asset.** If geometry moves, stations/radius/clearance move with it. Never move visuals relative to physics stations (that caused the 047 jitter). | user |
| R4 | **No value without provenance.** Every built value carries a class: `decoded`, `decoded (fleet)`, `derived`, `class`, `epe`, `read`. `assumed` is not buildable. A row with no semantic bridge is `blocked`, never `class`. | `T_PLAN.md` §0, `POSTMORTEM_DAMAGE.md` |
| R5 | **Behaviour before member.** A requirement is carried by a *behaviour* row with a take that can fail, not by the JC3 member whose name sounds closest (test-087 translated ram *attack* as *defence*). | `POSTMORTEM_DAMAGE.md` §8 |
| R6 | **No game launch before phase V exits.** No install into `D:\Games\Just Cause 3\dropzone` before phase Q, and only with the user's explicit approval. Builds are staged in `Builds/` only. | user 2026-10-24, plan §1.1.4 |
| R7 | **Never edit shared game modules in place** (`vehicle_common`, `lave_health_medium`, `vehicle_deform`, shared weapon files). Make a private copy with a new path and repoint the hash. | plan §1.2 |
| R8 | **Never internalise a module the archives carry** unless the card says so; `vehicle_parts`/`vehicle_deform` edits need `eetoc --internal` or the game keeps the archive copy. | MODLOG §71, §103c |
| R9 | **Budgets are hard walls**: vehicle Model 4,915 KB, Texture 7,065 KB. Over budget = the whole entity vanishes. Every build reports both. | MODLOG §76, §111 |
| R10 | **Game files stay outside the repo.** Extracted/decoded game data goes to `E:\Modding\JustCause3\_grab\` or `E:\Modding\ArkhamKnight\_grab\`. Never commit or publish game files, extracted assets or decompiled code. | universal-modder `AGENTS.md` |
| R11 | **Counts are generated, never typed.** `STATUS.md` is regenerated by `status_audit.py`; tables of counts in new docs come from a script with `--check`. | `STATUS.md` |
| R12 | **Kill processes by exact PID** (`um win kill`), never by name. Back up saves (`um backup`) before any modded launch. Ask before driving the user's mouse/keyboard. | universal-modder `AGENTS.md` |
| R13 | **One variable per in-game probe** unless the card explicitly batches independent checks that cannot interact (phase Q does this on purpose to save launches). | plan §1.1.3 |
| R14 | **Journal everything** in `MODLOG.md` (append-only), with file paths and command output. | plan §1.1.5 |

### 0.6 Where things live

| what | path |
|---|---|
| project root | `E:\Modding\JustCause3\JC3-Batmobile\` |
| game install / dropzone | `D:\Games\Just Cause 3\` · `D:\Games\Just Cause 3\dropzone\` |
| BmAK grab (repo evidence) | `Research/BatmobileGrab/` (`grab.json`, `objects.jsonl`, `CHAIN.json`, `OFFSETS.json`, `MECHANICS.md`, `LIGHTS.json`, `AUDIO_MAP.json`, `PARTICLES.json`, `MESHES.md`, `SLOTS.json`, `CAMERA.md`, `HUD_*.json`) |
| BmAK raw exports (outside repo) | `E:\Modding\ArkhamKnight\_grab\meshes\`, `E:\Modding\ArkhamKnight\_grab\gltf\`, `E:\Modding\_BmAK_grab\` |
| BmAK packages | `E:\Modding\JustCause3\JC3-Batmobile\Playable_Batmobile_SF\`, `BmGame\`, `Startup\` (+ the 15 `Playable_Batmobile*` packages listed in `Research/BatmobileGrab/README.md`) |
| JC3 grab (repo evidence) | `Research/JC3Grab/` (`INDEX.jsonl`, `ENTITIES.md`, `VOCABULARY.md`, `PARTS_TABLE.jsonl`, `WIRING.jsonl`, `FX_TABLE.jsonl`, `GEOMETRY.md`, `SHAPES.md`, `DAMAGE_MECHANISMS.md`, `FLEET.md`) |
| JC3 decoded data (outside repo) | `E:\Modding\JustCause3\_grab\` (`entities/*.ee.json` = modules as rows, `detail/*.ee.json` = `.epe` graph + meshes + physics, `geom/`, `hkx/`, `phys/`) |
| translation ledger | `Working/Translation/T_ROWS.jsonl` (+ `T6_HUD_CAMERA.md`), docs `T1_…`, `T2_…`, `T3_…`, `T5_BUILD.md`, `QA1_RESULTS.md` |
| builds | `Builds/test-0xx/` (live: **test-091**, verify `install.ps1 -Action Status`) |
| tools | `Tools/scripts/` (Python), `Tools/Gibbed/` (pack/unpack/ConvertAdf/ConvertProperty), `Tools/Gibbed-patched/`, `Tools/Deca/`, `E:\Modding\_shared\tools\ffdec\` |
| the one transform | `Tools/scripts/bat_assemble.py` → `Working/TrueScale/stations.json` |
| universal-modder CLI | `um` (`um win`, `um backup`, `um video`, `um publish check`, `um kb`) |

### 0.7 Standing gates (re-run at the start of phase work and after any build)

```
python Tools/scripts/grab_model.py check            # G1 inventory, schema 6
python Tools/scripts/bmak_chain.py --check           # 336 cross-checked names, 0 conflicts
python Tools/scripts/bmak_coverage.py --check        # every BmAK field has a row
python Tools/scripts/jc3index.py check               # 81,952 / 81,953 named
python Tools/scripts/jc3hkx.py check --all           # Havok shapes invariants
python Tools/scripts/jc3fx.py check                  # 57,187 effect/camera/trim files
python Tools/scripts/t_rows.py check                 # ledger sums
python Tools/scripts/t3_fleet.py --check             # class numbers behind class rows
python Tools/scripts/status_audit.py --check         # STATUS.md matches the ledger
```

A failing standing gate stops all work until it is fixed or explained in `MODLOG.md`.

---

## 1. The target: what "a complete, lore-accurate Batmobile" means

This is the definition of done for the whole project. Each line is a **feature code** used by the
task cards (`serves:`). The middle column says where the lore value comes from — always the BmAK
files first (`Research/BatmobileGrab/`), the wiki/footage only where a card proves the files have
nothing. The right column names the JC3 carrier, with the evidence that it exists.

### 1.1 Appearance (APP)

| code | requirement | lore source | JC3 carrier (evidence) |
|---|---|---|---|
| APP-1 | Body is `Batmobile_V2` at true scale, all 5 LODs, 19 material slots, no visible tears | `MESHES.md`, `SLOTS.json` | body RBM, 16 `CarPaintMM` + 1 `Window` blocks (live in test-091) |
| APP-2 | Paint reads as the Arkham Knight matte/satin armour in noon and night light | `MATERIALS.md`, `VALUES.json` | `CarPaintMM` params (`factors.py`) |
| APP-3 | Canopy is tinted glass; cockpit interior (seat, yoke, screens) visible through it | `SLOTS.json`, materials | `Window` block (BC3), interior blocks |
| APP-4 | Emissive parts glow (head-lamp lenses, tail strip, wheel-arch lights, dashboard) | `LIGHTS.json`, emissive params | `CarLight` RBM block (`GEOMETRY.md`), parts `has_lights` |
| APP-5 | Movable parts are separate meshes: turret, cannon, Vulcan barrels, rear fins/air-brakes, missile hatches, turbine fan, canopy, steering yoke | BmAK bones + anims (G1-10…G1-12) | `VehicleParts` behaviours (§2.3) |
| APP-6 | Battle-mode silhouette (turret raised, stance) is reachable, either as a pose of the same car or a second variant | `Batmobile_V2_Pose_States`, transform anims | parts angles / second entity (decision D-2) |
| APP-7 | The car never deforms; damage shows as scorch/smoke only | user rule R1; BmAK has no deform | `deform_scale` 0 (switch, `damage_audit.py`) |
| APP-8 | Optional: MK2 / Jokerfied skins | `Batmobile_MK2_Skin`, `Batmobile_Jokerfied_Skin` meshes | extra drop entries or palette (D-5) |

### 1.2 Dimensions and mass (DIM)

| code | requirement | lore source | JC3 carrier |
|---|---|---|---|
| DIM-1 | 7.026 × 3.495 × 2.271 m body, wheelbase 5.029 m, track 2.416 / 2.569 m | PSKX at real cm (`bat_assemble.py`) | body RBM, `land_global.base_wheel_hardpoint_positions` (T-G1, live) |
| DIM-2 | Tyre diameter matches the lore reference | PSKX **1.365–1.366 m** measured on all four tyres (`TYRES.md`, T-G2) vs wiki 1.40 → 2.4% apart, **accepted**; the docstring's 1.42 has no source and what it measured is UNKNOWN (`TYRES.md` §3) (D-1 resolved: keep the PSKX) | `land_global.*_wheels.radius`, wheel RBMs |
| DIM-3 | Mass is heavy-armoured (BmAK has no absolute mass; the 6 t class row stands until a lore source exists) | T-M1 ledger | `rigid_body.mass` |
| DIM-4 | Collision hull matches the Batmobile body, not the Serpente | `PHYSICS.md` (BmAK has no chassis body) | `.physicsc` hulls (needs the writer, G2-30) |

### 1.3 Armour and damage (ARM)

| code | requirement | lore source | JC3 carrier |
|---|---|---|---|
| ARM-1 | Small arms (pistol, rifle, MG) do not move the health bar | BmAK play behaviour (T-DM9) | entity root `CCar.invulnerable` / root `health` scale (`DAMAGE_MECHANISMS.md` §1) |
| ARM-2 | Heavy weapons (tank cannon, missiles, RPG) do damage; the car can be destroyed | `RVehicleBatmobile.Health` 1,200, damage rules (G1-14) | `VehicleDamage` channels, private health module (DMG-2) |
| ARM-3 | Ramming anything never damages the Batmobile | T-DM8 | `impact_damage_factor` 0 (switch) |
| ARM-4 | Wheels cannot be shot off or burst | BmAK (no wheel damage) | `Land_Wheel` damage type, `front/rear_wheels_damage.*` |
| ARM-5 | Armour regeneration out of combat, **if** BmAK has a regen value (G1-14 decides) | G1-14 | JC3 member if one exists (G2-28) else named omission |
| ARM-6 | Death = BmAK death explosion look/sound, not a crumpled Serpente | `DeathExplosionSoundArray`, particles | death effects in the `.epe` |

### 1.4 Weapons and gadgets (WPN)

BmAK carries 11 weapon/gadget classes (`MECHANICS.md` "Weapons and projectiles"). JC3 carries
**25 vehicle weapons** (`w601`…`w622`), and several are fired by the **driver of a car**
(evidence §2.1). Every BmAK weapon therefore gets a row; none is "out" until G2 proves no carrier.

| code | BmAK object (class) | lore behaviour (values from G1-08/G1-09) | JC3 candidate carrier (evidence §2.1) |
|---|---|---|---|
| WPN-1 | `Batmobile_Heavy_Cannon_Primary` (`RBatmobileHeavyCannon`) — 60 mm cannon | charged shot, projectile, big impulse | `w602_mediumtank_canon` / `w605_smalltank_canon` on a `Turret`+`Cannon` part (tank wiring) |
| WPN-2 | `Batmobile_Cannon_V2` (`RBatmobileCannon`) — Vulcan chain gun, heat bar, inaccuracy curves | sustained fire, overheats | `w603_mediumtank_mgun` / `w619_buggy_mgun` (+ `GatlingGun` barrel spin, `CBarrelSpinWeaponComponent`) |
| WPN-3 | `Batmobile_Missile_Launcher` (`RBatmobileMissileLauncher`) — missile barrage with target lock | multi-target lock-on salvo | `w618_sportsmuscle_missile` (same chassis!) / `w609`, `w612`, `w613` lock-on missiles, `CAimPOIWeaponComponent` |
| WPN-4 | `Batmobile_EMP_Missile_Launcher` (`RBatmobileEMPMissile`) — Immobilizer (pursuit mode, vs cars) | disables vehicles | EMP: `v0505 oldtruck_rebel_emp` device (G2-16) or a missile with an EMP explosion tune **Scrape lead 2026-11-07 (operator, unverified):** battle-mode EMP permanently disables cars (no explosion/smoke/flame, lightning effect); tank and chopper drones are stunned by it. Brief 7997 settles it. |
| WPN-5 | `Batmobile_EMP_Burst` (`RBatmobileEMP`) — electrical overcharge around the car | radial stun/push | `CForcePulse` (79 chassis / 232 `.ee`, G2-17) / EMP device **Scrape lead 2026-11-07 (operator, unverified):** battle-mode EMP permanently disables cars (no explosion/smoke/flame, lightning effect); tank and chopper drones are stunned by it. Brief 7997 settles it. |
| WPN-6 | `Batmobile_Winch` (`RBatmobileWinch`) — power winch | tow/pull objects | research: JC3 winch carriers (`transport_rope_winch`, tether) — G2-34 |
| WPN-7 | `Drone_Hacker` (`RBatmobileAllegianceSwitcher`) | turns enemy drones | research; likely named omission |
| WPN-8 | `Batmobile_Sonar` (`RBatmobileSonar`) — seismic sonar | scan + shockwave | `CForcePulse` / named omission |
| WPN-9 | `Vehicle_Tracker` (`RBatmobileVehicleTracker`) | tags a car | research; likely named omission |
| WPN-10 | Riot suppressor (non-lethal mode of `RBatmobileCannon`, `RiotSuppressorMuzzle`) | non-lethal vs humans | decision D-3 (lethality) |
| WPN-11 | `Batmobile_Booster` (`RBatmobileBooster`) — afterburner gadget mesh | boost | nitro (`custom_land_global.arcade.nitro_boost*`, T-B rows, live) |
| WPN-12 | HUD: weapon slots, reticle, cannon cooldown, Vulcan heat, missile lock | `HUD_INTERFACES.json` (`UC_SetCannonCoolDown` …) | `hud.gfx` `InitVehicleWeapons`/`UpdateVehicleWeapons` (T-HUD5) |

### 1.5 Handling (HDL) — pursuit mode

| code | requirement | source | carrier |
|---|---|---|---|
| HDL-1 | Top speed 209 mph with afterburner (signed-off wiki row) | T-E5 | `vehicle_misc.official_top_speed`, transmission |
| HDL-2 | Torque curve shape = BmAK `StandardTorqueVSpeedCurve` / `BoostTorqueVSpeedCurve` | `MECHANICS.md`, T-E1…E4, T-B1 | `land_engine`, `transmission`, nitro tiers |
| HDL-3 | Steering, drift, countersteer, braking, suspension from the T rows | T-1 ledger (A, B2, B3, B4 batches live in test-091) | `land_steering`, `custom_land_global.drift`, `brakes`, `suspension` |
| HDL-4 | Afterburner = nitro, extra speed 43.2 km/h derived | T-B2 | `nitro_boost.extra_top_speed` (queued take A2) |
| HDL-5 | Lands from jumps without bouncing, no wheel jitter, 0.70 m stroke | T-S3 | `suspension.*.length` (queued take A6) |
| HDL-6 | Air control / self-righting where JC3 has any member (re-decided in T-10) | T-AC1, T-SR1 (currently `out`) | `gravity_multiplier_*`, `takeoff_pitch_damping` — re-check |

### 1.6 Modes and gadget behaviour (MOD)

| code | requirement | source | carrier |
|---|---|---|---|
| MOD-1 | Pursuit mode: afterburner, Immobilizer, ram immunity, high speed | BmAK (`StandardTorqueVSpeedCurve`, EMP missile) | default drive |
| MOD-2 | Battle mode: turret weapons, turn on the spot, low top speed (`BattleModeVSpeedCurve`), armour reduction (`ArmourModeDamageReduction`), battle camera FOV 60 | `MECHANICS.md`, T-BM1, T-CAM10 | decision D-2 (two drop variants recommended) + tank pivot (G2-21) |
| MOD-3 | Ejection: hold-to-eject launches the driver into the air (Batman glides) | BmAK play | `exit.driver.moving.parachute` (present on 220 entities) → wingsuit/parachute (G2-20) |
| MOD-4 | Canopy opens on entry/exit | `Batmobile_Skel_Ctrl_Door` | door-part behaviour (G2-15) |
| MOD-5 | Nobody but the player drives it: no NPC hijack, no traffic copies | lore | entry/exit set, traffic tables (G2-29, D-6, D-9) |

### 1.7 Sound (AUD)

| code | requirement | source | carrier |
|---|---|---|---|
| AUD-1 | Engine start, idle, rev/load loop driven by RPM | `BML_Engine` / `VEH_Batmobile_MK2_Engine` banks, RTPC `RPM` | FMOD vehicle events (`vehicles.bank`, `.ee.fmod_guids`) |
| AUD-2 | Afterburner/boost roar, burnout | `BML_Burnout` | nitro event (sample swap live since test-060) |
| AUD-3 | Interior/cabin layer | `AUX_InBatmobile` | FMOD event / omission |
| AUD-4 | Battle-mode transform in/out | `Play_BattleMode_In_Rev` / `_Out_Rev` | only if a mode switch exists (D-2) |
| AUD-5 | Each weapon: fire, loop, tail, impact, lock beep | weapon `AkEvent`s (G1-15) | weapon `.ee` audio refs (G2-24) |
| AUD-6 | Tyres, skids, impacts | `BML_Impacts` is **absent** (T-AU3) | keep JC3's (named omission) |
| AUD-7 | No car radio / no horn unless lore has one (G1-15 decides) | BmAK events | JC3 radio/horn members (G2-24) |

### 1.8 Animation (ANI)

| code | requirement | source | carrier |
|---|---|---|---|
| ANI-1 | Wheels spin, front wheels steer, suspension travels | live | `wheel_parts` (T-PA4) |
| ANI-2 | Turret yaws and cannon pitches toward the camera aim | BmAK turret bones | `Turret` + `Cannon` behaviours (tanks) |
| ANI-3 | Vulcan barrels spin while firing | `ChainGunMuzzle`, anims | `GatlingGun` → `weapon_rpm` |
| ANI-4 | Turbine fan spins with engine RPM | rear turbine geometry | `EngineRotatingPart` → `engine_rpm` (proven on a land vehicle: `v0506 oldtractor_fan`) |
| ANI-5 | Rear fins / air-brakes deploy under braking | BmAK anims (G1-10) | `AirBrake` → `air_brakes_T` (only proven on a plane → probe) |
| ANI-6 | Missile hatches open when missiles fire | `MissileL/R` sockets, anims | `MissileHatch` door behaviour (proven on the monorail missile car) |
| ANI-7 | Steering yoke turns with steering | cockpit bone | `SteeringWheel` → `steering_turn` (proven on 9 chassis: 8 cars + 1 sailboat) |
| ANI-8 | Canopy opens on entry | `Batmobile_Skel_Ctrl_Door` | door behaviour (MOD-4) |
| ANI-9 | Rico sits in the Batmobile seat in a believable pose, head under the canopy | `Driver` socket | seat attach + pose set (G2-19) |

### 1.9 World interaction (WLD)

| code | requirement | carrier |
|---|---|---|
| WLD-1 | Spawned from a new Rebel Drop entry called "Batmobile" | `profile/item.onlinec`, `task.onlinec` (RD-1) |
| WLD-2 | Display name "Batmobile" and an icon everywhere JC3 names the vehicle | `.stringlookup`, UI (POL-3) |
| WLD-3 | Entry/exit points sit on the Batmobile's sides, not where the Serpente's doors were | `.epe` `entry.*`/`exit.*` objects (G2-18) |
| WLD-4 | Rico can stand/stunt on the roof; stunt points on the real roof surface | `point.stunt*`, `stunt_areas.vmodc` (G2-18) |
| WLD-5 | Heavy: shoves cars, flattens fences/lamp posts like a 6 t armoured vehicle | mass + collision (DIM-3/4) |
| WLD-6 | Water behaviour decided (lore: not amphibious) | `buoyancy`, `water_interaction` (G2-31, D-8) |
| WLD-7 | Rico's tether, helicopter airlift and the cargo plane behave sensibly with a 6 t car | tether/airlift tunes (G2-34) |
| WLD-8 | No traffic/NPC Batmobiles | traffic spawn tables (G2-29) |

### 1.10 Lights, effects, camera, HUD (LGT / FX / CAM / HUD)

| code | requirement | carrier |
|---|---|---|
| LGT-1 | Headlights (2 cones + flares), high beams, tail/brake, wheel-arch lights, boot light, dashboard light; colours from BmAK light components | `SVehicleLight` in `.epe`, lights module, `CarLight` blocks |
| LGT-2 | Battle-mode spotlight, if battle mode exists (D-2) | extra `SVehicleLight` |
| FX-1 | Afterburner flame + heat haze at the `Afterburner` socket during boost | `effect_attachments` + a `usage` slot (T-FX3) |
| FX-2 | Muzzle flashes, tracers, shell casings, missile trails, cannon impacts | weapon `.ee` effects |
| FX-3 | Tyre smoke/kick-up, wall-scrape sparks, brake-light trails | `tire_effects`, entity effects (T-EF1, T-FX6) |
| FX-4 | Death explosion, burn states without deform | damage effects |
| CAM-1 | Chase camera at the decoded composition (7.00 m back, 1.30 m up, FOV 55…63) | `bat_base.ctunec` (built in test-091) |
| CAM-2 | Battle camera framing (FOV 60) if battle mode exists | second tune per variant |
| HUD-1 | Speed, nitro meter (afterburner), health bar | `hud.gfx` (T-HUD1…3) |
| HUD-2 | Weapon slots, reticle, cooldown/heat, lock-on | T-HUD5, G2-25 |

---

## 2. Corrections this backlog makes (with the evidence, so nobody re-litigates them)

All four were found on 2026-10-24 by scanning the decoded JC3 graphs that already sit in
`E:\Modding\JustCause3\_grab\detail\` and `Research/JC3Grab/PARTS_TABLE.jsonl`. **P0-2 made them proof:**
`Tools/scripts/jc3_feature_census.py --check` re-derives every number below from those inputs and
writes `Research/JC3Grab/FEATURE_CENSUS.{json,md}`. Those scans count **chassis** (the vehicle's
parent folder), so each claim below states chassis, `.ee` files and objects separately. G2-11 and
G2-14 extend the census; they do not repeat an ad-hoc count.

### 2.1 "JC3 gives a car no player-fired weapons" (row T-W1, `out`) is wrong

The fleet carries these weapon components (`detail/*.ee.json`, class names in the `.epe`):
`CBulletWeaponBase` (**17 chassis / 45 `.ee` / 57 objects**, incl. APC, medium tank, Bavarium tank,
technical jeep, armoured jeep, small tank, **buggy**), `CMissileWeaponBase` (**7 chassis / 19 `.ee`
/ 25 objects**, incl. **`v0300` Serpente**),
`CAimPOIWeaponComponent` (**6 chassis / 11 `.ee`**, incl. **`v0300`** and the buggy),
`CBarrelSpinWeaponComponent`,
`CLightWeaponComponent`, `CTurretWeaponComponent`, `CLaserBeamWeaponComponent`,
`CRPGFireLeachWeapon`, and **25 weapon ids** (26 spellings: `w613_bomb` is the same weapon as
`w613_fighterbomber_missile_ground_lockon`; 22 of the 25 also have a `jc_weapons/06_vehicle/<id>/`
archive directory — `FEATURE_CENSUS.md` carries the per-id table):

```
w601_helicopter_missile          w609_fighterjet_missile_air_lockon      w616_corvette_canon
w602_mediumtank_canon            w610_fighterjet_mgun(+_impact)          w617_vintagefighter_mgun(+_impact)
w603_mediumtank_mgun             w611_fighterbomber_missile              w618_sportsmuscle_missile   <- donor chassis
w604_helicopter_mgun(+_impact)   w612_fighterbomber_missile_air_lockon   w619_buggy_mgun
w605_smalltank_canon             w613_bomb / w613_..._ground_lockon      w620_racingboat_mgun
w606_heavyhelicopter_missile     w614_monorailmissilecar_missile         w621_advancedhelicopter_missile
w607_heavyhelicopter_mgun        w615_helicopter_heavy_missile           w622_advancedhelicopter_mgun
w608_fighterjet_missile
```

The decisive one: **`v0300_car_kensington_sportsmuscle_signature_preorder`** — the same chassis
as our donor — ships `CMissileWeaponBase` + `CAimPOIWeaponComponent` + `SWeaponPoint` and
`editor/entities/jc_explosions/weapons/w618_sportsmuscle_missile.ftune`. Our donor's own parts
module already contains its `hood_signature` and `missile_base_signature` parts (MODLOG §114).
T-W1 is re-opened (T-10/T-11).

### 2.2 "EMP is a feature JC3 does not have" (row T-FX4, `out`) is wrong

`v0505_car_solar_oldtruck_rebel_emp_01` (and `…_emp_custom_mm250`) carries an EMP device
(`oldtruck_emp_device_rebel`, `oldtruck_emp_device_core_rebel` with a `Rotor` behaviour,
`emp_flatbed_table`) and the `entry.use_item` interaction. T-FX4 is re-opened (G2-16 → T-11).

### 2.3 Moving parts have shipped carriers, several proven on land vehicles

`vehicle_common` defines the behaviours and the variable that drives each one; the parts tables
show who uses them (`PARTS_TABLE.jsonl`, field `b`):

| behaviour | driving variable | used by (land = proven for a car) | Batmobile use |
|---|---|---|---|
| `Turret`, `Cannon` | aim | **medium tank, small tank, APC, technical, armoured jeep** | turret yaw + cannon pitch |
| `SteeringWheel` | `steering_turn` | **9 chassis: 8 cars + `v1302` sailboat** | cockpit yoke |
| `EngineRotatingPart` | `engine_rpm` | **`v0506` tractor fan** | rear turbine fan |
| `GatlingGun` | `weapon_rpm` | racing boat (driver-fired), helicopters | Vulcan barrels |
| `MissileHatch` (door) | — | monorail missile car (16 hatches) | missile bay doors |
| `TurretDoor`, `Hood`, `Trunk`, `FrontLeftDoor`… (doors) | entry/exit | **APC, armoured jeep, cars** | canopy |
| `AirBrake` | `air_brakes_T` | fighter-bomber only | rear air-brakes — **land use UNKNOWN → probe in Q** |
| `Flaps` | `flaps_T` | articulated truck / armoured transport mud flaps, planes | **not** for rigid aero fins (mud flaps dangle) |
| `Spring` | — | ATV, buggy, monster truck coil springs | visible suspension, optional |

`MODDING_PLAN.md` gate G3 ("do hinge/fin/rotating parts rotate without code hooks?") is answered
**yes for steering, engine-rpm and weapon-rpm behaviours** by shipped vehicles; only `AirBrake` on
a car stays a probe. Gate G5 (turret aim) is answered by the tanks' `Turret`/`Cannon` parts.

### 2.4 Interaction points still belong to the Serpente

The donor `.epe` carries `entry.*`, `exit.*`, `point.stunt*`, `transition.*` and `trigger.*`
objects (e.g. `entry.driver`, `entry.pull.up.to.stunt.hood.close`, `point.stunt.hood`,
`exit.driver.moving.parachute`) placed for a 3.72 m Serpente. The Batmobile body is 7.03 m long
and 2.27 m tall, so Rico's entry, stunt and exit positions are in the wrong places. This was in no
earlier backlog. G2-18 → T-13 → B-05.

---

## 3. Phase map and gates

```
 G1  BmAK grab completion      (desk; reads BmAK packages; writes Research/BatmobileGrab/*)
  |  exit gate G1X: every feature code in §1 has its BmAK source rows or a proven absence
 G2  JC3 grab completion       (desk; reads JC3 archives; writes Research/JC3Grab/*)
  |  exit gate G2X: every feature code in §1 has a JC3 carrier or a proven absence
 T   Translation               (desk; writes T_ROWS.jsonl + T7…T11 docs)
  |  exit gate TX: 0 rows assumed (or signed off), every row has value+verify, decisions D-1…D-10 answered
 B   Offline build             (writes Builds/bm-0xx/ only; NO install)
  |  exit gate BX: one staged tree per variant, receipts written
 V   Offline verification      (renders, read-backs, predictions written before testing)
  |  exit gate VX: every V check green + predicted-results sheet + user approval to install
 Q   In-game test campaign     (3 planned sessions, batched checklists, recorded)
  |  exit gate QX: every Q check passed or has a named, accepted omission
 R   Release                   (private build + KB field note; publishing needs approval)
```

**What already happened and is not repeated:** G1 18/18 units (423/423 fields, 19,203/20,128
objects); G2 11/11 units (81,952/81,953 entries, 6,045/6,045 modules, 77,611/77,611 geometry
blocks, 57,187 FX files, 18,865 hulls); translation batches A (test-085), B2 (088), B3 (089),
B4 (090), F camera (091) built and file-verified; QA-1 take 1 measured. The live dropzone carries
**test-091**. Phase Q inherits the five queued takes (A2, A5, A6, A7, A9) and every S5 check in
`T_PLAN.md` §5.

---
## 4. Phase P0 — orientation (do once, before G1)

#### P0-1 · Baseline the standing gates   S · deps: — · serves: all
In: §0.7 commands, `STATUS.md`, `MODLOG.md` tail.
Do: 1. Run every §0.7 command. 2. Run `powershell -File Builds/test-091/install.ps1 -Action Status`
and record the live `.ee`/`.toc` hashes (do **not** install or roll back anything).
3. Append a MODLOG section "Unified backlog baseline" with each command's one-line result.
Out: MODLOG section.
Done: every gate green, or each red gate has a MODLOG explanation and a `blocked:` row in §12.
Stop: a gate is red and you cannot explain it → stop, do not start G1.

#### P0-2 · Feature census script (turns §2 into a re-runnable proof)   S · deps: P0-1 · serves: WPN, ANI, WLD
In: `E:\Modding\JustCause3\_grab\detail\*.ee.json`, `Research/JC3Grab/PARTS_TABLE.jsonl`,
`E:\Modding\JustCause3\_grab\entities\v0300_…_civilian_01.ee.json` (module 3 = `vehicle_common`).
Do: write `Tools/scripts/jc3_feature_census.py` with `--write` / `--check`. It must emit, per
entity: weapon component classes found in the `.epe` (regex `C[A-Za-z]*(Weapon|Pulse|Turret|Aim)[A-Za-z]*`),
weapon ids (`w6\d\d_[a-z0-9_]+`), part behaviours (`PARTS_TABLE` field `b`), and the
`vehicle_common` behaviour → variable tables (`all_*_part_properties[].name/…variable`).
Out: `Research/JC3Grab/FEATURE_CENSUS.json` + `.md` (generated).
Done: `--check` passes; the `.md` reproduces every number in §2.1 and §2.3 (25 weapon ids, 17
`CBulletWeaponBase` entities, 7 `CMissileWeaponBase`, `EngineRotatingPart` on `v0506`, etc.).
If a number differs, correct §2 of this file and log it.

---

## 5. Phase G1 — finish the BmAK grab (desk only)

Goal: every BmAK value a feature in §1 needs exists in a generated file. G1 is "complete" for
the inventory (423/423 fields); what is missing is **per-feature extraction** of values the
earlier passes recorded but never organised (weapons, animation, bones, poses, sockets in JC3
space, light colours, audio-by-feature). Every G1 card writes into `Research/BatmobileGrab/` and
adds a `--check` mode. Raw exports (meshes, WAVs, animation keys) go to `E:\Modding\ArkhamKnight\_grab\`.

Rule for every G1 card: **values come from `grab_model.py` / `CHAIN.json` / `objects.jsonl`
only.** If a value is offset-only, use its SDK name from `CHAIN.json`; if it has none there,
record it as `offset 0x…` with the value — never invent a name.

#### G1-08 · Weapons: every value of every weapon/gadget archetype   M · deps: P0-1 · serves: WPN-1…11, HUD-2
In: `Research/BatmobileGrab/CHAIN.json`, `objects.jsonl`, `OFFSETS.json`, `MECHANICS.md`
§"Weapons and projectiles", `Tools/scripts/grab_model.py`, `bmak_chain.py`.
Do: 1. Select every object whose class starts with `RBatmobile` or is `RBasicProjectile`, in all
four vehicle packages (`Playable_Batmobile_SF`, `…MK2_SF`, `…Funhouse_SF`, `…Joker_SF`).
2. For each, dump **all** named values from `CHAIN.json` (fire rate / cooldown, damage, range,
projectile class, speed, acceleration, lifetime, heat bar start/size, inaccuracy-vs-time and
inaccuracy-vs-heat curves with every point, charge time, salvo count, lock time, lock range,
radius, impulse, screen-shake structs, `MissileLaunchSockets`, `BonesToHideWhenNotPresent`).
3. Resolve every object reference to its target (particle system, AkEvent, mesh, projectile).
4. Mark which vehicle variants differ (Batmobile vs MK2 vs Funhouse vs Joker) value by value.
Out: `Research/BatmobileGrab/WEAPONS.json`, `WEAPONS.md`, `Tools/scripts/grab_weapons.py --check`.
Done: `--check` re-derives the file; the `.md` has one section per class (11 gadget classes +
projectiles); every reference resolves or is listed as `missing-object`; 0 hand-typed values.
Stop: a weapon's damage is native-only (no value in any stream) → record `native`, continue.

#### G1-09 · Projectiles and explosions   S · deps: G1-08 · serves: WPN-1…5, FX-2
In: `WEAPONS.json`, `objects.jsonl`, `PARTICLES.json`.
Do: for each `RBasicProjectile`/`RBatmobileMissile` (`Batmobile_Heavy_Cannon_*_Projectile`,
`Batmobile_Missile_Projectile`, `Batmobile_EMPMissile_Projectile(_ForCars)`,
`Batmobile_Tracker_Projectile`, Joker variants): speed, max speed, acceleration, homing values,
lifetime, damage, damage radius, momentum/impulse (`ImpulseComponent0` values), trail and impact
particle systems, flight/explosion AkEvents.
Out: section "Projectiles" in `WEAPONS.md` + rows in `WEAPONS.json`.
Done: every projectile referenced by a launcher in G1-08 has a row.

#### G1-10 · Animation sequences: names, bones, lengths, notifies   M · deps: P0-1 · serves: ANI-2…8, APP-5/6, MOD-4
In: `objects.jsonl` (253 `AnimSequence`, 2 `AnimSet`, 1 `AnimTree`), `MECHANICS.md` §Animation,
umodel (UEViewer) already used for meshes, `upk_read.py`.
Do: 1. The `MECHANICS.md` table shows the class name in the name column, so object names were
not joined: fix the join (export table `ObjectName` → name table) in a new
`Tools/scripts/grab_anims.py`. 2. For each sequence: owning `AnimSet`, name, `SequenceLength`,
`NumFrames`, `RateScale`, animated bone list (from the AnimSet's `TrackBoneNames` / the
sequence's track table), notifies (`AnimNotify_Sound` → AkEvent, `RAnimNotify_Script` → name).
3. Export key-frames per bone with umodel (`umodel -export -anim <pkg> <AnimSet>` into
`E:\Modding\ArkhamKnight\_grab\anims\`), then convert to per-bone rotation/translation tables (JSON,
radians/metres in the PSK frame).
4. Classify each sequence by mechanism: canopy, turret, cannon, Vulcan, missile bays,
transformation (pursuit↔battle), wheels/strafe, suspension, fins/air-brakes, driver/Batman,
other. Classification must cite the animated bones, not the name alone.
Out: `Research/BatmobileGrab/ANIMATIONS.json` + `.md`; key-frame JSON outside the repo.
Done: 253/253 sequences named; each has a bone list and a mechanism class (or `other` with the
bones listed); `grab_anims.py --check` passes.
Stop: umodel cannot export a set → record which and why; continue with the names/bones.

#### G1-11 · Skeleton and vertex-to-bone ownership (needed to split movable parts)   M · deps: P0-1 · serves: APP-5, ANI-2…8
In: `E:\Modding\ArkhamKnight\_grab\meshes\` (`Batmobile_V2.pskx`), `Tools/scripts/pskx_parts.py`,
`psk_geom.py`, `MESHES.md`, `SLOTS.json`.
Do: 1. Read the bone table (name, parent, bind pose) and per-vertex influences of
`Batmobile_V2` LOD0 (and LOD1/LOD2). 2. For each bone, list the faces whose vertices are
weighted ≥ 0.5 to it, per material slot. 3. Give each bone its bind-pose pivot **in JC3
coordinates through the one transform** (`bat_assemble.T`). 4. Flag faces with split weights
(they will need a cut decision in B-02).
Out: `Research/BatmobileGrab/BONES.json` + `.md` (bone, parent, pivot_jc3_m, face counts per
slot, split-weight count); face index lists outside the repo
(`E:\Modding\ArkhamKnight\_grab\bones\<bone>.npy`).
Done: every LOD0 face is owned by exactly one bone or flagged as split; face totals per LOD equal
`MESHES.md` (299,837 for LOD0); pivots are produced by importing `bat_assemble`, not copied.

#### G1-12 · Pursuit ↔ battle pose deltas   S · deps: G1-10, G1-11 · serves: APP-6, MOD-2, ANI-2
In: `ANIMATIONS.json` (transformation sequences), `Batmobile_V2_Pose_States`, `BONES.json`.
Do: for the first and last frame of each transformation sequence, compute every bone's delta
(rotation axis/angle, translation in metres, JC3 frame). Report: turret raise, body lift, wheel
yaw (strafe stance), fin angles, and the total bounding box in each pose.
Out: `Research/BatmobileGrab/POSES.json` + `.md`.
Done: two complete poses (pursuit, battle) with bbox each; every moved bone listed.

#### G1-13 · Sockets in JC3 space (the anchor table every later step uses)   S · deps: G1-11 · serves: WPN, LGT, FX, ANI-9, WLD-3
In: `MECHANICS.md` §Sockets (247 sockets, 65 on `Batmobile_V2`), `BONES.json`, `bat_assemble.py`.
Do: for every `Batmobile_V2` socket: bone + relative location/rotation → world position and
forward vector in the JC3 frame, metres, through the one transform. Include at least: `Driver`,
`CannonMuzzle`, `ChainGunMuzzle`, `RiotSuppressorMuzzle`, `MissileL`, `MissileR`, every
`MissileLaunchSockets` entry from G1-08, `Afterburner`, `Afterburner_Front`, `WinchOrigin`,
`BattleModeSpotLight`, all `HeadLight*`, `BrakeLight*`, `*WheelLight*`, `BootLight`,
`Dashboard_Light`. Note each socket's bone and parent bone (hence which future part it rides on).
Out: `Research/BatmobileGrab/SOCKETS_JC3.json` + `.md`.
Done: 65/65 sockets placed with bone and parent bone; 61/65 lie within the body bbox expanded by
0.5 m. The 4 outliers are the HangFromRope anchors, 2.446 m above the box by design, and the 6
orphan light references from GRB-8 stay listed as orphans.

#### G1-14 · Damage rules, health, armour, regeneration   M · deps: G1-08 · serves: ARM-1…6
In: `CHAIN.json`, `OFFSETS.json`, `REGISTRATION.md`, `BmGame` package (script),
`Working/Translation/POSTMORTEM_DAMAGE.md`.
Do: 1. Dump every damage-related named value of `RVehicleBatmobile` (`Health` 1,200,
`ArmourModeDamageReduction`, `Impact*` (outgoing, T-DM7), death fields, any `*Regen*`,
`*Recover*`, `*Heal*`, `*Armour*`, `*Armor*`, damage-type arrays). 2. Try to read the script
bodies of `TakeDamage`, `ShouldRadialDamageHit`, `TakesDamageFromRam` (UE Explorer / UELib on
`BmGame.upk`). The exe carries 341 native functions for these classes, so a body may be native:
if so, record `native` and the evidence. 3. Write the rule as a table: damage type → multiplier →
which mode.
Out: `Research/BatmobileGrab/DAMAGE_RULES.md` (+ `.json`).
Done: every damage-related field listed with value and source; each script function either
decompiled into the file or marked `native` with proof; regeneration answered yes/no/unknown
with evidence.

#### G1-15 · Audio by feature, decoded to WAV   M · deps: P0-1 · serves: AUD-1…7
In: `AUDIO_MAP.json` (361 events, 447 WEMs), `Working/Audio/` banks, `Working/Audio/EVENTMAP.md`,
`Tools/scripts/grab_audio.py`, `_wem_decode.py`.
Do: 1. Group every event by feature: engine (start/idle/load/RPM loop), afterburner, burnout,
interior, battle-mode in/out, each weapon (fire/loop/stop/tail/impact), winch, EMP, sonar,
tracker, lock-on UI, impacts, death, horn (if any), voice. 2. For each: WEM ids, loop flags,
container type (random/sequence/blend), RTPC bindings with curve points (e.g. `RPM`,
`BML_Speed_Global`, `RevLimiter`). 3. Decode all embedded WEMs to 48 kHz WAV into
`E:\Modding\ArkhamKnight\_grab\audio\wav\` and measure each (duration, peak, integrated loudness LUFS).
Out: `Research/BatmobileGrab/AUDIO_FEATURES.json` + `.md`; WAVs outside the repo.
Done: every one of the 361 events is in exactly one feature group (or `other`); 447/447 WEMs
decoded or listed with the decode error; the 90 `missing-bank` rows stay explicit.

#### G1-16 · Particles by feature   S · deps: P0-1 · serves: FX-1…4, WPN
In: `PARTICLES.json` (206 systems), `WEAPONS.json`, `MECHANICS.md` (wheel particle refs).
Do: group systems by feature (afterburner/exhaust, muzzle flashes, tracers, casings, missile
trails, cannon impacts, EMP charge/burst, sonar, tyre kick-up/burnout/trails, wall-scrape sparks,
speed lines, death explosion, heat steam). Per system: lifetime ranges, spawn rates, sizes,
colours over life, materials/textures, emitter kinds.
Out: `Research/BatmobileGrab/PARTICLES_FEATURES.json` + `.md`.
Done: every system referenced by G1-08/G1-09 or a wheel/vehicle object has a feature group.

#### G1-17 · Light colours, intensities and cones   S · deps: P0-1 · serves: LGT-1/2, APP-4
In: `LIGHTS.json` (101 entries, 4 rigs), `objects.jsonl` (`SpotLightComponent`,
`PointLightComponent`, `LensFlareComponent`, `RHelicopterSpotLightComponent` objects).
Do: for each light entry's components read `LightColor`, `Brightness`, `Radius`,
`InnerConeAngle`, `OuterConeAngle`, `FalloffExponent`, cast-shadow flags, lens-flare colours.
Extend `grab_lights.py` (schema bump) — do not write a second light file.
Out: `LIGHTS.json` / `LIGHTS.md` with colour/intensity/cone columns.
Done: `grab_lights.py --check` passes; every component of the 28 `Batmobile` rig entries has
colour and intensity or `class default` with the default stated.

#### G1-18 · Tyre diameter reconciliation (input for decision D-1)   S · deps: G1-11 · serves: DIM-2
In: `Batmobile_V2.pskx`, `bat_assemble.py` docstring ("tyre Ø ≈ 1.42 m vs the 1.40 m
reference"), `T_ROWS.jsonl` T-G2 (1.366 m), `Working/TrueScale/stations.json`,
`Working/Movement/lore_batmobile.json`.
Do: measure each wheel's tyre outer diameter, rim diameter and width from the PSKX (vertices
owned by the wheel bones), in metres through the one transform. Explain the three numbers
(1.366 / 1.42 / 1.40): which is tread-to-tread, which includes sidewall bulge, which is the
physics radius ×2.
Out: `Research/BatmobileGrab/TYRES.md`.
Done: one table with the three numbers explained; D-1 filled with the measurement.
Stop: do **not** rescale anything. Rescaling is a decision (D-1) and must apply to the whole car
through the one transform (R2) — never to the wheels alone.

#### G1-19 · Cockpit and driver placement   S · deps: G1-11, G1-13 · serves: APP-3, ANI-9
In: `SLOTS.json`, `BONES.json`, `SOCKETS_JC3.json` (`Driver`), materials.
Do: identify the faces/slots of seat, yoke, dashboard screens; give the `Driver` socket's JC3
position, the canopy's inner clearance above it, and the eye point.
Out: `Research/BatmobileGrab/COCKPIT.md`.
Done: seat, yoke, dashboard identified by slot and bone; `Driver` position + headroom in metres.

#### G1-20 · Skins and variants inventory   S · deps: P0-1 · serves: APP-8
In: `MESHES.md` (`Batmobile_MK2_Skin` 55 sockets, `Batmobile_Jokerfied_Skin` 63), `MATERIALS.md`.
Do: per variant: mesh, LOD face counts, materials/textures that differ from `Batmobile_V2`,
socket differences, sim/weapon value differences (from G1-08 step 4).
Out: `Research/BatmobileGrab/VARIANTS.md`.
Done: each variant has a diff table; D-5 can be answered from it.

#### G1-21 · Modes and transformation values   S · deps: G1-08 · serves: MOD-1/2, HDL-6
In: `CHAIN.json`, `MECHANICS.md` sims (`BattleModeVSpeedCurve` etc.).
Do: list every value under `BattleMode*`, `TurnOnSpot*`, `Strafe*`, `Transformation*`,
`TurningModeMaxSpeed`, `ArmourModeDamageReduction`, `AirControl*`, `JumpRamp*`, `KillFlip*`,
`PMDodge*`, `BattleDodgeImpulse`, `StayUpright*` with units (cm, cm/s, degrees, seconds).
Out: `Research/BatmobileGrab/MODES.md` (+ `.json`).
Done: every field named in rows T-BM1, T-AC1, T-RA1, T-SR1 appears with its value.

#### G1-22 · Native remainder check for feature relevance   S · deps: G1-08 · serves: all
In: `GAPS.md`, `NATIVE.md`, `objects.jsonl` (925 untagged; 140 larger than 8 B).
Do: list the 140 by class/owner and mark each `irrelevant` (metadata, functions, stubs) or
`relevant` (could carry a weapon/sim/damage value). For each relevant one, try one more decode
pass with `upk_read.py`; if it fails, record why.
Out: `Research/BatmobileGrab/NATIVE_RELEVANCE.md`.
Done: 140/140 classified; relevant ones decoded or explained.

#### G1-23 · Footage capture for behaviours the files cannot give (only if G1-08…G1-21 leave gaps)   M · deps: G1-08…G1-21 · serves: WPN, MOD
In: list of `UNKNOWN`/`native` values from G1-08, G1-14, G1-21.
Do: for each gap only, measure from Arkham Knight gameplay (the user owns it) or footage: e.g.
cannon reload seconds, Vulcan time-to-overheat, missile lock time, number of missiles per salvo,
tank shells to destroy the Batmobile. Record source (file name + timestamp), method (frame count
at known fps), and repeat count (≥ 3 samples).
Out: `Research/BatmobileGrab/FOOTAGE.md`.
Done: every gap has a measured value with ≥ 3 samples, or stays `UNKNOWN` with the reason.
Stop: if a file value exists, footage never overrides it (R4).

**G1 exit gate (G1X):** `grab_model.py check`, `grab_weapons.py --check`, `grab_anims.py --check`,
`grab_lights.py --check` green; every feature code in §1 that names a BmAK source has rows in a
G1 file or a proven absence. Write a MODLOG section "G1X" listing the files.

---

## 6. Phase G2 — finish the JC3 grab (desk only)

Goal: every JC3 carrier a feature in §1 needs is decoded, with its members, the fleet range and
at least one shipped vehicle that uses it. Decoded data goes to `E:\Modding\JustCause3\_grab\`;
summaries and tables to `Research/JC3Grab/`. Use the existing readers (`jc3index.py`,
`tabextract.py`, `jc3grab.py`, `jc3detail.py`, `jc3adf.py`, `jc3hkx.py`, `jc3fx.py`) — extend
them; do not write a parallel reader.

#### G2-10 · Vehicle weapon catalogue (old WPN-1)   M · deps: P0-2 · serves: WPN-1…5, HUD-2
In: `Research/JC3Grab/INDEX.jsonl` (search `jc_weapons/06_vehicle`, `w6`), `tabextract.py`,
`jc3adf.py`, `jc3fx.py` (for `.ftune` explosion tunes), the 25 ids in §2.1.
Do: 1. List every archive path under `editor/entities/jc_weapons/06_vehicle/` and every
`jc_explosions/weapons/w6*.ftune`. 2. Extract each weapon `.ee` (and its inner `.wtunec` /
weapon tune files) to `E:\Modding\JustCause3\_grab\weapons\`. 3. Decode every tune: fire rate, burst,
damage per hit, damage type, projectile speed/gravity/lifetime, spread/recoil, ammo/clip/reload
or overheat (heat per shot, cool rate), lock-on time/angle/range, homing, explosion radius and
damage, impulse. 4. One row per weapon id.
Out: `Research/JC3Grab/WEAPONS.md` + `WEAPONS.jsonl`, `Tools/scripts/jc3weapons.py --write/--check`.
Done: 25/25 ids (count the `+_impact` variants separately) have a row with every decoded member;
`--check` re-reads the archives and compares.
Stop: a tune type the ADF reader cannot read → extend `jc3adf.py` (as G2-7/G2-9 did); never guess.

#### G2-11 · Weapon wiring per armed vehicle   M · deps: G2-10 · serves: WPN, ANI-2/3, HUD-2
In: `detail/*.ee.json` for the 53 armed `.ee` over 21 chassis (P0-2 list,
`FEATURE_CENSUS.json`), `PARTS_TABLE.jsonl`, `WIRING.jsonl`.
Do: for each armed entity, extract the `.epe` subgraph: weapon component (class + every
property), `SWeaponPoint`s (name, parent part/bone, transform), aim components (`CAimPOI…`,
`CTurretWeapon…`, `CBarrelSpin…`, `CLightWeapon…`), the seat that fires it (driver vs
`mounted_weapon` gunner seat), the `Turret`/`Cannon`/`GatlingGun` parts it moves, and how many
weapons the **driver** can fire and switch between.
Out: `Research/JC3Grab/WEAPON_WIRING.md` (one section per entity) + `.jsonl`.
Done: answers written for: (a) max driver-fired weapons per land vehicle, (b) how two weapons
are bound to primary/secondary fire, (c) whether any vehicle switches between ≥ 3 weapons,
(d) which wiring is driver-fired on a `CCar` (expected: medium tank, small tank, buggy,
signature Serpente).

#### G2-12 · The armed Serpente: exact diff civilian → signature_preorder   S · deps: G2-11 · serves: WPN-3, ANI-6, APP-5
In: `detail/` and `entities/` JSON for `v0300_…_civilian_01` and `v0300_…_signature_preorder`.
Do: diff the two entities file by file: `.epe` objects added/changed (weapon components,
weapon points, parts, effects), modules added/changed (parts module: `hood_signature`,
`missile_base_signature`, any hinge/door entries), meshes added, the `w618` tune path.
Out: `Research/JC3Grab/SIGNATURE_DIFF.md`.
Done: a complete list of what JC3 changes to arm this exact chassis — this is the template for
B-05/B-06.

#### G2-13 · Turret and cannon mechanics   S · deps: G2-11 · serves: ANI-2, WPN-1/2, MOD-2
In: `PARTS_TABLE.jsonl` (parts with `Turret`/`Cannon` behaviours on `v0201`, `v0202`, `v0603`,
`v0200`, `v0504`, `v0600`), the parts modules themselves (`jc3adf.py`), `vehicle_common`.
Do: decode `aim_part_constraints`, `hinged_parts` and related arrays for those vehicles (the
`VOCABULARY.md` `VehicleParts` table only reflects the 4 train files Gibbed reads — re-run
`jc3adf.py` on the tanks' parts modules); record yaw/pitch limits, rates, pivot offsets
(`parent_space_offset`), parent chain (turret → cannon), and how the aim target is chosen.
Out: `Research/JC3Grab/TURRET.md`.
Done: the medium tank's turret+cannon chain is fully described with numbers; same for one
wheeled vehicle (APC or armoured jeep).

#### G2-14 · Moving-part behaviours: who drives each variable   S · deps: P0-2 · serves: ANI-3…8
In: `FEATURE_CENSUS.json`, `vehicle_common` rows (`all_hinged_part_properties`,
`all_rotating_part_properties`, `all_door_part_properties`, `all_fin_part_properties`,
`all_spring_part_properties`), parts modules.
Do: for each behaviour: driving variable, the vehicles that use it, their root class (`CCar`,
`CAirPlane`, …), and the per-part arrays that carry it (`hinged_parts[]`, `rotating_parts[]`,
`door_parts[]`) with their members (axis, angle limits, rpm scale). Mark each
`proven-on-CCar` / `unproven-on-CCar`.
Out: `Research/JC3Grab/MOVING_PARTS.md`.
Done: every behaviour in §2.3 has its member layout and proof column; `AirBrake` on a car is
listed as the only probe (for Q-1) unless a `CCar` user is found.

#### G2-15 · Door-part animation (canopy, missile hatches)   S · deps: G2-14 · serves: MOD-4, ANI-6/8
In: `door_parts[]` of the donor (`door_f_l`, `door_f_r`, `hood_signature`), APC (`TurretDoor`),
monorail missile car (`MissileHatch` ×16), `vehicle_common.all_door_part_properties`.
Do: decode door members (hinge axis, open angle, speed, which interaction opens it, whether
weapons fire opens `MissileHatch`).
Out: `Research/JC3Grab/DOORS.md`.
Done: answers (a) can a door hinge about a transverse axis (canopy tilting forward)? (b) what
opens a `MissileHatch`? (c) does the driver's entry animation open the driver door part?

#### G2-16 · The EMP truck   S · deps: P0-2 · serves: WPN-4/5
In: `detail/` + `entities/` for `v0505_…_rebel_emp_01`, `…_emp_custom_mm250`; `INDEX.jsonl`
for any `emp` paths (effects, explosion tunes, weapons).
Do: describe the EMP device: components, trigger (`entry.use_item`), radius, duration, what it
disables (vehicles, electronics, AI), effects and sounds, whether it can be attached to another
entity.
Out: `Research/JC3Grab/EMP.md`.
Done: a yes/no answer "can the EMP effect be fired by a driver of a different vehicle", with
evidence; the list of files that would have to be copied.

#### G2-17 · `CForcePulse`   S · deps: P0-2 · serves: WPN-5/8, MOD-1
In: `detail/` (79 chassis / 232 `.ee` carry it, incl. the donor; `FEATURE_CENSUS.md`).
Do: dump every `CForcePulse` property per entity; find what triggers it (collision, horn,
explosion) by comparing values across vehicles that differ in behaviour.
Out: `Research/JC3Grab/FORCEPULSE.md`.
Done: members + fleet ranges + a stated trigger or `UNKNOWN` (then it becomes a Q-1 probe).

#### G2-18 · Interaction points and stunt areas   M · deps: P0-1 · serves: WLD-3/4, MOD-3/4, ANI-9
In: donor `.epe` (`detail/v0300_…_civilian_01.ee.json`), `sportsmuscle_stunt_areas.vmodc`,
`Research/Epe/serpente_civilian.xml`, body bbox (T-G1), `Working/TrueScale/stations.json`.
Do: 1. Extract every `entry.*`, `exit.*`, `point.*`, `transition.*`, `trigger.*`,
`interaction.*` object with its full transform and any referenced animation/state name.
2. Decode the stunt-areas module (boxes/planes Rico can stand on). 3. Express each point
relative to the Serpente body bbox and wheel stations, then report where it lands on the
Batmobile body (inside, floating, on-surface) using the Batmobile mesh. Write
`Tools/scripts/jc3interact.py` (`--write/--check`).
Out: `Research/JC3Grab/INTERACTION.md` + `INTERACTION.json`.
Done: every interaction object listed with Serpente position and Batmobile-surface verdict.

#### G2-19 · Driver seat and pose   S · deps: G2-18, G1-19 · serves: ANI-9, APP-3
In: donor `.epe`, `INDEX.jsonl` for `jc_statemachine/vehicles/*`, `jc_skeletons/vehicles/*.bsk`,
other cars' seat objects (supercar `v0401`, hothatch `v0003`, tank `v0201`).
Do: find where the driver attach transform and the driver pose/animation set are chosen; list
the pose sets that exist for cars (sports, truck, tank hatch, bike…) and their seat heights.
Out: `Research/JC3Grab/SEAT.md`.
Done: the member(s) that place Rico and choose his pose are named, with a candidate pose that
fits the Batmobile's `Driver` socket height (G1-19).

#### G2-20 · Exit, bail-out and eject   S · deps: G2-18 · serves: MOD-3
In: `exit.driver.moving.parachute`, `exit.driver.roll.out`, jet/heli exits, state-machine refs.
Do: record what each exit does (launch velocity? parachute/wingsuit state?) and whether any
vehicle launches the driver upward.
Out: `Research/JC3Grab/EJECT.md`.
Done: a stated mapping for BmAK ejection (launch → glide) or `UNKNOWN` (→ Q-1 probe).

#### G2-21 · Turn-on-the-spot (tank pivot)   S · deps: P0-2 · serves: MOD-2, HDL
In: tank/APC modules (`v0201`, `v0202`, `v0603`, `v0200`) in `entities/`, `VOCABULARY.md`
(`LandGlobal`, `LandSteering`, `Transmission`, `CustomLandGlobal`).
Do: compare the tanks' members with wheeled cars to find what makes a tracked vehicle pivot
(e.g. `number_of_wheels`, `is_all_wheel_steered`, track-specific modules or members).
Out: `Research/JC3Grab/TANKTURN.md`.
Done: the member set that produces a pivot is named with values, or the pivot is proven to be
code tied to a vehicle type (then MOD-2's turn-on-spot becomes a named omission).

#### G2-22 · Effect usage vocabulary (old T-FX3 route, `jc3usage.py`)   S · deps: P0-1 · serves: FX-1
In: all `effect_attachments` / `ExtendedEffectUsages` modules (6,045 modules decoded), `FX.md`.
Do: dump every `usage` name and hash across the fleet with the vehicles using it; find the
exhaust / nitro / afterburner / boost flame usages (JC3 shows exhaust flames on nitro).
Out: `Research/JC3Grab/USAGES.md`, `Tools/scripts/jc3usage.py --check`.
Done: the list of usages; a named candidate for "flame during nitro" or a proof none exists.

#### G2-23 · Nitro FX and audio carriers   S · deps: G2-22, G2-24 · serves: FX-1, AUD-2
In: donor effect attachments, `vehicles.bank` nitro event (test-060 swap), `custom_land_global`.
Do: trace what JC3 plays and attaches when nitro fires (effect + sound event + parameters).
Out: section in `USAGES.md`.
Done: the full chain nitro input → effect → sound event is written down.

#### G2-24 · JC3 vehicle audio system   M · deps: P0-1 · serves: AUD-1…7
In: `sound/fmod_banks/vehicles.bank` (210,781,376 B), donor `.ee.fmod_guids`, `LandAudio` (2
members), `Working/Audio/` scripts (`_fbank*.py`, `_fsb.py`, `_fmodguids.py`).
Do: 1. List every FMOD event used by the donor (GUID → event path → parameters → samples).
2. Find where weapon sounds are referenced (weapon `.ee`/tunes) for `w602`, `w603`, `w618`,
`w619`. 3. Find horn and radio carriers. 4. Record sample formats (FSB5 codec, rate, loop
points). 5. Decide which of three ship routes is possible: (a) sample swap inside a copy of
`vehicles.bank` (proven, test-060), (b) a new bank + `.fmod_guids`, (c) mixed.
Out: `Research/JC3Grab/JC3_AUDIO.md` + `JC3_AUDIO_EVENTS.json`.
Done: every donor event and every chosen weapon's events listed with GUID and samples; route
recommendation with evidence.

#### G2-25 · HUD vehicle-weapons API   S · deps: G2-11 · serves: HUD-2, WPN-12
In: decompiled `ui/hud.gfx` (260 scripts), `T6_HUD_CAMERA.md`.
Do: document `InitVehicleWeapons` / `UpdateVehicleWeapons` arguments (slot count, icon id,
ammo/heat/cooldown), the lock-on HUD used by `w609`/`w612`/`w613`, and how the entity feeds them
(weapon id → icon).
Out: `Research/JC3Grab/JC3_HUD_WEAPONS.md`.
Done: each BmAK HUD element in WPN-12 has a JC3 element or a stated absence.

#### G2-26 · Rebel Drop data (RD-1 read half)   S · deps: P0-1 · serves: WLD-1/2
In: `Research/1456340180_Rebel-Drop-Mod-V5.3/*/profile/item.onlinec` and `task.onlinec`, the
vanilla `profile/*.onlinec` from the archives, `jc3adf.py`.
Do: decode both mod and vanilla files; document an entry's fields (entity path, name string
hash, icon, category, cost/cooldown, unlock); diff mod vs vanilla to see exactly how a new entry
is added.
Out: `Research/JC3Grab/REBELDROP.md`.
Done: a field-by-field recipe for adding an entry named "Batmobile" that spawns a given `.ee`.

#### G2-27 · Standalone entity (no longer replacing the Serpente)   M · deps: G2-26, G2-29 · serves: WLD-1/8, MOD-5
In: `INDEX.jsonl`, settings/registry files that list vehicles (`settings/*.bin`), Rebel Drop V5.3
Plus `editor/entities/**` override pattern, `.stringlookup`.
Do: find every place a vehicle entity path or hash is registered (spawn tables, garage/drop,
vehicle id lists, string tables). Decide whether a **new** path (e.g.
`editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_batmobile.ee`)
can be loaded from the dropzone without editing a global registry.
Out: `Research/JC3Grab/STANDALONE.md`.
Done: a yes/no with evidence and the list of files a standalone entity needs. Feeds D-6.

#### G2-28 · Damage model, complete, with a predicted hits-to-kill table   M · deps: G2-10, G1-14 · serves: ARM-1…6
In: `DAMAGE_MECHANISMS.md`, `lave_health_medium` and other health modules, `PARTS_TABLE.jsonl`
damage types, tank parts/damage types, `WEAPONS.jsonl`, `damage_audit.py`, `vhealth.py`.
Do: 1. Write down how a hit becomes health loss (weapon damage × damage type × armour channel ×
armour strength gate (99 vs 100, MODLOG §97) × part damage type × root `health` scale).
Cite each step; mark undecoded steps `UNKNOWN`. 2. For the donor, the medium tank and the
current build, compute hits-to-kill for: Rico's pistol, assault rifle, MG, shotgun, RPG,
grenade, tank cannon (`w602`), heli missile (`w601`), heli MG (`w604`). 3. Compute what root
`health` scale / `invulnerable` / armour values would give ARM-1 (no small-arms damage) and
ARM-2 (destroyable by heavy weapons) with the BmAK ratio from G1-14.
Out: `Research/JC3Grab/DAMAGE_MODEL.md` + `Tools/scripts/damage_predict.py --check`.
Done: a predicted table for all three vehicles; any `UNKNOWN` step becomes a Q-1 damage probe
with the exact expected values for both hypotheses.

#### G2-29 · Traffic, AI and spawning of `v0300`   S · deps: P0-1 · serves: WLD-8, MOD-5
In: `INDEX.jsonl` (spawn/traffic/population files), any file referencing the donor entity hash
or path (`v0300_car_kensington_sportsmuscle_civilian_01`).
Do: list every file that can spawn the donor (traffic, parked cars, missions, Mario's house) and
whether AI drives it there.
Out: `Research/JC3Grab/TRAFFIC.md`.
Done: a list of spawn sites; a statement whether replacing `civilian_01` puts NPC-driven
Batmobiles in traffic (lore break → D-6).

#### G2-30 · `.physicsc` write spike (old Batch D route)   M · deps: P0-1 · serves: DIM-4
In: `Tools/scripts/jc3hkx.py`, `SHAPES.md`, `WIRING.md`, donor `sportsmuscle.physicsc`,
`Working/Assembled/sportsmuscle_true.physicsc`.
Do: 1. Round-trip the donor file byte-for-byte (read → write unchanged). 2. Replace one convex
hull with a scaled copy, write, re-read with `check --all` (plane/vertex/AABB invariants).
3. If 1 and 2 pass, write the plan for a Batmobile hull set (convex decomposition of the body
mesh, same compound/instance layout, same station table).
Out: `Research/JC3Grab/PHYSICS_WRITE.md`; tool changes in `jc3hkx.py`.
Done: round-trip identical and the modified file passes every invariant → rows T-P3/T-CO2/T-CO3
become buildable; otherwise they close as named omissions with the failure recorded.

#### G2-31 · Water behaviour   S · deps: P0-1 · serves: WLD-6
In: `buoyancy`, `water_interaction` modules of the donor, the armoured transport, tanks, the
`v1717 duck` (amphibious) and any engine-kill/drown member.
Do: describe what makes a car sink, float, keep driving or die in water; record the members.
Out: `Research/JC3Grab/WATER.md`.
Done: members + values for "sinks and stalls" vs "floats" vs "drives underwater".

#### G2-32 · Names, icons and strings   S · deps: G2-26 · serves: WLD-2
In: `.stringlookup` of the donor entity, localisation tables, UI icon references.
Do: find where "Kerner Serpente R" (or its hash) is displayed: vehicle HUD name, drop menu,
map icon; record string ids and icon textures.
Out: `Research/JC3Grab/NAMES.md`.
Done: every place the name/icon appears has a file + id.

#### G2-33 · Light system consolidated (LGT-1/LGT-2 evidence in one place)   S · deps: P0-1 · serves: LGT-1/2, APP-4
In: `Working/Lights/LGT1_FINDINGS.md`, MODLOG §112–§113, `ENTITIES.md` (3,972 `SVehicleLight`),
`GEOMETRY.md` (`CarLight` block), donor lights module.
Do: one document: `SVehicleLight` member list and presets, how a light binds to a part
(`has_lights`), the `CarLight` block format, what a custom light without a preset needs.
Out: `Research/JC3Grab/LIGHT_SYSTEM.md`.
Done: a recipe for one custom light (wheel-arch light) with every member value sourced.

#### G2-34 · Tether, airlift and winch carriers   S · deps: P0-1 · serves: WLD-7, WPN-6
In: `INDEX.jsonl` (grapple/tether tunes, `transport_rope_winch` on `v1602`, cargo plane
`v4603 … military_cargo_tank`), `tether_tear`/`tether_yank` objects.
Do: record tether strength vs vehicle mass, whether vehicles can be airlifted, and whether any
vehicle-mounted winch/rope exists that a car could carry.
Out: `Research/JC3Grab/TETHER.md`.
Done: WLD-7 has values; WPN-6 has a carrier or a proven absence.

**G2 exit gate (G2X):** every new reader has `--check` green; P0-2 census re-run; every feature
code in §1 has a JC3 carrier with evidence or a proven absence. MODLOG section "G2X".

---
## 6b. Phase G3 — research-reset grabs (2026-11-02; desk + read-only game measurement, no builds)

Added after the research reset (`RESET_FINDINGS.md`). Each card closes a grab that G1/G2 missed or left
partial; the evidence that the gap exists is in the card. **Nothing in T or B may consume a value whose
G3 card is open.** A card is done only when its Out file exists and its `--check` re-derives it.
Every Out file labels each value `decoded` / `derived (rule + inputs)` / `UNKNOWN` — no `chosen`/`assumed`.

#### G3-01 · BmAK drivable collision (class defaults)   M · deps: — · serves: DIM-4, WLD-4, R-1
Evidence of the gap: the 32 `RB_BodySetup` boxes belong to `Batmobile_V3_Destroyed_Physics` (the wreck,
`PHYSICS.md:75`). The drivable archetype `Vehicle.Batmobile` carries `BatmanCollisionMeshPursuitMode0`,
`BatmanCollisionMeshBattleMode0` (StaticMeshComponent, 36/59 B parsed), `CollisionCylinder`,
`FrontCollisionCylinder`, `RearCollisionCylinder` (CylinderComponent, `eof`), `RB_StayUprightSetup` (0 tags),
and `SVehicleMesh` (172/258 B parsed). All are instances of `Default__RVehicleBatmobile.*` (imports 456,
457, 577, 578), defined in `BmGame.upk`, which was only value-hunted (chase-02/03), never decoded for these.
Do: 1. decode `Default__RVehicleBatmobile` / `Default__RVehicleBatmobileBase` component objects in
`BmGame.upk` and the archetype overrides, to the last byte (StaticMesh refs, Translation/Rotation/Scale3D,
cylinder Radius/Height, BlockActors/CollideActors/BlockRigidBody flags, the SVehicleMesh PhysicsAsset ref).
2. locate every referenced StaticMesh/PhysicsAsset (BmGame/Startup/StartupPatch/other cooked packages) and
extract its collision geometry (umodel + the package's own collision data, not the render LOD).
3. express all of it in the Batmobile_V2 mesh frame and in JC3 space (same transform as G1-13 sockets).
4. state which primitive does what in BmAK (vehicle-vs-world, vehicle-vs-Batman/pawns, per mode).
Out: `Research/BatmobileGrab/COLLISION.md` + `COLLISION.json`. Done: every collision primitive of the
drivable car listed with source export, flags, geometry and JC3-space bounds; 0 bytes left unparsed on the
7 objects above, or the unparsed tail named with its reason.

#### G3-01b · BmAK collision geometry (BodySetup AggGeom + Batmobile_V3_Physics)   M · deps: G3-01 · serves: DIM-4, WLD-4, R-1
Evidence (G3-01, re-verified 2026-11-03): the drivable Batmobile's collision components reference, in
`BmGame.upk`: StaticMesh 175973 `Batmobile_V2` (battle-mode collision mesh, RB_BodySetup 169748, 43,346 B)
and StaticMesh 175974 `Batmobile_V2_Collision_Pursuite` (pursuit, RB_BodySetup 169749, 14,062 B);
SVehicleMesh references PhysicsAsset 158266 `Physics.Batmobile_V3_Physics` (drivable, not the wreck). Their
AggGeom payloads are native binary (not property tags) and were not decoded.
Do: decode the UE3/BmAK RB_BodySetup AggGeom serialisation (sphere / box / sphyl / convex elements:
transforms, extents, convex vertex + plane data) with an oracle (e.g. umodel/known UE3 layout + round trip,
bounds vs the render mesh); decode Batmobile_V3_Physics bodies (bone, BodySetup, AggGeom) and constraints;
decode the cylinder radius/height names (CylinderComponent layout: 78.0 / 175.0 at offsets 540/544) and
which collision mesh is active per mode (BatmanVsBatmobileCollisionMode). Express everything in the
Batmobile_V2 frame and JC3 space; resolve the actor-to-PSK frame link G3-01 left conditional.
Out: extend COLLISION.md/.json via grab_collision.py. Done: every element's geometry decoded with an oracle,
or UNKNOWN with what blocked it.

#### G3-01c · BmAK convex elements 1..N (battle 43 / pursuit 13)   M · deps: G3-01b · serves: DIM-4, R-1
Evidence: G3-01b decoded only element 0 of RB_BodySetup 169748 / 169749; the array chain does not close.
umodel's source does not decode BodySetup (UBodySetup is suppressed), so it is no layout reference. Do: test
the UE3 FKConvexElem serialisation as a HYPOTHESIS against the bytes (byte accounting to the payload end,
triangles on own planes, ElemBox == vertex bounds, union vs StaticMesh bounds); prove or reject.
Out: `Tools/scripts/grab_collision_convex.py` -> `Research/BatmobileGrab/COLLISION_CONVEX.md/.json`.
Done: 43 + 13 elements decoded with oracles, or the first undecodable byte named.

#### G3-02 · BmAK controls and input   M · deps: — · serves: D-11, MOD-1/2, WPN, R-2
Evidence: `BmGame/Config/BmInput.ini` exists in the install; no grab file mentions bindings or input.
Do: 1. read BmInput.ini (and the Default*/Bm* ini chain it inherits) for every binding/alias that drives
the Batmobile (keyboard + pad): accelerate, brake/reverse, steer, battle mode, afterburner, each weapon,
weapon cycle, exit/eject, camera, gadgets. 2. find the script/class side that consumes them
(`RVehicleBatmobile`, `RSpecialMoveConfig_DriveCar`, BmGame.upk functions/states): which action does what,
hold vs press, mode-dependent behaviour. 3. pursuit↔battle switching: the exact input and state change.
Out: `Research/BatmobileGrab/CONTROLS.md` + `.json`. Done: an action table (action, binding, script
consumer, behaviour, mode) with every Batmobile action and its source line/export.

#### G3-02b · BmAK driving-state input code (the meaning of LT/B/LB/A)   M · deps: G3-02 · serves: D-11, MOD-1/2, WPN-3/4, R-2
Evidence: the user states (2026-11-02, from play): **LT hold = battle mode, release = pursuit; B = track
enemy, or fire the immobilizer missile on a tracked target; missile barrage in battle mode; LB = exit;
A = electromagnetic ejection.** The shipped config (DefaultInput.ini) names none of these as Batmobile
commands; it binds generic tokens: LT -> `Axis aLeftTrigger` (253) + `HoldToZoom`/`DeepScanOut` (251);
B -> `QuickGadgetB` / `OnRelease ReleaseQuickGadgetB` / `Button bCancelButton` (268); LB -> `Button
aLeftShoulder` / `ThermalMode` (271); A -> `EjectFromVehicle` / `BattleStrafe` (267). So the meaning is in
script: the `DrivingMode` state of RPlayerController (BmGame.upk export 105048) and RVehicleBatmobileBase
`PursuitMode` (10525) / `BattleMode` (10547) read those tokens.
Do: decode the bytecode (or native, via NATIVE.md/BMSDK_OFFSETS) of the functions in those states that
read aLeftTrigger / QuickGadgetB / ReleaseQuickGadgetB / aLeftShoulder / bCancelButton / EjectFromVehicle /
BattleStrafe: the threshold on aLeftTrigger, the state transitions, which weapon class fires per mode
(RBatmobileVehicleTracker, RBatmobileEMPMissile, RBatmobileMissileLauncher), hold vs press timings.
Out: a "consumers" section in `Research/BatmobileGrab/CONTROLS.md` (via grab_controls.py). Done: each of
the user's five statements is confirmed or contradicted by decoded code, with export + offset, and every
threshold/timing value is decoded or UNKNOWN. Until then the user's statements are the spec, labelled
`stated (user)`.

#### G3-02c · BmAK native input path (BatmanAK.exe)   M · deps: G3-02b · serves: D-11, MOD-1/2, R-2
Evidence: G3-02b found ToggleBattleMode (BmGame.upk 105028) and TryToChangeMode (native thunk 10552) with
no script caller, aLeftShoulder with no script reader, so LT->battle and LB->exit are decided in native
code. `Binaries/Win64/BatmanAK.exe` (55 MB) carries the native side (`NATIVE.md`, grab_native.py: 31
classes, 341 native functions; BMSDK_OFFSETS.json).
Do: static disassembly only (no running game, no injection): locate the native implementations and
callers of ToggleBattleMode / TryToChangeMode / the input-axis handling that reads aLeftTrigger /
aLeftShoulder / the exit path (ExitVehicle, EjectFromVehicle) and SelectVehicleWeapon(1) weapon resolution;
decode thresholds and timings as constants with their addresses. Out: `Research/BatmobileGrab/
CONTROLS_NATIVE.md` + `.json` + `Tools/scripts/grab_controls_native.py`. Done: each user statement
confirmed/contradicted by an address + instruction trace, or UNKNOWN with what blocked it.

#### G3-02d · BmAK runtime observation of the controls (read-only)   M · deps: G3-02c · serves: D-11, MOD-1/2, R-2
Evidence: static analysis stops at the input->state link. G3-02c located the native mode switch
(TryToChangeMode impl 0x140063e90 called with BattleMode 0x240 / PursuitMode 0x241 from
ARPlayerController.DrivingPlayerMove body 0x140254560), gated by vehicle flag bits 0x10 / 0x8000 at
[vehicle+0x11d8] and a +-0.707 compare - but DrivingPlayerMove's caller and those meanings are UNKNOWN,
and LB->exit / A->eject / B->weapon per mode have no decoded route.
Do (only after the user approves the session and is at the keyboard): 1. check BatmanAK.exe for
anti-tamper/DRM that forbids debugging or memory reads; if present, STOP and report - never bypass it.
2. read-only observation of the running single-player game (no injection, no writes, no code patches):
sample the vehicle mode (the state TryToChangeMode sets), [vehicle+0x11d8], the float compared to +-0.707,
and the exit/eject natives' entry (by hardware-free means: periodic memory reads or a full-memory
minidump per input). 3. the user presses each input in a scripted order (LT hold/release, B tap/hold in
each mode, LB, A); the agent never drives the user's controls unless asked. 4. correlate each input to
the observed state change.
Out: `Research/BatmobileGrab/CONTROLS_RUNTIME.md` + the raw samples. Done: each of the user's five
statements CONFIRMED / CONTRADICTED by observed state changes with timestamps, LT threshold/timings
measured, flag bits and the 0.707 test named - or UNKNOWN with what blocked it.

#### G3-03 · BmAK config files   S · deps: — · serves: HDL, CAM, APP-2, R-6
Evidence: BmGame.ini (4 research hits, chase only), BmEngine.ini (2), BmCamera.ini, BmSystemSettings.ini
never read as a whole. Do: list every section/key in the BmAK ini set that names the Batmobile, vehicles,
physics (RB/PhysX settings, gravity, substeps), post-process/tonemap/exposure, and camera. Out:
`Research/BatmobileGrab/CONFIG.md`. Done: every relevant key with file, section, value.

#### G3-04 · BmAK colour pipeline (what "black" is in BmAK)   M · deps: G3-03 · serves: APP-1/2, R-4
Evidence: T-MA3 decoded base colour linear [0.0258, 0.0258, 0.030]; the build replaced it with screenshot-
chosen constants (ALB-2). Nothing decoded what BmAK does with that value before it reaches the screen.
Do: 1. the Mainbody material chain end to end (MIC → parent MICs → master material graph: every expression
and parameter that reaches BaseColor/Specular/Roughness/Emissive), already partly in MATERIALS.md - finish it.
2. the lighting terms that graph depends on (reflection/environment, wetness, post-process: tonemapper,
exposure, colour grading) and where each is set (G3-03 inis, level packages). 3. a reference measurement:
BmAK footage/screenshot pixel values of the body under named lighting (FOOTAGE.md) tied to those terms.
Out: `Research/BatmobileGrab/COLOUR.md`. Done: the BmAK body's on-screen colour written as a function of
named, sourced terms - or each missing term marked UNKNOWN with where it would be found.

#### G3-04b · BmAK material function bodies (the colour logic)   M · deps: G3-04 · serves: APP-1/2, R-4
Evidence: G3-04 decoded the Mainbody chain to the master, but the master's DiffuseColor/SpecularColor/
SpecularPower/Normal are null-with-mask: the colour is produced inside 12 MaterialFunctions
(Material_Functions.Batmobile_Edge_FCT, Batmobile_Damage_FCT, Batmobile_Damage_Dirt_FCT, mud, anisotropy,
BMBL_Rain_Opt / rain_effect_V2_Optimised, ...) in packages no grab has read. Do: locate those packages
(cooked .upk census by export name), decode each function's expression graph to the BaseColor/Specular/
Roughness outputs, with an oracle per function (every expression input resolved, parameter names match
the MIC chain's). Out: extend COLOUR.md via grab_colour.py (or grab_colour_functions.py). Done: the body
colour written from decoded expressions up to the lighting term; lighting/tonemap stay UNKNOWN (engine).

#### G3-05 · BmAK packages not yet read   S · deps: — · serves: APP, WPN, R-6
Evidence: grab scope = Playable_Batmobile*_SF only (GAPS.md "Excluded packages"); Std_* packages 25–50 %
decoded; not read at all: `Gad_RBatmobileRemoteBm_SF` (remote-control gadget), `Showcase_Batmobiles*`,
`Showcase_UI_Batmobile*`, Batmobile exports inside `Startup.upk`/`StartupPatch.upk`.
Do: census each (exports by class, Batmobile-relevant exports, what they add over Playable_Batmobile_SF).
Out: a section in `GAPS.md` per package. Done: each package either decoded for its relevant exports or
recorded as irrelevant with the export census that shows it.

#### G3-06 · BmAK untagged/native remainder   M · deps: G3-01 · serves: HDL, ARM, APP, R-6
Evidence: 925 untagged objects (GAPS.md), incl. RB_StayUprightSetup, RVisualDamageComponent,
SkeletalMeshComponent, 4 MaterialInstanceConstant (`eof`), the `BmScript` package (not on disk).
Do: for each class, decide relevance with evidence; decode the vehicle-relevant ones (native layouts via
NATIVE.md/BMSDK_OFFSETS). Also every **partly parsed** object (parsed < size, measured 2026-11-02: Vehicle 4, Weapons 10, Projectiles 8, Batmobile/BatmobileV3_Materials 36 materials, ...): the unparsed tail is either the asset's binary payload (texture/mesh/anim - name the extractor that reads it) or undecoded properties (decode them). Out: `Research/BatmobileGrab/REMAINDER.md`. Done: 925/925 untagged and every partial object in Vehicle/Weapons/Projectiles/materials accounted for.

#### G3-07 · JC3 runtime oracle (read-only)   L · deps: — · serves: every Q check, R-3
Evidence: every verification so far is file-vs-file; no observation ever showed which `.physicsc` the
drop loads, nor where its collision sits relative to the mesh (Q re-test 5).
Do: a read-only inspector for the running game (single-player, no anti-cheat; full-memory minidump or
ReadProcessMemory, no writes, no injection): 1. list the resources loaded for a spawned vehicle (path
hashes → names); 2. read the live physics bodies of that vehicle (body id, shape type, world transform,
AABB) and the render instance transform. Validate on the vanilla Serpente first (known files), then the drop.
Out: `Tools/scripts/jc3oracle.py` + `Research/JC3Grab/ORACLE.md`. Done: for vanilla Serpente, every
loaded resource and body matches the files; the method is then usable as the Q instrument.

#### G3-08 · JC3 vehicle input model   M · deps: — · serves: D-11, R-2
Evidence: D-11 "what JC3 lets a vehicle remap is not yet researched".
Do: where JC3 defines vehicle controls (input action maps in the archives/settings, per vehicle class:
car, tank, heli, boat), how an entity selects its scheme, which actions exist (enter, exit, weapons, nitro,
turret aim, tank pivot), and what an entity/module can change without code. Out:
`Research/JC3Grab/INPUT.md`. Done: every JC3 vehicle action with its definition file and the per-class
differences; a stated yes/no/UNKNOWN for each G3-02 action being reachable.

#### G3-09 · JC3 paint and colour pipeline   M · deps: — · serves: APP-1/2, R-4
Evidence: our CarPaintMM albedo 0x837d86 renders white-violet in noon light; no model predicts JC3's
on-screen colour from authored values. Do: 1. CarPaintMM params → shader (palette/tint path, TintMap,
dynamic params, clearcoat/metallic) as decoded facts; 2. JC3 exposure/tonemap/time-of-day; 3. calibration:
vanilla cars with known authored paint, measured on screen under fixed conditions (G3-07 for the frame).
Out: `Research/JC3Grab/COLOUR.md`. Done: JC3 on-screen colour as a function of named terms, calibrated on
≥3 vanilla paints, error stated. With G3-04: whether an exact BmAK→JC3 conversion exists, or what the
closest defensible mapping depends on.

#### G3-10 · JC3 vehicle physics roles   M · deps: G3-07 · serves: DIM-4, WLD-4, R-1
Evidence: learned only on 2026-11-02 that body 0 (world) is a convex polytope and body 42 (raycast) the
extern mesh; the donor's other 41 part bodies, 2 static compounds (7 front + 7 rear pieces), mass
properties and the `hknpPhysicsSystemData` body entries (G2-30 UNKNOWN 4) have no recorded role.
Do: fleet-wide, for every body: role (world/raycast/part/static compound), which part, which collision
layer, mass/inertia source, and the model↔physics frame relation. Out: `Research/JC3Grab/PHYSICS_ROLES.md`.
Done: every body of the Serpente and a fleet census explained; open fields UNKNOWN with the next source.

#### G3-12 · JC3 donor decode depth   M · deps: — · serves: all T/B, R-6
Evidence: all 566 files of the vanilla Serpente `.ee` are *named* in project docs (2026-11-02 census:
198 .rbm, 116 .ddsc, 74 .effc, 60 .trim, 59 .lod, 31 .vmodc, 17 .ctunec, 4 .pfxc, 2 .etunec, 1 each
.physicsc/.epe/.ftunec/.stringlookup/.fmod_guids) - but being named is how the BmAK collision hid (G3-01):
named, not decoded. Do: per file: decoded fully (with the oracle that proves it: round trip, re-encode,
fleet invariant), partially (which fields/bytes are not), or named only; the `.physicsc` per object
(54 hulls, 18 extern meshes, compounds, body table, constraints, mass properties). Out:
`Research/JC3Grab/DECODE_DEPTH.md` + `.json`. Done: 566/566 files classified; every partial/named-only
file that a Batmobile requirement touches becomes a named open item here.

#### G3-01d · BmAK collision -> render mesh frame link   M · deps: G3-01c · serves: DIM-4, R-1
Prove the chain SVehicleMesh / SkeletalMesh ref pose / collision component transforms that places the decoded
convex union on the render mesh; residual stated. Out: COLLISION_FRAME.md (grab_collision_frame.py).

#### G3-10b · JC3 constraints, mass properties, body entries   M · deps: G3-10 · serves: DIM-4, R-1
Decode the 11 constraints (joins, pivots, axes, limits), 56 hknpShapeMassProperties, the 96-byte body entries,
the second raycast id space and the static-compound references, with fleet invariants. Out: PHYSICS_ROLES2.md.

#### G3-02e · BmAK native mode flags, 0.707 test, exit route (static)   M · deps: G3-02c · serves: D-11, R-2
Who writes [vehicle+0x11d8] bits 0x10/0x8000; what float meets +-0.707; who calls DrivingPlayerMove; native route
from input to SetBatmobileExit / ModifyEjectUpLoc. Out: CONTROLS_NATIVE2.md.

#### G3-11b · Ledger re-check with the right decoders   S · deps: G3-11, G3-12 · serves: R-5
Collision rows via jc3hkx/bm_colmesh/bm_colhull; .epe rows via ConvertProperty named members; re-grade extern
mesh + dynamic compound trees. Out: LEDGER_AUDIT2.md.

#### G3-12b · Debris .pfxc + .ddsc containers   M · deps: G3-12 · serves: R-6
Decode the 4 NAMED-ONLY .pfxc and prove the 116 .ddsc containers to FULL. Out: DECODE_DEPTH2.md.

#### G3-09b · JC3 paint tint selection (static, executable)   M · deps: G3-09 · serves: APP-1/2, R-4
Find in the JC3 executable how a tint is chosen and written into CarPaintMM dynamic params; exposure/tonemap
constants. Out: Research/JC3Grab/COLOUR_NATIVE.md.

#### G3-05b · BmAK skins (MK2, Jokerfied, Standard)   M · deps: G3-05 · serves: APP-8, D-5
Decode the showcase packages' skins: meshes, material chains, sockets, PhysicsAsset bodies, differences to
Batmobile_V2. Out: SKINS.md.

#### G3-07a · JC3 runtime layout for a read-only sampler (static)   M · deps: G3-02d · serves: R-3
Globals/entity list, vehicle -> physics bodies (transforms, AABBs) and render instance, resource table; every offset
with an oracle. Out: Research/JC3Grab/RUNTIME_LAYOUT.md.

#### G3-02f · BmAK sampler fields for X / Y / missile launcher / booster / eject   S · deps: G3-02d · serves: D-11
Offsets from BmSDK for the inputs and gadget state not yet sampled. Out: SAMPLER_FIELDS2.md.

#### G3-10c · JC3 constraints' other side, body entries, inertia   M · deps: G3-10b · serves: DIM-4
Out: PHYSICS_ROLES3.md.

#### G3-14 · BmAK audio banks: referenced vs present vs absent   S · deps: — · serves: AUD, T-AU3/5
Out: AUDIO_BANKS.md.

#### G3-19 · JC3 partial .rbm / .epe to FULL   M · deps: G3-12 · serves: R-6
Out: DECODE_DEPTH3.md.

#### G3-20 · Ledger rows sourced from G3 results (synthesis)   M · deps: G3-11b · serves: R-5, T
Which G3 file supplies/corrects/refutes each of the 198 rows; OPEN rows named. Out: Working/Translation/LEDGER_G3.md.

#### G3-21 · RESET_FINDINGS status (synthesis)   S · deps: — · serves: all
Each R-1..R-6 item RESOLVED / PARTIAL / OPEN with evidence. Out: Research/RESET_STATUS.md.

#### G3-11 · Ledger reconciliation   S · deps: — · serves: all T/B, R-5
Evidence: `T_ROWS.jsonl` says `next` for rows already built (T-WP1/2 by B-05/06, T-L rows by B-05/07).
Do: for each of the 198 rows: translated (built file + member + value) / not / guessed, with evidence.
Out: `Working/Translation/LEDGER_AUDIT.md`. Done: 198/198 rows classified against the built files.

## 7. Phase T — translation (desk only)

Goal: one falsifiable row for every requirement in §1, using the schema already in
`T_ROWS.jsonl` (`cells = [id, BmAK source, JC3 target, transform, now, proposed, confidence,
verify]` + `doc`, `section`, `dispo`, `edits`, `why`). Rows are added through
`Tools/scripts/t_rows.py` (extend it for the new docs); `status_audit.py` counts them.

**Translation rules (apply to every T card):**

1. **Behaviour first (R5).** Write the BmAK behaviour, then the JC3 mechanism, then the value.
2. **Translate by effect when units differ.** Weapon damage, armour and health are translated by
   *ratios that the player experiences* (e.g. "tank shells to destroy the Batmobile",
   "seconds of Vulcan fire to overheat"), computed on both sides, never by copying a raw number
   between engines. Units that do convert (cm → m, cm/s → m/s → km/h, UE degrees, UU rotators
   65,536 = 360°) are converted, with the factor in the `transform` cell.
3. **Out-of-domain values are declared.** A value outside the JC3 fleet range is allowed only
   with an R3-style note in `why` (as Batch B3 did) and a Q check that can fail it.
4. **Medians never carry behaviour rows** (R2 in `T_PLAN.md`). Use a median only for rows with
   no BmAK behaviour, and say so.
5. **Every row ends with a `verify` cell** that is one of: a file check (V phase), a screenshot
   gate, or a Q-take with a numeric pass. "Feels right" is not a verify cell.
6. **Decisions are not rows.** If a row depends on a §11 decision, it is `blocked: D-n` until the
   user answers.

#### T-10 · Re-open the `out` rows with the G2 evidence   S · deps: G2X · serves: WPN, MOD, HDL-6, LGT-2, HUD-2, CAM-2
In: `T_ROWS.jsonl` rows with `dispo = out` (T-LG5, T-FX4, T-DM7, T-W1, T-BM1, T-AC1, T-RA1,
T-SR1) and the 7 `out` rows in `T6_HUD_CAMERA.md` (T-HUD4, T-HUD6…T-HUD10, T-CAM10); G2-10…G2-21.
Do: for each row decide again: (a) a carrier now exists → split into concrete rows in T-11…T-15
and mark the old row `superseded-by: <ids>`; (b) still no carrier → keep `out` and write the
G2 file that proves it in `why`. T-DM7 stays `out` unless G2-28 finds outgoing ram damage.
Expected outcomes (verify, do not assume): T-W1 → split per weapon; T-FX4 → EMP (G2-16);
T-BM1 → turn-on-spot (G2-21) + modes (D-2); T-LG5 → battle spotlight if D-2 keeps battle mode;
T-HUD5/6 → G2-25; T-AC1/T-SR1 → re-check `gravity_multiplier_*`, `takeoff_pitch_damping`.
Out: updated rows; MODLOG section with a table old row → new disposition → evidence file.
Done: `t_rows.py check` + `status_audit.py --check` green; no `out` row lacks a proof file.

#### T-11 · Weapons translation   L · deps: T-10, G1-08, G1-09, G1-23, G2-10…G2-13, G2-16, G2-25, D-3, D-7 · serves: WPN-1…12
In: `WEAPONS.json` (BmAK), `Research/JC3Grab/WEAPONS.jsonl`, `WEAPON_WIRING.md`,
`SIGNATURE_DIFF.md`, `TURRET.md`, `EMP.md`, `DAMAGE_MODEL.md`.
Do: for each WPN code write rows for: carrier (which JC3 weapon id is cloned), slot (primary /
secondary / unavailable, per D-7), weapon point (socket from `SOCKETS_JC3.json`), fire rate,
damage-by-effect (shots-to-kill a JC3 tank, an APC, a soldier, a helicopter vs the BmAK ratio),
projectile speed, spread curve (BmAK `InaccuracyVsTime`/`…VsHeat` fitted onto the JC3 spread
members), heat/overheat (BmAK `HeatBarStart`/`HeatBarSize` → JC3 overheat members if `w603`/
`w619` have them), lock-on (count, time, range), explosion radius/impulse, effects (G1-16 →
nearest JC3 `.effc` by kind), sounds (G1-15 → T-16).
Out: `Working/Translation/T7_WEAPONS.md` + rows (doc `T-7`), plus a weapon edits file per
cloned weapon: `Working/Translation/t7_weapons_edits.json` (same shape as `t5*_edits.json`).
Done: every WPN code has rows or a named omission; every value cell has a class; every row's
verify cell names a Q-3 check from §9 with a numeric pass.

#### T-12 · Moving-parts translation   M · deps: T-10, G1-10…G1-12, G2-13…G2-15 · serves: ANI-2…8, APP-5/6, MOD-4
In: `ANIMATIONS.json`, `BONES.json`, `POSES.json`, `MOVING_PARTS.md`, `DOORS.md`, `TURRET.md`.
Do: one row per moving part: part name (new, `batmobile_<part>`), BmAK bone(s), JC3 behaviour,
pivot (bone bind pose through the one transform), axis, limits (from the BmAK animation's
extreme frames), rate (BmAK anim length → deg/s), parent part, LOD policy, damage type.
Parts: turret (yaw), cannon (pitch), Vulcan barrels (spin), turbine fan (spin), canopy (door),
missile hatches L/R (door), rear air-brakes / fins (hinged; `AirBrake` probe), steering yoke.
Out: `Working/Translation/T8_PARTS.md` + rows (doc `T-8`).
Done: each part has pivot+axis+limit+rate+behaviour or a reason it stays static.

#### T-13 · Interaction translation   M · deps: G2-18…G2-20, G1-13, G1-19 · serves: WLD-3/4, MOD-3, ANI-9
In: `INTERACTION.json`, `SEAT.md`, `EJECT.md`, `COCKPIT.md`, Batmobile body mesh.
Do: for every interaction object, compute its new transform on the Batmobile body. Method:
keep the object's role (driver-side entry, hood stunt point, roof stunt, rear stunt, exit to
swim…), and place it on the Batmobile surface at the analogous location (side of the cockpit for
entry, roof centre for `point.stunt`, front deck for `point.stunt.hood`, rear deck for
`point.stunt.rear`), offset outward by the donor's own clearance from its surface. Driver seat
→ `Driver` socket. Stunt areas → planes fitted to the Batmobile roof/deck faces (normals within
20° of up). Decide hijack entries (`entry.driver.pull.out.*`, `exit.driver.pulled.out`) per D-9.
Out: `Working/Translation/T9_INTERACTION.md` + `Working/Translation/t9_interaction.json`
(object id → new transform), generated by `Tools/scripts/t9_interaction.py`.
Done: every object has a new transform; every transform is ≥ 0.05 m outside the hull and
≤ 0.30 m from the surface (stunt/entry) — checked by the script.

#### T-14 · Damage and armour translation   M · deps: G1-14, G2-28, T-10 · serves: ARM-1…6
In: `DAMAGE_RULES.md`, `DAMAGE_MODEL.md`, `damage_audit.py`, `damage_switches.json`, rows
T-DM1…T-DM9.
Do: 1. T-DM9 (small-arms immunity): choose between root `invulnerable` = 1 (then nothing
damages it — breaks ARM-2) and root `health` scale + armour channels that make small-arms
damage zero/negligible while heavy weapons still kill. Use `damage_predict.py` to show both
options' hits-to-kill tables; pick the one matching G1-14's ratio. 2. Wheels unbreakable
(ARM-4): part damage type for wheels and `front/rear_wheels_damage.*`. 3. Regen (ARM-5) if both
sides have a member. 4. Death look (ARM-6): effects/sound rows.
Out: rows in T-2b / new doc `T10_DAMAGE.md`; `t10_damage_edits.json`.
Done: predicted table shows small arms = no visible loss, heavy weapons = BmAK ratio ± 20 %;
every switch recorded in `damage_switches.json` with `damage_audit.py` green.

#### T-15 · Modes translation   M · deps: D-2, G1-21, G2-21, T-11 · serves: MOD-1/2, CAM-2, LGT-2, AUD-4
Do: if D-2 = two variants: list per variant every row that differs (top speed curve, torque,
steering/pivot, weapons enabled, camera tune, lights, armour reduction, audio) with the BmAK
source (`BattleModeVSpeedCurve` 0→60, 600→40, 1200→30 etc. — units converted). If D-2 = hybrid:
one row set with the compromise declared per row. If D-2 = toggle research: rows stay blocked
until a toggle is proven.
Out: `Working/Translation/T11_MODES.md` + rows; variant table `t11_variants.json`.
Done: every MOD-2 behaviour has a row in each variant or a named omission.

#### T-16 · Audio translation   M · deps: G1-15, G2-24 · serves: AUD-1…7
Do: one row per JC3 event the Batmobile uses: BmAK event(s)/WAV(s) → JC3 event GUID → sample
slot → transform (pitch curve fitted from BmAK RTPC `RPM` points onto the JC3 RPM parameter
range, loop points, gain matched to the vanilla event's loudness ± 1 LU). Weapons per T-11.
Horn/radio per AUD-7. Absent banks stay named omissions (T-AU3/T-AU5).
Out: `Working/Translation/T12_AUDIO.md` + `t12_audio_map.json`.
Done: every donor event and every chosen weapon event mapped or explicitly kept vanilla.

#### T-17 · Effects translation   S · deps: G1-16, G2-22, G2-23 · serves: FX-1…4
Do: per BmAK effect feature: JC3 effect chosen (existing `.effc` path, by kind and size match
from `FX_TABLE.jsonl`), attachment point (socket), trigger (usage/weapon/damage state). Where the
effect must be authored, write the plan with its copy, members and evidence (`T13_FX.md` §5); the
writer itself is card **B-17**.
Out: `Working/Translation/T13_FX.md` + rows.
Done: every FX code has a chosen effect or a named omission.

#### T-18 · Lights translation completion   S · deps: G1-17, G2-33 · serves: LGT-1/2, APP-4
Do: complete T-L1…T-L7, T-LG1…T-LG6 with colours/intensities/cones from G1-17, the wheel-arch
lights as custom `SVehicleLight` entries (closes T-L4/T-LG4), emissive `CarLight` blocks per
lamp part, light-part list for B-04.
Out: rows; `Working/Translation/t14_lights.json`.
Done: every light entry of the `Batmobile` rig (28) maps to an `SVehicleLight` or a named
omission (forensics rig stays out).

#### T-19 · HUD translation   S · deps: G2-25, T-11 · serves: HUD-1/2
Do: complete T-HUD5 (weapon slots/icons), lock-on, heat/cooldown mapping; keep T-HUD1…3.
Out: rows in `T6_HUD_CAMERA.md`.
Done: each HUD element mapped or omitted with proof.

#### T-20 · World translation   S · deps: G2-26, G2-27, G2-29, G2-31, G2-32, G2-34, D-6, D-8 · serves: WLD-1…8
Do: rows for: Rebel Drop entry fields, name/icon strings, standalone vs replacement, traffic
exclusion, water behaviour, tether/airlift expectations, mass/crush expectations.
Out: `Working/Translation/T15_WORLD.md` + rows.
Done: every WLD code has rows.

#### T-21 · Appearance completion   M · deps: G1-11, G1-19, G1-20, D-5 · serves: APP-1…8
In: `Working/Appearance/progress.md` (339 components: 167 transferred, 36 partial, 136
no-JC3-slot), `SLOTS.json`, `VARIANTS.md`.
Do: classify each of the 136 no-slot and 36 partial components: bake into albedo/normal
(POL-2), route to another block type, or drop with reason. Interior materials (POL-1). Skins per
D-5.
Out: `Working/Appearance/APPEARANCE_PLAN.md` + `appearance_progress.py` reflecting the plan.
Done: 0 unclassified components.

#### T-22 · Collision translation (only if G2-30 succeeded) — REOPENED 2026-11-07   M · deps: G2-30, `COLLISION_WHERE.md` · serves: DIM-4
Why it is live again: the card was closed on the 32-body **wreck** census (`PHYSICS.json`), and its
rows therefore reached "the drivable car has no physics asset". `tmp/freebuff/reports/collision-where.md`
(G3-16, `Research/BatmobileGrab/COLLISION_WHERE.md`) decoded the asset the player's car actually
simulates: `Physics.Batmobile_V3_Physics` (BmGame.upk export 158266) - **2 bodies, 3 boxes,
1 constraint** - reached from `Batmobile.SVehicleMesh` property offset 824. So T-P3/T-CO1's target
is 2 body setups / 3 boxes, not 11 of 32 wreck boxes, and the built set (62 donor bodies, body 0's
single hull rewritten - B-10e) is **2 shapes short**. Plan, steps and oracles:
`Working/Translation/T22_REOPEN.md`, `Tools/scripts/t22_reopen.py --check`.
Do: rows T-P3/T-CO2/T-CO3: hull set from the **drivable asset's 2 bodies** (3 boxes, 1 constraint),
convex-decomposition parameters that exist (max hulls, convex radius), part hull bindings
(`has_world_collision_shape`), stations unchanged (R3).
Out: rows + `Working/Translation/t16_collision.json` + `T22_REOPEN.md`.
Done: rows resolved against `COLLISION_WHERE.md`; the 1 constraint either carried or a named
omission with the missing writer named; the pod body's fate stated (it has no JC3 part to bind to).

#### T-23 · Ledger close-out and build batches   S · deps: T-10…T-22 · serves: all
Do: 1. `t_rows.py check`, `status_audit.py --write` then `--check`. 2. Confirm `rows assumed`
= 0 except signed-off rows. 3. Extend `bmak_coverage.py` so weapons, animation, audio and
light features are covered (every G1 file row is assigned to a T row). 4. Write the build batch
list for phase B (which edits file goes into which build step).
Out: `STATUS.md` regenerated; `Working/Translation/BUILD_BATCHES.md`.
Done (gate TX): all checks green; every §1 feature code maps to ≥ 1 row; decisions D-1…D-10 are
answered or their rows are `blocked: D-n` with the user informed.

#### T-24 · Lamp-bound flare sprite (the flare member JC3 does not have)   S · deps: T-18 · serves: LGT-1, APP-4
In: `tmp/freebuff/reports/lens-flare-carriers.md` (T-L25…T-L34), `LIGHT_SYSTEM.md` §2, `FX_TABLE.jsonl`.
Do: 1. Attach `effects/flare/headlight_flare_01.effc` (8,079 B, in **160** vehicle `.ee` bundles)
at each of the six socketed flare sockets through the entity/effect side (`SAttachedEffect`, T-13's
carrier), **not** through the light module: no member of the 25 names a sprite, `FX.md` has no flare
parameter, and no bloom setting is decoded. 2. Record per socket: parent entity, socket bone, effect
path, and whether the effect's `RenderBlockTypeHash` set matches the lamp (an `.effc` carries 0
strings, so the texture identity cannot be named). 3. Re-read the attachment after a save/reload.
Out: rows or a `.epe` edit spec; one line per socket in `T14_LIGHTS.md` §6.
Done: in the Q-1 #7 night take a flare appears at each attached socket and at no other lamp; an
effect that will not attach sends its rows to `blocked` with the attempted carrier named - never
to "omitted".

#### T-25 · Lamp state and pulse (forensics rig, muzzle flash)   S · deps: T-18, T-17 · serves: LGT-1/2, WPN
In: `tmp/freebuff/reports/muzzle-and-forensics-lights.md` (T-L10, T-L21…T-L23).
Do: 1. Assemble the two states BmAK switches at runtime: `RVehicle.bForensicsLightActive` (0x0884,
offset 2180) for T-L21…T-L23, and the weapon's fire event for T-L10. 2. Test the two carriers JC3
does ship: a lamp whose `behavior` is driven by the owning system (`SirenLight*` is the fleet's only
state-driven precedent, 15 rows) and an `.effc` + `SAttachedEffect` `Usage` = `Fire` (5,342 objects
in 232 graphs). 3. Record which carrier ran and the probe that shows the lamp **off** when the state
is off - `blinking` is a flag only (664 rows, no period decoded anywhere), so a timed pulse is
UNKNOWN until this card finds one.
Out: one carrier per state; the four rows lose their "no member" note.
Done: the forensics lamps light only in the state and the muzzle light only on the shot, both read
from a recorded take; a carrier that cannot be shown to switch sends its row to `blocked` with the
probe named.

#### T-26 · Decode the Batmobile drag triple (`Drag` / `DragNoLoad` / `DriftDrag`)   S · deps: T-A2 · serves: T-R2
In: `Research/BatmobileGrab/BMSDK_OFFSETS.json` (class `RVehicleSimBatmobile`), the four Batmobile
packages' `Batmobile.SimulationModel` export (5282, 2,328 B, class `RVehicleSimBatmobile`),
`Working/Translation/T1_TRANSLATION.md` T-R2.
Do: 1. Walk the simulation-model export's tag list for the three members the class dump names -
`Drag` @16 (0x10), `DragNoLoad` @20 (0x14), `DriftDrag` @712 (0x2c8) - and record whether each is
serialised in the archetype or only declared by the class. 2. Where one is serialised, decode the
float at its `offset-in-file` and compare it with JC3's `arcade_drag_multiplier` domain (0 … 0.5,
median 0.1, n=271): a load-dependent pair has no single-multiplier carrier, so the output is a
domain check, not a conversion. 3. Re-run T-A2's chain grep one class further
(`RVehicle → RVehicleBatmobileBase → RVehicleSimCar → RVehicleSimBatmobile → SVehicleSimCar`) so the
absence proof no longer stops at `SVehicleSimCar`.
Out: three values or three proven absences, on the T-R2 row.
Done: each of the three is decoded or proven not serialised, with the tag walk recorded.
Stop: the values are code-side (set by the sim at run time, never authored) → record that and keep
T-R2's 0.1 / 0.1 as a fleet-mode keep.

---

## 8. Phase B — build offline (no install)

Every B card writes into a new build lineage `Builds/bm-0NN/` (`bm` = backlog build) based on the
**test-091** `aaf` tree. Use `deploy.py` (golden-hash guard, receipt) with install disabled; the
installer is generated but **not run** until Q. One B card = one build step = one `aafdiff` whose
changed-file list is exactly what the card names (no collateral).

#### B-01 · Build scaffold   S · deps: TX · serves: all
Do: create `Tools/scripts/bm_build.py` that (1) copies `Builds/test-091/aaf` to
`Builds/bm-0NN/aaf`, (2) applies a named list of edit files in order (`t1_apply.py` /
`t5_apply.py` style, each with its own `*_current.json` snapshot), (3) packs (`t5_build.py`),
(4) writes `receipt.json`, `install.ps1` (Install/Verify/Rollback091) without running it.
Out: tool + `Builds/bm-001/` (identity build: no edits) as the control.
Done: `bm-001` `.ee`/`.toc` are byte-identical to test-091's (control proves the scaffold).

#### B-02 · Split the body into movable parts (old PRT-2)   L · deps: B-01, T-12 · serves: APP-5, ANI-2…8
In: `BONES.json`, face lists in `E:\Modding\ArkhamKnight\_grab\bones\`, `bat_assemble.py`,
`psk2rbm.py`, `appearance_pipeline.py`, budget numbers (BUD-1).
Do: 1. Extend `bat_assemble.py` (do not fork it) with `--parts T8_PARTS`: for each part, take
the faces owned by its bones, keep materials, express vertices **relative to the part pivot**
(pivot = bone bind pose through the same transform). The body keeps every unowned face.
2. Close split-weight seams by assigning each split face to the part with the larger weight;
log counts. 3. Emit 5 LODs per part with the same decimation settings as the body.
4. Run the budget: total Model KB ≤ 4,915 (R9); if over, decimate LOD4/5 of the body first
(BUD-1 rule), never the silhouette LODs.
Review input: `SPLIT_FACES.md` groups all 1,701 LOD0 split faces by bone set and slot. The
larger-weight rule resolves 1,670; the 31 three-bone ties are 1.0/1.0/1.0 and need the documented
2:1 or 3:0 part-level vertex fallback (all resolve to weapons).
Out: `Working/Appearance/build_parts/` RBMs; `parts_manifest.json` (part, pivot, faces per LOD).
Done: reassembling every part at its pivot reproduces the body silhouette at ≥ 99.9 %
(`silhouette_check.py`), 0 lost faces vs before the split, budget green.

#### B-03 · Emissive `CarLight` blocks and light parts (old LGT-2)   M · deps: B-02, T-18 · serves: APP-4, LGT-1
Do: for each lamp (head-lamp lenses, tail strip, wheel-arch lights, boot light, dashboard),
cut its faces into a light part (vanilla pattern: `CarLight` + `Window`, static), write the
`CarLight` block with values from T-18.
Out: light-part RBMs; manifest rows.
Done: `spec_check.py` passes on every new block; `GEOMETRY.md`-style decode of the written block
round-trips.

#### B-04 · Parts module (`vehicle_parts.vmodc`)   M · deps: B-02, B-03, T-12, T-14, T-18 · serves: APP-5, ANI, ARM-4, LGT-1
Do: 1. Remove `door_f_l`/`door_f_r` and their `door_parts` entries (old PRT-1; keep the index
map documented). 2. Add every new part (`parts[]`: name, model `.lod`, parent, `parent_space_offset`
= pivot, damage type, `has_lights`, `is_deformable` 0, collision ids). 3. Add behaviour entries
(`hinged_parts`, `rotating_parts`, `door_parts`, `aim_part_constraints`) per T-12/TURRET.md.
4. Pack with `eetoc --internal` (R8).
Out: `Working/Parts/bm_vehicle_parts.json` (edit spec) + the module in the build.
Done: `jc3parts.py check` and `jc3adf.py` re-read the built module; every part's model resolves
to a file in the build; `.toc` record for the module has a non-zero offset.

#### B-05 · Entity graph (`.epe`)   L · deps: B-04, T-11, T-13, T-14, T-18 · serves: WPN, WLD-3/4, ARM-1, LGT-1, ANI-9
Do: using `ConvertProperty` round-trip (proven, plan §7.1) and the signature-preorder diff
(G2-12) as the template: 1. `CPartProp` for every new part. 2. Weapon components and
`SWeaponPoint`s per T-11 (points at `SOCKETS_JC3.json` positions, parented to the turret/cannon
parts). 3. `SVehicleLight` entries per T-18. 4. Interaction objects moved per
`t9_interaction.json`. 5. Root `health`/`invulnerable` per T-14. 6. Keep the camera reference
(`bat_base.ctune`, test-091).
Out: `Working/Entity/bm_epe_edits.json` + the `.epe` in the build.
Done: `ConvertProperty` round-trips the built `.epe` to identical XML; every weapon point,
light and part name resolves (script check); `.epe` object count = base + planned additions.

#### B-06 · Weapon entities (private copies)   M · deps: B-05, T-11 · serves: WPN-1…5
Do: for each cloned JC3 weapon: copy its `.ee`/tunes to a new private path
(`editor/entities/jc_weapons/06_vehicle/w6xx_batmobile_<name>/…`), rename internal hashes,
apply `t7_weapons_edits.json`, point the `.epe` weapon components at the new paths. Never edit
the shipped `w6xx` files in place (R7) — other vehicles use them.
Out: weapon files in the build tree; `Working/Weapons/manifest.json`.
Done: every weapon path the `.epe` names exists in the build; edited tunes re-read with the
expected values (`jc3weapons.py --check --root <build>`).

#### B-07 · Lights module rewrite (old LGT-1 build half)   S · deps: B-05 · serves: LGT-1/2
Do: rewrite `v0300_…_lights.vmodc` entries so every behaviour (head, high, tail, brake, signal
if any) names Batmobile light parts. Private copy if shared (R7).
Done: every entry names a part that exists with `has_lights` = 1.

#### B-08 · Effect attachments   S · deps: B-05, T-17 · serves: FX-1…4
Do: add the afterburner flame / heat haze at `Afterburner` socket with the usage from G2-22;
weapon effects come with B-06; damage/death effects per T-14.
Done: every effect path resolves; usage hash exists in the fleet vocabulary.

#### B-09 · Private health module and damage types (old DMG-2/DMG-3)   S · deps: B-04, T-14 · serves: ARM-1…6
Do: copy `lave_health_medium.vmodc` to a private path, apply `t10_damage_edits.json`, repoint
the `.epe` `damage` reference; part damage types per T-14.
Done: `damage_audit.py` green; `damage_predict.py --root <build>` prints the T-14 table.

#### B-10 · Collision (only if T-22 resolved) — REOPENED 2026-11-07   M · deps: B-02, T-22 (reopened) · serves: DIM-4
Why it is live again: its Done rule compared the built hull to DIM-1's **render** bbox, which is why
the delivered body hull is 25 cm narrower and 20 cm taller than the drivable chassis box (B-10d).
`COLLISION_WHERE.md` (G3-16) decodes the source the car actually collides with - 2 bodies,
3 boxes, 1 constraint - and B-10e decoded the box TMs (identity on both chassis boxes, 4.000 deg on
the pod), so the target is now the asset, not the mesh. The 3-shape gap and the slot question are in
`Working/Translation/T22_REOPEN.md`.
Do: write the **drivable asset's** hull set with `jc3hkx.py`: body 0 <- chassis box 0 (690.305 x
374.536 x 207.5 cm at (9, 0, 106.75)) + chassis box 1 (679.585 x 345.688 x 103.5 cm at (0, 0, 79)),
pod box (166.177 x 189.365 x 39.8 cm at (-30.5, 0, 93.25)) at 4.000 deg about y; stations unchanged
(R3).
Done: `jc3hkx.py check --all --file` on the built file; body-0 shape union within 5 cm of the two
chassis boxes and the pod shape within 5 cm at 4.000 deg; the render-mesh gate moves to the raycast
body (B-10b/body 42); the 1 constraint carried or named as an omission with its missing writer.

#### B-11 · Audio bank   M · deps: T-16 · serves: AUD-1…7
Do: per the G2-24 route: build a private bank (or a copy of `vehicles.bank` with swapped
samples) from the T-16 map; generate `.ee.fmod_guids`; weapon sounds per T-11.
Out: bank file(s) in the build tree; `Working/Audio/bm_bank_manifest.json`.
Done: every mapped event resolves; sample count/lengths match the manifest; the installer
handles and rolls back the bank (old AUD-5).

#### B-12 · Variants (only if D-2 = two variants) — REOPENED 2026-11-06   S · deps: B-05…B-11, T-15 re-run · serves: MOD-1/2
Why it is live again: D-2's hybrid answer is withdrawn (2026-11-06). BmAK has two modes, and the
single car cannot carry the rows that change with them — **T-MD5** (battle top-speed curve),
**T-MD6** (21.6 km/h turning cap), **T-MD7** (battle steering/drive factors), **T-MD8** (turn on
the spot), **T-MD13** (transformation stance), **T-MD14** (battle audio). Evidence:
`tmp/freebuff/reports/mode-switch-carriers.md` §3/§6 (no JC3 member swaps a handling value at
runtime; the entity-variant pattern is the only carrier that holds all five handling rows),
`tmp/freebuff/reports/battle-audio-switch-event.md` §4 (usage-keyed audio, no mode flag),
`tmp/freebuff/reports/keep-audit-world-modes.md` §3 (T-MD10/T-MD11 turn on the same switch).
Preconditions — all new, none met today (a met one makes `b12_variants.py --check` fail: build it,
do not defer it):
1. D-2 re-resolved to **(a) two variants**; if the operator instead keeps the hybrid, this card
   closes again and the six rows stay `blocked` by decision.
2. `t11_modes.py` re-run to emit **two row sets** (`t11_variants.json` schema 2, `pursuit` +
   `battle`); today it emits the one hybrid set (15 rows, 1 variant).
3. A runtime entity swap: no data selects a variant (`mode-switch-carriers.md` §7 U1). The mode
   input is D-11's LT hold, but what it would drive is game-side and undecoded.
4. `bm_build.py --variant pursuit|battle` (it registers no `--variant` today) plus a second
   `Builds/` tree for `aafdiff` to diff.
Do: `bm_build.py --variant pursuit|battle` builds both entities from one source; the only
differences are the rows in `t11_variants.json`'s two variant sets.
Done: `aafdiff` between variants lists only the files the variant table names; each variant holds
its own values for T-MD5/T-MD6/T-MD7/T-MD13, and T-MD8 and T-MD14 stay **named omissions** — the
pivot has no carrier even with two variants (G2-21) and the `BattleMode` usage has no consumer
(U1).

#### B-13 · Rebel Drop entry, name, standalone/traffic (old RD-1, POL-3, EXP-2)   M · deps: B-12, T-20 · serves: WLD-1/2/8, MOD-5
Do: add the "Batmobile" entry (and the second variant if any) per `REBELDROP.md`; strings and
icon per `NAMES.md`; standalone entity path or traffic exclusion per D-6.
Done: decoded `item.onlinec`/`task.onlinec` show the new entries; the entity paths they name
exist in the build.

#### B-14 · Release candidate tree   S · deps: B-01…B-13 · serves: all
Do: one dropzone tree per variant set, `receipt.json`, `install.ps1` with
`-Action Install|Verify|Rollback091|Status`, rollback copy plan for every replaced file
(including the bank and Rebel Drop files).
Out: `Builds/bm-RC1/`.
Done (gate BX): receipt lists every file with sha256; installer `-WhatIf` lists exactly those.

#### B-17 · Effect writer (private `.effc` copies)   S · deps: B-05, T-17 · serves: FX-1…4
In: `Tools/scripts/effc_writer.py`, `Working/Effects/EFFC_WRITER.{json,md}`,
`tmp/freebuff/reports/effc-format-writable.md` §4, the five plans in `Working/Translation/T13_FX.md` §5.
Do: 1. Copy the carriers T-17 names into the build tree at private paths; never patch a shipped
`.effc` in place (R7). 2. Patch values at their decoded offsets - `EmitterTemplates[i].MaxParticles`,
`Instantiators[i].RenderBlockData[]` (one slot per probe: the slot semantics are UNKNOWN),
`Params[]`, `EmitterTemplates[i].StartTime`/`EmitterLifetimeIndex` - in carry mode so the
inline-array duplicate survives. 3. T-FX13's attachment is an entity-graph object
(`SAttachedEffect ShellEjection`, `Effect` = `hash_jenkins(<private .effc path>)`, `Usage`
4131019937, `name_hash` 3811014039, no `world`) under the chain-gun weapon entity, the class
`bm_fx.py` already places. 4. Growth (the two-emitter T-FX12/T-FX16 copy) last: re-lay out the
`A[..]` (offset, count) pairs and `total_size`, or keep the shipped emitter count and record which.
Out: private `.effc` files in the build tree, `Working/Effects/bm_effects.json`, the `.epe`
attachment rows.
Done: `python Tools/scripts/effc_writer.py check` passes; every built effect re-reads through the
built `.toc` with each patched member equal to its T-17 number and 0 unexplained bytes.
Stop: a member's slot semantics are UNKNOWN and no probe may run (test ban) → record UNKNOWN,
patch nothing.

#### B-18 · EMP disable write path (Immobiliser + EMP burst)   M · deps: B-05, B-06, T-11 · serves: WPN-4, WPN-5, MOD-1
In: `tmp/freebuff/reports/immobiliser-and-emp-trigger.md` §7-§8, `Research/JC3Grab/EMP.md` §2/§6/§7,
`Research/JC3Grab/FORCEPULSE.md` §4.3, `Research/JC3Grab/EMP_DISABLE.json`
(`python Tools/scripts/t_md2_emp_state.py --check` re-derives the 0-binding scan).
Do: 1. Clone `w702_emp.wtunec` at a private path (R7: never patch a shipped tune) and mount the
`CEMPWeapon`-bearing weapon entity on the second driver slot `id:00568A74` - the slot T-WP2 gives
the Vulcan, and the slot count itself stays T-WP13's question. 2. Copy the entity `CForcePulse`
`EMP` with `truck_emp.ftune` (100 player/AI damage in 25 m, `*RadiusPercentageMax` 1.0) at the
chassis centre, carrying the three flags as shipped (`4912FC04` 0 / `AE6F7EFF` 1 / `CF4F7880` 1)
and `id:D3DDD766` -> `emp_flatbed_table`. 3. Invent no trigger: the pulse ships unowned and
`is_disabled_by_emp` (exe 0x24EA080) has 0 bindings in 1,941 entries - record the four probes
below instead. 4. When `tmp/freebuff/APPROVED_Q.txt` exists, run Q-EMP-1 (does the engine's own
`w702_emp` stall a stock car), Q-EMP-2 (does the pulse alone), Q-EMP-3 (is a `CEMPWeapon`
accepted in a car's slot) and Q-EMP-4 (the duration bracket) and write the measured duration as
`DisableEnemyDuration`.
Out: `Working/Weapons/emp/` (cloned tune + weapon entity rows + pulse object), the probe build
under `Builds/`, the four predictions in `Working/Q/PREDICTIONS.md`.
Done: Q-EMP-1…4 answered and the duration written from the measurement; failing that, the probes
named and the card stays `todo`.
Stop: the test ban forbids launching → no disable value is invented; the card records the four
probes and stays open.

#### B-19 · Drone hacker chain (allegiance flip)   M · deps: B-05, B-06, T-11 · serves: WPN-7
In: `tmp/freebuff/reports/hacker-and-tracker-gadgets.md` T-WP7 table and leads 1-2,
`Research/JC3Grab/GADGETS_HACK_TRACK.md`, `Research/JC3Grab/EMP.md` §2 (the SAM context act),
`Research/JC3Grab/REBELDROP.md` §4.
Do: 1. Two `SAttachedEffect` rows on the drone-side weapon entity: the beam (`Usage`
4131019937 = `Fire`, effect from a B-17 `.effc` copy) and the success (second `Usage`, value
driven). 2. The interaction: the SAM context-act shape (`CInteractionGraph` with a `use_item`
exit state, `CInteractionTrigger` volumes, the `rico_contextact_hack_sam*.anim` set) authored on
the target drone. 3. The side flip: no `allegiance`/`owner` member exists in 295 decoded wiring
dumps, so author it on the target's weapon points (`faction` is the only side-like member) and
record which runtime value is read. 4. Optional drop route: `Item.Name` =
`hash_jenkins(leaf)` for a player-side drone, reusing the shipped
`v2901_drone_eden_elitedrone_rebeldrop.ddsc` / `.bikc` assets.
Out: `Working/Weapons/hacker/` (two attachment rows, the interaction objects), the probe build.
Done: a probe records a stock drone stopping fire for its own side and firing for the player's;
the HUD line (`NotEnoughEnergyThought` -> a POI label) is placed.
Stop: no runtime accepts the authored flip → record the reader as UNKNOWN and keep the effects
and interaction shipped.

#### B-20 · Sonar pulse and reveal   M · deps: B-05, T-11, T-17 · serves: WPN-8
In: `tmp/freebuff/reports/sonar-and-scan-pulse.md` §3-§4, `Research/JC3Grab/FORCEPULSE.md`,
`Research/BatmobileGrab/AUDIO_BANKS2.md:154-169` (`BmGame.BML_Sonar`),
`Research/JC3Grab/JC3_HUD_WEAPONS.md` §5.
Do: 1. `CForcePulse` + a `.ftunec` copied from `gen_explosion_5m_nodamage.ftune` (0 damage /
5 m, 2 pulses) so the pulse pushes and does not damage. 2. The look: a private `.effc` ring
(B-17's writer); `CMaterialEffectTable` is an opaque 30-byte blob, so nothing readable decides
what it draws. 3. Import `BML_Sonar`'s six verified events (`Pulse_Search` 0x97CBF248,
`Pulse_Full` 0xFFCC9813, `Rumble_Lp` 0x2A77A8B4 + `Stop` 0x835146BE, `Turn_On` 0x02EE7381,
`Turn_Off` 0x265FE0CD) and fire them with the pulse. 4. The reveal: author a vehicle action
that fires the pulse and a marker pass that calls
`CreatePoi(type, use_progress_bar, is_minor, label)` on each revealed target - no decoded script
creates a scan POI, and `CreatePoi` has no distance field. The treadmark half stays out: both of
its BmAK assets are `missing-object`.
Out: `Working/Effects/sonar/` (private `.effc`), the pulse + tune rows, the audio import rows.
Done: the pulse fires from a car action, pushes a parked car without damaging it, plays
`Pulse_Search`/`Pulse_Full`, and N markers appear and expire.
Stop: the marker renderer needs a script hook that does not exist → record UNKNOWN and ship the
pulse + sound, which are decoded.

#### B-21 · Vehicle tracker (projectile + distance HUD)   M · deps: B-05, B-06, T-11, T-19 · serves: WPN-9
In: `tmp/freebuff/reports/hacker-and-tracker-gadgets.md` T-WP9 and projectile tables,
`Research/JC3Grab/WEAPONS.jsonl`, `Research/JC3Grab/JC3_HUD_WEAPONS.md` §5.
Do: 1. Weapon entity + private missile-tune clone with the members that exist
(`missile_base_tuning.missile_loose_lock_distance`,
`meters_times_speed_in_front_of_target`); `SWeaponPoint.world` bakes `LaunchRotationOffset`
5461 = 30.0 deg at the `BattleModeSpotLight` socket, whose light use T-L17 already places.
2. The homing numbers that have no member (bool homing true, `HomingDelay` 0.2, `AccelRate`
30000.0, `MaxSpeed` 20000.0) are authored on the projectile entity and the member the engine
reads is recorded as UNKNOWN. 3. The HUD: a mission-style tracker graph
(`graphs/mission/mm130/mm130_tracker.gdc/.gsc`) creating a `POI_TYPE_LOCK_ON_TARGET` (21) on the
target, plus a HUD element printing the distance - `CreatePoi` carries no distance.
Out: `Working/Weapons/tracker/` (tune + fire position + projectile rows), the tracker graph, the
HUD element row for T-19.
Done: the round homes onto a moving car and a POI with a live distance follows it.
Stop: homing is native and unreadable → ship the weapon entity and the POI, record the homing
member as UNKNOWN with the probe named.

#### B-22 · Droop and up-travel (the two travels JC3 has no member for)   S · deps: T-S6, T-S3 · serves: T-S6
In: `tmp/freebuff/reports/suspension-unit-bridge.md` §7/§9, `Research/BatmobileGrab/TYRES_PACKAGE.md`,
`Research/JC3Grab/VOCABULARY.md` (the 166 `Suspension` modules), card `Research/specs/B-22.md`.
Do: 1. Settle the length first: T-S3 still says 0.70 m and the bridge fits 0.40 m (length/radius
p51.6 against p82.5; at 0.70 m the implied mass is 388.9 kg = +85.2% over the decoded 210 kg).
2. Author `Suspension.*.max_length_offset` 0.30 on both axles in a private `suspension.vmodc` copy -
the closest member to `SuspensionTravelUp` 30 cm, and 0 on all 166 fleet vehicles, so the engine's
reading of it is UNKNOWN. 3. Carry `BMRearWheelMaxDroop` 100 (1.0 m) as a named omission: no member
names a droop or rebound stop and 1.0 m is 2.5x the 0.40 m compression travel.
Out: the private module row; one line per axle on `T-S6` in `Working/Translation/T3_COVERAGE.md`.
Done: the built module reads back `length` 0.40 / `max_length_offset` 0.30 / `min_length` 0, and a Q-2
take shows the wheel extending 0.30 m and compressing onto the 0.40 m stop.
Stop: the engine ignores `max_length_offset` (no extension observed) → record the member as
write-only/UNKNOWN, keep both travels as named omissions and leave `length` at 0.40 m.

#### B-23 · Pursuit-mode and stationary spring rate (no per-mode member)   S · deps: T-S6, B-12 · serves: T-S6
In: `tmp/freebuff/reports/suspension-unit-bridge.md` §7/§9, `Research/BatmobileGrab/MODES.md`,
`Working/Translation/t11_variants.json`, card `Research/specs/B-23.md`.
Do: 1. Do not write `PMWheelSuspensionStiffness` 750 into `strength`: at the decoded 210 kg it is
3.571 s^-2 and a 0.6867 m rest sag = **172% of the 0.40 m travel** (implied mass 55.6 kg, or a 1.51 m
travel no JC3 vehicle at radius 0.64 m authors). 2. If B-12 ships the two-mode car, 750 belongs in the
**pursuit variant's** table with a 1.51 m travel or as a declared out-of-domain switch; otherwise
carry 750 / 20 / 5 as named omissions on `T-S6` with this arithmetic. 3. `StationaryWheelSuspensionBias`
5 has no speed gate at any layer, so only a script that rewrites `hardpoint_offset_along_spring` on a
stop condition can carry it.
Out: the variant row or the omission lines.
Done: a take shows the authored ride height in both modes, or the row names all three numbers as
omissions with the 172% sag beside them.
Stop: B-12 stays unbuilt and no script writes the suspension → the card closes as a documented
absence, not a todo.

#### B-24 · Handling values: the three keep-audits' replacements   M · deps: T-1 · serves: T-ST2, T-ST3, T-ST4, T-ST6, T-K3, T-K4, T-DR1, T-E2, T-E5, T-B1, T-B4, T-A3, T-G4
In: `tmp/freebuff/reports/keep-audit-dimensions-wheels.md`, `keep-audit-steering-and-drift.md`,
`keep-audit-engine-boost-aero.md`, `tmp/freebuff/reports/apply-keep-audit-fixes-handling.md`,
the ledger rows listed above, `Working/Translation/t1_handling.json`.
Do: 1. Write the fourteen replacement cells in one private tree: `land_global.ground_clearance`
0.071; `land_steering` 0.25 / 0.091 s, steer-input power 1/1/1, `wheel_drift_aligning_strength`
0.625; `brakes.handbrake_friction_factor` 4.0 and `min_time_to_block` 0.3; `custom_land_global`
drift min speed 0 and sensitivity 2, `nitro_boost.torque_multiplier` 6.3, `heat_boost` and
`nitro_boost_upgraded` grip 1.5 / extra 80; `land_engine.torque_factor_at_optimal_rpm` 2921;
`land_aerodynamics.top_speed_drag_coefficient` 1.0. 2. NO drag write for T-E5 and no
`official_top_speed` edit tuned to it: 336.4 km/h is the top of a **300-336 km/h** band labelled
`assumed` (signed off 2026-10-23) and the Cd keeps T-A2's class fit **0.55**. The 0.1213 that made
the label reachable was a balance value derived from the assumption and is withdrawn (correction
8391); at 0.55 and T-E2's 894.7 kW the predicted terminal is **267 km/h**, and a top-speed take
tests reachability of a label, not fidelity to BmAK. 3. T-ST2/T-ST3 carry the operator's 0.25 s ruling (item 1,
2026-11-06); do not re-derive them from 720 deg/s.
Out: the private tree plus a read-back of each of the fourteen members through the built `.toc`.
Done: all fifteen read back at the ledger values; the three Q-2 takes named in the audits
(lock timing, handbrake stop/yaw, 5 km/h drift entry) record their numbers.
Stop: a member refuses the value (clamped or ignored) → record the clamp and leave the ledger cell
as declared, with the clamp beside it, never a silently different number.

#### B-25 · Lens flares and the light units (17 flare entries, 4 cone/intensity members)   S · deps: B-03, B-07 · serves: T-LG6
**No payload in RC4** — the flare sprite cannot be attached (no effect member on a lamp), and the
`range`/`angle`/`multiplier` units are unproven, so this card stays `todo` and ships nothing in the
release candidate.
In: `tmp/freebuff/reports/keep-audit-lights.md` §3/§6, `Research/BatmobileGrab/LIGHTS.json`,
`Research/JC3Grab/LIGHT_SYSTEM.md` §3/§8, card `Research/specs/B-25.md`.
Do: 1. Carry the 17 LensFlareChart entries as part-side emitters, not `lights[]` rows: 10 are
flare-only (`T-L25…L27`, `T-L29`, `T-L31…L34`, plus the two orphan-socket cases) and 7 ride a lamp;
the carrier is a `CarLight` block or a `has_lights = 1` part, the technique the wheel-arch recipe
already uses (G2-33 §7). 2. Prove the two orphan sockets (`HeadLight1c`, `HeadLight2c`) are absent
from the shipped mesh before authoring anything on them. 3. Settle the units with one stock-vs-mod
take: `range`, `angle` and `multiplier` have no documented unit (`LIGHT_SYSTEM.md` §8), and T-LG6's
map (`range = Radius/100`, `angle = OuterConeAngle`, `multiplier = clamp(5 x Brightness, 0.5, 5)`)
rests on that assumption.
Out: the part-side emitter rows in `Working/Translation/t14_lights.json`, one probe build.
Done: 17 of 17 flare entries have a named part and socket in the built entity, the two orphan
sockets are recorded absent, and the take shows the beam reach/cone change proportionally when the
`range`/`angle`/`multiplier` triple is moved by a known ratio.
Stop: the take shows the members are display-only (no visible change) → record them as write-only
and keep the flare work as part-side geometry, which is independent of the units.

#### B-26 · Per-entity audio override (21 of 45 pinned GUIDs)   M · deps: B-11 · serves: AUD-2, T-AU2
**No payload in RC4** — the 21 pinned GUIDs stay donor (no private effects-class bank is bound), so
this card stays `todo` and ships nothing in the release candidate.
In: `tmp/freebuff/reports/keep-audit-audio-fx.md` §3, `Research/JC3Grab/JC3_AUDIO.md` §1/§3,
`Working/Translation/t12_audio_map.json`, card `Research/specs/B-26.md`.
Do: 1. `effects.bank` and `character.bank` are shared by every vehicle, so the 19 effects and 2
character GUIDs (breaks, `explosion`, `fire_post_explosion`, `TireDestroyed`, `damage_smoke`,
`water_explosion`, `speedwind_sound_player`, `jump_air_whoosh_sound`) cannot be replaced by a bank
swap. 2. Author the override the `.epe` already knows how to express: one `SAttachedEffect` /
`SDynamicAttachedEffect` per entity pointing at a private `effects`-class bank, keeping the 45 GUIDs
unchanged so the game code still fires them. 3. Do NOT rename or repoint a GUID: the events are
code-fired and their names are not in the bank (`JC3_AUDIO.md` §1).
Out: the private bank plus the per-entity binding rows; a manifest list of the 21 GUIDs.
Done: a stock car and the Batmobile play different samples for the same 21 GUIDs in one session
(recorded takes), and the 24 `vehicles.bank` GUIDs are unchanged.
Stop: an entity-level bank override is not honoured → record the 21 GUIDs as a stated gap on
`T-AU2` with the take, and leave the `vehicles` half green.

---

## 9a. Phase V — verify offline (everything that can be proven without the game)

#### V-01 · File gates on the release candidate   S · deps: BX
Do: `aafdiff` (only planned files), `.toc` records for every file (internal where required),
`spec_check.py`, budgets (Model ≤ 4,915 KB, Texture ≤ 7,065 KB), `jc3parts.py check`,
`jc3adf.py` re-read of every edited module, `ConvertProperty` round-trip of the `.epe`,
`t5_measure.py`-style read-back of **every** edited value through the built `.toc`.
Done: all green; output in `Builds/bm-RC1/verify/`.

#### V-02 · Geometry and pose gates   M · deps: BX
Do: 1. `preview_rbm.py` renders (side/front/top, `--albedo`) of the assembled car at LOD1…5.
2. Pose renders: apply each moving part's limits (turret ±yaw, cannon pitch, canopy open,
hatches open, air-brakes deployed, battle pose if any) and render; check no part leaves the body
envelope by > 2 cm or intersects another part at rest. 3. Silhouette ≥ 99.9 %.
4. Interaction points: every point outside the hull (≥ 5 cm) and within 30 cm of the surface.
Out: PNGs + `verify/geometry.json`.
Done: all checks pass; renders attached in MODLOG.

#### V-03 · Wiring gates   S · deps: BX
Do: every `SWeaponPoint` → existing part/bone; every weapon id/path exists; every effect, light,
sound GUID and Rebel Drop entity path resolves inside the build or the shipped archives
(`jc3index.py` lookup).
Done: 0 dangling references.

#### V-04 · Audio gates   S · deps: BX
Do: decode the built bank back; compare each sample to its WAV source (length ± 1 frame);
loudness within ± 1 LU of the vanilla event it replaces; loops seamless (no click > −40 dBFS at
the loop point).
Done: all events pass.

#### V-05 · Predicted-results sheet (written before any test)   S · deps: V-01…V-04
Do: for every Q check in §9b, write the expected number and pass band, from the T rows and
`damage_predict.py`: e.g. 0–100 km/h, top speed with/without afterburner, braking 100→0
distance, turning circle, drift angle hold, landing (no bounce), shots-to-kill per weapon,
turret traverse time, Vulcan time-to-overheat, missile lock time, camera distance/FOV, light
count at night.
Out: `Working/Q/PREDICTIONS.md`.
Done: every Q check has a prediction and a pass band; nothing in Q is judged without one.

#### V-06 · Install dry run   S · deps: V-05
Do: `deploy.py` guard against the live test-091 hashes; installer `-WhatIf`; run Install and
Rollback against a **copy** of the dropzone folder (e.g. `E:\Modding\_dropzone_sim\`), then diff
with the original copy.
Done: install adds/replaces exactly the receipt's files; rollback restores the copy byte-for-byte.

#### V-07 · Gate VX and approval   S · deps: V-01…V-06
Do: regenerate `STATUS.md`; write the MODLOG section "VX" with all results; ask the user for
approval to install and to start Q-1 (R6). Include the expected session count and length.
Done: written approval recorded in MODLOG.

---
## 9b. Phase Q — in-game test campaign (last, batched, recorded)

**Why it is shaped like this:** every launch costs time and money, so the campaign is three
planned sessions with fixed checklists. Each check has a prediction from V-05; a check passes or
fails against its band — it is never re-interpreted. Independent checks are batched in one
session on purpose (they cannot interact: e.g. a night screenshot cannot change a braking take).
Everything is recorded with `um win record` **with audio** (QA-1 take 1 lost the rpm channel to
`--no-audio`).

**Before every session:** user approval (R6) · game closed · `um backup` the saves ·
`install.ps1 -Action Install` → `-Action Verify` (must be green) · windowed fixed size ·
`um win` screenshot test · note the exact PID for `um win kill`.
**After every session:** kill by PID · copy recordings to `Working/Q/<session>/` · fill
`Working/Q/RESULTS.md` (check id, measured, band, pass/fail, recording timestamp) · MODLOG.

#### Q-PILOT · Narrow piloting cards so small models (even DeepSeek) can drive the game   M · deps: VX, Q-1 design (runs with Q, NOT before)   (operator 2026-11-05)
In:    `C:/Users/User/source/repos/universal-modder` (`knowledge/`, `skills/`, `agents/`: how Universal Modder drives games); `Q-1..Q-3` cards;
       `Research/BatmobileGrab/CONTROLS.md` + `SAMPLER_RESULTS.md` (BmAK controls); `Research/JC3Grab/INPUT.md`.
Do:    1. Write one card per atomic in-game action (launch, load save, spawn/enter the car, enter/exit, mode toggle, eject, weapon, screenshot/log capture), each one
          step per line with the exact command or key and a `Done when` check a script can verify.
       2. Same for the BmAK side (comparison drives): same actions, BmAK keys, so each mod mechanic is compared with Arkham Knight.
       3. Dry-run the cards on a DeepSeek lane WITHOUT the game (read-through) until it can restate each step without gaps; then use them in Q.
Out:   `Working/Testing/PILOT_CARDS.md` (+ `pilot_cards.json`).
Done:  every card has an exact action and a scriptable check; a DeepSeek read-through lists 0 ambiguous steps.
Stop:  **The testing ban has not been lifted.** Do not write cards that launch the game now, and do not queue this card until phase V has exited.

#### Q-1 · Session 1 — static, architecture probes, looks (no driving takes)   L · deps: VX
Spawn at Mario's house (or the Rebel Drop). Checklist:
1. **Spawn**: car appears; Rebel Drop entry "Batmobile" visible and spawns it (WLD-1/2).
2. **Noon screenshots** front/side/rear/top-down (APP-1/2/3, T-MA3…T-MA5 gate): body luminance
   above the road; satin not mirror; canopy reads as glass; no missing parts.
3. **Walk-around interaction**: driver entry from both sides (WLD-3, canopy opens: MOD-4/ANI-8),
   Rico seated pose and head under canopy (ANI-9), exit, exit while moving at 30 km/h
   (parachute/eject, MOD-3), climb to roof and stand on hood/roof/rear (WLD-4).
4. **Moving parts at standstill**: steering yoke turns (ANI-7), turbine spins with revs (ANI-4),
   turret follows camera (ANI-2), cannon pitch limits, Vulcan barrels spin when firing (ANI-3),
   missile hatches open on fire (ANI-6), **air-brake probe**: brake hard from 40 km/h, do the
   fins move? (ANI-5; one-variable probe: if no, ANI-5 becomes static with a named reason).
5. **Weapons, stationary at a wall/rock**: each weapon fires from its muzzle, not the car origin
   (WPN-1…5), HUD shows slots/reticle/heat/lock (HUD-2), effects/sounds play (FX-2, AUD-5).
6. **Damage, self-test**: Rico shoots his own parked Batmobile with pistol, assault rifle, MG
   (count magazines; expect per V-05: no health loss), then RPG/grenades (expect the predicted
   hits-to-kill); wheels survive (ARM-1/2/4). Re-spawn after destruction; death effect/sound
   (ARM-6).
7. **Dusk/night screenshots** with lights on/off: cone count, colours, brake red, wheel-arch
   lights, dashboard (LGT-1, T-LG3/T-LG6/T-L1…T-L7 gates).
8. **Audio at standstill**: start, idle, rev sweep (record), afterburner blip.
Done: every item has pass/fail in `RESULTS.md`; failures are turned into one-variable offline
fixes (Q-4) before Q-2.

#### Q-2 · Session 2 — driving takes at the airfield (QA-1 instrument)   L · deps: Q-1 (or its fixes)
Use `qa1_hud.py` for speed from the HUD; one take per manoeuvre; entry/exit conditions as in
`T_PLAN.md` §5.A. Takes (rows they clear):
- A1 launch 0–100 (repeatability ±5 %) · A2 top speed boost off then on (T-E5, T-B2, T-A1/A2) ·
  A3 constant-radius corner 60/100 km/h · A4 steering hold 60/100 km/h · A5 braking 100→0
  (T-K1/T-K2) · A6 kerb/pothole/landing at 3 speeds (T-S1…T-S3, T-M4, T-G4/T-G6) · A7 handbrake
  drift + release (T-ST5, T-DR1, T-K3/T-K4, T-ST6) · A8 shift points with audio (T-E3/T-E4, T-AU4)
  · A9 0–100 with/without boost (T-B1/T-B3) · A10 skid check (T-EF1) · A15 camera drive
  (T-CAM1…T-CAM7, T-CAM12/13) · A16 HUD drive (T-HUD1…T-HUD3) · battle variant (if D-2): turn on
  the spot, top speed per `BattleModeVSpeedCurve`, camera FOV 60.
Done: every take recorded and compared to V-05; the five queued rows (A2, A5, A6, A7, A9) move
from `next` to verified or back to T with the failure.

#### Q-3 · Session 3 — world and combat   L · deps: Q-2 (or its fixes)
1. A11 ram a wall and cars at 40/80 km/h: no damage (ARM-3), cars shoved (WLD-5).
2. A12 5-star heat survival ≥ 2 min (ARM-1/2); tank shells to destroy vs prediction.
3. Weapons vs targets: shots-to-kill vs soldier, APC, tank, helicopter (WPN-1…3); EMP/
   Immobilizer vs an enemy car (WPN-4/5); Vulcan overheat time (WPN-2); missile lock count and
   time (WPN-3).
4. Water: drive into a lake (WLD-6, D-8 expectation).
5. Tether the car to a pole; airlift if possible (WLD-7).
6. Traffic: drive 10 min through a town; count NPC Batmobiles (expect 0, WLD-8/MOD-5); try to
   get pulled out by enemies (D-9 expectation).
7. A13 break a lamp / burn engine: right effect on the right part (FX-4).
Done: every item in `RESULTS.md`.

#### Q-4 · Fix loop rules   ongoing · deps: Q-1…Q-3
- Each failure → find the row → change **one** value with a provenance class → stage offline →
  run the V gates for that build → batch into the next planned session. Never tune by feel; if
  no row explains the failure, the failure is a new G/T task, not a tweak.
- A Q check that cannot be executed (e.g. pursuit not triggering) is recorded as an attempt;
  the row stays open; the pass band is never lowered.
- Maximum one extra session per original session before the user decides how to proceed.

#### Q-5 · Showcase recording (optional, after QX)   S · deps: QX
Use the `showcase-video` skill: pursuit run, afterburner, battle weapons, night lights, a stunt
on the roof. Credits: Rocksteady/WB (Batmobile), Avalanche (JC3), tool authors.

**Gate QX:** every Q check passed, or has a named omission accepted by the user.

---

## 10. Phase R — release

#### R-1 · What may be shared   S · deps: QX
The Batmobile mesh, textures, audio and particles are extracted from Arkham Knight. Under the
toolkit rules (R10) they **cannot** be published. A shareable release is therefore the
**pipeline**: scripts + edit specs that rebuild the mod from the user's own copies of both games.
Write `RELEASE.md` stating this; run `um publish check .` on the release folder; it must find no
game files or extracted assets.
Done: lint clean; README with install-from-your-own-games steps; credits; AI disclosure.

#### R-2 · Knowledge-base field note   S · deps: QX
Write the field note from `MODLOG.md` with `um kb new` (route, versions, what worked, the four
§2 corrections, the gotchas). PR only after the user agrees (`um kb pr <note> --yes`).
Done: note passes `um kb check`; PR opened only with approval.

---

## 11. Decision register (questions only the user can answer)

Each decision blocks the rows that name it. Ask in one message when phase T starts (or earlier
if a G card produces the data). Record the answer in MODLOG and here.

| id | question | data that informs it | recommendation | blocks |
|---|---|---|---|---|
| D-1 | Tyre diameter: keep the PSKX true scale (1.366 m measured) or scale the **whole car** so the tyre reads 1.40 m? | G1-18 → `Research/BatmobileGrab/TYRES.md`: tread Ø1.3652–1.3657, shoulder Ø1.371, all four wheels within 0.5 mm; 1.42 has no source (initial-commit docstring; the wheel `Disc` bone's own vertical extent is 1.427) | **resolved 2026-10-24: keep the PSKX true scale** — the condition failed: 1.366 does exclude the shoulder, but the bulge is 5.5 mm, so the tyre with its shoulder reads 1.371, still 2.0% short of 1.40; the missing 34 mm to 1.40 is not in the mesh, so rescaling would move ride height, track and body by 2.5% to chase a wiki estimate | DIM-2, T-G2 |
| D-2 | Pursuit/Battle: (a) two Rebel Drop entries, (b) one hybrid car, (c) research a runtime toggle first | G2-14, G2-21, G1-21 | **REOPENED 2026-11-06 (research, task 8301): (b) withdrawn — awaiting the operator.** BmAK has **two modes** (`BattleMode*` 42 declared / 15 serialised, `TurningModeMaxSpeed` 600 cm/s, `TurnOnSpot*`, `Transformation*`) and **a hybrid cannot carry rows T-MD5, T-MD6, T-MD7, T-MD8, T-MD13 and T-MD14**: no JC3 member switches a handling value at runtime, and the only carrier that holds a second value set is a **second entity** (`tmp/freebuff/reports/mode-switch-carriers.md` §3/§6; audio: `tmp/freebuff/reports/battle-audio-switch-event.md` §4; the two rows that already turn on this switch: `tmp/freebuff/reports/keep-audit-world-modes.md` §3). Options now: **(a) two Rebel Drop entries, two entities of one chassis** — the only carrier for the six rows, cost = the swap trigger is UNKNOWN (§7 U1); **(b) keep the hybrid** and accept the six losses as declared omissions; **(c) a runtime selector** — no decoded selector in any module, entity graph or `.physicsc` (UNKNOWN, not planned). The two-mode plan (what flips, which member, which carrier, and every build step that changes) is `tmp/freebuff/reports/apply-mode-switch-rows.md`. Previous answer, kept as history and **no longer in force**: **resolved 2026-10-28 (user): (b) one hybrid car** — a single Rebel Drop entry carrying both modes; pursuit/battle switching is borrowed from JC3 functionality and altered to match BmAK. Until D-2 re-resolves, every approval that rests on the hybrid (audit A-02) is **provisional**, and B-12 is `todo: D-2 reopened`. | MOD-2, T-15, B-12 |
| D-3 | Weapon lethality: BmAK weapons are non-lethal to people (riot suppressor, drones are unmanned); JC3 weapons kill. Accept JC3 lethality, or limit the guns to vehicle targets where possible? | G2-10, G2-11 | **resolved 2026-10-28 (user): accept JC3 lethality, no toggle** — a non-lethal mode does not fit JC3 and would ruin battle mode; the riot suppressor stays a named omission | WPN-2, WPN-10 |
| D-4 | Donor chassis: keep `v0300` (the armed signature variant proves it can carry missiles) or move to a tank chassis for the turret? | G2-12, G2-13, `FLEET.md` | **resolved 2026-10-28 (user): whichever is easiest** → keep `v0300` (the current donor; the armed signature variant already carries missiles) and import turret wiring from the tank | B-04, B-05 |
| D-5 | Skins (MK2, Jokerfied) as extra drop entries, palette tints, or not at all | G1-20 | **resolved 2026-10-28 (user): skins as extra Rebel Drop entries** (MK2, Jokerfied, …) | APP-8 |
| D-6 | Standalone entity, or keep replacing the Serpente (which may put NPC Batmobiles in traffic) | G2-27, G2-29 | **resolved 2026-10-28 (user): standalone entity** (no Serpente replacement) | WLD-1/8, B-13 |
| D-7 | Weapon slots: which BmAK weapons take JC3's driver slots (cannon, Vulcan, missiles…) | G2-11 | **resolved 2026-10-28 (user): every BmAK weapon in both battle and pursuit modes** — no per-mode split; the slot count must carry all weapons (T-11 finds how, e.g. extra driver slots or mode-independent switching) | T-11 |
| D-8 | Water: BmAK's Batmobile is not amphibious. Sink and stall (lore), or JC3 default? | G2-31 | **resolved 2026-10-28 (user): lore** — sink and stall, Rico swims out | WLD-6 |
| D-9 | Can enemies pull Rico out of the Batmobile? | G2-18 | **resolved 2026-10-28 (user): no** — enemies cannot pull Rico out | T-13 |
| D-10 | JC3 gear mods (turbo jump, upgraded nitro tiers) on the Batmobile? BmAK cannot jump. | G1-21, `CustomLandGlobal` | **resolved 2026-10-28 (user): no JC3 gear mods** (no turbo jump, no upgraded nitro tiers); JC3 functionality may be borrowed and altered only so the Batmobile is 100% lore-accurate | HDL, T-B4 |
| D-11 | Controls: which actions use JC3's control and which the BmAK (lore) scheme | G2-14, G2-21, T-11 | **resolved 2026-11-02 (user): only ENTER uses JC3's control; exit and everything else (driving, pursuit/battle, afterburner, weapons) use BmAK's controls** ("only ENTER with JC3 controls (exit and else with BmAK controls)"). What JC3 lets a vehicle remap is not yet researched (open: G2 card) Mapping (user 2026-11-02, corrected 2026-11-03; runtime G3-02d): LT hold battle / release pursuit [CONFIRMED live]; B = immobilizer on an auto-tagged enemy [CONFIRMED live; tracking is automatic, not B]; X = missile barrage in battle [user; config QuickGadgetX -> SelectVehicleWeapon(2)]; Y = boost in pursuit [user; config bVehicleBoostButton]; LB = exit AND enter [CONFIRMED live]; A = ejection [exit CONFIRMED live, EM part UNKNOWN]. | MOD-1/2, WPN, D-2 |

---

## 12. Tracker (flip statuses here; evidence path required for `done`)

| id | status | evidence |
|---|---|---|
| P0-1 | done | MODLOG §"Unified backlog baseline (P0-1, 2026-10-24)" |
| P0-2 | done | `Research/JC3Grab/FEATURE_CENSUS.md` + MODLOG §"P0-2 · Feature census written" |
| G1-08 | done | `Research/BatmobileGrab/WEAPONS.md` + MODLOG §"G1-08 · Weapons record written" |
| G1-09 | done | `Research/BatmobileGrab/WEAPONS.md` §4 + MODLOG §"G1-09 · Projectiles and explosions — done" |
| G1-10 | done | `Research/BatmobileGrab/ANIMATIONS.md` + MODLOG §"G1-10 · Animation sequences — done" |
| G1-11 | done | `Research/BatmobileGrab/BONES.md` + MODLOG §"G1-11 · Bone ownership — done" |
| G1-12 | done | `Research/BatmobileGrab/POSES.md` + MODLOG §"G1-12 · Pose deltas — done" |
| G1-13 | done | `Research/BatmobileGrab/SOCKETS_JC3.md` + MODLOG §"G1-13 · Sockets — done" (4 rope anchors outside the body box; 6 GRB-8 orphan refs) |
| G1-14 | done | `Research/BatmobileGrab/DAMAGE_RULES.md` + `bmak_damage.py --check` (JSON and note byte-identical, 7/7 anchors) + MODLOG §"G1-14 · Damage rules — done" / "G1-14 rework — done" (14 entry points: 5 native, 9 script; missile 250 vs EMP missile 60; readers token-aligned, `HealthRecoverRate` read by one function; regen per class: 0 `*Regen*` members of 25 on the 70 `RVehicle*`/`Pawn`/`AkVehicle` classes, value UNKNOWN) |
| G1-15 | done | `Research/BatmobileGrab/AUDIO_FEATURES.md` + MODLOG §"G1-15 · Audio by feature — done" (361 rows in 14 groups; 423/447 WEMs decoded to 48 kHz WAVs, 24 streamed voice lines carry no bytes on disk; 506 RTPC bindings over 261 objects) |
| G1-16 | done | `Research/BatmobileGrab/PARTICLES_FEATURES.md` + MODLOG §"G1-16 · Particles by feature — done" (206 systems in 17 groups, 63 distinct names, 1433 emitters; 1290 colour boxes, 5 external refs) |
| G1-17 | done | `Research/BatmobileGrab/LIGHTS.md` + MODLOG §"G1-17 · Light values — done" (36 Batmobile-rig components: colour 129/129, intensity 74/74 lights; 67 colours from the component, 62 from `Default__*`, `FColor` read BGRA; the walker's 32-byte GuidProperty fix re-opened 1,786 truncated records) |
| G1-18 | done | `Research/BatmobileGrab/TYRES.md` (generated, `bmak_tyres.py --check`) + MODLOG §"G1-18 rework — done" (all four tyres Ø1.3652–1.3657 tread / Ø1.3711–1.3714 shoulder / 0.7314–0.7325 wide; tread = 2 × station radius to ≤0.6 mm; rim Ø1.0254 max-radial; 1.366 = physics radius ×2, 1.40 = wiki, 1.42 unsourced and its cause UNKNOWN; Disc 5.0 cm above ground, 394 radial / 338 vertical vertices outside the tyre; `stations.json` `tyre_width` mirrored L↔R; D-1 resolved: keep the PSKX) |
| G1-19 | done | `Research/BatmobileGrab/COCKPIT.md` + `COCKPIT.json` + `grab_cockpit.py --check` + MODLOG §"G1-19 · Cockpit and driver placement — done" / §"G1-19 rework — done" (seat = slot 11, 12,470 `Batmobile_Chassis` + 544 `CockPit_Mesh`; dash = slot 10, 14,136 `CockPit_Mesh` + 13,198 `Batmobile_Chassis`; `Driver` hip at (−0.0025, 0.8647, −1.0654), 24 mm above the cushion, socket up lateral; hip-to-liner 1.1014; centre screen 0.3188 × 0.1512 m; driver-facing panel 1,043 faces; hand box 4 faces; eye `derived (assumed input)` at 1.6547 / 1.7047 clears the crown by 0.211 / 0.151 m; only `Driver` is a required anchor) |
| G1-20 | done | `Research/BatmobileGrab/VARIANTS.md` (generated, `grab_variants.py --check`) + MODLOG §"G1-20 rework — done" (V2/MK2/Joker/Funhouse diffed: mesh LODs and bones, 65/55/64/63 sockets, 78/80/69/84 materials and 92/95/100/102 textures with every row closing as reference - missing + extra; `SimulationModel` identical in all four; 28/28/17 light-rig rows with 18/18/0 `MaterialType`; 10/10/5/10 gadgets and 8/8/2/8 projectile objects; Joker's tag diff is export indices, not values) |
| G1-21 | done | `Research/BatmobileGrab/MODES.md` + `grab_modes.py --check` (29/29, JSON and md both byte-compared) + MODLOG §"G1-21 · Modes and transformation values — done" (107 declared family fields, 46 serialised with per-package values, 61 carrying no value in the files; T-BM1's (9)/(3)/(2) now asserted as the serialised simulation scalars, the curve member extra; a missing tag is a CDO default, UNKNOWN — never 0) |
| G1-22 | done | `Research/BatmobileGrab/NATIVE_RELEVANCE.md` + `grab_native_relevance.py --check` (13/13, md compared) + MODLOG §"G1-22 rework — done" (140/140: 96 irrelevant = property decls, states, FaceFX; 44 relevant = 7 script-class exports (5 classes, parent inferred from the names) + 17 components (7 carry an unlabelled float at +40/+48, semantics UNKNOWN) + 20 `Function` exports, 5,562 B of undecoded bytecode (literals UNKNOWN); 768 two-byte + 17 six-byte rows ≤8 B named; 0 tags read, 96 native refs are pointers) |
| G1-23 | done | `Research/BatmobileGrab/FOOTAGE.md` + `grab_footage_gaps.py --check` (27/27, JSON and md both byte-compared) + MODLOG §"G1-23 · Footage and file answers — revised" (72 rows: 2 closed by file values — `HeatUpPerSecond` 0.0 means no per-second heat is configured and the bloom is the decoded `InaccuracyVsTime` curve 0/0.5/1.5/2.5 s → 0/0/1.5/3.0, the overheat mechanism otherwise UNKNOWN; 1 measured on five captures in `C:\Users\User\Videos\Captures` — airborne window 1.251/1.183/1.200 s on three ramp jumps, PTS-based because the clips are VFR, steering authority UNKNOWN; 53 VALUE-NATIVE, 8 WRONG-SCOPE, 5 UNDOCUMENTED, 2 NOT-IN-CLIP, 1 NATIVE plus the other four G1-14 natives listed out of scope; 20 file-answered quantities, 17 decoded) |
| G1X | done | `Tools/scripts/g1x_gate.py --check` (75 codes: 56 satisfied by G1 files, 19 proven absences) + MODLOG §"G1X · G1 exit gate — passed" (gate re-run: `grab_model.py check` schema 6, `grab_weapons`/`grab_anims`/`grab_lights --check` green; table of every feature code → file; sideswipe/ram targeting half added to `DAMAGE_RULES.md` §3.3.1 — impact numbers already decoded, `SideSwipeTargetsList`/`SideSwipeInSweetSpot`/`GetSideSwipeTarget` are runtime/native) |
| G2-10 | done | `Research/JC3Grab/WEAPONS.md` + `WEAPONS.jsonl` + `jc3weapons.py --check` (25/25 ids = 22 weapon ids + 3 `+_impact` blast ids, 26 spellings, 1 alias; 3 ADF classes: `WeaponTuning` 22 ids, `AutoAim` 3 per-id + 11 shared presets, `ForcePulseSettings` 9 ids; 161 sources, 4,054 decoded members, 67 `.ee` containers opened, 24 shared tunes, 197 files / 21,487,435 B extracted to `_JC3grab\weapons`) + MODLOG §"G2-10 · Vehicle weapon catalogue — done" (no `jc_explosions/` tree — blasts are `.ftunec` inside bundles; no overheat member anywhere; damage type is a part/health concept, not a weapon one) |
| G2-11 | done | `Research/JC3Grab/WEAPON_WIRING.md` + `WEAPON_WIRING.jsonl` + `jc3wiring.py --check` (53/53 armed entities, 88 weapon components: 57 `CBulletWeaponBase`, 25 `CMissileWeaponBase`, 6 `RPGFireLeach`; 62 driver slots + 19 gunner slots; 4 root pointers — `main_weapon` `851CAABE` and `mounted_weapon_2` `AC0BC788` recovered by Jenkins, second driver slot `00568A74` unnamed; max 2 driver weapons = medium/Bavarium tank; 7 unbound components; 22/88 weapons carry a type-4 `MountAttach` = all 19 gunner weapons + the corvette's driver cannon; the mounted M2 `w206` = 19 components / 5 chassis, outside G2-10's `06_vehicle` set) + MODLOG §"G2-11 · Weapon wiring — done" |
| G2-12 | done | `Research/JC3Grab/SIGNATURE_DIFF.md` + `SIGNATURE_DIFF.json` + `jc3sigdiff.py --check` (566→601 members: +167/−132, 108 same-role `signature/` replacements; graph 450→464 objects, 2 changed / 4 added subtrees / 1 removed after resolving ids through semantic paths; parts modules define the same 42 parts at the same indices, 19 models + 4 `model_swap` restyled, the `epe` instantiates 40 vs 41 by hood branch; 84 mesh pairs all same block count+AABB, +5 RPG projectile LODs; weapon `CMissileWeaponBase w618_sportsmuscle_missile` on `main_weapon`, 4 type-2 fire points each paired by position with its muzzle, all one `sportsmuscle_missile_muzzleflash.effc`; tune unguided `missile_turning_speed` 0, `magazine_size` −1, 1500 dmg / 300 m, blast 1100/500 in 8 m; embedded wtune 148 rows vs VFS 155; toc 468→498) + MODLOG §"G2-12 · Armed Serpente: civilian → signature_preorder diff — done" |
| G2-13 | done | `Research/JC3Grab/TURRET.md` + `TURRET.json` + `jc3turret.py --check` (8 entities / 106 constraints: medium tank turret ±179 at (0, 2.2812, 1.1382) about +Y and cannon -5..20 at (0, 2.5347, 0) about +X, hatch 0..130; Bavarium reuses both hinges and adds 12 skirts 0..30; APC/armoured jeep/technical mounts -15..50 / -25..50 / -10..45 behind unconstrained adapters, small tank -5..25 with its rack on a ragdoll; 92 fire points on 52 weapons name the moving parts via `id:80201E4D`/`id:5C19E7E0` — 47/47 pitch parts `Cannon`, 75 yaw = 18 `Turret` + 13 `Cannon` + 44 aircraft pods, 2 cross-entity entries on the cargo plane; `aim_part_constraints` = 85 rows in 17 of 78 modules, all suspension, 0 on the six turreted vehicles; `hinged_parts` 28/78, `rotating_parts` 22/78, both empty on tanks; aim = `STargetPoint` (0, 1, 0) + `autoaim_vehicle_mgun` 5..70 m, 0.03/0.05 rad, 6/16 deg sticky, `CanTargetVehicles` 0; tamper test caught and reverted) + MODLOG §"G2-13 · Turret and cannon mechanics — done" |
| G2-14 | done | `Research/JC3Grab/MOVING_PARTS.md` + `MOVING_PARTS.json` + `jc3moving.py --check` (67 behaviours over 233 vehicles; `vehicle_common` 53 rows = 14 doors / 25 hinged / 12 rotating / 1 fin / 1 spring, hinged carrying `target_position_variable` + `lod` + `use_target_position_as_angle` (only `SteeringFork` = 1), rotating carrying `rpm_variable` + rotoscope flags + 20 rpm/cycle, doors/fin/spring name-only; 38 behaviours have a row, 29 do not (turret/cannon, wheel, body, brakes, engine, windows, couplings), 37 proven on `CCar` and 30 not — `AirBrake` 3 parts on one `CAirPlane`; 11 of 25 hinged names used, 15 declared-unused incl. 12 spider legs; arrays: `door_parts` 224/56 modules `part_index` only, `hinged_parts` 148/28 `part_index` only, `rotating_parts` 47/22 with position/axis/blades/rpm; tamper test caught and reverted) + MODLOG §"G2-14 · Moving-part behaviours — done" |
| G2-15 | done | `Research/JC3Grab/DOORS.md` + `DOORS.json` + `jc3doors.py --check` (door = behaviour name in `all_door_part_properties` + bare `part_index` in `door_parts[]` + limited hinge in `.physicsc`; 224 door rows in 56 of 78 modules, 220 hinged, 4 with constraint -1: **60 X (transverse)**, 132 Y, 28 Z; donor doors ±Y 0..80 + hood +X 0..70, APC centre/rear doors ±Y 0..100/95 + front hatch and turret hatch +X 0..130, medium tank hatch +X 0..130, monorail 16 `MissileHatch` 0..150 about ±Z; monorail weapon `w614` fires from `InternalFirePosition_0…5` inside the bay and no non-`CPartProp` object names a hatch — trigger is code-side; entry paths `entry.driver`/`entry.driver.no.door` + `S_ENTER_DRIVER_VEHICLE`/`..._NO_DOOR_VEHICLE`: 21 both / 0 door-only / 4 no-door-only / 30 neither of 55 graphs, donor both but its container has 0 animation files; tamper test caught and reverted) + MODLOG §"G2-15 · Door-part animation — done" |
| G2-16 | done | `Research/JC3Grab/EMP.md` + `EMP.json` + `jc3emp.py --check` (both builds 794 members / 454 objects; 3 device parts, core = `Rotor` part 46 with a 6-blade +Z `rotating_parts[]` row; `CForcePulse` `EMP` on `truck_emp.ftune` at (0, 2.0356, 0.6992) — 100 player/AI damage in 25 m held at full radius, no duration/target class/disable member, stock car blast 500 in 5 m; only 3 unnamed flags + `emp_flatbed_table` differ from a plain pulse, whose refs are the table and one dangling id; `trigger.use_item` box at (0, 1.35, 2.396) + `entry.use_item` -> `S_STUNT_USE_ITEM_VEHICLE`, prompt `ui_activate_emp`, **no weapon component on the truck and no pointer from trigger to pulse**; both builds embed `explosion_emp_flatbed.effc`, mm250 drops pulse+tune and adds `epe_emp_powering_up` (`emp_active.effc`); all 9 oldtruck variants carry the 3 parts in the shared module, only the 2 EMP builds the props/pulse/trigger; weaponised EMP = `CEMPWeapon` `w702` (702/type 6, `FirePosition` (0, 0.13, -0.69), 3x `CBarrelSpin`, wall penetration) and `w503` (503/type 2, `fire_position_1`, `CTurretWeaponComponent`), neither tune has an EMP field and 0 of 88 fleet weapon components is a `CEMPWeapon`; **answer: the effect is an entity-level copy, not a weapon-slot copy**; tamper test caught and reverted) + MODLOG §"G2-16 · The EMP truck — done" |
| G2-17 | done | `Research/JC3Grab/FORCEPULSE.md` + `FORCEPULSE.json` + `jc3forcepulse.py --check` (307 pulses in all 232 vehicle `.ee` / 79 chassis, census agrees; **31 members** = 5 named + 26 Jenkins-hashed `id:*`; 23 explosion tunes with `PlayerDamage` 0..3000 / radius 1.5..50 m / `AIDamage` 0..1000 in 0..50 m; trigger = explosion named by the owner pointer `id:B5AE7986` on 293/307 - vehicle root -> own blast tune (CCar 126, CBoat 35, CHelicopter 23, CMotorBike 19, CAirPlane 18, CTrain 12), weapon component -> its own `jc_explosions/weapons/<id>.ftune` (CBulletWeaponBase 29, CMissileWeaponBase 25, CRPGFireLeachWeapon 6); horn refuted (178 `horn` effects, 0 horn/collision tune paths or pulse names); 14 unowned = UNKNOWN/Q-1 - 10 barrel blasts nesting under `CRigidObject` with an outgoing `id:73D4D940` -> `CEntityObject`, 2 zero-damage cargo pulses, the EMP pulse (G2-16), and the mm340 `BOMB_JEEP` pulse held by a `CGraphScriptGameObject` `id:65424AC6` (the only non-owner ref); unclear/absent semantics (`id:B5AE7986` name, firing moment, graph bytecode) recorded UNKNOWN; tamper test caught and reverted) + MODLOG §"G2-17 · `CForcePulse` — done"
| G2-18 | done | `Research/JC3Grab/INTERACTION.md` (jc3interact.py --check green) |
| G2-19 | done | `Research/JC3Grab/SEAT.md` + `SEAT.json` (jc3seat.py --check green) + MODLOG §"G2-19 · Driver seat and pose — done": `entry.driver`/34 interaction objects place Rico, `rico_base.afsmb`+`.asb` choose the pose (382 clips, 40 classes); candidate `sportsmuscle_f_l_seat` 0.855 m, 10 mm under the `Driver` hip) |
| G2-20 | done | `Research/JC3Grab/EJECT.md` + `EJECT.json` + `jc3eject.py --check` (4,832 exits / 232 graphs / 61 names, donor 26; every exit's members from a fixed 9-key set, **0 launch/velocity/impulse members** anywhere, `enabled` 1 and `interaction` 00000000 on all 4,832; of 104 graph classes only the velocity *condition* (4,057) and the car's `CForcePulse` move anything; module side has 1 launch-ish name in 232 entities (`TrainGlobal.crashing_impulse`) and one upward mechanism `arcade.turbo_jump` (145 land vehicles, `punch_speed_kph` 50/80, `top_speed_kph` 200, multipliers 15/12 & 30/25, cooldowns 5/2 s) which jumps the **car** and has no vertical-speed member; the donor splits exits at **5** - `default`/`to.fall` 0..5, `roll.out`/`moving.parachute` 5..999 - so `S_EXIT_VEHICLE_PARA` is *the fast exit*, present on 221/232 vehicles (125 cars, 35 boats, 23 helis, 19 jets, 19 bikes), and the two fast exits share a gate so the winner is code; 7 of 26 gated, 5 unconditional (pulled/pushed out, swim, upside down ×2); state string appears only on the exit and its `ExitObstructedCondition`, no vehicle state machine exists (0 `jc_statemachine/vehicles/`); BmAK eject = `EjectUpMove`/`EjectForwardMove`/`…VerticalMove`/`EjectToSpotMove` + `EjectUpDist` + `MaxEjectType` + `OverrideNextEject` + natives `ModifyEjectUpLoc`/`SetBatmobileExit`; **mapping: exit -> `exit.driver.moving.parachute`, launch -> UNKNOWN (Q1-EJ-A/B/C)**; per-exit conditions decoded for the donor only - the detail JSON sorts by id so nesting is unrecoverable; tamper test caught and reverted) + MODLOG §"G2-20 · Exit, bail-out and eject — done" |
| G2-21 | done | `Research/JC3Grab/TANKTURN.md` + `TANKTURN.json` + `jc3tankturn.py --check` (12 tank builds, 4 card modules member-identical: 0 tank-only / 0 non-tank-only members, 0 tank-only module types; 5 candidates refuted - `number_of_wheels` 6/8/8/4 shared with 114 non-tank builds, `wheels_friction_type=2` with 36, `is_rear_steered` 0 on all 145 player copies, only `is_all_wheel_steered=1` are 3 monster trucks, five-tuple shared by 27 non-tank builds; 262 tank-unique values fleet-wide, 0 in any driving module; 9 name matches all cosmetic skid / `CTrain` gauge, 0 in driving modules; all 12 tank builds declare `CCar`, containers data-only, wheel stations = `number_of_wheels`; turn-on-the-spot = **named omission**, pivot itself `UNKNOWN` (native code, Q-1 probe); tamper test caught and reverted) + MODLOG §"G2-21 · Turn-on-the-spot (tank pivot) — done" |
| G2-22 | done | `Research/JC3Grab/USAGES.md` + `USAGES.json` + `jc3usage.py --check` (6,045 modules / 232 caches; 225 `EffectAttachments` modules on **224 vehicles** - one plane carries two; 8 vehicles carry none; `ExtendedEffectUsages` = shared 627 B stub with `usages[]` **empty on all 232**; **12 usage names** in `usage_effects[]`: `HeadLights` 145, `EngineRunning` 69, `OnPartExplode` 33, `EngineSmoking` 23, `Explosion` 23, `EngineNitro` 18, `EngineTurboJump` 11, `OnPartReachedDamageState` 3, `Siren` 3, `OnPartBrokeOn` 2, `OnExploded` 2 + one **empty-string usage with hash `0xDEADBEEF`** (14); 346 rows / 885 effect links re-decoded from the `.vmodc` (caches drop the nesting), 0 mismatches; **flame-during-nitro candidate = `EngineNitro` (4197885156) -> `dynamic_nitrous` (14 vehicles) / `EngineNitro` (4)**, its `Usage` on 307 objects in 202/232 `.epe` graphs (`exhaust_upgrade_nitrous` 154, `engine_nitrous_sound` 41, `nitrous_active_sound` 35, `dynamic_exhaust_nitrous` 26); **0 usage names** match afterburner/boost/flame - the flame lives in effect names + 9 `*nitrous*.effc` paths / 275 containers; `.epe` `Usage` space 155 values / 12,576 objects with provenance 6 usage-name / 60 effect-name / 4 value-driven / **85 UNKNOWN**; donor module lists only `HeadLights` but its `.epe` attaches `exhaust_upgrade_nitrous*` under `EngineNitro` (51-value donor usage map for FX-1/T-17, 29 unnamed); 0 of 849,942 `.epe` strings name an `.effc`; tamper test caught and reverted) + MODLOG §"G2-22 · Effect usage vocabulary — done" |
| G2-23 | done | `Research/JC3Grab/USAGES.md` §6 "The nitro chain" + `USAGES.json` `nitro` block + `jc3usage.py --check` (donor `arcade.nitro_boost`: torque x2, grip x2, 15,000 N push, 0.2 s blend, +40 km/h; `_upgraded` 20,000 N / +80; the 5 `arcade.*` blocks on 145/232 vehicles; `EngineNitro` 4197885156 on `exhaust_upgrade_nitrous` (has `Sound`) + `exhaust_upgrade_nitrous2`; module effect `dynamic_nitrous` 397752766 on 14 vehicles vs the object's own unnamed `Effect` 3518298851 / 0xD1B4FAE3 on 28 objects / 17 vehicles, absent from every module `all_effects[]`; sound GUID `f74ea43b-a8ac-4548-ad27-b92fd40a516d` = 1 of the 45 donor `.fmod_guids`, carried by 202 objects / 172 vehicles (154 `exhaust_upgrade_nitrous`), = `vehicles.bank` `EVTS` ordinal 249 (195 B); samples by name 56 `jc3_veh_land_premium_nitro_start` / 150 `..._nitro_loop` / 355 `..._nitro_stop`, the same 0-based set test-060's `_apply_audio.py` swaps (asserted), 165 `..._nitro_jet_flame_loop` unused; tag -> button UNKNOWN; tamper test caught 249->250 and reverted) + MODLOG §"G2-23 · Nitro FX and audio carriers — done" |
| G2-24 | done | `Research/JC3Grab/JC3_AUDIO.md` + `JC3_AUDIO_EVENTS.json` + `jc3audio.py --check` (45 donor events: 758 B `.fmod_guids`, banks vehicles 24 / character 2 / effects 19, all 45 located as `EVTS` entries, 23 named by the `.epe`, **45/45 resolved to a tune index**; banks are FMOD **Designer/Ex** FEV v56 build 50, not Studio — corrects §70; vehicles.bank 257 events / 257 tunes / 1,674 sound instances / 649 waves / 649 FSB5 samples, 153,439,744 B, all PCM16 48 kHz, 22 looped; **event→tune is stored twice** — `TLNB` body offset 16 repeats the owning event GUID (257/257, 1:1) and the event body repeats the tune GUID at offset 32 (257/257); **tune→wave is not stored** (0/649 wave GUIDs in tune chunks or sound-instance bodies, `TLNT` tag 0, 0 `WAVS` GUID refs outside `WAVS`) → the sample inside a tune is picked by name/audition as test-060 did; `LandAudio` = 2 members `min_rpm` 1,000 / `max_rpm` 10,000, their runtime role UNKNOWN; w602/w603 tune 171 members, 0 audio, no `.ee` — sound on the tank (`Fire`/`ReloadStart`) + `weapons.bank`; w618/w619 own `.fmod_guids` (10/12, `weapons_preorder`/`effects`) + `fire*` Sound; horn 178 objects / 178 vehicles, radio 0/232; carrier provenance measured (nitrous2/tjump*/combined_wheel are donor graph objects without pinned GUIDs); `master.banklist` read (26 names / 434 B); census asserts the Working copy sha256 equals the archive entry; routes a+c possible, b not; tamper test caught and reverted) + MODLOG §"G2-24 · JC3 vehicle audio system — done" |
| G2-25 | done | `Research/JC3Grab/JC3_HUD_WEAPONS.md` + `JC3_HUD_WEAPONS.json` + `jc3hudwpn.py --check` (260 scripts; `InitVehicleWeapons` 9 args incl. `weapon_cooldown` 0..1 but **no heat** arg, `UpdateVehicleWeapons` 6; 2 slots `MCI_vehicle_weapons0/1`, `E_NUM_WEAPON_SLOTS` 7 is on-foot; 14 reticle shapes / 5 look states; lock-on = **one** `POI_TYPE_LOCK_ON_TARGET` 21 rotating 1.5 s + incoming `MCI_missile_locked` 0.5 s, link from `AutoAim` unwritten; `w609`/`w612`/`w613` envelopes - `w613` targets nothing; icon = `weapon_icons/<weapon_id>.ddsc`, 69 ids, wired id 614 missing; 0 heat params and 0 BmAK heat setters -> WPN-12 heat = stated absence both sides; 2 `TestConstructor` demos are the only call sites, entity->HUD native/UNKNOWN; tamper test caught and reverted) + MODLOG §"G2-25 · HUD vehicle-weapons API — done"
| G2-26 | done | `Research/JC3Grab/REBELDROP.md` + `REBELDROP.json` + `jc3rebeldrop.py --check` (vanilla `profile/item.onlinec` 196 items / `task.onlinec` 591 tasks from the base + patch layers; **`Item.Name` = 32-bit Jenkins hash of an entity leaf = the spawn binding**, 185/196 resolve to an `.ee` (the 11 that do not carry `UIType` 0), 80 vanilla vehicle drops all `Name == hash(UIImagePath)`, `UIName == Name`, `Type` 1 / `UIType` 3; `Item` = 128 B, **no cost field**, `RebelDropTimer` the only time; unlock = 87 `ItemReward` links in `task.onlinec` (donor drop from task 1361701860); the base's own `Item` has 25 members (no `DlcId`, `Type` at 8) and the patch's 26 (`DlcId` at 8), each file is read with the layout it declares, and the two agree on all 25 shared fields for 196/196 items (`DlcId` 0 throughout) with the 128 B stride proved by the `UIImagePath` pointers (196/196, 196/196, 232/232, 240/240); 4-byte `StringHash` values are masked to 32 bits; the mods carry no type table but the base root, so they read as base layout; mod V5.3 Plus adds 45 items (`Type` 1, `UIType` 3, timer 0, `BaseName` = `Name`) and rewrites 162 vs the base layer, tasks only reordered; recipe for "Batmobile" -> `hash_jenkins("v0300_car_kensington_sportsmuscle_batmobile")` = 443190071, that `.ee` not in the index yet (G2-27); which layout a type-table-less table loads with, enums/string hashes/timer unit UNKNOWN (G2-32, Q-1); tamper test caught and reverted) + MODLOG §"G2-26 · Rebel Drop data (RD-1 read half) — done"
| G2-27 | done | `Research/JC3Grab/STANDALONE.md` + `STANDALONE.json` (jc3standalone.py --check green) + MODLOG §"G2-27 · Standalone entity — done": **YES for the load, UNKNOWN for the hash** — 17 registration rows by key type (9 spawn tables key on a full path string, Rebel Drop on the 32-bit leaf hash); `global/entityregistry_gen.entityregc` is a tagged stream (leaf+hash+asset paths) holding 251/922 index leaves and 158/233 vehicles but 0/86 base spawn records, 163/169 debug and 13/21 DLC production records unregistered — incl. the retail playable `v0806_car_na_sportmech_01`, so a missing record does not stop a load; no shipped hash points at an unregistered leaf (Q-1 probe); the mod's 20 `.ee` are 20/20 vanilla paths with 0 `.toc`, inner names independent of the outer leaf; a standalone entity = one `.ee` (donor 10,737,057 B / 604 inner files) + one reference) |
| G2-28 | done | `Research/JC3Grab/DAMAGE_MODEL.md` + `DAMAGE_MODEL.json` + `damage_predict.py --check` (chain 7 steps, 7 with an UNKNOWN; 9 arms x 3 vehicles x 3 models = 81 hits-to-kill cells - donor 700 HP all channels 0@0, medium tank 2000 HP bullet 5000@99 explosion 250@50, build test-091 = the tank's profile in 6 values; tank shell = 2 hits H0/H2 vs 3 H1, shotgun 144/pull sets the ARM-1 gate at >=144 or 100, ARM-2's BmAK 24-hit ratio needs `max_health` 36,000 vs a fleet max of 4000; build's part table = donor's with exactly `Land_Wheel.instantly_damaged_by_bullets` 1->0; composition of armour+strength is in no file -> 3 named models + 3 Q-1 probes; tamper test caught and reverted) + MODLOG §"G2-28 · Damage model, complete, with a predicted hits-to-kill table — done"
| G2-29 | done | `Research/JC3Grab/TRAFFIC.md` + `TRAFFIC.json` + `jc3traffic.py --check` (11,751 data-table files / 7,719 MB scanned, **17 name the donor**; donor = **civilian traffic**: record in `settings/spawn_vehicle_defs.bin` 86 records / 8 keyed, 13 tags incl. `ambient`+`liberated`, satisfies 1 of 41 selectors in `global/global.blo` - `ambient,ground,car,liberated,-highend` -> `03_CivilianCarLiberatedProvince`, 10 `ai/bts` driver trees; other sites = Rebel Drop item `…_civilian_01_desc`, chop-shop task `chopshop_v0300_…`, 2 level `CVehicleRule`s, frontend list; only `civilian_01` is in the traffic table (`debug`/`preorder` in other tables); **replacing it = NPC-driven Batmobiles = lore break -> D-6 standalone**; pool key, record number fields, tag matcher native = UNKNOWN; tamper test caught and reverted)
| G2-30 | done | `Research/JC3Grab/PHYSICS_WRITE.md` + `PHYSICS_WRITE.json` + `jc3hkx.py write --check` (round trip **byte-identical** on both files, all 54 hulls re-emitted from their decoded values; a 16 B insert at data offset 0 moves all 430 objects and re-reads with 0 violations; one wheel hull scaled x1.6596 and the wheel slot holding a 704->1776 B hull block both re-read with 0 violations / 22 compounds / 112 instances; pointer slots must stay 0 (writing them cost 2,702 bytes while still passing the reader) and a grown child moves its 2 ancestors' AABBs; the face table fits **54/54** hulls (one 4-byte record per plane) behind an unnamed 0/16/32/48 B prefix (17/16/9/12), so brand-new hulls still need that block, as they do the extern-mesh quantization frame; standing gate `check --all` green 233/234 entities 18,865 hulls; tamper test caught and reverted) |
| G2-31 | done | `Research/JC3Grab/WATER.md` + `WATER.json` + `jc3water.py --check` (232 entities: `WaterInteraction.will_sink` 1 on **189** / 0 on 43; the 43 = **35 boats** with `BoatBuoyancy` (`base_buoyancy` 0.1/1/1.45, 6-9 pontoons) + **8 floaters** with the plain car `Buoyancy` (`v0200` APC 2, `v2603` sea scout 0.25, `v4500` floatplane 1.5); donor `will_sink` 1 `buoyancy` 2 `drag` 100 `radius` 0.55 `side_area` 1.85 `bottom_area` 3 `up_velocity_cap` 20, 1 hull element (`sportsmuscle_body`) - 10 sinkers ship an empty hull and still sink, so the mesh is not the switch; kill/stall is **fleet-wide**: all 232 share one `vehicle_common.vmodc` with `vehicle_damage.min/fatal_water_entry(_floating)_ms` 10/20/20/50 and `engine_shut_down_delay_s` 30 (car) / 5 (others), 0 overrides; **`drives underwater` has no member** - 38 water-ish paths in 52 module types, no drown/submerge/underwater member, only helicopter flight `dive_*` -> UNKNOWN/native; `Builds/test-091` water modules decoded and identical to the donor (1e-6) so D-8's lore route ships as-is; tamper test caught and reverted)
| G2-32 | done | `Research/JC3Grab/NAMES.md` + `jc3strings.py --check` (the car is **KERNER SERPENTE R**, a pair in `profile/online.stringlookup` keyed by `hash_jenkins(leaf)` = `D2B46B49`, 11 languages; blurb `7B942DF2`; the drop item carries `UIName` 3535039305 = the leaf hash, `UIImagePath` = the leaf, type/flag = SPORTS CAR / SPORTS CARS; task 1361701860 rewards it; icon `textures/ui/vehicle_icons/<leaf>.ddsc` 18,688 B; 45/45 vanilla vehicle items resolve name+icon; `ui/ui_localization` does NOT hold the name (only 2 DLC banners), the entity's own `.stringlookup` is one prompt `Get in Vehicle`/`A2B9F82C`, no `.gfx` names it, and there is no per-vehicle map icon - both stated as measured absences; tamper test caught and reverted) + MODLOG §"G2-32 · Names, icons and strings — done"
| G2-33 | done | `Research/JC3Grab/LIGHT_SYSTEM.md` + `LIGHT_SYSTEM.json` + `jc3lights.py --check` (**3,217 `VehicleDynamicLights` entries over 223 vehicles**, 25 members each, 9 behaviour values; the `.epe` side is a **different list** - 3,972 `SVehicleLight` objects / 404 preset names / no part binding, module `preset_id` = uint32 hash vs `.epe` string, no file joins them -> which one renders is UNKNOWN; 393 preset ids, **17 entries with `preset_id = 0`**, 34 presets with inconsistent value tuples -> the entry's own members are the numbers; `has_lights` is a flag not a gate (2,073 of 11,643 parts lit, 3 `part_index` misses, 27 name mismatches, 6 entries on unlit parts, 13 lit parts with no entry); `CarLight` 11,367 blocks all stride 12 B / uint16 / exactly 6 material slots, 1,085 B header layout from MODLOG §17, **parameter bytes UNKNOWN (§102d)**; **wheel-arch recipe**: 25 members each with a source and class - `HeadLight` from `VEHLT_HeadLight`, part `sportsmuscle_wheel_f_l` (26, `Land_Wheel`), colour 160,180,255 / 255, shape copied from the donor's shipped steady `HeadLight` point lamp `lights[2]`, `preset_id` 0, anchor `\|sportsmuscle_LOD1\|wheel_f_l\|Wheel_Frnt_Left_Disc\|Wheel_Frnt_Left_Disc_LIG`; both hashes are `rbmhdr.hash_jenkins`, **verified against all 3,217 shipped hash triples**; the wheel part ships `has_lights = 0` with no `CarLight` block and the anchor node is the §112 probe; LGT-2 = the same socket's `VEHLT_BattleModeLight`; tamper test caught and reverted) + MODLOG §"G2-33 · Light system consolidated — done" |
| G2-34 | done | `Research/JC3Grab/TETHER.md` (jc3tether.py --check green) |
| G2-35 | todo | capability to be found: `Research/specs/G2-35.md` - a triggered, non-damaging impulse/torque with target selection and a duration (ledger `T-RA1`, blocked); carrier `tmp/freebuff/reports/carrier-ram-and-dodge.md` section 8/9 |
| G2X | done | `Research/JC3Grab/G2X.md` + `G2X.json` + `Tools/scripts/g2x_gate.py --check` (75 codes **parsed from §1**, not typed: 67 carrier with labelled evidence — 7 numbers / 43 identifiers / 8 phrases / 9 short words — and 8 proven absence, all negative scans with a per-file anchor; the 24 G2 readers + the P0-2 census re-run 25/25 green; 7 codes decision-gated by D-2/D-3/D-5, all resolved, 0 open) + MODLOG §"G2X · G2 exit gate — passed" / §"G2X rework — done" |
| T-10 | done | `Working/Translation/T10_OPEN_ROWS.md` + `T10_OPEN_ROWS.json` + `Tools/scripts/t10_reopen.py --check` (16 rows: 5 superseded by T-11/T-12/T-15/T-17/T-18, 10 stay `out` each with a re-read proof file, T-HUD5 `blocked` for a narrower reason and naming T-11/B-05 as its unblockers; the proof scope is the 10 rows this card owns, the later-row census is printed not stored; ledger 105→122 rows then) + MODLOG §"T-10 · Re-open the `out` rows with the G2 evidence — done" + §"T-10 rework — done" |
| T-11 | done | `Working/Translation/T7_WEAPONS.md` + `t7_weapons_edits.json` + `Tools/scripts/t7_weapons.py --check` (14 rows = 12 WPN codes + the D-7 slot row and the D-3 decision record: 5 with a JC3 carrier, 6 named omissions, 3 blocked; 136 aspects with a class, 53 UNKNOWN; 3 edits + 6 structural + 6 withdrawn; carriers `w602`/`w603`/`w618`/`w619`, 2 driver slots; damage crosses as the 24:2 ratio to T-14; D-7 has no carrier for 11 weapons; D-3 resolved 2026-10-28 — JC3 lethality, no toggle, the riot suppressor a named omission) + MODLOG §"T-11 · Weapons translation — done" |
| T-12 | done | `Working/Translation/T8_PARTS.md` + `T8_PARTS.json` + `t12_parts.py --check` (15 rows = 11 cut parts + 4 no-part items: 12 with an animated joint, 4 with a shipped hinge, 3 static with a stored, check-asserted reason (P-02/P-05 translate, P-13 has no bone); the delivered JSON keeps `schema` 1 (`rows_schema` 2) so `bat_assemble.load_part_spec` still reads it; pivots re-derived through `bat_assemble.pivot_point`, max delta 1.3918e-05 m = BONES' own offset delta; turret +Y agrees with the tank hinge, canopy −X agrees with the donor hood but translates 72.5 cm, suppressor axis DISAGREES, Vulcan **6 turns / 2160° in 3.90 s** at 1229.5 °/s (a wrapped ±180° extent, not a limit), flaps 20/30° blade + 54.8° piston (both given, the child bone is labelled); 25 row-sequence pairs = 15 distinct clips; damage types from `PARTS_TABLE.dt`, land-first) + MODLOG §"T-12 · Moving-parts translation — done" |
| T-13 | done | `Working/Translation/T9_INTERACTION.md` + `t9_interaction.json` + `Tools/scripts/t9_interaction.py --check` (85 objects: 77 placed, every one 0.05-0.30 m from the nearest body triangle and outside the hull; 6 hijack objects dropped per D-9 = no; `Driver` socket 1; `interaction.seat.passenger1` UNKNOWN - one-seat cockpit; role anchors ray-cast on `body_lod1.rbm`: left/right cockpit side x -1.471/+1.462, front deck y 1.3606 at z -2.14, roof y 2.0811 at z -0.5; donor clearances 0.048/0.1474 m where G2-18 decoded them, 0.10 m chosen for the sides; tamper test caught and reverted) + MODLOG §"T-13 · Interaction translation — done" |
| T-14 | done | `Working/Translation/T10_DAMAGE.md` + `t10_damage_edits.json` + `Tools/scripts/t10_damage.py --check` (T-DM9 decided: option B - channels + `max_health` 36000, `invulnerable` stays 0; option A's `invulnerable` gate labelled unproven for a vehicle root; tank cannon 24/48/25 hits H0/H1/H2 vs the BmAK 24 with ARM-1 H0 and ARM-2 H1 printed as the two failing model cells, pending `Q1-DM-B`/`Q1-DM-A`; wheels at the fleet ceiling 400; ARM-5/ARM-6 named omissions; the stale `bullet_armor_strength` switch removed, `damage_audit.py` green, `max_health` switch pending the build; ledger T-DM1/T-DM9 `next`) + MODLOG §"T-14 · Damage and armour translation — done" + §"T-14 rework — done" |
| T-15 | done | `Working/Translation/T11_MODES.md` + `t11_variants.json` + `Tools/scripts/t11_modes.py --check` (D-2 hybrid: one row set, 15 rows = MOD-1 4 + MOD-2 11, compromise declared per row - `carried` 7 / `inside band` 1 / `omitted` 7; `BattleModeVSpeedCurve` 0->60, 600->40, 1200->30 and `TurningModeMaxSpeed` 600 cm/s = 21.6 km/h are named omissions, `ArmourModeDamageReduction` is 0 in every package, `BattleModeCamFOV` 60 sits inside the delivered 55-63 band, the battle lamps ride `HeadLight` because the fleet has no battle light behaviour, the Immobilizer is `blocked` for the disable it cannot carry (T-WP4), and BmAK's standard/boost torque curve is decoded from the G1 object stream; ledger 198 rows, `t_rows.py check` green) + MODLOG §"T-15 · Modes translation — done" + §"T-15 rework — done"; **D-2 reopened 2026-11-06**: this 15-row set is the one-hybrid record, and B-12's precondition 2 re-runs it as `pursuit` + `battle` sets |
| T-16 | done | `Working/Translation/T12_AUDIO.md` + `t12_audio_map.json` + `t12_audio.py --check` (53 rows = 45/45 donor events + 8 weapon/mode: 5 mapped with 5 chosen slots, 7 kept vanilla, 11 named omission, 1 remove, 29 blocked - 22 unnamed GUIDs by R4, A-01 pending Q-1 #8, A-04 unclippable at the shift slot, A-03/A-08/A-10/A-23 on D-10/D-8, W-08 on D-2; 34 slots decoded+measured, 22 gain-matched by measuring the written payload (0 chosen outside ±1 LU, 5 candidates outside and named: 3 gear-shift +3.5, nitro start -1.6, minigun endclick -16.8), 0 with an FSB5 loop field; event→tune stored 257/257 on both sides, tune→sample UNKNOWN, 24/45 tunes named; AUD-7 horn removed, AUD-3 named omission, nitro slots+spans proven by test-060 56/150/355) + MODLOG §"T-16 · Audio translation — done" + §"T-16 rework — done" |
| T-17 | done | `Working/Translation/T13_FX.md` + `t17_fx.json` + `Tools/scripts/t17_fx.py --check` (17 rows: **all 17 with a chosen carrier** - the 5 former named omissions T-FX9/12/13/16/20 were replaced by carriers + authoring plans, brief 8202, `tmp/freebuff/reports/apply-effects-rows.md`; FX-1…FX-4 4/4; 955 distinct fleet `.effc`, 85 on the donor `v0300` signature `.ee`, 8 sockets; rows in `T_ROWS.jsonl` as doc T-13; tamper 4/4 caught) + MODLOG §"T-17 · Effects translation — done" |
| T-18 | done | `Working/Translation/T14_LIGHTS.md` + `t14_lights.json` + `Tools/scripts/t18_lights.py --check` (28 rows = one per entry of the `Playable_Batmobile_SF` rig: 22 mapped, 6 named omissions; 18 distinct `SVehicleLight` targets = 11 of the donor's 21 shipped rows repointed at our sockets + the graph's unreferenced `Front_Secondary_Head` (T-L5's battle spot) + 6 custom `preset_id 0` entries (2 wheel arches + battle arch + 2 battle heads + boot); the two head clusters per side are the donor's `_01`/`_02` pairs; wheel arches close T-L4/T-LG4 through G2-33 §7 on new `sportsmuscle_wheel_f_*_arch` parts at parts 42/43; forensics rig + the two absent `HeadLight*c` flare sockets + the muzzle spot are the omissions; colours adopted from `LightColor`/255, cone/brightness reported not converted (no unit bridge); 21 donor rows / 22 objects / 20 presets resolve / 2 unreferenced; rows in `T_ROWS.jsonl` as doc T-14 (ledger 122→150); 3 tampers caught) + MODLOG §"T-18 · Lights translation completion — done" |
| T-19 | done | `Working/Translation/T6_HUD_CAMERA.md` §1a + `t19_hud.json` + `Tools/scripts/t19_hud.py --check` (T-HUD5 completed: 10 rows over 5/5 G2-25 elements, 6 map / 2 partial / 2 out, 12 proofs; T-HUD1…3 kept; heat = stated absence both sides, lock-on marker only, accuracy-frame scale UNKNOWN) + MODLOG §"T-19 · HUD translation — done" |
| T-20 | done | `Working/Translation/T15_WORLD.md` + `t15_world.json` + `Tools/scripts/t15_world.py --check` (19 rows, 8/8 WLD codes: 5 `next`, 6 `keep`, 3 `epe`, 3 `blocked`, 2 `out`; `BaseName` = `hash_jenkins(<family prefix>)` on 45/45 drops; the new leaf name hash 443190071 resolves in 0/11 languages, so the name and blurb pairs are `blocked` for lack of a `.stringlookup` writer; ledger 164→183, `t_rows.py check` green) + MODLOG §"T-20 · World translation — done" |
| T-21 | done | `Working/Appearance/APPEARANCE_PLAN.md` + `appearance_plan.json` + `Tools/scripts/appearance_plan.py --check` (172/172 classified: 23 bake POL-2, 8 route, 141 drop, 0 unclassified; POL-1 interior 6 slots all samplers bound; POL-2 bake is the only build work; skins per D-5) + MODLOG §"T-21 · Appearance completion — done" |
| T-22 | REOPENED 2026-11-07 (drivable asset decoded) | **`Research/BatmobileGrab/COLLISION_WHERE.md`** (G3-16): `Physics.Batmobile_V3_Physics` (BmGame 158266) = **2 bodies / 3 boxes / 1 constraint**, reached from `SVehicleMesh` @824; chassis boxes 690.305x374.536x207.5 + 679.585x345.688x103.5 (TM identity), pod 166.177x189.365x39.8 at 4 deg; the built set carries 62 donor bodies with body 0's single hull rewritten, so **2 shapes are missing**; plan `Working/Translation/T22_REOPEN.md` + `Tools/scripts/t22_reopen.py --check` (10/10 oracles); the 2026-10-28 close stays as history - `Working/Translation/t16_collision.json` + `Tools/scripts/t22_collision.py --check` (7 donor hull slots from the 11 driveable BmAK boxes: body 1, 2 doors, 4 wheels; 21 boxes are wreck-only and the 11 T-8 parts have no slot; 54 hulls, one per part, convex radius 0.01 m x k; wheel k 1.660052 = tyre 1.3654 m / 0.8225 m; body hull 3.495x2.032x6.167 m at k 1.676259; 38/42 parts carry `has_world_collision_shape`, the 4 wheels 0 with body -1; 0 station quads in the file, stations untouched; rows T-P3/T-CO2 `next`, T-CO3 `keep`; 4/4 tamper tests) |
| T-24 | todo | card added by `tmp/freebuff/reports/apply-light-rows.md` - the eight flare rows T-L25/T-L26/T-L27/T-L29/T-L31…T-L34 are `next` only because this card's carrier (an `.effc` spawned at a socket) is named; until it runs they are glow-only (the byte-copied `CarLight` lens + `volumetric_mode` halo) |
| T-25 | todo | card added by `tmp/freebuff/reports/apply-light-rows.md` - T-L10 and T-L21…T-L23 are `next` as `preset_id 0` lamp rows; the state/pulse that switches them (muzzle fire, `bForensicsLightActive`) has no JC3 member until this card shows a carrier |
| T-26 | todo | card added by `tmp/freebuff/reports/apply-suspension-rows.md` - T-R2 keeps 0.1 / 0.1 because `RVehicleSimBatmobile.Drag` @16, `DragNoLoad` @20 and `DriftDrag` @712 are declared by the class and carry no decoded value |
| B-22 | todo | card in §8 + `Research/specs/B-22.md`; `tmp/freebuff/reports/suspension-unit-bridge.md` §7/§9 - `BMRearWheelMaxDroop` 100 cm and `SuspensionTravelUp` 30 cm have no member; `max_length_offset` 0.30 is the only carrier, 0 on all 166 fleet cars |
| B-23 | todo | card in §8 + `Research/specs/B-23.md`; `tmp/freebuff/reports/suspension-unit-bridge.md` §7/§9 - 750 / 20 / 5 have no per-mode or stationary member; 750 is a 172% rest sag on the 0.40 m travel |
| T-S6-bridge | done | `tmp/freebuff/reports/apply-suspension-rows.md` + `tmp/freebuff/reports/suspension-unit-bridge.md` (`t_s6_bridge.py --check` 14/14) + `tmp/freebuff/reports/keep-audit-suspension-and-mass.md`: T-S6 `blocked` -> `next` (length 0.40 m, strength 13.500 s^-2, fit +5.8% / -5.5%, damping 1/2, front bias -0.10), T-S5 replaced 0.2/0.2 with 0.1/0.05, T-S4/T-M3/T-R2 restated with the member that does (not) exist, T-R3 LORE-EXACT; pins 14+4 -> 13+4 = **17 of 216**, `t_rows.py check` / `status_audit.py --check` / `t_blocked.py --check` all green |
| T-23 | done | `Working/Translation/BUILD_BATCHES.md` + `build_batches.json` (schema 2) + `Tools/scripts/t23_closeout.py --check` - one command, it runs the three sibling checks itself (gate TX: 75/75 §1 codes mapped, 0 unmapped - **51 carried / 9 named omission / 5 blocked (`AUD-1`, `AUD-4`, `HUD-2`, `WPN-4`, `WPN-5`) / 10 documented with no disposition (`ANI-2`…`ANI-9`, `CAM-1`, `HUD-1`, counted, not called carried)**; 198 ledger rows `edit 16 next 40 keep 60 epe 26 blocked 13 out 36 superseded 7`; rows assumed 1 of 180 and it is the signed-off T-E5; D-1…D-10 10/10 answered; 14 artefacts = **12 payloads + 2 records** over the 14 B steps, **3 with no step** (`t19_hud.json` a payload, `T10_OPEN_ROWS.json` and `damage_switches.json` records); 34 document anchors, 27 codes touch one) + `bmak_coverage.py --check` (777 G1 feature rows -> 34 T rows, 0 unassigned) + MODLOG §"T-23 · Ledger close-out and build batches — done" + §"T-23 rework — done" |
| G3-01 | done (geometry open -> G3-01b) | `Research/BatmobileGrab/COLLISION.md` + `grab_collision.py --check` ok (numpy+pillow); re-verified Startup 7530/82147/82148/169640/171103/171104/154788 and BmGame 10923/175973/175974/158266/169748/169749 |
| G3-01b | partial | `COLLISION_GEOM.md` + `grab_collision_geom.py --check` ok; chassis 2 boxes + weapons box decoded (bytes re-verified), convex sets: element 0 of 43 / 13 only; open: elements 1..N, box rotations, 0x4C tag, extents convention, frame, active mesh; was: AggGeom of the two collision StaticMeshes + Batmobile_V3_Physics bodies; cylinder field names; active mesh per mode |
| G3-01c | done | `Research/BatmobileGrab/COLLISION_CONVEX.md` + `grab_collision_convex.py --check` OK; independently re-parsed (both payloads walk to end-9 zero bytes, 56/56 boxes); pursuit 13 hulls 6.71x3.18x2.24 m, battle 43 hulls 6.95x4.93x2.95 m; open: 7th array/trailer semantics, frame link |
| G3-02 | done (12 UNKNOWN open) | `Research/BatmobileGrab/CONTROLS.md` + `grab_controls.py --check` ok; reviewed 10/10 tokens; open: effective merged map, pursuit<->battle input, consumer bytecode, keyboard driving |
| G3-02b | done (5/5 UNKNOWN; next: native) | `Research/BatmobileGrab/CONTROLS_CONSUMERS.md` + `grab_controls_consumers.py --check` ok; anchors re-read; LT->mode and LB->exit are not in script (ToggleBattleMode has no script caller) - native side or runtime next |
| G3-02c | done (5/5 UNKNOWN; switch located) | `Research/BatmobileGrab/CONTROLS_NATIVE.md` + `grab_controls_native.py --check` ok; re-verified: TryToChangeMode impl 0x140063e90 called with BattleMode 0x240 / PursuitMode 0x241 from DrivingPlayerMove 0x140254560, +-0.707 compares; input->switch link needs runtime (G3-02d?) |
| G3-02d | done (X/Y not sampled) | bmak_runtime_sampler.py + runtime/samples-*.jsonl: LT battle/pursuit, LB exit+enter, A eject exit, B immobilizer on auto-tagged enemy CONFIRMED live; X barrage + Y boost = user + config; open: EM ejection part, barrage runtime trace |
| G3-03 | done | `Research/BatmobileGrab/CONFIG.md` + `grab_config.py --check` OK (1,894 rows re-read); reviewed |
| G3-04 | partial | `Research/BatmobileGrab/COLOUR.md` + `grab_colour.py --check` OK; chain + Diffuse_Adjust [2.2,2,2] decoded; colour logic in 12 material functions -> G3-04b |
| G3-04b | partial (dead end on disk) | `COLOUR_FUNCTIONS.md`: function expression graphs are not in the cooked bytes (all FunctionExpressions slots zero) |
| G3-04c | done | `Research/BatmobileGrab/COLOUR_PARAMS.md` + `grab_colour_params.py --check` OK: body-slot MIC #767 params (BaseColour [0.0258,0.0258,0.03], Diffuse_Adjust [2.2,2,2]) by owner; combine rule UNKNOWN (graphs stripped) |
| G3-05 | done | `Research/BatmobileGrab/PACKAGES_G305.md` + `grab_packages_g305.py --check` OK (20 pkgs, 22/22); open: values of 97 RVehicleBatmobile defaults + 48 remote-gadget params (U-1/U-2) |
| G3-06 | done | `Research/BatmobileGrab/REMAINDER.md` + `grab_remainder.py --check` OK: 925/925; the 97 Startup property objects are descriptors, values UNKNOWN on disk (readable at runtime via the G3-02d sampler) |
| G3-07 | open | (research reset 2026-11-02; see §6b) |
| G3-08 | done (caveat: name-level verdicts) | `Research/JC3Grab/INPUT.md` + `jc3_input.py --check` OK (474/474); keymap is global (settings/keymap_*.bin), no entity references it; BmAK battle/eject/sonar/tag/barrage/pivot have no JC3 action |
| G3-09 | partial | `Research/JC3Grab/COLOUR.md` + `jc3_colour.py --check` OK 12/12; palette decoded (JC3 Black = 0.2); dynamic tint semantics + tonemap need runtime (G3-07) |
| G3-10 | partial (static done) | `Research/JC3Grab/PHYSICS_ROLES.md` + `jc3_physics_roles.py --check` OK; part<->body ids decoded; open: 2nd raycast id space, static-compound refs, constraint joins, body entries, mass props; runtime part needs G3-07 |
| G3-12 | done (correction noted) | `Research/JC3Grab/DECODE_DEPTH.md` + `decode_depth.py --check` OK 14/14: 441 FULL / 121 PARTIAL / 4 NAMED-ONLY; extern-mesh + dynamic-compound trees are decoded in bm_colmesh.py (audit missed it); mass props + 11 constraints undecoded |
| G3-01d | done | `COLLISION_FRAME.md` (7/7): pursuit hull inside render bounds, min +0.22 cm, +5 cm X offset, no fitting |
| G3-01e | done | `COLLISION_SELECTOR.md` + `grab_collision_selector.py --check` OK: mode 0 none / 1 pursuit mesh / 2 battle mesh (Batman-vs-car, attached only when Batman is outside); matches live samples |
| G3-10b | partial | `PHYSICS_ROLES2.md`: constraint joins/pivots/limits, 56 masses, fleet 5/5 |
| G3-02e | partial | `CONTROLS_NATIVE2.md`: dispatch by FName/ProcessEvent; 0.707 = [Pawn.Mesh+0xd8]; no native input->exit route |
| G3-11b | done | `Working/Translation/LEDGER_AUDIT2.md` + `ledger_audit2.py --check` OK: 72 rows re-checked, 19 changed, 5 REFUTED |
| G3-12b | done (UNKNOWN ranges) | `DECODE_DEPTH2.md`: .ddsc 71 FULL / 45 PARTIAL, .pfxc 4 PARTIAL |
| G3-09b | queued (Freebuff) | task 2017 |
| G3-05b | done | `Research/BatmobileGrab/SKINS.md` + `grab_skins.py --check` OK (4 pkgs, 248 sockets, 84 slots) |
| G3-01e-fix | done (adjudicated) | `COLLISION_SELECTOR2.md`: table unchanged; guard refs ArmouredMode/BatmobileWinch/FakeRoadCollisionStatic present (object refs), its offset labels partly wrong; WinchPullType/IsVehicleAsleep unconfirmed |
| G3-06b | done | `CLASS_DEFAULTS.md`: 93 + 181 default tags, all named by layout offset |
| G3-06c | done | `Research/BatmobileGrab/NATIVE_TRIAGE.md` + `Tools/scripts/bmak_native_triage.py --check` OK: 925 untagged = 768 stubs + 157 remainder (152 native + 5 closes); 15 read, 8 derived / 7 UNKNOWN, none carries a vehicle number |
| G3-06d | todo | damage component: 4 `RVisualRepresentation`-free `RVisualDamageComponent` exports (drivable package + 2 others), ARM-2/ARM-3; evidence `NATIVE_TRIAGE.md` §4 |
| G3-06e | todo | vehicle audio objects: 5 (`AkVehicleSound` x4, `AkDialogueComponent` x1), AUD-*; deps G3-14 |
| G3-06f | todo | interaction / threat / physics components: 17 (`RInteractionComponent` 15, `CylinderComponent` 1, `RVehicleThreatComponent` 1), DIM-4; deps G3-10 |
| G3-06g | todo | weapon-adjacent remainder: 4 (`RJokerMissileTarget`, launcher PFX and mesh components), WPN-3; deps T-11 |
| G3-06h | todo | parts / light / particle components: 6 (`PointLightComponent`, `ParticleSystemComponent`, `SkeletalMeshComponent`), APP-5; deps T-12, T-18 |
| G3-07a | done | `RUNTIME_LAYOUT.md` 8/8 oracles: part node, body-slot array, slot record, shape decoded; root global / transform-vs-AABB / render / resources UNKNOWN |
| G3-07b | queued (Freebuff) | task 2030: close G3-07a UNKNOWNs |
| G3-02f | done | `SAMPLER_FIELDS2.md`: 44 observables (Y +781, launcher targets +2400, booster, eject modifier +786); 3 UNKNOWN incl. X backing field |
| G3-10c | partial | `PHYSICS_ROLES3.md`: cinfo has no partner body; body entries + mass link decoded; inertia UNKNOWN |
| G3-10d | refuted in review | `PHYSICS_ROLES4.md`: 'partner = body 0' REFUTED (65 records impossible); script has leftovers; inertia UNKNOWN |
| G3-10g | done (UNKNOWN) | `PHYSICS_ROLES6.md`: 5 partner candidates scored, none holds (best 51%) |
| G3-10h | done | bodyB = 0x7fffffff 'no body' marker (494/494); record names one body; runtime binding open |
| G3-14 | done | `AUDIO_BANKS.md`: all 29 referenced banks present (BmGame/Startup/StartupPatch AkBank exports); T-AU3/T-AU5 block refuted |
| G3-19 | done | `DECODE_DEPTH3.md` PASS: 1/4 FULL, 3/4 FULL except one named block payload each |
| G3-20 | partial (keyword pass) | `LEDGER_G3.md`: 180 OPEN / 2 CORRECTED / 16 SUPPLIED by keyword, unverified |
| G3-20b | partial (verified) | `LEDGER_G3B.md`: 105 rows: 6 hold / 3 wrong value / 96 open (values from pre-reset files); first-pass 18: 6 hold, 9 wrong card, 3 wrong value |
| G3-20d | done | `LEDGER_SOURCES.md`: 7 pre-reset files all script-made, checks green; 96 open rows -> 69 re-derivable / 27 not; paint composite = assumed |
| G3-20c | done (verified) | `LEDGER_G3C.md`: 93 rows: 25 quoted / 68 open |
| G3-21 | done (snapshot) | `Research/RESET_STATUS.md`: R-1..R-6 all PARTIAL; re-run reset_status.py --write after the queue drains |
| G3-10e | done (verified) | `PHYSICS_LIMITS.md`: hinge limits +0x0FC/+0x100 rad, 419 hinges / 71 ragdolls / 51 files |
| G3-09c | done (verified) | `COLOUR_NATIVE2.md`: the 15 constants are vertex-element declarations, not a colour block; review queued |
| G3-02g | done | `BINDINGS_MERGED.md`: merge rule from the install (append / '-' removes whole-struct match / '.' appends) + effective gamepad table |
| G3-02h | done | only C -> ToggleDrivingCamera is vehicle-specific on keyboard; driving keys only via generic axes (consumers UNKNOWN) |
| G3-02i | done | `DRIVINGMODE.md`: 16 bodies / 51 calls; eject scripted (DriverLeave -> binds -> cockpit -> SetRBLinearVelocity); mode toggle by state name |
| G3-12c | done | PARTIAL ranked; .ddsc 116/116 FULL (confirms G3-12d); left: .epe round trip, .physicsc extents |
| G3-12d | done | `DECODE_DEPTH6.md`: .ddsc 116/116 FULL (84-B table = streamed-mip records), .pfxc 4/4 accounted |
| G3-11c | done (label corrected) | `MISSING_ROWS.md`: ALB-2 = literal gain 4 + guessed combine (BaseColour x Diffuse_Adjust, operator UNKNOWN); T-13 band 0.05-0.30 m literal |
| G3-11d | done | 5 collision rows: JC3 targets match; BmAK sources wrong - T-CO2 used a wreck wheel box (316 cm), not the drivable chassis (690 x 375 x 208 cm) |
| G3-10f | done | `PHYSICS_ROLES5.md`: one ray id space (indexes the body-entry array, 42/42); static-compound refs decoded |
| G3-21b | queued (Freebuff, brief) | task 9001: refresh reset status |
| G3-02j | done | eject velocity call = (0,0,0) on the CAR mesh (a stop); Batman's launch = TriggerSpecialMove |
| G3-04d | partial | shader caches decoded, no RDEF (0/40,299) -> cb0[n] unnamed; 6,934 uniform records remain |
| G3-09d | partial (tint parameter located, write path open) | `Research/JC3Grab/TINT.md` + `python Tools/scripts/jc3_tint.py --check` OK (9/9): the paint tint is the entity graph's inlined `Palette.tints[i].tint_r` (76 of 232 entity graphs, 26 modules, 401 distinct rgbs), oracle = disjoint `tint_r` sets for oldjeep vs armoredtruck; `CarPaintMM.dynamic float4[0]` is constant (0.14,0.19,0.25,1) across all 43 paint blocks with 0 palette rgbs in it, so the .rbm does not hold the per-car paint; `cb6[0..2]` = 0/16/32; what writes palette->`cb6` is UNKNOWN |
| G3-04e | partial (slots named, colour chain open) | `Research/JC3Grab/CB0_SLOTS.md` + `python Tools/scripts/jc3_cb0_slots.py --check` OK (10/10): the paint slots are `cb2`/`cb6`/`cb7` (+`cb8` RBIInfo), never `cb0`; 12/12 paint-family headers agree on every name/offset/size; the `.rbm` `CarPaintMM` payload is the cbuffer itself (288+28 / 76 / 20 B over 399 blocks in 163 files); tint = `cb6[0..2]` at 0/16/32; the 6,943 Arkham records name 0 slots (32 B entries, no slot field, 0/14 name overlap) |
| G3-12e | done | .epe round trip: 2,189 B canonical, 75 floats change <= 7 ulp |
| G3-11 | done (caveats) | `Working/Translation/LEDGER_AUDIT.md` + `ledger_audit.py --check` OK: value-verified 48/198, string-only 44, guessed 7, not translated 106; ledger lacks ALB-2 + T-13 rows; collision rows need re-check with jc3hkx |
| B-02 | done | `Working/Appearance/build_parts/parts_manifest.json` + `Working/Translation/T8_PARTS.md` + MODLOG §"B-02 · Part split — done" + §"B-02 polish — done" + `python Tools/scripts/parts_manifest_check.py --check` (14/14 assertions re-derived from the files, 5/5 tampers caught; silhouette 99.97 % **net** = gross holes 0.309 %, 0 lost faces, 4791/4915 KB; pivots re-derived from `BONES.json` 4.9e-07 m) |
| B-01 | done | `Builds/bm-001/receipt.json` + `python Tools/scripts/bm_build.py --tag bm-001 --check` + MODLOG §"B-01 · Build scaffold — done" + §"B-01 polish — done" (identity control: bm-001 `.ee` 10,737,057 B `6AB8275F…` and `.toc` 50,643 B `444ED479…` byte-identical to test-091's, 506 `.toc` records, 0 edit rows; R9 measured on the build — model non-vanilla 4,657.6 of 4,915 KB, texture resident 5,855.8 of 7,065 KB; the applier path proved on a deleted probe build — `.ee` +1 byte, aafdiff exactly 1 module; 4/4 tampers caught) |
| B-03 | done | `Working/Appearance/build_lights/lights_manifest.json` + `python Tools/scripts/spec_check.py --lights Working/Appearance/build_lights` + MODLOG §"B-03 · Emissive `CarLight` blocks and light parts — done" + §"B-03 rework — done" (8 lamp parts / 24 RBMs, 4,576 Emissive faces cut into head lamps, 4 arch lamps and 2 tail strips, vertices pivot-relative per parent part (`pivot_m` + `part_index` 42/43 recorded for B-04), 21 T-18 rows (19 mapped, 2 unmapped), 16 sockets (6 with a T-18 LightColor), 3 LODs per lamp, 24/24 CarLight blocks byte-identical to the cloned header, 288.6 KB lights / net 4,899.6 of 4,915 KB, 3 rig lamps with no faces measured; 16/16 script checks; tampers: header byte, manifest count and a stray RBM all caught) |
| B-10 | REOPENED 2026-11-07 (its Done rule was the render bbox) | the delivered 5-hull set was fitted to DIM-1's render bbox, which is 25 cm narrower / 20 cm taller than the drivable chassis box (B-10d); `COLLISION_WHERE.md` + B-10e make the BmAK asset and its decoded TMs the target, so the card re-runs with the chassis/pod shapes and the 5 cm gate on those; the 3-shape gap and the 0-free-slot question are `Working/Translation/T22_REOPEN.md`; 2026-11-06 shipped file stays as history - `Working/Collision/batmobile.physicsc` + `bm_collision.json` + `BM_COLLISION.md` + `Tools/scripts/bm_collision.py --check` + `jc3hkx.py check --all --file Working/Collision/batmobile.physicsc --against <donor>` (5 hulls written over the donor's 54: body re-scaled **per axis** to DIM-1 (`3.495 x 2.271 x 7.025` m; T-22's uniform k 1.676259 fits *inside* at 2.032 / 6.167 and leaves 0.239 / 0.858 m, so the linear map is per-axis with every plane re-derived, support gap 2.93e-07 m, radius 0.016763) + 4 wheel hulls at T-22's k 1.660052 (`0.491 x 1.3654 x 1.2986` m, radius 0.016601, centred on the wheel's own pivot); 2 door slots copied byte-identical (B-04 step 1 removes `door_f_l`/`door_f_r`); 3 ancestor compounds re-boxed; 430 objects / 22 compounds / 112 instances unchanged; 483 ranges / 1,926 B differ, same file size; **hull union vs body bbox max abs dev 0.0000 m <= 0.05 m**; stations 0 -> 0 and `hknpPhysicsSystemData` byte-identical (R3); standing gate 233/234 entities + the built file 54/54 convex, 22/22 AABB unions exact; 3/3 tampers caught and reverted, and the uniform-k control fails the same check at 0.8583 m) |
| Collision-reopen | done | `Working/Translation/T22_REOPEN.md` + `T22_REOPEN.json` + `Tools/scripts/t22_reopen.py --write/--check` (10/10 oracles: 2 bodies / 3 boxes / 1 constraint, chassis TM identity 0.0, pod 4.000 deg, 62 built bodies with 1 rewritten body hull and 2 shapes missing, 0 free hull slots of 54 with 14 unbound, axis map best residual 25.036 cm vs second 147.436 cm) + §8 B-10 / §9 T-22 REOPENED + ledger rows T-P3/T-CO1/T-CO2/T-CO3 re-pinned on the asset + `t_blocked.py --write`/`--check` and `status_audit.py --write`/`--check` green (task 8203) |
| B-10b | built, Q pending | `Tools/scripts/bm_colmesh.py` (RC step 3a2) + MODLOG §"B-10b" (new card, Q re-test 4 + user decision "B": body world collision = Batmobile body LOD2, 6,269 t, own tree + geometries + refit dynamic trees; above the fleet's 2,626-t max) |
| B-10c | built, Q pending | `Tools/scripts/bm_colhull.py` (RC step 3a3) + MODLOG §"Q re-test 5 result" (new card: body 0 = world collision is a convex polytope, not the extern mesh; Batmobile convex hull 95 v / 186 f, 54/54 donor hulls re-encode) |
| B-04 | done | `Working/Parts/bm_vehicle_parts.json` + `Builds/bm-002/receipt.json` + `python Tools/scripts/bm_parts.py --check` + `python Tools/scripts/jc3parts.py check` + `python Tools/scripts/jc3adf.py dump <built module> --paths` + MODLOG §"B-04 · Parts module — done" (42 → 59 parts: `door_f_l`/`door_f_r` removed with their `door_parts` entries and the body's children refs, indices 1/2 freed, 4 orphans (`door_f_*_window`, `*_mirror`) re-parented to the body; 19 new parts = 11 B-02 cut parts + 8 B-03 lamps with pivots/parents/models from the two manifests, damage types and behaviours from T-12, `has_lights` 1 on the 8 lamps, `is_deformable` 0, collision ids -1/-1 (T-22's hull-less pattern, 599/11,643 fleet parts); behaviour rows `hinged_parts` 4 (the AirBrake flaps), `rotating_parts` 1 (Vulcan: blades 1, axis T-12 P-03, position = its own `parent_space_offset`, proven against 11/11 shipped rotating rows), `door_parts` = [25] only, `aim_part_constraints` 0 (G2-13: all suspension); 5 omissions with the reason kept (jet axis UNKNOWN, canopy/bay rows name no part, steering yoke); module 29,886 → 39,278 B through the patched `ConvertAdf` (+9,392 B, unchanged round trip 2802/2802 rows and 42/42 parts), packed with `eetoc --internal sportsmuscle_vehicle_parts.vmodc` → `.toc` record offset 16,400,188 / 39,278 B; 59/59 part models resolve, 98 new files (79 `.rbm` + 19 `.lod`) registered in `@files.xml`, `aafdiff` vs bm-001 exactly 100 files; 4/4 tampers caught and reverted) |
| B-05 | done | `Working/Entity/bm_epe_edits.json` + `Builds/bm-005/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.epe` + `python Tools/scripts/bm_entity.py --check` + MODLOG §"B-05 · Entity graph (`.epe`) — done" + §"B-05 rework — intended change" (base **bm-009** 416 object elements = 415 classed + classless root / 43 classes → 467 = **466 classed + classless root / 46 classes**, `.epe` 124,488 B `f4abe91da0bc3ce3…`, `--write` deterministic); **Done 1** `ConvertProperty` round trip byte-identical (`--e` → 502,109 B XML, `--i` → same sha, second `--e` → `cmp` identical); **Done 2** 41 named weapon/light objects with **0** `name_hash` mismatches, 4 `attach.vehicle` points binding **two** B-04 part names each (the donor's third ref `weapon_anchor` has no B-04 equivalent and is omitted, in `declared[]`), 19/19 B-04 part names present in the 39,278 B module **read from the module's bytes by `--check`**; **Done 3** `467 = 416 + 51` by node-path diff (definitional; the object-for-object plan comparison is the guard; 27 rows, 24 nested); contents: 4 `CBulletWeaponBase` (w602 canon → root `id:851CAABE`, w603 mgun → `id:00568A74`, w618 missile 2 points, w618 emp 1 point; `weapon_type` **2** derived from the APC template and `SIGNATURE_DIFF`'s donor w618, where the first build had typed 1) + 9 `SWeaponPoint`, 28 lights (22 shipped + **6** T-18 custom cloned from `Front_Left_Point`; their 11 positional slots, the `A04C3B1E` matrix and `preset_id` are inherited and declared, so all six sit at that lamp until B-07's module anchor binds them), **15/84** interaction transforms (8 `PointNode` + 7 `Trigger`, the only objects with a *named* `world`; **69** rows skipped = 60 entries/exits/transitions with an unnamed matrix member `id:999864F0`/`id:C8F5DB5C` (UNKNOWN) + 9 transitions whose class+name matches 3 objects), **0** `CPartProp` by declared narrowing (spec L-3: 6 props / 42 parts shipped, no prop carries a behaviour), root `health` 100 / `invulnerable` 0 / `damage` 1928726201 and `bat_base.ctune` ×1 preserved; tamper test (an `attach.vehicle` part ref changed back to `weapon_anchor`, re-imported) **caught twice** (plan diff + the new dangling arm), restored, re-check PASS; limits carried: the two `w618` components are **unbound** (`unbound[]`: no free root slot exists, T-11 has no WPN-3 carrier, T-WP4 blocked) so the missiles cannot fire, components are **APC** clones (32 `w206`-path strings, 4 `50calImpact`, 4 `sound_turret_rotation_yaw`) for B-06 to repoint, T-WP5 unwritten (no trigger), 2 of 4 pod points UNKNOWN (2 sockets), 12 distinct shipped lights take T-18 members over 16 edit rows (19 edits incl. 2 slot pointers + 1 interaction), `Builds/bm-005` ships the **loose** `.epe` (no `.ee`/`.toc` re-pack) and the dropzone-loose-`.epe` install is unproven offline) |
| B-09 | done | `Working/Damage/bm_health.json` + `Builds/bm-009/receipt.json` + `python Tools/scripts/bm_health.py --check` + `python Tools/scripts/damage_audit.py --build Builds/bm-009/aaf` + `python Tools/scripts/damage_predict.py --root Builds/bm-009 table` + MODLOG §"B-09 · private health module — done" (the two blockers on this row are gone: `damage_predict.py` now takes `--root <build>` and prints the hits-to-kill table, and the ARM-4 rows are written where they live - the per-vehicle `custom_land_global.vmodc`. Built: a private `batmobile_health_medium.vmodc` (3,741 B) with `max_health` 2000 -> 36000 (T-DM1, a switch declared for `bm-009` only), `deform_scale` 0 (T-DM6) and `impact_damage_factor` 0 (T-DM8) asserted; the shared `lave_health_medium.vmodc` stays byte-identical (R7, sha256 `AF5C33E6…`); `front/rear_wheels_damage.skew_health` 200 -> 400 in our own land_global; the `.epe` root `damage` hash 670,155,287 -> 1,928,726,201 = `hash_jenkins` of the private path (one 4-byte write under name hash `4f489f01`, type 0x0e); values written at their decoded `offset-in-file` so no file grows, 245 health members and 61 land_global members re-read identical; packed, 605 `.toc` records, private module internal at offset 23,222,112; `aafdiff` vs bm-002 exactly 4 files. Done: `damage_audit.py --build Builds/bm-009/aaf` -> `29 members, 6 outside the shipped range, 6 declared switches` / `check ok` (it now audits the module the `.epe` names; the live `current.json` audit is still `check ok` with 5); `damage_predict.py --root Builds/bm-009 table` -> 36,000 HP and tank cannon 24 / 48 / 25 hits H0/H1/H2 = T-14's table. 4/4 tampers caught and reverted (module value, `.epe` hash, shared-module byte under R7, `.toc` offset 0); `t10_damage.py --check`, `t_rows.py check`, `status_audit.py --check` green. Open item: 4 part damage types (`Boat_Antenna`, `Boat_Generic`, `Plane_Control_Surface`, `Train_Generic`) have no `PartDamageType` row and fall back to `Default` - no row invented) |
| B-11 | done | `Working/Audio/bm_bank_manifest.json` + `Builds/bm-004/receipt.json` + `python Tools/scripts/bm_audio.py --check` + `Builds/bm-004/install.ps1 -Action Install/Verify/Rollback091 -GameDir <sim>` + MODLOG §"B-11 · Audio bank — done" (route **a + c** from `Research/JC3Grab/JC3_AUDIO.md` §10 — no `.fev` project ships, so a bank cannot be authored: two **private copies** of the shipped banks (R7) carry **5 swapped sample payloads** rebuilt from the T-16 map — `vehicles.bank` #7 `jc3_veh_door_tank_open_03` 29,954 fr, #98 `jc3_veh_door_tank_close_01` 24,933, #151 `jc3_veh_land_premium_nitro_loop` 154,818, #279 `jc3_veh_lave_chassis_spin_creaks_loop_fast` 336,000 and `weapons.bank` #408 `jc3_wpn_minigun_fire_close_loop_04` 160,337; sample counts **649 + 1,228** and both **file sizes unchanged** (210,781,376 B / 177,586,080 B), payload spliced into its own FSB5 `data:` block at its decoded `data_offset`; each payload re-measured as the map measured it, **max LU delta 0.00 ≤ 0.05** and 0 clipped/padded where the map says so; `.ee.fmod_guids` **re-emitted from the `.ee`'s own inner file** (758 B, version 1, banks vehicles/character/effects, **45 GUIDs**) and byte-identical, so no `.ee`/`.toc` change is needed for the event pins; `Builds/bm-004/aaf` is bm-001's identity tree; **Done 1** every mapped event resolves — 5/5 (`f74ea43b…`, `500e1421…`, `1f867af8…`, `f58a18f7…` as `EVTS` + `TLNB` tune rows in the built bank, W-03 through its slot, no donor GUID by T-11); **Done 2** sample count/lengths == manifest via `fsb5` + vgmstream on the written files (5/5 frames, names, rates, channels, durations) plus a per-slot `payload_sha256` recomputation; **Done 3** the generated installer rehearsed **offline** on a simulated dropzone (`-GameDir`, never `D:\Games`): decoy-vanilla Install → backup to `*.bm-004-backup` → Verify green → Rollback091 restores both bytes (`sha256sum -c` OK) and drops the backups; empty-dir Install → Rollback removes both "added by this build"; **5/5 tampers caught and reverted** — payload byte, manifest length, installer pin, `.fmod_guids` byte, and a T-16 map gain (provenance: "rebuilt payload is -8.20 LUFS, map says -10.33"); open items: no donor-GUID events for W-03, `tune→sample` stays UNKNOWN (T-16/G2-24), and `V-04` still owes the decode-back loudness/loop gate) |
| B-08 | done | `Working/Effects/bm_fx_edits.json` + `Builds/bm-008/receipt.json` + `python Tools/scripts/bm_fx.py --check` + MODLOG §"B-08 · Effect attachments — done" (the flame is **already in the donor graph and already `EngineNitro`** - `exhaust_upgrade_nitrous`/`…2` carry `Usage -97082140` = `4197885156` and `Effect -776668445` = `hash_jenkins("effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc")` (T-FX7) - so the card's build step is **placement**: both emitters' `world` becomes the `Afterburner` socket's matrix (G1-13, bone `JetSMove`, pos `-0.009578, 0.537762, 3.393177`), replacing the Serpente exhausts `±0.410, 0.373, 2.480`; objects 467 -> 467, bm-008 vs bm-005 = **1 changed file of 689**, the exported-XML diff is exactly the 2 `world` lines under `Usage -97082140`); **Done 1** 48 effect objects / **32 distinct `Effect` hashes -> 32/32 resolve to exactly one of the fleet's 955 `.effc` paths, 0 unresolved**, T-17 chosen paths 12/12 in the vocabulary, the flame path present in the build tree (donor container set 74 `.effc`); **Done 2** **89 (usage, object) pairs, 0 outside the 155-value fleet usage vocabulary**, the 2 emitters carry `4197885156` = `EngineNitro` (G2-22 `nitro.usage.objects` names exactly those two); heat haze = T-FX9 named omission (0 BmAK systems, 0 of 955 paths), weapon effects = B-06's payload (T-FX10/11/14/15 `next`), damage/death = T-FX21/22/23 `keep` and hash-resolve; 3/3 tampers caught and reverted (`world` +1 m, `Effect` -> 1234567, `Usage` -> 4242); limits: the loose `.epe` install is unproven offline (B-05), the emitters' orientation is the socket's decoded basis (row-2 axis semantics for effect attachments UNKNOWN -> Q-1 #5), and T-FX8's trigger column says `EngineRunning` while the graph's `exhaust`/`exhaust2` objects carry `3336946931` = `EngineKeyOn` (kept as T-17 says) |
| B-07 | done | `Working/Lights/bm_lightrig.json` + `Builds/bm-007/receipt.json` + `python Tools/scripts/bm_lightrig.py --check` + MODLOG §"B-07 — done" (21 shipped entries → **18**, module 6,337 → 5,745 B `D4E6610B…A34E`, packed `.ee` 11,180,088 B `B953E20C…C836B4`, `.toc` 605 records, module record 16,499,616 / 5,745; 11 shipped rows rewritten onto the B-03 lamp part that carries the lamp with T-18's colour + anchor, 1 new row for the graph's `Front_Secondary_Head` (T-L17), 6 T-18 `custom` rows (2 battle heads re-hosted from T-18's pre-B-03 body onto the head-lamp parts), 10 shipped rows dropped with measured reasons (2 tail points, 1 orphan `Rear_Brake` preset, 4 indicators + 2 reverse the BmAK rig has not, `Front_Primary_Head` whose BmAK socket has no lamp face); Done line **18/18** entries name a part that exists with `has_lights = 1` (7 distinct parts, indices from B-04), read back independently through the `.toc`→SARC→`jc3adf`; 450 member cells 360 decoded / 6 decoded (mapped) / 68 derived / 16 derived (verified), 0 assumed; `aafdiff` vs bm-005 exactly 1 file, shared modules and `@files.xml` byte-identical (R7); 2/2 tamper tests caught and reverted; the two rear arch parts stay lit with no entry (no BmAK rear-wheel socket); anchors remain the §112 / Q-1 #7 probe) |
| B-06 | done | `Working/Weapons/manifest.json` + `Builds/bm-006/receipt.json` + `python Tools/scripts/bm_weapons.py --check` + `python Tools/scripts/jc3weapons.py --check --root Builds/bm-006` + MODLOG §"B-06 — done" + §"B-06 rework — done" (rebuilt 2026-10-31 from the **reworked** `bm-005` `f4abe91da0bc3ce3…` — 124,488 B, 467 objects, **466 classed + 1 classless root / 46 classes**; 2 private tune copies, `w602_batmobile_cannon` 14,224 B and `w603_batmobile_vulcan` 14,223 B, each patched in place at its ConvertAdf `offset-in-file` (`fire_rate` 0xA0, `velocity` 0x9C) so its size is the shipped size; T-11's 3 numbers written: `fire_rate` 1.75 -> 2, `velocity` 500 -> 400, `fire_rate` 0.1 -> 0.138; 8 `id:` members repointed on B-05's 4 components — `AA7096C9` = `tuning_file` and `6D4C8277` = `autoaim_tuning_file` (WEAPON_WIRING.md:16), at the values the medium tank's own graph and the Serpente's own graph carry; B-05's rework is inherited, not re-applied: 0 `weapon_anchor` strings in the built graph and all 4 `weapon_type` = 2 (the old `bm-006` carried 4 refs + `weapon_type 1`); both private tunes registered in `@files.xml`; objects 467 -> 467, `.epe` 124,488 -> **124,744 B** `122912827db7ecfb…`, `--write` twice gives that sha; `aafdiff` vs bm-005 = 2 files only in the build (the private tunes) + 2 changed (`@files.xml`, `.epe`), **687 identical**, 689 -> 691 files; **Done 1** `bm_weapons.py --check`: 9 weapon paths named by the `.epe` — **2 private in the build** (0 exact, 2 via `.wtune` -> `.wtunec`), **3 in `INDEX.jsonl`**, **4 named only by a shipped graph** (the APC's body model, collision `.pfx`, grip point and shared effect `.etune`; the card copies tunes, not models), **0 dangling**; **Done 2** `jc3weapons.py --check --root Builds/bm-006`: 3/3 edits re-read, 2/2 tune files decode; 5/5 tampers caught and reverted (one byte on `fire_rate`, deleted private tune, unregistered `@files.xml` row, `weapon_type` 2 -> 1 in the built `.epe`, and the **new base-sha guard** fired against the pre-rework `d118c0aa…`); the receipt now records `base_sha256`/`base_bytes`/`base_classes` and `--check` compares the dependency with that recorded sha instead of a value re-derived in the same run; limits: `w602`/`w603` ship no `.ee` so their copies are tune-only; `w618` keeps the shared shipped tune (R7) and all four components are `CBulletWeaponBase` (0 `CMissileWeaponBase`), so the missile tune + no-lock-on missile autoaim on w618 is a **name-level match, behaviour UNKNOWN** (R5, `limits[]` L-1, w618 not counted in `private_tunes`); each copy's inner ADF instance name still reads `<shipped basename>.wtune` (renaming needs a re-encode that is not byte-identical — 14,224 -> 14,208 B — so whether the name is load-bearing is UNKNOWN, L-2); B-05's loose-`.epe` install stays UNKNOWN offline (L-3)) |
| B-12 | todo: D-2 reopened | `Tools/scripts/b12_variants.py --check` + MODLOG §"B-12 — reopened" + `tmp/freebuff/reports/apply-mode-switch-rows.md` (the card is live again: §11 D-2 was **reopened 2026-11-06** because BmAK has two modes and the hybrid cannot carry T-MD5…T-MD8/T-MD13/T-MD14; the card now carries four preconditions — D-2 re-resolved to (a), a two-set `t11_variants.json`, a runtime entity swap (UNKNOWN, `mode-switch-carriers.md` §7 U1), and `bm_build.py --variant` + a second tree; the checker re-derives all four from disk and fails the moment one is met, because then the card is buildable and must not stay a todo; today: `t11_variants.json` still declares **1 variant** (`hybrid`), `bm_build.py` registers **no** `--variant`, **0** variant-named trees, so the card is live and unbuilt); **no payload in RC4**: the pursuit/battle pair is built in `Builds/bm-RC4-modes` but is **unmerged** — the RC is the pursuit set only, with 0 rows carried exactly, 2 composed (T-MD5, T-MD6), 2 same-switch (T-MD10, T-MD11) and 4 not built (T-MD7, T-MD13, T-MD8, T-MD14) |
| B-13 | done | `Builds/bm-013/drop/profile/{item,task}.onlinec` + `online.stringlookup` + `textures/ui/vehicle_icons/v0300_car_kensington_sportsmuscle_batmobile.ddsc` + `Builds/bm-013b` (standalone leaf, B-13b) + `python Tools/scripts/bm_rebel.py --check` (`PASS: B-13 0 failure(s)`) + MODLOG §"B-13 done" (197 items, the Batmobile at UIDisplayOrder 12, unlocked with the Serpente by task 1361701860; name/blurb in `Working/World/bm_rebel_text.json`; UNKNOWN: new-leaf resolution from the item hash = Q-1) |
| B-14 | done | `Builds/bm-RC1/` (`drop/` 8 files + `receipt.json` schema 2 + `install.ps1` Status/WhatIf/Install/Verify/Rollback091) + `python Tools/scripts/bm_rc.py --check` (`PASS: bm-RC1 0 failure(s)`: -WhatIf == receipt, 2 offline rehearsals) + `Working/RC/bm_rc_manifest.json` + MODLOG §"B-14 done" (3-way .epe merge of B-06/07/08; B-10 integrated; found: 4 wheel lod4/5 unpacked -> V-02) |
| B-15 | done | new card (found by V-01): `Tools/scripts/bm_budget.py` applied in `bm_rc.py` step 3b; non-vanilla model 5,972.9 -> 4,791.3 KB of 4,915 (R9; method calibrated on test-065/081/085/091, which rendered); 16 far-LOD .lod trims; Serpente panels not unbound (vanilla-identical, not counted; V-02 checks if they draw) + MODLOG §"B-15" |
| B-16 | done | new card (found by V-03): weapon-clone cleanup in `bm_rc.py` (4 `F30CCB1C` owner links -> null, 12 APC mounted-M2 body members removed; medium-tank + preorder convention) + RC merge per-branch base fix (bm-007/008 on the pre-rework bm-005) + MODLOG §"RC merge fix" |
| B-17 | todo | **no payload in RC4** (declared no-payload in `BUILD_BATCHES` §4); card in §8; writer proof `tmp/freebuff/reports/effc-format-writable.md` + `python Tools/scripts/effc_writer.py check` (95/95 carry byte-identical, 91.49% bytes from fields, one edited copy re-read); the five plans it executes are `Working/Translation/T13_FX.md` §5 |
| B-18 | todo | **no payload in RC4** (declared no-payload in `BUILD_BATCHES` §4); card in §8; chain and probes `tmp/freebuff/reports/immobiliser-and-emp-trigger.md` §7-§8; state scan `python Tools/scripts/t_md2_emp_state.py --check` (0 literal / 0 hash bindings of `is_disabled_by_emp`) |
| B-19 | todo | **no payload in RC4** (declared no-payload in `BUILD_BATCHES` §4); card in §8; field-by-field mapping `tmp/freebuff/reports/hacker-and-tracker-gadgets.md` T-WP7 + leads 1-2 |
| B-20 | todo | **no payload in RC4** (declared no-payload in `BUILD_BATCHES` §4); card in §8; `tmp/freebuff/reports/sonar-and-scan-pulse.md` §4 (pulse + ring + `BML_Sonar`); audio ids `Research/BatmobileGrab/AUDIO_BANKS2.md:154-169` |
| B-25 | todo | **no payload in RC4**: the flare sprite cannot be attached (no effect member on a lamp); card in §8, 17 flare entries + 4 cone/intensity members, per `Research/specs/B-25.md` |
| B-26 | todo | **no payload in RC4**: the 21 pinned audio GUIDs stay donor; card in §8, private bank + per-entity binding rows, per `Research/specs/B-26.md` |
| B-21 | todo | card in §8; `tmp/freebuff/reports/hacker-and-tracker-gadgets.md` T-WP9 (fire position 30.0 deg, no homing/distance member) |
| V-03 | done | `python Tools/scripts/v03_wiring.py --check` -> `PASS: dangling 0` (9 weapon points, 63 objectid refs, 26 asset paths, audio, Rebel Drop) + `Builds/bm-RC1/verify/wiring.{json,md}` + MODLOG §"V-03 PASS" |
| V-06 | done | dry run on a copy of the live dropzone (`E:\Modding\_dropzone_sim`): WhatIf 8 / Install 8/8 / Verify 8/8 / Rollback091 -> sha256-identical to the live dropzone + MODLOG §"V-06" |
| B-06 … B-14 | superseded - see the individual B-xx rows above (all done) | stale placeholder corrected 2026-11-06 |
| V-01 … V-07 | partly done - see the V-xx rows (V-01, V-02, V-03, V-05, V-06 done on RC2; V-04 RED/partial; V-06-RC2 FAIL; V-07 not started) | stale placeholder corrected 2026-11-06 |
| Q-1 … Q-5 | todo | |
| G3-02f2 | done | `Research/BatmobileGrab/SAMPLER_UNKNOWNS.md` + `bmak_sampler_unknowns.py --check` OK (12/12 oracles): 4/7 UNKNOWNs closed from files, 3 partly with the missing input named (task 7207, re-run 2026-11-05) |
| G3-10c2 | done (UNKNOWN stays) | `Research/BatmobileGrab/INERTIA.md` + `grab_inertia.py --check` OK: BmAK cooked physics has no mass/tensor; JC3 hknpShapeMassProperties decoded (56 blocks); box/hull-formula oracle refuted 0/107 (task 7206) |
| T-MD-D2-reopen | done (decision + card + 6 rows) | `tmp/freebuff/reports/apply-mode-switch-rows.md` + `b12_variants.py --check` PASS (card live and unbuilt, 4 preconditions) + `t11_modes.py --check` PASS (15 rows, ledger 15/15) + `t_blocked.py --write/--check` PASS (18 blocked of 216) — D-2 **reopened 2026-11-06**: BmAK has two modes and a hybrid cannot carry T-MD5…T-MD8/T-MD13/T-MD14; B-12 is `todo` again with four preconditions (task 8301) |
| T-BLOCKED | done | `Working/Translation/BLOCKED_PROPOSALS.md` + `t_blocked.py --check` PASS: **17** blocked re-derived (13 ledger + 4 T6) of **216** in scope (re-run 2026-11-06 after T-S6's bridge moved it to `next`; `RESOLVED["T-S6"]` + 3 evidence oracles, `WAITS`/`ATTEMPTS` entries removed, `reconciles` 13+4=17); T-FX3 unblocked, T-ST7 reason refuted (operator decision), T-WP4 half; the five T-MD rows D-2's reopening put back in scope (task 8301) are the five new waits; `T_ROWS.jsonl` edited by task 8301 (the five rows + T-MD14 + T-MD15's note), `BLOCKED_PROPOSALS.{json,md}` regenerated |
| V-04 | RED | `Builds/bm-RC1/verify/audio.md` + `v04_audio.py --check` PASS (reproduces) but verdict RED: loudness 4/5 (max 2.33 LU), loop clicks 1/3 (weapons#408, vehicles#279); follow-up queued |
| T-FX9-carrier | done (research; ledger row not yet updated) | `Research/JC3Grab/FX9_HAZE.md` + `Tools/scripts/fx9_haze.py check` 12/12 (re-run 2026-11-06): closest carrier to BmAK heat-steam = `effects/jc_vehicles/exhaust/car_speedrom_heater.effc` (+ 24 `z80_exhaust_heat_l/r` attach objects, 2 distortion texture families); per-instantiator blend/texture hashes UNKNOWN; ledger row T-FX9 updated by brief 8202 (task 8103) |
| T-FX13-carrier | done (research; ledger row T-FX13 updated by brief 8202) | `tmp/freebuff/reports/fx13-shell-casings.md` + `Tools/scripts/fx13_casings.py --check` PASS 25 checks (re-run 2026-11-06): JC3 DOES eject casings on vehicles - `SAttachedEffect ShellEjection` (Effect 600259254, Usage 4131019937) in the mounted-MG entity, 14 containers / 5 vehicle dirs; the ledger sentence "no vehicle carries a casing effect" was false (task 8105) |
| T-FX12-16-tracer | done (rows T-FX12/T-FX16 flipped to `next` by brief 8202) | `tmp/freebuff/reports/fx12-16-tracer-and-trail.md`: tracer = 8 `bullet_base_tuning` members (texture, length, width, speed, TTL, 3 smoke-trail); colour not a tune member; trail half = `.effc` system, private copy of `missile_trail_car.effc` with two emitters; the refrain re-derives the cells via `t17_fx.py --check` (task 8104) |
| T-L10-L23-carriers | done (research; ledger rows updated by brief 8203) | `tmp/freebuff/reports/muzzle-and-forensics-lights.md` + `Tools/scripts/t_lights_forensics.py --check` PASS 16/16 (re-run 2026-11-06): closest = a `VehicleDynamicLights` row (spot cone angle 50 / range 50 shipped maxima) for T-L10 and T-L21..L23, with the gap for the build (task 8107) |
| T-G-research-batch-8106-8111 | reports only (no --check; not flipped) | `tmp/freebuff/reports/{fx20-brake-trail,lens-flare-carriers,winch-and-tether,sonar-and-scan-pulse,hacker-and-tracker-gadgets}.md`: each states closest system + gap per row; applied to the ledger by briefs 8202-8205 (tasks 8106, 8108-8111) |
| T-MD2-EMP-disable | done (research; ledger rows T-MD2/T-WP5 updated by brief 8205) | `tmp/freebuff/reports/immobiliser-and-emp-trigger.md` + `Tools/scripts/t_md2_emp_state.py --check` PASS (EMP_DISABLE.json re-derives byte for byte) + `Tools/scripts/jc3emp.py --check` PASS (re-run 2026-11-06): the effect half (pulse object) is decoded; closest system for turning an engine off is the engine's own `CEMPWeapon` path; build closes the rest (task 8117) |
| T-APP-research-8131-8133 | reports only (no --check of their own; not flipped) | `tmp/freebuff/reports/{app-wetness-and-rain,app-per-pixel-reflectivity,app-reflectance-f0,app-anisotropic-highlights}.md`: each states closest system + gap + build action; applied to the appearance plan by brief 8211 |
| T-WP4d | done | `Working/Translation/T_WP4D_TRACKER_EMP.md` + `t_wp4d.py --check` PASS: tracker bInstantFire now UNKNOWN, _ForCars archetype attribution fixed (corrects T-WP4c; task 7217) |
| G3-09d2 | done | `Research/JC3Grab/TINT_WRITE.md` + `jc3_tint_write.py --check` OK (14 gates): tint_r is NOT in the .epe (CCar.palette int32 @0x29a = hash of the palette .vmodc path); the float lives in the palette `.vmodc` (task 7211) |
| G3-12f | done | `Research/JC3Grab/PHYSICSC_EXTENTS.md` + `jc3_physicsc_extents.py --check` OK: extents/AABB decoded on 5 files, hull oracle passes (task 7216) |
| V-03-RC2 | done | `Builds/bm-RC2/verify/wiring.{json,md}` + `v03_wiring_rc2.py --check` PASS (dangling 0, deterministic; the drift was `bm_audio.py`'s manifest embedding `installer.dropzone_at_build`, a live probe) (tasks 7213/7223) |
| V-04-diag | done (fix not applied) | `Builds/bm-RC1/verify/audio_diag.md` + `v04_diag.py --check` PASS: both RED gates traced to the build's payload rule; fixes derived, NOT applied (task 7221) |
| G3-02f3 | done (2 UNKNOWN stay) | `Research/BatmobileGrab/SAMPLER_UNKNOWNS2.md` + `bmak_sampler_unknowns2.py --check` OK: U3 press path found; U2 writer and U7 producer still missing their input (task 7226) |
| T-CO-audit | done (3 rows wrong) | `Working/Translation/COLLISION_SOURCES_AUDIT.md` + `t_collision_sources.py --check` PASS: T-CO1, T-P3, t16_collision.json carry the wreck-vs-drivable error; T-CO3, T-PA3 clean (task 7220) |
| V-05-looks | done | `Working/Q/PREDICTIONS_LOOKS.md` + `v05_looks.py --check` 27/27 (34 lines, 9 UNKNOWN) (task 7219) |
| T-CO-corrected | done (proposals only) | `Working/Translation/COLLISION_ROWS_CORRECTED.json` + `t_collision_corrected.py --check` PASS (task 7227; T_ROWS.jsonl / t16_collision.json not edited) |
| T-TINT-impact | done | `Working/Translation/TINT_IMPACT.md` + `t_tint_impact.py --check` PASS (task 7224) |
| B-10-extents | done | `Working/Collision/BM_EXTENTS_CHECK.md` + `bm_extents_check.py --check` PASS: shipped batmobile.physicsc body hull 349.5 x 227.1 x 702.5 cm, 1,232 child vertices inside stored AABBs (task 7225) |
| DECISIONS | open: operator | `Working/Translation/DECISIONS_NEEDED.md` (task 7230): T-ST7, T-FX3, T-WP13, T-WP4 need an operator decision |
| V-06-RC2 | **FAIL: Rollback091 deletes files** | `Builds/bm-RC2/verify/dropzone_sim.md` + `dropzone_sim.py --check`: WhatIf/Install/Verify pass on a copy; `Rollback091` on a dropzone that already holds the build deletes all 9 payload files (install.ps1 line 49 backs up only when the hash differs; line 66 deletes targets with no backup). Real dropzone is in that state: do NOT run Rollback091 there. Fix queued (task 7231) |
| RC-diff | done | `Builds/bm-RC2/verify/rc_diff.md`: RC1 and RC2 payload byte-identical (700 files); only install.ps1 + receipt.json differ (tag/card fields); no MODLOG entry for bm-RC2 (task 7233) |
| V-05-combat | done | `Working/Q/PREDICTIONS_COMBAT.md` + `v05_combat.py --check` 54/54 (10 predicted, 1 UNKNOWN) (task 7232) |
| V-05-driving | done | `Working/Q/PREDICTIONS.md` + `v05_driving.py --check` 16/16 (4 Q-2 checks, 3 predicted, 2 UNKNOWN) (task 7203) |
| V-RC2-weapons | done (4 points UNKNOWN) | `Builds/bm-RC2/verify/weapon_points_vs_bmak.md` + `v_weapon_points_rc2.py --check` OK: 5/9 SWeaponPoints sit on their BmAK socket (max 0.000 cm); 4 are APC-template mount markers with no BmAK socket (task 7240) |
| V-RC2-lights | done (1 exception) | `Builds/bm-RC2/verify/lights_vs_bmak.md` + `v_lights_rc2.py --check` PASS: 18 entries, colour 17/18 equal (entry 11 / T-L17 differs: graph diffuse vs CDO fallback); module has no socket member (task 7239) |
| R-6-sample | done | `Research/BatmobileGrab/REMAINDER_SAMPLE_AUDIT.md` + `remainder_sample_audit.py --check` PASS: 30/30 sampled objects agree; REMAINDER.md has byte-accounting verdicts only, NOT handling/upright/damage/material classes (those are RESET_FINDINGS words) (task 7235) |
| T-ROW-EVIDENCE-1 | done (findings) | `Working/Translation/ROW_EVIDENCE_AUDIT.md` + `t_row_evidence.py --check` PASS: first 40 of 145 resolved rows: 21 cite no file, 6 cite a file without the quoted value, 1 partial (task 7234); rows 41-145 queued |
| V-06-fix | done (copies only) | `Working/Installer/install_v2.ps1` + `Tools/scripts/install_v2.py --check` PASS: guard refuses non-sim paths; all 3 cases (targets differ / identical / absent) Rollback sha256-identical to pre-Install; fixes the Rollback091 delete defect found in V-06-RC2. NOT yet used by Builds/bm-RC2/install.ps1; operator decision (task 7245) |
| MODLOG-RC2 | draft | `Working/Translation/MODLOG_RC2_DRAFT.md`: paste-ready bm-RC2 MODLOG block (bm_rc2.py = bm_rc.py + TAG/--physicsc/b10_input); not yet in MODLOG.md (task 7246) |
| T-FX-pairs | done | `Working/Translation/FX_PAIR_AUDIT.md` + `t_fx_pair_audit.py --check` OK: 3/3 chosen pairs hold, 4/5 omissions hold, T-FX16 "0 of 955" is UNKNOWN (names no search term) (task 7244) |
| T8-anim-coverage | done | `Working/Translation/PARTS_ANIM_COVERAGE.md` + `parts_anim_coverage.py --check` PASS: 12/15 parts covered; P-02 cannon, P-05 jet, P-13 steering wheel have no sequence (task 7243) |
| T-ROW-EVIDENCE-2 | done | `Working/Translation/ROW_EVIDENCE_AUDIT2.md` + `t_row_evidence2.py --check` 15/15: rows 41-90: 2 DEAD PATH, 26 NO PATH, 2 VALUE-NOT-FOUND (task 7247) |
| V-RC2-mounts | done (4 points UNKNOWN stays) | `Builds/bm-RC2/verify/mount_markers.md` + `v_mount_markers.py --check` OK: 4 type-4 points are JC3 MountAttach (APC w206 clone) wired by NAME to yaw/pitch parts; BmAK has no mount concept, so no anchor (task 7250) |
| T-MODES-HUD-ev | done | `Working/Translation/MODES_HUD_EVIDENCE.md` + `t_modes_hud_evidence.py --check` 35/35: 5 of 6 rows hold, T-CAM2 contradicts its own numbers (task 7255) |
| T-L17 | **row wrong** | `Research/BatmobileGrab/LIGHT_ENTRY11.md` + `t_light_entry11.py --check` 26/26: BmAK run-time colour for light entry 11 is class-default white [255,255,255,0]; built 0.6039/0.6039/0.9529 is JC3's graph colour; row T-L17 to change (not edited) (task 7251) |
| FX16-term | done | `Working/Translation/FX16_TERM.md` + `t_fx16_term.py --check` 27/27: T-FX16 term = `canon_trail` + `shell_trail` (t17_fx.py:154) (task 7253) |
| install_v2 | **needs fixes** | review `tmp/freebuff/reports/install-v2-review.md`: path guard is a bare string prefix (sibling folder accepted) and Rollback deletes any manifest path (outside-dropzone path deleted in test). Do not adopt install_v2.ps1 as-is |
| TL17-proposal | done (proposal) | `Working/Translation/TL17_PROPOSAL.md`: T-L17 colour must become 1.000/1.000/1.000 (class-default white), intensity unchanged; row/build not edited (task 7258) |
| T-CAM2-proposal | done (proposal) | `Working/Translation/T_CAM2_PROPOSAL.md` + `t_cam2_proposal.py --check` OK: numbers FOV [55,63] right, clause "68 only if +10 speed bonus; 95 boost is a gap" wrong (task 7257) |
| V-05-driving | done | `Working/Q/PREDICTIONS.md` + `v05_driving.py --check` 16/16: 4 Q-2 driving checks, 2 UNKNOWN needing a physics model (task 7203) |
| STATUS-stale | finding | `tmp/freebuff/reports/stale-status-numbers.md`: status_audit --check cannot see 3 stale/unsourced STATUS.md numbers (compares the doc with its own generator) (task 7259) |
| install_v3 | done (copies only) | `Working/Installer/install_v3.ps1` + `Tools/scripts/install_v3.py --check` PASS x3 from clean state (cleanup_own() missed SIM_ROOT; fixed task 7266): v2's two bypasses refused, 3 rollback scenarios sha256-identical. Not yet adopted by Builds/bm-RC2/install.ps1: operator decision |
| TURRET-joint | **root cause found** | `Builds/bm-RC2/verify/joint_trace.md` + `v_joint_trace.py --check` 21/21: joints die at the B-04 manifest (no joint member in `bm_vehicle_parts.json`), `bm_parts.py` hardcodes -1; no later step removes them; field description queued (task 7274) |
| V-04-loops | finding | `Builds/bm-RC1/verify/loops.md` + `v04_loops.py --check` 87/87: the 3 loop points are in neither the WAV nor the FSB5 LOOP chunk; loop region = whole payload; at that join only the minigun is below -40 dBFS (task 7260) |
| V-RC2-turret | **FAIL: no joint** | `Builds/bm-RC2/verify/turret_ranges.md` + `v_turret_ranges.py --check` 17/17: rows P-01/P-02 agree with BmAK to 0.000 deg, but bm-RC2 carries NO joint for turret or cannon (yaw missing 120 deg, pitch 25 deg); 4 of 5 comparisons flagged (task 7261) |
| BOOST-cov | done (gap) | `Working/Translation/BOOST_COVERAGE.md` + `t_boost_coverage.py --check` PASS: T-B1/B2/B3 cover torque cap, accel, decel; duration, recharge, donut, base cap and boost flags have NO row (task 7262) |
| V-RC2-wheels | warn | `Builds/bm-RC2/verify/wheels.md` + `v_wheels.py --check` ok: the 4 wheel parts still carry shipped Serpente parent_space_offset translations (max 1.013 m from the hardpoints) (task 7264) |
| V-RC2-strings | done | `Builds/bm-RC2/verify/strings.md` + `v_strings.py --check` 18/18: name 60A5E7A4 + blurb F34BA8E8 in 11 languages, hashes match, no vanilla pair lost; compromise: blurb is English in every language (task 7265) |
| V-RC2-entity | **36 unexplained** | `Builds/bm-RC2/verify/entity_diff.md` + `v_entity_diff.py --check` 15/15: debug.epe drops 34 of 40 CPartProp objects; 87 differences, 51 tagged, 36 UNEXPLAINED (root CCar rename, added palette member) (task 7263) |
| JOINT-fields | done | `Working/Parts/JOINT_FIELDS.md` + `joint_fields.py --check` PASS: donor joint indices (tank 2/0, APC 15/14); P-01 -60..60 deg = +-1.047198 rad, P-02 -5..20 deg = -0.087266..0.349066 rad; manifest has no joint key; next index 11 (task 7274) |
| V-RC2-wheels | resolved: harmless | `Builds/bm-RC2/verify/wheel_offset_effect.md` + `v_wheel_offset.py --check` PASS: stale wheel parent_space_offset is not used for placement (hardpoints are; live test-047/053/060); no visual or physics effect (task 7272) |
| V-RC2-strings | **compromise real** | `Builds/bm-RC2/verify/strings_languages.md` + `v_strings_languages.py --check` PASS: vanilla blurbs are translated in every language (83/83, 105/105); English-in-all-11 for the new blurb is NOT normal (task 7273) |
| HUD-radar-recheck | done | `Working/Translation/HUD_RADAR_RECHECK.md` + `hud_radar_recheck.py --check` PASS: 8 numbers: 5 SAME, 0 DIFFER, 3 no source; `Working/HUD/RADAR.json` standalone_divisor null is wrong, AS3 divides by 400 (task 6999) |
| BOOST-rows | done (proposal) | `Working/Translation/BOOST_ROWS_PROPOSAL.md` + `t_boost_rows.py --check` 21/21: BoostDuration 2.0 s -> VehicleMisc.full_nitro_use_time etc.; T_ROWS.jsonl untouched (198 rows) (task 7271) |
| V-RC2-entity | cause found | `Builds/bm-RC2/verify/entity_unexplained.md` + `v_entity_unexplained.py --check` 23/23: the 34 dropped CPartProp come from the graph B-05 starts from (bm-009, 416 objects / 6 props, descends from the 5-part carve), not from a later step (task 7270) |
| JOINTS-v2 | built, **NOT usable alone** | `Working/Parts/bm_vehicle_parts_v2.json` + `Tools/scripts/bm_parts_v2.py --check` ok + `Builds/bm-RC3-parts/` (61 parts; P-01 constraint_index -1 -> 11, P-02 -> 12; 59/59 other rows byte-identical to bm-RC2): the indices are a FORWARD REFERENCE - `batmobile.physicsc` has only 11 constraint objects, so 11/12 do not exist yet. Do not install RC3-parts until two hkpLimitedHingeConstraintData are appended (task 7275) |
| G3-04d2 | done (UNKNOWN stays) | `Research/JC3Grab/UNIFORM_RECORDS.md` + `jc3_uniform_records.py --check` ok (6,966 records, 12/12): records name parameters and values but none maps a name to a cbuffer offset; BaseColour/Diffuse_Adjust hashes resolve to nothing; paint combine rule stays UNKNOWN (task 7205) |
| BLURB-translations | done (proposal) | `Working/Translation/BLURB_TRANSLATIONS.{md,json}`: 10 machine-written proposals under unchanged key F34BA8E8, each needs native review (task 7276) |
| R-5-part1 | done | `Working/Translation/R5_PART1.md` + `r5_part1.py --check` PASS: first 35 "NOT TRANSLATED" rows: 20 built and equal, 5 built different, 6 absent, 4 unreadable - "not translated" does not mean missing (task 7208) |
| G3-20e | done | `Research/BatmobileGrab/LEDGER_G3E.md` + `g3_20e_rows.py --check` ok: second-half 35 re-derivable rows re-run fresh: 2 hold, 0 wrong value, 33 still open (task 7209) |
| V-01-RC2 | done GREEN | `Builds/bm-RC2/verify/files.md` + `v01_rc2.py --check` ALL GREEN: 5 file gates, Model 4,791.3/4,915 KB, Texture 5,855.8/7,065 KB, 12 values read back through the .toc (task 7213) |
| HINGES-physicsc | done (copy) | `Working/Collision/batmobile_hinged.physicsc` + `bm_physicsc_hinges.py --check` ok: 13 constraint objects, new hinges at 11 (turret) and 12 (cannon), original constraints and hknpPhysicsSystemData identical; closes the forward reference of Builds/bm-RC3-parts (task 7277) |
| V-04-fix | partial (1 red) | `Builds/bm-004c` + `v04_audio_004c.py --check`: loudness 5/5, loop wrap 2/3, vehicles#279 still red (-28.27 dBFS stored / -39.68 payload vs -40) (task 7228) |
| CHECKS-sweep-A | done | `Working/Translation/CHECKS_SWEEP_A.md` (scripts a-g, task 7268); h-z half parked after the 04:06Z refusal, re-briefed |
| T-ST7-evidence | evidence for operator | `Working/Translation/T_ST7_EVIDENCE.md`: the refuting evidence holds - a player module ships 0.3 s full lock (MotorbikeSteering, 2 modules) and 0.25 s on 4 AI LandSteering modules (T_ST7B_FLOOR.md:16-20); decision still the operator's (task 8007) |
| V-02-RC2 | done (passes by 0.0004 pt) | `Builds/bm-RC2/verify/geometry.md` + `v02_geometry.py --check`: silhouette 99.9004% (limit 99.9), BUD-1 holes 0.2968%, 77/77 interaction points in band (0.0577-0.1461 m), 61/61 parts (task 7212) |
| EMERGENCY-end | done | skills/freebuff `EMERGENCY_MODE_REPORT.md` (13 hiccups) + GUI `hours_exhausted()`/`emerg_end()`: emergency mode ends at 0 daily hours (confirmed daily=0/53 at 05:06-05:11Z 2026-11-06) |
| Q-PILOT | todo (deferred: after phase V; test ban stays) | operator 2026-11-05 |
| R-1, R-2 | todo | |

Recommended order inside a phase is the card order. Cards inside G1 and inside G2 are mostly
independent: two agents can split G1 and G2 between them, but **T starts only after both G1X
and G2X**, as the user ordered.

---

## 13. Where the old backlog items went (so nothing is lost)

| old id (source) | now |
|---|---|
| GRB-1…GRB-11 (MODDING_PLAN §0.6) | done; inputs to G1 |
| G1-1…G1-7, G2-1…G2-9 (old GRAB_BACKLOG) | done; inputs to G1/G2 |
| DEP-1/2/3, PRV-1, ALB-1, MAT-1, ALB-2, BUD-1, PHY-1 | done |
| QA-1 | instrument done; takes → Q-2 |
| LGT-1 (probe test-083, night look pending) | G2-33 → T-18 → B-03/B-05/B-07 → Q-1 item 7 (the floating-lamp probe is superseded by the full light build) |
| LGT-2 | B-03 |
| PRT-1 | B-04 step 1 |
| PRT-2 / PRT-3 / PRT-4 | B-02 / B-04 / T-12 + TURRET.md |
| DMG-1…DMG-5 | G2-28, T-14, B-09, Q-1 item 6, Q-3 |
| WPN-1 / WPN-2 / WPN-3 | G2-10 / T-11 + B-05 / B-06 |
| MOD-1 (gate G1) … MOD-4 | G2-14/G2-21 → D-2 → T-15 → B-12 |
| HDL-1 (gate G2) | closed: names come from `CHAIN.json` (Batch B3) |
| HDL-2…HDL-5, HP-1…HP-5 | replaced by T rows + Q-2 takes; no hand tuning |
| AUD-1…AUD-5 | G1-15, G2-24, T-16, B-11, V-04 |
| CAM-1 | done as Batch F (test-091); A15 in Q-2; battle camera in T-15 |
| FX-1 | G2-22/G2-23 → T-17 → B-08 |
| POL-1 / POL-2 / POL-3 | T-21 / T-21 / G2-32 + B-13 |
| EXP-1 (water) / EXP-2 (standalone) / EXP-3 (skinned parts) / EXP-4 (packaging) | G2-31 / G2-27 / not needed: rigid parts + behaviours replace skinning / R-1 |
| RD-1 Rebel Drop | G2-26 → T-20 → B-13 |
| T_PLAN Batch D blocked rows | T-FX3 → G2-22; T-P3/T-CO2/T-CO3 → G2-30; T-L4/T-LG4 → T-18; T-HUD5 → T-19; T-CAM9/T-CAM11 stay blocked (no unit bridge, never hand-substituted); T-S6, T-ST7, T-AU3, T-AU5, T-CAM8 stay permanent omissions |
| T_PLAN Batch E (66 carried rows) and §5 takes | Q-1/Q-2/Q-3 |
| Gates G3 (hinges) / G4 (missile weapon) / G5 (turret aim) (MODDING_PLAN §6) | answered by §2.3 / §2.1 / §2.3 — confirmed by G2-14 / G2-10 / G2-13 |

---

## 14. Anti-goals (recorded dead ends — do not repeat)

- Do not tune any value by feel or launch the game to judge a constant (four appearance builds
  and four handling sets were spent that way).
- Do not translate by the closest-sounding member name (test-087).
- Do not use a fleet median on a row that carries a BmAK behaviour.
- Do not fit any part, wheel or socket with its own transform (R2); do not move visuals off the
  physics stations (R3).
- Do not edit shared modules or shipped weapon files in place (R7); do not internalise archive
  modules without the card saying so (R8).
- Do not chase `a00_dummy_*` texture paths (vanilla uses them too, MODLOG §106).
- Do not add geometry by append/count; topology-preserving only (MODLOG §34/§56).
- Do not encode glass with BC1 punch-through (vanilla is BC3/DXT5, MODLOG §102).
- Do not set `bullet_armor_strength` above the fleet maximum 99 (the strength gate, MODLOG §97).
- Do not treat a successful build, a 9/9 file proof or a byte-exact read-back as behaviour
  evidence; only phase Q is.
- Do not claim a BmAK value is unavailable until `CHAIN.json` and `objects.jsonl` were searched,
  and the search is written in the row.
- Do not mark a workstream 100 % from a task count; counts come from `status_audit.py`.
