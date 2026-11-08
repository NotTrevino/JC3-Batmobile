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
| R10 | **Game files stay outside the repo.** Extracted/decoded game data goes to `E:\Modding\_JC3grab\` or `E:\Modding\_BmAKgrab\`. Never commit or publish game files, extracted assets or decompiled code. | universal-modder `AGENTS.md` |
| R11 | **Counts are generated, never typed.** `STATUS.md` is regenerated by `status_audit.py`; tables of counts in new docs come from a script with `--check`. | `STATUS.md` |
| R12 | **Kill processes by exact PID** (`um win kill`), never by name. Back up saves (`um backup`) before any modded launch. Ask before driving the user's mouse/keyboard. | universal-modder `AGENTS.md` |
| R13 | **One variable per in-game probe** unless the card explicitly batches independent checks that cannot interact (phase Q does this on purpose to save launches). | plan §1.1.3 |
| R14 | **Journal everything** in `MODLOG.md` (append-only), with file paths and command output. | plan §1.1.5 |

### 0.6 Where things live

| what | path |
|---|---|
| project root | `E:\Modding\JC3-Batmobile\` |
| game install / dropzone | `D:\Games\Just Cause 3\` · `D:\Games\Just Cause 3\dropzone\` |
| BmAK grab (repo evidence) | `Research/BatmobileGrab/` (`grab.json`, `objects.jsonl`, `CHAIN.json`, `OFFSETS.json`, `MECHANICS.md`, `LIGHTS.json`, `AUDIO_MAP.json`, `PARTICLES.json`, `MESHES.md`, `SLOTS.json`, `CAMERA.md`, `HUD_*.json`) |
| BmAK raw exports (outside repo) | `E:\Modding\_BmAKgrab\meshes\`, `E:\Modding\_BmAKgrab\gltf\`, `E:\Modding\_BmAK_grab\` |
| BmAK packages | `E:\Modding\JC3-Batmobile\Playable_Batmobile_SF\`, `BmGame\`, `Startup\` (+ the 15 `Playable_Batmobile*` packages listed in `Research/BatmobileGrab/README.md`) |
| JC3 grab (repo evidence) | `Research/JC3Grab/` (`INDEX.jsonl`, `ENTITIES.md`, `VOCABULARY.md`, `PARTS_TABLE.jsonl`, `WIRING.jsonl`, `FX_TABLE.jsonl`, `GEOMETRY.md`, `SHAPES.md`, `DAMAGE_MECHANISMS.md`, `FLEET.md`) |
| JC3 decoded data (outside repo) | `E:\Modding\_JC3grab\` (`entities/*.ee.json` = modules as rows, `detail/*.ee.json` = `.epe` graph + meshes + physics, `geom/`, `hkx/`, `phys/`) |
| translation ledger | `Working/Translation/T_ROWS.jsonl` (+ `T6_HUD_CAMERA.md`), docs `T1_…`, `T2_…`, `T3_…`, `T5_BUILD.md`, `QA1_RESULTS.md` |
| builds | `Builds/test-0xx/` (live: **test-091**, verify `install.ps1 -Action Status`) |
| tools | `Tools/scripts/` (Python), `Tools/Gibbed/` (pack/unpack/ConvertAdf/ConvertProperty), `Tools/Gibbed-patched/`, `Tools/Deca/`, `E:\Modding\_tools\ffdec\` |
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
| DIM-2 | Tyre diameter matches the lore reference | PSKX **1.365–1.366 m** measured on all four tyres (`TYRES.md`, T-G2) vs wiki 1.40 → 2.4% apart, **accepted**; the docstring's 1.42 was an assembly envelope, not rubber (D-1 resolved: keep the PSKX) | `land_global.*_wheels.radius`, wheel RBMs |
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
| WPN-4 | `Batmobile_EMP_Missile_Launcher` (`RBatmobileEMPMissile`) — Immobilizer (pursuit mode, vs cars) | disables vehicles | EMP: `v0505 oldtruck_rebel_emp` device (G2-16) or a missile with an EMP explosion tune |
| WPN-5 | `Batmobile_EMP_Burst` (`RBatmobileEMP`) — electrical overcharge around the car | radial stun/push | `CForcePulse` (79 chassis / 232 `.ee`, G2-17) / EMP device |
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
`E:\Modding\_JC3grab\detail\` and `Research/JC3Grab/PARTS_TABLE.jsonl`. **P0-2 made them proof:**
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
In: `E:\Modding\_JC3grab\detail\*.ee.json`, `Research/JC3Grab/PARTS_TABLE.jsonl`,
`E:\Modding\_JC3grab\entities\v0300_…_civilian_01.ee.json` (module 3 = `vehicle_common`).
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
adds a `--check` mode. Raw exports (meshes, WAVs, animation keys) go to `E:\Modding\_BmAKgrab\`.

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
`E:\Modding\_BmAKgrab\anims\`), then convert to per-bone rotation/translation tables (JSON,
radians/metres in the PSK frame).
4. Classify each sequence by mechanism: canopy, turret, cannon, Vulcan, missile bays,
transformation (pursuit↔battle), wheels/strafe, suspension, fins/air-brakes, driver/Batman,
other. Classification must cite the animated bones, not the name alone.
Out: `Research/BatmobileGrab/ANIMATIONS.json` + `.md`; key-frame JSON outside the repo.
Done: 253/253 sequences named; each has a bone list and a mechanism class (or `other` with the
bones listed); `grab_anims.py --check` passes.
Stop: umodel cannot export a set → record which and why; continue with the names/bones.

#### G1-11 · Skeleton and vertex-to-bone ownership (needed to split movable parts)   M · deps: P0-1 · serves: APP-5, ANI-2…8
In: `E:\Modding\_BmAKgrab\meshes\` (`Batmobile_V2.pskx`), `Tools/scripts/pskx_parts.py`,
`psk_geom.py`, `MESHES.md`, `SLOTS.json`.
Do: 1. Read the bone table (name, parent, bind pose) and per-vertex influences of
`Batmobile_V2` LOD0 (and LOD1/LOD2). 2. For each bone, list the faces whose vertices are
weighted ≥ 0.5 to it, per material slot. 3. Give each bone its bind-pose pivot **in JC3
coordinates through the one transform** (`bat_assemble.T`). 4. Flag faces with split weights
(they will need a cut decision in B-02).
Out: `Research/BatmobileGrab/BONES.json` + `.md` (bone, parent, pivot_jc3_m, face counts per
slot, split-weight count); face index lists outside the repo
(`E:\Modding\_BmAKgrab\bones\<bone>.npy`).
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
`E:\Modding\_BmAKgrab\audio\wav\` and measure each (duration, peak, integrated loudness LUFS).
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
at least one shipped vehicle that uses it. Decoded data goes to `E:\Modding\_JC3grab\`;
summaries and tables to `Research/JC3Grab/`. Use the existing readers (`jc3index.py`,
`tabextract.py`, `jc3grab.py`, `jc3detail.py`, `jc3adf.py`, `jc3hkx.py`, `jc3fx.py`) — extend
them; do not write a parallel reader.

#### G2-10 · Vehicle weapon catalogue (old WPN-1)   M · deps: P0-2 · serves: WPN-1…5, HUD-2
In: `Research/JC3Grab/INDEX.jsonl` (search `jc_weapons/06_vehicle`, `w6`), `tabextract.py`,
`jc3adf.py`, `jc3fx.py` (for `.ftune` explosion tunes), the 25 ids in §2.1.
Do: 1. List every archive path under `editor/entities/jc_weapons/06_vehicle/` and every
`jc_explosions/weapons/w6*.ftune`. 2. Extract each weapon `.ee` (and its inner `.wtunec` /
weapon tune files) to `E:\Modding\_JC3grab\weapons\`. 3. Decode every tune: fire rate, burst,
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
from `FX_TABLE.jsonl`), attachment point (socket), trigger (usage/weapon/damage state). Custom
`.effc` authoring is out of scope unless a card in B proves the writer.
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

#### T-22 · Collision translation (only if G2-30 succeeded)   M · deps: G2-30 · serves: DIM-4
Do: rows T-P3/T-CO2/T-CO3: hull set from the Batmobile body (convex decomposition parameters,
max hulls, convex radius), part hull bindings (`has_world_collision_shape`), stations unchanged
(R3).
Out: rows + `Working/Translation/t16_collision.json`.
Done: rows resolved; or closed as named omissions if G2-30 failed.

#### T-23 · Ledger close-out and build batches   S · deps: T-10…T-22 · serves: all
Do: 1. `t_rows.py check`, `status_audit.py --write` then `--check`. 2. Confirm `rows assumed`
= 0 except signed-off rows. 3. Extend `bmak_coverage.py` so weapons, animation, audio and
light features are covered (every G1 file row is assigned to a T row). 4. Write the build batch
list for phase B (which edits file goes into which build step).
Out: `STATUS.md` regenerated; `Working/Translation/BUILD_BATCHES.md`.
Done (gate TX): all checks green; every §1 feature code maps to ≥ 1 row; decisions D-1…D-10 are
answered or their rows are `blocked: D-n` with the user informed.

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
In: `BONES.json`, face lists in `E:\Modding\_BmAKgrab\bones\`, `bat_assemble.py`,
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

#### B-10 · Collision (only if T-22 resolved)   M · deps: B-02, T-22 · serves: DIM-4
Do: write the Batmobile hull set with `jc3hkx.py`; stations unchanged (R3).
Done: `jc3hkx.py check --all` on the built file; hull union bbox within 5 cm of the body bbox.

#### B-11 · Audio bank   M · deps: T-16 · serves: AUD-1…7
Do: per the G2-24 route: build a private bank (or a copy of `vehicles.bank` with swapped
samples) from the T-16 map; generate `.ee.fmod_guids`; weapon sounds per T-11.
Out: bank file(s) in the build tree; `Working/Audio/bm_bank_manifest.json`.
Done: every mapped event resolves; sample count/lengths match the manifest; the installer
handles and rolls back the bank (old AUD-5).

#### B-12 · Variants (only if D-2 = two variants)   S · deps: B-05…B-11, T-15 · serves: MOD-1/2
Do: `bm_build.py --variant pursuit|battle` builds both entities from one source; the only
differences are the rows in `t11_variants.json`.
Done: `aafdiff` between variants lists only the files the variant table names.

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
| D-1 | Tyre diameter: keep the PSKX true scale (1.366 m measured) or scale the **whole car** so the tyre reads 1.40 m? | G1-18 → `Research/BatmobileGrab/TYRES.md`: tread Ø1.365–1.3657, shoulder Ø1.371, all four wheels within 0.5 mm; 1.42 has no source (initial-commit docstring; the wheel `Disc` bone's own vertical extent is 1.427) | **resolved 2026-10-24: keep the PSKX true scale** — the condition failed: 1.366 does exclude the shoulder, but the bulge is 5.5 mm, so the tyre with its shoulder reads 1.371, still 2.0% short of 1.40; the missing 34 mm to 1.40 is not in the mesh, so rescaling would move ride height, track and body by 2.5% to chase a wiki estimate | DIM-2, T-G2 |
| D-2 | Pursuit/Battle: (a) two Rebel Drop entries, (b) one hybrid car, (c) research a runtime toggle first | G2-14, G2-21, G1-21 | **resolved 2026-10-28 (user): (b) one hybrid car** — a single Rebel Drop entry carrying both modes; pursuit/battle switching is borrowed from JC3 functionality and altered to match BmAK (B-12 `skipped: D-2`) | MOD-2, T-15, B-12 |
| D-3 | Weapon lethality: BmAK weapons are non-lethal to people (riot suppressor, drones are unmanned); JC3 weapons kill. Accept JC3 lethality, or limit the guns to vehicle targets where possible? | G2-10, G2-11 | **resolved 2026-10-28 (user): accept JC3 lethality, no toggle** — a non-lethal mode does not fit JC3 and would ruin battle mode; the riot suppressor stays a named omission | WPN-2, WPN-10 |
| D-4 | Donor chassis: keep `v0300` (the armed signature variant proves it can carry missiles) or move to a tank chassis for the turret? | G2-12, G2-13, `FLEET.md` | **resolved 2026-10-28 (user): whichever is easiest** → keep `v0300` (the current donor; the armed signature variant already carries missiles) and import turret wiring from the tank | B-04, B-05 |
| D-5 | Skins (MK2, Jokerfied) as extra drop entries, palette tints, or not at all | G1-20 | **resolved 2026-10-28 (user): skins as extra Rebel Drop entries** (MK2, Jokerfied, …) | APP-8 |
| D-6 | Standalone entity, or keep replacing the Serpente (which may put NPC Batmobiles in traffic) | G2-27, G2-29 | **resolved 2026-10-28 (user): standalone entity** (no Serpente replacement) | WLD-1/8, B-13 |
| D-7 | Weapon slots: which BmAK weapons take JC3's driver slots (cannon, Vulcan, missiles…) | G2-11 | **resolved 2026-10-28 (user): every BmAK weapon in both battle and pursuit modes** — no per-mode split; the slot count must carry all weapons (T-11 finds how, e.g. extra driver slots or mode-independent switching) | T-11 |
| D-8 | Water: BmAK's Batmobile is not amphibious. Sink and stall (lore), or JC3 default? | G2-31 | **resolved 2026-10-28 (user): lore** — sink and stall, Rico swims out | WLD-6 |
| D-9 | Can enemies pull Rico out of the Batmobile? | G2-18 | **resolved 2026-10-28 (user): no** — enemies cannot pull Rico out | T-13 |
| D-10 | JC3 gear mods (turbo jump, upgraded nitro tiers) on the Batmobile? BmAK cannot jump. | G1-21, `CustomLandGlobal` | **resolved 2026-10-28 (user): no JC3 gear mods** (no turbo jump, no upgraded nitro tiers); JC3 functionality may be borrowed and altered only so the Batmobile is 100% lore-accurate | HDL, T-B4 |

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
| G1-14 | done | `Research/BatmobileGrab/DAMAGE_RULES.md` + MODLOG §"G1-14 · Damage rules — done" (14 entry points: 5 native, 9 script; `HealthRecoverRate` read by one function) |
| G1-15 | done | `Research/BatmobileGrab/AUDIO_FEATURES.md` + MODLOG §"G1-15 · Audio by feature — done" (361 rows in 14 groups; 423/447 WEMs decoded to 48 kHz WAVs, 24 streamed voice lines carry no bytes on disk; 506 RTPC bindings over 261 objects) |
| G1-16 | done | `Research/BatmobileGrab/PARTICLES_FEATURES.md` + MODLOG §"G1-16 · Particles by feature — done" (206 systems in 17 groups, 63 distinct names, 1433 emitters; 1290 colour boxes, 5 external refs) |
| G1-17 | done | `Research/BatmobileGrab/LIGHTS.md` + MODLOG §"G1-17 · Light values — done" (36 Batmobile-rig components: colour 129/129, intensity 74/74 lights; 67 colours from the component, 62 from `Default__*`, `FColor` read BGRA; the walker's 32-byte GuidProperty fix re-opened 1,786 truncated records) |
| G1-18 | done | `Research/BatmobileGrab/TYRES.md` + MODLOG §"G1-18 · Tyre diameter — done" (all four tyres Ø1.365 tread / Ø1.371 shoulder / 0.732 wide; rim Ø1.025; 1.366 = physics radius ×2, 1.40 = wiki, 1.42 unsourced; D-1 resolved: keep the PSKX) |
| G1-19 | done | `Research/BatmobileGrab/COCKPIT.md` + MODLOG §"G1-19 · Cockpit and driver placement — done" (seat = slot 11 / dash = slot 10 on `Batmobile_Chassis`; `Driver` hip at (−0.003, 0.865, −1.065), 24 mm above the cushion; roof liner 1.101 m above the hip; derived eye point 1.655 / 1.705 clears the canopy by 0.21 / 0.15 m; centre screen 0.314 × 0.145 m; no yoke geometry in the hand box) |
| G1-20 | done | `Research/BatmobileGrab/VARIANTS.md` + MODLOG §"G1-20 · Skins and variants — done" (V2/MK2/Joker/Funhouse diffed: mesh LODs and bones, 65/55/64/63 sockets, 78/80/69/84 materials, 92/95/100/102 textures; `SimulationModel` identical in all four; Joker carries 6 gadgets vs 10) |
| G1-21 | done | `Research/BatmobileGrab/MODES.md` + `grab_modes.py --check` (26/26) + MODLOG §"G1-21 · Modes and transformation values — done" (107 declared family fields, 46 serialised with per-package values, 61 carrying no value in the files; T-BM1's (9)/(3)/(2) reconciled: 9 sim scalars + `BattleModeVSpeedCurve`) |
| G1-22 | done | `Research/BatmobileGrab/NATIVE_RELEVANCE.md` + `grab_native_relevance.py --check` (9/9) + MODLOG §"G1-22 · Native remainder relevance — done" (140/140 classified: 116 irrelevant = property decls, functions, states, FaceFX; 24 relevant = 7 script-class exports whose parent class the second pass decodes + 17 header-only components; 0 tags read, 96 native refs are pointers not values) |
| G1-23 | done | `Research/BatmobileGrab/FOOTAGE.md` + `grab_footage_gaps.py --check` (23/23) + MODLOG §"G1-23 · Footage and file answers — revised" (72 rows: 2 closed by file values — `HeatUpPerSecond` 0.0 means no overheat and the bloom is the decoded `InaccuracyVsTime` curve 0/0.5/1.5/2.5 s → 0/0/1.5/3.0; 1 measured on five captures in `C:\Users\User\Videos\Captures` — air time 1.251/1.183/1.200 s on three ramp jumps, PTS-based because the clips are VFR; 53 VALUE-NATIVE, 8 WRONG-SCOPE, 5 UNDOCUMENTED, 2 NOT-IN-CLIP, 1 NATIVE; 20 file-answered quantities untouched under R4) |
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
| G2X | done | `Research/JC3Grab/G2X.md` + `G2X.json` + `Tools/scripts/g2x_gate.py --check` (75 codes: 67 carrier with evidence, 8 proven absence; the 24 G2 readers + the P0-2 census re-run 25/25 green; 7 codes decision-gated by D-2/D-3/D-5) + MODLOG §"G2X · G2 exit gate — passed" |
| T-10 | done | `Working/Translation/T10_OPEN_ROWS.md` + `T10_OPEN_ROWS.json` + `Tools/scripts/t10_reopen.py --check` (16 rows: 5 superseded by T-11/T-12/T-15/T-17/T-18, 10 stay `out` each with a re-read proof file, T-HUD5 `blocked` for a narrower reason and naming T-11/B-05 as its unblockers; the proof scope is the 10 rows this card owns, the later-row census is printed not stored; ledger 105→122 rows then) + MODLOG §"T-10 · Re-open the `out` rows with the G2 evidence — done" + §"T-10 rework — done" |
| T-11 | done | `Working/Translation/T7_WEAPONS.md` + `t7_weapons_edits.json` + `Tools/scripts/t7_weapons.py --check` (14 rows = 12 WPN codes + the D-7 slot row and the D-3 decision record: 5 with a JC3 carrier, 6 named omissions, 3 blocked; 136 aspects with a class, 53 UNKNOWN; 3 edits + 6 structural + 6 withdrawn; carriers `w602`/`w603`/`w618`/`w619`, 2 driver slots; damage crosses as the 24:2 ratio to T-14; D-7 has no carrier for 11 weapons; D-3 resolved 2026-10-28 — JC3 lethality, no toggle, the riot suppressor a named omission) + MODLOG §"T-11 · Weapons translation — done" |
| T-12 | done | `Working/Translation/T8_PARTS.md` + `T8_PARTS.json` + `t12_parts.py --check` (15 rows = 11 cut parts + 4 no-part items: 12 with an animated joint, 4 with a shipped hinge, 3 static with a stored, check-asserted reason (P-02/P-05 translate, P-13 has no bone); the delivered JSON keeps `schema` 1 (`rows_schema` 2) so `bat_assemble.load_part_spec` still reads it; pivots re-derived through `bat_assemble.pivot_point`, max delta 1.3918e-05 m = BONES' own offset delta; turret +Y agrees with the tank hinge, canopy −X agrees with the donor hood but translates 72.5 cm, suppressor axis DISAGREES, Vulcan **6 turns / 2160° in 3.90 s** at 1229.5 °/s (a wrapped ±180° extent, not a limit), flaps 20/30° blade + 54.8° piston (both given, the child bone is labelled); 25 row-sequence pairs = 15 distinct clips; damage types from `PARTS_TABLE.dt`, land-first) + MODLOG §"T-12 · Moving-parts translation — done" |
| T-13 | done | `Working/Translation/T9_INTERACTION.md` + `t9_interaction.json` + `Tools/scripts/t9_interaction.py --check` (85 objects: 77 placed, every one 0.05-0.30 m from the nearest body triangle and outside the hull; 6 hijack objects dropped per D-9 = no; `Driver` socket 1; `interaction.seat.passenger1` UNKNOWN - one-seat cockpit; role anchors ray-cast on `body_lod1.rbm`: left/right cockpit side x -1.471/+1.462, front deck y 1.3606 at z -2.14, roof y 2.0811 at z -0.5; donor clearances 0.048/0.1474 m where G2-18 decoded them, 0.10 m chosen for the sides; tamper test caught and reverted) + MODLOG §"T-13 · Interaction translation — done" |
| T-14 | done | `Working/Translation/T10_DAMAGE.md` + `t10_damage_edits.json` + `Tools/scripts/t10_damage.py --check` (T-DM9 decided: option B - channels + `max_health` 36000, `invulnerable` stays 0; option A's `invulnerable` gate labelled unproven for a vehicle root; tank cannon 24/48/25 hits H0/H1/H2 vs the BmAK 24 with ARM-1 H0 and ARM-2 H1 printed as the two failing model cells, pending `Q1-DM-B`/`Q1-DM-A`; wheels at the fleet ceiling 400; ARM-5/ARM-6 named omissions; the stale `bullet_armor_strength` switch removed, `damage_audit.py` green, `max_health` switch pending the build; ledger T-DM1/T-DM9 `next`) + MODLOG §"T-14 · Damage and armour translation — done" + §"T-14 rework — done" |
| T-15 | done | `Working/Translation/T11_MODES.md` + `t11_variants.json` + `Tools/scripts/t11_modes.py --check` (D-2 hybrid: one row set, 15 rows = MOD-1 4 + MOD-2 11, compromise declared per row - `carried` 7 / `inside band` 1 / `omitted` 7; `BattleModeVSpeedCurve` 0->60, 600->40, 1200->30 and `TurningModeMaxSpeed` 600 cm/s = 21.6 km/h are named omissions, `ArmourModeDamageReduction` is 0 in every package, `BattleModeCamFOV` 60 sits inside the delivered 55-63 band, the battle lamps ride `HeadLight` because the fleet has no battle light behaviour, the Immobilizer is `blocked` for the disable it cannot carry (T-WP4), and BmAK's standard/boost torque curve is decoded from the G1 object stream; ledger 198 rows, `t_rows.py check` green) + MODLOG §"T-15 · Modes translation — done" + §"T-15 rework — done" |
| T-16 | done | `Working/Translation/T12_AUDIO.md` + `t12_audio_map.json` + `t12_audio.py --check` (53 rows = 45/45 donor events + 8 weapon/mode: 5 mapped with 5 chosen slots, 7 kept vanilla, 11 named omission, 1 remove, 29 blocked - 22 unnamed GUIDs by R4, A-01 pending Q-1 #8, A-04 unclippable at the shift slot, A-03/A-08/A-10/A-23 on D-10/D-8, W-08 on D-2; 34 slots decoded+measured, 22 gain-matched by measuring the written payload (0 chosen outside ±1 LU, 5 candidates outside and named: 3 gear-shift +3.5, nitro start -1.6, minigun endclick -16.8), 0 with an FSB5 loop field; event→tune stored 257/257 on both sides, tune→sample UNKNOWN, 24/45 tunes named; AUD-7 horn removed, AUD-3 named omission, nitro slots+spans proven by test-060 56/150/355) + MODLOG §"T-16 · Audio translation — done" + §"T-16 rework — done" |
| T-17 | done | `Working/Translation/T13_FX.md` + `t17_fx.json` + `Tools/scripts/t17_fx.py --check` (17 rows: 12 chosen `.effc`, 5 named omissions; FX-1…FX-4 4/4; 955 distinct fleet `.effc`, 85 on the donor `v0300` signature `.ee`, 8 sockets; rows in `T_ROWS.jsonl` as doc T-13; tamper 4/4 caught) + MODLOG §"T-17 · Effects translation — done" |
| T-18 | done | `Working/Translation/T14_LIGHTS.md` + `t14_lights.json` + `Tools/scripts/t18_lights.py --check` (28 rows = one per entry of the `Playable_Batmobile_SF` rig: 22 mapped, 6 named omissions; 18 distinct `SVehicleLight` targets = 11 of the donor's 21 shipped rows repointed at our sockets + the graph's unreferenced `Front_Secondary_Head` (T-L5's battle spot) + 6 custom `preset_id 0` entries (2 wheel arches + battle arch + 2 battle heads + boot); the two head clusters per side are the donor's `_01`/`_02` pairs; wheel arches close T-L4/T-LG4 through G2-33 §7 on new `sportsmuscle_wheel_f_*_arch` parts at parts 42/43; forensics rig + the two absent `HeadLight*c` flare sockets + the muzzle spot are the omissions; colours adopted from `LightColor`/255, cone/brightness reported not converted (no unit bridge); 21 donor rows / 22 objects / 20 presets resolve / 2 unreferenced; rows in `T_ROWS.jsonl` as doc T-14 (ledger 122→150); 3 tampers caught) + MODLOG §"T-18 · Lights translation completion — done" |
| T-19 | done | `Working/Translation/T6_HUD_CAMERA.md` §1a + `t19_hud.json` + `Tools/scripts/t19_hud.py --check` (T-HUD5 completed: 10 rows over 5/5 G2-25 elements, 6 map / 2 partial / 2 out, 12 proofs; T-HUD1…3 kept; heat = stated absence both sides, lock-on marker only, accuracy-frame scale UNKNOWN) + MODLOG §"T-19 · HUD translation — done" |
| T-20 | done | `Working/Translation/T15_WORLD.md` + `t15_world.json` + `Tools/scripts/t15_world.py --check` (19 rows, 8/8 WLD codes: 5 `next`, 6 `keep`, 3 `epe`, 3 `blocked`, 2 `out`; `BaseName` = `hash_jenkins(<family prefix>)` on 45/45 drops; the new leaf name hash 443190071 resolves in 0/11 languages, so the name and blurb pairs are `blocked` for lack of a `.stringlookup` writer; ledger 164→183, `t_rows.py check` green) + MODLOG §"T-20 · World translation — done" |
| T-21 | done | `Working/Appearance/APPEARANCE_PLAN.md` + `appearance_plan.json` + `Tools/scripts/appearance_plan.py --check` (172/172 classified: 23 bake POL-2, 8 route, 141 drop, 0 unclassified; POL-1 interior 6 slots all samplers bound; POL-2 bake is the only build work; skins per D-5) + MODLOG §"T-21 · Appearance completion — done" |
| T-22 | done | `Working/Translation/t16_collision.json` + `Tools/scripts/t22_collision.py --check` (7 donor hull slots from the 11 driveable BmAK boxes: body 1, 2 doors, 4 wheels; 21 boxes are wreck-only and the 11 T-8 parts have no slot; 54 hulls, one per part, convex radius 0.01 m x k; wheel k 1.660052 = tyre 1.3654 m / 0.8225 m; body hull 3.495x2.032x6.167 m at k 1.676259; 38/42 parts carry `has_world_collision_shape`, the 4 wheels 0 with body -1; 0 station quads in the file, stations untouched; rows T-P3/T-CO2 `next`, T-CO3 `keep`; 4/4 tamper tests) |
| T-23 | done | `Working/Translation/BUILD_BATCHES.md` + `build_batches.json` + `Tools/scripts/t23_closeout.py --check` (gate TX: 75/75 §1 codes mapped, 0 unmapped - 62 carried / 9 named omission / 4 blocked; 198 ledger rows; rows assumed 1 of 180 and it is the signed-off T-E5; D-1…D-10 10/10 answered; 14 payloads over the 14 B steps, `t19_hud.json` the one payload no step writes) + `bmak_coverage.py --check` (777 G1 feature rows -> 34 T rows, 0 unassigned) + MODLOG §"T-23 · Ledger close-out and build batches — done" |
| B-02 | done | `Working/Appearance/build_parts/parts_manifest.json` + `Working/Translation/T8_PARTS.md` + MODLOG §"B-02 · Part split — done" (silhouette 99.97 %, 0 lost faces, 4791/4915 KB) |
| B-01 | done | `Builds/bm-001/receipt.json` + `Tools/scripts/bm_build.py --check` + MODLOG §"B-01 · Build scaffold — done" (identity control: bm-001 `.ee` 10,737,057 B `6AB8275F…` and `.toc` 50,643 B `444ED479…` byte-identical to test-091's, 506 `.toc` records, 0 edit rows; the applier path proved on a deleted probe build — `.ee` +1 byte, aafdiff exactly 1 module; 2/2 tampers caught) |
| B-03 | done | `Working/Appearance/build_lights/lights_manifest.json` + `python Tools/scripts/spec_check.py --lights Working/Appearance/build_lights` + MODLOG §"B-03 · Emissive `CarLight` blocks and light parts — done" (8 lamp parts / 24 RBMs, 4,576 Emissive faces cut into head lamps, 4 arch lamps and 2 tail strips, 21 T-18 rows hosted, 3 LODs per lamp, 24/24 CarLight blocks byte-identical to the cloned header, 288.6 KB lights / net 4,899.6 of 4,915 KB, 3 rig lamps with no faces measured; 4/4 tampers caught) |
| B-04 … B-14 | todo | |
| V-01 … V-07 | todo | |
| Q-1 … Q-5 | todo | |
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
