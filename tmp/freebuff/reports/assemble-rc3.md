# Assemble bm-RC3: bm-RC2 + the jointed parts module + the two hinges

Card: "produce a NEW tree Builds/bm-RC3 from bm-RC2 + the jointed parts module + the hinged
physicsc (leave out the audio bank if bm-004c still has a red gate). Write Tools/scripts/bm_rc3.py
(a copy of bm_rc2.py with its own TAG, never editing bm_rc2.py), run it, and show receipt.json
lists the changed files and that every other payload file is sha256-identical to bm-RC2."

Status: **built and checked, 0 failures.** `Builds/bm-RC3` exists with `aaf/`, `drop/`,
`receipt.json`, `install.ps1`. Nothing was installed; no game was started.

Generator: `Tools/scripts/bm_rc3.py` (new file; `Tools/scripts/bm_rc2.py` untouched —
`git status` shows it unmodified). Same shape as bm_rc2.py: one TAG, a staged tree, SmallPack,
`.toc` rewrite, drop listing, receipt, PowerShell installer with rehearsals. The build shape
differs on purpose: bm-RC2 is a *merge of branches onto bm-005*; bm-RC3 is an **overlay onto
bm-RC2** — it stages a byte copy of `Builds/bm-RC2/aaf` and touches exactly two files.

    python Tools/scripts/bm_rc3.py --write   # builds Builds/bm-RC3, then runs --check
    python Tools/scripts/bm_rc3.py --check   # re-hash / re-derive / rehearse, writes nothing

## 1. What the tree is

| | |
|---|---|
| tag | `bm-RC3` |
| parent | `bm-RC2` (`parent_ee_sha256` 886a7919e205fc3b94e8ea1629587777cd62e3f3061ca4fc404f8b8ca09f9e2b) |
| leaf | `v0300_car_kensington_sportsmuscle_debug` (the Q-1a leaf; B-13b rename kept) |
| tree files | 691 |
| changed vs parent | **2** |
| sha256-identical to parent | **689 / 689 other payload files** |
| drop files | 7 (`.ee`, `.ee.toc`, 5 profile/icon files) |
| drop non-`.ee` files identical to parent | **5 / 5** |
| banks | **not shipped** (bm-004c gate is RED — §4) |

Build steps as recorded in `receipt.json`:

    stage = bm-RC2/aaf (691 files, byte-identical)
    jointed parts module <- Builds/bm-RC3-parts (sha 17d98205bb2e, constraint_index 11/12 on
        batmobile_turret/batmobile_cannon)
    physicsc: 11 -> 13 constraints, 902,384 -> 903,008 B, hinges 11/12
    packed v0300_car_kensington_sportsmuscle_debug.ee (11,390,715 B),
        unpack matches 687 listed files (manifest gaps inherited)
    .toc: 705 records, root last, parts (16625904, 46300), physicsc (15655680, 903008)

## 2. The two changed files

Both under `models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/batmobile/`:

| file | parent sha256 | bm-RC3 sha256 | bytes | why |
|---|---|---|---|---|
| `sportsmuscle_vehicle_parts.vmodc` | 6e379e4c5716f15c82f3b8a557f6140b059b7157f2655215f05fa8a340e82560 | 17d98205bb2eeaf7148804f291a7852a03de6f2335e284d2ba9887b2524f0c11 | 46,300 | the jointed module from `Builds/bm-RC3-parts`: `batmobile_turret` (part 50) → `constraint_index` 11, `batmobile_cannon` (part 51) → 12; the other 59 rows byte-identical |
| `sportsmuscle.physicsc` | eda17906c1f81c7bd0fd5798653eeb178d3c3b71e6a659f98576aaf0f9c99536 | 9c1867d0b5050449e5a53cc5da82b191898b3362c74ee86bdbaa20743f776945 | 903,008 | two `hkpLimitedHingeConstraintData` objects appended at indices 11 and 12 |

Nothing else in the tree moved: the generator asserts the two parent hashes, copies the parts
module only after checking `Builds/bm-RC3-parts/receipt.json` names `bm-RC2` as its base and
carries exactly sha256 `17d98205…`, then refuses to write if any other file's sha256 differs.

### 2a. Why the physicsc is appended, not copied

`Working/Collision/batmobile_hinged.physicsc` is the **pre-collision** file (340,992 B, 13
constraints) — it is `Working/Collision/batmobile.physicsc` (340,368 B, 11 constraints) plus the
two hinges. bm-RC2's physicsc is the **collision build** (902,384 B, 11 constraints) with
B-10b (body world-collision from the Batmobile mesh) and B-10c (convex hull). Copying the hinged
file would silently delete B-10b/B-10c, so `bm_physicsc_hinges.append_objects()` is applied to
bm-RC2's file with the two 304-byte hinge blobs taken byte-for-byte from the hinged file.

Evidence this is the same bytes the hinged file carries (all asserted at build time, not narrated):

* the two appended blobs equal `constraints(batmobile_hinged.physicsc)[11]` and `[12]`, byte for byte;
* object count 431 → 432, constraints 11 → 13, both new objects
  `hkpLimitedHingeConstraintData`;
* the 11 inherited constraint classes are unchanged and every `hknpPhysicsSystemData` object
  (body entries / stations) is byte-identical to bm-RC2's — i.e. collision data untouched;
* `jc3hkx.py check --file` on the result: `check ok`; virtual-table residue 0, class-name
  markers intact.

Hinge values as re-read from the built file:

| index | part | axis | pivot (m, vehicle frame) | min .. max (rad) | (deg) |
|---|---|---|---|---|---|
| 11 | `batmobile_turret` | (0, 1, 0) | (0.000013, 0.876249, 0.333226) | −1.047198 .. 1.047198 | −60 .. 60 |
| 12 | `batmobile_cannon` | (1, 0, 0) | (0.000358, 1.702446, 0.017586) | −0.087266 .. 0.349066 | −5 .. 20 |

## 3. Packed payload and `.toc`

* `v0300_car_kensington_sportsmuscle_debug.ee`, 11,390,715 B,
  sha256 `12ad850cd92c6aae1eeaba7b4d877675c0446d0c5d8700f111f5468b3644abe8`
  (bm-RC2: 11,390,571 B).
* `.ee.toc` sha256 `d6d78bb8f07b9db945d86d6466e3bda16269fe548e2b866cbb8bbb32996541cd`,
  705 records — same record set and order as bm-RC2's, root `.epe` last, 26 offset-0
  (archive) records left at 0.
* Both overlays are **internal** — the .toc points into the `.ee`, which is what makes an
  override take effect (the re-pointed `vehicle_parts.vmodc` lesson):

      parts     offset 16625904, size 46300   (== the staged file's size)
      physicsc  offset 15655680, size 903008  (== the staged file's size)

* SmallPack → SmallUnpack round trip: 687 listed files come back sha256-identical to the staged
  tree (the 4-file manifest gap — wheel lod4/5 `.rbm` on disk but unlisted — is inherited from
  bm-RC2, not added here).

## 4. Banks: left out, and why

`Builds/bm-004c/verify/audio_004c.md` still reads:

    STATUS: 5/5 loudness gates pass, 2/3 loop-wrap gates pass; red: vehicles#279

So the card's condition holds and the drop ships **no** `sound/fmod_banks/*`. bm-RC2 shipped two,
and the receipt records them as deliberately dropped (so the omission is visible, not silent):

| path | bm-RC2 sha256 | in bm-RC3 |
|---|---|---|
| `sound/fmod_banks/vehicles.bank` | 76d67bcef81c8d297082b9cb026e9e995762fb2f72e3b2c2d7f5a1570e2f00a7 | no |
| `sound/fmod_banks/weapons.bank` | 5b8a7605a8b70ca211defa3c8856a1ab26b4276e11ecc46a4147af245f7a7d78 | no |

Consequence: on a dropzone that still has bm-RC2's banks installed, those two files stay as
bm-RC2 left them; where none are installed, the game uses the archives' own banks. Rolling the
banks in is a one-line change to `BANK_PATHS`/the drop copy once the #279 wrap is fixed.

## 5. The 7 drop files

| bytes | sha256 | path | owner |
|---|---|---|---|
| 11,390,715 | 12ad850c…44abe8 | `editor/…/v0300_car_kensington_sportsmuscle_debug.ee` | B-RC3 |
| 68,221 | d6d78bb8…6541cd | `editor/…/v0300_car_kensington_sportsmuscle_debug.ee.toc` | B-RC3 |
| 77,569 | 239d6b6d…550a6c | `profile/item.onlinec` | B-13 |
| 1,746,322 | 6dcdf0ce…c60bc4 | `profile/online.stringlookup` | B-13 |
| 168,174 | 9250e271…89cae6c2 | `profile/task.onlinec` | B-13 |
| 27,785 | 797391dc…7043cf3 | `settings/spawn_vehicle_defs.bin` | B-13c |
| 18,688 | 5096fb74…fae5058f | `textures/ui/vehicle_icons/v0300_car_kensington_sportsmuscle_debug.ddsc` | B-13 |

## 6. Checks actually run

`python Tools/scripts/bm_rc3.py --write` then `--check` (0 failures, 23 PASS lines):

1. receipt lists every drop file, 7 = 7 on disk; all 7 re-hashed;
2. `aaf` tree 691 files, every sha256 matches the receipt;
3. **exactly 2 changed vs bm-RC2** (`sportsmuscle_vehicle_parts.vmodc`, `sportsmuscle.physicsc`);
   **689/689 other payload files sha256-identical**; the receipt's parent hashes are the parent
   tree's own;
4. drop: 5/5 non-`.ee` files sha256-identical to bm-RC2; no bank present;
5. `.toc` 705 records, every non-zero record matches the `.ee`, root `.epe` last, both overlays
   internal with the staged sizes, no offset-0 record carrying new bytes (0 stale);
6. physicsc re-derives: 13 constraints, 11/12 `hkpLimitedHingeConstraintData`, turret pivot
   (1.3e-05, 0.876249, 0.333226), cannon axis (1, 0, 0); `jc3hkx.py check --file` → `check ok`;
7. installer rehearsals against simulated dropzones under `tmp/rc3_sim` (deleted afterwards):
   `-WhatIf` lists exactly 7 files + sha256 and writes 0; `(a)` clean dropzone Install → Verify
   7/7 → Rollback091 leaves 0 files; `(b)` decoy dropzone installs over an existing
   `profile/item.onlinec`, backs it up, and Rollback091 restores it byte-for-byte.

Not run, by the card's own rule: no install into the game, no launch, no bank gate work, no
visual/physics inspection in engine.

## 7. UNKNOWN (each with its settling file and a one-sentence check)

1. **Do the jointed parts module and the two hinge objects load together?** — settling file:
   `Research/PhaseQ/` probe run on this tree. Pilot-card check: spawn the Batmobile and look for a
   turret that moves independently of the hull instead of a static mesh.
2. **Do `constraint_index` 11/12 bind the parts the joints name (turret / cannon)?** — settling
   file: `Builds/bm-RC3/receipt.json` → `parts_module.joints` + the Q-3 hinge probe. Pilot-card
   check: rotate the turret yaw and the cannon pitch separately; each should move alone.
3. **Is the omitted banks' RED loop wrap audible?** — settling file:
   `Builds/bm-004c/verify/audio_004c.md` (`red: vehicles#279`). Pilot-card check: drive with no
   bank installed and listen for a wrapped/seamless engine loop rather than a click every cycle.
4. **Does the dropzone accept this `.ee` at the `_debug` leaf with the appended physicsc (no size
   change elsewhere)?** — settling file: Q-1a note in `Tools/scripts/bm_leaf.py`. Pilot-card
   check: the model appears under the Rebel Drop name with the jointed turret, not the vanilla
   Serpente.

## 8. Revert / reproduce

* Revert: delete `Builds/bm-RC3/` and `Tools/scripts/bm_rc3.py`; nothing else changed.
  `Builds/bm-RC2`, `Builds/bm-RC3-parts`, `Working/Collision/batmobile_hinged.physicsc` and
  `Tools/scripts/bm_rc2.py` are untouched (the overlay reads them, never writes).
* Reproduce: `python Tools/scripts/bm_rc3.py --write` (needs the pinned `bm-RC3-parts` module
  sha256 and `batmobile_hinged.physicsc`; the script refuses if either moves).

Budgets: model delta +624 B (physicsc only), texture delta 0 — inherited from bm-RC2 otherwise.
