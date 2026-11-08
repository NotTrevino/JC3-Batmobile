# WPN-8 / T-WP8 — BmAK seismic sonar vs JC3's pulse, POI and reveal systems

Task: BmAK's Batmobile Sonar (`RBatmobileSonar`, `ChargingScreenShake`, the `BML_Sonar` audio bank)
pings and reveals the surroundings. JC3 has `CForcePulse` for the shockwave half only. Search for
anything that reveals or highlights objects through a pulse (chaos-object markers, enemy spotting,
Rico's scanner/binocular effects, vehicle Sensor/Radar members, HUD hooks, post-effects driven by a
pulse), list what each does with members and values, map the BmAK sonar fields onto them, and read
the `BML_Sonar` bank's HIRC events so the audio carrier is named. UNKNOWN stays UNKNOWN.

Operator lead (2026-11-06): in BmAK the sonar's treadmark tracking is mission-dependent; outside a
mission it is just a good-looking pulse, and it is the lowest-priority weapon in the ranking. So the
base behaviour's closest system is a **visible pulse** (`CForcePulse` + an effect + the `BML_Sonar`
sound), and treadmark tracking is a separate, later row.

**Verdict.**

* **The base sonar is a visible pulse, and that is the only half JC3 can carry.** `CForcePulse` is a
  31-member blast object on every vehicle (307 pulses / 232 entities), tuned by an `.ftunec` with
  exactly 8 numbers (`PlayerDamage`, `PlayerDamageRadius`, …) and pointed at a
  `CMaterialEffectTable` on 45 of them. A 0-damage tune already ships
  (`gen_explosion_5m_nodamage.ftune`, **0 damage / 5 m**, 2 pulses), so a "look, don't hurt" pulse
  exists as a data pattern. What does **not** exist is a scan trigger: every one of the 307 pulses is
  an **explosion** blast, and the 23 tunes contain 0 horn/collision/scan entries (`FORCEPULSE.md`
  §4.1).
* **There is no reveal/highlight carrier in JC3's vehicle data.** No sonar class in the 103-class
  census (`T7_WEAPONS.md:83`); the "radar" a vehicle has is a **rotating dish part** (`RadarSlow` ×3,
  `RadarFast` ×3, `radar_rpm_slow` 30 / `radar_rpm_fast` 60 on all 232 entities), not a sensor. The
  HUD has 32 `POI_TYPE_*` constants and one `CreatePoi(type, use_progress_bar, is_minor, label)`
  entry point, but **no decoded ship script creates a scan/reveal POI** and the only POI-shaped
  weapon component (`CAimPOIWeaponComponent`, 11 builds) carries one unnamed number
  (`id:2D0B3C09 = 100`) and a position. Enemy-spotting and chaos-object markers are **`UNKNOWN`** —
  nothing in the corpus names them.
* **The audio carrier is named and complete:** AkBank **`BML_Sonar`**, package **`BmGame`**,
  355,830 B, 7 HIRC event objects, **6 distinct events**, 18 references across the three Batmobile
  packages (`Playable_BatmobileFunhouse_SF`, `Playable_BatmobileMK2_SF`, `Playable_Batmobile_SF`).
  All six ids verify as `fnv1(lower(name))` and are present in `BmGame.BML_Sonar`
  (`AUDIO_BANKS2.md:154-159,169`).
* **The treadmark half is missing on BmAK's own side too.** `RBatmobileSonar.BasicScanEffect` points
  at `Engine.Tire_Track_Pulse_P` and `BasicScanSound` at `Engine.Play_BML_Sonar_Forensics_Pulse`;
  both resolve as **`missing-object`** in the grab (`WEAPONS.md` §14). So the mission-only treadmark
  scan is not reconstructable from the grab: it is referenced, not contained. That matches the
  operator's "mission-dependent, separate later row".
* **Closest system for the base behaviour:** a `CForcePulse` on the Batmobile entity using a
  zero-damage `.ftunec` (copy `gen_explosion_5m_nodamage.ftune`'s 8 numbers), its
  `CMaterialEffectTable` as the visual hook, plus the `BML_Sonar` pulse sound imported as an audio
  asset. The gap is the **trigger and the reveal**: no member fires a pulse on a button press, and no
  member reveals objects. Both are code-level.

---

## 1. BmAK side: `RBatmobileSonar` is 22 fields, identical in all three packages

Evidence: `Research/BatmobileGrab/WEAPONS.md` §14 (lines 1130-1180); `Working/Translation/T7_WEAPONS.md:44,83,288-300`.

3 objects, one name (`Batmobile_Sonar`), 66 field rows over 3 instances, **0 differences across the
three** (`WEAPONS.md:1139-1141`). 33 references, 27 resolved, **6 missing-object**.

| field | offset | type | value |
|---|---|---:|---|
| `ChargingScreenShake` | 0x0968 | struct, 4 props, 50 B | (below) |
| `ChargingScreenShake.offset 0x0004` | 0x0004 | FloatProperty | **10000.0** |
| `ChargingScreenShake.offset 0x0008` | 0x0008 | VectorProperty | **[4.0, 4.0, 4.0]** |
| `ChargingScreenShake.offset 0x0038` | 0x0038 | VectorProperty | **[40.0, 40.0, 40.0]** |
| `ChargingScreenShake.offset 0x0090` | 0x0090 | BoolProperty | **true** |
| `RBatmobileSonar.ScanParticle` | 0x0A10 | ObjectNCRProperty | `Particles.Batmobile_Seismic_Sonar` |
| `RBatmobileSonar.ScanSound` | 0x0A18 | ObjectNCRProperty | `Ww_BML_Sonar.Play_BML_Sonar_Pulse_Search` |
| `RBatmobileSonar.ChargeStartSound` | 0x0A28 | ObjectNCRProperty | `Ww_BML_Sonar.Play_BML_Sonar_Rumble_Lp` |
| `RBatmobileSonar.ChargeStopSound` | 0x0A30 | ObjectNCRProperty | `Ww_BML_Sonar.Stop_BML_Sonar_Rumble_Lp` |
| `RBatmobileSonar.BlastParticle` | 0x0A38 | ObjectNCRProperty | `Particles.Batmobile_Seismic_Sonar_Charged` |
| `RBatmobileSonar.BlastSound` | 0x0A40 | ObjectNCRProperty | `Ww_BML_Sonar.Play_BML_Sonar_Pulse_Full` |
| `RBatmobileSonar.BasicScanEffect` | 0x0A48 | ObjectNCRProperty | `Engine.Tire_Track_Pulse_P` — **missing-object** |
| `RBatmobileSonar.BasicScanSound` | 0x0A50 | ObjectNCRProperty | `Engine.Play_BML_Sonar_Forensics_Pulse` — **missing-object** |
| `RBatmobileSonar.ScannerOnSound` | 0x0A70 | ObjectNCRProperty | `Ww_BML_Sonar.Play_BML_Sonar_Turn_On` |
| `RBatmobileSonar.ScannerOffSound` | 0x0A78 | ObjectNCRProperty | `Ww_BML_Sonar.Play_BML_Sonar_Turn_Off` |
| `BlastScreenShake` | 0x0B1C | struct, 4 props, 66 B | (below) |
| `BlastScreenShake.offset 0x0008` | 0x0008 | VectorProperty | **[0.0, 70.0, 70.0]** |
| `BlastScreenShake.offset 0x0014` | 0x0014 | VectorProperty | **[10.0, 10.0, 10.0]** |
| `BlastScreenShake.offset 0x0038` | 0x0038 | VectorProperty | **[160.0, 160.0, 160.0]** |
| `BlastScreenShake.offset 0x0044` | 0x0044 | VectorProperty | **[15.0, 15.0, 15.0]** |
| `RInventoryGadget.Mesh` | 0x0318 | ObjectNCRProperty | `Batmobile_Sonar.GadgetMesh` |
| `Actor.Tag` | 0x0168 | NameProperty | `"RBatmobileSonar"` |

There is **no radius, range, reveal flag, marker list or scan target** in the class: the sonar owns
particles, sound events, two screen-shake structs and a mesh. "It reveals the surroundings" is
therefore script/native behaviour, not a serialised member — the reveal has to be re-created.

The pulse VFX is real in all three packages: `ParticleSystem` exports `Batmobile_Seismic_Sonar`
(205 B) and `Batmobile_Seismic_Sonar_Charged` (217 B), plus material `Batmobile_Seismic_Sonar`
(518 B) — `objects.jsonl` (Funhouse 5039/5040, MK2 4999/5000, Batmobile 4948/4949; material 367).

### 1a. The `BML_Sonar` bank and its HIRC events

`Research/BatmobileGrab/AUDIO_BANKS.md:31,172,206`; `AUDIO_BANKS2.md:33,154-159,169`.

| fact | value |
|---|---|
| AkBank | `BML_Sonar` |
| package / mount | `BmGame` (found in the Batmobile packages: `Playable_BatmobileFunhouse_SF`, `Playable_BatmobileMK2_SF`, `Playable_Batmobile_SF`) |
| bytes | **355,830** |
| sha1 (payload) | `3151382d4c24eb72` (prefix as recorded) |
| BKHD id | **112** |
| HIRC event objects | **7** |
| distinct events | **6** (18 references = 6 × 3 packages) |

| event | id (HIRC) | `fnv1(lower(name))` | in `BmGame.BML_Sonar` |
|---|---|---:|---|
| `Play_BML_Sonar_Pulse_Full` | `0xFFCC9813` | yes | yes |
| `Play_BML_Sonar_Pulse_Search` | `0x97CBF248` | yes | yes |
| `Play_BML_Sonar_Rumble_Lp` | `0x2A77A8B4` | yes | yes |
| `Play_BML_Sonar_Turn_Off` | `0x265FE0CD` | yes | yes |
| `Play_BML_Sonar_Turn_On` | `0x02EE7381` | yes | yes |
| `Stop_BML_Sonar_Rumble_Lp` | `0x835146BE` | yes | yes |

`Play_BML_Sonar_Forensics_Pulse` — the `BasicScanSound` target — is **not** one of them; it is a
`missing-object` (same for `Engine.Tire_Track_Pulse_P`). The audio carrier for the *base* pulse is
therefore complete (`Pulse_Search` on scan, `Pulse_Full` on blast, `Rumble_Lp`/`Stop` on charge,
`Turn_On`/`Turn_Off` for the scanner), while the *treadmark* sound and effect are absent from the grab.

---

## 2. JC3 side: what exists for pulse, reveal and highlight

### 2.1 `CForcePulse` — the blast object (the only pulse carrier)

`Research/JC3Grab/FORCEPULSE.md`; `ENTITIES.md` has no pulse class line but the object census is in
`FORCEPULSE.md` §2.

| quantity | value |
|---|---|
| `CForcePulse` objects | **307** |
| entities carrying one | **232** |
| chassis | **79** |
| entities with >1 pulse | 41 |
| members | **31**: 5 named (`SettingsFile`, `_object_id`, `name`, `name_hash`, `world`) + 26 Jenkins-hashed `id:*` whose names are in no shipped table |
| tunes | **23** `.ftunec`, each 8 numbers |
| material-effect pointer | `id:D3DDD766` → `CMaterialEffectTable` on **45** pulses |
| `world` | on all 307; all at the entity origin except EMP `(0, 2.0356, 0.6992)`, barrel/cargo pulses, and 10 at `(0.0129, 0.5109, 0)` |
| owner | `id:B5AE7986` on the owner object → 293/307 owned by exactly one object (vehicle root or weapon component); **14 unowned** (recorded as UNKNOWN) |
| trigger | **explosion only** — 22/23 tunes under `jc_explosions/`; 0 horn, 0 collision, 0 scan |

`ForcePulseSettings` members and fleet ranges (all 23 tunes):

| member | min | max |
|---|---:|---:|
| `AIDamage` | 0 | 1000 |
| `AIDamageRadius` | 0 | 50 |
| `AIDamageRadiusMin` | 0 | 1 |
| `AIDamageRadiusPercentageMax` | 0 | 1 |
| `PlayerDamage` | 0 | 3000 |
| `PlayerDamageRadius` | 1.5 | 50 |
| `PlayerDamageRadiusMin` | 0 | 1 |
| `PlayerDamageRadiusPercentageMax` | 0 | 1 |

Copyable precedents: `gen_explosion_5m_nodamage.ftune` = **0 damage / 5 m radius** (2 pulses),
`car_explosion_medium.ftune` = 500 / 5 m, `truck_emp.ftune` = 100 / 25 m with full radius
(`*RadiusPercentageMax` = 1.0). The ranges are the closest thing JC3 has to a "sonar radius": they
are **damage** radii, not a scan radius.

The visual hook is `CMaterialEffectTable`: 72 objects fleet-wide (`ENTITIES.md:64`), pointed at by 45
pulses; it is an **opaque 30-byte hash blob whose contents are not decoded**
(`SIGNATURE_DIFF.md:546`). So a pulse can *name* a material-effect table, but nothing readable says
what that table draws.

### 2.2 HUD / POI — 32 types, one lock-on, no scan

`Research/JC3Grab/JC3_HUD_WEAPONS.md` §5 (lines 106-118).

| fact | value |
|---|---|
| POI constants | **32** `POI_TYPE_*` in `hud.as` |
| API | `CreatePoi(type, use_progress_bar, is_minor, label)`; `hud_code/poi.as` switches on type for the icon |
| lock-on | `POI_TYPE_LOCK_ON_TARGET = 21` → `MCI_icon_and_label.MCI_icon.MCI_lock_on.MCI_reticle`, one 360° turn per 1.5 s, no progress bar |
| incoming warning | `MCI_missile_locked`, flash every 0.5 s; `ShowMissileLocked`/`HideMissileLocked` have **0 call sites** |
| POI created by movie for lock-on | **0** `CreatePoi(POI_TYPE_LOCK_ON_TARGET, …)` calls |
| POI weapon component | `CAimPOIWeaponComponent`, **11 builds**; props are only `id:2D0B3C09 = 100` and a world position |
| other POI types | named constants only; **no decoded script creates a scan/reveal/enemy-marker POI** |

So the HUD can draw arbitrary POIs, but the bridge from a pulse (or any vehicle event) to a POI is
**native** — the same conclusion the lock-on row reached (`JC3_HUD_WEAPONS.md:148`).

### 2.3 Vehicle "sensor/radar" members — a rotating dish, not a scanner

`Research/JC3Grab/MOVING_PARTS.md:62-63,159-160`; `VOCABULARY.md:1380-1381`.

| member | value | what it is |
|---|---|---|
| `all_vehicles_common.radar_rpm_slow` | **30** on all 232 entities | rotation rate of a `RadarSlow` part |
| `all_vehicles_common.radar_rpm_fast` | **60** on all 232 entities | rotation rate of a `RadarFast` part |
| `RadarSlow` / `RadarFast` behaviours | 3 parts each, all on `CBoat` | spinning radar dish geometry |
| rotating-part members | `inverted`, `number_of_water_collision_sensors`, `rotoscope_enabled`, `rotoscope_rpm_per_cycle`, `rpm_variable`, `special_collision_enabled` | part animation, no sensing |

There is **no** vehicle member that detects, tags, highlights or reveals anything. The word "radar"
in JC3 data means a mesh that turns.

### 2.4 Camera shake — a real carrier for the charge/blast shake

`ChargingScreenShake` and `BlastScreenShake` are plain structs with unnamed offsets in BmAK. JC3's
camera side has a decoded class for this: `CameraShakeModifierParams` in the `.ctunec` family
(`FX.md` `.ctunec` root-class list). Its members are **not decoded in the files read here**
(`FX.md` lists only the class name and the generic member paths), so the mapping is *system-level*:
the build can drive a camera shake from a tune, but the BmAK 10000 / [4,4,4] / [40,40,40] / true and
[0,70,70] / [10,10,10] / [160,160,160] / [15,15,15] values cannot be converted into a JC3 shake
tune by any decoded field. `UNKNOWN`.

### 2.5 Reveal systems that do **not** exist in the corpus

`UNKNOWN` / absent, with the search stated so it is not re-run blindly:

| candidate | result |
|---|---|
| chaos-object markers | no decoded member or doc; `chaos` appears only in a vehicle variant name (`…_propaganda_chaoslist`) and reward fields (`REBELDROP.md:117`) |
| enemy spotting / tagging | no decoded member; `CAimPOIWeaponComponent` is the only POI component and it is a lock-on shape |
| Rico scanner / binocular effect | no `.effc`, class or member named scanner/binocular in `FX_TABLE`/`ENTITIES`/`VOCABULARY` |
| post-effect driven by a pulse | only the opaque `CMaterialEffectTable` pointer (`id:D3DDD766`, 45 pulses); contents undecoded |
| bloom / screen-space highlight | no decoded renderer setting (see `tmp/freebuff/reports/lens-flare-carriers.md` §2.5) |

---

## 3. Mapping every BmAK sonar field onto the nearest JC3 carrier

| BmAK field (value) | nearest JC3 carrier | what it can carry | gap the build fills (STAGES.md) |
|---|---|---|---|
| `ScanParticle` → `Particles.Batmobile_Seismic_Sonar` (ParticleSystem 205 B) | `CForcePulse.id:D3DDD766` → `CMaterialEffectTable` (45 pulses) or a standalone `.effc` attached to the entity | a visual at the pulse's `world` | the table is opaque; the builder must supply the effect (an `.effc` is a portable asset, not a pulse member) |
| `BlastParticle` → `Batmobile_Seismic_Sonar_Charged` (217 B) | same | a second, stronger visual | same; the two-stage look (scan vs charged blast) has no JC3 switch |
| `ScanSound` → `Play_BML_Sonar_Pulse_Search` | none in JC3 (no sonar bank/event) | the `BML_Sonar` event can be imported as audio and fired by the same code that fires the pulse | no JC3 audio member for a pulse; audio wiring is code/entity-side |
| `BlastSound` → `Play_BML_Sonar_Pulse_Full` | same | the blast sound | same |
| `ChargeStartSound` / `ChargeStopSound` → `Play_BML_Sonar_Rumble_Lp` / `Stop_…` | none | looping charge audio | no loop/stop member on `CForcePulse`; must be scripted |
| `ScannerOnSound` / `ScannerOffSound` → `Turn_On` / `Turn_Off` | none | mode toggle audio | no scanner mode in JC3; the toggle itself is new |
| `BasicScanSound` → `Engine.Play_BML_Sonar_Forensics_Pulse` (**missing**) | **none** | — | missing on BmAK's side; treat as a later row |
| `BasicScanEffect` → `Engine.Tire_Track_Pulse_P` (**missing**) | **none** | — | missing on BmAK's side; treadmark reveal is not reconstructable |
| `ChargingScreenShake` 0x0004 **10000.0**, 0x0008 **[4,4,4]**, 0x0038 **[40,40,40]**, 0x0090 **true** | `.ctunec` `CameraShakeModifierParams` (class exists; members not decoded) | a camera shake at charge | cannot convert values; the class's fields are undecoded → `UNKNOWN` |
| `BlastScreenShake` 0x0008 **[0,70,70]**, 0x0014 **[10,10,10]**, 0x0038 **[160,160,160]**, 0x0044 **[15,15,15]** | same | a blast shake | same |
| `RInventoryGadget.Mesh` → `Batmobile_Sonar.GadgetMesh` | none (JC3 has no gadget mesh slot on a car) | — | the sonar is a Batmobile gadget, not a JC3 weapon; the mesh is portable but has no slot |
| `Actor.Tag` = `"RBatmobileSonar"` | — | identity | — |
| *implicit* reveal | **none** — no vehicle member, no scan POI, no marker class | — | the reveal is native on both sides; the build must script it or drop it |
| *implicit* radius | `PlayerDamageRadius` 1.5–50 m in the 23 `.ftunec` tunes | a radius number, but for damage | choose a radius as a design value, not a decode |

---

## 4. The base behaviour the build can actually compose

Per the operator lead, the base sonar is "just a good-looking pulse". That composes from three
portable pieces:

1. **A pulse object.** Copy the `CForcePulse` shape (31 members) onto the Batmobile entity, with a
   `.ftunec` copied from `gen_explosion_5m_nodamage.ftune` (**0 / 5**, 8 numbers) so the pulse pushes
   and does not damage. This is the closest exact carrier: the object, the tune layout and the
   `world` transform are all decoded. Trigger is **not** — an explosion fires every shipped pulse,
   and 0 of 23 tunes is a scan.
2. **A visual.** Either the pulse's `id:D3DDD766` → `CMaterialEffectTable` (opaque) or a standalone
   `.effc` attached to the vehicle (the `Batmobile_Seismic_Sonar` particle systems, 205/217 B, are
   portable assets). A ring/marker highlight has **no** JC3 carrier: the 32 POI types exist, but no
   decoded script creates one from a vehicle event.
3. **The sound.** `BML_Sonar` (`BmGame`, 355,830 B, 6 events) supplies `Pulse_Search`,
   `Pulse_Full`, `Rumble_Lp`/`Stop`, `Turn_On`/`Turn_Off` with verified ids. This is an **audio
   asset import**, not a JC3 data member — the bank is named, so the carrier is no longer unknown.

What the build must add (STAGES.md BUILD): a **trigger** (a vehicle action that fires the pulse), a
**reveal/highlight renderer** (script or shader; nothing in JC3 data), a **radius choice** (copying a
0-damage tune's 5 m is the only precedent), and a **scanner mode** (on/off, charge loop) if the
two-stage look is kept. The mission-specific treadmark tracking is a **separate later row**: its
BmAK effect and sound are `missing-object` in the grab, and JC3 has no tread/track reveal at all.

The 6 t car is irrelevant to this weapon (no force on the car, no mass term in any pulse tune), so
WLD-7's mass work does not block it.

---

## 5. UNKNOWNs (named, not filled)

- What the sonar's reveal actually does in BmAK — no serialised member; script/native.
- `ChargingScreenShake`'s and `BlastScreenShake`'s unnamed offsets' meanings; `CameraShakeModifierParams`
  member list in JC3 (class exists, fields undecoded).
- What a `CMaterialEffectTable` draws (opaque 30-byte hash blob, 72 objects).
- The names of the 26 hashed `CForcePulse` members (no dictionary hit).
- The firing moment of any pulse (owner pointer proves the carrier, not the trigger).
- Whether any native helicopter/vehicle scan exists — no file names one.
- `Engine.Tire_Track_Pulse_P` and `Engine.Play_BML_Sonar_Forensics_Pulse` — referenced, **not in the
  grab** (`missing-object`).
- Whether the 7th HIRC event object in `BML_Sonar` is a duplicate of one of the 6 names or a
  different object (the bank records 7 event objects, 6 distinct names).

## Evidence index

- `Research/BatmobileGrab/WEAPONS.md:1130-1180` — `RBatmobileSonar`, 3 objects, 22 fields, 66 rows,
  0 differences; every offset/value above; 27 resolved / 6 missing refs.
- `Research/BatmobileGrab/objects.jsonl` — `Batmobile_Seismic_Sonar` ParticleSystem 205 B (Funhouse
  5039, MK2 4999, Batmobile 4948), `_Charged` 217 B (5040/5000/4949), material 367.
- `Research/BatmobileGrab/AUDIO_BANKS.md:31,172,206`; `AUDIO_BANKS2.md:33,154-159,169` —
  `BmGame.BML_Sonar`, 355,830 B, BKHD id 112, 7 HIRC events, 6 verified event ids.
- `Research/BatmobileGrab/AUDIO_FEATURES.md:42,60-69,733-735` — sonar feature: 18 events / 6 distinct,
  the six names.
- `Research/JC3Grab/FORCEPULSE.md` §1 (31 members), §2 (307/232/79), §3 (23 tunes, 8 numbers,
  ranges), §4 (explosion-only trigger, owners), §6 (limits) — `CForcePulse` is the pulse carrier.
- `Research/JC3Grab/ENTITIES.md:64` — `CMaterialEffectTable` 72.
- `Research/JC3Grab/SIGNATURE_DIFF.md:546` — `CMaterialEffectTable` is an opaque 30-byte hash blob.
- `Research/JC3Grab/JC3_HUD_WEAPONS.md:106-118,148` — 32 POI types, lock-on 21, 0 POI creation calls,
  `CAimPOIWeaponComponent` props.
- `Research/JC3Grab/MOVING_PARTS.md:62-63,159-160`; `VOCABULARY.md:1380-1381` — radar dishes,
  rpm 30/60; rotating-part members.
- `Research/JC3Grab/FX.md` `.ctunec` class list — `CameraShakeModifierParams` exists; fields not listed.
- `Working/Translation/T7_WEAPONS.md:44,83,288-300` — T-WP8 row, "no sonar class in the 103-class
  census; CForcePulse is the shockwave half only".
- `GRAB_BACKLOG.md:173` — WPN-8 card (scan + shockwave, `CForcePulse` / named omission).
