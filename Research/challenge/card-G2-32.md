# Assumption challenge — G2-32 (`Names, icons and strings`)

Scope: the card (`GRAB_BACKLOG.md` "G2-32 · Names, icons and strings"), its §12 row, the MODLOG
blocks `G2-32 … intended change` / `… done` (lines 11413–11545) and the card's output
`Research/JC3Grab/NAMES.md` (+ `Tools/scripts/jc3strings.py`, which regenerates and byte-compares it).

Everything below was run read-only. Nothing was launched, no archive was written, nothing under
`D:\Games` was touched, nothing committed. Two of the checks need a file the card never opened:
the Scaleform movies are `CFX` + zlib at offset 8, so every "no `.gfx` contains …" statement in the
card was a search over *compressed* bytes; I inflated them **in memory only**. Where a read
reached outside the repo it is the project's own declared grab directory `E:\Modding\JustCause3\_grab`
(`JC3_GRAB` in `Tools/scripts/jc3hudwpn.py`), which already holds the decompiled HUD export
G2-25 used.

---

## VERDICT

**The store decode, the leaf-keyed name, the icon keying and the "no map icon" answer all hold and
in places are stronger than written. The two "no carrier" answers for the *display* of the name are
wrong, and so is the claim that the hash function reproduces every id.**

| # | Assumption | Verdict |
|---|---|---|
| A1 | `profile/online.stringlookup` is `Languages[N].SortedPairs[{Hash,TextOffset}]` + one shared NUL-separated `Text` blob, 11 languages | **HOLDS** (lane structure, sortedness, offset bounds and lane disjointness all check) |
| A2 | The 11 languages are `en, fr, de, it, es, ru, pl, ja, pt, es-MX, ar` | **HOLDS** for the order (content-verified 0–8, 10) / **WEAK** for `es` vs `es-MX` (lanes 4 and 9 are the same Spanish text) |
| A3 | The name id is `hash_jenkins(leaf)` = `D2B46B49` | **HOLDS** — and at fleet scale, not just for one item (80/80) |
| A4 | "45 of 45 vanilla vehicle items" — the fleet test | **WEAK** — the filter is `UIImagePath.startswith("v0")`, so the population is 45 cars out of 80 vehicles; all 80 pass |
| A5 | The icon is keyed by `UIImagePath` → `textures/ui/vehicle_icons/<leaf>.ddsc` | **HOLDS**, and it is no longer just a filename correlation: the movie holds the literal prefix |
| A6 | "No `.gfx` movie contains the leaf, the name hash or `vehicle_icons`" | **BROKEN** — 5 movies contain `vehicle_icons`/`vehicle_icon`, `comm_map` has `map_icon`, and **`pause.gfx` contains the donor's leaf** among 123 vehicle leaves (the card searched zlib-compressed bytes) |
| A7 | "vehicle HUD name — no carrier" | **BROKEN** — `hud.gfx` has `SetVehicleInfo`; the AS3 writes `MCI_vehicle.TXT_name.text = vehicle_name` (a bottom-left vehicle name panel) |
| A8 | "no per-vehicle map icon exists" | **HOLDS** — the map movie's marker classes contain no vehicle marker, and there is no marker texture directory |
| A9 | `ui/ui_localization` does not hold the name; only 2 Serpente banners | **HOLDS** (0 `KERNER`, exactly the 2 banner ids, donor hashes resolve nowhere) |
| A10 | `profile/online.stringlookup` is the **only** store that holds the name | **HOLDS** — across all 3,002 `.stringlookup` files |
| A11 | The entity carries one prompt, and "the name is looked up from the item, not from the entity" | **HOLDS** for the absence / **WEAK** for the mechanism (the HUD gets the string from native code, not provably from the item) |
| A12 | "`hash_jenkins` reproduces every id used here" | **BROKEN** — the leaf and `_desc` ids reproduce; `A2B9F82C`, `91018BDA`, `527AA70C` and the two banner ids do **not** |
| A13 | The build's own `.stringlookup` is 2210 B and byte-identical to the base copy | **HOLDS** (same SHA-256; patch differs only in decoded-identical strings) |
| A14 | `frontend_global.blo` names the entity, not the string | **HOLDS** |
| A15 | Item/type/flag/task ids (`3535039305`, `2073308658`, task `1361701860` Type 19) | **HOLDS** |
| A16 | The card's "every place the name/icon appears has a file + id" | **BROKEN** — the pause debug spawn list (123 leaves, `(V0300) STANDARD SPORT MUSCLE`) and the vehicle-unlock popup (`reward_vehicle_unlocked`, `img://vehicles/`) are display sites the doc does not list |

**Headline.** The *plumbing* answer is correct and better evidenced than the card claims: the leaf
name is the key, `profile/online.stringlookup` is the only store, the icon prefix is literally in
the store movie, and 80 of 80 vehicles agree. The *coverage* answer is wrong in the two places the
card gave as absences (HUD name, "no movie names it") because the check searched compressed bytes
and never opened the movie that actually lists vehicles. And one sentence in §7 — that the hash
function reproduces every id — is false for three of the ids the same document quotes.

---

## A1 — the string-store format

**Assumption (stated §1, and the whole `decode_stringlookup` basis):** a `StringLookup` is
`Languages[N]` each holding a `SortedPairs[]` of `{Hash, TextOffset}`, all `TextOffset`s indexing
one shared `Text` blob (`int8[]`, NUL-separated), 11 languages, blob 1,436,014 B.

**Test.** Re-decode and check the invariants the format implies: hashes sorted within a lane,
offsets inside the blob, lanes partitioning the blob (disjoint, ascending), and UTF-8 text starting
at each offset.

```
  languages: 11 text bytes: 1436014
   lang  0: 1385 pairs, hashes sorted: True, offsets in bounds: True, min/max off 0/105615
   lang  1: 1307 pairs, hashes sorted: True, offsets in bounds: True, min/max off 106686/235615
   lang  2: 1301 pairs, hashes sorted: True, offsets in bounds: True, min/max off 235623/352273
   lang  3: 1310 pairs, hashes sorted: True, offsets in bounds: True, min/max off 352280/465516
   lang  4: 1318 pairs, hashes sorted: True, offsets in bounds: True, min/max off 465523/581038
   lang  5: 1370 pairs, hashes sorted: True, offsets in bounds: True, min/max off 581044/778015
   lang  6: 1329 pairs, hashes sorted: True, offsets in bounds: True, min/max off 778026/897444
   lang  7: 1385 pairs, hashes sorted: True, offsets in bounds: True, min/max off 897454/1029819
   lang  8: 1307 pairs, hashes sorted: True, offsets in bounds: True, min/max off 1029832/1142923
   lang  9: 1320 pairs, hashes sorted: True, offsets in bounds: True, min/max off 1142929/1258608
   lang 10: 1380 pairs, hashes sorted: True, offsets in bounds: True, min/max off 1258614/1436007
```

**Result.** Every lane is sorted (it is a lookup, so it must be), every offset is in bounds, and
the lanes tile the blob without overlap (`max(lang n) < min(lang n+1)`), which is what "one shared
blob, one run per language" predicts and what a mis-decoded offset table would break. The
same name hash is present in all 11 lanes. Nothing in the store contradicts the format.

**Verdict: HOLDS.** (Byte offsets, not character indices — confirmed by the Japanese and Arabic
lanes decoding cleanly at the offsets given.)

---

## A2 — the language list and its order

**Assumption (§7, flagged by the card itself):** order is `en, fr, de, it, es, ru, pl, ja, pt,
es-MX, ar`, "read off the text itself — observation, not a decoded enum".

**Test.** Print the description for the donor's `_desc` hash out of each lane in index order.

```
lang  0: "Kerner's top sports model, boasting speeds in excess of 250 km/h. Tune…
lang  1: 'La meilleure voiture de sport jamais sortie des usines Kerner, capable…'
lang  2: 'Das Topmodell unter den Sportwagen von Kerner schafft über 250 km/h. D…'
lang  3: 'Modello di punta delle auto sportive Kerner, raggiunge una velocità ma…'
lang  4: 'El mejor deportivo de Kerner, que alcanza velocidades de más de 250 km…'
lang  5: 'Ведущая модель компании Kerner может похвастаться скоростью выше 250 к…'
lang  6: 'Topowy model sportowy stajni Kernera, szczycący się prędkością maksyma…'
lang  7: 'Kernerのトップスポーツモデルで、スピードは時速250キロを超える。…'
lang  8: 'O melhor modelo de carro esportivo de Kerner chega a velocidades de 25…'
lang  9: 'El mejor deportivo de Kerner, que alcanza velocidades de más de 250 km…'
lang 10: 'تتميز موديلات Kerner الرياضية الرائعة بسرعات جنونية تتجاوز 250 كم/ساعة…'
```

**Result.** The order is exactly as the card says — en, fr, de, it, es, ru, pl, ja, pt, **es**,
ar — so the *order* claim is safe and content-verified for ten of eleven lanes. The eleventh is the
problem: lanes 4 and 9 are the **same** Spanish sentence, character for character, so nothing in
this store distinguishes "es" from "es-MX". The card labels 9 `es-MX` and 4 `es`; that is an
assignment by convention, not an observation. (harmless for the build — both resolve the same text
— but the table presents a label the data does not carry.)

**Verdict: HOLDS (order), WEAK (the `es-MX` label).**

---

## A3 — the name id is the hash of the leaf, and it is the fleet rule

**Assumption (stated, and the card's one-line answer):** the string id is
`hash_jenkins("v0300_car_kensington_sportsmuscle_civilian_01") = D2B46B49`.

**Test 1.** Compute it, and resolve it in the store.

```
jenkins(name) = D2B46B49        (matches the documented id)
lang  0 name: 'KERNER SERPENTE R'
lang  1 name: 'KERNER SERPENTE R'
lang  2 name: 'KERNER SERPENTE R'
lang  9 name: 'KERNER SERPENTE R'
lang 10 name: 'KERNER SERPENTE R'
distinct texts for the name across languages: 1
```

**Test 2 — is it a rule or a one-off?** For every vanilla drop item whose `UIImagePath` is a `v…`
leaf, compare `Name`/`UIName` with `jenkins(UIImagePath)`:

```
vanilla items whose UIImagePath is a v-leaf: 80
   v0   items 45  named 45  iconed 45
   v1   items 11  named 11  iconed 11
   v2   items  9  named  9  iconed  9
   v3   items  9  named  9  iconed  9
   v4   items  6  named  6  iconed  6
vehicle leaves whose UIName does not resolve: []
  vehicle items: 80; Name == jenkins(UIImagePath): 80; UIName == jenkins(UIImagePath): 80
  jenkins(leaf+'_desc') = 7B942DF2 ; item UIDescription = 7B942DF2
```

**Result.** 80 of 80 – cars, bikes, boats, planes and helicopters – have `Name == UIName ==
jenkins(leaf)`, and the blurb is `jenkins(leaf + "_desc")`. The key really is the entity leaf; the
`KERNER SERPENTE R` name is not translated in any of the 11 languages.

**Verdict: HOLDS**, with better evidence than the card's own test (A4).

---

## A4 — "45 of 45" presented as the fleet

**Assumption (§4):** "The bridge is exact across the fleet's drop list: of **45** vanilla vehicle
items, **45** resolve their `UIName` … and **45** have a `textures/ui/vehicle_icons/<UIImagePath>.ddsc`."

**Test.** The filter in `jc3strings.py` is `it["UIImagePath"].startswith("v0")`. Count what that
excludes.

```
vanilla items: 196
items with a UIImagePath: 109
by prefix: {'11': 5, '12': 3, '13': 1, '14': 3, '15': 3, '16': 2, '17': 1, '21': 1, '31': 1,
            '32': 1, '33': 1, '70': 3, 'pl': 4, 'v0': 45, 'v1': 11, 'v2': 9, 'v3': 9, 'v4': 6}

  v0* (what the doc counts): 45 items, 45 named, 45 iconed
  everything else:           64 items, 64 named, 39 iconed
```

and per-vehicle-prefix, from A3's table: v0 45, v1 11, v2 9, v3 9, v4 6 → **80 vehicle items, all
80 named, all 80 iconed**. The 25 items without a `vehicle_icons` file are the ones whose
`UIImagePath` is a numeric weapon/prop id (`143`, `21`, `704`, …) or `placeholder` — they are not
vehicles and their icons live in `textures/ui/weapon_icons/`.

**Result.** The rule is true, and 35 more vehicles prove it. But the doc's number is a cropped
sample: `startswith("v0")` selects cars only, so a bike/boat/plane/helo that failed the rule would
have been invisible. It also contradicts the project's own G2-26 §12 row, which says "80 vanilla
vehicle drops". Label it 80 of 80 (or "45 of 45 cars, 80 of 80 vehicles").

**Verdict: WEAK** — the method is a sample-of-convenience; the conclusion is stronger than stated.

---

## A5 — the icon is keyed by `UIImagePath` (name correlation → behaviour)

**Assumption (§4, "how it is keyed"):** the icon file is `textures/ui/vehicle_icons/` + the
`UIImagePath` string + `.ddsc`.

**Test.** The doc's evidence is that the file's name *equals* the leaf (correlation). If the movie
builds the path, the literal prefix must be in the movie. Inflate the UI movies and look.

```
  ui/comm_store.gfx   patch  ['textures/ui/vehicle_icons']
      ...nst_drop_list_label_vehicle\x0bm_ImagePath\x1atextures/ui/vehicle_icons/\x0bm_VideoPath...
  ui/reward.gfx       patch  ['textures/ui/vehicle_icons']
      ..._icons/\nm_ItemIcon\x05.ddsc\x0eimg://weapons/\x1atextures/ui/vehicle_icons/\x0fimg://vehicles/...
  ui/rom.gfx          patch  ['textures/ui/vehicle_icons', 'placeholder']
      ...ures/ui/weapon_icons/\x0bm_ImagePath\x05.ddsc\x1atextures/ui/vehicle_icons/...
  ui/comm_store.gfx: img://vehicles/  img://weapons/  textures/ui/fallback.ddsc  .ddsc
```

**Result.** The path is assembled in the movie from a literal prefix (`textures/ui/vehicle_icons/`),
the extension (`.ddsc`) and a field (`m_ImagePath`), with `img://vehicles/` as the other form of
the same request and `textures/ui/fallback.ddsc` as the fallback. So the keying is **decoded**, not
inferred: the menu really does concatenate the leaf into that directory. Supporting numbers also
check: 113 vehicle icons, **all 113 exactly 18,688 B**, and 17 store icons at 3 sizes
(4,208 / 4,224 / 11,072).

**Verdict: HOLDS** (upgraded from inference to a decoded path).

---

## A6 — "no `.gfx` movie contains the leaf, the name hash or `vehicle_icons`"

**Assumption (§5, and §7 "the movies are compiled Scaleform and contain neither string (proven
above)"):** the scan of `ui/*.gfx` found nothing, so the movies do not name the vehicle.

**Test 1 — is the channel even readable?** Raw `hud.gfx` bytes and a positive control.

```
ui/hud.gfx patch: 386281 B; first 32 bytes: 4346580f91dd0e0078daec7d095c4e4ddfff5c4b7b5169d18284ca964a2509a5
  header ascii: b'CFX\x0f\x91\xdd\x0e\x00x\xda\xec}\t\\NM'
  zlib stream at 8 -> 974848 B decompressed
  contains 'SetVehicleInfo': True
```

On the raw bytes the same file yields 676 printable runs of noise
(`['KB"BDDR', '&Cn2pD', '7&o\\m:OG?', …]`) and **0** occurrences of `textures/`; after inflating,
974,848 B of real tags and strings. `SetVehicleInfo` — known present, because the decompiled AS3
carries it — is **invisible** before inflation. The doc's scan therefore had no sensitivity at all.

**Test 2 — inflate every `ui/*.gfx` (in memory) and search.**

```
  ui/comm_map.gfx     patch  90619 -> 200704  ['map_icon']
  ui/comm_store.gfx   patch  61956 -> 155648  ['vehicle_icons','vehicle_icon']
  ui/reward.gfx       patch 102145 -> 344064  ['vehicle_icons','vehicle_icon']
  ui/rom.gfx          patch  75681 -> 180224  ['vehicle_icons','vehicle_icon','placeholder']
  ui/hud.gfx          patch 386281 -> 974848  ['SetVehicleInfo','placeholder']
  ui/pause.gfx        patch  84962 -> 225280  ['leaf']
```

and the leaf in `pause.gfx` is not alone:

```
pause.gfx inflated 225280 B
  leaf occurrences 123, distinct 123
  Vxxxx labels: 101 ['(V0500) OLD MINI#v0500_car_solar_oldmini_civili', '(V0514) MODERN PICKUP(v0514_car_solar_modernpic', …]
  context: ['d_civilian_01', '(V0506) OLD TRACTOR&v0506_car_solar_oldtractor_civilian_01', 'LAND CIV AMBIENT',
            '(V0300) STANDARD SPORT MUSCLE-v0300_car_kensington_sportsmuscle_civilian_01',
            '(V0401) MUGELLO SUPERCAR,v0401_car_mugello_racingsupercar_civilian_01']
  spawn-ish strings: ['(V9999) MUGELLO HOT DLC"v9999_car_mugello_dlctestcar_debug',
                      'debug.complete.all.settlements', 'debugKeyDownHandler', 'debug_on_click', 'despawn.chars']
```

**Result.** Five movies contain `vehicle_icons`/`vehicle_icon`, `comm_map` contains `map_icon`, and
`ui/pause.gfx` contains the donor's leaf name inside a **debug vehicle-spawn list** (123 distinct
leaves, 101 `(Vxxxx)` display labels, debug key handlers). The claim as written is false, and it
was false at the time it was written: the search never decompressed the movie.

**Verdict: BROKEN.** Correct the sentence to: "the movie does not name the *display string*; the
store/reward/rom movies hold the icon prefix `textures/ui/vehicle_icons/` and the drop menu builds
the path from `UIImagePath`, and the pause menu's debug spawner lists 123 vehicle leaves including
this one."

---

## A7 — "vehicle HUD name — no carrier"

**Assumption (§2 and §7):** "**no carrier**: the donor's own `.stringlookup` holds only interaction
strings, and no `.gfx` references the name hash"; "JC3 shows no persistent vehicle name in the HUD
movie for this car (hud.gfx has no reference)".

**Test.** Inflate `ui/hud.gfx` and read the decompiled AS3 (the export G2-25 already uses).

```
$ grep -n "SetVehicleInfo" E:/Modding/JustCause3/_grab/hud/dec/scripts/hud.as
5228:      public function SetVehicleInfo(vehicle_name:String) : void
5230:         this.MCI_safe_area_bottom_left.MCI_vehicle.TXT_name.text = vehicle_name;

5015:            name_middle_x = this.MCI_safe_area_bottom_left.MCI_vehicle.TXT_name.x
                               + this.MCI_safe_area_bottom_left.MCI_vehicle.TXT_name.width / 2;
```

and the movie contains the symbol name (`SetVehicleInfo` → True after inflation, False on raw
bytes).

**Result.** There **is** a vehicle-name text field in the HUD: `MCI_safe_area_bottom_left.MCI_vehicle`
carries `TXT_name`, filled by `SetVehicleInfo(vehicle_name)`, and its width is used to centre the
chop-shop/rebel-drop info. So the HUD does display a vehicle name for whatever car the player is
in; the string's *source* is the caller. I searched every script for the caller:

```
script files: 724
  SetVehicleInfo   0 files
  VehicleInfo      0 files
  TXT_name         0 files
```

so the caller is native code (as with every other `hud.as` entry point) and the name must come from
data the code reads — the drop item's `UIName` is the only catalogue that holds it, but that is
inference.

**Verdict: BROKEN.** The "no carrier" is a missed carrier: the HUD names the vehicle through a
native call into `TXT_name`. What is genuinely unknown is *which* string the code passes.

---

## A8 — "no per-vehicle map icon exists"

**Assumption (§2, §4, §7):** the map has no per-vehicle marker; "the sprite set the map uses is
shared and its member names are UNKNOWN".

**Test.** The map movie, inflated, plus the texture tree.

```
comm_map.gfx: MAP ICON CLASSES, verbatim
   c_map_icon, c_map_icon_challenge, c_map_icon_collectible, c_map_icon_mission,
   c_map_icon_resupply_point, c_map_icon_settlement, c_map_icon_subsettlement,
   c_map_icon_unique_location, c_collectible_icon, c_poi_icon, c_resupply_point_icon,
   c_unique_location_icon, map_chaos_icon, map_icon_selection, map_icon_text_left,
   map_icon_undiscovered, map_icon_zoomed_out, map_fast_travel_flare, map_fast_travel_flares,
   MCI_chaos_icon, MCI_flare_icon, MCI_icon, MCI_icon_container, MCI_province_icon,
   MCI_settlement_icon, MCI_shrine_icon, challenge_icon, mission_icon, new_icon …

textures/ui/ subdirectories:
   {'collectibles': 2, 'dev_map_grid.ddsc': 1, 'fallback.ddsc': 1, 'load': 54, 'rom': 2,
    'store': 17, 'upgrades': 57, 'vehicle_icons': 113, 'weapon_icons': 112,
    'world_map.ddsc': 1, 'zoom1': 16, 'zoom2': 64, 'zoom3': 256}
```

**Result.** The map's marker vocabulary is challenge / collectible / mission / resupply / settlement
/ sub-settlement / unique location / POI / chaos / fast-travel / selection / undiscovered. **No
vehicle marker class exists**, and `textures/ui/` has no marker directory at all (`textures/ui/rom/`
holds 2 region icons: `cimagallo_icon`, `region11_icon`). So a Batmobile gets no map marker, and the
"member names are UNKNOWN" can now be replaced by the list above.

**Verdict: HOLDS** (and the UNKNOWN in §7 can be retired).

---

## A9 — `ui/ui_localization` does not hold the name

**Assumption (§3):** the HUD/UI store 923,234 B / 11 languages does not carry the name; its only
"Serpente" entries are the two Weaponized-Serpente banners.

**Test.** Decode it and search all lanes.

```
  bytes 923234, languages 11, text 780266 B
  Serpente     2 entries [('749CD88C', 'Add-on Weaponized Serpente available!'),
                          ('ED2B9C80', 'Add-on Weaponized Serpente available!')]
  SERPENTE     0 entries   Kerner 0 entries   KERNER 0 entries   Serpente R 0 entries
  donor name hash present in any language: False
  desc hash present: False
```

**Result.** Exactly as stated — and stronger: there is no `KERNER` string anywhere in the HUD/UI
store, so no vehicle name of this family lives there at all.

**Verdict: HOLDS.**

---

## A10 — `profile/online.stringlookup` is the only store that holds it

**Assumption (one-line answer, "which is the only store that holds it").**

**Test.** Read all 3,002 `.stringlookup` files in the index and search each for the name hash, the
desc hash and the leaf string.

```
  .stringlookup files: 3002
  HIT profile/online.stringlookup  base   namehash=True deschash=True leaf=False
  HIT profile/online.stringlookup  patch  namehash=True deschash=True leaf=False
```

**Result.** Two hits, both the same path in its two mounts; every other `.stringlookup` (per-movie,
per-mission, per-entity) holds neither hash. The claim is a real census, not a spot check.

**Verdict: HOLDS.**

---

## A11 — the entity's own `.stringlookup`, and "the name is looked up from the item"

**Assumption (§3):** the entity carries **one** entry, an interaction prompt `A2B9F82C` = `Get in
Vehicle`, and "the name is looked up from the item, not from the entity".

**Test.** Decode both mounts and the build copy.

```
base: 2210 B, languages 11, entries per lang [1,1,1,1,1,1,1,1,1,1,1], English {2730096684: 'Get in Vehicle'}
patch: 2226 B, languages 11, entries per lang [1,1,1,1,1,1,1,1,1,1,1], English {2730096684: 'Get in Vehicle'}
  base==patch decoded strings: True
  2730096684 = 0xA2B9F82C
```

**Result.** One entry, 11 lanes, identical text in base and patch, and the id is the one the doc
quotes. The absence of a name here is solid. What is *not* established is the causal half — "looked
up from the item": no script calls the HUD's `SetVehicleInfo` (A7), so the entity→item→name path is
an inference from "the item is the only place the name lives", which is A3+A10, not evidence of
which lookup the code performs.

**Verdict: HOLDS (absence), WEAK (mechanism).** Reword to "the name cannot come from the entity; the
only store holding it is `profile/online.stringlookup`, keyed by the same leaf the drop item uses".

---

## A12 — "`hash_jenkins` reproduces every id used here"

**Assumption (§7 last bullet):** "`hash_jenkins` reproduces every id used here (it is the same
function G2-26 proved on 196 items), but a collision-free guarantee … is UNKNOWN."

**Test.** Reproduce each id the document quotes from the text the document shows next to it.

```
jenkins(leaf)            = D2B46B49   == UIName 3535039305 / item Name        ✓
jenkins(leaf + '_desc')  = 7B942DF2   == UIDescription 2073308658             ✓
jenkins('Get in Vehicle')= D203ED45   != entity prompt  A2B9F82C              ✗
jenkins('SPORTS CAR')    = AFC7A919   != UITypeDescription 91018BDA           ✗
jenkins('SPORTS CARS')   = A1A1E99A   != UIFlagDescription 527AA70C           ✗
```

Over a hundred candidate spellings tried for the three (`sports car`, `SPORTS_CAR`, `type_sports_car`,
`ui_type_sports_car`, `vehicle_flag_sports_cars`, `SportsCar`, `get_in_vehicle`,
`prompt_get_in_vehicle`, `interaction_get_in_vehicle`, …) — no match:

```
91018BDA UITypeDescription SPORTS CAR       -> no candidate matches
527AA70C UIFlagDescription SPORTS CARS      -> no candidate matches
A2B9F82C entity prompt Get in Vehicle       -> no candidate matches
```

**Result.** The leaf-derived ids reproduce because the leaf *is* the key string. The other ids are
keys whose key string is something else entirely (an internal name, not the display text), so they
can only be *resolved*, never *reproduced* from the data shown. The sentence is therefore false for
five of the seven ids the document quotes — the three above plus the two banner ids (`749CD88C`,
`ED2B9C80`), which it presents the same way.

**Verdict: BROKEN.** Say instead: "the leaf-keyed ids are `hash_jenkins` and reproduce; the
type/flag/prompt ids are opaque keys that only resolve through the store."

**Why it matters for the build:** §6's rename recipe (add a pair at `hash_jenkins(new_leaf)`) is
safe because it only uses leaf-keyed ids. But if the Batmobile ever needs a new type/flag label,
"hash the text" is the wrong rule and would silently produce a dead id.

---

## A13 — "the build's own `.stringlookup` is 2210 B and byte-identical to the base copy"

**Test.** SHA-256 the build copy against both archive mounts.

```
  local file exists: True 2210
  base   2210 B sha=552edf4d7be736cc  build==copy: True
  patch  2226 B sha=f59be62b3a9efa96  build==copy: False
  build sha=552edf4d7be736cc
```

**Result.** Byte-identical to base; the patch copy differs in 16 bytes but decodes to the same single
entry in all 11 lanes (A11), so the mod loses nothing by shipping the base table.

**Verdict: HOLDS.**

---

## A14 — `frontend_global.blo` names the entity, not the string

**Test.**

```
frontend_global.blo patch: leaf True, name hash le False, be False
```

**Result.** Consistent with G2-29's census (one name hit, no hash hit) — the frontend holds the
entity string and labels the car through the item lookup, as the doc says.

**Verdict: HOLDS.**

---

## A15 — the item/type/flag/task ids

**Test.** Decode the donor's item out of `REBELDROP.json` and check the decimals against the hex the
doc prints.

```
   Name               3535039305 = 0xD2B46B49
   UIName             3535039305 = 0xD2B46B49
   UIDescription      2073308658 = 0x7B942DF2
   UITypeDescription  2432797658 = 0x91018BDA
   UIFlagDescription  1383769868 = 0x527AA70C
   UIFlag 5   UIType 3   Type 1   Rewardable 1   UIDisplayOrder 3   RebelDropTimer 1800
   UIVideoPath        v0300_car_kensington_sportsmuscle_civilian_01
   UIImagePath        v0300_car_kensington_sportsmuscle_civilian_01
   tasks rewarding the item: [(1361701860, 19)]
```

**Result.** Every decimal/hex pair in the doc matches, `UIImagePath` and `UIVideoPath` are both the
leaf (so the video is keyed the same way), and task `1361701860` (Type 19) is the one that rewards
it. These are read out of G2-26's decode, whose layout the G2-26 challenge covers — not re-derived
here.

**Verdict: HOLDS** (as a read of G2-26's output).

---

## A16 — the card's "every place the name/icon appears has a file + id"

**Assumption (card Done line, echoed by the doc's §2 table).**

**Test.** The places I found that the doc does not list:

| place | file | evidence |
|---|---|---|
| pause-menu **debug vehicle spawner** | `ui/pause.gfx` (patch, 225,280 B inflated) | 123 vehicle leaves, 101 `(Vxxxx)` labels; the donor's row is `(V0300) STANDARD SPORT MUSCLE-v0300_car_kensington_sportsmuscle_civilian_01`; the movie carries `debugKeyDownHandler`, `debug_on_click`, `debug.complete.all.settlements` |
| vehicle-unlock popup | `ui/reward.gfx` | `reward_vehicle_unlocked`, `img://vehicles/`, `textures/ui/vehicle_icons/`, `m_ItemIcon` + `.ddsc` — the popup that fires when task `1361701860` hands the car over draws its icon |
| drop/store rows | `ui/comm_store.gfx`, `ui/rom.gfx` | `const_drop_list_label_vehicle`, `m_ImagePath`, `textures/ui/vehicle_icons/`, `textures/ui/fallback.ddsc` |

**Result.** Two of these are *display* sites (the pause list shows a hardcoded "STANDARD SPORT
MUSCLE" label per leaf — not `KERNER SERPENTE R`; the reward popup shows the icon), and the pause
list is also a **spawn site**, which is a fact G2-29's census did not catch either (it searched the
compressed movies and found nothing). The card's "every place" is therefore not yet every place.

**Verdict: BROKEN** as an exhaustive claim; the listed rows themselves are correct.

---

## What this changes

* **Keep:** the store decode (A1), the leaf-keyed name and blurb (A3, A15), the icon keying — now
  decoded from the movies rather than correlated (A5), the "only store" census (A10), the HUD/UI
  store absence (A9), the byte-identical build copy (A13), the frontend behaviour (A14), and the
  no-map-icon answer, which can now cite the marker class list (A8).
* **Rewrite:** §5 entirely. "No `.gfx` contains the leaf / the hash / `vehicle_icons`" is false in
  all three parts for the raw byte reason: **the movies are `CFX` + zlib at offset 8**. After
  inflating, `comm_store`/`reward`/`rom` hold `textures/ui/vehicle_icons/`, `comm_map` holds
  `map_icon`, and `pause.gfx` holds the leaf among 123 others. Add the inflation step to
  `jc3strings.py` (five lines: `if b[:3] == b"CFX": b = zlib.decompressobj().decompress(b[8:])`)
  and a positive control (`SetVehicleInfo` in `hud.gfx`) so a future empty result is known to be a
  real absence.
* **Rewrite the HUD row:** the name *is* displayed — `hud.as:5230`
  `MCI_safe_area_bottom_left.MCI_vehicle.TXT_name.text = vehicle_name`, called through
  `SetVehicleInfo`, with no script caller. The open question is what string the native caller
  passes, not whether a carrier exists.
* **Fix §7's hash claim:** two ids reproduce (leaf, `_desc`); the type/flag/prompt/banner ids do
  not and are opaque keys.
* **Relabel the fleet test:** 80 of 80 vehicle items, not 45 of 45 — the current filter is
  `startswith("v0")`, i.e. cars only, and it silently disagrees with G2-26's own "80 vanilla
  vehicle drops".
* **Label the language table honestly:** order verified by content; `es` vs `es-MX` is an
  assignment, because lanes 4 and 9 carry the identical Spanish sentence.
* **Add the two display sites and the debug spawner** (A16) — the latter is also worth handing to
  G2-29/D-6, since it is a shipped, player-reachable way to spawn the donor without touching the
  traffic table.
