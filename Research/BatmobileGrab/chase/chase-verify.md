# Chase verify — audit of the local-LLM triage of the 235 G1 F-row hits

Scope: the 22 hits a local LLM marked `found: true` in `E:\Modding\_BmAKgrab\chase\verdicts.jsonl`
(inputs in `candidates.jsonl`, same ids), plus a 20-hit sample of the 213 it rejected. Every hit was
re-opened at the source it names: the cited text file line, or the cited `BatmanAK.exe` VA
(read-only). This pass changes **no** value: `FOOTAGE.md`, the chase files and `GRAB_BACKLOG.md`
are untouched. Nothing was launched, patched or written under either game folder.

**Result: 0 CONFIRMED, 22 REJECTED, 0 missed.** 14 F-rows are involved; all stay `UNKNOWN` —
the triage found no default value for any of them. Model precision on this run: **0 / 22 (0 %)**.
The rejection rate on the sample is not a precision figure: 20 of 20 rejected hits were correctly
rejected (0 misses), so on the 213 rejects the model is right so far as this pass can test.

## Result by row

| row | member (owner) | status in FOOTAGE | best value this pass can support | provenance | hits |
|---|---|---|---|---|---:|
| F-18 | `StrafeForce` (`RVehicleBatmobileBase`, 0x11f8) | UNKNOWN | **none** — no shipped file, no compiled initialiser for the class | none | 1 |
| F-23 | `TransformationAnimNode` (`RVehicleBatmobileBase`, 0x1494) | UNKNOWN | **none** — object ref, never serialised, no ctor | none | 1 |
| F-33 | `BattleModeHeight` (`RVehicleBatmobileBase`, 0x199c) | UNKNOWN | **none** | none | 1 |
| F-38 | `BattleModeSpeedDelta` (`RVehicleBatmobileBase`, 0x1eb4) | UNKNOWN | **none** | none | 1 |
| F-39 | `TurnOnSpotSteeringSpeedCurve` (`RVehicleSimBatmobile`, 0x268) | UNKNOWN | **none** — 0x268 is an `FInterpCurveFloat`, no scalar default exists | none | 4 |
| F-40 | `BattleModeMoving` (`RVehicleSimBatmobile`, 0x294) | UNKNOWN | **none** — bitfield byte, never written by code | none | 1 |
| F-44 | `BattleModeFrontThrottle` (`RVehicleSimBatmobile`, 0x2e4) | UNKNOWN | **none** — confirmed absent from the CDO (chase-06) | none | 2 |
| F-45 | `BattleModeRearThrottle` (`RVehicleSimBatmobile`, 0x2e8) | UNKNOWN | **none** — same | none | 1 |
| F-57 | `AirControlYawTorqueFactorMin` (`RVehicleSimBatmobile`, 0x4b0) | UNKNOWN | **none** | none | 1 |
| F-60 | `AirControlTimeInAir` (`RVehicleSimBatmobile`, 0x4bc) | UNKNOWN | **none** | none | 1 |
| F-61 | `BattleModeSlopeFactor` (`RVehicleSimBatmobile`, 0x4c0) | UNKNOWN | **none** | none | 1 |
| F-62 | `AirControlTurnTorque` (`RVehicleSimCar`, 0x17c) | UNKNOWN | **none** | none | 4 |
| F-63 | `StayUprightRollResistAngle` (`SVehicle`, 0x6d4) | UNKNOWN | **none** — and 0 store-form hits at 0x6d4 in the whole image | none | 1 |
| F-64 | `StayUprightPitchResistAngle` (`SVehicle`, 0x6d8) | UNKNOWN | **none** | none | 1 |

A confirmed value would have earned provenance `class` (R4: a native-C++ default). Nothing earned
it, so no row gains a provenance class.

## Verdict by hit

| id | claimed value | verdict | one-line ground |
|---|---|---|---|
| F-18#0014 | 250000.0 | **REJECTED** | source is the searcher's own *synthetic* fixture; the real bytes at 0x1406a2b10 are a hash-map lookup |
| F-23#0004 | 852 | **REJECTED** | 852 = 0x354 = a field **offset**, not a value (and the member is an object ref) |
| F-33#0002 | 1 | **REJECTED** | 1 = *number of packages containing the name*, not a value |
| F-38#0002 | 1 | **REJECTED** | same hit-count echo |
| F-39#0002 | 100.0 | **REJECTED** | value written is `old + 100.0` (wrapped to ±180) — a live heading; and 0x268 is an `FInterpCurveFloat` |
| F-39#0003 | 0.5 | **REJECTED** | store base is the **stack frame** (`lea rbp,[rax-0x248]`), into a local passed as an argument |
| F-39#0012 | (empty) | **REJECTED** | store base is the stack frame of a 19,025-byte function (255 distinct offsets off `rbp`) |
| F-39#0016 | 0.5 | **REJECTED** | `[rcx+0x268] = [rdx+0x14] - [rdx+8]`: the z of a `Vector3` written at 0x258/0x260/0x264/0x268 |
| F-40#0018 | 0.0 | **REJECTED** | `movss [rbp+0x294], xmm1`: stack frame, and a 4-byte float store into a `bool` bitfield byte |
| F-44#0004 | 50.0 | **REJECTED** | `[rbp+0x2e0/2e4/2e8] = 50.0` then passed as a `Vector3` argument — a local, not a field |
| F-44#0008 | 0.5 | **REJECTED** | `[rbx+0x2e4] = [rbx+0x2d4]` — copies another field; no literal; update chunk, not an initialiser |
| F-45#0007 | 50.0 | **REJECTED** | same local `Vector3` block as F-44#0004 |
| F-57#0008 | 1200 | **REJECTED** | 1200 = 0x4b0 = the field offset |
| F-60#0006 | 1212 | **REJECTED** | 1212 = 0x4bc = the field offset |
| F-61#0004 | 1216 | **REJECTED** | 1216 = 0x4c0 = the field offset |
| F-62#0007 | 15.0 | **REJECTED** | store base is the stack frame of a 6,339-byte function |
| F-62#0009 | 0.5 | **REJECTED** | same — `movss [rbp+0x17c], xmm1`, `rbp` a frame base |
| F-62#0014 | 0.001953125 | **REJECTED** | `xmm6 = xmm6 * [rip+0x190b918]` — a scaled live value; object's 0x170/0x184 are written as **ints**, contradicting the class |
| F-62#0032 | 0x40490fdb | **REJECTED** | claimed VA is 1 byte inside 0x1416faef9; that instruction stores **π** to `[r12+0x17c]`, and `r12` is not `this` |
| F-62#0035 | 380 | **REJECTED** | 380 = 0x17c = the field offset |
| F-63#0002 | 1748 | **REJECTED** | 1748 = 0x6d4 = the field offset |
| F-64#0002 | 1752 | **REJECTED** | 1752 = 0x6d8 = the field offset |

## Method (what makes an exe address testable)

`Tools/scripts/chase/chase_verify.py` (new, read-only) adds two things the earlier chases lacked:

1. **Exact function bounds** from the PE exception directory (`.pdata`): 123,960 runtime functions.
   Every claimed VA gets the function that *contains* it, so a VA that starts mid-instruction is
   reported as such instead of being disassembled from whatever byte happened to be there.
2. **The image's own native-function table**: 16-byte `{char* name, void* fn}` records in `.rdata`
   whose names are spelled `<Prefix><Class>exec<Function>` (5,737 entries). This is the first
   symbol source found in this exe — chase-09's "no symbol in the exe" holds only for *property*
   names (confirmed again: `BattleModeFrontThrottle`, `TurnOnSpotSteeringSpeedCurve` absent).

A verdict of CONFIRMED would additionally need: the instruction stores a literal (an immediate or a
RIP-referenced float) into the field's displacement, **and** the containing function is an
initialiser of the owning class — evidenced by a constructor shape (base-class call, vtable store,
contiguous field writes) or by the native table naming it for that class. No hit meets even the
first condition.

Class-shape is *not* by itself evidence: the two classes involved have long runs of consecutive
floats, so a foreign struct matches most displacements by accident. Both "well-matched" layouts
below are refuted by one contradiction each (0x294 read as a float where the class has 14 bools;
0x170 written as int `0x100` where the class has a float).

## Evidence, hit by hit

### The seven offset echoes and two count echoes (F-23, F-57, F-60, F-61, F-62#0035, F-63, F-64, F-33, F-38)

All nine quote the searcher's own JSON bookkeeping, not game data. In `value_cdo_08.json` the
"value" of each member is its **BmSDK offset in decimal**:

```
AirControlYawTorqueFactorMin  json 1200  = 0x4b0   MATCH
AirControlTimeInAir           json 1212  = 0x4bc   MATCH
BattleModeSlopeFactor         json 1216  = 0x4c0   MATCH
AirControlTurnTorque          json  380  = 0x17c   MATCH
StayUprightRollResistAngle    json 1748  = 0x6d4   MATCH
StayUprightPitchResistAngle   json 1752  = 0x6d8   MATCH
```

(`sim_cdo_07.json`'s `TransformationAnimNode: 852` is 0x354 — the offset of the same member as
declared on `RVehicleSimBatmobile`, not on `RVehicleBatmobileBase` where the row lives at 0x1494. So
it is an offset from a *different class's* target map, which is worse than a value: it is not even
the row's own number.)

In `namescan_b.json` the numbers are **how many packages contain the name**:

```
"names": ["BattleModeHeight", "JumpRampUpwardForce", …]          # name list
"packages_with_a_hit": {"GlobalPersistentCookerData.upk": {"BattleModeHeight": 1, …}}
```

`1` is a file count. `candidates.jsonl` even records the same text twice per row — once at the name
list (rejected) and once at the count (accepted) — which is how the error is visible.

### F-18#0014 — the searcher read its own fixture

`source: E:/Modding/_BmAKgrab/chase/selftest.jsonl:1`, and the record itself says
`"source":"exe 0x1406a2b10 (synthetic)"`. The bytes at that VA are the middle of a 143-byte
hash-map lookup (`0x1406a2ad0 .. 0x1406a2b5f`):

```
>> 0x1406a2b0f  mov  eax, dword ptr [r9 + rcx*4]
   0x1406a2b13  cmp  eax, -1
   0x1406a2b16  je   0x1406a2b37
   0x1406a2b18  mov  r8, qword ptr [r10]
   0x1406a2b20  movsxd rcx, eax
   0x1406a2b23  lea  rdx, [rcx + rcx*2]
   0x1406a2b27  cmp  qword ptr [r8 + rdx*8], r11
```

No store, no prologue, no vtable, no RIP float; the claimed VA does not even start an instruction.
The fixture's `call 0x1402f0000 ; RVehicle::RVehicle` / `lea rax,[rip] ; vtable
RVehicleBatmobileBase` comments are hand-written — a stripped image contains no such annotations.

**And the class has no compiled initialiser to be found.** The control chase-03 used still holds:

```
0x1cf8 VehicleShovingTorque (10000 in all four archetypes)   0 store-form hits
0x1fdc PMDodgeTorque (6000)                                  0
0x1fe0 PMDodgeForce (10000)                                  0
0x1fe4 PMDodgeDuration (0.15)                                0
0x11f8 F-18 StrafeForce                                     10   (other classes' layouts)
```

Four members whose shipped values are known from the archetypes are never written by code, so
`RVehicleBatmobileBase` is data-initialised only; the 10 hits at 0x11f8 belong to other classes.

### F-39 — four sites, three frames and one angle accumulator

```
0x140034dc3  fn 0x140034b30..0x140034eff, rcx spilled to rdi
   0x140034d8f  movss xmm1, [rdi + 0x268]
   0x140034d97  movaps xmm7, xmm1
   0x140034da2  addss xmm1, [rip+0x1be7b6e]   ; 100.0
   0x140034daa  movss [rdi + 0x268], xmm1
   0x140034db2  comiss xmm1, [rip+0x1b9bf83]  ; 180.0
   0x140034dbb  subss xmm1, [rip+0x1b9bf75]   ; 360.0
>> 0x140034dc3  movss [rdi + 0x268], xmm1
```

That is a heading that advances by 100 °/tick and wraps at ±180 — the stored value is whatever the
angle currently is, not 100.0. On `RVehicleSimBatmobile`, 0x268 is `TurnOnSpotSteeringSpeedCurve`
(`FInterpCurveFloat`, 0x268…0x27c, a `TArray` + interp method); a 4-byte scalar store to its first
word is not that member under any reading.

The other three write the same displacement off a **frame pointer**, inside functions that use
hundreds of locals:

| VA | function | how the base is established |
|---|---|---|
| 0x14014698f | 0x140146450, 567 ins | `0x140146464 lea rbp, [rax - 0x248]` (rax = rsp on entry) — `rdx = lea rbp+0x108` is then passed to a call |
| 0x140788c7c | 0x1407851b8, 3,723 ins | `rbp` never assigned in the chunk (a split fragment); 813 accesses, **255 distinct** displacements ≥0x100 |
| 0x140dfbadb | no `.pdata` entry (leaf tail-fragment) | `movss [rcx+0x268], xmm0`, `xmm0 = [rdx+0x14] − [rdx+8]`, after `movups [rcx+0x258]` and stores at 0x260/0x264 |

### F-40 / F-44 / F-45 — a local `Vector3` and a bool that gets a float

```
0x1417492e9  fn 0x141748360..0x14174ae75, 2,143 ins
   0x141748383  lea rbp, [rsp - 0x32d8]
>> 0x1417492e9  movss [rbp + 0x294], xmm1        ; 429 accesses off rbp, 184 distinct
```

```
0x14016b9e0 / 0x14016b9e8   fn 0x140169e10..0x14016dbef, 3,034 ins
   0x140169e2a  lea rbp, [rax - 0x858]
   0x14016b9d0  movss xmm7, [rip + 0x1a63b64]   ; 50.0
   0x14016b9d8  movss [rbp + 0x2e0], xmm7
>> 0x14016b9e0  movss [rbp + 0x2e4], xmm7
>> 0x14016b9e8  movss [rbp + 0x2e8], xmm7
   0x14016ba2c  lea r9, [rbp + 0x2e0]            ; passed as an argument
```

Three consecutive words set to 50.0 and then handed to a call as one `Vector3` — a local, so the
displacements coincide with the class's throttle floats and mean nothing. `BattleModeMoving` is a
`bool` sharing byte 0x294 with 13 other flags; a `movss` there is a 4-byte overwrite of the byte plus
`BoostDuration`'s first three bytes.

### F-44#0008 — class-shaped, still not a default

```
0x14024f094  fn 0x14024ee04..0x14024f2fc (split chunk, 256 ins)
   0x14024ee4e  mulss xmm1, xmm3
   0x14024f06a  movss xmm0, [rbx + 0x2d4]     ; BattleModeLatSlipScale
   0x14024f072  movss xmm2, [rip+0x1972476]   ; 0.5
   0x14024f08c  movss [rbx + 0x2e0], xmm1
>> 0x14024f094  movss [rbx + 0x2e4], xmm0     ; = the value of 0x2d4
```

The stored value is another field's, so the "0.5" the model reports is a constant compared three
instructions later. The chunk has no vtable store and no base-class call, and writes `0x2bc` with
`and`/`or` and reads `0x294` with `movss` — both contradict the class's declared types (a float and
14 bools), so the object is not demonstrably `RVehicleSimBatmobile` either. Even if it were, a
per-tick copy is not a default.

### F-62 — two frames, one scaled live value, one π

| VA | what the instruction actually is |
|---|---|
| 0x140775b71 | `movss [rbp+0x17c], xmm6` in a 6,339-byte function; `rbp` never derived from `rcx` (236 accesses, 60 distinct) — frame |
| 0x14077ce98 | `movss [rbp+0x17c], xmm1` in a 7,509-byte function; same — frame |
| 0x140815ba2 | `movss [rbx+0x17c], xmm6`, `rbx = rcx`; `xmm6 = xmm6 * [0x1421214a8] = 0.001953125`, i.e. the model read the **multiplier**, not the stored value, and the same block writes `[rbx+0x170] = 0x100` / `[rbx+0x184] = 0x200` **as ints** where the class declares floats — live state, not the class |
| 0x1416faefa | **no instruction starts there** (1 byte into 0x1416faef9): `mov dword [r12+0x17c], 0x40490fdb` = 3.1415927f; `rcx` is spilled to `r13`, so `r12` is not `this` |

### One pattern behind all five "computed" hits

Each exe hit the model accepted stores a register, and the number it reported is the nearest float
*constant in the same window*: 100.0 is the step added to the angle (F-39#0002), 50.0 is the local
`Vector3` fill (F-44#0004/F-45#0007), 0.5 is a comparison operand three instructions later
(F-44#0008), 0.001953125 is the scale multiplied into the value (F-62#0014), 0x40490fdb is π stored
as an immediate (F-62#0032). The store's *source* was never traced, which is the one step that
turns "a constant is nearby" into "this field's default is that constant".

## Missed finds: the sample and the whole pool

`python Tools/scripts/chase/chase_verify.py --sample 20 --seed 20261029` (pool 213, seed fixed for
re-runs). The 20: F-45#0013, F-44#0005, F-33#0001, F-58#0007, F-40#0001, F-44#0010, F-39#0004,
F-21#0003, F-62#0011, F-61#0003, F-62#0002, F-40#0021, F-18#0005, F-62#0028, F-37#0005, F-62#0003,
F-40#0022, F-37#0002, F-19#0002, F-34#0002.

Every one is correctly rejected: the exe ones are loads, increments (`[rcx+0x4bc] += dt`), field
copies or setters, and the text ones are names, hit counts or offset maps. **No miss in the 20.**

Because the sample is small next to 213, the whole pool was also screened mechanically:

```
$ python Tools/scripts/chase/chase_verify.py --screen
found=false exe hits: 148
   va_bad=7  not_store=2  wrong_disp=0  stack=50  nonliteral=89  literal=0
```

Zero of the 148 rejected exe hits is a store of a literal to the row's displacement (50 are stores
into a stack frame; 89 store a register whose value is computed). The 65 text rejects were read by
hand: 60 are the searcher's own JSON (name lists, counts, offset maps), 4 are input bindings
(`Bindings=(Name="StrafeRight", …)`, an input command, not a field), and 1 more is a repeat.

## Limits / UNKNOWNs of this pass

1. "No literal, no initialiser" is proven per site for the 22 found hits; the wider "no default
   exists" claim is **not** made for any row. The exe is stripped of property names, so a store to
   0x2e4 in a function the native table does not name stays unattributable — the same wall
   chase-06 and chase-09 hit. Rows stay `UNKNOWN`, not "zero".
2. The native table names 5,737 functions for the whole image and only **4** for
   `RVehicleSimBatmobile` (`execBoost`, `execSetDriveMode`, `execSetSuspensionForDriveMode`,
   `execSkidToStop`) and **none** for `RVehicleSimCar`, so class attribution by symbol is available
   only where the row's code happens to be an exec function.
3. Offset-fit is weak evidence: both classes have long runs of consecutive floats, so 25–26 of a
   function's displacements match "exact field start" for a foreign struct too. Where the fit was
   used it is paired with a contradiction (a float read of a bool byte, an int written into a
   float) and never used alone.
4. `.pdata` is not complete for leaf/tail fragments (0x140dfbadb has no entry) and some entries are
   hot/cold chunks of a larger function (F-39#0012, F-44#0008), where `rbp`/`rbx` are established
   in the part not covered by the entry. Both were handled by inspecting raw bytes rather than
   trusting the boundary.
5. The screen's "literal=0" covers immediates and RIP-referenced floats only; a constant loaded
   into a register several instructions earlier and then stored would be classed "nonliteral". The
   20-hit read-through found only per-frame updates in that class, but it is a screen, not a proof.
6. Nothing here changes `FOOTAGE.md`: every one of the 14 rows is still `UNKNOWN` / `VALUE-NATIVE`,
   and the reason narrows for none of them (no new evidence of any kind about a default appears).

## Commands this pass ran (all read-only, all re-runnable)

```
python Tools/scripts/chase/chase_verify.py --hits
python Tools/scripts/chase/chase_verify.py --va 0x140034dc3 0x14014698f 0x140788c7c 0x140dfbadb
python Tools/scripts/chase/chase_verify.py --va 0x1417492e9 0x14016b9e0 0x14016b9e8 0x14024f094
python Tools/scripts/chase/chase_verify.py --va 0x140775b71 0x14077ce98 0x140815ba2 0x1416faefa
python Tools/scripts/chase/chase_verify.py --va 0x1406a2b10
python Tools/scripts/chase/chase_verify.py --symbols RVehicleSimBatmobile
python Tools/scripts/chase/chase_verify.py --match 0x140815ba2 RVehicleSimCar rbx
python Tools/scripts/chase/chase_verify.py --match 0x14024f094 RVehicleSimBatmobile rbx
python Tools/scripts/chase/chase_verify.py --screen
python Tools/scripts/chase/chase_verify.py --sample 20 --seed 20261029
```

Exe: `E:\Games\Batman - Arkham Knight\Binaries\Win64\BatmanAK.exe`, 55,101,440 B, image base
0x140000000, 7 sections, 123,960 `.pdata` functions, 5,737 named natives.
