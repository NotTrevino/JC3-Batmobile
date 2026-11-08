# Keep audit: audio (T-AU1, T-AU2) and effects (T-FX1, T-FX2, T-FX5)

STATUS: done. Every number below is re-derived from the shipped tables, not asserted:

| source | path | what it supplies |
|---|---|---|
| `AUDIO_MAP.json` | `Research/BatmobileGrab/AUDIO_MAP.json` `events[]`, `summary` | 361 rows, 118 event ids, 447 media, per-row bank + status |
| `AUDIO_MAP.md` | `Research/BatmobileGrab/AUDIO_MAP.md` | same, readable, bank table |
| `AUDIO_FEATURES.md` / `AUDIO_FEATURES.json` | `Research/BatmobileGrab/` | feature groups (sonar 18, tracker 4, lock-on-ui 23, battle-mode 120 …) |
| JC3 audio graph | `Research/JC3Grab/JC3_AUDIO.md` §3, §4 | the 45 pinned GUIDs, **23 named `.epe` roles**, `LandAudio` 2 members |
| `FX_TABLE.jsonl` | `Research/JC3Grab/FX_TABLE.jsonl` | 57,187 rows over 1,533 paths, 955 `EffectRTSystem`, 338 under `/jc_vehicles/` |
| `LEAGER_G3E` / `LEDGER-g3src` | `Research/BatmobileGrab/LEDGER_G3E.md:31`, `tmp/freebuff/reports/LEDGER-g3src.md:14,197` | T-FX5's 74 `.effc` (holds) and its 23 (UNKNOWN) |

The five rows audited: `T-AU1` (`LandAudio` module, `min_rpm` 1000 / `max_rpm` 10000, keep),
`T-AU2` (engine start/loop, `sound/fmod_banks/vehicles.bank`, swapped at test-060, keep),
`T-FX1` (`all_effects[].effect` = `window_break`/`taillight_break`/`electric_break` vs donor `window_break`, `taillight_break`, `electric_break`, keep),
`T-FX2` (`burn_engine`, `burn_roof`, `burn_base`, keep),
`T-FX5` (74 `.effc` in the donor `.ee`, 23 unreferenced by the 51 rows, keep).

## 1. The classification rule (stated, so it can be attacked)

JC3 stores **no event name** in its FMOD bank — the `EVTS` body starts with a 16-byte GUID
(`Research/JC3Grab/JC3_AUDIO.md` §1), and 0 of the 29 `.epe` role names occurs in that
section. So a BmAK event can only be called *matched* if a JC3 entity (`SAttachedEffect` /
`SDynamicAttachedEffect`) binds a GUID to a **role of the same meaning**. Exactly **23 roles**
are named (45 GUIDs, 29 `Sound` objects); the `vehicles` bank itself holds **257 events** and
only 23 are named, so the other 234 are code-fired and unnamed.

| verdict | rule |
|---|---|
| **lore-exact** | one of the 23 JC3 roles means the same sound at the same moment as the BmAK event (engine loop, gear change, surface/tyre loop, jump whoosh, explosion) |
| **approximate** | JC3 has the same *family* (a role with a wider meaning, or the bank/event class exists) but no same-meaning role — e.g. four body mechanisms collapse onto the two door roles |
| **missing** | no JC3 role and no JC3 mechanism to fire it (no transformation state, no sonar, no lock-on tone, no tracker) |
| **dialogue** | BmAK narrative/cinematic voice, not vehicle audio — counted inside the 361 but not a translation target |

An event is **"merely the donor's"** when BmAK's own table is the only place it exists: the 21
dialogue/cinematic names (Joker/BatWing/chapter dialogue) and the 23 unreferenced donor
`.effc` in T-FX5. Everything else is BmAK behaviour that JC3 has to carry somehow.

## 2. The count (361 rows over 118 event ids, 447 media)

| bucket | names | rows | share of 361 | share of 332 vehicle rows |
|---|---:|---:|---:|---:|
| lore-exact | 9 | **27** | 7.5% | 8.1% |
| approximate | 40 | **124** | 34.3% | 37.3% |
| missing | 48 | **181** | 50.1% | 54.5% |
| dialogue (out of vehicle scope) | 21 | 29 | 8.0% | — |
| **total** | **118** | **361** | 100% | 332 |

Media: **447** distinct media entries (508 entries, 18,176,431 B) across 27 banks
(34,409,121 B). **90 rows / 26 ids** resolve to `missing-bank` — 10 banks are not on disk, so
their audio is **UNKNOWN in the grab** (a data gap, not a JC3 gap):
`BML_Batmobile_Subjective`, `BML_Impacts`, `BML_Sonar`, `CHR_BatmanAlerts`,
`CHR_BatmanDisruptor`, `OBJ_Rolling_Objects`, `UI_InGame`, `VEH_Tank_Heavy`,
`VEH_Tank_Missiles`, `VFX_Tank_Explosion`.

### The 27 lore-exact rows (named carrier per row)

| BmAK event | rows | JC3 role (GUID) | why exact |
|---|---:|---|---|
| `Play_Batmobile_Idle` | 2 | `engine_running_sound` `905be2e5` (vehicles/146) | engine loop, same state |
| `Play_Batmobile_MK2_Idle` | 2 | same | MK2 is the same state on the second bank |
| `Play_BML_Persistent_idles` | 4 | same | the persistent idle layer |
| `Play_Batmobile_GearShift_Up` | 4 | `GearChange` `3e448c6d` (vehicles/66) | gear-change one-shot |
| `Play_Batmobile_Tyres` | 1 | `ground_roughness_sound_attached` `100cbd8f` (vehicles/15) | surface/tyre bed |
| `Play_Batmobile_MK2_Tyres` | 2 | same | same bed, MK2 bank |
| `Play_Batmobile_Jump_Wind` | 4 | `jump_air_whoosh_sound` `d8a4e0fb` (character/166) | airborne whoosh |
| `Play_Batmobile_HeavyCannon_Explosion` | 4 | `explosion` `d167a490` (effects/464) | explosion |
| `Play_Explosion_2D` | 4 | `explosion` `d167a490` | 2D mix of the same event |

### The 124 approximate rows, by mechanism

| BmAK names | rows | JC3 nearest | the difference |
|---|---:|---|---|
| Boot_Open/Close, Chairs_In/Out, CockpitOpen/Close, Flaps_Open/Close | **32** | `DoorOpeningStart` `500e1421`, `DoorClosingEnd` `f58a18f7` | 8 events, 4 mechanisms -> 2 door roles; 6 events have no role of their own |
| Clutch, MShot, Reverse, Positional, DistantRev, Engine_Transition_In/Out, EngineCoolTicks (+MK2 twins) | 30 | `engine_running_sound`, `GearChange`, `exhaust_upgrade_*` | the role set has no clutch/backfire/distant/transition names; family only |
| Burnout, CornerSqueal, Drift, Skid_OneShot_Brakes, Skid_OneShot_Burnout, WheelSpin, MK2_Burnout | 24 | `ground_roughness_sound_attached` + the `BML_Tyres` family | JC3 pins only one tyre role; squeal/skid/wheelspin are code-fired and unnamed |
| Jump_PreJump, Jump_PreLand, Jump_Land | 12 | `jump_air_whoosh_sound` | one whoosh role for a four-phase jump |
| Rotation | 4 | `chassis_spinning_sound` `1f867af8` (vehicles/36) | BmAK rotation is a battle-mode body move, not a spinning chassis |
| Steering_Bed | 4 | `chassis_spinning_sound` / `ground_roughness_sound_attached` | no steering-bed role |
| Destroyed | 4 | `damage_smoke` `4eb19c73` (effects/146) + `TireDestroyed` `deca52af` (effects/491) | death has two generic roles, not a vehicle-death event |
| RocketTails / Stop_Batmobile_RocketTails | 6 | `exhaust_upgrade_nitrous` `f74ea43b`, `exhaust_upgrade_tjump_trail` `a5d32c2e` | trail is an exhaust upgrade, not a missile tail |
| Immobiliser_Impact | 3 | `dynamic_break_electric` `77009170` (effects/245) | electric crackle, not an EMP impact |
| Tank_Explosion_Barrage_Sweetener | 3 | `explosion` `d167a490` | a sweetener layer over the same explosion |

### The 181 missing rows, biggest first

| BmAK group | names | rows | why JC3 has nothing |
|---|---:|---:|---|
| `Play_BattleMode_*` + `Play_BattlemodeEngine` | 30 | **120** | JC3 has no vehicle mode-switch state; T-MD14 is blocked on the same absence. All 120 rows **are** resolved with media (bank `BML_Batmobile`) - the gap is the trigger, not the audio |
| `Play_HUD_Missile_Lock`, `Play_HUD_fail`, `Play_Tank_Heavy_Lock(ed/Beep)` + 2 `Stop_` | 6 | 23 | no lock-on tone role; `UI_InGame` and `VEH_Tank_Heavy` are both absent from the grab |
| `Play_BML_Sonar_*` (Pulse_Full, Pulse_Search, Rumble_Lp, Turn_On, Turn_Off) + `Stop_` | 6 | 18 | no sonar in JC3 at all; `BML_Sonar` absent |
| `Play_Batmobile_Tracker_Deploy`, `Play_BatSniperRifle_Vehicle_Tracking_Fire` | 2 | 7 | tracker is a BmAK gadget (`RPursuitModeMissileLauncher`), no JC3 role |
| `Play_Batmobile_Rain_Exterior/Interior` | 2 | 7 | no vehicle rain role; weather is world-side |
| `Play_Batmobile_Dodge` | 1 | 4 | no dodge action in JC3 |
| `Play_OBJ_Stagg_Battery_Roll` | 1 | 2 | a mission prop, not vehicle audio |

## 3. What this does to the two audio keep rows

**T-AU1 holds.** `LandAudio` carries exactly 2 members (`min_rpm` 1000.0, `max_rpm` 10000.0,
`Research/JC3Grab/JC3_AUDIO.md` §4) and the mapping is a bank task. Gap to name: the
event-to-parameter edge is not decoded (0 fields resolve it), so *which* BmAK curve becomes
`min_rpm`/`max_rpm` is UNKNOWN; the build keeps the two values and does the mapping in the bank.

**T-AU2 holds only for one of the three banks.** The 45 pinned GUIDs split
**vehicles 24 / character 2 / effects 19**, and test-060 swapped `vehicles.bank` only. So 21
GUIDs - the break effects (`dynamic_break_large/small/medium/window/window_sm/taillight/
turnsignal/electric/light_on/light_off`), `explosion`, `fire_post_explosion`, `TireDestroyed`,
`damage_smoke`, `water_explosion`, `speedwind_sound_player`, `jump_air_whoosh_sound` - still
play the donor audio. That is not a bank-swap job: `effects.bank` and `character.bank` are
shared by every vehicle in the game, so per-vehicle replacement needs an override
(`SDynamicAttachedEffect` per entity or a per-entity bank), and no such mechanism is decoded.
**Gap for the build:** 21 of 45 pinned GUIDs; closest system = the `SAttachedEffect` binding
the `.epe` already uses; missing capability = a per-entity bank override.

## 4. Effects: T-FX1, T-FX2, T-FX5 against the 955-path vocabulary

`FX_TABLE.jsonl` holds **955** `EffectRTSystem` paths, **338** of them under `/jc_vehicles/`.
Keyword census over those 955 (vehicle subset in brackets): `glass` 14 (3), `window` 12 (**12**),
`light` 28 (5), `taillight` 1 (1), `headlight` 7 (2), `electric` 42 (1), `burn` 17 (6),
`fire` 57 (33), `smoke` 29 (18), `roof` 5 (**5**), `spread` 12 (11), `engine` 45 (41).

**T-FX1 (glass/lamp break) - lore-exact, keep holds.** All three donor effects have a
same-meaning JC3 vehicle `.effc`:

| donor effect | JC3 carrier | count |
|---|---|---:|
| `window_break`, `window_break_sm` | `effects/jc_vehicles/damage/dmg_window_break_*` (`_bus_tall_01/02`, `_bus_wide_01`, `_oldtruck_windshield_01`), `dmg_window_tint_break`, `dmg_window_tint_break_windshield` | 12, all vehicle |
| `taillight_break` | `effects/jc_vehicles/damage/dmg_taillight_break.effc` | 1 |
| lamp on/off | `effects/jc_vehicles/collision/headlight_break_on_01.effc`, `headlight_break_off_01.effc` | 2 |
| `electric_break` | `effects/jc_vehicles/collision/break_electric_sm.effc` | 1 |

Gap: JC3's window effects are **per-vehicle**, BmAK's are per-part with 4 window variants
(`small_break` 8, `taillight_break` 4, `window_break` 6, `window_break_sm` 4 - 11 names, 51
rows, `Research/challenge/T2_TRANSLATION.md` §C19). The build must pick the variant per
Batmobile part (canopy vs side glass) rather than inherit one.

**T-FX2 (engine/roof fire) - lore-exact, keep holds.**

| donor effect | JC3 carrier | evidence |
|---|---|---|
| `burn_engine` | `effects/jc_vehicles/damage/dmg_fire_engine_*` (e.g. `dmg_fire_engine_minetruck`, `dmg_engine_ground_flames`), `dlc/.../dlc_dmg_burn_engine_rocketboat_01` | 41 vehicle paths carry `engine` |
| `burn_roof` | `dmg_fire_spread_roof.effc`, `..._minivan_roof`, `..._mini_roof`, `..._bus_roof_01`, `..._armoredtruck_roof` | 5, **all** vehicle |
| `burn_base` | `dmg_fire_spread_base.effc`, `dmg_fire_spread_base_medtank` | 2 |

Gap: the roof effect's emitter box is authored per donor body - the Batmobile's canopy has no
`roof` attachment in the JC3 graph, so the build needs the part + socket, not a new effect.

**T-FX5 (74 `.effc`, 23 unreferenced) - not a translation, and half of it is UNKNOWN.**
The 74 holds: `FX_TABLE.jsonl:27222`, container == donor `.ee`, ext == `.effc`
(`tmp/freebuff/reports/LEDGER-g3src.md:14`). The second half - "23 unreferenced by the 51 rows" -
is **UNKNOWN**, not reproduced: the producer never states what it counted
(`LEDGER-g3src.md:197`). Keep is the correct disposition because those paths are donor
content outside the 51-row effect set; they are **the donor's**, not BmAK lore, and the build
does not owe them a carrier.

## 5. Prioritised brief for the audio and effect build

Ordered by rows lost, then by whether the audio already exists.

| # | brief | rows | what the build does | gap / STAGES.md |
|---:|---|---:|---|---|
| A1 | **Battle-mode transition** | **120** | the 30 events are decoded and resolved in `BML_Batmobile`; build a bank slot + a state-switch trigger (T-MD14) and fire the In/Out set on the mode change | trigger missing: no mode state in the JC3 entity graph; closest = `chassis_spinning_sound` + `GearChange` + `exhaust_upgrade_*` layers |
| A2 | **Body mechanisms** | 32 | reuse `DoorOpeningStart`/`DoorClosingEnd` for boot/cockpit, author roles for chairs/flaps (or clone the two door GUIDs 4x and place them at 4 attachment points) | 6 of 8 events have no role; closest = the 2 door roles |
| A3 | **HUD / lock-on tones** | 23 | needs a UI audio channel: `UI_InGame` and `VEH_Tank_Heavy` are absent from the grab, so first re-grab the two banks, then bind a lock beep/locked pair to the HUD state | no lock-tone role in any decoded `.epe` |
| A4 | **Tyres: squeal / drift / skid / wheelspin** | 24 | bind the 5 one-shots to the tyre state machine; the `BML_Tyres` media (123 WEMs, 3,527,804 B for CornerSqueal alone) is already resolved | JC3 pins one tyre role (`ground_roughness_sound_attached`); the rest are code-fired, unnamed |
| A5 | **Sonar** | 18 | `BML_Sonar` is absent - re-grab first; then needs a sonar state in the vehicle (no JC3 sonar system) | no carrier at all; closest = a one-shot in the `effects` bank |
| A6 | **Jump phases** | 12 | `Jump_Wind` -> `jump_air_whoosh_sound` (already exact); PreJump/PreLand/Land need 3 authored roles | one whoosh role for 4 phases |
| A7 | **Tracker deploy + tracking fire** | 7 | needs the tracker gadget first (T-WP9); audio follows the gadget | no gadget, no role |
| A8 | **Vehicle rain interior/exterior** | 7 | world rain exists; a vehicle-mounted rain bed does not | no vehicle rain role |
| A9 | **Dodge** | 4 | no JC3 dodge action; needs the action before the sound | no mechanic |
| A10 | **Battery roll prop** | 2 | prop foley, not vehicle audio; assign to the prop entity | none needed on the car |
| F1 | **Glass/lamp break** | 51 rows / 11 names | map per part: canopy -> `dmg_window_break_bus_wide_01`, side -> `..._bus_tall_01`, tail -> `dmg_taillight_break`, lamp -> `headlight_break_on/off_01` | per-part choice, not per-vehicle |
| F2 | **Fire (engine/roof/base)** | 3 donor states | `dmg_fire_engine_*` / `dmg_fire_spread_roof` / `dmg_fire_spread_base`; needs the Batmobile canopy part + socket for the roof emitter | roof attachment missing on the body |
| F3 | **23 donor `.effc` (T-FX5)** | 0 | no action - donor content outside the 51 rows; keep them in the tree, do not count them as translated | UNKNOWN count, not a gap |

## 6. What is not claimed

* **Runtime trigger equivalence.** The 23 role names are `.epe` bindings; which game code fires
  each one, and when, is not in the files (`JC3_AUDIO.md` §1, §5). "Exact" here means *the
  same role exists and means the same thing*, not *JC3 fires it at the same moment*.
* **The 90 `missing-bank` rows' sound.** 10 banks are not on disk; their media is unknown, so
  a row's bucket is decided by the BmAK event's meaning, not by its audio.
* **T-FX5's 23.** UNKNOWN (`LEDGER-g3src.md:197`); the 74 holds.
* **Anything in-game.** Test ban (`STAGES.md`; `tmp/freebuff/APPROVED_Q.txt` absent): no bank was
  installed and no car was driven for this audit.

## COMPROMISES

None found in these five rows: T-AU1, T-AU2 and T-FX1/T-FX2 keep on decoded carriers, and
T-FX5 keeps because its content is outside the 51-row effect set. The one latent compromise is
T-AU2's single-bank swap (21 of 45 GUIDs), which is a stated gap above, not an accepted limit.
