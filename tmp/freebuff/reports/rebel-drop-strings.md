STATUS: done — the built drop carries both new pairs in all 11 languages (name `60A5E7A4`, blurb `F34BA8E8`, the Jenkins hashes of the leaf), the hashes match, no vanilla pair is missing or altered, and `item.onlinec` item 196 points at both. One compromise: the blurb is the same English sentence in every language.

# Rebel Drop strings: is the car named?

## What was asked

Check that the built bm-013 / bm-RC2 drop (`profile/online.stringlookup`, `profile/item.onlinec`)
contains the new name and blurb pairs for all 11 languages, that the hashes equal
`hash_jenkins` of the leaf names, and that no vanilla pair was removed (compare with the vanilla file
count). Output `Builds/bm-RC2/verify/strings.md` + `Tools/scripts/v_strings.py --check`.

## The chain, as `Research/JC3Grab/NAMES.md` states it

The display name is a 32-bit Jenkins hash of the entity **leaf**, resolved in
`profile/online.stringlookup`; the blurb is `<leaf>_desc` in the same store; `profile/item.onlinec`
holds the pointers. The build renames the leaf to `v0300_car_kensington_sportsmuscle_debug` (the
`.ee` the drop ships), so both pairs have to be added or the car shows no name.

## Result

| pair | hash | expected from | languages |
|---|---|---|---|
| name | `60A5E7A4` | `hash_jenkins("v0300_car_kensington_sportsmuscle_debug")` | 11/11 |
| blurb | `F34BA8E8` | `hash_jenkins("…_debug_desc")` | 11/11 |

* **Vanilla store** `_gamedata/JC3grab/strings_rt/online.stringlookup` — 11 languages
  (`en, fr, de, it, es, ru, pl, ja, pt, es-MX, ar`), 14,233 hashed pairs (1,385 / 1,307 / 1,301 /
  1,310 / 1,318 / 1,370 / 1,329 / 1,385 / 1,307 / 1,320 / 1,380 per language), text blob 1,436,014 B.
* **Built store** `Builds/bm-RC2/drop/profile/online.stringlookup` (sha256 `6dcdf0ce…60bc4`,
  1,746,322 B) — same 11 languages, **+2 pairs in every language** (1,387 … 1,382), text blob
  1,437,356 B; 1,425 distinct hashes vs 1,423 vanilla: exactly the two new ones, **no hash removed**.
* **Text** — `en` and every other lane: `BATMOBILE` and `Arkham Knight's armoured Batmobile: pursuit
  speed, a battle-mode turret, and armour that shrugs off small arms.`
* **Nothing vanilla lost or changed** — per language: `missing = 0`, `text changed = 0`; every vanilla
  `(hash, text)` still resolves identically in the built store.
* **`item.onlinec`** (`Builds/bm-RC2/drop/profile/item.onlinec`, sha256 `239d6b6d…50a6c`, 197 items) —
  item **196** has `UIImagePath = v0300_car_kensington_sportsmuscle_debug`, and its 48-bit members:
  `Name` = `107EA7B1 60A5E7A4`, `UIName` = `F34BA8E8 60A5E7A4`, `UIDescription` = `91018BDA F34BA8E8`
  — low 32 bits are the member's own hash, high 32 the next link, so both hashes are carried as
  required. The old leaf's item (118, `…_civilian_01`) is still in the table.
* **bm-013 vs bm-RC2** — the two `online.stringlookup` files and the two `item.onlinec` files are
  byte-identical (same sha256), so bm-013's drop carries the same strings.

## Files written

| file | what |
|---|---|
| `Tools/scripts/v_strings.py` | new generator; `--write` renders, `--check` re-reads the three stores/drops, re-derives every count and byte-compares the page |
| `Builds/bm-RC2/verify/strings.md` | the tabulation: the two pairs per language, the per-language census, the item members with their low/high halves, oracles, labels |
| `MODLOG.md` | one appended section (intended change, why, revert) |
| this report | `tmp/freebuff/reports/rebel-drop-strings.md` |

## Commands and output (verbatim)

```
cd "E:/Modding/JC3-Batmobile" && export PYTHONIOENCODING=utf-8 && set -o pipefail && python Tools/scripts/v_strings.py --write; echo "EXIT write=$?"; python Tools/scripts/v_strings.py --check; echo "EXIT check=$?"
wrote Builds/bm-RC2/verify/strings.md (6439 bytes)
EXIT write=0
PASS the vanilla store has 11 languages
PASS the built store has 11 languages
PASS exactly two new hashes appear
PASS the name hash is hash_jenkins(leaf)
PASS the blurb hash is hash_jenkins(leaf + _desc)
PASS both pairs are in all 11 languages
PASS every language grows by exactly two pairs
PASS no vanilla pair is missing
PASS no vanilla text is altered
PASS the built store carries vanilla + 22 pairs
PASS the item record exists for the leaf
PASS item Name low half is the name hash
PASS item UIName low half is the name hash
PASS item UIName high half is the blurb hash
PASS item UIDescription low half is the blurb hash
PASS the old leaf's item is still present
PASS bm-013 and bm-RC2 ship the same store
PASS bm-013 and bm-RC2 ship the same item table
oracles: 18/18 pass
document identical: Builds/bm-RC2/verify/strings.md
EXIT check=0
```

## UNKNOWNs

* **Whether the game's Rebel Drop menu actually displays these** — no test was run (the test ban
  stands); the chain is proven in the files only, which is what NAMES.md already establishes.
* **Whether 11 is the full language set for this install** — it is the set the vanilla store carries
  (0..10), which is what the brief asks to match; a locale the vanilla store itself lacks cannot be
  checked here.
* **Whether the blurb should be localized** — no translated text exists in any repo file or research
  output; writing it would be invention, so the same English sentence fills all 11 lanes.

## COMPROMISES

* **The blurb is the same English sentence in all 11 languages** (the name `BATMOBILE` is a proper
  noun and reads the same everywhere). Not a translation compromise of the *mechanism* — the pairs,
  hashes and item pointers are complete — but it is a lore/localization deviation the operator has to
  approve or replace with real translations.
* Nothing was installed, launched or attached to; both stores, both item tables and the vanilla file
  were opened read-only.
