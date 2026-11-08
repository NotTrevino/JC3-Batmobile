# Independent review — G2X · G2 exit gate

Reviewer: Freebuff (did not write this card). Date: 2026-10-29.
Scope: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G2X gate text (§6, line 823), the §12 `G2X` row (1318),
`MODLOG.md` §"G2X · G2 exit gate — passed" (12032), and the outputs
(`Research/JC3Grab/G2X.md`, `G2X.json`, `Tools/scripts/g2x_gate.py`, the README rows, the 75 rows
over 28 `Research/JC3Grab/` files).
Read-only: nothing under `Research/`, `Tools/`, `Working/`, `GRAB_BACKLOG.md`, `MODLOG.md` or the
game install was written; no game was launched; nothing was committed. This report is the only file
written.

## VERDICT: **needs rework**

The card's own gate is **red on disk**: `python Tools/scripts/g2x_gate.py --check` exits **1** with
four stale diffs. Nothing is wrong with the *substance* — no feature row fails, all 25 readers are
green, the census is ok — but the two artefacts freeze live state (the §11 decision states and each
reader's verdict text) that later work changed: D-2, D-3 and D-5 were resolved on 2026-10-28 after
`G2X.json` was written, and `jc3audio.py`'s summary line was extended. The card says `done`; the
command says otherwise.

Separately, the gate's central promise — "**every feature code in §1**" — is checked against a
hand-typed 75-code list (`EXPECTED_CODES`, range literals at `g2x_gate.py:275`) and no code in the
tool parses §1 at all. It matches §1 exactly today (verified), but a new or renamed §1 code would not
be noticed, which is the one thing an exit gate exists to prevent. And two of the eight "proven
absences" are prose needles rather than negative scans, so they cannot fail on the claim they stand
for.

## Check output (verbatim)

`python Tools/scripts/g2x_gate.py --check` — started 05:10, wrote its log at 05:24:54, so ≈15 min
wall time (it re-runs 25 readers; `G2-29 traffic` alone scans 11,751 files / 7,719 MB):

```
FAIL G2X.json stale: rows differ for APP-6, APP-8, WPN-10, MOD-2, AUD-4, LGT-2, CAM-2
FAIL G2X.json stale: summary block differs
FAIL G2X.json stale: readers block differs
FAIL G2X.md stale: --- G2X.md on disk
 / +++ re-derived
 / @@ -17 +17 @@
 / -| decisions still open | **3** (D-2, D-3, D-5) | / +| decisions still open | **0** (none) | / @@ -44 +44 @@
 / -| G2-24 audio | `python Tools/scripts/jc3audio.py --check` | 0 | `PASS: 45 donor events in 3 banks, 257/257 vehicle events/tunes, 649 samples (22 looped, 1 rate), wave refs 0, LandAudio 2 members, weapons 4, horn 178 / radio 0, md match True` | / +| G2-24 audio | `python Tools/scripts/jc3audio.py --check` | 0 | `PASS: 45 donor events in 3 banks, 257/257 vehicle events/tunes, 45/45 donor tunes, 257/257 tunes with an event GUID, 0/0 wave GUIDs in tunes/instances, 649 samples (22 looped, 1 rate), wave refs 0, LandAudio 2 members, weapons 4, horn 178 / radio 0, md match True` |
FAIL: 75 codes (67 carrier, 8 absence, 7 decision-gated) in 28 files | readers 25/25 green | census ok | json match False, md match False
EXIT=1
```

The re-derived half of that last line is itself the good news: **67 carrier / 8 absence /
7 decision-gated over 28 files, readers 25/25 green, census ok**. The gate fails only on the
comparison with the two files on disk.

## Out paths

| path (from the card / §12 row) | exists | evidence |
|---|---|---|
| `Research/JC3Grab/G2X.md` | yes | 171 lines, 24,852 B |
| `Research/JC3Grab/G2X.json` | yes | 41,440 B |
| `Tools/scripts/g2x_gate.py` | yes | 610 lines, 38,551 B; `python -m py_compile` clean |
| `Research/JC3Grab/README.md` two command rows | yes | lines 47–48 |
| `GRAB_BACKLOG.md` §12 `G2X` row | yes | line 1318 |

## Done criterion vs what `--check` verifies — mostly, with one hole

The card's Done is three clauses. `--check` covers clause 1 (it re-runs the 25 readers as
subprocesses and requires exit 0 **and** a verdict line), clause 2 (the P0-2 census is the last
reader), and clause 3 row-by-row (`needle` present / `vocab-scan` anchor present and no must-not word)
plus a code-set check of its own `ROWS` against `EXPECTED_CODES`.

What it does **not** do is read §1. `EXPECTED_CODES` is typed:

```python
EXPECTED_CODES = (
    ["APP-%d" % i for i in range(1, 9)]
    + ["DIM-%d" % i for i in range(1, 5)]
    …
)
```

and `grep -n 'BACKLOG' Tools/scripts/g2x_gate.py` shows the backlog is read in exactly one place —
`decisions()` (line 306), for §11. So "every feature code in §1" means "every code in my own list",
and the two are equal only because a human kept them equal.

## Issues

### 1. The gate is red on disk (§12 says `done`) — needs `--write`
Files: `Research/JC3Grab/G2X.json`, `G2X.md`.
Two independent causes, both freezing live state:

* **§11 decisions resolved after the write.** `G2X.json` records `decision_state: "open"` for
  `APP-6`, `APP-8`, `WPN-10`, `MOD-2`, `AUD-4`, `LGT-2`, `CAM-2`; §11 says otherwise:

```
$ grep -n '^| D-\(2\|3\|5\) |' GRAB_BACKLOG.md
1258:| D-2 | … **resolved 2026-10-28 (user): (b) one hybrid car** … |
1259:| D-3 | … **resolved 2026-10-28 (user): accept JC3 lethality, no toggle** … |
1261:| D-5 | … **resolved 2026-10-28 (user): skins as extra Rebel Drop entries** … |

$ python -c "… G2X.json …"
APP-6    decision=D-2 recorded_state=open
APP-8    decision=D-5 recorded_state=open
WPN-10   decision=D-3 recorded_state=open
MOD-2    decision=D-2 recorded_state=open
AUD-4    decision=D-2 recorded_state=open
LGT-2    decision=D-2 recorded_state=open
CAM-2    decision=D-2 recorded_state=open
summary: {'decision_gated': 7, 'decision_open': ['D-2', 'D-3', 'D-5'], 'verdict': 'PASS'}
```

  The file was written 2026-10-28 05:13; D-2/D-3/D-5 were resolved the same day, later. The md's
  header still prints "decisions still open | **3** (D-2, D-3, D-5)".
* **A reader's verdict text changed.** `jc3audio.py` now prints extra fields
  (`45/45 donor tunes, 257/257 tunes with an event GUID, 0/0 wave GUIDs …`), so the recorded line in
  `G2X.json`/`G2X.md` no longer equals the live one, even though the reader still exits 0 with
  `PASS`.

  Fix: regenerate (`--write`), and say in the file/README that any §11 edit or any reader whose
  summary line changes must be followed by `--write`. A sturdier fix is to record the reader's
  *status* (exit code + the verdict word) rather than its whole stdout line — the gate's purpose is
  "the reader is green", not "the reader prints today's sentence". Right now a cosmetic wording
  change in any of 25 readers turns a `done` card red.

### 2. §1 is not read; `EXPECTED_CODES` is typed (R11)
File: `Tools/scripts/g2x_gate.py:275-289`.
The gate's headline claim is "75 codes — the whole of §1". It is true today and unverified tomorrow:

```
$ python -c "… compare §1 parse with g2x_gate.ROWS / EXPECTED_CODES …"
§1 codes parsed: 75 | ROWS: 75 | EXPECTED: 75
§1 not in ROWS: []
ROWS not in §1: []
EXPECTED != ROWS: []
```

Set-equal today, zero drift. But the equality is maintained by hand, and the tool that already parses
§1 (`t23_closeout.py --check`, which fails on a stale/missing code) shows the pattern this gate lacks.
If §1 gained a `HUD-3` tomorrow, `--check` would still print PASS. For an *exit* gate that is the
wrong failure direction.

### 3. The per-family breakdown in the header is typed
File: `g2x_gate.py:464-465` (`markdown()`):
```python
a.append("| feature codes | **%d** (the whole of §1: APP 8, DIM 4, ARM 6, WPN 12, HDL 6, MOD 5, "
         "AUD 7, ANI 9, WLD 8, LGT 2, FX 4, CAM 2, HUD 2) |" % s["codes"])
```
`s["codes"]` is derived; the parenthetical is a literal. Same class as issue 2, smaller: it is the
sentence a reader quotes from `G2X.md` line 15.

### 4. "Carrier with evidence" is, for 19 rows, a single short word or number
Files: `G2X.md` §2 (69 needle rows), `g2x_gate.py` ROWS.
`§2` discloses the mechanism ("`needle` = the named file must still contain the string"), so this is
not hidden. But the summary line "67 carriers with evidence" and §12's "67 carrier with evidence" read
as stronger than what the check does for the weakest rows:

```
needle rows: 69
needles shorter than 8 chars: 19
  ('APP-1','56136'), ('APP-3','Window'), ('APP-5','11643'), ('APP-6','179'), ('DIM-3','975'),
  ('ARM-1','shotgun'), ('ARM-2','2000'), ('WPN-4','w702'), ('HDL-4','40 km/h'), ('MOD-4','canopy'),
  ('MOD-5','ambient'), ('AUD-7','horn'), ('ANI-1','wheel'), ('ANI-2','Cannon'), ('ANI-8','canopy'),
  ('ANI-9','0.855'), ('WLD-4','stunt'), ('WLD-5','6000'), ('CAM-2','T-CAM10')
numeric-only needles: 7 — APP-1 56136, APP-5 11643, APP-6 179, DIM-3 975, ARM-2 2000, ANI-9 0.855, WLD-5 6000
```

Examples of rows that cannot fail on their mechanism: `ANI-1` (`wheel` in `PARTS_TABLE.md` — the word
survives any change to wheel slots), `MOD-5` (`ambient` in `TRAFFIC.md`), `AUD-7` (`horn` in
`JC3_AUDIO.md`). A number needle (`APP-6` `179`, `WLD-5` `6000`) does detect *data drift* (the number
moves → byte diff → red), which is the stated purpose; a word needle mostly does not. This makes the
carrier claim honest-but-weak rather than false; a per-row strength label (number / identifier /
word) would remove the ambiguity.

### 5. Two of the eight "proven absences" are prose needles, not negative scans
Files: `g2x_gate.py` ROWS, `WPN-6` at line 150 and `AUD-3` at line 200.
Six absences are `vocab-scan`: an anchor proves the complete census was read and the must-not words
are searched in it. Two are `needle`:

```
WPN-6  needle 'Functional winch classes anywhere in the fleet: **0**'   in TETHER.md
AUD-3  needle 'speedwind_sound_player'                                  in JC3_AUDIO.md
```

`WPN-6` passes whenever `TETHER.md` still prints that sentence (it would also fail on a formatting
change: the bold markers are part of the needle), and `AUD-3`'s needle is the *nearest member's name*
— a positive string — so it passes whether or not a cabin effect exists. The MODLOG's description
("the absences are checked as negatives … any of them appearing fails the row") is accurate for six
rows, not eight. `G2X.md` §3's "each names the surface that was searched" is likewise true for six.

### 6. `--check --no-readers` is indistinguishable from a full run in a log
File: `g2x_gate.py:569-571` + `run_readers(recorded)`.
`--no-readers` reloads the recorded reader block from `G2X.json` and prints the same summary line:

```
$ time python Tools/scripts/g2x_gate.py --check --no-readers
FAIL G2X.json stale: rows differ for APP-6, APP-8, WPN-10, MOD-2, AUD-4, LGT-2, CAM-2
…
FAIL: 75 codes (67 carrier, 8 absence, 7 decision-gated) in 28 files | readers 25/25 green | census ok | json match False, md match False
real 0m0.178s
```

`readers 25/25 green` there is a reading of the stored file, not a re-run — and it is the same phrase
a real run prints. The docstring offers this mode "for a tamper test", so a tamper log could quote
"readers 25/25 green" without any reader having been executed. One word in the summary
(`readers 25/25 green (recorded)`) would close it.

### 7. `APP-1`'s fact mislabels the number its needle checks
File: `G2X.md:70` — "all **56,136 body meshes** decode", needle `56136`.
`Research/JC3Grab/GEOMETRY.md:8-11`:

```
| entities | 233 |
| meshes | 56136 |
```

56,136 is the fleet mesh count over **233** entities, not "body meshes" (and not the Batmobile body).
The carrier claim (JC3 meshes decode, so appearance work has a carrier) is fine; the label is wrong
(R4: a number with the wrong provenance). Note also the 233 here versus P0-2's 232 decoded graphs —
the mesh reader covers one more entity than the census.

### 8. Stale docstring: "last output line"
File: `g2x_gate.py:12-13` — "their last output line is recorded … a line that does not start with
`PASS` … fails the gate". The code (line 378-384) takes the **first** verdict line, which the MODLOG
records as a deliberate fix (`damage_predict.py` prints three lines under its `PASS`). The docstring
still describes the bug that was fixed.

## Spot-checks

| value in the doc | where verified | result |
|---|---|---|
| "the 103-class fleet class inventory in `ENTITIES.md`" | counted the `## Class inventory` table rows in `Research/JC3Grab/ENTITIES.md` → 103 | **agree** |
| "the 1,421-member module vocabulary in `VOCABULARY.md`", "52 module types" | counted `## \`module\`` sections → 52 (52 unique) and member rows → 1,421 | **agree** |
| "**75** codes … the whole of §1" | parsed §1 with `t23_closeout.parse_codes` → 75 codes; set-equal to `g2x_gate.ROWS` and `EXPECTED_CODES` (0 either way) | **agree today**, but by hand (issue 2) |
| "in 28 files" | `len({f for row in ROWS for f in row['files']})` → 28; all 28 exist | **agree** |
| "readers run 25/25" | `len(g2x_gate.READERS) + 1` (census) → 25; the live run re-ran them and reported 25/25 green | **agree** |
| "67 carrier / 8 absence / 7 decision-gated" | `Counter(r['verdict'])` over ROWS → carrier 67, absence 8; 7 rows carry a decision | **agree** |
| "decisions still open **3** (D-2, D-3, D-5)" | §11 lines 1258/1259/1261 say `resolved 2026-10-28`; re-derived summary says `0 (none)` | **disagree — stale** (issue 1) |
| `APP-1` "56,136 body meshes" | `GEOMETRY.md:8-11` → entities 233, meshes 56136 | **label wrong** (issue 7) |

## What is solid

* All 25 readers are genuinely re-run by `--check` (the process tree during the run showed each
  `python Tools/scripts/<reader> --check` in turn), and a reader that exits non-zero or prints no
  verdict fails the gate — not a quote from MODLOG.
* The 75 rows match §1 today exactly, with per-row failure messages naming the file and the needle.
* The proven-absence design (anchor proves the census surface was read; must-not words refute the
  absence) is a real derivation for 6 of 8 rows, and §4 of `G2X.md` states the limit honestly: names
  in the decoded fleet, not engine capability.
* The three UNKNOWNs the files cannot answer (mass unit, explosion-threshold semantics, module vs
  `.epe` light list) are named rather than filled in.
* The two artefacts are compared block-by-block (JSON: `features`, `summary`, `readers`, `census`;
  MD: byte equality), which is exactly why this review can point at the drift.
* Structurally nothing in this card touches a build, a game file or a shared module; the card is a
  desk artefact and reads only generated files.

## Not verified here

The MODLOG's tamper table is taken as reported: this review is read-only and the tampers edit
`G2X.json`/`G2X.md`/`g2x_gate.py`. The drift in issue 1 exercises the same comparison mechanism those
tampers rely on (the md diff and the json block diff both fire). The readers' own correctness is
outside G2X — each is its own card with its own `--check`, which this gate shows is green.
