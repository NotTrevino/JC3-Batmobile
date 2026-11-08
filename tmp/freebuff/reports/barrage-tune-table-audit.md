# Barrage tune table audit (WPN-3)

**Source table:** `tmp/freebuff/reports/homing-weapon-tunes-to-barrage-values-plan.md` §2, rows 1–7
(the `reports/homing-weapon-tunes-to-barrage-values-plan.md` path named in the brief does not exist;
the file is under `tmp/freebuff/reports/`). §2.1 is audited in the appendix.
**Record folder searched:** `Research/BatmobileGrab/`
**Date:** 2026-11-08. **Method:** quote the plan, locate a record by tune/weapon name, read the record's
own value, compare. No tune decode, no build, no game.

**Headline:** the plan's tune table names **four distinct JC3 tunes** (`w618_sportsmuscle_missile`,
`autoaim_vehicle_lockon_missile`, `w614_monorailmissilecar_missile`, `w618`). **None of the four has a
record anywhere in `Research/BatmobileGrab/`**, so all **7/7 tune rows are UNKNOWN** on the record side.
The folder does hold the BmAK side, and there **20 value comparisons** are possible: **20 agree
numerically**, with **2 owner/attribution flags** (F1 `MaxTargets`, F2 `MaxTargetsPerLevel`) and
**1 scope caveat** (row 1's lock time is an EMP-launcher field, not a barrage-launcher field).

**Why the folder cannot settle a tune (coverage, not a missing search):** the record defines itself as
"The Batmobile's weapons: every value in the four vehicle packages" (`WEAPONS.md:1`) and its selection is
literal: "in the four vehicle packages, every object whose class starts with `RBatmobile`, plus every
`RBasicProjectile`" (`WEAPONS.md:33-34`). Its inputs are `objects.jsonl`, `CHAIN.json` and
`PARTICLES.json` only (`WEAPONS.md:25-30`) — no tune dictionary, no `WeaponTuning`, no `AutoAim`.
Its census is 62 objects over 13 classes (`WEAPONS.md:37-63`).

---

## 1. Working list — the plan's tune table, copied

Rows copied verbatim from the plan's §2 (BmAK property / BmAK value at offset / nearest JC3 tune /
member + offset / value to write).

| # | BmAK property | BmAK value (offset) | nearest JC3 tune | member + offset | value to write |
|---:|---|---|---|---|---|
| 1 | lock time | `RBatmobileEMPMissile.MissileLockOnDuration` 2.0 s `0x0A00`; civilian 1.0 `0x0A04` (3/3) | `w618_sportsmuscle_missile` | `WeaponTuning.aim_timer_override` @108 | 2.0 |
| 2 | acquisition cone | `RBatmobileMissileLauncher.LockOnAngle` 40.0 `0x0980` | `autoaim_vehicle_lockon_missile` | `AutoAimSettings.AngleThresholdCurrentTarget` @4, `…NewTarget` @0 (preset 0.15 / 0.12) | keep 0.15 / 0.12 (converted 0.1111 or 0.6981 — ship neither) |
| 3 | target count | `MaxTargets` 8 `0x095C`; `MaxTargetsPerLevel` `0x0A20` 1 item; Joker CDO 16 | `w614_monorailmissilecar_missile` | none; closest is `missile_per_shot` @44 | 8 on `missile_per_shot` @44 |
| 4 | missile count / cadence | `FireInterval` 0.5 s `0x098C` (Joker); `WeaponCoolDown` 20.0 `0x0830` | `w614` / `w618` | `burst_count` @88 (`missile_per_shot` @44), `burst_cooldown` @92, `fire_rate` | `missile_per_shot` 8, `burst_count` 1, `burst_cooldown` 0 |
| 5 | homing turn rate | none — homing bool `0x0420`, `HomingDelay`, `AccelRate` absent | `w614` | `missile_turning_speed` @24, `missile_no_turning_time` @32, `missile_turning_speed_random` @28 | 200 / 0 / 0 |
| 6 | speed | UNKNOWN — `Speed`, `MaxSpeed`, `AccelRate` absent; Joker sibling 500/1000/8000 | `w618_sportsmuscle_missile` | `velocity` / `max_speed` (dictionary; `w618` = 360 m/s) | keep 360 |
| 7 | damage | `Damage` 250.0 `0x02D8`; `DamageRadius` 0.0 `0x02DC`; `MomentumTransfer` 25000.0 `0x02E0`; type `0x02C8` | `w618` | `damage` (dictionary; `w618` = 1500, impulse 350) | keep 1500 / 350 |

---

## 2. Record lookup by tune name

Searched `Research/BatmobileGrab/` (every file; `.md`, `.json`, `.jsonl`, `.txt` searched explicitly).
`0` matches for any tune id or for `autoaim|WeaponTuning|AutoAimSettings|aim_timer_override|
missile_per_shot|burst_count|burst_cooldown|missile_turning_speed|AngleThreshold|MaxAimDistance`.
The only `sportsmuscle`/`monorail` hits in the folder are collision-mesh paths
(`COLLISION_LEDGER_CHECK.json:72`, `:2684`), not weapon tunes.

| tune (as named in plan) | exposed in plan row(s) | record found in `Research/BatmobileGrab/` | value the record holds | verdict |
|---|---|---|---|---|
| `w618_sportsmuscle_missile` | 1, 6 | none | — | **UNKNOWN** |
| `autoaim_vehicle_lockon_missile` | 2 | none | — | **UNKNOWN** |
| `w614_monorailmissilecar_missile` | 3, 4, 5 | none | — | **UNKNOWN** |
| `w618` | 4 (`fire_rate`), 6 (`velocity`), 7 (`damage`) | none | — | **UNKNOWN** |

Per-row result (record side):

| row | tune | record | record value for the member | verdict |
|---:|---|---|---|---|
| 1 | `w618_sportsmuscle_missile` | none | — (`aim_timer_override` @108 unrecorded) | **UNKNOWN** |
| 2 | `autoaim_vehicle_lockon_missile` | none | — (`AngleThreshold…` @4/@0 unrecorded) | **UNKNOWN** |
| 3 | `w614_monorailmissilecar_missile` | none | — (`missile_per_shot` @44 unrecorded) | **UNKNOWN** |
| 4 | `w614` / `w618` | none | — (`burst_count` @88, `burst_cooldown` @92, `fire_rate` unrecorded) | **UNKNOWN** |
| 5 | `w614` | none | — (`missile_turning_speed` @24 unrecorded) | **UNKNOWN** |
| 6 | `w618_sportsmuscle_missile` / `w618` | none | — (`velocity`, `max_speed` unrecorded) | **UNKNOWN** |
| 7 | `w618` | none | — (`damage` 1500, impulse 350 unrecorded) | **UNKNOWN** |

**Consequence:** no tune-value *difference* can be flagged, because no tune value has a record to differ
from. The plan's 0.15/0.12, 200, 360 and 1500 are quoted from `Working/Translation/T_WP3B_LOCKON.md`
(outside this folder; not used as a record here) and remain UNKNOWN by this audit's evidence rule. The
values to write are proposals, not record contents.

**Record-side evidence for "none":** `WEAPONS.md:1` (four vehicle packages), `WEAPONS.md:33-34`
(selection literal), `WEAPONS.md:37-63` (62 objects / 13 classes), `WEAPONS.md:25-30` (inputs).
The folder's weapon object names are all Batmobile ones (`objects.jsonl:5209`
`Batmobile_Missile_Launcher`, `objects.jsonl:5207` `Batmobile_Missile_Projectile`).

---

## 3. BmAK-side comparison — every plan value against the record

All comparisons are plan quote vs `WEAPONS.md` line. "Match" = identical value and offset.

| # | plan quote | record value | file:line | verdict |
|---:|---|---|---|---|
| 1a | `MissileLockOnDuration` 2.0 `0x0A00` | 2.0, `0x0A00` | `WEAPONS.md:839` | match (owner is `Batmobile_EMP_Missile_Launcher`, `WEAPONS.md:828`) |
| 1b | `CivilianMissileLockOnDuration` 1.0 `0x0A04` | 1.0, `0x0A04` | `WEAPONS.md:840` | match (EMP launcher, as labelled) |
| 2 | `LockOnAngle` 40.0 `0x0980` | 40.0, `0x0980` | `WEAPONS.md:1028`; Joker `:1082` | match |
| 3a | `MaxTargets` 8 `0x095C` | 8, `0x095C` | `WEAPONS.md:1081` (Joker instance) | match on value; **F1 attribution flag** |
| 3b | Joker CDO `MaxTargets` 16 | 16, `0x095C` | `WEAPONS.md:1116` | match |
| 3c | `MaxTargetsPerLevel` `0x0A20` 1 item | 1 item, 4 B; CDO 4 items | `WEAPONS.md:1087`, `:1118`; shape `:1726` | match on Joker only; **F2 attribution flag** |
| 4a | `FireInterval` 0.5 `0x098C` (Joker) | 0.5, `0x098C` | `WEAPONS.md:1083` | match (Joker-only, as plan states) |
| 4b | `WeaponCoolDown` 20.0 `0x0830` | 20.0, `0x0830` | `WEAPONS.md:1039`; Joker `:1089` | match |
| 5 | homing bool `0x0420`, `HomingDelay`, `AccelRate` absent | all absent | `WEAPONS.md:485`; table `:468-473`; `objects.jsonl:5207` | match (absence recorded) |
| 6 | `Projectile.Speed`, `MaxSpeed`, `AccelRate` absent | all absent | `WEAPONS.md:469-471`, `:485` | match (absence recorded) |
| 7a | `Damage` 250.0 `0x02D8` | 250.0, `0x02D8` | `WEAPONS.md:1610`; §4 table `:478` | match |
| 7b | `DamageRadius` 0.0 `0x02DC` | 0.0, `0x02DC` | `WEAPONS.md:1611`; `:480` | match |
| 7c | `MomentumTransfer` 25000.0 `0x02E0` | 25000.0, `0x02E0` | `WEAPONS.md:1612`; `:481` | match |
| 7d | type `Core.RDmgType_BatmobileMissileBarrage` `0x02C8` | same, `0x02C8` | `WEAPONS.md:1609`; `:482` | match |

Raw instance corroboration: `objects.jsonl:5207` carries the projectile's three floats at offsets
728/732/736 = 250.0 / 0.0 / 25000.0 and the damage type at 712; `objects.jsonl:5209` is the launcher's
16-tag record (40.0 @2432, 12000.0 @2436, 20.0 @2096, 12000.0 @2304) with no tag at `0x095C` (2432+).

---

## 4. Flags and UNKNOWNs

| id | item | finding | file:line |
|---|---|---|---|
| **F1** | row 3, `MaxTargets` 8 `0x095C` | The value is real but **Joker-only**. `WEAPONS.md` §12 lists the three Batmobile/MK2/Funhouse launchers' 16 fields (48 comparisons, 0 differences) and `MaxTargets` is **not among them** (`:1026-1041`); it appears only on `Batmobile_JokerMissile_Launcher` (`:1081`) and the Joker CDO (`:1116`). The plan's §1 sentence — "The launcher's `MaxTargets` 8 … all 16 fields identical across Batmobile/MK2/Funhouse, 48 comparisons" — attributes a Joker field to that 3-instance set. The plan's own row 3 offset is right; the ownership claim is not. | `WEAPONS.md:1026-1041`, `:1081`, `:1116`; `objects.jsonl:5209` |
| **F2** | row 3, `MaxTargetsPerLevel` `0x0A20` 1 item | Same attribution issue: the 1-item array is on the **Joker instance** (`:1087`), 4 items on the Joker CDO (`:1118`); §20 lists its users as `Batmobile_JokerMissile_Launcher, Default__RBatmobileMissileLauncherJoker` (`:1726`). No Batmobile/MK2/Funhouse launcher record carries the field. | `WEAPONS.md:1087`, `:1118`, `:1726` |
| **C1** | row 1, lock time 2.0 / 1.0 | Numerically correct, but the record owner is `Batmobile_EMP_Missile_Launcher` (`WEAPONS.md:828`, values `:839-840`). The barrage launcher's §12 field list has no `MissileLockOnDuration` (`:1026-1041`). The plan labels the class correctly; this is a scope caveat, not a mismatch. | `WEAPONS.md:828`, `:839-840`, `:1026-1041` |
| **U1–U7** | all 7 tune rows | **UNKNOWN**: no record for any of the four tunes in `Research/BatmobileGrab/`. Nothing here licenses 0.15/0.12, 0.1111, 200, 360 or 1500 as recorded values. | `WEAPONS.md:1`, `:33-34`, `:25-30` |

**Counts:** 7 rows / 4 distinct tunes → 4 UNKNOWN, 0 found, 0 tune-value mismatches detectable.
BmAK side: 14 field comparisons in §3 + 6 in §A = 20; **20 agree numerically**; 2 attribution flags
(F1, F2); 1 scope caveat (C1).

---

## Appendix A — plan §2.1 adjacent values

| plan quote | record value | file:line | verdict |
|---|---|---|---|
| `LockOnRange` 12000.0 `0x0984` | 12000.0, `0x0984` | `WEAPONS.md:1029` | match |
| `RVehicleWeapon.LethalRange` 12000.0 `0x0900` | 12000.0, `0x0900` | `WEAPONS.md:1041` | match |
| `WeaponCoolDown` 20.0 `0x0830` | 20.0, `0x0830` | `WEAPONS.md:1039` | match |
| `MissileSockets` 10 items, payload not decoded | 10 items, 8 B each | `WEAPONS.md:1088`; shape `:1728` | match (Joker instance) |
| `MissileNumberParameter` `Ww_Parameters.BML_NumberOfTargets` | same | `WEAPONS.md:1035` | match |
| `MaxTargetsPerLevel` 1 item, payload not decoded | 1 item, 4 B | `WEAPONS.md:1087`; shape `:1726` | match (Joker instance; see F2) |

---

## Appendix B — limits

- The comparison is **value-level only**. The plan's offset claims for its own BmAK rows check out where
  quoted; the JC3 members (`aim_timer_override` @108, `burst_count` @88, `missile_per_shot` @44,
  `missile_turning_speed` @24, `AutoAimSettings` @4/@0) have **no record in this folder**, so their
  offsets are also unverified here.
- The plan's tune evidence lives in `Working/Translation/T_WP3B_LOCKON.md`; that file exists but is
  outside the folder this audit was told to use, so its 103-tune claims are not re-audited. A follow-up
  that audits that file would be the only way to test the 0.15/0.12, 200, 360 and 1500 quotes.
- No build, tune write, `.epe` write, ledger/backlog edit, or game run. **New file; revert = delete it.**

`reports/barrage-tune-table-audit.md` — same content mirrored to
`tmp/freebuff/reports/barrage-tune-table-audit.md`.
