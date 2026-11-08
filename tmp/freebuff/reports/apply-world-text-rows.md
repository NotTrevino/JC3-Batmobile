# Closing ledger rows T-WLD4, T-WLD6 and T-WLD11 (2026-11-06)

Offline only. No game launch, no install, **no `bm_rebel.py --write`** - the Rebel Drop tree was not
rebuilt. Everything below is either a file edit in `Working/Translation` / `Tools/scripts` or a
re-derived check.

**Result:** the three rows are closed in the ledger as `next` (carried by decoded evidence; the build
step that remains is named in the row), the ledger was regenerated through its own generators and
re-pinned, and every generator check passes:

| check | status |
|---|---|
| `python Tools/scripts/t15_world.py --check` | **PASS** - 19 rows, 8/8 WLD codes, ledger 19/19 |
| `python Tools/scripts/t_rows.py check` | **PASS** - 198 rows, 8 blocked, 50 next |
| `python Tools/scripts/t_blocked.py --check` | **PASS** - 12 blocked (8 ledger + 4 T6) of 185 |
| `python Tools/scripts/audit_compromises_t.py --check` | **PASS** - 72 audited, document re-derived identically |
| `python Tools/scripts/ledger_g3c.py --check` | **PASS** - 93 rows, 97 citations, 29 absent-claims |

Ledger `T_ROWS.jsonl` sha256 after the closure:
**`e2b7e3b14f53bd9c517e9af73f0aa6e4f2669eddbd45f7ea4fd9143f5e85e309`**
(was `8c0326a450ba4380...` in `BLOCKED_PROPOSALS`, `8996b60a5370d932...` in the first audit).

---

## 1. The string key - what T-WLD4 and T-WLD6 now say

Source: `tmp/freebuff/reports/name-string-lookup-key.md` (computed, proven on 5 shipped vehicles and
the donor's 3 leaves).

| quantity | value | derivation |
|---|---:|---|
| shipped leaf (bm-013, Q-1a) | `v0300_car_kensington_sportsmuscle_debug` | `Working/Translation/bm_leaf.py` (`LEAF = bm_leaf.NEW`); `Builds/bm-013/receipt.json` |
| name key | **1621485476** | `HashJenkins(leaf)`; re-derived in `t15_world.py:build_payload` (`hash_jenkins(st["new_leaf"].encode())`) |
| description key | **4081821928** | `HashJenkins(leaf + "_desc")`; `bm_rebel.py:226-227` |
| plan key that never ships | 443190071 | `HashJenkins("..._batmobile")` - 0/11 in vanilla and in the drop |
| plan desc that never ships | 1805638565 | `HashJenkins("..._batmobile_desc")` - 0/11 |
| donor name / blurb | 3535039305 / 2073308658 | `HashJenkins("..._civilian_01")` / `+ "_desc"`, 11/11 |

Proof of presence (`Builds/bm-013/drop/profile/online.stringlookup` vs vanilla):
pairs **14,712 -> 14,734** (+22 = 2 keys x 11 languages), added hashes exactly
`[1621485476, 4081821928]`, added text exactly `["BATMOBILE", "Arkham Knight's armoured Batmobile:
pursuit speed, a battle-mode turret, and armour that shrugs off small arms."]`, nothing else changed.

Row text now in the ledger (cells 5-6 and `why`):

- **T-WLD4** - was `blocked: "the new UIName hash 443190071 resolves in 0 of 11 ... no writer"`;
  now `next`, carrier: *"key carried: the plan hash 443190071 is `hash_jenkins("..._batmobile")` and
  resolves 0/11 - that leaf never ships (Q-1a). The leaf that ships is `..._debug`; its key is
  **1621485476** = `hash_jenkins(leaf)` and the pair is present **11/11** in
  `Builds/bm-013/drop/profile/online.stringlookup` ... the writer is `Tools/scripts/jc3strings_write`"*.
  Remaining: carry bm-013's drop into the RC + Q-1's runtime resolution.
- **T-WLD6** - now `next`, carrier: *"pair carried: `<leaf>_desc` = `hash_jenkins("..._debug_desc")`
  = **4081821928**, present **11/11** ... with the blurb in `Working/World/bm_rebel_text.json`"*.
- The `blocked` premise is gone from both rows, from `T15_WORLD.md`, `BLOCKED_PROPOSALS.md` (12 rows
  now, not 13; 8 ledger + 4 T6), `DECISIONS_NEEDED.md`, `BUILD_BATCHES.md` (`WLD-2` now
  `T-WLD4 (next); T-WLD5 (next); T-WLD6 (next)`), `COMPROMISES_T.md` (they moved from "blocked on a
  writer" to the carried list) and `LEDGER_G3C.md` (both rows now say "carried ... 1621485476 /
  4081821928").

## 2. The stunt-area coordinates - what T-WLD11 now says

Source: `tmp/freebuff/reports/stunt-areas-deform-points.md` §4 (P-1), measured on the shipped RC2
body `Builds/bm-RC2/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/batmobile/sportsmuscle_body_lod1.rbm`
(55,554 verts / 44,608 tris; bbox [-1.7508, 0.0867, -3.4218] .. [1.7464, 2.3627, 3.6055]).

Rule: row z from T-WLD11B's `target_rows` (donor host-band fraction -> target patch span), x = the
standing run containing x = 0 capped at 0.30 m, **y = top standing surface at (x,z) + the vertex's own
donor clearance**. Arithmetic shown in the report (§4.2); every vertex verified on RC2.

| area | vertex order x, y, z (m) |
|---|---|
| `front_area` / `front_signature_area` (same 6 points) | (-0.100, 1.9939, -1.390), (0.100, 1.9927, -1.390), (0.300, 1.4090, -2.309), (0.300, 1.1828, -2.916), (-0.300, 1.1827, -2.916), (-0.300, 1.4080, -2.309) |
| `main_area` (10 points) | (-0.160, 2.0866, -1.039), (0.140, 1.9766, 0.057), (-0.300, 2.1417, 1.294), (0.300, 2.1600, 2.400), (-0.300, 2.0886, 2.583), (0.300, 2.0884, 2.583), (0.300, 2.1583, 2.400), (-0.300, 2.1321, 1.294), (0.140, 1.9623, 0.057), (-0.160, 2.0866, -1.039) |

Measured: **22/22** vertices outside the shell, on a standing face (up-cos 0.749-0.994), at
0.036-0.105 m from the surface - inside the donor band 0.0388-0.1578 m. Stored areas sit 0.19-0.31 m
**below** the surface (unsigned 0.00-0.08 m); the bbox map floats 0.32-0.49 m. The 2-column ribbon
still chords the roof vents (1/40 and 16/80 interior samples inside, worst 0.110/0.162 m vs the donor's
0.075 m limit), so full width needs a third column: **3 new deform indices per hood area and 5 for the
roof (135+, none exist)** in `sportsmuscle_vehicle_deform.vmodc` + `sportsmuscle_stunt_areas.vmodc`.

Row T-WLD11 is now `next` (was `blocked`): the write is **22** `points[i].start_transform[12..14]` +
**22** `stunt_areas[k].vertices3D_local[3j..3j+2]` triples; triangles, `deform_points[]`,
`edges_valid[]` and `welding_info[]` unchanged. Revert path: the two module hashes are pinned in the
report (`6351f34a...` stunt areas, `d15f9df5...` deform), `Builds/_rollback/` holds the last rollback
tree, and `git checkout -- <path>` restores the tracked copies.

## 3. `Working/World/bm_rebel_text.json` - no edit, and why

The file holds only text:

```json
{"name": "BATMOBILE",
 "blurb": "Arkham Knight's armoured Batmobile: pursuit speed, a battle-mode turret, and armour that shrugs off small arms.",
 "_note": "B-13 entry text; English in all 11 languages. Edit, then re-run bm_rebel.py --write."}
```

It contains **no key**: `bm_rebel.py` derives both keys from `LEAF = bm_leaf.NEW` (`H = lambda s:
hash_jenkins(s.encode())`, lines 79 and 226-227). The key changed relative to the *row's premise*
(443190071 -> 1621485476) but **not relative to the file**, so the plan text stays as written. What
would change the file is translated text (gap: the pair is English in all 11 languages).

## 4. What `bm_rebel.py` would have to re-run (not run here)

Nothing was rebuilt. If the text or the leaf were re-pointed, the sequence is:

| # | command | what it rewrites |
|---:|---|---|
| 1 | `python Tools/scripts/bm_rebel.py --write` | `Builds/bm-013/drop/profile/item.onlinec` (one 128-byte record: `Name` = `UIName` = 1621485476, `UIDescription` = 4081821928, `UIImagePath` = leaf, `UIFlag` 7 / 1492769243, `UIDisplayOrder` 12), `profile/task.onlinec` (+1 `ItemReward` on starter task 1980624442), `settings/spawn_vehicle_defs.bin` (+1 record, 9 XML lines), `profile/online.stringlookup` (+22 pairs), the donor icon byte-copy - then `--check` |
| 2 | `python Tools/scripts/bm_leaf.py --check` | asserts the shipped leaf and the entity path still match |
| 3 | the B-18 packaging / RC drop merge | copies the five drop files into the RC tree and repoints the 11 referrers |
| 4 | the V-xx gates + Q-1 | item resolves, drop list reads "Batmobile", spawn works |

`bm_rebel.py` itself would not change: its `LEAF`, `H(LEAF)` and `H(LEAF + "_desc")` already compute
1621485476 / 4081821928, and `--check` (run in the earlier key report) re-derives 22 added pairs.

## 5. What was edited (file-level, for revert)

| file | change |
|---|---|
| `Tools/scripts/t15_world.py` | rows `T-WLD4`, `T-WLD6`, `T-WLD11` carrier/dispo/why text (the T-20 generator) |
| `Tools/scripts/t_rows.py` | `DISPO["T-WLD4"/"T-WLD6"/"T-WLD11"]` -> `next` + new reasons |
| `Tools/scripts/t_blocked.py` | removed the three rows from `WAITS` (they are no longer blocked) |
| `Tools/scripts/audit_compromises_t.py` | `T-WLD11` compromise text; `T-WLD4/6` moved to the "nothing lost" list; the "Stunt areas" reopened note |
| `Tools/scripts/ledger_g3c.py` | the three `R(...)` entries' `ledger` / `note` / `supplier` text |
| `Working/Translation/T15_WORLD.md` + `t15_world.json` | regenerated by `t15_world.py --write` |
| `Working/Translation/T_ROWS.jsonl` | regenerated by `t_rows.py build` (3 rows closed; 198 rows) |
| `Working/Translation/BLOCKED_PROPOSALS.{md,json}` | regenerated (`t_blocked.py --write`): 12 blocked, new ledger pin |
| `Working/Translation/COMPROMISES_T.{md,json}` | regenerated (`audit_compromises_t.py --write`) |
| `Working/Translation/LEDGER_G3C.{md,json}` | regenerated (`ledger_g3c.py --write`) |
| `Working/Translation/DECISIONS_NEEDED.md` | three rows removed from the needs table; closure note + new pin added |
| `Working/Translation/BUILD_BATCHES.md` | `WLD-2` and `WLD-4` now list the three rows as `next` |

Revert: `git checkout --` the twelve paths above (all tracked), or restore the pre-closure
`T_ROWS.jsonl` and re-run `t_rows.py build`; the generators reproduce the old text from
`git show HEAD:Tools/scripts/...`.

## 6. Re-pin: what is new, and what is deliberately historical

- **New pin**: `e2b7e3b14f53bd9c517e9af73f0aa6e4f2669eddbd45f7ea4fd9143f5e85e309` (198 rows).
  It is recorded in `BLOCKED_PROPOSALS.md`/`.json` (regenerated) and in the closure note in
  `DECISIONS_NEEDED.md`. `t_blocked.py --check` asserts it.
- **Deliberately unchanged**: the first-audit pages still quote `8996b60a5370d932...` -
  `LEDGER_AUDIT.md`, `LEDGER_AUDIT2.md`, `LEDGER_PROVENANCE.md`, `ROW_EVIDENCE_AUDIT{,2,3}.md`,
  `MISSING_ROWS.md`, `VALUE_NOT_FOUND_SIX.md`, `AU_BLOCKED_RETEST.md`, `COLLISION_ROWS_CORRECTED.json`.
  Those pages record the ledger as it was at their audit time; rewriting their hashes would falsify
  the record. Their tools hard-code the old prefix (`t_au_retest.py:34`, `t_row_evidence2.py:65`,
  `t_row_evidence3.py:89`, `t_vnf_six.py:37`), so **those four checks now fail by design** - they
  assert "the ledger is unchanged", which is exactly what this authorised edit changed. They were not
  run here and are not claimed green.
- `git status` shows `T_ROWS.jsonl` modified (expected) together with the regeneration outputs.
