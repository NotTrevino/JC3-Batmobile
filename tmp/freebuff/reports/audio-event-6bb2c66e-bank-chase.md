# audio-event-6bb2c66e-bank-chase — the last unlocated Batmobile event

**STATUS: DONE.** `0x6BB2C66E` is not a missing bank. It is a second, *per-character*
declaration of a cue whose cooked form ships under its global twin's id. The bank is
`CHR_BatmanDisruptor`; the event in it is **`Play_Disruptor_Vehicle_Tracking_Fire` =
`0x8EA6FCA0`**. `0x6BB2C66E` (`Play_BatSniperRifle_Vehicle_Tracking_Fire`) is declared by an
`AkEvent` object in 13 packages and is cooked by **no** located bank.

All figures below are **decoded** from bytes by the tool named in §7. Nothing is inferred.

## 1. The chain, read end to end

| link | value | where it was read |
|---|---|---|
| map row | `Play_BatSniperRifle_Vehicle_Tracking_Fire`, `0x6BB2C66E`, outer `ww_chr_batmandisruptor`, bank_ref `Engine.CHR_BatmanDisruptor`, 3 rows, `media_rows` 0 | `Research/BatmobileGrab/AUDIO_MAP.json` |
| name → id rule | `fnv1(lower(name))`, offset `0x811C9DC5`, prime `0x01000193`; reproduces `0x6BB2C66E` | recomputed |
| declaring object | `AkEvent` named `Play_BatSniperRifle_Vehicle_Tracking_Fire`, outer path `ww_chr_batmandisruptor.Play_BatSniperRifle_Vehicle_Tracking_Fire`, in **13** packages (Asylum, Burton, Classic, Comic, Funhouse, MK2, Prototype, RedRobin, Riddler, Rocksteady, Snyder, Tumbler, `_SF`) | `upk_read.Package` export table |
| its payload | 18 bytes, `10 00 5c 00 de fe ff ff 02 00 54 00 6e c6 b2 6b 00 00` — id `0x6BB2C66E` little-endian at `0x0c` | same |
| bank census | **117** payloads, **29** distinct banks, **1101** HIRC Event ids: **0** carry `0x6BB2C66E` as HIRC id, raw LE, raw BE or ASCII | same |
| cooked twin | `AkEvent` `Play_Disruptor_Vehicle_Tracking_Fire` in `Startup` export 45965 and `StartupPatch` export 44721; payload `… a0 fc a6 8e 00 00` → id `0x8EA6FCA0` at `0x0c` | same |
| where that id lives | HIRC Event of `BmGame.CHR_BatmanDisruptor` **and** `StartupPatch.CHR_BatmanDisruptor` (2 of the 117 payloads) | bank census |

So both halves exist and they are different objects: a per-character `AkEvent` that names
`0x6BB2C66E`, and a global `AkEvent`/Wwise event `Play_Disruptor_Vehicle_Tracking_Fire`
(`0x8EA6FCA0`) that the bank actually cooks. `AUDIO_BANKS2.md` listed "a bank whose Event id
is renamed at cook time, in which case the declared id never exists" as one of four
possibilities; this is that case, now shown rather than conjectured.

## 2. Every place searched for the id

| # | search | scope | result |
|---|---|---|---|
| S1 | parsed HIRC Event ids (type `0x04`, id = first u32 of the object body) | 117 payloads from `AUDIO_BANKS.json` `present_in_packages` | 0 hits |
| S2 | raw u32 little-endian anywhere in the payload | same | 0 hits |
| S3 | raw u32 big-endian anywhere in the payload | same | 0 hits |
| S4 | ASCII `Play_BatSniperRifle_Vehicle_Tracking_Fire` inside the payload | same | 0 hits |
| S5 | package **name tables** of all 31 packages the banks live in (+ the map's declaring packages) | `upk_read.Package.names` | name present in 13 packages as an `AkEvent`; absent from `Startup`, `StartupPatch`, `BmGame`, `Engine` |
| S6 | export tables of those packages | `upk_read.Package.exports` | 13 exports named `Play_BatSniperRifle_Vehicle_Tracking_Fire`, 2 named `Play_Disruptor_Vehicle_Tracking_Fire`; all `class = AkEvent` |
| S7 | the 18-byte `AkEvent` payloads | `upk_read.Package.data(i)` | each holds exactly one id at `0x0c`: `0x6BB2C66E` (13 objects) or `0x8EA6F0A0`-family `0x8EA6FCA0` (2 objects) |
| S8 | both byte orders of `0x8EA6FCA0` against the 117 payloads | same as S1–S3 | 2 hits: `BmGame.CHR_BatmanDisruptor`, `StartupPatch.CHR_BatmanDisruptor` |

The 117 payloads are the ones `AUDIO_BANKS.md` (G3-14) located for the 29 referenced banks;
their SHA-1s still match `AUDIO_BANKS.json`, and every HIRC walk reaches its last object with
the recorded Event count (oracles O-2 and O-4 = PASS), so the miss is about the banks, not
about the reader.

**Not searched** (unchanged from `AUDIO_BANKS2.md`): the other 34,380 `AkBank` exports of the
install, and the 15 `BKPK`-magic `.bnk` files whose HIRC block this toolkit does not parse.
Neither can change the verdict — they could only add a *third* bank that also cooks the id —
but they are not claimed.

## 3. Which feature code the neighbours belong to

`AUDIO_FEATURES.json` puts the event in group **`weapons`** → serves **AUD-5** ("each weapon:
fire, loop, tail, impact, lock beep"). Its same-outer neighbour:

| event | id | group | AUD row |
|---|---|---|---|
| `Play_Batmobile_Tracker_Deploy` | `0x4F380472` | `tracker` | none (no AUD-1…AUD-7 row; a gadget cue) |
| `Play_BatSniperRifle_Vehicle_Tracking_Fire` | `0x6BB2C66E` | `weapons` | **AUD-5** |

The group→row mapping is the one `Research/JC3Grab/JC3_AUDIO.md` §9 records (engine→AUD-1,
afterburner/burnout→AUD-2, interior→AUD-3, battle-mode→AUD-4, weapons→AUD-5,
impacts/movement→AUD-6, horn→AUD-7). So the chase was for an **AUD-5** cue: the disruptor's
vehicle-tracking shot, i.e. a weapon event, not the tracker deploy beside it.

## 4. T-AU3 — the 26 declared ids of the 10 claim banks

25 of 26 are carried by a located BmAK bank; the one that is not is `0x6BB2C66E`.

| bank | id | event | in a located bank |
|---|---|---|:-:|
| `BML_Batmobile_Subjective` | `0x78DACB3D` | `Play_Batmobile_Jump_Wind` | yes |
| `BML_Batmobile_Subjective` | `0xA7C5D89A` | `Play_Batmobile_Jump_PreJump` | yes |
| `BML_Batmobile_Subjective` | `0xC3438074` | `Play_Batmobile_Jump_Land` | yes |
| `BML_Batmobile_Subjective` | `0xCE18923D` | `Play_Batmobile_Jump_PreLand` | yes |
| `BML_Impacts` | `0x3531A5D5` | `Play_Batmobile_Destroyed` | yes |
| `BML_Sonar` | `0x02EE7381` | `Play_BML_Sonar_Turn_On` | yes |
| `BML_Sonar` | `0x265FE0CD` | `Play_BML_Sonar_Turn_Off` | yes |
| `BML_Sonar` | `0x2A77A8B4` | `Play_BML_Sonar_Rumble_Lp` | yes |
| `BML_Sonar` | `0x835146BE` | `Stop_BML_Sonar_Rumble_Lp` | yes |
| `BML_Sonar` | `0x97CBF248` | `Play_BML_Sonar_Pulse_Search` | yes |
| `BML_Sonar` | `0xFFCC9813` | `Play_BML_Sonar_Pulse_Full` | yes |
| `CHR_BatmanAlerts` | `0xDEAD7680` | `Play_HUD_fail` | yes |
| `CHR_BatmanDisruptor` | `0x4F380472` | `Play_Batmobile_Tracker_Deploy` | yes |
| `CHR_BatmanDisruptor` | `0x6BB2C66E` | `Play_BatSniperRifle_Vehicle_Tracking_Fire` | **no** (cooked as `0x8EA6FCA0` under the global name) |
| `UI_InGame` | `0x274D2DAA` | `Play_HUD_Missile_Lock` | yes |
| `VEH_Tank_Heavy` | `0x12D072C1` | `Stop_VEH_Tank_Heavy_Locked` | yes |
| `VEH_Tank_Heavy` | `0x39553BB8` | `Play_Tank_Heavy_LockBeep` | yes |
| `VEH_Tank_Heavy` | `0x9279017E` | `Stop_VEH_Tank_Heavy_LockBeep` | yes |
| `VEH_Tank_Heavy` | `0xEDFB1D8F` | `Play_Tank_Heavy_Locked` | yes |
| `VEH_Tank_Missiles` | `0x4334B8A3` | `Stop_Batmobile_RocketTails` | yes |
| `VEH_Tank_Missiles` | `0x6D02C4D5` | `Play_Batmobile_RocketTails` | yes |
| `VFX_Tank_Explosion` | `0x3FC50C64` | `Play_Explosion_2D` | yes |
| `VFX_Tank_Explosion` | `0xBD404E03` | `Play_Batmobile_Immobiliser_Impact` | yes |
| `VFX_Tank_Explosion` | `0xD6730A26` | `Play_Tank_Explosion_Barrage_Sweetener` | yes |
| `VFX_Tank_Explosion` | `0xDD424156` | `Play_Batmobile_HeavyCannon_Explosion` | yes |
| `OBJ_Rolling_Objects` | `0x51A67708` | `Play_OBJ_Stagg_Battery_Roll` | yes |

**Which of them still lack a JC3 binding, and why.** All 26 do, and the reason is the same for
all of them: a JC3 binding is an addressable event or bank in the *target* install — a path, a
Jenkins hash or an FSB5 sample name the rebuilt `.ee` can name. `T_AU3B.md` searched all 27
BmAK bank names and `sound/fmod_banks/<name>.bank` against 78,907 distinct index hashes plus
the 649 decoded FSB5 sample names and found **27 of 27 absent**; JC3 exposes no Wwise/`AkEvent`
surface at all (`Research/JC3Grab/JC3_AUDIO.md` §10 route b). What differs is the *source*
side: for 25 of the 26 an event id is proven present in a located BmAK bank, so the row is
bindable the day a JC3 carrier exists; for `0x6BB2C66E` the source id is proven **absent**,
so binding that row as written would bind nothing — the bindable id is `0x8EA6FCA0`.

## 5. T-AU5 — the three families

| token | hits in `AUDIO_MAP.json` | hits in `AUDIO_FEATURES.json` | has any event id |
|---|---:|---:|:-:|
| `TransformationReverseDirection` | 0 | 0 | no |
| `TaserSound` | 0 | 0 | no |
| `VehicleSound` | 0 | 0 | no |

These are **member names on the vehicle classes**, not event names, so no row, no id and no
bank exists to look for. Their JC3 binding is one decision earlier than T-AU3's: the `.ee`
reference has to be decoded to an `AkEvent` id first (the same decode that produced the 361
map rows). Until then the row cannot be bound to anything, in JC3 or in BmAK.

## 6. What STATUS.md should say now

`STATUS.md` (generated by `Tools/scripts/status_audit.py`, line ~301) still says *"only event
`0x6BB2C66E` has no located bank (UNKNOWN)"*. Regenerated it should say: the bank is
`CHR_BatmanDisruptor` and the event is `Play_Disruptor_Vehicle_Tracking_Fire` (`0x8EA6FCA0`);
`0x6BB2C66E` is a per-character declaration the cook dropped, so **no event id is unlocated**.
That sentence is generated, not hand-edited — I did not touch `STATUS.md` or the generator.

## 7. Files and reproduction

| path | what it is |
|---|---|
| `Tools/scripts/audio_event_6bb2c66e.py` | the tool; `--write` / `--check` / `--print` |
| `Research/BatmobileGrab/AUDIO_EVENT_6BB2C66E.md` | the evidence card (generated) |
| `Research/BatmobileGrab/AUDIO_EVENT_6BB2C66E.json` | the same facts as data, inputs pinned by sha256 prefix |

```
python Tools/scripts/audio_event_6bb2c66e.py --write
python Tools/scripts/audio_event_6bb2c66e.py --check
```

`--check` re-derives all 117 payloads, the 31 package tables and both names, compares both
outputs byte for byte, and fails if the target id ever becomes carried by a payload or if the
T-AU3 unlocated set changes. Oracles at the last run: O-1 name rule PASS, O-2 payload SHA-1
PASS (117/117), O-3 raw-vs-parse PASS, O-4 event counts PASS.

Read-only throughout: the BmAK install is inspected, never written or launched; no existing
pin, ledger row or generated status file was edited.
