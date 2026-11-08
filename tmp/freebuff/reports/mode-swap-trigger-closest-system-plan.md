# Mode-swap trigger — closest-system plan (D-2 reopened, U1)

D-2 is reopened: BmAK has two modes, the second value set can only live in a **second entity**, and
nothing in JC3 data selects one at runtime (`tmp/freebuff/reports/mode-switch-carriers.md` §7 U1;
`tmp/freebuff/reports/apply-mode-switch-rows.md` §4.1). This plan searches the places a runtime swap
could live, picks the closest JC3 mechanism for the trigger, names the entity pair, says what can and
cannot carry speed and state across, and gives the audio event. Steps are labelled
**decoded** / **derived** / **UNKNOWN** with the file that settles each UNKNOWN.

Sources read for this plan: `tmp/freebuff/reports/{mode-switch-carriers,apply-mode-switch-rows,
battle-audio-switch-event}.md`; `Research/JC3Grab/{REBELDROP,STANDALONE,TRAFFIC,INPUT,INPUT_D11,SEAT,
EJECT,ENTITIES,USAGES,VOCABULARY,FEATURE_CENSUS,NAMES}.md`; `Tools/scripts/jc3strings_write.py`.
(`reports/*.md` do not exist; the three inputs live under `tmp/freebuff/reports/`.)

---

## 0. Answer

**JC3 has no entity swap.** A search of the whole research corpus for spawn / replace / teleport
action classes returns **nothing**: the interaction-graph class census carries entries, exits,
points, transitions, triggers and ~40 condition classes, and **no** spawn / replace / teleport action
(`Research/JC3Grab/ENTITIES.md` class table). The only level-side spawn objects are `SSpawnPoint`
**5** and `SSpawnSeat` **1** (same file).

So a swap has to be **composed**, and there are exactly three homes in the data:

| home | what it is | can trigger a swap? | label |
|---|---|---|---|
| **Rebel Drop spawn** — `profile/item.onlinec` item whose `Name` is the Jenkins hash of the entity leaf | a player-triggered spawn of a named `.ee` at a beacon | **closest match.** It is the only player-initiated "this entity appears" path, and the item *is* the entity binding | decoded `REBELDROP.md` §7 |
| **enter/exit interaction graph** — `entry.driver` / `S_ENTER_DRIVER_VEHICLE`, 5,535 `CInteractionGraphEntry` | the only per-vehicle runtime transition the data owns | **no**: a graph node moves Rico between seats/states, it cannot spawn | decoded `SEAT.md` §1–2, `EJECT.md` §2 |
| **keymap action** — `USE_VEHICLE_MOD` (RPADRIGHT), the land-vehicle action whose consumer is native | a named button the sim may act on | **possible, not proven** — binding it is free, but a consumer must exist | decoded action `INPUT.md:223`; consumer **UNKNOWN** |

**The plan is therefore a spawn-swap, not a swap:** two `.ee` leaves of one chassis, two Rebel Drop
items, and a trigger that spawns the other leaf at the current car and removes the current one. What
that cannot do is the part BmAK gets for free — carrying **speed, gear, health and ammo** across. The
state carry is the plan's honest gap (§4), and it is where the closest JC3 mechanism (Rebel Drop,
which drops a stationary vehicle at a beacon) differs from BmAK (an in-place transform at speed).

---

## 1. What BmAK's switch is (the target)

| element | BmAK | label / evidence |
|---|---|---|
| trigger | hold **LT** for battle, release for pursuit (D-11 user mapping) | decoded control intent, `apply-mode-switch-rows.md` §3.1 |
| entity pair | one car, two value sets: `BattleMode*` 42 declared / 15 serialised, `TurnOnSpot*` 4/3, `Transformation*` 9/4, `TurningModeMaxSpeed` 600 cm/s | decoded `Research/BatmobileGrab/MODES.md` |
| state carried | speed, facing, gear, health, weapon ammo — the car *becomes* the other car | derived from what a transform preserves |
| visual | deployed stance (`TransformationRotation` 0x384 not serialised; `TransformationAnimNode` not serialised) | decoded carrier, values UNKNOWN |
| audio | 32 battle events + `Play_Batmobile_Steering_Bed` (`0xD28CAFB1`, radius 100) | decoded `battle-audio-switch-event.md` §1 |

JC3's own control vocabulary has **no** battle/pursuit/transform action: a regex over all four keymap
copies for `BATTLE|PURSUIT|TRANSFORM|MODE$` returns **0** (`INPUT_D11.md:20-23`, `INPUT.md:267`).
That is the trigger's absence stated from the input side.

---

## 2. Every place a runtime swap could live, tested

### 2.1 Rebel Drop — the player-triggered spawn (closest)

| fact | value | label |
|---|---|---|
| file | `profile/item.onlinec`, base 52,165 B and patch 52,204 B, both naming the donor | decoded `TRAFFIC.md:16-17` |
| binding | `Item.Name` = 32-bit **Jenkins hash of the entity leaf**; 80/80 vanilla vehicle drops bind this way | decoded `REBELDROP.md` §7 |
| worked example | `hash_jenkins("v0300_car_kensington_sportsmuscle_batmobile")` = **443190071** = `0x1A6A8B37` | decoded, same section |
| record size | **128 B** per item, back to back, strings after them | decoded `REBELDROP.md` §7 step 4 |
| free menu slot | `UIDisplayOrder` **12** is one past the highest vanilla slot (11) | decoded |
| cooldown | `RebelDropTimer` 1800 on the donor; 0 = none (the test mod uses 0) | decoded |
| what it does | spawns the hashed `.ee` at the drop beacon — a *stationary* vehicle, not the player's moving car | decoded behaviour of the mechanism; speed/state carry **UNKNOWN** |

**Gap:** the drop is a delivery, not a conversion. It gives the second entity a player-facing entry
point and a hash binding — the two things the swap needs — but it starts at a beacon, at rest, with
no relationship to the car the player is in.

### 2.2 Spawn tables — `settings/spawn_vehicle_defs.bin`

| fact | value | label |
|---|---|---|
| records | **86**, each `entity path` (full `.ee` string) + tag list + name | decoded `TRAFFIC.md:37`, `STANDALONE.md` §"records" |
| role | the ground-vehicle spawner's roster; the traffic picker reads tags | decoded |
| can it swap | **no** — a record registers a path for the spawner, it is not a runtime trigger | derived from the record shape |
| does it accept a new leaf | **yes**, as a new record with a path string | decoded `STANDALONE.md:20` |

**Gap:** registering the battle `.ee` here makes it spawnable (and, if the tags match
`ambient,ground,car,liberated,-highend`, makes AI drive it — `TRAFFIC.md:3`), which is the opposite of
what a player-car mode wants.

### 2.3 Enter/exit interaction graph — the only vehicle-side transition

| fact | value | label |
|---|---|---|
| objects | `CInteractionGraphEntry` **5,535**, `CInteractionGraphExit` **4,832**, `PointNode` 1,843, `Transition` 2,904 | decoded `ENTITIES.md` |
| the donor's driver set | `entry.driver` + 13 exits, states `S_ENTER_DRIVER_VEHICLE` … `S_EXIT_DRIVER_VEHICLE_UPSIDE_DOWN` | decoded `SEAT.md` §1 |
| what a node carries | a state string + a transform (15 of 85 own a matrix, 70 inherit) | decoded `INTERACTION.md:32` |
| spawn / replace / teleport nodes | **0** in the census | decoded negative `ENTITIES.md` |

**Gap:** the graph can gate *when* a transition is allowed (it already owns
`CInteractionGraphParentIsUpRightCondition`, 6,761 instances) but it has no action that moves the car.
A trigger can live here; the swap cannot.

### 2.4 Level `CVehicleRule` — faction/zone vehicle rules

| fact | value | label |
|---|---|---|
| the donor's rules | **2** `CVehicleRule` objects name it, in level data | decoded `TRAFFIC.md:5` |
| what a rule does | binds a vehicle to a faction/zone so the level spawns it | decoded |
| runtime | rules are level-load state, not a button | derived |

**Gap:** a rule is the closest thing to "which faction gets which car", and it is exactly the wrong
axis: it changes at load, not mid-drive.

### 2.5 Part `model_swap` — the only in-place geometry swap member

| fact | value | label |
|---|---|---|
| `VehicleParts.parts[].model_swap.string` | **1** distinct value across 100 part rows | decoded `VOCABULARY.md:1605-1606` |
| `model_swap.hash` | **0** (0..0, n=100) | decoded |
| siblings | `meshswap_parts_when_broken`, `always_mesh_swap_on_death`, `prevent_mesh_swap_while_alive`, `appears_on_death`, `disappears_when_broken` | decoded `VOCABULARY.md:1582,1602,1616` |
| what fires it | damage / death states only | decoded `mode-switch-carriers.md` §2.6 |

**Gap:** JC3 *does* have a runtime "swap this part's mesh" member — the closest in-data analogue of a
mode change — but every trigger it ships is damage, and the member is unused fleet-wide. It gives the
build a way to change *geometry in place* (`prevent_mesh_swap_while_alive` can be cleared), not a way
to change *handling*.

### 2.6 Aircraft / mech "transforms"

| searched | result | label |
|---|---|---|
| any module member named transform/stance/mode | **0 handling members**; the 42 hits are deform points, armour, RPM resistances, part/light names | decoded `mode-switch-carriers.md` §2.7 |
| a `*Mode*` / `*Transform*` module type | **none** in 52 types | decoded |
| the mech (`dlc/mech_land_assault`, `v0805_sportmech`) | a mech **suit** Rico enters — `rico_vehi_mech_driver_to_{std,rollout}.ban` clips exist | decoded `SEAT.md` §2 |
| does any vehicle change its own handling by becoming another shape? | **no decoded case** | UNKNOWN for the mech; settler: the DLC's `.ee` parts module + a take |

**Gap:** there is no JC3 "transform" to copy. The mech is entered, not transformed; the aircraft
"tilt" is a physics lean (`DriverLean`), not a state.

---

## 3. The plan, per step

### 3.1 The entity pair

| | pursuit | battle |
|---|---|---|
| leaf | the delivered leaf (B-13's) | a second leaf, same chassis, e.g. `…_battle` |
| `.ee` | today's build | copy with battle values (speed envelope raw from `BattleModeVSpeedCurve`, stance part angles, battle usage) |
| drop item | item 1 (`Name` = Jenkins hash of leaf 1) | **item 2** (`Name` = Jenkins hash of leaf 2), `UIDisplayOrder` 13 |
| why two entities | one entity cannot hold two value sets (0 selectors in 52 modules) | decoded `mode-switch-carriers.md` §2.7, §3 |

### 3.2 The trigger — three candidates, ranked

| rank | trigger | what it is | evidence | gap |
|---|---|---|---|---|
| 1 | **`USE_VEHICLE_MOD`** (RPADRIGHT) held/pressed in the car | a land-vehicle action that already exists in the patched keymap; its consumer is native | decoded action `INPUT.md:223`; consumer **UNKNOWN** | a name the game dispatches on: unless the vehicle's sim reads it, the press does nothing (U4) |
| 2 | **Rebel Drop item** (menu) | player-initiated spawn of the battle leaf at a beacon | decoded `REBELDROP.md` §7 | not in-place; car arrives at rest (U2) |
| 3 | **interaction-graph node** | a graph state on the car that fires a transition | decoded class census | no spawn/replace action exists, so it can only *gate* (U1) |

**Recommendation:** build candidate 1 as the trigger, with candidate 2 as the guaranteed-working
delivery path. That mirrors BmAK's own structure — BmAK's flip and its weapon both ride an existing
press because the *call* is inside a function the button already runs; JC3 has no such function for a
mode, so the trigger must be probed, not assumed.

### 3.3 What carries speed and state across

| state | JC3 carrier | verdict |
|---|---|---|
| position / rotation | the spawn call's transform (a beacon, or — if the consumer exists — the car's own) | **partial**: known only through the spawn's own transform, UNKNOWN at runtime |
| velocity | nothing in the item / spawn-table / entity format | **UNKNOWN**; settler: the spawn consumer in `JustCause3.exe` |
| gear / engine state | nothing | **not carried** |
| health | each entity has its own health module (one private module, referenced twice) | **not carried**: the new car starts at full |
| weapon ammo | per-weapon state, not in the entity | **not carried** |
| BmAK's own mode flag | the entity *is* the flag | **carried by construction** |

**Honest composition:** a spawn-swap is a **pit-stop swap** — the battle car appears where the
pursuit car is (or at the beacon), at rest, at full health. If that is unacceptable, the only
alternative is Option B from `mode-switch-carriers.md` §5: keep **one** entity and use the
`heat_boost` block as an in-place multiplier state (torque ×2, grip ×4.26, +100.92 km/h, blend
0.2 s), which carries *continuous* state for free because nothing is re-spawned — and carries only
about a third of one row's worth of BmAK's numbers.

### 3.4 The audio event

| element | value | label |
|---|---|---|
| mechanism | a `.epe` `Usage` int on the entity's state object, bound to an event in a FEV bank | decoded `USAGES.md`, `JC3_AUDIO.md` |
| closest existing usage | `EngineNitro` hash **4197885156**, 18 vehicles, **307** objects; sound GUID `f74ea43b-…` on 202 objects / 172 vehicles, `vehicles.bank` `EVTS` 249 | decoded |
| battle bed to import | `Play_Batmobile_Steering_Bed`, event id **3532435377** / `0xD28CAFB1`, outer `Ww_BML_Battlemode`, radius **100**, from `BML_Battlemode` (830,548 B, 7 events / 10 actions / 44 sounds / 24 media) | decoded `AUDIO_BANKS.md`, `AUDIO_MAP.json` |
| what a spawn-swap gets for free | the battle entity's graph plays the battle usage **from its first frame** — a swap *is* an entry, so the `In_*` stings are not needed | derived |
| what it cannot get | the `Out_*`/`In_*` **transition** pair and the steering bed's start/stop across a continuous mode change | UNKNOWN (U5) |

**This is the one place a spawn-swap is *better* than an in-place switch:** because the battle car is
a different entity, its audio is not switched — it simply starts. BmAK's 32 gear-indexed events are
still not importable (no gear event in JC3, `battle-audio-switch-event.md` §3), but the two
mode-level beds are.

---

## 4. Byte-level edits

| # | file | edit | numbers | label |
|---|---|---|---|---|
| E1 | second `.ee` | copy of the pursuit leaf with battle modules (speed envelope, stance angles, usage) | object count identical to the pursuit graph; no new classes | derived plan; B-05 writes it |
| E2 | `profile/item.onlinec` (patch 52,204 B preferred) | append one `Item`, bump `Items[]` count | record **128 B**; `Name` = `hash_jenkins(leaf2)`; `UIDisplayOrder` 13; `DlcId` 0; `UIType` 3; `Type` 1; `RebelDropTimer` 1800 or 0 | decoded recipe `REBELDROP.md` §7 |
| E3 | item strings | write `UIImagePath` / `UIVideoPath` = the new leaf | two strings in the string area, same leaf text | decoded |
| E4 | `settings/spawn_vehicle_defs.bin` (optional) | add a record with the battle path + tags | 86 → **87** records; path is a full `.ee` string; must **not** match the traffic selector `ambient,ground,car,liberated,-highend` | decoded record shape `STANDALONE.md` |
| E5 | keymap (only if candidate 1 is chosen) | none — `USE_VEHICLE_MOD` already exists at RPADRIGHT | 0 keymap edits | decoded `INPUT.md:223` |
| E6 | `vehicles.bank` copy + battle graph | import `BML_Battlemode`'s 24 media, bind the bed to a battle usage | bank 830,548 B source; `EVTS` 249 target; same-size PCM swap precedent (test-060) | decoded `JC3_AUDIO.md` §5, `bm_bank_manifest.json` |

**Revert.** E2/E3/E4/E6 are additive records/strings/samples in private copies (`bm_rebel.py`,
`bm_audio.py` generators), so re-running the generator without the row restores the file; E1 is a
whole-tree copy, so deleting the tree is the revert. Nothing is edited in place.

---

## 5. Gates that would prove it

| # | gate | pass condition |
|---|---|---|
| G1 | `bm_rebel.py --check` | item count moves by exactly **+1** (197 → 198), the new `Name` equals `hash_jenkins(leaf2)`, `UIDisplayOrder` 13 unused |
| G2 | `aafdiff` pursuit vs battle tree | the diff lists **only** the rows the variant table names (handling module, part angles, usage), no class or object-count change |
| G3 | `jc3strings_write.py` / `NAMES` check | the two new strings resolve, and the vanilla leaf strings are unchanged |
| G4 | `jc3hkx.py check --all` | 0 problems — the collision file is unchanged by the swap |
| G5 | in-game probe (candidate 1) | press/hold `USE_VEHICLE_MOD` in the car: does anything happen at all? A no-op means the action has no consumer for this entity, and the plan falls back to candidate 2 |
| G6 | in-game probe (candidate 2) | the battle item drops the battle leaf at the beacon with the battle stance and the bed audible |

---

## 6. Pilot card

> **Sit in the car, hold the mode input for 0.40 s, release, hold again:** each hold must produce the
> other car — same spot within **0.5 m**, facing within **5°**, stationary at the moment it appears
> (**≤ 1 km/h**), with the battle stance visible on the first frame and the battle bed audible within
> **0.20 s**; three holds must give three alternations, and releasing must never leave both cars alive.

Pass band, and why:

| number | source | fails if |
|---|---|---|
| 0.40 s hold | long enough to clear a tap, short enough to be a mode input; BmAK's own hold time is not in any read file (U6) | a tap also swaps, or a deliberate hold does nothing |
| 0.5 m / 5° | the spawn transform is the only position carrier; a beacon drop is metres away, so this band only passes on an in-place consumer | the battle car appears at the beacon, i.e. candidate 2 was shipped as if it were candidate 1 |
| ≤ 1 km/h | a spawn-swap cannot carry velocity; the card makes the limit explicit rather than hiding it | the car keeps its speed, meaning a real in-place consumer exists — the better outcome, and this card then needs raising |
| 0.20 s audio | `nitro_boost.boost_blend_time` 0.2, the only shipped state-blend time | the bed is late, silent, or continues after the swap back |
| both cars alive | the spawn must remove the old one; the item format has no "replace" field | two Batmobiles exist, one abandoned behind the player |

---

## 7. UNKNOWNs, each with the file or probe that settles it

| # | UNKNOWN | settles it |
|---|---|---|
| U1 | is there any consumer that swaps/replaces a vehicle entity at runtime? | `JustCause3.exe` entity/vehicle streaming consumer (not decoded); the class census already shows no spawn/replace action in the interaction graph |
| U2 | does a Rebel Drop spawn preserve or transfer the player's car state (speed, gear, health)? | the spawn consumer in the exe; or a live probe: drop a car while driving one and read the new car's speed/health |
| U3 | does `USE_VEHICLE_MOD` have a consumer on a mod vehicle? | a live press in the delivered car; the action exists at RPADRIGHT (`INPUT.md:223`) with no decoded consumer |
| U4 | can two Rebel Drop items name two `.ee` leaves of the same chassis without one shadowing the other? | `bm_rebel.py --check` on a build with both items, then the menu (G1/G6) |
| U5 | is `Play_Batmobile_Steering_Bed` a start/stop loop or a one-shot? | the event's HIRC action list (10 actions, 4 ranseq in `BML_Battlemode`) via `grab_audio_banks.py` |
| U6 | BmAK's own hold time for the mode input | no value in `AUDIO_MAP.json` or `MODES.md`; the `In_/Out_` events' crossfade in the bank's actions |
| U7 | does any JC3 vehicle (the `v0805_sportmech` mech included) change shape *and* handling in place? | the DLC's `.ee` parts module + `PARTS_TABLE.jsonl`, then a take; no doc in `Research/JC3Grab` covers the mech |
| U8 | whether a replaced `settings/spawn_vehicle_defs.bin` is honoured from the dropzone | `STANDALONE.md:227` records it as untested; needs a runtime test |

---

## 8. Checks run for this plan

| # | check | result |
|---|---|---|
| 1 | the three named inputs exist and were read | `tmp/freebuff/reports/{mode-switch-carriers,apply-mode-switch-rows,battle-audio-switch-event}.md` (the `reports/` copies do not exist) |
| 2 | spawn / replace / teleport classes searched across the JC3 corpus | **0** action classes; `SSpawnPoint` 5 / `SSpawnSeat` 1 are the only spawn objects (`ENTITIES.md:105,111`) |
| 3 | mode/transform action names in the keymaps | **0** matches for `BATTLE|PURSUIT|TRANSFORM|MODE$` in all four copies (`INPUT_D11.md:20-23`, `INPUT.md:267`) — the trigger's absence, from the input side |
| 4 | Rebel Drop binding re-read | `Item.Name` = Jenkins hash of the leaf; 80/80 vanilla vehicle items; 128 B records; `UIDisplayOrder` 12 is the first free slot; worked hash `443190071` (`REBELDROP.md` §7) |
| 5 | the second entity's cost | one `.ee` copy + one 128 B item + two strings + (optional) one 86→87 record — no new class, no object count change |
| 6 | audio carrier re-read | `EngineNitro` 4197885156 / 307 objects; bed `0xD28CAFB1` radius 100; `BML_Battlemode` 830,548 B / 24 media (`USAGES.md`, `AUDIO_BANKS.md`) |

**Limits.** This is a plan: no `.ee`, item, spawn record, bank or keymap was written, nothing was
installed, and no game was launched. The trigger is **not** proven — the whole plan rests on either a
native consumer for `USE_VEHICLE_MOD` (U3) or the Rebel Drop path (U2); the first is a 5-minute press
in the car, the second is a 5-minute drop, and both should be run before any variant tree is built.
The state-carry table is the plan's weakest link: a spawn-swap carries position at best, and the
pilot card states the speed/health loss rather than hiding it.
