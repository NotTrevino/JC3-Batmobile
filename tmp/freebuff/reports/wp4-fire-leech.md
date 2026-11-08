# T-WP4 — the Fire Leech as the lock-on carrier, and the approved split

Lane 8013, 2026-11-06. Operator lead: JC3's Fire Leech (justcause.fandom.com/wiki/Fire_Leech)
"has a lock-on HUD and heat-seeks after firing". This report finds it in `Research/JC3Grab`,
decodes its lock-on and homing members, compares them member by member with the w618 missile tune
and with the Batmobile's BmAK missile, states whether it can carry the lock-on missile, and records
the `T-WP4` split the operator approved.

Labels: **decoded** = read at the archive entry and offset named; **derived** = arithmetic shown;
**UNKNOWN** = searched in the named files and not present, with what would settle it. No game was
launched (test ban), and nothing outside `tmp/freebuff/reports/` was edited by this brief.

---

## 0. Answer in one paragraph

The Fire Leech is **`w143_rpg_fire_leach`**, a two-handed RPG in the decoded corpus, and it is the
fleet's best *guided-flight* donor: `missile_turning_speed` **300** (tied for the highest in the
fleet with `w612`), plus its own `AutoAim` tune whose acquisition cone is the same 0.12 / 0.15 as the
fleet's lock-on preset. So it **can carry the lock-on missile's guided flight and its target
acquisition** — both are ordinary data members and both are decoded here. It **cannot** carry what
BmAK's missile behaviour needs beyond that: the 2.0 s lock hold has **no member anywhere in JC3's
weapon data** (`T_WP3B_LOCKON.md` §4.1), the 8-target salvo has **no member either** (`missile_per_shot`
is 1 and no tune names a target count), and the lock-on reticle's entity→HUD link is **native,
UNKNOWN**. There is also a bonus fact that makes the donor choice cheaper than expected: **w618
already ships the Fire Leech's projectile mesh** — its weapon entity's model property points into
`jc_weapons/02_two_handed/w143_rpg_fire_leach/`.

---

## 1. Where the Fire Leech is, decoded

`decoded` — `Research/JC3Grab/INDEX.jsonl`, four entries under one directory, all in
`patch_win64/game1` (the patch copy wins; the `.ee` bundle sits in `archives_win64/game12`):

| path | offset | size | what it is |
|---|---|---|---|
| `editor/entities/jc_weapons/02_two_handed/w143_rpg_fire_leach/w143_rpg_fire_leach.wtunec` | 440494080 | 14238 | the tune, instance `w143_rpg_fire_leach.wtune`, class `WeaponTuning` |
| `editor/entities/jc_weapons/02_two_handed/w143_rpg_fire_leach/autoaim_w143_rpg_fire_leach.wtunec` | 440471552 | 2213 | the aim/lock block, instance `autoaim_rpg.wtune`, class `AutoAim` |
| `editor/entities/jc_weapons/02_two_handed/w143_rpg_fire_leach/w143_rpg_fire_leach.epe` | 440481792 | 11472 | the entity graph |
| `editor/entities/jc_weapons/02_two_handed/w143_rpg_fire_leach/w143_rpg_fire_leach.ee` | 125546496 (base) | 1450048 | the bundle (`.ee.toc` 4830 B) |

Two things to read off that directory name before any number: the Fire Leech is an **infantry,
two-handed** weapon (`jc_weapons/02_two_handed/`), not a vehicle weapon, so **no `CCar` binds it**
and mounting it on the Batmobile has no chassis precedent. It is, however, a plain `WeaponTuning` /
`AutoAim` pair — the same classes the vehicle missiles use — so its *values* transplant without a
class change (§3.3).

`decoded` — the wiki lead is directionally right about the two mechanisms, and both have a member:

* **"heat-seeks after firing"** = `missile_base_tuning.missile_turning_speed` (offset 24 of
  `MissileWeaponTuningBase`, `T_WP3B_LOCKON.md` §2). Value **300 / 300** (player / AI). There is
  **no heat member**: the whole type dictionary of `w143` contains no `heat`, `temperature` or
  `cool` name, and `missile_turning_speed` is the only steering member. "Heat-seeking" is the
  behaviour's *name*, not a field.
* **"lock-on HUD"** = the `AutoAim` tune above (acquisition) plus the HUD's
  `POI_TYPE_LOCK_ON_TARGET = 21` reticle (`Research/JC3Grab/JC3_HUD_WEAPONS.md` §5). The reticle
  exists in the Flash movie; **0 scripts create it** and the entity→HUD call is native
  (`UNKNOWN`) — same conclusion as `T_WP3B_LOCKON.md` §4 and §8.1, unchanged by this weapon.

---

## 2. The Fire Leech's lock-on and homing members, one by one

### 2.1 Homing block — `w143_rpg_fire_leach.wtune`, `missile_weapon[0]`

`decoded`, instance size 840 B, both `tuning` and `ai_tuning` instances printed:

| member | player | AI | meaning |
|---|---|---|---|
| `missile_turning_speed` | 300.0 | 300.0 | steering rate; **0 would be unguided** |
| `missile_turning_speed_random` | 60.0 | 60.0 | jitter added to the above |
| `missile_no_turning_time` | 0.0 | 0.0 | no steering for N s after launch - none |
| `missile_acceleration` | 30 → 65 | 10 → 25 | accel curve values (m/s²) |
| `missile_acceleration_time` | 0.2 → 10.0 | 0.2 → 10.0 | curve times (s) |
| `missile_acceleration_random` | 2 → 5 | 2 → 5 | jitter on the curve |
| `missile_loose_lock_distance` | 0.0 | 0.0 | lock is never let go by distance |
| `missile_detonation_time` | -1.0 | -1.0 | no timed self-destruct |
| `detonate_on_impact` | 1 | 1 | impact fuze |
| `missile_per_shot` | 1 | 1 | one missile per trigger pull |
| `gravity` | -9.82 | -9.82 | gravity on the projectile |
| `meters_times_speed_in_front_of_target` | 0.0 | 0.0 | no lead computation |
| `meters_proximity_self_detonate` | 0.0 | 0.0 | no proximity fuze |
| `random_detonation_offset` | 0.0 | 0.0 | no detonation jitter |

So the guidance is **pure pursuit at 300 deg/s (unit per `T_WP3B_LOCKON.md` §4.2's open unit
question) with 60 of jitter, full acceleration from 0.2 s, no loose-lock release, no lead** — a
close-range, hard-turning missile. `derived`: with `max_range` 1000 m and `velocity` 30 m/s the
projectile's own lifetime budget is ~33 s, far longer than the 10 s acceleration window, so the
curve is not range-limited in practice.

### 2.2 Fire block — same instance

`decoded`: `damage` **30** (player and AI), `impulse` 10, `vehicle_damage_factor` **0.5**,
`object_damage_factor` 1.0, `velocity` **30 m/s**, `max_range` **1000 m**, `fire_rate` **1.0**,
`fire_rate_level_2` 0.12, `magazine_size` **1**, `burst_count` 0, `fully_automatic` 0,
`aim_timer_override` 4.0, scatter all 0, recoil pitch 3→5, `unlimited_ammo` 0.

These are RPG numbers, not Batmobile numbers: **1/50th of w618's damage and 1/12th of its velocity**.
A copy of the Fire Leech tune would produce a slow 30-damage rocket (§3.3 says what to copy instead).

### 2.3 Lock-on block — `autoaim_w143_rpg_fire_leach.wtunec`

`decoded`, instance `autoaim_rpg.wtune`, class `AutoAim`, 528 B this instance (the two shared
`autoaim_vehicle_*` presets are 2216 B = 6 × 368-byte contexts; this one is 6 × 88 B, i.e. the
OnFoot context only, repeated identically for all six shooter contexts):

| member | value | compared with the fleet |
|---|---|---|
| `AngleThresholdNewTarget` | **0.12** | identical to `autoaim_vehicle_lockon_missile` OnFoot (0.12); no-lockon preset is 0.05 |
| `AngleThresholdCurrentTarget` | **0.15** | identical to the lock-on preset (0.15); no-lockon is 0.12 |
| `AngleThreshMultiplierAtCutoff` | 0.15 | identical to the lock-on preset (0.15); no-lockon is 1 |
| `AngleThreshMultiplierCutoff` | 100.0 | lock-on preset 500; no-lockon 120 |
| `StickyAimStartAngle` | 5.0 | 0 in `w609`/`w612`; 5 in `w613` |
| `StickyAimAngleNewTarget` | 10.0 | 0 / 0 / 10 |
| `StickyAimAngleCurrentTarget` | 15.0 | 0 / 0 / 15 |
| `StickyAimStrength` | **0.0** | 0 everywhere - the "lock" is acquisition, not magnetism |
| `StickyAimMinAccValue` / `Max` | 0.5 / 1.0 | matches `w613` |
| `SnapAimTarget` | 0.2 | matches `w613` |
| `FitWeightCurrentTarget` | 0.2 | matches `w612`/`w613` |
| `FitWeightDistance` | **0.15** | identical to the lock-on preset (0.15); no-lockon is 1 |
| `FitWeightAngleDeflection` | 0.6 | matches `w612`/`w613` |
| `AlwaysTargetDistance` | -1.0 | unlimited |
| `MaxAimDistance` | **-1.0** | unlimited, like both shared presets; `w609` sets 750 |
| `MinAimDistance` | 15.0 | matches `w613`; `w609` 25, `w612` 5 |
| `CanTargetCharacters` | **1** | **unique** - every fleet missile tune and both presets are 0 |
| `CanTargetVehicles` | **1** | matches the lock-on preset |
| `CanTargetRigidObjects` | **0** | lock-on preset is 1 |
| `UseWeaponDirection` | 0 | 1 on all three fleet lock-on tunes |
| `FactionNeedsToBeHostile` | 0 | 0 everywhere |

`derived` — read the first four rows together: the Fire Leech's acquisition cone **is the fleet's
lock-on preset cone**, not the no-lockon one, with the cutoff multiplier at 100 instead of 500. It
was authored as a lock-on weapon and its own tune says so, independently of the wiki. It is also the
**only** tune in the corpus that may acquire characters, and the only one that excludes rigid
objects while keeping vehicles.

`UNKNOWN`: the `AutoAim` angle unit. The file stores bare floats; as turns 0.15 = 54°, as radians
8.6°. `T_WP3B_LOCKON.md` §4.2 leaves this open because the `StickyAimAngle*` family (5/10/15) cannot
be turns. This report does not resolve it, and BmAK's 40° cannot be written until it is.

---

## 3. Compared member by member

### 3.1 Fire Leech vs the Batmobile's missile (`w618_sportsmuscle_missile`)

Both tunes decoded in this session from `patch_win64/game1` (`w618` at 442204160, 14244 B;
`w143` at 440494080, 14238 B) — the two files differ by 6 bytes in size and share the whole
`MissileWeaponTuningBase` layout.

| member | `w143` Fire Leech | `w618` Batmobile missile | verdict |
|---|---|---|---|
| `missile_turning_speed` | **300 / 300** | **0 / 0** | **the whole difference**: w618 cannot home at all |
| `missile_turning_speed_random` | 60 | 0 | jitter only |
| `missile_no_turning_time` | 0 | 0 | same |
| `missile_acceleration` / `_time` | 30→65 over 0.2→10 s | 200→0 over 5→0 s | w618 is faster off the rail, single-segment; w143 curves in |
| `missile_acceleration_random` | 2→5 | 0 | jitter only |
| `missile_loose_lock_distance` | 0 | 0 | same (never released) |
| `missile_detonation_time` | -1 | -1 | same |
| `detonate_on_impact` | 1 | 1 | same |
| `missile_per_shot` | 1 | 1 | same |
| `gravity` | -9.82 | -9.82 | same |
| `meters_times_speed_in_front_of_target` | 0 | 0 | **neither computes lead** |
| `meters_proximity_self_detonate` | 0 | 0 | **neither has a proximity fuze** |
| `damage` | 30 | **1500** (AI 30) | do **not** copy |
| `impulse` | 10 | 350 | do **not** copy |
| `vehicle_damage_factor` | 0.5 | 1.0 | do **not** copy |
| `velocity` | 30 m/s | **360 m/s** | do **not** copy |
| `max_range` | 1000 m | 300 m | do **not** copy |
| `fire_rate` | 1.0 | 0.5 | do **not** copy |
| `magazine_size` | 1 | -1 (unlimited) | do **not** copy |
| `burst_count` | 0 | 1 | do **not** copy |

The one member that matters is the first: **w618's `missile_turning_speed` is 0, so the shipped
Batmobile missile flies straight.** That is confirmed here directly and matches
`T_WP3B_LOCKON.md` §1's list of the seven zero-turning vehicle missiles.

### 3.2 Fire Leech vs the fleet's lock-on missiles (`w609`, `w612`)

| member | `w143` | `w612` bomber lockon | `w609` jet lockon |
|---|---|---|---|
| `missile_turning_speed` | 300 / 300 | 300 / 300 | 150 / 300 |
| `missile_turning_speed_random` | 60 | 0 | 0 |
| `missile_acceleration` / `_time` | 30→65 / 0.2→10 | 50→300 / 0.5→20 | 5→300 / 0.5→5 (AI 50→300 / 0.5→20) |
| `damage` | 30 | 1500 | 1500 |
| `velocity` | 30 | 600 | 600 |
| `max_range` | 1000 | 300 | 750 |
| `magazine_size` | 1 | 2 | 8 |
| `fire_rate` | 1.0 | 0.5 | 0.2 |
| `burst_cooldown` | 0 | 0 | 1.0 |
| guidance member set | same 15 | same 15 | same 15 |

`derived`: the Fire Leech is a **w612-class homing rate in a slow, single-shot body**. It ties the
fleet maximum turning speed; it has none of the fleet's missile damage or speed.

### 3.3 So what is actually transplantable

`decoded` + `derived`: guidance is a **tune** member, not a component or a class. The proof is
already in the corpus twice over — `w612` carries a `CRPGFireLeachWeapon` whose only component is a
*lazer/tracer* component (`WEAPON_WIRING.md`), and
`w621_advancedhelicopter_missile` binds the lock-on preset yet still has turning speed 0
(`T_WP3B_LOCKON.md` §7.3). So:

* **copy 5 values** from `w143` onto the Batmobile's missile tune: `missile_turning_speed` 300,
  `missile_turning_speed_random` 60, `missile_acceleration` 30→65, `missile_acceleration_time`
  0.2→10, `missile_acceleration_random` 2→5;
* **change no class and add no component** — w618's build keeps its own weapon class and only gains
  a lock-on `AutoAim` tune;
* **keep every fire-block value from `w618`** (damage 1500, velocity 360, range 300, fire rate 0.5).

### 3.4 Fire Leech vs BmAK's missile behaviour

| BmAK behaviour | where decoded (`Research/BatmobileGrab/WEAPONS.md`) | Fire Leech carrier | verdict |
|---|---|---|---|
| guided flight after firing | the launch missile's projectile has **no** homing flag (`homing flag … absent`, p.133/183/…); the *tracker* projectile's flag is true at `0x0420` with `RBatmobileMissile.HomingDelay` **0.2 s** (p.522-523) | `missile_turning_speed` 300 + no `no_turning_time` | **carried** - and it beats the tracker, which delays homing 0.2 s |
| lock cone `LockOnAngle` **40°** | launcher, `0x0980` | `AngleThresholdCurrentTarget` 0.15 (54° as turns, 8.6° as radians) | **member exists, value cannot be pinned** until the unit is known |
| lock range `LockOnRange` **12000 UU = 120 m** | launcher, `0x0984` | `MaxAimDistance` -1 (unlimited) | **member exists**; set it to 120 (no fleet precedent for 120, but it is a plain float) |
| lock hold `MissileLockOnDuration` **2.0 s** (civilian 1.0) | `RBatmobileEMPMissile` `0x0A00`/`0x0A04` | **no member** - `AutoAimSettings` is 22 members, none a duration | **not carried**, `UNKNOWN` - native aim manager (`T_WP3B_LOCKON.md` §4.1) |
| `MaxTargets` **8** / `MissileNumberParameter` | launcher | `missile_per_shot` 1, `magazine_size` 1, nothing names a target count | **not carried** - `UNKNOWN` (`T_WP3B_LOCKON.md` §8.5) |
| `TargetSwitchName` (switch target while locked) | launcher | none | **not carried** |
| lose-lock (`LoseLockTime`, `LoseLockXBonus` 600 / `YBonus` 800) | `RBatmobileVehicleTracker` (`T_WP4C_TRACKER_EMP.md` §1) | `missile_loose_lock_distance` is distance, not time; no lose-lock member | **not carried** |
| salvo of N missiles at one aim point | launcher `FireInterval` 0.5 | `burst_count` 0 / `burst_cooldown` 0 (w614 does 6 × 5 s) | **carried by another tune**, not by w143 |

One more `decoded` fact that narrows the target-class question: BmAK's tag is typed `RVehicle`
(`TagTarget` → `RVehicle`, `SetLockOnTarget(RVehicleNPC)`), while **w143 may target characters**
(`CanTargetCharacters` 1). Copying the tune wholesale would let the Batmobile lock pedestrians, which
BmAK does not. The lock-on `AutoAim` should therefore be a *new* tune with `CanTargetCharacters` 0,
`CanTargetVehicles` 1, `CanTargetRigidObjects` 1 — i.e. the fleet **lock-on preset**'s classes with
w143's 0.12 / 0.15 cone.

---

## 4. Can the Fire Leech carry the lock-on missile?

**Partly — and the part it carries is the part that was missing.**

| half of "lock-on missile" | carried? | evidence |
|---|---|---|
| guided flight to the acquired target | **yes** | `missile_turning_speed` 300, random 60, no-turning-time 0 - decoded in §2.1 |
| target acquisition (cone, fit weights, vehicle class) | **yes** | `AutoAim` tune decoded in §2.3, cone equal to the fleet lock-on preset |
| a lock that is *held* for a duration | **no** | no duration member in any of the 103 weapon tunes or the two presets (`T_WP3B_LOCKON.md` §4.1, §8.4) |
| a salvo split across 8 targets | **no** | `missile_per_shot` 1; no target-count member (§8.5) |
| the on-screen lock reticle | **not from data** | `POI_TYPE_LOCK_ON_TARGET` exists in the movie, 0 scripts create it, entity→HUD is native (`JC3_HUD_WEAPONS.md` §5) |
| heat as a mechanic | **no such member** | the word `heat` does not occur in `w143`'s type dictionary |

`derived` verdict in the operator's terms: **the Fire Leech proves JC3 ships lock-on missiles, and it
is the correct donor for the Batmobile's lock-on — for the flight model and the acquisition cone. It
is not a donor for the lock timer or the multi-target salvo, because JC3's weapon data has no such
members; those two stay `UNKNOWN`/native.**

**Bonus, `decoded`:** the donor is already half-installed. `w618`'s own weapon entity carries
`models/jc_weapons/02_two_handed/w143_rpg_fire_leach/w143_rpg_fire_leach_projectile_body.model_xml`
(`WEAPON_WIRING.jsonl`, prop `61641926` on the `w618_sportsmuscle_missile` build), and its
`autoaim` prop (`6D4C8277`) is `autoaim_vehicle_no_lockon_missile`. So the build already flies the
Fire Leech's projectile and simply points it at the *no-lockon* preset with turning speed 0. The
operator's lead is consistent with the bytes: JC3's car missile **is** the Fire Leech's body without
its guidance.

---

## 5. The split, as the operator approved it

`BLOCKED_PROPOSALS.md` proposed (unapplied) `dispo: split` with T-WP4a = launcher, T-WP4b =
disable. The operator approved it on 2026-11-06 (operator ruling 4 on `DECISIONS_NEEDED.md`'s operator
sheet), with this lane's lead attached. The exact edit, for whoever carries lane 8010-8016's ledger
pass (this brief does **not** edit the ledger):

### T-WP4a — the EMP missile launcher (`dispo: next`)

* **Value:** `Batmobile_EMP_Missile_Launcher` (3 instances, 63 fields) + the `_ForCars` projectile,
  mounted as a **w618 clone**; guidance block transplanted from `w143` per §3.3 (5 values), lock-on
  `AutoAim` = a new tune with the lock-on preset's classes and w143's 0.12/0.15 cone,
  `MaxAimDistance` 120.
* **Confidence:** `decoded` for structure, tune members and the transplant; the *behaviour in play*
  stays untested (test ban).
* **Why it is buildable now:** every member above exists in a shipped tune, and the donor body is
  already the one the Batmobile ships.
* **What it still cannot do:** hold a lock for 2.0 s, switch targets, or fire at 8 targets — §4.

### T-WP4b — the EMP disable (`named omission`, `UNKNOWN`)

* **Value:** `UNKNOWN` — named omission.
* **Evidence of absence:** no EMP-named member on any NPC `RVehicle*` class
  (`T_WP4C_TRACKER_EMP.md`, marker `no EMP-named member exists`); `SetDisabledByEMP` is a state name
  on `RVehicleBatmobileBase`, with no duration/timer/target filter on the missile class
  (marker `SetDisabledByEMP`); JC3's EMP is the truck's entity-level `CForcePulse` (`EMP.json`,
  `truck_emp`), i.e. a blast, not a disable; 0 of the fleet's 88 vehicle weapon components is a
  `CEMPWeapon`.
* **Sibling row:** `T-MD2` cites T-WP4's disable half; after the split it must cite **T-WP4b**, and
  its `why` stops being "T-WP4 is blocked" and becomes "the disable is a named omission".

### Ledger mechanics

`T_ROWS.jsonl:154` (`T-WP4`) becomes two rows; `BLOCKED_PROPOSALS.md`'s `T-WP4 - partially-unblocked`
section becomes `applied`; `Tools/scripts/t_blocked.py --check` pins the ledger's sha256 and
re-derives the blocked set, so it must be re-run after the edit (a row leaving the blocked set makes
it red until the proposals file is regenerated). Undo is the reverse edit; no build artefact is
touched.

---

## 6. UNKNOWNs (searched, with what would settle each)

1. **The `AutoAim` angle unit** (turns vs radians). *Tried:* the type dictionaries of `w143`, `w609`,
   `w612`, `w613` and both shared presets — the file stores bare floats, no unit metadata. *Would
   settle:* a game probe of a 40° cone, or a native disassembly.
2. **Whether `POI_TYPE_LOCK_ON_TARGET` is painted from `AutoAim` state.** *Tried:* 260 HUD scripts,
   0 `CreatePoi(POI_TYPE_LOCK_ON_TARGET, …)` calls; the two presets; the entity props. *Where:*
   native aim manager.
3. **Lock hold time** (BmAK 2.0 s). *Tried:* all weapon tunes' `AutoAimSettings` (22 members), no
   duration; `MissileWeaponTuningBase`'s only `lock` member is a distance. *Where:* native.
4. **Multi-target salvo** (BmAK `MaxTargets` 8). *Tried:* every missile tune — `missile_per_shot` 1,
   no target-count member. *Would settle:* a code bridge or a probe.
5. **Whether a `CCar` chassis will fire a `WeaponTuning` authored for `02_two_handed`.** No car binds
   w143, so the chassis path is untested; the tune classes are shared, which is why the value
   transplant is still the cheap route.
6. **The Fire Leech's own entity graph.** `w143_rpg_fire_leach.epe` was read for the component list,
   but this brief did not decode a vehicle mount for it — it has none, being infantry — so nothing
   was claimed from it beyond the directory and tune facts above.

---

## 7. Checks and revert

* Every number in §2 and §3.1-3.2 was decoded in this session from the patch archive by
  `Tools/scripts/jc3adf.py` against `Research/JC3Grab/INDEX.jsonl` (paths and offsets in §1 and
  §3.1). No number is typed from memory or from the wiki.
* The BmAK side is quoted from `Research/BatmobileGrab/WEAPONS.md` at the line numbers given in
  §3.4; the tracker/EMP facts from `Working/Translation/T_WP4C_TRACKER_EMP.md`; the HUD and
  lock-on-preset facts from `Research/JC3Grab/JC3_HUD_WEAPONS.md` §5 and
  `Working/Translation/T_WP3B_LOCKON.md` §3-§4.
* **Not run:** `python Tools/scripts/t_wp3b.py --check` and `t_blocked.py --check` — neither is
  affected by this report, and both re-read the archives; no ledger or build file was edited here.
* **Revert:** delete `tmp/freebuff/reports/wp4-fire-leech.md`. Nothing else changed.
