# WPN-6 / WLD-15 / WLD-17 — Batmobile winch, vehicle tether and airlift vs JC3's carriers

Task: open the four entities that carry rope/winch geometry, every tow/tether/grapple/cargo-hook
component in the JC3 grab (Rico's grappling hook, tow-style vehicles, helicopter hooks,
`CVehicleCargoBay`), list each member that controls attach point, length, force and release, state
what a Batmobile winch clone needs, and say whether helicopter airlift is blocked by data or by code.
Where JC3 has no exact carrier, give the closest system and the gap for the build (STAGES.md).

**Verdict.**

* **There is no vehicle winch, tether or tow mechanic in JC3's data.** No winch member exists in the
  52-type / 1,421-path module vocabulary, no winch class exists in the 103-class fleet census, and
  none of the 53 module types is a tether/rope/tow/cargo type (`G2X.md:103`; `TETHER.json` →
  `functional_winch_classes: 0`, `tetherish_module_types: {}`). The only rope/winch assets are
  **static mesh parts on four transport boats** (10 part names, 40 rows, `behavior = None`).
* **The grappling hook has no tune either.** JC3's hook/tether is character-side native code: the
  data carries only input actions (`FIRE_GRAPPLE`, `PUSH_GRAPPLE`, `RETRACT_GRAPPLE`,
  `RELEASE_GRAPPLE`, `VEHICLE_RELEASE_GRAPPLE`) and a **damage channel** named `grapple_pull`, not a
  projectile tune, length, force or release member. `tether` matches 335 index paths, of which the
  only non-dialogue, non-video hits are two GraphScripts (`graphs/dualtether_test_to_vehicle.gdc/
  .gsc`) and one challenge decal; tether strength is a proven absence (`TETHER.md` §1, §5).
* **The only decoded attach/release object that can hold a vehicle is `CVehicleCargoBay`:** 12
  objects on 12 entities (cargo plane ×6, transport boat ×4, monorail flatbed ×2), with exactly
  **7 members** — `_object_id`, `disable`, `enable`, `enabled`, `name`, `name_hash`, `world`
  (`TETHER.md` §2). No capacity, no mass limit, no rope, no force, no length. The attach rule is
  native.
* **Helicopter airlift is blocked by data, and the native alternative is `UNKNOWN`.** **0 of 23
  helicopters** has a `CVehicleCargoBay`; the class census has no helicopter hook class either. The
  only decoded proof of a vehicle riding in a vehicle is the **compound entity**
  `v4603_plane_urga_cargotransport_military_cargo_tank` (`CAirPlane` ×1 + `CCar` ×1, bodies
  `25,000` + `40,000`) — a plane, not a helicopter. Whether a native helicopter tow exists is engine
  code (`TETHER.md` §6).
* **For a 6 t car the mass half of the question is answerable, the force half is not.** `RigidBody`
  gives donor 975 and the build target 6,000 (**6.154×**), but the unit is `UNKNOWN` and no tether
  force exists in any table, so "6 t" only says the winch must beat 6.154× the donor's class, not a
  number in newtons. BmAK's own feat bound is **≥ ~2 t** (elevator + Batman + occupant, MODLOG §86),
  i.e. **below** a 6 t car.
* **Closest system per row:** WPN-6 → Rico's grapple/tether (pull mechanic) + the transport boat's
  `transport_rope_winch` mesh (geometry), with a vehicle entity object as the anchor; WLD-15 →
  `CVehicleCargoBay` / `CGrapplingHookPropData` (attach/release objects); WLD-17 → the cargo plane's
  bay + compound entity (the only decoded vehicle-carry). Every row's gap is a **code-level pull
  loop** plus a rope/reel renderer; no JC3 file supplies either.

---

## 1. The BmAK side (T-WP6): an 18-field winch class, no readable defaults

Evidence: `Working/Translation/T7_WEAPONS.md:46,81,256-266`,
`Research/BatmobileGrab/COVERAGE.md:93`, `Research/BatmobileGrab/ASSETS.md:187,334`.

| item | value | evidence |
|---|---|---|
| class | `RBatmobileWinch`, 3 instances | `ASSETS.md:187` |
| object | `Batmobile_Winch` | `ASSETS.md:334`; `COVERAGE.md:93` |
| serialised fields | **18** | `COVERAGE.md:93` ("`RBatmobileWinch` \| 18 \| `T-W1`") |
| named asset fields | `FireEffect` → `Winch.Winch_Muzzle`; `ImpactEffect` → `VFX_Batmobile.winch_latched`; `FireSound` → `Engine.Play_BML_WinchFire`; `ImpactSound` → `Engine.Play_BML_Winch_Attatch` | `T7_WEAPONS.md:81,258` |
| other field | a bool at object `offset 0x0970` (true) — **name and meaning `UNKNOWN`** in the corpus | `T7_WEAPONS.md:81` |
| pull-mode member | `Core.WinchPullType`, `ByteProperty`, import index `-1515`, outer/owner `RBatmobileWinch`, home `BmGame` | `COLLISION_SELECTOR3.md:392` |
| rope-length logic | `RestoreOldRopeLengthIfShorter` — a **function on `RBatmobileWinch`**, not a member | `DAMAGE_RULES.md:352` |
| trigger hooks in code | `FireWeaponInternal`, `HolsterWinch` (script stubs at `BmGame.upk` 48056 / 48069) | `COLLISION_MODES.md:66-67` |
| class default | **unreachable**: `RBatmobileWinch` / `Default__RBatmobileWinch` are imports from `BmGame` (214 MB, fully-compressed script package); current tools fail its magic gate | MODLOG §87 (lines 4465-4483) |
| anchor socket | `WinchOrigin` (one of the 65 sockets) | `GRAB_BACKLOG.md:467` (G1-13 card) |
| rope-hang sockets | 4 × `HangFromRope_Front/Right...`, z = **460.50** (BmAK cm) on the wheels | `MECHANICS.md:716-719` |
| VFX present | `Winch_Muzzle` and `winch_latched` particle systems, `fx_Winch_M_lit` material + instance | `objects.jsonl` (`Winch` matches) |
| rope carrier | `RSimpleRopeComponent` ×2 per package (`RopeComponent0`, `RopeComponent1`); **6 exports** fleet-wide | `ASSETS.md:144,345` |
| rope bindings | `RBatmobileWinch.ProjectileRope` @`0x0A18` → `Batmobile_Winch.RopeComponent0`; `RBatmobileWinch.StubRope` @`0x0A10` → `RopeComponent1` | `WEAPONS.md:1242-1243,1265-1266` |
| rope component fields | material `VFX_Generic.fx_Winch_M_lit_INST` @560; float **3.5** @680 (name `UNKNOWN`); `RopeComponent1` extra float **0.8690145611763** @364 | `objects.jsonl` (Funhouse 5357/5358, MK2 5319/5320) |

So BmAK itself gives **no length, speed, force or attach-point member**: the only rope-related names
are the *function* `RestoreOldRopeLengthIfShorter` and a `WinchPullType` enum whose values are not
decoded. The winch's authored numbers live in the unreachable `BmGame` class default, which is why
MODLOG §86 says a winch value can at best be a force and never a mass.

The `WinchOrigin`/`HangFromRope` sockets are the only car-side anchors the grab quantifies, and the
`HangFromRope_*` chain is already used by the four hang sockets in `SOCKETS_JC3` (the 4 outliers that
sit 2.446 m above the body box by design, `GRAB_BACKLOG.md` G1-13 "Done").

---

## 2. The four JC3 entities that carry rope/winch geometry

From `Research/JC3Grab/TETHER.json` → `winch.winch_parts` / `winch.picks` and `TETHER.md` §4. All
four are the **Urga transport boat** (`v1602_boat_urga_transport`), one row set per variant:

| # | entity (`.ee`) | parts |
|---|---|---|
| 1 | `editor/entities/jc_vehicles/03_sea/v1602_boat_urga_transport/v1602_boat_urga_transport_debug.ee` | 17–26 |
| 2 | `…/v1602_boat_urga_transport_military_01.ee` | 17–26 |
| 3 | `…/v1602_boat_urga_transport_military_01_delivery.ee` | 17–26 |
| 4 | `…/v1602_boat_urga_transport_rebel_01.ee` | 17–26 |

The ten part names, identical on all four entities (40 rows = 10 × 4):

| part_index | part | damage_type | behavior | parent | model |
|---:|---|---|---|---:|---|
| 17 | `transport_rope_01` | `Boat_Generic` | `None` | 0 | `models/…/transport_rope_01.lod` |
| 18 | `transport_rope_02` | `Boat_Generic` | `None` | 0 | `transport_rope_02.lod` |
| 19 | `transport_rope_03` | `Boat_Generic` | `None` | 0 | `transport_rope_03.lod` |
| 20 | `transport_rope_pontoon_c_l` | `Boat_Generic` | `None` | 0 | `…_c_l.lod` |
| 21 | `transport_rope_pontoon_c_r` | `Boat_Generic` | `None` | 0 | `…_c_r.lod` |
| 22 | `transport_rope_pontoon_f_l` | `Boat_Generic` | `None` | 0 | `…_f_l.lod` |
| 23 | `transport_rope_pontoon_f_r` | `Boat_Generic` | `None` | 0 | `…_f_r.lod` |
| 24 | `transport_rope_pontoon_r_l` | `Boat_Generic` | `None` | 0 | `…_r_l.lod` |
| 25 | `transport_rope_pontoon_r_r` | `Boat_Generic` | `None` | 0 | `…_r_r.lod` |
| 26 | `transport_rope_winch` | `Boat_Generic` | `None` | 0 | `transport_rope_winch.lod` |

Model files: 12 fleet-wide (`rebel_…` + `transport_rope_winch`, 6 files each: `.lod` + `_lod1..5.rbm`),
6 of them on one boat (`TETHER.json` → `winch_files`, `winch_files_one_entity`). Every part is a
plain mesh: **no behavior, no socket, no parent, no rope parameter**. Nothing in these four entities
reels, pulls or releases; they are the boat's pontoon lashings and a static winch drum.

Nearest JC3 part behaviours that *do* something link-like: `FrontWagonCoupling` ×5,
`RearWagonCoupling` ×12, `FrontWagonCouplingLinked` ×5, `RearWagonCouplingLinked` ×5, `TrainCargo`
×60, `CargoBayDoor` ×28 (`TETHER.json` → `winch.behaviour_totals`). The couplings are a rigid train
link with no distance or force member; `CargoBayDoor` opens 0–90° and stops (`DOORS.md:84`,
`DOOR_ANGLES.md:474`). Neither pulls.

---

## 3. Every attach / tow / hook / cargo component in the grab

### 3.1 `CVehicleCargoBay` — 12 objects, 7 members

`TETHER.md` §2; `ENTITIES.md:92` (`CVehicleCargoBay` 12).

| member | type / value | what it controls |
|---|---|---|
| `world` | 4×4 transform; four distinct worlds ship (below) | **attach point** (the bay's frame) |
| `enabled` | 1 on all 12 | on/off |
| `enable` / `disable` | event names — **empty on all 12** | **release** hook (unwired) |
| `name` / `name_hash` | `VehicleCargoBay` | identity |
| `_object_id` | object id | reference |

Bay worlds: `0,1.292236,-2.511719` ×4; `0,4.2,5` ×6; `0,5.902588,-0.5029297` ×1; `0,0,0` ×1.
Bay points on the six planes: `point.bay.cargo.hold` = `0,2.360596,1.009766`;
`point.bay.cargo.doors` = `0,3.109009,26.59424` (`TETHER.md` §2). The bay is a **transform with an
unwired enable/disable pair** — no capacity, no mass limit, no rope.

Carriers: cargo plane `v4603_plane_urga_cargotransport` ×6, transport boat `v1602_boat_urga_transport`
×4, monorail flatbed `v5602_train_urga_monorailflatbed` ×2. **Helicopters: 0.**

The proof a vehicle can ride: `v4603_plane_urga_cargotransport_military_cargo_tank` contains two
vehicle roots (`CAirPlane` ×1, `CCar` ×1) and two bodies (`25,000`, `40,000`) — the only compound
entity in the fleet (`TETHER.md` §2).

### 3.2 `CGrapplingHookPropData` — 33 objects on 3 prop entities

`TETHER.md` §3; `ENTITIES.md:74`.

| entity | objects |
|---|---|
| `v0505_car_solar_oldtruck_commercial_cargo_barrel` | 10 |
| `v0505_car_solar_oldtruck_commercial_cargo_random` | 13 |
| `v5602_train_urga_monorailflatbed_military_containers_rigidobject` | 10 |

Object names: `GrapplingHookPropData` 18, `CGrapplingHookPropData` 9, `tether_tear` 2,
`tether_tear7` 2, `tether_yank` 2. All `enabled = 1`; **`enable_event` and `disable_event` empty on
all 33**. The object's own member list is **`UNKNOWN`** in the corpus — only its name, enabled flag
and event pair are decoded, and it marks *which loose cargo prop may be torn or yanked*, carrying no
force, distance or mass. It is the closest JC3 "attach a rope to this object" tag, and it is a tag —
not a joint.

### 3.3 Rico's grapple and tether — actions and damage gates only

| member / name | value | evidence |
|---|---|---|
| `FIRE_GRAPPLE` | `LSHOULDER` (pad) / `MOUSE2` | `INPUT.md:75` |
| `PUSH_GRAPPLE` | `RPADRIGHT` / `C` (on-foot) | `INPUT.md:169` |
| `RELEASE_GRAPPLE` | `RPADRIGHT` / `V` (on-foot) | `INPUT.md:175` |
| `RETRACT_GRAPPLE` | on `LT` | `EJECT_MAP.md:119` |
| `VEHICLE_RELEASE_GRAPPLE` | `LPADDOWN` (vehicle page) | `DRIVE_CARRIERS.md:196` |
| `grapple_pull_armor` | int32, `-1 .. 0` over 233 entities (median 0) | `ARMOR_STEP.md:182`; `VOCABULARY.md:1472` |
| `grapple_pull_armor_strength` | float32, `0 .. 100` over 233 entities (median 0), one sample **100.0** (`0x42c80000`) | `ARMOR_STEP.md:183`; `VOCABULARY.md:1473` |

These are the *only* numeric "grapple" values in the decoded fleet, and they gate damage: the
`grapple_pull` channel is one of 8 `VehicleDamage` channels (`DAMAGE_MODEL.md:20,247`). There is **no**
grapple **length, force, reel rate, attach offset or release distance** anywhere. The two
`dualtether_test_to_vehicle.gdc/.gsc` GraphScripts are the only tether-to-vehicle assets and were not
read (`TETHER.md` §6) — `UNKNOWN`.

### 3.4 Absence measurements (all re-derived, `jc3tether.py --check`)

| measurement | value | evidence |
|---|---|---|
| winch member paths in the 52-type / 1,421-path vocabulary | **0** | `G2X.md:103` |
| winch classes in the 103-class fleet census | **0** | `G2X.md:103` |
| tether/cargo/rope/winch/tow module types (of 53) | **0** | `TETHER.json` → `module_types: 53`, `tetherish_module_types: {}` |
| functional winch classes | **0** | `TETHER.json` → `functional_winch_classes: 0` |
| part behaviours that pull or reel | **0** (67 named behaviours, nearest `CargoBayDoor`) | `TETHER.md` §4 |
| `winch` paths in `INDEX.jsonl` | **0** (parts-table prop meshes are not indexed; 196 `.lod` paths only) | `TETHER.md` §5 |
| `tether` paths in the index | 335 (124+124 dialogue, 60+20 DLC sound, 2 icons, 2 videos, 1 decal, 2 graph scripts) | `TETHER.md` §5 |

---

## 4. Member-by-member: attach point, length, force, release

| capability | BmAK (winch) | JC3 closest member | gap |
|---|---|---|---|
| **anchor on the vehicle** | `WinchOrigin` socket (bone + offset, G1-13); `HangFromRope_*` ×4 at z 460.50 cm | `CVehicleCargoBay.world` (4×4 transform) on a part-hosted object; bay points `point.bay.cargo.hold/doors`; part `deformable_transform` chain for a light-style anchor | JC3 has no socket table for ropes; a vehicle object can carry a `world`, but nothing binds it to a winch |
| **rope/cable geometry** | two `RSimpleRopeComponent`s per package, bound as `ProjectileRope` @0x0A18 / `StubRope` @0x0A10; each serialises only a material (`fx_Winch_M_lit_INST` @560), a float **3.5** @680 and, on the stub, **0.8690145611763** @364 | `transport_rope_winch` mesh (+ `transport_rope_01..03`), 6 files, static, `behavior = None` | BmAK has the rope renderer and the binding, but no length; JC3 has only a static mesh — no reel, no length parameter, no segment chain |
| **length** | function `RestoreOldRopeLengthIfShorter` (code), no member | **none** — no length member in any module or object | both sides: BmAK length is script-side and unreachable; JC3 has no member at all |
| **force / pull** | class has 18 fields, none decoded as force; MODLOG §86 bound ≥ ~2 t from a feat | **none** — tether strength proven absent; only `grapple_pull_armor(_strength)` damage gates | the whole pull loop is native on both sides |
| **release** | `HolsterWinch` (script stub) + `WinchPullType` byte (values unknown) | `CVehicleCargoBay.disable` (empty event); `CGrapplingHookPropData.disable_event` (empty) | no file wires a release; the inputs exist (`RELEASE_GRAPPLE`, `VEHICLE_RELEASE_GRAPPLE`) |
| **attach state** | none decoded (`WinchPullType` byte is the only state enum, values unknown) | `enabled` / `enable` on the bay (empty event) | no attach state machine in data |

---

## 5. The 6 t arithmetic (what can and cannot be said)

From `TETHER.md` §1 (all re-derived by `jc3tether.py --check`):

| quantity | value |
|---|---|
| donor `v0300_car_kensington_sportsmuscle_civilian_01` mass | **975** |
| Batmobile design mass | **6,000** |
| ratio | **6.154×** |
| cargo plane body mass | `25,000` / `40,000` → 6 t is **15.0 %** of the plane |
| transport boat body mass | `100,000` → **6.0 %** |
| flatbed body mass | `15,000` → **40.0 %** |
| unit of `RigidBody.mass` | **`UNKNOWN`** (bare number in the file) |
| tether/winch force in any table | **none** |

Consequences for a winch clone:

* A force can only be stated as a **ratio**, never in newtons: it must exceed 6.154× the donor's
  class, and must at least hold the car's own weight if the car is to hang from the cable
  (static `T = m·g` is one equation with `T` and the unit unknown — MODLOG §86).
* BmAK's demonstrated winch feat bounds the winch at **≥ ~2 t** (elevator + Batman + one occupant),
  so the shipped winch is **under** a 6 t car: cloning its numbers would not lift the Batmobile.
* If the car pulls rather than hangs (rolling resistance, not weight), the requirement is much lower
  and **cannot be computed** from the files: no friction, no cable tension, no motor rating is
  decoded. That is a design choice, not a decode.

---

## 6. What a Batmobile winch clone needs

1. **A vehicle-side anchor object.** Closest data pattern: a `CVehicleCargoBay`-style object
   (`name`, `name_hash`, `world`, `enabled`, `enable`, `disable`, `_object_id`) on the Batmobile's
   entity, positioned at the `WinchOrigin` socket. This is the only decoded object that already
   carries a transform + enable/disable pair, and it costs an entity-graph add, not a new class.
2. **Rope geometry.** The cable itself is BmAK's `RSimpleRopeComponent` pair — `RopeComponent0`
   (`ProjectileRope`, the flying end) and `RopeComponent1` (`StubRope`, the short remainder) — with
   the material `fx_Winch_M_lit_INST` and two floats (3.5; 0.869). That is the object to clone; the
   names of the floats are `UNKNOWN`, so their meaning cannot be carried as a length. For visible
   hardware, copy `transport_rope_winch` (1 part, `parent 0`, `Boat_Generic`, no behavior, 5 LOD
   RBMs, 6 files) as the drum/mesh donor and `transport_rope_01..03` for static segments; re-typing
   the part from `Boat_Generic` to a Land damage type is part of the copy.
3. **A pull loop.** This is the part JC3 does not have: a per-frame force toward a target, a length
   clamp and a release. None of the 53 module types does it, no part behaviour does it, and the only
   numeric grapple values are damage gates. The build must implement it as script/code (the
   `dualtether_test_to_vehicle` GraphScript is the only JC3 precedent and is unread → `UNKNOWN`).
4. **A trigger.** JC3's own bindings show the buttons exist — `RELEASE_GRAPPLE` (RPADRIGHT / V) and
   `VEHICLE_RELEASE_GRAPPLE` (LPADDOWN) — but no vehicle action calls a winch. The operator lead
   already assigns **d-pad RIGHT** to the winch, replacing Mission Select
   (`COMPROMISES_T.md:119`).
5. **The VFX/SFX.** BmAK's `Winch.Winch_Muzzle`, `VFX_Batmobile.winch_latched`,
   `Engine.Play_BML_WinchFire`, `Engine.Play_BML_Winch_Attatch` are portable assets (the grab keeps
   the sounds for T-16/T-13, `T7_WEAPONS.md:266`).
6. **The 6 t target.** Use 6,000 as the mass to move; because the unit is unknown, express the winch
   in game units by ratio (must beat 6.154× the donor), and validate with an in-game A/B pull, never
   by deriving newtons.

**Closest system + gap per translation row:**

| row | closest JC3 system | gap the build fills |
|---|---|---|
| **T-WP6** (winch) | Rico's grapple/tether for the *pull* (native, no members) + `transport_rope_winch` for the *drum mesh* + `CVehicleCargoBay` for the *vehicle-side anchor object* | no vehicle winch member, no force/length/reel, no trigger; STAGES.md BUILD must add the pull loop and the anchor object; the mesh copy is cheap |
| **T-WLD15** (tether a 6 t car) | `CVehicleCargoBay` (7 members, `world` + empty enable/disable) and `CGrapplingHookPropData` (33 tags on 3 prop entities, empty events) | attach works only as a transform + flag; length, force, rope and release are absent; the tether is native code — data cannot express it |
| **T-WLD17** (airlift) | cargo plane bay + the compound `…_military_cargo_tank` entity (`CAirPlane` + `CCar`, 25,000 + 40,000) | **0 of 23 helicopters** has a bay and the census has no helicopter hook class → data-blocked; a native helicopter tow may exist but is `UNKNOWN` |

---

## 7. Is helicopter airlift blocked by data or by code?

**Both, in different senses — and the data side is the blocker for any build we can author.**

* **Data-blocked for a data-built route:** `CVehicleCargoBay` appears 12 times, on planes (6), boats
  (4) and a flatbed (2), and **never on a helicopter** (`TETHER.md` §2). The 103-class census has
  `CGrapplingHookPropData` (33, all loose cargo props) but **no helicopter hook/cargo class**
  (`ENTITIES.md:74,92`). Adding a bay to a helicopter entity would be an entity-graph edit with an
  unverified native attach rule — the bay's own `enable`/`disable` events are empty on all 12.
* **Code-only for a native tow:** whether JC3 helicopters can pick up a car by a native hook/tether
  is `UNKNOWN`; no file names one, and the only vehicle-carry proof is the plane's compound entity
  (`TETHER.md` §6). That answer needs a Q-1 probe (fly a helicopter at a car and observe), not
  another decode.
* **For scale:** the plane's compound entity is the *only* decoded evidence that one vehicle's
  entity holds another; even there, the rule that keeps the tank in the bay is native.

---

## 8. UNKNOWNs (named, not filled)

- `RBatmobileWinch`'s 14 unnamed fields, its `0x0970` bool, and `WinchPullType`'s enum values — the
  class default is in the unreachable `BmGame` package (MODLOG §87).
- `RSimpleRopeComponent`'s **3.5** (@680) and **0.8690145611763** (@364) floats — the decoder names
  neither, so whether they are width, segment length, slack or a material parameter is `UNKNOWN`.
- BmAK winch force, cable speed, max rope length — none is a decoded member. `RestoreOldRopeLengthIfShorter`
  proves a length exists in code, not its value.
- `CGrapplingHookPropData`'s member list — not decoded; only name, `enabled`, `enable_event`,
  `disable_event`.
- JC3 tether strength, length, reel rate — proven absent from tables (`TETHER.md` §1).
- `graphs/dualtether_test_to_vehicle.gdc/.gsc` behaviour — not read.
- `RigidBody.mass` unit — bare number.
- Whether any native helicopter tow exists — code, `UNKNOWN`.

## Evidence index

- `Research/JC3Grab/TETHER.md` §1 (mass, donor 975, target 6,000, 6.154×, carrier ratios), §2
  (`CVehicleCargoBay` 12/7 members, bay worlds/points, compound tank entity, 0 helicopter bays), §3
  (`CGrapplingHookPropData` 33/3 entities, empty events), §4 (40 rope/winch part rows, 10 names, 4
  entities, 0 module types, 0 behaviours), §5 (index names), §6 (UNKNOWNs); `TETHER.json`
  (`winch_parts`, `winch_files`, `functional_winch_classes: 0`, `tetherish_module_types: {}`).
- `Research/JC3Grab/ENTITIES.md:74,92` — `CGrapplingHookPropData` 33, `CVehicleCargoBay` 12.
- `Research/JC3Grab/VOCABULARY.md:1472-1473` — `grapple_pull_armor`, `grapple_pull_armor_strength`.
- `Research/JC3Grab/ARMOR_STEP.md:182-183` — same two, with `0x42c80000` = 100.0.
- `Research/JC3Grab/DAMAGE_MODEL.md:20,247` — `grapple_pull` is one of 8 damage channels.
- `Research/JC3Grab/INPUT.md:75,169,175`; `EJECT_MAP.md:113,119`; `DRIVE_CARRIERS.md:196` — grapple
  input actions.
- `Research/JC3Grab/G2X.md:103,163` — measured absence: 0 winch member paths / 0 winch classes.
- `Research/JC3Grab/DOORS.md:84`; `DOOR_ANGLES.md:474` — `CargoBayDoor` 0–90°.
- `Research/BatmobileGrab/ASSETS.md:144,187,334,345`; `COVERAGE.md:93`; `T7_WEAPONS.md:46,81,256-266`
  — `RBatmobileWinch`, 18 fields, four asset refs, `0x0970`, and the two `RSimpleRopeComponent`
  exports; `WEAPONS.md:1242-1243,1265-1266` — `ProjectileRope`/`StubRope` bindings.
- `Research/BatmobileGrab/COLLISION_SELECTOR3.md:392`; `COLLISION_MODES.md:66-67`; `DAMAGE_RULES.md:352`
  — `WinchPullType`, `FireWeaponInternal`/`HolsterWinch`, `RestoreOldRopeLengthIfShorter`.
- `MODLOG.md` §86 (lines 4441-4461), §87 (4465-4483) — ~2 t feat bound; class default unreachable.
- `Research/BatmobileGrab/MECHANICS.md:716-719`; `GRAB_BACKLOG.md:467` — `HangFromRope_*` (z 460.50)
  and `WinchOrigin`.
- `Working/Translation/T7_WEAPONS.md:81`; `COMPROMISES_T.md:112-113,119` — T-WP6/T-WLD15/T-WLD17
  dispositions and the d-pad RIGHT decision.
