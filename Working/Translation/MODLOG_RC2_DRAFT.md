# MODLOG draft - the missing bm-RC2 entry (task 7233)

Not a MODLOG edit: `MODLOG.md` and `GRAB_BACKLOG.md` are read-only for this task. This
file is the block a human can paste into `MODLOG.md`, followed by the labelled evidence.

**Why this file exists** (decoded): `grep -c "bm-RC2" MODLOG.md` = `0`, `grep -c "B-RC2"
MODLOG.md` = `0`, `grep -c "B-RC2" GRAB_BACKLOG.md` = `0`; the backlog's B-14 row
(`GRAB_BACKLOG.md:1667`) still names `Builds/bm-RC1/` only.

Label legend: **decoded** = read from a file (path + value/line), **derived** = rule plus
inputs, **UNKNOWN** = not established, with what was tried.

---

## Ready-to-paste block (house style: `## date · title`, then Intended change / files, Why, Revert, Check)

```markdown
## 2026-11-05 · B-RC2 release candidate `Builds/bm-RC2` (new tag, RC1 bytes) - task 7233
Intended change / files: new tree `Builds/bm-RC2/` (9 drop files, 691 `aaf` files, `.toc` 607
records, `receipt.json` 205,440 B, `install.ps1` 4,614 B) built by the new
`Tools/scripts/bm_rc2.py` (a copy of `bm_rc.py`: `TAG = "bm-RC2"` plus `--tag`/`--physicsc`,
a `b10_input` receipt field and a tag-parameterised manifest), and the new owner map
`Working/RC/bm_rc_manifest_bm-RC2.json`. [decoded: `Builds/bm-RC2/receipt.json`,
`Tools/scripts/bm_rc2.py:53,77-80,410-412,586-596`; the report
`tmp/freebuff/reports/B-RC2.md` §1/§6 records the same file sizes]
Why: B-14's `bm_rc.py` hard-codes `TAG = "bm-RC1"`, so a second release-candidate tag needs a
copy; the tree is the same lineage (base `bm-005`, branches `bm-006/007/008`, B-10
`Working/Collision/batmobile.physicsc` pinned to `192c1247…`, B-11 banks, B-13 drop, leaf
`…_debug`) and **differs from RC1 only in the tag**. [derived: no input `bm_rc2.py` reads
changed between the two builds, so the bytes are equal; confirmed independently by hashing
both trees: 691 files each, 0 sha256 changed, and 9/9 drop files identical - decoded:
`tmp/freebuff/reports/B-RC2.md` §4]
Revert: delete `Builds/bm-RC2/`, `Tools/scripts/bm_rc2.py`, `Working/RC/bm_rc_manifest_bm-RC2.json`
and this entry; `Builds/bm-RC1/` and `Working/RC/bm_rc_manifest.json` are untouched by the card
[decoded: separate paths, RC1 receipt unchanged]. Do **not** revert by
`bm_rc2.py --write --tag bm-RC1` - the script refuses that tag and `--write` starts with
`shutil.rmtree(OUT)` [decoded: `bm_rc2.py:591,589`].
Receipt delta vs RC1 (the only four fields that differ): `card` `"B-14"` -> `"B-RC2"`,
`lineage_card` absent -> `"B-14"`, `b10_input` absent -> `{path, sha256, b10_pin_rc1}`, `tag`
[decoded: direct diff of the two `receipt.json`; `files`, `aaf`, `toc`, `budgets`, `steps`,
`deps`, `b18`, `leaf`, `unknown`, `variants`, `schema`, `replaced_rollback` are equal].
Check: `uv run python Tools/scripts/bm_rc2.py --check` -> `PASS: bm-RC2 0 failure(s), 9 drop
files, 691 tree files, .toc 607 records`, exit 0 (16 PASS lines) [decoded: re-run 2026-11-05,
output in `tmp/freebuff/reports/modlog-rc2-evidence.md`]. One inherited gate is RED and not
fixed by this card: `v03_wiring2.py --tag bm-RC2` G4 audio fails because
`Working/Audio/bm_bank_manifest.json` is stale; the shipped banks are byte-identical to
B-11's [decoded: `B-RC2.md` §3c]. Not run in game (test ban) [UNKNOWN: whether the tree loads].
```

---

## Every statement, labelled

| # | statement | label | evidence |
|---:|---|---|---|
| 1 | MODLOG has no bm-RC2/B-RC2 entry; the backlog has no B-RC2 card | decoded | `grep -c` = `0`, `0`, `0` (this task's brief says the same) |
| 2 | `bm_rc2.py` is a copy of `bm_rc.py` differing in TAG, CLI, receipt field, manifest name | decoded | `B-RC2.md` §1 diff; `bm_rc2.py:53,64,77-80,227,410-412,428,570,586-596` |
| 3 | Inputs: `card` = `"B-RC2"`, `lineage_card` = `"B-14"`, `b10_input {path, sha256, b10_pin_rc1}` | decoded | `bm_rc2.py:410-412`; `receipt.json` |
| 4 | `b10_input.path` = `Working/Collision/batmobile.physicsc`, sha256 `192c12479d81da6e9515b42df2f0e55db555986633c497d7f2013b1f913d0d9e`, pin equal to it | decoded | `bm_rc2.py:66-70`; `receipt.json: b10_input` |
| 5 | Lineage: base `bm-005`, branches `bm-006/007/008`, B-11 `bm-004/banks`, B-13 `bm-013/drop`, leaf `…_debug` | decoded | `bm_rc2.py:73-79`; `receipt.json: deps/steps` |
| 6 | `--physicsc` is opt-in and bypasses the B-10 pin (`ALLOW_ANY_B10`) | decoded | `bm_rc2.py:67,586-587,592-595` |
| 7 | `--tag` refuses `bm-RC1`; `--write` removes the target tree first | decoded | `bm_rc2.py:589-591` |
| 8 | RC2 differs from RC1 only in the tag; 691 tree files, 0 sha256 changed, 9/9 drop files identical, `.toc` 607 both | decoded | `B-RC2.md` §4 (independent hashing of both trees) |
| 9 | The reason is that no consumed input changed between the builds | derived | `B-RC2.md` §2 timestamps + §4 |
| 10 | Receipt differs in exactly `card`, `lineage_card`, `b10_input`, `tag` | decoded | direct diff this task (`SAME`/`DIFF` per key) |
| 11 | Tree built 2026-11-05 02:42-02:43; the card verified it instead of rebuilding | decoded | `B-RC2.md` §0 |
| 12 | `--check` passes 16/16 with exit 0 today | decoded | re-run output below |
| 13 | G4 audio gate is RED because the Working/ manifest is stale, not the banks | decoded | `B-RC2.md` §3c; bank sha256 listed there |
| 14 | Whether the tree loads in game | UNKNOWN | test ban; no runtime check |
| 15 | Why `bm_bank_manifest.json` no longer matches its re-derivation | UNKNOWN | gate names the file, not the field; `B-RC2.md` UNKNOWN 3 |
| 16 | Whether B-10d's hull should replace the shipped B-10/B-10b/B-10c | UNKNOWN | `B-RC2.md` §COMPROMISES 7, UNKNOWN 4 |
| 17 | Whether `--write --tag bm-RC2b` would reproduce these bytes | derived | same inputs, same code path; not run (no new tree was created) |

## Reproduction commands (read-only first)

```text
uv run python Tools/scripts/bm_rc2.py --check
uv run --with numpy --with fsb5 --with scipy python Tools/scripts/v03_wiring2.py --tag bm-RC2   # G4 RED, inherited
```

`--write` is **not** a reproduction command for this tree: it deletes `Builds/<tag>` first and
refuses `bm-RC1`, so a rebuild needs a new tag, e.g.
`uv run python Tools/scripts/bm_rc2.py --write --tag bm-RC2b`. That was not run (it would
create a new build tree; the brief asks for evidence, not a build).

## Note for the human writing the entry

The MODLOG's B-14 entry (if any) describes `bm-RC1`; this block is a separate entry because
RC2 is a separate tree with its own receipt and installer. If you would rather fold it into
B-14, the four receipt deltas (statement 10) are the only facts that must be carried over.
