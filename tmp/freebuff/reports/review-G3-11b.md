# Review — G3-11b (ledger re-check with the right decoders)

Reviewer: independent (did not write the card). Reviewed: `tmp/freebuff/reports/G3-11b.md`,
`Working/Translation/LEDGER_AUDIT2.md` (149 lines), `LEDGER_AUDIT2.json` (148,703 B),
`Tools/scripts/ledger_audit2.py` (1,199 lines). Re-read from the raw sources with my own code:
the built `sportsmuscle.physicsc`, the built `.epe` export, the built parts and lights modules,
`T_ROWS.jsonl`, `LEDGER_AUDIT.json`, and the unpacked donor tree under
`E:/Modding/_shared/gamedata/JC3grab/b13b/`. Nothing was written except this file; no game launched or
attached; no git operations.

## VERDICT: **minor issues**

The measurements are sound. I reproduced every number I tested — about a dozen, spanning both
decoders and the ledger's "before" side — exactly, to the byte and to the last digit. The two
re-grades rest on real oracles I re-ran. `--check` passes and the `.md` on disk is the tool's own
render.

The issues are about **frame and labels**, not arithmetic:

1. **Three `REFUTED` verdicts compare donor-frame numbers with the built file.** The donor lights
   module is on disk; its 21 rows and its 16×`2.0/10.0` + 5×`30.0/40.0` histogram are *exactly*
   what `T-LG6` and `T-LG1` state. The ledger is right about the donor and the build changed it —
   "REFUTED" says the ledger is wrong. (I-1)
2. **"12,537 packed vertices" is the tree-node array**, not a vertex array — the same number the
   card also reports as "12,537 tree nodes", and `2 × 6,269 − 1`. (I-2)
3. Smaller: a 42-vs-53 count in the narrative, "the translation lane" against its own UNKNOWN 5,
   "243 named objects" for 243 distinct names over 328 objects, and a 6+66 partition that hides
   the `T-PA3` overlap. (I-3…I-6)

No decoded value is wrong; no verdict is unsupported by the bytes it quotes. One class of verdict
is mislabelled in a way that would mislead the ledger's reader.

## 1. Check output (verbatim)

```
$ uv run --with numpy python Tools/scripts/ledger_audit2.py --check
OK 72 in-scope rows (19 changed, 53 unchanged) re-derived from the bytes
after: {'TRANSLATED': 42, 'GUESSED': 0, 'NOT TRANSLATED': 25, 'REFUTED': 5, 'UNVERIFIABLE': 0}
oracles: {'bm_colmesh.selftest': 'PASS', 'bm_colhull.selftest': 'PASS 54/54'}
CHECK_RC=0
```

I also ran the oracle directly rather than through the card: `bm_colhull.selftest(pf)` returns
`{'donor_hulls_reencoded': 54}` on the built file — 54/54, independently confirmed.

## 2. Spot-checks (value, source, match)

| # | value the card labels decoded/measured | my read | source | match |
|---|---|---|---|---|
| 1 | built `.physicsc` 902,384 B, sha256 `eda17906c1f81c7b…`; **430 objects, 16 classes** | 902,384 B, `sha256[:16] = eda17906c1f81c7b`, 430 objects, 16 classes | `Builds/bm-RC1/…/batmobile/sportsmuscle.physicsc`, `hashlib` + `jc3hkx.Packfile` | **yes** |
| 2 | body table **62 entries** (0..61): 40 hulls, 18 extern meshes, 2 dynamic + 2 static compounds; 54 hull objects | 62 entries, `index_max 61`; class census `{Polytope: 40, ExternMeshShape: 18, StaticCompoundShape: 2, DynamicCompoundShape: 2}`; 54 `hknpConvexPolytopeShape` objects | same file: `global_` entries at `hknpPhysicsSystemData + 0x2d20 + 0x60·i` | **yes** |
| 3 | body 0 hull: **96 vertices**, bounds `[[-1.7447, 0.0751, -3.4277], [1.7536, 2.3582, 3.6093]]` | 96 vertices, `min [-1.7447, 0.0751, -3.4277]`, `max [1.7536, 2.3582, 3.6093]`, convex ok | `jc3hkx.decode_polytope(pf, body0)` | **yes** |
| 4 | LOD2 **11,197 vertices / 6,269 triangles**, max protrusion **2.1e-08 m** | 11,197 / 6,269; hull own support 2.18e-07, mesh max 2.38e-07 → protrusion **2.1e-08 m** | `sportsmuscle_body_lod2.rbm` via `bm_colmesh.load_body`; my own plane-by-plane max, not the card's loop | **yes** |
| 5 | dynamic trees: **19/20 exact**, worst **0.01593 m** at `0xd3c80` | 20 trees; worst 0.01593; the only non-refitting compound is `0xd3c80` | `bm_colmesh.dyn_tree_refit` + my own float compare of the stored blob | **yes** |
| 6 | `T-CO1`: **44 B** differ from the grab extract, first at `+0x3590`, inside body entries **[22, 23, 36, 37]** at in-entry offsets `0x30–0x3b`, **0** above the table; `hknpPhysicsSystemData` **identical** to test-091 | 44 differing bytes, first **13712** (`0x3590`), entries `[22, 23, 36, 37]`, offsets `{0x30,0x31,0x32,0x34..0x3b}`, `above_table 0`; built vs test-091: **identical, 20,912 B, 0 diffs** | both `hknpPhysicsSystemData` blobs, compared by me | **yes** |
| 7 | `.epe`: **467** object elements, **466** classed, **46** classes; `SVehicleLight` **28**, `CInteractionGraphEntry` **29**, `…Exit` **26**, `CPartProp` **6**, `SWeaponPoint` **9**, `CInteractionTrigger` **7**, `CInteractionGraphPointNode` **8** | exactly those counts, from each object's own `_class` value | `tmp/g3_11b/epe.xml` (the card's `ConvertProperty --e` export of the built `.epe`), parsed with `ElementTree` | **yes** |
| 8 | lights module **18 rows**; histogram `2.0/10.0 ×13`, `30.0/40.0 ×4`, `10.0/60.0 ×1`; **12** presets resolve; 28 `SVehicleLight`, **12 referenced, 16 unreferenced** (list quoted in the md) | 18 rows, same histogram, 12 nonzero presets; referenced 12; unreferenced 16 and the list matches name for name | built lights `.vmodc` via `jc3adf.walk`, names resolved through the `.epe`'s `name_hash & 0xFFFFFFFF` | **yes** |
| 9 | parts module: **61** parts, **38** with `has_world_collision_shape=1`, **23** with `world_collision_body_id=-1`, 19 with raycast −1; body `0/42`, door_f_l `1/43`, engine `7/47`, wheels `-1` and `22/23/36/37` | all identical, including every named id | built parts `.vmodc` via `bm_parts.decode_parts` | **yes** |
| 10 | `T-CO2`: no hull has the 3.679 m axis; built maximum **7.037 m** | 54 hulls, max axis **7.037**, 0 within 0.01 of 3.679 | `jc3hkx.decode_polytope` over all polytopes | **yes** |
| 11 | `T-L5` refuted: `Front_Secondary_Head` **is** referenced, `lights[11]` preset **3189390601**, HeadLight, range 10, angle 60 | built row 11: HeadLight, preset 3189390601, 10.0/60.0; `Front_Secondary_Head`'s `name_hash & 0xFFFFFFFF` = **3189390601** | built module + `.epe` hash map | **yes** |
| 12 | "before" side of the changed rows (e.g. `T-L5` TRANSLATED/string, `T-CO3` TRANSLATED/value, `T-LG1` NOT TRANSLATED/member, `T-P3` NOT TRANSLATED/none) | identical to `LEDGER_AUDIT.json` row for row | `Working/Translation/LEDGER_AUDIT.json` | **yes** |
| 13 | scope: **72** rows (6 collision + 66 `.epe`) | applying the card's own rule to `T_ROWS.jsonl`: 6 collision ids, 67 `.epe` hits, **1 overlap (`T-PA3`)** → 72 unique | `T_ROWS.jsonl` | **yes** (see I-6) |

Spot-check 8 needed care: `name_hash` is a **signed decimal** in the XML (`Dash_Light` = `-1531768864`).
My first pass masked nothing and got zero resolutions — that was my bug, not the card's; the card's
`u32()` (`int(x) & 0xFFFFFFFF` → `2763198432`) is correct and resolves 12/16 exactly as reported.

## 3. Issues

### I-1 · Three `REFUTED` verdicts use the wrong frame — the ledger's numbers are the donor's, and they are exact

The card's headline for the lights rows is "**Light counts the ledger states are wrong in the
build**: 18 module rows (not 21), 28 `SVehicleLight` (22 in `_Default` + 6 in `Sport_Muscle`), …".
But the row's own text is a statement about the **donor** module, and the donor module is on disk:

`E:/Modding/_shared/gamedata/JC3grab/b13b/unpacked/…/modules/generated/v0300_car_kensington_sportsmuscle_lights.vmodc`

read with `jc3adf.walk`:

| quantity | donor (b13b, vanilla) | built (bm-RC1) | ledger says |
|---|---:|---:|---|
| rows | **21** | 18 | 21 (`T-LG1`) |
| `2.0 / 10.0` rows | **16** | 13 | 16 (`T-LG6`) |
| `30.0 / 40.0` rows | **5** | 4 | 5 (`T-LG6`) |
| `10.0 / 60.0` rows | 0 | 1 | — |

The ledger's `T-LG6` value — *"30 / 40 on the 5 spots; 2 / 10 on 16"* — is **exactly true of the
donor**, down to both counts, and 5 + 16 = 21. Marking it `REFUTED` asserts the ledger is false;
what the bytes show is that the **build** changed the module. The same applies to `T-LG1`'s
"21 entries" (true of the donor) and to `T-LG2`'s object count, where the built `.epe`'s 28
`SVehicleLight` objects include six the build added (the `*_arch_light`, `boot_light_light`,
`headlight_battle_*_light` family that `T-18` describes) — the card's own UNKNOWN 2 concedes the
frame is unsettled.

The build's relation to the donor is fully recoverable, which makes the frame question cheap to
settle. Every built row's preset maps to a donor row:

```
built 0..10  <- donor 2, 7, 8, 11, 12, 13, 14, 17, 18, 19, 20
built 11     <- new (Front_Secondary_Head, 3189390601)
built 12..17 <- no preset (preset_id 0, the six T-18 custom rows)
donor rows dropped: 0, 1, 3, 4, 5, 6, 9, 10, 15, 16 (tail, signals, reverse, front-primary)
```

i.e. the build is a filtered, reordered 21→18 subset, plus one new light and six custom rows. That
is the finding worth having in the ledger; `REFUTED` hides it and, worse, tells later cards the
`T-LG1`/`T-LG6` numbers were wrong when they were right about the file they describe.
Recommendation: keep the measurements, change the verdict wording to "build differs from donor"
(or add a `frame` column: donor / build), and cite the donor module path.

Note the `T-L5` refutation is *not* affected — `Front_Secondary_Head` really is referenced in the
built module (spot-check 11), and the row's own text says "exists in the graph and is
**unreferenced**", which is false of the built file. That one stands (with the same
donor/build caveat, since the donor's rows 0–20 have 21 nonzero presets and `Front_Secondary_Head`
appears in neither).

### I-2 · "12,537 packed vertices (stride 6)" is the tree-node array

The report (D3 table and md "What the decoders read") says:

> part 0 extern mesh: 12537 packed vertices (stride 6), geometry A 11197 vertices / 6269 triangles,
> tree 12537 nodes -> 6269 leaves

Those two 12,537s are the **same array**, and it is the node array:

- `pf.array(data + 0x10)["size"]` = **12,537**, pointer `631952`;
- `u32` at `db + 0x18` (the node count the card itself reads) = **12,537**;
- `2 × 6,269 − 1` = **12,537** — a full binary tree over the 6,269 leaves;
- the data blob is 75,552 B, and `12,537 × 6 = 75,222` plus the 0x60 header is the blob.

So the extern mesh's packed vertex array was **not** decoded; `jc3hkx.mesh_geometry()`'s field
name `vertex_count` (it returns `array(data+0x10)["size"]`) is a pre-existing misnomer that the
card inherited. This matters twice: the md/report present one measurement as two independent facts,
and the `hknpExternMeshShapeData` re-grade cites "count/AABB exact", where the count is the node
count, not a vertex count. The card's own UNKNOWN 3 (vertex dequantisation unpinned) is consistent
with the correction, so nothing downstream changes — but the label must be fixed, and the
`jc3hkx.mesh_geometry` misnomer recorded.

### I-3 · 42 vs 53 in the narrative

The report says "the other 53 in-scope rows keep their verdict; **42 of them** now carry
`.physicsc`/`.epe` evidence". The md says "53 rows keep their G3-11 verdict and evidence strength;
**53 of them** have new evidence … *(upgraded)*" and marks all 53 that way. 42 is the post-audit
`TRANSLATED` total, not an "upgraded" count. One of the two numbers is wrong; `--check` cannot catch
it because it re-derives the md, not the report's prose.

### I-4 · "The translation lane" contradicts the card's own UNKNOWN 5

Report §4: "all inside body entries 22, 23, 36, 37 at byte offsets 0x30–0x3b (**the translation
lane**)". UNKNOWN 5 says the 96-byte entries are "compared byte for byte … but not decoded field by
field, so this audit can say 'these 44 bytes moved' but not 'this field is the station'". Both cannot
stand. The parenthetical is supportable — `jc3hkx.stations` documents "position at +0x30" and that
is the project's decoded body-entry layout — but then it must cite that layout and UNKNOWN 5 must be
narrowed to "the meanings of the *other* fields in the changed lane are not decoded".

Related: the differing offset set is **not** contiguous — it is `{0x30, 0x31, 0x32, 0x34, …, 0x3b}`
(0x33 is unchanged). "0x30–0x3b" reads as a range; the md's exact list is correct and the report's
range is the loose version.

### I-5 · "243 named objects" is 243 distinct name values

`epe_facts` fills `names[nm] = cl` keyed by each object's `name` *value*, so `len(names) = 243`
distinct names — while **328** objects carry a `name` value and **96** object elements carry a
`name=` attribute. "243 named objects" (report §4.5, md) reads as 243 objects with names. Say
"243 distinct `name` values over 328 objects".

### I-6 · The 6 + 66 partition hides an overlap

"The card is 72 in-scope rows (6 collision/physics, 66 `.epe`)" is right in total but only because
`T-PA3` is counted on the collision side: the `.epe` rule (`dispo == epe`) also matches `T-PA3`, so
the raw split is 6 + 67 with one shared id. State the overlap (as the script's `COLLISION_IDS`
enumeration implies) so a later card does not read 66 as "epe rows that are not collision rows" and
double-count.

### I-7 · Minor wording

- The report's D3 line "oracles: … 'bm_colhull.selftest': 'PASS 54/54'" — the oracle returns
  `{'donor_hulls_reencoded': 54}`; fine, but it is the donor's 54 hulls re-encoded, not the built
  file's 54, so "PASS 54/54" should say what was re-encoded.
- "the 3.1615×0.6342×1.0988 m box fits part 0's hull (3.4982×2.2831×7.037 m, identity axes)" —
  the hull's three extents are quoted in `[X, Y, Z]` order while the box is quoted `3.1615 × 0.6342
  × 1.0988`; a reader cannot tell which pairing is being asserted. Since both are axis-aligned, the
  fit needs the per-axis intervals, not just the extents.

## 4. Resolvable UNKNOWNs

| card | status | how |
|---|---|---|
| **U-2** — the row-index frame of `T-L8`…`T-L35` | **mostly resolved** (was: "either the build reordered the rows or the ledger counted another file") | The donor module exists (`…/b13b/unpacked/…/v0300_car_kensington_sportsmuscle_lights.vmodc`, **21 rows**) and the build is a filtered/reordered subset of it (mapping in I-1); `rc_merge/stage` and `rc_merge/verify` both hold the 18-row built order, so the build's row 8 = `Sport_Muscle_Rear_Break_Left` is a **build** fact. The ledger's *counts and histogram* are donor-frame and exact (21 rows; 5 × 30/40; 16 × 2/10). What remains open is only the *per-row index* used by `T-L8`…`T-L35`: the donor's row 8 is `Sport_Muscle_Headlight_Volume_Left` (30/40) and `T-L8` names `Point_Left`, which is donor row 13 — so those indices come from a third ordering (the 28-entry/4-rig `VehicleDynamicLights` table, or an earlier extract), not from either module on disk. |
| **U-1** — the BmAK "32 boxes" side of the collision rows | **partially resolvable now** | `Research/BatmobileGrab/COLLISION_BOXES.json` (G3-01b) already decodes every BmAK box: the drivable car's `RB_BodySetup` bodies carry **2** (`169750`, `Batmobile_Chassis`) and **1** (`169751`, `Batmobile_Rig_Weapons_Trans`) box, and "32 per package" is the count in the four **wreck** PhysicsAssets. So "32 boxes → 7 hull slots" is not the drivable car's decoded box record; the card should cite that file rather than defer the whole BmAK half. The class-defaults mapping (`Default__RVehicleBatmobile`, imports 456/457/577/578) does remain outside the JC3 build. |
| **U-5** — `hknpPhysicsSystemData` field meanings | **partly resolvable** | The changed lane is `+0x30..+0x32, +0x34..+0x3b`; `jc3hkx.stations` already documents `position at +0x30`, so the lane can be named from that layout with a citation instead of being disclaimed wholesale (see I-4). |
| **U-3** — extern-mesh vertex dequantisation | **stays UNKNOWN, and the card's own numbers say why** | `array(data+0x10)` is the node array (I-2); the geometry arrays (`hkGeometry`, 11,197 verts / 6,269 tris) are decoded, which is what the LOD2 check uses. No packed vertex array is decoded here, so nothing is overclaimed — only the label needs fixing. |
| **U-4** — `hknpStaticCompoundShapeData` (2 objects) | **stays UNKNOWN** | Correct: `bm_colmesh` refits only `hkcdDynamicTree`; no in-scope row depends on the static trees. |

## 5. Reproduction

```
uv run --with numpy python Tools/scripts/ledger_audit2.py --check
# OK 72 in-scope rows (19 changed, 53 unchanged) re-derived from the bytes
# after: {'TRANSLATED': 42, 'GUESSED': 0, 'NOT TRANSLATED': 25, 'REFUTED': 5, 'UNVERIFIABLE': 0}
# oracles: {'bm_colmesh.selftest': 'PASS', 'bm_colhull.selftest': 'PASS 54/54'}
# CHECK_RC=0
```

My reads used `jc3hkx.Packfile` / `decode_polytope` / `geometry_mesh`, `bm_colmesh.load_body` /
`dyn_tree_refit`, `bm_colhull.selftest`, `bm_parts.decode_parts`, `jc3adf.walk` and
`xml.etree.ElementTree` directly — not `ledger_audit2.phys_facts/parts_facts/epe_facts/lights_facts`
— and the diff/containment/refit arithmetic is my own.

State left behind: only this review file. `LEDGER_AUDIT2.md/.json`, `T_ROWS.jsonl`,
`LEDGER_AUDIT.json`, the build and all tools are untouched.
