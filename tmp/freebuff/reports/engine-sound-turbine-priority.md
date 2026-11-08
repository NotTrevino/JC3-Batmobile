# Engine sound: turbine first

**STATUS: done (report only).** The newest engine-audio plan is
`tmp/freebuff/reports/engine-audio-layers-plan.md` (no later one exists — `tmp/freebuff/reports/*audio*`
holds 14 files, that is the only `engine-audio*`). This report re-ranks its layer table so the
**turbine layers take the first slots JC3's engine event offers**, per the operator ruling of
2026-11-08 ("Engine identity leans **turbine whine**", `ROADMAP.md:152`; recorded with the rest of the
gameplay facts at `MODLOG.md:21357`).

It changes no card, plan, bank, build or ledger row. Measurements are in
`Research/BatmobileGrab/ENGINE_TURBINE_SCAN.json` (digest `f61f1286e2f548b6`), produced by the new
read-only `Tools/scripts/engine_turbine_rank.py` (`--write`, `--check`, both run).

---

## 1. Verdict

1. **The re-rank costs nothing structurally and buys the identity.** Of the 6 engine sample slots the
   plan says a same-length swap can fill (`engine-audio-layers-plan.md` §6.1), **slots 1–5 go to turbine
   layers and slot 6 keeps the V8/exhaust double.** Neither the FSB5 writer nor the FEV graph is needed
   for that order — it is a change of *which donor goes in which shipped slot*, not a new slot.
2. **The turbine character is measurable and it is concentrated in exactly the five looped MK2 beds.**
   197 distinct engine-group media were measured; 44 are turbine-led, but only **five are sustained
   (12.3–13.7 s) *and* carry loop points**: `0x330DC554`, `0x3A44A5AD`, `0x22ED52BC`, `0x3B7D6AFA`,
   `0x1D0717F0`. Those five are the only BmAK media that are simultaneously (a) tonal in the whine band,
   (b) bright against the V8 region, and (c) loopable. They are the re-ranked bed.
3. **Every fill is a loop-repeat plus a tail trim, never a straight copy.** The five donors are
   12.3–13.7 s; the JC3 slots are **1.97–2.49 s** (94,376–119,392 frames). Their loop windows are
   0.93–1.52 s, so a slot takes 1–2 whole repeats and leaves 2,016–25,779 frames of tail to trim or
   crossfade (§5).
4. **Nothing the plan called "NEEDS NEW ENTRY" has to be solved to get turbine-first.** The
   pitch-fall `POS-mid-fall-a/b`, the `low-rise`/`lowmid-rise` bends, the reverse bed, the clutch, the
   cool ticks and the battle engine all now sit **below** the six slots and stay unbuilt (§6). The only
   layer family whose priority question the operator's ear can still overturn is which of the five
   looped beds gets slot 1.
5. **The battle-mode engine sample does not sound like the turbine.** `Play_BattlemodeEngine`'s looped
   `0x20E7C1E0` (21.897 s, loop 0.470–6.183 s) measures **T = −46.81 dB, low-band share dominant**
   (V8-LED) — the loudest tonal peak in it is a 1207 Hz body resonance, not a whine. Do not use it as a
   turbine source. Its one-shot `0x04F89F98` (8.917 s) is only weakly turbine (T = 1.87).
6. **JC3 already ships turbine-first samples** (mono, 48 kHz, in `vehicles.bank`): `jc3_veh_air_jet_fighter_01_jet_turbine_04`
   (150,738 frames), `jc3_veh_air_cargo_plane_turbine_drone` (204,807), `jc3_veh_ferrari_275_engine_whir_loop`
   (102,994), plus three `transmission_whine_forward_*` and a `nitro_jet_flame_loop`. That is a second,
   even cheaper route to the same identity (§5.2) and should be auditioned beside the BmAK donors.

---

## 2. What "turbine character" means here, and how it was measured

The plan already states the hard limit that decides how this had to be done: **a Wwise blend container's
track names are not stored** and the RTPC property (volume vs pitch) is not decoded
(`engine-audio-layers-plan.md` §0, §8). So "which WAV carries the turbine" cannot be a name lookup; it has
to be a measurement of the audio, and it is a **derived** classification, exactly like the plan's
volume/pitch split.

Two axes, both from an averaged power spectrum (4096-sample Hann, 2048 hop, mono downmix,
`Tools/scripts/engine_turbine_rank.py`):

| axis | definition | what it separates |
|---|---|---|
| **T** | `10·log10( E[2 kHz…10 kHz] / E[20…300 Hz] )` | brightness against the V8 combustion region |
| **P** | `10·log10( max(P[1.2 kHz…8 kHz]) / median(P[1.2 kHz…8 kHz]) )` | narrowband tonality — a whine is a *line*, an engine is a *comb* |

Class rule (stated so it can be argued with):

* **TURBINE-LED** — `T ≥ 0` **and** `P ≥ 10` **and** the peak inside 1.2–8 kHz is `≥ 1200 Hz`
* **V8-LED** — `E[20…300] / E[20…16k] ≥ 0.45` **and** the 20–400 Hz peak is `< 500 Hz`
* **MIXED** — otherwise

Ordering inside the class is `T + 0.5·P`; both axes are printed in the JSON so the order can be
re-derived by hand.

**Counts (engine + battle-mode groups, `AUDIO_FEATURES.json`):**

| fact | value |
|---|---|
| rows (event × media pairs) | 561 |
| measured | **517** |
| distinct media | **197** |
| turbine-led | **44** |
| v8-led | 130 |
| mixed | 23 |
| **with loop points** | **6** |

The 44/197 split is the headline: turbine is **not** the majority character of the engine group — it is a
minority that happens to sit almost entirely in the looped MK2 bed and in the rotation/tick one-shots.

---

## 3. The BmAK WAVs that carry the turbine character

### 3.1 Sustained (≥ 2 s, or looped) — 18 media

`T` / `P` in dB, `peak` is the strongest line in 1.2–8 kHz, `low` the 20–400 Hz peak, `loop` the frame
pair vgmstream reports.

| WAV | event | s | ch | T | P | peak Hz | low Hz | loop (frames) | class |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| `0x330DC554` | MK2_Engine_Transition_In / Positional / Reverse | 12.911 | 3 | **24.04** | 29.60 | 3398 | 387 | 34685–87196 (52,511) | TURBINE |
| `0x3A44A5AD` | MK2_Engine_Transition_In / Positional / Reverse | 12.924 | 3 | **21.22** | 33.58 | 1242 | 387 | 30661–85508 (54,847) | TURBINE |
| `0x0F82364C` | Play_Batmobile_Rotation / Persistent_idles | 4.677 | 2 | 15.66 | **43.93** | 3773 | 398 | — | TURBINE |
| `0x0728BD5A` | MK2_Reverse | 3.264 | 1 | 18.04 | 38.78 | 1207 | 387 | — | TURBINE |
| `0x22ED52BC` | MK2_Engine_Transition_In / Positional / Reverse | 12.336 | 3 | **21.57** | 29.52 | 2273 | 70 | 23053–67589 (44,536) | TURBINE |
| `0x3B7D6AFA` | MK2_Engine_Transition_In / Positional / Reverse | 13.673 | 3 | **18.64** | 30.43 | 1547 | 363 | 30479–103394 (72,915) | TURBINE |
| `0x1D0717F0` | MK2_Engine_Transition_In / Positional / Reverse | 12.835 | 3 | **15.30** | **36.39** | 1699 | 47 | 29723–82890 (53,167) | TURBINE |
| `0x188AB1BF` | MK2_Reverse | 2.286 | 1 | 14.00 | 35.25 | 1207 | 375 | — | TURBINE |
| `0x06A0436C` | MK2_Reverse | 2.154 | 1 | 13.72 | 35.48 | 1230 | 398 | — | TURBINE |
| `0x20BB89C9` | MK2_Reverse | 4.503 | 1 | 14.91 | 30.77 | 1219 | 398 | — | TURBINE |
| `0x0525C099` | MK2_Reverse | 2.567 | 1 | 14.41 | 30.85 | 1207 | 398 | — | TURBINE |
| `0x019C7EA6` | MK2_Reverse | 3.855 | 1 | 11.70 | 35.73 | 1230 | 398 | — | TURBINE |
| `0x1353277E` | MK2_Reverse | 2.083 | 1 | 13.80 | 31.23 | 1207 | 387 | — | TURBINE |
| `0x04E9DFA9` | MK2_Reverse | 2.946 | 1 | 12.87 | 32.29 | 1230 | 398 | — | TURBINE |
| `0x0437324E` | MK2_Reverse | 2.613 | 1 | 11.44 | 30.76 | 1207 | 398 | — | TURBINE |
| `0x0FDCA3EE` | MK2_Reverse | 2.849 | 1 | 12.12 | 29.18 | 1230 | 398 | — | TURBINE |
| `0x0D719316` | Play_Batmobile_Rotation | 4.228 | 2 | 4.21 | 22.78 | 1934 | 281 | — | TURBINE (weak) |
| `0x20E7C1E0` | Play_BattlemodeEngine | 21.897 | 2 | **−46.81** | 36.32 | 1207 | — | 22539–296799 (274,260) | **V8-LED** |

Readings that matter for the rank:

* **The five 3-channel MK2 beds are the turbine bed.** They are the same five media in
  `Play_Batmobile_Positional`, both `Transition_*` events and `Reverse`, i.e. one bank object serves the
  whole MK1 and MK2 positional graphs. Their low peaks (47–387 Hz) prove they still carry a body, so a
  turbine-first fill does not make the car sound like a hairdryer with no mass.
* **`0x1D0717F0` is the purest whine** (P = 36.39, low peak 47 Hz) and **`0x330DC554` the brightest**
  (T = 24.04, peak 3398 Hz). Those two are the natural "identity" pair for slots 1 and 2.
* **`0x0F82364C`** (Rotation, 4.677 s) has the highest tonality of anything in the group (P = 43.93 at
  3773 Hz) but it is a tick layer, not a bed — good as the high-rpm shriek, wrong as the idle bed.
* **The other 13 sustained turbine-led rows are MK2 *reverse* one-shots** (1-channel, 2.0–4.5 s) and the
  weak `0x0D719316`. They are candidates for a reverse bed only, which has no slot (§6).

### 3.2 Short media (the 44th-of-197 tail)

The remaining turbine-led media are 0.10–0.70 s one-shots in `Play_Batmobile_Rotation` /
`Play_BML_EngineCoolTicks` and the `Play_BattleMode_In*` transitions. The top of that list:

| WAV | event | s | T | P | peak Hz |
|---|---|---:|---:|---:|---:|
| `0x27109DA4` | Rotation / CoolTicks | 0.281 | 42.00 | 36.32 | 1242 |
| `0x38A7BA6E` | Rotation / CoolTicks | 0.322 | 49.93 | 20.17 | 1301 |
| `0x39D07B7A` | Rotation / CoolTicks | 0.103 | 48.72 | 20.03 | 1312 |
| `0x22E014C0` | Rotation / CoolTicks | 0.348 | 42.67 | 31.53 | 1840 |
| `0x033E6189` | Rotation / CoolTicks | 0.187 | 38.78 | 33.30 | 1312 |
| `0x181579D5` | Rotation / CoolTicks | 0.270 | 38.39 | 29.39 | 1242 |
| `0x2990B754` | Rotation / CoolTicks | 0.270 | 34.18 | 36.02 | 1301 |
| `0x3C46FAA0` | BattleMode_In_E | 0.395 | 29.34 | 16.06 | 1957 |
| `0x2E5DBF80` | BattleMode_In_D | 0.218 | 31.68 | 11.06 | 1594 |

Event-level aggregate (from the JSON `events` array): `Play_Batmobile_Rotation` and
`Play_BML_EngineCoolTicks` are **16 / 22 media turbine-led** each; `Play_Batmobile_MK2_Reverse` is
**11 / 21**; `Play_Batmobile_Positional` is **5 / 51**; `Play_Batmobile_Idle`, `MK2_Idle`, `Clutch`,
`GearShift_Up`, `DistantRev` are **0 / 5** each (all V8-LED).

So the turbine lives in *three* places: the looped MK2 bed (the only bed), the rotation/cool ticks, and
the battle-mode enter transitions. Only the first is a bed; the other two are events with no slot.

---

## 4. Loop points — measured, and the reason the fills are trims

vgmstream (the repo's decoder, `Tools/vgmstream-win64/vgmstream-cli.exe`, run by
`bmak_audio_features.py` and captured into `AUDIO_FEATURES.json` `media[].loop_lines`) reports loops on
**6 of the 197** engine-group media:

| WAV | event | total s | loop start | loop end | loop length |
|---|---|---:|---|---|---:|
| `0x330DC554` | MK2_Engine_Transition_In / Positional / Reverse | 12.911 | 34,685 (0.723 s) | 87,196 (1.817 s) | **52,511 (1.094 s)** |
| `0x3A44A5AD` | same | 12.924 | 30,661 (0.639 s) | 85,508 (1.781 s) | **54,847 (1.143 s)** |
| `0x22ED52BC` | same | 12.336 | 23,053 (0.480 s) | 67,589 (1.408 s) | **44,536 (0.928 s)** |
| `0x3B7D6AFA` | same | 13.673 | 30,479 (0.635 s) | 103,394 (2.154 s) | **72,915 (1.519 s)** |
| `0x1D0717F0` | same | 12.835 | 29,723 (0.619 s) | 82,890 (1.727 s) | **53,167 (1.108 s)** |
| `0x20E7C1E0` | Play_BattlemodeEngine | 21.897 | 22,539 (0.470 s) | 296,799 (6.183 s) | 274,260 (5.714 s) |

What this does and does not say:

* A **loop point is a property of the stream**, and five of the six are the MK2 bed — which is why the
  re-rank is cheap: those five are the only media in the group that *can* be laid into a short slot
  without cutting a one-shot's transient.
* **No loop points ≠ one-shot.** The absence only means this decoder sees no loop flag; the Wwise event's
  looping is carried by the event/container, which `AUDIO_FEATURES.md` §Method says this toolkit has not
  pinned. `Play_Batmobile_Idle`, `Clutch`, `MK2_Idle` are stationary beds by role and still report none.
* Every one of the five has a **loop window between 0.93 s and 1.52 s**, and the JC3 slots are
  1.97–2.49 s. The arithmetic in §5 follows directly.

---

## 5. The ranked table: turbine into the first slots

### 5.1 The re-rank

Slot order is the order the plan lists the six engine slots in (§6.1), idle → high rpm. Frames and
seconds are the slot's fixed capacity (a swap is frame-locked, `engine-audio-layers-plan.md` §6.3).

| # | JC3 slot | name | frames | s | **donor (ranked)** | donor loop | repeats + tail | donor T / P |
|---:|---:|---|---:|---:|---|---|---|---|
| **1** | 127 | `aston_martin_vantage_engine_rpm_idle_high` | 113,272 | 2.360 | **`0x330DC554`** | 52,511 | 2 reps + 8,250 | 24.04 / 29.60 |
| **2** | 619 | `aston_martin_vantage_engine_rpm_idle2` | 119,392 | 2.487 | **`0x3A44A5AD`** | 54,847 | 2 reps + 9,698 | 21.22 / 33.58 |
| **3** | 601 | `aston_martin_vantage_engine_rpm_low2` | 111,710 | 2.327 | **`0x22ED52BC`** | 44,536 | 2 reps + 22,638 | 21.57 / 29.52 |
| **4** | 390 | `aston_martin_vantage_engine_rpm_medium_low` | 98,882 | 2.060 | **`0x3B7D6AFA`** | 72,915 | 1 rep + 25,967 | 18.64 / 30.43 |
| **5** | 636 | `aston_martin_vantage_engine_rpm_medium_high2` | 98,694 | 2.056 | **`0x1D0717F0`** | 53,167 | 1 rep + 45,527 → **prefer 2 reps on slot 3/601 instead** | 15.30 / 36.39 |
| **6** | 236 | `aston_martin_vantage_engine_rpm_high` | 94,376 | 1.966 | **keep the V8/exhaust double** (turbine alternate: `0x0F82364C`, cut to 94,376 of 224,544) | — | straight cut | 15.66 / 43.93 |

Notes on the ordering:

* Rank inside the five is `score = T + 0.5·P`: **330DC554 (38.84) → 3A44A5AD (38.01) → 22ED52BC (36.33)
  → 3B7D6AFA (33.86) → 1D0717F0 (33.50)**. That is the table above; it puts the brightest bed in slot 1
  so the identity is audible from idle.
* `0x1D0717F0` is the *purest* whine but its loop is the shortest (1.108 s), so in a 2.056 s slot it is
  one repeat plus a 0.95 s tail — the least efficient fill of the five. If the operator's ear prefers its
  timbre, swap it into slot 3 (`601`, 2.327 s) where two full repeats fit (2 reps + 5,376) and move
  `0x22ED52BC` to slot 5.
* Slot 6 stays V8 deliberately: it is the only slot where the stock exhaust double still defines the top
  of the range, and a 3773 Hz tick layer cut to 1.97 s would read as a shriek over a cut, not a bed.
* All five donors are **3-channel**; the slots are **mono PCM16**. The fill needs a mono downmix first
  (§7.3).

### 5.2 The cheaper second route: JC3's own turbine samples

`JC3_AUDIO_EVENTS.json` `samples.list` (649 entries) already contains turbine/whine material in the very
bank the swaps write into:

| slot | name | frames | s |
|---:|---|---:|---:|
| 497 | `jc3_veh_ferrari_275_engine_whir_loop` | 102,994 | 2.146 |
| 484 | `jc3_veh_air_jet_fighter_01_jet_turbine_04` | 150,738 | 3.140 |
| 631 | `jc3_veh_air_cargo_plane_turbine_drone` | 204,807 | 4.267 |
| 403 / 565 / 645 | `jc3_veh_transmission_whine_forward_02 / _01 / _03` | 113,889 / 81,551 / 121,748 | 2.372 / 1.699 / 2.536 |
| 285 | `jc3_veh_transmission_whine_reverse_03` | 58,547 | 1.220 |
| 165 | `jc3_veh_land_premium_nitro_jet_flame_loop` | 132,615 | 2.763 |

`106` (`whir_loop`, 2.146 s) and `403` (2.372 s) are within 0.1–0.3 s of slots 1–3, and `403`/`645` are
**mono already**. This route needs no BmAK decode at all and keeps the whole "JC3-native, no new entry"
property. It is not ranked above the BmAK beds because nothing here has been auditioned against the
operator's ear, and the BmAK beds carry measured body (low peak 47–387 Hz) that a pure whine sample may
not. **Audition both in the same session before committing slot 1.**

### 5.3 What the fills are, mechanically

For each row: take the donor, downmix to mono, cut exactly the loop window, repeat it
`⌊slot_frames / loop_frames⌋` times, then trim (or crossfade) the residual. Residual per row is in the
table; the smallest is **2,016 frames** (`0x3A44A5AD` → slot 601, if slot 3 were reassigned) and the
largest is 45,527 (→ slot 636). A crossfade of 50–200 ms at the join is required to avoid a click; the
residual is exactly the length that crossfade consumes in the two bad rows.

---

## 6. Layers that stay unbuilt without an FMOD/FSB5 writer

Unchanged from the plan's write-path finding (§6.3: in-place FSB5 payload swap is proven; adding a sample
slot needs an FSB5 writer that does not exist under `Tools/scripts/`; the FEV graph cannot be authored),
but **re-ordered**: everything below the six slots is now explicitly lower priority than turbine.

| layer (plan label) | why it still cannot ship | status after the re-rank |
|---|---|---|
| any **7th** BmAK layer (e.g. a separate blade-whine layer beside the 6 slot beds) | one sample per slot; adding a slot is blocked | **unbuilt** — no writer |
| `POS-mid-fall-a/b` (+ MK2 twins) pitch fall | needs an authored cent-domain pitch curve over rpm | **deferred** (was priority; now below turbine) |
| `low-rise` / `lowmid-rise` pitch bends | same — a static swapped sample cannot bend | **deferred** |
| `REV-bed` / `MK2-Reverse` bed | no reverse engine slot exists; the 13 MK2 reverse one-shots have no home | **unbuilt** |
| `CLUTCH` / `MK2-CLUTCH` | no clutch sample family in the 649 | **unbuilt** |
| `COOLTICKS` / `ROTATION` as a gated layer | media exist (16/22 turbine-led) but there is no tick slot; usable only as a slot-6 alternate | **unbuilt** |
| `DISTANT-REV` | needs `distance_filter` gating proven, which it is not | **unbuilt** |
| `BATTLE-ENGINE` | JC3 has no battle-mode event (AUD-4 deferred with D-2), *and* its bed measures V8-LED | **unbuilt, and not a turbine source** |
| a **turbine top layer over slot 6** | would be a 7th sample | **unbuilt** (the 0F82364C cut above is the workaround) |
| `PERSIST-IDLE` long bed | — (slot 546 `olds_3000rpm_full_intake_lp` exists) | **buildable**, but it is a V8 intake, so it drops in priority under a turbine-led identity |

So the turbine-first order is buildable **inside six slots** and nothing else is. The moment the design
wants turbine *plus* a preserved V8 layer audible at the same rpm, it needs the writer.

---

## 7. What this ranking does not claim

1. **No media → layer edge.** The plan's §0/§8 limit stands: the eleven `POS-*` layers are HIRC objects
   with `REV_RPM` curves, and the media belong to the *event*, not provably to a given layer. "The five
   looped media are the bed" is an event-level statement, not a claim that they are `POS-full-a…e`.
2. **The thresholds in §2 are derived.** T ≥ 0 / P ≥ 10 / peak ≥ 1200 Hz were chosen to separate a line
   from a comb; a listening pass may re-rank within the class (the JSON prints both axes so it can).
3. **Downmix risk.** All five donors are 3-channel. If the whine sits mostly in one channel, a plain
   average will attenuate it; the fill should audition sum-with-gain-compensation against a straight L+R.
4. **A fill changes the whole band, not one layer.** Replacing slot 1 means the car reads turbine at
   idle-high *and* (because the event crossfades those slots upward) at every rpm above it. This is the
   intended effect, but it means there is no "turbine only when fast" variant without a writer.
5. **Loop-tail joins are unheard.** The residual trims and crossfades in §5.3 are arithmetic; whether the
   seams are inaudible is a listening test, not a measurement.

---

## 8. Checks run

| check | result |
|---|---|
| `python Tools/scripts/engine_turbine_rank.py --write` | wrote `Research/BatmobileGrab/ENGINE_TURBINE_SCAN.json`, digest `f61f1286e2f548b6` |
| `python Tools/scripts/engine_turbine_rank.py --check` | **PASS** — 197 rows, all `T_db`/`P_tone_db`/`peak_hz`/`low_share`/`class`/`duration_s` recompute identically from the 423 WAVs in `E:\Modding\_gamedata\BmAKgrab\audio\wav` |
| measured / distinct media | 517 rows / 197 media (561 event×media pairs, 44 with no WAV or no decode) |
| loop points | 6 of 197, quoted verbatim from `AUDIO_FEATURES.json` `loop_lines` (vgmstream `-m`) |
| slot arithmetic | `⌊slot_frames / loop_frames⌋` recomputed for all 6 slots × 18 sustained donors (`fill` block of the JSON) |
| JC3 slot capacities | 94,376 / 98,694 / 98,882 / 111,710 / 113,272 / 119,392 frames, from `JC3_AUDIO_EVENTS.json` as the plan §6.1 quotes them |
| no game, no bank, no ledger touched | only `Research/BatmobileGrab/ENGINE_TURBINE_SCAN.json` and `Tools/scripts/engine_turbine_rank.py` were created; no process launched, no install written |

---

## 9. Change record (per `AGENTS.md`)

1. **Intended change:** add one report that re-ranks the engine layers so turbine takes the first JC3
   slots, plus the measurement script and its JSON so the ranking is reproducible.
2. **Files:** `tmp/freebuff/reports/engine-sound-turbine-priority.md` (this file, the brief's DONE path),
   `Tools/scripts/engine_turbine_rank.py`, `Research/BatmobileGrab/ENGINE_TURBINE_SCAN.json`.
3. **Why these files:** the brief names the report path; every audio measurement in this repo lives as a
   `Tools/scripts/` script with a JSON beside it (`bmak_audio_features.py` → `AUDIO_FEATURES.json`), and
   no report may carry numbers that cannot be recomputed.
4. **Revert:** delete the three files. Nothing else changed — no card, plan, bank, build, manifest,
   module or ledger row was written or edited.

---

## 10. UNKNOWNs, each with its 5-minute experiment

| # | UNKNOWN | 5-minute experiment that settles it |
|---|---|---|
| U-1 | whether the five looped media really are the audible bed (not a component of it) | in `vehicles.bank` copy, mute each of the five in a scratch FSB5 payload and listen in-game at idle; whichever silence kills the bed is the bed |
| U-2 | whether a 2-repeat loop of `0x330DC554` in slot 127 beats a straight 2.360 s cut | build both PCM fills in `Working/Audio` scratch, audition back to back, pick by ear |
| U-3 | whether JC3's own `jc3_veh_ferrari_275_engine_whir_loop` (slot 497) sounds closer to BmAK than the MK2 beds | same audition, four-way: 330DC554 / 1D0717F0 / slot-497 whir / stock Vantage idle |
| U-4 | whether the 3-channel → mono downmix attenuates the whine | compare `mean(L,C,R)` against `L+R` on `0x1D0717F0` (P = 36.39): if P drops > 3 dB, the whine is in one channel |
| U-5 | whether the RTPC property on these five is volume or pitch (decides if the "turbine at all rpm" effect holds) | the plan's U-1: decode the parent HIRC `AkPropID` list; `bmak_audio_features.py` already has the object bodies |
| U-6 | whether slot 6 with `0x0F82364C` reads as a shriek rather than a top-end bed | one audition against the V8 keep, at 4000–6000 rpm |
| U-7 | whether the loop joins click | render the two trims with 50 ms and 200 ms crossfades and null them; a click shows as a broadband spike in the diff |
