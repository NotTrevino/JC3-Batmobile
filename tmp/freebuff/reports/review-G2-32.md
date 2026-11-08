# Independent review — G2-32 · Names, icons and strings

Reviewer note: I did not write this card. Read-only review; nothing under `GRAB_BACKLOG.md`,
`MODLOG.md`, `Research/`, `Tools/` or the game install was modified. No game was launched and
`D:\Games` was not touched.

## VERDICT

**minor issues.** The check is green, the Out path exists, and the core claim — the name is
`hash_jenkins(leaf)` = `D2B46B49`, resolved in `profile/online.stringlookup`, and the icon is
`textures/ui/vehicle_icons/<leaf>.ddsc` — is correct and reproduces. Two statements should be
fixed before the numbers are reused: the fleet figure **"45 of 45 vanilla vehicle items"** is a
filtered subset (the 45 land-vehicle items; there are **80** vehicle items, and **80/80** resolve
name and icon), and **"the patch copy … differs only in padding - its decoded strings are
identical" is false** (the Japanese prompt was re-translated between the base and patch copies).
Two more are scope overclaims ("the only store that holds it", "no carrier" for the HUD), and
several numbers in the generated doc are typed rather than derived (R11).

## Check output (verbatim)

```
$ python Tools/scripts/jc3strings.py --check
PASS: name 'KERNER SERPENTE R' in 11 languages (id D2B46B49), desc in 11 languages, item 3535039305, icon 18688 B, fleet 45/45 named 45/45 iconed, ui_localization resolves 0 of 2 keys, gfx references 0
```

Exit status 0. Identical to the line recorded in `MODLOG.md` §"G2-32 · Names, icons and strings —
done".

Out path: `Research/JC3Grab/NAMES.md` exists (167 lines). The card's Out names the doc only —
there is no `NAMES.json` and the row does not claim one, so `--check` comparing the generated md
with the file on disk (plus the derived PASS line) is the whole verification. It re-derives every
number the doc prints, but it cannot verify the substance of the Done ("every place the name/icon
appears has a file + id") beyond the generated table; and, as issue 2 shows, the doc also makes
claims the generator never computes.

## Issues

1. **`Research/JC3Grab/NAMES.md:108-111` — "45 vanilla vehicle items" is not the fleet.**
   The script's fleet filter is `UIImagePath.startswith("v0")` (`Tools/scripts/jc3strings.py`,
   `build_payload`, the `for it in drop["vanilla"]["items"]` loop), which keeps only the 45
   **land** vehicles. `REBELDROP.json` has **80** items of `Type 1` — the other 35 are boats
   (`v1302…`, `v1704…`), planes (`v2…`, `v4603…`) and bikes (`v3600…`). So the sentence "of 45
   vanilla vehicle items, 45 resolve … so the rule is exact rather than a one-off" reports a
   subset as the population, and the tracker row repeats "45/45 vanilla vehicle items resolve
   name+icon". I re-measured the full set: **80/80** resolve `UIName` in
   `profile/online.stringlookup` and **80/80** have `textures/ui/vehicle_icons/<UIImagePath>.ddsc`
   (0 missing). The conclusion is actually stronger than claimed; the number and the label are
   wrong.

2. **`NAMES.md:86-88` — the patch copy is not "padding only".** "The **patch** copy is **2226 B**
   and differs only in padding - its decoded strings are identical" is false. Decoding both copies
   with the same reader: base 2210 B / text blob 213 B, patch 2226 B / text blob 229 B, and in the
   Japanese lane (`lang 7`, hash `0xA2B9F82C`) the base says `乗る` while the patch says
   `ビークルに 乗る` — one re-translated prompt, not padding. So "the mod shipping the base table
   loses nothing" is wrong for that language, and the script never compares the two copies (it
   decodes only the patch copy via `best_by_path`; the base copy is only byte-counted and
   `matches_build`-checked). `MODLOG.md` §"G2-32 … done" repeats the same claim.

3. **`NAMES.md:9` — "which is the only store that holds it" is broader than the measurement.**
   The script reads exactly two global stores (`profile/online.stringlookup`,
   `ui/ui_localization.stringlookup`) plus the donor's own entity file. The index carries
   **3,002** `.stringlookup` files, **523** of them under `jc_vehicles`; none of those was
   searched. The `.gfx` half of the same paragraph *is* exhaustive (all **59** `.gfx` files in the
   index are under `ui/`, and the script reads every one), so only the store claim needs scoping
   ("of the stores read, only this one resolves the hash") or the vehicle stores need scanning.

4. **`NAMES.md:89-91` — "the only entries mentioning \"Serpente\" in the whole file" is an
   English-lane scan.** `serpente_banners` is built from `uiloc["pairs"].get(0, {})`, i.e. language
   0 only, while the text says "the whole file". The result happens to survive a full scan — I
   checked all 11 lanes and the same two hashes (`0x749CD88C`, `0xED2B9C80`) are the only ones
   whose text contains "Serpente" (in 10 of the 11 lanes) — but a string present only in another
   translation would have been missed, so the wording outruns the code.

5. **`NAMES.md:43-44`, `:139`, `:146` — the two "measured absences" are assertions, and one
   contradicts §7.** The map icon is not measured by the script at all (the payload has no
   map-icon census; only `vehicle_icons` and `store` are counted). My own path search finds no
   `map`+`icon/marker` texture, so the claim is plausible, but it is not what the card measured.
   The HUD row is worse: "**no carrier** … no `.gfx` references the name hash" uses the absence of
   a *static* reference to conclude no HUD name, yet the doc itself says the drop menu's binding
   is code-side and data-driven (`:120`, §7) — the same absence. §7's own line, "If a name toast
   exists, its source is UNKNOWN" (`:150`), directly contradicts the §2 "no carrier", and the
   tracker's "both stated as measured absences" inherits it.

6. **R11: typed values in the generated doc.** `NAMES.md:106` variant icons `18688`; `:137` "same
   size for every vehicle, so the format is one ADF-compressed texture"; `:112-113` "17 in store
   under a different naming scheme"; `:120` "The menu is data-driven: the movie asks for a string
   by id and a texture by path"; `:150` "the entity path that would supply one is empty". I
   checked the first: all **113** files in `textures/ui/vehicle_icons/` are exactly 18,688 B, so
   the number is true — but it is a literal in `to_md()`, not derived, so `--check` cannot catch
   it going stale (nor the 18,688 in the two other rows). The store claim is generalised from one
   path (`v0300_sportsmuscle_01`), and the store's own sizes are not uniform (11,072 ×10, 4,224 ×5,
   4,208 ×2) — naming, not size, is the point, but only one name was compared. The "movie asks for
   a string by id" sentence is a statement about Scaleform behaviour inferred from string absence
   (R5-adjacent); the doc does not decode a `.gfx` symbol.

7. **Minor: the language labels are positional.** `LANG_ORDER` is a hard-coded list mapped onto
   the store's lane index. The doc declares this as observation rather than a decoded enum (§7),
   which is honest, but the per-language table (`NAMES.md:16-26`) then presents labels the data
   does not confirm; a lane-order error would mislabel nine columns without failing `--check`.

## Spot-checks

| # | value in `NAMES.md` | where I verified it |
|---|---|---|
| 1 | name id `D2B46B49`, blurb `7B942DF2`, `SPORTS CAR` / `SPORTS CARS`, 11 languages, English `KERNER SERPENTE R` | `hash_jenkins("v0300_car_kensington_sportsmuscle_civilian_01")` = `0xD2B46B49` and `hash_jenkins(leaf + "_desc")` = `0x7B942DF2` (recomputed). Decoded `profile/online.stringlookup` with the script's own reader: both hashes resolve in **11** lanes, English `KERNER SERPENTE R` / "Kerner's top sports model…"; `0x91018BDA` = `SPORTS CAR`, `0x527AA70C` = `SPORTS CARS`; `0xA2B9F82C` resolves **0** lanes in the profile store (as claimed — it lives in the entity's store). |
| 2 | item record verbatim (`Name`/`UIName` 3535039305, `UIDescription` 2073308658, `UIType` 3, `UITypeDescription` 2432797658, `UIFlag` 5, `UIFlagDescription` 1383769868, `UIImagePath`/`UIVideoPath` = leaf, `UIDisplayOrder` 3, `RebelDropTimer` 1800, `Type` 1, `Rewardable` 1) and task 1361701860 Type 19 | `REBELDROP.json` `vanilla.items`: exactly one item with `Name` 3535039305; every field above matches field for field. `vanilla.tasks`: one task, `1361701860`, `Type 19`, rewarding that item. |
| 3 | icon 18,688 B, 113 files in `vehicle_icons`, 17 in `store`, variant icons 18,688, placeholder 18,688, store art 11,072 | `INDEX.jsonl`: 113 `.ddsc` under `textures/ui/vehicle_icons/`, **all** exactly 18,688 B (uniform, including the two variants and `placeholder`); 17 under `textures/ui/store/` (sizes 11,072 ×10 / 4,224 ×5 / 4,208 ×2), `v0300_sportsmuscle_01` = 11,072. Fleet icons: only **45** of the 80 `Type 1` items are `v0*`, but all **80** have an icon. |
| 4 | store sizes / languages: profile text blob **1,436,014 B**, 11 languages; `ui/ui_localization` **923,234 B**, 11 languages, **780,266 B** of text; entity `.stringlookup` **2226 B** patch / **2210 B** base, 1 entry, `A2B9F82C` = `Get in Vehicle` | Decoded both stores with `jc3strings.decode_stringlookup` on the live archives: profile 1,627,106 B / 11 lanes / text 1,436,014 B; ui_localization 923,234 B / 11 lanes / text 780,266 B. Entity file: patch 2226 B (1 pair per lane, `A2B9F82C` → `Get in Vehicle` in English), base 2210 B and **byte-identical to `Builds/test-091`'s copy**; but the Japanese lane differs between base and patch (issue 2). |
| 5 | `gfx references 0` — no `.gfx` contains the leaf, the hash or `vehicle_icons` | `INDEX.jsonl` has **59** `.gfx` rows, all under `ui/`, so the script's `ui/*.gfx` scan is exhaustive for the game; the scan returns 0 hits, matching the doc and the PASS line. |

## Not checked

- The tamper test (an edited `en` row → `FAIL: NAMES.md stale`) was not re-run; it writes into
  `Research/`, which this review may not do. The check's comparison path was read, and it is a
  straight `have != want` diff with exit 1.
- No game was launched. Which movie actually draws the drop-menu icon, and whether the map draws
  a vehicle-specific marker, remain code-side/UNKNOWN as the doc says.
