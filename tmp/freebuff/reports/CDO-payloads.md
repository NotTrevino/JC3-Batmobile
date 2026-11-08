# DONE — R-6: the six CDO component payloads past the 512 MiB budget

**STATUS: done.** The six children of `Default__RVehicleBatmobile` that
`grab_packages_g305.PartialPackage.data()` refused are decoded. They were never large: the
declared lengths are **67 B** (two `StaticMeshComponent`s) and **14 B** (four
`SVehicleWheel`s), and no length exceeds the 434,869,146 B package. What crossed 512 MiB was
their *offset* — 0x26795f7d..0x26796738 — inside an image that decompresses to
**869,335,540 B** (2.00x the chunk-compressed file). So the budget was a guard on image
position, not evidence of a misparse.

Decoded: **4 tags, 54 bytes left over, 0 UNKNOWN tags.** The two collision meshes carry
`ReplacementPrimitive = null` and `PerInstanceRandom`; the four wheels carry no serialised
tags at all.

## Files written

| file | what |
|---|---|
| `Tools/scripts/grab_cdo_payloads.py` | new script, `--write` / `--check`; reads `Startup.upk` with `upk_read`, names tags from BmSDK-AK |
| `Research/BatmobileGrab/CDO_PAYLOADS.md` | generated note: misparse test, method, per-component tags, leftovers, UNKNOWNs |
| `tmp/freebuff/reports/CDO-payloads.md` | this report |

Read-only inputs: `Startup.upk` (opened for reading only), `E:/Modding/_shared/tools/BmSDK-AK`
(read only). No game process was started or attached to, nothing was installed or built, and
no existing Research/ or Tools/ file was modified.

## Result

| component | class | declared length | offset | end | length > file? | tags | leftover | UNKNOWN |
|---|---|---:|---|---:|---|---:|---:|---:|
| `BatmanCollisionMeshBattleMode0` | `StaticMeshComponent` | 67 B | 0x26795f7d | 0x26795fc0 | no | 2 | 23 B | 0 |
| `BatmanCollisionMeshPursuitMode0` | `StaticMeshComponent` | 67 B | 0x26795fc0 | 0x26796003 | no | 2 | 23 B | 0 |
| `WheelFL` | `SVehicleWheel` | 14 B | 0x26796700 | 0x2679670e | no | 0 | 2 B | 0 |
| `WheelFR` | `SVehicleWheel` | 14 B | 0x2679670e | 0x2679671c | no | 0 | 2 B | 0 |
| `WheelRL` | `SVehicleWheel` | 14 B | 0x2679671c | 0x2679672a | no | 0 | 2 B | 0 |
| `WheelRR` | `SVehicleWheel` | 14 B | 0x2679672a | 0x26796738 | no | 0 | 2 B | 0 |

Tags, named against BmSDK-AK (both collision meshes, identical layout):

| # | type | offset | member | SDK class | value |
|---|---|---|---|---|---|
| 1 | ObjectProperty | 0x13c | `ReplacementPrimitive` | `PrimitiveComponent` | 0 (null ref) |
| 2 | FloatProperty | 0x16c | `PerInstanceRandom` | `PrimitiveComponent` | 0.8541215062141418 (Battle) / 0.08001953363418579 (Pursuit) |

Decoding route: each payload begins with a 12-byte CDO prefix whose bytes 4..7 are the
export's own name-table index (5198 → `BatmanCollisionMeshBattleMode0`, 64311 → `WheelFL`,
…). That oracle resolves to the object's own name for all six, so `walk_tags` starts at byte
12 rather than byte 0 (the reason `wal`k at 0 returned 0 tags). The wheels then hit the
`00 00` end marker immediately — 12 prefix + 2 terminator, no tags. The meshes stop at byte
44 of 67; the remaining 23 bytes are the end marker plus 21 zero bytes of padding.

Left over, exactly: 2 B per wheel (`00 00`), 23 B per collision mesh (all zeros). Zero bytes
are unaccounted for, so nothing was skipped between tags.

SDK naming is read, not guessed: the generated C# stores each member's layout offset in its
accessor (`MarshalUtil.ToManaged<float>(Ptr + 364)`), so `grab_cdo_payloads.py` parses
`Generated/**/*.g.cs` into offset→member maps and resolves each tag against the class and its
ancestors, most derived first. 0x13c → 316 → `ReplacementPrimitive` (declared on
`PrimitiveComponent`, line 2102-2107 of `PrimitiveComponent.g.cs`), 0x16c → 364 →
`PerInstanceRandom` (lines 2183-2188). The package's own name for the object tag
(`ReplacementPrimitive`) agrees with the SDK member at that offset, an independent check that
the naming is right rather than merely plausible.

## Commands run and their output

### 1. Locate R-6 and the guard

```
$ grep -n "R-6|CDO|512 MiB" Research/RESET_STATUS.md
14:| **R-6** | **PARTIAL** | `G3-05`, `G3-06`, `G3-12`, `G3-12b` | decode the 925 untagged objects … |
239:## R-6 — PARTIAL
276:* The 97 class-default *values* (the CDO is readable; the name→offset pairing is not done).
277:* The 6 CDO component payloads past the 512 MiB decode budget.

$ grep -n "DECODE_BUDGET" Tools/scripts/grab_packages_g305.py
123:DECODE_BUDGET = 512 * 1024 * 1024
… data(): if end > DECODE_BUDGET: raise UpkError("payload ends at %#x, past the %#x decode budget")
```

Decoded: the guard is on `offset + size`, not on `size`.

### 2. First size probe — and a wrong header parse, corrected

```
$ ls -l "…/CookedPCConsole/Startup.upk"
-rw-r--r-- 1 User 197121 434869146 Jul 15  2024 …/Startup.upk

$ python - (naive header read: group string then 6 ints)
file bytes 434869146 0x19eb939a
names 42467341 0x1074f exports 18185 0x2ab2a imports 3529468 0x1cfb
```

That parse is **wrong** — I skipped the u32 flags word between the group string and the table
counts, so 42,467,341 names is nonsense. Re-reading with `upk_read.Package` (which does read
the flags) gives the real tables below. Recorded here because a wrong intermediate parse is
exactly the failure mode the task asked me to test for.

```
$ python - (upk_read.Package on Startup.upk)
file bytes 434869146 image bytes 869335540
names 67407 0x4709 exports 174890 0x35dafc imports 7419 0x32af88
export 7530: Default__RVehicleBatmobile size 978 offset 0x10cbd1f class RVehicleBatmobile
children: 37
  171103 BatmanCollisionMeshBattleMode0   StaticMeshComponent size=67 off=0x26795f7d end=0x26795fc0 PAST-FILE
  171104 BatmanCollisionMeshPursuitMode0  StaticMeshComponent size=67 off=0x26795fc0 end=0x26796003 PAST-FILE
  171139 WheelFL                          SVehicleWheel       size=14 off=0x26796700 end=0x2679670e PAST-FILE
  171140 WheelFR                          SVehicleWheel       size=14 off=0x2679670e end=0x2679671c PAST-FILE
  171141 WheelRL                          SVehicleWheel       size=14 off=0x2679671c end=0x2679672a PAST-FILE
  171142 WheelRR                          SVehicleWheel       size=14 off=0x2679672a end=0x26796738 PAST-FILE
  … (31 more children, all ends below 512 MiB)
```

Decoded: exactly **six** of the 37 children have `end > 0x20000000`; those are the six R-6
names. "PAST-FILE" is expected for a compressed package (the on-disk file is 435 MB, the
image 869 MB) — it is not evidence of misparse, and no `size` is anywhere near the file size.

### 3. Tag start: the 12-byte prefix oracle

```
$ python - (walk from 0 and from 12)
171103 BatmanCollisionMeshBattleMode0 bytes[4:8]= 5198 name[ni]= BatmanCollisionMeshBattleMode0
  walk@12: 2 tags end 44 / 67 stop end leftover 23
    ObjectProperty 0x13c ReplacementPrimitive 4 0
    FloatProperty 0x16c None None 0.8541215062141418
171139 WheelFL bytes[4:8]= 64311 name[ni]= WheelFL
  walk@12: 0 tags end 12 / 14 stop eof leftover 2
```

Decoded: at byte 0 the walk returns 0 tags (`00 00…` reads as end); at byte 12 it decodes 2
tags for the mesh. The prefix's name index equals the export's own name index, which is what
makes byte 12 the tag start rather than an assumption.

### 4. SDK: where the offset→member map lives

```
$ grep -rn "ReplacementPrimitive" src --include=*.cs
src/BmSDK/Generated/Engine/PrimitiveComponent.g.cs:2102:    /// ComponentProperty: ReplacementPrimitive
src/BmSDK/Generated/Engine/PrimitiveComponent.g.cs:2104:    public unsafe BmSDK.Engine.PrimitiveComponent ReplacementPrimitive

$ sed -n '2100,2112p' …/PrimitiveComponent.g.cs
        get { return …ToManaged<BmSDK.Engine.PrimitiveComponent>(Ptr + 316); }
        set { …ToUnmanaged(value, Ptr + 316); }

$ grep -n -B 4 "Ptr + 364" …/PrimitiveComponent.g.cs
2183:    /// FloatProperty: PerInstanceRandom
2187:        get { …ToManaged<float>(Ptr + 364); }
```

Decoded: 0x13c = 316, 0x16c = 364. `api-reference.json` carries comments only (no offsets),
so the generated accessors are the offset source; 5,468 `.g.cs` files scan in the script run.

### 5. `--write` and `--check` (final)

```
$ uv run python Tools/scripts/grab_cdo_payloads.py --write
wrote Research\BatmobileGrab\CDO_PAYLOADS.md
counts: {"children": 37, "past_budget": 6, "under_budget": 31, "tags": 4, "unknown_tags": 0, "leftover_bytes": 54, "misparse": 0, "end_past_image": 0}
checks: {"file_below_budget": true, "no_declared_length_above_file": true, "no_end_past_image": true, "prefix_oracle_holds": true}
WRITE_EXIT=0

$ uv run python Tools/scripts/grab_cdo_payloads.py --check
OK 6/6 payloads decoded, 4 tags, 0 UNKNOWN
counts: {"children": 37, "past_budget": 6, "under_budget": 31, "tags": 4, "unknown_tags": 0, "leftover_bytes": 54, "misparse": 0, "end_past_image": 0}
CHECK_EXIT=0
```

`--check` re-derives the whole note from the bytes and compares the rendered markdown line for
line, and re-asserts: 6 past-budget payloads, no declared length above the file, no end past
the image, the prefix oracle on all six, walks that never overrun, and zero UNKNOWN tags.

## Value labels

- **decoded**: the file size 434,869,146 B; image size 869,335,540 B; export table counts
  (67,407 names / 174,890 exports / 7,419 imports); CDO export 7530 at 0x10cbd1f, 978 B, 37
  children; each child's size/offset/end; each prefix's name index; each tag's type, layout
  offset, value and stop position; each leftover hex run; SDK member names and their
  `Ptr + N` offsets (file + line quoted above).
- **derived**: the "past budget" classification (`offset + size > 536,870,912`); the counts
  4 tags / 54 leftover bytes / 0 UNKNOWN; the 2.00x image:file ratio; the statement that the
  budget was image position rather than object size.
- **UNKNOWN**: below.

## UNKNOWNs

1. **Runtime meaning.** Whether the engine reads these six values at all is not testable
   read-only; every claim is file-to-file and no process was attached (project rule).
2. **Why `PerInstanceRandom` is 0.854 / 0.080 on the two collision meshes.** The SDK names
   the offset; the bytes give the values; the purpose is not established by this file. Next
   source would be a runtime probe or the native `StaticMeshComponent` initialiser.
3. **The remaining 31 CDO children** are under the budget and were already walked by
   `REMAINDER.md`/`CLASS_DEFAULTS.md`; this note does not re-derive them, it only empties the
   six-payload UNKNOWN.
4. **The `SVehicleWheel` defaults themselves.** The four wheel components serialise no tags,
   so their values are whatever the native class default object holds — in `Engine.upk`, not
   in these 14 bytes. Reading them is a separate walk (same method, different export).
