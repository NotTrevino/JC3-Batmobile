# Unranked-weapons UNKNOWN register

Source: `tmp/freebuff/reports/unranked-weapons-closest-system.md` (read only, unchanged).

**SUMMARY: 18 distinct UNKNOWNs, 36 rows, 15 PRESENT / 2 ABSENT / 1 NOT_CHECKED, 0 closed.**
The report carries each UNKNOWN twice — once in its section table (§1.5, §2.5, §3.5, §4.5) and once
in the section-7 register — which is the "about thirty-six" count: 18 ids × 2 = 36 rows. Every one of
the 18 was copied into `Working/Prep/unranked_unknowns.json` with `item_id`, `report_line`,
`claim_text`, `settling_file`, `settling_status`, plus `report_line_repeat`, the closest
`settling_line` and a note. Fifteen of the eighteen are PRESENT; **no present line states the
answer**, so nothing is marked resolved. `UR-1` is counted ABSENT (its `.ftune` is not in the
repository) and its `_JC3grab` half is separately listed as NOT_CHECKED.

## 1. The register at a glance

| item | report line | settling file (as named) | status | closest line found | closes? |
|---|---:|---|---|---|---:|
| `UC-1` | 139 | `Research/BatmobileGrab/CLASS_DEFAULTS.md` (`Default__RBasicProjectile`) + vendor scripts | PRESENT | `CLASS_DEFAULTS.md:163` (SVehicle `MaxSpeed` — wrong class) | no |
| `UC-2` | 140 | `CLASS_DEFAULTS.md` (`Default__RBatmobileHeavyCannon`) | PRESENT | `DAMAGE_RULES.md:432` (`TurretShotDamage` 110) | no |
| `UC-3` | 141 | `BmGame.upk` `Default__RBatmobileHeavyCannon` + `REGISTRATION.md` | **ABSENT** | `REGISTRATION.md:16` (native counts only) | no |
| `UC-4` | 142 | `Research/JC3Grab/WEAPONS.md` §9 + `_JC3grab/w602_…/` | PRESENT | `WEAPONS.md:370` (`StickyAimStartAngle` 5) | no |
| `UC-5` | 143 | `CLASS_DEFAULTS.md` + `HUD_SPEC.json` | PRESENT | none (0 hits in `HUD_SPEC.json`) | no |
| `UV-1` | 224 | `CLASS_DEFAULTS.md` (`Default__RBatmobileCannon`) | PRESENT | none (class absent); nearest `chase-01.md:111` | no |
| `UV-2` | 225 | `Working/vendor/BmAKgrab/scripts/` + `REGISTRATION.md` | PRESENT | none (14 dumps, no fire loop) | no |
| `UV-3` | 226 | `MOVING_PARTS.md:71` + `ANIMATIONS.md` | PRESENT | `MOVING_PARTS.md:61`, and its own text says the meaning is UNKNOWN | no |
| `UV-4` | 227 | `_JC3grab/w603_…wtunec` | **NOT_CHECKED** | — (outside the project) | no |
| `UR-1` | 295 | `_JC3grab/w603_…wtunec` + `gen_explosion_5m_nodamage.ftune` | **ABSENT** | `FORCEPULSE.md:131` (documents the .ftune) | no |
| `UR-2` | 296 | `JC3Grab/WEAPONS.md` §9 | PRESENT | `WEAPONS.md:308` (`AngleThresholdNewTarget`) | no |
| `UR-3` | 297 | `CLASS_DEFAULTS.md` (`Default__RBatmobileCannon`) | PRESENT | none (class absent) | no |
| `UR-4` | 298 | `JC3Grab/WEAPONS.md` §3 | PRESENT | `WEAPONS.md:697` (impulse band 0–100) | no |
| `UP-1` | 391 | `CLASS_DEFAULTS.md` (`Default__RBatmobileMissile`) | PRESENT | none (class absent) | no |
| `UP-2` | 392 | `MECHANICS.md` + `CLASS_DEFAULTS.md` | PRESENT | `WEAPONS.md:143` (homing absent; class default not claimed) | no |
| `UP-3` | 393 | `SOCKETS_JC3.json` + `WEAPONS.md` §12 | PRESENT | `SOCKETS_JC3.json:2807` (`MissileL`) | no |
| `UP-4` | 394 | `JC3Grab/WEAPONS.md` §9 | PRESENT | `WEAPONS.md:370` | no |
| `UP-5` | 395 | `Working/vendor/BmAKgrab/scripts/` | PRESENT | none (no launcher loop) | no |

## 2. What each PRESENT file actually contains

The distinction that matters for a build lane: a settling file can exist and still carry no line for
the member it was named for. Four shapes were found.

**Carries the member, not the semantics** — `JC3Grab/WEAPONS.md` (the three `AutoAim` angle members,
`UC-4`/`UR-2`/`UP-4`): the tables at `:308-312` and `:366-370` list
`AngleThresholdNewTarget 0.085…1.4`, `AngleThresholdCurrentTarget 0.3…1.4` and
`StickyAimStartAngle 0…5`. A value of **5** cannot be a 0..1 fraction, so the members are not all
fractions — but the file never names the unit, so the 15°/40° question stays open.
`WEAPONS.md:697` gives the impulse band (`0` … `100` over 11 presets) without any clamp statement
(`UR-4`).

**Class not in the file at all** — `Research/BatmobileGrab/CLASS_DEFAULTS.md` is 770 lines and decodes
the *vehicle* CDOs; it has **no** `Default__RBasicProjectile`, `Default__RBatmobileHeavyCannon`,
`Default__RBatmobileCannon` or `Default__RBatmobileMissile` row (`UC-1`, `UC-2`, `UV-1`, `UR-3`,
`UP-1`). Its only `MaxSpeed` row is SVehicle's 4000.0 (`:163`), a different class. `HUD_SPEC.json`
returns 0 hits for `Lethal`/`lock` (`UC-5`).

**Directory present, dump absent** — `Working/vendor/BmAKgrab/scripts/` holds **14** `.hex` files, all
`RVehicleBatmobileBase_*` plus `RVehicleCombatManager_GetDamageMod`; a grep for
`ChainGun|MissileLauncher|TurretShot|LethalRadius` returns **0** files. So `UV-2` (fire loop) and
`UP-5` (launcher lock loop) have no source in the one directory named for them; those two are still
recorded PRESENT because the directory itself exists.

**Present and self-limiting** — `Research/JC3Grab/MOVING_PARTS.md:61` gives
`GatlingGun | weapon_rpm | … | 20.0`, and the same section states: "What the field drives is not
defined in any file read here … the value itself is decoded, the meaning is UNKNOWN" (`UV-3`).
`Research/BatmobileGrab/WEAPONS.md:143` records homing as absent from every projectile instance and
adds "Whether a class default supplies it is not claimed" — which is precisely `UP-2`'s question.
`SOCKETS_JC3.json:2807/2866` decodes both pod points (`MissileL` [0.593771, 1.484682, −1.14681],
`MissileR`) but says nothing about the BmAK array's order (`UP-3`).

## 3. The two that are ABSENT and the two NOT CHECKED

- `UC-3` — the settling file is `BmGame.upk`, which is **not in the repository** (game install, not
  opened). The equivalent in-repo record is `Research/BatmobileGrab/REGISTRATION.md:16-18`, a
  native-function table (5 / 75 / 1 functions) with no cannon entry. The value 2.5 s is decoded at
  `WEAPONS.md:915`; what it *gates* is written nowhere.
- `UR-1` — `gen_explosion_5m_nodamage.ftune` is **ABSENT**: `tmp/wiring_run1.md:43` records "path
  editor/entities/jc_explosions/gen_explosion_5m_nodamage.ftune not in the build or the index".
  `Research/JC3Grab/FORCEPULSE.md:131` documents the same tune's `0 / 5` numbers, but it is a pulse,
  not a bullet, so it cannot settle a bullet's impulse behaviour.
- `UV-4` — the only settling path is `E:/Modding/_JC3grab/weapons/w603_mediumtank_mgun/…`, **outside
  the project** and outside this brief's `Research/` + `Working/` scope, so it is `NOT_CHECKED`, not
  `ABSENT`. `UR-1` names the same directory for its first half but is recorded `ABSENT` because its
  other settling file (`gen_explosion_5m_nodamage.ftune`) is missing from the repository; the
  `_JC3grab` half is listed under `not_checked_paths` beside it. A lane with access to that tree can
  close `UV-4`, and half of `UR-1`, by reading the two `.wtunec` files.

## 4. Checks

- `Working/Prep/unranked_unknowns.json` parses; 18 rows; ids unique and equal to the 18 distinct ids
  parsed from the report's 36 id-bearing table rows; `report_line` and `report_line_repeat` both point
  at a line whose first cell is that id.
- Every `settling_status` is one of `PRESENT`/`ABSENT`/`NOT_CHECKED`; every `PRESENT` row has a note
  and, where one exists, a `settling_line` whose file and line were read back and matched to the
  quoted text.
- `closed_by_a_present_line` is `0`: no entry was marked resolved, and no claim was made from memory —
  each status is a filesystem/line result recorded here.
- The source report was not modified.

## 5. Revert

Delete `Working/Prep/unranked_unknowns.json` and this report.
