# T-16 rework — audio translation

Card: `GRAB_BACKLOG.md:924-930` (T-16, deps G1-15/G2-24, serves AUD-1…7).
Review under test: `tmp/freebuff/reports/review-T-16.md` (verdict `needs rework`, 11 issues).
Date: 2026-10-29. Read-only against game data; the only writes are the generator, its two generated
outputs, one §12 line and `MODLOG.md`.

**Change record (AGENTS.md).** Intended change: append `MODLOG.md` §"T-16 rework — intended change"
before any edit (done, 2026-10-29), then change `Tools/scripts/t12_audio.py` (the card's generator)
and regenerate `Working/Translation/T12_AUDIO.md` + `t12_audio_map.json` with `--write`. Why those
files: they are the card's `Out` paths and the generator is the only place a value may be set (R11).
Revert: restore the four files from `tmp/t16rework/` and re-run `t12_audio.py --write`; truncate
`MODLOG.md` at the intended-change heading.

## STATUS: **rework done — `--check` green**

| | |
|---|---|
| review issues | **10 CONFIRMED**, **1 partly REJECTED** (issue 2: the identity half is confirmed, the "1.4–6.9 dB low when padded" half is refuted by measurement) |
| review evidence corrected | 2 items (its `TLNB` byte reading; its engine-family census) |
| files changed | `Tools/scripts/t12_audio.py`; `Working/Translation/T12_AUDIO.md`; `Working/Translation/t12_audio_map.json`; the T-16 line of `GRAB_BACKLOG.md` §12; `MODLOG.md` |
| rows | 53 (45 donor + 8 weapon/mode) → `mapped` 5 · `kept vanilla` 7 · `named omission` 11 · `remove` 1 · `blocked` 29 |
| slots | 34 measured, 22 gain-matched **on the written payload**, 0 chosen slots outside ±1 LU, 5 candidates outside (named) |
| tunes | 24/45 rows carry the tune GUID their event owns (the other 21 are banks this card does not decode) |
| generated output | MD 295 → 339 lines / 34,579 → 43,571 B; JSON 140,849 → 181,839 B |

---

## Per-issue verdicts

Evidence is quoted from commands run in `E:/Modding/JC3-Batmobile`; nothing here is from memory.

### 1. "The premise *no event→tune edge* is false" — **CONFIRMED** (with a correction to the review's bytes)

Re-verified against `Working/Audio/jc3bank/sound/fmod_banks/vehicles.bank` through the G2-24 reader
(`jc3audio.fev / fev_events / fev_event_bodies / fev_tunes / fev_waves`):

```
events 257 tunes 257 waves 649
all 257 tune event_guids are EVTS guids: 257 / 257
JSON guid form matches bank raw form: 24 / 24        (the 24 donor rows in vehicles.bank)
tunes whose owner event body holds the tune guid at offset 32: 257 / 257
TLNS section bytes 95544 wave guids found in it: 0
first tune: {'index': 0, 'tune_guid': '00abd8a3904926478d56fe4682b6df55',
             'event_guid': '100cbd8f9b9f8749b853632b33d167e9', 'bytes': 164}
```

The first tune is owned by `100cbd8f-…` = vehicles/15 = `ground_roughness_sound_attached`, i.e. the
edge is stored in the tune list **and** in the event body. So `T12_AUDIO.md:27,268-269`, the JSON
`method.slot` and the two MODLOG sentences were a false negative (R4).

*Correction to the review:* the `TLNB` body has **no** 4-byte zero prefix. It is
`[16-byte tune GUID][16-byte event GUID]` in the same byte order as the GUID strings
(`00 ab d8 a3 90 49 26 47 …` at body 0, `10 0c bd 8f 9b 9f 87 49 …` at body 16). The review's
`90a3d8ab-2649-…` reading (little-endian UUID re-interpretation) is a mis-parse of the same bytes.

**Fix:** the generator now reads this edge (`bank_tunes()`), the doc carries a new section
"Event → tune (the edge the bank does store)" with the counts above and a per-row tune table, every
vehicles-bank row carries `tune: {tune_guid, index, owner_matches_row}`, and `method.slot` /
UNKNOWN #1 now say event→tune **is** stored and only tune→sample is not. Invariants assert
257/257 on both sides and 0 wave GUIDs in `TLNS`.

### 2. "The ±1 LU gate is an identity and cannot fail" — **CONFIRMED (identity) / REJECTED (the padding arithmetic)**

Identity half — confirmed from the old code (`t12_audio.py:535-539`, `838-841`):
`gain = slot − target`, `residual = target + gain − slot` ≡ 0, gate `max |residual| > 1` can never
fire. The old MD's "max |residual| 0.00 LU" and the §12 row presented that as the loudness match.

Padding half — **rejected by measurement**. The review assumed the pad scales integrated loudness by
`10·log10(frames/src)`. BS.1770-4 gates silence out, so it does not. Measured on the payloads the
swap actually writes:

| slot | stretch | pad / trim | delivered − slot |
|---|---|---|---|
| A-05 `vehicles#279` (pad 267,437 frames, stretch 4.902) | 4.902 | pad | **−0.54 LU**, not −6.9 dB |
| A-02 `vehicles#151` (trim 1, stretch 1.6143) | 1.614 | trim 1 | **0.00 LU** |
| A-01 `#127/#236/#390/#601/#619/#636` (pad 22k–47k, stretch 1.38–1.74) | 1.38–1.74 | pad | −0.16…+0.23 LU |
| W-03 `weapons#408` (pad 80,213, stretch 2.001) | 2.001 | pad | −0.57 LU |

Two slots do move: trimming (`weapons#469`, 8,081 frames of a fire loop → −16.78 LU) and clipping
(`vehicles#57`, +12.74 dB → 10.29 % clipped → −1.59 LU). Both are now reported.

**Fix:** `residual_lu` is gone. `delivered_lufs` is measured on the payload B-11 would write — mono
downmix (`mean`, as `_apply_audio.py` does), gain, trim/pad with zeros to the slot's frame count,
PCM16 clip + quantise — and `delta_lu = delivered − slot`, `clip_pct`, `padded_frames`,
`trimmed_frames` are stored per slot. `--check` hard-fails when a **chosen** slot is outside ±1 LU;
every other slot's delta is printed in the slot table and the count/list of over-gate slots is in
the summary.

### 3. "A-01's gain comes from a cool-tick event; A-02's loop/stop from the start WAV" — **CONFIRMED**

Old behaviour, reproduced from the code and the old JSON: `target = next(s["source"] for s in
sources if s.get("source"))` on `sorted(..., key=name)` sources. A-01's JSON row listed 12 events,
its target was `Play_BML_EngineCoolTicks` (−8.65 LUFS stored), and `Play_Batmobile_Rotation`,
Clutch, Positional, Reverse and the transitions were pulled in by the `group=engine &
rtpc=REV_RPM` filter — none of them the engine bed. A-02's `sources` were start.wav (−11.68, 1.998 s
→ `source_frames` 95,904) and `EC2FD42B.wav` (−12.77, 3.819 s); both were measured and only the
first was used, for all three slots.

**Fix:** per-slot targets with provenance.
* A-01's target is `Play_Batmobile_Idle` (group `engine`, **no** RTPC bindings, 5 WEMs measured at
  −11.97…−14.95 multi-channel) plus `Play_BML_EngineCoolTicks` (22 WEMs, binds `REV_RPM`); the other
  `engine`-group events are no longer sources. Its match text now says the idle event is the bed and
  that the "5 RPM layers" reading of its WEMs is not in the data.
* A-02 carries `slot_src` with **test-060's own spans** from `Tools/scripts/_apply_audio.py` JOBS:
  `#56 ← jc3_batmobile_start.wav` first 0.7445 s, `#150 ← EC2FD42B.wav` first 3.2254 s,
  `#355 ← EC2FD42B.wav` last 0.756 s. Gain and stretch are measured on that span.
* "loudest variant" now means loudest **as the payload reads it** (mono downmix), not the shipped
  multi-channel LUFS — a 6-channel WEM can lead on the latter and be the quietest mono payload
  (e.g. `Play_Batmobile_GearShift_Up` WEM `0x073E4D18`: stored −8.65, mono −22.04).

### 4. "A-01 is counted `mapped` with no chosen slot and no gain" — **CONFIRMED**

Old JSON: `A-01 … "dispo": "mapped", "chosen": null`, no `gain_db` on its five candidate slots, while
the summary and §12 said "7 mapped". R4: a row whose target is undecided is not `mapped`.

**Fix:** A-01 is `blocked` with `verify = "blocked: Q-1 #8 - …"`, and `mapped` now requires a chosen
slot **and** a measured delta (invariant). `mapped` 7 → 5. Measured consequence: AUD-1's only mapped
row is A-06 (door open); AUD-1's engine row waits for the audition.

### 5. "The Done criterion's *explicitly kept vanilla* is the default path" — **CONFIRMED**

Old `finish()` filled every unspecced event with `dispo="kept vanilla"` and one fixed verify
("V-04 file check: event kept exactly as shipped"); 22 of the 32 kept-vanilla rows were that default
(the `D-01…D-22` block), and `invariants()` could not tell a decision from its absence.

**Fix (R4):** the fallback is now `blocked`, with a verify that names the probe ("keeping it exactly
as shipped is the default, not a decision; an audition has to say whether this shared bank event is
audible on the car"). `kept vanilla` must come from a `SPECS` entry — an invariant now fails any
`kept vanilla` row without a spec. `kept vanilla` 32 → 7.

### 6. "Two typed counts in the renderer, one self-contradictory" — **CONFIRMED**

Old MD: "34 engine-ish samples across seven model families (Aston, Ducati, moped, fiat, saab, volvo,
train, tank)" — eight names for seven, typed in `render_md` as literals, so `--check` re-rendered
them unchanged. Recount from the name table (`JC3_AUDIO_EVENTS.json → samples.list`, 649 names):

```
names containing 'engine': 34
aston_martin_vantage_engine_rpm_*: 6
stacks: aston_martin_vantage 6, ducati_desmosedici 5, train_military 5
```

So the "34" reproduces with a `"engine" in name` filter; the family sentence does not.

*Correction to the review:* its own recount ("five families: aston 8, ducati 8, train 7, tank_m8 7,
fiat 1, plus 10 generic") does not reproduce either — the engine-named names are aston 8, ducati 8,
train 7, fiat 1, ferrari 2, generic damage/smoke 8 (34 total), and no `tank_m8_*` name contains
`engine`. The doc no longer types a family count at all.

**Fix:** `build()` derives an `engine_census` (`names`, `engine_named`, `rpm_stacks` grouped by the
prefix before `_engine_rpm_`) and the MD renders those numbers; no literal survives.

### 7. "The *only 5-layer RPM stack* — the bank has six" — **CONFIRMED**

```
aston_martin_vantage_engine_rpm_*: 6
  idle_high (127) high (236) medium_low (390) low2 (601) idle2 (619) medium_high2 (636)
```
A-01 listed five and silently dropped `idle_high`; the "five" was typed prose
(`t12_audio.py:89-91`) presenting a selection as a structural fact.

**Fix:** A-01 lists all six, its method text carries no numeral, and an invariant asserts both the
SPECS list and the row's slot list equal the largest `_engine_rpm_` stack derived from the name
table (tamper: dropping one layer → `A-01 carries 5 of the 6 aston_martin_vantage layers`).

### 8. "Three D-8 rows are `kept vanilla` while their own cell says `blocked: D-8`" — **CONFIRMED**

Old `T12_AUDIO.md:58,64,91` (A-08, A-10, A-23): `dispo = kept vanilla`, verify beginning
`blocked: D-8`, so the summary said "blocked 2" while MODLOG named D-8 open on three rows.

**Fix:** all three are `blocked`, and an invariant now requires every `blocked` row's verify to start
with `blocked:` (so a cell and its disposition cannot disagree again). `blocked` 2 → 29.

### 9. "The looping is done by the event/tune graph — inference, not measurement" — **CONFIRMED**

What is measured: `loop_start` is null on all 34 measured slots (0 with an FSB5 loop field). What was
asserted: that the event/tune graph therefore does the looping. Nothing read here parses the sound
instances' plugin/loop configuration, and a bank build without loop metadata would look identical.

**Fix:** the MD paragraph and `method.loop` now say the measured fact and then **UNKNOWN**: whether
the loop comes from the event/tune graph, or the bank simply carries no loop metadata, was not
measured.

### 10. "A-04's match cell asserts an unevidenced meaning for a `performance` name family" — **CONFIRMED**

The old cell ("the `performance` shift family is the sports-car set in vehicles.bank") is a
plausibility argument from a member name — exactly R5's failure mode. Neither `AUDIO_FEATURES.json`
nor the sample name table maps a shift family to a car class.

**Fix:** the claim is gone. The method now says: the three `performance` samples are one of the
shipped shift families (counted from the name table), and what `performance` denotes is not measured
— the audition decides. Measured while checking it: A-04 cannot meet the ±1 LU gate at all (below),
so it is `blocked`, not `mapped`.

### 11. "Cosmetic" — **CONFIRMED**

All three: `1 candidates` (two rows), `-0.00` in the peak column (five slots), and
`source_frames = duration_s × 48000` for every bank (`t12_audio.py:539`).

**Fix:** proper pluralisation; `fnum()` normalises negative zero (`|v| < 0.5·10⁻ⁿ → 0`); and
`source_frames` now comes from the payload source's own frame count — the WAV's sample count for
`*.wav` sources, vgmstream's `stream_total_samples` for WEM-backed ones — with a hard stop if a
source is not 48 kHz.

---

## Found while reworking (not in the review)

The first honest measurement of "the payload the swap writes" produced three slots that **cannot**
reach their slot's loudness within ±1 LU:

| slot | why | measured |
|---|---|---|
| `vehicles#15 #54 #362` (A-04, three `performance` shift slots) | BmAK shift WEMs are 6-channel; mono downmix lands ~11 LU below the slots, so the gain that reaches the slot clips | gain +9.75…+11.00 dB, 2.1–7.5 % clipped, delivered **+3.52…+3.68 LU** |
| `vehicles#57` (A-02 `premium_nitro_start`) | slot is mastered at −10.03 LUFS, the start WAV's first 0.7445 s at −22.77 | gain +12.74 dB, 10.29 % clipped, delivered **−1.59 LU** |
| `weapons#469` (W-03 `minigun_endclick`) | the slot is 8,081 frames; trimming the fire loop to it keeps only the quiet tail | gain −8.59 dB, delivered **−16.78 LU** |

None is a chosen slot, so the gate is green; all five are listed in the MD summary and their rows
carry the fact. A-04 is `blocked` because of it (decision: accept the clip or keep the stock shift).

---

## Files changed

| file | change |
|---|---|
| `Tools/scripts/t12_audio.py` | generator: `bank_tunes()` (event→tune), `measure_source()` / `build_payload()` (delivered-loudness gate), per-slot targets + `slot_src` spans, mono-loudest variant, A-01/A-04 dispositions and sources, loop + `performance` text, derived engine census, fallback `blocked`, new invariants, pluraliser/`fnum`/`source_frames` fixes, new summary + render sections |
| `Working/Translation/T12_AUDIO.md` | regenerated by `--write` (339 lines, 43,571 B) |
| `Working/Translation/t12_audio_map.json` | regenerated by `--write` (181,839 B) |
| `GRAB_BACKLOG.md` §12, T-16 line | one line — evidence summary updated (5 mapped / 7 kept vanilla / 29 blocked, 34 slots, 22 gain-matched on the written payload, event→tune 257/257, 24/45 tunes) |
| `MODLOG.md` | §"T-16 rework — intended change" and §"T-16 rework — done" (append-only) |

Backups for the revert: `tmp/t16rework/{t12_audio.py,T12_AUDIO.md,t12_audio_map.json,GRAB_BACKLOG.md}.bak`.
No game launched, nothing written under `D:/Games`, no shared game module edited, no git commit.

## `--check` output (verbatim)

```
$ python Tools/scripts/t12_audio.py --check
PASS: 53 rows = 45/45 donor events + 8 weapon/mode rows | dispositions {'blocked': 29, 'kept vanilla': 7, 'mapped': 5, 'named omission': 11, 'remove': 1} | 5 mapped with 5 chosen slot(s) | 34 slot candidates (22 gain-matched on the written payload, max |delivered-slot| 16.78 LU, 5 over 1 LU - chosen 0; 12 kept stock) | tunes 24/45 | 2 rpm curves | features 7/7 | json match True, md match True
EXIT=0
```

```
$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 40 keep 60 epe 26 re-read 0 blocked 13 out 36 superseded 7 | edits 35 over 16 rows
check ok
EXIT=0
```

```
$ python Tools/scripts/status_audit.py --check
STATUS.md is current
EXIT=0
```

## Tamper test (9/9 caught, each restored → `--check` PASS)

| tamper | result |
|---|---|
| JSON `summary.mapped_rows` 5 → 6 | exit 1, `FAIL: json stale: summary` |
| a row's `dispo` `blocked` → `mapped` | exit 1, `FAIL: json stale: rows` |
| MD summary `**53**` → `**54**` | exit 1, `FAIL: md differs: @@ -11,3 +11,3 @@ … rows | **54** …` |
| MD tune-table header deleted | exit 1, `FAIL: md differs: @@ -285,2 +285,3 @@ … | row | role | tune GUID | tune # |` |
| a chosen slot's `delta_lu` → 2.0 | `A-02/A-06/A-05/A-07/W-03 chosen slot … misses the 1 LU gate (+2.00 LU)` |
| A-04 set back to `mapped` (chosen `null`) | `A-04 is mapped with no chosen slot` |
| an unnamed GUID set to `kept vanilla` | `D-01 is kept vanilla without a SPECS decision` |
| `owner_body_holds_tune` 257 → 256 | `256/257 event bodies hold the tune GUID at offset 32` |
| A-01 truncated to 5 layers | `A-01 carries 5 of the 6 aston_martin_vantage layers` |

## Still UNKNOWN (not fixable from the files read)

* **tune → sample** — 0 of 649 sample GUIDs occur in `TLNS`; the rest of the tune body is not decoded.
* **the 21 donor rows in `character.bank` / `effects.bank`** — this card decodes `vehicles.bank` only,
  so their tune GUIDs and their slot sources stay UNKNOWN (G2-24 owns those banks).
* **the RTPC y target** (volume / pitch / low-pass) and **JC3's missing speed/boost parameter** — as
  the old doc said; unchanged.
* **whether a bank swap alone silences the horn** — data side vs input binding (Q-1).
* **which engine family the donor's `engine_running_sound` tune plays** — A-01 stays `blocked` on
  Q-1 #8; the six Aston layers are candidates, not a decision.
