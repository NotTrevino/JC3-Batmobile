# Review — G3-04c (`COLOUR_PARAMS`: Mainbody-chain parameters, reworked from G3-04b)

Reviewer: independent (did not write the card). Date 2026-11-03. Read-only: I ran `--check` only,
never `--write` (it would have overwritten the card's outputs). No game launched or read; nothing
under `E:/Games` or `D:/Games` written.

Reviewed: `tmp/freebuff/reports/G3-04c.md`, `Research/BatmobileGrab/COLOUR_PARAMS.md`,
`Research/BatmobileGrab/COLOUR_PARAMS.json`, `Tools/scripts/grab_colour_params.py`.

---

## VERDICT: **minor issues**

The substance is right and it fixes the two defects `review-G3-04b.md` found. I re-read every
load-bearing number from `Playable_Batmobile_SF.upk` with `upk_read` and raw `struct` unpacking, and
all five spot-checks match, including the exact float bits behind the body base colour. The chain
start is independently reproducible (mesh slot array at payload 8287, 19 slots, slot 2 = 763), the
GUID pairing resolves 52/52, and the 2-byte array tail is at least reported.

Defects found are presentational or scoping, not wrong values: one literal `%d` in the generated
document, one imprecise sentence about export 683, one oracle that only inspects the writer's own
output, the unnamed 2-byte array tail missing from the UNKNOWN list, a quoted JSON size that does not
match the file, and one engine-semantic sentence (MIC inheritance) that carries no label.

---

## Check output (verbatim)

Command:

```
cd "E:/Modding/JC3-Batmobile" && PYTHONIOENCODING=utf-8 uv run --with numpy python Tools/scripts/grab_colour_params.py --check; echo "CHECK_EXIT=$?"
```

Output:

```
OK 3 chain steps, 52 overrides, 69 defaults, 52 pairing rows; 82/87 vector defaults, 142/181 scalar defaults; md+json byte-identical to a fresh rebuild
oracles: {"chain_ends_at_one_material": true, "chain_start_is_body_slot_mic": true, "every_override_pairs_by_guid": true, "no_derived_composite_value": true, "operator_graph_is_stripped": true, "pairing_agrees_on_name": true, "parameter_value_arrays_consume_their_payloads": true, "scalar_defaults_are_floats_at_0xcc": true, "texture_defaults_are_object_references": true, "vector_defaults_are_named_structs_at_0xcc": true}
combine rule: UNKNOWN - 944 expression slots, 0 non-zero
CHECK_EXIT=0
```

This matches the report's quoted check block line for line, and the exit status is 0. `check()`
compares the stored JSON structurally against a fresh `build()`, compares the markdown string against
a fresh render, and re-runs all ten oracles — a stale or hand-edited output would fail here.

The report's `--write` block was **not** re-run (it would overwrite the card's outputs); its numbers
equal the check's, so nothing turns on it.

---

## Spot-checks (5 decoded values, re-read from the package)

Probe: `upk_read.Package` + `walk_tags` on the `*ParameterValues` payload, unpacked with `struct`.
Note `upk_read`'s item tags are payload-relative, so the array payload has to be walked from its own
base to reach the raw floats (my first two attempts read the wrong bytes; the values below are from the
corrected walk).

| # | value claimed | where I read it | match |
|---|---|---|---|
| 1 | MIC 767 `Material0_BaseColour` = `[0.025787, 0.025787, 0.03, 1]`, GUID `9620e42531864342`; `Diffuse_Adjust` = `[2.2, 2, 2, 1]` | `VectorParameterValues` (field 0x168, 12 items): items at payload 262 and 176; `StructProperty` @0x8, 16 B. Raw floats: `0.025786999613046646, 0.025786517187952995, 0.029999999329447746, 1.0`; GUID tail `9620e42531864342` | **yes** (6 dp faithful; see I-6) |
| 2 | 82/87 vector parameters carry a `StructProperty` **named `DefaultValue`**, 16 B, at 0xCC; the five without are 669, 683, 716, 720, 724 | every `MaterialExpressionVectorParameter` export (87) | **yes** — 82 with, tag name set = `{DefaultValue}`, size set = `{16}`; exceptions exactly `669 Anisotropic_Channel_Choice, 683 Main_BaseColour, 716 Material0_BaseColour, 720 Material0_BaseColour, 724 Direction` |
| 3 | scalars 142/181 with `FloatProperty` @0xCC; textures 56/56 with an object reference @0xAC | all 181 scalar + 56 texture parameters | **yes** (142, 56) |
| 4 | chain 763 → 767 → 359 `Batmobile_Worn`; mesh 5284 `Batmobile_V2` material array at payload byte **8287**, 19 slots, **slot 2 = 763** | MIC `ObjectNCRProperty` @0x84 in 763 (→767) and 767 (→359, class `Material`); independent containment scan of the mesh payload | **yes** — my own scan found exactly one candidate, at 8287, count 19, `refs[2]=763` (`Batmobile_V3_Mainbody_NEW_MIC`) |
| 5 | 69 parameter expressions outered to 359; 292 distinct GUIDs, 44 shared; `ExpressionGUID` is name 1310 | full package scan | **yes** — 69 outered to 359; 351 parameter expressions, 292 distinct GUIDs, 44 appear more than once; `names[1310] == "ExpressionGUID"` |

Extra values checked because they sit in the same table: MIC 763 `Mud_Opacity` = 50.0 and
`Mud_Edges_Opacity` = 100.0 (report rows 8/9) — **yes**.

---

## Issues

### I-1 (minor, generated-document defect) — a literal `%d`

`COLOUR_PARAMS.md:87` reads, verbatim:

> Each row is a `MaterialExpression*Parameter` outered to export **%d**.

The render append has no formatting: `Tools/scripts/grab_colour_params.py:578` —
`L.append("Each row is a \`MaterialExpression*Parameter\` outered to export %d. ...")`. Every other
number in the doc is interpolated; this one was missed. Fix: `% material_export` (359), then re-run
`--write` (the doc is generated, not hand-edited).

### I-2 (minor, imprecise claim) — export 683 is not named `Material0_BaseColour`

Report §1 item 2 says `Material0_BaseColour` resolves to "export 716 (same GUID also on 720 … and 683
…)", and UNKNOWN 2 calls 716/720/683 "the material's own expressions for it". The bytes say 683 is
`Main_BaseColour` in `Material_MASTERS.Batmobile_V3_Body_NoRain_MAT`:

```
767 Material0_BaseColour guid 9620e42531864342
  same GUID: expr 683  name ['Main_BaseColour']       outer Material_MASTERS.Batmobile_V3_Body_NoRain_MAT
  same GUID: expr 716  name ['Material0_BaseColour']  outer Material_MASTERS.Batmobile_Worn
  same GUID: expr 720  name ['Material0_BaseColour']  outer Material_MASTERS.Batmobile_Worn_NoRain
```

So the GUID is shared across a *different parameter name*, not only across materials. That does not
break the card — `pairing_agrees_on_name` is correctly scoped to expressions in the chain material,
and §4 states the (GUID, outer material) rule — but the prose must not call 683 an expression "for"
`Material0_BaseColour`. It also means the doc should say plainly that a GUID is not name-unique
across the package, which is the reason the pairing key includes the material.

### I-3 (minor, tautological oracle) — `no_derived_composite_value` cannot fail on the bytes

The oracle checks that its own output rows use only `float / linear_colour_4f / object_ref / none`
and that no key named `base_x_adjust`, `product`, `final_colour` exists in four top-level dicts. That
is a schema check of the writer: it would pass unchanged if the package gained a combine rule. The
byte-level support for "no combine rule" is oracle 10 (`operator_graph_is_stripped`, re-derived from
944 slots / 0 non-zero), which is sound. Suggest renaming oracle 9 to `no_composite_value_is_written`
and crediting the stripped graph for the claim, rather than listing it as a tenth byte oracle.

### I-4 (minor, unnamed residue) — the 2-byte array tail

Every present `*ParameterValues` array leaves `payload − consumed = 2` bytes
(`ScalarParameterValues:763` 584/582, `:767` 1280/1278, texture 120/118 and 352/350, vector 1036/1034).
The doc reports it per array, which is honest, but the two bytes are never named and do not appear in
the UNKNOWN list. The oracle's predicate tolerates `payload − consumed <= 2`, i.e. the tolerance is
set to the observed residue, so a decode that stopped 2 bytes early would still pass. Suggest adding
"the 2-byte tail of each parameter array (what it is; tried: item walk to terminator, trailing count/
version word)" to UNKNOWNs, and asserting `tail == 2` exactly with the value recorded.

### I-5 (minor, unlabelled engine semantic) — MIC inheritance

`COLOUR_PARAMS.md` §1 ends: "So a body-slot override is inherited from
`Batmobile_V3_WheelArchs_NEW_MIC` and, if not set there, from `Batmobile_Worn`." The parent links are
decoded; the *lookup rule* (a material instance inherits unset parameters from its Parent, nearest
first) is engine semantics, not a byte fact, and it is the premise the whole body-colour argument
rests on. Under the project rule it needs a label, e.g. `derived (rule: MIC parameter lookup follows
the Parent chain; engine semantic, asserted not proven here)`, or an explicit UNKNOWN. `767` does not
override nothing that `763` sets — everything the body needs is set in 767 — so the nearest-first
direction is not exercised by any decoded pair in this card.

### I-6 (nit) — 6-dp hides that the two channels differ

Raw: R = `0.025786999613046646`, G = `0.025786517187952995`. Both round to `0.025787` at 6 dp, so the
report's `[0.025787, 0.025787, 0.03, 1]` is faithful at that precision but makes the authored R and G
look identical. A 7-dp print (or the raw repr) would keep the distinction for anyone comparing this
value against a screenshot-derived constant later.

### I-7 (minor, wrong quoted size) — the JSON size in the report

`G3-04c.md` "Files written" gives `COLOUR_PARAMS.json` as **118,677 B**. The file on disk is
**121,499 B** (`ls -la`, mtime 06:01, same as the md). The md's 28,227 B is correct. Either the report
was written from an earlier build or the number was typed; it is a report-only error (the JSON itself
is consistent — `--check` re-derives it).

### What is right, and worth keeping

- The 82/87 fix, the tag name `DefaultValue`, size 16 at 0xCC, and the five exceptions: exactly the
  bytes, and exactly the correction `review-G3-04b.md` I-1 asked for.
- The GUID pairing removes the name-collision bug: `Diffuse_Adjust` now pairs to 711 (default
  `[1,1,1,1]`), not scalar 453; `Material0_BaseColour` pairs to 716. Both predictions from the earlier
  review are met.
- No derived composite: the JSON holds only single-tag values; no `base × adjust` anywhere.
- The chain start comes from the mesh slot, not from a document, and my independent scan reproduces
  the same offset (8287), count (19) and slot (2).
- `--check` is real: structural JSON compare, md string compare, all ten oracles re-run.

---

## Resolvable UNKNOWNs

| report's UNKNOWN | resolvable? | how, and what the bytes say |
|---|---|---|
| **1. The combine rule** (what multiplies what) | **NO — and now provably absent from the install's Batmobile packages** | Not in `Playable_Batmobile_SF` (944/944 slots zero). I also checked the other cooked Batmobile packages: `Playable_BatmobileMK2_SF`, `Playable_BatmobileJoker_SF`, `Playable_BatmobileFunhouse_SF`, `Showcase_Batmobiles_Standard`, `Showcase_Batmobiles_Jokerfied` each hold the same 11 functions with **944 slots, 0 non-zero**, and `Showcase_Batmobiles_MK2` 857/0, `Playable_Batmobile_Std_6_SF` 258/0. So the card's "needs uncooked content or the generated shader map" is the only remaining route; no cooked sibling has the links. |
| **2. The authored default of the body base colour** | **CLOSED negatively** — there is none in any Batmobile package | I scanned all seven Batmobile packages for `Material0_BaseColour` / `Main_BaseColour` vector parameters and checked each for a `DefaultValue` at 0xCC: **every one lacks it** (e.g. `Playable_Batmobile_SF` 683/716/720, MK2 720/753/757, Joker 945/964/997, Funhouse 756/775/808, the three Showcase packages likewise). So "no authored default exists" is a byte fact, not an open question; the override is the only value. Worth recording as such instead of leaving it as an UNKNOWN. |
| **3. Which parameter feeds which socket** | NO | In the stripped graph; same route as 1. |
| **4. Whether the MIC value is what the shader receives** | NO, not without a runtime read | The G3-02d sampler does not record material parameters; a runtime oracle would need a new sampler field (G3-07 territory). Note the value's *existence* is not in doubt — only the shader hand-off. |
| **5. Texture pixel contents** | NO (not this card) | Assets; a different extractor (G3-12 decode-depth work), out of the colour-parameter scope. |
| **6. Lighting / probe / tonemap** | NO | Shader code; unchanged from `COLOUR.md` §5-6. |

---

## Summary

Minimum to move this to "sound": fix I-1 (the `%d`), I-2 (683 is `Main_BaseColour`; state GUIDs are
not name-unique), I-7 (JSON size), and add I-4's tail to the UNKNOWN list. I-3 and I-5 are labelling
changes — the oracle name and the inheritance sentence. None touches a value: every number I re-read
from the package is the number the card reports.
