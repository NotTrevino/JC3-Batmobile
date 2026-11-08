# Independent review — B-01 · Build scaffold

Reviewer: Freebuff (did not write this card). Date: 2026-10-29.
Scope: `GRAB_BACKLOG.md` §0.5 (R1–R14), the B-01 card (§8, line 992), the §12 `B-01` row (1334),
`MODLOG.md` §"B-01 · Build scaffold — done" (14314–14420), and the outputs it names:
`Tools/scripts/bm_build.py`, `Builds/bm-001/` (receipt, `.ee`, `.toc`, `applied.json`,
`install.ps1`), against `Builds/test-091/`.
Read-only: nothing under `Builds/`, `Tools/`, `Research/`, `GRAB_BACKLOG.md`, `MODLOG.md` or the game
install was written; no build run, no install, no game. This report is the only file written.

## VERDICT: **minor issues**

The control is real and the Done is met: `bm-001`'s `.ee` and `.toc` are byte-identical to
test-091's, verified twice (the tool's own `--check` and `sha256sum` on both files), and the
identity build applied 0 rows. What is wrong is around it: the **§12 row names a command that does
not run** (`bm_build.py --check` exits 2 without `--tag`), and the receipt's `budgets` / `replaced`
/ `textures` fields are **empty defaults** that the MODLOG describes as the live build's numbers
(R9 says every build reports both budgets; `bm-001` reports neither).

## Check output (verbatim)

The command in the §12 row, exactly as written:

```
$ python Tools/scripts/bm_build.py --check
usage: bm_build.py [-h] --tag TAG [--base BASE] [--edits EDITS] [--force]
                   [--check]
bm_build.py: error: the following arguments are required: --tag
EXIT=2
```

The command the MODLOG quotes:

```
$ python Tools/scripts/bm_build.py --tag bm-001 --check
PASS: Builds/bm-001 re-read against its receipt (6AB8275F566A3542…, 506 .toc records)
EXIT=0
```

The Done, checked independently of the tool:

```
$ sha256sum Builds/bm-001/*.ee Builds/test-091/*.ee
6ab8275f566a354298c943f3ce3d747086c1b0e832091805ec9e5d70deafcf8d *Builds/bm-001/v0300_car_kensington_sportsmuscle_civilian_01.ee
6ab8275f566a354298c943f3ce3d747086c1b0e832091805ec9e5d70deafcf8d *Builds/test-091/v0300_car_kensington_sportsmuscle_civilian_01.ee
$ sha256sum Builds/bm-001/*.toc Builds/test-091/*.toc
444ed479eeba144f14b46554844e2768734d760054eed54c9fd73ba700ac55aa *Builds/bm-001/…_civilian_01.ee.toc
444ed479eeba144f14b46554844e2768734d760054eed54c9fd73ba700ac55aa *Builds/test-091/…_civilian_01.ee.toc
```

Byte sizes 10,737,057 / 50,643 on both sides. So the card's Done ("`bm-001` `.ee`/`.toc` are
byte-identical to test-091's") holds on disk today.

## Issues

### 1. The §12 evidence command does not run
`GRAB_BACKLOG.md:1334` names `Tools/scripts/bm_build.py --check`. `--tag` is a required argument, so
that exact command exits **2** with an argparse usage error (above). The MODLOG quotes the working
form. A tracker row's evidence command has to be runnable as printed (R11: "tables of counts … come
from a script with `--check`"; R14: command output with paths) — this one is missing its tag.

### 2. R9: the build reports no budgets, and the MODLOG says the base receipt carries them
`Builds/bm-001/receipt.json` has `"budgets": {}`. `t5_build.py:152` fills it with
`base_rec.get("budgets", {})`, and the base receipt is `Builds/test-091/receipt.json`, whose keys are:

```
['tag', 'built', 'base', 'src', 'ee', 'toc', 'candidate', 'files_xml_added', 'checks']
```

— no `budgets` key at all (`d.get("budgets")` → `None`). So `bm-001` reports neither the Model nor
the Texture number, while R9 says "vehicle Model 4,915 KB, Texture 7,065 KB … **Every build reports
both**". MODLOG limit 5 states the opposite: "the Model/Texture budgets (R9) are the ones test-091's
receipt already carries". test-091's receipt carries none; `test-090`'s does
(`{"model_kb": 4764, "model_cap_kb": 4915, "texture_kb": 3954, "texture_cap_kb": 4648}`), so the
budget fields exist in the builder but the tree B-01 was based on was made by the older receipt
path.

### 3. R4: `replaced` / `textures` are defaults presented as the live build's numbers
MODLOG limit 4: "`receipt.replaced` / `receipt.textures` come from the base receipt
(`t5_build.py` carries them forward); they are the live build's numbers, not re-measured by this
step." `t5_build.py:148-149` is `base_rec.get("replaced", {})` and `base_rec.get("textures", 0)`, and
test-091's receipt has neither key, so `bm-001`'s receipt says `"replaced": {}` and `"textures": 0`
**by default**. `textures: 0` is not a measurement of this build — test-090 reported a texture
working set of 3,954 KB — and any later card or audit that reads `receipt.textures` reads zero.
The honest value is UNKNOWN (not carried, not measured); the current one is a default wearing a
number.

### 4. `--check` verifies the Done, not the whole receipt
`check()` (`bm_build.py:279-317`) re-reads: `.ee`/`.toc` size and sha256 against the receipt,
byte-identity against the **base hashes pinned in the receipt** (not against `Builds/test-091` on
disk), `install.ps1` existence and its named actions, and the `.toc` record count via `read_toc`
(506 recomputed, not copied). It does **not** re-read the 590-file source tree digest, does not
assert `installed: false`, and does not look at `budgets`/`replaced`/`textures`. That is enough for
the card's Done (identity), which I confirmed outside the tool; it is not enough to call the
receipt's other fields checked.

### 5. Minor: "Rollback091" is an install of 091
`install.ps1`'s `Rollback091` action calls
`Builds/test-091/install.ps1 -Action Install`. That is a defensible restore, but it means the
rollback path is itself an install action, so "install.ps1 … never run" (MODLOG limit 1) also means
the rollback was never exercised. Worth one line in the limits; not an error.

### 6. Not an issue — verified
- **Done met and checked** (hashes above), including the tool's own identity assertion.
- **0 edit rows**: `applied.json` is `{"source": null, "base": "Builds/bm-001/aaf", "applied": []}`
  and the receipt has `bm.rows_applied: 0`, `bm.edit_steps: []`, `modules_changed: []`, `edits: 0`.
- **7 checks recorded with their details** and all `ok: true` (round-trip 5 top-level entries, 0
  changed modules, 479 internal of 506 records, 506 records identical to base, 590 files copied,
  0 edit steps/rows, `.ee`/`.toc` identical) — the MODLOG's list matches the receipt exactly.
- **Nothing installed**: `receipt.installed: false`; no install receipt in `Builds/bm-001`.
- **Probe build gone**: `Builds/bm-editprobe` does not exist; the fabricated `6000 → 6001` value left
  no trace in `Working/Translation` (the only `6001` hits are a hash, `2763586001`).
- **`bm-001` receipt's hash/byte numbers match test-091's** (`ee.sha256 6AB8275F…CF8D`,
  `toc.sha256 444ED479…5AA`, 10,737,057 / 50,643 B), as the MODLOG says.
- **506 `.toc` records** is recomputed by `--check` from the file and agrees with the receipt.
- **R6 respected on the evidence available**: no `D:/Games` path appears in the build's files, the
  installer was generated and not executed.

## Spot-checks

| value in the doc | where verified | result |
|---|---|---|
| `.ee` **10,737,057 B**, sha256 **6AB8275F…CF8D**, identical to test-091 | `sha256sum` on both files; `receipt.ee` | exact |
| `.toc` **50,643 B**, sha256 **444ED479…5AA**, identical to test-091 | `sha256sum` on both files; `receipt.toc` | exact |
| **506** `.toc` records, **479** of them internal | `--check` recomputes via `read_toc`; `receipt.toc.records = 506`, check detail "479 internal of 506" | agree |
| **590** files / **22,011,703 B** copied, digest `561D301D…` | `receipt.bm.src_tree`; check "tree copied from the base build (590 files)" — receipt-level, not re-hashed by `--check` | agree with the receipt, not re-derived |
| `budgets` reported for R9 | `receipt.budgets = {}`; base receipt has no `budgets` key; `test-090` has one | **missing** (issue 2) |
| `textures` / `replaced` "the live build's numbers" | `receipt.textures = 0`, `replaced = {}`; both are `.get(default)` on a base receipt without the keys | **defaults, not numbers** (issue 3) |

Not verified: the MODLOG's "2/2 tampers caught". `tmp/b01bak/` holds the pre-tamper `receipt.json`
and `.ee`, but re-running the tampers would edit `Builds/bm-001`, which this review may not do; the
`--check` paths those tampers exercise (sha256 mismatch, identity mismatch) are visible in
`check()` and both would fire.
