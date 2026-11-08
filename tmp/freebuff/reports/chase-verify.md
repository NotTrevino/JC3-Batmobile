# chase-verify

**STATUS: done.** All 22 `found: true` hits from the local-LLM triage were re-opened at the source
they name and decided; the 20-hit sample of rejects and a screen of the whole reject pool are in.
Evidence file: `Research/BatmobileGrab/chase/chase-verify.md`. Journal: `MODLOG.md`
(`## chase-verify — done (2026-10-29)`). Re-derivation script: `Tools/scripts/chase/chase_verify.py`.

## Counts

| | |
|---|---|
| hits triaged by the model | 235 |
| `found: true` audited | **22** |
| **CONFIRMED** | **0** |
| **REJECTED** | **22** (10 text-route, 12 exe-route) |
| **missed** (a real default in the `found: false` pool) | **0** |
| F-rows involved | 14 — all still `UNKNOWN` |
| **model precision on this run** | **0 / 22 = 0 %** |
| reject-side accuracy on the sample | 20 / 20 correctly rejected |

The sample (seed `20261029`): F-45#0013, F-44#0005, F-33#0001, F-58#0007, F-40#0001, F-44#0010,
F-39#0004, F-21#0003, F-62#0011, F-61#0003, F-62#0002, F-40#0021, F-18#0005, F-62#0028, F-37#0005,
F-62#0003, F-40#0022, F-37#0002, F-19#0002, F-34#0002 — none is a find.

## Per-row results

| row | member (owner @offset) | claim | verdict | what the evidence supports |
|---|---|---|---|---|
| F-18 | `StrafeForce` (`RVehicleBatmobileBase` 0x11f8) | 250000.0 | REJECTED | source is the searcher's own `selftest.jsonl` fixture marked `(synthetic)`; its VA 0x1406a2b10 is inside a hash-map lookup. Class has **no** compiled initialiser (0 stores at 0x1cf8/0x1fdc/0x1fe0/0x1fe4). Value: none |
| F-23 | `TransformationAnimNode` (0x1494) | 852 | REJECTED | 852 = 0x354 = an offset (and of the *sim* class, not this one); member is an object ref. Value: none |
| F-33 | `BattleModeHeight` (0x199c) | 1 | REJECTED | 1 = number of packages containing the name. Value: none |
| F-38 | `BattleModeSpeedDelta` (0x1eb4) | 1 | REJECTED | same package-count echo. Value: none |
| F-39 | `TurnOnSpotSteeringSpeedCurve` (`RVehicleSimBatmobile` 0x268) | 100.0 / 0.5 / — / 0.5 | REJECTED ×4 | 3 stores go to a **stack frame**; the 4th is `[rdi+0x268] += 100` wrapped at ±180 (a heading). 0x268 is an `FInterpCurveFloat` (0x268…0x27c). Value: none |
| F-40 | `BattleModeMoving` (0x294) | 0.0 | REJECTED | `movss [rbp+0x294]`, rbp a frame (`lea rbp,[rsp-0x32d8]`); 0x294 is a byte shared by 14 bools. Value: none |
| F-44 | `BattleModeFrontThrottle` (0x2e4) | 50.0 / 0.5 | REJECTED ×2 | 50.0 → local `Vector3` at `rbp+0x2e0…0x2e8` passed as an argument; the other copies `[rbx+0x2d4]` into the field in an update chunk. Value: none |
| F-45 | `BattleModeRearThrottle` (0x2e8) | 50.0 | REJECTED | same local `Vector3` block. Value: none |
| F-57 | `AirControlYawTorqueFactorMin` (0x4b0) | 1200 | REJECTED | 1200 = 0x4b0 = offset. Value: none |
| F-60 | `AirControlTimeInAir` (0x4bc) | 1212 | REJECTED | 1212 = 0x4bc = offset. Value: none |
| F-61 | `BattleModeSlopeFactor` (0x4c0) | 1216 | REJECTED | 1216 = 0x4c0 = offset. Value: none |
| F-62 | `AirControlTurnTorque` (`RVehicleSimCar` 0x17c) | 15.0 / 0.5 / 0.001953125 / 0x40490fdb | REJECTED ×4 | two are frame stores; one stores `xmm6 × 0.001953125` onto a struct whose 0x170/0x184 are written as **ints** (class contradiction); one stores **π** to `[r12+0x17c]` where `r12` is not `this`, from a VA that starts mid-instruction. Value: none |
| F-63 | `StayUprightRollResistAngle` (`SVehicle` 0x6d4) | 1748 | REJECTED | 1748 = 0x6d4 = offset; also **0** store-form hits at 0x6d4 in the image. Value: none |
| F-64 | `StayUprightPitchResistAngle` (0x6d8) | 1752 | REJECTED | 1752 = 0x6d8 = offset. Value: none |

Provenance: every row stays with **no** provenance class — a confirmed native default would have
earned `class` (R4); nothing did. `FOOTAGE.md` was not edited, so all 14 rows keep `UNKNOWN` /
`VALUE-NATIVE` as they were.

## Why the model's 22 split

| failure family | n | detail |
|---|---:|---|
| its own offset map echoed as a value | 7 | JSON carries `"Member": <offset in decimal>`: 1200=0x4b0, 1212=0x4bc, 1216=0x4c0, 380=0x17c, 1748=0x6d4, 1752=0x6d8, 852=0x354 |
| its own package count echoed | 2 | `"BattleModeHeight": 1`, `"BattleModeSpeedDelta": 1` = one package contains the name |
| its own synthetic fixture | 1 | `selftest.jsonl:1`, `"source":"exe 0x1406a2b10 (synthetic)"`; real bytes are a hash-map lookup |
| store into a stack frame | 7 | `[rbp+disp]` where `rbp = lea rbp,[rsp-…]`, or a split chunk where `rbp` is never derived from `rcx` |
| store of a computed value | 5 | angle accumulation, `Vector3` delta, field copy, scaled live value, π immediate |

The reported numbers in the exe hits are always the nearest float constant *in the window*
(100.0, 50.0, 0.5, 0.001953125, 0x40490fdb) — the store's source operand was never traced.

## What was actually learned about the exe (useful beyond this audit)

- The image carries a **UE3 native-function table**: 16-byte `{char* name, void* fn}` records in
  `.rdata`, 5,737 entries, named `<Prefix><Class>exec<Function>`. That is the first symbol source in
  this otherwise stripped image, and it makes class attribution possible where the code is an exec
  function — but it names only 4 functions of `RVehicleSimBatmobile` (`execBoost`,
  `execSetDriveMode`, `execSetSuspensionForDriveMode`, `execSkidToStop`) and **none** of
  `RVehicleSimCar`, so it does not break the property-default wall chase-06/09 reported.
- `.pdata` gives exact function bounds (123,960 entries) and catches VAs that start mid-instruction
  (F-62#0032, F-18#0014) — the previous displacement scans could not.
- Offset-fit against a class layout is **not** attribution: both classes have long runs of
  consecutive floats, so a foreign struct matches 25–26 displacements. Each "well-matched" site here
  was refuted by one contradiction (a float read of a bool byte at 0x294, an int written to 0x170).

## Files

| path | change |
|---|---|
| `Research/BatmobileGrab/chase/chase-verify.md` | **new** — per-row and per-hit verdicts with the instruction bytes |
| `Tools/scripts/chase/chase_verify.py` | **new** — read-only re-derivation (`--hits`, `--va`, `--match`, `--symbols`, `--screen`, `--sample`, `--raw`, `--line`, `--sites`) |
| `MODLOG.md` | appended `## chase-verify — done (2026-10-29)` |
| `tmp/freebuff/reports/chase-verify.md` | this report |

## Limits

- "No literal, no initialiser" is proven per site. "No default exists" is **not** claimed for any row:
  the exe has no property-name strings, so an unnamed function's store at 0x2e4 stays unattributable
  and the rows remain `UNKNOWN`, not "zero".
- The `--screen` result (`literal=0` over 148 rejected exe hits) rules out immediate and RIP-constant
  stores to the exact displacement; a constant loaded into a register earlier would be classed
  "nonliteral". The 20-hit read-through found only per-frame updates in that class, but this is a
  screen, not a proof.
- Class attribution for F-44#0008 and F-62#0014 is *not* established; their verdicts rest on
  "not a literal, not an initialiser", which holds whatever the class is.

## Safety

`BatmanAK.exe` opened `rb` only. Nothing written under `E:\Games` or `D:\Games`; no game launched or
patched; `FOOTAGE.md`, the chase `chase-0N.md`/`chase2-0N.md` files and `GRAB_BACKLOG.md` untouched;
no commit, no push; no secret read.
