# B-01 for the bm-RC4 line: scaffold `Builds/bm-RC4-base`

Card `B-01` (`GRAB_BACKLOG.md` §8): the phase-B scaffold, an identity build whose `.ee`/`.toc` are
byte-identical to the base, with a receipt and an unrun installer. This is that step for the new
release-candidate line, built as a **new private tree**.

```
python Tools/scripts/bm_build.py --tag bm-RC4-base --base test-091 --batches
```

Exit 0. No `--force`, so the target had to be absent: `bm_build.py` raises
`Builds/bm-RC4-base exists (use --force to rebuild it)` when the directory is already there, and it
did not raise. Nothing under `Builds/` was modified except the new directory, and the game folder
was not read, written or launched (see §5).

## 1. What was written

| path | contents |
|---|---|
| `Builds/bm-RC4-base/aaf/` | 590 files, 22,011,703 B, tree digest `561D301D0499EE7B…` — a copy of `Builds/test-091/aaf` |
| `Builds/bm-RC4-base/v0300_…_civilian_01.ee` | 10,737,057 B, sha256 `6AB8275F566A354298C943F3CE3D747086C1B0E832091805EC9E5D70DEAFCF8D` |
| `Builds/bm-RC4-base/v0300_…_civilian_01.ee.toc` | 50,643 B, sha256 `444ED479EEBA144F14B46554844E2768734D760054EED54C9FD73BA700AC55AA`, 506 records |
| `Builds/bm-RC4-base/applied.json` | identity step: 0 rows |
| `Builds/bm-RC4-base/snapshots/` | empty for this step (no edit list was applied) |
| `Builds/bm-RC4-base/receipt.json` | the receipt, including the phase-B batch record (§3) |
| `Builds/bm-RC4-base/install.ps1` | generated, **never run**: `Install` / `Verify` / `Rollback091` / `Status` |
| `Builds/bm-RC4-base/verify/` | the packer's verify output |

The packer reported `0 module(s), 0 edit(s)` and its own gates: pack/unpack round-trip PASS (5
top-level entries), only-edited-modules-differ PASS (0 changed), every internal `.toc` record
matches the `.ee` PASS (479 internal of 506), `.toc` record list identical to base PASS (506).

## 2. The identity control, re-run

Recorded in the receipt and re-derived by `--check` (which reads the files, not the receipt):

```
identity.ee_identical_to_base : true
identity.toc_identical_to_base: true
base_ee_sha256  : 6AB8275F566A354298C943F3CE3D747086C1B0E832091805EC9E5D70DEAFCF8D
base_toc_sha256 : 444ED479EEBA144F14B46554844E2768734D760054EED54C9FD73BA700AC55AA
```

Independent of the receipt, by direct hash of both builds:

```
.ee  == Builds/test-091 : True
.toc == Builds/test-091 : True
```

`bm_build.py --tag bm-RC4-base --check` → exit 0, every line PASS, ending
`PASS: Builds/bm-RC4-base re-read against its receipt (6AB8275F566A3542…, 506 .toc records)`.
The checked assertions: `.ee`/`.toc` size and sha256 against the receipt, the identity verdict
against both the pinned base hashes and `Builds/test-091` on disk, the source-tree digest
re-measured (590 files / 22,011,703 B / `561D301D0499EE7B…`), R9 model budget 4,657.6 KB of 4,915 KB,
R9 texture budget 5,855.8 KB of 7,065 KB, `replaced` and `textures` measured (0 body, 0 wheel,
0 changed), `installed: false` in both the receipt and the `bm` block, the four installer actions,
the `.toc` record count, and the four batch assertions in §3.

## 3. The receipt now carries the phase-B batch list

`B-01` alone would leave the scaffold un-auditable: a later step could apply a payload and never
prove it belonged to a batch. `bm_build.py` gained `--batches`, which freezes the generated sheet
into `receipt.json` under `bm.batches`:

- `sheet`: `Working/Translation/build_batches.json`, sha256 `CD1F18623B3167F0…` (the generated
  sheet that `t23_closeout.py --write` produces, so the record cannot drift from the prose by hand);
- `ledger`: `Working/Translation/T_ROWS.jsonl`, 199 rows, with its own sha256;
- `steps`: all **24** §8 steps, each with the `serves` codes, the edit files it applies with their
  row counts, the summed value count, or the declared no-payload reason — 17 payloads + 2 records
  over 24 steps, matching the T-23 close-out (B-01, B-14 and the eight unbuilt gates carry their
  reasons: B-17…B-20 the gates declared this week, B-21…B-23, B-25, B-26);
- `consumed`: `[]`, the list later steps append to;
- `how_to_consume`: a later step appends its step id here, and `bm_build.py --check` then fails if
  that id is not a recorded step, is consumed twice, or if its edit files are not among the build's
  own `edit_steps`.

The recorded list, by step (value counts): B-01 0 · B-02 187 (`T8_PARTS.json` 15,
`appearance_plan.json` 172) · B-03 200 · B-04 43 · B-05 125 · B-06 3 · B-07 34
(`t14_lights.json` 28 + `t14_lights_keepaudit.json` 6) · B-08 17 · B-09 15 (`t10_damage_edits.json`
9 + `t10_damage_keepaudit.json` 6) · B-10 7 (`t16_collision.json` 3 + `t16_collision_keepaudit.json`
4) · B-11 60 (`t12_audio_keepaudit.json` 7 + `t12_audio_map.json` 53) · B-12 15 · B-13 19 · B-14 0 ·
B-17…B-23 0 (declared gates) · B-24 15 (`t1_handling.json`) · B-25 0 · B-26 0.

Four `--check` assertions now cover it, all PASS on this build:
`recorded batch steps match the sheet (24 recorded of 24)`, `no batch consumed twice (consumed none)`,
`consumed ids are recorded steps`, `each consumed batch's edits were applied here (0 consumed)`.
The comparison is structural, not a hash of the sheet: regenerating `BUILD_BATCHES.md` with the same
steps keeps the check green, while a changed step list fails and forces a re-record.

## 4. Checks run

| check | result |
|---|---|
| `bm_build.py --tag bm-RC4-base --base test-091 --batches` | exit 0, 10/10 built-in checks PASS |
| `bm_build.py --tag bm-RC4-base --check` | exit 0, all lines PASS, `PASS: … re-read against its receipt` |
| `.ee` / `.toc` hash equality against `Builds/test-091` (independent of the receipt) | both `True` |

Not run, deliberately: `t_boost_rows.py` and `t_vnf_six.py` (both still fail on a hard-coded
198-row pin against the 199-row ledger; per review 8299 they are not a gate), and anything that
needs a game launch.

## 5. No game launch, nothing installed

`bm_build.py` only copies, packs, measures and writes; it never executes `install.ps1` (R6). The
receipt records `installed: false` both at the top level and inside `bm`, and `--check` asserts it.
`install.ps1` exists for a later operator to run by hand; its `Rollback091` action delegates to
`Builds/test-091/install.ps1`, which is itself an install and has never been exercised either. No
game process was started, the game folder was not written, and no `verify_install.py` run was made.

## 6. Files changed, and how to revert

| file | change | why this file | revert |
|---|---|---|---|
| `Tools/scripts/bm_build.py` | `--batches` flag + `batches_record()` + four `--check` assertions | it is the `B-01` scaffold tool; the receipt it writes is the only place a later step's batch claim can be checked | `git checkout -- Tools/scripts/bm_build.py` |
| `Builds/bm-RC4-base/` | new build tree + receipt + installer | the requested step output | delete the directory (`rm -rf Builds/bm-RC4-base`) |

No ledger row, batch card or payload was edited by this step. `Builds/test-091` is byte-for-byte
what it was: the new tree is a copy, and `--check` re-measures the base on disk to prove the copy
still matches it.
