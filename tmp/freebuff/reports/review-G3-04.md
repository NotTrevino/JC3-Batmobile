# Independent review — G3-04 (BmAK colour pipeline)

**VERDICT: minor issues.** The chain, the base colour, the parameter attribution and the slot map
all reproduce from the bytes exactly as written, and the record is honest about shader-level
UNKNOWNs. Three defects need fixing: the record's headline UNKNOWN (the master's 237-expression
list) is **self-inflicted and resolvable**, the "tag offset" column reports a *native layout
offset* as if it located the value, and two lines of §6 cite evidence that is not in the document.

Artifact under review: `Research/BatmobileGrab/COLOUR.md` (12,452 B),
`Research/BatmobileGrab/COLOUR.json` (27,327 B), `Tools/scripts/grab_colour.py` (35,292 B).
I did not write this card and changed nothing outside this report.

## 1. `--check` output (verbatim)

```
$ cd /e/Modding/JustCause3/JC3-Batmobile && uv run --with numpy --with pillow --with pefile --with capstone python Tools/scripts/grab_colour.py --check; echo "CHECK_EXIT=$?"
OK chain 3, slots 5, expressions 1, terms 31, unknowns 6
oracle: 3 objects re-opened, 0 mismatches
CHECK_EXIT=0
```

## 2. Spot-checks — six values re-read from the raw source by me

Method: `upk_read.Package("…/Playable_Batmobile_SF.upk")`, `data(index)` + `walk_tags`, then the
array item payloads and the 4-byte reference array unpacked with `struct` by me.

| # | value in the record | my source | match |
|---|---|---|---|
| 1 | chain `763 → 767 → 359`, i.e. body MIC's parent is `Material_Worn.Batmobile_V3_WheelArchs_NEW_MIC`, whose parent is `Material_MASTERS.Batmobile_Worn` | export 763's `ObjectNCRProperty` (native 132) → `Material_Worn.Batmobile_V3_WheelArchs_NEW_MIC` (MaterialInstanceConstant); export 767's → `Material_MASTERS.Batmobile_Worn` (Material) | **yes** |
| 2 | master `Batmobile_Worn` export 359, "1798/2004 bytes parsed, 11 tags" | my walk: size 2004, **11 tags**, ends at 1798 | **yes** |
| 3 | `Material0_BaseColour` = [0.02579, 0.02579, 0.03, 1] | export 767, `VectorParameterValues` item `Material0_BaseColour`, struct `ParameterValue` raw `423fd33c3f3ed33c8fc2f53c0000803f` → 4 floats `(0.02579, 0.02579, 0.03, 1.0)` | **yes** |
| 4 | `Diffuse_Adjust` = [2.2, 2, 2, 1] | same array, item raw `cdcc0c4000000040000000400000803f` → `(2.2, 2.0, 2.0, 1.0)` | **yes** |
| 5 | slots: `DiffuseColor` etc. are null-with-mask; `EmissiveColor` → export 593 | master 359 `DiffuseColor` struct = `ObjectNCRProperty` **0** + `IntProperty` **2** (mask); `EmissiveColor` = `ObjectNCR` **593**; export 593 is class `MaterialExpressionStaticSwitchParameter` | **yes** |
| 6 | master expression list `Expressions` "not at the recorded offset … 0 candidate(s) for 237 expressions" | master 359: tag `Expressions` has **at=270**, `offset=2088`, `size=952`, `count=237`; at byte 270 the count reads **237** and `4 + 4×237 = 952` = the tag's size exactly; refs at 274…1222 resolve to **69** material expressions (37 `MaterialExpressionScalarParameter`, 19 `…VectorParameter`, 10 `…TextureSampleParameter2D`, 3 `…StaticSwitchParameter`), **168 are zero** | **count/array: yes; the record's UNKNOWN is wrong** |

Also checked, not part of the five: `VALUES.json.paint.base_colour` = `[0.02579, 0.02579, 0.03, 1.0]`
and ledger `T-MA3`'s cell "authored base colour `[0.02579, 0.02579, 0.03]` linear" — both agree with
the package value, so §2's "matches the package: **True**" is correct.

## 3. Issues

### I-1 (must fix — the record's headline UNKNOWN is self-inflicted)

- **Where:** `COLOUR.md` §4 "The master's own expression list" and §7 bullet 3 — *"the array is not
  at the recorded offset and the containment search over the package image found 0 candidate(s) for
  237 expressions"*; `COLOUR.json → expressions_inventory` (`count: null`, `unresolved: 0`).
- **Why it is wrong:** `grab_colour.py::expression_inventory` reads the count at `tag["offset"]`.
  That field is the **native class member offset** (2088 here), not a position inside the export —
  the export is 2004 bytes, so the read is out of range and the code falls back to a whole-image
  search whose acceptance test (`unresolved == 0` over all 237 refs) can never pass, because 168 of
  the 237 slots are null. The payload position is the tag's `at` field: **byte 270 of export 359**,
  where the array is byte-accounted (`4 + 4×237 = 952` = the tag's recorded size) and 69 references
  resolve to named expression classes. So the array is locatable and partly decodable today.
- **Fix:** read at `tag["at"]`, keep the byte-accounting test, and report both numbers honestly:
  "237 slots, 69 non-null references (histogram), 168 nulls". That also gives §4 real content
  instead of one expression, and changes §7's third bullet from "0 candidates" to the resolution
  count. `MaterialFunctionInfos` (at 1242, `count` 12, size 556) is the other array the record
  leaves undecoded and the natural place to look for the 12 functions G3-04b names.

### I-2 (must fix — a column that mislabels what it proves)

- **Where:** `COLOUR.md` §2, the `tag offset` column: `328` on every scalar row, `344` on every
  texture row, `360` on every vector row; and the prose "`Material0_BaseColour` … (decoded: export
  #767, tag offset 360)".
- **Why:** those numbers are the **array members' native offsets** (`ScalarParameterValues` at 328,
  `TextureParameterValues` 344, `VectorParameterValues` 360 — the same in exports 763 and 767), not
  the position of any value. Export 767's vector array actually starts at export byte **1692**; each
  item's `ParameterValue` struct sits at a per-item offset (32 in the item chunk). As printed, the
  column cannot take a reader to the bytes it claims to have decoded.
- **Fix:** cite `export + array payload offset (at) + item index` per row, or drop the column and
  state once that every value is in the named array payload.

### I-3 (should fix — provenance of the vector values is weaker than the label)

- **Where:** §2 "Vector (12)" table and §2's base-colour bullet.
- **Why:** the values are not a decoded `VectorProperty`; they come from `_floats()` on the
  `ParameterValue` **`StructProperty`, which the tag walker does not descend into** (`nested` walk
  returns `[]`). The 16-byte payloads are FLinearColor-shaped and the four floats are exact (I
  re-read both raws), but no field is named: which float is R, G, B, A is not established by any
  decoded tag. The record presents them as plain decoded vectors.
- **Fix:** keep the numbers, label the layout as "4 floats in a 16-byte `ParameterValue` struct,
  channel order not proven".

### I-4 (should fix — an inference inside a "decoded" label)

- **Where:** §7 bullet 2 — *"FMaterialInput.Expression is null with a mask, **so** the colour is
  produced inside the material's function graph"* — and §6's line
  `diffuse_input = master slot DiffuseColor -> expression(s) [decoded, §3/§4]`.
- **Why:** I verified the decoded part (null `ObjectNCR` + `Mask` 2 on `DiffuseColor`, masks 4 on
  `SpecularColor`). A null input proves only that **no expression fills that slot**; "therefore the
  colour is produced inside the material's function graph" is an inference with no byte behind it
  (the function list is I-1's array, still undecoded). And in §6 the diffuse input is marked
  "decoded" while the table three lines above shows it as `None`.
- **Fix:** say "no expression fills DiffuseColor (null + mask 2); where the body colour comes from is
  UNKNOWN until the expression/function arrays are decoded", and mark §6's diffuse line accordingly.

### I-5 (should fix — a citation with no referent)

- **Where:** §6 line `wetness_term = rain_effect material function on the master [decoded ref, §4]`.
- **Why:** §4 contains exactly one expression (export 593, `MaterialExpressionStaticSwitchParameter`,
  whose own parameter name is `Enable_Emissive`) and no rain/effect function reference. Nothing in
  the record shows a `rain_effect`-named function on the master, so the `[decoded ref, §4]` tag
  points at nothing. The master does carry `MaterialFunctionInfos` (12 entries, 556 B), which is
  presumably where the function references live — undecoded.
- **Fix:** either decode `MaterialFunctionInfos` and cite the entry, or mark the term UNKNOWN.

### I-6 (minor — decoded facts dropped from §4)

- **Where:** §4 table, row for export 593: `decoded fields: —`.
- **Why:** export 593 does carry decoded values: `NameProperty` = `Enable_Emissive`, a `GuidProperty`,
  `BoolProperty` = `True`, and two input structs `A`/`B`. They do not appear because the collector
  keeps only tags that have a `name`, and this package serialises simple types **unnamed** (the
  name lives in the property's native slot). "—" reads as "nothing decoded", which is wrong.
- **Fix:** record the unnamed simple-type values by native offset, as `COLLISION_CYLINDERS.md` does.

### I-7 (minor — epistemic label)

- **Where:** §2 "derived: base x adjust = linear [0.056738, 0.05158, 0.06] (rule: component-wise
  multiply, both factors decoded above)".
- **Why:** the arithmetic is right (I recomputed: 0.02579×2.2, 0.02579×2, 0.03×2) and both factors
  are decoded, but the *relation* — that `Diffuse_Adjust` scales the diffuse colour — is a
  hypothesis about the shader, not something a tag proves. §6 hedges it ("optionally x
  Diffuse_Adjust"); §2 does not. Agreement with `VALUES.json`/T-MA3 is a consistency check, not
  evidence for the relation.
- **Fix:** call it a hypothesis in both places, with "the operator is UNKNOWN" as §6 already says
  for the rest of the pipeline.

### I-8 (minor — a config row with no visible matching token)

- **Where:** §5 `wetness` table, row `BmGame/Config/BmInput.ini:244`, key `Bindings`, value
  `(Name="F8",Command="show postprocess")`.
- **Why:** the wetness rule is `wet|rain|puddle|damp`; the printed value contains none of them (the
  md truncates values at 120 chars, so the match may be later in a long binding list). Either way
  the row cannot be checked as printed, and as it stands it looks like a false positive in the term
  census. **Fix:** name the matched substring, or drop the row.

## 4. UNKNOWNs that the bytes can resolve (or that are correctly open)

| unknown (§7) | status |
|---|---|
| "the master's expression list … 0 candidate(s) for 237 expressions" | **Resolvable now**: read at the tag's payload position `at = 270` (not the native offset 2088). Byte account `4 + 4×237 = 952` closes; 69 refs resolve to classes, 168 are nulls. |
| "1 expression(s) carry neither Value nor DefaultValue: a static switch's chosen branch is not in the export" | **Partly resolvable**: export 593 carries `Enable_Emissive` (a `NameProperty`) and a bool `True`; the chosen branch is selected by that named switch plus the bool, both in the export — what is *not* there is which of `A`/`B` it selects, so the sentence should be narrowed to that. |
| "slot(s) … Function bodies live in `Material_Functions`/`Engine`" | Correctly open (G3-04b), but the *function roster* is local: `MaterialFunctionInfos`, 12 entries in the master itself. |
| tonemap / exposure / reflection "no ini key matched" | Correctly open at the colour-card level: these are engine/level terms; a wider config sweep (G3-03) or the engine package is where a key would appear, not in these bytes. |
| "a screen pixel value under named lighting: UNKNOWN" | Correctly open — needs a calibrated capture, which the project does not have. No file can resolve it. |
| lighting sum / tonemap operator | Correctly open (shader code, not serialised). |

## 5. What holds up

- **The chain is real**: both parent links are in the tag streams at native offset 132, and the
  classes are as stated (`MIC → MIC → Material`).
- **The base colour is the authored value**, byte for byte, and it agrees with `VALUES.json` and
  ledger `T-MA3` — the one place where the build's paint number is anchored to a file.
- **The parameter attribution is right**: export 763 carries 10 scalars + 2 textures, export 767
  carries 22 scalars + 6 textures + 12 vectors, and the merged table assigns every row to the object
  that actually carries it (child-wins, as stated).
- **The slot map and masks are decoded, not guessed** (`DiffuseColor` null + mask 2,
  `SpecularColor` + 4, `EmissiveColor` → 593).
- **The UNKNOWN discipline is otherwise good**: shader operators, screen values and engine terms are
  explicitly marked UNKNOWN rather than filled in, and `--check` enforces section presence, ledger
  agreement and drift.

Scope of this review: read-only. I ran `--check`, re-walked exports 763/767/359/593, unpacked the
vector parameter structs and the 237-entry reference array myself, and cross-read `VALUES.json` and
`T_ROWS.jsonl`. I did not decode `MaterialFunctionInfos`, did not re-derive the config term census,
and touched no file except this report.
