# RC5 fire references — the four `F30CCB1C` dangling values (DONE)

Verdict: **4 real defects, 0 false positives.** The target is not in the RC4 graph, the gate's
cross-file rule does not cover it, and the smallest edit is the B-16 cleanup RC3 already carries:
set the four owner links to null. Nothing is cloned under the three new roots and the gate is not
changed. `Tools/scripts/rc5_fire_refs.py --check` exits **0** with `dangling 4 -> 0`.

| | |
|---|---|
| source (read only) | `Builds/bm-RC4/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.epe`, 134,072 B, sha256 `a8d5d11f93217ff9fc3975dfc28a0ea0f46490b6fb08f0cf73b0b4ec318a9069` |
| edit list | `Builds/bm-RC5-entity/fire_refs.json` — 4 edits, `verdict PASS`, `dangling_before 4`, `dangling_after 0` |
| gate machine record | `tmp/freebuff/scratch/rc5-gate/wiring.json` (scratch copy of the gate, output redirected) |
| `Builds/bm-RC4` | not written; `git status --porcelain Builds` is empty |

## 0. The gate's attribution is wrong, and that changes the fix

`verify-v03-wiring-rc4.md` §2 says the four values are member `F30CCB1C` of an `SAttachedEffect`
named `Fire`, and that each of the three new `CCar` roots carries one, pointing at a donor child
that was never cloned. The bytes say none of that:

* `F30CCB1C` is a **direct member of the four `CBulletWeaponBase` objects**, one indent level above
  the `SEffects` that holds the `Fire` attachment. XML line 7690 sits at 3 tabs; the `Fire` object
  at line 7606 is at 4 tabs and its members are at 5. The member is a sibling of the weapon's
  `SEffects` child, not a member of `Fire`.
* The **three extra roots are childless**: no object at indent 3 opens between 8231–8412,
  8660–8841 or 8842–end. They have no `Fire` attachment and no `F30CCB1C` member.
* All four carriers are `CBulletWeaponBase` at indent 2, i.e. top-level siblings of the four roots
  inside the container's `root` object — not children of any root.

So there is no "pointer to a donor child that was never cloned", and the gate's first-byte `0xef7c`
is only the first of four distinct offsets (the gate dedupes rows by `(gate, value, carrier)` and
counts occurrences; `0xef7c` is in `w603_mediumtank_mgun`, the second carrier in document order).

## 1. Fact one — does the donor carry the value, and who defines what it names?

**The vanilla donor carries no `F30CCB1C` member at all.** The donor graph
(`Builds/bm-RC4-base/.../v0300_car_kensington_sportsmuscle_civilian_01.epe`) has 415 objects and
zero `F30CCB1C` members; the string `FFFF05DA` does not occur anywhere in its 7,444 lines of XML.
The value therefore cannot be a donor reference, cloned or otherwise.

**The object it names is defined by the APC's own entity file**
`E:/Modding/_gamedata/JC3grab/epe_schema/apc_debug.epe`: `4DAE31AE=FFFF05DA` is that file's `CCar`
root (`_class CCar`), first raw byte `0x5d0` of a 100,278-byte blob. That file contains exactly one
`F30CCB1C` name-hash and two occurrences of the id — its own definition plus its mounted weapon's
owner link. The reference is a foreign entity's root, carried into a graph that does not define it.

**Why the gate does not excuse it.** G2 (`Tools/scripts/v03_wiring_rc4.py` L187–200) excuses a
reference when its tail (`FFFF05DA`) appears among the external tails the donor itself makes:
`v_ext` is built from the donor's own refs whose full id the donor does not define. Reproduced on
the RC4 file: **78 objectid refs → 452 objects, 10 cross-file refs the donor also makes, 3 distinct
tails.** `FFFF05DA` is not one of those three, and the donor never references it. The four are
therefore genuine dangling values by the gate's own rule — a real defect, not a gate false positive.

## 2. Fact two — which object should each new root's `Fire` attachment name?

**None, because the premise does not hold: no new root has a `Fire` attachment.** The three extra
roots are members-only clones (`build-d05` §3) and the file confirms it — they contain no child
objects. The four `SAttachedEffect` `Fire` objects in the file (lines 7606, 7853, 8100, 8542) are
children of the four weapons' `SEffects`, and none of them carries `F30CCB1C`; each carries its own
`_object_id 6B11EB53=FFFF6960`, `Effect 1687852927` and the same `world` matrix.

There is consequently nothing to repoint: the only repair the four values need is on the weapon that
owns them. (Separate observation, not a dangling reference: all four `Fire` objects share the id
`6B11EB53=FFFF6960` — 4 definitions, 0 references. A duplicate `_object_id` in the merged graph,
outside the scope of these three questions.)

Which slot each extra root is cannot be read from this file: the roots carry no `name` member, and
the file order is `…=FFFF801B` (all slot pointers null), `…=FFFF801A` (all null), `…=FFFF8019`
(`851CAABE` → `8AE3029C=FFFF8008`, `00568A74` → `AAE79E16=FFFF800C`, i.e. the missile pair). That is
one bound root and two reserved, matching `build-d05` §3's counts, but the slot **names/numbers** do
not follow the table's order — UNKNOWN, and not needed here.

## 3. Fact three — the smallest edit

**Null the four owner links** (8 zero bytes at each offset), which is what `Builds/bm-RC3` already
ships after B-16. Per occurrence, each proved by patching that offset alone and watching exactly one
member turn null (the four offsets are a bijection onto the four members; the packed order is not
the document order):

| # | `.epe` offset | packed rank | XML line | carrier class | carrier name | carrier `_object_id` | old | new | verdict |
|---:|---|---:|---:|---|---|---|---|---|---|
| 0 | `0x11054` (69,716) | 2 | 7690 | `CBulletWeaponBase` | `w602_mediumtank_canon` | `DF009C2C=FFFF8002` | `4DAE31AE=FFFF05DA` | `00000000` | real defect |
| 1 | `0xef7c` (61,308) | 0 | 7937 | `CBulletWeaponBase` | `w603_mediumtank_mgun` | `DD9B64C0=FFFF8005` | `4DAE31AE=FFFF05DA` | `00000000` | real defect |
| 2 | `0x1ff3c` (130,876) | 3 | 8184 | `CBulletWeaponBase` | `w618_sportsmuscle_missile` | `8AE3029C=FFFF8008` | `4DAE31AE=FFFF05DA` | `00000000` | real defect |
| 3 | `0x1009c` (65,692) | 1 | 8626 | `CBulletWeaponBase` | `w618_sportsmuscle_missile_emp` | `AAE79E16=FFFF800C` | `4DAE31AE=FFFF05DA` | `00000000` | real defect |

Precedent, all measured from the same member:

| build | `F30CCB1C` values | note |
|---|---|---|
| `bm-RC4-base` donor | *(no member)* | 415 objects, member absent |
| `bm-008` | `4DAE31AE=FFFF05DA` | same foreign value |
| `bm-RC3` | `00000000` | B-16 cleanup applied |
| `bm-RC4` | `4DAE31AE=FFFF05DA` | four occurrences |

RC4's entity tree therefore descends from the pre-B-16 lineage (bm-008-like), not from RC3: the B-16
null was lost in a rebuild, not merely never applied. The mechanism is visible in the weapon itself —
`w602_mediumtank_canon` carries `…/w602_batmobile_cannon.wtune` (line 7667) **and**
`…/w206_mounted_capstone_m2hm_body.model_xml` (line 7693), i.e. an APC weapon's member block with
the Batmobile's tune swapped in, and that block includes the APC root's owner link.

Why not the other two options:

* **Cloning a child under each new root** would write an object the roots deliberately do not have
  (`build-d05` §3 avoids duplicating the effect set), would duplicate four more `SAttachedEffect`
  objects, and would still be wrong: the target is the **APC entity's own root**, not a child of
  this entity. Cloning it into a Batmobile graph would bind a car root to another entity's car.
* **Teaching the gate the tail** `FFFF05DA` as an acceptable external reference would excuse a value
  that no file in the delivered build defines; the donor makes no such reference, so the excuse
  would be a suppression, not a rule.

## 4. The tool

`Tools/scripts/rc5_fire_refs.py` (`--write`, `--check`), read-only on `Builds/bm-RC4`:

1. converts the RC4 `.epe` and the donor `.epe`, and finds every `F30CCB1C` member (4) and every
   packed occurrence of `4DAE31AE=FFFF05DA` (4);
2. proves offset → carrier by patching **one occurrence at a time** and requiring exactly one member
   to change, then requiring the mappings to be a bijection (this is how the non-document packed
   order was caught: `0xef7c` is rank 0 but the second carrier);
3. applies the B-16 rule (target absent locally and not a donor tail ⇒ null) and records the
   verdict per occurrence;
4. re-runs **G2 itself** (`g2()`, the same `OBJ_RE`/`ID_RE`/tail rule as the gate) over the patched
   blob and requires `dangling == 0`;
5. `--check` re-emits the document and compares it byte for byte with the on-disk JSON.

Determinism: two `--write` runs are byte-identical (`cmp` clean), then `--check` prints
`OK: 4 occurrences, G2 dangling 4 -> 0, edit list matches` and exits 0.

The gate's own G2 was also re-run from a scratch copy of `Tools/scripts/v03_wiring_rc4.py`
(`tmp/freebuff/scratch/v03_wiring_rc4_scratch.py`, `ROOT` pinned and `OUTD` pointed at
`tmp/freebuff/scratch/rc5-gate/`, because the original's `--write` targets `Builds/bm-RC4/verify`).
It reproduces `FAIL G2: 78 objectid references -> 452 objects; 10 cross-file refs the donor .epe
also makes (3 distinct); dangling 4`, and the six G3 paths unchanged. `Builds/bm-RC4/verify` was not
touched.

## 5. Files written, and how to revert

| file | change | revert |
|---|---|---|
| `Tools/scripts/rc5_fire_refs.py` | new RC5 fire-reference resolver | delete the file |
| `Builds/bm-RC5-entity/fire_refs.json` | generated edit list, 4 edits, PASS | delete the file (and the empty `bm-RC5-entity/` dir) |
| `tmp/freebuff/scratch/v03_wiring_rc4_scratch.py` | scratch copy of the gate, output redirected | delete |
| `tmp/freebuff/scratch/rc5-gate/wiring.json`, `wiring.md` | gate re-run record | delete |
| `tmp/freebuff/reports/rc5-dangling-fire-refs.md` | this report | delete |

No build tree, `.ee`, `.toc`, card or game file was modified. The edit list is for the later 3-way
`.epe` merge, which must apply the four 8-byte writes at the recorded offsets (or re-resolve by
carrier `_object_id`, since a merge that shifts the packed layout invalidates absolute offsets).

## 6. Limits and UNKNOWNs

* **What `FFFF05DA` is, is UNKNOWN.** It may be a file id; the decoded fact is only that no object in
  this graph defines `4DAE31AE`, which is what the RC ships.
* **Whether a null owner link still fires at runtime is UNKNOWN** (test ban). RC3 ships the null
  form and is the B-16 decision; this report does not claim the weapon fires.
* **Slot numbering of the three extra roots is UNKNOWN** — they carry no `name` member and the file
  order does not match `build-d05` §3's table order (one root holds the missile pair, two are null).
* The duplicate `_object_id 6B11EB53=FFFF6960` on the four `Fire` objects is recorded, not repaired:
  it is a target-without-reference, which G2 does not test.
* G3's six missing asset paths are untouched here; they remain as `verify-v03-wiring-rc4.md` §2 lists
  them.
