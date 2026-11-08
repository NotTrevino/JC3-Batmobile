# RC5 loop-seam build - `vehicles#279` and the other two `_loop` slots

Date: 2026-11-08. New tree `Builds/bm-RC5-audio`, copied from `Builds/bm-RC4-audio`; the only
bytes changed are the two seam windows described below. `Builds/bm-004c` and `Builds/bm-RC4` were
never opened for writing (their banks still carry the 5 Nov / 7 Nov timestamps and their hashes).

**Result: 3/3 `_loop` slots at or below -40 dBFS in both measured domains.**

| slot | decoded seam (v04_loops `step`) | payload seam | p99 | verdict |
|---|---:|---:|---:|---|
| `vehicles#151` `jc3_veh_land_premium_nitro_loop` | -18.18 -> **0 LSB (-180.0)** | -16.36 -> **0 LSB (-180.0)** | -10.99 | PASS |
| `vehicles#279` `jc3_veh_lave_chassis_spin_creaks_loop_fast` | -24.96 -> **0 LSB (-180.0)** | -74.75 (already) | -46.07 | PASS |
| `weapons#408` `jc3_wpn_minigun_fire_close_loop_04` | -55.74 (already) | -90.31 (already) | -11.54 | PASS |

`-180.0` is `db()`'s floor: the edited end->start step is **0 LSB**, not a small number.

## 1. The report's best option cannot reach -40 — measured, not argued

`tmp/freebuff/reports/loop279-edit-options.md` recommends a source-level fade (its smallest clean
option: 2 samples, seam -58.49 dBFS on the raw WAV). That number is the *source's* boundary with no
build gain. Two facts in the built record stop it from carrying to the slot:

1. **The decoder's last frame is not the payload's last sample.** The record is
   `header(hlen B) + payload`; vgmstream decodes `frames` samples from byte 0, so the stream ends at
   `payload[frames-1-shift]` with `shift = hlen/(2*ch)` (30 frames for #151, 16 for #279, 23 for
   #408). Its first frame is the header's first int16 pair, read as audio. A source fade therefore
   cannot take the decoded seam below `|0 - header_first|`:

   | slot | header's first int16 | fade-to-zero ceiling, decoded | payload[0] | fade-to-zero ceiling, payload |
   |---|---:|---:|---:|---:|
   | `vehicles#151` | -7671 | **-12.61 dBFS** | 363 | **-39.11 dBFS** |
   | `vehicles#279` | -680 | **-33.66 dBFS** | 761 | **-32.68 dBFS** |
   | `weapons#408` | 44 | -57.44 dBFS | -358 | -39.23 dBFS |

   So the 2-sample source fade leaves #279 at -33.66 (decoded) and -32.68 (payload) — still above
   -40, exactly the trap the options report names: it moves the click one sample inward. #151 would
   be worse still.

2. **The payload's first sample sets the audio-domain floor.** Zeroing the tail makes the payload
   wrap `|0 - payload[0]|`, which is -32.68 dBFS for #279 because the loop-fill gain lifted
   `payload[0]` to 761 LSB.

The edit that actually gets there is a short ramp to the record's own first decoded frame (and, when
the audio-domain wrap also fails, on to `payload[0]`), because that is the value the two domains
compare against.

## 2. Applied edit

Per slot, `anchor = frames-1-shift`:

* **A**: over `K` frames ending at `anchor`, ramp to `header0` (the record's first decoded frame).
  `K` is searched (2, 4, 8, ...) and the first value whose *every* adjacent step in the edited span
  is also at or below -40 dBFS wins, so the click is removed rather than moved.
* **B**: `anchor+1 .. frames-1`. If the payload's own wrap fails, ramp to `payload[0]` (kills it);
  if it already passes, ramp back to the payload's own last sample so the tail stays continuous and
  the existing wrap is untouched.

| slot | `header0` (int16) | `anchor` | K | B | span / changed | span delta RMS | change RMS | whole-payload delta |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| `vehicles#151` | -7671 | 154787 | 8 | to `payload[0]` (30 f) | 38 f / 0.79 ms / 38 changed | **-5.71 dB** | -46.95 dBFS | **-0.000659 dB** |
| `vehicles#279` | -680 | 335983 | 8 | back to `payload[-1]` (16 f) | 24 f / 0.50 ms / 23 changed | **-5.72 dB** | -71.09 dBFS | **-0.000011 dB** |
| `weapons#408` | 44 | 160313 | - | **none** | 0 | 0 | 0 | 0 |

`span delta RMS` is `20log10(rms(edited)/rms(original))` over the changed frames — the energy removed
from that sub-millisecond window. `whole-payload delta` is the same ratio over all frames: ≤0.0007 dB,
i.e. the audible loop body is unchanged. The N=8 ladder is the smallest passing value: the analytic
floor for #279 is `|header0 - start|/0.01 ≈ 6` frames, so 8 is the first rung that both passes and
keeps every adjacent step below -40.

## 3. What `v04_loops.py` reports, and one caveat

Re-pointed at the new tree (`v04_loops.BANKS`, `v04_loops.MANIFEST`) and run through `facts()`:

```
jc3_veh_land_premium_nitro_loop:  step=-180.0 p99=-10.99 vanilla=-17.24 passes40=True loopchunk=False
jc3_veh_lave_chassis_spin_creaks_loop_fast: step=-180.0 p99=-46.07 vanilla=-41.24 passes40=True loopchunk=False
jc3_wpn_minigun_fire_close_loop_04: step=-55.74 p99=-11.54 vanilla=-11.13 passes40=True loopchunk=False
bank sha: {'vehicles': 'beaa14cecdaaeb07', 'weapons': 'd05b74ed9111ecad'}
census vs vanilla: LOOP 29 (vehicles) / 12 (weapons), identical in both trees
```

**Caveat, stated rather than hidden:** `v04_loops.facts()`'s `payload.own_wrap_dbfs` column
re-derives `bm_audio.payload()` from the *unfixed* source (`recon_ok=False`, `own_derived`
-16.36 / -17.52 / -30.87). It therefore describes the pre-edit payload and is not usable on this
tree. The payload-domain numbers in section 0 are read from the record's own bytes
(`pcm[-1]` vs `pcm[0]`); the `step` column — the card's gate — is measured from the tree and is
correct. `bm_audio --check` also does not describe this tree: the seam edit is applied after its
payload construction, which is why this tool carries its own `--check`.

## 4. FMOD loop points inside the bank cannot carry the fix

* The three slots carry **no** FSB5 `LOOP` chunk (`has_loop=False`; metadata is `['13']` for the two
  vehicles slots and `['5','13']` for the minigun), and their WAVs have no `smpl` chunk (only
  `fmt `/`data`). The whole payload is the loop.
* The bank format does use loop points elsewhere — `LOOP` (type 3, two little-endian uint32) on
  **29** samples in `vehicles.bank` and **12** in `weapons.bank`, identical in the RC4 and RC5 trees.
* It still cannot carry this fix: the `LOOP` pair lives in the per-sample header block, so adding one
  grows `shdr` and shifts every data offset — impossible inside the size-locked swap route
  (`210,781,376` / `177,586,080` B, size unchanged). A pair could in principle move the wrap to an
  interior sample, but that changes the loop length/phase (a different edit), breaks the
  built-vs-vanilla header identity `v04_loops` asserts, and whether JC3's FMOD honours FSB5 `LOOP`
  for these events is **UNKNOWN** (no loop line, no manifest `loop_start`/`loop_end`).
  Answer: **no — the samples carry the fix; a loop-point route would need a header rebuild and a
  runtime take.**

## 5. Artifacts

| file | what |
|---|---|
| `Builds/bm-RC5-audio/` | new tree: `aaf/` + `banks/` copied from `bm-RC4-audio`, plus `bank_set.json`, `events.json`, `install.ps1`, `receipt.json`, `verify/` |
| `Builds/bm-RC5-audio/banks/vehicles.bank` | 210,781,376 B, sha256 `beaa14cecdaaeb07d50b28f3c96419629076ec78b8d355969b2684b90f44ce13` (RC4: `aab92ca0…`) |
| `Builds/bm-RC5-audio/banks/weapons.bank` | 177,586,080 B, **unchanged** `d05b74ed…016a` |
| `Working/Audio/bm_bank_manifest_rc5.json` | the RC4 manifest with the two slots' `payload_sha256` / `data_offset` and the `seam_edits` block |
| `Builds/bm-RC5-audio/verify/loops_rc5.json` / `.md` | per-slot before/after, edits, bank hashes |
| `Tools/scripts/rc5_loop279.py` | `--write` / `--check`; derives both banks in memory from `bm-RC4-audio` and byte-compares the tree |
| `tmp/freebuff/reports/rc5-loop279-wrap-build.md` | this page |

## 6. Commands and exits

```
python Tools/scripts/rc5_loop279.py --write
  PASS jc3_veh_land_premium_nitro_loop            decoded -180.0  payload -180.0
  PASS jc3_veh_lave_chassis_spin_creaks_loop_fast decoded -180.0  payload -74.75
  PASS jc3_wpn_minigun_fire_close_loop_04         decoded -55.74  payload -90.31
  edit vehicles#151: K=8 wrap=True 38 frames (0.7917 ms), delta RMS -5.72 dB, change -10.85 dBFS
  edit vehicles#279: K=8 wrap=False 24 frames (0.5 ms), delta RMS -5.49 dB, change -29.63 dBFS
  edit weapons#408: none (already at or below -40 in both domains)
  summary: {'slots': 3, 'decoded_pass': 3, 'payload_pass': 3}
  PASS: Builds/bm-RC5-audio banks equal the re-derived edit
  WRITE_EXIT=0

python Tools/scripts/rc5_loop279.py --check
  ... same three PASS rows, same edit lines ...
  PASS: Builds/bm-RC5-audio banks equal the re-derived edit
  CHECK_EXIT=0
```

(The tool prints the span delta from its search; the per-frame figures in section 2 re-measure the
written banks, which is why #151 reads -5.71 vs -5.72 dB: one printed value is rounded inside the
search. 23 of #279's 24 span frames actually changed — one ramp step rounded onto its original
sample.)

## 7. Revert

Delete `Builds/bm-RC5-audio`, `Working/Audio/bm_bank_manifest_rc5.json` and
`Tools/scripts/rc5_loop279.py`; delete this page. Nothing else changed: `Builds/bm-RC4-audio`
(`aab92ca0…`, 7 Nov 12:52), `Builds/bm-004c` (5 Nov 22:53) and `Builds/bm-RC4` (7 Nov 13:00) keep
their bytes and timestamps.

## 8. UNKNOWNs

* **Whether FMOD/JC3 actually loops these three slots over the whole payload** — no loop pair, no
  `smpl`, no game run; the test ban stands. The seam is engineered against the only boundary the
  data carries.
* **Whether the `header0` target is sonically right.** It is the record's first decoded frame, which
  for #151 is -7671 LSB (-12.6 dBFS) — a metadata byte pair, not audio. The ramp is 0.79 ms and the
  whole-payload RMS moves 0.0007 dB, but the ear may still prefer the payload-domain fix alone
  (-16.36 -> 0 LSB at the true wrap) without the decoder-domain pass. Both numbers are in section 0
  so the operator can choose.
* **Whether -40 dBFS should apply to the decoder domain at all** — that number is set by a byte pair;
  this report satisfies both domains rather than arguing the bar down.
