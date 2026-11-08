# Independent review — T-16 · Audio translation

Reviewer: Buffy (did not write this card). Date: 2026-10-29. Read-only review: the only file
written is this report. No game launch, no commit, no edit to `GRAB_BACKLOG.md`, `MODLOG.md`,
`Research/`, `Tools/` or any game file.

**Change record (AGENTS.md).** Intended change: create this one review file. File:
`tmp/freebuff/reports/review-T-16.md`. Why this file: the review was asked to land exactly here and
nothing else is written. Revert: delete `tmp/freebuff/reports/review-T-16.md`.

**Scope reviewed:** `GRAB_BACKLOG.md` §0.5 (R1–R14), the T-16 card (`GRAB_BACKLOG.md:924-930`), the
T-16 §12 row (`GRAB_BACKLOG.md:1325`); `MODLOG.md:12153-12293` (intended change + done);
`Working/Translation/T12_AUDIO.md` (295 lines), `Working/Translation/t12_audio_map.json`
(140,849 B), `Tools/scripts/t12_audio.py` (962 lines); the inputs the script reads
(`Research/BatmobileGrab/AUDIO_FEATURES.json`, `Research/JC3Grab/JC3_AUDIO_EVENTS.json`) and the two
banks it decodes (`Working/Audio/jc3bank/sound/fmod_banks/vehicles.bank`, and the documented
`E:\Modding\JustCause3\_grab\audio\weapons.bank` path only).

---

## VERDICT

**needs rework**

The plumbing is real and the census is sound: both `Out` paths exist, `--check` is a genuine full
rebuild (it re-decodes all 33 slots, ~3.5 s; I reproduced it and it is green), the 53-row /
45+8 split, the five dispositions, the 33 measured slots, the "no FSB5 loop chunk" result and the
22 unnamed-GUID count all re-derive from the raw data. What needs rework is the part B-11 would
build from:

1. the doc's central negative — "no event→tune edge" — is **false** (the tune entries carry the
   owning event GUID; independently re-verified), yet it is the sentence the whole slot-selection
   method rests on (R4);
2. the `± 1 LU` gain gate cannot fail by construction (`residual_lu` is algebraically zero), and for
   the nine slots whose payload is **padded** to the slot length the delivered loudness is
   ~1.4–6.9 dB below the slot, so the card's ±1 LU requirement is not established for those;
3. two of the seven `mapped` rows derive their gain/stretch from the **wrong source**: A-01 (five
   engine layers) from `Play_BML_EngineCoolTicks`, A-02's loop and stop slots from
   `jc3_batmobile_start.wav` while `EC2FD42B.wav` is measured and never used;
4. A-01 — the card's headline feature, AUD-1 `engine_running_sound` — is counted `mapped` with
   `chosen: null` and no gain, so nothing is actually decided for the engine.

Plus two R11 typed counts in the renderer (one of them self-contradictory, "seven" families listed
as eight) that `--check` cannot see.

---

## Check output (verbatim)

Command, from `E:/Modding/JustCause3/JC3-Batmobile`:

```
python Tools/scripts/t12_audio.py --check
```

stdout, exact (single line, trailing CR from the console; exit status `0`, elapsed 4 s):

```
PASS: 53 rows = 45/45 donor events + 8 weapon/mode rows | dispositions {'blocked': 2, 'kept vanilla': 32, 'mapped': 7, 'named omission': 11, 'remove': 1} | 33 slot candidates (21 gain-matched, max |residual| 0.0 LU <= 1; 12 kept stock) | 2 rpm curves | features 7/7 | json match True, md match True
EXIT=0
```

`--check` is not a cached pass: `cmd_check(fast=False)` calls `build(True, None)`
(`t12_audio.py:890-891`), which re-decodes every slot through `vgmstream-cli` and re-measures with
`bmak_audio_features.integrated_lufs`; a timed call to `build(True, None)` returns 53 rows in 3.5 s.
The MODLOG's claim that the gate was run in full is accurate.

## Out paths

| path (card `Out` / row) | exists | size |
|---|---|---|
| `Working/Translation/T12_AUDIO.md` | yes | 34,579 B, 295 lines (MODLOG says 295 — match) |
| `Working/Translation/t12_audio_map.json` | yes | 140,849 B (MODLOG says 140,849 B — match) |
| `Tools/scripts/t12_audio.py` (extra, not in `Out`) | yes | 54,996 B, 962 lines |

No `Out` path is missing. Nothing else was promised.

## Does the card's `Done` match what `--check` verifies?

Card (`GRAB_BACKLOG.md:930`): *"every donor event and every chosen weapon event mapped or explicitly
kept vanilla."*

- **Donor half — mostly verified.** All 45 events in `JC3_AUDIO_EVENTS.json` (`donor.events` 45) are
  turned into rows, `invariants()` asserts `donor_rows == 45`, every disposition must be one of the
  five allowed words, every row must carry a verify cell, and every *named* role (23) must have a
  decision row. That is a real check.
- **Weapon half — satisfied by construction.** The eight weapon/mode rows come from `WEAPON_ROWS`, a
  typed list in the script; `invariants()` only asserts `weapon_rows == len(WEAPON_ROWS)`. Nothing
  reads T-11's chosen carriers, so "every chosen weapon event" is not tied to the card it delegates
  to.
- **"explicitly" is not enforced.** Any event with no `SPECS` entry is auto-filled by `finish()`
  (`t12_audio.py:512-526`) with `dispo="kept vanilla"` and one fixed verify sentence. 22 of the 32
  kept-vanilla rows are that default. The check cannot distinguish a decision from the absence of
  one, so the Done criterion's "explicitly" is a wish, not a test.

---

## Issues

### 1. Major — the premise "no event→tune edge" is false (R4, and it is the doc's justification)

`T12_AUDIO.md:27` (*"G2-24 §5 proved the bank stores no event→tune→sample edge"*),
`T12_AUDIO.md:268-269` (*"the bank holds one tune per event but no event→tune edge and no
tune→sample field (G2-24 §5, five proofs)"*), `t12_audio_map.json` → `method.slot`
(*"event -> tune -> sample is not stored in the bank"*), `MODLOG.md:12191`
(*"G2-24 §5 proved event → tune → sample is not stored in the bank"*) and `MODLOG.md:12279`
(*"G2-24 §5's five proofs"*).

The first hop is stored. In `vehicles.bank` the `TLNS` list begins at byte 55,181,586; its first
`TMLN`/`TLNB` entry (length `0xa4`) is

```
TMLN TLNB a4 00 00 00 | 00000000 | 90a3d8ab-2649-8d47-56fe-4682b6df5510 | 100cbd8f-9b9f-8749-b853-632b33d167e9 ...
```

i.e. a tune GUID followed by the GUID of the event that owns the tune (`100cbd8f…` = vehicles/15).
The `engine_running_sound` GUID `905be2e5-…` also occurs at byte 55,183,562 — inside that same tune
list, not only in the `EVTB` event body (55,152,970). All 24 vehicles-side donor GUIDs appear in the
bank. So the negative is wrong for `event → tune`; only `tune → sample` is genuinely unproven, which
is a much narrower and more useful UNKNOWN (and it would have let the doc name each row's tune, one
hop B-11 can verify).

This is a false negative presented as fact (R4) and it is already known in the project:
`tmp/freebuff/reports/review-G2-24.md:27,243` reported the same thing at 10:09 on 2026-10-28, after
this card closed at 05:38 — so the inheritance is understandable, but the rule is "when they
disagree about a measured fact, the evidence wins and this file must be corrected", and T-16's doc,
JSON and MODLOG all still state it.

### 2. Major — the `± 1 LU` gate is an identity and cannot fail (R11 evidence quality)

`t12_audio.py:535-539`:

```python
gain = round(s["lufs"] - target["lufs"], 2)
s["gain_db"] = gain
s["residual_lu"] = round(target["lufs"] + gain - s["lufs"], 2)
```

and the gate at `t12_audio.py:838-841` fails only if `max_abs_residual_lu > 1.0`. Since
`residual = target + (slot − target) − slot`, it is zero for every slot by algebra. `T12_AUDIO.md:15`
(*"max |residual| 0.00 LU"*) and the §12 row present that 0.00 LU as evidence that the card's
*"gain matched to the vanilla event's loudness ± 1 LU"* was met; it verifies nothing about the audio
that is actually delivered, and any error in the two LUFS measurements cancels.

It matters because the same transform pads payloads to the slot length
(`method.stretch`: *"trimmed/padded to `frames`"*). If the pad is silence, integrated loudness falls
roughly by `10·log10(frames/source_frames)`, and nine slot candidates have `stretch > 1`:
A-05 `4.902` (≈6.9 dB low), W-03 loop `2.001` (≈3.0 dB), A-02 loop `1.614` (≈2.1 dB), A-01 five
layers `1.377–1.742` (≈1.4–2.4 dB), W-03 barrel `1.160` (≈0.6 dB). For all of those the ±1 LU
requirement is unproven while the check reports 0.00 LU. (The doc never says what the pad is; that
gap is part of the problem.)

### 3. Major — one target per row: A-01's gains come from a cool-tick event, A-02's loop/stop from the start WAV

`t12_audio.py:526`: `target = next((s["source"] for s in sources if s.get("source")), None)` — a
single source per row, chosen by `src_events()`'s `sorted(..., key=name)` order
(`t12_audio.py:411-441`, sort at `:427`), then reused for every candidate slot in the row.

- **A-01** (`T12_AUDIO.md:66`) lists 12 BmAK events. The target is the alphabetically first with
  media, `Play_BML_EngineCoolTicks` (loudest WEM −8.65 LUFS, 1.428 s — confirmed in the JSON
  `sources[*].source`). So the five Aston layer gains (−1.39, −1.70, −1.81, −2.80, −3.38 dB) and all
  five `source_frames` (68,544 = 1.428 s) are measured against a *cool-tick one-shot*, not against
  the engine bed the row argues for. The same filter also pulls `Play_Batmobile_Rotation` into A-01
  while A-05 claims that same event as the chassis-spin source, and includes Clutch / Transition /
  Reverse / Positional one-shots — the "engine bed" set is not an engine bed.
- **A-02** (`T12_AUDIO.md:56`) has two measured WAVs. The target is
  `jc3_batmobile_start.wav` (−11.68 LUFS, 1.998 s → 95,904 frames), so the loop slot
  (`jc3_veh_land_premium_nitro_loop`, stretch 1.6143) and the stop slot (0.3784) are transformed
  from the **start** WAV. `EC2FD42B.wav` (−12.77 LUFS, 3.819 s) is measured and then unused by any
  gain or stretch in the map, although the row's verify promises *"all three payloads
  (start/loop/stop) audible"*. Against the real loop payload the gain would be 2.44 dB, i.e. outside
  the ±1 LU the card asks for.

Both are derived values, so R11 is not broken, but they are derived **from the wrong input** and no
check can see it.

### 4. Moderate — A-01 is counted `mapped` with no chosen slot and no gain

`T12_AUDIO.md:66` (`mapped`, *"5 candidates, UNKNOWN"*, gain `—`), `T12_AUDIO.md:34` (AUD-1 *2 rows,
2 mapped*), §12 *"7 mapped"*. The JSON has `A-01 … "chosen": null`. Under R4 a row whose target is
undecided is not `mapped`; the practical consequence is that the card's first feature (AUD-1,
engine start/idle/rev loop) has **no build value**, yet the headline count says seven rows are
mapped when six are. The row text itself is honest; the counts are not.

### 5. Moderate — Done criterion gap: "explicitly kept vanilla" is the default path

`finish()` (`t12_audio.py:512-526`) fabricates `kept vanilla` + `"V-04 file check: event kept
exactly as shipped"` for every event with no spec; 22 of the 32 kept-vanilla rows are that fallback
(the `D-01…D-22` block, `T12_AUDIO.md:239`). `invariants()` only requires that *named* roles have a
row, so an event with no decision is invisible to `--check`, and the weapon set is a typed list. The
card's Done therefore holds for coverage but not for "explicitly".

### 6. Minor — two typed counts in the renderer, one self-contradictory (R11)

`T12_AUDIO.md:271-273`: *"vehicles.bank carries 34 engine-ish samples across seven model families
(Aston, Ducati, moped, fiat, saab, volvo, train, tank)"* — **eight** names for "seven". These are
literals in `render_md` (`t12_audio.py:773-777`), so `--check` re-renders them unchanged and can
never catch the error.

Recount of the FSB5 name table (649 names): 34 names contain `engine` — so "34" is reproducible —
but they fall in **five** families (aston 8, ducati 8, train 7, tank_m8 7, fiat 1) plus 10 generic
`jc3_vehicle_engine_*` damage/smoke samples, and the moped, saab and volvo samples do not contain
`engine` at all (they are `moped_loop_rpm_*`, `saab_99_*`, `jc3_veh_volvo_1983_*`). No single filter
reproduces the sentence as written.

### 7. Minor — "the five `aston_martin_vantage_engine_rpm_*` layers … the only 5-layer RPM stack": the bank has six

`T12_AUDIO.md:124` (and `T12_AUDIO.md:66`). The name table holds six siblings: `idle_high` (index
127), `high` (236), `medium_low` (390), `low2` (601), `idle2` (619), `medium_high2` (636). A-01
lists five and silently omits `idle_high`. The "five" is typed prose (`t12_audio.py:89-91`), and a
selection is presented as a structural fact about the bank (R4).

### 8. Minor — three decision-gated rows are disposed `kept vanilla` while their own verify cell says "blocked: D-8"

`T12_AUDIO.md:58` (A-08), `:64` (A-10), `:91` (A-23) all start their verify with `blocked: D-8`, yet
their `dispo` is `kept vanilla`; the summary therefore reports `blocked 2` and §12 says *"2 blocked
D-2/D-10"*, while `MODLOG.md:12292` names D-8 as still open on three rows. R4 says a row with no
semantic bridge is `blocked`, never a class; at minimum the count and the dispositions disagree with
the doc's own cells. (`T12_AUDIO.md:58` also mixes "V-04 file check" and "blocked:" in one cell.)

### 9. Minor — "the looping is done by the event/tune graph" is an inference, not a measurement

`T12_AUDIO.md:203-206`, `t12_audio_map.json` `method.loop`. What was measured is that the 33 slots
report no loop fields through vgmstream (I re-checked four, including the three names containing
`loop`). Concluding that the loop therefore lives in the event/tune graph is not shown by any file
read here — the FSB5 could simply not carry loop metadata for this bank version, and the
sound-instance/plugin configuration is not parsed. It is stated as fact (R4), and B-11 will rely on
it.

### 10. Minor — A-04's match cell asserts an unevidenced meaning for a name family

`T12_AUDIO.md:112`: *"the `performance` shift family is the sports-car set in vehicles.bank (the
donor is the sports-muscle chassis)"*. Nothing read here establishes that `performance` denotes
sports cars; it is a plausibility argument in a `match` cell, which is exactly the member-name →
behaviour leap R5 warns about (the row is otherwise correctly `candidate`).

### 11. Cosmetic

`T12_AUDIO.md:97,99` print *"1 candidates"*; the peak column prints `-0.00` for two slots (`:181`,
`:183`); `source_frames` is computed as `duration_s × 48000` (`t12_audio.py:539`) for every bank,
which happens to be right only because all slots are 48 kHz — a 44.1 kHz slot would corrupt the
stretch silently.

---

## Spot-checks

Each value checked against the JSON and then against the raw data the script reads, not against the
doc.

| # | doc value | verified where | result |
|---|---|---|---|
| 1 | slot `vehicles/151` `jc3_veh_land_premium_nitro_loop`: 48,000 Hz, 1 ch, **154,818** frames, LUFS **−10.33**, gain **1.35**, stretch 1.6143 (`T12_AUDIO.md:181`) | re-decoded `vehicles.bank` index 151 with `Tools/vgmstream-win64/vgmstream-cli.exe` → *stream total samples: 154818*, 48,000 Hz, 16-bit PCM; integrated LUFS with `bmak_audio_features.integrated_lufs` = **−10.33**; JSON `source_frames` 95,904 = start WAV 1.998 s × 48k; gain = −10.33 − (−11.68) = 1.35 | match |
| 2 | A-06 gain **−16.39** (slot `vehicles/7`, LUFS −21.85) | JSON slot `vehicles/7` LUFS **−21.85**; `AUDIO_FEATURES.json` `Play_CockpitOpen` 3 WEMs, loudest **−5.46** → −21.85 − (−5.46) = **−16.39** | match |
| 3 | **22** pinned GUIDs no `.epe` object names / 45 donor events | `JC3_AUDIO_EVENTS.json` → `donor.events` 45, `donor.named` 23 → 22; the check's invariant (`unassigned_rows == 45 − 23`) reads those | match |
| 4 | **0** slots with an FSB5 loop chunk (`T12_AUDIO.md:15,203`) | vgmstream on `vehicles#151`, `weapons#408` (`minigun_fire_close_loop_04`), `weapons#1125` (`missile_trail_rear_loop`), `weapons#559`: no `loop start/end` lines on any; JSON `looped_slots` 0 | match |
| 5 | **34** engine-ish samples in `vehicles.bank` (`T12_AUDIO.md:271`) | FSB5 name table: 34 names contain `engine` | number matches; the "seven families / eight names" half does not (issue 6) |
| 6 | the doc's "no event→tune edge" (`T12_AUDIO.md:269`) | `TLNB` tune entry at byte 55,181,586 carries event GUID `100cbd8f-…`; `905be2e5-…` (`engine_running_sound`) occurs at byte 55,183,562 inside the same list | **contradicts the doc** (issue 1) |
| 7 | Aston engine layer census ("five") | name table: `idle_high` 127, `high` 236, `medium_low` 390, `low2` 601, `idle2` 619, `medium_high2` 636 = **six** | **contradicts the doc** (issue 7) |

---

## What would make this card `sound`

1. Replace the "no event→tune edge" sentence (`T12_AUDIO.md:27,268-269`, the JSON `method.slot`,
   `MODLOG.md:12191,12279`) with what the file says: event→tune is stored in `TLNS`/`TLNB`; only
   tune→sample is UNKNOWN. Name each row's tune (45/45 are resolvable) so B-11 has one more verifiable
   hop.
2. Make the loudness check real: compute the LUFS of the **padded** payload (or say the pad is
   silence and report the resulting `10·log10` offset per slot), and assert `|payload_lufs −
   slot_lufs| ≤ 1`. Drop `residual_lu` or keep it as an arithmetic self-test, not as the gate.
3. Select the source per slot (or per row deliberately): A-02's loop/stop must use `EC2FD42B.wav`;
   A-01's gains must come from the engine event the row claims, not `Play_BML_EngineCoolTicks`.
4. Either choose A-01's slot (or mark AUD-1 `blocked`/`candidate` and stop counting it in `mapped`),
   and make the weapon rows read T-11's carriers instead of a typed list.
5. Add computed invariants for the typed prose: the engine-sample count and family list, the Aston
   layer count, and the D-8 rows' disposition (`blocked: D-8` rather than `kept vanilla`).

## Limits of this review

- Read-only: I did not run the MODLOG's three tamper tests (they require editing the JSON/MD). The
  comparison paths are real code — `have != d` (`t12_audio.py:903`) and a byte compare of the
  re-rendered MD (`:911-913`) — and the negative slot test in
  `invariants()` (`:814-820`) exists, so the MODLOG's tamper claims are plausible but not
  reproduced here.
- No game launched, so every Q-1/Q-2/Q-3 audition listed in the verify cells is unverified by
  construction.
- I opened `E:\Modding\JustCause3\_grab\audio\weapons.bank` only because the doc names that exact path and
  the script reads it; nothing there was modified.
- LUFS arithmetic in issue 2 assumes the pad is silence. The doc does not say, which is itself the
  defect: if the pad is a repeat instead, the doc should say so and the ±1 LU claim changes shape.

## Files touched by this review

`tmp/freebuff/reports/review-T-16.md` (this file) and two throw-away WAVs under `tmp/freebuff/`
produced by vgmstream spot-checks, deleted in the same command. Nothing else.
