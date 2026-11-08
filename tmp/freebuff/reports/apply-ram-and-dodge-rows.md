# T-DM7 / T-RA1 — one carrier, one card, and the prediction the in-game test carries

STATUS: **done** — `T-DM7` moved `out → next` on a decoded outgoing contact-damage member with its
member paths and both BmAK value sets; `T-RA1` moved `out → blocked` on a new backlog card
(`G2-35`) that names the capability to be found instead of leaving "no JC3 system" in the row. The
ledger, `BLOCKED_PROPOSALS`, the T-10 table, the compromise audit and `STATUS.md` all re-derive from
the same edits; five checks pass and `t23_closeout --check` fails only its §11 decision-count gate
(unrelated, one decision record over D-1…D-10). Nothing launched, installed or written outside
`Working/Translation/`, `Research/specs/`, `GRAB_BACKLOG.md` and this report.

## 0. Change statement (AGENTS.md)

| item | value |
|---|---|
| intended change | re-decide the two ram/dodge rows against `tmp/freebuff/reports/carrier-ram-and-dodge.md`; add the card that names the missing capability; keep the ledger and the blocked-proposal sheet in step |
| files | `Working/Translation/T3_COVERAGE.md` (the two rows), `Tools/scripts/t_rows.py` (DISPO), `Tools/scripts/t10_reopen.py` (T-10 decisions + evidence), `Tools/scripts/audit_compromises_t.py` (two entries), `Tools/scripts/t_blocked.py` (wait + counts), `Research/specs/G2-35.md` (new), `GRAB_BACKLOG.md` (§12 tracker row) |
| why these files | the dispositions live in `T3_COVERAGE.md` and are generated into the ledger by `t_rows.py`; `t10_reopen.py` owns the T-10 re-decision table and fails if a row's `why` stops naming its proof; `t_blocked.py` fails if the blocked set drifts from its waits table; the card is the phase-G slot for a capability that no value row can carry |
| reverted by | `cp` back the five files from git, delete `Research/specs/G2-35.md`, drop the G2-35 tracker row, then re-run the five `--write` steps below. No build, install or launch is involved |

## 1. `T-DM7` — carrier found: `rotor_collision.damage_to_other_per_second`

The report's §2 re-counts the block on all 232 vehicle module sets (donor included): an **outgoing
contact-damage member exists**, so the row's old premise ("G2-28 found no outgoing ram damage") was
too strong. `T-DM7` is now `next`:

| cell | now says |
|---|---|
| JC3 target | `rotor_collision.damage_to_other_per_second` **100000/s**, `light_object_mass_ratio` 0.02, `mass_ratio_when_no_mass` 0.1, `min_rpm` 30 — module `VehicleCommon` / `all_vehicles_common`; **byte offset UNKNOWN** (the block sits inside the `.ee`-embedded shared module, not in any of the 408 standalone `*_vmodc` files) |
| BmAK numbers | `ImpactMinDamageSpeed` 20 (class 60), `ImpactMaxDamageSpeed` 150 (class 200), `ImpactStrafeMod` 2.25 (class 1.5), `ImpactBoostMod` 2.0 (class 1.5), `ImpactCivilianVehicleMod` 1.0 (class only, not serialised), `BattleModeImpact*` 120/540 — every one outgoing |
| transform | **rate vs band**: JC3 divides by time above `min_rpm` 30 and scales by the target's mass ratio; BmAK divides by contact speed in 20…150 with strafe and boost multipliers. No JC3 speed member, no strafe/boost member |
| confidence | decoded (member + n=232) / UNKNOWN (whether the engine evaluates it on a `CCar` with no rotor) |
| verify | **Q-RM-1**: ram a stock car and a `CDamageController` barrel at 20, 60 and 150 km/h — the target loses health at one per-second rate, not a 20→150 band, and the Batmobile's own bar does not move |

Named omission carried in the row, not hidden: the **speed band** (20→150, ×2.25 strafe, ×2.0 boost)
has no JC3 member, and 100000/s is a declared switch (3.4× BmAK's 150-speed damage). The report's
§1 also records that `CLASS_DEFAULTS.md` and the archetype tags disagree on four of these members
(60/200/1.5/1.5 vs 20/150/2.25/2.0); the row quotes both and treats the archetype as the shipped
instance, as the report does.

## 2. `T-RA1` — no carrier at any layer, so a card names the capability

The report searched five layers and found **0** road-assist / dodge / shove / kill-flip members:
vehicle modules (52 types / 1,421 paths), the 232 entity graphs and their 104-class vocabulary,
`CDamageController` (victim health only), the `.physicsc` packfiles (0 contact material, 0
contact-damage record) and the script layer (0 of 4,832 exit nodes carry a force). The nearest
members — `drift.max_drift_torque` 0x48, `arcade.nitro_boost.push_force` 15000,
`arcade.turbo_jump.*` 0xC4…0xD8 and a `CForcePulse` that only fires on an explosion — are all
continuous, target-less and duration-less.

`T-RA1` is now `blocked` (not `out`, not "no JC3 system"), and the row names:

* the values that have to arrive — road assist 40000/90000 factor, 15000/30000 max torque, 2000
  angle strength, 45°, 0.75/1.5/0.25 s; dodge 5000 torque / 6000 force / 0.25 s; shove
  20000/10000; kill-flip −2000000 over 1.5 s;
* the capability itself — **a triggered, non-damaging impulse/torque with target selection and a
  duration**;
* where it is argued — `Research/specs/G2-35.md` (new card; §12 tracker row `G2-35 = todo`) and
  `tmp/freebuff/reports/carrier-ram-and-dodge.md` §8/§9.

The card's Done clause is concrete: either a decoded carrier with member paths, fleet presence and
BmAK values (which moves the row to `next`), or the same absence proven across the two
entity-object candidates still open (the 14 unowned `CForcePulse` objects, the 33 empty
`CGrapplingHookPropData` enable/disable pairs), which keeps it `blocked` with the proof recorded.

## 3. The Arkham Knight prediction the later in-game test checks

`Research/BatmobileGrab/DAMAGE_RULES.md` §3.3 decodes the ram as **target-class sensitive only on the
vehicle side**, and that is the whole difference its notes support — so the card states it that way
rather than filling in the pedestrian case from memory:

| target | AK notes decode | prediction the test checks |
|---|---|---|
| car / any vehicle | band 20→150 pursuit (120→540 battle), ×2.25 strafe, ×2.0 boost, gate `CanBatmobileDoImpactDamage` (native), `TakesDamageFromRam(Target, RamSpeed)`; `bHasAPCStyleWeakSpot` targets lose the weak spot (`RemoveWeakSpot`) — a **multiplier removal**, not extra damage | the target loses health on the band, the Batmobile loses none (T-DM8 keeps `impact_damage_factor` 0), and the jc3 build shows a flat per-second rate instead |
| civilian vehicle | `ImpactCivilianVehicleMod` **1.0** as the class default (`CLASS_DEFAULTS.md:259`, 0x04f8) and **absent from both the shipped and the Joker archetype** | no civilian-specific multiplier in the instance; whether the class-default 1.0 is applied at runtime is UNKNOWN |
| pedestrian | the impact function reads `OtherVehicle` and only vehicle multipliers; `Pawn` classes carry `Health`/`HealthMax`/`Healer` (`DAMAGE_RULES.md` §5), but **no decoded member or script routes a Batmobile contact into them** | AK's pedestrian outcome is **UNKNOWN from the files**. JC3 has no character class in its 232 graphs (report §7), so the build prediction is: a pedestrian is untouched by contact at any speed. A reaction there is new information — a character-damage card, not a failed T-RA1 test |

That asymmetry is deliberate: the car half is a number to measure, the pedestrian half is an absence
to confirm.

## 4. The edits, file by file

| file | edit |
|---|---|
| `Working/Translation/T3_COVERAGE.md` | `T-DM7` row rewritten (carrier, offset UNKNOWN, rate-vs-band transform, Q-RM-1); `T-RA1` row rewritten (`blocked`, five-layer absence, capability named, G2-35, Q-RM-2) |
| `Tools/scripts/t_rows.py` | `DISPO["T-DM7"] = next`, `DISPO["T-RA1"] = blocked`, each with the carrier/card path in the `why` (the string `t10_reopen --check` re-reads) |
| `Tools/scripts/t10_reopen.py` | `T-DM7` `now: next` + three evidence needles (`VOCABULARY.md` member, mass ratio, report's named omission); `T-RA1` `now: blocked` + the existing absent-vocabulary test plus two needles (report §9, the card) |
| `Tools/scripts/audit_compromises_t.py` | `T-DM7` compromise restated as the rate + mass ratios with the band as the loss; `T-RA1` restated as "blocked, G2-35 names the capability" |
| `Tools/scripts/t_blocked.py` | `WAITS["T-RA1"]` added; `reconciles` now `9 ledger + 4 T6 = 13 blocked, in_scope 189`; docstring counts updated |
| `Research/specs/G2-35.md` | new card: values, five-layer search, AK prediction table, what "found" looks like, Done clause |
| `GRAB_BACKLOG.md` | §12 tracker row `G2-35 · todo` with the card and the carrier report |
| generated | `T_ROWS.jsonl` (198 rows), `BLOCKED_PROPOSALS.{json,md}` (13 blocked of 189, new ledger sha), `T10_OPEN_ROWS.{json,md}`, `COMPROMISES_T.{json,md}`, `STATUS.md`, `BUILD_BATCHES.md`/`build_batches.json` |

## 5. Checks actually run

```
python Tools/scripts/t_rows.py build            -> 198 rows, 35 edits over 16 rows
python Tools/scripts/status_audit.py --write    -> wrote STATUS.md (rc 0)
python Tools/scripts/t_blocked.py --write       -> 13 blocked (9 ledger + 4 T6) of 189 in scope
python Tools/scripts/t10_reopen.py --write      -> 16 rows: 5 superseded, 6 out, 2 blocked
python Tools/scripts/audit_compromises_t.py --write -> 72 audited, 1 approved
python Tools/scripts/t23_closeout.py --write    -> wrote build_batches.json
```

```
t_rows.py check           rc=0  "check ok"   (198 rows: edit 16, next 53, keep 60, epe 26,
                                                blocked 9, out 27, superseded 7)
t_blocked.py --check      rc=0  PASS: 13 blocked re-derived (9 + 4) of 189 in scope, all evidence
                                markers present, ledger sha256 unchanged
t10_reopen.py --check     rc=0  PASS: 16 rows, 6/6 out rows proven, successors B-05, T-11, T-12,
                                T-15, T-17, T-18, json + md match
status_audit.py --check   rc=0  "STATUS.md is current"
audit_compromises_t.py --check rc=0  every approval quote re-read at its cited line
t23_closeout.py --check   rc=1  FAIL §11 has 11 decisions, expected D-1...D-10
```

`T-RA1` appears as row 2 of the 13 in `BLOCKED_PROPOSALS.md`; `T-DM7` is no longer in that sheet.
`STATUS.md` now reports **13 blocked / 189 in scope**, 34 out, 8 superseded, 53 queued.

Two rounds were needed on the T-10 evidence: the first marker for the report matched the heading's
capital "T" wrongly, and the card's summary line wraps mid-phrase, so both were replaced with
substrings that survive the line break. The final `t10_reopen --check` above is the post-fix run.

## 6. What this cannot prove

* **`T-DM7`'s carrier is a candidate, not a demonstrated channel.** The member, its type and its
  fleet presence are decoded; the byte offset is not, and whether a `CCar` with no rotor evaluates
  the block is UNKNOWN. Q-RM-1 is the probe, and it needs a launch (test ban).
* **The 100000/s value is not BmAK's damage.** It is a per-second rate where BmAK has a speed band;
  the row declares the switch rather than pretending the numbers bridge.
* **`T-RA1` is blocked on a capability, not on a decision.** No operator question would unblock it;
  card G2-35 either finds the mechanism in data or proves it is code-only.
* **The pedestrian prediction is an absence claim about decoded surfaces**, not a measurement of
  Arkham Knight. It says the notes do not route a vehicle contact to a `Pawn`; it does not say AK
  cannot hurt a pedestrian.
* Nothing here launches the game, writes a game file or touches `Builds/`.
