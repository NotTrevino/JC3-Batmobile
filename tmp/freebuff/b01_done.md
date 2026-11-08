## B-01 · Build scaffold — done (2026-10-29)

**Why this section exists after the deferred one above.** The deferred block records the state at the
start of this session (`T-23 | todo`). The concurrent T-23 session closed gate TX during it: §12 now
reads `| T-23 | done | … t23_closeout.py --check (gate TX: 75/75 §1 codes mapped …) …|`,
`Working/Translation/BUILD_BATCHES.md` + `build_batches.json` are on disk, and its `T-23 done` block is
in this log. The item's prerequisite is therefore met and B-01 was run — the deferred block stands as
the record of what was seen first, this one supersedes its status. Re-reading §12 before every write
is what caught it; no decision in §11 was open either (D-1…D-10 all `resolved`).

**Delivered.** `Tools/scripts/bm_build.py` (the scaffold) and `Builds/bm-001/` (the identity control):

```
Builds/bm-001/aaf       590 files, 22,011,703 B, digest 561D301D0499EE7B8D2B4A1960C1850E43B50BAE30F7FA0D61944EAE20DA0076
Builds/bm-001/applied.json   {"applied": []}  (0 rows: identity build)
Builds/bm-001/snapshots/     per-step *_current.json snapshots (empty for an identity build)
Builds/bm-001/v0300_…_civilian_01.ee        10,737,057 B  6AB8275F566A354298C943F3CE3D747086C1B0E832091805EC9E5D70DEAFCF8D
Builds/bm-001/v0300_…_civilian_01.ee.toc        50,643 B  444ED479EEBA144F14B46554844E2768734D760054EED54C9FD73BA700AC55AA
Builds/bm-001/receipt.json   pack checks + bm{card,tag,base,src_tree,edit_steps,rows_applied,identity,installer_actions}
Builds/bm-001/install.ps1    Install / Verify / Rollback091 / Status — generated, **never run**
Builds/bm-001/verify/        SmallUnpack read-back of the built .ee (aafdiff's input)
```

**What the scaffold does, in the card's four steps.** (1) `--base Builds/test-091` → copies
`Builds/test-091/aaf` into `Builds/bm-0NN/aaf` (refuses an existing tag without `--force`) and hashes
the tree. (2) applies `--edits` spec files **in the order given**, each with its own
`snapshots/NN_<name>_current.json`; `t1_apply.py` steps only validate, `t5_apply.py` steps edit the
tree in place and write their own applied list — both are the existing appliers, not new ones.
(3) packs with `t5_build.py` (SmallPack → SmallUnpack → `aafdiff` vs the base's own `verify/` →
`.toc` rebuilt and every internal record checked → receipts), so the "one card = one build step = one
aafdiff whose changed list is exactly the card's files" rule is enforced by the packer it already had.
(4) writes `receipt.json` (the packer's, plus a `bm` block and the scaffold's checks) and
`install.ps1`. Nothing is installed, nothing under `D:/Games` is touched, no game is launched (R6).

**Done check (verbatim).**

```
$ python Tools/scripts/bm_build.py --tag bm-001
copy Builds/test-091/aaf -> Builds/bm-001/aaf
  590 files, 22011703 B, digest 561D301D0499EE7B…
 no edit steps: identity build (applied.json has 0 rows)
pack (t5_build.py) ...
   toc ...
   bm-001: 10737057 B .ee, 506 .toc records, 0 module(s), 0 edit(s)
bm-001: .ee 10737057 B 6AB8275F566A3542…, .toc 50643 B, 506 records, 0 edit step(s)
  pack/unpack round-trip                               PASS  (5 top-level entries)
  only edited modules differ                           PASS  (0 changed)
  every internal .toc record matches the .ee           PASS  (479 internal of 506)
  toc record list identical to base                    PASS  (506 records)
  tree copied from the base build                      PASS  (590 files)
  no edit step outside the named list                  PASS  (0 step(s), 0 rows)
  bm-001 .ee/.toc byte-identical to test-091           PASS  (both identical)

$ python Tools/scripts/bm_build.py --tag bm-001 --check
PASS: Builds/bm-001 re-read against its receipt (6AB8275F566A3542…, 506 .toc records)
exit=0
```

test-091's own receipt says `ee.sha256 6AB8275F…CF8D`, `toc.sha256 444ED479…5AA`, `bytes 10,737,057 /
50,643` — the same four numbers, so the scaffold reproduces the live build byte for byte.

**Positive control (the applier path, then deleted).** `bm-001` applies no edit by design, so the
edit half was proved on a throwaway tag: a probe spec with one `t5_apply` step whose single row was
`RigidBody.mass 6000 → 6001` (**a fabricated value, mechanism control only, build deleted and never
installed** — no row and no provenance claim). Result: `FILE …_rigid_body.vmodc: 1 edit(s)`,
`.ee 10,737,058 B 36E10AA9…` (+1 byte), `only edited modules differ PASS (1 changed)` — exactly the
module the edit named — and `--check` PASS. `Builds/bm-editprobe/` was then deleted. The same path
also **refuses drift**: replaying the already-applied `Working/Translation/t5c_edits.json` stops with
`T-K2: front.min_time_to_block holds '1' (float), list expects 5`, and `t1_edits.json` stops on 14
values later batches already changed. A build step can therefore only apply a list written for the
tree it starts from.

**Tamper tests (2/2 caught, both reverted and re-checked to PASS).**

| tamper | result |
|---|---|
| one byte of `Builds/bm-001/…_civilian_01.ee` flipped (byte 1000) | `--check` exit 1: `FAIL .ee: sha256 differs from the receipt` + `FAIL bm-001 is no longer byte-identical to its base (ee False, toc True)` |
| `Builds/bm-001/receipt.json` `ee.sha256` zeroed | `--check` exit 1: `FAIL .ee: sha256 differs from the receipt` (the receipt is not trusted over the bytes) |

**UNKNOWNs and limits.**

1. **`-Action Install` / `-Action Verify` were never run** (R6: no install before phase V/Q, and
   `verify_install.py` reads the dropzone). The installer is generated and its actions are checked to
   exist, not exercised.
2. **The `.toc` is rebuilt, not created**: `t5_build.py` passes the base build's own `.toc` to
   `eetoc.py patch`, so B-01 proves the *identity* path; a step that adds or removes a member is
   covered by the packer's "record list identical to base" refusal, which no phase-B card needs yet.
3. **Pack determinism is proven for this tree only** (`test-091/aaf` → the same `.ee`). Whether
   SmallPack orders identically for a tree with newly added files is untested here; B-04/B-06 add
   files and will show it.
4. **`receipt.replaced` / `receipt.textures` come from the base receipt** (`t5_build.py` carries them
   forward); they are the live build's numbers, not re-measured by this step.
5. **No budget line of its own**: an identity build adds no bytes, and its `.ee` is the base's
   (10,737,057 B); the Model/Texture budgets (R9) are the ones test-091's receipt already carries.
6. The scope of this card is the scaffold, not a stage: it does not render, does not verify in the
   engine and does not decide any value.

**Revert:** `rm -rf Builds/bm-001`; delete `Tools/scripts/bm_build.py`; delete this section (and, if
the whole session is reverted, the B-03 sections and the deferred B-01 block); remove the B-01 row
from §12. No game file, build, save or dropzone was modified, nothing was installed, and nothing was
committed.
