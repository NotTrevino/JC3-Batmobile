STATUS: done

# T-WP13 — the largest BmAK weapon set JC3's driver slots can carry

**Summary.** JC3's model carries **2 bound driver weapons at once**, with a **third index
addressable but no member behind it**. Measured from the fleet: 53 armed entity graphs, at most
2 driver-slot properties per root (24 graphs have both, 23 of them bound; 14 have one; 15 have
none). The `DrivingMode` state machine selects by integer — `SelectVehicleWeapon(1)`,
`(2)`, `(3)` from `QuickGadgetB/X/Y` — so three indices exist, but only `main_weapon`
(`id:851CAABE`) and `secondary (id:00568A74`) have decoded root properties to point at. The
shipped keymaps carry `NEXT_WEAPON` (MWHEELUP) and `PREV_WEAPON` (MWHEELDOWN) **on the keyboard
only, scoped on-foot**, and no action with `land-vehicle` scope matches next/previous/select
weapon.

Against D-7's 11 weapons: **3 addressable (2 decoded binds + 1 unresolved index), 8 lost.**

## Files written

* `Tools/scripts/t_wp13.py` — `--write` / `--check`; re-reads `WEAPON_WIRING.jsonl`,
  `INPUT.md`, `DRIVINGMODE.md` and `T_ROWS.jsonl` (read only) and rebuilds the proposal.
* `Working/Translation/T_WP13_PROPOSAL.md` and `T_WP13_PROPOSAL.json` — the measured slot
  table, the selection mechanism, the 11-weapon mapping and the loss list.
* this report.

`Working/Translation/T_ROWS.jsonl` was **not edited** (read only, as the brief requires).

## The proposed mapping

| BmAK weapon | JC3 slot | label |
|---|---|---|
| WPN-1 Heavy Cannon | slot 1 `main_weapon` (`id:851CAABE`) | **decoded** — the medium tank binds `w602_mediumtank_canon` there |
| WPN-2 Vulcan chain gun | slot 2 `secondary (id:00568A74)` | **decoded** — the tank binds `w603_mediumtank_mgun` there; the only *land* vehicle with two bound driver weapons |
| WPN-3 Missile launcher | slot 3 (index only) | **derived** — the state machine addresses index 3; no root has a third property, so the member is UNKNOWN |
| WPN-4 EMP missile | slot 3, shared with WPN-3 | **UNKNOWN** — same unresolved index |
| WPN-5 EMP burst | no weapon slot — entity `CForcePulse` | **decoded** (no slot) |
| WPN-6 Power winch | none | **decoded** (no slot) — no winch class in the fleet |
| WPN-7 Drone hacker | none | **decoded** (no slot) |
| WPN-8 Seismic sonar | none | **decoded** (no slot) |
| WPN-9 Vehicle tracker | none | **decoded** (no slot) |
| WPN-10 Riot suppressor | none — a mode, not a weapon | **decoded** (no slot) |
| WPN-11 Booster | no slot — the nitro button | **decoded** (no slot) |

## What is lost

* 8 of 11 weapons: only the cannon and the Vulcan fit; the missiles are index-only and the
  other seven have no carrier (entity pulse, proven absences, a button).
* The per-mode split (battle vs pursuit): JC3 has one vehicle mode and no decoded mode→slot
  table, so "every weapon in both modes" cannot be expressed even for the two that fit.
* Switching by input: `NEXT_WEAPON`/`PREV_WEAPON` are on-foot scoped, so a driver cannot
  cycle; the only in-vehicle selection is the three quick-gadget indices, two bound.
* The HUD's 5 BmAK slots (primary + secondary + 3 special states) against JC3's 2 clips.

## Commands and output

```
$ uv run python Tools/scripts/t_wp13.py --write; echo "WRITE_EXIT=$?"; uv run python Tools/scripts/t_wp13.py --check; echo "CHECK_EXIT=$?"
wrote Working/Translation/T_WP13_PROPOSAL.md (144 lines) and .json
fleet 53 graphs, max driver slots 2, 38 with a driver weapon
select indices [1, 2, 3], next/prev ['NEXT_WEAPON', 'PREV_WEAPON']
placed 3 of 11, lost 8
oracles 6/6
WRITE_EXIT=0
CHECK OK: 6 oracles, max 2 bound slots, 3 indices, 3/11 placed
CHECK_EXIT=0
```

Oracles, all re-derived by `--check`:

| oracle | result | evidence |
|---|---|---|
| `O1-fleet-slot-max` | PASS | 53 armed graphs of the 232: driver_slots {0:15, 1:14, 2:24}; 38 carry a driver weapon; max 2 |
| `O2-no-vehicle-select-action` | PASS | weapon-named actions are only `NEXT_WEAPON`/`PREV_WEAPON`, both on-foot; 0 land-vehicle |
| `O3-select-indices` | PASS | `SelectVehicleWeapon(1,2,3)` across 6 quick-gadget state bodies; release side 1/2/3 |
| `O4-capacity-is-two-bound` | PASS | 3 indices addressable, 2 root properties bindable |
| `O5-demand-exceeds-capacity` | PASS | 11 rows, 3 addressable (2 decoded + 1 index), 8 lost |
| `O6-md-recomputed` | PASS | `--check` rebuilds the document and compares it |

## UNKNOWNs

* **What the third `SelectVehicleWeapon` index selects.** The literal 3 is decoded; the object
  behind it is not in the state body, and no fleet root carries a third driver property. Where:
  the native `RPlayerController.SelectVehicleWeapon` body, absent from the decoded packages.
* **Whether a vehicle consumes `NEXT_WEAPON`/`PREV_WEAPON`.** Both exist on the keyboard with
  on-foot scope; no file maps them to a vehicle state (INPUT.md §"UNKNOWN", G3-08).
* **A per-mode slot table.** No file splits weapons by battle/pursuit mode.
* **The `id:851CAABE` / `id:00568A74` semantic names.** The properties are decoded by hash id;
  the fleet binds weapons through them but no file names them `PrimaryWeapon`/`SecondaryWeapon`
  (that mapping is DRIVINGMODE.md's name-match note, not a decoded member name).
