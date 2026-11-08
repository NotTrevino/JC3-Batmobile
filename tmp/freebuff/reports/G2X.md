# G2X — the G2 exit gate

**Item:** `GRAB_BACKLOG.md` §6, last paragraph (G2X has no numbered card, only the exit-gate text):
*"every new reader has `--check` green; P0-2 census re-run; every feature code in §1 has a JC3
carrier with evidence or a proven absence. MODLOG section 'G2X'."*

**Session:** 2026-10-28. Nothing was resumed: `grep -n "G2X" MODLOG.md` returned 0 hits before the
first edit, so no earlier session had started this item.

## STATUS

**done**

Prerequisites verified before starting (§0.2 step 2): all 25 prerequisite cards `G2-10`…`G2-34` are
`done` in §12 and each has a `## G2-… — done` heading in `MODLOG.md` (25 headings found). No §11
decision sits in G2X's `blocks` column: the seven rows whose *value* waits on D-2 / D-3 / D-5 are
recorded as `carrier + decision`, which is what §7 rule 6 asks for (`blocked: D-n` is a phase-T
state), so the gate was not deferred.

Result: **75 feature codes — 67 carriers with evidence, 8 proven absences, 0 unresolved**; the 24
G2 readers plus the P0-2 census re-run **25/25 green**.

## Outputs

| path | what |
|---|---|
| `Tools/scripts/g2x_gate.py` | new. Runs the 25 readers as subprocesses, re-derives the 75 feature rows, records the §11 decision state; `--write` / `--check` / `--check --no-readers` / `--markdown` |
| `Research/JC3Grab/G2X.md` | generated, 171 lines: the clause-by-clause gate, the reader table with each verdict line verbatim, the 75-row carrier table, the absences stated once, and what the gate cannot prove |
| `Research/JC3Grab/G2X.json` | generated: the same object as data (schema 1) — readers, census block, 75 rows, summary counts |
| `Research/JC3Grab/README.md` | one command pair (`--write` / `--check`) and one `Files` row |
| `GRAB_BACKLOG.md` §12 | **one added row** `G2X | done | …` after `G2-34` (the tracker had none); nothing else in the file was rewritten |
| `MODLOG.md` | intended-change entry + `## G2X · G2 exit gate — passed (2026-10-28)` (append-only) |
| this file | `tmp/freebuff/reports/G2X.md` |

Game data: none produced. The readers the gate calls read the existing `E:\Modding\JustCause3\_grab\`
decodes; nothing was written under `_JC3grab` or `_BmAKgrab` by this item, and no game, install,
dropzone, save or git operation was touched.

## Done-check command and output (verbatim)

```
> python Tools/scripts/g2x_gate.py --write
wrote Research/JC3Grab/G2X.md + Research/JC3Grab/G2X.json (75 codes: 67 carrier, 8 absence, 7 decision-gated; readers 25/25)

> python Tools/scripts/g2x_gate.py --check
PASS: 75 codes (67 carrier, 8 absence, 7 decision-gated) in 28 files | readers 25/25 green | census ok | json match True, md match True
```

exit 0. Re-run after the last edits (`--check --no-readers`, exit 0) gave the same summary line —
the tracker row, README row and MODLOG append are not gate inputs.

Standing gates re-run the same session (§0.7, JC3 side):

```
> python Tools/scripts/jc3index.py check
check ok: 81952 rows, 78907 paths, 1 unnamed entries, DLC 20682/20682 named, sources {'gibbed-filelist': 55811, 'jcmr-dictionary': 26051, 'derived-names': 90}
> python Tools/scripts/jc3hkx.py check --all
check ok
> python Tools/scripts/jc3fx.py check
checked 57187 files | problems 0
> python Tools/scripts/status_audit.py --check
STATUS.md is current
```

`status_audit.py --check` was run although no translation row was touched (§0.2 step 8 asks for it
only then); it proves the shared ledger is untouched.

## Tamper test

Three tampers, each restored from a pre-tamper copy and the tree re-verified green.

1. **JSON count.** `G2X.json` `summary.carrier` 67 → 66 →
   `FAIL G2X.json stale: summary block differs` and the summary line
   `FAIL: 75 codes (67 carrier, …) … json match False, md match True`, **exit 1**.
2. **Markdown cell.** `G2X.md` row `APP-1` verdict `carrier` → `absence` →
   `FAIL G2X.md stale:` with the one-line diff
   (`-| APP-1 | absence | needle | …` / `+| APP-1 | carrier | needle | …`),
   `md match False`, **exit 1**.
3. **The negative half.** An absence row cannot be tampered by editing an output, because the proof
   is the *source census not containing a word*. So it was tested directly: `WPN-8`'s `must_not`
   list was pointed at `max_health` (a word that **is** in `VOCABULARY.md`) →
   `row pass = False` / `WPN-8: Research/JC3Grab/VOCABULARY.md names max_health: the absence is
   refuted`. A proven absence therefore fails the moment the mechanism starts appearing in the
   fleet's decoded space.

`python -m py_compile Tools/scripts/g2x_gate.py` → OK.

Two generator bugs were caught by these runs and fixed before the done check: a `KeyError:
'decision_state'` on rows without a decision, and — more dangerous — a "last output line must start
with PASS" rule that marked the all-green `damage_predict.py` red (that script prints `PASS:` first
and two more lines after it). The gate now takes the first verdict line.

## UNKNOWNs and limits

* **A proven absence is a statement about names, not about the engine.** The 8 absences are proved
  against complete census surfaces (`ENTITIES.md`, 103 classes; `VOCABULARY.md`, 52 module types /
  1,421 member paths) and say so in `G2X.md` §4. Six codes lean on native code and remain UNKNOWN at
  that level: turn-on-the-spot (G2-21), the eject launch (G2-20), the effect trigger names (G2-22),
  graph bytecode (G2-17).
* The 8 absences are `ARM-5`, `WPN-6`, `WPN-7`, `WPN-8`, `WPN-9`, `WPN-10`, `HDL-6`, `AUD-3`. Each is
  the named omission its phase-T row already assumed; none is "deferred".
* **Three values the files do not give are left UNKNOWN, not filled in:** the `RigidBody.mass` unit
  (DIM-3 — 6 t stays a class row, compared as a ratio 6.154× the donor's 975), the
  explosion-threshold semantics (G2-28 step 7), and whether the module light list or the `.epe`
  `SVehicleLight` list renders (G2-33).
* **A carrier is not a build.** HUD-1/HUD-2 still need the entity → `hud.gfx` bridge, which is game
  code (`JC3_HUD_WEAPONS.md` caller census), and APP-6 / MOD-2 / LGT-2 / CAM-2 / AUD-4 still need
  D-2 answered. D-3 (lethality, WPN-10) and D-5 (skins, APP-8) are open too.
* `jc3fx.py check` takes ~7.7 min and `jc3traffic.py --check` ~1 min (7.7 GB scan), so a full
  `--check` is a ~4 min command; `--check --no-readers` is the fast structural form used for tamper
  runs.
* The G2-1…G2-9 archive readers are the §0.7 standing gates, re-run above, not inside the tool.

## MODLOG heading used

```
## G2X · G2 exit gate — passed (2026-10-28)
```

preceded by the required intended-change entry:

```
## G2X · G2 exit gate — intended change (2026-10-28)
```
