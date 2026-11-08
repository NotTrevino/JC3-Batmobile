# T-WP5b - the BmAK EMP burst, decoded; T-WP5's "nothing fires it" reopened

STATUS: done. The burst is now fully decoded (radius, four disable durations, four charge times, the
impulse, the effects, the audio switches, the wheel material, the button). The earlier closure was
narrowed, not accepted: a census proves there is no **data member** pointing at a pulse, and five
separate routes remain, each with a named 5-minute experiment. Nothing in the report says "JC3 cannot".

## Files

| file | what |
|---|---|
| `Tools/scripts/t_wp5b.py` | `--write` / `--check` / `--tamper`; decodes both packages + the research JSONs, rebuilds the md and the json byte for byte |
| `Working/Translation/T_WP5B_EMP_BURST.md` | 168 lines: 16 members, the numbers, the trigger, 5 JC3 routes, the disable question, the bindings, the row-by-row table, 3 compromises, 5 UNKNOWNs |
| `Working/Translation/T_WP5B_EMP_BURST.json` | the same facts as JSON (class members, archetype tags, impulse/charge rows, config rows, JC3 numbers) |

No existing file was edited. `T7_WEAPONS.md`, `T_ROWS.jsonl` and `COMPROMISES_T.md` are untouched; the
reopening is recorded in the new report only, as the card requires.

## The decode (all **decoded** from the packages, unless marked)

- **The row's "36 fields" is 36 rows, not 36 fields.** `RBatmobileEMP` declares **16** members; the
  archetype `Batmobile_EMP_Burst` serializes **12** tags in each of 3 variants = 36 field rows. Corrected
  in §1 of the output.
- **Range 7500 uu = 75 m** (`RBatmobileEMP.Range` @2396, class default; metres derived as uu/100).
- **Disable duration per power level: 2, 4, 8, 12 s** (`DisableEnemyDuration[4]` @2400).
- **Charge time per power level: 0, 0.5, 1.0, 1.5 s** (`PowerLevelChargeTime[4]` @2424).
- **Impulse**: radial component 15000.0 (`ImpulseComponent0` float @544, name UNKNOWN - `RB_RadialImpulseComponent`
  has no BmSDK-AK layout), falloff `RIF_Constant`, damage type `Core.RDmgType_Explosion`;
  `EMPImpulse` 5000, `EMPVehicleImpulse` 20000.
- **Cooldown 2.0 s** on the archetype, overriding a 10.0 s class default; `PowerConsumption` 1.0;
  `TempName` "EMP Burst"; `GadgetType` `GA_BatmobileWeapon_EMPBurst`.
- **Effects**: charge `Particles.EMP_Burst_Charge`; discharge `EMPs.EMP_Burst_Stage_01..04` (4 ParticleSystems,
  one per level); audio switches `Ww_Batmobile_Weapon_Level.Batmobile_Weapon_LVL1..4`; both `FireStartEvent`
  and `IndividualFireEvent` are `Engine.Play_Batmobile_EMP`.
- **The wheels light up**: `MaterialToUpdateWhenPresent` = `Batmobile_V3_Wheel_EMP_MAT_INST`, replacing
  `Batmobile_V3_Wheel_V2_MAT`, material index 0.
- **What it disables**: the gadget names it (`DisableEnemyDuration`); the vehicle class carries the receiving
  half - `RVehicleBatmobileBase.DisabledByEMP`, `VulnerableToEMP`, `EMPMaterialIndex` (default 9). The
  linking code is UNKNOWN; the two names plus the duration array are the evidence (derived).
- **Trigger, decoded from config**: `pBatmobileEMPLv1` = **Tap {PAD_B}**, `pBatmobileEMPLv2` = **Hold {PAD_B}**,
  keyboard `[3]` for both, and `RGameInfo.DefaultBattleKeyMap` binds the action as `EMPBlast` on
  `Three`/`LeftControl` with the HUD icons `CI_BatmobileEMPLv1/v2`. Tap vs hold = the two detents the keys
  advertise; the four-level ladder behind them is derived from `PowerLevelChargeTime`.

## T-WP5's closure, reopened

The old why: "nothing in the decoded files fires it". That is true of owners (`id:B5AE7986`) and of data
pointers; it is not a statement about the engine. The five routes, with status:

| route | status | 5-minute experiment |
|---|---|---|
| (a) copy the entity `CForcePulse` + `truck_emp.ftune` | decoded (the copy), firing UNKNOWN | put it on a test car and detonate: does the disable look appear? |
| (b) `CEMPWeapon` in a vehicle weapon slot | decoded absence (0 of 88 vehicle components), acceptance UNKNOWN | bind `w503_turret_emp` to a driver slot and fire |
| (c) copy the truck's use-item graph (`S_STUNT_USE_ITEM_VEHICLE`, `ui_activate_emp`) | decoded objects, link UNKNOWN | graft it on a test car and press use-item: does the prompt appear? |
| (d) a graph script fires it (the only non-owner pulse reference, mm340) | decoded pointer, bytecode UNKNOWN | decode the graph's node types for a pulse action |
| (e) a different host class (root `CCar` pulse that owns the blast) | decoded | 0-damage pulse on a `CCar`: does it still disable? |

Route (b) is the only carrier that is a **weapon**, so it is the only one with a fire button; that is where
the probe budget should go.

## COMPROMISES (recommendations only - the operator approves through Claude)

1. **Burst ships as a blast, not a disable.** Reason: every decoded carrier (pulse, tune, truck graph) fires
   a damage blast and the disable has no member in either game; all three probes that could settle it are
   forbidden by the test ban or need undecoded bytecode. Loss: the car cannot stop a pursuer. RECOMMENDED
   COMPROMISE: ship `CForcePulse` + `truck_emp.ftune` scaled to BmAK's 75 m intent and label it a blast
   until probe (b) returns.
2. **One power level instead of four.** Reason: JC3's pulse has one radius and one tune, no level member.
   Loss: the hold detent, the 0/0.5/1.0/1.5 s ladder, four effects, four audio switches. RECOMMENDED
   COMPROMISE: bind the single pulse to the tap detent, matching BmAK's tap.
3. **No wheel-EMP material flash.** Reason: no decoded JC3 member swaps a material on a charge state.
   Loss: the visible tell that the gadget is charging. RECOMMENDED COMPROMISE: discharge effect only.

Each is also written into §8 of the output with its reason, so a compromise without a reason cannot pass
`--check` unnoticed.

## Commands (verbatim, final run)

```
$ uv run python Tools/scripts/t_wp5b.py --write; echo "WRITE_EXIT=$?"
wrote Working\Translation\T_WP5B_EMP_BURST.md (168 lines) and Working\Translation\T_WP5B_EMP_BURST.json
range 7500 uu = 75 m; disable 2/4/8/12 s; charge 0/0.5/1/1.5 s; cooldown 2 s
PASS range 7500 uu (got 7500.0)
PASS range 75.0 m (got 75.0)
PASS disable durations 2/4/8/12 s (got [2.0, 4.0, 8.0, 12.0])
PASS charge times 0/0.5/1/1.5 (got [0.0, 0.5, 1.0, 1.5])
PASS EMPImpulse 5000 / EMPVehicleImpulse 20000
PASS cooldown 2.0 s on the archetype over a 10.0 s class default
PASS RBatmobileEMP declares 16 members
PASS the archetype serializes 12 tags
PASS 4 discharge ParticleSystems, Stage_01..04
PASS 4 AkSwitchNames, LVL1..LVL4
PASS both fire events are Engine.Play_Batmobile_EMP
PASS impulse 15000.0 with RIF_Constant falloff
PASS impulse damage type RDmgType_Explosion
PASS charge particle EMP_Burst_Charge
PASS at least 4 config rows for the burst (got 18)
PASS tap detent in the config
PASS hold detent in the config
PASS RVehicleBatmobileBase declares DisabledByEMP and VulnerableToEMP
PASS 0 CEMPWeapon among 88 vehicle components
PASS truck_emp tune 100 / 25 m
PASS car_explosion_medium 500 / 5 m
PASS 307 pulses over 232 entities
PASS 14 unowned pulses
PASS the two CEMPWeapon users
WRITE_EXIT=0

$ uv run python Tools/scripts/t_wp5b.py --check; echo "CHECK_EXIT=$?"
PASS T_WP5B_EMP_BURST.md re-derives byte for byte from the packages
PASS T_WP5B_EMP_BURST.json re-derives byte for byte from the packages
PASS: T-WP5b 0 failure(s)
CHECK_EXIT=0

$ uv run python Tools/scripts/t_wp5b.py --tamper; echo "TAMPER_EXIT=$?"
PASS tamper detected: the radius in metres
PASS tamper detected: a disable duration
PASS tamper detected: the falloff
PASS tamper detected: the cooldown
PASS tampered copy on disk differs from the re-derivation
PASS: 5/5 tamper probes detected
TAMPER_EXIT=0
```

`--check` re-reads `BmGame.upk` (`Default__RBatmobileEMP`) and `Playable_Batmobile_SF.upk`
(`Batmobile_EMP_Burst`, `ImpulseComponent0`, `ChargeParticle0`) through `Tools/scripts/upk_read.py`; with the
install absent it exits with "missing package ... - the decode needs the BmAK install", i.e. it fails rather
than passing on stale numbers. No game file was written and the game was not launched (test ban).

## Coordination with 7322

`Working/Translation/T_WP4C_TRACKER_EMP.md` **does not exist** at the time of writing (`ls` fails on it; no
`*wp4*`/`*7322*` report in `tmp/freebuff/reports/`). Nothing of 7322's was read or redone; the EMP-missile
half (T-WP4 / WPN-4) is left to it.

## UNKNOWNs (route named, none closed)

1. The names of the two `RB_RadialImpulseComponent` floats (15000 and the junk-looking 0.2468) - route:
   the component's generated header in BmSDK-AK.
2. `EMPForceFeedbackWaveform` samples - route: dump the default object's sub-object @0x9b8.
3. Which AI or vehicle classes set `VulnerableToEMP` - route: grep the 103-class census; the flag is
   declared on `RVehicleBatmobileBase` only in the decoded set.
4. The button -> `bButtonPressed` -> `ChargingEMP` code path - route: `RBatmobileEMP` function bodies.
5. The JC3 firing moment of any pulse, including the EMP - routes (b), (c), (d) above.
