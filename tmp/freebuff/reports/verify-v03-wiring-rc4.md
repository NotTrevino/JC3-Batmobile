# V-03 wiring gates on bm-RC4 (DONE — verdict FAIL, 7 dangling values)

Ran `Tools/scripts/v03_wiring_rc4.py` on `Builds/bm-RC4`, offline and read-only. Nothing was
installed and no game process was started. The gate's answer is **FAIL**: the wiring is not clean,
and the failures are real references, not missing files the build forgot to copy.

## 1. Result

| gate | result | measured |
|---|---|---|
| G1 points | **PASS** | 9 `SWeaponPoint`, 0 part refs dangling (59 parts in the built parts module) |
| G2 ids | **FAIL** | 78 objectid references → 452 objects; 10 cross-file refs the donor makes; **4 occurrences of `4DAE31AE=FFFF05DA` resolve to no object** |
| G3 refs | **FAIL** | 32 asset paths from the `.epe` + 7 non-base `.vmodc` modules; **6 dangling** (etune 2/3, ftune 1/3, model_xml 0/1, pfx 0/1, wtune 6/7, ctune 17/17) |
| G4 audio | **PASS** | `.ee.fmod_guids` byte-identical to the audio tree's (758 B); 45/45 present, 24 resolved in a built bank, 21 declared donor (B-26), 0 missing |
| G5 drop | **PASS** | item 1621485476 → `_debug.ee` + `.toc` + 18,688 B icon in `drop/` |

`wiring.json`: `verdict FAIL`, `dangling 7`, `dangling_occurrences 10`, `gate_failures 0`.
`.toc` 714 records, `.epe` 9,025 XML lines, 452 objects, 4 `CCar` roots.

## 2. What the failures are

### G2 — four `SAttachedEffect` "Fire" objects point at an object that does not exist

All four occurrences are member `F30CCB1C` of an `SAttachedEffect` whose `name` is `Fire`; the value
is `4DAE31AE=FFFF05DA`. No `_object_id` in the merged graph starts with `4DAE31AE`, and the value is
absent from the vanilla donor `.epe` (7,444 XML lines) as well.

Cause, from B-05's own build rule: the three extra `CCar` roots are **"cloned from the donor root's
members only (no children)"** (`build-d05` §3). Each new root's `Fire` attachment therefore carries a
pointer to a donor *child* object that was never cloned. The reference is copied faithfully; its
target is not in the file. First byte **0xef7c** in the `.epe` (all four share identical bytes, so
`locate` reports the first).

That is a wiring defect with an owner (B-05 / the T-WP13 root clone), not a merge artifact: the
reference is already in `Builds/bm-RC4-entity`.

### G3 — six donor asset paths are in neither the build nor the installed-archive index

| path | `.epe` byte | evidence |
|---|---:|---|
| `editor/entities/jc_environments/shared/rigid_object_effect_settings_default.etune` | 0xecf4 | index has `..._light.etunec` and `..._medium_light.etunec`, **no `_default`** |
| `editor/entities/jc_explosions/gen_explosion_5m_nodamage.ftune` | 0x2974 | absent from the index and from `dictionary.json` |
| `editor/entities/jc_explosions/vehicles/truck_emp.ftune` | 0x13a0 | absent from the index and the dictionary (B-18's chosen EMP tune) |
| `editor/entities/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm_grip_point.wtune` | 0xee50 | the w206 `.ee`/`.wtunec` are indexed; this sub-asset is not |
| `models/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm_body.model_xml` | 0xef88 | sub-asset, not a separately named archive entry |
| `models/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm_body_col.pfx` | 0xedf0 | same |

All six were introduced by the entity/weapons trees (`Builds/bm-RC4-entity`, `bm-RC4-weapons`); the
base `.epe` has none of them. None resolves as `<path>` or `<path>c` in the build, and none is a name
in `Research/JC3Grab/INDEX.jsonl` (81,952 entries; only 2 `.ftune` names total, so the index is a
partial grab and absence is **not** proof the game lacks the file). `capstone_m2hm`'s `.ee` and
`.wtunec` being indexed while its `grip_point`/`body`/`pfx` are not is consistent with sub-assets of
a compiled `.ee`; `truck_emp.ftune` and `rigid_object_effect_settings_default.etune` have no such
explanation — the latter has `_light`/`_medium_light` siblings, which looks like a wrong variant name.

## 3. Determinism, and why `--check` exits 1

`--write` was run twice; both artefacts are byte-identical:

```
run1=1 run2=1 json_identical=0 md_identical=0
36eb094fe7e6edcd868b53deb6018c26567728ce03c9f63924607923f5a02b00  wiring.json (both runs)
fe84f01c11f75191598115b470012d48bfed8cee6e4e12587d26677374419104  wiring.md   (both runs)
```

`--check` reproduces both documents exactly — `PASS documents: wiring.json and wiring.md match the
regenerated text` — and then exits **1** because the verdict is FAIL. That exit code is the gate's
honest result, not a document mismatch; weakening it would be exactly the suppression `AGENTS.md`
forbids.

## 4. Fixes made while writing the gate (not suppressions)

1. **G4 compared against a non-existent filename.** The audio tree predates B-14's leaf rename, so its
   copy is still `..._civilian_01.ee.fmod_guids` while the RC's inner record is `..._debug.ee.fmod_guids`.
   The first run reported "False" although the bytes are identical (758 B, 0 differing). The gate now
   matches by `*.ee.fmod_guids` suffix and compares bytes. G4 is green on evidence.
2. **Duplicate offsets.** The same objectid written into four objects was printed four times at the
   same first-hit offset. Rows are now deduped by `(gate, value, carrier)` with a `times` count.
3. **Vanilla precedent source.** The first version read the base tree's `.epe`; that is the pre-B-05
   graph, not vanilla. It is still used for G3's "donor uses it" excuse, and the six new paths were
   confirmed absent from the true vanilla `.epe` (reconstructed with `jc3weapons.read_row` +
   `jc3strings.load_index`, 7,444 XML lines). Using vanilla does not change the result: the six are
   new, not donor.

## 5. Declared stand-ins (counted, not dangling)

| stand-in | count | note |
|---|---:|---|
| `CCar` roots | 4 | 3 extra childless `_slot2/_slot3/_slot4`; whether several roots on one chassis fire from the driver seat is UNKNOWN |
| `CForcePulse` class values | 3 | B-05 names 2 (`CForcePulse_EMP`, `CForcePulse_Sonar`), both at the graph origin; the third is the donor object the copies came from |
| interaction objects with no named `world` | 69 | skipped by B-05, not written with a guessed transform |

## 6. Files written, and how to revert

| file | change | revert |
|---|---|---|
| `Tools/scripts/v03_wiring_rc4.py` | new V-03 gate for RC4 | delete the file |
| `Builds/bm-RC4/verify/wiring.json` | generated, `verdict FAIL`, 7 dangling values | delete both generated files |
| `Builds/bm-RC4/verify/wiring.md` | generated, same content | same |
| `tmp/freebuff/reports/verify-v03-wiring-rc4.md` | this report | delete it |

No build tree, no `.ee`/`.toc`, no card and no game file was modified.

## 7. Limits and UNKNOWNs

- **The six external paths' runtime resolution is UNKNOWN.** The index is a name index, not the
  VFS; a compiled sub-asset can be absent from it and still load. Proving it needs a game probe
  (test ban), or decoding the `.ee` that owns the sub-asset.
- **The `FFFF05DA` half of the objectid is not decoded.** It may be a file id; if so the target
  could live in a donor `.ee` and the reference might resolve at runtime. What is proven is that no
  object in *this* graph defines `4DAE31AE`, which is what the RC ships.
- **G2's 452 objects / 78 references are counted from the merged XML**; the gate does not verify that
  the referenced objects are the *right* ones, only that ids exist.
- Only the 7 non-base edited modules are walked for G3. Base modules are byte-identical to the
  lineage by construction; if one carried a stale path it would not be seen here.
- Nothing here says the car drives, fires or sounds in play.
