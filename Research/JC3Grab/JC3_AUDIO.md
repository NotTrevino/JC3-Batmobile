# JC3 vehicle audio system

G2-24. Every JC3 sound bank here is a **FMOD Designer/Ex event bank** (RIFF `FEV `, `FMT ` version 56 build 50), not an FMOD Studio bank: the event graph and one
FSB5 sample bank share one file. The donor pins **45 events** in `758 B` of `.ee.fmod_guids` across 3 banks
(`vehicles`, `character`, `effects`), 23 of them named by an `SAttachedEffect` /
`SDynamicAttachedEffect` in the `.epe`, and **45 of 45** are
found as an `EVTS` entry in one of those banks.

## 1. The event bank format (what is and is not in the file)

| fact | value |
|---|---|
| container | `RIFF`/`FEV `, `FMT ` version 56 build 50 |
| sections | `BEFX`, `CRVS`, `CTRS`, `EFIS`, `EVIS`, `EVTS`, `GBSS`, `IBSS`, `MBSS`, `MODS`, `MPGS`, `MUIS`, `PEFX`, `PMLS`, `PRIS`, `PRMS`, `RBSS`, `SCFX`, `SEFX`, `SNAS`, `SPIS`, `SUBS`, `TLNS`, `VCAS`, `WAIS`, `WAVS` |
| events | `EVTS` -> `LIST EVNT` -> `EVTB`; the body **starts with the 16-byte event GUID**, no name string |
| tunes | `TLNS` -> `LIST TMLN` -> `TLNB`, one per event: the body is the 16-byte tune GUID + the 16-byte GUID of the event that owns it (body offset 16) |
| sound instances | `WAIS` -> `WAIT` -> `LIST INST` -> `WAIB`: two 16-byte GUIDs per instance |
| waves | `WAVS` -> `WAV `: a u8 index + 16-byte GUID per sample slot |
| parameters | `PRMS` -> `PARM`: a GUID + a u16-length name |
| samples | `SND ` -> `FSB5` v1, 649 samples, 153,439,744 B of data |

**No event name or path is stored anywhere.** `EVTS` holds 2,333 printable runs of >= 3 chars (1,654 of >= 4), and every one is a chunk tag (`LIST`, `EVTS`, `EVTB`, `PRPS`, `PROP`) or binary noise: 0 of the 29 donor role names occurs in the section. The one name table in the file names
*samples*, not events. The GUID is the only event identity the game ships, so "event
path" below is the role name the donor `.epe` gives that GUID (or UNKNOWN where the
graph does not name it).

## 2. The three banks the donor uses

| bank | size | events | tunes | sound instances | waves | params | samples |
|---|---|---|---|---|---|---|---|
| `vehicles` | 210,781,376 | 257 | 257 | 1674 | 649 | 969 | 649 |
| `character` | 90,442,272 | 193 | 193 | 1938 | 976 | 262 | 976 |
| `effects` | 391,390,496 | 579 | 579 | 5310 | 1524 | 417 | 1524 |

## 3. Every event the donor pins

45 rows (`45` with a tune). `bank/ordinal` is the `EVTS` position in the bank that holds the GUID;
`role` is the `.epe` object name; `tune` is the `TLNS` index in the same bank (the tune
body carries the event GUID); `samples` stays UNKNOWN because no tune or sound-instance
body carries a wave GUID (0 / 649, §5).

| # | GUID | bank / ordinal | role (`.epe`) | tune | samples |
|---|---|---|---|---|---|
| 1 | `249a34b0-7997-424c-9f26-7b7eb0725e9c` | vehicles/43 | - | vehicles/230 | UNKNOWN |
| 2 | `a5d32c2e-6107-6045-bee4-c912599dacef` | vehicles/169 | `exhaust_upgrade_tjump_trail` (S), `exhaust_upgrade_tjump` (S) | vehicles/141 | UNKNOWN |
| 3 | `fd69c63c-84e6-fa43-b067-7eae99a59ce1` | vehicles/255 | `horn` (S) | vehicles/122 | UNKNOWN |
| 4 | `30d9ab54-baf7-5e44-ad67-22a72de44ad3` | vehicles/53 | - | vehicles/119 | UNKNOWN |
| 5 | `3e448c6d-61c1-5844-867d-06d741b7dd24` | vehicles/66 | `GearChange` (S) | vehicles/87 | UNKNOWN |
| 6 | `fe79719b-76fd-fb41-aed9-34ca185f5f4e` | vehicles/256 | - | vehicles/42 | UNKNOWN |
| 7 | `aaf215ac-f374-ba46-9ebf-241263187d1c` | vehicles/176 | - | vehicles/161 | UNKNOWN |
| 8 | `54dbc78f-6b87-bf40-b8ec-722de700572d` | vehicles/90 | - | vehicles/127 | UNKNOWN |
| 9 | `f74ea43b-a8ac-4548-ad27-b92fd40a516d` | vehicles/249 | `exhaust_upgrade_nitrous` (S) | vehicles/30 | UNKNOWN |
| 10 | `5a579b55-5cbc-b646-9d31-28d88292853b` | vehicles/96 | - | vehicles/178 | UNKNOWN |
| 11 | `24d39df9-5b95-2648-a33e-d4c19a70df1a` | vehicles/44 | `in_water_move_sound` (S) | vehicles/118 | UNKNOWN |
| 12 | `100cbd8f-9b9f-8749-b853-632b33d167e9` | vehicles/15 | `ground_roughness_sound_attached` (S) | vehicles/0 | UNKNOWN |
| 13 | `40beca2e-743c-664b-8e96-c09e3049346a` | vehicles/69 | - | vehicles/151 | UNKNOWN |
| 14 | `500e1421-3174-f54c-8b9a-c8c0c74a5baa` | vehicles/84 | `DoorOpeningStart` (S) | vehicles/154 | UNKNOWN |
| 15 | `0738b38a-2b66-dd4d-8804-f35759b6227d` | vehicles/9 | - | vehicles/131 | UNKNOWN |
| 16 | `3f6d8338-69e6-314f-9205-665aedd19b71` | vehicles/68 | - | vehicles/241 | UNKNOWN |
| 17 | `b38ac356-c78e-d447-867d-992db0b56c97` | vehicles/180 | `sinking_sound` (S) | vehicles/51 | UNKNOWN |
| 18 | `1f867af8-6e96-9c4f-81dc-9cd7ae7969bb` | vehicles/36 | `chassis_spinning_sound` (S) | vehicles/90 | UNKNOWN |
| 19 | `905be2e5-2544-8045-a10b-6034fd27ff11` | vehicles/146 | `engine_running_sound` (S) | vehicles/5 | UNKNOWN |
| 20 | `f58a18f7-719a-c64a-8e71-8da234d84ef9` | vehicles/246 | `DoorClosingEnd` (S) | vehicles/223 | UNKNOWN |
| 21 | `8ffcfde3-ab6f-3040-b43b-fc353312c6e4` | vehicles/144 | - | vehicles/97 | UNKNOWN |
| 22 | `491adddf-c649-2248-9407-c7f4cce4a084` | vehicles/78 | - | vehicles/174 | UNKNOWN |
| 23 | `68fec033-7c41-be46-9a15-443f84a6f209` | vehicles/110 | - | vehicles/192 | UNKNOWN |
| 24 | `fcd1c7f8-8e09-1b4b-91fd-6f813819cad9` | vehicles/254 | - | vehicles/175 | UNKNOWN |
| 25 | `d87e18de-2eb5-d243-a398-7fb69ccf6638` | character/165 | `speedwind_sound_player` (S) | character/117 | UNKNOWN |
| 26 | `d8a4e0fb-2270-9a45-9b07-998820fbb487` | character/166 | `jump_air_whoosh_sound` (S) | character/30 | UNKNOWN |
| 27 | `5e3f7a6d-81a9-1a40-ae0c-871a65a9b50c` | effects/179 | - | effects/347 | UNKNOWN |
| 28 | `7bcce25f-c1ef-3142-941f-ba3108eaf3d2` | effects/261 | - | effects/495 | UNKNOWN |
| 29 | `b6467bf6-a5e6-064e-b95a-de72922d2c4a` | effects/415 | `dynamic_break_large` (SDynamic) | effects/22 | UNKNOWN |
| 30 | `a61f100e-e793-b04b-92a9-506c5f467283` | effects/373 | - | effects/334 | UNKNOWN |
| 31 | `fd665c9f-629f-c944-9b4a-17965cec1509` | effects/570 | `dynamic_break_taillight` (SDynamic), `dynamic_break_turnsignal` (SDynamic), `dynamic_break_window_sm` (SDynamic), `dynamic_break_window` (SDynamic) | effects/442 | UNKNOWN |
| 32 | `4eb19c73-dc19-f748-b679-75bb183e0408` | effects/146 | `damage_smoke` (S) | effects/113 | UNKNOWN |
| 33 | `94ad2147-2ce3-1f4c-bd51-ff324dba3de5` | effects/331 | - | effects/28 | UNKNOWN |
| 34 | `77009170-11ad-a949-a478-f9358d245bb7` | effects/245 | `dynamic_break_electric` (SDynamic), `dynamic_break_light_off` (SDynamic), `dynamic_break_light_on` (SDynamic) | effects/502 | UNKNOWN |
| 35 | `78a954b8-920f-1d4c-b1b4-03eacb16b90f` | effects/252 | - | effects/443 | UNKNOWN |
| 36 | `844fb573-5a8d-8a4e-b989-5276030657cc` | effects/278 | `fire_post_explosion` (S) | effects/213 | UNKNOWN |
| 37 | `deca52af-98bc-6349-b6a4-1a16df3f62f8` | effects/491 | `TireDestroyed` (SDynamic) | effects/79 | UNKNOWN |
| 38 | `d167a490-2252-4b4c-8662-8dcb27901f0c` | effects/464 | `explosion` (S) | effects/86 | UNKNOWN |
| 39 | `8bd22a32-bc56-dd46-9131-28279f02686e` | effects/304 | `dynamic_break_small` (SDynamic) | effects/537 | UNKNOWN |
| 40 | `f04a7623-759b-c342-970c-8b6e0d401154` | effects/533 | - | effects/251 | UNKNOWN |
| 41 | `1f4a53c2-bf65-e445-bff0-abef23484ae4` | effects/64 | `dynamic_break_medium` (SDynamic) | effects/458 | UNKNOWN |
| 42 | `55d6b34f-fc0c-5a4c-928a-6d9f494ecccb` | effects/160 | - | effects/260 | UNKNOWN |
| 43 | `650d4611-9965-024c-9daf-ce3e1f15ddb9` | effects/194 | - | effects/385 | UNKNOWN |
| 44 | `09fa9fa3-218e-3041-9029-b69b82b63768` | effects/20 | `water_explosion` (S) | effects/410 | UNKNOWN |
| 45 | `db007316-ebd7-ae4a-a849-612ef7c87ee6` | effects/484 | - | effects/128 | UNKNOWN |

All 45 of 45 GUIDs resolve to a tune index in their
bank. What `.ee.fmod_guids` *means* is not decoded - the file itself only shows
`version 1`, 3 bank names, 45 GUIDs and 0 trailing bytes - so calling it a "preload
list" is an inference. The `.epe` names 23 of the 45 GUIDs with 29 `Sound` objects
(23 distinct values); the other 22 appear in no `Sound` field of the decoded graph. Whether
that is a second, native consumer of the block is UNKNOWN (it is code, not data).

## 4. Parameters

| where | member | value |
|---|---|---|
| `LandAudio` (`v0300_car_kensington_sportsmuscle_land_audio.vmodc`) | `max_rpm` | 10000.0 |
| `LandAudio` (`v0300_car_kensington_sportsmuscle_land_audio.vmodc`) | `min_rpm` | 1000.0 |

`LandAudio` carries **2 members**, the only vehicle-side
audio parameters the donor modules expose. Whether they are the RPM window a particular
engine event is driven over is **UNKNOWN**: the next paragraph shows the event-to-parameter
edge is not decoded, so the names (`min_rpm` / `max_rpm`) are the only evidence.

The banks also carry 969 project parameters (49 distinct names), e.g. `(event angle)`, `Distance`, `Event Cone Angle`, `Intensity`, `PlayerIsDriving`, `Speed` ... - the mixer's
global parameter space. **Which event reads which parameter is not decoded**: the `PMLS`
mapping lists reference the parameter GUIDs but the event-to-parameter edge is not a
field this reader can resolve, so per-event parameter bindings are UNKNOWN.

## 5. Event -> tune -> sample: what the files give

| probe | result |
|---|---|
| tune bodies carrying their event GUID (`TLNB` body offset 16) | **257 / 257** |
| tune <-> event pairs, 1:1 | **True** |
| event bodies carrying their tune GUID (body offset 32) | **257 / 257** |
| donor GUIDs resolved to a tune index | **45 / 45** |
| `WAVS` GUIDs referenced by any other section | **0** of 649 |
| wave GUIDs inside any tune chunk | **0** of 649 |
| wave GUIDs inside any sound instance (`WAIT`) body | **0** of 649 |
| `TLNT` chunk tag in the bank | **0** |

So the **event -> tune** hop *is* stored, twice: the `TLNB` body repeats the owning
event GUID, and the event body repeats the tune GUID at offset 32. `TLNS` holds one tune
per event, the pairs are a 1:1 map, and all 45 donor GUIDs resolve. The chain stops one
hop later: **tune -> wave is not stored** - no tune chunk and no sound-instance body
contains a `WAVS` GUID (0 / 649). A build therefore knows the event and its tune, and
must pick the sample it
replaces by name and audition (`§6` lists them), exactly as test-060 did.

## 6. The sample bank

| fact | value |
|---|---|
| FSB5 version | 1 |
| samples | 649 |
| sample header bytes | 22,100 |
| name table | 23,792 B (21,196 B of names) |
| sample data | 153,439,744 B |
| rates | 48000 Hz |
| channels | 1, 2 |
| encodings | 16-bit Little Endian PCM |
| looped samples | 22 / 649 |
| vgmstream names == name table | True |

First samples (index, name, rate/ch, frames, loop):

| # | name | rate | ch | frames | loop |
|---|---|---|---|---|---|
| 1 | `jc3_veh_bmw_m5_start` | 48000 | 1 | 91182 | - |
| 2 | `jc3_veh_land_door_moderncar_openstart_01` | 48000 | 1 | 24394 | - |
| 3 | `jc3_veh_reverse_warning2_03` | 48000 | 1 | 23233 | - |
| 4 | `dumper_shutdown` | 48000 | 2 | 253071 | - |
| 5 | `jc3_veh_wheel_car_asphalt_skid_hvy_veh_light_loop` | 48000 | 1 | 103868 | - |
| 6 | `jc3_veh_land_doors_bus_modern_closestart_01` | 48000 | 1 | 41263 | - |
| 7 | `jc3_veh_door_tank_open_03` | 48000 | 1 | 29954 | - |
| 8 | `iceskid1` | 48000 | 1 | 36349 | - |
| 9 | `moped_loop_rpm_02_2` | 48000 | 1 | 69868 | - |
| 10 | `jc3_vehicle_horn_truck_06_loop` | 48000 | 1 | 50140 | 17341..50137 |
| 11 | `train_military_rail_click_02` | 48000 | 2 | 4027 | - |
| 12 | `jc3_veh_generic_undercrrg_impact_suspension_ronk_12` | 48000 | 1 | 27507 | - |

All 649 rows are in the JSON (`samples.list`). A loop state is only claimed where vgmstream reads a loop chunk from
the FSB5 header (22 samples); every other sample is a one-shot and
shows `-`. Those looped samples are the only places a start/loop pair can land.

## 7. Weapon sounds: `w602`, `w603`, `w618`, `w619`

| id | source | tune members | audio members in tune | `.fmod_guids` | events in | sound roles |
|---|---|---|---|---|---|---|
| `w602` | `w602_mediumtank_canon.wtunec` | 171 | 0 | **none** (no `.ee`) | - | - |
| `w603` | `w603_mediumtank_mgun.wtunec` | 171 | 0 | **none** (no `.ee`) | - | - |
| `w618` | `w618_sportsmuscle_missile.ee` | 155 | 0 | 10 over `weapons_preorder`, `effects` | effects | `fire` `84232d53-cea8-2d44-86a1-b92ff2402743`, `fire2` `84232d53-cea8-2d44-86a1-b92ff2402743`, `fire4` `84232d53-cea8-2d44-86a1-b92ff2402743`, `fire3` `84232d53-cea8-2d44-86a1-b92ff2402743` |
| `w619` | `w619_buggy_mgun.ee` | 171 | 0 | 12 over `weapons_preorder`, `effects` | effects | `fire_sound_combi` `53e8d43a-0f09-434b-bf92-4239ffd243a8` |

**`w602`/`w603` carry no sound at all.** They exist only as `.wtunec` (no `.ee`, no
`.fmod_guids`), and every one of their 171 tune members is damage/recoil/scatter/shake - no `sound`, `event`, `audio` or `wav` member. Their firing audio lives on the *vehicle*
that fires them; the medium tank's `.epe` carries `ReloadStart` (`55051774-e5bc-7348-a20c-9a8fdd3dabe8`) and `Fire` (`ef8f8aaa-f95b-7846-9c25-f0c8f4bab301`),
and `weapons.bank` ships the samples by name (`jc3_wpn_tank_cannon_loaded_02`,
`jc3_wpn_mntd_tank_cannon_medium_02`, ...). The weapon events are listed above with
their GUIDs, but their samples are **UNKNOWN** for the same measured reason as the car:
`tune -> wave` is not stored (vehicle bank 0 / 649; the weapon banks were not probed for
this card), so the `Done` clause's sample half is a stated UNKNOWN, not a missing list.

`w618`/`w619` are the opposite: each `.ee` has its own `.fmod_guids`
(`w618` 10 GUIDs, `w619` 12), and the `.epe` binds the fire event
to a `SAttachedEffect` (`fire`/`fire2..4` for `w618`, `fire_sound_combi` for `w619`) whose
`Sound` is the first GUID of that list. Those banks are `weapons_preorder` and `effects`,
not `vehicles`.

## 8. Horn and radio

| probe | result |
|---|---|
| donor `horn` role | `fd69c63c-84e6-fa43-b067-7eae99a59ce1` in `vehicles` |
| `horn` objects in the fleet | **178** in 178 vehicles, 19 distinct GUIDs |
| `radio` objects in the fleet | **0** |
| `Sound`-carrying objects / entities | 6659 / 232 (176 distinct roles) |

The horn is a **per-model attached effect**, carried as 19 distinct GUIDs over 178 objects, so removing it from the Batmobile is deleting one `SAttachedEffect` - and BmAK has no horn event at all
(`AUDIO_FEATURES.md`: group `horn`, **0 rows / 0 events**), so AUD-7 says remove it.
There is **no radio member on any of the 232 decoded
vehicles**, so no vehicle-side member has to be suppressed for AUD-7. Where JC3's radio
lives (music system, another graph, code) is **UNKNOWN** - this card did not decode it.

## 9. AUD-1...7 against the carriers

| code | BmAK source (G1-15) | JC3 carrier | status |
|---|---|---|---|
| AUD-1 | `engine` group, 18 events / 130 WEMs, RTPCs `REV_RPM`, `REV_Throttle`, `Speed`, `EngineHeat` | `engine_running_sound` attached effect + `LandAudio.min_rpm`/`max_rpm` | carrier exists; sample mapping UNKNOWN |
| AUD-2 | `afterburner` + `burnout` groups | `exhaust_upgrade_nitrous` (donor event) / `exhaust_upgrade_nitrous2` (donor graph object, **not a pinned event**) / `exhaust_upgrade_tjump*` (donor event) | carrier exists; test-060 swapped three samples |
| AUD-3 | `interior` group, 9 events / 22 WEMs | no cabin effect on the donor; the nearest is `speedwind_sound_player` | **named omission** unless a bank swap adds it |
| AUD-4 | `battle-mode` group, 30 events / 75 WEMs | no mode-switch event in the donor; D-2 decides if a second variant ships | deferred with D-2 |
| AUD-5 | `weapons` group, 3 events / 10 WEMs | weapon `.ee` `SAttachedEffect` + `weapons.bank` samples | carrier exists per weapon (§7) |
| AUD-6 | `impacts` + `movement` groups | `wheel_suspension_*` (donor graph object, **not a pinned event**), `ground_roughness_sound_attached` (donor event), `combined_wheel_default_sfx` (donor graph object, **not a pinned event**) | keep JC3's (named omission, as T-AU3 says) |
| AUD-7 | `horn` 0 rows; no radio | donor `horn` effect; **0 radio objects** | remove the horn for lore, no radio member to touch |

## 10. Ship routes

| route | possible | evidence |
|---|---|---|
| **a** sample swap inside a copy of vehicles.bank | yes | test-060 swapped the FSB5 PCM payloads in place (same byte size, metadata untouched) and the bank still parses and decodes (MODLOG §71, `Tools/scripts/_apply_audio.py`); the bank is loaded as a loose override at sound/fmod_banks/vehicles.bank with no .toc (MODLOG §71); every donor sample is 16-bit PCM at 48 kHz (census), so a replacement must be PCM16/48 kHz and exactly the original frame count |
| **b** a new bank + .fmod_guids | **no** | the banks are FMOD Designer/Ex FEV v56 build 50, not FMOD Studio: the events, tunes, parameters and DSP live in the FEV graph, and no .fev project ships; the entity pins events by GUID, and the GUID is authored in the FEV graph; a new bank would have to reproduce that graph; master.banklist is a plain 26-line text list (434 B), so the loader can be told about another file, but nothing here can author its contents |
| **c** mixed: vehicles.bank swaps for the car, weapons.bank swaps for the guns | yes | the four chosen weapons pin their own events in weapons_preorder/effects, and the weapon .ee carries the Sound GUID; weapons.bank holds 1228 named samples (names such as `jc3_wpn_tank_cannon_loaded_02`), so the same payload swap applies there |

**Recommendation: route a + c.** The event graph is not editable
from the shipped data (route b needs the FMOD Designer project), but the sample payloads
are swappable in place (proven in test-060) and the weapon banks work the same way. The
limit is that the *sample inside a tune* has to be chosen by name and audition, because
tune -> wave is not stored (§5); the event and its tune are known. That is what
test-060 did (spectral ranking of the engine suspects in MODLOG §70), not a new
limitation introduced here.

## 11. Reproduce / limits

`python Tools/scripts/jc3audio.py --write` regenerates both files; `--check` re-reads every
bank, the donor `.ee`, the four weapon sources and the 232 decoded graphs, re-runs the
649-sample vgmstream census (~30 s here) and compares byte for byte.
`--fast` skips the census (checks everything else). The census runs on the
`Working/Audio/jc3bank` copy only after its sha256 is checked against the archive entry
(sha256 match).

**UNKNOWNs.** (1) Tune -> wave: see §5 (event -> tune *is* stored). (2) Event name/path: not stored. (3) Which event reads which parameter: not resolved. (4) What the FEV's tune `TRNS`
transitions mean at runtime (loop points, cut points) - the marker names (`Start`,
`start1..4`) are readable, their semantics are code. (5) Whether a horn removal alone
silences the horn: the horn is a GUID-pinned event, so removing the object is the data
side; the input binding is code (Q-1).
