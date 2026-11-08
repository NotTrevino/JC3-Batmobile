STATUS: done - the two files did not exist, so both were produced: `Tools/scripts/v05_combat.py` (new, `--write`/`--check`) and its generated `Working/Q/PREDICTIONS_COMBAT.md` (11 lines: 10 predicted, 1 UNKNOWN). `--check` passes 54/54 oracles and the document is byte-identical to the regenerated text. `--write` and `--check` both exit 0.

# V-05 part 2 rework - combat predictions (shots-to-kill, Vulcan overheat, missile lock)

## What the check found

Task 7204's part-3 report said `Working/Q/PREDICTIONS_COMBAT.md` did not exist. Confirmed on disk:

```
$ ls -la Working/Q/PREDICTIONS_COMBAT.md Tools/scripts/v05_combat.py
ls: cannot access 'Working/Q/PREDICTIONS_COMBAT.md': No such file or directory
ls: cannot access 'Tools/scripts/v05_combat.py': No such file or directory
```

`Working/Q/` held only `PREDICTIONS.md`, `PREDICTIONS_LOOKS.md`, `predictions.json`. So the
produce branch of the brief applied, not the audit branch. The new script was written to the
per-task naming rule (`v05_combat.py`, a new file - nothing of another task's was edited).

## Result

`Working/Q/PREDICTIONS_COMBAT.md` - build `Builds/bm-RC2`, `max_health` 36,000 re-read from the
built health module.

* **K-1..K-9 shots to kill**, one line per arm, with the H0/H1/H2 bracket, a pass band and its
  source row. Bm-RC2: pistol 1,200 / 120,000 / never; assault rifle 1,125 / 112,500 / never;
  machine gun 1,286 / 128,572 / never; shotgun 250 / 25,000 / 285; RPG 24 / 48 / 25; grenade
  36 / 36 / 36; tank cannon 24 / 48 / 25; heli missile 24 / 24 / 24; heli MG 1,440 / 144,000 /
  never. The band is the three-model bracket itself ("at least 1,200 hits (one model says
  never)" / "24-48 hits" / "36 hits, all three models agree"), never a single invented number.
* **K-10 Vulcan overheat time** = **never**: `HeatUpPerSecond` 0.0 @2680 (0x0A78) and
  `OverheatOffValue` 0.25 @2688 (0x0A80), 4/4 instances identical, so 0.25/0.0 has no finite
  time; pass band = no heat stop and no `Engine.Play_Minigun_Overheat` inside a 30 s burst (the
  30 s is the probe length, stated as such in the document - no row gives a limit).
* **K-11 missile lock time** = **UNKNOWN** for the build. BmAK's own rows are decoded
  (`MissileLockOnDuration` 2.0 s @2560 / 0x0A00, `CivilianMissileLockOnDuration` 1.0 s @2564 /
  0x0A04, 3/3 instances), but no JC3 row carries a duration: 0 of 4,054 decoded JC3 weapon-tune
  member rows name a lock duration, the only lock-named members are 22
  `missile_loose_lock_distance` rows (a distance), and the 1.5 s in `t19_hud.json` T-HUD18 is
  the POI 21 reticle's rotation. No band is printed for it.

**Finding worth carrying forward.** `DAMAGE_MODEL.md` §4's build column was written for
`Builds/test-091` at 2,000 HP, while `Builds/bm-RC2` reads 36,000 HP, so the published build
counts understate the RC by 18x (pistol 67 vs 1,200 hits). The same document's §5 already names
24 x 1500 = 36,000 and the fleet's 500..4000 range, so the RC ships a value that section calls
out of domain. The document prints both the RC table and the published test-091 table, and
`--check` asserts the published table against `DAMAGE_MODEL.json` row by row.

**Hand recomputation of three predictions** (arithmetic, as a cross-check on the script's
recompute): pistol H0 `ceil(36000/30)`, shotgun H2 `ceil((5000+36000)/144)`, tank cannon
H1/H0/H2 `ceil(36000/750)`, `ceil(36000/1500)`, `ceil((250+36000)/1500)`:

```
$ python -c "
import math
hp=36000
print('pistol H0', math.ceil(hp/30), '(30 dmg, bullet 5000@99)')
print('shotgun H2', math.ceil((5000+hp)/144), '(144/pull)', 'H0', math.ceil(hp/144))
print('tank_cannon H1', math.ceil(hp/(1500*(1-50/100))), 'H0', math.ceil(hp/1500), 'H2', math.ceil((250+hp)/1500))
print('grenade', math.ceil(hp/1012.5))
print('rpg H1', math.ceil(hp/(1500*0.5)))
"
pistol H0 1200 (30 dmg, bullet 5000@99)
shotgun H2 285 (144/pull) H0 250
tank_cannon H1 48 H0 24 H2 25
grenade 36
rpg H1 48
```

## Files written

| file | bytes/lines | sha256 |
|---|---|---|
| `Tools/scripts/v05_combat.py` | 417 lines | `b8b2459d141fef7123531a7235bf60ac947aa98c50a1ec8f9303f27abb124de8` |
| `Working/Q/PREDICTIONS_COMBAT.md` | 157 lines | `0b6d76f517379f6b7a5426be6cd3932dad8909bdca142966a932c7ce10534190` |
| `tmp/freebuff/reports/v05-combat-rewrite.md` | this report | - |

No existing `Builds/bm-*` tree, no `Research/` file and no other task's output was edited. No
game install, dropzone or process was touched; the test ban stays.

## Commands and verbatim output

```
$ python Tools/scripts/damage_predict.py --root Builds/bm-RC2 table
build under test: Builds/bm-RC2 (build_bm-RC2, max_health 36000)
arm            channel       damage     H0    H1    H2
pistol         bullet         30.00   1200 120000 never
assault_rifle  bullet         32.00   1125 112500 never
machine_gun    bullet         28.00   1286 128572 never
shotgun        bullet        144.00    250 25000   285
rpg            explosion    1500.00     24    48    25
grenade        unknown      1012.50     36    36    36
tank_cannon    explosion    1500.00     24    48    25
heli_missile   unknown      1500.00     24    24    24
heli_mg        bullet         25.00   1440 144000 never
hits-to-kill against the root pool; H0 armour ignored / H1 percentage gate / H2 threshold+pool
```

```
$ python Tools/scripts/v05_combat.py --write
write_exit=0
54/54 oracles pass
wrote Working/Q/PREDICTIONS_COMBAT.md
```

```
$ python Tools/scripts/v05_combat.py --check
check_exit=0
PASS DAMAGE_MODEL.md build table has 9 arm rows (9)
PASS DAMAGE_MODEL.json build_test-091 max_health 2000
PASS DAMAGE_MODEL.md section 2 prints the build as 2,000 HP
PASS DAMAGE_MODEL.md section 5 itself names the 36,000 HP ratio
PASS DAMAGE_MODEL.md build rows match DAMAGE_MODEL.json
PASS payload key is build_bm-RC2
PASS bm-RC2 max_health 36,000
PASS bm-RC2 table carries the 9 arms
PASS RC2 pistol H0 recomputes (1,200)
PASS RC2 pistol H1 recomputes (120,000)
PASS RC2 pistol H2 recomputes (never)
PASS RC2 assault_rifle H0 recomputes (1,125)
PASS RC2 assault_rifle H1 recomputes (112,500)
PASS RC2 assault_rifle H2 recomputes (never)
PASS RC2 machine_gun H0 recomputes (1,286)
PASS RC2 machine_gun H1 recomputes (128,572)
PASS RC2 machine_gun H2 recomputes (never)
PASS RC2 shotgun H0 recomputes (250)
PASS RC2 shotgun H1 recomputes (25,000)
PASS RC2 shotgun H2 recomputes (285)
PASS RC2 rpg H0 recomputes (24)
PASS RC2 rpg H1 recomputes (48)
PASS RC2 rpg H2 recomputes (25)
PASS RC2 grenade H0 recomputes (36)
PASS RC2 grenade H1 recomputes (36)
PASS RC2 grenade H2 recomputes (36)
PASS RC2 tank_cannon H0 recomputes (24)
PASS RC2 tank_cannon H1 recomputes (48)
PASS RC2 tank_cannon H2 recomputes (25)
PASS RC2 heli_missile H0 recomputes (24)
PASS RC2 heli_missile H1 recomputes (24)
PASS RC2 heli_missile H2 recomputes (24)
PASS RC2 heli_mg H0 recomputes (1,440)
PASS RC2 heli_mg H1 recomputes (144,000)
PASS RC2 heli_mg H2 recomputes (never)
PASS bm-RC2 bullet channel is 5000 @ 99 on every direct-hit arm
PASS tank cannon direct bullet is 1.0 (the 1500 blast is the primary)
PASS HeatUpPerSecond 0.0 in 4/4 instances
PASS HeatUpPerSecond @2680 (0x0A78)
PASS OverheatOffValue 0.25 in 4/4 instances
PASS OverheatOffValue @2688 (0x0A80)
PASS 0.25 / 0.0 has no finite time-to-overheat
PASS MissileLockOnDuration 2.0 in 3/3 instances
PASS MissileLockOnDuration @2560 (0x0A00)
PASS CivilianMissileLockOnDuration 1.0 in 3/3 instances
PASS CivilianMissileLockOnDuration @2564 (0x0A04)
PASS JC3 weapon tunes carry 4,054 member rows
PASS 0 JC3 weapon members name heat (0 distinct)
PASS 0 of 4,054 JC3 members name a lock duration
PASS the only lock-named JC3 members are 22 `missile_loose_lock_distance` rows
PASS T-HUD17 Vulcan heat is a named omission
PASS T-HUD18 lock is one marker rotating once per 1.5 s
PASS 7 capture files, 233 LockOnTime samples
PASS measured LockOnTime never reaches the 2.0 s row (max 1 s)
54/54 oracles pass
PASS document: PREDICTIONS_COMBAT.md matches the regenerated text
```

```
$ sha256sum Tools/scripts/v05_combat.py Working/Q/PREDICTIONS_COMBAT.md
b8b2459d141fef7123531a7235bf60ac947aa98c50a1ec8f9303f27abb124de8 *Tools/scripts/v05_combat.py
0b6d76f517379f6b7a5426be6cd3932dad8909bdca142966a932c7ce10534190 *Working/Q/PREDICTIONS_COMBAT.md
```

Failed draft kept for honesty: the first `--write` failed one oracle. I had claimed "0 JC3 weapon
members name lock"; the scan found 2 distinct paths, `missile_loose_lock_distance` under
`tuning` and `ai_tuning`. The claim was wrong, not the data: the document now says 0 members name
a *lock duration* and the two distance rows are named explicitly. No assertion was loosened and
no band changed.

## UNKNOWNs (no row gives a number)

* **missile lock time for the build** - 0 lock-duration members in 4,054 decoded JC3 weapon-tune
  rows, 0 `CreatePoi` calls of type 21 in the movie, and the entity -> HUD bridge is native
  (G2-25 §5). What would close it: a decoded JC3 missile `lock_time` member or the native
  caller. BmAK's 2.0 s cannot be copied.
* **Vulcan time-to-overheat on the BmAK side** - `HeatUpPerSecond` is 0.0; a per-shot heat add in
  native code is not excluded by the grab (`FOOTAGE.md` F-3). What would close it: a per-shot
  heat field in a decoded weapon object, or a measurement with the heat bar visible.
* **weapon -> armour channel** - no tune names a damage type or a `bullet_heavy` flag (0 of 1,515
  member rows, `DAMAGE_MODEL.md` step 3), so each arm's channel is taken from its gun class, not
  decoded. This is what makes each shots-to-kill line a bracket rather than one number.
* **the part layer** - every `*_vehicle_parts.vmodc` except the monorail flatbed fails ConvertAdf,
  so every count assumes the whole vehicle takes every hit.
* **whether the game honours any line** - the test ban stays; nothing was installed, launched or
  attached to, and no install script was run (not even `-WhatIf`).

## Labels

Decoded: the damage values (JC3 weapon tunes), the health module (`Builds/bm-RC2`), the heat and
lock fields with their `.uasset` offsets, the `DAMAGE_MODEL.md`/`.json` published table, the
`t19_hud.json` rows, the runtime samples. Derived: the hits (ceil per model), the band's
lo/hi, 0.25/0.0 = no finite time, 36,000/2,000 = 18x. UNKNOWN: the five items above, and
nothing was filled in from general knowledge of JC3, Unreal Engine 3 or Arkham Knight.

## COMPROMISES

None added by this task. The predictions describe `Builds/bm-RC2` as built; the one open lore
question the file cannot settle (a lock duration for the JC3 side) is listed as an UNKNOWN, not
as a compromise.
