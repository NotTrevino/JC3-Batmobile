# DONE — DRIVERLEFT-regions (review of G3-01e, issue 1)

STATUS: **done** — `DriverLeft` (`Startup.upk` export 7400) decodes to 368 B and **28** property
references. The four names are all present, **twice each**, but the G3-01e sentence labelled `decoded`
does not survive: `Core.ArmouredMode` (254, 318) and `Core.IsVehicleAsleep` (223, 328) each appear
**once before the value-2 call and once between the two calls**, so no positional split assigns them to
one branch. `COLLISION_SELECTOR2.md`'s offset table is a **partial (22 of 28) list read one byte
early**; its runtime section survives in the four rises it names, which are re-derived below with log
file and line — but the logs have since grown from 23 mode records to 30, so there are now **six**
`0 -> 1` rises, not four.

## Files written (the only files touched)

| path | what |
|---|---|
| `Tools/scripts/grab_driverleft_regions.py` | new script, `--write` / `--check`; re-reads both packages and every sampler log |
| `Research/BatmobileGrab/DRIVERLEFT_REGIONS.md` | generated report (21,096 chars) |
| `tmp/freebuff/reports/DRIVERLEFT-regions.md` | this DONE report |

Read-only: `Startup.upk`, `BmGame.upk`, `Research/BatmobileGrab/runtime/samples-*.jsonl`,
`DRIVERLEFT_7400.md` and `COLLISION_SELECTOR2.md` (the claims under adjudication),
`Tools/scripts/upk_read.py` (imported, unmodified), `Tools/scripts/grab_collision_selector.py` and
`review_g3_01e*.md` (read). No game ran; nothing under `E:/Games` was written; no build, no git.

## The decode (decoded)

`RVehicleBatmobile.DriverLeft`, class `Function`, outer **`RVehicleBatmobile`**, export 406 B /
script **368 B**, sha1 `70471c04b9526a2616e27c3c3830155112765efb`, size field @18 = 369, trailer name
index 19530 = `DriverLeft`.

The brief says the function is "in `RVehicleBatmobileBase`". It is not: `RVehicleBatmobileBase` is the
outer of the **selector** (`BmGame.upk` 10894, `RVehicleBatmobileBase.SetBatmanVsBatmobileCollisionMode`).
Recorded as a slip in the brief rather than silently corrected.

Calls: `Core.RemoveBatmobileBindsAndSetBatmanBinds` @213 (FName 56660);
`SetBatmanVsBatmobileCollisionMode` (FName 58517) @**301** with `0x24 2` and @**334** with `0x24 1`.
Comparison tokens `0x9A`/`0x9B` at **6** and **274**. Every one of the 28 references resolves to a
named import; none is unresolved.

Regions are byte positions relative to the two calls (a position, not a proven branch body — the branch
word encoding is UNKNOWN):

| region | bounds | references | distinct names |
|---|---|---:|---|
| A | before 301 | 24 | `bWasRemoteDriving`, `Driver` x3, `InteriorLightsSwitchedOn`, `WorldInfo` x2, `GRI` x2, `FlagManager` x2, `ReturnValue` x2, `IsVehicleAsleep`, `FakeRoadCollisionStatic`, `ArmouredMode`, `BatmobileWinch` x2, `WinchPullType` x2 |
| B | 301-334 | 2 | `ArmouredMode`, `IsVehicleAsleep` |
| C | after 334 | 2 | `bForceWheelspin`, `WheelspinSmokeMomentum` |

So the sentence "the 2-branch's guard region names `BatmobileWinch` and `WinchPullType`; the 1-branch's
region names `ArmouredMode` and `IsVehicleAsleep`" is contradicted by its own function: the
`ArmouredMode`/`IsVehicleAsleep` pair also sits in region A (at 254 and 223), which is the region
G3-01e assigns to the 2-branch. What the bytes support is "all four names occur twice each; which
reference guards which call is UNKNOWN".

## The rises (decoded from the logs, with file + line)

The four the brief and the card name are all present, unchanged, and all on `veh1`:

| # | timestamp | file | line |
|---:|---|---|---:|
| 1 | `2026-11-03T10:05:15.778Z` | `samples-20261103T085631Z.jsonl` | 26 |
| 2 | `2026-11-03T11:48:22.562Z` | `samples-20261103T114350Z.jsonl` | 8 |
| 3 | `2026-11-03T11:48:24.093Z` | `samples-20261103T114350Z.jsonl` | 12 |
| 4 | `2026-11-03T11:48:38.572Z` | `samples-20261103T114350Z.jsonl` | 18 |

Two more exist now, in `samples-20261103T120003Z.jsonl`: `2026-11-04T00:59:51.896Z` (line 270) and
`2026-11-04T01:05:05.268Z` (line 513), both `veh1`, both with `Driver` 0. Two further records carry a
value that is not a mode — `234` at line 727 (same record: `veh1.Driver` = 768603295890743556, 32-bit
garbage in the flags) and `None` at line 729 (every `veh0` field null). They are excluded from the
transition count and listed, not dropped.

The column "function that can pass the new value" is two entries because only two decoded callers pass
1: `OnSleepRBPhysics` (Startup 7402, call @54, constant 1) and `DriverLeft`'s second call (7400 @334).
Which of them fired for a given sample is not in the log, so that attribution is `derived`.

Every caller (decoded, whole-package scan of `BmGame.upk` + `Startup.upk`, name index 58517):

| package | export | function | call at | constant |
|---|---:|---|---:|---:|
| `BmGame.upk` | 10701 | `RVehicleBatmobileBase.StartSelfDrive` | 13 | 0 |
| `Startup.upk` | 7399 | `RVehicleBatmobile.DriverEnter` | 237 | 0 |
| `Startup.upk` | 7400 | `RVehicleBatmobile.DriverLeft` | 301 | 2 |
| `Startup.upk` | 7400 | `RVehicleBatmobile.DriverLeft` | 334 | 1 |
| `Startup.upk` | 7401 | `RVehicleBatmobile.OnWakeRBPhysics` | 17 | 0 |
| `Startup.upk` | 7402 | `RVehicleBatmobile.OnSleepRBPhysics` | 54 | 1 |

## Which statements of `COLLISION_SELECTOR2.md` survive

Survive: the selector's sha1/253 B (re-read identical); the value→mesh table (re-derived here:
detach 48/78, attach 105/135, `1` `BatmanCollisionMeshPursuitMode`, `2` `BatmanCollisionMeshBattleMode`,
`0` in no pair); the call sites 301 (arg 2) / 334 (arg 1); "all four names are in this function"; the
`ArmouredMode` @317 / `IsVehicleAsleep` @327 rows read as **prefix** offsets (tokens 318/328, between
301 and 334); "the rise at 11:48:24.093 has no driver evidence"; and its UNKNOWN 1, which is UNKNOWN
for a stronger reason than it gives.

Partly: the 22-row "6-byte member refs" table — right names, `at` column is the byte before the
reference token (e.g. 277 is `0x19`, the token is 278). The ref form is 5 bytes; the sixth byte is the
preceding opcode, so "6-byte" is a convention.

Do not survive: presenting that table as *the* list of the script's member refs (22 of 28 — missing
`Core.Driver` @54, `Core.InteriorLightsSwitchedOn` @61, `Core.ReturnValue` @100 and @179,
`Core.BatmobileWinch` @263, `Core.WheelspinSmokeMomentum` @351); and the implicit scope of the runtime
section, which counts three vehicle instances as one.

Superseded, not wrong: "23 samples / seated 7, absent 14, not logged 2 / four rises" — those 23 records
are all still in the files, but the directory now holds 30 (seated 9, absent 16, not logged 5, six
rises), because the sampler kept writing.

## Labels

**decoded** — every export field, offset and name in this report; all 28 references and their regions;
the call sites and constants; the four/five caller table; the four rise timestamps with log file and
line; the two later rises; the two corrupt records; all 17 oracle values.
**derived** — the region partition rule (position relative to the calls); the counts
(11 valid transitions = 6 rises + 5 falls; 28 usable records = 30 − 2); "the 11:48:22.898/24.093 pair is
sleep/wake cycling" (caller constants + 0.3 s/1.2 s spacing, the log does not name the caller);
"`COLLISION_SELECTOR2.md`'s offsets are one byte early" (prefix vs token).
**UNKNOWN** — which reference guards which call; the token grammar between references; which function
produced a given runtime transition.

## Commands run, with output

```
$ cd /e/Modding/JustCause3/JC3-Batmobile && PYTHONIOENCODING=utf-8 python Tools/scripts/grab_driverleft_regions.py --write
wrote Research/BatmobileGrab/DRIVERLEFT_REGIONS.md (19,504 chars)
WRITE_EXIT=0
```

The first rendering exposed three failing oracles (`caller_constants`, `runtime_counts`,
`seven_transitions_four_rises`) because my caller loop stopped 9 bytes before the end of short scripts
(`OnWakeRBPhysics` is 26 B with its call at 17) and because the logs had grown. A probe established the
real facts — this output is verbatim:

```
$ python - <<'PYEOF'  (probe: mode keys per log, the two odd records, Startup call sites)
FILES 7
   samples-20261103T084831Z.jsonl 17
   samples-20261103T085330Z.jsonl 17
   samples-20261103T085631Z.jsonl 26
   samples-20261103T113755Z.jsonl 1
   samples-20261103T114350Z.jsonl 18
   samples-20261103T115320Z.jsonl 314
   samples-20261103T120003Z.jsonl 729
KEYS {'veh0.BatmanVsBatmobileCollisionMode': {'0': 7, 'None': 1}, 'veh1.BatmanVsBatmobileCollisionMode': {'0': 10, '1': 8, '234': 1}, 'veh2.BatmanVsBatmobileCollisionMode': {'0': 3}}
--- lines 724-731 of samples-20261103T120003Z.jsonl
724 {"t": "2026-11-04T02:05:04.082Z", "changed": {"veh1.Driver": 0}}
725 {"t": "2026-11-04T02:05:05.983Z", "changed": {"veh1.CurrentStrafeTarget": "None:None", "veh1.WeaponUnavailableReason": 163, "veh1.WeaponGeneratorPower": 1.2521210070328934e+17}}
726 {"t": "2026-11-04T02:05:06.035Z", "changed": {"veh1.flags_11D8": 2080343039, ...}}
727 {"t": "2026-11-04T02:05:06.909Z", "changed": {"veh1.flags_11D8": 2080, "veh1.flags_11DC": 3210040661, "veh1.flags_11E0": 6307, "veh1.BatmanVsBatmobileCollisionMode": 234, ... "veh1.Driver": 768603295890743556, ...}}
728 {"t": "2026-11-04T02:05:16.108Z", ...}
729 {"t": "2026-11-04T02:05:16.159Z", "changed": {"veh0.flags_11D8": null, ... "veh0.BatmanVsBatmobileCollisionMode": null, ...}}
--- startup callers
name indices [58517]
7399 RVehicleBatmobile.DriverEnter Function bytes 345 script 307
   1b@ 237 idx 58517 SetBatmanVsBatmobileCollisionMode next 24 00 16 07
7400 RVehicleBatmobile.DriverLeft Function bytes 406 script 368
   1b@ 213 idx 56660 RemoveBatmobileBindsAndSetBatmanBinds next 16 07 60 01
   1b@ 301 idx 58517 SetBatmanVsBatmobileCollisionMode next 24 02 16 06
   1b@ 334 idx 58517 SetBatmanVsBatmobileCollisionMode next 24 01 16 14
7401 RVehicleBatmobile.OnWakeRBPhysics Function bytes 64 script 26
   1b@ 17 idx 58517 SetBatmanVsBatmobileCollisionMode next 24 00 16 04
7402 RVehicleBatmobile.OnSleepRBPhysics Function bytes 101 script 63
   1b@ 24 idx 56773 RestoreStopThreshold next 16 07 56 00
   1b@ 54 idx 58517 SetBatmanVsBatmobileCollisionMode next 24 01 16 04
```

After the fixes, the run that failed the corrupt-record oracle and the final run:

```
$ PYTHONIOENCODING=utf-8 python Tools/scripts/grab_driverleft_regions.py --write
wrote Research/BatmobileGrab/DRIVERLEFT_REGIONS.md (21,097 chars)
WRITE_EXIT=0
--- (oracle table) ---
| `invalid_records_are_corrupt` | False | [... "junk_fields": 2, "line": 727 ...]
| `caller_constants` | True | {"DriverEnter": [0], "DriverLeft": [1, 2], "OnSleepRBPhysics": [1], "OnWakeRBPhysics": [0], "StartSelfDrive": [0]}
| `runtime_counts` | True | {"coverage": {"absent": 16, "missing": 5, "seated": 9}, "invalid": 2, ...}
| `valid_transitions_six_rises_five_falls` | True | {"falls": 5, "rises": 6, "transitions": 11}

$ PYTHONIOENCODING=utf-8 python Tools/scripts/grab_driverleft_regions.py --write; echo "WRITE_EXIT=$?"; PYTHONIOENCODING=utf-8 python Tools/scripts/grab_driverleft_regions.py --check; echo "CHECK_EXIT=$?"; ... grep -c "False" .../DRIVERLEFT_REGIONS.md
wrote Research/BatmobileGrab/DRIVERLEFT_REGIONS.md (21,096 chars)
WRITE_EXIT=0
OK rebuilt byte-identical from the two packages and the sampler logs
CHECK_EXIT=0
0
```

`grep -c "False"` prints `0` — no oracle row is false. (The shell's last exit status 1 is `grep`
reporting no matches, which is the desired result.)

## UNKNOWNs

1. **Which reference guards which call.** The `0x9A/0x9B` tokens are located (6, 274) but their
   operator meaning and the branch bodies are not decoded; G3-01e's corpus test showed the branch words
   are not offsets in any encoding. Tried additionally: the positional split, which fails to separate
   `ArmouredMode`/`IsVehicleAsleep` from the Winch pair. Would need a token table for this build.
2. **The token grammar between references.** This card scans for the reference form and pins all 28
   offsets, but does not re-derive why 100/179 parse as references and not constants, nor the extent of
   the `0x19` contexts (carried from `DRIVERLEFT_7400.md`, not re-proven here).
3. **Which function produced each runtime transition.** The logs store the value, not the caller; two
   functions can pass 1, so the attribution is the caller set, not per sample.

## Housekeeping

- `--check` passes and re-derives every number from the two packages and the logs (17 oracles).
- The brief named its DONE path, so there is no `manual/claimed/` task file to move.
- Prior cards on this branch remain green: `sampler_unknowns.py --check` and
  `grab_vecdefaults.py --check` both rebuild byte-identically.
