# JC3 donor decode depth (G3-12)

Every one of the **566** inner files of the vanilla Serpente entity `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.ee` (79.9 MB of inner bytes) classified by what the project's own decoders actually read, not by its extension.

| grade | files | meaning |
|---|---|---|
| FULL | 441 | a project decoder reads every byte and an oracle passes |
| PARTIAL | 121 | reads the structure, stops short of some bytes/fields |
| NAMED-ONLY | 4 | no project decoder opens the payload |

The grades are computed, not asserted: `decode_depth.py` runs each decoder on each file and records the oracle's verdict. `--check` reruns the census and fails if a grade, a count or this document changes.

## 1. Per extension

| ext | files | bytes | FULL | PARTIAL | NAMED-ONLY | decoder | oracle |
|---|---|---|---|---|---|---|---|
| `.rbm` | 198 | 4431917 | 195 | 3 | 0 | rbm_geom.decode | decode -> encode == bytes |
| `.ddsc` | 116 | 73640512 | 0 | 116 | 0 | AVTX container (BM SARC payload) | 128 + size == len on all 116 |
| `.effc` | 74 | 982598 | 74 | 0 | 0 | jc3adf.Adf + walk | header total == len, allocation tiling, no raw types |
| `.trim` | 60 | 144540 | 60 | 0 | 0 | jc3adf.Adf + walk | header total == len, allocation tiling, no raw types |
| `.lod` | 59 | 26221 | 59 | 0 | 0 | text lines | lines re-join to the exact bytes |
| `.vmodc` | 31 | 195998 | 31 | 0 | 0 | jc3adf.Adf + walk | header total == len, allocation tiling, no raw types |
| `.ctunec` | 17 | 34035 | 17 | 0 | 0 | jc3adf.Adf + walk | header total == len, allocation tiling, no raw types |
| `.pfxc` | 4 | 10000 | 0 | 0 | 4 | none | none |
| `.etunec` | 2 | 2856 | 2 | 0 | 0 | jc3adf.Adf + walk | header total == len, allocation tiling, no raw types |
| `.fmod_guids` | 1 | 758 | 1 | 0 | 0 | walk (ver, banks, guids) | walk ends at EOF |
| `.physicsc` | 1 | 340368 | 0 | 1 | 0 | jc3hkx.Packfile | per class, see section 4 |
| `.stringlookup` | 1 | 2210 | 1 | 0 | 0 | jc3adf.Adf + walk | header total == len, allocation tiling, no raw types |
| `.ftunec` | 1 | 644 | 1 | 0 | 0 | jc3adf.Adf + walk | header total == len, allocation tiling, no raw types |
| `.epe` | 1 | 109526 | 0 | 1 | 0 | rtpcdump.parse_rtpc | ConvertProperty re-encode == bytes |

What each family is, and what the grade rests on:

* **`.rbm` (198).** `rbm_geom` decodes and re-encodes CarPaintMM and the generic blocks; 195 of them return byte-identical, which is the oracle. The 3 that do not carry a `GeneralMkIII` block (`sportsmuscle_missile_base_signature_lod1/2/3`): `rbm_geom` has no serializer for it (its own error says so), so those three are PARTIAL - `jc3geom` decodes their positions/indices with a containment oracle, but nothing re-encodes them.
* **ADF v4 (`.effc` + `.trim` + `.vmodc` + `.ctunec` + `.etunec` + `.stringlookup` + `.ftunec`).** 186 files: `.vmodc` modules, `.effc`, `.trim`, `.ctunec`, `.etunec`, `.ftunec`, `.stringlookup`. `jc3adf` reads the header, name table, type dictionary and every instance; the check here is the file's own accounting - the header's `total` equals the file length, the walk meets no undecoded type code, and header + instance extents + array/string allocations + declared tables + zero padding tile `[0, len)` with nothing left over. That closes on 186 of them. The string table at the tail is why they looked opaque: the data section comes *first* and the tables after it, the opposite of the header-first layout one expects.
* **`.ddsc` (116, 73640512 bytes - three quarters of the bundle).** The container is accounted on **116 of 116**: magic `AVTX`, then `u32[8] + u32[9] == len` (128 + payload). That mapping is DERIVED from the fleet, not published - it holds on all 116, which is why it is trusted, and the per-file bytes are in the JSON. What is missing is the payload itself: no project script reads the texels of a `.ddsc` (`tex2ddsc` only *writes* one, through ConvertTexture, and only formats 71 and 83), and `u32[2]`'s values (77 on the sampled files) are not mapped to a texture format. Grade: PARTIAL.
* **`.lod` (59).** Plain ASCII, and every one of the 59 has the same shape: five lines naming the part's render models, then a trailing decimal (`1.0`). A line may be the single character `-`, which is a LOD slot with no model - **16** of the 59 are like that (the `mshswap` parts, the seats, the engine). `bm_paths.py` already rewrites them by string. Decoded as text, re-joined against the bytes, every line a path or `-`, and the last a float - the shape is checked, not assumed. FULL.
* **`.pfxc` (4).** `PFX\0` magic and a header, then nothing the project reads: no script in `Tools/scripts` opens a `.pfxc` (`_check_pfxc.py` inspects the `.physicsc`, `jc3traffic`/`jc3sigdiff` only name the extension). NAMED-ONLY.
* **`.epe` (1).** `rtpcdump` walks 450 nodes of the RTPC tree; the oracle is ConvertProperty: export to XML and re-import must return the same bytes (the round trip B-05 relies on). It does not: ConvertProperty round trip is not byte-identical (109526 -> 109526 B, first diff at 0x765). The structure is read, the byte stream is not reproduced, so the grade is PARTIAL - and that is a fact about ConvertProperty on this file, not about the entity tree.
* **`.fmod_guids` (1).** version, bank names, then 16-byte event GUIDs; the walk ends exactly at EOF, which is the accounting. FULL.

## 2. The `.physicsc` per object class

One file, 340368 bytes, **430 objects in 16 classes**. `jc3hkx` types every object from the packfile's virtual fixup table, so the classes are the file's own, not a guess.

| class | objects | grade | what is read | oracle | not read |
|---|---|---|---|---|---|
| `CPfxPartIndexProperty` | 98 | PARTIAL | the part index (u32 at +0x10) | joined to PARTS_TABLE.jsonl, 25769/35499 compound instances resolve to a part name (WIRING.md) | the rest of the property object is not decoded |
| `hkRefCountedProperties` | 92 | PARTIAL | the property pointer list, followed to the CPfxPartIndexProperty it holds | the reached part index resolves to a name in PARTS_TABLE.jsonl (25769/35499 instances carry one) | the rest of this object's header is not named |
| `hknpShapeMassProperties` | 56 | NAMED-ONLY | nothing | none | layout not decoded, so no mass, inertia or centre of mass is read from it |
| `hknpConvexPolytopeShape` | 54 | FULL | header, vertices (w = 0.5 + rank/2^23), planes, face table, index block, 0x7F padding | block accounting `0x50 + 16V + 16P + faces + I + pad == extent` and every plane supporting (`abs(max n.v + d) <= r`) - jc3hkx check --all: 18865/18865 blocks and 18865/18865 supporting planes, 0 violations | - |
| `hkGeometry` | 36 | FULL | vertices + triangles | the arrays fill the object exactly (9582/9582) | - |
| `hknpDynamicCompoundShape` | 20 | PARTIAL | the same 128-byte instance array (a separate allocation) | child AABB containment, as the static class | as the static class |
| `hknpDynamicCompoundShapeData` | 20 | NAMED-ONLY | typed only | none | the data blob behind the shape is not decoded |
| `hknpExternMeshShape` | 18 | PARTIAL | vertex count, 6-byte stride (3 x u16), AABB | stride confirmed by the gap to the next array | the vertices' de-quantization frame is not pinned: the quantized triples reproduce the minimum corner but not the extent, so positions are not decoded |
| `hknpExternMeshShapeData` | 18 | PARTIAL | same as its shape (count, stride, AABB) | layout from the parent shape's array | vertex de-quantization frame unpinned |
| `hkpLimitedHingeConstraintData` | 9 | NAMED-ONLY | nothing | none | constraint layout not decoded: the hinge axis, pivot and angular limits are not read. This is the class a door or a hinged part's limits would live in. |
| `hknpStaticCompoundShape` | 2 | PARTIAL | inline array of 128-byte hknpShapeInstance records (basis, translation, scale, child shape pointer) and the child classes | every child AABB inside the parent AABB (6382/6382 compounds) and stride 128 confirmed by the gap to the next target | 41 of 6382 parent AABBs are not explained by the children's union; the rest of the shape header beyond the instance slot is not named |
| `hknpStaticCompoundShapeData` | 2 | NAMED-ONLY | typed only | none | the data blob behind the shape is not decoded (the shape's own inline instance array is, see hknpStaticCompoundShape) |
| `hkpRagdollConstraintData` | 2 | NAMED-ONLY | nothing | none | constraint layout not decoded: the cone/twist limits are not read |
| `hkRootLevelContainer` | 1 | PARTIAL | the named-variant array (name + object pointer) | every variant name resolves through its hkStringPtr | only the variant chain is read; the container's other fields are not named |
| `hknpPhysicsSceneData` | 1 | PARTIAL | the variant name chain down to hknpPhysicsSystemData | the chain reaches the system data on every vehicle | the scene's own arrays are not decoded, only walked through |
| `hknpPhysicsSystemData` | 1 | PARTIAL | the six arrays (80 / 64 / 112 / 96-byte elements, then two pointer arrays); the wheel hardpoint float4 at +0x30 of the 96-byte entries | element strides confirmed by the gap to the next array; the hardpoints agree with jc3phys.py's independent raw-quad scan on 17 vehicles, 0 disagreements | the 80-byte body and 64-byte motion entry fields are counted and sized but not pinned (PHYSICS_WRITE.md UNKNOWN 4) |

The card's own list, answered from the census above: **hulls** - 54 `hknpConvexPolytopeShape`, **FULL** (block accounting plus the supporting-plane oracle on all 18865 in the fleet, 0 violations); **extern meshes** - 18, **PARTIAL** (count and AABB exact, the 3 x u16 vertex frame unpinned); **compounds** - 20 dynamic + 2 static, **PARTIAL** (the 128-byte instance records decode and every child AABB sits inside its parent's, but 41 of 6382 parent AABBs are not explained by the children's union); **body table** - the 80-byte body and 64-byte motion entries in `hknpPhysicsSystemData` are counted and sized, fields unpinned; **constraints** - 9 `hkpLimitedHingeConstraintData` and 2 `hkpRagdollConstraintData`, both **NAMED-ONLY**: the class is typed by the virtual fixup table, the axis/pivot/limit layout is not decoded; **mass properties** - 56 `hknpShapeMassProperties`, **NAMED-ONLY** (no mass, inertia or centre of mass is read).

## 3. Per file

| # | file | bytes | stored | grade | what is not read |
|---|---|---|---|---|---|
| 1 | `editor/entities/jc_cameras/character_cameras/auxilarymotion/action_noise.ctunec` | 6099 | embedded | FULL | - |
| 2 | `editor/entities/jc_cameras/character_cameras/collision/no_plyr_vehicle_collision.ctunec` | 2102 | embedded | FULL | - |
| 3 | `editor/entities/jc_cameras/character_cameras/ignore_parent_rotation.ctunec` | 370 | embedded | FULL | - |
| 4 | `editor/entities/jc_cameras/character_cameras/listenerposition/vehicle_listener_position.ctunec` | 434 | embedded | FULL | - |
| 5 | `editor/entities/jc_cameras/character_cameras/transitions/any_to_action.ctunec` | 1334 | embedded | FULL | - |
| 6 | `editor/entities/jc_cameras/ctune_templates/full_screen_effect.ctunec` | 266 | embedded | FULL | - |
| 7 | `editor/entities/jc_cameras/vehicle_cameras/auxilarymotion/vehicle_motion.ctunec` | 8949 | embedded | FULL | - |
| 8 | `editor/entities/jc_cameras/vehicle_cameras/car_base.ctunec` | 5968 | embedded | FULL | - |
| 9 | `editor/entities/jc_cameras/vehicle_cameras/framing/exit_left_framing.ctunec` | 685 | embedded | FULL | - |
| 10 | `editor/entities/jc_cameras/vehicle_cameras/framing/exit_right_framing.ctunec` | 686 | embedded | FULL | - |
| 11 | `editor/entities/jc_cameras/vehicle_cameras/framing/left_hijack_framing.ctunec` | 687 | embedded | FULL | - |
| 12 | `editor/entities/jc_cameras/vehicle_cameras/framing/right_hijack_framing.ctunec` | 688 | embedded | FULL | - |
| 13 | `editor/entities/jc_cameras/vehicle_cameras/shake/vehicle_camera_shake.ctunec` | 405 | embedded | FULL | - |
| 14 | `editor/entities/jc_cameras/vehicle_cameras/to_vehicle_trans.ctunec` | 1339 | embedded | FULL | - |
| 15 | `editor/entities/jc_cameras/vehicle_cameras/transitions/greelin_to_vehicle_action.ctunec` | 1346 | embedded | FULL | - |
| 16 | `editor/entities/jc_cameras/vehicle_cameras/transitions/stunttrav_to_vehicle_action.ctunec` | 1341 | embedded | FULL | - |
| 17 | `editor/entities/jc_cameras/vehicle_cameras/transitions/vehicle_to_exit.ctunec` | 1336 | embedded | FULL | - |
| 18 | `effects/textures/decals/decal_scorch_alpha_dif.ddsc` | 349680 | embedded | PARTIAL | container accounted (AVTX, 128 + 349552 == 349680) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 19 | `effects/textures/decals/decal_scorch_mpm.ddsc` | 11064 | embedded | PARTIAL | container accounted (AVTX, 128 + 10936 == 11064) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 20 | `effects/textures/e_smoke02dist_alpha_dif.ddsc` | 349680 | embedded | PARTIAL | container accounted (AVTX, 128 + 349552 == 349680) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 21 | `effects/textures/erosion/erosion_smallcurve_soft.ddsc` | 16512 | embedded | PARTIAL | container accounted (AVTX, 128 + 16384 == 16512) but no project decoder reads the payload: the texel block format id (u32[2] = 87) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 22 | `effects/textures/t_blast_refraction_alpha_dif.ddsc` | 349680 | embedded | PARTIAL | container accounted (AVTX, 128 + 349552 == 349680) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 23 | `effects/textures/t_blood_splat_01_s2_alpha_dif.ddsc` | 1398256 | reference | PARTIAL | container accounted (AVTX, 128 + 1398128 == 1398256) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 24 | `effects/textures/t_bubble_singles_alpha_dif.ddsc` | 349680 | embedded | PARTIAL | container accounted (AVTX, 128 + 349552 == 349680) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 25 | `effects/textures/t_bullet_hits_bw_s2_dif.ddsc` | 87520 | embedded | PARTIAL | container accounted (AVTX, 128 + 87392 == 87520) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 26 | `effects/textures/t_bullet_hits_s2_dif.ddsc` | 87520 | embedded | PARTIAL | container accounted (AVTX, 128 + 87392 == 87520) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 27 | `effects/textures/t_cloud_grid_alpha_dif.ddsc` | 1398256 | reference | PARTIAL | container accounted (AVTX, 128 + 1398128 == 1398256) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 28 | `effects/textures/t_debris_car_01_s2_alpha_dif.ddsc` | 43840 | embedded | PARTIAL | container accounted (AVTX, 128 + 43712 == 43840) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 29 | `effects/textures/t_debris_glass_row_01_s2_alpha_dif.ddsc` | 43840 | embedded | PARTIAL | container accounted (AVTX, 128 + 43712 == 43840) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 30 | `effects/textures/t_debris_grass_row_01_s2_alpha_dif.ddsc` | 43840 | embedded | PARTIAL | container accounted (AVTX, 128 + 43712 == 43840) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 31 | `effects/textures/t_debris_row_01_s2_alpha_dif.ddsc` | 43840 | embedded | PARTIAL | container accounted (AVTX, 128 + 43712 == 43840) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 32 | `effects/textures/t_debris_shrapnel_row_01_s2_alpha_dif.ddsc` | 43840 | embedded | PARTIAL | container accounted (AVTX, 128 + 43712 == 43840) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 33 | `effects/textures/t_debris_stone_row_01_alpha_dif.ddsc` | 43840 | embedded | PARTIAL | container accounted (AVTX, 128 + 43712 == 43840) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 34 | `effects/textures/t_decohedge_s2alpha_dif.ddsc` | 43840 | embedded | PARTIAL | container accounted (AVTX, 128 + 43712 == 43840) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 35 | `effects/textures/t_dirt_grid_alpha_dif.ddsc` | 1398256 | reference | PARTIAL | container accounted (AVTX, 128 + 1398128 == 1398256) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 36 | `effects/textures/t_drips_01_nrm.ddsc` | 5600 | embedded | PARTIAL | container accounted (AVTX, 128 + 5472 == 5600) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 37 | `effects/textures/t_drips_base_01_alpha_dif.ddsc` | 11072 | embedded | PARTIAL | container accounted (AVTX, 128 + 10944 == 11072) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 38 | `effects/textures/t_explosiongrid_fume_06_gold_alpha_dif.ddsc` | 22369776 | reference | PARTIAL | container accounted (AVTX, 128 + 22369648 == 22369776) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 39 | `effects/textures/t_flame_dance_02_alpha_dif.ddsc` | 2796352 | reference | PARTIAL | container accounted (AVTX, 128 + 2796224 == 2796352) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 40 | `effects/textures/t_flare_glow_base_dif.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 41 | `effects/textures/t_flare_glow_blob_dif.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 42 | `effects/textures/t_flare_headlight_ramp.ddsc` | 262272 | embedded | PARTIAL | container accounted (AVTX, 128 + 262144 == 262272) but no project decoder reads the payload: the texel block format id (u32[2] = 87) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 43 | `effects/textures/t_flare_star_01_dif.ddsc` | 699192 | reference | PARTIAL | container accounted (AVTX, 128 + 699064 == 699192) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 44 | `effects/textures/t_flash_tile_dif.ddsc` | 174904 | embedded | PARTIAL | container accounted (AVTX, 128 + 174776 == 174904) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 45 | `effects/textures/t_goo_01_nrm.ddsc` | 87520 | embedded | PARTIAL | container accounted (AVTX, 128 + 87392 == 87520) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 46 | `effects/textures/t_goo_base_01_alpha_dif.ddsc` | 174912 | embedded | PARTIAL | container accounted (AVTX, 128 + 174784 == 174912) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 47 | `effects/textures/t_goo_base_erode_01_alpha_dif.ddsc` | 174912 | embedded | PARTIAL | container accounted (AVTX, 128 + 174784 == 174912) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 48 | `effects/textures/t_grass_blades_s2_alpha_dif.ddsc` | 349680 | embedded | PARTIAL | container accounted (AVTX, 128 + 349552 == 349680) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 49 | `effects/textures/t_grass_tall_s2_alpha_dif.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 50 | `effects/textures/t_grit_fine_01_s2_alpha_dif.ddsc` | 87536 | embedded | PARTIAL | container accounted (AVTX, 128 + 87408 == 87536) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 51 | `effects/textures/t_smoke_blast_alpha_dif.ddsc` | 699200 | reference | PARTIAL | container accounted (AVTX, 128 + 699072 == 699200) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 52 | `effects/textures/t_smoke_light_rolling_01_alpha_dif.ddsc` | 5592560 | reference | PARTIAL | container accounted (AVTX, 128 + 5592432 == 5592560) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 53 | `effects/textures/t_smoke_puffs_alpha_dif.ddsc` | 349680 | embedded | PARTIAL | container accounted (AVTX, 128 + 349552 == 349680) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 54 | `effects/textures/t_smoke_rolling_03a_alpha_dif.ddsc` | 1398256 | reference | PARTIAL | container accounted (AVTX, 128 + 1398128 == 1398256) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 55 | `effects/textures/t_smoke_rolling_04_alpha_dif.ddsc` | 5592560 | reference | PARTIAL | container accounted (AVTX, 128 + 5592432 == 5592560) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 56 | `effects/textures/t_smoke_rolling_06_alpha_dif.ddsc` | 5592560 | reference | PARTIAL | container accounted (AVTX, 128 + 5592432 == 5592560) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 57 | `effects/textures/t_smoke_rolling_top_04_alpha_dif.ddsc` | 5592560 | reference | PARTIAL | container accounted (AVTX, 128 + 5592432 == 5592560) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 58 | `effects/textures/t_spark_ash_s2_alpha_dif.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 59 | `effects/textures/t_spark_bits_02_s2_alpha_dif.ddsc` | 43840 | embedded | PARTIAL | container accounted (AVTX, 128 + 43712 == 43840) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 60 | `effects/textures/t_spark_bits_s2_alpha_dif.ddsc` | 87536 | embedded | PARTIAL | container accounted (AVTX, 128 + 87408 == 87536) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 61 | `effects/textures/t_spark_core_01_s2_alpha_dif.ddsc` | 87536 | embedded | PARTIAL | container accounted (AVTX, 128 + 87408 == 87536) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 62 | `effects/textures/t_sparks_blast_dif.ddsc` | 1398248 | reference | PARTIAL | container accounted (AVTX, 128 + 1398120 == 1398248) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 63 | `effects/textures/t_spherical_ramp.ddsc` | 262272 | embedded | PARTIAL | container accounted (AVTX, 128 + 262144 == 262272) but no project decoder reads the payload: the texel block format id (u32[2] = 87) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 64 | `effects/textures/t_splat_02_s2_alpha_dif.ddsc` | 349680 | embedded | PARTIAL | container accounted (AVTX, 128 + 349552 == 349680) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 65 | `effects/textures/t_velocity_streak_alpha_dif.ddsc` | 640 | embedded | PARTIAL | container accounted (AVTX, 128 + 512 == 640) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 66 | `effects/textures/t_water_splash_01_alpha_dif.ddsc` | 349680 | embedded | PARTIAL | container accounted (AVTX, 128 + 349552 == 349680) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 67 | `effects/textures/t_water_splash_02_alpha_dif.ddsc` | 349680 | embedded | PARTIAL | container accounted (AVTX, 128 + 349552 == 349680) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 68 | `effects/textures/t_water_splash_03_alpha_dif.ddsc` | 1398256 | reference | PARTIAL | container accounted (AVTX, 128 + 1398128 == 1398256) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 69 | `effects/textures/temp/water_explosion_temp_alpha_dif.ddsc` | 2796368 | reference | PARTIAL | container accounted (AVTX, 128 + 2796240 == 2796368) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 70 | `effects/textures/vfx_fireball_alpha_dif.ddsc` | 2796352 | reference | PARTIAL | container accounted (AVTX, 128 + 2796224 == 2796352) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 71 | `effects/textures/vfx_flames_small_alpha_dif.ddsc` | 699200 | reference | PARTIAL | container accounted (AVTX, 128 + 699072 == 699200) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 72 | `models/jc_environments/shared/textures/decals/roads/road_scorch_002_nrm.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 73 | `models/jc_vehicles/00_shared/car_lights/textures/car_lights_kensington_modern_dif.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 74 | `models/jc_vehicles/00_shared/car_lights/textures/car_lights_kensington_modern_emissive_alpha_mpm.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 75 | `models/jc_vehicles/00_shared/car_lights/textures/car_lights_kensington_modern_glass_dif.ddsc` | 21984 | embedded | PARTIAL | container accounted (AVTX, 128 + 21856 == 21984) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 76 | `models/jc_vehicles/00_shared/car_lights/textures/car_lights_kensington_modern_glass_mpm.ddsc` | 21984 | embedded | PARTIAL | container accounted (AVTX, 128 + 21856 == 21984) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 77 | `models/jc_vehicles/00_shared/car_lights/textures/car_lights_kensington_modern_mpm.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 78 | `models/jc_vehicles/00_shared/car_lights/textures/car_lights_kensington_modern_nrm.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 79 | `models/jc_vehicles/00_shared/car_tire/texture/car_tire_sport02_dif.ddsc` | 21984 | embedded | PARTIAL | container accounted (AVTX, 128 + 21856 == 21984) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 80 | `models/jc_vehicles/00_shared/car_tire/texture/car_tire_sport02_mpm.ddsc` | 21984 | embedded | PARTIAL | container accounted (AVTX, 128 + 21856 == 21984) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 81 | `models/jc_vehicles/00_shared/car_tire/texture/car_tire_sport02_nrm.ddsc` | 43840 | embedded | PARTIAL | container accounted (AVTX, 128 + 43712 == 43840) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 82 | `models/jc_vehicles/00_shared/car_undercarriage/texture/car_undercarriage_sport01_dif.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 83 | `models/jc_vehicles/00_shared/car_undercarriage/texture/car_undercarriage_sport01_mpm.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 84 | `models/jc_vehicles/00_shared/car_undercarriage/texture/car_undercarriage_sport01_nrm.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 85 | `models/jc_vehicles/00_shared/shared_car_007_windows/textures/shared_car_007_windows_alpha_dif.ddsc` | 1520 | embedded | PARTIAL | container accounted (AVTX, 128 + 1392 == 1520) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 86 | `models/jc_vehicles/00_shared/shared_car_009_licenseplate/textures/shared_car_009_licenseplate_decal_alpha_dif.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 87 | `models/jc_vehicles/00_shared/shared_car_009_licenseplate/textures/shared_car_009_licenseplate_decal_mpm.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 88 | `models/jc_vehicles/00_shared/shared_car_009_licenseplate/textures/shared_car_009_licenseplate_decal_nrm.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 89 | `models/jc_vehicles/00_shared/shared_car_009_licenseplate/textures/shared_car_009_licenseplate_dif.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 90 | `models/jc_vehicles/00_shared/shared_car_009_licenseplate/textures/shared_car_009_licenseplate_mpm.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 91 | `models/jc_vehicles/00_shared/shared_car_009_licenseplate/textures/shared_car_009_licenseplate_nrm.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 92 | `models/jc_vehicles/00_shared/textures/damage2_nrm.ddsc` | 1398256 | reference | PARTIAL | container accounted (AVTX, 128 + 1398128 == 1398256) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 93 | `models/jc_vehicles/00_shared/textures/vehicles_atlas_alpha_dif.ddsc` | 1398256 | reference | PARTIAL | container accounted (AVTX, 128 + 1398128 == 1398256) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 94 | `models/jc_vehicles/00_shared/vehicle_debris/textures/vehicle_debris_dif.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 95 | `models/jc_vehicles/00_shared/vehicle_debris/textures/vehicle_debris_mpm.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 96 | `models/jc_vehicles/00_shared/vehicle_debris/textures/vehicle_debris_nrm.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 97 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/body_aggregate_base_decal_alpha_dif.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 98 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/body_aggregate_base_dif.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 99 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/body_aggregate_base_mpm.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 100 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/body_aggregate_base_msk.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 101 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/body_aggregate_damage_alpha_dif.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 102 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/body_aggregate_damage_alpha_nrm.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 103 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/door_f_l_aggregate_base_decal_alpha_dif.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 104 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/door_f_l_aggregate_base_dif.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 105 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/door_f_l_aggregate_base_mpm.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 106 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/door_f_l_aggregate_base_msk.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 107 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/door_f_l_aggregate_damage_alpha_dif.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 108 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/door_f_l_aggregate_damage_alpha_nrm.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 109 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/door_f_r_aggregate_base_decal_alpha_dif.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 110 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/door_f_r_aggregate_base_dif.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 111 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/door_f_r_aggregate_base_mpm.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 112 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/door_f_r_aggregate_base_msk.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 113 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/door_f_r_aggregate_damage_alpha_dif.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 114 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/door_f_r_aggregate_damage_alpha_nrm.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 115 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/trunk_aggregate_base_decal_alpha_dif.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 116 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/trunk_aggregate_base_dif.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 117 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/trunk_aggregate_base_mpm.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 118 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/trunk_aggregate_base_msk.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 119 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/trunk_aggregate_damage_alpha_dif.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 120 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/trunk_aggregate_damage_alpha_nrm.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 121 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/v0300_car_kensington_sportsmuscle_body_dif.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 122 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/v0300_car_kensington_sportsmuscle_body_mpm.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 123 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/v0300_car_kensington_sportsmuscle_body_msk.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 124 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/v0300_car_kensington_sportsmuscle_body_nrm.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 83) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 125 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/v0300_car_kensington_sportsmuscle_glass_alpha_dif.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 126 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/v0300_car_kensington_sportsmuscle_glass_mpm.ddsc` | 2872 | embedded | PARTIAL | container accounted (AVTX, 128 + 2744 == 2872) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 127 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/v0300_car_kensington_sportsmuscle_int_dif.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 128 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/v0300_car_kensington_sportsmuscle_int_mpm.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 129 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/v0300_car_kensington_sportsmuscle_int_nrm.ddsc` | 22000 | embedded | PARTIAL | container accounted (AVTX, 128 + 21872 == 22000) but no project decoder reads the payload: the texel block format id (u32[2] = 77) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 130 | `models/jc_weapons/06_vehicle/w503_missile_capstone_billfire/textures/w503_missile_capstone_billfire_dif.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 131 | `models/jc_weapons/06_vehicle/w503_missile_capstone_billfire/textures/w503_missile_capstone_billfire_mpm.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 132 | `models/jc_weapons/06_vehicle/w503_missile_capstone_billfire/textures/w503_missile_capstone_billfire_nrm.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 133 | `textures/00_general/dummy/a00_dummy_grey_dif_detail.ddsc` | 43832 | embedded | PARTIAL | container accounted (AVTX, 128 + 43704 == 43832) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture |
| 134 | `effects/destruction/explosion_template_trail.effc` | 11295 | embedded | FULL | - |
| 135 | `effects/fire/generic_fire_single_01.effc` | 11807 | embedded | FULL | - |
| 136 | `effects/flare/headlight_flare_01.effc` | 8079 | embedded | FULL | - |
| 137 | `effects/jc_characters/traversal/aoe/rico_aoe_stunting_cars.effc` | 8975 | embedded | FULL | - |
| 138 | `effects/jc_vehicles/collision/break_electric_sm.effc` | 11535 | embedded | FULL | - |
| 139 | `effects/jc_vehicles/collision/break_impact_lg.effc` | 14527 | embedded | FULL | - |
| 140 | `effects/jc_vehicles/collision/break_impact_md.effc` | 14527 | embedded | FULL | - |
| 141 | `effects/jc_vehicles/collision/break_impact_sm.effc` | 14527 | embedded | FULL | - |
| 142 | `effects/jc_vehicles/collision/chassis_impact_default.effc` | 18767 | embedded | FULL | - |
| 143 | `effects/jc_vehicles/collision/chassis_impact_dirt.effc` | 16575 | embedded | FULL | - |
| 144 | `effects/jc_vehicles/collision/chassis_impact_sand.effc` | 15151 | embedded | FULL | - |
| 145 | `effects/jc_vehicles/collision/chassis_impact_snow.effc` | 16303 | embedded | FULL | - |
| 146 | `effects/jc_vehicles/collision/chassis_impact_vegetation.effc` | 19647 | embedded | FULL | - |
| 147 | `effects/jc_vehicles/collision/chassis_impact_water.effc` | 16095 | embedded | FULL | - |
| 148 | `effects/jc_vehicles/collision/chassis_slide_default.effc` | 11807 | embedded | FULL | - |
| 149 | `effects/jc_vehicles/collision/chassis_slide_dirt.effc` | 10863 | embedded | FULL | - |
| 150 | `effects/jc_vehicles/collision/chassis_slide_sand.effc` | 9167 | embedded | FULL | - |
| 151 | `effects/jc_vehicles/collision/chassis_slide_snow.effc` | 10847 | embedded | FULL | - |
| 152 | `effects/jc_vehicles/collision/chassis_slide_vegetation.effc` | 11039 | embedded | FULL | - |
| 153 | `effects/jc_vehicles/collision/headlight_break_off_01.effc` | 9631 | embedded | FULL | - |
| 154 | `effects/jc_vehicles/collision/headlight_break_on_01.effc` | 13535 | embedded | FULL | - |
| 155 | `effects/jc_vehicles/damage/dmg_engine_drips.effc` | 6943 | embedded | FULL | - |
| 156 | `effects/jc_vehicles/damage/dmg_engine_ground_flames.effc` | 6943 | embedded | FULL | - |
| 157 | `effects/jc_vehicles/damage/dmg_fire_engine.effc` | 15615 | embedded | FULL | - |
| 158 | `effects/jc_vehicles/damage/dmg_fire_spread_base.effc` | 15455 | embedded | FULL | - |
| 159 | `effects/jc_vehicles/damage/dmg_fire_spread_roof.effc` | 18511 | embedded | FULL | - |
| 160 | `effects/jc_vehicles/damage/dmg_post_burn.effc` | 9151 | embedded | FULL | - |
| 161 | `effects/jc_vehicles/damage/dmg_smoke_engine.effc` | 8047 | embedded | FULL | - |
| 162 | `effects/jc_vehicles/damage/dmg_taillight_break.effc` | 11455 | embedded | FULL | - |
| 163 | `effects/jc_vehicles/damage/dmg_turnsignal_break.effc` | 11391 | embedded | FULL | - |
| 164 | `effects/jc_vehicles/damage/dmg_window_break.effc` | 11455 | embedded | FULL | - |
| 165 | `effects/jc_vehicles/damage/dmg_window_break_sm.effc` | 11455 | embedded | FULL | - |
| 166 | `effects/jc_vehicles/damage/exp_car_01.effc` | 34895 | embedded | FULL | - |
| 167 | `effects/jc_vehicles/exhaust/car_cycle_base_dual.effc` | 12127 | embedded | FULL | - |
| 168 | `effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc` | 20671 | embedded | FULL | - |
| 169 | `effects/jc_vehicles/exhaust/car_cycle_base_dual_tjump.effc` | 15439 | embedded | FULL | - |
| 170 | `effects/jc_vehicles/exhaust/car_tjump_trail.effc` | 8815 | embedded | FULL | - |
| 171 | `effects/jc_vehicles/traversal_water/boat_splash_jetski.effc` | 12527 | embedded | FULL | - |
| 172 | `effects/jc_vehicles/wheels/no_tire/notire_asphalt.effc` | 12191 | embedded | FULL | - |
| 173 | `effects/jc_vehicles/wheels/no_tire/notire_dirt.effc` | 10511 | embedded | FULL | - |
| 174 | `effects/jc_vehicles/wheels/no_tire/notire_grass.effc` | 11983 | embedded | FULL | - |
| 175 | `effects/jc_vehicles/wheels/no_tire/notire_gravel.effc` | 9215 | embedded | FULL | - |
| 176 | `effects/jc_vehicles/wheels/no_tire/notire_sand.effc` | 9007 | embedded | FULL | - |
| 177 | `effects/jc_vehicles/wheels/no_tire/notire_snow.effc` | 9183 | embedded | FULL | - |
| 178 | `effects/jc_vehicles/wheels/no_tire/notire_water.effc` | 9199 | embedded | FULL | - |
| 179 | `effects/jc_vehicles/wheels/rear_asphalt.effc` | 20591 | embedded | FULL | - |
| 180 | `effects/jc_vehicles/wheels/rear_dirt.effc` | 18895 | embedded | FULL | - |
| 181 | `effects/jc_vehicles/wheels/rear_grass.effc` | 20623 | embedded | FULL | - |
| 182 | `effects/jc_vehicles/wheels/rear_gravel.effc` | 17727 | embedded | FULL | - |
| 183 | `effects/jc_vehicles/wheels/rear_sand.effc` | 16207 | embedded | FULL | - |
| 184 | `effects/jc_vehicles/wheels/rear_snow.effc` | 16047 | embedded | FULL | - |
| 185 | `effects/jc_vehicles/wheels/rear_water.effc` | 14959 | embedded | FULL | - |
| 186 | `effects/jc_vehicles/wheels/trail/dust_trail_asphalt.effc` | 6559 | embedded | FULL | - |
| 187 | `effects/jc_vehicles/wheels/trail/dust_trail_dirt.effc` | 11999 | embedded | FULL | - |
| 188 | `effects/jc_vehicles/wheels/trail/dust_trail_grass.effc` | 14175 | embedded | FULL | - |
| 189 | `effects/jc_vehicles/wheels/trail/dust_trail_sand.effc` | 11999 | embedded | FULL | - |
| 190 | `effects/jc_vehicles/wheels/trail/dust_trail_snow.effc` | 11999 | embedded | FULL | - |
| 191 | `effects/jc_vehicles/wheels/trail/dust_trail_water.effc` | 8175 | embedded | FULL | - |
| 192 | `effects/jc_vehicles/wheels/wheel_explosion_notiremesh.effc` | 16879 | embedded | FULL | - |
| 193 | `effects/jc_weapons/rpg_launcher/rpg_explosion_water.effc` | 17231 | embedded | FULL | - |
| 194 | `effects/physics/default_table/def_blood.effc` | 13775 | embedded | FULL | - |
| 195 | `effects/physics/default_table/def_concrete.effc` | 11503 | embedded | FULL | - |
| 196 | `effects/physics/default_table/def_default.effc` | 9887 | embedded | FULL | - |
| 197 | `effects/physics/default_table/def_dirt.effc` | 13311 | embedded | FULL | - |
| 198 | `effects/physics/default_table/def_grass.effc` | 15023 | embedded | FULL | - |
| 199 | `effects/physics/default_table/def_metal.effc` | 13727 | embedded | FULL | - |
| 200 | `effects/physics/default_table/def_sand.effc` | 13679 | embedded | FULL | - |
| 201 | `effects/physics/default_table/def_snow.effc` | 15375 | embedded | FULL | - |
| 202 | `effects/physics/default_table/def_stone.effc` | 12879 | embedded | FULL | - |
| 203 | `effects/physics/default_table/def_vegetation.effc` | 15023 | embedded | FULL | - |
| 204 | `effects/physics/default_table/def_water.effc` | 18623 | embedded | FULL | - |
| 205 | `effects/trails/car_explode_trail_01.effc` | 10175 | embedded | FULL | - |
| 206 | `effects/trails/car_explode_trail_01_sm.effc` | 10175 | embedded | FULL | - |
| 207 | `effects/trails/spark_trail_02_med.effc` | 8495 | embedded | FULL | - |
| 208 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.epe` | 109526 | embedded | PARTIAL | ConvertProperty round trip is not byte-identical (109526 -> 109526 B, first diff at 0x765) |
| 209 | `editor/entities/jc_vehicles/00_shared/modules/vehicle_physics_effects_car.etunec` | 1469 | embedded | FULL | - |
| 210 | `editor/entities/jc_vehicles/00_shared/modules/vehicle_rumble_effects.etunec` | 1387 | embedded | FULL | - |
| 211 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.ee.fmod_guids` | 758 | embedded | FULL | - |
| 212 | `editor/entities/jc_explosions/vehicles/car_explosion_medium.ftunec` | 644 | embedded | FULL | - |
| 213 | `models/jc_vehicles/00_shared/vehicle_debris/debris_vehicle_debri01.lod` | 390 | embedded | FULL | - |
| 214 | `models/jc_vehicles/00_shared/vehicle_debris/debris_vehicle_debri02.lod` | 390 | embedded | FULL | - |
| 215 | `models/jc_vehicles/00_shared/vehicle_debris/debris_vehicle_debri03.lod` | 390 | embedded | FULL | - |
| 216 | `models/jc_vehicles/00_shared/vehicle_debris/debris_vehicle_debri04.lod` | 390 | embedded | FULL | - |
| 217 | `models/jc_vehicles/00_shared/vehicle_debris/debris_vehicle_debri05.lod` | 390 | embedded | FULL | - |
| 218 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_body.lod` | 450 | embedded | FULL | - |
| 219 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_c_mirror.lod` | 470 | embedded | FULL | - |
| 220 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_door_f_l.lod` | 470 | embedded | FULL | - |
| 221 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_door_f_l_window.lod` | 505 | embedded | FULL | - |
| 222 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_door_f_r.lod` | 470 | embedded | FULL | - |
| 223 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_door_f_r_window.lod` | 505 | embedded | FULL | - |
| 224 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_engine.lod` | 284 | embedded | FULL | - |
| 225 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_f_l_seat.lod` | 290 | embedded | FULL | - |
| 226 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_f_r_seat.lod` | 290 | embedded | FULL | - |
| 227 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_fender_l.lod` | 470 | embedded | FULL | - |
| 228 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_fender_r.lod` | 470 | embedded | FULL | - |
| 229 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_front_bumper.lod` | 490 | embedded | FULL | - |
| 230 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_grill.lod` | 455 | embedded | FULL | - |
| 231 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_l_01.lod` | 510 | embedded | FULL | - |
| 232 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_l_01mshswap.lod` | 346 | embedded | FULL | - |
| 233 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_l_02.lod` | 510 | embedded | FULL | - |
| 234 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_l_02mshswap.lod` | 335 | embedded | FULL | - |
| 235 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_r_01.lod` | 510 | embedded | FULL | - |
| 236 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_r_01mshswap.lod` | 346 | embedded | FULL | - |
| 237 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_r_02.lod` | 510 | embedded | FULL | - |
| 238 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_r_02mshswap.lod` | 335 | embedded | FULL | - |
| 239 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_hood.lod` | 450 | embedded | FULL | - |
| 240 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_hood_signature.lod` | 500 | embedded | FULL | - |
| 241 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_l_mirror.lod` | 470 | embedded | FULL | - |
| 242 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_missile_base_signature.lod` | 540 | embedded | FULL | - |
| 243 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_plate_f.lod` | 465 | embedded | FULL | - |
| 244 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_plate_r.lod` | 465 | embedded | FULL | - |
| 245 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_r_mirror.lod` | 470 | embedded | FULL | - |
| 246 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_rear_bumper.lod` | 485 | embedded | FULL | - |
| 247 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_f_l.lod` | 480 | embedded | FULL | - |
| 248 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_f_r.lod` | 480 | embedded | FULL | - |
| 249 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_r_l.lod` | 480 | embedded | FULL | - |
| 250 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_r_lmshswap.lod` | 427 | embedded | FULL | - |
| 251 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_r_r.lod` | 480 | embedded | FULL | - |
| 252 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_r_rmshswap.lod` | 427 | embedded | FULL | - |
| 253 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_steeringwheel.lod` | 305 | embedded | FULL | - |
| 254 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_c.lod` | 495 | embedded | FULL | - |
| 255 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_l.lod` | 495 | embedded | FULL | - |
| 256 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_lmshswap.lod` | 439 | embedded | FULL | - |
| 257 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_r.lod` | 495 | embedded | FULL | - |
| 258 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_rmshswap.lod` | 439 | embedded | FULL | - |
| 259 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_trunk.lod` | 455 | embedded | FULL | - |
| 260 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_trunk_window.lod` | 490 | embedded | FULL | - |
| 261 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_f_l.lod` | 475 | embedded | FULL | - |
| 262 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_f_lmshswap.lod` | 422 | embedded | FULL | - |
| 263 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_f_r.lod` | 475 | embedded | FULL | - |
| 264 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_f_rmshswap.lod` | 422 | embedded | FULL | - |
| 265 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_l.lod` | 475 | embedded | FULL | - |
| 266 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_lmshswap.lod` | 422 | embedded | FULL | - |
| 267 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_r.lod` | 475 | embedded | FULL | - |
| 268 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_rmshswap.lod` | 422 | embedded | FULL | - |
| 269 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_window_f.lod` | 470 | embedded | FULL | - |
| 270 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_window_r_l.lod` | 480 | embedded | FULL | - |
| 271 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_window_r_r.lod` | 480 | embedded | FULL | - |
| 272 | `models/jc_vehicles/00_shared/vehicle_debris/debris_vehicle_debri01_col.pfxc` | 2500 | embedded | NAMED-ONLY | no project script parses a .pfxc payload; the extension is only named (grep: _check_types/jc3sigdiff/jc3traffic list it, none opens it) |
| 273 | `models/jc_vehicles/00_shared/vehicle_debris/debris_vehicle_debri02_col.pfxc` | 2500 | embedded | NAMED-ONLY | no project script parses a .pfxc payload; the extension is only named (grep: _check_types/jc3sigdiff/jc3traffic list it, none opens it) |
| 274 | `models/jc_vehicles/00_shared/vehicle_debris/debris_vehicle_debri03_col.pfxc` | 2500 | embedded | NAMED-ONLY | no project script parses a .pfxc payload; the extension is only named (grep: _check_types/jc3sigdiff/jc3traffic list it, none opens it) |
| 275 | `models/jc_vehicles/00_shared/vehicle_debris/debris_vehicle_debri04_col.pfxc` | 2500 | embedded | NAMED-ONLY | no project script parses a .pfxc payload; the extension is only named (grep: _check_types/jc3sigdiff/jc3traffic list it, none opens it) |
| 276 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc` | 340368 | embedded | PARTIAL | 430 objects, 16 classes; per class below |
| 277 | `models/jc_vehicles/00_shared/vehicle_debris/debris_vehicle_debri01_lod1.rbm` | 8111 | embedded | FULL | - |
| 278 | `models/jc_vehicles/00_shared/vehicle_debris/debris_vehicle_debri02_lod1.rbm` | 13553 | embedded | FULL | - |
| 279 | `models/jc_vehicles/00_shared/vehicle_debris/debris_vehicle_debri03_lod1.rbm` | 4319 | embedded | FULL | - |
| 280 | `models/jc_vehicles/00_shared/vehicle_debris/debris_vehicle_debri04_lod1.rbm` | 3815 | embedded | FULL | - |
| 281 | `models/jc_vehicles/00_shared/vehicle_debris/debris_vehicle_debri05_lod1.rbm` | 5519 | embedded | FULL | - |
| 282 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_body_lod1.rbm` | 403514 | embedded | FULL | - |
| 283 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_body_lod2.rbm` | 284214 | embedded | FULL | - |
| 284 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_body_lod3.rbm` | 182381 | embedded | FULL | - |
| 285 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_body_lod4.rbm` | 202321 | embedded | FULL | - |
| 286 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_body_lod5.rbm` | 105269 | embedded | FULL | - |
| 287 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_c_mirror_lod1.rbm` | 14211 | embedded | FULL | - |
| 288 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_c_mirror_lod2.rbm` | 5247 | embedded | FULL | - |
| 289 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_c_mirror_lod3.rbm` | 4035 | embedded | FULL | - |
| 290 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_c_mirror_lod4.rbm` | 2775 | embedded | FULL | - |
| 291 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_door_f_l_lod1.rbm` | 65526 | embedded | FULL | - |
| 292 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_door_f_l_lod2.rbm` | 37064 | embedded | FULL | - |
| 293 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_door_f_l_lod3.rbm` | 22609 | embedded | FULL | - |
| 294 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_door_f_l_lod4.rbm` | 13225 | embedded | FULL | - |
| 295 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_door_f_l_window_lod1.rbm` | 4421 | embedded | FULL | - |
| 296 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_door_f_l_window_lod2.rbm` | 3769 | embedded | FULL | - |
| 297 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_door_f_l_window_lod3.rbm` | 1635 | embedded | FULL | - |
| 298 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_door_f_l_window_lod4.rbm` | 1157 | embedded | FULL | - |
| 299 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_door_f_r_lod1.rbm` | 65526 | embedded | FULL | - |
| 300 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_door_f_r_lod2.rbm` | 37220 | embedded | FULL | - |
| 301 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_door_f_r_lod3.rbm` | 23109 | embedded | FULL | - |
| 302 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_door_f_r_lod4.rbm` | 12475 | embedded | FULL | - |
| 303 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_door_f_r_window_lod1.rbm` | 4421 | embedded | FULL | - |
| 304 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_door_f_r_window_lod2.rbm` | 3521 | embedded | FULL | - |
| 305 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_door_f_r_window_lod3.rbm` | 1779 | embedded | FULL | - |
| 306 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_door_f_r_window_lod4.rbm` | 1449 | embedded | FULL | - |
| 307 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_engine_lod1.rbm` | 269464 | embedded | FULL | - |
| 308 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_engine_lod2.rbm` | 174746 | embedded | FULL | - |
| 309 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_engine_lod3.rbm` | 119161 | embedded | FULL | - |
| 310 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_f_l_seat_lod1.rbm` | 23075 | embedded | FULL | - |
| 311 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_f_l_seat_lod2.rbm` | 19991 | embedded | FULL | - |
| 312 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_f_l_seat_lod3.rbm` | 11717 | embedded | FULL | - |
| 313 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_f_r_seat_lod1.rbm` | 23075 | embedded | FULL | - |
| 314 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_f_r_seat_lod2.rbm` | 20039 | embedded | FULL | - |
| 315 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_f_r_seat_lod3.rbm` | 11969 | embedded | FULL | - |
| 316 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_fender_l_lod1.rbm` | 63679 | embedded | FULL | - |
| 317 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_fender_l_lod2.rbm` | 36167 | embedded | FULL | - |
| 318 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_fender_l_lod3.rbm` | 20127 | embedded | FULL | - |
| 319 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_fender_r_lod1.rbm` | 63623 | embedded | FULL | - |
| 320 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_fender_r_lod2.rbm` | 34775 | embedded | FULL | - |
| 321 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_fender_r_lod3.rbm` | 18423 | embedded | FULL | - |
| 322 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_front_bumper_lod1.rbm` | 64919 | embedded | FULL | - |
| 323 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_front_bumper_lod2.rbm` | 29887 | embedded | FULL | - |
| 324 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_front_bumper_lod3.rbm` | 19131 | embedded | FULL | - |
| 325 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_grill_lod1.rbm` | 31023 | embedded | FULL | - |
| 326 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_grill_lod2.rbm` | 16339 | embedded | FULL | - |
| 327 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_grill_lod3.rbm` | 11407 | embedded | FULL | - |
| 328 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_l_01_lod1.rbm` | 12182 | embedded | FULL | - |
| 329 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_l_01_lod2.rbm` | 5930 | embedded | FULL | - |
| 330 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_l_01_lod3.rbm` | 4090 | embedded | FULL | - |
| 331 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_l_01mshswap_lod1.rbm` | 11765 | embedded | FULL | - |
| 332 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_l_01mshswap_lod2.rbm` | 5787 | embedded | FULL | - |
| 333 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_l_01mshswap_lod3.rbm` | 4163 | embedded | FULL | - |
| 334 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_l_02_lod1.rbm` | 12182 | embedded | FULL | - |
| 335 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_l_02_lod2.rbm` | 7086 | embedded | FULL | - |
| 336 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_l_02_lod3.rbm` | 4474 | embedded | FULL | - |
| 337 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_l_02mshswap_lod1.rbm` | 12031 | embedded | FULL | - |
| 338 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_l_02mshswap_lod2.rbm` | 6365 | embedded | FULL | - |
| 339 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_l_02mshswap_lod3.rbm` | 4475 | embedded | FULL | - |
| 340 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_r_01_lod1.rbm` | 12182 | embedded | FULL | - |
| 341 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_r_01_lod2.rbm` | 5778 | embedded | FULL | - |
| 342 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_r_01_lod3.rbm` | 3900 | embedded | FULL | - |
| 343 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_r_01mshswap_lod1.rbm` | 11921 | embedded | FULL | - |
| 344 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_r_01mshswap_lod2.rbm` | 5477 | embedded | FULL | - |
| 345 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_r_01mshswap_lod3.rbm` | 4131 | embedded | FULL | - |
| 346 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_r_02_lod1.rbm` | 12182 | embedded | FULL | - |
| 347 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_r_02_lod2.rbm` | 7014 | embedded | FULL | - |
| 348 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_r_02_lod3.rbm` | 4510 | embedded | FULL | - |
| 349 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_r_02mshswap_lod1.rbm` | 11697 | embedded | FULL | - |
| 350 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_r_02mshswap_lod2.rbm` | 6431 | embedded | FULL | - |
| 351 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_headlight_f_r_02mshswap_lod3.rbm` | 4365 | embedded | FULL | - |
| 352 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_hood_lod1.rbm` | 47415 | embedded | FULL | - |
| 353 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_hood_lod2.rbm` | 26531 | embedded | FULL | - |
| 354 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_hood_lod3.rbm` | 13091 | embedded | FULL | - |
| 355 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_hood_signature_lod1.rbm` | 170710 | embedded | FULL | - |
| 356 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_hood_signature_lod2.rbm` | 40502 | embedded | FULL | - |
| 357 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_hood_signature_lod3.rbm` | 25592 | embedded | FULL | - |
| 358 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_l_mirror_lod1.rbm` | 11979 | embedded | FULL | - |
| 359 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_l_mirror_lod2.rbm` | 5115 | embedded | FULL | - |
| 360 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_l_mirror_lod3.rbm` | 4347 | embedded | FULL | - |
| 361 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_l_mirror_lod4.rbm` | 3159 | embedded | FULL | - |
| 362 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_missile_base_signature_lod1.rbm` | 45912 | embedded | PARTIAL | no codec for a block: block 1 is GeneralMkIII, which this codec does not parse (need its serializer to know where it ends) |
| 363 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_missile_base_signature_lod2.rbm` | 21842 | embedded | PARTIAL | no codec for a block: block 1 is GeneralMkIII, which this codec does not parse (need its serializer to know where it ends) |
| 364 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_missile_base_signature_lod3.rbm` | 14590 | embedded | PARTIAL | no codec for a block: block 1 is GeneralMkIII, which this codec does not parse (need its serializer to know where it ends) |
| 365 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_plate_f_lod1.rbm` | 6139 | embedded | FULL | - |
| 366 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_plate_f_lod2.rbm` | 4687 | embedded | FULL | - |
| 367 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_plate_f_lod3.rbm` | 3463 | embedded | FULL | - |
| 368 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_plate_r_lod1.rbm` | 6139 | embedded | FULL | - |
| 369 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_plate_r_lod2.rbm` | 4519 | embedded | FULL | - |
| 370 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_plate_r_lod3.rbm` | 3379 | embedded | FULL | - |
| 371 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_plate_r_lod4.rbm` | 2827 | embedded | FULL | - |
| 372 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_r_mirror_lod1.rbm` | 11979 | embedded | FULL | - |
| 373 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_r_mirror_lod2.rbm` | 4767 | embedded | FULL | - |
| 374 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_r_mirror_lod3.rbm` | 4299 | embedded | FULL | - |
| 375 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_r_mirror_lod4.rbm` | 3411 | embedded | FULL | - |
| 376 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_rear_bumper_lod1.rbm` | 59335 | embedded | FULL | - |
| 377 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_rear_bumper_lod2.rbm` | 32483 | embedded | FULL | - |
| 378 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_rear_bumper_lod3.rbm` | 15415 | embedded | FULL | - |
| 379 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_rear_bumper_lod4.rbm` | 8119 | embedded | FULL | - |
| 380 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_f_l_lod1.rbm` | 2506 | embedded | FULL | - |
| 381 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_f_l_lod2.rbm` | 2194 | embedded | FULL | - |
| 382 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_f_l_lod3.rbm` | 1978 | embedded | FULL | - |
| 383 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_f_r_lod1.rbm` | 2506 | embedded | FULL | - |
| 384 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_f_r_lod2.rbm` | 2194 | embedded | FULL | - |
| 385 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_f_r_lod3.rbm` | 1978 | embedded | FULL | - |
| 386 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_r_l_lod1.rbm` | 5772 | embedded | FULL | - |
| 387 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_r_l_lod2.rbm` | 5096 | embedded | FULL | - |
| 388 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_r_l_lod3.rbm` | 4070 | embedded | FULL | - |
| 389 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_r_l_lod4.rbm` | 2434 | embedded | FULL | - |
| 390 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_r_lmshswap_lod1.rbm` | 7472 | embedded | FULL | - |
| 391 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_r_lmshswap_lod2.rbm` | 4323 | embedded | FULL | - |
| 392 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_r_lmshswap_lod3.rbm` | 3673 | embedded | FULL | - |
| 393 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_r_lmshswap_lod4.rbm` | 3089 | embedded | FULL | - |
| 394 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_r_r_lod1.rbm` | 5772 | embedded | FULL | - |
| 395 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_r_r_lod2.rbm` | 5128 | embedded | FULL | - |
| 396 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_r_r_lod3.rbm` | 4046 | embedded | FULL | - |
| 397 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_r_r_lod4.rbm` | 2518 | embedded | FULL | - |
| 398 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_r_rmshswap_lod1.rbm` | 7086 | embedded | FULL | - |
| 399 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_r_rmshswap_lod2.rbm` | 4429 | embedded | FULL | - |
| 400 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_r_rmshswap_lod3.rbm` | 3535 | embedded | FULL | - |
| 401 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_signal_r_rmshswap_lod4.rbm` | 2861 | embedded | FULL | - |
| 402 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_steeringwheel_lod1.rbm` | 13721 | embedded | FULL | - |
| 403 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_steeringwheel_lod2.rbm` | 11081 | embedded | FULL | - |
| 404 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_steeringwheel_lod3.rbm` | 10553 | embedded | FULL | - |
| 405 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_c_lod1.rbm` | 3826 | embedded | FULL | - |
| 406 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_c_lod2.rbm` | 2626 | embedded | FULL | - |
| 407 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_c_lod3.rbm` | 2230 | embedded | FULL | - |
| 408 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_c_lod4.rbm` | 1978 | embedded | FULL | - |
| 409 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_l_lod1.rbm` | 10132 | embedded | FULL | - |
| 410 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_l_lod2.rbm` | 10600 | embedded | FULL | - |
| 411 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_l_lod3.rbm` | 7238 | embedded | FULL | - |
| 412 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_l_lod4.rbm` | 3010 | embedded | FULL | - |
| 413 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_lmshswap_lod1.rbm` | 11458 | embedded | FULL | - |
| 414 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_lmshswap_lod2.rbm` | 7965 | embedded | FULL | - |
| 415 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_lmshswap_lod3.rbm` | 5931 | embedded | FULL | - |
| 416 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_lmshswap_lod4.rbm` | 5087 | embedded | FULL | - |
| 417 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_r_lod1.rbm` | 10132 | embedded | FULL | - |
| 418 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_r_lod2.rbm` | 10444 | embedded | FULL | - |
| 419 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_r_lod3.rbm` | 7284 | embedded | FULL | - |
| 420 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_r_lod4.rbm` | 3202 | embedded | FULL | - |
| 421 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_rmshswap_lod1.rbm` | 11464 | embedded | FULL | - |
| 422 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_rmshswap_lod2.rbm` | 8693 | embedded | FULL | - |
| 423 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_rmshswap_lod3.rbm` | 5849 | embedded | FULL | - |
| 424 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_taillight_r_rmshswap_lod4.rbm` | 4769 | embedded | FULL | - |
| 425 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_trunk_lod1.rbm` | 61114 | embedded | FULL | - |
| 426 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_trunk_lod2.rbm` | 36430 | embedded | FULL | - |
| 427 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_trunk_lod3.rbm` | 22334 | embedded | FULL | - |
| 428 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_trunk_lod4.rbm` | 13461 | embedded | FULL | - |
| 429 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_trunk_window_lod1.rbm` | 4895 | embedded | FULL | - |
| 430 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_trunk_window_lod2.rbm` | 4249 | embedded | FULL | - |
| 431 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_trunk_window_lod3.rbm` | 1929 | embedded | FULL | - |
| 432 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_trunk_window_lod4.rbm` | 1589 | embedded | FULL | - |
| 433 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_f_l_lod1.rbm` | 43886 | embedded | FULL | - |
| 434 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_f_l_lod2.rbm` | 22142 | embedded | FULL | - |
| 435 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_f_l_lod3.rbm` | 14042 | embedded | FULL | - |
| 436 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_f_lmshswap_lod1.rbm` | 29198 | embedded | FULL | - |
| 437 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_f_lmshswap_lod2.rbm` | 17942 | embedded | FULL | - |
| 438 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_f_lmshswap_lod3.rbm` | 11750 | embedded | FULL | - |
| 439 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_f_r_lod1.rbm` | 41414 | embedded | FULL | - |
| 440 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_f_r_lod2.rbm` | 23234 | embedded | FULL | - |
| 441 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_f_r_lod3.rbm` | 13502 | embedded | FULL | - |
| 442 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_f_rmshswap_lod1.rbm` | 29198 | embedded | FULL | - |
| 443 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_f_rmshswap_lod2.rbm` | 18302 | embedded | FULL | - |
| 444 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_f_rmshswap_lod3.rbm` | 11774 | embedded | FULL | - |
| 445 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_l_lod1.rbm` | 41486 | embedded | FULL | - |
| 446 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_l_lod2.rbm` | 21830 | embedded | FULL | - |
| 447 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_l_lod3.rbm` | 14366 | embedded | FULL | - |
| 448 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_l_lod4.rbm` | 10382 | embedded | FULL | - |
| 449 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_l_lod5.rbm` | 7442 | embedded | FULL | - |
| 450 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_lmshswap_lod1.rbm` | 29198 | embedded | FULL | - |
| 451 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_lmshswap_lod2.rbm` | 17834 | embedded | FULL | - |
| 452 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_lmshswap_lod3.rbm` | 11966 | embedded | FULL | - |
| 453 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_lmshswap_lod4.rbm` | 8222 | embedded | FULL | - |
| 454 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_r_lod1.rbm` | 41414 | embedded | FULL | - |
| 455 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_r_lod2.rbm` | 23210 | embedded | FULL | - |
| 456 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_r_lod3.rbm` | 13610 | embedded | FULL | - |
| 457 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_r_lod4.rbm` | 10478 | embedded | FULL | - |
| 458 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_r_lod5.rbm` | 6026 | embedded | FULL | - |
| 459 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_rmshswap_lod1.rbm` | 29198 | embedded | FULL | - |
| 460 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_rmshswap_lod2.rbm` | 18038 | embedded | FULL | - |
| 461 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_rmshswap_lod3.rbm` | 11642 | embedded | FULL | - |
| 462 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_wheel_r_rmshswap_lod4.rbm` | 8078 | embedded | FULL | - |
| 463 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_window_f_lod1.rbm` | 5531 | embedded | FULL | - |
| 464 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_window_f_lod2.rbm` | 5127 | embedded | FULL | - |
| 465 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_window_f_lod3.rbm` | 2385 | embedded | FULL | - |
| 466 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_window_f_lod4.rbm` | 1537 | embedded | FULL | - |
| 467 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_window_r_l_lod1.rbm` | 2547 | embedded | FULL | - |
| 468 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_window_r_l_lod2.rbm` | 2351 | embedded | FULL | - |
| 469 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_window_r_l_lod3.rbm` | 1163 | embedded | FULL | - |
| 470 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_window_r_l_lod4.rbm` | 1019 | embedded | FULL | - |
| 471 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_window_r_r_lod1.rbm` | 2547 | embedded | FULL | - |
| 472 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_window_r_r_lod2.rbm` | 2051 | embedded | FULL | - |
| 473 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_window_r_r_lod3.rbm` | 1209 | embedded | FULL | - |
| 474 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_window_r_r_lod4.rbm` | 921 | embedded | FULL | - |
| 475 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.stringlookup` | 2210 | embedded | FULL | - |
| 476 | `effects/textures/e_smoke02dist_alpha_dif.tga.1_1d.trim` | 657 | embedded | FULL | - |
| 477 | `effects/textures/t_blast_refraction_alpha_dif.tga.1_1d.trim` | 657 | embedded | FULL | - |
| 478 | `effects/textures/t_bubble_singles_alpha_dif.tga.2_2b.trim` | 945 | embedded | FULL | - |
| 479 | `effects/textures/t_bullet_hits_bw_s2_dif.tga.2_4a.trim` | 1329 | embedded | FULL | - |
| 480 | `effects/textures/t_bullet_hits_s2_dif.tga.2_4a.trim` | 1329 | embedded | FULL | - |
| 481 | `effects/textures/t_cloud_grid_alpha_dif.tga.4_4b.trim` | 2097 | embedded | FULL | - |
| 482 | `effects/textures/t_debris_car_01_s2_alpha_dif.tga.2_4b.trim` | 1329 | embedded | FULL | - |
| 483 | `effects/textures/t_debris_glass_row_01_s2_alpha_dif.tga.2_4b.trim` | 1329 | embedded | FULL | - |
| 484 | `effects/textures/t_debris_glass_row_01_s2_alpha_dif.tga.2_4bb.trim` | 1329 | embedded | FULL | - |
| 485 | `effects/textures/t_debris_grass_row_01_s2_alpha_dif.tga.2_4b.trim` | 1329 | embedded | FULL | - |
| 486 | `effects/textures/t_debris_row_01_s2_alpha_dif.tga.2_4b.trim` | 1329 | embedded | FULL | - |
| 487 | `effects/textures/t_debris_shrapnel_row_01_s2_alpha_dif.tga.2_4b.trim` | 1329 | embedded | FULL | - |
| 488 | `effects/textures/t_debris_stone_row_01_alpha_dif.tga.2_4b.trim` | 1329 | embedded | FULL | - |
| 489 | `effects/textures/t_debris_stone_row_01_alpha_dif.tga.2_4bb.trim` | 1329 | embedded | FULL | - |
| 490 | `effects/textures/t_decohedge_s2alpha_dif.tga.2_4b.trim` | 1329 | embedded | FULL | - |
| 491 | `effects/textures/t_dirt_grid_alpha_dif.tga.2_2a.trim` | 945 | embedded | FULL | - |
| 492 | `effects/textures/t_dirt_grid_alpha_dif.tga.2_2b.trim` | 945 | embedded | FULL | - |
| 493 | `effects/textures/t_dirt_grid_alpha_dif.tga.2_2bb.trim` | 945 | embedded | FULL | - |
| 494 | `effects/textures/t_flame_dance_02_alpha_dif.tga.7_7b.trim` | 5265 | embedded | FULL | - |
| 495 | `effects/textures/t_flare_glow_base_dif.tga.1_1a.trim` | 657 | embedded | FULL | - |
| 496 | `effects/textures/t_flare_glow_blob_dif.tga.1_1a.trim` | 657 | embedded | FULL | - |
| 497 | `effects/textures/t_flare_headlight_ramp.tga.1_1a.trim` | 657 | embedded | FULL | - |
| 498 | `effects/textures/t_flare_star_01_dif.tga.1_1a.trim` | 657 | embedded | FULL | - |
| 499 | `effects/textures/t_flash_tile_dif.tga.4_4a.trim` | 2097 | embedded | FULL | - |
| 500 | `effects/textures/t_goo_base_01_alpha_dif.tga.1_2b.trim` | 753 | embedded | FULL | - |
| 501 | `effects/textures/t_goo_base_erode_01_alpha_dif.tga.1_2b.trim` | 753 | embedded | FULL | - |
| 502 | `effects/textures/t_grass_blades_s2_alpha_dif.tga.1_5b.trim` | 1041 | embedded | FULL | - |
| 503 | `effects/textures/t_grass_tall_s2_alpha_dif.tga.1_5b.trim` | 1041 | embedded | FULL | - |
| 504 | `effects/textures/t_grit_fine_01_s2_alpha_dif.tga.1_1b.trim` | 657 | embedded | FULL | - |
| 505 | `effects/textures/t_smoke_blast_alpha_dif.tga.1_2b.trim` | 753 | embedded | FULL | - |
| 506 | `effects/textures/t_smoke_light_rolling_01_alpha_dif.tga.8_8b.trim` | 6705 | embedded | FULL | - |
| 507 | `effects/textures/t_smoke_light_rolling_01_alpha_dif.tga.8_8bb.trim` | 6705 | embedded | FULL | - |
| 508 | `effects/textures/t_smoke_puffs_alpha_dif.tga.2_2b.trim` | 945 | embedded | FULL | - |
| 509 | `effects/textures/t_smoke_rolling_03a_alpha_dif.tga.6_6b.trim` | 4017 | embedded | FULL | - |
| 510 | `effects/textures/t_smoke_rolling_04_alpha_dif.tga.8_8b.trim` | 6705 | embedded | FULL | - |
| 511 | `effects/textures/t_smoke_rolling_06_alpha_dif.tga.8_8b.trim` | 6705 | embedded | FULL | - |
| 512 | `effects/textures/t_smoke_rolling_06_alpha_dif.tga.8_8bb.trim` | 6705 | embedded | FULL | - |
| 513 | `effects/textures/t_smoke_rolling_top_04_alpha_dif.tga.8_8b.trim` | 6705 | embedded | FULL | - |
| 514 | `effects/textures/t_spark_ash_s2_alpha_dif.tga.2_2b.trim` | 945 | embedded | FULL | - |
| 515 | `effects/textures/t_spark_ash_s2_alpha_dif.tga.2_2bb.trim` | 945 | embedded | FULL | - |
| 516 | `effects/textures/t_spark_bits_02_s2_alpha_dif.tga.1_4a.trim` | 945 | embedded | FULL | - |
| 517 | `effects/textures/t_spark_bits_02_s2_alpha_dif.tga.1_4b.trim` | 945 | embedded | FULL | - |
| 518 | `effects/textures/t_spark_bits_s2_alpha_dif.tga.1_4a.trim` | 945 | embedded | FULL | - |
| 519 | `effects/textures/t_spark_core_01_s2_alpha_dif.tga.1_1b.trim` | 657 | embedded | FULL | - |
| 520 | `effects/textures/t_sparks_blast_dif.dds.1_3a.trim` | 849 | embedded | FULL | - |
| 521 | `effects/textures/t_spherical_ramp.tga.2_4b.trim` | 1329 | embedded | FULL | - |
| 522 | `effects/textures/t_spherical_ramp.tga.8_8b.trim` | 6705 | embedded | FULL | - |
| 523 | `effects/textures/t_spherical_ramp.tga.8_8bb.trim` | 6705 | embedded | FULL | - |
| 524 | `effects/textures/t_splat_02_s2_alpha_dif.tga.2_2b.trim` | 945 | embedded | FULL | - |
| 525 | `effects/textures/t_velocity_streak_alpha_dif.dds.1_1b.trim` | 657 | embedded | FULL | - |
| 526 | `effects/textures/t_water_splash_01_alpha_dif.tga.1_1b.trim` | 657 | embedded | FULL | - |
| 527 | `effects/textures/t_water_splash_02_alpha_dif.tga.1_1b.trim` | 657 | embedded | FULL | - |
| 528 | `effects/textures/t_water_splash_03_alpha_dif.tga.1_4b.trim` | 945 | embedded | FULL | - |
| 529 | `effects/textures/temp/water_explosion_temp_alpha_dif.dds.4_8b.trim` | 3633 | embedded | FULL | - |
| 530 | `effects/textures/vfx_fireball_alpha_dif.tga.4_8a.trim` | 3633 | embedded | FULL | - |
| 531 | `effects/textures/vfx_fireball_alpha_dif.tga.4_8bb.trim` | 3633 | embedded | FULL | - |
| 532 | `effects/textures/vfx_flames_small_alpha_dif.tga.8_8a.trim` | 6705 | embedded | FULL | - |
| 533 | `effects/textures/vfx_flames_small_alpha_dif.tga.8_8ab.trim` | 6705 | embedded | FULL | - |
| 534 | `effects/textures/vfx_flames_small_alpha_dif.tga.8_8b.trim` | 6705 | embedded | FULL | - |
| 535 | `effects/textures/vfx_flames_small_alpha_dif.tga.8_8bb.trim` | 6705 | embedded | FULL | - |
| 536 | `editor/entities/jc_vehicles/00_shared/modules/default_extended_effect_usages.vmodc` | 627 | embedded | FULL | - |
| 537 | `editor/entities/jc_vehicles/00_shared/modules/health/lave_health_medium.vmodc` | 3741 | embedded | FULL | - |
| 538 | `editor/entities/jc_vehicles/00_shared/modules/vehicle_common.vmodc` | 12271 | embedded | FULL | - |
| 539 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/ai/v0300_car_kensington_sportsmuscle_ai.vmodc` | 1345 | embedded | FULL | - |
| 540 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/ai/v0300_car_kensington_sportsmuscle_brakes_ai.vmodc` | 523 | embedded | FULL | - |
| 541 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/ai/v0300_car_kensington_sportsmuscle_land_aerodynamics_ai.vmodc` | 445 | embedded | FULL | - |
| 542 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/ai/v0300_car_kensington_sportsmuscle_land_global_ai.vmodc` | 1494 | embedded | FULL | - |
| 543 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/ai/v0300_car_kensington_sportsmuscle_land_steering_ai.vmodc` | 1073 | embedded | FULL | - |
| 544 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_brakes.vmodc` | 548 | embedded | FULL | - |
| 545 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_buoyancy.vmodc` | 733 | embedded | FULL | - |
| 546 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_custom_land_global.vmodc` | 3399 | embedded | FULL | - |
| 547 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_custom_velocity_damper.vmodc` | 543 | embedded | FULL | - |
| 548 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_decals.vmodc` | 392 | embedded | FULL | - |
| 549 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_front_tire.vmodc` | 4678 | embedded | FULL | - |
| 550 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_land_aerodynamics.vmodc` | 478 | embedded | FULL | - |
| 551 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_land_audio.vmodc` | 286 | embedded | FULL | - |
| 552 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_land_engine.vmodc` | 1045 | embedded | FULL | - |
| 553 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_land_global.vmodc` | 1494 | embedded | FULL | - |
| 554 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_land_steering.vmodc` | 1073 | embedded | FULL | - |
| 555 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_palette.vmodc` | 1897 | embedded | FULL | - |
| 556 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_rear_tire.vmodc` | 4678 | embedded | FULL | - |
| 557 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_rigid_body.vmodc` | 992 | embedded | FULL | - |
| 558 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_suspension.vmodc` | 1563 | embedded | FULL | - |
| 559 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_transmission.vmodc` | 1455 | embedded | FULL | - |
| 560 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_vehicle_misc.vmodc` | 2332 | embedded | FULL | - |
| 561 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/generated/v0300_car_kensington_sportsmuscle_effect_attachments.vmodc` | 12163 | embedded | FULL | - |
| 562 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/generated/v0300_car_kensington_sportsmuscle_lights.vmodc` | 6337 | embedded | FULL | - |
| 563 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/generated/v0300_car_kensington_sportsmuscle_water_interaction.vmodc` | 4648 | embedded | FULL | - |
| 564 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_stunt_areas.vmodc` | 26645 | embedded | FULL | - |
| 565 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_vehicle_deform.vmodc` | 67214 | embedded | FULL | - |
| 566 | `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_vehicle_parts.vmodc` | 29886 | embedded | FULL | - |

## 4. Open items (every partial/named-only file a Batmobile requirement touches)

| requirement | files | grades | what is missing |
|---|---|---|---|
| FX (particle system definitions) | 4 | NAMED-ONLY 4 | no project script parses a .pfxc payload; the extension is only named (grep: _check_types/jc3sigdiff/jc3traffic list it, none opens it) |
| appearance (body/paint/damage textures) | 116 | PARTIAL 116 | container accounted (AVTX, 128 + 10936 == 11064) but no project decoder reads the payload: the texel block format id (u32[2] = 71) and the other header fields are not decoded, and tex2ddsc only ever writes formats 71/83 through ConvertTexture; container accounted (AVTX, 128 + 10944 == 11072) but no  |
| collision + physics (hulls, chassis mesh, wheel body table) | 1 | PARTIAL 1 | 430 objects, 16 classes; per class below |
| entity (the entity's component tree and properties) | 1 | PARTIAL 1 | ConvertProperty round trip is not byte-identical (109526 -> 109526 B, first diff at 0x765) |
| geometry (render meshes of every part) | 3 | PARTIAL 3 | no codec for a block: block 1 is GeneralMkIII, which this codec does not parse (need its serializer to know where it ends) |

## 5. UNKNOWN

* **`.ddsc` texel payload.** No project decoder reads it; the block format ids (`u32[2]` = 77 on the sampled files, 71/83 elsewhere per `tex2ddsc`) are not mapped to a format table, and the remaining header fields are not named. Where it would be answered: a ddsc reader (header -> DDS shape, element table, mip chain) with the element sizes as its oracle.
* **`.pfxc` payload.** Nothing in the project opens one; where it would be answered: a PFX container reader, then the particle records against `FX.md`.
* **`hknpShapeMassProperties`.** The class is typed but its fields are not; where it would be answered: an object dump with the 4x4 inertia tensor as the check (symmetric, positive definite, and the total mass summing to the body entry).
* **`hknpExternMeshShape` vertex frame.** Counts and AABBs are exact; the de-quantization frame is not pinned, which is what blocks authoring a chassis mesh by hand (PHYSICS_WRITE.md).
* **ADF member semantics.** Every byte is accounted for 186 files, but a byte being read does not mean its *meaning* is known: `decode_depth` reports structure, and the semantic tables live in the per-feature docs (PARTS_TABLE, FX, LIGHT_SYSTEM...).

## Reproduce

```
python Tools/scripts/decode_depth.py --write
python Tools/scripts/decode_depth.py --check
```
