# Review - G3-02 (Batmobile controls from the shipped input configs)

VERDICT: **minor issues**. Every decoded value I re-read matches its source, the chain and hashes
are exact, and `--check` passes. The problems are: one derived summary mislabels "alias" as a
device, the word "exec" is used for tokens whose exec flag the card itself lists as UNKNOWN, and
the input-consumer UNKNOWN points at BmGame.upk bytecode although the driving input handler was
already decoded from `BatmanAK.exe` in G3-02c.

I wrote no research output; `grab_controls.py --write` was not run.

## Check output (verbatim)

```
$ cd "E:/Modding/JC3-Batmobile" && PYTHONIOENCODING=utf-8 uv run --with numpy --with pillow python Tools/scripts/grab_controls.py --check
same    E:\Modding\JC3-Batmobile\Research\BatmobileGrab\CONTROLS.md
same    E:\Modding\JC3-Batmobile\Research\BatmobileGrab\CONTROLS.json
check ok
CHECK_EXIT=0
```

Exit 0. The check compares both files byte-for-byte against a fresh derivation and prints `same`
per file.

## Spot-checks (5 values, re-read from the raw source)

| # | value in CONTROLS.md | source | re-read | match |
|---|---|---|---|---|
| 1 | `EjectFromVehicle` on gamepad `XboxTypeS_A`, `BmGame/Config/DefaultInput.ini:267` | ini line 267 | `.Bindings=(Name="XboxTypeS_A",Command="DebugCamSingleFrameStep \| EjectFromVehicle \| BattleStrafe  \| ContextSensitive \| Run \| …")` | **yes** |
| 2 | `BatmobileFireButton` on gamepad `XboxTypeS_RightTrigger`, `DefaultInput.ini:252` | ini line 252 | line 252 contains `… \| BatmobileFireButton \| Button bFireVehicleWeapon \| FireGun \| DeepScanIn` | **yes** |
| 3 | `aThrottleAxis` on gamepad `XboxTypeS_RightTriggerAxis`, `DefaultInput.ini:254` | ini line 254 | `Axis aThrottleAxis Speed=1.0 DeadZone=0.0` on that line | **yes** |
| 4 | chain table sha256 prefixes `13d3bc370e9f96df`, `b7436972c712d83d`, `7db2b893e174fb57`, `2bbb5862e2bbd1bd` | the four chain files, sha256 | exactly those four 16-hex prefixes, in the same file order | **yes** |
| 5 | consumer `RPlayerController.DrivingMode.BatmobileFireButton` (Function), and `aThrottleAxis` = `RPlayerInput.aThrottleAxis` (FloatProperty) | BmGame.upk export table | `BatmobileFireButton` exports 105039 (outer `RPlayerController.DrivingMode`) and 105256 (outer `RPlayerController`), class `Function`; `EjectFromVehicle` 104931 (DrivingMode); `aThrottleAxis` 107238, `FloatProperty`, outer `RPlayerInput` | **yes** |

Also checked: the `BasedOn` chain itself (PCInput.ini:2 -> `..\BmGame\Config\UserInput.ini`,
UserInput.ini:2 -> `..\BmGame\Config\DefaultInput.ini`, DefaultInput.ini:2 ->
`..\Engine\Config\BaseInput.ini`, BaseInput none), the package block (`214757637` bytes,
`177031` exports, `84813` names, `3268` imports, version `863`, licensee `32995`), and the alias
expansions the table relies on: `BrakeButton` = `BrakePressed | Button bHandbrakeOrBrake`
(DefaultInput.ini:177), `BatmobileSonar` = `BatmobileSonarPressed | OnRelease
BatmobileSonarReleased` (:184), `HoldForLineLaunchStop` (:183), `ContextSensitive` (:171),
`Run` (:152). All match.

## Issues

1. **"By device (derived from the Name field): gamepad 54, keyboard/mouse 271, alias 49".**
   The three classes are not devices. `alias` is the script's `device_of()` fallback for a Name
   that is neither a gamepad token nor a recognised physical key - i.e. **device unknown**, not a
   third device. Why it matters: the row is a headline number for D-11 (which inputs the Batmobile
   has); "alias 49" could be read as 49 alias-device bindings rather than 49 bindings whose Name
   the classifier did not recognise.

2. **"exec token" used where the exec flag is declared UNKNOWN.**
   The derived hold/press cells say e.g. "exec token BatmobileFireButton", and one UNKNOWN says
   "Exec flag of named token functions (whether the name is callable by the input layer) … not
   parsed". "exec" there is `parse_token()`'s label for a bare command token, not proof that the
   function carries FUNC_Exec. Suggested wording: "bare command token".

3. **Bare command tokens that are really console commands are counted as vehicle actions.**
   `KillVehicles` (DefaultInput.ini:207, `DebugKillAllEnemies | KillVehicles`) and `SpawnPlayerCar`
   (line 242) enter the action table only because the token contains "vehicle"/"car"; the
   relevance column does say "name match only", so this is disclosed, but the table is titled
   "One row per vehicle-relevant command token" and the two cheat rows are not vehicle controls.

4. **`Bindings parsed: 374` is a line count, not distinct bindings.** The same action is bound on
   several lines/files and inherited through the chain; nothing is de-duplicated. The number is
   reproducible, the wording invites a "374 distinct bindings" reading.

5. **No label on the `Package` block.** The last section prints
   `{"bytes": …, "export_count": …}` without the decoded/derived rule; every number there is
   decoded from the package header, but the card's own convention asks for the label.

6. **UNKNOWN "Keyboard keys that drive the Batmobile" / "Gamepad analogue inputs …" point at the
   wrong place.** Both say "would be in: consumer … in vehicle code (bytecode, BmGame.upk)". The
   driving input handler is native: `ARPlayerController::DrivingPlayerMove`, body `0x140254560`,
   decoded in `CONTROLS_NATIVE.md` (G3-02c), together with the two flag bits that gate the mode
   switch. Nothing in that card maps `aThrottleAxis` to that body, so the UNKNOWN itself stands,
   but its "where" is stale and should cross-reference `CONTROLS_NATIVE.md`.

## Resolvable UNKNOWNs

- **The input consumer (partly resolved already).** `RPlayerInput` is a cooked class with named
  `FloatProperty`/`ByteProperty` members (`aThrottleAxis` 107238, `aRawLHJoyUp`, `aStrafe`, …),
  and the BMSDK layout dump carries class offsets, so a native reader scan for
  `[playerinput+offset]` in `BatmanAK.exe` would show whether/where `aThrottleAxis` is consumed.
  The native driving handler is already known (G3-02c), so this is a bounded follow-up, not an
  open question.
- **"Which of BmInput.ini or the PC chain is loaded at runtime".** I tested the literal route:
  the executable contains **0** occurrences of `BmInput.ini`, `PCInput.ini`, `DefaultInput.ini`,
  `BaseInput.ini`, `UserInput.ini` and `Config\PC`. So the exe does not name these files as plain
  ASCII; the UNKNOWN cannot be closed by a string search and is honestly left open. (This also
  means the "IniVersion block = game-written style" argument for BmInput.ini remains an argument,
  not a decode - the card does not rely on it.)
- **Exec flag.** Resolvable in principle from the export header (`upk_read` reads 11 int32 per
  72-byte export record but keeps only six; the flags word is in the bytes), but proving *which*
  bit is FUNC_Exec needs a fleet invariant that this install does not give for script functions
  (the native registration only names native execs). Not resolvable honestly from these bytes.
- **Section precedence for duplicate aliases** (e.g. `MoveForward` in `Engine.PlayerInput` and
  `Engine.DebugCameraInput`): the ini files carry the sections; the precedence is engine behaviour,
  not serialised, so the UNKNOWN stands.
