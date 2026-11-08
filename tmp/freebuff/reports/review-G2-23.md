# Review — G2-23 · Nitro FX and audio carriers

Reviewer: independent (did not write the card). Read-only pass: `GRAB_BACKLOG.md`, `MODLOG.md`,
`Research/` and `Tools/` were only read; nothing outside this file was written, no game launched,
no git.

Scope checked: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G2-23 card (§7, line 714) and its §12 row
(line 1306); `MODLOG.md` §"G2-23 · Nitro FX and audio carriers — done" (line 11800);
`Research/JC3Grab/USAGES.md` §6 (lines 546–621) + §7–§8, `Research/JC3Grab/USAGES.json`
`nitro` block, `Tools/scripts/jc3usage.py` (1,150 lines: `arcade_scan` 344, `nitro_chain` 372,
report 874–940, `assertions()` 1003), `Research/JC3Grab/README.md` line 567.

## VERDICT

**Minor issues.**

The card is answered with data, and the data holds up under an independent recount: the sound
GUID is on **202 objects / 172 vehicles** (I re-counted all 232 `.epe` graphs and got 202/172 with
the same name split), the object's `Effect` hash `3518298851` is on **28 objects / 17 vehicles**
(reproduced exactly), the donor `arcade.nitro_boost` values are `torque 2 / grip 2 / push_force
15000 / boost_blend_time 0.2 / extra_top_speed 40` with `_upgraded` at 20000/80 (re-read straight
from the donor entity cache, not from the JSON), the five `arcade.*` blocks really do sit on 145 of
232, `EngineTurboJump` really is 11, and the "9 `*nitrous*.effc`" count is exactly 9 when counted
from `FX_TABLE.jsonl`. R5 is handled well where it matters most: the sample step is explicitly
"by name", the object's own effect hash is marked UNKNOWN rather than mapped onto
`dynamic_nitrous`, and the "which control fires it" edge is declared unknown.

What keeps it off "sound": the §6 table is titled and framed as *the chain*, but its first edge
(`arcade.nitro_boost` → `EngineNitro`) is name adjacency and no file joins the two — the doc says
so only in §7, one section later. The input row is also the one chain step with no entry in
`assertions()`, so `--check` cannot notice if those five values move. Two smaller rendering
defects: the carrier-name list is truncated at six names (194 of 202 objects) with no ellipsis, and
the "rest are turbo-jump whooshes and the tank's turbowhistle" list contains 165, which the same
sentence calls a nitrous clip.

## Check output (verbatim)

Command run from `E:/Modding/JC3-Batmobile`:

```
$ python Tools/scripts/jc3usage.py --check
PASS: 6045 modules in 232 caches, 225 EffectAttachments on 224 vehicles, 12 named usages (346 rows, 885 effect links re-decoded), ExtendedEffectUsages 0 usages, EngineNitro -> EngineNitro/dynamic_nitrous, 155 .epe Usage values / 12576 objects, 0 .effc refs in graphs, FX rows 57187
```

Exit status `0`. The summary line matches the one pasted in `MODLOG.md:11829` word for word; the
MODLOG wraps it over three lines, the terminal emits one.

Out paths — all present:

| path | state |
|---|---|
| `Research/JC3Grab/USAGES.md` §6 "The nitro chain: input -> effect -> sound event -> sample (G2-23)" (card's declared Out) | present, line 546; JSON/md regenerated together |
| `Research/JC3Grab/USAGES.json` `nitro` block | present: `usage`, `sound`, `effect`, `arcade`, `samples` |
| `Tools/scripts/jc3usage.py` G2-23 pass | present, `--write`/`--check`, `assertions()` has 10 nitro rows (lines 1022–1031) |
| `Research/JC3Grab/README.md` "The nitro chain (G2-23, `USAGES.md` §6)" | present, line 567, plus the Files row at line 936 |
| `GRAB_BACKLOG.md` §12 row `G2-23 \| done \| …` | present, line 1306 |
| `MODLOG.md` §"G2-23 … — done" | present, line 11800 |

## Issues

### 1. (R5/R4) The "chain" has one edge that no file carries, and the doc admits it only in §7 — `Research/JC3Grab/USAGES.md:546`, `:550`, `:561`; `MODLOG.md:11805`

§6 opens "The card's chain, **one step per row**; the last column names the file the value was read
from", and the table walks input → usage → effect → sound → ordinal → samples as one sequence. The
input row's file is the donor `custom_land_global.vmodc` and the usage row's is the donor `.epe`,
but no decoded file says that `arcade.nitro_boost` is what turns the `EngineNitro` usage on — the
join is the shared word "nitro". §7 bullet 2 says exactly this ("**what drives each usage.**
Which variable or event turns a usage on is code", line 611) and line 561's "**Which control fires
any of them is in no file here**" covers the *button*, not the block→usage edge. So the document
contains the caveat but places it where a reader following §6 will not apply it to the chain.
`MODLOG.md:11805` ("**Result - the chain, file by file**") is the stronger form and is the version
a later card will quote. Recommend one sentence in §6: "the input row and the usage row are each
data, but the *edge* between them is name inference — §7". Everything from **usage → effect →
event → ordinal → sample** is genuinely file-backed (the donor object carries `Usage` `EngineNitro`
and `Sound` on the same node, the module binds that usage to `dynamic_nitrous`, the GUID is an
`EVTS` entry, the names select three FSB5 samples).

### 2. (R11) The input step is the only chain step with no assertion — `Tools/scripts/jc3usage.py:1022`–`1031`, `:1003`–`:1031`

`assertions()` pins 232 caches, 6045 modules, `EVTS` 249, 202/172 carriers, 28 effect carriers,
`[56, 150, 355]`, 145 `nitro_boost` vehicles — but **none of the six boost values**. The md prints
them from `USAGES.json` (line 552, `report()` ~line 882), so they are derived, not typed; the gap is
that they are not *pinned*: `--check` re-derives md+json from the raw data and compares them to
each other, so a changed donor module would silently change the document and still print PASS.The nine other nitro facts would fail. Add one row (`torque 2 / grip 2 / push 15000 / blend 0.2 /
+40`) as an assertion, or take the value out of the `arcade` block rather than a constant list.

### 3. (R11) "five `arcade.*` blocks" is true by construction of the filter, not by measurement — `Tools/scripts/jc3usage.py:346`–`357`, `Research/JC3Grab/USAGES.md:561`

`arcade_scan()` only counts block names in the `ARCADE_BLOCKS` constant and silently drops any
other `arcade.*` path; the prose "carries five `arcade.*` blocks" is a literal in `report()`. I
counted independently: the fleet has exactly those five blocks (`heat_boost` 725 rows/145 files,
`nitro_boost` 725/145, `nitro_boost_upgraded` 725/145, `turbo_jump` 870/145, `turbo_jump_upgraded`
870/145), so the sentence is correct today — but a sixth block would be invisible to both the doc
and the check. The same applies to "torque x2, grip x2, a 15,000 N push, 0.2 s blend, +40 km/h"
(line 563, typed even though the table row above prints the same numbers), "`EngineTurboJump` usage (11 vehicles)" (line 566, 11 verified), "`EngineNitro` itself on 4 planes" (line 574, 4 verified), and "the 9
`*nitrous*.effc` files" (9 verified from `FX_TABLE.jsonl`). All correct; none re-derivable.

### 4. (data presentation) The carrier name list does not add up to the total it is attached to — `Research/JC3Grab/USAGES.md:580`–`581`

"**202 objects on 172 of the 232 decoded vehicles**, and every carrier is a nitrous exhaust
object - `exhaust_upgrade_nitrous` 154, `dynamic_exhaust_upgrade_nitrous` 14,
`exhaust_upgrade_nitrous_r` 13, `exhaust_left_upgrade_nitrous` 5, `exhaust_right_upgrade_nitrous`
5, `exhaust_upgrade_nitrous_b` 3, classes `SAttachedEffect` 188, `SDynamicAttachedEffect` 14".
The names sum to **194**, not 202. The class split does sum correctly (188+14 = 202), and the six
names are `most_common(6)` in the JSON (`EJECT`-style truncation, `jc3usage.py` builds
`dict(carriers["names"].most_common(6))`). The four missing names, which I re-counted: 
`exhaust_upgrade_nitrous_right` 2, `exhaust_upgrade_nitrous_left` 2, `exhaust_upgrade_nitrous2` 2,
`exhaust_upgrade_nitrous_l` 2. The claim "every carrier is a nitrous exhaust object" survives
(all ten names are nitrous), but a reader who sums the list gets a smaller number than the stated
total with no "…" to explain it. Same six-name list in `MODLOG.md:11818`.

### 5. (template bug) 165 is listed as "the rest" after being singled out — `Research/JC3Grab/USAGES.md:592`–`593`

"only 165 is a fourth nitrous clip (a flame loop test-060 left alone) - the rest are turbo-jump
whooshes and the tank's turbowhistle: 72 …, 90 …, **165** `jc3_veh_land_premium_nitro_jet_flame_loop`,
270 …, 448 …, 584 …, 605 …". The renderer prints the whole `nitro_like` set minus `by_name`, which
includes 165, under a sentence that has just classified 165 as *not* part of the rest. The
underlying data is right (`nitro_like` = 56, 72, 90, 150, 165, 270, 355, 448, 584, 605; `by_name` =
56, 150, 355 — I confirmed both from `USAGES.json` and re-counted the names from `FX_TABLE.jsonl`);
only the sentence is wrong.

### 6. (R4 phrasing) "The input half is module data, not code." — `Research/JC3Grab/USAGES.md:561`

The parameters are module data; whether the block is applied is code, as the next sentence says
("which control fires any of them is in no file here"). The heading overstates in the same
direction as issue 1. Cheap fix: "the boost parameters are module data".

### Note (not a defect): what `--check` proves for this card's Done clause

Card Done: "the full chain nitro input → effect → sound event is written down". §6 does write all
five stages down (input, usage, effect in both hash spaces, sound GUID → `EVTS` ordinal → sample
names), and `--check` verifies 29 re-derived assertions plus byte-equality of both files. What it
does **not** verify is that the chain is *causal* — no assertion can, because the missing edge (no
file joins the boost block to the usage) is the very thing issue 1 is about. The Done clause is
therefore met in the weaker, honest sense ("written down, with the unknown edge named"), which is
what the card asks for, but a reviewer should not read PASS as "chain proven". This is the same
shape as the other G2 readers, so I record it rather than fault it.

## Spot-checks

Each number was re-derived from the raw inputs by an independent script, not by re-reading
`USAGES.json`.

| # | value in `USAGES.md` §6 | where verified |
|---|---|---|
| 1 | sound GUID `f74ea43b-a8ac-4548-ad27-b92fd40a516d` "carried by **202 objects on 172 of the 232** decoded vehicles", names `exhaust_upgrade_nitrous` 154 / `dynamic_exhaust_upgrade_nitrous` 14 / `…_r` 13 / `…_left` 5 / `…_right` 5 / `…_b` 3 (lines 580–581) | Walked all 232 `E:/Modding/_JC3grab/detail/*.ee.json` and matched the GUID hex-normalised: **202 objects, 172 files**, names 154/14/13/5/5/3 plus four more (2/2/2/2) = 202; classes `SAttachedEffect` 188 + `SDynamicAttachedEffect` 14. Matches `USAGES.json` `nitro.sound.carriers`. |
| 2 | object `Effect` 3518298851 (0xD1B4FAE3) "carried by **28 objects on 17 vehicles**", names 12/6/5/5, "in **none** of the `all_effects[]`" (lines 569–577) | Same walk with the signed value masked to 32 bits (`-776668445 & 0xFFFFFFFF`): **28 objects, 17 files**, `exhaust_upgrade_nitrous` 12, `…nitrous2` 6, `exhaust_left_upgrade_nitrous` 5, `exhaust_right_upgrade_nitrous` 5. `USAGES.json` `nitro.effect.named_in_module_space` = `false`. |
| 3 | input row: `arcade.nitro_boost` torque x2, grip x2, `push_force` 15000, `boost_blend_time` 0.2 s, `extra_top_speed` +40 km/h; `_upgraded` push 20000, +80 km/h; five blocks on **145 of 232** (lines 552, 562) | Read the donor's module rows directly from `…/_JC3grab/entities/v0300_…_civilian_01.ee.json`: `arcade.nitro_boost.{torque_multiplier=2, grip_multiplier=2, push_force=15000, boost_blend_time=0.200000003, extra_top_speed=40}`, `nitro_boost_upgraded.{push_force=20000, extra_top_speed=80}`; `heat_boost.push_force = 0`, `+80`. Fleet sweep: all five blocks 145 files, `turbo_jump`/`_upgraded` 870 rows each. |
| 4 (bonus) | "`EngineEVents` 249 / 195 B" — i.e. `vehicles` `EVTS` ordinal 249, 195 B (line 558); "the 9 `*nitrous*.effc`" (line 575); "`EngineTurboJump` usage (11 vehicles)" (line 566) | 249/195 is produced by `jc3audio.fev_events` inside the run (same reader, so not independent) and is recorded identically in `Research/JC3Grab/JC3_AUDIO.md:52` (`… | vehicles/249 | exhaust_upgrade_nitrous (S)`) — cross-document agreement, two documents, one reader. The `.effc` count I counted independently from `FX_TABLE.jsonl`: exactly **9** distinct `*nitrous*.effc` paths. `EngineTurboJump` = 11 vehicles in `USAGES.json` (`usages` row, hash 3877802965). |

## Tamper test

Not re-run (journaled at `MODLOG.md:11836`–`11838`: `EVTS` ordinal 249 → 250 in the md → `FAIL: md
differs`, exit 1, reverted, PASS). Re-running it would mean writing `Research/`, which this review
may not do. The script's check path is consistent with what was journaled: it compares
`render_md(d)` against the file and exits 1 with a unified diff.

## Limits of this review

I did not re-implement the FEV/FSB5 reader, so the `EVTS` ordinal 249 / 195 B and the 649-sample
name table are attested by the run plus `JC3_AUDIO.md`, not by a second parser. The
`EngineNitro` → `dynamic_nitrous` binding on the fleet's 14 vehicles is a module-space fact owned by
G2-22 and was reviewed there; I only confirmed the donor side (usage + sound on the same object)
and that the object's own hash is absent from the module space.
