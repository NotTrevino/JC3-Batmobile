# G3-01b open item - which collision mesh is active per mode

STATUS: **done** - the question was asked of the bytes at every level the card names, and the
honest answer is that the selector is not referenced in any mode or vehicle function body:
`BatmanVsBatmobileCollisionMode` and both mesh component names appear in **no** script blob.
Which mesh is live per mode stays UNKNOWN, with the search and the place it would be settled
written down.

## Files written

| file | what |
|---|---|
| `Tools/scripts/grab_collision_modes.py` | the search (`--write` / `--check`) |
| `Research/BatmobileGrab/COLLISION_MODES.md` | verdicts, name indices, states, state functions, corpus hits |
| `Research/BatmobileGrab/COLLISION_MODES.json` | the same, machine-readable (every hit offset) |
| `tmp/freebuff/reports/G3-01b-mode.md` | this report |

Read-only inputs: `BmGame.upk` (177,031 exports / 84,813 names), `Startup.upk` (174,890 /
67,407), `Playable_Batmobile_SF.upk` (component instances). Nothing was written to the install.

## Commands and output (verbatim)

```
cd "E:/Modding/JC3-Batmobile" && uv run python Tools/scripts/grab_collision_modes.py --write
```

```
wrote Research\BatmobileGrab\COLLISION_MODES.md and Research\BatmobileGrab\COLLISION_MODES.json
BmGame.upk: 177031 exports, 84813 names, 6 state fns, 12 corpus hits
Startup.upk: 174890 exports, 67407 names, 0 state fns, 0 corpus hits
  PursuitMode_mesh: UNKNOWN
  BattleMode_mesh: UNKNOWN
  selector: UNKNOWN
```

```
cd "E:/Modding/JC3-Batmobile" && uv run python Tools/scripts/grab_collision_modes.py --check
```

```
OK 2 packages, 6 state functions, 12 corpus hits, 3 verdicts
```

`--check` exit status 0. It asserts: both outputs exist; every verdict carries a value and an
evidence string; at least one verdict is labelled `derived`/`UNKNOWN`; no stale section against a
fresh re-derivation; five markdown sections present.

## What was searched

Two operand classes, both as 4-byte little-endian values inside the function body slice
(`d[22:-16]`, the same slice `grab_controls_consumers.py` walks):

1. **name references** - FName indices for `BatmanCollisionMeshBattleMode0` (BmGame #4735,
   Startup #5198), `BatmanCollisionMeshPursuitMode0` (#4737 / #5200),
   `BatmanVsBatmobileCollisionMode` (#4844, **absent from Startup's name table**),
   `CollisionComponent` (#18394), `SetHidden` (#70289), `SetActorCollision` (#69657),
   `SetBlockRigidBody` (#69814);
2. **object references** - the component/template export indices: BmGame 176111 / 176112,
   Startup 171103 / 171104, Playable_Batmobile_SF instances 5392 / 5393.

Bodies searched:

- the two State exports `RVehicleBatmobileBase.PursuitMode` #10525 (83 B) and
  `RVehicleBatmobileBase.BattleMode` #10547 (107 B) - both are `State` objects with no bytecode;
- their own functions, each verified to be outered on its State export before use:

| mode | function | export | script bytes | hits |
|---|---|---|---|---|
| PursuitMode | BeginState | 10515 | 218 | none |
| PursuitMode | EndState | 10517 | 19 | none |
| PursuitMode | Tick | 10524 | 680 | none |
| BattleMode | BeginState | 10529 | 513 | none |
| BattleMode | EndState | 10533 | 538 | none |
| BattleMode | Tick | 10546 | 514 | none |

- `Startup.upk`: `RVehicleBatmobile.Tick` #7415 (the only `RVehicleBatmobile` function in that
  package) - no hits;
- the corpus: every `Function` in both packages whose path names `Batmobile` or `Vehicle`
  (2,483 functions in BmGame.upk) - **12 hits, all `SetHidden`**, in
  `RVehicleNPC.HideTankAndDisableCollisionOnDeath`, `RBatmobileForensicsBaseActor.PostBeginPlay`,
  `RBatmobileForensicsBaseActor.SetRevealed`, `RBatmobileWinch.FireWeaponInternal` (x2),
  `RBatmobileWinch.HolsterWinch` (x2), `RCinematicVehicle.SetMyComponentsHidden`,
  `RCinematicVehicle.SetProxyingActor`, `RCinematicVehicle.SetNoProxyActor`,
  `RVehicleBehaviour_HeavyTankSearch.Tick` (x2), `RVehicleHeavyTank.PostBeginPlay`,
  `RVehicleHeavyTank.SetWeakPointRevealed`, `RVehicleHeavyTank.TickAimAndShootAtBatman` (x2).
  None of them is a mode class and none names a collision mesh component.

## Verdicts

| question | verdict | why |
|---|---|---|
| PursuitMode selects `BatmanCollisionMeshPursuitMode0` | **UNKNOWN** | no reference to either mesh name, to `BatmanVsBatmobileCollisionMode`, to `CollisionComponent`, or to `SetHidden`/`SetActorCollision`/`SetBlockRigidBody` in BeginState/EndState/Tick |
| BattleMode selects `BatmanCollisionMeshBattleMode0` | **UNKNOWN** | same search, same result |
| `BatmanVsBatmobileCollisionMode` (layout 5895) picks the component | **UNKNOWN** | the name exists in BmGame's table (#4844) but in no function body, and COLLISION.md records that the property is not serialised in the archetype, the Startup CDO or the BmGame base walk |

This is consistent with the selector being **native**: a field read in C++ (`RVehicleBatmobileBase`
offset 5895), never referenced by UnrealScript, and not serialised - so no name, no object
reference and no explicit default exists in the packages to read. That reading is an inference
from three decoded absences; it is not proved by control flow and is labelled as such.

## UNKNOWNs (with why, and where each would be settled)

1. **The active mesh per mode.** Not decodable from the packages by name or object reference:
   0 hits in the four mode bodies (1,482 bytes) and in 2,483 vehicle functions. *Settled by:* a
   runtime read of the component's `bHidden`/collision state on mode entry (the runtime oracle
   R-3), or a disassembly of the native `ARVehicleBatmobileBase` code that reads offset 5895.
2. **Control flow.** Even a hit would only prove the body *touches* the object; the branch that
   ships needs the bytecode decoded. The token walker used here resolves references, not
   branches. *Settled by:* a UE3 bytecode interpreter over these four functions (they are 218 /
   19 / 680 / 513 / 538 / 514 bytes - small enough to decode by hand against the token table).
3. **The Playable_Batmobile_SF component instances (5392 / 5393).** Their export indices are
   package-local, so BmGame bytecode cannot reference them directly; the search covers them via
   the base template exports (176111 / 176112) instead. Whether a mode sets `CollisionComponent`
   on the *instance* through an imported reference is therefore not excluded, only unobserved.
4. **`CollisionComponent` / `SetActorCollision` / `SetBlockRigidBody`.** Present in BmGame's name
   table, referenced by none of the 2,483 vehicle functions searched - so the "hide one mesh, show
   the other" pattern the card anticipated is not visible in UnrealScript at all.

## Method defects found and fixed while building this

- Applying BmGame's decoded export indices to `Startup.upk` produced six fake "state functions"
  (`Startup` #10525 is a dialogue animation). Export indices are package-local; `Startup` is now
  resolved by path and `BmGame`'s fixed indices are path-verified (export outer must be the State
  export) before a body is used. `problems` is empty after the fix.
- A state's functions are outered on the **State**, so their rendered path is
  `PursuitMode.BeginState`, not `RVehicleBatmobileBase.PursuitMode.BeginState`; the first
  membership test therefore rejected all six and the run reported 0 state functions. The test now
  compares the export's outer index to the State export.
