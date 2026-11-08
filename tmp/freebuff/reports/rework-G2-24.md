# G2-24 rework — JC3 vehicle audio system

Date: 2026-10-29. Card: `GRAB_BACKLOG.md:720` (`G2-24 · JC3 vehicle audio system`), tracker row
`GRAB_BACKLOG.md:1307`. Review: `tmp/freebuff/reports/review-G2-24.md`.

## STATUS: DONE — all 9 issues confirmed and fixed in the generator; `--check` green

No game launched, nothing written to `D:/Games`, no shared game module touched, no commit/push.

One follow-up is **not** fixed here because it belongs to another finished card: the T-16 output
(`Working/Translation/T12_AUDIO.md:27,268-269`) still says "G2-24 §5 proved the bank stores no
event→tune→sample edge". That sentence is now false in its first hop. It needs a T-16 rework pass
(its generator `t12_audio.py`), and it is flagged in the MODLOG. The MODLOG's own historical entries
are append-only (R14), so the two wrong numbers there are corrected in the appended done entry, not
edited in place.

---

## Per issue

### 1. "event → tune is not stored" — CONFIRMED (and the review understates it)

Measured with the card's own readers (`jc3index.load_index`, `jc3audio.read_entry/fev/section_entries`):

```
tunes with an event GUID: 257 of 257
distinct event guids: 257 distinct tune guids: 257
max multiplicity: 1
event bodies containing their tune GUID: 257 offsets [32]
```

`TLNB` body = 16-byte tune GUID at offset 0, **owning event GUID at offset 16** (chunk offset 36).
The same tune GUID is also in the event body at **offset 32**, so the old doc line "event body
containing a TLNS tune identity GUID = 0 / 257" was false, not merely irrelevant — the review's
"no tune GUID in the event body is true but irrelevant" is wrong on the fact and right on the
conclusion. Character bank 193/193 and effects bank 579/579 are the same 1:1 shape; donor
resolution is 24 vehicles + 2 character + 19 effects = **45/45**.

Fix: `fev_tunes()` now returns `{index, tune_guid, event_guid, bytes}` from `TLNB`; every bank keeps
`tunes_with_event_guid` and `tune_event_bijection`; each donor event carries
`tune: {bank, index, tune_guid}`; the §3 `tune` column is filled for all 45 rows; §5's first rows are
computed and asserted in `invariants()`.

### 2. Two of the "five proofs" were typed literals — CONFIRMED

Old renderer printed `0 / 257`, `none`, `none` as text; `build()` never compared tune/event bytes.
Now `build()` computes `tunes_with_event_guid`, `event_bodies_carrying_tune_guid`,
`wave_guids_in_tunes`, `wave_guids_in_instances`, `tlnt_tag_count`, `evts_printable_runs`,
`evts_role_name_hits`; `invariants()` fails if any moves. `--check` re-renders from those fields.

### 3. Done clause's sample half unmet / unverified — CONFIRMED

Samples stay UNKNOWN, now on a measured ground rather than an argument: 0 of the 649 `WAVS` GUIDs
occur in any tune chunk (`0/649`) or any `WAIT` instance body (`0/649`), and `TLNT` occurs 0 times.
The doc's §3, §5, §7 and §11 now state the sample half as a justified UNKNOWN (R4), and the dead
`if e["banks"] and e["samples"] is not None` check is replaced by "in a bank but no tune".

### 4. Format table named a chunk that does not exist — CONFIRMED

```
TLNT count in bank: 0
first TMLN entry children [(b'TLNB', ..., 164), (b'LIST', ..., 136), (b'CTRO', ..., 2)]
```

Doc now: `TLNS` → `LIST TMLN` → `TLNB` (tune GUID + event GUID); `WAIS` → `WAIT` → `LIST INST` →
`WAIB`. `tlnt_tag_count` is an invariant, so the old name cannot come back silently.

### 5. `master.banklist` size — CONFIRMED

```
banklist bytes 434 lines 26 names 26 [... 'custom_mixes.bank']
```

The script now reads the file (`banklist.lines/bytes/names`), route b quotes the measured 26 lines /
434 B, and `invariants()` asserts both.

### 6. Three R4 guesses — CONFIRMED

- `.ee.fmod_guids` is no longer called a "preload list"; the doc prints what the file shows
  (`version 1`, 3 bank names, 45 GUIDs, 0 trailing bytes) and says the block's semantics are UNKNOWN.
  Measured: 29 `Sound` objects, 23 distinct GUIDs, 23 of the 45 named; the other 22 are named nowhere
  in the decoded `.epe`, and why they are pinned is UNKNOWN.
- `LandAudio` is no longer "the RPM window the engine event is driven over": only the 2 members and
  their values are claimed, the event-to-parameter edge is UNKNOWN.
- "JC3's radio is the music system" is replaced by "no radio member on any of the 232 decoded
  vehicles; where the radio lives is UNKNOWN".

### 7. Carrier provenance — CONFIRMED, with one correction to the review

Measured over the 232 decoded graphs (name or any string value, so effect-table names count):

```
exhaust_upgrade_nitrous        donor event
exhaust_upgrade_nitrous2       donor graph object, not a pinned event (19 decoded vehicles)
exhaust_upgrade_tjump*         donor event (exhaust_upgrade_tjump / _trail are among the 45)
wheel_suspension_*             donor graph object, not a pinned event (132 vehicles)
ground_roughness_sound_attached  donor event
combined_wheel_default_sfx     donor graph object, not a pinned event (126 vehicles)
```

So the review's "neither is among the donor's 45 events" is right, but "both names exist on other
fleet vehicles" is incomplete: both are in the **donor's own `.epe`** as `SAttachedEffectTable` /
materials objects, they are simply not bound to a pinned GUID. The §9 table now prints that measured
provenance per name (donor event / donor graph object / fleet member).

### 8. MODLOG numbers vs fresh measure — CONFIRMED

```
params 969 distinct 49
EVTS bytes 66560 printable runs >=3: 2333 >=4: 1654
```

The "19 distinct names" in the old done entry is wrong (49); "1,654 printable strings" is the
>=4-char rule and the old doc sentence "EVTS carries no printable string" was literally false (it
carries `LIST`/`EVTS`/`EVTB`/`PRPS`/`PROP`). The doc now says: 2,333 runs >=3 (1,654 >=4), all chunk
tags or binary noise, and **0 of the 29 donor role names** occurs in the section. The old MODLOG
entries stay as written (append-only); the appended done entry records both corrections.

### 9. Census ran on a mutable copy — CONFIRMED

`Working/Audio/jc3bank/sound/fmod_banks/vehicles.bank` vs the archive entry:

```
archive sha 6161104d8909b7b0 working 6161104d8909b7b0 equal True sizes 210781376 210781376
```

`build()` now hashes both (chunked) and raises `SystemExit` before vgmstream runs if they differ; the
sha pair goes into the JSON and `invariants()` re-asserts `matches`.

---

## Files changed

| path | change |
|---|---|
| `Tools/scripts/jc3audio.py` | the fixes above: `TLNB` tune/event parse, computed §5 probes, `fev_event_bodies`, banklist read, carrier provenance, bank-copy sha256 guard, new invariants, new PASS line |
| `Research/JC3Grab/JC3_AUDIO.md` | regenerated by `--write` (251 lines) |
| `Research/JC3Grab/JC3_AUDIO_EVENTS.json` | regenerated by `--write` (208,953 B; per-event `tune`, `banklist`, `bank_copy`, probe fields) |
| `GRAB_BACKLOG.md:1307` | only the G2-24 §12 row, evidence summary rewritten |
| `Research/JC3Grab/README.md` | one registration phrase ("five probes" → "event → tune stored on both sides, tune → wave not stored") |
| `MODLOG.md` | appended "G2-24 rework — intended change" and "G2-24 rework — done" |

No output file was hand-edited: the two `JC3_AUDIO*` files come from `--write`, and `--check`
rebuilds them byte for byte.

## `--check` output (verbatim, exit 0)

Command: `python Tools/scripts/jc3audio.py --check`

```
PASS: 45 donor events in 3 banks, 257/257 vehicle events/tunes, 45/45 donor tunes, 257/257 tunes with an event GUID, 0/0 wave GUIDs in tunes/instances, 649 samples (22 looped, 1 rate), wave refs 0, LandAudio 2 members, weapons 4, horn 178 / radio 0, md match True
```

`stderr`: the six `vgmstream census 100/649 … 600/649` progress lines (~31 s).

`python Tools/scripts/status_audit.py --check` → `STATUS.md is current` (exit 0).
`t_rows.py check` was not run: no translation row changed.

## Tamper tests

| tamper | result |
|---|---|
| `Research/JC3Grab/JC3_AUDIO_EVENTS.json`: `donor.events[0].tune.index` 230 → 0 | `FAIL: JC3_AUDIO_EVENTS.json stale`, exit 1 |
| `Research/JC3Grab/JC3_AUDIO.md`: `**257 / 257**` → `**256 / 257**` | md diff printed (both tune rows), exit 1 |

Both tampered files were restored from byte-identical copies (`cmp` clean) and `--check` was green
again afterwards.

## Limits of this pass

- The `tune → wave` edge is still UNKNOWN; nothing here claims otherwise.
- The weapon banks (`weapons.bank`, `weapons_preorder.bank`) were not probed for the same edge, so
  their samples are UNKNOWN by analogy with the vehicle bank, as the doc says.
- T-16's `T12_AUDIO.md` still repeats the old "no event→tune edge" claim and needs its own rework.
