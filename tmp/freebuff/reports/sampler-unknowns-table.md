# Sampler UNKNOWN fields — the table the G3-02f report actually supports

Source read: `tmp/freebuff/reports/7207-g3-02f-sampler-unknowns.md` (327 lines). Checked against the report only; no `Research/` file was opened for writing and nothing under `Research/` changed.

## 0. Premise check — the count is 7, not 24, and none of it is a shader field

| what the brief says | what the report holds |
|---|---|
| "twenty-four UNKNOWN sampler fields" | **7** UNKNOWN items: 4 ANSWERED, 2 PARTLY, 1 still UNKNOWN (`tmp/freebuff/reports/7207-g3-02f-sampler-unknowns.md:51-61`) |
| "shader_or_cb" per field | **0** mentions of "shader" or "constant buffer" in the report; the subject is `RPlayerInput` bytes, flag-word bits and bind chains, not shaders |
| "the file path and line the report gives for each one" | the report gives a path for **2 of 3** open fields; `BoostingOut` gets a class name and an offset, not a line |

A 24-row table does not exist in the report, and the five `Research/BatmobileGrab/SAMPLER_*` documents (294 / 126 / 320 / 154 / 93 lines) do not carry one either; the report states its own count at `tmp/freebuff/reports/7207-g3-02f-sampler-unknowns.md:51` ("The seven UNKNOWNs") and at `:64` ("six items … plus the 774 mapping row = 7").

## 1. The fields the report leaves open (`Working/Prep/sampler_unknowns.json`)

| field_name | shader_or_cb | report_line | cited_path | path exists |
|---|---|---:|---|---|
| `BoostingOut` | none | 56 | `E:/Modding/_shared/tools/BmSDK-AK/src/BmSDK/Generated/BmGame/RVehicleBatmobileBase.g.cs` 5901 (offset), class file no line given | yes |
| `RPlayerController.QuickGadgetX` | none | 57 | `E:/Modding/_shared/tools/BmSDK-AK/src/BmSDK/Generated/BmGame/RPlayerController.g.cs` :489 | yes |
| `bCancelButton` | none | 61 | `DefaultInput.ini` :268 | **MISSING_PATH** |

reason_unknown, verbatim from the report:

* **`BoostingOut`** (`: 56`) — 1. **Why `BoostingOut` (+5901) is 1 for ~0.05 s at the eject.** Tried: the generated class (offset and comments only, no bodies), the eject documents (`EJECT_VELOCITY.md`, `EJECT_MOVE.md` - kinematics, no mention), `PHYSICS.md` / `COLLISION_GEOM.md` (collision only), and a search over all of `Research/` (`BoostingOut` appears only in sampler notes). Where it would be found: the UFunction body that writes +5901, i.e. the eject/animation path's bytecode, which no card has decoded yet. 2. **What consumes the barrage charge on an X press.** Tried: the bind chain (decoded, 783 is X) and `RPlayerController.QuickGadgetX`, which is a `ProcessEvent` wrapper (`:489`) with no body in the tree. Where: the `QuickGadgetX` body, or a capture that reads `WeaponGeneratorPower` (0x1EE8) in the same frame as a 783 edge. 3. **What produced the five `774 bCancelButton` taps.** Tried: every decoded bind string that writes `Button bCancelButton` (only `XboxTypeS_B`, `DefaultInput.ini:268`; the X and A lines carry `CancelBatarangCamera`, not the Button token), and the tap times against the stated presses (gaps 0.718 / 1.131 / 11.203 / 1.489 / 1.130 s to the next other rise - see the document's table). No keyboard binding writes it and B was not part of the stated script. Where: a device-level trace, or a keyboard `Button bCancelButton` binding if one exists in a config this project has not dumped. 4. **Whether U2's pulse is the boost being cancelled by the eject** - the plausible story, recorded as unproven, not as a finding.

* **`RPlayerController.QuickGadgetX`** (`: 57`) — 2. **What consumes the barrage charge on an X press.** Tried: the bind chain (decoded, 783 is X) and `RPlayerController.QuickGadgetX`, which is a `ProcessEvent` wrapper (`:489`) with no body in the tree. Where: the `QuickGadgetX` body, or a capture that reads `WeaponGeneratorPower` (0x1EE8) in the same frame as a 783 edge. 3. **What produced the five `774 bCancelButton` taps.** Tried: every decoded bind string that writes `Button bCancelButton` (only `XboxTypeS_B`, `DefaultInput.ini:268`; the X and A lines carry `CancelBatarangCamera`, not the Button token), and the tap times against the stated presses (gaps 0.718 / 1.131 / 11.203 / 1.489 / 1.130 s to the next other rise - see the document's table). No keyboard binding writes it and B was not part of the stated script. Where: a device-level trace, or a keyboard `Button bCancelButton` binding if one exists in a config this project has not dumped. 4. **Whether U2's pulse is the boost being cancelled by the eject** - the plausible story, recorded as unproven, not as a finding.

* **`bCancelButton`** (`: 61`) — 3. **What produced the five `774 bCancelButton` taps.** Tried: every decoded bind string that writes `Button bCancelButton` (only `XboxTypeS_B`, `DefaultInput.ini:268`; the X and A lines carry `CancelBatarangCamera`, not the Button token), and the tap times against the stated presses (gaps 0.718 / 1.131 / 11.203 / 1.489 / 1.130 s to the next other rise - see the document's table). No keyboard binding writes it and B was not part of the stated script. Where: a device-level trace, or a keyboard `Button bCancelButton` binding if one exists in a config this project has not dumped. 4. **Whether U2's pulse is the boost being cancelled by the eject** - the plausible story, recorded as unproven, not as a finding.

## 2. MISSING_PATH

* `DefaultInput.ini` — the report gives a bare file name with no directory; no DefaultInput.ini exists under the repo or E:/Modding/_shared/gamedata (depth 3)

The other paths a field cites were checked and exist: `E:/Modding/_shared/tools/BmSDK-AK/src/BmSDK/Generated/BmGame` (class tree), `Research/BatmobileGrab/EJECT_VELOCITY.md`, `Research/BatmobileGrab/EJECT_MOVE.md`, `Research/BatmobileGrab/PHYSICS.md`, `Research/BatmobileGrab/COLLISION_GEOM.md`, `Research/BatmobileGrab/CONTROLS.md`.

## 3. What a build lane can take from this

Three field-level unknowns, each with the report's own "where it would be found":

| field | the missing input the report names |
|---|---|
| `BoostingOut` (+5901) | the UFunction body that writes +5901 (eject/animation path bytecode) |
| `RPlayerController.QuickGadgetX` | the `QuickGadgetX` body, or a capture reading `WeaponGeneratorPower` (0x1EE8) in the same frame as a 783 edge |
| `bCancelButton` (774) | a device-level trace, or a keyboard `Button bCancelButton` binding in an undumped config |

No value was invented for any of them, and `shader_or_cb` is recorded as `none` rather than guessed: the report has no shader or constant-buffer subject to attribute.

## 4. Files, revert

**Written:** `Working/Prep/sampler_unknowns.json` and this report. **Untouched:** the source report, every `Research/` file, and all build artefacts.
**Revert:** delete the two files above.
