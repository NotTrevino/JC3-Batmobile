# Water detection for the teleport: static candidates, ranked

STATUS: done — read-only. No game process was touched and no live check was executed; each candidate
carries the one 5-minute live check that would confirm or kill it.
Scope: JC3 side only (JC3 is the engine that would raise the signal; the Batmobile build inside it).
Question: *which signal can a hook read that means "this vehicle is in water"*, ranked by how directly
it answers that.

Evidence base (all in-repo unless marked): `Research/JC3Grab/WATER.md` (module inventory over 232
vehicle entities), `Research/JC3Grab/VOCABULARY.md` (member table), the cached module dumps at
`E:/Modding/_shared/gamedata/JC3grab/entities/*.ee.json` (232 files, re-probed here), `Working/RTTI/vehicle_rtti.json|.md`
(exe RTTI, 5,259 names), `Research/JC3Grab/USAGES.json|.md` (effect-usage names), and
`tmp/freebuff/reports/immobiliser-and-emp-trigger.md` §6 (the exe's vehicle-variable name block).

---

## 1. Three layers carry water, and only one of them is a state

| layer | carriers | is it a *state* of this vehicle? | can a hook read "in water" from it? |
|---|---|---|---|
| **static config** in the vehicle `.ee` | `WaterInteraction`, `Buoyancy`, `BoatBuoyancy`, `Fins.effective_in_water`, `number_of_water_collision_sensors`, `vehicle_damage.*_water_entry_*` | **no** — constants, identical on land and in water | no, by itself (they say what *would* happen) |
| **engine variable** per vehicle | `is_in_water` (0x24EA0B8), `sinking_progress` — exe name block, next to `engine_damage`, `health_norm`, `vehicle_burning` | **yes** — a per-vehicle value the engine tracks | **yes, most directly** |
| **effect binding** already wired in data | `IsInWater` (hash 2178731301), `Sinking` (2801386962), `WaterHullImpactSound` (946363877) as `SValueDrivenEffectUsage` names | **yes** — the engine's own boolean, consumed by shipped effects | **yes** — and it is the same value the game itself uses |
| **world objects** | `CWaterBox`, `CWaterExtensions`, `CPfxWaterPatch<CPfxVehicle>` (RTTI) | no — geometry / FX, not the car | only by proximity test (raycast / box top vs car Y) |

That split is the whole answer: the config layer that WC `will_sink` belongs to **cannot** detect
water, and the two layers that can are the engine variable and the effect binding that reads it.

---

## 2. Static module layer — the members, and their values on land cars

Re-probed from the 232 cached dumps (`tmp/freebuff/scratch/water/probe.py`, `probe2.py`):

| member | type | fleet | land car value (v0300 sportsmuscle / v0009 saloon) | what it means |
|---|---|---|---|---|
| `WaterInteraction.will_sink` | int32 | 233 modules, 189 entities `1` / 43 `0` | **1** | the hull *would* sink — a prediction, not a state |
| `Buoyancy.buoyancy` | float | 198, `0..2` | **2** | lift scalar used by the sink path |
| `Buoyancy.drag` / `radius` / `side_area` / `bottom_area` / `up_velocity_cap` | float | 198, one value each | **100 / 0.55 / 1.85 / 3 / 20** | shared by every sinking car; no discriminator |
| `WaterInteraction.part_elements[]` | hull mesh | 223 modules | 0 or 1 element | the shape the water plane pushes against — **10 sinking entities have none**, so the mesh is not the switch |
| `all_rotating_part_properties[].number_of_water_collision_sensors` | int8 | 2,784 rows, `0..5` | **5 per wheel** | dedicated water sensors on the wheels — a *contact* source, per wheel, not per vehicle |
| `vehicle_damage.min_water_entry_ms` / `fatal_water_entry_ms` | float | 232, `10` / `20` | **10 / 20** | entry **speed** thresholds in m/s (`card-G2-31.md` §5), i.e. splashdown impact, not submersion |
| `vehicle_damage.min_water_entry_floating_ms` / `fatal_…` | float | 232, `20` / `50` | **20 / 50** | same, for floating hulls |
| `Fins.fins[].effective_in_water` | uint8 | 200 rows, 40 entities (`1`) | absent on cars | per-fin config; the 40 carriers are the APC / sea scout / floatplane family |
| `WaterInteraction.planing_vs_forward_speed_ms`, `buoyancy_factor_vs_speed_ms`, `flat_water_vs_speed_ms` | curves | 233 | present | water handling curves; constants |

`will_sink` is the only scalar separating the 189 sinking vehicles from the 8 amphibious ones
(`WATER.md` §3) — and **the donor-type sports car is one of the 189** (`will_sink` 1). The build
therefore sits on the sinking path, which is why a water watcher has to fire *before* the sink/stall
chain, not after: `car_common.engine_shut_down_delay_s` is **30** on the donor
(`probe2.py` output), and the operator's target behaviour is "engine does not fail", so a hook that
reacts to the stall itself reacts ~30 s too late.

**Verdict on this layer: 0 of these members can answer "in water".** They are the build-side switch
(`will_sink` 0 + `BoatBuoyancy` = float, `WATER.md` §1) and the impact/contact hints, not a detector.

---

## 3. Engine variable layer — `is_in_water`, `sinking_progress`

From `tmp/freebuff/reports/immobiliser-and-emp-trigger.md` §6 (exe `JustCause3.exe`, sha256
`a53c2d6b…dac293`, image base 0x140000000):

```
0x24E9FC0 engine_real_load              0x24EA078 can_fly
0x24EA020 angular_velocity_yaw_rads     0x24EA080 is_disabled_by_emp
0x24EA0B8 is_in_water   <--               0x24EA0F0 …
```

and the wider run around it holds `engine_damage`, `engine_torque_max`, `vehicle_burning`,
`is_frozen`, **`sinking_progress`**, `health_norm` — the per-vehicle values the value-driven-effect
and HUD systems read. `is_in_water` is therefore a **named per-vehicle boolean** in engine
vocabulary, and `sinking_progress` is the float companion (0..1 submersion, range UNKNOWN).

Two measurements matter for how much this proves:

| measurement | result | source |
|---|---|---|
| literal `is_disabled_by_emp` in shipped entries | 0 / 1,941 | `EMP_DISABLE.json` |
| Jenkins hash of `is_in_water` (0x0A011C18) in the same corpus | **160 entries** | `EMP_DISABLE.json:192` |
| lowercase `is_in_water` / `IsInWater` / `Sinking` in the **232 vehicle module dumps** | **0 / 0 / 0** | `probe2.py` |
| `is_in_water` in `USAGES.json` (whole file) | **0** | probe |

So the 160 hits are **not** in the vehicle `.ee` module text; they are hash references somewhere the
module dumps do not show. `.epe` stores property names as hashes (`emp-effects-closest-system-plan.md`
M6), which makes an `.epe` value table the plausible home — **file-type split UNKNOWN** (would need a
per-extension tally of the same 3.98 GB scan; the current scan records only a total).

The same caveat the EMP work states applies verbatim: a name in the vocabulary block is *not* proof
that code reads it (0 instructions / 0 pointers address the ADF member names,
`ARMOR_STEP.md` §2), and that test has **not** been run on this block. What is proven: the engine
names the state, and data references its hash 160 times.

**Directness: highest.** A hook that reads the vehicle object's variable table gets the exact
question answered, with no geometry and no thresholds.

**One 5-minute live check** (read-only, no asset edit):
1. Attach Cheat Engine (or the SDK's object dumper) to the running game, spawn any car.
2. Scan the *module's* memory (base + 0x24E9F40..0x24EA210) for a **pointer to** the string at
   `base+0x24EA0B8`; the hits sit in a `[name_ptr, value]` table per vehicle.
3. Record the 4 bytes at `value`; drive the car into the sea; re-read.
   - **pass:** 0 → 1 at wheel contact and back to 0 on exit (the table's stride also gives the
     `sinking_progress` slot a few entries away).
   - **fail:** no pointer, or the value never moves → the state is HUD/effect-only and rank 4 below
     becomes the primary.
   Cost: one attach, two writes of the car's state, one screenshot of the two readings.

---

## 4. Effect-binding layer — `IsInWater`, `Sinking`, `WaterHullImpactSound`

`Research/JC3Grab/USAGES.json` → `value_driven_usages` (decoded from `.epe` `SValueDrivenEffectUsage`
objects; each row is a *named condition* that enables effects while it holds):

| usage name | name_hash | objects | vehicles | effects it drives |
|---|---|---|---|---|
| **`IsInWater`** | 2178731301 | 126 | **126** | `in_water_move_sound` (126), `sinking_sound` (126), `hull_water_impact_sound_looping` (3) — `USAGES.md:291` |
| `Sinking` | 2801386962 | 35 | 35 — **all boats** (`v1200…`, `v1302…` …) | sinking audio |
| `WaterHullImpactSound` | 946363877 | 35 | 35 — same boat set | hull impact audio |
| `IsInAir` (sibling, same shape) | 646966454 | 126 | 126 | airborne audio |

`IsInWater` is the load-bearing one: the shipped game already gates a **per-vehicle boolean** on 126
of 232 vehicles, and the effect list is exactly the water-contact set (move-through-water loop, sink
alarm, hull impact). That is the engine's own "this vehicle is in water" value, already wired, already
evaluated every frame for wheel-deep water on cars. `Sinking` and `WaterHullImpactSound` are boat-only
(35 = the boat count in `WATER.md` §3) and are therefore **not** usable for a car.

Two ways a hook reads it:
- **(a) value:** resolve the same source the evaluator resolves — the engine variable by hash
  `0x2178731301`'s producer, i.e. rank 3's `is_in_water` under its effect-facing name. Requires the
  producer address, which is what rank 3's check finds.
- **(b) observation:** watch the enabled flag of the attached effect `in_water_move_sound` on the
  vehicle. No engine address needed beyond the effect object, but it arrives one audio-frame late and
  only if the effect is attached (donor-dependent).

**Directness: second highest** — same semantic, one indirection (the effect object) or one name
mapping.

**One 5-minute live check:**
1. Spawn the donor-type car (the build's host), drive a front wheel into ankle-deep water and stop.
2. Listen / watch the attached effects: does `in_water_move_sound` start at **wheel contact** (before
   the car is deep), and does it stop on exit?
   - **pass:** the boolean is true at shallow depth → it is a valid trigger for a teleport-on-touch
     rule, and it is the same condition the ship uses.
   - **fail:** nothing plays on a car, or it only starts when the hull is submerged → the trigger is
     too late for the teleport and rank 3 (engine variable) must be used directly.
3. Cross-check the build's own `.epe`: confirm the donor's attachments include a `usage_effects` row
   for `IsInWater` (one grep of the build's effect-attachments file). If it does not, (b) is
   unavailable and only (a) works.

---

## 5. RTTI layer — what the exe actually names

`Working/RTTI/vehicle_rtti.json`, searched for Water / Buoyancy / Submerge / Swim / Float / Sink:
**7 raw "Water" hits, 0 Buoy, 0 Submerg, 0 Swim, 0 Sink** — i.e. **no buoyancy, submersion or swim
class exists in the RTTI at all.** The five distinct water types are:

| RTTI name | kind | TD | COL | vtable | slot0 | what it is |
|---|---|---|---|---|---|---|
| `.?AV?$CPfxWaterPatch@VCPfxVehicle@@@@` | vehicle | 0x142d455d0 | 0x14286e828 | 0x14234e4a8 | 0x140259950 | the **per-vehicle water patch** (`pfx` = particle FX): the wake/splash surface belonging to a vehicle |
| `.?AV?$CGameObjectCreator@VCWaterExtensions@@@@` | object | 0x142d71cf0 | 0x1428a49d8 | 0x142407720 | 0x1409c77f0 | creator that spawns a **water volume extension** |
| `.?AV?$CGameObjectCreator@VCWaterBox@@@@` | object | 0x142d726a0 | 0x1428a5738 | 0x142407f30 | 0x1409c7a00 | creator that spawns a **water box** (a water volume: the sea/lake body) |
| `.?AV?$sp_counted_impl_pd@PEAVCWaterExtensions…` | object | 0x142d71d60 | 0x1428a4b10 | 0x1424078d8 | 0x1409d59b0 | its refcount holder |
| `.?AV?$sp_counted_impl_pd@PEAVCWaterBox…` | object | 0x142d726e0 | 0x1428a57b8 | 0x142407f60 | 0x1409d5bc0 | its refcount holder |

Two facts to read off this table:
- there is **no bare `CWaterBox` / `CWaterExtensions` class row**, only creators — so the RTTI exposes
  these as *spawned world objects*, not as an API with named methods a hook could call;
- `CPfxWaterPatch<CPfxVehicle>` is templated on the **vehicle** pfx class, i.e. the engine has a
  per-vehicle water-patch object. Its existence/updating is a water signal, but whether it is created
  for a *car* dipping a wheel (vs only for boats) is **UNKNOWN**.

**Directness: medium (world-side).** This is the raycast route the platform check already called
"the fallback" (`jc3mp-runtime-platform-check.md`: *"No `IsInWater`-style member exists, so the
teleport rule needs a height/raycast"*) — that sentence is now **outdated**: `is_in_water` and the
`IsInWater` usage do exist; only the per-object *read* is unproven.

**One 5-minute live check each:**
- **`CWaterBox`:** one pass over the object list at a known lake; read each box's AABB / top Y and
  compare to the visible water surface. Pass = box top equals the surface (then "car Y < surface Y
  inside the box" is a usable fallback trigger). Fail = boxes are level-authoring data with no runtime
  extent.
- **`CPfxWaterPatch`:** put one wheel in shallow water and see whether a patch object appears for the
  car; repeat with the whole car submerged. Pass = the object exists exactly while in water.

---

## 6. Ranked candidates

Directness = how close the signal is to the literal question "is this vehicle in water", for a hook
that must fire *before* the sink chain (`engine_shut_down_delay_s` 30).

| # | candidate | evidence | directness | 5-minute live check | if it fails |
|---|---|---|---|---|---|
| **1** | **`is_in_water`** — engine per-vehicle bool, exe 0x24EA0B8 in the 0x24E9F40..0x24EA210 vehicle-variable block | exe name block; hash 0x0A011C18 in 160 shipped entries | **direct state** (read one bool) | pointer-scan the vehicle object for the name pointer, read the value dry vs in water | no readable table → fall to 2, and 160 hash refs stay unexplained |
| **2** | **`IsInWater`** — `SValueDrivenEffectUsage` name, hash 2178731301, 126 vehicles, gate for `in_water_move_sound`/`sinking_sound` | `USAGES.json`, `USAGES.md:291` | **engine's own boolean**, one indirection | wheel into shallow water → does `in_water_move_sound` start on contact | boat-only / late → use 1 directly |
| **3** | **`sinking_progress`** — engine float beside `is_in_water` | exe name block (§6 above) | submersion **depth**, needs a threshold | read the float dry → submerged; is it monotonic 0→1 | range/units unknown → unusable as a threshold |
| **4** | **`CWaterBox` / `CWaterExtensions`** world volumes (creators 0x142D726A0 / 0x142D71CF0) | RTTI §5 | proximity test, not a state | compare a lake box's top to the surface | authoring-only → **5** |
| **5** | **`number_of_water_collision_sensors`** 5/wheel + `part_elements[]` hull: physics water **contacts** | `VOCABULARY.md:1370`, `WATER.md` §2 | a contact *event*, per wheel | wheel in water → does a contact/impact event fire with a water material? | no material tag → useless |
| **6** | **`CPfxWaterPatch<CPfxVehicle>`** per-vehicle wake object, vtable 0x14234E4A8 | RTTI §5 | object presence while wet | wheel in shallow water → patch object created? | boats only |
| **7** | **`will_sink` 1 + `buoyancy` 2 + hull mesh** — the sink *path* | `WATER.md` §1–3, land values §2 here | config, **not** a state | set `will_sink` 0 on a copy and see whether the car floats instead of stalling | irrelevant — this is a build switch, not a detector |
| **8** | **`min_water_entry_ms` 10 / `fatal_water_entry_ms` 20** | 232 entities; **m/s**, `card-G2-31.md` §5 | splashdown **impact** only | slide in at <10 m/s vs >20 m/s: any damage/stall difference? | gentle entry never trips it → useless for "slid into the sea" |
| **9** | **`Fins.fins[].effective_in_water`** 1 | 40 entities (APC/sea scout/floatplane) | per-fin config | none needed — cars carry no fins | out |

Recommended shape: **1 → 2 → 4**. Read `is_in_water` if the table is reachable; otherwise observe the
`in_water_move_sound` binding on the shipped 126-vehicle set; keep the `CWaterBox` top-vs-Y test as the
fallback that cannot be undefined, since it needs no engine state at all.

---

## 7. Ruled out (with the measurement that rules it out)

| candidate | why not |
|---|---|
| `Sinking` usage (2801386962), `WaterHullImpactSound` (946363877) | 35 vehicles, **all boats** — `USAGES.json` roster; a car never raises them |
| any "exit in water" string | **0** occurrences of `IN_WATER` in the 232 vehicle module dumps (`probe2.py`); no such enum in vehicle modules |
| `Submerge*`, `Swim*`, `Buoyancy*` as RTTI classes | **0 / 0 / 0** hits in 5,259 RTTI names — the engine has no such class |
| `WaterInteraction` as a water *detector* | constants, identical wet or dry; `will_sink` is the only discriminator and it is a prediction |
| player oxygen / drowning HUD | character state, not the vehicle; nothing in `T-19` HUD rows reads a vehicle water flag |
| `traversal_water` (315 occurrences in module text) | not a row on the donor (`probe2.py` row dump empty); its carrier is **UNKNOWN** — it looks like a traversal/effect token, listed only so the next pass does not re-discover it as new |

---

## 8. What this means for the teleport (and the HUD rows)

- The operator rule is *"entering water teleports the car to land; the engine does not fail"*. On the
  JC3 side that is a **watcher → teleport** pair, and the watcher has a hard deadline:
  `will_sink` is **1** on the donor, so the native sink chain starts on water contact, with
  `car_common.engine_shut_down_delay_s` **30** s before engine stall. A detector that keys on the
  stall (or on `sinking_progress` late) cannot satisfy "engine does not fail". `is_in_water` /
  `IsInWater` fire at contact — that is the only timing that works.
- The detector must be **off on land**: all 232 vehicles carry the water modules and the 5-per-wheel
  sensors, so a naive "has water sensors" test is always true.
- HUD: there is no shipped "water" HUD row (the T-19 rows are speed/heat/spread/HUD-only). If a
  water-state row is wanted it has to be **new**, keyed on the same source as the watcher
  (§6 rank 1/2) — nothing existing can be repointed at it.
- Weapon/T-WP rows are untouched by this: no water member exists in any weapon module
  (`WATER.md` §7 keyword scan; `VOCABULARY.md` 1,421 members), so water state cannot reach spread or
  heat. The Vulcan curve work stays independent.

## 9. UNKNOWNs (stated, not filled)

1. Whether any code **reads** `is_in_water` (name in vocabulary ≠ reader; the EMP block's own test has
   not been run here) — rank 1's check decides it.
2. The per-vehicle storage layout/stride of that variable table, and thus `sinking_progress`'s offset.
3. `sinking_progress` range/units and whether it is 0..1.
4. Which file type carries the 160 hash references (`.epe` value tables most plausible; the existing
   scan stores a total, not a breakdown).
5. Whether the **donor/build's own `.epe`** binds `IsInWater` (the 126-vehicle roster is the fleet's;
   the build's attachment table was not opened in this pass).
6. Whether `CPfxWaterPatch` is created for land cars.
7. Whether the water collision sensors surface a taggable "water" material to a contact listener.

## 10. Repro / files

- `tmp/freebuff/scratch/water/probe.py` — token census over the 232 cached dumps, with contexts.
- `tmp/freebuff/scratch/water/probe2.py` — name spellings, the `*WATER*` vocabulary histogram, and the
  water module rows for the donor-type car, a saloon and the APC.
- `python Tools/scripts/t_md2_emp_state.py --check` re-derives the exe block and the 160
  `is_in_water` hits (`Research/JC3Grab/EMP_DISABLE.json`).
- Read-only: nothing was written outside `tmp/freebuff/`.
