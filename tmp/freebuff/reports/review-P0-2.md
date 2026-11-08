# Independent review — P0-2 · Feature census script

Reviewer: Freebuff, not the card author. Read-only: nothing under `GRAB_BACKLOG.md`,
`MODLOG.md`, `Research/`, `Tools/` or any game file was modified; this report is the only write.
No game launched, no commit, no secrets. Date 2026-10-29.

Card (`GRAB_BACKLOG.md:368-376`), checklist row (`GRAB_BACKLOG.md:1275`), MODLOG done section
(`MODLOG.md:7752-7795`, "P0-2 · Feature census written, and the four §2 claims reconciled
(2026-10-24)"; intent section at `:7742-7750`). Outputs: `Research/JC3Grab/FEATURE_CENSUS.json` (112,522 B),
`Research/JC3Grab/FEATURE_CENSUS.md` (24,926 B), `Tools/scripts/jc3_feature_census.py`.

**VERDICT: minor issues.** The census is real, generated and reproducible: `--check` re-derives both
files from the readers' outputs and passes, every number I could recompute from the raw decoded
graphs matches (232 entities, 17 chassis / 45 `.ee` / 57 objects for `CBulletWeaponBase`, 3
`EngineRotatingPart` parts on `v0506`, 233 parts rows / 11,643 parts), and the §2.1 / §2.3 wording
in the backlog was actually corrected to the census's numbers. Two things are wrong: the sha256
values quoted in the MODLOG do not match the delivered files, and the doc's "every vehicle carries
one" is a fleet-wide claim from a 79-chassis sample. Plus two R11/R4 nits.

## Check output (verbatim)

```
$ time python Tools/scripts/jc3_feature_census.py --check
ok FEATURE_CENSUS.json
ok FEATURE_CENSUS.md
check ok: census matches the data (232 entities, 53 armed, 25 weapon ids)

real    0m2.397s
```
Exit status 0.

## Issues

1. **The MODLOG's sha256 claim does not match the files on disk.**
   `MODLOG.md:7769-7770`: "Two `--write` runs produced identical sha256 (`652bb5f3…` JSON,
   `ac8d011d…` MD), so the file is order-stable." The delivered files hash to
   `241a8272e421ac0eb5aaaa2764836684286cf695a5f6758ecc04827c88185c57` (JSON) and
   `8fc0602569fc4ec8486451c1f4fd5ed66549c5f305493fc875c4c868b0fc55f2` (MD) — different in the
   first bytes, so not a truncation artefact. Either the files were regenerated after the sentence
   was written, or the quoted hashes were not taken from these files. `--check` still passes (the
   content is self-consistent), so the *output* is fine, but the log's order-stability evidence
   cannot be checked and the hashes do not identify the delivered artifacts — the one thing a hash
   in a log is for (R14 asks for the command output).

2. **"every vehicle carries one" is a fleet-wide claim from a 79-chassis sample.**
   `FEATURE_CENSUS.md:40` and the renderer line (`jc3_feature_census.py:507-508`): "so
   `CForcePulse` is listed; **every vehicle carries one**, and it is excluded from the armed list
   below." The evidence is 232 `.ee` files over **79** chassis (the `CForcePulse` row:
   `307 objects / 232 .ee / 79 chassis`). The project's own fleet count is "41 members over 156
   vehicles" (`t3_fleet.py --check`, §12). The 232 decoded entities are the whole *decoded* set, but
   they are 79 chassis, not 156 vehicles — so "every vehicle" is untested for the other 77. The
   exclusion of `CForcePulse` from "armed" rests on it: if some vehicle lacked the component, the
   armed count and the "CForcePulse on everything" statement would both be wrong. Correct wording:
   "every decoded entity (232/232 over 79 chassis) carries one".

3. **Numbers typed inside the reconciliation verdict strings (R11).**
   The `derived` column is computed (`jc3_feature_census.py:351-392`), but the `verdict` strings
   repeat the same numbers as literals — e.g. `"match (25 ids after the w613_bomb alias; 26
   spellings; 22 archive dirs)"` (`:357`), `"53 armed .ee over 21 chassis (17 bullet + 7 missile - 3
   chassis with both)"` (`:383-384`, where only the two leading counts are `%d`). If the data
   shifts, `--check` re-derives the `derived` column and rewrites both files, but the verdict text
   stays as typed — and `--check` still passes because JSON and MD agree. That is exactly the
   stale-number path R11 exists to prevent.

4. **The Done clause is only half automatable, and `--check` does not cover the half it names.**
   The card's Done is "`--check` passes; the `.md` reproduces every number in §2.1 and §2.3". The
   first half is verified (above). The second is a comparison between the generated `.md` and the
   *prose of `GRAB_BACKLOG.md` §2*, and `--check` never reads `GRAB_BACKLOG.md`. It holds today —
   §2.1 now says "17 chassis / 45 `.ee` / 57 objects" (`:263-264`), §1.4 WPN-5 says "79 chassis /
   232 `.ee`" (`:165`), §2.3 says "9 chassis: 8 cars + `v1302` sailboat" (`:304-305`) — but a later
   edit to §2 would leave `--check` green while the Done clause silently failed. The census emits
   the numbers; nothing forces the prose to keep quoting them.

5. **Unverifiable history (minor).** `MODLOG.md:7786` (reconciliation table) explains the old "24 armed entities" as
   "17+7 with 3 overlapping chassis counted twice". The overlap arithmetic is right (17+7−3 = 21),
   but which ad-hoc scan produced 24 is not recorded and cannot be re-derived from the data; it is
   a plausible story, not evidence. Nothing downstream depends on it once the 53-row list is used.

## Spot-checks

| value in the doc | where verified | result |
|---|---|---|
| "232 entities" (`FEATURE_CENSUS.md:27`, `--check` line) | `ls E:/Modding/JustCause3/_grab/detail/*.ee.json | wc -l` | 232 — exact |
| "`CBulletWeaponBase` 57 objects / 45 `.ee` / 17 chassis" (`FEATURE_CENSUS.md:46`, reconciliation `:325`, §2.1 `:263`) | independent scan of the same 232 graphs: files containing the class = 45; occurrences of `"class": "CBulletWeaponBase"` = 57; distinct chassis prefixes = 17 | 45 / 57 / 17 — exact on all three |
| "`EngineRotatingPart` on `v0506`: 1 chassis, 3 parts" (`FEATURE_CENSUS.md:332`, §2.3 `:305`) | `Research/JC3Grab/PARTS_TABLE.jsonl`: rows with a part whose `b` is `EngineRotatingPart` = 3, all under `v0506_car_solar_oldtractor` | 1 chassis / 3 parts — exact |
| "53 armed / 21 chassis" (`FEATURE_CENSUS.md:28-29`, `:329`) | `FEATURE_CENSUS.json`: `len(armed_entities)` = 53, distinct `chassis` = 21; `totals.armed_chassis` = 21 computed from the armed list (`script:139-145`, `:456`) | consistent (the field is not a mislabelled all-chassis count: 79 chassis exist in the `.ee` set) |
| inputs "233 rows / 11,643 parts", "81,952 INDEX rows" (`MODLOG.md:7755-7756`) | `PARTS_TABLE.jsonl` = 233 rows / 11,643 parts; `INDEX.jsonl` = 81,952 lines | exact |

## Out paths and Done

All three Out paths exist and are generated (the `.md` is rendered from the same object, both are
byte-compared by `--check`). The card's Done passes on its automatable half and the numbers it names
are present in the `.md` and correct; the §2 prose it also requires was corrected and matches (issue
4 for the durability gap). The script really is self-contained: it opens only
`E:/Modding/JustCause3/_grab/…` and `Research/JC3Grab/*.jsonl`, writes only the two census files, and does
not decode a game file.
