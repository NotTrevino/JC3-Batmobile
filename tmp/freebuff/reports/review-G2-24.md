# Independent review — G2-24 · JC3 vehicle audio system

Reviewer: Buffy (did not write this card). Date: 2026-10-28. Read-only review; the only file
written is this report. No game launch, no commit, no archive/dropzone write.

**Scope reviewed:** `GRAB_BACKLOG.md` §0.5 (R1–R14), the G2-24 card (§G2 cards, line 720) and its
§12 row (line 1307); `MODLOG.md` §"G2-24 · JC3 vehicle audio system — done" (line 11610);
`Research/JC3Grab/JC3_AUDIO.md` (237 lines), `Research/JC3Grab/JC3_AUDIO_EVENTS.json` (200,844 B),
`Tools/scripts/jc3audio.py` (917 lines). Source data read through the same readers the card uses
(`jc3index`, `jc3grab`, `jc3detail`, `jc3wiring`, `vgmstream-cli`).

---

## VERDICT

**needs rework**

The card's plumbing is good: every `Out` path exists, `--check` is green and is a real rebuild +
byte-compare, and nearly every number in the doc is script-derived and reproducible (I re-derived
the bank census, the fleet horn census and the sample formats independently and they match).
It fails on one central claim: **the doc's headline negative — "event → tune is not stored" — is
false.** Every one of the 257 tune entries in `vehicles.bank` carries the GUID of the event that
owns it (257/257, one-to-one, at `TLNB` body offset 16), so all 45 donor events' tune indices are
recoverable (e.g. `engine_running_sound` vehicles/146 → tune 5, `horn` vehicles/255 → tune 122).
That makes the doc's §3 "tune UNKNOWN for every row", §5 "no field ties an event to its tune",
§10's "pick by name and audition because event → sample is UNKNOWN" justification, the §12 row's
"five proofs", the MODLOG done section, and T-16 (which cites this card as proof) all overstate
what the files say. The false negative was possible because two of the five "proofs" are **typed
literals in the renderer** (R11), not computed — `--check` cannot see them, and it does not.

Secondary (real but smaller): the card's `Done` clause ("…listed with GUID **and samples**") is not
met for the samples half, the doc's format table names a chunk tag that does not exist (`TLNT`),
`master.banklist` is described as 24 lines and is 26, and several explanatory sentences present
guesses as fact (R4) instead of UNKNOWN.

---

## Check output (verbatim)

Command (project root `E:/Modding/JC3-Batmobile`):

```
python Tools/scripts/jc3audio.py --check
```

stdout, exact:

```
PASS: 45 donor events in 3 banks, 257/257 vehicle events/tunes, 649 samples (22 looped, 1 rate), wave refs 0, LandAudio 2 members, weapons 4, horn 178 / radio 0, md match True
```

exit status: `0` (captured as `EXIT=0`).

stderr (progress only, 649-sample vgmstream census; not part of the verdict line):

```
  vgmstream census 100/649
  vgmstream census 200/649
  vgmstream census 300/649
  vgmstream census 400/649
  vgmstream census 500/649
  vgmstream census 600/649
```

This matches the line pasted into `MODLOG.md:11615-11616` byte for byte.

Out paths (all present):

| path | state |
|---|---|
| `Research/JC3Grab/JC3_AUDIO.md` | 237 lines, 16,797 B, 2026-10-28 03:38 |
| `Research/JC3Grab/JC3_AUDIO_EVENTS.json` | generated, 200,844 B, 03:39, 649 sample rows + 45 donor events |
| `Tools/scripts/jc3audio.py` | 917 lines, `--write` / `--check` / `--fast` / `dump` |
| README section + Files row (not required by the card, claimed in MODLOG) | present, `Research/JC3Grab/README.md:863`, `:947` |

---

## Issues

### 1. Blocking — §5's "event → tune is not stored" is false; the edge is stored in every tune entry

Files/values:

- `Research/JC3Grab/JC3_AUDIO.md:116-117` — "`event body containing a TLNS tune identity GUID` =
  **0 / 257**", "`event body field permuting the 0..256 tune indices` = **none**".
- `JC3_AUDIO.md:120-121` — "The event -> tune edge is not stored either … so *which* tune an event
  plays is UNKNOWN."
- `JC3_AUDIO.md:40` — "no field ties an event to its tune (see §5)".
- `JC3_AUDIO.md:39-40` and the 45 rows at `:44-88` — `tune` and `samples` columns "UNKNOWN for
  every row".
- `Tools/scripts/jc3audio.py:600-604` — both zeros are **string literals** in `render_md`; `build()`
  never compares tune bytes with event bodies, and `donor.events[i]["samples"]` is hard-set to
  `None` (line 333), so the JSON has no `tune` field at all.

What the file actually contains: `TLNS` → `LIST TMLN` → `TLNB`, and `TLNB` body = 16-byte tune GUID
followed by **the 16-byte GUID of the owning event** at body offset 16 (chunk offset 36). Measured
with the card's own parsers:

```
tunes containing an event GUID: 257 of 257   (all at byte offset 36 of the LIST TMLN chunk)
distinct events referenced: 257   tunes: 257   (1:1 bijection)
e.g. tune 0  -> event ordinal 15   (100cbd8f-9b9f-8749-b853-632b33d167e9, vehicles/15)
     tune 5  -> event ordinal 146  (905be2e5-2544-8045-a10b-6034fd27ff11, engine_running_sound)
     tune 87 -> event ordinal 66   (3e448c6d-61c1-5844-867d-06d741b7dd24, GearChange)
     tune 122-> event ordinal 255  (fd69c63c-84e6-fa43-b067-7eae99a59ce1, horn)
```

All 45 donor GUIDs resolve to a tune index in their bank (vehicles 24, character 2, effects 19), so
the `tune` column in §3 could have been filled for **45 of 45** rows, and the `Done` clause's
"GUID and samples" chain is one hop closer than the doc claims. The card's `Do` step 1
(`GRAB_BACKLOG.md:723`) asks exactly for "GUID → event path → parameters → samples"; the report
answers "event path = the `.epe` role" but skips the tune hop it could have measured.

Why it matters beyond wording: the doc's actionable conclusion (§10, §11) is "swap by name and
audition because event → sample is UNKNOWN". The first hop is *not* unknown; only tune → wave is.
The false negative is already propagated: `GRAB_BACKLOG.md:1307` ("event→tune→sample UNKNOWN with
five proofs"), `MODLOG.md:11640-11645` (proofs b and c), and T-16 (`MODLOG.md:12191`, "G2-24 §5 proved
event → tune → sample is not stored"). Note the event body *does* carry several other GUID fields (its own GUID at
offset 0, plus three more at 32/48/64 in `EVTB`), so "no tune GUID in the event body" is true but
irrelevant: the edge is authored on the tune side.

### 2. Blocking — two of the five "proofs" are typed values, not derived (R11)

- `jc3audio.py:600` — the `0` in "**0 / 257**" is literal text; the `257` alone comes from
  `banks['vehicles']['events']`.
- `jc3audio.py:602` — "permuting the 0..N tune indices | **none**" is literal text, with `N` filled
  in; no code searches for such a field.
- `jc3audio.py:604` — "event name / path string in the bank | **none**" is literal text; the EVTS
  string census the MODLOG quotes (1,654) is not in the script either.

`--check` re-renders the same literals, so a wrong typed claim passes `--check` by construction.
R11 says counts in a new doc come from a script with `--check`; these are the doc's *central* counts
and they do not. (For contrast, the one §5 row that *is* computed — `wave_guid_refs_outside_wavs` —
is real, and I re-derived it: 0 of 649 wave GUIDs appear in tunes or sound-instance bodies.)

### 3. The card's `Done` criterion is only half machine-verified, and half unmet as written

Card (`GRAB_BACKLOG.md:729-730`): "every donor event and every chosen weapon's events listed with
GUID **and samples**; route recommendation with evidence." The doc lists all 45 GUIDs + bank +
ordinal, but **samples are `UNKNOWN` for every row** and no sample index/name is listed for any of
`w602`/`w603`/`w618`/`w619` (the `samples` column does not exist in §7 at all). `--check` asserts
the 45/45 count, the bank names, `named == 23`, FEV 56/50, 257/257, 649/649, `wave refs 0`,
`LandAudio` 1000.0/10000.0, horn 178, radio 0, w618/w619 "fire GUID is first `.fmod_guids` entry" —
but nothing about samples and nothing about the tune hop. The absence is argued rather than
measured, and the argument (issue 1) is wrong for the first hop.

Minor: `jc3audio.py:778-779` (`if e["banks"] and e["samples"] is not None`) is dead code — `build()`
always writes `samples: None` (line 333) — so it cannot protect the §3 "UNKNOWN" column.

### 4. Format table names a chunk that does not exist

`JC3_AUDIO.md:16` — "| tunes | `TLNS` -> `TLNT`, one per event |". `TLNT` occurs **0** times in
`vehicles.bank`; the actual chain is `TLNS` → `LIST TMLN` (257) → `TLNB` (257). Same literal at
`jc3audio.py:524` (the function docstring at `:153` is correct, the rendered table is not). Also
`JC3_AUDIO.md:17` "`WAIS` -> `WAIT`/`WAIB`" — actual `WAIT` → `LIST INST` → `WAIB`.

### 5. `master.banklist` size is wrong

`JC3_AUDIO.md:216` and `jc3audio.py:471` — "master.banklist is a plain 24-line text list". The
shipped file is 434 B with **26** bank names (`master`, `master_strings`, `vehicles`, …,
`custom_mixes`). Typed, not read by the script, and the number is part of route-b's evidence.

### 6. Speculation presented as fact (R4) in three places

- `JC3_AUDIO.md:90-92` — "The 45 GUIDs are the entity's preload list; … the other 22 are pinned but
  **not referenced by any object in this entity - they are the vehicle bank's shared set** (door,
  break, water and suspension variants the graph reaches through the parts and effect tables)."
  (a) What was measured is narrower: 22 GUIDs appear in no `Sound` field of the decoded `.epe`
  (I confirmed 29 `Sound` objects, 23 distinct values, 23 of the 45 GUIDs matched, and `Sound` is
  the *only* 16-byte-GUID-valued property key on those 450 objects). (b) The sentence contradicts
  itself — "not referenced by any object" vs "the graph reaches through the parts and effect
  tables" — and the "shared set" explanation is a guess. This should be UNKNOWN.
  (c) "preload list" is an assumption about what `.ee.fmod_guids` means; the file itself only shows
  `version 1`, three bank names, 45 GUIDs, 0 trailing bytes.
- `JC3_AUDIO.md:102-104` — "`LandAudio` is the whole vehicle-side audio parameter set … the RPM
  window the engine event is driven over". Only the two members and their values are measured; that
  they window *the engine event* is an inference, and the doc's own next paragraph
  (`:106-108`) says which event reads which parameter is UNKNOWN.
- `JC3_AUDIO.md:196-197` — "no `radio` objects in all 232 decoded graphs … JC3's radio is the music
  system, not a vehicle effect". The first clause is measured (I recount it: 0 of 232); the second
  is an unsourced claim about the whole game. Should read "no radio member on any of the 232
  decoded vehicles; where the radio lives is UNKNOWN".

### 7. Carrier names in §9 that are not in the donor

`JC3_AUDIO.md:204` (AUD-2) cites `exhaust_upgrade_nitrous2`; `:208` (AUD-6) cites
`combined_wheel_default_sfx`. Neither is among the donor's 45 events (§3); both names exist on other
fleet vehicles (e.g. `v0008_car_autostraad_modernsportssaloon…`, `v0000_car_autostraad_oldjeep…` in
`E:/Modding/_JC3grab/detail`). So they are real names, but the table's "JC3 carrier" column mixes
donor carriers with fleet members without saying which — provenance is missing for a decision table.

### 8. MODLOG done-section numbers that disagree with a fresh measure

- `MODLOG.md:11668` — "969 `PRMS` parameters (**19** distinct names)". The doc (`JC3_AUDIO.md:105`)
  and the JSON say **49**, and 49 is what the bank parses (`(event angle)`, `Distance`,
  `Event Cone Angle`, `Intensity`, `PlayerIsDriving`, `Speed`, `rpm_norm`, …). The MODLOG figure is
  wrong; the doc is right.
- `MODLOG.md:11632` and `JC3_AUDIO.md:22` contradict each other on the same fact: MODLOG says EVTS
  "holds 1,654 printable strings", the doc says "`EVTS` carries **no** printable string". Measured:
  2,333 printable runs ≥3 chars / 1,654 runs ≥4 chars in the 66,568-byte EVTS section — the 1,654 is
  reproducible only with an unstated ≥4-char rule, and the doc's sentence is literally false (the
  section carries `LIST`/`EVNT`/`PROPS`/`PROP` tags). The substantive claim (no *event name* among
  them) holds. Wording + method should be fixed rather than the conclusion.

### 9. Robustness (not a factual error today)

The 649-sample census runs on the repo copy
`Working/Audio/jc3bank/sound/fmod_banks/vehicles.bank` (`jc3audio.py:422-424`), not on the archive
entry the rest of the report is built from. I checked the copy: byte-identical to the game entry
(`sound/fmod_banks/vehicles.bank`, 210,781,376 B, sha256 prefix `6161104d8909b7b0`), so every sample
number is valid. But `--check` would silently pass on a stale or patched copy (and `Working/Audio/`
is exactly where test-060's swapped bank and `_apply_audio.py` live), so the check should read the
archive entry or assert the two are equal.

---

## Spot-checks

| # | value in the doc | how verified | result |
|---|---|---|---|
| 1 | `JC3_AUDIO.md:154` sample 10 `jc3_vehicle_horn_truck_06_loop`, 48000 Hz, 1 ch, 50,140 frames, loop 17,341..50,137 | `vgmstream-cli -s 10 -m Working/Audio/jc3bank/sound/fmod_banks/vehicles.bank` → "sample rate: 48000 Hz / channels: 1 / loop start: 17341 / loop end: 50137 / stream total samples: 50140 / 16-bit Little Endian PCM / stream count: 649 / stream name: jc3_vehicle_horn_truck_06_loop"; identical in `JC3_AUDIO_EVENTS.json` `samples.list[9]` | **match** |
| 2 | `JC3_AUDIO.md:55` (row 12) `100cbd8f-9b9f-8749-b853-632b33d167e9` at `vehicles/15`; row 1 `249a34b0…` at vehicles/43; row 3 `fd69c63c…` vehicles/255; row 19 `905be2e5…` vehicles/146 | parsed `EVTS`→`LIST EVNT`→`EVTB` ordinals directly with the script's `fev`/`section_entries`: ordinal 15 = `100cbd8f…`, 43 = `249a34b0…`, 255 = `fd69c63c…`, 146 = `905be2e5…` | **match** (4/4) |
| 3 | `JC3_AUDIO.md:189-191` horn **178** objects in 178 vehicles, 19 GUIDs; radio **0**; 6,659 `Sound` objects / 232 | independent recount over all 232 `E:/Modding/_JC3grab/detail/*.ee.json` (own code, not `jc3audio.py`): entities 232, `Sound` objects 6,659, horn 178 in 178 entities, radio 0; JSON `horn_guids` = 19 | **match** |
| 4 | `JC3_AUDIO.md:30-34` bank table: vehicles 210,781,376 / 257 / 1,674 / 649 / 969; character 90,442,272 / 193 / 976 / 262; effects 391,390,496 / 579 / 1,524 / 417 | re-parsed all three banks from the archives (`jc3grab.read_entry` + `fev`/`fev_events`/`fev_params`/`fev_waves`/`fev_sounds`/`fsb`): vehicles 56/50, 257 events, 257 tunes, 1,674 instances, 649 waves, 969 params, 649 samples; character 193/193/1,938/976/262/976; effects 579/579/5,310/1,524/417/1,524 | **match** |
| 5 | `JC3_AUDIO.md:132-135` FSB5 header 22,100 B header, 23,792 B name table (21,196 B of names), 153,439,744 B data | `fsb()` on the archive entry: `{samples: 649, sample_header_bytes: 22100, name_table_bytes: 23792, name_table_string_bytes: 21196, data_bytes: 153439744}` | **match** |

Re-derivation that **contradicts** a doc claim (issue 1), done twice with different slicing:

```
TLNS entries: 257   chunk[36:52] is a bank event GUID: 257/257   distinct: 257 (bijection)
all 45 donor GUIDs -> tune index: 45/45 resolved
```

---

## What would make this card `sound`

1. Parse `TLNB` body offset 16 as the owning event GUID, put the tune index in the §3 `tune` column
   for all 45 rows, and add `invariants()` for it (e.g. `tunes_with_event_guid == 257`,
   `donor tunes resolved == 45`).
2. Replace the §5 literal rows with computed probes, and restate the conclusion as "tune → wave is
   not stored (0/649)"; keep the "swap by name and audition" advice but grounded on the remaining
   hop only. Correct `GRAB_BACKLOG.md:1307`, the MODLOG done section and T-16's citation.
3. State the sample half of the card's `Done` as a justified UNKNOWN in the doc (or derive sample
   names per tune), rather than only `--check`-invisible prose.
4. Fix `TLNT`→`TLNB`, 24→26 lines, the MODLOG's 19→49, the EVTS "no printable string" wording, and
   demote the three R4 guesses (§3 exploded-set sentence, §4 LandAudio role, §8 radio sentence) to
   UNKNOWN.
