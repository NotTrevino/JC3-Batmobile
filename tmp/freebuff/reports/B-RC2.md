# B-RC2 - offline release candidate `Builds/bm-RC2`

STATUS: done, with one gate failure reported and not hidden. The tree exists, is byte-verified, was
built by the required tag-parameterised copy of `bm_rc.py`, and differs from RC1 in **nothing but the
tag**. `v03_wiring2.py` fails one gate (G4 audio) because `Working/Audio/bm_bank_manifest.json` is
stale; the shipped banks themselves are unchanged and match B-11's.

## 0. Two facts to read first

1. **`Builds/bm-RC2` already existed when I started** (built 2026-11-05 02:42-02:43 by an earlier run
   of this same card). I did **not** rebuild it: `bm_rc2.py --write` starts with
   `shutil.rmtree(OUT)`, which would delete and recreate an existing `Builds/bm-*` tree - the one
   thing the operator brief still forbids. Instead I verified it, ran the three requested checks
   against it, and compared it to RC1. Every input `bm_rc2.py` reads is older than 02:42 (table in
   §2), so a rebuild would reproduce the same bytes - which the RC1 == RC2 equality in §4 confirms
   independently.
2. **`bm_rc.py` hard-codes `TAG = "bm-RC1"`**, so the copy was made as instructed: `bm_rc2.py`,
   diffed against the original (§1). It is not a rewrite; the diff is TAG + a `--tag`/`--physicsc`
   CLI + the receipt's `b10_input` record + a tag-parameterised manifest filename.

## 1. `bm_rc2.py` vs `bm_rc.py` (full diff of the decisions)

```
$ diff Tools/scripts/bm_rc.py Tools/scripts/bm_rc2.py
53c53
< TAG = "bm-RC1"
---
> TAG = "bm-RC2"     # CLI --tag overrides (B-RC2: new tree, same lineage)
63a64
> ALLOW_ANY_B10 = False   # --physicsc names a file whose sha256 is not B-10's pin (B-RC2: B-10d)
75a77,80
> def rel_b10() -> str: ...
222c227
<     elif sha(B10) != B10_SHA:
---
>     elif sha(B10) != B10_SHA and not ALLOW_ANY_B10:
405c410,412   receipt: card "B-RC2", lineage_card "B-14", b10_input {path, sha256, b10_pin_rc1}
421c428       manifest written to Working/RC/bm_rc_manifest_bm-RC2.json (RC1's stays untouched)
563c570       decoy rehearsal asserts ".<TAG>-backup"
578a586,596   --tag (default bm-RC2; refuses bm-RC1) and --physicsc (B-10d input, off by default)
```

The lineage is unchanged: base `bm-005`, branches `bm-006/007/008`, B-10 from
`Working/Collision/batmobile.physicsc` (sha256 pinned to `192c1247…`), B-11 banks from `bm-004`,
B-13 drop from `bm-013`, leaf `v0300_car_kensington_sportsmuscle_debug`.

## 2. Inputs found when I started (timestamps, local time)

| input | timestamp | consumed by this build? |
|---|---|---|
| `Builds/bm-005/aaf` (base) | 2026-10-31 06:16 | yes |
| `Builds/bm-006/aaf` (B-06) | 2026-10-31 07:48 | yes |
| `Builds/bm-007/aaf` (B-07) | 2026-10-31 04:33 | yes |
| `Builds/bm-008/aaf` (B-08) | 2026-10-31 04:27 | yes |
| `Builds/bm-004/banks` (B-11) | 2026-10-31 15:05 | yes |
| `Builds/bm-013/drop` (B-13) | 2026-11-02 01:08 | yes |
| `Working/Collision/batmobile.physicsc` (B-10) | **2026-10-31 00:25** | yes (pinned sha256) |
| `Working/RC/base_bm005_prerework.epe` | 2026-10-31 10:40 | yes (3-way merge base) |
| `Working/Collision2/batmobile.physicsc` (B-10d) | **2026-11-05 02:25** | **no** - only via `--physicsc`, which the 02:42 build did not pass |
| `Working/Collision2/bm_vehicle_hull.json` (B-10d) | 2026-11-05 05:25 | no |
| `Working/Effects/bm_fx_edits.json` (B-08) | 2026-10-31 04:27 | via bm-008 |
| `Working/Audio/bm_bank_manifest.json` | 2026-11-02 22:23 | no (a gate reads it) |
| `Working/Translation/LEDGER_G3E.md` | 2026-11-05 02:37 | no |
| `Working/Translation/COMPROMISES_T.md` | 2026-11-05 08:01 | no |
| today's T-card outputs (`T_AU3B` 09:13, `T_FX3B` 09:22, `T_S6B` 09:30, `T_ST7B` 08:20, `T_MD14B` 08:13, `T_WLD4B` 08:14) | 2026-11-05 | **no** - none of them is read by `bm_rc2.py` |
| `tmp/freebuff/reports/AUDIT-B.md` (09:09), `B-10d.md` | 2026-11-05 | no (AUDIT-B is analysis; B-10d is the `Working/Collision2` pair above) |

So the build consumed every input as of 02:42 and nothing that arrived later; the two later *build*
inputs are B-10d's `Working/Collision2/*`, and shipping them is a build decision this card did not
take (see COMPROMISES, item 7).

## 3. The three requested checks on the new tree

```
$ uv run python Tools/scripts/bm_rc2.py --check; echo "RC2_CHECK_EXIT=$?"
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
RC2_CHECK_EXIT=0
```

The PowerShell rehearsal uses a simulated `-GameDir` under `tmp/rc_sim` only. **No install script was
run against a game folder** - not with `-WhatIf`, not with any other action.

### 3b. `bm_budget.py`

Run as-is it fails on the RC tree, because B-18 moved the parts module out of the path the script
hard-codes (`models/…/sportsmuscle_vehicle_parts.vmodc` -> `models/…/batmobile/…`):

```
$ uv run python Tools/scripts/bm_budget.py Builds/bm-RC2/aaf
FileNotFoundError: .../sportsmuscle_vehicle_parts.vmodc
BUDGET_EXIT=1
```

Same measurement with the moved path (no other change), which is what the build itself measured on
its pre-B-18 stage:

```
$ uv run python -c "... bm_parts.MODULE='models/…/batmobile/sportsmuscle_vehicle_parts.vmodc'; bm_budget.measure('Builds/bm-RC2/aaf')"
RC2 measure: {'reachable_kb': 7166.1, 'non_vanilla_kb': 4791.3, 'rbm': 189}
cap 4915.0
within cap: True
```

`non_vanilla_kb` 4791.3 <= 4915 (R9 model cap): **pass**, and exactly RC1's figure. `reachable_kb`
7166.1 is the vanilla-inclusive figure, which is not the cap metric (bm_budget.py docstring: only
non-vanilla meshes count; the calibration builds rendered at 4,657.6 non-vanilla with 6,132-7,032
reachable). Texture budget from the receipt: resident `.ddsc` inside the `.ee` - see §4.

### 3c. `v03_wiring` against the new tree

`v03_wiring.py` hard-codes `Builds/bm-RC1` and writes into `bm-RC1/verify`, so it was run through
`v03_wiring2.py`: the same file with `TAG` + `--tag`, and verify artefacts written to
`Working/RC/verify-<TAG>/` instead of inside a `Builds/` tree. It also had to resolve the parts
module by name (B-18 moved it; the original resolves `bm_parts.MODULE` literally and would fail on
RC1 too).

```
$ uv run --with numpy --with fsb5 --with scipy python Tools/scripts/v03_wiring2.py --tag bm-RC2
G1 points   9 SWeaponPoint, part refs dangling 0
G2 ids      63 objectid references -> 442 objects; 10 cross-file refs the vanilla .epe also makes (3 distinct); dangling 0
G3 refs     99 asset paths (ctune 17/17, etune 3/3, ftune 1/1, lod 73/73, wtune 5/5) from the .epe + 15 edited modules, dangling 0
G4 audio    bm_audio --check rc=1 (FAIL: Working/Audio/bm_bank_manifest.json differs from the re-derived record); .ee.fmod_guids == B-11's: True
G5 drop     item 1621485476 -> v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.ee + .toc + icon in the dropzone: True
FAIL: dangling 1
    bm_audio.py --check: FAIL: Working/Audio/bm_bank_manifest.json differs from the re-derived record
WIRING_EXIT=1
```

**G4 is a real failure and it is not about the shipped banks**: `Builds/bm-RC2/drop/sound/fmod_banks/
vehicles.bank` and `weapons.bank` are byte-identical to RC1's and to `Builds/bm-004/banks`
(sha256 `76d67bcef81c8d29…`, `5b8a7605a8b70ca2…`), and the `.ee`'s `fmod_guids` equal B-11's. What
is stale is the **record** in `Working/Audio/bm_bank_manifest.json` (written 2026-11-02 22:23), which
`bm_audio.py --check` re-derives and compares. Note the same gate would have failed on RC1; it was not
introduced by this tree. Fixing it means regenerating that Working/ file, which is B-11/T-12's
deliverable, not this card's, so I did not overwrite it.

## 4. RC1 vs RC2: drop file list and sha256

```
$ (compare Builds/bm-RC1/receipt.json with Builds/bm-RC2/receipt.json)
RC1 files 9 RC2 files 9
SAME  editor/entities/jc_vehicles/01_land/…/v0300_car_kensington_sportsmuscle_debug.ee
SAME  editor/entities/jc_vehicles/01_land/…/v0300_car_kensington_sportsmuscle_debug.ee.toc
SAME  profile/item.onlinec
SAME  profile/online.stringlookup
SAME  profile/task.onlinec
SAME  settings/spawn_vehicle_defs.bin
SAME  sound/fmod_banks/vehicles.bank
SAME  sound/fmod_banks/weapons.bank
SAME  textures/ui/vehicle_icons/v0300_car_kensington_sportsmuscle_debug.ddsc
toc RC1 607 RC2 607
aaf files 691 691
budget RC1 {'reachable_kb': 6895.9, 'non_vanilla_kb': 4791.3, 'rbm': 181} RC2 {'reachable_kb': 6895.9, 'non_vanilla_kb': 4791.3, 'rbm': 181}
```

| quantity | RC1 | RC2 | verdict |
|---|---|---|---|
| drop files | 9 | 9 | same list, **9/9 identical sha256** |
| `aaf` source files | 691 | 691 | same list, **0 sha256 changed**, 0 added, 0 removed |
| `.toc` records | 607 | 607 | identical |
| model budget (non-vanilla) | 4791.3 KB | 4791.3 KB | identical, under the 4,915 KB cap |

Verified independently of the receipts by hashing both trees (691 files each, 0 differing):

```
$ uv run python tmp/freebuff/scratch/cmp_aaf.py
rc1 files 691 rc2 files 691
changed sha256 0 []
only rc1 0 only rc2 0
```

**Reason from the input diff**: no input `bm_rc2.py` reads changed between RC1's build
(2026-11-02 21:48) and RC2's (2026-11-05 02:42) - `bm-005/006/007/008`, `bm-004/banks`, `bm-013/drop`,
`Working/Collision/batmobile.physicsc` (2026-10-31 00:25) and the merge base `.epe` are all older than
both builds. Every Working/ file that did change today (B-10d's `Working/Collision2/*`, the T-card
outputs) is either not an input or is opt-in (`--physicsc`). Hence RC2 = RC1 with a new tag, and the
reasons column is "input unchanged" for all 700 files (9 drop + 691 tree).

## 5. Tamper test of `--check`

```
$ cp -r Builds/bm-RC2 Builds/_bm-RC2-tamper
$ uv run python Tools/scripts/bm_rc2.py --check --tag _bm-RC2-tamper | tail -3
FAIL rehearsal (b) decoy dropzone: Install backed up the existing item.onlinec
PASS rehearsal (b) Rollback091 restored the decoy byte-for-byte and removed the rest
FAIL: _bm-RC2-tamper 1 failure(s), 9 drop files, 691 tree files, .toc 607 records
```

That single baseline failure is an artefact of copying, not of RC2: `install.ps1` is generated with
its own tag baked in (`.<TAG>-backup`), so the copy's installer writes `.bm-RC2-backup` while
`--check --tag _bm-RC2-tamper` looks for `._bm-RC2-tamper-backup`. Everything RC2-specific still
passed (9/9 rehash, 691 tree files, 607 toc records).

One byte flipped in the middle of the packed `.ee`:

```
flipped one byte at 5695285: 0x5c -> 0x5d; size 11390571
== check after tamper ==
FAIL rehashed 8/9 ok
TAMPER_CHECK_EXIT=1
```

So `--check` **fails on a one-byte change** and returns a non-zero exit code; the tamper tree was
deleted afterwards (`rm -rf Builds/_bm-RC2-tamper`), RC2 itself was never modified.

## 6. Receipt and installer

- `Builds/bm-RC2/receipt.json` (205,440 B) - schema 2, `card: "B-RC2"`, `lineage_card: "B-14"`,
  `tag: "bm-RC2"`, `b10_input {path, sha256, b10_pin_rc1}`, 14 deps, full `steps`, `b18`, 9 drop files
  with sha256 + owner card, 691 `aaf` entries, `toc` block, budgets, `unknown` list.
- `Builds/bm-RC2/install.ps1` (4,614 B) - generated, **not run** (see §3).
- `Working/RC/bm_rc_manifest_bm-RC2.json` - the owner map (`bm_rc_manifest.json` = RC1's, untouched).

## COMPROMISES

Every shipped value that is less than BmAK, from `Working/RC/COMPROMISES_B.md` (AUDIT-B) - all of
these are in RC2 because RC2 ships RC1's bytes:

1. **Model budget cut** - B-15 trimmed 16 far-LOD `.lod` files, non-vanilla model 5,972.9 ->
   4,791.3 KB (R9/4,915 cap). Mid/far LODs lose detail; not approved by the operator.
2. **Serpente panels left bound** - B-17 hidden panels were skipped (`BM_NO_B17=1` in the steps), so
   donor body panels are still bound/drawn over the Batmobile silhouette.
3. **Lamp rig 21 -> 18 entries** (B-07) - three BmAK lamps have no JC3 carrier.
4. **12 APC mounted-M2 body members removed** (B-16) and 4 owner links nulled - the donor's weapon
   clones carry fewer members than the APC original.
5. **One hybrid variant** (D-2): B-12 was skipped, so there is no separate battle-mode car; one tree
   serves both modes.
6. **Health and damage mods** and **audio route a+c** as recorded in COMPROMISES_B.md - the JC3
   carriers are coarser than BmAK's.
7. **Collision**: RC2 ships B-10 + B-10b + B-10c from `Working/Collision/batmobile.physicsc`
   (2026-10-31 00:25). **B-10d's re-derived hull (`Working/Collision2/batmobile.physicsc`,
   2026-11-05 02:25 / `bm_vehicle_hull.json` 05:25) is NOT in the tree** - it arrived after the
   build and shipping it would change the car's collision, so it stays an open, unapproved item.
8. **Not implemented yet - operator decisions** in
   `Research/BatmobileGrab/CONTROLS_MENU_SCREENS.md` (2026-11-05): drop **AR Challenges and Mission
   Select** from the d-pad, move the **Power Winch to d-pad right** using the tether mechanic, make
   **BmAK controls replace JC3's inside the car** (enter `Y`, exit `LB`, eject `A A`, pause and
   commlink keep priority), and use the **BmAK colour exactly** (lighting differences accepted).
   None of these is in the tree: RC2's step list contains no input-binding, winch or colour change,
   and the `.epe` it ships is the B-06/B-07/B-08 merge plus T-13R interaction transforms only.

## UNKNOWNs

1. Whether the tree loads in game (phase Q, not run - test ban).
2. Whether the game resolves the `_debug` leaf from the Rebel Drop hash (Q-1).
3. Why `Working/Audio/bm_bank_manifest.json` no longer matches the re-derived record - the gate's
   message names the file but not the field; re-deriving it is B-11/T-12's job.
4. Whether B-10d's hull is closer to BmAK than the shipped B-10/B-10b/B-10c triple - see
   `tmp/freebuff/reports/B-10d.md`; not settled by this card.
5. `bm_budget.py` cannot measure a post-B-18 tree without a patched module path; whether the gate
   should follow the move is a tools decision, not taken here.

## Commands run (verbatim, in order)

```
uv run python Tools/scripts/bm_rc2.py --check                      -> 16 PASS, exit 0
uv run python Tools/scripts/bm_budget.py Builds/bm-RC2/aaf        -> FileNotFoundError (module moved by B-18), exit 1
uv run python -c "…bm_parts.MODULE='…/batmobile/sportsmuscle_vehicle_parts.vmodc'; bm_budget.measure('Builds/bm-RC2/aaf')"
                                                                   -> non_vanilla_kb 4791.3 <= 4915, exit 0
cp -r Builds/bm-RC2 Builds/_bm-RC2-tamper && bm_rc2.py --check --tag _bm-RC2-tamper   (baseline)
python (flip one byte at 5695285 of the packed .ee) && bm_rc2.py --check --tag _bm-RC2-tamper
                                                                   -> FAIL rehashed 8/9 ok, exit 1
rm -rf Builds/_bm-RC2-tamper
uv run --with numpy --with fsb5 --with scipy python Tools/scripts/v03_wiring2.py --tag bm-RC2
                                                                   -> G1/G2/G3/G5 clean, G4 audio FAIL, exit 1
uv run python tmp/freebuff/scratch/cmp_aaf.py                      -> 691/691 files, 0 changed
```
