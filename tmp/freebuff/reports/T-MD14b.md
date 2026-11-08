STATUS: done - the fleet has no runtime handling switch; the closest carrier is the three parallel
boost blocks, and the selector for them is missing, so Pursuit/Battle cannot be expressed in JC3 data.

## Summary

The card asked two things: does any JC3 vehicle change handling or physics while it is being
driven (VTOL, hover, transforming/two-mode, boost/upgrade states), and can any such carrier hold
BmAK's Pursuit/Battle switch.

**Fleet answer.** A fleet-wide member scan of 232 vehicle builds / 51 module types against the
state vocabulary (`vtol`, `hover`, `_mode`, `state_machine`, `_switch`, `alternate`, `gear_up/down`,
`retract`, `deploy`, `rotor_tilt`, `thrust_angle`, `amphibious`, `two_mode`, `transform_`,
`model_swap`, `convert`) returns **one** member: `AirplaneAI.Limit_Pitch_Yaw_Switch` = -1, an AI
flight-authority limit on the two plane AI graphs - not a handling switch. There is **no VTOL and
no hover member at all**, no mode enum, no state machine and no `SetMode`-style selector on a
vehicle.

What does exist, decoded with module + offsets:
- **three parallel boost blocks** on one module - `nitro_boost`, `nitro_boost_upgraded`,
  `heat_boost` - each a full performance block at its own struct offset. `AirGlobal` (bytes of
  `v4202_plane_capstone_fighterjet_air_global.vmodc`, 2012 B): `nitro_boost` @120,
  `nitro_boost_upgraded` @132, `heat_boost` @144, all `AirPerformanceBoost` (12 B, three floats).
  Land equivalent `CustomLandGlobal` bytes (`v0012_car_autostraad_atv_custom_land_global.vmodc`,
  3399 B): `arcade` (`ArcadePhysics`) @136, with `heat_boost` @136, `nitro_boost` @156,
  `nitro_boost_upgraded` @176, each `PerformanceBoost` (torque@0, grip@4, push@8, blend@12,
  extra_top_speed@16). Blocks on AirGlobal 41 builds, BoatGlobal 35, CustomLandGlobal 145.
  **No member selects which block is active** - the alternatives are real, the selector is not in
  the files.
- `VehicleParts.parts[i].model_swap` - a per-part mesh swap (visual only).
- `Rotors.rotors[i].does_steer` (0/1) and the `HelicopterModel` / `HelicopterSteering` curve
  families - continuous hover-to-forward authority inside one state, not a switch.

**BmAK answer.** `DRIVE_MODES.md` (G3-02l) decoded the switch as a state-driven byte:
`EBatmobileDriveMode` 0 Drive / 1 TurnOnSpot / 2 BattleMode, `DriveMode` ByteProperty @0x03b0,
`PursuitMode.BeginState` calling `SetDriveMode(0)` at script offset 69 and
`BattleMode.BeginState` calling `SetDriveMode(2)` at 88 (NPC twins 58 / 103), plus a 40-field
per-mode family (`BattleModeSteerAngleFactor` 2.5, `BattleModeMaxSteering` 80,
`BattleModeLatSlipScale`/`LongSlipScale` 4/10, `BattleModeMaxSpeed` 1200) and the front/rear
counter-torque pair 0.6 / -0.5. **None of that can be expressed in JC3 data**: no mode byte, no
state machine, no selector, one value set per vehicle. The parallel-block pattern is the closest
structural carrier (a module can hold alternative performance blocks), but it cannot be switched
from the files, so the switch is UNKNOWN / code bridge - not "JC3 cannot".

No value was guessed from general knowledge. Everything is labelled decoded / derived / UNKNOWN in
`T_MD14B_STATES.md`.

## Files written

- `Tools/scripts/t_md14b.py` - the generator (`--write` / `--check` / `--dump`).
- `Working/Translation/T_MD14B_STATES.md` - the note with the carrier tables, offsets and verdicts.
- `Working/Translation/T_MD14B_STATES.json` - the same record (type dictionaries, every row).
- `tmp/freebuff/reports/T-MD14b.md` - this report.

Not edited: `DRIVE_MODES.md`, `T_ROWS.jsonl`, any build tree, any game file.

## Commands and output

```
$ python Tools/scripts/t_md14b.py --write
wrote E:\Modding\JC3-Batmobile\Working\Translation\T_MD14B_STATES.json
wrote E:\Modding\JC3-Batmobile\Working\Translation\T_MD14B_STATES.md
hits 1 air modules 13 blocks 9
```

```
$ python Tools/scripts/t_md14b.py --check
hits 1, air 13, blocks 9, donor 15 values
OK: state census re-derived; document and JSON identical
```

`--check` re-reads the 232 decoded builds, the 13 indexed `*_air_global.vmodc` bytes and the 3
`*_custom_land_global.vmodc` bytes, re-derives both outputs byte-for-byte, and asserts: the hit set
is exactly `AirplaneAI`/`VehicleMisc` (so a new state member cannot appear unnoticed), the
`heat_boost` block exists, the donor carries `arcade.nitro_boost.extra_top_speed`, and the air
boost offsets are ascending (120 < 132 < 144).

## UNKNOWNs

1. **A selector for the three boost blocks.** *Tried:* the member scan for mode/state/variant/
   toggle/switch names over all builds; the byte-level type dictionaries of `AirGlobal` and
   `CustomLandGlobal`. *Result:* no such member. *Where:* native (the upgrade/heat system).
2. **Whether `heat_boost` is a runtime state at all.** The block exists on 145 land builds with
   different values from `nitro_boost` (`extra_top_speed` up to 120 vs 30-60), but nothing says
   when it applies.
3. **A VTOL / hover / transform member.** *Tried:* the token scan plus the full member lists of
   `AirGlobal`, `AirSteering`, `HelicopterSteering`, `HelicopterModel`, `Rotors`, `AirEngine`,
   `TrainGlobal`, `VehicleParts`, `BoatGlobal`. *Result:* none. *Where:* a native aircraft class the
   entity graph does not expose.
4. **Byte-level offsets for every land build.** Only 3 `*_custom_land_global.vmodc` are indexed;
   the offsets are representative of the type, not re-read on all 145 land builds (member names and
   values are still decoded from the row cache).
5. **How far the offset claim reaches for modules not indexed per entry** (e.g. `Suspension`,
   `Transmission` byte offsets): same reason as 4.

## COMPROMISES

The translation's current choice - one hybrid car with the 30 `BattleMode*` rows omitted because a
hybrid has no second variant - is **not approved by this card**, and this card does not approve it
either. It confirms the omission has a cause (no JC3 carrier) but not that the loss is acceptable:
per the project goal, "JC3 has no mode switch" is a limit to amend or to record as UNKNOWN, not a
closure. T-MD14/T-MD5/MD6/MD7/MD8/MD13 remain UNAPPROVED until the operator accepts the loss or a
code bridge carries the mode.

Static only: no game launched, attached to or installed to; no install or dropzone written.
