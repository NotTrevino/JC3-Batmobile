# `vehicles#279` — wrap-edit options on the source WAV

Slot: `vehicles#279` `jc3_veh_lave_chassis_spin_creaks_loop_fast`, source
`E:/Modding/_gamedata/BmAKgrab/audio/wav/0C69336B.wav`.
Limit: **-40 dBFS** at the wrap. Bank `Builds/bm-004c/banks/vehicles.bank` was **not** touched.

State being fixed (`tmp/freebuff/reports/audio-fix-tree.md:1` and `:32`): the slot measures
**-28.27 dBFS** as stored and **-39.68 dBFS** on the payload alone; the 408-frame pre-roll trim is
already applied in that build (`audio-fix-tree.md:12` lists it as the derived fix for this slot, and
`:32` records the slot still red after it).

---

## 1. Method — the same one `audio_diag.md` uses

`Builds/bm-RC1/verify/audio_diag.md` measures the loop seam as

```
wrap = 20*log10( | x[last] - x[first] | )        # mono downmix, full scale 1.0
```

recorded in `Tools/scripts/v04_diag.py:194` and `:210-212` (`src_wrap` is exactly this expression on
the source WAV). This report applies that expression to the **source WAV alone**, mono downmix
`(L+R)/2`, 16-bit full scale, no gain, no tiling, no codec header. Nothing else from the build path is
included, so these numbers are the source's boundary and not the slot's.

Source facts, decoded from the file header: **2 ch, 16-bit, 48000 Hz, 186,497 frames**; first sample
`+0.001190185546875`, last sample `+0.0210113525390625`.

| measurement | value | vs -40 |
|---|---:|---|
| **baseline, source alone** | **-34.06 dBFS** | **FAIL** (+5.94 dB over) |
| channel 0 alone | -34.04 dBFS | FAIL |
| channel 1 alone | -34.08 dBFS | FAIL |

This reproduces `audio_diag.md`'s "source's own end→start step: -34.06 dBFS" exactly, which is the
control that the method here is the same method.

For each option the table also gives the **worst adjacent step inside the last six samples**, because
a seam-only edit can pass the gate while leaving a click one sample earlier. That column is not part
of the -40 gate; it is what decides whether the edit removes the step or relocates it.

---

## 2. Trim options (drop N samples from the loop end)

`y = x[0 : 186497-N]`, then seam `|y[-1] - y[0]|`.

| option | new last sample | seam dBFS | vs -40 | length change | one-frame tolerance (±1) |
|---|---:|---:|---|---:|---|
| trim **1** | +0.017960 | **-35.51** | **FAIL** (+4.49 dB over) | −1 frame | inside |
| trim **2** | +0.015030 | **-37.18** | **FAIL** (+2.82 dB over) | −2 frames | **outside** |
| trim **3** | +0.012360 | **-39.04** | **FAIL** (+0.96 dB over) | −3 frames | **outside** |

No trim in the requested range passes. Trim 3 is the closest and still 0.96 dB short — it would need
roughly a further 1 dB of amplitude at the new last sample, i.e. dropping into the samples around
`x[-6] = +0.006775` (-43.4 dBFS seam), which is **6 frames** off the end, well outside the tolerance.

---

## 3. Fade options (linear ramp to zero across the last N samples)

`samples n-N … n-1` are multiplied by `1 - (j+1)/N`, so the final sample lands on **0.0** and the ramp
starts at `(N-1)/N` of the original. Length is unchanged in every case.

| option | seam dBFS | vs -40 | worst adjacent step (last 6 samples) | length change |
|---|---:|---|---:|---:|
| fade **1** | **-58.49** | **PASS** (-18.49 margin) | **-34.91 dBFS** — still above -40 | 0 frames |
| fade **2** | **-58.49** | **PASS** (-18.49 margin) | **-40.93 dBFS** — passes | 0 frames |
| fade **4** | **-58.49** | **PASS** (-18.49 margin) | **-46.96 dBFS** — passes | 0 frames |

Tail after each edit (mono, last six samples):

```
fade 1: 0.006775  0.009628  0.012360  0.015030  0.017960  0.0
fade 2: 0.006775  0.009628  0.012360  0.015030  0.008980  0.0
fade 4: 0.006775  0.009628  0.009270  0.007515  0.004490  0.0
```

All three fades land on the same seam (-58.49 dBFS), because the seam is then `|0 - x[0]| = 0.00119`,
i.e. it is set by the **first** sample, not by the tail. That is why the fade length does not move the
seam number and why the internal column is the one that distinguishes them.

---

## 4. Smallest option that passes

**Fade over 1 sample — gate PASS at -58.49 dBFS, length change 0 frames** (inside the ±1-frame
tolerance with the full tolerance unused).

Caveat that the gate cannot see: with N=1 the only sample changed is the last one, so the step of
`0.01796` that used to sit across the file boundary now sits between the new last sample and zero —
**-34.91 dBFS**, 5.09 dB above the limit. The seam passes; the click is moved one sample inward, not
removed.

**Smallest option that passes the seam *and* leaves no adjacent step above -40: fade over 2 samples**
— seam -58.49 dBFS, worst adjacent step **-40.93 dBFS** (0.93 dB of margin), length **unchanged**
(0 frames). Fade over 4 buys 6.96 dB more internal margin at the same length cost; nothing in the
gate asks for it.

Neither fade changes the sample count, so neither consumes any of the one-frame tolerance: the
tolerance is only at risk for the trims, and trims 2 and 3 exceed it while still failing.

---

## 5. What this does and does not settle

* **Settles:** on the source WAV alone, the wrap gate (-40 dBFS) is passed by every fade in the
  request and by none of the trims. The smallest passing edit is a 1-sample fade; the smallest one
  that is also internally clean is a 2-sample fade; both are length-neutral.
* **Not settled by the bytes:** whether the engineered seam survives the build's own path. The slot
  measured -28.27 dBFS as stored after a 408-frame pre-roll trim, and the payload alone -39.68 dBFS,
  so the tiling/codec step adds several dB on top of the source's own -34.06. A 2-sample fade measured
  on the source does **not** prove the rebuilt slot clears -40 — it has to be re-measured through
  `bm_audio.payload()` and the bank splice, which is a rebuild, not this table.
* **Not settled by the bytes:** whether the engine loops this slot at all (no `loop_start`/`loop_end`
  in the manifest; vgmstream prints no loop line), so the wrap remains the only boundary the data
  carries.

Edit specification for the smallest clean option (not applied):

```
file   : E:/Modding/_gamedata/BmAKgrab/audio/wav/0C69336B.wav
format : PCM 16-bit, 2 ch, 48000 Hz, 186497 frames (length unchanged)
edit   : for k in 1..2:  x[186497-k] *= (1 - k/2)      # last two frames, both channels
result : source-alone wrap -58.49 dBFS; worst adjacent step -40.93 dBFS
```

Revert: delete this file. No WAV, manifest, bank or build file was written or modified; the slot's
state and the 408-frame pre-roll trim remain as `audio-fix-tree.md:12` and `:32` record them.
