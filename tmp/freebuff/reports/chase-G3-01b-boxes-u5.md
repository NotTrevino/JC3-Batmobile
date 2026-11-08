# Chase G3-01b / U-5 — the wreck-box union contradiction

**STATUS: resolved**

The contradiction is an artefact of G3-01b's frame, not of the extents convention.
The wreck boxes are **bone-local**; re-doing the union with the wreck skeleton's bind
pose makes the **FULL-length** reading the only one that matches the wreck mesh, and the
"half-length matches" result disappears.

## Answer

- **Frame:** each box's `TM` is relative to its own bone (`T_component = T_bone * T_box`).
  Proof: the wreck skeleton in each package is flat (all 32 bones are children of `Root`),
  and when the box is placed at its bone **23/32** boxes enclose their own bone; read as a
  component-space centre, **1/32** do, with a median 193.1 cm between the translation
  value and the bone it is welded to. G3-01b's numbers are exactly reproduced by that
  wrong reading: `453.2 / 197.09 / 156.04` (FULL) and `717.94 / 394.18 / 247.9` (HALF),
  which is what its U-5 row published.
- **Extents convention:** **FULL lengths**. In the bone frame the 128-box union is
  **704.71 × 347.02 × 239.30 cm**, against the wreck SkeletalMesh's own bounds
  **706.833 × 374.680 × 231.009 cm** (worst axis deviation **7.4 %**). The half-length
  reading gives **913.80 × 435.88 × 315.06 cm** (worst deviation **36.4 %**) — 4.9× worse.
  The independent chassis-box oracle points the same way: full extents 690.305 / 374.536 /
  207.500 cm against the intact render mesh's 702.560 / 349.530 / 234.185 cm
  (ratios 0.983 / 1.072 / 0.886); half extents would be 1380.6 / 749.1 / 415.0 cm for a
  7.03 × 3.50 × 2.34 m car.

So G3-01b's verdict (FULL lengths) stands, its U-5 limitation can be closed, and the
"half lengths match the wreck" observation was measuring a union of bone offsets, not of
boxes on the car.

## What the bytes gave that G3-01b did not use: the wreck reference skeleton

The cooked `SkeletalMesh` export `Batmobile_V3_Destroyed` carries an `FReferenceSkeleton`
of 32 bones in all four wreck packages (byte 1408 of the export in every one). The record
is 44 bytes and its fields sit **before** the bone name — this is why a name-anchored read
of `+32` lands on the *next* bone's position (the trap that made a layout fit look
shifted):

| offset | bytes | content |
|---:|---:|---|
| −28 | 16 | quat (x, y, z, w), parent-relative |
| −12 | 12 | position (cm), parent-relative |
| 0 | 8 | FName (name index, `number = 0`) |
| +8 | 4 | parent index |
| +12 | 4 | `-1` on every record |

Layout oracle (the check that would fail if this were wrong): the same read on the intact
`Batmobile_V2` export reproduces `BONES.json`'s PSK bind pose — **180/180** local
positions (worst 0.0000 cm), **180/180** parent indices, **180/180** component positions
after accumulation (worst 0.0251 cm), **180/180** local rotations under the PSK's mirrored
handedness `(x, −y, z, w)`. The wreck skeleton then validates structurally: 32/32 body
bones present, all parents = 0 (`Root`), 4/4 packages byte-identical at byte 1408.

This also revises a G3-01d UNKNOWN (U-1: "the ref-skeleton record's transform fields are
UNKNOWN"): the layout is now decoded and proven, with the fields 28 bytes before the name
rather than after it.

## Files written

| file | what |
|---|---|
| `Tools/scripts/grab_box_union_frame.py` | the tool (`--write` / `--check`), new script |
| `Research/BatmobileGrab/BOX_UNION_FRAME.json` | full data: box records, both skeletons, unions, 15 checks |
| `Research/BatmobileGrab/BOX_UNION_FRAME.md` | the record (generated) |
| `tmp/freebuff/reports/chase-G3-01b-boxes-u5.md` | this report |

G3-01b's files were **not** touched (verified with `git diff` on
`grab_collision_boxes.py`, `COLLISION_BOXES.md`, `COLLISION_BOXES.json`; all output empty).
No other task's files edited; reads only of `BONES.json`, `MESHES.json` and the game
installs. No game launched or attached; nothing under `Builds/`; no git operations.

## Commands and outputs (verbatim)

```
python -m py_compile Tools/scripts/grab_box_union_frame.py
```
```
COMPILE_OK
```
exit status **0**

```
uv run python Tools/scripts/grab_box_union_frame.py --write
```
```
wrote BOX_UNION_FRAME.json and BOX_UNION_FRAME.md; 15/15 checks; FULL lengths
```
exit status **0**

```
uv run python Tools/scripts/grab_box_union_frame.py --check
```
```
OK: 15/15 checks, union FULL lengths
```
exit status **0**. `--check` re-reads all five packages, re-decodes the 131 box records
and the 180 + 32 bone records, re-runs every oracle and fails if
`BOX_UNION_FRAME.md`/`.json` differs by one byte.

Key rows the tool prints (from `BOX_UNION_FRAME.json`):

```
union bone frame FULL : 704.71 / 347.02 / 239.30 cm   vs mesh 706.833 / 374.680 / 231.009  -> 7.4 %
union bone frame HALF : 913.80 / 435.88 / 315.06 cm   -> 36.4 %
G3-01b reading FULL   : 453.20 / 197.09 / 156.04 cm
G3-01b reading HALF   : 717.94 / 394.18 / 247.90 cm
bones inside own box  : bone-local 23/32, translation-as-coordinate 1/32
chassis FULL vs render: 690.305/374.536/207.500 vs 702.560/349.530/234.185 (0.983/1.072/0.886)
```

## Checks actually run (15/15)

1. layout reproduces PSK local positions — 180/180
2. … parent indices — 180/180
3. … component positions after accumulation — 180/180
4. … local rotations (PSK-mirrored) — 180/180
5. 32-bone wreck skeleton decoded in 4/4 packages — byte 1408 in each
6. every body bone exists in the wreck skeleton — 32/32
7. wreck skeletons are flat (all parents 0) — 4/4
8. bone enclosure: 23/32 bone-local vs 1/32 component
9. same union in 4/4 packages
10. G3-01b's published numbers reproduced from the translation-as-coordinate reading
11. FULL union within 15 % of the wreck mesh bounds — 7.4 %
12. HALF union more than 2× further — 36.4 %
13. chassis FULL extents within 15 % of the render bounds — 11.4 %
14. chassis HALF extents far outside — ratios 1.965/2.143/1.772
15. the four packages carry identical box + skeleton layouts

## UNKNOWNs

| # | unknown | what was tried | why it stays UNKNOWN / where it would be found |
|---|---|---|---|
| U-1 | whether the wreck SkeletalMesh stores its own `FBoxSphereBounds` equal to the PSK vertex bounds used here | scanned export 5285 (3,637,836 B) for the float triples 353.4/187.3/115.5 and the full sizes: no occurrence; the package's property tags for 5285 are only `ClothingAssets`, `ClothingTeleportRefBones`, `LODInfo`, one bool and one float | a decoded `FBoxSphereBounds` layout for this build (the value may live inside the LOD model blob), or the PSK export itself. The oracle is therefore the PSK vertex bounds already recorded in `MESHES.json` (706.833 × 374.680 × 231.009), not a value re-read from the upk |
| U-2 | why the destroyed asset has no chassis body | re-read all 32 bodies: wheels/suspension, cockpit, doors, turret, jet fin, debris fragments only | the destroyed mesh's skin weights per bone — which body the hull would be expected to follow |
| U-3 | whether the boxes' `0x4C` bool or the flat parenting changes behaviour at runtime | out of scope here; the frame and size questions do not depend on either | G3-06 native layouts / a runtime capture |

## Limitations

- The mesh-bounds oracle is a PSK vertex measurement (via `MESHES.json`), not a value read
  from the `.upk`; see U-1.
- A collision-envelope union is expected to be at or just above the visual mesh, not equal
  to it: FULL gives +7.4 % worst axis, which is the right order; HALF gives +36.4 %.
- `BOX_UNION_FRAME` does not re-derive the `0x4C` bool's meaning or the convex element
  layout; both remain as G3-01b left them.
