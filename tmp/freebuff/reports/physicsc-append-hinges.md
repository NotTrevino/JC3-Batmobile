**STATUS: DONE — `Working/Collision/batmobile_hinged.physicsc` has 13 constraint objects; the appended `hkpLimitedHingeConstraintData` objects are at indices 11 (P-01 turret) and 12 (P-02 cannon) with the Batmobile axis, pivot and limits; `jc3hkx.py check` passes on the file.**

# Appending the two Batmobile hinges to a copy of the physicsc

## Why

`Builds/bm-RC3-parts` writes `constraint_index` 11 for P-01 (`batmobile_turret`) and 12 for P-02 (`batmobile_cannon`), but `Working/Collision/batmobile.physicsc` holds **11** constraint objects (indices 0..10: 9 limited hinges + 2 ragdolls). Indices 11 and 12 name nothing. `Working/Parts/JOINT_FIELDS.md` §3 states the fields those objects need; this pass creates them on a copy.

## Files written

| file | what |
|---|---|
| `Working/Collision/batmobile_hinged.physicsc` | **new** 340,992 B copy (source 340,368 B, untouched) |
| `Tools/scripts/bm_physicsc_hinges.py` | writer + verifier, `--write` / `--check` |
| `tmp/freebuff/reports/physicsc-append-hinges.md` | this report |

Nothing was written to `Working/Collision/batmobile.physicsc`, to any `Builds/` tree, or to any parts module.

## Method

1. **Donor.** `editor/entities/jc_vehicles/01_land/v0201_car_capstone_mediumtank/v0201_car_capstone_mediumtank_debug.ee` → `models/.../mediumtank.physicsc` (206,976 B) extracted with `jc3hkx.physicsc_of`. Its three constraints in offset order are 0 = cannon, 1 = hatch, 2 = turret (`JOINT_FIELDS.md` §1); hinges 2 and 0 were copied as 304-byte blobs.
2. **Pointer-free guard.** The script aborts if any local or global fixup `from` lands inside a donor hinge blob, because a copied blob's internal offsets belong to the donor file. The donor has none, so the copy is byte-safe. (`hlpLimitedHingeConstraintData` carries its atoms inline.)
3. **Field patch** — only these four slots; the rest of each donor blob is copied verbatim:
   | part | +0x30 axis | +0x60 pivot (m) | +0xFC min (rad) | +0x100 max (rad) |
   |---|---|---|---|---|
   | P-01 `batmobile_turret` | (0, 1, 0) | (0.000013, 0.876249, 0.333226) | -1.047198 | 1.047198 |
   | P-02 `batmobile_cannon` | (1, 0, 0) | (0.000358, 1.702446, 0.017586) | -0.087266 | 0.349066 |

   These are `JOINT_FIELDS.md` §3: P-01 axis +Y yaw ±60°, P-02 axis +X pitch -5..+20°, pivots in vehicle space (P-02's pivot = P-01's pivot + its parent-space offset).
4. **Re-layout.** All 430 objects are laid out in order, the two 304-byte (16-aligned) hinges appended at data offset 322,288, then local / global / virtual fixups remapped and the `__data__` record rewritten. The virtual table grows by two 12-byte entries (class name offset 463 = `hkpLimitedHingeConstraintData`); pointer slots stay zero, as the file ships them. This is `packfile_bytes`'s mechanism (`Research/JC3Grab/PHYSICS_WRITE.md` §4, the 16-byte insert that moved all 430 objects) extended from a resized object to *new* objects.

## Verbatim commands and output

```
python Tools/scripts/bm_physicsc_hinges.py --write
wrote Working\Collision\batmobile_hinged.physicsc: 340,368 -> 340,992 B, objects 430 -> 432, constraints 11 -> 13
  index 11 P-01 batmobile_turret   axis [0.0, 1.0, 0.0] pivot [1.3e-05, 0.876249, 0.333226] limits -1.047198 .. 1.047198
  index 12 P-02 batmobile_cannon   axis [1.0, 0.0, 0.0] pivot [0.000358, 1.702446, 0.017586] limits -0.087266 .. 0.349066
ok: appended objects re-read clean
```

```
python Tools/scripts/jc3hkx.py check --entity __no_entity__ --file Working/Collision/batmobile_hinged.physicsc
file E:/Modding/JC3-Batmobile/Working/Collision/batmobile_hinged.physicsc: 340,992 B, 432 objects, 54 hulls (convex 54), 18 mesh shapes, 22 compounds (112 instances, 22 AABB unions exact), station sets 0, sha256 6eef93c6b2f747e6...
entities 0 | files 0 | objects 0 | hulls 0 (convex 0) | mesh shapes 0 | geometries 0 | compounds 0 (0 instances, 0 with a part index, 0 AABB unions exact) | station sets 0 (land_global agree 0, disagree 0)
check ok
```

```
python Tools/scripts/bm_physicsc_hinges.py --check
... (same check --file line, then)
  index 11 P-01 batmobile_turret   axis [0.0, 1.0, 0.0] pivot [1.3e-05, 0.876249, 0.333226] limits -1.047198 .. 1.047198
  index 12 P-02 batmobile_cannon   axis [1.0, 0.0, 0.0] pivot [0.000358, 1.702446, 0.017586] limits -0.087266 .. 0.349066
objects 432, constraint objects 13, original constraints identical True, hknpPhysicsSystemData identical True
ok: copy matches, 13 constraints, new objects at 11 and 12
```

`--entity __no_entity__` only skips the archive sweep (the `entities 0 | files 0` line); the written file is checked by `--file`.

## What the re-read proves

- **13 constraint objects**; indices 11 and 12 are `hkpLimitedHingeConstraintData`, 304 B each, at offsets after the original 11, matching the `constraint_index` values the parts module carries.
- Axis / pivot / limits match `JOINT_FIELDS.md` §3 to < 1e-5 (m / rad).
- The 11 original constraint objects are **byte-identical** to the source file; `hknpPhysicsSystemData` (body entries / wheel stations) is byte-identical.
- `check_file`'s ladder: magic/version/sections, empty `__types__`, no table residue, every fixup in bounds, 54/54 hulls convex, 112 instances, 22 AABB unions exact — 0 violations.
- `--check` rebuilds the blob in memory and requires the on-disk copy to match byte for byte, so the write is reproducible.

## UNKNOWNs

- **Runtime acceptance.** Every check is the reader's. Whether Havok/the game accepts two appended constraints, and honours `constraint_index` 11/12 at spawn, is a phase-Q question and is **not** claimed.
- **Pivot/axis frame.** Copied from the donor convention (vehicle space per `JOINT_FIELDS.md` §6); the body-local reading is unproven.
- **The parts side is not changed here.** This produces the physics file the indices will name; no parts or Builds file was touched.

## Revert

Delete `Working/Collision/batmobile_hinged.physicsc`, `Tools/scripts/bm_physicsc_hinges.py` and this report. The source physicsc and every Builds tree were opened read-only.
