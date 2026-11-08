# Does any game-side consumer swap or replace the vehicle entity when battle mode toggles?

Question only. The mode scalars (T-MD5, T-MD6, T-MD7, T-MD13) are closed by `T-MD14b.md` and
`mode-switch-carriers.md`'s carrier table, and are **not** redone here.

**Answer: no consumer was found, and U1 stays `UNKNOWN`.** `Research/JC3Grab/INDEX.jsonl`
(81,952 archive paths) contains **zero** paths with `replace`, `respawn` or `despawn`, **zero** paths
matching `swap` in a graph, entity or level file, and **zero** `variant` paths that are not art assets.
A vehicle's "variant" in JC3 is a **separate `.ee` file** (963 entities, 207 `_signature_`, 306
`_military_`, 758 `_rebel_`, 386 `_civilian_`, 438 `_debug`), never a runtime event. The only consumers
that address an **entity** rather than a flag are **teleport scripts** (11 paths, three graphs) — they
move an entity, they do not swap or spawn one. The game-side streaming consumer is not in the index at
all: **0 `.exe` / 0 `.dll`** entries. So the file that would settle U1 is
**`JustCause3.exe`** (its entity/vehicle streaming consumer), plus `JustCause3.exe`'s script binding
for the teleport graphs; neither is decoded and neither is in `INDEX.jsonl`.

## 1. The search, with terms and counts

Run over `Research/JC3Grab/INDEX.jsonl`, `path` field only, case-insensitive regex, whole file
(81,952 records, one per archived file):

| term | hits | composition |
|---|---:|---|
| `spawn` | **722** | `.wavc` **605** (dialogue lines with "spawn" in the name), `.bin` **53** (`settings/spawn_*_defs.bin` rosters), `.ee` **20** (`spawned_*` character entities, `spawner_*` mech entities), `.gdc` **17** + `.gsc` **17** (spawn-manager mission graphs), `.toc` 4, `.stringlookup` 2, `.hmddsc` 1 |
| `replace` | **0** | — |
| `swap` | **658** | `.rbm` **572**, `.hmddsc` **68**, `.lod` **18** — every one is a **mesh/texture asset** (`*mshswap*`, `*_swap_aggregate_*`); **0** in `graphs/`, **0** `.ee`, **0** `.bl` (both checked explicitly) |
| `variant` | **4** | 2 `.rbm` + 2 `.hmddsc`, all character/parachute art (`parachute_var_debug`, `rico_var_debug`, tourist head variant textures); **0** non-asset |
| `respawn` | **0** | — |
| `despawn` | **0** | — |
| `teleport` | **11** | `.gsc`/`.gdc` **8** (4 pairs), `.bl` **3** |
| `.exe` / `.dll` in the index | **0** | the index covers archive contents only |

The absence is not an artefact of the term list: the same query with `replac` (to catch "replacement"),
`respawn`, `despawn` is empty, and `swap` — the word the class would use — resolves to geometry names
only.

## 2. Every consumer that acts on an entity rather than on a flag

| consumer | file | what it acts on | swap? |
|---|---|---|---|
| `outpost_post_liberation_teleport` | `graphs/military/outpost_post_liberation_teleport.gsc` / `.gdc` | moves an entity on a liberation event | **no** — teleport, no spawn/despawn |
| `msub_teleport_on_mission_exit` | `graphs/mission/modules/msub_teleport_on_mission_exit.gsc` / `.gdc` (2 copies) | moves the player/vehicle when a mission ends | **no** |
| `majestic_3_rico_teleporter` | `graphs/easter_eggs/majestic_3_rico_teleporter.gsc` / `.gdc` + 3 `.bl` region markers | moves Rico between regions | **no** |
| `spawn_*_defs.bin` (53 files, incl. `spawn_vehicle_defs.bin`) | `settings/`, `dlc/*/settings/` | **data rosters** the spawner reads — not a consumer, and no per-entity call | **no** |
| `spawner_mech_*` / `v0805_*_spawner` entities (4 `.ee`) | `dlc/mech_land_assault/.../spawners/` | entity-side spawner objects that create **children** | **no** — spawns new actors, never replaces its own owner |
| `spawned_*` entities (20 `.ee`) | `dlc/.../editor/entities/...` | pre-placed character entities, authored at load | **no** |
| `spawn_manager` mission graphs (17 `.gsc`/`.gdc`) | `dlc/*/graphs/missions/...` | mission-scripted spawning of encounter actors | **no** — mission actor spawn, not the player's car |

**Result:** the only entity-addressing runtime consumers in the index are **teleports**. A teleport
proves the engine exposes "move this actor" to script; it does **not** prove "replace this actor", and
no path, graph or roster in `INDEX.jsonl` names a replacement or a despawn.

This agrees with the plan's negative from the class census (no spawn/replace/teleport **action class**
in the interaction graph, `SSpawnPoint` 5 / `SSpawnSeat` 1 only) — quoted from
`mode-swap-trigger-closest-system-plan.md` §0 and **not re-derived** here.

## 3. The variant side, counted

| family | count in `INDEX.jsonl` |
|---|---:|
| `.ee` entities | **963** |
| `_signature_` variants | **207** |
| `_military_` variants | **306** |
| `_rebel_` variants | **758** |
| `_civilian_` variants | **386** |
| `_debug` variants | **438** |

Every variant is a **file**. There is no `variant` member, no variant selector path, and — decisive for
this brief — no path in the index that names a **runtime** variant change.

## 4. Per D-2 loss: does a consumer remove it?

Since **no consumer exists**, no loss is removed by one. The table records what would remain even if a
swap consumer were found, so the ledger does not over-credit U1.

| row (T_ROWS.jsonl) | D-2 loss | removed by a swap consumer? | what remains |
|---|---|---|---|
| **T-MD5** | battle top-speed curve (`BattleModeVSpeedCurve` 3 points) | **would be**, if the battle entity carries its own `arcade`/`CustomLandGlobal` values | no member takes a curve — the 3 points stay raw |
| **T-MD6** | `TurningModeMaxSpeed` 600 cm/s = 21.6 km/h cap | **would be**, as a per-entity constant | **which** member is a speed cap is still UNKNOWN (no decoded cap member, §2.7 of `mode-switch-carriers.md`) |
| **T-MD7** | six steering/drive factors (`DriveForceFactor` 500, `LatSlipScale` 0.75, `LongSlipScale` 1.25, `SteerAngleFactor` 1, `TrailingSteerFactorMoving` −0.25, `DrivingForceZOffset` 20 cm) | **partly** — four land on the battle entity's modules | the two slip scales have **no member on either side**; stays partial |
| **T-MD8** | turn on the spot (`TurnOnSpot*` 0.8 / −0.8 / 2, `BattleModeTurnOnSpotTorqueFactor` 0.333) | **no** — G2-21 refuted 5 candidates and found 0 tank-only driving members | a second entity creates no pivot; native-only |
| **T-MD13** | transformation stance (`TransformationTurnTorqueFactor` 3000, `...DecelTorqueFactor` 24000, `TransformationAnimNode`) | **pose yes, animation no** — the variant holds part angles | `TransformationAnimNode` has **no JC3 analogue** (0 animation-node members) |
| **T-MD14** | battle audio / transformation sound (`TransformationReverseDirectionInto*ModeSound`) | **no** — a swap is not a transition; a new `Usage` hash still needs a consumer | entry/exit sting and the steering-bed crossfade stay UNKNOWN |
| **T-MD15** | one-row variant table (D-2's 2026-10-28 single-hybrid answer) | **would be** — a swap legitimises two rows | the table's values are still per row, not merged |
| **T-MD11** | battle camera (`BattleModeCamFOV` 60) | **no** — inside the delivered 55–63 band already | only the switch is missing, not a number |
| **T-MD12 / T-L17–T-L20** | battle lamps (`VEHLT_BattleModeLight` ×4) | **no** — mapped to `HeadLight`, they light with the headlights | independent of U1 |

Net: **three** of the ten losses (T-MD5, T-MD6, T-MD15) turn on a swap; **four** (T-MD7 partly, T-MD8,
T-MD13 animation, T-MD14) survive it; three are already carried (T-MD11, T-MD12/T-L17–L20, T-MD10's 0).

## 5. U1, stated

| field | value |
|---|---|
| id | **U1** — is there any consumer that swaps/replaces a vehicle entity at runtime? |
| status | **UNKNOWN** (no consumer found; not refuted) |
| searched | `INDEX.jsonl` with `spawn` (722), `replace` (0), `swap` (658, all mesh assets), `variant` (4, all art), `respawn` (0), `despawn` (0), `teleport` (11) |
| what the hits prove | teleport consumers exist and address entities; **no** spawn/replace/despawn consumer does |
| **file the game's streaming code would need** | **`JustCause3.exe`** — the entity/vehicle streaming consumer (not in `INDEX.jsonl`: 0 `.exe`, 0 `.dll`); its script binding for the three teleport graphs would be the second thing to read |
| cheapest non-code fallback | the Rebel Drop path (candidate 2 in the plan) — spawns the battle leaf at a beacon, proven by `REBELDROP.md` §7, without an entity swap |
| what would change the answer | a decoded exe call that takes an entity and returns another, or a live probe: press the bound action in a delivered car and watch whether the entity id changes |

## 6. Limits

Path-level search only: `INDEX.jsonl` records archive path, hash, archive, offset and size, and nothing
about behaviour, so a **consumer implemented entirely inside the exe** leaves no path trace and this
search cannot see it. That is why the verdict is UNKNOWN rather than REFUTED. The graph/entity/class
negatives quoted from `mode-swap-trigger-closest-system-plan.md` §0 were not re-derived here. No `.ee`,
item, spawn record or graph was read beyond its path; nothing was written outside
`tmp/freebuff/reports`.
