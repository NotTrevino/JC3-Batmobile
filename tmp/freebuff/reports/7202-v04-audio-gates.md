STATUS: partial — the gate script exists and reproduces, but 2 of 6 audio gates are RED on the RC
(loudness on `weapons#408`, a loop click on `vehicles#279`) and the three loop points stay UNKNOWN.
No bank, manifest, module, RC file or install was modified; every gate is re-derived from the bytes.

# V-04 audio gates on `Builds/bm-RC1` — task 7202

The card (`GRAB_BACKLOG.md` §9a, `#### V-04`): decode the built bank back; compare each sample to its
WAV source (length ±1 frame); loudness within ±1 LU of the vanilla event it replaces; loops seamless
(no click > −40 dBFS at the loop point). Done: all events pass.

## Files written

| file | role |
|---|---|
| `Tools/scripts/v04_audio.py` | the gate, `--write` / `--check`; rewritten from the check-only version. The previous lane's file is preserved verbatim at `tmp/freebuff/scratch/v04_audio.prev.py` |
| `Builds/bm-RC1/verify/audio.json` | 5 slot rows + 7 gates + UNKNOWNs, all numbers re-derived |
| `Builds/bm-RC1/verify/audio.md` | the same, rendered for reading |
| `tmp/freebuff/reports/7202-v04-audio-gates.md` | this report |
| `MODLOG.md` | one appended journal section (project rule R14) |
| `tmp/freebuff/scratch/v04_probe.py`, `.../audio.json.bak` | scratch only, not deliverables |

Inputs were read-only: `Builds/bm-RC1/drop/sound/fmod_banks/{vehicles,weapons}.bank`,
`Working/Audio/bm_bank_manifest.json` (B-11), `Working/Translation/t12_audio_map.json` (T-16), the
five WAV sources, and the two vanilla banks. All five WAV sources exist on disk (four under
`E:\Modding\_shared\gamedata\BmAKgrab\audio\wav\`, one in-repo) — none was skipped.

## Result

| gate | result | what it means |
|---|---|---|
| inputs | GREEN | RC banks sha256 == B-11's `written`; vanilla banks sha256 == the manifest's `source_sha256`; 5/5 WAV sources present |
| decode | GREEN | 5/5 slots decode (vgmstream) to the manifest's frames / rate / channels / name |
| provenance | GREEN | 5/5 decoded PCM is the payload B-11's own rule derives from the WAV — but offset by 16–30 frames (finding F3) |
| length | GREEN | 5/5 within ±1 frame of `src_frames + padded_frames − trimmed_frames`; against the raw WAV every slot differs by design (−3325 / −2961 / −28471 / +149503 / +80213) |
| loudness | **RED** | 4/5 within ±1 LU; `weapons#408` is **+2.33 LU** louder than the vanilla payload in its slot |
| loop | **RED** | 2/3 no click; `vehicles#279` seam **−16.95 dBFS** (vanilla −41.24, own p99 step −46.01) |
| tail | GREEN | 3/3 loop slots end in signal, no digital silence (B-11's earlier defect stays fixed) |

## Findings (each labelled)

**F1 — loudness, `weapons#408 jc3_wpn_minigun_fire_close_loop_04`: +2.33 LU (decoded).**
Built payload as stored: −2.97 LUFS; the vanilla payload at the same bank+index as stored: −5.30 LUFS.
Mono downmix of the same two: −5.98 vs −8.51 → +2.53 LU. Cause (derived): T-16 measured a slot's
loudness on its **as-stored 2-channel** decode (`t12_audio.py:432-434`, `g15._float_mono` passes a 2-D
array through unchanged), so the slot target is −5.30; B-11's payload is **mono** and measured as mono
(−5.99), then replicated to both channels, which adds ~3 dB of total energy. The map's own `delta_lu`
for this row (−0.57) compares a mono measurement with a stereo target, which is why B-11's ±1 LU check
looked green. The other four slots are mono in the bank, so the two scales coincide there (`0.00`,
`0.00`, `0.00`, `−0.20`).
Also carried from the manifest, not re-judged here: this slot clips 7.06 % of frames at T-16's gain.

**F2 — loop click, `vehicles#279 jc3_veh_lave_chassis_spin_creaks_loop_fast`: seam −16.95 dBFS (decoded).**
The vanilla payload at that index is continuous across the same boundary (−41.24 dBFS against its own
p99 interior step of −20.13), which is the evidence that the file wrap *is* the loop boundary. The built
payload's wrap step is 29 dB above its own p99 interior step (−46.01) → audible click if the engine loops
end→start. The **derived payload itself** (before the bank) has a −17.50 dBFS seam, so this is not the
16-frame splice offset (F3): it is the tiled fill being truncated mid-cycle at frame 336,000. The other
two loop slots are clean: nitro −18.18 dBFS against p99 −10.99 (inside its own step scale), minigun
−63.27. B-11's derived tile seams are smooth (creaks −65.2, minigun −50.7 dBFS).

**F3 — every swapped sample is written 16–30 frames late (decoded).**
`bm_audio.py` computes `hlen = len(sample.data) − frames·channels·2` and splices `data[:hlen] + body`,
i.e. it treats those bytes as a **leading** header. For FSB5 they are a **trailing** per-sample chunk:
for the vanilla `vehicles#7`, vgmstream's decoded bytes equal `sample.data[:frames·ch·2]` exactly
(`decode == data[60:] False`, `decode == data[:59908] True`). So the shipped record holds the previous
payload's first N frames at the head and the derived payload's last N frames are never written
(shift 30 / 27 / 30 / 16 / 23 frames = 0.33–0.63 ms). B-11's `--check` slices the same 60 bytes, so it
cannot see this. Audible impact is negligible; it matters because it means the *shipped* tail is not the
derived tail — the loop seam above is measured on the shipped bytes, as it must be.

**F4 — `bm_audio.py --check` is RED today, on metadata only (decoded/derived).**
Its only failure is `Working/Audio/bm_bank_manifest.json differs from the re-derived record`; the diff is
4 fields, all `.installer.dropzone_at_build.*` (the snapshot of the live `D:\Games\...\dropzone` banks
recorded when B-11 ran). The banks and every `payload_sha256` re-derive identically. So this is a stale
target-folder snapshot, **not** audio drift. It is recorded here because the previous V-04 run used
`bm_audio.py --check` as a gate; this gate deliberately derives the provenance itself instead.

## What cannot be checked offline

- the loop point / seam of `jc3_veh_land_premium_nitro_loop` (A‑02), `jc3_veh_lave_chassis_spin_creaks_loop_fast` (A‑05), `jc3_wpn_minigun_fire_close_loop_04` (W‑03): no loop field exists anywhere in the bank, so the seam above is measured at the only boundary the data carries (the file wrap)
- which vanilla event each slot really is — all five (`slot_confidence: candidate`), and W‑03 has no donor event GUID at all — so "the vanilla event it replaces" is, rigorously, "the vanilla payload at the same bank+index"
- whether the swapped payload is what the event plays at runtime (needs phase Q; test ban in force)
- how the swap sounds in game (timbre, mixing, ducking)

## UNKNOWNs

| what | status | what was tried | why still unknown |
|---|---|---|---|
| loop point of the three `_loop` payloads | UNKNOWN | manifest `loop_start`/`loop_end` (null on 5/5); `vgmstream -m` loop start/end/flag lines (none — the stream *name* contains `_loop`, which is not metadata); `t12_audio_map.json.method.loop` (records the FSB5 field absent) | the bank stores no loop field; whether the event/tune graph or the engine loops the payload, and over which region, is in no file readable here |
| whether the chosen slot is the vanilla event | UNKNOWN | `t12_audio_map.json.slots[].slot_confidence`, manifest `resolved` GUIDs, G2‑24 (no tune→sample field in the bank) | the ±1 LU comparison is against the vanilla payload in the same slot, not a proven event |
| runtime playback | UNKNOWN | FEV event/tune GUIDs present in the built bank (B‑11) | needs the game |

## Commands run, with verbatim output

**1 — the RC carries B-11's banks, and the vanilla banks are the ones B-11 copied**
```
$ sha256sum Builds/bm-RC1/drop/sound/fmod_banks/*.bank Builds/bm-004/banks/*.bank Working/Audio/jc3bank/sound/fmod_banks/vehicles.bank "E:/Modding/_shared/gamedata/JC3grab/audio/weapons.bank"
76d67bcef81c8d297082b9cb026e9e995762fb2f72e3b2c2d7f5a1570e2f00a7 *Builds/bm-RC1/drop/sound/fmod_banks/vehicles.bank
5b8a7605a8b70ca211defa3c8856a1ab26b4276e11ecc46a4147af245f7a7d78 *Builds/bm-RC1/drop/sound/fmod_banks/weapons.bank
76d67bcef81c8d297082b9cb026e9e995762fb2f72e3b2c2d7f5a1570e2f00a7 *Builds/bm-004/banks/vehicles.bank
5b8a7605a8b70ca211defa3c8856a1ab26b4276e11ecc46a4147af245f7a7d78 *Builds/bm-004/banks/weapons.bank
6161104d8909b7b0b7dd1d1201dbaa993e141877348457a6c7b5c84da1ccd983 *Working/Audio/jc3bank/sound/fmod_banks/vehicles.bank
ab537a7cfc4c4b258174978f3fc952ddeb731ca8a7fe5dd1b81b1f261c819c3e *E:/Modding/_shared/gamedata/JC3grab/audio/weapons.bank
```
(the four RC/`bm-004` hashes equal the manifest's `written[].sha256`; the two vanilla hashes equal its
`bank.*.source_sha256`)

**2 — B-11's own checker (supporting evidence only, see F4)**
```
$ uv run --with numpy --with scipy --with fsb5 python Tools/scripts/bm_audio.py --check
FAIL: Working/Audio/bm_bank_manifest.json differs from the re-derived record
EXIT=1
```

**3 — what that diff is**
```
$ uv run --with numpy --with scipy --with fsb5 python - <<'EOF'   # build(write=False) vs the manifest, field by field
...
DIFF COUNT 4
  .installer.dropzone_at_build.vehicles.bank.mtime -> re-derived='2026-11-02 21:48:39' disk='2026-10-14 15:33:28'
  .installer.dropzone_at_build.weapons.bank.bytes -> EXTRA in re-derived (177586080)
  .installer.dropzone_at_build.weapons.bank.mtime -> EXTRA in re-derived (2026-11-02 21:48:41)
  .installer.dropzone_at_build.weapons.bank.present -> re-derived=True disk=False

re-derived payload sha per slot vs disk manifest:
  jc3_veh_door_tank_open_03 2c8c0490a8c8 2c8c0490a8c8 match
  jc3_veh_door_tank_close_01 fc81c0ca387a fc81c0ca387a match
  jc3_veh_land_premium_nitro_loop 4b4fa551fe26 4b4fa551fe26 match
  jc3_veh_lave_chassis_spin_creaks_loop_fa f822ae78d583 f822ae78d583 match
  jc3_wpn_minigun_fire_close_loop_04 7d06097a9804 7d06097a9804 match
```

**4 — the FSB5 chunk is trailing, not leading (F3)**
```
$ uv run --with numpy --with scipy --with fsb5 python - <<'EOF'   # vanilla vehicles#7, fsb5 vs vgmstream
vanilla samp.data 59968 decode 59908
decode == data[60:] False  decode == data[:len] True
payload sha of data[60:] 6621cc11628cd74274a05838c64606f6aaeb70e19c712936991727924be9c8fe data[:len]  c4af616db8c9c44a6c54934ec7c0d7feda1d797a7e0d01531cb2fe9ebd4cf266
decoded sha c4af616db8c9c44a6c54934ec7c0d7feda1d797a7e0d01531cb2fe9ebd4cf266
Traceback (most recent call last):
  ...
TypeError: payload() got multiple values for argument 'loop'
```
(the traceback is from the *next* line of that throwaway probe, not from the measurement above; the same
offset was then measured for all five slots by the gate itself, `rows[].decode.payload_match = "shifted"`,
`shift_frames` 30 / 27 / 30 / 16 / 23)

**5 — the gate, written**
```
$ uv run --with numpy --with scipy --with fsb5 python Tools/scripts/v04_audio.py --write
wrote Builds/bm-RC1/verify/audio.json + audio.md: 5 slots, decode 5/5, length 5/5, loudness 4/5 (max |delta| 2.33 LU), loop clicks 1/3
    vehicles#7 jc3_veh_door_tank_open_03                fr   29954/29954   dspan +0 LU -21.85/-21.85 d +0.00 prov shifted  loop n/a
   vehicles#98 jc3_veh_door_tank_close_01               fr   24933/24933   dspan +0 LU -11.02/-11.02 d +0.00 prov shifted  loop n/a
  vehicles#151 jc3_veh_land_premium_nitro_loop          fr  154818/154818  dspan +0 LU -10.33/-10.33 d +0.00 prov shifted  loop ok
  vehicles#279 jc3_veh_lave_chassis_spin_creaks_loop_fa fr  336000/336000  dspan +0 LU -20.45/-20.25 d -0.20 prov shifted  loop CLICK
   weapons#408 jc3_wpn_minigun_fire_close_loop_04       fr  160337/160337  dspan +0 LU -2.97/-5.3 d +2.33 prov shifted  loop ok
verdict: RED: loudness, loop
WRITE_EXIT=0
```

**6 — `--check` reproduces every number from the source bytes**
```
$ uv run --with numpy --with scipy --with fsb5 python Tools/scripts/v04_audio.py --check
PASS: Builds/bm-RC1/verify/audio.json + audio.md reproduce from the banks and WAV sources (5 slots, 1,877 samples)
gates: decode 5/5, length 5/5, loudness 4/5 (max |delta| 2.33 LU), loop clicks 1/3, tail 3/3
verdict: RED: loudness, loop
CHECK_EXIT=0
```

**7 — the `--check` catches a tampered report, and the restore is clean**
```
tampered rows[3].loudness.delta_lu -> -0.10 (was -0.20)
---- check after tamper (must FAIL)
FAIL: .rows[3].loudness.delta_lu: -0.2 != -0.1
TAMPER_CHECK_EXIT=1
restored
---- final check
PASS: Builds/bm-RC1/verify/audio.json + audio.md reproduce from the banks and WAV sources (5 slots, 1,877 samples)
gates: decode 5/5, length 5/5, loudness 4/5 (max |delta| 2.33 LU), loop clicks 1/3, tail 3/3
verdict: RED: loudness, loop
CHECK_EXIT=0
```

**8 — F2 is the fill, not the splice offset (derived payload, before the bank)**
```
$ uv run --with numpy --with scipy --with fsb5 python - <<'EOF'
jc3_veh_land_premium_nitro_loop              derived-payload seam  -16.36 dBFS  p99 interior  -10.99 dBFS  -> no click
jc3_veh_lave_chassis_spin_creaks_loop_fast   derived-payload seam  -17.50 dBFS  p99 interior  -46.01 dBFS  -> CLICK
```

**9 — exploratory measurement that located the two red gates (`tmp/freebuff/scratch/v04_probe.py`)**
```
slot name | built fr | rawWAV fr | span | LUFS built / vanilla / map | wrap built/van | tile seam max/p99
jc3_veh_door_tank_open_03                       29954    33279    29954 -21.85 / -21.85 / -21.85 |  -29.7 /  -62.4 | ch 1/1 rawch 3
jc3_veh_door_tank_close_01                      24933    27894    24933 -11.02 / -11.02 / -11.02 |  -11.6 /  -67.4 | ch 1/1 rawch 3
jc3_veh_land_premium_nitro_loop                154818   183289   154818 -10.33 / -10.33 / -10.33 |  -18.2 /  -17.2 | ch 1/1 rawch 3 seams n=1 maxstep=-13.5dBFS p99=-11.0
jc3_veh_lave_chassis_spin_creaks_loop_fast     336000   186497   336000 -20.45 / -20.25 / -20.45 |  -16.9 /  -41.2 | ch 1/1 rawch 2 seams n=1 maxstep=-65.2dBFS p99=-46.0
jc3_wpn_minigun_fire_close_loop_04             160337    80124   160337  -5.98 /  -8.51 /  -5.99 |  -63.3 /  -11.1 | ch 2/2 rawch 2 seams n=2 maxstep=-50.7dBFS p99=-8.9
```

## Why the ±1 frame gate is against the derived span, not the raw WAV

Against the raw WAV the five slots differ by −3325 / −2961 / −28471 / +149503 / +80213 frames. That is
B-11's documented route‑a arithmetic (trim to the slot's fixed frame count, tile with a 2048‑frame
crossfade, or cut a `source_span_s` window), recorded in the manifest as `src_frames`, `trimmed_frames`,
`padded_frames` and `source_span_s`. The card's wording cannot hold against the raw WAV — that was
already established in `Research/specs/V-04.md` §3 (V‑04/3) — so the gate compares `frames_built` with
`src_frames + padded_frames − trimmed_frames` (±1) and prints the raw deltas beside it. This is a
restatement of the card, not a pass invented by this task.

## What this task did not do

No bank, manifest, module, `.toc`, installer or install tree was written or rebuilt; no game was
launched, attached to, or installed into (test ban intact); nothing was committed or pushed. The two red
gates are **properties of the RC**, reported, not accepted: fixing them means a new B‑11 derivation
(−2.33 LU on the W‑03 slot: measure the slot target mono, or de-replicate the payload) and a new loop
fill for the creaks slot (a wrap-aware crossfade at frame 336,000) — both outside a verify task's remit.

## COMPROMISES

None made by this task. The RED gates and the UNKNOWN loop points are not accepted compromises; they
need the operator's decision and, for the loop, a listener or phase Q.

## Revert

Copy `tmp/freebuff/scratch/v04_audio.prev.py` back to `Tools/scripts/v04_audio.py`, delete
`Builds/bm-RC1/verify/audio.json`, `Builds/bm-RC1/verify/audio.md` and the MODLOG section
"V-04 audio gates on bm-RC1". No input file was modified.
