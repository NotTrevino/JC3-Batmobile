# JC3 Batmobile — Engineering Plan and Backlog

> **2026-10-24: the single backlog is now [GRAB_BACKLOG.md](GRAB_BACKLOG.md) (unified).** This file is kept as history and evidence; for *what to do next*, follow the unified backlog.

**Status:** rewritten 2026-10-21 from the live project state, then reprioritised the same day: **the
GRAB step is the gate**. Nothing is tuned by hand and nothing is tested in game until the whole BmAK
Batmobile (every package, object, material, texture, mesh, socket, animation, sound, particle, weapon
and the vehicle/sim classes) has been read out of the shipped files by a re-runnable script and
documented as "what does what". The last four builds (078–081) were manual constant edits; that path
is lifted: GRB-1…GRB-11 are closed (§0.6), so appearance builds may resume from the grab-derived values.
**Gate, second half (2026-10-22):** GRB-1…GRB-11 closed BmAK's *inventory*, but the **JC3 side was
never grabbed** — 1 of 232 vehicle entities is decoded in depth, and 14 of vanilla v0300's 31 modules
have never been opened. Handling and appearance work was therefore guessing at targets. The order
was **G1 (finish BmAK) → G2 (grab JC3) → T (translate) → build once**, with the full picture in
[GRAB_BACKLOG.md](GRAB_BACKLOG.md). **That gate is now closed (2026-10-23):** G1 is 423/423 fields,
G2 is 99.999% of entries, the translation ledger is 97/113 in-scope rows resolved (85.8%), and
test-085 carries 35 values. **test-087 failed and is withdrawn** (2026-10-23): its damage rows
translated the Batmobile's ram *attack* as collision *defence* and turned impact damage on. The
chain is in `Working/Translation/POSTMORTEM_DAMAGE.md`; the dropzone was restored to test-085 and now carries **test-088** (Batch B2 on top of it). The
next build is the six handling values in `t5c_edits.json`, not cleared until each has a behaviour
and a take that can fail. Probes that answer architectural questions are still allowed (test-083
is one).
The whole translation is now mapped before it executes — stages, batches, verification gates and
the improvisation register — in [Working/Translation/T_PLAN.md](Working/Translation/T_PLAN.md).
**Scope:** a lore-accurate Arkham Knight Batmobile, drivable in Just Cause 3 single-player, spawned
from a **new Rebel Drop entry called "Batmobile"** (RD-1; reference implementation in
`Research/1456340180_Rebel-Drop-Mod-V5.3`). The Kerner Serpente R
(`v0300_car_kensington_sportsmuscle`) is the **donor/spawn convenience** — Rico spawns beside it at
Mario's house, so every test launch is instant — not a design constraint; the donor may change once
the G2-4 distributions can be compared.
**Method (revised 2026-10-23, after test-087):** a value's provenance is not a translation. A row
with no semantic bridge is `blocked`, never `class`; a build value outside the shipped range is a
declared switch, not a value (`damage_audit.py`); and a requirement is carried by a *behaviour* row
with a take that can fail, not by the member that sounds closest. See `POSTMORTEM_DAMAGE.md` §8.
Every claim below is tied to a file, a tool run or a MODLOG section. Anything unproven is
labelled **UNKNOWN** and appears in the risk/gate sections instead of the backlog as if it were known.

**How to use this document:** §0 is the measured starting point · §3 is the phase order · §4 is the
schedulable task table (IDs, dependencies, oracles) · §6 lists the gates that must be answered before
anything downstream can be planned · §7 records what not to repeat.

---

## 0. Verified state (2026-10-21)

### 0.1 What is live in the game right now

| Item | Value | Evidence |
|---|---|---|
| Live dropzone build | **test-088 (installed 2026-10-23)** — Batch B2's 4 values over 3 rows, packed on test-085, so the live pair still carries test-085's 35 values over 16 rows: 35/35 and 4/4 read back through the `.toc`. `.ee` `5A79D8859D0DCD6D…79DF556F7860` (10,736,878 B), `.toc` `4FD6DB3C1E2B7DB9…C88541A0` (50,573 B). test-086 (camera probe) was driven and its values withdrawn — **not** installed | `install.ps1 -Action Status` == test-088's receipt; `verify_install.py` 9/9, run 2026-10-23. The same day's deploy test first found the dropzone still holding **test-087's** `.ee` (the postmortem rollback had never run); it was restored to 085 before 088 was packed on it |
| Appearance build underneath | **test-082** (BUD-1: body lod1 44,608 tris, footprint 4,764/4,915 KB) | MODLOG §111 |
| Post-install proof | `verify_install.py`: **9/9 checks**, installed pair read through its `.toc` | MODLOG §105–§106 |
| Rollback points | **test-083** (`Builds/test-085/install.ps1 -Action Rollback083`), **test-082** (full appearance build, no probe), **test-081**, **test-080**, **test-079**, **test-078**, **test-077**; raw 077 copy in `Builds/_rollback/pre078/` | `install.ps1 -Action Rollback<one of those>` |
| Extra dropzone file | `sound/fmod_banks/vehicles.bank`, 210,781,376 B (nitro swap from test-060) | `D:\Games\Just Cause 3\dropzone\...` |
| Body mesh | Batmobile, true scale: 3.495 × 2.271 × 7.026 m, wheelbase 5.029 m, tyre Ø1.37 m, lod1 **44,608 tris** (31,139 until BUD-1, MODLOG §111) | MODLOG §70, §111, `Working/TrueScale/` |
| Body materials | **17 blocks per LOD** (16 `CarPaintMM` + 1 `Window`), 28 Batmobile textures; 200 `CarPaintMM` + 35 `Window` blocks across 35 meshes; body/arches/undercarriage/turret albedo `0x837d86` (linear ×4), gloss 0.45 | `verify_install.py` on the installed `.ee`, MODLOG §107 |
| Appearance look | 078 **flat black** (linear colour in an sRGB slot, byte 14 vs 67) → 079; 079 **wet black mirror** → gloss 0.45 in 080; 080 **too dark for daylight** (body lum 12–16 vs grass 85, while the reference car is brighter than its road) → albedo ×4 in 081. Verdict on 081 pending | user screenshots + measured, MODLOG §105–§107 |
| Body geometry integrity | silhouette **99.9%** of the full-resolution source (215,893-face body split → 44,602 rendered tris); holes **0.297%** of the silhouette (interior tears 0.051%) vs 0.471%/0.102% at 31,133 tris; winding agrees with normals 99–100% | MODLOG §106, §111, `Tools/scripts/silhouette_check.py` |
| Parts | 7 parts: body, 4 wheels, 2 doors | strings of the live `.epe`; the vehicle itself has **42** part indices — 40 `CPartProp` plus `hood_signature`/`missile_base_signature` — read from `DeformPoints`, 40/40 agreeing with the graph (`Research/JC3Grab/PARTS.md`) |
| Physics | stations + radius/width/clearance moved with the mesh, `land_global` 1,600 B patched, `physicsc` quads moved | MODLOG §70 |
| Handling | 075's values are live but **rejected**: understeer survived. HP-1…HP-5 stay parked, but their targets now exist: JC3's shipped distributions are decoded — 52 module types, 1,421 members, min/median/max across 232 vehicles (`RigidBody.mass` 50…550,000, median 3,000; donor 975) | MODLOG §95, §115, §117, [Research/JC3Grab/VOCABULARY.md](Research/JC3Grab/VOCABULARY.md) |
| Damage | tank header profile + `bullet_armor_strength` 100; **still dies to "a couple of mags"** | MODLOG §99 |
| Audio | engine loop/start decoded, nitro sample swap live; **no dynamic mapping yet** | `Working/Audio/CHECKLIST.md` |

**The single most important state fact:** the per-material appearance build (19 materials, 17 body
blocks, Batmobile textures) is **live** as test-079. It had been deployed once as test-066 and lost
when test-067 rebased on test-061 for the damage work (MODLOG §80–§81); recovered as 078, then found
to render **flat black** in game and corrected as 079 (MODLOG §105). Both regressions now have a
standing guard: golden-hash rebase guard (`deploy.py`), receipt-stamped installers, a post-install
verifier that reads the deployed pair through its own `.toc` (9/9), and an offline renderer
(`preview_rbm.py`) that catches "hash-perfect but visually wrong" before a deploy.

**What the last two days proved:** byte-exact verification does not imply a correct picture. The 078
build passed every check and still looked black, because the failure was a *colour-space* choice in a
generated constant, not a missing or corrupt asset. That class of bug is now tested where it is cheap:
the generated-value path (`srgb8`), the offline render, and the in-game screenshot.

### 0.2 What is built, installed and verified offline

`Working/Appearance/build` — produced by `Tools/scripts/appearance_pipeline.py` — packaged as
**test-081** by `Tools/scripts/deploy.py` (hash-pinned, receipt + installer + Verify + Rollback080)
and installed into the live dropzone on 2026-10-21 (superseding 078, whose albedos were re-encoded, 079,
whose gloss was re-tuned, and 080, whose albedo was too dark for daylight):

- 25 RBMs (5 parts × 5 LODs), every one byte-identical on re-encode.
- 19 materials mapped to JC3 blocks, 0 unhandled BmAK factors, 0 silent template values (`spec_check.py`: 185 blocks).
- 28 textures converted (BC1/BC5/BC3), glass now a real **BC3/DXT5** Window dif (alpha = Glass_A × 1.2, mean 193 vs vanilla 204) + normal, bound on all 5 body LODs.
- Generated albedos + the glass tint are **sRGB-encoded** from their linear BmAK params (`factors.srgb8`), and the paint albedo carries a **linear ×4 gain** (`PAINT_ALBEDO_GAIN`) for daylight readability; the body is `0x837d86` (was `0x0e0d0f` at 078). Gloss is capped at 0.45 (`PAINT_GLOSS_CAP`). MODLOG §105, §106, §107.
- `preview_rbm.py` renders the staged body offline in side/front/top views, with `--albedo` shading from the real dif means.
- **Model budget (BUD-1, MODLOG §111):** body lod1 at 44,608 tris; staged footprint **4,764 / 4,915 KB**
  against the game's own Model HARD cap (`--budget-safety 1.0` is now the default; the old ×0.9 guard
  = 4,424 KB survives as a flag). Staged in `Working/Appearance/build_bud1`, packaged as **test-082**.
- Transfer score: **339 components, 167 transferred, 36 partial, 0 missing, 136 no-JC3-slot.
  54.6% weighted · 49.3% strict · 91.1% of everything JC3 can hold** (`Working/Appearance/progress.md`).

### 0.3 What the project's own evidence says about remaining gaps

| Gap | Evidence |
|---|---|
| Lights are not wired to the Batmobile | the vanilla lights module maps `HeadLight`/`TailLight`/`Signal` to **vanilla part names and `_LIG` bone paths** our 7-part `.epe` lacks. The grab now supplies the real anchors: 65 sockets with bone + relative location, including `HeadLight2a/2b`, `LWheelLight`, `RWheelLight`, `BrakeLightL` (GRB-4) |
| Damage is not reaching the armour | `sportsmuscle_vehicle_parts.vmodc` (42 parts, 17 damage types) now readable; `Land_Wheel` 1020/400/100 with `instantly_damaged_by_bullets=1` vs tank 1000/500/100/0 (MODLOG §101) |
| No weapons | the Batmobile `.epe` has `SVehicleLights`/`SEffects` only; the tank `.epe` proves `CBulletWeaponBase` + `SWeaponPoint` (`turret_anchor`) + `CForcePulse` are entity components |
| No moving parts | `VehicleParts` has 11 arrays (`hinged_parts`, `rotating_parts`, `fin_parts`, `aim_part_constraints`, `skinned_parts`...); the Serpente has only `parts`, `wheel_parts`, `door_parts` populated |
| No Batmobile audio mapping | 132/132 WEMs decoded, 9 starter pairs in `EVENTMAP.md`. The grab found the banks inside the vehicle packages: `BML_Engine` 7.28 MB, `BML_Burnout` 477 KB, `AUX_InBatmobile`, `VEH_Batmobile_MK2_Engine` 7.14 MB, plus 361 AkEvents and RTPC names (GRB-4, `AUDIO.md`) |
| Handling numbers **were** called unavailable — now contradicted | §0.6 probe: `RVehicleSimBatmobile SimulationModel` exposes named structs and floats directly (curves + 600/500/750/3000/24000/100000). Only offset-serialized primitives lack names; complex properties do not. GRB-4 must read them all, HDL-1 is no longer a CDO-walk problem |
| Parts/deform edits would be silent | the vanilla `.toc` lists `vehicle_parts` and `vehicle_deform` at offset 0 (read from the archives): any edit to those files must add `--internal` to the `eetoc` patch or the game keeps the archive copy (MODLOG §103c) |

### 0.4 What a JC3 vehicle actually is (the feature map)

Every Batmobile feature must attach to one of these, and every module below exists per vehicle:

```
.epe  entity  ── components: CCar, parts, lights (SVehicleLights), effects (SEffects),
                 camera ref, weapons (CBulletWeaponBase / SWeaponPoint / CForcePulse)
.vmodc modules ── health, vehicle_common, vehicle_parts, vehicle_deform,
                  rigid_body, suspension, land_steering, brakes, land_aerodynamics,
                  buoyancy, water_interaction, land_engine, transmission, vehicle_misc,
                  custom_land_global, custom_velocity_damper, decals, palette,
                  land_audio, lights, effect_attachments, stunt_areas, ai
animations      ── jc_skeletons/vehicles/*.bsk + jc_statemachine/vehicles/vehicle_null.*
models          ── part RBMs + .lod tables + .physicsc
audio           ── .ee.fmod_guids + FMOD bank
camera          ── jc_cameras/vehicle_cameras/<vehicle>.ctunec
```

This map is the backbone of the backlog: **no feature is scheduled without naming the carrier file.**

### 0.5 Feature status matrix

`LIVE` = in the current dropzone (a build can be live and still unproven visually - see DEP-1's oracle) ·
`STAGED` = verified offline and packaged in a build, **not** installed ·
`PARTIAL` = some carrier exists but the feature does not work end to end · `PROTOTYPE` = value
edited, oracle not passed · `FAILED` = tried in game and rejected · `BROKEN` = carrier exists but
points at the wrong data · `VANILLA` = still the donor's data · `NOT STARTED` · `BLOCKED` = needs a
decision or missing data first.

| # | Feature | Status | Carrier | Backlog |
|---|---|---|---|---|
| 1 | Vehicle spawns and drives as the Serpente | LIVE | `.ee` + `.toc` replacement | — |
| 2 | Batmobile body at true scale, 5 parts | LIVE | body + 4 wheel RBMs, `sportsmuscle_vehicle_parts.vmodc` | — |
| 3 | 19-material appearance (17 body blocks) | LIVE (test-081; albedo, gloss corrected from three in-game measurements; daylight look unconfirmed) | installed `.ee` | DEP-1 ✅, ALB-1 ✅, MAT-1 ✅, ALB-2 ✅ |
| 4 | Batmobile textures incl. BC3 glass | LIVE (28 referenced, byte-identical to aaf; glass tint 0.05 linear -> 63 sRGB) | 28 `.ddsc` in the `.ee` | DEP-1 ✅ |
| 5 | Five LODs per part | LIVE (17 blocks × 5 body LODs, 5 × 30 wheel files) | `.rbm` | DEP-1 ✅ |
| 6 | Interior, cockpit, seat, power cell | PARTIAL | material blocks | POL-1 |
| 7 | Emissive / CarLight emitter | NOT STARTED | `CarLight` RBM block | LGT-2 |
| 8 | Headlights, tails, brake, signals | BROKEN (module points at vanilla parts) | `*_lights.vmodc` + parts `has_lights` | LGT-1 |
| 9 | Armour header (tank profile) | PARTIAL (dies to mags) | health module | DMG-1, DMG-2 |
| 10 | Per-part damage routing | PARTIAL (42 parts, medium rows) | `vehicle_parts.vmodc` | DMG-3 |
| 11 | Deform / crumple | NOT STARTED | `vehicle_deform.vmodc` | DMG-5 |
| 12 | Mass 4,000 kg + inertia | LIVE (inferred value) | `rigid_body.vmodc` | HDL-5 |
| 13 | Top speed / gearing | PROTOTYPE, oracle failed | transmission, `vehicle_misc` | HDL-5 |
| 14 | Yaw / understeer | FAILED (4 rejected value sets) | `custom_land_global`, steering | HDL-3, HDL-4 |
| 15 | Suspension / ride height | PROTOTYPE (launches off bumps) | suspension module | HDL-2 |
| 16 | Nitro / afterburner | LIVE (sound); behaviour unverified | `custom_land_global` tiers, bank | AUD-2, MOD-4 |
| 17 | Pursuit Mode as a state | NOT STARTED | — | MOD-1, MOD-2, MOD-4 |
| 18 | Battle Mode as a state | BLOCKED (no native toggle found) | — | MOD-1, MOD-3 |
| 19 | Machine gun | NOT STARTED | `.epe` weapon component | WPN-2 |
| 20 | Cannon / missile | BLOCKED (no suitable weapon catalogued yet) | `CForcePulse` | WPN-1, WPN-3 |
| 21 | Turret aiming | NOT STARTED | `aim_part_constraints` | PRT-4 |
| 22 | Aero flaps / missile bays | NOT STARTED | `hinged_parts`, `fin_parts` | PRT-2, PRT-3 |
| 23 | Jet nozzle spin | NOT STARTED | `rotating_parts` | PRT-3 |
| 24 | Exhaust / trail effects | NOT STARTED | `effect_attachments.vmodc` | FX-1 |
| 25 | Engine start + loop audio | PARTIAL (decoded, not wired) | `land_audio` + bank | AUD-1 |
| 26 | Turbo audio | LIVE (hardcoded sample swap) | `vehicles.bank` | AUD-2 |
| 27 | Battle-mode audio | BLOCKED (bank unlocated) | bank hunt | AUD-3 |
| 28 | Vehicle camera | WITHDRAWN (test-086 rejected; boom composition blocked) | `vehicle_cameras/*.ctunec` | CAM-1 |
| 29 | Controls | VANILLA (no mod-side binds) | engine | — |
| 30 | Water / amphibious | NOT STARTED | `buoyancy`, `water_interaction` | EXP-1 |
| 31 | Rebel Drop entry | LIVE (replaces the Serpente) | entity path | EXP-2 |
| 32 | Display name / icon | VANILLA ("Serpente") | stringlookup, UI | POL-3 |
| 33 | Standalone vehicle (own entity) | NOT STARTED | `settings\*.bin` registry | EXP-2 |
| 34 | Packaging / distribution | NOT STARTED | installers, README | EXP-4 |

### 0.6 GRAB is the gate (decision 2026-10-21, supersedes tuning-by-screenshot)

**Rule:** GRB-1…GRB-11 are green, so the inventory gate is closed. No appearance constant is edited by
hand: paint, glass and emissive values come from `VALUES.json`, and the light/audio/slot tables come from
`grab_lights.py` / `grab_audio.py` / `grab_slots.py`. The last four appearance builds changed one constant at a time (albedo encoding, gloss
cap, albedo gain) and each needed a manual screenshot to judge — that is the failure mode this section
ends. Every number a build uses must first be *read from the shipped Batmobile files* by a script that
can be re-run on any package.

What the files already proved is readable (2026-10-21 probe, `Playable_Batmobile_SF.upk`):

- **5,490 exports / 3,151 names / 649 imports** in the appearance package alone, across 161
  Package objects; class census includes **45 Material, 33 MaterialInstance, 3 SkeletalMesh, 92
  Texture2D, 37 AnimSequence, 2 AnimSet, 1 AnimTree, 65 SkeletalMeshSocket, 7 AkBank, 91 AkEvent,
  1 AkVehicleSound, 59 ParticleSystem, 18 ApexGenericAsset, 1 PhysicsAsset, 4 SVehicleWheel, 32
  RB_BodySetup, 1 RVehicleBatmobile, 1 RVehicleSimBatmobile** and the whole Batmobile weapon set.
- Arkham packages store properties as `int16 type + uint16 class-offset`, simple values inline and
  complex values by name. **Named** properties are therefore recoverable, and the sim archetype
  yields real names and numbers: `BoostTorqueVSpeedCurve`, `StandardTorqueVSpeedCurve`,
  `BattleModeVSpeedCurve`, `StandardSteeringSpeedCurve`, `TorqueVSpeedCurve`, `SteerSpeedVsSpeedCurve`.
  The earlier miss was `StrProperty` (type 13): one variable-length string aborted the whole tag walk,
  so every archetype carrying a string looked "native". With strings handled, all four
  `RVehicleBatmobile` and all 49 `RBatmobile*` objects decode; the remaining primitives keep their class
  offset (31 top-level values per sim: `0x2C4=600`, `0x2F4=500`, `0x304=3000`, `0x394=24000`,
  `0x190=100000`). This contradicts §0.3's "handling numbers unavailable".
- **The battle-mode bank is in this package:** `BML_Engine` (7,278,764 B), `BML_Burnout` (477,026 B),
  `AUX_InBatmobile`, 91 AkEvents and `AkVehicleSound VehicleSound_0` — the AUD-3 hunt was looking in
  the wrong place.
- Components/mechanics are ordinary objects: `RVehicleBatmobile Batmobile`, `RVehicleSimBatmobile
  SimulationModel`, `SVehicleWheel WheelFL/FR/RL/RR`, `RBatmobileCannon Batmobile_Cannon_V2`,
  `RBatmobileHeavyCannon`, `RBatmobileMissileLauncher`, `RBatmobileEMP`, `RBatmobileEMPMissile`,
  `RBatmobileSonar`, `RBatmobileWinch`, `RBatmobileVehicleTracker`, `RBatmobileBooster`,
  `RBatmobileAllegianceSwitcher`, `RBasicProjectile`/`RBatmobileMissile` projectiles.

The grab is therefore an *inventory + decoder*, not a screenshot loop:

| ID | Pri | Task | Effort | Oracle |
|---|---|---|---|---|
| **GRB-1** ✅ | P0 | `Tools/scripts/upk_read.py`: chunked-package reader (names/imports/exports, Batman property tags, object refs, recursive struct/array decode) | M | **DONE 2026-10-21** — 5,490/5,490 exports of `Playable_Batmobile_SF.upk`; class census equals `umodel -list` on 12/12 classes; sim curves and nested curve points decode |
| **GRB-2** ✅ | P0 | `Tools/scripts/batmobile_grab.py`: discover every Batmobile package, dump every export to `Research/BatmobileGrab/objects.jsonl`, classify by class, hash each file | M | **DONE 2026-10-21** — 15 packages, **20,128 objects**, 19,203 decoded (95.40%), 925 untagged; 14/14 checks against UEViewer's own listing |
| **GRB-3** ✅ | P0 | Material/texture graph: parent chain, scalar/vector/texture parameters, which texture feeds which slot | M | **DONE** — `MATERIALS.md` (185 masters + 130 instances, slots→expressions, params), `TEXTURES.md` (405 textures, dims/format, which instance+parameter binds each) |
| **GRB-4** ✅ | P0 | Mechanics graph: vehicle + sim objects with named properties and values, wheels, physics asset/bodies, sockets, anim sets/sequences/notifies, weapon archetypes + projectile links | L | **DONE** — `MECHANICS.md`: 4 sims with 24 named curves and points, 16 wheels with their particle refs, 12 meshes, 247 sockets with bone+location, 101 `VehicleLights` structs, 253 anim sequences, 32 collision bodies, weapon gadget meshes; `AUDIO.md`: 30 banks, 361 events |
| **GRB-5** ✅ | P0 | Completeness gate: per-package counts, decoded/undecoded ratio, dependency closure, `GAPS.md` listing what cannot be decoded and why | S | **DONE** — every object accounted for; 925 untagged objects named with their class and reason; 14/14 verification checks pass |
| **GRB-6** ✅ | P0 | Re-derive every constant the pipeline currently hardcodes (paint gloss/metallic/albedo, glass, emissive) from the grab; delete the manual constants | S | **DONE** — `grab_values.py` derives `VALUES.json` from the authored `Material0_BaseColour` + `Diffuse_Adjust` and the vanilla paint block; `factors.py` reads only that file (`GLASS_TINT`/`GLOSS_CAP`/`ALBEDO_GAIN`/`VALUES["emissive"]`); no hand-set `PAINT_*` remains |
| **GRB-7** ✅ | P0 | `Tools/scripts/grab_model.py`: schema-versioned query layer that every later step reads instead of parsing JSON by hand; the manifest resolves FNames, object refs and ByteProperty enum FNames inline; `check` re-validates it | S | **DONE 2026-10-23** — schema 6; `check` passes with 24 sim curves, 247 sockets/90 names, 101 light entries with socket→bone + `VEHLT_*` type + component classes (6 orphan sockets explicit), 30 `AkBank` objects (16 names) and the offset-only float `0x1214 = 640000` spot-verified |
| **GRB-8** ✅ | P1 | Lights wiring: `VehicleLights` entry → socket → bone → component class → JC3 part/behavior, one generated table for LGT-1 | M | **DONE 2026-10-21** — `grab_lights.py` writes `LIGHTS.json`/`.md`: 101 entries on 4 rigs, 95 resolve to bones in `Batmobile_V2.pskx`, 6 are the shipped `HeadLight1c/2c` orphans (explicit), 0 missing bones, every component class mapped or `no-jc3-equivalent`; behavior from `VEHLT_*` (mapped 54, approximated 23, no-equivalent 16, inferred 8); JC3 part + vanilla field values per behavior; every anchor flagged `needs-lig-bone` for LGT-1 |
| **GRB-9** ✅ | P1 | Audio map: 361 `AkEvent`s → bank → WEM, replacing the 9 hand-picked pairs in `EVENTMAP.md` | M | **DONE 2026-10-21** — `grab_audio.py` walks HIRC (Event → Action → Sound/RanSeq/container → DIDX) over 27 unique banks (15 vehicle packages + `Engine.upk`): 239 rows resolved to embedded WEMs (74 ids, 447 WEMs, 18.2 MB), 24 streamed, 8 no-media, 90 rows (26 ids) listed `missing-bank` with the 10 absent banks named |
| **GRB-10** ✅ | P2 | Mesh structure: LOD → material slot order → texture set, read from the SkeletalMesh export so slot→material is not assumed | M | **DONE 2026-10-21** — `grab_slots.py` writes `SLOTS.json`/`.md`: 19 slots agreeing across umodel `Materials[19]`, the pskx `MATERIALS` chunk and `assembly.json`; 299,837 LOD0 faces, all 19 slots draw geometry, 13 instances + 6 masters resolved in `MATERIALS.md`, 3 LODs with identity material maps |
| **GRB-11** ✅ (closed) | P2 | Name the last offset-only primitives on `RVehicleBatmobile`/`RBatmobile*` | M | **CLOSED 2026-10-23** (`OFFSETS.json` schema 3): **423 fields / 2,593 occurrences over 15 classes**, **423 named** (380 from the BmSDK-AK class dump, 40 struct elements, 3 `VehicleLights`), **0 undecidable**. The total is 423 because `RBatmobileCannon 0x0004` was two members in two nested structs; the last eight bool/float fields were resolved against the innermost struct and the packed bool word (`bits`, grab schema 6). `BmScript` is absent; the executable carries 341 native functions for these classes and 0 class-qualified property strings (`REGISTRATION.md`). The camera's boom composition is *not* part of this field set — see `Research/BatmobileGrab/CAMERA.md` |

**Result 2026-10-21 (`Research/BatmobileGrab/`).** The grab is complete for what the cooked files
expose — **95.4% of exports** (19,203 / 20,128; 925 native/untagged, 696 of them 2-byte stamps) and
**100% of offset fields named** (423 / 423). The camera boom composition is the known miss: the
values are authored (`DrivingCamConfig1/2`, 400/400 cm) but the native combination is not decoded. It
reads, without umodel or any hand list, through one supported API
(`grab_model.py`; `python Tools/scripts/grab_model.py check` re-proves the numbers below):

- **Simulation (the handling source):** 4 `RVehicleSimBatmobile` objects with 24 named curves and
  points, e.g. `BoostTorqueVSpeedCurve` (-1500→0, -300→200, 0→260, 1500→260, 2100→220, 2800→200,
  3000→150); `StandardTorqueVSpeedCurve` (…0→200, 750→170, 1600→150, 2100→105);
  `BattleModeVSpeedCurve` (0→60, 600→40, 1200→30); `StandardSteeringSpeedCurve` (0→60 … 2000→20);
  `SteerSpeedVsSpeedCurve` (0→720, 3500→720). Named scalars are read where the cooker kept the name;
  the rest stay as class-offset values (e.g. `0x1214 = 640000`) so GRB-6 can use them without inventing
  a field name.
- **Attachment anchors (the lights/weapons blocker):** 247 decoded sockets across the three meshes,
  65 on `Batmobile_V2`, with bone and relative location — `HeadLight2a/2b`, `LWheelLight/RWheelLight`,
  `BrakeLightL`, `CannonMuzzle`, `ChainGunMuzzle`, `RiotSuppressorMuzzle`, `BattleModeSpotLight`,
  `MissileL/MissileR`, `Afterburner`, `Afterburner_Front`, `WinchOrigin`, `Driver`.
- **Light rigs:** 101 `VehicleLights` structs across the four vehicles, each now socket → bone (read from
  `Batmobile_V2.pskx`) with its `VEHLT_*` type, `VEHLTMAT_*` material and component classes. GRB-8's
  `LIGHTS.md` is the JC3 table: 95 place correctly, 6 point at sockets the shipped mesh never defines.
- **Audio (the bank hunt):** 361 AkEvents resolved through HIRC over 27 unique banks (the vehicle
  packages plus `Engine.upk`): 239 rows → 447 embedded WEMs (18.2 MB), 24 streamed, 8 no-media, and 90
  rows whose banks (`BML_Sonar`, `BML_Impacts`, `BML_Batmobile_Subjective`, tank/UI banks) are not on
  disk — all named in `AUDIO_MAP.md`. RTPC names (`RPM`, `BML_Speed_Global`, `RevLimiter`, …) stay as
  the parameter side.
- **Components:** 4 `RVehicleBatmobile`, 4 sims, 16 `SVehicleWheel` (each carrying its kick-up/burnout/
  trail particle refs), 12 meshes (`Batmobile_V2` 3 LODs/65 sockets, `Batmobile_MK2_Skin` 55 sockets,
  `Batmobile_Jokerfied_Skin` 63), 32-body physics asset, 253 AnimSequences, weapon gadget meshes.
- **Appearance:** 185 master materials (slot → expression), 130 instances (parent + scalars/vectors/
  texture params), 405 textures with dimensions and the instance+parameter that binds each; `SLOTS.md`
  proves the 19 slots across three reads and gives each one's LOD0 face count and texture set.

The remaining **925 untagged objects** (4.6%) are objects the cooker serialized without tags, and they
are almost all metadata: 696 `Package` stubs, 30 two-byte `RAkAudible`, and property/function objects
that are themselves the schema (only 140 are larger than 8 B). All 4 `RVehicleBatmobile` and all 49
`RBatmobile*` archetypes now decode; the missing piece was the `StrProperty` tag type, which aborted
the walk on any object carrying a string. Their class, owner, size and recoverable references are
recorded in `objects.jsonl` and `GAPS.md`; nothing is guessed. GRB-11 records why the last names cannot
be recovered from these packages and what would unblock it.


**Blocked until GRB-5** *(lifted: GRB-1…GRB-11 closed, §0.6; BUD-1 then ran and closed, §111):* all in-game testing, LGT-1/2, DMG-1..5, PRT-*, WPN-*, MOD-*,
HDL-2..5, POL-2. **Unblocked by the grab itself:** AUD-3 (banks found), HDL-1 (sim properties now
readable from file, no runtime CDO walk needed), WPN-1 (weapons are in the same package).

---

## 1. Requirements and non-negotiables

### 1.1 Product requirements (from the user, ranked)

1. **Lore accuracy before convenience.** 100% BmAK Batmobile behaviour; no value chosen by feel.
2. **Dynamic pipelines.** Assets, textures, audio and mappings are derived from shipped files by a
   re-runnable script; hand-picked lists are recorded as hardcodes and burned down.
3. **One variable per test**, each with a stated oracle; a build that loads is not evidence.
4. **No deploy without explicit approval.** Staged builds are the default output.
5. **Everything journalled** in `MODLOG.md` with file-level evidence.

### 1.2 Engineering constraints (proven, not assumed)

- **No new input binds (no evidence of a hook).** JC3 mods are file overrides; the only input surface found is `BmGame.ini`'s keybind block (MODLOG §93). Until something proves otherwise, features must ride existing inputs: fire (weapons), nitro (boost), brake/handbrake, horn.
- **No runtime module swap.** The `.ee` is loaded at spawn; a "mode" cannot hot-swap modules unless the engine already supports it (**UNKNOWN**).
- **No skinned RBM writer.** Current writer emits plain `CarPaintMM`/`Window` blocks; skin-weighted parts (`SkinnedPart.bones`) are out of scope until a spike proves the layout.
- **Budgets are hard walls.** Vehicle-HD Model 4,915 KB / Texture 7,065 KB (×0.9 guard); exceeding them makes the whole entity vanish (MODLOG §76).
- **Shared modules must not be edited in place.** `vehicle_common`, `lave_health_medium`, `vehicle_deform` are game-wide; per-vehicle copies with repointed hashes only.
- **Never internalize a module the archives carry** (stale-engine trap, MODLOG §71).

### 1.3 Definition of Done (project level)

- [ ] Car looks like the Batmobile in-game at all 5 LODs, with correct materials, glass and emissive parts.
- [ ] Headlights, taillights, brake lights and signals work and are visible at night.
- [ ] Bullet/impact/explosion behaviour matches the shipped tank's damage model, verified by ammo-count and ram tests.
- [ ] Machine gun fires from the turret; heavier weapon fires from its own point; both have HUD ammo and reload.
- [ ] Aero flaps / missile bays / jet nozzles move or spin on their own pivots.
- [ ] Pursuit and Battle behaviour are defined, implemented by the chosen route, and documented.
- [ ] Handling is either BmAK-derived (values attributed to named properties) or explicitly signed off as JC3-band with measured telemetry.
- [ ] Engine start/loop, turbo and (if the bank is found) battle audio are wired dynamically.
- [ ] Camera behaviour is per-vehicle tuned and stable at speed.
- [ ] Installer + rollback + README + credits + KB field note shipped.

---

## 2. Priority system

| Level | Meaning | Rule |
|---|---|---|
| **P0** | Release-blocking or actively broken, or the GRAB gate (§0.6) | Do before any new feature. A P0 that regresses the live build must be fixed in the same session. **While GRB-6 is open, no appearance build and no hand-tuned value is allowed.** |
| **P1** | Core Batmobile identity | Required for "this is the Batmobile", not just "a car with the mesh". |
| **P2** | Fidelity and polish | Noticeable quality gap; can ship without it once. |
| **P3** | Optional / expansion | Nice-to-have, research-heavy, or distribution work. |
| **Gate** | Blocks scheduling until a decision or measurement exists | Never worked around with invented values. |

Effort: **S** ≤ 1 session · **M** 1–3 sessions · **L** 1–2 weeks · **XL** multi-week R&D.

---

## 3. Phases (with exit criteria)

### Phase 0 — GRAB, then consolidate what is already built (P0)

**Gate:** GRB-1…GRB-11 are closed (§0.6). Appearance builds run from `VALUES.json`; the generated
LIGHTS/AUDIO_MAP/SLOTS tables are the only inputs LGT-1, AUD-3 and MAT-2 may read. test-081 remains the
installed build until DEP-1 produces the next one.

**Why first:** the project has 77+ tests and two parallel trees. The appearance work is now live, but
until DEP-1/DEP-2/DEP-3 the live tree had no guard against another silent rebase and no way to prove
the installed bytes are the built ones. Every later phase multiplies the cost of a broken deploy path,
so the pipeline is closed before any feature work starts.

| ID | Task | Effort |
|---|---|---|
| DEP-1 | ✅ Rebase the 19-material appearance build onto live test-077 → **test-078**, install it | M |
| DEP-2 | ✅ One deploy pipeline + golden-hash guard (no more rebase-from-old-test) | S |
| DEP-3 | ✅ Post-install verifier: read the deployed pair through its `.toc`, compare to staged aaf | S |
| PRV-1 | ✅ `preview_rbm.py`: offline render of an RBM, per-block material colours, albedo mode | S |
| ALB-1 | ✅ Linear→sRGB encoding for every generated albedo and the glass tint | S |
| MAT-1 | ✅ Paint gloss capped at the vanilla paint level (0.45 vs Serpente 0.40) | S |
| ALB-2 | ✅ Albedo gain ×4 in linear space: daylight readability, measured against the reference | S |
| BUD-1 | ✅ Model budget: use the hard cap (or trim LOD4/5) so body lod1 can exceed 31k tris and decimation stops tearing plate borders | M |
| PHY-1 | ✅ Collision bodies decoded (MODLOG §115): 32 `RB_BodySetup` per vehicle → `Research/BatmobileGrab/PHYSICS.md` (bone, box extents, local centre). No chassis body exists — the driveable car's hull collision stays JC3-side | S |
| QA-1 | Objective measurement harness (speed, 0–100, turning circle, screenshots) — **instrument built and first take measured**: `qa1_hud.py` decodes the HUD speedometer from a take with no hand-read frames; take 1 gives 0–100 in 16.4 s / 257 m, peak 138 km/h, braking 3.5–3.8 m/s² (T-M1 and T-E1 closed, T-E4/T-K1 partial). The remaining manoeuvres are prescribed in `T_PLAN.md` §5 | M |
| LGT-1 | Batmobile lights module + light parts (`has_lights`, `_LIG` anchors) — **decoded 2026-10-22** (MODLOG §112): the 21 vanilla entries all name parts our entity does not expose; a vanilla light part is `CarLight` + `Window`, static; our body is static and the build has **no `CarLight` block**. Next: the one-variable part-exposure probe, then light parts | M |
| LGT-2 | CarLight/emissive block so lights have an emitter source | S |
| PRT-1 | Parts cleanup: drop the two dead door parts, name parts for the lights/weapons work | S |
| DMG-1 | Damage wiring audit: why 42 parts + tank armour still die to mags | M |

**Exit:** the current build loads, *looks like the Batmobile in daylight* (the 078 black-out proved
verifying is not seeing), has working head/tail lights, and passes
`spec_check` + budget + installer/rollback; the deploy command refuses to run on a drifted tree.

**State 2026-10-22:** DEP-1/2/3 done (install + 9/9 proof, MODLOG §104). Three in-game looks drove three
single-variable corrections - 078 **black** (linear colour in sRGB slots → ALB-1, 079), 079 **wet
mirror** (gloss → MAT-1, 080), 080 **too dark in daylight** (measured against the reference → ALB-2,
081). **BUD-1 closed** (MODLOG §111): hard-cap budget, body lod1 31,139 → 44,608 tris, silhouette
holes 0.471% → 0.297%, **test-082 installed and verified** (9/9; no appearance constant changed, so
081's daylight/night verdict still carries). **PHY-1 closed** (§115): the 128 collision bodies are
`PHYSICS.md`; **test-083** is the live LGT-1 probe (one vanilla light part exposed, awaiting a night
look). **Handling proposal written, not applied**: `Working/Movement/HDL_PROPOSAL.md` — the concrete
content of HDL-4, five one-variable stages (grip, steer geometry, steer rate, inertia/drift, boost),
with `arcade_friction_multiplier` 1.0/1.0 against Mugello's 4.2/4.7 as the largest un-derived number.
Phase 0 continues with LGT-1 → PRT-1 → LGT-2 → DMG-1; QA-1 is the prerequisite for every HP stage.

**Order change 2026-10-22 (§116):** feature work in Phase 0 is now queued behind the grab phases in
[GRAB_BACKLOG.md](GRAB_BACKLOG.md) — **G1** (the 380 unnamed BmAK values), **G2** (the JC3 grab),
**T** (the translation table). LGT-1's probe (test-083) stays live because it answers an architectural
question; PRT-1's build half, DMG-1 tuning and HP-1…HP-5 wait for the data.

**JC3 grab, step 2 (§117):** G2-1…G2-4 done. `jc3index.py` names **55,811** of 81,953 archive entries
(the base game is complete at 47,555/47,557; DLC has no filelists). `jc3grab.py` decoded **232 vehicle
entities**: 135,283 inner files, 6,045 modules, **5,816 decoded (96.2%)**, 3.1 M named values, plus
`Research/JC3Grab/VOCABULARY.md` — 52 module types × 1,421 members with fleet min/median/max and a
donor column. The only refusals are `*_vehicle_parts.vmodc` (229), a Gibbed parse bug. Still open:
`.physicsc` (233, inside the entity bundles), the `.epe` graph (232) and `.rbm` geometry (55,908).

**JC3 grab, step 3 (§118):** `jc3detail.py` decoded the **entity graph and shape** side of all 232
entities: 103 `.epe` classes, **11,041 `CPartProp`** (donor 40, `part_index` → mesh name), **3,972
`SVehicleLight`** (donor 22, with `preset_id`/`diffuse`/`radius`/`spot_angle`/`volumetric_mode`) and
every RBMDL header (bounds, blocks, all 1.16.0). That gives LGT-1 and PRT-1 their ground truth from the
shipped game instead of from probes, and gives donor selection a size comparison (Serpente body
2.099 × 1.3875 × 3.72 m vs Batmobile 3.495 × 2.271 × 7.026 m). `.physicsc` turned out to be a **Havok
2014 packfile**, not an RTPC file — that is G2-8.

**JC3 grab, step 4 (§119):** stations and the fleet table. `land_global.base_wheel_hardpoint_positions`
is the authoritative station set (145 vehicles); the Havok `.physicsc` copy exists in 17 and agrees
**17/17**. `FLEET.md` ranks 144 land vehicles by shape against the Batmobile (7.026 / 5.029 / 2.416 /
0.6826 m): Urga armored transport **0.134**, Capstone tanks **0.164**, articulated truck 0.182, old
truck 0.197 — and **the current Serpente donor 0.358, 45th of 144**. The built car is 4,000 kg on a
975 kg supercar's chassis. The donor is therefore an open, quantified decision (T-0), and T-1 is the
next step.

**T-1 draft written (§120):** `Working/Translation/T1_TRANSLATION.md` — ~60 rows over 12 subsystems,
each with BmAK source, JC3 member, transform, the value test-083 ships (`current.json`, decoded from the
build), a proposal, a confidence class and a falsifying measurement. Evidence for the `class` rows is
generated by `t1_fits.py` (`FITS.md`: 18 members fitted against mass over 156 land vehicles). Three
conclusions overrule earlier work: **T-0 keeps `v0300`** as wiring (shape is already ours), **the
understeer lever is `arcade_friction_multiplier` 1.0 → 3.0** (fleet median 3.0 in every mass class), and
**HP-3 (steering rate) is withdrawn** — BmAK's 720 °/s is six times outside the fleet's fastest
`t_to_full_steer_s`, so it is not the same quantity. **T-P2 (damage parts) is now decoded** (G2-7,
§123). **T-P3's source side is decoded too** (G2-8, §124): `jc3hkx.py` reads the Havok packfiles through their virtual fixup table — 18,797 hulls across all 233 files, every invariant passing — so "which shapes does the JC3 vehicle actually have" is answerable; what stays open is *writing* a `.physicsc`, and the plan still keeps the chassis JC3-side.

**T-2 draft written (§121):** `Working/Translation/T2_TRANSLATION.md` — the half T-1 does not cover:
appearance, assembly, lights, audio, effects, damage, collision (39 rows, facts generated by
`t2_facts.py` into `T2_FACTS.md`). It corrects T-1: **T-P2's values were never blocked** — the 24
damage types are `VehicleDamage.part_damage_types[]`, decoded for all 233 vehicles; only the
part→type mapping is in the parts module. `LandAudio` has exactly **2** members, so every audio task
is a bank task. The build sits at the fleet **maximum** on `explosion_threshold` (4,000),
`smoke_threshold` (1,050) and `burn_threshold` (250), and one above the maximum on
`bullet_armor_strength` (100 vs 99) — the health lever is `max_health` (T-DM1), not more armour.

**G2-7 solved (§123, `Research/JC3Grab/PARTS.md`):** the converter's crash was never a missing type
(the 31-type dictionary is byte-identical in 80 of 80 parts modules) — member offsets are *declared*
in the type dictionary, so `Tools/scripts/jc3adf.py` reads the structs directly and **232 of 232**
parts modules decode (11,599 parts, 0 failures). Validated 1,660/1,660 rows against Gibbed on the 4
files it can read, and the donor's 42 parts, 12 light parts and 4 wheels against `DeformPoints`.
`PARTS_TABLE.jsonl` is the fleet table; **T-P2 (per-part damage) is no longer blocked** — part →
damage type → health is now a join over decoded data.

### Phase 1 — Batmobile identity: weapons and moving parts (P1)

| ID | Task | Effort |
|---|---|---|
| WPN-1 | Catalog every `jc_weapons/06_vehicle/*` in the archives (mgun, cannon, missile?) | S |
| WPN-2 | Port `CBulletWeaponBase` + `SWeaponPoint(turret_anchor)` into the Batmobile `.epe` | L |
| WPN-3 | Second weapon (cannon / missile) via `CForcePulse` or the matching vehicle weapon | L |
| PRT-2 | Split body RBM into parts: turret, 4 flaps, missile bays, 2 nozzle banks | L |
| PRT-3 | Parts-module wiring: `parent_space_offset` pivots + `hinged_parts`/`fin_parts`/`rotating_parts` | L |
| PRT-4 | `aim_part_constraints` spike so the turret aims with the camera | L |

**Exit:** the car shoots from the right place, the turret moves, at least the flaps or the nozzles
animate, and neither breaks the LOD/parts system.

### Phase 2 — Damage and armour integrity (P1)

| ID | Task | Effort |
|---|---|---|
| DMG-2 | Private health module: copy `lave_health_medium`, write the tank's 24 rows, repoint the `.epe` hash | M |
| DMG-3 | Part damage-type remap (42 parts → tank/fitting rows), wheel flag included | M |
| DMG-4 | Bullet-path oracle: magazine count, ram, explosion, fire — one metric per test | S |
| DMG-5 | Decide `impact_damage_factor` 0 vs 1 and `deform_scale` 0 vs 1 with the tank as the only source | S |

**Exit:** a documented ammo count does nothing to the car; explosives still damage it; no part
silently falls back to `Default`.

### Phase 3 — Modes: Pursuit and Battle (P1, decision-gated)

| ID | Task | Effort |
|---|---|---|
| MOD-1 | **Gate G1:** determine whether JC3 has any vehicle state that can toggle behaviour | S |
| MOD-2 | If no native toggle: choose (a) permanent battle behaviour, (b) two drop variants, (c) cosmetic-only state on nitro | S |
| MOD-3 | Battle behaviours that do not need a toggle: turn-on-spot, impact immunity, camera framing, battle audio | L |
| MOD-4 | Pursuit behaviours: boost map, top-speed governor, camera, wind/whine audio | M |

**Exit:** a written, evidence-backed mode design, implemented for its chosen route, with the rejected
routes recorded.

### Phase 4 — Handling and drivetrain (P1, blocked on data)

| ID | Task | Effort |
|---|---|---|
| HDL-1 | **Gate G2:** BmAK live-property extraction spike (UE3 CDO walk in memory) | XL |
| HDL-2 | Suspension flight fix: revert 068 to 067 and isolate with telemetry | M |
| HDL-3 | Standstill tank-turn diagnosis: A/B 067 vs 068, then counter-steer/drift torques | M |
| HDL-4 | If G2 fails: JC3-band tuning against measured targets, signed off in writing | L |
| HDL-5 | Drivetrain: gears/final drive/mass re-derived once a source exists | M |

**Exit:** understeer is either gone or quantified against a target lap/turn metric, and the values
carry a named source (BmAK property or shipped-vehicle member).

### Phase 5 — Audio completion (P2)

| ID | Task | Effort |
|---|---|---|
| AUD-1 | Wire engine start + loop to `engine_running_sound` dynamically (GUID → bank → FSB) | M |
| AUD-2 | Replace 060's name-picked nitro with the `exhaust_upgrade_nitrous2` GUID path | S |
| AUD-3 | Battle-mode audio: one more bank hunt, else declare and keep stock | M |
| AUD-4 | Mix: gain staging, RTPC RPM/velocity, ducking | M |
| AUD-5 | Bank shipping: loose `vehicles.bank` vs rebuilt bank + `.toc` | M |

**Exit:** every mapped sound is attached by rule, not by name, and the manifest proves it.

### Phase 6 — Camera, effects, polish (P2)

| ID | Task | Effort |
|---|---|---|
| CAM-1 | Per-vehicle `.ctunec` (tank as reference) for chase + battle framing — candidate emitted by `bmak_camfile.py` | M |
| FX-1 | Exhaust/jet trails via `effect_attachments.vmodc` + `.etune` | M |
| POL-1 | Interior/cockpit materials, seat, battery/power-cell detail | M |
| POL-2 | Micro-detail bake into s1 (closes the largest "no-JC3-slot" group) | L |
| POL-3 | HUD/rebadging: display name, icon, drop entry text | S |

**Exit:** the car reads as complete in a 60-second driving clip.

### Phase 7 — Optional expansion (P3)

| ID | Task | Effort |
|---|---|---|
| EXP-1 | Amphibious tuning (`buoyancy`, `water_interaction`) | L |
| EXP-2 | Standalone vehicle registration (`settings\*.bin`, stringlookup, spawn table) | XL |
| EXP-3 | Skinned-part spike (turret on bones, not constraints) | XL |
| EXP-4 | Release packaging: README, credits, publish lint, KB field note | M |

---

## 4. Backlog (single table, ordered by priority)

`Deps` are task IDs. `Oracle` is what proves the task, not what "should" happen.

### P0 — GRAB gate (runs first, blocks every in-game test)

| ID | Task | Deps | Oracle |
|---|---|---|---|
| **GRB-1** ✅ | `upk_read.py` — chunked UE3/Batman package reader: names, imports, exports, `int16 type + uint16 offset` property tags, object refs, recursive struct/array decode | — | **DONE**: 5,490/5,490 exports read; class census matches `umodel -list` 12/12 |
| **GRB-2** ✅ | `batmobile_grab.py` — discover all Batmobile packages, dump every export to `Research/BatmobileGrab/objects.jsonl`, classify, hash | GRB-1 | **DONE**: 15 packages, 20,128 objects, 14/14 checks |
| **GRB-3** ✅ | Material/texture graph → `MATERIALS.md`, `TEXTURES.md` | GRB-2 | **DONE**: 185 materials, 130 instances, 405 textures with bindings |
| **GRB-4** ✅ | Mechanics graph → `MECHANICS.md` + `AUDIO.md` (vehicle, sim, wheels, physics, sockets, anims, weapons, banks/events) | GRB-2 | **DONE**: sim curves with points, 247 sockets, 30 banks, 361 events |
| **GRB-5** ✅ | Completeness gate → `GAPS.md`, dependency closure, decoded/undecoded ratio | GRB-3, GRB-4 | **DONE**: 19,203/20,128 decoded; 925 untagged objects named with reasons |
| **GRB-6** ✅ | Replace hand-tuned constants with values read by the grab | GRB-5, GRB-7 | **DONE**: `VALUES.json` from `grab_values.py`; `factors.py` imports it, no `PAINT_*` left |
| **GRB-7** ✅ | `grab_model.py` query layer + `check` | GRB-2 | **DONE**: schema 5, 14/14 grab checks, manifest cross-checked |

### P0 — consolidate (after the grab gate)

| ID | Task | Deps | Oracle |
|---|---|---|---|
| **DEP-1** ✅ | Build + **install** **test-078**: copy the live 077 `aaf` tree, replace the 5 body + 20 wheel RBMs (wheels go 1 → 5 blocks) and add the 28 converted textures; leave every module, `physicsc` and `land_global` untouched; installer + `Rollback077` | DEP-2 | **DONE 2026-10-21** (`Builds/test-078`, MODLOG §103): aafdiff 28 added / 40 changed / 0 removed, 0 modules; body 17 blocks × 5 LODs, wheels 5 × 5, 28/28 textures used and internal in the `.toc`, round-trip 576 files 0 lost; model 4,198/4,424 KB, texture 3,954/4,648 KB. **INSTALLED 2026-10-21** with a pre-install rollback copy; `verify_install.py` then read the deployed pair through its `.toc`: 9/9 (35 meshes and 28 textures byte-identical to aaf, body 17 blocks × 5 LODs, wheels 5 × 30, archives baseline identical to 077). Oracle run 2026-10-21: **FAILED** - the installed car rendered flat black (albedo byte 14 instead of 67, MODLOG §105); the mesh itself was verified correct with `preview_rbm.py`. Fixed as **ALB-1** and superseded by **test-079**, installed the same day (9/9). Remaining oracle: a daylight screenshot of 079 |
| **DEP-2** ✅ | `Tools/scripts/deploy.py`: golden hashes of the live `.ee`/`.toc`, refuses on drift, stamps build id, writes `Builds/<tag>/receipt.json` | — | **DONE 2026-10-21**: both guard paths tested (base-pin drift and live-dropzone drift each exit 1 and write nothing); clean build wrote `receipt.json` + installer; `install.ps1 -Action Status` reads the live 077 hashes |
| **DEP-3** ✅ | `Tools/scripts/verify_install.py`: decode the installed `.ee` through its `.toc`, compare every replaced mesh/texture with the staged aaf, assert the archives baseline did not move; wired to `install.ps1 -Action Verify` | DEP-2 | **DONE 2026-10-21** (MODLOG §104): 9/9 on test-078; negative control (one `.toc` record shortened by hand) fails three independent checks (`toc hash`, `baseline`, `texture bytes`), exit 1; the old 077 live body decodes as 1 `CarPaintMM`, so the 17-block oracle discriminates the regression |
| **PRV-1** ✅ | `Tools/scripts/preview_rbm.py`: render an RBM offline (side/front/top, z-buffered, per-block colours, `--albedo DIR` tints by the real dif mean) | — | **DONE 2026-10-21** (MODLOG §105): body renders as a complete Batmobile (31,139 tris, 17 blocks, correct 3.50×2.28×7.03 m bbox); first in-game look proves the render matches the shipped mesh |
| **ALB-1** ✅ | `factors.py srgb8()`: generated albedos and the glass tint must be sRGB-encoded, not raw linear | PRV-1 | **DONE 2026-10-21** (MODLOG §105): body albedo 0x0e0d0f → 0x434045, glass tint 13 → 63; test-079 built (14/14) and installed (9/9); 185 blocks, 0 spec mismatches |
| **MAT-1** ✅ | Paint response: compare our block's SpecularGloss/Metallic/ClearCoat with a vanilla `CarPaintMM` body block and change **one** of them per build | ALB-1 | **DONE 2026-10-21** (MODLOG §106): gloss was (0.6, 0.75, 0.85, 0.98) vs the vanilla paint channel's 0.400, so it is capped at **0.45** (`PAINT_GLOSS_CAP`, recorded in each channel's `source`); metal/clearcoat/textures untouched. test-080 built (14/14), installed, 9/9. Winding and the missing `a00_dummy_*` paths were ruled out first - the vanilla blocks use the same dummies |
| **ALB-2** ✅ | Albedo readable in daylight: multiply the linear paint colour before sRGB encoding | MAT-1 | **DONE 2026-10-21** (MODLOG §107): measured the 080 screenshot (body lum 12–16 vs grass 85; reference car 22 vs road 12), set `PAINT_ALBEDO_GAIN = 4.0` → body 0x434045 → **0x837d86**; glass tint, gloss, metallic untouched. test-081 built (14/14), installed, 9/9. Dial is the single constant if it reads too light |
| **BUD-1** | Model budget headroom: the cap is the hard limit × 0.9 (4,424 KB) with ~226 KB free; using the hard cap (+~700 KB) or trimming LOD4/5 would let body lod1 exceed 31k tris | GRB-5, ALB-1 | Body lod1 rose to ~43k tris without exceeding the hard cap; measured decimation holes drop below 0.3% of the silhouette (today 1.01%) |
| **QA-1** | Telemetry harness: fixed-distance speed run, 0–100 timer, skidpad radius, screenshot set, log capture → `Working/Telemetry/<tag>.json` | DEP-2 | Two runs of the same build agree within 5%; results stored per build |
| **LGT-1** | Lights module for the Batmobile: decode the FDA lights file, add light parts to parts/`.epe` with `has_lights`, anchor to `_LIG`-style names | DEP-1, PRT-1 | **DECODE DONE 2026-10-22** (MODLOG §112, `Working/Lights/LGT1_FINDINGS.md`): entity/lights/parts all decode; 21 module entries name parts the 7-part entity does not expose; `has_lights` is per part in the parts module; a vanilla light part is `CarLight`+`Window` (static) while the vanilla body is `IS_DEFORM`; ours is static with no `CarLight` anywhere; the `_LIG` names are in no RBM, no parts `bones` array and not the deform table. Design = light parts from the vanilla pattern + `.epe` exposure + rewritten module. **PROBE INSTALLED 2026-10-22 as test-083** (MODLOG §113): one `CPartProp` added to the entity's `CParts` chain (`sportsmuscle_taillight_r_l`, hash -640601345, idx 8), +128 B, everything else untouched; 13/13 build checks, install Verify 9/9, Rollback082 available. **Awaiting one night look**: a floating Serpente tail lamp = the name chain resolves and the §6 light-part build is confirmed; nothing = the next probe is the body-anchored entry 3/10. Oracle unchanged: every behavior toggles; night screenshot |
| **LGT-2** | `CarLight` block (or proven equivalent) on the emissive part, flags and textures from BmAK emissive data | DEP-1 | The emissive part is a light source, not a black block; compare screenshot day/night |
| **PRT-1** | Parts cleanup: remove `door_f_l`/`door_f_r` (no Batmobile doors), name parts for lights/weapons, document the 42-part map | — | **MAP DONE 2026-10-22** (MODLOG §114, `Working/Parts/PRT1_PARTMAP.md`): all 42 records documented (12 with `has_lights`, 18 deformable); `door_parts` = 1, 2 and **25 = `hood_signature`** (not a third door). Removal touches the entity's part names + the module's `door_parts` (in-place patch; writer still +544 B). **Not built while the LGT-1 probe (test-083) is live.** Remaining oracle: `aafdiff` clean; no door animation on entry |
| **DMG-1** | Damage wiring audit with the readable parts file: part → damage type → health row, measured end to end | DEP-1 | A table in `Working/Damage/` that predicts the observed magazine count, or names the exact step where it breaks |

### P1 — identity

| ID | Task | Deps | Oracle |
|---|---|---|---|
| **WPN-1** | Extract and catalog every vehicle weapon under `jc_weapons/06_vehicle` (name, type, ammo, projectile) | — | Catalog file with counts; nothing named from memory |
| **WPN-2** | Mgun on `turret_anchor`: entity weapon component + `SWeaponPoint` + `.wtune`, ammo/HUD | PRT-1, WPN-1 | Fire button shoots from the muzzle, not from the car origin; ammo counts down |
| **WPN-3** | Second weapon (cannon/missile) via `CForcePulse` or a matching vehicle weapon | WPN-1, WPN-2 | Second weapon fires from its own point with its own ammo |
| **PRT-2** | Split body into parts: turret, flaps, missile bays, nozzle banks (one RBM per part, LODs kept) | DEP-1 | Each part loads in place; total model KB still under cap |
| **PRT-3** | Pivots + `hinged_parts` / `fin_parts` / `rotating_parts` entries (`parent_space_offset`) | PRT-2 | Flaps/nozzles visibly move; no part flies off at speed |
| **PRT-4** | `aim_part_constraints` spike: turret follows the camera, clamped | WPN-2, PRT-3 | Turret tracks a target without spinning the body |

### P1 — damage

| ID | Task | Deps | Oracle |
|---|---|---|---|
| **DMG-2** | Private health module (tank's 24 rows, own path, repointed hash) | DMG-1 | `.epe` hash matches the new path; `_healthband` shows tank rows live |
| **DMG-3** | Part damage-type remap from the 42-part table, **and internalise `vehicle_parts.vmodc` in the `.toc`** (it is external today, MODLOG §103c) | DMG-1 | No part on `Default`/`Boat_Antenna`; wheel row matches tank; `.toc` record has a nonzero offset |
| **DMG-4** | Bullet/ram/explosion/fire oracle set | DMG-2, DMG-3 | Ammo and ram counts recorded per test, one metric each |
| **DMG-5** | `impact_damage_factor` / `deform_scale` decision with tank evidence; `vehicle_deform.vmodc` must also be internalised | DMG-4 | Written justification; no invented value; `.toc` record for deform has a nonzero offset |

### P1 — modes (gated)

| ID | Task | Deps | Oracle |
|---|---|---|---|
| **MOD-1** | Gate G1: evidence sweep for any native vehicle state toggle | — | Written answer: yes (with file) or no (with the search surface covered) |
| **MOD-2** | Mode design decision recorded in MODLOG | MOD-1 | One route chosen, others listed with why |
| **MOD-3** | Battle set: turn-on-spot, impact immunity, battle camera, battle audio | MOD-2, DMG-4 | Each behaviour tested separately |
| **MOD-4** | Pursuit set: boost map, governor, camera, wind/whine | MOD-2, HDL-4 | Boost changes top speed measurably; audio matches state |

### P1 — handling (gated)

| ID | Task | Deps | Oracle |
|---|---|---|---|
| **HDL-1** | Gate G2: BmAK live-property extraction spike | — | A name→value table for `RVehicleBatmobile` / `RVehicleSimBatmobile`, or a documented dead end with the methods tried |
| **HDL-2** | Revert 068 suspension, isolate the flight-off-bumps cause | QA-1 | Bump run at 3 speeds: no launch, or a single named parameter implicated |
| **HDL-3** | Tank-turn A/B (067 vs 068) then one-variable torque tests | QA-1 | Turning circle metric moves in the expected direction; no other metric regresses |
| **HDL-4** | Fallback: JC3-band handling against telemetry, signed off | QA-1 | Target lap/turn numbers met, values from shipped vehicles only |
| **HDL-5** | Drivetrain values (gears, final drive, mass) re-derived from whatever HDL-1 produces | HDL-1 | Every changed member cites a BmAK property or a shipped-vehicle member |

### P2 — audio / camera / polish

| ID | Task | Deps | Oracle |
|---|---|---|---|
| **AUD-1** | Engine start/loop wired dynamically | — | Start then loop in game, manifest row per sample |
| **AUD-2** | Dynamic nitro path replaces the 060 hardcode | AUD-1 | Same sound, proven path, hardcode removed from the checklist |
| **AUD-3** | Battle audio hunt: final pass, then declare | — | Either the bank is found, or `EVENTMAP` marks battle sounds as no-source with the coverage listed |
| **AUD-4** | Mix and RTPC pass | AUD-1 | Level-matched against a vanilla vehicle; no clipping |
| **AUD-5** | Bank ship strategy (loose vs rebuilt + `.toc`) | AUD-4 | Installer handles the bank and can roll it back |
| **CAM-1** | Per-vehicle `.ctunec` tuning | DEP-1 | Chase cam stable at 300+ kph; no clipping through the body |
| **FX-1** | Jet/exhaust effects via `effect_attachments` | PRT-2 | Trails appear from the nozzles, not the car centre |
| **POL-1** | Interior/cockpit materials | DEP-1 | Interior visible in cockpit-ish views; no untextured surfaces |
| **POL-2** | Micro-detail normal bake | DEP-1 | Microdetail group drops out of the "no-slot" list; visual A/B |
| **POL-3** | Display name, icon, drop text | EXP-2 or replacement route | Name shows in the drop menu and the vehicle HUD |

### P3 — expansion

| ID | Task | Deps | Oracle |
|---|---|---|---|
| **EXP-1** | Amphibious tuning | DEP-1 | Car floats, enters/exits water without exploding |
| **EXP-2** | Standalone registration | — | A new entity spawns by name, saves, and does not replace the Serpente |
| **EXP-3** | Skinned-part spike | PRT-2 | One skinned block round-trips and animates, or a documented layout spec |
| **EXP-4** | Release packaging | all P0/P1 | `um publish check` clean, README/credits, KB note, installer verified |

---

## 5. Dependency graph

```
GRB-1 reader ──> GRB-2 dump ──┬──> GRB-3 materials/textures
                              ├──> GRB-4 mechanics/audio/anims/weapons
                              └──> GRB-5 completeness gate ──> GRB-7 query layer
                                                                      │
        GRB-6 values / GRB-8 lights / GRB-9 audio / GRB-10 slots <───┘
                                                                      │
                GRB-11 closed with evidence  ·  everything below unblocked ▼

DEP-2 deploy guard ──> DEP-1 test-078 ──┬──> PRV-1 render ──> ALB-1 sRGB ──> MAT-1 paint   [all DONE]
                                        ├──> BUD-1 model budget ──> fewer decimation holes
                                        ├──> LGT-1 lights ──> LGT-2 CarLight
                                        ├──> DMG-1 damage audit ──> DMG-2/DMG-3 ──> DMG-4
                                        ├──> PRT-2 split parts ──> PRT-3 pivots ──> PRT-4 aim
                                        ├──> POL-1 interior / POL-2 microdetail
                                        └──> CAM-1 camera

DEP-2 ──> QA-1 telemetry ──┬──> HDL-2 suspension revert
                           ├──> HDL-3 tank-turn A/B
                           └──> HDL-4 fallback (band tuning, signed off)

WPN-1 weapon catalog ──> WPN-2 mgun ──> WPN-3 second weapon
WPN-2 + PRT-3 ──> PRT-4 aim constraint
MOD-1 mode gate ──> MOD-2 design ──> MOD-3 battle / MOD-4 pursuit
HDL-1 BmAK spike ──> HDL-5 drivetrain        (parallel, does not block the rest)
AUD-1 ──> AUD-2 ──> AUD-4 ──> AUD-5         (AUD-3 independent)
EXP-2 ──> POL-3
```

---

## 6. Decision gates (do not schedule past these without an answer)

| Gate | Question | How to answer | Cost | If it fails |
|---|---|---|---|---|
| **G1** | Can a JC3 vehicle switch behaviour at runtime? | Search all entity/module/parts schemas for state members; check mech/transform vehicles; test one candidate in game | S | Permanent battle behaviour, or two drop variants |
| **G2** | Can BmAK's `RVehicleBatmobile` / `Sim` properties be read with names? | Runtime CDO walk (UE3 property metadata lives in the UClass, which is loaded in memory) | XL | JC3-band tuning with telemetry sign-off |
| **G3** | Do hinge/fin/rotating parts rotate without code hooks? | Add one flap part with `parent_space_offset` + `hinged_parts`, test | M | Static flaps; skinned-part spike (EXP-3) |
| **G4** | Is there a vehicle weapon that fits a missile launcher? | Catalog `jc_weapons/06_vehicle` across archives | S | Mgun + cannon only |
| **G5** | Does `aim_part_constraints` need a target part or a camera target? | Tank parts file (unpopulated) vs any APC/boat with a turret | M | Turret fixed forward, or turret tied to hull yaw |

---

## 7. Risks and anti-goals

### 7.1 Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Another silent rebase loses staged work | High | DEP-2 deploy guard + `receipt.json` per build |
| Appearance build + live modules interact badly (budget, parts count) | High | DEP-3 reports both budgets on the installed bytes; `deploy.py` refuses to write a receipt when either is over |
| A hash-perfect build that still renders wrong (colour space, texture format, block flag) | High | PRV-1 renders offline before deploy; colour-managed constants live in one helper (`factors.srgb8`); every in-game look gets recorded as an image + MODLOG entry |
| Chasing JC3 dummy texture paths that do not resolve | Medium | **Recorded dead end** (MODLOG §106): `a00_dummy_*` never resolves in any `.tab`, and vanilla blocks reference the same names - the engine supplies its own default. Dummies are not a bug |
| Entity edits (weapons, lights) corrupt the `.epe` | High | `.epe` writer is proven (§31); every edit round-trips through `ConvertProperty`; keep rollback installers |
| Handling stays blocked forever | Medium | G2 spike funded early; HDL-4 fallback signed off, not pretended |
| Test sprawl (77 builds, no metrics) | Medium | QA-1 telemetry; one metric per test; retire superseded trees |
| Weapon/turret work destabilises the parts system | Medium | Split into parts only after DEP-1 is green; keep a static-body fallback build |
| Texture/model budget overrun after new parts | Medium | Both guards are already in the pipeline; run them per build |

### 7.2 Anti-goals (recorded dead ends — do not repeat)

- Do not tune any value by hand, and do not launch the game to judge a constant, unless the number
  came out of the grab (§0.6). Four appearance builds and four handling value sets were spent the
  other way.
- Do not claim a BmAK value is unavailable until GRB-1 has walked that object; §0.6 already disproved
  the previous "no property names" conclusion for complex properties.
- Do not tune handling by feel (four rejected value sets, §95).
- Do not edit shared modules in place (`vehicle_common`, `lave_health_medium`, `vehicle_deform`).
- Do not internalize a module the archives carry (stale engine, §71).
- Do not add geometry by append/count (topology-preserving only, §34/§56).
- Do not pick armour values without checking the *strength* gate (99 vs 100, §97).
- Do not encode glass with BC1 punch-through (vanilla is BC3/DXT5, §102).
- Do not treat a successful build as evidence; the game is the oracle.
- Do not claim BmAK numbers that the files cannot supply (§93).

---

## 8. Suggested sequence (first five sessions)

0. **Session 0 (current, mandatory) — GRB-1…GRB-5:** build the reader, dump every Batmobile object,
   document materials/textures/mechanics/audio, and close the completeness gate. **No game launch,
   no build, no constant edit in this session.** GRB-6…GRB-11 followed on the same day and are closed;
   appearance work may resume from `VALUES.json`.
1. **Session A — DEP-1/DEP-2/DEP-3 + PRV-1 + ALB-1 + MAT-1:** ✅ done 2026-10-21. test-078 installed and
   proven on its bytes (9/9) → rendered black → albedo colour space fixed (079) → read as wet mirror →
   gloss capped (080). **Outstanding: one daylight screenshot of 080**; if it is still too shiny, the
   next variable is Metallic (ours 0 on the paint channel, vanilla 1).
2. **Session B — LGT-1 + PRT-1 + LGT-2:** lights module + part cleanup + `CarLight`. PRT-1 sits between
   them because the lights module must name real parts. Night screenshots are the lights oracle - and
   they double as the ALB-2 night check.
3. **Session C — DMG-1 + QA-1:** damage wiring audit and telemetry harness; both feed every later
   oracle. Include the `.toc --internal` rule for `vehicle_parts`/`vehicle_deform` in the audit.
4. **Session D — WPN-1 + WPN-2:** weapon catalog and the machine gun on `turret_anchor`.
5. **Session E — PRT-2/PRT-3 + G3:** split the turret and one flap, test pivot animation, then decide
the full split.

HDL-1 (the BmAK extraction spike) is the only task that should run as a separate parallel workstream:
it is the longest pole, and every drivetrain value in Phase 4 depends on its answer.

---

## 9. File and tool map (what to touch for each area)

| Area | Files |
|---|---|
| Appearance | `Tools/scripts/appearance_pipeline.py`, `appearance_grab.py`, `factors.py`, `bat_assemble.py`, `tex2ddsc.py`, `spec_check.py`, `appearance_progress.py`, `preview_rbm.py` (offline render; colour management lives in `factors.srgb8`) |
| Deploy | `deploy.py` (build + guard + receipt), `verify_install.py` (post-install oracle), `eetoc.py`, `SmallPack/SmallUnpack`; `_build_assembled.ps1` is legacy |
| Damage | `Working/Damage/*.json`, `_health.py`, `_healthband.py`, `_adftypes.py`, patched `ConvertAdf` |
| Parts/weapons | `sportsmuscle_vehicle_parts.vmodc` (readable), tank `.epe` (weapon reference), `ConvertProperty` |
| Lights | `modules/generated/..._lights.vmodc`, parts `has_lights`, RBM `CarLight` block |
| Audio | `Working/Audio/*`, `_apply_audio.py`, `_grab_all.py`, `vehicles.bank` |
| Physics/handling | `Working/Movement/*.json`, `_apply_move.py`, `physics_stations.py`, `land_*`/`rigid_body`/`suspension` modules |
| Camera | `jc_cameras/vehicle_cameras/*.ctunec`, `_cam_inv.py`, `_cammap.py` |
| Evidence | `MODLOG.md` (append-only), `FINDINGS_AND_BUGS.md`, `Working/Appearance/progress.md` |

---

## 10. Change log for this plan

- Replaced the old assumption-based plan (which still called the RBM pipeline an open unknown) with a
  verified state section, a module-level feature map, P0–P3 priorities, gates, phases, and a
  task-level backlog with oracles.
- Recorded the appearance regression (066 → 067) as the reason DEP-1 exists.
- **2026-10-21 (eighth update, GRAB prioritised and GRB-7 executed):** the untagged remainder is
  925 objects, not 1,030: all `RVehicleBatmobile`/`RBatmobile*` archetypes decode once `StrProperty`
  is walked, and the rest is almost all `Package` stubs. GRB-6 (constants), GRB-8 (lights), GRB-9 (audio),
  GRB-10 (mesh slots) and GRB-11 (offsets, closed with evidence) were done in that order on the same day. `Tools/scripts/grab_model.py` is now
  the single reader for the output (schema 5, `check` re-validates totals, references, curves, sockets
  and their resolved names, light rigs with socket→bone and `VEHLT_*` types, banks and an offset spot
  value); `grab_lights.py`, `grab_audio.py`, `grab_slots.py` and `grab_offsets.py` each have `--check`.
- 2026-10-21: DEP-1/DEP-2 completed offline (test-078 + `deploy.py` + guard tests); added the
  `.toc` externalisation finding for `vehicle_parts`/`vehicle_deform` (§0.3, DMG-3/DMG-5).
- 2026-10-21 (same day, after approval): test-078 **installed**; DEP-3 added and completed
  (`verify_install.py`, 9/9 on the installed pair, negative controls documented). Plan rows 3-5 moved
  from BUILT to LIVE, with the visual oracle explicitly still owed.
- 2026-10-21 (third update, in-game feedback): 078 rendered **black**. PRV-1 (offline renderer) ruled
  out geometry; ALB-1 fixed linear→sRGB encoding of generated albedos and the glass tint; **test-079**
  built (14/14) and installed (9/9). Added MAT-1 (paint response vs vanilla) as the next appearance
  task, and a risk row for "verifies but renders wrong".
- 2026-10-21 (fourth update): 079 read as a wet mirror. Winding and the missing `a00_dummy_*` paths were
  ruled out with measurements (99–100% normal agreement; vanilla uses the same dummies), body holes
  measured at 1.01% of the silhouette, MAT-1 capped gloss at 0.45, **test-080** built + installed (9/9).
  Added BUD-1 for the model-budget headroom that keeps decimation from tearing plate borders.
- 2026-10-21 (fifth update): 080 read too dark in daylight (body lum 12–16 vs grass 85; the reference car
  is brighter than its road). ALB-2 added a linear ×4 albedo gain; **test-081** built (14/14) and
  installed (9/9). Four single-variable corrections now form the appearance baseline: colour space, gloss,
  albedo gain - each recorded in the spec `source` strings, not in chat.
- **2026-10-21 (seventh update, GRAB executed):** `upk_read.py` + `batmobile_grab.py` built and run over
  all 15 `Playable_Batmobile*` packages: 20,128 objects, 19,203 decoded, 14/14 verification checks against
  UEViewer's listing. `Research/BatmobileGrab/` now holds `README`, `ASSETS`, `MATERIALS`, `TEXTURES`,
  `MECHANICS`, `AUDIO`, `GAPS` and `objects.jsonl`. The sim object yields named curves with values, the
  mesh yields 65 light/weapon/afterburner sockets, the vehicle packages contain the engine/burnout banks,
  and 253 animation sequences are catalogued. GRB-1…GRB-5 marked done; GRB-6 (delete the hand-tuned
  constants) is the next task, and no in-game test is scheduled before it.
- **2026-10-21 (sixth update, user decision):** GRAB replaces manual tuning as the first step. Added
  §0.6 and GRB-1…GRB-6 as P0, made GRB-5 a hard gate for every in-game test, marked the
  paint/albedo/gloss constants as temporary until GRB-6 re-derives them, moved BUD-1 behind the gate,
  and corrected the §0.3 "handling numbers unavailable" row: a probe of `Playable_Batmobile_SF.upk`
  read 5,490 exports with named sim properties and found the `BML_Engine`/`BML_Burnout` banks the audio
  hunt was missing. Sequence now starts at Session 0 (grab only).
- Recorded the proven carriers for lights, weapons, moving parts and modes so no future task starts
  from a blank page.
