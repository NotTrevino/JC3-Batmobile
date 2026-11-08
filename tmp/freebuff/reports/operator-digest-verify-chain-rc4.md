# Operator digest — RC4 verification chain

Build: `Builds/bm-RC4`. Six reports, each read only in its first 40 lines; every figure below is
copied from those lines. No figure was recomputed, and nothing outside those six files was read.

| gate | figure | verdict | report path |
|---|---|---|---|
| V-01 `tree` | `.ee` **11,225,532 B** (**−2** vs pinned 11,225,534); `receipt.json` **215,445 B** (**+3,734** vs pinned 211,711) | **FAIL** | `tmp/freebuff/reports/verify-v01-file-gates-rc4.md` |
| V-01 `toc` | **225** records differ from the vanilla donor (receipt 225); **26** at offset 0, **19** of them size-only `@files.xml` stubs; offset-0 records carrying non-vanilla bytes: **0** | PASS | same |
| V-01 `internal` | root `.epe` **17,713,812 / 134,072**; `sportsmuscle.physicsc` **15,993,844 / 340,368**; lights module **7,105 B** internal at **16,500,744** | PASS | same |
| V-01 `budget` | model non-vanilla **4,791.3 KB** of **4,915**; texture **5,380.9 KB** of **7,065** (33 textures); allocator **4,648.0 KB** present and OVER its own sub-allocation | PASS | same |
| V-01 `aafdiff` | **120** files differ from bm-RC2 = **20** + **2** + **98**, **0** unexplained | PASS | same |
| V-01 `ledger` | **199** rows, **35** edits over **16** rows; STATUS.md **145 / 216** evidenced, **15 / 216** blocked | PASS | same |
| V-01 `handling` | **17/17** numeric member values read back from the `.toc` slice | PASS | same |
| V-01 `spec` | "checked 24 blocks over 8 lamp parts; spec mismatches 0" | PASS | same |
| V-01 `parts` | parts module **59** parts, matching `Working/Parts/bm_vehicle_parts.json` (59) | PASS | same |
| V-01 `adf` | **15/15** edited `.vmodc` byte-equal to their `.toc` slice | PASS | same |
| V-01 `epe` | base **7,084** → merged **9,025** XML lines, re-export **byte-identical** | PASS | same |
| V-01 `readback` | **695** internal `.toc` slices equal their aaf file; lights reaches **[18, 18, 60, 60]** | PASS | same |
| V-02 silhouette | side **99.9004 %**, front **100.0691 %**, top **99.9247 %** | PASS | `tmp/freebuff/reports/verify-v02-geometry-poses-rc4.md` |
| V-02 census | **59 parts, 19 distinct damage types**, 59/59 resolve, indices 1 and 2 absent | PASS | same |
| V-02 interaction | **77/77** in band, distance **0.0577–0.1461 m**, worst excursion **0.0000 m** | PASS | same |
| V-02 collision | shape **0.000000 m**; placement **[0.0005, 0.0000, 0.0025] m = 0.25 cm**; **5 hulls**; **0 of 54** slots free; **2 of 3** BmAK boxes have no shape instance | PASS (shipped bytes only — on payload `0164936b928f821c…9399323`, not in RC4, **NOT MET**) | same |
| V-03 G1 points | 9 `SWeaponPoint`, 0 part refs dangling | PASS | `tmp/freebuff/reports/verify-v03-wiring-rc4.md` |
| V-03 G2 ids | **4 occurrences of `4DAE31AE=FFFF05DA`** resolve to no object (78 objectid references → 452 objects) | **FAIL** | same |
| V-03 G3 refs | **6 dangling** of 32 asset paths + 7 non-base `.vmodc` (etune 2/3, ftune 1/3, model_xml 0/1, pfx 0/1, wtune 6/7, ctune 17/17) | **FAIL** | same |
| V-03 G4 audio | `.ee.fmod_guids` byte-identical (758 B); **45/45** present, **24** resolved, **21** declared donor, 0 missing | PASS | same |
| V-03 G5 drop | item 1621485476 → `_debug.ee` + `.toc` + 18,688 B icon | PASS | same |
| V-04 loudness | **5/5** within 1 LU of the vanilla event | PASS | `tmp/freebuff/reports/verify-v04-audio-rc4.md` |
| V-04 loop wrap | **2/3** below the -40 dBFS rule (**vehicles#279 RED**) | **FAIL** | same |
| V-04 events | **24/45** events resolved; `vehicles.bank` 210,781,376 B, `weapons.bank` 177,586,080 B, both receipt-matched | PASS | same |
| V-04 length / decode / tail | **5/5** within 1 frame of the source span; decode GREEN, tail GREEN | PASS | same |
| V-05 coverage | **28 checks parsed, 27 predicted, 0 blocked, 1 excluded** (battle variant, by D-2) | PASS | `tmp/freebuff/reports/verify-v05-predictions-rc4.md` |
| V-05 `t_boost_rows` | **21/21**, exit 0 | PASS | same |
| V-05 `t_vnf_six` | **87/87**, exit 0, sha pin `220dead9…` unchanged | PASS | same |
| V-05 `v05_driving` | **34/34**, exit 0, **T-ST7 miss still RED**: built **0.80 s low / 0.60 s high**, goal **0.250 / 0.091 s** | PASS (miss still printed) | same |
| V-06 cases | six cases matched their expected exit code: Status 0, WhatIf 0, Install empty 0, Install over installed 0, decoy 0 with Rollback, guard negative **2** | PASS | `tmp/freebuff/reports/verify-v06-install-dry-run-rc4.md` |
| V-06 artifact | `install.ps1` **6,535 B**, sha256 `b4589d40…5382`; `receipt.json` **schema 2**, **9 files**; `.ee` **11,225,533 B**; `.toc` **68,675 B** | PASS | same |
| V-06 record | `Builds/bm-RC4/verify/dropzone_sim.md`; `--check` re-ran all eight probes, byte-for-byte, exit 0 | PASS | same |

## Three lines

**What failed.** V-03 as a gate (**7 dangling values**: G2's four `4DAE31AE=FFFF05DA` `SAttachedEffect`
"Fire" refs and G3's six donor asset paths), V-01's `tree` (**`.ee` −2 B, `receipt.json` +3,734 B**),
V-04's loop wrap (**vehicles#279**, 2/3), and V-05's **T-ST7 miss**, still printed **RED** on every run.

**What is unknown.** The `.ee` size is quoted three ways in these lines — **11,225,532 B** (V-01),
**11,225,533 B** (V-06 receipt and built file), **11,225,534 B** (the pinned and brief values) — and
V-06 also reports the brief's installer hash as **32 hex characters**, so which number is the artifact
is not settled by these files; V-02's collision PASS holds only for the RC4 bytes, while the same gate
is **NOT MET** on payload `0164936b928f821c…9399323`, which is not in the tree.

**What blocks the first in-game test.** The two open reds — V-03's `verdict FAIL, dangling 7` and V-01's
`tree` — plus V-05's own line **"Nothing was tested in / game; the test ban stands"** (it wraps across two
lines in the source): no figure in this chain is yet a game observation, so there is nothing for an
in-game test to confirm against.
