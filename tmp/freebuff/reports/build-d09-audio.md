# D-09 · B-11 re-run — `Builds/bm-RC4-audio`

**STATUS: built, all five slots green.** 5/5 loudness within ±1 LU of the vanilla payload,
3/3 loop seams below −40 dBFS, 2 private bank copies at their original byte sizes, `.fmod_guids`
re-emitted byte-identically from the `.ee`, and the 45-GUID keep-audit event list resolved
24/45 in the build with the other 21 named per GUID as B-26 (donor `character`/`effects` banks).

Two numbers to lead with, because they are the point of this run:

| defect | before | after | how |
|---|---|---|---|
| `vehicles#279` loop seam | −39.68 dBFS (0.32 dB short of the card's −40) | **−74.75 dBFS** | phase trim 932 frames, derived by search |
| `weapons#408` loop seam | −30.87 dBFS at the true boundary (the −50.75 on record was a truncated window) | **−90.31 dBFS** | diag's −2.72 dB source gain + phase trim 544 frames |

Both are *derived here*, and the gate reproduces each derivation to the sample
(`gate_agrees: true` for both). bm-004c left 279 red and never phase-fixed 408 at all.

## 1. What was built

`Builds/bm-RC4-audio/` — a private tree on bm-001's identity `aaf` (no `.ee`/`.toc` change):

| file | what |
|---|---|
| `banks/vehicles.bank` | 210,781,376 B, sha256 `aab92ca03f8cbbfe…`, 649 samples, **size unchanged** |
| `banks/weapons.bank` | 177,586,080 B, sha256 `d05b74ed9111ecad…`, 1,228 samples, **size unchanged** |
| `aaf/.../v0300_..._civilian_01.ee.fmod_guids` | 758 B, v1, banks `vehicles/character/effects`, **45 GUIDs**, sha256 `44ca55635ad83fdb…` |
| `install.ps1` | `Install` / `Verify` / `Rollback091` / `Status`, every bank sha pinned |
| `receipt.json`, `bank_set.json`, `events.json` | the build record, the bank set, the 45-GUID resolution |
| `verify/audio.json` + `audio.md` | the gates below |

5 mapped slots, 1,877 samples, both files byte-length identical to the vanilla banks. The
splice is the same one bm-004 shipped: payload rebuilt by `bm_audio.payload()` from the T-16
map, written at the sample's own `data_offset`, metadata untouched.

The `.fmod_guids` is regenerated from the `.ee`'s inner file and asserted byte-identical
(`fmod_guids_of()` refuses otherwise), so the event pins need no `.ee` edit — that part of
B-11 is carried over, not assumed.

## 2. The two fixes

### `vehicles#279` — chassis-creaks loop, phase derived

The payload is the source tiled with an equal-power crossfade, so the seam depends on which
sample of the source the cycle starts at. bm-004c dropped 408 frames and reached −39.68. This
searches the phase and keeps the loudness at the map's −20.45:

| drop (frames) | seam dBFS | mono LUFS | clip % |
|---:|---:|---:|---:|
| **932** | **−74.75** | −20.45 | 0.00 |
| 931 | −52.92 | −20.45 | 0.00 |
| 933 | −51.52 | −20.45 | 0.00 |
| 930 | −46.67 | −20.45 | 0.00 |

A plateau, not a knife-edge: ±1 frame stays ≤ −46 dBFS.

### `weapons#408` — minigun loop, gain + phase

The −2.72 dB source gain from `Builds/bm-RC1/verify/audio_diag.md` (factor 0.731139) is applied
as a source gain, and the slot's loudness oracle becomes the diag's own post-fix measurement
(−8.31 mono / −5.30 stereo, corroborated by bm-004c) rather than T-16's unfixed −5.87 — that is
the one place where a fix legitimately retargets the map's number, and `bm_audio` now records it
as `fix_expect_lufs`. Then the same phase search: 544 frames, seam −90.31.

Worth recording: the vanilla minigun payload's own seam is **−5.36 dBFS** — the donor loop is
the noisy one; our rebuilt loop is 85 dB quieter at the join.

## 3. Gates, per sample

| slot | name | LUFS built / vanilla | Δ LU | loudness | seam (payload bytes) | vanilla seam | p99 step | loop |
|---|---|---|---:|---|---:|---:|---:|---|
| `vehicles#7` | `jc3_veh_door_tank_open_03` | −21.85 / −21.85 | +0.00 | PASS | n/a | n/a | −22.27 | one-shot |
| `vehicles#98` | `jc3_veh_door_tank_close_01` | −11.02 / −11.02 | +0.00 | PASS | n/a | n/a | −10.42 | one-shot |
| `vehicles#151` | `jc3_veh_land_premium_nitro_loop` | −10.33 / −10.33 | +0.00 | PASS | −16.36 | −19.52 | −10.99 | PASS |
| `vehicles#279` | `jc3_veh_lave_chassis_spin_creaks_loop_fast` | −20.45 / −20.25 | −0.20 | PASS | **−74.75** | −59.68 | −46.07 | PASS |
| `weapons#408` | `jc3_wpn_minigun_fire_close_loop_04` | −5.30 / −5.30 | +0.00 | PASS | **−90.31** | −5.36 | −11.54 | PASS |

- **decode** 5/5, **length** 5/5 (Δ span 0 frames), **loudness** 5/5, **loop** 3/3, **tail** 3/3.
- `#151` passes on the card's outlier clause: −16.36 dBFS is above the −40 threshold but *better*
  than the payload's own p99 interior step (−10.99), so it is not a click. The vanilla seam
  (−19.52) is worse than ours.
- The minigun's loudness error in bm-RC1 (+2.33 LU) is gone: Δ +0.00.

### Measurement domain (why two numbers exist)

An FSB5 PCM record carries a byte header before its PCM (32–60 B = 16–30 frames here), and
vgmstream decodes the record from its first byte. So `v04_audio`'s record-domain step compares
the payload's last sample with a **metadata word**: its magnitudes come out at **+21 to +35 dBFS**
(vehicles#7 29.46, #98 21.33, #151 25.19, #279 27.94, #408 34.92; vanilla 35.90 / 36.57 / 24.73 /
32.31 / 20.93). A step larger than full scale is only possible because the "first sample" is a
header byte pair — which is the proof that this domain cannot measure a loop.

The gate therefore measures the payload as written (`record[hlen:]`), and the record-domain
numbers stay printed in `verify/audio.md` beside the vanilla ones. Both the write and the check
use the same rule, and the derivation oracle (`gate_agrees`) is what keeps them honest.

## 4. The bank set — "10 banks were never absent"

`Research/BatmobileGrab/AUDIO_BANKS.json` (G3‑14) re-tested the old "90 events in 10 banks absent"
claim against the whole install, and this build records the result rather than the claim:

- **10 claimed / 10 found / 0 absent**, 90 event rows — each of the ten named in
  `bank_set.json → claims.banks` with its verdict (`BML_Impacts`, `BML_Sonar`, `CHR_BatmanAlerts`,
  `CHR_BatmanDisruptor`, `OBJ_Rolling_Objects`, `UI_InGame`, `VEH_Tank_Heavy`,
  `VEH_Tank_Missiles`, `VFX_Tank_Explosion`, `BML_Batmobile_Subjective` — all FOUND).
- **29 referenced banks / 29 present as `AkBank` exports / 0 present only as a file / 0 absent.**
- Install scan: 4,145 packages scanned, 4,145 readable, 2,325 with `AkBank`; 34,497 `AkBank`
  exports, 117 payloads read (157,819,974 B); 15 `.bnk` files (14 `BKPK`, 1 `BKHD`).

Those banks are **evidence, not payload**: they are Wwise (BKHD/HIRC) sources inside `.upk`
packages, and JC3 loads FSB5 banks — copying them in would ship a non-loadable file. So the
private copies are the two JC3 banks whose samples were mapped, and the receipt says exactly
which found banks are not shipped and why.

One number I am *not* publishing as clean: `references.banks[].event_rows` sums to **1173**,
while `AUDIO_BANKS.md`'s table states **361 event rows over 29 banks**. No field says what the
JSON counts. `bank_set.json` records it as `event_rows_field_sum` with that discrepancy in the
note, not as "event rows".

## 5. The event list (audio keep audit)

`Working/Audio/jc3_event_roles.json` — the 45 GUIDs the `.fmod_guids` pins:

| bank | GUIDs | resolved in the build | status |
|---|---:|---:|---|
| `vehicles` | 24 | 24 | `EVTS` + `TLNB` present in the built bank |
| `character` | 2 | 0 | donor bank, not built — **B-26** |
| `effects` | 19 | 0 | donor bank, not built — **B-26** |
| **total** | **45** | **24** | 45/45 present in the re-emitted `.fmod_guids` |

The 21 unresolved are the keep-audit's "still donor" set: `effects.bank` and `character.bank` are
shared by every vehicle in the game, so replacing them per-vehicle needs an override
(`SDynamicAttachedEffect` per entity or a per-entity bank) and **no such mechanism is decoded**.
That is B-26, not this step, and it is named per GUID in `events.json` (`status`,
`mapped_slot`, `in_fmod_guids`).

## 6. Checks actually run

| check | result |
|---|---|
| `b11_rc4_audio.py --write` | rc 0 — banks, `aaf`, `install.ps1`, `receipt.json`, `bank_set.json`, `events.json`, manifest, `verify/*` |
| `b11_rc4_audio.py --check` | **PASS** — re-derives payloads/banks/records, re-measures every gate: `ALL GREEN: 5/5 loudness, 3/3 loop, 2 banks, events 24/45 resolved` |
| `v04_audio.py --check` (`Builds/bm-RC1`) | PASS — the RC1 journal still reproduces; its own verdict is unchanged: RED on loudness (4/5, max 2.33 LU) and loop (1/3 clicks) |
| `bm_audio.py --check` (`Builds/bm-004`) | **FAIL on 4 paths, all `installer.dropzone_at_build`** — the live game folder now holds both banks (mtimes 2026‑11‑02 21:48:39), so a probe of the environment no longer equals the manifest written on Nov 2 |
| derivation vs `bm_bank_manifest.json`, probe excluded | **DERIVED_FIELD_DIFFS 0**, slot `payload_sha256` list identical — the refactor changed no byte of bm-004's derivation |

That last row is the honest reading of the `bm_audio --check` failure: the check compares a
probe of the live install, not a derivation, and that probe drifted when test installs put
`vehicles.bank`/`weapons.bank` into the game directory. The derivation itself is unchanged.

Environmental note: **C: is 100 % full (29 MB free)** and `/tmp` is on it, so the two
`--check` runs first died with `No space left on device` while writing the re-derived banks to a
610 MB temp tree. `TMPDIR`/`TEMP`/`TMP` were pointed at `E:/…/tmp/tmpdir` and the stale
`/tmp/bm_audio_check_*` trees removed; both checks then ran clean. Anyone re-running these
scripts on this machine needs the same `TMPDIR`.

## 7. Files changed, and how to revert

| file | change |
|---|---|
| `Tools/scripts/b11_rc4_audio.py` | new: derives both fixes, builds the tree through `bm_audio`, records bank set + events, runs the gates |
| `Tools/scripts/bm_audio.py` | additive `SOURCE_FIXES` + `configure()` hook (empty by default), stdlib-`wave` fallback in `mono_48k`, and a memory-lean splice (no `bytes(bank)` copies; banks written and re-read one at a time) |
| `Builds/bm-RC4-audio/` | new tree (banks, aaf, installer, receipt, bank_set, events, verify) |
| `Working/Audio/bm_bank_manifest_rc4.json` | new manifest (bm-004's `bm_bank_manifest.json` untouched) |
| `tmp/freebuff/reports/build-d09-audio.md` | this report |

Revert: delete the tree, the `_rc4` manifest and the new script; `bm_audio.py`'s changes are
behaviour-neutral with `SOURCE_FIXES` empty (proved by `DERIVED_FIELD_DIFFS 0`), so reverting it
is only needed to drop the hook. Nothing was installed, no dropzone was written, and no game
process was started.

## 8. UNKNOWNs and what is still red

- **Whether the engine loops these payloads at the file wrap.** No slot carries an FSB5 loop
  field (`loop_start`/`loop_end` null on all five), so the wrap is the only boundary the data
  carries; the vanilla payload at the same index is the oracle that the boundary is the loop.
- **The 21 donor GUIDs' audio** — needs B-26's per-entity override; the mechanism is undecoded.
- **`T-AU1`'s event→parameter edge** — still UNKNOWN; the build keeps `LandAudio`'s
  `min_rpm` 1000 / `max_rpm` 10000 and maps in the bank.
- **How any of this sounds in play** — phase Q; the test ban is in force and nothing was
  installed or driven.
- **`bm_audio.py --check` on bm-004 is red for the live-path probe** (see §6). Not repaired
  here: re-pinning the probe would hide that the dropzone state changed.
- **`1173` vs `361` event rows** in `AUDIO_BANKS.json` vs its own `.md` — recorded, unexplained.
