# Collision selector, corrected: guard-region evidence and the full transition set (G3-01e-fix)

The value->mesh table is **unchanged** (oracle `mesh_table_unchanged` and
`mesh_table_matches_g3_01e`): **0** attaches nothing, **1** `BatmanCollisionMeshPursuitMode`,
**2** `BatmanCollisionMeshBattleMode`. What changes is the evidence statement about the
`DriverLeft` branches and the runtime narrative.

## 1. The selector body (unchanged)

`BmGame.upk` export 10894, 253 B script, sha1 `c2f6a2ee667c544876e5317a103072c44ea17788` (re-read here, equals G3-01e's).

| mode value | mesh component | detach at | attach at |
|---|---|---|---|
| 0 | - | - | - |
| 1 | BatmanCollisionMeshPursuitMode | [48] | [105] |
| 2 | BatmanCollisionMeshBattleMode | [78] | [135] |

## 2. What the `DriverLeft` guard bytes actually contain

`Startup.upk` export 7400 `RVehicleBatmobile.DriverLeft`, 368 B script. The two selector calls are at 301 (argument 2), 334 (argument 1).

The script's **6-byte member refs** (prefix form + int32 index), `decoded`:

| at | form | resolves to | window |
|---|---|---|---|
| 4 | `0x2D 0x01` | `Core.bWasRemoteDriving` | before the value-2 call |
| 20 | `0x00 0x01` | `Core.Driver` | before the value-2 call |
| 42 | `0x00 0x01` | `Core.Driver` | before the value-2 call |
| 69 | `0x19 0x01` | `Core.WorldInfo` | before the value-2 call |
| 75 | `0x09 0x00` | `Core.GRI` | before the value-2 call |
| 81 | `0x00 0x01` | `Core.GRI` | before the value-2 call |
| 87 | `0x09 0x00` | `Core.FlagManager` | before the value-2 call |
| 93 | `0x00 0x01` | `Core.FlagManager` | before the value-2 call |
| 148 | `0x19 0x01` | `Core.WorldInfo` | before the value-2 call |
| 154 | `0x09 0x00` | `Core.GRI` | before the value-2 call |
| 160 | `0x00 0x01` | `Core.GRI` | before the value-2 call |
| 166 | `0x09 0x00` | `Core.FlagManager` | before the value-2 call |
| 172 | `0x00 0x01` | `Core.FlagManager` | before the value-2 call |
| 222 | `0x2D 0x01` | `Core.IsVehicleAsleep` | before the value-2 call |
| 229 | `0x2D 0x01` | `Core.FakeRoadCollisionStatic` | before the value-2 call |
| 253 | `0x2D 0x01` | `Core.ArmouredMode` | before the value-2 call |
| 277 | `0x19 0x01` | `Core.BatmobileWinch` | before the value-2 call |
| 283 | `0x09 0x00` | `Core.WinchPullType` | before the value-2 call |
| 289 | `0x00 0x01` | `Core.WinchPullType` | before the value-2 call |
| 317 | `0x2D 0x01` | `Core.ArmouredMode` | between the value-2 and value-1 calls |
| 327 | `0x2D 0x01` | `Core.IsVehicleAsleep` | between the value-2 and value-1 calls |
| 343 | `0x2D 0x01` | `Core.bForceWheelspin` | after the value-1 call |

So the names **are** in this function: `Core.BatmobileWinch` @277, `Core.WinchPullType` @283
and @289 sit before the value-**2** call at 301; `Core.ArmouredMode` @317 and
`Core.IsVehicleAsleep` @327 sit between the value-**2** call and the value-**1** call at 334.
The review's negative came from scanning only 5-byte refs behind `00/01/1C`, which misses the
`2D 01`, `19 01`, `09 00` and `00 01` member-access forms - these are 6-byte.

What is **not** decoded: which side of a branch each ref guards. The `0x9A/0x9B` comparison tokens
sit at 6, 274, and the branch words are not offsets (G3-01e's corpus test), so the association
"2 <-> Winch", "1 <-> ArmouredMode/IsVehicleAsleep" is **derived from position only**.
{
 "decoded": "Startup.upk 7400 script: @222/@327 Core.IsVehicleAsleep, @253/@317 Core.ArmouredMode, @277 Core.BatmobileWinch, @283/@289 Core.WinchPullType (6-byte member refs; each row has its offset and form)",
 "derived": "the value-2 call is at 301 and the value-1 call at 334; the Winch refs sit before 301, the ArmouredMode/IsVehicleAsleep pair between 301 and 334. That positional split *suggests* 2<->Winch and 1<->ArmouredMode/IsVehicleAsleep, but the branch encoding is UNKNOWN, so which body/guard each ref belongs to is not proven",
 "label": "names decoded, branch association derived/UNKNOWN"
}

## 3. Runtime: all seven transitions, with coverage

23 samples across 7 logs: values {'0': 17, '1': 6}.
Driver field present in the same sample: {'seated': 7, 'absent': 14, 'missing': 2}.

| mode | seated | absent | not logged |
|---|---|---|---|
| 0 | 7 | 9 | 1 |
| 1 | 0 | 5 | 1 |

| transition | from -> to | driver in that sample |
|---|---|---|
| 2026-11-03T10:05:15.778Z | 0 -> 1 | absent |
| 2026-11-03T11:48:22.562Z | 0 -> 1 | absent |
| 2026-11-03T11:48:22.898Z | 1 -> 0 | missing |
| 2026-11-03T11:48:24.093Z | 0 -> 1 | missing |
| 2026-11-03T11:48:25.206Z | 1 -> 0 | seated |
| 2026-11-03T11:48:38.572Z | 0 -> 1 | absent |
| 2026-11-03T11:53:43.969Z | 1 -> 0 | seated |

**All four 0->1 rises**: 10:05:15.778, 11:48:22.562, 11:48:24.093, 11:48:38.572. **All three 1->0 falls**: 11:48:22.898, 11:48:25.206, 11:53:43.969.

Two samples carry no `Driver` field (`11:48:22.898`, `11:48:24.093`) because the sampler logs
only fields that changed; they are counted as `not logged`, not dropped. In particular the
rise at `11:48:24.093` has **no driver evidence**, so it cannot be called an exit.

## 4. Oracles (`--check` re-runs all of them)

| oracle | ok | detail |
|---|---|---|
| `mesh_table_unchanged` | True | {"rows": {"0": null, "1": "BatmanCollisionMeshPursuitMode", "2": "BatmanCollisionMeshBattleMode"}, "expected": {"0": null, "1": "BatmanCollisionMeshPursuitMode", "2": "BatmanCollisionMeshBattleMode"}} |
| `mesh_table_matches_g3_01e` | True | {"g3_01e_rows": {"0": null, "1": "BatmanCollisionMeshPursuitMode", "2": "BatmanCollisionMeshBattleMode"}} |
| `selector_sha1` | True | {"recomputed": "c2f6a2ee667c544876e5317a103072c44ea17788", "g3_01e": "c2f6a2ee667c544876e5317a103072c44ea17788"} |
| `guard_refs_present` | True | {"missing": [], "found": [["Core.ArmouredMode", 253], ["Core.ArmouredMode", 317], ["Core.BatmobileWinch", 277], ["Core.Driver", 20], ["Core.Driver", 42], ["Core.FakeRoadCollisionStatic", 229], ["Core.FlagManager", 87], ["Core.FlagManager", 93], ["Core.FlagMana |
| `guard_windows` | True | {"before_301": [[277, "Core.BatmobileWinch"], [283, "Core.WinchPullType"], [289, "Core.WinchPullType"]], "between_301_334": [[317, "Core.ArmouredMode"], [327, "Core.IsVehicleAsleep"]]} |
| `runtime_values` | True | {"value_counts": {"0": 17, "1": 6}, "samples": 23} |
| `runtime_coverage` | True | {"coverage": {"seated": 7, "absent": 14, "missing": 2}, "sum_check": true} |
| `runtime_transitions` | True | {"rises": 4, "falls": 3, "total": 7, "list": [["10:05:15.778", 0, 1, "absent"], ["11:48:22.562", 0, 1, "absent"], ["11:48:22.898", 1, 0, "missing"], ["11:48:24.093", 0, 1, "missing"], ["11:48:25.206", 1, 0, "seated"], ["11:48:38.572", 0, 1, "absent"], ["11:53: |
| `runtime_rise_list` | True | {"actual": [["10:05:15.778", 0, 1], ["11:48:22.562", 0, 1], ["11:48:22.898", 1, 0], ["11:48:24.093", 0, 1], ["11:48:25.206", 1, 0], ["11:48:38.572", 0, 1], ["11:53:43.969", 1, 0]]} |
| `caller_constants` | True | {"constants": [0, 1, 2], "sites": 6} |

## 5. UNKNOWN

1. Which `DriverLeft` condition selects 1 and which selects 2 - the refs are decoded, the
   branch encoding is not, so the positional association in section 2 is `derived`.
2. Branch-word encoding (G3-01e UNKNOWN 1, unchanged).
3. Whether `Core.BatmobileWinch` / `Core.WinchPullType` / `Core.ArmouredMode` /
   `Core.IsVehicleAsleep` are globals or members - the import path says `Core.<name>` and the
   layout to expand that is not in the packages read here.
