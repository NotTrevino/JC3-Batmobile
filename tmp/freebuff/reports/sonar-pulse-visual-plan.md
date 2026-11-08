# Sonar pulse — BmAK's ring measured against JC3's nearest expanding blast

**Question:** the pulse ring's speed, maximum radius, thickness and fade from the grab, with its
sound; then the nearest JC3 expanding-ring or shockwave effect and the parameters that equal BmAK's.

**Verdict.** BmAK's sonar ring is a **7-emitter particle system** whose only motion value is an axial
**2500 cm/s (25 m/s)** velocity, over emitter lifetimes of **1 / 1.5 / 1.5 / 1–3 s** — so the ring
reaches **25 m at 1 s, 37.5 m at 1.5 s and 75 m at 3 s** if the velocity is the expansion rate, which
is the reading the data supports but does not label. Its drawn thickness starts at **0.2 × 0.2 × 0.1**
on the `Blast_Radius_Cylinder` mesh (sprites add **2–50 cm**), and its **fade is not decoded**: the
three sonar materials have **no opacity, emissive or distortion parameter wired at all**
(`Opacity→—`, `Distortion→—`), so the only envelope in the files is the emitter lifetime. Its sound is
**`Play_BML_Sonar_Pulse_Full` / `_Search`** from the `Engine.BML_Sonar` bank, plus a rumble loop and
turn-on/off. On the JC3 side **no effect file is named for a ring, shockwave, wave or pulse**
(0 of 930 decoded `.effc` paths contain any of those words), and the nearest logic carrier —
`CForcePulse` + `ForcePulseSettings` — has **8 numeric members, all damage/radius**, with **no
expansion-speed or lifetime member at all**. So the honest port is: a damage-free pulse tuned to
BmAK's radius, plus a **new** effect for the ring itself, because JC3 ships no ring effect to copy.

Labels: **decoded** = read at the cited field; **derived** = arithmetic over decoded inputs with the
assumption stated; **UNKNOWN** = searched and absent, with the settler named.

---

## 1. What carries the sonar on the BmAK side (decoded)

| layer | object | evidence |
|---|---|---|
| gadget class | `RBatmobileSonar`, object **`Batmobile_Sonar`**, 1 per package (Batmobile / MK2 / Funhouse; 3 total) | `ASSETS.md:185, 332`; `MECHANICS.md:1465, 1489, 1507` |
| its 10 members | `ScanParticle`, `ScanSound`, `ChargeStartSound`, `ChargeStopSound`, `BlastParticle`, `BlastSound`, `BasicScanEffect`, `BasicScanSound`, `ScannerOnSound`, `ScannerOffSound` | `WEAPONS.json` (all 10 per instance, values differ only by object index) |
| **no numeric member** | there is **no radius, speed, thickness or duration field on `RBatmobileSonar`** — the ring is entirely in the particle system | same |
| scan system | `Particles.Batmobile_Seismic_Sonar` | `MECHANICS.md:1465`; `WEAPONS.md` (`RBatmobileSonar.ScanParticle`) |
| blast system | `Particles.Batmobile_Seismic_Sonar_Charged` | `WEAPONS.json` (`BlastParticle`) |
| mesh effect | `BasicScanEffect` (an object property, **not** a numeric) | `WEAPONS.json` |

Per-package wiring from `MECHANICS.md` (the `ScreenShake` and particle/event columns):

| package | object | class | shake structs | particle / event |
|---|---|---|---:|---|
| Funhouse | `Batmobile_Sonar` | `RBatmobileSonar` | 2 | `Particles.Batmobile_Seismic_Sonar`; `Ww_BML_Sonar.Play_BML_Sonar…` |
| MK2 | `Batmobile_Sonar` | `RBatmobileSonar` | 2 | same |
| Batmobile | `Batmobile_Sonar` | `RBatmobileSonar` | 2 | same |

The two shake structs are `ChargingScreenShake` and `BlastScreenShake` — the charge and the released
pulse shake the camera; neither carries a ring parameter.

---

## 2. The ring, emitter by emitter

`Batmobile_Seismic_Sonar`: **7 emitters**, kinds **`mesh, sprite`**, key material
`Materials.SeismicScan_Distortion` (`PARTICLES.md:123, 333`; `FX9_HAZE.md:98`).

| emitter | start_size (cm) | start_velocity (cm/s) | start_location (cm) | mesh / note |
|---|---|---|---|---|
| **4738** (ring) | **0.2, 0.2, 0.1** | — | — | **`Meshes.Blast_Radius_Cylinder`**, `beam: {length: True}` |
| 4734 | 400, 0, 0 | — | — | the only size on this emitter |
| **4739** (shell) | 400, 0, 0 | **0, 0, −2500** | **0, 0, 500** | the expansion value |
| 4736 | 2 … **50** | 0, 0, **200 … 900** | — | sprite drift |
| 4735 | 2 … **50** | 0, 0, **100 … 700** | — | sprite drift |
| 4740 | 2 … 50 | — | — | sprite |
| 4737 | 200, 0, 0 | — | 0, 0, 100 | — |

(the same seven appear as 4698/4694/4699/4696/4695/4700/4697 in the MK2 copy — same values, different
object ids; `PARTICLES.md:2118-2160`).

**Lifetimes and spawn** (the system row, `PARTICLES.md:123`):
`1, 1.5, 1.5, 1–3 …` seconds, spawn **10, 10**. So the longest-lived emitter runs **3 s**, the ring
emitter's own envelope is in the **1–3 s** band.

**Charged variant** (`Batmobile_Seismic_Sonar_Charged`): **10 emitters**, lifetimes `10, 1, 1.5, 1–4 …`,
kinds **`decal, mesh, sprite`**, and one emitter is a **10–12 m decal**
(`start_size` **1000–1200**, `Engine.CITY_Decals_Scarecrow1`). Its shell emitter repeats the
**−2500 cm/s** figure (4750 / 4710), and its sprites grow to 80–100 cm instead of 50. So the charged
pulse is the same ring **plus a ground decal** and a longer (4 s) tail.

---

## 3. The four requested numbers

| quantity | value | class | how it is obtained |
|---|---:|---|---|
| **ring speed** | **2500 cm/s = 25 m/s** | **derived** (velocity decoded; that it is the *ring radius* rate is the reading) | the system's only axial velocity is `[0, 0, −2500]` on emitters 4739 / 4750; sprites drift at 1–9 m/s |
| **maximum radius** | **25 m @1 s, 37.5 m @1.5 s, 75 m @3 s** | **derived** | 25 m/s × lifetime; the 3 s emitter is the top of the band |
| **thickness** | **0.2 × 0.2 × 0.1 m** at the ring mesh, sprites **0.02–0.5 m** | **decoded** (sizes) | `start_size` on 4738 and 4736/4735 |
| **fade** | **UNKNOWN curve**; envelope **1–3 s** | **UNKNOWN** | `Batmobile_Seismic_Sonar`, `SeismicScan_Distortion` and `SeismicSonar_Smoke` all decode **EmissiveColor→—, Opacity→—, Distortion→—** (`MATERIALS.md:32, 36, 40`): no parameter is wired, so no fade value exists to read |
| **system lifetime** | **1 / 1.5 / 1.5 / 1–3 s** | decoded | `PARTICLES.md:123` |
| **charge variant** | **1–4 s** tail, **10–12 m** decal, 10 emitters | decoded | `PARTICLES.md:124, 802-837` |

**Why "derived" and not "decoded" for speed and radius.** The grab records the emitter's
`start_velocity` and `start_location`; it does **not** record which module scales the ring mesh over
life (there is no size-over-life or velocity-scale row for emitter 4738 — its block holds only
`start_size`, the mesh and the beam flag). Two readings fit the data:

1. **expansion**: the velocity drives the radius, so 25 m/s and 25–75 m — the reading used above,
   and the one consistent with the emitter being a **beam-length** mesh (`beam: {length: True}` on a
   `Blast_Radius_Cylinder`);
2. **a travelling shell**: the velocity pushes a 4 m cylinder along −Z from 5 m in front of the car,
   and the radius is scaled by something not in the grab.

The ring's own lifetime (1–3 s) and its 0.2 m cross-section are decoded either way, and the
**expansion reading is the only one that produces a circle at all**, so it is presented as derived
rather than as fact.

---

## 4. The sound (decoded)

| member | event | bank | evidence |
|---|---|---|---|
| `RBatmobileSonar.ScanSound` | **`Play_BML_Sonar_Pulse_Full`** | `Engine.BML_Sonar` (package `BmGame`) | `AUDIO_BANKS2.md:154` (bank `BML_Sonar`, path `BmGame.BML_Sonar`, event present) |
| `RBatmobileSonar.BasicScanSound` | **`Play_BML_Sonar_Pulse_Search`** | same | `AUDIO_BANKS2.md:155` |
| rumble loop | `Play_BML_Sonar_Rumble_Lp` + `Stop_BML_Sonar_Rumble_Lp` | same | `AUDIO_BANKS2.md:156`; `AUDIO_FEATURES.md:66` |
| scanner on / off | `Play_BML_Sonar_Turn_On` / `_Off` | same | `AUDIO_BANKS2.md:157-158` |
| charge | `ChargeStartSound` / `ChargeStopSound` | same | `WEAPONS.json` |
| blast | `BlastSound` | same | `WEAPONS.json` |

The bank itself: **`BML_Sonar`, 355,830 B, 7 events, 112 bytes of ids, present-package** on all three
playable packages (`AUDIO_BANKS.md:31, 172`; `AUDIO_BANKS2.md:33`).

**One conflict, stated rather than smoothed:** `AUDIO_FEATURES.md` §sonar lists all six events as
`missing-bank` (`AUDIO_FEATURES.md:64-69`), while `AUDIO_BANKS2.md` resolves the same six to
`BmGame.BML_Sonar` with `yes / yes` (present, hashed). They read different things — the features card
checks the bank *reference* inside the package, the banks card checks the *archive* — so the events
ship in the archive but the package's pointer does not resolve in the features pass. For the port,
what matters is that the **bank is in the install** (§`AUDIO_BANKS.md` row) and the event names are
stable; anyone reusing them should expect to re-point the package.

---

## 5. JC3: what exists to copy, and what does not

### 5.1 There is no ring effect by name (decoded search)

Over the **930** `.effc` paths that appear in `Research/JC3Grab/*.json*`:

| word in path | paths |
|---|---:|
| `ring` | **0** |
| `shock` | **0** |
| `wave` | **0** |
| `pulse` | **0** |
| `radial` | **0** |
| `emp` | **11** (`effects/destruction/explosion_emp_flatbed.effc`, `effects/jc_weapons/emp_mounted/impact_emp_large.effc`, …) |
| `blast` | 1 (`effects/cinematic/dmg_fire_engine_plane_top_lblast.effc`) |

`FX9_HAZE.md` §1's keyword census over the 955 paths agrees for the words it covers (`haze` 0,
`steam` 0, `distort` 0, `refract` 0, `vapor` 0, `shimmer` 0, `warp` 0). **So no shipped effect is
named as an expanding ring** — the nearest *names* are the EMP effects, which are explosions with an
EMP look, not a sonar sweep.

### 5.2 The nearest *logic* carrier is the force pulse (decoded)

`CForcePulse` + `ForcePulseSettings` (G2-17): **307 pulses across 232 vehicle `.ee`s**, 23 tunes, and
**exactly 8 numeric members**, all damage/radius (`FORCEPULSE.md` §3):

| member | fleet min | fleet max | what it is |
|---|---:|---:|---|
| `PlayerDamage` | 0 | 3000 | damage at the centre |
| `PlayerDamageRadius` | 1.5 | **50** | metres |
| `PlayerDamageRadiusMin` | 0 | 1 | — |
| `PlayerDamageRadiusPercentageMax` | 0 | 1 | share of the radius at full damage |
| `AIDamage` | 0 | 1000 | — |
| `AIDamageRadius` | 0 | **50** | metres |
| `AIDamageRadiusMin` | 0 | 1 | — |
| `AIDamageRadiusPercentageMax` | 0 | 1 | — |

**There is no speed, no lifetime, no falloff-time member.** The pulse is an instantaneous damage
sphere; its expansion is engine-side and **UNKNOWN** in the files.

The one tune with **zero damage** is `gen_explosion_5m_nodamage.ftune`, whose eight values are
`PlayerDamage 0 / PlayerDamageRadius 5 / *Min 0 / *Percent 0` and the same on the AI side — i.e. a
push-only 5 m sphere. The closest radius to BmAK's 25 m is the **EMP** pulse on the flatbed,
`truck_emp.ftune` = **100 / 25 m** (`FORCEPULSE.md` §5).

---

## 6. The parameters that equal BmAK

| BmAK quantity | BmAK value | JC3 carrier | parameter to set |
|---|---:|---|---|
| pulse type | a ring, no damage | `CForcePulse` (owner: the vehicle root) | use `gen_explosion_5m_nodamage.ftune` as the template |
| **radius** | **25 m** (1 s) / 37.5 m / 75 m (3 s) | `PlayerDamageRadius`, `AIDamageRadius` | **25** for the 1 s reading (or **37.5** / **50** for the longer ones; the member's fleet max is 50) |
| **damage** | none | `PlayerDamage`, `AIDamage` | **0** (keeps it a push, like the shipped 5 m template) |
| falloff floor | none | `*RadiusMin`, `*RadiusPercentageMax` | **0, 0** (the shipped zero-damage template's own values) |
| **speed** | 25 m/s | — | **no member**; the expansion is engine-side (UNKNOWN) |
| **thickness** | 0.2 m ring mesh | — | a **new effect**; JC3 has no ring mesh to point at |
| **fade** | 1–3 s envelope, curve UNKNOWN | — | the new effect's own lifetime; set **1.5 s** to sit in BmAK's band |
| **sound** | `Play_BML_Sonar_Pulse_Full` / `_Search` | **no sonar class exists** (`WPN-8`: 0 sonar classes in the 103-class census) | reuse an `SAttachedEffect` on the entity with BmAK's event name if the bank is kept, else the nearest decoded EMP event |

**Verdict on "the nearest expanding-ring effect":** by name, **none**; by logic, the **force pulse**
(radius + zero damage), and by visual intent, the **EMP effect families**
(`effects/destruction/explosion_emp_flatbed.effc`, `effects/jc_weapons/emp_mounted/impact_emp_large.effc`)
— which are blasts, so the ring's *shape* still has to be authored. That is the gap the brief's
"nearest effect" assumes does not exist; stating it is more useful than picking a blast and calling it
a ring.

---

## 7. Build order

1. **Pulse (logic)** — add or retarget a `CForcePulse` on the private entity with
   `gen_explosion_5m_nodamage.ftune` as the template, `PlayerDamageRadius = AIDamageRadius = 25`,
   both damages **0**, `*Min`/`*Percent` **0**. That gives a 25 m damage-free sphere matching BmAK's
   radius at 1 s.
2. **Ring (visual)** — author a private `.effc`: one mesh emitter on a ring/cylinder mesh,
   `start_size` **0.2 / 0.2 / 0.1**, radius scaled **25 m/s over 1.5 s**, opacity fading to 0 across
   that life (BmAK's fade curve is undecoded, so this is a choice, not a copy).
3. **Sound** — attach `Play_BML_Sonar_Pulse_Full` by name if the bank is retained; otherwise pick the
   nearest decoded EMP event, and record the swap.
4. **Do not** try to make `CForcePulse` animate: it has no time member (§5.2).

---

## 8. Checks run

| check | result |
|---|---|
| gadget members | 10 on `RBatmobileSonar`, **none numeric** (`WEAPONS.json`) |
| system emitters | `Batmobile_Seismic_Sonar` **7** (`mesh, sprite`); Charged **10** (`decal, mesh, sprite`) |
| ring mesh emitter | `start_size` 0.2/0.2/0.1, `Meshes.Blast_Radius_Cylinder`, `beam length True` |
| fast emitter | `[0, 0, −2500]` cm/s at `[0, 0, 500]` (4739, and 4750 in Charged) |
| lifetimes | 1 / 1.5 / 1.5 / 1–3 s; Charged 10 / 1 / 1.5 / 1–4 s |
| radius arithmetic | 25 m/s × 1 s = **25 m**; ×1.5 = **37.5 m**; ×3 = **75 m** |
| fade | **UNKNOWN**: three sonar materials decode `Opacity→—`, `EmissiveColor→—`, `Distortion→—` |
| sound | `Play_BML_Sonar_Pulse_Full` / `_Search` in `Engine.BML_Sonar` (`BmGame`), 7-event bank, 355,830 B |
| sound conflict | `AUDIO_FEATURES.md` says `missing-bank`, `AUDIO_BANKS2.md` says present — both recorded |
| JC3 ring by name | **0** of 930 `.effc` paths contain ring / shock / wave / pulse / radial |
| JC3 pulse members | **8**, damage/radius only; no speed or lifetime (`FORCEPULSE.md` §3) |
| JC3 zero-damage tune | `gen_explosion_5m_nodamage`: 0 damage, **5 m** radius, min 0, percent 0 |
| JC3 nearest radius | `truck_emp.ftune` **100 / 25 m** |

## 9. Change record (per `AGENTS.md`)

1. **Intended change:** add one report that measures BmAK's sonar ring, names its sound, and states
   which JC3 carrier can and cannot reproduce it.
2. **File:** `tmp/freebuff/reports/sonar-pulse-visual-plan.md` — the brief names this path and every
   comparable plan is in `tmp/freebuff/reports/`. No `Research/` card is regenerated and no build file
   is written.
3. **Revert:** delete this file. Nothing else changed (read-only JSON/Markdown queries and
   `write_file`).

## 10. UNKNOWNs

| # | UNKNOWN | settler |
|---|---|---|
| U-1 | whether 2500 cm/s is the ring's radius rate or a shell's travel | the emitter's missing size-over-life / velocity-scale module; a frame grab of the pulse at t=0.5 s and t=1.5 s settles it in one shot |
| U-2 | the ring's fade curve | no opacity parameter on any sonar material; decompile the material instances under `_BmAK_grab` for a ScalarParameter |
| U-3 | the sonar's gameplay radius (as opposed to the visual) | no numeric member on `RBatmobileSonar`; it is in native code |
| U-4 | JC3's pulse expansion speed | no member; engine-side |
| U-5 | whether any `.effc` *contains* a ring mesh without the word in its path | `FX_TABLE.jsonl` rows decode only paths/containers/instances, not meshes; needs a mesh-reference pass |
| U-6 | a JC3 sonar/scan sound event | `WPN-8`: 0 sonar classes in the 103-class census; `JC3_AUDIO_EVENTS.json` has no scan event |
