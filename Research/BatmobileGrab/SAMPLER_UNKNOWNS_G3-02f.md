# SAMPLER_UNKNOWNS - the three G3-02f action UNKNOWNs, tested against the existing sampler logs

**Card:** SAMPLER-offline (follow-on to **G3-02f**). **Status:** 3 of 3 UNKNOWN, for two measured
reasons: the seven logs never carry a press of X, Y or A, and only 4 of G3-02f's 44 observables are
among the fields the sampler ever read; and the rate test the brief specifies has no discriminating
power on this corpus - run on a binding that is known (LT -> battle mode) it promotes nothing and does
not beat its own baseline. Both facts are measured below, with counts.

**Inputs (read-only, nothing else):** `Research/BatmobileGrab/runtime/samples-*.jsonl`, `Research/BatmobileGrab/SAMPLER_FIELDS2.md`, and - only to name the log keys - `Tools/scripts/bmak_runtime_sampler.py`. No game was run, attached to or read.

## 0. The three UNKNOWNs, restated

`SAMPLER_FIELDS2.md` §6 lists four UNKNOWNs; three are *actions*, and they are the ones this card tests.
The fourth (`TArray` element stride for `CurrentTargets`/`FiredProjectiles`) is not an action and is out
of scope here.

| # | UNKNOWN (G3-02f §6) | the corresponding action | what the logs would need |
|---|---|---|---|
| 1 | X (missile barrage) input byte | an X press | a sampled X byte - none exists in the layout, none in the log |
| 2 | A (eject) input byte | an A press / an eject | a sampled A byte or eject field - neither is in the log |
| 3 | boost duration / boost time field | a boost (Y) engagement | a sampled boost flag/timer - none is in the log |

## 1. Corpus - what the logs are (decoded: file, sha256, records)

| log | bytes | records | sha256 (first 16) |
|---|---:|---:|---|
| `samples-20261103T084831Z.jsonl` | 2,023 | 17 | `5038d38a73d0bba8` |
| `samples-20261103T085330Z.jsonl` | 2,795 | 17 | `264e1e9b508d64de` |
| `samples-20261103T085631Z.jsonl` | 4,067 | 26 | `76503811614a58a9` |
| `samples-20261103T113755Z.jsonl` | 1,666 | 1 | `2b59bc61aff56caf` |
| `samples-20261103T114350Z.jsonl` | 3,443 | 18 | `0e592e1bfa7735b5` |
| `samples-20261103T115320Z.jsonl` | 32,646 | 314 | `7349ca9845bcf694` |
| `samples-20261103T120003Z.jsonl` | 77,597 | 729 | `765110a3f2c1cc2b` |
| **total** | **124,237** | **1122** | |

- span: `2026-11-03T08:48:31.767000+00:00` to `2026-11-04T02:05:16.159000+00:00` (UTC, from the log's own `t`)
- sampling intervals <= 5 s: **399.1 s**; intervals > 5 s: **73** (max 46,273.1 s) - session pauses, excluded from every rate below
- records carrying a `null`: **38** (teardown/GC; a null is never counted as a change)
- distinct sampled fields: **63**

## 2. Press census - and the exact X and Y counts

A press is a rising edge (`0 -> >0`) of a sampled input byte. The sampler reads exactly five input
fields; the offsets are decoded at the line `--check` re-reads:

| # | input | log key | offset | .py line | presses | measurable brackets | analog (<0.9) | first | last | action (source) |
|---|---|---|---:|---:|---:|---:|---:|---|---|---|
| 1 | LT | `in0.aLeftTrigger` | 724 | `bmak_runtime_sampler.py:60` | 175 | 175 | 2 | 08:49:17.715 | 01:08:03.880 | hold battle / release pursuit (D-11 CONFIRMED live) |
| 2 | B | `in0.bCancelButton` | 774 | `bmak_runtime_sampler.py:61` | 62 | 62 | 0 | 08:51:08.304 | 01:08:04.913 | immobilizer on an auto-tagged enemy (D-11 CONFIRMED live) |
| 3 | LB | `in0.aLeftShoulder` | 760 | `bmak_runtime_sampler.py:60` | 4 | 4 | 0 | 11:48:22.562 | 01:05:33.287 | exit AND enter (D-11 CONFIRMED live) |
| 4 | RT | `in0.aRightTrigger` | 720 | `bmak_runtime_sampler.py:60` | 70 | 70 | 2 | 08:54:31.488 | 01:08:46.896 | throttle (driving, BmAK scheme) |
| 5 | THR | `in0.aThrottleAxis` | 840 | `bmak_runtime_sampler.py:61` | 73 | 73 | 1 | 08:54:31.488 | 01:08:46.896 | throttle axis (moves with RT) (driving, BmAK scheme) |

**The answer to the brief's question, stated exactly:** the logs contain **0 presses of X** and
**0 presses of Y**. Not "few": zero - neither button was ever sampled: `bVehicleBoostButton`
(+781) and the X byte are absent from the sampler's `PI` table (five entries, above), and for X there is
also no decoded byte to sample at all (G3-02f UNKNOWN 1). The sections below can therefore only test
X/Y hypotheses against *other* presses, which is exactly what §5-§7 show cannot work. A (eject) is also
unpressed: **0 presses of A**. The eject-adjacent action the logs do carry is LB (D-11: exit AND enter),
**4 presses**, analysed in §6.

## 3. Which of the 44 observables the logs actually contain (decoded: class + offset match)

Each of the 44 rows of `SAMPLER_FIELDS2.md` §1-§4 was matched to a sampled field by **class and offset**,
never by name similarity. **4 of 44** are present:

| observable | offset | sampled as | records where the sampled field changed |
|---|---:|---|---|
| `RPlayerInput.aThrottleAxis` | 840 | `in0.aThrottleAxis` | 153 |
| `RVehicleWeapon.bFiring` | 2084 | `RBatmobileEMPMissile0.bFiring`, `RBatmobileEMPMissile1.bFiring`, `RBatmobileEMPMissile2.bFiring` ... | 26 |
| `RVehicleBatmobileBase.bBoostLocked` | 4568 | `veh0.bits11D8`, `veh0.flags_11D8`, `veh1.bits11D8` ... | 451 |
| `RVehicleBatmobileBase.InfiniteBoost` | 4568 | `veh0.bits11D8`, `veh0.flags_11D8`, `veh1.bits11D8` ... | 451 |

The other **40** are not in any log - including every missile-launcher field, every eject field
(`MaxEjectType`, `EjectUpDist`, `OverrideNextEject`, `CurrentEjectType`, `LastEjectFromBatmobileTime`,
`UsedQuickGadget`) and the boost objects (`RBatmobileBooster.bBoosting`/`bWarming`, `BoostingOut`,
`AfterburnerSystem`, `LastBoostPickupTime`). That absence alone decides UNKNOWN 1 and 3; §5-§7 say what
*can* still be measured.

`RVehicleBatmobileBase.bBoostLocked` (bit 0x4000) and `InfiniteBoost` (bit 0x20000000) are the two
exceptions: the sampler reads their whole word as `vehN.flags_11D8` (offset 0x11D8 = 4568, the layout's
own offset). Across every record:

| bit | field | records where set | records read |
|---|---|---:|---:|
| 0x00004000 | `bBoostLocked` | 0 | 284 |
| 0x20000000 | `InfiniteBoost` | 1 | 284 |

`bBoostLocked` never sets, `InfiniteBoost` sets only in the teardown garbage records, so neither bit is a
usable signal; and neither is a *duration* in any case (G3-02f: no boost timer field exists).

## 4. Method, stated so it can be rejected

* **press** = rising edge of a sampled input byte (table §2).
* **bracket** ("within one sampling interval of the press") = `[t_edge, next sample]` plus
  `[previous sample, t_edge]` when that side is a normal sampling interval (<= 5 s). Rationale:
  the press onset is only localised to the interval that ended at the edge sample, so one interval either
  side is the narrowest window that certainly contains the onset and its first consequence. A bracket
  whose next sample is > 5 s away contributes no seconds and is reported as unmeasurable.
* **away** = every sampling interval (<= 5 s) that **no bracket of any sampled input** touches,
  so the baseline is press-free; long pauses are excluded from both sides, which can only *lower* the
  baseline rate and therefore cannot manufacture a candidate.
* **rate** = changes per second; a change is a record inside the window where that field's new value is
  non-null (the log is a diff stream, so a field that changes twice between two samples shows once).
* **margin (candidate rule):** changed inside >= 3 distinct brackets **and**
  `rate_in >= 3 x rate_out` **and** `rate_in - rate_out >= 0.5 s^-1`. Otherwise UNKNOWN.
  A candidate is a field that *tracks the action*; it is never the action's input byte unless it is an
  input byte, which for X and A does not exist in any log.

## 5. UNKNOWN 1 - X (missile barrage) input byte

**Sampled fields that change when X occurs: none are identifiable, because X never occurs in the logs.**
Presses of X: **0** (§2). No sampled input byte is X, and no missile-launcher field is sampled (§3), so
there is no window to measure and no field whose in-press rate can be compared with its baseline. Under
the stated rule the answer is UNKNOWN - not "no field correlates", but "no X press exists to correlate
against". Nothing in this corpus can distinguish X from the presses that are there (LT/B/LB/RT), and a
field that tracks those presses is evidence for *them*, not for X.

| candidate tested | presses available | in-bracket changes | away changes | rate_in | rate_out | verdict |
|---|---:|---:|---:|---:|---:|---|
| (none: no X-named or barrage-named field in the log, and no X press) | 0 | - | - | - | - | UNKNOWN |

## 6. UNKNOWN 2 - A (eject) input byte

Presses of A: **0**. The eject-adjacent event the logs *do* carry is **LB**, which D-11 records as
exit AND enter, confirmed live; in these logs LB brackets coincide with the vehicle losing its driver and
opening the cockpit (below). That is the closest known-to-occur eject/exit action in the corpus.
**LB presses: 4; measurable brackets: 4; bracket seconds: 1.397; press-free seconds: 179.6.**

Per press:

| press (UTC) | log | bracket s | left side | sampled fields that changed inside |
|---|---|---:|---|---|
| `2026-11-03T11:48:22.562` | `20261103T114350` | 0.491 | interval | `in0.aLeftShoulder`, `veh1.BatmanVsBatmobileCollisionMode`, `veh1.Driver`, `veh1.bits11D8`, `veh1.flags_11D8` |
| `2026-11-03T11:48:24.620` | `20261103T114350` | 0.696 | interval | `in0.aLeftShoulder`, `veh1.bits11D8`, `veh1.flags_11D8` |
| `2026-11-04T01:00:13.456` | `20261103T120003` | 0.157 | gap (not counted) | `in0.aLeftShoulder` |
| `2026-11-04T01:05:33.287` | `20261103T120003` | 0.053 | gap (not counted) | `veh1.flags_11DC` |

Rate table (real log fields that changed in or out of an LB bracket, sorted by in-bracket rate):

| field | presses it changed in | changes in brackets | rate_in (s^-1) | changes press-free | rate_out (s^-1) | ratio | verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| `veh1.bits11D8` | 2 | 2 | 1.432 | 99 | 0.551 | 2.60 | **UNKNOWN** |
| `veh1.flags_11D8` | 2 | 2 | 1.432 | 204 | 1.136 | 1.26 | **UNKNOWN** |
| `veh1.BatmanVsBatmobileCollisionMode` | 1 | 1 | 0.716 | 5 | 0.028 | 25.71 | **UNKNOWN** |
| `veh1.Driver` | 1 | 1 | 0.716 | 7 | 0.039 | 18.36 | **UNKNOWN** |
| `veh1.flags_11DC` | 1 | 1 | 0.716 | 22 | 0.123 | 5.84 | **UNKNOWN** |
| `RBatmobileEMPMissile1.LockOnTarget` | 0 | 0 | 0.000 | 9 | 0.050 | 0.00 | **UNKNOWN** |
| `RBatmobileEMPMissile1.LockOnTime` | 0 | 0 | 0.000 | 195 | 1.086 | 0.00 | **UNKNOWN** |
| `RBatmobileEMPMissile1.MissileAnimState` | 0 | 0 | 0.000 | 13 | 0.072 | 0.00 | **UNKNOWN** |
| `RBatmobileEMPMissile1.TagTarget` | 0 | 0 | 0.000 | 16 | 0.089 | 0.00 | **UNKNOWN** |
| `in0.bCancelButton` | 0 | 0 | 0.000 | 9 | 0.050 | 0.00 | **UNKNOWN** |
| `veh1.BattleModePrimaryWeapon` | 0 | 0 | 0.000 | 1 | 0.006 | 0.00 | **UNKNOWN** |
| `veh1.CurrentStrafeTarget` | 0 | 0 | 0.000 | 1 | 0.006 | 0.00 | **UNKNOWN** |
| `veh1.CurrentThrottle` | 0 | 0 | 0.000 | 2 | 0.011 | 0.00 | **UNKNOWN** |
| `veh1.CurrentWeapon` | 0 | 0 | 0.000 | 43 | 0.239 | 0.00 | **UNKNOWN** |
| `veh1.PreventModeSwitchDuration` | 0 | 0 | 0.000 | 2 | 0.011 | 0.00 | **UNKNOWN** |
| `veh1.PursuitModePrimaryWeapon` | 0 | 0 | 0.000 | 1 | 0.006 | 0.00 | **UNKNOWN** |
| `veh1.SecondaryWeapon` | 0 | 0 | 0.000 | 1 | 0.006 | 0.00 | **UNKNOWN** |
| `veh1.WeaponGeneratorPower` | 0 | 0 | 0.000 | 23 | 0.128 | 0.00 | **UNKNOWN** |
| `veh1.WeaponUnavailableReason` | 0 | 0 | 0.000 | 2 | 0.011 | 0.00 | **UNKNOWN** |
| `veh1.flags_11E0` | 0 | 0 | 0.000 | 2 | 0.011 | 0.00 | **UNKNOWN** |

`42` of the 62 real fields changed neither inside an LB bracket nor press-free
and are omitted above. The press definition `in0.aLeftShoulder` is excluded from this table: its
presence in its own bracket is true by construction, not evidence.

**Verdict:** 0 field(s) pass the margin on >= 3 presses: none. Nothing is promoted, so the answer
for A is **UNKNOWN**, for two counted reasons: A itself is never pressed (0) and
`bBatmobileEjectModifier` (+786) is never read, so no A byte exists in the corpus at all; and the
strongest eject-adjacent action that does occur (LB, 4 presses) moves the driver/collision/cockpit
fields on only 1-2 of those 4 presses - below the >= 3-press floor - while section 8 shows that a
window wide enough to catch them also catches the press-free baseline.

## 7. UNKNOWN 3 - boost duration / boost time field

Presses of Y: **0**. No boost flag, timer or object field is sampled (§3): `RBatmobileBooster.bBoosting`/
`bWarming` (+2396), `BoostingOut` (+5901), `AfterburnerSystem` (+4636), `LastBoostPickupTime` (+6580) are
all absent, and the two boost bits that *are* in the word (`bBoostLocked`, `InfiniteBoost`) never move
(§3 table). So there is neither a press window nor a boost signal to measure:

| candidate tested | presses available | in-bracket changes | away changes | rate_in | rate_out | verdict |
|---|---:|---:|---:|---:|---:|---|
| `RBatmobileBooster.bBoosting` (+2396 &1) | - | not sampled | not sampled | - | - | UNKNOWN |
| `RBatmobileBooster.bWarming` (+2396 &2) | - | not sampled | not sampled | - | - | UNKNOWN |
| `RVehicleBatmobileBase.bBoostLocked` (0x11D8 &0x4000) | 0 (Y) | 0 | 0 | 0.000 | 0.000 | UNKNOWN |
| `RVehicleBatmobileBase.InfiniteBoost` (0x11D8 &0x20000000) | 0 (Y) | 0 | 0 | 0.000 | 0.000 | UNKNOWN |

A duration also cannot be *derived* from this corpus: deriving it needs the `bBoosting` rise and fall,
and that bit was never read. UNKNOWN.

## 8. Method oracle - the same test on a binding that is known

A negative result is worthless if the instrument is blind, so the identical test is run on **LT**, whose
binding is decoded and was CONFIRMED live (D-11: hold battle / release pursuit; `aLeftTrigger` +724). The
battle-mode transition *should* appear in `veh1.flags_11D8` (the sampler names bit 0x2 ArmouredMode)
and in `veh1.CurrentWeapon` (booster -> heavy cannon); neither link is asserted here - the point is
only that a real, known input->state link exists in this corpus and the test is asked to find it.

**LT presses: 175; measurable brackets: 175; bracket seconds: 168.310; press-free seconds: 179.6.**

| field | presses it changed in | changes in brackets | rate_in (s^-1) | changes press-free | rate_out (s^-1) | ratio | verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| `veh1.bits11D8` | 12 | 16 | 0.095 | 99 | 0.551 | 0.17 | **UNKNOWN** |
| `veh1.flags_11D8` | 12 | 16 | 0.095 | 204 | 1.136 | 0.08 | **UNKNOWN** |
| `veh1.CurrentWeapon` | 6 | 6 | 0.036 | 43 | 0.239 | 0.15 | **UNKNOWN** |
| `veh1.BatmanVsBatmobileCollisionMode` | 0 | 0 | 0.000 | 5 | 0.028 | 0.00 | **UNKNOWN** |
| `veh1.Driver` | 0 | 0 | 0.000 | 7 | 0.039 | 0.00 | **UNKNOWN** |

**Oracle: FAIL** - 0 of 5 fields pass the same margin on a
binding that is known to work, so the mandated test cannot promote even a real input->state link here.
The cause is countable: 49 of 175 LT presses are followed by a
`flags_11D8`/`CurrentWeapon` change within 2.0 s, against 294 of 402
press-free sampled instants in the same 2.0 s window. The press does not raise the hit rate at all -
it is lower (28% vs 73%) - so
timing these logs cannot attribute the change to the press, and widening the window does not rescue
the test (sensitivity check only, `derived`).

## 9. Oracles (`--check` re-runs each)

| oracle | ok | detail |
|---|---|---|
| `away_is_press_free` | True | `{"away_seconds": 179.565, "bracket_seconds_LB": 1.397}` |
| `buttons_present` | True | `{"B": 62, "LB": 4, "LT": 175, "RT": 70, "THR": 73}` |
| `corpus_loads` | True | `{"files": 7, "records": 1122}` |
| `every_input_key_is_a_known_PI_field` | True | `["in0.aLeftShoulder", "in0.aLeftTrigger", "in0.aRightTrigger", "in0.aThrottleAxis", "in0.bCancelButton"]` |
| `logs_are_change_only` | True | `"first record of each file is the initial snapshot; later records are diffs"` |
| `margin_is_stated` | True | `{"abs_rate": 0.5, "gap_max": 5.0, "min_brackets": 3, "ratio": 3.0}` |
| `observable_coverage_recomputes` | True | `{"of_44_in_logs": 4, "present": ["RPlayerInput.aThrottleAxis", "RVehicleWeapon.bFiring", "RVehicleBatmobileBase.bBoostLocked", "RVehicleBatmobileBase.InfiniteBoost"]}` |
| `presses_are_rising_edges` | True | `"every bracket has right >= left"` |
| `sampler_offsets_match` | True | `{"BatmanVsBatmobileCollisionMode": 40, "BattleModePrimaryWeapon": 44, "CurrentStrafeTarget": 45, "CurrentThrottle": 40, "CurrentWeapon": 43, "Driver": 41, "PreventModeSwitchDuration": 41, "PursuitModePrimaryWeapon": 44, ` |
| `x_and_y_unpressed` | True | `{"X": 0, "Y": 0}` |

## 10. What stays UNKNOWN, and why no log can close it

1. **X barrage input byte** - no X press in any log (0), no X-named field in `RPlayerInput`, no
   missile-launcher field sampled. Closing it needs either the bind table/`BmInput.ini` (decode) or a
   new capture that samples `PI` at +773/+774/+784 and the launcher's `CurrentTargets` count.
2. **A eject input byte** - 0 A presses; `bBatmobileEjectModifier` (+786) never read. The LB-correlated
   vehicle-state fields above are consequence markers only. Same two routes.
3. **Boost duration/time** - 0 Y presses; `bBoosting` (+2396) never read; the two boost bits in the
   sampled word never change. A capture that reads +2396 is required; the duration must be measured
   from its rise/fall, not read from a field (G3-02f: none exists).

Everything above is `decoded` (file + offset + line, cited) or `derived` (rule + inputs, stated); no
value here is filled from general knowledge of the game or the engine.
