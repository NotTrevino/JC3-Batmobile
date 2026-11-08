# The smart search's four `found=true` values — re-verified at the source under R4

STATUS: **done** — every `found=true` from `tmp/freebuff/reports/smart-search-open-unknowns.md` was
re-opened at its own record and re-classified: **2 VERIFIED**, **2 WRONG**, **0 UNVERIFIABLE** for the
claims, plus **one value the judge missed** at F-32's real offset (430.0), which is VERIFIED. The
ready-to-apply table is §4. `FOOTAGE.md`, `MODES.json`, the tracker and `T_ROWS.jsonl` were not
edited; nothing was launched or built.

Two things the first pass got wrong, both now fixed:

* it said **"no value for F-32 enters"** — the dump *does* carry a literal at `BattleModeLength`'s own
  offset (0x1998): **430.0**. The judge simply quoted the neighbouring slot.
* it treated the F-37 rejection as a judge error only. The record is real but lives on
  `Default__RVehicleNPC`, so the member's value is not merely misjudged — it is **not in this corpus**.

## 0. What was re-checked, and how

The four hits are all **text-route** candidates in one derived dump,
`E:/Modding/_shared/gamedata/BmAKgrab/chase/chase2_defaults.json` (a `default_objects` array of 30 records,
each `{bits, class, export, field, object, offset, owner_expected, type, value}`). For each claim I:

1. opened the record itself at its offset (not the judge's summary) and quoted `class`, `object`,
   `export`, `offset`, `type`, `value`;
2. established **which member owns that byte offset** from the SDK accessors in
   `Working/vendor/BmSDK/RVehicleBatmobileBase.g.cs` (`Ptr + N` per property) and from
   `Research/BatmobileGrab/BMSDK_OFFSETS.json`;
3. checked the dump holds exactly **one** record per offset (no competing literal): offsets 6548,
   6552, 6556, 7368, 7372, 7376, 7380 each appear once;
4. checked the declared owner: `RVehicleBatmobileBase : BmSDK.BmGame.RVehicle`
   (`RVehicleBatmobileBase.g.cs:11`), CDO export **10923**, object `Default__RVehicleBatmobileBase`.

**R4 reading.** These records are class-default (CDO) properties serialised at a byte offset — the
value the class loads into that member. That is an offset-addressed default, not an instruction in a
constructor body; no init code assigns these floats literally. Under the "offset or file line" form of
R4 the two matching records are verified; under a strict "instruction in initialisation code" reading
none of the four would be, because UE3 default objects are deserialised tag data. Stated rather than
glossed, and it is the one limitation in §5.

## 1. The four claims

| # | member | judge said | source it named | verdict |
|---:|---|---|---|---|
| 1 | `BattleModeLength` (F-32, 0x1998) | `265.0` | `chase2_defaults.json:107` | **WRONG** — 265.0 is `BattleModeWidth`'s value at 0x1994 |
| 2 | `BattleModeHeight` (F-33, 0x199c) | `250.0` | `chase2_defaults.json:129` | **VERIFIED** |
| 3 | `ImpactShakeAbandonedVehicleFactor` (F-35, 0x1ccc) | `3.0` | `chase2_defaults.json:151` | **VERIFIED** |
| 4 | `ImpactShakeCoolDown` (F-37, 0x1cd4) | `20.0` | `chase2_defaults.json:316` | **WRONG** — right offset, wrong class/object |

## 2. The two that hold

### 2.1 `BattleModeHeight` = 250.0 — VERIFIED

Record at `chase2_defaults.json:129` (offset **6556 = 0x199c**):

```json
{ "bits": null, "class": "RVehicleBatmobileBase", "export": 10923,
  "field": "F-33 BattleModeHeight",
  "object": "Default__RVehicleBatmobileBase",
  "offset": 6556, "owner_expected": "RVehicleBatmobileBase",
  "type": "FloatProperty", "value": 250.0 }
```

The offset is the member's: `RVehicleBatmobileBase.g.cs` declares
`public unsafe float BattleModeHeight { get … Ptr + 6556 }`, and `BMSDK_OFFSETS.json` gives
`BattleModeHeight 6556 float`. Declared type float, record type `FloatProperty`; class and object are
the Batmobile base CDO; value **250.0**. `FOOTAGE.md` F-33 declared 0x199c. Offset, owner, type and
literal all agree.

### 2.2 `ImpactShakeAbandonedVehicleFactor` = 3.0 — VERIFIED

Record at `chase2_defaults.json:151` (offset **7372 = 0x1ccc**):

```json
{ "class": "RVehicleBatmobileBase", "export": 10923,
  "field": "F-35 ImpactShakeAbandonedVehicleFactor",
  "object": "Default__RVehicleBatmobileBase",
  "offset": 7372, "type": "FloatProperty", "value": 3.0 }
```

`RVehicleBatmobileBase.g.cs` declares the accessor at `Ptr + 7372`; `BMSDK_OFFSETS.json`:
`ImpactShakeAbandonedVehicleFactor 7372 float`; F-35 is declared at 0x1ccc. Value **3.0**. The
calibration run independently reached the same field/value (F35 = 3.0), so this is the one hit two
separate passes agree on.

## 3. The two that fail, and the value one of them missed

### 3.1 `BattleModeLength` = 265.0 — WRONG (265.0 is Width); the real value is 430.0

The record the judge quoted is at offset **6548 = 0x1994**:

```json
{ "class": "RVehicleBatmobileBase", "export": 10923,
  "field": "control BattleModeLength",
  "object": "Default__RVehicleBatmobileBase",
  "offset": 6548, "type": "FloatProperty", "value": 265.0 }
```

`0x1994` is **`BattleModeWidth`** (F-31) — `RVehicleBatmobileBase.g.cs` gives
`BattleModeWidth … Ptr + 6548`, `BattleModeLength … Ptr + 6552`, `BattleModeHeight … Ptr + 6556`, and
`BMSDK_OFFSETS.json` agrees (6548 / 6552 / 6556). The dump's `field` string is an annotator's label,
not the engine's property name: it says "control BattleModeLength" on the Width slot. 265.0 is the
known Width default, so the judge attached the Width number to the Length member.

**What the judge missed:** the same dump holds a second record at offset **6552 = 0x1998**, the
Length member's own slot:

```json
{ "class": "RVehicleBatmobileBase", "export": 10923,
  "field": "control (unlabelled width/length neighbour F-32 class)",
  "object": "Default__RVehicleBatmobileBase",
  "offset": 6552, "type": "FloatProperty", "value": 430.0 }
```

430.0 at the offset the SDK calls `BattleModeLength`. 430 > 265 is consistent with a car longer than
it is wide, and the three slots read 265.0 / 430.0 / 250.0 — Width / Length / Height. So F-32 is not
value-less after all; it is **430.0**, and the judge's 265.0 is rejected.

### 3.2 `ImpactShakeCoolDown` = 20.0 — WRONG (right offset, wrong class)

```json
{ "class": "RVehicleNPC", "export": 12268,
  "field": "F-37 ImpactShakeCoolDown",
  "object": "Default__RVehicleNPC",
  "offset": 7380, "type": "FloatProperty", "value": 20.0 }
```

Offset **7380 = 0x1cd4** does match F-37 (`RVehicleBatmobileBase.g.cs`: `ImpactShakeCoolDown … Ptr +
7380`; `BMSDK_OFFSETS.json`: 7380). But the record's class and object are **`RVehicleNPC` /
`Default__RVehicleNPC`**, export 12268 — not the Batmobile base (export 10923), and
`RVehicleBatmobileBase` derives from `RVehicle` (`RVehicleBatmobileBase.g.cs:11`), not from
`RVehicleNPC`. The judge's reason asserts "on the RVehicleBatmobileBase object", which the record
contradicts. A 20.0 at the same offset on another class is a coincidence until the Batmobile-base
record exists.

**Verdict on the claim: WRONG. On the member: UNVERIFIABLE from this corpus** — there is no
`Default__RVehicleBatmobileBase` record at 0x1cd4 in the dump, and the class-default table treats
`ImpactShakeCoolDown` as not serialised (`FOOTAGE.md` F-37: "not serialised … no file value exists").
It would be settled by reading the live CDO or the class-default object's tag stream directly
(`RVehicleBatmobileBase` export 10923), not by a sibling class.

## 4. Ready-to-apply table (for the ledger)

Five columns as asked. `source` is the record, by file line and offset; `id` rides in the member cell.
Only VERIFIED rows belong here.

| member | owner | offset | value | source |
|---|---|---:|---:|---|
| `BattleModeHeight` (F-33) | `RVehicleBatmobileBase` (`Default__RVehicleBatmobileBase`, export 10923) | 0x199c (6556) | **250.0** | `E:/Modding/_shared/gamedata/BmAKgrab/chase/chase2_defaults.json:129`, record offset 6556, `FloatProperty` |
| `ImpactShakeAbandonedVehicleFactor` (F-35) | `RVehicleBatmobileBase` (`Default__RVehicleBatmobileBase`, export 10923) | 0x1ccc (7372) | **3.0** | `chase2_defaults.json:151`, record offset 7372, `FloatProperty` |
| `BattleModeLength` (F-32) | `RVehicleBatmobileBase` (`Default__RVehicleBatmobileBase`, export 10923) | 0x1998 (6552) | **430.0** | `chase2_defaults.json`, record offset 6552, `FloatProperty` — **found by this re-check, not by the judge**; replaces the rejected 265.0 |

Not to be applied: `BattleModeLength = 265.0` (that is `BattleModeWidth`, 0x1994) and
`ImpactShakeCoolDown = 20.0` (that is `Default__RVehicleNPC`, export 12268).

When they are applied, the change belongs in `MODES.json`/`MODES.md` and `FOOTAGE.md` F-31/F-32/F-33/
F-35 as `FILE-VALUE` with the record above as the source, re-rendered by their own generators so
`--check` stays green. That is a separate brief; this report does not touch them.

## 5. What this cannot prove

* **The values are CDO serialised defaults, not instructions.** The offset-addressed record is the
  value the class loads into the member; no constructor or `PostLoad` code was found writing these
  literals. Under a strict "initialisation code" reading R4 is not satisfied by any of the four, and
  the file value is the closest the corpus gets.
* **The dump's `field` strings are annotations.** Two of the four labels are wrong for their offset
  ("control BattleModeLength" on Width; "unlabelled … F-32 class" on Length). The offsets, class,
  object, export, type and value are the record; the name is not evidence on its own.
* **F-32's 430.0 rests on the offset match**, which is strong (SDK accessor + offset table + a
  consistent 265/430/250 triple) but still a text-dump record rather than a live read.
* **F-37 remains open.** The member is declared at 0x1cd4 and ships no value in the tagged stream; a
  20.0 on `RVehicleNPC` says nothing about it.
* Nothing here edits `FOOTAGE.md`, `MODES.json`, the tracker or the pinned ledger, and nothing was
  launched.
