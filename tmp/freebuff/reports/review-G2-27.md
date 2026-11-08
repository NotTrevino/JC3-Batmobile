# Independent review — G2-27 · Standalone entity

Reviewer note: I did not write this card. This review is read-only; nothing under `GRAB_BACKLOG.md`,
`MODLOG.md`, `Research/`, `Tools/` or the game install was modified. No game was launched.

## VERDICT

**minor issues.** Every measured number I could re-derive is correct, `--check` is green, the
card's Done clause is met (a yes/no in `STANDALONE.md` §4 plus a file list in §5), and the
`UNKNOWN` on the drop-hash route is declared honestly. Three items should be corrected before the
numbers or the "no record" argument are quoted elsewhere: the registry record layout in §2 is
stated one byte off, the decisive "retail-playable DLC vehicle with no record" is true only at
exact-leaf granularity (the registry does hold a same-shaped record for the mech's base name), and
the 10,737,057 B / 604-file `.ee` is labelled "the donor" when it is the live build `test-091`
(the vanilla donor is 5,539,952 B). The card's answer — no global registry edit for a
path-referenced new leaf, hash resolution `UNKNOWN` — survives all three.

## Check output (verbatim)

```
$ python Tools/scripts/jc3standalone.py --check
PASS: 17 registration rows | registry records 251/922 index leaves (158/233 vehicles) | 101 spawned-by-path leaves unregistered | mod 20 .ee / 0 .toc, 20 vanilla paths | donor .ee 604 inner files, json match True, md match True
```

Exit status 0. Identical to the line recorded in `MODLOG.md` §"G2-27 · Standalone entity — done".
Out paths exist: `Research/JC3Grab/STANDALONE.md` (244 lines, matches the MODLOG's "244 lines"),
`Research/JC3Grab/STANDALONE.json`, `Tools/scripts/jc3standalone.py`.

What `--check` actually verifies: it re-runs `build()` + `report()` and compares the regenerated
markdown and JSON byte-for-byte with the files on disk. That covers every number the script emits,
but not typed numbers inside `report()` (see issue 6) and not the substance of the yes/no, which is
prose. The Done criterion is met by the content; the check enforces that the content is the
script's own output.

## Issues

1. **`Research/JC3Grab/STANDALONE.md:75-76` — the registry record layout is one byte off.**
   The doc says the record is "`03 <len16> <leaf>` followed by the leaf's 32-bit hash
   (`01496bb4` little-endian) - the same `D2B46B49`". The dump on line 72 gives the tail
   `8c863a7d01496bb4d2502586`; read little-endian, `01 49 6b b4` is `0xB46B4901`, not
   `D2B46B49`. The hash is actually at tail+5 (`49 6b b4 d2`), after an unexplained `01` byte, and
   `8c863a7d` is a second unexplained 4 bytes. The same shift is in the data:
   `STANDALONE.json` `registry.per_file.{base,patch}.donor_record.hash_after = "01496bb4"` and
   `hash_value = 3026929921` (`0xB46B4901`). The conclusion (it is the same `D2B46B49` G2-29
   searched for) is right; the stated layout and the JSON field are not, and the two boss bytes are
   presented as decoded when they are `UNKNOWN`. Anyone re-deriving the hash from the doc's quoted
   bytes gets a different number.

2. **`STANDALONE.md:109, 112-113` — "no record" is only true for the exact leaf name, not for the
   entity.** The decisive sentence is "a retail-playable DLC vehicle with **no record** means the
   registry cannot be a hard gate for *loading* an entity - it is a bake of the base roster's
   assets." `v0806_car_na_sportmech_01` is indeed absent as a leaf, but the patch registry holds a
   record of the identical shape for the mech's **base** name: offset 5,839,110 =
   `03 16 00` `v0806_car_na_sportmech` `8c863a7d 01 6b ff 44 5b 50 25 86 …` (`6b ff 44 5b`
   = `0x5B44FF6B` = `hash_jenkins("v0806_car_na_sportmech")`), and offset 6,047,588 =
   `03 1b 00` `v0806_car_na_sportmech_base` + its hash. The same name-space drift makes the DLC
   counts an upper bound: the registry carries `v0806_car_na_mech_minigun` /
   `v0806_car_na_mech_rebel_minigun` while the shipped leaves are `v0805_car_na_mech_*`, and
   `v0805_car_na_mech_generated` is present too. So "13 of 21 DLC production records unregistered"
   and "163 of 169 debug" measure *no record under the identical name*, not *no record for the
   entity's assets*; the doc must say so (R4) or the mech stops being a clean counter-example.
   The load verdict survives, because it rests on the spawn table's path strings, not on this.

3. **`STANDALONE.md:170-189`, `GRAB_BACKLOG.md:1310` — "the donor `.ee`" is the live build.**
   `Builds/test-091/…_civilian_01.ee` is 10,737,057 B; the vanilla donor at the same VFS path is
   5,539,952 B (`INDEX.jsonl`, base). §4.2, §5 and the tracker row therefore attribute our built
   entity's size, 604 inner files and 506-entry `.toc` to "the donor". The file is named correctly
   and the numbers are right for it (see spot-check 3) — the label is wrong, and 604 files is a
   property of the Batmobile build, not of the vanilla entity.

4. **`STANDALONE.md:6-13, 135-137` — the "yes to the loading" is a prediction, not a measurement.**
   Point 1 generalises in-game test-003 (a repacked `.ee` at a path the archives already contain)
   to "the dropzone directory is searched for a path whose archive entry also exists. A new path is
   the same lookup with every archive missing it." The property test-003 proves (an archive entry
   exists) is exactly the property a new path lacks, so this step is not established. The doc does
   hedge later ("yes, derived", point 5 "never been demonstrated"), but the headline and the
   tracker's "**YES for the load**" read as measured. It should read "yes, derived, untested".

5. **`STANDALONE.md:105` — "the `*_debug` entities" is 2 short.** Recomputed over the three
   `spawn_vehicle_proto_defs.bin` tables: 75 (74 `_debug`), 87 (86 `_debug`), 1 (1 `_debug`) =
   163 unregistered, of which 161 end in `_debug`; the other two are spawner entities
   (`spawner_mech_*`), which the same page lists as unregistered path-referenced leaves.

6. **R11: several counts in a generated doc are typed, so `--check` cannot catch them going stale.**
   Literals inside `report()`: `STANDALONE.md:18` "11,751 files / 7,719 MB"; `:20` "(86 records)";
   `:21` "0 shipped counter-examples"; `:22` "the mod's 20 `.ee`"; `:189` "1 inside the `.ee`";
   `:211` "13 tags, 1 of 41"; `:242` "the 9 spawn tables". All match today, but if
   `settings/spawn_vehicle_defs.bin` gained a record the table on `:123` would print 87 while line
   20 still said 86, and `--check` would stay green. Each is already available as a script variable
   (`sp['tables']`, `mod['ee_files']`, `needs['by_ext']`, `sites['count']`, `TRAFFIC.json` totals).

7. **`STANDALONE.md:27` and §1 title — the census scope is not stated.** `TRAFFIC.json`
   (`scan`) covers 11,751 files / 7.72 GB and records 59 unscanned extension classes / 70,201
   files / 48.6 GB, including `.gfx` (59 files, the frontend UI) and `.fl`. "Every registration
   site" and "a name + hash scan of 11,751 data files" should carry that limit. Related, the
   tracker (`GRAB_BACKLOG.md:1310`) compresses this into "17 registration rows by key type (9 spawn
   tables key on a full path string …)"; only **1** of the 17 census rows is a spawn table
   (`TRAFFIC.json` kinds: spawn table 1, level rule 2, Rebel Drop 2, task table 2, frontend 1,
   registry 2, localisation 2, patch metadata 1, self 2, other 2). The 9 tables are §3's separate
   analysis.

8. **`GRAB_BACKLOG.md:1310` — "0/86 base spawn records" is ambiguous.** Parsed with the trailing
   "unregistered" it means 0 of 86 unregistered, which matches the doc ("86 of them carry a registry
   record"); parsed on its own it reads as "0 of 86 registered", the opposite. Also
   "no shipped hash points at an unregistered leaf" generalises the measured claim ("all 80 vanilla
   vehicle drop items point at registered leaves", `STANDALONE.md:21`). True as far as I could test
   (spot-check 4), but the measurement covers the 80 vehicle drops only.

9. **`STANDALONE.md:51` — "Rows with `0` name hits … are not used for any claim" contradicts the
   table it introduces.** The two `profile/online.stringlookup` rows have 0 name hits, confidence
   "hash only (may be a coincidence)", yet they are given a key type and "optional, for a label",
   and the MODLOG lists the `.stringlookup` as a registration site. Either the note or the rows
   have to give.

10. **`STANDALONE.md:77` — "Each record also carries that entity's asset paths" is inferred.**
    No record delimiter or length was decoded; the asset-path attribution rests on file order plus
    the donor's own `.eff`/`.ctune`/`.vmod` paths. It does not affect the coverage counts (which
    only test string presence), but it is stated as decoded.

11. **`STANDALONE.md:175-189` — the extension table is silently truncated.** The rows list 10 of
    the 14 extensions (they sum to 600) under a total of "inner files 604"; §4.2 uses a trailing
    "..." for the same truncation, §5 does not. Cosmetic, but a summing reader gets 600.

12. **`STANDALONE.md:243` — §8 lists `REBELDROP.json` as an input; the script never opens it.**
    `REBELDROP` appears in `jc3standalone.py` only inside two prose strings (lines 466, 537).
    Consequently the "every shipped vehicle drop points at a leaf that does have a record" /
    "0 shipped counter-examples" statement is prose that `--check` does not verify (it is true —
    spot-check 4 — but the input list is wrong and the claim unguarded).

## Spot-checks

| # | value in `STANDALONE.md` | where I verified it |
|---|---|---|
| 1 | **251** of **922** index leaves registered, **671** without a record (:16, :91-93) | Independent exact-byte search `\x03 + <len16> + <leaf>` over both blobs `E:/Modding/JustCause3/_grab/standalone/{base,patch}_entityregistry_gen.entityregc`; 251 hits / 671 misses over the 922 distinct `.ee` leaves counted directly from `INDEX.jsonl` (81,952 rows). Matches. |
| 2 | base `settings/spawn_vehicle_defs.bin` = **86 records**, **27,513 B** (:20, :101, :124) | Re-read the file through `jc3grab`; 86 raw `.../entities/….ee` path occurrences, 86 distinct leaves, 0 duplicates, size 27,513 B = the `INDEX.jsonl` size. Same raw-vs-distinct check on all 9 tables (2/1/16/1/1/1/86/79/89) — all equal, so "records" is not hiding duplicate records. |
| 3 | donor `.ee` = **10,737,057 B**, **604 inner files**, `.toc` **506 entries**; mod **20 `.ee` / 0 `.toc` / 20 vanilla paths** (:22, :141-146, :155-160) | `eetoc.unaaf` + `eetoc.sarc_dir` on `Builds/test-091/v0300_…_civilian_01.ee`: 10,737,057 B, 604 SARC entries, 506 `.toc` entries. Walk of `Research/1456340180_Rebel-Drop-Mod-V5.3`: 20 `.ee`, 0 `.toc`, 20/20 paths present in `INDEX.jsonl` (15 distinct paths across the two variants — the "20" is a file count, see issue 3/11 for labelling). |
| 4 | "0 shipped counter-examples" for a hash pointing at an unregistered leaf (:21) | `REBELDROP.json` `vanilla.items`: 80 items of `Type 1`, all with `Name == UIName`, all 80 `UIImagePath` leaves present in the registry blobs. Claim holds; it is not derived by the script (issue 12). |
| 5 | **163 of 169** debug and **13 of 21** DLC production records unregistered (:105-108) | Recomputed from the nine tables: 79+89+1 = 169 records, 75+87+1 = 163 unregistered; 2+16+1+1+1 = 21 DLC production records, 1+11+0+0+1 = 13 unregistered. Matches, subject to the exact-name caveat in issue 2. |

## Not checked

- The MODLOG's tamper test and the `jc3index.py check` / `py_compile` lines were not re-run;
  reproducing the tamper test would write into `Research/`, which this review is forbidden to do.
- No game was launched and no dropzone or archive file was touched; the "can a new path load"
  question is therefore still exactly where the card leaves it (a Q-1 probe).
