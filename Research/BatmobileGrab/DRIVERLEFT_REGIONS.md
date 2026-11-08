# DRIVERLEFT_REGIONS - what `DriverLeft` actually references around each selector call

**Card:** DRIVERLEFT-regions (follow-on to the review of **G3-01e**, issue 1).
**Verdict:** the four names are in the function, but the sentence that is labelled `decoded`
is still wrong: `ArmouredMode` and `IsVehicleAsleep` are referenced **before** the value-2
call as well as between the two calls, so no positional split assigns them to one branch.
`COLLISION_SELECTOR2.md`'s offset table is a **partial list read one byte early**, and its
runtime section survives: it carries all four `0 -> 1` rises, and they are re-derived here with
the log file and line of each.

## 1. The export (decoded)

| field | value |
|---|---|
| package | `Startup.upk` |
| export | 7400 |
| path | `RVehicleBatmobile.DriverLeft` |
| outer | `RVehicleBatmobile` |
| class | `Function` |
| export bytes | 406 |
| script bytes (`payload[22:-16]`) | 368 |
| script sha1 | `70471c04b9526a2616e27c3c3830155112765efb` |
| size field @18 | 369 (= script + 1) |
| trailer name index | 19530 (`DriverLeft`) |

The brief says `RVehicleBatmobileBase`; the export's own outer is `RVehicleBatmobile`, and its path is `RVehicleBatmobile.DriverLeft`.
`RVehicleBatmobileBase` is the outer of the *selector* (`BmGame.upk` 10894, `RVehicleBatmobileBase.SetBatmanVsBatmobileCollisionMode`), which is where the value->mesh table lives. The function the
brief asks about is therefore this one, and the brief's class name is a slip, recorded rather
than silently corrected.

## 2. How the references were found (decoded)

Every offset in the 368-byte script is tested for the reference form `<0x00|0x01|0x02>` + int32,
and the int32 is resolved through the package object table. Matches that start inside an earlier
match's 5-byte extent are dropped. The result is compared against the 28 reference offsets
`DRIVERLEFT_7400.md` publishes, so a false positive or a miss fails the oracle:

- raw pattern hits: **28**; after de-overlap: **28**
- oracle `refs_reproduce_the_published_28`: **True**
- the scan is a byte pattern, not a token walk: it can only mislabel a reference if a random
  int32 lands on a named object at a non-reference offset. The 28/28 agreement with the
  published set, and with the call sites at 301/334 below, is the check that this does not
  happen here. The *token* shape of the bytes between references is not re-derived (see
  UNKNOWN 1) - this card needs offsets and names, not a full grammar.

## 3. Every reference, with the region it sits in (decoded)

`region` is a byte position relative to the two selector calls: **A** before the value-2 call
(@301), **B** between it and the value-1 call (@334), **C** after the value-1 call.
It is a position, not a proven branch body - the branch-word encoding is UNKNOWN (G3-01e).
`prefix` is the byte immediately before the reference token.

| # | token at | prefix | form | index | resolves to | class | region |
|---:|---:|---|---|---:|---|---|---|
| 1 | 5 | `0x2D` | `0x01` | -1382 | `Core.bWasRemoteDriving` | BoolProperty | A |
| 2 | 21 | `0x00` | `0x01` | -5746 | `Core.Driver` | ObjectProperty | A |
| 3 | 43 | `0x00` | `0x01` | -5746 | `Core.Driver` | ObjectProperty | A |
| 4 | 54 | `0x0F` | `0x01` | -5746 | `Core.Driver` | ObjectProperty | A |
| 5 | 61 | `0x8C` | `0x01` | -1581 | `Core.InteriorLightsSwitchedOn` | ByteProperty | A |
| 6 | 70 | `0x19` | `0x01` | -5702 | `Core.WorldInfo` | ObjectProperty | A |
| 7 | 76 | `0x09` | `0x00` | -5749 | `Core.GRI` | ObjectProperty | A |
| 8 | 82 | `0x00` | `0x01` | -5749 | `Core.GRI` | ObjectProperty | A |
| 9 | 88 | `0x09` | `0x00` | -5377 | `Core.FlagManager` | ObjectProperty | A |
| 10 | 94 | `0x00` | `0x01` | -5377 | `Core.FlagManager` | ObjectProperty | A |
| 11 | 100 | `0x2C` | `0x00` | -995 | `Core.ReturnValue` | BoolProperty | A |
| 12 | 149 | `0x19` | `0x01` | -5702 | `Core.WorldInfo` | ObjectProperty | A |
| 13 | 155 | `0x09` | `0x00` | -5749 | `Core.GRI` | ObjectProperty | A |
| 14 | 161 | `0x00` | `0x01` | -5749 | `Core.GRI` | ObjectProperty | A |
| 15 | 167 | `0x09` | `0x00` | -5377 | `Core.FlagManager` | ObjectProperty | A |
| 16 | 173 | `0x00` | `0x01` | -5377 | `Core.FlagManager` | ObjectProperty | A |
| 17 | 179 | `0x20` | `0x00` | -995 | `Core.ReturnValue` | BoolProperty | A |
| 18 | 223 | `0x2D` | `0x01` | -1498 | `Core.IsVehicleAsleep` | BoolProperty | A |
| 19 | 230 | `0x2D` | `0x01` | -1361 | `Core.FakeRoadCollisionStatic` | BoolProperty | A |
| 20 | 254 | `0x2D` | `0x01` | -1366 | `Core.ArmouredMode` | BoolProperty | A |
| 21 | 263 | `0x77` | `0x01` | -5673 | `Core.BatmobileWinch` | ObjectProperty | A |
| 22 | 278 | `0x19` | `0x01` | -5673 | `Core.BatmobileWinch` | ObjectProperty | A |
| 23 | 284 | `0x09` | `0x00` | -1515 | `Core.WinchPullType` | ByteProperty | A |
| 24 | 290 | `0x00` | `0x01` | -1515 | `Core.WinchPullType` | ByteProperty | A |
| 25 | 318 | `0x2D` | `0x01` | -1366 | `Core.ArmouredMode` | BoolProperty | B |
| 26 | 328 | `0x2D` | `0x01` | -1498 | `Core.IsVehicleAsleep` | BoolProperty | B |
| 27 | 344 | `0x2D` | `0x01` | -1494 | `Core.bForceWheelspin` | BoolProperty | C |
| 28 | 351 | `0x0F` | `0x01` | -3046 | `Core.WheelspinSmokeMomentum` | FloatProperty | C |

## 4. The real names in each region (decoded)

**A - before the value-2 call (@301):**

- `Core.bWasRemoteDriving`
- `Core.Driver`
- `Core.Driver`
- `Core.Driver`
- `Core.InteriorLightsSwitchedOn`
- `Core.WorldInfo`
- `Core.GRI`
- `Core.GRI`
- `Core.FlagManager`
- `Core.FlagManager`
- `Core.ReturnValue`
- `Core.WorldInfo`
- `Core.GRI`
- `Core.GRI`
- `Core.FlagManager`
- `Core.FlagManager`
- `Core.ReturnValue`
- `Core.IsVehicleAsleep`
- `Core.FakeRoadCollisionStatic`
- `Core.ArmouredMode`
- `Core.BatmobileWinch`
- `Core.BatmobileWinch`
- `Core.WinchPullType`
- `Core.WinchPullType`

**B - between the value-2 call (@301) and the value-1 call (@334):**

- `Core.ArmouredMode`
- `Core.IsVehicleAsleep`

**C - after the value-1 call (@334):**

- `Core.bForceWheelspin`
- `Core.WheelspinSmokeMomentum`

Read as a whole function, the distinct names are: `Core.ArmouredMode`, `Core.BatmobileWinch`, `Core.Driver`, `Core.FakeRoadCollisionStatic`, `Core.FlagManager`, `Core.GRI`, `Core.InteriorLightsSwitchedOn`, `Core.IsVehicleAsleep`, `Core.ReturnValue`, `Core.WheelspinSmokeMomentum`, `Core.WinchPullType`, `Core.WorldInfo`, `Core.bForceWheelspin`, `Core.bWasRemoteDriving`.

### What this does to the G3-01e sentence

G3-01e said, labelled `decoded`: *"2 on the other `DriverLeft` branch (its guard region names
`BatmobileWinch` and `WinchPullType`; the 1-branch's region names `ArmouredMode` and
`IsVehicleAsleep`)"*. The bytes say:

- `Core.BatmobileWinch` is referenced at 263 and 278, both **before** the value-2 call;
  `Core.WinchPullType` at 284 and 290, also both before it. That half of the claim is
  positionally consistent with the bytes.
- `Core.ArmouredMode` is referenced at **254** (before the value-2 call) **and** 318 (between
  the calls). `Core.IsVehicleAsleep` at **223** (before the value-2 call) **and** 328
  (between). So the pair G3-01e assigns to the 1-branch is also present in the region it
  assigns to the 2-branch, once each.
- Therefore the assignment is not merely unproven (branch encoding UNKNOWN): even the purely
  positional reading it relies on does not separate the two pairs. What the bytes support is
  that **all four names are in this function, twice each**, with `ArmouredMode`/
  `IsVehicleAsleep` occurring on both sides of the value-2 call.
- The honest statement is: the function references these four properties around its two
  `SetBatmanVsBatmobileCollisionMode` calls; **which reference guards which call is UNKNOWN**.
  A predicate that reads a winch property before choosing 2 is plausible, but nothing in the
  bytes orders the references into branch bodies.

## 5. The calls and comparisons (decoded)

| at | token | call | argument |
|---:|---|---|---|
| 11 | `0x1C` | `Core.TriggerEventClass` | - |
| 33 | `0x1C` | `Core.TriggerEventClass` | - |
| 106 | `0x1C` | `Core.SetGlobalFlag` | - |
| 185 | `0x1C` | `Core.SetGlobalFlag` | - |
| 213 | `0x1B` | `RemoveBatmobileBindsAndSetBatmanBinds` | - |
| 236 | `0x1C` | `Core.UpdateFakeRoadCollision` | - |
| 301 | `0x1B` | `SetBatmanVsBatmobileCollisionMode` | byte 2 @306 |
| 334 | `0x1B` | `SetBatmanVsBatmobileCollisionMode` | byte 1 @339 |
| 361 | `0x1C` | `Core.DriverLeft` | - |

Comparison tokens (`0x9A`/`0x9B`) are at 6, 274;
their operator meaning (`==` vs `!=`) is UNKNOWN. The branch words that would associate a
comparison with a body are not offsets in any encoding tried (G3-01e's corpus test), so this
card does not group the references into bodies.

## 6. The `0 -> 1` transitions of the collision mode (decoded from the logs)

Re-derived from `samples-*.jsonl` (7 files, 30 mode records across 3 vehicle instances): **11** valid transitions, **6** rises, **5** falls, and **2** records whose value is not a mode (6.3).

### 6.1 The four rises the brief and the card name - all still present

| # | timestamp | log file | line | vehicle | transition | Driver in the sample | callers that can pass 1 |
|---:|---|---|---:|---|---|---|---|
| 1 | `2026-11-03T10:05:15.778Z` | `samples-20261103T085631Z.jsonl` | 26 | `veh1` | 0 -> 1 | 0 | `OnSleepRBPhysics` (Startup 7402 @54) or `DriverLeft`'s second call (Startup 7400 @334) |
| 2 | `2026-11-03T11:48:22.562Z` | `samples-20261103T114350Z.jsonl` | 8 | `veh1` | 0 -> 1 | 0 | `OnSleepRBPhysics` (Startup 7402 @54) or `DriverLeft`'s second call (Startup 7400 @334) |
| 3 | `2026-11-03T11:48:24.093Z` | `samples-20261103T114350Z.jsonl` | 12 | `veh1` | 0 -> 1 | not logged | `OnSleepRBPhysics` (Startup 7402 @54) or `DriverLeft`'s second call (Startup 7400 @334) |
| 4 | `2026-11-03T11:48:38.572Z` | `samples-20261103T114350Z.jsonl` | 18 | `veh1` | 0 -> 1 | 0 | `OnSleepRBPhysics` (Startup 7402 @54) or `DriverLeft`'s second call (Startup 7400 @334) |

### 6.2 Two further rises in the same logs

The card was written against 23 mode samples; the sampler kept writing, and the same directory
now holds 30. Two more `0 -> 1` rises are in `samples-20261103T120003Z.jsonl`:

| timestamp | log file | line | vehicle | transition | Driver in the sample |
|---|---|---:|---|---|---|
| `2026-11-04T00:59:51.896Z` | `samples-20261103T120003Z.jsonl` | 270 | `veh1` | 0 -> 1 | 0 |
| `2026-11-04T01:05:05.268Z` | `samples-20261103T120003Z.jsonl` | 513 | `veh1` | 0 -> 1 | 0 |

So "all four 0 -> 1 rises" was right for the read it describes, and is no longer the whole
set: there are 6 now. The four it named are unchanged, which is what the fix to
G3-01e's three-rise narrative needed.

### 6.3 Two records that are not mode changes

| timestamp | log file | line | vehicle | value | junk fields in the same record | transition from |
|---|---|---:|---|---:|---:|---|
| `2026-11-04T02:05:06.909Z` | `samples-20261103T120003Z.jsonl` | 727 | `veh1` | `234` | 3 of 10 | 0 |
| `2026-11-04T02:05:16.159Z` | `samples-20261103T120003Z.jsonl` | 729 | `veh0` | `None` | 16 of 16 | 0 |

These are corrupt reads, not modes: `234` arrives in a record where `veh1.Driver` is
`768603295890743556` and the flag fields are 32-bit garbage, and the `None` record nulls every
`veh0` field. They are excluded from the transition count and listed here rather than dropped.

### 6.4 Per-vehicle census

| vehicle instance | mode records | values seen |
|---|---:|---|
| `veh0` | 8 | `{"0": 7, "None": 1}` |
| `veh1` | 19 | `{"0": 10, "1": 8, "234": 1}` |
| `veh2` | 3 | `{"0": 3}` |

The earlier cards counted these three instances together (23 records then, 30 now). Every rise
in 6.1 and 6.2 is a single instance's, which the table's `vehicle` column shows.

### Callers and the constant each passes (decoded)

| package | export | function | call at | constant |
|---|---:|---|---:|---:|
| `BmGame.upk` | 10701 | `RVehicleBatmobileBase.StartSelfDrive` | 13 | 0 |
| `Startup.upk` | 7399 | `RVehicleBatmobile.DriverEnter` | 237 | 0 |
| `Startup.upk` | 7400 | `RVehicleBatmobile.DriverLeft` | 301 | 2 |
| `Startup.upk` | 7400 | `RVehicleBatmobile.DriverLeft` | 334 | 1 |
| `Startup.upk` | 7401 | `RVehicleBatmobile.OnWakeRBPhysics` | 17 | 0 |
| `Startup.upk` | 7402 | `RVehicleBatmobile.OnSleepRBPhysics` | 54 | 1 |

`0` is passed by `DriverEnter`, `OnWakeRBPhysics` and `StartSelfDrive`; `1` by
`OnSleepRBPhysics` and one `DriverLeft` call; `2` by the other. The `11:48:22.898` fall and the
`11:48:24.093` rise are 0.3 s and 1.2 s apart with no driver field in either sample, which is
the sleep/wake pair (`OnSleepRBPhysics` passes 1, `OnWakeRBPhysics` passes 0) rather than a
driver event - `derived`, since the log does not name the caller.

## 7. Runtime coverage (decoded)

- mode records: 30; `Driver` co-sampled: seated 9, absent 16, not logged 5
- of those, 2 carry a value that is not a mode (6.3), so 28 are usable mode readings
- "not logged" means the sampler writes only changed fields, so a sample without a `Driver`
  key is missing evidence, not evidence of absence. The `11:48:24.093` rise is such a sample,
  so it cannot be called an exit.

## 8. Which statements of `COLLISION_SELECTOR2.md` survive

| statement | verdict | evidence |
|---|---|---|
| selector body: `BmGame.upk` 10894, 253 B, sha1 `c2f6a2ee667c` | **survives** | re-read here: same size, same sha1 |
| value->mesh table: 0 attaches nothing, 1 Pursuit, 2 Battle | **survives** | re-derived here from the four component calls (detach 48/78, attach 105/135) with the mesh properties they name |
| "the two selector calls are at 301 (argument 2), 334 (argument 1)" | **survives** | decoded: `SetBatmanVsBatmobileCollisionMode` at 301 with `0x24 2`, at 334 with `0x24 1` |
| "the names `BatmobileWinch`/`WinchPullType`/`ArmouredMode`/`IsVehicleAsleep` **are** in this function" | **survives** | all four present, twice each, table in §3 |
| the 22-row "6-byte member refs" table with an `at` column | **partly** | the names are right; each `at` is the byte **before** the reference token (e.g. 277 is `0x19`, the token is 278), so the column is a prefix offset, not a reference offset |
| that table presented as *the* list of the script's member refs | **does not survive** | it lists 22 of 28; missing `Core.Driver` @54, `Core.InteriorLightsSwitchedOn` @61, `Core.ReturnValue` @100 and @179, `Core.BatmobileWinch` @263, `Core.WheelspinSmokeMomentum` @351 |
| "the review's negative came from scanning only 5-byte refs behind `00/01/1C`" | **survives in substance** | the names are there and the earlier negative was a scan artefact; but the ref form is 5 bytes, so "6-byte" counts the leading byte, which is a convention, not a width |
| "the refs that sit between the two calls are `ArmouredMode` @317 and `IsVehicleAsleep` @327" | **survives positionally** | prefix 317/327 -> tokens 318/328, both between 301 and 334 |
| "what is not decoded: which side of a branch each ref guards" | **survives, and is now stronger** | `ArmouredMode` @254 and `IsVehicleAsleep` @223 also sit **before** the value-2 call, so position cannot even separate the two pairs |
| "all four `0 -> 1` rises: 10:05:15.778, 11:48:22.562, 11:48:24.093, 11:48:38.572" | **survives for the 23-record read it describes** | all four re-derived with file + line in §6.1; the logs now hold 30 records and six rises, so "all" is no longer the whole set (§6.2) |
| "the rise at `11:48:24.093` has no driver evidence" | **survives** | that sample carries no `Driver` key (oracle `rise_114824093_has_no_driver`) |
| coverage "seated 7, absent 14, not logged 2" over 23 samples | **superseded, not wrong when written** | the 23 records are all still present; the directory now holds 30, with seated 9 / absent 16 / not logged 5 (§7) |
| the runtime section treats the mode as one vehicle's | **does not survive as a scope** | the logs carry `veh0`, `veh1` and `veh2`; §6.4 counts them separately |
| UNKNOWN 1 ("which condition selects 1 and which selects 2") | **survives, reframed** | it is UNKNOWN, but not for the reason given: the claimed guard regions are not separated by the bytes at all (§4) |

What G3-01e itself still gets wrong: its runtime narrative named three rises and one fall,
omitting `11:48:22.898` and `11:48:24.093`. `COLLISION_SELECTOR2.md` fixed that; this card
confirms the fix rather than repeating the error.

## 9. Oracles (`--check` re-runs each)

| oracle | ok | detail |
|---|---|---|
| `armouredmode_and_asleep_sit_in_region_A_too` | True | `{"Core.ArmouredMode": ["A: before the value-2 call", "B: between the value-2 and value-1 calls"], "Core.BatmobileWinch": ["A: before the value-2 call", "A: before the value-2 call"], "Core.IsVehicleAsleep": ["A: before the value-2 call", "B` |
| `caller_constants` | True | `{"DriverEnter": [0], "DriverLeft": [1, 2], "OnSleepRBPhysics": [1], "OnWakeRBPhysics": [0], "StartSelfDrive": [0]}` |
| `comparison_tokens_at_6_and_274` | True | `{"compare_offsets": [6, 274]}` |
| `every_ref_resolves` | True | `{"refs": 28, "unresolved": 0}` |
| `export_identity` | True | `{"outer": "RVehicleBatmobile", "path": "RVehicleBatmobile.DriverLeft", "script_bytes": 368, "sha1": "70471c04b9526a2616e27c3c3830155112765efb", "size_field": 369}` |
| `four_named_rises_still_present` | True | `{"all_rises": ["2026-11-03T10:05:15.778Z", "2026-11-03T11:48:22.562Z", "2026-11-03T11:48:24.093Z", "2026-11-03T11:48:38.572Z", "2026-11-04T00:59:51.896Z", "2026-11-04T01:05:05.268Z"], "named": ["2026-11-03T10:05:15.778Z", "2026-11-03T11:48:` |
| `four_names_present_twice` | True | `{"Core.ArmouredMode": [254, 318], "Core.BatmobileWinch": [263, 278], "Core.IsVehicleAsleep": [223, 328], "Core.WinchPullType": [284, 290]}` |
| `invalid_records_are_corrupt` | True | `[{"file": "samples-20261103T120003Z.jsonl", "from": 0, "junk_fields": 3, "line": 727, "record_fields": 10, "t": "2026-11-04T02:05:06.909Z", "value": 234, "vehicle": "veh1"}, {"file": "samples-20261103T120003Z.jsonl", "from": 0, "junk_fields` |
| `mesh_rows_rederived` | True | `{"1": {"attach_at": [105], "detach_at": [48], "mesh": "BatmanCollisionMeshPursuitMode"}, "2": {"attach_at": [135], "detach_at": [78], "mesh": "BatmanCollisionMeshBattleMode"}}` |
| `refs_reproduce_the_published_28` | True | `{"found": 28, "offsets_match": true, "raw_hits": 28}` |
| `regions_partition_the_refs` | True | `{"A: before the value-2 call": 24, "B: between the value-2 and value-1 calls": 2, "C: after the value-1 call": 2}` |
| `rise_114824093_has_no_driver` | True | `[["2026-11-03T10:05:15.778Z", 0], ["2026-11-03T11:48:22.562Z", 0], ["2026-11-03T11:48:24.093Z", "not logged"], ["2026-11-03T11:48:38.572Z", 0], ["2026-11-04T00:59:51.896Z", 0], ["2026-11-04T01:05:05.268Z", 0]]` |
| `runtime_counts` | True | `{"coverage": {"absent": 16, "missing": 5, "seated": 9}, "invalid": 2, "per_vehicle": {"veh0": {"samples": 8, "values": {"0": 7, "None": 1}}, "veh1": {"samples": 19, "values": {"0": 10, "1": 8, "234": 1}}, "veh2": {"samples": 3, "values": {"` |
| `selector_calls_at_301_and_334` | True | `{"calls": [[301, 2], [334, 1]], "v1": 334, "v2": 301}` |
| `selector_sha1_unchanged` | True | `{"script_bytes": 253, "sha1": "c2f6a2ee667c544876e5317a103072c44ea17788"}` |
| `valid_transitions_six_rises_five_falls` | True | `{"falls": 5, "rises": 6, "transitions": 11}` |

## 10. Result

- the function: `RVehicleBatmobile.DriverLeft`, 368 B script, 28 references [decoded]
- value-2 call @301, value-1 call @334 [decoded]
- region A (before 301) names: `Core.bWasRemoteDriving`, `Core.Driver`, `Core.InteriorLightsSwitchedOn`, `Core.WorldInfo`, `Core.GRI`, `Core.FlagManager`, `Core.ReturnValue`, `Core.IsVehicleAsleep`, `Core.FakeRoadCollisionStatic`, `Core.ArmouredMode`, `Core.BatmobileWinch`, `Core.WinchPullType` [decoded]
- region B (301-334): `Core.ArmouredMode`, `Core.IsVehicleAsleep` [decoded]
- region C (after 334): `Core.bForceWheelspin`, `Core.WheelspinSmokeMomentum` [decoded]
- `ArmouredMode`/`IsVehicleAsleep` occur in **both** A and B, so the G3-01e branch attribution does not survive [decoded offsets; conclusion derived]
- 6 `0 -> 1` rises, with file + line: §6.1 for the four the card named, §6.2 for the two added since [decoded]
- which reference guards which call: **UNKNOWN** (branch encoding)

## 11. UNKNOWN

1. **The token grammar between references.** This card scans for the reference form; it does
   not re-derive why the bytes at 100/179 parse as references rather than constants, nor the
   extent of the `0x19` contexts. Tried: 28/28 offset agreement and the call sites, which
   pins the references but not the surrounding tokens. Would need a token table for this build.
2. **Which reference guards which call.** The `0x9A/0x9B` tokens are decoded as bytes at 6 and
   274; the branch bodies are not. Tried: G3-01e's corpus test (branch words are not offsets)
   and the positional check in §4, which fails to separate the pairs.
3. **Which function produced each runtime transition.** The logs record the value, not the
   caller. Tried: caller constants (§6); two functions can pass 1, so a given rise is
   attributed by the caller set, not per sample.
