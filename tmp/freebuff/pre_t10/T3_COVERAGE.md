# T-3 — every other Batmobile factor, accounted

T-1 and T-2b translate the factors they name. They do not prove the list was complete. This table
closes that: the decoded Arkham Knight Batmobile is **423 fields across 15 classes**
(`Research/BatmobileGrab/OFFSETS.json`), and `Tools/scripts/bmak_coverage.py` assigns every one to a
row here or in T-1/T-2b. `--check` fails on a field with no row, so a factor that never reached the
table cannot hide.

Three kinds of row appear below:

* a **factor JC3 does carry**, with fleet numbers behind it (`T3_FLEET.md`: 156 land vehicles,
  medians and interquartile bands at the built 6 t class);
* a **factor JC3 cannot express**, marked `out` with the reason — accounting, not a to-do;
* a **factor blocked by a missing member or asset**, with the probe that would unblock it.

The damage block is the exception to "a value is a value": the car's immunity to collisions is a
declared **switch** (**T-DM8**, `damage_switches.json`), not a translated number, and the small-arms
half (**T-DM9**) has no member to hold it at all. T-DM7, which used to read as a value correction
there, is `out`: it was the Batmobile's ram *attack*, and test-087 mistook it for defence. That
regression is written up in `POSTMORTEM_DAMAGE.md`.

## 1. The rows

| # | BmAK source | JC3 target | transform | now | proposed | conf | verify |
|---|---|---|---|---|---|---|---|
| T-G6 | `SVehicleWheel.WheelRadius` = 64.0 | `land_global.front/rear_wheels.radius` | decoded | 0.68275 / 0.68265 m (mesh) | **keep** the mesh radius: 0.64 m is BmAK's contact-radius simplification inside a 0.683 m visual tyre, and the JC3 radius sets both contact and ride height | decoded | T-G2 mesh bounds; ride height in QA-1 |
| T-S6 | `SuspensionTravelUp` 30, `SuspensionTravelDown` 40, `BMRearWheelMaxDroop` 100 (cm); `BM/PMWheelSuspensionStiffness` 3000/750, `SuspensionDamping` 300, `SuspensionBias` 50, `FrontWheelSuspensionBias` 10, `PMWheelSuspensionBias` 20 | none — `suspension.length/min_length` carry one stroke, and `strength/compression` carry one rate | — | length 0.25, min 0, max offset 0 (T-S3); strength 45, compression 3.0 (T-S1/S2) | **blocked**: JC3 has no per-axle bias, no droop and no undamped-rate member, and the stiffness/damping pair has no unit bridge to `strength` (fleet 4–80). The stroke half is no longer blocked: as of Batch B4, T-S3 carries BmAK's 0.70 m (TravelUp 30 + TravelDown 40) directly, and T-S1/S2 keep the fleet's rate. That stroke is 3.9× the heavy-class median (0.18 m) but inside its band (0.18 … 0.75), so it is declared BmAK-first, not silent | blocked | needs a decoded JC3 suspension model; the row exists so the omission is explicit |
| T-ST7 | `SteerSpeed` 220 °/s, `SpinSteeringFactor` 100000, steer-curve knots `InVal/OutVal/ArriveTangent/LeaveTangent` | `land_steering.t_to_full_steer_s` (T-ST1/T-ST3 cover the curve and the high-speed rate) | derived | 0.8 s low speed / 0.6 s high speed | **blocked**: 55° lock at 220 °/s is 0.25 s, and the fleet's fastest rack is 0.5 s; JC3's steering model cannot be that quick, so the table keeps 0.8 s inside the family | blocked | slalom at 60 km/h; the lag is a JC3 model limit, not a value left untranslated |
| T-K4 | `EbrakeTime` 0.75, `EBrakeBrakeForce` 640000, `HandbrakeOnSpeed` 10000, `HandbrakeOffSpeed` 1, `HandbrakeLatSlipFactor` 1.5/1.1 | `brakes.front/rear.handbrake`, `handbrake_friction_factor` (T-K3), `min_time_to_block` (T-K2) | class | rear-only handbrake, friction 1, min_time 5 | **keep**: the 6 t friction median is 1 and every heavy vehicle is rear-handbrake; the e-brake force is in Unreal force units with no bridge, and its 0.75 s duration has no JC3 member | class | handbrake turn at 40 km/h in QA-1 |
| T-DR1 | `LatSlipFactor` 1.6, `HandbrakeLatSlipFactor` 1.5, `DriftingBoostCooldown` 1.5 s | `custom_land_global.drift.*` (12 members) | — | 45° max, 20° entry, 10 km/h minimum, sensitivity 4, yaw damping 0.02/0.03 | **keep**: the build's drift block is the donor's own, member for member (`VOCABULARY.md` donor column: entry 20, max 45°, min 10 km/h, sensitivity 4). Against the 6 t class (`T3_FLEET.md`: median entry 180°, sensitivity 2) the entry and sensitivity are donor character, not class medians | decoded | 60 km/h handbrake drift: angle holds, no snap-back |
| T-EF1 | `SquealThreshold` 0.2, `SquealLatThreshold` 0.2, wheel skid/spin/wetness particle systems | `vehiclecommon.tire_effects.*` (23 members) | class | min skid velocity 0.5 m/s, slip-to-skid 0.8, scale 0.25 | **keep**: fleet p25 = median = p75 on all three, so there is nothing class-specific to move; the particle systems are T-FX6 | class | skid and smoke appear at the same slip angle as another 6 t car |
| T-DM7 | `ImpactMinDamageSpeed` 20, `ImpactMaxDamageSpeed` 150, `ImpactStrafeMod` 2.25, `ImpactBoostMod` 2.0, `BattleModeImpact*` — **all outgoing** | none | **none**: `TakesDamageFromRam(Target, RamSpeed)`, `CanBatmobileDoImpactDamage(OtherVehicle)` and `CalculateAndStoreImpactDamage(OtherVehicle, …)` all take the vehicle being rammed; the class has no incoming-impact entry | impact_damage_factor 0, impact_armor 5000 (both out of domain, inert) | **out**: this is the ram *attack* — the Batmobile wrecking what it hits — and JC3 gives a player car no way to damage the vehicle it rams. The incoming direction is T-DM8. test-087 translated this block as defence and turned collision damage on; withdrawn | decoded (class API) | n/a — no JC3 system |
| T-DM8 | **behaviour**: ramming anything at any speed leaves the health bar untouched (BmAK play; the HUD feeds the bar through `UC_SetHealth`, `HUD.md`) | `vehicledamage.impact_damage_factor` | **switch** 0, declared in `damage_switches.json` | 0 (hand-set, unrecorded until now) | **keep 0**: a multiplied-off switch, not a value. The shipped range is 1…12, so it is recorded as a deviation with its reason — never "corrected" to the fleet median | behaviour (BmAK) + switch (JC3) | full-boost ram into traffic and into a wall: health bar unchanged, no crumple, no fire |
| T-DM9 | **behaviour**: small arms do not move the health bar; only heavy weapons (tank cannon, missiles) do | entity root **`CCar.invulnerable`** (int32), not the module; `VehicleDamage` channels stay as they are | **module: none** — the build is already at the shipped maximum in every armour channel (bullet 5000/100, explosion 250/4000, smoke 1050, burn 250) and bullets still destroy it, so armour only reduces. **Entity: route found** — `invulnerable` is 0 on all 233 shipped roots, `1` is shipped by 10 `CDamageController` objects, and the field is `type 0x0e · hash af4406fb · value` at `epe+1162/+1163/+1167` | all channels at the ceiling; root flag 0 | **blocked pending the write**: set `invulnerable = 1` (4 bytes at `epe+1167`) in a one-variable probe build. Whole-vehicle flag — it also blocks the destruction BmAK has in tank battles, so it fits "ramming and small arms do not scratch it", not "only heavy weapons" | measured (test-087, fleet domain) + decoded (232 entity graphs, `Research/JC3Grab/DAMAGE_MECHANISMS.md`) | 200 rounds of SMG + a full-boost ram: health bar untouched, no fire, no explosion |
| T-FX6 | `BrakeLightTrailSystemL/R`, `RearFinTrail`, `SpeedLinesSystem`, `HeatSteam`, `WallScrapeSparksSystemL/R`, `ExhaustBurstEffect`, `SideExhaust*`, wheel particles | entity-graph effects (`.effc`, part trails) | epe | carried from test-083 | **keep**: the effect graph is already the Batmobile's | epe | night run in QA-1 |
| T-AU5 | `TransformationReverseDirection*` sounds, `TaserSound`, `VehicleSound` | audio banks in the entity graph | blocked | engine bank swapped (T-AU2) | **blocked**: these events have no JC3 bank and 10 BmAK banks are absent from the install (T-AU3) | blocked | needs the banks |
| T-W1 | 11 weapon classes: cannon, heavy cannon, missiles, EMP, sonar, winch, tracker, Joker launcher, hacker | — | — | — | **out**: JC3 gives a car no player-fired weapons, and the mod has no weapon slots. This is the largest block in the file — 261 of 423 fields — and none of it is a vehicle factor | out | n/a — feature gap |
| T-BM1 | `BattleMode*` (9), `TurnOnSpot*` (3), `TransformationTurn*` (2), `TurningModeMaxSpeed`, `ArmourModeDamageReduction` | — | — | — | **out**: JC3 has no transformation, no tank turn and no battle-mode armour; the mod ships pursuit-mode behaviour permanently | out | n/a |
| T-AC1 | `AirControlYawTorqueFactorMax` 8000 | — | — | — | **out**: JC3 cars have no mid-air yaw authority; the fleet's only air member is `takeoff_pitch_damping` | out | n/a |
| T-RA1 | `ImpactRoadAssist*` (90000 / 30000 / 2000), `PMDodge*`, `BattleDodgeImpulse`, `VehicleShovingTorque` 10000, `KillFlip*`, `KillKeepyUp*`, `ImpactShake*` | — | — | — | **out**: these are Batman's ram/dodge/shove assists against thugs; JC3 has no car melee or ram-assist system | out | n/a |
| T-SR1 | `JumpRampRightingTorque` 2000, `JumpNoRampRightingTorque` 2000, `StayUprightConstraintSetup/Instance` | — | — | — | **out**: JC3 has no upright constraint; a rolled car stays rolled. That is an engine feature, not a table value | out | n/a |
| T-PA9 | the remaining `RVehicleBatmobile` actor composition: components, sockets, archetypes, tags, light and health refs | entity graph | epe | donor wiring | **keep**: the graph carries it; this row exists so the count is auditable | epe | entity census (`ENTITIES.md`) |

## 2. Coverage

`python Tools/scripts/bmak_coverage.py --check` prints one line per row and `check ok`. The generated
`Research/BatmobileGrab/COVERAGE.md` lists all 423 fields, their class and their row.

| what | count |
|---|---|
| decoded fields | **423** |
| classes | **15** |
| assigned to a T-1/T-2b/T-3 row | **423** |
| fields that are vehicle factors or effects | **74** |
| fields that are Unreal actor plumbing (T-PA9) | **51** |
| fields JC3 has no expression for (T-W1 261, T-BM1 16, T-RA1 16, T-SR1 4, T-AC1 1) | **298** |

Two classes are held to a stricter rule than the rest: a *new* field in `RVehicleSimBatmobile` or
`SVehicleWheel` fails `--check` rather than being filed as plumbing. Those two classes are the car.

## 3. Evidence

`T3_FLEET.md` is generated by `Tools/scripts/t3_fleet.py`: the median and interquartile band of every
member the T-1, T-2b and T-3 rows cite, across 156 land vehicles, at 3–8 t and 6 t+. Every "the 6 t
median is …" in those tables is quoting it, and re-running the script reproduces the numbers. A
`-1` in a steering or brake member is the game's sentinel, not a measured time.

## 4. What the next handling build carries (damage block withdrawn)

**Nothing damage-related.** test-087 carried three damage values and was withdrawn after the drive
(`POSTMORTEM_DAMAGE.md`): `impact_damage_factor 0 → 1` was a direction error, `impact_armor 5000 → 5`
removed a (misrecorded, out-of-domain) belt-and-braces cap, and `deform_scale 0 → 1` is a cosmetic
switch that stays off. The live build rolls back to test-085, which has the switch on.

Staged but **not built**, and not to be built until each has a behaviour and a failing take (rule R1
in `POSTMORTEM_DAMAGE.md` §8) — these six are class medians and nothing more:

```
custom_land_global.arcade.nitro_boost.grip_multiplier  5.68 -> 2.0   T-B3
land_steering.countersteer_speed_factor         2.0 -> 3.0   T-ST5
land_steering.steer_in_speed_factor             1.5 -> 2.0   T-ST5
brakes.front.min_time_to_block                  5 -> 1      T-K2
brakes.rear.min_time_to_block                   5 -> 1      T-K2
custom_land_global.arcade.nitro_boost.extra_top_speed  50.46 -> 40   T-B2
```

Everything else in this table is already correct, impossible in JC3, or waiting on a decoded model
or a missing bank. The end state is not "all numbers differ from the fleet"; it is "every factor is
accounted for, and the parts of Arkham Knight's Batmobile that JC3 has no system for are named
instead of silently dropped".
