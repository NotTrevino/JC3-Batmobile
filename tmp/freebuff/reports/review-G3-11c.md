VERDICT: needs rework

Narrow, but it is the project's one rule: the report presents ALB-2's combine
(`Material0_BaseColour` x `Diffuse_Adjust`) as **derived** and ships it in a proposed
ledger row whose confidence cell says **decoded**, while the project's own decode card
says the opposite in as many words - `COLOUR_PARAMS.md` §5: "**No product, sum or final
colour.** ... whether and how they combine is UNKNOWN ... G3-04b's `base x adjust` line
assumed a multiply and is not repeated here." The multiplication is an assumed operator,
so `derived` is the wrong label and `decoded` is a stronger wrong label.

Everything else the brief asked about holds: the gain **4** is a literal and is cited
correctly, the T-13 band **0.05–0.30 m** is a literal and is cited to the exact line, every
other T-13 constant's line number is exact, and `Tools/scripts/bm_*.py` contains **no**
constant named GAIN, CLEARANCE, SCALE or OFFSET at all, so nothing of that kind is missing
from the table.

Note also that this brief and `GRAB_BACKLOG.md`:1631 both describe the report as already
carrying the "guessed combine (operator UNKNOWN)" label. It does not. Either the correction
was recorded as done before it was written, or it was lost. I did not edit
`GRAB_BACKLOG.md` or `MISSING_ROWS.md`.

## The claims, re-read

### C1. "ALB-2 is a literal gain of 4" - HOLDS

`MODLOG.md`:5471 (§107 heading) and 5488, read verbatim:

```
5471: ## 107. ALB-2: the paint is readable in daylight. test-081
5488: Change (ALB-2, one variable): `PAINT_ALBEDO_GAIN = 4.0` - the linear colour is multiplied *before*
5489: sRGB encoding, so the stored byte goes 0x43/0x40/0x45 -> 0x83/0x7d/0x86 (67 -> 131). Only generated
```

`Working/Translation/MISSING_ROWS.md`:31 (in the §1 table):

```
| PAINT_ALBEDO_GAIN = 4 | literal | `MODLOG.md`:5488 (§107) - the one hand-entered number of ALB-2,
chosen after measuring test-080 (body 12/16 luma vs grass 85; reference car 22/22 vs road 12) |
```

Label **literal** is correct, and the line number 5488 is exact. The constant no longer
exists in code: the only occurrences of `PAINT_ALBEDO_GAIN` in `Tools/scripts/*.py` are
inside `missing_rows.py` (its regex over MODLOG and its own status text), so ALB-2's gain
is historical and MODLOG is the right source to cite.

### C2. "combined by a guessed rule (BaseColour x Diffuse_Adjust, operator UNKNOWN)" - DOES NOT HOLD

The report says the opposite. `MISSING_ROWS.md`:28-30:

```
| base colour [0.02579, 0.02579, 0.03, 1.0] | decoded | ... Material0_BaseColour on
  Batmobile_V3_Mainbody_NEW_MIC (via parent chain), x Diffuse_Adjust [2.2, 2.0, 2.0] |
| Diffuse_Adjust [2.2, 2.0, 2.0] | decoded | ... paint.source.base_colour - the multiplier is
  recorded there as the derivation input |
| effective colour [0.056738, 0.05158, 0.06] | derived | base x Diffuse_Adjust, 6 dp -
  `Tools/scripts/grab_values.py` (`paint.effective_base_colour`) |
```

and `MISSING_ROWS.md`:101-105 (`T-AB2`, the row a ledger owner would splice in):

```
| BmAK source | authored paint colour `Material0_BaseColour` = [0.02579, 0.02579, 0.03] linear x
  `Diffuse_Adjust` [2.2, 2.0, 2.0] |
| transform | x `Diffuse_Adjust`, then x gain, then sRGB encode |
| now | effective [0.056738, 0.05158, 0.06] |
| confidence | decoded |
```

`grep -ni "operator|guessed|hypoth"` over `MISSING_ROWS.md` and `MISSING_ROWS.json`
returns no qualifying text at all (only an unrelated LEDGER_AUDIT sentence and a
`"GUESSED": 0` counter). So the multiply carries no UNKNOWN label anywhere in the report.

What the evidence actually says - `COLOUR_PARAMS.md` §5, lines 227-231, verbatim:

```
## 5. What this document does not claim

- **No product, sum or final colour.** `Material0_BaseColour` and `Diffuse_Adjust` are two decoded parameters;
  whether and how they combine is UNKNOWN (next item). G3-04b's `base x adjust`
  line assumed a multiply and is not repeated here.
- **No combine rule.** The 11 Batmobile `MaterialFunction`s hold 944 expression slots,
  **0 non-zero** in this read, so no operator, input or output link is in the package.
```

`COLOUR.md`:171 hedges the same way: `, optionally x Diffuse_Adjust   [decoded, §2]` -
"optionally", i.e. not established.

Independently of `COLOUR_PARAMS.md`, my own card G3-04e1 (this session) measured that the
shader caches cannot supply the operator either: 0 `RDEF` chunks in 38,201 + 2,098 DXBC
containers, and each material record's entry is exhausted by `(class FName, parameter
FName, RGBA)` - no slot, no operator field (`Research/BatmobileGrab/UNIFORM_FORMAT.md`
§3/§8, `SHADER_COMBINE.md` §4). So the multiply has no decoded source in the project.

**Why this is "needs rework" rather than cosmetic.** `T-AB2`'s `confidence: decoded` is
what a ledger owner copies. It would enter the ledger as the claim "the paint colour is
BaseColour x Diffuse_Adjust, decoded" - a rule the project itself declared UNKNOWN. That is
the exact failure mode the reset exists to stop (`RESET_FINDINGS.md`:23, :53 call ALB-2's
chosen constant out by name). The fix is small: label the product *hypothesis* / *assumed
operator (UNKNOWN)* in §1 row 3, drop "x Diffuse_Adjust" out of the **decoded** cell in row
1 (leave it as a note), and set `T-AB2`'s confidence to something that does not claim the
operator is decoded. The arithmetic itself is right: 0.02579 x 2.2 = 0.056738, 0.02579 x
2.0 = 0.05158, 0.03 x 2.0 = 0.06.

### C3. "the T-13 clearance band 0.05-0.30 m is a literal" - HOLDS

`GRAB_BACKLOG.md`:1147-1148 (the T-13 Done rule), verbatim:

```
1147: Done: every object has a new transform; every transform is ≥ 0.05 m outside the hull and
1148: ≤ 0.30 m from the surface (stunt/entry) — checked by the script.
```

`Tools/scripts/t9_interaction.py`:50, verbatim:

```
50: BAND = (0.05, 0.30)         # the card's Done rule, metres
```

`MISSING_ROWS.md`:41:

```
| clearance band 0.05..0.3 m | literal | the card's Done rule (`GRAB_BACKLOG.md` T-13: "nearest hull
triangle >= 0.05 m and <= 0.3 m"), encoded at Tools/scripts/t9_interaction.py:50 |
```

Label **literal** is correct (the band is a card constant, not a game number) and the line
number 50 is exact.

### C4. The rest of the T-13 table - HOLDS, line numbers exact

`t9_interaction.py`:50-57 as read:

```
50: BAND = (0.05, 0.30)         # the card's Done rule, metres
51: SIDE_MARGIN = 0.06          # band floor + 10 mm so a re-measure stays above 0.05
52: SIDE_CLEARANCE = 0.10       # chosen, inside the band (donor side clearance is not decoded)
53: SIDE_Y = 1.15               # cockpit side height, m  (COCKPIT.md: tub y 0.676..2.029)
54: SIDE_Z = -0.95              # cockpit side station, m (Driver z -1.065)
55: ROOF_Z = -0.50              # roof centre = the canopy over the driver (COCKPIT.md §3)
56: HOOD_Z = -2.14              # front deck = the hood (G2-18 front_area centre station)
57: UP_COS = math.cos(math.radians(20.0))   # the card's "normals within 20 deg of up"
```

`MISSING_ROWS.md` cites :51, :52, :53, :54, :55, :56, :57 for exactly those constants, and
labels `SIDE_CLEARANCE` **literal/chosen** (correct - donor side clearance is in no decoded
file; `T9_INTERACTION.md`:25-26 says "0.1 m - chosen (band midpoint; donor side clearance
not decoded - UNKNOWN)"). The "`solve_offset`, 4 mm tolerance" claim (`MISSING_ROWS.md`:50)
is also exact: line 175 is `if abs(d - target) <= 0.004:`; the `0.006` on line 177 is a
band clamp margin, not the tolerance. The derived clearances check out against
`MISSING_ROWS.md`:50-51 (hood 0.1659, roof 0.1656) and `T9_INTERACTION.md`:61, :70.

### C5. Other chosen constants of the same kind - NONE MISSING

The brief's grep, run two ways over all 19 `Tools/scripts/bm_*.py`, returns **zero** hits:

```
$ grep -nE "[A-Za-z0-9_]*(GAIN|CLEARANCE|SCALE|OFFSET)[A-Za-z0-9_]*[[:space:]]*=" Tools/scripts/bm_*.py
(no output)
$ grep -rniE "(GAIN|CLEARANCE|SCALE|OFFSET)[A-Za-z0-9_]*[[:space:]]*=[[:space:]]*[-0-9]" Tools/scripts/bm_*.py
(no output)
$ grep -rn "PAINT_ALBEDO_GAIN" Tools/scripts/*.py        # definition anywhere?
Tools/scripts/missing_rows.py:120:    m_gain = re.search(r"`PAINT_ALBEDO_GAIN = ([0-9.]+)`", mod)
Tools/scripts/missing_rows.py:168:        "log": {"section": "MODLOG §107", "gain_line": line_of(MODLOG, r"`PAINT_ALBEDO_GAIN = "),
Tools/scripts/missing_rows.py:189:            {"value": "PAINT_ALBEDO_GAIN = %g" % gain_lit,
Tools/scripts/missing_rows.py:193:                       "road 12)" % line_of(MODLOG, r"`PAINT_ALBEDO_GAIN = ")},
Tools/scripts/missing_rows.py:476:                   "linear colour x `PAINT_ALBEDO_GAIN` **before** sRGB encoding",
Tools/scripts/missing_rows.py:649:    A("The one hand-entered number is `PAINT_ALBEDO_GAIN = %g`; everything downstream of it is "
```

So there is no `*_GAIN`, `*_CLEARANCE`, `*_SCALE` or `*_OFFSET` constant in any `bm_*.py`
for the report to have omitted. For completeness I inventoried every module-level numeric
constant in those files. The nearest same-kind literals all belong to *other* cards and
none is used by ALB-2 or T-13:

| file:line | constant | note |
|---|---|---|
| `bm_audio.py`:91,128 | `LUFS_TOL = 0.05`, `XFADE = 2048` | B-11's loudness tolerance / crossfade |
| `bm_budget.py`:32-33 | `CAP_KB = 4915.0`, `TARGET_KB = 4800.0` | budget (R9) |
| `bm_collision.py`:79 | `TOLERANCE_M = 0.05` | B-10 collision tolerance |
| `bm_colmesh.py`:51-52 | `DOMAIN_MARGIN = 0.05` (comment: decoded), `Q = 226.0` | B-10 codec |
| `bm_entity.py`:96-97 | `BASE_OBJECTS = 416`, `BASE_CLASSES = 43` | asserted censuses |
| `bm_fx.py`/`bm_parts.py`/`bm_lights.py` | `CAP_MODEL_KB = 4915.0`, `EMISSIVE_SLOT = 5`, `MAX_LODS = 8` | other cards' constants |

`MISSING_ROWS.md`:36-37 explicitly excludes MAT-1's gloss from the ALB-2 table ("not part
of ALB-2 and are not listed here"), which is the right call: MAT-1 is its own card.

### C6. The report's own oracle - PASSES

```
$ uv run python Tools/scripts/missing_rows.py --check
OK: ledger 198 rows, doc T-13 = 17 FX rows, doc T-13i = 0
OK: ALB-2 gain 4 -> 0x837d86 (literal, MODLOG:5488); current gain 3.4476 -> 0x7a757e in 58 RBM(s); ALB-2 byte bound by 0 RBM(s), named only in @files.xml
OK: T-13 85 objects, 77 placed all in 0.05..0.3 m, 6 dropped, 1 socket, 1 unknown; side clearance 0.1 chosen
OK: 8 proposed rows (T-AB1, T-AB2, T-AB3, T-IN1, T-IN2, T-IN3, T-IN4, T-IN5), each 8 cells
CHECK_EXIT=0
```

Its numbers reproduce, so the defect is a label, not arithmetic.

## Smaller items (fix while reworking C2)

1. **The Done-rule quote is not verbatim.** `MISSING_ROWS.md`:41 puts in quotes
   `"nearest hull triangle >= 0.05 m and <= 0.3 m"`; `GRAB_BACKLOG.md`:1147-1148 actually
   says "every transform is ≥ 0.05 m outside the hull and ≤ 0.30 m from the surface".
   Same meaning, but a quotation mark implies the source's words.
2. **"The one hand-entered number" contradicts the report's own table.** `MISSING_ROWS.md`:33
   correctly labels the sRGB EOTF constants `literal` ("hand-written in `srgb8()`, not read
   from any file"), and :34 says "The one hand-entered number is `PAINT_ALBEDO_GAIN = 4`;
   everything downstream of it is arithmetic." Two rows apart, the table lists two literal
   *kinds*. The intended claim is presumably "the one hand-entered number **of ALB-2's own
   choice**" (the sRGB constants being the standard's transfer). Worth rewording, since the
   whole point of the row is provenance.
3. **`VALUES.json`'s gain does not reproduce from its stated operands.** `albedo_gain` is
   3.4476 while 0.1837 / 0.0533 = 3.44653; `MISSING_ROWS.md` §6 flags this honestly
   ("the unrounded operands are not recoverable"), and the value *is* decoded (read from the
   file). No change needed to the label, but a reader should not read "vanilla luma /
   authored luma" as a derivation that reproduces 3.4476 to 4 dp.
4. **`GRAB_BACKLOG.md`:1631 is wrong about this report.** Its status cell reads
   "G3-11c | done (label corrected) | `MISSING_ROWS.md`: ALB-2 = literal gain 4 + guessed
   combine (BaseColour x Diffuse_Adjust, operator UNKNOWN)". The file does not say that.
   Whoever owns the backlog should re-open that cell when C2 is fixed; I did not edit it.

## What I could not check

* **Whether the multiply is decoded in a package G3-04c did not read.** I did not re-run the
  expression-slot measurement (`COLOUR_PARAMS.md`: "944 expression slots, **0 non-zero**");
  I cite that card. What I did verify independently is that the shader caches cannot carry
  the operator (my G3-04e1: 0 `RDEF` in 40,299 containers; record entries are
  `(class, parameter, RGBA)` only). A cooked package this project has not read could in
  principle hold the graph; nothing in the project claims it does.
* **Whether the ledger owner wants `T-AB2`'s cell to read `hypothesis` or the ledger's own
  vocabulary** (the audit uses `guessed`). That is a ledger-owner decision, not mine.
* **The splices themselves** (`T-AB1..T-IN5` into `T_ROWS.jsonl`) - the report proposes and
  `T_ROWS.jsonl` was not touched; its sha256/198 rows are asserted by `--check` and I did
  not re-hash it myself.
* **Pixel-level truth of the gain and the band** - both are chosen/derived for on-screen
  behaviour; no in-game check is possible in this project state (research reset).
