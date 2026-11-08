# Review - G3-01b (drivable Batmobile collision geometry)

VERDICT: **minor issues**. Every decoded value I re-read reproduces from the bytes, the plane
oracle holds under independent arithmetic, and `--check` passes. The problems are labels and one
heading: meanings attached to header words are hypotheses printed as decoded, box centres are
inherited by a rule from another asset and labelled decoded, and the mode attribution in the
section headings is asserted rather than labelled.

I wrote no research output; `grab_collision_geom.py --write` was not run.

## Check output (verbatim)

```
$ cd "E:/Modding/JC3-Batmobile" && PYTHONIOENCODING=utf-8 uv run --with numpy --with pillow python Tools/scripts/grab_collision_geom.py --check
COLLISION_GEOM.md/json current
CHECK_EXIT=0
```

The check compares both output files against a fresh derivation (byte-for-byte text compare) and
prints "regenerate with --write" + exit 1 on drift. It does not re-run any oracle; that is fine
because the oracles are computed inside `build()` and therefore baked into the compared JSON.

## Spot-checks (5 values, re-read from raw package bytes)

Method: `upk_read.Package("BmGame.upk").data(export)`, `AggGeom` payload located by the tag, then
all arithmetic done independently of the script (my own `struct` reads and my own plane test).

| # | value in COLLISION_GEOM.md | source | re-read | match |
|---|---|---|---|---|
| 1 | `RB_BodySetup` 169748: AggGeom **25907** bytes, header words **[0, 0, 0, 43]** | BmGame 169748 | AggGeom 25907 B; u32 at 0/4/8/12 = 0, 0, 0, 43 | **yes** |
| 2 | 169748 convex element 0: **10** vertices, **16** triangles, **7** planes, all triangles on a stored plane | BmGame 169748, AggGeom +16 | nV 10, nA 9, nI 48 (=16 tris), 7 planes; my own oracle: **0 unmatched**, all 7 planes used | **yes** |
| 3 | `RB_BodySetup` 169749: AggGeom **8275** bytes, header **[0, 0, 0, 13]**, convex **8** vertices / **12** triangles / **6** planes, 0 unmatched | BmGame 169749 | 8275 B, header 0,0,0,13; nV 8, nI 36 (=12), 6 planes; my oracle 0 unmatched, 6/6 used | **yes** |
| 4 | chassis body 169750 box 0 extents **[690.305, 374.536, 207.5]** cm, centre **[9.0, 0.0, 106.75]** cm | BmGame 169750, AggGeom byte 92 | tagged floats `85932c44 / 9e44bb43 / 00804f43` = 690.3050 / 374.5360 / 207.5000; 12 B before = 9.0 / 0.0 / 106.75 | **yes** |
| 5 | constraint 171462 offsets 84/92/100 = `Batmobile_Rig_Weapons_Trans`, `Batmobile_Rig_Weapons_Trans`, `Batmobile_Chassis`; 144/156/168 vectors as written | BmGame 171462 | NameProperty at 0x54/0x5c/0x64 and VectorProperty at 0x90/0x9c/0xa8 with exactly those values | **yes** |

Also checked while there:

- PhysicsAsset 158266 arrays: `BodySetup` count 2 -> [169750, 169751], `ConstraintSetup` count 1 ->
  [171462], `BoundsBodies` count 2 -> [0, 1]. Matches the note.
- StaticMesh 175973 -> ref path `Batmobile_V2.RB_BodySetup`; 175974 -> `Batmobile_V2_Collision_Pursuite.RB_BodySetup`
  (tag at 0x11c). The note's bodies are named by those paths, so the mesh→BodySetup link is real.
- `Bounds` array: 72 B payload = count 2 + 68 B of data, i.e. 34 B per element. The note's refusal
  to decode it is justified - 34 B is not a whole number of 4-byte floats times a sane record, so
  no layout is proven.

## Issues

1. **`COLLISION_GEOM.md` - header-word meanings inside a "decoded" label.**
   Example: `header words [0, 0, 0, 43] (decoded (words 0..3 of the AggGeom payload); word 0 = 0
   sphere count, word 3 = convex count when it is small)`. The four words are decoded; "sphere
   count" and "convex count" are interpretations. The script's own data undermines the second: the
   box bodies 169750/169751 have header word 3 = **78655**, so the field is not always a count,
   and the code silently switches to the box path. For 169748 the note then says 43 elements while
   only element 0 is decoded, so "43" is an unverified count. Suggested label: words decoded,
   meanings **hypothesis** (supported only by element 0 for the convex case).

2. **`COLLISION_GEOM.md` - box centres labelled decoded.**
   Each box row ends with `centre: 12 bytes before the tag stream, grab_physics rule, rotation not
   decoded`, inside a field introduced as "decoded". The centre rule is imported from
   `grab_physics.py` and its own UNKNOWN list says it is "proven only on the wreck". So the centre
   is **derived** by an unproven rule, not decoded. The values reproduce, the label is too strong.

3. **Headings assert the mode attribution without a label.**
   `## Battle-mode mesh: RB_BodySetup 169748 (Batmobile_V2)` and the pursuit equivalent present as
   fact the chain collision-component name -> StaticMesh -> BodySetup. In G3-01 that chain is
   explicitly "by component name; the walk does not decode the link", and the pairing is odd:
   BattleMode0 points at the **render** mesh `Batmobile_V2` and PursuitMode0 at
   `Batmobile_V2_Collision_Pursuite` (I re-verified both refs in the previous review). Either label
   the heading (derived from component names) or add the one-line caveat.

4. **`RB_BodySetup 169748 (Batmobile_V2)` / "`Batmobile_V2 battle`" reads like an object name.**
   The export's own name is `RB_BodySetup` (its ref path is `Batmobile_V2.RB_BodySetup`); the
   string in backticks is the script's `label` argument. A reader can take it for a decoded name.

5. **The chassis/body oracle is weaker than the wording suggests** (not an error, but worth
   knowing before reuse). It compares *sorted* spans, so it cannot test axes, and a 0.25 m window on
   a 3.5-3.7 m span is ~7 %. It does what the note claims - it rules out half-lengths (which would
   give ~13.8 m) - and the note says axes are unproven.

## Resolvable UNKNOWNs

- **AggGeom elements 1..N ("the element chain does not close").** Resolvable, with the oracle
  already in the script: after element 0 ends, scan forward for a u32 `n` with 3 <= n <= 64 whose
  `n` FVectors are finite and whose following blocks end on a plane table that satisfies the same
  triangle-plane test element 0 passes. A candidate that closes (`next element offset` advancing by
  4 + 12n + ...) is provable by byte accounting; a candidate that does not is discarded. I did not
  run this, but the test is the script's own oracle applied at a candidate boundary.
- **Block A ("values are vertex components, semantic UNKNOWN").** I tested the strongest competing
  reading - that the 16-byte records are planes - in both orders: treat each record as
  `(W, nx, ny, nz)` and as `(nx, ny, nz, W)`, then check every triangle plane against the 9
  (169748) and 6 (169749) records at the script's own tolerances. Result: **0/16 and 0/12 matched
  in both orderings**. So block A is *not* a plane table, the note's UNKNOWN is corroborated rather
  than resolvable this way, and the "vertex components" reading remains a hypothesis (the records'
  3-element norms are 150-432, not 1, so they are not unit normals either).
- **`Bounds` array (72 B, count 2).** Not resolvable from these bytes with the readers at hand:
  34 B per element does not fit an obvious float record, and there is no layout entry. A stride
  scan would only produce a guess. The note is right to leave it UNKNOWN.
- **Box rotations.** The centres are proven by an imported rule; the rotations are not in the
  decoded bytes at all (no tag carries them), so this stays UNKNOWN unless the chassis component's
  transform is decoded elsewhere.
