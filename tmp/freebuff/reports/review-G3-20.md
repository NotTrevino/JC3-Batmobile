# review-G3-20 — the ledger↔G3 mapping, re-read value by value

VERDICT: **needs rework**

`ledger_g3.py --check` is green and the row count is right, but the pass's own headline —
**180 OPEN / 2 CORRECTED / 16 SUPPLIED** — does not survive a value-level re-read in either
direction. Of the **18** rows it marks answered, **12 do not use the value they cite** (9 name a card
that answers a different question, 3 quote a different number); and of the **180** it leaves OPEN, the
two later passes over the same rows (`G3-20b`, `G3-20c`) close **34 more** and change **20 numbers**,
so OPEN is an over-count as well. What the checker validates is that a citation *exists*, not that it
*answers its row* — which is exactly the failure mode this review was asked to test.

## 1. `ledger_g3.py --check`

```
$ uv run python Tools/scripts/ledger_g3.py --check; echo "EXIT=$?"
OK 198 rows; {'OPEN': 180, 'CORRECTED': 2, 'SUPPLIED': 16}; every evidence file exists; md+json byte-identical
EXIT=0
```

Re-read from `Working/Translation/LEDGER_G3.json`: 198 rows, `Counter({'OPEN': 180, 'SUPPLIED': 16,
'CORRECTED': 2})`, and **180/180 OPEN rows carry an `open_with` supplier** — the one part of the
design that holds up without qualification.

The check's failure list (stale md/json, row count ≠ 198, duplicate ids, order, unknown status,
missing evidence file) is **structural**: it would pass this table if every row cited the wrong
card, because it never re-reads the cited value.

## 2. The two cited evidence values the brief names

| citation | re-read | verdict |
|---|---|---|
| `E-MASS` = **1627.097155** over 56 blocks | `Research/JC3Grab/PHYSICS_ROLES2.md:48`: "strictly positive in the donor: **True**; finite: **True**; total over all 56 blocks: **1627.097155**" | **holds** |
| `E-LINK` = **54/54** | `Research/JC3Grab/PHYSICS_ROLES3.md:59`: "… `hknpShapeMassProperties` block. **54 of 54** polytopes resolve; 0 do not" | **holds** |

Both numbers are present, at the lines cited, with the same magnitude. The problem is not the
values; it is which row they are attached to.

## 3. The 18 non-OPEN rows, tested for "does the row use this value"

| row | what it marks | what the cited card actually gives | test |
|---|---|---|---|
| `T-M1` | CORRECTED | `PHYSICS_ROLES2.md:48/:49` — 56 per-shape blocks, total 1627.097155 | **holds** |
| `T-M4` | CORRECTED | `PHYSICS_ROLES2.md:49` — wheel mass is a per-hull `+0x28` block | **holds** |
| `T-B2`, `T-MD1` | SUPPLIED | `SAMPLER_FIELDS2.md` — `bBoosting` @2396 &0x1, `bVehicleBoostButton` @781 | **hold** |
| `T-PA3` | SUPPLIED | `PHYSICS_ROLES3.md:41` — `+0x0C` = body id | **holds** |
| `T-PA6` | SUPPLIED | `PHYSICS_ROLES3.md:25` — 24-byte record, one body id | **holds** |
| `T-MA1`, `T-MA3` | SUPPLIED | `COLOUR_PARAMS.md:69` gives authored `Material0_BaseColour` [0.025787, 0.025787, 0.03, 1]; the rows want the **effective** [0.056738, 0.05158, 0.06], which the card says is UNKNOWN (944/944 expression slots zero) | **wrong value** |
| `T-MA4` | SUPPLIED | row is gloss **0.45**; the card has `Material0_Roughness` 0.4/0.25 and `Material0_Reflectivity` 0.2/0.25 — a different parameter | **wrong value** |
| `T-B3`, `T-B4`, `T-P3`, `T-MA2`, `T-MA5`, `T-MA7`, `T-CO1`, `T-CO2`, `T-WP11` | SUPPLIED | each names a card answering another question (absence proof vs state bit; census vs write mapping; paint chain vs texture count / Window block / donor palette; body words vs a box fit) | **wrong card** |

Tally: **6 hold, 3 wrong value, 9 wrong card** — the same split `G3-20b` publishes for these 18 rows,
and independently visible in `LEDGER_G3.json`: the `value` string attached to `T-MA1/2/3/4/5/7` is
**byte-identical** ("body base colour [0.025787, …]; 52 MIC overrides, 69 chain defaults"), so a texture
count (`T-MA2`), a gloss (`T-MA4`), a `Window` block (`T-MA5`) and a donor palette (`T-MA7`) are all
"supplied" by one sentence about base colour.

That is the withdrawn first mapping repeating in miniature: 63 SUPPLIED became 16, but 12 of the 16
are still keyword matches on `colour`, `boost`, `census` or `body`.

## 4. Ten OPEN rows, sampled evenly (`rows[::18]`), against decoded cards

| row | target (short) | supplier named | re-read |
|---|---|---|---|
| `T-G1` | `land_global.base_wheel_hardpoint_positions[0..3]` | G3-01/02/03 or a new decode | OPEN defensible — no card in this set decodes JC3 wheel hardpoints |
| `T-ST4` | `land_steering.steer_input_power_pc/durango/orbis` | G3-01/02/03 | OPEN defensible — platform rows, no card |
| `T-L3` | the 5 `TailLight` rows | G3-01/02/03 | **probably supplied** — `G3-20c` quotes `BrakeLightsLensFlare` / `TailLightsLensFlare` (`CLASS_DEFAULTS.md:122/:123`) for `T-L15/T-L16`; `T-L3` is the same family |
| `T-LG5` | light rig, mode/forensics | G3-04..06 | OPEN defensible |
| `T-G6` | `front/rear_wheels.radius` | G3-10/10b/10c | **probably supplied** — `CLASS_DEFAULTS.md` decodes `SVehicleWheel.WheelRadius` (the row's own source quotes 64.0), which is `G3-06b`, not read by this pass |
| `T-FX8` | `car_cycle_base_dual.effc` carrier | G3-07 + `.effc` decode | **already answered outside the G3 cards** — `FX_TABLE.jsonl` rows carry the container/vehicle counts (used in `LEDGER_G3_REDERIVE.md`); the eight-card rule excludes it by construction |
| `T-L10`, `T-L28` | per-light rows (omitted) | G3-05/06 | OPEN defensible — the JC3-side light preset is the open half |
| `T-WP12` | 2 clips, 5 mapped elements | G3-08/09 | **probably supplied** — `G3-20c` quotes ten `GadgetMesh` components and the HUD setters from `REMAINDER.md`/`G3-06b` |
| `T-WLD16` | cargo plane / boat can carry the car | G3-07 | OPEN defensible — world row, no decoded card |

So **4 of 10 sampled OPEN rows** look answerable from files already in `Research/` (one of them —
`T-FX8` — from a decode this pass's own predecessor used), **6 are correctly open**. A 40 % over-open
rate on a 10-row sample is consistent with what `G3-20b`/`G3-20c` measured on their full sets.

## 5. Where `G3-20b` and `G3-20c` disagree with `LEDGER_G3.md`

| report | its scope | its result | disagreement with `LEDGER_G3.md` |
|---|---|---|---|
| `G3-20b` | T-1 + T-2b + T-13, **105 rows** | 6 HOLDS / 3 WRONG_VALUE / 0 WRONG_CARD / **96 OPEN**; and the 18 first-pass rows re-checked as 6/3/9 | the 18 answered rows are **6 correct, 12 mis-cited**; and `T-ST5` is closed on `CLASS_DEFAULTS.md:317` (`DriftCorrectionSteerSpeed` = **1.0**), a row this table leaves OPEN |
| `G3-20c` | T-20, T-3, T-7, T-15, T-14, **93 rows** | **25 QUOTED / 68 OPEN**; **20** of the 25 disagree numerically with the ledger (all `CLASS_DEFAULTS.md`, object = `Default__RVehicleBatmobileBase` 10923) | **25 rows this table calls OPEN are answered**, and 20 of them *contradict* the ledger number — e.g. `T-EF1` 0.2/0.2 → **0.5/0.5**, `T-DM7` 20/150/2.25/2.0 → **60/200/1.5/1.5**, `T-K4` 0.75/640000 → **1.0/160000** |

Both later passes also reclassify rows this document counts as OPEN into a third state the ledger has
no name for: **"a card contradicts the row's number"**. That is more valuable than SUPPLIED, and
`LEDGER_G3.md` has no column for it.

Neither report reconciles back into `LEDGER_G3.md` (G3-20c says explicitly: "The earlier keyword pass
was not read and none of its statuses is reused"), so the project currently holds three
non-intersecting classifications of the same 198 rows.

## 6. What this review could not check

- **Whether the 96 + 68 rows of the later passes are themselves right.** I re-read their *claims about
  the first pass*, not each of their 164 verdicts; that is their own `--check`'s job.
- **The four "probably supplied" sampled rows' values.** I identified the file and family that carries
  them (`FX_TABLE.jsonl`, `CLASS_DEFAULTS.md`, `REMAINDER.md`) but did not re-decode the bytes, so the
  label stays "probably".
- **`T-M2` (inertia) / `T-M3` (centre of mass).** Both stay OPEN, and that is right: `INERTIA.md`
  (G3-10e work) reports the tensor oracle **failing** (27/54 box agreement) — the block is decoded in
  shape but not in scale, so no row value can be written from it.
- **The 198 row texts themselves.** They come from `T_ROWS.jsonl`; I did not re-check that file
  against the build.

## Commands run

```
$ uv run python Tools/scripts/ledger_g3.py --check; echo "CHECK_EXIT=$?"
OK 198 rows; {'OPEN': 180, 'CORRECTED': 2, 'SUPPLIED': 16}; every evidence file exists; md+json byte-identical
CHECK_EXIT=0

$ grep -n "1627" Research/JC3Grab/PHYSICS_ROLES2.md
48:- strictly positive in the donor: **True**; finite: **True**; total over all 56 blocks: **1627.097155**

$ grep -n "54 of 54" Research/JC3Grab/PHYSICS_ROLES3.md
59:-> the `hknpShapeMassProperties` block. **54 of 54** polytopes resolve; 0 do not.

$ uv run python - <<'PY'   # LEDGER_G3.json: counts, open_with coverage, 10 sampled OPEN rows
rows: 198
Counter({'OPEN': 180, 'SUPPLIED': 16, 'CORRECTED': 2})
open: 180 with open_with: 180
[OPEN rows[::18] printed: T-G1, T-ST4, T-L3, T-LG5, T-G6, T-FX8, T-L10, T-L28, T-WP12, T-WLD16]
PY
```

No file was edited; `LEDGER_G3.md/.json`, `T_ROWS.jsonl` and every card were read only. No new script:
this review re-reads existing outputs with inline commands, and the authoritative re-derivation stays
`ledger_g3.py --check` (structural) plus `G3-20b`/`G3-20c` (value-level).
