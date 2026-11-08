# Surface marks: skid marks and tyre tracks

**Question.** BmAK leaves skid marks and tyre tracks, and the sonar mission follows them.
Find how each is made (decal, mesh strip, particle), their length, width and fade time, then the
JC3 tyre-decal and surface-effect members that can leave the same marks, and what to change on the
private tyre set.

**Verdict in one paragraph.** BmAK's ground marks are **particles**, not decals and not authored
strips: every wheel owns a six-slot `WheelSkidMarkSystem` of `ParticleSystem`s plus a matching
`ParticleSystemComponent`, and the Batmobile's four wheels each point at
`Engine.tyreMarks_ribbonTest` — a ribbon (mesh-strip) particle renderer — alongside the smoke
systems (`Batmobile_Burnout`, `Batmobile_Burnout_MUD`, `Batmobile_Mud_Trail`, `Water_Splash`). The
`RParticleModuleTypeDataDecal` class is present in the Batmobile package but is used by exactly one
system, and that system is the **sonar**, not the wheels. JC3's equivalent is a different shape
entirely: `VehicleCommon.tire_effects.*` only holds the **gates** (23 members, all fleet-invariant),
while the marks themselves are `SAttachedEffectTable` objects named `vehicle_dust_trail` (145
vehicles) pointing at the per-surface `effects/jc_vehicles/wheels/trail/dust_trail_<surface>.effc`
family and the per-wheel `effects/jc_vehicles/wheels/rear_<surface>.effc` family. The numeric
length/width/fade of the markings are **UNKNOWN on both sides** — on BmAK because the ribbon system
lives in the `Engine` package, outside the four Batmobile packages the project grabbed, and on JC3
because no project decoder reads a `.effc` emitter's geometry. What *is* known, and is enough to
build, is every gate, every carrier path, and the module that has to be privatised first.

---

## 0. Method and evidence standard

Per `AGENTS.md`: no JC3-specific claim below comes from pretrained knowledge. Every row cites a
local file and line. Where the file set does not contain a number, the cell says **UNKNOWN** with
the reason, and no plausible-looking value is substituted.

Two premise checks that the evidence contradicts, stated up front so the report is not read as
confirming them:

| # | premise as asked | what the files show |
|---|---|---|
| P-1 | "BmAK leaves skid marks **and** tyre tracks" as two things | One mechanism produces both: the ribbon particle `Engine.tyreMarks_ribbonTest` (a continuous strip) plus the smoke family. There is **no separate track mesh, decal sheet or track actor** in the grab. Evidence: `Research/BatmobileGrab/PARTICLES_FEATURES.md:249-253` (external refs `Batmobile_Burnout`, `Tire_Track_Pulse_P`, `Water_Splash`, `tyreMarks_ribbonTest`, all sourced from `objects.jsonl (SVehicleWheel)`), and `MECHANICS.md:594-609` (the four wheels' 12–13 `ParticleSystem` refs, each list containing `Engine.tyreMarks_ribbonTest`). |
| P-2 | "the sonar mission follows them" | The sonar **is** wired to a tyre-track particle: `RBatmobileSonar` carries `Engine.Tire_Track_Pulse_P` at property offset **2632** (`{offset: 2632, ref: "Engine.Tire_Track_Pulse_P", ref_class: "ParticleSystem"}`), and the `Batmobile_Seismic_Sonar_Charged` system carries the package's only decal emitter. What the mission logic *does* with the mark (whether it raycasts a decal, samples the PS, or just reads a saved track) is **UNKNOWN** — no graph or mission file for it is decoded in this repo. Evidence: `Research/BatmobileGrab/objects.jsonl:5210` (the `RBatmobileSonar` object dump, refs + tags). |

---

## 1. BmAK: how the marks are made

### 1.1 The carrier is per wheel, six slots deep

| member | type | offset | count | evidence |
|---|---|---|---|---|
| `SVehicleWheel.WheelSkidMarkSystem` | `InlineArray{ObjectProperty}` of `ParticleSystem` | **236** | **6** | `Working/vendor/BmSDK/SVehicleWheel.g.cs:398-400` (`new(6, Ptr + 236, 8, this)`); slots `WheelSkidMarkSystem_0.._5` at 236…276 (`:403-445`) |
| `SVehicleWheel.WheelSkidMarkComp` | `InlineArray{ComponentProperty}` of `ParticleSystemComponent` | **396** | **6** | `Working/vendor/BmSDK/SVehicleWheel.g.cs:578-580` |
| `SVehicle.SquealThreshold` | `FloatProperty` | 1860 | Batmobile CDO = **0.2** | `Research/BatmobileGrab/CLASS_DEFAULTS.md:164` (SVehicle default 0.5 at `:437`), `MECHANICS_NAMES.md:29` (`0x744`, 0.2) |
| `SVehicle.SquealLatThreshold` | `FloatProperty` | 1864 | Batmobile CDO = **0.2** | `CLASS_DEFAULTS.md:165`, `MECHANICS_NAMES.md:30` (`0x748`, 0.2) |
| `SVehicle.TyreSmokeSkidThreshold` | `FloatProperty` | 1668 | **UNKNOWN** (not in the decoded CDO delta table) | declared `SVehicle.g.cs:1676-1678`; the CDO table `CLASS_DEFAULTS.md:500-504` lists only `bCanFlip`, `bIsBatmobile`, `ChassisName`, `DefaultTyreUpdates`, `RoadObstacleType`, `RoadObstacleAvoidTypes` |
| `SVehicle.TyreSmokeWheelSpinThreshold` | `FloatProperty` | 1660 | **UNKNOWN** (same reason) | `SVehicle.g.cs:1667-1669` |
| `SVehicle.DefaultTyreUpdates` | `FloatProperty` | 2064 | Batmobile CDO = **16.5** | `CLASS_DEFAULTS.md:349` and `:502`; declared `SVehicle.g.cs:1709-1711` |
| `SVehicle.HideSkidMarks()` | native function | — | — | `SVehicle.g.cs:722-726` — the only "clear the marks" entry point in the class |

Two independent offset tables (`CLASS_DEFAULTS.md`, `OFFSETS.md:378-379`, `:520-521`) agree on the
slot kinds: `WheelSkidMarkSystem` is an `ObjectNCRProperty` in the raw slot table and an
`InlineArray{ObjectProperty}` of six in the SDK dump, i.e. the six PS references are stored
consecutively at 236 and each wheel supplies its own.

### 1.2 Which systems the Batmobile's wheels actually reference

`Research/BatmobileGrab/MECHANICS.md:594-609` — every wheel object, in all four Batmobile packages:

| package | wheel | PS refs | the refs named in the cell |
|---|---|---|---|
| `Playable_BatmobileFunhouse_SF` | `WheelFL` / `WheelFR` | 12 | `Engine.Batmobile_Burnout`, `Engine.Water_Splash`, `Engine.tyreMarks_ribbonTest`, `Impacts.Batmobile_Wheels_Wood_Collision`, `Mud.Batmobile_Mud_Trail`, `Particles.Batmobile_Burnout_MUD` |
| `Playable_BatmobileFunhouse_SF` | `WheelRL` / `WheelRR` | 13 | same set |
| `Playable_BatmobileMK2_SF`, `Playable_Batmobile_SF` | all four | 12 / 12 / 13 / 13 | same set |
| `Playable_BatmobileJoker_SF` | `WheelFL` | 4 | `Engine.Batmobile_Burnout`, `Mud.Batmobile_Mud_Trail`, `Particles.Batmobile_FearGas_Burnout`, `Particles.Batmobile_FearGas_KickUp` — **no `tyreMarks_ribbonTest` on the Joker car** |

That last row is the useful negative: the Joker variant is the same `SVehicleWheel` class with the
ribbon entry absent, so the mark is a per-wheel *reference*, not engine logic tied to the vehicle
type.

### 1.3 Decal, mesh strip, or particle? — all three words apply, to different objects

| renderer | where it is used | evidence |
|---|---|---|
| **Ribbon (mesh strip)** | `Engine.tyreMarks_ribbonTest` — the ground-mark strip on WheelFL/FR/RL/RR | `MECHANICS.md:594-605`; `PARTICLES_FEATURES.md:253` names it in the `tyre-surface` group and says it is *external* to the 206 grabbed systems |
| **Particle sprites / GPU sprites** | burnout and mud smoke on the same wheels (`Batmobile_Burnout_MUD` 6 sprite emitters, `RParticleModuleTypeDataGPU` on its LODs; `Batmobile_Burnout_Water` 4 sprites; `Batmobile_Pollen_KickUP` 4) | `PARTICLES_FEATURES.md:217-224`; `objects.jsonl:1086-1088` (`RParticleModuleTypeDataGPU` refs) |
| **Decal type-data** | exactly **3** objects in the grab, all named `RParticleModuleTypeDataDecal`, all outered to `Particles.Batmobile_Seismic_Sonar_Charged` | `ASSETS.md:188` (census 3), `:341` (class list), `objects.jsonl:5239` (the object itself), `:1136`/`:10076` (the LOD that references it) |

The decal object's full serialised payload (`objects.jsonl:5239`) is:

- `ref` → **`Engine.CITY_Decals_Scarecrow1`** (`Material`, offset 96);
- `InitialRotation` struct (offset 104, 169 B) = a 14-float lookup table (`Op` 2, `LookupTableNumElements` 2, `LookupTableChunkSize` 6, values `0,0,0,0, 1,0,0,0, 0,0,1,0, 0,0`), i.e. the decal's default orientation basis;
- two empty per-instance-random override structs (offsets 168, 204);
- `LODValidity` = 1.

**There is no `DecalWidth`, `DecalHeight`, `DecalFadeTime` or lifetime field on the object.** Size
and life are therefore not properties of the decal type-data in this build — they come from the
emitter's own particle modules (`ParticleModuleSize`, `ParticleModuleRequired.Lifetime`). Any spec
that writes "decal width = N" on the BmAK side would be inventing a member; the honest statement is
that the decal's footprint is the particle size, and the particle size is in the emitter.

### 1.4 Length, width and fade — what is measured, what is not

| quantity | value | status / evidence |
|---|---|---|
| Ribbon **width** | **UNKNOWN** | `tyreMarks_ribbonTest` is an `Engine.` package object; the grab covers four Batmobile packages only, and `PARTICLES_FEATURES.md:257` says external refs "carry no lifetime/spawn/size numbers" and that closing it needs `grab_particles.py` extended to `Engine`. No `DecalWidth` exists on the decal type-data (§1.3). |
| Ribbon **fade time** | **UNKNOWN**, same reason | idem — the ribbon's material fade is inside the engine PS |
| Ribbon **segment spacing** | **UNKNOWN** — `DefaultTyreUpdates` 16.5 is decoded but its unit is not | `CLASS_DEFAULTS.md:349`. 16.5 as Hz would put segments 1.8 m apart at 30 m/s, which contradicts a continuous strip; 16.5 as an update *interval divisor* is equally plausible. Do not use either number as a length without an in-game measurement. |
| Smoke **particle lifetime** (the visible part of the mark for ~1–2 s) | **0.1 – 2.0 s** for the `tyre-surface` group | `PARTICLES_FEATURES.md:53` (`tyre-surface | 16 | 6 | 90 | 12 | 0.1..2 | 0..500 | -`), per-system rows at `:217-224` |
| Smoke **spawn rate** | 0 – 500 /s (group) | idem; per system e.g. `Batmobile_Burnout_MUD` 15…200, `Batmobile_Burnout_Water` 15…500 |
| Smoke **size** | `[35 0 0] .. [150 0 0]` (MUD), `[1 0 0] .. [150 1 0]` (Water), `[2 0 0] .. [100 20 18]` (Wood) — UE3 units are cm, so **0.35–1.50 m** across the burnout | `PARTICLES_FEATURES.md:217-224`; unit convention stated at `:235-240` ("the cooked lookup table's two stored vectors give per-component bounds") |
| **Mark start gate** (what counts as a skid) | slip **0.2** on both axes (Batmobile), against 0.5 class default | `CLASS_DEFAULTS.md:164-165` vs `:437-438` |
| **Mark length for one decal particle** | `speed × lifetime` — a derived identity, not a stored value | derived from the 0.1–2.0 s lifetime above; at 20 m/s that is 2–40 m of trail per emitted particle, which is why the ribbon (not a sprite) is the ground renderer |

**So the requested triple is: length UNKNOWN (derived only as speed × 0.1–2.0 s for smoke), width
UNKNOWN, fade UNKNOWN — all three inside `Engine.tyreMarks_ribbonTest`, which the grab does not
contain.** The measured, usable numbers are the gate (0.2), the smoke lifetime (0.1–2 s), the smoke
size (0.35–1.5 m) and the tyre radius (0.6826 m) / track (2.416 m) from
`Research/JC3Grab/FLEET.md:8` — those are the scale anchors a JC3 mapping can actually use.

### 1.5 The sonar's two track-aware objects

| object | what it is | value | evidence |
|---|---|---|---|
| `RBatmobileSonar.ScanParticle` @ 0x0A10 | sonar pulse | `Particles.Batmobile_Seismic_Sonar` | `WEAPONS.md:1152`, `OFFSETS.md:323` |
| `RBatmobileSonar.BlastParticle` @ 0x0A38 | charged pulse | `Particles.Batmobile_Seismic_Sonar_Charged` | `WEAPONS.md:1156` |
| *(unnamed, offset 2632)* | **tyre-track probe** | `Engine.Tire_Track_Pulse_P` (index −621, i.e. engine package) | `objects.jsonl:5210` tags: `{"offset": 2632, "ref": "Engine.Tire_Track_Pulse_P", "ref_class": "ParticleSystem", "value": -621}` |
| sonar decal | the only decal emitter in the package | material `Engine.CITY_Decals_Scarecrow1` | `objects.jsonl:5239` |

`Batmobile_Seismic_Sonar_Charged`'s emitter mix is `decal×1, mesh×1, sprite×8`, 10 emitters,
lifetime 1..10 s (`PARTICLES_FEATURES.md:72`) — the decal there is the ground-reaching ring, and it
is *not* a tyre mark. `Engine.Tire_Track_Pulse_P` is the object literally named for tyre tracks and
is referenced only by the sonar. Its own stats are **UNKNOWN** (engine package).

---

## 2. JC3: the tyre decal and surface-effect members

### 2.1 The gates — `VehicleCommon.tire_effects`, 23 members, identical on all 232 vehicles

Values from `Research/JC3Grab/VOCABULARY.md:1420-1440` (fleet p1..p99 all equal) and re-checked
against a live module row in `Working/Translation/LEDGER_AUDIT.json:2294-2308`
(`editor/entities/jc_vehicles/00_shared/modules/vehicle_common.vmodc`).

| member | type | value (all 232) | what it gates |
|---|---|---|---|
| `tire_effects.min_skid_velocity_for_skid_ms` | float | **0.5** m/s | ground speed below which skid effects stay off |
| `tire_effects.min_slip_velocity_for_spin_ms` | float | **1.0** m/s | slip speed that starts a *spin* effect |
| `tire_effects.min_slip_velocity_notyre_eff` / `max_slip_velocity_notyre_eff` | float | **2.0** / **10.0** m/s | slip band in which the no-tyre (rim) effect replaces the tyre one |
| `tire_effects.min_spin_velocity_roll_effect` | float | **20.0** m/s | wheel-spin speed for the rolling effect |
| `tire_effects.min_skid_for_effect_front` / `_rear` | float | **0.01** | fraction-of-peak skid that triggers front / rear |
| `tire_effects.min_spin_for_effect_front` / `_rear` | float | **0.30** / **0.10** | fraction-of-peak spin that triggers front / rear |
| `tire_effects.slip_angle_to_peak_to_skid` | float | **0.80** | slip-angle fraction of the peak at which skid starts |
| `tire_effects.slip_ratio_to_peak_to_spin` | float | **0.50** | slip-ratio fraction at which spin starts |
| `tire_effects.skid_velocity_scale` | float | **0.25** | scales slip velocity into the skid effect |
| `tire_effects.slip_velocity_scale` | float | **0.25** | scales slip velocity into the spin effect |
| `tire_effects.skid_effect_drift_boost` | float | **3.0** | multiplier while drifting |
| `tire_effects.slip_effect_drift_boost` | float | **1.5** | idem, spin side |
| `tire_effects.effect_frame_delay_skid` / `_spin` / `_roll` / `_notyre` | uint8 | **5 / 3 / 3 / 5** | frames to wait before the effect may fire |
| `tire_effects.effect_frame_hold_skid` / `_spin` / `_roll` / `_notyre` | uint8 | **2 / 2 / 2 / 2** | frames the effect is held once fired |

`Research/JC3Grab/TANKTURN.md:68-80` is the corroborating negative: a token scan for
`track|pivot|skid|…` over all 52 module sections returns exactly these nine `tire_effects` names plus
`train_common.train_track_width_scale` — **there is no separate track/decal module member**. This
is why §2.2 matters: the marks are not in the module.

### 2.2 The carrier — `SAttachedEffectTable vehicle_dust_trail`

| fact | value | evidence |
|---|---|---|
| the table's usage value | **2355303491** (name **UNKNOWN** in the vocabulary) | `Research/JC3Grab/USAGES.md:300` — `| 2355303491 | UNKNOWN | UNKNOWN | 290 | 145 | SAttachedEffectTable x290 | vehicle_dust_trail x145, combined_wheel_default_sfx x84, combined_wheel_heavyvehicle_sfx x42, wheel_sounds_combined x19 |` |
| reach | **145 vehicles** carry a `vehicle_dust_trail` table | idem (`SAttachedEffectTable x290`, two per vehicle) |
| the leaves | `effects/jc_vehicles/wheels/trail/dust_trail_{asphalt,dirt,grass,sand,snow,water}.effc` | `DECODE_DEPTH.md:256-261`, sizes 6,559–14,175 B, all **FULL** |
| the per-wheel leaves | `effects/jc_vehicles/wheels/rear_{asphalt,dirt,grass,gravel,sand,snow,water}.effc` (2,382–3,042 rows) + `no_tire/notire_*` (651–1,312 rows) | `DECODE_DEPTH.md:242-255` |
| the ground textures exist | `textures/skidmarks_dif.ddsc` (43,856 B, game0) and `textures/skidmarks_nrm.ddsc`; road-side `textures/roads/standard/asphalt_001_skidmarks_{dif,alpha_mpm}.ddsc` | `Research/JC3Grab/INDEX.jsonl:80785-80786, :80803-80804` |
| the build already ships them | `rear_asphalt…rear_water` (7), `dust_trail_*` (6), `no_tire/notire_*` (6), `wheel_explosion_notiremesh` — all `owner_card: "base (bm-005 lineage)"` | `Builds/bm-RC1/receipt.json:730-824` (first `rear_*` at `:751`, first `dust_trail_*` at `:786`) |
| the civilian decal module is gone; the entity binds the shared one | root content id `decals` 1732285335 → `00_shared/modules/decals/default_decals.vmodc`, "the civilian `..._decals.vmodc` is removed" | `MODLOG.md:9539` |
| the civilian decal module itself | 392 B, decodes **FULL** | `DECODE_DEPTH.md:618` |
| its members | **UNKNOWN / none named**: `VOCABULARY.md` has no `VehicleDecals` section and a search for `VehicleDecals` returns 0 matches, so the 392 B module carries no member the project has named | search result: `Found 0 matches` for `## \`VehicleDecals\`\|decals\.\|VehicleDecals` in `Research/JC3Grab/VOCABULARY.md` |

**The consequence for the build is the single most useful finding in this report:** the trailer rows
`T-FX17`/`T-FX18` say `trigger: "tire_effects (T-EF1)"`, but a `tire_effects` hash appears on **0 of
12,187** `SAttachedEffect`/`SDynamicAttachedEffect` objects across the 295 cached fleet graphs
(`Research/specs/B-08.md`, BL-3, with the measurement `hash_jenkins("tire_effects") = 3510048717 =
0xd13717cd`). In `.epe` space the tyre trail's home is the **`SAttachedEffectTable` named
`vehicle_dust_trail`**, and in module space it is nothing at all. Any plan that tries to hang the
marks off `tire_effects` as an *attachment* will fail its own check.

### 2.3 Length, width and fade on the JC3 side

| quantity | value | status |
|---|---|---|
| trail effect **node geometry** (width, fade, tiling) | **UNKNOWN** | the `.effc` files are decoded FULL at the *container/row* level (`DECODE_DEPTH.md:256-261`), but no project decoder reads an emitter's width/fade: `FX.md`'s `.effc` member table stops at `Emitters[]`, `Modifiers[]`, `NamedParameters[]` paths (`Research/JC3Grab/FX.md:55-58` region), and `EFFC_WRITER.json` contains no `width`/`fade` field (`search: 0 matches for "width"|"fade|width_|fade_|lifetime`) |
| mark **lifetime** | **UNKNOWN** for the same reason | — |
| the closest measured analogue | BmAK's smoke 0.1–2.0 s / 0.35–1.50 m (§1.4) | measurement on the other engine, not a JC3 value |
| **what can be measured cheaply** (5-minute experiment, per `AGENTS.md`) | spawn the Batmobile build, hold a drift on asphalt for 2 s, screenshot top-down against a 1 m reference (the tyre radius is 0.6826 m, `FLEET.md:8`), and read the mark's width in tyre diameters; do the same after 5 s idle for the fade | deferred — no measurement was taken in this session, so the cells stay UNKNOWN |

---

## 3. The numeric mapping (BmAK gate → JC3 member)

The two engines gate the same effect on different normalisations, so the mapping is not a unit
conversion and must not be written as one:

- BmAK gates on **`SquealThreshold` = 0.2 / `SquealLatThreshold` = 0.2** — normalised slip, class
  default 0.5, i.e. the Batmobile starts squealing/smoking at **40 % of the class's slip threshold**.
- JC3 gates on `slip_angle_to_peak_to_skid` = 0.8 (fraction of *peak* slip angle) plus
  `min_skid_for_effect_front/rear` = 0.01, *and* a hard velocity floor
  `min_skid_velocity_for_skid_ms` = 0.5.

### 3.1 The mapping table

| BmAK quantity | value | JC3 member | value to set | basis |
|---|---|---|---|---|
| slip gate, longitudinal | `SquealThreshold` **0.2** (class 0.5 → 0.4×) | `tire_effects.slip_angle_to_peak_to_skid` | **0.32** | same relative move: 0.8 × 0.4. The 0.8 is the fleet value and the only anchor; the 0.4 ratio is BmAK's own CDO-vs-class ratio. Both numbers are cited (§1.1, §2.1) |
| slip gate, lateral | `SquealLatThreshold` **0.2** (class 0.5 → 0.4×) | `tire_effects.slip_ratio_to_peak_to_spin` | **0.20** | 0.5 × 0.4 |
| effect onset fraction, front / rear | *(no BmAK member)* | `min_skid_for_effect_front` / `_rear` | **keep 0.01 / 0.01** | no BmAK field to translate; the fleet value is the only evidence |
| spin onset fraction, front / rear | *(no BmAK member)* | `min_spin_for_effect_front` / `_rear` | **keep 0.30 / 0.10** | idem |
| hard velocity floor | *(no BmAK member)* | `min_skid_velocity_for_skid_ms` | **keep 0.5** | idem — BmAK's floor is inside `tyreMarks_ribbonTest`, which is UNKNOWN |
| drift boost | *(no BmAK member)* | `skid_effect_drift_boost` / `slip_effect_drift_boost` | **keep 3.0 / 1.5** | idem |
| mark scale | *(no BmAK member)* | `skid_velocity_scale` / `slip_velocity_scale` | **keep 0.25 / 0.25** | idem |
| frame delay / hold | *(no BmAK member)* | `effect_frame_delay_*` / `effect_frame_hold_*` | **keep 5/3/3/5, 2/2/2/2** | idem |
| smoke lifetime | 0.1–2.0 s | *(no JC3 member — lives in `dust_trail_*.effc`)* | **UNKNOWN**, edit the `.effc` if needed | §1.4 vs §2.3 |
| smoke size | 0.35–1.50 m | *(no JC3 member — `.effc`)* | **UNKNOWN** | idem |
| mark width / fade | UNKNOWN (ribbon) | *(no JC3 member — `.effc`)* | **UNKNOWN** | idem |

**Only two rows move.** Everything else is `keep`, and that is not laziness: the fleet is
invariant on all 23 members (`VOCABULARY.md:1420-1440`, p1 = p99 on every one), so there is no
class-specific value to bring across, and the BmAK members that would justify a change are either
absent or inside an ungrabbed engine package. The two rows that do move come from the one BmAK
pair that *is* measured (0.2 vs class 0.5).

### 3.2 The mapping's own check

`--check` for any future writer must prove, per row:

1. the old value read from the module equals the table's `from` (`0.8`, `0.5`);
2. the written value re-reads as the table's `to` (`0.32`, `0.20`) — exact float32, so
   `0.31999999284…` and `0.20000000298…`;
3. every other `tire_effects` row is byte-identical (the `--write` must walk the whole struct, not
   just the two rows — the B-04 lesson: "every other ADF row unchanged (full walk)",
   `Working/Camera/CAM_TUNE.json` checks block);
4. the shared module's sha256 stays `b402542d7641d6b7f9a6795a50c19b7882890ac08d89a121f65814db150574ba`
   (`Builds/bm-RC1/receipt.json:355-358`) — i.e. the *shared* file must not change, only the private
   copy (§4).

---

## 4. What we change on the private tyre set

### 4.1 The set, named exactly

| file | state today | evidence |
|---|---|---|
| `editor/entities/jc_vehicles/00_shared/modules/vehicle_common.vmodc` | **shared, one copy for all 232 vehicles**, sha256 `b402542d…574ba`, owner `base (bm-005 lineage)`; it is the module that holds all 23 `tire_effects` rows | `Builds/bm-RC1/receipt.json:355-358`; `LEDGER_AUDIT.json:2294-2308` reads `tire_effects.*` **out of this path** |
| `…/v0300_car_kensington_sportsmuscle/modules/default/…_front_tire.vmodc` | 4,678 B, FULL, lives inside the `.ee` | `DECODE_DEPTH.md:619`; `Research/INVENTORY.md:141` |
| `…/…_rear_tire.vmodc` | 4,678 B, FULL | `DECODE_DEPTH.md:626`; `INVENTORY.md:148` |
| any build-tree copy of a `*tire*.vmodc` | **none** — `glob Builds/**/*tire*` → 0 files | search result |
| `…/modules/decals/default_decals.vmodc` | the decal module the built `.epe` binds (civilian one removed) | `MODLOG.md:9539` |

So "the private tyre set" does not exist yet. Building it means creating **three** private copies
under the entity's own module paths, because the behaviour to tune lives in the *shared* module:

| new private file | copied from | why |
|---|---|---|
| `…/v0300_car_kensington_sportsmuscle/batmobile_vehicle_common.vmodc` | `00_shared/modules/vehicle_common.vmodc` | holds `tire_effects`; the only file whose rows §3 changes |
| `…/…/batmobile_front_tire.vmodc` | `…_front_tire.vmodc` (4,678 B) | per-wheel suspension/tyre tuning, kept with the car so a later wheel-width change has a home |
| `…/…/batmobile_rear_tire.vmodc` | `…_rear_tire.vmodc` (4,678 B) | idem |

This is exactly the B-09 recipe, which is already proven in this repo for the health module:
copy `lave_health_medium.vmodc` → `batmobile_health_medium.vmodc`, edit the **copy**, repoint the
entity, re-pack with `eetoc.py patch --internal`, and let the receipt's `modules_changed` name the
new file (`Research/specs/B-09.md:104-116`, and the shipped receipt line
`batmobile_health_medium.vmodc` at `Builds/bm-RC1/receipt.json:371`).

### 4.2 The edit list on the private copy

| # | member | from | to | source |
|---|---|---|---|---|
| 1 | `tire_effects.slip_angle_to_peak_to_skid` | 0.8 (`0.800000011920929`) | **0.32** | §3.1 |
| 2 | `tire_effects.slip_ratio_to_peak_to_spin` | 0.5 | **0.20** | §3.1 |
| 3–23 | all other `tire_effects.*` | — | **unchanged** | fleet-invariant, §2.1 |

Nothing else in `vehicle_common.vmodc` is touched: the file also carries the whole
`VehicleCommon` surface (doors, fins, hinged/propeller/rotating/spring parts, `car_common.*`,
`boat_common.*`, `rotor_collision.*`) — 23 `tire_effects` rows out of the section, and the walk
check in §3.2 is what proves the rest is untouched.

### 4.3 For the marks themselves: the `.epe` table, not the module

The private tyre set changes **when** the marks fire. **Whether** they exist is the graph side,
already shipped by the base:

| thing | what to do | evidence |
|---|---|---|
| keep the donor table | leave `SEffects` → `SAttachedEffectTable vehicle_dust_trail` (usage 2355303491) alone; the build's receipt already carries all 13 `dust_trail_*` / `rear_*` `.effc` at `owner_card: base (bm-005 lineage)` | `USAGES.md:300`; `Builds/bm-RC1/receipt.json:730-824` |
| **do not** add a `tire_effects` attachment | 0/12,187 attachments carry that hash; T-FX17/T-FX18 have no attachment-space carrier | `Research/specs/B-08.md` BL-3 |
| if the marks are invisible on the rebuilt car | the real cause to check first is the wheel part names the table points at (`part:wheel_f_l` in `Working/Effects/bm_fx_edits.json:187-193`), not `tire_effects` | `bm_fx_edits.json:190` |
| sonar/track-reading equivalent | **omit** — JC3 has no sonar class (`Research/JC3Grab/ENTITIES.md`, 103-class census: the only "track" name is `CMusicTrack`), so `Engine.Tire_Track_Pulse_P` and its use have no JC3 home | `G2X.md:106` (WPN-9 named omission) |

### 4.4 How to revert

| change | revert |
|---|---|
| private module copies | delete the three `batmobile_*tire*/…vehicle_common.vmodc` files and re-pack from the previous `.ee` (B-09's revert, `Research/specs/B-09.md:139`: the shared module is copied once and never edited in place) |
| the two row edits | restore the copy from `00_shared/modules/vehicle_common.vmodc` (sha256 above) and re-run the writer's `--check`, which must then re-derive `0.8`/`0.5` |
| any `.effc` edit (only if a width/fade experiment is done) | the receipt's per-path sha256 is the manifest — `Builds/bm-RC1/receipt.json:751-824` lists the `rear_*` and `dust_trail_*` hashes to compare against |

---

## 5. What is UNKNOWN, and the cheapest test that would settle each

| # | UNKNOWN | why it is unknown | 5-minute test |
|---|---|---|---|
| 1 | `tyreMarks_ribbonTest` width / fade / segment length | engine-package PS, outside the four grabbed packages (`PARTICLES_FEATURES.md:257`) | extend `Tools/scripts/grab_particles.py` to the `Engine` package for the one object, or read the ribbon material's tile size in game |
| 2 | `DefaultTyreUpdates` 16.5 unit | decoded value, undecoded semantics (`CLASS_DEFAULTS.md:349`) | drive 10 m at constant speed and count mark segments |
| 3 | `TyreSmokeSkidThreshold` / `TyreSmokeWheelSpinThreshold` on the Batmobile | not present in the decoded CDO delta table (`CLASS_DEFAULTS.md:500-504`) | re-run the CDO dump filtered to offsets 1660/1668 |
| 4 | JC3 `.effc` trail width / fade | no decoder reads emitter geometry (`EFFC_WRITER.json` has no width/fade field) | top-down screenshot of a 2 s asphalt drift against the 0.6826 m tyre radius |
| 5 | what the sonar **does** with `Tire_Track_Pulse_P` | mission logic is not decoded; the reference itself is proven (`objects.jsonl:5210`, offset 2632) | not a data question — needs the mission's `.gdc`, outside this repo's index |
| 6 | usage name for 2355303491 | the vocabulary stops at "UNKNOWN" (`USAGES.md:300`) though 145 vehicles carry the table | hash-search candidate strings against 2355303491 with `rbmhdr.hash_jenkins` |

## 6. Files this report touched

Only this file. No `.vmodc`, `.effc`, `.epe`, `Builds/` tree or game install was read-modified or
written; the two earlier reports (`tmp/freebuff/reports/health-damage-states-plan.md`,
`tmp/freebuff/reports/cameras-per-mode-plan.md`) are unchanged.
