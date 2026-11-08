# Review — P0-1 · Baseline the standing gates

Independent, read-only pass. Nothing under `Research/`, `Tools/`, `Working/` or either game folder
was edited; the only file written is this report. Card: `GRAB_BACKLOG.md` §0.5 / §0.7 / §12 line 1274
(card at lines 355-362). Output: the MODLOG section `## Unified backlog baseline (P0-1, 2026-10-24)`
at `MODLOG.md:7728`, plus its intent block at `:7713`.

## VERDICT: sound

All nine §0.7 gates are green when re-run today, and the five "content" numbers in the baseline table
that a later card has not touched reproduce exactly (81,952/78,907/1/20,682 for the index;
233/18,865/6,382/17/17 for Havok; 57,187/0 for FX; 41 members/156 vehicles for the fleet; 380
offset-only values and 101 light rigs for the grab). The two rows that no longer match are the two the
project has since grown (`bmak_chain`, `t_rows`), which is what a dated baseline is supposed to look
like, and the header carries the date. The step-2 claim (the dropzone still holds test-091) is true: I
hashed both live files and got the recorded digests exactly.

Blemishes, none of which misstates anything: the hashes are recorded shortened, two rows are now
stale without a per-row date, and the exact `install.ps1 -Action Status` call does not run in this
shell (see issues 1-3).

## Check output (verbatim)

The card has no `--check`; its verification is "run every §0.7 command" plus the Status call. I ran
all nine gates and the dropzone hash check.

```
$ python Tools/scripts/grab_model.py check
sims           4
sim curves     24
sockets        247
socket names   90
light rigs     101
orphan sockets 6
offset-only values 380
banks          30 objects / 16 names
checks         15/15 grab checks passed
schema         6

OK: grab output matches schema 6 and its own summary.

$ python Tools/scripts/bmak_chain.py --check
PASS: chain record current (105 objects, 9225 named bindings, 336 cross-checked, 0 conflicts, 0 bool words left unnamed)

$ python Tools/scripts/bmak_coverage.py --check
  audio       361 rows ->  8 T rows, 0 unassigned
  lights      101 rows ->  8 T rows, 0 unassigned
  weapons      62 rows -> 10 T rows, 0 unassigned
check ok

$ python Tools/scripts/jc3index.py check
check ok: 81952 rows, 78907 paths, 1 unnamed entries, DLC 20682/20682 named, sources {...}

$ python Tools/scripts/jc3hkx.py check --all
entities 233 | files 234 | objects 130513 | hulls 18865 (convex 18865) | mesh shapes 4791 | geometries 9582 | compounds 6382 (35499 instances, 25769 with a part index, 6341 AABB unions exact) | station sets 17 (land_global agree 17, disagree 0)
check ok

$ python Tools/scripts/jc3fx.py check
checked 57187 files | problems 0

$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 39 keep 61 epe 26 re-read 0 blocked 13 out 36 superseded 7 | edits 35 over 16 rows
check ok

$ python Tools/scripts/t3_fleet.py --check
E:\Modding\JustCause3\JC3-Batmobile\Working\Translation\T3_FLEET.md: 41 members over 156 vehicles
check ok

$ python Tools/scripts/status_audit.py --check
STATUS.md is current
```

All nine exit green, as the baseline claims.

Dropzone (the card's step 2), computed directly because the scripted `Status` action does not run in
this shell (issue 3):

```
v0300_car_kensington_sportsmuscle_civilian_01.ee      10737057  6AB8275F566A354298C943F3CE3D747086C1B0E832091805EC9E5D70DEAFCF8D
v0300_car_kensington_sportsmuscle_civilian_01.ee.toc     50643  444ED479EEBA144F14B46554844E2768734D760054EED54C9FD73BA700AC55AA
```

The baseline records `.ee` `6AB8275F…FCF8D`, `.toc` `444ED479…C55AA`, "== test-091 (all match)" —
prefix and suffix of exactly these digests, and both equal the constants `install.ps1` installs from
(`$EeSha`/`$TocSha` at `Builds/test-091/install.ps1:10-11`, sizes `10,737,057` / `50,643` at
`:12-13`). Nothing was installed or rolled back.

## Issues

### 1. The recorded hashes are abbreviated, so the row cannot be checked from the log alone

`MODLOG.md:7743`: `.ee` `6AB8275F…FCF8D`, `.toc` `444ED479…C55AA`. The card's Do step 2 asks to
"record the live `.ee`/`.toc` hashes"; 13 characters are a fingerprint, not a hash — a reader cannot
recompute a match, and the full values exist only inside `install.ps1`. They are correct (verified
above), and the intent block says the Status call is read-only, so this is a record-quality point, not
a wrong value. The build sizes are not recorded either.

### 2. Two of the nine rows are now stale, and the table does not say so per row

| row | baseline (2026-10-24) | today |
|---|---|---|
| `bmak_chain.py --check` | 86 objects, 8,595 bindings | **105 objects, 9,225 bindings** |
| `t_rows.py check` | 105 rows (edit 16, next 5, keep 49, epe 16, blocked 11, out 8) | **198 rows** (edit 16, next 39, keep 61, epe 26, re-read 0, blocked 13, out 36, superseded 7) |

Both are consequences of cards that ran after P0-1 (the G1 record grew; the ledger kept taking T
rows), and both gates are green today, so nothing is wrong. The baseline's internal sum does check
out (16+5+49+16+11+8 = 105 = the row total, i.e. `superseded` and `re-read` were 0 then). What a
future reader lacks is a per-row "as of" marker: the heading is dated, the table is not. A one-line
"numbers are the 2026-10-24 state; the gates are re-run at every phase start" would close it.

### 3. `install.ps1 -Action Status` cannot be re-run in this shell

```
$ powershell -NoProfile -Command "& 'E:\Modding\JustCause3\JC3-Batmobile\Builds\test-091\install.ps1' -Action Status"
+ CategoryInfo : ObjectNotFound: (Get-FileHash:String) [install.ps1], CommandNotFoundException
```

`Get-FileHash` is missing from the PowerShell on this machine's PATH, so the card's exact step-2
command fails here — the author must have run it in a shell where it exists (the P0-1 block was
written 2026-10-24). This is an environment gap, not a false claim: the hashes the call would print
are the ones I computed, and they match. If P0-1's step 2 is ever repeated, the command should fall
back to `certutil -hashfile` or Python; as written, the check is not reproducible by a reviewer.

### 4. R11 in the strict sense: the table is a transcription, and I can only check it by re-running

The nine results are hand-copied one-line outputs (the card asks for exactly that, so this is by
design, not a break). Five of the nine are still exact today, two drifted for good reasons, and two
are state assertions (`check ok`, `STATUS.md is current`). No number in the block is invented, and
each is the tail of a command that a reader can re-run — which is the best a log section can do.

### 5. No R4/R5 exposure

The block makes no value or behaviour claim beyond the gates' own verdicts and the dropzone identity.
The `.ee`/`.toc` equality is the only "value", and it is a hash equality (verified). There is no
member-name-to-behaviour inference anywhere in the section.

## Spot-checks

| value in the baseline | where verified |
|---|---|
| `jc3index` 81,952 rows / 78,907 paths / 1 unnamed / DLC 20,682/20,682 | own run: `check ok: 81952 rows, 78907 paths, 1 unnamed entries, DLC 20682/20682 named` — identical |
| `jc3hkx` 233 entities / 18,865 hulls / 6,382 compounds / 17/17 station sets | own run: identical line, incl. 130,513 objects, 35,499 instances, 6,341 AABB unions exact |
| `jc3fx` 57,187 files, problems 0 | own run: `checked 57187 files \| problems 0` |
| `t3_fleet` 41 members over 156 vehicles | own run: `T3_FLEET.md: 41 members over 156 vehicles`, `check ok` |
| `grab_model` 15/15 checks, schema 6, 380 offset-only values, 101 rigs | own run: `checks 15/15`, `offset-only values 380`, `light rigs 101`, `OK: grab output matches schema 6` |
| dropzone `.ee`/`.toc` == test-091 | own SHA-256 of both live files under `D:\Games\Just Cause 3\dropzone\…` = the recorded prefixes/suffixes and the `$EeSha`/`$TocSha` constants in `install.ps1:10-11` |
