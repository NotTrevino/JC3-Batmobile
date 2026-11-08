# Mode switching in JC3 — every runtime-switching vehicle, and whether it can carry BmAK's two modes

**Rows:** T-MD5 (battle-mode top-speed curve), T-MD6 (turning-mode speed cap), T-MD7 (steering
factors), T-MD8 (turn on the spot), T-MD13 (transformation stance) — all `out`, all `MOD-2`, all
hinged on D-2's resolution to **one hybrid car**.

**Answer:** **no JC3 vehicle switches its handling at runtime.** Every handling member in the
vocabulary is a single static value per module instance; there is no mode table, no selector and no
per-mode curve. What *does* switch at runtime is geometry (a hinged part's angle, driven by an
exposed `*_T` variable), a part's damage/death mesh, and — the only handling-shaped thing — the
**arcade boost state**, which multiplies torque, grip and top speed *while the boost is on*. The
closest system is therefore the `arcade.nitro_boost` state block over `LandGlobal`, plus
`all_hinged_part_properties` for the pose. That pattern can carry a **temporary** handling change and
a **visual** stance, but not a selectable second mode: the gap the build must fill is a selector and a
second value set, and the only JC3-native way to hold both sets is **two entity variants of one
chassis**.

Nothing was tuned, no row was edited, no build was written. Revert = delete this file.

Labels: **decoded** = read at the file/member named; **derived** = arithmetic/rule over decoded
inputs; **UNKNOWN** = searched and absent, with where it would be found.

---

## 1. What BmAK's two modes actually change (the target)

From `Research/BatmobileGrab/MODES.md` (generated from `BMSDK_OFFSETS.json`, `objects.jsonl`,
`OFFSETS.json`):

| family | declared | serialised | what a mode switch needs to change |
|---|---:|---:|---|
| `BattleMode*` | 42 | 15 | top speed, steering, throttle split, engine braking, upright torque, slope factor |
| `TurnOnSpot*` | 4 | 3 | front/rear torque factors (0.8 / −0.8), engine-braking factor 2 |
| `Transformation*` | 9 | 4 | turn torque 3000 / decel 24000, rotation rotator, **`TransformationAnimNode`** (not serialised), turn-on-spot speed |
| `TurningModeMaxSpeed` | 1 | 1 | **600 cm/s = 21.6 km/h** cap |
| `ArmourModeDamageReduction` | 1 | 1 | 0 shipped (damage, not handling) |

The five ledger rows pick five of these: the battle top-speed curve (`BattleModeVSpeedCurve`,
0x218), the 21.6 km/h turning cap (0x2c4), the steering factors (0x2cc/0x300/0x320), turn-on-the-spot
(0x1c8/0x1cc/0x1d0 + 0x2e0), and the stance (`TransformationRotation` 0x384 + `TransformationAnimNode`
0x354, the latter not serialised anywhere).

**All five need the same thing JC3 does not have: a state that swaps a value set at runtime.**

---

## 2. Every runtime-switching vehicle behaviour found in JC3

Searched: the 52-module / 1,421-path vocabulary (`VOCABULARY.md`, member names containing
mode/state/transform/deploy/retract/tilt/switch/shield/fold/extend), the 66 part behaviours
(`FEATURE_CENSUS.md`), the `vehicle_common` part-property tables, the entity class census, and the
`*_signature_*` / `_military_01` / `_rebel_01` entity variants.

### 2.1 Hinged parts driven by an exposed variable — **the real switch mechanism**

`VehicleCommon` carries `all_hinged_part_properties` (25 rows). Each row is
`part name → driving variable`, and the other members are `lod` and `use_target_position_as_angle`
(`FEATURE_CENSUS.md`, "vehicle_common behaviour -> variable"):

| part behaviour | driving variable | chassis | what moves |
|---|---|---:|---|
| `LandingGear` | `landing_gears_T` | 7 (25 entities, 114 parts) | gear down/up |
| `LandingGearHatch` | `hatches_T` | 5 (76 parts) | hatch doors |
| `AirBrake` | `air_brakes_T` | 1 (`v4602_plane_urga_fighterbomber`, 3 parts) | air brake open/closed |
| `Flaps` | `flaps_T` | 8 (202 parts) | flaps |
| `Aileron` (L/R) | `steering_roll` / `_inverted` | 6 | roll surface |
| `Elevator` | `steering_pitch` | 6 | pitch surface |
| `Rudder` | `steering_yaw` | 7 | yaw surface |
| `SteeringWheel` / `BoatEngine` | `steering_turn` | 9 / 8 | wheel / outboard |
| `TurretDoor` | (door table, no driving variable) | **2** (6 parts, 6 entities) | turret hatch |
| `MissileHatch` | (door table, no driving variable) | **1** (`v5603_train_urga_monorailmissilecar`, 16 parts) | missile bay |

`all_rotating_part_properties` is the same shape: `MainRotor ← main_rotor_rpm`,
`TailRotor ← tail_rotor_rpm`, `Propeller ← propeller_rpm`, `GatlingGun ← weapon_rpm`,
`RadarFast/Slow ← radar_*_rpm`, `Rotor/LeftRotor/RightRotor/Outer*Rotor ← rotor_rpm`.

`ExtendedExposedVariables` is the module that can define such variables from expressions — and it is
almost unused: **2 expression strings in the whole fleet**, both for a speed-ramp effect:

```
speed_rom_intensity = 1 - ( speed_rom_time_remaining / speed_rom_total_time )
speed_rom_threshold = speed_ms / speed_rom_speed_threshold
```

**Derived:** the switch is a *part transform*, driven by a variable the sim or native code writes. No
hinged-part row names a handling member, and no driving variable in the fleet is a handling value.

### 2.2 The Bavarium shield — a part behaviour, not a mode

`BavariumShield` is a part behaviour: **26 parts, 14 entities, 4 chassis** (`FEATURE_CENSUS.md`).
The named chassis is `v0202_car_capstone_bavariumtank` (three entities: `debug`, `military_01`,
`rebel_01` — `FORCEPULSE.json`, `FLEET.md` rows 7-9). It is a `CPartProp` with a part behaviour and a
physics component; its role is damage (T-WP13 already found the shield is a prop, not a damage
source). **No handling member is attached to it**: the tank's `LandGlobal`/`CustomLandGlobal` values
are the same while the shield is up or down.

### 2.3 Aircraft that "tilt" — lean, not a mode

- `DriverLean` (23 aircraft): `righting_torque` 1500..4000, `leaning_torque` 2000..8000 — a
  continuous bank/lean controller, no state.
- `Fins`: `fins[].effective_in_air` is **0 in 200/200** rows; `effective_in_water` is 0..1. A
  per-medium enable, and the only boolean-shaped handling member — but it never enables in air, so no
  aircraft in the fleet has an air-only fin state.
- `HelicopterAI.Limit_Speed_Hover` (20..60): a hover speed, not a hover mode; the helicopter tilts
  because the physics pushes it, not because a state flipped.
- `AirplaneAI.Limit_Pitch_Yaw_Switch` (−1..0.82): a pitch/yaw coupling limit, not a switch.

### 2.4 Turbo jump and the boost blocks — the only handling that changes at runtime

`CustomLandGlobal` (the car's own module, decoded values):

| member | `nitro_boost` | `nitro_boost_upgraded` | `heat_boost` |
|---|---:|---:|---:|
| `push_force` | 15000 | 20000 | **0.0** |
| `torque_multiplier` | 2.0 | 2.0 | 2.0 |
| `grip_multiplier` | 1.0 | 4.26 | 4.26 |
| `extra_top_speed` | 43.2 | 100.92 | 100.92 |
| `boost_blend_time` | 0.2 | 0.2 | **0.0** |

`arcade.turbo_jump`: `f_multiplier` 15, `r_multiplier` 12, `punch_delay_time` 0.1,
`punch_speed_kph` 50, `top_speed_kph` 200, `top_speed_jump_multiplier` 2.0 (and an `_upgraded` set at
30 / 25 / 0.1 / 80 / 200 / 2.0).

**This is a genuine runtime handling change:** while the boost state is on, torque ×2, grip ×1 or
×4.26 and top speed +43.2 or +100.92 km/h apply, blended in over 0.2 s. It is *time- and
input-bounded* (held boost), not a selectable mode, and it multiplies the base value rather than
loading a second one.

### 2.5 Entity variants — JC3's answer to "the same vehicle in another state"

The fleet ships the same chassis as **separate entities**, not as a runtime mode:

| chassis | variants | evidence |
|---|---|---|
| `v2604_helicopter_urga_advancedassault` | `_debug`, `_military_01`-class, **`_signature_shielded`**, `_signature_shielded_di_ravello` | `ENTITIES.md`, `FORCEPULSE.json` |
| `v0202_car_capstone_bavariumtank` | `_debug`, `_military_01`, `_rebel_01` | `FLEET.md` rows 7-9 |
| every armed chassis | `_military_01` / `_rebel_01` / `_civilian_01` | `FEATURE_CENSUS.md` |

**Derived:** when JC3 needs a vehicle in a different configuration, it ships another `.ee`. There is
no button that converts one into the other, and no entity-level member that selects a variant.

### 2.6 Part-state swaps (damage, not mode)

`VehicleParts.parts[]` carries `model_swap` (string, **one fleet value, 0..0 in the 100 rows decoded**),
`meshswap_parts_when_broken`, `always_mesh_swap_on_death`, `appears_on_death`,
`disappears_when_broken`, `hide_parts_when_broken`. These fire on **damage and death**; the only
"state" they express is broken / intact.

### 2.7 What is absent

| searched | result |
|---|---|
| module members named mode/stance/transform/state/deploy/retract/tilt/switch/toggle | **0 handling members**; the 42 hits are deform points, damage armour, RPM resistances, part names and light modes |
| a module named `*Mode*` / `*Transform*` | **none** in the 52 types |
| a per-mode value table (array of handling structs) | **none** |
| a selector member (bool/enum choosing a handling set) | **none** |
| `Fins.effective_in_air` = 1 anywhere | **0 of 200** |
| `ExtendedExposedVariables` expressions beyond the speed-ramp pair | **0** |

---

## 3. Can the pattern carry BmAK's pursuit and battle modes?

| JC3 pattern | top speed | 21.6 km/h cap | steering factors | turn on the spot | stance | verdict |
|---|---|---|---|---|---|---|
| **boost state** (`nitro_boost*`) | **partial** (+43.2 / +100.92 km/h, `extra_top_speed`) | no | partial (torque/grip multipliers, not steering angle) | no | no | carries a *temporary* handling change only |
| **hinged part + `*_T` variable** | no | no | no | no | **yes** (pose, angle set by the variable) | stance only |
| **entity variant** (`_signature_shielded` pattern) | **yes** (its own module values) | **yes** (own `TurningModeMaxSpeed`) | **yes** (own curve) | **yes-ish** (own torque factors; rotation at rest still unproven) | **yes** (own parts/pose) | **carries all five — as a different entity** |
| **BavariumShield part** | no | no | no | no | no | damage only |
| **part damage/death swap** | no | no | no | no | no | broken/intact only |

**Verdict:** no single in-place pattern carries the two modes. The **entity-variant pattern is the
only one that carries all five rows**, because it is the only one where a second complete set of
handling values exists; but it carries them as two vehicles, not as a switch. The **boost state** is
the only in-place runtime handling change and it carries roughly a third of one row.

---

## 4. The closest system, named

> **Closest runtime-switching vehicle behaviour:** the **arcade boost state** — a named block of
> handling multipliers (`torque_multiplier`, `grip_multiplier`, `extra_top_speed`,
> `boost_blend_time`) applied over the base `LandGlobal`/`CustomLandGlobal` values while a state is
> active. It is the fleet's only decoded case of handling members taking a different value at
> runtime, and it already ships three variants of itself (`nitro_boost`,
> `nitro_boost_upgraded`, `heat_boost`).
>
> **Closest stance carrier:** the **hinged-part table** — `all_hinged_part_properties` maps a part to
> a driving variable (`landing_gears_T`, `air_brakes_T`, `hatches_T`), which is how a JC3 vehicle
> visibly changes shape. It gives BmAK's stance pose, with no animation state behind it.

---

## 5. The gap the build must fill

BmAK's mode switch needs two things JC3 separates: **(a) a selector** and **(b) a second value set**.
JC3 has neither in one place — the selector analogue is an input held for a timed state, and the
second value set only exists on another entity.

Three candidate builds, cheapest first, with what each buys:

### Option A — two entity variants of the one hybrid chassis (data-only, carries all five)

Duplicate the Batmobile's `.ee` into `batmobile_pursuit.ee` and `batmobile_battle.ee`, with the
battle copy's modules carrying the battle values: `TurningModeMaxSpeed` equivalent (the car's
`LandGlobal` speed cap set to 21.6 km/h for the turning mode), the battle steering curve, the
turn-on-spot torque block, and the stance parts (hinged part angles for the deployed pose).
**Switch:** the entity swap itself — the same mechanism the fleet already uses for
`_signature_shielded` / `_military_01`. Nothing in the files selects a variant at runtime, so the
swap needs a game-side call (UNKNOWN, §7 U1).
**Evidence:** decoded variant pattern; values decoded; the swap trigger is the gap.
**Cost:** no runtime blend, two entities to maintain, save/streaming behaviour unproven.

### Option B — repurpose `heat_boost` as the battle-mode multiplier state (in place, partial)

`heat_boost` ships as an unused duplicate of `nitro_boost_upgraded` (`push_force` 0, `blend 0`). Fill
it with the battle-mode ratios derived from the BmAK pairs and drive it from the battle input:

| member | from | to | derivation |
|---|---:|---:|---|
| `arcade.heat_boost.push_force` | 0 | **15000** | copy `nitro_boost.push_force` so the state has a push |
| `arcade.heat_boost.torque_multiplier` | 2.0 | **2.0** | already at the battle/base ratio if `BattleModeDriveForceFactor` 500 is read as a gain (keep) |
| `arcade.heat_boost.grip_multiplier` | 4.26 | **4.26** | keep; it is the only shipped "more grip" value |
| `arcade.heat_boost.extra_top_speed` | 100.92 | **100.92** | keep; the battle top-speed delta has no shipped number (`BattleModeMaxSpeed` not serialised) |
| `arcade.heat_boost.boost_blend_time` | 0.0 | **0.2** | copy `nitro_boost`'s blend so the change is a ramp, not a step |

**Buys:** a held state that changes torque, grip and top speed in place, blended over 0.2 s.
**Does not buy:** the 21.6 km/h cap, a steering-angle set, turn-on-the-spot, or a persistent stance.
**Evidence:** decoded members, decoded values; the mapping from BmAK's battle numbers is **partial and
declared** (only the multipliers have a counterpart).

### Option C — code bridge: a native selector (out of reach)

No decoded selector exists in any module, entity graph or `.physicsc`. A true in-place mode switch
would need the vehicle sim to read a state and pick a value set — i.e. new native code or a memory
hook. **UNKNOWN, not planned.**

**Recommendation:** ship **A** for the two modes' *look and numbers* and **B** only as the in-place
approximation if a single entity is mandatory. D-2's hybrid car cannot have both modes in one
entity's data; that is a structural fact, not a tuning choice.

---

## 6. Per-row consequence (what each row can now say)

| row | BmAK need | carrier in this report | status the row can claim |
|---|---|---|---|
| T-MD5 | battle top-speed curve | entity variant holding its own `extra_top_speed`/cap | **buildable as a variant**, not as a curve (JC3 has no speed→factor curve on a car except `Aerodynamics`/`Fins` splines) |
| T-MD6 | 21.6 km/h turning cap | variant's own speed cap; `LandGlobal` has one value per entity | **buildable as a variant value**, not as a second in-place cap |
| T-MD7 | battle steering factors | variant's `land_steering` values, or boost torque/grip multipliers (partial) | **partial**; no per-mode steering table |
| T-MD8 | turn on the spot | `drift` torque at 0 km/h (UNKNOWN on the drift carrier's own gate, see the air-control plan) + variant torque factors | **not carried by any switch**; still a torque-at-rest question |
| T-MD13 | transformation stance | hinged part + driving variable (`landing_gears_T` pattern), `TransformationAnimNode` has no JC3 equivalent (no animation-node member) | **pose yes, animated transition no** — the row's existing `out` wording stays true |

---

## 7. UNKNOWNs, each with what would settle it

| # | unknown | why it matters | settler |
|---|---|---|---|
| U1 | can a vehicle entity be swapped at runtime for its variant (no game-side call decoded)? | Option A's switch | `JustCause3.exe` entity/vehicle streaming consumer (not decoded); or a live probe (test ban) |
| U2 | does any native code key off `ExtendedExposedVariables` to change handling? | the only in-data path from an expression to a value | the `ExtendedExposedVariables` consumer in the exe (not decoded) |
| U3 | is `heat_boost` reachable at all (it has `push_force` 0)? | Option B is dead if nothing triggers it | the boost-state consumer in the exe; the vehicle's action map |
| U4 | does `TurretDoor` open on a handling event or only on a weapon state? | whether a hatch can be the mode's visual tell | `PARTS_TABLE` driving variable is `-` for `TurretDoor`; the part consumer in the exe |
| U5 | is there any animation-node member on a JC3 car (BmAK's `TransformationAnimNode` analogue)? | T-MD13's animated transition | `VOCABULARY.md` has no anim module; the `LandAudio`/`VehicleParts` modules carry no node ref; exe-side animation system |
| U6 | `TransformationRotation` (0x384) is not serialised — what pose did BmAK ship? | the stance angle to copy | `BmGame.upk` CDO `chase08_cdo.py`; if absent, the `BatmanAK.exe` store site |

---

## 8. Sources

- `Research/JC3Grab/VOCABULARY.md` — 52 module types; `CustomLandGlobal` (boost/turbo-jump blocks),
  `Fins`, `VehicleParts`, `ExtendedExposedVariables`, `VehicleMisc`, `LandGlobal`, `DriverLean`.
- `Research/JC3Grab/FEATURE_CENSUS.md` — part-behaviour census (66 behaviours, incl.
  `BavariumShield` 26/14/4, `TurretDoor` 6/6/2, `LandingGear` 114/25/7, `MissileHatch` 16/1) and the
  `vehicle_common` part-property tables with their **driving variables**.
- `Research/JC3Grab/ENTITIES.md`, `FORCEPULSE.json`, `Research/JC3Grab/FLEET.md` — the entity-variant
  pattern (`_signature_shielded`, `_military_01`/`_rebel_01`, the three bavarium-tank entities) and
  the shield meshes.
- `Research/BatmobileGrab/MODES.md` — 42 `BattleMode*` declared / 15 serialised, `TurningModeMaxSpeed`
  600 cm/s, `Transformation*`, the 61 unserialised fields.
- `Working/Translation/T_ROWS.jsonl` (`T-MD5..8`, `T-MD13`) — the `out` wording this report tests.
- `tmp/freebuff/reports/carrier-air-control.md`, `carrier-ram-and-dodge.md` — the drift torque's
  at-rest behaviour and the absence of contact triggers, both referenced in §6.
