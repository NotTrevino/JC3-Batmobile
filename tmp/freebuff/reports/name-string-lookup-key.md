STATUS: done. The key **is** derivable from the item path, and the build already derives it: the store's
key is `StringHelpers.HashJenkins(leaf)` where `leaf` is the entity `.ee`'s own name, and the
description is `HashJenkins(leaf + "_desc")`. Proven on five shipped vehicles (all compute and resolve
11/11) and on the Serpente's three vanilla leaves. The Batmobile's key is **1621485476**
(`..._debug`, the leaf bm-013 ships) with description **4081821928**, and both are present 11/11 in
`Builds/bm-013/drop/profile/online.stringlookup` carrying "BATMOBILE" and the blurb.

Two corrections to the row's premise, both decoded:

1. **`443190071` resolves to nothing, not to Serpente text.** It is `HashJenkins("v0300_car_kensington_sportsmuscle_batmobile")`
   — the leaf name bm_leaf.py *proposed*, before Q-1a moved the build to the `_debug` leaf. It has
   **0/11** pairs in the vanilla store and **0/11** in bm-013's drop. The Serpente name is at
   `3535039305 = HashJenkins("..._civilian_01")`. If the menu showed Serpente text on an entry whose
   `UIName` is `443190071`, that was a **fallback on the item's `Name`/leaf**, not a lookup hit; the fix
   is to key the pair on the leaf that actually ships, which bm-013 does.
2. **T-WLD4/T-WLD6's "blocked: no write side" is superseded.** `Tools/scripts/jc3strings_write`
   exists and `bm_rebel.py` calls it; bm-013's drop adds exactly **22 pairs (2 per language × 11)** and
   nothing else changes.

## Files written

| file | what |
|---|---|
| `tmp/freebuff/reports/name-string-lookup-key.md` | this report |

Read-only: nothing in `Builds/`, `Working/` or the store was modified. Revert = delete this file.

## 1. What the key is made from (decoded)

| element | definition | evidence |
|---|---|---|
| leaf | the entity `.ee` file name without `.ee`, e.g. `v0300_car_kensington_sportsmuscle_debug` | `bm_leaf.py` docstring + `INDEX.jsonl` (`<leaf>.ee`, `.ee.toc`, `.epe`, `.stringlookup` per leaf) |
| name key | `HashJenkins(leaf)` — `rbmhdr.hash_jenkins`, a byte-for-byte port of `StringHelpers.HashJenkins` | `rbmhdr.py:54`; `bm_rebel.py:79` `H = lambda s: hash_jenkins(s.encode())` |
| desc key | `HashJenkins(leaf + "_desc")` | `bm_rebel.py:226-227` (`add_string_hash(LEAF, H(LEAF))`, `add_string_hash(LEAF + "_desc", H(LEAF + "_desc"))`) |
| store | `profile/online.stringlookup`: 11 languages × `SortedPairs[].Hash → TextOffset` into one `Text[]` byte pool | `stringlookup_compare.load`, `COLOUR`/`bm_rebel.py:10` |

So the key is a function of the **leaf name**, which is exactly the last path component of the item's
entity path (`editor/entities/jc_vehicles/<...>/<leaf>.ee`). Nothing else — not the item's `Name`
field, not the display string — feeds it.

## 2. Where `443190071` came from

| value | source |
|---|---|
| `443190071` | `HashJenkins("v0300_car_kensington_sportsmuscle_batmobile")` — computed, and recorded at `bm_leaf.py` header: *"the Rebel Drop item (B-13) names `..._batmobile` (hash_jenkins 443190071)"* |
| `1621485476` | `HashJenkins("..._debug")` — the leaf bm-013 actually ships after Q-1a (a NEW leaf never spawns; the dropzone only overrides paths already in the archives) |
| `4081821928` | `HashJenkins("..._debug_desc")` — bm-013's description pair |
| `2073308658` | `HashJenkins("..._civilian_01_desc")` — the donor's vanilla blurb, verified below |

## 3. Proof on shipped vehicles (decoded)

Computed key vs the vanilla `online.stringlookup` (11/11 = resolves in every language):

| leaf | computed name key | pairs | text (L0) | computed desc key | pairs |
|---|---:|---:|---|---:|---:|
| `v0001_car_autostraad_armoredtruck_commercial_01` | **484034449** | 11/11 | "STADT TRESOR ST 8530" | 1743565940 | 11/11 |
| `v0000_car_autostraad_oldjeep_civilian_z80` | **2887741045** | 11/11 | "WEIMARANER Z80" | 1189452051 | 0/11 |
| `v0201_car_capstone_mediumtank_rebel_01` | **2758160814** | 11/11 | "CS ODJUR" | 1268493907 | 11/11 |
| `v0300_car_kensington_sportsmuscle_signature_preorder` | **3012064047** | 11/11 | "WEAPONIZED SERPENTE" | 2829338084 | 11/11 |
| `v0300_car_kensington_sportsmuscle_civilian_01` | **3535039305** | 11/11 | "KERNER SERPENTE R" | 2073308658 | 11/11 |

Two identity checks that make the derivation an oracle rather than a fit:

* `HashJenkins("v0300_car_kensington_sportsmuscle_civilian_01_desc") == 2073308658` → **True**, the
  exact `UIDescription` T-WLD6 quotes as the Serpente's blurb.
* `HashJenkins("v0300_car_kensington_sportsmuscle_debug_desc") == 4081821928` → **True**, bm-013's
  receipt `desc_hash`.

Coverage over the whole vehicle corpus (139 leaves from `INDEX.jsonl`):

| fact | value |
|---|---:|
| leaves with a name pair in 11/11 languages | **77 / 139** |
| leaves with a `_desc` pair in 11/11 | **47 / 139** |
| leaves with both | **47 / 139** |

The 62 leaves without a name pair are the variant leaves a menu never lists (`_blackhand_01`,
`_prisoner_01`, `_debug`, mech parts) — which is exactly why `_debug` needed a pair added and why the
"no pair" state for a new leaf is normal, not a bug.

## 4. The Batmobile's key

| leaf the build ships | name key | desc key | state |
|---|---:|---:|---|
| `v0300_car_kensington_sportsmuscle_debug` (**bm-013**) | **1621485476** | **4081821928** | present **11/11** in `Builds/bm-013/drop/profile/online.stringlookup`, text "BATMOBILE" + the blurb (`Working/World/bm_rebel_text.json`), English in all 11 |
| `v0300_car_kensington_sportsmuscle_batmobile` (old plan) | 443190071 | 1805638565 | **0/11** in vanilla and in the drop — the leaf is never shipped |

Drop diff (vanilla → bm-013): pairs **14,712 → 14,734** (+22), added hashes per language exactly
`[1621485476, 4081821928]`, added text exactly `["BATMOBILE", "Arkham Knight's armoured Batmobile:
pursuit speed, a battle-mode turret, and armour that shrugs off small arms."]`; no pre-existing pair
changed, every `SortedPairs` ascending, dialogue lines untouched.

**So: what is missing is not the key.** The key is a two-line computation from the leaf, and the
pairs exist in the RC. What remains is runtime (Q-1): whether the drop menu resolves the new leaf's
pair when the item names it — the same unknown `bm_rebel.py` records.

## 5. Row consequence and the STAGES.md gap

| row | current state | what the files support |
|---|---|---|
| `T-WLD4` (display name) | `blocked`, "443190071 resolves in 0 of 11… no write side" | **carried**: key `HashJenkins(leaf)`, and the pair exists 11/11 in bm-013 for the shipped leaf. The `0 of 11` was measured against the *unshipped* leaf. |
| `T-WLD6` (description) | `blocked`, same reason | **carried**: key `HashJenkins(leaf + "_desc")`, pair exists 11/11. |

Closest JC3 system, per STAGES.md: **exact** — `profile/online.stringlookup` is the name/description
carrier, and the only JC3 convention needed is "key = leaf hash, desc key = `leaf_desc` hash", which
5 shipped vehicles and the donor's own three leaves reproduce. Gaps the build still owns:

1. **Language coverage.** The pair exists in 11 languages, but the text is English in all 11
   (`bm_rebel.py` decision: "English text in all 11 languages"). BmAK ships its strings in the
   game's 11 languages; JC3's carrier can hold all 11 correctly — the missing piece is the translated
   text, not a system.
2. **`UIVideoPath` still points at the donor's string** (`bm_rebel.py` decision), because no video
   asset exists for the new leaf. That is a real asset gap, not a key problem.
3. **Runtime resolution (Q-1)** — untestable under the test ban; the only item that cannot be closed
   offline.

## Commands and output, verbatim

```text
$ python - <<'PY'    # key = hash_jenkins(leaf); check against the vanilla store
...
civilian_01          name=3535039305 (11/11)  desc=2073308658 (11/11)
signature_preorder   name=3012064047 (11/11)  desc=2829338084 (11/11)
debug                name=1621485476 (0/11)  desc=4081821928 (0/11)
batmobile            name=443190071 (0/11)  desc=1805638565 (0/11)

donor desc 2073308658 == hash(civilian_01_desc)? True
bm-013 desc 4081821928 == hash(debug_desc)? True

leaves: 139
name pair 11/11: 77  desc pair 11/11: 47  both: 47
  v0201_car_capstone_mediumtank_rebel_01   2758160814 11/11 'CS ODJUR'  desc=1268493907 11/11 'Equipped with a 14mm machine gun...'
  v0001_car_autostraad_armoredtruck_commercial_01  484034449 11/11 'STADT TRESOR ST 8530' desc=1743565940 11/11
  v0000_car_autostraad_oldjeep_civilian_z80  2887741045 11/11 'WEIMARANER Z80' desc=1189452051 0/11
  v0300_car_kensington_sportsmuscle_signature_preorder 3012064047 11/11 'WEAPONIZED SERPENTE' desc=2829338084 11/11
```

```text
$ python - <<'PY'    # vanilla store vs bm-013 drop
vanilla pairs 14712 drop pairs 14734
added per lang: {0: [1621485476, 4081821928], 1: [1621485476, 4081821928]}
added text: ["Arkham Knight's armoured Batmobile: ...", 'BATMOBILE']

key 443190071: vanilla 0/11  drop 0/11
key 1621485476: vanilla 0/11  drop 11/11   drop L0: BATMOBILE
key 4081821928: vanilla 0/11  drop 11/11   drop L0: Arkham Knight's armoured Batmobile: ...
key 2073308658: vanilla 11/11 drop 11/11   drop L0: Kerner's top sports model, ... (Serpente blurb)
key 3535039305: vanilla 11/11 drop 11/11   drop L0: KERNER SERPENTE R
```

```text
$ python -c "print({k:r[k] for k in ('leaf','leaf_hash','desc_hash')})"  # from Builds/bm-013/receipt.json
{'leaf': 'v0300_car_kensington_sportsmuscle_debug', 'leaf_hash': 1621485476, 'desc_hash': 4081821928}
```

## UNKNOWNs

1. **The 11 language names.** `Languages[i].Name` produced no rows through `jc3adf.walk` on this file
   (the language list is keyed by index only in what the walker exposes). The *text* is readable per
   index; the mapping index → language code is UNKNOWN from this store. Would be found in: the
   `.stringlookup`'s `Languages[]` struct header or the loc system.
2. **Whether the menu resolves a pair for a leaf the item names but no `.ee` loads under.** bm-013
   ships the pair and the entity under `_debug`; Q-1 is the only oracle and is banned.
3. **Why the `_debug` leaf has no vanilla pair while 77 other leaves do.** The pattern (debug
   protos are not listed in the drop menu) is consistent with observation but not proven here.
