# BmAK engine audio vs the JC3 donor - DONE report

STATUS: done. `Research/BatmobileGrab/ENGINE_AUDIO_PAIRS.md` now lists all **18** distinct
events of the `engine` group with every RTPC bind (name, x range, variant count), the donor
event/parameter it would map onto, and a class from the three the brief allows. Result:
**10 `same-role`, 21 `plausible-by-name only`, 77 `no counterpart`** rows; 18/18 events
paired to a donor event (`engine_running_sound`, or `GearChange` for the gear-shift event).
`--check` passes all 12 gates and re-derives the `.md` byte for byte. Read-only.

One correction to the brief's premise: **506 is not the number of RTPC binds in
`AUDIO_FEATURES.json`.** It is that file's own `summary.rtpc_entries` value; the per-event
`rtpc` lists sum to **3328** entries (782 of them in the engine group). Both figures are in
the document and what `summary.rtpc_entries` counts is listed as UNKNOWN - I did not
re-read the generator to define it, and I did not align the two by assumption.

## Files written

| file | what |
|---|---|
| `Research/BatmobileGrab/ENGINE_AUDIO_PAIRS.md` | 335 lines: donor-side facts, the mechanical class rule, one subsection per engine event with its bind table + curves, totals, checks, UNKNOWNs |
| `Tools/scripts/engine_audio_pairs.py` | `--write` / `--check`; derives everything from the two JSONs, asserts the donor event GUIDs/ordinals/tunes and that every stem name exists in a donor bank |
| `tmp/freebuff/reports/engine-sound-mapping.md` | this report |

Earlier briefs of this session remain complete, with their DONE paths present:
`tmp/freebuff/reports/weapon-points-vs-bmak.md`, `v05-combat-rewrite.md`,
`t-rows-no-evidence.md`, `review-tint-impact.md`.

## What was classified, and on what evidence

BmAK side (`AUDIO_FEATURES.json`, group `engine`, 44 rows / 18 names / 130 WEMs / 782 raw
RTPC entries = 106 distinct event x parameter pairs, 5 unresolved parameter hashes).
Donor side (`JC3_AUDIO_EVENTS.json`, cross-checked against `JC3_AUDIO.md`):

* one engine-role event: `engine_running_sound`, GUID `905be2e5-2544-8045-a10b-6034fd27ff11`,
  `vehicles/146`, tune `vehicles/5` (`JC3_AUDIO.md` §3);
* one gear-role event: `GearChange`, GUID `3e448c6d-61c1-5844-867d-06d741b7dd24`,
  `vehicles/66`, tune `vehicles/87`;
* 49 parameter names in the donor `vehicles` bank (93 across all three banks);
* **zero decoded event -> parameter edges** (`JC3_AUDIO.md` §4), so no donor "RTPC bind"
  can be cited for any event;
* `LandAudio.min_rpm` 1000.0 / `max_rpm` 10000.0 - two module members, not a bind.

Class rule (mechanical, stated in the document, no mapping chosen):

* `same-role` - the BmAK parameter name exists **verbatim** in the donor `vehicles` bank and
  the pair's donor event is the engine-role event. Both halves decoded.
* `plausible-by-name only` - the donor event role is only adjacent (`GearChange` vs a
  gear-shift event), or a donor parameter shares the parameter's word stem
  (`REV_RPM`/`rpm`, `EngineHeat`/`heat`, `REV_Throttle`/`throttle`, `BML_Steering_Rotation`/`steer`).
* `no counterpart` - no donor event role for the event's job and no name/stem match,
  including every unresolved `0x...` parameter hash.

Outcome: only `Speed` is a verbatim donor parameter name, so the 10 `same-role` rows are
`Speed` on the 10 engine events that carry it (GearShift_Up is held at
`plausible-by-name only` because its donor event is `GearChange`, not the engine bed).
The 5 hash parameters and BML_WheelSpeed / Startup / Occlusion have no counterpart.

## Commands, verbatim

```text
$ python Tools/scripts/engine_audio_pairs.py --write
wrote Research/BatmobileGrab/ENGINE_AUDIO_PAIRS.md: 18 events, 106 pairs, classes {'no counterpart': 77, 'plausible-by-name only': 21, 'same-role': 10}
```

```text
$ python Tools/scripts/engine_audio_pairs.py --check
  group_is_engine                          PASS
  engine_group_events_18                   PASS
  engine_group_rows_44                     PASS
  summary_rtpc_entries_506                 PASS
  raw_rtpc_entries_3328                    PASS
  donor_engine_event_found                 PASS
  donor_gear_event_found                   PASS
  donor_vehicles_params_49                 PASS
  all_events_have_a_donor_event            PASS
  every_bind_has_a_class                   PASS
  stem_names_exist_in_donor_bank           PASS
  file_matches_rederivation                PASS (28103 bytes of text)
OK: 108 classified rows, 3328 raw entries in the whole file
```

Count checks that fixed the 506 figure:

```text
$ python -c "... sum(len(e['rtpc'] or []) for e in feats['events']) ..."
raw 3328 distinct(event,param) 222 per-package triples 671 distinct curves 471
$ python -c "... feats['summary'] ..."
{"rows": 361, ..., "rtpc_objects": 261, "rtpc_entries": 506, "rtpc_params_distinct": 41, ...}
```

## UNKNOWNs

* **What `summary.rtpc_entries` = 506 counts.** Not the sum of the per-event lists (3328),
  not the whole-file distinct (event, parameter) pairs (222), not the distinct curves (471).
  `AUDIO_FEATURES.json` states no definition; the generator's summary block was not re-read.
  Would be found in: `Tools/scripts/bmak_audio_features.py`.
* **Which donor parameter each donor event reads.** `JC3_AUDIO.md` §4: the `PMLS`
  reference lists exist, the event -> parameter edge is not a field the reader resolves.
  Would be found in: the `PMLS`/`MPGS` bodies.
* **The names behind the 5 unresolved BmAK parameter hashes** (`0x55C2A93B`, `0x7D530EF5`,
  `0xE5E768E2`, `0x7CF1B505`, `0x1DCD6409`). The event rows carry no `name_source`. Would
  be found in: the BmAK RTPC definition table, not in these banks.
* **Whether the donor `Speed` is the same quantity/scale as the BmAK `Speed`** - identical
  name, no decoded edge, no unit or range match proven (donor speed scale not decoded).
* **Whether `LandAudio.min_rpm` / `max_rpm` drive any event** - two module members, no
  binding; the donor events are GUID-pinned and carry no parameter field.

## COMPROMISES

None. Read-only analysis; no install, dropzone, launch or game process (test ban kept).
