# T-WP3b — JC3 lock-on / homing carriers for the Missile Barrage

## STATUS: DONE

Read-only on the game install: no archive or install was written, no game launched, no git.
`Research/JC3Grab/WEAPONS.md` and `Working/Translation/T7_WEAPONS.md` were not edited.

## Outputs

| file | what |
|---|---|
| `Working/Translation/T_WP3B_LOCKON.md` | the answer, tables with offsets/values, behaviour-by-behaviour mapping, contradictions, UNKNOWNs |
| `Working/Translation/T_WP3B_LOCKON.json` | the same decode, machine-readable |
| `Tools/scripts/t_wp3b.py` | `--write` / `--check` generator (decodes 103 weapon tunes + 2 shared presets + 3 per-weapon AutoAim tunes from `D:/Games/Just Cause 3/*.arc`) |

## Result in one paragraph

JC3 carries the Barrage: `WeaponTuning -> missile_weapon[0].missile_base_tuning.missile_turning_speed`
(struct offset **24**) is the homing strength — 150 on `w609`, 300 on `w612`, 200 on `w614`, 0 on
`w618`/`w611`/`w613`/`w601`/`w606`/`w615`/`w621` — and the fleet ships a real lock-on AutoAim preset
(`autoaim_vehicle_lockon_missile`) that differs from the no-lockon one in **15 rows of 3 members,
across all 6 shooter contexts**: the two cone angles, `AngleThreshMultiplierCutoff` 500 vs 100/120,
`FitWeightDistance` 0.15 vs 1.0, and `CanTargetVehicles` 1 vs 0 outside OnFoot. The lock **hold
timer** is the only missing piece: `AutoAimSettings` has 22 members and none is a duration, so
BmAK's `MissileLockOnDuration` 2.0 s (EMP 2.0 / civilian 1.0) stays `UNKNOWN`; that row is not
closed as "JC3 cannot" — it is named as native, with what was tried.

## What T7 missed (and where T7 stays right)

* Missed: a range member **does** exist — `MaxAimDistance` (offset **60**), -1 (= unlimited) in
  both shared presets, 750 in `w609`'s own preset. The car-missile read could not see a value.
* Missed: guided vehicle missiles exist (`w609`, `w612`, `w614`); `w614_monorailmissilecar_missile`
  on `v5603_train_urga_monorailmissilecar` is the only vehicle weapon that is both guided (200) and
  binds the lock-on preset.
* Holds: no lock duration anywhere in the weapon data; the HUD POI is still the only lock marker.
* Corrected: T7's "fractions of a turn" for AutoAim angles is one candidate reading, not decoded —
  the same block carries `StickyAimAngle*` 5/10/15, which cannot be turns.

## Contradictions against the leads (reported, files not bent)

1. Operator "JC3 already has heat-seeking missiles and target lock" — **confirmed** for 16 homing
   tunes, **but not fleet-wide**: 7 of 11 vehicle missiles have turning speed 0.
2. `w613_fighterbomber_missile_ground_lockon` acquires **nothing** (`CanTarget*` 0/0/0,
   `MaxAimDistance` -1, turning speed 0) — the name is the only "ground lock-on" in the ship.
3. The lock-on preset alone does not guide: `w621_advancedhelicopter_missile` binds it and has
   turning speed 0.
4. `w612` is guided but has `binding: []` on all three bomber builds — a donor value, not a
   working weapon.
5. No `CCar` binds the lock-on preset (only a CTrain and a CHelicopter do), so the Batmobile's
   lock-on has no car precedent — the carrier is the tune, not the chassis.

## Salvo / EMP

* Salvo: `burst_count` 6 (`w614` 5 s, `w613` 4 s) and `magazine_size` 8 (`w609`) exist, but
  `missile_per_shot` is 1 on every vehicle missile and **no member counts targets**. BmAK's
  `MaxTargets` 8 has no JC3 counterpart; a salvo across N targets needs a code bridge or an
  amended behaviour.
* EMP missile: same AutoAim machinery; no lock-duration member (2.0 s / 1.0 s stay UNKNOWN). The
  disable itself remains a separate row (`CEMPWeapon` + `CForcePulse` `EMP`, G2-16), untouched here.

## Checks

```
python Tools/scripts/t_wp3b.py --write   # wrote both files
python Tools/scripts/t_wp3b.py --check    # exit 0
fleet tunes 23, homing 16, preset diff rows 15
OK: lock-on data, preset diff and prose all re-derived identically
```

`--check` asserts: presets share one member set and differ in exactly 15 rows; `AutoAimSettings`
is 22 members with none matching `duration|hold_time|lock_time|linger`; the only `lock` member of
`MissileWeaponTuningBase` is `missile_loose_lock_distance`; the six compared tunes share one
struct layout; every quoted BmAK row still exists in `Research/BatmobileGrab/WEAPONS.md`; at least
one build binds the lock-on preset and none is a `CCar`; and the rendered markdown matches the
regenerated one byte for byte.

Two defects the check caught in my own first draft and that were fixed: the "vehicle missiles"
count read 0 of 0 (wrong path prefix), and the `CAimPOIWeaponComponent` table printed an empty
`id:2D0B3C09` column (the prop sits on the component, not the weapon).

## UNKNOWNs

1. What paints `POI_TYPE_LOCK_ON_TARGET` (21) from AutoAim state — native; 0 `CreatePoi` call sites
   in 260 scripts (G2-25).
2. The AutoAim angle unit.
3. `CAimPOIWeaponComponent`'s prop `id:2D0B3C09` (25 / 50 / 100) — no hash dictionary resolves it.
4. Lock hold time.
5. Whether a missile can hold several targets at once.
