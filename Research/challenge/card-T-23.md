# Assumption challenge — backlog card T-23 (ledger close-out and build batches)

Scope: `GRAB_BACKLOG.md` §0.5 (R1–R14), the T-23 card (§7), its §12 row, and the T-23 outputs and
journal sections: `Working/Translation/BUILD_BATCHES.md`, `Working/Translation/build_batches.json`,
`Tools/scripts/t23_closeout.py`, `Tools/scripts/bmak_coverage.py` (+ `Research/BatmobileGrab/COVERAGE.{md,json}`),
MODLOG §"T-23 · Ledger close-out and build batches — done" and §"T-23 rework — done".

Read-only. Nothing was written except this file; no game, no `D:/Games`, no commit.
The card's own check was re-run first, on the current tree:

```
$ python Tools/scripts/t23_closeout.py --check
gate TX: 75 codes (51 carried, 9 named omission, 5 blocked, 10 documented, 0 unmapped) | 198 ledger rows | assumed 1 (0 unsigned) | decisions 10/10 answered | 14 artefacts (12 payloads + 2 records) over 14 B steps
siblings: t_rows.py check exit 0 | status_audit.py --check exit 0 | bmak_coverage.py --check exit 0
gate TX ok: every §1 code maps to a row, assumed rows are signed off, D-1...D-10 answered
EXIT=0
```

So the gate is green and reproducible. The question is what that green *rests on*.

## VERDICT summary

| # | Assumption | Verdict |
|---|---|---|
| A1 | §1 has exactly 75 feature codes and the parser sees all of them | **HOLDS** |
| A2 | "every §1 code maps to ≥ 1 row" — a row in a document, found by substring, proves the requirement is carried | **WEAK** |
| A3 | A document row that states no *keyword* disposition is `documented` (10 codes) | **BROKEN** — HUD-1 and CAM-1 state `reuse`/`map`/concrete values **and a take**; the count is 53 carried / ≤8 documented, not 51 / 10 |
| A4 | A document row's state is read from the first line containing its id | **BROKEN** — 4 row ids are read from summary lines / prose, not from the row; 1 is `superseded` and read as `documented` |
| A5 | `rows assumed` = 1 of 180 | **WEAK** — 36 of those 180 in-scope rows (20 %) carry no class the counter recognises and are dropped into an unreported `other` bucket; 27 of them are ledger rows phase B will build |
| A6 | The 54 values already in `Builds/test-091` are vetted, so a B step may copy them | **BROKEN** — 2 of the 54 were applied under `T-DM7`, which the ledger has since closed as `out` |
| A7 | "14 artefacts (12 payloads + 2 records)" is the whole set | **WEAK** — the set is `Working/**/*.json` with a `card` key plus a hand-written table; B-04/B-05/B-06/B-11's own `Out` edit files do not exist and are not counted |
| A8 | The `(rows / values)` column is two measurements read from each file | **BROKEN** — `payload_rows()` returns the row count twice; real leaf counts are 3–140× larger |
| A9 | One payload table maps each payload to the step that applies it | **WEAK** — `B-12` is counted as a live step with a payload although D-2 skipped it, `B-13` depends on it, and `appearance_plan.json` is assigned to steps whose cards never name it |
| A10 | "777 G1 feature rows" is a feature census | **WEAK** — 299 distinct over 4 packages; 384 of 777 (49 %) land on a plumbing row, a blocked row or a "bank absent" row |
| A11 | The 9 `named omission` codes are "no carrier exists" claims | **HOLDS**, with a stated residual risk: the searches are name-based class/module-type/vocab scans |
| A12 | "D-1…D-10 answered" | **HOLDS** |
| A13 | "One command", the check runs its three siblings | **HOLDS** (failure path verified); it never runs `status_audit.py --write` |
| A14 | Unit / coordinate convention | **N/A on this page, and that is the problem** — no number carries a unit; the conventions that do the work are "row" (ledger row / document row / file row / package instance) and "value", and A8 shows one of them is not measured |

Overall: the *mechanics* of T-23 hold — the ledger arithmetic, the code count, the decision gate, the
sibling plumbing and the named-absence research all reproduce. What does **not** hold is the page's
two headline content claims: the **51 / 9 / 5 / 10 code split** (A3/A4 — at least 2 codes are in the
wrong bucket, and one document row's real state, `superseded`, has no representation at all) and the
**"rows / values"** and **base-tree** evidence columns (A8/A6 — one is a number printed twice, the
other contains two values no current row authorises). The card is `done` on a real check, but §12's
evidence text repeats the wrong split and the batch page understates one hole while inventing a
measurement.

---

## A1 · "§1 has 75 feature codes" (parsed, not typed)

**The assumption (stated).** `t23_closeout.py` `parse_codes()` walks §1 and matches
`^\|\s*(APP|DIM|ARM|WPN|HDL|MOD|AUD|ANI|WLD|LGT|FX|CAM|HUD)-\d+\s*\|`; if the count is not 75 the gate
adds a problem.

**Test — count §1 independently, three ways.**

```
$ awk '/^## 1\. /{f=1} /^## 2\. /{f=0} f' GRAB_BACKLOG.md | grep -cE '^\| *[A-Z]+-[0-9]+ *\|'
75
$ ... | grep -oE '^\| *[A-Z]+-[0-9]+' | tr -d '| ' | sort -u | wc -l
75
$ ... | grep -oE '\b(APP|DIM|ARM|WPN|HDL|MOD|AUD|ANI|WLD|LGT|FX|CAM|HUD)-[0-9]+' | sort -u | wc -l
75
$ ... | grep -oE '^\| *[A-Z]+-[0-9]+' | tr -d '| ' | sort | uniq -d
(no output)
```

75 rows, 75 distinct, no duplicates, and no code is mentioned in §1 that lacks a table row (third
count). Family arithmetic also closes: 8+4+6+12+6+5+7+9+8+2+4+2+2 = 75.

**Verdict: HOLDS.** The one thing the parse cannot see is §1.4's *prose* rule ("Every BmAK weapon
therefore gets a row; none is 'out' until G2 proves no carrier"). It is not a code, it is not gated,
and it is the rule the 5 `out` weapon rows depend on — see A11.

---

## A2 · "every §1 code maps to ≥ 1 row" is satisfied by a declared table

**The assumption (silent).** `CODE_ROWS` is a hand-written dict of 75 entries in
`t23_closeout.py:62-190`. `feature_gate()` only checks that (a) the document exists, (b)
`anchor in rd(path)` — a **substring test on the whole file** — and (c) the state word. Nothing
connects the requirement in §1 to the behaviour in the row; the mapping is authored by the same
session that calls the gate.

**Test 1 — resolve every anchor through the tool's own reader and print the line it read.** The
document-only anchors come back as:

```
APP-5  P-03   T8_PARTS.md -> documented | | joints that are a continuous spin | P-03 |
ANI-3  P-03   T8_PARTS.md -> documented | | joints that are a continuous spin | P-03 |
ANI-2  P-02   T8_PARTS.md -> documented | | internal rows (no joint, reason given) | P-02, P-05, P-13 |
ANI-1  P-05   T8_PARTS.md -> documented | | internal rows (no joint, reason given) | P-02, P-05, P-13 |
MOD-5  hijack objects  T9_INTERACTION.md -> documented | `D-9` is **resolved 2026-10-28 (user): no**: hijack objects (*pull.out*, *pulled.out*) dropped. |
```

Three of those returned lines are **summary lines**, not the rows P-02/P-03/P-05, and one is a prose
sentence, not a row at all. The gate says APP-5/ANI-1/ANI-2/ANI-3/MOD-5 map to a row; for these
anchors it established that the string occurs somewhere in the document.

**Test 2 — the table's "best row wins" rule.** `feature_gate()` marks a code `carried` if *any* of
its rows is carried (`elif states & (DISPO_CARRIED | {"carried (document row)"})`), and the §12 row
sells that as "51 carried":

```
carried-but-has-blocked-row: MOD-1 ['blocked','keep','next']   (T-MD2 blocked)
carried-but-has-blocked-row: WLD-2 ['blocked','keep','next']   (T-WLD4, T-WLD6 blocked)
carried-but-has-blocked-row: WLD-4 ['blocked','epe']           (T-WLD11 blocked)
carried-but-has-blocked-row: WPN-12 ['blocked','next']         (T-HUD5 blocked)
carried with a named-omission row: ARM-6, AUD-5                (AUD-5: W-01 and W-07 are omissions, only W-03 is mapped)
```

`AUD-5` = "Each weapon: fire, loop, tail, impact, lock beep" is reported `carried` on the strength of
one Vulcan row while its cannon row (`W-01`) and its lock-on row (`W-07`) are both `named omission`.
That is the R5 failure mode the backlog records (a member whose name sounds right standing in for a
behaviour), reappearing one level up: a *code* is carried by its best row, not by its behaviours.

**Verdict: WEAK.** The check does prove what it says — every code has an anchor whose string exists —
but "maps to ≥ 1 row" is not the same claim as "the requirement is carried by rows whose takes can
fail". 4 codes carry a blocked row, 2 carry a named omission, and at least 5 anchors resolve to a
summary line or prose rather than the row they name. The §12 sentence "75/75 §1 codes mapped" is
literally true and rhetorically stronger than the evidence.

---

## A3 · HUD-1 and CAM-1 are "documented with no disposition" (the 10-code bucket)

**The assumption (stated).** The rework replaced "`documented` counts as carried" with a new state:
"a row that exists but states no disposition does not carry its behaviour (R4/R5)". The keyword list
in `doc_row_state()` (`t23_closeout.py:394-401`) is:

```python
elif "**out**" in low or "| out |" in low:            state = "out"
elif any(k in low for k in ("`next`","`keep`","`mapped`","`epe`","`edit`","kept vanilla","`remove`")):
                                                       state = "carried (document row)"
else:                                                  state = "documented"
```

So `documented` means "none of those words appeared", not "the row has no disposition".

**Test — print the last three cells (proposal | confidence | take) of every anchor the tool calls
`documented` in `T6_HUD_CAMERA.md`.** The T6 table is `id | source | JC3 carrier | scale | proposal |
confidence | take`:

```
HUD-1  T-HUD1  cells=8 last3=['**reuse**', 'decoded', 'speed reads correctly in a drive']
HUD-1  T-HUD2  cells=8 last3=['**map**: boost = nitrous; upgrade badges have no member', 'decoded', 'boost fills/drains the nitro meter']
HUD-1  T-HUD3  cells=8 last3=['**map** health; armour is out', 'decoded', 'damage paints the bar, heals cleanly']
CAM-1  T-CAM5  cells=8 last3=['**`CameraPosition [0,1.30,7.00]`**, `LookAtPoint [0,1.55,0]`', 'decoded', 'distance at rest']
CAM-1  T-CAM2  cells=8 last3=['`FOV [55,63]` v; 68 only if the +10 speed bonus is folded in; **95 boost is a gap**', 'decoded', 'wide chase, no fisheye']
CAM-1  T-CAM12 cells=8 last3=['**400 cm boom, additive to the sit offset** (T-CAM5)', 'decoded', 'distance at rest']
CAM-2  T-CAM10 cells=8 last3=['**superseded by T-15** (D-2): no battle-camera member, ...', 'decoded', "T-15's variant table"]
```

All six HUD-1/CAM-1 rows carry a **proposal**, a **confidence class** and a **take** — exactly what
R5's "behaviour row with a take that can fail" asks for. The tool reads them as "no disposition"
because the proposal cells read `reuse` / `map` / a literal value instead of `keep`/`next`/`mapped`.

A seventh distinct anchor, `T-CAM10`, states `**superseded by T-15**`; the reader has no word for
`superseded`, so a superseded row is filed as `documented` too.

**Consequence, computed from the same run.** The gate's split would be **53 carried / 9 named
omission / 5 blocked / 8 documented**, and the document-anchor census would read *carried 9,
documented 14, superseded 1* instead of the published *carried 3, documented 21, superseded 0*:

```
doc_stats (as shipped): {"anchors": 34, "by_state": {"blocked": 4, "carried (document row)": 3,
  "documented": 21, "named omission": 6}, "carried_total": 51,
  "carried_codes_with_doc_anchor": 11, "codes_with_doc_anchor": 27}
```

§12 (`| T-23 | done | …`) prints: "**51 carried / 9 named omission / 5 blocked (`AUD-1`, `AUD-4`,
`HUD-2`, `WPN-4`, `WPN-5`) / 10 documented with no disposition (`ANI-2`…`ANI-9`, `CAM-1`, `HUD-1`,
counted, not called carried)**". `CAM-1` and `HUD-1` are named there as having no disposition; both
have a proposal, a class and a take on every row.

**Verdict: BROKEN.** The bug is a fixed keyword list standing in for a table schema (R5: the tool
reads the row by a word it hopes to find, not by the row's behaviour), and the MODLOG's "rework —
done" §2/builds the whole new split on it. Every affected number is script-derived (R11 satisfied)
but from a mis-reading; the fix belongs in the generator (parse the T6 columns or add `reuse`/`map`/
value-proposals/`superseded` to the vocabulary), not in the page.

---

## A4 · A document row's state is read from the first line containing its id

**The assumption (silent).** `doc_row_state()` does
`for i, l in enumerate(lines): if anchor in l: line, at = l, i; break`. First substring hit wins —
across the whole document, including summaries, prose and other rows' cells.

**Test.** A2's print shows the hits. Four row ids are resolved from a line that is not their row:

| anchor | line actually read | what the row itself says |
|---|---|---|
| `P-02` | `\| internal rows (no joint, reason given) \| P-02, P-05, P-13 \|` | `\| P-02 \| batmobile_cannon \| Cannon \| — \| … \| static \| … \| -5.0…20.0° … \|` |
| `P-05` | same summary line | `\| P-05 \| batmobile_jet \| EngineRotatingPart \| … \| static \|` |
| `P-13` | same summary line | `\| P-13 \| — \| SteeringWheel \| — \| n/a \| … \| static \|` |
| `P-03` | `\| joints that are a continuous spin \| P-03 \|` | `\| P-03 \| batmobile_machine_gun \| GatlingGun \| … \| 6.00 turns / 2160.0° in 3.90 s \|` |
| `hijack objects` | a sentence, `cells=1` | no row; the anchor is prose in T9 |

For these five the answer is right by luck (`documented` happens to be the verdict a reader would
also reach for P rows), but the mechanism is not reading the row. Two further failure modes follow
from the same code: `anchor in l` also matches an id appearing inside another row's cell or a
heading, and the heading branch (`line.lstrip().startswith("#")`) concatenates the heading plus the
next eight lines, so a heading whose body mentions "blocked" would flip every anchor under it.

**Verdict: BROKEN** as a reader (A3 is the case where the same code produced a wrong answer). It is
not a T-23-specific bug — `doc_row_state` was written by the rework — and the fix is the same one:
resolve the table row by its first cell, not by substring, and parse the columns.

---

## A5 · "rows assumed = 1 of 180"

**The assumption (stated).** The count comes from `status_audit.build()["t"]["total"]["assumed"]`;
`status_audit.row_kind()` classifies the confidence cell into `blocked / out / assumed / evidenced
/ other`. `t23_closeout.assumed_gate()` then lists the assumed rows from `T_ROWS.jsonl` only.

**Test 1 — what the classifier actually sees.**

```
$ python -c "import status_audit; print(status_audit.build()['t']['total'])"
{"evidenced": 126, "assumed": 1, "blocked": 17, "out": 43, "superseded": 8, "other": 36, "rows": 231}
```

In scope = 231 − 43(out) − 8(superseded) = **180**. Of those 180, 126 are evidenced, 1 assumed,
17 blocked — and **36 are `other`**, i.e. the confidence cell matched no class at all. Those 36 are
*inside* the 180 denominator and *outside* every numerator the page prints.

**Test 2 — which rows are they.**

```
ledger rows classified other: 27
  T-R1  edit      **3.0 / 3.0** (fleet median by mass class is 3.0 in every class: ...)
  T-P3  next      written (G2-30): 11 driveable boxes map onto 7 donor hull slots; ...
  T-CO2 next      measured (T-22)
  T-CO3 keep      measured (T-22)
  T-DM9 next      measured (test-087, fleet domain) + decoded (232 entity graphs, ...)
  T-WP1 next      clone w602 under a private path, bind it to `main_weapon`, set fire_rate 2 ...
  T-WP2 next      clone w603, bind it to the second driver slot, ...
  T-WP3 next      clone w618, move it to the free driver slot (T-WP13), ...
  T-L8 … T-L35 (14 rows)  donor row 13 (`HeadLight`, preset ...) hangs on ...
  T-A2, T-K2, T-B3, T-WP11, T-WP12 ...
T6 other: T-HUD11, T-HUD12, T-HUD13, T-HUD14, T-HUD15, T-HUD16, T-HUD17, T-HUD18, T-HUD20
```

These are not stray rows: `T-P3`, `T-CO2`, `T-CO3` are the T-22 collision values, `T-WP1…3` are the
three cloned weapons, `T-L8…L35` are the light values — the rows phase B will write. Their cells say
`measured (T-22)`, `written (G2-30)`, `donor row 13 (…)` — prose, not one of R4's classes
(`decoded`, `decoded (fleet)`, `derived`, `class`, `epe`, `read`). The auditor neither rejects nor
reports them; it files them under `other`, and gate TX never prints `other`.

**Test 3 — two different row sets.**

```python
count  = status_audit.build()["t"]["total"]["assumed"]      # 231 rows, includes T6_HUD_CAMERA.md
rows   = ledger()                                           # 198 rows, T_ROWS.jsonl only
unsigned = [a["id"] for a in assumed_rows if not a["signed_off"]]
```

Today `t6.assumed = 0`, so the two agree by luck. If the one assumed row were a T6 row, the page
would print "assumed 1 … none, unsigned 0" — a count with no row behind it and no sign-off check.
`in_scope` also silently includes 25 in-scope T6 rows (33 − 7 out − 1 superseded) that are not in the
198, which is why 198 − 36 − 7 = 155 ≠ 180.

**Verdict: WEAK.** The card's step 2 ("confirm `rows assumed` = 0 except signed-off rows") is
confirmed for 144 of 180 in-scope rows; for the other 36 it is **not determined**, and nothing on the
page says so. I found no evidence that any of the 36 is actually assumed — that is why this is not
BROKEN — but the claim "1 of 180" is a claim about the classifier's vocabulary, not about the ledger.

---

## A6 · The base tree's 54 applied values are vetted, so a B step only copies them

**The assumption (stated in `BUILD_BATCHES.md` §3).** "`Builds/test-091` is the phase-B base. These
values are already applied and read back; a B step copies them, it does not re-apply them." Gate TX
counts them (`t5_applied.json` 35/16 … `t5e_applied.json` 2/1) and never checks them against the
ledger's current dispositions.

**Test — join every applied value to its ledger row and print the rows that are no longer buildable.**

```
$ python - (join t5*_applied.json rows against T_ROWS.jsonl)
applied values 54
applied values whose ledger row is out/blocked/superseded/absent: 2
   ('t5b_applied.json', 'T-DM7', 'VehicleDamage', 'impact_damage_factor', 1.0, 'out')
   ('t5b_applied.json', 'T-DM7', 'VehicleDamage', 'impact_armor', 5.0, 'out')
rows touched by base builds: 23 {'T-DM2': 1, 'T-K1': 2, 'T-A2': 1, 'T-A4': 1, 'T-AU4': 1,
 'T-E1': 3, 'T-E3': 2, 'T-M4': 2, 'T-R1': 2, 'T-G5': 1, 'T-ST1': 5, 'T-M1': 1, 'T-M2': 3,
 'T-S1': 2, 'T-S2': 2, 'T-E4': 6, 'T-DM7': 2, 'T-DM6': 1, 'T-K2': 4, 'T-B3': 3, 'T-B2': 3,
 'T-ST5': 4, 'T-S3': 2}
```

`T-DM7` is `out` in `T_ROWS.jsonl` with confidence `decoded (class API)` — i.e. the ledger has since
decided that the JC3 damage system does not express that row. Test-087 (`t5b_applied.json`) still
ships `impact_damage_factor` 1.0 and `impact_armor` 5.0 from it, and §3 itself attributes that
record to the `Builds/test-091` base the B steps copy. The applied records carry no confidence field at all (`keys: row, module, member, old, new,
file, kind, applied, size_before, size_after, members_unchanged`), so nothing in the base can be
audited on its own terms.

**Verdict: BROKEN** — not for the values themselves (they may be exactly what ARM-3 wants; `T-DM8`
is the live row for `impact_damage_factor` 0), but for the claim §3 makes about them. A close-out
card that lists "what the base already carries" without joining it to current dispositions leaves
2/54 values (3.7 %) in the build that no current row authorises, and phase V will gate a tree
containing them. This is a real gap the card was in a position to catch — it already reads all five
applied records.

---

## A7 · "14 artefacts (12 payloads + 2 records)" is the whole artefact set

**The assumption (silent).** The set is built by `discover_payloads()` — `os.walk(Working/)` for
`*.json` whose own `card` field matches `T-\d+` — **plus** the hand-written `BATCH_KIND` table
(`t19_hud.json`, `T10_OPEN_ROWS.json`, `damage_switches.json`, …). A payload JSON elsewhere, or one
without a `card` key, is invisible.

**Test 1 — scan the whole repo for card-bearing JSONs.**

```
T-21     .\Working\Appearance\appearance_plan.json
B-03     .\Working\Appearance\build_lights\lights_manifest.json
T-10     .\Working\Translation\T10_OPEN_ROWS.json
T-12     .\Working\Translation\T8_PARTS.json
T-23     .\Working\Translation\build_batches.json
T-14     .\Working\Translation\t10_damage_edits.json
T-15     .\Working\Translation\t11_variants.json
T-16     .\Working\Translation\t12_audio_map.json
T-18     .\Working\Translation\t14_lights.json
T-20     .\Working\Translation\t15_world.json
T-22     .\Working\Translation\t16_collision.json
T-17     .\Working\Translation\t17_fx.json
T-19     .\Working\Translation\t19_hud.json
T-11     .\Working\Translation\t7_weapons_edits.json
T-13     .\Working\Translation\t9_interaction.json
total 15
```

15 repo-wide; the tool's own output and the B-03 manifest are (correctly) out of scope, leaving the
13 T-carded payloads + `damage_switches.json` (which has **no** `card` field and is in the set only
because the table names it) = 14. So the arithmetic is right *inside its rule*.

**Test 2 — does the rule cover the phase-B edit files the cards actually name?**

```
$ ls Working/Parts Working/Entity Working/Weapons Working/Audio
ls: cannot access 'Working/Entity': No such file or directory
ls: cannot access 'Working/Weapons': No such file or directory
Working/Parts: (present)
```

B-04's `Out` is `Working/Parts/bm_vehicle_parts.json`, B-05's is
`Working/Entity/bm_epe_edits.json`, B-06's is `Working/Weapons/manifest.json`, B-11's is
`Working/Audio/bm_bank_manifest.json`. `Working/Parts/` exists but holds only `PRT1_PARTMAP.md`; the
other three directories do not exist. None of those files is in the batch list. They are future outputs, so listing them now would be wrong — but that is exactly why
"14 artefacts … 3 with no step" is a statement about **today's** files, not about phase B's payload
surface.

**Verdict: WEAK.** The count is right and the tool reports the one real hole (`t19_hud.json`, no
`hud.gfx` writer in B-01…B-14). The completeness claim rests on a directory (`Working/`) and a
convention (`card` key) that phase B's own `Out` paths already break; a payload saved outside
`Working/`, or without the key, would be counted by nobody.

---

## A8 · The `(rows / values)` column is two numbers read from each file

**The assumption (stated).** `BUILD_BATCHES.md` §4's header: "The payload column is the edit file the
step applies; the rows and values are read from that file's own record." The generator:

```python
def payload_rows(path):
    for key in ("rows","edits","objects","components","parts","variants","switches"):
        v = d.get(key)
        if isinstance(v, (list, dict)):
            return len(v), len(v)          # <-- same number, twice
```

**Test — count the leaves each record actually holds, next to what the page prints.**

| file (card) | what the page prints | entries | leaf values in those entries | leaves in the whole file |
|---|---|---|---|---|
| `T8_PARTS.json` (T-12) | (15 / 15) | 15 | 2,013 | 2,115 |
| `t9_interaction.json` (T-13) | (85 / 85) | 85 | 2,616 | 2,686 |
| `t12_audio_map.json` (T-16) | (53 / 53) | 53 | 3,124 | 5,278 |
| `t14_lights.json` (T-18) | (28 / 28) | 28 | 1,384 | 2,785 |
| `t17_fx.json` (T-17) | (17 / 17) | 17 | 821 | 867 |
| `t15_world.json` (T-20) | (19 / 19) | 19 | 323 | 748 |
| `t11_variants.json` (T-15) | (15 / 15) | 15 | 315 | 695 |
| `t10_damage_edits.json` (T-14) | (9 / 9) | 9 | 81 | 317 |
| `t7_weapons_edits.json` (T-11) | (3 / 3) | 3 | 30 | 79 |
| `t19_hud.json` (T-19) | (10 / 10) | 10 | 140 | 158 |
| `T10_OPEN_ROWS.json` (T-10) | (16 / 16) | 16 | 402 | 434 |
| `damage_switches.json` (none) | (5 / 5) | 5 | 15 | 18 |
| `t16_collision.json` (T-22) | (3 / 3) | 3 | 3 | 662 |

The "values" column is the "rows" column. There is no file on the page where the two are different,
because the second is generated from the first. `t16_collision.json` is the only genuine 3/3 — its
three rows happen to be scalars — and it is the exception that shows the rest are not measurements.

**Verdict: BROKEN** (R11's spirit: a count that looks generated and is instead a duplicate). This is
the card's core deliverable — "the build batch list (which edits file goes into which build step)" —
and its per-step size column overstates precision: `t12_audio_map.json` is not "53 values", it is
3,124, a 59× difference that matters for a reviewer asking "how big is step B-11".

---

## A9 · One curated table maps each payload to the one step that applies it

**The assumption (stated, and hedged in MODLOG limit 5).** "The payload → step mapping is glue, and
glue can be wrong once."

**Test 1 — is every listed step a live step?** `BATCH_PAYLOADS["t11_variants.json"] = ["B-12"]`, so
the page prints

```
| B-12 · Variants (only if D-2 = two variants) | `Builds/bm-012/` | `t11_variants.json` (15 / 15) | D-2 (resolved) | `aafdiff` between variants … |
```

D-2 in §11 is `resolved 2026-10-28 (user): (b) one hybrid car` and its own cell says
`B-12 skipped: D-2`; §12 has no B-12 row (the range row `| B-04 … B-14 | todo | |` covers it). So the
batch list counts a step that must not run as one of the "14 B steps", gives it a payload, and `B-13`
lists `deps: B-12`.

**Test 2 — do the cards name the payloads they are given?**

```
| B-02 | `T8_PARTS.json` (15 / 15), `appearance_plan.json` (172 / 172) |
| B-03 | `appearance_plan.json` (172 / 172), `t14_lights.json` (28 / 28) |
```

B-02's card says `--parts T8_PARTS` (named) but never mentions the appearance plan; B-03's card says
"write the `CarLight` block with values from T-18" (names T-18, not the file). `appearance_plan.json`
is T-21's output: `card: T-21`, 172 `components` (paint/material routing: `bake`/`drop`/`route`,
POL-1/POL-2). Phase B has **no appearance step** at all — B-02 keeps materials, B-03 writes lights —
so the 172-row appearance plan is a payload with no dedicated step, presented as if B-02/B-03 consume
it. That is the same class of hole `t19_hud.json` is reported for, minus the report.

**Test 3 — count.** 12 payload names, 11 of them with steps (18 payload→step links because of
reuse), 2 steps with no payload (`B-01`, `B-14`). "14 artefacts … over 14 B steps" is 14 = 14 by coincidence (12 payloads + 2
records; 14 cards), not by a one-to-one mapping.

**Verdict: WEAK.** Every named file exists and every step id exists, so the glue cannot silently
dangle — but "which edits file goes into which build step" is answered with a reading that (a)
includes a step the decision register skipped, (b) leaves an orphan edges onto it, and (c) files the
appearance plan under two steps that do not name it. MODLOG limit 5 says a glue error is possible;
this is that error, twice.

---

## A10 · "777 G1 feature rows -> 34 T rows, 0 unassigned" is a feature census

**The assumption (stated).** `bmak_coverage.py` "G1 feature rows": one row of the G1 file = one T
row; an unmatched row is a FAIL. 777 = WEAPONS 62 + ANIMATIONS 253 + AUDIO 361 + LIGHTS 101.

**Test 1 — are 777 rows 777 features?** Each of the four records spans the four Batmobile packages:

```
weapons objects 62  distinct (class,name) 24  packages 4
anim sequences 253  distinct name 128  packages 4  duplicate_names 51
audio events 361  distinct name 118  packages 4
light entries 101  distinct (socket,behavior,dispo) 29  rigs 4
sum of distinct-name counts: 299
```

So the census that reads "777 feature rows" is 299 distinct features with 4-package duplication
(2.6×). The card's wording is "every G1 file row", so file rows is defensible; the §12 phrase
"777 G1 feature rows" is not.

**Test 2 — where do the 777 land?** From `Research/BatmobileGrab/COVERAGE.md`:

```
| `T-PA9` | 174 | no cut part moves / character dialogue / world audio |
| `W-08`   | 120 | AUD-4: the 30 battle-mode events need a mode switch a hybrid has not |
| `T-AU3`  |  90 | the bank is absent from the install |
```

174 + 120 + 90 = **384 of 777 (49 %)** are assigned to a plumbing row (`T-PA9`, the tool's
"Unreal actor plumbing" bucket), a **blocked** row (`W-08`) or a row whose reason is that the media
is missing (`T-AU3`). "Assigned" is therefore satisfied for them, "covered" (the card's word in step
3) is not. The W-08 note is also wrong on its face: it says "the 30 battle-mode events" under 120
assigned rows — 30 is the distinct count, 120 is the 4-package count, and the generated file does not
say which.

**Test 3 — is the rule set stable?** `audio_row()` has keys for 10 of the 14 audio groups;
`lock-on-ui` (23), `sonar` (18), `death` (4), `tracker` (4) have **no** mapping rule and are assigned
only because `status == "missing-bank"` is tested first:

```
('lock-on-ui','missing-bank') 23   ('sonar','missing-bank') 18
('death','missing-bank') 4         ('tracker','missing-bank') 4
```

A group that is later resolved (not missing-bank) and has no rule would fail loudly, which is the
right contract — but it means "0 unassigned" today is partly produced by an earlier catch-all, not by
the group table.

**Verdict: WEAK.** Counts reproduce exactly (62/253/361/101, 34 distinct T rows, 0 empty) and the
rule set is explicit. What is inflated is the *meaning*: half the rows are "assigned" to a row that
does not build them, and the headline number is package instances, not features. The card's own
`Done` says "every G1 file row is assigned to a T row", which is true; the §12 summary presents it as
feature coverage.

---

## A11 · The 9 `named omission` + 5 `blocked` codes are "no carrier exists" claims

**The assumption (stated).** A `named omission` is a terminal, acceptable state in gate TX (it is
neither unmapped nor a problem), so 9 codes close on it: ARM-5, AUD-3, AUD-6, HDL-6, WPN-6…WPN-10.
§1.4 adds the constraint that no weapon is `out` until G2 proves no carrier.

**Test 1 — is the search written down, and where?** `Research/JC3Grab/G2X.md` (the phase-G2 exit
gate) carries an explicit absence row per code, each naming what was scanned:

```
| WPN-6 | absence | vocab-scan | scan | VOCABULARY.md | no winch member path in the 52-type /
1,421-path vocabulary and no winch class in the 103-class fleet census (0 occurrences in both,
measured); rope/winch geometry ships on 4 entities (TETHER.md §4) but no part can pull …
| WPN-8 | absence | vocab-scan | scan | ENTITIES.md | no sonar class in the 103-class census;
CForcePulse is the shockwave half only …
| WPN-9 | absence | vocab-scan | scan | ENTITIES.md | no tracker class in the 103-class census
(the only 'track' is CMusicTrack) …
| AUD-3 | absence | vocab-scan | scan | JC3_AUDIO_EVENTS.json | no cabin/interior event name in
the 45-event donor census (0 occurrences of either, measured) …
```

and `Research/JC3Grab/TETHER.md` §4 is the most careful of them:

```
The mechanic is not there:
- The fleet's 53 module types contain 0 tether/cargo/rope/winch/tow type (none).
- Parts-module behaviours over all 11,643 fleet part rows: 7,367 None, 67 distinct named behaviours …
  None is a winch, rope, tow or reel, so no vehicle part can pull another vehicle.
- Functional winch classes anywhere in the fleet: 0.
WPN-6 verdict: a carrier exists for the geometry (copy transport_rope_winch …) and the mechanic is a
proven absence. … JC3's pulling is Rico's grapple/tether, which belongs to the character, not the vehicle.
```

**Test 2 — is "0 classes" the right kind of evidence?** The backlog's own corrections show the
failure mode: §2.1 reopens `T-W1` because "JC3 gives a car no player-fired weapons" was wrong, and
§2.2 reopens `T-FX4` because the EMP exists *without* a weapon class (`CForcePulse` on the truck).
A class-name / module-type / vocabulary scan is exactly the instrument that produced both wrong
answers. TETHER §4 mitigates this by checking three spaces (module types, 11,643 part behaviours,
class census) plus the 335-path index scan and by stating the one carrier that *does* exist (the
geometry). WPN-6's row in `T7_WEAPONS.md` records the same three checks.

**Verdict: HOLDS**, with the risk stated in the row rather than hidden: the absences are searched
spaces that are named, bounded and reproducible, and the one carrier that exists (winch geometry) is
reported instead of suppressed. The residual assumption — that a graph-script/native implementation
with no class would be invisible, as the EMP's was — is real and is not tested by any of the five
weapon codes. If one of these omissions is ever challenged, `T-20`/`G2-17`'s `id:*`-hash census of
graph objects (31 unnamed members on `CForcePulse` alone) is the place to re-run it.

---

## A12 · "D-1…D-10 answered"

**The assumption (stated).** `decision_gate()` marks a decision answered iff
`re.search(r"resolved\s+(\d{4}-\d{2}-\d{2})", answer_cell)`; otherwise it needs a row whose cells say
`blocked: D-n`, else it adds a problem. It also requires exactly 10 decisions.

**Test.** All ten §11 cells carry `resolved 2026-10-2x` and the gate prints
`D-1 answered, … D-10 answered`; `len(decisions) != 10` is a problem and does not fire. The
`blocks` column is then reused for the per-step decisions in §4 of `BUILD_BATCHES.md`
(`D-4 (resolved)` on B-04/B-05, `D-2 (resolved)` on B-12, `D-6 (resolved)` on B-13).

**Verdict: HOLDS** for the card's Done clause ("answered or their rows are `blocked: D-n`"). What
the check cannot see is whether the answer is *coherent with the build list* — D-2's answer skipped
B-12 and the batch table keeps it (A9). That is a mapping defect, not a decision defect.

---

## A13 · "One command", the check runs its three siblings

**The assumption (stated).** The rework's fix 5: `--check` runs `t_rows.py check`,
`status_audit.py --check`, `bmak_coverage.py --check` and fails on any non-zero exit.

**Test 1 — code path.** `sibling_checks()` runs each via `subprocess.run([sys.executable, …])` with
`cwd=ROOT`; `main()` appends a `bad` entry per non-zero exit and returns 1 if `problems` is non-empty.

**Test 2 — exercise the failure branch without touching a file** (monkeypatch the sibling runner in
memory; `--write` is not passed, nothing is written):

```
$ python - (t23_closeout.sibling_checks = lambda: [{"check":"t_rows.py check","exit":1,…}]; main())
gate TX: 75 codes (51 carried, 9 named omission, 5 blocked, 10 documented, 0 unmapped) | …
siblings: t_rows.py check exit 1
FAIL t_rows.py check exits 1: simulated ledger sum failure
1 problem(s)
simulated main() returned 1
```

**Test 3 — what the command does not do.** The card's step 1 is
"`t_rows.py check`, `status_audit.py --write` then `--check`". The tool runs `--check` only. If
`STATUS.md` is stale the gate fails and tells the operator to run `--write` (the rework's own tamper
table records exactly that: "status_audit.py --check exits 1: STATUS.md is stale; run --write"). So
the "one command" claim covers 5 of the 6 acts in step 1; the sixth is still manual, which is safe
but not what "one command" suggests.

**Verdict: HOLDS.** The sibling plumbing is real and fails correctly.

---

## A14 · Unit and coordinate conventions

**Observation.** `BUILD_BATCHES.md` has no physical quantity on it: no metres, no KB, no angles — the
units live in the T-1…T-22 documents and in the §8 `Done` gates ("Model KB ≤ 4,915", "hull union bbox
within 5 cm"). So there is no unit or coordinate convention to break here, and that is a strength of
the card's scope.

**What replaces it is a vocabulary of counts**, and that is where the conventions fail:

| word on the page | what it means | evidence |
|---|---|---|
| "row" | a `T_ROWS.jsonl` line (198) **or** a document table row **or** a G1 file row over 4 packages **or** a leaf | A2/A5/A10 |
| "values" | the row count again | A8 |
| "documented" | "no keyword matched", not "no disposition" | A3 |
| "carried" | "≥ 1 of the code's rows is carried" | A2 |

**Verdict: N/A as a unit claim; BROKEN as a vocabulary claim** — the same word carries four
different meanings across the page, and the one place a second quantity was needed (values) it was
duplicated from the first.

---

## What would change the verdicts

1. `doc_row_state()`: resolve the table row by its first cell; parse the disposition/take columns
   instead of grepping seven words; add `reuse`, `map`, `partial`, a value proposal and
   `superseded`. Then the split becomes 53/9/5/8 and §12 can be corrected (A3/A4).
2. `payload_rows()`: count leaves (or the count the record itself declares) for "values" (A8).
3. `assumed_gate()`: report the `other` bucket and fail when an in-scope row's confidence cell is not
   one of R4's classes (A5).
4. `batch_gate()`: join the five `t5*_applied.json` records to the ledger and fail on a value whose
   row is `out`/`blocked`/`superseded` (A6); mark `B-12` (and any step its decision cell skips) as
   `skipped: D-n` rather than a step with a payload (A9).
5. Coverage: print distinct-feature counts next to package-instance counts (A10).

Checked, re-runnable, and every quoted output above came from the current tree on 2026-10-30. No
game was launched, no file outside this report was written, nothing was committed.
