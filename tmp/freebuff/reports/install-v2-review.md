**VERDICT: needs fixes** — the three-scenario proof is sound for an honest `-GameDir` and an honest
manifest, but the guard is a bare string prefix (a sibling folder is accepted, proven below) and
`Rollback` deletes whatever paths the manifest lists (a path outside the dropzone was deleted,
proven below). Both are fixable in two lines each; do not adopt as-is.

**STATUS: review complete, read-only on the installer.** `Working/Installer/install_v2.ps1` and
`Tools/scripts/install_v2.py` were not edited; `python Tools/scripts/install_v2.py --check` is
still green (`CHECK_EXIT=0`, 9 rows, three cases). No real game path was read, written or passed;
the two live tests ran only on `E:\Modding\_dropzone_sim_rc2_review_prefix` and
`E:\Modding\_dropzone_sim_rc2_review_manifest` and both copies were removed afterwards.

## Findings, by line

### F1 — HIGH — line 46: the guard accepts any sibling whose name starts with the sim root

```powershell
46: if (-not ($full.Equals($simFull, $cmp) -or $full.StartsWith($simFull, $cmp))) {
```

`StartsWith` has no separator boundary, so `E:\Modding\_dropzone_sim_rc2_review_prefix` — a folder
outside the simulation root — passes. The deny-root check at 49-53 does not help: the path is not
under `D:\Games` or `E:\Games`.

**Proven:** `Install` on the review copy succeeded (`installed 9/9; snapshotted 9 existing
target(s)`, exit 0, `.install_v2_snapshot` created). Fix: `$full.StartsWith($simFull + '\', $cmp)`
(the deny check at 51 already does exactly this).

### F2 — HIGH — lines 161, 170, 177-179: Rollback trusts the manifest for paths and membership

```powershell
161: $d = Join-Path $Drop $e.path
170:     Remove-Item -LiteralPath $d -Force
177: foreach ($dir in ($m.created_dirs | Sort-Object Length -Descending)) {
179:         Remove-Item -LiteralPath $dir -Force
```

`$e.path` is used as-is: it is never checked against the installer's own `$Files` list, and the
joined path is never re-checked for containment under `$Drop`. Any entry with `existed = false`
deletes whatever sits at that path; any `created_dirs` entry (if empty) is removed.

**Proven:** after a normal Install, one entry `{"path": "..\\decoy_outside_dropzone.txt",
"existed": false}` was appended to the manifest. Rollback printed
`removed ..\decoy_outside_dropzone.txt` and the decoy at the case root was gone (outside the
`dropzone` tree). The summary `rollback 10/9 target(s)` also shows the loop is manifest-driven, not
receipt-bound. Fix: `if ($e.path -notin $Files.rel) { throw }`, then `$fullD =
[IO.Path]::GetFullPath($d); if (-not $fullD.StartsWith($Drop + '\', $cmp)) { throw }` before both
`Copy-Item` and `Remove-Item`, and the same containment test for `created_dirs`.

### F3 — MEDIUM — lines 91-94 with 111/130: an interrupted snapshot is a dead end

`EnsureDir $Snap` runs at 94, the snapshot loop can throw at 111, and the manifest is only written
at 130. A crash/throw in between leaves `.install_v2_snapshot` with no manifest: Install refuses
forever ("a snapshot already exists", proven — exit 1), Rollback refuses ("no snapshot manifest").
Recovery is manual deletion of the folder. Fix: write the manifest before copying, or make Rollback
treat a manifest-less snapshot as "nothing installed yet" and remove it.

### F4 — MEDIUM — line 170: deletion is unconditional on current content

For a target recorded `existed = false`, Rollback deletes whatever is at that path now, with no hash
check. If another tool (or the user) created or replaced that file after Install, its content is
lost and the installer reports a clean rollback. Fix: record the installed hash in the manifest and
refuse (or move to the snapshot) when the current hash differs.

### F5 — MEDIUM — lines 46/55: no reparse-point check

`$Drop` is `Join-Path $full 'dropzone'`; nothing checks whether `$Drop` or a parent under `$full` is
a junction/symlink. If a junction under the sim root points at a real dropzone, every
`Copy-Item`/`Remove-Item` follows it. Untested here (creating junctions was out of scope of the two
tests) — **UNKNOWN**, but F1 makes it reachable from any sibling folder, so it compounds.

### F6 — LOW — line 43: the path forms that are handled, and the one that is only harmless

| input | result | why |
|---|---|---|
| `..._rc2\` (trailing slash) | accepted, normalised | `TrimEnd('\')` at 43 |
| `..._rc2\..\_other` | refused | `GetFullPath` normalises before the compare |
| relative path | refused unless it lands under the root | resolved against the process CWD, then compared |
| 8.3 name `_DROPZO~1` | refused | string compare, no short-name expansion — fail-closed |
| `\\?\E:\Modding\...` | refused | prefix survives `GetFullPath` — fail-closed |
| `..._rc2.` (trailing dot) | accepted | prefix matches and Windows resolves it to the real folder — harmless today, gone with F1 |

### F7 — LOW — lines 60-61: the snapshot sits in the game dir, not the dropzone

`$full\.install_v2_snapshot` is outside the compared tree (which is why the 7231 proof compares
cleanly), but it is inside the folder the user passes as `-GameDir`. An existing folder of that name
(pointed at anything) makes Install throw at 91 — safe, but it also means the snapshot's location is
user-controllable, which is what F2 abuses.

### F8 — LOW — lines 57-59, 99-101: `-Source` is unvalidated

Any directory can be passed, but every file copied must hash-equal the receipt, so the worst case is
re-installing the nine receipt files from a copy. Not a write outside the target tree.

### F9 — INFO — `Status` and `WhatIf` are read-only

No write path is reachable before `EnsureDir $Snap` at 94; both actions only hash and print. This is
code reading, not a filesystem-permission test.

### F10 — LOW — line 182: `Remove-Item -Recurse -Force` on the snapshot

Correct for a snapshot this installer wrote. Behaviour when the snapshot directory contains a
junction is **UNKNOWN** (not tested).

## The question "does Rollback ever delete a file that existed before Install?"

* With the manifest this installer writes: **no.** A target that existed is restored from
  `files\`, never deleted (162-168), and an absent one is deleted only under `elseif` (169-172). The
  three cases in `install_v2.py --check` (differ / identical / absent) still pass, including the
  identical-to-receipt case that broke v1.
* With a manifest that has been edited: **yes** — proven as F2. The installer has no way to tell;
  the manifest is a plain JSON file in a user-writable folder.

## Live tests (verbatim, review copies only)

```
$ pwsh -NoProfile -File Working/Installer/install_v2.ps1 -Action Install \
    -GameDir "E:\Modding\_dropzone_sim_rc2_review_prefix" \
    -Source "E:\Modding\JustCause3\JC3-Batmobile\Builds\bm-RC2\drop"
installed textures\ui\vehicle_icons\v0300_car_kensington_sportsmuscle_debug.ddsc
installed 9/9; snapshotted 9 existing target(s)
install_exit=0
$ ls -a "E:/Modding/_dropzone_sim_rc2_review_prefix"
.  ..  .install_v2_snapshot  dropzone
$ pwsh ... -Action Install (same path, second time)
a snapshot already exists at E:\Modding\_dropzone_sim_rc2_review_prefix\.install_v2_snapshot - run Rollback first
second_exit=1

$ pwsh ... -Action Install -GameDir "E:\Modding\_dropzone_sim_rc2_review_manifest" -Source ...
installed 9/9; snapshotted 9 existing target(s)
install_exit=0
$ python  # append {"path":"..\\decoy_outside_dropzone.txt","existed":false} to manifest.json
entries now 10 last ..\decoy_outside_dropzone.txt
$ pwsh ... -Action Rollback -GameDir "E:\Modding\_dropzone_sim_rc2_review_manifest" -Source ...
removed ..\decoy_outside_dropzone.txt
rollback 10/9 target(s) match the pre-Install state; snapshot removed
rollback_exit=0
$ ls -l "E:/Modding/_dropzone_sim_rc2_review_manifest/decoy_outside_dropzone.txt"
ls: cannot access '...': No such file or directory

$ python Tools/scripts/install_v2.py --check
PASS: guard refuses both probe paths; in all three cases Install snapshots 9/9 and Rollback restores the pre-Install tree byte-for-byte (identical payload case included)
CHECK_EXIT=0
```

## Ordered fix list (smallest first)

1. line 46: add the `'\'` boundary (`$simFull + '\'`), exactly as line 51 already does.
2. Rollback: whitelist `$e.path` against `$Files`, and re-check `GetFullPath($d)` containment under
   `$Drop + '\'`; same for `created_dirs` under `$full`.
3. F4: store each installed hash in the manifest and check it before deleting.
4. F3: write the manifest before the copy loop, or let Rollback clear a manifest-less snapshot.

## UNKNOWNs

1. Junction/symlink behaviour (F5, F10) — not tested; creating junctions was outside the two tests.
2. Whether `Remove-Item -Recurse` on a snapshot containing a junction follows it — untested.
3. Concurrent use: two Install runs racing between `Test-Path $Snap` (91) and `EnsureDir` (94) are
   not serialised — no lock; untested.
4. Long paths (> 260 chars) and non-ASCII paths — not tested.
5. Filesystem permission failures (read-only target, locked file) — not tested; `$ErrorActionPreference
   = 'Stop'` means a locked file aborts mid-rollback with the snapshot still present (safe, manual).

## Labels

Decoded: the installer's text, its line numbers, `install_v2.py`, the `--check` output. Derived: the
bypass analysis, the containment gaps, the fix list. Proven by experiment: F1 (install outside the
sim root) and F2 (delete outside the dropzone). Untested/UNKNOWN: F5, F10, concurrency, long paths,
permissions.
