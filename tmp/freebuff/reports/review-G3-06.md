# Review — G3-06 (BmAK untagged/partial remainder and the BmScript defaults)

Reviewer: independent (did not write the card). Date: 2026-11-03.
Inputs read: `tmp/freebuff/reports/G3-06.md`, `Tools/scripts/grab_remainder.py` (864 lines),
`Research/BatmobileGrab/REMAINDER.md` (1,926 lines) and `REMAINDER.json` (1.0 MB),
`Research/BatmobileGrab/objects.jsonl`, `GRAB_BACKLOG.md` §6b, `Tools/scripts/grab_packages_g305.py`,
`Tools/scripts/upk_read.py`, `Research/BatmobileGrab/BMSDK_OFFSETS.json`,
`E:/Modding/_shared/tools/BmSDK-AK/src/BmSDK/Generated/Engine/{CylinderComponent,PrimitiveComponent,
ParticleSystemComponent}.g.cs`, and the cooked packages
`E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole/{Playable_Batmobile_SF,Startup}.upk`
(read-only). Nothing was written except this file; no card output was regenerated; no game was
launched, attached to or read from memory; nothing committed.

## VERDICT: **needs rework**

The census half is solid: every count the card publishes reproduces exactly, `--check` is green and
byte-identical on rebuild, and the tamper tests are real. The defaults half is not. The card's
headline sub-item — *where the 97 class-default property values are* — is answered "UNKNOWN: they
would be in `BmScript`, a package that is not shipped", and that answer is contradicted by bytes the
card could read with its own reader: the cooked class default object
`BmScript.Default__RVehicleBatmobile` is **export 7530 of `Startup.upk`**, 978 bytes, and it parses
from byte 0 as a 93-tag default-property stream carrying exactly those kinds of values. The card
enumerated all 37 *children* of that object and never read the object.

Two of the five declared UNKNOWNs are resolvable today (one from `BMSDK_OFFSETS.json`, one from the
export table the card already walks), and one "measurement" used as evidence cannot see what it
claims to test. Details below, with the fix for each.

## Check output (verbatim)

```
$ uv run --with numpy --with pillow --with pefile --with capstone python Tools/scripts/grab_remainder.py --check
OK untagged 925, partial Projectiles 40, Vehicle 70, Weapons 23, materials 454, startup 97 properties / 37 components; md+json byte-identical to a fresh rebuild
CHECK_EXIT=0
```

Exit status 0. Matches the report line for line. The `--check` asserts the untagged total and
per-object verdict/shape, a tail class per partial object, the CDO prefix oracle, the class-size
oracle, the Rumble identical-payload oracle, `property_names_as_tags.count <= 3`, and byte equality
of both outputs against a fresh rebuild — i.e. it is a real comparison, not a summary echo.

## Spot-checks (5 values labelled decoded, re-read from the raw source)

| # | value as stated by the card | source re-read by me | match |
|---|---|---|---|
| 1 | 925 untagged objects; 768 `empty_stub`; base package 183; `Playable_BatmobileJoker_SF` 334; `MK2` 189; `Funhouse` 183 | `objects.jsonl`: 20,128 rows in 15 packages; rows without `tag_count` = **925**; of those, size 2 = **768**; by package = Joker 334 / MK2 189 / Funhouse 183 / base 183 / Std_6 12 / 3×3 / 6×2 — identical including the tail | **yes** |
| 2 | 97 property objects under `BmScript.RVehicleBatmobile`, 37 under `BmScript.Default__RVehicleBatmobile`; scalars 30 B (Float 6, Bool 5, Int 1), pointer/array 34 B (Object 25, Array 3, Component 1) | `PartialPackage(Startup.upk)`: export_count 174,890; owner counts **97 / 37**; size table by class exactly `{FloatProperty:{30:6}, BoolProperty:{30:5}, IntProperty:{30:1}, ObjectProperty:{34:25}, ArrayProperty:{34:3}, ComponentProperty:{34:1}}`, 56 Functions 39…3,336 B | **yes** |
| 3 | the three Rumble payloads are byte-identical once the counter at byte 2 is masked | masked with `d[:2]+b"\0\0\0\0"+d[6:]` → all three equal **True**; the bytes are `00 00 | 89 1c 00 00 | 8a 1c / 8c 1c`, the only difference being bytes 2–5 | **yes** |
| 4 | partial objects of the base package: Vehicle 70, Weapons 23, Projectiles 40, materials 454; "tail > 2" 9 / 10 / 8 / 61 | recomputed with the card's own `group_of`/`MATERIAL_CLASSES`: **70 / 23 / 40 / 454** (`parsed<size`), **9 / 10 / 8 / 61** (`tail>2`), and `stop!=eof` gives the same 9/10/8/61 (so two of the three rows in the report's table are the same definition twice) | **yes** (see Issue 5 for the one object 454 misses) |
| 5 | the only property name that appears as a tag is `UpgradedGeneratorBonus` on `JokersBatmobile` — `Playable_BatmobileJoker_SF` export 3180, `ArrayProperty` at class offset 8608 | re-scanned all 20,128 rows for the 97 names: exactly **1** hit, and it is that one (`('Playable_BatmobileJoker_SF', 3180, 'UpgradedGeneratorBonus', 'ArrayProperty', 8608)`) | **yes** |

Two further byte-level checks I ran on the CDO components because they are the card's only decoded
vehicle values:

* `FrontCollisionCylinder` (46 B): prefix `int32@4 = 25827` equals the export's name index —
  oracle holds; `0.9997864` (`00 f2 7f 3f`) sits at payload byte **40**; `RearCollisionCylinder`
  holds `0.6011841` at byte 40. Yes.
* `XrayLightComponent` (98 B): `3.0` at byte 16; `SimulationModel` (4,920 B): `0.01` at 16, `0.003`
  at 24. Yes.

## Issues

### 1. The class default object was never read — and it settles UNKNOWN #1 (central, blocking)

The card's chain of evidence is: the 97 property objects hold no value → their names appear on none
of the grab's objects → therefore the defaults live somewhere not shipped. The middle step is run
over `objects.jsonl`, which contains **only the 15 `Playable_Batmobile*` packages** (I listed them:
Joker, MK2, Funhouse, base, Std_1…Std_6 and their `_Std_` siblings — no `Startup`). `Startup.upk`
is exactly where the card itself read the 37 CDO components from, and the CDO export is in the same
table:

```
BmScript.Default__RVehicleBatmobile   export 7530   class RVehicleBatmobile   978 B
walk from 0  -> 93 tags, end 976, "eof"   (payload is 978 B: 976 + the 2-byte terminator)
walk from 12 -> 0 tags (not a prefixed payload; this one parses from byte 0)
```

The stream is not ambiguous — it is a default-property list with real values, ending on the
terminator, e.g.:

```
ObjectNCRProperty @0x20a0 = 169048        ArrayProperty @0x21a0 = UpgradedGeneratorBonus
IntProperty       @0x2170 = 5000          ArrayProperty @0x21b0 = UpgradedGeneratorShielding
BoolProperty      @0x2174 = True          ArrayProperty @0x1954 = ColourLevels (84 B)
FloatProperty     @0x218c = 5.0           ArrayProperty @0x066c = WheelSpeedMap (4 B)
FloatProperty     @0x2190 = 25.0          ArrayProperty @0x06ac = Wheels (20 B)
FloatProperty     @0x219c = 100.0         ArrayProperty @0x005c = Components (20 B)
FloatProperty     @0x1790 = 1300.0        NameProperty   @0x04dc = 'DrivingMode'
FloatProperty     @0x1a60 = 2000.0        NameProperty   @0x19bc = 'Material_Pollen_Override'
FloatProperty     @0x0710 = 4000.0        ObjectNCRProperty @0x038c = 169640
FloatProperty     @0x0430 = 6000.0           (= the `SVehicleMesh` export seen in the card's own
FloatProperty     @0x0744 = 0.5               component table)
FloatProperty     @0x0614 = 1.0
```

So the statement "the defaults are not in the shipped packages' decodable streams" is false, and
"`BmScript` (where such defaults would be authored) is not on disk" is misleading: the cooked CDO
is on disk, in `Startup.upk`, 978 bytes, and the card's own `PartialPackage` reads it without
hitting the budget. What genuinely remains open is narrower and worth stating as such: *which of the
93 tag offsets correspond to which of the 97 declared properties* (the declarations carry no obvious
offset field — see Issue 2).

**Fix:** read export 7530, publish its 93 tags, and restate UNKNOWN #1 as
"values are on the CDO at these 93 class offsets; the name↔offset mapping for the 97 declarations is
UNKNOWN because <the specific reason>".

### 2. Oracle 3 ("96 of the 97 names do not occur as a tag") cannot detect a scalar default

`names_as_tags` matches `tag["name"]`, and in this tag format only some types carry a name. Measured
over the whole grab: tags **with** a name are `StructProperty` 18,325, `ByteProperty` 14,771,
`ArrayProperty` 4,975, `ObjectProperty` 398, `ClassProperty` 3, `FixedArrayProperty` 1. Tags
**without** one are `ObjectNCRProperty` 8,352, `FloatProperty` 7,668, `IntProperty` 6,281,
`BoolProperty` 5,542, `NameProperty` 4,589, `GuidProperty` 1,855, `VectorProperty` 608, … So a
`FloatProperty`, `BoolProperty` or `IntProperty` default could be present in a package and this test
would still return "absent" — it is structurally blind to 12 of the 97. The number 96/97 is
arithmetically right and evidentially vacuous for those 12. (The card's own doc §3a prints
`u32@18` for each property; that field *is* a name index — see Issue 3 — so the tooling to name
things exists.)

**Fix:** say what the test covers (named-tag types only), and drop it as support for "the values are
not in the packages" — the CDO in Issue 1 is the answer.

### 3. Two decoded record fields are characterised more strongly than the bytes allow

The report §4a describes the 30/34-byte payload as "a 26/30-byte record whose fields are a per-object
counter at byte 2 and a name index at byte 18".

* byte 2 is **not a counter**: for all 97 exports it equals `export index − 1` (7305→7304,
  7306→7305, 7308→7307; the exports are contiguous 7304…7311, so "previous sibling" and
  "index − 1" are not distinguishable from these bytes). Either way it is an index field, and the
  conclusion it supports ("no value field lives there") survives.
* byte 18 **is** a name index and it resolves: 58154 → `RVehicleBatmobile` (5×), 59747 (23×),
  33203 (10×), 2×62939, and small values such as 36/61/119/458/2317 for others — i.e. it names the
  declaring class, not the property (which is why the three Rumble properties share it). The card
  never looked the index up, so this readable fact is reported as an unnamed field.

### 4. UNKNOWN #2 (member names of the decoded CDO offsets) is resolvable from a file the card already has

`@0x13c` = 316 and `@0x16c` = 364 are not subclass fields at all:

* `BMSDK_OFFSETS.json` → `PrimitiveComponent` → `{"kind": "ComponentProperty", "member":
  "ReplacementPrimitive", "offset": 316}`;
* `BmSDK-AK/src/BmSDK/Generated/Engine/PrimitiveComponent.g.cs:2183` — `FloatProperty:
  PerInstanceRandom`, `Ptr + 364`.

So the two tags that appear on **every one of the 37 CDO components** are `ReplacementPrimitive`
(null) and `PerInstanceRandom`; the per-component floats the doc tabulates (0.9997864, 0.6011841,
0.9370708, 0.67…, 0.0143…0.9004) are `PerInstanceRandom`, not authored vehicle parameters. That
changes how a reader will use those numbers. The UNKNOWN is true only for the *subclass-specific*
offsets (`CylinderComponent` 540/544, `ParticleSystemComponent`, …), which `BMSDK_OFFSETS.json`
genuinely does not carry (41 classes; `CylinderComponent`, `ParticleSystemComponent`,
`StaticMeshComponent` absent, `SVehicleWheel`/`PointLightComponent`/`PrimitiveComponent` present) but
the BmSDK tree itself does (`CylinderComponent.g.cs`: `CollisionHeight` 540, `CollisionRadius` 544,
`AABBScale` 548).

### 5. One material-class partial object is outside the "accounted for" set

With the card's exact `MATERIAL_CLASSES` whitelist the four groups sum to **587** (70+23+40+454), but
the base package has one more material-class partial object that the whitelist does not match and
whose owner path contains no "Material": export **656**, class
`MaterialExpressionTextureSampleParameterSubUV`, `Smoke.MAT_Smoke_4x4_LIT`, 66/64 B. It lands in
"other" (4,903 objects, never listed), so the Done line "every partial object in
Vehicle/Weapons/Projectiles/materials accounted for" is short by one object. Its tail is 2 bytes —
almost certainly the same terminator class as the other 393 — but the record does not say so.

### 6. Smaller items

* **Dead verdict branch.** In `account_untagged`, `if shape == "empty_stub"` is tested before
  `elif cls == "Package"`, so the "import stub - carries no data" verdict and its evidence string
  are unreachable: all 696 `Package` stubs get "no properties to decode". The doc's own §1 verdict
  table reflects this, so nothing published is wrong — the code and the report's prose ("a class
  default stub", §4a) both describe a case that never renders.
* **`native_record` asserts a format the test does not establish.** The test is "no start 0..19
  closes a 2+ tag stream"; calling the result a *native* record is an interpretation. 20 of the 152
  are `Function` payloads (e.g. `MovePawnTo` 193 B = `00 00 00 00 00 00 56 fe ff ff 03 …`) — script
  bytecode, not a native C++ record. The shape is defined in the doc, so this is naming, not a false
  value; still, `untagged_payload` would be honest and `native_record` is what later cards will cite.
* **Two of the three rows in the report's §3 table are the same definition** ("tail > 2 bytes" and
  "`stop != eof`" give 9/10/8/61 identically). The text presents them as independent definitions
  that both fail to reproduce the card's Vehicle 4 / materials ~36. On this corpus they are one
  definition counted twice; only `parsed<size` and `tail>2` are independent.
* **`--check`'s `property_names_as_tags["count"] > 3`** allows three hits while the record claims
  one. Harmless today, but it means a regression to 2–3 hits would pass silently.

## Resolvable UNKNOWNs

1. **UNKNOWN #1 — where the 97 defaults are. Resolvable, and resolved in part.** Read
   `Startup.upk` export 7530 (`BmScript.Default__RVehicleBatmobile`, 978 B) with the card's own
   `PartialPackage` and `upk_read.walk_tags(pkg, data, 0)`; it yields 93 tags ending on the 2-byte
   terminator (976/978) with real defaults (see Issue 1). What stays UNKNOWN afterwards is only the
   name↔offset mapping for the 97 declarations, and even that has a route: the declarations' `u32@18`
   names the declaring class (58154 = `RVehicleBatmobile`), and their export names are in the
   table, so the pairing can be attempted property-by-property against the CDO's offsets.
2. **UNKNOWN #2 — member names of the decoded CDO offsets. Resolvable for the two offsets that
   matter most.** `PrimitiveComponent` is in `BMSDK_OFFSETS.json` (`ReplacementPrimitive` 316,
   and `PerInstanceRandom` 364 in `PrimitiveComponent.g.cs`); the subclass fields are in the BmSDK
   tree even where `BMSDK_OFFSETS.json` lacks the class (`CylinderComponent.g.cs` 540/544/548).
   Only the offsets with no BmSDK member at all stay unknown.
3. **UNKNOWN #3 — the 3 untagged objects "not reached by the decoded graph". Resolvable by
   ownership.** They are `Loc` (StructProperty, outer `RHidePoint_Batmobile.MovePawnTo`),
   `MovePawnTo` (Function, outer `BmScript.RHidePoint_Batmobile`), and `Interactions`
   (RInteractionComponent, outer `BmScript.Default__RHidePoint_Batmobile`) — i.e. a function, its
   local, and a component of the class **`BmScript.RHidePoint_Batmobile` (export 5)**, which the
   card's own walk already lists as reachable. Following `outer_index` one step (the same link the
   card uses to build its seeds and its CDO owner sets) places all three inside a reachable class's
   subtree. They are hide-point members, not vehicle properties — a decoded answer, not a runtime
   question.
4. **UNKNOWN #4 (6 payloads past the 512 MiB budget)** is correctly reported; nothing in the bytes
   makes it cheaper, and the reader's refusal is the right behaviour.
5. **UNKNOWN #5 (the card's 4 / ~36 partial counts)** — not resolvable from `objects.jsonl` alone;
   the superset accounting is the right response. Note that the ~36 figure is also consistent with
   the 61 `tail>2` materials objects if the 2026-11-02 count excluded `MaterialExpression` children,
   which is testable if anyone wants it settled.

## What the card gets right (so the rework does not disturb it)

* The entire untagged census (925; 768/152/5; 696 `Package`, 30 `RAkAudible`, …; every package
  count; the by-class table summing to 925; 17 reachable / 3 UNKNOWN / 757 / 148 verdict split).
* The 20,128-object grab total and the 15-package scope.
* The 97/37 split, the class-determined payload sizes (30 vs 34, with the exact class breakdown),
  and the identical-payload oracle.
* The partial-object accounting under `parsed<size` (587 objects, 70/23/40/454) and the `tail>2`
  reconciliation that reproduces Weapons 10 and Projectiles 8 exactly.
* The single tag hit, down to package, export, class and class offset.
* The CDO prefix oracle (byte 4 = the export's own name index) — I re-checked four payloads
  (25,827 / 56,206 / 67,313 / 59,263), all matching, and 28/37 components qualify as "prefixed" with
  no mismatch; the 9 non-prefixed ones are the small 14-byte records where no prefix is expected.
* The honesty of the limitations section and the two tamper tests (924 ≠ 925 caught, stale md
  caught).

## Required changes before this card can be called done

1. Add export 7530 (`BmScript.Default__RVehicleBatmobile`, `Startup.upk`) to the record, publish its
   93 tags, and rewrite UNKNOWN #1 and the doc's §3a conclusion ("the values are not in the shipped
   packages' decodable streams") accordingly.
2. Replace oracle 3 with a statement of what it can see, or with a per-type check that includes the
   scalar case (a scalar tag carries no name — so the test must be offset-based, not name-based).
3. Name `0x13c` = `ReplacementPrimitive` and `0x16c` = `PerInstanceRandom`, and reword the component
   table so the `PerInstanceRandom` floats are not read as authored vehicle parameters.
4. Resolve the 3 untagged objects by `outer_index` and drop UNKNOWN #3 (or restate it as
   "owned by a reachable class, not referenced by one").
5. Add `MaterialExpressionTextureSampleParameterSubUV` (or match material classes by prefix) so the
   materials group is 455 and the Done line is exactly true.
