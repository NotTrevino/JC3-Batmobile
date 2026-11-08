# Applying the weapon-slot rows — T-WP13, T-WP4, T-WP15

Task 8210. Inputs: `tmp/freebuff/reports/wp13-slots-force.md`,
`tmp/freebuff/reports/wp4-fire-leech.md`, `tmp/freebuff/reports/lock-hold-and-salvo-carrier.md`,
`tmp/freebuff/reports/lock-on-reticle-hud-link.md`, and the operator rulings at the bottom of
`Working/Translation/DECISIONS_NEEDED.md` (**ruling 3: force extra weapon slots**; **ruling 4:
approve the T-WP4 split**).

Generated, not hand-edited: `Working/Translation/T7_WEAPONS.md` and `t7_weapons_edits.json` come from
`Tools/scripts/t7_weapons.py --write`, the ledger from `t_rows.py build`, the sheet from
`t_blocked.py --write`. Every number below is decoded, derived or UNKNOWN.

## 1. T-WP13 — forced slots (disposition `blocked` → **`next`**)

**The premise, checked.** The two reference graphs carry **exactly two non-null slot pointers each**
and the "third weapon" is not a weapon:

| graph | slot pointers (of 4) | weapons | the shield |
|---|---|---|---|
| Imperator `v0202_car_capstone_bavariumtank_military_01.ee` | 2 — `main_weapon` → `w602_mediumtank_canon`, `id:00568A74` → `w603_mediumtank_mgun` | 2 | 3 `CPartProp` parts with the `BavariumShield` behaviour + `SValueDrivenEffectUsage` + 2 dynamic effects + 1 sound |
| Urga Mstitel `v2601_helicopter_urga_heavyassault_military_01.ee` | 2 — `w607_heavyhelicopter_mgun`, `w606_heavyhelicopter_missile` | 2 | 1 `BavariumShield` part |

So JC3's two driver slots are a **convention**, and a third slot is a **design decision**. The ruling
is applied as a forced design and recorded as one.

**Final value cell.** Four `CCar` roots on the one Batmobile entity, each with `main_weapon`
(`id:851CAABE`) and `id:00568A74` non-null = **8 slots** for the 8 slot-able BmAK objects (heavy
cannon, V2 cannon, missile launcher, EMP launcher, tracker, Joker cannon, Joker V2, Joker launcher).
Only decoded property names are used — **0 invented**. The four `mounted_weapon` /
`mounted_weapon_2` pointers stay null, because no graph mixes driver and gunner slots. Multi-root
precedent: `v4603_plane_urga_cargotransport_military_cargo_tank` (`CAirPlane` + `CCar`, each with its
own slot set).

**Entity-graph members involved:** the four root pointers (`main_weapon`, `id:00568A74`,
`mounted_weapon`, `mounted_weapon_2`), one `SWeaponPoint` per firing point (type 2 = muzzle,
`world` carries the direction), and 5 non-slot objects the slots cannot hold: `CForcePulse` (T-WP5),
`arcade.nitro_boost` (T-WP11), the winch anchor (B-16), the sonar pulse (B-20), the hacker effects
(B-19).

**Gaps, named not invented:** `RiotSuppressorMuzzle` has a decoded socket (0.389 / 1.451 / 0.142) and
**no point**; the Joker weapons have **no decoded socket**. Whether two or more roots on one car
chassis fire from the driver seat is **UNKNOWN** — no entity states the input-to-root binding.

## 2. T-WP4 — the launcher half (disposition `blocked` → **`next`**)

**Final value cell.** A `w618_sportsmuscle_missile` clone plus the entity `CForcePulse` copy, with
the **Fire Leech's guidance transplanted by value**:

```
w143_rpg_fire_leach.wtune -> w618 clone      (5 values, same MissileWeaponTuningBase layout)
  missile_turning_speed         300      (w618's own value is 0 - the shipped missile cannot home)
  missile_turning_speed_random   60
  missile_acceleration       30 -> 65    over _time 0.2 -> 10 s
  missile_acceleration_random  2 -> 5
new lock-on AutoAim tune (NOT w143's own, see below)
  AngleThresholdNewTarget 0.12 / AngleThresholdCurrentTarget 0.15   (= the fleet lock-on preset)
  MaxAimDistance 120 m                (= BmAK LockOnRange 12000 UU)
  CanTargetVehicles 1, CanTargetRigidObjects 1, CanTargetCharacters 0
every fire-block value stays w618's: damage 1500, velocity 360, max_range 300, fire_rate 0.5
```

Why a *new* `AutoAim` rather than a copy: `w143` sets `CanTargetCharacters` **1** and
`CanTargetRigidObjects` **0**; BmAK's lock is typed `RVehicle`, so a wholesale copy would let the
Batmobile lock pedestrians. The cone values are copied; the target classes come from the fleet
lock-on preset.

**Bonus, decoded:** the donor body is already half-installed — `w618`'s weapon entity points its
model at `jc_weapons/02_two_handed/w143_rpg_fire_leach/w143_rpg_fire_leach_projectile_body.model_xml`
and its autoaim prop is `autoaim_vehicle_no_lockon_missile`.

**Entity-graph members involved:** one more `CCar` root with `main_weapon` = the EMP missile clone
(and `id:00568A74` free, or the Vulcan's — T-WP13 decides), a `SWeaponPoint` at
`BattleModeSpotLight` with the −20 deg pitch, and the `CForcePulse` object copied from `truck_emp`.

## 3. The B-05 and B-06 edits these rows imply

**B-05 (entity graph, `bm_epe_edits.json` → `Builds/bm-0xx/.../*.epe`)** — object count grows, no
module row changes:

1. Two more `CCar` roots (roots 3 and 4 of T-WP13's plan seen as objects 468+), each cloned from the
   donor root with `main_weapon` (`id:851CAABE`) and `id:00568A74` re-pointed at the new weapon
   objects; the other four pointers copied as null.
2. `SWeaponPoint` rows: `RiotSuppressorMuzzle` (needs a socket, currently none) and one per Joker
   weapon (no socket exists — declared, not invented); the existing 5 socket-named points and 4
   `attach.vehicle` markers stay as they are.
3. The `CForcePulse` object (T-WP5) added once, not once per root.
4. Re-read: 8 non-null slot ids, every id a private or shipped weapon object, 0 dangling.

**B-06 (weapon tunes, private copies)** —

1. Private `w618` copy bound to the EMP launcher root: the 5 guidance values above written at their
   `offset-in-file` in `missile_weapon[0].tuning` (size unchanged — the Fire Leech's tune is the same
   class, 14,238 B vs w618's 14,244 B, so only member values change, never the layout).
2. A new `AutoAim` `.wtunec` (private path) with the six values above; the root's `6D4C8277`
   (`autoaim_tuning_file`) repointed at it.
3. Both private files registered in `@files.xml`; `bm_weapons.py --check` must resolve them and
   `jc3weapons.py --check` must re-read the two edited values.

## 4. T-WP15 — the disable half, a new row (`out`, named omission)

The split the operator approved needed a home for the half that cannot ship. `T-WP15` (code
`WPN-4b`) records it: `SetDisabledByEMP` is a state **name** on `RVehicleBatmobileBase`, no
EMP-named member exists on any NPC `RVehicle*` class, and **0 of the fleet's 88 vehicle weapon
components is a `CEMPWeapon`**. Nothing can be waited for, so it is not a `blocked` value row; the
route is T-WP5's `w702_emp` clone (card B-18), and the row says so.

## 5. The capabilities the emergency check added

`wp4-fire-leech.md` found three behaviours with no member. Each is now a card or a named omission:

| behaviour | status | where |
|---|---|---|
| 2.0 s held lock (`MissileLockOnDuration`) | **no member** — `AutoAim` is 22 members, 0 durations; `StickyAimStrength` 0 everywhere, so no magnet to hold | card `Research/specs/B-24.md` |
| 8-target salvo (`MaxTargets` 8) | **no member** — `missile_per_shot` 1 in all 7 missile tunes; closest is 8 slot-able missiles at one aim point (T-WP13 supplies the slots) | card `Research/specs/B-24.md` |
| reticle entity → HUD link | **art exists, caller absent** — `POI_TYPE_LOCK_ON_TARGET` 21 with 1.5 s rotation and a 0.5 s `MCI_missile_locked` banner, 0 of 260 HUD scripts create it | card `Research/specs/B-25.md` |

The lock **range** and **cone** are not gaps: `MaxAimDistance` 120 m and the 0.12 / 0.15 cone are
plain tune members and are written in T-WP4's cell.

## 6. Pin upkeep — `Tools/scripts/t_blocked.py`

Two rows left the blocked set (T-WP4, T-WP13) and one row was added as `out`, so both the blocked
count and the row count moved. Backup first: `Tools/scripts/t_blocked.py.bak-20261106` (the file is
untracked, so that copy is the pre-edit state).

| pin | from → to |
|---|---|
| `RESOLVED["T-WP4"]`, `RESOLVED["T-WP13"]` | new — 3 evidence oracles each (the two reports + the operator sheet) |
| `WAITS` | T-WP4 and T-WP13 removed |
| `ATTEMPTS` | now empty — the sheet enumerates waits only, no row waits on a test the repo can already decide |
| `counts["reconciles"]` | `13 ledger + 4 T6 = 17 of 216` → **`11 ledger + 4 T6 = 15 of 216`** |
| `in_scope` | **216** — unchanged: the `out` row that T-WP4's split added raises the row count and the excluded count equally |
| docstring + `render_md` | seven rows have left the set; "none left to test" |

Note on the `in_scope` arithmetic: the `out` bucket went 7 → 8 (`T-WP15`), rows 198 → 199, so
`199 + 33 − 8 − 8 = 216`. It was checked against `status_audit` rather than assumed.

## 7. Checks run

```
$ python Tools/scripts/t7_weapons.py --write
15 rows (13 WPN + 2 decisions), 164 aspects (46 UNKNOWN), 3 edits, 577 md lines      (exit 0)
$ python Tools/scripts/t7_weapons.py --check                                        (exit 0, after t_rows build)
$ python Tools/scripts/t_rows.py build
T_ROWS.jsonl: 199 rows, 35 edits over 16 rows                                       (exit 0)
$ python Tools/scripts/t_rows.py check
ledger 199 rows | edit 16 next 82 keep 56 epe 26 re-read 0 blocked 11 out 1 superseded 7
check ok                                                                            (exit 0)
$ python Tools/scripts/status_audit.py --write / --check
STATUS.md is current                                                                (exit 0)
$ python Tools/scripts/t_blocked.py --write / --check
15 blocked rows (11 ledger + 4 T6) of 216 in scope; 0 tested, 7 resolved            (exit 0)
```

`t7_weapons.py`'s own invariants were updated with the split: 15 rows now (12 WPN codes + `WPN-4b` +
D-7 + D-3), and `T-WP15` carries a `Research/…` proof path so the `out` row passes the same rule as
every other `out` row.

## 8. One check that is red, and why it is not this task's

`python Tools/scripts/t23_closeout.py --check` still exits 1. It reports **§11 has 11 decisions,
expected D-1…D-10** and that **B-17…B-22 have no payload and are not declared as no-payload steps**.
Both predate this task (B-17…B-21 were already listed before the row edits) and belong to the
build-batch sheet, not to the weapon rows: declaring a payload for a card that has none would be a
false record, so it was left red and reported rather than papered over. This task's four checks
(`t7_weapons`, `t_rows`, `status_audit`, `t_blocked`) are green.

## 9. Files changed

| file | change |
|---|---|
| `Working/Translation/T7_WEAPONS.md`, `t7_weapons_edits.json` | regenerated by `t7_weapons.py --write` (T-WP4 launcher, T-WP15 new, T-WP13 forced slots) |
| `Working/Translation/T_ROWS.jsonl` | regenerated — 199 rows, blocked 11, out 1 |
| `Tools/scripts/t7_weapons.py` | `row_wpn4` (launcher + Fire Leech), new `row_wp15`, `row_slots` (forced 8), invariants 15 rows, header prose |
| `Tools/scripts/t_rows.py` | `DISPO` for T-WP4 (`next`), T-WP13 (`next`), T-WP15 (`out`) |
| `Tools/scripts/t_blocked.py` | pins in section 6 (backup `.bak-20261106`) |
| `Working/Translation/BLOCKED_PROPOSALS.{json,md}`, `STATUS.md` | regenerated |
| `Research/specs/B-24.md`, `Research/specs/B-25.md` | new cards for the lock hold + salvo and the reticle link |

## 10. UNKNOWN

1. Whether multiple `CCar` roots on one car chassis fire from the driver seat (no entity states the
   binding; test ban).
2. The `AutoAim` angle unit (turns vs radians): 0.15 is 54° as turns, 8.6° as radians, and BmAK's 40°
   cannot be written until it is known.
3. `MissileSockets` (10 items × 8 B on the Joker launcher) — the array payload is undecoded, so the
   missile tube count is UNKNOWN; `MissileL`/`MissileR` are matched by name and shape.
4. The `id:00568A74` property's name (its id is the name of record).
5. Whether a `CCar` will fire a `WeaponTuning` authored for `jc_weapons/02_two_handed` — no car binds
   the Fire Leech, so the chassis path is untested.
