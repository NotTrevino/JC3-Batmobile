# Lock hold and salvo — plan v2, with the two reticles separated

**Provenance / reversibility.** New file, `tmp/freebuff/reports/lock-hold-salvo-reticle-plan-v2.md`
= `E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/lock-hold-salvo-reticle-plan-v2.md`. Intended change:
rebuild every number of `lock-hold-salvo-closest-system-plan.md` against
`audit-lock-hold-salvo-and-fire-leech.md`, split the operator's two reticle observations into two
behaviours with the BmAK member that drives each, and restate the closest JC3 mechanism, the gap and a
one-session build step for each from `reticle-opt-in-build-plan.md`,
`lock-on-reticle-hud-link.md`, `Research/specs/B-24.md` and `B-25.md`. It is the correct file because
it is the requested output path and consumes those six documents. **The plan, the audit, both decoded
reports and all four build documents are read only.** **Revert = delete this file.**

Labels: **decoded** = read at the named file:line/offset; **derived** = arithmetic shown; **operator** =
the 2026-11-08 observation, which no file confirms or refutes; **UNKNOWN** = absent from the named
files, with the file or take that settles it.

---

## 0. Verdict summary

| item | count | what it is |
|---|---:|---|
| plan numbers checked | **34** | §2 BmAK values (9), §3 JC3 values (9), D1–D10, §4 leg rows (6) |
| audit verdicts carried | **22 claim rows** | 3 **OVERSTATED** (L6 salvo, L10 turning speed, L13 AutoAim copy), 3 **UNSUPPORTED / contradicted** (L2 `aim_timer_override`, L19 class move, L17 offsets), 4 verified only against the **carrier report** (L3, L4, L9, L21), 12 verified |
| corrected here | **11** | see §3 — five change a value or a composition, six change a label or a citation |
| **found by this rebuild, not in the audit** | **4** | `MaxTargets` 8 is the *Joker* instance, not the playable launcher (`WEAPONS.md:1081` vs `:1116`; the playable archetypes set no tag); `MaxAimDistance` should be **120**, not −1 (`LockOnRange` 12000 cm); the 2.0 s is declared on the **pursuit** launcher, so the plan's "2.0 s lock hold" is a different behaviour from the battle barrage; the lock-on preset's `AngleThresholdNewTarget` **0.12 turn = 43.2°** already brackets BmAK's 40° cone |
| the plan's central claim | **half right** | the 2.0 s duration exists and is decoded — but **not on the launcher the plan builds** and **not in any JC3 member** |

**The one-line correction.** `MissileLockOnDuration` 2.0 s belongs to **`RBatmobileEMPMissile`**, the
**pursuit-mode** missile launcher, which has a real acquisition state machine and a `LoseLockTime`;
the **battle-mode** `RBatmobileMissileLauncher` has **no duration member at all**. That is why the
operator sees an instant diamond in battle mode and a shrinking circle in pursuit mode — and it means
the plan's four legs mix two behaviours: the battle reticle is a *gate-only* system (no timer to
carry), the pursuit reticle is a *timed fill* (no JC3 member to carry the timer).

---

## 1. The two reticles, separated

| | **battle mode — instant orange diamond** | **pursuit mode — diamond with edge centres missing + shrinking circle** |
|---|---|---|
| BmAK HUD module | `HudModuleTargets` (the boxes) | `HudModuleBespokeLocalRadar` (the meter) |
| elements (`HUD.md:218-219`) | `batmobile_lockon`, `missile_lockon_square_anim`, `missile_border_anim`, `batmobile_aim`, `VehicleMissileTarget` + `_bomb` / `_emp` / `_friend` / `_multi` / `Invalid` (**6 kinds**) | `LockonMeter`, `lockonAndHealthMeter`, `lockonStatusTextContainer` |
| setters | `UC_SetBatmobileWeapon(primary, bool)`, `UC_SetBatmobileWeaponHit`, `UC_SetBatmobileWeaponFailure` | `UC_SetLockonValue(value, threshold)`, `UC_SetStationaryLockonValue`, `UC_UpdateTargetPosition(angle, distance, bearing, dots)`, `UC_SetHealthValue(value, instant)` |
| **BmAK member that drives it** | **none — that is the point.** `RBatmobileMissileLauncher` has `LockOnAngle` 0x0980 **40.0**, `LockOnRange` 0x0984 **12000.0 (120 m)**, `MaxTargets` 0x095C, `NthTarget` 0x0A00, `InitialFireDelay`, `FireInterval` 0x098C **0.5**, `CooldownDelay` — and **no duration field** (`bm-lock-duration-and-cone.md` §2) | **`RBatmobileEMPMissile.MissileLockOnDuration` 2.0 s @0x0A00** (civilian **1.0** @0x0A04), fed to a continuous value; accumulator `LockOnTime` @0x09EC (unserialised), state `bTryingToAcquireNewTarget` @0xA30, drop `LoseLockTime` @0xA6C, `bInstantFire` **true** after lock |
| why it looks the way the operator describes | "appears at once" is **the absence of a timer**, not a zero-length one: there is no member to slow the acquisition down | the meter is a **0..1 value** (`UC_SetLockonValue` writes `Bar.Element.scaleX`; the second argument is a *threshold*, 0.3 in the demo, that picks display state 0/1/2). A 0→1 ramp over 2.0 s **is** a shrinking circle |
| what the files prove | the *gates* (40°, 120 m) and the *absence* of a duration — both decoded | the duration, the accumulator, the acquisition state and the separate lose-lock path — all decoded on the pursuit class |
| what only the operator supplies | the **orange**, the **diamond shape**, and "instant" as an appearance | the **geometry** ("middle of each edge missing") and that the circle **is** the 2.0 s fill rather than a hold before launch |

**Why the split is real, not a guess.** The two BmAK HUD paths are distinct modules with distinct
setters, and only one of them has a meter (`bm-lock-duration-and-cone.md` §4). On the weapon side the
split is equally clean: the battle launcher's members are gates and counters; the pursuit launcher's
super is `RPursuitModeMissileLauncher`, its anim node is `"PursuitMissileAnim"`, and it alone carries
`MissileLockOnDuration` / `CivilianMissileLockOnDuration`. So **three** facts point the same way: box
path + no duration on the battle launcher + a duration on the pursuit launcher.

---

## 2. Is `MissileLockOnDuration` 2.0 s the circle? — decided as far as the files allow

| candidate | for | against | status |
|---|---|---|---|
| **the pursuit lock's acquisition time, i.e. the circle's fill** | declared on the pursuit class; the class has `bTryingToAcquireNewTarget`, `LockOnTarget`/`LastLockTarget` and a separate `LoseLockTime`; a continuous proportion is proved to exist on the BmAK side by `LockOnBeepProportionParam` (`Ww_Parameters.BML_AP_Rocket_Lock`), which an audio RTPC can only consume from a 0..1 progress value; the battle launcher's *absence* of a timer matches the operator's "battle is instant" | **no file names the HUD call the field feeds**; `poi.as` sets `m_HasProgressBar = false` for type 21 | **supported as the pursuit acquisition time; as *the* circle driver it is the strongest model and still `UNKNOWN`** |
| a hold before launch | — | `bInstantFire` is **true** (`RPursuitModeMissileLauncher`, 0x09A0), so nothing waits after the lock completes | **not supported** |
| a re-acquire time | `bTryingToAcquireNewTarget` exists | a re-acquire duration would sit beside `LoseLockTime` (0xA6C), which is the dedicated member for it | **not supported** |
| the battle barrage's lock | — | not declared on `RBatmobileMissileLauncher`; its members are gates, counts and cadence | **refuted** |
| **`LockOnTime` 0x09EC is the accumulator that runs against it** | it is the only unserialised float on the class, directly under the duration pair | value is runtime-only, so no export holds it | **derived, high confidence** — a tick advancing `LockOnTime` toward 2.0 is what a "shrink" looks like |

**Consequence for the plan.** The 2.0 s is a **pursuit** number and a **native acquisition** number.
Carrying it as JC3's "lock hold" on `aim_timer_override` is wrong twice: the member is on the other
launcher, and JC3 has no duration member to receive it (audit L2; `B-24` §SUMMARY). The correct
restatement is: **2.0 s is the pursuit circle's fill time; there is no JC3 member to hold it, so the
fill must be authored in the private movie and nothing in the weapon data can gate on it.**

---

## 3. Every plan number, audit verdict, corrected value

### 3.1 BmAK side (plan §2)

| # | plan :line | old value | audit verdict | corrected value | label | file:line |
|---|---|---|---|---:|---|---|
| W1 | :33, :34, §1 P1 | `MissileLockOnDuration` **2.0** @0x0A00, civilian 1.0 @0x0A04, "BmAK lock hold" | **VERIFIED** as a value | same numbers, **re-scoped: declared on `RBatmobileEMPMissile` (pursuit), which is the circle; the battle launcher has no duration** | decoded | `WEAPONS.md:839-840`; `bm-lock-duration-and-cone.md` §1-§2 |
| W2 | :39, §2 | `MaxTargets` **8** @0x095C on `RBatmobileMissileLauncher` | **VERIFIED** for the value | **8 is the `Batmobile_JokerMissile_Launcher` instance**; the **Joker class default is 16**; the three playable launchers **set no tag**, so the playable/ battle value is **UNKNOWN** | decoded / UNKNOWN | `WEAPONS.md:1081` (8), `:1116` (16); archetype tag absent at 0x95C in `objects.jsonl:5209`, `:14150`, `:19641` |
| W3 | :44 | `LockOnAngle` **40.0** @0x0980 | verified (not in the audit) | **40.0**, unit **degrees (derived)** | decoded | `WEAPONS.md:1028`; `objects.jsonl:5209` |
| W4 | :45 | `LockOnRange` **12000.0** @0x0984, unit UNKNOWN | verified (not in the audit) | **12000 cm = 120 m** — `WEAPONS.md:16` declares positions in cm, so the unit is **decoded, not UNKNOWN** | decoded + derived | `WEAPONS.md:16`, `:1029` |
| W5 | :40 | `MaxTargetsPerLevel` @0x0A20, array 1 item, payload not decoded | verified | same, **still UNKNOWN** (a per-level cap could clamp any number) | UNKNOWN | `WEAPONS.md:1087` |
| W6 | :41 | `MissileSockets` @0x0A30, 10 items | verified | same | decoded | `WEAPONS.md` §13 |
| W7 | :46 | `FireInterval` **0.5 s** @0x098C | **UNSOURCED offset**, value verified | value **0.5**; offset must cite `WEAPONS.md` §13 (**Joker** launcher) — and it is the only cadence member, so it survives the salvo rework as the 0.5 s per-shot gate | decoded | `WEAPONS.md` §13; wp4 §3.1 (`w618 fire_rate` 0.5) |
| W8 | :47 | `MissileNumberParameter` @0x09CC = `Ww_Parameters.BML_NumberOfTargets` | verified | same — and note it is an **audio** parameter, evidence that BmAK sends the **number of targets** to audio, i.e. a multi-lock exists at runtime even though no comparator is stored | decoded | `WEAPONS.md` §12; `bm-lock-target-sort-key.md` §2 |
| W9 | — | *(the operator's "crosshair-nearest first")* | not in the plan | **no sort key exists**: `LockOnAngle`/`LockOnRange` are **admission gates**, `MaxTargets` is a **cap**, `NthTarget` **indexes**, `CurrentTargets` 0x0960 is a bare `Actor[]` whose order no field writes; the only health-adjacent logic is `CheckForDeadThugs`, an alive/dead **cull** on the Joker subclass | **UNKNOWN** | `bm-lock-target-sort-key.md` verdict + §3-§4 |

### 3.2 Derived values (plan §5, §4 D1-D10)

| # | plan :line | old value | audit verdict | corrected value | label | why |
|---|---|---:|---|---:|---|---|
| D1 | :150 | **8** — `MaxTargets` 8 → `missile_per_shot` 8 | **OVERSTATED** (L6) | **8 separate slot-able missile weapons at one aim point**; `missile_per_shot` stays **1** on each | declared composition, **not a 1:1 carry** | `missile_per_shot` counts **projectiles per trigger pull**, not targets; `B-24` §3.2 prescribes 8 weapons, not 8-on-one |
| D2 | :151 | **1.33** = 8 / 6 muzzles | moot | **drop** — with 8 weapons there are no repeat muzzles | — | the 6-muzzle pattern was the vehicle for D1; both go |
| D3 | :152 | **3.5 s** = 7 × 0.5 s | arithmetic correct, premise changed | **3.5 s** if the launcher still sequences 8 shots at `FireInterval` 0.5 s; **4.0 s** if each weapon fires on its own `fire_rate` | derived, **conditional** | the arithmetic is unchanged; what changed is that the 8 are 8 weapons |
| D4 | :153 | **10** sockets, 6 used, 4 unwired | moot | **10 decoded sockets; 8 weapons** — 2 stay unwired | decoded + build choice | follows D1 |
| D5 | :157 | **2.0 s** → `aim_timer_override` 2.0 **and** `STimerComponent` 2.0, "derived 1:1" | **UNSUPPORTED / contradicted** (L2) | **the 2.0 s has no JC3 member.** It is re-filed as the **pursuit circle's authored fill time**; `aim_timer_override` is an **RPG-class aim timer, not lock-gated**, and may be written only as a labelled secondary experiment | **invented gate**, not a carry | `AutoAimSettings` = 22 members, none a duration; `T_WP3B_LOCKON.md` §4.1; carrier §4.1 |
| D6 | :158 | **1.6–2.4 s** hold band (±20 %) | follows D5 | **1.8–2.2 s** for the circle's 0→1 fill (±10 % of 2.0, a visual timing band); **0.9–1.1 s** for the civilian 1.0 s. Rename to *circle fill* | declared band | ±20 % was borrowed from ARM-2's damage band; a HUD timing band does not inherit it |
| D7 | :159 | **0.6 s** = 90° at 150 units/s | arithmetic fine, donor wrong (L10) | **0.6 s** only for a **`w609`-guided** missile (150); the **Fire Leech is 300** → **0.3 s**; and the Fire Leech's own projectile turning speed is UNKNOWN, so this is a donor choice | derived, conditional | wp4 §2.1/§3.3; `T_WP3B_LOCKON.md` §2.1 |
| D8 | :160 | **8** (markers) | follows D1 | **8 markers** only if 8 targets are held at once — **UNKNOWN** (L22); the safe count is whatever `POI` instances the movie can draw | derived, conditional | `B-24`; `bm-lock-duration-and-cone.md` (pursuit holds **1**, battle count UNKNOWN) |
| D9 | :161 | **6** muzzles | moot | **drop** | — | D1 |
| D10 | :162 | cone **40°** vs JC3 0.15, unit UNKNOWN | **VERIFIED** | **40.0°** BmAK; JC3 `AngleThresholdNewTarget` **0.12** / `CurrentTarget` **0.15** — **if the unit is a turn, 0.12 = 43.2° and 0.15 = 54°**, i.e. the shipped preset already brackets 40° within 8 % | decoded + derived, unit UNKNOWN | `WEAPONS.md:1028`; `reticle-opt-in-build-plan.md` §2.1 |

### 3.3 JC3 side and composition rows (plan §3, §4)

| # | plan row | old | audit verdict | corrected | label | source |
|---|---|---|---|---|---|---|
| J1 | `aim_timer_override` @108 | 4.0 → 2.0, "the only root-level timer" | **UNSUPPORTED** (L2), offset verified only against the carrier report (L3) | **offset 108 and the distribution (8 × 4.0, 1 × 0.001, 65 × −1) are real** — but the member is an RPG aim timer, **not a lock hold**. Write 2.0 only as a labelled probe; do not call it a carry | decoded, wrong function | carrier §4.1; `wp4` §2.2 |
| J2 | `STimerComponent` 2.0 on the launcher | 2.0 s gate from `w501`'s timers (1 / 2 / 6 / 0.6 / 0.01 / 20 s) | verified only against the carrier report (L4) | keep **as the only honest gate** — an entity timer the graph can read; 2.0 is inside the shipped band. Re-cite `lock-hold-and-salvo-carrier.md` §8, not wp4/T-WP3b | decoded (carrier) | carrier §8, `w501_turret_sam_v2.epe` |
| J3 | `missile_per_shot` @44 = 8 | 1 → 8, "8 missiles, one trigger" | **OVERSTATED** (L6); value 1 verified (L7), offset/u8 verified (L8) | **stays 1**; the salvo is **8 weapons** | decoded, composition changed | `T_WP3B_LOCKON.md` §1-§2; `B-24` §3.2 |
| J4 | 6-muzzle `SWeaponFirePattern` from `w501` | 6 muzzles, 8 = 6 + 2 repeat | verified only against the carrier report (L9), **moot** | **drop the pattern work**; if a pattern is ever wanted, `w501`'s 6 muzzles are real but the object has **name + pointers only, no count field** | decoded (carrier) | carrier §5, §8 |
| J5 | carrier class → `CMissileWeaponBase` | swap the missile off `CBulletWeaponBase` | **UNSUPPORTED / contradicted** (L19) | **one source says tune-only** (`wp4` §3.3: "change no class and add no component"), **one says the missile block lives only on a missile carrier** (`lock-on-reticle-hud-link.md` §5: a `CBulletWeaponBase` has no `missile_base_tuning` block). The two disagree; the offline check decides (T2/T3 below) | **contradiction, open** | wp4 §3.3 vs `lock-on-reticle-hud-link.md` §5 |
| J6 | `missile_turning_speed` @24 = **150** | "Fire Leech guided flight" | **OVERSTATED** (L10) | 150 is **`w609`**; the Fire Leech is **300**; `w618` is **0**. Rename the leg "w609-guided", or write 300 | decoded | `T_WP3B_LOCKON.md` §2.1; wp4 §2.1/§3.3 |
| J7 | Fire Leech AutoAim copied wholesale | 0.12 / 0.15 / Cutoff 100 / `MaxAim` −1 / `MinAim` 15 / `CanTargetVehicles` 1, "all 6 contexts identical" | **OVERSTATED** (L13) | **do not copy wholesale**: the source tune is the only one with `CanTargetCharacters` **1** and `CanTargetRigidObjects` **0**. Corrected profile: **characters 0, vehicles 1, rigid 1**, `AngleThresholdNewTarget` 0.12, `CurrentTarget` 0.15, `MaxAimDistance` **120**, `MinAimDistance` 15, `StickyAimStrength` 0 | decoded values, **edited profile** | wp4 §2.3/§3.4; `reticle-opt-in-build-plan.md` §2.1 |
| J8 | `MaxAimDistance` −1 (unlimited) | "750 m would clip a 12000-unit range whose unit is not decoded" | not in the audit | **120** — the unit *is* decoded (cm), so 12000 = 120 m and the range is writable exactly. Keep the preset's 750 rejected for the same reason: it is 6× the BmAK reach | decoded + derived | `WEAPONS.md:16`, `:1029`; `bm-lock-duration-and-cone.md` §6 |
| J9 | lock range / cone carried as "−1 and 40°" | — | not in the audit | **120 m / 40° (43.2° achievable)** | decoded + derived | J8, D10 |
| J10 | `burst_count` / `burst_cooldown` @88 / @92 | 0 / 0 | **UNSOURCED** (L16) | values 0/0 are harmless; **the offsets are not in either named source** (T-WP3b's table ends at 68) — cite `WEAPONS.md` §13 or drop | decoded / unsourced offset | `T_WP3B_LOCKON.md` §2 |
| J11 | `MaxTargetsPerLevel` / `MissileSockets` / `MissileNumberParameter` offsets | 0x0A20 / 0x0A30 / 0x09CC | **UNSOURCED in the named files** (L17) | values and offsets real; **attribute them to `WEAPONS.md` §12-§13** | decoded | `WEAPONS.md` §12-§13 |
| J12 | `FireInterval` 0x098C | 0.5 s | unsourced offset (L18) | 0.5 s verified via `w618` `fire_rate`; offset from `WEAPONS.md` §13 | decoded | J7 above |
| J13 | "8 markers need 8 held targets" | UNKNOWN U3 | **VERIFIED as UNKNOWN** (L22) | unchanged, and now sharper: pursuit holds **1** (`LockOnTarget` 0x09A4, `LastLockTarget` 0x09AC); the **battle** hold count is UNKNOWN because the base CDO is absent | UNKNOWN | `bm-lock-duration-and-cone.md` §1 |
| J14 | reticle = `POI_TYPE_LOCK_ON_TARGET` 21, 1.5 s, 0 `CreatePoi` | — | **VERIFIED** (L15) | unchanged: **21**, `LOCK_ON_TARGET_ROTATION_TIME` **1.5 s**, **0** creators in 260 scripts, `m_HasProgressBar = false`, `MCI_missile_locked` blink **0.5 s** | decoded | `lock-on-reticle-hud-link.md` §1; `B-25` §1 |
| J15 | `w618` turning speed **0** | "today's missile does not home" | **VERIFIED** (L20) | unchanged | decoded | `T_WP3B_LOCKON.md` §2.1 |
| J16 | "8 from 6 muzzles is legal" | inferred from `w123`'s 6-per-shot | partially supported (L9) | **still true as a fact** (`w123` fires 6 from 1 muzzle) but **no longer needed** — the salvo is 8 weapons | decoded precedent | carrier §7 |

---

## 4. Closest JC3 mechanism, per behaviour

### 4.1 Battle instant diamond

**Mechanism: the data opt-in.** Everything the battle reticle needs on the data side is one string and
one carrier, and the car's own donor already proves the string is legal:

| layer | member path | value | source |
|---|---|---|---|
| acquisition | weapon object `props["id:6D4C8277"]` (`autoaim_tuning_file`) on the missile component | `autoaim_vehicle_lockon_missile.wtune` (today the build writes `…no_lockon_missile`) | `lock-on-reticle-hud-link.md` §3-§4 |
| where it must be written | **both** carriers: the weapon bundle `.epe` **and** the vehicle graph's override object | vanilla disagrees on 4 ids including `w618` (bundle = no-lockon, slot = lock-on); which wins is UNKNOWN | same §3 |
| cone | `OnFoot.AngleThresholdNewTarget` **0.12** / `CurrentTarget` **0.15** (turns → 43.2° / 54°) | versus **0.05 / 0.12** in the no-lockon preset — the only 15-row difference | `reticle-opt-in-build-plan.md` §2.1 |
| range | `OnFoot.MaxAimDistance` **120**, `MinAimDistance` **15** | 120 m = BmAK's 12000 cm | J8 |
| homing | `missile_turning_speed` @24 > 0 (150 `w609` / 300 Fire Leech) | **0** today | J6 |
| the drawn box | `POI_TYPE_LOCK_ON_TARGET` 21, one clip, **0 creators** in the movie | art is authored; the marker cannot be opted into by data | `B-25` §SUMMARY |

**Gap.** The movie draws **one** rotating clip with **no kind argument** (`CreatePoi(type,
use_progress_bar, is_minor, label)` — no colour, size or kind); BmAK draws **six** kinds plus a
separate `batmobile_aim` box. Neither the box geometry nor the orange exists in any decoded file.
And the *trigger* — native code creating the type-21 POI — is the one link no data file contains.

**Build step, one session.** *Battle leg — data opt-in only.*

| field | value |
|---|---|
| tree | `Builds/bm-RC5-lock/`, from the current missile build (no HUD work in this session) |
| files | the weapon bundle `.epe` (missile component) **and** the vehicle graph's weapon override object |
| member | `props["id:6D4C8277"]` = **`.../autoaim_vehicle_lockon_missile.wtune`** on both; plus the private tune's `MaxAimDistance` **120** / `MinAimDistance` **15** / `AngleThresholdNewTarget` **0.12** / `CurrentTarget` **0.15** / `CanTargetCharacters` **0** / `CanTargetVehicles` **1** / `CanTargetRigidObjects` **1** / `StickyAimStrength` **0** |
| proof (offline, no game) | grep the built `.epe` for `autoaim_vehicle_lockon_missile` → **≥1** hit and **0** `no_lockon` on the missile; decode the private tune → the values above; component `id:6D4C8277` equals vanilla `w618` on `v0300` (T5) |
| deliberately **not** in this session | the carrier-class question (J5 — contradictory sources), turning speed, the 8 weapons, any movie edit |
| why one session | one string on two carriers + one tune's 8 fields — the class swap and the salvo are separate cards, and J5 has to be measured before either |

### 4.2 Pursuit shrinking circle

**Mechanism: the radar meter, driven by an authored fill.** JC3's closest element is not a POI at all —
it is `LockonMeter` / `lockonAndHealthMeter` on the **radar** module, fed by
`UC_SetLockonValue(value, threshold)` (value → `Bar.Element.scaleX`, threshold 0.3 → display state
0/1/2) and `UC_SetHealthValue(value, instant)` on the same bar.

| layer | JC3 element | value | source |
|---|---|---|---|
| the meter | `LockonMeter`, `lockonAndHealthMeter`, `lockonStatusTextContainer` | present in the shipped movie | `lock-on-reticle-hud-link.md` §6 |
| the setter | `UC_SetLockonValue(value:Number, threshold:Number)` | `value` is continuous 0..1; `threshold` 0.3 | `reticle-opt-in-build-plan.md` §3 |
| the timeline | 2.0 s fill = **60 frames** at 30 fps (`TickDeltaTime` 0.033 → **≈60 ticks**) | 2.0 s → 60; 1.5 s → 45; 0.25 s square-in → 7.5 | same §3, `HUD_SPEC.json` bmak constants |
| civilian variant | **1.0 s** = 30 frames | from `CivilianMissileLockOnDuration` | `bm-lock-duration-and-cone.md` §1 |
| the POI that marks the target | type **21**, 1.5 s rotation, `m_HasProgressBar = false` | the circle is **not** the POI's progress bar (it has none) — it is the radar meter | `B-25` §1 |
| the trigger for the fill | `B-25` step 1: a tracker graph in the `mm130_tracker.gdc` pattern creates the POI on the acquired target from a script-side re-check of the same 120 m / 0.12-turn cone | precedent decoded | `B-25` §2 |

**Gap.** The duration has **no data carrier** (22 `AutoAimSettings` members, none a timer; no
`MissileWeaponTuningBase` duration except projectile-side `missile_detonation_time` −1 and
`missile_no_turning_time` 0), and the meter's own writer is native: `UC_SetLockonValue` has no
in-movie caller, so either native drives it or nothing does. A graph→movie call is **not decoded**. So
the fill can be authored, but the *authorship* has to be decided first: if native also writes the
property, an authored tween will fight it (two writers, one `scaleX`).

**Build step, one session.** *Pursuit leg — the authored fill.*

| field | value |
|---|---|
| tree | `Builds/bm-RC5-pursuit/` |
| files | private `ui/hud.gfx` (patch copy, 386,281 B, 260 scripts, 1280×720) + one tracker graph cloned from `graphs/mission/mm130/mm130_tracker.gdc` |
| members / elements | `hud_code/poi.as` case 21: add the acquire timeline on `LockonMeter.Bar.Element.scaleX`, **0→1 over 60 frames (2.0 s)**, then the shipped `TweenRotation(ret, 1.5, 360, TM_LINEAR, TR_LOOP)`; civilian branch **30 frames (1.0 s)**; threshold unchanged **0.3** |
| graph | create `POI_TYPE_LOCK_ON_TARGET` (21) on the target the same 120 m / 0.12-turn cone admits; clear on fire and on cone exit; banner `MCI_missile_locked` **0.5 s** |
| proof (offline) | recompile keeps **260** scripts and 1280×720; `poi.as` still has **0** native-style `CreatePoi(21)` outside the authored call; the meter tween is the only writer of `scaleX` in the package (grep); the graph parses and references type 21 |
| deliberately **not** in this session | the six-kind box family, the aim box, hit/failure clips, the 5 audio events, the 8-weapon salvo |
| why one session | one setter, one timeline, one graph — and it is the only leg whose *behaviour* (a visible shrink over 2.0 s) can be judged without the box art |

**Why the circle is not the POI's own bar.** `m_HasProgressBar = false` is set for type 21, so
`CreatePoi(21, true, …)` would draw nothing; the shrink the operator describes is on the radar meter,
which is the module that differs between the two modes. That is also why the battle diamond can be
instant while the pursuit circle is timed **in the same movie**: they are different instruments.

---

## 5. What only a player take can confirm

| # | claim | why no file settles it | the take |
|---|---|---|---|
| P1 | the shrinking circle **is** `MissileLockOnDuration` 2.0 s | no file names the field's consumer; the accumulator (`LockOnTime` 0x09EC) is runtime-only | time the circle from first frame to full: **1.8–2.2 s**; a civilian target **0.9–1.1 s** |
| P2 | the battle diamond appears **instantly** | absence of a duration member proves no timer *exists*, not how the frame renders | press the trigger on a target already inside the cone; marker on the **same or next frame** (≤2 frames, ≤0.066 s) |
| P3 | the diamond's **orange** colour and the "missing edge centres" geometry | `HUD.md` / `HUD_SPEC.json` carry clip **names** only, no geometry, no colour; no clip is named for the cut-edge diamond | author against a screenshot; colour is an operator fact until sampled from the `Image_I1*.tga` atlases |
| P4 | barrage picks **crosshair-nearest** first | no comparator is stored; gates (40°, 120 m) only admit candidates; `CurrentTargets` 0x0960 order is written by native code | log the order of `CurrentTargets` at acquisition for candidates at varied health, distance and off-axis angle; **health-first is refuted by data, angle-first is permitted by it** |
| P5 | eight markers appear at once | battle hold count is UNKNOWN (base CDO absent); pursuit holds **1** | put 9 hostiles in the cone; count markers (expect 8, and a 9th never gains one) |
| P6 | which preset wins — bundle or vehicle graph | vanilla disagrees on 4 ids incl. `w618`; the merge is native | with both written, fire at a hostile inside 43° at ≤120 m: a marker proves the write took |
| P7 | a mod weapon gets a native type-21 POI at all | 0 creators in the movie; the entity→HUD call is native | disable the authored `CreatePoi` and fire; if no box appears, the link is native-only |
| P8 | `aim_timer_override` 2.0 does anything | the member is real, the function is an RPG aim timer | only worth a probe after P1/P2; if nothing changes, close it as wrong-function |

---

## 6. Limits

* **No original edited.** The plan, the audit, `bm-lock-duration-and-cone.md`,
  `bm-lock-target-sort-key.md`, `reticle-opt-in-build-plan.md`,
  `lock-on-reticle-hud-link.md`, `B-24.md` and `B-25.md` are read only. Revert = delete this file.
* **Static reads only.** No game launched, no archive, tune, `.epe` or `.gfx` written. The two reticle
  shapes remain operator observations; the files confirm the *split* (box path vs meter path, battle
  launcher without a duration vs pursuit launcher with one), not the geometry or the colour.
* **One contradiction is left open on purpose** (J5): `wp4` §3.3 says guidance is a tune member and the
  class must not change; `lock-on-reticle-hud-link.md` §5 says a `CBulletWeaponBase` has no
  `missile_base_tuning` block, so the block has nowhere to live. Neither is contradicted by a third
  file, so the v2 does not pick a winner — the T2/T3 decode of the built component decides it.
* **`MaxTargets` is not 8 for the launcher the plan builds.** 8 is the Joker *instance*; 16 is the
  Joker *class default*; the three playable launchers set nothing. Any salvo count of 8 is therefore a
  **build choice**, and the operator's observed barrage count is the only evidence for it.
* **The 2.0 s is not a "hold".** Every reading that survives says *acquisition*; `bInstantFire` true
  removes the post-lock wait. The plan's "hold" wording should retire with its `aim_timer_override`
  leg.
