**STATUS: DONE (with one gate still RED) — the two V-04 derived fixes are applied in the new private tree `Builds/bm-004c`; all **5/5 loudness gates pass** and **2/3 loop-wrap gates pass**. `vehicles#279` still clicks: wrap **-28.27 dBFS** as stored (**-39.68 dBFS** on the payload alone) against the -40 dBFS limit.**

# V-04 fixes applied in `Builds/bm-004c`

## What was applied

`Builds/bm-RC1/verify/audio_diag.md` derived two WAV-level fixes. They were applied to the build's **inputs in memory** (the source WAVs under `E:/Modding/_shared/gamedata/BmAKgrab/audio/wav/` were not edited), then both payloads were rebuilt through `bm_audio.payload()` with the manifest's own loop-fill gain and the build's own re-level loop, and spliced into copies of `bm-RC1`'s two banks.

| slot | derived fix | source WAV |
|---|---|---|
| `weapons#408` `jc3_wpn_minigun_fire_close_loop_04` | gain **0.731139** (-2.72 dB) | `098BBFE1.wav` |
| `vehicles#279` `jc3_veh_lave_chassis_spin_creaks_loop_fast` | drop the first **408 frames** (pre-roll trim) | `0C69336B.wav` |

## Files written

| file | what |
|---|---|
| `Tools/scripts/v04_audio_004c.py` | applies the fixes, rebuilds both payloads, splices the banks, re-runs the V-04 gates; `--write` / `--check` |
| `Working/Audio/bm_bank_manifest_v2.json` | copy of `bm_bank_manifest.json` with only the two slots' `measured` + `payload_sha256` changed |
| `Builds/bm-004c/banks/weapons.bank` | 177,586,080 B (copy of bm-RC1's bytes, 1 payload spliced) |
| `Builds/bm-004c/banks/vehicles.bank` | 210,781,376 B (copy of bm-RC1's bytes, 1 payload spliced) |
| `Builds/bm-004c/verify/audio_004c.json` / `.md` | per-sample gates |
| `tmp/freebuff/reports/audio-fix-tree.md` | this report |

`Builds/bm-RC1` was opened read-only (its banks still carry their 2 Nov timestamp); `install.ps1` was not run, nothing was copied to a dropzone, and no game process was started.

## Verbatim commands and output

```
python Tools/scripts/v04_audio_004c.py --write
wrote Working/Audio/bm_bank_manifest_v2.json, Builds/bm-004c/banks, Builds/bm-004c/verify/audio_004c.*
5/5 loudness, 2/3 loop-wrap, red: vehicles#279
  vehicles#279: sha_matches=True mono=-20.45 stereo=-20.45 gain=-6.95
  weapons#408: sha_matches=True mono=-8.31 stereo=-5.3 gain=1.13

python Tools/scripts/v04_audio_004c.py --check
CHECK PASS - 5/5 loudness, 2/3 loop-wrap, red: vehicles#279
```

## Per sample

Loudness = BS.1770-4 gated integrated LUFS as stored, built vs the vanilla payload at the same bank+index (±1 LU). Wrap = `v04_audio.seam` end→start step at the file wrap, the only loop boundary the data carries.

| slot | loop | built LUFS | vanilla LUFS | Δ LU | loudness | wrap dBFS | payload wrap | p99 step | loop click |
|---|---|---|---|---|---|---|---|---|---|
| `vehicles#7` door_tank_open_03 | no | -21.85 | -21.85 | +0.00 | PASS | -29.73 | -30.02 | -22.27 | n/a (one-shot) |
| `vehicles#98` door_tank_close_01 | no | -11.02 | -11.02 | +0.00 | PASS | -11.65 | -12.01 | -10.42 | n/a (one-shot) |
| `vehicles#151` premium_nitro_loop | yes | -10.33 | -10.33 | +0.00 | PASS | -18.18 | -8.67 | -10.99 | PASS (inside its own step distribution) |
| `vehicles#279` chassis_spin_creaks_loop_fast | yes | -20.45 | -20.25 | -0.20 | PASS | **-28.27** | **-39.68** | -46.01 | **RED: click** |
| `weapons#408` minigun_fire_close_loop_04 | yes | -5.30 | -5.30 | +0.00 | PASS | -61.21 | -50.75 | -11.54 | PASS (below -40) |

### The two fixes against the diag's predicted values

| slot | payload sha256 = predicted | mono LUFS (want) | stereo LUFS (want) | fill gain | padded frames (want) |
|---|---|---|---|---|---|
| `vehicles#279` | yes (`117f8aa2…`) | -20.45 (-20.45) | -20.45 (-20.45) | -6.95 | 149,911 (149,911) |
| `weapons#408` | yes (`12b8cf4e…`) | -8.31 (-8.31) | -5.30 (-5.30) | 1.13 | 80,213 (80,213) |

The loudness gate that was RED on bm-RC1 for `weapons#408` (+2.33 LU) is now **+0.00 LU**.

## The gate that is still RED, and why

`vehicles#279`: after the 408-frame pre-roll trim the wrap is **-28.27 dBFS** on the decoded record and **-39.68 dBFS** on the payload alone (the 32-byte record header decodes as its first 16 frames, so the two domains differ by the header). The payload's own p99 interior step is -46.01 dBFS, i.e. the seam is **5.7 dB worse** than the payload's normal steps, so under V-04's rule (worse than -40 dBFS **and** an outlier against p99) it is a click. The trim moved the seam from -17.50 to -39.68 dBFS (22.18 dB better) but did not clear the threshold.

`audio_diag.md` predicted **-60.77 dBFS** for this same rebuild. The payload sha256 matches the diag's predicted sha exactly, so the bytes are the predicted ones, yet its seam does not reproduce: the -60.77 figure is not reproducible with `v04_audio.seam` on either the full record or the payload alone. That discrepancy is UNKNOWN (see below) and is reported rather than papered over.

## Oracles / checks that ran

- `--write` then `--check`: `CHECK PASS`, verify `.json`/`.md` byte-identical on re-derivation, and both fixed slots' `payload_sha256` in `bm_bank_manifest_v2.json` equal the bytes rebuilt in memory.
- Bank sizes unchanged (177,586,080 / 210,781,376 B) — only the two payload byte ranges differ; all other samples come from bm-RC1's own bytes.
- 5 slots / 1,877 samples across the two banks decoded with `v04_audio.decode`; no install, no game.

## UNKNOWNs

- **Why `vehicles#279` is still at -39.68 dBFS when the diag predicted -60.77 dBFS for the same payload.** Tried: recomputing `v04_audio.seam` on the decoded record and on the header-shifted payload; the payload sha matches the diag's predicted sha, so this is a measure/prediction mismatch, not a different build. Where it would be answered: the diag's own seam computation (not in the repo as a script).
- **The loop region.** No slot carries loop metadata (manifest `loop_start`/`loop_end` null, vgmstream prints no loop line), so the file wrap is the only boundary measured.
- **Whether the engine loops these slots at all, and how they sound in play** — phase Q; the test ban is in force.
- **`weapons#408` event identity.** No GUID (`slot_confidence: candidate`); the vanilla payload at the same bank+index is the oracle.

## Compromises

None against BmAK lore. One V-04 loop gate (`vehicles#279`) remains RED because the derived fix clears the loudness/duration side but not the -40 dBFS click rule; a further trim offset would be a new derivation, not this card's fix, so it was not invented here.
