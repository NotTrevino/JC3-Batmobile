# Lock-on reticle: the entity -> HUD link, from the data side

G-card follow-up, 2026-11-06. Question: `Research/JC3Grab/JC3_HUD_WEAPONS.md` §5 calls the link from a
weapon to `POI_TYPE_LOCK_ON_TARGET` `UNKNOWN` (native). Does the data side settle it? Which weapons
show a reticle on lock, what in their data selects it, and can a private Batmobile missile weapon opt
in **by data alone**?

**Answer, in one paragraph.** The movie side is one POI type (`POI_TYPE_LOCK_ON_TARGET = 21`) drawn as
one rotating clip, and nothing in the movie ever creates it. The data side has exactly one field that
says "this weapon locks": the weapon object's `autoaim_tuning_file` member (`id:6D4C8277`), whose
value is one of two presets, `autoaim_vehicle_lockon_missile.wtune` or
`autoaim_vehicle_no_lockon_missile.wtune`. Vanilla `w618_sportsmuscle_missile` - the Batmobile's own
donor - points at the **lock-on** preset at vehicle level (`WEAPON_WIRING.jsonl`, chassis
`v0300_car_kensington_sportsmuscle`), while its own bundle ships the **no-lockon** preset
(`WEAPONS.md` §1) and its `missile_turning_speed` is **0**. The build today writes the **no-lockon**
preset onto the missile component and rides it on `CBulletWeaponBase`, so it has opted out twice in
data. Data can therefore opt a private weapon **into the acquisition cone and into homing**; it
cannot opt it into the **drawn reticle**, because no data member names a POI, a reticle shape or a
HUD element anywhere in the decoded corpus. That last step is native and stays `UNKNOWN`.

Labels: `decoded` = read from the file cited; `derived` = arithmetic on decoded values; `UNKNOWN` =
not in the files, with what was tried.

## 1. The movie side: one lock-on element, one creator that does not exist

Source: the decompiled `ui/hud.gfx` export read in `JC3_HUD_WEAPONS.md` §4-§5 (260 AS3 scripts,
1280x720, 9 external DDS atlases) and `HUD_SPEC.json` `jc3` block.

| what | value | where |
|---|---|---|
| lock-on POI type | `POI_TYPE_LOCK_ON_TARGET = 21` of 32 `POI_TYPE_*` constants | `hud.as` constant, `hud_code/poi.as` `case 21` |
| the clip | `MCI_icon_and_label.MCI_icon.MCI_lock_on.MCI_reticle` | `poi.as` case 21 |
| motion | `TweenRotation(ret, 1.5, 360, TM_LINEAR, TR_LOOP)` - one turn per 1.5 s | `LOCK_ON_TARGET_ROTATION_TIME` |
| progress bar | `m_HasProgressBar = false` | same case |
| POI constructor | `CreatePoi(type, use_progress_bar, is_minor, label)` - the only one | `hud.as` |
| `CreatePoi(POI_TYPE_LOCK_ON_TARGET, ...)` calls in the movie | **0** | grep of 260 scripts |
| incoming warning | `MCI_safe_area_bottom_middle.MCI_missile_locked`, flashes every 0.5 s | `MISSILE_LOCKED_TIMER`, `FlashMissileLocked` |
| `ShowMissileLocked` / `HideMissileLocked` callers | **0** | grep |
| movie dimensions | 1280 x 720 | `HUD_SPEC.json` `jc3.constants` |

The generic crosshair is a different API and a different element:

```
UpdateWeaponReticle(show:Boolean, weapons_look:int, reticle_size:Number, reticle_shape:int)
```

| shape | id | | look state | id |
|---|---|---|---|---|
| `E_RETICLE_SINGLE_SHOT` | 0 | | `ECrosshairLook_InRangeTargetNeutral` | 0 |
| `E_RETICLE_CIRCLE` | 1 | | `ECrosshairLook_InRangeTargetAllied` | 1 |
| `E_RETICLE_DOT` | 2 | | `ECrosshairLook_InRangeTargetHostile` | 2 |
| `E_RETICLE_NONE` | 3 | | `ECrosshairLook_InRangeNoTarget` | 3 |
| `E_RETICLE_AUTO` | 4 | | `ECrosshairLook_OutOfRange` | 4 |
| `E_RETICLE_WINGSUIT` | 5 | | | |
| `E_RETICLE_ROCKET` | 6 | | | |
| `E_RETICLE_GRENADE_LAUNCHER` | 7 | | | |
| `E_RETICLE_CANNON` | 8 | | | |
| `E_RETICLE_FLAK` | 9 | | | |
| `E_RETICLE_WINGSUIT_WEAPONIZED` | 10 | | | |
| `E_RETICLE_MECH_CANNON` | 11 | | | |
| `E_RETICLE_MECH_MINIGUN` | 12 | | | |
| `E_RETICLE_POWERCORE` | 13 | | | |

14 shapes, 5 look states, widths `RETICLE_*_WIDTH_MIN .. MAX` in the 5..30 px band;
`UpdateWeaponReticle` has **0 call sites** in the movie (`HUD_SPEC.json` `jc3.vehicle_api` lists it
as a public method of the document class, so native code calls it).

`derived`: the movie contains **two** lock instruments and **zero** code that produces either. A
lock-on marker therefore exists only if native code both creates the POI and (for a gun) calls
`UpdateWeaponReticle`. No data file can call a function that has no callers.

## 2. The data side: one field, two presets, 22 members

The only decoded weapon data that describes lock behaviour is the `AutoAim` tune. It is 6 shooter
contexts x 22 `AutoAimSettings` members, 132 rows total (`WEAPONS.md` §13, `T_WP3B_LOCKON.md` §3).

| member | `autoaim_vehicle_lockon_missile` | `autoaim_vehicle_no_lockon_missile` | what it decides |
|---|---|---|---|
| `OnFoot.AngleThresholdNewTarget` | 0.12 | 0.05 | cone to acquire a new target, fractions of a turn |
| `OnFoot.AngleThresholdCurrentTarget` | 0.15 | 0.12 | cone to hold the current target |
| `OnFoot.AngleThreshMultiplierAtCutoff` | 0.15 | 1 | cone widening beyond the cutoff |
| `OnFoot.AngleThreshMultiplierCutoff` | 500 | 120 | distance where that widening applies, m |
| `OnFoot.FitWeightDistance` | 0.15 | 1 | target-scoring weight |
| `OnFoot.CanTargetVehicles` (+ `CanTargetRigidObjects`) | 1 / 1 | 0 / 0 outside `OnFoot` | whether a vehicle may ever be a target |
| `OnFoot.MaxAimDistance` | 750 | 750 | m |
| `OnFoot.MinAimDistance` | 25 | 25 | m |

`decoded` from `autoaim_vehicle_lockon_missile.wtunec` (`patch_win64/game1`, offset 439742464,
2216 B) and `autoaim_vehicle_no_lockon_missile.wtunec` (offset 439750656, 2227 B). **The presets
differ in exactly 15 of 132 rows**, and every one is an angle, a cutoff, a fit weight or a target
class. There is **no** member naming a reticle, a POI, a HUD clip, a shape id or a colour. `derived`:
the tune can gate *acquisition*; it cannot select *art*.

Homing is a second, independent field, in `MissileWeaponTuningBase` at offset 24:

| weapon | `missile_turning_speed` (player / AI) | `missile_loose_lock_distance` | `missile_no_turning_time` |
|---|---|---|---|
| `w609_fighterjet_missile_air_lockon` | 150 / 300 | 0 | 0 |
| `w612_fighterbomber_missile_air_lockon` | 300 / 300 | 0 | 0 |
| `w613_fighterbomber_missile_ground_lockon` | 0 / 0 | 0 | 0 |
| `w614_monorailmissilecar_missile` | 200 / 200 | 0 | 0 |
| `w618_sportsmuscle_missile` | **0 / 0** | 0 | 0 |
| `w611_fighterbomber_missile` | 0 / 0 | 0 | 0 |

`decoded`, `T_WP3B_LOCKON.md` §2.1. There is no boolean "homing" flag: the turning speed **is** the
homing, so `w618` is unguided while it still carries a lock-on acquisition preset.

## 3. Which weapons opt in, and where the opt-in lives

`decoded`, `WEAPON_WIRING.jsonl` (vehicle graphs, 53 entities). The member is the weapon object's
`props["id:6D4C8277"]`, spelled `autoaim_tuning_file` by `WEAPON_WIRING.md:16`.

| weapon id | class at the slot | slot | `autoaim_tuning_file` in the vehicle graph |
|---|---|---|---|
| `w601_helicopter_missile` | `CMissileWeaponBase` | main | `.../autoaim_vehicle_lockon_missile.wtune` |
| `w606_heavyhelicopter_missile` | `CMissileWeaponBase` | secondary | `.../autoaim_vehicle_lockon_missile.wtune` |
| `w608_fighterjet_missile` | `CMissileWeaponBase` | - (unbound) | `.../autoaim_vehicle_lockon_missile.wtune` |
| `w611_fighterbomber_missile` | `CMissileWeaponBase` | main | `.../autoaim_vehicle_lockon_missile.wtune` |
| `w614_monorailmissilecar_missile` | `CMissileWeaponBase` | - (unbound, turret) | `.../autoaim_vehicle_lockon_missile.wtune` |
| `w615_helicopter_heavy_missile` | `CMissileWeaponBase` | secondary | `.../autoaim_vehicle_lockon_missile.wtune` |
| **`w618_sportsmuscle_missile`** | **`CMissileWeaponBase`** | **main, `v0300`** | **`.../autoaim_vehicle_lockon_missile.wtune`** |
| `w621_advancedhelicopter_missile` | `CMissileWeaponBase` | secondary | `.../autoaim_vehicle_lockon_missile.wtune` |

Eight missile ids, twelve wiring rows, one value. **The car the Batmobile is built on already points
its missile at the lock-on preset.**

That is not the whole story, and the two carriers disagree. `WEAPONS.md` §1 records the preset the
weapon **bundle** ships:

| weapon | preset in its own bundle (`WEAPONS.md` §1) | preset at the vehicle slot (`WEAPON_WIRING.jsonl`) |
|---|---|---|
| `w608` | `autoaim_vehicle_no_lockon_missile` | `autoaim_vehicle_lockon_missile` |
| `w611` | `autoaim_vehicle_no_lockon_missile` | `autoaim_vehicle_lockon_missile` |
| `w615` | `autoaim_vehicle_no_lockon_missile` | `autoaim_vehicle_lockon_missile` |
| **`w618`** | **`autoaim_vehicle_no_lockon_missile`** | **`autoaim_vehicle_lockon_missile`** |
| `w601`, `w606`, `w614`, `w621` | none | `autoaim_vehicle_lockon_missile` |

`derived`: for four ids the bundle and the spawning graph name opposite presets, and `w618` is one of
them. Which one the engine reads is **UNKNOWN** (native merge of the bundle entity and the vehicle
graph's override object); no decoded file states a precedence rule. What is proven is that both
strings exist as data, so **both opt-ins are writable**, and a build must set both to be safe.

`UNKNOWN` also stands on the connection from the tune to the POI: `AutoAim` names no POI, and
`poi.as` is never asked for one. The tune decides *whether a target is acquired*; whether the native
layer then paints `POI_TYPE_LOCK_ON_TARGET` and calls `UpdateWeaponReticle` is not in any file. A
drive is the only settling evidence, and that is TEST-stage work.

## 4. What the build carries today

`decoded` by scanning the built `.epe` bytes for `autoaim` and `w6xx` strings (every `Builds/bm-00*`
tree on disk, 6 files, 5 distinct sizes).

| build | size | `autoaim` path in the file | carrier class |
|---|---|---|---|
| `bm-005` (pre-rework) | 124,520 B | `autoaim_assault_rifle.wtune` | 4 x `CBulletWeaponBase` |
| `bm-005` (current, `f4abe91d...`) | 124,488 B | `autoaim_assault_rifle.wtune` | 4 x `CBulletWeaponBase` |
| `bm-006` (pre-rework) | 124,520 B | `autoaim_assault_rifle.wtune` | 4 x `CBulletWeaponBase` |
| `bm-006` (A-03 test build) | 105,430 B | none | - |
| **`bm-006` (current)** | **124,744 B** | **`autoaim_vehicle_mgun.wtune`, `autoaim_vehicle_no_lockon_missile.wtune`** | **4 x `CBulletWeaponBase` (0 `CMissileWeaponBase`)** |

So on the missile path the build writes the **no-lockon** preset - the exact opposite of the donor's
own vehicle-level value - and the missile rides a **bullet** carrier. `MODLOG.md` (B-05/B-06 reworks)
records the same two facts as declared limits: `w618` keeps the shared shipped tune (turning speed
**0**), the two `w618` components are **unbound** (no root slot points at them), and all four
carriers are `CBulletWeaponBase`. `derived`: today's built car cannot lock even if the engine's
native layer were willing, because (a) its acquisition preset is the no-lockon one, (b) the tune it
rides has turning speed 0, (c) a `CBulletWeaponBase` has no `missile_base_tuning` block at all, and
(d) no weapon slot points at the components.

## 5. Can a private Batmobile missile weapon opt in by data alone?

Split the question by what "opt in" means.

| layer | member | data-only? | evidence |
|---|---|---|---|
| acquisition cone | weapon object `props["id:6D4C8277"]` = `autoaim_vehicle_lockon_missile.wtune` (or a private copy) | **yes** | vanilla `w618` on `v0300` already carries the string; the build writes the other preset |
| homing | carrier class `CMissileWeaponBase` + `missile_base_tuning.missile_turning_speed` > 0 (offset 24) | **yes**, but the carrier class is a composition choice, and the shared `w618` tune has 0 | `T_WP3B_LOCKON.md` §2; MODLOG L-1 |
| missile reaching a slot | root slot `secondary (id:00568A74)` or `main_weapon` -> component `_object_id` | **yes** | `w618` components are unbound today (`counts.unbound_weapons = 2`) |
| lock **reticle drawn** | none - no data member names a POI, shape, look or size for a lock | **no** | §1 and §2: 0 creators, 0 `UpdateWeaponReticle` callers, 22 `AutoAim` members with no HUD term |
| lock **sound** | none in the HUD movie | **no** (audio is a separate system) | `JC3_HUD_WEAPONS.md` §5: the movie only flashes; no lock tone constant |

**Result:** a private Batmobile missile can opt into *behaviour* by data alone - swap the preset
string, give it a `CMissileWeaponBase` carrier with its own tune and a non-zero
`missile_turning_speed`, and bind it to a root slot. It cannot opt into *art* by data alone. The
honest statement for the ledger is: **acquisition data-only, reticle native-UNKNOWN.**

## 6. What the BmAK reticle and its tones contain, for the build to match

Sources: `Research/BatmobileGrab/HUD.md` §5, §5.1, §4; `HUD_SPEC.json` `bmak` block (99 scripts, 4
`.tga` externals, 31 `uc_setters`, movie 1024x768, `TickDeltaTime` 0.033); `AUDIO.md`.

The vehicle lock is drawn by **two independent paths that can be on screen at once**:

| path | elements | driven by |
|---|---|---|
| `HudModuleTargets` (the boxes) | `batmobile_lockon`, `batmobile_aim`, `missile_lockon_square_anim`, `missile_border_anim`, `batmobileattack`, and the `VehicleMissileTarget*` family: plain, `_bomb`, `_emp`, `_friend`, `_multi`, `Invalid`; `Tank_Hack_BOMB/EMP/FRIEND` | `UC_SetBatmobileWeapon(primary, bool)`, `UC_SetBatmobileWeaponHit`, `UC_SetBatmobileWeaponFailure` |
| `HudModuleBespokeLocalRadar` (the meter) | `LockonMeter`, `lockonAndHealthMeter`, `lockonStatusTextContainer` | `UC_SetLockonValue(value, kind)`, `UC_UpdateTargetPosition(x,y,z,kind)`, `UC_SetStationaryLockonValue` |

plus battle mode, which swaps in `recticuleHeavy`, `battleMode_crosses_group_anim`,
`battle_mode_topCorner`/`bottomCorner`, `ZoomInterfaceTopBottom`.

| what the BmAK lock shows | BmAK evidence | JC3 element that would have to match | gap |
|---|---|---|---|
| a box per target, 6 kinds (plain, bomb, EMP, friend, multi, invalid) | `VehicleMissileTarget*`, `bBatmobileTarget` on `ModuleStruct_Targets_TargetMovie` | one `POI_TYPE_LOCK_ON_TARGET` rotating clip | 1 marker vs 6 kinds; no kind field in `CreatePoi` |
| an aim box distinct from the lock box | `batmobile_aim` | none | no second POI type; gap for the build |
| squaring/border animation on acquisition | `missile_lockon_square_anim`, `missile_border_anim` | the 1.5 s rotation is the only motion | animation authored by the build |
| target health in the lock meter, full at 1.0, pulse under 0.2 | `TargetHealthProportion` (a proportion, not HP), `param1 < 0.2 && TargetHealthProportion < 0.2` | none - the POI has `m_HasProgressBar = false` | no per-target health member; build composes |
| a status line under the meter | `lockonStatusTextContainer` | POI `label` argument of `CreatePoi` | label is static text, not a state line |
| hit / failure feedback | `UC_SetBatmobileWeaponHit`, `UC_SetBatmobileWeaponFailure` | none | no HUD event member; nearest is ammo/cooldown updates |
| lock tone while acquiring | `Play_Tank_Heavy_LockBeep` / `Stop_VEH_Tank_Heavy_LockBeep` | none in the HUD movie | audio bank event, not HUD data |
| locked tone | `Play_Tank_Heavy_Locked` / `Stop_VEH_Tank_Heavy_Locked` | none | same |
| missile-lock cue (the HUD sting) | `Play_HUD_Missile_Lock` | none | same |
| failure cue | `Play_HUD_fail` | none | same |

All five tone events are shipped on `Playable_BatmobileFunhouse_SF` and repeated on
`Playable_BatmobileJoker_SF` and `Playable_BatmobileMK2_SF` (`AUDIO.md`).

## 7. Gap list against STAGES.md

Per the operator ruling, no row is left as "JC3 has no system". Closest system + gap + BUILD action:

| # | missing BmAK thing | closest JC3 system | gap | BUILD closes it by |
|---|---|---|---|---|
| L-1 | 6-kind `VehicleMissileTarget*` family | `POI_TYPE_LOCK_ON_TARGET = 21` (one clip) | one type, no kind argument | authoring per-kind clips in a private HUD movie build or overlaying authored sprites, and driving them from a mission/graph script that reads the weapon event; record as authored, not decoded |
| L-2 | `batmobile_aim` aim box | `ECrosshairLook_*` 5 states on the generic reticle | the generic reticle is the player gun's, not a vehicle's; shape id is native | TEST-stage observation of which shape a vehicle missile gets, then a private movie that adds a vehicle aim clip |
| L-3 | per-target health in the lock meter | POI `label` only; `CreatePoi` has no progress bar for this type | no health member | a tracker graph that reads target health and a HUD text/bar authored in the private movie |
| L-4 | hit / failure events | weapon ammo + cooldown update calls (`UpdateVehicleWeapons`) | no event channel | graph-side detection of projectile impact, driving the authored clip |
| L-5 | 5 lock audio events | vehicle audio bank / `.sbnk` events | no HUD-side audio API | authoring the 5 events into the Batmobile's private bank, triggered from the graph |
| L-6 | `MissileLockOnDuration` 2.0 s (BmAK) | `AutoAim` has no duration member | 22 members, none is a timer | a script-side timer on the fire button, or accept the cone-only model and record it |
| L-7 | battle-mode heavy reticle | `E_RETICLE_CANNON` (8) / `E_RETICLE_ROCKET` (6) + `reticle_size` | shape selection is native; no member binds a weapon to a shape | TEST observation, then authored clip in the private movie |

Open appearance/HUD classes this leaves for the briefs: **L-1, L-3, L-4, L-5** are BUILD-authored
(would live in a private `ui/hud.gfx` + private sound bank); **L-2, L-7** are TEST-observed first;
**L-6** is a TRANSLATE row with a named omission unless a script timer is accepted.

## 8. Tests that could prove this

| test | command / observation | pass |
|---|---|---|
| T1 preset opt-in present | grep the built `.epe` bytes for `autoaim_vehicle_lockon_missile` | 1+ hit on the missile component (today: 0, the no-lockon string is there instead) |
| T2 carrier class | read the built graph's weapon object class for the missile | `CMissileWeaponBase` (today: `CBulletWeaponBase`) |
| T3 homing value | decode the build's private missile tune at `MissileWeaponTuningBase` offset 24 | equals the target turning speed (e.g. 150), not 0 |
| T4 slot binding | count components whose `_object_id` occurs once in the graph | 0 unbound weapons (today: 2) |
| T5 donor parity | compare the missile component's `id:6D4C8277` with vanilla `w618` on `v0300` | identical string |
| T6 negative control | fire the current build's missile at a hostile vehicle inside 0.15 turn | no lock marker, no homing (the predicted outcome of the no-lockon preset) |
| T7 reticle observation (TEST stage, needs a drive) | lock a hostile vehicle and time the marker | a rotating marker appears within 0.12 rad new-target cone and turns once per 1.5 s; if it does not, the native link is disproven for mod weapons, not for the preset |

T1-T5 are offline and can run against `Builds/bm-006` today. T6/T7 need the test ban lifted
(`tmp/freebuff/APPROVED_Q.txt`).

## 9. Checks

- movie facts: `JC3_HUD_WEAPONS.md` §4-§5, `HUD_SPEC.json` `jc3.constants` (`MovieWidth` 1280,
  `MovieHeight` 720); the same report's `--check` (`Tools/scripts/jc3hudwpn.py`) rebuilds it.
- preset numbers: `WEAPONS.md` §13 and `T_WP3B_LOCKON.md` §3 (15 of 132 rows differ; 22 members x 6
  contexts).
- wiring: `WEAPON_WIRING.jsonl`, 8 missile ids / 12 rows naming the lock-on preset.
- build bytes: 6 `.epe` files under `Builds/bm-00*`, scanned inline (sizes 105,430 / 124,488 /
  124,520 / 124,520 / 124,744 B).
- BmAK: `HUD.md` §4-§5.1, `HUD_SPEC.json` `bmak` (31 setters, 99 scripts), `AUDIO.md` lock events.

Nothing here is taken from a wiki. No game launch, no install, no write outside
`tmp/freebuff/reports`.
