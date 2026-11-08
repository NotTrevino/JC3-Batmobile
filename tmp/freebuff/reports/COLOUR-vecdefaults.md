# DONE — COLOUR-vecdefaults (review of G3-04b, issue I-1)

STATUS: **done** — the review is upheld on the bytes: `Playable_Batmobile_SF.upk` holds **87**
`MaterialExpressionVectorParameter` exports, **82** of which serialise a default, and the default is a
`StructProperty` named `DefaultValue` at field **0xCC**, 16 B (four LE floats). G3-04b's "0/87 vector
defaults, no value tag at all" is a decoder miss. The 5 without a default are 669
`Anisotropic_Channel_Choice`, 683 `Main_BaseColour`, 716 `Material0_BaseColour`, 720
`Material0_BaseColour`, 724 `Direction`. Neither value the brief names is a default:
`BaseColour` [0.0258, 0.0258, 0.03] has no default anywhere (all three same-named expressions have
none, so only the MIC 767 override carries it), and `Diffuse_Adjust`'s own default is [1, 1, 1, 1]
(export 711) while [2.2, 2, 2, 1] is the MIC 767 override. The combine rule is untouched: UNKNOWN.

## Files written (the only files touched)

| path | what |
|---|---|
| `Tools/scripts/grab_vecdefaults.py` | new read-only script, `--write` / `--check`; rebuilds every number from the package bytes |
| `Research/BatmobileGrab/VEC_DEFAULTS.md` | generated report (23,139 B) |
| `tmp/freebuff/reports/COLOUR-vecdefaults.md` | this DONE report |

Read-only inputs: `E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole/Playable_Batmobile_SF.upk`,
`Research/BatmobileGrab/COLOUR_FUNCTIONS.md`, `Research/BatmobileGrab/COLOUR_PARAMS.md`,
`Tools/scripts/upk_read.py`, and BmSDK-AK's `Generated/Engine/MaterialExpressionVectorParameter.g.cs`
(MIT). No game was run or attached to; no build, no install, no git operation. The package's sha1 is
`c6e87dd0c06fbce956c0fd0adaebacef54e093a0`, matching the one `COLOUR_PARAMS.md` records.

## Commands run, with their output

```
$ cd /e/Modding/JC3-Batmobile && PYTHONIOENCODING=utf-8 python Tools/scripts/grab_vecdefaults.py --write
wrote Research\BatmobileGrab\VEC_DEFAULTS.md (22,863 chars, 22,871 B)

$ PYTHONIOENCODING=utf-8 python Tools/scripts/grab_vecdefaults.py --check
OK rebuilt byte-identical from the package and the two colour documents
```

Three wording/pointer defects were then fixed in the script (the five-without section pointer said §3
instead of §5; two prose numbers were hardcoded rather than computed; singular/plural of
"expression(s)"), and both modes re-run:

```
$ PYTHONIOENCODING=utf-8 python Tools/scripts/grab_vecdefaults.py --write; echo "WRITE_EXIT=$?"; PYTHONIOENCODING=utf-8 python Tools/scripts/grab_vecdefaults.py --check; echo "CHECK_EXIT=$?"
wrote Research\BatmobileGrab\VEC_DEFAULTS.md (23,106 chars, 23,115 B)
WRITE_EXIT=0
OK rebuilt byte-identical from the package and the two colour documents
CHECK_EXIT=0

$ PYTHONIOENCODING=utf-8 python Tools/scripts/grab_vecdefaults.py --write; echo "WRITE_EXIT=$?"; PYTHONIOENCODING=utf-8 python Tools/scripts/grab_vecdefaults.py --check; echo "CHECK_EXIT=$?"; echo ---; sed -n '/## 6\./,/## 7\./p' Research/BatmobileGrab/VEC_DEFAULTS.md; echo ---; sed -n '/## 8\./,/## 9\./p' Research/BatmobileGrab/VEC_DEFAULTS.md
wrote Research\BatmobileGrab\VEC_DEFAULTS.md (23,132 chars, 23,141 B)
WRITE_EXIT=0
OK rebuilt byte-identical from the package and the two colour documents
CHECK_EXIT=0
---
## 6. The two values the brief names, checked against the whole default set

Both are compared **by value** over all 82 defaults (max component difference <= 0.0005), not by
name, so a differently named expression carrying the same colour would still be found.

| target | value (COLOUR_PARAMS.md) | same-named expressions and their defaults | defaults matching the value | nearest default | distance |
|---|---|---|---|---|---|
| BaseColour | [0.0258, 0.0258, 0.03, 1] | 683 `Main_BaseColour` **no default**; 716 `Material0_BaseColour` **no default**; 720 `Material0_BaseColour` **no default** | 0 | 710 `EdgeMask_Colour` [0.1, 0.1, 0.1, 1] | 0.074200 |
| Diffuse_Adjust | [2.2, 2, 2, 1] | 711 `Diffuse_Adjust` [1, 1, 1, 1] | 0 | 743 `Electricity_Tiling` [1.5, 1.5, 1.5, 1] | 0.700000 |

**BaseColour.** ... Of the 3 expressions with that name, 3 carries **no default at all** (683, 716, 720).
...
**Diffuse_Adjust.** ... The single expression with that name (`Diffuse_Adjust`) carries a default: 711 [1, 1, 1, 1].
...
---
## 8. What is not claimed

- **No combine rule.** Re-counted only as a guard: 11 MaterialFunctions, 944 `FunctionExpressions` slots, 0 non-zero. ...
- **No claim that a default is what the shader receives.** ...
- **No socket mapping** ... the links are stripped, so that stays UNKNOWN.
- **GUIDs are not unique per export.** 13 of the 82 default GUIDs occur in more
  than one export (the body/worn copies share them), so a GUID names a parameter slot and cannot
  on its own tie one expression to one override [derived: §4 guid column].
```

That run exposed one remaining grammar slip ("3 carries"), fixed and re-run:

```
$ PYTHONIOENCODING=utf-8 python Tools/scripts/grab_vecdefaults.py --write; echo "WRITE_EXIT=$?"; PYTHONIOENCODING=utf-8 python Tools/scripts/grab_vecdefaults.py --check; echo "CHECK_EXIT=$?"; echo ---; grep -n "Of the 3 expressions\|single expression with that name" Research/BatmobileGrab/VEC_DEFAULTS.md; ls -la Research/BatmobileGrab/VEC_DEFAULTS.md tmp/freebuff/reports/SAMPLER-offline.md
wrote Research\BatmobileGrab\VEC_DEFAULTS.md (23,130 chars, 23,139 B)
WRITE_EXIT=0
OK rebuilt byte-identical from the package and the two colour documents
CHECK_EXIT=0
---
167:Of the 3 expressions with that name, 3 carry **no default at all** (683, 716, 720).
173:The single expression with that name (`Diffuse_Adjust`) carries a default: 711 [1, 1, 1, 1].
-rw-r--r-- 1 User 197121 23139 Nov  4 23:13 Research/BatmobileGrab/VEC_DEFAULTS.md
-rw-r--r-- 1 User 197121  9558 Nov  4 23:10 tmp/freebuff/reports/SAMPLER-offline.md
```

An inline byte probe was used before the script existed to confirm the count (87 params, 82 with a
16 B struct at 0xCC, five without) and to pick the reader API; it was scratch and is superseded — every
number it produced is reproduced by `--write` and asserted by an oracle in `--check`.

## Values, labelled

**decoded** (package + offset, or package + export + offset)
- `MaterialExpressionVectorParameter` exports: 87 (export table, class per export).
- 82 defaults: `StructProperty`, tag name `DefaultValue`, field offset 0xCC = 204, payload 16 B, four
  LE f32; value bytes at object offset 20 in each of the 82 (table in `VEC_DEFAULTS.md` §4).
- 5 without any default: 669, 683, 716, 720, 724 — each walks to `eof` with no `StructProperty` at
  any offset; 58 B or 66 B against 90 B for the smallest export that has one (§5).
- The 82 values themselves (§4), e.g. 711 `Diffuse_Adjust` [1, 1, 1, 1]; 698
  `Material1_Basecolour` [0.623595, 0.39245, 0.329779, 1]; 706 `Batman_Rain_Direction` [0, 0, -1, 0].
- Class layout agreement: 0xCC + 16 = 0xDC = 220, and BmSDK
  `MaterialExpressionVectorParameter.g.cs:8` declares `size = 220`, with `StructProperty: DefaultValue`
  at line 82 and `Ptr + 204` at line 85.
- 11 MaterialFunctions / 944 `FunctionExpressions` slots, 0 non-zero (only a guard; the operator
  graph is G3-04b's subject).
- The two target values' provenance: `COLOUR_PARAMS.md` §2 rows 37–38, both `FVectorParameterValue`
  items of MIC 767 `Batmobile_V3_WheelArchs_NEW_MIC` (field 0x168, item bytes 176 and 262).

**derived**
- 82 = 87 − 5, and the per-material census in §7 (counts of §4–§5).
- "Not among the 82 with the same numbers": both targets compared by value over all 82 defaults with
  a 5e-4 max-component tolerance; nearest to BaseColour is 0.0742 away (710 `EdgeMask_Colour`), to
  Diffuse_Adjust 0.7000 (743 `Electricity_Tiling`).
- 13 of the 82 GUIDs recur across exports, so a GUID names a slot, not an export.

**UNKNOWN**
- How the parameters combine (the 944/944 zero slots) — out of scope by the brief, unchanged.
- Which default is live at runtime, and whether the shader receives the default or a MIC override.
- Socket mapping (base colour / roughness / dirt), since the expression links are stripped.

## UNKNOWNs and what was tried

1. **Combine / routing.** Tried: re-count of `FunctionExpressions` per MaterialFunction (944 slots, 0
   non-zero). Still unknown because the cooked graph is stripped; it would be found in the uncooked
   material assets, which this project does not have.
2. **Whether the default is what renders.** Tried: reading every MIC override in `COLOUR_PARAMS.md`
   and the defaults here; they are separate stores with no recorded evaluation order. Would need a
   runtime probe, which the rules forbid.
3. **Why 5 exports lack a default** (e.g. whether 0xCC was simply never touched on those expressions).
   Tried: tag fingerprints for all 87 (§3) — the 5 lack the tag entirely rather than carrying a
   zeroed one; no earlier serialisation exists in the package, so the reason is not recoverable.

## Housekeeping

- `--check` passes and recomputes every number in `VEC_DEFAULTS.md` from the package (11 oracles:
  package header/sha1, the 87 vs `COLOUR_FUNCTIONS.md`, walk-to-eof, tag name/offset/size, the five,
  class size vs BmSDK, targets absent, `Diffuse_Adjust` white, operator graph still stripped).
- This brief named its DONE path, so it is not a `manual/claimed/` task file and there was nothing to
  move to `manual/done/` (INSTRUCTIONS §1).
- The earlier `SAMPLER-offline.md` (offline sampler-unknowns card) is present and its `--check` is green.
