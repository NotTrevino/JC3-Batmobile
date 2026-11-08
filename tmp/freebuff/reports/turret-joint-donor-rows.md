# DONE - turret/cannon joint fields from the donor rows

Task: learn what a correct joint looks like in the donor parts module (medium tank plus one
other hinged vehicle), describe field-by-field what B-04's `bm_vehicle_parts.json` would need
for P-01 (yaw 120°) and P-02 (pitch 25°), and do not edit the manifest or the generator.

## Artifacts

- `Working/Parts/JOINT_FIELDS.md` - field-by-field description (generated page).
- `Tools/scripts/joint_fields.py` - `--write` / `--check`; `--check` re-decodes the donor
  modules and `TURRET.json` and compares the page byte for byte.
- This report.

**No edits** to `Working/Parts/bm_vehicle_parts.json` or `Tools/scripts/bm_parts.py`.
`joint_fields.py` only opens them for reading. Manifest sha256 seen by the check:
`d5df53458a8759a57fc0a827798acaa88f343601e86d757115e380c696462222`.

## Findings

1. **One joint member.** The parts module has no joint object. The only link is
   `parts[i].constraint_index`, a signed int32 indexing the ordered list of constraint
   objects in the vehicle's `.physicsc`. `hinged_parts[]` stores only a part index
   (`MOVING_PARTS.md` §3) and `aim_part_constraints[]` is the suspension linkage
   (`TURRET.md` §4), not a turret joint.

2. **Donor rows decoded** (medium tank `mediumtank_vehicle_parts.vmodc`, sha256
   `50072282...4310`; APC `apc_vehicle_parts.vmodc`, sha256 `610dbc17...f456`):

   | vehicle | part | i | behaviour | parent | constraint_index | axis | pivot (m) | min..max |
   |---|---|---|---|---|---|---|---|---|
   | medium tank | `mediumtank_turret` | 26 | Turret | 0 | **2** | +Y | (0, 2.2812, 1.1382) | -179..179° |
   | medium tank | `mediumtank_cannon` | 38 | Cannon | 26 | **0** | +X | (0, 2.5347, 0) | -5..20° |
   | APC | `apc_turret_base` | 30 | Turret | 0 | **15** | +Y | (-0.0037, 2.1367, 1.3048) | -179..179° |
   | APC | `apc_weapon_mount_vertical` | 44 | Cannon | 30 | **14** | +X | (0, 2.7313, 0.5942) | -15..50° |

   Each index resolves to a 304-byte `hkpLimitedHingeConstraintData`: axis at `+0x30`
   (float4), pivot at `+0x60` (float4), min angle at `+0xFC` and max at `+0x100`, both
   **radians** (`jc3turret.py` lines 117-119; `TURRET.md` §6 "Limits"). The index is the
   constraint object's position in file-offset order, not a body id: medium tank order is
   cannon 0, hatch 1, turret 2; APC order gives weapon mount 14, turret base 15.

3. **B-04 target fields.** P-01 (`batmobile_turret`, part 50, parent `sportsmuscle_body`):
   axis `[-0.0, 1.0, -0.0]` (+Y), pivot `(0.000013, 0.876249, 0.333226)` m,
   min/max `-60..60°` = `-1.047198..1.047198 rad` (span 120°). P-02
   (`batmobile_cannon`, part 51, parent `batmobile_turret`): axis `[1.0, 0.0, 0.0]` (+X),
   pivot `(0.000358, 1.702446, 0.017586)` m, min/max `-5..20°` =
   `-0.087266..0.349066 rad` (span 25°; the row's own `joint` is null, the range is its
   carrier hinge, quoted in `Builds/bm-RC2/verify/joint_trace.md` and `turret_ranges.md`).

4. **Minimum manifest change:** add integer `constraint_index` per Turret/Cannon part. To
   make it resolvable, the generator must also create the two `hkpLimitedHingeConstraintData`
   objects and assign the indices from the final object order. On the built `bm-RC2`
   physicsc there are 11 constraint objects (9 limited hinges + 2 ragdolls), so appending
   the two Batmobile hinges would place them at **11** (P-01) and **12** (P-02). The
   manifest page also proposes `constraint_class`, `constraint_axis`,
   `constraint_pivot_m`, `constraint_min_rad`, `constraint_max_rad`, `constraint_min_deg`,
   `constraint_max_deg`, `constraint_frame` and `constraint_source`, with values in
   `JOINT_FIELDS.md` §4.

5. **Frame correction found while checking.** `pivot_m` is vehicle-space, not
   parent-relative: P-02's `pivot_m` equals P-01's `pivot_m` plus P-02's
   `parent_space_offset` (0.876249 + 0.826197 = 1.702446), and P-02's
   `parent_frame_origin_m` is P-01's pivot. Therefore `constraint_pivot_m` must take the
   part's `pivot_m`; the pso stays the parent-relative placement and must not be copied into
   the constraint. The page states this.

## Verification

```
python Tools/scripts/joint_fields.py --write   # wrote Working/Parts/JOINT_FIELDS.md
python Tools/scripts/joint_fields.py --check
PASS: donor indices tank 2/0, APC 15/14; P-01 -60.0..60.0 deg = -1.047198..1.047198 rad;
P-02 -5.0..20.0 deg = -0.087266..0.349066 rad; manifest joint key False; next index 11
CHECK_EXIT=0
```

The check asserts the four donor indices, both BmAK spans, the absence of a joint key in
the manifest, that `bm_parts.py` still writes the literal `-1`, and the pivot relation; it
also requires the page to match the re-derived bytes.

## UNKNOWNs (unchanged from the research record)

- Hinge transform frame: body-A-local vs vehicle space is not proven; the donor numbers
  agree with vehicle space, so a port should copy that convention and verify it in-game
  (`TURRET.md` §6).
- Turn rate/acceleration are code-side, not hinge fields.
- Whether a `Turret`/`Cannon` part with `constraint_index = -1` still receives a runtime
  joint is not answered by any decoded engine code in the repo.
