# review-G3-14 · independent re-test of the audio-bank claim

**STATUS: done.** The claim holds at bank level and G3-14's refutation of "10 banks absent" is
**confirmed** for the three banks re-tested here: each is a real `AkBank` export in the
install, each payload is a well-formed Wwise bank (`BKHD` id 112, `DIDX → DATA → HIRC → STID`,
HIRC tiling exactly), and every chunk walk lands inside the payload. One event-level discrepancy
surfaced, which is G3-14's own declared UNKNOWN: 11 of the 12 event ids the Batmobile uses across
those three banks are in their bank; `0x6BB2C66E`
(`Play_BatSniperRifle_Vehicle_Tracking_Fire`, declared at `Engine.CHR_BatmanDisruptor`) is **not**
among `CHR_BatmanDisruptor`'s 17 events. The id itself is correct — the name→id rule was
identified and reproduces 12/12 known pairs — so this is a fact about the bank, not a bad lookup.
No translation decision is made here; the ledger consequence is stated in the last section.

`review_g314.py --check` exits 0; `grab_audio_banks.py --check` exits 0.

## Files written (only these)

| file | what |
|---|---|
| `Tools/scripts/review_g314.py` | the review tool; `--write` regenerates both outputs, `--check` re-derives every byte range and fails on drift. Imports nothing from `grab_audio_banks.py`; carries no value from `AUDIO_BANKS.json` (that file is the thing under review) |
| `Research/BatmobileGrab/AUDIO_REVIEW_G314.json` | 15,178 B — inputs + package headers, the 4 copies with their full chunk walks, per-bank id lookups, the six hash-rule tests, the missing-id hunt, duplicates |
| `Research/BatmobileGrab/AUDIO_REVIEW_G314.md` | 7,065 B — the same as tables |
| `tmp/freebuff/reports/review-G3-14.md` | this report |

Read-only everywhere else: no edit to `grab_audio_banks.py`, `AUDIO_BANKS.*`, `AUDIO_MAP.json`,
`GRAB_BACKLOG.md`, `MODLOG.md`, any other report; nothing written under `E:/Games` or `D:/Games`;
no game launched or attached; no commit.

## Commands and outputs (verbatim)

```
$ python Tools/scripts/grab_audio_banks.py --check
OK 29 referenced banks over 361 event rows; 34497 AkBank exports in 4145 packages; 0/10 claim banks confirmed absent; md+json byte-identical
oracles: banks_refound=True, hirc_mismatches=0, claim_verdicts={'BML_Batmobile_Subjective': 'FOUND', 'BML_Impacts': 'FOUND', 'BML_Sonar': 'FOUND', 'CHR_BatmanAlerts': 'FOUND', 'CHR_BatmanDisruptor': 'FOUND', 'UI_InGame': 'FOUND', 'VEH_Tank_Heavy': 'FOUND', 'VEH_Tank_Missiles': 'FOUND', 'VFX_Tank_Explosion': 'FOUND', 'OBJ_Rolling_Objects': 'FOUND'}
banks: present 29 package, 0 file, absent 0
exit=0
```

```
$ python Tools/scripts/review_g314.py --write
wrote Research\BatmobileGrab\AUDIO_REVIEW_G314.json and Research\BatmobileGrab\AUDIO_REVIEW_G314.md
packages opened 4 | banks located 3/3 | copies 4 | structure_ok True
ids: 11/12 found | hash rule fnv1(lower(name)) 12/12
  BML_Batmobile_Subjective   Startup                  events 12  ids 4/4 all found
  BML_Sonar                  BmGame                   events 7   ids 6/6 all found
  CHR_BatmanDisruptor        BmGame+StartupPatch      events 17  ids 1/2 MISSING 0x6BB2C66E
missing id hunt over 20 referenced banks: not found
write exit=0
```

```
$ python Tools/scripts/review_g314.py --check
check OK: 4 packages re-opened, 4 copies re-parsed, every chunk walk and HIRC/DIDX accounting tiles, 11/12 Batmobile ids found, hash rule fnv1(lower(name)) 12/12, md+json byte-identical
  BML_Batmobile_Subjective   events 12  ids 4/4 all found
  BML_Sonar                  events 7   ids 6/6 all found
  CHR_BatmanDisruptor        events 17  ids 1/2 MISSING 0x6BB2C66E
check exit=0
```

```
$ ls -l Research/BatmobileGrab/AUDIO_REVIEW_G314.*
-rw-r--r-- 1 User 197121 15178 Nov  3 07:48 Research/BatmobileGrab/AUDIO_REVIEW_G314.json
-rw-r--r-- 1 User 197121  7065 Nov  3 07:48 Research/BatmobileGrab/AUDIO_REVIEW_G314.md
```

## VERDICT

**SUPPORTS G3-14**, with one correction at event level that G3-14 did not claim and flagged as its
own UNKNOWN.

| question | answer | basis |
|---|---|---|
| Are the three banks in the install? | **yes, 3/3** | decoded: `AkBank` exports, 4 copies over 3 packages |
| Is the payload real bank data? | **yes, 4/4 copies** | decoded: `BKHD` id 112, full chunk chain, HIRC tiles with 0 pad, DIDX 100% inside DATA |
| Are the Batmobile's event ids in them? | **11/12** | decoded: HIRC type-0x04 ids |
| Was "10 banks absent" wrong? | **yes for these 3** | the three are present and decodable; the other 7 are quoted from G3-14, not re-read here |

## The three banks (decoded: package + export + payload offset)

| bank | package | export | file offset | bytes | sha1 | BKHD at | chunks | HIRC obj/count | events | DIDX in DATA |
|---|---|---:|---:|---:|---|---:|---|---:|---:|---|
| `BML_Batmobile_Subjective` | `Startup` | 7756 | 20,560,301 | 712,059 | `9b057ac9612031a5` | 135 | BKHD→DIDX→DATA→HIRC→STID | 61/61 | 12 | 18/18 |
| `BML_Sonar` | `BmGame` | 131399 | 28,905,351 | 355,830 | `3151382d4c24eb72` | 2160 | BKHD→DIDX→DATA→HIRC→STID | 67/67 | 7 | 22/22 |
| `CHR_BatmanDisruptor` | `BmGame` | 131407 | 38,229,950 | 453,260 | `0aa7842d470f483c` | 2170 | BKHD→DIDX→DATA→HIRC→STID | 118/118 | 17 | 40/40 |
| `CHR_BatmanDisruptor` | `StartupPatch` | 7463 | 28,649,656 | 453,260 | `410814e9ffb298a4` | 2170 | BKHD→DIDX→DATA→HIRC→STID | 118/118 | 17 | 40/40 |

On "is it real bank data" the evidence is structural, not a magic-string hit — a fake or truncated
blob cannot pass all of: the chunk chain is **walked** (each `u32 size` lands the next chunk on a
known Wwise magic or exactly at the payload end, `chunk tail` 0), `HIRC` tiles its chunk exactly
with 0 pad bytes, `HIRC objects == HIRC count`, DIDX's 12-byte records (id, offset, size) all point
inside DATA, and one Event body layout fits all events under it (the alternative `u8 scope` layout
fits none — so the parse is not ambiguous).

Package headers, for the file+offset trail: `BmGame.upk` 214,757,637 B / v863 / licensee 32995 /
177,031 exports, name+import+export prefix 15,529,470 B; `Startup.upk` 434,869,146 B / 174,890
exports / 16,103,363 B; `StartupPatch.upk` 248,812,096 B / 142,232 exports / 13,065,905 B;
`Engine.upk` 26,578,385 B / 39,080 exports / 3,637,868 B. The prefix must be decompressed only to
the export-table end, which is why four packages of this size are cheap to open.

## Event ids, id by id (decoded; declared from `AUDIO_MAP.json`)

`BML_Batmobile_Subjective` — 4/4 found. Bank carries 12 events: `0x66B6C3A7`, `0x78DACB3D`,
`0x9F5181BC`, `0x9F5181BD`, `0xA7C5D89A`, `0xA86F5A4E`, `0xACB34CB7`, `0xC3438074`,
`0xCE18923D`, `0xD58EF546`, `0xD6BC3575`, `0xD6BC3576`. The Batmobile's: `0xC3438074`
`Play_Batmobile_Jump_Land`, `0xA7C5D89A` `Play_Batmobile_Jump_PreJump`, `0xCE18923D`
`Play_Batmobile_Jump_PreLand`, `0x78DACB3D` `Play_Batmobile_Jump_Wind` — all present.

`BML_Sonar` — 6/6 found. Bank carries 7 events (`0x02EE7381`, `0x265FE0CD`, `0x2A77A8B4`,
`0x4B0D3A52`, `0x835146BE`, `0x97CBF248`, `0xFFCC9813`); the Batmobile uses six of them, including
the pair `0x2A77A8B4` `Play_BML_Sonar_Rumble_Lp` / `0x835146BE` `Stop_BML_Sonar_Rumble_Lp`.

`CHR_BatmanDisruptor` — **1/2**. Bank carries 17 events: `0x07CE378F`, `0x16443024`, `0x308BC06A`,
`0x42F3A5EF`, `0x4F380472`, `0x5BC3EE41`, `0x62F2DD13`, `0x741478DC`, `0x8EA6FCA0`,
`0x9C5EF1D6`, `0xB38D34B4`, `0xB4635EBB`, `0xBF0CEE98`, `0xDA7661EA`, `0xEE5F1211`,
`0xF1BB7098`, `0xF94B9C61`. Present: `0x4F380472` `Play_Batmobile_Tracker_Deploy`. **Absent:
`0x6BB2C66E` `Play_BatSniperRifle_Vehicle_Tracking_Fire`.**

## The absent id is the right id (derived, and why it matters)

Before calling that a miss I had to rule out a wrong hash. Six candidate rules over the 12 known
(name, id) pairs in `AUDIO_MAP.json`:

| rule | matches |
|---|---:|
| `fnv1(lower(name))` | **12/12** |
| `fnv1(name)` | 0/12 |
| `fnv1a(lower(name))` | 0/12 |
| `fnv1a(name)` | 0/12 |
| `crc32(lower(name))` | 0/12 |
| `crc32(name)` | 0/12 |

FNV-1 (the classic 32-bit prime/XOR, over the **lowercased** name) reproduces every pair including
`0x6BB2C66E`, so the id in the map is right and the bank genuinely does not declare it. This
upgrades G3-14's UNKNOWN from "not tried" to a decoded negative for that one id, and it also
gives the general rule: any event name's id can now be computed rather than guessed.

## Where that id is not (decoded, bounded)

The 20 `AkBank` exports named by 14 of the 29 referenced banks were parsed in the four packages
above (`BmGame` 7, `Engine` 4, `Startup` 3, `StartupPatch` 6) and every event set searched for
`0x6BB2C66E`: **found in none of them** — not in `BmGame`'s own `CHR_BatmanDisruptor`, not in
either `BML_Batmobile` bank, not in `BML_Tyres`/`BML_Battlemode`/`BML_Impacts`/`CHR_BatmanAlerts`/
`OBJ_Rolling_Objects`/`UI_InGame`/`VFX_Tank_Explosion`/`WEA_Rain_Materials`/`VEH_Tank_*`. The
remaining 15 referenced banks (8 `DLG_*`, 3 `SEQ_*`, `BML_Burnout`, `BML_Engine`,
`CHR_Joker_Foley_Gun`, `VEH_Batmobile_MK2_Engine`) live in level packages this card did not open.

## Duplicate copies are not byte-identical

`CHR_BatmanDisruptor` exists in `BmGame` (sha1 `0aa7842d470f483c`) and `StartupPatch`
(`410814e9ffb298a4`): same 453,260 bytes, same `BKHD` id and version (3303467862), same 118 HIRC
objects, same 17 event ids — but **different bytes**. G3-14's table quotes per-carrier sha1s, so it
is not wrong; the difference is worth recording because "the patch replaces the bank" and "the
patch ships a second, differently-built copy" are distinguishable from these two hashes but not
from one. Both copies carry the same event set, so the miss above holds for both.

## What this means for the ledger (no translation decision)

- `T-AU3` / `T-AU5`'s block reason "90 events in 10 banks absent from the install" is **refuted**,
  independently for 3 of the 10: those banks are in the install and decode. The correct wording is
  G3-14's: banks present, per-event content the remaining gap.
- The tracker-fire row is a different defect from the one G3-14 fixed. `0x6BB2C66E` is a valid id
  pointing at `Engine.CHR_BatmanDisruptor`, and that bank does not carry it. So the row is not
  blocked on a missing bank *or* on a missing decode — its `bank_ref` is wrong (or the event ships
  in an unnamed `ww_*` bank). Until the owning bank is found, that row cannot be resolved by
  reading `CHR_BatmanDisruptor` further.

## UNKNOWN

- **Which bank owns `0x6BB2C66E`.** Tried: full HIRC event-id search of the 20 exports named by 14
  referenced banks in `BmGame`/`Startup`/`StartupPatch`/`Engine` (in `--check`); raw-byte search of
  every `.bnk` under the install and a full-name search inside `CHR_BatmanDisruptor`'s `STID`
  (exploratory, this session, not reproduced by `--check` - no hit in either). Not tried: the 15
  other referenced banks (level packages), and a
  name-table (`ww_chr_batmandisruptor`) scan of all 4,145 packages. Where it would be found: that
  scan, or a `SoundbanksInfo` manifest (none under the install root).
- **What each event plays.** Event ids are declared by the bank; their action lists were not
  followed into `CAkActionPlay`/`AkBankSourceData`, so no media id is claimed per event here.
- **The other seven claimed-missing banks.** Not re-read by this tool; their FOUND verdicts are
  `grab_audio_banks.py`'s, whose `--check` passes but is not independent of itself.
- **Runtime playability.** Every statement above is a file fact. Nothing observes the game loading
  a bank; out of scope (no attach).
