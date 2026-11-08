# Lock hold and 8-target salvo — the closest JC3 systems, and the build that carries them

**Rows:** the BmAK missile lock hold (`RBatmobileEMPMissile.MissileLockOnDuration` 2.0 s) and the
8-target salvo (`RBatmobileMissileLauncher.MaxTargets` 8). `tmp/freebuff/reports/lock-hold-and-salvo-carrier.md`
establishes where JC3 could carry them (§4.1, §7, §8, §9); this note turns that map into a build
composition, because the project rule is that a gap is closed by the build, not reported (`STAGES.md`).

**The composition, in one line:** carry the **hold** on `WeaponTuning.aim_timer_override` (offset 108,
the only root-level timer; 4.0 on the RPG class, **2.0** for BmAK) gated by a 2.0 s `STimerComponent`
on the launcher; carry the **salvo** on `MissileWeaponTuningBase.missile_per_shot` (offset 44, **8**)
driven by a **6-muzzle `SWeaponFirePattern`** cloned from `w501_turret_sam_v2`; carry the **guided
flight** by moving the missile onto a `CMissileWeaponBase` carrier with `missile_turning_speed`
(offset 24) non-zero and the Fire Leech's own AutoAim preset; carry the **reticle** by swapping the
weapon object's `autoaim_tuning_file` (`id:6D4C8277`) from the no-lockon to the lock-on preset and
authoring the BmAK marker art in the private movie.

This is a plan: no build, `.epe`, tune, receipt or ledger row is modified. Revert = delete this file.

Labels: **decoded** = read at the archive entry, offset or file named; **derived** = arithmetic on
decoded values, shown; **UNKNOWN** = absent from the named files, with the file or probe that settles it.

---

## 1. The four pieces against their closest JC3 system

| # | BmAK piece | closest JC3 system | what the system has (decoded) | what the build does |
|---|---|---|---|---|
| P1 | 2.0 s lock hold | `WeaponTuning.aim_timer_override` @108 + `STimerComponent` (entity) | a float timer, 4.0 on 8 RPG-class tunes, −1 on 65; entity timers 0.2–50 s on damage/effects | private missile tune with **2.0**; a 2.0 s `STimerComponent` gate on the launcher |
| P2 | 8-target salvo | `SWeaponFirePattern` + `MissileWeaponTuningBase.missile_per_shot` @44 | 55 pattern objects (name + pointers, no fields); `missile_per_shot` **6** on `w123`, 1 on every vehicle missile; `w501` has **6 muzzles** | private pattern with **6** `SWeaponPoint` muzzles, `missile_per_shot` **8** |
| P3 | Fire Leech guided flight | `CRPGFireLeachWeapon` + `MissileWeaponTuningBase.missile_turning_speed` @24 | Fire Leech class on `w143`, 1 muzzle, 0 patterns, AutoAim 0.12/0.15, `MaxAim −1`, `MinAim 15`, `CanTargetVehicles 1`; turning 150 `w609` / 200 `w614` / 300 `w612` / **0** `w618` | missile moves to `CMissileWeaponBase`, turning **150**, Fire Leech AutoAim as a private copy |
| P4 | lock-on reticle | `POI_TYPE_LOCK_ON_TARGET = 21` + weapon prop `id:6D4C8277` | 1 rotating clip (1.5 s/turn), **0** `CreatePoi` calls, 0 `UpdateWeaponReticle` callers; the prop names the AutoAim preset | prop → lock-on preset; BmAK 6-kind marker art authored in the private movie |

---

## 2. The values, BmAK side (decoded)

| member | offset | value | source |
|---|---|---:|---|
| `RBatmobileEMPMissile.MissileLockOnDuration` | 0x0A00 | **2.0** (3/3 instances) | `Research/BatmobileGrab/WEAPONS.md` §10; `Tools/scripts/v05_combat.py` gate |
| `RBatmobileEMPMissile.CivilianMissileLockOnDuration` | 0x0A04 | 1.0 (3/3) | same gate |
| `RBatmobileMissileLauncher.MaxTargets` | 0x095C | **8** | `WEAPONS.md:1081`, `FOOTAGE.md:121` |
| `MaxTargetsPerLevel` | 0x0A20 | array, 1 item (payload not decoded) | `WEAPONS.md:1087` |
| `MissileSockets` | 0x0A30 | array, **10 items** | `WEAPONS.md` §13 |
| `RBatmobileMissileLauncher.LockOnAngle` | 0x0980 | 40.0° | `WEAPONS.md` §12 |
| `RBatmobileMissileLauncher.LockOnRange` | 0x0984 | 12000.0 | `WEAPONS.md` §12 |
| `RBatmobileMissileLauncher.FireInterval` | 0x098C | 0.5 s | `WEAPONS.md` §13 (Joker launcher) |
| `MissileNumberParameter` | 0x09CC | `Ww_Parameters.BML_NumberOfTargets` (audio) | `WEAPONS.md` §12 |

---

## 3. The values, JC3 side (decoded)

| member / object | where | value | source |
|---|---|---:|---|
| `WeaponTuning.aim_timer_override` | tune member @108, 4 B float | **4.0** on `w143_rpg_fire_leach` (8 files at 4.0, 1 at 0.001, 65 at −1) | `lock-hold-and-salvo-carrier.md` §4.1; `lock-hold-and-salvo-carrier.json` `aim_timer` |
| `MissileWeaponTuningBase.missile_per_shot` | tune member @44, u8 | 1 on every vehicle missile; **6** on `w123` | carrier §7 |
| `MissileWeaponTuningBase.missile_turning_speed` | tune member @24, 4 B float | 150 `w609`, 200 `w614`, 300 `w612`, **0** `w618`/`w611`/`w613` | carrier §9; `T-WP3b.md` |
| `SWeaponFirePattern` / `…Component` | entity objects | 55 / 145, **name + pointers only** | carrier §5, §8 |
| `w501_turret_sam_v2` | `CMissileWeaponBase` entity | **6 muzzles**, turning 35, `missile_per_shot` 1, `STargetPoint.min_aim_distance` 5 | carrier §8 |
| `w143_rpg_fire_leach` | `CRPGFireLeachWeapon` entity | 1 `SWeaponPoint`, **0** patterns, `aim_timer_override` 4.0, `fire_rate` 1.0, `weapon_type` 6, AutoAim 0.12 new / 0.15 current / `MaxAim` −1 / `MinAim` 15 / `CanTargetVehicles` 1 × 6 contexts | `lock-hold-and-salvo-carrier.json` `epe_detail` + `tune_values` + `aa_uniform[11]` |
| `autoaim_tuning_file` prop | weapon object `props["id:6D4C8277"]` | lock-on / no-lockon preset strings | `lock-on-reticle-hud-link.md` §2-§3 |
| HUD lock marker | `hud.as` / `poi.as` | `POI_TYPE_LOCK_ON_TARGET` 21, `LOCK_ON_TARGET_ROTATION_TIME` 1.5, `MISSILE_LOCKED_TIMER` 0.5 | `lock-hold-and-salvo-carrier.md` §6 |

Build today (`Builds/bm-006`): 4 × `CBulletWeaponBase`, 0 × `CMissileWeaponBase`, the **no-lockon**
preset on the missile components, 2 `w618` components unbound, 2 missile `SWeaponPoint`s
(`MissileL` / `MissileR`), turning speed 0 (`lock-on-reticle-hud-link.md` §4).

---

## 4. The build composition

New private tree `Builds/bm-007-lock/`, based on `bm-006`. Four legs, each removable on its own.

### Leg 1 — the 2.0 s hold (P1)

**Member repurposed:** `WeaponTuning.aim_timer_override` @108 of a **new private tune**
`editor/entities/jc_weapons/06_vehicle/bmak_missile/batmobile_missile_bmak.wtune` (built from the
`w618` tune, which is already private to the build tree).

| member | from | to | evidence |
|---|---:|---:|---|
| `aim_timer_override` @108 | 4.0 (the RPG class value; `w143` carries 4.0) | **2.0** | derived — BmAK `MissileLockOnDuration` 2.0 carried 1:1 into the only root-level timer member |
| `fire_rate` | 1.0 (`w143`) | **1.0** | decoded, unchanged |
| `burst_count` / `burst_cooldown` @88 / @92 | 0 / 0.0 | **0 / 0.0** | the salvo is carried by `missile_per_shot`, not a burst (a burst is sequential at one point, carrier §7) |

**Entity object added:** one `STimerComponent` on the launcher component, `duration` **2.0 s**
(repurposed from `w501`'s `STimerComponent`, whose decoded values are 1 / 2 / 6 / 0.6 / 0.01 / 20 s —
2.0 is inside the shipped band). This is the *gate*: the tune timer says how long the weapon may
hold, the entity timer is what the graph can read and act on.

**Why two carriers:** `aim_timer_override` is decoded as a value but its consumer is native
(UNKNOWN U1). The `STimerComponent` is a graph-level object the build already knows how to write
(B-05 writes entity objects); if U1 resolves the other way, the entity timer still closes the hold.

**UNKNOWN, with what settles it:** what `aim_timer_override` gates → `JustCause3.exe` WeaponTuning
consumer (search the 4.0 constant) or pilot card Q-LOCK-1 below.

### Leg 2 — the 8-missile salvo (P2)

**Members repurposed:** `MissileWeaponTuningBase.missile_per_shot` @44 (u8) **1 → 8**, and the
`w618` entity's fire pattern, which today has 2 `SWeaponPoint`s and no pattern.

**Entity objects added** (cloned from `w501_turret_sam_v2`, the only 6-muzzle missile object):

| object | count | detail |
|---|---:|---|
| `SWeaponPoint` (type 2 muzzle) | **6** total (2 exist: `MissileL`/`MissileR`; **4 added**: `MissileC1`, `MissileC2`, `MissileL2`, `MissileR2`) | positions from the BmAK `MissileSockets` array (10 items) where a socket resolves, else the existing pod matrix |
| `SWeaponFirePattern` | **1 added** | name + pointers, no fields (decoded) — it orders the 6 muzzles |
| `SWeaponFirePatternComponent` | **1 added** | binds the pattern to the weapon object |

**Derived numbers**

| # | value | derivation | label |
|---|---:|---|---|
| D1 | **8** | `MaxTargets` 8 → `missile_per_shot` 8 (both are "missiles this launcher may send in one action") | derived, 1:1 |
| D2 | **1.33** | 8 missiles / 6 muzzles = 1.33 → **two** muzzles fire twice per salvo, four fire once | derived |
| D3 | **3.5 s** | (8 − 1) × `FireInterval` 0.5 s = 3.5 s from first to last missile (decoded interval, BmAK side) | derived |
| D4 | **10** | BmAK `MissileSockets` array length; the build uses 6, so 4 sockets stay unwired and are recorded as unused | decoded count, build choice |

**Why 6 muzzles and not 8:** `w501` is the only decoded 6-muzzle missile entity, and
`SWeaponFirePattern` has no count field — the muzzle count *is* the pattern. `missile_per_shot` 8 on
a 6-muzzle pattern is a legal combination because the field counts projectiles, not muzzles
(carrier §7: `w123` fires 6 from one muzzle). The two repeat muzzles are what makes 8 fit 6.

**UNKNOWN, with what settles it:** whether one trigger may fire more projectiles than there are
muzzles → `JustCause3.exe` weapon-fire consumer; the static route is `w123`'s 6-per-shot from its
1 muzzle (`lock-hold-and-salvo-carrier.json` `tune_values.w123_grenade_launcher_upu_210`), which
already proves the field is not clamped to the muzzle count.

### Leg 3 — the Fire Leech guided flight (P3)

**Objects repurposed:**

| from | to | value | evidence |
|---|---|---|---|
| carrier class `CBulletWeaponBase` (4 × today) | `CMissileWeaponBase` on the missile component | — | decoded class on `w618`, `w501`, `w614` |
| `missile_turning_speed` @24 | on the private tune | **150** (from `w609_fighterjet_missile_air_lockon`) | decoded donor; `w618` is **0**, which is why today's missile does not home |
| `missile_no_turning_time` @32 | on the private tune | **0.0** (`w609` value) | decoded |
| `missile_loose_lock_distance` @48 | on the private tune | **0** (`w609`) | decoded |
| `autoaim_tuning_file` (`id:6D4C8277`) | private copy of `autoaim_w143_rpg_fire_leach.wtune` | 0.12 / 0.15 / `Cutoff` 100 / `MaxAim` −1 / `MinAim` 15 / `CanTargetVehicles` 1 | decoded, all 6 contexts identical |

**Why the Fire Leech:** it is the only decoded guided missile-class weapon that is not an aircraft
slot (`CRPGFireLeachWeapon`, `w143`), its AutoAim profile is a complete 22-member block, and its own
entity is a 1-muzzle weapon the build can copy without a vehicle-graph change. The homing *strength*
comes from `missile_turning_speed`, not from the class, so 150 is the decoded donor value; the Fire
Leech's own turning speed is UNKNOWN (its tune carries `bullet_weapon ''` and no missile block —
`lock-hold-and-salvo-carrier.json` `tune_values.w143_rpg_fire_leach`), settled by decoding
`w143_rpg_fire_leach_projectile` with `Tools/scripts/t_lock_salvo.py` extended to projectile
entities, or by `Tools/scripts/t_wp3b.py` on the projectile's `.wtunec`.

**Lock range:** BmAK `LockOnRange` 12000.0 (unit UNKNOWN — 120 m if cm, 12 km if m) and
`LockOnAngle` 40.0°. JC3's decoded member is `MaxAimDistance` @60 (750 on `w609`, −1 = unlimited in
both shared presets). The build carries **−1 (unlimited)** and lets the 40° cone do the gating,
because the cone is the one quantity both sides name in degrees; 750 m would silently clip a
12000-unit range whose unit is not decoded.

**UNKNOWN, with what settles it:** whether a car weapon slot accepts `CRPGFireLeachWeapon`
(no `CCar` binds a lock-on preset today — `T-WP3b.md` contradiction 5) → `JustCause3.exe` weapon
class factory / the Q-LOCK-3 pilot card; static route: `Research/JC3Grab/WEAPON_WIRING.jsonl` slot
list plus `Tools/scripts/t7_weapons.py` class check.

### Leg 4 — the lock-on reticle (P4)

**Member repurposed:** the weapon object prop `id:6D4C8277` (`autoaim_tuning_file`) on the missile
component, from `autoaim_vehicle_no_lockon_missile.wtune` to the private Fire Leech profile — the
same value the vanilla `w618` carries at vehicle level (`WEAPON_WIRING.jsonl`, chassis `v0300`), which
is the donor parity test T5 in `lock-on-reticle-hud-link.md` §8.

**Objects added:** the BmAK marker art the JC3 movie does not have — `VehicleMissileTarget*` × 6
kinds, `batmobile_aim`, the square/border animations, `LockonMeter`, `lockonStatusTextContainer` —
authored into a **private `ui/hud.gfx`** (copy of the JC3 movie) and driven by
`UC_SetLockonValue` + `UC_UpdateTargetPosition` (BmAK-side setters, `HUD.md` §5.1). The JC3 movie
receives an already-chosen target and never creates the POI (0 `CreatePoi` calls), so the private
movie is where the 8 markers are drawn.

**What stays native:** the link from `AutoAim` state to `POI_TYPE_LOCK_ON_TARGET` (21). It is UNKNOWN
and settled by a runtime HUD trace (Q-LOCK-4) or by the native HUD bridge in `JustCause3.exe`;
nothing in any decoded data file names a POI, so no static file settles it.

---

## 5. Derived values carried into the build

| # | value | derivation | label |
|---|---:|---|---|
| D5 | **2.0 s** | BmAK `MissileLockOnDuration` 2.0 → `aim_timer_override` 2.0 and `STimerComponent` 2.0 | derived, 1:1 |
| D6 | **1.6–2.4 s** | 2.0 s ±20 % (the project's ratio tolerance, `T10_DAMAGE.md` §0) — the hold pass band | derived |
| D7 | **0.6 s** | a 90° re-point at 150 units/s = 0.6 s; the guided-flight pass band uses ≤0.8 s to allow the launch arc | derived, conditional on the unit being deg/s (UNKNOWN U5) |
| D8 | **8** | `MaxTargets` 8 → `missile_per_shot` 8 and the marker count | derived, 1:1 |
| D9 | **6** | muzzle count = `w501`'s decoded 6; 8 = 6 + 2 repeat | decoded + derived |
| D10 | **40°** | BmAK `LockOnAngle` 40.0 vs JC3 `AutoAimSettings.AngleThresholdCurrentTarget` 0.15 (unit UNKNOWN) — the cone is set by the JC3 field, the 40° is the BmAK target the pilot check compares against | decoded values, unit UNKNOWN |

---

## 6. Pilot checks, one sentence each

| card | sentence | pass band |
|---|---|---|
| **Q-LOCK-1** (hold) | Lock a hostile vehicle inside the cone and hold the trigger: the first missile must leave **1.6–2.4 s** after the marker appears. | 1.6–2.4 s (D6), 3 runs, mean inside and no single run outside |
| **Q-LOCK-2** (count) | Put **eight** hostiles inside the cone at 100–300 m and press once: exactly **8** missiles leave and **8** markers appear, and a ninth hostile never gains one. | 8 launched / 8 markers, 0 markers on the ninth (integer count, no band) |
| **Q-LOCK-3** (guided flight) | Fire at a target crossing at 40 m/s: at least **7 of 8** missiles strike it and each missile's heading error is inside **5°** within **0.8 s** of launch. | ≥7/8 hits, ≤0.8 s to 5° (D7 ± tolerance) |
| **Q-LOCK-4** (reticle) | After the build's marker art loads, every acquired target shows a marker within the hold, the marker turns once per **1.5 s**, and markers clear on launch. | 8/8 markers, rotation period **1.35–1.65 s** (±10 % of the decoded 1.5 s), 0 markers left after launch |

Controls: same target set, same distance, same cone entry; HUD on for Q-LOCK-2/Q-LOCK-4 and off for
Q-LOCK-1/Q-LOCK-3 (so the marker cannot be used as the timing cue where timing is the measurement).
Each card runs three times; a card passes on its mean with no run outside the band. The test ban
stays until `tmp/freebuff/APPROVED_Q.txt` exists.

---

## 7. UNKNOWNs, each with the file or probe that settles it

| # | unknown | why it matters | file / probe that settles it |
|---|---|---|---|
| U1 | what `aim_timer_override` 4.0 gates | if it is not the hold, the tune timer is decorative and the entity timer carries the 2.0 s alone | `JustCause3.exe` WeaponTuning consumer (the constant 4.0 and its xrefs); **Q-LOCK-1** |
| U2 | whether one trigger may exceed the muzzle count | `missile_per_shot` 8 over 6 muzzles is the salvo | `w123`'s 6-from-1-muzzle is the decoded precedent (`lock-hold-and-salvo-carrier.json`); **Q-LOCK-2** |
| U3 | whether several targets can be held at once | the 8 markers need 8 held targets, not 8 shots at one | `JustCause3.exe` AutoAim/weapon-fire consumer; **Q-LOCK-2** (8 markers at once) |
| U4 | the Fire Leech projectile's own homing member | decides whether 150 is a copy or a retune | `w143_rpg_fire_leach_projectile` entity's tune, decoded by `Tools/scripts/t_lock_salvo.py` (extend to projectile entities) or `Tools/scripts/t_wp3b.py` |
| U5 | `missile_turning_speed` unit (deg/s?) | D7's 0.6 s is a unit assumption | `JustCause3.exe` missile guidance consumer; **Q-LOCK-3** measures the real rate |
| U6 | the AutoAim angle unit (turns vs radians) | the 40° BmAK cone vs 0.15 in the tune | `T_WP3B_LOCKON.md` §3 open item; a cone-entry probe at a measured angle (**Q-LOCK-2**'s ninth-target test) |
| U7 | what paints `POI_TYPE_LOCK_ON_TARGET` | the reticle's existence at all | runtime HUD trace / native HUD bridge; **Q-LOCK-4** |
| U8 | whether a car slot accepts `CRPGFireLeachWeapon` | the Fire Leech class may be player-weapon-only | `JustCause3.exe` weapon class factory; `Research/JC3Grab/WEAPON_WIRING.jsonl`; **Q-LOCK-3** load |
| U9 | `MaxTargetsPerLevel` payload (array, 1 item, not decoded) | a per-level cap could clamp 8 to 4 | `Research/BatmobileGrab/WEAPONS.md` §13 array + `Tools/scripts/grab_weapons.py` decode of the payload |

---

## 8. Offline checks before any launch

| check | command | pass |
|---|---|---|
| private tune decodes, 2.0 / 8 / 150 in place | `python Tools/scripts/jc3adf.py dump <batmobile_missile_bmak.wtune>` | `aim_timer_override 2.0`, `missile_per_shot 8`, `missile_turning_speed 150` |
| Fire Leech AutoAim copy is identical to the source | `python Tools/scripts/t_lock_salvo.py --check` | the 22-member block matches `autoaim_w143_rpg_fire_leach` row for row |
| 6 muzzles + 1 pattern in the graph | `bm_entity.py --check` | 6 `SWeaponPoint` (type 2), 1 `SWeaponFirePattern`, 1 `…Component`, 0 unbound weapons |
| prop swap present | grep the built `.epe` for `autoaim` | the private Fire Leech profile string, no `no_lockon` string |
| reticle art in the private movie | `Tools/scripts/jc3hudwpn.py` | 6 `VehicleMissileTarget*` clips + meter present, 0 `CreatePoi(POI_TYPE_LOCK_ON_TARGET)` still |
| tamper | flip 2.0 → 2.5, 8 → 4, drop one muzzle, revert the prop string | each caught and reverted |

---

## 9. Sources

- `tmp/freebuff/reports/lock-hold-and-salvo-carrier.md` §4.1, §5, §6, §7, §8, §9 — the aim-timer
  distribution, the salvo mechanics, the 6-muzzle SAM, the member-by-member table.
- `tmp/freebuff/reports/lock-hold-and-salvo-carrier.json` — `aim_timer`, `tune_values`,
  `epe_detail.w143_rpg_fire_leach`, `aa_uniform[11]` (the values quoted above).
- `tmp/freebuff/reports/lock-on-reticle-hud-link.md` §2-§5, §8 — the preset strings, the 0 `CreatePoi`
  calls, the current build's carrier class, tests T1-T7.
- `Research/BatmobileGrab/WEAPONS.md` §10 (0x0A00 2.0), §12 (0x095C 8, 0x0980 40.0, 0x0984 12000.0),
  §13 (`FireInterval` 0.5, `MissileSockets` 10), `Tools/scripts/v05_combat.py` (the 3/3 gate).
- `tmp/freebuff/reports/T-WP3b.md` — turning speeds 150/200/300/0, `missile_per_shot` 1 on vehicle
  missiles, the five contradictions (no `CCar` lock-on precedent).

## 10. Change statement and revert

- **Intended change:** add this one plan report; no game data, tune, `.epe`, build tree, receipt or
  ledger row is written. Every number is quoted from the files above or derived from them with the
  arithmetic shown.
- **File:** `tmp/freebuff/reports/lock-hold-salvo-closest-system-plan.md` — the brief names this path.
- **Revert:** delete this file.
