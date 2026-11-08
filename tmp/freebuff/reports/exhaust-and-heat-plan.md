# Exhaust & heat — what BmAK emits, and the JC3 effect files that come closest

**Question:** what comes out of the BmAK exhaust at idle, under throttle and during boost (sizes,
timings); which JC3 flame / smoke / heat-haze effect files come closest; which attach points are
needed.

**Verdict in one paragraph.** BmAK ships **three** exhaust particle systems and **no idle system**.
`batmobileExhaust_burst` is the throttle/afterburner plume: **17 emitters**, lifetimes **0.05–1.5 s**,
emitter sizes from a **0.9 m** jet mesh at **+32 cm** to **30–50** sprites at **+15 cm**, spawn rates
**4–15/s** on the main emitters, and the only distortion material in the set
(**`Engine.Fire_Distortion`**) — that is BmAK's "heat haze", and it is part of the exhaust effect
rather than a separate volume. `SideExhaust_Boost` is the boost plume: **5 emitters**, lifetimes
**0.15–0.35 s**, sizes **50–80** at velocities **300–500 cm/s** plus a **1.2–1.3 m**
`Engine.Firefly_JetMesh` flame, spawn **10/40/40 per s**, materials
**`Engine.INST_JetExhaust` + `Engine.MAT_Fire_Dissipate`**, offset **[-5, 0, 16] cm** from its
attach. `SideExhaust_Burst` is the ignition crackle: **3 emitters**, **0.1–0.4 s**, sizes 30–80,
materials **`Engine.Fire_Flames3` / `Engine.explosion_med_01`**. Idle is **UNKNOWN**: the package has
`ExhaustComponent0` and `BoosterComponent0` components but no system is named "idle", and the
component→template link is not decoded. On the JC3 side the closest files are
**`effects/jc_vehicles/exhaust/jet_exhaust_base.effc`** (11 emitters, max 64, the jet-plume carrier),
**`effects/jc_vehicles/exhaust/car_cycle_base.effc`** (2 emitters, the steady car exhaust —
idle/drive), **`effects/jc_vehicles/exhaust/car_cycle_base_nitrous.effc`** (8 emitters, the boost
carrier), **`effects/jc_vehicles/exhaust/car_speedrom_heater.effc`** (the **only** "heat" path among
955 `.effc` files) and **`effects/fire/generic_fire_01.effc`** (flame). The attach points needed are
the **18 jet nozzle bones** (`Batmobile_Rig_Jet_Nozzle_001…018`, all at **z = 2.989 m**), their
parents `Batmobile_Rig_Jet_Root` (**z 2.354 m**) / `JetSMove` (**z 1.343 m**) and
`Batmobile_Rig_Jet_Thruster` — **none of which exists in a JC3 part**, so each becomes a
`deformable_transform` node on a rear body part.

Labels: **decoded** = read from the cited file; **derived** = arithmetic/mapping; **UNKNOWN** =
searched and absent, with where it would be settled.

---

## 1. BmAK's three exhaust systems (decoded)

Source: `Research/BatmobileGrab/PARTICLES.md` (206 systems, 1,433 emitters, cooked
lifetime/spawn/size/velocity tables) and `FX9_HAZE.md` §6 (the `afterburner-exhaust` group).

| system | role | emitters | kinds | lifetime (s) | spawn (/s) | materials |
|---|---|---:|---|---|---|---|
| `batmobileExhaust_burst` | light emitter | **17** | light, mesh, none, sprite | **0.05 – 1.5** | **15, 4, 5, 10** | **`Engine.Fire_Distortion`** |
| `SideExhaust_Boost` | light emitter | **5** | light ×1, sprite ×2, mesh ×2 | **0.15 – 0.35** | **10, 40, 40** | `Engine.INST_JetExhaust`, `Engine.MAT_Fire_Dissipate` |
| `SideExhaust_Burst` | light emitter | **3** | sprite ×2, light ×1 | **0.1 – 0.4** | **13, 10** | `Engine.Fire_Flames3`, `Engine.explosion_med_01` |

### 1.1 Sizes and offsets (the serialised vectors)

`batmobileExhaust_burst`, per emitter (the 1079-line vector table):

| emitter | start_size (cm / m) | start_location (cm) | mesh |
|---|---:|---:|---|
| jet mesh | **0.9 × 0.9 × 0.9 m** | **+32 cm** | `Engine.MESH_Batmobile_Jet_V01` |
| plume sprite | **30 – 50** | **+15 cm** | — |
| the other 15 | (no vector serialised; inherit required-module defaults) | +15 cm | — |

`SideExhaust_Boost`:

| emitter | start_size | start_velocity (cm/s) | start_location | mesh |
|---|---:|---|---:|---|
| outer sprite | **50 – 80** | **300 – 500** (+50 lateral) | — | — |
| core sprite ×2 | **15 – 15 – 15** to **25 – 25 – 25** | **200 – 400** | **[-5, 0, 16]** for one | — |
| flame mesh ×2 | **1.2–1.3 m** (beam tiles 90) | **50 – 100** | **[-5, 0, 16]** for one | `Engine.Firefly_JetMesh` |

`SideExhaust_Burst`:

| emitter | start_size | start_velocity |
|---|---:|---|
| flash | **50 – 80** | 50 – 300 |
| puff | **40 – 60** | **50 – 200** forward, **-80 … +50** lateral |
| spark | **30 – 40** | 0 – 200 (+20 lateral) |

### 1.2 Idle — the honest answer

* There is **no system named "idle"** among the 206.
* The actor carries **`ExhaustComponent0`** and **`BoosterComponent0`**
  (`ASSETS.md` §ParticleSystemComponent), so the plumbing exists, but the census records component
  names, not their `Template` → **which system idles is UNKNOWN**.
* `FX9_HAZE.md` §6 also records a **`heat-steam` feature group with 0 systems, 0 rows, 0 emitters**:
  "no system of that name ships in the 206". So BmAK has no separate idle-steam puffer either.
* Nothing in the 206 has a lifetime long enough for a steady idle plume (the longest in the exhaust
  set is 1.5 s), which is consistent with an idle effect that is either absent or a looping short
  system — but the loop flag is not decoded. **UNKNOWN.**

### 1.3 Heat haze

BmAK has **no dedicated heat-haze/distortion volume**. The distortion-capable materials in the 206
are: `Engine.Distort_s` (gel rounds), `Engine.steam` (muzzle flashes, casings, small rocket
explosion), `Materials.SeismicScan_Distortion` (sonar), `Engine.AR_Distortion` (EMP),
`Engine.Distortion_mesh` / `Shaders.Engine_Distortion` (Batwing), and
**`Engine.Fire_Distortion` — only in `batmobileExhaust_burst`**. That is the single heat-shimmer
carrier, and it rides the exhaust burst (0.05–1.5 s), not the idle.

---

## 2. Attach points BmAK uses

From `BONES.md` (bind transforms, metres relative to the parent):

| bone | parent | x | y | z |
|---|---|---|---:|---:|
| `JetSMove` | `Batmobile_Chassis_Mesh` | 0.000 | 0.543 | **1.343** |
| `Batmobile_Rig_Jet_Root` | `JetSMove` | 0.000 | 0.544 | **2.354** |
| `Batmobile_Rig_Jet_Nozzle_001` | `Batmobile_Rig_Jet_Root` | 0.000 | 0.857 | **2.989** |
| `…_002` | `Batmobile_Rig_Jet_Root` | 0.107 | 0.838 | 2.989 |
| `…_004` | `Batmobile_Rig_Jet_Root` | 0.270 | 0.700 | 2.989 |
| `…_005` | `Batmobile_Rig_Jet_Root` | 0.307 | 0.599 | 2.989 |
| `…_006` | `Batmobile_Rig_Jet_Root` | 0.307 | 0.490 | 2.989 |
| `…_007` | `Batmobile_Rig_Jet_Root` | 0.270 | 0.388 | 2.989 |
| `Batmobile_Rig_Jet_Thruster` | `Batmobile_Rig_Jet_Root` | 0.000 | 0.544 | 2.354 |

**18 nozzles** (`_001` … `_018`) sit on a ring at **z = 2.989 m**, y 0.388…0.857 m, x 0…0.307 m —
i.e. a **~34 cm radius ring, 63.5 cm behind the jet root**. The two side exhausts use the *weapon*
side roots in the transform pass (`Batmobile_Rig_Weapons_Sides_Root` carries `SideExhaust_*` in the
clip track lists), not the nozzle ring — so the boost plume and the main plume are on **different
bones**, which matters when picking JC3 attach points.

---

## 3. JC3 effect files that come closest

All from `Research/JC3Grab/FX9_HAZE.md` (955 `.effc`, 8 render-block hashes, 53 emitter types;
**0 string values in any effect file**, so no effect can be traced to a texture or shader by name).

| BmAK | JC3 file | emitters | max particles | property range | why this one |
|---|---|---:|---|---|---|
| **jet plume / throttle** (`batmobileExhaust_burst`, 17 emitters, 0.05–1.5 s) | **`effects/jc_vehicles/exhaust/jet_exhaust_base.effc`** | **11** | `[64, 64, 20, 16, 16, 16, 16, 1, 100, 16, 16]` | `[20.0, 100.0]` | the fleet's jet-plume carrier; nearest emitter count and the same 20–100 property window |
| **steady exhaust / idle-drive** (`car_cycle_base` shape) | **`effects/jc_vehicles/exhaust/car_cycle_base.effc`** | **2** | `[50, 50]` | `[-1.0, 50.0]` | plain two-emitter car exhaust; the only candidate for a continuous low-rate plume |
| **boost plume** (`SideExhaust_Boost`, 5 emitters, 0.15–0.35 s) | **`effects/jc_vehicles/exhaust/car_cycle_base_nitrous.effc`** | **8** | `[20, 5, 30, 20, 10, 1, 1, 1]` | `[10.0, 500.0]` | 8 emitters incl. a `[1562615418]` + `[522936798]` pair — the nitrous-only render blocks |
| **boost burst** (`SideExhaust_Burst`, 3 emitters, 0.1–0.4 s) | `effects/jc_vehicles/exhaust/jet_cargo_exhaust_base.effc` | **7** | `[10, 30, 16, 16, 1, 16, 16]` | `[-1.0, 500.0]` | short-lived, low-count, matches the 0.1–0.4 s crackle better than the jet base |
| **flame** | **`effects/fire/generic_fire_01.effc`** (or `generic_fire_single_01.effc`) | **4** | `[14, 1, 20, 5]` | `[20.0, 100.0]` | the stock flame; `generic_fire_single_01` is the single-plume variant |
| **heat haze / distortion** (`Engine.Fire_Distortion`) | **`effects/jc_vehicles/exhaust/car_speedrom_heater.effc`** | **5** | `[10, 60, 3, 7, 100]` | `[20.0, 100.0]` | **the only path containing "heat" in all 955 `.effc`**; also the only one with a 3-count emitter (a subtle shimmer) |
| engine fire (damage) | `effects/cinematic/dmg_fire_engine.effc` | **5** | `[50, 50, 100, 100, 1]` | `[20.0, 500.0]` | if the exhaust should set the engine alight |

Two hard limits on all of them:

* **No `.effc` names anything** — 955 files, **0 string values**. So "which emitter is the flame" can
  never be read from the file; only the render-block hash counts (`3012430835` on 930 files is the
  common sprite block, `2199516487` on 487 the second).
* **`haze`, `distort`, `refract`, `vapor`, `shimmer`, `warp` return 0 paths each**; `heat` returns
  exactly 1 (`car_speedrom_heater.effc`). A heat haze in JC3 is therefore an effect *we* point at,
  not one the naming gives us.

---

## 4. The attach points to add

BmAK's nozzle ring does not exist in a JC3 part, so each plume needs a node on a JC3 part — the same
`part` + `deformable_transform` chain that a light uses (`LIGHT_SYSTEM.md` §6: the
`deformable_transform` node is "not in the RBM, not in the parts `bones` array and not in the deform
table", so the part must carry the node).

| plume | BmAK source | JC3 attach | count |
|---|---|---|---:|
| main jet | `Batmobile_Rig_Jet_Nozzle_001…018`, ring r ≈ 34 cm at z 2.989 m | 18 nodes on the rear body part, spaced on that ring | **18** |
| jet root (fallback) | `Batmobile_Rig_Jet_Root` z 2.354 m | 1 node, used if 18 is too many | 1 |
| side boost L/R | `Batmobile_Rig_Weapons_Sides_Root` (the clip track that carries `SideExhaust_Boost`) | 2 nodes, one per side, offset `[-5, 0, 16] cm` as the effect already expects | 2 |
| heat haze | same as the main jet, `car_speedrom_heater.effc` | reuse the 18 nodes | 0 new |
| flame | same as the main jet, `generic_fire_01.effc` | reuse | 0 new |

**Minimum viable set: 18 + 2 = 20 attach nodes**, of which 18 are a ring that can be reduced to 1
(`Jet_Root`) for the first pass. The effect file's own `start_location` (`+32 cm`, `+15 cm`,
`[-5,0,16]`) is measured from whatever node it is spawned at, so the ring nodes should be placed at
the **nozzle mouths** and let the effect's +15/+32 cm offsets carry the rest.

---

## 5. What the build should do (and not do)

1. **Idle**: use `car_cycle_base.effc` (2 emitters, max 50) — it is the only continuous car exhaust
   in the fleet. Do **not** claim it is BmAK's idle; BmAK's idle is UNKNOWN (§1.2).
2. **Throttle**: `jet_exhaust_base.effc` on the ring; it is the closest in emitter count (11 vs 17)
   and property window.
3. **Boost**: `car_cycle_base_nitrous.effc` for the plume + `jet_cargo_exhaust_base.effc` for the
   crackle, on the two side nodes.
4. **Heat haze**: `car_speedrom_heater.effc`, spawned from the same ring, gated by the same boost
   state — this is the only heat-named carrier and it is cheap.
5. **Do not author `.effc` contents.** The files carry no strings and the parameters are not decoded;
   pick and attach, never edit.

---

## 6. UNKNOWNs, each with its settler

| # | unknown | settler |
|---|---|---|
| U1 | which system `ExhaustComponent0` / `BoosterComponent0` actually play | the component's `Template` tag in the archetype (per-component walk, not the census) |
| U2 | whether BmAK has any idle exhaust at all | same walk; plus the loop flag on whichever template it names |
| U3 | the 15 `batmobileExhaust_burst` emitters with no serialised vector | required-module defaults in the cooked graph |
| U4 | JC3's effect→part binding mechanism (does `.effc` attach through `deformable_transform` like a light?) | the vehicle's VFX/emitter module; `LIGHT_SYSTEM.md` proves the node chain for lights only |
| U5 | which JC3 render-block hash is a flame vs a smoke vs a distortion | 0 strings in 955 files; only a runtime capture distinguishes them |
| U6 | whether `car_speedrom_heater.effc` is actually a heat-haze volume rather than an engine heater | its 5 emitters and `[20,100]` property range fit a shimmer, but nothing names it |
| U7 | how many of the 18 nozzles are visible in game | `MESHES.md` / the jet mesh; the ring is a rig, not proof of 18 openings |

## 7. Sources

**BmAK:** `Research/BatmobileGrab/PARTICLES.md` (the three systems' emitter counts, kinds, lifetimes,
spawn rates, materials, and every serialised start_size/start_velocity/start_location vector),
`FX9_HAZE.md` §6 (the `afterburner-exhaust` group and the 0-system `heat-steam` group),
`BONES.md` (`JetSMove`, `Batmobile_Rig_Jet_Root`, the 18 nozzles, `Jet_Thruster`, with bind
transforms), `ASSETS.md` (`ExhaustComponent0`, `BoosterComponent0`,
`Engine.MESH_Batmobile_Jet_V01`, `Engine.Firefly_JetMesh`), `ANIMATIONS.md` (the `ActivateExhaust`
anim notify on `Batwing_Rescue_01`, the only exhaust *trigger* named in the anim data),
`AUDIO.md` (`Play_Batmobile_RocketTails` / `Stop_…` — the audio half of boost).
**JC3:** `Research/JC3Grab/FX9_HAZE.md` (955 `.effc`, the path-keyword census, the per-effect
emitter/max-particle/property table, the 8 render-block hashes),
`LIGHT_SYSTEM.md` §6 (the part + `deformable_transform` binding rule this report reuses for
attachments).
