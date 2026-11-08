# Hits and scrapes — what BmAK throws off on contact, and the JC3 collision tables that can carry it

Scope: the spawn side of a collision for `RVehicleBatmobile` (spark systems, debris,
sound, screen shake, dent) with the speed numbers that *are* decoded, then the JC3
collision effect tables, what they are keyed by, and exactly which entries we copy,
which we add, and which numbers no file gives us.

Per `AGENTS.md` this is a **plan only**: no game file is modified by this document.

---

## 1. Evidence base

| source | what it gave |
|---|---|
| `Research/BatmobileGrab/CLASS_DEFAULTS.md` | the 13 impact / scrape / spark / rumble members of `RVehicleBatmobileBase`, with archetype + class-default offsets and values |
| `Research/BatmobileGrab/DAMAGE_RULES.md` §3.3 | `CalculateAndStoreImpactDamage` (script, 1,532 B) field list; the shipped / Joker / base-CDO impact speed columns |
| `Research/BatmobileGrab/SPEEDOMETER.md` | the only unit statement in the grab: `3500` Unreal units (cm/s) = **126 km/h** |
| `Research/BatmobileGrab/PARTICLES.md` | 206 systems / 1,433 emitters — the census. `Impact_Body_UPGR` 39 emitters, `Impact_Full_UPGR` 42, `Impact_Head_UPGR` 33, `Batmobile_HeavyCannon_Impact_Px` 11 |
| `Research/BatmobileGrab/AUDIO_FEATURES.md` | `Engine.BML_Impacts` = 4 events, all `Play_Batmobile_Destroyed` |
| `Research/JC3Grab/USAGES.md` | `SDynamicAttachedEffectTable` / `SAttachedEffectTable` usage names and how many entities carry each |
| `Research/JC3Grab/DECODE_DEPTH.md` | the `effects/jc_vehicles/collision/` package list, sizes, FULL decode status |
| `Research/JC3Grab/FX_TABLE.jsonl` | per-package rows/arrays/types for those same packages |
| `Research/JC3Grab/PALETTE_HASH.md` | the per-package palette key of every collision `.effc` |
| `Research/JC3Grab/DAMAGE_MODEL.md`, `ARMOR_STEP.md`, `DAMAGE_MECHANISMS.md` | searched for a speed-keyed collision effect table — **0 hits** (§5.3) |

---

## 2. What BmAK actually spawns — the members, verbatim

Every row below is a decoded class default of `RVehicleBatmobileBase`
(`CLASS_DEFAULTS.md`; offsets relative to the archetype serialisation unless the
"layer" column says CDO).

| member | type | value | offset | layer |
|---|---|---|---:|---|
| `ImpactSparks` | ObjectProperty | `Engine.Batmobile_Impact_02` (ParticleSystem) | `0x0144` / 4708 | archetype |
| `SpinningSpikesImpactFX` | ObjectProperty | `Particles.SpikeAsset_Impact_P` (ParticleSystem) | `0x014c` / 4812 | archetype |
| `SpinningSpikesImpactSound` | ObjectProperty | `Ww_OBJ_Orphan_Spike.Play_OBJ_Orphan_Riddler_Spike_Hit_Batmobile_CODE` (AkEvent) | `0x0154` / 4820 | archetype |
| `JumpLandSparksEffectL` | ObjectProperty | `Impacts.Batmobile_Landing_Sparks_L` | `0x007c` / 4716 | CDO |
| `JumpLandSparksEffectR` | ObjectProperty | `Impacts.Batmobile_Landing_Sparks_R` | `0x0084` / 4724 | CDO |
| `WallScrapeSparksSystemR` | ComponentProperty | `Default__RVehicleBatmobile.WallScrape1` (ParticleSystemComponent) | `0x020c` / 5868 | archetype |
| `WallScrapeSparksSystemL` | ComponentProperty | `Default__RVehicleBatmobile.WallScrape0` (ParticleSystemComponent) | `0x0214` / 5876 | archetype |
| `WallScrapeSparksSystemR/L` | ComponentProperty | `Default__RVehicleBatmobileBase.WallScrape1` / `WallScrape0` | `0x013c`,`0x0144` / 5868, 5876 | CDO |
| `ImpactSparksSizeName` | NameProperty | **`'Size'`** | `0x0168` / 5904 | CDO |
| `CollisionFFWaveForm` | ObjectProperty | `Default__RVehicleBatmobile.CollisionForceFeedbackWaveform` | `0x019c` / 5596 | archetype |
| `ExplosiveImpactScreenShake` | StructProperty | 18 nested props: `0x00 0.0`, `0x04 0.5`, `0x08 [0,5,5]`, `0x14 [35,35,35]`, `0x20 [0,0,…]` | `0x03a6` / 6596 | CDO |

So the contact response is **four visual systems, one rumble, one shake**:

1. **sparks** — `Engine.Batmobile_Impact_02` for any impact,
2. **wall scrape** — two *components* (`WallScrape0` left, `WallScrape1` right), i.e.
   the scrape is a continuously-emitting pair of particles, not a one-shot,
3. **landing sparks** — `Impacts.Batmobile_Landing_Sparks_L/R` (jump/land contact),
4. **spike strike** — a separate particle + AkEvent for the spinning spikes,
5. **force feedback** — `CollisionForceFeedbackWaveform`, the pad rumble,
6. **screen shake** — `ExplosiveImpactScreenShake`.

`ImpactSparksSizeName = 'Size'` is the interesting one: it is a *name*, so the spark
system has a float parameter called `Size` that something writes from outside. The
spark burst is therefore speed/severity-scalable **by design** — the parameter is
named in the class default. What writes it, and with what curve, is §6.

### 2.1 What the census can and cannot tell us about those systems

`PARTICLES.md` contains **no** `Batmobile_Impact_02`, **no** `Batmobile_Landing_Sparks_L/R`
and **no** `WallScrape0/1` block (0 matches for each). The census covers the
`Batmobile_*` systems in the packages it scanned; these four live in
`Engine` / `Impacts` and are outside it. Their emitter counts, lifetimes and sizes are
therefore **UNKNOWN** — not zero, absent.

Systems that *are* in the census and belong to the impact family:

| system | emitters | notable numbers |
|---|---:|---|
| `Impact_Body_UPGR` | **39** | sizes 100/150, 40–60, 20–80, `Engine.EMP_Sphere` at 0.4–0.6, `Engine.fx_sun` at 2.0 |
| `Impact_Full_UPGR` | **42** | same family, larger |
| `Impact_Head_UPGR` | **33** | same family |
| `Batmobile_HeavyCannon_Impact_Px` | **11** (4645–4655) | sizes 5–1000, velocities to 800 cm/s, two sprite beams `APEX_IOFX_SPRITE_0056` length **252**, `APEX_IOFX_SPRITE_0006` length **246** |

Those are the *projectile* impacts, not the car's chassis impacts, but the
`Impact_*_UPGR` naming ("upgrade", i.e. the progressive-damage flavour of an impact)
is the closest thing in the census to a severity-graded impact system.

---

## 3. Debris and dent — what the files say

**Debris: no member.** `RVehicleBatmobileBase` names no debris/break-off mesh, no
`*Debris*` object property, and `PARTICLES.md` has no `Impact_*Debris*` system. The
only fragments in the grab belong to the weapon shells
(`HeavyCannon_Shell`, `ChainGunShells0`).

**Dent: no member, no asset.** A case-insensitive search for `dent` / `deform` /
`scrape` across `Research/BatmobileGrab/*.md` returns **no** dent or deformation
member, mesh or morph target. The vehicle's damage *visual* state in the data is the
destruction path, not progressive panel deformation:

- the destruction sound: `Engine.BML_Impacts` — 4 objects, 4 events, all
  `Play_Batmobile_Destroyed` (`AUDIO_FEATURES.md`);
- `ExplosiveImpactScreenShake` (§2) — the shake for the big hit;
- the four impact particle members above.

So **"dent" is UNKNOWN in BmAK** — the grab does not show one. Do not build one for
fidelity; if the operator wants a dent, it is an addition, not a port.

**Sound beyond destruction.** The only impact-family AkEvent decoded on the class is
the spike hit. Scrape and body-impact audio are not members of
`RVehicleBatmobileBase`, so they are either fired by the Ak component's own
`Impact`/material switch or by native code — **UNKNOWN** from this grab, and the bank
census only lists `Play_Batmobile_Destroyed` inside `Engine.BML_Impacts`.

---

## 4. The speed numbers that *are* decoded

### 4.1 Ram damage curve (`CalculateAndStoreImpactDamage`, script 1,532 B)

`DAMAGE_RULES.md` §3.3 — every field the body reads is listed there; the values:

| field | shipped `Batmobile` | Joker `JokersBatmobile` | base CDO |
|---|---:|---:|---:|
| `ImpactMinDamageSpeed` | **20** | **40** | 60 |
| `ImpactMaxDamageSpeed` | **150** | **180** | 200 |
| `ImpactMaxDamage` | — | — | 100 |
| `ImpactMaxDamagePow` | 0.666 | 0.666 | 0.666000009 |
| `ImpactStrafeMod` | **2.25** | **0.8** | 1.5 |
| `ImpactBoostMod` | **2** | — | 1.5 |
| `ImpactCivilianVehicleMod` | — | — | 1.0 |
| `StafeImpactImpulse` | — | — | 100000 |
| `BattleModeImpactMinDamageSpeed` | **120** | **120** | — |
| `BattleModeImpactMaxDamageSpeed` | **540** | **540** | — |
| `BattleModeImpactMaxDamagePow` | **0.5** | **0.666** | — |

`—` = the archetype carries no tag, so the shipped number is whatever the native CDO
holds: **UNKNOWN from the files**.

### 4.2 The unit — stated honestly

`SPEEDOMETER.md`: the debug readout's `3500` is Unreal units (cm/s) = **126 km/h**,
so 1 km/h = 27.78 cm/s and the vehicle's own speed channel is cm/s.

The two impact fields carry **no unit annotation** anywhere in the grab. Read as cm/s:
`ImpactMinDamageSpeed = 20` is 0.72 km/h and `ImpactMaxDamageSpeed = 150` is 5.4 km/h —
impossible as a ram ramp. Read as km/h: 20 → 150 km/h for the shipped car, 120 → 540
for battle mode, base CDO 60 → 200. That is coherent with a 126 km/h cruising speed
and a tank that out-runs it. **The km/h reading is the only self-consistent one**, but
it is an inference, not a decoded fact — §9 turns it into a 5-minute test.

There is precedent for km/h numbers on this very class family: `CAMERA.md:33` states the
unit rule outright — "FOV is degrees; `*InterpMaxSpeed` is UE3 cm/s (3000 = 30 m/s =
108 km/h)" — and `CAMERA.md:206` then gives `FOVVelocityRange` as `[5, 50]` **km/h**.
So the grab carries both conventions and labels them per member; the `Impact*Speed`
members are the ones with no label. That is why U1 stays open rather than being
resolved here.

The interpolation between the two ends is also **not decoded**: the body reads both
ends, the power and the three multipliers, but not the expression joining them. A
power curve `MaxDamage · ((v − vMin)/(vMax − vMin))^Pow` is the shape the field names
imply; it is a *proposal*.

### 4.3 The ram *assist* — the other half of a hit

`RVehicleBatmobileBase` carries nine `ImpactRoadAssist*` floats (`CLASS_DEFAULTS.md`
rows 49–57). They do not spawn anything; they are how contact deflects the car:

| member | value |
|---|---:|
| `ImpactRoadAssistSceneryDuration` | 0.75 s |
| `ImpactRoadAssistEnemyDuration` | 1.5 s |
| `ImpactRoadAssistFactor` | 40000.0 |
| `ImpactRoadAssistMaxTorque` | 15000.0 |
| `ImpactRoadAssistMaxAngle` | 45.0° |
| `ImpactRoadAssistAngVelocityTime` | 0.25 s |
| `ImpactRoadAssistSteeringFactor` | 30.0 |
| `ImpactRoadAssistLookAheadTime` | 1.0 s |
| `ImpactRoadAssistAngleStrength` | 1500.0 |

Note the asymmetry: scenery deflects for **0.75 s**, an enemy vehicle for **1.5 s** —
double, and one of the few places the grab distinguishes "hit a wall" from "hit a car".

---

## 5. The JC3 side

### 5.1 There is no "speed" axis in the JC3 collision effects

Searched `USAGES.md`, `DAMAGE_MODEL.md`, `DAMAGE_MECHANISMS.md`, `ARMOR_STEP.md` for a
speed or velocity field on a collision effect table: **0 hits**. The `SDynamicAttachedEffectTable`
/ `SAttachedEffectTable` records are name + path records; nothing in them is a speed.

JC3 keys collision effects by **part** and by **surface material**, not by speed.

### 5.2 What the tables are keyed by — the usage census

`SDynamicAttachedEffectTable` (1,212 objects) and `SAttachedEffectTable` (1,678) are
looked up by a **usage name**. The collision-relevant usages, with the number of
entities that carry each (`USAGES.md`):

| usage name | entities | what it is |
|---|---:|---|
| `part_impact` | **168** | per-part impact effect (any body part) |
| `chassis_impact` | **41** (+19 at `1770819418`) | chassis impact, older/short form |
| `chassis_impact_vfx` | **171** | chassis impact, visual |
| `chassis_impact_default_sfx` | **128** | chassis impact, audio |
| `chassis_undercarriage_impact` | **180** | undercarriage hit (kerb, ramp, wreck) |
| `chassis_sliding` | **214** (+19 at `3370375413`) | chassis scrape while sliding |
| `chassis_undercarriage_slide_sfx` | **159** | undercarriage scrape audio |
| `wheel_suspension_car_materials` | **101** | wheel hit, per material |
| `landing_wheel_impact_sound` | **41** | wheel landing audio |
| `wheel_suspension_bottom_out_materials` | **107** | suspension bottom-out, per material |
| `wheel_suspension_bottom_out_sound` | **6** | the same, audio |

`chassis_impact_vfx` (171) and `chassis_impact_default_sfx` (128) sit on the *same*
object hash `2963579072` — that entity carries both the visual and the audio table, so
**a private vehicle that gets one of them gets the pair from the same template**.

### 5.3 The material keying is real, and it is in the filenames

`effects/jc_vehicles/collision/` holds one package per surface, all FULL-decoded
(`DECODE_DEPTH.md` rows 138–154, `PALETTE_HASH.md`, `FX_TABLE.jsonl`):

| package | size | palette key | rows |
|---|---:|---:|---:|
| `chassis_impact_default.effc` | 18,767 | `0x6568` | 2,669 (36 types) |
| `chassis_impact_dirt.effc` | 16,575 | `0x65b8` | — |
| `chassis_impact_sand.effc` | 15,151 | `0x657c` | — |
| `chassis_impact_snow.effc` | 16,303 | `0x6608` | — |
| `chassis_impact_vegetation.effc` | 19,647 | `0xc2e0` | — |
| `chassis_impact_water.effc` | 16,095 | `0x6658` | — |
| `chassis_slide_default.effc` | 11,807 | — | — |
| `chassis_slide_dirt/sand/snow/vegetation.effc` | 10,863 / 9,167 / 10,847 / 11,039 | — | — |
| `break_impact_sm/md/lg.effc` | 14,527 each | — | — |
| `break_electric_sm.effc` | 11,535 | — | — |
| `headlight_break_off_01.effc` / `_on_01.effc` | 9,631 / 13,535 | — | — |

plus a parallel `cargo_chassis_impact_{default,dirt,sand,snow,water}` set, used by
cargo vehicles.

That is a **complete six-material impact family and a four-material slide family that
already exists** — nothing has to be authored for material. What does not exist is a
size/severity axis: `chassis_impact_default` and `break_impact_lg` are different
*events*, not one event at two intensities.

### 5.4 The nearest thing to a debris table

`break_impact_sm` / `_md` / `_lg` are three pre-made break-up bursts at three sizes,
and `headlight_break_off_01` / `_on_01` are the lamp coming loose. These are
"break a part off", triggered by a part's own event, not by impact speed.

---

## 6. What BmAK's bands would have to become

Because JC3 has no speed axis, a speed-banded BmAK port is **our own selection logic**
over existing JC3 effects. The bands are anchored on the only speed numbers the grab
gives (§4.1, km/h reading):

| band | contact speed | damage (`shipped`) | BmAK state | JC3 effect to use |
|---|---|---|---|---|
| 0 — touch | < 20 | none | nothing spawns (no member is gated below min speed — see below) | none / `chassis_slide_*` while in contact |
| 1 — light | 20 – 75 | ramp begins, `Pow` 0.666 | `ImpactSparks` + `CollisionFFWaveForm` | `chassis_impact_default.effc` via `chassis_impact_vfx` |
| 2 — heavy | 75 – 150 | ramp continues | sparks + `ExplosiveImpactScreenShake` at the 0.5 s / 5.0 radius end | `chassis_impact_<material>.effc` + `break_impact_md` |
| 3 — critical | > 150 | clamped at `ImpactMaxDamage` 100 × mods | + `Engine.BML_Impacts` (`Play_Batmobile_Destroyed`) | `break_impact_lg` + `headlight_break_off_01` |
| battle mode | 120 – 540 | `Pow` 0.5, `BattleModeImpactMaxDamage` | the tank's much wider ramp | same effects, wider gate |

**Caveat that must not be smoothed over:** the grab does **not** show the spark or
scrape members being gated by speed. They are unconditional class defaults; the only
speed-gated thing decoded is *damage*. The band cut-points above are therefore a
**proposal** built on the damage thresholds (which are facts) plus the plausible
reading that `ImpactSparksSizeName = 'Size'` scales the burst (which is a field name,
not a curve). Band 0 "nothing spawns" is an assumption, not a reading.

The one thing the data does support: **between 0.75 s and 1.5 s of deflection**, and
**0.25 s** to reach the new angular velocity, are the timings to copy for the
post-hit response in any band.

---

## 7. Entries we copy or add

Attach model, unchanged from the light and exhaust reports: a
`deformable_transform` node on the rear/chassis part, with the effect table on the
part, because no JC3 part in a stock car is named after a BmAK bone.

### 7.1 Copy — no new assets

| copy from | onto | as | why |
|---|---|---|---|
| `effects/jc_vehicles/collision/chassis_impact_default.effc` | chassis part | `chassis_impact_vfx` (band 1) | the stock chassis hit, 171 entities use it |
| `chassis_impact_dirt / sand / snow / vegetation / water` | same part | the same usage, material-switched | the six-surface family already exists; the material switch picks them |
| `chassis_slide_default` (+`_dirt/_sand/_snow/_vegetation`) | chassis part | `chassis_sliding` (band 0, while in contact) | continuous scrape, 214 entities |
| `break_impact_md.effc` | chassis part | band 2 layer | mid-size debris burst, exists |
| `break_impact_lg.effc` | chassis part | band 3 layer | large burst, exists |
| `headlight_break_off_01.effc` | the lamp part from the taillight report | band 3 | lamp comes loose, exists |
| `chassis_undercarriage_impact.effc`-backed table | undercarriage node | `chassis_undercarriage_impact` (180 entities) | kerbs and ramps |
| `landing_wheel_impact_sound` + `wheel_suspension_car_materials` | wheel stations | as named | kerb/landing, per material |

### 7.2 Add — only the band gate

There is no speed axis to copy, so the addition is **one new lookup layer** of our own:
a `SDynamicAttachedEffectTable` per band (`batmobile_impact_light`,
`batmobile_impact_heavy`, `batmobile_impact_critical`), each pointing at the packages
in §7.1, plus a contact handler that reads the closing speed and picks the band.

Two honest limits on that:

- the numeric fields inside an `SDynamicAttachedEffect` record are **not decoded**
  (`DECODE_DEPTH*` gives package-level rows/types only), so a hand-written row is a
  guess until we read a stock one out of a donor entity;
- until §9's experiment, we do not know whether a band table can be attached to a
  part at all, or only to the vehicle root.

### 7.3 Numbers that have no JC3 home

| BmAK value | JC3 equivalent |
|---|---|
| `ImpactMinDamageSpeed` 20 / `ImpactMaxDamageSpeed` 150 | **none** — no speed field in the collision tables |
| `ImpactMaxDamagePow` 0.666, `ImpactStrafeMod` 2.25, `ImpactBoostMod` 2 | **none** — damage lives in `DAMAGE_MODEL`/`ARMOR_STEP`, and neither is speed-keyed |
| `ImpactSparksSizeName` `'Size'` | maps onto whichever particle float the JC3 `.effc` exposes; **name not decoded** (the `.effc` string table is 0 values across 955 files, per the exhaust report) |
| `ImpactRoadAssist*` nine floats | **none** — deflection is physics, not effects |
| `CollisionFFWaveForm` | the pad rumble is engine-side; no JC3 member decoded |
| `ExplosiveImpactScreenShake` (0.0 / 0.5 / [0,5,5] / [35,35,35]) | no JC3 screen-shake table decoded on a vehicle |

---

## 8. The five-minute experiment (before any of §7 is built)

`AGENTS.md`: prefer one experiment over a large speculative change.

1. Pick a donor car entity that carries usage `2963579072`
   (`chassis_impact_vfx` + `chassis_impact_default_sfx`).
2. Clone it to a scratch entity, change only the entity name, load it.
3. Drive it into a wall at two speeds and read the log for the effect spawn and the
   Ak event. This tells us, in one run: whether the table needs the vehicle root or a
   part, and whether the SFX table fires without the VFX table present.
4. Only then write the band table from §7.2.

Expected cost: one entity clone, two collisions, one log read.

---

## 9. UNKNOWNs — stated, not filled in

| # | question | status |
|---|---|---|
| U1 | unit of `ImpactMinDamageSpeed` / `ImpactMaxDamageSpeed` | **UNKNOWN** — no unit annotation on the member; km/h is the only self-consistent reading (cm/s is arithmetically impossible as a ram ramp), and `CAMERA.md` shows both cm/s and km/h members exist side by side on this class family, labelled per member |
| U2 | expression joining the two ends | **UNKNOWN** — power-curve shape proposed from `ImpactMaxDamagePow` |
| U3 | what writes `ImpactSparksSizeName = 'Size'`, and its curve | **UNKNOWN** — the name is decoded, the writer is native |
| U4 | emitters/lifetime/size of `Engine.Batmobile_Impact_02` | **UNKNOWN** — outside the particle census |
| U5 | emitters/lifetime of `WallScrape0/1` and `Impacts.Batmobile_Landing_Sparks_L/R` | **UNKNOWN** — outside the census |
| U6 | does BmAK dent? | **no dent member, no dent asset** — an absence of evidence; treated as "no" |
| U7 | BmAK scrape/body impact audio | **UNKNOWN** — only the spike AkEvent and `Play_Batmobile_Destroyed` are decoded |
| U8 | numeric layout of an `SDynamicAttachedEffect` row | **UNKNOWN** — read one from a donor before hand-writing |
| U9 | do the JC3 collision usages key on part or on root | **UNKNOWN** — §8 tests it |
| U10 | which JC3 .effc emitter is "sparks" vs "dust" | **UNKNOWN** — 0 string values across 955 `.effc` |

---

## 10. Change record

- **Intended change:** none to game data. This document plans the collision-effect
  port only.
- **File written:** `tmp/freebuff/reports/collision-impact-effects-plan.md`.
- **Why this file:** the request names it as the deliverable.
- **Revert:** delete the file. No other file was touched.

---

## 11. Checks run

- every offset/value in §2 quoted from `CLASS_DEFAULTS.md` rows 35–37, 46, 60–61,
  16–17, 26, 40–41, 43, 75, 77–84;
- §4 values re-read from `DAMAGE_RULES.md` §3.3 (shipped / Joker / base-CDO columns);
- §5.2 counts quoted from `USAGES.md` lines 227, 274, 290, 297, 328, 329, 340, 344,
  362 (object hashes kept so a later card can re-open them);
- §5.3 sizes and palette keys quoted from `DECODE_DEPTH.md` 208–224 and
  `PALETTE_HASH.md` 70–94; `rows 2669 / types 36` from the `FX_TABLE.jsonl` record for
  `chassis_impact_default.effc`;
- the "no speed axis" claim is a negative search result (§5.1) — a search that returned
  nothing, reported as such;
- the absence of `Batmobile_Impact_02`, `Batmobile_Landing_Sparks_*`, `WallScrape*` in
  `PARTICLES.md` is likewise a negative result, reported as "outside the census", not
  as "no emitters".
