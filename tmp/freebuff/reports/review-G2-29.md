# Review — G2-29 · Traffic, AI and spawning of `v0300`

Reviewer: independent (did not write the card). Read-only pass: `GRAB_BACKLOG.md`, `MODLOG.md`,
`Research/` and `Tools/` were only read; the archives were read only through the project's own
reader; nothing outside this file was written, no game launched, no git.

Scope: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G2-29 card (§7, line 773) and its §12 row;
`MODLOG.md` §"G2-29 … — done" (line 10484); `Research/JC3Grab/TRAFFIC.md` (163 lines),
`Research/JC3Grab/TRAFFIC.json`, `Tools/scripts/jc3traffic.py`.

## VERDICT

**Minor issues.**

The card is answered and the core record is real — I re-read the raw spawn table and counted
**86 distinct `.ee` paths**, and the donor's record reads exactly as claimed: path, the thirteen
tags `vehicle,ground,car,civilian,racing,modern,muscle,kensington,sports,unarmed,unarmored,ambient,
liberated`, the leaf name, and no pool key anywhere in that record. The selector match is also
exactly as printed (`ambient,ground,car,liberated,-highend` → `03_CivilianCarLiberatedProvince`),
the rule/selector counts reproduce from the JSON (31 names / 41 selectors / 1 match / 40 misses /
10 `.bts` paths), and the two level-rule rows really do contain `CVehicleRule` (1×) and
`point.stunt` (2×) alongside the donor name. R5 is respected where it counts: §6 states plainly
that the tag matcher is native and that "1 of 41 selectors matches" is a string-level match.

What is not clean is provenance for the *kinds* of file and for a couple of sentences: the §1
"what it is" column and the §4 evidence cells are hardcoded filename heuristics inside the
generator (`kind`/`note` by path), so `--check` re-asserts them without ever measuring them, and the
document's closing line — "Every number here is regenerated from the archives; none is typed by
hand" — is one step stronger than what the pipeline does. The headline also states the D-6
conclusion flatly while the qualifier sits two sections later.

## Check output (verbatim)

Command run from `E:/Modding/JustCause3/JC3-Batmobile`:

```
$ python Tools/scripts/jc3traffic.py --check
PASS: 11751 files scanned (7719 MB, A+B), 17 name the donor (Rebel Drop/entity registry/frontend/level rule/localisation/other/patch metadata/self/spawn table/task table), 86 spawn records (8 with a pool key), donor tag list of 13 tags, 31 traffic rules / 41 selectors, 1 match (`ambient,ground,car,liberated,-highend`), 10 AI behaviour trees
```

Exit status `0`. Identical to the line pasted in `MODLOG.md` under the G2-29 done heading.

Out paths — present:

| path | state |
|---|---|
| `Research/JC3Grab/TRAFFIC.md` (card's only Out) | present, 163 lines, §1–§8 |
| `Research/JC3Grab/TRAFFIC.json` (row) | present: `scan`, `spawn`, `rules`, `profiles`, `donor`, `donor_modules`, `inputs` |
| `Tools/scripts/jc3traffic.py` (row) | present, `--write`/`--check`/`dump` |
| README section + Files row, §12 row, MODLOG done section | present |

## Issues

### 1. (R11) The per-file "what it is" column is a filename heuristic, not a decoded kind — `Tools/scripts/jc3traffic.py:200`–`220`, `Research/JC3Grab/TRAFFIC.md:14`–`19`

`hit_kind()` returns a hardcoded `(kind, note)` from the path: any `*.blo` becomes "level rule / a
`CVehicleRule` in a level's logic object", `profile/item.onlinec` becomes "Rebel Drop / an item in
the Rebel Drop list", `profile/task.onlinec` becomes "a task key naming the vehicle (chop shop)".
Those strings go into `TRAFFIC.json` as data, so `--check` regenerates them — but it is re-deriving
a constant, not re-measuring the file. The `confidence` column covers *name matching*, not the
kind, so a reader cannot tell which of the two is established. I spot-checked two of the
attributions and they hold (`CVehicleRule` 1× and `point.stunt` 2× in each of the two `.blo`
files), so this is a labelling defect, not a wrong claim. Recommend a `kind_basis: name` column or
one line under the table.

### 2. (R11) "Every number here is regenerated from the archives; none is typed by hand" is too strong — `Research/JC3Grab/TRAFFIC.md:163`

The numbers are derived; three statements in the same file are literals in `render_md()` that no
assertion covers:

* `:127` — "`CVehicleRule` + `point.stunt` + the donor name in the level's logic object"
  (`jc3traffic.py:543`). True (verified in both files, above), typed.
* `:37` — "`settings/spawn_budget_pools.bin` names it as *Ground Vehicles*, alongside
  `spawn_aircraft_defs.bin`, `spawn_boat_defs.bin`" (`jc3traffic.py:462`–`463`). True — the budget
  file groups `settings/spawn_vehicle_defs.bin` under the string `Ground Vehicles` — typed.
* `:105` — the five excluded `*Rule` names (`jc3traffic.py:508`–`509`). The count is derived
  (`other_rules` = 5), the names are typed, and those five are exactly the ones the script chose to
  exclude from `rule_names`; a sixth would silently move into "traffic rule names".

The sentence should say the numbers and counts are re-derived, not "every number".

### 3. (R4) The headline states the D-6 consequence as settled while the decisive unknown is two sections away — `Research/JC3Grab/TRAFFIC.md:3`, `:146`

Line 3: "`…_civilian_01` is a civilian traffic vehicle, **so replacing it puts AI-driven Batmobiles
on the roads**". The evidence chain is a tag-list selector match plus `Driver` seats in the rule
block; §6 correctly says the matcher is native and that nothing in the archive states a superset
rule, and §7's route table repeats the conclusion as fact. The card asks exactly this question, so
answering it is right — but the one sentence that decides D-6 should carry its own confidence (the
tags *select it into* the civilian-car rule; the runtime picker is UNKNOWN), the way §6 and the
MODLOG paragraph do. As written, a reader who stops at the summary has a firmer claim than the
data.

### 4. (method, minor) "1 of 41 selectors" mixes vehicle selectors with character selectors — `Research/JC3Grab/TRAFFIC.md:105`, `:117`

The doc says the 41 selectors are "vehicle lists and driver-character lists", and the §3 sample
table includes `character,civilian` rows. A character selector can never match a vehicle record, so
the denominator inflates the impression of selectivity: the meaningful figure is "1 of the N
vehicle selectors". The JSON has all 41 (`rules.selectors`), so splitting them is a two-line
change; the current phrasing is not wrong, just not the sharpest form of the card's answer.

### 5. (data note, not a defect) The pool-key paragraph is a good correction of the card's premise — `TRAFFIC.md:39`

Worth recording in the review because it is the kind of thing that usually goes unsaid: the earlier
pass had read `a|b|c` strings as group labels and invented 35-record pools; the doc says so, and
shows that each of the 8 keys occurs once (`spawn.main.pool_counts` all 1), so the donor's pool is
UNKNOWN. That is the honest form of R4 and it is done.

## Spot-checks

| # | value in `TRAFFIC.md` | where verified |
|---|---|---|
| 1 | "`settings/spawn_vehicle_defs.bin` … **86 records**", donor record at offset 23240 = path + 13 tags + name, "pool key none" (§2, lines 37–58) | Re-read the base archive entry directly (`jc3grab.read_entry`, 27,513 B) and extracted its printable strings: **86 distinct `.ee` paths**; the donor's record strings are its path, the 13-tag list exactly as tabled, and the leaf name, with no `a\|b\|c` key in the record. Matches `TRAFFIC.json` `spawn.main` (`records` 86, `keyed_records` 8, `donor_record.offset` 23240). |
| 2 | "**31 traffic-rule names**, **41 tag selectors** … **10 AI behaviour-tree paths** … **1 of 41 selectors match**" (§3, lines 105–117; check line) | `TRAFFIC.json` `rules`: `rule_names` 31, `selectors` 41, `selector_count` 41, `bts` 10, `donor_matches` 1, `donor_misses` 40; the matching selector string in `donor_matches` is `ambient,ground,car,liberated,-highend` and the JSON's pairing names `03_CivilianCarLiberatedProvince`. |
| 3 | "Of the 86 … **32 carry `ambient`** and **14 carry both `ambient` and `liberated`** … 0 carry `liberated` without `ambient`, and 10 carry a faction `*_traffic` tag" (§5, line 134) | `TRAFFIC.json` `spawn.main.tag_pairs`: `ambient` 32, `ambient_and_liberated` 14, `liberated` 14, `liberated_without_ambient` 0, `records` 86, `traffic_tagged` 10; the full tag census (`spawn.tag_counts`) matches §2's list (`vehicle` 63, `ground` 59, `unarmed` 51, `unarmored` 47, `car` 27, `civilian` 25, `solar` 25, `modern` 26, `liberated` 14, `r03_outpost` 12). |
| 4 (bonus) | "`settings/spawn_budget_pools.bin` **does** contain the donor's chassis only in this table" and "`CVehicleRule` + `point.stunt`" (§2 line 37, §4 line 127) | Read both files: the budget-pools file lists `settings/spawn_vehicle_defs.bin` under `Ground Vehicles`; `locations/jc_prototype/mm320/train_test.blo` (2,292 B) and `locations/rom/wingsuit_course/wing20_logic.blo` (539,192 B) each contain `CVehicleRule` (1×), `point.stunt` (2×) and the donor leaf (1×). |

## Tamper test

Not re-run (journaled in the MODLOG G2-29 done section: `rules.selector_count` 41 → 40 in
`TRAFFIC.json` → `FAIL: TRAFFIC.json stale`, exit 1; a number in the md → `FAIL: md differs`, exit
1; restored → PASS). Re-running would mean writing `Research/`, which this review may not do. The
check path is consistent with the journal (JSON equality plus rendered-md comparison).

## Limits of this review

I verified the donor's record and the two level files from the archives, but I did not re-run the
11,751-file census (7.7 GB) or re-derive the 17-file list; those come from `TRAFFIC.json` and the
`--check` run. I did not test the native tag matcher — nothing here can, and the document says so.
The `settings/spawn_budget_pools.bin` association is verified only as a string grouping, not as a
runtime pool binding.
