# Assumption challenge — backlog card G2-27 (standalone entity)

Read-only pass over the finished card. What I read: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G2-27 card
(§7, line 757), its §12 row (line 1310), the MODLOG `G2-27 · Standalone entity — intended change`
and `— done` sections, the outputs `Research/JC3Grab/STANDALONE.md` (244 lines) + `STANDALONE.json`,
the generator `Tools/scripts/jc3standalone.py`, and what it reads: `INDEX.jsonl` (81,952 rows),
`E:/Modding/JustCause3/_grab/standalone/{base,patch}_entityregistry_gen.entityregc` (33,003,365 +
39,220,585 B), the 9 `spawn_*_defs.bin` tables, `PARTS_TABLE.jsonl`, `TRAFFIC.json`, `REBELDROP.json`,
`Builds/test-091/v0300_car_kensington_sportsmuscle_civilian_01.ee`, and the shipped Rebel-Drop mod
`Research/1456340180_Rebel-Drop-Mod-V5.3/`. Extra readers used for the tests below: `eetoc`
(AAF/SARC/.toc), `jc3grab`/`jc3index`, `rbmhdr.hash_jenkins`, and `Tools/GibbedSrc` source.

Constraints honoured: no game launched, nothing written into `D:/Games`, nothing committed, no
secret read, no file touched except this one. Game bytes were read through the existing readers.

The card's Done check re-run today (exit status captured without a pipe):

```
$ python Tools/scripts/jc3standalone.py --check
PASS: 17 registration rows | registry records 251/922 index leaves (158/233 vehicles) | 101
spawned-by-path leaves unregistered | mod 20 .ee / 0 .toc, 20 vanilla paths | donor .ee 604
inner files, json match True, md match True
exit=0
```

---

## VERDICT

**Two BROKEN, five WEAK, eight HOLDS.** The *loading* answer survives, and two of its legs are
stronger than the md argues: `.toc` is provably optional (232 shipped `.ee` have no `.toc` at all,
37 of them on the base mount) and the `.ee` is provably self-contained (619 shipped `.ee`, including
**82 vehicle `.ee`** — 81 DLC builds plus the 1 patch override), have no sibling `.epe` — so the
inner `.epe` is what loads). The
registry is also better characterised than the card says: **157 of the 158 non-debug base vehicle
leaves have a record and 0 of the 75 `*_debug` leaves do** — the registry is a base-retail bake, not
a gate, and 35 non-debug DLC vehicle leaves (drones, boats, blackhand variants) are unregistered too.

What is broken is (a) the one place the card quotes registry *bytes*, and (b) the shape of the probe
it recommends. `STANDALONE.md` §2 says the donor record is "`03 <len16> <leaf>` followed by the leaf's
32-bit hash (`01496bb4` little-endian) - the same `D2B46B49` G2-29 searched for". Those two numbers
are not the same number: `01496bb4` little-endian is `B46B4901`. The real leaf hash `49 6b b4 d2`
(`D2B46B49`) sits **one byte later**, after a `01` tag, and the generator reads the wrong four bytes
(`hash_after: 01496bb4`, `hash_value: 3026929921`). The template also only covers **610 of 691**
index-leaf records (88%); the rest are a different variant. And the "**Q-1 probe (one variable)**"
changes three things at once (a new VFS path, a new hash in the drop table, and donor content under a
foreign inner `.epe` name), so a null result cannot be attributed — while a genuinely single-variable
probe exists in the shipped data (an item hashing one of the 35 unregistered DLC leaves, no new `.ee`).

Two smaller but real gaps: the "route with no unknown" (`spawn_vehicle_defs.bin`) still needs a
*writer*, and the only one that exists is Gibbed's untried `ConvertProperty -i`; and "content
unchanged … at a new leaf" keeps an inner `.epe` name that deviates from a **52/52** invariant in
shipped entities, which the card's own counter-example does not test.

| # | assumption | verdict |
|---|---|---|
| C1 | a new path needs no global registry edit; a missing record does not stop a load | **WEAK** — coverage is real (157/158 non-debug base), but "the sport mech is playable in retail" is not in any file, and it is the load-bearing bullet |
| C2 | "158/233 vehicles have a record" frames the vehicle fleet | **WEAK** — 233 is the base `PARTS_TABLE` set; the index has **288** distinct vehicle leaves (232 base + 55 DLC + 1 patch), 169 with records |
| C3 | the record is `03 <len> <leaf>` + the leaf's hash, quoted as `01496bb4` = `D2B46B49` | **BROKEN** — the hash is at `end+5` (`49 6b b4 d2`), not `end+4`; the quoted value is `B46B4901`; the template holds 610/691 |
| C4 | the registry stores `hash(leaf)` next to the leaf | **HOLDS** — `hash_jenkins(donor leaf) = D2B46B49`, present as those 4 bytes |
| C5 | `Item.Name` is the 32-bit leaf hash, and no shipped vehicle drop points at an unregistered leaf | **HOLDS** — 80/80 `Name == hash(UIImagePath) == hash(entity leaf)`, 0 unregistered; new-leaf hash reproduces `443190071` |
| C6 | the 11 items that resolve to no `.ee` are not vehicles | **HOLDS** — all `UIType` 0 with empty/`placeholder` icons (`Type` 0/2) |
| C7 | spawn records hold the full `editor\entities\…ee` path string | **HOLDS** — base table uses backslashes, DLC tables use forward slashes; 86/86, 16/16, … |
| C8 | the 17 rows are "every registration site" | **WEAK** — 21 `spawn_*_defs.bin` kinds exist (`spawn_vehicle_premium_defs.bin` is a 44 B empty stub, so no practical miss); the census is donor-name-driven, not a table taxonomy |
| C9 | "a new record in an overridden copy" is "the route with no unknown" | **WEAK** — no project writer exists; the only writer is Gibbed's `ConvertProperty -i`, untried here, and the card never names the step |
| C10 | the `.ee.toc` is optional | **HOLDS (stronger than the card)** — 232 shipped `.ee` have no `.toc` sibling (195 DLC + 37 base, incl. 1 vehicle) |
| C11 | the donor `.toc` has 506 entries against 604 SARC entries | **HOLDS** — 506 / 604 reproduced; 506 of the 604 inner names are listed |
| C12 | the `.ee` is self-contained; nothing points at a sibling VFS file | **HOLDS (stronger than the card)** — 619 of 963 shipped `.ee` have no sibling `.epe`; the 82 vehicle `.ee` in that set are the 81 DLC builds + the 1 patch override |
| C13 | "content unchanged … at a new leaf" is safe (inner names may keep the donor leaf) | **WEAK** — 52/52 sampled shipped `.ee` name their inner `.epe` exactly `<outer leaf>.epe`; the card's boat example is a vanilla path that still has an archive sibling |
| C14 | the dropzone is enumerated, so a new path is the same lookup with every archive missing it | **HOLDS as labelled derivation** — the only evidence is in-game test-003; no disk artefact can settle it, and the card says "derived, not proven" |
| C15 | "**Q-1 probe (one variable)**" | **BROKEN** — three variables; a cheaper single-variable probe exists (C15) |

Counts: 8 HOLDS, 5 WEAK, 2 BROKEN.

---

## C1 — a new path needs no global registry edit. **WEAK**

`STANDALONE.md`, headline:

> **Answer: yes to the *loading*, UNKNOWN to the *hash*.** A new entity path … needs **no global
> registry edit** for the routes that name the entity by *path* … and one of those DLC vehicles (the
> sport mech) is playable in retail - so a missing record does not stop an entity loading.

The coverage numbers are right, and the split is sharper than the card states. Recomputing the two
registry blobs against the index leaves (my own `tag03` walker, not the script's cached JSON):

```
base vehicle leaves 232 | in base registry 157 | in patch registry 157
DLC  vehicle leaves  55 | in base registry   0 | in patch registry  11
patch vehicle leaf    1 | in patch registry  1
```

and the composition of the missing base 75:

```
base vehicle leaves 233  unregistered 75
last-token patterns: [('debug', 74), ('tank', 1)]
not debug/custom/preorder/signature: ['v4603_plane_urga_cargotransport_military_cargo_tank']
```

So the base registry is **157 of 158 non-debug base vehicle leaves (99.4%) and 0 of 75 `*_debug`
leaves**, which is a much better statement of "a bake of the base retail roster's assets" than the
md's "0 of 86 base spawn records" — and the DLC side is stronger evidence still: 35 *non-debug* DLC
vehicle leaves are unregistered, including ten drones, six boats and the blackhand variants:

```
unregistered DLC not debug: spawner_mech_enemy_cannon, spawner_mech_enemy_minigun,
  spawner_mech_friendly_cannon, spawner_mech_friendly_minigun,
  v0201_car_capstone_mediumtank_blackhand_01, v0600_car_urga_armoredjeep_blackhand_01,
  v0805_car_na_mech_civilian, v0805_car_na_mech_minigun, v0805_car_na_mech_rebel_minigun,
  v0805_car_na_mech_rebel_minigun_spawner, v0806_car_na_sportmech_01,
  v1200_boat_capstone_heavypatrol_blackhand_01, … v2900_drone_eden_gruntdrone_* (4),
  v2900_drone_eden_gruntdrone_military_01/02, v2901_drone_eden_elitedrone_military_01/02/03,
  v2903_drone_eden_transportdrone_military_01, v2905_drone_blackhand_gruntdrone_military_01,
  v2906_drone_blackhand_elitedrone_military_01, v3600_bike_urga_combatdirt_blackhand_01,
  v4600_plane_urga_privatepropeller_civilian_02, v4603_plane_urga_cargotransport_blackhand_mission_01
```

The problem is the step from *coverage* to *tolerance*. "The registry is incomplete" does not imply
"the engine ignores it" — the md knows this, and that is why it reaches for a counter-example. Its
counter-example is game knowledge, not file content: *"vehicles the player actually drives
(`v0806_car_na_sportmech_01`, …)"*. Nothing in the archive says a sport mech is drivable; what the
archive says is that the mech DLC's own production spawn table carries exactly one record and that
record is the unregistered leaf:

```
sportmech table strings: ['RTPC', 'Pvehicle|ground|mech',
  'dlc/v0805_sportmech/editor/entities/jc_vehicles/01_land/v0806_car_na_sportmech/v0806_car_na_sportmech_01.ee',
  'vehicle, sportmech', 'v0806_car_na_sportmech']
```

That is a *derivation* (DLC production spawn record → the DLC spawns it → it loads with no record),
and a good one, but it is one inference further from the bytes than the md's confident "the decisive
one". **WEAK**: every number in the argument is reproducible; the premise that turns coverage into
tolerance is not in the files, and the md does not label it that way. The Q-1 probe is still the
right answer.

## C2 — "158/233 vehicles" as the fleet. **WEAK**

The md says "Of the 233 vehicle entities in `PARTS_TABLE.jsonl`, 158 have a record and **75 do
not**", which is accurate for that file, and the tracker then compresses it to "158/233 vehicles".
The index has a bigger vehicle population:

```
index .ee rows 963          distinct .ee leaves 922
vehicle .ee rows 314        distinct vehicle leaves 288 = 232 base + 55 dlc + 1 patch
registry records on vehicle leaves 169 (157 base + 11 dlc + 1 patch)
DLC vehicle leaves 55, of which 44 unregistered (9 debug, 35 not)
```

`PARTS_TABLE.jsonl` is base-only, so 233 silently excludes the 55 DLC vehicles — the exact set that
supplies the card's decisive counter-example. The ratio that carries the argument is not 158/233 but
"**0 of 75 debug** base leaves and **0 of 55** DLC leaves in the base registry". **WEAK**: the
  number is true of its stated source and misleading as a fleet figure.

## C3 — the registry record template and its quoted hash. **BROKEN**

`STANDALONE.md` §2:

> i.e. `03 <len16> <leaf>` followed by the leaf's 32-bit hash (`01496bb4` little-endian) - the
> same `D2B46B49` G2-29 searched for.

Reading the donor record out of the two blobs directly:

```
== base len 33003365
at offset: 032d00            (tag 03, length 0x002d = 45)
declared len 45 string v0300_car_kensington_sportsmuscle_civilian_01 match True
next 16 bytes: 8c 86 3a 7d 01 49 6b b4 d2 50 25 86 e4 01 ff ff
leaf hash       : D2B46B49
```

`hash_jenkins("v0300_car_kensington_sportsmuscle_civilian_01") = D2B46B49`, and the bytes `49 6b b4
d2` are at `end+5`, not `end+4`: the tail is `<4 bytes> 01 <hash LE>`. `STANDALONE.json` records
`"hash_after": "01496bb4"` and `"hash_value": 3026929921` because `jc3standalone.registry_facts`
reads `blob[end+4:end+8]`:

```
next 16 bytes: 8c 86 3a 7d 01 49 6b b4 d2 50 25 86
labelled (end+4): 01 49 6b b4 = B46B4901     # 3026929921
actual   (end+5): 49 6b b4 d2 = D2B46B49     # 3535039305
```

So the md's parenthetical is internally contradictory (`01496bb4` ≠ `D2B46B49`), and the generator
that "decodes" the registry is reading the wrong four bytes — the structure was established by eye
from one record, not by an offset that reproduces. Scale test, over every record whose string is an
index `.ee` leaf:

```
+0: 0 matches   +4: 0 matches      (of 20,000 leaf-like strings tested)
+5: 277/317 (base)   333/374 (patch)   = 610/691 = 88.3%
```

and the 81 misses are a different variant — e.g. `38 c9 75 38 01 00 00 00 00 b9 d4 a6`, where the
slot at +5 is zero (`v4202_plane_capstone_fighterjet_military_01`,
`w111_assault_rifle_up_39_mag`, …). **BROKEN**: the quoted bytes are wrong, the reader is off by
one, and "leaf + hash" is an 88% template, not the format. The *idea* (a leaf is followed by its
hash) is right (C4); the md should not print a byte string it did not verify.

## C4 — the registry stores `hash(leaf)`. **HOLDS**

This is the useful half of C3 and it is confirmed: `hash_jenkins(leaf) = D2B46B49` and the 4 bytes
`49 6b b4 d2` sit immediately after the leaf's `01` tag, in both the base and the patch blob
(identical 12-byte tail `8c863a7d 01 496bb4d2 502586e4`). The `D2B46B49` G2-29 searched for is
therefore a leaf hash, not a path hash — and the path hash is different:

```
leaf hash       D2B46B49      (v0300_car_kensington_sportsmuscle_civilian_01)
full path hash  FC21B7E3      (editor/entities/…/v0300_…_civilian_01.ee)
```

That distinction matters for the Q-1 item hash (C5) and it is the one place the card got the hash
space exactly right.

## C5 — the drop item's `Name` is the leaf hash, and no shipped drop points at an unregistered leaf. **HOLDS**

Recomputed over all 196 vanilla items:

```
Name == hash(UIImagePath): 80 of 196
vehicle-style items 80
resolved to index leaf 80 | of those with NO registry record 0 | not in index 0
hash_jenkins('v0300_car_kensington_sportsmuscle_batmobile') = 1A6A8B37 = 443190071
```

So the 80 vehicle items are exactly the `UIType 3` rows, each `Name` hashes its own
`UIImagePath`, and for those 80 the `UIImagePath` is the entity leaf (that is what makes the
resolution possible). The recipe's `443190071` reproduces. The "0 shipped counter-examples" claim is
exact — and it is the reason the md's UNKNOWN is honest rather than lazy. One precision the md
should carry: the string that is hashed is the **bare leaf**, and it is stored in the item as
`UIImagePath`/`UIVideoPath` (the icon name), which equals the entity leaf only for vehicles. A
non-vehicle item's `Name` hashes something else entirely (`Name == hash(UIImagePath)` fails 116/196).

## C6 — the 11 unresolvable items are not vehicles. **HOLDS**

```
items without an .ee leaf hash: 11
 UIType 0 | UIImagePath ''           | Name 761188693
 UIType 0 | UIImagePath 'placeholder'| Name 1835714130
 … (9 more, all UIType 0, Type 0 except one Type 2)
UIType distribution: {0: 98, 1: 7, 2: 11, 3: 80}
```

All 11 carry no icon path (empty or `placeholder`), and all 80 `UIType 3` resolve. So "the resolution
is complete for vehicles" holds, and G2-26's 185/196 figure decomposes cleanly.

## C7 — a spawn record can express a new path. **HOLDS**

The base table's strings show the record shape the md describes (`entity` path + tags + leaf name),
and the separator convention differs by table — a real convention the md implies but never states:

```
'Pvehicle|ground|z80'
'editor\\entities\\jc_vehicles\\01_land\\v0402_car_mugello_vintagesuper\\…_civilian_z80_01.ee'
'vehicle,z80'
'v0402_car_mugello_vintagesuper_civilian_z80_01'
…
'Pvehicle|ground|mech'                                     (DLC table)
'dlc/v0805_sportmech/editor/entities/jc_vehicles/01_land/v0806_car_na_sportmech/…_01.ee'
```

and the count is not a regex artefact — `SPAWN_RE` matches exactly the printable strings containing
`entities` in every one of the 9 tables:

```
base spawn_vehicle_defs.bin      27,513 B  regex 86  strings-with-entities 86
base spawn_vehicle_proto_defs   16,410 B  regex 79  strings-with-entities 79
patch spawn_vehicle_proto_defs  18,374 B  regex 89  strings-with-entities 89
dlc mech spawn_vehicle_defs      4,894 B  regex 16  strings-with-entities 16
dlc bavarium / preorder / sportmech  …    regex  2/1/1/1, all equal
```

**HOLDS**: full paths are expressible, the backslash/forward-slash split is real (so a new record
must follow its table's convention, which the md should say), and the record count is not a scan
artefact.

## C8 — "17 registration rows" is every site. **WEAK**

All 17 rows resolve in the index (checked one by one, including the odd ones:
`locations/jc_prototype/mm320/train_test.blo`, `profile/online.stringlookup`, `patchmetadata.bin`,
`global/frontend_global.blo`). But the row set is "places the **donor** is named", while the table is
titled "where an entity path/hash is registered". The index carries 21 spawn-table kinds, not 2:

```
spawn_aircraft_defs, spawn_aircraft_premium_defs, spawn_aircraft_proto_defs, spawn_animals_defs,
spawn_boat_defs, spawn_boat_premium_defs, spawn_boat_proto_defs, spawn_civilian_defs,
spawn_combatant_defs, spawn_device_defs, spawn_effect_defs, spawn_encounter_defs,
spawn_prop_defs, spawn_road_decoration_defs, spawn_train_defs, spawn_vehicle_defs,
spawn_vehicle_premium_defs, spawn_vehicle_proto_defs, spawn_weapon_defs,
spawn_weapon_premium_defs, spawn_weapon_proto_defs
```

`spawn_vehicle_premium_defs.bin` is the one that could have bitten a Batmobile record: it exists,
but it is an empty stub, so there is no practical miss:

```
base settings/spawn_vehicle_premium_defs.bin 44 bytes, ee paths 0, strings ['RTPC']
```

**WEAK**: the census answers "where is the donor named" (correctly) and presents it as "every kind of
place an entity can be registered" (not established); the empty premium stub is the reassuring part
the md does not have.

## C9 — "a new record in an overridden copy" is the route with no unknown. **WEAK**

`STANDALONE.md` §6:

> | standalone `.ee` + spawn-table record | no | 0 | whether the engine honours an overridden
> `settings/*.bin` (G2-29's own UNKNOWN) |

Zero *registry* edits, yes — but the step has to be *written*, and nothing in the project can write
it. `spawn_vehicle_defs.bin` is a property container (`RTPC 01 00 00 00` header, `27,513 B`), and the
project's readers are read-only:

```
Tools/scripts/rtpcdump.py:  "Read-only; prints to stdout."
Tools/scripts/jc3adf.py:    428 lines, grep 'write|wb' → no match (reader only)
Tools/scripts/jc3rebeldrop.py: "Inputs, all read-only:"  (its only `wb` writes Research JSON)
Tools/scripts/jc3standalone.py / jc3traffic.py: read only
```

A writer does exist, third-party, and the md never names it: `Tools/Gibbed/Gibbed.JustCause3.ConvertProperty.exe`
advertises `-i input_xml [output_bin]` and `Program.cs:291` calls `propertyFile.Serialize(output)`.
So the gate is not architectural — it is an untried tool and an unstated step, on both routes (the
drop item `profile/item.onlinec` has no encoder anywhere in the project at all; G2-26 is a read
half by design). **WEAK**: the card's recommendation ("standalone … at the cost of one probe") hides
a build step it has not costed, and "0 remaining unknown" is true only of the *engine* question.

## C10 — the `.ee.toc` is optional. **HOLDS (stronger than the card)**

The card argues from the shipped mod (20 `.ee`, 0 `.toc`). The archive settles it outright:

```
index .ee 963   .ee.toc 731
.ee without a sibling .toc in the index: 232   (dlc 195, editor/base 37)
vehicle .ee 314, without .toc 82
base-mount .ee without .toc 37, incl.
  editor/entities/jc_vehicles/02_air/v2602_helicopter_urga_lightassault/…_custom_mm230.ee
  editor/entities/jc_weapons/…/*_mag.ee (many)
  editor/entities/dlc/parachute_skins/para002_skin_flame.ee
```

232 shipped entities — one of them a vehicle on the base mount — carry no `.toc` at all, so the
`.toc` cannot be required. The md's weaker evidence (a mod at vanilla paths) happens to be right.

## C11 — donor `.toc` 506 entries against 604 SARC entries. **HOLDS**

```
Builds/test-091/v0300_car_kensington_sportsmuscle_civilian_01.ee   10,737,057 B
inner files 604   .toc entries 506   inner names present in the .toc: 506 of 604
```

Exact. (It also means 98 inner files — 16% — are not in the `.toc`, which is why the `.toc` cannot
be a complete directory either; the card says this.)

## C12 — the `.ee` is self-contained; nothing points at a sibling VFS file. **HOLDS (stronger than the card)**

The card's evidence is the donor's 604 inner files. The archive has the decisive version:

```
.ee 963 | with sibling .epe 344 | without 619
vehicle .ee 314 | with sibling .epe 232 (all base) | without 82 (all DLC)
```

82 vehicle `.ee` (81 DLC builds + the patch override) have **no** sibling `.epe`, and 50 of my
52-entity sample had none either. So the entity's own `.epe` inside the AAF/SARC is what loads, and a new leaf needs no sibling
files. The md's §4.2 sentence ("Nothing in it points at a sibling VFS file that would have to be
renamed") is therefore true for `.epe`/`.stringlookup` — but see C13 for the part it glosses.

## C13 — "content unchanged … at a new leaf" is safe. **WEAK**

`STANDALONE.md` §5:

> 1. `editor/entities/jc_vehicles/01_land/…/v0300_car_kensington_sportsmuscle_batmobile.ee` - the
>    donor's AAF, content unchanged or rebuilt, at a new leaf;

and §4.3, the evidence for it:

> the shipped mod's `…v1704_boat_na_lightpatrol_civic_police_01.ee` (a *boat* path) contains
> `…playground_kit/merry_go_boom_01.epe` - a playground prop - so the container does not care what
> the outer file is called.

The container part is true (I re-read that file: 23 inner files, `.epe`
`merry_go_boom_01.epe`, `.fmod_guids` `merry_go_boom_01.ee.fmod_guids`, plus
`graphs/usable_object.stringlookup`). But that example cannot test what the md uses it for: the mod
sits at a **vanilla** path whose archive sibling `.epe` exists, so if the engine opens
`<outer leaf>.epe` from the VFS it would find the *vanilla boat* `.epe` and the mod would still work.
The shipped corpus points the other way:

```
sampled shipped .ee 52 (50 with no sibling .epe)  →  inner .epe name == <outer leaf>.epe : 52 / 52
donor: 1 inner .epe, named v0300_car_kensington_sportsmuscle_civilian_01.epe
donor payload: full VFS path occurs 3× (inner names), leaf 4×; 349 of 604 inner names mention the leaf
```

So "content unchanged at a new leaf" leaves an inner `.epe` named after the *old* leaf, in a corpus
where 52/52 shipped entities keep the two equal and the one counter-example is non-discriminating.
**WEAK**: the card's stated basis ("inner names are independent") is a container property, not a
load-path finding; the cheap fix (rename the inner `.epe`/`.stringlookup`/`.fmod_guids` to the new
leaf, or Q-1 both ways) is not mentioned.

## C14 — the dropzone is enumerated, not read from a list. **HOLDS as labelled derivation**

The only evidence is in-game (`MODLOG` §14, test-003: a repacked `.ee` at a vanilla path is applied),
and no artefact on disk can settle it. The card states the status correctly — "the answer is 'yes,
derived' and not 'yes, proven'" — and its reason (a new path is the same lookup with every archive
missing it) is a sound statement of the hypothesis. Nothing to break; the caveat is that this step
is untestable without the game, which the card already says.

## C15 — "**Q-1 probe (one variable)**". **BROKEN**

`STANDALONE.md` §4:

> **Q-1 probe (one variable):** ship the new-path `.ee` + one drop item whose `Name` is
> `hash('v0300_car_kensington_sportsmuscle_batmobile')`, and see whether the item appears and spawns.

Three novel things change at once:

1. a VFS path that no archive contains (the load question),
2. an item `Name` that no shipped table contains (the hash-resolution question),
3. donor content under a foreign inner `.epe` name (C13), i.e. a container the corpus has no
   precedent for.

If the item never appears, nothing is learned: the hash may have failed to resolve, the path may have
failed to load, or the renamed inner `.epe` may have failed. R13 ("one variable per in-game probe")
is not met, and the md calls it met.

There is a genuinely single-variable probe in the shipped data, and it costs no new entity. 35
non-debug DLC vehicle leaves are unregistered *and have an `.ee` in the index*, e.g.
`v2900_drone_eden_gruntdrone_military_01`. A drop item whose `Name` hashes **that existing leaf**
tests the hash→load route with the entity already on disk and nothing else changed: if the item
spawns, the registry is not the hash table (the card's first reading), and the new path becomes a pure
load question; if it does not, the registry reading wins and the standalone drop route is dead
before anyone builds a `.ee`. That is the probe the card should have named.

---

## What this changes (for the card owner, not done here)

1. **`STANDALONE.md` §2 / `STANDALONE.json` — fix the record bytes.** The tail is
   `<4 bytes> 01 <hash LE>`; the leaf hash is at `end+5` (`49 6b b4 d2` = `D2B46B49`), and
   `hash_after: 01496bb4` / `hash_value: 3026929921` in the JSON are the wrong four bytes. State the
   88% coverage (610/691) instead of presenting a universal template.
2. **§3 — replace the "decisive" argument's numbers with the split that is in the files**: 157 of
   158 non-debug base vehicle leaves registered, 0 of 75 `*_debug`, 11 of 55 DLC; 35 non-debug DLC
   vehicle leaves unregistered. Keep the sport-mech sentence, but label "the player drives it" as
   outside knowledge.
3. **§5/§6 — cost the write step.** Both reference routes need a writer; the only one is Gibbed's
   `ConvertProperty -i` (untried), and `profile/item.onlinec` has none at all. "0 remaining unknown"
   and "at the cost of one probe" are not true as written.
4. **§4 — split the probe.** Use the unregistered-DLC-leaf item as the single-variable hash probe
   first; keep the new path as a separate probe; if content is not rebuilt, rename the inner `.epe`
   or Q-1 the naming question explicitly.
5. **§1 — say the census is donor-driven**, and that `spawn_vehicle_premium_defs.bin` exists but is
   an empty 44 B stub.

## What still holds

The load answer's structural legs, and the hash answer's honest UNKNOWN: full paths are expressible in
`spawn_vehicle_defs.bin` (base `\`, DLC `/`); `.toc` is optional (232 shipped `.ee` without one); the
`.ee` is self-contained (619 shipped `.ee`, incl. 82 vehicle builds, with no sibling `.epe`); the registry
stores `hash(leaf)` and covers the base retail roster, not every entity; 80/80 shipped vehicle drops
point at registered leaves and `hash(new leaf) = 443190071` reproduces; `spawn_budget_pools.bin` names
tables (37 strings, no vehicle leaves); `frontend_global.blo` names the donor leaf (present in the
95,864 B file); and the donor `.ee` is 10,737,057 B / 604 inner files with a 506-entry `.toc`.

## Appendix — commands used (all read-only)

```
python Tools/scripts/jc3standalone.py --check          # PASS, exit 0
python - <<PY  # registry: tag03 walk of the two blobs; hash offset scan (+0/+4/+5 over 20k + 691)
python - <<PY  # registry coverage vs INDEX leaves by mount; debug/non-debug split (75, 44)
python - <<PY  # spawn tables: SPAWN_RE vs every printable string in all 9 tables
python - <<PY  # spawn leaves vs registry; sportmech table strings; premium table (44 B stub)
python - <<PY  # REBELDROP.json: Name vs hash(UIImagePath)/hash(leaf); 80/80 + 11 UIType-0
python - <<PY  # INDEX: .ee vs .ee.toc; sibling .epe/.stringlookup coverage; mod 20/20 paths
python - <<PY  # eetoc: donor .ee 604 inner / 506 toc; 52-entity inner-.epe name sample
python - <<PY  # spawn_budget_pools.bin and frontend_global.blo string checks
grep -rn "wb|write" Tools/scripts/jc3adf.py Tools/scripts/rtpcdump.py   # no writer
grep -n "input_xml|Serialize" Tools/GibbedSrc/Gibbed.JustCause3.ConvertProperty/Program.cs
```

Nothing was written outside `Research/challenge/card-G2-27.md`; no game process was started; the
`D:/Games` install was only read through the existing readers (`jc3grab`), never written.
