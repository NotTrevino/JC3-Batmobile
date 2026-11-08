# bm-RC2 MODLOG evidence - DONE report

STATUS: done. The evidence a human needs is collected in
`Working/Translation/MODLOG_RC2_DRAFT.md` as a paste-ready MODLOG block plus a
per-statement label table. `MODLOG.md` and `GRAB_BACKLOG.md` were not edited. The card's
own check was re-run today and passes (16/16, exit 0). The decisive facts:

* `bm_rc2.py` is `bm_rc.py` with `TAG = "bm-RC2"`, a `--tag`/`--physicsc` CLI, a
  `b10_input` receipt field and a tag-parameterised manifest filename.
* Its receipt records `card: "B-RC2"`, `lineage_card: "B-14"`, and
  `b10_input {path: "Working/Collision/batmobile.physicsc", sha256: 192c1247…,
  b10_pin_rc1: 192c1247…}`.
* RC2 differs from RC1 in **nothing but the tag**: 691 tree files with 0 sha256 changed,
  9/9 drop files identical, `.toc` 607 records in both (per `B-RC2.md` §4, independently
  hashed there).
* The two receipts differ in **exactly four fields**: `card`, `lineage_card`, `b10_input`,
  `tag` - every other key is equal.
* Reproduction is `uv run python Tools/scripts/bm_rc2.py --check`; `--write` is not a
  reproduction command for this tree (it `rmtree`s the target and refuses `bm-RC1`), so a
  rebuild would need a new tag.

## Files written

| file | what |
|---|---|
| `Working/Translation/MODLOG_RC2_DRAFT.md` | the ready-to-paste MODLOG block (intended change / files, why, revert, check), then a 17-row table labelling every statement decoded/derived/UNKNOWN, the reproduction commands, and a note on folding it into B-14 |
| `tmp/freebuff/reports/modlog-rc2-evidence.md` | this report |

Nothing else was written. `MODLOG.md`, `GRAB_BACKLOG.md`, `Builds/bm-RC1`, `Builds/bm-RC2`
and the ledger were **not edited by this task**. Note for the record: `git status` does show
`MODLOG.md` and `GRAB_BACKLOG.md` modified relative to `HEAD`, but that predates this task
(both were already listed as changed when the session started) and neither contains a
`bm-RC2`/`B-RC2` mention (`grep -c` = 0 for both), so the missing entry is still missing.

## What `bm_rc2.py` does and which inputs it takes

| item | value | label | source |
|---|---|---|---|
| script | copy of `bm_rc.py`; `TAG = "bm-RC2"` (CLI overrides), `--tag`, `--physicsc`, `ALLOW_ANY_B10`, `rel_b10()`, manifest written to `Working/RC/bm_rc_manifest_<TAG>.json` | decoded | `bm_rc2.py:53,64,77-80,586-596`; `B-RC2.md` §1 diff |
| receipt `card` | `"B-RC2"` | decoded | `bm_rc2.py:410`; `Builds/bm-RC2/receipt.json` |
| receipt `lineage_card` | `"B-14"` | decoded | same |
| receipt `b10_input` | `{"path": "Working/Collision/batmobile.physicsc", "sha256": "192c12479d81da6e9515b42df2f0e55db555986633c497d7f2013b1f913d0d9e", "b10_pin_rc1": "192c1247…0d9e"}` - path, actual sha256, and the RC1 pin it is compared with | decoded | `bm_rc2.py:66-70,410-412`; receipt |
| other inputs | base `bm-005`; branches `bm-006`/`bm-007`/`bm-008` (B-06/07/08); B-11 banks `Builds/bm-004/banks`; B-13 drop `Builds/bm-013/drop`; merge base `Working/RC/base_bm005_prerework.epe`; leaf `…_debug` | decoded | `bm_rc2.py:73-79`; receipt `deps`/`steps` |
| opt-in input | `--physicsc FILE` lets a file whose sha256 is not the B-10 pin be used (built for B-10d); the 02:42 build did not pass it | decoded | `bm_rc2.py:67,592-595`; `B-RC2.md` §2 |
| guard rails | `--tag bm-RC1` is refused; `--write` begins with `shutil.rmtree(OUT)` | decoded | `bm_rc2.py:589-591` |

## What `B-RC2.md` says changed relative to bm-RC1

Decoded from `tmp/freebuff/reports/B-RC2.md`:

* §0: the tree already existed (built 2026-11-05 02:42-02:43); the card verified it rather
  than rebuilding, because `--write` would delete an existing `Builds/bm-*` tree.
* §1: `bm_rc2.py` differs from `bm_rc.py` only in TAG, the CLI, the receipt's `b10_input`
  record, a tag-parameterised manifest name, and the `ALLOW_ANY_B10` opt-in.
* §4: "RC2 = RC1 with a new tag" - 9 drop files with 9/9 identical sha256, 691 `aaf` files
  with 0 changed/added/removed, `.toc` 607 records both, non-vanilla budget 4,791.3 KB both.
* §2: no input `bm_rc2.py` reads changed between the RC1 build (2026-11-02 21:48) and the
  RC2 build (2026-11-05 02:42), which is why the bytes are equal.

## Receipt fields that differ (re-derived in this task)

Direct key-by-key comparison of `Builds/bm-RC1/receipt.json` and
`Builds/bm-RC2/receipt.json`:

| key | RC1 | RC2 |
|---|---|---|
| `card` | `"B-14"` | `"B-RC2"` |
| `lineage_card` | absent | `"B-14"` |
| `b10_input` | absent | `{path, sha256, b10_pin_rc1}` |
| `tag` | `"bm-RC1"` | `"bm-RC2"` |

Equal keys: `schema`, `variants`, `deps` (13), `steps` (17), `b18`, `leaf`, `files` (9),
`aaf` (dict), `toc`, `budgets`, `budgets_note`, `replaced_rollback`, `unknown` (3).

## Commands, verbatim

```text
$ grep -c "bm-RC2" MODLOG.md
0
$ grep -c "B-RC2" MODLOG.md
0
$ grep -c "B-RC2" GRAB_BACKLOG.md
0
```

```text
$ uv run python Tools/scripts/bm_rc2.py --check
PASS receipt lists every drop file: 9 = 9 on disk
PASS rehashed 9/9 ok
PASS aaf source tree: 691 files, every sha256 matches
PASS .toc: 607 records, every non-zero record matches the .ee (705 entries)
PASS .toc ends with the root .epe (v0300_car_kensington_sportsmuscle_debug.epe)
PASS R8: no offset-0 record carries bytes that differ from the vanilla .ee (19 size-only shared references excluded)
PASS internal (real offset) land_global.vmodc: [16773152, 16788160]
PASS internal (real offset) land_engine.vmodc: [16804280]
PASS internal (real offset) vehicle_parts.vmodc: [16625280]
PASS internal (real offset) health_medium.vmodc: [16769408, 23472352]
PASS internal records point into the .ee: 0 ()
PASS -WhatIf lists exactly the receipt's 9 files + sha256, wrote 0 files
PASS rehearsal (a) clean dropzone: Install -> Verify verified 9/9
PASS rehearsal (a) Rollback091 removed every added file (0 left)
PASS rehearsal (b) decoy dropzone: Install backed up the existing item.onlinec
PASS rehearsal (b) Rollback091 restored the decoy byte-for-byte and removed the rest
PASS: bm-RC2 0 failure(s), 9 drop files, 691 tree files, .toc 607 records
CHECK_EXIT=0
```

```text
$ python -c "compare Builds/bm-RC1/receipt.json with Builds/bm-RC2/receipt.json"
SAME aaf dict 3
DIFF b10_input
  rc1: null
  rc2: {"path": "Working/Collision/batmobile.physicsc", "sha256": "192c12479d81da6e9515b42df2f0e55db555986633c497d7f2013b1f913d0d9e", "b10_pin_rc1": "192c12479d81da6e9515b42df2f0e55db555986633c497d7f2013b1f913d0d9e"}
SAME b18 dict 6
SAME budgets dict 3
SAME budgets_note str 105
DIFF card
  rc1: "B-14"
  rc2: "B-RC2"
SAME deps list 13
SAME files list 9
SAME leaf str 39
DIFF lineage_card
  rc1: null
  rc2: "B-14"
SAME replaced_rollback str 144
SAME schema int 2
SAME steps list 17
DIFF tag
  rc1: "bm-RC1"
  rc2: "bm-RC2"
SAME toc dict 5
SAME unknown list 3
SAME variants str 31
```

Reproduction of the *tree* (not run here; would create a new build tree):

```text
uv run python Tools/scripts/bm_rc2.py --write --tag <new-tag>
```

`--write --tag bm-RC2` itself is not safe on this repo: `--write` deletes the target tree
first, and RC2 already exists.

## UNKNOWNs

* **Whether the tree loads in game** - test ban; no runtime check exists; `B-RC2.md`
  UNKNOWN 1.
* **Why `Working/Audio/bm_bank_manifest.json` is stale** - the G4 gate names the file, not
  the differing field; fixing it is B-11/T-12's deliverable (`B-RC2.md` UNKNOWN 3). The
  shipped banks themselves are byte-identical to B-11's (decoded there).
* **Whether B-10d's re-derived hull should replace the shipped B-10/B-10b/B-10c** - a build
  decision, not taken by the card (`B-RC2.md` COMPROMISES 7, UNKNOWN 4).
* **Whether `--write --tag <new>` would reproduce the same bytes** - derived from identical
  inputs and code, but not run (no build was requested and none was created).
* **Whether MODLOG should carry this as its own entry or fold it into B-14** - an editorial
  choice left to the human; the draft states the four required deltas either way.

## COMPROMISES

None. Read-only evidence gathering; the draft is a proposal for a human edit, and neither
`MODLOG.md` nor `GRAB_BACKLOG.md` was modified.
