# BmAK lock numbers — the duration, the cone, the count, and what each one governs

**Answer in one paragraph.** `MissileLockOnDuration` **2.0** and `CivilianMissileLockOnDuration` **1.0**
are floats at **0x0A00 / 0x0A04**, but they are declared on **`RBatmobileEMPMissile`** — the
**pursuit-mode** missile launcher (super `RPursuitModeMissileLauncher`, archetype
`Batmobile_EMP_Missile_Launcher`, anim `"PursuitMissileAnim"`, launch socket `"BattleModeSpotLight"`,
`bInstantFire` true) — **not** on `RBatmobileMissileLauncher`, the battle-mode barrage launcher, which has
**no duration member at all**. That is the strongest fact in this brief: the only lock timer BmAK ships
sits on the pursuit missile, and the battle launcher's absence of any timer is consistent with the
operator's "battle diamond appears instantly". The 2.0 s therefore **is the pursuit lock's acquisition
time**; that it specifically drives the shrinking circle rather than a hold-before-launch is *not*
stated anywhere, and is recorded as `UNKNOWN` with the file that would settle it. The cone is **40**
(0x0980) and the range is **12000 cm = 120 m** (0x0984) on the battle launcher. Locks held at once:
**UNKNOWN for the battle launcher** (base class-default export is not in the dump), **1 for the pursuit
missile** (one `LockOnTarget` slot).

Scope note: this settles numbers and units only. Target ordering is a separate brief
(`tmp/freebuff/reports/bm-lock-target-sort-key.md`, verdict `UNKNOWN`).

## 1. The BmAK numbers, with unit and provenance

Labels: `decoded` = the number is in the cited file at that offset; `derived` = arithmetic or a unit
convention applied to a decoded number; `UNKNOWN` = not in any file here.

| value | number | unit | unit provenance | offset | value source |
|---|---|---|---|---|---|
| `MissileLockOnDuration` | **2.0** | **seconds** | **derived** — the field is a bare float; `WEAPONS.md:16` declares the record's conventions as *"Unreal units are centimetres for positions, cm/s for speeds and 16-bit angle units for rotators"* and states **no time unit**. Seconds come from the name/type only, so the unit is not decoded. | **0x0A00** | `WEAPONS.md:839` (`RBatmobileEMPMissile.MissileLockOnDuration`, FloatProperty, 2.0) |
| `CivilianMissileLockOnDuration` | **1.0** | seconds | derived, same caveat | **0x0A04** | `WEAPONS.md:840` |
| `RBatmobileEMPMissile.LockOnTime` | **not serialised** | seconds (derived, same caveat) | — | 0x09EC | `BMSDK_OFFSETS.json`, `RBatmobileEMPMissile`; absent from the archetype's 21 serialised fields (`WEAPONS.md` §10) — likely the live progress accumulator, value UNKNOWN |
| `LockOnAngle` | **40.0** | **degrees** | **derived** — a float angle; `WEAPONS.md:16` only fixes the *rotator* unit as 16-bit ints (65 536 = 360°), which a float 40.0 cannot be | **0x0980** | `objects.jsonl:19641`, `:14150`, `:5209`; `WEAPONS.md:1028` |
| `LockOnRange` | **12000.0** stored = **120 m** | **centimetres** stored | **decoded** unit convention (`WEAPONS.md:16`: positions in cm); the /100 is **derived** | **0x0984** | `objects.jsonl:19641`, `:14150`, `:5209`; `WEAPONS.md:1029` |
| locks held at once, battle | **UNKNOWN** | count | — | **0x095C** `MaxTargets` (int) | **8** on `Batmobile_JokerMissile_Launcher` (`WEAPONS.md:1081`), **16** on `Default__RBatmobileMissileLauncherJoker` (`WEAPONS.md:1116`); **the three `Batmobile_Missile_Launcher` archetypes set no tag at 2396/0x95C** and no base class-default export exists in `objects.jsonl` |
| locks held at once, pursuit | **1** | count | **derived** — a single `LockOnTarget` slot plus `LastLockTarget` | 0x09A4 / 0x09AC | `BMSDK_OFFSETS.json`, `RBatmobileEMPMissile`: `LockOnTarget` `RVehicleNPC`, `LastLockTarget` `RVehicleNPC`; no count member on the class |

`MaxTargetsPerLevel` (0x0A20) is an int array, payload undecoded (`WEAPONS.md:1087`), so the per-upgrade
lock count is `UNKNOWN` too.

## 2. What the 2.0 s governs — the candidates, decided as far as the files allow

The class that declares it decides the missile; the field name decides that it is a duration. Nothing
names the consumer.

| candidate meaning | evidence for | evidence against | status |
|---|---|---|---|
| **the pursuit lock's acquisition time (the circle's shrink)** | declared on `RBatmobileEMPMissile`, whose super is **`RPursuitModeMissileLauncher`** and whose anim node is **`"PursuitMissileAnim"`** (`WEAPONS.md` §10 rows 0xA1C, 0x097C-0x09A0); it has `bTryingToAcquireNewTarget` (0xA30) and `LockOnTarget`/`LastLockTarget` (0x9A4/0x9AC), i.e. a real acquisition state machine; the battle launcher has **no** duration field, matching "battle is instant" | no file states which HUD call the timer feeds | **supported as the pursuit lock time.** That it is *the* circle-shrink driver is `UNKNOWN` |
| a hold before launch | — | `RPursuitModeMissileLauncher.bInstantFire` is **true** (0x09A0, `WEAPONS.md` §10), so the shot is not gated by a second delay after lock | **not supported** |
| a re-acquire time | `bTryingToAcquireNewTarget` (0xA30) exists, and a separate **`LoseLockTime`** (0xA6C) exists for dropping a lock | a duration that governs *re-acquisition* would sit next to `LoseLockTime`, not be the class's only "MissileLockOnDuration" | **not supported** — `LoseLockTime` is the separate member for that |
| another missile (the battle barrage's lock) | — | it is not declared on `RBatmobileMissileLauncher`; the battle launcher's members are `LockOnAngle`/`LockOnRange`/`MaxTargets`/`NthTarget`/`InitialFireDelay`/`FireInterval`/`CooldownDelay` only | **refuted** |
| the civilian variant distinguishes target class | separate `CivilianMissileLockOnDuration` **1.0** vs **2.0** on the same class — the only difference is target class | — | decoded pairing; which targets count as "civilian" is `UNKNOWN` |

So: **2.0 s belongs to the pursuit missile lock, 1.0 s to its civilian-target lock, and the battle
missile lock has no duration because it has no timer.** The operator's report of "pursuit has a visible
lock time, battle does not" is the one model the data supports without contradiction.

## 3. JC3 members that could hold each of these numbers

From `Working/Translation/T_WP3B_LOCKON.md` §3 and §3.1 (decoded from `autoaim_vehicle_lockon_missile`
/ `..._no_lockon_missile` and the three per-weapon `OnFoot` tunes). Values shown are what each member
**already** carries.

| BmAK number | JC3 member that could hold it | offset | current value | fit |
|---|---|---|---|---|
| **2.0 s / 1.0 s lock duration** | *(none)* — `AutoAimSettings` has 22 members, none matching `duration\|hold_time\|lock_time\|linger` (asserted, `T_WP3B_LOCKON.md` §9) | — | — | **no carrier.** Closest time-shaped members: `missile_no_turning_time` **0** (`MissileWeaponTuningBase` +32), `missile_detonation_time` **-1** (+36), `missile_loose_lock_distance` **0** (+48, a distance) — none is a lock timer |
| | `LOCK_ON_TARGET_ROTATION_TIME` (HUD movie) | — | **1.5 s per turn** | a *visual* period, not a fill; cannot hold 2.0 |
| | `CAimPOIWeaponComponent` prop `id:2D0B3C09` | — | **25 / 50 / 100** | unknown meaning; not a duration |
| **40 deg cone** | `OnFoot.AngleThresholdNewTarget` | 0 | `w609` **0.085**, `w612` **1.4**, `w613` **0.12**; preset **0.12** (lockon) / **0.05** | angle exists; **unit unknown** (0.12 as turns = 43.2°, as radians = 6.9°) |
| | `OnFoot.AngleThresholdCurrentTarget` | 4 | `w609` **0.3**, `w612` **1.4**, `w613` **0.15**; preset **0.15** / **0.12** | hold-cone; same unit problem |
| | `OnFoot.AngleThreshMultiplierAtCutoff` / `...Cutoff` | 8 / 12 | **0.15 / 500** (lockon), **1 / 120** (no-lockon) | cutoff is a **distance in m**, not an angle |
| **120 m range** | `OnFoot.MaxAimDistance` | 60 | **750** (`w609`), **750** (`w612`), **-1** (`w613`); **-1** in both shared presets | range exists; 120 is writable here |
| | `OnFoot.MinAimDistance` | 64 | **25** (`w609`), **5** (`w612`), **15** (`w613`); **25** in the presets | inner gate |
| | `WeaponTuning.max_range` | — | **750 m** (`w609`), **300 m** (`w612`/`w613`/`w614`/`w618`) | per-tune cap |
| **locks held at once** | *(none)* — `missile_per_shot` is **1** on every vehicle missile; no member counts targets (`T_WP3B_LOCKON.md` §5) | 44 | **1** | **no carrier**; a multi-lock must be script-side |
| | `burst_count` / `magazine_size` | — | **6** (`w614`), **8** (`w609`) | sequential missiles at one aim point, not N targets |

## 4. HUD: where the lock fill is shown, and the two reticle shapes

Sources: `tmp/freebuff/reports/lock-on-reticle-hud-link.md` §1, §6; `Research/BatmobileGrab/HUD.md:218-219`,
`:242-255`.

| element | BmAK / JC3 | shape as the operator describes it | what the files support |
|---|---|---|---|
| **battle reticle** | BmAK `HudModuleTargets`: `batmobile_lockon`, `missile_lockon_square_anim`, `missile_border_anim`, `VehicleMissileTarget` + `_bomb/_emp/_friend/_multi/Invalid` (`HUD.md:218`) | **orange diamond, appears instantly** | **shape: not decoded** — the movie exposes clip *names*, no geometry and **no colour** anywhere in `HUD.md`/`HUD_SPEC.json`. `missile_lockon_square_anim` is the square/diamond-plausible clip; "instant" matches the **absence of any duration member** on `RBatmobileMissileLauncher`. Colour and shape are operator facts only. |
| **pursuit reticle** | BmAK radar path: `LockonMeter`, `lockonAndHealthMeter`, `lockonStatusTextContainer` (`HUD.md:219`), driven by `UC_SetLockonValue(value, kind)` and `UC_SetStationaryLockonValue` (`HUD.md:254`) | **diamond with edge centres missing + a circle that starts large and shrinks** | **supports the existence of a fill**: `UC_SetLockonValue(value, kind)` is a continuous 0..1-style value into `LockonMeter`, i.e. the meter is what "shrinks". The "diamond with missing edge centres" is **not** in any file — no clip named for it. |
| **where the fill is** | the **radar module** (`HudModuleBespokeLocalRadar`), not the target-box module | — | **this is why battle and pursuit can differ**: the box path (`HudModuleTargets`) carries no meter, the meter path carries `UC_SetLockonValue`. That division is the closest the files come to confirming two different reticle behaviours. |
| **lock sound during fill** | `LockOnBeepSound` / `LockOnBeepProportionParam` (`Ww_Parameters.BML_AP_Rocket_Lock`) on the EMP launcher (`WEAPONS.md` §10) | — | decoded: a **proportion parameter** implies a continuous 0..1 lock value exists on the BmAK side — but it is fed to audio, and no file shows the HUD and audio being fed from one value. |

**Match claims I am *not* making:** that 2.0 s equals any HUD clip duration, that the 1.5 s POI rotation
is the battle reticle, or that the orange colour exists in BmAK data. None is in the files.

## 5. UNKNOWN table

| item | why UNKNOWN | file that would settle it |
|---|---|---|
| the unit of `MissileLockOnDuration` (seconds vs ticks) | no unit metadata; `WEAPONS.md:16` covers cm, cm/s and rotator units only | the engine's property serializer, or a decompiled `RBatmobileEMPMissile` tick that advances `LockOnTime` (0x09EC) against it |
| whether 2.0 s is the circle's shrink time, a hold, or a re-acquire | no file names the consumer of the field | decompiled `RBatmobileEMPMissile` (`LockOnTime`/`bTryingToAcquireNewTarget` usage) or a BmAK drive timing the `LockonMeter` |
| the degree unit of `LockOnAngle` | float angle, no unit declared | engine `FRotator` conversion; a 40 vs 65536-scale check at runtime |
| what counts as a "civilian" target for the 1.0 s variant | no member names a target class | `RBatmobileEMPMissileCivilian`-style check in the native class; `CivilianMissileLockOnDuration`'s call site |
| battle-launcher lock count (`MaxTargets`) | base class-default export `Default__RBatmobileMissileLauncher` is absent from `objects.jsonl`; the three archetypes set no 0x95C tag | a dump that includes the base CDO, or the runtime value of 0x095C |
| `MaxTargetsPerLevel` payload | array, undecoded (`WEAPONS.md:1087`) | the same array re-decoded with element payload |
| BmAK reticle shape and colour | `HUD.md`/`HUD_SPEC.json` record clip names and setter signatures, never geometry or colour | the `hud.gfx` bytecode of the `HudModuleTargets`/`LocalRadar` clips |
| which JC3 HUD call a lock timer would feed | `AutoAim` names no HUD term; `poi.as` `m_HasProgressBar = false` for `POI_TYPE_LOCK_ON_TARGET` | native aim manager, or a drive reading `UC_SetLockonValue` |

## 6. What the JC3 build must do

**Battle diamond, instant:**
1. Point the missile component's `autoaim_tuning_file` (`id:6D4C8277`) at **`autoaim_vehicle_lockon_missile.wtune`** — today the build writes the *no-lockon* preset (`lock-on-reticle-hud-link.md` §4), which is the opposite of the donor `w618` on `v0300`.
2. Keep the acquisition cone wide enough that "instant" reads as instant: the lock-on preset's `AngleThresholdNewTarget` **0.12** / `CurrentTarget` **0.15**, versus **0.05 / 0.12** in the no-lockon preset (the only 15-row difference, §3 of T_WP3b).
3. Do **not** add a timer: no JC3 weapon member can hold one, so "instant" is the only model the data expresses. The drawn diamond itself must be authored — no data member names a POI, shape or colour (0 `CreatePoi(POI_TYPE_LOCK_ON_TARGET, …)` calls in 260 scripts).

**Pursuit circle, shrinking over 2.0 s:**
4. Drive a 0..1 value from a script timer over **2.0 s** and feed the authored meter clip. BmAK's own tick is `TickDeltaTime = 0.033` (`HUD_SPEC.json` `bmak.constants`), i.e. **≈60 ticks** for 2.0 s (*derived*).
5. Hold the shot until the timer completes — BmAK does this with `bInstantFire` true *after* the lock, so in JC3 the delay is the script timer, not a weapon member (`missile_per_shot` 1, no duration member).
6. Use **1.0 s** when the target is civilian, matching `CivilianMissileLockOnDuration`, and copy **`LockOnAngle` 40 / `LockOnRange` 120 m** onto the acquisition (`AngleThreshold*` and `MaxAimDistance` **120**, replacing the fleet's -1/750).
7. Accept that re-acquire (`bTryingToAcquireNewTarget`, `LoseLockTime`) has **no JC3 counterpart** — that is a script-state decision, not a tune value.

## 7. Limits

Static reads of `Research/BatmobileGrab/objects.jsonl`, `WEAPONS.md`,
`Research/BatmobileGrab/BMSDK_OFFSETS.json`, `HUD.md`, `HUD_SPEC.json`,
`tmp/freebuff/reports/lock-on-reticle-hud-link.md`, `tmp/freebuff/reports/T-WP3b.md`,
`Working/Translation/T_WP3B_LOCKON.md`. No game launch, no install or archive written, no file under
`Research/` or `Working/Translation/` modified. `LockOnTime`, `bTryingToAcquireNewTarget`,
`LockOnTarget`, `CurrentTargets` and `LoseLockTime` are runtime members and are absent from every
archetype export, so their live values stay `UNKNOWN`. The two reticle shapes are the operator's
observation (marked uncertain by the operator); the files confirm the *split* between the box path and
the meter path, but not the geometry or the colour.
