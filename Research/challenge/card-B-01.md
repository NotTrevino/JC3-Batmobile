# Assumption challenge — B-01 · Build scaffold

**Card:** `GRAB_BACKLOG.md` §8 `B-01 · Build scaffold` (line 992), tracker row `GRAB_BACKLOG.md` line 1334,
MODLOG `## B-01 · Build scaffold — done (2026-10-29)` (line 14314) and the deferred block (line 13963).
**Outputs on disk:** `Tools/scripts/bm_build.py`, `Builds/bm-001/` (aaf, applied.json, receipt.json,
install.ps1, .ee, .ee.toc, verify/, snapshots/), the packer `Tools/scripts/t5_build.py` it drives.
**Rules applied:** §0.5 R1–R14 (this report is the R5 reading of the card: behaviour, not member names).
**Method:** every claim was re-derived from files on disk with read-only commands. The only writes were
throw-away files in the OS temp dir (`C:\Users\User\AppData\Local\Temp\tmp.hLKXGVM9KL`, now deleted) and
this report. Nothing in `D:\Games`, nothing in `Builds/`, no game launched, no commit.

---

## VERDICT

The card's own **Done** line is true and it is stronger than it looks: bm-001's `.ee`/`.toc` really are
byte-identical to test-091's, and an independent repack of the aaf in a temp directory reproduces the same
bytes, so the scaffold genuinely packs rather than copies. The edit half is also real: the probe build the
MODLOG says was deleted reproduces exactly (same `.ee` size, same sha prefix, exactly one changed module),
and both drift refusals reproduce verbatim.

What the card does **not** establish, and where its report overstates:

| # | assumption | verdict |
|---|---|---|
| A1 | bm-001's `.ee`/`.toc` are byte-identical to test-091's (the Done line) | **HOLDS** |
| A2 | the `.ee` is produced by packing `bm-001/aaf`, not copied from the base | **HOLDS** |
| A3 | the aaf tree *is* the archive's content — every file in it lands in the `.ee` | **WEAK** (4 unregistered files are silently inert) |
| A4 | the receipt's `checks[].ok` flags are measurements | **WEAK** (the four packer checks hardcode `ok: True`) |
| A5 | "the applier path proved on a deleted probe build" | **HOLDS** (reproduced exactly, and its spec survives in `tmp/freebuff/`) |
| A6 | phase B's batch file is the scaffold's edit-list input | **WEAK** (schema/keys don't match: `schema 2` vs expected `1`) |
| A7 | the scaffold's multi-step path edits the tree the way `t5_apply.py` documents | **WEAK** (in-place, against that tool's own "never the source" contract; 0 steps ever run) |
| A8 | "the Model/Texture budgets (R9) are the ones test-091's receipt already carries" | **BROKEN** (test-091's receipt has no `budgets` key; bm-001 reports `{}`) |
| A9 | `receipt.textures: 0` describes this build | **BROKEN** (inherited default; the tree carries 134 `.ddsc`) |
| A10 | every module the scaffold accepts as "changed" reaches the game | **WEAK** (2 `.vmodc` are in the `.ee` but in no `.toc` record; nothing checks this) |
| A11 | the `.toc` is rebuilt without adding or dropping files | **HOLDS** (and it is why a later add-a-file card cannot use this path) |
| A12 | nothing was installed, R6 respected | **HOLDS as far as the repo can show** (`installed: false` is hardcoded, and the dropzone now holds bm-001's exact bytes anyway) |
| A13 | build artifacts inside the repo do not break R10 | **HOLDS** (`git check-ignore`: `.gitignore:104 Builds/`, plus `*.ee`, `@files.xml`) |
| A14 | the card's "use `deploy.py` (golden-hash guard)" was followed | **WEAK** (`bm_build.py` never calls `deploy.py`; and `deploy.py` has no "golden" either) |

No coordinate or unit convention is involved: B-01 moves no vertex, socket or light, so R2's `T(p)` is
untouched and the identity build says nothing about scale. Nothing here was tested on a fleet sample —
B-01 has exactly one build and the report treats it as one build.

---

## A1 · "bm-001 `.ee`/`.toc` are byte-identical to test-091's"

*Why it matters:* this is the card's entire Done criterion; the manifest row (line 1334) quotes the same
two hashes as evidence.

*Test:*

```
$ sha256sum Builds/bm-001/*.ee Builds/bm-001/*.toc Builds/test-091/*.ee Builds/test-091/*.toc
6ab8275f566a354298c943f3ce3d747086c1b0e832091805ec9e5d70deafcf8d *Builds/bm-001/…civilian_01.ee
444ed479eeba144f14b46554844e2768734d760054eed54c9fd73ba700ac55aa *Builds/bm-001/…civilian_01.ee.toc
6ab8275f566a354298c943f3ce3d747086c1b0e832091805ec9e5d70deafcf8d *Builds/test-091/…civilian_01.ee
444ed479eeba144f14b46554844e2768734d760054eed54c9fd73ba700ac55aa *Builds/test-091/…civilian_01.ee.toc
```

`python Tools/scripts/bm_build.py --tag bm-001 --check` → `PASS … (6AB8275F566A3542…, 506 .toc records)`,
exit 0; the tree digests of the two `aaf` dirs are also identical
(`561D301D0499EE7B…`, 590 files, 22,011,703 B).

**Verdict: HOLDS.**

## A2 · "the `.ee` comes from packing the tree" (silent)

*Why it matters:* a copied base `.ee` would satisfy A1 without exercising the pack path at all, and every
later B card depends on that path. Nothing in the receipt distinguishes "packed" from "copied": both give
the same bytes in an identity build.

*Test (independent of `bm_build.py`, in a temp dir):*

```
$ cp -r Builds/bm-001/aaf $TMP/aaf
$ Tools/Gibbed/Gibbed.JustCause3.SmallPack.exe $TMP/aaf $TMP/x.ee
$ sha256sum $TMP/x.ee ; ls -l $TMP/x.ee
6ab8275f566a354298c943f3ce3d747086c1b0e832091805ec9e5d70deafcf8d *…/x.ee
-rw-r--r-- 1 User 197121 10737057 … /x.ee
```

The four numbers in the MODLOG (`10,737,057 B`, `6AB8275F…`, `444ED479…`, `506 records`) are reproduced by
the packer alone, so the identity is a property of the tool chain, not of a copy. `t5_build.py` does call
`SmallPack` (line 84) and raises on a non-zero exit, and `bm_build.py` never copies a `.ee`.

**Verdict: HOLDS** — the strongest single result in this card.

## A3 · "the aaf tree is the archive's content" (silent)

*Why it matters:* every phase-B card edits files **in the aaf** and assumes the edit is what the archive
carries. If a file in the tree is not registered in `@files.xml`, `SmallPack` drops it (`deploy.py`'s own
docstring: "add the converted textures to the tree AND to `@files.xml` (SmallPack drops unregistered
files)"). An edit to such a file would be accepted by the scaffold's diff check only because the file
never changed in the output — or refused as "missing", depending on whether the packer rewrote it.

*Test:*

```
$ find Builds/bm-001/aaf -type f | wc -l                       # 590
members of the .ee (project reader)                             # 604
files after SmallUnpack of the .ee (Builds/bm-001/verify)       # 586
$ python - <<'PY'  # relative-path sets, aaf vs verify
in aaf, not in verify:
  + …/sportsmuscle_wheel_f_l_lod4.rbm 31789
  + …/sportsmuscle_wheel_f_l_lod5.rbm 22981
  + …/sportsmuscle_wheel_f_r_lod4.rbm 30941
  + …/sportsmuscle_wheel_f_r_lod5.rbm 23489
in verify, not in aaf: []
PY
```

`@files.xml` lists exactly the 604 `.ee` member names (set-equal), and none of those four names is among
them; nor is either name a member of the `.ee` (`members()` → `[]`). So the aaf advertises 590 files while
the archive carries 586. The base build knew this: test-091's own receipt check reads
`"pack/unpack: every registered file unpacked", "586 packed, 0 missing"` — the count is against
*registered* files, not against the tree.

Also measured: `@files.xml` is **not byte-stable** across pack/unpack (`113,804 B → 114,410 B`), but the
difference is line endings only — same 607 lines, same order, same values (verified by comparing the
stripped line lists, not by `diff`).

*Consequence:* B-02's plan (line 1008) says "if over, decimate LOD4/5 of the body first". Body LOD4/5 are
registered; the four **wheel** front LOD4/5 are not. A later card that decimates `sportsmuscle_wheel_f_?_lod4/5`
would see `aafdiff` report 1 changed module and a bigger build, while the game loads the old meshes from
the archives. `t5_build.py`'s `missing` check would catch it (`diff outside the edit list: … missing [...]`),
but only after the edit step has already rewritten the build tree.

**Verdict: WEAK** — true for registered files (586), false for the tree (590); the four dead files are
inherited from test-091 and are undocumented in the B-01 report.

## A4 · "the seven PASS lines are measurements" (R5 reading)

*Why it matters:* §12 and the MODLOG quote the PASS block as the Done evidence.

*Test:* `Tools/scripts/t5_build.py` lines 124–135 — the four packer checks are a literal list with
`"ok": True` in the source, and the failure paths `raise SystemExit` before the receipt is written:

```
checks = [
    {"name": "pack/unpack round-trip", "ok": True, "detail": f"{len(os.listdir(verify))} top-level entries"},
    {"name": "only edited modules differ", "ok": True, "detail": f"{len(changed)} changed"},
    …
]
```

`bm_build.py` adds two more with `"ok": True` written literally (`tree copied from the base build`,
`no edit step outside the named list`). Only the seventh (`bm-001 .ee/.toc byte-identical to test-091`) is
computed (`identity`), and only it can be `False`. So `receipt.checks[].ok` carries no information: every
listed check that could fail aborted the build instead.

Note also that `pack/unpack round-trip`'s detail is the count of **top-level directories** in `verify/`
(`5`), i.e. `editor effects models textures` + `@files.xml` — not a comparison of any file with the aaf.

**Verdict: WEAK** — the checks are real guards (they raise), but reading their `ok` flags is reading a
constant. The card's Done does not depend on them.

## A5 · "the applier path was proved on a deleted probe build"

*Why it matters:* it is the only evidence in the card that step (2) — apply a named edit list — works at
all, and the build it refers to (`Builds/bm-editprobe/`) is gone (`ls Builds/` has no such tag).

*Test:* the probe's own inputs survive at `tmp/freebuff/bm_probe_spec.json` (`schema 1`, tag
`bm-editprobe`, one `t5_apply` step) and `tmp/freebuff/bm_probe_edits.json` (`T-M1 RigidBody.mass 6000 →
6001`, `"note": "BM probe: mechanism control only, values fabricated, build deleted"`). Replaying them
into a temp tree:

```
$ python Tools/scripts/t5_apply.py --aaf $TMP/aaf --out $TMP/edit --edits $TMP/probe.json \
      --current Working/Translation/current.json --json $TMP/applied.json
FILE v0300_car_kensington_sportsmuscle_rigid_body.vmodc: 1 edit(s)
1 edit(s) over 1 module(s) applied, re-read and size-checked
$ Tools/Gibbed/Gibbed.JustCause3.SmallPack.exe $TMP/edit $TMP/probe.ee ; ls -l ; sha256sum
-rw-r--r-- 1 User 197121 10737058 … /probe.ee
36e10aa9377ef3c704931bef0a45dacb692c21e3ef1625a15855e960625a9036 *…/probe.ee
$ python Tools/scripts/aafdiff.py Builds/test-091/verify $TMP/verify2 --hash
| 976 | 976 | +0 | `editor/…/modules/default/…_rigid_body.vmodc` |
| Common, identical content | 585 |
```

That is the MODLOG's transcript reproduced to the byte: +1 byte (`10,737,058`), sha prefix `36E10AA9…`,
exactly one changed module. The two drift refusals also reproduce verbatim:

```
$ python Tools/scripts/t5_apply.py --aaf Builds/bm-001/aaf --check-only \
      --edits Working/Translation/t5c_edits.json --current Working/Translation/t5c_current.json
T-K2: front.min_time_to_block holds '1' (float), list expects 5
$ … --edits Working/Translation/t1_edits.json --current Working/Translation/current.json
T-DM2: bullet_armor_strength holds '99' (float), list expects 100
```

One imprecision: the MODLOG says replaying `t1_edits.json` "stops on 14 values later batches already
changed". Row-by-row, **all 35 rows** in that list now hold their new value (35 rows over 10 modules;
`t1_edits.json` has no "14"). The refusals are real; the number 14 is not the row count.

**Verdict: HOLDS** (with the "14" corrected).

## A6 · "phase B's batch file is the scaffold's edit-list input" (silent)

*Why it matters:* B-01's whole point is to be the phase-B entry point; step (2) takes `--edits` specs.

*Test:* `bm_build.load_specs` requires `schema == 1` and a `steps` list. The file the gate card T-23
delivered for phase B is `Working/Translation/build_batches.json`:

```
$ python -c "import sys;sys.path.insert(0,'Tools/scripts');import bm_build;bm_build.load_specs(['Working/Translation/build_batches.json'])"
SCHEMA = 1
keys: ['card','schema','generated_by','sources','gate','features','batches','t_cards'] schema: 2 steps: 0
SystemExit: Working/Translation/build_batches.json: schema 2, expected 1
```

The only JSON with `"steps"` outside `Builds/` are `tmp/freebuff/bm_probe_spec.json`, the `tmp/t23bak`/
`tmp/t23rework` backups and the rejected build_batches.json. So the scaffold's documented interface has no
producer on disk — the probe spec was hand-written and its build deleted.

**Verdict: WEAK** — the interface exists and is validated, but nothing that phase B will actually hand it
parses. The first B card that passes a real list will be the first test of this step.

## A7 · "each step edits the tree" (silent; R5)

*Why it matters:* `t5_apply.py`'s own help says `--out` is "copy of that tree to write into (**never the
source**)"; `bm_build.apply_steps` deliberately omits `--out`:

```
# t5_apply writes into a COPY of the tree (never the source); with --out == the tree in place
# it would copy onto itself, so the build tree is passed as --aaf and edited in place
run([sys.executable, …/t5_apply.py, "--aaf", tree, "--edits", …, "--current", current, "--json", out])
```

`t5_apply.py` has no guard against that (`if a.out and not a.check_only:` — with no `--out` it edits
`groups` paths inside `--aaf` directly), so it works today. The build never exercised it:
`Builds/bm-001/snapshots/` contains **0** files, and the probe I replayed used `--out`, not the in-place
path. A failing second step therefore leaves `Builds/bm-0NN/aaf` half-edited with no rollback, and a
future tightening of `t5_apply` per its own docstring breaks the scaffold silently.

**Verdict: WEAK** — in-place mode is real but undocumented in the tool's contract and unexercised by the
build; the multi-step ordering has never run end to end.

## A8 · "the R9 budgets are test-091's own numbers"

*Why it matters:* R9 is a non-negotiable rule ("Every build reports both"), and the MODLOG's UNKNOWN 5
says: "the Model/Texture budgets (R9) are **the ones test-091's receipt already carries**".

*Test:*

```
$ python -c "import json;d=json.load(open('Builds/test-091/receipt.json'));print(list(d))"
['tag','built','base','src','ee','toc','candidate','files_xml_added','checks']
$ … Builds/bm-001/receipt.json → "budgets": {}
```

test-091's receipt has **no `budgets` key at all**, so `t5_build.py`'s
`"budgets": base_rec.get("budgets", {})` produced an empty table; bm-001 therefore reports neither number,
and UNKNOWN 5 describes a receipt that does not exist. 12 of the 15 receipts in `Builds/` do carry the
pair — the nearest is `test-090`: `model_kb 4764 / model_cap_kb 4915, texture_kb 3954 / texture_cap_kb 4648`
— but 091 (the base of the whole B lineage) does not, so no B build inherits it.

Second discrepancy: those receipts use a **texture cap of 4,648 KB**, while R9 states 7,065 KB. Whatever
the reason (R9 cites MODLOG §76/§111), the number a B build would inherit and the number the rule states
are not the same.

**Verdict: BROKEN** — bm-001 reports no budget, and the MODLOG's sentence explaining that is false.

## A9 · "`textures: 0` describes this build"

*Why it matters:* a later budget/asset audit reading receipts would take 0 as "this entity ships no new
textures".

*Test:* same inheritance (`"textures": base_rec.get("textures", 0)`) against a base with no `textures` key.
Meanwhile:

```
$ find Builds/bm-001/aaf -iname "*.ddsc" | wc -l      # 134
.toc records: 506, internal 479 (97 of them .ddsc); .ee members not in the .toc: 98 (37 .ddsc)
```

So `0` is a default, not a count. (It may mean "textures *added by this step*", which is 0 and correct —
but nothing in the receipt says that, and the base it copies from has no such number either.)

**Verdict: BROKEN as a description** of the build; harmless if read as "this step converted nothing".

## A10 · "a module the scaffold accepts as edited is a module the game loads" (silent)

*Why it matters:* R7/R8 exist precisely because the archive and the `.toc` disagree about which copy wins.

*Test:* count `.ee` members with no `.toc` record and list the modules among them:

```
ee members not in .toc: 98   Counter({'.trim': 43, '.ddsc': 37, '.ctunec': 10, '.effc': 6, '.vmodc': 2})
UNLISTED vmodc: editor/entities/jc_vehicles/00_shared/modules/default_extended_effect_usages.vmodc (…,627)
UNLISTED vmodc: editor/entities/jc_vehicles/00_shared/modules/vehicle_common.vmodc (…,12271)
```

`vehicle_common.vmodc` — the exact module R7 forbids editing — is carried inside the `.ee` (12,271 B) and
is in **no** `.toc` record, so the game keeps the archive copy. `sportsmuscle_vehicle_deform.vmodc` and
`sportsmuscle_vehicle_parts.vmodc` are `.toc` records with offset 0 (external, R8's `--internal` problem).
Neither `t5_build.py` nor `bm_build.py` checks that a changed file is a `.toc` record: the only guards are
"changed list ⊆ edit list" and "record **list** identical to base". An edit to `vehicle_common.vmodc` would
pass all seven checks and change nothing in game.

**Verdict: WEAK** — B-01 edits nothing, so the Done is unaffected, but the scaffold cannot tell a carried
edit from an inert one.

## A11 · "the `.toc` is rebuilt without adding or dropping files"

*Test:* the base `.toc`'s sha equals bm-001's (`444ED479…`, 50,643 B, 506 records), so `eetoc.py patch`
with zero changes is idempotent; `t5_build.py` raises if `base_names != recs` and if any internal record
disagrees with the `.ee` (`479 internal of 506`).

**Verdict: HOLDS** — and it is also the reason the MODLOG's UNKNOWN 2 is right: a card that *adds* a
member (B-04/B-06 per §8) cannot use this path, and the scaffold will refuse it rather than silently
dropping the file.

## A12 · "nothing was installed; R6 respected"

*Test:* `receipt.bm.installed` is `False` — but it is written literally (`"installed": False`), not
measured, so it is an author's assertion. What the disk can show: the installer's `Install` block copies
to `D:\Games\Just Cause 3\dropzone\…` and its `Verify` action calls an existing tool with an existing flag
(`Tools/scripts/verify_install.py --build` exists, `--build` is a real argument), and `Rollback091`
delegates to `Builds/test-091/install.ps1`, which exists. Neither action was ever run (MODLOG UNKNOWN 1).

A coincidence worth recording: because bm-001's `.ee`/`.toc` are test-091's bytes, the hashes the installer
would check are the hashes already in the dropzone, so an accidental `-Action Install` would leave no
trace in any hash — this state cannot distinguish "never installed" from "installed".

**Verdict: HOLDS as far as the repo can show**; the flag is not evidence.

## A13 · "build artifacts inside the repo do not break R10"

*Test:*

```
$ git check-ignore -v Builds/bm-001/v0300_…_civilian_01.ee
.gitignore:104:Builds/   Builds/bm-001/…_civilian_01.ee
$ git status --short Builds/bm-001     # (empty)
```

`*.ee`, `*.ee.toc`, `*.rbm`, `*.ddsc`, `@files.xml` and `Builds/` are all ignored.

**Verdict: HOLDS.**

## A14 · "the card's 'use `deploy.py` (golden-hash guard)' was followed"

*Why it matters:* the card's leader paragraph is a Do instruction, and the scaffold's missing budget step
(A8) and missing `@files.xml` registration step (A3) are exactly the two things `deploy.py` does in its
stage/verify phases (docstring: "add the converted textures … AND to `@files.xml`", "model + texture
budgets").

*Test:* `bm_build.py` imports only `eetoc`; it never invokes `deploy.py`. And `deploy.py` itself contains
no "golden" (`grep -n "golden" Tools/scripts/deploy.py` → no output); its guard is the hash-pinned base
installer it reads, which the scaffold replaces with a tree digest plus the two identity hashes.

**Verdict: WEAK** — the requirement ("guard the build against a drifted base, with a receipt") is met by a
different and smaller mechanism, deliberately and with reasons in the docstring; the two capabilities the
card's wording pointed at (budgets, archive registration) are absent, which is what A8 and A3 measure.

---

## What this card actually establishes

1. `Builds/bm-001/` is a faithful copy of test-091, produced by the real packer, reproducibly (A1, A2).
2. The applier + packer + diff chain works for a one-row edit and refuses a drifted list (A5).
3. The `.toc` patch is idempotent and refuses a changed record list (A11).
4. Builds stay out of git (A13).

## What it does not

- It reports **no** R9 budget, and says it does because test-091's receipt has one (A8, A9).
- It cannot tell a carried module from an inert one (A10).
- Its edit-list input format has no producer yet, and its multi-step in-place path has never run (A6, A7).
- The aaf it will hand every later card carries 4 files that never reach the archive (A3).

## Reproduce

```
python Tools/scripts/bm_build.py --tag bm-001 --check
sha256sum Builds/bm-001/*.ee Builds/bm-001/*.toc Builds/test-091/*.ee Builds/test-091/*.toc
python Tools/scripts/t5_apply.py --aaf Builds/bm-001/aaf --check-only \
    --edits Working/Translation/t1_edits.json --current Working/Translation/current.json
```
