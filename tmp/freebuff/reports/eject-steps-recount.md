STATUS: done

# Eject build steps — recount of exits per name, against the plan and G2-20 (MOD-3)

Read-only recount. No game binary, build, `.epe` or module was touched; only the script and this
report were created.

- **Script:** `Working/Prep/count_eject_steps.py` — run `python -I Working/Prep/count_eject_steps.py`
- **JSON:** `Research/JC3Grab/EJECT.json`
- **Key counted:** `fleet.names` — one entry per distinct exit name, each with `count` (exits carrying
  that name). Cross-checked against `fleet.exits`, `fleet.graphs`, `fleet.distinct_names`, the
  `counts` block and `donor.exits`.
- **Plan compared:** `tmp/freebuff/reports/eject-sequence-build-steps-from-donor-exits.md`
- **G2-20 row:** `tmp/freebuff/reports/G2-20.md:31` and `:34`

**What "per step name" means here.** `EJECT.json` has no build-step key; its per-unit census is the
exit name (`fleet.names`). The table below therefore counts exits per exit name, and section 2 maps
every count the plan prints in its step table (steps 1–11) to that census.

## 1. Fleet exits per exit name (`fleet.names[*].count`)

| exit name | exits | states | roots |
|---|---:|---|---|
| `exit.driver.moving.parachute` | 221 | `S_EXIT_VEHICLE_PARA` 221 | CCar 125, CBoat 35, CHelicopter 23, CMotorBike 19, CAirPlane 19 |
| `exit.driver.pushed.out` | 221 | `S_PUSHED_OUT_VEHICLE` 221 | CCar 125, CBoat 35, CHelicopter 23, CMotorBike 19, CAirPlane 19 |
| `exit.driver.upside.down` | 221 | `S_EXIT_DRIVER_VEHICLE_UPSIDE_DOWN` 221 | CCar 125, CBoat 35, CHelicopter 23, CMotorBike 19, CAirPlane 19 |
| `exit.ai.driver.default0` | 206 | `S_EXIT_VEHICLE_0` 206 | CCar 124, CBoat 30, CHelicopter 32, CAirPlane 20 |
| `exit.ai.driver.default90L` | 206 | `S_EXIT_VEHICLE_90L` 206 | CCar 124, CBoat 30, CHelicopter 32, CAirPlane 20 |
| `exit.ai.driver.default90R` | 206 | `S_EXIT_VEHICLE_90R` 206 | CCar 124, CBoat 30, CHelicopter 32, CAirPlane 20 |
| `exit.driver.pulled.out` | 193 | `S_PULLED_OUT_VEHICLE` 193 | CCar 121, CBoat 30, CHelicopter 23, CAirPlane 19 |
| `exit.driver.to.swim` | 191 | `S_EXIT_DRIVER_VEHICLE_IN_WATER` 163, `S_EXIT_IN_WATER_MOTORBIKE` 28 | CCar 125, CBoat 5, CHelicopter 23, CMotorBike 19, CAirPlane 19 |
| `exit.driver.roll.out` | 183 | `S_ROLL_OUT_EXIT_VEHICLE` 183 | CCar 112, CBoat 30, CHelicopter 23, CAirPlane 18 |
| `exit.ai.driver.to.hood` | 175 | `S_EXIT_DRIVER_TO_HOOD_VEHICLE` 175 | CCar 104, CBoat 30, CHelicopter 23, CAirPlane 18 |
| `exit.ai.passenger1.default0` | 165 | `S_EXIT_VEHICLE_0` 165 | CCar 116, CBoat 10, CHelicopter 29, CAirPlane 10 |
| `exit.ai.passenger1.default90L` | 165 | `S_EXIT_VEHICLE_90L` 165 | CCar 116, CBoat 10, CHelicopter 29, CAirPlane 10 |
| `exit.ai.passenger1.default90R` | 165 | `S_EXIT_VEHICLE_90R` 165 | CCar 116, CBoat 10, CHelicopter 29, CAirPlane 10 |
| `exit.driver.default` | 161 | `S_EXIT_VEHICLE` 161 | CCar 119, CHelicopter 23, CAirPlane 19 |
| `exit.driver.to.fall` | 161 | `S_EXIT_VEHICLE_TO_FALL` 161 | CCar 117, CBoat 5, CHelicopter 18, CMotorBike 19, CAirPlane 2 |
| `exit.from.stunt` | 135 | `S_STUNT_EXIT_VEHICLE` 135 | CCar 107, CBoat 11, CAirPlane 17 |
| `exit.ai.driver.default` | 133 | `S_EXIT_VEHICLE` 133 | CCar 133 |
| `exit.ai.passenger1.to.hood` | 133 | `S_EXIT_DRIVER_TO_HOOD_VEHICLE` 133 | CCar 95, CBoat 10, CHelicopter 20, CAirPlane 8 |
| `exit.passenger1.upside.down` | 133 | `S_EXIT_PASSENGER_VEHICLE_UPSIDE_DOWN` 133 | CCar 95, CBoat 10, CHelicopter 20, CAirPlane 8 |
| `exit.ai.driver.default180` | 124 | `S_EXIT_VEHICLE_180` 124 | CCar 124 |
| `exit.passenger1.default` | 123 | `S_EXIT_VEHICLE` 123 | CCar 95, CHelicopter 20, CAirPlane 8 |
| `exit.passenger1.pulled.out` | 123 | `S_PULLED_OUT_VEHICLE` 123 | CCar 95, CHelicopter 20, CAirPlane 8 |
| `exit.passenger1.roll.out` | 123 | `S_ROLL_OUT_EXIT_VEHICLE` 123 | CCar 95, CHelicopter 20, CAirPlane 8 |
| `exit.ai.passenger1.default` | 116 | `S_EXIT_VEHICLE` 116 | CCar 116 |
| `exit.ai.passenger1.default180` | 116 | `S_EXIT_VEHICLE_180` 116 | CCar 116 |
| `exit.from.stunt.hood` | 93 | `S_STUNT_EXIT_VEHICLE` 93 | CCar 84, CBoat 5, CAirPlane 4 |
| `exit.reel.kicked.off.bwd.motorbike` | 33 | `S_REEL_KICKED_OFF_MOTORBIKE_BWD` 33 | CCar 9, CBoat 5, CMotorBike 19 |
| `exit.reel.kicked.off.fwd.motorbike` | 33 | `S_REEL_KICKED_OFF_MOTORBIKE_FWD` 33 | CCar 9, CBoat 5, CMotorBike 19 |
| `exit.reel.kicked.off.left.motorbike` | 33 | `S_REEL_KICKED_OFF_MOTORBIKE_LFT` 33 | CCar 9, CBoat 5, CMotorBike 19 |
| `exit.reel.kicked.off.right.motorbike` | 33 | `S_REEL_KICKED_OFF_MOTORBIKE_RGT` 33 | CCar 9, CBoat 5, CMotorBike 19 |
| `exit.passenger2.default` | 30 | `S_EXIT_VEHICLE` 30 | CCar 21, CHelicopter 9 |
| `exit.passenger2.roll.out` | 30 | `S_ROLL_OUT_EXIT_VEHICLE` 21, `S_EXIT_VEHICLE` 9 | CCar 21, CHelicopter 9 |
| `exit.passenger3.default` | 30 | `S_EXIT_VEHICLE` 30 | CCar 21, CHelicopter 9 |
| `exit.passenger3.roll.out` | 30 | `S_ROLL_OUT_EXIT_VEHICLE` 21, `S_EXIT_VEHICLE` 9 | CCar 21, CHelicopter 9 |
| `exit.ai.passenger2.to.back` | 29 | `S_EXIT_PASSENGER_LEFT_TO_BACK_VEHICLE` 29 | CCar 21, CHelicopter 6, CAirPlane 2 |
| `exit.ai.passenger3.to.back` | 29 | `S_EXIT_PASSENGER_LEFT_TO_BACK_VEHICLE` 29 | CCar 21, CHelicopter 6, CAirPlane 2 |
| `exit.driver.motorbike.left` | 28 | `S_EXIT_LEFT_MOTORBIKE` 28 | CCar 4, CBoat 5, CMotorBike 19 |
| `exit.driver.motorbike.right` | 28 | `S_EXIT_RIGHT_MOTORBIKE` 28 | CCar 4, CBoat 5, CMotorBike 19 |
| `exit.driver.motorbike.roll.out.left` | 28 | `S_ROLL_OUT_EXIT_LEFT_MOTORBIKE` 28 | CCar 4, CBoat 5, CMotorBike 19 |
| `exit.driver.motorbike.roll.out.right` | 28 | `S_ROLL_OUT_EXIT_RIGHT_MOTORBIKE` 28 | CCar 4, CBoat 5, CMotorBike 19 |
| `exit.kicked.off.left.motorbike` | 28 | `S_KICKED_OFF_LEFT_MOTORBIKE` 28 | CCar 4, CBoat 5, CMotorBike 19 |
| `exit.kicked.off.right.motorbike` | 28 | `S_KICKED_OFF_RIGHT_MOTORBIKE` 28 | CCar 4, CBoat 5, CMotorBike 19 |
| `exit.from.stunt.rear` | 27 | `S_STUNT_EXIT_VEHICLE` 27 | CCar 17, CAirPlane 8, CTrain 2 |
| `exit.stunt_to_reel` | 23 | `null` 23 | CHelicopter 23 |
| `exit.ai.driver.to.right.hood` | 16 | `S_EXIT_DRIVER_TO_RIGHT_HOOD_VEHICLE` 16 | CCar 16 |
| `exit.ai.passenger1.to.right.hood.` | 13 | `S_EXIT_DRIVER_TO_RIGHT_HOOD_VEHICLE` 13 | CCar 13 |
| `exit.mounted_weapon.fail.upright` | 13 | `S_EXIT_MOUNTED_WEAPON_FAIL` 13 | CBoat 13 |
| `exit.from.stunt.platform` | 11 | `S_STUNT_EXIT_VEHICLE` 11 | CCar 2, CBoat 9 |
| `exit.mounted_weapon.to.swim` | 10 | `S_EXIT_SPINNING_MOUNTED_VEHICLE_IN_WATER` 10 | CCar 7, CBoat 3 |
| `exit.hijack` | 7 | `S_EXIT_VEHICLE_HIJACK` 7 | CCar 7 |
| `exit.mounted_weapon` | 7 | `S_EXIT_SPINNING_MOUNTED_TO_FALL` 7 | CCar 7 |
| `exit.mounted_weapon.moving.parachute` | 7 | `S_EXIT_VEHICLE_PARA` 7 | CCar 7 |
| `exit.from.stunt.left` | 4 | `S_STUNT_EXIT_VEHICLE` 4 | CAirPlane 4 |
| `exit.ai.passenger4.default0` | 3 | `S_EXIT_VEHICLE_0` 3 | CCar 3 |
| `exit.ai.passenger4.default180` | 3 | `S_EXIT_VEHICLE_180` 3 | CCar 3 |
| `exit.ai.passenger4.default90L` | 3 | `S_EXIT_VEHICLE_90L` 3 | CCar 3 |
| `exit.ai.passenger4.default90R` | 3 | `S_EXIT_VEHICLE_90R` 3 | CCar 3 |
| `exit.ai.passenger5.default0` | 3 | `S_EXIT_VEHICLE_0` 3 | CCar 3 |
| `exit.ai.passenger5.default180` | 3 | `S_EXIT_VEHICLE_180` 3 | CCar 3 |
| `exit.ai.passenger5.default90L` | 3 | `S_EXIT_VEHICLE_90L` 3 | CCar 3 |
| `exit.ai.passenger5.default90R` | 3 | `S_EXIT_VEHICLE_90R` 3 | CCar 3 |

Totals: **61** names, **4,832** exits; `fleet.exits` 4,832, `fleet.graphs` 232,
`fleet.distinct_names` 61 — the per-name sum equals `fleet.exits` exactly.

### Donor-side checks (`donor.exits`)

| donor check | value |
|---|---:|
| donor exits (`donor.exits`) | 26 |
| donor exits with a gate | 7 |
| donor exits with no condition and no gate | 5 |
| donor `exit.driver.*` exits | 8 |
| donor `exit.driver.*` with null modifier | 8 |
| fleet exits `enabled=1` | 4832 |
| fleet exits `enabled=0` | 0 |
| `counts.fleet_exits` | 4832 |
| `counts.fleet_graphs` | 232 |
| `counts.fleet_names` | 61 |
| `counts.exit_launch_members` | 0 |

## 2. Counts printed in the plan, and in G2-20

| # | figure as printed | where printed | printed | recount from EJECT.json | verdict |
|---:|---|---|---:|---|---|
| 1 | donor exits copied verbatim | plan step 1, line 105; step 3, line 107; step 10, line 288; step 11, line 115 | 26 | `donor.exits` = 26 | **VERIFIED** |
| 2 | donor's "61-name vocabulary" | plan step 1, line 105 | 61 | donor has **26** distinct names; 61 is `fleet.distinct_names`, the fleet vocabulary | **OVERSTATED** — 61 names is the fleet figure, not the donor's |
| 3 | 5 named donor exits, "the other 21 exits" | plan lines 81–88 | 5 + 21 | all 5 names present verbatim; 26 − 5 = 21 | **VERIFIED** |
| 4 | "the 7 gated exits" | plan step 5, line 109 | 7 | donor rows with non-null `gate` = 7 | **VERIFIED** |
| 5 | "25 siblings" / "25 unchanged" / "25 still on `point.driver`" | plan lines 119, 155, 289 | 25 | 26 − 1 re-parented = 25 | **VERIFIED** (arithmetic on 26; not a separate JSON key) |
| 6 | `exit.driver.moving.parachute` on 221 of 232 vehicles | plan lines 91–92 | 221 / 232 | `fleet.names["exit.driver.moving.parachute"].count` = 221; `fleet.graphs` = 232 | **VERIFIED** |
| 7 | 4,832 exits | plan lines 37, 45; G2-20 lines 31, 34 | 4832 | sum of the 61 name counts = 4,832 = `fleet.exits` = `counts.fleet_exits` | **VERIFIED** |
| 8 | 232 graphs | plan line 46; G2-20 lines 31, 34 | 232 | `fleet.graphs` = 232 = `counts.fleet_graphs` | **VERIFIED** |
| 9 | 61 names | plan line 105 (as donor); G2-20 lines 31, 34, 64 | 61 | `len(fleet.names)` = 61 = `fleet.distinct_names` = `counts.fleet_names` | **VERIFIED as the fleet count**; see row 2 for the plan's attribution |
| 10 | every one of the 4,832 fleet exits is `enabled=1`, `0` never appears | plan line 188 | 4832 / 0 | `enabled=1` sum over `fleet.names` = 4,832; `enabled=0` sum = 0 | **VERIFIED** |
| 11 | 0 of 4,832 exits carry a launch member | plan lines 37, 45, 195 | 0 | `counts.exit_launch_members` = 0; `fleet.exit_keys` is the fixed 9-key set and contains no velocity/impulse/force/motion member | **VERIFIED** (aggregate; per-exit values are not re-derived here) |
| 12 | 2 of 104 graph classes name motion | plan lines 45–46, 196–197 | 2 / 104 | `counts.graph_classes_with_launch_name` = 2; `len(fleet.classes)` = 104 | **VERIFIED** |
| 13 | 1 hit in 232 module graphs | plan line 46 | 1 / 232 | `launch.launch` holds one name, `TrainGlobal.crashing_impulse` (value 12 = references, not members) | **VERIFIED** (one distinct member; the 12 is a reference count) |
| 14 | "the donor's seven driver exits all carry no modifier" | plan line 228 | 7 null | donor `exit.driver.*` rows = **8**, all with null `modifier` | **COUNT OFF** (8, not 7); the null-modifier assertion is VERIFIED |
| 15 | donor 26 exits, 7 speed-gated, 5 unconditional | G2-20 lines 31, 34 | 26 / 7 / 5 | `donor.exits` 26; non-null `gate` 7; no condition **and** no gate 5 | **VERIFIED** |
| 16 | 0 of 26 donor exits carry their own world | plan lines 37, 51–52 | 0 | donor records carry no `world` key (keys: `name`, `state`, `modifier`, `gate`, `conditions`, `parent`, `interaction`, `enabled`, `condition_classes`, `surface_m`, `batmobile`, `serpente`, `verdict`) | **VERIFIED as absence in this JSON**; the world census itself is `INTERACTION.md` §2 |
| 17 | 26 in, 26 out, 1 re-parented | plan step 11, lines 115, 288–289 | 26 / 1 | 26 donor exits; re-parent target `exit.driver.moving.parachute` is one of them | **VERIFIED** (the re-parent is a build action, not JSON data) |

**Result:** of 17 checked figures, 15 match the JSON exactly, 1 is a misattributed 61
(the donor vocabulary is 26 names), and 1 is a count error (eight `exit.driver.*` exits carry no
modifier, not seven). The G2-20 row's three headline figures — **4,832 exits, 232 graphs, 61
names** — all reproduce from `fleet.names` / `fleet.exits` / `fleet.graphs`.

## 3. Caveats

- The recount is a census of `fleet.names`; it does not re-open the 232 entity dumps. It proves the
  JSON's own arithmetic (61 rows summing to 4,832), not the dump scan behind it.
- `fleet.exit_keys` records `state` on 4,809 of 4,832 exits: 23 `exit.stunt_to_reel` rows carry a
  null state (`fleet.names["exit.stunt_to_reel"].states` = `{"null": 23}`). No plan figure depends on
  it, but a "every exit has a state" reading would be wrong.
- `modifier` is present on only 1,399 of 4,832 fleet exits; the plan's null-modifier claim is about
  the 26 donor exits and was checked there, not fleet-wide.

## 4. Files and revert

| file | change | revert |
|---|---|---|
| `Working/Prep/count_eject_steps.py` | **new** read-only counter | delete it |
| `tmp/freebuff/reports/eject-steps-recount.md` | **new** (this report) | delete it |

Nothing else was written or run: no game binary, no build, no `.epe`, no module, no plan edit.
