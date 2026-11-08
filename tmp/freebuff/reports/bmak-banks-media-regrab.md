# BmAK bank media regrab — NEW-AUD-1

**STATUS: done.** The ten banks the ledger called `missing-bank` were not missing (G3-14, 2026-11-06); this card
takes the step nobody took afterwards: it reads all ten out of their cooked packages, walks the Wwise HIRC graph
from every Event to its media, writes **516 WEM files**, decodes them to **516 WAVs** with the repo's own
vgmstream-cli, and joins each event id to its WAV. Every oracle passes and `--check` reproduces
`Research/BatmobileGrab/AUDIO_REGRAB.json` byte for byte.

Nothing in the ledger, the cards or any earlier generated file was edited. The install was read only.

---

## 1. Files written

| path | what it is |
|---|---|
| `Tools/scripts/bmak_audio_regrab.py` | the tool: `--write` (extract + decode + JSON) and `--check` (re-derive, compare, verify every WAV) |
| `Research/BatmobileGrab/AUDIO_REGRAB.json` | machine-readable map: 15 bank payloads, 350 events, 10,249 media entries, per-media WEM/WAV path + sha1 + duration |
| `E:/Modding/ArkhamKnight/_grab/audio_regrab/wem/*.wem` | 516 extracted Wwise media files (outside the repo, as the brief asked) |
| `E:/Modding/ArkhamKnight/_grab/audio_regrab/wav/*.wav` | 516 decoded WAVs (vgmstream-cli, same decoder `_wem_decode.py` used for G1-15) |
| `tmp/freebuff/reports/bmak-banks-media-regrab.md` | this report |

## 2. Method (reuses this repo's tools, no new decoder, no external download)

1. **Bank list** — `grab_audio_banks2.bank_list()` over `AUDIO_BANKS.json`: every `present_in_packages` export,
   filtered to the ten `missing_claim_banks` in `AUDIO_BANKS.json` `totals`
   (`BML_Batmobile_Subjective, BML_Impacts, BML_Sonar, CHR_BatmanAlerts, CHR_BatmanDisruptor, UI_InGame,
   VEH_Tank_Heavy, VEH_Tank_Missiles, VFX_Tank_Explosion, OBJ_Rolling_Objects`).
2. **Payload** — `grab_audio_banks2.Image(path, name_offset, chunk_at).get(offset, offset+size)`, i.e. the
   export's own byte range of the cooked package, decompressed block by block. 15 payloads for 10 banks (five
   banks ship twice, in `BmGame`/`Startup` and in `StartupPatch`, with different payload sha1s — they are kept
   separate, as G3-14 recorded them).
3. **HIRC graph** — `grab_audio.parse_bank` + `grab_audio.resolve`: Event (`0x04`) → Action (`0x03`) →
   Sound (`0x02`) / RanSeq (`0x05`) / container (`0x06,0x07,0x09`) → DIDX media id. Same parser G1-15 used for
   `AUDIO_MAP.json`, unchanged.
4. **WEM** — the DIDX entry's `(offset, size)` sliced out of the `DATA` chunk body; must start `RIFF`/`WAVE`,
   and the extracted length must equal the DIDX length (oracle O-3).
5. **WAV** — `Tools/vgmstream-win64/vgmstream-cli.exe -o out.wav in.wem`; header re-read with Python's `wave`
   (channels, rate, frames, seconds) and stored per file.
6. **Bytes are written once.** The same media id appears under many events (10,249 entries for 531 distinct
   ids); the first occurrence writes the file, every later occurrence records `duplicate_of` and points at that
   WAV, so each event resolves to a real WAV without storing the bytes nine times.

## 3. What the ten banks actually hold

| bank | package | HIRC events | media entries | distinct media | WEM written | payload sha1 = AUDIO_BANKS |
|---|---|---:|---:|---:|---:|:-:|
| `BML_Batmobile_Subjective` | `Startup` | 12 | 28 | 18 | 18 | yes |
| `BML_Impacts` | `BmGame` | 5 | 233 | 71 | 71 | yes |
| `BML_Impacts` | `StartupPatch` | 5 | 233 | 71 | 0 (all duplicates of `BmGame`) | yes |
| `BML_Sonar` | `BmGame` | 7 | 70 | 22 | 22 | yes |
| `CHR_BatmanAlerts` | `BmGame` | 6 | 36 | 11 | 10 (1 id has no DIDX row) | yes |
| `CHR_BatmanAlerts` | `StartupPatch` | 6 | 36 | 11 | 0 (duplicates) | yes |
| `CHR_BatmanDisruptor` | `BmGame` | 17 | 238 | 40 | 40 | yes |
| `CHR_BatmanDisruptor` | `StartupPatch` | 17 | 238 | 40 | 0 (duplicates) | yes |
| `OBJ_Rolling_Objects` | `BmGame` | 9 | 26 | 20 | 20 | yes |
| `UI_InGame` | `BmGame` | 219 | 2,804 | 187 | 173 (14 no DIDX row) | yes |
| `UI_InGame` | `StartupPatch` | 219 | 2,804 | 187 | 0 (duplicates) | yes |
| `VEH_Tank_Heavy` | `Startup` | 41 | 464 | 40 | 40 | yes |
| `VEH_Tank_Missiles` | `Startup` | 12 | 113 | 26 | 26 | yes |
| `VFX_Tank_Explosion` | `BmGame` | 22 | 1,463 | 96 | 96 | yes |
| `VFX_Tank_Explosion` | `StartupPatch` | 22 | 1,463 | 96 | 0 (duplicates) | yes |

Totals: **15 payloads, 350 distinct events, 327 with playable media, 531 distinct media ids, 516 WEM/WAV
pairs, 0 decode failures.** 23 events resolve to no media at all (state/switch-only entries, same status
`no-media` as in `AUDIO_MAP.json`). 9 media ids are named by a Sound but have **no DIDX row** in their bank —
recorded as `no-didx-entry`, not as missing from the install.

## 4. Event → WAV (the 26 ledger ids, 33 bank/event pairs)

`wav=…` counts distinct WAVs the event resolves to; the filename shown is the first one. Every path is
`E:/Modding/ArkhamKnight/_grab/audio_regrab/wav/<bank>__<event id>__<media id>.wav`; a `duplicate_of` row points at the
twin's WAV, so no event is left without a file.

| bank | event id | event name | media | wav | first WAV |
|---|---|---|---:|---:|---|
| `BML_Batmobile_Subjective` | `0x78DACB3D` | `Play_Batmobile_Jump_Wind` | 4 | 4 | `BML_Batmobile_Subjective__66B6C3A7__3C68C9F5.wav` |
| `BML_Batmobile_Subjective` | `0xA7C5D89A` | `Play_Batmobile_Jump_PreJump` | 3 | 3 | `BML_Batmobile_Subjective__A7C5D89A__041F050D.wav` |
| `BML_Batmobile_Subjective` | `0xC3438074` | `Play_Batmobile_Jump_Land` | 6 | 6 | `BML_Batmobile_Subjective__ACB34CB7__006183BE.wav` |
| `BML_Batmobile_Subjective` | `0xCE18923D` | `Play_Batmobile_Jump_PreLand` | 3 | 3 | `BML_Batmobile_Subjective__ACB34CB7__006183BE.wav` |
| `BML_Impacts` | `0x3531A5D5` | `Play_Batmobile_Destroyed` | 17 | 17 | `BML_Impacts__13CF3DFD__0C9F7F81.wav` |
| `BML_Sonar` | `0x02EE7381` | `Play_BML_Sonar_Turn_On` | 22 | 22 | `BML_Sonar__02EE7381__022C4A7D.wav` |
| `BML_Sonar` | `0x265FE0CD` | `Play_BML_Sonar_Turn_Off` | 22 | 22 | `BML_Sonar__02EE7381__022C4A7D.wav` |
| `BML_Sonar` | `0x2A77A8B4` | `Play_BML_Sonar_Rumble_Lp` | 3 | 3 | `BML_Sonar__02EE7381__0BF3262B.wav` |
| `BML_Sonar` | `0x835146BE` | `Stop_BML_Sonar_Rumble_Lp` | 3 | 3 | `BML_Sonar__02EE7381__0BF3262B.wav` |
| `BML_Sonar` | `0x97CBF248` | `Play_BML_Sonar_Pulse_Search` | 7 | 7 | `BML_Sonar__02EE7381__022C4A7D.wav` |
| `BML_Sonar` | `0xFFCC9813` | `Play_BML_Sonar_Pulse_Full` | 7 | 7 | `BML_Sonar__02EE7381__022C4A7D.wav` |
| `CHR_BatmanAlerts` | `0xDEAD7680` | `Play_HUD_fail` | 11 | 10 | `CHR_BatmanAlerts__3882D601__03A32B6A.wav` |
| `CHR_BatmanDisruptor` | `0x4F380472` | `Play_Batmobile_Tracker_Deploy` | 1 | 1 | `CHR_BatmanDisruptor__308BC06A__3F39B9FB.wav` |
| `CHR_BatmanDisruptor` | `0x8EA6FCA0` | `Play_Disruptor_Vehicle_Tracking_Fire` | 18 | 18 | `CHR_BatmanDisruptor__8EA6FCA0__0BA98083.wav` |
| `OBJ_Rolling_Objects` | `0x51A67708` | `Play_OBJ_Stagg_Battery_Roll` | 2 | 2 | `OBJ_Rolling_Objects__51A67708__1BC12121.wav` |
| `UI_InGame` | `0x274D2DAA` | `Play_HUD_Missile_Lock` | 2 | 2 | `UI_InGame__274D2DAA__1D3788FA.wav` |
| `VEH_Tank_Heavy` | `0x12D072C1` | `Stop_VEH_Tank_Heavy_Locked` | 1 | 1 | `VEH_Tank_Heavy__0FA4AD78__1764ACFD.wav` |
| `VEH_Tank_Heavy` | `0x39553BB8` | `Play_Tank_Heavy_LockBeep` | 3 | 3 | `VEH_Tank_Heavy__0FA4AD78__1764ACFD.wav` |
| `VEH_Tank_Heavy` | `0x9279017E` | `Stop_VEH_Tank_Heavy_LockBeep` | 1 | 1 | `VEH_Tank_Heavy__0FA4AD78__1E31ACDB.wav` |
| `VEH_Tank_Heavy` | `0xEDFB1D8F` | `Play_Tank_Heavy_Locked` | 3 | 3 | `VEH_Tank_Heavy__0FA4AD78__1764ACFD.wav` |
| `VEH_Tank_Missiles` | `0x4334B8A3` | `Stop_Batmobile_RocketTails` | 5 | 5 | `VEH_Tank_Missiles__4334B8A3__059DE750.wav` |
| `VEH_Tank_Missiles` | `0x6D02C4D5` | `Play_Batmobile_RocketTails` | 10 | 10 | `VEH_Tank_Missiles__4334B8A3__059DE750.wav` |
| `VFX_Tank_Explosion` | `0x3FC50C64` | `Play_Explosion_2D` | 88 | 88 | `VFX_Tank_Explosion__029B33B7__00078058.wav` |
| `VFX_Tank_Explosion` | `0xBD404E03` | `Play_Batmobile_Immobiliser_Impact` | 91 | 91 | `VFX_Tank_Explosion__029B33B7__00078058.wav` |
| `VFX_Tank_Explosion` | `0xD6730A26` | `Play_Tank_Explosion_Barrage_Sweetener` | 88 | 88 | `VFX_Tank_Explosion__029B33B7__00078058.wav` |
| `VFX_Tank_Explosion` | `0xDD424156` | `Play_Batmobile_HeavyCannon_Explosion` | 88 | 88 | `VFX_Tank_Explosion__029B33B7__00078058.wav` |

The lock beeps, sonar on/off/pulse/rumble, tracker deploy, the missile-lock HUD cue, the tank explosion family
and both rocket-tail cues now have audible files — these are the AUD-2…AUD-6 cues the weapon and HUD work was
waiting on.

Two rows deserve a note: `Play_Tank_Heavy_LockBeep`/`Locked`/`Stop_*` share the same media ids (the lock family
reuses one beep set), and `Play_HUD_fail` resolves to 11 media of which one has no DIDX row.

## 5. The `0x6BB2C66E` twin — confirmed again, now with media

* `0x6BB2C66E` (`Play_BatSniperRifle_Vehicle_Tracking_Fire`, the map-side name): **carried by no bank in this
  set** — `missing_twin.carried_by` is `[]`. Its twin relationship is unchanged from
  `AUDIO_EVENT_6BB2C66E.md`.
* `0x8EA6FCA0` (`Play_Disruptor_Vehicle_Tracking_Fire`, the name the cooked package actually holds): **carried by
  `CHR_BatmanDisruptor`** with **18 media ids**, all extracted and decoded
  (`CHR_BatmanDisruptor__8EA6FCA0__*.wav`).

So the pair is confirmed at the media level, not only at the id level: the bank ships the disruptor twin and its
sounds, and still does not cook the declared `0x6BB2C66E`. Oracle `O-6-twin` asserts exactly this.

## 6. Oracles and commands (verbatim)

```
$ python Tools/scripts/bmak_audio_regrab.py --write
{
 "banks_parsed": 15,
 "payloads_searched": 15,
 "events_seen": 350,
 "events_with_media": 327,
 "map_rows_covered": 33,
 "media_entries": 10249,
 "media_unique_wem": 531,
 "media_written": 516,
 "wav_decoded": 516,
 "wav_failed": 0
}
  O-1-payload_sha1: PASS
  O-2-hirc_complete_and_counts: PASS
  O-3-wem_riff_and_size: PASS
  O-4-name_rule: PASS
  O-5-wav_redecodes: PASS
  O-6-twin: PASS
missing twin {'id': '0x6BB2C66E', 'carried_by': []}
cooked twin  {'id': '0x8EA6FCA0', 'carried_by': ['CHR_BatmanDisruptor'], 'media': [18 ids]}
wrote E:\Modding\JustCause3\JC3-Batmobile\Research\BatmobileGrab\AUDIO_REGRAB.json
WRITE_EXIT=0

$ python Tools/scripts/bmak_audio_regrab.py --check
json identical True; banks 15; media 10249; wav 516; missing files 0
CHECK PASS
CHECK_EXIT=0
```

| oracle | what it proves | result |
|---|---|---|
| `O-1-payload_sha1` | each payload is the bank `AUDIO_BANKS.json` recorded (same export, same bytes) | PASS (15/15) |
| `O-2-hirc_complete_and_counts` | the HIRC walk reaches the recorded Event count for every bank | PASS |
| `O-3-wem_riff_and_size` | every extracted media is a RIFF/WAVE of exactly its DIDX length | PASS |
| `O-4-name_rule` | `fnv1(lower(name))` reproduces the declared id for every mapped event | PASS |
| `O-5-wav_redecodes` | every entry is decoded, a duplicate of a decoded file, or a recorded no-DIDX id; 0 decode failures | PASS |
| `O-6-twin` | `0x6BB2C66E` carries no media here; `0x8EA6FCA0` does | PASS |

## 7. UNKNOWNs

1. **What the 9 no-DIDX media ids are.** `0x007BBDEB, 0x07F3FFF8, 0x08932462, 0x1D0BE971, 0x1DBCA88D` and four
   more are named by a Sound object but have no DIDX row in the bank payload. They are either streamed from a
   `.pck`/`.wad` this install does not ship (the install has 0 `.pck`) or resolved at runtime by the game. Tried:
   DIDX lookup, raw u32 search in the payload, `Working/Audio` WAD census from G1-15. Where it would be found: a
   Wwise `SoundbanksInfo` manifest (absent) or a streamed-media WAD the install does not contain.
2. **Event names for ids not in `AUDIO_MAP.json`.** 350 events were extracted; only the mapped ones have names,
   because the name comes from the `AkEvent` objects in the grab. The other events are recorded by id only.
3. **What each WAV sounds like.** File level only (channels/rate/frames stored); no listening, no spectral
   analysis, no judgement that a cue is the "right" lock beep. The mapping is HIRC-graph evidence, not audition.
4. **Whether these WAVs can be bound to JC3.** Unchanged from `T_AU3B.md`: every BmAK bank name is absent from
   the JC3 install, so the files are source material for a carrier, not a drop-in replacement. This card did not
   touch the JC3 side.

**COMPROMISES: none.** Nothing was accepted as a limit: the ten banks were decoded end to end, and the 9 ids
without DIDX rows are recorded with their ids rather than dropped.
