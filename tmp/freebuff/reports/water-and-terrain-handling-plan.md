# Off the road — water, grass, sand and slopes: BmAK's handling members and the JC3 values

**STATUS: done (plan, read-only probe).** BmAK does **not** have grass, sand, snow or asphalt as handling
surfaces. `SVehicleWheel.EDrivableSurfaceMaterialType` has exactly six values — **Default 0, Mud 1, FearGas 2,
Wood 3, Water 4, Pollen 5** — so grass and sand share *Default* with tarmac, and the only off-road grip change
BmAK can make is the **tyre type** (`ETyreType`, 17 values, `CurDSMT` at wheel offset **592**) selected by
`RVehicleSimBatmobile.ForceUpdateTyreFriction`. Water is the one terrain with a real module on both sides
(`SVehicle.bVehicleOnWater` + `BatmobileHitWater` / `BatmobileAboutToHitWater` + `SpawnWaterImpactEffect`), and
slopes are carried by **`FVehicleTransmission.SlopeTorqueScale`** and **`BattleModeSlopeFactor`**. JC3 has the
mirror-image gaps: a complete water block (`WaterInteraction`, 52 members), a **3-value**
`wheels_friction_type` selector with no surface names, and **no slope-torque member at all** — slope behaviour
is an emergent result of `gravity_multiplier_grounded`, suspension strength and `max_tilt_to_land_deg`.

Where a number is not in the files it says **UNKNOWN**; no handling value below is invented.

---

## 1. BmAK: what the members are

### 1.1 The surface enum — six values, and grass/sand are not among them

`Working/vendor/BmSDK/SVehicleWheel.g.cs:150-160`:

| value | name | what BmAK does with it |
|---:|---|---|
| 0 | **`DSMT_Default`** | tarmac, **grass**, **sand**, dirt — all one handling class |
| 1 | `DSMT_Mud` | grip + mud material layer (`MAT_Mud`, `Batmobile_Mud_FCT`) |
| 2 | `DSMT_FearGas` | fear-gas burnout effects |
| 3 | `DSMT_Wood` | wood-collision effects (`Impacts.Batmobile_Wheels_Wood_Collision`) |
| 4 | **`DSMT_Water`** | the water plane; `SVehicle.bVehicleOnWater` flips here |
| 5 | `DSMT_Pollen` | pollen kick-up (`Particles.Batmobile_Pollen_KickUP`) |
| 6 | `DSMT_MAX` | sentinel |

**This is the answer to "how does it behave on grass and sand":** the same as on tarmac, because the surface
enum has no entry for them. What changes is **visual only** — the mud/pollen/dust layers and the tyre-smoke
particles — not the friction class. Any plan claiming a BmAK grass or sand grip value would be inventing an
enum member that does not exist.

### 1.2 The tyre type — 17 entries, the actual grip selector

`SVehicleWheel.g.cs:125-147` (`ETyreType`), with the four wheel slots that select it:

| slot | offset | type | purpose |
|---|---:|---|---|
| `CurDSMT` | **592** | `EDrivableSurfaceMaterialType` | current surface under this wheel |
| `TyreType` | **595** | `ETyreType` | normal driving tyre |
| `HandbrakeTyreType` | **596** | `ETyreType` | handbrake |
| `WheelspinTyreType` | **597** | `ETyreType` | wheelspin |
| `DriftTyreType` | 598 | `ETyreType` | drift |

| value | `ETyreType` | comment |
|---:|---|---|
| 0 | `ETyreType_ZeroFriction` | the "no grip" state (ice-like / airborne) |
| 1 | `ETyreType_Batmobile` | normal |
| 2 | `ETyreType_BatmobileBattleMode` | battle mode |
| 3 / 4 | `…HandbrakeFront` / `…HandbrakeRear` | handbrake, front/rear |
| 5 / 6 | `…DriftFront` / `…DriftRear` | drift |
| 7 / 8 | `…WheelspinFront` / `…WheelspinRear` | wheelspin |
| 9 | `…WheelspinBoost` | boost wheelspin |
| 10 | `…TwoWheels` | two-wheel strafe |
| 11 / 12 | `…BrakeFront` / `…BrakeRear` | braking |
| 13 / 14 | `Car` / `Tank` | generic classes |
| 15 / 16 | `NpcWheelspin` / `NpcTwoWheels` | AI |

**The surface does not pick a friction number directly** — it picks a `TyreType` via
`RVehicleSimBatmobile.ForceUpdateTyreFriction(SVehicle Vehicle)` (`RVehicleSimBatmobile.g.cs:117`), and the
tyre type indexes the friction table. Two debug setters expose the table by handle:
`RVehicleBatmobileBase.DebugSetTireFrictionMod(ETyreType, float)` (`:482`) and
`DebugSetTireLatSlipMod(ETyreType, float)` (`:462`) — proof the table is per-`ETyreType`, not per-surface.

### 1.3 Water members on the car

| member | class / offset | what it does |
|---|---|---|
| `bVehicleOnWater` | `SVehicle` bool, **1040** (`SVehicle.g.cs:1040-1042`) | the in-water flag |
| `BatmobileHitWater` | `RVehicleBatmobileBase` bool, **4878** | water entry already happened |
| `BatmobileAboutToHitWater` | `RVehicleBatmobileBase` bool, **4896** | pre-entry state |
| `SpawnWaterImpactEffect(HitLocation, PlayerCamera)` | `RVehicleBatmobileBase` (`:2347`) | the splash |
| `StopWaterImpactEffect()` | `RVehicleBatmobileBase` (`:2336`) | splash stop |
| `BatmobileSnapToGround(pos, rot, archetype)` | `RVehicleBatmobileBase` (`:2457`) | re-seat after a jump/entry |
| `DrawGraphsAndPrintTireSurfaceTypes(HUD, YL, YPos)` | `SVehicle` (`:494`) | **debug readout of the per-wheel surface** — the cheapest way to observe §1.1 in game |

`SVehicleWheel` also carries **six `WheelSkidMarkSystem` slots** (offset 236) and six
`WheelSkidMarkComp` (396) — already covered in `surface-skids-and-tracks-plan.md`; the skid gate is
`SquealThreshold` 0.2 / `SquealLatThreshold` 0.2, `DefaultTyreUpdates` 16.5.

### 1.4 Slope members

| member | class / offset | meaning |
|---|---|---|
| `FVehicleTransmission.SlopeTorqueScale` | float, **64** in the 112-byte struct (`RVehicleSimBatmobile.g.cs:335-337`) | torque scale applied on a gradient |
| `RVehicleSimBatmobile.BattleModeSlopeFactor` | float, **1216** (`:1583-1585`) | how much slope matters in battle mode |
| `FVehicleTransmission.Friction` | float, **12** | drivetrain friction |
| `FVehicleTransmission.Drag` / `DragNoLoad` | **16** / **20** | load drag |
| `RVehicleSimBatmobile.AirControlInterpTime` / `AirControlTimeInAir` | **1208** / **1212** | the airborne blend around a crest |
| `RVehicleBatmobileBase.BatmobileSnapToGround` | function | re-grounds after a crest |

**Numeric defaults for `SlopeTorqueScale`, `BattleModeSlopeFactor`, `Friction`, `Drag`, `DragNoLoad` are
UNKNOWN** — the decoded CDO delta table (`Research/BatmobileGrab/CLASS_DEFAULTS.md`) contains only
`DefaultTyreUpdates` 16.5, `SquealThreshold` 0.2, `SquealLatThreshold` 0.2 for the terrain-relevant members
(`:164-165, :349`). The names and offsets are proven; the values are not.

---

## 2. JC3: the members that exist, and the ones that do not

All values below are the donor `v0300_car_kensington_sportsmuscle` entity, read out of
`E:/Modding/_gamedata/JC3grab/entities/v0300_…_civilian_01.ee.json` this pass.

### 2.1 Friction and grip

| member | donor value | fleet range | source |
|---|---:|---|---|
| `wheels_friction_type` (`LandGlobal`) | **0** | **0 … 2**, median 0, n=271 | entity grab; `VOCABULARY.md:873` |
| `front_wheels.arcade_friction_multiplier` | **1.0** | 0.8 … 5 (med 2.8) | `VOCABULARY.md:852` |
| `rear_wheels.arcade_friction_multiplier` | **1.0** | 1 … 6 (med 3) | `VOCABULARY.md:866` |
| `front_wheels.arcade_drag_multiplier` | 0.1 | — | entity grab |
| `front_wheels.mass` / `rear_wheels.mass` | **25** / **75** (AI set: 75 / 75) | — | entity grab |
| `handbrake_friction_factor` | **1.0** (AI 2.0) | 1 … 10 (med 2) | entity grab; `VOCABULARY.md:388` |
| `front_wheels_damage.broken_wheel_friction_fraction` | 0.5 | 0.5 … 0.75 | `VOCABULARY.md:488` |

`wheels_friction_type` is an **int32 index into three friction tables** (domain 0…2). **The files name none of
the three** — there is no `friction_type_0/1/2` member and no surface keyword anywhere in the 52 module types
(`WATER.md` §9 does the same scan for water; a `grass|sand|snow|asphalt|terrain` scan of `VOCABULARY.md`
returns only `aerodynamic_surfaces`, `wheels_friction_type` and the water members). So JC3, like BmAK, has **no
per-surface grip value to set**; the surface split is in the `.effc` trail family
(`dust_trail_{asphalt,dirt,grass,sand,snow,water}.effc`) and the wheel `rear_*` effects.

### 2.2 Water — the complete block, already on the build

| member | donor | meaning |
|---|---:|---|
| `WaterInteraction.will_sink` | **1** | 189 of 232 sink; the donor is one |
| `Buoyancy.buoyancy` | **2** | lift multiplier |
| `Buoyancy.drag` | 100 | water drag |
| `Buoyancy.radius` / `side_area` / `bottom_area` / `up_velocity_cap` | 0.55 / 1.85 / 3 / 20 | hull approximation |
| `angular_drag_pitch` / `yaw` / `roll` / `roll_at_speed` | 0.05 / 0.05 / 0.05 / 0.05 | rotational drag |
| `angular_drag_ref_speed_kmph` | 50 | reference speed for the above |
| `drag_falloff_power` | 1 | falloff exponent |
| `pressure_drag` / `pressure_drag_2` | 5000 / 20000 | pressure terms |
| `suction_drag` / `suction_drag_2` | 5000 / 20000 | suction terms |
| `depth_full_drag` | 0.1 | depth at which drag is full |
| `add_skin_friction_laminar` / `_turbulent` | **-0.8** / **3** | skin friction |
| `reference_drag_speed_ms` | 20 | reference |
| `anti_penetration_max_accel` / `_multiplier` / `_power` | 15 / 2 / 1 | hull push-out |
| `depth_full_anti_penetration` | 0.1 | push-out depth |
| `planing_vs_forward_speed_ms` | x 0…20, y 0…0.1, 5 points | planing curve |
| `buoyancy_factor_vs_speed_ms` | x 0…20, y 0…1, 2 points (flat 1) | buoyancy vs speed |
| `flat_water_vs_speed_ms` | x 0…30, y 0…1, 3 points (1 → 0.3568 at 30) | flat-water attenuation |
| `part_elements[0]` | 1 hull, `name` **body**, `from_part` **sportsmuscle_body** | the collider the water plane pushes |
| `vehicle_damage.min_water_entry_ms` / `fatal_water_entry_ms` | **10** / **20** | shared, all 232 |
| `vehicle_damage.min_water_entry_floating_ms` / `fatal_…` | **20** / **50** | shared |
| `car_common.engine_shut_down_delay_s` | **30** | cars (5 for every other class) |

Source: entity grab for the module rows; `Research/JC3Grab/WATER.md` §2, §7 for the fleet ranges and the
shared-timer proof (232/232 identical).

### 2.3 Slope and terrain attitude

| member | donor | what it does |
|---|---:|---|
| `vehicle_misc.max_tilt_to_land_deg` | **80** | the angle at which a landing is still a landing |
| `vehicle_misc.max_landing_speed_kmph` | **170** | landing speed cap |
| `vehicle_misc.max_take_off_speed_kmph` | 150 | take-off cap |
| `vehicle_misc.official_top_speed` | 250 | top speed |
| `custom_land_global.gravity_multiplier_grounded` | **1.0** | ground gravity — the slope-load term |
| `…gravity_multiplier_in_air_up` / `_down` | 1.0 / 1.0 | airborne |
| `…takeoff_pitch_damping` | **0.5** | pitch settling over a crest |
| `…linear_damping[0..2]` | 0 / 0 / 0 | body damping |
| `suspension.front.strength` / `rear.strength` | **40** / **35** | spring rate |
| `suspension.front.compression` / `relaxation` | 4 / 7 | damping |
| `suspension.rear.compression` / `relaxation` | 3 / 4 | damping |
| `suspension.front.length` / `rear.length` | 0.25 / 0.25 | travel |
| `…max_velocity_for_damp_clamp` | 1.5 | clamp |
| `…lateral_tire_force_offset` front / rear | **0.10** / **0.05** | lateral force point (the anti-roll behaviour) |
| `…antirollbar_strength` front / rear | 0 / 0 | no ARB |
| `rigid_body.mass` | **975** | 975 units (kg-class) |
| `rigid_body.center_of_mass` | (0, 0.6, 0.65) | low CoM |
| `rigid_body.unit_inertia_yaw` / `_pitch` | 1.8 / 1.5 | yaw/pitch inertia |
| `drift.drift_entry_slip_angle` / `exit` / `max` | **20° / 2° / 45°** | the drift envelope on a loose surface |
| `drift.max_keep_velocity_acceleration_g` | 2 g | how hard a slide can hold speed |
| `arcade.nitro_boost.grip_multiplier` | **2.0** | grip while boosting |

**There is no slope-torque, slope-factor or climb-limit member anywhere in the JC3 fleet.** The keyword scan
over `VOCABULARY.md` for `slope|incline` returns **0 rows**; the only attitude members are
`max_tilt_to_land_deg` and `takeoff_pitch_damping`.

---

## 3. The mapping — what to set for each case

### 3.1 Tarmac / grass / sand (one class on both sides)

| BmAK | JC3 | value |
|---|---|---|
| `DSMT_Default` 0 for tarmac, grass and sand | `wheels_friction_type` 0 | **keep 0** |
| `ETyreType_Batmobile` 1 (normal) | `front/rear arcade_friction_multiplier` 1.0 | **keep 1.0 / 1.0** |
| no per-surface grip | `wheels_friction_type` 0…2 tables, unnamed | **no change** — the three tables cannot be labelled from the files |
| mud surface (1) → mud layer | `dust_trail_dirt.effc`, `rear_dirt.effc` | effect only, already shipped |
| sand surface → **Default** (no BmAK sand class) | `dust_trail_sand.effc`, `rear_sand.effc` | effect only — **this is where JC3 has more surface art than BmAK has handling** |
| grass surface → **Default** | `dust_trail_grass.effc`, `rear_grass.effc` | effect only |

So the "grass and sand" behaviour reproduces by **not changing a number**: both engines drive them on the
default tyre, and the difference is the trail effect. If the port *wants* a grip penalty on grass/sand (a
design choice, not a translation), the only place to express it is a private copy of
`vehicle_common.vmodc`'s `tire_effects` gates combined with the `dust_trail_*` selection — never
`wheels_friction_type`, which has no per-surface meaning in the data.

### 3.2 Water

| BmAK | JC3 | value |
|---|---|---|
| `bVehicleOnWater` flip on `DSMT_Water` | `WaterInteraction.will_sink` | **keep 1** (sinks, like the donor and 189/232) |
| splash on entry | `SpawnWaterImpactEffect` analogue — the fleet's water entry effects | keep donor |
| hull drag in water | `Buoyancy.drag` **100**, `pressure_drag` 5000 / `_2` 20000, `suction_drag` 5000 / `_2` 20000, `depth_full_drag` 0.1 | **keep** |
| skin friction | `add_skin_friction_laminar` **-0.8**, `turbulent` **3** | **keep** |
| push-out | `anti_penetration_max_accel` 15, `_multiplier` 2, `_power` 1, `depth_full_anti_penetration` 0.1 | **keep** |
| planing | `planing_vs_forward_speed_ms` x 0…20 / y 0…0.1 | **keep** |
| engine stalls in water | `car_common.engine_shut_down_delay_s` **30** | **keep** (a private copy only if we want a different delay) |
| death timer | `fatal_water_entry_ms` **20** (floating 50) | **keep**; unit UNKNOWN |

The build is **already correct for water**: `WATER.md` §8 proves the shipped `.ee` carries the donor's
`WaterInteraction` (734 rows, `will_sink` 1, 1 hull element) and `Buoyancy` (10 rows, buoyancy 2, drag 100,
0.55 / 1.85 / 3) byte-for-byte.

### 3.3 Slopes

| BmAK | JC3 | value |
|---|---|---|
| `SlopeTorqueScale` (transmission, offset 64) — **value UNKNOWN** | *no member* | the closest equivalents are the grounded gravity and the spring rates below |
| `BattleModeSlopeFactor` (offset 1216) — **value UNKNOWN** | *no member* | keep battle-mode behaviour driven by `BattleModeMaxSpeed` (1200 cm/s) instead |
| `AirControlInterpTime` / `AirControlTimeInAir` — **values UNKNOWN** | `takeoff_pitch_damping` **0.5** | **set 0.50** |
| suspension travel over crests | `front.strength` **40**, `rear.strength` **35**, compression 4/3, relaxation 7/4, length 0.25 | **keep** |
| slope load | `gravity_multiplier_grounded` **1.0** | **keep 1.0**; raising it is the only lever that makes a slope bite harder, and it is a design choice |
| landing on a slope | `max_tilt_to_land_deg` **80** | **keep 80** |
| low CoM | `rigid_body.mass` 975, CoM y 0.60 | **keep** |

**Slope handling on the JC3 side is emergent.** The car climbs or slides because of mass 975, the 40/35 spring
rates, `max_tilt_to_land_deg` 80 and the tyre friction — not because of a slope scalar. Reproducing BmAK's
slope feel therefore means matching the **spring rate and the pitch damping**, which are the two numbers above
that we can set with confidence; the BmAK factors themselves cannot be translated because their values are not
decoded.

### 3.4 The one place the JC3 side has *more* than BmAK

| surface | BmAK handling class | JC3 handling class | JC3 art |
|---|---|---|---|
| grass | Default | `wheels_friction_type` 0 | `dust_trail_grass.effc` + `rear_grass.effc` |
| sand | Default | 0 | `dust_trail_sand.effc` + `rear_sand.effc` |
| snow | **none** | 0 | `dust_trail_snow.effc` + `rear_snow.effc` |
| gravel | **none** | 0 | `rear_gravel.effc` |
| wood | `DSMT_Wood` 3 | 0 | (effect only) |

BmAK has **no snow and no gravel surface at all**; JC3 ships art for both. That asymmetry belongs in the port
notes: we are not losing anything by leaving `wheels_friction_type` at 0, because neither engine changes grip
by surface name.

---

## 4. Checks run

| check | result |
|---|---|
| surface enum re-read | `SVehicleWheel.g.cs:150-160` — Default, Mud, FearGas, Wood, Water, Pollen (6) |
| tyre enum re-read | `SVehicleWheel.g.cs:125-147` — 17 values, `ZeroFriction` 0 … `NpcTwoWheels` 16 |
| wheel slots | `CurDSMT` 592, `TyreType` 595, `HandbrakeTyreType` 596, `WheelspinTyreType` 597, `DriftTyreType` 598 |
| water fields | `SVehicle.bVehicleOnWater` 1040; `BatmobileHitWater` 4878; `BatmobileAboutToHitWater` 4896; `SpawnWaterImpactEffect` / `StopWaterImpactEffect` |
| slope fields | `FVehicleTransmission.SlopeTorqueScale` 64; `BattleModeSlopeFactor` 1216; `AirControlInterpTime` 1208; `AirControlTimeInAir` 1212 |
| BmAK numeric defaults | only `DefaultTyreUpdates` 16.5, `SquealThreshold` 0.2, `SquealLatThreshold` 0.2 decoded; friction/slope **UNKNOWN** |
| JC3 donor rows dumped | `_land_global`, `_land_global_ai`, `_water_interaction` (734), `_buoyancy`, `_suspension` (49), `_rigid_body` (17), `_vehicle_misc` (33), `_custom_land_global` (61) |
| JC3 surface keywords | `VOCABULARY.md` scan: `wheels_friction_type` 0…2 (med 0, n=271); no grass/sand/snow/slope member; 0 rows for `slope|incline` |
| water fleet facts | `WATER.md`: 189 sink / 8 amphibious / 35 boats; shared timers 10/20, 20/50; `car_common` 30 s |
| build already correct for water | `WATER.md` §8 — `will_sink` 1, buoyancy 2, drag 100, 1 hull element, identical to donor |

---

## 5. Change record (per `AGENTS.md`)

1. **Intended change:** add one report describing BmAK's water/grass/sand/slope handling members and the JC3
   values that reproduce each case.
2. **File:** `tmp/freebuff/reports/water-and-terrain-handling-plan.md` (this file). Correct file because the
   brief names it and every comparable plan lives in `tmp/freebuff/reports/`; no module, entity, build,
   `Research/` table or install is modified.
3. **Revert:** delete this file. Nothing else changed.

---

## 6. UNKNOWNs

| # | UNKNOWN | what settles it |
|---|---|---|
| U-1 | `SlopeTorqueScale`, `BattleModeSlopeFactor`, `FVehicleTransmission.Friction` / `Drag` / `DragNoLoad` defaults | a CDO dump of `RVehicleSimBatmobile`'s transmission struct (the decoded table covers `SVehicle` only) |
| U-2 | which of JC3's three `wheels_friction_type` tables is which | no names in any module; a Q-1 drive test on `wheels_friction_type` 0 vs 1 vs 2 |
| U-3 | whether BmAK grass/sand differ from tarmac at all | `DrawGraphsAndPrintTireSurfaceTypes(HUD, …)` prints the per-wheel `CurDSMT`; drive onto grass and read it — if it stays `DSMT_Default`, §1.1 is confirmed |
| U-4 | the unit of `vehicle_damage.*_water_entry_ms` (10/20) | the field name only; 10 ms cannot be a drown timer, so the mapping must not quote it as seconds |
| U-5 | the metric climb limit on a JC3 slope | needs the tyre friction table (U-2) plus mass 975 — a measurement, not a decode |
| U-6 | whether the BmAK splash/hull behaviour changes grip at `DSMT_Water` or only drag | `ForceUpdateTyreFriction` is native; only a runtime read of the tyre type in water settles it |
