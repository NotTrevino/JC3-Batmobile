# D-2 reopened — applying the two-mode rows (T-MD5…T-MD8, T-MD13, T-MD14)

**Task:** reopen decision **D-2** (`GRAB_BACKLOG.md` §11) on the evidence that BmAK has two modes and
a hybrid cannot carry rows **T-MD5, T-MD6, T-MD7, T-MD8, T-MD13, T-MD14**; write the two-mode plan
(what flips, which member, which carrier) on the closest JC3 system with the gap the build must
fill; re-open **card B-12** with its new preconditions; update the affected ledger rows; keep
`BLOCKED_PROPOSALS` and `t_blocked.py` pins consistent; and record every build step that changes if
two variants are carried.

**State after this pass:** D-2 reads **REOPENED 2026-11-06** (2026-10-28's answer kept as history),
B-12 is `todo: D-2 reopened` with four preconditions, five rows moved `out` → `blocked`, T-MD14's
wait was restated, and the pin chain is green (18 blocked of 216). **Nothing was built, launched or
installed**; no build tree, bank or dropzone file changed.

Labels: **decoded** = read at the file/member named; **derived** = arithmetic over decoded inputs;
**UNKNOWN** = searched and absent, with where it would be settled.

---

## 0. Answer

BmAK's car has **two modes with two value sets**. Every JC3 handling member is a single static value
per module instance, so one entity cannot hold both: the mode has to be **an entity**, and the
switch has to be a **swap**. That is what the research notes establish, and it is why the six rows
were `out`/`blocked` rather than mistranslated. Reopening D-2 does **not** by itself make the rows
buildable: the second value set exists in JC3 (the `_signature_shielded` / `_military_01` entity
pattern), but nothing in the data selects one at runtime (`mode-switch-carriers.md` §7 **U1**), and
two of the six rows (T-MD8, T-MD14) stay carriers-missing even with two entities.

| question | answer | evidence |
|---|---|---|
| does BmAK have two modes? | yes — `BattleMode*` 42 declared / 15 serialised, `TurnOnSpot*` 4/3, `Transformation*` 9/4, `TurningModeMaxSpeed` 600 cm/s | `Research/BatmobileGrab/MODES.md` via `mode-switch-carriers.md` §1 |
| can one entity carry both? | no — 0 handling members switch at runtime; the boost state is the only in-place change and it multiplies, not swaps | `mode-switch-carriers.md` §2.4, §2.7, §3 |
| what is the closest system? | the **entity variant** (second `.ee` of one chassis) for the numbers; the **`arcade.nitro_boost`** state for semantics; the **hinged-part table** for the pose; the **`EngineNitro` usage** for audio | `mode-switch-carriers.md` §4, `battle-audio-switch-event.md` §4 |
| what is the gap? | a **selector/swap** (U1) + a per-entity value set the build writes; plus four member absences (cap, slip, pivot, usage consumer) | §3, §4 below |
| does D-2 (a) close all six? | **no** — four flip to the battle variant, T-MD8 and T-MD14 stay named omissions | §3.4, §3.6 |

---

## 1. What BmAK's two modes actually change (the target)

From `Research/BatmobileGrab/MODES.md` (generated from `BMSDK_OFFSETS.json`, `objects.jsonl`,
`OFFSETS.json`), as tabulated in `mode-switch-carriers.md` §1:

| family | declared | serialised | what a mode switch changes |
|---|---:|---:|---|
| `BattleMode*` | 42 | 15 | top speed, steering, throttle split, engine braking, upright torque, slope factor |
| `TurnOnSpot*` | 4 | 3 | front/rear torque factors (0.8 / −0.8), engine-braking factor 2 |
| `Transformation*` | 9 | 4 | turn torque 3000 / decel 24000, rotation rotator, `TransformationAnimNode` (not serialised) |
| `TurningModeMaxSpeed` | 1 | 1 | **600 cm/s = 21.6 km/h** cap |
| `ArmourModeDamageReduction` | 1 | 1 | **0** shipped, every package that carries it |

The six ledger rows pick six of these: the battle top-speed curve (`BattleModeVSpeedCurve`, 0→60,
600→40, 1200→30), the 21.6 km/h cap, the six battle drive/slip factors, turn-on-the-spot, the stance
(`TransformationTurnTorqueFactor` 3000 / `…DecelTorqueFactor` 24000 + the unserialised anim node),
and the two transformation `AkEvent` sounds (V2 62 / 47, MK2 60 / 45, Joker 191 / 176, Funhouse
60 / 45).

---

## 2. The closest system, per row (closest JC3 pattern → member → carrier)

This is the "closest system with the gap the build must fill" the card asks for, one row at a time.
**Member** is the JC3 module member that would hold the value; **carrier** is where it lives in a
two-variant world.

| row | BmAK need | closest JC3 system | member | carrier | gap the build must fill |
|---|---|---|---|---|---|
| **T-MD5** | `BattleModeVSpeedCurve` 0→60, 600→40, 1200→30 | the **boost state** (`arcade.nitro_boost`: `torque_multiplier`, `grip_multiplier`, `extra_top_speed`, `boost_blend_time`) — the only runtime handling change in the fleet | `arcade.*` + `vehicle_misc.official_top_speed` (T-E5) / `land_aerodynamics.top_speed_drag_coefficient` (T-A3) | **battle entity** (its own module set) | no member takes a *curve*: the 3 points stay raw; the values are per-entity constants, and the swap (U1) is what makes them apply |
| **T-MD6** | `TurningModeMaxSpeed` 600 cm/s = 21.6 km/h | per-entity speed values; no cap member exists in the 52-module vocabulary | **UNKNOWN** — nearest decoded speed members are `vehicle_misc.official_top_speed`, `arcade.nitro_boost.extra_top_speed`, `land_aerodynamics.top_speed_drag_coefficient` | battle entity | **which member caps speed is not decoded**; B-12 must read the battle copy's modules, or the cap becomes a torque proxy (derived: the battle curve reads **40/60 = 0.667** at 600 cm/s vs 0 — unit undocumented) |
| **T-MD7** | `BattleModeDriveForceFactor` 500, `LatSlipScale` 0.75, `LongSlipScale` 1.25, `SteerAngleFactor` 1, `TrailingSteerFactorMoving` −0.25, `DrivingForceZOffset` 20 cm | the **boost multipliers** (partial) + the single-car handling rows | `land_steering.steer_angle_min/max_speed_deg`, `min/max_speed_kmph`, `steer_curve_falloff` (T-ST1, T-ST5); torque factors T-E3; `rigid_body.mass` T-M1 | battle entity | `SteerAngleFactor` **1** ⇒ the steering angle does not change; the two **slip scales have no member** on either side ⇒ partial carry |
| **T-MD8** | `TurnOnSpotFrontTorqueFactor` 0.8 / `Rear` −0.8 / engine-braking 2 / `BattleModeTurnOnSpotTorqueFactor` 0.333333 | **none** — G2-21 refuted 5 candidates, 52 module types, 262 tank-unique values, 0 in a driving module | — | **none, in either variant** | a native pivot keyed to the vehicle; a second entity does **not** create one (`drift` torque at 0 km/h stays UNKNOWN) |
| **T-MD13** | stance (`TransformationTurnTorqueFactor` 3000, `…Decel` 24000, `TransformationAnimNode` absent) | the **hinged-part table**: `all_hinged_part_properties` maps a part to a driving variable (`landing_gears_T`, `air_brakes_T`, `hatches_T`) | the same table (T-12's part angles) | battle entity's part transforms (pose = per-entity constant) | **pose yes, animation no**: `TransformationAnimNode` has no JC3 analogue (0 values in any file); the torque factors have no counterpart |
| **T-MD14** | 30 battle events / 75 WEMs (32 names in `BML_Batmobile`; the steering bed `0xD28CAFB1` in `BML_Battlemode`, 7 events / 24 media) | the **`EngineNitro` usage** (4197885156, 18 vehicles, 307 objects) — a state name that already switches a sound + effect set | `.epe` `Usage` int on the state object + `vehicles.bank` `EVTS` | battle entity's graph + the shared bank | a **`BattleMode` usage the engine dispatches on** (U1) and an entry/exit **transition**; a swap is not a transition |

---

## 3. The two-mode plan — what flips, which member, which carrier

Built on the **entity-variant** pattern (`mode-switch-carriers.md` §5 Option A): one chassis, two
`.ee` entities, the battle copy carrying its own values. Pursuit is the delivered car (RC2 values);
battle is the second entity. "Flips" = what differs between the two.

### 3.1 Shape

| | pursuit | battle |
|---|---|---|
| entity | `…_civilian_01.ee` (today's build) | second `.ee` of the same chassis (name/hash: B-13) |
| drop entry | B-13's single item | **second** item (D-2 (a): "two Rebel Drop entries") |
| handling | T-A1/T-B2/T-E3/T-ST1 values | its own `CustomLandGlobal` / `land_steering` / torque values |
| pose | parts parked (T-12) | deployed pose (T-12 angles), held as part transforms |
| weapons | all (D-7) | all (D-7) — no per-mode split |
| audio | T-16's drive slots | drive slots + its own usage (if U1 lands) |
| swap | — | D-11's **LT hold battle / release pursuit** (decoded control, not a data selector) |

### 3.2 T-MD5 — battle top-speed curve

* **flips:** the speed envelope. Pursuit = T-E5's `official_top_speed` 336.4 km/h with T-B2's boost
  delta; battle = the curve's own shape (0→60, 600→40, 1200→30, unit undocumented, carried raw).
* **member:** `arcade.nitro_boost.extra_top_speed` / `vehicle_misc.official_top_speed` — a **value**,
  not a curve.
* **carrier:** battle entity's module set.
* **what the build must add:** the per-entity value (B-12 writes it into the battle copy) and the
  swap that applies it. No curve member exists in any of the 52 module types.

### 3.3 T-MD6 — 21.6 km/h turning cap

* **flips:** the cap. Pursuit has none; battle is limited to 600 cm/s.
* **member:** **UNKNOWN**. The three decoded speed members are a stat (`official_top_speed`), a boost
  delta (`extra_top_speed`) and a drag coefficient (`top_speed_drag_coefficient`) — none is a cap.
* **carrier:** battle entity, *if* a cap member exists on it; otherwise the cap is expressed through
  the torque collapse the curve already describes (**derived**: 40/60 = 0.667 of the 0 cm/s factor
  at 600 cm/s).
* **what the build must add:** the member read at B-12 (the battle `.ee`'s module set), then either a
  written cap or a declared torque-proxy compromise.

### 3.4 T-MD7 — battle steering / drive factors

* **flips:** four of six factors land on existing members: `DriveForceFactor` 500 (engine gain),
  `TrailingSteerFactorMoving` −0.25, `DrivingForceZOffset` 20 cm, and `SteerAngleFactor` **1** (no
  change to `land_steering.steer_angle_*`).
* **member:** `land_steering.*` (T-ST1/T-ST5), the T-E3 torque factors, and `rigid_body.mass` (T-M1).
* **carrier:** battle entity.
* **what the build must add:** the two **slip scales** (`LatSlipScale` 0.75, `LongSlipScale` 1.25)
  have **no member**; they stay a declared partial. No per-mode steering table exists.

### 3.5 T-MD8 — turn on the spot

* **flips:** nothing. Neither variant has a pivot carrier.
* **member:** none (G2-21: 5 candidates refuted, 0 tank-only driving members, 262 tank-unique values
  with 0 in a driving module).
* **carrier:** **none**.
* **what the build must add:** a native mechanism (UNKNOWN). This row is why "two variants" is not a
  blanket fix: it stays a named omission and its ledger wait says so.

### 3.6 T-MD13 — transformation stance

* **flips:** the pose. Pursuit parts are parked; battle holds the deployed angle set (T-12).
* **member:** the `all_hinged_part_properties` rows (`part → *_T` driving variable) and the part
  transforms that hold an angle; the animation member does not exist.
* **carrier:** battle entity's part transforms (a per-entity constant).
* **what the build must add:** the pose values in the battle graph; `TransformationAnimNode` and the
  3000/24000 turn-torque factors stay UNKNOWN, so the *transition* remains a named omission.

### 3.7 T-MD14 — battle audio

* **flips:** the graph's usage object and the event set it names.
* **member:** the `.epe` `Usage` int on the state object; `vehicles.bank` `EVTS` for the samples.
* **carrier:** battle entity's graph + the shared bank (no second bank is needed; the media come from
  `BML_Battlemode`, 7 events / 10 actions / 44 sounds / 24 media / 830,548 B).
* **what the build must add:** a **`BattleMode` usage hash the engine dispatches on** (U1) and the
  import of the battle media; the entry/exit sting (`Play_BattleMode_In_*` / `Out_*`) still needs a
  *transition*, which an entity swap is not. Stays blocked.

### 3.8 Not in the six, but affected

T-MD10 (`ArmourModeDamageReduction` 0) and T-MD11 (battle FOV 60 inside the delivered 55–63 band) are
the two rows `keep-audit-world-modes.md` §3 says "turn on the mode switch". Both stay **compromises**:
0 is the shipped value, and 60 already sits in the band — a second variant changes nothing for them.

---

## 4. The gap the build must fill (one list)

1. **A selector** — nothing in any module, entity graph or `.physicsc` chooses a value set
   (`mode-switch-carriers.md` §2.7). The variant pattern only says *two entities exist*; it does not
   say how one becomes the other. **U1**, game-side.
2. **A second value set** — supplied by the battle `.ee` (this is the cheap half; the values are
   decoded).
3. **A cap member** (T-MD6) — none decoded; B-12's member read settles it or the row declares the
   torque proxy.
4. **Slip members** (T-MD7) — none exist; partial carry by definition.
5. **A pivot** (T-MD8) — native, no carrier even with two variants.
6. **A usage consumer** (T-MD14) — a new `Usage` hash must be recognised (`battle-audio-switch-event.md`
   §8 U1/U2), and a transition must exist for the `In_/Out_` stings.

---

## 5. Card B-12 — reopened, with its new preconditions

`GRAB_BACKLOG.md` §8 now reads (abridged; the file has the full text): heading
`B-12 · Variants (only if D-2 = two variants) — REOPENED 2026-11-06`, deps `B-05…B-11, T-15 re-run`,
and **four preconditions, none met today**:

| # | precondition | state (re-derived) | how `b12_variants.py` sees it |
|---|---|---|---|
| 1 | D-2 re-resolved to **(a) two variants** | open — §11 reads REOPENED | fails when §11 loses REOPENED without a recorded answer; passes while it reads reopened |
| 2 | `t11_modes.py` re-run to emit **two row sets** (schema 2) | not done — `t11_variants.json` declares **1** variant (`hybrid`) | fails when the table declares ≠1 variant |
| 3 | a **runtime entity swap** | UNKNOWN (U1) | reported `UNKNOWN` every run; can never be derived from disk |
| 4 | `bm_build.py --variant pursuit\|battle` + a second tree | not done — `--variant` absent, 0 variant-named trees | fails when the flag or a variant tree appears |

`b12_variants.py --check` now inverts the old sense: it passes while the card is **live and unbuilt**
and fails the moment a precondition is met ("the card is buildable and must not stay a todo"), or if
the register silently reverts to `skipped: D-2`.

**Done** (unchanged in substance): `aafdiff` between variants lists only the files the variant table
names — **plus** the new clause that T-MD8 and T-MD14 remain named omissions even when it passes.

---

## 6. Every build step that changes if two variants are carried

Today every card builds **one** tree. With two variants, the changes are:

| step | today (hybrid) | with two variants | why |
|---|---|---|---|
| **B-01 scaffold** | one tree from `test-091`, `receipt.json`, `install.ps1` | `bm_build.py --variant pursuit\|battle`, **two** trees, one receipt + installer per tree; the cross-variant `aafdiff` becomes a gate | the card's Do-line names `--variant`; the identity control (`bm-001`) stays single |
| **B-02 parts (meshes)** | 59 parts, 5 LODs | **unchanged** mesh set — the battle stance is part *angles*, not new meshes; re-verify every pose angle stays inside its part's pivot/LOD | the pose needs no second carve |
| **B-03 lights (`CarLight`)** | 8 lamp parts, 24 blocks | unchanged geometry | lamps exist in both variants |
| **B-04 parts module** | one `…vehicle_parts.vmodc`, `hinged_parts` 4, `rotating_parts` 1 | one module preferred; the pose goes in the **battle `.epe`'s part transforms**. A second module is needed only if the deployed pose needs a hinge limit the shipped rows do not give | R7 keeps shared modules private, so a second module is a real fork |
| **B-05 entity graph** | 467 objects, one `.epe` | **two `.epe`s from one plan**; the battle graph differs in: part-transform rows (pose), `SVehicleLight` rows (battle lamps), the audio usage object, and any per-mode module reference. Two `ConvertProperty` round trips, two object-count assertions | the graph is where a variant's identity lives |
| **B-06 weapons** | 4 components + 9 points, private tunes | **unchanged count** — D-7 keeps every weapon in both modes, so both graphs reference the same private files | weapons are not mode-gated |
| **B-07 lights module** | 18 entries, 1 module | stays one module: the fleet has **9 light behaviours and 0 battle value**, so T-L17…T-L20 ride `HeadLight` in both. Only a per-variant row set (if the operator ever accepts one) would fork it | no battle behaviour exists |
| **B-08 effects** | 2 emitter `world` edits in the graph | **×2** (graph objects): both variants need the afterburner placement, and a battle-only effect would need its own row | effect placement is graph data |
| **B-09 health** | one private health module (36,000 HP, `deform_scale` 0) | **one module, referenced twice** — `ArmourModeDamageReduction` is 0 in every package, so there is no second damage profile to build | T-MD10 |
| **B-10 collision** | one `batmobile.physicsc` (5 hulls), `batmobile_hinged.physicsc` (13 constraints, hinges 11/12) | same file **unless** the battle stance raises the turret: then the battle copy needs the raised pose's hull/constraint set (second `.physicsc` or a constraint at the pose) | the hull follows the geometry |
| **B-11 audio bank** | 2 private bank copies, 5 swapped payloads, 45 GUIDs | **one bank set** (banks are global); new work is the `BML_Battlemode` media import **only if** the usage consumer exists (U1). The two transformation stings stay unbound | T-MD14 |
| **B-12 variants** | skipped | **runnable**: build both entities, diff them, assert the diff is exactly the table's rows | this pass |
| **B-13 Rebel Drop** | 1 item (197 items total), one name/blurb pair, one icon | **2 items** (D-2 (a)), two leaf hashes, name/icon per entry; `bm_rebel.py --check` counts move; the second entry's display name is an operator call | D-2 (a) |
| **B-14 RC tree** | one dropzone tree, `receipt.json`, `install.ps1` | **one tree per variant set**; the receipt lists both payload sets; rollback copies double; `bm_rc*.py`'s `"variants": "one tree (D-2 = one hybrid car)"` field becomes a two-tree record | the RC ships what B-12 builds |
| **B-17…B-21** | each edits the one graph | each edit applies **twice** (two graphs); any card whose payload is graph-side doubles, a tune-side card does not | they all deps B-05 |
| **T-15 re-run** | 1 row set + `t11_variants.json` schema 1 | **2 row sets**, schema 2 (`pursuit` / `battle`), 15 rows each; the hybrid set stays as the record | B-12 precondition 2 |
| **T-16 / W-08** | battle row blocked | still blocked, but now names the second entity as the host | §3.7 |
| **V-01 / V-02 / V-03** | one payload, one silhouette, one wiring set | re-run **per variant**; V-02's silhouette is unchanged (one mesh) but the *bounds* move if the pose does | verification follows the trees |
| **V-04 audio** | 5 payloads measured | unchanged unless the battle media land | U1 |
| **V-05 / V-06** | `Q2-battle` recorded as **excluded by decision** (27 + 1 checks); V-06's file set "one tree" | `Q2-battle` becomes a real take (28 checks); V-06's receipt set question (`:120`, `:139`, `:287`) resolves to two trees; Q-2 take 17 and `Q-5`'s `bm-001` requirement change wording | the decision they cited moved |
| **pull-side docs** | `Research/specs/{B-12,B-13,B-14,V-05,V-06,Q-2,Q-5}.md`, `v05_predictions.py:67`, `bm_rc*.py` receipt field | stale until re-run; they describe the 2026-10-28 answer | recorded here, **not** edited (see §8 limits) |

---

## 7. What this pass changed, and the pins

### 7.1 Ledger (`Working/Translation/T_ROWS.jsonl`, 198 rows)

| row | before | after | reason |
|---|---|---|---|
| `T-MD5` | `out` — "omitted: the car keeps one top speed" | `blocked` — battle variant's own values; waits D-2 + swap | a hybrid cannot hold a second curve; the battle entity can |
| `T-MD6` | `out` — "omitted: no 21.6 km/h battle cap" | `blocked` — per-entity constant, **cap member UNKNOWN** | needs the second value set **and** a member read |
| `T-MD7` | `out` — "omitted: one handling set" | `blocked` — four factors land, two slip scales have no member | partial carry on the battle entity |
| `T-MD8` | `out` — "omitted: no pivot" | `blocked` — no pivot in **either** variant | G2-21; the reopen does not close it |
| `T-MD13` | `out` — pose reachable, change not | `blocked` — battle parts hold the pose; animation absent | pose is per-entity, animation is not |
| `T-MD14` | `blocked` (old wait) | `blocked` — wait restated: usage consumer + second variant | the host exists now; the consumer does not |
| `T-MD15` | "B-12 is `skipped: D-2`" | annotated: B-12 `todo: D-2 reopened` | it asserted the withdrawn answer |

Totals: `next 75 keep 60 epe 26 blocked 14 out 0 superseded 7`; **in scope 211 → 216**;
**blocked 13 → 18** (14 ledger + 4 T6).

### 7.2 `BLOCKED_PROPOSALS` + `t_blocked.py` pins

* `WAITS` gained five rows (`T-MD5`, `T-MD6`, `T-MD7`, `T-MD8`, `T-MD13`) and `T-MD14`'s line was
  rewritten to "a `BattleMode` usage … plus a second variant to hang T-16's 30 battle-mode events on
  (B-12)".
* `reconciles` pin: `9 ledger / 13 blocked / 211 in scope` → **`14 ledger / 18 blocked / 216 in
  scope`**; the module docstring's counts were corrected with it.
* `python Tools/scripts/t_blocked.py --write` then `--check` → **PASS** (see §8). The generated
  `BLOCKED_PROPOSALS.{json,md}` now enumerate **18**, with the five new waits in ledger order.

### 7.3 Other files touched

* `GRAB_BACKLOG.md` — §11 D-2 (reopened, options, history, note that approval A-02 is provisional
  until D-2 re-resolves), §8 B-12 (reopened + preconditions), §12 rows `T-MD-D2-reopen` (new),
  `B-12` (`todo`), `T-15` (hybrid record), `T-BLOCKED` (18 of 216).
* `Tools/scripts/t11_modes.py` — the six rows' cells/dispositions (`out` → `blocked`, T-MD14/T-MD15
  prose), the doc's D-2 paragraph and decision row, the `decisions` check (now requires `REOPENED`
  **and** the 2026-10-28 answer as history), and the emitted table's `B-12` field.
* `Tools/scripts/b12_variants.py` — rewritten to check the reopened card and its four preconditions.
* `MODLOG.md` — §"2026-11-06 · D-2 reopened — the two modes need two variants (task 8301)".
* Regenerated by their own generators: `T11_MODES.md`, `t11_variants.json`,
  `BLOCKED_PROPOSALS.{json,md}`, `STATUS.md`, `COMPROMISES_T.{json,md}`,
  `BUILD_BATCHES.md`/`build_batches.json`.

---

## 8. Verification actually run

All commands in `E:/Modding/JustCause3/JC3-Batmobile` with `PYTHONIOENCODING=utf-8` (plain `--write` on
`status_audit.py` exits 1 printing `→` to cp1252).

| check | result |
|---|---|
| `t_blocked.py --write` then `--check` | **PASS** — 18 blocked (14 ledger + 4 T6) of 216; 2 attempts, all markers present; ledger sha unchanged |
| `t11_modes.py --check` | **PASS** — 15 rows (MOD-1 4 / MOD-2 11), ledger 15/15 |
| `b12_variants.py --check` | **PASS** — live and unbuilt; 4 preconditions; `--variant` False; 0 variant trees |
| `t_rows.py check` | ok — 198 rows, `blocked 14 out 0` |
| `status_audit.py --check` | current (STATUS.md regenerated; it also carried older staleness: 112 → 216 in-scope) |
| `audit_compromises_t.py --check` | OK — 72 audited, 1 approved, quotes re-read at their lines |
| `t_md14.py --check` | OK — 6 oracles, 30/30 pairings |
| `bmak_coverage.py --check` | OK |
| `t23_closeout.py --check` | **FAIL — 6 pre-existing problems**, unrelated to this change: `B-17`…`B-21: no payload and not declared as a no-payload step` (the same family as the 2 noted in the T-18 entry; four more cards have been added since). Its drift caused by this ledger move was regenerated |

`audit_compromises_b.py --check` was already **red before this pass** (line 56 of
`Working/RC/COMPROMISES_B.md` differs from its sources) and was left alone.

**Limits, stated:** no game was launched and no BmAK or JC3 file was decoded in this pass — every
number is quoted from the three reports or from the ledger. Documents that still describe the
2026-10-28 answer were **not** edited: `Research/specs/{B-12,B-13,B-14,V-05,V-06,Q-2,Q-5}.md`,
`v05_predictions.py:67` ("excluded by decision: D-2 = one hybrid car, B-12 skipped"), and the
`bm_rc*.py` receipt field. They are the pre-reopen record; re-running them is B-12's work.

---

## 9. UNKNOWNs, each with its settler

| # | unknown | settler |
|---|---|---|
| U1 | can a vehicle entity be swapped at runtime for its variant? | `JustCause3.exe` entity/vehicle streaming consumer, or a live probe (test ban) |
| U2 | does any native code read `ExtendedExposedVariables` to change handling? | the exe's consumer for that module (2 expressions in the whole fleet, both speed-ramp) |
| U3 | which member caps speed to 21.6 km/h, if any? | B-12's read of the battle `.ee`'s `CustomLandGlobal`/`LandGlobal`/`vehicle_misc` set |
| U4 | is `heat_boost` reachable (push_force 0)? | the boost-state consumer; relevant only to the in-place Option B, not to two variants |
| U5 | is there any animation-node member on a JC3 car? | `VOCABULARY.md` has no anim module; exe-side animation system (T-MD13's transition) |
| U6 | what pose did BmAK ship (`TransformationRotation` 0x384 is not serialised)? | BmGame CDO decode (`chase08_cdo.py`) or the `BatmanAK.exe` store site |
| U7 | does a new `Usage` hash dispatch at all? | the `Usage` consumer in the exe, or a one-variable probe (T-MD14) |

---

## 10. Sources

* `tmp/freebuff/reports/mode-switch-carriers.md` — the runtime-switch census (§2), the five-row
  verdict (§3), the closest system (§4), the three options and the gap (§5), per-row consequence (§6),
  UNKNOWNs (§7).
* `tmp/freebuff/reports/battle-audio-switch-event.md` — 32 named `BML_Batmobile` events / 7
  `BML_Battlemode` events / 24 media, the 12-name usage vocabulary, `EngineNitro` 4197885156, the
  three build legs and what the missing flag costs.
* `tmp/freebuff/reports/keep-audit-world-modes.md` §3 — the two rows (T-MD10, T-MD11) that turn on
  the switch; both stay compromises.
* `GRAB_BACKLOG.md` §8 (cards B-01…B-21), §11 (D-2, D-7, D-11), §12 (tracker).
* `Working/Translation/T_ROWS.jsonl`, `Working/Translation/t11_variants.json`,
  `Working/Translation/T11_MODES.md` (the hybrid record).
* `Research/BatmobileGrab/MODES.md` (values) and `Research/JC3Grab/{VOCABULARY,FEATURE_CENSUS,
  ENTITIES,USAGES,TANKTURN}.md` (carriers), as cited inside the three reports.

---

## 11. Revert

1. **Backlog:** restore `GRAB_BACKLOG.md` from git (`git checkout -- GRAB_BACKLOG.md`) or re-edit the
   four places: §11 D-2, §8 B-12, §12 `B-12`/`T-15`/`T-BLOCKED`/`T-MD-D2-reopen`.
2. **Ledger:** `Backups/T_ROWS.jsonl.bak-pre8301` is the pre-change file (verified: only the seven
   `T-MD` rows differ, and the eight unrelated `why` fields I briefly clobbered were restored from
   it).
3. **Scripts:** `Tools/` is **untracked in git**, so the two edited scripts have no revert point;
   `Backups/{b12_variants,t_blocked}.py.8301-after` are *post*-change snapshots for comparison. To
   reverse: remove the five `WAITS` entries + T-MD14's rewritten wait + the `14/18/216` pin from
   `t_blocked.py`, and restore `b12_variants.py`'s skipped-by-D-2 assertions (its docstring quotes the
   contract it replaced).
4. **Regenerate** after any reversal: `t11_modes.py --write`, `t_blocked.py --write`,
   `status_audit.py --write`, `audit_compromises_t.py --write`, `t23_closeout.py --write`.
5. Nothing else exists to revert: no build tree, bank, dropzone or game file was written.
