# The 60 mm cannon's reload circle — BmAK numbers, the HUD element that draws it, and the JC3 loader

**Scope.** The operator's 2026-11-08 fact — *the 60 mm cannon behaves differently from the Vulcan: it has
a reloading circle that shows the reload in progress* — traced to the cannon's reload duration, its shot
count, the HUD element that draws the circle and the member that fills it, then onto JC3's reload system
and its own circular cooldown loader.

Starting points read in full: `reports/ammo-types-and-reload-plan.md`, `reports/cannon-p02-mechanism.md`,
`reports/cannon-recoil-and-muzzle-plan.md`. Sources of record: `Research/BatmobileGrab/objects.jsonl`,
`HUD.md`, `HUD_SPEC.json`, `WEAPONS.md`, `ANIMATIONS.md`, `PARTICLES.md` (via the recoil report), and
`Research/JC3Grab/JC3_HUD_WEAPONS.md` §7, `WEAPONS.md` §2/§10.

**Labels.** **decoded** = read from the file at the row/export/offset cited. **derived** = arithmetic over
decoded values. **UNKNOWN** = absent from every file read, settler named. **absent** = a member that does
not exist (a file answer, not a zero).

**Headline, and it is not what the translation notes assumed.**

1. **BmAK has no magazine and no reload timer.** A field scan of all 1,214 rows in `WEAPONS.json` finds no
   `Ammo`/`Magazine`/`Clip`/`MaxAmmo`/`Round` member on any of the 62 weapon objects (`ammo-types-and-reload-plan.md`
   §1). The only reload-named value is **`RVehicleWeapon.ReloadSoundDuration` = 0.4 s** (`WEAPONS.md:925`,
   `0x08F0`) — the *length of a sound*, not a reload.
2. **The reload that the circle shows is an animation, and it is decoded twice over**:
   `Batmobile_V2_Cannon_Reload_Left` and `…_Reload_Right`, **15 frames, 0.467 s each at 30 fps**
   (`ANIMATIONS.md:119-120`). Two racks → **0.933 s** if they run in sequence (derived).
3. **The HUD element is a five-state ring, not a 0…1 sweep.** The cannon's own timeline group is
   `PreReady`, `Ready`, `PreReadyLevel1`, `PreReadyLevel2`, `Blank` (`HUD.md:138`), driven by
   **`UC_SetCannonCoolDown(0…4)`** (`HUD.md:167`). There is **no float fill member**: `HUD_SPEC.json`
   carries `bar_fill` / `armour_fill` for **health only**, and 0 of the 37 setters is a reload fraction.
4. **JC3's loader is the better carrier**: `SetCooldownRotation(0..1)` sweeps a radial mask **360°** over
   `MCI_mask_0_50` + `MCI_mask_50_100` — literally a circle that fills (`JC3_HUD_WEAPONS.md` §7).
5. **The gap is the duration, not the circle.** JC3's `reload_time_scale` is a **scale (0…1)**, not a
   duration, and the absolute reload time is engine-side → **UNKNOWN**. The build therefore needs one
   measurement take to solve the scale (§4.3).

---

## 1. BmAK — the cannon's numbers, decoded or derived

| # | quantity | value | kind | label |
|---|---|---|---:|---|
| R1 | reload **animation**, one rack | **0.467 s** (15 frames @ 30 fps, 56/57 tracks) | `Batmobile_V2_Cannon_Reload_Left` / `_Right` | **decoded** (`ANIMATIONS.md:119-120`, identical in Batmobile, MK2, Funhouse) |
| R2 | reload **animation**, both racks in sequence | **0.933 s** (2 × 0.467) | arithmetic | **derived** — nothing states they are sequential |
| R3 | reload **sound** length | **0.4 s** (Joker 0.5) | `RVehicleWeapon.ReloadSoundDuration` @0x08F0 | **decoded** (`WEAPONS.md:925`, `:991`) |
| R4 | reload sound object | `Engine.Play_BML_HeavyCannon_Reload` | `RVehicleWeapon.ReloadSound` @0x08A0, 3 carriers | **decoded**, **missing-object** in the grab (`WEAPONS.md:919, 940, 1683`) |
| R5 | shot count / magazine | **absent** — no member on any of the 62 weapon objects | field scan of 1,214 rows | **decoded absence** |
| R6 | shell-rack geometry | `Batmobile_R_Shell_001…009` + `_Chamber` + `_Tween_001…006` (and the `L_` set) | bones, animated **only** by the two reload clips | **decoded** (`cannon-recoil-and-muzzle-plan.md` §1.3) |
| R7 | does 9 shells mean 9 rounds | — | the rack is geometry, not ammunition; no ammo member reads it | **UNKNOWN** (settler §6 U1) |
| R8 | fire cadence | `FiringInterval` **2.0 s** (Joker 2.5) | `RBatmobileHeavyCannon` | **decoded** (`ammo…plan.md` §2) |
| R9 | fire pose | `Batmobile_V2_Cannon_Fire` **0.700 s** (22 frames) | pose clip | **decoded** (`ANIMATIONS.md:95`) |
| R10 | reload as a state flag | `bReloading` ships **false** | `WEAPONS_BOOLS.md:93` | **decoded**, so the flag exists but nothing drives it in data |

**The one-line answer on the numbers:** **reload = 0.467 s per rack (decoded), 0.933 s for both
(derived); the "magazine" is absent, and the only 9 in the files is a rack of shells, not a round count.**

### 1.1 Why this is consistent with the Vulcan difference the operator reports

The Vulcan is a **cadence** weapon: `FiringInterval` 0.138 s, heat 0.0, `OverheatOffValue` 0.25, no
reload (`ammo…plan.md` §2). The 60 mm is a **cycle** weapon: 2.0 s between shots, a 0.467 s two-rack
reload animation, a dedicated reload sound. So the circle is the visualisation of R1/R2, and the
"different behaviour" is real in the data — not just in the HUD.

---

## 2. BmAK — the HUD element that draws it, and the member that fills it

### 2.1 The element

| item | value | label |
|---|---|---|
| module | `ModuleStruct_Batmobile` in `ModularHudBm3` (51 frames, 30 fps, 1024×720 stage) | **decoded** (`HUD.md:125`) |
| cannon timeline group | **`PreReady`, `Ready`, `PreReadyLevel1`, `PreReadyLevel2`, `Blank`** — **5 labels** | **decoded** (`HUD.md:138`) |
| state field | `Blank` (reloading), `PreReady*` (progressing), `Ready` (loaded) | **decoded** labels, **derived** reading |

### 2.2 The member

| item | value | label |
|---|---|---|
| setter | **`UC_SetCannonCoolDown(0…4)`** | **decoded** (`HUD.md:167`, `HUD_SPEC.json`) |
| argument | **integer 0…4** — a *state index*, not a fraction | **decoded** |
| what it drives | the reticle state `Ready` / `Blank` / `PreReady*` | **decoded** (`HUD.md:167`) |
| a 0…1 fill / rotation member for the reload | **absent** — `HUD_SPEC.json` carries `bar_fill` = `Math.min(1, CurrentHealthProportion)` and `armour_fill` = `Math.max(0, CurrentHealthProportion - 1)`, both **health**; 0 of the 37 setters is a reload proportion | **decoded absence** |
| the cannon's own HUD disposition in the translation | **"partial: the HUD supports it, the entity has no weapon component"** | **decoded** (`HUD.md:289`) |

**So the member that "fills" the circle in BmAK is `UC_SetCannonCoolDown`, and it is a 5-value
categorical.** The circle is *drawn* by the movie from the state — the modder cannot drive it with a
0…1 value, because no such value exists. That is the single most useful finding for the JC3 side: JC3
takes the fraction BmAK does not have, so the mapping has to **synthesise** the 0…1 from the reload
clock rather than translate a member.

---

## 3. JC3 — the closest reload system and its circular indicator

### 3.1 The reload system

| member | type | shipped range | meaning as the record states it |
|---|---|---|---|
| `magazine_size` | int32 | **-1 … 8** (22 tunes) | **-1 = no magazine** |
| `reload_time_scale` | float | **0 … 1** | **a scale, not a duration**; 0 = no reload step is scaled in (`WEAPONS.md:880`) |
| `unlimited_ammo` | uint8 | 1 … 1 | never runs dry (§2) |
| `burst_count` | uint8 | 1 … 6 | shots per burst |
| `burst_cooldown` | float | 0 … 5 s | seconds between bursts |

Carriers that already ship a magazine: `w609` **8**, `w613` **6**, `w612` **2**
(`ammo…plan.md` §3). So the "circle" is a solved HUD problem in JC3 and an **unsolved tune problem for
the duration** — `reload_time_scale` cannot state 0.467 s.

### 3.2 The circular indicator

`JC3_HUD_WEAPONS.md` §7, the cooldown column:

| piece | value |
|---|---|
| API | `InitVehicleWeapons(slot_index, …, weapon_cooldown)` / `UpdateVehicleWeapons(…)` |
| loading signal | **`weapon_cooldown` = -1 → no loader**; any other value drives it |
| fill | **`SetCooldownRotation` 0…1 → 360°** over **`MCI_mask_0_50` + `MCI_mask_50_100`** (two half-circle mask clips) |
| overcharge | `AnimateOvercharged`, sound `dlc_wingsuit_weapon_ready` |
| slots | 2 (`MCI_vehicle_weapons0/1`) |
| caller | **native** — the movie's API is decoded, the entity-side caller is not (`JC3_HUD_WEAPONS.md` §8) |

This is a **radial mask swept 0→360°** — the same object the operator describes as a reloading circle,
already in the game, on every vehicle weapon slot.

### 3.3 The two gaps, stated

| gap | evidence | consequence |
|---|---|---|
| the absolute reload **duration** is not a tune member | `reload_time_scale` is 0…1 and documented as a scale (`WEAPONS.md:880`); no `reload_time` member exists in the 444 decoded tune paths | the 0.467 s cannot be written directly — it must be **calibrated** (§4.3) |
| who passes `weapon_cooldown` to the movie | native; `JC3_HUD_WEAPONS.md` §8 (TV-HUD4/§8) | the loader appears only if the entity actually has a weapon component and a magazine — which the cannon clone does |

---

## 4. Values to write, and the build step

### 4.1 Values

| # | file / object | member | write | label |
|---|---|---|---:|---|
| CR-1 | cannon tune (a `w602_mediumtank_canon` clone) | `magazine_size` | **2** (one round per rack) — 1 if a single-shot cycle is preferred | **derived** from the two reload clips R1 |
| CR-2 | same | `reload_time_scale` | **1.0** (full reload step) | **decoded** domain max |
| CR-3 | same | `unlimited_ammo` | **1** (BmAK has no ammo pool — R5) | **decoded** |
| CR-4 | same | `fire_rate` | **2.0** (already T-11's edit; matches `FiringInterval`) | **decoded** |
| CR-5 | same | `burst_count` / `burst_cooldown` | **1 / 0** | **decoded** |
| CR-6 | HUD (no edit — movie-side) | `SetCooldownRotation` target | **360° over 0.467 s** (or 0.933 s for both racks) | **decoded** value, **derived** mapping |
| CR-7 | `UC_SetCannonCoolDown` equivalent | 5 states → fraction | `Blank` = 0.0, `PreReadyLevel1` = 0.25, `PreReadyLevel2` = 0.5, `PreReady` = 0.75, `Ready` = 1.0 | **derived** (even spacing over 5 states) |

### 4.2 The build step that makes the circle fill over the BmAK reload time

1. **Give the cannon a magazine** (CR-1 `magazine_size` 2). A weapon with `-1` never reloads and the
   loader never appears — `weapon_cooldown` stays -1. This is the step that makes the circle exist at all.
2. **Let the reload run** (CR-2 `reload_time_scale` 1.0, CR-3 `unlimited_ammo` 1 so the mag refills
   forever and the fiction stays "no ammo pool").
3. **Measure the fill** with one take: fire once, time `SetCooldownRotation` reaching 1.0 (the mask
   closing) on a 60 fps capture. Call it `T_base`.
4. **Solve the scale**: `reload_time_scale = 0.467 / T_base` if the member multiplies the duration (the
   reading §3.1 implies). Clamp to 0…1 — if `T_base` is already shorter than 0.467 s, the scale cannot
   lengthen it and the build accepts the shorter fill, recording it. *(derived; direction of the scale is
   one of the two things step 3 settles.)*
5. **Map the 5 BmAK states** onto the fraction (CR-7) only if the build also wants the reticle to change
   state at 25/50/75 %; the circle itself needs no state mapping.

**What the build must not do:** invent a reload *timer* member for JC3, or fake the circle with a HUD
element that does not exist. The loader is shipped; the duration is the only unknown, and it is measurable
in one take.

---

## 5. Pilot card

**One sentence:**

> "Fire the 60 mm once and start the clock: the reload circle must start empty and be **full again in
> 0.47 s ± 0.10 s** (**0.93 s ± 0.15 s** if the two racks reload in sequence), and the cannon must not
> fire a second round before the circle closes."

Bands: **0.47 s** decoded (R1), **0.93 s** derived (R2); ±0.10 / ±0.15 s are the tolerance for a 30 fps
HUD movie (`ModularHudBm3.TickDeltaTime` 0.033 s, `HUD.md:125`) — **derived**, so three frames.

---

## 6. UNKNOWN register

| # | unknown | settler |
|---|---|---|
| U1 | whether the 9 rack shells (`R_Shell_001…009`) correspond to a round count | the reload clip's bone keys: do the shells advance one per shot? `cannon-recoil-and-muzzle-plan.md` §3 item 3 |
| U2 | whether the two racks reload **sequentially** (0.933 s) or together (0.467 s) | the same clip's key timing, or a 60 fps capture of two consecutive shots |
| U3 | JC3's absolute reload duration for a `magazine_size` weapon (the base `reload_time_scale` multiplies) | one take (§4.2 step 3); no tune member states it |
| U4 | which way `reload_time_scale` acts (duration × scale, or speed × 1/scale) | the same take, run twice at scale 1.0 and 0.5 |
| U5 | the mapping from `UC_SetCannonCoolDown`'s 5 states to the movie's internal fractions | `HUD_INTERFACES.json` / the `cannon` label group's frame lengths in `ModularHudBm3` |
| U6 | whether the entity-side caller passes `weapon_cooldown` for a **mod** weapon | `JC3_HUD_WEAPONS.md` §8 (native); probe the build with the cannon equipped |

---

## 7. Change record

- **Intended change:** none to game data. This document maps the cannon's reload onto a JC3 tune and the
  shipped cooldown loader.
- **File written:** `tmp/freebuff/reports/cannon-60mm-reload-circle-plan.md`.
- **Why this file:** the request names it as the deliverable.
- **Revert:** delete the file. No other file was touched.

## 8. Checks run

| # | check | result |
|---|---|---|
| 1 | `ammo-types-and-reload-plan.md` §1-§4 | no magazine on any BmAK weapon; `ReloadSoundDuration` 0.4/0.5; `FiringInterval` 2.0/2.5; JC3 `magazine_size` -1…8, `reload_time_scale` 0…1 |
| 2 | `cannon-recoil-and-muzzle-plan.md` §1.1, §1.3 | reload clip 0.467 s; fire pose 0.700 s; the shell rack is geometry, no heavy-cannon casing |
| 3 | `cannon-p02-mechanism.md` | the cannon is aimed by bone rotation, not an animation — no reload mechanism there |
| 4 | `ANIMATIONS.md:119-120`, `:95` | `Cannon_Reload_Left/Right` 15 frames 0.467 s (Batmobile/MK2/Funhouse); `Cannon_Fire` 0.700 s |
| 5 | `WEAPONS.md:919, 925, 940, 991, 1683` | `ReloadSound` → `Play_BML_HeavyCannon_Reload` (missing-object), `ReloadSoundDuration` 0.4 (Joker 0.5) |
| 6 | `HUD.md:125, 138, 167, 289` | the cannon's 5 labels; `UC_SetCannonCoolDown(0…4)`; the "HUD supports it, entity has no weapon component" disposition |
| 7 | `HUD_SPEC.json` walk for fill/reload/circle/ring/cooldown keys | only `bar_fill` and `armour_fill` (health) + `UC_SetCannonCoolDown`; **no reload fill member** |
| 8 | `objects.jsonl` name scan | `RBatmobileCannon` 17, `RBatmobileHeavyCannon` 16, `CannonMuzzle` 4, one `Reload` — no magazine/ammo name |
| 9 | `JC3_HUD_WEAPONS.md` §7 | `weapon_cooldown` -1 = no loader; `SetCooldownRotation` 0…1 → 360° over `MCI_mask_0_50/50_100` |

No game process was started, attached to or injected into; static read only.
