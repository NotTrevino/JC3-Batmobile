# Independent review — T-21 · Appearance completion

Reviewer: Buffy (did not write this card). Date: 2026-10-29. Read-only review: the only file
written is this report. No game launch, no commit, no edit to `GRAB_BACKLOG.md`, `MODLOG.md`,
`Research/`, `Tools/` or any game file.

**Change record (AGENTS.md).** Intended change: create this one review file. File:
`tmp/freebuff/reports/review-T-21.md`. Why this file: the review was asked to land exactly here and
nothing else is written. Revert: delete `tmp/freebuff/reports/review-T-21.md`.

**Scope reviewed:** `GRAB_BACKLOG.md` §0.5 (R1–R14), the T-21 card (`GRAB_BACKLOG.md:958-966`), the
T-21 §12 row (`GRAB_BACKLOG.md:1330`); `MODLOG.md:13121-13147` (intended change) and
`MODLOG.md:13349-13431` (done); `Working/Appearance/APPEARANCE_PLAN.md` (522 lines),
`Working/Appearance/appearance_plan.json` (96,186 B), `Tools/scripts/appearance_plan.py` (31,765 B),
`Tools/scripts/appearance_progress.py` (14,145 B); the inputs it reads (`Working/Appearance/progress.json`,
`Research/BatmobileGrab/SLOTS.json`, `Research/BatmobileGrab/VARIANTS.md`,
`Working/Appearance/build_bud1/factors.json`) and `Tools/scripts/factors.py` for the factor lists.

---

## VERDICT

**minor issues**

The card is done and the Done criterion is genuinely enforced. `--check` re-derives the plan from
`progress.json`, `SLOTS.json`, `VARIANTS.md` and `factors.json`, re-renders both files and compares
them byte for byte, and then asserts the things the card actually asks for: `unclassified == 0`,
`missing == 0`, `planned == partial + excluded`, every action is bake/route/drop with a target, every
rule is used (no dead rows), POL-2 == bake, all four skin rows parsed. I re-derived the headline
numbers (172 / 23 / 8 / 141), the 14 drop-rule tallies (41/27/4+1/12/9+1/8+7/8/4/3/4/2 = 141), the
interior face counts and the four skin material counts straight from the inputs, and all matched.

The defects are wording-level but two of them matter to the build: **`route` is used for eight rows
although five of them do not carry the value** (the doc's own §8 says the glass values stay vanilla),
and **§5 asserts a column relationship that is simply false** (the interior column sums to exactly
24, not "more than 24"). The rest are typed numbers in prose, a budget claim that the bake cannot
support yet, and a hedge in the bake target.

---

## Check output (verbatim)

Command, from `E:/Modding/JustCause3/JC3-Batmobile`:

```
python Tools/scripts/appearance_plan.py --check
```

stdout, exact (exit status `0`):

```
components 339 | transferred 167 | partial 36 | excluded 136 | missing 0
planned 172: bake 23 route 8 drop 141 | POL-1 24 POL-2 23 | unclassified 0
md match True, json match True
check ok
EXIT=0
```

## Out paths

| path (card `Out` / row) | exists | evidence |
|---|---|---|
| `Working/Appearance/APPEARANCE_PLAN.md` (card `Out`) | yes | 522 lines, 53,762 B, nine sections, 172-row table in §7 |
| `Working/Appearance/appearance_progress.py` "reflecting the plan" (card `Out`) | yes | `--plan` / `--strict-plan` added; `attach_plan()` annotates every non-transferred component and `--strict-plan` fails on any unclassified |
| `Working/Appearance/appearance_plan.json` (row) | yes | 172 components, 21 rules, 6 interior slots, 4 skin rows, `unclassified: []` |
| `Tools/scripts/appearance_plan.py` (row) | yes | `--write` / `--check` / `--show <component>` |
| `Working/Appearance/progress.json` / `progress.md` (side effect, MODLOG) | yes | 172 components now carry a `plan` key; overall/class summaries byte-identical to `tmp/progress.beforeT21.json` (I diffed them) |

Both halves of the card's `Out` are on disk.

## Does the card's `Done` match what `--check` verifies?

Card (`GRAB_BACKLOG.md:966`): *"0 unclassified components."*

- **Yes, and with teeth.** `check()` fails on any `unclassified` entry, on `planned != partial +
  excluded`, on `missing`, on an action outside bake/route/drop, on a row with no target, on a rule
  that matches nothing, and on `POL-2 != bake`. The MODLOG's tamper #4 (deleting rule D7 → eight
  components unclassified → the Done criterion itself fails) matches the code.
- **What "classified" means here.** The classifier is an exact match of the reason string that
  `appearance_progress.py` recorded against 21 typed rules (`_rule_for(cls, status, why)` in
  `appearance_plan.py`), and the action is the rule's decision. So the gate proves *coverage of the
  reason set*, not that each action is the right one: a rule wrongly labelled `drop` passes. The doc
  says this in its docstring ("a rule here is a decision about a disposition") but not in §8, where a
  reader would look for limits.
- **Input coupling.** The check also asserts `components == 339` and `transferred == 167`; a
  legitimate change in the inventory would fail the gate as "progress.json changed shape" rather than
  as a plan error. That is a deliberate guard, but it means the plan cannot be re-run against a
  changed inventory without editing the constant.

---

## Issues

### 1. Moderate — `route` is used for five rows whose value is not carried

`APPEARANCE_PLAN.md:26` defines the action: *"route | 8 | the value is carried by another carrier the
build writes"*. `APPEARANCE_PLAN.md:500-501` (the §8 limits) says the opposite for three of them:
*"the three glass rows route to the block but their values stay vanilla."*

Reading the eight route rows (`APPEARANCE_PLAN.md:66-73`):

| rule | rows | what the note admits | is the value carried? |
|---|---|---|---|
| R1 | 3 | light colour/group to `CarLight` + lights module, T-18 decodes them | yes |
| R2 | 2 | *"the mask itself is not sampled (channel undecoded)"* — only the intensity/emitter | no (the mask is the component) |
| R3 | 2 | *"its numeric parameters are UNKNOWN (§102d) so the vanilla glass response is kept"* | no |
| R4 | 1 | *"the mask's per-layer split is lost, its tint survives"* | partly |

So "route 8" tells B-08 there are eight values to carry when only three are carried, three carry a
different (smaller) value, and two carry nothing. The taxonomy has no state for "carrier exists, value
not sent", and the doc's own §8 admits it — the §1 table should not say "the value is carried" for
that state. This is the R4/R5 risk in this card: the carrier is present, but the behaviour the row
claims is not.

### 2. Moderate — §5's claim about the interior column sum is false

`APPEARANCE_PLAN.md:264-265`: *"A component shared by two interior materials (a texture bound by the
cockpit and the seat) appears in both rows, which is why the column sums to more than the 24 unique
interior components listed next."*

The column is `17 + 6 + 0 + 0 + 0 + 1 = 24` (same table, `APPEARANCE_PLAN.md:255-260`), exactly the
24 rows listed at `:269-292`, so no component is shared and the sum is not greater than 24. The
sentence is emitted unconditionally by `render()` — it is prose, not a computed relation — so
`--check` cannot see it (R11). It is the one place in the generated doc where a number the data
contradicts is asserted.

### 3. Minor — the R9 budget claim is a size claim made from a count claim, and the bake does not exist yet

`APPEARANCE_PLAN.md:34-36`: *"The bake changes no block count and no texture count, so it does not
touch the R9 texture budget."* A constant *count* does not establish a constant *size*: folding six
detail textures into each material's `s1` re-encodes that texture and can change its KB. The same doc
says at `:503-505` that the bake step does not exist yet, so nothing about the budget has been
measured. The correct statement is "no new block or texture is added; s1's size after the bake is
unmeasured (UNKNOWN)".

### 4. Minor — typed numbers in generated prose (R11)

`appearance_plan.py`'s docstring says *"nothing is hand-typed, every number below is re-derived"*.
The tables are; these are literals in `render()`:

- `:32-33` *"18 static float4 + 7 support floats + the 4 tint components"* — I verified 18
  (`factors.STATIC`) and 7 (`factors.SUPPORT`), but the counts are typed and "the 4 tint components"
  is loose (the tint is an RGB/vec3 write in `factors.py:211-217`).
- `:245` *"six of the 19 slots"* — the 19 is typed; `SLOTS.json` has 19 (verified).
- `:320`, `:508` *"Texture 7,065 KB"* — R9's wall, typed.
- `:510` *"the 27 reflectance rows and the 4 per-pixel roughness textures"* — both are derived in §4
  (D2 27, D3 4) but typed here; `:265` is the same class of defect and is wrong.
- `:505` *"the 23 bake rows stay `partial`/`excluded`"* — all 23 bake rows have status `excluded`
  (json: `('bake','excluded') 23`); the `partial` half is a hedge that no row exercises.

### 5. Minor — the bake target leaves the per-texture decision open

`APPEARANCE_PLAN.md:39` (P1's target): *"s1 Normal (and s0 where the pattern is albedo detail)"*.
The six P1 textures (`Batmobile_Microdetail`, the four `Micropattern*`, `neutral_normal`) are listed
individually at `:41-46` with the same hedge, so the plan does not say which sampler each one gets
even though `factors.json` already lists the materials that bind each. The card asks to "bake into
albedo/normal"; this row says "normal, or albedo, depending", which is a decision deferred to the
bake's author rather than made here.

### 6. Minor — "interior components" is really "components that touch an interior material"

`APPEARANCE_PLAN.md:251` counts *"24 interior components"*, and `:267` labels the list "Interior
components in this plan (POL-1 tag)". A texture is tagged when **any** binding material is interior
(`build_rows()`: `if any(m in INTERIOR for m in mats)`), so `Aniso_ramp_Lacquered`
(`:269`, bound by cockpit + six non-interior materials) is counted as interior. The table's own
caveat at `:264-265` was presumably meant to cover this but, as issue 2 shows, it does not describe
the data.

### 7. Nit — classification is by reason string, and the reason text is copied

The §4 column "reason recorded by `appearance_progress.py`" (`:78`) is the rule's `why`, which is
typed in `appearance_plan.py` and must equal the recorded string; when it does not, the component
becomes unclassified and the check fails (a good design). But it means the doc's reason column is a
copy that can only be right when the equality holds — nothing renders the reason *from*
`progress.json`. No action needed; noted for the next reader.

---

## Spot-checks

| # | doc value | verified where | result |
|---|---|---|---|
| 1 | *"planned 172: bake 23 \| route 8 \| drop 141"* (`:17`) | `progress.json` `overall`: 339 = 167 + 36 + 136 + 0; plan JSON actions `drop 141, bake 23, route 8` (sum 172) | match |
| 2 | §4 drop tallies D1 41, D2 27, D3 4, D4 14, D5 1, D6 12, D7 8, D8 7, D9 4, D10 3, D11 9, D12 1, D13 8, D14 2 (`:80-93`) | re-counted from `appearance_plan.json`: identical; sum 141 | match |
| 3 | §5 LOD0 faces 27,334 / 13,014 / 100 / 2,949 / 18 / 788 (`:255-260`) | `SLOTS.json` slots 10, 11, 12, 14, 15, 16 — same faces, 19 slots in the file | match |
| 4 | §6 skin material counts 78 / 80 / 69 / 84 (`:313-316`) | `VARIANTS.md` §3 lines 56-59 (`V2 **78**`, `MK2 **80**`, `Joker **69**`, `Funhouse **84**`) | match |
| 5 | *"18 static float4 + 7 support floats"* (`:32`) | `factors.STATIC` length 18, `factors.SUPPORT` length 7 | match |
| 6 | *"the column sums to more than the 24 unique interior components"* (`:265`) | interior table 17+6+0+0+0+1 = 24; the POL-1 list has exactly 24 rows; no component appears twice | **contradicts the doc** (issue 2) |
| 7 | POL-1 *"bake 7, route 1, drop 16"* (`:251`) | plan JSON POL-1 rows: 24 total, `drop 16, bake 7, route 1` | match |

---

## What would make this card `sound`

1. Split `route` into "carried" and "carrier exists, value pending" (or add a `partial` action) and
   restate §1's row so "route 8" does not claim eight carried values; the eight notes already say which
   is which.
2. Replace §5's column-sum sentence with the computed relationship (it sums to exactly 24 here), or
   derive it and let `--check` assert it.
3. Reword the R9 sentence to a count claim plus an UNKNOWN size, and make P1's target per texture.
4. Pull the typed numbers (`19`, `7,065`, `27`, `4`, "4 tint components") from the inputs or label
   them as quoted from R9/factors.py, and drop the `partial` half of the §8 "partial/excluded" hedge.

## Limits of this review

- Read-only: `--write` was not run (it would rewrite the plan) and the MODLOG's six tamper tests were
  not reproduced. The mechanisms they exercise are real code — the exact doc compare, the JSON
  compare, the `unclassified`/`planned`/rule-used assertions in `check()` — and I re-derived every
  headline number independently.
- `appearance_progress.py --strict-plan` was not run because it rewrites `progress.json`/
  `progress.md`; I read the code path (`attach_plan()` + `--strict-plan`) and confirmed the stored
  annotations and unchanged totals against `tmp/progress.beforeT21.json`.
- No game launched (R6); every build step the plan proposes (POL-2 bake, the routed carriers) is
  unbuilt and therefore unverified.
- "The ramp files are missing on disk" (rule D10's reason) was not checked: it lives in the
  `E:\Modding\ArkhamKnight\_grab` export, outside this repo, and is taken from the recorded reason.

## Files touched by this review

`tmp/freebuff/reports/review-T-21.md` (this file). Nothing else.
