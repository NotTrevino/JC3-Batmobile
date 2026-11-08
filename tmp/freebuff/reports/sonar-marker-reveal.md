# Sonar: what it draws, what the tread-mark mode needs, and what JC3 can carry

Scope: the marker/reveal half only. Pulse range, period and sound events are settled in
`tmp/freebuff/reports/sonar-and-scan-pulse.md` and are **not** repeated here — this report takes its
verdict as given (base sonar = visible pulse; `CForcePulse` is the only carrier; no reveal class).

Operator fact (2026-11-08): enemies are already marked on the radar without the sonar; sonar is a
mission tool for following tread marks and otherwise only looks and sounds good.

**Answer in one paragraph.** Outside missions BmAK's sonar draws **two particle systems**
(`Particles.Batmobile_Seismic_Sonar` for the scan, `..._Charged` for the blast), **two screen shakes**
and **six sound events** — and nothing on the HUD at all: `HUD.md` mentions "sonar" **0 times** and
`HUD_SPEC.json` has no sonar setter among its 31 `UC_*` entries. It also *declares* a real highlight
mechanism the grab never serialised: `VehicleScannerMaterial` / `ObjectScannerMaterial` /
`MaterialPool` / `MeshPool` / `ScannedMeshes` / `MaxScannedVehicles`, i.e. **material swaps on scanned
vehicles and objects**, plus `ScanPct` / `ScannerSpeed` / `ScanDuration` for the scan's progress and
end. The tread-mark mode hangs off `BasicScanEffect = Engine.Tire_Track_Pulse_P` and
`BasicScanSound = Engine.Play_BML_Sonar_Forensics_Pulse` — both **`missing-object`**, both in the
**Engine** package, so the track data comes from the engine's tyre-track decal system, which is not in
the grab. JC3 has **no counterpart for the highlight** and **no tyre-track decal entity**; its closest
visual is a 0-damage `CForcePulse` (`gen_explosion_5m_nodamage.ftune`, 0 damage / 5 m) and its closest
trail is the wheel dust `.effc` set, which is an effect, not a followable mark.

## 1. What the sonar actually draws — world and screen

Class `RBatmobileSonar`, super `RVehicleWeapon`, size 3084 (`BMSDK_OFFSETS.json`). It declares **48**
properties; **22** are serialised on `Batmobile_Sonar` and are identical in all three packages
(`WEAPONS.md:82`, `:1139-1141`). The other 26 are class defaults the dump never writes — their values
are `UNKNOWN`, their **existence is decoded**.

### 1.1 Serialised (decoded values)

| element | offset | value | what it draws |
|---|---|---|---|
| `ScanParticle` | 0x0A10 | `Particles.Batmobile_Seismic_Sonar` (ParticleSystem 205 B) | the scan pulse VFX |
| `BlastParticle` | 0x0A38 | `Particles.Batmobile_Seismic_Sonar_Charged` (217 B) | the charged blast VFX |
| `ScanSound` | 0x0A18 | `Ww_BML_Sonar.Play_BML_Sonar_Pulse_Search` | pulse sound |
| `BlastSound` | 0x0A40 | `Ww_BML_Sonar.Play_BML_Sonar_Pulse_Full` | blast sound |
| `ChargeStartSound` / `ChargeStopSound` | 0x0A28 / 0x0A30 | `Play_BML_Sonar_Rumble_Lp` / `Stop_…` | looping charge |
| `ScannerOnSound` / `ScannerOffSound` | 0x0A70 / 0x0A78 | `Play_BML_Sonar_Turn_On` / `Turn_Off` | scanner mode toggle |
| `BasicScanEffect` | 0x0A48 | `Engine.Tire_Track_Pulse_P` — **`missing-object`** (ref −648) | tread-mark pulse |
| `BasicScanSound` | 0x0A50 | `Engine.Play_BML_Sonar_Forensics_Pulse` — **`missing-object`** (ref −267) | tread-mark sound |
| `ChargingScreenShake` | 0x0968 | **10000.0**, `[4,4,4]`, `[40,40,40]`, **true** | charge shake |
| `BlastScreenShake` | 0x0B1C | `[0,70,70]`, `[10,10,10]`, `[160,160,160]`, `[15,15,15]` | blast shake |

`objects.jsonl` confirms all 14 tags per package (`Batmobile_Sonar`, refs 4948/4949/5296 etc.); the
two `Engine.*` refs are negative indices in every package, i.e. unresolved in all three.

### 1.2 Declared but never serialised — including the only highlight machinery

| element | offset | type | why it matters |
|---|---|---|---|
| `VehicleScannerMaterial` | 0x0A60 | MaterialInterface | **the highlight**: material swapped onto scanned vehicles |
| `ObjectScannerMaterial` | 0x0A68 | MaterialInterface | highlight for scanned non-vehicle objects |
| `MaterialPool` | 0x0BD8 | MaterialInstanceConstant | pool the scan draws its materials from |
| `MeshPool` | 0x0BE8 | SkeletalMeshComponent | pool for scanned vehicle meshes |
| `ScannedMeshes` | 0x0BFC | `FScannedVehicleMesh` | the per-vehicle scanned-mesh record |
| `MaxScannedVehicles` | 0x0BF8 | int | cap on simultaneously highlighted vehicles |
| `ScanningTank` | 0x0A58 | RVehicleHeavyTank | a dedicated heavy-tank scan path |
| `ScanPct` / `ScannerSpeed` / `ScanDuration` | 0x0BCC / 0x0BD0 / 0x0BD4 | float | progress 0→1, rate, total time — **this is what ends a scan** |
| `VehicleScanRange` / `VehicleScanAngle` | 0x0BC4 / 0x0BC8 | float | scan volume (the only range/angle in the class) |
| `KnockDownThugsRange` / `StunThugsRange` / `AlertVehiclesRange` | 0x0BB8 / 0x0BBC / 0x0BC0 | float | **gameplay radii** — see §4 |
| `bScannerActive`, `bFirstPulse`, `bSonarGadget`, `FireButtonHeld`, `ChargingShot`, `BatmobileMovementStopped` | 0x0A04 | bool (bit-packed) | scanner state, first-pulse flag |
| `CoolDownTime`, `ChargeUpDelay`, `ChargeUpTime`, `ChargeTime`, `ChargeShakeId`, `ScanScreenShake` | 0x095C–0x0964, 0x0A08, 0x0A0C, 0x0A80 | float/int/struct | timing, second shake |

None of these has a value in the dump, so "how big is the highlight radius / how long is a scan" is
`UNKNOWN` — but the **mechanism** is decoded: the sonar highlights by **swapping material and mesh on
scanned actors**, with a percent-driven timer and a vehicle cap. That is more than the earlier report
recorded, which read only the 22 serialised fields.

### 1.3 On screen

| source | finding |
|---|---|
| `Research/BatmobileGrab/HUD.md` | **0 occurrences of "sonar"** (case-insensitive count). No sonar module, clip or setter. |
| `HUD_SPEC.json` `bmak.uc_setters` | 31 setters, **none** sonar- or scan-related (`UC_SetScannerDetail` belongs to detective mode, §1.4) |
| closest existing HUD surface | `HudModuleBespokeLocalRadar`: `MapPulseTimer` + `UC_DoPulse` (a **radar** pulse), `UC_SetLockonValue` (a lock fill) — `HUD.md:219` |
| closest reveal surface | `HudModuleScanner` (scan reticle, deep-scan markers, timeline): `UC_SetScanAnimProportion`, `UC_SetDeepScanLevel`, `UC_FindDeepScanEvidence` — `HUD.md:224` |

So: **the sonar's world half is fully authored (particles, shakes, sounds); its on-screen half is
native and has no movie hook at all.** Any ring, marker or highlight the player sees in BmAK is drawn
by the material-swap path in 1.2 or natively — not by `HUD.md`'s modules.

### 1.4 On-screen pieces that exist for the forensic/tread-mark mode

| element | where | what it is |
|---|---|---|
| `UC_SetForensicTrail` | `HUD.md:220` (`HudModuleAlertsAndSurveillance`) | a forensic **trail** drawn on the alert module — the only "follow a path" HUD verb in the movie |
| `UC_SetForensicTracking(text)` | `HUD.md:176` | forensic tracking readout (text) |
| `RHudModuleForensicBeaconTracking` (`SetLockon`) | `HUD.md:99` | beacon-tracking module; **unshipped** — no carved movie implements its cached names |
| `HudModuleScanner` deep-scan calls | `HUD.md:224` | scan progress/markers, used by detective mode, re-usable as a pattern |

## 2. What the tread-mark mode needs

| question | answer | evidence |
|---|---|---|
| **where does the track data come from?** | **the Engine package, not the Batmobile one.** `BasicScanEffect` points at `Engine.Tire_Track_Pulse_P` and `BasicScanSound` at `Engine.Play_BML_Sonar_Forensics_Pulse`; both resolve as **`missing-object`** in all three packages | `WEAPONS.md` §14 rows 0x0A48/0x0A50; `objects.jsonl` `Batmobile_Sonar` refs −648 / −267 |
| is there a track/mark field anywhere else? | **no.** `RBatmobileSonar` has no track list, no decal pointer, no mark count | full 48-property dump of the class |
| **how is a mark shown?** | as a **particle pulse over existing tyre tracks** (`Tire_Track_Pulse_P`), plus `ScanScreenShake` and the forensic-trail HUD verb — not as a new decal | 0x0A48; `HUD.md:220` |
| **what ends it?** | `ScanPct` (0x0BCC) driven by `ScannerSpeed` (0x0BD0) until `ScanDuration` (0x0BD4) elapses; capped by `MaxScannedVehicles` (0x0BF8). Re-entry is gated by `CoolDownTime` (0x095C) | class properties; values `UNKNOWN` |
| what makes it mission-only? | nothing in the data. There is no mission flag; the mission binding is script-side | 48-property dump |

## 3. The main table: BmAK element → JC3 member → verdict → pilot-card pass band

"Verdict" is `decoded` (value read from a file), `derived` (arithmetic/design on decoded facts) or
`UNKNOWN` (needs a file named in §5).

| BmAK element | value | JC3 member / file to write | verdict | pilot-card sentence, with pass band |
|---|---|---|---|---|
| scan pulse VFX `ScanParticle` | `Particles.Batmobile_Seismic_Sonar`, 205 B | `CForcePulse` on the Batmobile entity + a 0-damage `.ftunec` copied from `gen_explosion_5m_nodamage.ftune` (`FORCEPULSE.md:108`, `:131`); visual via its `id:D3DDD766` → `CMaterialEffectTable` (`:52`); or the imported `.effc` from the BmAK particle | pulse carrier **decoded**, visual hook **decoded as a pointer**, draw contents **UNKNOWN** | "Tap sonar: a ring expands from the car, hurts nothing, and cannot be mistaken for a hit." **Pass band: 0 damage to Rico/NPCs/vehicles at any range (the tune's `PlayerDamage = 0`, `AIDamage = 0`), radius 5 m as shipped by that tune, single pulse under 1 s, no alert raised.** |
| blast pulse `BlastParticle` | `..._Charged`, 217 B | same pulse object, second tune/effect slot | carrier decoded, two-stage switch **UNKNOWN** | "A held charge produces a visibly stronger pulse than a tap." **Pass band: two distinguishable effects, tap first, charged second; neither damages.** |
| six sound events | `Pulse_Search`, `Pulse_Full`, `Rumble_Lp`/`Stop`, `Turn_On`/`Turn_Off` | no JC3 audio member on a pulse; import the `BML_Sonar` bank (355,830 B, 6 ids verified) and fire from the same code | **decoded** (bank/ids), mapping **derived** | "The pulse is audible and the same six cues fire on the same beats as BmAK." **Pass band: search tone on tap, full tone on charge, loop start/stop on hold/release, on/off on mode toggle; 0 missing event ids.** |
| charge / blast screen shake | 10000.0, `[4,4,4]`, `[40,40,40]`, true / `[0,70,70]`, `[10,10,10]`, `[160,160,160]`, `[15,15,15]` | `.ctunec` `CameraShakeModifierParams` (class exists, fields undecoded) | **UNKNOWN** conversion | "The car shakes on charge and harder on blast." **Pass band: two shakes, blast visibly larger; no value conversion claimed.** |
| **highlight** `VehicleScannerMaterial` / `ObjectScannerMaterial` / `MaterialPool` / `MeshPool` / `ScannedMeshes` | materials and pool, values not serialised | **no JC3 member.** Closest: a material swap driven by a graph script; `CMaterialEffectTable` is opaque and not per-target | mechanism **decoded**, values **UNKNOWN**, JC3 carrier **absent** | "Scanned vehicles and objects glow briefly." **Pass band: highlight visible on ≥1 scanned actor inside `VehicleScanRange` (value UNKNOWN → pick a design radius) and cleared when the scan ends; 0 permanent material changes.** |
| scan progress/end `ScanPct` / `ScannerSpeed` / `ScanDuration` | floats, unset in dump | mission-graph timer; no vehicle member | **UNKNOWN** values, timer **derived** | "A scan runs for a fixed time and stops itself." **Pass band: progress 0→1 over `ScanDuration`, then all highlights clear without a second input.** |
| `MaxScannedVehicles` | int, unset | cap in the same script | **UNKNOWN** value | "At most N vehicles highlighted at once." **Pass band: N is a chosen number, never exceeded in a 10-vehicle test.** |
| **tread marks** `BasicScanEffect` / `BasicScanSound` | `Engine.Tire_Track_Pulse_P` / `Engine.Play_BML_Sonar_Forensics_Pulse`, both **missing** | no JC3 tyre-track decal class; closest effect set is `effects/jc_vehicles/wheels/trail/dust_trail_{asphalt,dirt,grass,sand}.effc` (`DECODE_DEPTH.md:256-259`, FULL) | **UNKNOWN** on BmAK's side, carrier **absent** in JC3 | "In a mission, follow the tracks to the source." **Pass band: a spawned trail persists ≥ the mission window and is visible from the driver's seat; PASS only if the trail is a real mark, not dust.** |
| forensic trail HUD | `UC_SetForensicTrail`, `UC_SetForensicTracking(text)` | JC3 has 32 POIs but **0 decoded creators** | HUD verb **decoded** (BmAK), JC3 bridge **UNKNOWN** | "The tracked path is drawn on the HUD." **Pass band: path visible while tracking, gone when the scan ends.** |
| enemy markers | — (already on radar, not sonar) | not this row | **out of scope** | — |

## 4. Where the files agree, disagree, or say nothing

* **Agree with the operator:** the sonar's own serialised payload is a *look* — two particles, two
  shakes, six sounds, no marker, no reveal flag, no radar marker field. `HUD.md` has no sonar hook, so
  a sonar that only "looks and sounds good" is exactly what the data shows.
* **Disagree, or at least not settled:** the class *does* carry three gameplay radii —
  `KnockDownThugsRange` (0x0BB8), `StunThugsRange` (0x0BBC), `AlertVehiclesRange` (0x0BC0) — plus
  `ScanningTank` and a vehicle **scan** that swaps materials. "No gameplay effect" cannot be confirmed
  from these files because none of those values is serialised; if the defaults are non-zero, the sonar
  can knock down or stun thugs. This is a **conflict to keep open**, not a fact to overwrite.
* **Say nothing:** whether the material highlight fires outside missions (`bScannerActive` is the only
  gate and its default is unset), and whether the tread-mark pulse fires only when tyre tracks exist.

## 5. UNKNOWN table — with the file that would fix each

| item | file that would settle it |
|---|---|
| values of `VehicleScanRange`, `VehicleScanAngle`, `ScanDuration`, `ScannerSpeed`, `ScanPct`, `MaxScannedVehicles` | the class-default export `Default__RBatmobileSonar` — **absent from `objects.jsonl`** (only 3 archetypes exist), so a dump that includes it |
| which material `VehicleScannerMaterial` / `ObjectScannerMaterial` actually is | the same class-default export, or `ScannedMeshes` (`FScannedVehicleMesh`) decoded |
| whether `KnockDownThugsRange` / `StunThugsRange` / `AlertVehiclesRange` are non-zero (the operator's "no gameplay effect") | the same class-default export; nothing serialised carries them |
| what `Engine.Tire_Track_Pulse_P` / `Engine.Play_BML_Sonar_Forensics_Pulse` are | the `Engine` package, which is not in the grab — the 6 `missing-object` refs are the record |
| whether `HudModuleScanner` or the forensic trail is ever driven by the sonar | native module bindings (`RHudModuleScanner`, `RHudModuleForensicBeaconTracking`), no script in the 260-script census calls them for a sonar |
| what `CMaterialEffectTable` draws | the 30-byte hash blob is undecoded (`SIGNATURE_DIFF.md:546`) |
| whether JC3 has any persistent tyre-track decal | no class, member or doc names one; the wheel `dust_trail_*.effc` set is a particle effect (`DECODE_DEPTH.md:256-259`), and the decal textures in the corpus are scorch/plate art (`:88-89`) |

## 6. What the build must write, in one list

1. **Pulse:** `CForcePulse` on the Batmobile root, `.ftunec` copied from `gen_explosion_5m_nodamage.ftune` (8 numbers: 0 damage, 5 m). Trigger is script-side — no shipped pulse is button-fired.
2. **Visual:** the two BmAK particle systems are portable assets; attach as an `.effc`, since `CMaterialEffectTable` is opaque.
3. **Audio:** import `BML_Sonar`'s six verified events; fire from the same script.
4. **Highlight (the part JC3 cannot copy):** a graph script that swaps a material on actors inside a chosen radius, tracks them in a list, and restores them — there is no data member for this.
5. **Tread marks:** cannot be built from the grab (effect and sound are `missing-object`); the closest JC3 primitive is a spawned `dust_trail_*` effect following the car, which is a *moving* trail, not a persistent mark.

## 7. Limits

Static reads of `Research/BatmobileGrab/WEAPONS.md` §14, `objects.jsonl` (`RBatmobileSonar`, 3
packages), `BMSDK_OFFSETS.json` (`RBatmobileSonar` 48 properties), `HUD.md`, `HUD_SPEC.json`,
`Research/JC3Grab/FORCEPULSE.md`, `DECODE_DEPTH.md`, and
`tmp/freebuff/reports/sonar-and-scan-pulse.md` (verdict and UNKNOWNs taken as given, not re-derived).
`HUD.md` really does contain zero "sonar" matches; that is a counted absence, not an impression. No
game launched, no install or archive written, no `Research/` file modified. Every class-default value
in §1.2 stays `UNKNOWN`: the dump carries archetype overrides only.
