STATUS: done - the single unnamed archive entry is `patch_win64/game4` hash **`016DE9D1`** at +618637312, 84,720 B (16-byte prefix + one-sample FSB5 bank, token `1606523576`); 243,341 evidence-based candidate paths all fail `hash_jenkins(name) == 016DE9D1`, so its name is **UNKNOWN**, with every source searched and its hit count recorded.

# G2-last - the one archive entry that has no name

## 1. The entry

Located by diffing every `.tab` against the index (not by trusting the README):

| field | value |
|---|---|
| hash | **`016DE9D1`** |
| archive | `patch_win64/game4` - mount `patch`, 4,453 records, 4,452 named |
| offset / size | **+618,637,312 / 84,720 B** |
| payload magic | `E04A0100` - a 16-byte prefix (`u32 84704 = size - 16`, twelve zero bytes) then `FSB5` |
| decoded payload | FSB5 v1, **1 sample**, sample headers 60 B, name table 40 B, data 84,544 B |
| name table | exactly one string, `1606523576` (10 B) - the take token |
| identity | a `.wavc` (prefix + FSB5) one-take dialogue bank; the only identifying field is the FMOD token |

`INDEX.json` agrees independently: `unnamed_magic` = `{"patch_win64/game4": {"E04A0100": 1}}`,
`unnamed_sample_sizes` = `{"patch_win64/game4": [84720]}`, `tab_entries` 81,953 vs `named_rows`
81,952.

## 2. What the neighbours say

| relation | path | hash | offset | size |
|---|---|---|---:|---:|
| previous payload | `sound/dialogue/ara/mission_mm320_dial_gameplay_090.wavc` | `5567C6E5` | 618,592,256 | 44,368 |
| **the unnamed record** | `UNKNOWN` | **`016DE9D1`** | 618,637,312 | 84,720 |
| next payload | `sound/dialogue/ara/mission_mm320_dial_gameplay_start05.wavc` | `CB7DBEA9` | 618,723,328 | 141,040 |

Payloads start on 0x800 boundaries: the previous record ends at 618,636,624 and the unnamed
record starts at 618,637,312 (688 B of pad), and the next record starts at 618,723,328 where
this one ends at 618,722,032 (1,296 B of pad). So it is the sole occupant of that aligned slot,
and in write order it sits inside the Arabic `mm320` gameplay family - but "between those two
takes" is not a name: the `_091`-style take it would imply does not hash to it.

## 3. Every naming attempt, by source (the oracle rejects all of them)

`hash_jenkins(name.encode())` (a port of `StringHelpers.HashJenkins`, the same hash the `.tab`
stores) must equal `016DE9D1`.

| source | attempts | hits |
|---|---:|---:|
| every distinct `.wavc` basename in the index (14,849) x every dialogue language directory (11) | 163,339 | **0** |
| numeric takes 0..9999, widths 1..4, of both bracketing basenames | 80,002 | **0** |
| FSB5 token `1606523576` -> cross-language sibling basename | 0 candidates | **0** |
| `.ee` / `.toc` / `.adf` under `E:/Modding/_shared/gamedata/JC3grab` (39 files, 70.1 MB, depth <= 3, complete) | 39 files | **0** references |
| **total name candidates** | **243,341** | **0** |

The token route is closed for a reason that is decodable: the token is FMOD's *original source
file name*, not a hash of the shipped basename, and **no named path in the index contains that
take id**, so there is no sibling language copy to borrow a basename from - exactly the route
that named `archives_win64/game67` `966DB7BC` (token `a1630394639`, shared with the Japanese and
English copies).

## 4. Files written

- `Tools/scripts/jc3_last_entry.py` - new, `--write` / `--check`; re-reads all 88 tabs, the
  payload bytes, the index and the grab, re-runs 7 checks and byte-compares the document.
- `Research/JC3Grab/LAST_ENTRY.md` - the table above, the neighbour arithmetic, the attempt
  census, the reference search and the verdict.
- `Research/JC3Grab/LAST_ENTRY.json` - the same record for machines.
- This report. `Tools/names/*` was read, not edited; no game file was written.

## 5. Commands and output (verbatim)

```
$ uv run python Tools/scripts/jc3_last_entry.py --write && uv run python Tools/scripts/jc3_last_entry.py --check; echo "check exit=$?"
wrote Research/JC3Grab/LAST_ENTRY.md and Research/JC3Grab/LAST_ENTRY.json
entry 016DE9D1 in patch_win64/game4 +618637312, 84720 B, FSB5 token 1606523576, 1 samples
candidates tried 243341, hits 0 -> UNKNOWN - no candidate reproduces the hash
checks 7/7
CHECK OK: 7 checks, entry 016DE9D1, 243341 candidates, 0 hits, verdict UNKNOWN
check exit=0
```

The 7 checks, all PASS:

| check | evidence |
|---|---|
| `O1-one-unnamed-record` | INDEX.json 81,953 tab entries, 81,952 named, `unnamed_entries=1`; the tab-vs-index diff over 88 archives leaves exactly 1 record |
| `O2-identity` | `unnamed_magic` lists `E04A0100` once in `patch_win64/game4` and `unnamed_sample_sizes` lists 84720 - the record found here |
| `O3-payload-decoded` | prefix `u32 84704 = size - 16`, 12 zero bytes, then FSB5 v1, 1 sample, 60 B sample headers, 40 B name table, 84,544 B data |
| `O4-bracket-is-exact` | 0x800-aligned slot on both sides (pad 688 B / 1,296 B) |
| `O5-no-name-reproduces-the-hash` | 243,341 candidates, 0 hits |
| `O6-token-is-an-orphan` | name table carries exactly `['1606523576']`; no named path contains it |
| `O7-references` | 39 `.ee`/`.toc`/`.adf` files, 70.1 MB, complete scan, 0 references |

## 6. UNKNOWNs

- **The name itself.** 243,341 candidates fail the hash oracle. What would close it: the
  original FMOD project for the Arabic `mm320` session (the token is its source file name), a
  newer Gibbed filelist or JCMR dictionary carrying the take, or an executable string naming it.
- **The name table's 4 leading u32 fields** (68699 / 239296 / 83322 / 4 in this file). The single
  string is decoded and is the token; the field semantics are not decoded, and no naming test
  depends on them.
- **Why the take exists in the patch mount at all.** The record is `patch`-only and its two
  neighbours are Arabic `mm320` takes; nothing decoded says which session or line it belongs to,
  so "an Arabic mm320 line" is a bracket, not an identification.
