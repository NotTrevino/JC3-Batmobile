# G3-01e-fix — `SetBatmanVsBatmobileCollisionMode`: guard-region evidence and the full transition set

STATUS: **done, with one substantive correction to the review this card was based on.** The
value→mesh table is untouched (0 → none, 1 → `BatmanCollisionMeshPursuitMode`,
2 → `BatmanCollisionMeshBattleMode`; three oracles prove it). Two things changed:

1. **The guard-region names were NOT removed, because they are in the bytes.** `review-G3-01e.md`
   item 1 reported `BatmobileWinch` / `WinchPullType` / `ArmouredMode` / `IsVehicleAsleep` as absent
   from `DriverLeft`'s script. That is a **false negative**: the review scanned 5-byte refs behind
   the prefixes `00`/`01`/`1C` and missed the **6-byte member-access forms** (`2D 01`, `19 01`,
   `09 00`, `00 01`). Decoded here from `Startup.upk` 7400:
   `@277 Core.BatmobileWinch`, `@283`/`@289 Core.WinchPullType` — before the value-**2** call at
   301; `@317 Core.ArmouredMode`, `@327 Core.IsVehicleAsleep` — between the value-2 call and the
   value-**1** call at 334; also `@222 Core.IsVehicleAsleep`, `@253 Core.ArmouredMode`,
   `@229 Core.FakeRoadCollisionStatic`, `@343 Core.bForceWheelspin`. What *was* wrong in G3-01e is
   the **label**: the names are decoded, but which branch body/guard each belongs to is only
   **positional**, so the 2↔Winch / 1↔ArmouredMode association is `derived`, not `decoded`.

   The task asked to remove the claim "the review shows those names are not in that function's
   script"; the review's negative does not survive the bytes, so removing a true fact would have been
   the guess. The claim is kept and strengthened with offsets, and the derived part is relabelled.

2. **The runtime narrative is fixed** (the review was right here). The logs hold **7 transitions =
   4 rises + 3 falls**, over **23 samples** (`{0: 17, 1: 6}`); **2 samples carry no `Driver` field**
   (`11:48:22.898`, `11:48:24.093`) because the sampler logs only changes. G3-01e quoted three rises
   and called them "exactly the exit events"; the fourth rise at `11:48:24.093` has **no driver
   evidence at all**. Denominators are now explicit per mode: mode 0 = 7 seated / 9 absent /
   1 not logged; mode 1 = 0 seated / 5 absent / 1 not logged.

`bmak_runtime_sampler.py` was not touched; the G3-01e files (`COLLISION_SELECTOR.md/.json`,
`grab_collision_selector.py`) were not edited; the review file was not edited (read-only rule — it
should be read together with this report).

## Files written

| file | size | what |
|---|---|---|
| `Tools/scripts/grab_collision_selector2.py` | new | reuses the G3-01e decoder, adds the member-ref scan and the coverage-complete runtime count; `--write` / `--check` |
| `Research/BatmobileGrab/COLLISION_SELECTOR2.md` | generated | refs table, transitions table, coverage, oracles |
| `Research/BatmobileGrab/COLLISION_SELECTOR2.json` | generated | same, machine-readable |

## Commands and output (verbatim)

```
cd "E:/Modding/JustCause3/JC3-Batmobile" && PYTHONIOENCODING=utf-8 uv run python Tools/scripts/grab_collision_selector2.py --write; echo "WRITE_EXIT=$?"; echo "=== CHECK ==="; PYTHONIOENCODING=utf-8 uv run python Tools/scripts/grab_collision_selector2.py --check; echo "CHECK_EXIT=$?"
```

```
wrote Research\BatmobileGrab\COLLISION_SELECTOR2.md and Research\BatmobileGrab\COLLISION_SELECTOR2.json
mesh table: {0: None, 1: 'BatmanCollisionMeshPursuitMode', 2: 'BatmanCollisionMeshBattleMode'}
driverleft refs: 22; transitions: 7 (4 rises, 3 falls)
oracles: 10/10 ok
WRITE_EXIT=0
=== CHECK ===
OK table {0: None, 1: 'BatmanCollisionMeshPursuitMode', 2: 'BatmanCollisionMeshBattleMode'}; 22 driverleft refs; 7 transitions (4 up, 3 down); md+json byte-identical
oracles: {"caller_constants": true, "guard_refs_present": true, "guard_windows": true, "mesh_table_matches_g3_01e": true, "mesh_table_unchanged": true, "runtime_coverage": true, "runtime_rise_list": true, "runtime_transitions": true, "runtime_values": true, "selector_sha1": true}
CHECK_EXIT=0
```

## The guard bytes, as decoded

`Startup.upk` export 7400 `RVehicleBatmobile.DriverLeft`, 368 B script, 9 calls, comparison tokens
`0x9A`/`0x9B` at 6 and 274. The two selector calls are at 301 (`byte 2`) and 334 (`byte 1`).

| at | form | resolves to | position |
|---|---|---|---|
| 222 | `2D 01` | `Core.IsVehicleAsleep` | before 301 |
| 229 | `2D 01` | `Core.FakeRoadCollisionStatic` | before 301 |
| 253 | `2D 01` | `Core.ArmouredMode` | before 301 |
| 277 | `19 01` | `Core.BatmobileWinch` | before 301 |
| 283 | `09 00` | `Core.WinchPullType` | before 301 |
| 289 | `00 01` | `Core.WinchPullType` | before 301 |
| 317 | `2D 01` | `Core.ArmouredMode` | between 301 and 334 |
| 327 | `2D 01` | `Core.IsVehicleAsleep` | between 301 and 334 |
| 343 | `2D 01` | `Core.bForceWheelspin` | after 334 |

(The full 22-row list, including `Core.Driver`, `Core.WorldInfo`, `Core.GRI`, `Core.FlagManager`, is
in the generated doc.) The Winch pair sits before the value-2 call and the ArmouredMode/IsVehicleAsleep
pair between the two calls — that is the positional basis for the 2↔Winch / 1↔ArmouredMode reading,
not a decoded branch mapping.

## The runtime, as recomputed

| transition | from → to | Driver in that sample |
|---|---|---|
| 10:05:15.778 | 0 → 1 | absent |
| 11:48:22.562 | 0 → 1 | absent |
| 11:48:22.898 | 1 → 0 | **not logged** |
| 11:48:24.093 | 0 → 1 | **not logged** |
| 11:48:25.206 | 1 → 0 | seated |
| 11:48:38.572 | 0 → 1 | absent |
| 11:53:43.969 | 1 → 0 | seated |

Coverage: 23 samples, `{0: 17, 1: 6}`, Driver co-sampled in 21 (7 seated, 14 absent), missing in 2.
The `11:48:22.898 → 11:48:24.093 → 11:48:25.206` sequence (1→0→1→0 in 2.6 s) is a **flicker**, not
one exit: the caller set explains it as wake/sleep cycling (`OnWakeRBPhysics` passes 0,
`OnSleepRBPhysics` passes 1), but the samples do not say which handler fired, so the fix card states
the transitions and leaves the cause derived.

## Table unchanged (the constraint)

| oracle | what it proves |
|---|---|
| `mesh_table_unchanged` | rows equal `{0: None, 1: Pursuit, 2: Battle}` |
| `mesh_table_matches_g3_01e` | identical to the stored `COLLISION_SELECTOR.json` rows |
| `selector_sha1` | re-read export 10894 script hashes to `c2f6a2ee…788`, the G3-01e value |

Other oracles: `guard_refs_present` (the seven expected refs, with offsets),
`guard_windows` (3 Winch refs before 301, 2 Armoured/Asleep refs between 301 and 334),
`runtime_values`, `runtime_coverage` (buckets sum to 23), `runtime_transitions` (4 up / 3 down, all
0↔1), `runtime_rise_list` (exact timestamp list), `caller_constants` (6 sites, {0,1,2}).

## UNKNOWNs

1. **Branch side of each guard ref.** The refs and their offsets are decoded; which one guards the
   value-2 body and which the value-1 body needs the branch encoding, so it stays `derived`. Where it
   would be answered: a BmScript VM reference, or the same function from a second build.
2. **Branch-word encoding** (G3-01e UNKNOWN 1, unchanged): the 2-byte word after `0x06`/`0x07` is not
   an offset under any of the five encodings tried (corpus test, ~10% vs chance).
3. **What `Core.BatmobileWinch`, `Core.WinchPullType`, `Core.ArmouredMode`, `Core.IsVehicleAsleep`
   are.** The import path is `Core.<name>`; whether they are `Core` globals or members of an object
   is not in the packages read. Where it would be answered: `Core.upk`'s export/import tables.
