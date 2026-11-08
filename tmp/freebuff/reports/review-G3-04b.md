# Review — G3-04b "BmAK material function bodies"

Reviewer: independent (did not write the card). Date 2026-11-03. Read-only: the only file written is
this one. All byte probes were inline (`uv run python - <<PY`) against `Tools/scripts/upk_read.py`;
no scratch files, no game launched, no game folder written.

Reviewed artifacts:

| artifact | size | mtime |
|---|---|---|
| `tmp/freebuff/reports/G3-04b.md` | 9,446 B | 2026-11-03 02:59 |
| `Research/BatmobileGrab/COLOUR_FUNCTIONS.md` | 10,450 B | 2026-11-03 02:58 |
| `Research/BatmobileGrab/COLOUR_FUNCTIONS.json` | 184,570 B | 2026-11-03 02:58 |
| `Tools/scripts/grab_colour_functions.py` | 29,751 B | 2026-11-03 02:57 |

---

## VERDICT: **needs rework**

The central, load-bearing finding of the card is **correct and independently reproduced**: the 11
Batmobile `MaterialFunction` exports are 744–754 of `Playable_Batmobile_SF.upk`, each carries one
`FunctionExpressions` `ArrayProperty` at field 0x90, and **all 944 slots are zero**, with the payload
length exactly `4 + 4·count` on 11/11 (walk reaches `eof` on 11/11). That is a genuine dead end for the
operator graph, and the card reports it honestly.

What blocks a "sound" verdict:

1. **A `decoded` fact is false and it is load-bearing.** The card says vector parameter defaults
   "do not survive: 0/87 … no value tag at all". The bytes hold **82 of 87** vector defaults as a
   `StructProperty` (16 B = `FLinearColor`) at field **0xCC**, and BmSDK's own layout confirms
   `DefaultValue` at `Ptr+204` (0xCC). The decoder in `grab_colour_functions.py` only looks for
   `FloatProperty`/`VectorProperty` at 0xCC, so it cannot see them. This turns a decoded set of colours
   into UNKNOWN #4 and removes 82 values the card claimed were unavailable (its "153 without a value"
   is 71 once these are read).
2. **A `derived` value rests on the operator the card itself calls UNKNOWN.** `base x adjust` is the
   component-wise product of a base colour and `Diffuse_Adjust`, but whether the graph multiplies them,
   and in which slot order, is exactly what "combine(term…) = UNKNOWN" says is not in the bytes.
3. **Cross-material parameter pairing by bare name.** The terms table pairs MIC `Diffuse_Adjust`
   `[2.2, 2.0, 2.0, 1.0]` (a *vector* in MIC 767) with export 453, a **scalar** `Diffuse_Adjust`
   (2.0) in `Batmobile_V3_Tyre_V2_MAT` — a different parameter in a different material. The vector's
   real default is export 711 `[1,1,1,1]` in `Batmobile_Worn`. Same pattern for `Mud_Opacity`,
   `Mud_Edges_Opacity`, `Material0_Reflectivity`, `Material0_Roughness`.
4. **The `mic_parameter_match` oracle does not enforce what the report says it enforces**
   (`ok = bool(matched)`; it passes with 1 of 40).

Everything else checked out, including the census, the export indices, the outers, the class
histogram, the G3-04 correction quote, and the claim that `grab_colour.py` / `COLOUR.json` were not
touched.

---

## Check output

Command:

```
cd "E:/Modding/JustCause3/JC3-Batmobile" && PYTHONIOENCODING=utf-8 uv run --with numpy python Tools/scripts/grab_colour_functions.py --check; echo "EXIT=$?"
```

Output, verbatim:

```
OK 11 functions, 351 expressions, 40 MIC parameters matched
all FunctionExpressions slots zero: 944 slots, 0 non-zero
oracles: {'census_by_export_table': True, 'function_expressions_layout': True, 'expression_walk_eof': True, 'parameter_name_offsets_by_class': True, 'mic_parameter_match': True}
EXIT=0
```

This is identical to the block quoted in `G3-04b.md`, line for line, and the exit status is 0. The
check really did re-derive (it rebuilds the document and compares the JSON structure, renders the
markdown, and re-runs every oracle): a stale or hand-edited output would fail here.

One caveat on the report's wording of the check: it says the check asserts the JSON "re-derives
**byte-identically**". `check()` compares `json.dumps(fresh, sort_keys=True)` against the same
serialisation of the stored file — a structural re-derivation, not a byte comparison. The distinction
does not change the result, only the wording.

---

## Spot-checks (5 × decoded, read from the raw package myself)

Probe: `upk_read.Package(...)` + `pk.exports[i]` / `pk.data(i)` / `upk_read.best_walk(...)`, with the
array payload unpacked by `struct.unpack("<i", …)` directly. No function from
`grab_colour_functions.py` was imported or called.

| # | value claimed | where I read it | result |
|---|---|---|---|
| 1 | `Batmobile_Edge_FCT` = export 747, size 234, `FunctionExpressions` count 43, layout `4+4n` = True, 0 non-zero | export table row 747; tag stream: `GuidProperty` @0x54 (32 B payload), then `ArrayProperty` **@0x90**, name `FunctionExpressions`, size 176, count 43, payload at 0x38 of the object | **MATCH** (43 × 0 = 0 non-zero) |
| 2 | 11 functions, 944 slots, 0 non-zero, 11/11 layout | all 11 export records, raw slot unpack | **MATCH** (counts 88/87/121/43/95/84/11/12/24/198/181 = 944; nonzero 0 on all) |
| 3 | scalar defaults 142/181 as `FloatProperty` +0xCC | every `MaterialExpressionScalarParameter` export's tag stream | **MATCH** (142 exactly; the 39 without carry only bool/guid/name/material) |
| 4 | "Vector defaults **do not survive: 0/87**. … no value tag at all. … 0/87 carry one" | every `MaterialExpressionVectorParameter` export's tag stream | **NO MATCH — 82/87 carry `StructProperty` @0xCC, size 16** |
| 5 | `Material0_BaseColour` = `[0.02579, 0.02579, 0.03, 1.0]`, MIC 767 `Batmobile_V3_WheelArchs_NEW_MIC` | export 767, `VectorParameterValues` array (field 0x168, 12 items): item 3 is `NameProperty "Material0_BaseColour"` + `StructProperty` @0x8 (16 B) = `0.02579, 0.02579, 0.03, 1.0` | **MATCH** (value and owner both confirmed) |

Extra checks done while there (all matched): census for all four packages — `Startup.upk` 54
`MaterialFunction` / 3,702 `MaterialExpression`, `Engine.upk` 6 / 213, `BmGame.upk` 73 / 3,495 with
exactly `Batmobile_Decal_FCT`, `Batmobile_RemoveUVOffsets_FCT`, `BMBL_Smoothstep_Opt`,
`Batmobile_UI_Colors`, `Playable_Batmobile_SF` 11 / 351; package header 17,916,421 B, version 863,
licensee 32995, 5,490 exports, 3,151 names; class histogram 181/87/51/27/3/1/1 = 351 and all 351 are
`*Parameter` classes; unnamed exports `[663, 732]`; scalars 453/446/448/425/515/506 = 2.0 / 1.0 / 0.1 /
0.6 / 0.25 / 0.25 with the materials the tables name.

Spot-check 4 in detail, because it is the one that fails. Per-class tag fingerprints of all 87
`MaterialExpressionVectorParameter` exports:

```
n=63  BoolProperty@0x64  GuidProperty@0xb4  NameProperty@0xac  ObjectNCRProperty@0x68  StructProperty@0xcc size=16
n=14  GuidProperty@0xb4  NameProperty@0xac  ObjectNCRProperty@0x68  StructProperty@0xcc size=16
n=4   BoolProperty@0x64  GuidProperty@0xb4  NameProperty@0xac  ObjectNCRProperty@0x68
n=3   BoolProperty@0x64  GuidProperty@0xb4  NameProperty@0xac  NameProperty@0xc4  ObjectNCRProperty@0x68  StructProperty@0xcc size=16
n=2   BoolProperty@0x64  GuidProperty@0xb4  ObjectNCRProperty@0x68  StructProperty@0xcc size=16
n=1   GuidProperty@0xb4  NameProperty@0xac  ObjectNCRProperty@0x68
```

82 have the 16-byte struct; the five that do not are 669 `Anisotropic_Channel_Choice`, 683
`Main_BaseColour`, 716 `Material0_BaseColour`, 720 `Material0_BaseColour`, 724 `Direction`. The payloads
are colours, e.g. `Mud_Colour` 713 `[0.26317, 0.14198, 0.06772, 1.0]`, `Damage_Dirt_Colour` 707
`[0.41573, 0.38949, 0.33165, 1.0]`, `Diffuse_Adjust` 711 `[1.0, 1.0, 1.0, 1.0]`,
`Material1_Basecolour` 698 `[0.6236, 0.39245, 0.32978, 1.0]` — each the authored default that the MIC
overrides by a slightly different value (767's `Mud_Colour` `[0.26518, 0.14326, 0.06887, 1.0]`).

Corroboration that 0xCC is `DefaultValue` and not something else (BmSDK-AK, MIT, allowed input):

- `src/BmSDK/Generated/Engine/MaterialExpressionVectorParameter.g.cs:82-85` — `StructProperty:
  DefaultValue`, `FLinearColor`, `Ptr + 204` = 0xCC. Class `(size = 220)` = 0xDC; 0xCC + 16 = 0xDC.
- `MaterialExpressionScalarParameter.g.cs` — `(size = 208)` = 0xD0; FloatProperty at 0xCC + 4 = 0xD0.
- `MaterialExpressionParameter.g.cs:82-94` — `ParameterName` at `Ptr + 172` (0xAC) and
  `ExpressionGUID` at `Ptr + 180` (0xB4), i.e. exactly the offsets the script reports.

So the 0xCC slot is the class's serialised default, the type is `FLinearColor`, and the values read as
authored colours. This is not an inference from UE3 knowledge; it is BmSDK's own field layout plus the
serialised tag offset agreeing with the class size arithmetic.

---

## Issues

### I-1 (major, wrong `decoded` label) — vector defaults

- **Where:** `G3-04b.md` "The parameter layer" bullet 3 and UNKNOWN 4; `COLOUR_FUNCTIONS.md` §3
  ("vectors **0/87** … **no default colour at all**") and §6.3; JSON
  `expressions.vector_with_default = 0`, `without_value = 153`.
- **Claim:** `MaterialExpressionVectorParameter` "serialises name, guid, bool and material and no value
  tag at all - 0/87".
- **Bytes:** 82/87 serialise a 16-byte `StructProperty` at 0xCC (`DefaultValue`, `FLinearColor`).
- **Cause:** `num_tag()` tries `FloatProperty` then `VectorProperty` at `OFF_FLOAT = 0xCC`; the game
  writes the vector default as a `StructProperty` (`LinearColor`), so the lookup returns
  `{"kind": "none"}` and the exporter reports 0. The script's docstring even states this as a design
  decision ("vector parameter: **nothing** - no Float/Vector/Struct value tag exists in its stream"),
  which the bytes contradict.
- **Consequences:** 82 colour values that *are* in the package are declared UNKNOWN; "153 without a
  value" should read 71; UNKNOWN 4 ("only MIC overrides exist") is wrong for 82 of 87 parameters.
- **Fix:** recognise `StructProperty`@0xCC (16 B) as the vector default, report
  `vector_with_default = 82/87`, and list the five that genuinely lack one (669, 683, 716, 720, 724).
  Note that the *body's* two relevant ones — `Main_BaseColour` 683 and `Material0_BaseColour` 716/720 —
  are in that five, so the body-colour conclusion survives; the general claim does not.

### I-2 (major, `derived` over-reach) — `base × adjust`

- **Where:** `G3-04b.md` §"The parameter layer" code block and `COLOUR_FUNCTIONS.md` §4:
  `base x adjust = [0.056738, 0.05158, 0.06]   [derived: component-wise product …]`.
- **Problem:** the multiplication is a hypothesis about the graph. The same block says
  `combine(term...) = ? [UNKNOWN: FunctionExpressions links are 0]`. If the combine rule is unknown then
  the product cannot be "derived"; it assumes (a) that `Diffuse_Adjust` multiplies base colour, (b) that
  it applies per component to RGB, (c) that the two are in the same slot. None of the three is in the
  bytes.
- **Task-rule impact:** this is the exact pattern the reset forbids — a rule invented to bridge a gap
  and then labelled derived. Label it `hypothesis (unproven: operator not in the bytes)` or drop it.
- Also: `Diffuse_Adjust`'s MIC value is a *vector* override `[2.2, 2.0, 2.0, 1.0]`; its authored
  default is `[1,1,1,1]` (711). Nothing in the package says the two are combined by multiplication.

### I-3 (major, data-association bug) — parameters matched by name only

- **Where:** `COLOUR_FUNCTIONS.md` §3 table (13 rows) and JSON `body_colour.terms`.
- **Problem:** `match_mic()` intersects bare parameter-name strings, ignoring class and material, so a
  MIC override is attached to an unrelated expression that happens to share the name. Verified cases:

  | parameter | MIC (object) | expression the table shows | actual same-name parameter being overridden |
  |---|---|---|---|
  | `Diffuse_Adjust` | vector `[2.2,2.0,2.0,1.0]` (767) | export **453**, `MaterialExpressionScalarParameter` 2.0, `Batmobile_V3_Tyre_V2_MAT` | export **711**, vector `[1,1,1,1]`, `Batmobile_Worn` |
  | `Mud_Opacity` | 50.0 (763) | export 446, 1.0, `Batmobile_V3_Discbreak` | same-name scalar in the MIC's own parent chain (not 446) |
  | `Mud_Edges_Opacity` | 100.0 (763) | export 448, 0.1, `Batmobile_V3_Discbreak` | as above |
  | `Material0_Reflectivity` | 0.2 (763) | export 515, 0.25, `Batmobile_Worn` | 515 is the right *material*, but the table implies one parameter; the MIC scalar is 0.2 vs default 0.25 — fine as a pair, but the pairing method is the same name-only one |

  `Wetness_Refl_Fresnel` (0.6 vs 0.6) happens to agree, which is luck, not proof.
- **Ready-made fix (resolvable from the bytes):** `FVectorParameterValue`/`FScalarParameterValue` items
  carry an `ExpressionGUID` that equals the expression's own `GuidProperty` (`MaterialExpressionParameter.
  ExpressionGUID` @0xB4, BmSDK `MaterialExpressionParameter.g.cs:91-94`). I verified two:
  MIC 767 `Material0_BaseColour` GUID `…f36abc2b…` == export 716 GUID (and 720, same GUID),
  MIC 767 `Diffuse_Adjust` GUID `…5fda350d…` == export **711** GUID — not 453. Matching on
  `(name, GUID)` (or GUID alone) removes the collision and makes the oracle strong.

### I-4 (minor, oracle weaker than the report claims) — `mic_parameter_match`

- **Where:** `grab_colour_functions.py` `build()`, `"mic_parameter_match": {"ok": bool(mm["matched"]), …}`.
- **Problem:** the report says this oracle proves "**40 of 40** … none missing". The predicate is true
  as soon as **one** name matches; 39 losses would still print `True`. The *numbers* are right
  (`matched 40`, `in_mic_not_in_expressions []`), but the check cannot protect them.
- **Fix:** `ok = len(mm["matched"]) == mm["mic_parameters"] and not mm["in_mic_not_in_expressions"]`,
  and assert both sets in the detail (the detail already carries `in_mic_not_in_expressions` but the
  assertion ignores it).

### I-5 (minor, overstated decode claim) — "the declared size equals the tag stream exactly"

- **Where:** `G3-04b.md` §"Card step 2"; `COLOUR_FUNCTIONS.md` §2.
- **Bytes:** every one of the 11 walks stops with `eof` at `size − 2` (232/234, 408/410, 544/546,
  232/234 …). Two bytes at the tail are never consumed, on all 11, consistently.
- **Effect:** the arithmetic "234 B = 4+4·43 payload + tags" is 2 bytes short. The conclusion (the
  array is complete and the slots are real, not a decoder desync) is unaffected — the tail is constant
  and after the last tag — but "equals exactly" is not what the bytes show. Say "size − 2, with a
  constant 2-byte tail".

### I-6 (minor, missing derivation step) — whose colour is the "body colour"?

- **Where:** `G3-04b.md` "Body colour as far as the bytes go" and `COLOUR_FUNCTIONS.md` §4.
- **Issue:** the value is an override in `Batmobile_V3_WheelArchs_NEW_MIC` (767), not in the body-slot
  MIC `Batmobile_V3_Mainbody_NEW_MIC` (763) — 763 has no `VectorParameterValues` array at all
  (only `ScalarParameterValues` 10 and `TextureParameterValues` 2). Calling 767's value "the body
  colour" therefore needs one more step, and that step is in the bytes: MIC 763 carries an
  `ObjectNCRProperty` at 0x84 whose value is **767** (`ref_class MaterialInstanceConstant`), i.e. the
  body MIC inherits from the wheel-arch MIC. Both documents and the report skip this, so the reader
  cannot tell whether the number is inherited or just borrowed.
- **Fix:** cite the 0x84 reference (763 → 767) as the inheritance link, then the value is defensible
  as inherited; without it, the label should be "wheel-arch override, body value UNKNOWN".

### I-7 (cosmetic) — docstring slot count

`grab_colour_functions.py` module docstring says "**1,115 slots** over the 11 functions". Measured and
printed: **944** (88+87+121+43+95+84+11+12+24+198+181). The script's own output is right; the prose
above it is not.

### I-8 (minor, unexplained delta) — the card said 12 functions, the card found 11

The card's evidence paragraph names 12 `MaterialFunction`s (including `rain_effect_V2_Optimised`). The
package has **exactly 11** `MaterialFunction` exports, all Batmobile-named, and the 11th is
`rain_effect_V2_Batmobile`, not `…_Optimised`. The card is therefore *better* than its own evidence,
but it never says so, leaving the reader to wonder whether a 12th was missed. One sentence closes it:
"the package holds 11 `MaterialFunction` exports in total; the card's count of 12 was an over-count,
and the name is `rain_effect_V2_Batmobile`".

### I-9 (not an issue, recorded because it looks like one) — G3-04 correction

The quoted `COLOUR.json` note is accurate: `"the array is not at the recorded offset and the
containment search over the package image found 0 candidate(s) for 237 expressions"`. The new count of
351 expression exports in the same package is right, and all 351 are parameter classes, so the earlier
"0 of 237" was indeed an access-path miss. The report's phrase "searched one array offset inside the
function bodies" is a gloss on the recorded note rather than a quoted fact; it is consistent with what
`COLOUR.json` says ("the array is not at the recorded offset"), so I would keep it but mark it as the
card reviewer's reading, not a byte fact.

### Housekeeping verified

- `Tools/scripts/upk_read.py` mtime **2026-10-25 06:23** (unchanged by this card, as claimed);
  `grab_colour.py` 02:10 and `COLOUR.json` 02:11 predate the card's 02:57–02:59 writes (untouched).
- `Working/Translation/LEDGER_AUDIT2.md` 29,495 B, `.json` 148,703 B, `G3-11b.md` 15,618 B, all
  02:44 — exactly the sizes the report quotes in its last section.
- The card does not modify `GRAB_BACKLOG.md`, `MODLOG.md`, `STATUS.md` or any earlier research file as
  far as the artifacts show; new files are only the four it names.

---

## Resolvable UNKNOWNs

| report's UNKNOWN | resolvable? | how, and what the bytes say |
|---|---|---|
| **4. Vector parameter default values** — "0/87 carry a value tag; only MIC overrides exist" | **YES — today, from the same package** | Read `StructProperty`@0xCC (16 B `FLinearColor`) on each `MaterialExpressionVectorParameter`. 82/87 decode; five have none (669, 683, 716, 720, 724). BmSDK `MaterialExpressionVectorParameter.g.cs:82-85` names that field `DefaultValue` at `Ptr+204`. This is the fix for I-1 and it removes the need for uncooked content for these 82 values. |
| **6. "Whether the missing links are a licence-specific cooker setting or this build" — "only one BmAK install is in scope, so there is no second sample"** | **PARTLY — yes, there are second samples in the same install** | The same 11 functions with the same counts appear in six other cooked Batmobile packages, all zero: `Playable_BatmobileMK2_SF` (exports 787-797, 944 slots), `Playable_BatmobileJoker_SF` (1009-…, 944), `Playable_BatmobileFunhouse_SF` (832-…, 944), `Showcase_BatmobileMK2` (10 MF, 857 slots — one function short), `Showcase_Batmobile_Standard` (11, 944), `Showcase_Batmobile_Jokerfied` (11, 944); `Playable_Batmobile_Std_6_SF` holds 3 of them (258 slots) plus a `Batmobile_FearSand_FCT` (94 slots) that is not in the base package. **Total non-zero slots across all of them: 0.** So the stripping is systematic for this cooker/build, not a one-package accident — but a non-cooked sample still does not exist, so the "cooker setting vs build" wording stays open. (A plain `grep` of the directory cannot answer this: packages are chunk-compressed, `grep -c "Batmobile_Edge_FCT"` finds 0 hits even in the package that owns the name. It has to be `upk_read`.) |
| **2. Which parameter feeds which socket** (partly) | **PARTLY — identity yes, sockets no** | `ExpressionGUID` (`MaterialExpressionParameter` @0xB4) in the MIC array item equals the expression's `GuidProperty`; verified for `Material0_BaseColour` (767 ↔ 716/720) and `Diffuse_Adjust` (767 ↔ 711). That proves *which* expression an override targets — enough to kill the I-3 name collision — but says nothing about which socket it feeds, which still needs the stripped links. |
| **1. The operator graph** | **NO** (confirmed dead end, and now narrower) | Not in `Playable_Batmobile_SF`, and not in any of the seven other Batmobile packages tested (all zero). It is not recoverable by re-reading these packages; the card's "uncooked content or the shader map" is the right place. One addition: `Startup.upk` (434 MB) was included in the card's census but I did not re-read it for slot values — only its `MaterialFunction` count (54), which matched. |
| **3. The functions' own output pins** | **NO** | Each `MaterialFunction` export serialises exactly two tags (a 32-byte `GuidProperty` @0x54 and the `FunctionExpressions` array @0x90). There is no pin data at all in the export, so the absence is a byte fact, not a decode gap. Worth stating that way. |
| **5. Lighting / reflection / tonemap** | **NO** | Shader, as the card says; unchanged from `COLOUR.md` §5-6. |

---

## Summary of what would move this to "sound"

Minimum: fix I-1 (vector defaults), I-2 (relabel the product), I-3 (GUID-based matching), I-4 (assert
40/40). I-5 to I-8 are one-line wording/count corrections. None of them changes the card's honest
headline — that the graph is stripped — but I-1 in particular means the card currently reports 82
decoded colours as absent, which is the kind of inversion the reset exists to prevent.
