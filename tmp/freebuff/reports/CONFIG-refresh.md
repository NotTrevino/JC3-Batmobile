# DONE — CONFIG refresh (G3-03 ini set): re-run, classify the drift, check the downstream docs

STATUS: **done** — the check was run, the three files and all 41 changed rows are named and classified, the
BmInput.ini / Batmobile-binding question is answered, every claim in `CONTROLS.md` and `BINDINGS_MERGED.md`
that touches those rows was re-derived, and a regenerated artifact was written to a new file
(`CONFIG2.md` / `CONFIG2.json`) through a new script (`grab_config2.py`). `CONFIG.md` was not touched.
Two limitations are recorded as UNKNOWN at the end (the identity of one uncategorised removed row, and what
changed inside `BmInput.ini` outside its `Bindings=` lines).

Labels: **decoded** = read from a file (file:line or filesystem metadata) or from a file's bytes;
**derived** = computed here, with the rule stated; **UNKNOWN** = not established, with what blocked it.

## 1. The check fails, exactly as the review said — but against a newer install state

Verbatim, project root, unchanged script:

```
$ uv run --with numpy python Tools/scripts/grab_config.py --check
json MISMATCH
  differs: counts
  differs: files
  differs: profile_basedon
  differs: containment
  differs: categories
  differs: highlights
md MISMATCH (122612 on disk vs 122548 re-rendered)
row fidelity: 1894/1894 rows re-read from disk contain their key and value verbatim
CHECK FAILED
EXIT=1
```

`row fidelity: 1894/1894` is the important line: the generator is self-consistent with the current bytes,
so the published `CONFIG.json` / `CONFIG.md` are what is stale. (The re-rendered size differs by one byte
from the review's `122549`; the published file's character count is 122,612 and its byte count is 123,116 —
the offset is the multibyte UTF-8 characters, decoded.)

**The install moved again after the review.** Decoded from the filesystem:

| file | mtime (decoded) | bytes | lines | sha256 (published → now) |
|---|---|---|---|---|
| `BmGame/Config/BmEngine.ini` | **2026-11-03 20:05:13** | 115,968 → 115,968 | 1,565 → 1,565 | `3282dd4d…` → `2e433995…` |
| `BmGame/Config/BmSystemSettings.ini` | 2026-11-03 02:37:28 | 40,985 → 39,521 | 779 → 778 | `a16ac5bf…` → `becebd57…` |
| `BmGame/Config/BmInput.ini` | 2026-11-03 02:37:28 | 43,825 → 43,825 | 568 → 568 | `71eac81c…` → `b17711be…` |

The review recorded `BmEngine.ini` as 116,344 B / 1,573 lines at 02:37; it is back to the published
115,968 B / 1,565 lines with different content. So the review's +8 lines were undone at 20:05, and the
current row total is **20,960**, not the review's 20,966 and not the published 20,961. No Arkham process was
running when I read the files (`tasklist` grep: none), and I did not run or attach to the game. Nothing under
`Builds/` was touched. Only these three files carry a post-2024 mtime; the other 34 ini files are
2024-07-15 (decoded, `ls -lt`).

Consequence: the "41 changed rows" are the same 41 the review counted, but the numbers around them are
different from the review's snapshot, and the review's 20,966-row state cannot be re-measured (no bytes
preserved). Everything below is measured against the bytes as they stand now.

## 2. The three files, and where the change is

- `BmEngine.ini` — **bytes and line count unchanged, content changed** (sha256 moves). 92 of its 1,894
  published category rows and all 33 of its published highlight rows are still byte-identical in key, value
  and line. So its edit is outside every row the published artifact carries. What changed inside it: the
  containment oracle counts one more value-equal pair with its family (428 → 429, derived), which is the only
  measurable trace. The edit itself is UNKNOWN (see §7).
- `BmSystemSettings.ini` — **one line removed, 1,464 B smaller, 1,778 → 778 lines**. This is where all 41
  published-row changes are. The removal is in `[SystemSettings]`, after line 140 (`ApexTurbulence…`,
  unchanged) and before line 241 (`[SystemSettingsBucket1]`): every row from `MotionBlur` in Bucket1 onward
  is at line −1, every row at or before line 140 is at the same line (decoded).
- `BmInput.ini` — **same 43,825 B, same 568 lines, different sha256**. Its 165 published category rows
  (batmobile) and all 366 `Bindings=` lines are unchanged (§4).

## 3. The 41 changed rows (all in `BmSystemSettings.ini`)

Classification over the 1,894 published rows: **9 value changes, 32 line-shift-only changes, 0 new rows,
0 removed rows**. The 32 are not new and not removed — same section, key, operator and value, one line
earlier. Every one of the 41 is **decoded** from the current file line; the "published" value is **decoded**
from `CONFIG.json`.

### 3a. Value changes — 9 rows, all category `physics`, all `[SystemSettings]`

| # | key | line | published value | current value | nature (derived) |
|---|---|---|---|---|---|
| 1 | `ApexLODResourceBudget` | 120 | `100000.000000` | `100000.0` | float formatting |
| 2 | `ApexDestructionMaxChunkSeparationLOD` | 123 | `1.000000` | `1.0` | float formatting |
| 3 | `ApexGRBMeshCellSize` | 130 | `7.500000` | `7.5` | float formatting |
| 4 | `ApexGRBNonPenSolverPosIterCount` | 131 | `9` | `9;` | inline comment added (value now carries `;`) |
| 5 | `ApexGRBFrictionSolverPosIterCount` | 132 | `3` | `3;` | inline comment added |
| 6 | `ApexGRBFrictionSolverVelIterCount` | 133 | `3` | `3;` | inline comment added |
| 7 | `ApexGRBSkinWidth` | 134 | `0.025000` | `0.025` | float formatting |
| 8 | `ApexGRBMaxLinearAcceleration` | 135 | `1000000.000000` | `1000000.0` | float formatting |
| 9 | `ApexTurbulenceStopEmittingDistance` | 140 | `4650.000000` | `4650.0` | float formatting |

The three `9;` / `3;` / `3;` rows are still parsed as the same key with the value `9;`; the script's
`inline_comment` flag is set for them (derived from its `;`-outside-quotes rule, decoded against the line).

### 3b. Line-shift-only changes — 32 rows, category `postprocess`, value identical

| section | key | published line | current line |
|---|---|---|---|
| `SystemSettingsBucket1` | `MotionBlur` / `DepthOfField` / `Bloom` / `bAllowPostprocessMLAA` | 250 / 251 / 253 / 260 | 249 / 250 / 252 / 259 |
| `SystemSettingsBucket2` | same four | 312 / 313 / 315 / 322 | 311 / 312 / 314 / 321 |
| `SystemSettingsBucket3` | same four | 374 / 375 / 377 / 384 | 373 / 374 / 376 / 383 |
| `SystemSettingsBucket4` | same four | 436 / 437 / 439 / 446 | 435 / 436 / 438 / 445 |
| `SystemSettingsBucket5` | same four | 498 / 499 / 501 / 508 | 497 / 498 / 500 / 507 |
| `SystemSettingsMobile` | `MotionBlur` / `MotionBlurPause` / `DepthOfField` / `Bloom` | 611 / 612 / 613 / 615 | 610 / 611 / 612 / 614 |
| `SystemSettingsFlash` | same four | 667 / 668 / 669 / 671 | 666 / 667 / 668 / 670 |
| `SystemSettingsFlash_Detail` | same four | 683 / 684 / 685 / 687 | 682 / 683 / 684 / 686 |

### 3c. Changes the 41 do not cover, but the artifact records elsewhere

- **Two further value changes**, visible only in the `highlights` table because their keys are in no
  category (decoded): `CSMMinimumFOV` 82 `40.000000` → `40`; `CSMFOVRoundFactor` 83 `4.000000` → `4`.
- **One row removed that was in no category** (derived): `counts.rows` 20,961 → 20,960 and
  `rows_in_no_category` 19,185 → 19,184, while every category count is unchanged. Byte arithmetic
  (derived): the 11 known value edits account for −39 B; the file lost 1,464 B, leaving **≈1,425 B** for the
  removed line — so it was a single long `key=value` line inside `[SystemSettings]` between old lines 141 and
  240, present in the cooked file but not in its family (cooked-only 5 → 4, family pairs unchanged at 719).
  Its identity is **UNKNOWN** — `CONFIG.json` stores only the 1,894 categorised/highlight rows, not the full
  20,961.
- The published artifact cannot see the other ~19,000 uncategorised rows, so "no other value changed" is
  **UNKNOWN**, not proven.

## 4. Does any change touch `BmInput.ini` or a Batmobile binding? No evidence of one

- All 41 changed rows are in `BmSystemSettings.ini`; **none** is in `BmInput.ini` (decoded: changed-group
  files = `[]` both directions; every changed row's `file` is `BmGame/Config/BmSystemSettings.ini`).
- None of the 41 is a binding line: their keys are `Apex*`, `MotionBlur`, `MotionBlurPause`, `DepthOfField`,
  `Bloom`, `bAllowPostprocessMLAA` — rendering/physics settings, no `Bindings=`, no `Name=`, no exec token
  (decoded).
- `BmInput.ini` *did* change, but outside its bindings: 366 `Bindings=` lines (decoded count), the
  165 batmobile category rows and the 14 vehicle-keyword lines are all unchanged, and the independent
  `grab_bindings_merge.py --check` still reproduces `BmInput.ini` entry for entry (366/366, §5). So no
  Batmobile binding changed by that oracle. **What did change in `BmInput.ini` is UNKNOWN** — no pre-change
  bytes exist, and it is not in any `Bindings=` line, any published category row, or any highlight row.

## 5. `CONTROLS.md` and `BINDINGS_MERGED.md`: claims citing those rows

Both docs were re-derived against the current bytes with their own scripts. Both pass unchanged.

- **`CONTROLS.md`** mentions the three files on two lines only, both count claims, both still true (decoded
  now, re-derived with its own rule):
  - line 32 `BmGame/Config/BmInput.ini`: **14** — current file also yields **14** (unchanged).
  - line 33 `BmGame/Config/BmSystemSettings.ini`: **40** — current file also yields **40** (unchanged).
  - No line-number citation of any of the 41 rows appears in the file (grep for `BmSystemSettings.ini:` /
    `BmInput.ini:` finds only those two bullets). Its chain sources are `PCInput`/`UserInput`/
    `DefaultInput`/`BaseInput` — all unedited, sha256 unchanged.
  - `grab_controls.py --check` therefore prints `same CONTROLS.md`, `same CONTROLS.json`, `check ok` (exit 0).
  - **One claim is nevertheless incomplete** (derived): `BmEngine.ini` is absent from its "Other config
    files" table. That table is emitted only for files with a non-zero count, and `read_ini_lines()` decodes
    every file as latin-1, so a UTF-16LE+BOM file scores 0. With the correct decode (`decode_ini`, UTF-16LE)
    the current `BmEngine.ini` has **32** lines matching the same rule (decoded). The script's own
    `--check` cannot see this, which is why it still says `same`.
- **`BINDINGS_MERGED.md`** cites the 41 rows **nowhere**. Its citations are `DefaultInput.ini:251–272` and
  `DefaultInput.ini:71` (unedited, sha `7db2b893…`, decoded) and its oracle is `BmInput.ini` itself. Its
  central claim — the merge rule reproduces the oracle 366/366, in order — **still holds** (verified,
  below). No claim in it changes.

So: **zero claims in either doc cite one of the 41 rows by line or value**; the only ini-set statement that
changes is the `BmEngine.ini` omission in `CONTROLS.md`'s count table (32 lines, keyed on the correct decode).

## 6. `CONFIG2.md` — the claims that change against `CONFIG.md`

`Tools/scripts/grab_config2.py` is a copy of `grab_config.py` with only the output paths and the
generated-by line changed (`CONFIG2.md` / `CONFIG2.json`, schema and every rule untouched). It writes
`CONFIG2.md` (122,549 characters) and `CONFIG2.json`; `--write` then `--check` passed. The diff of
`CONFIG.md` vs `CONFIG2.md` is 230 diff lines; the claims that change:

1. **Preamble counts** — `Data rows: 20961` → **20960**; `rows in no category 19185` → **19184**. Category
   counts are unchanged (batmobile 768, vehicle 164, physics 143, postprocess 155, camera 664), `BasedOn`
   edges 18, profile `BasedOn` 51, malformed 17, comment lines 653 — all unchanged.
2. **Files (decoded) table, 3 of 37 rows**:
   - `BmEngine.ini`: sha256 `3282dd4d953e3b6a` → `2e4339959cb68ce2` (bytes/lines unchanged).
   - `BmInput.ini`: sha256 `71eac81cbaf5538e` → `b17711be7f9d2dfc` (bytes/lines unchanged).
   - `BmSystemSettings.ini`: 40,985 B / 779 lines / `a16ac5bf11d2300b` → **39,521 B / 778 lines /
     `becebd57e74d9ce7`**.
3. **Settings-profile `BasedOn` table** — 23 line numbers in `BmSystemSettings.ini`, each −1 (243→242,
   305→304, 367→366, 429→428, 491→490, 553→552, 594→593, 597→596, 603→602, 629→628, 633→632, 663→662,
   666→665, 682→681, 698→697, 701→700, 708→707, 713→712, 724→723, 730→729, 742→741, 753→752, 765→764).
4. **Containment oracle** — `BmEngine.ini` value-equal 428 → **429**; `BmSystemSettings.ini` cooked pairs
   700 → **699**, cooked-only 5 → **4**, value-equal 584 → **641** (family 719, shared 695, family-only 24
   unchanged). Verdicts are unchanged ("not exact: relationship UNKNOWN").
5. **Physics category group table** — the 9 values of §3a.
6. **Post-process category group table** — the 32 line numbers of §3b (values identical).
7. **Expanded key values (highlights)** — 24 rows change: the 2 CSM camera values (`40.000000` → `40`,
   `4.000000` → `4`) plus the 9 Apex values and 13 `Bloom`/`bAllowPostprocessMLAA` line shifts.
8. **Header only (not a data claim)** — "Generated by `Tools/scripts/grab_config2.py --write`".

What does **not** change: all 37 file entries other than the three above; the 18 `[Configuration]` edges
and their resolutions (incl. `BaseCompat.ini` MISSING); the 17 malformed lines; the `[Configuration]`-edge
count; the absence probes; the category rules and membership counts; every row in `BmEngine.ini` that the
artifact publishes (92 category rows, 33 highlight rows) — still identical in key, value and line.

## 7. UNKNOWNs

- **Identity of the removed uncategorised row in `BmSystemSettings.ini`.** Tried: `counts.rows` and
  `rows_in_no_category` deltas, category counts, containment cooked-only/pair counts, byte arithmetic
  (≈1,425 B line, `[SystemSettings]`, between old lines 141 and 240). Blocked by: the published artifact
  keeps only the 1,894 categorised/highlight rows out of 20,961, and no pre-change copy of the file exists.
  Would be found in a pre-02:37 copy of `BmSystemSettings.ini`.
- **What changed inside `BmInput.ini`.** Tried: 165 published category rows (unchanged), 14 vehicle-keyword
  lines (unchanged), 366 `Bindings=` lines (unchanged; merge oracle still 366/366), highlight rows (none for
  this file), byte size and line count (unchanged), containment counts (61/58/57/4/1/21, unchanged). Blocked
  by: no pre-change bytes. Would be found in a pre-02:37 copy; it is not in the `Bindings` array.
- **What changed inside `BmEngine.ini`.** Tried: 92 published category rows and 33 highlight rows
  (identical), file bytes/lines (identical), containment value-equal (+1 only). Blocked by: the remaining
  ~1,470 of its ~1,573 rows are not in the artifact. Would be found in a pre-20:05 copy.
- **Whether any other uncategorised row changed** in `BmSystemSettings.ini` (beyond the two CSM rows and the
  removed line). Same blocker; the byte arithmetic is only consistent with "one ~1,425 B line removed and no
  other edit", which is consistent but not proof.
- **Why the three files are being rewritten** (01:33 → 02:37 → 20:05). Hypothesis: engine write-back on
  exit (format normalisation toward the base file, rows added and removed), but no process was observed, no
  file records it, and I did not run the game. Not to be quoted as fact.
- **The review's 20,966-row state** cannot be reproduced: no bytes from it were preserved. The measured
  current state is 20,960 rows, and the per-row reconciliation to 20,966 is UNKNOWN.

## 8. Files written

| file | what |
|---|---|
| `Tools/scripts/grab_config2.py` | copy of `grab_config.py`; outputs `CONFIG2.md` / `CONFIG2.json`; `--write` / `--check`; no rule changed |
| `Research/BatmobileGrab/CONFIG2.md` | regenerated human-readable tables (122,549 chars) |
| `Research/BatmobileGrab/CONFIG2.json` | regenerated row-by-row data (877,957 B) |
| `tmp/freebuff/reports/CONFIG-refresh.md` | this report |
| `tmp/freebuff/scratch/g3c_refresh_diff.py`, `g3c_sections_diff.py`, `g3c_byte_arith.py` | read-only diff/arithmetic scripts |
| `tmp/freebuff/scratch/g3c_diff.log`, `g3c_sections.log`, `g3c_arith.log`, `CONFIG_vs_CONFIG2.diff` | their captured output |

`CONFIG.md`, `CONFIG.json`, `CONTROLS.md`, `CONTROLS.json`, `BINDINGS_MERGED.md` and `BINDINGS_MERGED.json`
were read, not written. No `Builds/` file, no game process, no git commit, no network.

## 9. Commands run and their output

### 9a. The card's check (first thing run)

```
$ uv run --with numpy python Tools/scripts/grab_config.py --check
json MISMATCH
  differs: counts
  differs: files
  differs: profile_basedon
  differs: containment
  differs: categories
  differs: highlights
md MISMATCH (122612 on disk vs 122548 re-rendered)
row fidelity: 1894/1894 rows re-read from disk contain their key and value verbatim
CHECK FAILED
EXIT=1
```

### 9b. mtimes, sizes, hashes, process, and the two downstream checks

```
$ for f in BmEngine.ini BmSystemSettings.ini BmInput.ini; do stat -c '%y  %s  %n' "$f"; sha256sum "$f"; done
2026-11-03 20:05:13.892785100 -0600  115968  .../BmGame/Config/BmEngine.ini
2e4339959cb68ce2c5e6591462df73ab135c66b8e6cd9a691f1ea73c8849c2e9 *...BmEngine.ini
2026-11-03 02:37:28.492692800 -0600  39521  .../BmGame/Config/BmSystemSettings.ini
becebd57e74d9ce756101bd1bd59fd4eb5e3421b11bfdaf57c9e32232e4a43ee *...BmSystemSettings.ini
2026-11-03 02:37:28.893899100 -0600  43825  .../BmGame/Config/BmInput.ini
b17711be7f9d2dfc4b0642f138863dd1a6a0bba1f2354e8c85bb71855070d40b *...BmInput.ini

$ ls -lt --time-style=full-iso <37 ini files> | head -6
-rw-r--r-- 1 User 197121 115968 2026-11-03 20:05:13 ... BmEngine.ini
-rw-r--r-- 1 User 197121  43825 2026-11-03 02:37:28 ... BmInput.ini
-rw-r--r-- 1 User 197121  39521 2026-11-03 02:37:28 ... BmSystemSettings.ini
-rw-r--r-- 1 User 197121  50919 2024-07-15 05:12:08 ... BaseEditor.ini
-rw-r--r-- 1 User 197121   5268 2024-07-15 05:12:08 ... BaseEditorKeyBindings.ini
-rw-r--r-- 1 User 197121  11439 2024-07-15 05:12:08 ... BaseEditorUserSettings.ini

$ tasklist | grep -i -E 'arkham|batman'
no arkham process

$ git status --porcelain Research/BatmobileGrab/CONFIG.md Research/BatmobileGrab/CONFIG.json
?? Research/BatmobileGrab/CONFIG.json
?? Research/BatmobileGrab/CONFIG.md
```

```
$ uv run --with pefile python Tools/scripts/grab_bindings_merge.py --check
OK: 8 candidates; 2 reproduce BmInput.ini exactly (dot=append/minus=exact, dot=replace_exact/minus=exact)
OK: chain BaseInput -> DefaultInput -> UserInput -> PCInput; oracle 366 bindings; '-' discriminating cases 1; '.' duplicates 0
OK: gamepad rows 22, with vehicle tokens 13
OK: BINDINGS_MERGED.md and BINDINGS_MERGED.json match the re-derived render
EXIT_BINDINGS=0
```

```
$ uv run --with numpy python Tools/scripts/grab_controls.py --check
same    E:\Modding\JustCause3\JC3-Batmobile\Research\BatmobileGrab\CONTROLS.md
same    E:\Modding\JustCause3\JC3-Batmobile\Research\BatmobileGrab\CONTROLS.json
check ok
EXIT=0
```

### 9c. `grab_config2.py --write` and `--check`

```
$ uv run --with numpy python Tools/scripts/grab_config2.py --write
wrote E:\Modding\JustCause3\JC3-Batmobile\Research\BatmobileGrab\CONFIG2.md (122549 bytes)
wrote E:\Modding\JustCause3\JC3-Batmobile\Research\BatmobileGrab\CONFIG2.json (877957 bytes)
files=37 rows=20960 basedon_file_chain=18 basedon_profile=51 malformed=17 categories={'batmobile': 768, 'vehicle': 164, 'physics': 143, 'postprocess': 155, 'camera': 664} uncategorised=19184
EXIT=0

$ uv run --with numpy python Tools/scripts/grab_config2.py --check
json ok: re-derived data == CONFIG2.json (20960 rows, 37 files)
md ok: re-rendered text == CONFIG2.md (122549 bytes)
row fidelity: 1894/1894 rows re-read from disk contain their key and value verbatim
CHECK OK
EXIT=0
```

### 9d. The 41-row diff (scratch, read-only) — full log

Command: `uv run --with numpy python tmp/freebuff/scratch/g3c_refresh_diff.py`
(full output appended below, §9g).

### 9e. Remaining JSON sections + CONTROLS/BINDINGS re-derivation (scratch, read-only)

Command: `uv run --with numpy python tmp/freebuff/scratch/g3c_sections_diff.py`
(decisive lines quoted in §5; full output appended below, §9h).

### 9f. Byte arithmetic for the removed row (scratch, read-only)

Command: `uv run --with numpy python tmp/freebuff/scratch/g3c_byte_arith.py`
(full output appended below, §9i).

### 9g. Full output — `g3c_refresh_diff.py`

```
published category rows: 1894   re-derived: 1894
published counts.rows=20961 now=20960

== file table: published vs now ==
  BmGame/Config/BmEngine.ini                    sha256: 3282dd4d953e3b6a4d1ba7d7078097d025a595eb6e97f8e3e52708b23c6e227a -> 2e4339959cb68ce2c5e6591462df73ab135c66b8e6cd9a691f1ea73c8849c2e9
  BmGame/Config/BmInput.ini                     sha256: 71eac81cbaf5538ea01b077a9811a2c9226ed35154a97c00837ae0487a5ccc48 -> b17711be7f9d2dfc4b0642f138863dd1a6a0bba1f2354e8c85bb71855070d40b
  BmGame/Config/BmSystemSettings.ini            bytes: 40985 -> 39521
  BmGame/Config/BmSystemSettings.ini            lines: 779 -> 778
  BmGame/Config/BmSystemSettings.ini            sha256: a16ac5bf11d2300baca4751423da51411cdf449a02b0f2a6ab904305f3b1078e -> becebd57e74d9ce756101bd1bd59fd4eb5e3421b11bfdaf57c9e32232e4a43ee

== (file,section,key,op) groups: published 502, now 502, removed 0, added 0 ==

== removed groups (present in published table, absent in current bytes) ==

== added groups (in current bytes, not in published table) ==

== same-key groups with different lines/values ==
  BmGame/Config/BmSystemSettings.ini [SystemSettings] ApexLODResourceBudget: published [(120, '100000.000000', 'physics')] -> now [(120, '100000.0', 'physics')]
  BmGame/Config/BmSystemSettings.ini [SystemSettings] ApexDestructionMaxChunkSeparationLOD: published [(123, '1.000000', 'physics')] -> now [(123, '1.0', 'physics')]
  BmGame/Config/BmSystemSettings.ini [SystemSettings] ApexGRBMeshCellSize: published [(130, '7.500000', 'physics')] -> now [(130, '7.5', 'physics')]
  BmGame/Config/BmSystemSettings.ini [SystemSettings] ApexGRBNonPenSolverPosIterCount: published [(131, '9', 'physics')] -> now [(131, '9;', 'physics')]
  BmGame/Config/BmSystemSettings.ini [SystemSettings] ApexGRBFrictionSolverPosIterCount: published [(132, '3', 'physics')] -> now [(132, '3;', 'physics')]
  BmGame/Config/BmSystemSettings.ini [SystemSettings] ApexGRBFrictionSolverVelIterCount: published [(133, '3', 'physics')] -> now [(133, '3;', 'physics')]
  BmGame/Config/BmSystemSettings.ini [SystemSettings] ApexGRBSkinWidth: published [(134, '0.025000', 'physics')] -> now [(134, '0.025', 'physics')]
  BmGame/Config/BmSystemSettings.ini [SystemSettings] ApexGRBMaxLinearAcceleration: published [(135, '1000000.000000', 'physics')] -> now [(135, '1000000.0', 'physics')]
  BmGame/Config/BmSystemSettings.ini [SystemSettings] ApexTurbulenceStopEmittingDistance: published [(140, '4650.000000', 'physics')] -> now [(140, '4650.0', 'physics')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsBucket1] MotionBlur: published [(250, 'False', 'postprocess')] -> now [(249, 'False', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsBucket1] DepthOfField: published [(251, 'False', 'postprocess')] -> now [(250, 'False', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsBucket1] Bloom: published [(253, 'False', 'postprocess')] -> now [(252, 'False', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsBucket1] bAllowPostprocessMLAA: published [(260, 'False', 'postprocess')] -> now [(259, 'False', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsBucket2] MotionBlur: published [(312, 'False', 'postprocess')] -> now [(311, 'False', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsBucket2] DepthOfField: published [(313, 'True', 'postprocess')] -> now [(312, 'True', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsBucket2] Bloom: published [(315, 'False', 'postprocess')] -> now [(314, 'False', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsBucket2] bAllowPostprocessMLAA: published [(322, 'False', 'postprocess')] -> now [(321, 'False', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsBucket3] MotionBlur: published [(374, 'False', 'postprocess')] -> now [(373, 'False', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsBucket3] DepthOfField: published [(375, 'True', 'postprocess')] -> now [(374, 'True', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsBucket3] Bloom: published [(377, 'True', 'postprocess')] -> now [(376, 'True', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsBucket3] bAllowPostprocessMLAA: published [(384, 'True', 'postprocess')] -> now [(383, 'True', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsBucket4] MotionBlur: published [(436, 'True', 'postprocess')] -> now [(435, 'True', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsBucket4] DepthOfField: published [(437, 'True', 'postprocess')] -> now [(436, 'True', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsBucket4] Bloom: published [(439, 'True', 'postprocess')] -> now [(438, 'True', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsBucket4] bAllowPostprocessMLAA: published [(446, 'True', 'postprocess')] -> now [(445, 'True', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsBucket5] MotionBlur: published [(498, 'True', 'postprocess')] -> now [(497, 'True', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsBucket5] DepthOfField: published [(499, 'True', 'postprocess')] -> now [(498, 'True', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsBucket5] Bloom: published [(501, 'True', 'postprocess')] -> now [(500, 'True', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsBucket5] bAllowPostprocessMLAA: published [(508, 'True', 'postprocess')] -> now [(507, 'True', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsMobile] MotionBlur: published [(611, 'FALSE', 'postprocess')] -> now [(610, 'FALSE', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsMobile] MotionBlurPause: published [(612, 'FALSE', 'postprocess')] -> now [(611, 'FALSE', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsMobile] DepthOfField: published [(613, 'FALSE', 'postprocess')] -> now [(612, 'FALSE', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsMobile] Bloom: published [(615, 'FALSE', 'postprocess')] -> now [(614, 'FALSE', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsFlash] MotionBlur: published [(667, 'FALSE', 'postprocess')] -> now [(666, 'FALSE', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsFlash] MotionBlurPause: published [(668, 'FALSE', 'postprocess')] -> now [(667, 'FALSE', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsFlash] DepthOfField: published [(669, 'FALSE', 'postprocess')] -> now [(668, 'FALSE', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsFlash] Bloom: published [(671, 'FALSE', 'postprocess')] -> now [(670, 'FALSE', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsFlash_Detail] MotionBlur: published [(683, 'FALSE', 'postprocess')] -> now [(682, 'FALSE', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsFlash_Detail] MotionBlurPause: published [(684, 'FALSE', 'postprocess')] -> now [(683, 'FALSE', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsFlash_Detail] DepthOfField: published [(685, 'FALSE', 'postprocess')] -> now [(684, 'FALSE', 'postprocess')]
  BmGame/Config/BmSystemSettings.ini [SystemSettingsFlash_Detail] Bloom: published [(687, 'FALSE', 'postprocess')] -> now [(686, 'FALSE', 'postprocess')]

== per-file row-level diff (published table vs current bytes) ==

-- BmGame/Config/BmSystemSettings.ini: published 64 rows, now 64 rows --
  op=replace published[10:11] -> now[10:11]
    - line 120 [SystemSettings] ApexLODResourceBudget = '100000.000000'
    + line 120 [SystemSettings] ApexLODResourceBudget = '100000.0'
  op=replace published[13:14] -> now[13:14]
    - line 123 [SystemSettings] ApexDestructionMaxChunkSeparationLOD = '1.000000'
    + line 123 [SystemSettings] ApexDestructionMaxChunkSeparationLOD = '1.0'
  op=replace published[20:26] -> now[20:26]
    - line 130 [SystemSettings] ApexGRBMeshCellSize = '7.500000'
    - line 131 [SystemSettings] ApexGRBNonPenSolverPosIterCount = '9'
    - line 132 [SystemSettings] ApexGRBFrictionSolverPosIterCount = '3'
    - line 133 [SystemSettings] ApexGRBFrictionSolverVelIterCount = '3'
    - line 134 [SystemSettings] ApexGRBSkinWidth = '0.025000'
    - line 135 [SystemSettings] ApexGRBMaxLinearAcceleration = '1000000.000000'
    + line 130 [SystemSettings] ApexGRBMeshCellSize = '7.5'
    + line 131 [SystemSettings] ApexGRBNonPenSolverPosIterCount = '9;'
    + line 132 [SystemSettings] ApexGRBFrictionSolverPosIterCount = '3;'
    + line 133 [SystemSettings] ApexGRBFrictionSolverVelIterCount = '3;'
    + line 134 [SystemSettings] ApexGRBSkinWidth = '0.025'
    + line 135 [SystemSettings] ApexGRBMaxLinearAcceleration = '1000000.0'
  op=replace published[29:30] -> now[29:30]
    - line 140 [SystemSettings] ApexTurbulenceStopEmittingDistance = '4650.000000'
    + line 140 [SystemSettings] ApexTurbulenceStopEmittingDistance = '4650.0'
  op=replace published[32:64] -> now[32:64]
    - line 250 [SystemSettingsBucket1] MotionBlur = 'False'
    - line 251 [SystemSettingsBucket1] DepthOfField = 'False'
    - line 253 [SystemSettingsBucket1] Bloom = 'False'
    - line 260 [SystemSettingsBucket1] bAllowPostprocessMLAA = 'False'
    - line 312 [SystemSettingsBucket2] MotionBlur = 'False'
    - line 313 [SystemSettingsBucket2] DepthOfField = 'True'
    - line 315 [SystemSettingsBucket2] Bloom = 'False'
    - line 322 [SystemSettingsBucket2] bAllowPostprocessMLAA = 'False'
    - line 374 [SystemSettingsBucket3] MotionBlur = 'False'
    - line 375 [SystemSettingsBucket3] DepthOfField = 'True'
    - line 377 [SystemSettingsBucket3] Bloom = 'True'
    - line 384 [SystemSettingsBucket3] bAllowPostprocessMLAA = 'True'
    - line 436 [SystemSettingsBucket4] MotionBlur = 'True'
    - line 437 [SystemSettingsBucket4] DepthOfField = 'True'
    - line 439 [SystemSettingsBucket4] Bloom = 'True'
    - line 446 [SystemSettingsBucket4] bAllowPostprocessMLAA = 'True'
    - line 498 [SystemSettingsBucket5] MotionBlur = 'True'
    - line 499 [SystemSettingsBucket5] DepthOfField = 'True'
    - line 501 [SystemSettingsBucket5] Bloom = 'True'
    - line 508 [SystemSettingsBucket5] bAllowPostprocessMLAA = 'True'
    - line 611 [SystemSettingsMobile] MotionBlur = 'FALSE'
    - line 612 [SystemSettingsMobile] MotionBlurPause = 'FALSE'
    - line 613 [SystemSettingsMobile] DepthOfField = 'FALSE'
    - line 615 [SystemSettingsMobile] Bloom = 'FALSE'
    - line 667 [SystemSettingsFlash] MotionBlur = 'FALSE'
    - line 668 [SystemSettingsFlash] MotionBlurPause = 'FALSE'
    - line 669 [SystemSettingsFlash] DepthOfField = 'FALSE'
    - line 671 [SystemSettingsFlash] Bloom = 'FALSE'
    - line 683 [SystemSettingsFlash_Detail] MotionBlur = 'FALSE'
    - line 684 [SystemSettingsFlash_Detail] MotionBlurPause = 'FALSE'
    - line 685 [SystemSettingsFlash_Detail] DepthOfField = 'FALSE'
    - line 687 [SystemSettingsFlash_Detail] Bloom = 'FALSE'
    + line 249 [SystemSettingsBucket1] MotionBlur = 'False'
    + line 250 [SystemSettingsBucket1] DepthOfField = 'False'
    + line 252 [SystemSettingsBucket1] Bloom = 'False'
    + line 259 [SystemSettingsBucket1] bAllowPostprocessMLAA = 'False'
    + line 311 [SystemSettingsBucket2] MotionBlur = 'False'
    + line 312 [SystemSettingsBucket2] DepthOfField = 'True'
    + line 314 [SystemSettingsBucket2] Bloom = 'False'
    + line 321 [SystemSettingsBucket2] bAllowPostprocessMLAA = 'False'
    + line 373 [SystemSettingsBucket3] MotionBlur = 'False'
    + line 374 [SystemSettingsBucket3] DepthOfField = 'True'
    + line 376 [SystemSettingsBucket3] Bloom = 'True'
    + line 383 [SystemSettingsBucket3] bAllowPostprocessMLAA = 'True'
    + line 435 [SystemSettingsBucket4] MotionBlur = 'True'
    + line 436 [SystemSettingsBucket4] DepthOfField = 'True'
    + line 438 [SystemSettingsBucket4] Bloom = 'True'
    + line 445 [SystemSettingsBucket4] bAllowPostprocessMLAA = 'True'
    + line 497 [SystemSettingsBucket5] MotionBlur = 'True'
    + line 498 [SystemSettingsBucket5] DepthOfField = 'True'
    + line 500 [SystemSettingsBucket5] Bloom = 'True'
    + line 507 [SystemSettingsBucket5] bAllowPostprocessMLAA = 'True'
    + line 610 [SystemSettingsMobile] MotionBlur = 'FALSE'
    + line 611 [SystemSettingsMobile] MotionBlurPause = 'FALSE'
    + line 612 [SystemSettingsMobile] DepthOfField = 'FALSE'
    + line 614 [SystemSettingsMobile] Bloom = 'FALSE'
    + line 666 [SystemSettingsFlash] MotionBlur = 'FALSE'
    + line 667 [SystemSettingsFlash] MotionBlurPause = 'FALSE'
    + line 668 [SystemSettingsFlash] DepthOfField = 'FALSE'
    + line 670 [SystemSettingsFlash] Bloom = 'FALSE'
    + line 682 [SystemSettingsFlash_Detail] MotionBlur = 'FALSE'
    + line 683 [SystemSettingsFlash_Detail] MotionBlurPause = 'FALSE'
    + line 684 [SystemSettingsFlash_Detail] DepthOfField = 'FALSE'
    + line 686 [SystemSettingsFlash_Detail] Bloom = 'FALSE'

== classification tally (changed rows) ==
  value change: 9
  removed/replaced row: 32

== changed-group files ==
  removed: []
  added:   []
```

### 9h. Full output — `g3c_sections_diff.py`

```
== counts ==
  files: published 37 -> now 37
  rows: published 20961 -> now 20960   <-- CHANGED
  basedon_file_chain: published 18 -> now 18
  basedon_profile: published 51 -> now 51
  malformed: published 17 -> now 17
  comment_lines: published 653 -> now 653
  by_category: published {'batmobile': 768, 'vehicle': 164, 'physics': 143, 'postprocess': 155, 'camera': 664} -> now {'batmobile': 768, 'vehicle': 164, 'physics': 143, 'postprocess': 155, 'camera': 664}
  rows_in_no_category: published 19185 -> now 19184   <-- CHANGED

== highlights: published vs now ==
  published 192 rows, now 192 rows
  only in published: 24   only now: 24
    - BmGame/Config/BmSystemSettings.ini:82 [SystemSettings] CSMMinimumFOV = '40.000000'
    - BmGame/Config/BmSystemSettings.ini:83 [SystemSettings] CSMFOVRoundFactor = '4.000000'
    - BmGame/Config/BmSystemSettings.ini:120 [SystemSettings] ApexLODResourceBudget = '100000.000000'
    - BmGame/Config/BmSystemSettings.ini:123 [SystemSettings] ApexDestructionMaxChunkSeparationLOD = '1.000000'
    - BmGame/Config/BmSystemSettings.ini:130 [SystemSettings] ApexGRBMeshCellSize = '7.500000'
    - BmGame/Config/BmSystemSettings.ini:131 [SystemSettings] ApexGRBNonPenSolverPosIterCount = '9'
    - BmGame/Config/BmSystemSettings.ini:132 [SystemSettings] ApexGRBFrictionSolverPosIterCount = '3'
    - BmGame/Config/BmSystemSettings.ini:133 [SystemSettings] ApexGRBFrictionSolverVelIterCount = '3'
    - BmGame/Config/BmSystemSettings.ini:134 [SystemSettings] ApexGRBSkinWidth = '0.025000'
    - BmGame/Config/BmSystemSettings.ini:135 [SystemSettings] ApexGRBMaxLinearAcceleration = '1000000.000000'
    - BmGame/Config/BmSystemSettings.ini:140 [SystemSettings] ApexTurbulenceStopEmittingDistance = '4650.000000'
    - BmGame/Config/BmSystemSettings.ini:253 [SystemSettingsBucket1] Bloom = 'False'
    - BmGame/Config/BmSystemSettings.ini:260 [SystemSettingsBucket1] bAllowPostprocessMLAA = 'False'
    - BmGame/Config/BmSystemSettings.ini:315 [SystemSettingsBucket2] Bloom = 'False'
    - BmGame/Config/BmSystemSettings.ini:322 [SystemSettingsBucket2] bAllowPostprocessMLAA = 'False'
    - BmGame/Config/BmSystemSettings.ini:377 [SystemSettingsBucket3] Bloom = 'True'
    - BmGame/Config/BmSystemSettings.ini:384 [SystemSettingsBucket3] bAllowPostprocessMLAA = 'True'
    - BmGame/Config/BmSystemSettings.ini:439 [SystemSettingsBucket4] Bloom = 'True'
    - BmGame/Config/BmSystemSettings.ini:446 [SystemSettingsBucket4] bAllowPostprocessMLAA = 'True'
    - BmGame/Config/BmSystemSettings.ini:501 [SystemSettingsBucket5] Bloom = 'True'
    - BmGame/Config/BmSystemSettings.ini:508 [SystemSettingsBucket5] bAllowPostprocessMLAA = 'True'
    - BmGame/Config/BmSystemSettings.ini:615 [SystemSettingsMobile] Bloom = 'FALSE'
    - BmGame/Config/BmSystemSettings.ini:671 [SystemSettingsFlash] Bloom = 'FALSE'
    - BmGame/Config/BmSystemSettings.ini:687 [SystemSettingsFlash_Detail] Bloom = 'FALSE'
    + BmGame/Config/BmSystemSettings.ini:82 [SystemSettings] CSMMinimumFOV = '40'
    + BmGame/Config/BmSystemSettings.ini:83 [SystemSettings] CSMFOVRoundFactor = '4'
    + BmGame/Config/BmSystemSettings.ini:120 [SystemSettings] ApexLODResourceBudget = '100000.0'
    + BmGame/Config/BmSystemSettings.ini:123 [SystemSettings] ApexDestructionMaxChunkSeparationLOD = '1.0'
    + BmGame/Config/BmSystemSettings.ini:130 [SystemSettings] ApexGRBMeshCellSize = '7.5'
    + BmGame/Config/BmSystemSettings.ini:131 [SystemSettings] ApexGRBNonPenSolverPosIterCount = '9;'
    + BmGame/Config/BmSystemSettings.ini:132 [SystemSettings] ApexGRBFrictionSolverPosIterCount = '3;'
    + BmGame/Config/BmSystemSettings.ini:133 [SystemSettings] ApexGRBFrictionSolverVelIterCount = '3;'
    + BmGame/Config/BmSystemSettings.ini:134 [SystemSettings] ApexGRBSkinWidth = '0.025'
    + BmGame/Config/BmSystemSettings.ini:135 [SystemSettings] ApexGRBMaxLinearAcceleration = '1000000.0'
    + BmGame/Config/BmSystemSettings.ini:140 [SystemSettings] ApexTurbulenceStopEmittingDistance = '4650.0'
    + BmGame/Config/BmSystemSettings.ini:252 [SystemSettingsBucket1] Bloom = 'False'
    + BmGame/Config/BmSystemSettings.ini:259 [SystemSettingsBucket1] bAllowPostprocessMLAA = 'False'
    + BmGame/Config/BmSystemSettings.ini:314 [SystemSettingsBucket2] Bloom = 'False'
    + BmGame/Config/BmSystemSettings.ini:321 [SystemSettingsBucket2] bAllowPostprocessMLAA = 'False'
    + BmGame/Config/BmSystemSettings.ini:376 [SystemSettingsBucket3] Bloom = 'True'
    + BmGame/Config/BmSystemSettings.ini:383 [SystemSettingsBucket3] bAllowPostprocessMLAA = 'True'
    + BmGame/Config/BmSystemSettings.ini:438 [SystemSettingsBucket4] Bloom = 'True'
    + BmGame/Config/BmSystemSettings.ini:445 [SystemSettingsBucket4] bAllowPostprocessMLAA = 'True'
    + BmGame/Config/BmSystemSettings.ini:500 [SystemSettingsBucket5] Bloom = 'True'
    + BmGame/Config/BmSystemSettings.ini:507 [SystemSettingsBucket5] bAllowPostprocessMLAA = 'True'
    + BmGame/Config/BmSystemSettings.ini:614 [SystemSettingsMobile] Bloom = 'FALSE'
    + BmGame/Config/BmSystemSettings.ini:670 [SystemSettingsFlash] Bloom = 'FALSE'
    + BmGame/Config/BmSystemSettings.ini:686 [SystemSettingsFlash_Detail] Bloom = 'FALSE'
  highlights per file (published / now):
    BmGame/Config/BmCamera.ini: 1 / 1
    BmGame/Config/BmEngine.ini: 33 / 33
    BmGame/Config/BmGame.ini: 6 / 6
    BmGame/Config/BmSystemSettings.ini: 43 / 43
    BmGame/Config/DefaultCamera.ini: 1 / 1
    BmGame/Config/DefaultEngine.ini: 22 / 22
    BmGame/Config/DefaultGame.ini: 2 / 2
    BmGame/Config/DefaultSystemSettings.ini: 15 / 15
    BmGame/Config/Launcher.ini: 1 / 1
    Engine/Config/BaseEditor.ini: 4 / 4
    Engine/Config/BaseEditorUserSettings.ini: 1 / 1
    Engine/Config/BaseEngine.ini: 25 / 25
    Engine/Config/BaseGame.ini: 6 / 6
    Engine/Config/BaseSystemSettings.ini: 32 / 32

== profile_basedon ==
  published 51, now 51
  - {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 243, 'section': 'SystemSettingsBucket1', 'text': 'SystemSettings', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  + {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 242, 'section': 'SystemSettingsBucket1', 'text': 'SystemSettings', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  - {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 305, 'section': 'SystemSettingsBucket2', 'text': 'SystemSettings', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  + {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 304, 'section': 'SystemSettingsBucket2', 'text': 'SystemSettings', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  - {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 367, 'section': 'SystemSettingsBucket3', 'text': 'SystemSettings', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  + {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 366, 'section': 'SystemSettingsBucket3', 'text': 'SystemSettings', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  - {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 429, 'section': 'SystemSettingsBucket4', 'text': 'SystemSettings', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  + {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 428, 'section': 'SystemSettingsBucket4', 'text': 'SystemSettings', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  - {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 491, 'section': 'SystemSettingsBucket5', 'text': 'SystemSettings', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  + {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 490, 'section': 'SystemSettingsBucket5', 'text': 'SystemSettings', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  - {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 553, 'section': 'SystemSettingsScreenshot', 'text': 'SystemSettings', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  + {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 552, 'section': 'SystemSettingsScreenshot', 'text': 'SystemSettings', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  - {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 594, 'section': 'SystemSettingsEditor', 'text': 'SystemSettings', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  + {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 593, 'section': 'SystemSettingsEditor', 'text': 'SystemSettings', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  - {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 597, 'section': 'SystemSettingsSplitScreen2', 'text': 'SystemSettings', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  + {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 596, 'section': 'SystemSettingsSplitScreen2', 'text': 'SystemSettings', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  - {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 603, 'section': 'SystemSettingsMobile', 'text': 'SystemSettings', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  + {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 602, 'section': 'SystemSettingsMobile', 'text': 'SystemSettings', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  - {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 629, 'section': 'SystemSettingsMobilePreviewer', 'text': 'SystemSettingsMobile', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  + {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 628, 'section': 'SystemSettingsMobilePreviewer', 'text': 'SystemSettingsMobile', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  - {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 633, 'section': 'SystemSettingsMobileTextureBias', 'text': 'SystemSettingsMobile', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  + {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 632, 'section': 'SystemSettingsMobileTextureBias', 'text': 'SystemSettingsMobile', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  - {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 663, 'section': 'SystemSettingsAndroid', 'text': 'SystemSettingsMobileTextureBias', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  + {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 662, 'section': 'SystemSettingsAndroid', 'text': 'SystemSettingsMobileTextureBias', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  - {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 666, 'section': 'SystemSettingsFlash', 'text': 'SystemSettingsMobileTextureBias', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  + {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 665, 'section': 'SystemSettingsFlash', 'text': 'SystemSettingsMobileTextureBias', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  - {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 682, 'section': 'SystemSettingsFlash_Detail', 'text': 'SystemSettingsMobileTextureBias', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  + {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 681, 'section': 'SystemSettingsFlash_Detail', 'text': 'SystemSettingsMobileTextureBias', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  - {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 698, 'section': 'SystemSettingsIPhone', 'text': 'SystemSettingsMobileTextureBias', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  + {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 697, 'section': 'SystemSettingsIPhone', 'text': 'SystemSettingsMobileTextureBias', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  - {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 701, 'section': 'SystemSettingsIPhone3GS', 'text': 'SystemSettingsMobileTextureBias', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  + {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 700, 'section': 'SystemSettingsIPhone3GS', 'text': 'SystemSettingsMobileTextureBias', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  - {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 708, 'section': 'SystemSettingsIPhone4', 'text': 'SystemSettingsMobile', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  + {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 707, 'section': 'SystemSettingsIPhone4', 'text': 'SystemSettingsMobile', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  - {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 713, 'section': 'SystemSettingsIPhone4S', 'text': 'SystemSettingsMobile', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  + {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 712, 'section': 'SystemSettingsIPhone4S', 'text': 'SystemSettingsMobile', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  - {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 724, 'section': 'SystemSettingsIPodTouch4', 'text': 'SystemSettingsMobileTextureBias', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  + {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 723, 'section': 'SystemSettingsIPodTouch4', 'text': 'SystemSettingsMobileTextureBias', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  - {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 730, 'section': 'SystemSettingsIPad', 'text': 'SystemSettingsMobileTextureBias', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  + {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 729, 'section': 'SystemSettingsIPad', 'text': 'SystemSettingsMobileTextureBias', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  - {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 742, 'section': 'SystemSettingsIPad2', 'text': 'SystemSettingsMobile', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  + {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 741, 'section': 'SystemSettingsIPad2', 'text': 'SystemSettingsMobile', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  - {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 753, 'section': 'SystemSettingsIPad3', 'text': 'SystemSettingsMobile', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  + {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 752, 'section': 'SystemSettingsIPad3', 'text': 'SystemSettingsMobile', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  - {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 765, 'section': 'SystemSettingsIPad2_Detail', 'text': 'SystemSettingsIPad2', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}
  + {'f': 'BmGame/Config/BmSystemSettings.ini', 'line': 764, 'section': 'SystemSettingsIPad2_Detail', 'text': 'SystemSettingsIPad2', 'kind': 'profile_inheritance', 'file': 'BmGame/Config/BmSystemSettings.ini'}

== containment ==
  BmGame/Config/BmCamera.ini: cooked 2->2, family 1->1, shared 1->1, cooked-only 1->1, family-only 0->0, value-equal 1->1
  BmGame/Config/BmEngine.ini: cooked 601->601, family 596->596, shared 594->594, cooked-only 7->7, family-only 2->2, value-equal 428->429   <-- CHANGED
  BmGame/Config/BmGame.ini: cooked 737->737, family 723->723, shared 722->722, cooked-only 15->15, family-only 1->1, value-equal 698->698
  BmGame/Config/BmInput.ini: cooked 61->61, family 58->58, shared 57->57, cooked-only 4->4, family-only 1->1, value-equal 21->21
  BmGame/Config/BmSystemSettings.ini: cooked 700->699, family 719->719, shared 695->695, cooked-only 5->4, family-only 24->24, value-equal 584->641   <-- CHANGED
  BmGame/Config/BmUI.ini: cooked 27->27, family 24->24, shared 24->24, cooked-only 3->3, family-only 0->0, value-equal 24->24

== published rows per file (categories / highlights) ==
  BmGame/Config/BmEngine.ini: 92 category rows, 33 highlight rows
  BmGame/Config/BmSystemSettings.ini: 64 category rows, 43 highlight rows
  BmGame/Config/BmInput.ini: 165 category rows, 0 highlight rows

== CONTROLS.md claims: lines naming a vehicle keyword (grab_controls build_other rule) ==
  rule = KV_RE.match(line) and re.search(r'(?i)vehicle|batmobile|driv|boost|sonar|brake|eject', line)
  BmGame/Config/BmCamera.ini: 0
  BmGame/Config/BmEngine.ini: 32   <-- CONTROLS.md says 0
  BmGame/Config/BmGame.ini: 453
  BmGame/Config/BmInput.ini: 14
  BmGame/Config/BmSystemSettings.ini: 40
  BmGame/Config/BmUI.ini: 0
  BmGame/Config/Credits.ini: 0
  BmGame/Config/DefaultCamera.ini: 0
  BmGame/Config/DefaultCompat.ini: 0
  BmGame/Config/DefaultEngine.ini: 25
  BmGame/Config/DefaultGame.ini: 154
  BmGame/Config/DefaultInput.ini: 14
  BmGame/Config/DefaultSystemSettings.ini: 30
  BmGame/Config/DefaultUI.ini: 0
  BmGame/Config/Launcher.ini: 1
  BmGame/Config/MapItemsBackscreen.ini: 212
  BmGame/Config/PC/PCEngine.ini: 2   <-- CONTROLS.md says None
  BmGame/Config/PC/PCGame.ini: 87   <-- CONTROLS.md says None
  BmGame/Config/UserEngine.ini: 0
  BmGame/Config/UserGame.ini: 0
  BmGame/Config/UserInput.ini: 0
  BmGame/Config/UserSystemSettings.ini: 0
  Engine/Config/BaseEditor.ini: 22   <-- CONTROLS.md says None
  Engine/Config/BaseEngine.ini: 6   <-- CONTROLS.md says None
  Engine/Config/BaseSystemSettings.ini: 15   <-- CONTROLS.md says None

== BmInput.ini Bindings count (BINDINGS_MERGED oracle says 366) ==
  encoding latin-1; Bindings lines now: 366
  sha256 now: b17711be7f9d2dfc4b0642f138863dd1a6a0bba1f2354e8c85bb71855070d40b
  published CONFIG.json sha: 71eac81cbaf5538ea01b077a9811a2c9226ed35154a97c00837ae0487a5ccc48

== row totals per file: published artifact has no full row list; current build only ==
  current rows 1894 in categories; counts.rows 20960

== malformed ==
  published 17, now 17; identical sets: True
```

### 9i. Full output — `g3c_byte_arith.py`

```
published: bytes 40985 lines 779 blank 28 comments 0
now      : bytes 39521 lines 778 blank 28 
published rows known for this file: 67
current rows: 700, malformed 0

== known value-length deltas (published -> current, matched by key) ==
  CSMMinimumFOV @82->82: '40.000000' -> '40'  len 9->2 (-7)
  CSMFOVRoundFactor @83->83: '4.000000' -> '4'  len 8->1 (-7)
  ApexLODResourceBudget @120->120: '100000.000000' -> '100000.0'  len 13->8 (-5)
  ApexDestructionMaxChunkSeparationLOD @123->123: '1.000000' -> '1.0'  len 8->3 (-5)
  ApexGRBMeshCellSize @130->130: '7.500000' -> '7.5'  len 8->3 (-5)
  ApexGRBNonPenSolverPosIterCount @131->131: '9' -> '9;'  len 1->2 (+1)
  ApexGRBFrictionSolverPosIterCount @132->132: '3' -> '3;'  len 1->2 (+1)
  ApexGRBFrictionSolverVelIterCount @133->133: '3' -> '3;'  len 1->2 (+1)
  ApexGRBSkinWidth @134->134: '0.025000' -> '0.025'  len 8->5 (-3)
  ApexGRBMaxLinearAcceleration @135->135: '1000000.000000' -> '1000000.0'  len 14->9 (-5)
  ApexTurbulenceStopEmittingDistance @140->140: '4650.000000' -> '4650.0'  len 11->6 (-5)
  sum of known value-length deltas: -39 bytes
  total file delta: -1464 bytes
  unexplained remainder: -1425 bytes (= size of removed line(s) if nothing else changed)

== probes examples mentioning this file (published) ==

== current lines 140..252 (line: text) ==
  140: 'ApexTurbulenceStopEmittingDistance=4650.0'
  141: 'FlexInvisibleFramesBeforeSleep=0'
  142: 'FlexDistanceBeforeSleep=0.0'
  143: 'NVOpacityShadows=True'
  144: 'NVProjectedOpacityShadows=True'
  145: 'NVOpacityShadowTransitionSize=0.1'
  146: 'NVPSM=True'
  147: 'NVPSMSize=1024'
  148: 'NVPSMDepth=128'
  149: 'NVPSMMultisampleCount=1'
  150: 'NVParticleDownsampling=True'
  151: 'NVParticleDownsamplingDepthScale=1.0'
  152: 'NVHalfResParticlesMaxResX=2560'
  153: 'NVHalfResParticlesMaxResY=1600'
  154: 'bEnableInteractiveSmoke=0'
  155: 'bEnableInteractivePaperDebris=0'
  156: 'bEnableRainFX=0'
  157: 'bEnableVolumetricLighting=0'
  158: 'TEXTUREGROUP_World=(MinLODSize=128,MaxLODSize=1024,LODBias=0,MinMagFilter=Linear,MipFilter=Linear,MipGenSettings=TMGS_Sharpen6)'
  159: 'TEXTUREGROUP_WorldNormalMap=(MinLODSize=128,MaxLODSize=1024,LODBias=0,MinMagFilter=Linear,MipFilter=Linear)'
  160: 'TEXTUREGROUP_WorldSpecular=(MinLODSize=128,MaxLODSize=1024,LODBias=0,MinMagFilter=Linear,MipFilter=Linear)'
  161: 'TEXTUREGROUP_Character=(MinLODSize=128,MaxLODSize=1024,LODBias=0,MinMagFilter=Linear,MipFilter=Linear)'
  162: 'TEXTUREGROUP_CharacterNormalMap=(MinLODSize=128,MaxLODSize=1024,LODBias=0,MinMagFilter=Linear,MipFilter=Linear)'
  163: 'TEXTUREGROUP_CharacterSpecular=(MinLODSize=128,MaxLODSize=1024,LODBias=0,MinMagFilter=Linear,MipFilter=Linear)'
  164: 'TEXTUREGROUP_Weapon=(MinLODSize=128,MaxLODSize=1024,LODBias=0,MinMagFilter=Linear,MipFilter=Linear,MipGenSettings=TMGS_Sharpen6)'
  165: 'TEXTUREGROUP_WeaponNormalMap=(MinLODSize=128,MaxLODSize=512,LODBias=0,MinMagFilter=Linear,MipFilter=Linear)'
  166: 'TEXTUREGROUP_WeaponSpecular=(MinLODSize=128,MaxLODSize=512,LODBias=0,MinMagFilter=Linear,MipFilter=Linear)'
  167: 'TEXTUREGROUP_Vehicle=(MinLODSize=128,MaxLODSize=1024,LODBias=0,MinMagFilter=Linear,MipFilter=Linear,MipGenSettings=TMGS_Sharpen6)'
  168: 'TEXTUREGROUP_Vehicle_Low=(MinLODSize=128,MaxLODSize=512,LODBias=0,MinMagFilter=Linear,MipFilter=Linear,MipGenSettings=TMGS_Sharpen6)'
  169: 'TEXTUREGROUP_Vehicle_High=(MinLODSize=128,MaxLODSize=2048,LODBias=0,MinMagFilter=Linear,MipFilter=Linear,MipGenSettings=TMGS_Sharpen6)'
  170: 'TEXTUREGROUP_VehicleNormalMap=(MinLODSize=128,MaxLODSize=2048,LODBias=0,MinMagFilter=Linear,MipFilter=Linear)'
  171: 'TEXTUREGROUP_VehicleSpecular=(MinLODSize=128,MaxLODSize=2048,LODBias=0,MinMagFilter=Linear,MipFilter=Linear)'
  172: 'TEXTUREGROUP_Cinematic=(MinLODSize=128,MaxLODSize=2048,LODBias=0,MinMagFilter=Linear,MipFilter=Linear)'
  173: 'TEXTUREGROUP_Effects=(MinLODSize=128,MaxLODSize=1024,LODBias=0,MinMagFilter=Linear,MipFilter=Linear)'
  174: 'TEXTUREGROUP_EffectsNotFiltered=(MinLODSize=128,MaxLODSize=4096,LODBias=0,MinMagFilter=Linear,MipFilter=Linear)'
  175: 'TEXTUREGROUP_Skybox=(MinLODSize=128,MaxLODSize=1024,LODBias=0,MinMagFilter=Linear,MipFilter=Linear)'
  176: 'TEXTUREGROUP_UI=(MinLODSize=512,MaxLODSize=4096,LODBias=0,MinMagFilter=Linear,MipFilter=Linear)'
  177: 'TEXTUREGROUP_Lightmap=(MinLODSize=128,MaxLODSize=4096,LODBias=0,MinMagFilter=Linear,MipFilter=Linear)'
  178: 'TEXTUREGROUP_Shadowmap=(MinLODSize=128,MaxLODSize=4096,LODBias=0,MinMagFilter=Linear,MipFilter=Linear)'
  179: 'TEXTUREGROUP_RenderTarget=(MinLODSize=1,MaxLODSize=2048,LODBias=0,MinMagFilter=Linear,MipFilter=Linear)'
  180: 'TEXTUREGROUP_MobileFlattened=(MinLODSize=1,MaxLODSize=4096,LODBias=0,MinMagFilter=aniso,MipFilter=point)'
  181: 'TEXTUREGROUP_ProcBuilding_Face=(MinLODSize=256,MaxLODSize=4096,LODBias=0,MinMagFilter=aniso,MipFilter=Linear,MipGenSettings=TMGS_Sharpen5)'
  182: 'TEXTUREGROUP_ProcBuilding_LightMap=(MinLODSize=1,MaxLODSize=4096,LODBias=-1,MinMagFilter=Linear,MipFilter=Linear)'
  183: 'TEXTUREGROUP_Terrain_Heightmap=(MinLODSize=1,MaxLODSize=4096,LODBias=0,MinMagFilter=aniso,MipFilter=point)'
  184: 'TEXTUREGROUP_Terrain_Weightmap=(MinLODSize=1,MaxLODSize=4096,LODBias=0,MinMagFilter=aniso,MipFilter=point)'
  185: 'TEXTUREGROUP_ImageBasedReflection=(MinLODSize=128,MaxLODSize=128,LODBias=1,MinMagFilter=Linear,MipFilter=Linear)'
  186: 'TEXTUREGROUP_Bokeh=(MinLODSize=128,MaxLODSize=512,LODBias=0,MinMagFilter=linear,MipFilter=linear)'
  187: 'TEXTUREGROUP_LOD1_RRM_Mask=(MinLODSize=128,MaxLODSize=4096,LODBias=0,MinMagFilter=linear,MipFilter=Linear)'
  188: 'TEXTUREGROUP_LOD1_Opacity_Mask=(MinLODSize=128,MaxLODSize=4096,LODBias=0,MinMagFilter=aniso,MipFilter=Linear)'
  189: 'TEXTUREGROUP_LOD1_Emissive=(MinLODSize=128,MaxLODSize=4096,LODBias=0,MinMagFilter=linear,MipFilter=Linear)'
  190: 'Reflections=True'
  191: 'DisableLightEnvironments=False'
  192: 'DisableForceDynamicLighting=False'
  193: 'AmbientShadowColor=(R=0.0,G=0.0,B=0.0)'
  194: 'MinShadowAngle=0.0'
  195: 'ChromaticAberration=True'
  196: 'FilmGrain=True'
  197: 'AllowedTextureRequests=100'
  198: 'LimitTextureIncreasesInFlight=200'
  199: 'TexStreamingCopySharedMipsPerFrame=50'
  200: 'AllowD3D10=False'
  201: 'DisableSphericalHarmonicLights=False'
  202: 'TextureFiltering=0'
  203: 'UseAdaptiveVsync=0'
  204: 'TEXTUREGROUP_CharacterLow=(MinLODSize=128,MaxLODSize=512,LODBias=0,MinMagFilter=Linear,MipFilter=Linear)'
  205: 'TEXTUREGROUP_CharacterHigh=(MinLODSize=128,MaxLODSize=2048,LODBias=0,MinMagFilter=Linear,MipFilter=Linear)'
  206: 'TEXTUREGROUP_CharacterSpecPower=(MinLODSize=128,MaxLODSize=1024,LODBias=0,MinMagFilter=Linear,MipFilter=Linear)'
  207: 'TEXTUREGROUP_World_Low=(MinLODSize=128,MaxLODSize=512,LODBias=0,MinMagFilter=Linear,MipFilter=Linear,MipGenSettings=TMGS_Sharpen6)'
  208: 'TEXTUREGROUP_World_Hi=(MinLODSize=128,MaxLODSize=2048,LODBias=0,MinMagFilter=aniso,MipFilter=Linear,MipGenSettings=TMGS_Sharpen6)'
  209: 'TEXTUREGROUP_WorldNormalMap_Hi=(MinLODSize=128,MaxLODSize=2048,LODBias=0,MinMagFilter=Linear,MipFilter=Linear)'
  210: 'TEXTUREGROUP_WorldSpecular_Hi=(MinLODSize=128,MaxLODSize=2048,LODBias=0,MinMagFilter=Linear,MipFilter=Linear)'
  211: 'TEXTUREGROUP_Interior_High=(MinLODSize=128,MaxLODSize=2048,LODBias=0,MinMagFilter=aniso,MipFilter=Linear,MipGenSettings=TMGS_Sharpen6)'
  212: 'TEXTUREGROUP_InteriorNormalMap_High=(MinLODSize=128,MaxLODSize=2048,LODBias=0,MinMagFilter=aniso,MipFilter=Linear)'
  213: 'TEXTUREGROUP_InteriorSpec_High=(MinLODSize=128,MaxLODSize=2048,LODBias=0,MinMagFilter=aniso,MipFilter=Linear)'
  214: 'TEXTUREGROUP_LightAndShadowMap=(MinLODSize=128,MaxLODSize=4096,LODBias=0,MinMagFilter=Linear,MipFilter=Linear)'
  215: 'bApexClothingAsyncFetchResults=True'
  216: 'WindowDisplayMode=0'
  217: 'Antialiasing=1'
  218: 'TextureResolution=1'
  219: 'ShadowQuality=1'
  220: 'LevelOfDetail=1'
  221: 'DefaultFullscreen=True'
  222: 'DefaultWindowDisplayMode=2'
  223: 'DefaultUseVsync=False'
  224: 'DefaultUseAdaptiveVsync=False'
  225: 'DefaultResX=1280'
  226: 'DefaultResY=720'
  227: 'DefaultAntiAliasing=1'
  228: 'DefaultTextureResolution=0'
  229: 'DefaultShadowQuality=0'
  230: 'DefaultLevelOfDetail=0'
  231: 'DefaultMaxFPS=30'
  232: 'bDefaultEnableInteractiveSmoke=0'
  233: 'bDefaultEnableInteractivePaperDebris=0'
  234: 'bDefaultEnableRainFX=0'
  235: 'bDefaultEnableVolumetricLighting=0'
  236: 'DefaultMotionBlur=True'
  237: 'DefaultChromaticAberration=True'
  238: 'DefaultFilmGrain=True'
  239: 'DefaultTextureFiltering=0'
  240: ''
  241: '[SystemSettingsBucket1]'
  242: 'BasedOn=SystemSettings'
  243: 'StaticDecals=False'
  244: 'DynamicDecals=False'
  245: 'UnbatchedDecals=True'
  246: 'DecalCullDistanceScale=0.4'
  247: 'DynamicShadows=False'
  248: 'LightEnvironmentShadows=False'
  249: 'MotionBlur=False'
  250: 'DepthOfField=False'
  251: 'AmbientOcclusion=False'
  252: 'Bloom=False'

== longest current lines in 141..249 ==
  138 bytes @ 181: 'TEXTUREGROUP_ProcBuilding_Face=(MinLODSize=256,MaxLODSize=4096,LODBias=0,MinMagF'
  134 bytes @ 211: 'TEXTUREGROUP_Interior_High=(MinLODSize=128,MaxLODSize=2048,LODBias=0,MinMagFilte'
  134 bytes @ 169: 'TEXTUREGROUP_Vehicle_High=(MinLODSize=128,MaxLODSize=2048,LODBias=0,MinMagFilter'
  132 bytes @ 168: 'TEXTUREGROUP_Vehicle_Low=(MinLODSize=128,MaxLODSize=512,LODBias=0,MinMagFilter=L'
  130 bytes @ 207: 'TEXTUREGROUP_World_Low=(MinLODSize=128,MaxLODSize=512,LODBias=0,MinMagFilter=Lin'
  129 bytes @ 208: 'TEXTUREGROUP_World_Hi=(MinLODSize=128,MaxLODSize=2048,LODBias=0,MinMagFilter=ani'
```

### 9j. Full output — `diff <(tr -d '\r' < CONFIG.md) CONFIG2.md` (230 lines)

```
3c3
< Generated by `Tools/scripts/grab_config.py --write`. Do not edit by hand; `--check` re-derives and compares.
---
> Generated by `Tools/scripts/grab_config2.py --write`. Do not edit by hand; `--check` re-derives and compares.
7c7
< Files parsed: **37** (`BmGame/Config`, `BmGame/Config/PC`, `Engine/Config`). Data rows: **20961**. `[Configuration] BasedOn` edges: **18**. Settings-profile BasedOn lines (not followed): **51**. Malformed key lines: **17**.
---
> Files parsed: **37** (`BmGame/Config`, `BmGame/Config/PC`, `Engine/Config`). Data rows: **20960**. `[Configuration] BasedOn` edges: **18**. Settings-profile BasedOn lines (not followed): **51**. Malformed key lines: **17**.
9c9
< Rows per category (derived, one row can be in several): batmobile 768, vehicle 164, physics 143, postprocess 155, camera 664; rows in no category 19185.
---
> Rows per category (derived, one row can be in several): batmobile 768, vehicle 164, physics 143, postprocess 155, camera 664; rows in no category 19184.
16c16
< | `BmGame/Config/BmEngine.ini` | 115968 | 1565 | utf-16-le+bom | `3282dd4d953e3b6a` | C02 | — |
---
> | `BmGame/Config/BmEngine.ini` | 115968 | 1565 | utf-16-le+bom | `2e4339959cb68ce2` | C02 | — |
18,19c18,19
< | `BmGame/Config/BmInput.ini` | 43825 | 568 | latin-1 | `71eac81cbaf5538e` | C04 | — |
< | `BmGame/Config/BmSystemSettings.ini` | 40985 | 779 | latin-1 | `a16ac5bf11d2300b` | C05 | — |
---
> | `BmGame/Config/BmInput.ini` | 43825 | 568 | latin-1 | `b17711be7f9d2dfc` | C04 | — |
> | `BmGame/Config/BmSystemSettings.ini` | 39521 | 778 | latin-1 | `becebd57e74d9ce7` | C05 | — |
200,222c200,222
< | `BmGame/Config/BmSystemSettings.ini` | 243 | `SystemSettingsBucket1` | `SystemSettings` |
< | `BmGame/Config/BmSystemSettings.ini` | 305 | `SystemSettingsBucket2` | `SystemSettings` |
< | `BmGame/Config/BmSystemSettings.ini` | 367 | `SystemSettingsBucket3` | `SystemSettings` |
< | `BmGame/Config/BmSystemSettings.ini` | 429 | `SystemSettingsBucket4` | `SystemSettings` |
< | `BmGame/Config/BmSystemSettings.ini` | 491 | `SystemSettingsBucket5` | `SystemSettings` |
< | `BmGame/Config/BmSystemSettings.ini` | 553 | `SystemSettingsScreenshot` | `SystemSettings` |
< | `BmGame/Config/BmSystemSettings.ini` | 594 | `SystemSettingsEditor` | `SystemSettings` |
< | `BmGame/Config/BmSystemSettings.ini` | 597 | `SystemSettingsSplitScreen2` | `SystemSettings` |
< | `BmGame/Config/BmSystemSettings.ini` | 603 | `SystemSettingsMobile` | `SystemSettings` |
< | `BmGame/Config/BmSystemSettings.ini` | 629 | `SystemSettingsMobilePreviewer` | `SystemSettingsMobile` |
< | `BmGame/Config/BmSystemSettings.ini` | 633 | `SystemSettingsMobileTextureBias` | `SystemSettingsMobile` |
< | `BmGame/Config/BmSystemSettings.ini` | 663 | `SystemSettingsAndroid` | `SystemSettingsMobileTextureBias` |
< | `BmGame/Config/BmSystemSettings.ini` | 666 | `SystemSettingsFlash` | `SystemSettingsMobileTextureBias` |
< | `BmGame/Config/BmSystemSettings.ini` | 682 | `SystemSettingsFlash_Detail` | `SystemSettingsMobileTextureBias` |
< | `BmGame/Config/BmSystemSettings.ini` | 698 | `SystemSettingsIPhone` | `SystemSettingsMobileTextureBias` |
< | `BmGame/Config/BmSystemSettings.ini` | 701 | `SystemSettingsIPhone3GS` | `SystemSettingsMobileTextureBias` |
< | `BmGame/Config/BmSystemSettings.ini` | 708 | `SystemSettingsIPhone4` | `SystemSettingsMobile` |
< | `BmGame/Config/BmSystemSettings.ini` | 713 | `SystemSettingsIPhone4S` | `SystemSettingsMobile` |
< | `BmGame/Config/BmSystemSettings.ini` | 724 | `SystemSettingsIPodTouch4` | `SystemSettingsMobileTextureBias` |
< | `BmGame/Config/BmSystemSettings.ini` | 730 | `SystemSettingsIPad` | `SystemSettingsMobileTextureBias` |
< | `BmGame/Config/BmSystemSettings.ini` | 742 | `SystemSettingsIPad2` | `SystemSettingsMobile` |
< | `BmGame/Config/BmSystemSettings.ini` | 753 | `SystemSettingsIPad3` | `SystemSettingsMobile` |
< | `BmGame/Config/BmSystemSettings.ini` | 765 | `SystemSettingsIPad2_Detail` | `SystemSettingsIPad2` |
---
> | `BmGame/Config/BmSystemSettings.ini` | 242 | `SystemSettingsBucket1` | `SystemSettings` |
> | `BmGame/Config/BmSystemSettings.ini` | 304 | `SystemSettingsBucket2` | `SystemSettings` |
> | `BmGame/Config/BmSystemSettings.ini` | 366 | `SystemSettingsBucket3` | `SystemSettings` |
> | `BmGame/Config/BmSystemSettings.ini` | 428 | `SystemSettingsBucket4` | `SystemSettings` |
> | `BmGame/Config/BmSystemSettings.ini` | 490 | `SystemSettingsBucket5` | `SystemSettings` |
> | `BmGame/Config/BmSystemSettings.ini` | 552 | `SystemSettingsScreenshot` | `SystemSettings` |
> | `BmGame/Config/BmSystemSettings.ini` | 593 | `SystemSettingsEditor` | `SystemSettings` |
> | `BmGame/Config/BmSystemSettings.ini` | 596 | `SystemSettingsSplitScreen2` | `SystemSettings` |
> | `BmGame/Config/BmSystemSettings.ini` | 602 | `SystemSettingsMobile` | `SystemSettings` |
> | `BmGame/Config/BmSystemSettings.ini` | 628 | `SystemSettingsMobilePreviewer` | `SystemSettingsMobile` |
> | `BmGame/Config/BmSystemSettings.ini` | 632 | `SystemSettingsMobileTextureBias` | `SystemSettingsMobile` |
> | `BmGame/Config/BmSystemSettings.ini` | 662 | `SystemSettingsAndroid` | `SystemSettingsMobileTextureBias` |
> | `BmGame/Config/BmSystemSettings.ini` | 665 | `SystemSettingsFlash` | `SystemSettingsMobileTextureBias` |
> | `BmGame/Config/BmSystemSettings.ini` | 681 | `SystemSettingsFlash_Detail` | `SystemSettingsMobileTextureBias` |
> | `BmGame/Config/BmSystemSettings.ini` | 697 | `SystemSettingsIPhone` | `SystemSettingsMobileTextureBias` |
> | `BmGame/Config/BmSystemSettings.ini` | 700 | `SystemSettingsIPhone3GS` | `SystemSettingsMobileTextureBias` |
> | `BmGame/Config/BmSystemSettings.ini` | 707 | `SystemSettingsIPhone4` | `SystemSettingsMobile` |
> | `BmGame/Config/BmSystemSettings.ini` | 712 | `SystemSettingsIPhone4S` | `SystemSettingsMobile` |
> | `BmGame/Config/BmSystemSettings.ini` | 723 | `SystemSettingsIPodTouch4` | `SystemSettingsMobileTextureBias` |
> | `BmGame/Config/BmSystemSettings.ini` | 729 | `SystemSettingsIPad` | `SystemSettingsMobileTextureBias` |
> | `BmGame/Config/BmSystemSettings.ini` | 741 | `SystemSettingsIPad2` | `SystemSettingsMobile` |
> | `BmGame/Config/BmSystemSettings.ini` | 752 | `SystemSettingsIPad3` | `SystemSettingsMobile` |
> | `BmGame/Config/BmSystemSettings.ini` | 764 | `SystemSettingsIPad2_Detail` | `SystemSettingsIPad2` |
259c259
< | `BmGame/Config/BmEngine.ini` | 5 | 601 | 596 | 594 | 7 | 2 | 428 | not exact: relationship UNKNOWN |
---
> | `BmGame/Config/BmEngine.ini` | 5 | 601 | 596 | 594 | 7 | 2 | 429 | not exact: relationship UNKNOWN |
262c262
< | `BmGame/Config/BmSystemSettings.ini` | 5 | 700 | 719 | 695 | 5 | 24 | 584 | not exact: relationship UNKNOWN |
---
> | `BmGame/Config/BmSystemSettings.ini` | 5 | 699 | 719 | 695 | 4 | 24 | 641 | not exact: relationship UNKNOWN |
517c517
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettings` | `ApexLODResourceBudget` | 1 | 120 | 100000.000000 |
---
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettings` | `ApexLODResourceBudget` | 1 | 120 | 100000.0 |
520c520
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettings` | `ApexDestructionMaxChunkSeparationLOD` | 1 | 123 | 1.000000 |
---
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettings` | `ApexDestructionMaxChunkSeparationLOD` | 1 | 123 | 1.0 |
527,532c527,532
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettings` | `ApexGRBMeshCellSize` | 1 | 130 | 7.500000 |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettings` | `ApexGRBNonPenSolverPosIterCount` | 1 | 131 | 9 |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettings` | `ApexGRBFrictionSolverPosIterCount` | 1 | 132 | 3 |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettings` | `ApexGRBFrictionSolverVelIterCount` | 1 | 133 | 3 |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettings` | `ApexGRBSkinWidth` | 1 | 134 | 0.025000 |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettings` | `ApexGRBMaxLinearAcceleration` | 1 | 135 | 1000000.000000 |
---
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettings` | `ApexGRBMeshCellSize` | 1 | 130 | 7.5 |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettings` | `ApexGRBNonPenSolverPosIterCount` | 1 | 131 | 9; |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettings` | `ApexGRBFrictionSolverPosIterCount` | 1 | 132 | 3; |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettings` | `ApexGRBFrictionSolverVelIterCount` | 1 | 133 | 3; |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettings` | `ApexGRBSkinWidth` | 1 | 134 | 0.025 |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettings` | `ApexGRBMaxLinearAcceleration` | 1 | 135 | 1000000.0 |
536c536
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettings` | `ApexTurbulenceStopEmittingDistance` | 1 | 140 | 4650.000000 |
---
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettings` | `ApexTurbulenceStopEmittingDistance` | 1 | 140 | 4650.0 |
652,683c652,683
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket1` | `MotionBlur` | 1 | 250 | False |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket1` | `DepthOfField` | 1 | 251 | False |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket1` | `Bloom` | 1 | 253 | False |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket1` | `bAllowPostprocessMLAA` | 1 | 260 | False |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket2` | `MotionBlur` | 1 | 312 | False |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket2` | `DepthOfField` | 1 | 313 | True |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket2` | `Bloom` | 1 | 315 | False |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket2` | `bAllowPostprocessMLAA` | 1 | 322 | False |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket3` | `MotionBlur` | 1 | 374 | False |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket3` | `DepthOfField` | 1 | 375 | True |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket3` | `Bloom` | 1 | 377 | True |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket3` | `bAllowPostprocessMLAA` | 1 | 384 | True |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket4` | `MotionBlur` | 1 | 436 | True |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket4` | `DepthOfField` | 1 | 437 | True |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket4` | `Bloom` | 1 | 439 | True |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket4` | `bAllowPostprocessMLAA` | 1 | 446 | True |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket5` | `MotionBlur` | 1 | 498 | True |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket5` | `DepthOfField` | 1 | 499 | True |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket5` | `Bloom` | 1 | 501 | True |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket5` | `bAllowPostprocessMLAA` | 1 | 508 | True |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsMobile` | `MotionBlur` | 1 | 611 | FALSE |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsMobile` | `MotionBlurPause` | 1 | 612 | FALSE |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsMobile` | `DepthOfField` | 1 | 613 | FALSE |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsMobile` | `Bloom` | 1 | 615 | FALSE |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsFlash` | `MotionBlur` | 1 | 667 | FALSE |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsFlash` | `MotionBlurPause` | 1 | 668 | FALSE |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsFlash` | `DepthOfField` | 1 | 669 | FALSE |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsFlash` | `Bloom` | 1 | 671 | FALSE |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsFlash_Detail` | `MotionBlur` | 1 | 683 | FALSE |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsFlash_Detail` | `MotionBlurPause` | 1 | 684 | FALSE |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsFlash_Detail` | `DepthOfField` | 1 | 685 | FALSE |
< | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsFlash_Detail` | `Bloom` | 1 | 687 | FALSE |
---
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket1` | `MotionBlur` | 1 | 249 | False |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket1` | `DepthOfField` | 1 | 250 | False |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket1` | `Bloom` | 1 | 252 | False |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket1` | `bAllowPostprocessMLAA` | 1 | 259 | False |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket2` | `MotionBlur` | 1 | 311 | False |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket2` | `DepthOfField` | 1 | 312 | True |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket2` | `Bloom` | 1 | 314 | False |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket2` | `bAllowPostprocessMLAA` | 1 | 321 | False |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket3` | `MotionBlur` | 1 | 373 | False |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket3` | `DepthOfField` | 1 | 374 | True |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket3` | `Bloom` | 1 | 376 | True |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket3` | `bAllowPostprocessMLAA` | 1 | 383 | True |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket4` | `MotionBlur` | 1 | 435 | True |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket4` | `DepthOfField` | 1 | 436 | True |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket4` | `Bloom` | 1 | 438 | True |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket4` | `bAllowPostprocessMLAA` | 1 | 445 | True |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket5` | `MotionBlur` | 1 | 497 | True |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket5` | `DepthOfField` | 1 | 498 | True |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket5` | `Bloom` | 1 | 500 | True |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsBucket5` | `bAllowPostprocessMLAA` | 1 | 507 | True |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsMobile` | `MotionBlur` | 1 | 610 | FALSE |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsMobile` | `MotionBlurPause` | 1 | 611 | FALSE |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsMobile` | `DepthOfField` | 1 | 612 | FALSE |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsMobile` | `Bloom` | 1 | 614 | FALSE |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsFlash` | `MotionBlur` | 1 | 666 | FALSE |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsFlash` | `MotionBlurPause` | 1 | 667 | FALSE |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsFlash` | `DepthOfField` | 1 | 668 | FALSE |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsFlash` | `Bloom` | 1 | 670 | FALSE |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsFlash_Detail` | `MotionBlur` | 1 | 682 | FALSE |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsFlash_Detail` | `MotionBlurPause` | 1 | 683 | FALSE |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsFlash_Detail` | `DepthOfField` | 1 | 684 | FALSE |
> | `BmGame/Config/BmSystemSettings.ini` | `SystemSettingsFlash_Detail` | `Bloom` | 1 | 686 | FALSE |
923,924c923,924
< | `BmGame/Config/BmSystemSettings.ini` | 82 | `SystemSettings` | `CSMMinimumFOV` | 40.000000 |
< | `BmGame/Config/BmSystemSettings.ini` | 83 | `SystemSettings` | `CSMFOVRoundFactor` | 4.000000 |
---
> | `BmGame/Config/BmSystemSettings.ini` | 82 | `SystemSettings` | `CSMMinimumFOV` | 40 |
> | `BmGame/Config/BmSystemSettings.ini` | 83 | `SystemSettings` | `CSMFOVRoundFactor` | 4 |
930c930
< | `BmGame/Config/BmSystemSettings.ini` | 120 | `SystemSettings` | `ApexLODResourceBudget` | 100000.000000 |
---
> | `BmGame/Config/BmSystemSettings.ini` | 120 | `SystemSettings` | `ApexLODResourceBudget` | 100000.0 |
933c933
< | `BmGame/Config/BmSystemSettings.ini` | 123 | `SystemSettings` | `ApexDestructionMaxChunkSeparationLOD` | 1.000000 |
---
> | `BmGame/Config/BmSystemSettings.ini` | 123 | `SystemSettings` | `ApexDestructionMaxChunkSeparationLOD` | 1.0 |
940,945c940,945
< | `BmGame/Config/BmSystemSettings.ini` | 130 | `SystemSettings` | `ApexGRBMeshCellSize` | 7.500000 |
< | `BmGame/Config/BmSystemSettings.ini` | 131 | `SystemSettings` | `ApexGRBNonPenSolverPosIterCount` | 9 |
< | `BmGame/Config/BmSystemSettings.ini` | 132 | `SystemSettings` | `ApexGRBFrictionSolverPosIterCount` | 3 |
< | `BmGame/Config/BmSystemSettings.ini` | 133 | `SystemSettings` | `ApexGRBFrictionSolverVelIterCount` | 3 |
< | `BmGame/Config/BmSystemSettings.ini` | 134 | `SystemSettings` | `ApexGRBSkinWidth` | 0.025000 |
< | `BmGame/Config/BmSystemSettings.ini` | 135 | `SystemSettings` | `ApexGRBMaxLinearAcceleration` | 1000000.000000 |
---
> | `BmGame/Config/BmSystemSettings.ini` | 130 | `SystemSettings` | `ApexGRBMeshCellSize` | 7.5 |
> | `BmGame/Config/BmSystemSettings.ini` | 131 | `SystemSettings` | `ApexGRBNonPenSolverPosIterCount` | 9; |
> | `BmGame/Config/BmSystemSettings.ini` | 132 | `SystemSettings` | `ApexGRBFrictionSolverPosIterCount` | 3; |
> | `BmGame/Config/BmSystemSettings.ini` | 133 | `SystemSettings` | `ApexGRBFrictionSolverVelIterCount` | 3; |
> | `BmGame/Config/BmSystemSettings.ini` | 134 | `SystemSettings` | `ApexGRBSkinWidth` | 0.025 |
> | `BmGame/Config/BmSystemSettings.ini` | 135 | `SystemSettings` | `ApexGRBMaxLinearAcceleration` | 1000000.0 |
949c949
< | `BmGame/Config/BmSystemSettings.ini` | 140 | `SystemSettings` | `ApexTurbulenceStopEmittingDistance` | 4650.000000 |
---
> | `BmGame/Config/BmSystemSettings.ini` | 140 | `SystemSettings` | `ApexTurbulenceStopEmittingDistance` | 4650.0 |
951,963c951,963
< | `BmGame/Config/BmSystemSettings.ini` | 253 | `SystemSettingsBucket1` | `Bloom` | False |
< | `BmGame/Config/BmSystemSettings.ini` | 260 | `SystemSettingsBucket1` | `bAllowPostprocessMLAA` | False |
< | `BmGame/Config/BmSystemSettings.ini` | 315 | `SystemSettingsBucket2` | `Bloom` | False |
< | `BmGame/Config/BmSystemSettings.ini` | 322 | `SystemSettingsBucket2` | `bAllowPostprocessMLAA` | False |
< | `BmGame/Config/BmSystemSettings.ini` | 377 | `SystemSettingsBucket3` | `Bloom` | True |
< | `BmGame/Config/BmSystemSettings.ini` | 384 | `SystemSettingsBucket3` | `bAllowPostprocessMLAA` | True |
< | `BmGame/Config/BmSystemSettings.ini` | 439 | `SystemSettingsBucket4` | `Bloom` | True |
< | `BmGame/Config/BmSystemSettings.ini` | 446 | `SystemSettingsBucket4` | `bAllowPostprocessMLAA` | True |
< | `BmGame/Config/BmSystemSettings.ini` | 501 | `SystemSettingsBucket5` | `Bloom` | True |
< | `BmGame/Config/BmSystemSettings.ini` | 508 | `SystemSettingsBucket5` | `bAllowPostprocessMLAA` | True |
< | `BmGame/Config/BmSystemSettings.ini` | 615 | `SystemSettingsMobile` | `Bloom` | FALSE |
< | `BmGame/Config/BmSystemSettings.ini` | 671 | `SystemSettingsFlash` | `Bloom` | FALSE |
< | `BmGame/Config/BmSystemSettings.ini` | 687 | `SystemSettingsFlash_Detail` | `Bloom` | FALSE |
---
> | `BmGame/Config/BmSystemSettings.ini` | 252 | `SystemSettingsBucket1` | `Bloom` | False |
> | `BmGame/Config/BmSystemSettings.ini` | 259 | `SystemSettingsBucket1` | `bAllowPostprocessMLAA` | False |
> | `BmGame/Config/BmSystemSettings.ini` | 314 | `SystemSettingsBucket2` | `Bloom` | False |
> | `BmGame/Config/BmSystemSettings.ini` | 321 | `SystemSettingsBucket2` | `bAllowPostprocessMLAA` | False |
> | `BmGame/Config/BmSystemSettings.ini` | 376 | `SystemSettingsBucket3` | `Bloom` | True |
> | `BmGame/Config/BmSystemSettings.ini` | 383 | `SystemSettingsBucket3` | `bAllowPostprocessMLAA` | True |
> | `BmGame/Config/BmSystemSettings.ini` | 438 | `SystemSettingsBucket4` | `Bloom` | True |
> | `BmGame/Config/BmSystemSettings.ini` | 445 | `SystemSettingsBucket4` | `bAllowPostprocessMLAA` | True |
> | `BmGame/Config/BmSystemSettings.ini` | 500 | `SystemSettingsBucket5` | `Bloom` | True |
> | `BmGame/Config/BmSystemSettings.ini` | 507 | `SystemSettingsBucket5` | `bAllowPostprocessMLAA` | True |
> | `BmGame/Config/BmSystemSettings.ini` | 614 | `SystemSettingsMobile` | `Bloom` | FALSE |
> | `BmGame/Config/BmSystemSettings.ini` | 670 | `SystemSettingsFlash` | `Bloom` | FALSE |
> | `BmGame/Config/BmSystemSettings.ini` | 686 | `SystemSettingsFlash_Detail` | `Bloom` | FALSE |
```
