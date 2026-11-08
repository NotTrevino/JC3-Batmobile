# t-au3-t-au5 - the blocked audio rows re-tested after G3-14

## STATUS

**done - 10/10 banks T-AU3 called absent are present (Startup, BmGame, StartupPatch), and
25 of its 26 event ids are HIRC `0x04` Events inside those payloads. The single miss is
`0x6BB2C66E` (`Play_BatSniperRifle_Vehicle_Tracking_Fire`), the same id AUDIO_BANKS2.md leaves
UNKNOWN. T-AU3 is therefore no longer blocked on banks; what it still lacks is that one id and
per-event media/source extraction. T-AU5 is still UNKNOWN for a different reason: its three
event families never resolved to an id at all, so there is no id to look up in the now-present
banks. `--check` PASS, `T_ROWS.jsonl` untouched (sha256 `8996b60a5370d932…`).**

Files written:

- `Working/Translation/AU_BLOCKED_RETEST.md` (11,644 chars - the per-bank and per-id tables)
- `Working/Translation/AU_BLOCKED_RETEST.json` (the same rows as data)
- `Tools/scripts/t_au_retest.py` (`--write` / `--check`; reads T_ROWS, never edits it)
- `tmp/freebuff/reports/t-au3-t-au5.md` (this card)

Untouched: `Working/Translation/T_ROWS.jsonl`, all `Research/BatmobileGrab/` files, the install.
No game launched or attached (INSTRUCTIONS §3).

---

## 1. What each row needs, exactly

**T-AU3** (T-2b, "90 event rows in 10 absent banks"): 90 rows / **26 distinct ids** over these
10 banks, every one of them present as an `AkBank` export:

| bank | rows | ids | carrier (package/export) |
|---|---:|---:|---|
| `BML_Batmobile_Subjective` | 4 | 4 | `Startup`/7756, 712,059 B |
| `BML_Impacts` | 1 | 1 | `BmGame`/131397 and `StartupPatch`/7454, 2,051,795 B |
| `BML_Sonar` | 6 | 6 | `BmGame`/131399, 355,830 B |
| `CHR_BatmanAlerts` | 1 | 1 | `BmGame`/131401 and `StartupPatch`/7457, 97,708 B |
| `CHR_BatmanDisruptor` | 2 | 2 | `BmGame`/131407 and `StartupPatch`/7463, 453,260 B |
| `UI_InGame` | 1 | 1 | `BmGame`/131652 and `StartupPatch`/9950, 2,799,217 B |
| `VEH_Tank_Heavy` | 4 | 4 | `Startup`/10397, 1,602,466 B |
| `VEH_Tank_Missiles` | 2 | 2 | `Startup`/10398, 2,752,713 B |
| `VFX_Tank_Explosion` | 4 | 4 | `BmGame`/131672 and `StartupPatch`/9966, 7,456,768 B |
| `OBJ_Rolling_Objects` | 1 | 1 | `BmGame`/131630, 516,986 B |

**T-AU5** (T-3, "`TransformationReverseDirection*` sounds, `TaserSound`, `VehicleSound`"):
- the two `TransformationReverseDirection*` fields are real serialised `AkEvent` properties
  (`MODES.md`: offsets 0x12dc / 0x12e4, present on V2/MK2/Joker/Funhouse), but the **ids of the
  events they point at are not decoded**;
- `VehicleSound` exists only as an `AkVehicleSound` component object (`ASSETS.md`), not as a
  mapped event;
- `TaserSound` has no decoded audio object in these censuses.

So T-AU5's blocker is **event identity**, not banks. G3-14 refutes only the row's parenthetical.

## 2. What the bytes look like offline

- **Banks: readable.** Every carrier above is an `AkBank` export with size + sha1; both bank
  cards re-read the payloads byte-identically (AUDIO_BANKS2 oracle `O-1-payload_sha1` PASS), and
  the install root `E:/Games/Batman - Arkham Knight` is present.
- **Per-event media: not established.** All 90 claim rows carry **0 media records** in
  `AUDIO_MAP.json` - the grab that produced them never opened these banks - and
  `AUDIO_BANKS2.json` records HIRC object types / `carries_bkpk`, not Sound/`DIDX`/`DATA` source
  ids. So "the wem bytes are on disk" is UNKNOWN for the 26 ids, neither confirmed nor refuted.
- **No streamed-audio container:** AUDIO_BANKS.md records 0 `.pck` in the install, so a streamed
  source would have no package to read; which of the 26 events is streamed is exactly the
  extraction above.

## 3. The 25/26 membership result

Membership was decoded from `AUDIO_BANKS2.json`'s HIRC walk (117 payloads, 1,101 event ids),
not inferred from the bank name: each of the 26 ids was looked up as a HIRC type-`0x04` object in
every located bank. 25 hit; `0x6BB2C66E` hits none, matching that card's own UNKNOWN answer
(`"no HIRC Event in any bank AUDIO_BANKS.md lists carries this id"`). Its candidate homes remain
an `AkBank` export outside the 117, an unparsed `BKPK` blob, a `BKPK`-magic `.bnk`, or a
cook-time rename.

## 4. Commands (verbatim)

```
$ cd E:/Modding/JustCause3/JC3-Batmobile && python Tools/scripts/t_au_retest.py --write; echo "write_exit=$?"; python Tools/scripts/t_au_retest.py --check; echo "check_exit=$?"
wrote Working/Translation/AU_BLOCKED_RETEST.md (11644 chars) and Working/Translation/AU_BLOCKED_RETEST.json
banks 10 FOUND 10 | rows 90 ids 26 carried 25 | not found ['0x6BB2C66E'] | T-AU5 hits 0
write_exit=0
claim banks 10 (FOUND 10) | rows 90 ids 26 | carried 25/26 | T-AU5 name hits 0/0 | T_ROWS sha 8996b60a5370
PASS: 10/10 banks present, 25/26 ids in a located bank, the miss is 0x6BB2C66E (UNKNOWN per AUDIO_BANKS2), T-AU5 has no resolved id, T_ROWS untouched
CHECK_EXIT=0
check_exit=0
```

The eight checks in the output document: T_ROWS sha unchanged; the claim table is 10 banks all
FOUND; the claim rows are 90 / 26 ids; every claim bank has a decoded carrier; exactly one id is
in no located bank and it is `0x6BB2C66E`; AUDIO_BANKS2's answer for it is UNKNOWN; T-AU5's
families have 0 name hits in the 361-event map and the 361-event feature census; the two
`TransformationReverseDirection*` fields are present in MODES.md.

## 5. UNKNOWNs (with what was tried)

1. **Where `0x6BB2C66E` lives.** Searched: all 117 located payloads as HIRC events and as raw LE
   u32. Remaining candidates listed in §3. Settling it means scanning all 34,497 `AkBank` exports.
2. **Each event's media/source ids and bytes.** Not decoded by either bank card; 0 media rows on
   the 26 claim ids. Where it would be found: the located payloads' Sound objects and their
   `DIDX`/`DATA` ranges.
3. **T-AU5's AkEvent ids.** The properties are serialised, the referenced `AkEvent` objects were
   never resolved. No bank lookup is possible until they are.
4. **Audibility in BmAK.** Nothing here observes the game; no launch or attach (§3).
