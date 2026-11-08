STATUS: done

# T-WP13b - multiple vehicle weapon slots (second pass)

**Answer to the operator's question: yes, a vehicle can carry more than two - the entity has
four slot properties and two spare object pointers, and the fleet already ships weapons no slot
points at. What JC3 limits is not the slot count but the number of fire paths: two.**

The first pass was wrong in a measurable way. It counted the two *bound* driver pointers, called
`SelectVehicleWeapon` a selector and hung WPN-3/WPN-4 on an unresolved index 3. The decoded body
contradicts both claims:

* `DrivingMode.SelectVehicleWeapon` (export 104971) is a **fire** body - `ReadyToFire()`,
  `IsFiring()`, `RVehicleWeapon.TryToFireWeapon()` twice, `RSeqEvent_BatmobileRiddlerButton`.
  There is no active-slot variable in any of the 16 decoded bodies.
* BmAK addresses **four** indices, one button each: 1 -> `XboxTypeB`, 2 -> `XboxTypeX`,
  3 -> `XboxTypeY`, 4 -> `XboxTypeS_DPad_Up` (binding literal `SelectVehicleWeapon 4`, which the
  first pass never read). BmAK's model is "N slots, one button each", so JC3's
  primary/secondary pair is the borrowed thing to amend, not a ceiling.

## Files written

* `Tools/scripts/t_wp13b.py` - `--write` / `--check`, 13 oracles, reads only decoded artefacts.
* `Working/Translation/T_WP13B.md` - 253 lines, generated (not hand-edited).
* this report.

Nothing else was edited. `T_WP13_PROPOSAL.md`, `T_ROWS.jsonl`, `INPUT.md` and every other task's
files are untouched; no game process was started; no git.

## The four root properties, split by seat

| slot property | seat | roots carrying | roots bound |
|---|---|---:|---:|
| `main_weapon` | driver | 54 | 38 |
| `secondary (id:00568A74)` | driver | 54 | 24 |
| `mounted_weapon` | gunner | 54 | 14 |
| `mounted_weapon_2` | gunner | 54 | 5 |

All four sit on all 54 fleet roots (the same class-level pointers the first pass counted as
"main_weapon x54 ... "). Exactly two are driver-fired; `mounted_weapon` is gated by the
`gunner1` seat state `S_IDLE_VEHICLE_SPINNING_MOUNTED_WEAPON`, so the engine fires it only with a
pawn in the seat. Whether a driver can fire a gunner slot is UNKNOWN.

## The amendment path the first pass missed

Every root also carries `id:8580BA42` and `id:CA86AA17`: same class, same root, same object
reference shape as a weapon slot, present on all 54 roots, **non-null on none**. They are the only
decoded place to write WPN-3/WPN-4. Whether the engine fires a weapon behind them is UNKNOWN and
is a 5-minute experiment (point one at a copy of `w602_mediumtank_canon` on the medium tank).

Separately, **carrying** a third weapon is already normal: max 3 weapon components on one entity,
7 graphs with a component no slot points at (fighter jet, fighter-bomber, monorail missile car -
the last with zero bound slots). The limit is pointer + fire path, not component count.

## Slots are reused by mode in BmAK itself

BmAK binds `EMP` to B in battle and `Tracker / Immobilizer` to B in pursuit - one physical button,
two weapons, split by mode. So "slot sharing" is not a compromise invented here; it is BmAK's own
behaviour, and it is the fallback if the spare pointers do not fire.

Against the 11 weapons: 2 decoded slot carriers (WPN-1, WPN-2), 2 candidate spare-pointer carriers
(WPN-3, WPN-4), slot sharing by mode for WPN-8/WPN-9, 3 decoded absences that need no slot
(WPN-5 entity pulse, WPN-6 tether, WPN-11 nitro module), and 2 open (WPN-7 drone hacker - owned by
7137/G3-08d and placed here only; WPN-10 riot suppressor - no menu row, no member, no button).

## The Power Winch (d-pad RIGHT)

`TETHER.json`: 335 tether rows, 7 non-dialogue, `transport_rope_winch` on 4 entities over 40 part
rows, **0 functional winch classes**. The winch's button is free under the priority rule (d-pad
RIGHT ships as `USE_VEHICLE_MOD`), its geometry exists on a fleet vehicle (4 entities), and its
runtime is Rico's grapple, which the vehicle graphs do not carry - the only vehicle-scope tether
action is `VEHICLE_RELEASE_GRAPPLE` (d-pad DOWN, land-vehicle). Vehicle-side attach/reel members
are UNKNOWN.

## Commands and output

```
$ python -I Tools/scripts/t_wp13b.py --write; echo "WRITE_EXIT=$?"
wrote Working\Translation\T_WP13B.md (253 lines)
oracles 13/13 pass
WRITE_EXIT=0

$ python -I Tools/scripts/t_wp13b.py --check; echo "CHECK_EXIT=$?"
CHECK OK: 13 oracles, 11 weapons, 4 slots + 2 spare pointers
CHECK_EXIT=0
```

Oracles (all PASS, re-derived by `--check`): eleven weapons present; four slots on 54/54 roots;
driver/gunner split 2+2; max 2 driver slots; spare pointers null everywhere; carried-but-unbound
weapon exists; BmAK indices [1,2,3,4]; one button per index; index is a fire path; no JC3
land-vehicle selector action; HUD slots = 2; winch parts present; every cited menu label found.

## Corrections to hand back to the tracker

* The first pass's "3 indices, third unresolved" becomes "4 indices, all four with a button,
  none of them a stored selection".
* "8 of 11 lost" is no longer the summary: 5 weapons have a decoded non-slot carrier, 2 have a
  candidate pointer, 2 share a position by mode, and only WPN-10 has nothing.
* The 2-slot ceiling belongs to the HUD and the fire actions, not to the entity graph.

## UNKNOWNs

* Whether `id:8580BA42` / `id:CA86AA17` fire a weapon (native reader, not in the packages).
* Whether a driver can fire a gunner slot with nobody seated.
* Which weapon object a BmAK index resolves to (literals decoded, object not).
* How JC3 adds a third fire path: `TryToFireWeapon` has 0 rows in `INDEX.jsonl`, so JC3's
  per-weapon fire is native.
* The winch's vehicle-side attach/reel/release members.
* WPN-10 Riot suppressor's carrier and button.
