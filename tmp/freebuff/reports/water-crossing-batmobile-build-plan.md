# Water crossing for the Batmobile — members, values, and the two gaps

Sources: `Research/JC3Grab/WATER.md` (288 generated lines, G2-31) and `tmp/freebuff/reports/G2-31.md`.
Every number below cites a `WATER.md` line. Nothing else is used as a value source; where a member or a
number is not in that file, the row says UNKNOWN and names the file that would settle it.

Labels: **decoded** = read at the WATER.md line given; **derived** = a stated rule over decoded lines;
**UNKNOWN** = absent from WATER.md's own scan.

**Answer in one line:** the Batmobile's water behaviour is **already the BmAK behaviour and needs no
edit** — it carries the donor's `WaterInteraction.will_sink` 1 and `Buoyancy` 2 (WATER.md 243-250, 271),
stalls its engine on the car timer 30 s (230) and dies on the fleet-wide `fatal_water_entry_ms` 20 (235)
— and the two things the brief asks about that WATER.md does **not** carry are **splash/wake effects**
and **water sounds**: they are not among the 38 water-related member paths in the whole fleet (254-265),
so they are UNKNOWN here rather than absent from the game. The one real build step is the **hull mesh**:
`part_elements[]` is built from the donor body part `sportsmuscle_body` (275), so a Batmobile body
changes the shape the water plane pushes against.

---

## 1. What the build exposes today

`Builds/test-091/v0300_car_kensington_sportsmuscle_civilian_01.ee` (604 inner files) carries the donor's
two water modules, decoded and compared against the donor cache as **identical** (243-250, 286):

| module | file inside the `.ee` | rows | build value |
|---|---|---|---|
| `WaterInteraction` | `v0300_car_kensington_sportsmuscle_water_interaction.vmodc` | 734 | `will_sink` **1**, 1 hull element (245, 250) |
| `Buoyancy` | `v0300_car_kensington_sportsmuscle_buoyancy.vmodc` | 10 | `buoyancy` **2**, `drag` **100**, `radius` **0.55**, `side_area` **1.85**, `bottom_area` **3**, `up_velocity_cap` **20** (33-38, 245) |

The fleet context that makes those numbers meaningful: **189** entities sink, **8** float without a boat
module, **35** boats float with `BoatBuoyancy` (11-13, 152, 156-167). The donor is one of the 189 (11), and
`will_sink` is the **only** scalar that separates the sinking cars from the eight floaters — the drags are
identical across both groups (130).

## 2. Member-by-member: what carries each behaviour

### 2.1 Buoyancy — `Buoyancy` module (8 member paths, WATER.md §2 lines 29-40)

| member | build | what it does | line | evidence |
|---|---:|---|---|---|
| `buoyancy` | 2 | lift multiplier; **not a switch** — sinking cars carry 0, 0.25, 1.5 or 2 as well (167) | 33 | decoded |
| `drag` | 100 | vertical drag of the float body | 34 | decoded |
| `radius` | 0.55 | float-sphere radius | 35 | decoded |
| `side_area` | 1.85 | area presented sideways | 36 | decoded |
| `bottom_area` | 3 | area presented to the water plane — the closest thing to a "how much water lifts the hull" number | 37 | decoded |
| `up_velocity_cap` | 20 | cap on the upward push | 38 | decoded |
| `buoyancy_modules[]` | present (array) | per-element floats | 39-40 | decoded |

**Derived:** wading is a *hull-geometry* question, not a `buoyancy` question — `buoyancy` 2 is the same
value the floating APC carries (156-167), so the scalar cannot be read as "floats" and must not be tuned
to change wade depth.

### 2.2 Water drag and the water plane — `WaterInteraction` (52 member paths, §2 lines 42-100)

| member | build | role | line |
|---|---:|---|---|
| `part_elements` | 1 element | the hull triangle mesh the water plane pushes against — the **wade-depth carrier** | 43 |
| `will_sink` | 1 | the sink switch | 47 |
| `angular_drag_pitch` | 0.05 | pitch damping once in water | 48 |
| `pressure_drag` | 5000 | bow pressure | 54 |
| `suction_drag` | 5000 | stern suction | 56 |
| `depth_full_drag` | 0.1 | depth at which full drag applies | 58 |
| `anti_penetration_multiplier` | 2 | keeps the hull out of the water plane | 63 |
| `planing_vs_forward_speed_ms.x_max` | 20 | planing curve domain — the only "how fast before the hull lifts" data | 67 |

The build carries the same values as every sinking car in the fleet (130), so a Batmobile that behaves
differently in water can only differ by **editing these or the hull**, not by inheriting another car's
numbers.

### 2.3 Submersion damage and engine cut-out — `VehicleCommon`, one shared file (lines 213-239)

All 232 entities point their `VehicleCommon` at
`editor/entities/jc_vehicles/00_shared/modules/vehicle_common.vmodc` (213). The Batmobile's `.ee` embeds a
copy of that module; the values are:

| member | value | what it is | line |
|---|---:|---|---|
| `vehicle_damage.min_water_entry_ms` | 10 | entry threshold | 237 |
| `vehicle_damage.fatal_water_entry_ms` | 20 | the fatal one | 235 |
| `vehicle_damage.min_water_entry_floating_ms` | 20 | entry threshold, floating hull | 236 |
| `vehicle_damage.fatal_water_entry_floating_ms` | 50 | fatal, floating hull | 234 |
| `car_common.engine_shut_down_delay_s` | **30** | the car's engine cut after water entry | 230 |
| `boat_common.engine_shut_down_delay_s` | 5 | every non-car class | 229 |
| `helicopter_common` / `motorbike_common` / `plane_common` | 5 each | same | 231-233 |
| `all_rotating_part_properties[].number_of_water_collision_sensors` | 5 on index 0; 3 on 1, 6, 7, 8, 10, 11; 0 on 2-5, 9 | how many water sensors each rotating part (wheel, rotor) has | 217-228 |

Two things must be said plainly because the file says them plainly:

* **No vehicle overrides any of these** (239). Changing the Batmobile's drown or stall behaviour means
  shipping a **private copy** of `vehicle_common.vmodc`, which is shared by all 232 entities — a
  fleet-wide change if the path stays shared, a new file if it does not (239).
* **The unit behind `_ms` is UNKNOWN** (239). 10/20 ms cannot be a drown timer, so the number is quoted
  as-is and never as seconds or as damage. Anything that needs "seconds to die in water" is UNKNOWN and
  settles in the water-entry consumer in `JustCause3.exe`.

### 2.4 Splash and wake — **UNKNOWN by absence**

WATER.md's keyword scan over all 232 entities × 52 module types returns **38** member paths mentioning
water/drown/sink/float/dive/submerge/buoyancy, and they are exactly: `WaterInteraction` 17,
`BoatBuoyancy` 9, `HelicopterModel` 5 (flight `dive_*`), `VehicleCommon` 5, `Buoyancy` 3, `Fins` 1
(254-263). There is **no** member named splash, wake, spray, foam, ripple or entry-effect (265).

So a splash or a wake is not authored by any water module. What plausibly carries it is the per-vehicle
effect graph (`SEffects` / `SAttachedEffect` objects, 359 + 5342 across the fleet) driven by the water
collision sensor counts above (217-228). That is **UNKNOWN from WATER.md**; it settles in
`Research/JC3Grab/FX.md` (the effect-table decode) and the donor's `.epe` effect objects — not in the
water data.

### 2.5 Water sounds — **UNKNOWN by absence**

Same scan, same verdict: no sound, no `AkEvent`, no audio member appears among the 38 paths (254-263).
The water sound, if any, is an effect/audio-table row, not a water member; it settles in
`Research/JC3Grab/JC3_AUDIO.md` and the vehicle's `SAttachedEffect` roles.

---

## 3. The two depth questions, answered honestly

| question | answer | evidence |
|---|---|---|
| **what depth does it wade?** | **no number exists.** WATER.md carries no metre figure for a waterline, wade depth or submersion limit — the geometric members are `radius` 0.55, `side_area` 1.85, `bottom_area` 3 (35-37), which are float-model quantities, and the hull is whatever `part_elements[]` holds (42) | **UNKNOWN**; settles in the engine's water-plane test (Q-1 probe) and in a measured waterline on the built car |
| **what depth does it stall?** | the only authorable number is `car_common.engine_shut_down_delay_s` **30** (230) — a *delay*, not a depth; the entry thresholds 10 / 20 (235, 237) have an undecoded unit (239) | decoded delay, **UNKNOWN** depth |
| **what depth is it destroyed?** | `fatal_water_entry_ms` **20** (235), `_floating_` **50** (234), shared by all 232 entities (239) | decoded value, undecoded unit |
| **does it need a water edit for the lore route?** | **no** — "sink and stall" is what the build already does (271); touching the values *is* the change | 271, 250 |
| **could it float instead?** | only with `will_sink` 0 **and** a `BoatBuoyancy` block the donor does not have (273); the APC floats with `will_sink` 0 and the plain `Buoyancy` module (156-167) — the cheaper amphibious precedent | 156-167, 273 |

## 4. What the build must add or copy

| # | item | verdict | file / member | evidence |
|---|---|---|---|---|
| B1 | sink + stall (lore route) | **nothing to add** — inherited | `..._water_interaction.vmodc` `will_sink` 1; `..._buoyancy.vmodc` `buoyancy` 2 | 245-250, 271 |
| B2 | **hull mesh for the Batmobile body** | **the one real step**: `part_elements[]` is built from `sportsmuscle_body` (275); a body swap leaves the water plane pushing the donor's shape | `WaterInteraction.part_elements[].hull.vertices` / `.triangles` (43) against the Batmobile body part | 275, 43 |
| B3 | splash effect | **not copyable from a car** — no water module carries it; if wanted, it is an effect-graph row, not a module member | settles in `FX.md` + the `.epe` `SEffects` | 254-265 |
| B4 | wake effect | same as B3 | same | 254-265 |
| B5 | water sound | same as B3, audio side | settles in `JC3_AUDIO.md` | 254-265 |
| B6 | amphibious option (rejected by D-8) | if ever wanted: `will_sink` 0 **plus** a `BoatBuoyancy` block; donor precedent for the 0-with-`Buoyancy` route is the APC (`will_sink` 0, `buoyancy` 2, no boat module), the full-boat route is the duck (`base_buoyancy` 1.45, 9 pontoons) | `<chassis>_water_interaction.vmodc` `will_sink`; a new `<chassis>_boat_buoyancy.vmodc` | 156-167, 171-186, 273 |
| B7 | shallower/narrower water tolerance | would require a **private** `vehicle_common.vmodc` (no vehicle overrides it, 239) with the `_ms` unit undecoded (239) | shared module, lines 215-239 | **not recommended** |

**Revert** for B2: restore `..._water_interaction.vmodc` from the donor copy in the build's AAF tree
(`Builds/test-091/aaf/.../modules/default/`), rebuild, reinstall. B1, B3-B6 are "no change"; B7 is not
proposed.

---

## 5. Pilot cards

**W1 — shallow wade.**
*Cross a 0.25 m ford at 30 km/h without lifting: speed stays within 15 % of the dry-road value, no stall, and no damage in the damage log. Pass band: 3/3 crossings clean; a stall at 0.25 m means the entry thresholds are being hit far earlier than the hull implies.*

**W2 — bumper-depth wade, stall.**
*Enter water to bumper depth and stop: the engine cuts between 5 s and 35 s after entry (the car timer is 30 s, line 230) and restarts on dry land. Pass band: cut inside 5-35 s on 2/2 attempts, restart always.*

**W3 — drowning / destruction.**
*Drive into water deep enough to cover the roof and stay: the car is destroyed (not left drivable) within 10 s, with no engine sound after the cut. Pass band: 2/2 destroyed inside 10 s; a car that keeps driving submerged contradicts the sink route and means `will_sink` is not being read.*

**W4 — splash on entry.**
*Hit a 0.3 m puddle at 40 km/h: a splash appears at the hull's water contact within 0.2 s of the first wheel entering and is gone within 1.5 s. Pass band: visible on 3/3 entries; absent splash = the effect is not wired (B3), not that the water module failed.*

**W5 — wake while moving.**
*Drive 30 km/h through 0.4 m of water for 3 s: a wake trail follows the hull and stops within 2 s of leaving the water. Pass band: wake present on 3/3 runs and gone ≤ 2 s after exit; a permanent wake means an effect is stuck.*

**W6 — water sound.**
*Enter the same water at 30 km/h: an entry sound is audible within 0.5 s of contact, and the engine note changes for as long as the car is in water. Pass band: 3/3 entries audible; silence is the shipped state until B5 is sourced.*

**W7 — rain-slick road (the part WATER.md cannot carry).**
*Brake from 60 km/h to 0 on the same road segment in dry weather and in rain, same session: the rain stop distance is ≥ 10 % longer. Pass band: measured on 3 dry / 3 wet runs; a difference under 10 % means JC3 has no wet-grip term at all, which is what WATER.md's scan implies (no wetness member among the 38 paths, 254-263).*

## 6. UNKNOWNs, with the file that settles each

| # | unknown | settler |
|---|---|---|
| U1 | what `vehicle_damage.*_water_entry_ms` (10 / 20 / 20 / 50) actually measures | the water-entry consumer in `JustCause3.exe`; `WATER.md` 239 says the unit is not decoded |
| U2 | the wade depth in metres (where lift starts) | the engine's water-plane test (Q-1) — no metre member exists (35-37, 42) |
| U3 | whether a submerged car keeps driving before the fatal timer | native (`WATER.md` 5, 265) |
| U4 | what carries splash and wake | `Research/JC3Grab/FX.md` + the `.epe` `SEffects` objects — not a water member (254-265) |
| U5 | what carries water sound | `Research/JC3Grab/JC3_AUDIO.md` + the vehicle's `SAttachedEffect` roles (254-265) |
| U6 | whether rain lowers grip at all | no wetness member among the 38 paths (254-265); the road-grip members live in `LandGlobal` (`front_wheels` / `rear_wheels.arcade_friction_multiplier`) — `DRIVE_CARRIERS.md` §3.2 |
| U7 | whether the second `WaterInteraction` on the cargo plane is ever read | `WATER.md` 27 — both copies say `will_sink` 1, so no verdict changes |

## 7. Change record

1. **Intended change:** add one plan stating which water members the Batmobile exposes, their values
   with `WATER.md` line citations, the two depth answers (a stalled engine delay and a fatal timer, with
   the unit UNKNOWN), the hull-mesh step a body swap forces, and the splash/wake/sound gap.
2. **File:** `tmp/freebuff/reports/water-crossing-batmobile-build-plan.md` — the brief names it; no file
   in `Research/`, `Working/`, `Builds/`, the archive or the game install is modified.
3. **Revert:** delete this file. Nothing else changed; no game launched, no build packed, no git.

**Limits.** Static only. The unit of the water-entry timers is UNKNOWN in the source and is not guessed
here; wading depth has no member in the files and is measured, not written. Splash, wake and sound are
recorded as gaps with a settler rather than invented from a plausible-looking member.
