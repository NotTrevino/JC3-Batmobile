# SAM turret hack — what state it is left in, carrier by carrier

Scope: `w501_turret_sam_v2` and its interaction graph, per `tmp/freebuff/reports/G3-08d.md` and
`tmp/freebuff/reports/hacker-and-tracker-gadgets.md`. Drones are **excluded** (separate brief).
Requirement being reproduced (operator, 2026-11-08): after a SAM turret is hacked it stops firing at
the player and fires at enemies, **aircraft only**, and its radar marker goes red → green.

Labels: **decoded** = read at the file and line named; **derived** = arithmetic or a stated rule over
decoded inputs; **UNKNOWN** = searched and absent, with the search and the file that would settle it.

---

## 0. Answer in one line

The hack leaves the turret with **exactly one state change**: the completion exit fires event
`5D26E95A`, which is one of the three events listed in the `CInteractionContext`'s `disable_event`
list — the prompt is switched off. The graph's success exit has a **null** `interaction` target
(`00000000`), and the entity contains **no** faction write, no owner/team/allegiance member, no
aircraft filter and no radar/marker member. So the turret keeps `CTurretWeaponComponent.faction` = 5
and `CAreaDamage.faction` = 2 before and after the hack, unchanged; the closest carrier for BmAK's
allegiance flip is that `faction` int, and the file would have to show a runtime consumer that both
re-targets the turret and re-colours its marker from it — neither exists in any decoded file.

---

## 1. Sources and method

| what | value | source |
|---|---|---|
| entity, patch layer | `editor/entities/jc_weapons/05_stationary/w501_turret_sam_missile/w501_turret_sam_v2.ee` — 3,542,656 B | `Research/JC3Grab/INDEX.jsonl:38637` |
| its wiring graph | same folder, `w501_turret_sam_v2.epe` — 115,460 B | `INDEX.jsonl:38639` |
| scripted variant | `w501_turret_sam_v2_custom_scripted.epe` — 116,812 B | `INDEX.jsonl:38644` |
| its weapon tune | `w501_sam_missile.wtunec` — 14,235 B, `patch_win64/game1`, offset 441,362,432 | `INDEX.jsonl:38636` |
| decoded working copy | `tmp/freebuff/scratch/epe/w501_turret_sam_v2.epe.xml` — 462,926 B, 8,642 lines | this session |

All line numbers below are lines of that working copy. The `.epe` is the interaction/event wiring; it
is where a "hack changes the turret" effect would have to appear. Nothing under a game install was
opened this session; the `.ee` bytes were not re-read (they are not in the project tree).

---

## 2. The graph, decoded — states, events, targets

Object tree (decoded, `w501_turret_sam_v2.epe.xml`):

| line | object | class | decoded values |
|---:|---|---|---|
| 7179 | `CInteractionContext` | `CInteractionContext` | `enabled` 1; `disable_event` `5D26E95A, D6DBD97F, 5527168B`; `enable_event` `06F7657B`; `world` matrix at the turret (−0.4 m off the root) |
| 7189 | `CInteraction` | `CInteraction` | `_object_id` `BC2CF98E` — the target the entry binds to |
| 7195 | `CInteractionComponentAnimationLayer` | `CInteractionComponentAnimationLayer` | `file` `animations/jc_statemachine/main_characters/rico/external/use_item_progress.al`; unnamed values: `1900FF1E` = `…/rico/contextact/rico_contextact_hack_sam_enter.anim`, `230FBFB4` = `…_exit.anim`, `B3248BAD` = `…_hack_sam.anim`, `90A5F97F` = `FullBody` |
| 7218 | `CInteractionGraph` | `CInteractionGraph` | `enabled` 1; own `enable_event`/`disable_event` **empty** |
| 7228 | `entry.use_item` | `CInteractionGraphEntry` | `state` `S_ENTER_USE_ITEM`; `interaction` `BC2CF98E` (the `CInteraction`); `E9AE11FE` = event `79C46856`; `565F571C` = event `C8058578`; `0ECBF7B1` = object `27A2128C` (the point node); `3B381407` = string `ui_i001_name`; `BA25AE52` = `ACT_ENTER_VEHICLE`; conditions: `CInteractionGraphParentVelocityCondition` min 0 / max 0.5, `CInteractionGraphNodeAboveWaterCondition` 1.2, `CInteractionGraphParentIsUpRightCondition` check 1 |
| 7308 | `point.use_item` | `CInteractionGraphPointNode` | `world` matrix at −0.68 m; one child exit (below) |
| 7312 | `exit.use_item.success` | `CInteractionGraphExit` | `state` `S_EXIT_USE_ITEM_SUCCESS`; `interaction` **`00000000`**; `enable_event`/`disable_event` **empty**; `E9AE11FE` = **`5D26E95A`** (the only event) |
| 7355 | `exit.use_item.fail.up_right` | `CInteractionGraphExit` | `state` `S_EXIT_USE_ITEM_FAIL`; `interaction` `00000000`; `CInteractionGraphParentIsUpRightCondition` check 0 |
| 7371 | `exit.use_item.fail.moving` | `CInteractionGraphParentIsUpRightCondition` | `state` `S_EXIT_USE_ITEM_FAIL`; `min` 0.5 / `max` 9999 |

**The causal chain (derived from the five decoded links, each quoted above):**

1. `entry.use_item` binds to interaction `BC2CF98E` and enters at state `S_ENTER_USE_ITEM`.
2. It moves to `point.use_item` (object `27A2128C`), whose only child is `exit.use_item.success`.
3. The success exit **targets nothing** (`interaction` `00000000`) and **enables/disables nothing**
   directly (both lists empty).
4. Its one event is `5D26E95A` — and `5D26E95A` is the first entry in the `CInteractionContext`'s
   `disable_event` list (line 7182).
5. So completing the hack disables the interaction context and nothing else. That is the whole
   state transition: **the prompt goes away**.

The three hack animation paths (lines 7203, 7204, 7207) are on the **player's** animation layer
(rico context-act, `FullBody`), not on the turret and not on any turret state object.

The `_custom_scripted` variant is identical for this question: the same three animations at its lines
5159–5163, `CInteractionContext` at 5135, the same `faction` values (5 at 6534, 2 at 2614 and 8578),
`STargetPoint` at 8610, and **0** hits for `radar`, `allegiance`, `owner`, `team`, and 1 hit for
`script` — its own object name. Being "custom scripted" changes no decoded state carrier here.

---

## 3. Every state carrier in the entity

| # | carrier | path + line | value it sets / holds | label |
|---:|---|---|---|---|
| 1 | `CInteractionContext.enabled` | `.epe:7184` | `1` — the hack prompt is live at load | decoded |
| 2 | `CInteractionContext.enable_event` | `.epe:7183` | `06F7657B` (not defined in this file — resolves in the `.ee` event table) | decoded id / UNKNOWN name |
| 3 | `CInteractionContext.disable_event` | `.epe:7182` | `5D26E95A, D6DBD97F, 5527168B` — any of the three turns the prompt off | decoded |
| 4 | `CInteractionGraph.enabled` | `.epe:7223` | `1` | decoded |
| 5 | `entry.use_item.state` | `.epe:7249` | `S_ENTER_USE_ITEM` (string state) | decoded |
| 6 | `entry.use_item` events | `.epe:7272`, `:7260` | `79C46856`, `C8058578` (entry-side, before the act completes) | decoded id / UNKNOWN name |
| 7 | `point.use_item` | `.epe:7308` | node at −0.68 m with the exit below | decoded |
| 8 | `exit.use_item.success.state` | `.epe:7321` | `S_EXIT_USE_ITEM_SUCCESS` | decoded |
| 9 | `exit.use_item.success.interaction` | `.epe:7318` | **`00000000`** — no target object | decoded (absence) |
| 10 | `exit.use_item.success` events | `.epe:7336` | **only** `5D26E95A` (= carrier 3, the context disable) | decoded |
| 11 | `exit.use_item.fail.*` | `.epe:7355`, `:7371` | `S_EXIT_USE_ITEM_FAIL`, velocity 0.5..9999 | decoded |
| 12 | player animation layer | `.epe:7195-7208` | `hack_sam`, `_enter`, `_exit` on `use_item_progress.al`, `FullBody` | decoded |
| 13 | `CTurretWeaponComponent.faction` | `.epe:4952` (scripted: `:6534`) | **`5`** — the turret mount's side value | decoded value / meaning UNKNOWN (see §5) |
| 14 | `SPhysicsParams.faction` | `.epe:4284`, `:7702` | **`2`** (two physics params blocks) | decoded |
| 15 | `CAreaDamage` | `.epe:4407` (values `:4413`, `:4416-4418`) | `enabled` **0**, `faction` **2**, `interval` 3, `max_damage` 20, `damage_type` 32 | decoded |
| 16 | weapon root | `.epe:7` | `CMissileWeaponBase`, name `w501_turret_sam_v2`, `weapon_id` 501, `weapon_type` 2 | decoded |
| 17 | fire points | `.epe` `SWeaponPoint` ×7 (`fire_position_1..6`, `SWeaponPoint1`) | positions/rotations only; **no `faction`, no target filter** on any of them | decoded (absence) |
| 18 | aim point | `.epe:8524` | `STargetPoint`, `min_aim_distance` **5** | decoded |
| 19 | aircraft target priority | `Research/JC3Grab/WEAPONS.md:767` (fleet) | `missile_weapon[].ai_tuning.ai_base_tuning.air_vehicle_target_priority` — 11 builds, min **1**, max **1** | decoded fleet member / SAM's own value UNKNOWN |
| 20 | radar / marker / minimap | `.epe` whole file | **0** hits for `radar`, `marker`, `minimap`; the 63 `poi` hits are all `CEffectPointEmitter` | decoded (absence) |
| 21 | allegiance / owner / team / sides | `.epe` whole file | **0** hits each (`ignore_faction` also 0) | decoded (absence) |
| 22 | what the hack writes to ownership | — | nothing: no event, member or animation layer sets a side (§2 chain) | UNKNOWN (no carrier exists) |

**Rows 13–15 are the only side-carrying integers, and all three are authored constants.** None sits
on the graph, none is in an event list, and none is touched by the success exit.

---

## 4. What the hack provably does not do

| claim | evidence | label |
|---|---|---|
| it does not write a faction | the success exit's event list holds one id (`5D26E95A`), which is the context's own disable event; no faction object appears in any event target | decoded |
| it does not retarget the turret | success exit `interaction` = `00000000`; the graph has no `CInteractionGraphNode` that names a weapon, target or AI object | decoded |
| it does not touch the weapon tune | the graph objects reference animation, events and matrices only; no `.wtunec` path occurs in the `.epe` | decoded |
| it does not create a marker | 0 `radar` / `marker` / `minimap` hits; `poi` hits are effect emitters | decoded |
| it does not filter aircraft | 0 hits for `ai_tuning`, `air_vehicle`, `target_priority` in the entity; fire points carry no target field | decoded |

This matches the earlier records and does not contradict them: `G3-08d.md` §4 and
`hacker-and-tracker-gadgets.md` "What the SAM hack does to ownership" both leave it UNKNOWN because
the graph+animation are there and the effect is not. This report narrows that UNKNOWN to a decoded
statement: the effect is **prompt-disable only**.

---

## 5. The closest match to BmAK's allegiance switch — and what would have to be true

**Closest carrier: `CTurretWeaponComponent.faction` = 5** (`.epe:4952`; scripted variant `:6534`).
It is the only integer in the entity that names a side and belongs to the turret's weapon component
rather than to physics or a damage volume. Runners-up, rejected:

* `SPhysicsParams.faction` = 2 (lines 4284, 7702) — physics/collision side hint, not a firing side.
* `CAreaDamage.faction` = 2 with `enabled` **0** (line 4407) — a disabled damage volume; it cannot
  be the post-hack firing state because it is off before and after.
* per-weapon-point `faction` — a real fleet member (25 rows, `HACKABLES.md` §3) but **absent on all
  seven fire points of this entity**, so there is nothing here to flip.

BmAK's switch has two visible halves: the turret changes sides (stops firing at the player, starts
firing at enemies) and the **radar marker goes red → green**. The `faction` int is the only candidate
for the first half. For the match to **hold**, the files would have to show all three of:

1. **a runtime consumer of `faction`** — something that reads the turret component's `faction` and
   chooses targets from it. Not decoded: the `.epe` has no AI/targeting object, and the entity's
   `ai_tuning` members live in the weapon tune (`w501_sam_missile.wtunec`), which no decoded record
   covers (`Research/JC3Grab/WEAPONS.md` / `WEAPONS_SHARED.json` contain **0** `w501` rows). The
   settling file is the `CTurretWeaponComponent` implementation in `JustCause3.exe`, or a decoded
   `.wtunec` that carries `ai_tuning.ai_base_tuning.*`.
2. **a writer that sets `faction` at hack completion** — the success exit would need an event or a
   component-set node naming the turret component. It has none: its `interaction` is null and its
   only event disables the prompt (`.epe:7318`, `:7336`). A build would have to add that writer; the
   file cannot be pointed at one.
3. **a marker whose colour or type is derived from the same value** — the marker half of BmAK's
   switch. Nothing in the entity names a marker; the JC3 HUD carrier is a POI
   (`CreatePoi(type, use_progress_bar, is_minor, label)`, `POI_TYPE_LOCK_ON_TARGET` = 21, per
   `hacker-and-tracker-gadgets.md` Lead 3), and a POI has **no colour, faction or hostility field**.
   For the match, a file would have to show a POI/marker element reading the object's faction — the
   per-type icon switch in `hud_code/poi.as` decoded type by type, or a radar/marker component on the
   entity with a colour member. Neither is decoded; both are named as the settling files.

**Verdict (derived):** `faction` is a *label* on the mount, not an *allegiance switch*, in every file
read here. It is the closest carrier because it is the only one that names a side and survives the
hack unchanged — but calling it an allegiance flip would be a claim the files do not support.

---

## 6. Aircraft-only targeting — the closest JC3 mechanism

The SAM's own tune is not decoded (`INDEX.jsonl:38636` names `w501_sam_missile.wtunec`; 0 `w501`
rows in `WEAPONS.md` / `WEAPONS_SHARED.json`). What the fleet does carry, decoded:

| member | builds | min | max | source |
|---|---:|---:|---:|---|
| `missile_weapon[].ai_tuning.ai_base_tuning.air_vehicle_target_priority` | 11 | 1 | 1 | `WEAPONS.md:767` |
| `missile_weapon[].ai_tuning.ai_base_tuning.character_target_priority` | 11 | 1 | 1 | `WEAPONS.md:768` |
| `missile_weapon[].ai_tuning.ai_base_tuning.land_vehicle_target_priority` | 11 | 1 | 1 | `WEAPONS.md:770` |
| `missile_weapon[].ai_tuning.ai_base_tuning.mounted_gun_target_priority` | 11 | 1 | 1 | `WEAPONS.md:773` |

**Mechanism:** `ai_tuning.ai_base_tuning.<class>_target_priority` is a per-target-class weight. The
aircraft-only requirement maps to it directly: raise `air_vehicle_target_priority` and zero the
ground classes (`character`, `land_vehicle`, `mounted_gun`, and the sea/tank siblings where a missile
weapon carries them).

**Two honest limits.**

1. **The SAM's own values are UNKNOWN**, because its `.wtunec` is named in the index but not decoded.
   The fleet table proves the member exists on 11 missile weapons; it does not prove `w501` carries
   it. The settling file is a decode of `editor/entities/jc_weapons/05_stationary/
   w501_turret_sam_missile/w501_sam_missile.wtunec` (`INDEX.jsonl:38636`, 14,235 B) — the same
   `grab_weapons` reader that produced `WEAPONS.md`.
2. **Zero is outside the shipped range.** All four members ship 1 on every build, so "0 for ground"
   is a value no shipped missile weapon uses. **derived:** the write is expressible, but its effect
   is a pilot test, not a decoded outcome.

This is also the only decoded carrier that distinguishes aircraft from ground **inside the weapon**;
the entity itself has no such field (0 `air_vehicle` hits, no target field on any fire point).

---

## 7. UNKNOWNs, with the searches run and the settling file

| # | unknown | searches run | settling file |
|---|---|---|---|
| U1 | names of events `5D26E95A`, `06F7657B`, `79C46856`, `C8058578`, `D6DBD97F`, `5527168B` | whole `.epe` scanned for each id; no `<object>`/`_object_id` definition exists in the file — only uses (`7182`, `7183`, `7260`, `7272`, `7336`, `7484`, `4985`) | the entity's event table in `w501_turret_sam_v2.ee` (3.5 MB, `INDEX.jsonl:38637`) — not in the project tree |
| U2 | whether `faction` 5 selects targets at runtime | `.epe` has no AI/targeting object; 0 `ai_tuning`/`target`-class hits; tune not decoded | `CTurretWeaponComponent` implementation in `JustCause3.exe` |
| U3 | the SAM tune's `ai_tuning` values | 0 `w501` rows in `WEAPONS.md` / `WEAPONS_SHARED.json` | `w501_sam_missile.wtunec`, `INDEX.jsonl:38636` |
| U4 | the marker red→green carrier | 0 `radar` / `marker` / `minimap` hits in both `.epe` variants; POI has no colour field | `hud_code/poi.as` decoded per type, or a radar/marker component layout in the engine |
| U5 | whether the `.ee` (not just the `.epe`) carries a side or marker object | not read this session (not in the project tree; game install not opened) | `w501_turret_sam_v2.ee` decode — a `--strings`/object sweep with the existing reader |

No row is closed from memory. Every "no carrier" statement above is a counted absence in the named
file, not an inference from another game's behaviour.

---

## 8. Limits and revert

* **Limits.** Desk decode of the `.epe` only. The `.ee` (where event names and component wiring live)
  and the `.wtunec` (where `ai_tuning` lives) were not decoded this session; both are named above
  with their `INDEX.jsonl` lines. The behaviour claim is the operator's (2026-11-08) and is treated as
  the target, not as evidence about JC3.
* **Revert.** Delete this file and its copy under `tmp/freebuff/reports/`. No other file was created,
  edited or moved; `G3-08d.md`, `hacker-and-tracker-gadgets.md`, `HACKABLES.md` and
  `tmp/freebuff/scratch/epe/*.xml` were read only.
