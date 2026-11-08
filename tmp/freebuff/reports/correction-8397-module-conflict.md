# Correction 8397 - the two cards that wrote one module (2026-11-07)

Review 8399 confirmed the conflict: D-08 and D-10 both wrote
`editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_custom_land_global.vmodc`,
and the RC kept only D-10's copy, so `front_wheels_damage.skew_health` and
`rear_wheels_damage.skew_health` (both 200 -> 400) were absent from `Builds/bm-RC4` and listed as
`not_carried`.

**Resolution: option (a) - one merged module, both sets carried and read back. Option (b) was not
needed: the two writes are not mutually exclusive.** Nothing in the packed `.ee` was hand-edited;
the module is produced by the build and proved from the packed bytes.

## 1. The measurement that decides (a) vs (b)

`t5_apply.decode` + `paths` over the two branch copies, before any change:

| | D-08 (`bm-RC4-damage-collision`) | D-10 (`bm-RC4-handling`) |
|---|---|---|
| size | 3,399 B | 3,399 B |
| members | 61 | 61 |
| members unique to this branch | 0 | 0 |

They differ in **exactly 7 members** - and nothing else:

| member | D-08 | D-10 |
|---|---|---|
| `front_wheels_damage.skew_health` | **400** | 200 |
| `rear_wheels_damage.skew_health` | **400** | 200 |
| `drift.min_speed_to_drift_kmph` | 10 | **0** |
| `drift.steering_sensitivity` | 4 | **2** |
| `arcade.nitro_boost.torque_multiplier` | 2 | **6.30000019** |
| `arcade.heat_boost.grip_multiplier` | 4.26000023 | **1.5** |
| `arcade.nitro_boost_upgraded.extra_top_speed` | 100.919998 | **80** |

Same layout, member-disjoint edits: a binary merge is not only possible, it is two fixed-width
writes. So there is no exclusivity to prove.

Also measured, and worth stating because the old receipt text said "18 handling writes": only **5**
of D-10's writes are in this module (the other 13 are in the other four handling modules). The
policy that dropped D-08 was therefore justified by 18-vs-2 across all modules, but the overlap in
this file was 5-vs-2.

## 2. What the build now does

`Tools/scripts/bm_rc4.py`:

* `MERGE_EDITS` - the two D-08 rows (`T-14 ARM-4`, `front/rear_wheels_damage.skew_health`
  200 -> 400) and `MODULE_MERGES` - the module, its two branches, its base (`bm-RC4-handling`) and
  the reason. `CONFLICTS` is now empty: nothing is left to choose.
* build step 2b copies D-10's module into the stage and calls `t5_apply.apply_file(dst, MERGE_EDITS,
  False)`. That writer resolves each member's `offset-in-file` anchor, **asserts the old value is
  200 before writing**, writes 400 at the same width, then re-decodes and refuses to continue if any
  untouched member moved. So D-10's five values are proved unchanged by the same call.
* the receipt gets `module_merges`, one record with: the two source sha256s, the base, the two edits
  (`old`/`new`), the merged sha256 and byte size, and `read_back`.
* a new `read_module()` reads the members **from the packed `.ee` through the `.toc`** (record ->
  (offset, size) into the decompressed SARC stream -> slice -> ConvertAdf -> member compare), the
  same path `b10_handling.py` uses. `build()` runs it and stores the result;
  `check()` runs it again independently.
* `receipt.not_done` no longer carries "the D-08 wheel skew_health rows are not carried".
* `check()` now requires `conflicts == []` and one `module_merges` record whose packed read-back is
  complete, plus the tree sha256 equal to the recorded merged sha256.

## 3. The result

`python Tools/scripts/bm_rc4.py --write` then `--check`, both exit 0:

```
PASS 0 unresolved module conflict(s); 1 overlapping module(s) carried by merge
PASS module merge read back from the packed .toc: 7 member(s) = both branches' sets
     (D-08 skew 400 + D-10's 5), merged sha256 d67f0fe92536a44a...
PASS: bm-RC4 0 failure(s), 9 drop files, 696 tree files, .toc 714 records, model 4791.3 KB
```

`receipt.json` now parses and records:

```
conflicts      []
module_merges  base bm-RC4-handling, branches [bm-RC4-damage-collision, bm-RC4-handling]
               merged_sha256 d67f0fe92536a44a975bc3dd3283efb27c8bc95f998cd1650474db9f5f82fb60
               bytes 3399
edits          front_wheels_damage.skew_health 200 -> 400
               rear_wheels_damage.skew_health 200 -> 400
read_back      ok, 7 checked:
               front_wheels_damage.skew_health 400
               rear_wheels_damage.skew_health 400
               drift.min_speed_to_drift_kmph 0
               drift.steering_sensitivity 2
               arcade.nitro_boost.torque_multiplier 6.30000019
               arcade.heat_boost.grip_multiplier 1.5
               arcade.nitro_boost_upgraded.extra_top_speed 80
not_done       no skew_health entry
```

The `6.30000019` is the float32 representation of 6.3, which is what the module holds; the
comparison is tolerance-based (1e-4 relative), so the value is the target, not a near miss.

`tmp/freebuff/reports/build-d13-release-candidate-4.md` §1, its summary line and its not-done list
now describe the merge instead of the drop.

## 4. Checks run (all exit 0)

```
python Tools/scripts/bm_rc4.py --write   -> PASS: bm-RC4 0 failure(s)
python Tools/scripts/bm_rc4.py --check   -> all PASS (30 lines), exit 0
python -c "json.load(receipt)"           -> parses; conflicts []; read_back ok / 7 members
```

The check re-reads the whole RC: drop hashes 9/9, aaf 696/696, `.toc` 714 records matching the
`.ee`, R8 offset-0 rule, internal records for health/physicsc/parts/custom_land_global/engine/
lights, R9 model 4791.3 KB <= 4915 KB, aafdiff vs RC2 120 planned / 0 unexplained, B-10 recorded
NOT MET (6.1 cm vs the 5 cm gate), texture rows 12/23 unfaithful, and the installer rehearsal
(WhatIf/Install/Verify/Rollback/REFUSED) unchanged.

## 5. Limits

* **No game run.** The two values are proven in the packed `.toc`, not in play: whether JC3 applies
  wheel `skew_health` 400 and the D-10 boost/drift set together is UNKNOWN (test ban). The merge
  proves the bytes, not the behaviour.
* **The build tree is shared.** While this ran, another session held
  `Builds/bm-RC4/drop/sound/fmod_banks/weapons.bank` (the tree could not be deleted) and edited
  `bm_rc4.py` concurrently: a `_json_safe` helper landed with a string literal broken across a line
  (a syntax error at line 614), and one receipt written during that overlap was unparseable JSON at
  line 1819. I repaired the literal (docstring first, `ctrl = {chr(9), chr(10), chr(13)}`, no
  backslash escapes) so the file compiles, then rebuilt; the receipt now parses. `_json_safe` is a
  no-op on this receipt (no control characters present). The helper is not part of the module
  merge and was left in place.
* **Untracked script.** `Tools/scripts/bm_rc4.py` is untracked in git (`??`), so a `git checkout`
  cannot revert it; revert by restoring the pre-edit copy. The generated trees
  (`Builds/bm-RC4`, and the `tmp/b14` work dir) are rebuilt by `--write`.
* **Still not done in this RC** (unchanged by this correction): 12 of 23 texture rows are
  unfaithful and the reopened B-10 chassis-box placement gate is 6.1 cm against 5 cm; both stay in
  `receipt.not_done`.
