STATUS: DONE - both V-04 red gates diagnosed; 2/2 root causes located in the build's payload rule; fixes derived with the build's own `bm_audio.payload` and NOT applied. `Tools/scripts/v04_diag.py --check` passes (145 lines reproduce byte-for-byte from the RC banks and the WAV sources, rc=0). No game, no install, no bank/WAV/manifest written.

## Files written

- `Tools/scripts/v04_diag.py` - new `--write` / `--check` generator. Read-only against the build.
- `Builds/bm-RC1/verify/audio_diag.md` - the diagnosis (145 lines).
- `tmp/freebuff/reports/v04-red-diagnosis.md` - this report.

Nothing else was modified: `Builds/bm-RC1/verify/audio.json|md`, `Working/Audio/bm_bank_manifest.json`, `Working/Translation/t12_audio_map.json` and both source WAVs are untouched (the manifest diff in the diagnosis is a proposal only).

## Command and verbatim output

```
$ python -m py_compile Tools/scripts/v04_diag.py; echo "compile rc=$?"; python Tools/scripts/v04_diag.py --write; echo "write rc=$?"; python Tools/scripts/v04_diag.py --check; echo "check rc=$?"
compile rc=0
wrote Builds/bm-RC1/verify/audio_diag.md: 145 lines
write rc=0
PASS: Builds/bm-RC1/verify/audio_diag.md reproduces from the RC banks and WAV sources (145 lines)
check rc=0
```

Tamper test (one digit changed in the committed text, then restored):

```
$ python Tools/scripts/v04_diag.py --check      # after editing -16.95 -> -16.96
FAIL: line 8: "- `vehicles#279` loop: wrap step **-16.95 dBFS** vs the -40 dBFS limit ..." != "- `vehicles#279` loop: wrap step **-16.96 dBFS** vs the -40 dBFS limit ..."
tamper check rc=1
$ cp tmp/freebuff/scratch/audio_diag.bak Builds/bm-RC1/verify/audio_diag.md; python Tools/scripts/v04_diag.py --check
PASS: Builds/bm-RC1/verify/audio_diag.md reproduces from the RC banks and WAV sources (145 lines)
restored check rc=0
```

## What the gate measures

`bmak_audio_features.integrated_lufs`: **ITU-R BS.1770-4 gated** integrated loudness (K-weighting, 400 ms blocks / 100 ms hop, -70 LUFS absolute and -10 LU relative gates). It is **not** plain RMS. Both measures are printed for both slots, because the card's ±1 LU verdict is measure-dependent in both directions:

| slot | BS.1770 as stored (built/vanilla) | plain RMS as stored (built/vanilla) | verdict |
|---|---|---|---|
| `weapons#408` | -2.97 / -5.30 -> **+2.33 LU** | -6.86 / -6.18 -> -0.68 dB | BS.1770 RED, RMS would pass |
| `vehicles#279` | -20.45 / -20.25 -> -0.20 LU | -16.61 / -20.73 -> +4.12 dB | BS.1770 pass, RMS would fail |

## `weapons#408` - loudness +2.33 LU

- WAV source: `E:\Modding\_gamedata\BmAKgrab\audio\wav\098BBFE1.wav`, 2 ch, 16-bit, 48 kHz, 80,124 frames. Map row `W-03`, `source_rule: first` on `Play_Batmobile_MShot`.
- The event it replaces: **UNKNOWN as an identity**. W-03 has `guid: null` and `slot_confidence: candidate` (name match only), so the comparison is against the vanilla payload at the same bank+index (`weapons#408`, -5.30 LUFS as stored), which is the only oracle the data carries.
- Recompute both ways: BS.1770 as stored **+2.33 LU** (RED); BS.1770 mono +2.53; plain RMS as stored -0.68 dB (would pass).
- Cause (derived): the slot is `mono-replicated` to 2 channels; two identical channels add **+3.01 LU** (`10 log10 2`) under BS.1770. `bm_audio.payload()` measures the mono `q`, and the loop-fill path (`bm_audio.py:294-299`) re-levels only *down* (`if corr >= 0: break`) and then sets `want = meas['delivered_lufs']` - the fresh mono measurement becomes its own target. The map's stereo target `lufs` -5.30 / `delivered_lufs` -5.87 are never compared with the shipped channel layout. The +1.13 dB gain also clips 7.06 % of samples (the WAV already peaks at 0.00 dBFS).
- Fix (derived, not applied): attenuate the WAV by **2.72 dB** (factor 0.731139). Rebuilt payload: stereo -5.30 LUFS (delta 0.00 vs vanilla), mono -8.31, clip 0.00 %, peak -1.59 dBFS.

## `vehicles#279` - loop click

- WAV source: `E:\Modding\_gamedata\BmAKgrab\audio\wav\0C69336B.wav`, 2 ch, 16-bit, 48 kHz, 186,497 frames; slot 336,000 frames, mono, gain -6.95 dB.
- Loop point: no loop metadata (`loop_start`/`loop_end` null, vgmstream prints no loop line), so the file wrap is the only boundary the data carries.
- Samples printed around the wrap in `audio_diag.md` (frames 335992-335999 and 0-7, decoded built / derived payload / vanilla). Decoded `built[k] == derived[k-16]` because the record's 32-byte codec header occupies the first 16 decoded frames (identical in vanilla, which is why frames 0-7 agree).
- Steps: decoded wrap **-16.95 dBFS** (limit -40), derived payload alone -17.50, vanilla slot -41.24, source WAV's own end->start step -34.06, built interior p99 -46.01. Tile seam at frame 184449 = -68.03 dBFS.
- Verdict: **the click is created by the build's loop fill, not present in the source WAV.** The 7.0 s slot cuts the tiled source mid-waveform at source frame 151551 (value -0.29152, head 0.00119), not at a boundary the source makes; rebuilding the same rule from the same WAV reproduces -17.50 dBFS; the source's own boundary step is 17.11 dB smaller.
- Fix (derived, not applied): drop the first **408 frames** (0.0085 s) of the WAV head (both channels). Rebuilt payload: wrap **-60.77 dBFS**, loudness -20.45 LUFS (delta -0.20), clip 0, padded frames 149911 (was 149503).

## Proposed diffs (NOT applied)

The WAVs live outside the repository, so both WAV fixes are edit specifications, not patches; the manifest is a receipt and changing it alone changes no bank byte. The diagnosis contains:

- `weapons#408`: 16-bit PCM edit `y[n] = round(x[n] * 0.731139)` (length unchanged).
- `vehicles#279`: drop 408 frames/channel; frames 186497 -> 186089; data/RIFF sizes -1632 bytes.
- `Working/Audio/bm_bank_manifest.json`: a unified diff of the fields a rebuild would write (A-05 `src_frames`/`padded_frames`/`loop_fill`/`payload_sha256`; W-03 `delivered_lufs`/`clip_pct`/`payload_sha256`). New payload sha256 values are computed by the script from the edited sources.

## UNKNOWNs and what was tried

- **Which vanilla event `weapons#408` is.** Tried: map row W-03 (`guid: null`, `slot_confidence: candidate`, name match only), manifest `resolved`, the event `Play_Batmobile_MShot` media list. Only the vanilla payload in the same slot is measurable; no GUID ties the slot to the event.
- **The loop point/region of all three `_loop` slots** (`vehicles#151` nitro, `vehicles#279` creaks, `weapons#408` minigun). Tried: manifest `loop_start`/`loop_end` (null on 5/5), vgmstream `-m` (no loop start/end/flag line), `t12_audio_map.json` `method.loop` (FSB5 field absent). Only the file wrap is measurable; `vehicles#151` and `weapons#408` therefore remain UNKNOWN for a real loop region, and neither is the reported click (408's wrap is -63.27 dBFS).
- **Whether the engine loops `vehicles#279` at all**, and how either fix sounds in game (timbre, mixing, ducking): phase Q; the test ban is in force.
- **Whether the manifest's `delivered_lufs` acceptance is the intended contract** for stereo-replicated slots: the code path is decoded and the behaviour reproduced, but no spec row states that a mono measurement may stand for a two-channel payload.
