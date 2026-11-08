# The 60 mm cannon's reload circle — the reload seconds, the circle art, its fill and its anchor

STATUS: done — read-only. No game process was started; every number below is decoded from a repo file
at the cited line, or derived arithmetically from one (labelled).
Scope: BmAK side (`RBatmobileHeavyCannon` = `Batmobile_Heavy_Cannon_Primary`, the 60 mm), the HUD
circle it draws (`UC_SetCannonCoolDown` + the movie), and the JC3 member that carries the same beat for
the `w602` / `w605` cannon carriers.

Sources: `Research/BatmobileGrab/WEAPONS.md`, `WEAPONS.jsonl`, `WEAPONS_BOOLS.md`, `ANIMATIONS.md`,
`HUD.md`, `HUD_INTERFACES.json`, `HUD_SPEC.json`; `Research/JC3Grab/JC3_HUD_WEAPONS.md|.json`,
`WEAPONS.md`, `WEAPONS.jsonl`; `Working/Translation/T7_WEAPONS.md`.
Companion (numbers already worked out there, re-verified here): `tmp/freebuff/reports/cannon-60mm-reload-circle-plan.md`.

---

## 1. Answer at a glance

| question | answer | label |
|---|---|---|
| **reload time** | **0.467 s per rack**, two racks = **0.933 s** if they run in sequence | decoded `ANIMATIONS.md:119-120`; derived for the pair |
| reload *sound* length (not a timer) | **0.4 s** (`ReloadSoundDuration` 0x08F0) | decoded `WEAPONS.md:925` |
| shot cadence that the circle is *not* | `FiringInterval` **2.0 s** (0x0828) | decoded `WEAPONS.md:918` |
| magazine / round count | **absent** — no `Ammo`/`Magazine`/`Clip`/`Round` member on any of the 62 weapon objects | decoded absence (1,214-row field scan) |
| circle art (BmAK) | the **battle-reticle ring**, driven by 5 categorical labels `PreReady · Ready · PreReadyLevel1 · PreReadyLevel2 · Blank` — no sprite of its own is recorded | decoded labels `HUD.md:138`; the ring graphic itself **UNKNOWN** |
| fill member (BmAK) | **`UC_SetCannonCoolDown(param1:int)` 0…4** — a state index, **not** a 0…1 fill | decoded `HUD_INTERFACES.json:100-102`, `HUD.md:167` |
| circle art (JC3) | `MCI_radial_loader_cooldown` = **two 180° half-ring masks** `MCI_mask_0_50` + `MCI_mask_50_100` | decoded `JC3_HUD_WEAPONS.md:58, 62` |
| fill direction (JC3) | a **continuous 0→360° sweep**: `rot = v*360`; `mask_0_50.rotation = min(rot,180)`, `mask_50_100.rotation = max(rot-180,0)` → first half then second half; positive Flash rotation = **clockwise** | formula decoded `JC3_HUD_WEAPONS.md:62`; clockwise + start angle **derived/UNKNOWN** |
| screen anchor (JC3) | **bottom-right safe area**: `MCI_safe_area_bottom_right.MCI_vehicle_weapons0 / …1` → `MCI_bullet_bar_anim` → `MCI_radial_loader_cooldown`; pixel x/y **UNKNOWN** (no clip matrix in the dumps) | decoded path `JC3_HUD_WEAPONS.json` `slots.array_line`, `JC3_HUD_WEAPONS.md:58` |
| screen anchor (BmAK) | the **reticle** in battle mode (i.e. screen centre), not a corner widget | decoded (`UC_SetCannonCoolDown` drives reticle labels); centre position derived |
| JC3 fire-interval member | **`fire_rate`**, float, **0x50 (offset 80)** in the weapon `.wtune` — **seconds per shot** | decoded (`WEAPONS.jsonl`, `T7_WEAPONS.md:24`) |
| w602 / w605 values | `w602_mediumtank_canon` **1.75 s**; `w605_smalltank_canon` **0.75 s** | decoded `WEAPONS.jsonl` |
| does it block or pace? | it **paces** (a round per `fire_rate`); the *gate* members `magazine_size -1` / `reload_time_scale 0.0` / `burst_count 1` / `burst_cooldown 0` leave **no reload gate** on either carrier, so nothing but `fire_rate` stops a second shot | decoded values; "trigger pressed inside the interval is dropped or queued" = **UNKNOWN** (§7) |

**One sentence:** the circle is a **0.467 s** animation per rack (0.933 s both), it is drawn as a
**reticle ring in 5 discrete states** on the BmAK side with no fraction, while JC3 already ships a
**360° radial mask loader in the bottom-right safe area** fed by a 0…1 `weapon_cooldown`; the JC3
counterpart of BmAK's 2.0 s beat is the tune member **`fire_rate` (seconds per shot)**, which paces the
cannon (1.75 s on w602) and does not by itself gate it — neither shipped cannon has a magazine.

---

## 2. The reload seconds, with the source

| # | quantity | value | file / offset | label |
|---|---|---|---|---|
| 1 | `Batmobile_V2_Cannon_Reload_Left` | **15 frames, 0.467 s @30 fps**, 56 tracks | `ANIMATIONS.md:120` (identical in Batmobile, MK2, Funhouse, Joker) | decoded |
| 2 | `Batmobile_V2_Cannon_Reload_Right` | **15 frames, 0.467 s**, 57 tracks | `ANIMATIONS.md:119` | decoded |
| 3 | both racks, sequential | **0.933 s** | 2 × #1 | **derived** — nothing states they are sequential |
| 4 | reload sound length | **0.4 s** (Joker instance 0.5) | `RVehicleWeapon.ReloadSoundDuration` **0x08F0**, `WEAPONS.md:925`, `:991` | decoded |
| 5 | reload sound object | `Engine.Play_BML_HeavyCannon_Reload` | `RVehicleWeapon.ReloadSound` **0x08A0**, 3 carriers, `WEAPONS.md:919` | decoded, `missing-object` in the grab (`:940`) |
| 6 | shot interval | **`FiringInterval` 2.0 s** (`0x0828`, FloatProperty) — Joker 2.5 | `WEAPONS.md:918` | decoded |
| 7 | fire pose clip | `Batmobile_V2_Cannon_Fire` **0.700 s** (22 frames) | `ANIMATIONS.md:95` | decoded |
| 8 | `WeaponCoolDown` | **20 s** on the *launcher* family, not the cannon | `T7_WEAPONS.md:179`; `WEAPONS.md:553` | decoded — a different beat (barrage cooldown) |
| 9 | magazine / ammo | **absent** on all 62 weapon objects | `ammo-types-and-reload-plan.md` §1 (1,214 rows) | decoded absence |
| 10 | `bReloading` | ships **false** | `WEAPONS_BOOLS.md:93` | decoded — the flag exists, nothing in data drives it |

So: **the reload is 0.467 s** (one rack, the only duration in the files) — **0.933 s** if both racks
run one after the other. The operator's "reload circle" visualises exactly this clip, not
`FiringInterval` 2.0 s and not `WeaponCoolDown` 20 s.

### 2.1 Why the cannon differs from the Vulcan, in the data
The Vulcan is a cadence weapon: `FiringInterval` 0.138 s (`T7_WEAPONS.md:143`), heat rate **0.0**
(`HeatUpPerSecond`), no reload clip, no reload sound. The 60 mm is a cycle weapon: 2.0 s between shots,
a 0.467 s two-rack rack animation, a dedicated reload sound, and `AllowChargedShot` false /
`ContinuousFire` true on the same actor (`WEAPONS_BOOLS.md:145-160`). The difference the operator
describes is real in the data, not only in the HUD.

---

## 3. The circle on the BmAK side — a state, not a fill

| item | value | label |
|---|---|---|
| setter signature | `UC_SetCannonCoolDown(param1:int)` | decoded `HUD_INTERFACES.json:100-102` |
| argument domain | **0…4** — five states | decoded |
| labels it drives | `PreReady`, `Ready`, `PreReadyLevel1`, `PreReadyLevel2`, `Blank` | decoded `HUD.md:138` |
| what it is attached to | the **reticle** in battle mode (`ModuleStruct_Batmobile`, 51 frames, 30 fps, 1024×720 stage, `TickDeltaTime` 0.033) | decoded `HUD.md:125, 167` |
| a 0…1 fill / rotation member for the reload | **absent** — `HUD_SPEC.json` carries `bar_fill` / `armour_fill`, both **health**; 0 of the 37 setters is a reload fraction | decoded absence |
| the ring's own art (sprite/shape name, radius, start angle) | **UNKNOWN** — only the label names are decoded; the movie's cooldown graphic is not in the dumps | UNKNOWN |
| measured on screen? | never captured for this task (no screenshot asked for, no process started) | — |

**Consequence:** there is no "fill direction" to read on the BmAK side, because the movie does not
interpolate anything — it *jumps* between five labels. Any 0…1 circle is a **synthesis** the build has to
author (the 5 states pinned to 5 fractions), and `HUD_SPEC.json` has no member to carry it.

---

## 4. The circle on the JC3 side — art, fill, anchor

### 4.1 Where it lives
```
MCI_safe_area_bottom_right
  └ MCI_vehicle_weapons0 / MCI_vehicle_weapons1        (2 slots, main / alternative)
      └ MCI_bullet_bar_anim
          └ MCI_radial_loader_cooldown                  (the circle)
```
Decoded: `JC3_HUD_WEAPONS.json` `slots.array_line` (`this.m_WeaponsArray = new Array(this.MCI_safe_area_bottom_right.MCI_vehicle_weapons0, this.MCI_safe_area_bottom_right.MCI_vehicle_weapons1);`),
`slots.bar_parts` = `["MCI_bullet_bar_anim", "MCI_radial_loader_cooldown", "alpha"]`,
`JC3_HUD_WEAPONS.md:58`.

### 4.2 The art
Two **180° half-ring masks**, `MCI_mask_0_50` and `MCI_mask_50_100` — a circle built from two halves,
so the visible arc is the sum of two rotations. That is the "reload circle" the operator describes,
already shipped in `ui/hud.gfx` for every vehicle weapon slot (`JC3_HUD_WEAPONS.md:62`).

### 4.3 The fill
```
rot = weapon_cooldown * 360
MCI_mask_0_50.rotation   = min(rot, 180)
MCI_mask_50_100.rotation = max(rot - 180, 0)
```
- `weapon_cooldown` is a **fraction**: `1` = full ring, `0` = empty, **`-1` = no loader at all**
  (`InitVehicleWeapons`: `MCI_radial_loader_cooldown.visible = weapon_cooldown != -1`).
- The sweep is **monotonic and continuous**: 0→180° turns the first half, then 180→360° the second.
  Because a Flash `rotation` increases **clockwise**, the ring fills **clockwise** — this step is
  **derived** from the Flash convention, not stated in the file; the masks' rest angle (where "12 o'clock"
  sits) is the clip's own art and is **UNKNOWN**.
- Overcharge rides the same widget: `AnimateOvercharged` tints the bullet bar to alpha 0.7, pulses the
  radial loader, and plays `dlc_wingsuit_weapon_ready` (`JC3_HUD_WEAPONS.md:64`).
- **The sign of the value is the speed, not the direction**: JC3 gives no duration. `rot_degrees` is
  **360** per full `1.0`, so the fill time is whatever clock feeds the 0…1.

### 4.4 The anchor
| piece | value | label |
|---|---|---|
| parent chain | `MCI_safe_area_bottom_right` → `MCI_vehicle_weapons<0|1>` → `MCI_bullet_bar_anim` → `MCI_radial_loader_cooldown` | decoded |
| anchor corner | **bottom-right** of the screen, inside the safe area | decoded (clip name) |
| slot order | index 0 = `EVEHICLE_WEAPON_SLOT_MAIN`, 1 = `..._ALTERNATIVE`; two slots stacked in that clip | decoded `JC3_HUD_WEAPONS.md:56` |
| pixel position / radius | **UNKNOWN** — the decoded record keeps names and code, not the clip matrices | UNKNOWN |

**Anchor contrast, which matters for the build:** the BmAK circle is on the **reticle (screen centre)**
and the JC3 loader is in the **bottom-right corner**. Reproducing "a circle around the crosshair" means
either moving `MCI_vehicle_weapons0` in `hud.gfx`, or accepting the corner loader and letting the reticle
change shape instead (BmAK's 5 labels are reticle states, which is the cheaper mapping).

---

## 5. The JC3 member that carries the fire interval — `fire_rate`

| item | value | label |
|---|---|---|
| member | **`fire_rate`**, float, **offset 0x50 (80)** in the weapon `.wtune` | decoded (`T7_WEAPONS.json` field table: `{"name":"fire_rate","offset":80,"size":4,"type":"float"}`) |
| unit | **seconds per shot** (the same beat as `RVehicleWeapon.FiringInterval`, which is also seconds) | decoded mapping `T7_WEAPONS.md:24` — "shot interval · `RVehicleWeapon.FiringInterval`, seconds · `fire_rate`, seconds · **exact 1:1**" |
| BmAK counterpart | `RBatmobileHeavyCannon` / `RVehicleWeapon.FiringInterval` 2.0 s | decoded `WEAPONS.md:918` |
| `w602_mediumtank_canon` | **`fire_rate` 1.75** (T-11 writes **2.0**, `T7_WEAPONS.md:532`) | decoded |
| `w605_smalltank_canon` | **`fire_rate` 0.75** | decoded `WEAPONS.jsonl` |
| sibling fields on both | `magazine_size` **-1**, `reload_time_scale` **0.0**, `burst_count` **1**, `burst_cooldown` **0.0** | decoded `WEAPONS.jsonl` |
| leveled variant | `fire_rate_level_2` @0x54 (0.12 on several tunes) | decoded |

### 5.1 Does it block firing, or only pace it?
- **It paces.** `fire_rate` is the interval between successive rounds; a held trigger produces one round
  per `fire_rate`. Evidence: T-WP2's Q-3 #3 take — hold the trigger 2 s at `fire_rate` 0.138 and count
  **14 ± 1** impacts (`T7_WEAPONS.md:534`); T-WP1's take times **2.0 s ± 0.15** between cannon rounds
  (`T7_WEAPONS.md:532`). Rounds appear *at* the interval, i.e. the value schedules them.
- **It is not the gate.** On both `w602` and `w605`, `magazine_size` is **-1** (no magazine → the weapon
  never reloads and `reload_time_scale` 0.0 never applies), `burst_count` is 1 and `burst_cooldown` 0.
  So in the shipped tanks the *only* thing between two shots is `fire_rate`. JC3's reload gate lives in
  `magazine_size` / `reload_time_scale` (see `JC3_HUD_WEAPONS.md` §1: `-1` hides the loader), which is
  why the shipped cannon has **no reload circle to show**.
- **What is not settled by the files:** whether a press *inside* the interval is dropped, ignored, or
  queued. `fire_rate` schedules the next round; it does not state trigger handling. **UNKNOWN** — one
  take settles it (§7, pilot card).

---

## 6. What to write (short, so the circle exists at all)

| # | file / object | member | write | why |
|---|---|---|---|---|
| CR-1 | cannon tune clone (`w602` → private) | `magazine_size` | **2** (one round per rack) | `-1` = no magazine = no loader (`weapon_cooldown` stays -1) |
| CR-2 | same | `reload_time_scale` | **1.0** | full step; it is a **scale 0…1**, so it cannot *state* 0.467 s |
| CR-3 | same | `unlimited_ammo` | **1** | BmAK has no ammo pool |
| CR-4 | same | `fire_rate` | **2.0** (T-11's edit) | the 2.0 s beat |
| CR-5 | same | `burst_count` / `burst_cooldown` | **1 / 0** | BmAK single-shot cycle |
| CR-6 | HUD (no edit) | `weapon_cooldown` fed by the mod's own clock | 0 → 1 over **0.467 s** (or 0.933 s both racks) | `rot = v*360` makes the mask close once per reload |
| CR-7 | reticle states (optional) | `Blank/PreReadyLevel1/PreReadyLevel2/PreReady/Ready` | 0.0 / 0.25 / 0.5 / 0.75 / 1.0 | derived, even spacing — only if the reticle should also change at 25/50/75 % |

Nothing here needs a new member on either side; the only undecoded quantity is JC3's absolute reload
duration, which is measured once (fire, time the mask closing) and then inverted into
`reload_time_scale`.

---

## 7. Pilot card

> "Fire the 60 mm once and start the clock: the loader must go from full to empty and **back to full in
> 0.47 s ± 0.10 s** (**0.93 s ± 0.15 s** if the racks run in sequence); a second press inside that
> window must either do nothing or queue one round — never fire early."

Bands: **0.47 s** decoded (`ANIMATIONS.md:119-120`); **0.93 s** derived; the ±0.10 / ±0.15 s tolerance is
three frames of a 30 fps movie (`TickDeltaTime` 0.033). The second clause settles the block-vs-pace
question in §5.1 in the same take.

## 8. UNKNOWNs

| # | unknown | settler |
|---|---|---|
| U1 | the BmAK ring's own art (sprite/shape, radius, start angle) | the movie's cannon label group in `ModularHudBm3` — the extracted streams are not in this checkout (`_BmAK_grab/hud/` holds `lock/` only) |
| U2 | the 5 `UC_SetCannonCoolDown` states pinned to 5 fractions | `HUD_INTERFACES.json` gives the signature only; a capture or the label frame lengths |
| U3 | the JC3 loader's pixel anchor / radius | clip matrices inside `ui/hud.gfx` (not recorded by `jc3hudwpn.py`) |
| U4 | the masks' rest angle, therefore the sweep's start point | the same matrices; clockwise itself is the Flash convention (derived) |
| U5 | whether a press inside `fire_rate` is dropped or queued | the pilot card's second clause |
| U6 | whether the two racks reload sequentially (0.933 s) or together (0.467 s) | the reload clip's key timing |

## 9. Change record

- **Intended change:** none to game data, no code. This document answers the four questions (reload
  seconds, circle art + fill, anchor, JC3 interval member).
- **File written:** `tmp/freebuff/reports/cannon-reload-circle.md`.
- **Why this file:** the request names it as the deliverable.
- **Revert:** delete it. Nothing else was touched; all reads were repo files, no process attached.

## 10. Checks run

| # | check | result |
|---|---|---|
| 1 | `ANIMATIONS.md:119-120`, `:95` | reload clips 15 frames / 0.467 s (all four Batmobile variants); fire pose 0.700 s |
| 2 | `WEAPONS.md:918, 919, 925, 940, 991` | `FiringInterval` 2.0, `ReloadSound`, `ReloadSoundDuration` 0.4 (Joker 0.5) |
| 3 | `HUD_INTERFACES.json:100-102`, `HUD.md:138, 167, 289` | `UC_SetCannonCoolDown(param1:int)`; the 5 labels; reticle attachment |
| 4 | `HUD_SPEC.json` walk | only health `bar_fill`/`armour_fill`; **0** reload fraction |
| 5 | `JC3_HUD_WEAPONS.md:56-66` + `.json` `slots`/`cooldown` | masks, `rot = v*360`, `-1` hides, bottom-right path, `rot_degrees` 360 |
| 6 | `WEAPONS.jsonl` rows | `w602` fire_rate 1.75 / `w605` 0.75; `magazine_size` -1 and `reload_time_scale` 0.0 on both |
| 7 | `T7_WEAPONS.md:24, 104, 143, 178-182, 532, 534` | `FiringInterval` → `fire_rate` 1:1 in seconds; the Q-3 timing takes that prove pacing |
