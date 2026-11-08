VERDICT: minor issues

The report's two load-bearing measurements reproduce: **all seven producer checks exit 0**
when I run them, and the **69 / 27 split of the 96 OPEN rows reproduces exactly** (69 rows
cite at least one of the seven files, 27 cite none). The **944-of-944 zero
`FunctionExpressions`** claim is verbatim the project's own oracle, so it holds.

Three things need fixing, none of which invalidates the pass:

1. **`T-B1` is labelled `grabbed` from `CHAIN.json`, but `CHAIN.json` does not carry its
   value.** The row's boost member is recorded with `"value": null`, and the `2.0` it
   proposes comes from `TANKTURN.md` - a file outside the seven that this pass did not
   check.
2. **34 of the 69 rows also cite a file outside the seven in their own `open_with`**
   (`TANKTURN.md`, `t16_collision.json`, `FX.md`), but the report's table lists only the
   seven-file for each. "69 rest on re-derivable evidence" is true and insufficient: for
   those 34, part of the evidence is unvouched.
3. **"It is now labelled assumed" is true of the report, not of `VALUES.json`.**
   `VALUES.json` has no label field at all; `effective_base_colour` has no `source` string.
   The label lives in `LEDGER_SOURCES.md` / `.json`.

Why not "needs rework": every number reproduces, the producer mapping is right, and the
mis-tagged row is one (plus two siblings that still hold on other grounds) out of 69. Why
not "holds": a provenance label contradicted by the cited file's own bytes is the one
thing this project does not tolerate.

## Claim 1. Seven producers, seven checks - HOLDS (7/7 exit 0)

Run by me in this session, each with its own exit status captured:

```
=== 1 CHAIN.json: bmak_chain.py --check ===
PASS: chain record current (105 objects, 9225 named bindings, 336 cross-checked, 0 conflicts, 0 bool words left unnamed)
EXIT=0
=== 2 VALUES.json: grab_values.py (default run; protected file backed up) ===
 }
}
EXIT=0
4d5a55dd643f15a599acdb5e7cf479bc84086315992694625f2b67045e3b9fde *Research/BatmobileGrab/VALUES.json
BYTES=identical
=== 3 VOCABULARY.md: jc3grab.py check ===
probe: 566 inner files, 30 modules decoded, 1 refused, mass=975, official_top_speed=250
check ok
EXIT=0
=== 4 PARTS_TABLE.jsonl: jc3parts.py check ===
ok: 40 part indices agree between .epe and DeformPoints; 4 wheel points -> 4 wheel parts; 21 light points -> 12 parts
ok: donor table has 42 parts, names 42/42 with DeformPoints, lights 12 parts match, wheels 4 match, damage types 17 used
  note: ['Boat_Antenna'] not in this vehicle's VehicleDamage table (24 types) - the part falls back to Default damage
EXIT=0
=== 5 T3_FLEET.md: t3_fleet.py --check ===
E:\Modding\JustCause3\JC3-Batmobile\Working\Translation\T3_FLEET.md: 41 members over 156 vehicles
check ok
EXIT=0
=== 6 FITS.md: t1_fits.py -o scratch/FITS_recheck.md ===
FITS.md: 156 land vehicles, 19 members fitted, 5 usable (R2 >= 0.5) -> tmp/freebuff/scratch/FITS_recheck.md
EXIT=0
=== 7 FX_TABLE.jsonl: jc3fx.py check (long) ===
  50,000 files re-read
  55,000 files re-read
checked 57187 files | problems 0
EXIT=0
```

One caveat on method: **`grab_values.py` has no `--check`** - its "check" is a default run
that rewrites `Research/BatmobileGrab/VALUES.json`, a file this card calls read-only. I
copied the file to scratch first, ran it, and compared: `sha256 4d5a55dd…` before and
after, **byte-identical**, so the file is exactly as I found it. The report's `exit 0` for
this producer is correct, but "check" here means "re-run and hope it is the same", not a
verification mode.

## Claim 2. `paint.effective_base_colour` labelled assumed - PARTIALLY HOLDS

What the report says (`Working/Translation/LEDGER_SOURCES.md`, VALUES.json bullet):

```
- **rule:** gloss_cap, base_colour and the vanilla tint are grabbed (rbm block / material member);
  albedo_gain = vanilla paint luma 0.1837 / authored luma 0.0533 is DERIVED; effective_base_colour
  multiplies by the grabbed Diffuse_Adjust, but the engine's combine operator is UNKNOWN in
  COLOUR_PARAMS.md, so that composite is ASSUMED, not derived
- **assumed inside this file (not decoded):** `paint.effective_base_colour` — the composite is
  computed by the producer; `Research/BatmobileGrab/COLOUR_PARAMS.md:228` says
  `whether and how they combine is UNKNOWN`
```

and in `LEDGER_SOURCES.json` (`"value_label": "grabbed + derived (one assumed composite)"`,
`assumed_fields` populated for `VALUES.json` only, `assumed_rule` beside it). That is the
correct classification, and it is where the `assumed_rules_cited` oracle reads.

But the brief asked me to open `VALUES.json` - and the label is **not there**:

```
$ grep -n "assumed\|effective_base_colour\|label" Research/BatmobileGrab/VALUES.json
13:  "effective_base_colour": [
```

The file's paint block is `gloss_cap`, `authored_gloss`, `base_colour`,
`effective_base_colour`, `albedo_gain`, `source{gloss_cap, base_colour, albedo_gain}`.
`effective_base_colour` has **no `source` entry and no label**, while `base_colour`'s
source string still reads:

```
"base_colour": "Material0_BaseColour on Batmobile_V3_Mainbody_NEW_MIC (via parent chain), x Diffuse_Adjust [2.2, 2.0, 2.0]"
```

So a reader who follows G3-20d's sentence "It is now labelled assumed" to `VALUES.json`
finds the opposite impression: the multiply is written into a `source` string as if it were
part of the grab. Since the report also states `VALUES.json` was not edited (correct - I
confirm its sha256 is unchanged from before my run), the honest phrasing is "the ledger
sources pass labels it assumed"; the JSON itself stays unlabelled and unfixable within this
card's rules. Worth one sentence in the report, and worth a `G3-11c`-style follow-up row if
the file is ever regenerated.

## Claim 3. "944 of 944 `FunctionExpressions` slots are zero" - HOLDS

`Research/BatmobileGrab/COLOUR_PARAMS.md`:

```
230: - **No combine rule.** The 11 Batmobile `MaterialFunction`s hold 944 expression slots,
231:   **0 non-zero** in this read, so no operator, input or output link is in the
240: 1. **the rule that combines the parameters (what multiplies what, in which order)** - every
     `FunctionExpressions` slot of the 11 Batmobile MaterialFunctions is zero (944 slots,
     0 non-zero in this read), so no operator, input or output link is in the package
259: | `no_derived_composite_value` | True | {"combine_rule": "UNKNOWN: 944 of 944 FunctionExpressions slots are zero", ...}
260: | `operator_graph_is_stripped` | True | {"functions": 11, "nonzero_slots": 0, "slots": 944} |
```

`Research/BatmobileGrab/COLOUR_FUNCTIONS.md:34` says the same in different words ("Every
slot of every `FunctionExpressions` array is 0. The count survives (944 slots), the links
do not"), and `COLOUR_PARAMS.json:1680` carries the exact string G3-20d quotes. So the
wording and the number are the project's own, not this card's. **944 slots / 0 non-zero /
11 functions** is decoded; "operator UNKNOWN" is the correct consequence.

## Claim 4. 69 re-derivable / 27 not - REPRODUCES, with one qualifier

Parsed the ledger's own `open_with` for every OPEN row:

```
OPEN 96
per-source citations {'CHAIN.json': 38, 'T3_FLEET.md': 30, 'FITS.md': 5, 'PARTS_TABLE.jsonl': 9, 'FX_TABLE.jsonl': 22}
groups {('cites-none', 'plus-outside'): 27, ('cites-seven', 'only-seven'): 35, ('cites-seven', 'plus-outside'): 34}
rows citing at least one of the seven: 69
rows citing a file outside the seven: 61
  of those ALSO citing a seven-file: 34
```

**69 / 27 matches the report exactly.** Per-source counts agree for CHAIN (38), T3_FLEET
(30), FX (22) and PARTS (9); they differ only for FITS (5 vs 6), VOCABULARY (0 vs 4) and
VALUES (0 vs 1) because the report counts a source named *anywhere* in the row (e.g.
`T-S5`'s `proposed` cites `VOCABULARY.md n=167 median 0.2` while its `open_with` does not),
whereas I counted `open_with` only. That is a definitional difference, not an error - but it
means the classification is text-based, so the `open_with` field is the better evidence and
the two counts should say which they use.

The qualifier: **34 of the 69 name a second, non-seven source in `open_with` itself.**

```
   T-B1    seven=CHAIN.json          also=TANKTURN.md
   T-B3    seven=CHAIN.json          also=TANKTURN.md
   T-B4    seven=CHAIN.json          also=TANKTURN.md
   T-P1    seven=PARTS_TABLE.jsonl   also=t16_collision.json      (and T-P2, T-P3, T-PA1,
   T-FX1   seven=FX_TABLE.jsonl      also=FX.md                    PA2, PA4, PA5, PA7, PA8)
                                                                    (and T-FX2 … T-FX23)
```

All 9 parts rows and all 22 FX rows are in this group. The report's row table lists only
the seven-file, so those rows read as fully re-derivable when they are only *partly*
re-derivable. The 27 "outside the seven" stay correct; the 34 need a column.

## Claim 5. Five of the 69 traced to a byte source

I picked five across the three shapes (grabbed / derived statistic / absence) and followed
each hop myself.

### 5.1 `T-FX1` - reaches the shipped bytes (strongest)

Ledger: `now: present`, `open_with: "Research/JC3Grab/FX_TABLE.jsonl + FX.md"`. A row of
`FX_TABLE.jsonl` (first row, verbatim, truncated):

```
{"container":"dlc/bavarium_sea_heist/.../spawned_bh_paratrooper.ee","source":"dlc/.../spawned_bh_paratrooper.ee",
 "path":"effects/jc_characters/decal_blood_splatter.effc","ext":".effc","size":6271,"mount":"dlc",
 "root":"EffectRTSystem","rows":112,"arrays":13,"objects_digest":"b3c3994c7b82a1a6",
 "digest":"27d0018c27809216f8c746332cba6dee1b15c0d1","types":36}
```

The row names the container, the inner `.effc` path, its size and a `sha1` digest, and
`jc3fx.py check` re-reads the game and recomputes it ("checked 57187 files | problems 0").
**Chain: ledger row -> FX_TABLE row -> game archive member -> decoded rows digest. Reaches
bytes.** (It also cites `FX.md`, outside the seven - the qualifier above.)

### 5.2 `T-B1` - the chain does not reach a value (the mis-tag)

Ledger: `now: 2.0`, `open_with: "Research/BatmobileGrab/CHAIN.json (boost members) +
Research/JC3Grab/TANKTURN.md"`, classified **grabbed** in G3-20d's table citing
`CHAIN.json` only. In `CHAIN.json`:

```
('RVehicleSimBatmobile', 'Playable_BatmobileFunhouse_SF.SimulationModel', 476, 'BoostTorqueVSpeedCurve', None)
('RVehicleSimBatmobile', 'Playable_BatmobileJoker_SF.SimulationModel',   476, 'BoostTorqueVSpeedCurve', None)
('RVehicleBatmobile',    'Playable_BatmobileFunhouse_SF.BatmobileFunhouse', 6876, 'RVehicleBatmobileBase.ImpactBoostMod', 2.0)
```

The boost curve at offset 476 is recorded with **`value: None`** - name and offset decoded
from the SDK layout, value absent from the archetype. The only `2.0` in a boost-named
member is `ImpactBoostMod` at offset 6876, which is a different property (impact, not the
nitro torque multiplier the row targets). So the row's `2.0` rests on `TANKTURN.md`
(its `source` says "boost/standard ratio 1.30 → 2.10"), which is **not among the seven and
was not checked**. Correct label: outside/partly outside, not grabbed.

`T-B3` (identity / absence proof) and `T-B4` (Serpente defaults) cite the same
`TANKTURN.md` but their claims are absence/default statements that `CHAIN.json` can carry,
so they survive this objection; `T-B1` does not.

### 5.3 `T-E2` - opens correctly, stops in the decoded extraction

Ledger: `now: 1393.5`, `open_with: CHAIN.json (torque curve) + FITS.md`. `FITS.md` row:

```
| `torque at optimal rpm` | 2.153 | +0.719 | +0.808 | 142 | 12 … 5e+04 | 834.1 |
```

The file prints the fit at 4,000 kg; the ledger's "1,121 at 6 t" is that fit at 6,000 kg,
and it checks: `2.153 * 6000^0.719 = 1120.8`, and `1393.5 / 1120.8 = 1.243` = the row's
"×1.24". Arithmetic holds (derived, 1 dp).

But the terminal is not bytes: `t1_fits.py` reads `RAW = os.environ.get("JC3_RAW",
r"E:/Modding/_shared/gamedata/JC3grab")` and globs `entities/*.json` - the **decoded extraction**,
not the shipped archives. `jc3grab.py` writes that extraction (`RAW ... Raw decodes stay
OUTSIDE the repo`) and its `check` re-scans it ("566 inner files, 30 modules decoded"). So
the chain is ledger -> FITS.md -> `_gamedata` JSON -> (game archive, one hop not re-run
here). **Stops at a derived layer**, exactly what the brief asked me to look for.

### 5.4 `T-S5` - same terminal

Ledger `now: 0.2`; `T3_FLEET.md` row `suspension front lateral tyre offset | n=125 **0.2**
(0.1 … 0.3)` matches. `t3_fleet.py` reads the same `RAW = .../JC3grab` and globs
`entities/*.json`. **Stops at the same derived layer**; the `VOCABULARY.md` cross-check the
row's `proposed` cites has the same terminal (`jc3grab.py` -> `_gamedata`).

### 5.5 `T-P1` - decoded values with no byte anchor

`PARTS_TABLE.jsonl` first row (truncated):

```
{"entity":"editor/entities/jc_vehicles/.../oldjeep_civilian_01.ee","module":"oldjeep_vehicle_parts.vmodc",
 "parts":[{"i":0,"n":"oldjeep_body","dt":"Land_Body","b":"None","m":"models/.../civilian_oldjeep_body.lod",
 "parent":-1,"body":0,"ray":64,"lights":1,"deform":1,"kids":[1,2,...]}, ...]}
```

No offset, no size, no digest - only decoded member values keyed by part index. And the
green check does not touch the game: `cmd_check` reads `ENTITIES.md` and the `DeformPoints`
decode only (`epe_parts()`, `deform_parts()`, `check_parts_table()`), while only
`cmd_build` opens `D:/Games/Just Cause 3` (`jc3grab.read_entry(r, game)`). So the check
proves the tables agree **with each other**, not with the shipped bytes. **No byte anchor**;
the value is decoded-but-unaddressed, one hop short of a traceable offset. (It also cites
`t16_collision.json`, outside the seven.)

**Tally: 1 reaches bytes with a digest, 1 does not carry its value at all, 2 stop in the
`_gamedata` extraction, 1 has no offset.** None of the five is fabricated; three are
weaker than the "re-derivable" column implies.

## Smaller notes

* **`FITS.md`'s own noise warning applies to 12 of 19 fits** (R² < 0.2), which the report
  says. `T-E2`'s fit is R² = 0.808, so it is one of the five usable ones - good.
* **`T3_FLEET.md` is quoted in the report as "n / median / p25..p75 per mass class over 156
  land vehicles"**, which matches the file (`rigid body mass | n=156 …`) - holds.
* **`assumed_rules_cited`** exists in `LEDGER_SOURCES.json` and fires on the
  `COLOUR_PARAMS.md:228` citation; that is the right kind of oracle for an assumed label.

## What I could not check

* **`ledger_sources.py --check` itself** (8 oracles, and it re-runs all seven producers).
  The brief asked for the seven producer checks, which I ran directly; I did not separately
  run the wrapper, so the oracle table in `LEDGER_SOURCES.md` §4 is quoted, not re-derived.
* **A single `FX_TABLE` digest recomputed by hand.** I trusted `jc3fx.py check`'s
  "57187 files | problems 0" (exit 0) rather than re-reading one `.effc` and hashing it.
* **Whether `_gamedata` still equals what the archives hold.** `jc3grab.py check` re-scans
  the extraction; a full re-decode from `D:/Games/Just Cause 3` is `jc3grab.py`'s build
  path, which I did not run (it would rewrite the extraction). So `FITS.md` / `T3_FLEET.md`
  / `VOCABULARY.md` chains are re-derivable *given the extraction*, which is the report's
  own caveat.
* **The 27 outside-the-seven rows** (`stations.json`, the §70 mesh measurement,
  `T14_LIGHTS.md`/`LIGHT_SYSTEM.md`, `DAMAGE_MODEL.md`, `t16_collision.json`) - out of this
  card's scope and not traced.
* **`T-B3`/`T-B4`** - I checked that their claims are absence/default statements CHAIN can
  carry, but did not re-verify the absence in the package bytes myself.
