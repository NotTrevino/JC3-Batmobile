# Reticle opt-in: the private missile's data, the HUD boxes, and the build that closes each gap

2026-11-06. `lock-on-reticle-hud-link.md` proved the split: a private Batmobile missile can opt
**into lock behaviour by data**, while the drawn reticle is produced by native code. This is the build
plan for both halves: the exact weapon-preset/AutoAim fields the missile sets, the HUD movie elements
that draw the boxes, BmAK's box system beside JC3's one reticle, and for every difference the closest
JC3 mechanism that reproduces it — with the numbers and the texture/geometry cost.

Labels: **decoded** = read at the named file/tag/offset; **derived** = arithmetic shown;
**UNKNOWN** = absent from the named files, with the file that settles it and a one-sentence
pilot-card check. No game launch, no install, no write outside `tmp/freebuff/reports`.

## 0. Change statement (AGENTS.md)

| item | value |
|---|---|
| intended change | add one report: the data opt-in + HUD build plan for the Batmobile missile reticle |
| file | `tmp/freebuff/reports/reticle-opt-in-build-plan.md` (this file) |
| why this file | the brief names it; it changes nothing the game reads |
| reverted by | deleting this file. No build, `.epe`, `.gfx`, tune or texture was written |

## 1. The plan in one paragraph

The missile weapon sets **`autoaim_tuning_file` = `autoaim_vehicle_lockon_missile.wtune`** on both
carriers (the bundle `.epe` and the vehicle graph's override object), rides a **`CMissileWeaponBase`**
with `missile_turning_speed` **150** at offset 24, and is bound to the root `secondary` slot
(`id:00568A74`). That is the whole data opt-in: 22 `AutoAimSettings` values, five missile fields, the
carrier class and one slot. The HUD half is a private `ui/hud.gfx` built from the shipped 386,281 B
patch copy (1280×720, 260 scripts): the **six-kind box family** replaces the single
`MCI_lock_on.MCI_reticle` clip, a second `batmobile_aim` clip is added, the 1.5 s rotation becomes a
**2.0 s** acquire-then-lock timeline (60 frames at 30 fps), and the radar meter's existing
`UC_SetLockonValue(value, threshold)` and `UC_SetHealthValue(value, instant)` drive the lock
progression and the health fill. The six art variants are selected by authored `label` tokens (the
only per-POI string channel) with `is_minor` as the fallback. Everything is drawn; nothing is left as
"JC3 cannot".

## 2. Weapon data: the fields the private missile sets

### 2.1 The AutoAim preset, all 22 members

`decoded` — `autoaim_vehicle_lockon_missile.wtunec` (`patch_win64/game1`, offset 439742464, 2,216 B;
6 contexts × 88 B). The preset differs from the no-lockon preset in **15 of 132 rows**; every one is
an angle, cutoff, fit weight or target class. The private missile sets these values:

| off | member | value | why the build sets it |
|---:|---|---:|---|
| 0 | `AngleThresholdNewTarget` | 0.12 | acquire a new target inside 0.12 turn |
| 4 | `AngleThresholdCurrentTarget` | 0.15 | hold the acquired target inside 0.15 turn |
| 8 | `AngleThreshMultiplierAtCutoff` | 0.15 | cone widening beyond the cutoff |
| 12 | `AngleThreshMultiplierCutoff` | 500 | metres where widening starts |
| 16 | `StickyAimStartAngle` | 5 | sticky-aim start |
| 20 | `StickyAimAngleNewTarget` | 10 | sticky-aim new target |
| 24 | `StickyAimAngleCurrentTarget` | 15 | sticky-aim held target |
| 28 | `StickyAimStrength` | 0 | no sticky assist (missiles home, not the camera) |
| 32 | `StickyAimMinAccValue` | 0.5 | — |
| 36 | `StickyAimMaxAccValue` | 1 | — |
| 40 | `SnapAimTarget` | 0.2 | — |
| 44 | `FitWeightCurrentTarget` | 0.2 | scoring weight for the held target |
| 48 | `FitWeightDistance` | 0.15 | scoring weight for distance |
| 52 | `FitWeightAngleDeflection` | 0.6 | scoring weight for angle |
| 56 | `AlwaysTargetDistance` | −1 | disabled |
| 60 | `MaxAimDistance` | 750 | 750 m lock range |
| 64 | `MinAimDistance` | 25 | 25 m minimum |
| 68 | `CanTargetCharacters` | 0 | vehicles only |
| 72 | `CanTargetVehicles` | 1 | the target class the car needs |
| 76 | `CanTargetRigidObjects` | 1 | tanks/props |
| 80 | `UseWeaponDirection` | 0 | aim from the camera, not the muzzle |
| 84 | `FactionNeedsToBeHostile` | 0 | any faction can be acquired |

`derived` — this is the same 22-member struct as every other tune (88 B, no gaps), so a **private
copy** written into the build's `.epe` is byte-compatible; only the 15 values above differ from the
no-lockon preset.

### 2.2 The missile block and the carrier

`decoded` (`T_WP3B_LOCKON.md` §2; `WEAPON_WIRING.jsonl`; MODLOG B-05/B-06):

| field | offset | value to write | current build |
|---|---:|---:|---|
| `missile_turning_speed` | 24 | **150** (player) / **300** (AI) | 0 |
| `missile_loose_lock_distance` | — | 0 | 0 |
| `missile_no_turning_time` | — | 0 | 0 |
| `missile_per_shot` | 44 | 1 | 1 |
| carrier class | — | **`CMissileWeaponBase`** | `CBulletWeaponBase` ×4 |
| `autoaim_tuning_file` (`id:6D4C8277`) | — | `.../autoaim_vehicle_lockon_missile.wtune` | `.../autoaim_vehicle_no_lockon_missile.wtune` |
| root binding | — | `secondary` (`id:00568A74`) | 2 unbound components |

**Build steps (offline, all verifiable):**
1. Replace the `w618` missile component's `id:6D4C8277` value in **both** the weapon bundle `.epe`
   and the vehicle graph's override object. The two carriers disagree in vanilla (bundle: no-lockon;
   vehicle slot: lock-on), and which one wins is UNKNOWN, so writing both removes the ambiguity.
2. Swap the component's class to `CMissileWeaponBase` and give it a private
   `MissileWeaponTuningBase` with turning speed 150.
3. Bind `_object_id` into the root `secondary` slot; count unbound weapons = 0.
4. Keep the four existing cannon carriers as they are; this plan adds one missile carrier.

**Proof (offline):** grep the built `.epe` for `autoaim_vehicle_lockon_missile` → ≥1 hit;
`CMissileWeaponBase` present; decode the private tune at offset 24 → 150; unbound weapons → 0;
component `id:6D4C8277` equals vanilla `w618` on `v0300`.

## 3. The HUD elements that draw the boxes

`decoded` — JC3 `ui/hud.gfx` (patch archive `patch_win64/game6+288028672`, 386,281 B; base copy
296,631 B; 260 AS3 scripts; 1280×720; 9 external DDS atlases; largest `hud_i46.dds` 1,044,608 B,
1024×1020).

| element | value |
|---|---|
| lock POI type | `POI_TYPE_LOCK_ON_TARGET = 21` of **32** `POI_TYPE_*` constants |
| clip | `MCI_icon_and_label.MCI_icon.MCI_lock_on.MCI_reticle` |
| rotation | `TweenRotation(ret, 1.5, 360, TM_LINEAR, TR_LOOP)` — **45 frames/turn** at 30 fps |
| progress bar | `m_HasProgressBar = false` |
| constructor | `CreatePoi(type, use_progress_bar, is_minor, label)` — no colour, size or kind argument |
| movie calls | **0** `CreatePoi(21, …)`; 4 `CreatePoi` total |
| incoming warning | `MCI_safe_area_bottom_middle.MCI_missile_locked`, blink **0.5 s** |
| radar meter | `LockonMeter`, `lockonAndHealthMeter`, `lockonStatusTextContainer` |
| radar setter | `UC_SetLockonValue(value:Number, threshold:Number)` — value writes `Bar.Element.scaleX`; threshold (0.3 in the demo) picks display state 0/1/2 |
| target position | `UC_UpdateTargetPosition(angle, distance, bearing, dots)` — radar geometry + tracking-dot count, no kind |
| radar health | `UC_SetHealthValue(value, instant)` — the same `lockonAndHealthMeter` bar |
| status text | display state 0/1/2 → `$Tracking.VehicleLockon` / `VehicleNoLockon` / lost, into `LockonStatusText` |
| vehicle weapon slots | **2** (`MCI_vehicle_weapons0/1`) |
| reticle API | `UpdateWeaponReticle(show, weapons_look, reticle_size, reticle_shape)`; **14** shapes, **5** looks |
| reticle widths | `RETICLE_*_WIDTH_MIN .. MAX` = **5 … 30 px**; out-of-range alpha **0.4** |

`derived` — there is **no kind enum** on either radar call: `UC_SetLockonValue`'s second argument is
a threshold (0.3 in the demo) that picks one of three display states, and `UC_UpdateTargetPosition`'s
fourth is a tracking-dot count. The per-POI data the movie receives is `is_minor` (1 bit) and
`label` (a string). The six art variants are therefore **authored**: six label tokens are the
channel, with `is_minor` as the 1-bit fallback. What a native-created POI puts in `label` is U2.

## 4. BmAK versus JC3, difference by difference

`decoded` — BmAK (`HUD.md` §5, §5.1; `HUD_SPEC.json` `bmak`: 99 scripts, 31 `UC_*` setters, 112 frame
labels, 4 external TGAs, 1024×768 movie, 1024×720 stage, `TickDeltaTime` 0.033).

| # | BmAK shows | JC3 draws | closest JC3 mechanism | build numbers |
|---|---|---|---|---|
| R-1 | **6** target kinds: `VehicleMissileTarget` plain, `_bomb`, `_emp`, `_friend`, `_multi`, `Invalid`; `batmobile_lockon` | **1** rotating clip (type 21); no kind argument anywhere | **HUD movie edit**: six subclips under `MCI_lock_on`, selected by six **label tokens** (fallback: `is_minor` 0/1) | 6 clips; 6 tokens; 2 `is_minor` states; 256² BC1 atlas = **32 KB** (3×2 grid of 64 px icons) |
| R-2 | `batmobile_aim`, a box distinct from the lock box | no vehicle aim clip; generic 14-shape reticle | **HUD movie edit**: add `batmobile_aim` under the same container; drive it with `weapons_look` 2 (hostile) and `reticle_size` **18 px** (mid of 5…30) | 1 clip; 18 px; alpha 1.0; out-of-range look 4 → alpha **0.4** |
| R-3 | `missile_lockon_square_anim` + `missile_border_anim` on acquisition | 1.5 s rotation only | **HUD movie edit**: 2.0 s acquire timeline, then loop the shipped 1.5 s rotation | **60 frames** @30 fps: 0.25 s square-in (**7.5 frames**) + 1.75 s rotate; 1.5 s = **45 frames**/turn |
| R-4 | target health in `LockonMeter`, full 1.0, pulse below **0.2** | POI progress bar off; radar `lockonAndHealthMeter` exists | **icon/value setter**: bind the bar fill to `UC_SetHealthValue(value, instant)` on the same meter; pulse <0.2, full 1.0 | 1 fill; 0.2 threshold; 1.0 full; 0.05 per demo step |
| R-5 | `lockonStatusTextContainer` status line | 3 display states (`VehicleLockon`, `VehicleNoLockon`, lost) written into `LockonStatusText` | **HUD movie edit**: add the missing **acquire** state; 3 native + 1 authored = 4 | 4 states; 1 text field; label ≤ 32 chars |
| R-6 | `UC_SetBatmobileWeaponHit` / `UC_SetBatmobileWeaponFailure` | no event; `UpdateVehicleWeapons` ammo + 0…1 cooldown ring | **icon/colour setter**: hit clip on ammo decrement, failure clip on cooldown == 1; cooldown ring rotation = `value × 360°`, masks at **180°/180°** | 2 clips; 360° ring; 2 masks |
| R-7 | battle-mode `recticuleHeavy`, `battleMode_crosses_group_anim`, top/bottom corners | shapes 6 (`ROCKET`) / 8 (`CANNON`), 5…30 px | **HUD movie edit** for the corners + `UpdateWeaponReticle(true, 2, 18, 8)` for the heavy reticle | shape **8**; look **2**; **18 px**; 2 corner clips |
| R-8 | **5** lock audio events: `Play_Tank_Heavy_LockBeep`, `Play_Tank_Heavy_Locked`, `Play_HUD_Missile_Lock`, `Play_HUD_fail`, stop variants | none in the HUD movie | **private sound bank** + `PlaySound` in the edited movie at the 4 state transitions | 5 events; 4 trigger points |
| R-9 | `MissileLockOnDuration` **2.0 s** hold | `AutoAim` has no duration; HUD has no lock timer | **HUD movie edit**: 2.0 s timer from first `kind` frame to the locked art (R-3); fire gating stays engine-side | **2.0 s = 60 ticks** at 30 fps / 0.033 s |
| R-10 | box appears per target as soon as acquired | **0** movie `CreatePoi(21)` calls; native creates it | **POI marker data**: keep native type 21 as primary; add one `CreatePoi(21, false, false, label)` in the movie only as the private fallback when no POI arrives | 1 call; type 21; no progress bar; label carries the kind token |

`derived` — R-1/R-2/R-6/R-7 are pure movie work (clips + setters), R-4/R-5/R-10 use data the movie
already receives, R-3/R-9 are one timeline, and R-8 is one private bank. No difference needs a new
engine field.

## 5. The private `hud.gfx` build

`decoded` — the patch copy is 386,281 B and the base copy 296,631 B; both decompile to the same 260
scripts and 1280×720 stage. `ffdec` is the tool already used by `jc3hudwpn.py`/`hud_spec.py`.

| step | file | content | number |
|---|---|---|---|
| 1 | `hud_code/poi.as` | case 21 draws six subclips from `MCI_lock_on` instead of one reticle | 6 clips |
| 2 | `hud_code/poi.as` | add `batmobile_aim` child + 4-state label switch | 1 clip, 4 states |
| 3 | `hud.as` / radar module | map `label` token 0…5 → clip index; bind the fill to `UC_SetHealthValue(param1, param2)` | 6 tokens, 0…1 |
| 4 | timeline | 2.0 s acquire, 1.5 s loop rotation | 60 + 45 frames |
| 5 | atlases | one 256² BC1 atlas for the 6 icons and 2 corner clips | 32 KB (+0 to the 9 shipped atlases) |
| 6 | audio | private `.sbnk` with the 5 events, `PlaySound` at 4 transitions | 5 events |
| 7 | package | rebuild `ui/hud.gfx`, patch the `.toc` entry, install only this file | 1 archive entry |

`derived` — the HUD art budget is the smallest of the build: 32 KB for 8 clips, versus the 694 KB
texture headroom on the car. The movie's byte size changes by the clip/script payload only; the
386,281 B patch copy is the baseline.

## 6. Build order and gates

1. Weapon data (§2) — offline; run the five `.epe`/tune checks before any HUD work.
2. Private `hud.gfx` (§5) — decompile the patch copy, apply R-1…R-10, recompile, keep the 260-script
   count and 1280×720 stage.
3. Audio bank — 5 events, 4 trigger points.
4. Gates: built `.epe` has ≥1 lock-on preset, `CMissileWeaponBase`, turning 150, 0 unbound; HUD
   decompiles with 6 kind clips + 1 aim clip + 4 states; atlas ≤ 32 KB; archive entry round-trips.
5. Pilot (test ban lifted): T1 acquisition, T2 kind split, T3 2.0 s hold, T4 health pulse, T5 audio.

## 7. UNKNOWNs: the file that settles each, and the pilot check

| # | unknown | settles in | one-sentence pilot check |
|---|---|---|---|
| U1 | which preset wins when the bundle and the vehicle graph disagree | the native entity merge (no decoded file); evidence in the built `.epe` after writing both | Fire the missile at a hostile inside 0.12 turn and confirm a lock marker appears. |
| U2 | what `label` a native-created type-21 POI carries, and whether native calls `UC_SetHealthValue` for a target | a HUD trace of `ui/hud.gfx` (`hud_code/poi.as` + the native caller); `label` is passed by `CreatePoi` | Lock a car, then a tank, and log the POI label and the health-setter calls for both. |
| U3 | which of the 32 POI type ids are free for new art | `hud.as`'s 32 `POI_TYPE_*` constants | Create each unused id once and count which clips appear. |
| U4 | BmAK's box pixel sizes on its 1024×768 stage | `HUD_INVENTORY.json` + the movie XML element bounds (not extracted) | Overlay the BmAK reference and measure one box's width in stage pixels. |
| U5 | BmAK's box colours | the four external `Image_I1*.tga` atlases | Sample the lock-box border and fill from the reference PNG. |
| U6 | whether native calls `UpdateWeaponReticle` for a vehicle weapon | `hud.as` (0 call sites; native caller UNKNOWN) | Drive with the missile selected and observe whether the reticle shape changes to 8. |
| U7 | whether native creates the type-21 POI for a mod weapon | native HUD bridge; the movie has 0 creators | Fire once with the private movie's fallback `CreatePoi` disabled and see whether a box still appears. |

Each pilot is one fixed-frame observation; none needs a code change to answer.

## 8. Checks and revert

| # | check | result |
|---|---|---|
| 1 | HUD spec counts re-read (`HUD_SPEC.json`) | 99 BmAK scripts, 31 setters, 4 TGAs, 1024×768; 260 JC3 scripts, 9 atlases, 1280×720 |
| 2 | preset values re-read from the two AutoAim tunes | 22 members, 15 differing rows |
| 3 | built `.epe` bytes scanned for presets/carrier | current build: 0 lock-on, ≥1 no-lockon, 0 `CMissileWeaponBase`, 2 unbound |
| 4 | timings recomputed at 30 fps | 2.0 s = 60, 1.5 s = 45, 0.25 s = 7.5 frames |
| 5 | `python Tools/scripts/t_reticle_plan.py --check` | re-derives the anchors and the arithmetic |

No game process was started; no `.gfx`, `.epe`, bank or texture was written. **Revert:** delete this
file; nothing else changed.
