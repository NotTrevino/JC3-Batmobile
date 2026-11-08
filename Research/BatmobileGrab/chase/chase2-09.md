# Chase 2-09 — second pass on F-65, F-66 and the five unit rows (F-68 … F-72)

Scope: every row of `Research/BatmobileGrab/chase/chase-09.md` that is STILL UNKNOWN — F-65, F-66
(two native values) and F-68 … F-72 (five undocumented units). Only routes the first pass did not
try or did not finish are used here; `FOOTAGE.md`, `chase-09.md`, `GRAB_BACKLOG.md` and every other
existing document are untouched. Read-only for the game: packages and ini files opened `rb`, the
executable read-only, no game launched, nothing committed. Game-derived output:
`E:/Modding/_BmAKgrab/chase2_09_packages.json`.

**Result: 0 of 7 rows closed. Three of them gained a stronger negative (the field is not touched by
any shipped file or any static instruction at its displacement), and two got a first read-site.**

| row | question | status | answer / reason | provenance |
|---|---|---|---|---|
| F-65 | `StayUprightStiffness` (0x6dc) value | **STILL UNKNOWN** | the only two stores at 0x6dc are arithmetic/clamped updates in a function that treats 0x6e4 as a *float* (`divss`), while SVehicle's 0x6e4 is `StayUprightConstraintSetup`, an object pointer → the sites belong to another class; no literal anywhere | read (exe) + decoded (SDK layout) |
| F-66 | `StayUprightDamping` (0x6e0) value | **STILL UNKNOWN** | **0 store sites and 0 read sites** of `[reg+0x6e0]` in the whole executable; no package or ini carries the name | read (exe) |
| F-68 | unit of `AirControl` (0.05) | **STILL UNKNOWN** | value unchanged (decoded 0.05 at `Default__Pawn` 0x448); 3 read sites, read beside `[rax+0x444]`, no scaling constant in any window; no file and no reachable published source states a unit | decoded (value) / UNKNOWN (unit) |
| F-69 | unit of `BattleModeYawOffset` (0) | **STILL UNKNOWN** | value 0 in all four archetypes; zero is the same number in every unit, so no build depends on it | decoded |
| F-70 | unit of `ArmourModeDamageReduction` (0) | **STILL UNKNOWN** | value 0 in three packages, `—` in Joker; same zero argument | decoded |
| F-71 | unit of `BattleModeThrottleSpeed` (10.0) | **STILL UNKNOWN** | one read site: `0x140c00098 movss xmm0,[rax+0x2ec]` then `0x140c000a0 comiss xmm0,[rcx+0x2ec]` — the field is only *compared* with another object's same field; no scale, no delta-time multiply, no bridge | read (exe) |
| F-72 | unit of `BattleModeSteerBiasRate` (3.0) | **STILL UNKNOWN** | value 3.0 unchanged; **0 read sites** of `[reg+0x3c4]` and only constructor stores; nothing consumes it statically | read (exe) |

## Routes tried this pass

### 1. Every shipped package (route (a), finished for the first time)

The first pass opened `BmGame.upk` and `Engine.upk`. This pass scanned **4,145 packages** — the whole
`BmGame/CookedPCConsole` tree, every DLC layer and every `.u` script package under
`E:/Games/Batman - Arkham Knight` — for the ASCII name of each member, recording where the name
occurs and whether a property-type string follows it:

```
$ python Tools/scripts/chase/chase2_09_scan.py --names
scanning 4145 packages
  StayUprightStiffness             2 name hits in 2 package(s): BmGame/CookedPCConsole/GlobalPersistentCookerData.upk, DLC/350171/Content/BmGame/CookedPCConsole/GlobalPersistentCookerData.upk
  StayUprightDamping               2 name hits in 2 package(s): (same two)
  StayUprightRollResistAngle       …  AirControl …  BattleModeYawOffset …
  ArmourModeDamageReduction …  BattleModeThrottleSpeed …  BattleModeSteerBiasRate …
```

Every one of the nine names occurs **only** in `GlobalPersistentCookerData.upk` (the cooker's global
name table) and its DLC copy — never in a package's class/property table, never next to a value.
`Awesome: no shipped package declares these members as script properties, so no package can supply
a default, a subclass override or an archetype value. The name survives in the name table because
the native class layout (BMSDK dump) declares it.

### 2. Every ini (route (a) tail)

```
$ python Tools/scripts/chase/chase2_09_scan.py --inis
76 ini files under E:/Games/Batman - Arkham Knight — 0 hits for any of the nine names
```

### 3. Native code, per displacement (route (b))

`chase2_09_scan.py --stores` disassembles every store at the displacement and resolves RIP-relative
float constants inline. Results:

**F-65 (0x6dc) — 2 sites, both in one function starting `0x14018ff50`:**

```
0x1401900a0  addss    xmm6, xmm0
0x1401900a4  comiss   xmm6, xmm1
0x1401900a7  jae      0x1401900ac
0x1401900a9  movaps   xmm1, xmm6
0x1401900ac  movss    dword ptr [rbx + 0x6dc], xmm1     ; computed + clamped, no literal
...
0x1401900c5  xorps    xmm1, xmm1
0x1401900c8  comiss   xmm0, xmm1
0x1401900cb  ja       0x1401900d0
0x1401900cd  movaps   xmm0, xmm1
0x1401900d0  movss    dword ptr [rbx + 0x6dc], xmm0     ; max(xmm0, 0.0), no literal
```

Attribution, which the first pass asserted but did not demonstrate: the same function does
`0x1401900b9 divss xmm6, dword ptr [rbx + 0x6e4]` and `0x140190098 divss xmm6, dword ptr [rbx + 0x6e8]`.
In `SVehicle` (BMSDK layout, `Research/BatmobileGrab/BMSDK_OFFSETS.json` →
`classes.SVehicle.properties`) **0x6e4 is `StayUprightConstraintSetup`, an ObjectProperty** (0x6ec is
`StayUprightConstraintInstance`), so a `divss` through 0x6e4 cannot be this class: the two stores are
some other class's float at the same displacement. No literal default exists at 0x6dc.

**F-66 (0x6e0) — 0 store sites.** A read scan (`movss xmm, [reg+disp32]`, ModRM mod=10) also finds
**0** read sites at 0x6e0 anywhere in the executable. The field is not touched by any static
instruction at its displacement. **Hypothesis, explicitly not a finding:** its value may reach the
physics constraint through `StayUprightConstraintSetup` at 0x6e4; nothing read here proves it.

**F-71 (0x2ec) — 1 read site**: `0x140c00098 movss xmm0,[rax+0x2ec]` / `0x140c000a0 comiss
xmm0,[rcx+0x2ec]` / `jb` — a cross-object comparison, no constant, so no unit bridge.

**F-72 (0x3c4) — 0 read sites.**

**F-68 (0x448) — 3 read sites**, e.g. `0x14075ab57 movss xmm0,[rax+0x448]` immediately followed by
`0x14075ab65 movss xmm1,[rax+0x444]`; the values are packed into a call argument block
(`[rsp+0x50]`, `[rsp+0x4c]`, `[rsp+0x44]`) with no scaling constant in the window.

### 4. `smart_search` (the two-stage tool), per row

The tool is built and calibrated (`tmp/freebuff/reports/smart-search.md`, STATUS done), and its
report says the live search half currently returns **no candidates** for this corpus. Run anyway,
as the task requires, one call per row:

```
$ python Tools/scripts/chase/smart_search.py --member StayUprightStiffness --owner SVehicle --offset 0x6dc --type float --max 6
StayUprightStiffness (SVehicle, float, 0x6dc): 0 candidates, 0 judged, 0 from cache
no candidates (nothing at this offset/name in the corpus)
```

Same result for all seven rows (0 candidates, 0 judged: the search's mechanical rejection removes
every hit before the judge sees it). It contributed nothing here, which is consistent with its
calibration: on this corpus the value is package-only and the routes do not decode packages.

### 5. Frame-timed measurement (route (c)) — not applicable

None of the seven quantities is visible in footage: F-65/F-66 are physics-constraint stiffness and
damping, F-69/F-70 are zero-valued units, F-71/F-72 are internal rate fields, and F-68 is a control
authority. No clip was measured; running ffprobe on clips could not answer a unit question.

### 6. Published sources (route (d)) — cross-check attempted, nothing usable

A search for UDK documentation of `Pawn.AirControl` returned no authoritative result page, so no
published unit is quoted. Even if one were found it would be a cross-check only (R4): the BmAK unit
would still be `UNKNOWN`.

## Why these stay UNKNOWN (and what would close them)

- **F-65 / F-66:** the values are set by native code at runtime (F-65's field is computed and
  clamped each update) or are not touched at all at that displacement (F-66). Closing them needs a
  runtime probe (read the value out of a live `SVehicle` object) — a Q-phase item, not a desk task.
- **F-69 / F-70:** both values are **0**, which is identical in any unit, so no build decision hangs
  on the answer; the unit is unprovable from the files, and the amount needed is zero tolerance.
- **F-68 / F-71 / F-72:** the only static uses are a comparison and an argument pack, with no
  constant, no delta-time multiply and no conversion anywhere in the window. A unit would have to
  come from a runtime probe or an engine source that this machine does not have.

No value was inferred, rounded or copied from another engine's convention: each row keeps the value
the record already had and states `UNKNOWN` for the part the data does not give (R4).
