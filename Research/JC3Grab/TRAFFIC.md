# Traffic, AI and spawning of `v0300`

G2-29. **Answer: `v0300_car_kensington_sportsmuscle_civilian_01` is a civilian traffic vehicle, so replacing it puts AI-driven Batmobiles on the roads.** It has a record in the ground-vehicle spawn table (`settings/spawn_vehicle_defs.bin`) whose tag list `vehicle, ground, car, civilian, racing, modern, muscle, kensington, sports, unarmed, unarmored, ambient, liberated` satisfies 1 of the 41 tag selectors in the traffic-rule block of `global/global.blo` - `ambient,ground,car,liberated,-highend`; those rules spawn a driver seat with an AI behaviour tree, and the entity ships its own AI module. Only `civilian_01` is in that table, not the other `v0300` builds. **Lore break (MOD-5, WLD-8): decision D-6 must take the standalone route (G2-27).**

The full census is 17 files that name the donor out of 11751 scanned (7719 MB, tier A+B); the spawn sites are one spawn table, one Rebel Drop item, one chop-shop task key, two level `CVehicleRule` objects and one frontend list entry. What the tags *mean* and whether the engine's traffic picker reads them that way is `UNKNOWN` - that matcher is native code (§6).

## 1. Every file that names the donor

Scan: every index entry whose extension is one of `.bin, .bl, .blo, .btc, .ctunec, .defc, .destc, .ee, .effc, .entityregc, .epe, .gadfc, .gdc, .gsc, .lua, .mdic, .onlinec, .pfs, .pfxc, .physicsc, .revolutionc, .stringlookup, .toc, .trim, .vmodc, .wtunec` - **11751 files / 7719.5 MB** - read from the archives and searched for the ASCII name `v0300_car_kensington_sportsmuscle_civilian_01` and for the 32-bit Jenkins hash `D2B46B49` of that name in both byte orders. Tier B (`.bl, .blo, .ee`: levels, level logic, entity modules) is included.

| kind | file | mount | bytes | name hits | hash hits | confidence | what it is |
|---|---|---|---|---|---|---|---|
| spawn table | `settings/spawn_vehicle_defs.bin` | base | 27513 | 2 | 1 | name | a record in a spawn-definition table |
| level rule | `locations/jc_prototype/mm320/train_test.blo` | patch | 2292 | 1 | 0 | name | a CVehicleRule in a level's logic object |
| level rule | `locations/rom/wingsuit_course/wing20_logic.blo` | patch | 539192 | 1 | 0 | name | a CVehicleRule in a level's logic object |
| Rebel Drop | `profile/item.onlinec` | base | 52165 | 4 | 1 | name | an item in the Rebel Drop list |
| Rebel Drop | `profile/item.onlinec` | patch | 52204 | 4 | 1 | name | an item in the Rebel Drop list |
| task table | `profile/task.onlinec` | base | 167286 | 2 | 1 | name | a task key naming the vehicle (chop shop) |
| task table | `profile/task.onlinec` | patch | 167470 | 2 | 1 | name | a task key naming the vehicle (chop shop) |
| frontend | `global/frontend_global.blo` | patch | 95864 | 1 | 0 | name | named in the frontend's vehicle list |
| entity registry | `global/entityregistry_gen.entityregc` | base | 33003365 | 1 | 1 | name | lists the entity, not a spawn |
| entity registry | `global/entityregistry_gen.entityregc` | patch | 39220585 | 1 | 1 | name | lists the entity, not a spawn |
| localisation | `profile/online.stringlookup` | base | 1621250 | 0 | 1 | hash only (may be a coincidence) | name lookup only |
| localisation | `profile/online.stringlookup` | patch | 1627106 | 0 | 1 | hash only (may be a coincidence) | name lookup only |
| patch metadata | `patchmetadata.bin` | patch | 9227364 | 3 | 0 | name | lists the file as changed by the patch |
| self | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.ee.toc` | patch | 46192 | 3 | 0 | name | the entity's own file |
| self | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.epe` | patch | 109766 | 1 | 1 | name | the entity's own file |
| other | `dlc/mech_land_assault/editor/entities/jc_weapons/05_stationary/w506_sam_blackhand_heavycontroldrone/dlc2_sam_bh_controldrone_02.ee` | dlc | 4028000 | 0 | 1 | hash only (may be a coincidence) | unclassified |
| other | `dlc/mech_land_assault/editor/entities/jc_weapons/05_stationary/w506_sam_blackhand_heavycontroldrone/dlc2_sam_bh_controldrone_04.ee` | dlc | 4028000 | 0 | 1 | hash only (may be a coincidence) | unclassified |

**Not read:** 70201 files / 48.6 GB of media and navmesh types (`.hmddsc` 8296, `.nl` 2771, `.bank` 54, `.streampatch` 5600, `.bikc` 228) - none of them is a data table, and a level that names the donor is covered by tier B. The full exclusion census is in the JSON.

17 file rows (0 could not be read). Rows with 0 name hits are a 32-bit hash that happens to occur in the file - they are listed for completeness and are not used for any claim. Of the name hits, three are not spawn sites: the entity's own `.epe`, the entity registry (which lists every entity) and `patchmetadata.bin` (which lists the file as patched). Base and patch copies of the same path each get their own row.

## 2. The spawn table

`settings/spawn_vehicle_defs.bin` (base, 27513 B) is the ground-vehicle spawn table: **86 records**, each `entity path` + `tag list` + `name`. `settings/spawn_budget_pools.bin` names it as *Ground Vehicles*, alongside `spawn_aircraft_defs.bin`, `spawn_boat_defs.bin` and the rest, so this is the file the spawner draws ground vehicles from.

**A pool key is a sparse field, and the donor's record has none.** Only 8 of the 86 records carry a `a|b|c` key string in the same record, and every key that does occur occurs once: `vehicle|bavarium`, `vehicle|ground|civilian`, `vehicle|ground|commercial`, `vehicle|ground|military`, `vehicle|ground|militia`, `vehicle|ground|rebel`, `vehicle|ground|reward`, `vehicle|ground|z80`. So the key cannot be read as a group label (my first pass did exactly that and invented pools with 35 records in them), and **the donor's pool is `UNKNOWN`** - what selects it is the tag list, which is what §3 tests. The record layout beyond its three strings is not decoded here.

The donor's record, read out of the table (offset 23240):

| field | value |
|---|---|
| pool key | none in this record (UNKNOWN) |
| entity path | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.ee` |
| tags | `vehicle`, `ground`, `car`, `civilian`, `racing`, `modern`, `muscle`, `kensington`, `sports`, `unarmed`, `unarmored`, `ambient`, `liberated` |
| name | `v0300_car_kensington_sportsmuscle_civilian_01` |

Tag census over the 86 records: `vehicle` 63, `ground` 59, `unarmed` 51, `unarmored` 47, `ambient` 32, `car` 27, `modern` 26, `civilian` 25, `solar` 25, `old` 20, `global_neutral` 15, `oppressed` 15, `liberated` 14, `r03_outpost` 12 …

Each build of the chassis sits in exactly one table, and they are different tables: `civilian_01` here (the traffic table), the debug build in `settings/spawn_vehicle_proto_defs.bin` and the pre-order build in the DLC's own `dlc/v0300_preorder/settings/spawn_vehicle_defs.bin`. That matters for D-6: the *Batmobile* would inherit the civilian car's traffic slot **only because it replaces `civilian_01`**, not because the chassis is spawnable in general.

| spawn table | mount | records | pool keys | `v0300` records |
|---|---|---|---|---|
| `dlc/bavarium_sea_heist/settings/spawn_aircraft_defs.bin` | dlc | 8 | 2 | - |
| `dlc/bavarium_sea_heist/settings/spawn_boat_defs.bin` | dlc | 8 | 2 | - |
| `dlc/bavarium_sea_heist/settings/spawn_combatant_defs.bin` | dlc | 5 | 2 | - |
| `dlc/bavarium_sea_heist/settings/spawn_prop_defs.bin` | dlc | 3 | 1 | - |
| `dlc/bavarium_sea_heist/settings/spawn_vehicle_defs.bin` | dlc | 2 | 1 | - |
| `dlc/bavarium_sea_heist/settings/spawn_vehicle_proto_defs.bin` | dlc | 1 | 1 | - |
| `dlc/bavarium_sea_heist/settings/spawn_weapon_defs.bin` | dlc | 3 | 2 | - |
| `dlc/mech_land_assault/settings/spawn_aircraft_defs.bin` | dlc | 14 | 2 | - |
| `dlc/mech_land_assault/settings/spawn_boat_defs.bin` | dlc | 6 | 3 | - |
| `dlc/mech_land_assault/settings/spawn_combatant_defs.bin` | dlc | 39 | 1 | - |
| `dlc/mech_land_assault/settings/spawn_encounter_defs.bin` | dlc | 18 | 0 | - |
| `dlc/mech_land_assault/settings/spawn_prop_defs.bin` | dlc | 3 | 1 | - |
| `dlc/mech_land_assault/settings/spawn_vehicle_defs.bin` | dlc | 16 | 3 | - |
| `dlc/mech_land_assault/settings/spawn_weapon_defs.bin` | dlc | 12 | 2 | - |
| `dlc/sky_fortress/settings/spawn_aircraft_defs.bin` | dlc | 11 | 1 | - |
| `dlc/sky_fortress/settings/spawn_combatant_defs.bin` | dlc | 3 | 1 | - |
| `dlc/sky_fortress/settings/spawn_prop_defs.bin` | dlc | 4 | 0 | - |
| `dlc/sky_fortress/settings/spawn_weapon_defs.bin` | dlc | 7 | 2 | - |
| `dlc/v0300_preorder/settings/spawn_vehicle_defs.bin` | dlc | 1 | 1 | v0300_car_kensington_sportsmuscle_signature_preorder |
| `dlc/v0604_preorder/settings/spawn_vehicle_defs.bin` | dlc | 1 | 1 | - |
| `dlc/v0805_sportmech/settings/spawn_vehicle_defs.bin` | dlc | 1 | 1 | - |
| `dlc/v1401_preorder/settings/spawn_boat_defs.bin` | dlc | 1 | 1 | - |
| `dlc/w142_preorder/settings/spawn_weapon_defs.bin` | dlc | 1 | 0 | - |
| `dlc/w163_preorder/settings/spawn_weapon_defs.bin` | dlc | 1 | 0 | - |
| `dlc/w901_scorpiongun/settings/spawn_weapon_defs.bin` | dlc | 1 | 0 | - |
| `settings/spawn_aircraft_defs.bin` | patch | 29 | 5 | - |
| `settings/spawn_aircraft_premium_defs.bin` | base | 0 | 0 | - |
| `settings/spawn_aircraft_proto_defs.bin` | base | 0 | 0 | - |
| `settings/spawn_animals_defs.bin` | base | 6 | 1 | - |
| `settings/spawn_boat_defs.bin` | base | 18 | 3 | - |
| `settings/spawn_boat_premium_defs.bin` | base | 0 | 0 | - |
| `settings/spawn_boat_proto_defs.bin` | patch | 0 | 0 | - |
| `settings/spawn_civilian_defs.bin` | base | 135 | 14 | - |
| `settings/spawn_combatant_defs.bin` | base | 67 | 7 | - |
| `settings/spawn_device_defs.bin` | base | 3 | 0 | - |
| `settings/spawn_effect_defs.bin` | base | 39 | 0 | - |
| `settings/spawn_encounter_defs.bin` | base | 56 | 0 | - |
| `settings/spawn_prop_defs.bin` | patch | 114 | 0 | - |
| `settings/spawn_road_decoration_defs.bin` | base | 5 | 0 | - |
| `settings/spawn_train_defs.bin` | base | 11 | 0 | - |
| `settings/spawn_vehicle_defs.bin` | base | 86 | 8 | v0300_car_kensington_sportsmuscle_civilian_01 |
| `settings/spawn_vehicle_premium_defs.bin` | base | 0 | 0 | - |
| `settings/spawn_vehicle_proto_defs.bin` | patch | 89 | 3 | v0300_car_kensington_sportsmuscle_debug |
| `settings/spawn_weapon_defs.bin` | base | 65 | 1 | - |
| `settings/spawn_weapon_premium_defs.bin` | base | 0 | 0 | - |
| `settings/spawn_weapon_proto_defs.bin` | patch | 1 | 1 | - |

## 3. The traffic rules, and why this record is traffic

`global/global.blo` (79340 B) carries **31 traffic-rule names**, **41 tag selectors** (vehicle lists and driver-character lists), driver seats (Driver) and **10 AI behaviour-tree paths**. A rule there is a tag list plus a driver: e.g. the rebel tank rule pairs a vehicle selector with `character,rebel` / `grunt` / `Driver` / `ai/bts/enemies/01_shared/soldier_tank_driver.bts`. The numbered civilian rules carry no `Rule` suffix in the game's data (`03_CivilianCarLiberatedProvince`), so the census matches both spellings; 5 other `*Rule` objects in the same file are not traffic (`AmbienGoatRule`, `AmbientDeerRule`, `PCEncounterRule`, `PPCAmbientWildlifeRule`, `PPPCSprinkleRule`) and are excluded.

Testing the donor's tags against every selector (a selector matches when all of its plain tags are present and none of its `-tag` exclusions are):

| selector | next rule name in the file | requires | excludes | matches the donor? |
|---|---|---|---|---|
| `ambient,ground,car,liberated,-highend` | `03_CivilianCarLiberatedProvince` | ambient, ground, car, liberated | highend | **yes** |
| `ambient,ground,bike,liberated` | `04_CivilianBikeLiberatedProvince` | ambient, ground, bike, liberated | - | no (missing bike) |
| `character,civilian` | `06_CivilianBikeOppressedProvinceLiberatedSettlement` | character, civilian | - | no (missing character) |
| `character,civilian, -farmer, -servant` | `07b_HighEndOppressedProvinceLiberatedSettlement` | character, civilian | farmer, servant | no (missing character) |
| `ambient,ground,car, highend` | `07b_HighEndOppressedProvinceLiberatedSettlement` | ambient, ground, car, highend | - | no (missing highend) |

**1 of 41 selectors match**, and the match is a civilian *car* rule, not a faction or special one. The pairing of selector to rule name is positional (selector, then its rule name, then its driver list) and is labelled as such: the record layout of the file is not decoded, only its strings.

Rule names in the file, for context: `CAmbientTrafficRule`, `B03_RebelTankTrafficRule`, `11_TruckOutsideSettlementsTrafficRule`, `08_PoliceCarOutsideLiberatedSettlementsTrafficRule`, `B01_MilitaryBikerTrafficRule`, `MilitaryAmbientLowAltitudeAirTrafficRule`, `B01_MilitaryBuggyTrafficRule`, `B01_MilitaryJeepTrafficRule`, `B06_MilitaryWaterTrafficRule`, `B00_RebelBikerTrafficRule`, `04_CivilianBikeLiberatedProvince`, `02_CivilianBikeGlobalNeutral`, `B06_RebelWaterTrafficRule2`, `06_CivilianBikeOppressedProvinceLiberatedSettlement`, `03_CivilianCarLiberatedProvince`, `07b_HighEndOppressedProvinceLiberatedSettlement`, `NOW02_ProvinceOppressed_MilitaryBikeTrafficRule`, `99_OpenWorldAuthority_MilitaryTrafficRule`, `B00_RebelOldJeepTrafficRule`, `B00_RebelTechnicalJeepTrafficRule`, `01_CivilianCarGlobalNeutral`, `07_HighEndLiberatedProvince`, `12_MilitaryJeepTrafficRule`, `B00_RebelMountedGunnerJeepTrafficRule`, `09_CommercialAmbientInSettlementsTrafficRule`, `B05_MilitaryAmbientAirTrafficRule`, `10_CommercialAmbientOutsideSettlementsTrafficRule`, `NOW01_ProvinceOppressed_MilitaryTrafficRule`, `05_CivilianCarOppressedProvinceLiberatedSettlement`, `B02_MilitaryTankTrafficRule`, `CivilianAmbientLowAltitudeAirTrafficRule`.

## 4. The other spawn sites

| site | file | evidence |
|---|---|---|
| Rebel Drop item | `profile/item.onlinec` (patch, 52204 B) | the donor name appears 3× plus 1 key(s): `v0300_car_kensington_sportsmuscle_civilian_01_desc` - an item with a description key, so it is droppable by the player |
| chop-shop task | `profile/task.onlinec` (patch, 167470 B) | `chopshop_v0300_car_kensington_sportsmuscle_civilian_01` - a chop-shop task keyed on the vehicle |
| level vehicle rules | `locations/jc_prototype/mm320/train_test.blo`, `locations/rom/wingsuit_course/wing20_logic.blo` | `CVehicleRule` + `point.stunt` + the donor name in the level's logic object |
| frontend list | `global/frontend_global.blo` | the name sits in the frontend's padded string table |

No shipped *region* level places the donor: the tier-B scan read every `.bl`, `.blo` and `.ee` and found it in two course/prototype logic objects and the frontend only. So the world does not park this car anywhere - **the spawner is what puts it in the world**, which is exactly the case the card asks about.

## 5. What the tags say, counted

Of the 86 ground-vehicle records, **32 carry `ambient`** and **14 carry both `ambient` and `liberated`** - the donor is one of them; 0 carry `liberated` without `ambient`, and 10 carry a faction `*_traffic` tag instead (`mil_now_traffic`, `mil_auth_road_traffic`, `rebel_now_traffic`). So `ambient` is the civilian-traffic marker and `liberated` is the province condition, and the donor has both. The matching selector asks for exactly `ambient,ground,car,liberated` and excludes `highend` - which the donor is not tagged with.

## 6. What AI drives it, and what stays UNKNOWN

* **Proven.** The donor has a traffic-table record (§2); a civilian-car selector in the traffic-rule block is satisfied by its tags (§3); the traffic rules in that block spawn `Driver` seats bound to `ai/bts/...` behaviour trees, and the file also carries `AITrafficImpostorSystem`, `PCAITrafficImpostorSystem`; and the entity ships its own AI module(s): `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/ai/v0300_car_kensington_sportsmuscle_land_global_ai.vmodc` (3 module files in the entity's `modules/` tree).
* **UNKNOWN.** The tag matcher itself: no file in the archive states that a rule selecting `ambient,ground,car,liberated,-highend` takes records whose tags are a superset, and no script (`graphs/*.gsc`, `ai/bts/*.btc`) mentions these tags - the picker is native. Whether the impostor system reuses the same records, how often a province's traffic is re-rolled, and what each record's six numeric fields mean (offsets, weights?) are also UNKNOWN: the file's numeric block is not decoded, only its strings.
* **UNKNOWN.** Whether the two `CVehicleRule` levels would drag a Batmobile into their course logic at runtime (they name the donor, but nothing says when the rule fires).

## 7. What this means for the build

| route | what happens to traffic |
|---|---|
| replace `civilian_01` (current plan) | the Batmobile inherits the civilian car's traffic record: NPC-driven Batmobiles in liberated provinces = **lore break** (MOD-5, WLD-8) |
| standalone entity, unhooked from the table (G2-27) | no traffic record, so no NPC Batmobiles - and the chop-shop/drop keys are keyed on the donor's name, so they would have to be added for the new path |
| replace `civilian_01` **and** edit `spawn_vehicle_defs.bin` to drop/mark the record | needs a `settings/` override in the dropzone; whether the engine honours a replaced settings file without a hash change is `UNKNOWN` (G2-27's question) |

That third row is the decision D-6 actually owns; G2-29 only proves the record exists and that its tags select it into traffic.

## 8. Checks

| check | result |
|---|---|
| `python Tools/scripts/jc3traffic.py --check` | rebuilds both files and asserts the census, the donor's record and the tag match |
| files scanned | 11751 (7719.5 MB), tiers A+B |
| files naming the donor | 17 |
| spawn records | 86 (8 carry a pool key) |
| traffic rules / selectors | 31 / 41 |
| selectors the donor satisfies | 1 |

Every number here is regenerated from the archives; none is typed by hand.
