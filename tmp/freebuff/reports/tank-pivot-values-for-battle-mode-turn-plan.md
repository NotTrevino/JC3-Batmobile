# Turn-on-the-spot in battle mode — BmAK's members against JC3's tank values

Sources: `Research/JC3Grab/TANKTURN.json` / `TANKTURN.md` (G2-21, the tank pivot decode),
`tmp/freebuff/reports/G2-21.md`, `tmp/freebuff/reports/T-MD14b.md` and
`tmp/freebuff/reports/mode-switch-carriers.md` (the mode-switch work), plus
`Research/BatmobileGrab/MODES.md` for the BmAK values themselves.

Labels: **decoded** = read in the file named (TANKTURN.json keys are quoted); **derived** = a
stated conversion over decoded values; **UNKNOWN** = absent, with the file that settles it.

**Answer in one line:** the tank pivot does **not** carry BmAK's turn-on-the-spot. JC3's four tanks
are ordinary `CCar` wheel vehicles (`TANKTURN.md` §5, 12/12 `CCar`), the four card modules are
member-identical between tanks and cars (`0` tank-only / `0` non-tank-only members), no driving
module holds a tank-unique value (262 tank-unique members, **0** in a driving module), and no member
in the 1,421-row vocabulary names a track or a pivot (`TANKTURN.md` §3-§4). Of BmAK's six
turn-on-the-spot members, **three have a JC3 receiver and three have none**: the speed cap, the
stationary angle and the counter-steer gain map onto real members; the front/rear torque pair, the
turn-on-spot torque factor and the engine-braking factor have no per-axle or per-mode torque member
to land in, because a wheeled car has one driveline. The split BmAK does with counter-rotating axles
can only be approximated by **per-axle grip asymmetry plus the drift yaw-torque block**.

---

## 1. What the tanks actually are (the premise, decoded)

| fact | value | source |
|---|---|---|
| tank builds | **12** (4 chassis × 3 variants) | `TANKTURN.json` `card.tank_builds` |
| vehicle class | `CCar` on 12/12 | `TANKTURN.md` §5 |
| module types on a tank | 25 of the fleet's 52; **0 tank-only** | `TANKTURN.json` `module_types.tank / .tank_only` |
| card modules (`LandGlobal`, `LandSteering`, `Transmission`, `CustomLandGlobal`) | 48 / 15 / 40 / 61 members, **identical sets**, no tank-only and no non-tank-only member | `TANKTURN.json` `card.module_sets` |
| tank-unique values | 262, by module `WaterInteraction` 194, `EffectAttachments` 37, `Propellers` 16, `Fins` 14, `DeformPoints` 1 — **0 in a driving module** | `TANKTURN.md` §3 |
| wheel stations | match `number_of_wheels` on all 12 — a wheel set, not a track belt | `TANKTURN.md` §5 |
| member names containing track/pivot/skid/neutral/counter-rot | **9 hits**, all tyre-smoke effect thresholds plus the train's rail gauge; none in a driving module | `TANKTURN.md` §4 |

**Derived:** the tanks pivot (if they pivot at all) because of native code keyed to the vehicle's
identity, not because of a value a mod can copy. Whatever the Batmobile gets must be built out of
ordinary car members.

## 2. The tank values that are available to copy (`TANKTURN.json` `table.chassis`)

Player copies, four chassis, member → value:

| member | `v0200` APC | `v0201` medium | `v0202` Bavarium | `v0603` small | fleet range (n) |
|---|---:|---:|---:|---:|---|
| `LandGlobal.number_of_wheels` | 6 | 8 | 8 | 4 | 2..8 (271) |
| `LandGlobal.number_of_front_wheels` | −1 | 4 | 4 | −1 | −1..4 (271) |
| `LandGlobal.wheels_friction_type` | 2 | 2 | 2 | 2 | 0..2 (271) |
| `LandGlobal.ground_clearance` | 0.4 | 0.4 | 0.4 | 0.6 | 0.05..1 (271) |
| `LandGlobal.front_wheels.radius` | 0.48 | 0.66 | 0.66 | 0.564 | 0.2..1.8 (271) |
| `LandSteering.steer_angle_min_speed_deg` | 35 | **45** | 45 | 35 | 20..45 (252) |
| `LandSteering.steer_angle_max_speed_deg` | 15 | **30** | 30 | 25 | 10..35 (252) |
| `LandSteering.min_speed_kmph` | 20 | **10** | 10 | 10 | 1..80 (252) |
| `LandSteering.max_speed_kmph` | 150 | 100 | 100 | 100 | 50..300 (252) |
| `LandSteering.countersteer_speed_factor` | 3 | **5** | 5 | 5 | 1.5..20 (252) |
| `Transmission.final_drive` | −1 | **8.4** | 8.4 | 10 | −1..37.33 (145) |
| `Transmission.gears` | 5 | 5 | 5 | 4 | 1..8 (145) |
| `Transmission.top_speed` | 110 | 105 | 105 | 90 | 90..505 (145) |
| `CustomLandGlobal.drift.max_drift_angle_deg` | 25 | **45** | 45 | 45 | 20..60 (145) |
| `CustomLandGlobal.drift.min_speed_to_drift_kmph` | 10 | **10** | 10 | 10 | 0..60 (145) |

Donor (the Batmobile's own car values, same file, `names.card_module_ranges`): `steer_angle_min_speed_deg`
**35**, `steer_angle_max_speed_deg` **15**, `min_speed_kmph` **30**, `max_speed_kmph` **220**,
`countersteer_speed_factor` **2**, `final_drive` **3.91**, `gears` **6**, `top_speed` **320**,
`drift.max_drift_angle_deg` **45**, `drift.min_speed_to_drift_kmph` **10**.

## 3. Member-by-member: BmAK → nearest tank value → number to write

The BmAK side is `Research/BatmobileGrab/MODES.md` (offsets and per-package values). Six members are
in scope; the transformation torque pair (`TransformationTurnTorqueFactor` 3000 / `…DecelTorqueFactor`
24000, 0x390/0x394) belongs to the mode-switch build and is listed last because it has no turn
receiver at all.

| # | BmAK member (0x) | value | nearest `TANKTURN.json` value | unit conversion | number to write | evidence |
|---|---|---|---:|---|---|---|
| 1 | `TurnOnSpotFrontTorqueFactor` (0x1c8) | 0.8 | **none** — no per-axle torque member in any driving module; nearest *carrier class* is `LandGlobal.wheels_friction_type` **2** (all 12 tanks) | factor is dimensionless; the tyre enum is 0/1/2, so no conversion exists | **none** — `wheels_friction_type` 2 may be copied as the tanks' only tyre signal, but it carries no torque value | decoded value + decoded absence (`TANKTURN.md` §2, §3) |
| 2 | `TurnOnSpotRearTorqueFactor` (0x1cc) | −0.8 | **none**, same reason; the pair is symmetric (\|0.8\| = \|0.8\|), so it encodes counter-rotation, not a grip bias | — | **none**; the only authorable split is the per-axle friction pair (see §4) | decoded value + decoded absence |
| 3 | `TurnOnSpotModeEngineBrakingFactor` (0x1d0) | 2 | `LandSteering.countersteer_speed_factor` **5** (medium/Bavarium/small tanks; donor car **2**) | factor → factor, 1:1 | **2 — keep the donor's 2**: it already equals BmAK's value, and the tank's 5 is a counter-steer gain, not engine braking. Copying 5 would *raise* it | decoded (BmAK 2, donor 2, tank 5) |
| 4 | `BattleModeTurnOnSpotTorqueFactor` (0x2e0) | 0.333333 | `Transmission.final_drive` **8.4** (medium/Bavarium tanks; donor car **3.91**) | torque-to-ground scales with the ratio; BmAK reduces torque to ⅓, so the car's 3.91 / 3 = **1.30** | **either 1.30 (BmAK's ⅓ applied to the donor ratio) or 8.4 (the tank's ratio)** — the two answer different questions and only one car can hold one value: **8.4 on the battle entity**, 1.30 rejected because a 1.30 ratio is below every shipped land car's gearing band in practice | decoded values, derived arithmetic |
| 5 | `TurningModeMaxSpeed` (0x2c4) | 600 cm/s | `CustomLandGlobal.drift.min_speed_to_drift_kmph` **10** (donor 10; fleet 0..60) | 600 cm/s × 0.036 = **21.6 km/h** | **22** (21.6 rounded into an integer km/h member) on the drift gate; the tanks ship 10, so 22 is inside the fleet range | decoded + derived conversion |
| 6 | `BattleModeStopAndTurnAngleStationary` (0x2f8) | 30° | `CustomLandGlobal.drift.max_drift_angle_deg` **45** (medium/Bavarium/small tanks; APC 25; donor 45) | degrees → degrees, **1:1** | **30** — BmAK's own angle, inside the fleet's 20..60 | decoded |
| 7 | `TransformationTurnTorqueFactor` / `…DecelTorqueFactor` (0x390/0x394) | 3000 / 24000 | **none** — no transformation torque member; the tanks carry no such pair | — | **none** — this is the mode-switch build's problem (second entity), not a pivot value | decoded absence |

**The write set that survives:** `drift.min_speed_to_drift_kmph` **22**, `drift.max_drift_angle_deg`
**30**, `countersteer_speed_factor` **2** (no change), `final_drive` **8.4** on the battle entity,
`wheels_friction_type` **2** optionally. Everything else is "no member".

### 3.1 A contradiction to settle before any byte is written

Two project records disagree on three BmAK members, and this plan must not pick silently:

| member | `MODES.md` (per-package archetype values) | `T-MD14b` (from `DRIVE_MODES.md`) |
|---|---|---|
| front / rear turn-on-spot factor | **0.8 / −0.8** (0x1c8/0x1cc, all four packages) | **0.6 / −0.5** |
| `BattleModeSteerAngleFactor` | **1** (0x300, serialised) | **2.5** |
| `BattleModeLatSlipScale` / `LongSlipScale` | **0.75 / 1.25** | **4 / 10** |

`MODES.md` is generated from the archetype tag stream and reports the value in each of the four
BmAK packages; `T-MD14b` quotes the SDK-side decode. **Settling file:** re-read `DRIVE_MODES.md`'s
rows against the offsets in `MODES.md` (0x1c8, 0x1cc, 0x300, 0x2d4, 0x2d8) — one of the two is
reading a different class layout. Until then this plan's arithmetic uses `MODES.md` because it is
per-package and serialised, and nothing in §3 depends on the slip scales. Note that neither
record's steering-angle factor changes the write set: the donor already ships 35/15, which is what
BmAK's factor of 1 asks for if `MODES.md` is right; if 2.5 is right, the battle entity's angles would
be 35×2.5 / 15×2.5 → 87.5/37.5, above the fleet's 45/35 maximum — impossible, which is itself
evidence for `MODES.md`.

## 4. What is missing on a four-wheeled car, and the closest JC3 mechanism

**Missing (decoded):** a tank turns by driving its two tracks in opposite directions. JC3 has no
track: one `Transmission` (one `final_drive`) and two `Tire` modules, front and rear axle
(`DRIVE_CARRIERS.md` §0/§4). There is no per-wheel or per-axle torque member anywhere (`0` matches
in the per-wheel/differential scan), no `CTrackVehicle` class (12/12 tanks are `CCar`), and no
pivot/neutral-turn member in the vocabulary (`TANKTURN.md` §4). So the Batmobile cannot counter-rotate
axles; it can only **yaw its body with torque while the wheels slip**.

**Closest mechanisms, ranked:**

| rank | mechanism | member / file | why it is the closest | evidence |
|---|---|---|---|---|
| 1 | **drift yaw-torque block** | `CustomLandGlobal.drift.constant_drift_torque` (donor **0**, fleet 0..20000), `max_drift_torque` (donor 5000, 0..35000), `min_speed_to_drift_kmph` (donor 10; **0 ships on 4 builds, 1 chassis**) | the only place in a land car where the body is rotated by torque instead of a front wheel angle | `DRIVE_CARRIERS.md` §3.1 |
| 2 | **per-axle grip asymmetry** | `LandGlobal.front_wheels.arcade_friction_multiplier` (donor 1, 0.8..4.4) / `rear_wheels.…` (donor 1, 1..6) | the only per-axle axis the fleet has; rear stiffer than front on 108 builds, **never lower** — so "rear looser" is the one configuration no shipped car uses and must be tested | `DRIVE_CARRIERS.md` §3.2 |
| 3 | **handbrake counter-steer torque** | `drift.counter_steer_torque_handbrake` (donor **30000**, fleet 0..100000) | a yaw torque applied while the rear axle is locked — the nearest thing to "both ends pull opposite ways" | `DRIVE_CARRIERS.md` §6.1 |
| 4 | tank gearing | `Transmission.final_drive` **8.4** | low gearing = torque at the wheels, which is the *effect* a pivot needs even though it is not a pivot | `TANKTURN.json` `table.chassis` |

**Build edit (B1):** on the Batmobile's own
`Builds/test-0NN/aaf/editor/entities/jc_vehicles/01_land/<chassis>/modules/default/<chassis>_custom_land_global.vmodc`:
`drift.min_speed_to_drift_kmph` 10 → **22**, `drift.max_drift_angle_deg` 45 → **30**,
`drift.constant_drift_torque` 0 → **20000** (fleet maximum, a shipped value), and
`drift.counter_steer_torque_handbrake` 30000 → **60000** (mid of 0..100000).
**Build edit (B2):** `<chassis>_land_global.vmodc`: `wheels_friction_type` → **2** and
`rear_wheels.arcade_friction_multiplier` set **below** the front's (the untested direction), only if
B1's pilot card shows no rotation.
**Build edit (B3):** on the battle entity only, `<chassis>_transmission.vmodc` `final_drive` 3.91 →
**8.4** — this is the tank's ratio and it belongs to the second-entity build, because one car cannot
have both a 3.91 and an 8.4 ratio.
**Revert:** restore the three module files from the donor copies in `Builds/test-091/aaf/.../modules/default/`,
rebuild, reinstall.

## 5. UNKNOWNs

| # | unknown | settler |
|---|---|---|
| U1 | whether a JC3 car yaws at 0 km/h under `drift` torque at all | the land-vehicle torque solver in `JustCause3.exe`; the drift path is slip-angle driven (`DRIVE_CARRIERS.md` §3.1) |
| U2 | whether the shipped tanks pivot in game | runtime; `TANKTURN.md` §6 says no data value distinguishes a pivot-capable vehicle |
| U3 | the pivot's rate and the native key that decides it | `TANKTURN.md` §6 — not in any decoded member |
| U4 | which of `MODES.md` / `DRIVE_MODES.md` reads the 0x1c8 pair correctly | the two files' rows re-read at the same offsets (§3.1) |
| U5 | whether a drift-gate member can *disable* turning above a speed (BmAK's cap is a maximum, the member is a minimum) | `CustomLandGlobal` member list — no maximum-speed gate exists; the cap must be approximated by the drift gate's lower bound |
| U6 | whether `wheels_friction_type` 2 means anything for a wheeled car (enum 0/1/2 undecoded) | `TANKTURN.md` §7 — the enum's labels are not decoded |

## 6. Pilot card — the on-the-spot turn

*In battle mode, stopped (0 km/h) on flat tarmac, hold the stick fully left for 2 s: the car's heading changes ≥ 90° within 2.0 s, its ground position moves ≤ 3 m over those 2 s, and its speed never exceeds 5 km/h; repeat to the right and get ≥ 90° within 2.0 s. Pass band: 2 of 2 directions inside all three limits — ≥ 90° of yaw, ≤ 3 m of drift, ≤ 5 km/h — otherwise the pivot is a named omission and the move stays on the second-entity route.*

## 7. Change record

1. **Intended change:** add one plan that lines BmAK's turn-on-the-spot members up against the JC3
   tank values in `TANKTURN.json`, gives the conversion and the number to write for each, states what
   a four-wheeled car cannot carry, names the closest split mechanism and the build edit, and flags
   the `MODES.md` / `DRIVE_MODES.md` contradiction rather than choosing silently.
2. **File:** `tmp/freebuff/reports/tank-pivot-values-for-battle-mode-turn-plan.md` — the brief names it;
   no file in `Research/`, `Working/`, `Builds/` or the game install is modified.
3. **Revert:** delete this file. Nothing else changed; no game launched, no build packed, no git.

**Limits.** Static only. Three of the seven members have no receiver and are recorded as "none"
rather than filled with a plausible tank number; the one conversion that is pure arithmetic
(600 cm/s → 21.6 km/h) is shown with its factor; the pivot itself remains unproven until the card
is run.
