STATUS: done - the store format is decoded end to end and the key function is proven on 45/45
items. A new name/blurb needs a **whole-file patch of the existing `profile/online.stringlookup`**
(11 language arrays in one file, one shared text blob), not a new store file; it is blocked only on
a missing ADF writer in `Tools/scripts`, not on the format or the engine.

## Summary

**Format (decoded).** `profile/online.stringlookup` is one ADF, 1,627,106 B, patch mount
(`patch_win64/game4.arc`), entry offset 609081344, sha256 `f9d3cbf91dce8960...`, one instance
`stringlookup` at ADF offset 80 (1,625,646 B) of type `StringLookup` (32 B):

| type | size | member | offset | size | type |
|---|---:|---|---:|---:|---|
| `StringLookup` | 32 | `Languages` | 0 | 8 | `A[LanguageStringLookup]` |
| `StringLookup` | 32 | `Text` | 16 | 8 | `A[int8]` |
| `LanguageStringLookup` | 32 | `SortedPairs` | 0 | 8 | `A[HashPropertiesPair]` |
| `LanguageStringLookup` | 32 | `SortedDialogueLines` | 16 | 8 | `A[DialogueLine]` |
| `HashPropertiesPair` | 8 | (hash, text offset) | - | 4 + 4 | - |

The "11 language stores" are **11 `Languages[i]` arrays inside this one file**, not 11 files:
1,385 / 1,307 / 1,301 / 1,310 / 1,318 / 1,370 / 1,329 / 1,385 / 1,307 / 1,320 / 1,380 pairs
(14,712 total), every array sorted ascending by hash, every offset into the one 1,436,014 B
NUL-separated `Text` blob (sha256 `fbf5397bc7ea60eb...`).

**Key (decoded + proven).** The key is the 32-bit Jenkins hash of the *name of the thing*, not of
its display text:

- `hash_jenkins("<leaf>")` -> display name (`v0300_car_kensington_sportsmuscle_civilian_01` ->
  `d2b46b49` -> "KERNER SERPENTE R");
- `hash_jenkins("<leaf>_desc")` -> blurb (`7b942df2` -> the Serpente description).

**Oracles (all pass, re-run by `--check`):**
- O1: `UIName == hash_jenkins(UIImagePath)` for **45/45** Rebel Drop vehicle items;
- O2: the donor's name key resolves in **11/11** stores, its `_desc` key in **11/11**;
- O3: for 25 sampled items, both the name key and the `_desc` key resolve in **25/25 x 11/11**.

**Answer to the card.** Adding the Batmobile name and blurb means:
1. **Patch the existing path, whole-file, in the mod's patch layer** - a new file at a *different*
   path is never read (nothing references it; the item stores hashes and the game reads this one
   path). There is no per-language file to add.
2. Per language: insert one 8-byte `{Hash, TextOffset}` pair at its sorted position (positions are
   listed per language in the note) and append one NUL-terminated UTF-8 string to `Text`; both the
   name and the `_desc` pair are needed. Growth: 11 x 2 x 8 = 176 B of pairs plus 11 x (string + NUL)
   of text (~1.5 KB with placeholder strings), on a 1.6 MB file; no new ADF type is needed.
3. The `profile/item.onlinec` record must point at the same hashes (`UIName` / `UIDescription`) -
   vanilla already does; a renamed leaf needs the `.ee` leaf, the item hashes and the pairs to agree.
4. **Blocker: no ADF writer.** A source scan of `jc3adf.py` finds no `def` containing
   write/encode/serial/pack (`writer_present` = False), so the modified ADF cannot be serialised
   with today's tooling. This is a **tooling gap**, not an engine limit and not "impossible".
5. **Revert path:** delete the patched copy from the build's overlay; the game falls back to the
   vanilla store, which was never modified (installs are read-only and the vanilla copy stays in its
   own mount).

No game file was written; nothing was tested.

## Files written

- `Tools/scripts/t_wld4b.py` - the generator (`--write` / `--check` / `--dump`).
- `Working/Translation/T_WLD4B_STRINGS.md` - the note: struct layout, 11 stores, oracles, per-language
  insertion points, the three shipping options, the revert path, UNKNOWNs.
- `Working/Translation/T_WLD4B_STRINGS.json` - the same record, including every pair offset.
- `tmp/freebuff/reports/T-WLD4b.md` - this report.

Not edited: `NAMES.md`, `jc3strings.py`, `T_ROWS.jsonl`, any build tree, any game file.

## Commands and output

```
$ python Tools/scripts/t_wld4b.py --write
wrote E:\Modding\JC3-Batmobile\Working\Translation\T_WLD4B_STRINGS.json
wrote E:\Modding\JC3-Batmobile\Working\Translation\T_WLD4B_STRINGS.md
languages 11 pairs 14712 O1 45 / 45 O3 25 /25
```

```
$ python Tools/scripts/t_wld4b.py --check
langs 11, pairs 14712, O1 45/45, O3 25/25, text 1436014 B, writer False
OK: store decoded, all oracles pass, document and JSON identical
```

`--check` re-reads the store bytes, re-walks all 1,479,755 rows, re-derives both outputs
byte-for-byte, and asserts: 11 stores, each sorted; O1 fully passing; O3 at 25/25; the donor's name
and `_desc` present in all 11; and that no ADF writer has appeared (which would make the
"blocked on tooling" finding stale).

## UNKNOWNs

1. **The 16-byte array descriptor layout** (`A[LanguageStringLookup]`). *Tried:* the store's own
   type table (gives only the size). *Where:* `jc3adf`'s array reader. The pair counts used here are
   re-read from the elements, so the write estimate does not depend on this.
2. **Whether the engine tolerates a duplicate hash** in one store (same key twice). *Tried:*
   nothing - the files prove sorting, not uniqueness. *Where:* a runtime test, which the test ban
   forbids.
3. **The language order.** No language-name field exists; the order (en, fr, de, it, es, ru, pl, ja,
   pt, es-MX, ar) is read off the text - an observation, not a decoded enum.
4. **Whether `profile/online.stringlookup` is the only store the drop menu consults** for this item.
   `ui/ui_localization.stringlookup` does not hold the name (G2-32) and the item's UI hashes only
   resolve here, but the menu's code path is not decoded.
5. **The exact final size** of a patched store: the estimate (+ growth) excludes ADF header/padding
   effects, because the writer does not exist to measure them.

## COMPROMISES

None. This card adds a route (patch the existing store once a writer exists) and does not close any
lore row: T-WLD4/T-WLD6 stay blocked on the writer, exactly as before, but now with the format,
the key, the per-language insert positions and the revert path documented.

Static only: no game launched, attached to or installed to; no install or dropzone written.
