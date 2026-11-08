# Independent review — G2-22 · Effect usage vocabulary

Reviewer: independent read-only pass (did not write the card). Date 2026-10-28.
Card: `GRAB_BACKLOG.md:707` (`G2-22 · Effect usage vocabulary (old T-FX3 route, jc3usage.py)`, S,
deps P0-1, serves FX-1). Tracker row: `GRAB_BACKLOG.md:1305` (`G2-22 | done`).
Journal: `MODLOG.md:10019` (intended change), `MODLOG.md:10547` (done).
Outputs reviewed: `Research/JC3Grab/USAGES.md` (660 lines, 80,039 B), `Research/JC3Grab/USAGES.json`
(693,322 B), `Tools/scripts/jc3usage.py` (59,074 B).

## VERDICT: minor issues

The card is done and the numbers are unusually well founded: I re-derived the headline counts from
the raw graphs and they match to the digit, the `--check` compares both artefacts byte for byte, and
the two `.epe` caveats the card's assumptions got wrong are recorded honestly. One sentence in the
doc, however, claims a negative that its own tables contradict (C-issue 1), and the MODLOG's line
count for the delivered doc is stale (issue 2). Neither changes the answer the card was asked for.

## Check output (verbatim)

Command: `python Tools/scripts/jc3usage.py --check`

```
PASS: 6045 modules in 232 caches, 225 EffectAttachments on 224 vehicles, 12 named usages (346 rows, 885 effect links re-decoded), ExtendedEffectUsages 0 usages, EngineNitro -> EngineNitro/dynamic_nitrous, 155 .epe Usage values / 12576 objects, 0 .effc refs in graphs, FX rows 57187
```

Exit code 0. All three Out paths exist. The card's Done — "the list of usages; a named candidate for
'flame during nitro' or a proof none exists" — is what the check verifies: §1-2 print the 12 usages
with hashes and carriers, §5 names `EngineNitro` → `dynamic_nitrous`, and the check asserts both
`EngineNitro` links `dynamic_nitrous` and the count of flame-worded usage names. The Done criterion
and the check match.

## Issues

1. **`USAGES.md:422` states a negative its own table refutes.** The sentence reads
   *"Flame words in usage names: **none** - no usage anywhere in the fleet vocabulary is named
   afterburner, boost, flame or fire."* Three problems:
   - The document's own §3 table lists `.epe` usage values whose name **is** a flame/nitro word:
     `engine_burn_top` (line 222), `engine_burn_tail` (235), `burn_roof` (272, 138 objects),
     `burn_base_bottom` (293), `engine_burn` (308, 33 objects), `dynamic_nitrous` — all with
     `name_source: module effect name`. The json agrees (`epe.values` → 13 rows matching
     `burn|nitro|flame|boost`). A reader of §3 and §5 gets opposite answers.
   - The check that backs the sentence (`jc3usage.py:536`) scans **only the 12 module usage names**
     (`usage_names.values()`), not the 155 `.epe` values — so "anywhere in the fleet vocabulary" is
     wider than what was measured.
   - The regex is `afterburner|afterburn|boost|flame` (`jc3usage.py:63`) — it does not contain
     **"fire"**, so the word the sentence adds was never tested (it happens to be absent, but the
     claim is not the one the assertion makes; the validation row at `USAGES.md:646` is honest and
     says "afterburner/boost/flame").
   Fix: "the 12 module usage names contain no flame word; 13 `.epe` usage values are *named* after
   their effect (`burn_*`, `dynamic_nitrous`), which is why the flame is a property of the effect
   name, not of the usage vocabulary." Keep "fire" out or add it to the regex.

2. **MODLOG's delivered-size figure is stale.** The done section says "`USAGES.md` is **588** lines as
   delivered (`USAGES.json` 687,497 B)" (and the body above it says 585). On disk the doc is **660**
   lines and the json **693,322 B** — the file was evidently regenerated after that addendum. R11
   (counts generated, never typed) applies to the journal's own numbers; the check does not guard
   them. Cosmetic, but it is exactly the kind of number a later reader trusts.

3. **Minor scope note, already declared.** The README section and `Files` row were added although the
   intended-change table did not list `Research/JC3Grab/README.md`; the MODLOG says so itself under
   "Scope note (R14 honesty)". Registration matches every other G2 table, so this is disclosure, not
   a defect.

## Spot-checks

| value in the doc | where verified |
|---|---|
| 12 named usages / 346 `usage_effects[]` rows / 885 effect links / 0 cache-vs-redecode mismatches (`USAGES.md` §1-2, validation table) | `USAGES.json`: `usages` has 12 entries with carriers summing to **346** (145+69+33+23+23+18+11+3+3+2+2+14); `usage_effects` = `cache_rows 346`, `redecoded_rows 346`, `cache_nested_indices 885`, `redecoded_nested_indices 885`, `cache_vs_redecode_mismatches 0` |
| `EngineNitro` (4197885156) on 18 modules → `dynamic_nitrous` 14 vehicles + `EngineNitro` 4; donor attaches `exhaust_upgrade_nitrous`/`…nitrous2` (`USAGES.md` §5) | `USAGES.json` `usages[hash 4197885156]`: 18 vehicles, effects `EngineNitro` (4) and `dynamic_nitrous` (14); `flame.donor_usage_map` entry for that usage = `{name: EngineNitro, objects: [exhaust_upgrade_nitrous, exhaust_upgrade_nitrous2]}` (51 donor entries, 29 unnamed, as the doc says) |
| **307** objects in **202** of 232 graphs carry that `Usage`, `SAttachedEffect` 281 / `SDynamicAttachedEffect` 26 (`USAGES.md` §5, MODLOG) | independently recounted from `E:/Modding/_JC3grab/detail/*.json` (`epe.objects[].values.Usage`, signed→unsigned): **307 objects / 202 graphs / 281 / 26** — exact |
| 12,576 `.epe` objects carry a `Usage`; **155** distinct values; 849,942 `.epe` strings; 0 `.effc` references (`USAGES.md` validation) | same independent pass: **12,576** objects, **155** distinct values over 232 graphs; `USAGES.json` `epe.string_values` 849,942 and `epe.effect_file_references` 0 |
| "9 `*nitrous*.effc` paths across **275** containers" (`USAGES.md` §5) | `Research/JC3Grab/FX_TABLE.jsonl`: 275 rows whose path contains `nitrous`, **9** distinct paths (`car_cycle_base_nitrous`, `…_nitrous_c`, `…_dual_nitrous`, `…_v0602`, `helicopter_base_nitrous`, `minetruck_…`, `monstertruck_base_nitrous`, `boat_splash_nitrous`, `jetski_splash_nitrous`), 275 distinct containers |
| Usage 456657646 = 121 objects named `flame`, name UNKNOWN (`USAGES.md:241`, `:491`) | `USAGES.json` `epe.values[usage 456657646]`: 121 objects, `object_names {"flame": 121}`, `SDynamicAttachedEffect`, `name: null` — the table is faithful; note it is the object that is named `flame`, not the usage, which is why issue 1 needs the precise wording |

## Rules

R4: every number in the doc is printed from `build()`; the one place provenance is overstated is the
"none … anywhere" sentence (issue 1). R5: the doc is careful where it counts — `EngineNitro` is called
a *named candidate*, and "whether the engine draws a flame when nitro fires is code, not data — a Q-1
probe, never claimed here" (§5). R11: the delivered artefact is generated, but the MODLOG's line and
byte counts are typed and stale (issue 2).

## Limits of this review

Read-only: I ran `--check`, re-counted the `.epe` usage values and the `FX_TABLE` nitrous rows
independently, and read the script's assertions; I did not re-decode the 232 `_effect_attachments.vmodc`
files myself (the check's own cache-vs-redecode comparison covers that), did not re-run the two tamper
tests recorded at `MODLOG.md:10616-10620`, and did not attempt to resolve the 85 unnamed `Usage` values.
No archive was opened, no game launched, nothing committed.
