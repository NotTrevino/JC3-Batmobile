# MECHANICS.md offset-only rows, named from the BmSDK layout

STATUS: done

## Summary

`Research/BatmobileGrab/MECHANICS.md` (1,508 lines, pre-reset) lists **244** values as bare
`offset 0xNNN  <float>` because the cooker stripped the property names. All 244 are now named
from the BmSDK binding layout, each with its declaring class and the generated `.g.cs` file:line:

| quantity | count |
|---|---:|
| offset-only rows | 244 |
| named to a field | **244** |
| inside a struct (container named) | 0 |
| UNKNOWN | **0** |
| bit-packed bool members named | 0 |
| declaring classes | `RVehicleBatmobileBase`, `RVehicleSimBatmobile`, `RVehicleSimCar`, `SVehicle`, `SVehicleSimCar` |

Sections covered: 8 (class, package) contexts — `RVehicleBatmobile` and `RVehicleSimBatmobile`
in each of `Playable_BatmobileFunhouse_SF`, `Playable_BatmobileJoker_SF`,
`Playable_BatmobileMK2_SF` and `Playable_Batmobile_SF`.

Examples (all four packages carry the same rows, so each is named once per section):

| MECHANICS.md line | offset | value | field | declared in | `.g.cs` |
|---:|---|---:|---|---|---|
| 66 | `0x744` | 0.2 | `SquealThreshold` | `SVehicle` | `SVehicle.g.cs:1495` |
| 67 | `0x748` | 0.2 | `SquealLatThreshold` | `SVehicle` | `SVehicle.g.cs:1504` |
| 68 | `0x1210` | 0.75 | `EbrakeTime` | `RVehicleBatmobileBase` | `RVehicleBatmobileBase.g.cs:5273` |
| 69 | `0x1214` | 640000 | `EBrakeBrakeForce` | `RVehicleBatmobileBase` | `RVehicleBatmobileBase.g.cs:5282` |
| 70 | `0x175C` | 0 | `ImpactRoadAssistSceneryDuration` | `RVehicleBatmobileBase` | `RVehicleBatmobileBase.g.cs:6919` |
| 71 | `0x1760` | 0.333 | `ImpactRoadAssistEnemyDuration` | `RVehicleBatmobileBase` | `RVehicleBatmobileBase.g.cs:6928` |

Two offsets that are visible in the ledger and worth calling out because they resolve through a
base class rather than the section class: `0x744`/`0x748` are `SVehicle.SquealThreshold` /
`SquealLatThreshold`, not `RVehicleBatmobile` members — the section class declares nothing at
those offsets, which is exactly the case where a naive same-class lookup would have reported
"stripped/UNKNOWN".

## Files written

- `Tools/scripts/mechanics_names.py` (new, `--write` / `--check`)
- `Research/BatmobileGrab/MECHANICS_NAMES.md` (35,207 B)
- `Research/BatmobileGrab/MECHANICS_NAMES.json` (385,635 B)
- this report

`MECHANICS.md` was **not** edited (read-only input), as the card required. Other inputs read:
`BMSDK_OFFSETS.json`, `CLASS_DEFAULTS.json`, `Working/vendor/BmSDK/*.g.cs`.

## Commands and output

### `--write`

```
$ PYTHONIOENCODING=utf-8 uv run python Tools/scripts/mechanics_names.py --write
PASS  the 244 offset-only rows in MECHANICS.md all parse
      244 rows over 8 sections
PASS  every row gets a name, a struct container or is reported UNKNOWN
      244 named, 0 inside a struct, 0 UNKNOWN
PASS  every named row's .g.cs getter reads Ptr + <the row's offset>
      244 named rows checked, 0 mismatch: []
PASS  every declaring class is on the section class's binding chain
      244 rows, 0 off-chain
PASS  every offset lies inside the class's own size
      244 rows; 0 beyond size []
PASS  bit-packed offsets name every member with its mask
      0 bool members named, masks []
PASS  no member is bound at two different offsets inside one section
      8 sections; 0 members with two offsets: []
PASS  the sections cover 8 vehicle/simulation contexts
      8 (class, package) pairs

8/8 oracles pass
wrote Research\BatmobileGrab\MECHANICS_NAMES.md (35207 B)
wrote Research\BatmobileGrab\MECHANICS_NAMES.json (385635 B)
```

Exit status 0.

### `--check`

```
$ PYTHONIOENCODING=utf-8 uv run python Tools/scripts/mechanics_names.py --check
... 8/8 oracles pass ...
CHECK OK: the stored .md/.json are byte-identical to a fresh recompute
```

Exit status 0.

## How a name is proven, not guessed

1. **Offset** — read from `MECHANICS.md` (`offset 0xNNN`), i.e. the value the package actually
   carries; `MECHANICS.md` itself is never written.
2. **Field** — the member bound at that absolute offset in `BMSDK_OFFSETS.json`, searched from
   the section class outward along the binding chain parsed from each `.g.cs` header
   (`public partial class X : BmSDK.<ns>.Y`). The chain is derived from the bindings themselves,
   so it is not limited to the eight-class chain in `CLASS_DEFAULTS.json`.
3. **Citation** — the declaration line in `Working/vendor/BmSDK/<Class>.g.cs`.
4. **Oracle** — the getter within nine lines of that declaration must read `Ptr + <the row's
   offset>`. This is the check that fails on a wrong file, a wrong line, a wrong declaring class
   or an off-by-one offset; it passes on all 244 rows.

Bit-packed bools and struct containment are implemented (all members at the offset with their
masks; enclosing `StructProperty` plus relative offset and struct member when the struct has a
binding) — **no row in this file needed either path**: every offset-only row resolved to a plain
declared field. That is a property of this file, not evidence that the paths work, and is
recorded as a limitation below.

## Oracles

| # | check | result |
|---:|---|---|
| O1 | 244 offset-only rows parse, over 8 sections | PASS |
| O2 | every row named / struct-contained / UNKNOWN | PASS (244 named) |
| O3 | every named row's `.g.cs` getter reads `Ptr + <offset>` | PASS (0 mismatch) |
| O4 | every declaring class on the section class's chain | PASS |
| O5 | every offset inside the class's own size | PASS |
| O6 | bool offsets name every member with a mask | PASS (vacuous here: 0 bool rows) |
| O7 | no member bound at two offsets in one section | PASS |
| O8 | 8 (class, package) sections | PASS |

## UNKNOWNs

1. **The bool-mask path is unexercised.** No MECHANICS.md offset-only row landed on a
   bit-packed bool, so O6 passes vacuously. The code path exists (it lists every member at the
   offset with `mask_hex`), but it has no passing instance in this file to demonstrate.
2. **The struct path is unexercised.** Zero rows fell inside a struct span, so no container was
   named. Same caveat: implemented, not demonstrated here.
3. **What the values mean mechanically.** This pass names fields only; it does not interpret
   `EBrakeBrakeForce = 640000` or any other number.
4. **Rows in MECHANICS.md that were already named** (property-tag rows with a name) were left
   alone; only the 244 `offset 0x...` lines were in scope.
