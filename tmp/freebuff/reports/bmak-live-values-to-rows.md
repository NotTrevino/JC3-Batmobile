# BmAK live values → translation rows — the proposal (no ledger edit)

STATUS: **done, report only.** `Working/Translation/T_ROWS.jsonl` was **not edited** (the 903x apply chain owns
it). No value is quoted as live, because **the reader read nothing**: `reports/bmak-gog-live-batmobile-reader.md`
§5 says *"All six: UNKNOWN. No process was attached in this session; `BatmanAK.exe` is not running."* So for every
value below the proposed new value is **UNKNOWN**, with
(a) the exact reader field that will print it, (b) the row that will carry it, and (c) the hook module that will
consume it. The moment the reader runs, the slot becomes `read (live)` — nothing else in the row changes.

## 1. How each value is obtained (decoded, from the reader report §2)

| # | value | member the reader reads (offset from `BMSDK_OFFSETS.json`) | class of the read |
|---|---|---|---|
| V1 | LT battle-mode hold time | `RVehicleBatmobileBase.PreventModeSwitchDuration` +6544 f32, `LastBattleModeControlledTime` +7852, `bBattleModeControlled` word | `read (live)` scalar, once running |
| V2 | eject charge window | `MaxEjectType` +5902 byte (`EBatmobileEjectType`), `EjectUpDist` +6032 f32; carriers `EjectUpMove` +8416 / `EjectToSpotMove` +8496 / `EjectForwardMove` +8424 | `read (live)` byte/float; **no duration member exists in either JSON** — the window is inside `RSpecialMoveConfig`, which neither JSON decodes |
| V3 | steering curve at speed | `StandardSteeringSpeedCurve` +576, `BoostSteeringSpeedCurve` +556, `HandbrakeSteeringSpeedCurve` +596 (`FInterpCurveFloat`); `SteerSpeedVsSpeedCurve` +404, `SteeringReductionFactor` +324, `SteeringReductionSpeed` +340; `BattleModeSteerAngleFactor` +768 | `read (live)` curve points; the 20-byte stride is **derived** and validated at read time |
| V4 | `HealthRecoverRate` | `RVehicleBatmobileBase.HealthRecoverRate` +8220, `ArrayProperty<float>` | `read (live)` array |
| V5 | summon / homing | `RemoteCallIn` +4572 word, `RemoteSafePointLocation` +6512 / `Rotation` +6524, `RBatmobileMissile.HomingDelay` +1060, `bHoming` +1056 | `read (live)` word/vector/float |
| V6 | physics asset in use | `BatmobileViewMesh` +5716 → scan the component's first `0x600` bytes for a pointer landing on a live `PhysicsAsset` (class name from GNames) | `read (live)` object name — the **only** member here whose value is an asset identity, not a scalar |

Two of the six have **no owner row today**: the eject charge window (the reader's own `--check` prints
`ledger GAPs … ['V2 …']`) and the LT hold duration (the reader's keyword join lands on `T-BM1`, which is
**superseded** and names no duration).

## 2. The proposal, value by value

### V1 — LT battle-mode hold time

| field | value |
|---|---|
| row | **new `T-CT6`** (the control rows are `T-CT1`…`T-CT5`; none owns a hold duration) |
| current value and provenance | no row carries it. Nearest: `T-BM1` (`superseded_by` T-12/T-15, provenance `decoded`) lists `BattleMode*` but **no hold time**; `T-MD5` holds `BattleModeVSpeedCurve` only; a ledger-wide search for `Hold`/`hold` hits `T-R1`, `T-R2`, `T-ST5`, `T-ST6`, `T-E2`, `T-MA2`, `T-AU2`, `T-FX2` — none of them a mode hold |
| proposed new value | **UNKNOWN** now; becomes `V1 PreventModeSwitchDuration` (seconds, raw f32, no unit bridge) as `read (live)` |
| how it settles | the reader's `--selftest` then a live run; if the value does not track a stopwatch on a held LT, the duration is code-side (reader §8.2) and the row keeps its UNKNOWN with that reason |
| carrier | **7983 gamepad** — it is the only module that sees the LT hold edge and can gate the transform on the duration; `T-CT1` (enter/exit keymap) is data and cannot hold a timing |
| row shape | `requirement`: "hold LT for `N` s to commit the transform"; `new value` = UNKNOWN → `read (live)` `PreventModeSwitchDuration` = ? ; `carrier` = 7983; `dispo` = `blocked` until the run, then `next` |

### V2 — eject charge window

| field | value |
|---|---|
| row | **new `T-CT7`** (the reader's ledger GAP; `T-CT2` owns the *input*, not the window) |
| current value and provenance | `T-CT2` is `blocked`: *"eject = double press of A … no hold/duration/tap field exists in 145+104+249 binding rows (U2), and 0 of 4,832 exits carries a launch member"* — provenance `decoded (keymap, exit census) + UNKNOWN (the tap timer)`. That wording is **stale against the operator fact** in §3 below |
| proposed new value | **UNKNOWN**; becomes `read (live)` `MaxEjectType` (enum byte) + `EjectUpDist` (cm, f32) and, if the stride validates, the `RSpecialMoveConfig` block behind `EjectUpMove`/`EjectToSpotMove`/`EjectForwardMove` for the window |
| how it settles | the live read of the four carriers; if `RSpecialMoveConfig`'s own properties have no duration, the window stays UNKNOWN with *that* reason (reader §8.3), not with "no field exists" |
| carrier | **7983 gamepad** — the charge is measured on the A hold; the keymap only carries the binding (`T-CT2`'s point), so the window cannot live there |
| row shape | `requirement`: "hold A `N` s to reach the charged eject; tap = higher, double-tap = lowest"; `value` = UNKNOWN → `read (live)`; `carrier` = 7983; `dispo` = `blocked`, then `next` |

### V3 — steering curve at speed

| field | value |
|---|---|
| row | **`T-ST7`** (owner of the rate and the knots) + **`T-CT4`** (the blocked input row that waits on the curve) |
| current value and provenance | `T-ST7`, `next`, provenance `derived`: *"`SteerSpeed` 220 °/s, `SpinSteeringFactor` 100000, steer-curve knots `InVal/OutVal/ArriveTangent/LeaveTangent`"*; the write is 0.25 s low / 0.091 s high (55°/220 and 20°/220), with 0.091 s declared out-of-domain below the 0.2 s fleet minimum. `T-CT4`, `blocked`: *"BmAK's in-car curve is UNKNOWN (`StandardSteeringSpeedCurve` / `DesiredTurnOnSpotSpeed` are the read sites, no values decoded) … the response curve needs the capture set (U6)"* |
| proposed new value | **UNKNOWN** now; `read (live)` `StandardSteeringSpeedCurve` (+576) / `BoostSteeringSpeedCurve` (+556) / `HandbrakeSteeringSpeedCurve` (+596) point lists, plus `SteerSpeedVsSpeedCurve` (+404), `SteeringReductionFactor` (+324), `SteeringReductionSpeed` (+340) and `BattleModeSteerAngleFactor` (+768). The 220 °/s scalar stays `derived` until a live damping value confirms it |
| how it settles | one live read of a **moving** car (reader §4 step 2: a still car never writes the curve). `T-CT4`'s "capture set (U6)" is **superseded for the curve** by this read — the capture set was the only way to get the shape without a reader |
| carrier | **7987 handling** — the curve is a handling member; `T-CT4`'s axes (`aTurn` = `RightX`, `aStrafe` = `LeftX`, both decoded) are the input pair 7987 reads |
| row shape | `T-ST7`: add a third value cell `read (live)` for the curve knots; `T-CT4`: replace the "needs the capture set (U6)" blocker with "the live curve read", `dispo` stays `blocked`, then `next` |

### V4 — `HealthRecoverRate`

| field | value |
|---|---|
| row | **new `T-DM10`** (damage rows stop at `T-DM9`; no row in 244 names a regen rate — a search for `regen` returns none) |
| current value and provenance | none. `T-DM1`, `next`, `class`: *"`RVehicleBatmobile.Health` = 1,200 (3 archetypes)"* against build `max_health` 2,000 → 36,000 (T-14 option B); `T-DM9`, `blocked`, owns `invulnerable`. Regeneration is carried only outside the ledger: `Working/Roadmap/damage_world.md` ARM-5 / **NEW-ARM-01** (blocked), with `RB-9` named as the carrier |
| proposed new value | **UNKNOWN**; `read (live)` `HealthRecoverRate` (+8220) as a float array — the array shape (`[rate, delay]?`) is **not** decoded, so the reader prints up to 128 floats and the row records the count it got rather than assuming two |
| how it settles | the live read; the rate's *unit* (hp/s vs fraction/s) stays UNKNOWN until it is compared with a measured regen over a known interval |
| carrier | **7986 regen/flip** — the same module that owns the flip timer owns the regen gate; the entity `invulnerable` flag (`T-DM9`) is a different mechanism and cannot express a rate |
| row shape | `requirement`: "health returns out of combat at rate R after delay D; full on re-summon"; `value` = UNKNOWN → `read (live)`; `carrier` = 7986; `dispo` = `next` (the mechanism is lore, the value is the only gap) |

### V5 — summon / homing numbers

| field | value |
|---|---|
| rows | **`T-RC1`** (remote/summon, `blocked`), **`T-RC2`** (summon, `blocked`), **`T-RC3`** (homing, `next`); `T-WP9` (`next`) keeps the tracker missile tune |
| current value and provenance | `T-RC1`/`T-RC2`/`T-RC3` were written by the 2026-11-08 v2 pass from `water-flip-damage-remote-plans-v2.md`, which **halts remote control and the overlay outright** and **holds homing at the probe gate** (LB is exit; the drop is the summon). `T-WP9`, `decoded`, carries the tracker's `LaunchSocketName` `BattleModeSpotLight` and its projectile |
| proposed new value | **UNKNOWN**; `read (live)` `RemoteCallIn` (+4572 word — a flag/limit, not a distance), `RemoteSafePointLocation`/`Rotation` (+6512/+6524), `RBatmobileMissile.HomingDelay` (+1060) and `bHoming` (+1056) |
| how it settles | one live read; note what it **cannot** give: the reader has no member for the remote **boundary distance** (the plan's U14 `GetDistanceToRemoteControlBoundary` is a native body), so that stays UNKNOWN after the read |
| carrier | **no hook module** — these are data rows. The summon route is the shipped Rebel Drop item (`T-RC1`), and the homing half is `car_drive_to_point.btc` per the plan; 7986 does not touch them |
| row shape | `T-RC1`: new cell "live: `RemoteCallIn` = ? / safe point = ?"; `T-RC3`: new cell "live: `HomingDelay` = ?, `bHoming` = ?"; both keep their existing disposition until the read |

### V6 — the physics asset in use

| field | value |
|---|---|
| row | **`T-P3`** (`next`) and **`T-CO1`** (`next`) — the same asset named from two documents |
| current value and provenance | `T-P3`, `decoded (asset, 2026-11-07)`: *"the drivable rigid body is `Physics.Batmobile_V3_Physics` (BmGame.upk export 158266: 2 bodies, 3 boxes, 1 constraint, reached from `Batmobile.SVehicleMesh` property offset 824)"*; the built tree still carries 62 donor bodies with one hull rewritten. `T-CO1` restates the 2 bodies / 3 boxes / 1 constraint and the box dimensions |
| proposed new value | **not a new number** — the identity is already decoded; the live read (`V6`) becomes **`read (live)` confirmation** of the string the running car binds, which is what turns "the package says so" into "the running game uses so" |
| how it settles | the reader's class-name scan; if it finds nothing, it says so (reader §8.5) and the row keeps the decoded identity with that note |
| carrier | **no hook module**: the consumer is the `.physicsc` writer in brief **9141** (three boxes within 5 cm). The read names the object; the build writes the hulls |
| row shape | add one cell to `T-P3`/`T-CO1`: `read (live)` = the `PhysicsAsset` object name found on `BatmobileViewMesh`, expected `Physics.Batmobile_V3_Physics`; a mismatch is a finding, not a silent overwrite |

## 3. Contradictions with the operator facts of `ROADMAP.md` §7 — both kept

| value | operator fact (§7, 2026-11-08) | what the ledger/reader says | how the report keeps both |
|---|---|---|---|
| **V1** LT hold | "Transform: **turret rises + wheels/body reconfigure, ~2 s**; swap causes a **near-instant slowdown**" | the reader's only candidate is `PreventModeSwitchDuration` (no decode of its value, no unit); `T-BM1`/`T-MD*` carry no duration at all | the row records **both**: the operator's ~2 s (fact, undated measurement) and the live `PreventModeSwitchDuration` (once read). If they differ, the transform's *animation* duration and the *input hold* are two different quantities and the row says so; neither is deleted |
| **V2** eject window | "Eject: **hold A to charge, tap A to eject higher; a plain double-tap gives the lowest**" | `T-CT2` (`blocked`) says *"eject = double press of A … no hold/duration/tap field exists"* | the fact **overturns the requirement wording**, not the census: `T-CT2`'s "no field in the keymap" stays true, and the three-level mechanic is runtime logic. `T-CT2`'s `requirement` cell is rewritten by the apply chain; the decoded census sentence is kept as evidence |
| **V3** steering curve | no §7 fact | `T-ST7` is 220 °/s `derived`; `T-CT4` is `blocked` on a capture set | no contradiction; the live read **replaces the capture set**, and the 220 °/s stays `derived` until confirmed. If the live curve and the 0.25 s/0.091 s write disagree, both are recorded and 0.091 s's out-of-domain note stays |
| **V4** regen | "Regen: **out of combat over time; full on re-summon / after death**" | no ledger row; `NEW-ARM-01` blocked for the value | consistent — the fact fixes the *mechanism* as required lore, the read fills the *rate*; neither replaces the other |
| **V5** summon/homing | §7 does not cover summon; the v2 plan **halts** remote/homing | `T-RC1`/`T-RC2` `blocked`, `T-RC3` `next`; the reader has `HomingDelay`/`bHoming` members | the halt is a **plan decision**, not a fact: if the live read shows `bHoming` set on a shipped missile, the halt's premise ("no member") is narrowed to "no *caller*", and both readings are kept with the plan's written reason quoted |
| **V6** physics asset | §7 does not cover it | decoded identity already in `T-P3`/`T-CO1` | no conflict; the read only confirms |

## 4. Summary table — what the apply chain should change, and when

| value | row | change | blocked on |
|---|---|---|---|
| V1 LT hold | new **T-CT6** | add the row; value UNKNOWN → `read (live)` `PreventModeSwitchDuration` | a live session (reader `--selftest` + run) |
| V2 eject window | new **T-CT7** | add the row (reader's GAP); value UNKNOWN → `read (live)` `MaxEjectType`/`EjectUpDist`/carriers | a live session; `RSpecialMoveConfig` properties not in either JSON |
| V2 wording | `T-CT2` | rewrite the `requirement` cell to the three-level eject (already queued in brief 9170) | the 903x apply chain |
| V3 curve | `T-ST7`, `T-CT4` | add a `read (live)` cell; drop "capture set (U6)" from `T-CT4`'s blocker | a live session with the car moving |
| V4 regen | new **T-DM10** | add the row; value UNKNOWN → `read (live)` `HealthRecoverRate` | a live session |
| V5 summon/homing | `T-RC1`, `T-RC3` | add a `read (live)` cell to each; boundary distance stays UNKNOWN | a live session; the native boundary body |
| V6 asset | `T-P3`, `T-CO1` | add a `read (live)` confirmation cell | a live session |

Hook modules that will carry the values: **7983 gamepad** (V1 hold, V2 charge — input timing),
**7986 regen/flip** (V4 rate), **7987 handling** (V3 curve). V5 is data (Rebel Drop + `car_drive_to_point.btc`),
V6 is data (the `.physicsc` writer in 9141). None of the six needs a new hook module.

## 5. What I checked, and what I did not

Read: `tmp/freebuff/reports/bmak-gog-live-batmobile-reader.md` in full; `ROADMAP.md` §7; the queue briefs
list (`7981`…`7987` exist as briefs; 7983 gamepad scoping, 7986 world logic water/flip/regen, 7987 runtime
handling switch); every ledger row named above, by id, from `Working/Translation/T_ROWS.jsonl` (244 rows, read
with `json.loads` per line, no edit). Row inventory used to place the new ids: `T-CT` = 1…5,
`T-DM` = 1…9, `T-MD` = 1…15, `T-WLD` = 1…19, no `T-SU*`; `T-RC1`…`T-RC3` are the remote/summon/homing rows.

I did **not** run `Tools/scripts/bmak_live_read.py` and did not start `BatmanAK.exe`: the brief is a ledger
proposal, the test ban stands, and the reader's own report records `RUN_EXIT=3` with `--check: 0 problem(s),
1 ledger gap(s)`.

## 6. UNKNOWNs

| # | UNKNOWN | what was tried | what settles it |
|---|---|---|---|
| 1 | all six live values | nothing — no process; the reader report is the only source and it prints UNKNOWN | `bmak_live_read.py --selftest` then a run with the car moving (reader §4) |
| 2 | the unit of `PreventModeSwitchDuration` | the reader decodes it as f32 with no unit; no doc strings in `BMSDK_OFFSETS.json` | a stopwatch against a held LT, or the function body |
| 3 | the eject window's location | `RSpecialMoveConfig` properties are in neither JSON | a dump of that class (BmSDK class dump, if a build is ever available) |
| 4 | the `FInterpCurveFloat` point stride (20 B) | derived, validated only at read time | the reader's own validation output |
| 5 | `HealthRecoverRate`'s array shape and unit | decoded as `ArrayProperty<float>`; count unknown | the live read |
| 6 | the remote boundary distance | no member in either JSON | the native `GetDistanceToRemoteControlBoundary` body |
| 7 | whether `bHoming` is set on the shipped missile | not decoded | the live read (V5) |

## 7. Revert

Nothing to revert: this report wrote no ledger row, no brief, no script and no build. Delete the file to undo it.
