# Booster nozzle — the BmAK jet mesh, its deploy motion, the flame over time, and the JC3 carrier

**STATUS: done (plan, read-only probe).** BmAK's booster is a **18-nozzle ring** on the rear of the car: the
plume mesh is `Engine.MESH_Batmobile_Jet_V01` (0.9 m, one per nozzle), the flame is the beam mesh
`Engine.Firefly_JetMesh` (1.2–1.3 m, 90 tiles), and the ring is **posed, not scaled** — the
`Batmobile_V2_Jet_Boost` pose state opens it in **0.600 s** (19 keys @ 30 fps) and
`Batmobile_V2_Jet_Close` shuts it in **0.833 s** (26 keys), in the same animation group as the aero flaps.
The flame itself is **five emitters with 0.15–0.35 s lifetimes**, sizes 15→80 (sprites) and 1.2–1.3 m (mesh),
colour ramping from `(0.9, 0.3, 0.1)` to white over life. On the JC3 side the carrier is
**`effects/jc_vehicles/exhaust/car_cycle_base_nitrous.effc`** (8 emitters, 17 timelines, decoded below) for the
nitrous plume, **`jet_exhaust_base.effc`** (11 emitters) for a jet plume, and **`generic_fire_01.effc`** for the
flame — plus a nozzle mesh **we must author**, because no JC3 vehicle part is named "nozzle" (0 hits in the
17 MB index). §6 gives the scale table per time step.

Every row is labelled **decoded** (read from the cited file), **derived** (arithmetic printed) or **UNKNOWN**.

---

## 1. The BmAK booster assembly (decoded)

| element | value | source |
|---|---|---|
| plume mesh | **`Engine.MESH_Batmobile_Jet_V01`** — export **176021**, **114,160 B** | `SM_BOUNDS.json:389-393`, `ASSETS.md` |
| flame mesh | **`Engine.Firefly_JetMesh`** — export **175976**, **5,270 B**, extent/centre self-consistent (`extent_abs_diff_cm` 6.0e-7) | `SM_BOUNDS.json:440-444` |
| nozzle bones | **18**: `Batmobile_Rig_Jet_Nozzle_001…018` on a ring at **z = 2.989 m**, radius ≈ **34 cm** (x 0…0.307, y 0.232…0.857) | `BONES.md:84-103` |
| ring parents | `Batmobile_Rig_Jet_Root` (z **2.354 m**) ← `JetSMove` (z **1.343 m**) ← `Batmobile_Chassis_Mesh` | `BONES.md:82-83` |
| other jet bones | `Batmobile_Rig_Jet_Thruster` (z 2.354), `Batmobile_Rig_Jet_Fins` (z 2.354) | `BONES.md:101,103` |
| the booster as a weapon | `PursuitModePrimaryWeapon` = `Weapons.Batmobile_Booster` → **`RBatmobileBooster`** | `COLLISION_WHERE.md:75` |
| boost effect hook | `SideExhaustBoostEffect` = **`Exhaust.SideExhaust_Boost`** (ParticleSystem) | `COLLISION_WHERE.md:63` |
| boost audio | `Play_Batmobile_RocketTails` / `Stop_…` | `AUDIO.md` (via `exhaust-and-heat-plan.md` §7) |

The mesh is **one nozzle's worth of geometry** used 18 times: the particle that renders it starts at
**0.9 × 0.9 × 0.9 m** (`PARTICLES.md` `batmobileExhaust_burst` jet-mesh emitter) at **+32 cm** from its bone,
which is why the emitter count in that system is 17 — one mesh emitter per ring position, minus the two side
plumes that use `Firefly_JetMesh` instead.

---

## 2. Deploy motion (decoded — it is a pose, not a scale)

The jet ring is animated by the Batmobile's **pose-state** set (`Batmobile_V2_Pose_States`):

| clip | length | keys | fps | tracks | notifies | source |
|---|---:|---:|---:|---:|---:|---|
| **`Batmobile_V2_Jet_Boost`** (deploy) | **0.600 s** | **19** | 30.0 | **21** | 0 | `ANIMATIONS.md:93`; `ANIMATIONS.json:4887,4889`; `objects.jsonl:211` (length 0.6, frames 19, fps 30) |
| **`Batmobile_V2_Jet_Close`** (retract) | **0.8333 s** | **26** | 30.0 | **26** | 0 | `ANIMATIONS.json:14612-14614`; `PARTICLES.md`/`ANIMATIONS.md` pose table |

The 21 tracked bones of `Jet_Boost` are exactly the ring plus its two ends:
`Batmobile_Rig_Jet_Nozzle_001, 002, 003, 004 … 018`, `Batmobile_Rig_Jet_Thruster`, `Batmobile_Rig_Jet_Fins`,
`Batmobile_Bone_Chair_Rot_001` (`ANIMATIONS.md:357`). So the deploy **opens the nozzles and the jet fins
together**, and it is grouped with the aero flaps: `COVERAGE.json:3640-3644` files
`Batmobile_V2_Jet_Boost` under group **`fins/air-brakes`**, row **P-09** — the same row the fins work uses.

Derived rates (arithmetic, not a file value):

```
deploy  19 keys / 0.600 s  = 30 keys/s  -> 0.600 s span, 0.0333 s per key
retract 26 keys / 0.8333 s = 31.2 keys/s -> 0.8333 s span, 0.0321 s per key
deploy : retract = 0.600 : 0.8333 = 0.72  (closing is 39 % slower than opening)
```

**No notifies** means the clip carries no timed sub-events: the effect start is **not** in the animation, it
follows the boost state (`SideExhaust_Boost` is bound to the actor's `BoosterComponent0`, and the anim only
poses the ring). The only anim notify named anywhere near exhaust is `ActivateExhaust` on
`Batwing_Rescue_01` — a **different vehicle** (`ANIMATIONS.md:1260` region), not the Batmobile.

---

## 3. The flame, decoded: five emitters, 0.15–0.35 s

`SideExhaust_Boost` (`PARTICLES_FEATURES.md:185`; `PARTICLES.md:1278-1302`), bound to `Exhaust.SideExhaust_Boost`:

| emitter | kind | start_size | start_velocity (cm/s) | start_location (cm) | lifetime (s) | mesh |
|---|---|---|---:|---:|---:|---|---|
| outer flash | sprite | **50 … 80** | **300 … 500** (+50 lateral) | — | 0.15 | — |
| core puff A | sprite | **15 … 25** | 200 … 400 | — | 0.2–0.3 | — |
| core puff B | sprite | **15 … 25** | 200 … 400 | **[-5, 0, 16]** | 0.2–0.3 | — |
| flame A | mesh | **1.2 × 1.0 × 1.0 … 1.3 × 1.2 × 1.2 m** | 50 … 100 | — | 0.2–0.3 | `Engine.Firefly_JetMesh` (beam, **tiles 90**) |
| flame B | mesh | **1.2 … 1.3 m** | 50 … 100 | **[-5, 0, 16]** | 0.2–0.3 | `Engine.Firefly_JetMesh` (beam, tiles 90) |

Spawn rates **10 / 40 / 40 per s**; materials `Engine.INST_JetExhaust`, `Engine.MAT_Fire_Dissipate`.

The two companion systems:

| system | emitters | lifetime (s) | spawn /s | size | what it is |
|---|---:|---|---:|---|---|
| `SideExhaust_Burst` | 3 (sprite×2, light×1) | 0.1–0.3, 0.1–0.3, 0.2–0.4 | 13, 10 | 50–80 / 40–60 / 30–40 | the ignition crackle |
| `batmobileExhaust_burst` | 17 (light×2, mesh×2, sprite×9) | **0.05–1.5** | 4–15 | **0.9 m** jet mesh, 30–50 sprites | the throttle plume + the only `Engine.Fire_Distortion` (heat haze) |

**Colour over life (decoded, the part that reads as “flame size/intensity over time”):**

| system | start colour | over life |
|---|---|---|
| `SideExhaust_Boost` | **(0.9, 0.3, 0.1)** — orange | Scaleover life **(1.0, 0.6, 0.6) … (1.0, 1.0, 1.0)** |
| `batmobileExhaust_burst` | **(0.997, 0.578, 0.367)** — pale orange | **(1.0, 0.5, 0.5) … (1.0, 0.8, 0.8)** |
| `SideExhaust_Burst` | (not serialised) | **(1.0, 1.0, 1.0)** flat |

**UNKNOWN:** BmAK does **not** serialise a size-over-life curve for these emitters — the particle census stores
`start_size` min/max only (`PARTICLES_FEATURES.json` has keys `size`, `systems_with_size`; no
`*over_life*` key at all). So the flame's growth curve is **not in the data**; only its start size, lifetime and
colour ramp are. The build therefore *authors* the size curve (§6), and this report says so instead of quoting a
BmAK curve that does not exist.

---

## 4. The JC3 side: what exists, and what does not

### 4.1 Nozzle meshes — there is no nozzle part

`grep '"[^"]*nozzle[^"]*"' Research/JC3Grab/INDEX.jsonl` → **0 hits**. JC3's vehicle part meshes carry no
"nozzle"/"thruster"/"turbine" name for any car. What the fleet does have:

| candidate | file(s) | what it gives us |
|---|---|---|
| **fighter-jet mesh family** | `models/jc_vehicles/02_air/v4202_plane_capstone_fighterjet/fighterjet_*.rbm` (flap L/R lod1, hatch r_r lod1-3, wing inner lod1-5 + `innermshswap` copies) | curved engine-nacelle-shaped art to cannibalise as a nozzle bell |
| **jetski** | `editor/entities/jc_vehicles/03_sea/v1500_boat_solar_jetski/…_fins.vmodc` (a hinged fins module) | a water-jet nozzle is a **fin part**, not a mesh name |
| **JC3 booster on a car** | `editor/entities/jc_vehicles/01_land/v0300_…/modules/default/v0300_…_land_aerodynamics_ai.vmodc` and the nitro members | no geometry: JC3's "boost" is a **module + effect**, not a mesh |

So the nozzle **geometry is authored**: a cone/ring on the rear body part, 18 of them at the BmAK ring radius
(**34 cm** ring, **63.5 cm** behind `Jet_Root`), each 0.9 m long to match the BmAK plume mesh's start size. The
JC3 binding is the one a light uses: `part` + `deformable_transform` node (`LIGHT_SYSTEM.md` §6), which is also
how `exhaust-and-heat-plan.md` §4 already planned the 18 + 2 attach nodes.

### 4.2 The effect files that carry the flame

| role | JC3 file | size | emitters | max particles per emitter | property range | source |
|---|---|---:|---:|---|---|---|
| **nitrous plume (boost)** | **`effects/jc_vehicles/exhaust/car_cycle_base_nitrous.effc`** | **15,359 B** | **8** | `[20, 5, 30, 20, 10, 1, 1, 1]` | `[10.0, 500.0]` | `FX9_HAZE.md:76` |
| nitrous, dual outlet | `car_cycle_base_dual_nitrous.effc` | — | — | — |   | `FX_TABLE.jsonl` |
| nitrous, single-outlet variant | `car_cycle_base_nitrous_c.effc`, `…_v0602.effc` | — | — | — | — | `FX_TABLE.jsonl` |
| **jet plume** | **`effects/jc_vehicles/exhaust/jet_exhaust_base.effc`** | **18,927 B** | **11** | `[64, 64, 20, 16, 16, 16, 16, 1, 100, 16, 16]` | `[20.0, 100.0]` | `FX9_HAZE.md:77` |
| crackle | `jet_cargo_exhaust_base.effc` | — | 7 | `[10, 30, 16, 16, 1, 16, 16]` | `[-1.0, 500.0]` | `exhaust-and-heat-plan.md` §3 |
| **flame** | **`effects/fire/generic_fire_01.effc`** (single-plume: `generic_fire_single_01.effc`) | — | 4 | `[14, 1, 20, 5]` | `[20.0, 100.0]` | same |
| heat shimmer | `car_speedrom_heater.effc` | 14,703 B | 5 | `[10, 60, 3, 7, 100]` | `[20.0, 100.0]` | `FX9_HAZE.md:74` |

All six are **ADF v4** inside an `.ee` (not standalone archive entries: only `car_cycle_base.effc` is a
standalone path, per `grep '"effects/jc_vehicles/exhaust/'`). No `.effc` contains a single string — **0 strings in
955 files** (`FX9_HAZE.md` §3) — so no emitter can be traced to a texture or shader by name.

### 4.3 The decoded scale timelines of `car_cycle_base_nitrous.effc`

`jc3fx.py` cannot open this file by path (it lives inside
`dlc/bavarium_sea_heist/editor/entities/jc_vehicles/01_land/v0000_car_autostraad_oldjeep/v0000_car_autostraad_oldjeep_blackhand_01.ee`,
`FX_TABLE.jsonl`), so it was read the way `jc3fx.py` reads inner files: AAF → SARC → slice → `jc3adf`. The file
decodes to **1,953 rows, 36 types, 212 arrays, 8 emitters, 52 `Params[]`, 17 `Timelines[]`**.

`Timelines[]` is where an `.effc` stores its **curve over life**: `StartX`, `EndX`, `XScaleRecip` and a
`ControlPointsY[]` of **int8** values (−128…127), i.e. **normalised, /127**. The first six, as stored (each is a
4-channel × 4-key curve, the channels repeated identically in these six):

| timeline | StartX | EndX | XScaleRecip | ControlPointsY (4 keys) | normalised (÷127) |
|---|---:|---:|---:|---|---|
| TL0 | 0.000 | **0.2749** | 3.6371 | 0, 1, **77**, 64 | 0.000 → 0.008 → **0.606** → 0.504 |
| TL1 | **0.2749** | 1.000 | 1.3792 | 64, 31, 0, 0 | 0.504 → 0.244 → 0.000 → 0.000 |
| TL2 | 0.000 | 1.000 | 1.0000 | **127, 127, 127**, 0 | 1.000 → 1.000 → 1.000 → 0.000 |
| TL3 | 0.000 | 0.000 | 0.0000 | 64, 64, 64, 0 | constant 0.504 |
| TL4 | 0.000 | **0.4994** | 2.0024 | 0, 64, **63**, 64 | 0.000 → 0.504 → 0.496 → 0.504 |
| TL5 | **0.4994** | 1.000 | 1.9976 | 64, 64, 64, 0 | 0.504 flat |

Read as intensity/scale over the emitter's life, the shape is: **snap in over the first 27.5 % of life to ~0.61,
hold ~0.50, decay to 0 by the end** (TL0+TL1), while TL2 is the on/off channel (full, full, full, off) and
TL4/TL5 are a slower 0→0.50 ramp split at mid-life. Those are the only decoded flame/plume curves in the JC3
fleet that this project can point at.

---

## 5. The mapping, member by member

| BmAK | JC3 carrier | reuse? | the value we set |
|---|---|---|---|
| 18-nozzle ring, `MESH_Batmobile_Jet_V01`, 0.9 m | **authored cone** on the rear body part, 18 `deformable_transform` nodes at r 34 cm / z 2.989 m | **author** | 18 nodes; 1 node (`Jet_Root`) for the first pass |
| `Firefly_JetMesh` flame, 1.2–1.3 m, beam tiles 90 | `generic_fire_01.effc` on the same nodes, or the mesh emitter inside `car_cycle_base_nitrous.effc` | **reuse effect** | attach at the nozzle mouth, offset `[-5, 0, 16]` cm as BmAK does |
| `SideExhaust_Boost` (0.15–0.35 s, 5 emitters) | `car_cycle_base_nitrous.effc` (8 emitters, `[10,500]`) | **reuse** | gate on the JC3 nitro state |
| `batmobileExhaust_burst` (0.05–1.5 s, 17 emitters, `Fire_Distortion`) | `jet_exhaust_base.effc` (11 emitters, `[20,100]`) + `car_speedrom_heater.effc` for the distortion | **reuse** | ring nodes |
| `SideExhaust_Burst` (0.1–0.4 s, crackle) | `jet_cargo_exhaust_base.effc` (7 emitters) | **reuse** | side nodes |
| deploy 0.600 s / retract 0.833 s | JC3 hinge or part-swap; the flap hinge is the carrier (`MOVING_PARTS.md` `flaps_T`, `DOOR_ANGLES.md`) | **map** | **0.600 s** open, **0.833 s** close, 30 fps keys |
| colour over life (0.9,0.3,0.1) → white | `.effc` timeline colour channels (TL0/TL1 shape) | **map** | ramp per §6.3 |

---

## 6. The scale table, per time step

### 6.1 What BmAK gives, and what we must author

BmAK gives: start size (1.2–1.3 m mesh; 50–80 outer sprite; 15–25 core sprites), lifetime (0.15 / 0.2–0.3 /
0.35 s), spawn rate (10/40/40 per s), and a colour ramp. It does **not** give a size-over-life curve (§3).
The JC3 side gives a **normalised curve** (§4.3) but no absolute scale (the `.effc` has no strings and its
`Params[]` are 52 unnamed floats, e.g. 100.0, 0.05, 0.1, 0.01, 1.0, 4.0, 8.0, 5.0, 1000.0).

So the table below is the **authored** scale ramp: BmAK's absolute start sizes on the x-axis of its own
lifetime, with the shape taken from the JC3 timeline it will run on (TL0/TL1). It is a mapping, not a decoded
BmAK curve, and it is the one thing to review before the effect is bound.

### 6.2 Flame mesh (`Firefly_JetMesh` equivalent) — lifetime 0.30 s

| t (s) | t / life | **scale** | length (m) | source of the shape |
|---:|---:|---:|---:|---|
| 0.000 | 0.00 | **0.00** | 0.00 | TL0 key 1 (y 0) |
| 0.083 | 0.275 | **1.00** | **1.30** | TL0 key 3 (77/127 = 0.606 of the range, applied to the 1.2–1.3 m start size → 1.30 m at peak) |
| 0.150 | 0.50 | **0.83** | 1.08 | TL1 key 1 (64/127 = 0.504 → held) |
| 0.225 | 0.75 | **0.40** | 0.52 | TL1 key 2 (31/127 = 0.244) |
| 0.300 | 1.00 | **0.00** | 0.00 | TL1 key 3/4 (0) |

### 6.3 Colour / intensity (the part BmAK does serialise)

| t (s) | BmAK `SideExhaust_Boost` | BmAK `batmobileExhaust_burst` | to set |
|---:|---|---|---|
| 0.00 | (0.90, 0.30, 0.10) | (0.997, 0.578, 0.367) | start orange, alpha 1 |
| 0.15 | × (1.00, 0.60, 0.60) | × (1.00, 0.50, 0.50) | red falls slower than green/blue → whitens |
| 0.30 | × (1.00, 1.00, 1.00) | × (1.00, 0.80, 0.80) | near-white, fading out |

### 6.4 The sprites around the mesh

| t (s) | outer sprite (50 → 80) | core sprites (15 → 25) | spawn |
|---:|---:|---:|---|
| 0.00 | 50 | 15 | 40 /s at t < 0.15, then 10 /s |
| 0.15 | 65 | 20 | — |
| 0.25 | 80 | 25 | burst ends (lifetime 0.15 for the outer) |
| 0.35 | — (last core dies) | 25 → 0 | 0 |

Velocities stay **300–500 cm/s** outer, **200–400 cm/s** core, **50–100 cm/s** mesh — decoded, do not change
them; they are what makes the plume read as thrust rather than smoke.

### 6.5 The deploy timeline we drive it from

| t (s) | event |
|---:|---|
| 0.000 | `Jet_Boost` starts; nozzles begin to open; effect **off** |
| **0.600** | `Jet_Boost` ends (19 keys) — **boost plume on** (`car_cycle_base_nitrous.effc`) |
| 0.600 → 0.900 | flame mesh life 0.30 s runs as §6.2 |
| **1.433** | retract complete if `Jet_Close` starts at 0.600 (**0.600 + 0.8333**) |

BmAK's own boost state is 2.0 s (`BoostDuration`) with a 12 s cooldown (`t_boost_coverage.py` PASS line), so in
practice the ring is open for the whole 2 s and closes on release — the 0.6/0.833 s numbers are the *edges*.

---

## 7. Checks run

| check | result |
|---|---|
| mesh sizes re-read | `MESH_Batmobile_Jet_V01` 114,160 B export 176021; `Firefly_JetMesh` 5,270 B export 175976 (`SM_BOUNDS.json:389-393,440-444`) |
| nozzle geometry | 18 bones, ring z 2.989 m, x 0…0.307, y 0.232…0.857 (`BONES.md:84-103`) |
| deploy/retract | 0.600 s / 19 keys / 30 fps / 21 tracks; 0.8333 s / 26 keys / 30 fps / 26 tracks; 0 notifies |
| flame emitters | 5 (light×1, mesh×2, sprite×2), lifetimes 0.15–0.35, spawn 10/40/40, sizes 15–80 and 1.2–1.3 m (`PARTICLES_FEATURES.md:185`, `PARTICLES.md:1278-1302`) |
| colour over life | (0.9,0.3,0.1) → (1.0,0.6,0.6)…(1.0,1.0,1.0); burst (0.997,0.578,0.367) → (1.0,0.5,0.5)…(1.0,0.8,0.8) |
| size-over-life in BmAK | **absent** — `PARTICLES_FEATURES.json` keys `size`, `systems_with_size` only |
| JC3 nozzle name | `grep -o '"[^"]*nozzle[^"]*"' INDEX.jsonl` → **0** |
| JC3 effect identity | `car_cycle_base_nitrous.effc` 15,359 B, 8 emitters, `[20,5,30,20,10,1,1,1]`, `[10,500]` (`FX9_HAZE.md:76`) |
| JC3 timelines decoded | 1,953 rows, 17 timelines, 52 Params, 8 emitters (AAF→SARC→`jc3adf`, container per `FX_TABLE.jsonl`) |
| scale arithmetic | 77/127 = 0.606, 64/127 = 0.504, 31/127 = 0.244; 1.30 m peak from 1.2–1.3 m start |
| deploy vs retract | 0.600/0.8333 = 0.72 |

Probe artefacts: none written for this card beyond this report (the `.ee` in §4.3 was read in memory; no file was
extracted to disk).

---

## 8. Change record (per `AGENTS.md`)

1. **Intended change:** add one report that describes the BmAK booster mesh, its deploy motion and flame over
   time, names the JC3 nozzle/effect carriers and gives the per-step scale values.
2. **File:** `tmp/freebuff/reports/booster-mesh-and-flame-plan.md` (this file). Correct file because the brief
   names it and every comparable plan lives in `tmp/freebuff/reports/`; no `Research/` table, build, entity,
   module, `.effc`, graph or install is regenerated.
3. **Revert:** delete this file. Nothing else changed.

---

## 9. UNKNOWNs

| # | UNKNOWN | what settles it |
|---|---|---|
| U-1 | the flame's size-over-life curve in BmAK | not serialised (`PARTICLES_FEATURES.json` has no `*over_life*` key); only a runtime capture or the cooked particle graph's required-module arrays would show it |
| U-2 | which of the 18 nozzles are actually open/visible in game | the jet mesh LODs (`MESHES.md`); the ring is a rig, not proof of 18 openings |
| U-3 | which `.effc` timeline index is *scale* vs *alpha* vs *rotation* in `car_cycle_base_nitrous.effc` | the 17 timelines have no names; a runtime capture, or a decode of the emitter→timeline binding (`Instantiators[].Parameters.FloatParamIndices[]`) against a known effect |
| U-4 | whether JC3's nozzle must be a `part` or may be a plain `deformable_transform` on the body | `LIGHT_SYSTEM.md` §6 proves the node chain for lights only; `exhaust-and-heat-plan.md` U4 repeats this |
| U-5 | the JC3 boost→effect trigger (which module plays `car_cycle_base_nitrous`) | the `custom_land_global.vmodc` nitro block (`USAGES.md:552`) names parameters, not the effect path; needs the effect-attachment module walk |
| U-6 | whether `batmobileExhaust_burst`'s `Fire_Distortion` maps to `car_speedrom_heater.effc` or a generic distortion material | 0 strings in 955 `.effc`; only a visual capture distinguishes them |
