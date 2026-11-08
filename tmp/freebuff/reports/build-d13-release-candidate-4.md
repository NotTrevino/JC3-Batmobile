# B-14 / D-13 — release candidate 4 (`Builds/bm-RC4`)

Built and verified offline. **Nothing was installed and no game was launched.** The tree is
deliberately **not marked complete** (`receipt.complete = false`): 12 of 23 texture rows are
unfaithful and the reopened B-10 chassis-box gate does not pass. Both are recorded below and in
the receipt.

Command that produced this: `python Tools/scripts/bm_rc4.py --write`
Command that proves it: `python Tools/scripts/bm_rc4.py --check` → `PASS: bm-RC4 0 failure(s)`.

---

## 1. What was merged, and from where

`bm_rc4.py` was already the B-14 assembler for the RC4 tree set; this run completed it and fixed
four defects that made the previous output unusable (see §7). The merge itself is unchanged in
shape from RC1/RC2: every `.epe` contributor goes through `git merge-file` on the
`ConvertProperty` XML, base = the parts tree's graph, conflicts stop the build.

| input tree | contributes | result |
|---|---|---|
| `bm-RC4-lights` | **stage**: parts split + 24-row lights module (688 files) | copied as the base |
| `bm-RC4-entity` | the `.epe` (B-05) | 3-way merged |
| `bm-RC4-weapons` | 7 private `.wtunec` files + repointed `.epe` members | 3-way merged onto entity; 7 tunes overlaid |
| `bm-RC4-effects` | `.epe` effect attachments (B-08) | 3-way merged |
| `bm-RC4-damage-collision` | private `batmobile_health_medium.vmodc`, `sportsmuscle.physicsc`, `custom_land_global.vmodc` | modules overlaid; `.epe` merged |
| `bm-RC4-handling` | 5 handling modules | overlaid; its `custom_land_global` is the merge base (§1) |
| `bm-RC4-rebel` | `item.onlinec`, `task.onlinec`, `online.stringlookup`, `spawn_vehicle_defs.bin`, icon | copied into `drop/` |
| `bm-RC4-audio` | `vehicles.bank`, `weapons.bank` | copied into `drop/` |

`.epe` merge: 7,084 → 9,025 XML lines, `ConvertProperty -i` output re-exports to the merged XML
byte-for-byte (`round trip identical`). 5 earlier-branch lines were superseded by a later branch
(weapons repoints the same five members B-05 wrote); the check prints the count rather than hiding it.

**Module overlap resolved, both sets carried** (`module_merges[0]`, `conflicts: []`):
`…_custom_land_global.vmodc` is written by D-08 (wheel `skew_health` 200 → 400) and by D-10 (nitro /
heat / drift members). A `.vmodc` is binary, but the two branch copies are the **same 3,399 B /
61-member layout and differ in exactly 7 members** (2 + 5, no member unique to either), so the RC
starts from D-10's module and writes D-08's two rows onto it at their decoded `offset-in-file`
anchors (`t5_apply.apply_file`, which asserts each old value and that no untouched member moves).
The merged module is 3,399 B, sha256 `d67f0fe92536a44a...`, and **7 members read back from the
packed `.toc`**: both `skew_health` = 400 and D-10's five (`drift.min_speed_to_drift_kmph` 0,
`drift.steering_sensitivity` 2, `arcade.nitro_boost.torque_multiplier` 6.3,
`arcade.heat_boost.grip_multiplier` 1.5, `arcade.nitro_boost_upgraded.extra_top_speed` 80).
Nothing is `not_carried`.

---

## 2. Reopened B-10 collision and health

Health (D-08): the shared `lave_health_medium.vmodc` is not edited (R7). The RC carries the
private `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/batmobile_health_medium.vmodc`
(3,741 B) and the `.epe` `damage` hash points at it; the module is internal in the `.toc` at
offset **23,252,584**.

Collision (B-10 reopened 2026-11-07): `sportsmuscle.physicsc` ← `Working/Collision2/batmobile.physicsc`
(B-10e BmAK-chassis variant), sha256 `0164936b928f821c058c5a154a93b7cadcdbb9baca7d44fb67cb8f18a9399323`,
340,368 B, internal in the `.toc` at offset **15,993,844**.

| B-10 fact | value |
|---|---|
| BmAK asset | `Physics.Batmobile_V3_Physics` — **2 bodies / 3 boxes / 1 constraint** |
| hulls written | 5 (body 0 + 4 wheels) over the donor's 54 |
| donor bodies still in the file | 62; shapes missing 2; free hull slots 0 |
| hull **shape** vs chassis box 0 (690.305 × 374.536 × 207.5 cm) | max dev **0.0000 m** |
| hull **placement** vs chassis box 0 | `[0.0005, 0.061, 0.0025]` m → **6.1 cm** |
| card gate | 5 cm → **NOT MET** |
| why | the hull is the box's shape but keeps DIM-1's **ground line**, so it sits 6.1 cm above the decoded box (the old render-bbox target was 0.1252 / 0.196 / 0.061 m off) |
| 1 constraint | **named omission** — no JC3 constraint writer exists |

This is a measurement, not a build failure: the file is carried as B-10 delivered it, the gate
result is stored in `receipt.collision.gate` (`pass: false`, `not_carried: "chassis-box placement"`),
and it is the first entry in `receipt.not_done`. **B-10 stays not-done.**

---

## 3. Artifacts

`Builds/bm-RC4/` — receipt schema **2**, 696-file `aaf` source tree, `drop/` payload, installer,
`verify/`.

| artifact | bytes | sha256 (32) |
|---|---:|---|
| `drop/…/v0300_car_kensington_sportsmuscle_debug.ee` | 11,225,534 | `a233c93dcbbe0732b48a448e5818e296` |
| `drop/…/v0300_car_kensington_sportsmuscle_debug.ee.toc` | 68,675 | `cde0678e2fb710bad98b223854ea4ae3` |
| `install.ps1` | 6,535 | `df23485d65f358e14ea8d0b5037d42f0` |
| `receipt.json` | 211,711 | `8c361822c3ae5cd5b6dea2680b1b3a6d` |
| `verify/aafdiff_rc2.md` | 17,587 | `4f44e11224a08da562329334c52075e8` |

`drop/` = 9 files, each with sha256 and owner card in the receipt:

| path | bytes | owner |
|---|---:|---|
| `editor/entities/.../v0300_car_kensington_sportsmuscle_debug.ee` | 11,225,534 | B-01…B-13b merged |
| `…debug.ee.toc` | 68,675 | B-14 |
| `profile/item.onlinec` | 77,569 | B-13 |
| `profile/online.stringlookup` | 1,746,322 | B-13 |
| `profile/task.onlinec` | 168,174 | B-13 |
| `settings/spawn_vehicle_defs.bin` | 27,785 | B-13c |
| `sound/fmod_banks/vehicles.bank` | 210,781,376 | B-11 |
| `sound/fmod_banks/weapons.bank` | 177,586,080 | B-11 |
| `textures/ui/vehicle_icons/…_debug.ddsc` | 18,688 | B-13 |

`.toc`: **714 records**, ends with the root `.epe` (offset 17,713,812 / 134,072 B), 225 records
differ from the vanilla donor `.ee`, 26 remain at offset 0 — every one of those is byte-identical
to vanilla or a size-only `@files.xml` stub (R8 gate, §4).

Leaf: `v0300_car_kensington_sportsmuscle_debug` (`name_hash` 1621485476); 3 inner files renamed.

`install.ps1` is rendered from **`Working/Installer/install_v3.ps1`** with its guard semantics
adopted: `-GameDir` must normalise to `E:\Modding\JustCause3\_dropzone_sims\_dropzone_sim_rc4` or sit below it, real game
roots (`D:\Games`, `E:\Games`) are refused, every receipt target must resolve strictly inside
`<GameDir>\dropzone`, failure prints `REFUSED` and exits **2**. Actions: `Status | WhatIf |
Install | Verify | Rollback`; Install snapshots every existing target to `<GameDir>\snapshot\…`
and Rollback restores those byte-for-byte and removes only targets that did not exist.

---

## 4. Gates run (`bm_rc4.py --check`, RC1/RC2's `--check` equivalent)

`PASS: bm-RC4 0 failure(s), 9 drop files, 696 tree files, .toc 714 records, model 4791.3 KB,
textures 12/23 unfaithful (incomplete)` — 22 PASS lines, 0 FAIL:

- receipt lists every `drop/` file (9 = 9 on disk) and every sha256 rehashes;
- `aaf` source tree 696 files, every sha256 matches the receipt;
- `.toc`: 714 records, every non-zero record matches the packed `.ee`, ends with the root `.epe`;
- root `.epe` and `sportsmuscle.physicsc` are internal (real offsets, quoted above);
- **R8**: no offset-0 record carries bytes that differ from the vanilla donor `.ee`
  (19 size-only shared references excluded); changed modules verified internal individually —
  `batmobile_health_medium`, `physicsc`, `vehicle_parts`, `custom_land_global`, `land_engine`, `lights`;
- **R9 model**: 4,791.3 KB ≤ **4,915 KB** (from 5,972.9 KB; 16 far-LOD `.lod` trimmed by `bm_budget.py`);
- **R9 texture**: 5,380.9 KB ≤ **7,065 KB** (D-04 ledger: 33 textures, `hard_ok`; the allocator
  figure 4,648.0 KB is over its own sub-allocation and is reported, not hidden);
- aafdiff vs **bm-RC2**: 120 files differ = exactly the planned set, 0 unexplained;
- B-10 reopened facts present and internally consistent (see §2);
- BUILD_BATCHES = 24 steps with B-17…B-20 declared no-payload; B-25/B-26 recorded as cards;
- every tree file has an owner card; texture rows and `complete: false` present; 0 module conflicts, 1 merged module read back.

`python Tools/scripts/bm_budget.py Builds/bm-RC4/aaf` (dry run): `before = after = 4791.3 KB
non-vanilla of 4,915`, reachable 6,895.9 KB, 181 RBMs, 0 `.lod` changed — the tree is already trimmed.

### aafdiff vs RC2 (exactly the planned files)

`Builds/bm-RC4/verify/aafdiff_rc2.md` (`aafdiff.py --hash`). 120 files differ, all classified:

| class | count | meaning |
|---|---:|---|
| merge-overlay | 20 | written by this B-14 merge (`owners`): `.epe`, `@files.xml`, 5 handling modules, 7 private `.wtunec`, `physicsc`, 5 trimmed `.lod` |
| stage | 2 | rebuilt by the stage tree: parts module and the 24-row lights module |
| base-lineage | 98 | already different from RC2 in `bm-RC4-base`: appearance body/wheel RBMs, mshswap sets, the `batmobile/` private-path modules, 33 textures |

Previously 39 of these were “unexplained” because the classifier only recognised files present in
RC2; files the RC4 base **added** (mshswap wheels, `batmobile/` modules) were invisible to it.

---

## 5. Known gaps carried in the receipt

1. **B-10 chassis-box gate not met** — 6.1 cm placement (see §2). B-10 stays not-done.
2. **Texture rows: 12 of 23 unfaithful** — 4 chapter masks (`Body/Wheel/Glass/Undercarriage
   Damage_ChapterMask`, no chapter selector) + 8 rows whose pixel set the D-04 bake could not
   supply. `receipt.complete = false`; the tree is not complete.
3. **Module overlap resolved** — D-08's two wheel `skew_health` rows are carried with D-10's five
   in one `custom_land_global.vmodc`; 7 members read back from the packed `.toc` (§1).
4. **B-12 / D-2** (pursuit vs battle variants) has no payload — this is one tree; `bm-RC4-modes/`
   is not merged.
5. **B-25 and B-26 are cards only** — lens flares/light units and the per-entity audio override
   have no payload in this RC. `BUILD_BATCHES` is 24 steps with B-17…B-20 declared no-payload.
6. **Runtime is untested** — load, Rebel Drop resolution from the new leaf hash, and every Q take.

---

## 6. Verification rehearsals (offline, simulated dropzone only)

- `-WhatIf` lists exactly the receipt's 9 files + sha256, writes 0 files.
- Decoy dropzone (`profile/item.onlinec` pre-existing): `Install` snapshots it, copies the payload,
  `Verify` → **9/9**, `Rollback` restores the decoy byte-for-byte and removes only the 8 files that
  did not exist.
- Guard negative control: `-GameDir E:\Modding\not_the_sim` → `REFUSED: … is not the simulation
  root …`, exit **2**, nothing written.
- Environment note: this session's `powershell.exe` is 5.1.19041 but `Get-FileHash` is not
  available (module load failure). The generated installer hashes with `System.Security.Cryptography.SHA256`
  directly, so it does not depend on that cmdlet.

---

## 7. Defects found and fixed while completing the build

1. **12 overlay files were never packed.** `SmallPack` packs only what `@files.xml` lists. The
   D-08 private `batmobile_health_medium.vmodc` and all 7 private `.wtunec` files were in the tree
   but unlisted, so the previous `.ee` silently contained neither the health module the `.epe`
   points at nor the weapon tunes. Fixed by registering every unlisted overlay file in
   `@files.xml` before packing (`.ee` 11,188,402 → 11,225,534 B; `.toc` 702 → 714 records).
2. **Installer `Get-Parts` did not split Windows paths** — the regex form returned one component,
   so the containment guard refused the legitimate simulation root. Replaced with the
   `IO.Path` separator API (no literals, no regex).
3. **`Get-FileHash` absent** — every `Install`/`Verify` aborted before snapshotting, and `Rollback`
   then deleted the pre-existing decoy. Replaced with .NET SHA-256.
4. **aafdiff classification** — see §4 (39 unexplained → 0).
5. **R8 safety net was missing from RC4** — the RC derived its `.toc` with `internal=()` and only
   spot-checked the `.epe`/`physicsc`. Now every offset-0 record is compared to the vanilla donor
   `.ee` and made internal from bytes (no hand list), with the gate in `--check`.

---

## 8. What is next

- Rebuild B-10 with the chassis box's own placement (drop the ground-line offset) to clear the
  5 cm gate, or re-word the card if the ground line is the intended behaviour.
- Close the 12 unfaithful texture rows (chapter selector + the 8 missing pixel sets) before any
  “complete” claim.
- Run Q-1 (leaf resolution), then the runtime takes; then V-01/V-02/V-03 on this tree.
- `Builds/bm-RC4-*` remain the per-card trees; `Builds/bm-RC4` is the merged artifact only.
