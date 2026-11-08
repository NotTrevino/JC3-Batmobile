STATUS: partial — inertia's **home and packed form are decoded on the JC3 side** (56 `hknpShapeMassProperties` blocks: mass `f32` at `+0x28`, centre of mass in payload group 1, inertia diagonal in group 2, exponent bias 111 measured), and **BmAK's cooked physics is proven to carry no mass and no tensor at all**; the brief's oracle (stored inertia == a box/hull formula) is **refuted on every resolvable body** (0 of 107 single-box fleet bodies at 1 %, 0 of 1651 at the exact hull tensor), so the absolute semantics of the JC3 diagonal — and therefore the Batmobile's inertia tensor — stays **UNKNOWN**.

## What was asked, and what was found

Brief: find where inertia lives in the cooked physics data, both sides (BmAK `grab_collision_geom.py` / `COLLISION_GEOM.md`; JC3 `jc3hkx.py` / `PHYSICS_ROLES.md`), decode the mass-properties record for "the 56 BmAK masses" and a JC3 donor vehicle, and test with the box oracle whether the stored values equal a box/hull formula.

Two corrections to the premise, both from the bytes:

1. **The 56 mass-properties records are not BmAK's.** `hknpShapeMassProperties` is a Havok class; BmAK's cooked format is UE3 and has no such object. The 56 blocks are the **JC3 Serpente donor's** (`sportsmuscle.physicsc`), and that is what was decoded. BmAK's body setups were decoded separately and carry no mass field at all.
2. **BmAK's `AggGeom` has no inertia to find.** Its whole serialized property list is `PreCachedPhysDataVersion`, a bone `NameProperty`, one `BoolProperty` and `AggGeom`; and a scale-free scan of every aligned f32 triple in all four payloads finds **0** triples shaped like the decoded boxes' or hulls' moment tensor. So the Batmobile's mass and inertia cannot be read out of its cooked collision physics — that is a decode, not a failure to look.

The JC3 side does hold a tensor, and this pass decodes it end to end, but the box/hull oracle refutes the "collision shape's tensor" reading: the stored diagonal is a **near-uniform 1.277x** the collision box's `m/12*(b^2+c^2)` on all three moments (medians 1.2752 / 1.2877 / 1.2767), which is one scalar defect, not scatter — i.e. the tensor was authored from geometry slightly larger than the collision hull, not computed from it.

## Files written

- `Tools/scripts/grab_inertia.py` — new tool, `--write` / `--check` (no existing tool was edited). Decodes both formats, links shapes to mass blocks, runs the bias ladder, the box oracle, the exact hull-tensor oracle, a scale-free f32-triple scan on both sides, and renders the note. `--check` recomputes every number from the source bytes, compares `INERTIA.md`/`.json` byte-for-byte, re-runs all 12 oracles and fails on drift.
- `Research/BatmobileGrab/INERTIA.md` — generated note (214 lines): verdict table, BmAK tag census + geometry + scan, the 48-byte JC3 record with all 56 donor rows, the bias ladder, the box/hull oracle tables, oracles, UNKNOWNs.
- `Research/BatmobileGrab/INERTIA.json` — generated data (all 56 donor blocks, 107 fleet box rows, bias ladder, oracles, verdict, UNKNOWNs).
- `tmp/freebuff/scratch/inertia_bmak_probe1.py`, `tmp/freebuff/scratch/inertia_g3_10c_log.txt` — scratch probe and raw command log (both in `scratch/`).

Read-only inputs touched: `E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole/BmGame.upk`, `Builds/test-091/.../sportsmuscle.physicsc`, `E:/Modding/_gamedata/JC3grab/hkx/all` (41 files). No game process, no install folder write, no existing `Research/` or `Tools/` file edited.

## Values, labelled

| value | label |
|---|---|
| BmAK body setups 169748/169749/169750/169751 serialize only `PreCachedPhysDataVersion`, NameProperty (2 of them), BoolProperty, `AggGeom` | **decoded** (`BmGame.upk` export tag streams, §1) |
| no `Mass`/`MassScale`/`Inertia` property on any of them; PhysicsAsset 158266 tags are `BodySetup`, `BoundsBodies`, `Bounds`, `ConstraintSetup` | **decoded** (same walk) |
| BmAK box records: 8-byte header (sphere count, box count), then 20-byte `TM` tag + 64-byte TM + extent floats at tag offsets 0x40/0x44/0x48 + bool at 0x4C | **decoded** (tag name resolves to `TM`, size 64; extents land at byte 92 as G3-01b recorded) |
| chassis boxes: extents 690.305/374.536/207.5 cm and 679.585/345.688/103.5 cm; centres 9.0/0.0/106.75 and 0.0/0.0/79.0 cm (TM floats 13..15) | **decoded** — centres now agree exactly with `COLLISION_GEOM.md`, an independent confirmation of the TM reading |
| weapons-trans box: 166.177/189.365/39.8 cm, centre −30.5/0.0/93.25 cm | **decoded** |
| convex element 0 hulls: 3.6029 m³ (battle), 3.4489 m³ (pursuit) | **derived** (tetrahedral decomposition of the decoded vertices) |
| 0 tensor-shaped triples in 9006 aligned triples of the four `AggGeom` payloads | **decoded negative** (scale-free test, 1 %) |
| JC3 `hknpShapeMassProperties` = 48 B, 16 zero bytes, 24-byte payload (three `int16x4`), mass f32 at +0x28, f32 at +0x2c | **decoded** (56/56 donor blocks, extent 48 in all 56) |
| payload group 1 = centre of mass; exponent `value = mantissa * 2**(floor(w/128) − 111)` | **decoded / derived** (oracle: hull centroid, median error 0.0156 of the body's largest extent, 91.9 % within 10 %; bias 110 and 112 are a factor of two out) |
| payload group 2 = inertia diagonal in the shape frame | **derived** (decode that lands the COM also lands the diagonal's axes on the hull's; absolute semantics refuted below) |
| 54 of 54 donor polytopes resolve to a mass block; 40 of them are body-level shapes | **decoded** (shape+0x20 → `hkRefCountedProperties` → +0x10) |
| donor mass total 1627.097 kg over 56 positive blocks | **decoded** |
| total mass fig for the chassis body 800.0 kg, stored diagonal 973.56/1128.31/396.81 kg·m², box formula 1000.19/1192.08/387.75, exact hull 820.36/980.80/304.43 | **decoded** (diagonal) / **derived** (box, hull) |
| box oracle: 0/107 at 1 %, 1 at 2 %, 14 at 5 %, 34 at 25 %; median ratio 1.275/1.288/1.277 | **derived** (stored diag ÷ `m/12*(b²+c²)`) |
| hull oracle over all 1651 hull bodies: 0 hits at 1 %, 1 at 2 %, 14 at 5 %, 166 at 25 % | **derived** (stored diag ÷ exact tetrahedral tensor at the stored mass) |
| the hull accumulator itself is validated: hull tensor == `m/12*(b²+c²)` on box bodies to 1.85e-4 | **derived** (two independent code paths, `hull_tensor_reproduces_box_formula_on_boxes`) |
| 8 scale-free f32-triple hits in the donor data section, all inside `hkGeometry` objects, 0 inside a mass block | **derived** (recorded as coincidences, not read as tensors) |
| the Batmobile's mass and inertia tensor | **UNKNOWN** |

## Commands run, verbatim

### 1) BmAK property tags of the four `RB_BodySetup` exports and the PhysicsAsset

```
$ cd "E:/Modding/JC3-Batmobile" && uv run python tmp/freebuff/scratch/inertia_bmak_probe1.py
======================================================================
export 169750  Batmobile_V3_Physics.RB_BodySetup  class RB_BodySetup  size 2698  offset 0xc1ddb82
tags 4 end 0x71c reason end
  PreCachedPhysDataVersion     ByteProperty       off=0x00cd at=0x0014 size=1 value=5
  (simple)                     NameProperty       off=0x00d0 at=0x0019 size=None value=Batmobile_Chassis
  (simple)                     ObjectNCRProperty  off=0x00ec at=0x0025 size=None value=158234
  AggGeom                      StructProperty     off=0x0060 at=0x003d size=1759 value=None
======================================================================
export 169751  Batmobile_V3_Physics.RB_BodySetup  class RB_BodySetup  size 214  offset 0xc1de60c
tags 4 end 0xcc reason end
  PreCachedPhysDataVersion     ByteProperty       off=0x00cd at=0x0014 size=1 value=5
  (simple)                     NameProperty       off=0x00d0 at=0x0019 size=None value=Batmobile_Rig_Weapons_Trans
  (simple)                     BoolProperty       off=0x00e0 at=0x0025 size=None value=True
  AggGeom                      StructProperty     off=0x0060 at=0x003d size=143 value=None
======================================================================
export 169748  Batmobile_V2.RB_BodySetup  class RB_BodySetup  size 43346  offset 0xc1cfb42
tags 3 end 0x6564 reason end
  PreCachedPhysDataVersion     ByteProperty       off=0x00cd at=0x0014 size=1 value=5
  (simple)                     BoolProperty       off=0x00e0 at=0x0019 size=None value=True
  AggGeom                      StructProperty     off=0x0060 at=0x0031 size=25907 value=None
======================================================================
export 169749  Batmobile_V2_Collision_Pursuite.RB_BodySetup  class RB_BodySetup  size 14062  offset 0xc1da494
tags 3 end 0x2084 reason end
  PreCachedPhysDataVersion     ByteProperty       off=0x00cd at=0x0014 size=1 value=5
  (simple)                     BoolProperty       off=0x00e0 at=0x0019 size=None value=True
  AggGeom                      StructProperty     off=0x0060 at=0x0031 size=8275 value=None
======================================================================
export 158266  Physics.Batmobile_V3_Physics  class PhysicsAsset  size 194  offset 0xc16a59b
tags 5 end 0xc0 reason eof
  (simple)                     ObjectNCRProperty  off=0x0064 at=0x0004 size=None value=158308
  BodySetup                    ArrayProperty      off=0x0084 at=0x001c size=12 value=None
  BoundsBodies                 ArrayProperty      off=0x00dc at=0x003c size=12 value=None
  Bounds                       ArrayProperty      off=0x00ec at=0x005c size=72 value=None
  ConstraintSetup              ArrayProperty      off=0x00fc at=0x00b8 size=8 value=None
```

### 2) Box-body `AggGeom` layout (2-u32 header, record tag at 0x08, extents at 0x5c = byte 92)

```
$ uv run --with numpy --with scipy python - <<'EOF'
import struct, sys
sys.path.insert(0,'Tools/scripts')
import upk_read as U
pkg=U.Package(r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\BmGame.upk")
for idx in (169750,169751):
    data=pkg.data(idx); tags,_e,_w=U.walk_tags(pkg,data)
    a=[t for t in tags if t.get('name')=='AggGeom'][0]
    b=data[a['at']:a['at']+a['size']]
    print('export',idx,'agg',len(b),'first words',[hex(struct.unpack_from('<I',b,o)[0]) for o in range(0,16,4)])
    print('  tag at 0x08: type',struct.unpack_from('<h',b,8)[0],'offset',struct.unpack_from('<H',b,10)[0],
          'name',pkg.names[struct.unpack_from('<i',b,12)[0]],'size',struct.unpack_from('<i',b,20)[0])
    print('  extent tags at', hex(8+20+64))
EOF
export 169750 agg 1759 first words ['0x0', '0x2', '0xa', '0x1333f']
  tag at 0x08: type 10 offset 0 name TM size 64
  extent tags at 0x5c
export 169751 agg 143 first words ['0x0', '0x1', '0xa', '0x1333f']
  tag at 0x08: type 10 offset 0 name TM size 64
  extent tags at 0x5c
```

(This is the layout probe that fixed the first version of the tool, which assumed a 16-byte header and found no box record. G3-01b's recorded "extent tag at byte 92" is what identified the error.)

### 3) Write the outputs

```
$ cd "E:/Modding/JC3-Batmobile" && uv run --with numpy --with scipy python Tools/scripts/grab_inertia.py --write
wrote INERTIA.md and INERTIA.json
bmak: exports 4, mass/inertia properties True, tensor-shaped triples 0
jc3: blocks 56, bodies 1651, boxes 107, box-oracle 0/107, hull-oracle 0/107
bias 111, com median 0.0156, median box ratio [1.275178, 1.287701, 1.276702]
write_exit=0
```

### 4) `--check` (final, passing)

```
$ uv run --with numpy --with scipy python Tools/scripts/grab_inertia.py --check
oracle jc3_box_formula_reproduced (reported, not a drift): ok=False {"hits_1pct": 0, "of": 107, "median_ratio": [1.275178, 1.287701, 1.276702]}
oracle jc3_hull_formula_reproduced (reported, not a drift): ok=False {"hits_1pct": 0, "of": 107, "median_ratio": [1.275178, 1.287701, 1.276702], "all_bodies_hits_1pct": 0}
OK: bmak tags no mass/inertia; jc3 blocks 56, boxes 107, box-oracle 0/107, bias 111, com median 0.0156
INERTIA.md/json current
check_exit=0
```

Both files re-derived byte-for-byte; the two failing oracles are the brief's own test and are printed explicitly, never suppressed.

### 5) Hull-accumulator cross-check (the bug this caught, and its fix)

The first version of `hull_props()` accumulated second moments about a reference point without the
reference↔centroid cross term, which produced **negative** diagonals on 17 of the donor's 40 hull
tensors. Negative inertia is impossible, so the accumulator — not the data — was wrong. After fixing
it, the hull tensor of every single-box body must equal the closed-form box formula:

```
$ uv run --with numpy --with scipy python - <<'EOF'
import json, numpy as np
d=json.load(open('Research/BatmobileGrab/INERTIA.json'))
rows=d['jc3']['box_rows']
dif=[abs(np.array(r['I_hull'])-np.array(r['box'])).max()/max(r['box']) for r in rows]
print('box rows',len(rows),'max |I_hull-box|/box over box bodies: %.2e  median %.2e'%(max(dif),float(np.median(dif))))
b=d['jc3']['donor_blocks'][0]
print('donor chassis block:',b['mass'],b['diag'],'hull',b['I_hull'],'box',b['box'])
print('oracles:',{k:v['ok'] for k,v in d['oracles'].items()})
print('donor link counts:',d['jc3']['fleet']['donor_polytopes'],d['jc3']['fleet']['donor_polytopes_linked'],d['jc3']['fleet']['donor_blocks_from_shapes'],d['jc3']['fleet']['donor_blocks_linked'])
print('hull formula all bodies:',d['jc3']['box_oracle']['hull_formula_all_bodies'])
print('median hull ratio all:',d['jc3']['box_oracle']['median_ratio_hull_all'])
EOF
box rows 107 max |I_hull-box|/box over box bodies: 1.85e-04  median 0.00e+00
donor chassis block: 800.0 [973.5625, 1128.3125, 396.8125] hull [820.360189885, 980.79545377, 304.427564814] box [1000.191625887, 1192.077237234, 387.745470344]
oracles: {'bmak_every_box_record_located': True, 'bmak_no_mass_or_inertia_property_serialized': True, 'bmak_no_tensor_shaped_triple_in_aggeom': True, 'jc3_bias_is_111': True, 'jc3_block_is_48_bytes_zero_header': True, 'jc3_box_bodies_exist': True, 'jc3_box_formula_reproduced': False, 'jc3_centre_of_mass_matches_hull_centroid': True, 'jc3_every_polytope_resolves_to_a_mass_block': True, 'jc3_hull_formula_reproduced': False, 'jc3_hull_tensors_are_positive_definite': True, 'jc3_hull_tensor_reproduces_box_formula_on_boxes': True}
donor link counts: 54 54 54 40
hull formula all bodies: {'1%': 0, '2%': 1, '5%': 14, '25%': 166}
median hull ratio all: [1.54379, 1.535634, 1.609253]
```

1.85e-4 on 107 box bodies (median exactly 0) is the independent proof that the hull accumulator is
right; the ones that fail the *stored-value* oracle are therefore the stored values' problem, not the
arithmetic's.

## Oracles and their status

| oracle | ok | meaning |
|---|---|---|
| `bmak_no_mass_or_inertia_property_serialized` | pass | no mass/inertia property name in any of the four body setups or the PhysicsAsset |
| `bmak_every_box_record_located` | pass | 2 and 1 `TM` records found for header counts 2 and 1 |
| `bmak_no_tensor_shaped_triple_in_aggeom` | pass | 0 hits in 9006 aligned triples across 36084 payload bytes |
| `jc3_block_is_48_bytes_zero_header` | pass | 56/56 blocks, extent 48, header zero |
| `jc3_every_polytope_resolves_to_a_mass_block` | pass | 40 donor body-level hulls all linked |
| `jc3_bias_is_111` | pass | only 111 puts the COM on the centroid; 110/112 a factor of two out |
| `jc3_centre_of_mass_matches_hull_centroid` | pass | median 0.0156, 91.9 % within 10 % |
| `jc3_box_bodies_exist` | pass | 107 of 1651 |
| `jc3_hull_tensors_are_positive_definite` | pass | 0 non-positive of 1651 |
| `jc3_hull_tensor_reproduces_box_formula_on_boxes` | pass | max rel diff 1.85e-4 on 107 boxes |
| `jc3_box_formula_reproduced` | **fail (the finding)** | 0/107 at 1 %; median ratio 1.275/1.288/1.277 |
| `jc3_hull_formula_reproduced` | **fail (the finding)** | 0/107 at 1 % (and 0/1651 at 1 %) |

## What this means for the Batmobile (no values invented)

- The Batmobile's **mass** is not in its cooked physics. The body setups serialize geometry only. Where a
  mass does exist on the BmAK side is a *vehicle-sim* field, `SVehicle.ChassisMass`, decoded earlier at
  `Research/BatmobileGrab/CLASS_DEFAULTS.md:434` as the class default `210.0` — a class default, not a
  per-vehicle authored value, and not this task's format. I did not evaluate any inertia against it.
- The Batmobile's **inertia tensor** is UNKNOWN, and now for a *located* reason: the format that would
  carry it (UE3 `AggGeom`) does not, and the format that does carry one (JC3 `hknpShapeMassProperties`)
  stores values that are not the collision shape's box or hull tensor. Substituting the JC3 chassis
  diagonal (973.56/1128.31/396.81 kg·m² at 800 kg) for the Batmobile would be a guess of a different
  body's tensor, so it is not done here.

## UNKNOWNs, with what was tried and why they stand

1. **The Batmobile's mass.** Tried: full tag walk of all four `RB_BodySetup` exports and the PhysicsAsset
   (§1 output); a name-table search for `Mass`/`MassScale`/`Inertia` across the project's SDK dump (41
   classes — it has no `RB_BodySetup` entry, so the class layout, where a `MassScale` would sit, is not
   available either). What would settle it: the `PrimitiveComponent`/body-instance field layout for the
   Batmobile's own component, or a decoded per-vehicle value in the vehicle-sim module.
2. **The Batmobile's inertia tensor.** Tried: scale-free scan of every aligned f32 triple in all four
   `AggGeom` payloads against both the decoded boxes' and the decoded convex hulls' moment tensors (0
   hits). There is no tensor-shaped data to interpret, so no formula can be evaluated. What would settle
   it: a decoded mass plus the engine's inertia mode for the body (computed-from-shape vs authored), neither
   of which is in the files read here.
3. **The absolute semantics of the JC3 stored diagonal.** Tried: the brief's box formula (0/107 at 1 %),
   the exact hull tensor at the stored mass (0/1651 at 1 %), the centroid vs frame-origin parallel-axis
   models, and a scale-free scan for a plain-float tensor elsewhere in the donor (8 coincidental hits, all
   in `hkGeometry`). The residual is a single near-uniform factor (1.2752/1.2877/1.2767, spread 0.0125),
   so the tensor is self-consistent but authored from another geometry. What would settle it: the render
   mesh of the same part, whose tensor at the stored mass would show whether the factor is a mass or an
   extent difference.
4. **Payload group 3 (`+0x20..+0x27`).** The raw words are recorded for all 56 blocks; its exponent lane
   decodes its mantissas to ~1e-36 ("no products"). Whether it is products of inertia, a principal axis or
   a tag is not decoded.
5. **The packing is derived, not documented.** `value = mantissa * 2**(floor(w/128) − 111)` is measured
   (bias pinned by the COM oracle to better than one octave), but no Havok header in this tree names the
   layout, so the bit-level reading of the exponent lane is derived.
6. **Two quantised lanes on tiny hulls.** On sub-centimetre plates the stored diagonal's 16-bit mantissas
   carry no resolution (ratios of 8232 and 5225 appear), so those rows cannot test anything; the oracle is
   reported on all bodies and the effect is stated, not filtered away.
7. **One fleet file does not decode:** `town_01_ai_junction.physicsc` raises "no hknpPhysicsSystemData"
   (same file the earlier passes reported), so fleet coverage is 40 of 41 files.

## Compliance

- No game launched, attached to or read; no write under `E:/Games` or `D:/Games`; no build, no install, no
  translation file written; no git commit or push; no network use.
- No existing `Research/` or `Tools/` file was edited: this pass adds `grab_inertia.py`, `INERTIA.md` and
  `INERTIA.json` (the JC3-only earlier outputs `jc3_inertia2.py` / `INERTIA2.*` are left untouched and their
  numbers reproduce here: 107 boxes, 0/107, com median 0.0156, bias 111).
- Test ban respected: nothing was run in or against the game.
