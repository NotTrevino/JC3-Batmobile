STATUS: done

# Homing weapon tunes → Missile Barrage values (WPN-3)

Card scope: the **Missile Barrage** (`RBatmobileMissileLauncher`, 3 instances), property by property —
lock time, acquisition cone, target count, missile count, homing turn rate, speed, damage — each against
the nearest JC3 tune and member with its offset, the value to write, and what the build must add where no
member exists.

**Sources, cited not re-derived:** `Working/Translation/T_WP3B_LOCKON.md` (103 tunes, 2 shared presets,
3 per-weapon `AutoAim` tunes; `MissileWeaponTuningBase` offsets; the 15-row preset diff; no duration
member), `tmp/freebuff/reports/lock-hold-salvo-closest-system-plan.md` (the hold/salvo composition:
`aim_timer_override` @108, `missile_per_shot` @44, the 6-muzzle SAM, pilot cards Q-LOCK-1…4),
`tmp/freebuff/reports/wp4-fire-leech.md` (Fire Leech values, `w618`'s fire block: damage 1500,
velocity 360, range 300, fire_rate 0.5), `Research/BatmobileGrab/WEAPONS.md` §12 (launcher fields),
§13 (Joker launcher), and the `Batmobile_Missile_Projectile` / `Batmobile_JokerMissile_Projectile`
sections (`WEAPONS.md:400-500`, `:1560-1615`).

**New in this card:** the barrage's own projectile carries **no speed, no acceleration and no homing**
(`WEAPONS.md:464-485`: all three absent on all 3 instances), so the *only* BmAK numbers the barrage
itself supplies are the launcher's four (`MaxTargets` 8, `LockOnAngle` 40, `LockOnRange` 12000,
`WeaponCoolDown` 20) plus the projectile's damage triple (250 / 0 / 25000). Every other row in the
table below is a **JC3 donor value**, not a BmAK copy — and that is the honest shape of WPN-3.

Labels: **decoded** = read at the file/offset named; **decoded (fleet)** = counted across the corpus;
**derived** = arithmetic shown; **UNKNOWN** = absent from the named files, with the file that settles it
and (where a check exists) a pilot card.

**Not done:** no build, no tune or `.epe` write, no ledger/backlog edit, no game launch. This file is
new; revert = delete it.

---

## 1. The headline

**Four of the seven barrage properties are data copies and three are not.** The launcher's
`MaxTargets` 8, `LockOnAngle` 40°, `LockOnRange` 12000 and `WeaponCoolDown` 20 are **decoded**
(`WEAPONS.md` §12, all 16 fields identical across Batmobile/MK2/Funhouse, 48 comparisons, 0
differences). Its projectile contributes **damage 250, radius 0, momentum transfer 25000** and
**nothing else**: `Projectile.Speed`, `Projectile.MaxSpeed`, `RBatmobileMissile.AccelRate`, the homing
bool at `0x0420` and `HomingDelay` are **absent from all 3 instances** (`WEAPONS.md:464-485`).

So the table's real content is: **which JC3 member carries each behaviour, and which number is the
donor's rather than BmAK's.** Three rows cannot be written at all — the lock hold has no member
(`T_WP3B_LOCKON.md` §4.1), the target count has no member (§8.5), and the cone can't be converted
because the `AutoAim` angle unit is UNKNOWN (§4.2). Those three are what the build composes or declares,
not what it copies.

---

## 2. The table

`missile_base_tuning` offsets are `MissileWeaponTuningBase` in the tune's type dictionary (identical in
`w609`/`w612`/`w613`/`w614`/`w618`/`w611`, asserted — `T_WP3B_LOCKON.md` §2). `AutoAimSettings` offsets
are the 88-byte context block (`T_WP3B_LOCKON.md` §3.1). `aim_timer_override` @108 and
`burst_count`/`burst_cooldown` @88/@92 are the lock-hold plan's decoded rows. Fire-block members whose
offset this card does not quote (`damage`, `velocity`, `impulse`, `max_range`, `fire_rate`,
`magazine_size`) are read from the tune's type dictionary at build time by `jc3adf.py` — the value is
decoded (`wp4-fire-leech.md` §3.1), the offset is resolved, not typed.

| # | BmAK property | BmAK value (offset) | nearest JC3 tune | member + offset | value to write | what the build adds | evidence |
|---:|---|---|---|---|---|---|---|
| 1 | **lock time** | `RBatmobileEMPMissile.MissileLockOnDuration` **2.0 s** `0x0A00`; civilian **1.0** `0x0A04` (3/3 instances) | private tune from `w618_sportsmuscle_missile` | `WeaponTuning.aim_timer_override` **@108** (4.0 on `w143`, −1 on 65) | **2.0** | `STimerComponent` **2.0 s** on the launcher (the graph-readable gate; the tune timer's consumer is native) | decoded both sides; what @108 *gates* UNKNOWN |
| 2 | **acquisition cone** | `RBatmobileMissileLauncher.LockOnAngle` **40.0** `0x0980` | `autoaim_vehicle_lockon_missile` (shared) or a private copy of Fire Leech's | `AutoAimSettings.AngleThresholdCurrentTarget` **@4**, `…NewTarget` **@0** (preset 0.15 / 0.12) | **keep 0.15 / 0.12** — the converted value would be **0.1111** (if turns) or **0.6981** (if radians); ship neither until the unit is pinned | nothing structural; a private `AutoAim` copy so the car keeps the lock-on preset with `CanTargetCharacters` 0 | decoded values; **angle unit UNKNOWN** |
| 3 | **target count** | `RBatmobileMissileLauncher.MaxTargets` **8** `0x095C`; `MaxTargetsPerLevel` `0x0A20` array 1 item (payload not decoded); Joker CDO **16** | `w614_monorailmissilecar_missile` (6-missile vehicle launcher) | **none** — no tune names a target count; `missile_per_shot` **@44** counts projectiles, not targets | **8** on `missile_per_shot` @44, as the closest count member | 6-muzzle `SWeaponFirePattern` + the multi-target bridge; 8 markers require 8 held targets | decoded absence (`T_WP3B_LOCKON.md` §8.5) |
| 4 | **missile count / cadence** | `FireInterval` **0.5 s** `0x098C` (Joker launcher; the 3 Batmobile launchers carry 16 fields and no `FireInterval`); `WeaponCoolDown` **20.0** `0x0830` | `w614` (burst **6 × 5 s**) and `w618` (`fire_rate` 0.5) | `burst_count` **@88** (fleet 1…6), `burst_cooldown` **@92**, `fire_rate` (dictionary) | **`missile_per_shot` 8, `burst_count` 1, `burst_cooldown` 0** (one pull, 8 projectiles) — the alternative, `burst_count` 8 × 0.5 s, is **outside the shipped 1…6** | muzzle pattern (6) + repeat nozzles; 20 s weapon cooldown has **no tune member** | decoded values; the 0.5 s spacing has no *within-action* member |
| 5 | **homing turn rate** | **none** — homing bool `0x0420`, `HomingDelay`, `AccelRate` all absent on the barrage projectile (only the *tracker* homes, delay 0.2 s) | `w614` (200/200, vehicle-mounted, guided) | `missile_turning_speed` **@24**; `missile_no_turning_time` **@32**; `missile_turning_speed_random` **@28** | **200**, `no_turning_time` **0**, random **0** | nothing — the value is the carrier | decoded (BmAK absence + JC3 value); unit (deg/s assumed) UNKNOWN |
| 6 | **speed** | **UNKNOWN** — `Projectile.Speed`, `Projectile.MaxSpeed`, `AccelRate` absent from every barrage instance; Joker sibling (same class) ships 500 / 1000 / 8000, EMP sibling max 7500 / accel 40000 | `w618_sportsmuscle_missile` (same chassis) | `velocity` / `max_speed` (type dictionary; `w618` = **360 m/s**, range 300) | **keep 360** — no BmAK number to copy, and the siblings' unit is not convertible | nothing | decoded JC3; BmAK value UNKNOWN |
| 7 | **damage** | `Projectile.Damage` **250.0** `0x02D8`; `DamageRadius` **0.0** `0x02DC`; `MomentumTransfer` **25000.0** `0x02E0`; type `Core.RDmgType_BatmobileMissileBarrage` `0x02C8` | `w618` | `damage` (type dictionary; `w618` = **1500**, impulse 350, AI 30) | **keep 1500 / impulse 350** — 250 has no unit bridge and copying it would make the barrage quieter than the car's other missiles | nothing | decoded both sides; **no damage-unit bridge** |

### 2.1 Adjacent launcher values (recorded so the table is not silently partial)

| BmAK field | offset | value | JC3 member | write |
|---|---|---:|---|---|
| `LockOnRange` | `0x0984` | **12000.0** | `AutoAimSettings.MaxAimDistance` **@60** (−1 unlimited in both presets; 750 on `w609`) | **−1** (keep unlimited — 12000's unit is UNKNOWN; 120 only if cm, and the earlier plan chose not to guess) |
| `RVehicleWeapon.LethalRange` | `0x0900` | 12000.0 | none (no lethal-range member in `WeaponTuning`) | declare; range stays `max_range` 300 (w618) |
| `WeaponCoolDown` | `0x0830` | 20.0 s | none (`fire_rate` is per-shot, `burst_cooldown` is within-action) | declare; the cooldown row is native or a timer |
| `MissileSockets` | `0x0A30` | array, 10 items (payload not decoded) | `SWeaponPoint` muzzle set | 6 muzzles (w501 pattern), 4 sockets unwired |
| `MissileNumberParameter` | `0x09CC` | `Ww_Parameters.BML_NumberOfTargets` | audio parameter only | no value to write |

---

## 3. The three rows that are not copies, and why

1. **Lock hold (row 1) — a member exists, its meaning does not.** `aim_timer_override` is the only
   root-level timer in `WeaponTuning` and 4.0 on the RPG class; nothing in the tune says it times a
   *lock* (`T_WP3B_LOCKON.md` §4.1: `AutoAimSettings`'s 22 members include no duration). The build
   writes **2.0** on the tune *and* a **2.0 s `STimerComponent`** on the launcher, so the hold survives
   either reading of the member. That is the lock-hold plan's P1, unchanged.
2. **Target count (row 3) — no member at all.** A burst is several missiles at one aim point
   (`w614` 6 × 5 s at `missile_per_shot` 1); a salvo split across 8 targets needs the fire call to take
   8 aim points. The build can write **8** into `missile_per_shot` and add the pattern; it cannot make
   the game *choose* 8 targets from data. That half stays UNKNOWN and is the reason the barrage's pilot
   card counts **markers** as well as missiles.
3. **Cone (row 2) — the value exists, the unit does not.** `AngleThresholdCurrentTarget` 0.15 cannot be
   compared with 40° until the unit is known: as turns it is **54°** (wider than BmAK's 40°), as radians
   **8.6°** (narrower). Writing **0.1111** turns is the only conversion with a defensible arithmetic
   (40/360), and it is wrong by 5× if the field is radians. So the row writes **nothing** and the 40° is
   a pilot comparison, not a build value — exactly the substitution `AGENTS.md` forbids.

---

## 4. What the build adds, itemised (only where no member carries the behaviour)

| addition | object / file | value | why it cannot be a tune member |
|---|---|---|---|
| lock-hold gate | `STimerComponent` on the launcher | **2.0 s** | tune timers' consumer is native and unnamed (row 1) |
| salvo seating | `SWeaponFirePattern` + 4 `SWeaponPoint` (2 exist: `MissileL`/`MissileR`) | **6 muzzles**, 8 missiles → 2 repeat | pattern objects are name + pointers, no count field (`lock-hold-salvo…` §1 P2) |
| per-target aim | none available | — | no target-count or aim-point-array member in any of the 103 tunes |
| lock markers | private `ui/hud.gfx` | 6 marker kinds + meter | 0 `CreatePoi(POI_TYPE_LOCK_ON_TARGET)` calls; the POI is painted natively (§4 of `T_WP3B_LOCKON.md`) |
| cooldown | none available | — | no weapon-cooldown member; `fire_rate` is per-shot |

No new weapon class, no component swap, and no `CRPGFireLeachWeapon` mount: the guidance is a tune
member, proven twice in the corpus (`w612` carries a Fire-Leech class with a *tracer* component;
`w621` binds the lock-on preset with turning speed 0 — `wp4-fire-leech.md` §3.3).

---

## 5. Pilot card — the barrage as a whole

> **Q-BARR-1** — Put **eight** hostiles inside the cone at 100–250 m, hold the lock, then fire once:
> within **2.4 s** of the lock the build must show **8 markers**, and after the press **8 missiles**
> must leave inside **1.0 s** of each other, at least **6** must strike **their own** target (not a
> neighbour's), and no missile may re-strike a target already destroyed.

| element | value | source |
|---|---|---|
| marker count | **8** | `MaxTargets` 8 (decoded) |
| hold before launch | **1.6–2.4 s** | 2.0 s ±20 % (the project's ratio tolerance), `MissileLockOnDuration` |
| launch spread | **≤1.0 s** for all 8 | design band: 2 muzzles repeat at most twice, no member spaces them |
| hits on own target | **≥6 of 8** | design band (a 360 m/s missile needs ≤0.7 s of flight at 250 m; the 200 turning rate has that long to correct) |
| cone | 8/8 acquired at 40°-equivalent; the 9th hostile outside the cone never gains a marker | 40° is a BmAK target, JC3's value is 0.15 of an unnamed unit |
| repeats | 3 runs, HUD **on** (markers are the count) and the timing read from the launch sound, not the marker | — |

**Pass** = all six clauses hold on the mean with no run outside a band. **Fail mapping:** fewer than 8
markers = the target-count bridge is absent (row 3, declare it); 8 markers but <8 launches =
`missile_per_shot` did not take (row 4); 8 launches but <6 own-target hits = the turning rate is too low
or the aim points are all the same point (row 5); no marker at all = the native POI link (UNKNOWN, not a
build fault); more than 1.0 s spread = `burst_cooldown` is being applied as the salvo interval.

---

## 6. UNKNOWNs, with the file that settles each

| # | UNKNOWN | settling file |
|---|---|---|
| U1 | what `aim_timer_override` @108 gates (a lock hold, a fire delay, or nothing) | `JustCause3.exe` `WeaponTuning` consumer (the 4.0 constant and its xrefs); Q-BARR-1's hold clause |
| U2 | the `AutoAim` angle unit (turns vs radians) | `w609`/`w612`/`w613` type dictionaries store bare floats with no unit metadata; `JustCause3.exe` AutoAim consumer; a cone-entry probe |
| U3 | the barrage projectile's speed / max speed / acceleration (absent from every instance) | `RBatmobileMissile` class defaults — `Default__RBatmobileMissile` in `BmGame.upk`; `Research/BatmobileGrab/WEAPONS.md` records instance absence only |
| U4 | `MaxTargetsPerLevel` `0x0A20`'s 1-item payload (could clamp 8) | `Batmobile_JokerMissile_Launcher`'s array body in `Playable_BatmobileJoker_SF` (`Tools/scripts/grab_weapons.py` decode of the array payload) |
| U5 | whether a salvo can hold several targets at once (8 markers ≠ 8 shots) | `JustCause3.exe` AutoAim/fire consumer; Q-BARR-1's marker clause |
| U6 | whether `0.5 s` `FireInterval` can be carried (no within-action interval member) | tune dictionary (`burst_cooldown` is the only interval) — a build attempt; else declared |
| U7 | whether a `CCar` slot can mount a `CMissileWeaponBase` with a private guided tune | `JustCause3.exe` weapon-class factory; `Research/JC3Grab/WEAPON_WIRING.jsonl` (no car binds a lock-on preset) |
| U8 | the damage-unit bridge (BmAK 250 vs JC3 1500) | no file; both are engine-internal scales — declared as "keep the JC3 donor", not converted |

---

## 7. Checks, limits, and the change

**Read for this card:** `Working/Translation/T_WP3B_LOCKON.md` (full), `lock-hold-salvo-closest-system-plan.md`
(full), `wp4-fire-leech.md` (full), `Research/BatmobileGrab/WEAPONS.md` §12 (`:1029-1040`, 16 identical
launcher fields), §13 (`:1080-1100`, Joker `MaxTargets` 8 / CDO 16, `FireInterval` 0.5,
`MaxTargetsPerLevel`, `MissileSockets`), the projectile sections at `:120-160` (EMP), `:400-500` (Joker
missile 500/1000/8000/250, then `Batmobile_Missile_Projectile`), `:1560-1615` (instance field table:
`Damage` 250 `0x02D8`, `DamageRadius` 0 `0x02DC`, `MomentumTransfer` 25000 `0x02E0`).

**Verified this session:** the barrage projectile's `Speed`/`MaxSpeed`/`AccelRate`/homing rows are
recorded **absent** in `WEAPONS.md` (the "absent from every instance" line at `:485`), and its three
present floats are 250 / 0 / 25000 — matching the instance tag dump (`objects.jsonl`, offsets 728/732/736).
The launcher's 16 fields are identical across all three vehicle packages (the report's own 48/0
comparison).

**Not run:** no tune decode, no `jc3adf dump`, no `t_wp3b.py --check`, no build, no game. Every number is
a quoted file value or an arithmetic step shown beside it (40/360 = 0.1111; 2.0 ±20 % = 1.6–2.4).

**Intended change:** add this one plan report. **File:**
`tmp/freebuff/reports/homing-weapon-tunes-to-barrage-values-plan.md` — the brief names this path.
**Revert:** delete it. Nothing else was touched (no tune, `.epe`, module, ring, ledger or backlog edit).
