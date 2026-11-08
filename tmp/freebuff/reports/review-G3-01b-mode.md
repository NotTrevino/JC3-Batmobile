# Independent review — G3-01b-mode (which BmAK collision mesh is live per mode)

Reviewer: independent (did not write the card). Date: 2026-11-03.
Targets read: `tmp/freebuff/reports/G3-01b-mode.md`, `Research/BatmobileGrab/COLLISION_MODES.md`,
`Research/BatmobileGrab/COLLISION_MODES.json`, `Tools/scripts/grab_collision_modes.py`.
Read-only: I ran `--check` only. I did **not** run `--write` (it would have overwritten the card's
outputs). Nothing under `E:/Games` was written; no game was launched.

Method note / limitation: my spot-checks use the same decoder the card uses (`Tools/scripts/upk_read.py`),
so a decoder bug would be common-mode. I compensated with two independent cross-checks — the export
table printed by `CONTROLS.md` (a different card, different script) and byte-level operand patterns in
the function bodies, which do not depend on the tag walker.

---

## VERDICT: **needs rework**

The mode bodies really are empty of `SetHidden`/mesh references — that negative stands. But the card's
central conclusion, that the selector is **native and referenced by no UnrealScript**, is **contradicted
by the bytes**: `BmGame.upk` export **10894 `RVehicleBatmobileBase.SetBatmanVsBatmobileCollisionMode`**
(291 B) references the mode property and **both** collision-mesh component properties in its body. The
card scanned that very function (it is inside its 2,483-function corpus) and reported no hit, because its
needle set never included the property exports those bodies actually use. So one of the three `UNKNOWN`
verdicts is not UNKNOWN — it is a 291-byte function away — and the card does not meet its own Done
criterion for "which collision mesh is active per mode".

---

## 1. Check output (verbatim)

Command run (the card's own, with exit status not piped away):

```
cd "E:/Modding/JC3-Batmobile" && uv run python Tools/scripts/grab_collision_modes.py --check; echo "EXIT=$?"
```

```
OK 2 packages, 6 state functions, 12 corpus hits, 3 verdicts
EXIT=0
```

This matches the report's quoted `--check` line exactly, including the count of 12 (which is 12
*functions*; the JSON holds **16** hit records — see issue I5).

---

## 2. Spot-checks — 5 decoded values re-read from the raw packages

All values below were read by me with `upk_read.Package` + `pkg.data(export)` and `struct` — not copied
from the card's outputs.

| # | decoded value claimed | where I read it | match |
|---|---|---|---|
| 1 | FName indices `BatmanCollisionMeshBattleMode0` = 4735, `...PursuitMode0` = 4737, `BatmanVsBatmobileCollisionMode` = 4844, `CollisionComponent` = 18394, `SetHidden` = 70289, `SetActorCollision` = 69657, `SetBlockRigidBody` = 69814 (BmGame.upk, 84,813 names) | `names[4735/4737/4844/18394/70289/69657/69814]` of `BmGame.upk` | **yes** (all seven exact) |
| 2 | Startup.upk (67,407 names) has `BatmanCollisionMeshBattleMode0` = 5198, `...PursuitMode0` = 5200, and **no** `BatmanVsBatmobileCollisionMode` | Startup.upk name table, full scan | **yes** (ABSENT confirmed) |
| 3 | State exports 10525 `RVehicleBatmobileBase.PursuitMode` (class `State`, 83 B) and 10547 `RVehicleBatmobileBase.BattleMode` (`State`, 107 B) | `object_class` / `object_path` / `exports[i]["size"]` | **yes** |
| 4 | The six mode functions 10515/10517/10524/10529/10533/10546 are `Function`s whose outer is the State export, with script slices 218/19/680/513/538/514 B | export table outer index + `data(22:-16)`; SHA-1 of each slice | **yes** — sizes and all six `script_sha1` values equal those stored in `COLLISION_MODES.json` (`3847dcc4b412`, `ffcd226b4c5e`, `00a11a56778d`, `621255c88373`, `ae7e82e1df52`, `e311339268ab`), so the card's inputs have not drifted |
| 5 | Component exports: BmGame 176111/176112 = `StaticMeshComponent Default__RVehicleBatmobileBase.BatmanCollisionMesh[Battle\|Pursuit]Mode0`; Startup 171103/171104 = same names on `Default__RVehicleBatmobile`; Playable 5392/5393 = instances under `Batmobile` | export table of the three packages | **yes** for indices/classes — but see I4: the Playable pair is never actually searched by the script |

Instrument sanity (not one of the five): I reproduced the card's `SetHidden` offsets in
`RBatmobileWinch.FireWeaponInternal` (export 48056) — slice 1,719 B, hits at **1625** and **1645**, exactly
as the doc's corpus table says. The search mechanics work where a needle exists.

---

## 3. Issues

### I1 (blocking) — the selector *is* referenced by UnrealScript; the "native, not referenced" inference is false

`BmGame.upk` export **10894**, class `Function`, path `RVehicleBatmobileBase.SetBatmanVsBatmobileCollisionMode`,
**291 bytes**. 4-byte values in that body:

| operand | export it resolves to | byte offsets in 10894 |
|---|---|---|
| 9777 | `RVehicleBatmobileBase.BatmanVsBatmobileCollisionMode` (ByteProperty) | 30, 61, 91, 265 |
| 9797 | `RVehicleBatmobileBase.BatmanCollisionMeshPursuitMode` (ComponentProperty) | 76, 133 |
| 9798 | `RVehicleBatmobileBase.BatmanCollisionMeshBattleMode` (ComponentProperty) | 106, 163 |
| 69765 | the function's own name | 283 |

The three property operands appear in a repeated token pattern (`9a <expr> 01 <prop-index> … 24 01/02 16
1c <jump>`), i.e. the setter reads the mode argument and touches the mode property plus **both** mesh
component properties. This is exactly the "hide one mesh, show the other" site the card expected to find.

Damage to the card:

- Report/STATUS: "*`BatmanVsBatmobileCollisionMode` and both mesh component names appear in **no** script
  blob … Which mesh is live per mode stays UNKNOWN, with the search and the place it would be settled
  written down*" — the first half is only true of the **FName indices**; the selector has a dedicated
  UnrealScript setter, in `BmGame.upk`, and the doc's `selector` verdict evidence ("appears in no state or
  Batmobile/vehicle function body") is **false**: 10894's path contains `Batmobile`.
- The inference paragraph ("consistent with the selector being **native** … never referenced by
  UnrealScript, and not serialised") must be withdrawn, not merely relabelled. Good practice that it was
  labelled an inference; the premise is simply wrong.
- Why the search missed it: the needle set is FName indices (4735/4737/4844) plus component **object**
  exports (176111/176112). These bodies address properties by **property export index** (9777/9797/9798).
  **Every one of the offsets 30, 61, 76, 91, 106, 133, 163, 265 lies inside the card's own slice**
  (`data[22:-16]` of a 291-byte export = bytes 22–274), so the script *read the answer* and had no needle
  for it. This is a needle-class defect, not a decoder defect.
- Corroborating local evidence the card did not use: `CONTROLS.md:170` already lists export 9777
  `BatmanVsBatmobileCollisionMode` (ByteProperty, `RVehicleBatmobileBase`), and `CONTROLS.md:9797/9798`
  rows (`BatmanCollisionMeshPursuitMode` / `...BattleMode`, ComponentProperty). The card's own sibling
  documents already held the operand class it failed to search for.
- The whole-image scan also shows why FName-index matching alone is weak: packed 4844 occurs 71 times in
  BmGame's image (6 of them inside `RBMRoomAIState.CheckForTooManyStaticGuards`), all false positives.
  Absence under this method carries almost no evidential weight, which the verdicts do not admit.

### I2 — the corpus is not "every vehicle function": 178 vehicle functions and the mode switch itself are outside it

`resolve_funcs` matches `"Batmobile" in path or "Vehicle" in path` on the **one-level** path
`<outer>.<name>`. Functions outered on a `State` render as `<State>.<fn>`, so their class name never
appears and they match neither the six hard-coded indices nor the corpus substring test. Measured: **178**
such functions in `BmGame.upk` whose owning class name contains Batmobile/Vehicle, e.g.
`PursuitMode.BattleDodge` (10519), `BattleMode.BattleDodge` (10544), `BattleMode.TriggerBoost` (10526),
`BattleMode.VehicleStrafe` (10536).

Worse, the concrete mode switch is missed for a second reason: **`DrivingMode.ToggleBattleMode`
(`BmGame.upk` 105028, 238 B)** — named in sibling card G3-02b as the mode switch — has path
`DrivingMode.ToggleBattleMode`, class `RPlayerController`, so no filter in the script reaches it.

So the doc/report sentence "*the corpus scan covers every Function whose path names a Batmobile or vehicle
class, so a selector outside the state bodies is not missed silently*" is false. (I checked 105028's body
for the property operands: it does **not** contain 9777/9797/9798, so this is a coverage-honesty defect
rather than a second missed answer — but it is the function most likely to hold the branch, and the card
asserts it was searched.)

### I3 — the 38-byte head/tail exclusion is a real blind spot and is not stated as one

`script_of` returns `data[22:len-16]`. The report mentions the slice only as "the same slice
`grab_controls_consumers.py` walks"; neither report nor doc lists the excluded 22+16 bytes as a limit.
Two demonstrations from the packages:

- In export 10894 the function's own name operand sits at byte **283 of 291** — inside the excluded
  16-byte tail.
- `TryToChangeMode` (`BmGame.upk` 10552) is 43 bytes, so its "script" is the **5 bytes** at 22–26; the
  4-byte values 10549 and 10551 sit at bytes 2 and 11, inside the excluded head.

Any short function is therefore effectively unsearched, and a body whose operand sits in the tail is
invisible. The report's table presents `script bytes` per function as if it were the whole body.

### I4 — `Playable_Batmobile_SF.upk` is claimed as an input but the script never opens it

`PACKAGES = ("BmGame.upk", "Startup.upk")`. `COMPONENTS` carries a `Playable_Batmobile_SF.upk` entry
(5392/5393), but needles are built inside the loop over `PACKAGES`, so those two indices are **never
searched** — dead data. Consequently:

- the report's "Read-only inputs: … `Playable_Batmobile_SF.upk` (component instances)" is false;
- the report's "object references … Playable_Batmobile_SF instances 5392 / 5393" is false as a statement
  about what was searched;
- `--check` prints "OK **2** packages", quietly contradicting both.

(The report's prose that package-local indices cannot be referenced from BmGame bytecode is correct, and
the base templates are the right proxies — but then the Playable row should not be presented as searched.)

### I5 — counts that do not match the bytes or the card's own JSON

| claim | actual (measured) |
|---|---|
| "0 hits in the **four** mode bodies (**1,482** bytes)" | **six** bodies; 218+19+680+513+538+514 = **2,482** bytes |
| "**12 hits**, all `SetHidden`" (corpus) | 12 **functions**, **16** hit records (`sum(len(hits))` over `COLLISION_MODES.json` = 16) |
| "Startup … `RVehicleBatmobile.Tick` #7415 (**the only** `RVehicleBatmobile` function in that package)" | Startup has **56** Functions on `RVehicleBatmobile`; 7415 is the only one *named* BeginState/EndState/Tick (966 B, 928 B slice) |
| "2,483 functions in BmGame.upk" | **2,483** exactly — correct |

The 928-byte Startup slice is a `Tick` of `RVehicleBatmobile`, not of `RVehicleBatmobileBase`, and the doc
labels it "(path-resolved)" in a table whose other rows are the base class's states; the distinction
matters for anyone reading the table as "the vehicle's tick was cleared".

### I6 — parts of `--check` are vacuous

- `check()` contains `for row in p["state_functions"]: if row["script_bytes"] and not row["hits"]: continue`
  — a loop whose body does nothing, yet the report lists it among what `--check` "asserts".
- `resolve_funcs` has a dead `for` loop with an empty body.
- The real assertions are: outputs exist, every verdict has value+evidence, at least one verdict is
  derived/UNKNOWN, no drift against a fresh `build()`, five headings present. None of them can detect a
  missing needle class or an unsearched package — precisely the defects that matter here. `--check` green
  is therefore not evidence for this card's claim.

### I7 — an unlabelled epistemic step: absence treated as a finding

The doc defines `UNKNOWN = not found by the search`, which is honest. But the verdicts are phrased as
decoded negatives ("*no reference to either mesh name, to BatmanVsBatmobileCollisionMode, to
CollisionComponent, or to SetHidden/… in the state's functions*"). For the six state bodies that phrasing
is supported by the bytes. For the `selector` verdict and for the report's headline ("the honest answer is
that the selector is not referenced in any mode or vehicle function body") it is not: the statement
conflates "not found with these needles" with "not present", and the inference built on it fails (I1).

### I8 (minor) — three different class-default chains are treated as one

BmGame 176111/176112 are outered on `Default__RVehicleBatmobileBase`; Startup 171103/171104 on
`Default__RVehicleBatmobile`; Playable 5392/5393 on `Batmobile`. The report calls all of them "the base
template exports" and G3-01 calls them "instances of `Default__RVehicleBatmobile.*`", which is not what the
BmGame outers say. The two collision mesh components are declared on the **Base** class, which is also
where `BatmanVsBatmobileCollisionMode`, `BatmanCollisionMeshPursuitMode` and `BatmanCollisionMeshBattleMode`
live (9777/9797/9798), and where the setter is defined (10894). Ownership of the selector belongs to
`RVehicleBatmobileBase`, not `RVehicleBatmobile`.

---

## 4. Resolvable UNKNOWNs (from the bytes / from data already in the repo)

1. **Which mesh per mode — resolvable by decoding export 10894, 291 B.** The body pairs the mode property
   (9777) with 9797 and 9798 under the same comparison/branch pattern. 291 bytes is hand-decodable against
   the token table, and it is UnrealScript, not the native path the card proposes. *This is the card's own
   Done criterion; it needs no new instrument.*
2. **Who calls the setter — resolvable by decoding three small bodies already located.** Whole-image scan
   for the setter: `RVehicleBatmobileBase.StartSelfDrive` (export 10701) contains FName 69765 (the setter's
   name); `RVehicleBatmobileBase.LandedJump` (export 10895) contains export index 10894 (a direct call).
   Decoding those two plus `DrivingMode.ToggleBattleMode` (105028) and `RVehicleBatmobileBase.TryToChangeMode`
   (10552, the native thunk) gives the call graph from input/mode switch to the mesh swap.
3. **The runtime read the card asks for already exists in the repo.** `Research/BatmobileGrab/runtime/*.jsonl`
   (5 files) sample `vehN.BatmanVsBatmobileCollisionMode` directly: values observed **0 ×9, 1 ×2**, including
   a 0→1 change at `2026-11-03T10:05:15.778Z`. The sampler does not log the current mode state, so the
   value↔mode map is not yet readable — adding that one key to the existing sampler settles verdicts 1–2 by
   measurement without any new tooling. The card cites "a runtime read of bHidden" as the only route and does
   not mention that the field and the instrument are already captured locally.
4. **"No explicit default exists" is not yet shown for the components themselves.** All six component
   exports (Playable 5392/5393, BmGame 176111/176112, Startup 171103/171104) yield **zero property tags**
   from `walk_tags` at byte 0 (immediate terminator). That means no serialised visibility flag is readable
   *from offset 0*; `upk_read.best_walk` (starts 0/1/2/4) was not run, so "not serialised" is still open
   for the component objects (COLLISION.md's zero-tail observation is about a different object set).

---

## 5. What the card gets right (so the rework does not throw it away)

- The six mode functions and both State exports are real, path-verified, correctly sized, and their
  SHA-1s reproduce — inputs are not stale.
- No `SetHidden` / `SetActorCollision` / `SetBlockRigidBody` / mesh-name reference exists in the six mode
  bodies; the corpus hit list (12 functions, 16 offsets) reproduces exactly, including offsets 1625/1645.
- The two method defects it found and fixed are genuine and correctly fixed: package-local export indices
  (Startup 10525 is an `AkDialogueAnim`, verified), and State-owned functions hanging off the State export
  (outer indices verified for all six).
- The discipline of labelling the native-selector paragraph as an inference rather than a fact is the right
  instinct; it is the premise, not the labelling, that failed.

---

## 6. Required changes before this card can be called done

1. Withdraw the "native / not referenced by UnrealScript" conclusion; add export 10894 to the searched set
   and decode it (or report it as the located but undecoded site, with its 291 bytes and the eight operand
   offsets above).
2. Add property-export needles (9777, 9797, 9798) and the mode-switch functions (105028, 10552, 10701,
   10895) to the search, and fix the corpus filter so State-owned functions and `DrivingMode.*` are covered
   — or state the exclusion explicitly.
3. Either search `Playable_Batmobile_SF.upk` or remove it from the inputs list and from the "what was
   searched" table.
4. Correct the four counts in I5 and state the 22/16-byte slice exclusion as a limitation with the
   short-function cases named.
5. Make `--check` assert something about coverage (e.g. every corpus candidate is either scanned or listed
   as skipped, and every package in `COMPONENTS` is actually opened); delete the no-op loops.
6. Keep the three `UNKNOWN` verdicts only where they survive the corrected search — on present evidence,
   verdict 3 does not.
