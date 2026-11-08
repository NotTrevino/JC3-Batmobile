# AUDIT-G3-01 — the collision card audited against the packages

STATUS: done

`Research/BatmobileGrab/COLLISION.md` / `.json` (G3-01, generator `grab_collision.py`) were audited by
re-parsing all **22** exports it lists with `Tools/scripts/upk_read.py`, independently of the card's own
walker, and by checking its four tracker claims plus every statement the later cards have superseded.
Nothing in the card was edited.

**The card itself is largely sound** — all 22 objects re-parse to exactly the shape it records (start
offset, tag count, parsed end, tail hex, and all six input sha256s match), no published flag name is
wrong, and its `svehicle_tail_check` reproduces byte for byte. **The tracker row built on top of it is
not**: of its four claims, one is right about the count and wrong about the bytes, two misdescribe the
primitive set, and one states a cylinder-name assignment the card deliberately marks UNKNOWN.

## The verdict, claim by claim

| claim (G3-01 tracker row) | verdict |
|---|---|
| 7 objects, Startup 7530 / 82147 / 82148 / 169640 / 171103 / 171104 / 154788 | **holds** — 7 exports, 1,264 B, classes as listed |
| …with **0 unparsed bytes** | **WRONG** — **54** unparsed bytes in 3 of the 7: 169640 12 B, 171103 21 B, 171104 21 B |
| two StaticMesh components, switched by mode | **holds** |
| **three CylinderComponents** | **WRONG at that layer** — Startup + BmGame carry templates for **two** (82147/82148 → 142597/142598); the third (Playable 276) has no template in either chain |
| a **mode-dependent set** of (2 static + 3 cylinders + RB_StayUprightSetup + SVehicleMesh) | **WRONG** — only the two StaticMesh components are attached/detached (G3-01e-fix mesh table 0/1/2); the cylinders, StayUpright and SVehicleMesh exist in every mode |
| 78.0 / 175.0 as **radius/height** at 540/544 | **values hold** (both re-derive exactly), **names UNKNOWN** — no layout names 540 or 544, and the card says so itself |

Two further card defects the audit found:

- **`RB_StayUprightSetup` is the wrong export name.** Startup **154788** and BmGame **172112** are both
  named `MyStayUprightSetup`; only the Playable instance **5106** is `RB_StayUprightSetup`. The card
  states that the instance→template link is by component name — for this component the names do not
  match, so that link cannot have been the name there. The other five components do match.
- **`0 unparsed bytes` contradicts the card's own UNKNOWN list**, which already records the 12/21/21
  tails. The row was written as if the tails did not exist.

## What the card gets right (re-derived, not quoted)

| item | result |
|---|---|
| input hashes | all 6 sha256 match the recorded ones — the audit is provably on the same bytes |
| all 22 objects re-parsed | 22/22 identical to the card's recorded start / tags / parsed_end / tail_hex |
| flags at 476 and 484 | every published flag name re-derives from the object's own 32-bit word + the BMSDK mask table (0 disagreements) |
| `svehicle_tail_check` | reproduces: the 84-byte tail is the object's own `XRayMaterials` payload (76 B at offset 556 = int32 18 then 18×779) plus 8 zero bytes |
| `CollisionCylinder` at `Pawn.CylinderComponent` (900) | holds — archetype 5281 carries `Batmobile.CollisionCylinder` at offset 900 |
| cylinders at 540/544 | 78.0 / 175.0 exactly, in both BmGame base templates |
| unparsed total, all 22 objects | 234 B of 9,553 B, all zero except the XRayMaterials copy |

Flag facts the card does **not** state, now decoded:

- the two cylinder primitives carry `0x110a4222` at 484, which sets **no** `CollideActors`,
  `BlockActors`, `BlockZeroExtent`, `BlockNonZeroExtent` or `BlockRigidBody` bit — unlike the two
  StaticMesh collision meshes (`0x11027e32`, which sets all of them). So the cylinders are not the
  blocking collision of the car.
- the card mixes layers inside one row (PerInstanceRandom and 476 from the instance, 484/540/544 from the
  BmGame base). An effective flag word assembled across layers is **derived**, not decoded; the card's
  `value_from` labels make it traceable, but the picture is not the instance's serialised state.

## Statements the later cards superseded (8)

| # | the card says | status | superseded by |
|---|---|---|---|
| S1 | which component is active in each mode is UNKNOWN | **STALE** | G3-01e-fix §1 — selector = BmGame 10894, table 0/1/2 (runtime only ever shows 0 and 1) |
| S2 | StaticMesh BodySetup AggGeom not decoded, no geometry claimed | **STALE** | G3-01c — 56 elements decoded, 56/56 ElemBox oracle |
| S3 | PhysicsAsset bodies and constraints not decoded | **PARTLY STALE** | G3-01d — bone 0 chassis box decoded; others still open |
| S4 | actor→PSK frame link UNKNOWN, JC3 positions conditional | **STALE** | G3-01d — link PROVEN within tolerance; component offsets [5,0,0] (pursuit) / [10,0,-15] (battle) are not in the card's JC3 positions |
| S5 | BodySetup 169748 "walk parsed 25958, unparsed 17388" | **STALE** | G3-01c — every AggGeom byte accounted; "unparsed" describes the tag walk, not geometry |
| S6 | tail sizes listed for templates only | **INCOMPLETE** | instances 5392/5393 also carry 21 B |
| S7 | offset 556 ArrayProperty "not decoded" | **INCOMPLETE** | the card's own tail check decodes exactly that payload |
| S8 | prefixes: 4 zero bytes in instances, 12 in templates | **INCOMPLETE** | archetype 5281 starts at 1 (1 zero byte), both CDOs at 0 (no prefix) |

Also found, in a later card rather than this one: **G3-01e-fix's selector size/hash line cannot be
reproduced from the export.** BmGame export 10894 `SetBatmanVsBatmobileCollisionMode` is **291 B**, sha1
of the whole export `7f78b9fb17b1cf5417619fbed42bf219c1619ef7`. The quoted **253 B / sha1
`c2f6a2ee…788`** is exactly export bytes **[22:275]** — a 253-byte slice, verified by search over every
offset. Its mesh table is unaffected; the size/hash line is a slice, not the export.

## Files written

- `Tools/scripts/audit_g301.py` — new, `--write` / `--check` (the check re-parses everything and compares
  the JSON and the rendered text byte for byte)
- `Research/BatmobileGrab/AUDIT_G301.md` — the audit (186 lines, 17 oracles, 8 stale statements)
- `Research/BatmobileGrab/AUDIT_G301.json` — the same data, machine-readable
- `tmp/freebuff/reports/AUDIT-G3-01.md` — this report

Read-only inputs: the three packages (`Playable_Batmobile_SF.upk`, `Startup.upk`, `BmGame.upk`),
`COLLISION.md`/`.json`, `Collision_CONVEX`/`_FRAME`/`_SELECTOR2`.md, `BMSDK_OFFSETS.json`,
`upk_read.py`, plus `grab_collision.py` read only to confirm what `svehicle_tail_check` compares.

## Commands run, with output

1. Structure of the card's JSON (which objects, which tails it recorded):

```
$ python - <<'PY'  # print COLLISION.json objects, primitives, svehicle_tail_check, unknown
archetype:Batmobile            exp=5281  size=3905 start= 1 parsed_end=3905 tags=136 tail=[3905,3905]
...
instance:SVehicleMesh          exp=5289  size= 258 start= 4 parsed_end= 174 tags=  6 tail=[174,258] tailhexlen=84
startup_template:SVehicleMesh  exp=169640 size= 58 start=12 parsed_end=  46 tags=  3 tail=[46,58] tailhexlen=12
svehicle_tail_check: {"XRayMaterials_payload_bytes": 76, "remaining_bytes_after_copy_all_zero": true,
  "tail_bytes": 84, "tail_starts_with_XRayMaterials_payload": true}
unknown: 12
```

2. First `--write` (my re-walk disagreed with the card on 20 rows):

```
objects: 22 | startup-7 tails: 60 B | all tails: 242 B
  every_export_reparses_to_the_recorded_shape    False
  recorded_tail_bytes_sum_matches_reparse         False
write_exit=1
```

   Cause was mine, not the card's: `upk_read.walk_tags` returns the terminator's own offset and never
   emits it as a tag, and my start-scorer let a zero-tag walk at offset 40 win on short objects. After
   normalising the terminator and requiring a real walk:

```
objects: 22 | startup-7 tails: 54 B | all tails: 234 B
  every_export_reparses_to_the_recorded_shape    True
  recorded_tail_bytes_sum_matches_reparse         True
```

3. Where the card's Translation at 400 lives (my C3 table was empty because I read offset 400 as a float;
   the tags are `VectorProperty`):

```
--- base_template:FrontCollisionCylinder  exp=142597
    [(540,'FloatProperty',78.0), (544,'FloatProperty',175.0), (316,'ObjectProperty','ReplacementPrimitive'),
     (364,'FloatProperty',0.4289...), (400,'VectorProperty',[100.0,0.0,0.0]), (484,'BoolProperty',True),
     (512,'StructProperty','LightingChannels')]
--- base_template:RB_StayUprightSetup  exp=172112 name=MyStayUprightSetup
    []
--- startup_template:RB_StayUprightSetup  exp=154788 name=MyStayUprightSetup
    []
```

4. Which 253-byte blob G3-01e-fix hashed:

```
size 291
slice hits: [(22, 253)]
full 7f78b9fb17b1cf5417619fbed42bf219c1619ef7
bmgame 10894 291 7f78b9fb17b1cf54
```

5. Final write and check:

```
$ PYTHONIOENCODING=utf-8 uv run python Tools/scripts/audit_g301.py --write; echo "write_exit=$?"
$ PYTHONIOENCODING=utf-8 uv run python Tools/scripts/audit_g301.py --check;  echo "check_exit=$?"
objects: 22 | startup-7 tails: 54 B | all tails: 234 B
flag mismatches: 0 | stale statements: 8
  inputs_are_the_recorded_bytes                        True
  every_export_reparses_to_the_recorded_shape          True
  recorded_tail_bytes_sum_matches_reparse               True
  tap_object_set_is_22                                  True
  tap_seven_startup_exports_present                     True
  tap_tail_claim_contradicted                           True
  startup_carries_two_cylinder_templates                True
  three_cylinder_instances_in_the_playable_layer        True
  cylinder_floats_are_78_and_175                        True
  svehicle_tail_check_reproduces                        True
  flag_names_rederive_from_the_mask_table               True
  selector_export_found                                 True
  static_meshes_have_no_bounds_tag                      True
  stale_statements_each_name_a_later_card               True
  only_the_stayupright_templates_are_misnamed           True
  selector_quoted_blob_located                          True
  archetype_900_slot_is_the_collision_cylinder          True
write_exit=0
OK: 22 objects re-parsed, 8 stale statements, all 17 oracles true
verdicts: C1b WRONG (54 unparsed B in the 7), C2b/C2c WRONG, C3 values hold / names UNKNOWN
check_exit=0
```

## Values, labelled

| value | label |
|---|---|
| 22 exports, their sizes, start offsets, tag counts, parsed ends and tail hex | **decoded** (each package export, re-walked with `upk_read.walk_tags`) |
| 54 B unparsed in the 7 Startup objects; 234 B of 9,553 B across all 22 | **derived** (size − parsed end, per object, summed) |
| 78.0 at 540, 175.0 at 544 in 142597 and 142598 | **decoded** (FloatProperty payloads) |
| which of the two is the radius | **UNKNOWN**; the geometry test (78 fits the 159.16 cm half-width, 175 does not) is **derived** under a stated assumption |
| flag words 0x110a4222 / 0x11027e32 / 0x1582fe32 / 0xd0004011 and every flag name | **decoded** (BoolProperty payload + BMSDK mask table) |
| 8/22 objects with a tail, 9 including the 84-byte instance | **derived** |
| selector export 291 B, sha1 `7f78b9fb…`; quoted 253 B = bytes [22:275] | **decoded** / **derived** (slice search) |
| that the tracker row and the card disagree | **derived** (comparison of the row's sentence with the re-parse) |

## UNKNOWNs

1. **CylinderComponent field names at 540/544** — `BMSDK_OFFSETS.json` has no CylinderComponent layout and
   no decoded file labels them; radius vs height is unresolved (the geometry test only narrows it).
2. **What the zero tails *mean*** (21 B StaticMeshComponent, 12 B SVehicleMesh, 84 B instance) — decoded as
   bytes, no layout covers them. Whether they are padding, a field, or a cooked duplicate is not proven.
3. **What the 18 × 779 values in the SVehicleMesh tail mean** — they reproduce the object's own
   `XRayMaterials` payload, so the copy is proven but the values are unnamed.
4. **Whether battle mode (value 2) ever attaches** — decoded in the selector, never observed: no sample in
   the 7 runtime logs carries value 2.
5. **Which package record carries the reference-skeleton transforms** — G3-01d's U-1, not reopened here.
6. **The `MyStayUprightSetup` ↔ `RB_StayUprightSetup` link** — the names differ, so *how* places the
   instance on the template is not decoded; only the slot/class evidence says they correspond.
7. **Why the tracker row claims 0 unparsed bytes** — no file explains the sentence; the card's own numbers
   contradict it, so this is a provenance question, not a decoding one.

This audit does not re-derive G3-01c/d/e's own numbers (their `--check`s own that), except the two cheap,
decisive ones reported above (the selector slice, and the StaticMesh exports carrying no `Bounds` tag).
