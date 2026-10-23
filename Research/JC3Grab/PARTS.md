# JC3 vehicle part tables — G2-7 solved

**Status: solved.** `Tools/scripts/jc3adf.py` reads the ADF v4 files directly and
`Tools/scripts/jc3parts.py build` decodes **233 of 233** vehicle parts modules — **11,643 parts**,
0 failures — in 34 seconds. Gibbed's `ConvertAdf` refuses 229 of those same files; it is still used
for everything else and nothing about the existing grab changed.

Raw game bytes stay outside the repo (`E:\Modding\_JC3grab`); the derived table is
[PARTS_TABLE.jsonl](PARTS_TABLE.jsonl) (2.6 MB) and the human summary
[PARTS_TABLE.md](PARTS_TABLE.md).

## 1. Why the converter was failing

`ConvertAdf` deserialises ADF v4 by *guessing* where an inline array copy sits
(`InstanceInfo.GuessInlineArrayCopyPosition`); it throws `NullReferenceException` four member levels
down when the guess does not land on a real instance. Measured by hand:

* the 31-type dictionary and the name table are **byte-identical in 80 of 80** parts modules — so it
  was never a missing type, and a newer DLL built on the same guess was never going to fix it;
* only the payload differs.

## 2. The format (from Gibbed's own `AdfFile.cs`, then confirmed on the files)

```
header     u32 magic ' FDA', u32 version=4,
           11 × u32: instanceCount, instanceOffset, typeCount, typeOffset,
                     stringHashCount, stringHashOffset, nameCount, nameOffset,
                     totalSize, unknown2C..34, then a NUL-terminated comment
data       from the instance's own offset (0x50 in every parts file)
instances  u32 nameHash, u32 typeHash, u32 dataOffset, u32 size, s64 nameIndex
types      u32 code, u32 size, u32 align, u32 nameHash, s64 nameIndex,
           u32 flags, u32 elementTypeHash, u32 elementLength, u32 memberCount,
           then memberCount × { s64 nameIndex, u32 typeHash, u32 size, u32 offset,
                               u32 defaultType, u64 defaultValue }
names      count × u8 length, then the names back to back, each NUL-terminated
```

Value storage, which is the part that matters:

| kind | storage |
|---|---|
| `Structure` | members at their declared offsets — **absolute within the struct** |
| `A[T]` | 16 bytes: u64 offset (relative to the instance's data), u64 count |
| `IA[T]` | inline; the element count is the type's `elementLength` |
| `HashString` | 16 bytes: u64 string offset (relative to the data), u32 hash |
| primitives | `int8`, `int16`, `float` in this schema; signedness fixed by decoded values (−1 stays −1) |

Strings are **deduplicated by sharing an offset**: a part whose `damage_type` repeats the previous
part's points at the same pool text. That is why a naive byte walk sees "missing" strings, and it is
what made the extent guess ambiguous for Gibbed.

Because member offsets are declared rather than inferred, `jc3adf` needs no guess at all — that is
the whole fix.

## 3. Validation

| check | result |
|---|---|
| reader vs Gibbed, 4 flatbed modules (the only ones that convert) | **1,660 / 1,660 rows each, 0 mismatches**, inline-array element rows included (`jc3adf.py verify`) |
| donor part names vs `DeformPoints` | **42 / 42**, indices 0…41 |
| donor parts that carry lights vs `DeformPoints.light_indices` | **12 / 12** |
| donor parts with `behavior = Wheel` vs `DeformPoints.wheel_indices` | **4 / 4** |
| donor wheel slots (`wheel_parts[]`) | parts 11, 12, 26, 27 → slots 3, 2, 0, 1 |
| donor `door_parts[]` | parts 1, 2, 25 |
| children indices inside the part list | yes, all 42 |
| fleet build | **233 / 233 entities, 11,643 parts, 0 failures** |

One quirk worth keeping: the donor's `sportsmuscle_c_mirror` has damage type `Boat_Antenna`, which is
**not** in its own `VehicleDamage.part_damage_types[]` table (24 types, `Land_*`). The part therefore
falls back to `Default` damage — a shipped-file inconsistency, not a decoding error. It is reported by
`jc3parts.py check` rather than hidden.

## 4. What the fleet table says

`PARTS_TABLE.jsonl` — one JSON object per entity: `parts[]` (index, name, damage type, behavior,
model path, parent, world collision body/raycast ids, `has_lights`, `is_deformable`, children),
plus `wheels[]` (part, slot, spokes, spins) and `doors[]`.

| item | value |
|---|---|
| entities | **233** |
| parts | **11,643** (3 … 119 per entity, median **48**) |
| damage types used fleet-wide | **71** |
| most common types | `Land_Generic` 2,336 · `Land_Light` 1,421 · `Land_Window` 815 · `Land_Wheel` 593 · `Boat_Generic` 542 · `Train_Generic` 371 · `Land_Door` 369 |

The donor's 42-row table (name, damage type, behavior, collision body, light flag, children) is in
[PARTS_TABLE.md](PARTS_TABLE.md).

## 5. What this unblocks

* **T-P2** (per-part damage): part → damage type is now decoded fleet-wide, and the health values per
  type were already in `VehicleDamage.part_damage_types[]` (decoded by Gibbed; 4,820 rows). The row
  group is no longer blocked.
* **T-PA3 / T-CO3**: `world_collision_body_id`, `raycast_body_id` and the instance ids are decoded per
  part, so the part → Havok body map exists.
* **PRT-3 / T-PA4**: `wheel_parts[]` (slot, spokes, spins) and `door_parts[]` are decoded.
* **PRT-2**: the part list with each part's `model` path is exactly the split the body mesh needs.

## 6. Scope and limits

`jc3adf` is a general ADF v4 reader but has only been exercised on this schema family: the parts
modules use `Structure`, `Array`, `InlineArray`, `HashString` and the `int8`/`int16`/`float`
primitives, and all 233 decode. The effect/camera/trim family (G2-9) later added the type kinds these
modules never use — pointer, `String`, `StringHash`, inline primitive arrays — so the reader is now
general rather than parts-specific.
