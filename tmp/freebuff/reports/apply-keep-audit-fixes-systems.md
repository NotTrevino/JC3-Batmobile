# Applying the systems keep-audits — lights, audio/FX, damage and collision

**STATUS: done.** Every approximate or missing item in the three audits is now either a ledger edit
with its derivation or a card with a measurable done-line. The lights items are in **B-07**, the
audio/effects items in **B-11**, the damage items in **B-09** and the collision items in **B-10**
(two capability gaps became new cards, **B-25** and **B-26**). `t_blocked.py` is re-pinned and
passes; the blocked set and the in-scope count did not move, so `WAITS` and `in_scope == 216` are
unchanged. One real gate failure found by the damage audit (bm-RC2 losing its `max_health`
declaration) is repaired and verified.

No game was launched or attached to. No file under `Builds/` was touched.

## 1. What each audited item became

### 1.1 Lights — `keep-audit-lights.md`

| item | before | now | where |
|---|---|---|---|
| T-LG1 built row count | `21 entries` (stale) | **18** = 21 − 10 dropped + 7 added | ledger edit (`next`) + B-07 payload |
| T-LG3 spot rows at 30/40 | `5` | **4** (rows 2, 4, 6, 10) | ledger edit + B-07 |
| T-LG6 `range` | 30 on 5 rows (donor value) | `Radius_cm/100` → **60, 45, 40.96, 20.48, 10.24, 4, 1.5, 0.8** — 60 and 45 above the fleet max 50, declared **R3** rather than rounded into the band | ledger edit + B-07 |
| T-LG6 `angle` | 40 | `OuterConeAngle` → **70, 60, 50, 44, 35, 15** | ledger edit + B-07 |
| T-LG6 `multiplier` | donor 1–2 | `clamp(5 × Brightness, 0.5, 5)` → **0.75 / 5** (unit UNKNOWN, declared) | ledger edit + B-07 |
| T-LG6 `blinking` | 1 on rows 3, 5, 7, 9 | **0** — no BmAK entry authors a blink; the flicker invented behaviour | ledger edit + B-07 |
| T-LG6 `InnerConeAngle` (8 entries) | absent | closest composition: a second row on the same part with the narrow angle and the higher multiplier | ledger cell + B-07 |
| 17 lens-flare entries (10 flare-only, 7 riding) | 0 carried | **card B-25**: part-side emitters (`CarLight` block / `has_lights` part), the wheel-arch recipe | new card |
| T-LG2 | `closed` | restated: `t2_lg2.py` measures the donor join, not BmAK fidelity | ledger `keep`, cell corrected |

### 1.2 Audio and effects — `keep-audit-audio-fx.md`

| item | before | now | where |
|---|---|---|---|
| T-AU1 `min_rpm`/`max_rpm` | keep | unchanged, with the event→parameter edge named UNKNOWN | ledger `why` + B-11 |
| T-AU2 bank swap | "engine bank already swapped" | **24 of 45 GUIDs ours, 21 still donor** (effects 19 + character 2); the 24 vehicle-bank GUIDs, the 120 battle-mode rows and the 24 tyre one-shots are B-11's plan | ledger `why` + B-11 |
| 21 shared-bank GUIDs | unstated gap | **card B-26**: per-entity `SAttachedEffect`/`SDynamicAttachedEffect` bank override, GUIDs unchanged | new card |
| T-FX1 glass/lamp breaks | keep | lore-exact; the plan picks the variant **per part** (canopy `bus_wide_01`, side `bus_tall_01`, tail `dmg_taillight_break`, lamp `headlight_break_on/off_01`) | ledger `why` + B-11 |
| T-FX2 fire states | keep | lore-exact; the roof emitter needs the canopy part + socket (B-02/B-03) | ledger `why` + B-11 |
| T-FX5 23 unreferenced `.effc` | "belong to donor parts" | the 74 holds; the **23 is UNKNOWN** (the producer never states what it counted) and they are donor content, so no carrier is owed | ledger `why` |

### 1.3 Damage and collision — `keep-audit-damage-collision.md`

| row | before | now | where |
|---|---|---|---|
| T-DM3 | `keep` (implicit translation) | **5 @ 20 kept but labelled a donor carry**: no decoded weapon writes `bullet_heavy`, so it is a carrier waiting for a channel | ledger `next` + B-09 |
| T-DM4 | 3 thresholds recorded | **all four**: explosion 4000 / npc_explosion 4000 / smoke 1050 / burn 250, each at its domain top (fleet maximum, not BmAK) | ledger `next` + B-09 |
| T-DM5 | 42 parts, `Boat_Antenna` "not in the table" | **42 (bm-009) / 61 (bm-RC2)**, 17 / 19 types; `Boat_Antenna` **is** a real type (35 boat entities) and only absent from this vehicle's land table | ledger `next` + B-09 |
| T-DM6 | proposed **1** (fleet rule) | **keep 0** under R1; the `1` proposal is withdrawn and the BmAK evidence recorded as UNKNOWN | ledger `next` + B-09 |
| T-DM8 | `keep` | unchanged, `LORE-EXACT (behaviour)`; `TakesDamageFromRam` returns true, so the switch reproduces the observable, not the mechanism | ledger `why` + B-09 |
| T-P2 | 42 parts | **61 parts at RC2, 19 types, 4 fallback types** (`Boat_Antenna`, `Boat_Generic`, `Plane_Control_Surface`, `Train_Generic`) | ledger `next` + B-09 |
| T-CO1 | "32 boxes" (the wreck) | **3 drivable boxes + 56 convex elements** with the decoded extents/centres; the 32-body set is the destroyed asset, which has no chassis body; live mesh per mode UNKNOWN | ledger `next` + B-10 |
| T-CO3 | "wheels are sim-only on both sides" | restated donor carry: BmAK exposes no per-part flag (two whole-car meshes + 3 boxes); RC2's 61 parts make the 42 denominator stale | generator `t22_collision.py` updated, row regenerated, ledger `next` + B-10 |

## 2. The batch plans

`BUILD_BATCHES.md` is generated from the §8 cards and the payload glue, so every item is carried by
a payload file the step applies:

| step | card | payload (rows/values) | what it now carries |
|---|---|---|---|
| **B-07** | Lights module rewrite | `t14_lights.json` (28 / 28) + **`t14_lights_keepaudit.json` (6 / 6)** | the three corrected counts and the derived range/angle/multiplier/blinking |
| **B-11** | Audio bank | `t12_audio_map.json` (53 / 53) + **`t12_audio_keepaudit.json` (7 / 7)** | 24/45 GUIDs, the 120 battle-mode rows, 24 tyre one-shots, the per-part break variants, the fire states, T-FX5's UNKNOWN |
| **B-09** | Private health module | `t10_damage_edits.json` (9 / 9) + **`t10_damage_keepaudit.json` (6 / 6)** | the donor-carry label, the fourth threshold, the 61-part join, the R1 switch, P2's fallbacks |
| **B-10** | Collision | `t16_collision.json` (3 / 3) + **`t16_collision_keepaudit.json` (4 / 4)** | the 3-box + 56-convex drivable asset, the UNKNOWN live mesh, the RC2 hull set, the restated flags |
| **B-25** | new | no payload (declared) | 17 flare entries as part-side emitters; the light-unit probe |
| **B-26** | new | no payload (declared) | the 21 shared-bank GUIDs via a per-entity override |

Gate TX now reads `19 artefacts (17 payloads + 2 records) over 24 B steps`; the step table and the
card-order table both list **B-24, B-25, B-26** with their deps (`B-25`: B-03, B-07; `B-26`: B-11)
and done-lines (17/17 flare entries with a part and socket; stock vs Batmobile playing different
samples on the same 21 GUIDs).

## 3. The gate failure this found, and its repair

`damage_audit.py --build Builds/bm-RC2/aaf` failed: `max_health 36000 … is not declared`, because
`damage_switches.json` scoped the declaration with `"build": "bm-009"` and `applies()` ignored any
declaration whose tag differed. RC2 carries the same module (same sha256) and was therefore
unlicensed. Repair, verified on both builds:

* `damage_switches.json`: `"build": "bm-009"` → `"builds": ["bm-009", "bm-RC2"]`.
* `damage_audit.py`: `applies()` accepts either a `builds` list or the older single `build` string,
  and still refuses any build not listed — the declaration is licensed for exactly the trees that
  carry the value.

```
$ python Tools/scripts/damage_audit.py --build Builds/bm-009/aaf   -> exit 0
29 members, 6 outside the shipped range, 6 declared switches
check ok
$ python Tools/scripts/damage_audit.py --build Builds/bm-RC2/aaf   -> exit 0
29 members, 6 outside the shipped range, 6 declared switches
check ok
```

## 4. Pin upkeep

The edits changed dispositions (`keep` → `next` for eleven rows) but **not** the blocked set and not
the in-scope count, so `WAITS` and `in_scope` in `t_blocked.py` needed no change; only the ledger
sha256 moved, which `t_blocked.py --write` re-pins:

```
$ python Tools/scripts/t_blocked.py --write
wrote Working/Translation/BLOCKED_PROPOSALS.{json,md}: 15 blocked rows (11 ledger + 4 T6) of 216 in scope; 0 tested, 7 resolved
$ python Tools/scripts/t_blocked.py --check
PASS: 15 blocked rows re-derived (11 ledger + 4 T6) of 216 in scope; 0 attempts, all evidence markers present; ledger sha256 unchanged
```

## 5. Checks run

```
$ python Tools/scripts/t22_collision.py --check
PASS: 32 BmAK bodies | 7 mapped / 21 unmapped | 54 donor hull slots, one per part | 38/42 parts collide | rows 3 (next 2, keep 1) | stations unchanged   (exit 0)

$ python Tools/scripts/t_rows.py check
ledger 199 rows | edit 16 next 110 keep 28 epe 26 re-read 0 blocked 11 out 1 superseded 7 | edits 35 over 16 rows
check ok                                                            (exit 0)

$ python Tools/scripts/status_audit.py --check
STATUS.md is current                                                (exit 0)

$ python Tools/scripts/t_blocked.py --check
PASS: 15 blocked rows re-derived (11 ledger + 4 T6) of 216 in scope; 0 attempts, all evidence markers present; ledger sha256 unchanged   (exit 0)

$ python Tools/scripts/t23_closeout.py --check
gate TX: 75 codes (58 carried, 3 named omission, 4 blocked, 10 documented, 0 unmapped) | 199 ledger rows | assumed 1 (0 unsigned) | decisions 11/10 answered | 19 artefacts (17 payloads + 2 records) over 24 B steps
FAIL §11 has 11 decisions, expected D-1...D-10
FAIL B-17: no payload and not declared as a no-payload step
FAIL B-18: no payload and not declared as a no-payload step
FAIL B-19: no payload and not declared as a no-payload step
FAIL B-20: no payload and not declared as a no-payload step
5 problem(s)                                                        (exit 1)

$ python Tools/scripts/damage_predict.py --check                     (exit 0)
$ python Tools/scripts/v_wheels.py --check                           (exit 0, check ok)
$ python Tools/scripts/audit_compromises_t.py --check
72 audited: 1 approved, 71 unapproved; OK: every approval quote re-read at its cited line; document re-derived identically   (exit 0)

$ python Tools/scripts/damage_audit.py --build Builds/bm-009/aaf     (exit 0, check ok)
$ python Tools/scripts/damage_audit.py --build Builds/bm-RC2/aaf     (exit 0, check ok)
```

The five gate-TX problems are the same five present before this pass (the D-1…D-10 count text and
the four no-payload cards B-17…B-20); none is new and none concerns a row or batch touched here.

Two scripts could not be run as checks, both for reasons outside this change:
`t2_lg2.py` needs an installed build (`--ee`; no dropbox under `D:/Games` in this environment), and
`t_boost_rows.py` / `t_vnf_six.py` still fail on their hard-coded 198-row ledger pin (the ledger has
had 199 rows since before this pass).

## 6. COMPROMISES

1. **Light units are declared, not proven.** `range`, `angle` and `multiplier` have no documented
   unit (`LIGHT_SYSTEM.md` §8); T-LG6's map is arithmetic on the decoded `Radius`/`OuterConeAngle`/
   `Brightness` and is marked declared until the Q-1 night take.
2. **`range` 60 and 45 are outside the fleet band** (max 50). They are authored as the decoded
   radius, declared R3, rather than clipped to the band — clipping would undo the BmAK number.
3. **T-DM3 stays a donor carry.** No per-channel armour exists on the BmAK side and no decoded JC3
   weapon writes `bullet_heavy`; the pair is recorded as a carrier waiting for a channel, not as a
   translation.
4. **T-DM6 keeps 0 under R1** with the BmAK evidence UNKNOWN — the cell no longer claims "BmAK has
   no deform", which the record does not prove.
5. **21 of 45 audio GUIDs remain donor** until B-26's per-entity override exists.

## 7. UNKNOWNs

- The renderer's `range`/`angle`/`multiplier` units, and which of `lights[]` / the `.epe`
  `SVehicleLight` the renderer reads (`LIGHT_SYSTEM.md` §8) — one night take settles both.
- Which drivable collision mesh is live per mode (`BatmanVsBatmobileCollisionMode` is not serialised)
  and the box rotations.
- The BmAK per-part damage table and break order — none exists in the record; the 32 bodies are
  wreck geometry.
- T-FX5's "23 unreferenced" count — the producer never states what it counted.
- Whether an entity-level bank override is honoured by the runtime (B-26's stop condition).

## 8. Files changed

| file | change |
|---|---|
| `Working/Translation/T2_TRANSLATION.md` | T-LG1, T-LG2, T-LG3, T-LG6, T-DM3, T-DM4, T-DM5, T-DM6, T-CO1 cells rewritten (T-CO3 regenerated by its own script) |
| `Tools/scripts/t_rows.py` | `DISPO` entries for the twelve audited rows (+ T-P2), with the derivation and the source section in each `why` |
| `Tools/scripts/t22_collision.py` | T-CO3 row text + disposition now `next`; `--write` regenerated the row and `t16_collision.json` |
| `Working/Translation/t14_lights_keepaudit.json`, `t12_audio_keepaudit.json`, `t10_damage_keepaudit.json`, `t16_collision_keepaudit.json` | **new** payloads for B-07 / B-11 / B-09 / B-10 |
| `GRAB_BACKLOG.md` | §8 cards **B-25** (flare carriers + light units) and **B-26** (per-entity bank override) |
| `Tools/scripts/t23_closeout.py` | the four payloads mapped to their steps; B-25/B-26 declared no-payload |
| `Working/Translation/damage_switches.json`, `Tools/scripts/damage_audit.py` | `builds` list support; `max_health` 36000 licensed for bm-009 and bm-RC2 |
| `Working/Translation/T_ROWS.jsonl`, `BUILD_BATCHES.md`, `build_batches.json`, `BLOCKED_PROPOSALS.{json,md}`, `STATUS.md`, `COMPROMISES_T.{md,json}` | regenerated by their own writers |

Revert: restore the eight cells and the `DISPO` entries, delete the four payloads and the two cards,
drop the four glue lines and the two no-payload declarations, put `"build"` back in
`damage_switches.json`, reverse `applies()`, then re-run the writers listed in §5.
