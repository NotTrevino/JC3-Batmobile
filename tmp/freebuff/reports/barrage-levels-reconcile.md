# Barrage levels — reconciling the operator's 1/4/7/10 with the decoded weapon data

Card: `barrage-levels-reconcile`. 2026-11-08. Report only; no build, tune, entity or ledger row written.

Operator fact being reconciled: **the battle-mode missile barrage auto-fires once the lock is complete, and the
number of locked targets scales with upgrade level — 1 bar = 1 target, 2 = 4, 3 = 7, 4 = 10.**

Labels: **decoded** = read at the named file:line or offset; **derived** = arithmetic shown; **operator** = the
2026-11-08 statement, which no file confirms or refutes; **UNKNOWN** = absent from the named files, with what
settles it.

## 0. Answer, in four lines

1. **No. The record does not hold 1/4/7/10.** The numbers appear in no file under `Research/BatmobileGrab/`.
2. **But the record holds the shape of that table**: `MaxTargetsPerLevel` @`0x0A20`, an `int` array indexed by
   `CurrentLevel` @`0x0A1C` — **4 entries** on exactly one object, the Joker class default; its **payload bytes
   were never decoded** (`WEAPONS.md` §20).
3. **No data member decides auto-fire.** The only fire-gate flag in the record is `bInstantFire` **true**, and it
   is declared on the **pursuit** class, not the barrage launcher. Battle auto-fire is native.
4. **`MissileLockOnDuration` 2.0 s belongs to pursuit** — confirmed three ways, so the memory note is right and
   the 2.0 s has nothing to do with the barrage's level table.

---

## 1. The BmAK values that exist, with sources

### 1.1 On the barrage launcher (`Batmobile_Missile_Launcher`, 3 instances: Batmobile, MK2, Funhouse)

`WEAPONS.md:1026-1041` — 16 field rows, **all 48 comparisons identical** (3 instances × 16 fields, 0 differences):

| member | offset | value | source |
|---|---|---:|---|
| `RBatmobileMissileLauncher.LockOnAngle` | 0x0980 | 40.0 | `WEAPONS.md:1028` |
| `RBatmobileMissileLauncher.LockOnRange` | 0x0984 | 12000.0 (cm → 120 m) | `WEAPONS.md:1029`; unit from `WEAPONS.md:16` |
| `RBatmobileMissileLauncher.MissileClass` | 0x0994 | `Batmobile_Missile_Projectile` | `:1030` |
| `RBatmobileMissileLauncher.TargetSwitchName` | 0x09BC | `Ww_Batmobile_Target.Batmobile_Target` | `:1033` |
| `RBatmobileMissileLauncher.LastTargetSwitchName` | 0x09C4 | `…_Target_Last` | `:1034` |
| `RBatmobileMissileLauncher.MissileNumberParameter` | 0x09CC | `Ww_Parameters.BML_NumberOfTargets` | `:1035` |
| `RVehicleWeapon.WeaponCoolDown` | 0x0830 | 20.0 | `:1039` |
| `RVehicleWeapon.LethalRange` | 0x0900 | 12000.0 | `WEAPONS.md` §12 |

**What is absent from that list is the point**: no `MaxTargets`, no `MaxTargetsPerLevel`, no `FireInterval`, no
`MissileSockets`, no `NthTarget`, no `CurrentLevel`, **no duration member of any kind**. The three playable
launchers set none of the level machinery.

### 1.2 There is no `RBatmobileMissileLauncher.MaxTargets` value anywhere on the playable side

The one value that gets quoted as "the launcher's `MaxTargets` 8" is on the **Joker** gadget instance
(`WEAPONS.md:1081`), and the same field is **16** on the Joker class default (`:1116`). Neither is the playable
launcher; the playable launchers set no tag at `0x095C` (the 16-field list above, and `lock-hold-salvo-reticle-
plan-v2.md` §3.1 W2).

| object | `MaxTargets` 0x095C | `MaxTargetsPerLevel` 0x0A20 | `MissileSockets` 0x0A30 | source |
|---|---:|---|---|---|
| `Batmobile_Missile_Launcher` ×3 (playable) | **absent** | **absent** | **absent** | `WEAPONS.md:1026-1041` |
| `Batmobile_JokerMissile_Launcher` | **8** | 1 item, 4 B | **10 items** | `:1081`, `:1087`, `:1088` |
| `Default__RBatmobileMissileLauncherJoker` | **16** | **4 items**, 4 B | absent | `:1116`, `:1118` |
| `Default__RBatmobileMissileLauncher` (BmGame CDO) | UNKNOWN | present (shape only) | present (shape only) | `SAMPLER_UNKNOWNS3.md:119`; values not in `WEAPONS.md` |

`MaxPostTapTargets` is a fourth counter on the Joker pair (12 instance / 32 CDO, `:1114`, `:1115`) — a Joker-only
"targets for a post-tap volley", not a level table.

### 1.3 The level machinery itself — decoded, in `SAMPLER_FIELDS2.md`

These are BmSDK-named, offset-decoded fields on `RBatmobileMissileLauncher` (the base class every variant shares):

| role | member | offset | kind | source |
|---|---|---|---:|---|
| target count ceiling | `MaxTargets` | 2396 (`0x95C`) | i32 | `SAMPLER_FIELDS2.md:55` |
| targets currently held (array, `Num` at +8) | `CurrentTargets` | 2400 (`0x960`) | tarray | `:56` |
| targets on the previous frame | `LastTargets` | 2416 (`0x970`) | tarray | `:57` |
| index of the **next target to fire at** | `NthTarget` | 2560 (`0xA00`) | i32 | `:66` |
| launcher state name | `LastState` | 2564 (`0xA04`) | fname | `:67` |
| **current target level** | `CurrentLevel` | 2588 (`0xA1C`) | i32 | `:68` |
| **per-level target cap** | `MaxTargetsPerLevel` | 2592 (`0xA20`) | tarray (16 B header) | `:69` |

`SAMPLER_FIELDS2.md:86` states the relationship in one line: *"`RBatmobileMissileLauncher.CurrentLevel`: with
MaxTargetsPerLevel, the per-level target cap"*. That is a **4-entry int table indexed by the upgrade level** —
exactly the container the operator's 1/4/7/10 needs.

### 1.4 …and the container is empty in the grab

`WEAPONS.md:1726` (§20, "Arrays whose elements the grab did not decode") lists `MaxTargetsPerLevel`
`count 1, stride 4, size 8` — and `MODLOG.md:7867-7870` records why: `objects.jsonl` keeps the array header
(`count`/`stride`/`size`) but not the element bytes, so these are "recorded by shape only … rather than
guessing". The **4-item** array is the CDO's (`WEAPONS.md:1118`); its four `int32` payloads are **UNKNOWN**.

So: **the table exists, is 4 levels wide, and its contents are not in the repository.** 1/4/7/10 is therefore
`operator`, not `decoded` — and it is *consistent* with a 4-level container in a way that `MaxTargets` 8/16 is
not, because 8 and 16 are single scalars, not levels.

### 1.5 The one decoded 4-level table in the record is the EMP burst, not the barrage

`Working/Translation/T_WP5B_EMP_BURST.md` via `Working/Roadmap/weapons.md` (T-WP5 row): EMP burst disable
**2 / 4 / 8 / 12 s per power level**, charge **0 / 0.5 / 1 / 1.5 s**. That proves BmAK ships per-level arrays
of exactly this shape elsewhere on the Batmobile — the pattern is real. It also shows the pattern is **not**
arithmetic: 2/4/8/12 is not +const, so 1/4/7/10 being +3/+3/+3 is not a fabrication by symmetry, it is just what
the operator reports.

---

## 2. Does auto-fire have a member? — no

| candidate | where | value | verdict |
|---|---|---|---|
| `RPursuitModeMissileLauncher.bInstantFire` | 0x09A0, `WEAPONS.md:848`; `OFFSETS.md:203` | **true** | **pursuit only** — declared on `RBatmobileEMPMissile`'s superclass, absent from the barrage launcher's field list |
| `LastState` (fname) | 0xA04, `SAMPLER_FIELDS2.md:67` | runtime `"None"` when idle (`runtime/samples2-*.jsonl`) | a **state name**, i.e. the launcher *is* a state machine — but the states are native strings, not data |
| `FireInterval` | 0x098C | **0.5 s** — Joker instance only (`WEAPONS.md:1083`) | cadence between shots, not a trigger condition |
| `WeaponCoolDown` | 0x0830 | 20.0 | cooldown after a volley |
| `CurrentTargets` / `LastTargets` | 0x960 / 0x970 | tarray | what the lock holds — the *input* to a decision, not the decision |
| `FiredProjectilesNum`, `InfinitMissilesTime` 10.0, `CurrentMissileSocket` | runtime only | 0 / 10.0 / 0 | counters that a native state machine drives (`SAMPLER_FIELDS2.md`, `runtime/samples2-*.jsonl`) |

There is **no** `bAutoFire`, `FireOnLock`, `AutoFireWhenLocked` or similar in `WEAPONS.md`, `OFFSETS.md`,
`CHAIN.json` or the BmSDK dump (`grep` over `Research/BatmobileGrab/` for `AutoFire|FireOnLock|bInstantFire` →
one hit, `bInstantFire`). Auto-fire at full lock is therefore **native behaviour over decoded counters**:
`CurrentTargets` reaching `MaxTargetsPerLevel[CurrentLevel]` while `LastState` is in a lock-complete state, then
`NthTarget` walks the array and `FireInterval` paces the shots. That reading is **derived** — it is consistent
with every member that exists and with the runtime sample, and it is not stated by any file.

**Consequence for JC3**: JC3 has no auto-fire member either (`T_WP3B_LOCKON.md` §5: a multi-target salvo needs a
code bridge; `fire_rate`/`burst_count` are trigger-driven), so "auto-fires at full lock" cannot be carried by
weapon data on either side. It needs a graph or the native hook.

---

## 3. `MissileLockOnDuration` 2.0 s — pursuit, confirmed

| check | evidence |
|---|---|
| declared on `RBatmobileEMPMissile`, **not** the barrage launcher | `WEAPONS.md:839-840` (EMP launcher section), offset `0x0A00`, value 2.0, civilian 1.0 at `0x0A04`; the barrage launcher's 16-field list (`:1026-1041`) contains **no** duration |
| the class it belongs to is the pursuit one | same offset `0x09A0` region is `RPursuitModeMissileLauncher.bInstantFire` (`OFFSETS.md:203`); `RPursuitModeMissileLauncher` is the EMP missile's superclass (`lock-hold-salvo-reticle-plan-v2.md` §1, from `bm-lock-duration-and-cone.md`) |
| the battle launcher has gates, not a timer | `LockOnAngle` 40.0, `LockOnRange` 12000.0, `MaxTargets`, `NthTarget`, `InitialFireDelay`, `FireInterval`, `CooldownDelay` — `lock-hold-salvo-reticle-plan-v2.md` §1, `Research/specs/B-24.md` §1 |
| JC3 has no duration member to receive it anyway | `AutoAimSettings` = 22 members, none a duration (`T_WP3B_LOCKON.md` §4.1, §9) |

**Verdict: memory note confirmed.** The 2.0 s is the pursuit acquisition (the shrinking circle), and any build
row that carries 2.0 s as the *barrage's* lock hold is carrying the wrong behaviour — `B-24`'s title ("the held
lock (2.0 s) and the 8-target salvo") pairs two numbers from two different launchers.

---

## 4. Agreements and contradictions (both kept)

| # | item | operator | decoded record | verdict |
|---|---|---|---|---|
| A1 | 4 upgrade levels | 4 bars | `MaxTargetsPerLevel` is a 4-entry array; the EMP burst ships 4 levels | **agree** (shape) |
| A2 | level indexes the cap | yes | `CurrentLevel` @0xA1C + `MaxTargetsPerLevel` @0xA20, `SAMPLER_FIELDS2.md:86` | **agree** |
| A3 | auto-fire when lock completes | yes | pursuit `bInstantFire` true; no battle flag | **partly** — no member; native |
| A4 | max = 10 targets | 4 bars = 10 | *nothing*; nearest scalars are 8 (Joker instance) and 16 (Joker CDO) | **contradiction — keep both.** 10 is operator; 8/16 are Joker-only and not the playable launcher |
| A5 | 1 target at 1 bar | 1 | next to 10 decoded `MissileSockets` on the Joker instance — could be 10 hardpoints matching 10 targets, or coincidence | **coincidence, flagged not claimed** |
| A6 | lock hold 2.0 s | — | 2.0 s is on `RBatmobileEMPMissile` (pursuit) | **contradiction with `B-24`'s framing**, not with the operator |
| A7 | barrage fires missiles at *locked targets* | yes | `MissileNumberParameter` = `Ww_Parameters.BML_NumberOfTargets`: BmAK **sends the target count to audio**, so a runtime multi-lock is implied by the audio parameter even though no comparator is stored | **agree** (indirect but strong) |
| A8 | 1/4/7/10 as data | — | B-24/plan v2 say `MaxTargets` 8 and compose "8 weapons" | **contradiction — keep both**; the 8 was never the playable value |

The two records that now disagree with each other: `Research/specs/B-24.md` §1/§3.2 ("fires at `MaxTargets` 8",
"8 slot-able missile weapons") versus this card plus `ROADMAP.md` §7 ("pick the max level (10)"). Both stay on
the record; §5 says which the build should use and why.

---

## 5. The value the build should use for a fully upgraded car

**10 targets, 10 missiles, one trigger pull** — i.e. the operator's 4-bar row, not the record's 8.

| field | value | why |
|---|---:|---|
| locked targets per barrage | **10** | operator 4-bar row; no file contradicts it (8 and 16 are Joker scalars, not levels) |
| missiles launched per trigger | **10** | BmAK fires one missile per target (`MissileClass` is a single projectile; `NthTarget` walks targets one shot at a time) |
| cadence | **0.5 s** between shots → **4.5 s** first-to-last ((10−1) × 0.5, `FireInterval` decoded on the Joker launcher) | decoded cadence, derived total |
| cooldown after the volley | **20.0 s** (`WeaponCoolDown` 0x0830, identical on all three playable instances) | decoded |
| lock gates | **40° / 120 m** | decoded (`LockOnAngle`, `LockOnRange` 12000 cm) |
| lock hold | **none for the barrage**; 2.0 s only if the pursuit circle is also built | §3 |
| auto-fire | not in data on either side → **graph or native hook**; if neither is available, hold-trigger + 10 shots is the closest honest composition | §2 |
| JC3 carrier for the count | `missile_per_shot` **10** on the private tune (precedent: `w123` fires 6 from **one** muzzle, `T_WP3B_LOCKON.md` §1), or 10 slot-able missile weapons (plan v2 D1), or 10 `SWeaponPoint`s on the 10 decoded `MissileSockets` | `MissileSockets` **count** is decoded (10); the socket **names/positions are not** (`WEAPONS.md:1088`, §20) |

**Why 10 and not 8.** The 8 has no owner on the playable launcher (§1.2) and the 8-vs-10 difference is exactly
the difference between the Joker's shipped instance value and the operator's max upgrade — so a build written to
8 would look correct in data review and wrong in game at 4 bars. Also note `B-24`'s "8 weapons" composition was
sized by the Joker scalar; **10** is the operator number and needs 10 weapons (or `missile_per_shot` 10).

**Do not use `MaxTargets` 16.** It is the Joker class default; using it would give a barrage 60 % larger than
the operator describes.

**Band for the test** (not a new value, the pass window): 10 markers / 10 launches at 4 bars, 7 at 3 bars, 4 at
2, 1 at 1 — integer counts, no tolerance, one run each; a 11th hostile never gains a marker. Gated on
`APPROVED_Q.txt`.

---

## 6. What would settle the payload (none of it done here)

| # | probe | settles | cost |
|---|---|---|---|
| 1 | decode the `MaxTargetsPerLevel` element bytes from the Batmobile package export (`grab_weapons.py` currently keeps only the header; `objects.jsonl` has no bytes) | 1/4/7/10 vs anything else — the only direct answer | one offline script extension |
| 2 | runtime sample with `CurrentLevel` ≠ 0 (the two samples on record both read `CurrentLevel: 0`) | whether the cap really is `MaxTargetsPerLevel[CurrentLevel]` | one BmSDK sampling session |
| 3 | footage count at 4 bars: markers on 9 hostiles in the cone | 10 vs 8 vs 16 | 10 minutes of play |
| 4 | `Default__RBatmobileMissileLauncher` (BmGame CDO) `MaxTargets` + `MaxTargetsPerLevel` values | what the playable launchers *inherit* (they set neither) | one grab of that export |

Probe 1 is the cheap one and it is the only one that can move 1/4/7/10 from `operator` to `decoded`.

---

## 7. Limits

- No game was launched and no archive, tune, entity or ledger row was written; every value here is quoted from
  the files named in-line or derived with the arithmetic shown.
- The 1/4/7/10 row is **operator** evidence. Nothing in `Research/BatmobileGrab/` contains those four numbers;
  the closest is a 4-slot container whose contents the grab never captured.
- The auto-fire mechanism is **derived** from the members that exist plus one runtime sample; no file states it.
- `MissileSockets` count (10) matching the 4-bar target count (10) is flagged as a possible coincidence; the
  socket payload is undecoded, so no claim is made that the 10 hardpoints are the 10 targets.
- The 0.5 s cadence and the 20.0 s cooldown are decoded **on the Joker instance / the three playable instances
  respectively**; the playable launchers set no `FireInterval`, so 0.5 s is the class value as shipped on the
  one object that sets it — UNKNOWN whether the playable launcher inherits it.

## 8. Reproduce

```bash
cd /e/Modding/JustCause3/JC3-Batmobile
sed -n '1026,1041p' Research/BatmobileGrab/WEAPONS.md   # playable launcher: 16 fields, no MaxTargets
sed -n '1081,1088p;1114,1119p' Research/BatmobileGrab/WEAPONS.md   # Joker 8 / 16, arrays
sed -n '1720,1730p' Research/BatmobileGrab/WEAPONS.md   # §20: payloads not decoded
sed -n '55,70p;86p' Research/BatmobileGrab/SAMPLER_FIELDS2.md      # CurrentLevel + MaxTargetsPerLevel
sed -n '839,848p' Research/BatmobileGrab/WEAPONS.md     # 2.0 s and bInstantFire, both on the EMP/pursuit class
grep -rn "MaxTargetsPerLevel" Research/BatmobileGrab/MODLOG.md      # (in MODLOG.md) header-only, 1 item / 4 B
grep -c "CurrentLevel" Research/BatmobileGrab/runtime/samples2-20261105T075011Z.jsonl
```
