# DONE — G3-11 provenance dimension (LEDGER-provenance)

**STATUS: done.** Every one of the 85 TRANSLATED rows in `LEDGER_AUDIT.md` is now joined to the
file it actually rests on, that file's `receipt.aaf.list[]` entry, its `owner_card`, and a
byte-level test against the earlier builds on disk. 49 rows rest on a file bm-RC1 wrote,
**36 must be downgraded** (35 inherited, 1 vanilla). Two corrections to the review's premise are
recorded below: the downgrade set is 36, not 35 (the lights row was missed by the review's
`base`-string test), and 5 rows the review counted as inherited are actually edited by this build
— the receipt's `owner_card` for that file omits the card that wrote it.

Nothing was edited except two new files. `T_ROWS.jsonl`, `Builds/bm-RC1/receipt.json`,
`LEDGER_AUDIT.md`/`.json` and `LEDGER_AUDIT2.md`/`.json` are byte-untouched (git status empty for
all six; mtimes 2026-10-31 / 11-02 / 11-03, all before this task).

## Files written

| file | what |
|---|---|
| `Tools/scripts/ledger_provenance.py` | new script, `--write` / `--check`; reads the ledger, the receipt and the earlier builds, writes one md |
| `Working/Translation/LEDGER_PROVENANCE.md` | 30,940 B — count table, per-file table, all 85 rows, the 36-row downgrade list, reconciliation with the review's 35 |
| `tmp/freebuff/reports/LEDGER-provenance.md` | this report |

## Result

Count table, as generated (`LEDGER_PROVENANCE.md`, "Counts"):

| provenance of the cited file | rows | tiers | status to record |
|---|---|---|---|
| edited by this build | 49 | string 44, value 5 | TRANSLATED (unchanged) |
| inherited | 35 | value 35 | CARRIED (value is the earlier build's) |
| vanilla | 1 | value 1 | NOT TRANSLATED (vanilla bytes) |
| **total TRANSLATED** | **85** | | |

Downgrade set = **36 rows**: 35 inherited + `T-DM1` (vanilla).

### Cited files (17 distinct, 85 rows)

| cited file | rows | owner_card | provenance | bytes vs earlier builds (decoded) |
|---|---|---|---|---|
| `…/v0300…_debug.epe` | 44 | `B-06+B-07+B-08+B-16+T-13R+B-18+B-13b` | edited | differs from every earlier copy |
| `…/batmobile/sportsmuscle_vehicle_parts.vmodc` | 5 | `B-02/B-03/B-04+B-04L+B-18` | edited | 46,300 B vs 39,278 / 29,886 B |
| `…/land_steering.vmodc` | 7 | `base (bm-005 lineage)+B-18` | inherited | same as bm-013b |
| `…/land_global.vmodc` | 5 | `base (bm-005 lineage)+B-18` | inherited | same as bm-013b |
| `…/custom_land_global.vmodc` | 5 | `base (bm-005 lineage)+B-18` | inherited | same as bm-013b |
| `…/rigid_body.vmodc` | 4 | `base (bm-005 lineage)+B-18` | inherited | same as bm-013b |
| `…/brakes.vmodc` | 2 | `base (bm-005 lineage)+B-18` | inherited | same as bm-013b |
| `…/land_aerodynamics.vmodc` | 2 | `base (bm-005 lineage)+B-18` | inherited | same as bm-013b |
| `…/land_engine.vmodc`, `…/transmission.vmodc`, `…/palette.vmodc`, `…/land_audio.vmodc` | 1 each | `base (bm-005 lineage)+B-18` | inherited | same as bm-013b |
| `…/generated/batmobile/…_lights.vmodc` | 1 (`T-LG6`) | `B-07+B-18` | inherited | same as **bm-007** |
| `…/00_shared/modules/vehicle_common.vmodc` | 2 | `base (bm-005 lineage)` | inherited | same as bm-013b |
| `…/sportsmuscle_vehicle_deform.vmodc` | 1 | `base (bm-005 lineage)` | inherited | same as bm-013b |
| `…/generated/…_effect_attachments.vmodc`, `…_water_interaction.vmodc` | 1 each | `base (bm-005 lineage)` | inherited | same as bm-013b |
| `…/00_shared/modules/health/lave_health_medium.vmodc` | 1 (`T-DM1`) | `B-18 (vanilla bytes)` | **vanilla** | in `b18.reverted_to_vanilla`; differs from every earlier copy |

### The 36 rows whose status must be downgraded

Inherited (35): `T-G1 T-G2 T-M1 T-M3 T-M4 T-R1 T-ST1 T-ST2 T-ST3 T-ST4 T-ST5 T-ST6 T-E2 T-E4
T-B1 T-B2 T-A3 T-A4 T-K3 T-MA7 T-PA2 T-LG6 T-AU4 T-FX1 T-G6 T-ST7 T-K4 T-DR1 T-EF1 T-WP11
T-WLD12 T-WLD13 T-WLD14 T-WLD16 T-MD1`.
Vanilla (1): `T-DM1` — `max_health = 700` on `lave_health_medium.vmodc`, which B-18 reverted to
vanilla bytes. Its TRANSLATED verdict must become NOT TRANSLATED, not merely CARRIED.

Rows that keep TRANSLATED (49): the 44 `.epe` string rows and the 5 parts rows.

### Where this differs from review-G3-11

- **Review's 35 = 34 + 1 vanilla.** My owner-card-only pass finds **41** rows naming no writer
  card: those 34, the vanilla row, **5 parts rows** and **1 lights row** whose `owner_card` names
  earlier-build ids without the word `base`.
- **The 5 parts rows are raised, not downgraded.** `sportsmuscle_vehicle_parts.vmodc` is
  `B-02/B-03/B-04+B-04L+B-18`; B-04L's own step says `ported: False` (no bytes written) and B-18
  only moved it. But the built file is **46,300 B** while every earlier build's copy is
  **39,278 B** (bm-005…bm-013b) or **29,886 B** (bm-001/bm-004), and B-04R's step records 61
  re-parted parts with two door parts deleted. So a card of this build wrote that file and the
  receipt's `owner_card` does not say so. Verdict: **edited by this build** (on the bytes), and the
  receipt has a provenance gap of its own.
- **The lights row is downgraded.** `T-LG6` cites the lights module, byte-identical to **bm-007**'s
  copy (`d4e6610b0ea33a77…`, 5,745 B) and different from bm-013b's (6,337 B,
  `a7d5c520149cc29a…`): it is a copy from an earlier build, made in this build, not an edit.
- Net: 35 (review) + 1 lights = **36**, with the 5 parts rows removed from the inherited side
  because the bytes prove an edit.

### Caveat carried into the md

The verdict is about the **file**, not the value. The `.epe` was edited by this build (B-16, T-13R,
B-13b), yet LEDGER_AUDIT2 shows those string hits are donor graph names — editing the container
does not make the token a translation. Conversely an inherited file may hold a value an earlier
build wrote. The md states this in the Method section rather than letting "edited" imply "written".

## Commands run and their output

### 1. Inventory of the inputs

```
$ ls -l Working/Translation/ Builds/bm-RC1/receipt.json
-rw-r--r-- 1 User 197121  168243 Nov  3 02:03 Working/Translation/LEDGER_AUDIT.json
-rw-r--r-- 1 User 197121   50824 Nov  3 02:03 Working/Translation/LEDGER_AUDIT.md
-rw-r--r-- 1 User 197121  148703 Nov  3 02:44 Working/Translation/LEDGER_AUDIT2.json
-rw-r--r-- 1 User 197121   29495 Nov  3 02:44 Working/Translation/LEDGER_AUDIT2.md
-rw-r--r-- 1 User 197121  133520 Oct 31 08:35 Working/Translation/T_ROWS.jsonl
-rw-r--r-- 1 User 197121  205174 Nov  2 21:48 Builds/bm-RC1/receipt.json

$ … Counter(r.get('status') for r in rows)
rows 198
keys ['cells', 'dispo', 'doc', 'edits', 'id', 'section', 'why']
Counter({None: 198})
```

Decoded: `T_ROWS.jsonl` has **no status field** — the TRANSLATED set exists only in
`LEDGER_AUDIT`. So the new script imports `ledger_audit` and reuses its `build()` for verdicts
rather than inventing a second classifier.

### 2. Receipt shape

```
$ python -c "… receipt['card'], steps, b18 …"
card B-14 tag bm-RC1
steps 17
b18 keys ['card', 'moved', 'reverted_to_vanilla', 'repointed', 'files_xml_rows', 'changed_at_shared_path_after']
b18 reverted count 10
aaf list entries 691
owner_card families over the 691: base (bm-005 lineage) 613, base (bm-005 lineage)+B-18 43,
  B-15 11, B-18 (vanilla bytes) 10, B-15+B-18 5, B-13b 2, B-06 2, B-06+B-13b 1, B-07+B-18 1,
  B-06+B-07+B-08+B-16+T-13R+B-18+B-13b 1, B-10+B-10b+B-10c+B-18 1, B-02/B-03/B-04+B-04L+B-18 1
```

Decoded: 17 build steps, card B-14, ten files reverted by B-18 including
`lave_health_medium.vmodc`. Step texts read for the writer/non-writer split:
`B-04L: {'card': 'B-04L', 'ported': False, 'reason': 'already the live schema', 'hash': '2760276721'}`,
`B-17: SKIPPED (BM_NO_B17=1)`, `B-18: 51 files -> .../batmobile/, 11 referrers repointed, reverted to vanilla [...]`.

### 3. Join prototype (85 rows → aaf entries)

```
$ time uv run --with numpy --with pillow --with pefile --with capstone python -c "import ledger_audit as la; …"
TRANSLATED rows 85
c Counter({'ok': 85})
owner_card families over cited files:
   44 B-06+B-07+B-08+B-16+T-13R+B-18+B-13b
   29 base (bm-005 lineage)+B-18
   5 base (bm-005 lineage)
   5 B-02/B-03/B-04+B-04L+B-18
   1 B-07+B-18
   1 B-18 (vanilla bytes)
misses 0
real    0m28.415s
```

Decoded: the cited path parsed from the audit's evidence string always exists in
`receipt.aaf.list[]` — **85/85 joined, 0 misses**. Derived: the base families total 34, plus the
vanilla row, i.e. the review's 35 is reproducible.

### 4. Per-file grouping

```
$ … group TRANSLATED rows by (owner_card, cited file) …
B-02/B-03/B-04+B-04L+B-18                          M/.../batmobile/sportsmuscle_vehicle_parts.vmodc   5  T-PA3,T-PA4,T-PA5,T-DM5,T-CO3
B-06+B-07+B-08+B-16+T-13R+B-18+B-13b               E/.../v0300_car_kensington_sportsmuscle_debug.epe 44  T-L1,T-L3,…T-WLD11
B-07+B-18                                          E/.../generated/batmobile/…_lights.vmodc           1  T-LG6
B-18 (vanilla bytes)                               E/00_shared/modules/health/lave_health_medium.vmodc 1  T-DM1
base (bm-005 lineage)                              E/00_shared/modules/vehicle_common.vmodc          2  T-EF1,T-WLD14
base (bm-005 lineage)                              …_effect_attachments.vmodc                        1  T-FX1
base (bm-005 lineage)                              …_water_interaction.vmodc                         1  T-WLD13
base (bm-005 lineage)                              M/.../sportsmuscle_vehicle_deform.vmodc           1  T-PA2
base (bm-005 lineage)+B-18                         …_brakes.vmodc                                    2  T-K3,T-K4
base (bm-005 lineage)+B-18                         …_custom_land_global.vmodc                        5  T-B1,T-B2,T-DR1,T-WP11,T-MD1
base (bm-005 lineage)+B-18                         …_land_aerodynamics.vmodc                         2  T-A3,T-A4
base (bm-005 lineage)+B-18                         …_land_audio.vmodc                                1  T-AU4
base (bm-005 lineage)+B-18                         …_land_engine.vmodc                               1  T-E2
base (bm-005 lineage)+B-18                         …_land_global.vmodc                               5  T-G1,T-G2,T-M4,T-R1,T-G6
base (bm-005 lineage)+B-18                         …_land_steering.vmodc                             7  T-ST1…T-ST7
base (bm-005 lineage)+B-18                         …_palette.vmodc                                   1  T-MA7
base (bm-005 lineage)+B-18                         …_rigid_body.vmodc                                4  T-M1,T-M3,T-WLD12,T-WLD16
base (bm-005 lineage)+B-18                         …_transmission.vmodc                              1  T-E4
```

Decoded: 17 distinct cited files cover all 85 rows.

### 5. Byte test against the earlier builds

```
$ python - … sha256/size of bm-RC1 vs bm-013b / bm-007 / bm-005 …
land_global.vmodc      rc1=None bm013b=None          <- my first path guess was wrong (missing the
                                                       v0300_…_ filename prefix); redone by the script
parts rc1=(46300, '6e379e4c5716f15c') bm-013b=(39278, '4fa283fc774f78b1')
parts rc1=(46300, '6e379e4c5716f15c') bm-009=(39278,  '4fa283fc774f78b1')
parts rc1=(46300, '6e379e4c5716f15c') bm-005=(39278,  '4fa283fc774f78b1')
lights rc1=(5745, 'd4e6610b0ea33a77') bm-007=(5745,  'd4e6610b0ea33a77')
lights rc1=(5745, 'd4e6610b0ea33a77') bm-013b=(6337, 'a7d5c520149cc29a')
vehicle_common rc1 (12271, 'b402542d7641d6b7')
  bm-013b (12271, 'b402542d7641d6b7')
  bm-005  (12271, 'b402542d7641d6b7')
```

Decoded: (a) the B-18 move into `batmobile/` does **not** change bytes — `vehicle_common.vmodc`
has the same sha256 in bm-RC1, bm-013b and bm-005, so a hash mismatch means an edit, not a move;
(b) the parts module was rewritten in this build (46,300 B, matches no earlier build);
(c) the lights module is bm-007's copy exactly.

### 6. `--write` and `--check` (final state)

```
$ uv run --with numpy --with pillow --with pefile --with capstone python Tools/scripts/ledger_provenance.py --write
wrote Working\Translation\LEDGER_PROVENANCE.md
provenance: {'edited by this build': 49, 'inherited': 35, 'vanilla': 1, 'UNKNOWN': 0}
downgrade: 36 rows
WRITE_EXIT=0

$ uv run --with numpy --with pillow --with pefile --with capstone python Tools/scripts/ledger_provenance.py --check
OK 85/85 TRANSLATED rows with provenance
provenance: {'edited by this build': 49, 'inherited': 35, 'vanilla': 1, 'UNKNOWN': 0}
downgrade: 36 rows
CHECK_EXIT=0
```

`--check` re-derives the whole document and compares the rendered markdown byte for byte (the
review's I4 criticised `ledger_audit.py --check` for comparing only verdicts; this one does not
repeat that), then asserts 85 TRANSLATED rows, unique ids, counts summing to 85, and that every
cited file exists in the build.

### 7. Protected inputs untouched

```
$ git status --porcelain -- Working/Translation/T_ROWS.jsonl Builds/bm-RC1/receipt.json \
    Working/Translation/LEDGER_AUDIT.md Working/Translation/LEDGER_AUDIT.json \
    Working/Translation/LEDGER_AUDIT2.md Working/Translation/LEDGER_AUDIT2.json
(no output)

$ ls -l --time-style=long-iso …
2026-11-02 21:48  Builds/bm-RC1/receipt.json
2026-11-04 22:20  Tools/scripts/ledger_provenance.py
2026-11-03 02:03  Working/Translation/LEDGER_AUDIT.md
2026-11-03 02:44  Working/Translation/LEDGER_AUDIT2.md
2026-11-04 22:21  Working/Translation/LEDGER_PROVENANCE.md
2026-10-31 08:35  Working/Translation/T_ROWS.jsonl

$ git status --porcelain -- Tools/scripts/ledger_provenance.py Working/Translation/LEDGER_PROVENANCE.md
?? Tools/scripts/ledger_provenance.py
```

Decoded: no modification to any protected file; the only new tracked-path file is the script
(`Working/` is ignored by git, so the generated md does not appear).

## Value labels

- **decoded**: the 85 cited paths and their `receipt.aaf.list[]` entries; every `owner_card` string;
  every sha256 and byte size; the 17 step texts; the ten `b18.reverted_to_vanilla` paths; the
  writer/non-writer split (`B-04L ported: False`, `B-17 SKIPPED`, B-18 move+revert).
- **derived**: the three provenance verdicts per row (rule stated in the md's Method section); the
  counts 49 / 35 / 1; the 36-row downgrade set; the reconciliation arithmetic (41 by owner_card,
  35 by the review's base-string test, 5 parts rows raised, +1 lights row).
- **UNKNOWN**: see below.

## UNKNOWNs

1. **Who wrote an inherited value.** `bm-005`…`bm-013b` are compared by hash only, so "inherited"
   means *bm-RC1 did not change these bytes*, not *no build ever did*. Which card set e.g.
   `t_to_full_steer_s = 0.8` would need those builds' receipts/cards, not this one. The review
   flagged the same limit for itself.
2. **Whether the game reads any of these files.** Every verdict is file-to-file; no runtime
   observation was made and none is available from the build.
3. **Which cell of a comma-shifted row a value came from.** Unchanged from `LEDGER_AUDIT.md`; this
   script inherits the audit's evidence strings instead of re-reading cells.
4. **The parts module's true owner.** The bytes prove this build wrote it, and B-04R's step matches
   its content (61 parts, door parts deleted, 4 reparented), but the receipt's `owner_card` does not
   name B-04R. Why the receipt is incomplete is not recorded anywhere in `Builds/bm-RC1`; fixing it
   would mean editing the receipt, which this task was told not to do.
