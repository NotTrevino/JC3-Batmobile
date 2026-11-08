# Standalone entity - can a new path load from the dropzone? (G2-27)

**Answer: yes to the *loading*, UNKNOWN to the *hash*.** A new entity path -
`editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_batmobile.ee` -
needs **no global registry edit** for the routes that name the entity by *path*: the
spawn tables store the entity as a full path string, and the one global entity table
is not a complete list - it covers the **base retail roster** (251
of 922 index leaves) but leaves out **163 of the 169** debug spawn records and
**13 of the 21** DLC production records,
and one of those DLC vehicles (the sport mech) is playable in retail - so a missing
record does not stop an entity loading.
The one route that names the entity by *hash* is the Rebel Drop item, and every shipped
vehicle drop points at a leaf that does have a record - so whether the game resolves a
*new* leaf from an item hash is **UNKNOWN** and is a Q-1 probe, not a file answer.

| question | answer | evidence |
|---|---|---|
| where an entity path/hash is registered | **17** file rows in 10 kinds | `TRAFFIC.json` scan (11,751 files / 7,719 MB) |
| does a global table list every entity? | no - 251/922 index leaves have a record | `global/entityregistry_gen.entityregc` |
| is a path reference expressible for a new leaf? | yes - spawn records hold the full `editor\entities\...ee` string | `settings/spawn_vehicle_defs.bin` (86 records) |
| does a hash reference resolve for a new leaf? | **UNKNOWN** - 0 shipped counter-examples | `profile/item.onlinec`, this doc §4 |
| what a standalone entity ships | one `.ee` (604 inner files, 10,737,057 B), `.toc` optional | `Builds/test-091` donor `.ee`, the mod's 20 `.ee` |
| decision D-6 | **standalone is the route with the fewest unknowns** | this doc §6 |

## 1. Every registration site, classified by key type

The census itself is G2-29's (a name + hash scan of 11,751 data files); what this card
adds is the **key type** per site, because the key type decides whether a new leaf can
be expressed without rewriting a table that is keyed by something we cannot compute:

| file | mount | kind | key type | a new path fits? |
|---|---|---|---|---|
| `settings/spawn_vehicle_defs.bin` | base | spawn table | path string | yes, as a new record |
| `locations/jc_prototype/mm320/train_test.blo` | patch | level rule | path string in a `.bl?` object | no |
| `locations/rom/wingsuit_course/wing20_logic.blo` | patch | level rule | path string in a `.bl?` object | no |
| `profile/item.onlinec` | base | Rebel Drop | 32-bit leaf hash | yes, a computable hash |
| `profile/item.onlinec` | patch | Rebel Drop | 32-bit leaf hash | yes, a computable hash |
| `profile/task.onlinec` | base | task table | leaf string in a task key | no |
| `profile/task.onlinec` | patch | task table | leaf string in a task key | no |
| `global/frontend_global.blo` | patch | frontend | hash/name in the frontend list | no |
| `global/entityregistry_gen.entityregc` | base | entity registry | leaf + 32-bit hash + asset paths | UNKNOWN |
| `global/entityregistry_gen.entityregc` | patch | entity registry | leaf + 32-bit hash + asset paths | UNKNOWN |
| `profile/online.stringlookup` | base | localisation | hash only | optional, for a label |
| `profile/online.stringlookup` | patch | localisation | hash only | optional, for a label |
| `patchmetadata.bin` | patch | patch metadata | file hash, patch bookkeeping | no |
| `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.ee.toc` | patch | self | its own `.epe`/`.toc` | no |
| `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.epe` | patch | self | its own `.epe`/`.toc` | no |
| `dlc/mech_land_assault/editor/entities/jc_weapons/05_stationary/w506_sam_blackhand_heavycontroldrone/dlc2_sam_bh_controldrone_02.ee` | dlc | other | name or hash in another table | - |
| `dlc/mech_land_assault/editor/entities/jc_weapons/05_stationary/w506_sam_blackhand_heavycontroldrone/dlc2_sam_bh_controldrone_04.ee` | dlc | other | name or hash in another table | - |

Rows with `0` name hits are 32-bit hash coincidences and are not used for any claim
(G2-29 says the same). The four sites that matter:

* **`settings/spawn_vehicle_defs.bin`** - a record is `entity` (full path string) +
  `tags` + `name`. A new path is a **new record in an overridden copy**; nothing global
  is rewritten.
* **`profile/item.onlinec`** (Rebel Drop) - the record's `Name` is the 32-bit Jenkins
  hash of the leaf (G2-26). The hash is computable, the *resolution* is the question.
* **`global/entityregistry_gen.entityregc`** - the global entity table, 33,003,365 B base +
  39,220,585 B patch. §3 shows it is not a complete list.
* **`profile/task.onlinec`**, the two level `CVehicleRule`s and `frontend_global.blo` -
  the donor is named there for its *vanilla* identity (chop-shop task, level rules,
  frontend entry). A new leaf simply has none of them, which is the desired state.

## 2. What the global entity registry actually is

`global/entityregistry_gen.entityregc` is not ADF and not a plain string list: it is a tagged stream. The donor's
record, byte for byte, is

```
base  offset 7,376,079  leaf_len  45  tail 8c863a7d01496bb4d2502586
patch offset 13,461,069  leaf_len  45  tail 8c863a7d01496bb4d2502586
```

i.e. `03 <len16> <leaf>` followed by the leaf's 32-bit hash
(`01496bb4` little-endian) - the
same `D2B46B49` G2-29 searched for. Each record also carries that entity's asset paths:

| mount | bytes | tag-03 strings | path strings | `C*` class names | leaf-like | of which index leaves | vehicles | donor records |
|---|---|---|---|---|---|---|---|---|
| base | 33,003,365 | 381,985 | 56,173 | 29,079 | 6,526 | 232 | 157 | 1 |
| patch | 39,220,585 | 454,351 | 67,037 | 35,088 | 6,988 | 251 | 158 | 1 |

Path extensions inside the records:
`.eff` 81,531, `.ctune` 23,977, `.vmod` 11,753, `.etune` 1,211, `.wtune` 980, `.ftune` 539, `.model_xml` 527, `.vehicle_deform_xml` 511 -
asset dependencies (effects, tunes, generated modules), not a spawn list.

## 3. What the registry covers - and why a missing record is not fatal

The index carries **922** distinct `.ee` leaves. The registry, base
and patch together, holds **7005** no-slash strings, of which
**251** are index entity leaves - so
**671 shipped entities have no record at all**, e.g.
`air_conditioner01_small`, `air_conditioner2_ac01`, `air_conditioner2_ac02`, `air_ducting_pieces_a_outlet_small_001`, `ammo_box_bullet_spewer_single`, `ammo_caches_cache_03_crate`. Of the
233 vehicle entities in `PARTS_TABLE.jsonl`, 158
have a record and **75 do not** (`v0000_car_autostraad_oldjeep_debug`, `v0001_car_autostraad_armoredtruck_debug`, `v0003_car_autostraad_racinghothatch_debug`, `v0005_car_autostraad_minetruck_debug`).

The gap splits three ways, and the split is the answer:

* **The base retail roster is fully registered.** `settings/spawn_vehicle_defs.bin`
  has 86 records and **86**
  of them carry a registry record.
* **The debug builds are the unregistered mass.** The
  3 `spawn_vehicle_proto_defs.bin` tables hold
  169 records, **163** of them unregistered - the `*_debug`
  entities.
* **But DLC production is not.** The 5 DLC `spawn_vehicle_defs.bin` tables
  hold 21 records, **13** unregistered, and those include
  vehicles the player actually drives (`v0806_car_na_sportmech_01`,
  `v0600_car_urga_armoredjeep_blackhand_01`).

The third bullet is the decisive one: a retail-playable DLC vehicle with **no record**
means the registry cannot be a hard gate for *loading* an entity - it is a bake of the
base roster's assets. What actually references a spawnable entity is the spawn table:

| spawn table | mount | bytes | `.ee` records | of which unregistered | path record |
|---|---|---|---|---|---|
| `dlc/bavarium_sea_heist/settings/spawn_vehicle_defs.bin` | dlc | 781 | 2 | 1 | full path string |
| `dlc/bavarium_sea_heist/settings/spawn_vehicle_proto_defs.bin` | dlc | 291 | 1 | 1 | full path string |
| `dlc/mech_land_assault/settings/spawn_vehicle_defs.bin` | dlc | 4,894 | 16 | 11 | full path string |
| `dlc/v0300_preorder/settings/spawn_vehicle_defs.bin` | dlc | 437 | 1 | 0 | full path string |
| `dlc/v0604_preorder/settings/spawn_vehicle_defs.bin` | dlc | 387 | 1 | 0 | full path string |
| `dlc/v0805_sportmech/settings/spawn_vehicle_defs.bin` | dlc | 314 | 1 | 1 | full path string |
| `settings/spawn_vehicle_defs.bin` | base | 27,513 | 86 | 0 | full path string |
| `settings/spawn_vehicle_proto_defs.bin` | base | 16,410 | 79 | 75 | full path string |
| `settings/spawn_vehicle_proto_defs.bin` | patch | 18,374 | 89 | 87 | full path string |

**101 of 196 distinct spawn leaves are
referenced by path with no registry record**: `spawner_mech_enemy_cannon`, `spawner_mech_enemy_minigun`, `spawner_mech_friendly_cannon`, `spawner_mech_friendly_minigun`, `v0000_car_autostraad_oldjeep_debug` …
So the reference that matters for a *load* is the path string in the table above, and it
is available for a new leaf.

## 4. So can a new path load? The evidence, in order of strength

1. **The dropzone is enumerated, not read from a list.** A repacked `.ee` at a vanilla
   VFS path is applied by the game (in-game test-003, `MODLOG` §14), i.e. the dropzone
   directory is searched for a path whose archive entry also exists. A new path is the
   same lookup with every archive missing it.
2. **The `.ee` is self-contained.** The donor's `.ee` is an AAF around a SARC with
   **604** inner files (`.rbm` 198, `.ddsc` 153, `.effc` 74, `.trim` 60, `.lod` 59 ...), including its own `.epe`, `.stringlookup` and `.fmod_guids`.
   Nothing in it points at a sibling VFS file that would have to be renamed.
3. **Inner names are independent of the outer leaf.** The shipped mod's
   `editor/entities/jc_vehicles/03_sea/v1704_boat_na_lightpatrol/v1704_boat_na_lightpatrol_civic_police_01.ee` (a *boat* path) contains
   `editor/entities/jc_environments/structures/modern/playground_kit/merry_go_boom_01.epe`
   - a playground prop - so the container does not care what the outer file is called.
4. **The `.ee.toc` is optional**: the mod ships **20** `.ee` with
   **0** `.toc` files. (Our own build writes one; the donor's has
   506 entries against 604 SARC entries, so it is not a full
   directory either.)
5. **No shipped counter-example.** All **20** mod `.ee` files are at
   **vanilla paths** (20/20 in the index, 0 new), and so are all our builds. The
   genuinely-new-entity mod (Meme Vehicle Pack) is still unexamined (`MODLOG` line 1090)
   - so the *new path itself* has never been demonstrated on this project.

Points 1-4 make a new path **structurally** loadable. Point 5 is why the answer is
"yes, derived" and not "yes, proven". The one step the files do not decide is the
**hash**: the drop item's `Name` is a hash of the leaf, and the only table that could
turn a hash into a path is the registry of §3, which is incomplete. Two readings survive:

* the game hashes VFS paths at startup and the registry is only a cache - then a new
  leaf resolves and the drop works;
* the registry *is* the hash table - then a new leaf needs a record we cannot write.

**Q-1 probe (one variable):** ship the new-path `.ee` + one drop item whose `Name` is
`hash('v0300_car_kensington_sportsmuscle_batmobile')`, and see whether the item appears and spawns. Everything else in
this card is already answered (see `REBELDROP.md` §7 for the item fields).

## 5. What a standalone entity needs on disk

Measured off the donor `.ee` (`Builds/test-091/v0300_car_kensington_sportsmuscle_civilian_01.ee`, 10,737,057 B):

| item | count / value |
|---|---|
| one `.ee` (AAF + SARC) | 10,737,057 B |
| inner files | 604 |
| &nbsp;&nbsp;`.rbm` | 198 |
| &nbsp;&nbsp;`.ddsc` | 153 |
| &nbsp;&nbsp;`.effc` | 74 |
| &nbsp;&nbsp;`.trim` | 60 |
| &nbsp;&nbsp;`.lod` | 59 |
| &nbsp;&nbsp;`.vmodc` | 31 |
| &nbsp;&nbsp;`.ctunec` | 18 |
| &nbsp;&nbsp;`.pfxc` | 4 |
| &nbsp;&nbsp;`.etunec` | 2 |
| &nbsp;&nbsp;`.fmod_guids` | 1 |
| top-level dirs | models 363, effects 188, editor 52, textures 1 |
| its own `.epe` | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.epe` |
| `.toc` | present (506 entries) - **optional**, see §4.4 |
| `.stringlookup` | 1 inside the `.ee` (hash-only, G2-32) |

So the **minimum** for a standalone Batmobile is:

1. `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/
   v0300_car_kensington_sportsmuscle_batmobile.ee` - the donor's AAF, content unchanged or rebuilt, at a new leaf;
2. **one reference** so anything can ask for it:
   * a record in an overridden `settings/spawn_vehicle_defs.bin` (path string) - the
     route with no unknown, or
   * a record in `profile/item.onlinec` with `Name` = `hash('v0300_car_kensington_sportsmuscle_batmobile')` - the player-
     facing route, pending the Q-1 probe;
3. **optionally** a name/icon: a `.stringlookup` entry and a `ui/store` `.ddsc` (G2-32),
   which only affect the label, never the load.

Nothing else: no `global/` edit, no `settings/spawn_budget_pools.bin` edit (that names
*tables*, not vehicles), no `frontend_global.blo` edit (it names the vanilla entity and
would be wrong for a standalone one).

## 6. What this means for D-6

| route | traffic copies | registry edits | remaining unknown |
|---|---|---|---|
| replace `civilian_01` | **yes** - it is in the ground spawn table with 13 tags, 1 of 41
  traffic selectors matches (G2-29) | 0 | none for the load; lore break is certain |
| standalone `.ee` + drop item | no | 0 for the path; **UNKNOWN** for the hash | the Q-1
  probe of §4 |
| standalone `.ee` + spawn-table record | no | 0 | whether the engine honours an
  overridden `settings/*.bin` (G2-29's own UNKNOWN) |

**Recommendation: standalone.** It removes the lore break (MOD-5, WLD-8) at the cost of
one probe, and every file-level requirement it adds is already measured above.

## 7. UNKNOWNs

1. **Hash resolution for a new leaf** (§4). No file decides it; one drop item answers it.
2. **Why 671 entities are unregistered.** The record set
   looks like "entities with generated module dependencies" (the asset paths above), but
   the criterion is native. UNKNOWN, and it does not affect the verdict.
3. **Whether a replaced `settings/spawn_vehicle_defs.bin` is honoured** from the dropzone
   without a hash change - G2-29's open question, unchanged here.
4. **Whether the entity registry must gain a record for the drop route.** Same as 1, from
   the writer's side: we have no writer for a 39 MB tagged stream and did not attempt one.
5. **The `.toc`** - the mod ships none and works, but whether the game ever prefers it
   when present (eetoc's hypothesis) is not settled by these files.

## 8. Files and commands

```
python Tools/scripts/jc3standalone.py --write    # this report + STANDALONE.json
python Tools/scripts/jc3standalone.py --check    # re-derive and compare
```

Inputs: `INDEX.jsonl`, `global/entityregistry_gen.entityregc` (base + patch, extracted to
`standalone\` under `_JC3grab`), the 9 spawn
tables, `PARTS_TABLE.jsonl`, `TRAFFIC.json` (G2-29's census), `REBELDROP.json` (G2-26),
the donor `.ee` in `Builds/test-091`, and the shipped Rebel-Drop mod's 20 `.ee`.
