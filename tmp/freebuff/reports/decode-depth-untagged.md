STATUS: done — with the brief's premise corrected rather than assumed. **All 30 sampled objects agree with `REMAINDER.md`** on class, object name, size, payload shape and verdict, recomputed from the package bytes (`mismatches 0`). But `REMAINDER.md` **has no handling/upright/damage/material/other classification** to audit: its per-object fields are `package | export | class | object | size | payload | verdict`, and the verdicts are byte accounting. The five words come from `RESET_FINDINGS.md:85` (R-6's topic list), not from a per-object field. And the property-value requirement cannot be met by any of the 925: they are *untagged* by definition (`tag_count == 0` in `objects.jsonl`), so not one of them carries a named property. The audit therefore checks the classification that exists, records the property evidence per object, and maps the four R-6 topics across the whole population by class.

## Result

| question | answer |
|---|---|
| 925 untagged objects present | yes, `tag_count == 0` for 925 of `objects.jsonl` |
| sample | 30, evenly spaced by list position: `[0, 32, 64, 96, 127, 159, 191, 223, 255, 287, 319, 350, 382, 414, 446, 478, 510, 542, 574, 605, 637, 669, 701, 733, 765, 797, 828, 860, 892, 924]` |
| sampled rows found in `REMAINDER.md` | 30/30 |
| misclassified objects | **0** — class, name, size, payload shape and verdict re-derived from the package all agree |
| sampled objects with a property value | **0 of 30** (untagged by definition) |
| objects in the four R-6 topic classes | **20 of 925**: `RB_StayUprightSetup` 4 + `RB_ConstraintInstance` 4 (upright 8), `RB_BodyInstance` 4 (handling), `RVisualDamageComponent` 4 (damage), `MaterialInstanceConstant` 4 (material) |
| of those, carrying a property value | **0** — every one is `tag_count == 0`; the topic can be *class*-supported, never *property*-supported |

The sample's verdict spread: 23 `no properties to decode`, 6 `not in the drivable vehicle's package`, 1 `reachable from the drivable vehicle chain`. The even sample happened to contain **none** of the four topic classes, so §4b of the audit answers the topic question on the full 925 instead — stated there as population coverage, not passed off as the sample.

## Misclassified objects

**None.** Every sampled row was re-derived from `E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\<package>.upk`: export class and name from the export record, payload size from the payload length, shape from `grab_remainder.untagged_shape` (2-byte `0000` stub vs no 2+ tag stream closing at the payload end), and the verdict by re-running the same reachability rule over all 20k objects. One apparent mismatch during development was my own comparison artifact (`None` string vs Python `None`), fixed in the tool — it was not a `REMAINDER.md` error, and I did not record it as one.

## Files written

- `Research/BatmobileGrab/REMAINDER_SAMPLE_AUDIT.md` — the requested page: method, the 30-row table with recomputed payload and published verdict, the mismatch section, the topic census, consequences and UNKNOWNs.
- `Tools/scripts/remainder_sample_audit.py` — new tool, `--write` / `--check`; reads the cooked packages, `objects.jsonl` and `REMAINDER.md`, writes only the md.
- `tmp/freebuff/reports/decode-depth-untagged.md` — this report.
- `tmp/freebuff/scratch/v06rc2/r6_write.log`, `r6_check.log` — the captured output below.

Nothing was launched, installed or written outside those files; the game was not touched (test ban).

## Commands and verbatim output

```
python Tools/scripts/remainder_sample_audit.py --write
```

```
untagged 925 sampled 30 md_rows 925
mismatches 0
wrote E:\Modding\JustCause3\JC3-Batmobile\Research\BatmobileGrab\REMAINDER_SAMPLE_AUDIT.md (10028 bytes)
write exit=0
```

```
python Tools/scripts/remainder_sample_audit.py --check
```

```
PASS 925 untagged objects in objects.jsonl  925
PASS sample is 30 objects  30
PASS every sampled object has a REMAINDER.md row  30/30
PASS sample rows agree with the package bytes  0 mismatches
PASS every sampled package is on disk
PASS the four R-6 topic classes hold 20 of the 925  20
PASS class census covers all 925
PASS no sampled untagged object carries a property value (the documented limit)
PASS md lists every sampled package+export
PASS md marks every sample row as agrees or MISMATCH
PASS md states the taxonomy finding
check PASS  (0 failing assertion(s))
check exit=0
```

## What this means for R-6

1. **`REMAINDER.md` is not misclassifying objects; it is answering a different question.** Its rows are byte-accounted payload facts, and the sample confirms them. R-6's "(handling, upright, visual damage, materials)" is a *topic* list from `RESET_FINDINGS.md:85`, so treating it as a per-object field reads a classification into the file that is not there.
2. **A property-backed topic classification is impossible for this population.** `tag_count == 0` means no property tag stream exists at all, so any handling/upright/damage/material claim for these 925 would rest on the class or the object name — exactly what the brief forbids. The 20 class-supported objects (§4b) are the only candidates, and even they carry no value.
3. **What would make the classification property-backed:** decode the native payloads of those 20 (the `NATIVE.md` / `BMSDK_OFFSETS` layout work), or use the runtime oracle G3-07 to observe which of them the vehicle actually uses. Neither is done here and neither is assumed.

## UNKNOWNs

1. **Which artefact was meant to hold the five-way classification.** Searched `REMAINDER.md` (no such field), `REMAINDER.json` (`untagged` is a 6-key summary block, not per-object records) and `GAPS.md` (counts only). It would be a new field on the 925 rows — G3-06 work not yet done.
2. **Whether any of the 925 is functionally handling/upright/damage/material in game.** For the 20 class-supported ones the *class* says so, but the value/role is UNKNOWN; the other 905 have no decoded evidence of a topic. Would be found with G3-07 (runtime) or the native layout decode.
3. **What the 17 reachable objects' payloads mean.** Reachability is recomputed (1 in the sample, reported as such); their contents are not interpreted here — that was G3-06's own scope, not this audit's.
4. **Whether the 768 `empty_stub` objects are genuinely propertyless in the shipped asset rather than truncated by the grab.** UNKNOWN here: the audit re-reads the same cooked bytes, so it can confirm the stub, not the asset's intent.

## Limitations

- The sample is even by list position, not stratified by class; that is why §4b covers the four topic classes across all 925 instead of claiming the sample covered them.
- The audit is read-only evidence about files; it says nothing about behaviour, which stays with the test ban and G3-07.
