**STATUS: DONE — the copy `Working/Collision/batmobile_hinged.physicsc` has 13 constraint objects; the two appended `hkpLimitedHingeConstraintData` objects sit at indices 11 and 12 with the Batmobile axis, pivot and limits, and `jc3hkx.py check` passes on the file.**

# Batmobile hinges appended to a copy of the physicsc

## What was wrong

`Builds/bm-RC3-parts` writes `constraint_index` 11 for P-01 (`batmobile_turret`) and 12 for P-02 (`batmobile_cannon`), but `Working/Collision/batmobile.physicsc` holds **11** constraint objects (indices 0..10: 9 limited hinges + 2 ragdolls). Indices 11 and 12 therefore name nothing. `Working/Parts/JOINT_FIELDS.md` §3 predicted exactly this and put the values on the parts side; this pass puts the objects on the physics side.

## Files written

| file | what |
|---|---|
| `Working/Collision/batmobile_hinged.physicsc` | **new** 340,992 B copy (original 340,368 B, untouched) |
| `Tools/scripts/bm_physicsc_hinges.py` | writer + verifier, `--write` / `--check` |
| `tmp/freebuff/reports/physicsc-hinges.md` | this report |

Nothing was written to `Working/Collision/batmobile.physicsc`, to `Builds/`, or to any parts module.

## Method

1. **Donor.** `editor/entities/jc_vehicles/01_land/v0201_car_capstone_mediumtank/v0201_car_capstone_mediumtank_debug.ee` → `models/.../mediumtank.physicsc` (206,976 B) via `jc3hkx.physicsc_of`. Its three constraints in offset order are 0 = cannon, 1 = hatch, 2 = turret (`JOINT_FIELDS.md` §1). Hinges 2 and 0 were copied as 304-byte blobs.
2. **Pointer-free guard.** The script aborts if any local or global fixup `from` lands inside a donor hinge blob, because a copied blob's internal offsets belong to the donor file. The donor passes (0 such fixups), so the copy is byte-safe.
3. **Field patch** (only these four slots; everything else copied):
   | part | +0x30 axis | +0x60 pivot (m) | +0xFC min (rad) | +0x100 max (rad) |
   |---|---|---|---|---|
   | P-01 `batmobile_turret` | (0, 1, 0) | (0.000013, 0.876249, 0.333226) | -1.047198 | 1.047198 |
   | P-02 `batmobile_cannon` | (1, 0, 0) | (0.000358, 1.702446, 0.017586) | -0.087266 | 0.349066 |
4. **Re-layout.** All 430 objects are copied in order, the two 304-byte (16-aligned) hinges appended at data offset 322,288, then local / global / virtual fixups remapped and the `__data__` record rewritten. The virtual table grows by two 12-byte entries (class offset 463, `hkpLimitedHingeConstraintData`); pointer slots stay zero, as the file ships them. This is `packfile_bytes`'s mechanism (`Research/JC3Grab/PHYSICS_WRITE.md` §4) extended from a resized object to new objects.

## Observed output

```
wrote Working\Collision\batmobile_hinged.physicsc: 340,368 -> 340,992 B, objects 430 -> 432, constraints 11 -> 13
  index 11 P-01 batmobile_turret   axis [0.0, 1.0, 0.0] pivot [1.3e-05, 0.876249, 0.333226] limits -1.047198 .. 1.047198
  index 12 P-02 batmobile_cannon   axis [1.0, 0.0, 0.0] pivot [0.000358, 1.702446, 0.017586] limits -0.087266 .. 0.349066
ok: appended objects re-read clean
```

```
file E:/Modding/JustCause3/JC3-Batmobile/Working/Collision/batmobile_hinged.physicsc: 340,992 B, 432 objects, 54 hulls (convex 54), 18 mesh shapes, 22 compounds (112 instances, 22 AABB unions exact), station sets 0, sha256 6eef93c6b2f747e6...
entities 0 | files 0 | objects 0 | hulls 0 (convex 0) | mesh shapes 0 | geometries 0 | compounds 0 ...
check ok
  index 11 P-01 ... axis [0.0, 1.0, 0.0] pivot [1.3e-05, 0.876249, 0.333226] limits -1.047198 .. 1.047198
  index 12 P-02 ... axis [1.0, 0.0, 0.0] pivot [0.000358, 1.702446, 0.017586] limits -0.087266 .. 0.349066
objects 432, constraint objects 13, original constraints identical True, hknpPhysicsSystemData identical True
ok: copy matches, 13 constraints, new objects at 11 and 12
```

`jc3hkx.py check` was called with `--entity __no_entity__ --file ...` so the archive sweep is skipped and only the written file is checked; the `entities 0 | files 0` line is that filter, not a failure.

## Verified

- 13 constraint objects; index 11 and 12 are `hkpLimitedHingeConstraintData`, 304 B, at increasing offsets after the original 11.
- Axis / pivot / min / max match `JOINT_FIELDS.md` §3 to < 1e-5 rad / m; the 11 original constraint objects are **byte-identical** to the source file.
- `hknpPhysicsSystemData` (body entries, wheel stations) is byte-identical — the write did not touch vehicle physics.
- `shape_checks` through `check_file`: 54/54 hulls convex, 112 instances, 22 AABB unions exact, 0 violations; `__types__` still empty; no table residue or classname-marker damage.
- Copy is reproducible: `--check` rewrites the blob in memory and requires the on-disk copy to match byte for byte.

## UNKNOWNs

- **Runtime acceptance.** Every check is the reader's; whether Havok/the game accepts two appended constraints, and whether the loader honours `constraint_index` 11/12 at spawn, is a phase-Q question and is **not** claimed.
- **Pivot/axis frame.** Copied unchanged from the donor convention (vehicle space, per `JOINT_FIELDS.md` §6); the body-local reading is still unproven.
- **The parts side is unchanged.** `Builds/bm-RC3-parts` still carries the `-1`-era module unless a later step writes the joints; this pass only produces the physics file those indices will name.

## Revert

Delete `Working/Collision/batmobile_hinged.physicsc`, `Tools/scripts/bm_physicsc_hinges.py` and this report. The source physicsc and every Builds tree were opened read-only.
