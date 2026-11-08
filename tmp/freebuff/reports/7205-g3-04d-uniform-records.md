# G3-04d · material uniform records vs the CarPaintMM parameters

STATUS: done — the 6,966 proven uniform records name parameters and carry values, but no record
maps a name to a cbuffer offset, slot or bind; 0 entries name any of the 32 CarPaintMM
`cb2`/`cb6` members, and the Jenkins hashes of `BaseColour` / `Diffuse_Adjust` resolve to
nothing. The paint colour combine rule therefore stays UNKNOWN. 12/12 oracles pass.

## Files written

| file | what |
|---|---|
| `Tools/scripts/jc3_uniform_records.py` | new pass; `--write` / `--check` (re-derives every number from the install file and compares the page byte for byte) |
| `Research/JC3Grab/UNIFORM_RECORDS.md` | the generated page: layout, census, paint family, names/hashes, oracles, UNKNOWNs |
| `tmp/freebuff/reports/7205-g3-04d-uniform-records.md` | this report |

Nothing else was edited. Read-only input: `E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole/CombinedShaderCache-PC-D3D-SM5.upk` (21,268,515 B, sha1[:16] `c7b2759c9eddcc38`).

## 1. What the records are (decoded)

```
record := i32 n; u8[n] name; u8[16] guid; u8[16] zero; u32 count; entry[count]
entry  := u32 class; u32 class_number; u32 parameter; u32 param_number; f32[4] value
```

Measured over the region after the last DXBC container (`0x8ab3e03`):

| measurement | value |
|---|---:|
| candidate offsets tested | 13,486 |
| headers where the predicate holds | 7,278 |
| records proven end to end (count x 32 B) | **6,966** |
| headers that leave the 32 B shape (reported, not decoded) | 312 |
| entries | **9,582** |
| entry bytes / record bytes | 305,472 / 764,817 |
| every record span == `40 + n + 32 x count` | 6,966 / 6,966 |
| distinct entry class | 2055 only (`FMaterialUniformExpressionVectorParameter`) |

The 6,966 / 9,582 numbers agree with the earlier G3-04e1 format pass; the older 6,934 figure
was that pass's 60-character name cap, not a different layout.

## 2. Which records belong to the paint family

Definition used: a record that carries a BmAK paint parameter (`BaseColour` / `Basecolour` /
`Diffuse_Adjust`). Five records match:

| record | offset | entries | paint parameters named |
|---|---|---:|---|
| `Batmobile_MK2_WheelArch_MAT` | `0x8b010ca` | 10 | `Diffuse_Adjust` |
| `Batmobile_Worn` | `0x8bc1f56` | 14 | `Diffuse_Adjust`, `Material0_BaseColour`, `Material1_Basecolour`, `Material2_BaseColour`, `Material3_BaseColour` |
| `JasonTodd_Civilian_Master_MAT_APEX` | `0x911479e` | 5 | `demonized_base_colour` |
| `Demon_Civilian_Master_MAT` | `0x91718bf` | 2 | `demonized_base_colour` |
| `Red_Hood_Excavator_MASTER` | `0x930a8fc` | 4 | `Diffuse_Adjust` |

`Batmobile_Worn` is found independently by GUID `5e56a7942acfba4493fbad0c769a1976`, and its 14
values reproduce all 12 declared defaults in `COLOUR_PARAMS.json` at 1e-4 (0 mismatches). Its
`Material0_BaseColour` is `[0.0, 0.0, 0.0, 1.0]` and `Diffuse_Adjust` is
`[1.0, 1.0, 1.0, 1.0]` — the parent material's defaults, not the MIC overrides.

## 3. Names and hashes vs the BmAK parameters

`hash_jenkins` (`Tools/scripts/rbmhdr.py`, the project's archive-path Jenkins function):

| BmAK parameter | hash (dec) | hash (hex, masked) | in the package name table as a string | hash used as an FName index | hash as a u32 anywhere in the region |
|---|---:|---|---:|---:|---:|
| `BaseColour` | 3472103038 | `0xcef47f7e` | no (0 occurrences) | no | 0 |
| `Diffuse_Adjust` | 2130409324 | `0x7efa4c6c` | **yes**, name-table index 1283 | no | 0 |

A parameter is written as an FName index, not a hash, so a hash cannot be the binding; the
comparison above is exhaustive: the hash value occurs 0 times as raw LE bytes in the 9.9 MB
region.

Of the 32 CarPaintMM members named in `Research/JC3Grab/CB0_SLOTS.md` §3–§4 (25 `cb2` + 7
`cb6`; `cb7`'s two slots have no member names in that page), **0** occur as a parameter in any
record. Expected: those are JC3 reflection-header names, these are Arkham material names.

## 4. The oracle: is there a name -> offset field?

| entry word | distinct | min | max | non-zero | constant across the 300 names that occur more than once |
|---|---:|---:|---:|---:|---:|
| `class_id` | 1 | 2055 | 2055 | 9,582 | 300 / 300 |
| `class_number` | 1 | 0 | 0 | 0 | 300 / 300 |
| `param_index` | 696 | 3 | 5055 | 9,582 | 300 / 300 |
| `param_number` | 5 | 0 | 5 | 46 | 289 / 300 |

A slot field would show up as a per-name constant integer over `cb2`'s 0..316-byte span, in an
entry that has only four integers. The only per-name constants are the name's own index and the
FName number, whose whole range is 0..5; **0 entries carry any number word in the range 8..316**,
and there is no fifth field because `span == 40 + n + 32 x count` for every record.

So the answer to the card's question: the records name the parameters, and they do **not** map a
name to a `cb2`/`cb6`/`cb7` slot or offset; the only name→offset table on disk is the JC3
reflection header set that `CB0_SLOTS.md` already decoded.

## 5. Commands and output, verbatim

```
$ python Tools/scripts/jc3_uniform_records.py --write
wrote Research\JC3Grab\UNIFORM_RECORDS.md: 6966 records, 9582 entries, 5 paint records, 12/12 oracles

$ python Tools/scripts/jc3_uniform_records.py --check
ok: 6966 records, 9582 entries, 5 paint records, 12/12 oracles, page matches
```

Oracles in the page (all **PASS**): `headers_are_self_delimiting`,
`every_entry_is_the_vector_class`, `every_entry_is_32_bytes`, `guids_are_distinct`,
`anchor_found_by_guid`, `anchor_reproduces_the_declared_defaults`,
`no_entry_names_a_carpaintmm_cbuffer_member`, `no_record_maps_a_name_to_a_cbuffer_offset`,
`the_only_per_name_constant_is_the_name_index`, `name_numbers_cannot_encode_a_cbuffer_offset`,
`bmak_name_hashes_do_not_name_an_fname_index`, `region_has_no_slot_field`.

## 6. UNKNOWNs

1. **Which slot a paint parameter lands in.** Not in these records: 0 slot fields, 0 paint-member
   names, 0 hash hits. The cooker stripped `RDEF` from all 40,299 containers, so the binding
   needs a build that keeps `RDEF`, the cooker's shader map, or a live constant-buffer capture.
2. **How `BaseColour` and `Diffuse_Adjust` combine.** Values are present (see §2), the operator
   graph is not: the material functions' 944 `FunctionExpressions` slots are all zero
   (`COLOUR_PARAMS.md` §6). Needs the SHEX body or the graph.
3. **The 312 headers that leave the 32 B shape.** Reported, not decoded: the first entry there
   has a class word outside 2040..2055 or a parameter index outside the 5,058-name table; their
   widths are unproven. They carry no paint parameter (all 5 paint records are in the proven
   set), so the answer does not depend on them.

## COMPROMISES

None. All outputs are static file reads; no install, no game process, no writes outside
`Research/`, `Tools/scripts/` and this report.
