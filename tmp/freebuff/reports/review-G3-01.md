# Review - G3-01 (drivable Batmobile collision primitives)

VERDICT: **minor issues**. Every value I re-read matches the bytes, and `--check` passes. The
problems are labelling: several field *names* that come from a class layout are printed as
"decoded", and the "value (decoded)" column carries values that reach the instance only through
a CDO-inheritance ladder the note itself says is not byte-proven.

I wrote no research output; `grab_collision.py --write` was not run.

## Check output (verbatim)

```
$ cd "E:/Modding/JustCause3/JC3-Batmobile" && PYTHONIOENCODING=utf-8 uv run --with numpy --with pillow python Tools/scripts/grab_collision.py --check
check ok: E:\Modding\JustCause3\JC3-Batmobile\Research\BatmobileGrab\COLLISION.json E:\Modding\JustCause3\JC3-Batmobile\Research\BatmobileGrab\COLLISION.md
CHECK_EXIT=0
```

Run exactly as the card's header prescribes (`python Tools/scripts/grab_collision.py --check`,
without `--with pillow`) it fails before doing any work:

```
ModuleNotFoundError: No module named 'PIL'
  at Tools/scripts/bat_assemble.py:48 -> import tex2ddsc -> from PIL import Image
CHECK_EXIT=1
```

That is a dependency omission, not drift: the script needs `pillow` for a module it imports only
to reuse the JC3 transform.

## Spot-checks (5 values, re-read from the raw package bytes)

Method: `upk_read.Package(path).data(export)`, the script's own tag walk to locate the tag, then
the payload decoded independently with `struct` at the tag's byte range.

| # | value in COLLISION.md | source | re-read | match |
|---|---|---|---|---|
| 1 | `FrontCollisionCylinder` instance 277, offset 364 `PerInstanceRandom` = 0.6867886 | Playable 277, tag at byte 28 | Float payload `60d12f3f` = 0.6867885589599609 | **yes** |
| 2 | `FrontCollisionCylinder` base template 142597, offset 400 `Translation` = [100.0, 0.0, 0.0] | BmGame 142597, tag at byte 56 | Vector payload `0000c842 00000000 00000000` = [100.0, 0.0, 0.0] | **yes** |
| 3 | `RearCollisionCylinder` base template 142598, offset 400 `Translation` = [-200.0, 0.0, 0.0] | BmGame 142598, tag at byte 56 | Vector payload `000048c3 …` = [-200.0, 0.0, 0.0] | **yes** |
| 4 | `BatmanCollisionMeshBattleMode0` base template 176111, offset 644 -> export 175973 `Batmobile_V2_Mesh.Batmobile_V2` (StaticMesh) | BmGame 176111, tag at byte 16 | ObjectNCR payload `65af0200` = 175973, `object_class` = `StaticMesh` | **yes** |
| 5 | `SVehicleMesh` instance 5289, offset 640 -> export 5284 `Batmobile_V2_Mesh.Batmobile_V2` (SkeletalMesh) | Playable 5289, tag at byte 8 | ObjectNCR payload `a4140000` = 5284, `object_class` = `SkeletalMesh` | **yes** |

Two extra checks while there:

- 142597 offsets 540 and 544: payload `00009c42` = 78.0 and `00002f43` = 175.0 - the two floats the
  note keeps UNKNOWN are present exactly as written.
- 5289 byte accounting: walk ends at 174 of 258, tail 84 B, and the tail's first 76 B equal the
  `XRayMaterials` payload with the remaining 8 B zero - the note's `svehicle_tail_check` claim holds.
- The UNKNOWN "Pawn.CylinderComponent (offset 900) is the slot it fills (decoded from the
  archetype)": archetype 5281 has a type-16 tag at offset 0x384 whose payload is `14010000` = 276,
  i.e. `object_class` = `CylinderComponent`. Claim verified.

## Issues

1. **`COLLISION.md` - field-name labels say "decoded" for layout-derived names.**
   Examples: `Translation (decoded)` (offset 400), `PerInstanceRandom (decoded)` (364),
   `Rotation (decoded)` (412), `LightingChannels (decoded)` (512). The tag at those offsets is
   unnamed in the bytes (type 11/4/12/10 with no `FName`); the text comes from
   `BMSDK_OFFSETS.json` via `name_offset()` -> `layout_at()`, which returns
   `("...", "decoded", "BMSDK_OFFSETS.json Pawn.Translation at 0x190")`.
   Why it matters: the page's own rule says decoded = "read from bytes (export, offset, tag type,
   payload)". A name looked up in an external layout table is exactly the `derived` case the
   script already uses for `PrimitiveComponent` lookups. The evidence is fine (the reason string
   names the class and offset), the label is one grade too strong. Contrast offset 316
   `ReplacementPrimitive`, where the tag really does carry the name - that one is correctly
   decoded.

2. **`COLLISION.md` - "value (decoded)" for values inherited through the CDO ladder.**
   `FrontCollisionCylinder` translation [100, 0, 0] is taken from `base_template` 142597 because
   the instance (277) and the Startup template (82147) carry no offset-400 tag. The note discloses
   that the instance-to-template link is by component name and not decoded, and calls the ladder
   itself derived - but the table column and the bullet ("Translation (offset 400, decoded from
   `base_template`)") both say decoded. A reader can take the value as belonging to the instance.
   Suggested wording: "decoded on `base_template`; applicability to this instance is derived from
   the CDO inheritance rule (not byte-proven)".

3. **`COLLISION.md` - the shielded claim about which mesh a mode uses.**
   The note records (correctly, verified) BattleMode0 -> `Batmobile_V2` (the render mesh) and
   PursuitMode0 -> `Batmobile_V2_Collision_Pursuite` (the collision mesh), but never comments on
   the inversion. The values are decoded; the sentence a reader will infer ("battle mode collides
   with the body mesh") is not stated or tested. Either state it as an observation with its
   consequence, or add one line that the pairing is unexplained.

4. **`grab_collision.py` header - the documented command is incomplete.**
   The docstring and the card's usage line omit `--with pillow`; following them gives the
   `ModuleNotFoundError` above. The check itself is fine.

5. **No issue found in the values.** Not one of the decoded numbers I re-read disagrees with the
   bytes, the byte accounting I could test (277 = 38/38, 5392 = 38 of 59 + 21-byte tail, 5289 =
   174 of 258, tail = XRayMaterials copy) is correct, and the JSON and the markdown are the same
   document (`--check` compares both).

## Resolvable UNKNOWNs

- **Cylinder radius vs height (offsets 540/544, values 78.0 / 175.0).** Not resolvable from the
  archetype or the component templates (BMSDK has no `CylinderComponent` layout, and I confirmed
  there is no `CollisionCylinder` template under `Default__RVehicleBatmobile`/`...Base` in
  Startup/BmGame). It could be narrowed by decoding the shipped `CylinderComponent` UClass
  property list (two float properties, names only) - but which name is 540 and which is 544 then
  rests on declaration order, i.e. an inference, so the card's refusal to name them is defensible
  and it should stay UNKNOWN until an offset-carrying layout exists.
- **BatmanVsBatmobileCollisionMode (5895).** The note calls it "not serialised". I re-checked
  offset 0x1707 in five layers (archetype 5281, Startup CDO 7530, BmGame base CDO 10923, base
  templates 175716 and 176111): absent in all. The UNKNOWN stands as written; nothing more can be
  resolved without the selector's real offset.
- **RBChannel (524) / RBCollideWithChannels (516).** Also absent from those five layers, matching
  the note. Not resolvable from the walked objects; the values are not in these bytes.
- **Closed during the review:** I walked the Startup templates 82147/82148 (46 B each). Both hold
  only `ReplacementPrimitive` (offset 316) and a float at offset 364 (`3f7ff200` = 0.99977 and
  `3f19e734` = 0.60117); **neither carries offset 400**. So for `FrontCollisionCylinder` and
  `RearCollisionCylinder` the base template is the only layer with a `Translation`, issue 2 stays
  a wording problem (the value itself is right for the ladder as defined), and no value in the
  note is contradicted by this check.
