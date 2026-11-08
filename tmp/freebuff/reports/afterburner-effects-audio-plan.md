# Afterburner show: the BmAK boost sequence, element by element, and its JC3 carriers

**Scope.** One boost press on the BmAK Batmobile, from the frame it starts to the frame the
cooldown begins, listing every visual and audio element **in time order** — flame mesh, particles,
light, sound start/loop/stop, camera kick — each matched to a JC3 nitro or jet effect file, with the
pieces JC3 does not already carry written out as **new private effect definitions**.

**Not in scope / not done.** No game launch, no attach, no install, no build write, no ledger,
`GRAB_BACKLOG.md` or tracker edit. Every value below is a static decode or a derivation shown with
its arithmetic. Where a file is absent I write **UNKNOWN** and name the file or probe that settles
it; no JC3 implementation is filled in from plausibility.

**One-line answer.** JC3 already has four of the six elements: the **flame** (T-FX3's
`car_cycle_base_dual_nitrous.effc` on `EngineNitro`), the **particle burst** (same file's two
`exhaust_upgrade_nitrous*` emitters), the **start/loop/stop audio** (the `vehicles` bank's premium
nitro event, which ships all three samples), and the **camera kick** (`CameraShakeModifierParams` in
`vehicle_camera_shake.ctunec`). Two are genuinely missing and get private definitions: the **jet
cone mesh** (no JC3 nitro `.effc` carries a mesh emitter) and the **boost light** (the `.effc`
vocabulary has no light member at all, and no `VehicleDynamicLights` behaviour is boost-driven).

---

## 1. Evidence inventory

### 1.1 BmAK side (what the sequence is made of)

| element | decoded fact | source |
|---|---|---|
| boost window | `BoostDuration` **2.0 s**, `BoostCooldown` **12.0 s** (tier 0) | `CLUSTER.md:50,51`, carried through the checker in `tmp/freebuff/reports/boost-rows-proposal.md` (P-B5/P-B6) |
| boost cap / blend | `FakeExtaSpeedDecel` 2000 cu/s², no duration member in the JC3 donor block | `CLASS_DEFAULTS.md:267`, same report P-B7 |
| particle components | `Default__RVehicleBatmobile.ab` and `.ABW` are **`ParticleSystemComponent`s** (4 declarations across `RVehicleBatmobile` / `RVehicleBatmobileBase`) | `Research/BatmobileGrab/CLASS_DEFAULTS.json` (grep `RVehicleBatmobile.ab`) |
| flame system | `batmobileExhaust_burst`, **13** emitter rows in the lifetime/rate census and **17** graph objects in the render census; render modules **`light, mesh, none, sprite`**; required module `batmobileExhaust_burst.ParticleModuleRequired`; 18 objects | `PARTICLES.md:143`, `PARTICLES.md:501` |
| flame mesh | emitter 4888 carries mesh **`Engine.MESH_Batmobile_Jet_V01`**, `start_size` `[0.9,0.9,0.9]`, `start_location` `[32,0,0]` | `PARTICLES.md:1250-1254` |
| burst emitters | emitter 4894 `start_size` `[30,0,0]…[50,0,0]` at `[15,0,0]`; six more emitters all pinned at `[15,0,0]` | `PARTICLES.md:1256-1277` |
| burst timing | lifetimes `0.7-0.8, 0.75, 0.5-1.5, 0.05-0.1 …`; rates `15, 4, 5, 10 …` | `PARTICLES.md:143` |
| side jets | `SideExhaust_Boost`, **5** emitters, `light, mesh, sprite`; mesh **`Engine.Firefly_JetMesh`** on emitters 4908/4905 at `[−5,0,16]`, scale `1.2–1.3`, velocity `50–500`; sizes `50–80` at velocity `300–500` | `PARTICLES.md:144,502,1278-1302` |
| shutoff puff | `SideExhaust_Burst`, **3** emitters, `light, sprite`; sizes `40–60`; lifetimes `0.1-0.3, 0.1-0.3, 0.2-0.4`; rates `13, 10` | `PARTICLES.md:145,503,1304-1314` |
| cinematic twins | `Batwing_Booster_CINE` (10/11 emitters, `light, mesh, none, sprite`) and `Batwing_Exhaust_P` (18/11 emitters, `mesh, sprite, trail`) | `PARTICLES.md:184,188,395,399` |
| audio: start / stop | `Play_Batmobile_RocketTails` **3 rows** and `Stop_Batmobile_RocketTails` **3 rows**; group `afterburner` = 6 rows / 2 events; both `missing-bank` (`Engine.VEH_Tank_Missiles`), **0 WEMs, no RTPC**; *"no separate boost bed is an event in these packages"*; loop evidence is the `Stop_` counterpart | `AUDIO_FEATURES.md` afterburner group + §Gaps + §Missing |
| camera kick | boost adds a **35-unit shake** (`BatmobileBoostCameraShake`); the `AdvancedOptions` child carries a **0.1 s interval** and **2,000 / 10,000** limits; wheelspin is `50×50×25` | `CAMERA.md:189-190` |
| camera FOV | 85° base → **95° on boost**, +10° by speed to 108 km/h | `CAMERA.md:183` |

### 1.2 JC3 side (what already exists to receive it)

| element | decoded fact | source |
|---|---|---|
| flame file | `effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc`, hash `-776668445`, **20,671 B, 3,161 rows**; the two `EngineNitro` (4197885156) emitters `exhaust_upgrade_nitrous2` / `exhaust_upgrade_nitrous`; already placed on socket `Afterburner` (bone `JetSMove`, `[-0.009578, 0.537762, 3.393177] m`) | `tmp/freebuff/reports/fx3-afterburner-apply.md` §2; `Working/Effects/bm_fx_edits.json` |
| nitro effect family | **9** `*nitrous*.effc`: `car_cycle_base_dual_nitrous`, `car_cycle_base_nitrous`, `car_cycle_base_nitrous_c`, `car_cycle_base_nitrous_v0602`, `helicopter_base_nitrous`, `minetruck_cycle_base_nitrous`, `monstertruck_base_nitrous`, `boat_splash_nitrous`, `jetski_splash_nitrous` | `FX_TABLE.jsonl` (path census) |
| module-side trigger | `dynamic_nitrous` (397752766) on 14 vehicles; object-side `Effect` 3518298851 on 28 objects / 17 vehicles, unnamed | `USAGES.md:552-577` |
| audio chain | usage `EngineNitro` → `dynamic_nitrous` → object `Sound` GUID **`f74ea43b-a8ac-4548-ad27-b92fd40a516d`** (202 objects / 172 vehicles) → `vehicles` bank **EVTS ordinal 249, 195 B** → samples **56 `jc3_veh_land_premium_nitro_start`, 150 `jc3_veh_land_premium_nitro_loop`, 355 `jc3_veh_land_premium_nitro_stop`** | `USAGES.md:546-559,579-584` |
| camera shake carrier | `editor/entities/jc_cameras/vehicle_cameras/shake/vehicle_camera_shake.ctunec`, root **`CameraShakeModifierParams`**, 302 FX_TABLE records; family root appears in only 3 tunes (vehicle/shake, `ctune_templates/camera_shake`, character/shake) | `FX_TABLE.jsonl` (root census) |
| shake member domain | `ShakeAnimations[]`: `Control.Duration` **1.0 … 10.0** (585 rows), `Control.Looping` 0/1, `Control.AutoStart` 0/1, `EaseInTime` 0 … 0.5, `EaseOutTime` 0.1 … 0.5, `StartMessage` / `StopMessage` / `ParameterMessage` (strings), `TranslationMaxAmplitude` **0 … 0.5**, `RotationMaxAmplitude` **0.4 … 10**, `TranslationMaxFrequency` 5 … 30, `RotationMaxFrequency` 9 … 40, `TranslationFrequencyScale` 0.5 … 30, `RotationFrequencyScale` 1.2 … 40; **590** `ShakeAnimations` rows fleet-wide | `FX_VOCAB.json` keys `.ctunec\tShakeAnimations*` |
| car camera tune | `car_base.ctune` (63 records) reached from the entity by `CarCameraRef` → `CCameraObject SharedCarCamera` → `CCameraModifier`; `car_base.ctune` → `bat_base.ctune` is the same 14-byte path | `CAMERA.md:220-228`, `T6_HUD_CAMERA.md:126,143` |
| light: none in effects | `.effc` vocabulary is **94 member paths** (`EmitterTemplates`, `Emitters`, `Instantiators.RenderInfos.RenderBlockTypeHash`, `Timelines`, `Modifiers` …) and **not one is a light** | `FX_VOCAB.json` (all `.effc\t` keys) |
| light: the real carrier | `VehicleDynamicLights`: **3,217 entries / 223 vehicles**, each with `range`, `angle`, `multiplier`, `diffuse.RGB`, `behavior`, `preset_id`, `falloff_start`, `min_luminosity`, `near_cap`, `volume_intensity`, `volumetric_mode`, `light_type`, `blinking`, `cast_shadows` | `LIGHT_SYSTEM.md:22-55` |
| light behaviours | **9** values: `None` 1177, `HeadLight` 1027, `TailLight` 301, `LeftSignal` 253, `RightSignal` 253, `Reverse` 191, `SirenLightOn` 9, `SirenLightOffOnFast` 3, `SirenLightOnOffFast` 3 — **no boost/nitro value** | `LIGHT_SYSTEM.md:57-68` |

---

## 2. The sequence, in time order

`t=0` is the boost press. BmAK's burst is 2.0 s and its cooldown 12.0 s, so the whole show is one
2-second window; there is no ramp and no re-trigger inside it.

| t | element | what BmAK does, with its numbers | confidence |
|---|---|---|---|
| 0.000 | **camera kick** | the 35-unit `BatmobileBoostCameraShake` is added; `AdvancedOptions` interval 0.1 s, limits 2,000/10,000 | decoded (value), derived (that it lands on the press frame) |
| 0.000 | **sound: start** | `Play_Batmobile_RocketTails` begins — the 3-row Play event carries the transient | decoded (event exists, has a `Stop_`), derived (transient inside Play) |
| 0.000 | **flame mesh** | `batmobileExhaust_burst` emitter 4888 switches on `Engine.MESH_Batmobile_Jet_V01` at `[32,0,0]` (0.32 m aft), scale 0.9 | decoded |
| 0.000 | **light** | the `light` render module of the same systems fires with the burst | decoded (module present), UNKNOWN (its brightness/cone/range — the dump carries none; the light census found 0 brightness entries) |
| 0.000 | **particles: core burst** | emitters 4894–4903 at `[15,0,0]`, sizes 30–50, rates 4–15/s, lifetimes 0.05–1.5 s | decoded |
| 0.000 | **particles: side jets** | `SideExhaust_Boost` emitters 4906/4907/4909 (sizes 15–80, velocity 200–500) and 4905/4908 (`Firefly_JetMesh`, scale 1.2–1.3, velocity 50–100) at `[−5,0,16]` per side | decoded |
| 0.000 → 2.000 | **sound: loop** | the Play event loops while the boost is held; no separate loop event exists | decoded (no loop event in the group), derived (loop-from-Play is the Wwise convention; **the loop bit is not pinned** — `AUDIO_FEATURES.md` §Gaps) |
| 0.000 → 2.000 | **flame + particles: sustain** | the mesh and sprite emitters keep spawning; the 0.05–0.1 s lifetime emitters flicker, the 0.7–1.5 s ones carry the plume | decoded (lifetimes), derived (which emitter is the flicker layer) |
| 0.000 → 2.000 | **camera kick: repeat** | shake reapplied every 0.1 s (20 applications over the burst) | derived from the 0.1 s interval and 2.0 s duration |
| 0.000 → 2.000 | **camera FOV** | 85° → 95°, interpolated to 108 km/h | decoded |
| 2.000 | **sound: stop** | `Stop_Batmobile_RocketTails` | decoded |
| 2.000 | **flame mesh off** | the mesh emitter stops; the 0.5–1.5 s tail decays | decoded (lifetimes), derived (which emitter is the tail) |
| 2.000 | **shutoff puff** | `SideExhaust_Burst` 3 emitters, sizes 40–60, rates 13/10, lifetimes 0.1–0.4 s | derived — this system is the only 3-object one in the group and reads as a burst, but **UNKNOWN** whether it fires on press or on release |
| 2.000 → 14.000 | **nothing** | 12 s cooldown; no event, no effect, no shake | decoded (`BoostCooldown` 12.0 s) |

**Time-order caveat.** No BmAK file gives per-emitter start times: `PARTICLES.md` carries sizes,
velocities, lifetimes and rates, and the graph carries the components, but nothing in the grab
states that 4888 begins before 4894. The 0.000 column above is the press frame for all of them;
what orders them *within* the frame is the lifetime (a 0.05 s emitter is the ignition spark, a
0.7 s one the plume). Labelled derived, not decoded.

---

## 3. Matching each element to a JC3 file

| element | JC3 carrier | status | the gap, stated as a system |
|---|---|---|---|
| **flame mesh** | **new private** `bm_afterburner_core.effc` (§4.1); nearest shipped family is the 9 `*nitrous*.effc` | **missing** | The flame file JC3 does use (`car_cycle_base_dual_nitrous.effc`) is built from the two `exhaust_upgrade_nitrous*` emitters, and no JC3 nitro file is recorded as carrying a **mesh** emitter — the 9-file family is known by name only, and the object-hash → `.effc` edge is itself UNKNOWN (`USAGES.md:575-577`). So the cone needs a private `.effc` with a mesh render block, not a re-point of the shipped one. |
| **particles (core)** | `effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc`, emitters `exhaust_upgrade_nitrous2` / `exhaust_upgrade_nitrous`, usage `EngineNitro`, on socket `Afterburner` | **carried** | Already applied as T-FX3. Only the density/velocity numbers differ: BmAK rates 4–15/s and sizes 30–50 have no JC3 counterpart member in the donor effect that is decoded. |
| **particles (side jets)** | **new private** `bm_afterburner_side.effc`, one `SAttachedEffect` per side | **missing** | JC3 has no side-jet effect on any nitro file. The two side emitters exist only inside BmAK's own `SideExhaust_Boost` system at `[−5,0,16]`; there is no vehicle-space socket for them in the grab, so the placement is UNKNOWN (§6 U-2). |
| **light** | additive glow sprite inside `bm_afterburner_core.effc`; **dynamic light** would be a `VehicleDynamicLights` entry | **partial** | A private `.effc` *cannot* carry a light: the 94-member `.effc` vocabulary has no light member. The real carrier is the `VehicleDynamicLights` module (3,217 entries), but its behaviour state machine offers 9 values and **none is boost/nitro**, so a light entry would be always-on. |
| **sound: start / loop / stop** | the `vehicles` bank event **f74ea43b-a8ac-4548-ad27-b92fd40a516d**, EVTS 249, 3 samples (`_start` 56 / `_loop` 150 / `_stop` 355), reached from the same `EngineNitro` objects that carry the flame | **carried (in JC3), binding to check** | JC3 is actually *better* here than BmAK: BmAK's `RocketTails` has **no samples on disk** (bank `Engine.VEH_Tank_Missiles` is missing, 0 WEMs, status `missing-bank`), while JC3 ships all three segments inside one event. What is unverified is whether the build's `.epe` kept the donor's `Sound` sibling object next to the two `SAttachedEffect`s (§6 U-3). |
| **camera kick** | **new private** `bat_base_shake.ctunec` = a copy of `vehicle_camera_shake.ctunec` (`CameraShakeModifierParams`) plus one `ShakeAnimations[]` entry; reached from `bat_base.ctune` | **missing (blocked row exists)** | `T6_HUD_CAMERA.md:136` (T-CAM11) is `blocked` with "no numeric bridge". There is a bridge now: BmAK's 35 units → **0.35 m** inside the decoded `TranslationMaxAmplitude` domain `0 … 0.5`; BmAK's 2.0 s burst → `Control.Duration` 2.0 inside `1.0 … 10.0` with `Looping` 1. What stays UNKNOWN is the frequency in Hz (BmAK gives an interval, not a frequency). |
| **FOV 85 → 95** | `bat_base.ctune` FOV row (T-CAM2) | carried (queued) | Not this card's row; named only so the kick is not confused with the FOV change. |

---

## 4. The missing pieces, as new private definitions

Proposed file: **`Working/Effects/bm_afterburner_fx.json`** (does not exist yet; this section is the
spec). Format follows `Working/Effects/bm_fx_edits.json` (`schema`, `card`, `base`, `inputs`,
`socket`, `edits[]` with `class`/`name`/`member`/`row`/`old`/`new`/`why`) plus a `definitions[]`
block for files JC3 does not ship. `.effc` is writable: 95/95 files carry-round-trip and an
`EmitterTemplates[0].MaxParticles` edit re-reads correctly (`Working/Effects/EFFC_WRITER.md`).

Every field below is tagged: `[B]` from a BmAK number above, `[J]` from a decoded JC3 domain,
`[U]` UNKNOWN with its probe in §6.

### 4.1 `bm_afterburner_core.effc` — flame cone mesh + glow + core particles

```
row            FX-A1     feature "afterburner core"      attachment socket:Afterburner
trigger        EngineNitro (4197885156, already on the two donor SAttachedEffects)
emitters
  1 mesh   mesh       = Engine.MESH_Batmobile_Jet_V01  converted BmAK asset   [B: PARTICLES.md:1253]
           max_particles = 8                         [U-1]  [J domain 1..500]
           scale        = 0.9                         [B: start_size 0.9]
           offset       = (0, 0, +0.32) m             [B: start_location [32,0,0] cm]
           lifetime     = 0.75 s                      [B: 0.75]
  2 sprite additive glow, colour amber→white-over-0.4 s [B: light module present, colour UNKNOWN U-1]
           emission     = 15/s                         [B: rate 15]
           start_size   = 0.30 m                       [B: 30 cm]
           end_size     = 0.50 m                       [B: 50 cm]
           lifetime     = 0.05 .. 0.10 s               [B: the flicker layer]
  3 sprite    smoke/heat shimmer, emission 4/s, size 0.15 m, lifetime 0.5 .. 1.5 s  [B: 4/s, 0.5-1.5]
  4 sprite    ignition spark, 10/s, size 0.15 m, lifetime 0.05 .. 0.10 s           [B: 10/s, 0.05-0.1]
timelines      one float timeline per emitter, EndX 1.0  [J: Timelines[].EndX 0..1]
```

### 4.2 `bm_afterburner_side.effc` — the two side jets

```
row            FX-A2     attachment 2 × SAttachedEffect (bm_afterburner_side_l / _r)
                          position UNKNOWN [U-2]; candidate = mirror about the chassis centreline
emitters
  1 mesh   mesh = Engine.Firefly_JetMesh, scale 1.2 .. 1.3, velocity 50 .. 100, lifetime 0.30 s  [B: 4905/4908]
  2 sprite size 15 .. 25 cm, velocity 200 .. 400, lifetime 0.20 .. 0.30 s                          [B: 4906/4907]
  3 sprite size 50 .. 80 cm, velocity 300 .. 500, lifetime 0.15 .. 0.35 s                          [B: 4909]
```

### 4.3 `bm_afterburner_burst.effc` — the shut-off puff

```
row            FX-A3     attachment socket:Afterburner, second SAttachedEffect gated on release
emitters       3 sprites, sizes 40 .. 60 cm, lifetimes 0.1-0.3 / 0.1-0.3 / 0.2-0.4, rates 13 and 10
                          [B: PARTICLES.md:145, SideExhaust_Burst]
```
Which frame this fires on — press or release — is §6 U-4; the definition is written so the release
is the default because BmAK's press frame is already covered by `SideExhaust_Boost`.

### 4.4 `bat_base_shake.ctunec` — the boost camera kick

```
row            T-CAM11 (unblocks the blocked row; no number is substituted, one is derived)
base file      editor/entities/jc_cameras/vehicle_cameras/shake/vehicle_camera_shake.ctunec
root           CameraShakeModifierParams                              [J]
ShakeAnimations[0]
  Control.Duration            = 2.0 s      [B: BoostDuration 2.0]     inside [J] 1.0 .. 10.0
  Control.Looping             = 1          [B: boost lasts the full 2.0 s]
  Control.AutoStart           = 0          message-driven, see below  [J] 0/1 both shipped
  Control.EaseInTime          = 0.10 s     [B: 0.1 s interval]        inside [J] 0 .. 0.5
  Control.EaseOutTime         = 0.20 s     [derived: 10% of the 2.0 s burst]  inside [J] 0.1 .. 0.5
  Control.StartMessage        = "BoostStart"     [U-5 the message vocabulary]
  Control.StopMessage         = "BoostStop"      [U-5]
  TranslationMaxAmplitude     = 0.35 m     [B: 35 units → 0.35 m]     inside [J] 0 .. 0.5 (70% of max)
  TranslationMaxFrequency     = 20 Hz      [U-6; BmAK gives 0.1 s, not Hz]  inside [J] 5 .. 30
  RotationMaxAmplitude        = 1.0        [derived: 0.35 / 0.35 × a mid-domain rotation value] inside [J] 0.4 .. 10
  RotationMaxFrequency        = 20 Hz      [U-6]                       inside [J] 9 .. 40
```
The unit step is the only conversion: BmAK's length tables in this grab are centimetres
(`CAMERA.md:169` heads its sit-offset and boom columns "cm"; `WEAPONS.md:695` reads the same struct
as `[-20.0, 0.0, 0.0]`), so 35 → 0.35 m. If 35 is not centimetres the amplitude rescales by the
same factor and must stay under 0.5.

### 4.5 Audio: no private definition (and why)

The gap list does **not** include a new sound definition, because JC3's event already carries the
whole shape BmAK wants:

| BmAK segment | event | JC3 equivalent inside f74ea43b | sample index |
|---|---|---|---|
| start | `Play_Batmobile_RocketTails` transient | `jc3_veh_land_premium_nitro_start` | 56 |
| loop | the same Play row looping (no loop event exists) | `jc3_veh_land_premium_nitro_loop` | 150 |
| stop | `Stop_Batmobile_RocketTails` | `jc3_veh_land_premium_nitro_stop` | 355 |

All three live in `vehicles` EVTS 249 (195 B), reached from the same `EngineNitro` objects that
carry the flame. A private event cannot be authored here: BmAK's own RocketTails samples are **not
on disk** (bank `Engine.VEH_Tank_Missiles` missing, 0 WEMs), and no FEV-writing tool exists in
`Tools/scripts/`. So the audio element is closed by **reuse**, and the only open question is whether
the build kept the `Sound` object (§6 U-3).

---

## 5. Build recipe, in order

1. **Confirm the flame object is still on the nozzle.** `Working/Effects/bm_fx_edits.json` already
   places both `EngineNitro` emitters at `Afterburner`; re-run the tool that owns `.epe` FX and read
   its census (`python Tools/scripts/bm_fx.py --check`). It is currently **red on six `SWeaponPoint`
   objects** (a weapon lane wrote `weapon_anchor` after B-08) — that failure is not this card's and
   must be fixed by the weapon lane before any FX rebuild (§6 U-7).
2. **Compile the three new `.effc`** from `bm_afterburner_fx.json` `definitions[]` with
   `Tools/scripts/effc_writer.py` (the writer's proven edit path). Do not touch
   `car_cycle_base_dual_nitrous.effc`; the core cone is an **additional** object so the T-FX3 result
   is not lost if the private file fails.
3. **Attach**: `SAttachedEffect` rows on the `Afterburner` socket — `bm_afterburner_core` (usage
   `EngineNitro`), `bm_afterburner_burst` (usage `EngineNitro`), and two side effects at the §6 U-2
   positions once known.
4. **Camera**: copy `vehicle_camera_shake.ctunec` → `bat_base_shake.ctunec`, write the
   `ShakeAnimations[0]` block of §4.4, and point `bat_base.ctune`'s modifier at it. `bat_base.ctune`
   already exists as the rename of `car_base.ctune` (T-CAM rows); this adds the modifier, it does not
   change the eight camera values.
5. **Audio**: nothing to author. Check §6 U-3; if the `Sound` object is absent, add a `Sound`
   object carrying GUID f74ea43b next to the core effect (an existing event, not a new one).
6. **Light**: do not add a `VehicleDynamicLights` entry yet. §6 U-8 is the gate; the additive sprite
   in `bm_afterburner_core.effc` is the in-effects substitute and needs no new mechanism.
7. **Only then** run the pilot card in game (separately authorised): one boost, watch the nozzle.

---

## 6. UNKNOWNs, each with the file or probe that settles it

| id | UNKNOWN | what settles it | one-sentence pilot check + pass band |
|---|---|---|---|
| U-1 | BmAK light module's brightness/cone/range, and the mesh emitter's particle cap | re-read `batmobileExhaust_burst.ParticleModuleRequired`'s light and mesh sub-blocks in the BmAK package (the grab's `PARTICLES.json` has the required module but not these fields) | Boost at night: a warm glow is visible on the rear bodywork and the jet cone reads as solid geometry, not a flat sprite — pass if the glow is visible at 5 m and the cone is not visibly billboarded. |
| U-2 | the two side-jet positions in vehicle space | `Research/BatmobileGrab/SOCKETS_JC3.json` role list for a side-exhaust socket, or a FOOTAGE frame of the boost from the side | Side view of a boost: both jets leave just behind the front wheels and converge aft — pass if neither plume intersects the bodywork for the full 2 s. |
| U-3 | whether the build `.epe` kept the donor `Sound` object (GUID f74ea43b) beside the two `SAttachedEffect`s | `bm_fx.py` object census on `Builds/bm-008/.../*_civilian_01.epe` | Boost: the jet roar starts, holds for the full 2 s and stops with the flame — pass if no tail is heard more than 0.3 s after the flame dies. |
| U-4 | whether `SideExhaust_Burst` fires on press or release | BmAK component `ab`/`ABW` activation order, or a frame-by-frame look at the 30–38 s boost clip in `FOOTAGE.md:47` | Boost: a puff appears at the start (press) or the end (release), not both — record which; pass if it is exactly one puff per boost. |
| U-5 | the message strings the camera modifier listens for | the camera code's message table, or a probe that logs received messages | Boost: the kick happens once per press and stops on release — pass if 20 presses give 20 kicks and 0 kicks during the 12 s cooldown. |
| U-6 | the shake frequency in Hz | no BmAK field carries frequency; it needs a measurement of the 0.1 s interval as a wave (or the camera code) | Boost: the shake reads as a fast buzz, not a slow sway — pass if it is visibly faster than the wheelspin shake. |
| U-7 | whether `bm_fx.py --check`'s six `SWeaponPoint` diffs block an FX rebuild | the weapon lane re-deriving its plan, or scoping the compare to FX objects | — (tooling gate, not a game check) |
| U-8 | whether any light can be gated on the nitro state | `USAGES.json`'s 155-value vocabulary for a light-ish usage, or `LIGHTS_FORENSICS.md`'s behaviour list (9 values, none boost) | Boost at night: a dynamic light (not just the sprite) lights the road behind the car — pass if the road patch brightens within 0.1 s of the flame appearing. |
| U-9 | whether `EngineNitro` actually fires on this vehicle's boost | `USAGES.md:566` says which control fires a nitro block is code, not data; needs a probe | Boost: flame appears — pass if it appears on the first press and on every one of ten presses. |

---

## 7. What was verified, and the limits of it

**Checks run for this report (read-only):** the render/lifetime/emitter censuses above were re-read
out of `PARTICLES.md`, `AUDIO_FEATURES.md`, `FX_TABLE.jsonl`, `FX_VOCAB.json`, `CLASS_DEFAULTS.json`,
`USAGES.md`, `CAMERA.md`, `LIGHT_SYSTEM.md`, `T6_HUD_CAMERA.md` and `Working/Effects/*` in this
session; the counts quoted (13/17, 5, 3, 302, 590/585, 3,217/223, 9 behaviours, 9 nitrous files,
202/172) are from those files, not from memory.

**No test, build or launch was run.** Nothing here was observed in game; `bm_fx.py --check` was not
re-run (its known weapon-object failure is recorded, not reproduced). Every "carried" row above is a
static file statement, and the sequence's intra-frame ordering is a derivation from lifetimes.

**Deliberate omissions.** Heat haze is not re-derived here — `tmp/freebuff/reports/fx9-heat-haze-source.md`
already owns that question and this card adds nothing to it. The FOV row (T-CAM2) is named but not
changed. `T6_HUD_CAMERA.md`'s T-CAM11 stays blocked in the ledger; §4.4 is a proposal that would
unblock it, and no ledger cell was edited.

## 8. Files and revert

| file | change | revert |
|---|---|---|
| `tmp/freebuff/reports/afterburner-effects-audio-plan.md` | **new** (this report) | delete it |

Read-only: `PARTICLES.md`, `AUDIO_FEATURES.md`, `CAMERA.md`, `CLASS_DEFAULTS.json`, `FOOTAGE.md`,
`FX_TABLE.jsonl`, `FX_VOCAB.json`, `USAGES.md`, `LIGHT_SYSTEM.md`, `T6_HUD_CAMERA.md`,
`Working/Effects/bm_fx_edits.json`, `Working/Effects/EFFC_WRITER.md`,
`tmp/freebuff/reports/fx3-afterburner-apply.md`, `tmp/freebuff/reports/boost-rows-proposal.md`.
Proposed-but-not-written: `Working/Effects/bm_afterburner_fx.json`, `bat_base_shake.ctunec`, the
three `bm_afterburner_*.effc`. No module, `.epe`, game file, ledger row, backlog or tracker was
changed; nothing was installed or launched.
