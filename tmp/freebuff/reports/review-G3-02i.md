# Review — G3-02i `RPlayerController.DrivingMode`

Reviewed: `Research/BatmobileGrab/DRIVINGMODE.md`, `Research/BatmobileGrab/DRIVINGMODE.json`,
`Tools/scripts/grab_drivingmode.py`, against `BmGame.upk` read only with `Tools/scripts/upk_read.py`
(imported, unmodified) plus my own throw-away probes. No game process was touched, nothing was
written except this file.

## VERDICT: **minor issues**

The decode holds. I re-read every one of the 51 call sites in the 16 state bodies and all 51 target
names are right (12 of them resolve through the import table, not the export table), the byte at
each claimed offset really is `0x1B`/`0x1C`, no body contains a call token the report missed, and
the eject sequence is bytecode order: `DriverLeave`@365 → `RemoveBatmobileBindsAndSetBatmanBinds`@424
→ `PlayCockpitOpenFast`@443 → `Core.SetRBLinearVelocity`@513, each argument list closing on `0x16`
where the report says. The `FFInRange` label is a real local variable export (104926) under
`EjectFromVehicle`, so no region/label name here is invented (unlike G3-01e).

Three small defects keep it from "holds": one argument count is short by one token and `0x4A` is
rendered two different ways, O3's call-site total (69) does not reconcile with the report's own
tables (67 unique), and "the payload is that state's index" conflates a *name* index with the state
objects' export ids.

## Spot-checks (3 calls, my own reads)

| # | claim | bytes I read | verdict |
|---|---|---|---|
| 1 | `EjectFromVehicle@365` `DriverLeave(true, <0x2d>, FFInRange)`, virtual(0x1B) | `1b 01 6c 00 00 27 2d 00 de 99 01 00 16` at 365–377; name index `0x00006c01` = 27649 = `DriverLeave`; `27` = true; `2d` bare; `00 de 99 01 00` = local ref `0x000199de` = 104926 = `FFInRange` (outer 104931, `EjectFromVehicle`); closes `0x16` at 377 | **yes**, 3 arguments, close at 377 |
| 2 | `EjectFromVehicle@513` `Core.SetRBLinearVelocity(0, ref 0, ref 0, false)`, final(0x1C) | `1c 04 f7 ff ff 23 00 00 00 00 00 00 00 00 00 00 28 16` at 513–532; operand `0xFFFFF704` = −2300 → import `{'class_package': 'Core', 'name': 'SetRBLinearVelocity'}`; `0x23` carries 2 bytes (only that width lands on `0x16` at 532); two `00` refs at 521 and 526; `28` = false | **yes**, 4 arguments, close at 532 |
| 3 | `ToggleBattleMode@145` `TryToChangeMode(5269)` | `1c 38 29 00 00 2b 95 14 00 00 16` at 145–155; operand `0x00002938` = 10552 = `RVehicleBatmobileBase.TryToChangeMode`; `0x2b` + 4 bytes = `0x1495` = 5269; closes at 155 | **yes**, 1 argument; `names[5269] = 'BattleMode'` |

Widths used above are not assumed: `0x23`=2 B, `0x2B`=4 B, `0x2D`=0 B are each the only width that
puts the argument list's terminator on the `0x16` the report quotes. The report's `*` footnotes mark
these as heuristics; the bytes confirm the values it chose.

## All 51 call sites (independent re-walk)

Method: for every table row in the report, read the body's script (`pk.data(export)[22:-16]`), check
the token at the quoted offset, decode the operand (name index for `0x1B`, export **or** import ref
for `0x1C`) and compare with the quoted target. Result: **51/51 offsets and 51/51 names match**,
including the 12 rows whose operand is a negative import ref (`Core.IsButtonInputIgnored` −2189,
`Core.SetRBLinearVelocity` −2300, `Core.VSizeSq2D` −1486, `Core.ClearTimer` −1516,
`Core.TriggerEventClass` −1641, `Core.GetLineCount` −1690).

A byte scan of each of the 16 bodies for `0x1B`/`0x1C` with a resolvable operand returns exactly the
listed sites — `EjectFromVehicle` 15, `SelectVehicleWeapon` 8, `ToggleBattleMode` 5,
`BatmobileFireButton` 2, `SecondaryFireVehicleWeapon` 2, `FirePursuitMissile` 3,
`ReleaseVehicleWeapon` 3, `IsBatmobileFireButtonHeld` 2, `TriggerBatmobileBoost` 3, `BattleStrafe` 2,
and 1 each for the six QuickGadget bodies — **0 unlisted call tokens**. So the report's "51 call
sites" is complete, not a sample.

## The eject sequence, in execution order

The four calls in `EjectFromVehicle` (export 104931, 1297 script bytes, sha1 `070df66156ce` — matches
the report) are at ascending offsets with no call in between:

| order | at | call | arguments | arg list closes |
|---:|---:|---|---|---:|
| 1 | 365 | `DriverLeave(true, <0x2d>, FFInRange)` (0x1B, 27649) | 3 | 377 |
| 2 | 424 | `RemoveBatmobileBindsAndSetBatmanBinds()` (0x1B, 64560) | 0 | 430 |
| 3 | 443 | `PlayCockpitOpenFast()` (0x1B, 59294) | 0 | 449 |
| 4 | 513 | `Core.SetRBLinearVelocity(0, ref 0, ref 0, false)` (0x1C, −2300) | 4 | 532 |

So the narrative "eject is scripted as DriverLeave → binds → cockpit → SetRBLinearVelocity" is
**decoded**, not inferred. One qualifier the report does not spell out at the narrative: the run sits
inside a conditional — `07 7b 02` at 348 is `EX_JumpIfNot` with skip `0x027b`, i.e. the four calls
are in the guarded branch, so they execute in that order only when the guard passes. §4 does list
"control flow inside every body" as an exact gap, so this is a wording problem, not a false claim.

## Labels and region names

- `FFInRange` — real: export 104926, `class_index` −625 (local variable), outer 104931
  (`EjectFromVehicle`). Not invented, and it is the third argument of the call the report attaches
  it to.
- `CantEjectFromBatmobile`, `DriverLeave`, `RemoveBatmobileBindsAndSetBatmanBinds`,
  `PlayCockpitOpenFast`, `TriggerBoost`, `BattleModeFireButtonPressed`, `ButtonPressed`,
  `ButtonReleased`, `ReadyToFire`, `IsFiring`, `IsMoveInputIgnored`,
  `RVehicleBatmobileBase.TryToChangeMode` — every one is a `0x1B` name index or `0x1C` export ref in
  the body the report puts it in; none is a string that appears only in prose.
- `object_path` = `<outer short name>.<name>` — confirmed: export 104931 is
  `DrivingMode.EjectFromVehicle`, state 105048 is `RPlayerController.DrivingMode` (outer 106013
  `RPlayerController`).
- Bindings: the seven cited `DefaultInput.ini` lines re-read at :252, :259, :267–:270, :272 —
  `XboxTypeS_RightTrigger` carries `BatmobileFireButton` (:252), `DPad_Up` carries
  `SelectVehicleWeapon 4 / OnRelease ReleaseVehicleWeapon 4` (:259), `A` carries
  `EjectFromVehicle | BattleStrafe` (:267), `B` `QuickGadgetB / OnRelease ReleaseQuickGadgetB` (:268),
  `X` `QuickGadgetX / OnRelease ReleaseQuickGadgetY` (:269), `Y` `QuickGadgetY / OnRelease
  ReleaseQuickGadgetY` (:270), `RightShoulder` `SecondaryFireVehicleWeapon` (:272). All as tabulated.
- 16 commands, 16 bodies: exactly one export named each command with `outer_index == 105048`,
  verified for all 16.

## Issues

1. **`EjectFromVehicle@3` argument count is short by one.** Bytes `1b 5a 3c 00 00 4a 4a 16` at 3–10
   contain **two** `0x4A` tokens before the `0x16`; the table lists one (`CantEjectFromBatmobile(74)`,
   `unnamed 0x4a@8*`). The same table writes that token as `<0x4a>` in every other row, so one token
   is both missing and rendered inconsistently. Its own count for this row should be 2.

2. **O3's totals do not reconcile.** O3 says "69 call sites: 63 … + 6 stop at an exact gap" and lists
   five gaps (`EjectFromVehicle`@236, @276, @679, @1238; `AllowGadget`@39). The report's tables hold
   51 rows and its deeper lists hold 16 calls, i.e. 67 unique sites; `DRIVINGMODE.json` has 69 row
   objects because the two `TryToChangeMode` rows appear twice — once under `functions`, once under
   `mode_calls`. My independent walk agrees with 67 sites and 5 stalls (token `0x19` at 241 and 281,
   `0xd8` at 684, `0x2b` at 1243, `0x19` at 44). The intro line "51 call sites" is correct; the
   oracle line is not.

3. **"that state's index in the name table" conflates two id spaces.** `names[5269] = 'BattleMode'`
   and `names[61474] = 'PursuitMode'` are **decoded**. But the states themselves are exports 10547
   (`RVehicleBatmobileBase.BattleMode`) and 10525 (`RVehicleBatmobileBase.PursuitMode`, both
   `class_index` −645). So the argument is a *name* index, not the state's index, and
   `TryToChangeMode`'s own body is 5 script bytes (`29 37 29 00 00`), so nothing in it shows the
   argument being used as a state name. "The mode toggle is by name" is therefore **derived** at
   best, and the report should say so rather than calling O8 a pass on the meaning.

4. **The JSON carries the two mode calls twice** (issue 2's other half). Harmless for the reader of
   the MD, but any script consuming the JSON will count 69 and double the toggle.

## What I could not check

- **The guard's condition** at 348 (`0xF2 19 …`): the expression that decides the eject branch is
  not decoded by my walker (no width for `0xF2`, and the `0x19` context wrapper's skip field is not
  pinned). The report lists control flow as an exact gap; I confirm it is still open, so "when the
  player presses eject, this runs" is not proven — only that the four calls are in one guarded run.
- **What an `EX_VirtualFunction` dispatches to** (`DriverLeave`, `PlayCockpitOpenFast`,
  `RemoveBatmobileBindsAndSetBatmanBinds`, `ButtonPressed`, `ReadyToFire`, …): as the report says,
  the package stores a name, not an object. My probes list the name-matches; the dispatch is UNKNOWN
  and I did not try to close it.
- **The effect of the imported `Core.*` callees**: no body in this package, so their semantics are
  outside anything I can read here.
- **`UNKNOWN` in the report's §4 worth keeping**: which weapon/mode integer selects which object
  (`SelectVehicleWeapon 2/3` and the mode names) — the literals are decoded, the receivers are not.

## Commands (verbatim, trimmed to the output that carries the evidence)

```
$ PYTHONIOENCODING=utf-8 python - <<'PYEOF'   # export ids, script layout, sha1
...
105048 RPlayerController.DrivingMode script 645 5a09f82852bb
104931 DrivingMode.EjectFromVehicle script 1297 070df66156ce
104971 DrivingMode.SelectVehicleWeapon script 448 ff7bcbfcab46
105028 DrivingMode.ToggleBattleMode script 200 1cb9801219cb
...
state outer chain: 106013 RPlayerController
```

```
$ PYTHONIOENCODING=utf-8 python - <<'PYEOF'   # imports + states named BattleMode/PursuitMode
-2300 -> {'class_package': 'Core', 'class_name': 'Function', 'outer': -948, 'name': 'SetRBLinearVelocity'}
-1486 -> {... 'name': 'VSizeSq2D'}   -1516 -> {... 'name': 'ClearTimer'}
-2189 -> {... 'name': 'IsButtonInputIgnored'}   -1641 -> {... 'name': 'TriggerEventClass'}
10525 PursuitMode class -645 outer RVehicleBatmobileBase
10547 BattleMode class -645 outer RVehicleBatmobileBase
commands without exactly one body under 105048: none
```

```
$ PYTHONIOENCODING=utf-8 python - <<'PYEOF'   # every MD row re-read from the bytes
EjectFromVehicle  @3    tok=1b idx=15450  got=CantEjectFromBatmobile  md=1 mine=2
EjectFromVehicle  @365  tok=1b idx=27649  got=DriverLeave            md=3 mine=1 (stall 0x2d@371)
EjectFromVehicle  @513  tok=1c idx=-2300  got=<import>               md=4 mine=0 (stall 0x23@518)
ToggleBattleMode  @145  tok=1c idx=10552  got=RVehicleBatmobileBase.TryToChangeMode md=1 mine=0
... 51 rows checked, 0 name mismatches
```

```
$ PYTHONIOENCODING=utf-8 python - <<'PYEOF'   # corrected widths, eject order, scan for missed calls
@365  tok=1b DriverLeave                         args=3 end=377 byte[end-1]=16
@424  tok=1b RemoveBatmobileBindsAndSetBatmanBinds args=0 end=430 byte[end-1]=16
@443  tok=1b PlayCockpitOpenFast                 args=0 end=449 byte[end-1]=16
@513  tok=1c Core.SetRBLinearVelocity            args=4 end=532 byte[end-1]=16
@145 RVehicleBatmobileBase.TryToChangeMode args=[('w4', '0x2b', 5269)] end=155 close=16
@188 RVehicleBatmobileBase.TryToChangeMode args=[('w4', '0x2b', 61474)] end=193 close=16
names[5269]='BattleMode' names[61474]='PursuitMode'
DrivingMode.EjectFromVehicle  listed 15 scan 15 unlisted -
... all 16 bodies: listed == scan, unlisted "-"
```

```
$ sed -n '252p;259p;267p;268p;269p;270p;272p' ".../BmGame/Config/DefaultInput.ini"
.Bindings=(Name="XboxTypeS_RightTrigger",Command="... | BatmobileFireButton | ...")
.Bindings=(Name="XboxTypeS_DPad_Up",Command="... | SelectVehicleWeapon 4 | OnRelease ReleaseVehicleWeapon 4")
.Bindings=(Name="XboxTypeS_A",Command="... | EjectFromVehicle | BattleStrafe | ...")
.Bindings=(Name="XboxTypeS_B",Command="... | QuickGadgetB | OnRelease ReleaseQuickGadgetB | ...")
.Bindings=(Name="XboxTypeS_X",Command="... | QuickGadgetX | OnRelease ReleaseQuickGadgetY | ...")
.Bindings=(Name="XboxTypeS_Y",Command="... | QuickGadgetY | OnRelease ReleaseQuickGadgetY | ...")
.Bindings=(Name="XboxTypeS_RightShoulder",Command="... | SecondaryFireVehicleWeapon | ...")
```

No `--check` run of the card's own script was needed for the verdict: every number above comes from
my own reads of the package bytes, and the card's own `--check` result is quoted in the report, not
re-verified here (its oracles do not cover the three issues, which are all prose/count matters).
