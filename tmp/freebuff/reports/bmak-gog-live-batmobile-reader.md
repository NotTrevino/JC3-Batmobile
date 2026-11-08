# BmAK GOG live Batmobile reader — `Tools/scripts/bmak_live_read.py`

**STATUS: partial.** The reader is written, its offset table is machine-checked against the two grab JSONs
(`--check`: 0 problems), and its live values are **UNKNOWN because `BatmanAK.exe` is not running**. Nothing was
launched, attached, injected or written by this task; the GOG exe was only stat-ed (`exists: True`). No JC3
process was looked at. The script contains no `WriteProcessMemory` reference at all.

The brief allowed launching `E:\Games\BmAK-GOG-sdk\Binaries\Win64\BatmanAK.exe` for read-only scraping, and the
brief also says that if the game is not running the values are UNKNOWN and the exact run steps are written
instead. Arkham Knight has no headless mode: a launch would spend the operator's session on a game nobody is
driving, and the six values only exist once the Batmobile is spawned and moving. So the run steps are below and
the values are UNKNOWN — not zero, not guessed.

---

## 1. What was written

| file | what it is |
|---|---|
| `Tools/scripts/bmak_live_read.py` | the reader: `--check` (no game), `--selftest` (walker oracle), default read, `--json PATH`, `--any-build` (guard bypass, unused) |
| `tmp/freebuff/reports/bmak-gog-live-batmobile-reader.md` | this report |

Nothing else in the repo was modified.

## 2. Method (read-only, two primitives, no code addresses)

```
OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION)   pid = the only BatmanAK.exe
image path must start with E:\Games\BmAK-GOG-sdk                   (else SystemExit; --any-build overrides)
GNames     = module_base + 0x3A8E978    -> TArray<FNameEntry*>; entry 0 must be "None" (validated, else stop)
GObjObjects= module_base + 0x347ACA4    -> inline UObject* array; a live slot holds its own index at +0x30
UObject    = +0x08 flags, +0x3C FName index/number, +0x44 Class          (BmSDK UObject.h, already used here)
FNameEntry = +0 inline text, or bit 0x2 -> +0x0C pointer to text          (BmSDK FName.cs)
```

Both globals are the ones `tmp/freebuff/reports/bmsdk-gog-address-hunt.md` records as **runtime-validated for
this GOG build** (`inline constexpr uintptr_t GNames = 0x3A8E978;` line 286, `GObjObjects = 0x347ACA4;` line 287).
`--check` re-reads those two lines from that report and fails if the script's constants differ — the constants
are not free-floating numbers.

The walk is `bmak_runtime_sampler.py`'s walk (same file layout, same validation), extended in this script
because the sampler drops class defaults and only keeps wanted classes:

* `walk()` reads 4096 slots at a time, keeps a slot only when `UObject.Index == slot number`, records the class
  name of every object, and also builds an address → (class, name) map for `PhysicsAsset` objects.
* `live()` drops `RF_CDO` objects when real instances exist, so a class template is never read as the value.
* Property **names, offsets, kinds and types are read at run time from
  `Research/BatmobileGrab/BMSDK_OFFSETS.json`** (41 classes, schema 1, generated from `Team-BmSDK/BmSDK-AK`
  `main-bm4`, MIT). The script holds only the class+member names in its `SPEC`; `--check` recomputes all 25
  offsets from that JSON and asserts the property kind matches the decoder.
* Inherited offsets: `RVehicleBatmobileBase` members are read from a `RVehicleBatmobile` instance, and
  `RVehicleSimCar` members from a `RVehicleSimBatmobile` instance, because UE3 keeps an inherited property's
  offset in the child. This is the same assumption `bmak_runtime_sampler2.py` already relies on.

`Research/BatmobileGrab/OFFSETS.json` (the package-grab side, 423 field rows) is read only for a cross-file
check: it lists the same class names (`class only` — it does not carry these property offsets), which is what
`--check` prints per item.

### How each of the six is decoded

| # | value | member read (class, offset from JSON) | decoder |
|---|---|---|---|
| V1 | LT battle-mode hold time | `RVehicleBatmobileBase.PreventModeSwitchDuration` +6544 float; `LastBattleModeControlledTime` +7852; `bBattleModeControlled` word | scalar / bool-word hex |
| V2 | eject charge window | `MaxEjectType` +5902 byte (enum `EBatmobileEjectType`), `EjectUpDist` +6032 float; carriers `RVehicleBatmobile.EjectUpMove` +8416, `EjectToSpotMove` +8496, `EjectForwardMove` +8424 (all `RSpecialMoveConfig*`) | byte / float / pointer resolved to `Class:Name` |
| V3 | steering curve at speed | `RVehicleSimBatmobile.StandardSteeringSpeedCurve` +576, `BoostSteeringSpeedCurve` +556, `HandbrakeSteeringSpeedCurve` +596 (`FInterpCurveFloat`); `RVehicleSimCar.SteerSpeedVsSpeedCurve` +404, `SteeringReductionFactor` +324, `SteeringReductionSpeed` +340; `BattleModeSteerAngleFactor` +768 | `TArray{Data,Num,Max}` + points; the 20-byte point stride (`InVal,OutVal,Arrive,Leave` + `InterpMode` byte) is **derived** and accepted only if it validates (InVal non-decreasing, `InterpMode <= 4`, magnitudes sane) — otherwise the raw floats are printed and the parse is marked rejected |
| V4 | `HealthRecoverRate` | `RVehicleBatmobileBase.HealthRecoverRate` +8220, `ArrayProperty` of `float` | `TArray` header + up to 128 floats |
| V5 | summon / homing numbers | `RemoteCallIn` word +4572, `RemoteSafePointLocation` +6512 / `RemoteSafePointRotation` +6524 (`Vector3`), `RBatmobileMissile.HomingDelay` +1060 float, `bHoming` word +1056 | word hex / 3 floats / float |
| V6 | physics asset in use | `BatmobileViewMesh` component pointer +5716, then the component's first `0x600` bytes scanned at 8-byte alignment for any pointer that lands on a live object of class **`PhysicsAsset`** (class name from GNames, no guessed component offset); every `PhysicsAsset` object named `*batmobile*` is listed too | pointer scan with class-name oracle |

**Role labels in the output matter.** `value` = the member is the quantity; `nearest` = the closest decoded
member when the exact one does not exist; `carrier` = an object that owns the quantity; `context` = adjacent
readable state. V1 and V2 have no `value` row: **`BMSDK_OFFSETS.json` has no `*HoldTime`, `ModeSwitchHold`,
`EjectCharge*` or `ChargeTime` member on any of its 41 classes**, so the LT hold duration and the eject charge
window are printed as UNKNOWN with their nearest/carrier members beside them. (`ChargeTime` in that JSON is
`RVehicleSimBatmobile.SlipstreamChargeTime` +872 — boost slipstream, not the eject charge.)

## 3. Selftest plan (three classes, two independent oracles)

`--selftest` walks `GObjObjects` once and checks, per class:

1. a `UClass` object named `RVehicleBatmobile` / `RVehicleSimBatmobile` / `RBatmobileMissileLauncher` exists
   under class **`Class`** (the class object is found by name through GNames and its own `Class` field must read
   `Class` — an address-independent consistency check);
2. the class-default object `Default__<class>` exists **under that same class** — e.g.
   `Default__RVehicleBatmobile` must report `Class` = `RVehicleBatmobile`.

All three names are known from the grab (`BMSDK_OFFSETS.json` classes; `OFFSETS.json` evidence records the
`Default__RVehicleBatmobile` imports). If any of the six assertions fails, the walker is wrong and the six
values would be meaningless — the reader exits **4** without printing values. Expected output shape:

```
walked <n> object slots; found class objects for [...]
  RVehicleBatmobile: UClass objects 1 at ['0x...']; CDOs 1 at ['0x...']
  ...
selftest: PASS
```

## 4. Exact run steps (operator)

```
1. start the GOG copy:   "E:\Games\BmAK-GOG-sdk\Binaries\Win64\BatmanAK.exe"
   (exe present, 55,101,440 bytes, PE 0x6508b1ce; launching it for read-only scraping was approved 7993-7994)
2. spawn the Batmobile and drive it (a still car never writes the steering curve / regen values)
3. in another shell:
     cd E:\Modding\JC3-Batmobile
     uv run python Tools/scripts/bmak_live_read.py --selftest
     uv run python Tools/scripts/bmak_live_read.py --json Research/BatmobileGrab/live_batmobile.json
4. read the six blocks V1..V6, then the UNKNOWN footer
5. stop: close the game yourself. This script never kills anything; if a kill is ever needed it is
   taskkill /PID <the exact pid this script prints> — never by image name.
```

## 5. Values read

**All six: UNKNOWN.** No process was attached in this session; `BatmanAK.exe` is not running. What the reader
will print when it is running is fixed by §2; what it cannot print even then is listed in §7.

## 6. Ledger rows each value feeds

The join is a keyword match against `tmp/freebuff/pre_t10/T_ROWS.jsonl` (105 rows), printed by `--check` — it is
a join, not a semantic claim; the section headers below are quoted from the rows.

| value | rows matched | note |
|---|---|---|
| V1 battle-mode hold | `T-BM1`, `T-LG5`, `T-AU5` | `T-BM1` is the battle-mode row ("`BattleMode*` (9), `TurnOnSpot*` (3), `TransformationTurn*`…"); `T-LG5` lights / battle-mode rigs; `T-AU5` transformation sounds |
| V2 eject charge | **none — GAP** | no row in the 105 mentions ejection. The charge window needs a new row: nothing in the ledger currently owns it. |
| V3 steering curve | `T-ST1`, `T-ST2`, `T-ST3`, `T-ST4`, `T-ST5`, `T-ST6`, `T-ST7`, `T-R1`, `T-PA4` | §6 "Steering — BmAK's numbers exist…"; `T-ST7` already names `SteerSpeed 220 °/s`, `SpinSteeringFactor`, and the curve knots `InVal/OutVal/ArriveTangent/LeaveTangent` |
| V4 regen | `T-DM1`, `T-DM8`, `T-DM9`, `T-P2`, `T-FX2`, `T-PA9` | damage/health rows (keyword hit on "health"); no row names a regen *rate* |
| V5 summon/homing | `T-W1`, `T-DM9` | weapons row + damage row |
| V6 physics asset | `T-B4`, `T-P3`, `T-CO1` | collision/physics rows |

## 7. Commands run, verbatim

```
$ python Tools/scripts/bmak_live_read.py --check
BMSDK_OFFSETS.json schema 1, source {'branch': 'main-bm4', 'license': 'MIT', 'note': 'Generated C# bindings;
each property carries the offset the engine linked it to, ...', 'repo': 'https://github.com/Team-BmSDK/BmSDK-AK'}
41 classes
spec items resolved: 25; unresolved: 0
GNames 0x3A8E978 == bmsdk-gog-address-hunt.md
GObjObjects 0x347ACA4 == bmsdk-gog-address-hunt.md
V1 'LT battle-mode hold time': ledger rows ['T-LG5', 'T-AU5', 'T-BM1']
V2 'eject charge window (hold A to charge, tap A higher)': ledger rows NONE
V3 'steering curve at speed': ledger rows ['T-R1', 'T-ST1', 'T-ST2', 'T-ST3', 'T-ST4', 'T-ST5', 'T-ST6', 'T-PA4', 'T-ST7']
V4 'HealthRecoverRate (regen)': ledger rows ['T-P2', 'T-FX2', 'T-DM1', 'T-DM8', 'T-DM9', 'T-PA9']
V5 'summon / homing numbers': ledger rows ['T-DM9', 'T-W1']
V6 'physics asset the running car uses': ledger rows ['T-B4', 'T-P3', 'T-CO1']
ledger GAPs (value feeds no existing row - a new row is needed): ['V2 (eject charge window (hold A to charge, tap A higher))']
  cross-file: RVehicleBatmobile.EjectUpMove class only
  ... (9 more "class only" lines, one per member absent from OFFSETS.json's field rows)
--check: 0 problem(s), 1 ledger gap(s)
CHECK_EXIT=0

$ python Tools/scripts/bmak_live_read.py
BatmanAK.exe is not running, so the six values are UNKNOWN. ...
Expected exe path: E:\Games\BmAK-GOG-sdk\Binaries\Win64\BatmanAK.exe (exists: True)
RUN_EXIT=3
```

## 8. UNKNOWNs

1. **All six live values** — no process attached; §4 is how they are obtained.
2. **The LT hold duration as such.** No member in `BMSDK_OFFSETS.json` or `OFFSETS.json` is named for it. It may
   be a literal in `RPlayerController`/`RPlayerInput` code (neither class is in the 41) or a `UISettings`/config
   value. 5-minute experiment: read `PreventModeSwitchDuration` (already in the reader) against a stopwatch on a
   held LT; if it does not track the hold, the duration is code-side and needs a function address this build does
   not have.
3. **The eject charge window as such.** `MaxEjectType`/`EjectUpDist` are decoded; the four eject
   `RSpecialMoveConfig` carriers are named (the reader resolves them to `Class:Name`), but `RSpecialMoveConfig`'s
   own properties are not in either JSON, so the window duration inside them is unseen.
4. **Whether the `FInterpCurveFloat` point stride is 20 bytes in this build.** Derived, validated at read time
   by the InVal/InterpMode test; a rejection is printed rather than hidden.
5. **Whether `PhysicsAsset` objects are named per Batmobile** — the class-name scan is exact, the naming is not
   assumed; if the scan finds nothing the reader says so instead of picking a nearby pointer.
6. **Whether the GOG build's linked property offsets equal `BMSDK_OFFSETS.json`'s.** That JSON is generated from
   the Steam `main-bm4` branch; the earlier tools check flagged this as derived-but-unverified. The `--selftest`
   + the class-default check are what turn it into evidence (a wrong offset reads a wrong number, and the CDO
   value is known from the grab). If the six values look wrong, this is the first thing to question.
7. **Anything about JC3** — untouched; no JC3 process was enumerated or attached.

**COMPROMISES: none.** The values are UNKNOWN for want of a running game, which the brief allows; no value was
replaced by an estimate, and no offset was accepted without the JSON behind it.
