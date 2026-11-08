# EJECT.md vs EJECT.json: do the headline counts agree, and do REVIEW/MAP contradict them?

Card: 8825-eject-md-json-crosscheck. 2026-11-08.

**Count: 4 headline counts compared — 4 MATCHING, 0 DIFFERING, 0 ABSENT.**

| # | headline count | EJECT.md (line) | EJECT.json (key) | verdict |
|---|---|---|---|---|
| 1 | **exits** | `4832` — `EJECT.md:16` "`CInteractionGraphExit` objects: **4832** in 232 graphs," | `counts.fleet_exits = 4832`; `fleet.exits = 4832` | **MATCHING** |
| 2 | **graphs** | `232` — `EJECT.md:5` "232 vehicle `.epe` graphs in …"; `EJECT.md:16` "in 232 graphs" | `counts.fleet_graphs = 232`; `fleet.graphs = 232` | **MATCHING** |
| 3 | **names** | `61` — `EJECT.md:16-17` "61 distinct names, 26 in the donor." | `counts.fleet_names = 61`; `fleet.distinct_names = 61`; `fleet.names` = dict of **61** entries | **MATCHING** |
| 4 | **donor entry at 26** | `26` — `EJECT.md:17` "26 in the donor" (the §2 table has 26 rows) | `counts.donor_exits = 26`; `donor.exits` = list of **26** | **MATCHING** |

"Donor entry at 26" is read as **the donor's exit count is 26** — the only reading the two files'
own vocabulary supports (`counts.donor_exits`, `donor.exits` length). The alternative reading ("the
26th donor row") is also consistent: the last row of `EJECT.md` §2's 26-row table is
`exit.passenger1.upside.down`, and `donor.exits` has 26 entries, so the table and the list are the
same set. Both files come from one generator run: `EJECT.md`'s header and `EJECT.json`'s `.digest`
carry the same digest `8dca980204969198`, which `EJECT_REVIEW.md:9` independently confirms as
`json_equal=True`.

No count differs. Three non-headline differences exist and are recorded in §3 — none of them touches
the four counts above.

## 1. The agreeing counts, extended

Beyond the four headlines, every count quoted in both files agrees. These are the pairs that let the
cross-check be more than a four-line assertion:

| count | EJECT.md (line) | EJECT.json (key) | verdict |
|---|---|---|---|
| exit member keys = **9** | `EJECT.md:18` "members from a set of **9 keys**" | `fleet.exit_keys` = dict of **9**; `fleet.unexpected_keys` = `[]` (0 outside) | **MATCHING** |
| `enabled` = `1` on all exits | `EJECT.md:27` "`enabled` \| `1` on all 4832" | `fleet.exit_keys.enabled = 4832` | **MATCHING** |
| `interaction` null on all | `EJECT.md:28` "null on all 4832" | `fleet.exit_keys.interaction = 4832` | **MATCHING** |
| graph vocabulary = **104** classes | `EJECT.md:35` "The graph vocabulary is **104** classes" | `fleet.classes` = dict of **104** | **MATCHING** |
| launch-named classes = **2** | `EJECT.md:35` "…in the name: **2**" | `counts.graph_classes_with_launch_name = 2` | **MATCHING** |
| velocity-condition instances = **4057** | `EJECT.md:38` "4057 instances" | `fleet.classes.CInteractionGraphParentVelocityCondition = 4057` | **MATCHING** |
| exit objects fleet-wide = 4832 | `EJECT.md:16` | `fleet.classes.CInteractionGraphExit = 4832` | **MATCHING** |
| non-null modifiers = **15 distinct** | `EJECT.md:161` "Non-null `modifier` values … (15 distinct)" | `fleet.exit_keys.modifier = 1399`; the MD's 15-row table sums to **1399** | **MATCHING** (derived sum) |
| launch members in exits = **0** | `EJECT.md:188` "0 of 4832" | `counts.exit_launch_members = 0` | **MATCHING** |
| module launch members = **1** | `EJECT.md:190-191` "`1` distinct member name … `TrainGlobal.crashing_impulse` ×12" | `counts.module_launch_members = 1`; `launch.launch.TrainGlobal.crashing_impulse = 12` | **MATCHING** |
| donor gated exits = **7** | `EJECT.md:84` "7 of 26 exits are speed-gated" | `counts.donor_with_gate = 7` | **MATCHING** |
| donor exits with no condition = **5** | `EJECT.md:84` "5 carry no condition at all" | `counts.donor_without_condition = 5` | **MATCHING** |
| BmAK eject properties = **19** | `EJECT.md` §6 table (19 rows) | `counts.bmak_eject_props = 19`; `bmak.properties` = list of **19**; `bmak.classes` = list of **3** | **MATCHING** |

## 2. Differences that do exist (none is a headline count)

**D1 — `turbo_jump_cooldown` is 232 in the MD but two different numbers inside the JSON.**

- `EJECT.md:217`: "`arcade.turbo_jump` is on **145** land vehicles, `VehicleMisc.turbo_jump_cooldown`
  on **232**."
- `EJECT.json` → `launch.jump.VehicleMisc.turbo_jump_cooldown = 233` **and**
  `launch.jump.VehicleMisc.turbo_jump_cooldown_upgraded = 233`, while
  `launch.files.VehicleMisc.turbo_jump_cooldown = 232` and
  `launch.files.VehicleMisc.turbo_jump_cooldown_upgraded = 232`.

The MD agrees with `launch.files` and disagrees with `launch.jump` by **1**. The two JSON sub-objects
count the same member over slightly different populations (one per member occurrence, one per file),
so this is an internal JSON inconsistency for **one** key-pair, not a MD-vs-JSON contradiction of the
report's statement. It touches no headline count. **Who is right is UNKNOWN** — settling it needs the
generator's definition of the two dicts (`Tools/scripts/jc3eject.py`), not another read of these files.

**D2 — `state` coverage: 4809 in the JSON, unstated in the MD.**

- `EJECT.json` → `fleet.exit_keys.state = 4809` (so **23** of 4832 exits carry no `state`).
- `EJECT.md` does not give that number: `EJECT.md:18` names the 9-key set, and the only all-4832
  claims are for `enabled` (`:27`) and `interaction` (`:28`).

Not a contradiction — the MD never claims state is universal — but it is a **difference in
disclosure**, and `EJECT_REVIEW.md:33` states the missing fact explicitly ("`state` is absent on 23
exits"). A reader who only had `EJECT.md` would not know 23 exits have no state.

**D3 — `launch` member hits: 30 in EJECT_MAP.md, 1 distinct member in EJECT.md.**

- `EJECT_MAP.md:78`: "member-style census of 232 dumps: `eject` 0, `parachute` 0, `bail` 0,
  **`launch` 30**, `catapult` 0, `impulse` 12, `hold_time` 0 (`launch` = fighterjet sockets, `impulse`
  = `crashing_impulse`)".
- `EJECT.md:190-191`: "**1** distinct member name matching eject/launch/catapult/impulse/parachute/
  wingsuit: `TrainGlobal.crashing_impulse` ×12".
- `EJECT_REVIEW.md:35` re-counts the reviewed regex and also reads **1**.

A regex containing "launch" cannot find 1 distinct member if 30 `launch` hits exist on the same 232
dumps. The most likely reconciliation is the one MAP states in its own parenthesis — its 30 are
asset/socket **names** (fighterjet sockets) that its wider member-style census includes and the
module-member sweep does not — but neither file states the population, so the reconciliation is
**derived, not decoded**. Marked **UNKNOWN**, because it does not affect the four headline counts and
cannot be settled from these files. It does not weaken the "no launch velocity" finding: sockets are
asset references, not velocities, and both files agree `impulse` = 12 = `crashing_impulse`.

## 3. Do EJECT_REVIEW.md and EJECT_MAP.md contradict the four counts?

**No. Neither contradicts exits, graphs, names, or the donor's 26.** Both affirm what they restate,
and the numbers they add sit *outside* the roster scope rather than against it.

| file | what it says about the four counts | verdict |
|---|---|---|
| `EJECT_REVIEW.md:33` | "From the 232 `detail/*.ee.json` graphs: **4832** exits, 61 distinct names, **9** member keys, no key outside the 9." | **confirms** exits, graphs, names and the 9-key count |
| `EJECT_REVIEW.md:37-45` | member table: `_object_id`/`disable_event`/`enable_event`/`enabled`/`interaction`/`name`/`name_hash` = **4832** each; `state` = **4809**; `modifier` = **1399** | **confirms**, and supplies the `state` number the MD omits (D2) |
| `EJECT_REVIEW.md:51` | donor `.epe` "carries **17 hash-named members** on every one of its **26** exits as well" | **confirms 26**; adds members, not exits |
| `EJECT_REVIEW.md:74`, `:170` | "**57** exits (17 hash-named members each)" in **12** off-roster graphs; "4832 roster + 57 off-roster exits" | **scope extension, not a contradiction** — 4832/232 stays true for the roster; review:93 calls the MD's 232-graph scope an understatement "by 57 exits" |
| `EJECT_MAP.md:18` | donor graph: "**26 exits**" | **confirms the donor count** |
| `EJECT_MAP.md:20`, `:131` | "**232 dumps**"; "`keymap` in 0/232 dumps" | **confirms the 232 population** |
| `EJECT_MAP.md:78`, `:132` | "0 launch/impulse/force members in the donor's **26** exits"; "JC3's exits carry 0 launch members" | **confirms 26** and the 0-launch finding |

Two places where the review **does** push back — recorded so this page is not read as "all four files
agree on everything":

1. **The 9-key census is incomplete at the donor level.** `EJECT_REVIEW.md:51` and `:181`: the donor
   `.epe` carries **17 hash-named members per exit** that the detail JSON drops ("The 9-key exit
   census is incomplete"). This contradicts `EJECT.md`'s framing that the members are "a set of 9
   keys" (`EJECT.md:18`) as a *completeness* claim. It does not contradict the **count of exits,
   graphs, names or the donor 26**, and the no-launch conclusion survives by type (`EJECT_REVIEW.md`
   finds the invisible members are int/event/matrix only, float/vector **0**).
2. **The headline "JC3 has no eject" is overstated.** `EJECT_REVIEW.md:1` verdict is "PARTLY
   CONTRADICTED": the exe carries `ACT_EJECT_FROM_VEHICLE`, `S_EJECT_FROM_VEHICLE_ALIVE/DEAD`, etc.,
   with **0** data references (`EJECT_REVIEW.md`, §5). That is a claim-level correction, not a
   numeric one, so it does not change any count on this page.

## 4. Checks run

| check | result |
|---|---|
| headline counts read from MD | 4 of 4, at `EJECT.md:5`, `:16`, `:17` |
| headline counts read from JSON | 4 of 4, at `counts.*` and `fleet.*` / `donor.exits` |
| headline comparison | **4 matching, 0 differing** |
| supporting counts compared | 14 of 14 match (table §1) |
| MD modifier table arithmetic | 15 rows sum to **1399** = `fleet.exit_keys.modifier` |
| digest identity | `8dca980204969198` in the MD header and `.digest`; `EJECT_REVIEW.md:9` reports `json_equal=True` |
| REVIEW contradiction check | 0 contradictions of the four counts; 2 claim-level corrections (key completeness, "no eject"), both quoted |
| MAP contradiction check | 0 contradictions; MAP simply does not restate 4832 or 61 |
| JSON internal check | 1 inconsistency found (`launch.jump` 233 vs `launch.files` 232 for the turbo-jump cooldowns) |
| files edited | **none** — this page is the only write |
| game launched / archive written | **no** |

## 5. UNKNOWNs

1. **Which of 233 / 232 is the real `turbo_jump_cooldown` population (D1).** Settle with the two dict
   builders in `Tools/scripts/jc3eject.py`; the files here cannot decide it.
2. **The population behind MAP's `launch` 30 (D3).** Settle by re-running that census with its pattern
   and dump list named; the parenthetical ("fighterjet sockets") is the likely answer but is MAP's
   own gloss.
3. **Whether the 57 off-roster exits should be added to the headline 4832.** `EJECT_REVIEW.md:93`
   says the 232-graph scope understates the census by 57, but no count in either EJECT.md or
   EJECT.json changes, and whether the roster's 232 is the intended universe is a scope decision no
   file records.
