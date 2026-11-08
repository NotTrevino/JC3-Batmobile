# Rework — G2X · G2 exit gate

Review reworked: `tmp/freebuff/reports/review-G2X.md` (2026-10-29). Rework date: 2026-10-30.
Card: `GRAB_BACKLOG.md` §6 last paragraph (§12 row `G2X`). Rules applied: §0.5 R1–R14.

## STATUS: **DONE — 8 issues raised, 8 CONFIRMED, 0 REJECTED, all fixed at the generator; `--check` is green on disk (exit 0).**

| # | review issue | verdict | where the fix lives |
|---|---|---|---|
| 1 | gate red on disk; artefacts freeze §11 state and a reader's sentence | **CONFIRMED** | `--write` regeneration + status-only reader comparison |
| 2 | §1 not read; `EXPECTED_CODES` typed (R11) | **CONFIRMED** | `section1_codes()`; `EXPECTED_CODES` deleted |
| 3 | family breakdown in the md header typed | **CONFIRMED** | `family_text(section1_codes())` |
| 4 | "carrier with evidence" hides 9 word-needles / 19 short needles | **CONFIRMED** | `needle_kind()`, per-row `strength`, derived count line |
| 5 | 2 of 8 "proven absences" are prose needles, not negative scans | **CONFIRMED** | `WPN-6` + `AUD-3` → `vocab-scan`, one anchor per file |
| 6 | `--no-readers` indistinguishable from a full run | **CONFIRMED** | `(recorded)` in the summary; `readers_mode` in the JSON |
| 7 | `APP-1`'s fact mislabels 56,136 (fleet meshes, 233 entities) | **CONFIRMED** | row fact corrected |
| 8 | docstring describes the fixed "last output line" rule | **CONFIRMED** | docstring corrected |

**One thing the reviewer could not see.** When this session started, `Tools/scripts/g2x_gate.py` had
already been partly edited by an interrupted earlier attempt (an uncommitted "G2X rework — intended
change" section sat at `MODLOG.md:16470`) while `G2X.md`/`G2X.json` were still the 2026-10-28 05:13
files. So issues 2, 3, 5, 6 and 8 were **confirmed against the pre-rework artefacts and the review's
quoted source** and then verified fixed; the remaining gaps I had to close were: the artifacts
(issue 1, still stale), `WPN-6`'s second file having no anchor (issue 5, half-fixed), three
generated sentences still asserting the *rejected* D-2 route (same defect class as issue 1), and a
docstring sentence claiming the md prints "recorded" (it does not — and putting the mode in the md
would make `--check --no-readers` report the md stale, so the docstring is what changed).

---

## 1. Gate red on disk — CONFIRMED

**Before (this session, before any write):**

```
$ python Tools/scripts/g2x_gate.py --check --no-readers
FAIL G2X.json stale: rows differ for APP-1, APP-2, … , HUD-2      (all 75)
FAIL G2X.json stale: summary block differs
FAIL G2X.md stale: … -| decisions still open | **3** (D-2, D-3, D-5) | / +| decisions still open | **0** (none) | …
FAIL: 75 codes (67 carrier, 8 absence, 7 decision-gated) in 29 files | readers 25/25 green (recorded) | census ok | json match False, md match False
EXIT=1
```

(The review's own capture listed 7 differing rows instead of 75; by the time I ran it, the
interrupted edit had added `needle_kind` to every row, so every row differed.)

Both halves of the review's claim reproduce:

```
$ python - <<'EOF'   # recorded decision state in G2X.json vs §11
APP-6 decision= D-2 recorded_state= open
APP-8 decision= D-5 recorded_state= open
WPN-10 decision= D-3 recorded_state= open
MOD-2 decision= D-2 recorded_state= open
AUD-4 decision= D-2 recorded_state= open
LGT-2 decision= D-2 recorded_state= open
CAM-2 decision= D-2 recorded_state= open
summary: {… 'decision_open': ['D-2', 'D-3', 'D-5'], 'verdict': 'PASS'}
EOF

$ grep -n '^| D-\(2\|3\|5\) |' GRAB_BACKLOG.md
1258:| D-2 | … **resolved 2026-10-28 (user): (b) one hybrid car** …
1259:| D-3 | … **resolved 2026-10-28 (user): accept JC3 lethality, no toggle** …
1261:| D-5 | … **resolved 2026-10-28 (user): skins as extra Rebel Drop entries** …
```

and the recorded `jc3audio.py` sentence differed from the live one (`45 donor events in 3 banks, …`
vs the live `… 45/45 donor tunes, 257/257 tunes with an event GUID, 0/0 wave GUIDs …`).

**Fix (R11: regenerate, never hand-edit).** `python Tools/scripts/g2x_gate.py --write`. Plus the
structural half: `run_reader` records `exit`, the matched `verdict` token and the full `summary`, and
the staleness comparison uses **status only** (`label, command, exit, verdict, ok`); a changed
sentence now prints `NOTE … run --write to refresh it`, not `FAIL`. Regenerating the artefacts was
then the only remaining step, so a future §11 edit or a reworded reader cannot turn a green gate red
again — the gate's promise is "the reader is green", which is what it compares.

## 2. §1 is not read; `EXPECTED_CODES` typed — CONFIRMED

At review time `EXPECTED_CODES` was a hand-typed 75-code list (`["APP-%d" % i for i in range(1, 9)] …`)
and `grep -n BACKLOG` found it read only by `decisions()`. Verified now:

```
$ python -c … import g2x_gate; print(len(g.section1_codes()), len(g.ROWS), hasattr(g,'EXPECTED_CODES'))
section1 parsed: 75 | ROWS: 75 | unique codes: 75
section1 not in ROWS: []
ROWS not in section1: []
EXPECTED_CODES present: False
family_text: APP 8, DIM 4, ARM 6, WPN 12, HDL 6, MOD 5, AUD 7, ANI 9, WLD 8, LGT 2, FX 4, CAM 2, HUD 2
```

Set-equality with §1 is now **computed** (`section1_codes()` + `CODE_ROW_RE` over `## 1.` … `## 2.`),
not maintained by hand, and a mismatch in either direction is a problem string. Proved by tamper:

```
# GRAB_BACKLOG.md §1 gains a row `| HUD-3 | (tamper test row) | … |` before "## 2."
FAIL section 1 codes with no row: HUD-3
# ROWS loses HUD-2
FAIL section 1 codes with no row: HUD-2
```

## 3. Typed family breakdown — CONFIRMED

Old md line 13 read `| feature codes | **75** (the whole of §1: APP 8, DIM 4, … HUD 2) |` — the count
derived, the parenthetical a literal. Now the cell says `**75** (parsed from §1: APP 8, DIM 4, …)`
from `family_text(section1_codes())`, which reproduced the old literal exactly (see the output
above), so nothing changed numerically and the text can no longer drift from §1.

## 4. Evidence strength was implied, not shown — CONFIRMED

Review's counts reproduce exactly: 19 needles shorter than 8 characters, 7 of them numeric.

```
short needles: 19
   ('APP-1','56136','number') ('APP-3','Window','word') ('APP-5','11643','number')
   ('APP-6','179','number')   ('DIM-3','975','number')  ('ARM-1','shotgun','word')
   ('ARM-2','2000','number')  ('WPN-4','w702','identifier') ('HDL-4','40 km/h','phrase')
   ('MOD-4','canopy','word')  ('MOD-5','ambient','word') ('AUD-7','horn','word')
   ('ANI-1','wheel','word')   ('ANI-2','Cannon','word') ('ANI-8','canopy','word')
   ('ANI-9','0.855','number') ('WLD-4','stunt','word')  ('WLD-5','6000','number')
   ('CAM-2','T-CAM10','identifier')
```

**Fix.** `needle_kind()` derives `number` / `identifier` / `phrase` / `word`, the md prints a
`strength` column per row and a derived summary line, and the summary carries `needle_kinds`:

```
| evidence strength | numbers 7 · identifiers 43 · phrases 8 · short words 9 (a needle is only as strong as what it keys on) |
```

No row was promoted: the 9 short-word needles are still word needles (that is their honest
strength), but the file no longer lets "67 carriers with evidence" read as uniform.

## 5. Two "proven absences" were prose needles — CONFIRMED

Before (from `G2X.json.before-rework`):

```
WPN-6 OLD: needle ['Research/JC3Grab/TETHER.md'] 'Functional winch classes anywhere in the fleet: **0**'
AUD-3 OLD: needle ['Research/JC3Grab/JC3_AUDIO.md'] 'speedwind_sound_player'
```

**Fix.** Both are `vocab-scan` now, and a scan requires **one anchor per named file** (`anchors`
parallel to `files`), so every surface the fact names is proven read:

```
WPN-6 NEW: vocab-scan ['RESEARCH/JC3Grab/VOCABULARY.md','Research/JC3Grab/ENTITIES.md']
           anchors ['max_health','CPartProp']  must_not ['winch']
AUD-3 NEW: vocab-scan ['Research/JC3Grab/JC3_AUDIO_EVENTS.json']
           anchors ['speedwind_sound_player']  must_not ['cabin','interior']
```

The absences are real, measured on the files:

```
$ grep -c -i winch Research/JC3Grab/VOCABULARY.md            → 0
$ grep -c -i winch Research/JC3Grab/ENTITIES.md              → 0
$ grep -c -i cabin   Research/JC3Grab/JC3_AUDIO_EVENTS.json  → 0
$ grep -c -i interior Research/JC3Grab/JC3_AUDIO_EVENTS.json → 0
anchors: max_health 1 (VOCABULARY.md), CPartProp present (first class row of the 103-class
         inventory), speedwind_sound_player 1 (event census)
```

(`ENTITIES.md`'s class-inventory table has 105 `|` lines = header + separator + **103** classes,
matching the fact.) And both rows can now fail on what they claim:

```
# WPN-6 must_not "winch" -> "CCar" (present in ENTITIES.md)
FAIL WPN-6: the absence is refuted: 'CCar' in Research/JC3Grab/ENTITIES.md
# WPN-6 second anchor -> "no_such_class"
FAIL WPN-6: anchor missing: 'no_such_class' in Research/JC3Grab/ENTITIES.md (census surface not read)
```

Consequence: the md/JSON now span **29** files, not 28 — `AUD-3`'s evidence moved from prose in
`JC3_AUDIO.md` to the 45-event census `JC3_AUDIO_EVENTS.json`.

**Found while verifying (same class, not raised by the review).** Three generated sentences still
asserted the D-2 route the user rejected on 2026-10-28 ("(b) one hybrid car"):

* `markdown()`: *"D-2 (a second variant for battle mode) is the only decision that reaches the build
  route"* and *"CAM-2/APP-6/MOD-2/LGT-2 need D-2 answered"* — both false with D-2 resolved and would
  have been **re-written by `--write`**, i.e. the regenerated file would still contradict its own
  `state` column. Replaced by a sentence that names no route and a derived list of decisions *still
  open* (`waiting` is empty today, so §4 now ends at `hud.gfx`).
* Row facts `APP-6` ("two drop entries is the variant route") and `MOD-2` ("the second variant is
  the mode"). Reworded to "which drop entry carries it is section 11 D-2's answer, not this row's" —
  the carrier claim (turret/cannon part angles, `TANKTURN.md`'s named omission) is unchanged, and no
  new value was invented (R4).
* `APP-1`'s fact was also worded awkwardly by the interrupted edit (`… (GEOMETRY.md, not "body
  meshes") …`); now "56,136 meshes over 233 entities decode (GEOMETRY.md, a fleet count, not the
  Batmobile body); 806,529 material slots are counted per block" — both numbers re-read from
  `GEOMETRY.md:8-11` and `GEOMETRY.md:18`.

## 6. `--no-readers` was indistinguishable in a log — CONFIRMED

```
# before:  … | readers 25/25 green | census ok | json match False, md match False   (0.18 s, no reader run)
# now:     PASS: 75 codes (67 carrier, 8 absence, 7 decision-gated) in 29 files | readers 25/25 green
           (recorded) | census ok | json match True, md match True
# full run: … readers 25/25 green (re-run) | census ok | json match True, md match True
```

The mode also lands in the JSON (`"readers_mode": "re-run"`; the pre-rework file had `None`), and the
docstring states that the two artefacts are only written by `--write`, which always re-runs.

## 7. `APP-1`'s fact mislabelled its needle — CONFIRMED

Old md line 70: `| APP-1 | carrier | needle | … | all 56,136 body meshes decode; … — needle 56136 |`.
`Research/JC3Grab/GEOMETRY.md:8-11` reads `| entities | 233 |` / `| meshes | 56136 |`, i.e. a fleet
count over 233 entities, not "body meshes". Fixed in the row's fact (regenerated md line 80 now says
"56,136 meshes over 233 entities … a fleet count, not the Batmobile body"); the needle `56136` is
unchanged, so the check is exactly as strong as before.

## 8. Stale docstring — CONFIRMED

Old text (quoted by the review): *"their last output line is recorded … a line that does not start
with `PASS` … fails the gate"*. The code takes the **first** verdict line
(`last = verdicts[0] if verdicts else …`, with the comment "the verdict line is not always the last
one … so take the first line"). The docstring now says *"(the first such line is the verdict; readers
such as `damage_predict.py` print more lines under it)"* — description and behaviour agree.

---

## Files changed

| file | change | revert |
|---|---|---|
| `Tools/scripts/g2x_gate.py` | generator: §1 parse + `family_text`; `needle_kind`; `WPN-6`/`AUD-3` as per-file-anchored `vocab-scan`; status-only reader comparison; `(recorded)` mode; `APP-1`/`APP-6`/`MOD-2` facts; derived decision sentences; docstring | `cp tmp/freebuff/reports/.tamper/g2x_gate.py.bak Tools/scripts/g2x_gate.py` |
| `Research/JC3Grab/G2X.md`, `G2X.json` | regenerated by `--write` (never hand-edited) | `cp tmp/freebuff/reports/G2X.*.before-rework Research/JC3Grab/` |
| `Research/JC3Grab/README.md` | gate command comment: "every §1 feature row" instead of a typed count (pre-existing edit from the interrupted session, verified) | restore the comment |
| `GRAB_BACKLOG.md` §12 | the `G2X` evidence line only (status `done` unchanged) | put the old line back |
| `MODLOG.md` | "G2X rework — intended change" (before any edit) + "G2X rework — done" (append) | delete the two sections |
| `tmp/freebuff/reports/rework-G2X.md` | this report | delete |

Not touched: `Research/JC3Grab/*.md` other than `G2X.md`/`README.md`, any other script, `Working/`,
`Builds/`, `D:\Games\…`, saves. No game launched, no shared module edited, nothing committed.

## Check output (verbatim)

```
$ python Tools/scripts/g2x_gate.py --write
wrote Research/JC3Grab/G2X.md + Research/JC3Grab/G2X.json (75 codes: 67 carrier, 8 absence, 7 decision-gated; readers 25/25 re-run)
EXIT=0

$ python Tools/scripts/g2x_gate.py --check
PASS: 75 codes (67 carrier, 8 absence, 7 decision-gated) in 29 files | readers 25/25 green (re-run) | census ok | json match True, md match True
EXIT=0
```

(≈9 min wall, 25 readers re-run as subprocesses; the final `--check` was run **after** the §12 edit,
so the output above is the state of the tree as delivered.)

Standing gates re-run although no translation row changed (R14 courtesy check):

```
$ python Tools/scripts/status_audit.py --check
STATUS.md is current
EXIT=0

$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 40 keep 60 epe 26 re-read 0 blocked 13 out 36 superseded 7 | edits 35 over 16 rows
check ok
EXIT=0
```

## Tamper tests (6, each caught, each reverted; sha256 unchanged)

| tamper | output | exit |
|---|---|---|
| `G2X.json` `summary.carrier` 67 → 66 | `FAIL G2X.json stale: summary block differs` / `json match False, md match True` | 1 |
| `G2X.md` `APP-1` verdict `carrier` → `absence` | `FAIL G2X.md stale: …` (1 line) / `json match True, md match False` | 1 |
| §1 gains `HUD-3` | `FAIL section 1 codes with no row: HUD-3` | 1 |
| `ROWS` loses `HUD-2` | `FAIL section 1 codes with no row: HUD-2` | 1 |
| `WPN-6` must_not → `CCar` | `FAIL WPN-6: the absence is refuted: 'CCar' in Research/JC3Grab/ENTITIES.md` | 1 |
| `WPN-6` anchor → `no_such_class` | `FAIL WPN-6: anchor missing: 'no_such_class' in Research/JC3Grab/ENTITIES.md (census surface not read)` | 1 |

After restore: `PASS: 75 codes (67 carrier, 8 absence, 7 decision-gated) in 29 files | readers 25/25
green (recorded) | census ok | json match True, md match True`, and
`sha256sum` = `f1ae56ce…` (script), `37ae1a7c…` (JSON), `6d246b7b…` (md), `e7b9f55a…` (backlog), the
same as before the tampers.

## What this rework does not claim

* The 9 word-needles and 1 phrase-needle under 8 characters are still weak on their own; they are
  now **labelled** weak (issue 4's own suggested remedy), not strengthened. Turning them into
  numeric or identifier keys would change what each row proves, which is a card-level decision, not
  a rework.
* A `vocab-scan` still proves absence of *names in the decoded fleet*, not of engine capability;
  `G2X.md` §4 keeps that caveat.
* Each reader's own correctness is its own card's `--check`; G2X only proves they run green.
* `G2X.md`'s §1 reader table prints exit + verdict only; the full sentences are in `G2X.json`
  `readers[].summary` (recorded at the last `--write`).
