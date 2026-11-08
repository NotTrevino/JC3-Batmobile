# DONE — V-RC2 (verification gates on the RC2 candidate)

STATUS: blocked — the gate `tmp/freebuff/reports/B-RC2.md` does not exist, and there is no
`Builds/bm-RC2` tree to gate. The brief's instruction for this case is explicit: write
`STATUS: blocked` and stop. Nothing was built, run, copied or installed.

## Summary

V-RC2 verifies a candidate that has not been produced. Per the brief's gate:

> Start only after `E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/B-RC2.md` exists (if not,
> write `STATUS: blocked` and stop).

`B-RC2.md` is absent, and `Builds/` contains only `bm-001` … `bm-013b`, `bm-RC1` and the
`_bisect` / `_deployed` / `_rollback` / `_shelved-061maxrpm` trees — no `bm-RC2`. Running V-01,
V-02, V-03 or the V-05 delta against a nonexistent candidate would require inventing inputs,
which the one rule forbids.

Consequently:

- **V-01 file gates**: not run (no `Builds/bm-RC2` to read).
- **V-02 geometry/pose gates**: not run.
- **V-03 wiring gates** (`Tools/scripts/v03_wiring.py`): not run.
- **V-05 predicted-results delta (Q-1, Q-2 vs RC1)**: not written. The RC2 input diff cannot be
  cited because there is no RC2 input tree.
- No output was created under `Builds/bm-RC2/verify/` — that path does not exist and was not
  created, since creating a candidate tree is the build card's job, not this one's.

The operator's overrides were respected: no install script, no write under `E:/Games`,
`D:/Games` or any dropzone, no game launch, no edits to any existing `Builds/bm-*` tree, no git,
no `Builds/` or `Working/` writes beyond this report.

## Files written

| file | what |
|---|---|
| `tmp/freebuff/reports/V-RC2.md` | this blocked report (the only file touched) |

## Commands run, with output

```
=== gate B-RC2 ===
ls: cannot access 'tmp/freebuff/reports/B-RC2.md': No such file or directory
=== candidate tree ===
total 448
drwxr-xr-x 1 User 197121 0 Nov  2 21:48 .
drwxr-xr-x 1 User 197121 0 Nov  2 23:21 ..
drwxr-xr-x 1 User 197121 0 Oct  8 06:38 _bisect
drwxr-xr-x 1 User 197121 0 Oct  8 04:40 _deployed
drwxr-xr-x 1 User 197121 0 Oct 21 10:29 _rollback
drwxr-xr-x 1 User 197121 0 Oct 15 18:42 _shelved-061maxrpm
drwxr-xr-x 1 User 197121 0 Nov  1 00:20 bm-001
drwxr-xr-x 1 User 197121 0 Nov  1 00:27 bm-002
drwxr-xr-x 1 User 197121 0 Oct 31 15:05 bm-004
drwxr-xr-x 1 User 197121 0 Oct 31 06:16 bm-005
drwxr-xr-x 1 User 197121 0 Oct 31 07:48 bm-006
drwxr-xr-x 1 User 197121 0 Oct 31 04:33 bm-007
drwxr-xr-x 1 User 197121 0 Oct 31 04:27 bm-008
drwxr-xr-x 1 User 197121 0 Oct 31 00:54 bm-009
drwxr-xr-x 1 User 197121 0 Nov  2 01:08 bm-013
drwxr-xr-x 1 User 197121 0 Nov  2 00:41 bm-013b
drwxr-xr-x 1 User 197121 0 Nov  2 21:48 bm-RC1
drwxr-xr-x 1 User 197121 0 Oct  7 13:15 test-001
drwxr-xr-x 1 User 197121 0 Oct  7 13:59 test-002
ls: cannot access 'Builds/bm-RC2': No such file or directory
```

No further command was run after the gate check.

## What unblocks it

1. `tmp/freebuff/reports/B-RC2.md` appears and names the RC2 candidate tree.
2. A `Builds/bm-RC2` tree exists with its input manifest, so V-01/V-02/V-03 can read it and
   write only under `Builds/bm-RC2/verify/`.
3. Then: run `Tools/scripts/v01_*`, `Tools/scripts/v02_*`, `Tools/scripts/v03_wiring.py` (per
   the GRAB_BACKLOG §7 tracker rows), and compute the V-05 delta for each Q-1/Q-2 test against
   RC1 with the input diff cited.

## UNKNOWNs

- **Every gate result** — UNKNOWN, not run. There is no RC2 artifact, so V-01/V-02/V-03 have no
  input. It would be found by the three steps above once the build card lands.
- **Whether RC2 changes any Q-1/Q-2 predicted result, and which input diff causes it** —
  UNKNOWN. No RC2 input tree exists, so no diff can be cited; asserting a delta would be a
  guess.
- **Whether `Builds/bm-RC2` is meant to be created by this card** — UNKNOWN, and deliberately
  not assumed: the brief says build into a new private tree for a *build* task, while this card
  is verification and explicitly says to start only after the build report exists.
