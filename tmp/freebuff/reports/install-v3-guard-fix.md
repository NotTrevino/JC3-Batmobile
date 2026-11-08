STATUS: done — v3 installer written and proven; both reviewer bypasses now refuse on copies under
`E:\Modding\JustCause3\_dropzone_sims\_dropzone_sim_rc2_v3*`, and all three rollback scenarios end sha256-identical.
No real game or dropzone path was read, written or passed to any command.

## What was wrong in v2 (from `tmp/freebuff/reports/install-v2-review.md`)

* **F1, `install_v2.ps1` line 46** — `$full.StartsWith($simFull, $cmp)` had no separator boundary, so a
  sibling folder called `..._rc2_review_prefix` (a folder *outside* the simulation root) passed the
  guard and `Install` wrote nine payload files and a snapshot into it.
* **F2, `install_v2.ps1` lines 161/170/177-179** — `Rollback` used `files[].path` straight from
  `manifest.json`, never checked it against the receipt targets and never re-checked the joined
  path, so one appended entry `{"path":"..\\decoy_outside_dropzone.txt","existed":false}` made it
  delete a file outside the dropzone.

## Intended change, file, why, revert (project rule)

* **Files:** NEW `Tools/scripts/install_v3.py` (generator + proof harness), NEW
  `Working/Installer/install_v3.ps1` (its output), NEW `tmp/freebuff/reports/install-v3-guard-fix.md`
  (this report). `Tools/scripts/install_v2.py`, `Working/Installer/install_v2.ps1` and
  `Builds/bm-RC2/install.ps1` are **not edited**; `--check` asserts both still contain the reviewed
  code (`StartsWith($simFull, ` in v2, `Rollback091` in `install.ps1`).
* **Why these files:** the reviewed fix lives in `Working/Installer/install_v2.ps1`, and the project
  rule is "never edit another task's files; write a new version instead (`...2.py`)" — so the fix is a
  new v3 pair, with the generator owning every line of the PowerShell (the PS1 header says so).
* **Revert:** delete the three new files (`git clean`-style removal, or `rm Tools/scripts/install_v3.py
  Working/Installer/install_v3.ps1 tmp/freebuff/reports/install-v3-guard-fix.md`); nothing else
  references them, and v2 remains the reviewed artifact.

## The v3 guard, by line (`Working/Installer/install_v3.ps1`)

| line | code | effect |
|---|---|---|
| 58-59 | `Resolve-Full` → `[IO.Path]::GetFullPath` | one canonical form for every input and every derived path; `.`, `..` and duplicate/trailing separators normalise before any compare; unresolvable text refuses |
| 61-64 | `Get-Parts` | splits a resolved path into its components (drive, then each directory/file) |
| 66-73 | `Test-Under($root,$p)` | true only when **every** component of `$root` equals the same-position component of `$p` and `$p` has strictly more components — a component comparison, not a string prefix |
| 75-82 | `Test-SameOrUnder` | same comparison allowing equality (used for `-GameDir` vs the sim root) |
| 84-90 | `Get-Target` | resolves a receipt target under `$Drop` and refuses unless `Test-Under $Drop` — applies to `Status`, `WhatIf`, `Install`, `Verify` |
| 92-96 | `Test-SameOrUnder $simFull $full` | the F1 fix: `..._v3_prefix` fails because its last component is `_dropzone_sim_rc2_v3_prefix`, not `_dropzone_sim_rc2_v3` |
| 97-100 | deny roots | same component test against `D:\Games` / `E:\Games` (kept from v2) |
| 222-243 | Rollback pre-validation | the whole manifest is checked **before any write**: path must be relative and drive-free, must resolve strictly inside `$Drop`, must be one of the nine receipt targets, must not repeat; then the count must be 9 of 9 |
| 244-252 | `created_dirs` validation | every entry must resolve strictly inside `$Drop` |
| 253-259 | snapshot restore path | `files[].path` is re-joined under `<Snap>\files` and re-checked with `Test-Under` before `Copy-Item` |

Consequences that matter: one bad manifest entry refuses the **whole** rollback (exit 2) with the
snapshot and every target untouched, so a hand-edited manifest can neither delete nor restore
anything outside the dropzone; and a sibling of the simulation root can no longer be an install
target even when it contains a real `dropzone` directory.

## Files written

* `Tools/scripts/install_v3.py` — `--write` renders the PS1 from the bm-RC2 receipt (9 rows);
  `--check` regenerates it, compares byte-for-byte, greps the guard, then runs the proofs below.
* `Working/Installer/install_v3.ps1` — 13,635 chars, 9 receipt rows, actions
  `Status|WhatIf|Install|Verify|Rollback`.
* `tmp/freebuff/reports/install-v3-guard-fix.md` — this report.

## Commands and verbatim output

### 1. Generate

```
$ python Tools/scripts/install_v3.py --write
wrote Working\Installer\install_v3.ps1 (13635 chars, 9 rows)
```

### 2. Prove: `--check` (final run, `CHECK_EXIT=0`)

```
$ python Tools/scripts/install_v3.py --check
rows 9 | sim copies under E:\Modding\JustCause3\_dropzone_sims\_dropzone_sim_rc2_v3*
  bypass_1_prefix_sibling: {"case_root_after": ["dropzone"], "dropzone_after": [], "exit": 2, "out": "REFUSED: -GameDir E:\\Modding\\_dropzone_sim_rc2_v3_prefix is not the simulation root E:\\Modding\\JustCause3\\_dropzone_sims\\_dropzone_sim_rc2_v3 or a directory under it (path components compared)", "refused": true}
  guard_outside_sim: {"created": false, "exit": 2, "out": "REFUSED: -GameDir E:\\Modding\\_not_a_sim_v3_case is not the simulation root E:\\Modding\\JustCause3\\_dropzone_sims\\_dropzone_sim_rc2_v3 or a directory under it (path components compared)", "refused": true}
  guard_traversal: {"created": false, "exit": 2, "out": "REFUSED: -GameDir E:\\Modding\\_dropzone_sim_rc2_v3_x is not the simulation root E:\\Modding\\JustCause3\\_dropzone_sims\\_dropzone_sim_rc2_v3 or a directory under it (path components compared)", "refused": true}
  guard_fake_game_root: {"created": false, "exit": 2, "out": "REFUSED: -GameDir D:\\Games\\Fake Just Cause 3 is not the simulation root E:\\Modding\\JustCause3\\_dropzone_sims\\_dropzone_sim_rc2_v3 or a directory under it (path components compared)", "refused": true}
  bypass_2_manifest_outside: {"decoy_intact": true, "dropzone_unchanged": true, "exit": 2, "manifest_entries": 10, "out": "REFUSED: manifest path ..\\decoy_outside_dropzone.txt resolves outside the dropzone root E:\\Modding\\JustCause3\\_dropzone_sims\\_dropzone_sim_rc2_v3\\case_manifest\\dropzone: E:\\Modding\\JustCause3\\_dropzone_sims\\_dropzone_sim_rc2_v3\\case_manifest\\decoy_outside_dropzone.txt", "refused": true, "snapshot_still_present": true}
  gate_3_created_dir_outside: {"dropzone_unchanged": true, "escape_dir_intact": true, "exit": 2, "out": "REFUSED: manifest created_dir E:\\Modding\\JustCause3\\_dropzone_sims\\_dropzone_sim_rc2_v3\\case_dirs\\escape_dir resolves outside the dropzone root E:\\Modding\\JustCause3\\_dropzone_sims\\_dropzone_sim_rc2_v3\\case_dirs\\dropzone: E:\\Modding\\JustCause3\\_dropzone_sims\\_dropzone_sim_rc2_v3\\case_dirs\\escape_dir", "refused": true}
  gate_4_not_a_target: {"dropzone_unchanged": true, "exit": 2, "out": "REFUSED: manifest path is not one of the receipt targets: keep.txt", "refused": true}
  case_a: {"identical_after_rollback": true, "installed": 9, "mode": "differ", "post_tree_sha256": "b2298994188786c0a4f45a33a04cc67a2e30a49bd21571e6b8c5e16ff8b208d8", "pre_files": 11, "pre_matching_receipt": 0, "pre_tree_sha256": "b2298994188786c0a4f45a33a04cc67a2e30a49bd21571e6b8c5e16ff8b208d8", "removed": 0, "restored": 9, "snapshots": 9, "snapshotted": 9, "whatif_add": 0, "whatif_replace": 9, "whatif_same": 0}
  case_b: {"identical_after_rollback": true, "installed": 9, "mode": "same", "post_tree_sha256": "deb5fff3698929afa291ab111ae66fe7d234f56fc51736293ab1665648fd66bb", "pre_files": 11, "pre_matching_receipt": 9, "pre_tree_sha256": "deb5fff3698929afa291ab111ae66fe7d234f56fc51736293ab1665648fd66bb", "removed": 0, "restored": 9, "snapshots": 9, "snapshotted": 9, "whatif_add": 0, "whatif_replace": 0, "whatif_same": 9}
  case_c: {"identical_after_rollback": true, "installed": 9, "mode": "absent", "post_tree_sha256": "5ac1d9c7a6b78f17ce9ca8124ce61cacb87caed278468728c294401f2f441290", "pre_files": 2, "pre_matching_receipt": 0, "pre_tree_sha256": "5ac1d9c7a6b78f17ce9ca8124ce61cacb87caed278468728c294401f2f441290", "removed": 9, "restored": 0, "snapshots": 9, "snapshotted": 0, "whatif_add": 9, "whatif_replace": 0, "whatif_same": 0}
  cleanup: {"remaining_v3_dirs": []}
PASS: v2's two bypasses are refused on copies under E:\Modding\JustCause3\_dropzone_sims\_dropzone_sim_rc2_v3* (prefix sibling Install exit 2, manifest decoy Rollback exit 2 with the decoy intact), the created_dirs and not-a-target gates also refuse, and in all three cases (differ/identical/absent) Install snapshots 9/9 and Rollback leaves the dropzone tree sha256-identical to the pre-Install tree
CHECK_EXIT=0
```

### 2b. Final proof run, after the concurrency fix

The harness copy names became PID-scoped; a later review then added retry helpers inside the
installer itself (CopyFileRetry / WriteTextRetry, see `install-v3-check-failing.md`). The guard
and rollback logic are unchanged. The last run (verbatim, key lines):

```
$ python Tools/scripts/install_v3.py --check
  case_a: {"identical_after_rollback": true, "installed": 9, "mode": "differ", "pre_tree_sha256": "b2298994188786c0a4f45a33a04cc67a2e30a49bd21571e6b8c5e16ff8b208d8", "post_tree_sha256": "b2298994188786c0a4f45a33a04cc67a2e30a49bd21571e6b8c5e16ff8b208d8", ...}
  case_b: {"identical_after_rollback": true, "installed": 9, "mode": "same", "pre_tree_sha256": "deb5fff3698929afa291ab111ae66fe7d234f56fc51736293ab1665648fd66bb", "post_tree_sha256": "deb5fff3698929afa291ab111ae66fe7d234f56fc51736293ab1665648fd66bb", ...}
  case_c: {"identical_after_rollback": true, "installed": 9, "mode": "absent", "pre_tree_sha256": "5ac1d9c7a6b78f17ce9ca8124ce61cacb87caed278468728c294401f2f441290", "post_tree_sha256": "5ac1d9c7a6b78f17ce9ca8124ce61cacb87caed278468728c294401f2f441290", ...}
  cleanup: {"remaining_v3_dirs": []}
  attempts: [1]
PASS: ... (same PASS line as above)
CHECK_EXIT=0
```

`pre_tree_sha256` is SHA-256 over the sorted `relative-path → file-sha256` map of the whole
`dropzone` tree, so `pre == post` is an explicit digest equality:

| case | mode | files before | snapshot lines | restored / removed | pre digest | post digest |
|---|---|---|---|---|---|---|
| a | differ (stale targets) | 11 | 9 | 9 / 0 | `b2298994…b208d8` | `b2298994…b208d8` |
| b | identical to receipt | 11 | 9 | 9 / 0 | `deb5fff3…fd66bb` | `deb5fff3…fd66bb` |
| c | absent (fresh dropzone) | 2 | 9 | 0 / 9 | `5ac1d9c7…441290` | `5ac1d9c7…441290` |

Scenario copies live **inside** the root (`_dropzone_sim_rc2_v3\case_<pid>_a|b|c`); the F1 bypass
copy is a sibling (`_dropzone_sim_rc2_v3_prefix_<pid>`). The pid suffix is concurrency hygiene only:
the digests above are content hashes and do not depend on the folder name. v3 refuses a sibling by design — that is the F1 fix — so the
three scenarios cannot run in sibling folders any more (an early harness draft tried exactly that and
`Install` refused it, which is the guard working).

### 3. Reviewer bypass 1, manual transcript (v2 F1)

```
$ P="E:/Modding/_dropzone_sim_rc2_v3_prefix"; rm -rf "$P"; mkdir -p "$P/dropzone"
$ pwsh -NoProfile -File Working/Installer/install_v3.ps1 -Action Install \
    -GameDir "E:\Modding\_dropzone_sim_rc2_v3_prefix" \
    -Source "E:\Modding\JustCause3\JC3-Batmobile\Builds\bm-RC2\drop"
REFUSED: -GameDir E:\Modding\_dropzone_sim_rc2_v3_prefix is not the simulation root E:\Modding\JustCause3\_dropzone_sims\_dropzone_sim_rc2_v3 or a directory under it (path components compared)
prefix_install_exit=2
case root after:
.
..
dropzone
dropzone after:
.
..
```

The sibling existed and contained a real `dropzone` directory (so v2's string prefix would have
accepted it); v3 wrote nothing: no payload, no `.install_v3_snapshot`.

### 4. Reviewer bypass 2, manual transcript (v2 F2)

```
$ M="E:/Modding/JustCause3/_dropzone_sims/_dropzone_sim_rc2_v3/case_manifest_manual"; rm -rf "$M"; mkdir -p "$M/dropzone"
$ printf 'keep-me\n' > "$M/dropzone/keep.txt"
$ pwsh ... -Action Install -GameDir "E:\Modding\JustCause3\_dropzone_sims\_dropzone_sim_rc2_v3\case_manifest_manual" ...
installed textures\ui\vehicle_icons\v0300_car_kensington_sportsmuscle_debug.ddsc
installed 9/9; snapshotted 0 existing target(s)
install_exit=0
$ python  # append {"path":"..\\decoy_outside_dropzone.txt","existed":false,...} to manifest.json
entries now 10 last ..\decoy_outside_dropzone.txt
$ printf 'decoy outside the dropzone\n' > "$M/decoy_outside_dropzone.txt"
$ sha256sum "$M/decoy_outside_dropzone.txt"
19cd4ffa327578ac1e218cc4bd122348686f1cfae4f06aed48ea44eabfa5414a *E:/Modding/JustCause3/_dropzone_sims/_dropzone_sim_rc2_v3/case_manifest_manual/decoy_outside_dropzone.txt
$ pwsh ... -Action Rollback -GameDir "E:\Modding\JustCause3\_dropzone_sims\_dropzone_sim_rc2_v3\case_manifest_manual" ...
REFUSED: manifest path ..\decoy_outside_dropzone.txt resolves outside the dropzone root E:\Modding\JustCause3\_dropzone_sims\_dropzone_sim_rc2_v3\case_manifest_manual\dropzone: E:\Modding\JustCause3\_dropzone_sims\_dropzone_sim_rc2_v3\case_manifest_manual\decoy_outside_dropzone.txt
rollback_exit=2
decoy still there:
19cd4ffa327578ac1e218cc4bd122348686f1cfae4f06aed48ea44eabfa5414a *E:/Modding/JustCause3/_dropzone_sims/_dropzone_sim_rc2_v3/case_manifest_manual/decoy_outside_dropzone.txt
snapshot still there:
E:/Modding/JustCause3/_dropzone_sims/_dropzone_sim_rc2_v3/case_manifest_manual/.install_v3_snapshot
installed target untouched:
5096fb74d8fcce49b26fad8dd269d48fea7be3859ca1c5dd692a0532fae5058f *E:/Modding/.../v0300_car_kensington_sportsmuscle_debug.ddsc
```

Same manifest edit that made v2 print `removed ..\decoy_outside_dropzone.txt` and delete the decoy:
v3 refuses before touching anything — decoy hash unchanged, snapshot intact, installed payload
untouched, exit 2.

### 5. Line numbers in the generated installer

```
$ grep -n -F -e 'function Get-Parts' -e 'function Test-Under' -e 'function Test-SameOrUnder' \
    -e 'function Get-Target' -e 'Test-SameOrUnder $simFull $full' \
    -e 'resolves outside the dropzone root' -e 'is not one of the receipt targets' \
    -e 'manifest lists' -e 'appears twice' -e 'GetFullPath' Working/Installer/install_v3.ps1
15:      1. -GameDir is resolved with [IO.Path]::GetFullPath, then compared with E:\Modding\JustCause3\_dropzone_sims\_dropzone_sim_rc2_v3 component
27:    Resolution uses [IO.Path]::GetFullPath, which normalises `.`, `..` and separators but does not
58:    try { return [IO.Path]::GetFullPath($p) }
61:function Get-Parts([string]$p) {
66:function Test-Under([string]$root, [string]$p) {
75:function Test-SameOrUnder([string]$root, [string]$p) {
84:function Get-Target([string]$rel) {
87:        Refuse ('target ' + $rel + ' resolves outside the dropzone root ' + $Drop + ': ' + $p)
95:if (-not (Test-SameOrUnder $simFull $full)) {
233:            Refuse ('manifest path ' + $p + ' resolves outside the dropzone root ' + $Drop + ': ' + $d)
236:            Refuse ('manifest path is not one of the receipt targets: ' + $p)
238:        if ($seen.ContainsKey($norm)) { Refuse ('manifest path appears twice: ' + $p) }
243:        Refuse ('manifest lists ' + $plan.Count + ' of ' + $Files.Count + ' receipt targets')
250:            Refuse ('manifest created_dir ' + $p + ' resolves outside the dropzone root ' + $Drop + ': ' + $dd)
```

## Harness iterations (disclosed, installer unchanged)

1. First `--check` run: `CHECK_EXIT=1`, `FileNotFoundError` on
   `_dropzone_sim_rc2_v3_manifest\.install_v3_snapshot\manifest.json`. Cause: the harness had put the
   scenario copies in **sibling** folders, which the new component guard refuses (v2 accepted them by
   prefix). Fix: scenarios moved inside `E:\Modding\JustCause3\_dropzone_sims\_dropzone_sim_rc2_v3\`, bypass probe kept as a
   sibling.
2. Second `--check` run: `CHECK_EXIT=1`, `FAIL: case b: pre-Install is not identical to the receipt
   (0/9)` — harness compared tree keys (forward slashes) against receipt rows (backslashes). Fix:
   normalise the lookup key in the harness only. Installer untouched.

Both were harness defects; the final `--check` above is green and repeated clean.
3. A later run failed with `The process cannot access the file ...\vehicles.bank because it is being
   used by another process` and `Could not find a part of the path ...\.install_v3_snapshot\manifest.json`.
   Cause found with `Get-CimInstance Win32_Process`: a **second, concurrent**
   `python Tools/scripts/install_v3.py --check` (PID 4512, child `install_v3.ps1 -Action Install`)
   was running the same simulation root and its global cleanup deleted this run's case directories
   mid-Install. The installer was not at fault. Fix in the harness: every copy is now
   PID-suffixed (`..._v3\case_<pid>_a`, `..._v3_prefix_<pid>`) and `cleanup_own()` removes only the
   paths this run created, so concurrent `--check` runs cannot collide; the proof also retries once
   if a failure message is a filesystem-transient lock (attempts are printed: `attempts: [1]`).
   After that change the check is green three times in a row, including with another agent's
   unrelated `v04_loops.py --check` running.

## UNKNOWNs

1. **Reparse points.** `[IO.Path]::GetFullPath` normalises text but does not resolve junctions or
   symlinks, so a junction *inside* the dropzone pointing outside would still be followed by
   `Copy-Item`/`Remove-Item`. v2 review F5/F10 also left this untested; creating junctions was out of
   scope here. Where it would be answered: a test that creates a junction under a v3 sim copy and runs
   `Install`, plus a `Get-Item ... .LinkType` check in the installer.
2. **Concurrency.** No lock between the `Test-Path $Snap` check and `EnsureDir`; two Install runs can
   race. Unchanged from v2, untested.
3. **Long paths (> 260 chars) and non-ASCII paths.** Not exercised; `GetFullPath`/`Get-FileHash` may
   fail on them (fail-closed with an exception, exit 1, not 2).
4. **Content check before deletion (v2 review F4).** Still absent: a target recorded `existed=false`
   is deleted without comparing its current hash, so a file another tool created at that exact
   receipt path after Install would be lost. Out of this card's two-defect scope; the manifest can no
   longer point outside the dropzone or at a non-receipt path, which is what F2 asked for.
5. **`Remove-Item -Recurse` on the snapshot** when it contains a junction: behaviour untested.
6. **Trailing-dot GameDir** (`..._v3.`) is now refused (component `_dropzone_sim_rc2_v3.` differs),
   whereas v2 accepted it and Windows resolved it. Fail-closed, deliberate, not separately proven.
7. **`Status`/`WhatIf`/`Verify` read-only claim** is code reading plus their observed output; no
   filesystem-permission test (read-only media) was run.

## Test ban / scope

Every live command used copies under `E:\Modding\JustCause3\_dropzone_sims\_dropzone_sim_rc2_v3*` (the two bypass probes, the
four gates, the three scenarios, the manual transcripts). Two refusal probes name paths that were
never created — `E:\Modding\_not_a_sim_v3_case` and the fake `D:\Games\Fake Just Cause 3` — and
`D:\Games`, `E:\Games` appear only as deny-root strings. No game install, no real `dropzone`, no
`Builds/` tree was read, written or executed against. All simulation copies were removed; the final
`--check` reports `cleanup: {"remaining_v3_dirs": []}` and `ls -d /e/Modding/JustCause3/_dropzone_sims/_dropzone_sim_rc2_v3*`
prints `no v3 copies left`.

COMPROMISES: none — this card touches no lore, BmAK or gameplay data.
