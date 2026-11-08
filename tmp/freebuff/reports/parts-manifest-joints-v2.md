# Parts manifest v2 - P-01/P-02 joint members, and the module that carries them

Offline only: no install, no game, no writes into `Builds/bm-RC2`.

## Deliverables

| file | what |
|---|---|
| `Working/Parts/bm_vehicle_parts_v2.json` | copy of `bm_vehicle_parts.json`; only the two joint records gained members |
| `Tools/scripts/bm_parts_v2.py` | copy of `bm_parts.py` (original untouched); builds/checks the jointed module |
| `Builds/bm-RC3-parts/` | new private tree: copy of `Builds/bm-RC2/aaf` with the patched parts module |
| `Builds/bm-RC3-parts/receipt.json` | shas, byte offsets, row evidence, physicsc state |

## 1. Manifest delta

19 records in both files; a recursive compare shows `parts[]` as the only top-level member that
differs. Exactly two records were touched, and only by **adding** keys - no existing value changed:

| record | keys added (JOINT_FIELDS.md §4) |
|---|---|
| `batmobile_turret` (P-01, part 50) | `constraint_index` 11, `constraint_class` `hkpLimitedHingeConstraintData`, `constraint_axis` `[-0.0, 1.0, -0.0]`, `constraint_pivot_m` `[1.3e-05, 0.876249, 0.333226]`, `constraint_min_rad` -1.047198, `constraint_max_rad` 1.047198, `constraint_min_deg` -60.0, `constraint_max_deg` 60.0, `constraint_frame` `vehicle`, `constraint_source` |
| `batmobile_cannon` (P-02, part 51) | `constraint_index` 12, same class/frame, `constraint_axis` `[1.0, 0.0, 0.0]`, `constraint_pivot_m` `[0.000358, 1.702446, 0.017586]`, `constraint_min_rad` -0.087266, `constraint_max_rad` 0.349066, `constraint_min_deg` -5.0, `constraint_max_deg` 20.0, `constraint_source` |

`constraint_pivot_m` is the part's own `pivot_m`, not its `parent_space_offset` (JOINT_FIELDS §3:
P-02's pivot is P-01's pivot plus P-02's pso; the pso stays the parent-relative placement).
Values and provenance are copied from `JOINT_FIELDS.md` §3; the 11/12 numbers are the append
positions into the 11-object constraint list.

## 2. What the generator writes

`bm_parts_v2.py` is a byte copy of `bm_parts.py` with four edits plus a new entry point:

* docstring/name `bm_parts_v2.py`;
* `BASE_TAG = "bm-RC2"`, `TAG = "bm-RC3-parts"`;
* `SPEC` -> `Working/Parts/bm_vehicle_parts_v2.json`;
* the legacy `write_module` flag tuple now reads `p.get("constraint_index", -1)` instead of the
  literal `-1` (the only place the original hardcoded it, line 645).

The active `--write` path does not rebuild from `bm-001`. It copies `Builds/bm-RC2/aaf` into
`Builds/bm-RC3-parts/aaf` and rewrites **only** the `constraint_index` member of rows 50 and 51,
taking the value from the manifest. It refuses to run unless the old value is `-1` and the
manifest `part_index` matches the decoded row, then re-decodes the result before writing the
receipt. That is what makes "every other part row byte-identical" a property of the build, not a
claim about it.

## 3. Read-back

Module:
`Builds/bm-RC3-parts/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/batmobile/sportsmuscle_vehicle_parts.vmodc`

`jc3adf.py info`: 46300 B, 33 types, 119 names, `VehicleParts` at 0x50; `Part` is 304 bytes with
39 members.

`jc3adf.py dump <module> --paths` (one line per part) finds both rows:

```
 50  batmobile_turret                   Land_Generic           Turret               kids=3 body=-1 lights=0
 51  batmobile_cannon                   Land_Generic           Cannon               kids=0 body=-1 lights=0
```

`jc3adf.py dump <module>` (path/value mode) shows the changed members themselves:

```
parts[50].constraint_index    int16  11
parts[51].constraint_index    int16  12
```

**Measured correction to the page:** `constraint_index` is stored as **int16** (2 bytes,
`+0x3d7c` / `+0x3eac` in this file), not int32 as JOINT_FIELDS §1 says. `-1` therefore reads as
`0xFFFF` in the raw bytes; the reader decodes it as `-1`. Both indices fit int16.

Joint rows after the build:

| row | part | part_index | `constraint_index` (bm-RC2 -> bm-RC3-parts) | axis | pivot (m, vehicle frame) | limits (deg) | limits (rad) |
|---|---|---|---|---|---|---|---|
| 50 | `batmobile_turret` | 50 | -1 -> **11** | (-0.0, 1.0, -0.0) | (0.000013, 0.876249, 0.333226) | -60.0 .. 60.0 | -1.047198 .. 1.047198 |
| 51 | `batmobile_cannon` | 51 | -1 -> **12** | (1.0, 0.0, 0.0) | (0.000358, 1.702446, 0.017586) | -5.0 .. 20.0 | -0.087266 .. 0.349066 |

The limits live in the manifest row; the module carries only the index. `bm_parts_v2.py --check`
re-verifies the manifest round-trip (unit axis, pivot == `pivot_m`, rad == deg*pi/180 within
1e-5, class/frame strings).

## 4. Every other part row

Independent comparison of the two files (not through the generator):

* 61 parts in both, 46300 bytes in both;
* **59 / 61 part rows byte-identical**;
* the only differing rows are `[50] batmobile_turret` (-1 -> 11) and `[51] batmobile_cannon`
  (-1 -> 12);
* exactly **4 bytes** differ in the whole file: `0x3d7c`, `0x3d7d`, `0x3eac`, `0x3ead` - the two
  2-byte `constraint_index` fields, nothing else.

`bm_parts_v2.py --check`:

```
ok: 61 parts; 2 joint rows hold their manifest indices; 59/59 other part rows byte-identical to bm-RC2; 4 byte(s) changed inside the two constraint_index fields
```

## 5. `jc3parts.py check`

```
ok: 40 part indices agree between .epe and DeformPoints; 4 wheel points -> 4 wheel parts; 21 light points -> 12 parts
ok: donor table has 42 parts, names 42/42 with DeformPoints, lights 12 parts match, wheels 4 match, damage types 17 used
  note: ['Boat_Antenna'] not in this vehicle's VehicleDamage table (24 types) - the part falls back to Default damage
```

That command checks the donor table against the `.epe`/`DeformPoints`, not the built module
(`jc3parts.py` has no build argument; its `--raw` points at the game grab). It passes, and it is
unaffected by this build.

## 6. Limits and honest caveats

* **The `constraint_index` now names an object that does not exist yet.** The physicsc in
  `Builds/bm-RC3-parts` is copied unchanged from bm-RC2 (shas in `receipt.json`). JOINT_FIELDS §4
  counts 11 constraint objects in that file, so 11 and 12 are the positions two appended
  `hkpLimitedHingeConstraintData` objects would occupy. Until those objects are appended, the
  index is a forward reference - it is correct only together with the append, which this task
  did not ask for and this generator does not do. `-1` was "no joint"; 11/12 is "this joint,
  once the object exists".
* The frame of axis/pivot is the donor's stored `vehicle` frame, unproven body-local
  (JOINT_FIELDS §6 Q-1).
* Turn rate is code-side; a limited hinge has no rate field.
* `.physicsc` object count is cited from the page; no reader in the repo decodes it here, so the
  count was not re-measured by this work.
* The v2 tree is private and offline: no `.ee` repack, no install, no game start.

## 7. Commands

```
python Tools/scripts/bm_parts_v2.py --write
python Tools/scripts/bm_parts_v2.py --check
python Tools/scripts/jc3adf.py info  Builds/bm-RC3-parts/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/batmobile/sportsmuscle_vehicle_parts.vmodc
python Tools/scripts/jc3adf.py dump  Builds/bm-RC3-parts/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/batmobile/sportsmuscle_vehicle_parts.vmodc --paths
python Tools/scripts/jc3parts.py check
```
