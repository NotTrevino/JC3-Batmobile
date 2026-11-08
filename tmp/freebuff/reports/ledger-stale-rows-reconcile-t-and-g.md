# T-row reconciliation: reports newer than the ledger (read-only, 2026-11-07)

**Purpose.** The T-row ledger was last generated at **11:48** today (`T_ROWS.jsonl` 11:48:13,
`COMPROMISES_T.md` 11:48:40). **29 reports in `tmp/freebuff/reports/` were newer than both at the sweep (32 after this pass's own
two reports landed)**, and one of them
(`review-build-wave.md`) already finds a row citing the wrong cards. This file pairs each newer report with
the row it touches, quotes the line that no longer holds and the line that replaces it, and ends in one
table the operator can work down.

**Nothing was edited and no `--check` was run.** `T_ROWS.jsonl`, `COMPROMISES_T.*`, `GRAB_BACKLOG.md`,
`STATUS.md` and every report are untouched. The only writes are this file and its two read commands.

## 0. How the ledger is wired (this decides *where* the edit goes)

`COMPROMISES_T.md` is **generated**: "Counts are computed by the script from `dispo`, never typed" and
"`--check` asserts ... the rendered markdown/JSON match a fresh re-derivation" (`COMPROMISES_T.md` §5).
So a hand edit to `COMPROMISES_T.md` is undone by the next run. The operator edits **`T_ROWS.jsonl`**
(`dispo` + `cells`) and then regenerates with `audit_compromises_t.py --write` — that is a **write**, and
it is the operator's step, not this pass's.

Two consequences for the list below:

1. every "change" is a change to a **`T_ROWS.jsonl` row** unless it is marked *(COMPROMISES_T text)*, in
   which case it disappears on regeneration and only the row matters;
2. a `dispo` change also moves the count table at the top of `COMPROMISES_T.md` (`next 48`, `blocked 11`,
   ...). The numbers below say which.

## 1. Baseline

```
$ stat -c '%y %n' Working/Translation/COMPROMISES_T.md Working/Translation/T_ROWS.jsonl
2026-11-07 11:48:40.458038600 -0600 Working/Translation/COMPROMISES_T.md
2026-11-07 11:48:13.474160800 -0600 Working/Translation/T_ROWS.jsonl

$ find tmp/freebuff/reports -maxdepth 1 -name '*.md' \
    -newer Working/Translation/COMPROMISES_T.md -newer Working/Translation/T_ROWS.jsonl
29 files, 11:52 → 18:58
```

| quantity | value |
|---|---:|
| ledger rows (`T_ROWS.jsonl`) | 199 |
| `COMPROMISES_T.md` audited rows | 72 (`next` 48 · `blocked` 11 · `edit` 10 · `superseded` 2 · `keep` 1) |
| reports newer than the ledger | **29** at the sweep, **32** after this pass's two reports |
| of the 32, quoting a `T_ROWS` id | 15 |
| of the 32, quoting only a card with **no** `T_ROWS` row (`T-12`, `T-22`, `V-0x`, `B-xx`) | 10 |
| of the 32, build/verify/tooling with no row at all | 7 |

(15 + 10 + 7 = 32, counted by matching every `T_ROWS` id and the card ids against each file's text —
not by eye. `moving-parts-behaviour-gaps-closest-system-plan.md` and this file are the two that landed
after the 18:58 sweep.)

## 2. The newer reports, grouped by the row or card they touch

| group | reports (mtime) | row / card |
|---|---|---|
| **EMP missile** | `immobiliser-launch-payload-build-plan.md` (18:58), `verify-v03-wiring-rc4.md` (11:52, G4 table), `review-build-wave.md` (11:52 §3) | **T-WP4**, T-WP15 |
| **EMP burst** | `T-WP5b.md`, `emp-effects-closest-system-plan.md` (17:26), `emp-burst-fire-route-experiments.md` (18:50), `four-weapon-slot-build-plan.md` (18:52 §"Reconciliation with the EMP card") | **T-WP5**, T-MD2, T-WP15 |
| **weapon slots** | `T-WP13b.md`, `four-weapon-slot-build-plan.md` (18:52), `control-scheme-closest-system-plan.md` (17:23) | **T-WP13**, T-WP3, T-WP9 |
| **mode switch / battle handling** | `T-MD14b.md`, `mode-swap-trigger-closest-system-plan.md` (17:36), `boost-block-selector-closest-system-plan.md` (18:17) | **T-MD5, T-MD6, T-MD7, T-MD8, T-MD13, T-MD14** |
| **moving parts** | `T-12.md`, `moving-parts-behaviour-gaps-closest-system-plan.md` (18:51) | **T-12** (§12 row, no `T_ROWS` id) |
| **steering / driving** | `build-d10-handling-values.md` (11:58), `review-build-wave.md` (11:52), `correction-8396-stale-checkers.md` (12:11) | **T-ST2, T-ST3, T-ST7** |
| **lights** | `correction-8394-light-units-domain.md` (12:11) | **T-L17, T-L28, T-L30** |
| **audio** | `verify-v04-audio-rc4.md` (12:55), `correction-8393-donor-audio-guids.md` (12:56) | **T-AU2, T-AU3** |
| **collision** | `correction-8390-collision-placement.md` (18:07), `collision-missing-shapes-closest-system-plan.md` (17:32), `verify-v02a-silhouette-census-collision.md` (18:47) | **T-22 / B-10** (§12, no `T_ROWS` id) |
| **HUD / radar** | `hud-cluster-closest-system-plan.md` (17:46), `radar-setters-to-jc3-minimap-plan.md` (18:47), `_fair_dryrun.md` (17:41) | **T-DM9** (only) + new HUD rows |
| **recovery / stuck** | `stuck-flip-build-plan-merge.md` (17:29) | **T-RA1, T-SR1** (nearest) + a new row |
| **build / correction / review** | `build-d13-release-candidate-4.md` (12:25), `correction-8391` (12:11), `-8392` (12:43), `-8397` (12:25), `-8398` (12:14), `verify-v01` (12:27), `tracker-rows-reconcile-report.md` (17:44) | **no `T_ROWS` row** — §12 / `STATUS.md` territory |

Two reports sit in two groups (`four-weapon-slot-build-plan.md` in *weapon slots* and *EMP burst*;
`review-build-wave.md` in *EMP missile* and *steering*), so the table's cells sum above the 32 files.

## 3. The pairs: superseded line → replacing line

Quotes are verbatim; the locator after each path is the key or section, because the ledger is one JSON
object per line and the markdown is generated.

### 3.1 T-WP4 — the damage cell and the card citation

| | old | new |
|---|---|---|
| damage | `Working/Translation/T_ROWS.jsonl` `T-WP4` cells[4]: `"damage: no damage to translate"` | `tmp/freebuff/reports/immobiliser-launch-payload-build-plan.md` §2: "`Projectile.Damage` \| 728 \| `FloatProperty` \| `60.0` \| 16 @728 \| BmAK Immobiliser payload damage; the fired archetype has no scalar at all" |
| where it lives | same row, cells[5]: "neither the missile nor a pulse object is in the build" | same report §0: "the damage, damage type and Immobiliser impact sound sit on `Batmobile_EMPMissile_Projectile` (export 16), which **0 exports reference**" |
| cards | same row, `why`: "the 2.0 s lock hold / 8-target salvo / reticle link have no member (cards B-24 / B-25)" | `tmp/freebuff/reports/review-build-wave.md` §3: "row `T-WP4`, cites **B-24 / B-25**. Those are the handling-values card and the lens-flare/light-unit card. T-WP4 is the EMP missile ... Brief **8395** replaces it with the owning cards (B-18 pulse/disable, T-WP3b lock half, B-15 ...)" |

**Change:** `T-WP4` cells[4] becomes `60.0 @728 / DamageRadius 0.0 @732 / MyDamageType Core.RDmgType_BatmobileCannon @712, copied from export 16 (splice re-walks as 14 tags)`; the `why` citation
becomes `B-18 / T-WP3b / B-15`. `dispo` stays `next`. No count changes.

### 3.2 T-WP5 — "36 fields" is 36 rows, and "one named writer" is five routes

| | old | new |
|---|---|---|
| size | `T_ROWS.jsonl` `T-WP5` cells[1]: ``"`RBatmobileEMP` `Batmobile_EMP_Burst` (3 instances, 36 fields)"`` | `tmp/freebuff/reports/T-WP5b.md` §"The decode": "**The row's \"36 fields\" is 36 rows, not 36 fields.** `RBatmobileEMP` declares **16** members; the archetype `Batmobile_EMP_Burst` serializes **12** tags in each of 3 variants = 36 field rows." |
| trigger | same row, `why`: "the missing link is one named writer - BUILD card B-18 with probes Q-EMP-1…4 (report `tmp/freebuff/reports/immobiliser-and-emp-trigger.md` §7-§8)" | `tmp/freebuff/reports/T-WP5b.md` §"T-WP5's closure, reopened": "five separate routes remain, each with a named 5-minute experiment"; `tmp/freebuff/reports/emp-burst-fire-route-experiments.md` §"Decision": "The burst is fired by **route (b), a `CEMPWeapon` in a driver weapon slot** ... **The winner's cost is a slot:** JC3 binds at most two driver weapons, so the EMP takes the secondary slot that currently holds the Vulcan clone." |
| numbers | same row, cells[3]: "the pulse's own position: `(0, 2.0356, 0.6992)` on the truck" | `T-WP5b.md` §"The decode": "Range 7500 uu = 75 m ... Disable duration per power level: 2, 4, 8, 12 s ... Charge time per power level: 0, 0.5, 1.0, 1.5 s ... Cooldown 2.0 s on the archetype, overriding a 10.0 s class default" |

**Change:** cells[1] → `16 members / 12 tags × 3 variants = 36 field rows`; `why` → the five routes with
(b) ranked first and the slot cost stated. `dispo` stays `next`. `B-18` stays the build card, but it now
carries the E1/E2/E3 experiment cards rather than "the" writer.

### 3.3 T-WP13 — the slot model, and the "8 lost" arithmetic

| | old | new |
|---|---|---|
| model | `T_ROWS.jsonl` `T-WP13` cells[2]: "53 armed entities, **max 2 driver slots**, no active-slot index and no next/previous weapon action anywhere in the `.epe`" | `tmp/freebuff/reports/T-WP13b.md` §"The four root properties": "All four sit on all 54 fleet roots ... Exactly two are driver-fired" and "`DrivingMode.SelectVehicleWeapon` (export 104971) is a **fire** body ... There is no active-slot variable in any of the 16 decoded bodies" |
| plan | same row, cells[6]: "**forced (operator ruling 3, 2026-11-06)**: ... Build **four `CCar` roots on the one entity**, each with `main_weapon` (`id:851CAABE`) and `id:00568A74` non-null = **8 slots**" | `tmp/freebuff/reports/four-weapon-slot-build-plan.md` §2: "cannon and the Vulcan on the two proven slots, the missile launcher on spare pointer `id:8580BA42` (a **second weapon component**, fired from `USE_VEHICLE_MOD`) , and the EMP on a **gadget**" |
| count | `COMPROMISES_T.md` §1 `controls` *(generated text)*: "**Build instead:** 2 driver slots bind; a 3rd SelectVehicleWeapon index has no member; 8 weapons have no slot." | `T-WP13b.md` §"Corrections to hand back": "\"8 of 11 lost\" is no longer the summary: 5 weapons have a decoded non-slot carrier, 2 have a candidate pointer, 2 share a position by mode, and only WPN-10 has nothing." |
| indices | `COMPROMISES_T.md` §3.1 *(generated text)*: "`T_WP13_PROPOSAL.md:18` records **3 addressable** (2 decoded binds + 1 index with no member) and **8 lost**" | `T-WP13b.md` §"The first pass was wrong": "BmAK addresses **four** indices, one button each: 1 -> `XboxTypeB`, 2 -> `XboxTypeX`, 3 -> `XboxTypeY`, 4 -> `XboxTypeS_DPad_Up`" |

**Change:** cells[2] keeps "max 2 driver slots" but gains "4 slot properties on 54/54 roots (2 driver,
2 gunner) + 2 spare pointers (`id:8580BA42`, `id:CA86AA17`) non-null on 0/54"; cells[6] → the four-slot
plan (slot 3 = spare pointer, probe P1; slot 4 = use-item gadget, probe P4). `dispo` stays `next`.
The two generated `COMPROMISES_T` lines fix themselves on regeneration.

### 3.4 T-MD8 — turn on the spot: `blocked` → `next`

| | old | new |
|---|---|---|
| carrier | `T_ROWS.jsonl` `T-MD8` cells[4]: "none - G2-21: 5 candidates refuted, 52 module types ... the pivot is native code keyed to the vehicle" | `tmp/freebuff/reports/four-wheel-drive-and-spin-in-place-build-plan.md` §1: "**found, tune + UNKNOWN behaviour** — `CustomLandGlobal.drift.*`" |
| plan | same row, cells[5]: "no pivot in either variant: G2-21 refuted the candidates and found 0 tank-only driving members, and a second entity does not create one" | same report §2: "`drift.min_speed_to_drift_kmph` 10 → **0** ... `drift.constant_drift_torque` 0 → **20000** ... `drift.max_drift_angle_deg` 45 → **30** ... `rear_wheels.arcade_friction_multiplier` 1 → **4.4**" |
| residual | — | same report §2 **UNKNOWN**: "Whether yaw torque is applied at 0 km/h ... **Settling file:** none in the packages — the land-vehicle torque solver in `JustCause3.exe`; settled in practice by pilot card P1" |

**Change:** `T-MD8` `dispo` `blocked` → **`next`**, cells[4]/[5] → the drift-block carrier and the four
tuned values, with "0 km/h application UNKNOWN, pilot card P1" in the verify cell. This is the one
**status** change in the whole reconciliation, and it moves `COMPROMISES_T`'s own table from
`blocked 11 / next 48` to `blocked 10 / next 49`.

### 3.5 T-MD5, T-MD6, T-MD7, T-MD13, T-MD14 — "the variant can carry it" meets "no selector"

| | old | new |
|---|---|---|
| T-MD14 | `T_ROWS.jsonl` `T-MD14` cells[4]: "the battle variant can carry its own graph + usage and the `BML_Battlemode` set (7 events / 24 media) with `BML_Batmobile`'s 32 battle events; the entry/exit sting still needs a transition, not a variant" | `tmp/freebuff/reports/T-MD14b.md` §Summary: "**No member selects which block is active** - the alternatives are real, the selector is not in the files" and "there is **no VTOL and no hover member at all**, no mode enum, no state machine and no `SetMode`-style selector on a vehicle" |
| T-MD5/6/7 | each row's `why` ends "the row waits on D-2's re-resolution to two variants (B-12) and on the runtime swap that is UNKNOWN (`mode-switch-carriers.md` §7 U1)" | `tmp/freebuff/reports/mode-swap-trigger-closest-system-plan.md` §"E1": "second `.ee` — copy of the pursuit leaf with battle modules ... **derived plan**; B-05 writes it" + `boost-block-selector-closest-system-plan.md`: "`arcade.nitro_boost` (156) \| **Pursuit**" |

**Change:** no `dispo` moves (`blocked` stays for MD5/6/7/13/14 — the swap is still B-12's UNKNOWN U1).
The **rationale cell** of each must stop implying a variant toggle exists: the carrier is a *second
entity* (`E1`) precisely because no selector exists. `T-MD14` also gains: "a new `Usage` hash still needs a
consumer (U1)".

### 3.6 T-WP3 — which slot the missile takes

| | old | new |
|---|---|---|
| assembly | `T_ROWS.jsonl` `T-WP3` cells[6]: "clone w618, move it to the free driver slot (T-WP13), and place the 4 fire points on the pod parts" | `tmp/freebuff/reports/four-weapon-slot-build-plan.md` §2: "3 \| 3 · Y (battle) \| WPN-3 Missile launcher \| spare `id:8580BA42` \| `USE_VEHICLE_MOD` (d-pad right / MOUSE3), **displacing turbo jump** \| **a second weapon component**" |

**Change:** cells[6] → the missile is no longer a driver-slot occupant; it rides the spare pointer (P1
gates it). `dispo` stays `next`; the verify cell gains "if P1 fails, slot 3 falls back to mode sharing".

### 3.7 T-ST7 — the ledger already carries the ruling; `COMPROMISES_T` does not

| | old | new |
|---|---|---|
| steering | `COMPROMISES_T.md` §1 `handling` *(generated text)*: "**T-ST7** (`next`, T-3) ... **Build instead:** `t_to_full_steer_s` 0.8 low / 0.6 high. **Loss:** BmAK locks 55 deg in 0.25 s at 220 deg/s; the car steers 2.4-3.2x slower - reopened 2026-11-05." | `tmp/freebuff/reports/build-d10-handling-values.md`: "`T-ST7`'s 0.25 s is `T-ST2`'s member (`t_to_full_steer_s`): the row ruling is applied here as 0.25 s" and its table: "`T-ST2` ... 0.800000012 \| 0.25" / "`T-ST3` ... 0.600000024 \| 0.091" |
| row itself | `T_ROWS.jsonl` `T-ST7` cells[5]: "**next** (operator ruling 2026-11-06, option A, no compromise): **0.25 s low speed** ... and **0.091 s high speed**" | unchanged — the row is already current, which is why the generated text is the stale half |

**Change:** no row edit for the 0.25/0.091 values. The generated `COMPROMISES_T` line is stale *because
the render is older than the row*, so regenerating is enough. **Not** a row change: `review-build-wave.md`
§"T-ST7" reports `v05_driving.py --check` **FAIL** ("the script still asserts it is blocked") — that is a
stale checker, owned by `correction-8396`, not a row.

### 3.8 T-L17 — body-hosted light becomes `donor-carried`

| | old | new |
|---|---|---|
| carrier | `T_ROWS.jsonl` `T-L17` cells[2]: "`Front_Secondary_Head` (graph only, no row)" | `tmp/freebuff/reports/correction-8394-light-units-domain.md`: "**Row 11 (`T-L17`)** keeps the donor graph object's own numbers (`radius 10`, `spot_angle 60`, ...)" and "row 11 (`T-L17`) is marked **donor-carried**, not [a stand-in]" |
| blocked pair | `T_ROWS.jsonl` `T-L28` cells[2]: "**blocked** (socket-absent)" | same report: "`T-L28`/`T-L30` remain blocked (null socket **and** null bone, no [anchor])" |

**Change:** `T-L17` cells[2] → `donor-carried` with `radius 10`, `spot_angle 60`; `dispo` stays `next`.
`T-L28`/`T-L30` unchanged (the report confirms them). No count change.

### 3.9 T-12 — `done`, but its own gate is red and its rows now have a mechanism map

| | old | new |
|---|---|---|
| gate | `tmp/freebuff/reports/T-12.md` §"Done-check command and output": "PASS: 15 rows (11 cut parts, 12 with an animated joint, 4 with a shipped hinge) ... exit status 0" | measured in this session: `python Tools/scripts/t12_parts.py --check` **exits 1** on a stale keyframe path in `Working/Translation/T8_PARTS.md` (the row numbers still print; the MD comparison fails) |
| rows | same report: "15 rows = 11 cut parts + 4 items with no part" | `tmp/freebuff/reports/moving-parts-behaviour-gaps-closest-system-plan.md` §1: every omitted / partial / blocked / UNKNOWN T-12 row grouped by mechanism, with "hinge/rotating rate \| **UNKNOWN** (T-12 §UNKNOWN 1) \| `all_hinged_part_properties` has no rate member" |

**Change:** `T-12` has **no `T_ROWS` row** — its status lives in `GRAB_BACKLOG.md` §12 and reads `done`.
That `done` is not re-derivable today (exit 1). Options, in order: (a) leave `done` and cite the new
mechanism map, (b) flip to `todo` until `t12_parts.py --check` exits 0. Do **not** flip on the plan's word
alone: the plan is a classification, not a re-decode.

### 3.10 T-22 / B-10 — the 5 cm gate statement

| | old | new |
|---|---|---|
| gate | `tmp/freebuff/reports/correction-8390-collision-placement.md` §"corrections", quoting the earlier bullet: "Rebuild B-10 with the chassis box's own placement … to clear the 5 cm gate" (status `to do`) | same report, same row: "done; the bullet should read \"the gate is met; the shape count is the open half\"" |
| consequence | `tmp/freebuff/reports/collision-missing-shapes-closest-system-plan.md` §3.6 reading: "0 free hull slots" as the blocker | same plan: "box 1 protrudes past box 0 by **3.640 cm** and box 2 lies entirely inside box 0, so one body-0 hull to the union ... closes the gap inside the 5 cm gate with **no second instance**" |

**Change:** the `B-10`/`T-22` §12 evidence cells must stop calling the placement gate failed; the open half
is the **shape count** (2 of 3 boxes without a shape instance, 0/54 free hull slots). No `T_ROWS` row
exists. `verify-v02a-silhouette-census-collision.md` (18:47) adds the shipped-bytes measurement.

### 3.11 Rows that need no change (checked, so the operator can skip them)

| row | newer report | why it stands |
|---|---|---|
| `T-WP15` | `T-WP5b.md`, `emp-effects-closest-system-plan.md` | still a named omission (`out`); no member appeared on either side |
| `T-WP9` | `T-WP13b.md`, `control-scheme-closest-system-plan.md` | carrier unchanged; the new report only says a gadget slot may host it by mode — an additive note, not a correction |
| `T-AU3` | `verify-v04-audio-rc4.md`, `correction-8393` | 21 donor GUIDs still donor; no number moves |
| `T-AU2` | `correction-8393` | `keep`; the report only names it as the stated gap |
| `T-DM9` | `hud-cluster-closest-system-plan.md` | the plan quotes `max_health 36,000 (T-DM9, B-09)` — agrees with the row |
| `T-RA1`, `T-SR1` | `stuck-flip-build-plan-merge.md` | nearest carriers only (`AddTorqueOverTime` + `AddKeepyUpForce`, `DriverLean.righting_torque`); `blocked`/`next` unchanged |
| `T-WP4` lock half | `T-WP4d.md` (11:39, *older than the ledger*) | already folded into the row's "2.0 s lock hold ... has no member" |

## 4. Operator table — the one to work down

Order: run the **read-only** check, read the printed line, then edit the named `T_ROWS.jsonl` key, then
regenerate `COMPROMISES_T` (`--write`, operator-only). Every check in this column is quoted from the report
and **was not run here**; the two commands marked **WRITE** are the regeneration steps, never a check.

| # | row | change | run this (read-only) | expect |
|---:|---|---|---|---|
| 1 | `T-WP4` | cells[4] `damage: no damage to translate` → `Damage 60.0 @728 / DamageRadius 0.0 @732 / RDmgType_BatmobileCannon @712 from export 16`; `why` cards `B-24/B-25` → `B-18 / T-WP3b / B-15` | `python Tools/scripts/wp4_emp_payload_check.py` | pointers PASS ×6, payload currently FAIL ×12 (the baseline the edit closes) |
| 2 | `T-WP5` | cells[1] `36 fields` → `16 members / 12 tags × 3 = 36 field rows`; `why` → the five routes, (b) first, slot cost named | `python Tools/scripts/t_wp5b.py --check` | `PASS: T-WP5b 0 failure(s)` |
| 3 | `T-WP13` | cells[2] += the 4 slot properties + 2 spare pointers; cells[6] → the four-slot plan (slot 3 = `id:8580BA42`, slot 4 = gadget) | `python -I Tools/scripts/t_wp13b.py --check` | `CHECK OK: 13 oracles, 11 weapons, 4 slots + 2 spare pointers` |
| 4 | `T-MD8` | `dispo` `blocked` → **`next`**; cells[4]/[5] → `CustomLandGlobal.drift.*` + the four values; verify cell = "0 km/h UNKNOWN, P1" | `python Tools/scripts/t_md14b.py --check` | `hits 1, air 13, blocks 9, donor 15 values` (the state census the plan rests on) |
| 5 | `T-MD5`, `T-MD6`, `T-MD7`, `T-MD13`, `T-MD14` | rationale cell: no selector exists; the carrier is a second entity (`E1`). `dispo` unchanged | same `t_md14b.py --check` | as #4 |
| 6 | `T-WP3` | cells[6] driver slot → spare pointer `id:8580BA42` via `USE_VEHICLE_MOD` | `python -I Tools/scripts/t_wp13b.py --check` | as #3 (the spare pointers are 3 of its 13 oracles) |
| 7 | `T-ST7` | **no row edit** (already 0.25 / 0.091); regenerate only | `python Tools/scripts/v05_driving.py --check` | currently **FAIL** on the stale `blocked` pin — `correction-8396` owns it, do not read it as a row error |
| 8 | `T-L17` | cells[2] → `donor-carried`, `radius 10`, `spot_angle 60` | `python Tools/scripts/bm_rc4_lights.py --check` | light rows re-derive; row 11 `donor-carried` |
| 9 | `T-12` (§12) | decide `done` vs `todo`: the mechanism map is in, the gate is red | `python Tools/scripts/t12_parts.py --check` | **exit 1** today (stale keyframe path in `T8_PARTS.md`) |
| 10 | `T-22` / `B-10` (§12) | evidence cell: placement gate met; open half = 2 of 3 boxes without a shape, 0/54 free slots | `python Tools/scripts/t22_reopen.py --check` | `10/10 oracles` |
| 11 | `COMPROMISES_T.md` | *(after #1-#8)* regenerate from the rows | **WRITE — operator only**: `python Tools/scripts/audit_compromises_t.py --write`, then `... --check` | `next 49 / blocked 10` after #4; the T-ST7 and T-WP13 lines re-render |
| 12 | `STATUS.md` | *(after #11)* the pin counts follow the rows | **WRITE — operator only**: `python Tools/scripts/status_audit.py --write`, then `--check` | `STATUS.md is current` |

## 5. What this pass could not settle

1. **No `--check` was run**, per the brief. Every "expect" column is the report's own quoted output; the
   T-12 exit 1 is the one measured in this session, by `t12_parts.py --check` (it writes nothing).
2. **`T_ROWS.jsonl` has no row for `T-12`, `T-22`, `V-01…V-07` or any `B-xx` card.** Those statuses live
   in `GRAB_BACKLOG.md` §12 (`217` rows), which is a different tracker; #9/#10 are therefore §12 edits,
   included because the file name and the collision/moving-parts reports cross both.
3. **`T_ROWS.jsonl` has no "as of" field.** A row and the report it cites can disagree only because of
   mtime; where a report states no date and the row states none, the verdict above is a content
   comparison (does the claim still hold), not a timestamp one.
4. **`correction-8395-twp4-card-citation.md` is older than the ledger** (11:39 vs 11:48) and is therefore
   not in the 29; `review-build-wave.md` re-states its finding, which is why the `T-WP4` citation pair is
   still actionable.
5. **`T-WP9`'s `bInstantFire` is UNKNOWN on the tracker** (`T-WP4d.md` C1: 0 of 3 `Vehicle_Tracker`
   records serialize offset 2464) and **no `T_ROWS` cell claims it** — an addition, not a correction, so it
   is not on the table. The file that settles it is the runtime read of `Default__RBatmobileVehicleTracker`
   at 2464, not a package.
