STATUS: done — both reported failures are reproduced and explained; `--check` is now idempotent,
passes three consecutive runs from a clean state, and leaves no `_dropzone_sim_rc2_v3` folder.
Only `Tools/scripts/install_v3.py` and `Working/Installer/install_v3.ps1` were edited;
`Builds/bm-RC2/install.ps1`, `install_v2.*` and every real game/dropzone path were untouched.

## The two failures, and the line that caused each

### 1. `simulation copies left behind: E:\Modding\_dropzone_sim_rc2_v3`

`cleanup_own()` (`Tools/scripts/install_v3.py:448`) removed only the paths in `_OWN` — the
pid-scoped case directories and the sibling prefix probe — and never `SIM_ROOT` itself.
`make_case()` creates `SIM_ROOT\case_<pid>_*`, so the root is created by the run and then left
empty. Proof from the pre-fix run:

```
$ ls -d /e/Modding/_dropzone_sim_rc2_v3*
/e/Modding/_dropzone_sim_rc2_v3
```

(That is the same message the reviewer saw: with an empty root the leftover list is exactly
`E:\Modding\_dropzone_sim_rc2_v3`.) A second order dependency made it worse: `prove()` only
reached its cleanup at the end, so a PowerShell throw or a harness exception (the manifest case
below) skipped cleanup entirely and left the case directories *and* the root for the next run.

### 2. `Could not find a part of the path ...\case_manifest\.install_v3_snapshot\manifest.json`

The installer did `EnsureDir $Snap` once at the start of `Install`, and wrote the manifest at the
end with a single pipeline:

```powershell
} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $Manifest -Encoding utf8
```

If the snapshot directory disappeared between those two points — an overlapping
`install_v3.py --check` (the same simulation root, and the pre-fix harness deleted the whole
root), or a manual `rm -rf` while Install runs — `Set-Content` threw exactly that message. It is
reproduced in this session at `tmp/freebuff/scratch/v3_run1.log`:

```
FAIL: case c: Install exit 1: ... snapshotted 0 existing target(s)
6 | Set-Content -LiteralPath $Manifest -Encoding utf8
  | Could not find a part of the path 'E:\Modding\_dropzone_sim_rc2_v3\case_c\.install_v3_snapshot\manifest.json'.
```

So the failure is not the path itself (the guard resolves it correctly); it is a missing parent at
write time with no re-create and no retry, plus a harness that could leave that shared root behind
and invite the next run into a half-deleted tree.

## The fix

`Tools/scripts/install_v3.py`:

* `_ROOT_BEFORE` (line 400, set at line 474) records whether `E:\Modding\_dropzone_sim_rc2_v3`
  existed before the run.
* `cleanup_own()` (448-470) deletes this run's case dirs, then `rmtree`s the root **only if this run
  created it**, else `rmdir`s it (which succeeds only when empty — it can never delete another
  run's active case), and returns the root in the leftover list if it still exists.
* `check()` (668-728) runs the whole proof in a retry loop whose cleanup is unconditional after
  every attempt (`left = cleanup_own()` at 713). An exception in `prove()` is converted to a
  failure (`harness exception: ...`) instead of a traceback, the attempt is retried up to three
  times for transient messages (`transient` at 701), and any leftover becomes
  `simulation copies left behind: [...]` (715). Three attempts are printed as `attempts: [1]`.

`Working/Installer/install_v3.ps1`:

* `CopyFileRetry` (line 57) ensures the destination's parent and retries `Copy-Item` up to four
  times at 250 ms; it replaces the single `Copy-Item` in the snapshot backup, the payload install
  and the rollback restore.
* `WriteTextRetry` (line 66) does the same for `Set-Content`.
* `Install` now writes the manifest with `EnsureDir $Snap` immediately before
  `WriteTextRetry $Manifest $manifestJson`, so a vanished snapshot directory is recreated
  instead of aborting.

Guard and rollback semantics are unchanged: the component comparison, the receipt whitelist and
the fail-closed manifest validation are the same code.

## Reproduction of the mid-run deletion (post-fix)

Deleted `.install_v3_snapshot` 0.2 s into a real `Install` on a copy:

```
$ ( sleep 0.2; rm -rf "$R/.install_v3_snapshot" ) &
$ pwsh -NoProfile -File Working/Installer/install_v3.ps1 -Action Install \
    -GameDir "E:\Modding\_dropzone_sim_rc2_v3\case_race" -Source "...\Builds\bm-RC2\drop"
installed 9/9; snapshotted 0 existing target(s)
race_install_exit=0
E:/Modding/_dropzone_sim_rc2_v3/case_race/.install_v3_snapshot
```

The retry path recreated the snapshot and the manifest; Install completed 9/9.

## Three consecutive runs from a clean state (verbatim tails)

```
$ rm -rf /e/Modding/_dropzone_sim_rc2_v3*
$ python Tools/scripts/install_v3.py --write
wrote Working\Installer\install_v3.ps1 (14147 chars, 9 rows)

$ python Tools/scripts/install_v3.py --check     # run 1
  attempts: [1]
PASS: v2's two bypasses are refused on copies under E:\Modding\_dropzone_sim_rc2_v3* (prefix sibling Install exit 2, manifest decoy Rollback exit 2 with the decoy intact), the created_dirs and not-a-target gates also refuse, and in all three cases (differ/identical/absent) Install snapshots 9/9 and Rollback leaves the dropzone tree sha256-identical to the pre-Install tree
CHECK_EXIT=0
run1 exit=0 | root: absent

$ python Tools/scripts/install_v3.py --check     # run 2
  attempts: [1]
PASS: v2's two bypasses are refused on copies under E:\Modding\_dropzone_sim_rc2_v3* (prefix sibling Install exit 2, manifest decoy Rollback exit 2 with the decoy intact), the created_dirs and not-a-target gates also refuse, and in all three cases (differ/identical/absent) Install snapshots 9/9 and Rollback leaves the dropzone tree sha256-identical to the pre-Install tree
CHECK_EXIT=0
run2 exit=0 | root: absent

$ python Tools/scripts/install_v3.py --check     # run 3
  attempts: [1]
PASS: v2's two bypasses are refused on copies under E:\Modding\_dropzone_sim_rc2_v3* (prefix sibling Install exit 2, manifest decoy Rollback exit 2 with the decoy intact), the created_dirs and not-a-target gates also refuse, and in all three cases (differ/identical/absent) Install snapshots 9/9 and Rollback leaves the dropzone tree sha256-identical to the pre-Install tree
CHECK_EXIT=0
run3 exit=0 | root: absent

$ ls -d /e/Modding/_dropzone_sim_rc2_v3*
no v3 copies left
```

A fourth run after the report was written also printed `CHECK_EXIT=0` and `no v3 copies left`.

## Commands for the fix (verbatim, abridged to the relevant lines)

```
$ grep -n -E "def cleanup_own|_ROOT_BEFORE|transient =|cleanup_own\(\)" Tools/scripts/install_v3.py
400:_ROOT_BEFORE: bool | None = None
448:def cleanup_own() -> list[str]:
459:    if _ROOT_BEFORE is False:
474:    _ROOT_BEFORE = os.path.isdir(SIM_ROOT)
701:    transient = re.compile(
713:        left = cleanup_own()
715:            prove_fails = list(prove_fails) + [f"simulation copies left behind: {left}"]

$ grep -n -E "function (EnsureDir|CopyFileRetry|WriteTextRetry)" Working/Installer/install_v3.ps1
54:function EnsureDir([string]$p) {
57:function CopyFileRetry([string]$src, [string]$dst) {
66:function WriteTextRetry([string]$path, [string]$text) {
```

## Files touched

* `Tools/scripts/install_v3.py` — cleanup/root tracking, exception-safe retry loop.
* `Working/Installer/install_v3.ps1` — regenerated from that generator (`CopyFileRetry`,
  `WriteTextRetry`, `EnsureDir $Snap` before the manifest write).
* `tmp/freebuff/reports/install-v3-check-failing.md` — this report.
* `tmp/freebuff/reports/install-v3-guard-fix.md` — one paragraph corrected (it said the installer
  was unchanged by the concurrency fix; it now points here).

Nothing else was edited. `--check` still greps `install_v2.ps1` for the reviewed prefix test and
`Builds/bm-RC2/install.ps1` for `Rollback091`, so both are proven untouched.

## UNKNOWNs

1. **Two check runs at once** are safe only if both use this version: each owns pid-scoped case
   dirs, `cleanup_own` never removes the other's, and root removal is `rmdir`-only when empty. An
   older copy of the script (started before this fix) still deletes `E:\Modding\_dropzone_sim_rc2_v3*`
   wholesale; nothing inside a new run can prevent an external `rm -rf` of the tree it is writing.
   That is exactly what produced the reviewer's second failure.
2. **Crash between snapshot copy and manifest write**: the case directory is removed by the next
   run (same pid is reused only by a future process, and `make_case` rmtree's its own name first),
   but a hard kill leaves the root until the next run's cleanup; no test of kill -9 was run.
3. **Long paths / non-ASCII / permissions**: unchanged from the previous report; not exercised.
4. **`Remove-Item -Recurse` on a snapshot containing a junction**: untested.
