# Review - G3-10f (PHYSICS_ROLES5.md: raycast ids and static compounds)

**VERDICT: minor issues.** Both structural claims reproduce on the three files I recomputed
(52/52, 90/90, 64/64 ray ids land on the entry that carries that part's index; the two
compounds I followed resolve to the part bodies the card names, with matching offsets), and
the card's own `--check` passes. The issues are methodological: the fleet "id space" oracles
(`ray_in_table`, `ray_selects_a_shape`) cannot fail on this data, the headline is stronger
than they support, and two sentences about compounds are true for the donor but not
fleet-wide. Nothing I re-read is a wrong value; one inference is an overclaim of exactly the
kind that broke G3-10d's "partner = body 0".

Independent review. Read-only: no `Research/`, `Tools/` or `_gamedata` file was modified; no
game process was run. My recompute is
`tmp/freebuff/scratch/roles5_review.py` (+ inline sweeps quoted below), print-only.

Labels: **decoded** = a byte offset or a field read from the file; **derived** = a stated rule
over decoded values; **UNKNOWN** = not decodable here, blocker named.

## 1. The three files I recomputed

The card's donor is `sportsmuscle.physicsc` (62 body entries, 42 parts). I picked three other
vehicles that have both a parts row and a raw `.physicsc`, decoded each independently
(`jc3hkx.Packfile`, body array at `hknpPhysicsSystemData+0x40`, 96-byte entries, shape pointer
at entry+0x00, part index via `CPfxPartIndexProperty+0x10`):

| file | bytes | objects | body entries | parts | parts with a ray | ray in bounds | entry has a shape | entry.part_index == part index |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `racinghothatch.physicsc` | 708,848 | 614 | 85 | 56 | 52 | 52/52 | 52/52 | **52/52** |
| `modernbus.physicsc` | 479,296 | 900 | 118 | 90 | 90 | 90/90 | 90/90 | **90/90** |
| `oldjeep.physicsc` | 678,576 | 794 | 106 | 71 | 64 | 64/64 | 64/64 | **64/64** |

- decoded: duplicate ray ids in these three files: **none** (each ray id is used by at most one
  part), so the ray value identifies a body entry unambiguously here.
- decoded: the entry class distribution is not all extern mesh - e.g. `racinghothatch` has 42
  polytopes, 31 extern meshes, 10 static compounds, 2 dynamic compounds among its shaped
  entries; the card's donor-only "42..59 window = extern block" is not a fleet rule and the
  card does not claim it is.
- derived: on these three files the role the card assigns ("the entry carries this part's
  index") is **true for every ray id**, extending the donor's 42/42 to 206/206 parts over four
  files.

## 2. Claim (1): "one id space that indexes the body-entry array"

The card supports it with two fleet invariants, `ray_in_table` 6309/6309 and
`ray_selects_a_shape` 6309/6309, plus the donor's identity table. What those invariants can
actually fail on, measured on the same 40 raw files that have a parts row (2,057 parts, 1,949
ray ids):

| quantity | value | can it fail? |
|---|---:|---|
| ray ids inside `0..body_count-1` | 1949/1949 | no ray id is out of bounds (decoded) |
| every body entry has a non-null shape | **2936/2936** | no - every entry is shaped, so `ray_selects_a_shape` cannot fail |
| duplicate ray ids | 0 | ray ids do not collide |
| `entry.part_index == part index` | **1669/1949 = 0.8563** | this is the only discriminating test, and it fails in 15 of 40 files |
| card's own rate (121 entity decodes) | 5466/6696 = 0.8160 | same quantity, different denominator |

- **decoded**: a bounds test over small integers into a 57-130 entry table, plus "the entry has
  a shape" where *all* entries have a shape, is satisfied by any ray value in range. It does
  not distinguish "ray indexes the body-entry array" from "ray is a small integer that happens
  to be in range". `ray_in_table` and `ray_selects_a_shape` are therefore near-vacuous
  invariants; the card treats them as fleet proof of the id-space claim.
- **decoded**: the discriminating test fails on real files. Two examples, recomputed:

| file | part | ray | entry offset | entry class | entry.part_index | part named by that index |
|---|---:|---:|---:|---|---:|---|
| `bavariumtank.physicsc` | 0 `bavariumtank_body` | 46 | `0x3df0` | `hknpExternMeshShape` | 8 | `bavariumtank_skirt_l_1` |
| `armoredjeep.physicsc` | 0 `armoredjeep_body` | 71 | `0x6620` | `hknpExternMeshShape` | 3 | `armoredjeep_door_f_l` |

  `bavariumtank` is the strongest case: **0 of 38** rays land on an entry carrying that part's
  index; `armoredjeep` is 12 of 67. So on those files "the ray id indexes the body entry whose
  part index is that part" is false for most or all parts.
- The card does state this limit in §1 ("the property numbering is not the parts-module index
  for every vehicle ... the identity of a ray id's part is therefore proved by the part-index
  round trip for the donor ... and is not proved by it elsewhere"). The problem is the
  headline sentence, "**No second id space** ... It is the body table's order, not a separate
  space", which the two quoted invariants do not support: what is proven is that ray ids are
  in range, not that they index the entry carrying that part.

### The assumption that could fail like G3-10d's "partner = body 0"

G3-10d failed because a universal statement was backed by a comparison that could not
discriminate (body 0's hull is near every pivot because it is the largest hull), and the
discriminating comparison went the other way. The same shape of error here is:

> "every ray id selects a body entry, each with a shape, therefore the ray id indexes the body
> table" - where "selects a body entry, each with a shape" is true for **every** integer in
> range, because all 2,936 entries in my sweep carry a shape.

The discriminating test is the identity rate, and it is 85.6% on my sweep (81.6% on the
card's), with whole files at 0%. That does not refute "ray is a body id" - the ray value may
still be a body id while the shape's `CPfxPartIndexProperty` uses another numbering - but it
means the "one id space" claim is an **inference from the donor**, not a fleet invariant.
UNKNOWN: which numbering `CPfxPartIndexProperty` uses on the 15 failing files. The card says
the same thing in its own UNKNOWN 1.

## 3. Claim (2): static-compound references, followed to the part bodies

Two references, followed independently with offsets (the compound's instances are at
`compound+0x60`; a body references a compound when its 96-byte entry's shape pointer equals
the compound's offset):

| file | compound | extent | instances | body ref | body entry offset | shape pointer | part_index | part |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `racinghothatch.physicsc` | `0xa440` | 720 | 4 | 10 | **`0x3c20`** (array ptr `0x3860` + 96*10) | -> `0xa440` | 10 | `racinghothatch_bumper_f` |
| `modernbus.physicsc` | `0xa950` | 464 | 2 | 0 | **`0x60c0`** (array ptr `0x60c0` + 96*0) | -> `0xa950` | 0 | `modernbus_body` |

- decoded: both compounds are `hknpStaticCompoundShape`, referenced by exactly one body entry,
  and that body's `CPfxPartIndexProperty` names a real part; the card's decode path
  (compound -> body ref -> part index -> part name) **reproduces**.
- decoded: their children are `hknpConvexPolytopeShape` with `part_index = None`
  (`0xa790/0xaa10/0xad30/0xaf50` for the first, `0xaba0/0xb730` for the second), matching the
  donor's "children are not in the body table and carry no part index".
- decoded: across my 40-file sweep there are **444** static compounds; 357 are referenced by at
  least one body, 87 by none, and none is referenced by more than one body (so a compound names
  one body, not several). The 87 without a body ref are the "(0, n)" cases the card reports.
- **decoded, and where a sentence overgeneralises**: of 1,811 compound children in the sweep,
  **223 are themselves a body entry's shape** and **244 carry a non-None part_index**. The
  card's §1 sentence ("its seven children are ... that are not in the body table and carry no
  part index") is donor-true, but the later generalisation "The body's shape is the addressable
  one; the child instances are not addressable through the body table" is **false fleet-wide**:
  a child shape that is also some body's shape is reachable through the body table (223 cases).

## 4. What else I re-read

- `uv run python Tools/scripts/jc3_physics_roles5.py --check` -> all 12 invariants pass, the
  three measured rates reproduce (6309/6309, 6309/6309, 5466/6696 parts, 50/121 permutation,
  1165/1167 parent-has-part), no drift. The card is current against today's files.
- decoded: the fleet denominators in the card mix two units - "121 entries name a `.physicsc`"
  (entity decodes) and "40 distinct files, decoded once each" (raw files). The `1480/1480`
  compound check covers 1,480 of the 2,677 static compounds the card itself counts; the
  remaining 1,197 are not in that oracle. Similarly my sweep's 444 compounds are the raw-file
  subset. The card should say "of the 1,480 compounds in the raw subset" instead of "the
  decoded fleet".

## 5. Issues

### I1 - the id-space invariants are near-vacuous (major for the headline, minor for the data)

`ray_in_table` (6309/6309) cannot fail while every ray id is a small integer, and
`ray_selects_a_shape` (6309/6309) cannot fail while all body entries carry a shape - I measured
2,936/2,936 shaped entries. Fix: report the identity rate next to them as the actual evidence,
and rename the headline to what is proven ("ray is a body id in range; on the donor and three
sampled files the entry carries the part's index").

### I2 - "No second id space" is stronger than the evidence (minor)

It is true that no *separate shape table* is needed: 1,949/1,949 ray ids are body-entry indices.
It is not proven that the entry they select is the part's body, because on `bavariumtank` 0/38
and `armoredjeep` 12/67 the entry's part index is a different part. The card's §1 caveat says
so, but the bold sentence does not. Fix: move the caveat into the sentence.

### I3 - "child instances are not addressable through the body table" is false fleet-wide (minor)

223 of 1,811 compound children are also a body entry's shape (decoded, same decoder the card
uses). Fix: "in the donor the children are not body entries; fleet-wide 223/1,811 are, so a
child may be reachable as that body."

### I4 - denominators are unstated in the compound oracles (minor)

`1480/1480` covers 1,480 of 2,677 static compounds; the report's phrase "across the decoded
fleet" reads as if all were tested. Fix: name the subset.

## 6. What I could not check

- **Which numbering `CPfxPartIndexProperty` uses** on the 15 files where identity fails
  (`bavariumtank` etc.). The card's UNKNOWN 1 covers exactly this; I confirm it is still open.
- **Whether a ray id is used at runtime at all.** The field is decoded from the parts module;
  its consumer is native and not in this tree.
- **The 24 donor body ids that no part names** (card §2): I did not re-derive that list beyond
  the three files above.
- **Compounds in the 1,197 static compounds outside the raw subset** (files without a raw
  `.physicsc`): not decodable here, as the card says.
- **The AABB-overflow numbers** in §3: I followed two compounds' references but did not
  re-measure the child AABB overflow (the donor's 0.0202 m) independently.

## 7. Commands run (verbatim, project root)

```
$ uv run python Tools/scripts/jc3_physics_roles5.py --check
OK   donor_rays_resolve [invariant]: 42/42 (no-ray parts [])
OK   donor_window_is_extern_block [invariant]: 18 rays >= 42, 18 extern bodies
OK   donor_ray_below_window_is_hull_or_compound [invariant]: 24 rays below the extern block
OK   donor_compound_single_body [invariant]: ['1 body / 1 parent', '1 body / 1 parent']
OK   donor_compound_children_nested [invariant]: [0, 0]
OK   donor_compound_child_has_no_part [invariant]: [[None], [None]]
OK   fleet_ray_in_body_table [invariant]: 6309/6309
OK   fleet_ray_selects_a_shape [invariant]: 6309/6309
OK   fleet_world_body_in_table [invariant]: 6265/6265
OK   fleet_compound_is_body_or_child [invariant]: 1480/1480; combos {'(0, 1)': 313, '(1, 0)': 2, '(1, 1)': 810, '(1, 2)': 355}
OK   fleet_compound_child_is_object [invariant]: 6093/6093
RATE fleet_property_is_permutation [measured]: 50/121 files
RATE fleet_part_index_identity [measured]: 5466/6696 parts (121 files); delta histogram {'-45': 3, '-43': 3, ...}
RATE fleet_static_parent_has_part [measured]: 1165/1167
OK   fleet_one_system_per_file [invariant]: 0 without
OK   fleet_compound_data_pair [invariant]: 233/233
OK   fleet_extern_le_polytope [invariant]: 233/233
invariants not universal: none
measured rates below 1.0 (reported, not asserted): ['fleet_property_is_permutation', 'fleet_part_index_identity', 'fleet_static_parent_has_part']
CHECK_EXIT=0
```

```
$ uv run python tmp/freebuff/scratch/roles5_review.py
== racinghothatch.physicsc  708848 B  objects 614  body entries 85  parts 56
  rays present 52/56  in bounds 52  entry has shape 52  entry.part_index == part index 52  part.body == ray 21
  duplicate ray ids: none
  entry shape classes: {'hknpConvexPolytopeShape': 42, 'hknpStaticCompoundShape': 10, 'hknpExternMeshShape': 31, 'hknpDynamicCompoundShape': 2}
  compound 0xa440 extent 720 refs [10] -> body 10 entry_off 0x3c20 shape 0xa440 part_index 10 part racinghothatch_bumper_f
== modernbus.physicsc  479296 B  objects 900  body entries 118  parts 90
  rays present 90/90  in bounds 90  entry has shape 90  entry.part_index == part index 90  part.body == ray 64
  duplicate ray ids: none
  compound 0xa950 extent 464 refs [0] -> body 0 entry_off 0x60c0 shape 0xa950 part_index 0 part modernbus_body
== oldjeep.physicsc  678576 B  objects 794  body entries 106  parts 71
  rays present 64/71  in bounds 64  entry has shape 64  entry.part_index == part index 64  part.body == ray 24
  duplicate ray ids: none
  compound 0x8f10 extent 464 refs [3] -> body 3 entry_off 0x4640 shape 0x8f10 part_index 3 part oldjeep_back_seat
```

```
$ # fleet sweep over the 40 raw .physicsc files that have a parts row (inline script)
files 40 parts 2057 rays 1949 in-bounds 1949 shaped 1949 identity 1669 rate 0.8563 dup-ray-ids 0
out-of-bounds rays: none
body entries 2936 with shape 2936
files with identity < shaped: 15
   ('apc', 45, 44, 37, 44, [(31, 72, 43, 'apc_undercarriage'), (33, 73, 44, 'apc_wheel_c_l')])
   ('armoredjeep', 67, 67, 12, 67, [(0, 71, 3, 'armoredjeep_body'), (1, 1, 2, 'armoredjeep_antenna_base')])
   ('bavariumtank', 38, 38, 0, 38, [(0, 46, 8, 'bavariumtank_body'), (1, 28, 3, 'bavariumtank_headlight_d_l')])
   ('modernsaloon', 46, 42, 16, 42, ...)
   ('technicaljeep', 56, 55, 46, 55, ...)
   ... (15 files total)
compounds {'total': 444, 'with_ref': 357, 'no_ref': 87} children 1811 child-is-body-entry 223 child-with-part 244
```

```
$ # the two counterexamples, with entry offsets
== bavariumtank: bodies 57, parts 38
  part  0 bavariumtank_body                ray  46 -> entry 46 at 0x3df0 class hknpExternMeshShape        entry.part_index 8 (names bavariumtank_skirt_l_1)
  part  1 bavariumtank_headlight_d_l       ray  28 -> entry 28 at 0x3730 class hknpConvexPolytopeShape    entry.part_index 3 (names bavariumtank_shield_body)
  part  2 bavariumtank_headlight_d_r       ray  29 -> entry 29 at 0x3790 class hknpConvexPolytopeShape    entry.part_index 4 (names bavariumtank_signal_l_f)
  part  3 bavariumtank_shield_body         ray   0 -> entry  0 at 0x2cb0 class hknpConvexPolytopeShape    entry.part_index 1 (names bavariumtank_headlight_d_l)
== armoredjeep: bodies 106, parts 67
  part  0 armoredjeep_body                 ray  71 -> entry 71 at 0x6620 class hknpExternMeshShape        entry.part_index 3 (names armoredjeep_door_f_l)
  part  1 armoredjeep_antenna_base         ray   1 -> entry  1 at 0x4be0 class hknpConvexPolytopeShape    entry.part_index 2 (names armoredjeep_axe)
  part  2 armoredjeep_axe                  ray   2 -> entry  2 at 0x4c40 class hknpConvexPolytopeShape    entry.part_index 37 (names armoredjeep_antenna)
```

## 8. Limits

- My sweep is raw-file level (40 files), one parts row per file (the first row whose entity
  token matches the file stem); the card's is entity-decode level (121 rows sharing 40 files),
  which is why my 1,949 rays / 2,057 parts differ from its 6,309 / 6,696. The rates agree in
  size (0.856 vs 0.816), not to the digit.
- I did not re-measure the donor's own 42-row table or its AABB overflows; I recomputed three
  other files and two references as the brief asked.
- No runtime: nothing here says the engine uses the `ray` field at all.
