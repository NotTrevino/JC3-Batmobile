# Apply the four v2 plans to the ledger — second serial pass

Card: apply-v2-driving-and-world-rows. 2026-11-08. The second serial pass over
`Working/Translation/T_ROWS.jsonl` (the weapon pass ran first). Inputs, read only:
`tmp/freebuff/reports/air-control-and-ram-assist-plans-v2.md`,
`boost-selector-and-moving-parts-plans-v2.md`, `controls-entry-exit-eject-plans-v2.md`,
`water-flip-damage-remote-plans-v2.md`.

**Provenance / reversibility.** Intended change: apply the corrected figures to the rows that already
carried them, add the operator-observed behaviours and the T-12 part / control cells that had no row,
and keep the pin (`Tools/scripts/t_blocked.py`) honest afterwards. Files edited: this page,
`Working/Translation/T3_COVERAGE.md`, `Working/Translation/T1_TRANSLATION.md`,
`Tools/scripts/t_rows.py`, `Tools/scripts/t_blocked.py`; regenerated: `Working/Translation/T_ROWS.jsonl`,
`Working/Translation/BLOCKED_PROPOSALS.{json,md}`, `STATUS.md`. Backups taken before editing:
`Tools/scripts/t_rows.py.bak-b14` and `Tools/scripts/t_blocked.py.bak-b14`. Revert = restore those two,
`git checkout -- Working/Translation/T3_COVERAGE.md Working/Translation/T1_TRANSLATION.md STATUS.md`
and re-run `t_rows.py build`, `t_blocked.py --write`, `status_audit.py --write`. No game was launched,
no archive, module, `.epe` or build was written, and no test was run (test ban unchanged).

---

## 1. Row counts, before and after

The ledger is generated (`t_rows.py build`) from the document tables, so a row is added by adding it
to `T3_COVERAGE.md`, never by editing the `.jsonl` by hand; `t_rows.py check` fails on either
direction of drift.

| metric | before | after | source of the number |
|---|---:|---:|---|
| ledger rows (`T_ROWS.jsonl`) | 199 | **225** | `t_rows.py check` header |
| in-scope rows (`status_audit.t_rows()`) | 221 | **244** | `t_blocked.py` header line |
| blocked rows (ledger + T6) | 11 + 4 = 15 | **18 + 4 = 22** | `t_rows.py` counts + `t_blocked.py` |
| queued (`next`) | 110 | **114** | `t_rows.py` counts |
| `epe` | 26 | **38** | `t_rows.py` counts |
| `out` in the ledger | 0 | **3** | `t_rows.py` counts (T6's 7 are unchanged) |
| resolved from evidence / in scope | 148 / 221 (67.0%) | **164 / 244 (67.2%)** | after: `STATUS.md` as written by `status_audit.py`; before: 164 − 16 new evidenced rows |

Sixteen of the 26 new rows are evidenced (`next` or `epe`); the other ten are 3 `out` and 7
`blocked`. The in-scope count moves by +23 (26 rows − 3 `out`), which is why the pin had to be
updated in §5.

## 2. Rows whose old value was replaced, and the audit line that justifies it

Each replacement is a correction of a number the ledger already carried, not a new claim.

| row | old value in the ledger | new value | audit line that justifies it |
|---|---|---|---|
| `T-AC1` | airborne window **1.212 s**; products **9696** / **14544**; normaliser inverse **6600.7** | **1.211 s** (1.251 / 1.183 / 1.199 s); **9691** = 8000 × 1.211333 and **14536** = 12000 × 1.211333; **6604.3** = 8000 / 1.211333 | `air-control-and-ram-assist-plans-v2.md` A4 (**MISMATCH** +0.000667 s, +0.055 %), A5 (third sample 1.200 → **1.199**, from the row's own PTS 149 / 5.006 s → 186 / 6.205 s), D3 (**−5.33**), D4 (**−8.0**), `alt` (**+3.6**); the stale 1.212 literal lives at `Research/BatmobileGrab/FOOTAGE.md:27, :93` and the plan took route (b), so the `T-AC1` cell in `T3_COVERAGE.md` now prints "1.211 (the mean of 1.251 / 1.183 / 1.199 s, not the 1.212 the footage file prints)" — the correction lives in the cell, not in the row's `why`, because `t10_reopen.py --check` owns the `why` of the T-10 rows. The −33.3 % ratio and both steering bands (0.53–0.80×, 1.23–1.85×) are invariant to it and were **not** touched |
| `T-RA1` | `KillFlip*` (**−2000000** over **1.5 s**), repeated in the disposition as the "2000× out of domain" example | `KillFlip*` (**−200** over **0.5 s** shipped; −2000000 / 1.5 s is the **class default**) | `air-control-and-ram-assist-plans-v2.md` §0 table ("`KillFlipTorque` **−2,000,000 → −200 shipped** (−2,000,000 is the class default)") and §0.1: the ram plan's "impossible / 57× short / 2000× out of domain" verdict is **void** — the value fits a real torque member and fails only on duration and target selection. `T-RA1` stays `blocked`: the missing capability is unchanged, only its example number was wrong |
| `T-B4` | **"grip 1.5 / extra 80 on both blocks"**, presented as the donor's numbers with no per-block split | donor decode per block: `nitro_boost` grip **2** / speed **40** (already shipped), `nitro_boost_upgraded` grip **1.5** / speed **80**, `heat_boost` grip **1.5** / speed **80**; the **battle rung** writes `heat_boost` grip **1.333** = 1 / `BattleModeLatSlipScale` 0.75 and `extra_top_speed` **0.0** | `boost-selector-and-moving-parts-plans-v2.md` §0, **A-C1**: the §2.4 table (1.0 / 4.26 / 4.26 and 43.2 / 100.92 / 100.92) and the T-MD14b donor (2 / 1.5 / 1.5 and 40 / 80 / 80) are **different `CustomLandGlobal` copies**, so "restore 1.5 / 80 on both blocks" was true of only two of the three blocks and silent about `nitro_boost`; §1.4 fixes the battle rung at grip 1.333 / speed 0.0 because battle caps speed (`TurningModeMaxSpeed` 600 cm/s = 21.6 km/h) and never adds it |

The two blocks whose values did **not** move: `T-B3` (nitro grip 5.68 → 1.0, identity) and `T-B1`
(6.3× thrust), which the v2 plan leaves as the keep-audit fixed them.

## 3. Rows added — 26, each with its disposition

All 26 live in `T3_COVERAGE.md` §1b ("Rows the four 2026-11-08 v2 plans add"), the table whose shape
(`BmAK source | JC3 target | transform | now | proposed | conf | verify`) fits both a behaviour and a
part cell; `T3_COVERAGE.md` is prose, so no generator's own `--check` is bypassed.

**Operator-observed behaviours missing from the ledger** (`water-flip-damage-remote-plans-v2.md`):

| row | behaviour | dispo | note |
|---|---|---|---|
| `T-WT1` | water entry teleports the car to land, engine keeps running | `next` | `will_sink` 1 → 0 + nearest-land ring; the ring thresholds are **chosen**, the destination rule is UNKNOWN |
| `T-FR1` | a stuck or flipped car rights itself with its thrusters after a rest | `next` | gate + timer pair decoded (`StuckTimeMax` 2.0 / `StuckTimeFlip` 0.5); 230,300 N·m for 0.5 s is **derived** |
| `T-DE1` | health to zero from weapons → explodes, kills the occupants; crashes never damage it | `next` | pulse + tune decoded; **do not** wire a destroyed-mesh `mshswap` |
| `T-RC1` | remote control (Batman stationary, car empty) | **`blocked`** | **halted by ruling**, §1.4 of the plan — reason in the cell, see §4 |
| `T-RC2` | static overlay from ~100 m, hard stop at 150 m | **`blocked`** | **halted by ruling** — no distance read and no overlay element |
| `T-RC3` | LB makes the car drive itself to the player | `next` | probe-gated; **LB is exit** (`T-CT1`), so the trigger must be a free key |

**The T-12 part rows** (`P-01`…`P-15`, carried with their audit corrections C6–C11):
`T-PT1`…`T-PT15`, ids mapped one-to-one so the T-12 numbering stays legible. Corrections applied:
`P-03` states **peak 1229.51 °/s and mean 553.8 °/s** (C6 — 2160 / 3.90 cannot also be 1229.51),
`P-12` is **105.82 °/s**, not P-11's 106.14 (C7), `P-14`/`P-15` say **"no behaviour of its own"**, not
"static" (C8), `P-01` carries hinge `constraint_index` **11** with the **−60…60°** limits, `P-04` is
stated as the one `axis_agrees: false` row (two lines, one row — a decision, not a value), `P-06`'
72.481 cm translation is a **named omission** (JC3 door parts rotate only), `P-05`'s `batmobile_jet`
is in no name table and no export (the driver is code). Dispositions: **`epe` ×12** (a part/behaviour
in the entity graph), **`out` ×3** — `T-PT2` (`joint: null`, declared static), `T-PT5` (no bone, no
binding), `T-PT13` (no part, no joint). Those three are `out` because the plan *declares* them
unbuildable, not because a behaviour was halted.

**The control-scheme cells** (`controls-entry-exit-eject-plans-v2.md`): `T-CT1` (enter = Y, exit =
LB), `T-CT2` (eject = double press A + glide), `T-CT3` (winch = D-pad Right), `T-CT4` (`aTurn` =
`RightX`, `aStrafe` = `LeftX`; curve UNKNOWN), `T-CT5` (the keymap writer). All five are **`blocked`**,
because §4 of that plan says every keymap row ends in the same missing build step and "a row that says
'rebind' is a plan, not a build". Corrections carried: **C1** (no X token count exists — the 8-token
button is `LSHOULDER` alone and export X carries 3), **C2** (five buttons collide, not one), **C3**
(the two steering axes stated separately instead of blended), **C9** (145/104 are the **patch**
counts, base 131/94).

## 4. Halts recorded as notes, never as a disposition of `out`

`water-flip-damage-remote-plans-v2.md` §4.4 halts three things and gives a written reason. The ledger
records the reason in the row's `proposed` cell and keeps the disposition `blocked`:

* `T-RC1` — **remote control** has no input carrier to rebind (no aim/stick/cursor action on a land
  vehicle, no 2D vehicle stick, the gadget route is a proximity interaction with 0 range members), the
  overlay that makes it read as remote has no HUD element, and the car's arrival is **already a Rebel
  Drop item in this build** (`profile/item.onlinec` `Name` = the Jenkins hash of the entity leaf,
  `bm_rc4.py:69-72` ships the file, `RebelDropTimer` 0) — a second arrival path for the same entity
  buys nothing.
* `T-RC2` — the **static overlay** and the **150 m** stop: BmAK's 100 m is a gadget float
  (`JammingRange` 10000 cm), not a world range; no HUD element is a static/noise/jam overlay and no
  member carries a distance-to-player read.
* `T-RC3` — **homing** is *held at the probe gate*, not halted: it stays `next` because
  `car_drive_to_point.btc` (80,366 B) ships; what is unproven is a per-entity binding and a target
  point, and the note says the trigger may not be LB.

## 5. Pin upkeep

Edits changed both the blocked set and the in-scope count, so the pin was re-derived, not guessed.

| pin | before | after |
|---|---|---|
| `Tools/scripts/t_blocked.py` `WAITS` | 15 ids | **22 ids** — added `T-RC1`, `T-RC2`, `T-CT1`…`T-CT5`, each with the one input it waits for |
| `build()["counts"]["reconciles"]` | `len(lb) == 11`, `t6 == 4`, `blocked == 15`, `in_scope == 221` | `len(lb) == 18`, `t6 == 4`, `blocked == 22`, `in_scope == 244` |
| tool docstring | "15 blocked of 216", "carries 11" | rewritten to the two-file derivation (18 ledger + 4 T6 = 22) and to why the seven joined |

`t_blocked.py` was backed up to `t_blocked.py.bak-b14` first (and `t_rows.py` to `.bak-b14`). It was
run `--write` then `--check`; `--check` also re-ran every evidence marker in `RESOLVED` and compared
the ledger sha256, so the sheet is not stale.

## 6. Checks run

| check | result |
|---|---|
| `python Tools/scripts/t_rows.py build` | `225 rows, 35 edits over 16 rows` |
| `python Tools/scripts/t_rows.py check` | `ledger 225 rows \| edit 16 next 114 keep 29 epe 38 re-read 0 blocked 18 out 3 superseded 7 \| edits 35 over 16 rows` → `check ok` |
| `python Tools/scripts/t_blocked.py --write` | `22 blocked rows (18 ledger + 4 T6) of 244 in scope; 0 tested, 7 resolved` |
| `python Tools/scripts/t_blocked.py --check` | `PASS: 22 blocked rows re-derived (18 ledger + 4 T6) of 244 in scope; 0 attempts, all evidence markers present; ledger sha256 unchanged` |
| `python Tools/scripts/status_audit.py --write` then `--check` | `STATUS.md is current` — `164 / 244` resolved (67.2 %), `22 / 244` blocked, `114` queued, `T-3` now 43 rows with 3 `out` |
| `python Tools/scripts/bmak_coverage.py --check` | `check ok` — the 423 G1 fields are still all assigned, 0 unassigned in the animation/audio/lights/weapons censuses (adding rows to `T3_COVERAGE.md` did not disturb the coverage map) |
| `t10_reopen.py`, `t7_weapons.py`, `t11_modes.py`, `t12_parts.py` | `t10_reopen.py --check` **initially failed** (my two `why` edits), so the `why` strings were restored to the T-10 table's text and the correction kept in the T-3 cells — it now exits 0; the other three were not run, because none of their documents was edited |

## 7. UNKNOWNs this pass did not settle (each with its settler)

| # | UNKNOWN | where it is now recorded | settles with |
|---:|---|---|---|
| 1 | the reset action's own destination rule and who consumes `CHALLENGE_RESET_VEHICLE` | `T-WT1` | a vanilla `P` press on a flipped car, or the graph binding the action |
| 2 | `sinking_progress` / `is_safe_to_teleport` type and range | `T-WT1` | the executable's variable table (`EMP_DISABLE.json` holds names + addresses) |
| 3 | the unit of `BatmobileStuckTimeMax` 2.0 / `Flip` 0.5 | `T-FR1` | a live read of the accumulator's rate |
| 4 | whether a `CCar` accepts `DriverLean` (`righting_torque` 3000) | `T-FR1` | one build + the module loader |
| 5 | whether the Batmobile's `.ee` still carries `CForcePulse` + `car_explosion_medium` | `T-DE1` | `jc3forcepulse.py` dump |
| 6 | the player's health (is the blast's 500 lethal to the occupant) | `T-DE1` | the player `CPawn` module — not decoded here |
| 7 | `explosion_threshold` / `smoke_threshold` / `burn_threshold` semantics | `T-DE1` | `DAMAGE_MODEL.md` step 7 and the probes |
| 8 | whether a mod can bind `car_drive_to_point.btc` to one vehicle, with a target point | `T-RC3` | the `.btc` body + the `…_land_global_ai.vmodc` fields |
| 9 | BmAK's remote boundary value | `T-RC1`/`T-RC2` (halted) | the native body / a runtime sample |
| 10 | the double-press timer that turns A into Eject Into Glide | `T-CT2` | no hold/duration/tap field exists in 145+104+249 rows; native input code |
| 11 | BmAK's in-car steering response curve | `T-CT4` | the capture set (`StandardSteeringSpeedCurve`, `DesiredTurnOnSpotSpeed`) |
| 12 | which bone the `P-09` 25.817° headline belongs to | `T-PT9` | `RESET_FINDINGS`-style bone re-read of the flap parts |

Nothing above is filled in with a plausible-sounding JC3 implementation: each row states the negative
(the member does not exist) or the chosen number, labelled as chosen.

## How this page is checked

Every count in §1 and §5 is a line of tool output, quoted verbatim in §6. Every replaced value in §2
names the audit row (`A4`, `A5`, `D3`, `D4`, `alt`, `§0`, `A-C1`, `C1`, `C2`, `C3`, `C6`, `C7`, `C8`,
`C9`) that produced it. `python Tools/scripts/t_rows.py check` and
`python Tools/scripts/status_audit.py --check` both pass on the state written by this pass, and
`t_blocked.py --check` passes on the updated pin.
