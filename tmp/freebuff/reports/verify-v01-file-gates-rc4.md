# V-01 file gates on `Builds/bm-RC4` (the tree B-14 produced)

Date: 2026-11-07. Offline, read-only on the build: V-01 wrote **only**
`Builds/bm-RC4/verify/files.md` and `files.json`. Nothing was installed, nothing launched, no file
inside `aaf/` or `drop/` was modified.

```
python Tools/scripts/v01_rc4.py --write   # 11 GREEN, 1 RED  -> WRITE_EXIT=1
python Tools/scripts/v01_rc4.py --check   # PASS: verify/files.md + files.json match  -> CHECK_EXIT=1
python Tools/scripts/status_audit.py --write   # STATUS.md was stale; regenerated once
```

**Verdict: 11 of 12 gates GREEN, 1 RED — and the red is the artifact, not the gate.** The `.ee` in
`Builds/bm-RC4/drop` is **11,225,532 B**, two bytes short of the 11,225,534 B build-d13 recorded,
and `receipt.json` is **215,445 B**, not 211,711 B. Everything else in the pinned set reproduces
exactly.

## 1. What the gates measure

| gate | result | number, as measured |
|---|---|---|
| `tree` | **RED** | aaf **696** files (receipt 696), `.toc` **714** records, drop **9** files, `.ee` **11,225,532 B** (**−2** vs pinned 11,225,534), `.ee.toc` **68,675 B**, `install.ps1` **6,535 B**, `receipt.json` **215,445 B** (**+3,734** vs pinned 211,711), schema **2** |
| `toc` | GREEN | **225** records differ from the vanilla donor `.ee` (receipt 225); **26** at offset 0, **19** of them size-only `@files.xml` stubs; offset-0 records carrying non-vanilla bytes: **0** |
| `internal` | GREEN | root `.epe` **17,713,812 / 134,072**; `sportsmuscle.physicsc` **15,993,844 / 340,368**, sha256 `0164936b…9399323` (B-10's pin); `batmobile_health_medium.vmodc` **23,252,584 / 3,741**; lights module **7,105 B** internal at **16,500,744**; `vehicle_parts` @16,401,428; `_custom_land_global` @16,543,640; `_land_engine` @16,574,768 |
| `budget` | GREEN | model non-vanilla **4,791.3 KB** of **4,915** (reachable 6,895.9 KB, 181 `.rbm`, re-measured from the tree); texture **5,380.9 KB** of **7,065** (33 textures, `hard_ok`); allocator figure **4,648.0 KB present and OVER its own sub-allocation — reported, not hidden** |
| `aafdiff` | GREEN | **120** files differ from bm-RC2 = **20** merge-overlay + **2** stage + **98** base-lineage, **0** unexplained (receipt 120/120) |
| `ledger` | GREEN | **199** rows, **35** edits over **16** rows; STATUS.md **145 / 216** evidenced, **15 / 216** blocked; `status_audit.py --check` exit 0 |
| `handling` | GREEN | `t1_handling.json` **14** entries → **17** numeric member values, **17/17** read back from the `.toc` slice (1 composition-only entry not written); test-085 receipt `edits` = **35** |
| `spec` | GREEN | `spec_check.py --lights Working/Appearance/build_lights` exit **0**: "checked 24 blocks over 8 lamp parts; spec mismatches 0"; independent CarLight census **24 blocks / 8 lamp parts** |
| `parts` | GREEN | `jc3parts.py check` exit **0** ("40 part indices agree…"); parts module decoded **from the `.toc`** = **59** parts, matching `Working/Parts/bm_vehicle_parts.json` (59) |
| `adf` | GREEN | **15** edited `.vmodc` re-read with `jc3adf.py info`, **15/15** byte-equal to their `.toc` slice, 0 bad |
| `epe` | GREEN | ConvertProperty round trip: base **7,084** → merged **9,025** XML lines, re-export **byte-identical** |
| `readback` | GREEN | **695** internal `.toc` slices equal their aaf file (**0** differ); lights module **24** rows, **2** two 70° beams per side, reaches **[18, 18, 60, 60]** |

Commands: the per-gate commands are the ones printed in `Builds/bm-RC4/verify/files.md`
(`spec_check.py --lights …`, `jc3parts.py check`, `status_audit.py --check`, `jc3adf.py info <module>`,
`ConvertProperty --e/-i`, plus the in-process re-computations). Nothing was piped through `head`/`tail`
for the exit statuses: each is echoed unpiped (`WRITE_EXIT`, `CHECK_EXIT`).

## 2. The one red, and what it is

`Builds/bm-RC4` was **rebuilt by another job while this gate ran**. Observed directly: the `.ee`
first read as 0 B, then vanished, then settled at 11,225,532 B — `os.path.getsize` and `open()`
raised `FileNotFoundError`/`PermissionError` on files under `aaf/` during the same window. V-01 does
not write there.

The settled tree is internally consistent: the receipt's 9 drop entries rehash, all 696 aaf hashes
match, 714 `.toc` records match the `.ee` directory, and 225/26/19 reproduce. Only two pinned
figures differ:

| fact | pinned (build-d13) | measured now | delta |
|---|---:|---:|---:|
| `drop/…_debug.ee` | 11,225,534 B | **11,225,532 B** | **−2 B** |
| `receipt.json` | 211,711 B | **215,445 B** | **+3,734 B** |

A 2-byte `.ee` delta with an unchanged record count, unchanged `.toc` size and an unchanged
`physicsc`/`.epe`/health/parts layout is not explainable from V-01's read-only position, and I will
not guess at it. It needs the rebuild's own receipt diff. **Re-run `v01_rc4.py` against the tree once
the rebuild job is quiet; if the 2 bytes are intended, the pinned fact in the brief is the thing to
update, not the gate.**

Also worth stating rather than glossing: the lights module's `.toc` offset in this merged tree is
**16,500,744**, not the **16,499,504** in the brief. The size is exactly **7,105 B** and the record
is internal; the +1,240 B is the merged tree's layout (D-03's figure is `bm-RC4-lights`, which packs
one file earlier). The value in the brief belongs to the stage tree, not to `bm-RC4`.

## 3. Two counts where the brief and the files disagree

- **Handling: 14 entries, not 15.** `Working/Translation/t1_handling.json` carries 14 edit entries;
  three of them name several members at once (`steer_input_power_pc/durango/orbis`,
  `front/rear.min_time_to_block`, `grip_multiplier/extra_top_speed`), which is **17** numeric member
  writes plus **1** composition-only entry ("30000 (composition, unchanged)") that is not written.
  All 17 read back from the packed `.toc`. test-085's receipt indeed holds **35** edits, so the
  "must match the 35 already in test-085" half is true; the "15" is not the file's count.
- **Parts: 59, not 61.** The `.toc`-decoded parts module has 59 parts and `bm_vehicle_parts.json`
  says 59. The 61 in v01_rc2 was that tree's B-04R figure; this tree's own manifest is the
  expectation.

## 4. Deliberately not gated

`t_boost_rows.py` and `t_vnf_six.py` were **not run**: both pin a 198-row ledger and RC4 has 199
(correction 8396). Gating on them would have produced two reds that say nothing about this tree.

## 5. Files touched, and how to revert

| file | change | revert |
|---|---|---|
| `Tools/scripts/v01_rc4.py` | new gate script (12 gates, `--write`/`--check`, byte-compares the generated page) | delete the file |
| `Builds/bm-RC4/verify/files.md`, `files.json` | new: the per-gate numbers above, generated | delete the two files |
| `STATUS.md` | regenerated by `status_audit.py --write` because the on-disk copy was stale (76 insertions / 36 deletions vs HEAD); numbers unchanged at 145/216 and 15/216 | `git checkout -- STATUS.md` |

Nothing else changed. `Builds/bm-RC4/aaf`, `drop/`, `install.ps1` and `receipt.json` were read only.

## 6. Limits

- The gates are static: they prove the bytes, not that the car loads. Runtime stays Q-1/Q-2/Q-3.
- The `tree` red is **unresolved**: it is recorded here, in `verify/files.md` and in `files.json`,
  and the script exits 1 so a caller cannot mistake the tree for green.
- Textures are gated on D-04's ledger figure (5,380.9 KB, `hard_ok`) and the allocator
  over-allocation is reported, but 12 of 23 texture rows remain unfaithful — the tree is still
  `complete: false` for that reason (build-d13 §5), which V-01 does not change.
- `.wtunec` files are covered by the byte-equality of every internal `.toc` slice, not by
  `jc3adf.py info` (the reader is for `.vmodc`); the `.epe` is covered by the ConvertProperty round
  trip.

Updated by review 8399: rewritten for the real RC4 counts (696/714/9/225/26/120, model 4,791.3,
texture 5,380.9) and told not to gate on the two 198-row pins. Measured: 11/12 green; the `.ee` is
2 B and the receipt 3,734 B away from the pinned figures after a concurrent rebuild.
